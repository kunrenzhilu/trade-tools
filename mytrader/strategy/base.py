"""Strategy layer base types: Signal 数据结构和 SignalDirection 枚举。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class SignalDirection(Enum):
    BUY  = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class Signal:
    """策略引擎产出的交易信号。

    Attributes:
        symbol:        股票代码
        direction:     BUY / SELL / HOLD
        timestamp:     信号产生时间（UTC）
        confidence:    置信度 0.0~1.0（策略对本次信号的把握程度）
        strategy_name: 产生信号的策略名称
        indicators:    当时的指标值快照，便于复盘
        price_hint:    建议入场价（可为 None，由执行层决定）
    """

    symbol: str
    direction: SignalDirection
    timestamp: datetime
    confidence: float
    strategy_name: str
    indicators: dict[str, Any] = field(default_factory=dict)
    price_hint: float | None = None

    def is_actionable(self) -> bool:
        """是否需要执行（非 HOLD）。"""
        return self.direction != SignalDirection.HOLD
