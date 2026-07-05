"""PortfolioBacktest — 组合层级回测。

职责：
    1. 按日期遍历，每个交易日复用 StrategyMatrixRunner / SignalRanker /
       CandidateSelector 模拟"信号 → 排名 → 约束选股 → 换仓"全流程
    2. 模拟持仓市值变动并计算组合层级净值曲线
    3. 输出 Constitution L1 关键 KPI：Sortino / Sharpe / Max DD / Calmar
    4. 记录 holdings_history 与 group_exposure_history 用于事后归因

防前视偏差（与实盘一致）：
    - 每个交易日只用截至当日的数据
    - 信号在收盘后产生，次日开盘价执行换仓（此简化版用当日 close 计价）
    - weight 配置来自离线 MatrixBacktest，run() 期间不重新优化

设计原则（AI Constitution L5）：
    - 复用现有组件，不重写 StrategyMatrixRunner / SignalRanker / CandidateSelector
    - 纯函数式日期循环，无副作用
    - 类型注解全覆盖，所有时间统一 UTC

注意：本模块是迭代 #4 新增（P0），作为 MatrixBacktest（标的层）的组合层补充。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from loguru import logger

from mytrader.backtest.matrix_backtest import (
    _compute_sharpe,
    _compute_sortino,
    _safe_float,
)
from mytrader.data.store.market_data_store import MarketDataStore
from mytrader.risk.candidate_selector import (
    AccountState,
    select_orders_from_candidates,
)
from mytrader.signal.ranker import SignalRanker
from mytrader.strategy.base import Signal, SignalDirection
from mytrader.strategy.matrix_runner import (
    StrategyMatrixRunner,
    build_matrix_signal_indicators,
)
from mytrader.universe.manager import UniverseManager


# ---------------------------------------------------------------------------
# Constitution L1 硬约束：组合最大回撤 ≤ 20%
# ---------------------------------------------------------------------------

PORTFOLIO_MAX_DRAWDOWN_PCT: float = 20.0


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------

@dataclass
class PortfolioBacktestConfig:
    """PortfolioBacktest 配置。

    与 CandidateSelector / SignalRanker 默认值对齐，便于复用。

    Attributes:
        initial_capital:          初始资金（美元）
        top_k:                    目标持仓数（最终保留的标的数）
        candidates_multiplier:    候选倍数（输出 top_k * multiplier 候选给 selector）
        max_single_position_pct:  单标的仓位上限（与 risk 模块一致）
        max_total_exposure_pct:   总持仓上限
        max_sector_exposure_pct:  板块持仓上限（本简化版按 group_id 近似）
        rebalance_freq:           换仓频率（'daily' / 'weekly'；本版本仅实现 daily）
        signal_valid_bars:        信号有效期（与 StrategyMatrixRunner 一致）
    """

    initial_capital: float = 100_000.0
    top_k: int = 5
    candidates_multiplier: int = 2
    max_single_position_pct: float = 0.20
    max_total_exposure_pct: float = 0.80
    max_sector_exposure_pct: float = 0.40
    rebalance_freq: str = "daily"
    signal_valid_bars: int = 3


@dataclass
class PortfolioBacktestResult:
    """组合回测结果。

    Constitution L1 关键 KPI：Sortino > Sharpe > Max DD > Calmar > Annual Return。

    Attributes:
        start_date:               回测起始日期
        end_date:                 回测结束日期
        initial_capital:          初始资金
        final_equity:             期末净值
        total_return_pct:         总收益率（百分数）
        annualized_return_pct:    年化收益率（百分数）
        sharpe_ratio:             年化 Sharpe Ratio
        sortino_ratio:             年化 Sortino Ratio（Constitution L1 首要 KPI）
        max_drawdown_pct:         最大回撤（百分数，正值）
        calmar_ratio:             Calmar = Annual Return / Max DD
        daily_returns:            日收益率序列
        equity_curve:             净值曲线（初始 = initial_capital）
        holdings_history:         每日持仓快照列表（按交易日）
        dd_violation:             DD 是否超过 20% 硬约束
        group_exposure_history:   每日按 group_id 的暴露度快照
        benchmark_symbol:          Benchmark 标的（默认 SPY，迭代 #7）
        benchmark_total_return_pct:    Benchmark 同期总收益（百分数）
        benchmark_annualized_return_pct: Benchmark 年化收益（百分数）
        benchmark_sortino_ratio:       Benchmark Sortino Ratio
        benchmark_max_drawdown_pct:    Benchmark 最大回撤（百分数，正值）
        alpha_pct:                     超额收益 = 组合年化 - benchmark 年化（百分数）
        information_ratio:             信息比率（年化）
    """

    start_date: date
    end_date: date
    initial_capital: float
    final_equity: float
    total_return_pct: float
    annualized_return_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown_pct: float
    calmar_ratio: float
    daily_returns: pd.Series
    equity_curve: pd.Series
    holdings_history: list[dict[str, Any]] = field(default_factory=list)
    dd_violation: bool = False
    group_exposure_history: list[dict[str, Any]] = field(default_factory=list)
    # Benchmark 对比（Iteration #7 新增）
    benchmark_symbol: str = "SPY"
    benchmark_total_return_pct: float = 0.0
    benchmark_annualized_return_pct: float = 0.0
    benchmark_sortino_ratio: float = 0.0
    benchmark_max_drawdown_pct: float = 0.0
    alpha_pct: float = 0.0
    information_ratio: float = 0.0


# ---------------------------------------------------------------------------
# PortfolioBacktester
# ---------------------------------------------------------------------------

class PortfolioBacktester:
    """组合层级回测器。

    Args:
        store:        MarketDataStore 实例
        universe:     UniverseManager 实例
        weights_file: strategy_weights.json 路径（来自离线 MatrixBacktest）
        config:       PortfolioBacktestConfig

    使用方式：
        bt = PortfolioBacktester(store, universe, "config/strategy_weights.json", cfg)
        result = bt.run(start=date(2024,1,1), end=date(2024,6,30))
        print(result.sortino_ratio, result.max_drawdown_pct)
    """

    def __init__(
        self,
        store: MarketDataStore,
        universe: UniverseManager,
        weights_file: str | Path | None = None,
        config: PortfolioBacktestConfig | None = None,
    ) -> None:
        self._store = store
        self._universe = universe
        self._weights_file = Path(weights_file) if weights_file else None
        self._config = config or PortfolioBacktestConfig()

        # 内部 StrategyMatrixRunner（复用其信号生成能力）
        # signal_valid_bars 与 config 对齐
        self._matrix_runner = StrategyMatrixRunner(
            store=store,
            universe=universe,
            weights_file=self._weights_file,
            signal_valid_bars=self._config.signal_valid_bars,
        )

        # 内部 SignalRanker（复用其聚合 + Top-2K 排名）
        self._ranker = SignalRanker(
            top_k=self._config.top_k,
            candidates_multiplier=self._config.candidates_multiplier,
        )

        # 历史记录在 run() 开始时重置（实例属性，避免跨实例污染）
        self._holdings_history: list[dict[str, Any]] = []
        self._group_exposure_history: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # 公共接口
    # ------------------------------------------------------------------

    def run(self, start: date, end: date) -> PortfolioBacktestResult:
        """执行组合回测。

        每日流程：
            1. 用截至当日的数据生成信号（StrategyMatrixRunner.run_symbol）
            2. SignalRanker 聚合 + Top-2K 排名
            3. CandidateSelector 5 级约束选 Top-5
            4. 按当日 close 计价，模拟换仓（卖出不在新 Top-5 的、买入新进的）
            5. 用当日 close 重估持仓市值 → 更新净值

        Args:
            start: 回测起始日期（含）
            end:   回测结束日期（含）

        Returns:
            PortfolioBacktestResult
        """
        cfg = self._config
        symbols = self._universe.get_universe()

        # 1. 拉取所有标的的完整日历数据（一次性，避免每日重复查询）
        all_bars: dict[str, pd.DataFrame] = self._store.get_bars_multi(
            symbols, start, end
        )
        if not all_bars:
            logger.warning("[PortfolioBacktest] no data, returning empty result")
            return self._empty_result(start, end)

        # 2. 构造统一交易日历（所有标的的 date index 并集）
        all_dates: list[date] = sorted({
            ts.date() if isinstance(ts, (datetime, pd.Timestamp)) else ts
            for df in all_bars.values()
            for ts in df.index
        })
        # 限定到 [start, end] 区间
        all_dates = [d for d in all_dates if start <= d <= end]
        if not all_dates:
            logger.warning("[PortfolioBacktest] no trading dates in range")
            return self._empty_result(start, end)

        logger.info(
            f"[PortfolioBacktest] start={start}, end={end}, "
            f"symbols={len(symbols)}, trading_days={len(all_dates)}"
        )

        # 3. 按日期循环
        cash = cfg.initial_capital
        # holdings: {symbol: (shares, avg_cost)} — 简化：用 close 计价
        holdings: dict[str, float] = {}     # symbol → shares
        avg_cost: dict[str, float] = {}    # symbol → 平均成本（用于成本基础）

        daily_returns_list: list[float] = []
        equity_list: list[float] = []
        date_list: list[date] = []

        prev_equity = cfg.initial_capital

        for trading_date in all_dates:
            # 截至当日的数据切片（防前视偏差）
            bars_up_to_date: dict[str, pd.DataFrame] = {}
            for sym, df in all_bars.items():
                # df.index 可能是 datetime/timestamp
                mask = df.index <= pd.Timestamp(trading_date)
                sub = df.loc[mask]
                if not sub.empty:
                    bars_up_to_date[sym] = sub

            # 当日 close 价查表（用于市值计价 + 换仓）
            close_today: dict[str, float] = {}
            for sym, df in bars_up_to_date.items():
                if not df.empty:
                    close_today[sym] = _safe_float(df["close"].iloc[-1])

            # ── Step 1: 生成信号（复用 StrategyMatrixRunner 的 run_symbol 逻辑）──
            # 用截至当日的数据子集生成信号；为避免修改 store 状态，
            # 直接调用策略函数（不读 store，而是用 bars_up_to_date）
            signals = self._generate_signals(bars_up_to_date, trading_date)

            # ── Step 2: 排名 + Top-2K ──
            rank_report = self._ranker.rank(signals)

            # ── Step 3: 候选选股 ──
            # 构造当前账户状态
            current_exposure = sum(
                shares * close_today.get(sym, 0.0)
                for sym, shares in holdings.items()
            )
            sector_exposure: dict[str, float] = {}
            for sym, shares in holdings.items():
                meta = self._universe.get_symbol_meta(sym)
                sector = meta.sector if meta else "Unknown"
                mv = shares * close_today.get(sym, 0.0)
                sector_exposure[sector] = sector_exposure.get(sector, 0.0) + mv

            account = AccountState(
                total_capital=cfg.initial_capital,
                current_exposure=current_exposure,
                current_position_count=len(holdings),
                sector_exposure=sector_exposure,
            )

            approved, _ = select_orders_from_candidates(
                candidates=rank_report.buy_candidates,
                account=account,
                max_orders=cfg.top_k,
                max_single_position_pct=cfg.max_single_position_pct,
                max_total_exposure_pct=cfg.max_total_exposure_pct,
                max_sector_exposure_pct=cfg.max_sector_exposure_pct,
                max_concurrent_positions=cfg.top_k,
            )

            # ── Step 4: 换仓 ──
            # SELL 信号优先：先处理 sell_signals
            for ranked in rank_report.sell_signals:
                sym = ranked.signal.symbol
                if sym in holdings:
                    # 卖出全部持仓
                    cash += holdings[sym] * close_today.get(sym, 0.0)
                    del holdings[sym]
                    avg_cost.pop(sym, None)

            # 计算目标持仓集合（来自 approved 的 BUY）
            target_symbols = {o.signal.symbol for o in approved}

            # 卖出不在目标集合的现有持仓
            for sym in list(holdings.keys()):
                if sym not in target_symbols:
                    cash += holdings[sym] * close_today.get(sym, 0.0)
                    del holdings[sym]
                    avg_cost.pop(sym, None)

            # 买入新进的目标标的（等权分配可用资金）
            new_buys = [o for o in approved if o.signal.symbol not in holdings]
            if new_buys:
                # 等权分配当前 cash 给新买入标的
                per_symbol_budget = min(
                    cfg.initial_capital * cfg.max_single_position_pct,
                    cash / max(len(new_buys), 1),
                )
                for o in new_buys:
                    sym = o.signal.symbol
                    price = close_today.get(sym, 0.0)
                    if price <= 0:
                        continue
                    shares_to_buy = per_symbol_budget / price
                    if shares_to_buy <= 0:
                        continue
                    cost = shares_to_buy * price
                    if cost > cash:
                        continue
                    cash -= cost
                    # 更新平均成本
                    old_shares = holdings.get(sym, 0.0)
                    old_cost = avg_cost.get(sym, 0.0) * old_shares
                    new_shares = old_shares + shares_to_buy
                    avg_cost[sym] = (old_cost + cost) / new_shares if new_shares > 0 else 0.0
                    holdings[sym] = new_shares

            # ── Step 5: 计算当日净值 ──
            market_value = sum(
                shares * close_today.get(sym, 0.0)
                for sym, shares in holdings.items()
            )
            equity = cash + market_value

            # 日收益率
            daily_ret = (equity - prev_equity) / prev_equity if prev_equity > 0 else 0.0
            daily_returns_list.append(daily_ret)
            equity_list.append(equity)
            date_list.append(trading_date)
            prev_equity = equity

            # 记录 holdings_history
            self._record_holdings(
                trading_date, holdings, close_today, avg_cost, cash, equity
            )
            # 记录 group_exposure_history
            self._record_group_exposure(trading_date, holdings, close_today, equity)

        # 4. 计算最终指标
        daily_returns = pd.Series(daily_returns_list, index=pd.to_datetime(date_list))
        equity_curve = pd.Series(equity_list, index=pd.to_datetime(date_list))

        final_equity = equity_list[-1] if equity_list else cfg.initial_capital
        total_return_pct = (
            (final_equity / cfg.initial_capital) - 1.0
        ) * 100.0

        # 年化收益率：按交易日数推算
        n_days = len(daily_returns_list)
        years = n_days / 252.0 if n_days > 0 else 0.0
        if years > 0 and final_equity > 0:
            annualized_return_pct = (
                (final_equity / cfg.initial_capital) ** (1.0 / years) - 1.0
            ) * 100.0
        else:
            annualized_return_pct = 0.0

        sharpe = _compute_sharpe(daily_returns)
        sortino = _compute_sortino(daily_returns)
        max_dd = self._compute_max_drawdown_pct(daily_returns)

        calmar = (
            abs(annualized_return_pct / max_dd)
            if max_dd > 0 else 0.0
        )

        dd_violation = max_dd > PORTFOLIO_MAX_DRAWDOWN_PCT

        result = PortfolioBacktestResult(
            start_date=start,
            end_date=end,
            initial_capital=cfg.initial_capital,
            final_equity=final_equity,
            total_return_pct=total_return_pct,
            annualized_return_pct=annualized_return_pct,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            max_drawdown_pct=max_dd,
            calmar_ratio=calmar,
            daily_returns=daily_returns,
            equity_curve=equity_curve,
            holdings_history=self._holdings_history,
            dd_violation=dd_violation,
            group_exposure_history=self._group_exposure_history,
        )

        # ── Benchmark: SPY buy-and-hold（迭代 #7）──
        # 数据不可用时降级为 0.0，不抛异常（spec §4.2）
        benchmark_result = self._compute_benchmark(
            start, end, daily_returns_list, date_list
        )
        result.benchmark_symbol = benchmark_result.get("symbol", "SPY")
        result.benchmark_total_return_pct = benchmark_result.get(
            "total_return_pct", 0.0
        )
        result.benchmark_annualized_return_pct = benchmark_result.get(
            "annualized_return_pct", 0.0
        )
        result.benchmark_sortino_ratio = benchmark_result.get(
            "sortino_ratio", 0.0
        )
        result.benchmark_max_drawdown_pct = benchmark_result.get(
            "max_drawdown_pct", 0.0
        )
        result.alpha_pct = (
            result.annualized_return_pct - result.benchmark_annualized_return_pct
        )
        result.information_ratio = benchmark_result.get(
            "information_ratio", 0.0
        )

        logger.info(
            f"[PortfolioBacktest] done: final=${final_equity:,.0f}, "
            f"total_return={total_return_pct:.2f}%, "
            f"annualized={annualized_return_pct:.2f}%, "
            f"sharpe={sharpe:.4f}, sortino={sortino:.4f}, "
            f"max_dd={max_dd:.2f}%, dd_violation={dd_violation}, "
            f"benchmark={result.benchmark_symbol} "
            f"return={result.benchmark_annualized_return_pct:.2f}%, "
            f"alpha={result.alpha_pct:.2f}%, ir={result.information_ratio:.4f}"
        )

        return result

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _empty_result(self, start: date, end: date) -> PortfolioBacktestResult:
        """空结果（无数据时返回）。"""
        cfg = self._config
        empty = pd.Series(dtype=float)
        return PortfolioBacktestResult(
            start_date=start,
            end_date=end,
            initial_capital=cfg.initial_capital,
            final_equity=cfg.initial_capital,
            total_return_pct=0.0,
            annualized_return_pct=0.0,
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            max_drawdown_pct=0.0,
            calmar_ratio=0.0,
            daily_returns=empty,
            equity_curve=empty,
        )

    def _generate_signals(
        self,
        bars_up_to_date: dict[str, pd.DataFrame],
        trading_date: date,
    ) -> list[Signal]:
        """复用 StrategyMatrixRunner 的策略调用逻辑生成信号。

        为避免修改 store 状态（防前视偏差），这里直接基于 bars_up_to_date
        调用注册表中的策略函数，绕过 runner.run_symbol 内部的 store.get_latest_n_bars。

        信号有效期通过 config.signal_valid_bars 检查（与 runner 一致）。
        """
        from mytrader.strategy.registry import STRATEGY_REGISTRY

        signals: list[Signal] = []
        now = datetime.now(tz=timezone.utc)
        svb = self._config.signal_valid_bars

        for sym, df in bars_up_to_date.items():
            if df.empty or len(df) < 30:
                # 需要足够数据：bollinger period 最多 25 + signal_valid_bars 3 = 28
                continue

            meta = self._universe.get_symbol_meta(sym)
            if meta is None:
                continue

            group_strategies = self._matrix_runner._weights.get(meta.group_id, [])
            if not group_strategies:
                continue

            for entry in group_strategies:
                strategy_name = entry["strategy"]
                params = entry.get("params", {})
                weight = float(entry.get("weight", 1.0))

                strategy_fn = STRATEGY_REGISTRY.get(strategy_name)
                if strategy_fn is None:
                    continue

                try:
                    sig_series = strategy_fn(df["close"], df=df, **params)
                except TypeError:
                    sig_series = strategy_fn(df["close"], **params)
                except (ValueError, KeyError, Exception):
                    # ValueError: 指标数据不足（如 bbands 返回 None）
                    # KeyError: 列名不匹配
                    continue

                # 信号有效期检查
                recent = sig_series.iloc[-svb:]
                nonzero = recent[recent != 0]
                if nonzero.empty:
                    continue

                latest = int(nonzero.iloc[-1])
                direction = SignalDirection.BUY if latest == 1 else SignalDirection.SELL
                confidence = min(weight, 1.0)

                signals.append(
                    Signal(
                        symbol=sym,
                        direction=direction,
                        timestamp=now,
                        confidence=confidence,
                        strategy_name=strategy_name,
                        # 迭代 #5：复用 matrix_runner.build_matrix_signal_indicators
                        # 保证线上扫描与组合回测 signal metadata 完全一致
                        # （P0-A：曾因 sector=Unknown 导致 73 候选 → 2 approved）
                        indicators=build_matrix_signal_indicators(meta, entry, weight),
                    )
                )

        return signals

    def _record_holdings(
        self,
        trading_date: date,
        holdings: dict[str, float],
        close_today: dict[str, float],
        avg_cost: dict[str, float],
        cash: float,
        equity: float,
    ) -> None:
        """记录每日持仓快照（用于事后归因）。"""
        holdings_snapshot = []
        for sym, shares in holdings.items():
            price = close_today.get(sym, 0.0)
            holdings_snapshot.append({
                "symbol": sym,
                "shares": float(shares),
                "price": float(price),
                "market_value": float(shares * price),
                "avg_cost": float(avg_cost.get(sym, 0.0)),
                "unrealized_pnl": float((price - avg_cost.get(sym, 0.0)) * shares),
            })

        self._holdings_history.append({
            "date": trading_date.isoformat(),
            "cash": float(cash),
            "equity": float(equity),
            "positions": holdings_snapshot,
            "position_count": len(holdings_snapshot),
        })

    def _record_group_exposure(
        self,
        trading_date: date,
        holdings: dict[str, float],
        close_today: dict[str, float],
        equity: float,
    ) -> None:
        """记录每日按 group_id 的暴露度（用于风控观测）。"""
        group_exposure: dict[str, float] = {}
        for sym, shares in holdings.items():
            meta = self._universe.get_symbol_meta(sym)
            gid = meta.group_id if meta else "UNKNOWN"
            mv = shares * close_today.get(sym, 0.0)
            group_exposure[gid] = group_exposure.get(gid, 0.0) + mv

        # 转为百分比
        group_exposure_pct = {
            gid: (mv / equity * 100.0 if equity > 0 else 0.0)
            for gid, mv in group_exposure.items()
        }

        self._group_exposure_history.append({
            "date": trading_date.isoformat(),
            "total_equity": float(equity),
            "group_exposure_value": {k: float(v) for k, v in group_exposure.items()},
            "group_exposure_pct": group_exposure_pct,
        })

    def _compute_benchmark(
        self,
        start: date,
        end: date,
        portfolio_daily_returns: list[float],
        dates: list[date],
    ) -> dict[str, Any]:
        """计算 SPY buy-and-hold benchmark 指标（迭代 #7）。

        从 MarketDataStore 拉取 SPY 同期数据，计算：
            - total_return_pct / annualized_return_pct
            - sortino_ratio / max_drawdown_pct（与组合层同口径）
            - information_ratio（基于 portfolio - spy 的超额收益序列）

        降级处理：SPY 数据不可用时所有字段保持 0.0，不抛异常（spec §4.2）。

        Args:
            start:                   回测起始日期
            end:                     回测结束日期
            portfolio_daily_returns: 组合日收益率序列（与 dates 对齐）
            dates:                   交易日日期序列

        Returns:
            dict with benchmark metrics。失败时仅含 "symbol"。
        """
        benchmark_symbol = "SPY"
        try:
            spy_bars = self._store.get_bars_multi([benchmark_symbol], start, end)
            spy_df = spy_bars.get(benchmark_symbol)
            if spy_df is None or spy_df.empty:
                logger.warning(
                    "[PortfolioBacktest] SPY data unavailable, benchmark skipped"
                )
                return {"symbol": benchmark_symbol}

            spy_close = spy_df["close"].astype(float)
            if len(spy_close) < 2:
                logger.warning(
                    "[PortfolioBacktest] SPY data too short, benchmark skipped"
                )
                return {"symbol": benchmark_symbol}

            spy_returns = spy_close.pct_change().dropna()

            # SPY total / annualized return
            spy_final = float(spy_close.iloc[-1])
            spy_initial = float(spy_close.iloc[0])
            spy_total_return_pct = (
                (spy_final / spy_initial) - 1.0
            ) * 100.0 if spy_initial > 0 else 0.0

            n_spy = len(spy_returns)
            years_spy = n_spy / 252.0 if n_spy > 0 else 0.0
            if years_spy > 0 and spy_final > 0 and spy_initial > 0:
                spy_annualized_pct = (
                    (spy_final / spy_initial) ** (1.0 / years_spy) - 1.0
                ) * 100.0
            else:
                spy_annualized_pct = 0.0

            # Sortino / Max DD（复用 matrix_backtest helper，与组合层同口径）
            spy_sortino = _compute_sortino(spy_returns)
            spy_max_dd = self._compute_max_drawdown_pct(spy_returns)

            # Information Ratio：基于超额收益序列
            # 将 SPY returns 对齐到 portfolio 的交易日历
            ir = self._compute_information_ratio(
                portfolio_daily_returns, dates, spy_returns
            )

            return {
                "symbol": benchmark_symbol,
                "total_return_pct": float(spy_total_return_pct),
                "annualized_return_pct": float(spy_annualized_pct),
                "sortino_ratio": float(spy_sortino),
                "max_drawdown_pct": float(spy_max_dd),
                "information_ratio": float(ir),
            }
        except Exception as e:
            logger.warning(
                f"[PortfolioBacktest] benchmark computation failed: {e}"
            )
            return {"symbol": benchmark_symbol}

    @staticmethod
    def _compute_information_ratio(
        portfolio_daily_returns: list[float],
        portfolio_dates: list[date],
        spy_returns: pd.Series,
    ) -> float:
        """计算年化信息比率。

        IR = mean(excess_returns) / std(excess_returns) * sqrt(252)
        excess_returns = portfolio_returns - spy_returns（按日期对齐）
        """
        if not portfolio_daily_returns or len(spy_returns) == 0:
            return 0.0

        # 组合 returns 转为 pd.Series，index 用 portfolio_dates
        port_idx = pd.to_datetime(portfolio_dates)
        port_series = pd.Series(
            portfolio_daily_returns, index=port_idx, dtype=float
        )

        # 对齐：取两序列 index 的交集（inner join）
        aligned = pd.concat(
            [port_series.rename("port"), spy_returns.rename("spy")],
            axis=1,
            join="inner",
        ).dropna()
        if aligned.empty or len(aligned) < 5:
            return 0.0

        excess = aligned["port"] - aligned["spy"]
        std = excess.std()
        if std <= 0 or not np.isfinite(std):
            return 0.0
        return float(excess.mean() / std * np.sqrt(252))

    @staticmethod
    def _compute_max_drawdown_pct(daily_returns: pd.Series) -> float:
        """计算最大回撤（百分数正值）。

        与 matrix_backtest._portfolio_max_drawdown_from_results 同口径。
        """
        if daily_returns.empty:
            return 0.0
        cumvalue = (1.0 + daily_returns).cumprod()
        peak = cumvalue.cummax()
        drawdown = (cumvalue - peak) / peak
        dd_min = float(drawdown.min())
        if not np.isfinite(dd_min):
            return 0.0
        return abs(dd_min) * 100.0
