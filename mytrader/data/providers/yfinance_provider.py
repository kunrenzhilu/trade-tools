"""YFinance 数据源实现。

注意事项：
    - 港股 symbol 格式：0700.HK
    - auto_adjust=True 自动后复权，避免手动处理拆分
    - 日内数据（1m/5m）只能拉最近 7-60 天，超出范围会返回空 DataFrame
    - yfinance 偶尔限速，加了简单的重试
"""

from __future__ import annotations

import time
from datetime import date, datetime, timedelta, timezone

import pandas as pd
import yfinance as yf
from loguru import logger

from mytrader.data.base import OHLCVFrame
from mytrader.data.cache import DataCache
from mytrader.data.cleaner import clean_ohlcv
from mytrader.data.validator import validate_ohlcv

# yfinance timeframe 映射
_TF_MAP = {
    "1m":  "1m",
    "5m":  "5m",
    "15m": "15m",
    "30m": "30m",
    "1h":  "1h",
    "1d":  "1d",
    "1wk": "1wk",
}


class YFinanceProvider:
    """基于 yfinance 的数据提供者，内置本地 Parquet 缓存。"""

    PROVIDER_NAME = "yfinance"

    def __init__(
        self,
        cache: DataCache | None = None,
        max_retries: int = 3,
        retry_delay: float = 2.0,
    ) -> None:
        self._cache = cache or DataCache()
        self._max_retries = max_retries
        self._retry_delay = retry_delay

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_ohlcv(
        self,
        symbol: str,
        start: date,
        end: date,
        timeframe: str = "1d",
    ) -> OHLCVFrame:
        """获取 OHLCV 数据（含缓存）。

        Args:
            symbol:    股票代码，如 "AAPL" 或 "0700.HK"
            start:     开始日期（含）
            end:       结束日期（含）
            timeframe: "1m","5m","15m","1h","1d"

        Returns:
            清洗后的 OHLCVFrame，索引为 UTC DatetimeIndex
        """
        if timeframe not in _TF_MAP:
            raise ValueError(f"Unsupported timeframe: {timeframe}. Supported: {list(_TF_MAP)}")

        # 1. 查缓存
        cached = self._cache.get(self.PROVIDER_NAME, symbol, start, end, timeframe)
        if cached is not None:
            return cached

        # 2. 拉取远程
        logger.info(f"Fetching {symbol} {timeframe} {start}~{end} from yfinance")
        raw = self._fetch_with_retry(symbol, start, end, timeframe)

        if raw is None or raw.empty:
            logger.warning(f"[{symbol}] yfinance returned empty data for {start}~{end} {timeframe}")
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

        # 3. 清洗 + 验证
        df = clean_ohlcv(raw, symbol=symbol)
        report = validate_ohlcv(df, symbol=symbol, timeframe=timeframe)
        if not report.is_ok:
            logger.warning(f"[{symbol}] Data quality issues: {report.issues}")

        # 4. 写缓存
        self._cache.set(self.PROVIDER_NAME, symbol, start, end, timeframe, df)

        return df

    def get_latest_bar(
        self,
        symbol: str,
        timeframe: str = "1d",
    ) -> pd.Series:
        """获取最新一根 K 线（不使用缓存）。"""
        today = datetime.now(tz=timezone.utc).date()
        yesterday = today - timedelta(days=5)  # 取最近 5 天，防止节假日空

        df = self._fetch_with_retry(symbol, yesterday, today, timeframe, use_cache=False)
        if df is None or df.empty:
            raise RuntimeError(f"[{symbol}] Cannot get latest bar")

        df = clean_ohlcv(df, symbol=symbol)
        return df.iloc[-1]

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _fetch_with_retry(
        self,
        symbol: str,
        start: date,
        end: date,
        timeframe: str,
        use_cache: bool = True,
    ) -> pd.DataFrame | None:
        """带重试的 yfinance 数据拉取。"""
        yf_interval = _TF_MAP[timeframe]
        # yfinance end 日期是不含的，所以加 1 天
        end_exclusive = end + timedelta(days=1)

        for attempt in range(1, self._max_retries + 1):
            try:
                ticker = yf.Ticker(symbol)
                df = ticker.history(
                    start=str(start),
                    end=str(end_exclusive),
                    interval=yf_interval,
                    auto_adjust=True,   # 后复权，自动处理拆分
                    back_adjust=False,
                    actions=False,      # 不需要分红/拆股列
                )
                return df
            except Exception as exc:
                logger.warning(f"[{symbol}] yfinance attempt {attempt}/{self._max_retries} failed: {exc}")
                if attempt < self._max_retries:
                    time.sleep(self._retry_delay * attempt)

        return None
