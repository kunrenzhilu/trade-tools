"""RiskManager — 风险管理器门面。

整合：仓位计算 + 止损设置 + 熔断检查 + 仓位约束，
消费 FilteredSignal，输出 OrderIntent 或 None（被风控拦截）。
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import pandas as pd
from loguru import logger

from mytrader.risk.circuit_breaker import CircuitBreaker
from mytrader.risk.constraints import (
    check_max_positions,
    check_min_order_value,
    check_single_position_limit,
    check_total_exposure,
)
from mytrader.risk.models import CircuitBreakerState, OrderIntent
from mytrader.risk.position_sizer import atr_position_size, fixed_amount_size
from mytrader.risk.stop_loss import atr_stop, fixed_stop, fixed_take_profit
from mytrader.strategy.base import SignalDirection

if TYPE_CHECKING:
    from mytrader.infra.config import RiskConfig
    from mytrader.signal.models import FilteredSignal


class RiskManager:
    """风险管理器。

    Args:
        config:           RiskConfig（来自 AppConfig.risk）
        total_capital:    当前总资产（现金 + 持仓市值）
        current_exposure: 当前已有持仓市值
        current_positions_count: 当前持仓标的数
    """

    def __init__(
        self,
        config: "RiskConfig",
        total_capital: float = 100_000.0,
        current_exposure: float = 0.0,
        current_positions_count: int = 0,
    ) -> None:
        self._cfg = config
        self.total_capital = total_capital
        self.current_exposure = current_exposure
        self.current_positions_count = current_positions_count

        self._circuit_breaker = CircuitBreaker(
            daily_loss_limit=config.circuit_breaker.daily_loss_limit,
            weekly_loss_limit=config.circuit_breaker.weekly_loss_limit,
            monthly_loss_limit=config.circuit_breaker.monthly_loss_limit,
        )

    @property
    def circuit_breaker(self) -> CircuitBreaker:
        return self._circuit_breaker

    def update_portfolio_state(
        self,
        total_capital: float,
        current_exposure: float,
        current_positions_count: int,
    ) -> None:
        """在每个交易周期开始时同步持仓状态。"""
        self.total_capital = total_capital
        self.current_exposure = current_exposure
        self.current_positions_count = current_positions_count
        self._circuit_breaker.update(total_capital)

    def evaluate(
        self,
        filtered_signal: "FilteredSignal",
        df: pd.DataFrame,
        now: datetime | None = None,
    ) -> OrderIntent | None:
        """评估信号，输出 OrderIntent 或 None。

        Args:
            filtered_signal: 经过信号过滤器的信号
            df:              行情 DataFrame（含 OHLCV，index 为 DatetimeIndex）
            now:             当前时间（UTC），None 时取信号时间戳

        Returns:
            OrderIntent（风控通过）或 None（风控拒绝）
        """
        signal = filtered_signal.source_signal
        if now is None:
            now = signal.timestamp

        # 1. 熔断检查
        if self._circuit_breaker.is_triggered:
            logger.warning(
                f"[{signal.symbol}] Rejected by circuit breaker: {self._circuit_breaker.state}"
            )
            return None

        # 2. 只处理 BUY/SELL
        if signal.direction == SignalDirection.HOLD:
            return None

        is_long = signal.direction == SignalDirection.BUY

        # 3. 确定入场价（优先使用 price_hint，否则取 df 最新 close）
        entry_price = signal.price_hint
        if entry_price is None or entry_price <= 0:
            idx = df.index[df.index <= signal.timestamp]
            if idx.empty:
                logger.warning(f"[{signal.symbol}] No price data for signal timestamp {signal.timestamp}")
                return None
            entry_price = float(df.loc[idx[-1], "close"])

        # 4. 仓位计算（ATR 法优先）
        try:
            quantity, risk_amount, stop_loss_price = atr_position_size(
                capital=self.total_capital,
                risk_per_trade=self._cfg.risk_per_trade,
                entry_price=entry_price,
                df=df,
                atr_multiplier=2.0,
            )
        except Exception as e:
            logger.warning(f"[{signal.symbol}] ATR position sizing failed: {e}, fallback to fixed_amount")
            stop_loss_price = fixed_stop(entry_price, stop_pct=0.02, is_long=is_long)
            quantity, risk_amount = fixed_amount_size(
                capital=self.total_capital,
                risk_per_trade=self._cfg.risk_per_trade,
                entry_price=entry_price,
                stop_loss_price=stop_loss_price,
            )

        if quantity <= 0:
            logger.warning(f"[{signal.symbol}] Calculated quantity=0, skipping")
            return None

        # 5. 止盈（2:1 风险收益比）
        stop_distance = abs(entry_price - stop_loss_price)
        take_profit = fixed_take_profit(entry_price, tp_pct=(stop_distance / entry_price) * 2, is_long=is_long)

        position_value = quantity * entry_price

        # 6. 约束检查
        checks = [
            check_min_order_value(quantity, entry_price, self._cfg.min_order_value),
            check_single_position_limit(position_value, self.total_capital, self._cfg.max_single_position_pct),
            check_total_exposure(self.current_exposure, position_value, self.total_capital, self._cfg.max_total_exposure_pct),
            check_max_positions(self.current_positions_count, self._cfg.max_concurrent_positions),
        ]
        for chk in checks:
            if not chk.passed:
                logger.info(f"[{signal.symbol}] Constraint rejected: {chk.reason}")
                return None

        return OrderIntent(
            symbol=signal.symbol,
            direction=signal.direction,
            quantity=quantity,
            entry_price=entry_price,
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit,
            risk_amount=risk_amount,
            position_value=position_value,
            timestamp=now,
            strategy_name=signal.strategy_name,
            meta={
                "atr_multiplier": 2.0,
                "confidence": signal.confidence,
            },
        )
