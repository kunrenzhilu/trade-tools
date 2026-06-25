"""Data layer base types and Protocol."""

from __future__ import annotations

from datetime import date
from typing import Protocol, runtime_checkable

import pandas as pd


# ---------------------------------------------------------------------------
# 类型别名
# ---------------------------------------------------------------------------

# OHLCV DataFrame 约定：
#   - 列名：open, high, low, close, volume（全小写）
#   - 索引：DatetimeIndex，tz-aware UTC
#   - 每行代表一根 K 线
OHLCVFrame = pd.DataFrame

OHLCV_COLUMNS = ["open", "high", "low", "close", "volume"]


# ---------------------------------------------------------------------------
# DataProvider Protocol
# ---------------------------------------------------------------------------

@runtime_checkable
class DataProvider(Protocol):
    """所有数据源必须实现的统一接口。

    Strategy Engine 只依赖此 Protocol，不依赖具体实现，
    方便在不同数据源之间切换或在测试中注入 Mock。
    """

    def get_ohlcv(
        self,
        symbol: str,
        start: date,
        end: date,
        timeframe: str = "1d",
    ) -> OHLCVFrame:
        """获取 OHLCV 历史数据。

        Args:
            symbol:    股票代码（美股如 "AAPL"，港股如 "0700.HK"）
            start:     开始日期（含）
            end:       结束日期（含）
            timeframe: K 线周期，支持 "1m","5m","15m","1h","1d"

        Returns:
            OHLCVFrame — 列：open, high, low, close, volume；索引：UTC DatetimeIndex
        """
        ...

    def get_latest_bar(
        self,
        symbol: str,
        timeframe: str = "1d",
    ) -> pd.Series:
        """获取最新一根 K 线（实盘用）。

        Returns:
            pd.Series，index 为 OHLCV_COLUMNS
        """
        ...
