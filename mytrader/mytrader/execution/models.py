"""Execution Engine 数据模型：OrderResult + OrderStatus。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from mytrader.strategy.base import SignalDirection


class OrderStatus(Enum):
    """订单状态。"""

    PENDING = "PENDING"
    FILLED = "FILLED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


@dataclass
class OrderResult:
    """执行引擎产出的订单结果，供 PortfolioTracker 消费。

    Attributes:
        client_order_id:  来自 OrderIntent 的幂等 ID
        symbol:           股票代码
        direction:        BUY / SELL
        quantity:         成交数量
        fill_price:       成交价格
        commission:       手续费
        status:           订单状态
        filled_at:        成交时间（UTC）
        stop_loss_price:  止损价（传递给 Portfolio 监控）
        take_profit_price: 止盈价（传递给 Portfolio 监控）
        meta:             附加信息（来源 OrderIntent meta 等）
    """

    client_order_id: str
    symbol: str
    direction: SignalDirection
    quantity: int
    fill_price: float
    commission: float
    status: OrderStatus
    filled_at: datetime
    stop_loss_price: float = 0.0
    take_profit_price: float | None = None
    rejection_reason: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def gross_value(self) -> float:
        """成交总金额（不含手续费）。"""
        return self.quantity * self.fill_price

    @property
    def net_value(self) -> float:
        """成交净金额（含手续费）。"""
        if self.direction == SignalDirection.BUY:
            return self.gross_value + self.commission
        return self.gross_value - self.commission
