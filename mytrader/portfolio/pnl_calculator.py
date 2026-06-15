"""FIFO 成本法盈亏计算。

买入按先入先出（FIFO）消费成本队列，计算已实现盈亏和平均成本更新。
"""

from __future__ import annotations

from mytrader.portfolio.models import Position


def apply_buy(position: Position, quantity: int, fill_price: float) -> None:
    """处理买入，更新持仓成本（加权平均 + FIFO 队列）。

    Args:
        position:   当前持仓（原地修改）
        quantity:   买入股数
        fill_price: 成交价
    """
    total_cost = position.avg_cost * position.quantity + fill_price * quantity
    position.quantity += quantity
    position.avg_cost = total_cost / position.quantity if position.quantity > 0 else 0.0
    position.lots.append((quantity, fill_price))


def apply_sell(position: Position, quantity: int, fill_price: float) -> float:
    """处理卖出，按 FIFO 消费成本队列，返回已实现盈亏。

    Args:
        position:   当前持仓（原地修改）
        quantity:   卖出股数
        fill_price: 成交价

    Returns:
        本次卖出的已实现盈亏（正 = 盈利，负 = 亏损）
    """
    if quantity > position.quantity:
        raise ValueError(
            f"Sell quantity {quantity} > position quantity {position.quantity}"
        )

    realized = 0.0
    remaining = quantity

    while remaining > 0 and position.lots:
        lot_qty, lot_cost = position.lots[0]
        consume = min(remaining, lot_qty)

        realized += consume * (fill_price - lot_cost)
        remaining -= consume

        if consume == lot_qty:
            position.lots.pop(0)
        else:
            position.lots[0] = (lot_qty - consume, lot_cost)

    position.quantity -= quantity
    if position.quantity == 0:
        position.avg_cost = 0.0
        position.lots.clear()
    elif position.lots:
        # 重算加权平均成本
        total = sum(q * c for q, c in position.lots)
        total_qty = sum(q for q, _ in position.lots)
        position.avg_cost = total / total_qty if total_qty > 0 else 0.0

    return realized
