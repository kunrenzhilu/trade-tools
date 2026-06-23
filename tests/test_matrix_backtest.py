"""MatrixBacktest 测试。

使用 Mock MarketDataStore + 内置策略，不触碰网络。
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from mytrader.backtest.matrix_backtest import (
    MatrixBacktest,
    _backtest_one,
    _compute_sharpe,
    _portfolio_sharpe_from_results,
    SingleBacktestResult,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_ohlcv(n: int = 300, trend: str = "up") -> pd.DataFrame:
    """生成测试 OHLCV 数据（足够计算慢均线）。"""
    idx = pd.date_range("2021-01-01", periods=n, freq="B")
    if trend == "up":
        close = [100.0 + i * 0.1 for i in range(n)]
    else:
        close = [100.0 - i * 0.05 for i in range(n)]
    return pd.DataFrame(
        {
            "open":   [c - 0.5 for c in close],
            "high":   [c + 1.0 for c in close],
            "low":    [c - 1.0 for c in close],
            "close":  close,
            "volume": [1_000_000] * n,
        },
        index=idx,
    )


@pytest.fixture
def mock_store(tmp_path):
    store = MagicMock()
    df_aapl = _make_ohlcv(300, trend="up")
    df_msft = _make_ohlcv(300, trend="up")
    df_jpm  = _make_ohlcv(300, trend="up")

    def get_bars_multi(symbols, start, end, timeframe="1d"):
        mapping = {"AAPL": df_aapl, "MSFT": df_msft, "JPM": df_jpm}
        return {s: mapping[s] for s in symbols if s in mapping}

    store.get_bars_multi.side_effect = get_bars_multi
    return store


@pytest.fixture
def mock_universe():
    from mytrader.universe.models import SymbolMeta
    universe = MagicMock()
    universe.get_groups.return_value = {
        "NDX_mid_vol": ["AAPL", "MSFT"],
        "SPX_mid_vol": ["JPM"],
    }

    def get_meta(sym):
        ndx = ["AAPL", "MSFT"]
        return SymbolMeta(
            symbol=sym,
            index_membership=["NASDAQ100"] if sym in ndx else ["SP500"],
            sector="Technology" if sym in ndx else "Financials",
            market_cap_tier="large",
            volatility_tier="mid",
            group_id="NDX_mid_vol" if sym in ndx else "SPX_mid_vol",
        )
    universe.get_symbol_meta.side_effect = get_meta
    return universe


# ---------------------------------------------------------------------------
# 单函数测试
# ---------------------------------------------------------------------------

class TestHelpers:

    def test_compute_sharpe_positive(self):
        """正向收益的 Sharpe > 0。"""
        returns = pd.Series([0.001] * 252)
        sharpe = _compute_sharpe(returns)
        assert sharpe > 0

    def test_compute_sharpe_zero_std(self):
        """收益恒定（零方差）返回 0。"""
        returns = pd.Series([0.0] * 100)
        assert _compute_sharpe(returns) == 0.0

    def test_compute_sharpe_empty(self):
        assert _compute_sharpe(pd.Series([], dtype=float)) == 0.0

    def test_portfolio_sharpe_from_results(self):
        """等权组合 Sharpe 不等于算术平均 Sharpe（差异 > 1e-6）。"""
        n = 252
        r1 = pd.Series(np.random.normal(0.001, 0.01, n))   # 高收益高波动
        r2 = pd.Series(np.random.normal(0.0005, 0.002, n)) # 低收益低波动

        s1 = _compute_sharpe(r1)
        s2 = _compute_sharpe(r2)
        arithmetic_avg = (s1 + s2) / 2

        results = [
            SingleBacktestResult("SYM1", "s1", {}, s1, 10, 5, 60, 20, r1),
            SingleBacktestResult("SYM2", "s2", {}, s2, 5, 3, 55, 15, r2),
        ]
        portfolio_sharpe = _portfolio_sharpe_from_results(results)

        # 组合 Sharpe 与算术平均 Sharpe 应不同（这正是为什么要用组合方式）
        diff = abs(portfolio_sharpe - arithmetic_avg)
        assert diff > 1e-6, (
            f"组合 Sharpe({portfolio_sharpe:.4f}) 与算术平均 Sharpe({arithmetic_avg:.4f}) "
            f"差异应 >1e-6，否则说明实现有误"
        )

    def test_backtest_one_with_open(self):
        """传入 open= 参数，回测正常运行。"""
        df = _make_ohlcv(300)
        result = _backtest_one(df, "dual_ma", {"fast": 5, "slow": 20})
        assert result is not None
        assert not result.daily_returns.empty
        assert isinstance(result.sharpe, float)

    def test_backtest_one_without_open(self):
        """DataFrame 中无 open 列时也能正常回测（降级为 close 执行）。"""
        df = _make_ohlcv(300).drop(columns=["open"])
        result = _backtest_one(df, "dual_ma", {"fast": 5, "slow": 20})
        assert result is not None

    def test_backtest_one_empty_df(self):
        """空 DataFrame 返回 None。"""
        assert _backtest_one(pd.DataFrame(), "dual_ma", {}) is None

    def test_backtest_one_short_df(self):
        """不足 30 根 bar 返回 None。"""
        df = _make_ohlcv(10)
        assert _backtest_one(df, "dual_ma", {"fast": 5, "slow": 20}) is None

    def test_backtest_one_unknown_strategy(self):
        """未注册策略返回 None。"""
        df = _make_ohlcv(300)
        assert _backtest_one(df, "nonexistent_xyz", {}) is None

    def test_open_parameter_is_passed_to_vectorbt(self):
        """验证有 open 列时 _backtest_one 使用 open= 参数（而非仅用 close）。

        用 mock 拦截 vbt.Portfolio.from_signals，检查 open 参数是否被传入。
        """
        import unittest.mock as mock
        df = _make_ohlcv(100)

        with mock.patch("mytrader.backtest.matrix_backtest.vbt.Portfolio.from_signals") as m:
            # 让 mock 返回一个假 Portfolio
            fake_pf = mock.MagicMock()
            fake_pf.stats.return_value = {
                "Sharpe Ratio": 1.0, "Total Return [%]": 5.0,
                "Max Drawdown [%]": 3.0, "Win Rate [%]": 55.0, "Total Trades": 10,
            }
            fake_pf.returns.return_value = pd.Series([0.001] * len(df), index=df.index)
            m.return_value = fake_pf

            _backtest_one(df, "dual_ma", {"fast": 5, "slow": 20})

        # 验证 from_signals 被调用了，且 open 参数被传入
        assert m.called
        call_kwargs = m.call_args[1] if m.call_args[1] else {}
        # open 参数应该在 kwargs 中
        assert "open" in call_kwargs, "有 open 列时，open 参数应被传给 from_signals"


# ---------------------------------------------------------------------------
# MatrixBacktest 集成测试
# ---------------------------------------------------------------------------

class TestMatrixBacktest:

    def test_run_produces_groups(self, mock_store, mock_universe):
        """run() 产出包含分组权重的 MatrixBacktestReport。"""
        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=2)
        strategies = ["dual_ma"]
        param_grids = {"dual_ma": {"fast": [5], "slow": [20]}}

        report = mb.run(strategies=strategies, param_grids=param_grids)
        assert len(report.groups) >= 1
        # 每个分组应有策略权重配置
        for gid, weights in report.groups.items():
            assert isinstance(weights, list)

    def test_run_weights_sum_to_one(self, mock_store, mock_universe):
        """每个分组的策略权重之和 ≈ 1.0。"""
        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=2)
        report = mb.run(
            strategies=["dual_ma", "rsi"],
            param_grids={
                "dual_ma": {"fast": [5], "slow": [20]},
                "rsi": {"period": [14], "oversold": [30], "overbought": [70]},
            },
        )
        for gid, weights in report.groups.items():
            if weights:
                total = sum(w["weight"] for w in weights)
                assert abs(total - 1.0) < 0.01, f"{gid}: weights sum={total:.4f} ≠ 1.0"

    def test_run_output_file(self, mock_store, mock_universe, tmp_path):
        """output_file 参数会生成有效的 JSON 文件。"""
        output = tmp_path / "strategy_weights.json"
        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)
        mb.run(
            strategies=["dual_ma"],
            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
            output_file=output,
        )
        assert output.exists()
        data = json.loads(output.read_text())
        assert "_meta" in data
        assert "groups" in data
        assert "survivorship_bias_warning" in data["_meta"]

    def test_run_empty_universe(self, mock_store):
        """空标的组不崩溃。"""
        universe = MagicMock()
        universe.get_groups.return_value = {}
        mb = MatrixBacktest(store=mock_store, universe=universe, years=1)
        report = mb.run(strategies=["dual_ma"], param_grids={"dual_ma": {}})
        assert report.groups == {}

    def test_run_no_data_for_group(self, mock_universe, tmp_path):
        """组内无数据时优雅跳过。"""
        store = MagicMock()
        store.get_bars_multi.return_value = {}
        mb = MatrixBacktest(store=store, universe=mock_universe, years=1)
        report = mb.run(
            strategies=["dual_ma"],
            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
        )
        # 无数据 → 分组权重为空列表
        for gid, weights in report.groups.items():
            assert weights == []

    def test_group_results_have_portfolio_sharpe(self, mock_store, mock_universe):
        """GroupBacktestResult 中 portfolio_sharpe 是用组合 Sharpe 计算的浮点数。"""
        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)
        report = mb.run(
            strategies=["dual_ma"],
            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
        )
        for gr in report.group_results:
            assert isinstance(gr.portfolio_sharpe, float)
            assert gr.symbol_count > 0

    def test_survivorship_bias_warning_in_output(self, mock_store, mock_universe, tmp_path):
        """输出文件中包含幸存者偏差警告。"""
        output = tmp_path / "weights.json"
        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1)
        mb.run(
            strategies=["dual_ma"],
            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
            output_file=output,
        )
        data = json.loads(output.read_text())
        warning = data["_meta"].get("survivorship_bias_warning", "")
        assert "成分" in warning or "survivorship" in warning.lower()
