"""测试 Phase 3 ReconciliationService — 本地持仓与券商持仓对账。"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from mytrader.portfolio.reconciliation import (
    ReconciliationService,
    ReconciliationReport,
    PositionDiff,
)
from mytrader.portfolio.models import Portfolio, Position
from mytrader.portfolio.tracker import PortfolioTracker
from mytrader.infra.event_bus import EventBus, Events


# ---------------------------------------------------------------------------
# 测试夹具
# ---------------------------------------------------------------------------

def make_tracker_with_positions(positions: dict[str, int]) -> PortfolioTracker:
    """创建有指定持仓的 PortfolioTracker（直接注入 Position 对象）。"""
    tracker = PortfolioTracker(initial_cash=100_000.0)
    for symbol, qty in positions.items():
        pos = Position(symbol=symbol, quantity=qty, avg_cost=100.0)
        tracker.portfolio.positions[symbol] = pos
    return tracker


def make_broker_with_positions(positions: dict[str, int]) -> MagicMock:
    """创建返回指定持仓的 Mock Broker。"""
    broker = MagicMock()
    broker.get_positions.return_value = [
        {"symbol": symbol, "quantity": qty, "avg_cost": 100.0}
        for symbol, qty in positions.items()
    ]
    return broker


# ---------------------------------------------------------------------------
# 无差异场景
# ---------------------------------------------------------------------------

class TestReconciliationClean:
    def test_clean_report_when_positions_match(self):
        """本地与券商持仓完全一致时报告为 clean。"""
        tracker = make_tracker_with_positions({"AAPL": 100, "TSLA": 50})
        broker = make_broker_with_positions({"AAPL": 100, "TSLA": 50})
        svc = ReconciliationService(tracker, broker)

        report = svc.run()
        assert report.is_clean

    def test_clean_report_no_diffs(self):
        """无差异时 diffs 列表为空。"""
        tracker = make_tracker_with_positions({"AAPL": 100})
        broker = make_broker_with_positions({"AAPL": 100})
        svc = ReconciliationService(tracker, broker)
        report = svc.run()
        assert len(report.diffs) == 0


# ---------------------------------------------------------------------------
# 差异场景
# ---------------------------------------------------------------------------

class TestReconciliationDiff:
    def test_local_only_detected(self):
        """本地有持仓但券商无持仓（local_only）。"""
        tracker = make_tracker_with_positions({"AAPL": 100, "TSLA": 50})
        broker = make_broker_with_positions({"AAPL": 100})  # TSLA 券商无
        svc = ReconciliationService(tracker, broker)
        report = svc.run()

        assert not report.is_clean
        tsla_diffs = [d for d in report.diffs if d.symbol == "TSLA"]
        assert len(tsla_diffs) == 1
        assert tsla_diffs[0].diff_type == "local_only"
        assert tsla_diffs[0].local_qty == 50
        assert tsla_diffs[0].broker_qty == 0

    def test_broker_only_detected(self):
        """券商有持仓但本地无（broker_only）。"""
        tracker = make_tracker_with_positions({"AAPL": 100})
        broker = make_broker_with_positions({"AAPL": 100, "NVDA": 200})  # NVDA 本地无
        svc = ReconciliationService(tracker, broker)
        report = svc.run()

        nvda_diffs = [d for d in report.diffs if d.symbol == "NVDA"]
        assert len(nvda_diffs) == 1
        assert nvda_diffs[0].diff_type == "broker_only"
        assert nvda_diffs[0].broker_qty == 200

    def test_qty_mismatch_detected(self):
        """本地和券商数量不符（qty_mismatch）。"""
        tracker = make_tracker_with_positions({"AAPL": 100})
        broker = make_broker_with_positions({"AAPL": 80})  # 数量不符
        svc = ReconciliationService(tracker, broker)
        report = svc.run()

        aapl_diffs = [d for d in report.diffs if d.symbol == "AAPL"]
        assert len(aapl_diffs) == 1
        assert aapl_diffs[0].diff_type == "qty_mismatch"
        assert aapl_diffs[0].diff_abs == 20

    def test_multiple_diffs(self):
        """多个标的同时出现差异。"""
        tracker = make_tracker_with_positions({"AAPL": 100, "TSLA": 50, "NVDA": 30})
        broker = make_broker_with_positions({"AAPL": 90, "MSFT": 200})  # TSLA/NVDA丢失，MSFT多出
        svc = ReconciliationService(tracker, broker)
        report = svc.run()

        assert not report.is_clean
        symbols = {d.symbol for d in report.diffs}
        assert "AAPL" in symbols  # qty_mismatch
        assert "TSLA" in symbols  # local_only
        assert "NVDA" in symbols  # local_only
        assert "MSFT" in symbols  # broker_only


# ---------------------------------------------------------------------------
# 事件总线集成
# ---------------------------------------------------------------------------

class TestReconciliationEventBus:
    def test_diff_publishes_event(self):
        """发现差异时发布 RECONCILIATION_DIFF 事件。"""
        tracker = make_tracker_with_positions({"AAPL": 100})
        broker = make_broker_with_positions({"AAPL": 80})

        bus = EventBus()
        received: list = []
        bus.subscribe(Events.RECONCILIATION_DIFF, lambda payload: received.append(payload))

        svc = ReconciliationService(tracker, broker, event_bus=bus)
        svc.run()

        assert len(received) == 1
        assert isinstance(received[0], ReconciliationReport)
        assert not received[0].is_clean

    def test_clean_does_not_publish_event(self):
        """无差异时不发布事件。"""
        tracker = make_tracker_with_positions({"AAPL": 100})
        broker = make_broker_with_positions({"AAPL": 100})

        bus = EventBus()
        received: list = []
        bus.subscribe(Events.RECONCILIATION_DIFF, lambda payload: received.append(payload))

        svc = ReconciliationService(tracker, broker, event_bus=bus)
        svc.run()

        assert len(received) == 0


# ---------------------------------------------------------------------------
# Broker 不支持 get_positions 场景
# ---------------------------------------------------------------------------

class TestReconciliationNoGetPositions:
    def test_paper_broker_no_get_positions(self):
        """PaperBroker 不支持 get_positions，对账服务应优雅跳过。"""
        from mytrader.execution.paper_broker import PaperBroker
        tracker = make_tracker_with_positions({"AAPL": 100})
        broker = PaperBroker()

        svc = ReconciliationService(tracker, broker)
        report = svc.run()

        # 不报错，返回空对账报告（clean）
        assert report is not None

    def test_broker_get_positions_exception(self):
        """get_positions 抛异常时优雅处理。"""
        broker = MagicMock()
        broker.get_positions.side_effect = ConnectionError("broker offline")

        tracker = make_tracker_with_positions({"AAPL": 100})
        svc = ReconciliationService(tracker, broker)
        report = svc.run()

        assert report is not None  # 不崩溃


# ---------------------------------------------------------------------------
# auto_sync 测试
# ---------------------------------------------------------------------------

class TestReconciliationAutoSync:
    def test_auto_sync_updates_local_quantity(self):
        """auto_sync=True 时，本地数量以券商为准修正。"""
        tracker = make_tracker_with_positions({"AAPL": 100})
        broker = make_broker_with_positions({"AAPL": 80})

        svc = ReconciliationService(tracker, broker, auto_sync=True)
        svc.run()

        # 本地 AAPL 数量应被修正为 80
        assert tracker.portfolio.positions["AAPL"].quantity == 80

    def test_no_auto_sync_does_not_modify_local(self):
        """auto_sync=False（默认）时不修改本地记录。"""
        tracker = make_tracker_with_positions({"AAPL": 100})
        broker = make_broker_with_positions({"AAPL": 80})

        svc = ReconciliationService(tracker, broker, auto_sync=False)
        svc.run()

        assert tracker.portfolio.positions["AAPL"].quantity == 100


# ---------------------------------------------------------------------------
# PositionDiff 测试
# ---------------------------------------------------------------------------

class TestPositionDiff:
    def test_diff_abs(self):
        d = PositionDiff("AAPL", 100, 80, "qty_mismatch")
        assert d.diff_abs == 20

    def test_str_representation(self):
        d = PositionDiff("TSLA", 50, 0, "local_only")
        s = str(d)
        assert "TSLA" in s
        assert "local_only" in s

    def test_report_summary_clean(self):
        """clean 报告摘要含成功标志。"""
        report = ReconciliationReport(
            checked_at=datetime.now(timezone.utc),
            diffs=[],
        )
        assert "CLEAN" in report.summary()

    def test_report_summary_diff(self):
        """有差异的报告摘要含 DIFF。"""
        report = ReconciliationReport(
            checked_at=datetime.now(timezone.utc),
            diffs=[PositionDiff("AAPL", 100, 80, "qty_mismatch")],
        )
        assert "DIFF" in report.summary()
        assert "AAPL" in report.summary()
