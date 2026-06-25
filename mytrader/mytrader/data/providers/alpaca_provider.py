"""AlpacaDataProvider — 基于 Alpaca Market Data API v2 的数据源。

数据端点：
    - 日线/多分钟级：/v2/stocks/{symbol}/bars（SIP feed，免费，15min 延迟）
    - 最新一根 Bar：  /v2/stocks/{symbol}/bars/latest

特点：
    - 与 YFinanceProvider 实现相同的 DataProvider Protocol
    - 内置本地 Parquet 缓存，与 YFinance 缓存路径隔离（provider="alpaca"）
    - 支持 timeframe：1m, 5m, 15m, 30m, 1h, 1d
    - 测试友好：data_client 可外部注入（Mock），无需真实 API
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

import pandas as pd
from loguru import logger

from mytrader.data.base import OHLCVFrame
from mytrader.data.cache import DataCache
from mytrader.data.cleaner import clean_ohlcv
from mytrader.data.validator import validate_ohlcv


# Alpaca timeframe 映射（alpaca-py TimeFrame）
_TF_MAP = {
    "1m":  ("Minute", 1),
    "5m":  ("Minute", 5),
    "15m": ("Minute", 15),
    "30m": ("Minute", 30),
    "1h":  ("Hour", 1),
    "1d":  ("Day", 1),
}

# Alpaca 免费 Feed（SIP=全量，15min 延迟；IEX=免费实时但覆盖较少）
_DEFAULT_FEED = "sip"


class AlpacaDataProvider:
    """基于 Alpaca Market Data API v2 的 OHLCV 数据源。

    Args:
        api_key:     Alpaca API Key（空字符串时尝试环境变量）
        secret_key:  Alpaca Secret Key
        paper:       True=沙盒（paper trading key）；False=真实账户
        feed:        "sip"（默认，免费全量，15min 延迟）或 "iex"
        cache:       DataCache 实例（None=使用默认）
        data_client: 可注入的 StockHistoricalDataClient（测试用 Mock）
    """

    PROVIDER_NAME = "alpaca"

    def __init__(
        self,
        api_key: str = "",
        secret_key: str = "",
        paper: bool = True,
        feed: str = _DEFAULT_FEED,
        cache: DataCache | None = None,
        data_client: Any | None = None,
    ) -> None:
        self._api_key = api_key
        self._secret_key = secret_key
        self._paper = paper
        self._feed = feed
        self._cache = cache or DataCache()
        self._data_client = data_client  # 延迟初始化

    # ------------------------------------------------------------------
    # Public API（DataProvider Protocol）
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
            symbol:    股票代码，如 "AAPL"（仅支持美股）
            start:     开始日期（含）
            end:       结束日期（含）
            timeframe: "1m","5m","15m","30m","1h","1d"

        Returns:
            清洗后的 OHLCVFrame，索引为 UTC DatetimeIndex
        """
        if timeframe not in _TF_MAP:
            raise ValueError(
                f"Unsupported timeframe: {timeframe}. Supported: {list(_TF_MAP)}"
            )

        # 1. 查缓存
        cached = self._cache.get(self.PROVIDER_NAME, symbol, start, end, timeframe)
        if cached is not None:
            return cached

        # 2. 拉取远程
        logger.info(
            f"[AlpacaProvider] Fetching {symbol} {timeframe} {start}~{end} "
            f"(feed={self._feed})"
        )
        raw = self._fetch_bars(symbol, start, end, timeframe)

        if raw is None or raw.empty:
            logger.warning(
                f"[{symbol}] Alpaca returned empty data for {start}~{end} {timeframe}"
            )
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
        """获取最新一根 K 线（不使用缓存，适用于实盘扫描）。

        Args:
            symbol:    股票代码
            timeframe: K 线周期

        Returns:
            pd.Series，index 包含 open/high/low/close/volume
        """
        today = datetime.now(tz=timezone.utc).date()
        lookback_days = 5 if timeframe == "1d" else 2
        start = today - timedelta(days=lookback_days)

        raw = self._fetch_bars(symbol, start, today, timeframe)
        if raw is None or raw.empty:
            raise RuntimeError(
                f"[{symbol}] Alpaca cannot get latest bar (feed={self._feed})"
            )

        df = clean_ohlcv(raw, symbol=symbol)
        return df.iloc[-1]

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _get_client(self) -> Any:
        """获取或延迟初始化 Alpaca StockHistoricalDataClient。"""
        if self._data_client is not None:
            return self._data_client

        try:
            from alpaca.data.historical import StockHistoricalDataClient
        except ImportError as exc:
            raise ImportError(
                "alpaca-py not installed. Run: pip install alpaca-py"
            ) from exc

        # StockHistoricalDataClient 不区分 paper/live（仅用于行情查询）
        self._data_client = StockHistoricalDataClient(
            api_key=self._api_key or None,
            secret_key=self._secret_key or None,
        )
        return self._data_client

    def _fetch_bars(
        self,
        symbol: str,
        start: date,
        end: date,
        timeframe: str,
    ) -> pd.DataFrame | None:
        """调用 Alpaca /v2/stocks/{symbol}/bars，返回原始 DataFrame。"""
        try:
            from alpaca.data.requests import StockBarsRequest
            from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
        except ImportError as exc:
            raise ImportError(
                "alpaca-py not installed. Run: pip install alpaca-py"
            ) from exc

        tf_unit_name, tf_amount = _TF_MAP[timeframe]

        # 构造 TimeFrame
        unit_map = {
            "Minute": TimeFrameUnit.Minute,
            "Hour":   TimeFrameUnit.Hour,
            "Day":    TimeFrameUnit.Day,
        }
        tf = TimeFrame(tf_amount, unit_map[tf_unit_name])

        # Alpaca end 日期需含当天：设为 end + 1 day 的 00:00 UTC
        start_dt = datetime.combine(start, datetime.min.time()).replace(
            tzinfo=timezone.utc
        )
        end_dt = datetime.combine(
            end + timedelta(days=1), datetime.min.time()
        ).replace(tzinfo=timezone.utc)

        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=tf,
            start=start_dt,
            end=end_dt,
            feed=self._feed,
            adjustment="all",  # 复权：split + dividend
        )

        try:
            client = self._get_client()
            bars = client.get_stock_bars(request)
        except Exception as exc:
            logger.error(f"[{symbol}] Alpaca get_stock_bars failed: {exc}")
            return None

        return self._bars_to_dataframe(bars, symbol)

    def _bars_to_dataframe(self, bars: Any, symbol: str) -> pd.DataFrame | None:
        """将 Alpaca BarSet / DataFrame 转换为统一 OHLCV DataFrame。

        alpaca-py get_stock_bars 返回 BarDataset，可通过 .df 属性
        转成 MultiIndex DataFrame：(symbol, timestamp) → OHLCV 列。
        """
        if bars is None:
            return None

        try:
            # 方式 1：BarDataset 有 .df 属性（alpaca-py >= 0.8）
            df = bars.df
        except AttributeError:
            # 方式 2：注入的 Mock 直接是 DataFrame
            if isinstance(bars, pd.DataFrame):
                df = bars
            else:
                logger.warning(f"[{symbol}] Unknown bars type: {type(bars)}")
                return None

        if df is None or df.empty:
            return None

        # MultiIndex → 单 symbol
        if isinstance(df.index, pd.MultiIndex):
            if symbol in df.index.get_level_values(0):
                df = df.loc[symbol]
            else:
                # 取第一个 symbol
                first_sym = df.index.get_level_values(0)[0]
                df = df.loc[first_sym]

        # 列名标准化（Alpaca 用 open/high/low/close/volume，与约定一致）
        df = df.rename(
            columns={
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "volume": "volume",
                "vwap": "vwap",
                "trade_count": "trade_count",
            }
        )

        # 保留标准 OHLCV 列（忽略 vwap/trade_count）
        cols = [c for c in ["open", "high", "low", "close", "volume"] if c in df.columns]
        df = df[cols].copy()

        # 确保索引为 UTC DatetimeIndex
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index, utc=True)
        elif df.index.tz is None:
            df.index = df.index.tz_localize("UTC")
        else:
            df.index = df.index.tz_convert("UTC")

        df.index.name = "timestamp"
        return df
