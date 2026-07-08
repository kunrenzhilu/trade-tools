"""ADX 趋势强度 + EMA 交叉确认策略（ADX Trend Strength + EMA Crossover）。

信号规则：
    - BUY:  fast EMA > slow EMA (金叉状态) AND ADX > adx_threshold (强趋势) → +1
    - SELL: fast EMA < slow EMA (死叉) OR ADX < exit_threshold (趋势衰退) → -1

设计动机：纯 EMA 交叉在震荡市频繁假突破。ADX 量化趋势强度，仅在强趋势市
入场，趋势衰退时无条件出场（即使 EMA 未死叉）。这是典型的"趋势跟随 +
强度过滤"双因子设计。

注：BUY 信号要求 EMA 已金叉（fast > slow），而非刚刚穿越。这样信号在
整个趋势期间可持续 HOLD，直到 ADX 衰退或 EMA 死叉才出场。
"""

from __future__ import annotations

import pandas as pd

from mytrader.strategy.indicators import adx, ema
from mytrader.strategy.registry import register_strategy


@register_strategy("adx_trend")
def adx_trend_signal(
    close: pd.Series,
    fast: int = 10,
    slow: int = 30,
    adx_period: int = 14,
    adx_threshold: float = 25.0,
    exit_threshold: float = 20.0,
    df: pd.DataFrame | None = None,
) -> pd.Series:
    """ADX + EMA Crossover 趋势跟随信号。

    Args:
        close:         收盘价 Series
        fast:          快线 EMA 周期（默认 10）
        slow:          慢线 EMA 周期（默认 30）
        adx_period:    ADX 计算周期（默认 14）
        adx_threshold: 入场 ADX 阈值，高于此值视为强趋势（默认 25）
        exit_threshold: 出场 ADX 阈值，低于此值无条件出场（默认 20）
        df:            完整 OHLCV DataFrame（用于读取 high/low 计算 ADX）；
                       None 时退化为纯 EMA 交叉策略

    Returns:
        信号 Series：1=BUY, -1=SELL, 0=HOLD
    """
    fast_ema = ema(close, fast)
    slow_ema = ema(close, slow)

    # EMA 金叉状态（fast > slow，持续条件，非"刚刚穿越"）
    buy_signal = (fast_ema > slow_ema) & (fast_ema.shift(1) <= slow_ema.shift(1))
    sell_cross = (fast_ema < slow_ema) & (fast_ema.shift(1) >= slow_ema.shift(1))

    if df is not None and all(c in df.columns for c in ["high", "low"]):
        adx_series = adx(df["high"], df["low"], close, period=adx_period)
        # ADX 确认入场（仅在强趋势时买入）
        buy_signal = buy_signal & (adx_series > adx_threshold)
        # ADX 衰退时无条件出场（即使 EMA 未死叉，趋势已弱）
        sell_adx = adx_series < exit_threshold
        sell_signal = sell_cross | sell_adx
    else:
        # 无 df 时退化为纯 EMA 交叉（不崩溃，但失去 ADX 过滤）
        sell_signal = sell_cross

    signal = pd.Series(0, index=close.index, dtype=int)
    signal[buy_signal] = 1
    signal[sell_signal] = -1

    # shift(1) 避免前视偏差：用前一根 K 线的指标值做决策，在当前 K 线开盘时执行
    return signal.shift(1).fillna(0).astype(int)
