"""成交量确认过滤器 — 当日量 > N日均量 * threshold 时信号有效。"""

from __future__ import annotations

import pandas as pd

from mytrader.signal.models import FilteredSignal
from mytrader.strategy.base import Signal


class VolumeFilter:
    """成交量确认过滤器。

    只允许当日成交量 > 过去 window 日平均成交量 * threshold 的信号通过。
    防前视偏差：使用 rolling(window).mean().shift(1)。
    """

    name = "volume_filter"

    def __init__(self, threshold: float = 1.5, window: int = 20) -> None:
        self.threshold = threshold
        self.window = window

    def apply(self, signal: Signal, df: pd.DataFrame) -> FilteredSignal:
        ts = signal.timestamp

        # 找到信号时间对应的行（向前最近匹配）
        if "volume" not in df.columns:
            return FilteredSignal(source_signal=signal, passed=True)

        # 计算过去 window 日平均量（shift(1) 防前视偏差）
        avg_vol = df["volume"].rolling(self.window).mean().shift(1)

        # 取最近不超过信号时间的行
        idx = df.index[df.index <= ts]
        if idx.empty:
            return FilteredSignal(source_signal=signal, passed=True)

        latest = idx[-1]
        current_vol = df.loc[latest, "volume"]
        avg = avg_vol.loc[latest]

        if pd.isna(avg) or pd.isna(current_vol):
            # 数据不足，放行（避免误杀）
            return FilteredSignal(source_signal=signal, passed=True)

        if current_vol >= avg * self.threshold:
            return FilteredSignal(source_signal=signal, passed=True)

        return FilteredSignal(
            source_signal=signal,
            passed=False,
            rejected_by=self.name,
            rejection_reason=(
                f"volume={current_vol:.0f} < avg_vol*threshold="
                f"{avg * self.threshold:.0f} (avg={avg:.0f}, threshold={self.threshold})"
            ),
        )
