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
        return summary

    # ------------------------------------------------------------------
    # Internal scan logic
    # ------------------------------------------------------------------

    def _run_scan(self, scan_type: str) -> ScanSummary:
        """盘前/盘中通用扫描逻辑。"""
        # 1. 同步 RiskManager 持仓状态
        self._sync_risk_state()

        symbols = self._cfg.watchlist.symbols
        lookback = self._cfg.watchlist.lookback_days
        summary = ScanSummary(scan_type=scan_type)

        for symbol in symbols:
            result = self._scan_symbol(symbol, lookback)
            summary.results.append(result)

        return summary

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
    """从 Container.build() 返回的 AppComponents 构建 ScanOrchestrator。

    Args:
        components: AppComponents 实例

    Returns:
        ScanOrchestrator 实例，已完成依赖注入
    """
    from mytrader.data.cache import DataCache
    from mytrader.risk.manager import RiskManager
    from mytrader.signal.pipeline import SignalPipeline

    cfg = components.config

    # 数据提供者：根据 data.provider 配置选择
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
        logger.info(
            f"[Orchestrator] Using AlpacaDataProvider "
            f"(paper={cfg.alpaca.paper})"
        )
    else:
        # 默认 yfinance
        from mytrader.data.providers.yfinance_provider import YFinanceProvider
        cache = DataCache(cache_dir=cfg.data.cache_dir)
        data_provider = YFinanceProvider(cache=cache)
        logger.info("[Orchestrator] Using YFinanceProvider")

    # 信号过滤管线
    pipeline = SignalPipeline.from_config(cfg.signal_filter)

    # 风险管理器（初始资金来自 backtest.init_cash）
    risk_manager = RiskManager(
        config=cfg.risk,
        total_capital=cfg.backtest.init_cash,
    )

    # 导入所有策略（确保注册表已填充）
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
