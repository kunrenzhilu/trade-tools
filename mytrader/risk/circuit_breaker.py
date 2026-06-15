"""熔断器 — 三层熔断保护（日/周/月亏损阈值）。

状态存储在内存中（Phase 2），重启后从 portfolio 快照重算。
熔断触发后，RiskManager 拒绝新的 OrderIntent。
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from loguru import logger

from mytrader.risk.models import CircuitBreakerState


class CircuitBreaker:
    """三层熔断器。

    Args:
        daily_loss_limit:   单日最大亏损比例（如 0.02 = 2%）
        weekly_loss_limit:  单周最大亏损比例（如 0.05 = 5%）
        monthly_loss_limit: 单月最大亏损比例（如 0.10 = 10%）
    """

    def __init__(
        self,
        daily_loss_limit: float = 0.02,
        weekly_loss_limit: float = 0.05,
        monthly_loss_limit: float = 0.10,
    ) -> None:
        self.daily_loss_limit = daily_loss_limit
        self.weekly_loss_limit = weekly_loss_limit
        self.monthly_loss_limit = monthly_loss_limit

        # 各周期起始资产快照
        self._daily_start: float | None = None
        self._weekly_start: float | None = None
        self._monthly_start: float | None = None

        # 各周期起始日期
        self._daily_date: date | None = None
        self._weekly_start_date: date | None = None
        self._monthly_month: tuple[int, int] | None = None  # (year, month)

        self._state: CircuitBreakerState = CircuitBreakerState.NORMAL

    @property
    def state(self) -> CircuitBreakerState:
        return self._state

    @property
    def is_triggered(self) -> bool:
        return self._state != CircuitBreakerState.NORMAL

    def update(self, current_equity: float, now: datetime | None = None) -> CircuitBreakerState:
        """根据当前资产更新熔断状态。

        Args:
            current_equity: 当前总资产（现金 + 持仓市值）
            now:            当前时间（None 时使用 datetime.utcnow()）

        Returns:
            当前熔断状态
        """
        if now is None:
            now = datetime.utcnow()
        today = now.date()

        # --- 初始化各周期起始值 ---
        if self._daily_start is None or self._daily_date != today:
            self._daily_start = current_equity
            self._daily_date = today

        week_start = today - timedelta(days=today.weekday())
        if self._weekly_start is None or self._weekly_start_date != week_start:
            self._weekly_start = current_equity
            self._weekly_start_date = week_start

        ym = (today.year, today.month)
        if self._monthly_start is None or self._monthly_month != ym:
            self._monthly_start = current_equity
            self._monthly_month = ym

        # --- 计算各周期亏损率 ---
        if self._daily_start and self._daily_start > 0:
            daily_loss = (self._daily_start - current_equity) / self._daily_start
            if daily_loss >= self.daily_loss_limit:
                if self._state == CircuitBreakerState.NORMAL:
                    logger.warning(
                        f"Circuit breaker DAILY triggered: loss={daily_loss:.2%} >= limit={self.daily_loss_limit:.2%}"
                    )
                self._state = CircuitBreakerState.DAILY_TRIGGERED
                return self._state

        if self._weekly_start and self._weekly_start > 0:
            weekly_loss = (self._weekly_start - current_equity) / self._weekly_start
            if weekly_loss >= self.weekly_loss_limit:
                if self._state == CircuitBreakerState.NORMAL:
                    logger.warning(
                        f"Circuit breaker WEEKLY triggered: loss={weekly_loss:.2%} >= limit={self.weekly_loss_limit:.2%}"
                    )
                self._state = CircuitBreakerState.WEEKLY_TRIGGERED
                return self._state

        if self._monthly_start and self._monthly_start > 0:
            monthly_loss = (self._monthly_start - current_equity) / self._monthly_start
            if monthly_loss >= self.monthly_loss_limit:
                if self._state == CircuitBreakerState.NORMAL:
                    logger.warning(
                        f"Circuit breaker MONTHLY triggered: loss={monthly_loss:.2%} >= limit={self.monthly_loss_limit:.2%}"
                    )
                self._state = CircuitBreakerState.MONTHLY_TRIGGERED
                return self._state

        self._state = CircuitBreakerState.NORMAL
        return self._state

    def reset(self, state: CircuitBreakerState = CircuitBreakerState.NORMAL) -> None:
        """手动重置熔断状态（人工干预后调用）。"""
        self._state = state
        self._daily_start = None
        self._weekly_start = None
        self._monthly_start = None
        logger.info(f"Circuit breaker manually reset to {state}")
