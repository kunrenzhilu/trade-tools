"""测试 execution 模块：PaperBroker 成交逻辑 + 幂等性 + 滑点。"""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import pytest

from mytrader.execution.models import OrderResult, OrderStatus
from mytrader.execution.paper_broker import PaperBroker
from mytrader.execution.slippage import SlippageModel
from mytrader.risk.models import OrderIntent
from mytrader.strategy.base import SignalDirection


def make_ohlcv(n: int = 20, base_price: float = 100.0) -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=n, freq="D", tz="UTC")
    close_vals = [base_price + i for i in range(n)]
    return pd.DataFrame(
        {
            "open": [v * 0.999 for v in close_vals],
            "high": [v * 1.01 for v in close_vals],
            "low": [v * 0.99 for v in close_vals],
            "close": close_vals,
            "volume": [500_000] * n,
        },
        index=dates,
    )


def make_intent(
    symbol: str = "AAPL",
    direction: SignalDirection = SignalDirection.BUY,
    quantity: int = 100,
    entry_price: float = 105.0,
    ts_index: int = 10,
    df: pd.DataFrame | None = None,
    order_id: str = "",
) -> OrderIntent:
    if df is None:
        df = make_ohlcv()
    return OrderIntent(
        symbol=symbol,
        direction=direction,
        quantity=quantity,
        entry_price=entry_price,
        stop_loss_price=entry_price * 0.98,
        take_profit_price=entry_price * 1.04,
        risk_amount=200.0,
        position_value=entry_price * quantity,
        timestamp=df.index[ts_index],
        strategy_name="test",
        client_order_id=order_id,
    )


# ---------------------------------------------------------------------------
# SlippageModel 测试
# ---------------------------------------------------------------------------

class TestSlippageModel:
    def test_buy_price_increases(self):
        sm = SlippageModel(slippage_pct=0.001)
        adjusted = sm.adjust_price(100.0, SignalDirection.BUY)
        assert adjusted == pytest.approx(100.1)

    def test_sell_price_decreases(self):
        sm = SlippageModel(slippage_pct=0.001)
        adjusted = sm.adjust_price(100.0, SignalDirection.SELL)
        assert adjusted == pytest.approx(99.9)

    def test_commission_calculation(self):
        sm = SlippageModel(commission_pct=0.001)
        commission = sm.calc_commission(100, 100.0)
        assert commission == pytest.approx(10.0)


# ---------------------------------------------------------------------------
# PaperBroker 测试
# ---------------------------------------------------------------------------

class TestPaperBroker:
    def test_buy_order_filled(self):
        df = make_ohlcv(20)
        broker = PaperBroker(slippage_pct=0.001, commission_pct=0.001)
        intent = make_intent(direction=SignalDirection.BUY, ts_index=10, df=df)
        result = broker.submit(intent, df)
        assert result.status == OrderStatus.FILLED
        assert result.quantity == 100
        # 成交价应略高于下一 bar open（含滑点）
        next_open = float(df.iloc[11]["open"])
        assert result.fill_price == pytest.approx(next_open * 1.001, rel=1e-4)

    def test_sell_order_filled(self):
        df = make_ohlcv(20)
        broker = PaperBroker(slippage_pct=0.001)
        intent = make_intent(direction=SignalDirection.SELL, ts_index=10, df=df)
        result = broker.submit(intent, df)
        assert result.status == OrderStatus.FILLED
        next_open = float(df.iloc[11]["open"])
        assert result.fill_price == pytest.approx(next_open * 0.999, rel=1e-4)

    def test_rejected_when_no_next_bar(self):
        """最后一个 bar 信号无法成交（无下一 bar）。"""
        df = make_ohlcv(20)
        broker = PaperBroker()
        intent = make_intent(ts_index=19, df=df)  # 最后一行
        result = broker.submit(intent, df)
        assert result.status == OrderStatus.REJECTED

    def test_idempotency(self):
        """相同 client_order_id 不重复成交。"""
        df = make_ohlcv(20)
        broker = PaperBroker()
        intent = make_intent(ts_index=5, df=df, order_id="test_id_001")
        result1 = broker.submit(intent, df)
        result2 = broker.submit(intent, df)
        assert result1 is result2
        assert len(broker.order_history) == 1

    def test_commission_non_zero(self):
        df = make_ohlcv(20)
        broker = PaperBroker(commission_pct=0.001)
        intent = make_intent(ts_index=5, df=df)
        result = broker.submit(intent, df)
        assert result.commission > 0

    def test_order_history_tracking(self):
        df = make_ohlcv(20)
        broker = PaperBroker()
        for i in range(3):
            intent = make_intent(ts_index=i + 5, df=df)
            broker.submit(intent, df)
        assert len(broker.order_history) == 3

    def test_gross_value(self):
        df = make_ohlcv(20)
        broker = PaperBroker(slippage_pct=0.0, commission_pct=0.0)
        intent = make_intent(quantity=100, ts_index=5, df=df)
        result = broker.submit(intent, df)
        assert result.gross_value == pytest.approx(result.quantity * result.fill_price)

    def test_empty_dataframe_rejected(self) -> None:
        """EX1 (P0): 空 DataFrame 提交订单被拒绝。"""
        broker = PaperBroker()
        empty_df = pd.DataFrame()
        intent = make_intent()
        result = broker.submit(intent, empty_df)
        assert result.status == OrderStatus.REJECTED
        assert len(broker.order_history) == 1  # 仍记录在历史中

    def test_zero_quantity_handled(self) -> None:
        """EX2 (P0): 零数量订单在 submit 层面不崩溃（在 RiskManager 层清零）。"""
        df = make_ohlcv(20)
        broker = PaperBroker()
        intent = make_intent(quantity=0, ts_index=5, df=df)
        result = broker.submit(intent, df)
        assert result.quantity == 0
        # 未崩溃，合理返回结果

    def test_negative_slippage_price_clamped(self) -> None:
        """EX3 (P1): 滑点不会导致负执行价。"""
        df = make_ohlcv(20, base_price=5.0)  # 低价数据
        broker = PaperBroker(slippage_pct=0.02, commission_pct=0.001)
        intent = make_intent(ts_index=5, df=df, quantity=50)
        result = broker.submit(intent, df)
        assert result.status == OrderStatus.FILLED
        assert result.fill_price > 0  # 价格不会变负

    def test_batch_orders_independent(self) -> None:
        """EX4 (P1): 多个 OrderIntent 批量提交，不相互干扰。"""
        df = make_ohlcv(20)
        broker = PaperBroker()
        intents = [
            make_intent(symbol="AAPL", ts_index=5, df=df, order_id="id_1"),
            make_intent(symbol="TSLA", ts_index=7, df=df, order_id="id_2"),
            make_intent(symbol="MSFT", ts_index=9, df=df, order_id="id_3"),
        ]
        results = [broker.submit(i, df) for i in intents]
        assert all(r.status == OrderStatus.FILLED for r in results)
        assert results[0].symbol == "AAPL"
        assert results[1].symbol == "TSLA"
        assert results[2].symbol == "MSFT"
        assert len(broker.order_history) == 3

    def test_order_history_persistence(self) -> None:
        """EX5 (P1): 连续交易后 order_history 完整记录。"""
        df = make_ohlcv(20)
        broker = PaperBroker()
        for i in range(5):
            intent = make_intent(
                symbol=f"STOCK_{i}", ts_index=i + 5, df=df,
                order_id=f"ex5_{i}",
            )
            broker.submit(intent, df)
        assert len(broker.order_history) == 5
        # 确认所有订单都被记录
        order_ids = {r.client_order_id for r in broker.order_history}
        assert order_ids == {f"ex5_{i}" for i in range(5)}
