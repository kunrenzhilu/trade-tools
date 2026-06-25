"""布林带均值回归策略（Bollinger Band Mean Reversion）。

信号规则（均值回归版本）：
    - 收盘价跌破下轨 → 超跌，BUY  (+1)
    - 收盘价突破上轨 → 超涨，SELL (-1)
    - 否则           → HOLD  (0)

注意：这是均值回归版本（逆势），不是突破版本（顺势）。
      在震荡市有效，趋势市中慎用。
"""

from __future__ import annotations

import pandas as pd

from mytrader.strategy.indicators import bollinger_bands
from mytrader.strategy.registry import register_strategy


@register_strategy("bollinger_band")
def bollinger_signal(
    close: pd.Series,
    period: int = 20,
    std_dev: float = 2.0,
) -> pd.Series:
    """布林带均值回归信号。

    Args:
        close:   收盘价 Series
        period:  布林带计算周期（默认 20）
        std_dev: 标准差倍数（默认 2.0）

    Returns:
        信号 Series：1=BUY, -1=SELL, 0=HOLD
    """
    upper, middle, lower = bollinger_bands(close, period, std_dev)

    signal = pd.Series(0, index=close.index, dtype=int)
    signal[close < lower] =  1   # 跌破下轨 → BUY
    signal[close > upper] = -1   # 突破上轨 → SELL

    # ⚠️ shift(1) 避免前视偏差
    return signal.shift(1).fillna(0).astype(int)
