"""StrategyMatrixRunner — 策略矩阵运行器。

对全标的池中每只标的，运行其所属组分配的策略，输出 Signal 列表。

关键设计点：
    1. 信号有效期（signal_valid_bars）：检查最近 N bar 内是否出现过非零信号，
       解决事件型信号（如双均线只在金叉当天发出）在非信号日被漏掉的问题。
    2. 传入完整 df：strategy_fn(df["close"], df=df, **params)，
       兼容需要 high/low/volume 的策略。
    3. 全读本地 MarketDataStore，无网络 IO，亚秒级完成 550 只扫描。
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from loguru import logger

from mytrader.data.store.market_data_store import MarketDataStore
from mytrader.strategy.base import Signal, SignalDirection
from mytrader.strategy.registry import STRATEGY_REGISTRY
from mytrader.universe.manager import UniverseManager


@dataclass
class MatrixScanResult:
    """单次矩阵扫描结果。"""

    signals: list[Signal] = field(default_factory=list)
    symbol_count: int = 0
    strategy_runs: int = 0
    errors: dict[str, str] = field(default_factory=dict)

    @property
    def buy_signals(self) -> list[Signal]:
        return [s for s in self.signals if s.direction == SignalDirection.BUY]

    @property
    def sell_signals(self) -> list[Signal]:
        return [s for s in self.signals if s.direction == SignalDirection.SELL]


class StrategyMatrixRunner:
    """策略矩阵运行器。

    Args:
        store:             MarketDataStore 实例
        universe:          UniverseManager 实例
        weights_file:      strategy_weights.json 路径
        signal_valid_bars: 信号有效期（bar 数），默认 3
                           N=1 退化为只看最后一根 bar（严格模式）
    """

    def __init__(
        self,
        store: MarketDataStore,
        universe: UniverseManager,
        weights_file: str | Path | None = None,
        signal_valid_bars: int = 3,
    ) -> None:
        self._store = store
        self._universe = universe
        self._signal_valid_bars = signal_valid_bars

        if weights_file is None:
            weights_file = self._find_weights_file()
        self._weights_file = Path(weights_file) if weights_file else None
        self._weights: dict[str, list[dict[str, Any]]] = {}
        self._load_weights()

    # ------------------------------------------------------------------
    # 公共接口
    # ------------------------------------------------------------------

    def run(
        self,
        lookback_days: int = 90,
        max_workers: int = 8,
    ) -> MatrixScanResult:
        """对全标的池运行各自分组的策略，输出信号列表。"""
        symbols = self._universe.get_universe()
        result = MatrixScanResult(symbol_count=len(symbols))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.run_symbol, sym, lookback_days): sym
                for sym in symbols
            }
            for future in as_completed(futures):
                sym = futures[future]
                try:
                    sigs = future.result()
                    result.signals.extend(sigs)
                    result.strategy_runs += len(sigs) + 1  # 近似
                except Exception as e:
                    result.errors[sym] = str(e)
                    logger.debug(f"[matrix] {sym} error: {e}")

        logger.info(
            f"[matrix] scan done: {result.symbol_count} symbols, "
            f"{len(result.signals)} signals, {len(result.errors)} errors"
        )
        return result

    def run_symbol(
        self,
        symbol: str,
        lookback_days: int = 90,
    ) -> list[Signal]:
        """运行单只标的的所有分配策略。"""
        meta = self._universe.get_symbol_meta(symbol)
        if meta is None:
            return []

        group_strategies = self._weights.get(meta.group_id, [])
        if not group_strategies:
            # 未找到组权重 → fallback：尝试 UNKNOWN 或空列表
            logger.debug(f"[matrix] {symbol}: no strategies for group {meta.group_id}")
            return []

        df = self._store.get_latest_n_bars(symbol, n=lookback_days)
        if df.empty or len(df) < 10:
            return []

        signals: list[Signal] = []
        now = datetime.now(tz=timezone.utc)

        for entry in group_strategies:
            strategy_name = entry["strategy"]
            params = entry.get("params", {})
            weight = float(entry.get("weight", 1.0))

            strategy_fn = STRATEGY_REGISTRY.get(strategy_name)
            if strategy_fn is None:
                logger.warning(f"[matrix] strategy '{strategy_name}' not in registry, skip")
                continue

            try:
                # ⚠️ 传入完整 df（部分策略需 high/low/volume）
                sig_series = strategy_fn(df["close"], df=df, **params)
            except TypeError:
                # 策略函数不接受 df 参数时，只传 close
                sig_series = strategy_fn(df["close"], **params)
            except Exception as e:
                logger.debug(f"[matrix] {symbol}/{strategy_name} error: {e}")
                continue

            # ⚠️ 信号有效期：检查最近 N bar 内是否出现过非零信号
            # 解决事件型信号（金叉只在当天=1）在非信号日被漏掉的问题
            recent = sig_series.iloc[-self._signal_valid_bars :]
            nonzero = recent[recent != 0]
            if nonzero.empty:
                continue

            latest = int(nonzero.iloc[-1])  # 取最近一次有效信号方向

            direction = SignalDirection.BUY if latest == 1 else SignalDirection.SELL
            confidence = min(weight, 1.0)

            signals.append(
                Signal(
                    symbol=symbol,
                    direction=direction,
                    timestamp=now,
                    confidence=confidence,
                    strategy_name=strategy_name,
                    indicators={
                        "group_id": meta.group_id,
                        "backtest_sharpe": entry.get("backtest_sharpe", 0.0),
                        "backtest_win_rate": entry.get("backtest_win_rate", 0.0),
                        "weight": weight,
                    },
                )
            )

        return signals

    def reload_weights(self) -> None:
        """热加载 strategy_weights.json（每月 MatrixBacktest 更新后无需重启）。"""
        self._load_weights()
        logger.info("[matrix] weights reloaded")

    def set_weights_for_group(
        self, group_id: str, strategies: list[dict[str, Any]]
    ) -> None:
        """直接注入分组权重（测试/调试用）。"""
        self._weights[group_id] = strategies

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _load_weights(self) -> None:
        """从 JSON 文件加载策略权重。"""
        if self._weights_file and self._weights_file.exists():
            with open(self._weights_file, encoding="utf-8") as f:
                data = json.load(f)
            self._weights = data.get("groups", {})
            logger.info(
                f"[matrix] weights loaded: {len(self._weights)} groups from {self._weights_file}"
            )
        else:
            self._weights = {}
            logger.debug("[matrix] no weights file, using empty weights")

    @staticmethod
    def _find_weights_file() -> Path | None:
        """从 cwd 向上查找 config/strategy_weights.json。"""
        here = Path.cwd()
        for parent in [here, *here.parents]:
            candidate = parent / "config" / "strategy_weights.json"
            if candidate.exists():
                return candidate
        return None
