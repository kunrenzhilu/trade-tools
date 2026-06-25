"""Risk Manager 数据模型：OrderIntent + CircuitBreakerState。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from mytrader.strategy.base import SignalDirection


class CircuitBreakerState(Enum):
    """熔断状态。"""

    NORMAL = "NORMAL"
    DAILY_TRIGGERED = "DAILY_TRIGGERED"
    WEEKLY_TRIGGERED = "WEEKLY_TRIGGERED"
    MONTHLY_TRIGGERED = "MONTHLY_TRIGGERED"


@dataclass
class OrderIntent:
    """风险管理器产出的订单意图，提交给执行引擎。

    Attributes:
        symbol:          股票代码
        direction:       BUY / SELL
        quantity:        建议数量（股数）
        entry_price:     建议入场价（None = 市价）
        stop_loss_price: 止损价格
        take_profit_price: 止盈价格（可选）
        risk_amount:     本次交易承担的风险金额（仓位计算依据）
        position_value:  订单总价值（quantity * entry_price）
        timestamp:       创建时间（UTC）
        strategy_name:   来源策略名称
        client_order_id: 客户端幂等 ID
        meta:            附加元信息（ATR 值、仓位法名称等）
    """

    symbol: str
    direction: SignalDirection
    quantity: int
    entry_price: float
    stop_loss_price: float
    take_profit_price: float | None
    risk_amount: float
    position_value: float
    timestamp: datetime
    strategy_name: str
    client_order_id: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.client_order_id:
            import uuid
            self.client_order_id = uuid.uuid4().hex[:16]
