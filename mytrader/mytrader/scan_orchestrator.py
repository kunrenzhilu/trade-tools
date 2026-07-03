"""ScanOrchestrator — 扫描编排器，连接 Data → Strategy → Signal → Risk → Execution。

Phase 4 核心：将 main.py 调度器回调从 lambda logger.info 替换为真实业务逻辑。

数据流：
    DataProvider.get_ohlcv(symbol, lookback)
        → StrategyFn(close, **params) → raw_signals: pd.Series
        → Signal 列表（只取最新一根 bar 的信号）
        → SignalPipeline.run(signals, df)
        → RiskManager.evaluate(filtered_signal, df)
        → Broker.submit(intent, df)
        → PortfolioTracker.process_order(result)
        → NotificationService.notify_order（semi_auto/auto 时推送）

设计原则：
    - 单个 symbol 扫描异常不影响其余 symbol（独立 try-except）
    - 每次扫描前同步 PortfolioTracker → RiskManager 状态
    - EOD check：持仓触碰止损/止盈时生成 SELL 信号
    - 编排器无状态（状态由 PortfolioTracker + Broker 持有），可重入
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, TYPE_CHECKING

import pandas as pd
from loguru import logger

from mytrader.strategy.base import Signal, SignalDirection
from mytrader.strategy.registry import STRATEGY_REGISTRY

if TYPE_CHECKING:
    from mytrader.data.base import DataProvider
    from mytrader.execution.base import BrokerProtocol
    from mytrader.execution.notification import NotificationService
    from mytrader.infra.config import AppConfig
    from mytrader.portfolio.tracker import PortfolioTracker
    from mytrader.risk.manager import RiskManager
    from mytrader.signal.pipeline import SignalPipeline


# ---------------------------------------------------------------------------
# 扫描结果数据类
# ---------------------------------------------------------------------------

@dataclass
class SymbolScanResult:
    """单标的扫描结果。"""

    symbol: str
    signal_direction: str = "HOLD"    # BUY / SELL / HOLD
    order_submitted: bool = False
    order_status: str = ""
    error: str = ""

    @property
    def has_error(self) -> bool:
        return bool(self.error)


@dataclass
class ScanSummary:
    """一次扫描（盘前/盘中/EOD）的汇总。"""

    scan_type: str                          # morning / intraday / eod
    triggered_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    results: list[SymbolScanResult] = field(default_factory=list)

    @property
    def buy_count(self) -> int:
        return sum(1 for r in self.results if r.signal_direction == "BUY")

    @property
    def sell_count(self) -> int:
        return sum(1 for r in self.results if r.signal_direction == "SELL")

    @property
    def order_count(self) -> int:
        return sum(1 for r in self.results if r.order_submitted)

    @property
    def error_count(self) -> int:
        return sum(1 for r in self.results if r.has_error)


# ---------------------------------------------------------------------------
# ScanOrchestrator
# ---------------------------------------------------------------------------

class ScanOrchestrator:
    """扫描编排器，驱动一次完整的"拉数据→信号→风控→执行"循环。

    Args:
        config:       AppConfig（全局配置）
        data_provider:DataProvider 实例（YFinance 或 Alpaca）
        pipeline:     SignalPipeline 实例
        risk_manager: RiskManager 实例
        broker:       BrokerProtocol 实例
        tracker:      PortfolioTracker 实例
        notification: NotificationService 实例（可为 None）
    """

    def __init__(
        self,
        config: "AppConfig",
        data_provider: "DataProvider",
        pipeline: "SignalPipeline",
        risk_manager: "RiskManager",
        broker: "BrokerProtocol",
        tracker: "PortfolioTracker",
        notification: "NotificationService | None" = None,
    ) -> None:
        self._cfg = config
        self._provider = data_provider
        self._pipeline = pipeline
        self._risk = risk_manager
        self._broker = broker
        self._tracker = tracker
        self._notification = notification

        # Phase 5 专属依赖（由 build_orchestrator 注入）
        self._use_phase5: bool = False
        self._universe: Any = None
        self._matrix_runner: Any = None
        self._signal_ranker: Any = None

        # 迭代 #5：pending 订单幂等去重集合
        # 同一 client_order_id 被刷新为 FILLED 后只应调用 tracker.process_order 一次
        self._processed_order_ids: set[str] = set()

    # ------------------------------------------------------------------
    # Public 扫描入口
    # ------------------------------------------------------------------

    def morning_scan(self) -> ScanSummary:
        """盘前扫描（09:35 ET）：生成 BUY/SELL 信号，提交订单。"""
        logger.info("[Orchestrator] === Morning scan started ===")
        summary = self._run_scan("morning")
        logger.info(
            f"[Orchestrator] Morning scan done: "
            f"buy={summary.buy_count} sell={summary.sell_count} "
            f"orders={summary.order_count} errors={summary.error_count}"
        )
        self._notify_scan_result(summary)
        return summary

    def intraday_scan(self) -> ScanSummary:
        """盘中扫描（每 30 分钟）：更新信号，补仓/减仓。"""
        logger.info("[Orchestrator] === Intraday scan started ===")
        summary = self._run_scan("intraday")
        logger.info(
            f"[Orchestrator] Intraday scan done: "
            f"buy={summary.buy_count} sell={summary.sell_count} "
            f"orders={summary.order_count} errors={summary.error_count}"
        )
        self._notify_scan_result(summary)
        return summary

    def eod_check(self) -> ScanSummary:
        """收盘前检查（15:45 ET）：检查止损/止盈，生成平仓单。"""
        logger.info("[Orchestrator] === EOD check started ===")
        summary = self._run_eod_check()
        logger.info(
            f"[Orchestrator] EOD check done: "
            f"sell={summary.sell_count} orders={summary.order_count} "
            f"errors={summary.error_count}"
        )
        self._notify_scan_result(summary)
        return summary

    # ------------------------------------------------------------------
    # 扫描结果通知
    # ------------------------------------------------------------------

    _SCAN_LABEL = {
        "morning": "盘前扫描",
        "intraday": "盘中扫描",
        "eod": "收盘检查",
    }

    def _notify_scan_result(self, summary: ScanSummary) -> None:
        """每次扫描结束后推送结果报告（不受理赔 level/cooldown 限制）。"""
        if self._notification is None:
            return
        try:
            label = self._SCAN_LABEL.get(summary.scan_type, summary.scan_type)
            # 区分已成交 / 信号未成交（风控拒绝或过滤拦截）
            buy_filled = [r.symbol for r in summary.results
                          if r.signal_direction == "BUY" and r.order_submitted]
            buy_blocked = [r.symbol for r in summary.results
                           if r.signal_direction == "BUY" and not r.order_submitted and not r.has_error]
            sell_filled = [r.symbol for r in summary.results
                           if r.signal_direction == "SELL" and r.order_submitted]
            sell_blocked = [r.symbol for r in summary.results
                            if r.signal_direction == "SELL" and not r.order_submitted and not r.has_error]
            err_syms = [r.symbol for r in summary.results if r.has_error]

            lines = [
                f"📊 *{label}报告*",
                f"时间：{summary.triggered_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
                f"信号候选：{len(summary.results)}  下单：{summary.order_count}  错误：{summary.error_count}",
            ]
            if buy_filled:
                lines.append(f"✅ 买入成交：{', '.join(buy_filled[:10])}")
            if buy_blocked:
                lines.append(f"⏸ 买入未成交（风控/过滤拦截）：{', '.join(buy_blocked[:10])}")
            if sell_filled:
                lines.append(f"✅ 卖出成交：{', '.join(sell_filled[:10])}")
            if sell_blocked:
                lines.append(f"⏸ 卖出未成交：{', '.join(sell_blocked[:10])}")
            if err_syms:
                lines.append(f"⚠️ 异常：{', '.join(err_syms[:5])}")
            self._notification.send_message("\n".join(lines))
        except Exception as exc:
            logger.warning(f"[Orchestrator] scan result notification failed: {exc}")

    # ------------------------------------------------------------------
    # 迭代 #5：Pending 订单刷新
    #
    # 问题（P0-B）：AlpacaBroker._submit_auto() 提交后只解析一次状态。若订单
    # 初始状态是 new/accepted/pending_new，本地 cached 为 PENDING，
    # ScanOrchestrator 只在 FILLED 时调用 tracker.process_order()，导致真实
    # paper 账户可能已成交但本地 tracker 仍为空仓。
    #
    # 修复：每次扫描开始前刷新 broker 端 pending 订单，对新变为 FILLED 的订单
    # 调用 tracker.process_order()。幂等性通过 _processed_order_ids 集合保证。
    # 不提交新订单、不取消订单，只做状态同步。
    # ------------------------------------------------------------------

    def _refresh_pending_orders(self) -> int:
        """刷新 broker pending 订单；对新变为 FILLED 的订单更新 tracker。

        Returns:
            本轮新转为 FILLED 并交给 tracker 处理的订单数。
        """
        refresh_fn = getattr(self._broker, "refresh_pending_orders", None)
        if not callable(refresh_fn):
            # PaperBroker 等不支持 refresh，直接跳过（不抛异常）
            return 0

        try:
            refreshed_orders = refresh_fn()
        except Exception as exc:
            logger.warning(
                f"[Orchestrator] broker.refresh_pending_orders failed: {exc}; "
                f"scan continues"
            )
            return 0

        filled_count = 0
        for order_result in refreshed_orders or []:
            # 只处理新变为 FILLED 的订单，且未处理过
            from mytrader.execution.models import OrderStatus as _OS
            if order_result.status != _OS.FILLED:
                continue
            oid = order_result.client_order_id
            if not oid or oid in self._processed_order_ids:
                continue
            try:
                self._tracker.process_order(order_result)
                self._processed_order_ids.add(oid)
                filled_count += 1
                logger.info(
                    f"[Orchestrator] pending order {oid} ({order_result.symbol}) "
                    f"confirmed FILLED via refresh; tracker updated"
                )
            except Exception as exc:
                # tracker 失败不能让扫描失败；下次扫描会重试
                logger.warning(
                    f"[Orchestrator] tracker.process_order failed for {oid}: {exc}"
                )
        if filled_count:
            logger.info(
                f"[Orchestrator] refresh_pending_orders: {filled_count} new FILLED"
            )
        return filled_count

    # ------------------------------------------------------------------
    # Internal scan logic
    # ------------------------------------------------------------------

    def _run_scan(self, scan_type: str) -> ScanSummary:
        """盘前/盘中扫描：Phase 5 链路或 Phase 4 降级。"""
        # 迭代 #5：扫描开始前先刷新 broker pending 订单
        # （将 paper 账户已成交但本地仍 PENDING 的订单补交给 tracker）
        self._refresh_pending_orders()

        if self._use_phase5 and self._matrix_runner is not None:
            return self._run_scan_phase5(scan_type)

        # Phase 4 降级
        self._sync_risk_state()
        symbols = self._cfg.watchlist.symbols
        lookback = self._cfg.watchlist.lookback_days
        summary = ScanSummary(scan_type=scan_type)

        for symbol in symbols:
            result = self._scan_symbol(symbol, lookback)
            summary.results.append(result)

        return summary

    def _run_scan_phase5(self, scan_type: str) -> ScanSummary:
        """Phase 5 链路：MarketDataStore → MatrixRunner → SignalRanker → CandidateSelector → Broker。

        数据流：
            1. StrategyMatrixRunner.run() 扫全标的池 → M×N 条 Signal
            2. SignalRanker.rank() 聚合 + Top-2K 候选
            3. CandidateSelector 递补选出 ≤K 个订单
            4. 每张订单经过 SignalFilter + RiskManager → Broker.submit()
        """
        self._sync_risk_state()
        summary = ScanSummary(scan_type=scan_type)
        lookback = self._cfg.watchlist.lookback_days

        # Step 1: 矩阵扫描
        logger.info(f"[Phase5] Matrix scan: {len(self._universe.get_universe())} symbols...")
        scan_result = self._matrix_runner.run(lookback_days=lookback, max_workers=4)
        logger.info(
            f"[Phase5] Scan done: {scan_result.symbol_count} symbols → "
            f"{len(scan_result.signals)} raw signals "
            f"({len(scan_result.buy_signals)} BUY, {len(scan_result.sell_signals)} SELL)"
        )

        if not scan_result.signals:
            logger.info("[Phase5] No signals today")
            return summary

        # Step 2: 排名 + Top-2K 候选
        ranking = self._signal_ranker.rank(scan_result.signals)
        logger.info(
            f"[Phase5] Ranker: {ranking.total_candidates} signals → "
            f"{len(ranking.buy_candidates)} BUY candidates, "
            f"{len(ranking.sell_signals)} SELL, "
            f"dropped={ranking.dropped_conflicts}"
        )

        # Step 3a: SELL 优先（不受 Top-K 限制）
        for rs in ranking.sell_signals:
            result = self._execute_ranked_signal(rs, lookback)
            summary.results.append(result)

        # Step 3b: CandidateSelector 递补选出 BUY 订单
        from mytrader.risk.candidate_selector import AccountState, select_orders_from_candidates

        account = AccountState(
            total_capital=self._risk.total_capital,
            current_exposure=self._risk.current_exposure,
            current_position_count=self._risk.current_positions_count,
        )
        approved, rejections = select_orders_from_candidates(
            candidates=ranking.buy_candidates,
            account=account,
            max_orders=self._cfg.signal_ranker.top_k,
            max_single_position_pct=self._cfg.risk.max_single_position_pct,
            max_total_exposure_pct=self._cfg.risk.max_total_exposure_pct,
            max_sector_exposure_pct=self._cfg.risk.get("max_sector_exposure_pct", 0.40)
                if isinstance(self._cfg.risk, dict) else getattr(self._cfg.risk, 'max_sector_exposure_pct', 0.40),
            max_concurrent_positions=self._cfg.risk.max_concurrent_positions
                if hasattr(self._cfg.risk, 'max_concurrent_positions') else 5,
            target_position_pct=self._cfg.risk.max_single_position_pct
                if hasattr(self._cfg.risk, 'max_single_position_pct') else 0.20,
        )

        logger.info(
            f"[Phase5] CandidateSelector: {len(ranking.buy_candidates)} candidates → "
            f"{len(approved)} approved, {len(rejections)} rejected"
        )

        # Step 3c: 执行每一张通过约束的订单
        for order in approved:
            result = self._execute_phase5_order(order, lookback)
            summary.results.append(result)

        return summary

    def _execute_ranked_signal(self, rs: Any, lookback_days: int) -> SymbolScanResult:
        """执行一条已排名的 SELL 信号（经过过滤+风控 → Broker）。"""
        from mytrader.signal.ranker import RankedSignal as _RS
        sig = rs.signal if isinstance(rs, _RS) else rs
        symbol = sig.symbol if hasattr(sig, 'symbol') else str(sig)

        result = SymbolScanResult(symbol=symbol)
        try:
            df = self._fetch_data_phase5(symbol, lookback_days)
            if df is None or df.empty:
                result.error = "empty data"
                logger.warning(f"[Phase5] {symbol} SELL skipped: empty data")
                return result

            # 信号过滤
            filtered_signals, filter_result = self._pipeline.run([sig], df)
            if not filtered_signals:
                logger.warning(f"[Phase5] {symbol} SELL skipped: SignalFilter rejected")
                return result

            result.signal_direction = sig.direction.value
            filtered = filtered_signals[0]

            # 风控
            intent = self._risk.evaluate(filtered, df)
            if intent is None:
                logger.warning(f"[Phase5] {symbol} SELL skipped: RiskManager rejected (intent=None)")
                return result

            # 下单
            order_result = self._broker.submit(intent, df)
            result.order_submitted = True
            result.order_status = order_result.status.value

            from mytrader.execution.models import OrderStatus
            if order_result.status == OrderStatus.FILLED:
                self._tracker.process_order(order_result)

            if self._notification is not None:
                try:
                    self._notification.notify_order(order_result)
                except Exception as exc:
                    logger.warning(f"[{symbol}] Notification failed: {exc}")

            logger.info(f"[{symbol}] SELL submitted: {result.order_status}")
        except Exception as exc:
            logger.exception(f"[{symbol}] Phase5 SELL error: {exc}")
            result.error = str(exc)

        return result

    def _execute_phase5_order(self, order: Any, lookback_days: int) -> SymbolScanResult:
        """执行一张 CandidateSelector 通过的订单。"""
        sig = order.signal
        symbol = sig.symbol
        result = SymbolScanResult(symbol=symbol)
        result.signal_direction = sig.direction.value

        try:
            df = self._fetch_data_phase5(symbol, lookback_days)
            if df is None or df.empty:
                result.error = "empty data"
                logger.warning(f"[Phase5] {symbol} BUY skipped: empty data")
                return result

            # 信号过滤
            filtered_signals, filter_result = self._pipeline.run([sig], df)
            if not filtered_signals:
                logger.warning(f"[Phase5] {symbol} BUY skipped: SignalFilter rejected")
                return result

            filtered = filtered_signals[0]

            # 风控
            intent = self._risk.evaluate(filtered, df)
            if intent is None:
                logger.warning(f"[Phase5] {symbol} BUY skipped: RiskManager rejected (intent=None)")
                return result

            # 下单
            order_result = self._broker.submit(intent, df)
            result.order_submitted = True
            result.order_status = order_result.status.value

            from mytrader.execution.models import OrderStatus
            if order_result.status == OrderStatus.FILLED:
                self._tracker.process_order(order_result)

            if self._notification is not None:
                try:
                    self._notification.notify_order(order_result)
                except Exception as exc:
                    logger.warning(f"[{symbol}] Notification failed: {exc}")

            logger.info(
                f"[{symbol}] Phase5 order: {sig.direction.value} "
                f"value=${order.order_value:,.0f} status={order_result.status.value}"
            )
        except Exception as exc:
            logger.exception(f"[{symbol}] Phase5 order error: {exc}")
            result.error = str(exc)

        return result

    def _fetch_data_phase5(self, symbol: str, lookback_days: int) -> pd.DataFrame | None:
        """Phase 5 数据获取：优先读 MarketDataStore 本地库，降级到外部 DataProvider。"""
        # 先尝试本地库
        if self._use_phase5 and hasattr(self._provider, 'get_latest_n_bars'):
            try:
                df = self._provider.get_latest_n_bars(symbol, n=lookback_days)
                if not df.empty:
                    return df
            except Exception:
                pass  # 降级到外部 API

        # 降级：走外部 DataProvider
        return self._fetch_data(symbol, lookback_days)

    def _scan_symbol(self, symbol: str, lookback_days: int) -> SymbolScanResult:
        """扫描单个标的：拉数据 → 信号 → 风控 → 执行。"""
        result = SymbolScanResult(symbol=symbol)

        try:
            # 1. 拉取历史数据
            df = self._fetch_data(symbol, lookback_days)
            if df is None or df.empty:
                result.error = "empty data"
                return result

            # 2. 策略信号
            signals = self._generate_signals(symbol, df)
            if not signals:
                return result  # HOLD

            # 3. 信号过滤
            filtered_signals, filter_result = self._pipeline.run(signals, df)
            logger.debug(
                f"[{symbol}] Signal filter: "
                f"in={filter_result.original_signal_count} "
                f"out={filter_result.passed_count}"
            )

            if not filtered_signals:
                return result  # 全部被过滤

            # 4. 取第一个通过过滤的信号（理论上一个 symbol 只有 1 个信号）
            filtered = filtered_signals[0]
            result.signal_direction = filtered.source_signal.direction.value

            if filtered.source_signal.direction == SignalDirection.HOLD:
                return result

            # 5. 风控评估
            intent = self._risk.evaluate(filtered, df)
            if intent is None:
                logger.info(f"[{symbol}] Order rejected by risk manager")
                return result

            # 6. 提交订单
            order_result = self._broker.submit(intent, df)
            result.order_submitted = True
            result.order_status = order_result.status.value

            # 7. 更新持仓（仅 FILLED 状态时生效；PENDING 在手动确认后由 tracker 更新）
            from mytrader.execution.models import OrderStatus
            if order_result.status == OrderStatus.FILLED:
                self._tracker.process_order(order_result)

            # 8. 通知推送（semi_auto 模式下 broker 已 PENDING，由此推送供人工确认）
            if self._notification is not None:
                try:
                    self._notification.notify_order(order_result)
                except Exception as exc:
                    logger.warning(f"[{symbol}] Notification failed: {exc}")

            logger.info(
                f"[{symbol}] Order submitted: "
                f"{filtered.source_signal.direction.value} "
                f"{intent.quantity} @ ~${intent.entry_price:.2f} "
                f"status={order_result.status.value}"
            )

        except Exception as exc:
            logger.exception(f"[{symbol}] Scan error: {exc}")
            result.error = str(exc)

        return result

    def _run_eod_check(self) -> ScanSummary:
        """EOD：检查持仓是否触碰止损/止盈，生成平仓单。"""
        # 迭代 #5：EOD 前也刷新一次 pending，避免止损判断基于过时持仓
        self._refresh_pending_orders()

        self._sync_risk_state()
        summary = ScanSummary(scan_type="eod")

        open_positions = self._tracker.open_positions
        if not open_positions:
            logger.info("[Orchestrator] EOD: no open positions")
            return summary

        now = datetime.now(timezone.utc)
        lookback = self._cfg.watchlist.lookback_days

        for symbol, position in list(open_positions.items()):
            result = SymbolScanResult(symbol=symbol)
            try:
                # 拉最近价格
                df = self._fetch_data(symbol, lookback_days=5)
                if df is None or df.empty:
                    result.error = "empty data"
                    summary.results.append(result)
                    continue

                latest_close = float(df.iloc[-1]["close"])
                avg_cost = position.avg_cost
                stop_loss = position.stop_loss_price
                take_profit = position.take_profit_price

                should_close = False
                close_reason = ""

                # 止损检查
                if stop_loss and stop_loss > 0 and latest_close <= stop_loss:
                    should_close = True
                    close_reason = f"stop_loss triggered: close={latest_close:.2f} <= sl={stop_loss:.2f}"

                # 止盈检查
                if (
                    take_profit
                    and take_profit > 0
                    and latest_close >= take_profit
                ):
                    should_close = True
                    close_reason = f"take_profit triggered: close={latest_close:.2f} >= tp={take_profit:.2f}"

                if should_close:
                    logger.info(f"[{symbol}] EOD close: {close_reason}")
                    result.signal_direction = "SELL"

                    # 构造 SELL 信号 → 经过 RiskManager 生成 intent
                    sell_signal = Signal(
                        symbol=symbol,
                        direction=SignalDirection.SELL,
                        timestamp=now,
                        confidence=1.0,
                        strategy_name="eod_stop_check",
                        price_hint=latest_close,
                    )
                    from mytrader.signal.models import FilteredSignal
                    filtered = FilteredSignal(source_signal=sell_signal)
                    intent = self._risk.evaluate(filtered, df, now=now)

                    if intent is not None:
                        order_result = self._broker.submit(intent, df)
                        result.order_submitted = True
                        result.order_status = order_result.status.value

                        from mytrader.execution.models import OrderStatus
                        if order_result.status == OrderStatus.FILLED:
                            self._tracker.process_order(order_result)

                        if self._notification is not None:
                            try:
                                self._notification.notify_order(order_result)
                            except Exception as exc:
                                logger.warning(
                                    f"[{symbol}] EOD notification failed: {exc}"
                                )

            except Exception as exc:
                logger.exception(f"[{symbol}] EOD check error: {exc}")
                result.error = str(exc)

            summary.results.append(result)

        return summary

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------

    def _fetch_data(self, symbol: str, lookback_days: int) -> pd.DataFrame | None:
        """拉取历史 OHLCV 数据。"""
        end = datetime.now(tz=timezone.utc).date()
        # 加 buffer：lookback_days + 50 日交易日以覆盖节假日
        start = end - timedelta(days=lookback_days + 14)

        try:
            df = self._provider.get_ohlcv(
                symbol=symbol,
                start=start,
                end=end,
                timeframe="1d",
            )
            return df if not df.empty else None
        except Exception as exc:
            logger.error(f"[{symbol}] Data fetch failed: {exc}")
            return None

    def _generate_signals(
        self,
        symbol: str,
        df: pd.DataFrame,
    ) -> list[Signal]:
        """调用配置指定的策略函数，生成最新一根 bar 的信号列表。"""
        strategy_name = self._cfg.strategy.name
        params = self._cfg.strategy.params

        strategy_fn = STRATEGY_REGISTRY.get(strategy_name)
        if strategy_fn is None:
            logger.error(
                f"[{symbol}] Strategy '{strategy_name}' not registered. "
                f"Available: {list(STRATEGY_REGISTRY.keys())}"
            )
            return []

        try:
            signal_series: pd.Series = strategy_fn(df["close"], **params)
        except Exception as exc:
            logger.error(f"[{symbol}] Strategy '{strategy_name}' raised: {exc}")
            return []

        if signal_series.empty:
            return []

        # 取最新一根 bar 的信号
        latest_ts = signal_series.index[-1]
        latest_val = int(signal_series.iloc[-1])

        direction_map = {1: SignalDirection.BUY, -1: SignalDirection.SELL, 0: SignalDirection.HOLD}
        direction = direction_map.get(latest_val, SignalDirection.HOLD)

        if direction == SignalDirection.HOLD:
            return []

        latest_close = float(df["close"].iloc[-1])
        return [
            Signal(
                symbol=symbol,
                direction=direction,
                timestamp=latest_ts.to_pydatetime()
                if hasattr(latest_ts, "to_pydatetime")
                else latest_ts,
                confidence=0.7,  # 基础策略置信度
                strategy_name=strategy_name,
                indicators={"params": params},
                price_hint=latest_close,
            )
        ]

    def _sync_risk_state(self) -> None:
        """将 PortfolioTracker 的最新状态同步给 RiskManager。"""
        portfolio = self._tracker.portfolio
        total_capital = portfolio.cash + sum(
            pos.quantity * pos.avg_cost
            for pos in portfolio.open_positions.values()
        )
        current_exposure = sum(
            pos.quantity * pos.avg_cost
            for pos in portfolio.open_positions.values()
        )
        current_positions_count = len(portfolio.open_positions)

        self._risk.update_portfolio_state(
            total_capital=total_capital,
            current_exposure=current_exposure,
            current_positions_count=current_positions_count,
        )
        logger.debug(
            f"[RiskSync] capital={total_capital:.0f} "
            f"exposure={current_exposure:.0f} "
            f"positions={current_positions_count}"
        )


# ---------------------------------------------------------------------------
# 工厂函数：从 AppComponents 快速构建 Orchestrator
# ---------------------------------------------------------------------------

def build_orchestrator(components: Any) -> ScanOrchestrator:
    """从 Container.build() 返回的 AppComponents 构建编排器。

    优先使用 Phase 5 链路（若 Phase 5 模块可用），否则降级为 Phase 4 单策略模式。
    """
    cfg = components.config

    # 判断是否走 Phase 5 链路
    use_phase5 = (
        components.data_store is not None
        and components.universe is not None
        and components.matrix_runner is not None
        and components.signal_ranker is not None
    )

    if use_phase5:
        logger.info("[Orchestrator] Using Phase 5 multi-strategy pipeline")
        return _build_phase5_orchestrator(components)
    else:
        logger.info("[Orchestrator] Using Phase 4 single-strategy pipeline")
        return _build_phase4_orchestrator(components)


# ---------------------------------------------------------------------------
# Phase 5 Orchestrator 工厂
# ---------------------------------------------------------------------------

def _build_phase5_orchestrator(components: Any) -> ScanOrchestrator:
    """构建 Phase 5 编排器：MarketDataStore → MatrixRunner → SignalRanker → CandidateSelector → Broker。"""
    cfg = components.config
    import mytrader.strategy.strategies  # noqa: F401

    # 信号过滤管线
    from mytrader.signal.pipeline import SignalPipeline
    pipeline = SignalPipeline.from_config(cfg.signal_filter)

    # 风险管理器
    from mytrader.risk.manager import RiskManager
    risk_manager = RiskManager(
        config=cfg.risk,
        total_capital=cfg.backtest.init_cash,
    )

    orchestrator = ScanOrchestrator(
        config=cfg,
        data_provider=components.data_store,   # Phase 5: 用本地库替代 DataProvider
        pipeline=pipeline,
        risk_manager=risk_manager,
        broker=components.broker,
        tracker=components.tracker,
        notification=components.notification,
    )

    # 注入 Phase 5 专属依赖
    orchestrator._use_phase5 = True
    orchestrator._universe = components.universe
    orchestrator._matrix_runner = components.matrix_runner
    orchestrator._signal_ranker = components.signal_ranker

    logger.info("[Orchestrator] Phase 5 pipeline: MarketDataStore → MatrixRunner → SignalRanker → CandidateSelector → Broker")
    return orchestrator


# ---------------------------------------------------------------------------
# Phase 4 Orchestrator 工厂（向后兼容）
# ---------------------------------------------------------------------------

def _build_phase4_orchestrator(components: Any) -> ScanOrchestrator:
    """构建 Phase 4 编排器：DataProvider → 单策略 → 信号过滤 → 风控 → Broker。"""
    cfg = components.config

    from mytrader.data.cache import DataCache
    from mytrader.risk.manager import RiskManager
    from mytrader.signal.pipeline import SignalPipeline

    # 数据提供者
    provider_name = cfg.data.provider.lower()
    if provider_name == "alpaca":
        from mytrader.data.providers.alpaca_provider import AlpacaDataProvider
        cache = DataCache(cache_dir=cfg.data.cache_dir)
        data_provider = AlpacaDataProvider(
            api_key=cfg.alpaca.api_key,
            secret_key=cfg.alpaca.secret_key,
            paper=cfg.alpaca.paper,
            cache=cache,
        )
        logger.info("[Orchestrator] Using AlpacaDataProvider")
    else:
        from mytrader.data.providers.yfinance_provider import YFinanceProvider
        cache = DataCache(cache_dir=cfg.data.cache_dir)
        data_provider = YFinanceProvider(cache=cache)
        logger.info("[Orchestrator] Using YFinanceProvider")

    pipeline = SignalPipeline.from_config(cfg.signal_filter)
    risk_manager = RiskManager(config=cfg.risk, total_capital=cfg.backtest.init_cash)

    import mytrader.strategy.strategies  # noqa: F401

    return ScanOrchestrator(
        config=cfg,
        data_provider=data_provider,
        pipeline=pipeline,
        risk_manager=risk_manager,
        broker=components.broker,
        tracker=components.tracker,
        notification=components.notification,
    )
