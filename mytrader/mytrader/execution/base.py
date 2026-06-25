"""BrokerProtocol — 经纪商接口 Protocol 定义。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    import pandas as pd
    from mytrader.execution.models import OrderResult
    from mytrader.risk.models import OrderIntent


class BrokerProtocol(Protocol):
    """所有经纪商实现必须满足的接口。"""

    def submit(
        self,
        intent: "OrderIntent",
        df: "pd.DataFrame",
    ) -> "OrderResult":
        """提交订单意图，返回订单结果。

        Args:
            intent: 风险管理器生成的订单意图
            df:     行情 DataFrame（下一 bar 开盘价用于成交）

        Returns:
            OrderResult
        """
        ...

    def cancel(self, client_order_id: str) -> bool:
        """取消未成交订单（Paper Broker 中立即返回 True）。"""
        ...
