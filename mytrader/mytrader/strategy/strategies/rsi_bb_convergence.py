"""RSI + Bollinger Band 双确认均值回归策略（RSI + BB Convergence）。

信号规则：
    - BUY entry:  RSI < oversold AND close < lower_bb → 双重超卖确认 → +1
    - SELL entry: RSI > overbought AND close > upper_bb → 双重超买确认 → -1
    - Exit long:  RSI 向上穿越中性 OR close 向上穿越中轨 → SELL (-1)
    - Exit short: RSI 向下穿越中性 OR close 向下穿越中轨 → BUY (+1)

设计动机：单一 RSI 或单一布林带信号假阳性率高。双重确认要求两个独立
均值回归指标同时触发，降低假信号。出场条件也放宽为任一指标回归即出场。
"""

from __future__ import annotations

import pandas as pd

from mytrader.strategy.indicators import (
    rsi,
    bollinger_bands,
    crossed_above,
    crossed_below,
)
from mytrader.strategy.registry import register_strategy


@register_strategy("rsi_bb_convergence")
def rsi_bb_convergence_signal(
    close: pd.Series,
    rsi_period: int = 14,
    oversold: float = 30.0,
    overbought: float = 70.0,
    bb_period: int = 20,
    bb_std: float = 2.0,
    exit_rsi_neutral: float = 50.0,
) -> pd.Series:
    """RSI + Bollinger Band 双确认均值回归信号。

    Args:
        close:            收盘价 Series
        rsi_period:       RSI 计算周期（默认 14）
        oversold:         RSI 超卖阈值（默认 30）
        overbought:       RSI 超买阈值（默认 70）
        bb_period:        布林带周期（默认 20）
        bb_std:           布林带标准差倍数（默认 2.0）
        exit_rsi_neutral: RSI 中性水平，RSI 回归此值时出场（默认 50）

    Returns:
        信号 Series：1=BUY, -1=SELL, 0=HOLD
    """
    rsi_values = rsi(close, rsi_period)
    upper, middle, lower = bollinger_bands(close, period=bb_period, std_dev=bb_std)

    # Entry: 双确认
    buy_entry = (rsi_values < oversold) & (close < lower)
    sell_entry = (rsi_values > overbought) & (close > upper)

    # Exit: 任一条件清除（RSI 回归中性 OR 价格穿越中轨）
    exit_long_rsi = (rsi_values > exit_rsi_neutral) & (rsi_values.shift(1) <= exit_rsi_neutral)
    exit_long_bb = crossed_above(close, middle)
    exit_short_rsi = (rsi_values < exit_rsi_neutral) & (rsi_values.shift(1) >= exit_rsi_neutral)
    exit_short_bb = crossed_below(close, middle)

    signal = pd.Series(0, index=close.index, dtype=int)
    signal[buy_entry] = 1
    signal[sell_entry] = -1
    signal[exit_long_rsi | exit_long_bb] = -1
    signal[exit_short_rsi | exit_short_bb] = 1

    # shift(1) 避免前视偏差
    return signal.shift(1).fillna(0).astype(int)
