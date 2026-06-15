"""ATR 波动率过滤器 — ATR/close > max_atr_pct 时市场过于波动，过滤信号。"""

from __future__ import annotations

import pandas as pd

from mytrader.signal.models import FilteredSignal
from mytrader.strategy.base import Signal
from mytrader.strategy.indicators import atr as compute_atr


class ATRFilter:
    """ATR 波动率过滤器。

    当 ATR(period) / close_price > max_atr_pct 时，认为市场极端波动，过滤所有信号。
    ATR 使用 shift(1) 防前视偏差。
    """

    name = "atr_filter"

    def __init__(self, period: int = 14, max_atr_pct: float = 0.05) -> None:
        self.period = period
        self.max_atr_pct = max_atr_pct

    def apply(self, signal: Signal, df: pd.DataFrame) -> FilteredSignal:
        ts = signal.timestamp
        required = {"high", "low", "close"}
        if not required.issubset(df.columns):
            return FilteredSignal(source_signal=signal, passed=True)

        # 计算 ATR 并 shift(1) 防前视偏差
        atr_series = compute_atr(df, period=self.period).shift(1)

        idx = df.index[df.index <= ts]
        if idx.empty:
            return FilteredSignal(source_signal=signal, passed=True)

        latest = idx[-1]
        atr_val = atr_series.loc[latest]
        close_val = df.loc[latest, "close"]

        if pd.isna(atr_val) or pd.isna(close_val) or close_val == 0:
            return FilteredSignal(source_signal=signal, passed=True)

        atr_pct = atr_val / close_val

        if atr_pct <= self.max_atr_pct:
            return FilteredSignal(source_signal=signal, passed=True)

        return FilteredSignal(
            source_signal=signal,
            passed=False,
            rejected_by=self.name,
            rejection_reason=(
                f"ATR/close={atr_pct:.3%} > max_atr_pct={self.max_atr_pct:.3%}, "
                f"market too volatile"
            ),
        )
