"""MACD 信号线交叉策略。

信号规则：
    - MACD 线上穿信号线 → BUY  (+1)
    - MACD 线下穿信号线 → SELL (-1)
    - 否则              → HOLD  (0)

适用场景：中期趋势确认，适合日线级别，不适合短周期（噪音大）。
"""

from __future__ import annotations

import pandas as pd

from mytrader.strategy.indicators import macd, crossed_above, crossed_below
from mytrader.strategy.registry import register_strategy


@register_strategy("macd_cross")
def macd_signal(
    close: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal_period: int = 9,
) -> pd.Series:
    """MACD 信号线交叉信号。

    Args:
        close:         收盘价 Series
        fast:          快线 EMA 周期（默认 12）
        slow:          慢线 EMA 周期（默认 26）
        signal_period: 信号线 EMA 周期（默认 9）

    Returns:
        信号 Series：1=BUY, -1=SELL, 0=HOLD
    """
    macd_line, signal_line, _ = macd(close, fast, slow, signal_period)

    buy_signal  = crossed_above(macd_line, signal_line).astype(int)
    sell_signal = crossed_below(macd_line, signal_line).astype(int)

    signal = buy_signal - sell_signal

    # ⚠️ shift(1) 避免前视偏差
    return signal.shift(1).fillna(0).astype(int)
