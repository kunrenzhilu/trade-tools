"""Signal Filter 数据模型：FilteredSignal + FilterResult。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mytrader.strategy.base import Signal


@dataclass
class FilteredSignal:
    """经过过滤器流水线后的信号。

    Attributes:
        source_signal: 原始策略信号
        passed:        是否通过所有过滤器
        rejected_by:   被哪个过滤器拒绝（None 表示通过）
        rejection_reason: 拒绝原因说明
    """

    source_signal: "Signal"
    passed: bool = True
    rejected_by: str | None = None
    rejection_reason: str | None = None

    @property
    def symbol(self) -> str:
        return self.source_signal.symbol

    @property
    def direction(self):
        return self.source_signal.direction

    @property
    def timestamp(self):
        return self.source_signal.timestamp

    @property
    def confidence(self) -> float:
        return self.source_signal.confidence

    @property
    def price_hint(self) -> float | None:
        return self.source_signal.price_hint


@dataclass
class FilterResult:
    """一批信号经过流水线后的过滤统计。

    Attributes:
        original_signal_count: 进入流水线的原始信号数量
        passed_count:          通过所有过滤器的信号数量
        filtered_by:           各过滤器拦截的信号数量，key 为过滤器名称
        filter_rate:           过滤率 = 1 - passed/original
    """

    original_signal_count: int = 0
    passed_count: int = 0
    filtered_by: dict[str, int] = field(default_factory=dict)

    @property
    def filter_rate(self) -> float:
        if self.original_signal_count == 0:
            return 0.0
        return 1.0 - self.passed_count / self.original_signal_count

    def record_filtered(self, filter_name: str) -> None:
        self.filtered_by[filter_name] = self.filtered_by.get(filter_name, 0) + 1

    def __repr__(self) -> str:
        return (
            f"FilterResult(original={self.original_signal_count}, "
            f"passed={self.passed_count}, "
            f"filter_rate={self.filter_rate:.1%}, "
            f"filtered_by={self.filtered_by})"
        )
