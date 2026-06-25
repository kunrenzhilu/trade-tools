"""冷却期过滤器 — 同方向信号在 min_bars 间隔内只允许通过一次。

防止策略在震荡行情中频繁触发相同方向的信号（信号抖动）。
冷却期按 bar 计数（不依赖实际时间），由外部调用方维护 bar 序列。
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

import pandas as pd

from mytrader.signal.models import FilteredSignal
from mytrader.strategy.base import Signal, SignalDirection


class CooldownFilter:
    """冷却期过滤器。

    维护每个 (symbol, direction) 上一次通过信号的时间戳，
    通过对比 DataFrame index 的 bar 数来判断冷却期是否结束。

    Args:
        min_bars: 同向信号最小间隔 bar 数，默认 5
    """

    name = "cooldown_filter"

    def __init__(self, min_bars: int = 5) -> None:
        self.min_bars = min_bars
        # key: (symbol, direction) -> last pass timestamp
        self._last_pass: dict[tuple[str, str], datetime] = defaultdict(lambda: None)  # type: ignore[return-value]

    def apply(self, signal: Signal, df: pd.DataFrame) -> FilteredSignal:
        key = (signal.symbol, signal.direction.value)
        last_ts = self._last_pass.get(key)

        if last_ts is None:
            # 首次信号，直接通过
            self._last_pass[key] = signal.timestamp
            return FilteredSignal(source_signal=signal, passed=True)

        # 计算信号时间戳对应的 bar 位置
        # df.index 可能是 tz-naive 或 tz-aware；signal.timestamp 同理。统一转为 tz-naive 比较。
        all_idx = df.index

        # 若 df.index 是 tz-aware，先去掉 tz
        if hasattr(all_idx, 'tz') and all_idx.tz is not None:
            all_idx = all_idx.tz_localize(None)

        def _to_naive(ts):
            if ts is None:
                return None
            if hasattr(ts, 'tzinfo') and ts.tzinfo is not None:
                return ts.replace(tzinfo=None)
            return ts

        sig_ts = _to_naive(signal.timestamp)
        last_ts_cmp = _to_naive(last_ts)

        signal_idx = all_idx[all_idx <= sig_ts]
        last_idx = all_idx[all_idx <= last_ts_cmp]

        if signal_idx.empty or last_idx.empty:
            # 找不到对应 bar，放行
            self._last_pass[key] = signal.timestamp
            return FilteredSignal(source_signal=signal, passed=True)

        pos_signal = signal_idx.get_loc(signal_idx[-1]) if hasattr(signal_idx, "get_loc") else len(signal_idx) - 1
        pos_last = last_idx.get_loc(last_idx[-1]) if hasattr(last_idx, "get_loc") else len(last_idx) - 1

        # pandas Index.get_loc 返回 int 或 slice，统一处理
        if isinstance(pos_signal, slice):
            pos_signal = pos_signal.stop - 1
        if isinstance(pos_last, slice):
            pos_last = pos_last.stop - 1

        bars_elapsed = pos_signal - pos_last

        if bars_elapsed >= self.min_bars:
            self._last_pass[key] = signal.timestamp
            return FilteredSignal(source_signal=signal, passed=True)

        return FilteredSignal(
            source_signal=signal,
            passed=False,
            rejected_by=self.name,
            rejection_reason=(
                f"{signal.direction.value} signal within cooldown: "
                f"{bars_elapsed} bars elapsed < min_bars={self.min_bars}"
            ),
        )

    def reset(self) -> None:
        """重置冷却状态（测试用）。"""
        self._last_pass.clear()
