"""Portfolio 数据模型：Position + Portfolio + TradeRecord。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from mytrader.strategy.base import SignalDirection


@dataclass
class TradeRecord:
    """单笔成交记录（用于 FIFO 盈亏计算和持久化）。

    Attributes:
        trade_id:         唯一记录 ID（来自 OrderResult.client_order_id）
        symbol:           股票代码
        direction:        BUY / SELL
        quantity:         成交股数
        fill_price:       成交价
        commission:       手续费
        filled_at:        成交时间（UTC）
        realized_pnl:     本笔成交已实现盈亏（SELL 时由 FIFO 计算）
        stop_loss_price:  止损价（记录用）
        take_profit_price: 止盈价（记录用）
        meta:             附加信息
    """

    trade_id: str
    symbol: str
    direction: SignalDirection
    quantity: int
    fill_price: float
    commission: float
    filled_at: datetime
    realized_pnl: float = 0.0
    stop_loss_price: float = 0.0
    take_profit_price: float | None = None
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class Position:
    """单标的当前持仓。

    Attributes:
        symbol:         股票代码
        quantity:       持有股数（0 = 无持仓）
        avg_cost:       平均成本（FIFO 加权）
        stop_loss_price: 止损价
        take_profit_price: 止盈价
        opened_at:      建仓时间
        lots:           FIFO 成本队列（每次买入的 (quantity, price) 对）
    """

    symbol: str
    quantity: int = 0
    avg_cost: float = 0.0
    stop_loss_price: float = 0.0
    take_profit_price: float | None = None
    opened_at: datetime | None = None
    lots: list[tuple[int, float]] = field(default_factory=list)  # [(qty, cost_price), ...]

    @property
    def is_open(self) -> bool:
        return self.quantity > 0

    @property
    def market_value(self, current_price: float | None = None) -> float:
        """持仓市值（需外部提供当前价）。用 current_price 参数计算。"""
        # 通常由 Portfolio.market_value() 方法调用，此处仅返回成本价值
        return self.quantity * self.avg_cost

    def unrealized_pnl(self, current_price: float) -> float:
        """未实现盈亏。"""
        return (current_price - self.avg_cost) * self.quantity


@dataclass
class Portfolio:
    """整体持仓组合快照。

    Attributes:
        cash:       可用现金
        positions:  当前所有标的持仓，key 为 symbol
        trades:     历史成交记录（所有标的）
        created_at: 创建时间
    """

    cash: float = 100_000.0
    positions: dict[str, Position] = field(default_factory=dict)
    trades: list[TradeRecord] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def open_positions(self) -> dict[str, Position]:
        """当前未平仓持仓。"""
        return {s: p for s, p in self.positions.items() if p.is_open}

    @property
    def total_cost(self) -> float:
        """所有持仓的总成本（无当前市价时用成本估算市值）。"""
        return sum(p.quantity * p.avg_cost for p in self.positions.values() if p.is_open)

    def total_equity(self, prices: dict[str, float] | None = None) -> float:
        """总资产 = 现金 + 持仓市值。

        Args:
            prices: 各标的当前价格 {symbol: price}，None 时用成本价代替
        """
        if prices is None:
            return self.cash + self.total_cost
        market_val = sum(
            p.quantity * prices.get(s, p.avg_cost)
            for s, p in self.positions.items()
            if p.is_open
        )
        return self.cash + market_val

    @property
    def realized_pnl(self) -> float:
        """所有历史成交的已实现盈亏总和。"""
        return sum(t.realized_pnl for t in self.trades)

    @property
    def total_commission(self) -> float:
        """历史总手续费。"""
        return sum(t.commission for t in self.trades)
