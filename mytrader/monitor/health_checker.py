"""HealthChecker — 系统健康检查。

检查项：
1. data_feed:   数据源可用性（yfinance）
2. broker_api:  券商 API 连接（Alpaca/IBKR/Paper）
3. database:    SQLite 数据库可读写
4. scheduler:   APScheduler 调度器运行状态

设计原则：
- 每项检查独立 try-except，单项失败不影响其他项
- HealthReport.status = "healthy" | "degraded" | "unhealthy"
- 可作为 EventBus 的 HEALTH_CHECK_FAILED 事件发布源
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------

class HealthStatus:
    OK = "ok"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass
class HealthReport:
    """健康检查报告。

    Attributes:
        status:    整体状态（healthy / degraded / unhealthy）
        checks:    各检查项结果 {name -> status_str}
        details:   各检查项详细信息 {name -> detail}
        timestamp: 检查时间（UTC）
    """

    status: str
    checks: dict[str, str]
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_healthy(self) -> bool:
        return self.status == "healthy"

    @property
    def failed_checks(self) -> list[str]:
        return [k for k, v in self.checks.items() if v != HealthStatus.OK]


# ---------------------------------------------------------------------------
# HealthChecker
# ---------------------------------------------------------------------------

class HealthChecker:
    """系统健康检查器。

    用法：
        checker = HealthChecker()
        checker.register("data_feed", lambda: check_yfinance())
        report = checker.run_all()
        if not report.is_healthy:
            bus.publish(Events.HEALTH_CHECK_FAILED, report)

    也可使用内置的便捷注册方法：
        checker.register_database(engine)
        checker.register_scheduler(scheduler)
    """

    def __init__(self) -> None:
        self._checks: dict[str, Callable[[], tuple[str, Any]]] = {}

    # ------------------------------------------------------------------ #
    # 注册方法
    # ------------------------------------------------------------------ #

    def register(
        self,
        name: str,
        check_fn: Callable[[], tuple[str, Any]],
    ) -> None:
        """注册自定义检查项。

        check_fn 应返回 (status_str, detail)，status_str 为 "ok" 或失败描述。
        """
        self._checks[name] = check_fn

    def register_database(self, engine: Any) -> None:
        """注册 SQLAlchemy 数据库健康检查。"""
        def _check() -> tuple[str, Any]:
            try:
                with engine.connect() as conn:
                    conn.execute(__import__("sqlalchemy").text("SELECT 1"))
                return HealthStatus.OK, "database reachable"
            except Exception as exc:
                return f"failed: {exc}", str(exc)

        self.register("database", _check)

    def register_scheduler(self, scheduler: Any) -> None:
        """注册 APScheduler 健康检查。"""
        def _check() -> tuple[str, Any]:
            try:
                if scheduler.running:
                    jobs = scheduler.get_jobs()
                    return HealthStatus.OK, f"{len(jobs)} jobs registered"
                return "failed: scheduler not running", "not running"
            except Exception as exc:
                return f"failed: {exc}", str(exc)

        self.register("scheduler", _check)

    def register_data_feed(self, symbols: list[str] | None = None) -> None:
        """注册 yfinance 数据源健康检查（尝试获取 AAPL 最新数据）。"""
        test_symbol = (symbols or ["AAPL"])[0]

        def _check() -> tuple[str, Any]:
            try:
                import yfinance as yf
                ticker = yf.Ticker(test_symbol)
                info = ticker.fast_info
                price = getattr(info, "last_price", None)
                if price and price > 0:
                    return HealthStatus.OK, f"{test_symbol} last_price={price:.2f}"
                return "failed: no price data", f"price={price}"
            except Exception as exc:
                return f"failed: {exc}", str(exc)

        self.register("data_feed", _check)

    # ------------------------------------------------------------------ #
    # 执行检查
    # ------------------------------------------------------------------ #

    def run_all(self) -> HealthReport:
        """执行所有注册的检查项，返回 HealthReport。"""
        results: dict[str, str] = {}
        details: dict[str, Any] = {}

        for name, check_fn in self._checks.items():
            try:
                status, detail = check_fn()
            except Exception as exc:
                status = f"failed: {exc}"
                detail = str(exc)
            results[name] = status
            details[name] = detail

        # 整体状态判断
        failed_count = sum(1 for v in results.values() if v != HealthStatus.OK)
        if failed_count == 0:
            overall = "healthy"
        elif failed_count < len(results):
            overall = "degraded"
        else:
            overall = "unhealthy"

        return HealthReport(status=overall, checks=results, details=details)

    def run_check(self, name: str) -> tuple[str, Any]:
        """执行单个检查项。"""
        if name not in self._checks:
            return HealthStatus.UNKNOWN, f"check '{name}' not registered"
        try:
            return self._checks[name]()
        except Exception as exc:
            return f"failed: {exc}", str(exc)
