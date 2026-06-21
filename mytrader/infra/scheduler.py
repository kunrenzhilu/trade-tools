"""TradingScheduler — APScheduler 定时任务调度器。

定时任务（美东时间 ET）：
1. 盘前扫描（09:35）：拉取行情 + 生成信号
2. 盘中扫描（10:00-15:30，每 30 分钟）：更新信号
3. 收盘前检查（15:45）：决定是否平仓
4. 盘后对账（16:30）：本地 vs 券商持仓核对

设计原则：
- 每个 job 独立 try-except，异常不崩溃调度器
- 熔断前置检查：熔断期间跳过所有信号生成任务
- misfire_grace_time 防止短暂延迟导致任务跳过
- BlockingScheduler 适合单进程部署
"""

from __future__ import annotations

from typing import Callable, Any

from loguru import logger


class TradingScheduler:
    """APScheduler 定时任务调度器封装。

    Args:
        config:           SchedulerConfig
        on_morning_scan:  盘前扫描回调
        on_intraday_scan: 盘中扫描回调
        on_eod_check:     收盘前检查回调
        on_reconciliation: 盘后对账回调
        circuit_breaker:  熔断器（可选，有 is_triggered() 方法）
        scheduler:        可注入的 APScheduler 实例（测试用）
    """

    def __init__(
        self,
        config: Any,  # SchedulerConfig
        on_morning_scan: Callable[[], None] | None = None,
        on_intraday_scan: Callable[[], None] | None = None,
        on_eod_check: Callable[[], None] | None = None,
        on_reconciliation: Callable[[], None] | None = None,
        circuit_breaker: Any | None = None,
        scheduler: Any | None = None,
    ) -> None:
        self._config = config
        self._on_morning_scan = on_morning_scan or (lambda: None)
        self._on_intraday_scan = on_intraday_scan or (lambda: None)
        self._on_eod_check = on_eod_check or (lambda: None)
        self._on_reconciliation = on_reconciliation or (lambda: None)
        self._circuit_breaker = circuit_breaker
        self._scheduler = scheduler
        self._jobs_registered = False

    def _get_scheduler(self) -> Any:
        """获取或初始化 APScheduler BlockingScheduler。"""
        if self._scheduler is None:
            try:
                from apscheduler.schedulers.blocking import BlockingScheduler
            except ImportError as exc:
                raise ImportError(
                    "APScheduler not installed. Run: pip install apscheduler"
                ) from exc
            self._scheduler = BlockingScheduler(timezone=self._config.timezone)
        return self._scheduler

    @property
    def running(self) -> bool:
        """调度器是否正在运行。"""
        if self._scheduler is None:
            return False
        return bool(getattr(self._scheduler, "running", False))

    def get_jobs(self) -> list:
        """获取已注册的 job 列表（用于健康检查）。"""
        sched = self._get_scheduler()
        return list(sched.get_jobs())

    def setup_jobs(self) -> None:
        """注册所有定时任务（不启动调度器）。"""
        if self._jobs_registered:
            return

        try:
            from apscheduler.triggers.cron import CronTrigger
        except ImportError as exc:
            raise ImportError("APScheduler not installed") from exc

        sched = self._get_scheduler()
        tz = self._config.timezone
        grace = self._config.misfire_grace_time

        # 1. 盘前扫描
        sched.add_job(
            self._safe_morning_scan,
            CronTrigger(
                day_of_week="mon-fri",
                hour=self._config.morning_scan_hour,
                minute=self._config.morning_scan_minute,
                timezone=tz,
            ),
            id="morning_scan",
            name="Morning Scan (Signal Generation)",
            misfire_grace_time=grace,
            replace_existing=True,
        )

        # 2. 盘中扫描（10:00 至 15:00，每 N 分钟）
        intraday_minutes = self._config.intraday_interval_minutes
        sched.add_job(
            self._safe_intraday_scan,
            CronTrigger(
                day_of_week="mon-fri",
                hour="10-14",
                minute=f"*/{intraday_minutes}",
                timezone=tz,
            ),
            id="intraday_scan",
            name=f"Intraday Scan (every {intraday_minutes}min)",
            misfire_grace_time=grace,
            replace_existing=True,
        )

        # 3. 收盘前检查
        sched.add_job(
            self._safe_eod_check,
            CronTrigger(
                day_of_week="mon-fri",
                hour=self._config.eod_check_hour,
                minute=self._config.eod_check_minute,
                timezone=tz,
            ),
            id="eod_check",
            name="End-of-Day Check",
            misfire_grace_time=grace,
            replace_existing=True,
        )

        # 4. 盘后对账
        sched.add_job(
            self._safe_reconciliation,
            CronTrigger(
                day_of_week="mon-fri",
                hour=self._config.reconciliation_hour,
                minute=self._config.reconciliation_minute,
                timezone=tz,
            ),
            id="reconciliation",
            name="Post-Market Reconciliation",
            misfire_grace_time=grace,
            replace_existing=True,
        )

        self._jobs_registered = True
        logger.info(
            f"TradingScheduler: {len(sched.get_jobs())} jobs registered "
            f"(tz={tz}, grace={grace}s)"
        )

    def start(self) -> None:
        """注册任务并启动调度器（阻塞运行）。"""
        if not self._config.enabled:
            logger.info("TradingScheduler: disabled in config, skipping start")
            return

        self.setup_jobs()
        sched = self._get_scheduler()
        logger.info("TradingScheduler starting (blocking)...")
        sched.start()

    def shutdown(self, wait: bool = True) -> None:
        """停止调度器。"""
        if self._scheduler is not None and self.running:
            self._scheduler.shutdown(wait=wait)
            logger.info("TradingScheduler stopped")

    # ------------------------------------------------------------------ #
    # 受保护的任务包装器（异常隔离 + 熔断检查）
    # ------------------------------------------------------------------ #

    def _is_circuit_breaker_triggered(self) -> bool:
        if self._circuit_breaker is None:
            return False
        try:
            state = self._circuit_breaker.state
            from mytrader.risk.models import CircuitBreakerState
            return state != CircuitBreakerState.NORMAL
        except Exception:
            return False

    def _safe_morning_scan(self) -> None:
        try:
            if self._is_circuit_breaker_triggered():
                logger.warning("Morning scan SKIPPED: circuit breaker triggered")
                return
            logger.info("=== Morning Scan started ===")
            self._on_morning_scan()
            logger.info("=== Morning Scan completed ===")
        except Exception as exc:
            logger.exception(f"Morning scan error: {exc}")

    def _safe_intraday_scan(self) -> None:
        try:
            if self._is_circuit_breaker_triggered():
                logger.warning("Intraday scan SKIPPED: circuit breaker triggered")
                return
            logger.info("--- Intraday Scan started ---")
            self._on_intraday_scan()
            logger.info("--- Intraday Scan completed ---")
        except Exception as exc:
            logger.exception(f"Intraday scan error: {exc}")

    def _safe_eod_check(self) -> None:
        try:
            logger.info("=== EOD Check started ===")
            self._on_eod_check()
            logger.info("=== EOD Check completed ===")
        except Exception as exc:
            logger.exception(f"EOD check error: {exc}")

    def _safe_reconciliation(self) -> None:
        try:
            logger.info("=== Reconciliation started ===")
            self._on_reconciliation()
            logger.info("=== Reconciliation completed ===")
        except Exception as exc:
            logger.exception(f"Reconciliation error: {exc}")
