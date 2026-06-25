"""测试 risk 模块：仓位计算 + 止损 + 熔断 + 约束 + RiskManager 门面。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import pytest

from mytrader.infra.config import RiskConfig
from mytrader.risk.circuit_breaker import CircuitBreaker
from mytrader.risk.constraints import (
    check_max_positions,
    check_min_order_value,
    check_single_position_limit,
    check_total_exposure,
)
from mytrader.risk.manager import RiskManager
from mytrader.risk.models import CircuitBreakerState, OrderIntent
from mytrader.risk.position_sizer import atr_position_size, fixed_amount_size, fixed_fraction_size
from mytrader.risk.stop_loss import atr_stop, fixed_stop, fixed_take_profit
from mytrader.signal.models import FilteredSignal
from mytrader.strategy.base import Signal, SignalDirection


def make_ohlcv(n: int = 50, base_price: float = 100.0) -> pd.DataFrame:
    dates = pd.date_range("2023-11-01", periods=n, freq="D", tz="UTC")
    close_vals = [base_price + i * 0.1 for i in range(n)]
    return pd.DataFrame(
        {
            "open": [v * 0.999 for v in close_vals],
            "high": [v * 1.01 for v in close_vals],
            "low": [v * 0.99 for v in close_vals],
            "close": close_vals,
            "volume": [1_000_000] * n,
        },
        index=dates,
    )


# ---------------------------------------------------------------------------
# PositionSizer 测试
# ---------------------------------------------------------------------------

class TestPositionSizer:
    def test_fixed_amount_basic(self):
        qty, risk = fixed_amount_size(
            capital=100_000,
            risk_per_trade=0.01,
            entry_price=100.0,
            stop_loss_price=98.0,
        )
        # risk_amount = 1000; stop_dist = 2; qty = 500
        assert qty == 500
        assert risk == pytest.approx(1000.0)

    def test_fixed_amount_zero_stop_distance(self):
        qty, risk = fixed_amount_size(100_000, 0.01, 100.0, 100.0)
        assert qty == 0

    def test_atr_position_size_returns_positive(self):
        df = make_ohlcv(50)
        qty, risk, stop = atr_position_size(
            capital=100_000,
            risk_per_trade=0.01,
            entry_price=105.0,
            df=df,
        )
        assert qty >= 0
        assert stop < 105.0  # 做多时止损低于入场价

    def test_fixed_fraction_size(self):
        qty, val = fixed_fraction_size(100_000, fraction=0.10, entry_price=100.0)
        assert qty == 100
        assert val == pytest.approx(10_000.0)

    def test_fixed_fraction_zero_price(self):
        qty, val = fixed_fraction_size(100_000, 0.10, 0.0)
        assert qty == 0

    def test_atr_position_size_zero_atr(self) -> None:
        """RM6 (P0): ATR 计算为零时不抛除零异常。"""
        df = make_ohlcv(50)
        df["high"] = df["close"]
        df["low"] = df["close"]  # high==low → ATR≈0
        qty, risk, stop = atr_position_size(
            capital=100_000, risk_per_trade=0.01, entry_price=105.0, df=df,
        )
        assert qty >= 0  # 不抛异常，安全降级

    def test_atr_position_size_negative_equity(self) -> None:
        """RM7 (P1): account_equity <= 0 时不崩溃。"""
        df = make_ohlcv(50)
        qty, risk, stop = atr_position_size(
            capital=0, risk_per_trade=0.01, entry_price=105.0, df=df,
        )
        # capital=0 时 quantity=0，不抛异常
        assert qty == 0


# ---------------------------------------------------------------------------
# StopLoss 测试
# ---------------------------------------------------------------------------

class TestStopLoss:
    def test_fixed_stop_long(self):
        price = fixed_stop(100.0, stop_pct=0.02, is_long=True)
        assert price == pytest.approx(98.0)

    def test_fixed_stop_short(self):
        price = fixed_stop(100.0, stop_pct=0.02, is_long=False)
        assert price == pytest.approx(102.0)

    def test_fixed_take_profit_long(self):
        price = fixed_take_profit(100.0, tp_pct=0.04, is_long=True)
        assert price == pytest.approx(104.0)

    def test_atr_stop_returns_below_entry(self):
        df = make_ohlcv(50)
        stop = atr_stop(105.0, df, atr_period=14, atr_multiplier=2.0, is_long=True)
        assert stop < 105.0

    def test_time_stop_bars_default(self) -> None:
        """RM8 (P1): time_stop_bars 返回配置的 bar 数。"""
        from mytrader.risk.stop_loss import time_stop_bars
        assert time_stop_bars(10) == 10


# ---------------------------------------------------------------------------
# CircuitBreaker 测试
# ---------------------------------------------------------------------------

class TestCircuitBreaker:
    def test_normal_state_no_loss(self):
        cb = CircuitBreaker(daily_loss_limit=0.02)
        state = cb.update(100_000)
        assert state == CircuitBreakerState.NORMAL
        assert cb.is_triggered is False

    def test_daily_triggered(self):
        cb = CircuitBreaker(daily_loss_limit=0.02)
        cb.update(100_000)  # 初始化基准
        state = cb.update(97_500)  # 亏损 2.5% > 2%
        assert state == CircuitBreakerState.DAILY_TRIGGERED
        assert cb.is_triggered is True

    def test_weekly_triggered(self):
        from datetime import timedelta
        cb = CircuitBreaker(daily_loss_limit=0.10, weekly_loss_limit=0.05)  # 日限10%不触发
        now = datetime.now()
        today = now.date()
        # 将周起始日设为当前周的周一
        week_start = today - timedelta(days=today.weekday())
        cb._weekly_start = 100_000
        cb._weekly_start_date = week_start
        # 也初始化日基准（日亏损 6% < 10%）
        cb._daily_start = 100_000
        cb._daily_date = today
        cb._monthly_start = 100_000
        cb._monthly_month = (today.year, today.month)
        state = cb.update(94_000, now=now)  # 周亏损 6% > 5%
        assert state == CircuitBreakerState.WEEKLY_TRIGGERED

    def test_reset_clears_state(self):
        cb = CircuitBreaker(daily_loss_limit=0.02)
        cb.update(100_000)
        cb.update(97_500)
        assert cb.is_triggered
        cb.reset()
        assert cb.state == CircuitBreakerState.NORMAL

    def test_not_triggered_after_recovery(self):
        """资产回升后熔断解除。"""
        cb = CircuitBreaker(daily_loss_limit=0.05)
        # 同一天初始化
        now = datetime(2024, 1, 10, 9, 0, tzinfo=timezone.utc)
        cb.update(100_000, now=now)
        # 亏损 3%（未触发）
        state = cb.update(97_000, now=now)
        assert state == CircuitBreakerState.NORMAL

    def test_exact_boundary_daily_loss(self) -> None:
        """RM9 (P1): 日亏损恰好等于阈值时行为明确。"""
        cb = CircuitBreaker(daily_loss_limit=0.02)
        cb.update(100_000.0)
        state = cb.update(98_000.0)  # 恰好 2% 亏损
        assert state == CircuitBreakerState.DAILY_TRIGGERED  # >= 触发

    def test_reset_after_new_day(self) -> None:
        """RM10 (P0): 跨日后日熔断自动恢复（资产持平）。"""
        cb = CircuitBreaker(daily_loss_limit=0.02, weekly_loss_limit=0.05)
        day1 = datetime(2024, 1, 10, 10, 0, tzinfo=timezone.utc)
        cb.update(100_000, now=day1)
        cb.update(97_000, now=day1)  # 触发日熔断
        assert cb.is_triggered is True

        # 跨日，资产持平（100k），应恢复 NORMAL
        day2 = datetime(2024, 1, 11, 10, 0, tzinfo=timezone.utc)
        state = cb.update(100_000, now=day2)
        assert state == CircuitBreakerState.NORMAL

    def test_monthly_persists_across_day(self) -> None:
        """RM11 (P1): 月熔断不随跨日恢复。"""
        cb = CircuitBreaker(
            daily_loss_limit=0.50,   # 日限非常大，不触发
            weekly_loss_limit=0.50,  # 周限非常大，不触发
            monthly_loss_limit=0.02,  # 月限 2%
        )
        day1 = datetime(2024, 1, 10, 10, 0, tzinfo=timezone.utc)
        cb.update(100_000, now=day1)
        state = cb.update(97_000, now=day1)  # 触发月熔断
        assert state == CircuitBreakerState.MONTHLY_TRIGGERED

        # 跨日，但仍在同一月
        day2 = datetime(2024, 1, 11, 10, 0, tzinfo=timezone.utc)
        state = cb.update(97_000, now=day2)
        assert state == CircuitBreakerState.MONTHLY_TRIGGERED

    def test_multi_level_priority(self) -> None:
        """RM12 (P1): 日+周同时触发时，日优先返回 DAILY。"""
        cb = CircuitBreaker(
            daily_loss_limit=0.02,    # 日限 2%
            weekly_loss_limit=0.03,   # 周限 3%
            monthly_loss_limit=0.50,
        )
        today = datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc)
        cb.update(100_000, now=today)
        # 亏损 4%：同时超过日限 2% 和周限 3%，日优先检查
        state = cb.update(96_000, now=today)
        assert state == CircuitBreakerState.DAILY_TRIGGERED  # 日优先


# ---------------------------------------------------------------------------
# Constraints 测试
# ---------------------------------------------------------------------------

class TestConstraints:
    def test_min_order_value_pass(self):
        result = check_min_order_value(100, 10.0, min_order_value=500)
        assert result.passed is True  # 1000 >= 500

    def test_min_order_value_fail(self):
        result = check_min_order_value(10, 10.0, min_order_value=500)
        assert result.passed is False  # 100 < 500

    def test_single_position_limit_pass(self):
        result = check_single_position_limit(15_000, 100_000, max_single_position_pct=0.20)
        assert result.passed is True  # 15% < 20%

    def test_single_position_limit_fail(self):
        result = check_single_position_limit(25_000, 100_000, max_single_position_pct=0.20)
        assert result.passed is False  # 25% > 20%

    def test_total_exposure_pass(self):
        result = check_total_exposure(50_000, 10_000, 100_000, max_total_exposure_pct=0.80)
        assert result.passed is True  # 60% < 80%

    def test_total_exposure_fail(self):
        result = check_total_exposure(75_000, 10_000, 100_000, max_total_exposure_pct=0.80)
        assert result.passed is False  # 85% > 80%

    def test_max_positions_pass(self):
        result = check_max_positions(3, max_concurrent_positions=5)
        assert result.passed is True

    def test_max_positions_fail(self):
        result = check_max_positions(5, max_concurrent_positions=5)
        assert result.passed is False


# ---------------------------------------------------------------------------
# RiskManager 门面积分测试 (P0/P1)
# ---------------------------------------------------------------------------

def _make_filtered_signal(
    direction: SignalDirection = SignalDirection.BUY,
    ts: datetime | None = None,
    price_hint: float | None = 105.0,
) -> FilteredSignal:
    if ts is None:
        ts = datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc)
    sig = Signal(
        symbol="AAPL", direction=direction, timestamp=ts,
        confidence=0.8, strategy_name="test", price_hint=price_hint,
    )
    return FilteredSignal(source_signal=sig, passed=True)


class TestRiskManagerIntegration:
    """RM1-RM5: RiskManager 全链路集成测试。"""

    def test_full_pipeline_approve(self) -> None:
        """RM1 (P0): 全链路通过，返回 OrderIntent 含仓位+止损+止盈。"""
        cfg = RiskConfig(max_single_position_pct=0.50)  # 放宽单仓位限制
        mgr = RiskManager(config=cfg, total_capital=300_000.0)
        df = make_ohlcv(50)  # 足够数据供 ATR
        fs = _make_filtered_signal(ts=df.index[45])
        result = mgr.evaluate(fs, df)
        assert result is not None
        assert result.symbol == "AAPL"
        assert result.direction == SignalDirection.BUY
        assert result.quantity > 0
        assert result.stop_loss_price > 0
        assert result.take_profit_price is not None
        assert result.take_profit_price > result.entry_price

    def test_circuit_breaker_reject(self) -> None:
        """RM2 (P0): 熔断触发后拒绝订单。"""
        cfg = RiskConfig()
        mgr = RiskManager(config=cfg)
        # 触发日熔断
        mgr._circuit_breaker.update(100_000)
        mgr._circuit_breaker.update(97_000)
        assert mgr._circuit_breaker.is_triggered

        df = make_ohlcv(50)
        fs = _make_filtered_signal(ts=df.index[45])
        result = mgr.evaluate(fs, df)
        assert result is None  # 被熔断拒绝

    def test_constraint_reject_max_positions(self) -> None:
        """RM3 (P0): 超过最大持仓数时拒绝订单。"""
        cfg = RiskConfig(max_concurrent_positions=2)
        mgr = RiskManager(
            config=cfg, current_positions_count=2,
        )
        df = make_ohlcv(50)
        fs = _make_filtered_signal(ts=df.index[45])
        result = mgr.evaluate(fs, df)
        assert result is None  # 仓位已满

    def test_stop_loss_integration(self) -> None:
        """RM5 (P1): RiskManager 自动附加 stop_loss 和 take_profit。"""
        cfg = RiskConfig(risk_per_trade=0.01, max_single_position_pct=0.50)
        mgr = RiskManager(config=cfg, total_capital=300_000.0)
        df = make_ohlcv(50)
        fs = _make_filtered_signal(ts=df.index[45], price_hint=105.0)
        result = mgr.evaluate(fs, df)
        assert result is not None
        # 做多止损应低于入场价
        assert result.stop_loss_price < 105.0
        # 止盈应高于入场价
        assert result.take_profit_price > 105.0
        # take_profit 应为 2:1 风险收益比
        stop_dist = 105.0 - result.stop_loss_price
        tp_dist = result.take_profit_price - 105.0
        assert tp_dist == pytest.approx(stop_dist * 2, rel=0.1)

    def test_hold_signal_returns_none(self) -> None:
        """HOLD 信号直接返回 None。"""
        cfg = RiskConfig()
        mgr = RiskManager(config=cfg)
        df = make_ohlcv(50)
        fs = _make_filtered_signal(direction=SignalDirection.HOLD, ts=df.index[45])
        result = mgr.evaluate(fs, df)
        assert result is None

    def test_multiple_violations_circuit_breaker_first(self) -> None:
        """RM4 (P1): 同时违反熔断和约束时，熔断优先返回 None。"""
        cfg = RiskConfig(max_concurrent_positions=1)
        mgr = RiskManager(
            config=cfg, total_capital=200_000.0,
            current_positions_count=1,  # 已达最大仓位
        )
        # 触发熔断
        mgr._circuit_breaker.update(100_000)
        mgr._circuit_breaker.update(97_000)
        assert mgr._circuit_breaker.is_triggered

        df = make_ohlcv(50)
        fs = _make_filtered_signal(ts=df.index[45])
        result = mgr.evaluate(fs, df)
        # 熔断优先于约束检查
        assert result is None


# ---------------------------------------------------------------------------
# OrderIntent 测试
# ---------------------------------------------------------------------------

class TestOrderIntent:
    def test_auto_client_order_id(self):
        intent = OrderIntent(
            symbol="AAPL",
            direction=SignalDirection.BUY,
            quantity=100,
            entry_price=150.0,
            stop_loss_price=147.0,
            take_profit_price=156.0,
            risk_amount=300.0,
            position_value=15_000.0,
            timestamp=datetime.utcnow(),
            strategy_name="test",
        )
        assert len(intent.client_order_id) == 16

    def test_custom_client_order_id(self):
        intent = OrderIntent(
            symbol="AAPL",
            direction=SignalDirection.BUY,
            quantity=100,
            entry_price=150.0,
            stop_loss_price=147.0,
            take_profit_price=None,
            risk_amount=300.0,
            position_value=15_000.0,
            timestamp=datetime.utcnow(),
            strategy_name="test",
            client_order_id="custom_id_123",
        )
        assert intent.client_order_id == "custom_id_123"
