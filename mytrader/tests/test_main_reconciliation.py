"""Reconciliation callback 测试（迭代 #5 P0-C）。

验证 main.py::_build_reconciliation_callback 修复后：
    - 调用 ReconciliationService(portfolio_tracker=...) 而非 tracker=
    - 调用 svc.run() 而非 svc.reconcile()
    - 读取 report.is_clean 而非 report.has_diff
    - 无差异时 notification.send_message 被调用
    - 有差异时 notification.send_message 包含 diff symbols
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

# 确保 mytrader/ 在 sys.path（main.py 在项目根）
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_components(
    *,
    tracker: MagicMock | None = None,
    broker: MagicMock | None = None,
    notification: MagicMock | None = None,
    bus: MagicMock | None = None,
) -> SimpleNamespace:
    """构造最小 AppComponents-like 对象，供 _build_reconciliation_callback 使用。"""
    return SimpleNamespace(
        tracker=tracker or MagicMock(),
        broker=broker or MagicMock(),
        notification=notification,
        bus=bus,
    )


# ---------------------------------------------------------------------------
# 1. 调用参数：portfolio_tracker= / svc.run() / is_clean
# ---------------------------------------------------------------------------

class TestReconciliationCallbackServiceArgs:
    def test_reconciliation_callback_calls_service_run_with_correct_args(
        self, monkeypatch
    ):
        """callback 应使用 portfolio_tracker= 关键字传给 ReconciliationService。"""
        from main import _build_reconciliation_callback

        fake_service = MagicMock()
        fake_report = MagicMock()
        fake_report.is_clean = True
        fake_report.diffs = []
        fake_report.total_local = 0
        fake_report.total_broker = 0
        fake_service.run.return_value = fake_report

        components = _make_components(
            tracker=MagicMock(),
            broker=MagicMock(),
            notification=MagicMock(),
            bus=MagicMock(),
        )

        # patch ReconciliationService 类
        with patch("mytrader.portfolio.reconciliation.ReconciliationService") as mock_cls:
            mock_cls.return_value = fake_service

            cb = _build_reconciliation_callback(components, sync_fn=None)
            cb()

            # 断言使用 portfolio_tracker= 关键字
            kwargs = mock_cls.call_args.kwargs
            assert "portfolio_tracker" in kwargs
            assert kwargs["portfolio_tracker"] is components.tracker
            # 不应再有 tracker= 关键字
            assert "tracker" not in kwargs

            # 断言调用 svc.run() 而非 svc.reconcile()
            fake_service.run.assert_called_once()
            fake_service.reconcile.assert_not_called()

    def test_reconciliation_callback_uses_is_clean_not_has_diff(self):
        """callback 读取 report.is_clean，不访问 report.has_diff。"""
        from main import _build_reconciliation_callback

        # 构造一个 report 对象：只有 is_clean，没有 has_diff
        fake_report = SimpleNamespace(
            is_clean=True,
            diffs=[],
            total_local=0,
            total_broker=0,
        )
        fake_service = MagicMock()
        fake_service.run.return_value = fake_report

        components = _make_components(
            notification=MagicMock(),
            bus=MagicMock(),
        )

        with patch("mytrader.portfolio.reconciliation.ReconciliationService") as mock_cls:
            mock_cls.return_value = fake_service

            cb = _build_reconciliation_callback(components, sync_fn=None)
            # 不应抛 AttributeError（has_diff 不存在）
            cb()

            fake_service.run.assert_called_once()


# ---------------------------------------------------------------------------
# 2. 通知分支
# ---------------------------------------------------------------------------

class TestReconciliationCallbackNotifications:
    def test_reconciliation_callback_sends_clean_notification(self):
        """clean report 时 notification.send_message 被调用。"""
        from main import _build_reconciliation_callback

        fake_report = SimpleNamespace(
            is_clean=True,
            diffs=[],
            total_local=3,
            total_broker=3,
        )
        fake_service = MagicMock()
        fake_service.run.return_value = fake_report

        notification = MagicMock()
        components = _make_components(notification=notification, bus=MagicMock())

        with patch("mytrader.portfolio.reconciliation.ReconciliationService") as mock_cls:
            mock_cls.return_value = fake_service

            cb = _build_reconciliation_callback(components, sync_fn=None)
            cb()

            notification.send_message.assert_called_once()
            text = notification.send_message.call_args.args[0]
            assert "持仓一致" in text or "No diff" in text or "无差异" in text

    def test_reconciliation_callback_sends_diff_notification(self):
        """diffs 非空时通知内容包含 diff symbols。"""
        from main import _build_reconciliation_callback

        # 构造两个 diff 对象
        diff_aapl = SimpleNamespace(symbol="AAPL", local_qty=10, broker_qty=0, diff_type="local_only")
        diff_msft = SimpleNamespace(symbol="MSFT", local_qty=0, broker_qty=5, diff_type="broker_only")

        fake_report = SimpleNamespace(
            is_clean=False,
            diffs=[diff_aapl, diff_msft],
            total_local=1,
            total_broker=1,
        )
        fake_service = MagicMock()
        fake_service.run.return_value = fake_report

        notification = MagicMock()
        components = _make_components(notification=notification, bus=MagicMock())

        with patch("mytrader.portfolio.reconciliation.ReconciliationService") as mock_cls:
            mock_cls.return_value = fake_service

            cb = _build_reconciliation_callback(components, sync_fn=None)
            cb()

            notification.send_message.assert_called_once()
            text = notification.send_message.call_args.args[0]
            # 通知应包含差异 symbol
            assert "AAPL" in text
            assert "MSFT" in text


# ---------------------------------------------------------------------------
# 3. 兼容性 / 错误隔离
# ---------------------------------------------------------------------------

class TestReconciliationCallbackResilience:
    def test_callback_does_not_crash_when_notification_is_none(self):
        """components.notification 为 None 时不应崩溃。"""
        from main import _build_reconciliation_callback

        fake_report = SimpleNamespace(
            is_clean=True, diffs=[], total_local=0, total_broker=0,
        )
        fake_service = MagicMock()
        fake_service.run.return_value = fake_report

        # notification=None
        components = _make_components(notification=None, bus=None)

        with patch("mytrader.portfolio.reconciliation.ReconciliationService") as mock_cls:
            mock_cls.return_value = fake_service
            cb = _build_reconciliation_callback(components, sync_fn=None)
            # 不应抛异常
            cb()

    def test_callback_does_not_crash_when_service_run_raises(self):
        """svc.run() 抛异常时 callback 应 logger.error，不抛出。"""
        from main import _build_reconciliation_callback

        fake_service = MagicMock()
        fake_service.run.side_effect = Exception("DB error")

        components = _make_components(notification=MagicMock(), bus=MagicMock())

        with patch("mytrader.portfolio.reconciliation.ReconciliationService") as mock_cls:
            mock_cls.return_value = fake_service
            cb = _build_reconciliation_callback(components, sync_fn=None)
            # 不应抛异常（已用 try/except 包裹）
            cb()

    def test_callback_invokes_sync_fn_first(self):
        """sync_fn 应在 reconciliation 之前被调用。"""
        from main import _build_reconciliation_callback

        call_order = []

        def sync_fn():
            call_order.append("sync")

        fake_report = SimpleNamespace(
            is_clean=True, diffs=[], total_local=0, total_broker=0,
        )
        fake_service = MagicMock()
        fake_service.run.side_effect = lambda: (
            call_order.append("reconcile"),
            fake_report,
        )[1]

        components = _make_components(notification=MagicMock(), bus=MagicMock())

        with patch("mytrader.portfolio.reconciliation.ReconciliationService") as mock_cls:
            mock_cls.return_value = fake_service
            cb = _build_reconciliation_callback(components, sync_fn=sync_fn)
            cb()

            assert call_order == ["sync", "reconcile"]

    def test_callback_invokes_paper_metrics_collection(self):
        """callback 末尾应 best-effort 调用 collect_paper_daily_metrics。"""
        from main import _build_reconciliation_callback

        fake_report = SimpleNamespace(
            is_clean=True, diffs=[], total_local=0, total_broker=0,
        )
        fake_service = MagicMock()
        fake_service.run.return_value = fake_report

        components = _make_components(notification=MagicMock(), bus=MagicMock())

        with patch("mytrader.portfolio.reconciliation.ReconciliationService") as mock_cls, \
             patch("mytrader.monitor.paper_metrics.collect_paper_daily_metrics") as mock_metrics:
            mock_cls.return_value = fake_service
            cb = _build_reconciliation_callback(components, sync_fn=None)
            cb()

            mock_metrics.assert_called_once()
            # 验证传入 broker 和 tracker
            kwargs = mock_metrics.call_args.kwargs
            assert kwargs.get("broker") is components.broker
            assert kwargs.get("tracker") is components.tracker
