"""PaperDailyMetrics 测试（迭代 #5 P0-D）。

spec §4.5 测试清单：
    1. test_collect_paper_daily_metrics_writes_json
    2. test_metrics_no_credentials_or_account_api_does_not_crash
    3. test_metrics_counts_order_statuses
    4. test_metrics_does_not_include_sensitive_fields
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from mytrader.execution.models import OrderResult, OrderStatus
from mytrader.monitor.paper_metrics import (
    PaperDailyMetrics,
    _sanitize,
    collect_paper_daily_metrics,
)
from mytrader.portfolio.models import Portfolio
from mytrader.strategy.base import SignalDirection


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_broker(
    *,
    account_status: str = "connected",
    cash: float = 50_000.0,
    buying_power: float = 100_000.0,
    positions: list[dict] | None = None,
    order_history: list[OrderResult] | None = None,
):
    broker = MagicMock()
    broker.health_check.return_value = {
        "status": account_status,
        "account_id": "acct_test",
        "cash": cash,
        "buying_power": buying_power,
        "paper": True,
    }
    broker.get_positions.return_value = positions or []
    broker.order_history = order_history or []
    return broker


def _make_tracker(*, cash: float = 50_000.0, positions: dict | None = None):
    tracker = MagicMock()
    portfolio = Portfolio(cash=cash)
    if positions:
        portfolio.positions = positions
    tracker.portfolio = portfolio
    tracker.open_positions = positions or {}
    return tracker


def _make_order(
    *,
    client_order_id: str = "ord_001",
    status: OrderStatus = OrderStatus.FILLED,
    symbol: str = "AAPL",
    quantity: int = 10,
) -> OrderResult:
    return OrderResult(
        client_order_id=client_order_id,
        symbol=symbol,
        direction=SignalDirection.BUY,
        quantity=quantity,
        fill_price=150.0,
        commission=0.0,
        status=status,
        filled_at=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# 1. 写出 JSON
# ---------------------------------------------------------------------------

class TestCollectPaperDailyMetricsWritesJson:
    def test_collect_paper_daily_metrics_writes_json(self, tmp_path: Path):
        """函数应写出 JSON 文件到指定目录，结构完整。"""
        broker = _make_broker(
            cash=50_000.0,
            buying_power=100_000.0,
            positions=[{"symbol": "AAPL", "quantity": 10}],
        )
        tracker = _make_tracker(cash=50_000.0)

        out = collect_paper_daily_metrics(
            broker=broker,
            tracker=tracker,
            scan_summary=None,
            data_status={"symbols": 515, "latest_bar": "2026-07-02"},
            output_dir=tmp_path,
            today=date(2026, 7, 3),
        )

        # 文件存在
        assert out.exists()
        assert out.name == "2026-07-03.json"
        assert out.parent == tmp_path

        # 解析 JSON
        data = json.loads(out.read_text(encoding="utf-8"))

        # 必需字段
        assert data["date"] == "2026-07-03"
        assert "account" in data
        assert "signals" in data
        assert "orders" in data
        assert "positions" in data
        assert "risk" in data
        assert "data" in data

        # account 字段
        assert data["account"]["cash"] == pytest.approx(50_000.0)
        assert data["account"]["buying_power"] == pytest.approx(100_000.0)
        # positions
        assert data["positions"]["local_count"] == 0
        assert data["positions"]["broker_count"] == 1
        assert data["positions"]["diff_count"] == 1  # AAPL in broker but not local

        # data
        assert data["data"]["symbols"] == 515
        assert data["data"]["latest_bar"] == "2026-07-02"

    def test_metrics_creates_output_dir_if_missing(self, tmp_path: Path):
        """输出目录不存在时应自动创建。"""
        broker = _make_broker()
        tracker = _make_tracker()

        nested = tmp_path / "deep" / "path" / "metrics"
        out = collect_paper_daily_metrics(
            broker=broker, tracker=tracker,
            output_dir=nested,
            today=date(2026, 7, 3),
        )
        assert out.exists()
        assert nested.exists()


# ---------------------------------------------------------------------------
# 2. 缺 credentials / account API 时不崩溃
# ---------------------------------------------------------------------------

class TestMetricsResilience:
    def test_metrics_no_credentials_or_account_api_does_not_crash(self, tmp_path: Path):
        """broker 不支持 health_check / get_account 时不崩溃。"""
        # 构造一个最简 broker：只有 order_history
        broker = MagicMock(spec=["order_history"])
        broker.order_history = []
        tracker = _make_tracker(cash=30_000.0)

        out = collect_paper_daily_metrics(
            broker=broker, tracker=tracker,
            output_dir=tmp_path,
            today=date(2026, 7, 3),
        )
        assert out.exists()

        data = json.loads(out.read_text(encoding="utf-8"))
        # account 字段填 0（health_check 不存在 → 走 tracker.portfolio.cash 兜底）
        assert data["account"]["cash"] == pytest.approx(30_000.0)
        assert data["account"]["equity"] == pytest.approx(30_000.0)

    def test_metrics_handles_broker_exception(self, tmp_path: Path):
        """broker.health_check() 抛异常时不崩溃。"""
        broker = MagicMock()
        broker.health_check.side_effect = Exception("API error")
        broker.get_positions.side_effect = Exception("API error")
        broker.order_history = []

        tracker = _make_tracker()

        out = collect_paper_daily_metrics(
            broker=broker, tracker=tracker,
            output_dir=tmp_path,
            today=date(2026, 7, 3),
        )
        # 不应抛异常，文件正常写出
        assert out.exists()


# ---------------------------------------------------------------------------
# 3. 订单状态计数
# ---------------------------------------------------------------------------

class TestMetricsOrderCounts:
    def test_metrics_counts_order_statuses(self, tmp_path: Path):
        """orders 字段应正确统计 submitted/filled/pending/rejected 数量。"""
        history = [
            _make_order(client_order_id="f1", status=OrderStatus.FILLED),
            _make_order(client_order_id="f2", status=OrderStatus.FILLED, symbol="MSFT"),
            _make_order(client_order_id="p1", status=OrderStatus.PENDING, symbol="TSLA"),
            _make_order(client_order_id="r1", status=OrderStatus.REJECTED, symbol="JPM"),
        ]
        broker = _make_broker(order_history=history)
        tracker = _make_tracker()

        out = collect_paper_daily_metrics(
            broker=broker, tracker=tracker,
            output_dir=tmp_path,
            today=date(2026, 7, 3),
        )
        data = json.loads(out.read_text(encoding="utf-8"))

        assert data["orders"]["submitted"] == 4
        assert data["orders"]["filled"] == 2
        assert data["orders"]["pending"] == 1
        assert data["orders"]["rejected"] == 1

    def test_metrics_orders_zero_when_empty(self, tmp_path: Path):
        """空 order_history 时 orders 字段全为 0。"""
        broker = _make_broker()
        tracker = _make_tracker()

        out = collect_paper_daily_metrics(
            broker=broker, tracker=tracker,
            output_dir=tmp_path,
            today=date(2026, 7, 3),
        )
        data = json.loads(out.read_text(encoding="utf-8"))

        assert data["orders"] == {
            "submitted": 0, "filled": 0, "pending": 0, "rejected": 0,
        }


# ---------------------------------------------------------------------------
# 4. 敏感字段过滤
# ---------------------------------------------------------------------------

class TestMetricsNoSensitiveFields:
    def test_metrics_does_not_include_sensitive_fields(self, tmp_path: Path):
        """JSON 输出不应包含 api_key / secret / token 等敏感字段。

        将敏感字段注入 broker.health_check() 返回的 account dict（_collect_account
        只读 cash/buying_power/equity，多余字段不会进入输出）以及 data_status
        （_collect_data_status 也只读 symbols/latest_bar）。

        本测试覆盖两条防线：
            1. _collect_* 函数只读取白名单字段（最小暴露）
            2. _sanitize 在 JSON 输出时递归剔除敏感 key（兜底）
        """
        broker = MagicMock()
        broker.health_check.return_value = {
            "status": "connected",
            "cash": 50_000.0,
            "buying_power": 100_000.0,
            "paper": True,
            # 故意注入敏感字段
            "api_key": "AKIA1234567890",
            "secret_key": "SHHH_SECRET",
        }
        broker.get_positions.return_value = []
        broker.order_history = []

        tracker = _make_tracker()

        out = collect_paper_daily_metrics(
            broker=broker, tracker=tracker,
            data_status={
                "symbols": 100,
                "latest_bar": "2026-07-02",
                "api_key": "AKIA1234567890",   # 注入到 data_status
            },
            output_dir=tmp_path,
            today=date(2026, 7, 3),
        )
        content = out.read_text(encoding="utf-8")

        # 不应包含任何敏感值
        assert "AKIA1234567890" not in content
        assert "SHHH_SECRET" not in content
        # 敏感 key 也不应出现
        assert "api_key" not in content.lower()
        assert "secret_key" not in content.lower()
        assert "token" not in content.lower()

        # 但 safe 字段应保留
        data = json.loads(content)
        assert data["data"]["symbols"] == 100
        assert data["data"]["latest_bar"] == "2026-07-02"
        assert data["account"]["cash"] == pytest.approx(50_000.0)

    def test_sanitize_helper_directly(self):
        """_sanitize 在 dict / list / nested 上递归生效。"""
        obj = {
            "api_key": "LEAKED",
            "safe_int": 42,
            "nested": {
                "token": "LEAKED",
                "list_field": ["a", {"secret_key": "LEAKED", "ok": 1}],
            },
        }
        clean = _sanitize(obj)
        assert clean == {
            "safe_int": 42,
            "nested": {
                "list_field": ["a", {"ok": 1}],
            },
        }
        # 确认敏感值确实被剔除
        assert "LEAKED" not in str(clean)


# ---------------------------------------------------------------------------
# 5. PaperDailyMetrics dataclass
# ---------------------------------------------------------------------------

class TestPaperDailyMetricsDataclass:
    def test_to_dict_returns_sanitize_safe(self):
        """PaperDailyMetrics.to_dict() 应调用 _sanitize。"""
        m = PaperDailyMetrics(
            date="2026-07-03",
            account={"cash": 1000.0, "api_key": "LEAKED"},
            signals={"raw": 5},
            orders={"submitted": 5},
            positions={"local_count": 3},
            risk={"daily_return": 0.01},
            data={"symbols": 500},
        )
        d = m.to_dict()
        assert "api_key" not in d["account"]
        assert d["account"]["cash"] == pytest.approx(1000.0)
        assert d["date"] == "2026-07-03"
