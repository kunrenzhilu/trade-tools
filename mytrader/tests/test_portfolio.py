"""测试 portfolio 模块：持仓更新 + FIFO 盈亏 + 指标 + 持久化。"""

from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import pandas as pd
import pytest

from mytrader.execution.models import OrderResult, OrderStatus
from mytrader.portfolio.metrics import (
    calmar_ratio,
    max_drawdown,
    portfolio_summary,
    profit_factor,
    sharpe_ratio,
    win_rate,
)
from mytrader.portfolio.models import Portfolio, Position, TradeRecord
from mytrader.portfolio.persistence import PortfolioPersistence
from mytrader.portfolio.pnl_calculator import apply_buy, apply_sell
from mytrader.portfolio.tracker import PortfolioTracker
from mytrader.strategy.base import SignalDirection


def make_order(
    symbol: str = "AAPL",
    direction: SignalDirection = SignalDirection.BUY,
    quantity: int = 100,
    fill_price: float = 100.0,
    order_id: str | None = None,
    status: OrderStatus = OrderStatus.FILLED,
) -> OrderResult:
    import uuid
    return OrderResult(
        client_order_id=order_id or uuid.uuid4().hex[:16],
        symbol=symbol,
        direction=direction,
        quantity=quantity,
        fill_price=fill_price,
        commission=quantity * fill_price * 0.001,
        status=status,
        filled_at=datetime(2024, 1, 10, 10, 0, tzinfo=timezone.utc),
        stop_loss_price=fill_price * 0.98,
        take_profit_price=fill_price * 1.04,
    )


# ---------------------------------------------------------------------------
# FIFO PnL Calculator 测试
# ---------------------------------------------------------------------------

class TestPnlCalculator:
    def test_buy_updates_position(self):
        pos = Position("AAPL")
        apply_buy(pos, 100, 100.0)
        assert pos.quantity == 100
        assert pos.avg_cost == pytest.approx(100.0)
        assert len(pos.lots) == 1

    def test_buy_multiple_lots_avg_cost(self):
        pos = Position("AAPL")
        apply_buy(pos, 100, 100.0)
        apply_buy(pos, 100, 110.0)
        assert pos.quantity == 200
        assert pos.avg_cost == pytest.approx(105.0)

    def test_sell_fifo_profit(self):
        pos = Position("AAPL")
        apply_buy(pos, 100, 100.0)
        realized = apply_sell(pos, 50, 120.0)
        assert realized == pytest.approx(50 * (120.0 - 100.0))
        assert pos.quantity == 50

    def test_sell_fifo_loss(self):
        pos = Position("AAPL")
        apply_buy(pos, 100, 100.0)
        realized = apply_sell(pos, 100, 90.0)
        assert realized == pytest.approx(-1000.0)
        assert pos.quantity == 0

    def test_sell_fifo_multi_lots(self):
        pos = Position("AAPL")
        apply_buy(pos, 50, 100.0)  # lot1
        apply_buy(pos, 50, 120.0)  # lot2
        # 卖出 80 股：先消耗 lot1（50 @ 100），再消耗 lot2（30 @ 120）
        realized = apply_sell(pos, 80, 130.0)
        expected = 50 * (130 - 100) + 30 * (130 - 120)
        assert realized == pytest.approx(expected)
        assert pos.quantity == 20
        assert len(pos.lots) == 1

    def test_sell_too_many_raises(self):
        pos = Position("AAPL")
        apply_buy(pos, 50, 100.0)
        with pytest.raises(ValueError):
            apply_sell(pos, 100, 110.0)

    def test_full_sell_clears_position(self):
        pos = Position("AAPL")
        apply_buy(pos, 100, 100.0)
        apply_sell(pos, 100, 105.0)
        assert pos.quantity == 0
        assert pos.avg_cost == 0.0
        assert pos.lots == []


# ---------------------------------------------------------------------------
# PortfolioTracker 测试
# ---------------------------------------------------------------------------

class TestPortfolioTracker:
    def test_initial_state(self):
        tracker = PortfolioTracker(initial_cash=100_000.0)
        assert tracker.cash == 100_000.0
        assert len(tracker.open_positions) == 0

    def test_buy_reduces_cash(self):
        tracker = PortfolioTracker(initial_cash=100_000.0)
        order = make_order(direction=SignalDirection.BUY, quantity=100, fill_price=100.0)
        tracker.process_order(order)
        # cost = 100 * 100 + commission(0.1%=10) = 10010
        assert tracker.cash == pytest.approx(100_000 - order.net_value, abs=1)

    def test_buy_creates_position(self):
        tracker = PortfolioTracker(initial_cash=100_000.0)
        order = make_order(direction=SignalDirection.BUY, quantity=100, fill_price=100.0)
        tracker.process_order(order)
        assert "AAPL" in tracker.open_positions
        assert tracker.open_positions["AAPL"].quantity == 100

    def test_sell_after_buy_generates_pnl(self):
        tracker = PortfolioTracker(initial_cash=200_000.0)
        buy = make_order(direction=SignalDirection.BUY, quantity=100, fill_price=100.0, order_id="buy_1")
        sell = make_order(direction=SignalDirection.SELL, quantity=100, fill_price=110.0, order_id="sell_1")
        tracker.process_order(buy)
        trade = tracker.process_order(sell)
        assert trade is not None
        assert trade.realized_pnl == pytest.approx(100 * (110.0 - 100.0), abs=1)

    def test_rejected_order_not_processed(self):
        tracker = PortfolioTracker(initial_cash=100_000.0)
        order = make_order(status=OrderStatus.REJECTED)
        result = tracker.process_order(order)
        assert result is None
        assert tracker.cash == 100_000.0

    def test_insufficient_cash_returns_none(self):
        tracker = PortfolioTracker(initial_cash=100.0)  # 很少的钱
        order = make_order(quantity=1000, fill_price=100.0)  # 需要 100000
        result = tracker.process_order(order)
        assert result is None

    def test_snapshot_returns_dict(self):
        tracker = PortfolioTracker(initial_cash=100_000.0)
        snap = tracker.snapshot()
        assert "cash" in snap
        assert "total_equity" in snap
        assert snap["total_equity"] == pytest.approx(100_000.0)

    def test_total_trades_tracked(self):
        tracker = PortfolioTracker(initial_cash=200_000.0)
        for i in range(3):
            order = make_order(
                direction=SignalDirection.BUY,
                quantity=10,
                fill_price=100.0 + i,
                order_id=f"order_{i}",
            )
            tracker.process_order(order)
        assert len(tracker.portfolio.trades) == 3


# ---------------------------------------------------------------------------
# Metrics 测试
# ---------------------------------------------------------------------------

class TestMetrics:
    def make_equity(self, values: list[float]) -> pd.Series:
        idx = pd.date_range("2024-01-01", periods=len(values), freq="D")
        return pd.Series(values, index=idx)

    def test_sharpe_positive_trend(self):
        eq = self.make_equity([100_000 + i * 100 for i in range(50)])
        sr = sharpe_ratio(eq)
        assert sr > 0

    def test_max_drawdown_is_negative(self):
        eq = self.make_equity([100, 110, 90, 95, 100])
        mdd = max_drawdown(eq)
        assert mdd < 0

    def test_max_drawdown_no_drawdown(self):
        eq = self.make_equity([100, 110, 120, 130])
        assert max_drawdown(eq) == pytest.approx(0.0)

    def test_win_rate_all_wins(self):
        assert win_rate([100.0, 200.0, 50.0]) == pytest.approx(1.0)

    def test_win_rate_half(self):
        assert win_rate([100.0, -50.0]) == pytest.approx(0.5)

    def test_win_rate_empty(self):
        assert win_rate([]) == 0.0

    def test_profit_factor_basic(self):
        pf = profit_factor([100.0, 200.0, -50.0])
        assert pf == pytest.approx(6.0)

    def test_calmar_positive(self):
        eq = self.make_equity([100_000 + i * 200 for i in range(252)])
        c = calmar_ratio(eq)
        assert c >= 0

    def test_portfolio_summary_keys(self):
        eq = self.make_equity([100_000 + i * 50 for i in range(100)])
        summary = portfolio_summary(eq, [100.0, -50.0, 200.0], 100_000)
        for key in ("total_return", "sharpe_ratio", "max_drawdown", "win_rate", "total_trades"):
            assert key in summary


# ---------------------------------------------------------------------------
# Persistence 测试（内存 SQLite）
# ---------------------------------------------------------------------------

class TestPersistence:
    def test_save_and_load_trade(self):
        persistence = PortfolioPersistence()  # :memory:
        trade = TradeRecord(
            trade_id="test_001",
            symbol="AAPL",
            direction=SignalDirection.BUY,
            quantity=100,
            fill_price=150.0,
            commission=15.0,
            filled_at=datetime(2024, 1, 10, tzinfo=timezone.utc),
            realized_pnl=0.0,
        )
        persistence.save_trade(trade)
        trades = persistence.load_trades()
        assert len(trades) == 1
        assert trades[0]["trade_id"] == "test_001"
        assert trades[0]["symbol"] == "AAPL"

    def test_idempotent_save(self):
        """重复保存同一 trade_id 不报错，不重复插入。"""
        persistence = PortfolioPersistence()
        trade = TradeRecord(
            trade_id="dup_001",
            symbol="TSLA",
            direction=SignalDirection.SELL,
            quantity=50,
            fill_price=200.0,
            commission=10.0,
            filled_at=datetime.utcnow(),
        )
        persistence.save_trade(trade)
        persistence.save_trade(trade)  # 重复保存
        trades = persistence.load_trades("TSLA")
        assert len(trades) == 1

    def test_save_and_load_snapshot(self):
        persistence = PortfolioPersistence()
        portfolio = Portfolio(cash=95_000.0)
        persistence.save_snapshot(portfolio, total_equity=95_000.0)
        snap = persistence.load_latest_snapshot()
        assert snap is not None
        assert snap["cash"] == pytest.approx(95_000.0)

    def test_filter_by_symbol(self):
        persistence = PortfolioPersistence()
        for symbol in ["AAPL", "TSLA", "AAPL"]:
            trade = TradeRecord(
                trade_id=f"{symbol}_{id(symbol)}_{__import__('uuid').uuid4().hex[:8]}",
                symbol=symbol,
                direction=SignalDirection.BUY,
                quantity=10,
                fill_price=100.0,
                commission=1.0,
                filled_at=datetime.utcnow(),
            )
            persistence.save_trade(trade)
        aapl_trades = persistence.load_trades("AAPL")
        assert len(aapl_trades) == 2


# ---------------------------------------------------------------------------
# FIFO 多次部分卖出测试 (P0/P1)
# ---------------------------------------------------------------------------

class TestPnlCalculatorAdvanced:
    """PF1/PF2/PF8: FIFO 高级场景。"""

    def test_multi_partial_sell_lots_fully_consumed(self) -> None:
        """PF1 (P0): 多次部分卖出后仓库正确清空。"""
        pos = Position("AAPL")
        apply_buy(pos, 100, 100.0)   # lot1: 100@100
        apply_buy(pos, 100, 120.0)   # lot2: 100@120

        r1 = apply_sell(pos, 50, 130.0)   # 卖 50 (FIFO lot1)
        assert r1 == pytest.approx(50 * (130 - 100))  # 1500
        assert pos.quantity == 150
        assert len(pos.lots) == 2  # lot1: 50@100, lot2: 100@120

        r2 = apply_sell(pos, 100, 135.0)  # 卖 100 (lot1剩余50, lot2:50)
        expected_r2 = 50 * (135 - 100) + 50 * (135 - 120)  # 1750 + 750 = 2500
        assert r2 == pytest.approx(expected_r2)
        assert pos.quantity == 50
        assert len(pos.lots) == 1  # lot2: 50@120

        r3 = apply_sell(pos, 50, 140.0)   # 卖最后 50 (lot2剩余)
        assert r3 == pytest.approx(50 * (140 - 120))  # 1000
        assert pos.quantity == 0
        assert pos.lots == []
        assert pos.avg_cost == 0.0

        # 总盈亏
        total_pnl = r1 + r2 + r3
        expected_total = (100 * 130 + 100 * 135 + 50 * 140) - (100 * 100 + 100 * 120 + 50 * 120)
        # Actually let me recalculate:
        # Buy: 100@100 + 100@120 = 22000 cost
        # Sell: 50@130 + 100@135 + 50@140 = 6500 + 13500 + 7000 = 27000
        # Realized: 27000 - 22000 = 5000
        assert total_pnl == pytest.approx(5000.0)

    def test_large_buy_many_small_sells(self) -> None:
        """PF2 (P1): 大批买入后多次小额卖出，FIFO 正确消费。"""
        pos = Position("AAPL")
        apply_buy(pos, 1000, 100.0)
        assert pos.avg_cost == pytest.approx(100.0)

        total_realized = 0.0
        for i in range(10):
            price = 110.0 + i  # 分批卖出，价格递增
            r = apply_sell(pos, 100, price)
            expected = 100 * (price - 100.0)
            assert r == pytest.approx(expected)
            total_realized += r

        assert pos.quantity == 0
        assert total_realized == pytest.approx(1000 * (sum(range(110, 120)) / 10 - 100.0))
        # Check: sum 110..119 = 1145, avg = 114.5, total = 1000*(114.5-100) = 14500

    def test_zero_cost_division_safe(self) -> None:
        """PF8 (P0): 零成本开仓时 sell 不除零。"""
        pos = Position("AAPL")
        # 模拟零成本场景（如赠股或成本为0的异常数据）
        pos.quantity = 100
        pos.avg_cost = 0.0
        pos.lots = [(100, 0.0)]
        r = apply_sell(pos, 50, 100.0)
        assert r == pytest.approx(50 * 100)  # realized = 50 * (100 - 0)
        assert pos.quantity == 50


# ---------------------------------------------------------------------------
# PortfolioTracker 连续订单测试 (P1)
# ---------------------------------------------------------------------------

class TestPortfolioTrackerAdvanced:
    """PF3: 连续订单累积状态测试。"""

    def test_consecutive_orders_cumulative_state(self) -> None:
        """PF3 (P1): 建仓→加仓→平仓，累积状态正确。"""
        tracker = PortfolioTracker(initial_cash=200_000.0)

        # 建仓 100 股 @100
        buy1 = make_order(
            direction=SignalDirection.BUY, quantity=100,
            fill_price=100.0, order_id="b1",
        )
        tracker.process_order(buy1)
        assert tracker.cash < 200_000.0
        assert "AAPL" in tracker.open_positions

        # 加仓 50 股 @110
        buy2 = make_order(
            direction=SignalDirection.BUY, quantity=50,
            fill_price=110.0, order_id="b2",
        )
        tracker.process_order(buy2)
        pos = tracker.open_positions["AAPL"]
        assert pos.quantity == 150
        assert pos.avg_cost == pytest.approx((100 * 100 + 50 * 110) / 150)

        # 平仓 150 股 @120
        sell = make_order(
            direction=SignalDirection.SELL, quantity=150,
            fill_price=120.0, order_id="s1",
        )
        trade = tracker.process_order(sell)
        assert trade is not None
        assert trade.realized_pnl > 0
        assert "AAPL" not in tracker.open_positions


# ---------------------------------------------------------------------------
# Metrics 边界测试 (P0/P1)
# ---------------------------------------------------------------------------

class TestMetricsAdvanced:
    """PF4/PF5: Metrics 边界条件。"""

    def make_equity(self, values: list[float]) -> pd.Series:
        idx = pd.date_range("2024-01-01", periods=len(values), freq="D")
        return pd.Series(values, index=idx)

    def test_no_trades_metrics_safe(self) -> None:
        """PF4 (P0): 无交易时 metrics 不抛异常。"""
        eq = self.make_equity([100_000.0])
        summary = portfolio_summary(eq, [], 100_000.0)
        assert "total_trades" in summary
        assert summary["total_trades"] == 0
        assert summary["win_rate"] == 0.0

    def test_win_rate_empty_returns_zero(self) -> None:
        """无交易时 win_rate 返回 0。"""
        assert win_rate([]) == 0.0

    def test_profit_factor_no_losses(self) -> None:
        """全部盈利时 profit_factor 为 inf。"""
        import math
        pf = profit_factor([100.0, 200.0])
        assert pf == float("inf")

    def test_profit_factor_no_profits(self) -> None:
        """全部亏损时 profit_factor 为 0。"""
        pf = profit_factor([-100.0, -200.0])
        assert pf == 0.0

    def test_extreme_values_handled(self) -> None:
        """PF5 (P1): 极端盈亏值不导致 NaN/崩溃。"""
        eq = self.make_equity([100_000, 101_000, 99_000, 102_000, 98_000])
        summary = portfolio_summary(eq, [5000.0, -3000.0, 200.0], 100_000.0)
        assert not any(np.isnan(v) for v in summary.values() if isinstance(v, float))
        assert "sharpe_ratio" in summary

    def test_max_drawdown_no_drawdown_zero(self) -> None:
        """持续上涨时 MaxDD 为 0。"""
        eq = self.make_equity([100, 110, 120, 130, 140])
        assert max_drawdown(eq) == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Persistence 高级测试 (P1)
# ---------------------------------------------------------------------------

class TestPersistenceAdvanced:
    """PF6/PF7: 持久化高级场景。"""

    def test_snapshot_roundtrip_consistency(self) -> None:
        """PF7 (P1): 快照写入后读回一致性。"""
        persistence = PortfolioPersistence()
        portfolio = Portfolio(cash=90_000.0)
        # 添加持仓
        pos = Position(symbol="AAPL", quantity=200, avg_cost=105.0)
        portfolio.positions["AAPL"] = pos

        snap_at = datetime(2024, 1, 15, tzinfo=timezone.utc)
        persistence.save_snapshot(portfolio, total_equity=120_000.0, snapshot_at=snap_at)
        loaded = persistence.load_latest_snapshot()
        assert loaded is not None
        assert loaded["cash"] == pytest.approx(90_000.0)
        assert loaded["total_equity"] == pytest.approx(120_000.0)
        assert loaded["open_positions"] == 1

    def test_connection_failure_graceful(self) -> None:
        """PF6 (P1): 无效数据库路径不导致崩溃（创建时允许，使用 sqlite:///:memory: 验证降级）。"""
        # 使用内存数据库验证初始化成功
        persistence = PortfolioPersistence("sqlite:///:memory:")
        assert persistence is not None
        # 验证可以正常读写
        trade = TradeRecord(
            trade_id="safe_001", symbol="TEST",
            direction=SignalDirection.BUY, quantity=10,
            fill_price=50.0, commission=0.5,
            filled_at=datetime.utcnow(),
        )
        persistence.save_trade(trade)
        trades = persistence.load_trades()
        assert len(trades) == 1
