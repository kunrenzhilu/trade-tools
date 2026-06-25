"""UniverseManager — 标的池管理器。

职责：
    1. 维护 S&P 500 + Nasdaq 100 成分股（去重约 550 只）
    2. 基于 MarketDataStore 中的历史数据动态计算波动率分层
    3. 向 StrategyMatrixRunner 提供"标的 → 所属组"的映射
    4. 提供历史时点分组接口（供矩阵回测 point-in-time 使用）
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
from loguru import logger

from mytrader.data.store.market_data_store import MarketDataStore
from mytrader.universe.constituents import (
    fetch_nasdaq100,
    fetch_sp500,
    load_from_csv,
    save_to_csv,
)
from mytrader.universe.grouping import build_group_id, compute_volatility_tier
from mytrader.universe.models import SymbolMeta


class UniverseManager:
    """标的池管理器。

    Args:
        store:          MarketDataStore 实例（用于读取历史数据计算波动率）
        universe_file:  成分股缓存 CSV 路径（默认 config/universe.csv）
        volatility_lookback_days: 波动率计算用近多少天数据
    """

    def __init__(
        self,
        store: MarketDataStore,
        universe_file: str | Path | None = None,
        volatility_lookback_days: int = 60,
    ) -> None:
        self._store = store
        self._lookback = volatility_lookback_days

        if universe_file is None:
            # 向上查找 config/universe.csv
            universe_file = self._find_universe_file()
        self._universe_file = Path(universe_file) if universe_file else None

        # 内存缓存
        self._constituents: list[dict[str, str]] = []   # [{symbol, sector, index}, ...]
        self._meta_map: dict[str, SymbolMeta] = {}       # symbol → SymbolMeta

        self._load_constituents()

    # ------------------------------------------------------------------
    # 公共接口
    # ------------------------------------------------------------------

    def get_universe(self) -> list[str]:
        """返回当前全部可交易标的列表（去重后约 550 只）。"""
        return [m.symbol for m in self._meta_map.values()]

    def get_symbol_meta(self, symbol: str) -> SymbolMeta | None:
        """返回单只标的的元信息（含所属组）。"""
        return self._meta_map.get(symbol.upper())

    def get_groups(self) -> dict[str, list[str]]:
        """返回 {group_id: [symbols]} 分组映射。"""
        groups: dict[str, list[str]] = {}
        for sym, meta in self._meta_map.items():
            gid = meta.group_id
            groups.setdefault(gid, []).append(sym)
        return groups

    def refresh_constituents(self, save: bool = True) -> None:
        """从网络刷新成分股列表（每月调用）。

        成功时更新内存缓存 + 保存 CSV；失败时保持原有缓存。
        """
        sp500 = fetch_sp500()
        ndx100 = fetch_nasdaq100()

        if not sp500 and not ndx100:
            logger.warning("[universe] refresh failed: both sources empty, keeping cache")
            return

        merged = self._merge_constituents(sp500, ndx100)
        self._constituents = merged
        if save and self._universe_file:
            save_to_csv(merged, self._universe_file)

        # 保留已有波动率分组，重建 meta_map
        self._rebuild_meta(merged)
        logger.info(f"[universe] refreshed: {len(self._meta_map)} symbols")

    def recompute_volatility_tiers(
        self,
        lookback_days: int | None = None,
        max_workers: int = 8,
    ) -> None:
        """基于近 lookback_days 天数据重算波动率分层（当前时点）。"""
        self._do_recompute(
            as_of_date=None,
            lookback_days=lookback_days or self._lookback,
            max_workers=max_workers,
            inplace=True,
        )

    def recompute_volatility_tiers_at(
        self,
        as_of_date: date,
        lookback_days: int | None = None,
    ) -> dict[str, str]:
        """历史时点波动率分层（供矩阵回测 point-in-time 使用）。

        Returns:
            {symbol: volatility_tier} 快照，不修改内部状态
        """
        return self._do_recompute(
            as_of_date=as_of_date,
            lookback_days=lookback_days or self._lookback,
            max_workers=4,
            inplace=False,
        )

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _load_constituents(self) -> None:
        """从 CSV 或内置迷你列表加载成分股。"""
        if self._universe_file and self._universe_file.exists():
            records = load_from_csv(self._universe_file)
            if not records:
                logger.warning(
                    f"[universe] universe.csv found but empty ({self._universe_file.stat().st_size} bytes), "
                    f"falling back to builtin list"
                )
                records = self._builtin_universe()
        else:
            records = self._builtin_universe()
            logger.info(
                f"[universe] no universe.csv found, using builtin {len(records)} symbols"
            )

        self._constituents = records
        self._rebuild_meta(records)

    def _rebuild_meta(self, records: list[dict[str, str]]) -> None:
        """从成分股列表重建 meta_map（不含波动率，需单独计算）。"""
        meta_map: dict[str, SymbolMeta] = {}
        for rec in records:
            sym = rec["symbol"].upper()
            if sym in meta_map:
                # 已存在 → 合并 index_membership
                meta_map[sym].index_membership.append(rec["index"])
            else:
                meta_map[sym] = SymbolMeta(
                    symbol=sym,
                    index_membership=[rec["index"]],
                    sector=rec.get("sector", "Unknown"),
                    market_cap_tier="large",   # Phase 5 初期默认
                    volatility_tier="unknown",
                    group_id="UNKNOWN",
                )

        # 用原有波动率（若存在）恢复分组
        for sym, new_meta in meta_map.items():
            if sym in self._meta_map:
                old_tier = self._meta_map[sym].volatility_tier
                if old_tier != "unknown":
                    new_meta.volatility_tier = old_tier
                    new_meta.group_id = build_group_id(
                        new_meta.index_membership, old_tier
                    )

        self._meta_map = meta_map

    def _do_recompute(
        self,
        as_of_date: date | None,
        lookback_days: int,
        max_workers: int,
        inplace: bool,
    ) -> dict[str, str]:
        """通用的波动率分层计算（inplace=True 时更新 meta_map，否则只返回快照）。

        Returns:
            {symbol: tier} 字典
        """
        symbols = list(self._meta_map.keys())
        tier_map: dict[str, str] = {}

        def _calc(sym: str) -> tuple[str, str]:
            try:
                if as_of_date is not None:
                    end = as_of_date
                    start = end - timedelta(days=lookback_days + 30)  # 多拿一些保证 ATR 预热
                    df = self._store.get_bars(sym, start, end)
                else:
                    df = self._store.get_latest_n_bars(sym, n=lookback_days + 30)

                tier = compute_volatility_tier(df, lookback=lookback_days // 3)
            except Exception as e:
                logger.debug(f"[universe] vol tier calc failed for {sym}: {e}")
                tier = "unknown"
            return sym, tier

        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = {ex.submit(_calc, s): s for s in symbols}
            for f in as_completed(futures):
                sym, tier = f.result()
                tier_map[sym] = tier

        if inplace:
            for sym, tier in tier_map.items():
                if sym in self._meta_map:
                    meta = self._meta_map[sym]
                    meta.volatility_tier = tier
                    meta.group_id = build_group_id(meta.index_membership, tier)
            logger.info(
                f"[universe] volatility tiers recomputed for {len(symbols)} symbols"
            )

        return tier_map

    @staticmethod
    def _merge_constituents(
        sp500: list[dict], ndx100: list[dict]
    ) -> list[dict[str, str]]:
        """合并两个成分股列表，标记各自归属（不去重，由 _rebuild_meta 处理重复）。"""
        merged = []
        seen_sp500: set[str] = set()
        seen_ndx: set[str] = set()

        for rec in sp500:
            sym = rec["symbol"].upper()
            if sym not in seen_sp500:
                merged.append({**rec, "index": "SP500"})
                seen_sp500.add(sym)

        for rec in ndx100:
            sym = rec["symbol"].upper()
            if sym not in seen_ndx:
                merged.append({**rec, "index": "NASDAQ100"})
                seen_ndx.add(sym)

        return merged

    @staticmethod
    def _find_universe_file() -> Path | None:
        """从 cwd 向上查找 config/universe.csv。"""
        here = Path.cwd()
        for parent in [here, *here.parents]:
            candidate = parent / "config" / "universe.csv"
            if candidate.exists():
                return candidate
        return None

    @staticmethod
    def _builtin_universe() -> list[dict[str, str]]:
        """内置最小标的列表（供无 CSV 时使用）。"""
        return [
            {"symbol": "AAPL",  "sector": "Information Technology", "index": "NASDAQ100"},
            {"symbol": "MSFT",  "sector": "Information Technology", "index": "NASDAQ100"},
            {"symbol": "NVDA",  "sector": "Information Technology", "index": "NASDAQ100"},
            {"symbol": "TSLA",  "sector": "Consumer Discretionary",  "index": "NASDAQ100"},
            {"symbol": "AMZN",  "sector": "Consumer Discretionary",  "index": "NASDAQ100"},
            {"symbol": "META",  "sector": "Communication Services",  "index": "NASDAQ100"},
            {"symbol": "GOOGL", "sector": "Communication Services",  "index": "NASDAQ100"},
            {"symbol": "JPM",   "sector": "Financials",              "index": "SP500"},
            {"symbol": "JNJ",   "sector": "Health Care",             "index": "SP500"},
            {"symbol": "PG",    "sector": "Consumer Staples",        "index": "SP500"},
            {"symbol": "SPY",   "sector": "ETF",                     "index": "SP500"},
        ]
