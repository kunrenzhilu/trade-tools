"""RSI 均值回归策略。

信号规则：
    - RSI < oversold（默认 30）→ 超卖，BUY  (+1)
    - RSI > overbought（默认 70）→ 超买，SELL (-1)
    - 否则                      → HOLD  (0)

适用场景：震荡市；单边趋势中会频繁逆势，需配合趋势过滤。
"""

from __future__ import annotations

import pandas as pd

from mytrader.strategy.indicators import rsi
from mytrader.strategy.registry import register_strategy


@register_strategy("rsi_mean_revert")
def rsi_signal(
    close: pd.Series,
    period: int = 14,
    oversold: float = 30.0,
    overbought: float = 70.0,
) -> pd.Series:
    """RSI 超买超卖信号。

    Args:
        close:      收盘价 Series
        period:     RSI 计算周期（默认 14）
        oversold:   超卖阈值，低于此值发出 BUY（默认 30）
        overbought: 超买阈值，高于此值发出 SELL（默认 70）

    Returns:
        信号 Series：1=BUY, -1=SELL, 0=HOLD
    """
    rsi_values = rsi(close, period)

    signal = pd.Series(0, index=close.index, dtype=int)
    signal[rsi_values < oversold]   =  1   # BUY
    signal[rsi_values > overbought] = -1   # SELL

    # ⚠️ shift(1) 避免前视偏差
    return signal.shift(1).fillna(0).astype(int)
