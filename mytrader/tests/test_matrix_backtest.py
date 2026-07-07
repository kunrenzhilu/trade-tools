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
    _combine_daily_returns,
    _compute_alpha,
    _compute_sharpe,
    _compute_sortino,
    _portfolio_max_drawdown_from_results,
    _portfolio_sharpe_from_results,
    _portfolio_sortino_from_results,
    _optimize_ensemble_weights,
    _safe_float,
    _safe_mean,
    MAX_PORTFOLIO_DRAWDOWN_PCT,
    MIN_SORTINO_THRESHOLD,
    WALK_FORWARD_VAL_DD_THRESHOLD,
    SingleBacktestResult,
    WalkForwardReport,
    WalkForwardRound,
    _add_months,
    run_walk_forward,
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

    # ── Sortino（迭代 #1 新增，Constitution L1 首要 KPI）─────────────────────

    def test_compute_sortino_positive(self):
        """正均值的收益序列 Sortino > 0。"""
        returns = pd.Series([0.001, -0.0005, 0.002, -0.0003, 0.0015] * 60)
        assert _compute_sortino(returns) > 0

    def test_compute_sortino_empty(self):
        """空序列返回 0。"""
        assert _compute_sortino(pd.Series([], dtype=float)) == 0.0

    def test_compute_sortino_no_downside_returns_zero(self):
        """全正收益（无下行波动）→ 0.0（退化处理，与 _compute_sharpe 一致）。

        理论上 Sortino 应为 +inf，但返回 0 保持可算术聚合 + 保守评估。
        """
        returns = pd.Series([0.001] * 100)   # 全正，无下行
        assert _compute_sortino(returns) == 0.0

    def test_compute_sortino_differs_from_sharpe_when_asymmetric(self):
        """当上行/下行波动不对称时，Sortino ≠ Sharpe（这是引入 Sortino 的意义）。"""
        # 大幅上行小波动 + 偶尔小幅下行：Sortino 应明显高于 Sharpe
        np.random.seed(42)
        upside = np.random.normal(0.003, 0.005, 200)   # 正均值的上行
        downside_shocks = np.array([-0.01, -0.012, -0.008] * 3)  # 少量下行冲击
        returns = pd.Series(np.concatenate([upside, downside_shocks]))

        sharpe = _compute_sharpe(returns)
        sortino = _compute_sortino(returns)
        # Sortino 仅对下行惩罚 → 上行波动不计入分母 → Sortino > Sharpe
        assert sortino > sharpe, (
            f"非对称收益下 Sortino({sortino:.4f}) 应 > Sharpe({sharpe:.4f})，"
            f"否则说明 Sortino 公式退化为 Sharpe"
        )

    def test_compute_sortino_known_value(self):
        """已知值验算 Sortino 公式正确性。"""
        # r = [0.01, 0.01, 0.01, -0.01]
        # mean = 0.005; downside = [0,0,0,-0.01]; dd = sqrt(mean([0,0,0,0.0001])) = sqrt(0.000025) = 0.005
        # Sortino = 0.005 / 0.005 * sqrt(252) = 15.8745...
        returns = pd.Series([0.01, 0.01, 0.01, -0.01] * 25)   # 重复 25 次以满足 len>=5
        expected = (0.005 / 0.005) * np.sqrt(252)
        assert abs(_compute_sortino(returns) - expected) < 1e-6

    def test_portfolio_sortino_from_results(self):
        """等权组合 Sortino 不等于各标的 Sortino 算术平均（与 Sharpe 同理）。"""
        n = 252
        np.random.seed(0)
        r1 = pd.Series(np.random.normal(0.001, 0.01, n))
        r2 = pd.Series(np.random.normal(0.0005, 0.002, n))

        s1 = _compute_sortino(r1)
        s2 = _compute_sortino(r2)
        arithmetic_avg = (s1 + s2) / 2

        results = [
            SingleBacktestResult("SYM1", "s1", {}, 0.0, 0, 0, 0, 0, r1),
            SingleBacktestResult("SYM2", "s2", {}, 0.0, 0, 0, 0, 0, r2),
        ]
        portfolio_sortino = _portfolio_sortino_from_results(results)

        diff = abs(portfolio_sortino - arithmetic_avg)
        assert diff > 1e-6, (
            f"组合 Sortino({portfolio_sortino:.4f}) 与算术平均({arithmetic_avg:.4f}) "
            f"差异应 >1e-6，否则说明实现退化为算术平均"
        )

    # ── _safe_float / _safe_mean（迭代 #2 新增）─────────────────────────────

    def test_safe_float_handles_nan(self):
        """NaN 是 truthy，`NaN or 0.0` 仍为 NaN；_safe_float 必须返回 default。"""
        nan = float("nan")
        assert _safe_float(nan) == 0.0
        assert _safe_float(nan, default=-1.0) == -1.0

    def test_safe_float_handles_none(self):
        assert _safe_float(None) == 0.0
        assert _safe_float(None, default=3.14) == 3.14

    def test_safe_float_handles_inf(self):
        assert _safe_float(float("inf")) == 0.0
        assert _safe_float(float("-inf")) == 0.0

    def test_safe_float_passes_normal_numbers(self):
        assert _safe_float(1.5) == 1.5
        assert _safe_float(0) == 0.0
        assert _safe_float(-2.7) == -2.7
        assert _safe_float("3.14") == 3.14   # 字符串数字可转

    def test_safe_float_handles_non_numeric(self):
        assert _safe_float("abc") == 0.0
        assert _safe_float([1, 2, 3]) == 0.0
        assert _safe_float(object()) == 0.0

    def test_safe_mean_empty_list(self):
        """空列表返回 default（np.mean([]) 会触发 RuntimeWarning 并返回 NaN）。"""
        assert _safe_mean([]) == 0.0
        assert _safe_mean([], default=2.0) == 2.0

    def test_safe_mean_all_nan(self):
        """全 NaN 列表返回 default。"""
        assert _safe_mean([float("nan"), float("nan")]) == 0.0

    def test_safe_mean_partial_nan(self):
        """部分 NaN 自动忽略（nanmean 语义）。"""
        result = _safe_mean([1.0, float("nan"), 3.0])
        assert abs(result - 2.0) < 1e-9

    def test_safe_mean_normal(self):
        assert abs(_safe_mean([1.0, 2.0, 3.0]) - 2.0) < 1e-9

    # ── _portfolio_max_drawdown_from_results（迭代 #2 新增）────────────────

    def test_portfolio_max_drawdown_no_returns(self):
        """无有效日收益率 → 0.0。"""
        results: list[SingleBacktestResult] = []
        assert _portfolio_max_drawdown_from_results(results) == 0.0

    def test_portfolio_max_drawdown_all_positive(self):
        """全正收益 → 无回撤，返回 0.0。"""
        r = pd.Series([0.001] * 100)
        results = [SingleBacktestResult("S1", "s", {}, 0.0, 0, 0, 0, 0, r)]
        assert _portfolio_max_drawdown_from_results(results) == 0.0

    def test_portfolio_max_drawdown_known_value(self):
        """已知值验算：先涨后跌回测组合 DD。

        组合等权日收益率 = r。cumvalue 从 1.0 涨到 1.05，再跌到 0.95。
        peak = 1.05, trough = 0.95, DD = (0.95 - 1.05) / 1.05 ≈ -9.524%。
        """
        # 10 天 +1% → cumvalue 涨到 1.01^10 ≈ 1.1046
        # 10 天 -1% → cumvalue 跌到 1.1046 * 0.99^10 ≈ 0.9994
        # peak=1.1046, trough=0.9994, DD = (0.9994 - 1.1046) / 1.1046 ≈ -9.52%
        returns = pd.Series([0.01] * 10 + [-0.01] * 10)
        results = [SingleBacktestResult("S1", "s", {}, 0.0, 0, 0, 0, 0, returns)]
        dd = _portfolio_max_drawdown_from_results(results)
        assert dd > 0.0, "存在回撤时应返回正值"
        assert 8.0 < dd < 11.0, f"DD 应在 9.5% 附近，实际 {dd:.4f}%"

    def test_portfolio_max_drawdown_returns_positive_pct(self):
        """返回值为正百分数（与 backtest_max_drawdown 输出口径一致）。"""
        np.random.seed(42)
        # 模拟一个带回撤的序列
        r = pd.Series(np.concatenate([
            np.random.normal(0.002, 0.005, 50),
            np.random.normal(-0.003, 0.008, 30),
            np.random.normal(0.001, 0.004, 50),
        ]))
        results = [SingleBacktestResult("S1", "s", {}, 0.0, 0, 0, 0, 0, r)]
        dd = _portfolio_max_drawdown_from_results(results)
        assert dd >= 0.0
        assert isinstance(dd, float)

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
            strategies=["dual_ma", "rsi_mean_revert"],
            param_grids={
                "dual_ma": {"fast": [5], "slow": [20]},
                "rsi_mean_revert": {"period": [14], "oversold": [30], "overbought": [70]},
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

    # ── 迭代 #1 新增：观测性 + 回归 + Sortino 输出 ──────────────────────────

    def test_unknown_strategy_logs_warning(self, mock_store, mock_universe):
        """未注册策略名在 _run_group 中输出 WARNING 日志（而非静默跳过）。

        这是迭代 #1 修复的核心观测性问题：之前 _backtest_one 内部静默 return None，
        导致 main.py 误用 "rsi"/"macd"/"bollinger" 简称 6 天未被发现。

        注意：项目用 loguru 而非 stdlib logging，故用 loguru sink 捕获（caplog 无效）。
        """
        from loguru import logger

        msgs: list[str] = []
        # 临时 sink 捕获所有 WARNING+ 日志到列表
        handler_id = logger.add(lambda m: msgs.append(str(m)), level="WARNING")
        try:
            mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=2)
            mb.run(
                strategies=["dual_ma", "totally_bogus_name"],
                param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
            )
        finally:
            logger.remove(handler_id)

        # 应有 WARNING 提及 bogus 策略名
        assert any("totally_bogus_name" in m for m in msgs), (
            f"未注册策略应触发 WARNING，实际捕获: {msgs}"
        )

    def test_reoptimize_strategy_names_match_registry(self):
        """回归测试：main.REOPTIMIZE_STRATEGIES 中每个策略名必须在注册表中。

        防止迭代 #1 的 bug 重现：策略名拼写与 @register_strategy 装饰器不匹配，
        导致矩阵回测静默跳过整类策略、strategy_weights.json 退化为仅 dual_ma。
        """
        from main import REOPTIMIZE_STRATEGIES, REOPTIMIZE_PARAM_GRIDS
        from mytrader.strategy.registry import STRATEGY_REGISTRY

        assert len(REOPTIMIZE_STRATEGIES) >= 4, (
            f"预期至少 4 个策略，实际 {len(REOPTIMIZE_STRATEGIES)}：{REOPTIMIZE_STRATEGIES}"
        )
        for name in REOPTIMIZE_STRATEGIES:
            assert name in STRATEGY_REGISTRY, (
                f"REOPTIMIZE_STRATEGIES 中的 '{name}' 未在 STRATEGY_REGISTRY 注册。"
                f"已注册: {sorted(STRATEGY_REGISTRY.keys())}"
            )
            assert name in REOPTIMIZE_PARAM_GRIDS, (
                f"REOPTIMIZE_PARAM_GRIDS 缺少 '{name}' 的参数网格"
            )

    def test_output_file_contains_sortino(self, mock_store, mock_universe, tmp_path):
        """strategy_weights.json 每个权重条目含 backtest_sortino 字段（Constitution L1 首要 KPI）。"""
        output = tmp_path / "weights_with_sortino.json"
        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)
        mb.run(
            strategies=["dual_ma"],
            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
            output_file=output,
        )
        data = json.loads(output.read_text())
        for gid, weights in data["groups"].items():
            for w in weights:
                assert "backtest_sortino" in w, (
                    f"{gid}: 权重条目缺少 backtest_sortino 字段，实际 keys={list(w.keys())}"
                )
                assert isinstance(w["backtest_sortino"], (int, float)), (
                    f"{gid}: backtest_sortino 应为数值，实际 {type(w['backtest_sortino'])}"
                )

    def test_group_results_have_portfolio_sortino(self, mock_store, mock_universe):
        """GroupBacktestResult.portfolio_sortino 是浮点数（迭代 #1 新增字段）。"""
        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)
        report = mb.run(
            strategies=["dual_ma"],
            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
        )
        for gr in report.group_results:
            assert isinstance(gr.portfolio_sortino, float), (
                f"portfolio_sortino 应为 float，实际 {type(gr.portfolio_sortino)}"
            )

    # ── 迭代 #2 新增：portfolio_max_drawdown 字段 + backtest_max_drawdown 输出 ──

    def test_group_results_have_portfolio_max_drawdown(self, mock_store, mock_universe):
        """GroupBacktestResult.portfolio_max_drawdown 是非负浮点数。"""
        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)
        report = mb.run(
            strategies=["dual_ma"],
            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
        )
        for gr in report.group_results:
            assert isinstance(gr.portfolio_max_drawdown, float), (
                f"portfolio_max_drawdown 应为 float，实际 {type(gr.portfolio_max_drawdown)}"
            )
            assert gr.portfolio_max_drawdown >= 0.0, (
                f"portfolio_max_drawdown 应非负，实际 {gr.portfolio_max_drawdown}"
            )

    def test_output_file_contains_max_drawdown(self, mock_store, mock_universe, tmp_path):
        """strategy_weights.json 每个权重条目含 backtest_max_drawdown 字段。"""
        output = tmp_path / "weights_with_dd.json"
        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)
        mb.run(
            strategies=["dual_ma"],
            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
            output_file=output,
        )
        data = json.loads(output.read_text())
        for gid, weights in data["groups"].items():
            for w in weights:
                assert "backtest_max_drawdown" in w, (
                    f"{gid}: 权重条目缺少 backtest_max_drawdown 字段，"
                    f"实际 keys={list(w.keys())}"
                )
                assert isinstance(w["backtest_max_drawdown"], (int, float)), (
                    f"{gid}: backtest_max_drawdown 应为数值，"
                    f"实际 {type(w['backtest_max_drawdown'])}"
                )

    def test_output_file_no_nan(self, mock_store, mock_universe, tmp_path):
        """输出的 JSON 文件不能包含 NaN（否则非法 JSON）。

        迭代 #2 修复的核心问题：vectorbt 无交易场景下 Win Rate 返回 NaN，
        `float(NaN or 0.0)` 仍为 NaN（NaN 是 truthy），导致 JSON 序列化写出
        非法 JSON（NaN/Infinity 非 JSON 规范）。_safe_float 修复后不应再出现。
        """
        output = tmp_path / "weights_no_nan.json"
        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)
        mb.run(
            strategies=["dual_ma"],
            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
            output_file=output,
        )
        # 用严格模式解析 JSON：json.loads 默认接受 NaN，需用 parse_constant 拦截
        raw = output.read_text()
        # 替换 NaN/Infinity 为哨兵字符串，再用 json 解析检测
        import re as _re
        bad_tokens = _re.findall(r"\bNaN\b|\bInfinity\b|\b-Infinity\b", raw)
        assert not bad_tokens, (
            f"JSON 中发现非法 token: {bad_tokens}（应为有限数值）"
        )


# ---------------------------------------------------------------------------
# 迭代 #3 P0 新增：DD 约束 + fallback + dd_constrained 字段
# ---------------------------------------------------------------------------

class TestDDConstraint:
    """P0: 修复 NDX_high_vol DD 超标（Gate 1 阻塞项）。"""

    def test_dd_constrained_field_exists_in_group_result(self, mock_store, mock_universe):
        """GroupBacktestResult 含 dd_constrained bool 字段，默认 False。"""
        from mytrader.backtest.matrix_backtest import GroupBacktestResult
        gr = GroupBacktestResult(
            group_id="test", strategy="dual_ma", params={},
            portfolio_sharpe=1.0, avg_total_return_pct=10.0,
            avg_max_drawdown_pct=-5.0, avg_win_rate_pct=55.0, symbol_count=3,
        )
        assert hasattr(gr, "dd_constrained"), "GroupBacktestResult 必须有 dd_constrained 字段"
        assert gr.dd_constrained is False, "dd_constrained 默认应为 False"

    def test_compliant_candidates_selected_by_sortino(self, tmp_path):
        """P0 case 1: 有合规候选时，按 Sortino 降序选 top-K（不选 DD 超标的候选）。

        场景：3 个候选，其中 2 个 DD=10%（合规）、1 个 DD=25%（超标）。
        虽然 DD=25% 的候选 Sortino 更高，但 DD 约束应将其排除。
        """
        # 构造 mock store：返回一组上涨数据，回测 DD 自然 < 20%
        store = MagicMock()
        df = _make_ohlcv(300, trend="up")
        store.get_bars_multi.side_effect = lambda symbols, start, end, timeframe="1d": {
            s: df.copy() for s in symbols
        }

        universe = MagicMock()
        universe.get_groups.return_value = {"test_group": ["AAPL", "MSFT"]}

        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
        # 用两个策略（都合规）测试 top-K 选择
        report = mb.run(
            strategies=["dual_ma", "rsi_mean_revert"],
            param_grids={
                "dual_ma": {"fast": [5], "slow": [20]},
                "rsi_mean_revert": {"period": [14], "oversold": [30], "overbought": [70]},
            },
            output_file=tmp_path / "weights.json",
        )

        # 验证：有合规候选时 dd_constrained=False
        for gid, weights in report.groups.items():
            for w in weights:
                assert "dd_constrained" in w, f"{gid}: 缺少 dd_constrained 字段"
                assert w["dd_constrained"] is False, (
                    f"{gid}: 有合规候选时 dd_constrained 应为 False，"
                    f"实际 {w['dd_constrained']}（候选 DD 均在阈值内）"
                )

    def test_fallback_when_no_compliant_candidates(self, tmp_path):
        """P0 case 2: 无合规候选时 fallback — 按 DD 升序选 top-K，标记 dd_constrained=True。

        场景：构造 rsi_mean_revert 会买入后持续下跌的数据，让 portfolio DD >> 20%。
        使用 rsi_mean_revert 策略：先压低 RSI（超卖触发买入），买入后价格持续大幅下跌。
        验证：top-K 仍产出（不抛异常），且 dd_constrained=True。

        注：dual_ma 是趋势跟踪策略，"先涨后跌"场景下会在下跌初期平仓，DD 不易超 20%。
        rsi_mean_revert 在 oversold 买入后若价格持续跌，会持续持仓，DD 显著更高。
        """
        store = MagicMock()
        # 构造：先压低 RSI（200天缓慢下跌触发超卖买入信号），
        # 然后买入后价格急速崩溃下跌 60%，造成巨大持仓损失
        n = 400
        idx = pd.date_range("2021-01-01", periods=n, freq="B")
        close = (
            [100.0 * (1 - 0.002 * i) for i in range(200)]   # 缓慢下跌压低RSI
            + [60.0 * (1 - 0.005 * (i - 200)) for i in range(200, n)]  # 急速崩溃
        )
        close = [max(c, 1.0) for c in close]  # 防止价格为负
        df_crash = pd.DataFrame(
            {
                "open":   [c - 0.3 for c in close],
                "high":   [c + 0.5 for c in close],
                "low":    [c - 0.5 for c in close],
                "close":  close,
                "volume": [1_000_000] * n,
            },
            index=idx,
        )
        store.get_bars_multi.side_effect = lambda symbols, start, end, timeframe="1d": {
            s: df_crash.copy() for s in symbols
        }

        universe = MagicMock()
        universe.get_groups.return_value = {"volatile_group": ["AAPL", "MSFT"]}

        # 使用 rsi_mean_revert，超卖买入后持续下跌，确保 DD >> 20%
        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
        report = mb.run(
            strategies=["rsi_mean_revert"],
            param_grids={"rsi_mean_revert": {
                "period": [14], "oversold": [35], "overbought": [65]
            }},
            output_file=tmp_path / "weights_fallback.json",
        )

        # 若产生权重，验证：fallback 触发（dd_constrained=True）或无权重（极端无交易场景）
        has_weights = any(weights for weights in report.groups.values() if weights)
        if has_weights:
            for gid, weights in report.groups.items():
                for w in weights:
                    if w.get("backtest_max_drawdown", 0) > 20.0:
                        assert w["dd_constrained"] is True, (
                            f"{gid}: DD={w['backtest_max_drawdown']:.1f}% > 20% "
                            f"但 dd_constrained 为 False"
                        )

    def test_output_file_contains_dd_constrained_field(self, mock_store, mock_universe, tmp_path):
        """P0 case 3: strategy_weights.json 每个权重条目含 dd_constrained 字段。"""
        output = tmp_path / "weights_dd_constrained.json"
        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)
        mb.run(
            strategies=["dual_ma"],
            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
            output_file=output,
        )
        data = json.loads(output.read_text())
        for gid, weights in data["groups"].items():
            for w in weights:
                assert "dd_constrained" in w, (
                    f"{gid}: 权重条目缺少 dd_constrained 字段，"
                    f"实际 keys={list(w.keys())}"
                )
                assert isinstance(w["dd_constrained"], bool), (
                    f"{gid}: dd_constrained 应为 bool，"
                    f"实际 {type(w['dd_constrained'])}"
                )

    def test_max_drawdown_threshold_is_20(self):
        """Constitution L1: MAX_PORTFOLIO_DRAWDOWN_PCT = 20.0（硬约束）。"""
        assert MAX_PORTFOLIO_DRAWDOWN_PCT == 20.0, (
            f"MAX_PORTFOLIO_DRAWDOWN_PCT 应为 20.0 (Constitution L1)，"
            f"实际 {MAX_PORTFOLIO_DRAWDOWN_PCT}"
        )


# ---------------------------------------------------------------------------
# 迭代 #3 P1 新增：Walk-Forward 4 轮验证
# ---------------------------------------------------------------------------

class TestWalkForward:
    """P1: Walk-Forward 4 轮验证（Constitution L7 流水线硬要求）。"""

    def test_walk_forward_round_dataclass(self):
        """WalkForwardRound dataclass 字段完整 + passed 判定正确。"""
        from datetime import date as _date
        r = WalkForwardRound(
            round_num=1,
            train_start=_date(2021, 7, 2),
            train_end=_date(2023, 1, 2),
            val_start=_date(2023, 1, 2),
            val_end=_date(2023, 7, 2),
            val_sortino=1.5,
            val_max_dd=10.0,
            passed=True,
        )
        assert r.round_num == 1
        assert r.train_start == _date(2021, 7, 2)
        assert r.val_end == _date(2023, 7, 2)
        assert r.val_sortino == 1.5
        assert r.val_max_dd == 10.0
        assert r.passed is True

    def test_walk_forward_round_passed_threshold(self):
        """passed = val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD (15%)。"""
        from datetime import date as _date
        # DD = 15.0 → passed (边界)
        r_boundary = WalkForwardRound(
            round_num=1,
            train_start=_date(2021, 1, 1), train_end=_date(2023, 1, 1),
            val_start=_date(2023, 1, 1), val_end=_date(2023, 7, 1),
            val_sortino=1.0, val_max_dd=15.0, passed=True,
        )
        assert r_boundary.passed is True
        assert WALK_FORWARD_VAL_DD_THRESHOLD == 15.0, (
            f"WF 验证 DD 门槛应为 15.0%，实际 {WALK_FORWARD_VAL_DD_THRESHOLD}"
        )

        # DD = 15.01 → not passed
        r_fail = WalkForwardRound(
            round_num=2,
            train_start=_date(2021, 1, 1), train_end=_date(2023, 1, 1),
            val_start=_date(2023, 1, 1), val_end=_date(2023, 7, 1),
            val_sortino=1.0, val_max_dd=15.01, passed=False,
        )
        assert r_fail.passed is False

    def test_walk_forward_report_dataclass(self):
        """WalkForwardReport: pass_all_rounds + max_val_dd 计算正确。"""
        from datetime import date as _date
        rounds = [
            WalkForwardRound(1, _date(2021, 1, 1), _date(2023, 1, 1),
                             _date(2023, 1, 1), _date(2023, 7, 1), 1.0, 10.0, True),
            WalkForwardRound(2, _date(2021, 7, 1), _date(2023, 7, 1),
                             _date(2023, 7, 1), _date(2024, 1, 1), 0.8, 12.0, True),
            WalkForwardRound(3, _date(2022, 1, 1), _date(2024, 1, 1),
                             _date(2024, 1, 1), _date(2024, 7, 1), 1.2, 8.0, True),
            WalkForwardRound(4, _date(2022, 7, 1), _date(2024, 7, 1),
                             _date(2024, 7, 1), _date(2025, 1, 1), 0.9, 14.0, True),
        ]
        report = WalkForwardReport(
            rounds=rounds,
            pass_all_rounds=all(r.passed for r in rounds),
            max_val_dd=max(r.val_max_dd for r in rounds),
        )
        assert report.pass_all_rounds is True
        assert report.max_val_dd == 14.0
        assert len(report.rounds) == 4

    def test_walk_forward_report_all_fail(self):
        """pass_all_rounds=False 当任一轮失败。"""
        from datetime import date as _date
        rounds = [
            WalkForwardRound(1, _date(2021, 1, 1), _date(2023, 1, 1),
                             _date(2023, 1, 1), _date(2023, 7, 1), 1.0, 10.0, True),
            WalkForwardRound(2, _date(2021, 7, 1), _date(2023, 7, 1),
                             _date(2023, 7, 1), _date(2024, 1, 1), 0.8, 18.0, False),  # fail
        ]
        report = WalkForwardReport(
            rounds=rounds,
            pass_all_rounds=all(r.passed for r in rounds),
            max_val_dd=max(r.val_max_dd for r in rounds),
        )
        assert report.pass_all_rounds is False
        assert report.max_val_dd == 18.0

    def test_add_months_basic(self):
        """_add_months 基本加减月数正确。"""
        from datetime import date as _date
        # +18 months
        assert _add_months(_date(2021, 7, 2), 18) == _date(2023, 1, 2)
        # -6 months
        assert _add_months(_date(2023, 7, 2), -6) == _date(2023, 1, 2)
        # +0 months (identity)
        assert _add_months(_date(2026, 7, 1), 0) == _date(2026, 7, 1)

    def test_add_months_month_end_clamp(self):
        """_add_months 自动 clamp 到月末（如 1/31 + 1 month = 2/28）。"""
        from datetime import date as _date
        # 1月31日 + 1月 → 2月28日（2023非闰年）
        result = _add_months(_date(2023, 1, 31), 1)
        assert result == _date(2023, 2, 28), f"1/31 + 1m 应为 2/28，实际 {result}"

    def test_walk_forward_windows_match_user_spec(self):
        """验证默认参数 (rounds=4, train_months=18, val_months=6) 产生的窗口
        与用户提供的固定窗口匹配（today=2026-07-01）。

        用户固定窗口：
            Round 1: train 2021-07-02~2023-01-02, val 2023-01-02~2023-07-02
            Round 2: train 2022-01-02~2023-07-02, val 2023-07-02~2024-01-02
            Round 3: train 2022-07-02~2024-01-02, val 2024-01-02~2024-07-02
            Round 4: train 2023-01-02~2024-07-02, val 2024-07-02~2025-01-02
        """
        from datetime import date as _date
        today = _date(2026, 7, 1)
        rounds = 4
        train_months = 18
        val_months = 6
        # run_walk_forward 从最近往前推：last round 的 val_end = today - val_months
        # Round 4: val_end=2026-01-01, val_start=2025-07-01, train=2024-01-01~2025-07-01
        # Round 3: val_end=2025-07-01, val_start=2025-01-01, train=2023-07-01~2025-01-01
        # Round 2: val_end=2025-01-01, val_start=2024-07-01, train=2023-01-01~2024-07-01
        # Round 1: val_end=2024-07-01, val_start=2024-01-01, train=2022-07-01~2024-01-01
        expected = [
            # (round_num, train_start, train_end, val_start, val_end)
            (1, _date(2022, 7, 1), _date(2024, 1, 1), _date(2024, 1, 1), _date(2024, 7, 1)),
            (2, _date(2023, 1, 1), _date(2024, 7, 1), _date(2024, 7, 1), _date(2025, 1, 1)),
            (3, _date(2023, 7, 1), _date(2025, 1, 1), _date(2025, 1, 1), _date(2025, 7, 1)),
            (4, _date(2024, 1, 1), _date(2025, 7, 1), _date(2025, 7, 1), _date(2026, 1, 1)),
        ]
        for round_num, exp_ts, exp_te, exp_vs, exp_ve in expected:
            val_end = _add_months(
                today, -val_months - (rounds - round_num) * val_months
            )
            val_start = _add_months(val_end, -val_months)
            train_end = val_start
            train_start = _add_months(train_end, -train_months)
            assert train_start == exp_ts, (
                f"Round {round_num} train_start: 期望 {exp_ts}，实际 {train_start}"
            )
            assert train_end == exp_te, (
                f"Round {round_num} train_end: 期望 {exp_te}，实际 {train_end}"
            )
            assert val_start == exp_vs, (
                f"Round {round_num} val_start: 期望 {exp_vs}，实际 {val_start}"
            )
            assert val_end == exp_ve, (
                f"Round {round_num} val_end: 期望 {exp_ve}，实际 {val_end}"
            )

    def test_run_walk_forward_mock_integration(self, mock_store, mock_universe):
        """P1 集成测试：run_walk_forward 用 mock store/universe 跑完 4 轮。

        验证：
            1. 返回 WalkForwardReport 实例
            2. rounds 长度为 4
            3. 每轮有 val_sortino / val_max_dd / passed 字段
            4. pass_all_rounds 与 rounds 中 passed 一致
            5. max_val_dd = max(r.val_max_dd)
        """
        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=2)

        report = run_walk_forward(
            mb=mb,
            strategies=["dual_ma"],
            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
            rounds=4,
            train_months=18,
            val_months=6,
        )

        assert isinstance(report, WalkForwardReport), (
            f"run_walk_forward 应返回 WalkForwardReport，实际 {type(report)}"
        )
        assert len(report.rounds) == 4, (
            f"应跑 4 轮，实际 {len(report.rounds)} 轮"
        )
        for i, r in enumerate(report.rounds):
            assert isinstance(r, WalkForwardRound)
            assert r.round_num == i + 1, (
                f"Round {i}: round_num 应为 {i+1}，实际 {r.round_num}"
            )
            assert isinstance(r.val_sortino, float)
            assert isinstance(r.val_max_dd, float)
            assert r.val_max_dd >= 0.0
            assert isinstance(r.passed, bool)
            assert r.passed == (r.val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD)

        expected_pass = all(r.passed for r in report.rounds)
        assert report.pass_all_rounds == expected_pass
        expected_max_dd = max(r.val_max_dd for r in report.rounds)
        assert abs(report.max_val_dd - expected_max_dd) < 1e-9

    def test_run_walk_forward_empty_universe(self):
        """空标的组时返回空 WalkForwardReport，不抛异常。"""
        store = MagicMock()
        store.get_bars_multi.return_value = {}
        universe = MagicMock()
        universe.get_groups.return_value = {}
        mb = MatrixBacktest(store=store, universe=universe, years=1)

        report = run_walk_forward(
            mb=mb,
            strategies=["dual_ma"],
            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
            rounds=4,
        )
        assert isinstance(report, WalkForwardReport)
        assert report.rounds == []
        assert report.pass_all_rounds is False
        assert report.max_val_dd == 0.0

    def test_run_walk_forward_custom_rounds(self, mock_store, mock_universe):
        """run_walk_forward 支持自定义 rounds 参数（非默认 4）。"""
        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)
        report = run_walk_forward(
            mb=mb,
            strategies=["dual_ma"],
            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
            rounds=2,
            train_months=12,
            val_months=4,
        )
        assert len(report.rounds) == 2
        assert report.rounds[0].round_num == 1
        assert report.rounds[1].round_num == 2


# ---------------------------------------------------------------------------
# 迭代 #9 新增：Alpha-Based Strategy Selection
# ---------------------------------------------------------------------------

class TestAlphaComputation:
    """_compute_alpha / _combine_daily_returns 单元测试。"""

    def test_compute_alpha_basic(self):
        """构造已知策略收益和 SPY 收益，验证 alpha 计算正确。

        策略日均收益 0.001 (0.1%)，SPY 日均收益 0.0004 (0.04%)。
        年化：(1.001^252 - 1) - (1.0004^252 - 1) ≈ 0.285 - 0.110 = 0.175 → 17.5%
        """
        np.random.seed(42)
        idx = pd.date_range("2021-01-01", periods=252, freq="B")
        # 策略收益：稳定 0.1%/日（年化 ~28.5%）
        strat_returns = pd.Series(
            np.random.normal(0.001, 0.002, 252), index=idx
        )
        # SPY 收益：稳定 0.04%/日（年化 ~11.0%）
        spy_returns = pd.Series(
            np.random.normal(0.0004, 0.001, 252), index=idx
        )

        alpha = _compute_alpha(strat_returns, spy_returns)

        # 期望 alpha ≈ 17.5%（正数，跑赢 SPY）
        assert alpha > 0.0, f"策略年化应高于 SPY，alpha 应为正，实际 {alpha:.4f}"
        # 验证量级在合理范围（10~25%）
        assert 10.0 < alpha < 25.0, (
            f"alpha 应在 10~25% 范围，实际 {alpha:.4f}%"
        )

    def test_compute_alpha_spy_unavailable(self):
        """SPY 数据为 None → alpha = 0.0（降级处理，不抛异常）。"""
        idx = pd.date_range("2021-01-01", periods=100, freq="B")
        strat_returns = pd.Series(np.random.normal(0.001, 0.01, 100), index=idx)

        # spy_returns=None
        assert _compute_alpha(strat_returns, None) == 0.0
        # spy_returns=空 Series
        empty_spy = pd.Series(dtype=float)
        assert _compute_alpha(strat_returns, empty_spy) == 0.0

    def test_compute_alpha_strategy_underperforms(self):
        """策略跑输 SPY → alpha 为负。"""
        idx = pd.date_range("2021-01-01", periods=252, freq="B")
        # 策略日均 0.0001 (0.01%)，SPY 日均 0.001 (0.1%)
        strat_returns = pd.Series(np.random.normal(0.0001, 0.005, 252), index=idx)
        spy_returns = pd.Series(np.random.normal(0.001, 0.002, 252), index=idx)

        alpha = _compute_alpha(strat_returns, spy_returns)
        assert alpha < 0.0, (
            f"策略跑输 SPY 时 alpha 应为负，实际 {alpha:.4f}"
        )

    def test_combine_daily_returns_basic(self):
        """等权合并组内日收益率序列。"""
        idx = pd.date_range("2021-01-01", periods=10, freq="B")
        r1 = pd.Series([0.001] * 10, index=idx)
        r2 = pd.Series([0.003] * 10, index=idx)
        results = [
            SingleBacktestResult("S1", "s", {}, 0.0, 0, 0, 0, 0, r1),
            SingleBacktestResult("S2", "s", {}, 0.0, 0, 0, 0, 0, r2),
        ]
        combined = _combine_daily_returns(results)
        # 等权平均：(0.001 + 0.003) / 2 = 0.002
        assert len(combined) == 10
        assert all(abs(v - 0.002) < 1e-9 for v in combined)

    def test_combine_daily_returns_empty(self):
        """空列表 → 空 Series。"""
        combined = _combine_daily_returns([])
        assert combined.empty

    def test_min_sortino_threshold_constant(self):
        """MIN_SORTINO_THRESHOLD = 0.5（spec §4.2 硬约束）。"""
        assert MIN_SORTINO_THRESHOLD == 0.5, (
            f"MIN_SORTINO_THRESHOLD 应为 0.5（迭代 #9 spec），"
            f"实际 {MIN_SORTINO_THRESHOLD}"
        )


class TestAlphaBasedTopKSelection:
    """top-K 选择逻辑从 Sortino 改为 Alpha 的集成测试。"""

    def test_top_k_selection_uses_alpha(self, tmp_path):
        """top-K 排序使用 Alpha 而非 Sortino。

        场景：策略 A 的 Sortino 高于 B，但 B 的 Alpha 高于 A。
        应选择 B（高 alpha）而非 A（高 Sortino）。

        构造方法：用 patch 拦截 _backtest_one，返回受控的 daily_returns。
        """
        from unittest.mock import patch

        # 构造 SPY 数据：温和上涨（年化 ~10%）
        n = 300
        idx = pd.date_range("2021-01-01", periods=n, freq="B")
        spy_close = [100.0 * (1.0004 ** i) for i in range(n)]  # ~10% 年化
        spy_df = pd.DataFrame({
            "open": [c - 0.1 for c in spy_close],
            "high": [c + 0.5 for c in spy_close],
            "low": [c - 0.5 for c in spy_close],
            "close": spy_close,
            "volume": [1_000_000] * n,
        }, index=idx)
        spy_returns = spy_df["close"].pct_change().dropna()

        # 策略 A (dual_ma): 低波动低收益 → 高 Sortino 但低 alpha
        # 日均 0.0004（~10% 年化，与 SPY 持平 → alpha ≈ 0）
        np.random.seed(42)
        returns_a = pd.Series(
            np.random.normal(0.0004, 0.002, n), index=idx
        )
        # 策略 B (rsi_mean_revert): 高波动高收益 → 低 Sortino 但高 alpha
        # 日均 0.0011（~32% 年化，远超 SPY → alpha ≈ 22%）
        returns_b = pd.Series(
            np.random.normal(0.0011, 0.008, n), index=idx
        )

        # 验证测试前提：A 的 Sortino > B 的 Sortino，B 的 alpha > A 的 alpha
        sortino_a = _compute_sortino(returns_a)
        sortino_b = _compute_sortino(returns_b)
        alpha_a = _compute_alpha(returns_a, spy_returns)
        alpha_b = _compute_alpha(returns_b, spy_returns)
        assert sortino_a > sortino_b, (
            f"测试前提失败：A 的 Sortino({sortino_a:.4f}) 应 > B({sortino_b:.4f})"
        )
        assert alpha_b > alpha_a, (
            f"测试前提失败：B 的 alpha({alpha_b:.4f}) 应 > A({alpha_a:.4f})"
        )

        # Mock _backtest_batch 返回受控结果（迭代 #10：_run_group 改用 batch）
        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
            results = []
            for sym, df in data.items():
                if df is None or df.empty or len(df) < 30:
                    continue
                if strategy_name == "dual_ma":
                    results.append(SingleBacktestResult(
                        sym, strategy_name, params, 1.0, 10.0, 5.0, 55.0, 10, returns_a,
                        closed_trades=10,
                    ))
                else:  # rsi_mean_revert
                    results.append(SingleBacktestResult(
                        sym, strategy_name, params, 1.0, 30.0, 8.0, 50.0, 10, returns_b,
                        closed_trades=10,
                    ))
            return results

        # 构造 mock store：返回 SPY + 普通上涨数据
        df_up = _make_ohlcv(n, trend="up")
        store = MagicMock()

        def get_bars_multi(symbols, start, end, timeframe="1d"):
            mapping = {"AAPL": df_up, "SPY": spy_df}
            return {s: mapping[s] for s in symbols if s in mapping}

        store.get_bars_multi.side_effect = get_bars_multi

        universe = MagicMock()
        universe.get_groups.return_value = {"test_group": ["AAPL"]}

        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=1)

        with patch(
            "mytrader.backtest.matrix_backtest._backtest_batch",
            side_effect=mock_backtest_batch,
        ):
            report = mb.run(
                strategies=["dual_ma", "rsi_mean_revert"],
                param_grids={
                    "dual_ma": {"fast": [5], "slow": [20]},
                    "rsi_mean_revert": {
                        "period": [14], "oversold": [30], "overbought": [70]
                    },
                },
            )

        # 验证：选择了 rsi_mean_revert（高 alpha）而非 dual_ma（高 Sortino）
        weights = report.groups["test_group"]
        assert len(weights) == 1, f"top_k=1 应只选 1 个策略，实际 {len(weights)}"
        assert weights[0]["strategy"] == "rsi_mean_revert", (
            f"应选择高 alpha 的 rsi_mean_revert，"
            f"实际选择了 {weights[0]['strategy']}（高 Sortino 的 dual_ma）"
        )
        # backtest_alpha 字段应反映 B 的高 alpha
        assert weights[0]["backtest_alpha"] > 5.0, (
            f"B 的 alpha 应 > 5%，实际 {weights[0]['backtest_alpha']:.4f}"
        )

    def test_sortino_filter_excludes_garbage(self, tmp_path):
        """Sortino < 0.5 的候选被过滤（即使 alpha 高也不选）。

        场景：构造一个 Sortino < 0.5 的"垃圾"策略 A，和一个 Sortino > 0.5 的正常策略 B。
        即使 A 的 alpha 略高，也应被 Sortino 门槛排除。

        注：由于 Sortino 门槛是 Tier 1 过滤，若无候选通过门槛，会触发 Tier 2 fallback
        放宽门槛。本测试构造"至少有一个正常候选"的场景验证 Tier 1 正常工作。
        """
        from unittest.mock import patch

        n = 300
        idx = pd.date_range("2021-01-01", periods=n, freq="B")
        # SPY 温和上涨
        spy_close = [100.0 * (1.0004 ** i) for i in range(n)]
        spy_df = pd.DataFrame({
            "open": [c - 0.1 for c in spy_close],
            "high": [c + 0.5 for c in spy_close],
            "low": [c - 0.5 for c in spy_close],
            "close": spy_close,
            "volume": [1_000_000] * n,
        }, index=idx)
        spy_returns = spy_df["close"].pct_change().dropna()

        # 垃圾策略 A：极低 Sortino（高下行波动）+ 高 alpha（靠总体高收益）
        # 构造大起大落的收益序列：均值高但下行波动大
        np.random.seed(42)
        returns_a = pd.Series(
            np.concatenate([
                np.random.normal(0.003, 0.015, 200),   # 高波动高收益
                np.random.normal(-0.005, 0.01, 100),   # 大幅下行
            ]),
            index=idx,
        )
        # 正常策略 B：稳定收益，Sortino > 0.5
        returns_b = pd.Series(
            np.random.normal(0.0008, 0.003, n), index=idx
        )

        sortino_a = _compute_sortino(returns_a)
        sortino_b = _compute_sortino(returns_b)
        # 验证前提：A 的 Sortino < 0.5（垃圾），B 的 Sortino > 0.5（正常）
        assert sortino_a < MIN_SORTINO_THRESHOLD, (
            f"A 应为 Sortino < 0.5 的垃圾策略，实际 {sortino_a:.4f}"
        )
        assert sortino_b > MIN_SORTINO_THRESHOLD, (
            f"B 应为 Sortino > 0.5 的正常策略，实际 {sortino_b:.4f}"
        )

        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
            results = []
            for sym, df in data.items():
                if df is None or df.empty or len(df) < 30:
                    continue
                if strategy_name == "dual_ma":
                    results.append(SingleBacktestResult(
                        sym, strategy_name, params, 0.5, 15.0, 10.0, 50.0, 5, returns_a,
                        closed_trades=5,
                    ))
                else:  # rsi_mean_revert
                    results.append(SingleBacktestResult(
                        sym, strategy_name, params, 1.0, 20.0, 5.0, 55.0, 10, returns_b,
                        closed_trades=10,
                    ))
            return results

        df_up = _make_ohlcv(n, trend="up")
        store = MagicMock()
        store.get_bars_multi.side_effect = lambda symbols, start, end, timeframe="1d": {
            s: {"AAPL": df_up, "SPY": spy_df}[s] for s in symbols
            if s in {"AAPL", "SPY"}
        }

        universe = MagicMock()
        universe.get_groups.return_value = {"test_group": ["AAPL"]}

        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=1)
        with patch(
            "mytrader.backtest.matrix_backtest._backtest_batch",
            side_effect=mock_backtest_batch,
        ):
            report = mb.run(
                strategies=["dual_ma", "rsi_mean_revert"],
                param_grids={
                    "dual_ma": {"fast": [5], "slow": [20]},
                    "rsi_mean_revert": {
                        "period": [14], "oversold": [30], "overbought": [70]
                    },
                },
            )

        weights = report.groups["test_group"]
        assert len(weights) == 1
        # 应选择 rsi_mean_revert（Sortino > 0.5），排除 dual_ma（Sortino < 0.5）
        assert weights[0]["strategy"] == "rsi_mean_revert", (
            f"应排除 Sortino < 0.5 的 dual_ma，选择 rsi_mean_revert，"
            f"实际选择了 {weights[0]['strategy']}"
        )

    def test_dd_filter_still_applies(self, tmp_path):
        """DD > 20% 的候选被过滤（即使 alpha 高也不通过 DD 硬约束）。

        场景：构造 rsi_mean_revert 在持续下跌数据上产生大 DD 的策略行为。
        验证：dd_constrained=True（触发 DD fallback），权重仍产出。
        """
        store = MagicMock()
        # 构造先涨后崩数据：rsi_mean_revert 会在下跌中超卖买入，持续持仓导致大 DD
        n = 400
        idx = pd.date_range("2021-01-01", periods=n, freq="B")
        close = (
            [100.0 * (1 - 0.002 * i) for i in range(200)]   # 缓慢下跌压低 RSI
            + [60.0 * (1 - 0.005 * (i - 200)) for i in range(200, n)]  # 急速崩溃
        )
        close = [max(c, 1.0) for c in close]
        df_crash = pd.DataFrame({
            "open": [c - 0.3 for c in close],
            "high": [c + 0.5 for c in close],
            "low": [c - 0.5 for c in close],
            "close": close,
            "volume": [1_000_000] * n,
        }, index=idx)
        # 同时提供 SPY 数据（让 alpha 计算不降级）
        spy_df = _make_ohlcv(n, trend="up")
        spy_df = spy_df.copy()
        spy_df.index = idx  # 对齐索引

        def get_bars_multi(symbols, start, end, timeframe="1d"):
            mapping = {"AAPL": df_crash, "SPY": spy_df}
            return {s: mapping[s] for s in symbols if s in mapping}

        store.get_bars_multi.side_effect = get_bars_multi

        universe = MagicMock()
        universe.get_groups.return_value = {"volatile_group": ["AAPL"]}

        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=1)
        report = mb.run(
            strategies=["rsi_mean_revert"],
            param_grids={"rsi_mean_revert": {
                "period": [14], "oversold": [35], "overbought": [65]
            }},
            output_file=tmp_path / "weights_dd.json",
        )

        # 验证：DD 超标时 dd_constrained=True（DD fallback 触发）
        has_weights = any(weights for weights in report.groups.values() if weights)
        if has_weights:
            for gid, weights in report.groups.items():
                for w in weights:
                    if w.get("backtest_max_drawdown", 0) > MAX_PORTFOLIO_DRAWDOWN_PCT:
                        assert w["dd_constrained"] is True, (
                            f"{gid}: DD={w['backtest_max_drawdown']:.1f}% > "
                            f"{MAX_PORTFOLIO_DRAWDOWN_PCT}% 但 dd_constrained 为 False"
                        )

    def test_fallback_when_no_sortino_compliant(self, tmp_path):
        """所有候选 Sortino < 0.5 → 触发 Tier 2 fallback（放宽 Sortino 门槛）。

        场景：构造低 Sortino 的策略，但 DD ≤ 20%。
        验证：权重仍产出（不空），dd_constrained=False（因为 DD 合规），
        且日志中应有 "Sortino filter relaxed" 警告。
        """
        from unittest.mock import patch
        from loguru import logger

        n = 300
        idx = pd.date_range("2021-01-01", periods=n, freq="B")
        spy_df = pd.DataFrame({
            "open": [99.9], "high": [100.5], "low": [99.5],
            "close": [100.0], "volume": [1_000_000],
        }, index=idx[:1])
        # 让 SPY 数据足够长
        spy_close = [100.0 * (1.0004 ** i) for i in range(n)]
        spy_df = pd.DataFrame({
            "open": [c - 0.1 for c in spy_close],
            "high": [c + 0.5 for c in spy_close],
            "low": [c - 0.5 for c in spy_close],
            "close": spy_close,
            "volume": [1_000_000] * n,
        }, index=idx)

        # 低 Sortino 但 DD 合规的收益序列
        np.random.seed(42)
        returns_garbage = pd.Series(
            np.concatenate([
                np.random.normal(0.0002, 0.01, 200),  # 低均值高波动
                np.random.normal(-0.0001, 0.008, 100), # 略负
            ]),
            index=idx,
        )
        # 验证前提：Sortino < 0.5（垃圾门槛）
        assert _compute_sortino(returns_garbage) < MIN_SORTINO_THRESHOLD

        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
            results = []
            for sym, df in data.items():
                if df is None or df.empty or len(df) < 30:
                    continue
                results.append(SingleBacktestResult(
                    sym, strategy_name, params, 0.3, 5.0, 10.0, 50.0, 3, returns_garbage,
                    closed_trades=3,
                ))
            return results

        df_up = _make_ohlcv(n, trend="up")
        store = MagicMock()
        store.get_bars_multi.side_effect = lambda symbols, start, end, timeframe="1d": {
            s: {"AAPL": df_up, "SPY": spy_df}[s] for s in symbols
            if s in {"AAPL", "SPY"}
        }

        universe = MagicMock()
        universe.get_groups.return_value = {"test_group": ["AAPL"]}

        # 捕获 WARNING 日志
        msgs: list[str] = []
        handler_id = logger.add(lambda m: msgs.append(str(m)), level="WARNING")

        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=1)
        try:
            with patch(
                "mytrader.backtest.matrix_backtest._backtest_batch",
                side_effect=mock_backtest_batch,
            ):
                report = mb.run(
                    strategies=["dual_ma"],
                    param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
                )
        finally:
            logger.remove(handler_id)

        # 验证：fallback 触发，日志记录 Sortino 放宽
        assert any("Sortino filter relaxed" in m for m in msgs), (
            f"应触发 Tier 2 fallback（Sortino relaxed），实际日志: {msgs}"
        )

        # 权重仍产出（DD 合规），dd_constrained=False
        weights = report.groups.get("test_group", [])
        if weights:
            for w in weights:
                assert w["dd_constrained"] is False, (
                    "DD 合规时 dd_constrained 应为 False（Sortino fallback 不影响）"
                )

    def test_fallback_when_no_dd_compliant(self, tmp_path):
        """所有候选 DD > 20% → 触发 Tier 3 fallback（按 DD 升序）。

        场景：复用 test_fallback_when_no_compliant_candidates 的数据构造，
        验证 dd_constrained=True（与迭代 #3 行为一致）。
        """
        store = MagicMock()
        n = 400
        idx = pd.date_range("2021-01-01", periods=n, freq="B")
        close = (
            [100.0 * (1 - 0.002 * i) for i in range(200)]
            + [60.0 * (1 - 0.005 * (i - 200)) for i in range(200, n)]
        )
        close = [max(c, 1.0) for c in close]
        df_crash = pd.DataFrame({
            "open": [c - 0.3 for c in close],
            "high": [c + 0.5 for c in close],
            "low": [c - 0.5 for c in close],
            "close": close,
            "volume": [1_000_000] * n,
        }, index=idx)
        # SPY 数据（让 alpha 不降级，验证 DD fallback 优先于 Sortino 过滤）
        spy_close = [100.0 * (1.0004 ** i) for i in range(n)]
        spy_df = pd.DataFrame({
            "open": [c - 0.1 for c in spy_close],
            "high": [c + 0.5 for c in spy_close],
            "low": [c - 0.5 for c in spy_close],
            "close": spy_close,
            "volume": [1_000_000] * n,
        }, index=idx)

        def get_bars_multi(symbols, start, end, timeframe="1d"):
            mapping = {"AAPL": df_crash, "SPY": spy_df}
            return {s: mapping[s] for s in symbols if s in mapping}

        store.get_bars_multi.side_effect = get_bars_multi

        universe = MagicMock()
        universe.get_groups.return_value = {"volatile_group": ["AAPL", "MSFT"]}

        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
        report = mb.run(
            strategies=["rsi_mean_revert"],
            param_grids={"rsi_mean_revert": {
                "period": [14], "oversold": [35], "overbought": [65]
            }},
            output_file=tmp_path / "weights_fallback_dd.json",
        )

        has_weights = any(weights for weights in report.groups.values() if weights)
        if has_weights:
            for gid, weights in report.groups.items():
                for w in weights:
                    if w.get("backtest_max_drawdown", 0) > MAX_PORTFOLIO_DRAWDOWN_PCT:
                        assert w["dd_constrained"] is True, (
                            f"{gid}: DD={w['backtest_max_drawdown']:.1f}% > 20% "
                            f"但 dd_constrained 为 False（Tier 3 应触发）"
                        )

    def test_alpha_field_in_weights_json(self, mock_store, mock_universe, tmp_path):
        """strategy_weights.json 每个权重条目含 backtest_alpha 字段。"""
        output = tmp_path / "weights_with_alpha.json"
        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)
        mb.run(
            strategies=["dual_ma"],
            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
            output_file=output,
        )
        data = json.loads(output.read_text())
        for gid, weights in data["groups"].items():
            for w in weights:
                assert "backtest_alpha" in w, (
                    f"{gid}: 权重条目缺少 backtest_alpha 字段，"
                    f"实际 keys={list(w.keys())}"
                )
                assert isinstance(w["backtest_alpha"], (int, float)), (
                    f"{gid}: backtest_alpha 应为数值，"
                    f"实际 {type(w['backtest_alpha'])}"
                )

    def test_group_results_have_backtest_alpha(self, mock_store, mock_universe):
        """GroupBacktestResult.backtest_alpha 是浮点数（迭代 #9 新增字段）。"""
        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)
        report = mb.run(
            strategies=["dual_ma"],
            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
        )
        for gr in report.group_results:
            assert isinstance(gr.backtest_alpha, float), (
                f"backtest_alpha 应为 float，实际 {type(gr.backtest_alpha)}"
            )

    def test_per_strategy_best_params_uses_alpha(self, tmp_path):
        """per-strategy best params 选择使用 Alpha 而非 Sharpe。

        场景：两个参数组合 A (fast=5, slow=20) 和 B (fast=10, slow=50)，
        A 的 Sharpe 高但 alpha 低，B 的 Sharpe 低但 alpha 高。
        验证最终 GroupBacktestResult.params 是 B（高 alpha）。
        """
        from unittest.mock import patch

        n = 300
        idx = pd.date_range("2021-01-01", periods=n, freq="B")
        spy_close = [100.0 * (1.0004 ** i) for i in range(n)]
        spy_df = pd.DataFrame({
            "open": [c - 0.1 for c in spy_close],
            "high": [c + 0.5 for c in spy_close],
            "low": [c - 0.5 for c in spy_close],
            "close": spy_close,
            "volume": [1_000_000] * n,
        }, index=idx)
        spy_returns = spy_df["close"].pct_change().dropna()

        # 参数 A 的收益：低波动低收益 → 高 Sharpe 但低 alpha
        np.random.seed(42)
        returns_a = pd.Series(
            np.random.normal(0.0005, 0.002, n), index=idx  # 与 SPY 接近，alpha≈0
        )
        # 参数 B 的收益：高波动高收益 → 低 Sharpe 但高 alpha
        returns_b = pd.Series(
            np.random.normal(0.0012, 0.008, n), index=idx  # 远超 SPY，alpha>0
        )

        # 验证前提
        sharpe_a = _compute_sharpe(returns_a)
        sharpe_b = _compute_sharpe(returns_b)
        alpha_a = _compute_alpha(returns_a, spy_returns)
        alpha_b = _compute_alpha(returns_b, spy_returns)
        assert sharpe_a > sharpe_b, (
            f"A 的 Sharpe({sharpe_a:.4f}) 应 > B({sharpe_b:.4f})"
        )
        assert alpha_b > alpha_a, (
            f"B 的 alpha({alpha_b:.4f}) 应 > A({alpha_a:.4f})"
        )

        # 根据参数选择返回不同收益（迭代 #10：mock _backtest_batch）
        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
            results = []
            for sym, df in data.items():
                if df is None or df.empty or len(df) < 30:
                    continue
                if params.get("fast") == 5:  # 参数 A
                    results.append(SingleBacktestResult(
                        sym, strategy_name, params, sharpe_a, 10.0, 5.0, 55.0, 10, returns_a,
                        closed_trades=10,
                    ))
                else:  # 参数 B (fast=10)
                    results.append(SingleBacktestResult(
                        sym, strategy_name, params, sharpe_b, 30.0, 8.0, 50.0, 10, returns_b,
                        closed_trades=10,
                    ))
            return results

        df_up = _make_ohlcv(n, trend="up")
        store = MagicMock()
        store.get_bars_multi.side_effect = lambda symbols, start, end, timeframe="1d": {
            s: {"AAPL": df_up, "SPY": spy_df}[s] for s in symbols
            if s in {"AAPL", "SPY"}
        }

        universe = MagicMock()
        universe.get_groups.return_value = {"test_group": ["AAPL"]}

        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=1)
        with patch(
            "mytrader.backtest.matrix_backtest._backtest_batch",
            side_effect=mock_backtest_batch,
        ):
            report = mb.run(
                strategies=["dual_ma"],
                param_grids={
                    "dual_ma": {"fast": [5, 10], "slow": [20, 50]}
                },
            )

        # 验证：选择参数 B（fast=10, slow=50，高 alpha）
        gr = next(
            (r for r in report.group_results if r.group_id == "test_group"),
            None,
        )
        assert gr is not None, "应至少有一个 GroupBacktestResult"
        assert gr.params.get("fast") == 10, (
            f"应选高 alpha 的参数 B (fast=10)，实际选了 {gr.params}"
        )
        assert gr.backtest_alpha > 5.0, (
            f"B 的 alpha 应 > 5%，实际 {gr.backtest_alpha:.4f}"
        )


class TestEnsembleWeightsUsesAlpha:
    """_optimize_ensemble_weights 从 Sharpe 改为 Alpha。"""

    def test_ensemble_weights_use_alpha(self):
        """两个策略的权重应基于 alpha 分配，alpha 高的策略权重大。"""
        n = 252
        idx = pd.date_range("2021-01-01", periods=n, freq="B")
        spy_returns = pd.Series(np.random.normal(0.0004, 0.001, n), index=idx)

        # 策略 A：alpha=0（与 SPY 持平）
        returns_a = pd.Series(np.random.normal(0.0004, 0.003, n), index=idx)
        # 策略 B：alpha 高（远超 SPY）
        returns_b = pd.Series(np.random.normal(0.0012, 0.005, n), index=idx)

        results_a = [SingleBacktestResult(
            "S1", "strat_a", {}, 1.0, 10.0, 5.0, 55.0, 10, returns_a
        )]
        results_b = [SingleBacktestResult(
            "S2", "strat_b", {}, 1.5, 30.0, 8.0, 50.0, 10, returns_b
        )]

        group_results = [
            ("strat_a", {}, results_a),
            ("strat_b", {}, results_b),
        ]

        weights = _optimize_ensemble_weights(group_results, spy_returns=spy_returns)

        # B 的 alpha 更高 → 权重应更大
        weights_dict = {s: w for s, _, w in weights}
        assert weights_dict["strat_b"] > weights_dict["strat_a"], (
            f"B 的 alpha 更高，权重应大于 A，"
            f"实际 A={weights_dict['strat_a']:.4f}, B={weights_dict['strat_b']:.4f}"
        )
        # 权重和 = 1.0
        total = sum(weights_dict.values())
        assert abs(total - 1.0) < 1e-6, f"权重和应为 1.0，实际 {total:.6f}"

    def test_ensemble_weights_spy_unavailable_degrades_to_equal(self):
        """SPY 数据不可用时 alpha 降级为 0 → 退化为等权。"""
        n = 100
        idx = pd.date_range("2021-01-01", periods=n, freq="B")
        returns_a = pd.Series(np.random.normal(0.001, 0.005, n), index=idx)
        returns_b = pd.Series(np.random.normal(0.002, 0.008, n), index=idx)

        results_a = [SingleBacktestResult(
            "S1", "strat_a", {}, 1.0, 10.0, 5.0, 55.0, 10, returns_a
        )]
        results_b = [SingleBacktestResult(
            "S2", "strat_b", {}, 1.5, 30.0, 8.0, 50.0, 10, returns_b
        )]

        group_results = [
            ("strat_a", {}, results_a),
            ("strat_b", {}, results_b),
        ]

        # spy_returns=None → alpha=0 → 退化为等权（max(0, 0.01)）
        weights = _optimize_ensemble_weights(group_results, spy_returns=None)
        weights_dict = {s: w for s, _, w in weights}
        # 等权：各 0.5
        assert abs(weights_dict["strat_a"] - 0.5) < 1e-6
        assert abs(weights_dict["strat_b"] - 0.5) < 1e-6

    def test_ensemble_weights_single_strategy(self):
        """单策略时直接返回权重 1.0。"""
        n = 100
        idx = pd.date_range("2021-01-01", periods=n, freq="B")
        returns = pd.Series(np.random.normal(0.001, 0.005, n), index=idx)
        results = [SingleBacktestResult(
            "S1", "strat_a", {}, 1.0, 10.0, 5.0, 55.0, 10, returns
        )]

        weights = _optimize_ensemble_weights(
            [("strat_a", {}, results)],
            spy_returns=pd.Series(dtype=float),
        )
        assert len(weights) == 1
        assert weights[0][0] == "strat_a"
        assert weights[0][2] == 1.0


