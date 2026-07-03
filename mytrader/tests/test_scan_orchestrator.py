"""ScanOrchestrator 单元测试（全 Mock，无网络 / 无 DB）。

覆盖点：
- morning_scan：BUY 信号 → 提交订单 → tracker 更新
- morning_scan：SELL 信号 → 提交订单
- morning_scan：HOLD 信号 → 无订单
- morning_scan：风控拦截 → 无订单
- morning_scan：数据获取失败 → SymbolScanResult.error 非空
- morning_scan：策略不存在 → HOLD（无订单）
- morning_scan：过滤器过滤 → 无订单
- intraday_scan：复用 _run_scan，通量快检
- eod_check：止损触发 → 生成 SELL 单
- eod_check：止盈触发 → 生成 SELL 单
- eod_check：未触碰 → 无订单
- eod_check：无持仓 → 空 ScanSummary
- ScanSummary 统计属性正确
- build_orchestrator：yfinance 模式
- build_orchestrator：alpaca 模式
- _sync_risk_state：正确同步 RiskManager 状态
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from mytrader.execution.models import OrderResult, OrderStatus
from mytrader.portfolio.models import Position
from mytrader.strategy.base import Signal, SignalDirection
from mytrader.scan_orchestrator import (
    ScanOrchestrator,
    ScanSummary,
    SymbolScanResult,
    build_orchestrator,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ohlcv(n: int = 60) -> pd.DataFrame:
    idx = pd.date_range("2024-01-02", periods=n, freq="B", tz="UTC")
    return pd.DataFrame(
        {
            "open":   [100.0 + i * 0.1 for i in range(n)],
            "high":   [105.0 + i * 0.1 for i in range(n)],
            "low":    [98.0 + i * 0.1 for i in range(n)],
            "close":  [103.0 + i * 0.1 for i in range(n)],
            "volume": [1_000_000] * n,
        },
        index=idx,
    )


def _make_order_result(
    symbol: str = "AAPL",
    direction: SignalDirection = SignalDirection.BUY,
    status: OrderStatus = OrderStatus.FILLED,
) -> OrderResult:
    return OrderResult(
        client_order_id="order-001",
        symbol=symbol,
        direction=direction,
        quantity=10,
        fill_price=150.0,
        commission=0.0,
        status=status,
        filled_at=datetime.now(timezone.utc),
    )


def _make_orchestrator(
    *,
    symbols: list[str] | None = None,
    strategy_name: str = "dual_ma",
    ohlcv_df: pd.DataFrame | None = None,
    order_status: OrderStatus = OrderStatus.FILLED,
    signal_val: int = 1,        # 1=BUY, -1=SELL, 0=HOLD
    risk_returns_intent: bool = True,
    filter_passes: bool = True,
) -> ScanOrchestrator:
    """构建注入 Mock 的 Orchestrator。"""
    # Config mock
    cfg = MagicMock()
    cfg.watchlist.symbols = symbols or ["AAPL"]
    cfg.watchlist.lookback_days = 90
    cfg.strategy.name = strategy_name
    cfg.strategy.params = {"fast": 10, "slow": 30}
    cfg.data.provider = "yfinance"
    cfg.data.cache_dir = "~/.mytrader/cache"
    cfg.backtest.init_cash = 100_000.0

    # DataProvider mock
    df = ohlcv_df if ohlcv_df is not None else _make_ohlcv()
    data_provider = MagicMock()
    data_provider.get_ohlcv.return_value = df

    # 预构建信号，供 _generate_signals mock 使用
    _direction = (
        SignalDirection.BUY if signal_val == 1
        else SignalDirection.SELL if signal_val == -1
        else SignalDirection.HOLD
    )
    _signal = Signal(
        symbol="AAPL",
        direction=_direction,
        timestamp=datetime.now(timezone.utc),
        confidence=0.7,
        strategy_name=strategy_name,
    )

    # Pipeline mock
    pipeline = MagicMock()
    if filter_passes and signal_val != 0:
        from mytrader.signal.models import FilteredSignal, FilterResult
        filtered = FilteredSignal(source_signal=_signal)
        fr = FilterResult(original_signal_count=1)
        fr.passed_count = 1
        pipeline.run.return_value = ([filtered], fr)
    else:
        from mytrader.signal.models import FilterResult
        fr = FilterResult(original_signal_count=1)
        fr.passed_count = 0
        pipeline.run.return_value = ([], fr)

    # RiskManager mock
    risk_manager = MagicMock()
    if risk_returns_intent:
        intent = MagicMock()
        intent.client_order_id = "order-001"
        intent.symbol = "AAPL"
        intent.direction = _direction
        intent.quantity = 10
        intent.entry_price = 103.0
        intent.stop_loss_price = 98.0
        intent.take_profit_price = 113.0
        intent.risk_amount = 50.0
        intent.meta = {}
        risk_manager.evaluate.return_value = intent
    else:
        risk_manager.evaluate.return_value = None

    # Broker mock
    broker = MagicMock()
    broker.submit.return_value = _make_order_result(
        status=order_status,
        direction=_direction,
    )

    # Tracker mock
    tracker = MagicMock()
    from mytrader.portfolio.models import Portfolio
    portfolio = Portfolio(cash=95_000.0)
    tracker.portfolio = portfolio
    tracker.open_positions = {}

    # Notification mock
    notification = MagicMock()

    orch = ScanOrchestrator(
        config=cfg,
        data_provider=data_provider,
        pipeline=pipeline,
        risk_manager=risk_manager,
        broker=broker,
        tracker=tracker,
        notification=notification,
    )

    # Mock _generate_signals，绕开策略注册表依赖
    if signal_val != 0 and ohlcv_df is None:
        # 返回非空信号（让 pipeline 决定是否过滤）
        orch._generate_signals = MagicMock(return_value=[_signal])
    elif ohlcv_df is not None and ohlcv_df.empty:
        # 空数据 → 生成空信号
        orch._generate_signals = MagicMock(return_value=[])
    elif signal_val == 0:
        # HOLD
        orch._generate_signals = MagicMock(return_value=[])
    else:
        orch._generate_signals = MagicMock(return_value=[_signal])

    return orch


# ---------------------------------------------------------------------------
# SymbolScanResult & ScanSummary
# ---------------------------------------------------------------------------

class TestScanModels:
    def test_symbol_scan_result_default(self):
        r = SymbolScanResult(symbol="AAPL")
        assert r.signal_direction == "HOLD"
        assert not r.order_submitted
        assert not r.has_error

    def test_symbol_scan_result_with_error(self):
        r = SymbolScanResult(symbol="AAPL", error="test error")
        assert r.has_error

    def test_scan_summary_counts(self):
        s = ScanSummary(scan_type="morning")
        s.results = [
            SymbolScanResult("AAPL", signal_direction="BUY", order_submitted=True),
            SymbolScanResult("TSLA", signal_direction="SELL", order_submitted=True),
            SymbolScanResult("MSFT", signal_direction="HOLD"),
            SymbolScanResult("NVDA", error="timeout"),
        ]
        assert s.buy_count == 1
        assert s.sell_count == 1
        assert s.order_count == 2
        assert s.error_count == 1


# ---------------------------------------------------------------------------
# morning_scan
# ---------------------------------------------------------------------------

class TestMorningScan:
    def test_buy_signal_submits_order(self):
        """BUY 信号 → broker.submit 被调用，order_submitted=True。"""
        orch = _make_orchestrator(signal_val=1, order_status=OrderStatus.FILLED)
        summary = orch.morning_scan()

        assert len(summary.results) == 1
        result = summary.results[0]
        assert result.signal_direction == "BUY"
        assert result.order_submitted
        assert result.order_status == "FILLED"
        assert not result.has_error

    def test_sell_signal_submits_order(self):
        """SELL 信号也提交订单。"""
        orch = _make_orchestrator(signal_val=-1, order_status=OrderStatus.FILLED)
        # 调整 pipeline mock 返回 SELL FilteredSignal
        sell_sig = Signal(
            symbol="AAPL",
            direction=SignalDirection.SELL,
            timestamp=datetime.now(timezone.utc),
            confidence=0.7,
            strategy_name="dual_ma",
        )
        from mytrader.signal.models import FilteredSignal, FilterResult
        fs = FilteredSignal(source_signal=sell_sig)
        fr = FilterResult(original_signal_count=1)
        fr.passed_count = 1
        orch._pipeline.run.return_value = ([fs], fr)
        orch._broker.submit.return_value = _make_order_result(
            direction=SignalDirection.SELL, status=OrderStatus.FILLED
        )

        summary = orch.morning_scan()
        assert summary.results[0].order_submitted

    def test_hold_signal_no_order(self):
        """HOLD 信号（过滤后无信号）不提交订单。"""
        orch = _make_orchestrator(signal_val=0)  # _generate_signals 返回空
        summary = orch.morning_scan()
        assert not summary.results[0].order_submitted
        assert summary.results[0].signal_direction == "HOLD"

    def test_filter_blocks_order(self):
        """过滤器拦截信号 → 无订单。"""
        orch = _make_orchestrator(signal_val=1, filter_passes=False)
        summary = orch.morning_scan()
        assert not summary.results[0].order_submitted

    def test_risk_rejected_no_order(self):
        """RiskManager 返回 None → 不提交订单。"""
        orch = _make_orchestrator(signal_val=1, risk_returns_intent=False)
        summary = orch.morning_scan()
        assert not summary.results[0].order_submitted

    def test_data_fetch_failure_records_error(self):
        """数据获取失败 → SymbolScanResult.error 非空。"""
        orch = _make_orchestrator(signal_val=1)
        orch._provider.get_ohlcv.side_effect = ConnectionError("network error")
        summary = orch.morning_scan()
        assert summary.results[0].has_error

    def test_empty_data_no_order(self):
        """Provider 返回空 DataFrame → HOLD，无订单。"""
        orch = _make_orchestrator(signal_val=1, ohlcv_df=pd.DataFrame())
        summary = orch.morning_scan()
        assert not summary.results[0].order_submitted

    def test_multiple_symbols(self):
        """多个 symbol 各自独立扫描。"""
        orch = _make_orchestrator(symbols=["AAPL", "TSLA", "MSFT"])
        summary = orch.morning_scan()
        assert len(summary.results) == 3

    def test_one_symbol_error_others_continue(self):
        """一个 symbol 异常，不影响其余扫描继续进行。"""
        orch = _make_orchestrator(symbols=["AAPL", "TSLA"])

        # 让 TSLA 数据获取抛异常，AAPL 正常
        def data_side_effect(symbol, start, end, timeframe="1d"):
            if symbol == "TSLA":
                raise RuntimeError("TSLA data error")
            return _make_ohlcv()

        orch._provider.get_ohlcv.side_effect = data_side_effect

        # 针对 TSLA，_generate_signals 也要正常（因为 _fetch_data 会先抛异常）
        # _generate_signals 是 Mock，不会被调用到 TSLA（fetch 已异常）

        summary = orch.morning_scan()
        assert len(summary.results) == 2
        tsla_result = next(r for r in summary.results if r.symbol == "TSLA")
        assert tsla_result.has_error

    def test_pending_order_not_processed_by_tracker(self):
        """PENDING 订单不调用 tracker.process_order。"""
        orch = _make_orchestrator(signal_val=1, order_status=OrderStatus.PENDING)
        orch.morning_scan()
        orch._tracker.process_order.assert_not_called()

    def test_filled_order_calls_tracker(self):
        """FILLED 订单调用 tracker.process_order。"""
        orch = _make_orchestrator(signal_val=1, order_status=OrderStatus.FILLED)
        orch.morning_scan()
        orch._tracker.process_order.assert_called_once()

    def test_notification_called_on_order(self):
        """有订单时通知服务被调用。"""
        orch = _make_orchestrator(signal_val=1, order_status=OrderStatus.FILLED)
        orch.morning_scan()
        orch._notification.notify_order.assert_called_once()

    def test_notification_failure_does_not_crash(self):
        """通知失败不影响主流程。"""
        orch = _make_orchestrator(signal_val=1, order_status=OrderStatus.FILLED)
        orch._notification.notify_order.side_effect = ConnectionError("telegram down")
        summary = orch.morning_scan()
        # 不抛异常
        assert not summary.results[0].has_error


# ---------------------------------------------------------------------------
# intraday_scan
# ---------------------------------------------------------------------------

class TestIntradayScan:
    def test_intraday_scan_returns_summary(self):
        orch = _make_orchestrator(signal_val=1)
        summary = orch.intraday_scan()
        assert summary.scan_type == "intraday"
        assert len(summary.results) == 1


# ---------------------------------------------------------------------------
# eod_check
# ---------------------------------------------------------------------------

class TestEODCheck:
    def _make_orch_with_position(
        self,
        stop_loss: float = 0.0,
        take_profit: float | None = None,
        latest_close: float = 103.0,
    ) -> ScanOrchestrator:
        orch = _make_orchestrator(signal_val=1)

        # 设置持仓
        pos = Position(
            symbol="AAPL",
            quantity=10,
            avg_cost=105.0,
            stop_loss_price=stop_loss,
            take_profit_price=take_profit,
        )
        orch._tracker.open_positions = {"AAPL": pos}

        # 设置最近价格
        df = _make_ohlcv(5)
        df.iloc[-1, df.columns.get_loc("close")] = latest_close
        orch._provider.get_ohlcv.return_value = df

        # 调整 risk intent 为 SELL
        intent = MagicMock()
        intent.client_order_id = "eod-sell-001"
        intent.symbol = "AAPL"
        intent.direction = SignalDirection.SELL
        intent.quantity = 10
        intent.entry_price = latest_close
        intent.stop_loss_price = 0.0
        intent.take_profit_price = None
        intent.risk_amount = 0.0
        intent.meta = {}
        orch._risk.evaluate.return_value = intent

        orch._broker.submit.return_value = _make_order_result(
            direction=SignalDirection.SELL, status=OrderStatus.FILLED
        )
        return orch

    def test_stop_loss_triggered(self):
        """止损触发时生成 SELL 单。"""
        orch = self._make_orch_with_position(stop_loss=105.0, latest_close=100.0)
        summary = orch.eod_check()
        assert summary.sell_count == 1
        assert summary.order_count == 1

    def test_take_profit_triggered(self):
        """止盈触发时生成 SELL 单。"""
        orch = self._make_orch_with_position(take_profit=100.0, latest_close=101.0)
        summary = orch.eod_check()
        assert summary.sell_count == 1

    def test_no_trigger_no_order(self):
        """未触碰止损/止盈 → 无订单。"""
        orch = self._make_orch_with_position(
            stop_loss=90.0,   # close 103 > 90，不触发
            take_profit=120.0,  # close 103 < 120，不触发
            latest_close=103.0,
        )
        summary = orch.eod_check()
        assert summary.order_count == 0

    def test_no_positions_returns_empty_summary(self):
        """无持仓 → 返回空 ScanSummary。"""
        orch = _make_orchestrator()
        orch._tracker.open_positions = {}
        summary = orch.eod_check()
        assert summary.scan_type == "eod"
        assert len(summary.results) == 0


# ---------------------------------------------------------------------------
# _sync_risk_state
# ---------------------------------------------------------------------------

class TestSyncRiskState:
    def test_sync_updates_risk_manager(self):
        """_sync_risk_state 正确将 Portfolio 数据传入 RiskManager。"""
        orch = _make_orchestrator()

        # 模拟持仓
        pos = Position(symbol="AAPL", quantity=100, avg_cost=150.0)
        from mytrader.portfolio.models import Portfolio
        portfolio = Portfolio(cash=50_000.0)
        portfolio.positions["AAPL"] = pos
        orch._tracker.portfolio = portfolio

        orch._sync_risk_state()

        orch._risk.update_portfolio_state.assert_called_once_with(
            total_capital=50_000.0 + 100 * 150.0,
            current_exposure=100 * 150.0,
            current_positions_count=1,
        )


# ---------------------------------------------------------------------------
# build_orchestrator
# ---------------------------------------------------------------------------

class TestBuildOrchestrator:
    def test_build_with_yfinance(self):
        """默认配置正确构建 Orchestrator（Phase 5 模式）。"""
        from mytrader.infra.config import load_config
        from mytrader.infra.container import Container

        config = load_config()
        components = Container.build(config, db_url=":memory:", build_phase5=True)

        orch = build_orchestrator(components)
        assert isinstance(orch, ScanOrchestrator)
        # Phase 5 模式时 _provider 是 MarketDataStore
        assert orch._use_phase5 is True

    def test_build_uses_alpaca_provider_when_configured(self):
        """Phase 4 降级模式时，data.provider='alpaca' 使用 AlpacaDataProvider。"""
        from mytrader.infra.config import load_config
        from mytrader.infra.container import Container

        config = load_config()
        object.__setattr__(config.data, "provider", "alpaca")

        # Phase 4 模式：关闭 Phase 5 模块装配
        components = Container.build(config, db_url=":memory:", build_phase5=False)
        orch = build_orchestrator(components)

        from mytrader.data.providers.alpaca_provider import AlpacaDataProvider
        assert isinstance(orch._provider, AlpacaDataProvider)

    def test_build_phase5_uses_market_data_store(self):
        """Phase 5 模式时，_provider 是 MarketDataStore。"""
        from mytrader.infra.config import load_config
        from mytrader.infra.container import Container

        config = load_config()
        components = Container.build(config, db_url=":memory:", build_phase5=True)
        orch = build_orchestrator(components)

        assert orch._use_phase5 is True
        from mytrader.data.store.market_data_store import MarketDataStore
        assert isinstance(orch._provider, MarketDataStore)
        assert orch._universe is not None
        assert orch._matrix_runner is not None
        assert orch._signal_ranker is not None


# ---------------------------------------------------------------------------
# 迭代 #5 新增：Pending 订单刷新（_refresh_pending_orders）
# ---------------------------------------------------------------------------

class TestRefreshPendingOrders:
    """spec §4.3 测试清单。"""

    def _make_orchestrator_with_broker(
        self,
        broker: Any,
    ) -> ScanOrchestrator:
        """构造一个用指定 broker 的 Orchestrator（Phase 4 模式）。"""
        cfg = MagicMock()
        cfg.watchlist.symbols = ["AAPL"]
        cfg.watchlist.lookback_days = 90
        cfg.strategy.name = "dual_ma"
        cfg.strategy.params = {"fast": 10, "slow": 30}

        data_provider = MagicMock()
        df = _make_ohlcv()
        data_provider.get_ohlcv.return_value = df

        pipeline = MagicMock()
        # 让 pipeline 返回空，避免触发后续下单流程
        from mytrader.signal.models import FilterResult
        pipeline.run.return_value = ([], FilterResult(original_signal_count=0))

        risk_manager = MagicMock()
        tracker = MagicMock()
        from mytrader.portfolio.models import Portfolio
        tracker.portfolio = Portfolio(cash=100_000.0)
        tracker.open_positions = {}

        notification = MagicMock()

        return ScanOrchestrator(
            config=cfg,
            data_provider=data_provider,
            pipeline=pipeline,
            risk_manager=risk_manager,
            broker=broker,
            tracker=tracker,
            notification=notification,
        )

    def test_refresh_pending_orders_processes_newly_filled_order_once(self):
        """同一订单被 refresh 多次返回，tracker.process_order 只调用一次。"""
        from datetime import datetime, timezone

        # 构造一个 OrderResult，状态为 FILLED
        filled_order = OrderResult(
            client_order_id="repeat_001",
            symbol="AAPL",
            direction=SignalDirection.BUY,
            quantity=10,
            fill_price=150.0,
            commission=0.0,
            status=OrderStatus.FILLED,
            filled_at=datetime.now(timezone.utc),
        )

        broker = MagicMock()
        # refresh 返回同一个 filled 订单（即使重复）
        broker.refresh_pending_orders.return_value = [filled_order, filled_order]

        orch = self._make_orchestrator_with_broker(broker)

        # 第一次 refresh：应处理一次
        count1 = orch._refresh_pending_orders()
        assert count1 == 1
        orch._tracker.process_order.assert_called_once_with(filled_order)

        # 第二次 refresh：同一 client_order_id 已在 _processed_order_ids 中，不应重复处理
        count2 = orch._refresh_pending_orders()
        # 第二次返回 0（因为 client_order_id 已处理）
        assert count2 == 0
        # tracker.process_order 仍然只被调用一次
        orch._tracker.process_order.assert_called_once()

    def test_refresh_pending_orders_noop_when_broker_not_supported(self):
        """PaperBroker 或普通 mock 无 refresh_pending_orders 时不抛异常。"""
        # 不给 broker 添加 refresh_pending_orders 方法
        broker = MagicMock(spec=["submit", "cancel", "get_order"])
        orch = self._make_orchestrator_with_broker(broker)

        # 不应抛异常，返回 0
        count = orch._refresh_pending_orders()
        assert count == 0

    def test_refresh_pending_orders_warning_but_scan_continues_on_broker_error(self):
        """broker.refresh_pending_orders 抛异常时，扫描仍继续。"""
        broker = MagicMock()
        broker.refresh_pending_orders.side_effect = Exception("API error")
        orch = self._make_orchestrator_with_broker(broker)

        # 不应抛异常
        count = orch._refresh_pending_orders()
        assert count == 0

        # 扫描仍能执行（验证不阻塞）
        summary = orch.morning_scan()
        assert isinstance(summary, ScanSummary)

    def test_refresh_skips_non_filled_orders(self):
        """refresh 返回的 PENDING/REJECTED 订单不交给 tracker。"""
        from datetime import datetime, timezone

        pending_order = OrderResult(
            client_order_id="p_001",
            symbol="AAPL",
            direction=SignalDirection.BUY,
            quantity=10,
            fill_price=0.0,
            commission=0.0,
            status=OrderStatus.PENDING,
            filled_at=datetime.now(timezone.utc),
        )
        broker = MagicMock()
        broker.refresh_pending_orders.return_value = [pending_order]
        orch = self._make_orchestrator_with_broker(broker)

        count = orch._refresh_pending_orders()
        assert count == 0
        orch._tracker.process_order.assert_not_called()

