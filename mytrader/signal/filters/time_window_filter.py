"""时间窗口过滤器 — 屏蔽开盘和收盘前缓冲期内的信号。

适用于日内交易：避免在开盘后 N 分钟和收盘前 N 分钟内入场。
对于日线数据（无具体时间），该过滤器默认放行。
"""

from __future__ import annotations

from datetime import time

import pandas as pd

from mytrader.signal.models import FilteredSignal
from mytrader.strategy.base import Signal


class TimeWindowFilter:
    """时间窗口过滤器。

    屏蔽：
    - 开盘后 open_buffer_min 分钟内的信号（美股 9:30 开盘）
    - 收盘前 close_buffer_min 分钟内的信号（美股 16:00 收盘）

    对于日线数据（timestamp 无时分秒），直接放行。
    """

    name = "time_window_filter"

    def __init__(
        self,
        open_buffer_min: int = 15,
        close_buffer_min: int = 15,
        market_open: time = time(9, 30),
        market_close: time = time(16, 0),
    ) -> None:
        self.open_buffer_min = open_buffer_min
        self.close_buffer_min = close_buffer_min
        self.market_open = market_open
        self.market_close = market_close

    def apply(self, signal: Signal, df: pd.DataFrame) -> FilteredSignal:
        ts = signal.timestamp
        # 去掉 timezone，避免与 naive datetime 比较时报错
        if hasattr(ts, 'tzinfo') and ts.tzinfo is not None:
            ts = ts.replace(tzinfo=None)
        signal_time = ts.time()

        # 如果时间恰好是午夜（日线数据），直接放行
        if signal_time == time(0, 0):
            return FilteredSignal(source_signal=signal, passed=True)

        from datetime import datetime, timedelta

        open_dt = datetime.combine(ts.date(), self.market_open)
        close_dt = datetime.combine(ts.date(), self.market_close)

        open_cutoff = (open_dt + timedelta(minutes=self.open_buffer_min)).time()
        close_cutoff = (close_dt - timedelta(minutes=self.close_buffer_min)).time()

        if signal_time < open_cutoff:
            return FilteredSignal(
                source_signal=signal,
                passed=False,
                rejected_by=self.name,
                rejection_reason=(
                    f"Signal time {signal_time} is within {self.open_buffer_min}min "
                    f"of market open {self.market_open}"
                ),
            )

        if signal_time > close_cutoff:
            return FilteredSignal(
                source_signal=signal,
                passed=False,
                rejected_by=self.name,
                rejection_reason=(
                    f"Signal time {signal_time} is within {self.close_buffer_min}min "
                    f"of market close {self.market_close}"
                ),
            )

        return FilteredSignal(source_signal=signal, passed=True)
