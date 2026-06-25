"""OHLCV 数据清洗规则。

规则：
    1. 列名统一小写
    2. 索引转为 UTC tz-aware DatetimeIndex
    3. 去除重复行
    4. 前向填充缺失 K 线（同时标记异常）
    5. 标记价格异常值（单 bar 涨跌 > 50%）
    6. 标记成交量为 0 的 bar（流动性不足）
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from loguru import logger


def clean_ohlcv(df: pd.DataFrame, symbol: str = "") -> pd.DataFrame:
    """对原始 OHLCV DataFrame 做标准化清洗。

    Args:
        df:      从数据源拿到的原始 DataFrame
        symbol:  股票代码（仅用于日志）

    Returns:
        清洗后的 DataFrame，含额外列：
            - is_suspect (bool)：价格异常 bar
            - is_low_liquidity (bool)：成交量为 0 的 bar
    """
    if df is None or df.empty:
        logger.warning(f"[{symbol}] Received empty DataFrame, skipping clean")
        return df

    df = df.copy()

    # 1. 列名统一小写
    df.columns = [c.lower() for c in df.columns]

    # 确保必要列存在
    required = {"open", "high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"[{symbol}] Missing columns: {missing}")

    # 2. 索引转 UTC
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    else:
        df.index = df.index.tz_convert("UTC")
    df.index.name = "datetime"

    # 3. 按时间排序，去除重复行
    df = df.sort_index()
    dup_count = df.index.duplicated().sum()
    if dup_count:
        logger.warning(f"[{symbol}] Dropping {dup_count} duplicate index rows")
        df = df[~df.index.duplicated(keep="last")]

    # 4. 前向填充 NaN（节假日/缺失 bar）
    nan_before = df[["close"]].isna().sum().sum()
    df = df.ffill()
    if nan_before:
        logger.warning(f"[{symbol}] Forward-filled {nan_before} NaN close values")

    # 5. 标记价格异常值（涨跌 > 50%）
    pct_change = df["close"].pct_change().abs()
    df["is_suspect"] = pct_change > 0.50
    suspect_count = df["is_suspect"].sum()
    if suspect_count:
        logger.warning(f"[{symbol}] {suspect_count} suspect bars (price change > 50%)")

    # 6. 标记低流动性 bar（成交量为 0）
    df["is_low_liquidity"] = df["volume"] == 0

    return df
