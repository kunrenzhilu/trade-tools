"""PaperBroker — 纸面交易经纪商，模拟下一 bar 开盘价成交。

设计原则：
- 成交价 = 下一 bar 开盘价 * (1 + slippage)（BUY）
- 幂等性：相同 client_order_id 不重复成交
- 不自动提交真实券商，只生成 OrderResult 供 PortfolioTracker 消费
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd
from loguru import logger

from mytrader.execution.models import OrderResult, OrderStatus
from mytrader.execution.slippage import SlippageModel
from mytrader.risk.models import OrderIntent
from mytrader.strategy.base import SignalDirection


class PaperBroker:
    """纸面交易经纪商。

    Args:
        slippage_pct:   滑点比例（默认 0.001）
        commission_pct: 手续费比例（默认 0.001）
    """

    def __init__(
        self,
        slippage_pct: float = 0.001,
        commission_pct: float = 0.001,
    ) -> None:
        self._slippage = SlippageModel(
            slippage_pct=slippage_pct,
            commission_pct=commission_pct,
        )
        self._submitted: dict[str, OrderResult] = {}  # client_order_id -> result

    def submit(
        self,
        intent: OrderIntent,
        df: pd.DataFrame,
    ) -> OrderResult:
        """提交订单意图，按下一 bar 开盘价模拟成交。

        Args:
            intent: OrderIntent（来自 RiskManager）
            df:     行情 DataFrame（index 为 DatetimeIndex，需含 open 列）

        Returns:
            OrderResult
        """
        # 幂等性检查
        if intent.client_order_id in self._submitted:
            logger.warning(
                f"[{intent.symbol}] Duplicate order_id={intent.client_order_id}, skipping"
            )
            return self._submitted[intent.client_order_id]

        # 找下一 bar 开盘价
        next_open = self._get_next_bar_open(intent, df)
        if next_open is None:
            result = OrderResult(
                client_order_id=intent.client_order_id,
                symbol=intent.symbol,
                direction=intent.direction,
                quantity=intent.quantity,
                fill_price=0.0,
                commission=0.0,
                status=OrderStatus.REJECTED,
                filled_at=intent.timestamp,
                stop_loss_price=intent.stop_loss_price,
                take_profit_price=intent.take_profit_price,
                rejection_reason="No next bar open price available",
                meta=intent.meta,
            )
            self._submitted[intent.client_order_id] = result
            logger.warning(f"[{intent.symbol}] Order rejected: no next bar data")
            return result

        # 应用滑点
        fill_price = self._slippage.adjust_price(next_open, intent.direction)
        commission = self._slippage.calc_commission(intent.quantity, fill_price)

        result = OrderResult(
            client_order_id=intent.client_order_id,
            symbol=intent.symbol,
            direction=intent.direction,
            quantity=intent.quantity,
            fill_price=fill_price,
            commission=commission,
            status=OrderStatus.FILLED,
            filled_at=intent.timestamp,
            stop_loss_price=intent.stop_loss_price,
            take_profit_price=intent.take_profit_price,
            meta={
                **intent.meta,
                "raw_next_open": next_open,
                "slippage_pct": self._slippage.slippage_pct,
            },
        )
        self._submitted[intent.client_order_id] = result

        logger.info(
            f"[{intent.symbol}] Paper order filled: {intent.direction.value} "
            f"{intent.quantity} @ {fill_price:.4f} (raw_open={next_open:.4f}), "
            f"commission={commission:.2f}"
        )
        return result

    def cancel(self, client_order_id: str) -> bool:
        """取消订单（Paper 模式立即成功）。"""
        if client_order_id in self._submitted:
            result = self._submitted[client_order_id]
            if result.status == OrderStatus.PENDING:
                self._submitted[client_order_id] = OrderResult(
                    **{**result.__dict__, "status": OrderStatus.CANCELLED}
                )
                return True
        return True  # Paper 模式总是返回成功

    def get_order(self, client_order_id: str) -> OrderResult | None:
        """查询订单结果。"""
        return self._submitted.get(client_order_id)

    @property
    def order_history(self) -> list[OrderResult]:
        """所有历史订单。"""
        return list(self._submitted.values())

    def _get_next_bar_open(
        self,
        intent: OrderIntent,
        df: pd.DataFrame,
    ) -> float | None:
        """获取信号时间戳之后第一个 bar 的开盘价。"""
        if "open" not in df.columns:
            # 如果没有 open 列，用 close 代替
            col = "close" if "close" in df.columns else None
            if col is None:
                return None
        else:
            col = "open"

        future_idx = df.index[df.index > intent.timestamp]
        if future_idx.empty:
            return None

        return float(df.loc[future_idx[0], col])
