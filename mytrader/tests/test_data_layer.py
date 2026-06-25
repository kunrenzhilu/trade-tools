"""Tests for data layer."""

from __future__ import annotations

from datetime import date, datetime, timezone

import numpy as np
import pandas as pd
import pytest

from mytrader.data.cleaner import clean_ohlcv
from mytrader.data.validator import validate_ohlcv


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_ohlcv(n: int = 50, base_price: float = 100.0) -> pd.DataFrame:
    """生成合法的测试 OHLCV DataFrame。"""
    idx = pd.date_range("2023-01-01", periods=n, freq="B", tz="UTC")
    close = pd.Series(base_price + np.random.randn(n).cumsum(), index=idx)
    open_ = close * (1 + np.random.uniform(-0.005, 0.005, n))
    high  = pd.concat([close, open_], axis=1).max(axis=1) * (1 + np.random.uniform(0, 0.01, n))
    low   = pd.concat([close, open_], axis=1).min(axis=1) * (1 - np.random.uniform(0, 0.01, n))

    return pd.DataFrame({
        "Open":   open_,
        "High":   high,
        "Low":    low,
        "Close":  close,
        "Volume": np.random.randint(1_000_000, 10_000_000, n).astype(float),
    }, index=idx)


# ---------------------------------------------------------------------------
# cleaner 测试
# ---------------------------------------------------------------------------

class TestCleanOHLCV:
    def test_columns_lowercased(self):
        df = make_ohlcv()
        result = clean_ohlcv(df)
        assert set(result.columns) >= {"open", "high", "low", "close", "volume"}

    def test_index_is_utc(self):
        df = make_ohlcv()
        result = clean_ohlcv(df)
        assert result.index.tz is not None
        assert str(result.index.tz) == "UTC"

    def test_sorted_index(self):
        df = make_ohlcv().iloc[::-1]  # 倒序
        result = clean_ohlcv(df)
        assert result.index.is_monotonic_increasing

    def test_duplicate_rows_removed(self):
        df = make_ohlcv(20)
        df = pd.concat([df, df.iloc[:5]])  # 加入重复行
        result = clean_ohlcv(df)
        assert not result.index.duplicated().any()

    def test_nan_forward_filled(self):
        df = make_ohlcv(20)
        df = clean_ohlcv(df)  # 先清洗确保列名正确
        df.loc[df.index[5], "close"] = np.nan
        # 重新清洗
        result = clean_ohlcv(df)
        assert result["close"].isna().sum() == 0

    def test_suspect_flag_on_large_move(self):
        df = make_ohlcv(20)
        df_clean = clean_ohlcv(df)
        # 手动制造一个 >50% 的单日涨幅
        df_clean.loc[df_clean.index[10], "close"] = df_clean["close"].iloc[9] * 2.0
        result = clean_ohlcv(df_clean)
        assert result["is_suspect"].sum() >= 1

    def test_low_liquidity_flag(self):
        df = make_ohlcv(20)
        df_clean = clean_ohlcv(df)
        df_clean.loc[df_clean.index[3], "volume"] = 0
        result = clean_ohlcv(df_clean)
        assert result["is_low_liquidity"].sum() >= 1

    def test_empty_input_returns_empty(self):
        result = clean_ohlcv(pd.DataFrame(), symbol="TEST")
        assert result is not None


# ---------------------------------------------------------------------------
# validator 测试
# ---------------------------------------------------------------------------

class TestValidateOHLCV:
    def test_valid_data_is_ok(self):
        df = clean_ohlcv(make_ohlcv(50))
        report = validate_ohlcv(df, symbol="TEST")
        assert report.is_ok
        assert report.total_rows == 50

    def test_empty_dataframe_fails(self):
        report = validate_ohlcv(pd.DataFrame(), symbol="TEST")
        assert not report.is_ok
        assert "empty_dataframe" in report.issues

    def test_too_few_rows(self):
        df = clean_ohlcv(make_ohlcv(5))
        report = validate_ohlcv(df, symbol="TEST", min_rows=10)
        assert not report.is_ok
        assert any("too_few_rows" in i for i in report.issues)

    def test_non_positive_price_detected(self):
        df = clean_ohlcv(make_ohlcv(20))
        df.loc[df.index[2], "close"] = -1.0
        report = validate_ohlcv(df, symbol="TEST")
        assert not report.is_ok


# ---------------------------------------------------------------------------
# cleaner 补充测试（P0-P1）
# ---------------------------------------------------------------------------

class TestCleanOHLCVEdgeCases:
    """cleaner 边界条件和异常路径测试。"""

    def test_none_input_returns_none(self):
        """C1: df=None 返回原值。"""
        result = clean_ohlcv(None)
        assert result is None

    def test_missing_columns_raises(self):
        """C2: 缺少 OHLCV 列时抛出 ValueError。"""
        idx = pd.date_range("2023-01-01", periods=5, freq="B", tz="UTC")
        df = pd.DataFrame({"close": [100.0] * 5, "volume": [1e6] * 5}, index=idx)
        with pytest.raises(ValueError, match="Missing columns"):
            clean_ohlcv(df, symbol="TEST")

    def test_non_datetime_index_converted(self):
        """C3: 非 DatetimeIndex 应被转换为 UTC DatetimeIndex。"""
        df = pd.DataFrame(
            {c: [100.0, 101.0, 102.0] for c in ["open", "high", "low", "close", "volume"]},
            index=[0, 1, 2],
        )
        result = clean_ohlcv(df, symbol="TEST")
        assert isinstance(result.index, pd.DatetimeIndex)
        assert result.index.tz is not None
        assert str(result.index.tz) == "UTC"

    def test_non_utc_tz_converted(self):
        """C4: 非 UTC 时区应转换为 UTC。"""
        idx = pd.date_range("2023-01-01", periods=5, freq="B", tz="Asia/Shanghai")
        df = make_ohlcv(5)
        df.index = idx
        result = clean_ohlcv(df, symbol="TEST")
        assert str(result.index.tz) == "UTC"


# ---------------------------------------------------------------------------
# validator 补充测试（P0-P1）
# ---------------------------------------------------------------------------

class TestValidateOHLCVEdgeCases:
    """validator 边界条件和异常路径测试。"""

    def test_high_suspect_rate(self):
        """V1: 嫌疑 bar 比例 >1% 时触发 is_ok=False。"""
        df = make_ohlcv(100)
        # 先清洗 → 再制造异常 → 再清洗（重新标记 is_suspect）
        df = clean_ohlcv(df)
        df.loc[df.index[10], "close"] = df["close"].iloc[9] * 2.0
        df.loc[df.index[20], "close"] = df["close"].iloc[19] * 0.4
        df = clean_ohlcv(df)  # 重新清洗以更新 is_suspect
        report = validate_ohlcv(df, symbol="TEST")
        assert not report.is_ok
        assert any("high_suspect_rate" in i for i in report.issues)
        assert report.suspect_bars >= 2

    def test_price_ohlc_violation(self):
        """V2: OHLC 价格逻辑违反被检测。"""
        idx = pd.date_range("2023-01-01", periods=20, freq="B", tz="UTC")
        df = pd.DataFrame({
            "open":   [100.0] * 20,
            "high":   [95.0] * 20,   # high < open → 违反
            "low":    [98.0] * 20,    # low > high → 违反
            "close":  [96.0] * 20,
            "volume": [1e6] * 20,
        }, index=idx)
        report = validate_ohlcv(df, symbol="TEST")
        assert not report.is_ok
        assert any("price_ohlc_violation" in i for i in report.issues)

    def test_validator_without_suspect_column(self):
        """V4: 不含 is_suspect 列的数据也能正常校验。"""
        idx = pd.date_range("2023-01-01", periods=20, freq="B", tz="UTC")
        df = pd.DataFrame({
            "open":   [100.0 + i for i in range(20)],
            "high":   [102.0 + i for i in range(20)],
            "low":    [99.0 + i for i in range(20)],
            "close":  [101.0 + i for i in range(20)],
            "volume": [1e6] * 20,
        }, index=idx)
        report = validate_ohlcv(df, symbol="TEST")
        assert report.is_ok
        assert report.suspect_bars == 0

    def test_none_input(self):
        """V5: df=None 时 is_ok=False，记录 empty_dataframe。"""
        report = validate_ohlcv(None, symbol="TEST")
        assert not report.is_ok
        assert "empty_dataframe" in report.issues
