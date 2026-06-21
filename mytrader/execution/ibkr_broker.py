"""IBKRBroker — Interactive Brokers 港美股经纪商，实现 BrokerProtocol。

依赖：ib_insync（需本地运行 TWS 或 IB Gateway）

设计原则：
- 自动重连：连接断开时重试最多 3 次
- readonly 保护：初期 readonly=True，仅查询持仓，不下单
- 测试友好：依赖注入 IB 实例，测试时可注入 Mock
- 港美股统一处理，currency 通过 meta 区分

注意：
- IBKR 需本地运行 TWS（端口 7497/7496）或 IB Gateway（端口 4002/4001）
- 测试环境中不建立真实连接，使用 MockIB 替代
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

import pandas as pd
from loguru import logger

from mytrader.execution.models import OrderResult, OrderStatus
from mytrader.risk.models import OrderIntent
from mytrader.strategy.base import SignalDirection


class IBKRBroker:
    """Interactive Brokers 经纪商。

    Args:
        host:        TWS/IB Gateway 主机（默认 127.0.0.1）
        port:        端口（7497=TWS Paper; 7496=TWS Live; 4002=GW Paper; 4001=GW Live）
        client_id:   客户端 ID（每个连接需唯一）
        timeout:     连接超时（秒）
        readonly:    True 时仅允许查询，禁止下单（Phase 3 初期保护）
        mode:        "semi_auto" | "auto"
        ib:          可注入的 IB 实例（测试时注入 Mock）
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 7497,
        client_id: int = 1,
        timeout: int = 10,
        readonly: bool = True,
        mode: str = "semi_auto",
        ib: Any | None = None,
    ) -> None:
        self._host = host
        self._port = port
        self._client_id = client_id
        self._timeout = timeout
        self._readonly = readonly
        self._mode = mode
        self._ib = ib
        self._submitted: dict[str, OrderResult] = {}

    def connect(self) -> bool:
        """建立与 TWS/IB Gateway 的连接。"""
        try:
            from ib_insync import IB
        except ImportError as exc:
            raise ImportError(
                "ib_insync not installed. Run: pip install ib_insync"
            ) from exc

        if self._ib is None:
            self._ib = IB()

        for attempt in range(1, 4):
            try:
                if not self._ib.isConnected():
                    self._ib.connect(
                        self._host,
                        self._port,
                        clientId=self._client_id,
                        timeout=self._timeout,
                        readonly=self._readonly,
                    )
                logger.info(
                    f"IBKRBroker connected: {self._host}:{self._port} "
                    f"client_id={self._client_id} readonly={self._readonly}"
                )
                return True
            except Exception as exc:
                logger.warning(f"IBKRBroker connect attempt {attempt}/3 failed: {exc}")
                time.sleep(2)

        logger.error("IBKRBroker: all connection attempts failed")
        return False

    def disconnect(self) -> None:
        """断开连接。"""
        if self._ib is not None:
            try:
                self._ib.disconnect()
                logger.info("IBKRBroker disconnected")
            except Exception as exc:
                logger.warning(f"IBKRBroker disconnect error: {exc}")

    @property
    def is_connected(self) -> bool:
        if self._ib is None:
            return False
        return bool(self._ib.isConnected())

    def submit(self, intent: OrderIntent, df: pd.DataFrame) -> OrderResult:
        """提交订单意图。

        readonly=True 时直接拒绝下单。
        semi_auto 模式：返回 PENDING（通知由 NotificationService 推送）。
        auto 模式：调用 IBKR API 下市价单。
        """
        # 幂等性检查
        if intent.client_order_id in self._submitted:
            logger.warning(
                f"[{intent.symbol}] Duplicate order_id={intent.client_order_id}, skipping"
            )
            return self._submitted[intent.client_order_id]

        if self._readonly:
            logger.warning(
                f"[{intent.symbol}] IBKRBroker is in readonly mode, order rejected"
            )
            result = self._make_rejected(intent, "IBKRBroker is readonly")
            self._submitted[intent.client_order_id] = result
            return result

        if self._mode == "semi_auto":
            return self._submit_semi_auto(intent)
        return self._submit_auto(intent)

    def _submit_semi_auto(self, intent: OrderIntent) -> OrderResult:
        """半自动模式：生成 PENDING 结果。"""
        result = OrderResult(
            client_order_id=intent.client_order_id,
            symbol=intent.symbol,
            direction=intent.direction,
            quantity=intent.quantity,
            fill_price=0.0,
            commission=0.0,
            status=OrderStatus.PENDING,
            filled_at=datetime.now(timezone.utc),
            stop_loss_price=intent.stop_loss_price,
            take_profit_price=intent.take_profit_price,
            meta={**intent.meta, "broker": "ibkr", "mode": "semi_auto"},
        )
        self._submitted[intent.client_order_id] = result
        logger.info(
            f"[{intent.symbol}] IBKR semi-auto order: {intent.direction.value} "
            f"{intent.quantity} @ ~${intent.entry_price:.2f}"
        )
        return result

    def _submit_auto(self, intent: OrderIntent) -> OrderResult:
        """全自动模式：调用 IBKR API 下市价单。"""
        if not self.is_connected:
            ok = self.connect()
            if not ok:
                result = self._make_rejected(intent, "IBKR connection failed")
                self._submitted[intent.client_order_id] = result
                return result

        try:
            from ib_insync import Stock, MarketOrder
        except ImportError as exc:
            raise ImportError("ib_insync not installed") from exc

        # 确定交易所和货币（简化：USD=美股 SMART，HKD=港股 SEHK）
        currency = intent.meta.get("currency", "USD")
        exchange = "SEHK" if currency == "HKD" else "SMART"

        try:
            contract = Stock(intent.symbol, exchange, currency)
            action = "BUY" if intent.direction == SignalDirection.BUY else "SELL"
            order = MarketOrder(action=action, totalQuantity=intent.quantity)
            order.orderRef = intent.client_order_id  # 幂等性 ID

            trade = self._ib.placeOrder(contract, order)
            self._ib.sleep(1)  # 等待确认回报

            result = self._parse_ibkr_trade(intent, trade)
        except Exception as exc:
            logger.error(f"[{intent.symbol}] IBKR placeOrder failed: {exc}")
            result = self._make_rejected(intent, str(exc))

        self._submitted[intent.client_order_id] = result
        logger.info(
            f"[{intent.symbol}] IBKR order: {intent.direction.value} {intent.quantity} "
            f"status={result.status.value}"
        )
        return result

    def cancel(self, client_order_id: str) -> bool:
        """取消订单（IBKR semi_auto 模式：标记为 CANCELLED）。"""
        cached = self._submitted.get(client_order_id)
        if cached and cached.status == OrderStatus.PENDING:
            if self._mode == "semi_auto":
                cached.status = OrderStatus.CANCELLED
                return True
            if self.is_connected:
                try:
                    # 找到并取消对应的 IBKR 订单
                    open_orders = self._ib.openOrders()
                    for order in open_orders:
                        if order.orderRef == client_order_id:
                            self._ib.cancelOrder(order)
                            cached.status = OrderStatus.CANCELLED
                            return True
                except Exception as exc:
                    logger.warning(f"IBKR cancel order failed: {exc}")
                    return False
        return False

    def get_positions(self) -> list[dict]:
        """查询 IBKR 真实持仓（用于对账）。"""
        if not self.is_connected:
            logger.warning("IBKRBroker.get_positions: not connected")
            return []
        try:
            positions = self._ib.positions()
            return [
                {
                    "symbol": pos.contract.symbol,
                    "quantity": pos.position,
                    "avg_cost": pos.avgCost,
                    "currency": pos.contract.currency,
                }
                for pos in positions
            ]
        except Exception as exc:
            logger.error(f"IBKRBroker.get_positions failed: {exc}")
            return []

    @property
    def order_history(self) -> list[OrderResult]:
        return list(self._submitted.values())

    # ------------------------------------------------------------------ #
    # 内部工具
    # ------------------------------------------------------------------ #

    def _make_rejected(self, intent: OrderIntent, reason: str) -> OrderResult:
        return OrderResult(
            client_order_id=intent.client_order_id,
            symbol=intent.symbol,
            direction=intent.direction,
            quantity=intent.quantity,
            fill_price=0.0,
            commission=0.0,
            status=OrderStatus.REJECTED,
            filled_at=datetime.now(timezone.utc),
            stop_loss_price=intent.stop_loss_price,
            take_profit_price=intent.take_profit_price,
            rejection_reason=reason,
            meta={**intent.meta, "broker": "ibkr"},
        )

    def _parse_ibkr_trade(self, intent: OrderIntent, trade: Any) -> OrderResult:
        """将 ib_insync Trade 对象解析为 OrderResult。"""
        from ib_insync import OrderStatus as IBStatus

        order_status = trade.orderStatus
        raw_status = order_status.status if hasattr(order_status, "status") else str(order_status)

        filled = getattr(order_status, "filled", 0)
        avg_fill_price = getattr(order_status, "avgFillPrice", 0.0)
        commission = getattr(order_status, "commission", 0.0)
        if commission is None or commission != commission:  # NaN check
            commission = 0.0

        # 状态映射
        if raw_status in ("Filled",):
            status = OrderStatus.FILLED
        elif raw_status in ("Cancelled", "Inactive"):
            status = OrderStatus.CANCELLED
        elif raw_status in ("Submitted", "PreSubmitted", "PendingSubmit"):
            status = OrderStatus.PENDING
        else:
            status = OrderStatus.PENDING

        return OrderResult(
            client_order_id=intent.client_order_id,
            symbol=intent.symbol,
            direction=intent.direction,
            quantity=int(filled) if filled else intent.quantity,
            fill_price=float(avg_fill_price),
            commission=float(commission),
            status=status,
            filled_at=datetime.now(timezone.utc),
            stop_loss_price=intent.stop_loss_price,
            take_profit_price=intent.take_profit_price,
            meta={
                **intent.meta,
                "broker": "ibkr",
                "raw_status": raw_status,
            },
        )
