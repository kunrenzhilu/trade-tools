"""RSI 趋势过滤均值回归策略（Trend-Filtered Mean Reversion）。

信号规则：
    - RSI < oversold AND close > SMA(200)  → BUY  (+1)  上升趋势中的超卖
    - RSI > overbought AND close < SMA(200) → SELL (-1)  下降趋势中的超买
    - 否则                                → HOLD  (0)

设计动机：经典 RSI 均值回归在震荡市有效，但单边趋势中会频繁逆势。
通过 200 日 SMA 趋势过滤：
    - 上升趋势中只做多（超卖反弹），不做空
    - 下降趋势中只做空（超买回落），不做多
"""

from __future__ import annotations

import pandas as pd

from mytrader.strategy.indicators import rsi, sma
from mytrader.strategy.registry import register_strategy


@register_strategy("rsi_trend_filter")
def rsi_trend_filter_signal(
    close: pd.Series,
    rsi_period: int = 14,
    oversold: float = 30.0,
    overbought: float = 70.0,
    trend_period: int = 200,
) -> pd.Series:
    """RSI 超买超卖信号 + 200 日 SMA 趋势过滤。

    Args:
        close:        收盘价 Series
        rsi_period:   RSI 计算周期（默认 14）
        oversold:     超卖阈值，低于此值发出潜在 BUY（默认 30）
        overbought:   超买阈值，高于此值发出潜在 SELL（默认 70）
        trend_period: SMA 趋势过滤周期（默认 200）

    Returns:
        信号 Series：1=BUY, -1=SELL, 0=HOLD
    """
    rsi_values = rsi(close, rsi_period)
    trend_ma = sma(close, trend_period)

    # 趋势条件
    above_trend = close > trend_ma   # 上升趋势
    below_trend = close < trend_ma   # 下降趋势

    signal = pd.Series(0, index=close.index, dtype=int)
    # BUY: 超卖 (RSI < oversold) 且 上升趋势 (close > SMA)
    signal[(rsi_values < oversold) & above_trend] = 1
    # SELL: 超买 (RSI > overbought) 且 下降趋势 (close < SMA)
    signal[(rsi_values > overbought) & below_trend] = -1

    # shift(1) 避免前视偏差
    # 使用前一根 K 线的指标值做决策，在当前 K 线开盘时执行
    return signal.shift(1).fillna(0).astype(int)
