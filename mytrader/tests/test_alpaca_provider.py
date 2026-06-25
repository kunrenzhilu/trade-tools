"""AlpacaDataProvider 单元测试（Mock alpaca-py，无需真实 API）。

覆盖点：
- get_ohlcv：正常流程（Mock client）
- get_ohlcv：空数据返回空 DataFrame
- get_ohlcv：缓存命中（不调用 client）
- get_ohlcv：不支持的 timeframe 抛 ValueError
- get_ohlcv：client 抛异常返回空 DataFrame
- get_latest_bar：正常返回最新 Series
- get_latest_bar：空数据抛 RuntimeError
- _bars_to_dataframe：MultiIndex DataFrame
- _bars_to_dataframe：单标的 DataFrame
- _bars_to_dataframe：Mock DataFrame 直接传入
- _bars_to_dataframe：None 输入
- 不同 timeframe 映射正确
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from mytrader.data.providers.alpaca_provider import AlpacaDataProvider


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_ohlcv_df(n: int = 10, symbol: str = "AAPL") -> pd.DataFrame:
    """创建一个标准 OHLCV DataFrame（UTC DatetimeIndex）。"""
    idx = pd.date_range(
        start="2024-01-02", periods=n, freq="B", tz="UTC", name="timestamp"
    )
    return pd.DataFrame(
        {
            "open":   [100.0 + i for i in range(n)],
            "high":   [105.0 + i for i in range(n)],
            "low":    [98.0 + i for i in range(n)],
            "close":  [103.0 + i for i in range(n)],
            "volume": [1_000_000 + i * 1000 for i in range(n)],
        },
        index=idx,
    )


def _make_multiindex_df(symbol: str = "AAPL", n: int = 5) -> pd.DataFrame:
    """创建 Alpaca 风格的 MultiIndex DataFrame (symbol, timestamp)。"""
    idx = pd.date_range(
        start="2024-03-01", periods=n, freq="B", tz="UTC", name="timestamp"
    )
    multi_idx = pd.MultiIndex.from_product(
        [[symbol], idx], names=["symbol", "timestamp"]
    )
    return pd.DataFrame(
        {
            "open":  [150.0 + i for i in range(n)],
            "high":  [155.0 + i for i in range(n)],
            "low":   [148.0 + i for i in range(n)],
            "close": [153.0 + i for i in range(n)],
            "volume": [500_000 + i * 1000 for i in range(n)],
        },
        index=multi_idx,
    )


@pytest.fixture
def mock_bars_response():
    """模拟 Alpaca BarDataset 响应（有 .df 属性）。"""
    df = _make_ohlcv_df(10)
    bars = MagicMock()
    bars.df = df
    return bars


@pytest.fixture
def tmp_cache(tmp_path):
    """使用临时目录的 DataCache，每个测试隔离，避免缓存交叉污染。"""
    from mytrader.data.cache import DataCache
    return DataCache(cache_dir=str(tmp_path / "cache"))


@pytest.fixture
def provider_with_mock_client(mock_bars_response, tmp_cache):
    """注入 Mock client 的 AlpacaDataProvider（不发真实请求）。"""
    mock_client = MagicMock()
    mock_client.get_stock_bars.return_value = mock_bars_response

    return AlpacaDataProvider(
        api_key="test_key",
        secret_key="test_secret",
        cache=tmp_cache,
        data_client=mock_client,
    )


# ---------------------------------------------------------------------------
# get_ohlcv 正常流程
# ---------------------------------------------------------------------------

class TestGetOHLCV:
    def test_returns_ohlcv_dataframe(self, provider_with_mock_client):
        """正常返回包含 OHLCV 列的 DataFrame。"""
        df = provider_with_mock_client.get_ohlcv(
            "AAPL",
            date(2024, 1, 2),
            date(2024, 1, 31),
        )
        assert not df.empty
        assert set(["open", "high", "low", "close", "volume"]).issubset(df.columns)

    def test_index_is_utc_datetimeindex(self, provider_with_mock_client):
        """索引必须是 UTC DatetimeIndex。"""
        df = provider_with_mock_client.get_ohlcv(
            "AAPL",
            date(2024, 1, 2),
            date(2024, 1, 31),
        )
        assert isinstance(df.index, pd.DatetimeIndex)
        assert df.index.tz is not None
        assert str(df.index.tz) == "UTC"

    def test_cache_hit_skips_client(self, provider_with_mock_client):
        """缓存命中时不再调用 client。"""
        start = date(2024, 1, 2)
        end = date(2024, 1, 31)
        # 第一次 —— miss
        provider_with_mock_client.get_ohlcv("AAPL", start, end)
        call_count_after_first = (
            provider_with_mock_client._data_client.get_stock_bars.call_count
        )
        # 第二次 —— hit（相同参数）
        provider_with_mock_client.get_ohlcv("AAPL", start, end)
        call_count_after_second = (
            provider_with_mock_client._data_client.get_stock_bars.call_count
        )
        assert call_count_after_second == call_count_after_first

    def test_unsupported_timeframe_raises(self, provider_with_mock_client):
        """不支持的 timeframe 抛 ValueError。"""
        with pytest.raises(ValueError, match="Unsupported timeframe"):
            provider_with_mock_client.get_ohlcv(
                "AAPL", date(2024, 1, 2), date(2024, 1, 31), timeframe="3m"
            )

    def test_empty_response_returns_empty_df(self, tmp_path):
        """客户端返回空 BarDataset 时，返回空 DataFrame（含列名）。"""
        from mytrader.data.cache import DataCache
        mock_client = MagicMock()
        empty_bars = MagicMock()
        empty_bars.df = pd.DataFrame()
        mock_client.get_stock_bars.return_value = empty_bars

        provider = AlpacaDataProvider(
            data_client=mock_client,
            cache=DataCache(cache_dir=str(tmp_path / "cache")),
        )
        df = provider.get_ohlcv("AAPL", date(2024, 1, 2), date(2024, 1, 31))

        assert df.empty
        assert "close" in df.columns

    def test_client_exception_returns_empty_df(self, tmp_path):
        """客户端抛出异常时，返回空 DataFrame（不传播异常）。"""
        from mytrader.data.cache import DataCache
        mock_client = MagicMock()
        mock_client.get_stock_bars.side_effect = ConnectionError("API error")

        provider = AlpacaDataProvider(
            data_client=mock_client,
            cache=DataCache(cache_dir=str(tmp_path / "cache")),
        )
        df = provider.get_ohlcv("AAPL", date(2024, 1, 2), date(2024, 1, 31))

        assert df.empty

    def test_different_timeframes_accepted(self, provider_with_mock_client):
        """所有支持的 timeframe 均不抛出异常。"""
        for tf in ["1m", "5m", "15m", "30m", "1h", "1d"]:
            df = provider_with_mock_client.get_ohlcv(
                "AAPL", date(2024, 1, 2), date(2024, 1, 5), timeframe=tf
            )
            assert isinstance(df, pd.DataFrame)


# ---------------------------------------------------------------------------
# get_latest_bar
# ---------------------------------------------------------------------------

class TestGetLatestBar:
    def test_returns_series_with_ohlcv(self, provider_with_mock_client):
        """返回的 Series 包含 close 字段。"""
        bar = provider_with_mock_client.get_latest_bar("AAPL")
        assert "close" in bar.index

    def test_empty_data_raises_runtime_error(self, tmp_path):
        """无数据时抛 RuntimeError。"""
        from mytrader.data.cache import DataCache
        mock_client = MagicMock()
        empty_bars = MagicMock()
        empty_bars.df = pd.DataFrame()
        mock_client.get_stock_bars.return_value = empty_bars

        provider = AlpacaDataProvider(
            data_client=mock_client,
            cache=DataCache(cache_dir=str(tmp_path / "cache")),
        )
        with pytest.raises(RuntimeError, match="cannot get latest bar"):
            provider.get_latest_bar("AAPL")


# ---------------------------------------------------------------------------
# _bars_to_dataframe 内部方法
# ---------------------------------------------------------------------------

class TestBarsToDataframe:
    def test_none_input_returns_none(self):
        provider = AlpacaDataProvider(data_client=MagicMock())
        result = provider._bars_to_dataframe(None, "AAPL")
        assert result is None

    def test_dataframe_passthrough(self):
        """直接传入 DataFrame（Mock 注入的情况）时正确处理。"""
        provider = AlpacaDataProvider(data_client=MagicMock())
        df = _make_ohlcv_df(5)
        result = provider._bars_to_dataframe(df, "AAPL")
        assert result is not None
        assert not result.empty
        assert "close" in result.columns

    def test_multiindex_dataframe(self):
        """MultiIndex DataFrame（(symbol, timestamp)）正确展开。"""
        provider = AlpacaDataProvider(data_client=MagicMock())
        multi_df = _make_multiindex_df("AAPL", 5)

        bars = MagicMock()
        bars.df = multi_df

        result = provider._bars_to_dataframe(bars, "AAPL")
        assert result is not None
        assert not isinstance(result.index, pd.MultiIndex)
        assert "close" in result.columns

    def test_utc_timezone_enforced(self):
        """结果 DataFrame 索引必须是 UTC DatetimeIndex。"""
        provider = AlpacaDataProvider(data_client=MagicMock())
        df = _make_ohlcv_df(5)
        result = provider._bars_to_dataframe(df, "AAPL")
        assert str(result.index.tz) == "UTC"

    def test_non_utc_tz_converted(self):
        """非 UTC 时区的 DatetimeIndex 被转换为 UTC。"""
        provider = AlpacaDataProvider(data_client=MagicMock())
        df = _make_ohlcv_df(5)
        # 改为 ET 时区
        df.index = df.index.tz_convert("America/New_York")

        result = provider._bars_to_dataframe(df, "AAPL")
        assert str(result.index.tz) == "UTC"
