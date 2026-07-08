"""Rate of Change 动量策略（Momentum — Rate of Change）。

信号规则：
    - BUY:  RoC > buy_threshold AND close > SMA(trend_period) → 强动量 + 上升趋势 → +1
    - SELL: RoC < sell_threshold OR close < SMA(trend_period) → 动量反转 OR 趋势破位 → -1

设计动机：动量（Momentum）是经典的 alpha 来源——"买赢家、卖输家"。
Rate-of-Change (RoC) 是最简单可解释的动量指标，仅用收盘价计算。
加入 SMA(200) 趋势过滤避免在下降趋势中追多（Constitution L3: Hybrid system）。

RoC 公式：RoC = (close - close_shift(period)) / close_shift(period) * 100
"""

from __future__ import annotations

import pandas as pd

from mytrader.strategy.indicators import sma
from mytrader.strategy.registry import register_strategy


@register_strategy("momentum_roc")
def momentum_roc_signal(
    close: pd.Series,
    roc_period: int = 20,
    buy_threshold: float = 5.0,
    sell_threshold: float = -3.0,
    trend_period: int = 200,
) -> pd.Series:
    """Rate of Change 动量信号。

    Args:
        close:          收盘价 Series
        roc_period:     RoC 计算周期（默认 20）
        buy_threshold:  买入 RoC 阈值（%），高于此值视为强动量（默认 5.0）
        sell_threshold: 卖出 RoC 阈值（%），低于此值视为动量反转（默认 -3.0）
        trend_period:   SMA 趋势过滤周期（默认 200）

    Returns:
        信号 Series：1=BUY, -1=SELL, 0=HOLD
    """
    # RoC = (close - close_shift(period)) / close_shift(period) * 100
    roc = (close - close.shift(roc_period)) / close.shift(roc_period) * 100
    trend_ma = sma(close, trend_period)

    above_trend = close > trend_ma
    below_trend = close < trend_ma

    # 入场：强动量 + 上升趋势
    buy_signal = (roc > buy_threshold) & above_trend
    # 出场：动量反转 OR 趋势破位（任一触发即出场）
    sell_roc = roc < sell_threshold
    sell_trend = below_trend

    signal = pd.Series(0, index=close.index, dtype=int)
    signal[buy_signal] = 1
    signal[sell_roc | sell_trend] = -1

    # shift(1) 避免前视偏差：用前一根 K 线的指标值做决策，在当前 K 线开盘时执行
    return signal.shift(1).fillna(0).astype(int)
