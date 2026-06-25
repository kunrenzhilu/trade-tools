"""测试 Phase 3 AlpacaBroker — 美股券商接入（Mock alpaca-py）。"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from mytrader.execution.alpaca_broker import AlpacaBroker
from mytrader.execution.models import OrderResult, OrderStatus
from mytrader.risk.models import OrderIntent
from mytrader.strategy.base import SignalDirection


# ---------------------------------------------------------------------------
# 测试夹具
# ---------------------------------------------------------------------------

def make_intent(
    symbol: str = "AAPL",
    direction: SignalDirection = SignalDirection.BUY,
    quantity: int = 100,
    order_id: str = "test_alpaca_001",
) -> OrderIntent:
    return OrderIntent(
        symbol=symbol,
        direction=direction,
        quantity=quantity,
        entry_price=150.0,
        stop_loss_price=147.0,
        take_profit_price=156.0,
        risk_amount=300.0,
        position_value=quantity * 150.0,
        timestamp=datetime.now(timezone.utc),
        strategy_name="dual_ma",
        client_order_id=order_id,
    )


def make_df() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=5, freq="D", tz="UTC")
    return pd.DataFrame({"open": [100.0] * 5, "close": [100.0] * 5}, index=dates)


def make_mock_alpaca_order(
    status: str = "filled",
    filled_avg_price: float = 150.2,
    order_id: str = "alpaca-uuid-001",
) -> MagicMock:
    mock_order = MagicMock()
    mock_order.status = status
    mock_order.filled_avg_price = str(filled_avg_price)
    mock_order.id = order_id
    return mock_order


# ---------------------------------------------------------------------------
# semi_auto 模式测试
# ---------------------------------------------------------------------------

class TestAlpacaBrokerSemiAuto:
    def test_semi_auto_returns_pending(self):
        """semi_auto 模式返回 PENDING 状态，不调用 API。"""
        mock_client = MagicMock()
        broker = AlpacaBroker(
            api_key="key", secret_key="secret", paper=True,
            mode="semi_auto", client=mock_client
        )
        intent = make_intent()
        result = broker.submit(intent, make_df())

        assert result.status == OrderStatus.PENDING
        assert result.symbol == "AAPL"
        assert result.fill_price == 0.0
        mock_client.submit_order.assert_not_called()

    def test_semi_auto_idempotent(self):
        """相同 client_order_id 不重复提交。"""
        broker = AlpacaBroker(api_key="k", secret_key="s", mode="semi_auto")
        intent = make_intent(order_id="dup_001")
        df = make_df()

        r1 = broker.submit(intent, df)
        r2 = broker.submit(intent, df)

        assert r1 is r2

    def test_semi_auto_stores_order_history(self):
        """提交后可在 order_history 中找到。"""
        broker = AlpacaBroker(api_key="k", secret_key="s", mode="semi_auto")
        intent = make_intent(order_id="hist_001")
        broker.submit(intent, make_df())

        assert len(broker.order_history) == 1
        assert broker.order_history[0].client_order_id == "hist_001"

    def test_semi_auto_buy_meta(self):
        """semi_auto meta 包含 broker 和 mode。"""
        broker = AlpacaBroker(api_key="k", secret_key="s", mode="semi_auto")
        result = broker.submit(make_intent(), make_df())
        assert result.meta.get("broker") == "alpaca"
        assert result.meta.get("mode") == "semi_auto"

    def test_semi_auto_sell(self):
        """SELL 方向的 semi_auto 也返回 PENDING。"""
        broker = AlpacaBroker(api_key="k", secret_key="s", mode="semi_auto")
        intent = make_intent(direction=SignalDirection.SELL, order_id="sell_001")
        result = broker.submit(intent, make_df())
        assert result.status == OrderStatus.PENDING
        assert result.direction == SignalDirection.SELL


# ---------------------------------------------------------------------------
# auto 模式测试（Mock alpaca-py）
# ---------------------------------------------------------------------------

class TestAlpacaBrokerAuto:
    def test_auto_buy_filled(self):
        """auto 模式 BUY 提交成功，解析 FILLED 状态。"""
        mock_client = MagicMock()
        mock_client.submit_order.return_value = make_mock_alpaca_order("filled", 150.2)

        broker = AlpacaBroker(api_key="k", secret_key="s", mode="auto", client=mock_client)
        result = broker.submit(make_intent(order_id="auto_buy_001"), make_df())

        assert result.status == OrderStatus.FILLED
        assert result.fill_price == pytest.approx(150.2)
        assert result.commission == 0.0  # Alpaca 零佣金
        mock_client.submit_order.assert_called_once()

    def test_auto_sell_filled(self):
        """auto 模式 SELL 提交成功。"""
        mock_client = MagicMock()
        mock_client.submit_order.return_value = make_mock_alpaca_order("filled", 149.8)

        broker = AlpacaBroker(api_key="k", secret_key="s", mode="auto", client=mock_client)
        intent = make_intent(direction=SignalDirection.SELL, order_id="auto_sell_001")
        result = broker.submit(intent, make_df())

        assert result.status == OrderStatus.FILLED
        assert result.fill_price == pytest.approx(149.8)

    def test_auto_api_exception_returns_rejected(self):
        """API 调用异常时返回 REJECTED 而非抛出。"""
        mock_client = MagicMock()
        mock_client.submit_order.side_effect = Exception("API rate limit")

        broker = AlpacaBroker(api_key="k", secret_key="s", mode="auto", client=mock_client)
        result = broker.submit(make_intent(order_id="err_001"), make_df())

        assert result.status == OrderStatus.REJECTED
        assert "API rate limit" in result.rejection_reason

    def test_auto_pending_status_parsed(self):
        """pending_new 状态解析为 PENDING。"""
        mock_client = MagicMock()
        mock_client.submit_order.return_value = make_mock_alpaca_order("pending_new", 0.0)

        broker = AlpacaBroker(api_key="k", secret_key="s", mode="auto", client=mock_client)
        result = broker.submit(make_intent(order_id="pend_001"), make_df())
        assert result.status == OrderStatus.PENDING

    def test_auto_idempotent(self):
        """相同 client_order_id 不重复调用 API。"""
        mock_client = MagicMock()
        mock_client.submit_order.return_value = make_mock_alpaca_order()

        broker = AlpacaBroker(api_key="k", secret_key="s", mode="auto", client=mock_client)
        intent = make_intent(order_id="idem_001")
        df = make_df()

        broker.submit(intent, df)
        broker.submit(intent, df)

        mock_client.submit_order.assert_called_once()

    def test_auto_meta_contains_broker_info(self):
        """auto meta 包含 alpaca_order_id。"""
        mock_client = MagicMock()
        mock_client.submit_order.return_value = make_mock_alpaca_order(order_id="alpaca-xyz")

        broker = AlpacaBroker(api_key="k", secret_key="s", mode="auto", client=mock_client)
        result = broker.submit(make_intent(order_id="meta_001"), make_df())
        assert result.meta.get("alpaca_order_id") == "alpaca-xyz"


# ---------------------------------------------------------------------------
# cancel 测试
# ---------------------------------------------------------------------------

class TestAlpacaBrokerCancel:
    def test_cancel_pending_semi_auto(self):
        """semi_auto PENDING 订单可被取消。"""
        mock_client = MagicMock()
        broker = AlpacaBroker(api_key="k", secret_key="s", mode="semi_auto", client=mock_client)
        intent = make_intent(order_id="cancel_001")
        broker.submit(intent, make_df())

        # 手动设置为 PENDING（semi_auto 默认就是 PENDING）
        result = broker.get_order("cancel_001")
        assert result is not None
        result.status = OrderStatus.PENDING

        cancel_ok = broker.cancel("cancel_001")
        # semi_auto 模式下 cancel 通过 alpaca client，Mock 时 client 已注入
        mock_client.cancel_order_by_id.assert_called_once_with("cancel_001")

    def test_cancel_nonexistent_returns_false(self):
        """取消不存在的订单返回 False。"""
        broker = AlpacaBroker(api_key="k", secret_key="s", mode="semi_auto")
        result = broker.cancel("nonexistent_id")
        assert result is False
