"""滑点模型 — 固定比例滑点 + 手续费计算。"""

from __future__ import annotations

from dataclasses import dataclass

from mytrader.strategy.base import SignalDirection


@dataclass
class SlippageModel:
    """固定比例滑点 + 手续费。

    Args:
        slippage_pct:   滑点比例（如 0.001 = 0.1%）
        commission_pct: 手续费比例（如 0.001 = 0.1%）
    """

    slippage_pct: float = 0.001
    commission_pct: float = 0.001

    def adjust_price(self, raw_price: float, direction: SignalDirection) -> float:
        """调整成交价（BUY 时加滑点，SELL 时减滑点）。"""
        if direction == SignalDirection.BUY:
            return raw_price * (1 + self.slippage_pct)
        return raw_price * (1 - self.slippage_pct)

    def calc_commission(self, quantity: int, fill_price: float) -> float:
        """计算手续费。"""
        return quantity * fill_price * self.commission_pct
