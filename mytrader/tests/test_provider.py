"""Tests for YFinanceProvider — 数据源功能测试。

使用 mock 隔离，不发起真实网络请求。

测试范围（P1）：
    P1  test_conforms_to_protocol        P1  YFinanceProvider 符合 DataProvider Protocol
    P2  test_unsupported_timeframe_raises P1  不支持的时间周期抛 ValueError
    P3  test_cache_hit_returns_cached     P1  缓存命中时跳过网络请求
    P4  test_cache_miss_fetches_and_caches P1  缓存未命中时拉取并写入缓存
    P5  test_empty_response_returns_empty_df P1  yfinance 返回空数据降级
    P6  test_retry_on_failure             P1  网络异常后自动重试
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from unittest import mock

import numpy as np
import pandas as pd
import pytest

from mytrader.data.base import DataProvider, OHLCVFrame
from mytrader.data.cache import DataCache
from mytrader.data.providers.yfinance_provider import YFinanceProvider


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_ohlcv(n: int = 30) -> pd.DataFrame:
    """生成模拟 yfinance 格式的 OHLCV DataFrame。"""
    idx = pd.date_range("2023-01-03", periods=n, freq="B", tz="UTC")
    close = pd.Series(100.0 + np.random.RandomState(0).randn(n).cumsum(), index=idx)
    return pd.DataFrame({
        "Open":   close * (1 + np.random.RandomState(1).uniform(-0.005, 0.005, n)),
        "High":   close * (1 + np.random.RandomState(2).uniform(0, 0.015, n)),
        "Low":    close * (1 - np.random.RandomState(3).uniform(0, 0.015, n)),
        "Close":  close,
        "Volume": np.random.RandomState(4).randint(1_000_000, 10_000_000, n).astype(float),
    }, index=idx)


# ---------------------------------------------------------------------------
# P1 类型/接口
# ---------------------------------------------------------------------------

class TestProviderProtocol:
    """P1: YFinanceProvider 符合 DataProvider Protocol。"""

    def test_conforms_to_protocol(self):
        """P1: isinstance 检查通过。"""
        provider = YFinanceProvider()
        assert isinstance(provider, DataProvider)


# ---------------------------------------------------------------------------
# P1 参数校验
# ---------------------------------------------------------------------------

class TestProviderValidation:
    """P2: 不支持的时间周期抛 ValueError。"""

    def test_unsupported_timeframe_raises(self):
        """P2: timeframe='3m' 不支持。"""
        provider = YFinanceProvider()
        with pytest.raises(ValueError, match="Unsupported timeframe"):
            provider.get_ohlcv("AAPL", date(2023, 1, 1), date(2023, 2, 1), timeframe="3m")


# ---------------------------------------------------------------------------
# P1 缓存命中/未命中
# ---------------------------------------------------------------------------

class TestProviderCache:
    """P3, P4: 缓存集成行为。"""

    @pytest.fixture(autouse=True)
    def _isolated_cache(self, tmp_path):
        """每个测试使用独立的缓存目录。"""
        self._cache_dir = str(tmp_path / "cache")

    def test_cache_hit_returns_cached(self):
        """P3: 缓存命中时跳过网络请求，返回缓存数据。"""
        cache = DataCache(cache_dir=self._cache_dir)
        df = _make_mock_ohlcv()
        # 直接写入缓存
        cache.set("yfinance", "AAPL", date(2023, 1, 1), date(2023, 2, 1), "1d", df)

        provider = YFinanceProvider(cache=cache)
        # 应命中缓存，不调用 yfinance
        with mock.patch("yfinance.Ticker") as mock_ticker:
            result = provider.get_ohlcv("AAPL", date(2023, 1, 1), date(2023, 2, 1), "1d")
            mock_ticker.assert_not_called()

        assert result is not None
        assert len(result) == len(df)

    def test_cache_miss_fetches_and_caches(self):
        """P4: 缓存未命中时拉取 yfinance 并写入缓存。"""
        cache = DataCache(cache_dir=self._cache_dir)
        df_fake = _make_mock_ohlcv()

        mock_ticker_instance = mock.MagicMock()
        mock_ticker_instance.history.return_value = df_fake

        provider = YFinanceProvider(cache=cache)
        with mock.patch("yfinance.Ticker", return_value=mock_ticker_instance):
            result = provider.get_ohlcv("AAPL", date(2023, 1, 1), date(2023, 2, 1), "1d")

        assert result is not None
        # 验证缓存已写入
        cached = cache.get("yfinance", "AAPL", date(2023, 1, 1), date(2023, 2, 1), "1d")
        assert cached is not None


# ---------------------------------------------------------------------------
# P1 异常和降级
# ---------------------------------------------------------------------------

class TestProviderErrorHandling:
    """P5, P6: 异常响应和重试。"""

    @pytest.fixture(autouse=True)
    def _isolated_cache(self, tmp_path):
        """每个测试使用独立的缓存目录。"""
        self._cache_dir = str(tmp_path / "cache")

    def test_empty_response_returns_empty_df(self):
        """P5: yfinance 返回空数据时返回含 OHLCV 列的空 DataFrame。"""
        mock_ticker = mock.MagicMock()
        mock_ticker.history.return_value = pd.DataFrame()

        cache = DataCache(cache_dir=self._cache_dir)
        provider = YFinanceProvider(cache=cache)
        with mock.patch("yfinance.Ticker", return_value=mock_ticker):
            result = provider.get_ohlcv("AAPL", date(2023, 1, 1), date(2023, 2, 1), "1d")

        assert result is not None
        expected_cols = {"open", "high", "low", "close", "volume"}
        assert expected_cols.issubset(set(result.columns))
        assert result.empty

    def test_retry_on_failure(self):
        """P6: 前 2 次抛异常，第 3 次成功时返回数据。"""
        df_fake = _make_mock_ohlcv()

        # 前 2 次异常，第 3 次正常
        mock_history = mock.MagicMock()
        mock_history.side_effect = [
            RuntimeError("network error"),
            RuntimeError("network error"),
            df_fake,
        ]

        mock_ticker = mock.MagicMock()
        mock_ticker.history = mock_history

        cache = DataCache(cache_dir=self._cache_dir)
        provider = YFinanceProvider(cache=cache, max_retries=3, retry_delay=0.01)
        with mock.patch("yfinance.Ticker", return_value=mock_ticker):
            result = provider.get_ohlcv("AAPL", date(2023, 1, 1), date(2023, 2, 1), "1d")

        assert result is not None
        assert len(result) == len(df_fake)
        assert mock_history.call_count == 3, f"expected 3 calls, got {mock_history.call_count}"
