"""通用技术指标函数 — 基于 pandas-ta 0.4.71b0 实现。

对外接口与原版完全相同（函数签名不变），策略文件无需修改。

pandas-ta 列名约定（供内部参考）：
    RSI       → RSI_{length}
    BB upper  → BBU_{length}_{std}_{std}
    BB middle → BBM_{length}_{std}_{std}
    BB lower  → BBL_{length}_{std}_{std}
    MACD line → MACD_{fast}_{slow}_{signal}
    MACD hist → MACDh_{fast}_{slow}_{signal}
    MACD sig  → MACDs_{fast}_{slow}_{signal}
    ATR       → ATRr_{length}

所有函数：
    - 输入 pd.Series（close）或 pd.DataFrame（OHLCV）
    - 输出 pd.Series（指标值）或 tuple[pd.Series, ...]
    - 无副作用，不做 shift（由策略函数负责时移）

环境要求：pandas-ta >= 0.4.71b0（需 Python 3.12+）
"""

from __future__ import annotations

import pandas as pd
import pandas_ta as ta


def sma(series: pd.Series, period: int) -> pd.Series:
    """简单移动平均（Simple Moving Average）。"""
    result = ta.sma(series, length=period)
    if result is None:
        return pd.Series(
            float("nan"), index=series.index, name=series.name, dtype="float64"
        )
    return result.rename(series.name)


def ema(series: pd.Series, period: int) -> pd.Series:
    """指数移动平均（Exponential Moving Average）。"""
    result = ta.ema(series, length=period)
    if result is None:
        return pd.Series(
            float("nan"), index=series.index, name=series.name, dtype="float64"
        )
    return result.rename(series.name)


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """RSI（Relative Strength Index），Wilder 平滑法，返回值 0~100。"""
    return ta.rsi(close, length=period)


def bollinger_bands(
    close: pd.Series,
    period: int = 20,
    std_dev: float = 2.0,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """布林带。

    Returns:
        (upper, middle, lower)
    """
    bb = ta.bbands(close, length=period, std=std_dev)
    if bb is None or not hasattr(bb, "columns"):
        # pandas-ta 在数据不足（len < period）或全 NaN 时返回 None
        raise ValueError(
            f"bbands returned None — data may be too short (len={len(close)}, period={period})"
        )
    # 从 pandas-ta 返回的 DataFrame 中按前缀匹配列名（避免手动拼列名因格式化差异而 KeyError）
    uppers = [c for c in bb.columns if c.startswith("BBU_")]
    middles = [c for c in bb.columns if c.startswith("BBM_")]
    lowers = [c for c in bb.columns if c.startswith("BBL_")]
    if not uppers or not middles or not lowers:
        raise KeyError(
            f"Unexpected BB columns: {list(bb.columns)}. Expected BBU_/BBM_/BBL_ prefixes"
        )
    return bb[uppers[0]], bb[middles[0]], bb[lowers[0]]


def macd(
    close: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal_period: int = 9,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """MACD。

    Returns:
        (macd_line, signal_line, histogram)
    """
    mc = ta.macd(close, fast=fast, slow=slow, signal=signal_period)
    col_macd = f"MACD_{fast}_{slow}_{signal_period}"
    col_hist = f"MACDh_{fast}_{slow}_{signal_period}"
    col_sig  = f"MACDs_{fast}_{slow}_{signal_period}"
    return mc[col_macd], mc[col_sig], mc[col_hist]


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range（平均真实波幅）。

    Args:
        df: 含 high, low, close 列的 DataFrame
    """
    return ta.atr(df["high"], df["low"], df["close"], length=period)


def crossed_above(series_a: pd.Series, series_b: pd.Series) -> pd.Series:
    """series_a 上穿 series_b 时为 True（纯 pandas 实现，无需 pandas-ta）。"""
    return (series_a > series_b) & (series_a.shift(1) <= series_b.shift(1))


def crossed_below(series_a: pd.Series, series_b: pd.Series) -> pd.Series:
    """series_a 下穿 series_b 时为 True（纯 pandas 实现，无需 pandas-ta）。"""
    return (series_a < series_b) & (series_a.shift(1) >= series_b.shift(1))
