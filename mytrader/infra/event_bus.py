"""EventBus — 同步发布/订阅事件总线。

设计原则：
- 单个 handler 异常不阻断其他 handler
- 同步执行，适合 Phase 2 单进程场景
- 通过 Events 常量统一管理事件名称
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable

from loguru import logger


class Events:
    """全局事件类型常量。"""

    BAR_RECEIVED = "bar_received"
    SIGNAL_GENERATED = "signal_generated"
    SIGNAL_FILTERED = "signal_filtered"
    ORDER_INTENT_CREATED = "order_intent_created"
    ORDER_SUBMITTED = "order_submitted"
    ORDER_FILLED = "order_filled"
    POSITION_UPDATED = "position_updated"
    CIRCUIT_BREAKER_TRIGGERED = "circuit_breaker_triggered"
    ALERT = "alert"


class EventBus:
    """同步事件总线。

    用法：
        bus = EventBus()
        bus.subscribe(Events.SIGNAL_GENERATED, my_handler)
        bus.publish(Events.SIGNAL_GENERATED, signal)
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable[[Any], None]]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: Callable[[Any], None]) -> None:
        """注册事件处理器。"""
        self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: Callable[[Any], None]) -> None:
        """移除事件处理器。"""
        handlers = self._handlers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)

    def publish(self, event_type: str, payload: Any = None) -> None:
        """发布事件，同步调用所有 handler。单个 handler 异常不阻断其他 handler。"""
        for handler in list(self._handlers.get(event_type, [])):
            try:
                handler(payload)
            except Exception as exc:
                logger.exception(
                    f"EventBus handler error: event={event_type!r} "
                    f"handler={handler.__name__!r}: {exc}"
                )

    def clear(self) -> None:
        """清空所有订阅（测试用）。"""
        self._handlers.clear()
