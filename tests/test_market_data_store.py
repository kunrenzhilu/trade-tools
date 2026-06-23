"""MarketDataStore + DataSyncService 测试。

使用 SQLite in-memory（:memory:）和 Mock DataProvider，不触碰网络。
"""

from __future__ import annotations

import threading
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from mytrader.data.store.market_data_store import MarketDataStore
from mytrader.data.store.models import SyncReport
from mytrader.data.store.sync_service import DataSyncService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def store(tmp_path):
    """使用临时目录创建 MarketDataStore（每个测试独立的 SQLite 文件）。"""
    db = MarketDataStore(db_path=tmp_path / "test.db")
    yield db
    db.close()


def _make_ohlcv(n: int = 10, start: str = "2024-01-01") -> pd.DataFrame:
    """生成测试用 OHLCV DataFrame。"""
    idx = pd.date_range(start=start, periods=n, freq="B")
    rng = list(range(n))
    return pd.DataFrame(
        {
            "open":   [100.0 + i for i in rng],
            "high":   [102.0 + i for i in rng],
            "low":    [98.0  + i for i in rng],
            "close":  [101.0 + i for i in rng],
            "volume": [1_000_000] * n,
        },
        index=idx,
    )


# ---------------------------------------------------------------------------
# MarketDataStore — 基础功能
# ---------------------------------------------------------------------------

class TestMarketDataStore:

    def test_upsert_and_count(self, store):
        df = _make_ohlcv(10)
        n = store.upsert_bars("AAPL", df, timeframe="1d", source="alpaca")
        assert n == 10
        assert store.count_bars("AAPL") == 10

    def test_upsert_idempotent(self, store):
        """重复 upsert 不增加行数。"""
        df = _make_ohlcv(10)
        store.upsert_bars("AAPL", df)
        n2 = store.upsert_bars("AAPL", df)
        assert store.count_bars("AAPL") == 10
        assert n2 == 0

    def test_upsert_incremental(self, store):
        """第二次 upsert 只新增不重叠部分。"""
        df1 = _make_ohlcv(5, start="2024-01-01")
        df2 = _make_ohlcv(5, start="2024-01-08")  # 不重叠
        store.upsert_bars("AAPL", df1)
        n = store.upsert_bars("AAPL", df2)
        assert n == 5
        assert store.count_bars("AAPL") == 10

    def test_get_bars_range(self, store):
        df = _make_ohlcv(20, start="2024-01-01")
        store.upsert_bars("AAPL", df)
        result = store.get_bars("AAPL", date(2024, 1, 1), date(2024, 1, 10))
        assert len(result) > 0
        assert list(result.columns) == ["open", "high", "low", "close", "volume"]

    def test_get_latest_n_bars(self, store):
        df = _make_ohlcv(30)
        store.upsert_bars("AAPL", df)
        result = store.get_latest_n_bars("AAPL", n=10)
        assert len(result) == 10
        # 应该是时间正序
        assert result.index.is_monotonic_increasing

    def test_get_bars_empty_returns_empty_df(self, store):
        result = store.get_bars("AAPL", date(2020, 1, 1), date(2020, 12, 31))
        assert result.empty

    def test_sync_state(self, store):
        assert store.get_last_synced("AAPL") is None
        store.set_last_synced("AAPL", date(2024, 6, 1))
        assert store.get_last_synced("AAPL") == date(2024, 6, 1)

    def test_sync_state_update(self, store):
        store.set_last_synced("AAPL", date(2024, 6, 1))
        store.set_last_synced("AAPL", date(2024, 6, 2))
        assert store.get_last_synced("AAPL") == date(2024, 6, 2)

    def test_data_quality_ok(self, store):
        store.set_last_synced("AAPL", date(2024, 6, 1), data_quality="ok")
        assert store.get_data_quality("AAPL") == "ok"

    def test_data_quality_degraded(self, store):
        store.set_last_synced("AAPL", date(2024, 6, 1), data_quality="degraded")
        assert store.get_data_quality("AAPL") == "degraded"

    def test_multi_timeframe_isolation(self, store):
        df = _make_ohlcv(10)
        store.upsert_bars("AAPL", df, timeframe="1d")
        store.upsert_bars("AAPL", df, timeframe="1h")
        assert store.count_bars("AAPL", "1d") == 10
        assert store.count_bars("AAPL", "1h") == 10

    def test_get_bars_multi_sqlite_fallback(self, store):
        """get_bars_multi 在 duckdb 不可用时 fallback 到 SQLite 逐只查询。"""
        df_aapl = _make_ohlcv(10, start="2024-01-01")
        df_msft = _make_ohlcv(10, start="2024-01-01")
        store.upsert_bars("AAPL", df_aapl)
        store.upsert_bars("MSFT", df_msft)

        # Patch duckdb 不可用
        with patch("mytrader.data.store.market_data_store._DUCKDB_AVAILABLE", False):
            result = store.get_bars_multi(
                ["AAPL", "MSFT"],
                date(2024, 1, 1),
                date(2024, 12, 31),
            )
        assert "AAPL" in result
        assert "MSFT" in result
        assert len(result["AAPL"]) > 0

    def test_thread_safety(self, store):
        """多线程并发 upsert 不崩溃。"""
        errors = []
        def write(sym):
            try:
                df = _make_ohlcv(5)
                store.upsert_bars(sym, df)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=write, args=(f"SYM{i}",)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Thread errors: {errors}"


# ---------------------------------------------------------------------------
# DataSyncService
# ---------------------------------------------------------------------------

class TestDataSyncService:

    def _make_provider(self, df: pd.DataFrame | None = None, raises: bool = False):
        """创建 Mock DataProvider。"""
        mock = MagicMock()
        if raises:
            mock.get_ohlcv.side_effect = ConnectionError("network error")
        else:
            mock.get_ohlcv.return_value = df if df is not None else _make_ohlcv(5)
        return mock

    def test_sync_symbol_first_time(self, store, tmp_path):
        """首次同步：主源有数据，写入并更新 sync_state。"""
        primary = self._make_provider(_make_ohlcv(20))
        svc = DataSyncService(store, primary=primary)
        n = svc.sync_symbol("AAPL")
        assert n > 0
        assert store.get_last_synced("AAPL") is not None
        assert store.get_data_quality("AAPL") == "ok"

    def test_sync_symbol_already_uptodate(self, store):
        """已是最新日期，跳过同步。"""
        store.set_last_synced("AAPL", date.today())
        primary = self._make_provider()
        svc = DataSyncService(store, primary=primary)
        n = svc.sync_symbol("AAPL")
        assert n == 0
        primary.get_ohlcv.assert_not_called()

    def test_sync_symbol_fallback_on_primary_empty(self, store):
        """主源返回空 df，fallback 到 yfinance，标记 degraded。"""
        primary = self._make_provider(pd.DataFrame())
        fallback = self._make_provider(_make_ohlcv(5))
        svc = DataSyncService(store, primary=primary, fallback=fallback)
        n = svc.sync_symbol("AAPL")
        assert n > 0
        assert store.get_data_quality("AAPL") == "degraded"

    def test_sync_symbol_no_fallback_when_disabled(self, store):
        """use_fallback_on_empty=False 时，主源无数据不写入。"""
        primary = self._make_provider(pd.DataFrame())
        fallback = self._make_provider(_make_ohlcv(5))
        svc = DataSyncService(store, primary=primary, fallback=fallback,
                               use_fallback_on_empty=False)
        n = svc.sync_symbol("AAPL")
        assert n == 0
        fallback.get_ohlcv.assert_not_called()
        assert store.get_data_quality("AAPL") == "degraded"

    def test_sync_symbol_primary_exception_uses_fallback(self, store):
        """主源抛异常，fallback 正常工作。"""
        primary = self._make_provider(raises=True)
        fallback = self._make_provider(_make_ohlcv(5))
        svc = DataSyncService(store, primary=primary, fallback=fallback)
        n = svc.sync_symbol("AAPL")
        assert n > 0
        assert store.get_data_quality("AAPL") == "degraded"

    def test_sync_all(self, store):
        """sync_all 并发同步多只，汇总报告正确。"""
        symbols = ["AAPL", "MSFT", "TSLA"]
        primary = self._make_provider(_make_ohlcv(10))
        svc = DataSyncService(store, primary=primary)
        report = svc.sync_all(symbols, max_workers=3)
        assert report.total_symbols == 3
        assert report.synced_ok == 3
        assert report.failed == 0
        assert report.total_new_bars > 0

    def test_sync_all_partial_failure(self, store):
        """sync_all 部分失败时：主源抛异常且无 fallback → degraded（不计入 failed）。
        sync_service 的设计是"尽力而为"，异常被吞掉并标记 degraded，确保其他标的不受影响。
        """
        def side_effect(symbol, start, end, timeframe="1d"):
            if symbol == "FAIL":
                raise RuntimeError("API error")
            return _make_ohlcv(5)

        primary = MagicMock()
        primary.get_ohlcv.side_effect = side_effect
        svc = DataSyncService(store, primary=primary)
        report = svc.sync_all(["AAPL", "FAIL", "MSFT"])
        assert report.synced_ok == 2
        assert report.synced_degraded == 1   # FAIL 标记为 degraded
        assert report.failed == 0            # 不计为 failed（已被优雅处理）
        assert report.total_new_bars == 10
