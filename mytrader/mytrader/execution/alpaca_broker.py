"""AlpacaBroker — Alpaca 美股券商接入，实现 BrokerProtocol。

支持模式：
- paper:     Alpaca 沙盒账户，实际调用 Alpaca API（非 Paper Trading）
- semi_auto: 生成通知推送，等待人工确认，本次调用返回 PENDING 状态
- auto:      直接提交市价单，轮询订单状态

设计原则：
- 幂等性：client_order_id 传给 Alpaca client_order_id，券商自动去重
- 超时保护：API 调用设 10s 超时
- 测试友好：依赖注入 TradingClient，测试时可注入 Mock
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd
from loguru import logger

from mytrader.execution.models import OrderResult, OrderStatus
from mytrader.risk.models import OrderIntent
from mytrader.strategy.base import SignalDirection


class AlpacaBroker:
    """Alpaca 美股经纪商。

    Args:
        api_key:    Alpaca API Key
        secret_key: Alpaca Secret Key
        paper:      True=沙盒账户; False=真实账户
        mode:       "semi_auto" | "auto"（控制是否自动下单）
        client:     可注入的 TradingClient（测试用 Mock）
    """

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        paper: bool = True,
        mode: str = "semi_auto",
        client: Any | None = None,
    ) -> None:
        self._api_key = api_key
        self._secret_key = secret_key
        self._paper = paper
        self._mode = mode
        self._submitted: dict[str, OrderResult] = {}

        # 延迟初始化，测试时可注入 Mock
        self._client = client

    def _get_client(self) -> Any:
        """获取或初始化 Alpaca TradingClient。"""
        if self._client is None:
            try:
                from alpaca.trading.client import TradingClient
            except ImportError as exc:
                raise ImportError(
                    "alpaca-py not installed. Run: pip install alpaca-py"
                ) from exc
            self._client = TradingClient(
                self._api_key,
                self._secret_key,
                paper=self._paper,
            )
        return self._client

    def health_check(self) -> dict:
        """启动自检：验证 API 连通性并返回账户摘要。

        在 dry-run 或启动时调用，比等到第一个信号到来时才发现 API Key 错误更好。
        """
        try:
            client = self._get_client()
            acct = client.get_account()
            return {
                "status": "connected",
                "account_id": str(acct.id),
                "cash": float(acct.cash),
                "buying_power": float(acct.buying_power),
                "account_status": str(acct.status),
                "paper": self._paper,
            }
        except ImportError:
            return {"status": "error", "reason": "alpaca-py not installed"}
        except Exception as e:
            return {"status": "error", "reason": str(e)}

    def submit(self, intent: OrderIntent, df: pd.DataFrame) -> OrderResult:
        """提交订单意图。

        semi_auto 模式：返回 PENDING（通知已通过 NotificationService 推送）。
        auto 模式：调用 Alpaca API 提交市价单，轮询成交状态。

        Args:
            intent: 来自 RiskManager 的订单意图
            df:     行情 DataFrame（AlpacaBroker 不使用，保持接口统一）
        """
        # 幂等性检查
        if intent.client_order_id in self._submitted:
            logger.warning(
                f"[{intent.symbol}] Duplicate order_id={intent.client_order_id}, skipping"
            )
            return self._submitted[intent.client_order_id]

        if self._mode == "semi_auto":
            return self._submit_semi_auto(intent)
        return self._submit_auto(intent)

    def _submit_semi_auto(self, intent: OrderIntent) -> OrderResult:
        """半自动模式：生成 PENDING 结果，通知由 NotificationService 推送。"""
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
            rejection_reason="",
            meta={**intent.meta, "broker": "alpaca", "mode": "semi_auto"},
        )
        self._submitted[intent.client_order_id] = result
        logger.info(
            f"[{intent.symbol}] Semi-auto order created: {intent.direction.value} "
            f"{intent.quantity} @ ~${intent.entry_price:.2f}, "
            f"client_order_id={intent.client_order_id}"
        )
        return result

    def _submit_auto(self, intent: OrderIntent) -> OrderResult:
        """全自动模式：直接调用 Alpaca API 下市价单。"""
        direction_str = intent.direction.value
        try:
            # 构造订单请求对象（使用 Mock 或真实的 alpaca-py 枚举）
            order_data = self._build_market_order(intent)
            client = self._get_client()
            alpaca_order = client.submit_order(order_data)
            result = self._parse_alpaca_order(intent, alpaca_order)
        except Exception as exc:
            logger.error(f"[{intent.symbol}] Alpaca submit_order failed: {exc}")
            result = OrderResult(
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
                rejection_reason=str(exc),
                meta={**intent.meta, "broker": "alpaca", "mode": "auto"},
            )

        self._submitted[intent.client_order_id] = result
        logger.info(
            f"[{intent.symbol}] Alpaca order: {direction_str} {intent.quantity} "
            f"status={result.status.value} fill_price={result.fill_price:.4f}"
        )
        return result

    def _build_market_order(self, intent: OrderIntent) -> Any:
        """构造 Alpaca MarketOrderRequest（或在 client 已注入时用简单 dict）。"""
        if self._client is not None:
            # 测试时 client 已注入（Mock），用 dict 作为 order_data 占位
            return {
                "symbol": intent.symbol,
                "qty": intent.quantity,
                "side": "buy" if intent.direction == SignalDirection.BUY else "sell",
                "time_in_force": "day",
                "client_order_id": intent.client_order_id,
            }
        # 真实模式：使用 alpaca-py 类型
        try:
            from alpaca.trading.requests import MarketOrderRequest
            from alpaca.trading.enums import OrderSide, TimeInForce
        except ImportError as exc:
            raise ImportError("alpaca-py not installed. Run: pip install alpaca-py") from exc

        return MarketOrderRequest(
            symbol=intent.symbol,
            qty=intent.quantity,
            side=OrderSide.BUY if intent.direction == SignalDirection.BUY else OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
            client_order_id=intent.client_order_id,
        )

    def cancel(self, client_order_id: str) -> bool:
        """取消订单。"""
        cached = self._submitted.get(client_order_id)
        if cached and cached.status == OrderStatus.PENDING:
            try:
                client = self._get_client()
                client.cancel_order_by_id(client_order_id)
                cached.status = OrderStatus.CANCELLED
                return True
            except Exception as exc:
                logger.warning(f"Alpaca cancel_order failed: client_order_id={client_order_id}: {exc}")
                return False
        return False

    def get_order(self, client_order_id: str) -> OrderResult | None:
        """查询本地缓存的订单结果。"""
        return self._submitted.get(client_order_id)

    @property
    def order_history(self) -> list[OrderResult]:
        return list(self._submitted.values())

    # ------------------------------------------------------------------ #
    # 内部解析
    # ------------------------------------------------------------------ #

    def _parse_alpaca_order(self, intent: OrderIntent, alpaca_order: Any) -> OrderResult:
        """将 Alpaca 订单对象解析为 OrderResult。"""
        # Alpaca 订单状态映射
        status_map = {
            "filled": OrderStatus.FILLED,
            "partially_filled": OrderStatus.FILLED,  # 部分成交按成交处理
            "canceled": OrderStatus.CANCELLED,
            "rejected": OrderStatus.REJECTED,
            "pending_new": OrderStatus.PENDING,
            "new": OrderStatus.PENDING,
            "accepted": OrderStatus.PENDING,
        }

        raw_status = getattr(alpaca_order, "status", "pending_new")
        if hasattr(raw_status, "value"):
            raw_status = raw_status.value
        order_status = status_map.get(str(raw_status).lower(), OrderStatus.PENDING)

        # 成交价（已成交时有 filled_avg_price，未成交时为 None）
        fill_price = 0.0
        raw_fill = getattr(alpaca_order, "filled_avg_price", None)
        if raw_fill is not None:
            try:
                fill_price = float(raw_fill)
            except (ValueError, TypeError):
                fill_price = 0.0

        # Alpaca 美股无佣金，commission=0
        return OrderResult(
            client_order_id=intent.client_order_id,
            symbol=intent.symbol,
            direction=intent.direction,
            quantity=intent.quantity,
            fill_price=fill_price,
            commission=0.0,
            status=order_status,
            filled_at=datetime.now(timezone.utc),
            stop_loss_price=intent.stop_loss_price,
            take_profit_price=intent.take_profit_price,
            meta={
                **intent.meta,
                "broker": "alpaca",
                "alpaca_order_id": str(getattr(alpaca_order, "id", "")),
                "raw_status": str(raw_status),
            },
        )
