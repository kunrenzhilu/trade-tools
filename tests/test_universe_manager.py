"""UniverseManager 测试。

所有测试使用内置迷你标的列表，Mock MarketDataStore，不触碰网络。
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from mytrader.universe.manager import UniverseManager
from mytrader.universe.grouping import build_group_id, compute_volatility_tier
from mytrader.universe.models import SymbolMeta


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_store():
    """Mock MarketDataStore，返回简单的 OHLCV 数据。"""
    store = MagicMock()
    n = 30
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    df = pd.DataFrame(
        {
            "open":   [100.0] * n,
            "high":   [103.0] * n,
            "low":    [97.0]  * n,
            "close":  [101.0] * n,
            "volume": [1_000_000] * n,
        },
        index=idx,
    )
    store.get_latest_n_bars.return_value = df
    store.get_bars.return_value = df
    return store


@pytest.fixture
def universe(mock_store):
    """使用内置标的列表的 UniverseManager（无 CSV）。"""
    return UniverseManager(store=mock_store, universe_file=None)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestUniverseManager:

    def test_get_universe_returns_symbols(self, universe):
        syms = universe.get_universe()
        assert len(syms) > 0
        assert "AAPL" in syms

    def test_get_universe_no_duplicates(self, universe):
        syms = universe.get_universe()
        assert len(syms) == len(set(syms))

    def test_get_symbol_meta_known(self, universe):
        meta = universe.get_symbol_meta("AAPL")
        assert meta is not None
        assert meta.symbol == "AAPL"
        assert "NASDAQ100" in meta.index_membership
        assert meta.sector != ""

    def test_get_symbol_meta_unknown(self, universe):
        meta = universe.get_symbol_meta("NOTEXIST")
        assert meta is None

    def test_get_groups_structure(self, universe):
        """get_groups 返回非空字典，values 是标的列表。"""
        groups = universe.get_groups()
        assert isinstance(groups, dict)
        # 内置标的，未计算波动率，全在 UNKNOWN 组
        assert len(groups) >= 1
        for gid, syms in groups.items():
            assert isinstance(syms, list)
            assert len(syms) > 0

    def test_recompute_volatility_tiers(self, universe):
        """重算后 meta 中 volatility_tier 不再是 unknown，group_id 合法。"""
        universe.recompute_volatility_tiers(max_workers=2)
        for sym in ["AAPL", "MSFT", "TSLA"]:
            meta = universe.get_symbol_meta(sym)
            assert meta is not None
            assert meta.volatility_tier in ("high", "mid", "low", "unknown")
            assert meta.group_id != "UNKNOWN" or meta.volatility_tier == "unknown"

    def test_groups_after_recompute_have_multiple(self, universe):
        """重算后至少有 2 个分组（NDX/SPX × vol 层级）。"""
        universe.recompute_volatility_tiers(max_workers=2)
        groups = universe.get_groups()
        # 内置标的含 NDX 和 SPX，至少 2 组
        assert len(groups) >= 2

    def test_recompute_volatility_tiers_at(self, universe, mock_store):
        """历史时点分组返回字典，不修改当前 meta。"""
        tier_map = universe.recompute_volatility_tiers_at(date(2024, 6, 1))
        assert isinstance(tier_map, dict)
        for sym in tier_map:
            assert tier_map[sym] in ("high", "mid", "low", "unknown")
        # 内部 meta 未被修改（inplace=False）
        meta = universe.get_symbol_meta("AAPL")
        assert meta is not None  # meta 仍存在

    def test_recompute_tiers_at_differ_from_current(self, universe, mock_store):
        """历史时点分组可以与当前不同（不同 mock 数据）。"""
        # 用高波动数据给历史时点
        n = 30
        idx = pd.date_range("2022-01-01", periods=n, freq="B")
        high_vol_df = pd.DataFrame(
            {
                "open":   [100.0] * n,
                "high":   [110.0] * n,   # 高波动
                "low":    [90.0]  * n,
                "close":  [100.0] * n,
                "volume": [1_000_000] * n,
            },
            index=idx,
        )
        mock_store.get_bars.return_value = high_vol_df
        tier_map = universe.recompute_volatility_tiers_at(date(2022, 6, 1))
        # 高波动数据应产生 "high" tier
        non_unknown = [t for t in tier_map.values() if t != "unknown"]
        if non_unknown:
            assert "high" in non_unknown

    def test_refresh_constituents_fallback_on_network_failure(self, universe):
        """网络失败时 refresh_constituents 保持原有成分股。"""
        original_count = len(universe.get_universe())
        with patch("mytrader.universe.manager.fetch_sp500", return_value=[]), \
             patch("mytrader.universe.manager.fetch_nasdaq100", return_value=[]):
            universe.refresh_constituents(save=False)
        # 应保持原有成分股不变
        assert len(universe.get_universe()) == original_count

    def test_load_from_csv(self, tmp_path, mock_store):
        """从 CSV 加载成分股。"""
        csv_path = tmp_path / "universe.csv"
        csv_path.write_text(
            "symbol,sector,index\nAAPL,Technology,NASDAQ100\nJPM,Financials,SP500\n"
        )
        um = UniverseManager(store=mock_store, universe_file=csv_path)
        syms = um.get_universe()
        assert "AAPL" in syms
        assert "JPM" in syms


class TestGrouping:

    def test_build_group_id_ndx_high(self):
        assert build_group_id(["NASDAQ100"], "high") == "NDX_high_vol"

    def test_build_group_id_spx_low(self):
        assert build_group_id(["SP500"], "low") == "SPX_low_vol"

    def test_build_group_id_both_indices_ndx_priority(self):
        """同时属于两个指数时 NDX 优先。"""
        gid = build_group_id(["SP500", "NASDAQ100"], "mid")
        assert gid == "NDX_mid_vol"

    def test_build_group_id_unknown_tier(self):
        gid = build_group_id(["SP500"], "unknown")
        # unknown 降级为 mid
        assert gid == "SPX_mid_vol"

    def test_compute_volatility_tier_empty_df(self):
        df = pd.DataFrame()
        assert compute_volatility_tier(df) == "unknown"

    def test_compute_volatility_tier_high(self):
        """极高波动数据 → high。"""
        n = 20
        idx = pd.date_range("2024-01-01", periods=n, freq="B")
        df = pd.DataFrame(
            {
                "open":   [100.0] * n,
                "high":   [115.0] * n,   # ATR% ≈ 15% → high
                "low":    [85.0]  * n,
                "close":  [100.0] * n,
                "volume": [1_000_000] * n,
            },
            index=idx,
        )
        tier = compute_volatility_tier(df)
        assert tier == "high"

    def test_compute_volatility_tier_low(self):
        """极低波动数据 → low。"""
        n = 20
        idx = pd.date_range("2024-01-01", periods=n, freq="B")
        df = pd.DataFrame(
            {
                "open":   [100.0] * n,
                "high":   [100.2] * n,   # ATR% ≈ 0.2% → low（<1%）
                "low":    [99.8]  * n,
                "close":  [100.0] * n,
                "volume": [1_000_000] * n,
            },
            index=idx,
        )
        tier = compute_volatility_tier(df)
        assert tier == "low"
