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


# ---------------------------------------------------------------------------
# 迭代 #5 新增：get_positions / get_order_by_client_order_id / refresh_pending
# ---------------------------------------------------------------------------

class TestAlpacaBrokerGetPositions:
    def test_get_positions_maps_alpaca_positions_to_reconciliation_format(self):
        """get_positions 返回 ReconciliationService 兼容的 [{symbol, quantity, ...}]。"""
        mock_client = MagicMock()
        # 构造 mock position 列表（Alpaca SDK Position 对象属性）
        pos_aapl = MagicMock()
        pos_aapl.symbol = "AAPL"
        pos_aapl.qty = "10"
        pos_aapl.market_value = "1500.00"
        pos_aapl.avg_entry_price = "148.50"
        pos_aapl.current_price = "150.00"
        pos_aapl.unrealized_pl = "15.00"

        pos_msft = MagicMock()
        pos_msft.symbol = "MSFT"
        pos_msft.qty = "5.5"  # 小数也支持（zero_pct 后会 int 化）
        pos_msft.market_value = "2000.00"
        pos_msft.avg_entry_price = "360.00"
        pos_msft.current_price = "400.00"
        pos_msft.unrealized_pl = "220.00"

        mock_client.get_all_positions.return_value = [pos_aapl, pos_msft]

        broker = AlpacaBroker(
            api_key="k", secret_key="s", paper=True,
            mode="semi_auto", client=mock_client
        )
        positions = broker.get_positions()

        assert len(positions) == 2
        # quantity 必须为 int（ReconciliationService 兼容）
        aapl = next(p for p in positions if p["symbol"] == "AAPL")
        assert aapl["quantity"] == 10
        assert isinstance(aapl["quantity"], int)
        assert aapl["market_value"] == pytest.approx(1500.0)
        assert aapl["avg_entry_price"] == pytest.approx(148.50)

        msft = next(p for p in positions if p["symbol"] == "MSFT")
        assert msft["quantity"] == 5  # int(5.5) = 5
        assert isinstance(msft["quantity"], int)

    def test_get_positions_returns_empty_on_api_error(self):
        """API 异常时不崩溃，返回空列表。"""
        mock_client = MagicMock()
        mock_client.get_all_positions.side_effect = Exception("API timeout")

        broker = AlpacaBroker(
            api_key="k", secret_key="s", paper=True,
            mode="semi_auto", client=mock_client
        )
        positions = broker.get_positions()
        assert positions == []

    def test_get_positions_skips_malformed_entries(self):
        """缺 symbol/qty 的条目被跳过，不抛异常。"""
        mock_client = MagicMock()
        bad_pos = MagicMock()
        bad_pos.symbol = None
        bad_pos.qty = "10"
        good_pos = MagicMock()
        good_pos.symbol = "AAPL"
        good_pos.qty = "5"
        mock_client.get_all_positions.return_value = [bad_pos, good_pos]

        broker = AlpacaBroker(
            api_key="k", secret_key="s", paper=True,
            mode="semi_auto", client=mock_client
        )
        positions = broker.get_positions()
        assert len(positions) == 1
        assert positions[0]["symbol"] == "AAPL"


class TestAlpacaBrokerRefreshPending:
    def test_refresh_pending_orders_updates_filled_order(self):
        """本地 pending 订单在远端变为 filled 后，refresh 应更新本地缓存为 FILLED。"""
        mock_client = MagicMock()
        # 第一次 submit 返回 pending_new
        mock_client.submit_order.return_value = make_mock_alpaca_order("pending_new", 0.0)
        # get_order_by_client_id 返回 filled + filled_avg_price
        filled_order = make_mock_alpaca_order("filled", 152.5)
        mock_client.get_order_by_client_id.return_value = filled_order

        broker = AlpacaBroker(
            api_key="k", secret_key="s", paper=True,
            mode="auto", client=mock_client
        )
        intent = make_intent(order_id="refresh_001")
        broker.submit(intent, make_df())

        # 本地缓存应为 PENDING
        cached = broker.get_order("refresh_001")
        assert cached is not None
        assert cached.status == OrderStatus.PENDING

        # refresh
        refreshed = broker.refresh_pending_orders()
        assert len(refreshed) == 1
        assert refreshed[0].status == OrderStatus.FILLED
        assert refreshed[0].fill_price == pytest.approx(152.5)

        # 本地缓存也被更新为 FILLED
        assert broker.get_order("refresh_001").status == OrderStatus.FILLED

    def test_get_order_by_client_order_id_falls_back_to_cache_when_remote_query_fails(self):
        """远端异常时不崩溃，返回本地缓存。"""
        mock_client = MagicMock()
        mock_client.submit_order.return_value = make_mock_alpaca_order("pending_new", 0.0)
        mock_client.get_order_by_client_id.side_effect = Exception("API timeout")

        broker = AlpacaBroker(
            api_key="k", secret_key="s", paper=True,
            mode="auto", client=mock_client
        )
        intent = make_intent(order_id="fallback_001")
        broker.submit(intent, make_df())

        # 查询：远端异常 → 返回缓存（仍为 PENDING）
        result = broker.get_order_by_client_order_id("fallback_001")
        assert result is not None
        assert result.status == OrderStatus.PENDING  # 未被远端更新

    def test_refresh_pending_returns_empty_when_no_pending(self):
        """无 PENDING 订单时返回空列表。"""
        mock_client = MagicMock()
        broker = AlpacaBroker(
            api_key="k", secret_key="s", paper=True,
            mode="semi_auto", client=mock_client
        )
        # 没有任何订单提交过
        assert broker.refresh_pending_orders() == []

    def test_refresh_pending_skips_terminal_orders(self):
        """FILLED/REJECTED 订单不会触发远端查询。"""
        mock_client = MagicMock()
        mock_client.submit_order.return_value = make_mock_alpaca_order("filled", 150.0)

        broker = AlpacaBroker(
            api_key="k", secret_key="s", paper=True,
            mode="auto", client=mock_client
        )
        intent = make_intent(order_id="terminal_001")
        broker.submit(intent, make_df())

        # refresh 不应调用 get_order_by_client_id
        refreshed = broker.refresh_pending_orders()
        assert refreshed == []
        mock_client.get_order_by_client_id.assert_not_called()
