"""RSI 趋势过滤均值回归策略（Trend-Filtered Mean Reversion）。

迭代 #14 修复：entry 用趋势过滤，exit 用 RSI 回归中性（exit_neutral）。
- 迭代 #8 原版：entry 和 exit 都用趋势方向 → 互斥，0 closed_trades（退化）
- 迭代 #14：entry 用趋势过滤，exit 用 RSI 回归中性 → 自然闭环

信号规则：
    - BUY entry:  RSI < oversold AND close > SMA(trend_period)  → +1
    - SELL entry: RSI > overbought AND close < SMA(trend_period) → -1
    - Exit long:  RSI 向上穿越 exit_neutral → SELL (-1)
    - Exit short: RSI 向下穿越 exit_neutral → BUY (+1)

设计动机：经典 RSI 均值回归在震荡市有效，但单边趋势中会频繁逆势。
通过 SMA 趋势过滤入场方向，出场用 RSI 回归中性实现自然闭环。
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
    exit_neutral: float = 50.0,
) -> pd.Series:
    """RSI 超买超卖信号 + 趋势过滤入场 + RSI 回归中性出场。

    Args:
        close:        收盘价 Series
        rsi_period:   RSI 计算周期（默认 14）
        oversold:     超卖阈值，低于此值发出潜在 BUY（默认 30）
        overbought:   超买阈值，高于此值发出潜在 SELL（默认 70）
        trend_period: SMA 趋势过滤周期（默认 200）
        exit_neutral: RSI 中性水平，RSI 回归此值时出场（默认 50）

    Returns:
        信号 Series：1=BUY, -1=SELL, 0=HOLD
    """
    rsi_values = rsi(close, rsi_period)
    trend_ma = sma(close, trend_period)

    # Entry: 趋势过滤（仅在趋势方向一致时入场）
    above_trend = close > trend_ma   # 上升趋势
    below_trend = close < trend_ma   # 下降趋势
    buy_entry = (rsi_values < oversold) & above_trend
    sell_entry = (rsi_values > overbought) & below_trend

    # Exit: RSI 回归中性（不检查趋势，自然均值回归出场）
    exit_long = (rsi_values > exit_neutral) & (rsi_values.shift(1) <= exit_neutral)
    exit_short = (rsi_values < exit_neutral) & (rsi_values.shift(1) >= exit_neutral)

    signal = pd.Series(0, index=close.index, dtype=int)
    signal[buy_entry] = 1
    signal[sell_entry] = -1
    signal[exit_long] = -1   # SELL to exit long
    signal[exit_short] = 1  # BUY to exit short

    # shift(1) 避免前视偏差：用前一根 K 线的指标值做决策，在当前 K 线开盘时执行
    return signal.shift(1).fillna(0).astype(int)
