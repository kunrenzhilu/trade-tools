"""测试 Phase 3 Monitor Layer — HealthChecker + logger_setup。"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from mytrader.monitor.health_checker import (
    HealthChecker,
    HealthReport,
    HealthStatus,
)
from mytrader.monitor.logger_setup import setup_logger


# ---------------------------------------------------------------------------
# HealthChecker 测试
# ---------------------------------------------------------------------------

class TestHealthChecker:
    def test_empty_checker_returns_healthy(self):
        """无检查项时整体状态为 healthy。"""
        checker = HealthChecker()
        report = checker.run_all()
        assert report.status == "healthy"
        assert report.is_healthy

    def test_all_ok_returns_healthy(self):
        """所有检查项通过时返回 healthy。"""
        checker = HealthChecker()
        checker.register("check_a", lambda: (HealthStatus.OK, "ok"))
        checker.register("check_b", lambda: (HealthStatus.OK, "ok"))

        report = checker.run_all()
        assert report.status == "healthy"
        assert len(report.failed_checks) == 0

    def test_one_failed_returns_degraded(self):
        """一项失败时状态为 degraded。"""
        checker = HealthChecker()
        checker.register("check_ok", lambda: (HealthStatus.OK, "ok"))
        checker.register("check_fail", lambda: ("failed: timeout", "timeout"))

        report = checker.run_all()
        assert report.status == "degraded"
        assert "check_fail" in report.failed_checks

    def test_all_failed_returns_unhealthy(self):
        """所有项失败时状态为 unhealthy。"""
        checker = HealthChecker()
        checker.register("check_a", lambda: ("failed: a", "err"))
        checker.register("check_b", lambda: ("failed: b", "err"))

        report = checker.run_all()
        assert report.status == "unhealthy"

    def test_check_exception_treated_as_failed(self):
        """检查函数抛出异常时被视为失败，不传播。"""
        checker = HealthChecker()
        def bad_check():
            raise RuntimeError("check crashed")
        checker.register("crash_check", bad_check)

        report = checker.run_all()
        assert report.status == "unhealthy"
        assert "crash_check" in report.failed_checks

    def test_failed_checks_property(self):
        """failed_checks 返回所有失败项名称。"""
        checker = HealthChecker()
        checker.register("ok", lambda: (HealthStatus.OK, "fine"))
        checker.register("bad1", lambda: ("failed: x", "x"))
        checker.register("bad2", lambda: ("failed: y", "y"))

        report = checker.run_all()
        assert set(report.failed_checks) == {"bad1", "bad2"}

    def test_run_single_check_ok(self):
        """run_check 单个检查项 OK。"""
        checker = HealthChecker()
        checker.register("db", lambda: (HealthStatus.OK, "connected"))

        status, detail = checker.run_check("db")
        assert status == HealthStatus.OK

    def test_run_single_check_not_registered(self):
        """run_check 查询未注册项返回 UNKNOWN。"""
        checker = HealthChecker()
        status, detail = checker.run_check("nonexistent")
        assert status == HealthStatus.UNKNOWN

    def test_details_populated(self):
        """details 字段包含各检查项详细信息。"""
        checker = HealthChecker()
        checker.register("db", lambda: (HealthStatus.OK, "latency=5ms"))

        report = checker.run_all()
        assert report.details.get("db") == "latency=5ms"


# ---------------------------------------------------------------------------
# register_database 测试
# ---------------------------------------------------------------------------

class TestHealthCheckerDatabase:
    def test_register_database_ok(self):
        """SQLAlchemy 引擎可用时返回 ok。"""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.return_value = None
        mock_engine.connect.return_value = mock_conn

        checker = HealthChecker()
        checker.register_database(mock_engine)
        status, _ = checker.run_check("database")
        assert status == HealthStatus.OK

    def test_register_database_failed(self):
        """引擎连接失败时返回 failed。"""
        mock_engine = MagicMock()
        mock_engine.connect.side_effect = Exception("DB connection failed")

        checker = HealthChecker()
        checker.register_database(mock_engine)
        status, detail = checker.run_check("database")
        assert status != HealthStatus.OK
        assert "failed" in status


# ---------------------------------------------------------------------------
# register_scheduler 测试
# ---------------------------------------------------------------------------

class TestHealthCheckerScheduler:
    def test_register_scheduler_running(self):
        """调度器运行中时返回 ok。"""
        mock_sched = MagicMock()
        mock_sched.running = True
        mock_sched.get_jobs.return_value = [MagicMock(), MagicMock()]

        checker = HealthChecker()
        checker.register_scheduler(mock_sched)
        status, detail = checker.run_check("scheduler")
        assert status == HealthStatus.OK
        assert "2 jobs" in detail

    def test_register_scheduler_not_running(self):
        """调度器未运行时返回 failed。"""
        mock_sched = MagicMock()
        mock_sched.running = False

        checker = HealthChecker()
        checker.register_scheduler(mock_sched)
        status, _ = checker.run_check("scheduler")
        assert status != HealthStatus.OK


# ---------------------------------------------------------------------------
# HealthReport 测试
# ---------------------------------------------------------------------------

class TestHealthReport:
    def test_is_healthy_true(self):
        report = HealthReport(
            status="healthy",
            checks={"a": HealthStatus.OK},
        )
        assert report.is_healthy

    def test_is_healthy_false_degraded(self):
        report = HealthReport(
            status="degraded",
            checks={"a": HealthStatus.OK, "b": "failed: x"},
        )
        assert not report.is_healthy

    def test_failed_checks_list(self):
        report = HealthReport(
            status="degraded",
            checks={"ok_check": HealthStatus.OK, "fail_check": "failed: timeout"},
        )
        assert report.failed_checks == ["fail_check"]

    def test_timestamp_is_utc(self):
        """HealthReport 默认时间戳有时区信息。"""
        report = HealthReport(
            status="healthy",
            checks={},
        )
        assert report.timestamp.tzinfo is not None


# ---------------------------------------------------------------------------
# logger_setup 测试
# ---------------------------------------------------------------------------

class TestLoggerSetup:
    def test_setup_logger_creates_log_dir(self, tmp_path):
        """setup_logger 会创建日志目录。"""
        log_dir = tmp_path / "test_logs"
        assert not log_dir.exists()

        setup_logger(log_dir=str(log_dir), level="DEBUG", serialize=False)
        assert log_dir.exists()

    def test_setup_logger_does_not_raise(self, tmp_path):
        """setup_logger 不抛出异常。"""
        setup_logger(log_dir=str(tmp_path / "logs"), level="INFO", serialize=False)

    def test_setup_logger_existing_dir(self, tmp_path):
        """setup_logger 对已存在目录不报错。"""
        log_dir = tmp_path / "existing_logs"
        log_dir.mkdir()
        setup_logger(log_dir=str(log_dir), level="WARNING", serialize=False)
