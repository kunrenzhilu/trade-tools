"""PortfolioTracker — 消费 OrderResult，更新持仓、计算盈亏、持久化。"""

from __future__ import annotations

from datetime import datetime

import pandas as pd
from loguru import logger

from mytrader.execution.models import OrderResult, OrderStatus
from mytrader.portfolio.metrics import portfolio_summary
from mytrader.portfolio.models import Portfolio, Position, TradeRecord
from mytrader.portfolio.persistence import PortfolioPersistence
from mytrader.portfolio.pnl_calculator import apply_buy, apply_sell
from mytrader.strategy.base import SignalDirection


class PortfolioTracker:
    """持仓追踪器。

    Args:
        initial_cash:  初始资金
        persistence:   持久化实例（None = 不持久化，仅内存）
    """

    def __init__(
        self,
        initial_cash: float = 100_000.0,
        persistence: PortfolioPersistence | None = None,
    ) -> None:
        self._portfolio = Portfolio(cash=initial_cash)
        self._persistence = persistence
        self._equity_history: list[tuple[datetime, float]] = []

    @property
    def portfolio(self) -> Portfolio:
        return self._portfolio

    @property
    def cash(self) -> float:
        return self._portfolio.cash

    @property
    def open_positions(self) -> dict[str, Position]:
        return self._portfolio.open_positions

    def process_order(self, order: OrderResult) -> TradeRecord | None:
        """处理一笔成交结果，更新持仓和现金。

        Args:
            order: 来自 PaperBroker（或真实经纪商）的成交结果

        Returns:
            TradeRecord（已更新盈亏）；REJECTED/CANCELLED 订单返回 None
        """
        if order.status not in (OrderStatus.FILLED,):
            logger.debug(
                f"[{order.symbol}] Order {order.client_order_id} status={order.status.value}, skip"
            )
            return None

        symbol = order.symbol

        # 确保持仓对象存在
        if symbol not in self._portfolio.positions:
            self._portfolio.positions[symbol] = Position(
                symbol=symbol,
                opened_at=order.filled_at,
            )

        position = self._portfolio.positions[symbol]
        realized_pnl = 0.0

        if order.direction == SignalDirection.BUY:
            # 扣减现金（含手续费）
            cost = order.gross_value + order.commission
            if cost > self._portfolio.cash:
                logger.warning(
                    f"[{symbol}] Insufficient cash: need={cost:.2f}, have={self._portfolio.cash:.2f}"
                )
                return None
            self._portfolio.cash -= cost
            apply_buy(position, order.quantity, order.fill_price)
            # 更新止损/止盈
            position.stop_loss_price = order.stop_loss_price
            position.take_profit_price = order.take_profit_price
            if position.opened_at is None:
                position.opened_at = order.filled_at

        elif order.direction == SignalDirection.SELL:
            if position.quantity < order.quantity:
                logger.warning(
                    f"[{symbol}] Sell quantity {order.quantity} > position {position.quantity}"
                )
                return None
            realized_pnl = apply_sell(position, order.quantity, order.fill_price)
            # 回收现金（含盈亏，扣手续费）
            self._portfolio.cash += order.gross_value - order.commission

        trade = TradeRecord(
            trade_id=order.client_order_id,
            symbol=symbol,
            direction=order.direction,
            quantity=order.quantity,
            fill_price=order.fill_price,
            commission=order.commission,
            filled_at=order.filled_at,
            realized_pnl=realized_pnl,
            stop_loss_price=order.stop_loss_price,
            take_profit_price=order.take_profit_price,
            meta=order.meta,
        )
        self._portfolio.trades.append(trade)

        logger.info(
            f"[{symbol}] {order.direction.value} {order.quantity}@{order.fill_price:.4f} "
            f"realized_pnl={realized_pnl:.2f} cash={self._portfolio.cash:.2f}"
        )

        # 持久化
        if self._persistence:
            self._persistence.save_trade(trade)

        return trade

    def snapshot(
        self,
        prices: dict[str, float] | None = None,
        now: datetime | None = None,
    ) -> dict:
        """保存并返回当前持仓快照。

        Args:
            prices: 各标的当前市价，用于计算市值
            now:    快照时间（UTC）
        """
        if now is None:
            now = datetime.utcnow()
        equity = self._portfolio.total_equity(prices)
        self._equity_history.append((now, equity))

        if self._persistence:
            self._persistence.save_snapshot(self._portfolio, equity, now)

        return {
            "snapshot_at": now.isoformat(),
            "cash": round(self._portfolio.cash, 2),
            "total_equity": round(equity, 2),
            "realized_pnl": round(self._portfolio.realized_pnl, 2),
            "open_positions": len(self._portfolio.open_positions),
        }

    def get_metrics(self) -> dict:
        """计算并返回组合绩效指标（需有足够的 equity_history）。"""
        if len(self._equity_history) < 2:
            return {"message": "Insufficient equity history for metrics"}

        equity_series = pd.Series(
            [v for _, v in self._equity_history],
            index=pd.DatetimeIndex([t for t, _ in self._equity_history]),
        )
        pnls = [t.realized_pnl for t in self._portfolio.trades if t.direction == SignalDirection.SELL]
        initial = self._equity_history[0][1]
        return portfolio_summary(equity_series, pnls, initial)
