"""仓位计算器 — 固定金额法 + ATR 波动率仓位法 + 固定比例法。

所有方法均为纯函数，无副作用。
"""

from __future__ import annotations

import math

import pandas as pd

from mytrader.strategy.indicators import atr as compute_atr


def fixed_amount_size(
    capital: float,
    risk_per_trade: float,
    entry_price: float,
    stop_loss_price: float,
) -> tuple[int, float]:
    """固定金额仓位法。

    用单笔最大亏损金额 = capital * risk_per_trade 除以每股止损距离，
    得到买入股数。

    Args:
        capital:        总资产
        risk_per_trade: 每笔交易风险比例（如 0.01 = 1%）
        entry_price:    入场价
        stop_loss_price: 止损价

    Returns:
        (quantity, risk_amount)
    """
    risk_amount = capital * risk_per_trade
    stop_distance = abs(entry_price - stop_loss_price)
    if stop_distance <= 0 or entry_price <= 0:
        return 0, 0.0
    quantity = int(risk_amount / stop_distance)
    return quantity, risk_amount


def atr_position_size(
    capital: float,
    risk_per_trade: float,
    entry_price: float,
    df: pd.DataFrame,
    atr_period: int = 14,
    atr_multiplier: float = 2.0,
) -> tuple[int, float, float]:
    """ATR 波动率仓位法。

    止损距离 = ATR * atr_multiplier，以此反推买入股数。

    Args:
        capital:         总资产
        risk_per_trade:  每笔交易风险比例（如 0.01 = 1%）
        entry_price:     入场价
        df:              含 high/low/close 的 DataFrame
        atr_period:      ATR 计算周期（默认 14）
        atr_multiplier:  ATR 倍数（默认 2.0）

    Returns:
        (quantity, risk_amount, stop_loss_price)
    """
    atr_series = compute_atr(df, period=atr_period)
    if atr_series.empty or atr_series.isna().all():
        return 0, 0.0, entry_price * 0.98

    atr_val = float(atr_series.iloc[-1])
    if math.isnan(atr_val) or atr_val <= 0:
        return 0, 0.0, entry_price * 0.98

    stop_distance = atr_val * atr_multiplier
    stop_loss_price = entry_price - stop_distance

    risk_amount = capital * risk_per_trade
    quantity = int(risk_amount / stop_distance)

    return quantity, risk_amount, stop_loss_price


def fixed_fraction_size(
    capital: float,
    fraction: float,
    entry_price: float,
) -> tuple[int, float]:
    """固定比例仓位法（Kelly 简化版）。

    Args:
        capital:     总资产
        fraction:    仓位占总资产比例（如 0.10 = 10%）
        entry_price: 入场价

    Returns:
        (quantity, position_value)
    """
    if entry_price <= 0:
        return 0, 0.0
    position_value = capital * fraction
    quantity = int(position_value / entry_price)
    return quantity, position_value
