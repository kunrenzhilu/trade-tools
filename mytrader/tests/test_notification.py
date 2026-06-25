"""测试 Phase 3 通知推送模块：TelegramAlerter + WeChatWorkAlerter + NotificationService。"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, call

import pytest

from mytrader.execution.notification import (
    TelegramAlerter,
    WeChatWorkAlerter,
    NotificationService,
    _LEVEL_WEIGHT,
)
from mytrader.execution.models import OrderResult, OrderStatus
from mytrader.infra.config import NotificationConfig
from mytrader.risk.models import OrderIntent
from mytrader.strategy.base import SignalDirection


# ---------------------------------------------------------------------------
# 测试夹具
# ---------------------------------------------------------------------------

def make_notification_config(**kwargs) -> NotificationConfig:
    defaults = {
        "telegram_enabled": False,
        "wechat_work_enabled": False,
        "alert_cooldown_seconds": 0,  # 测试时禁用冷却
        "min_alert_level": "INFO",
    }
    defaults.update(kwargs)
    return NotificationConfig(**defaults)


def make_intent(symbol: str = "AAPL", direction: SignalDirection = SignalDirection.BUY) -> OrderIntent:
    return OrderIntent(
        symbol=symbol,
        direction=direction,
        quantity=100,
        entry_price=150.0,
        stop_loss_price=147.0,
        take_profit_price=156.0,
        risk_amount=300.0,
        position_value=15000.0,
        timestamp=datetime.now(timezone.utc),
        strategy_name="dual_ma",
        client_order_id="test_order_001",
    )


def make_order_result(status: OrderStatus = OrderStatus.FILLED) -> OrderResult:
    return OrderResult(
        client_order_id="test_order_001",
        symbol="AAPL",
        direction=SignalDirection.BUY,
        quantity=100,
        fill_price=150.15,
        commission=0.15,
        status=status,
        filled_at=datetime.now(timezone.utc),
        stop_loss_price=147.0,
        take_profit_price=156.0,
    )


# ---------------------------------------------------------------------------
# TelegramAlerter 测试
# ---------------------------------------------------------------------------

class TestTelegramAlerter:
    def test_send_success(self):
        """发送成功时返回 True。"""
        alerter = TelegramAlerter(bot_token="test_token", chat_id="12345")
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None

        with patch("httpx.post", return_value=mock_resp) as mock_post:
            result = alerter.send("Hello World")
            assert result is True
            mock_post.assert_called_once()
            call_kwargs = mock_post.call_args
            assert "test_token" in call_kwargs[0][0]
            assert call_kwargs[1]["json"]["chat_id"] == "12345"
            assert call_kwargs[1]["json"]["text"] == "Hello World"

    def test_send_failure_returns_false(self):
        """发送失败时返回 False，不抛异常。"""
        alerter = TelegramAlerter(bot_token="bad_token", chat_id="12345")
        with patch("httpx.post", side_effect=Exception("Network error")):
            result = alerter.send("test message")
            assert result is False

    def test_send_http_error_returns_false(self):
        """HTTP 非 2xx 时返回 False。"""
        alerter = TelegramAlerter(bot_token="token", chat_id="123")
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = Exception("404 Not Found")
        with patch("httpx.post", return_value=mock_resp):
            result = alerter.send("test")
            assert result is False


# ---------------------------------------------------------------------------
# WeChatWorkAlerter 测试
# ---------------------------------------------------------------------------

class TestWeChatWorkAlerter:
    def test_send_success(self):
        """企业微信发送成功。"""
        alerter = WeChatWorkAlerter(webhook_url="https://qyapi.example.com/webhook")
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None

        with patch("httpx.post", return_value=mock_resp) as mock_post:
            result = alerter.send("企业微信消息")
            assert result is True
            call_kwargs = mock_post.call_args
            assert call_kwargs[1]["json"]["msgtype"] == "text"
            assert "企业微信消息" in call_kwargs[1]["json"]["text"]["content"]

    def test_send_failure_returns_false(self):
        """发送失败时返回 False，不抛异常。"""
        alerter = WeChatWorkAlerter(webhook_url="https://bad.url")
        with patch("httpx.post", side_effect=Exception("Timeout")):
            result = alerter.send("message")
            assert result is False


# ---------------------------------------------------------------------------
# NotificationService 测试
# ---------------------------------------------------------------------------

class TestNotificationService:
    def test_no_channels_logs_only(self, capfd):
        """无渠道时只记录日志，不发送。"""
        cfg = make_notification_config()
        svc = NotificationService(cfg)
        # 不抛异常
        svc.notify_alert("INFO", "test message")

    def test_notify_order_filled(self):
        """订单成交通知格式正确。"""
        mock_tg = MagicMock()
        mock_tg.send.return_value = True
        cfg = make_notification_config()
        svc = NotificationService(cfg, telegram=mock_tg)

        intent = make_intent()
        result = make_order_result(OrderStatus.FILLED)
        svc.notify_order(intent, result)

        mock_tg.send.assert_called_once()
        text = mock_tg.send.call_args[0][0]
        assert "AAPL" in text
        assert "✅" in text
        assert "150.15" in text

    def test_notify_order_rejected(self):
        """订单拒绝通知格式正确。"""
        mock_tg = MagicMock()
        mock_tg.send.return_value = True
        cfg = make_notification_config()
        svc = NotificationService(cfg, telegram=mock_tg)

        intent = make_intent()
        result = make_order_result(OrderStatus.REJECTED)
        result.rejection_reason = "Insufficient cash"
        svc.notify_order(intent, result)

        text = mock_tg.send.call_args[0][0]
        assert "❌" in text
        assert "Insufficient cash" in text

    def test_notify_semi_auto_order(self):
        """半自动模式推送包含 JSON 内容。"""
        mock_tg = MagicMock()
        mock_tg.send.return_value = True
        cfg = make_notification_config()
        svc = NotificationService(cfg, telegram=mock_tg)

        intent = make_intent()
        svc.notify_semi_auto_order(intent)

        text = mock_tg.send.call_args[0][0]
        assert "半自动下单" in text
        assert "client_order_id" in text
        assert "test_order_001" in text

    def test_sell_direction_label(self):
        """卖出订单显示卖出标签。"""
        mock_tg = MagicMock()
        mock_tg.send.return_value = True
        cfg = make_notification_config()
        svc = NotificationService(cfg, telegram=mock_tg)

        intent = make_intent(direction=SignalDirection.SELL)
        result = make_order_result(OrderStatus.FILLED)
        result.direction = SignalDirection.SELL
        svc.notify_order(intent, result)

        text = mock_tg.send.call_args[0][0]
        assert "卖出" in text

    def test_alert_min_level_filter(self):
        """低于 min_alert_level 的告警被过滤。"""
        mock_tg = MagicMock()
        cfg = make_notification_config(min_alert_level="WARN")
        svc = NotificationService(cfg, telegram=mock_tg)

        svc.notify_alert("INFO", "this should be suppressed")
        mock_tg.send.assert_not_called()

    def test_alert_passes_min_level(self):
        """等于或超过 min_alert_level 的告警正常发送。"""
        mock_tg = MagicMock()
        mock_tg.send.return_value = True
        cfg = make_notification_config(min_alert_level="WARN")
        svc = NotificationService(cfg, telegram=mock_tg)

        svc.notify_alert("WARN", "warning message")
        mock_tg.send.assert_called_once()

    def test_alert_cooldown_deduplication(self):
        """相同告警在冷却期内只发送一次。"""
        mock_tg = MagicMock()
        mock_tg.send.return_value = True
        cfg = make_notification_config(alert_cooldown_seconds=9999)
        svc = NotificationService(cfg, telegram=mock_tg)

        svc.notify_alert("WARN", "duplicate alert")
        svc.notify_alert("WARN", "duplicate alert")
        svc.notify_alert("WARN", "duplicate alert")

        # 只发送一次
        assert mock_tg.send.call_count == 1

    def test_different_alerts_not_deduplicated(self):
        """不同内容的告警不受冷却期影响。"""
        mock_tg = MagicMock()
        mock_tg.send.return_value = True
        cfg = make_notification_config(alert_cooldown_seconds=9999)
        svc = NotificationService(cfg, telegram=mock_tg)

        svc.notify_alert("WARN", "alert A")
        svc.notify_alert("WARN", "alert B")

        assert mock_tg.send.call_count == 2

    def test_channel_exception_does_not_propagate(self):
        """渠道发送异常不向上传播。"""
        mock_tg = MagicMock()
        mock_tg.send.side_effect = Exception("Channel crashed!")
        cfg = make_notification_config()
        svc = NotificationService(cfg, telegram=mock_tg)

        # 不应抛出异常
        svc.notify_alert("ERROR", "test")

    def test_wechat_removes_markdown(self):
        """企业微信去掉 Markdown 标记。"""
        mock_ww = MagicMock()
        mock_ww.send.return_value = True
        cfg = make_notification_config()
        svc = NotificationService(cfg, wechat=mock_ww)

        svc.notify_alert("ERROR", "**bold** _italic_ `code`")
        text = mock_ww.send.call_args[0][0]
        assert "*" not in text
        assert "`" not in text
        assert "_" not in text

    def test_alert_extra_dict_included(self):
        """extra 字典内容包含在通知文本中。"""
        mock_tg = MagicMock()
        mock_tg.send.return_value = True
        cfg = make_notification_config()
        svc = NotificationService(cfg, telegram=mock_tg)

        svc.notify_alert("ERROR", "system error", extra={"module": "risk_manager"})
        text = mock_tg.send.call_args[0][0]
        assert "risk_manager" in text


# ---------------------------------------------------------------------------
# 告警级别权重
# ---------------------------------------------------------------------------

class TestAlertLevelWeight:
    def test_level_order(self):
        assert _LEVEL_WEIGHT["INFO"] < _LEVEL_WEIGHT["WARN"]
        assert _LEVEL_WEIGHT["WARN"] < _LEVEL_WEIGHT["ERROR"]
        assert _LEVEL_WEIGHT["ERROR"] < _LEVEL_WEIGHT["CRITICAL"]
