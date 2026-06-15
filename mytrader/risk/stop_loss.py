"""止损/止盈计算 — 固定止损 + ATR 跟踪止损 + 时间止损。"""

from __future__ import annotations

import pandas as pd

from mytrader.strategy.indicators import atr as compute_atr


def fixed_stop(
    entry_price: float,
    stop_pct: float = 0.02,
    is_long: bool = True,
) -> float:
    """固定百分比止损。

    Args:
        entry_price: 入场价
        stop_pct:    止损幅度（如 0.02 = 2%）
        is_long:     做多为 True，做空为 False

    Returns:
        止损价格
    """
    if is_long:
        return entry_price * (1 - stop_pct)
    return entry_price * (1 + stop_pct)


def fixed_take_profit(
    entry_price: float,
    tp_pct: float = 0.04,
    is_long: bool = True,
) -> float:
    """固定百分比止盈。

    Args:
        entry_price: 入场价
        tp_pct:      止盈幅度（如 0.04 = 4%）
        is_long:     做多为 True，做空为 False

    Returns:
        止盈价格
    """
    if is_long:
        return entry_price * (1 + tp_pct)
    return entry_price * (1 - tp_pct)


def atr_stop(
    entry_price: float,
    df: pd.DataFrame,
    atr_period: int = 14,
    atr_multiplier: float = 2.0,
    is_long: bool = True,
) -> float:
    """ATR 跟踪止损。

    止损距离 = ATR(period) * multiplier。

    Args:
        entry_price:    入场价
        df:             含 high/low/close 的 DataFrame
        atr_period:     ATR 计算周期
        atr_multiplier: ATR 倍数
        is_long:        做多为 True，做空为 False

    Returns:
        止损价格
    """
    atr_series = compute_atr(df, period=atr_period)
    if atr_series.empty or atr_series.isna().all():
        return fixed_stop(entry_price, stop_pct=0.02, is_long=is_long)

    atr_val = float(atr_series.iloc[-1])
    stop_distance = atr_val * atr_multiplier

    if is_long:
        return entry_price - stop_distance
    return entry_price + stop_distance


def time_stop_bars(max_bars: int = 10) -> int:
    """时间止损：持仓超过 max_bars 个 bar 强制平仓。

    返回最大持仓 bar 数（由执行层/策略层检查是否触发）。
    """
    return max_bars
