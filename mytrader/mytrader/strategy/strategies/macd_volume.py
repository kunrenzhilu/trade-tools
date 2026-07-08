"""MACD + 成交量确认策略（MACD + Volume Confirmation）。

信号规则：
    - BUY: MACD 上穿信号线 AND 成交量 > 成交量均线 → 放量确认 → +1
    - SELL: MACD 下穿信号线 → 无需成交量确认（不 trap in losing position）→ -1

设计动机：MACD 交叉信号噪音大，加入成交量确认可过滤低量假突破。
出场不需成交量确认——亏损时必须无条件出场，不被低量困住。
"""

from __future__ import annotations

import pandas as pd

from mytrader.strategy.indicators import macd, sma, crossed_above, crossed_below
from mytrader.strategy.registry import register_strategy


@register_strategy("macd_volume")
def macd_volume_signal(
    close: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal_period: int = 9,
    volume_period: int = 20,
    df: pd.DataFrame | None = None,
) -> pd.Series:
    """MACD 交叉 + 成交量确认信号。

    Args:
        close:         收盘价 Series
        fast:          快线 EMA 周期（默认 12）
        slow:          慢线 EMA 周期（默认 26）
        signal_period: 信号线 EMA 周期（默认 9）
        volume_period: 成交量均线周期（默认 20）
        df:            完整 OHLCV DataFrame（用于读取 volume 列）；
                       None 时退化为纯 MACD 策略

    Returns:
        信号 Series：1=BUY, -1=SELL, 0=HOLD
    """
    macd_line, signal_line, _ = macd(close, fast=fast, slow=slow, signal_period=signal_period)

    buy_signal = crossed_above(macd_line, signal_line)
    sell_signal = crossed_below(macd_line, signal_line)

    # 成交量确认（仅入场需要，出场无条件）
    if df is not None and "volume" in df.columns and len(df) > volume_period:
        volume_ma = sma(df["volume"], period=volume_period)
        vol_confirm = df["volume"] > volume_ma
        buy_signal = buy_signal & vol_confirm

    signal = pd.Series(0, index=close.index, dtype=int)
    signal[buy_signal] = 1
    signal[sell_signal] = -1

    # shift(1) 避免前视偏差
    return signal.shift(1).fillna(0).astype(int)
