"""市场情绪过滤器 — 基于大盘趋势（参考标的 200 日均线）判断市场方向。

Phase 2 实现：简化版，检查参考标的（如 SPY）是否在 200 日均线之上。
- 若大盘跌破 200 日均线，只允许 SELL 信号，屏蔽 BUY 信号。
- 若未提供参考数据，过滤器放行（降级处理）。
"""

from __future__ import annotations

import pandas as pd

from mytrader.signal.models import FilteredSignal
from mytrader.strategy.base import Signal, SignalDirection
from mytrader.strategy.indicators import sma


class SentimentFilter:
    """大盘趋势过滤器（简化版市场情绪过滤）。"""

    name = "sentiment_filter"

    def __init__(self, ma_period: int = 200) -> None:
        self.ma_period = ma_period
        self._benchmark_df: pd.DataFrame | None = None

    def set_benchmark(self, df: pd.DataFrame) -> None:
        """设置参考标的 OHLCV 数据（如 SPY 日线）。"""
        self._benchmark_df = df

    def apply(self, signal: Signal, df: pd.DataFrame) -> FilteredSignal:
        # 若无参考数据，直接放行
        if self._benchmark_df is None or "close" not in self._benchmark_df.columns:
            return FilteredSignal(source_signal=signal, passed=True)

        ts = signal.timestamp
        bdf = self._benchmark_df
        ma = sma(bdf["close"], self.ma_period).shift(1)

        idx = bdf.index[bdf.index <= ts]
        if idx.empty or len(idx) < self.ma_period:
            return FilteredSignal(source_signal=signal, passed=True)

        latest = idx[-1]
        ma_val = ma.loc[latest]
        close_val = bdf.loc[latest, "close"]

        if pd.isna(ma_val):
            return FilteredSignal(source_signal=signal, passed=True)

        # 大盘跌破 200 日均线时，禁止做多
        if close_val < ma_val and signal.direction == SignalDirection.BUY:
            return FilteredSignal(
                source_signal=signal,
                passed=False,
                rejected_by=self.name,
                rejection_reason=(
                    f"Benchmark close={close_val:.2f} < MA{self.ma_period}={ma_val:.2f}, "
                    f"bearish market, BUY signal suppressed"
                ),
            )

        return FilteredSignal(source_signal=signal, passed=True)
