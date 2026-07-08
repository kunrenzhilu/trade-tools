"""迭代 #12：alpha>0 硬门槛测试（Reject Negative-Alpha Strategies）。

迭代 #16 更新：alpha gate 从 alpha>0 放宽至 alpha > ALPHA_GATE_THRESHOLD (-2%)。
动机：SPX 成分股 vs SPY benchmark 存在结构性近零 alpha，严格 alpha>0 门槛导致
4/6 组空仓。放宽至 -2% 仍过滤"灾难性跑输"，但保留"小幅跑输 SPY 但 Sortino/DD
优秀"的候选。WF OOS 校验仍用 -5% 单轮下限 + avg>0 汇总门槛，不削弱 OOS 验证。

验证：
    1. `GroupBacktestResult.no_positive_alpha` 字段默认 False
    2. `_run_group` 在 candidates 构建后、Tier 1 剔除 alpha ≤ ALPHA_GATE_THRESHOLD 的候选
    3. 全负 alpha（< -2%）组返回空权重 + `no_positive_alpha=True` 标记
    4. 混合 alpha 组只保留 alpha > -2% 的候选
    5. `_optimize_ensemble_weights` 负 alpha 策略权重为 0（不再 max(0.01) 掩盖）
    6. 全负 alpha ensemble 退化为等权 + WARNING（防御性 fallback）
    7. 健全性门槛 + alpha 门槛协同工作
    8. [Iter #16] ALPHA_GATE_THRESHOLD 常量存在且等于 -2.0
    9. [Iter #16] alpha=-1% 通过 gate（在 -2% 与 0% 之间）
    10. [Iter #16] alpha=-5% 仍被拒绝
    11. [Iter #16] alpha=-2.0% 边界值被拒绝（使用 > 严格比较）
    12. [Iter #16] alpha=+1% 仍通过（无回归）
    13. [Iter #16] 集成场景：SPX 组 alpha=-1.5% 策略入选 tier1
    14. [Iter #16] 单策略 ensemble 负 alpha（> -2%）仍得 weight=1.0（早返回）

背景见 `iterations/iteration_16/spec.md` + `.codebuddy/notes/experience.md` #8。
"""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from mytrader.backtest.matrix_backtest import (
    ALPHA_GATE_THRESHOLD,
    GroupBacktestResult,
    MatrixBacktest,
    MatrixBacktestReport,
    SingleBacktestResult,
    _combine_daily_returns,
    _compute_alpha,
    _optimize_ensemble_weights,
)


# ---------------------------------------------------------------------------
# Test data generators（与 test_degenerate_filter.py / test_matrix_backtest.py 同风格）
# ---------------------------------------------------------------------------

def _make_ohlcv(
    n: int = 300,
    trend: str = "up",
    start: str = "2021-01-01",
    seed: int | None = None,
) -> pd.DataFrame:
    """生成测试 OHLCV 数据。"""
    idx = pd.date_range(start, periods=n, freq="B")
    if trend == "up":
        close = np.array([100.0 + i * 0.1 for i in range(n)])
    elif trend == "down":
        close = np.array([100.0 - i * 0.05 for i in range(n)])
    elif trend == "random":
        rng = np.random.default_rng(seed if seed is not None else 42)
        steps = rng.normal(0, 0.5, n)
        close = np.cumsum(np.concatenate([[100.0], steps]))[1:]
    else:
        raise ValueError(f"unknown trend: {trend}")

    return pd.DataFrame(
        {
            "open":   close - 0.5,
            "high":   close + 1.0,
            "low":    close - 1.0,
            "close":  close,
            "volume": [1_000_000] * n,
        },
        index=idx,
    )


def _make_spy_df(n: int = 300, annual_return: float = 0.10) -> pd.DataFrame:
    """生成 SPY benchmark 数据，年化收益可调。

    annual_return=0.10 → 日均收益 ≈ 0.00038（对数展开近似）。
    annual_return=0.30 → 日均收益 ≈ 0.00107（高涨幅，策略难跑赢）。
    """
    idx = pd.date_range("2021-01-01", periods=n, freq="B")
    daily_rate = (1.0 + annual_return) ** (1.0 / 252) - 1.0
    close = [100.0 * ((1.0 + daily_rate) ** i) for i in range(n)]
    return pd.DataFrame(
        {
            "open":   [c - 0.1 for c in close],
            "high":   [c + 0.5 for c in close],
            "low":    [c - 0.5 for c in close],
            "close":  close,
            "volume": [1_000_000] * n,
        },
        index=idx,
    )


def _make_store_with_spy(
    symbols_data: dict[str, pd.DataFrame],
    spy_df: pd.DataFrame,
) -> MagicMock:
    """构造 Mock MarketDataStore，含 SPY benchmark 数据。"""
    store = MagicMock()
    mapping = dict(symbols_data)
    mapping["SPY"] = spy_df

    def get_bars_multi(symbols, start, end, timeframe="1d"):
        return {s: mapping[s] for s in symbols if s in mapping}

    store.get_bars_multi.side_effect = get_bars_multi
    return store


def _make_mock_universe(groups: dict[str, list[str]]) -> MagicMock:
    """构造 Mock UniverseManager。"""
    universe = MagicMock()
    universe.get_groups.return_value = groups
    return universe


def _make_result(
    symbol: str,
    strategy: str,
    daily_returns: pd.Series,
    closed_trades: int = 10,
) -> SingleBacktestResult:
    """快捷构造 SingleBacktestResult（带默认字段）。"""
    return SingleBacktestResult(
        symbol=symbol,
        strategy=strategy,
        params={},
        sharpe=1.0,
        total_return_pct=10.0,
        max_drawdown_pct=5.0,
        win_rate_pct=55.0,
        total_trades=10,
        daily_returns=daily_returns,
        closed_trades=closed_trades,
    )


# ---------------------------------------------------------------------------
# Test 1: no_positive_alpha 字段
# ---------------------------------------------------------------------------

class TestNoPositiveAlphaField:
    """GroupBacktestResult.no_positive_alpha 字段测试。"""

    def test_no_positive_alpha_field_default_false(self):
        """GroupBacktestResult.no_positive_alpha 默认 False。"""
        gr = GroupBacktestResult(
            group_id="g", strategy="s", params={}, portfolio_sharpe=0.0,
            avg_total_return_pct=0.0, avg_max_drawdown_pct=0.0,
            avg_win_rate_pct=0.0, symbol_count=0,
        )
        assert hasattr(gr, "no_positive_alpha"), (
            "GroupBacktestResult 必须有 no_positive_alpha 字段"
        )
        assert gr.no_positive_alpha is False, (
            "no_positive_alpha 默认应为 False"
        )

    def test_no_positive_alpha_field_settable(self):
        """no_positive_alpha 可被设置为 True。"""
        gr = GroupBacktestResult(
            group_id="g", strategy="s", params={}, portfolio_sharpe=0.0,
            avg_total_return_pct=0.0, avg_max_drawdown_pct=0.0,
            avg_win_rate_pct=0.0, symbol_count=0,
            no_positive_alpha=True,
        )
        assert gr.no_positive_alpha is True


# ---------------------------------------------------------------------------
# Test 2-3: _run_group alpha>0 门槛集成
# ---------------------------------------------------------------------------

class TestRunGroupAlphaGate:
    """_run_group alpha>0 硬门槛集成测试。"""

    def test_positive_alpha_candidates_pass(self):
        """全正 alpha 候选组正常产出权重，no_positive_alpha=False。

        场景：两个策略都跑赢 SPY（正 alpha），健全性门槛通过。
        验证：权重正常产出，no_positive_alpha 不被标记。
        """
        n = 300
        idx = pd.date_range("2021-01-01", periods=n, freq="B")
        # SPY 年化 ~10%
        spy_df = _make_spy_df(n, annual_return=0.10)
        spy_returns = spy_df["close"].pct_change().dropna()

        # 策略收益：日均 0.0012（年化 ~35%）→ 正 alpha
        np.random.seed(42)
        returns_a = pd.Series(np.random.normal(0.0012, 0.005, n), index=idx)
        returns_b = pd.Series(np.random.normal(0.0010, 0.004, n), index=idx)

        # 验证前提：两个策略 alpha 都 > 0
        alpha_a = _compute_alpha(returns_a, spy_returns)
        alpha_b = _compute_alpha(returns_b, spy_returns)
        assert alpha_a > 0, f"策略 A alpha 应 > 0，实际 {alpha_a:.4f}"
        assert alpha_b > 0, f"策略 B alpha 应 > 0，实际 {alpha_b:.4f}"

        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
            results = []
            for sym, df in data.items():
                if df is None or df.empty or len(df) < 30:
                    continue
                returns = returns_a if strategy_name == "dual_ma" else returns_b
                results.append(_make_result(sym, strategy_name, returns, closed_trades=10))
            return results

        df_up = _make_ohlcv(n, trend="up")
        store = _make_store_with_spy({"AAA": df_up, "BBB": df_up}, spy_df)
        universe = _make_mock_universe({"test_group": ["AAA", "BBB"]})

        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
        report = MatrixBacktestReport(
            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
            backtest_window="2021-01-01 ~ 2022-01-01",
            groups={},
        )

        with patch(
            "mytrader.backtest.matrix_backtest._backtest_batch",
            side_effect=mock_backtest_batch,
        ):
            weights = mb._run_group(
                group_id="test_group",
                symbols=["AAA", "BBB"],
                start=date(2021, 1, 1),
                end=date(2022, 1, 1),
                strategies=["dual_ma", "rsi_mean_revert"],
                param_grids={
                    "dual_ma": {"fast": [5], "slow": [20]},
                    "rsi_mean_revert": {
                        "period": [14], "oversold": [30], "overbought": [70]
                    },
                },
                report=report,
            )

        # 正 alpha 候选 → 权重正常产出
        assert len(weights) > 0, (
            f"全正 alpha 组应产出权重，实际 weights={weights}"
        )
        # no_positive_alpha 不应被标记
        for gr in report.group_results:
            if gr.group_id == "test_group":
                assert gr.no_positive_alpha is False, (
                    "全正 alpha 组不应标记 no_positive_alpha=True"
                )
        # report.warnings 不含 no_positive_alpha
        warning_text = " ".join(report.warnings)
        assert "no_positive_alpha" not in warning_text, (
            f"全正 alpha 组不应有 no_positive_alpha 警告，实际 warnings={report.warnings}"
        )

    def test_all_negative_alpha_group_empty(self):
        """全负 alpha 组返回空权重 + no_positive_alpha=True 标记。

        场景：两个策略都跑输 SPY（负 alpha），健全性门槛通过。
        验证：返回空 weights，report.warnings 含 no_positive_alpha 标记，
              group_results 条目 no_positive_alpha=True。
        """
        n = 300
        idx = pd.date_range("2021-01-01", periods=n, freq="B")
        # SPY 年化 ~30%（高涨幅，策略难跑赢）
        spy_df = _make_spy_df(n, annual_return=0.30)
        spy_returns = spy_df["close"].pct_change().dropna()

        # 策略收益：日均 0.0003（年化 ~8%）→ 负 alpha（跑输 SPY 30%）
        np.random.seed(42)
        returns_a = pd.Series(np.random.normal(0.0003, 0.005, n), index=idx)
        returns_b = pd.Series(np.random.normal(0.0002, 0.004, n), index=idx)

        # 验证前提：两个策略 alpha 都 < 0
        alpha_a = _compute_alpha(returns_a, spy_returns)
        alpha_b = _compute_alpha(returns_b, spy_returns)
        assert alpha_a < 0, f"策略 A alpha 应 < 0，实际 {alpha_a:.4f}"
        assert alpha_b < 0, f"策略 B alpha 应 < 0，实际 {alpha_b:.4f}"

        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
            results = []
            for sym, df in data.items():
                if df is None or df.empty or len(df) < 30:
                    continue
                returns = returns_a if strategy_name == "dual_ma" else returns_b
                results.append(_make_result(sym, strategy_name, returns, closed_trades=10))
            return results

        df_up = _make_ohlcv(n, trend="up")
        store = _make_store_with_spy({"AAA": df_up, "BBB": df_up}, spy_df)
        universe = _make_mock_universe({"test_group": ["AAA", "BBB"]})

        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
        report = MatrixBacktestReport(
            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
            backtest_window="2021-01-01 ~ 2022-01-01",
            groups={},
        )

        with patch(
            "mytrader.backtest.matrix_backtest._backtest_batch",
            side_effect=mock_backtest_batch,
        ):
            weights = mb._run_group(
                group_id="test_group",
                symbols=["AAA", "BBB"],
                start=date(2021, 1, 1),
                end=date(2022, 1, 1),
                strategies=["dual_ma", "rsi_mean_revert"],
                param_grids={
                    "dual_ma": {"fast": [5], "slow": [20]},
                    "rsi_mean_revert": {
                        "period": [14], "oversold": [30], "overbought": [70]
                    },
                },
                report=report,
            )

        # 全负 alpha → 空权重
        assert weights == [], (
            f"全负 alpha 组应返回空权重，实际 weights={weights}"
        )
        # report.warnings 含 no_positive_alpha 标记
        warning_text = " ".join(report.warnings)
        assert "no_positive_alpha" in warning_text, (
            f"report.warnings 应含 no_positive_alpha 标记，"
            f"实际 warnings={report.warnings}"
        )
        assert "test_group" in warning_text
        # group_results 条目被标记 no_positive_alpha=True
        test_group_results = [
            gr for gr in report.group_results if gr.group_id == "test_group"
        ]
        assert len(test_group_results) > 0, (
            "test_group 应在 report.group_results 中有存档条目（供审计追溯）"
        )
        for gr in test_group_results:
            assert gr.no_positive_alpha is True, (
                f"test_group 的 no_positive_alpha 应为 True，"
                f"实际 {gr.no_positive_alpha}"
            )
            # no_valid_strategy 应仍为 False（健全性门槛没触发）
            assert gr.no_valid_strategy is False, (
                "全负 alpha 但非退化组，no_valid_strategy 应为 False"
            )

    def test_negative_alpha_excluded(self):
        """混合 alpha 候选组：负 alpha 不出现在 weights_list。

        场景：dual_ma 负 alpha，rsi_mean_revert 正 alpha。
        验证：只有 rsi_mean_revert 出现在 weights，dual_ma 被 alpha 门槛剔除。
        """
        n = 300
        idx = pd.date_range("2021-01-01", periods=n, freq="B")
        spy_df = _make_spy_df(n, annual_return=0.10)
        spy_returns = spy_df["close"].pct_change().dropna()

        # dual_ma：日均 0.0002（年化 ~5%）→ 负 alpha（跑输 SPY 10%）
        np.random.seed(42)
        returns_a = pd.Series(np.random.normal(0.0002, 0.005, n), index=idx)
        # rsi_mean_revert：日均 0.0015（年化 ~45%）→ 正 alpha
        returns_b = pd.Series(np.random.normal(0.0015, 0.006, n), index=idx)

        # 验证前提
        alpha_a = _compute_alpha(returns_a, spy_returns)
        alpha_b = _compute_alpha(returns_b, spy_returns)
        assert alpha_a < 0, f"dual_ma alpha 应 < 0，实际 {alpha_a:.4f}"
        assert alpha_b > 0, f"rsi_mean_revert alpha 应 > 0，实际 {alpha_b:.4f}"

        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
            results = []
            for sym, df in data.items():
                if df is None or df.empty or len(df) < 30:
                    continue
                returns = returns_a if strategy_name == "dual_ma" else returns_b
                results.append(_make_result(sym, strategy_name, returns, closed_trades=10))
            return results

        df_up = _make_ohlcv(n, trend="up")
        store = _make_store_with_spy({"AAA": df_up, "BBB": df_up}, spy_df)
        universe = _make_mock_universe({"test_group": ["AAA", "BBB"]})

        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
        report = MatrixBacktestReport(
            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
            backtest_window="2021-01-01 ~ 2022-01-01",
            groups={},
        )

        with patch(
            "mytrader.backtest.matrix_backtest._backtest_batch",
            side_effect=mock_backtest_batch,
        ):
            weights = mb._run_group(
                group_id="test_group",
                symbols=["AAA", "BBB"],
                start=date(2021, 1, 1),
                end=date(2022, 1, 1),
                strategies=["dual_ma", "rsi_mean_revert"],
                param_grids={
                    "dual_ma": {"fast": [5], "slow": [20]},
                    "rsi_mean_revert": {
                        "period": [14], "oversold": [30], "overbought": [70]
                    },
                },
                report=report,
            )

        # 负 alpha 的 dual_ma 不应在权重中
        strategies_in_weights = [w["strategy"] for w in weights]
        assert "dual_ma" not in strategies_in_weights, (
            f"dual_ma（负 alpha）不应出现在权重中，实际 weights={strategies_in_weights}"
        )
        assert "rsi_mean_revert" in strategies_in_weights, (
            f"rsi_mean_revert（正 alpha）应在权重中，实际 weights={strategies_in_weights}"
        )
        # no_positive_alpha 不应被标记（因为有正 alpha 候选通过）
        for gr in report.group_results:
            if gr.group_id == "test_group":
                assert gr.no_positive_alpha is False


# ---------------------------------------------------------------------------
# Test 4: 健全性门槛 + alpha>0 门槛协同
# ---------------------------------------------------------------------------

class TestSanityGateAndAlphaGateCoordination:
    """健全性门槛（Iter #11）+ alpha>0 门槛（Iter #12）协同工作。"""

    def test_alpha_gate_after_sanity_gate(self):
        """健全性门槛先剔除退化策略，alpha 门槛再剔除负 alpha 策略。

        场景：3 个策略
          - dual_ma: 退化（closed_trades=0）→ 健全性门槛剔除
          - rsi_mean_revert: 正常但负 alpha → alpha 门槛剔除
          - bollinger_band: 正常且正 alpha → 应入选

        验证：只有 bollinger_band 出现在 weights。
        """
        n = 300
        idx = pd.date_range("2021-01-01", periods=n, freq="B")
        spy_df = _make_spy_df(n, annual_return=0.10)
        spy_returns = spy_df["close"].pct_change().dropna()

        np.random.seed(42)
        # dual_ma: 退化（closed_trades=0）+ 正 alpha（但健全性门槛先剔除）
        returns_degenerate = pd.Series(np.random.normal(0.0015, 0.005, n), index=idx)
        # rsi_mean_revert: 正常（closed_trades>0）+ 负 alpha
        returns_negative_alpha = pd.Series(np.random.normal(0.0002, 0.004, n), index=idx)
        # bollinger_band: 正常（closed_trades>0）+ 正 alpha
        returns_positive_alpha = pd.Series(np.random.normal(0.0014, 0.005, n), index=idx)

        # 验证前提
        alpha_neg = _compute_alpha(returns_negative_alpha, spy_returns)
        alpha_pos = _compute_alpha(returns_positive_alpha, spy_returns)
        assert alpha_neg < 0, f"rsi_mean_revert alpha 应 < 0，实际 {alpha_neg:.4f}"
        assert alpha_pos > 0, f"bollinger_band alpha 应 > 0，实际 {alpha_pos:.4f}"

        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
            results = []
            for sym, df in data.items():
                if df is None or df.empty or len(df) < 30:
                    continue
                if strategy_name == "dual_ma":
                    # 退化：closed_trades=0
                    results.append(_make_result(
                        sym, strategy_name, returns_degenerate, closed_trades=0
                    ))
                elif strategy_name == "rsi_mean_revert":
                    # 正常但负 alpha
                    results.append(_make_result(
                        sym, strategy_name, returns_negative_alpha, closed_trades=10
                    ))
                else:  # bollinger_band
                    # 正常且正 alpha
                    results.append(_make_result(
                        sym, strategy_name, returns_positive_alpha, closed_trades=10
                    ))
            return results

        df_up = _make_ohlcv(n, trend="up")
        # 5 标的让退化比例 5/5=100% ≥ 0.8
        store = _make_store_with_spy(
            {"AAA": df_up, "BBB": df_up, "CCC": df_up, "DDD": df_up, "EEE": df_up},
            spy_df,
        )
        universe = _make_mock_universe(
            {"test_group": ["AAA", "BBB", "CCC", "DDD", "EEE"]}
        )

        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=3)
        report = MatrixBacktestReport(
            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
            backtest_window="2021-01-01 ~ 2022-01-01",
            groups={},
        )

        with patch(
            "mytrader.backtest.matrix_backtest._backtest_batch",
            side_effect=mock_backtest_batch,
        ):
            weights = mb._run_group(
                group_id="test_group",
                symbols=["AAA", "BBB", "CCC", "DDD", "EEE"],
                start=date(2021, 1, 1),
                end=date(2022, 1, 1),
                strategies=["dual_ma", "rsi_mean_revert", "bollinger_band"],
                param_grids={
                    "dual_ma": {"fast": [5], "slow": [20]},
                    "rsi_mean_revert": {
                        "period": [14], "oversold": [30], "overbought": [70]
                    },
                    "bollinger_band": {"period": [20], "std_dev": [2.0]},
                },
                report=report,
            )

        # 只有 bollinger_band 应出现在权重中
        strategies_in_weights = [w["strategy"] for w in weights]
        assert "dual_ma" not in strategies_in_weights, (
            f"dual_ma（退化）应被健全性门槛剔除，实际 weights={strategies_in_weights}"
        )
        assert "rsi_mean_revert" not in strategies_in_weights, (
            f"rsi_mean_revert（负 alpha）应被 alpha 门槛剔除，"
            f"实际 weights={strategies_in_weights}"
        )
        assert "bollinger_band" in strategies_in_weights, (
            f"bollinger_band（正常 + 正 alpha）应入选，"
            f"实际 weights={strategies_in_weights}"
        )

    def test_degenerate_takes_precedence_over_alpha_gate(self):
        """全退化组触发 no_valid_strategy（先于 alpha 门槛），不触发 no_positive_alpha。

        场景：所有策略都退化（closed_trades=0）。
        验证：返回空权重，标记 no_valid_strategy=True，no_positive_alpha=False
              （健全性门槛先返回，alpha 门槛未到达）。
        """
        n = 300
        idx = pd.date_range("2021-01-01", periods=n, freq="B")
        spy_df = _make_spy_df(n, annual_return=0.10)

        np.random.seed(42)
        returns_a = pd.Series(np.random.normal(0.001, 0.005, n), index=idx)
        returns_b = pd.Series(np.random.normal(0.0008, 0.003, n), index=idx)

        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
            results = []
            for sym, df in data.items():
                if df is None or df.empty or len(df) < 30:
                    continue
                returns = returns_a if strategy_name == "dual_ma" else returns_b
                # 全退化：closed_trades=0
                results.append(_make_result(sym, strategy_name, returns, closed_trades=0))
            return results

        df_up = _make_ohlcv(n, trend="up")
        store = _make_store_with_spy(
            {"AAA": df_up, "BBB": df_up, "CCC": df_up, "DDD": df_up, "EEE": df_up},
            spy_df,
        )
        universe = _make_mock_universe(
            {"test_group": ["AAA", "BBB", "CCC", "DDD", "EEE"]}
        )

        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
        report = MatrixBacktestReport(
            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
            backtest_window="2021-01-01 ~ 2022-01-01",
            groups={},
        )

        with patch(
            "mytrader.backtest.matrix_backtest._backtest_batch",
            side_effect=mock_backtest_batch,
        ):
            weights = mb._run_group(
                group_id="test_group",
                symbols=["AAA", "BBB", "CCC", "DDD", "EEE"],
                start=date(2021, 1, 1),
                end=date(2022, 1, 1),
                strategies=["dual_ma", "rsi_mean_revert"],
                param_grids={
                    "dual_ma": {"fast": [5], "slow": [20]},
                    "rsi_mean_revert": {
                        "period": [14], "oversold": [30], "overbought": [70]
                    },
                },
                report=report,
            )

        # 全退化 → 空权重
        assert weights == []
        # 健全性门槛先返回 → no_valid_strategy=True
        warning_text = " ".join(report.warnings)
        assert "no_valid_strategy" in warning_text
        # alpha 门槛未到达 → no_positive_alpha 不应被标记
        assert "no_positive_alpha" not in warning_text, (
            f"全退化组应触发 no_valid_strategy（先于 alpha 门槛），"
            f"不应触发 no_positive_alpha，warnings={report.warnings}"
        )
        for gr in report.group_results:
            if gr.group_id == "test_group":
                assert gr.no_valid_strategy is True
                assert gr.no_positive_alpha is False


# ---------------------------------------------------------------------------
# Test 5-8: _optimize_ensemble_weights 负 alpha 归一化
# ---------------------------------------------------------------------------

class TestEnsembleWeightsNegativeAlpha:
    """_optimize_ensemble_weights 负 alpha 归一化测试（迭代 #12 修复）。"""

    def test_ensemble_negative_alpha_zero_weight(self):
        """负 alpha 策略权重为 0（不再被 max(0.01) 掩盖成等权）。

        场景：策略 A 正 alpha=10%，策略 B 负 alpha=-5%。
        旧代码：max(-5, 0.01)=0.01, max(10, 0.01)=10 → 权重 ≈ 0.001 / 0.999
        新代码：max(-5, 0)=0, max(10, 0)=10 → 权重 = 0.0 / 1.0
        验证：B 的权重严格为 0，A 的权重为 1.0。
        """
        n = 252
        idx = pd.date_range("2021-01-01", periods=n, freq="B")
        spy_returns = pd.Series(np.random.normal(0.0004, 0.001, n), index=idx)

        # A: 正 alpha（日均 0.0012 >> SPY 0.0004）
        returns_a = pd.Series(np.random.normal(0.0012, 0.005, n), index=idx)
        # B: 负 alpha（日均 0.0001 << SPY 0.0004）
        returns_b = pd.Series(np.random.normal(0.0001, 0.005, n), index=idx)

        results_a = [_make_result("S1", "strat_a", returns_a)]
        results_b = [_make_result("S2", "strat_b", returns_b)]

        group_results = [
            ("strat_a", {}, results_a),
            ("strat_b", {}, results_b),
        ]

        weights = _optimize_ensemble_weights(group_results, spy_returns=spy_returns)
        weights_dict = {s: w for s, _, w in weights}

        # 验证前提：A 的 alpha > 0，B 的 alpha < 0
        alpha_a = _compute_alpha(
            _combine_daily_returns(results_a), spy_returns
        )
        alpha_b = _compute_alpha(
            _combine_daily_returns(results_b), spy_returns
        )
        assert alpha_a > 0, f"A 的 alpha 应 > 0，实际 {alpha_a:.4f}"
        assert alpha_b < 0, f"B 的 alpha 应 < 0，实际 {alpha_b:.4f}"

        # B（负 alpha）权重应为 0
        assert weights_dict["strat_b"] == 0.0, (
            f"负 alpha 策略权重应为 0，实际 {weights_dict['strat_b']:.6f}"
        )
        # A（正 alpha）权重应为 1.0
        assert abs(weights_dict["strat_a"] - 1.0) < 1e-9, (
            f"全正 alpha 归一化后 A 权重应为 1.0，"
            f"实际 {weights_dict['strat_a']:.6f}"
        )
        # 权重和 = 1.0
        total = sum(weights_dict.values())
        assert abs(total - 1.0) < 1e-9

    def test_ensemble_all_positive_normalizes(self):
        """全正 alpha 正常归一化（权重和=1.0，高 alpha 权重大）。"""
        n = 252
        idx = pd.date_range("2021-01-01", periods=n, freq="B")
        spy_returns = pd.Series(np.random.normal(0.0004, 0.001, n), index=idx)

        # A: 高 alpha（日均 0.0015）
        returns_a = pd.Series(np.random.normal(0.0015, 0.005, n), index=idx)
        # B: 低 alpha（日均 0.0008，仍 > SPY 0.0004）
        returns_b = pd.Series(np.random.normal(0.0008, 0.003, n), index=idx)

        results_a = [_make_result("S1", "strat_a", returns_a)]
        results_b = [_make_result("S2", "strat_b", returns_b)]

        group_results = [
            ("strat_a", {}, results_a),
            ("strat_b", {}, results_b),
        ]

        weights = _optimize_ensemble_weights(group_results, spy_returns=spy_returns)
        weights_dict = {s: w for s, _, w in weights}

        # 验证前提：两个策略 alpha 都 > 0
        alpha_a = _compute_alpha(_combine_daily_returns(results_a), spy_returns)
        alpha_b = _compute_alpha(_combine_daily_returns(results_b), spy_returns)
        assert alpha_a > 0 and alpha_b > 0

        # A 的 alpha 更高 → 权重更大
        assert weights_dict["strat_a"] > weights_dict["strat_b"], (
            f"A 的 alpha 更高，权重应大于 B，"
            f"实际 A={weights_dict['strat_a']:.4f}, B={weights_dict['strat_b']:.4f}"
        )
        # 权重和 = 1.0
        total = sum(weights_dict.values())
        assert abs(total - 1.0) < 1e-9, f"权重和应为 1.0，实际 {total:.6f}"
        # 两个权重都 > 0（不是 0）
        assert weights_dict["strat_a"] > 0
        assert weights_dict["strat_b"] > 0

    def test_ensemble_mixed_alpha_only_positive_weighted(self):
        """混合 alpha：只正 alpha 参与归一化，负 alpha 权重=0。

        场景：3 个策略，2 正 alpha + 1 负 alpha。
        验证：负 alpha 权重=0，两个正 alpha 按比例分配，权重和=1.0。
        """
        n = 252
        idx = pd.date_range("2021-01-01", periods=n, freq="B")
        spy_returns = pd.Series(np.random.normal(0.0004, 0.001, n), index=idx)

        # A: 强正 alpha（日均 0.0020）
        returns_a = pd.Series(np.random.normal(0.0020, 0.005, n), index=idx)
        # B: 弱正 alpha（日均 0.0006，略 > SPY 0.0004）
        returns_b = pd.Series(np.random.normal(0.0006, 0.003, n), index=idx)
        # C: 负 alpha（日均 0.0001 << SPY）
        returns_c = pd.Series(np.random.normal(0.0001, 0.005, n), index=idx)

        results_a = [_make_result("S1", "strat_a", returns_a)]
        results_b = [_make_result("S2", "strat_b", returns_b)]
        results_c = [_make_result("S3", "strat_c", returns_c)]

        group_results = [
            ("strat_a", {}, results_a),
            ("strat_b", {}, results_b),
            ("strat_c", {}, results_c),
        ]

        # 验证前提
        alpha_a = _compute_alpha(_combine_daily_returns(results_a), spy_returns)
        alpha_b = _compute_alpha(_combine_daily_returns(results_b), spy_returns)
        alpha_c = _compute_alpha(_combine_daily_returns(results_c), spy_returns)
        assert alpha_a > 0, f"A alpha 应 > 0，实际 {alpha_a:.4f}"
        assert alpha_b > 0, f"B alpha 应 > 0，实际 {alpha_b:.4f}"
        assert alpha_c < 0, f"C alpha 应 < 0，实际 {alpha_c:.4f}"

        weights = _optimize_ensemble_weights(group_results, spy_returns=spy_returns)
        weights_dict = {s: w for s, _, w in weights}

        # C（负 alpha）权重 = 0
        assert weights_dict["strat_c"] == 0.0, (
            f"负 alpha 策略 C 权重应为 0，实际 {weights_dict['strat_c']:.6f}"
        )
        # A 和 B 权重都 > 0
        assert weights_dict["strat_a"] > 0
        assert weights_dict["strat_b"] > 0
        # A 的 alpha > B 的 alpha → A 权重 > B 权重
        assert weights_dict["strat_a"] > weights_dict["strat_b"]
        # 权重和 = 1.0（C=0，A+B=1.0）
        total = sum(weights_dict.values())
        assert abs(total - 1.0) < 1e-9

    def test_ensemble_all_negative_fallback_equal(self):
        """全负 alpha 退化为等权 + WARNING（防御性 fallback）。

        场景：两个策略都负 alpha。
        验证：权重等权（各 0.5），WARNING 日志触发。
        注：上游 alpha>0 门槛应已拦截此情形，此处为防御性设计测试。
        """
        from loguru import logger

        n = 252
        idx = pd.date_range("2021-01-01", periods=n, freq="B")
        spy_returns = pd.Series(np.random.normal(0.001, 0.001, n), index=idx)

        # A: 负 alpha（日均 0.0001 << SPY 0.001）
        returns_a = pd.Series(np.random.normal(0.0001, 0.005, n), index=idx)
        # B: 负 alpha（日均 0.0002 << SPY 0.001）
        returns_b = pd.Series(np.random.normal(0.0002, 0.005, n), index=idx)

        results_a = [_make_result("S1", "strat_a", returns_a)]
        results_b = [_make_result("S2", "strat_b", returns_b)]

        group_results = [
            ("strat_a", {}, results_a),
            ("strat_b", {}, results_b),
        ]

        # 验证前提：两个策略 alpha 都 < 0
        alpha_a = _compute_alpha(_combine_daily_returns(results_a), spy_returns)
        alpha_b = _compute_alpha(_combine_daily_returns(results_b), spy_returns)
        assert alpha_a < 0, f"A alpha 应 < 0，实际 {alpha_a:.4f}"
        assert alpha_b < 0, f"B alpha 应 < 0，实际 {alpha_b:.4f}"

        # 捕获 WARNING 日志
        msgs: list[str] = []
        handler_id = logger.add(lambda m: msgs.append(str(m)), level="WARNING")

        try:
            weights = _optimize_ensemble_weights(
                group_results, spy_returns=spy_returns
            )
        finally:
            logger.remove(handler_id)

        weights_dict = {s: w for s, _, w in weights}

        # 全负 alpha → 等权 fallback
        assert abs(weights_dict["strat_a"] - 0.5) < 1e-9, (
            f"全负 alpha fallback 应等权 0.5，实际 {weights_dict['strat_a']:.6f}"
        )
        assert abs(weights_dict["strat_b"] - 0.5) < 1e-9, (
            f"全负 alpha fallback 应等权 0.5，实际 {weights_dict['strat_b']:.6f}"
        )
        # WARNING 日志触发
        assert any("alphas <= 0" in m for m in msgs), (
            f"全负 alpha 应触发 WARNING 日志，实际捕获: {msgs}"
        )

    def test_ensemble_spy_unavailable_degrades_to_equal(self):
        """SPY 数据不可用时 alpha=0 → 全零 alpha → 等权 fallback。

        注：Iter #9 旧代码 max(0, 0.01)=0.01 也是等权，但语义是"避免零权重"。
        Iter #12 新代码 max(0, 0)=0 → total=0 → 等权 fallback。
        行为一致（等权），但路径不同（fallback 而非归一化）。
        """
        n = 100
        idx = pd.date_range("2021-01-01", periods=n, freq="B")
        returns_a = pd.Series(np.random.normal(0.001, 0.005, n), index=idx)
        returns_b = pd.Series(np.random.normal(0.002, 0.008, n), index=idx)

        results_a = [_make_result("S1", "strat_a", returns_a)]
        results_b = [_make_result("S2", "strat_b", returns_b)]

        group_results = [
            ("strat_a", {}, results_a),
            ("strat_b", {}, results_b),
        ]

        # spy_returns=None → alpha=0 → 全零 → 等权 fallback
        weights = _optimize_ensemble_weights(group_results, spy_returns=None)
        weights_dict = {s: w for s, _, w in weights}
        # 等权：各 0.5
        assert abs(weights_dict["strat_a"] - 0.5) < 1e-9
        assert abs(weights_dict["strat_b"] - 0.5) < 1e-9

    def test_ensemble_single_strategy_returns_one(self):
        """单策略时直接返回权重 1.0（与 Iter #9 行为一致）。"""
        n = 100
        idx = pd.date_range("2021-01-01", periods=n, freq="B")
        returns = pd.Series(np.random.normal(0.001, 0.005, n), index=idx)
        results = [_make_result("S1", "strat_a", returns)]

        weights = _optimize_ensemble_weights(
            [("strat_a", {}, results)],
            spy_returns=pd.Series(dtype=float),
        )
        assert len(weights) == 1
        assert weights[0][0] == "strat_a"
        assert weights[0][2] == 1.0


# ---------------------------------------------------------------------------
# Iter #16: Relaxed alpha gate (ALPHA_GATE_THRESHOLD = -2.0)
# ---------------------------------------------------------------------------

class TestAlphaGateRelaxedThreshold:
    """迭代 #16：alpha gate 从 alpha>0 放宽至 alpha > ALPHA_GATE_THRESHOLD (-2%)。

    动机见 spec §1：SPX 成分股 vs SPY 存在结构性近零 alpha，严格 alpha>0 门槛
    导致 4/6 组空仓。放宽至 -2% 仍过滤"灾难性跑输"，但保留"小幅跑输"候选。
    """

    def test_alpha_gate_constant_exists(self):
        """ALPHA_GATE_THRESHOLD 常量存在且等于 -2.0。"""
        assert hasattr(
            __import__("mytrader.backtest.matrix_backtest", fromlist=["matrix_backtest"]),
            "ALPHA_GATE_THRESHOLD",
        ), "matrix_backtest 必须导出 ALPHA_GATE_THRESHOLD 常量"
        assert ALPHA_GATE_THRESHOLD == -2.0, (
            f"ALPHA_GATE_THRESHOLD 应为 -2.0，实际 {ALPHA_GATE_THRESHOLD}"
        )

    def test_alpha_gate_relaxed_negative_alpha_passes(self):
        """alpha=-1% 通过 gate（在 -2% 与 0% 之间，旧 gate 会拒绝，新 gate 通过）。

        场景：单策略 alpha=-1%，健全性通过。
        验证：权重正常产出（非空），no_positive_alpha=False。

        实现注：用 patch _compute_alpha 返回精确 -1.0%，避免随机收益序列的方差干扰。
        重点测试 gate 逻辑，不测试 alpha 计算本身（后者在 test_matrix_backtest 覆盖）。
        """
        n = 300
        idx = pd.date_range("2021-01-01", periods=n, freq="B")
        spy_df = _make_spy_df(n, annual_return=0.10)

        # 用任意正收益序列（健全性门槛需要 closed_trades>0，已由 _make_result 默认值满足）
        np.random.seed(42)
        returns_a = pd.Series(np.random.normal(0.0004, 0.004, n), index=idx)

        # 通过 mock 精确控制 alpha = -1.0%（在 -2% 与 0% 之间）
        mock_alpha = -1.0
        assert ALPHA_GATE_THRESHOLD < mock_alpha < 0, (
            f"测试前提失败：mock alpha 应在 (-2%, 0) 之间"
        )

        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
            results = []
            for sym, df in data.items():
                if df is None or df.empty or len(df) < 30:
                    continue
                results.append(_make_result(sym, strategy_name, returns_a, closed_trades=10))
            return results

        df_up = _make_ohlcv(n, trend="up")
        store = _make_store_with_spy({"AAA": df_up, "BBB": df_up}, spy_df)
        universe = _make_mock_universe({"test_group": ["AAA", "BBB"]})

        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
        report = MatrixBacktestReport(
            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
            backtest_window="2021-01-01 ~ 2022-01-01",
            groups={},
        )

        with patch(
            "mytrader.backtest.matrix_backtest._backtest_batch",
            side_effect=mock_backtest_batch,
        ), patch(
            "mytrader.backtest.matrix_backtest._compute_alpha",
            return_value=mock_alpha,
        ):
            weights = mb._run_group(
                group_id="test_group",
                symbols=["AAA", "BBB"],
                start=date(2021, 1, 1),
                end=date(2022, 1, 1),
                strategies=["dual_ma"],
                param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
                report=report,
            )

        # 关键断言：alpha=-1% 应通过 gate（旧 gate 会拒绝）
        assert len(weights) > 0, (
            f"alpha=-1% 应通过 Iter #16 放宽后的 gate，实际 weights={weights}"
        )
        # no_positive_alpha 不应被标记
        for gr in report.group_results:
            if gr.group_id == "test_group":
                assert gr.no_positive_alpha is False, (
                    "alpha=-1% 组不应标记 no_positive_alpha=True（Iter #16 放宽后）"
                )
        warning_text = " ".join(report.warnings)
        assert "no_positive_alpha" not in warning_text, (
            f"alpha=-1% 组不应有 no_positive_alpha 警告，warnings={report.warnings}"
        )

    def test_alpha_gate_very_negative_fails(self):
        """alpha=-5% 仍被拒绝（远低于 -2% 阈值）。

        场景：单策略 alpha=-5%，健全性通过。
        验证：返回空权重，no_positive_alpha=True。
        """
        n = 300
        idx = pd.date_range("2021-01-01", periods=n, freq="B")
        spy_df = _make_spy_df(n, annual_return=0.10)

        np.random.seed(42)
        returns_a = pd.Series(np.random.normal(0.0004, 0.004, n), index=idx)

        # mock alpha = -5.0%（远低于 -2% 阈值）
        mock_alpha = -5.0
        assert mock_alpha < ALPHA_GATE_THRESHOLD, (
            f"测试前提失败：mock alpha 应 < {ALPHA_GATE_THRESHOLD}%"
        )

        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
            results = []
            for sym, df in data.items():
                if df is None or df.empty or len(df) < 30:
                    continue
                results.append(_make_result(sym, strategy_name, returns_a, closed_trades=10))
            return results

        df_up = _make_ohlcv(n, trend="up")
        store = _make_store_with_spy({"AAA": df_up, "BBB": df_up}, spy_df)
        universe = _make_mock_universe({"test_group": ["AAA", "BBB"]})

        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
        report = MatrixBacktestReport(
            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
            backtest_window="2021-01-01 ~ 2022-01-01",
            groups={},
        )

        with patch(
            "mytrader.backtest.matrix_backtest._backtest_batch",
            side_effect=mock_backtest_batch,
        ), patch(
            "mytrader.backtest.matrix_backtest._compute_alpha",
            return_value=mock_alpha,
        ):
            weights = mb._run_group(
                group_id="test_group",
                symbols=["AAA", "BBB"],
                start=date(2021, 1, 1),
                end=date(2022, 1, 1),
                strategies=["dual_ma"],
                param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
                report=report,
            )

        # 关键断言：alpha=-5% 应被拒绝
        assert weights == [], (
            f"alpha={mock_alpha}% 应被拒绝（< {ALPHA_GATE_THRESHOLD}%），实际 weights={weights}"
        )
        warning_text = " ".join(report.warnings)
        assert "no_positive_alpha" in warning_text
        for gr in report.group_results:
            if gr.group_id == "test_group":
                assert gr.no_positive_alpha is True

    def test_alpha_gate_threshold_boundary(self):
        """alpha=-2.0% 恰好在阈值边界 → 被拒绝（使用 > 严格比较）。

        场景：alpha 精确等于 -2.0%（边界值）。
        验证：返回空权重（因为 `c[5] > ALPHA_GATE_THRESHOLD` 是严格大于）。
        """
        n = 300
        idx = pd.date_range("2021-01-01", periods=n, freq="B")
        spy_df = _make_spy_df(n, annual_return=0.10)

        np.random.seed(42)
        returns_a = pd.Series(np.random.normal(0.0004, 0.004, n), index=idx)

        # mock alpha 精确等于阈值边界
        mock_alpha = ALPHA_GATE_THRESHOLD  # -2.0

        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
            results = []
            for sym, df in data.items():
                if df is None or df.empty or len(df) < 30:
                    continue
                results.append(_make_result(sym, strategy_name, returns_a, closed_trades=10))
            return results

        df_up = _make_ohlcv(n, trend="up")
        store = _make_store_with_spy({"AAA": df_up, "BBB": df_up}, spy_df)
        universe = _make_mock_universe({"test_group": ["AAA", "BBB"]})

        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
        report = MatrixBacktestReport(
            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
            backtest_window="2021-01-01 ~ 2022-01-01",
            groups={},
        )

        # patch _compute_alpha 返回精确 -2.0%（边界值）
        with patch(
            "mytrader.backtest.matrix_backtest._backtest_batch",
            side_effect=mock_backtest_batch,
        ), patch(
            "mytrader.backtest.matrix_backtest._compute_alpha",
            return_value=mock_alpha,
        ):
            weights = mb._run_group(
                group_id="test_group",
                symbols=["AAA", "BBB"],
                start=date(2021, 1, 1),
                end=date(2022, 1, 1),
                strategies=["dual_ma"],
                param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
                report=report,
            )

        # 关键断言：alpha == threshold 应被拒绝（因为 c[5] > ALPHA_GATE_THRESHOLD 是严格大于）
        assert weights == [], (
            f"alpha == {ALPHA_GATE_THRESHOLD}% 应被拒绝（使用 > 严格比较），"
            f"实际 weights={weights}"
        )
        warning_text = " ".join(report.warnings)
        assert "no_positive_alpha" in warning_text

    def test_alpha_gate_positive_alpha_passes(self):
        """alpha=+1% 仍通过 gate（无回归，正 alpha 行为不变）。

        场景：单策略 alpha=+1%（正 alpha）。
        验证：权重正常产出，no_positive_alpha=False。
        这是回归测试，确保 Iter #16 放宽不破坏正 alpha 行为。
        """
        n = 300
        idx = pd.date_range("2021-01-01", periods=n, freq="B")
        spy_df = _make_spy_df(n, annual_return=0.10)

        np.random.seed(42)
        returns_a = pd.Series(np.random.normal(0.0004, 0.004, n), index=idx)

        # mock alpha = +1.0%（正 alpha）
        mock_alpha = 1.0
        assert mock_alpha > 0

        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
            results = []
            for sym, df in data.items():
                if df is None or df.empty or len(df) < 30:
                    continue
                results.append(_make_result(sym, strategy_name, returns_a, closed_trades=10))
            return results

        df_up = _make_ohlcv(n, trend="up")
        store = _make_store_with_spy({"AAA": df_up, "BBB": df_up}, spy_df)
        universe = _make_mock_universe({"test_group": ["AAA", "BBB"]})

        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
        report = MatrixBacktestReport(
            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
            backtest_window="2021-01-01 ~ 2022-01-01",
            groups={},
        )

        with patch(
            "mytrader.backtest.matrix_backtest._backtest_batch",
            side_effect=mock_backtest_batch,
        ), patch(
            "mytrader.backtest.matrix_backtest._compute_alpha",
            return_value=mock_alpha,
        ):
            weights = mb._run_group(
                group_id="test_group",
                symbols=["AAA", "BBB"],
                start=date(2021, 1, 1),
                end=date(2022, 1, 1),
                strategies=["dual_ma"],
                param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
                report=report,
            )

        # 正 alpha 应���常通过
        assert len(weights) > 0, (
            f"正 alpha 应通过 gate（无回归），实际 weights={weights}"
        )
        for gr in report.group_results:
            if gr.group_id == "test_group":
                assert gr.no_positive_alpha is False

    def test_alpha_gate_relaxed_unblocks_spx(self):
        """集成场景：SPX 组 alpha=-1.5% 策略入选 tier1（旧 gate 会拒绝）。

        场景：模拟 Iter #15 reoptimize 中 SPX 组的情况——
        策略 alpha=-1.5%（在 -2% 与 0% 之间），DD ≤ 20%，Sortino > 0.5。
        验证：
          - 旧 gate（alpha>0）会拒绝 → 空权重
          - 新 gate（alpha>-2%）通过 → 权重非空
        """
        n = 300
        idx = pd.date_range("2021-01-01", periods=n, freq="B")
        spy_df = _make_spy_df(n, annual_return=0.10)

        np.random.seed(42)
        returns_a = pd.Series(np.random.normal(0.0004, 0.004, n), index=idx)

        # mock alpha = -1.5%（在 -2% 与 0% 之间，模拟 SPX near-zero alpha 场景）
        mock_alpha = -1.5
        assert ALPHA_GATE_THRESHOLD < mock_alpha < 0

        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
            results = []
            for sym, df in data.items():
                if df is None or df.empty or len(df) < 30:
                    continue
                results.append(_make_result(sym, strategy_name, returns_a, closed_trades=10))
            return results

        df_up = _make_ohlcv(n, trend="up")
        store = _make_store_with_spy({"AAA": df_up, "BBB": df_up}, spy_df)
        # 模拟 SPX 组名（仅用于语义清晰，不影响逻辑）
        universe = _make_mock_universe({"SPX_mid_vol": ["AAA", "BBB"]})

        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
        report = MatrixBacktestReport(
            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
            backtest_window="2021-01-01 ~ 2022-01-01",
            groups={},
        )

        with patch(
            "mytrader.backtest.matrix_backtest._backtest_batch",
            side_effect=mock_backtest_batch,
        ), patch(
            "mytrader.backtest.matrix_backtest._compute_alpha",
            return_value=mock_alpha,
        ):
            weights = mb._run_group(
                group_id="SPX_mid_vol",
                symbols=["AAA", "BBB"],
                start=date(2021, 1, 1),
                end=date(2022, 1, 1),
                strategies=["dual_ma"],
                param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
                report=report,
            )

        # 关键断言：SPX 组不再空仓
        assert len(weights) > 0, (
            f"SPX 组 alpha={mock_alpha}%（> {ALPHA_GATE_THRESHOLD}%）应通过 gate，"
            f"实际 weights={weights}（Iter #15 此场景被 alpha>0 gate 阻塞）"
        )
        # backtest_alpha 字段应存在
        for w in weights:
            assert "backtest_alpha" in w
        # no_positive_alpha 不应被标记
        warning_text = " ".join(report.warnings)
        assert "no_positive_alpha" not in warning_text

    def test_ensemble_weights_with_negative_alpha_single_strategy(self):
        """单策略 ensemble 负 alpha（> -2%）仍得 weight=1.0（早返回）。

        场景：单策略 alpha=-1%（通过 Iter #16 gate），进入 ensemble。
        验证：`_optimize_ensemble_weights` 的 `len == 1` 早返回路径给 weight=1.0。

        注：多策略 ensemble 中负 alpha 权重仍为 0（max(a, 0.0)），
        这是保守设计——正 alpha 策略应主导权重。单策略场景是特例。
        """
        n = 252
        idx = pd.date_range("2021-01-01", periods=n, freq="B")
        spy_returns = pd.Series(np.random.normal(0.0004, 0.001, n), index=idx)

        # 策略收益序列（alpha 值由 mock 控制，这里只需要非空序列）
        np.random.seed(42)
        returns_a = pd.Series(np.random.normal(0.00035, 0.004, n), index=idx)

        results_a = [_make_result("S1", "strat_a", returns_a)]

        # 单策略 ensemble（早返回路径，不计算 alpha）
        weights = _optimize_ensemble_weights(
            [("strat_a", {}, results_a)],
            spy_returns=spy_returns,
        )

        # 早返回路径 → weight=1.0
        assert len(weights) == 1
        assert weights[0][0] == "strat_a"
        assert weights[0][2] == 1.0, (
            f"单策略 ensemble 应早返回 weight=1.0（不依赖 alpha 值），"
            f"实际 {weights[0][2]}"
        )
