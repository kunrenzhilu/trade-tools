"""Notification Service — 订单通知 + 告警推送（Telegram / 企业微信）。

设计原则：
- 通知失败只记日志，不抛异常，不阻塞主流程
- 防骚扰冷却：同类告警最小间隔 alert_cooldown_seconds
- 告警级别分层：INFO / WARN / ERROR / CRITICAL
- 半自动模式下，订单 JSON 随通知一起推送，等待人工确认
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TextIO
from typing import Any

from loguru import logger

from mytrader.infra.config import NotificationConfig
from mytrader.execution.models import OrderResult, OrderStatus
from mytrader.risk.models import OrderIntent
from mytrader.strategy.base import SignalDirection


# ---------------------------------------------------------------------------
# 告警级别权重（用于 min_alert_level 过滤）
# ---------------------------------------------------------------------------

_LEVEL_WEIGHT: dict[str, int] = {
    "INFO": 0,
    "WARN": 1,
    "ERROR": 2,
    "CRITICAL": 3,
}

_LEVEL_EMOJI: dict[str, str] = {
    "INFO": "ℹ️",
    "WARN": "⚠️",
    "ERROR": "🚨",
    "CRITICAL": "🆘",
    "TRADE": "💹",
}


# ---------------------------------------------------------------------------
# 渠道实现
# ---------------------------------------------------------------------------

class TelegramAlerter:
    """Telegram Bot 推送（通过 REST API，无第三方 SDK 依赖）。"""

    def __init__(self, bot_token: str, chat_id: str) -> None:
        self.bot_token = bot_token
        self.chat_id = chat_id
        self._base_url = f"https://api.telegram.org/bot{bot_token}"

    def send(self, text: str, parse_mode: str = "Markdown") -> bool:
        """发送消息，返回是否成功。"""
        try:
            import httpx  # 运行时导入，测试时可 Mock
            resp = httpx.post(
                f"{self._base_url}/sendMessage",
                json={"chat_id": self.chat_id, "text": text, "parse_mode": parse_mode},
                timeout=10.0,
            )
            resp.raise_for_status()
            return True
        except Exception as exc:
            logger.warning(f"TelegramAlerter.send failed: {exc}")
            return False


class WeChatWorkAlerter:
    """企业微信群机器人 Webhook 推送。"""

    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url

    def send(self, content: str) -> bool:
        """发送文本消息，返回是否成功。"""
        try:
            import httpx
            resp = httpx.post(
                self.webhook_url,
                json={"msgtype": "text", "text": {"content": content}},
                timeout=10.0,
            )
            resp.raise_for_status()
            return True
        except Exception as exc:
            logger.warning(f"WeChatWorkAlerter.send failed: {exc}")
            return False


# ---------------------------------------------------------------------------
# 通知服务
# ---------------------------------------------------------------------------

class NotificationService:
    """统一通知服务：管理多个推送渠道，支持冷却期去重。

    Args:
        config: NotificationConfig 配置
        telegram: 可选的 TelegramAlerter（测试时注入 Mock）
        wechat:   可选的 WeChatWorkAlerter（测试时注入 Mock）
    """

    def __init__(
        self,
        config: NotificationConfig,
        telegram: TelegramAlerter | None = None,
        wechat: WeChatWorkAlerter | None = None,
    ) -> None:
        self._config = config
        self._min_weight = _LEVEL_WEIGHT.get(config.min_alert_level, 1)

        # 渠道初始化（未提供则根据配置自动创建）
        if telegram is None and config.telegram_enabled and config.telegram_bot_token:
            telegram = TelegramAlerter(config.telegram_bot_token, config.telegram_chat_id)
        if wechat is None and config.wechat_work_enabled and config.wechat_work_webhook_url:
            wechat = WeChatWorkAlerter(config.wechat_work_webhook_url)

        self._telegram = telegram
        self._wechat = wechat

        # 冷却期：{key -> last_sent_timestamp}
        self._cooldown: dict[str, float] = {}

        # Telegram 消息日志文件（记录所有发出的消息，便于追溯用户收到的内容）
        self._tg_log_path = Path.home() / ".mytrader" / "telegram.log"
        try:
            self._tg_log_path.parent.mkdir(parents=True, exist_ok=True)
            # 测试文件可写性
            self._tg_log_path.open("a").close()
        except Exception:
            logger.warning(f"Cannot write telegram log to {self._tg_log_path}")
            self._tg_log_path = None

    # ------------------------------------------------------------------ #
    # 公共接口
    # ------------------------------------------------------------------ #

    def notify_order(self, intent: OrderIntent, result: OrderResult) -> None:
        """订单成交/拒绝通知（TRADE 级别，始终发送，不受 min_alert_level 限制）。"""
        status_emoji = "✅" if result.status == OrderStatus.FILLED else "❌"
        direction_str = "买入" if intent.direction == SignalDirection.BUY else "卖出"

        lines = [
            f"{status_emoji} *订单通知* — {result.symbol}",
            f"方向：{direction_str}  数量：{result.quantity} 股",
            f"成交价：${result.fill_price:.2f}  手续费：${result.commission:.2f}",
            f"状态：{result.status.value}",
        ]
        if result.stop_loss_price:
            lines.append(f"止损：${result.stop_loss_price:.2f}")
        if result.take_profit_price:
            lines.append(f"止盈：${result.take_profit_price:.2f}")
        if result.rejection_reason:
            lines.append(f"拒绝原因：{result.rejection_reason}")
        lines.append(f"时间：{result.filled_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")

        self._send_all("\n".join(lines), cooldown_key=None)  # 订单通知不冷却

    def notify_semi_auto_order(self, intent: OrderIntent) -> None:
        """半自动模式：推送订单 JSON，等待人工确认。"""
        direction_str = "买入" if intent.direction == SignalDirection.BUY else "卖出"
        intent_dict = {
            "symbol": intent.symbol,
            "direction": intent.direction.value,
            "quantity": intent.quantity,
            "entry_price": intent.entry_price,
            "stop_loss_price": intent.stop_loss_price,
            "take_profit_price": intent.take_profit_price,
            "position_value": intent.position_value,
            "strategy_name": intent.strategy_name,
            "client_order_id": intent.client_order_id,
            "timestamp": intent.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
        }
        lines = [
            "💹 *半自动下单请求*",
            f"标的：{intent.symbol}  方向：{direction_str}",
            f"数量：{intent.quantity} 股  约 ${intent.position_value:.0f}",
            f"建议入场：${intent.entry_price:.2f}  止损：${intent.stop_loss_price:.2f}",
            "",
            "```json",
            json.dumps(intent_dict, ensure_ascii=False, indent=2),
            "```",
            "_请确认后手动在券商 APP 下单_",
        ]
        self._send_all("\n".join(lines), cooldown_key=None)

    def notify_alert(self, level: str, message: str, extra: dict[str, Any] | None = None) -> None:
        """发送告警通知。

        Args:
            level:   告警级别（INFO/WARN/ERROR/CRITICAL）
            message: 告警内容
            extra:   附加信息字典
        """
        weight = _LEVEL_WEIGHT.get(level.upper(), 0)
        if weight < self._min_weight:
            logger.debug(f"Alert suppressed (level={level} < min={self._config.min_alert_level}): {message}")
            return

        emoji = _LEVEL_EMOJI.get(level.upper(), "")
        text = f"{emoji} [{level.upper()}] {message}"
        if extra:
            text += f"\n{json.dumps(extra, ensure_ascii=False, default=str)}"

        # 冷却期去重
        cooldown_key = f"{level.upper()}:{message[:50]}"
        self._send_all(text, cooldown_key=cooldown_key)

    def send_message(self, text: str) -> None:
        """直接发送消息（不受 min_alert_level / cooldown 限制）。

        用于扫描结果、对账报告等必须送达的通知。
        """
        self._send_all(text, cooldown_key=None)

    def _write_tg_log(self, text: str, sent: bool) -> None:
        """将发出的消息记录到 ~/.mytrader/telegram.log。

        格式：[timestamp] [SENT/FAILED] message

        用于追溯用户收到了哪些消息，便于调试和审计。
        """
        if not self._tg_log_path:
            return
        try:
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            status = "SENT" if sent else "FAILED"
            with self._tg_log_path.open("a", encoding="utf-8") as f:
                f.write(f"[{ts}] [{status}]\n{text}\n{'='*60}\n")
        except Exception as exc:
            logger.debug(f"Failed to write telegram log: {exc}")

    # ------------------------------------------------------------------ #
    # 内部方法
    # ------------------------------------------------------------------ #

    def _send_all(self, text: str, cooldown_key: str | None) -> None:
        """推送到所有启用的渠道，可选冷却期去重。"""
        now = time.monotonic()
        if cooldown_key is not None:
            last = self._cooldown.get(cooldown_key, 0.0)
            if now - last < self._config.alert_cooldown_seconds:
                logger.debug(f"Notification cooldown active for key={cooldown_key!r}")
                return
            self._cooldown[cooldown_key] = now

        sent = False
        if self._telegram is not None:
            try:
                sent = self._telegram.send(text) or sent
            except Exception as exc:
                logger.warning(f"TelegramAlerter send raised: {exc}")
        if self._wechat is not None:
            # 企业微信不支持 Markdown，去掉标记符号
            plain = text.replace("*", "").replace("`", "").replace("_", "")
            try:
                sent = self._wechat.send(plain) or sent
            except Exception as exc:
                logger.warning(f"WeChatWorkAlerter send raised: {exc}")

        if not (self._telegram or self._wechat):
            logger.info(f"[Notification no-channel] {text}")
        else:
            logger.info(f"Notification sent (channels={'tg' if self._telegram else ''}"
                        f"{'ww' if self._wechat else ''}): {text[:100]}")

        # 记录到 telegram.log（所有发出的消息，含时间戳和发送状态）
        self._write_tg_log(text, sent)
