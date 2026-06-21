"""测试 Phase 3 TradingScheduler — APScheduler 定时任务调度器。"""

from __future__ import annotations

from unittest.mock import MagicMock, call, patch

import pytest

from mytrader.infra.scheduler import TradingScheduler
from mytrader.infra.config import SchedulerConfig


# ---------------------------------------------------------------------------
# 测试夹具
# ---------------------------------------------------------------------------

def make_scheduler_config(**kwargs) -> SchedulerConfig:
    defaults = {
        "enabled": True,
        "timezone": "America/New_York",
        "morning_scan_hour": 9,
        "morning_scan_minute": 35,
        "intraday_interval_minutes": 30,
        "eod_check_hour": 15,
        "eod_check_minute": 45,
        "reconciliation_hour": 16,
        "reconciliation_minute": 30,
        "misfire_grace_time": 60,
    }
    defaults.update(kwargs)
    return SchedulerConfig(**defaults)


def make_mock_apscheduler() -> MagicMock:
    """创建 Mock APScheduler BlockingScheduler。"""
    mock_sched = MagicMock()
    mock_sched.running = True
    mock_sched.get_jobs.return_value = [
        MagicMock(id="morning_scan"),
        MagicMock(id="intraday_scan"),
        MagicMock(id="eod_check"),
        MagicMock(id="reconciliation"),
    ]
    return mock_sched


# ---------------------------------------------------------------------------
# setup_jobs 测试
# ---------------------------------------------------------------------------

class TestTradingSchedulerJobs:
    def test_setup_jobs_registers_four_jobs(self):
        """setup_jobs 注册 4 个定时任务。"""
        mock_sched = make_mock_apscheduler()
        cfg = make_scheduler_config()
        scheduler = TradingScheduler(config=cfg, scheduler=mock_sched)
        scheduler.setup_jobs()

        assert mock_sched.add_job.call_count == 4

    def test_setup_jobs_idempotent(self):
        """重复调用 setup_jobs 不重复注册。"""
        mock_sched = make_mock_apscheduler()
        cfg = make_scheduler_config()
        scheduler = TradingScheduler(config=cfg, scheduler=mock_sched)
        scheduler.setup_jobs()
        scheduler.setup_jobs()
        # 只调用一次 add_job（第二次因 _jobs_registered=True 被跳过）
        assert mock_sched.add_job.call_count == 4

    def test_job_ids_registered(self):
        """检查 job ID 正确。"""
        mock_sched = make_mock_apscheduler()
        cfg = make_scheduler_config()
        scheduler = TradingScheduler(config=cfg, scheduler=mock_sched)
        scheduler.setup_jobs()

        registered_ids = {c.kwargs.get("id") or c[1].get("id", "") for c in mock_sched.add_job.call_args_list}
        assert "morning_scan" in registered_ids
        assert "intraday_scan" in registered_ids
        assert "eod_check" in registered_ids
        assert "reconciliation" in registered_ids

    def test_get_jobs_returns_list(self):
        """get_jobs 返回 job 列表。"""
        mock_sched = make_mock_apscheduler()
        cfg = make_scheduler_config()
        scheduler = TradingScheduler(config=cfg, scheduler=mock_sched)
        jobs = scheduler.get_jobs()
        assert len(jobs) == 4


# ---------------------------------------------------------------------------
# running 属性测试
# ---------------------------------------------------------------------------

class TestTradingSchedulerRunning:
    def test_running_true_when_scheduler_running(self):
        """调度器运行时 running=True。"""
        mock_sched = make_mock_apscheduler()
        mock_sched.running = True
        cfg = make_scheduler_config()
        scheduler = TradingScheduler(config=cfg, scheduler=mock_sched)
        assert scheduler.running is True

    def test_running_false_before_start(self):
        """调度器未启动时 running=False。"""
        cfg = make_scheduler_config()
        scheduler = TradingScheduler(config=cfg)
        # _scheduler is None
        assert scheduler.running is False


# ---------------------------------------------------------------------------
# 熔断检查测试
# ---------------------------------------------------------------------------

class TestTradingSchedulerCircuitBreaker:
    def test_morning_scan_skipped_when_circuit_triggered(self):
        """熔断触发时盘前扫描被跳过。"""
        from mytrader.risk.models import CircuitBreakerState

        mock_cb = MagicMock()
        mock_cb.state = CircuitBreakerState.DAILY_TRIGGERED

        mock_fn = MagicMock()
        cfg = make_scheduler_config()
        scheduler = TradingScheduler(
            config=cfg,
            on_morning_scan=mock_fn,
            circuit_breaker=mock_cb,
        )
        scheduler._safe_morning_scan()
        mock_fn.assert_not_called()

    def test_morning_scan_runs_when_normal(self):
        """熔断正常时盘前扫描正常执行。"""
        from mytrader.risk.models import CircuitBreakerState

        mock_cb = MagicMock()
        mock_cb.state = CircuitBreakerState.NORMAL

        mock_fn = MagicMock()
        cfg = make_scheduler_config()
        scheduler = TradingScheduler(
            config=cfg,
            on_morning_scan=mock_fn,
            circuit_breaker=mock_cb,
        )
        scheduler._safe_morning_scan()
        mock_fn.assert_called_once()

    def test_intraday_scan_skipped_when_circuit_triggered(self):
        """熔断时盘中扫描也被跳过。"""
        from mytrader.risk.models import CircuitBreakerState

        mock_cb = MagicMock()
        mock_cb.state = CircuitBreakerState.WEEKLY_TRIGGERED

        mock_fn = MagicMock()
        cfg = make_scheduler_config()
        scheduler = TradingScheduler(
            config=cfg,
            on_intraday_scan=mock_fn,
            circuit_breaker=mock_cb,
        )
        scheduler._safe_intraday_scan()
        mock_fn.assert_not_called()

    def test_eod_check_runs_regardless_of_circuit(self):
        """收盘前检查不受熔断影响（平仓需要执行）。"""
        from mytrader.risk.models import CircuitBreakerState

        mock_cb = MagicMock()
        mock_cb.state = CircuitBreakerState.DAILY_TRIGGERED

        mock_fn = MagicMock()
        cfg = make_scheduler_config()
        scheduler = TradingScheduler(
            config=cfg,
            on_eod_check=mock_fn,
            circuit_breaker=mock_cb,
        )
        scheduler._safe_eod_check()
        mock_fn.assert_called_once()


# ---------------------------------------------------------------------------
# 异常隔离测试
# ---------------------------------------------------------------------------

class TestTradingSchedulerErrorIsolation:
    def test_morning_scan_exception_does_not_propagate(self):
        """盘前扫描回调异常不向上传播。"""
        def bad_fn():
            raise RuntimeError("策略引擎崩溃")

        cfg = make_scheduler_config()
        scheduler = TradingScheduler(config=cfg, on_morning_scan=bad_fn)
        # 不应抛出异常
        scheduler._safe_morning_scan()

    def test_intraday_scan_exception_does_not_propagate(self):
        """盘中扫描回调异常不向上传播。"""
        def bad_fn():
            raise ValueError("数据异常")

        cfg = make_scheduler_config()
        scheduler = TradingScheduler(config=cfg, on_intraday_scan=bad_fn)
        scheduler._safe_intraday_scan()

    def test_eod_check_exception_does_not_propagate(self):
        cfg = make_scheduler_config()
        scheduler = TradingScheduler(config=cfg, on_eod_check=lambda: (_ for _ in ()).throw(Exception("EOD崩溃")))
        scheduler._safe_eod_check()

    def test_reconciliation_exception_does_not_propagate(self):
        """对账回调异常不向上传播。"""
        def bad_fn():
            raise ConnectionError("DB not available")

        cfg = make_scheduler_config()
        scheduler = TradingScheduler(config=cfg, on_reconciliation=bad_fn)
        scheduler._safe_reconciliation()


# ---------------------------------------------------------------------------
# disabled 配置测试
# ---------------------------------------------------------------------------

class TestTradingSchedulerDisabled:
    def test_disabled_scheduler_does_not_start(self):
        """enabled=False 时 start() 不启动调度器。"""
        mock_sched = make_mock_apscheduler()
        cfg = make_scheduler_config(enabled=False)
        scheduler = TradingScheduler(config=cfg, scheduler=mock_sched)
        scheduler.start()
        mock_sched.start.assert_not_called()
