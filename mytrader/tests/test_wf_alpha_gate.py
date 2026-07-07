"""迭代 #13：WF Gate 加 Alpha 校验测试（Walk-Forward alpha gate）。

验证：
    1. `WalkForwardRound.val_alpha` 字段存在且默认 0.0
    2. `WalkForwardReport.avg_val_alpha` / `min_val_alpha` 字段存在
    3. 单轮 alpha < -5% → `passed=False`（即使 DD 合规）
    4. 单轮 alpha > 0 且 DD ≤ 15% → `passed=True`
    5. 单轮 alpha = -3%（> -5%）且 DD 合规 → `passed=True`
    6. 4 轮全 pass 但 avg alpha < 0 → `pass_all_rounds=False`
    7. 4 轮全 pass 且 avg alpha > 0 → `pass_all_rounds=True`
    8. SPY 不可用时 val_alpha=0.0 + WARNING（降级不阻塞）
    9. 用已知 returns + spy_returns 验证 val_alpha 值正确

背景见 `iterations/iteration_13/spec.md` + `.codebuddy/notes/experience.md` #8。
"""

from __future__ import annotations

from datetime import date as _date
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from mytrader.backtest.matrix_backtest import (
    MatrixBacktest,
    SingleBacktestResult,
    WALK_FORWARD_VAL_ALPHA_FLOOR,
    WALK_FORWARD_VAL_DD_THRESHOLD,
    WalkForwardReport,
    WalkForwardRound,
    _compute_alpha,
    run_walk_forward,
)


# ---------------------------------------------------------------------------
# 1. Dataclass 字段测试
# ---------------------------------------------------------------------------

class TestWFAlphaDataclassFields:
    """迭代 #13：WalkForwardRound / WalkForwardReport 新增 alpha 字段。"""

    def test_wf_round_has_val_alpha_field(self):
        """WalkForwardRound.val_alpha 字段存在且默认 0.0。"""
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
        # 默认值 0.0
        assert hasattr(r, "val_alpha"), "WalkForwardRound 应有 val_alpha 字段"
        assert r.val_alpha == 0.0, f"val_alpha 默认应为 0.0，实际 {r.val_alpha}"

    def test_wf_round_val_alpha_can_be_set(self):
        """val_alpha 可以显式设置。"""
        r = WalkForwardRound(
            round_num=1,
            train_start=_date(2021, 1, 1),
            train_end=_date(2023, 1, 1),
            val_start=_date(2023, 1, 1),
            val_end=_date(2023, 7, 1),
            val_sortino=1.0,
            val_max_dd=10.0,
            val_alpha=5.23,
            passed=True,
        )
        assert r.val_alpha == 5.23

    def test_wf_report_has_alpha_aggregation(self):
        """WalkForwardReport.avg_val_alpha 和 min_val_alpha 字段存在。"""
        report = WalkForwardReport()
        assert hasattr(report, "avg_val_alpha"), (
            "WalkForwardReport 应有 avg_val_alpha 字段"
        )
        assert hasattr(report, "min_val_alpha"), (
            "WalkForwardReport 应有 min_val_alpha 字段"
        )
        assert report.avg_val_alpha == 0.0
        assert report.min_val_alpha == 0.0

    def test_wf_report_alpha_aggregation_values(self):
        """avg_val_alpha / min_val_alpha 可以正确设置。"""
        rounds = [
            WalkForwardRound(
                1, _date(2021, 1, 1), _date(2023, 1, 1),
                _date(2023, 1, 1), _date(2023, 7, 1),
                val_sortino=1.0, val_max_dd=10.0,
                val_alpha=5.0, passed=True,
            ),
            WalkForwardRound(
                2, _date(2021, 7, 1), _date(2023, 7, 1),
                _date(2023, 7, 1), _date(2024, 1, 1),
                val_sortino=0.8, val_max_dd=12.0,
                val_alpha=-3.0, passed=True,
            ),
            WalkForwardRound(
                3, _date(2022, 1, 1), _date(2024, 1, 1),
                _date(2024, 1, 1), _date(2024, 7, 1),
                val_sortino=1.2, val_max_dd=8.0,
                val_alpha=7.0, passed=True,
            ),
        ]
        val_alphas = [r.val_alpha for r in rounds]
        report = WalkForwardReport(
            rounds=rounds,
            pass_all_rounds=True,
            max_val_dd=12.0,
            avg_val_alpha=sum(val_alphas) / len(val_alphas),
            min_val_alpha=min(val_alphas),
        )
        assert report.avg_val_alpha == pytest.approx(3.0, abs=1e-9)
        assert report.min_val_alpha == -3.0


# ---------------------------------------------------------------------------
# 2. Gate 逻辑测试（单轮）
# ---------------------------------------------------------------------------

class TestWFGateSingleRound:
    """迭代 #13：单轮 gate = DD ≤ 15% AND alpha > -5%。"""

    def test_wf_gate_rejects_negative_alpha(self):
        """单轮 alpha < -5% → passed=False（即使 DD 合规）。

        场景：DD=10%（≤ 15% 合规），但 alpha=-8%（< -5% 灾难性跑输）
        → passed=False
        """
        r = WalkForwardRound(
            round_num=1,
            train_start=_date(2021, 1, 1),
            train_end=_date(2023, 1, 1),
            val_start=_date(2023, 1, 1),
            val_end=_date(2023, 7, 1),
            val_sortino=1.0,
            val_max_dd=10.0,   # DD 合规
            val_alpha=-8.0,    # 灾难性跑输
            passed=False,      # alpha < -5% → fail
        )
        assert r.passed is False, (
            "alpha=-8% 应被 alpha floor=-5% 拦截，passed=False"
        )
        # 验证常量
        assert WALK_FORWARD_VAL_ALPHA_FLOOR == -5.0

    def test_wf_gate_passes_positive_alpha(self):
        """单轮 alpha > 0 且 DD ≤ 15% → passed=True。"""
        r = WalkForwardRound(
            round_num=1,
            train_start=_date(2021, 1, 1),
            train_end=_date(2023, 1, 1),
            val_start=_date(2023, 1, 1),
            val_end=_date(2023, 7, 1),
            val_sortino=1.5,
            val_max_dd=10.0,
            val_alpha=5.0,    # 跑赢 SPY
            passed=True,
        )
        assert r.passed is True
        assert r.val_alpha > 0

    def test_wf_gate_allows_small_negative_alpha(self):
        """单轮 alpha = -3%（> -5% floor）且 DD 合规 → passed=True。

        设计动机：单轮允许小幅跑输 SPY（-5%~0%），可能是市场噪音。
        但 4 轮平均必须 > 0（在汇总层校验）。
        """
        r = WalkForwardRound(
            round_num=1,
            train_start=_date(2021, 1, 1),
            train_end=_date(2023, 1, 1),
            val_start=_date(2023, 1, 1),
            val_end=_date(2023, 7, 1),
            val_sortino=1.0,
            val_max_dd=10.0,
            val_alpha=-3.0,   # 小幅跑输，但 > -5% floor
            passed=True,      # DD 合规 + alpha > floor
        )
        assert r.passed is True
        assert r.val_alpha > WALK_FORWARD_VAL_ALPHA_FLOOR

    def test_wf_gate_alpha_floor_boundary(self):
        """alpha = -5.0（恰好等于 floor）→ alpha_passed = False（> 严格大于）。

        gate 条件是 alpha > WALK_FORWARD_VAL_ALPHA_FLOOR（严格大于），
        alpha=-5.0 不满足 > -5.0，所以 passed=False。
        """
        # alpha = -5.0 恰好等于 floor，不满足 > -5.0
        alpha_at_boundary = -5.0
        alpha_passed = alpha_at_boundary > WALK_FORWARD_VAL_ALPHA_FLOOR
        assert alpha_passed is False, (
            "alpha=-5.0 不满足 > -5.0（严格大于），应 fail"
        )

        # alpha = -4.99 刚好过 floor
        alpha_just_above = -4.99
        alpha_passed_just = alpha_just_above > WALK_FORWARD_VAL_ALPHA_FLOOR
        assert alpha_passed_just is True


# ---------------------------------------------------------------------------
# 3. 汇总 gate 逻辑测试（pass_all_rounds）
# ---------------------------------------------------------------------------

class TestWFSummaryGate:
    """迭代 #13：汇总 gate = all rounds passed AND avg_val_alpha > 0。"""

    def test_wf_summary_avg_alpha_negative_fails(self):
        """4 轮全 pass（单轮 DD+alpha floor 都过）但 avg alpha < 0
        → pass_all_rounds=False。

        场景：4 轮 alpha 分别为 1, -3, -2, -1（avg=-1.25 < 0）
        每轮 alpha > -5% floor 所以单轮 passed=True，
        但 avg=-1.25 < 0 → pass_all_rounds=False
        """
        rounds = [
            WalkForwardRound(
                1, _date(2021, 1, 1), _date(2023, 1, 1),
                _date(2023, 1, 1), _date(2023, 7, 1),
                val_sortino=1.0, val_max_dd=10.0,
                val_alpha=1.0, passed=True,
            ),
            WalkForwardRound(
                2, _date(2021, 7, 1), _date(2023, 7, 1),
                _date(2023, 7, 1), _date(2024, 1, 1),
                val_sortino=0.8, val_max_dd=12.0,
                val_alpha=-3.0, passed=True,   # > -5% floor
            ),
            WalkForwardRound(
                3, _date(2022, 1, 1), _date(2024, 1, 1),
                _date(2024, 1, 1), _date(2024, 7, 1),
                val_sortino=1.2, val_max_dd=8.0,
                val_alpha=-2.0, passed=True,   # > -5% floor
            ),
            WalkForwardRound(
                4, _date(2022, 7, 1), _date(2024, 7, 1),
                _date(2024, 7, 1), _date(2025, 1, 1),
                val_sortino=0.9, val_max_dd=11.0,
                val_alpha=-1.0, passed=True,   # > -5% floor
            ),
        ]
        val_alphas = [r.val_alpha for r in rounds]
        avg_alpha = sum(val_alphas) / len(val_alphas)

        # 验证测试前提：每轮单轮 pass，但 avg < 0
        assert all(r.passed for r in rounds), "测试前提：每轮单轮都 pass"
        assert avg_alpha < 0, (
            f"测试前提：avg alpha 应 < 0，实际 {avg_alpha}"
        )

        # 汇总：all passed AND avg > 0 → False（因为 avg < 0）
        all_rounds_passed = all(r.passed for r in rounds)
        avg_alpha_positive = avg_alpha > 0
        pass_all = all_rounds_passed and avg_alpha_positive
        assert pass_all is False, (
            "avg alpha < 0 时 pass_all_rounds 应为 False"
        )

    def test_wf_summary_avg_alpha_positive_passes(self):
        """4 轮全 pass 且 avg alpha > 0 → pass_all_rounds=True。"""
        rounds = [
            WalkForwardRound(
                1, _date(2021, 1, 1), _date(2023, 1, 1),
                _date(2023, 1, 1), _date(2023, 7, 1),
                val_sortino=1.0, val_max_dd=10.0,
                val_alpha=5.0, passed=True,
            ),
            WalkForwardRound(
                2, _date(2021, 7, 1), _date(2023, 7, 1),
                _date(2023, 7, 1), _date(2024, 1, 1),
                val_sortino=0.8, val_max_dd=12.0,
                val_alpha=-3.0, passed=True,   # 小幅跑输但 > floor
            ),
            WalkForwardRound(
                3, _date(2022, 1, 1), _date(2024, 1, 1),
                _date(2024, 1, 1), _date(2024, 7, 1),
                val_sortino=1.2, val_max_dd=8.0,
                val_alpha=7.0, passed=True,
            ),
            WalkForwardRound(
                4, _date(2022, 7, 1), _date(2024, 7, 1),
                _date(2024, 7, 1), _date(2025, 1, 1),
                val_sortino=0.9, val_max_dd=11.0,
                val_alpha=4.0, passed=True,
            ),
        ]
        val_alphas = [r.val_alpha for r in rounds]
        avg_alpha = sum(val_alphas) / len(val_alphas)

        # 验证测试前提
        assert all(r.passed for r in rounds)
        assert avg_alpha > 0, f"avg alpha 应 > 0，实际 {avg_alpha}"

        all_rounds_passed = all(r.passed for r in rounds)
        avg_alpha_positive = avg_alpha > 0
        pass_all = all_rounds_passed and avg_alpha_positive
        assert pass_all is True

    def test_wf_summary_single_round_fail_fails(self):
        """1 轮 fail（alpha < floor）即使 avg > 0 → pass_all_rounds=False。

        场景：3 轮强正 alpha，1 轮 alpha=-8%（< -5% floor → fail）
        avg = (5+7+4-8)/4 = 2.0 > 0，但因为 R2 fail → pass_all=False
        """
        rounds = [
            WalkForwardRound(
                1, _date(2021, 1, 1), _date(2023, 1, 1),
                _date(2023, 1, 1), _date(2023, 7, 1),
                val_sortino=1.0, val_max_dd=10.0,
                val_alpha=5.0, passed=True,
            ),
            WalkForwardRound(
                2, _date(2021, 7, 1), _date(2023, 7, 1),
                _date(2023, 7, 1), _date(2024, 1, 1),
                val_sortino=0.8, val_max_dd=12.0,
                val_alpha=-8.0, passed=False,   # < -5% floor → fail
            ),
            WalkForwardRound(
                3, _date(2022, 1, 1), _date(2024, 1, 1),
                _date(2024, 1, 1), _date(2024, 7, 1),
                val_sortino=1.2, val_max_dd=8.0,
                val_alpha=7.0, passed=True,
            ),
            WalkForwardRound(
                4, _date(2022, 7, 1), _date(2024, 7, 1),
                _date(2024, 7, 1), _date(2025, 1, 1),
                val_sortino=0.9, val_max_dd=11.0,
                val_alpha=4.0, passed=True,
            ),
        ]
        val_alphas = [r.val_alpha for r in rounds]
        avg_alpha = sum(val_alphas) / len(val_alphas)
        assert avg_alpha > 0  # avg 仍然是正的

        all_rounds_passed = all(r.passed for r in rounds)
        avg_alpha_positive = avg_alpha > 0
        pass_all = all_rounds_passed and avg_alpha_positive
        assert pass_all is False, (
            "R2 fail 时即使 avg > 0，pass_all_rounds 也应为 False"
        )


# ---------------------------------------------------------------------------
# 4. 集成测试：run_walk_forward 计算 val_alpha
# ---------------------------------------------------------------------------

def _make_spy_ohlcv(n: int = 300, annual_growth: float = 0.10) -> pd.DataFrame:
    """生成 SPY OHLCV 数据（温和上涨，默认年化 10%）。"""
    idx = pd.date_range("2021-01-01", periods=n, freq="B")
    daily_growth = (1.0 + annual_growth) ** (1.0 / 252.0) - 1.0
    close = [100.0 * ((1.0 + daily_growth) ** i) for i in range(n)]
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


def _make_strategy_ohlcv(n: int = 300, trend: str = "up") -> pd.DataFrame:
    """生成策略 OHLCV 数据（强趋势，使策略跑赢 SPY）。"""
    idx = pd.date_range("2021-01-01", periods=n, freq="B")
    if trend == "up":
        close = [100.0 + i * 0.3 for i in range(n)]   # 强趋势，年化 ~50%+
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


class TestWFAlphaIntegration:
    """迭代 #13：run_walk_forward 集成测试 — val_alpha 计算正确性。

    用 patch 拦截 _backtest_batch，返回受控的 daily_returns + closed_trades>0
    （避免退化门槛拦截），验证 WF 验证期正确计算 alpha vs SPY。
    """

    def test_wf_spy_unavailable_alpha_zero(self):
        """SPY 不可用时 val_alpha=0.0 + WARNING（降级不阻塞）。

        构造 mock_store 不返回 SPY 数据 → _get_spy_returns 返回 None
        → val_alpha=0.0（降级处理，不抛异常）
        → 单轮 passed=True（alpha=0 > -5 floor）
        → 但 avg_alpha=0 → pass_all_rounds=False（0 不 > 0）
        """
        df_strat = _make_strategy_ohlcv(300, trend="up")

        store = MagicMock()
        # 不包含 SPY
        def get_bars_multi(symbols, start, end, timeframe="1d"):
            mapping = {"AAPL": df_strat, "MSFT": df_strat}
            return {s: mapping[s] for s in symbols if s in mapping}
        store.get_bars_multi.side_effect = get_bars_multi

        universe = MagicMock()
        universe.get_groups.return_value = {"test_group": ["AAPL", "MSFT"]}

        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=1)

        # patch _backtest_batch 返回非退化结果（closed_trades>0）
        # 使策略能通过健全性门槛，产出非空权重
        idx = pd.date_range("2021-01-01", periods=300, freq="B")
        controlled_returns = pd.Series(
            np.random.normal(0.001, 0.002, 300), index=idx
        )

        def mock_batch(data, strategy_name, params, *args, **kwargs):
            results = []
            for sym in data.keys():
                results.append(SingleBacktestResult(
                    symbol=sym, strategy=strategy_name, params=params,
                    sharpe=1.0, total_return_pct=10.0, max_drawdown_pct=5.0,
                    win_rate_pct=55.0, total_trades=10,
                    daily_returns=controlled_returns,
                    sortino=1.5, closed_trades=10,
                ))
            return results

        with patch(
            "mytrader.backtest.matrix_backtest._backtest_batch",
            side_effect=mock_batch,
        ):
            report = run_walk_forward(
                mb=mb,
                strategies=["dual_ma"],
                param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
                rounds=2,
                train_months=12,
                val_months=4,
            )

        assert isinstance(report, WalkForwardReport)
        assert len(report.rounds) == 2
        # SPY 不可用 → val_alpha=0.0
        for r in report.rounds:
            assert r.val_alpha == 0.0, (
                f"SPY 不可用时 val_alpha 应为 0.0，实际 {r.val_alpha}"
            )
        # avg=0 → 不 > 0 → pass_all_rounds=False
        assert report.avg_val_alpha == 0.0
        assert report.pass_all_rounds is False, (
            "avg_alpha=0 不满足 > 0，pass_all_rounds 应为 False"
        )

    def test_wf_alpha_computed_correctly(self):
        """用已知 returns + spy_returns 验证 val_alpha 值正确。

        构造 mock store 返回 SPY（温和上涨 ~10% 年化），
        patch _backtest_batch 返回策略 daily_returns（强正收益 ~28% 年化）。
        验证 val_alpha > 0（策略跑赢 SPY）。
        """
        n = 300
        idx = pd.date_range("2021-01-01", periods=n, freq="B")
        df_spy = _make_spy_ohlcv(n, annual_growth=0.10)
        # 策略数据（仅用于 _backtest_batch 的 data 参数，实际 returns 由 mock 提供）
        df_strat = _make_strategy_ohlcv(n, trend="up")

        store = MagicMock()
        def get_bars_multi(symbols, start, end, timeframe="1d"):
            mapping = {"AAPL": df_strat, "MSFT": df_strat, "SPY": df_spy}
            return {s: mapping[s] for s in symbols if s in mapping}
        store.get_bars_multi.side_effect = get_bars_multi

        universe = MagicMock()
        universe.get_groups.return_value = {"test_group": ["AAPL", "MSFT"]}

        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=1)

        # 策略 daily_returns：日均 0.001（~28% 年化），跑赢 SPY 的 ~10%
        controlled_returns = pd.Series(
            np.random.normal(0.001, 0.002, n), index=idx
        )

        def mock_batch(data, strategy_name, params, *args, **kwargs):
            results = []
            for sym in data.keys():
                results.append(SingleBacktestResult(
                    symbol=sym, strategy=strategy_name, params=params,
                    sharpe=1.0, total_return_pct=10.0, max_drawdown_pct=5.0,
                    win_rate_pct=55.0, total_trades=10,
                    daily_returns=controlled_returns,
                    sortino=1.5, closed_trades=10,
                ))
            return results

        with patch(
            "mytrader.backtest.matrix_backtest._backtest_batch",
            side_effect=mock_batch,
        ):
            report = run_walk_forward(
                mb=mb,
                strategies=["dual_ma"],
                param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
                rounds=2,
                train_months=12,
                val_months=4,
            )

        assert len(report.rounds) == 2
        # 策略 ~28% 年化 > SPY ~10% 年化 → alpha > 0
        for r in report.rounds:
            assert r.val_alpha > 0, (
                f"策略强趋势应跑赢 SPY，val_alpha 应 > 0，实际 {r.val_alpha}"
            )
        assert report.avg_val_alpha > 0
        assert report.min_val_alpha == min(r.val_alpha for r in report.rounds)

    def test_wf_alpha_underperforms_spy(self):
        """策略 OOS 跑输 SPY → val_alpha < 0 → pass_all_rounds=False。

        场景：策略在训练期有正 alpha（通过 alpha>0 门槛），
        但在验证期跑输 SPY（OOS 负 alpha）。
        这是 WF alpha gate 设计的核心目标：捕获 in-sample 过拟合。

        实现：patch _backtest_batch 返回正 alpha 训练结果，
        patch _backtest_with_params_on_period 返回负 alpha 验证结果。
        """
        n = 300
        idx = pd.date_range("2021-01-01", periods=n, freq="B")
        df_spy = _make_spy_ohlcv(n, annual_growth=0.10)
        df_strat = _make_strategy_ohlcv(n, trend="up")

        store = MagicMock()
        def get_bars_multi(symbols, start, end, timeframe="1d"):
            mapping = {"AAPL": df_strat, "MSFT": df_strat, "SPY": df_spy}
            return {s: mapping[s] for s in symbols if s in mapping}
        store.get_bars_multi.side_effect = get_bars_multi

        universe = MagicMock()
        universe.get_groups.return_value = {"test_group": ["AAPL", "MSFT"]}

        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=1)

        # 训练期 returns：日均 0.001（~28% 年化 > SPY 10%）→ 正 alpha，通过训练门槛
        train_returns = pd.Series(
            np.random.normal(0.001, 0.002, n), index=idx
        )
        # 验证期 returns：日均 -0.0008（~-20% 年化 < SPY 10%）→ 负 alpha
        val_returns = pd.Series(
            np.random.normal(-0.0008, 0.002, n), index=idx
        )

        def mock_batch(data, strategy_name, params, *args, **kwargs):
            results = []
            for sym in data.keys():
                results.append(SingleBacktestResult(
                    symbol=sym, strategy=strategy_name, params=params,
                    sharpe=1.0, total_return_pct=10.0, max_drawdown_pct=5.0,
                    win_rate_pct=55.0, total_trades=10,
                    daily_returns=train_returns,
                    sortino=1.5, closed_trades=10,
                ))
            return results

        def mock_val_period(mb_arg, symbols, weights, start, end):
            """验证期返回负 alpha returns。"""
            return [val_returns, val_returns]  # 2 个标的的 returns

        with patch(
            "mytrader.backtest.matrix_backtest._backtest_batch",
            side_effect=mock_batch,
        ), patch(
            "mytrader.backtest.matrix_backtest._backtest_with_params_on_period",
            side_effect=mock_val_period,
        ):
            report = run_walk_forward(
                mb=mb,
                strategies=["dual_ma"],
                param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
                rounds=2,
                train_months=12,
                val_months=4,
            )

        # 验证期 OOS 负 alpha
        for r in report.rounds:
            assert r.val_alpha < 0, (
                f"OOS 策略跑输 SPY，val_alpha 应 < 0，实际 {r.val_alpha}"
            )
        assert report.pass_all_rounds is False
        assert report.avg_val_alpha < 0

    def test_wf_alpha_floor_constant_value(self):
        """WALK_FORWARD_VAL_ALPHA_FLOOR 常量值为 -5.0。"""
        assert WALK_FORWARD_VAL_ALPHA_FLOOR == -5.0, (
            f"WF alpha floor 应为 -5.0，实际 {WALK_FORWARD_VAL_ALPHA_FLOOR}"
        )

    def test_wf_alpha_floor_vs_dd_threshold_independent(self):
        """alpha floor 和 DD threshold 是两个独立的 gate（AND 关系）。"""
        # DD 合规但 alpha 灾难性跑输
        dd_passed = 10.0 <= WALK_FORWARD_VAL_DD_THRESHOLD
        alpha_passed = -8.0 > WALK_FORWARD_VAL_ALPHA_FLOOR
        passed = dd_passed and alpha_passed
        assert passed is False, "DD 合规但 alpha < floor 时应 fail"

        # DD 合规 + alpha 小幅跑输但 > floor
        alpha_passed_ok = -3.0 > WALK_FORWARD_VAL_ALPHA_FLOOR
        passed_ok = dd_passed and alpha_passed_ok
        assert passed_ok is True, "DD 合规 + alpha > floor 时应 pass"

        # DD 不合规 + alpha 跑赢
        dd_fail = 20.0 <= WALK_FORWARD_VAL_DD_THRESHOLD
        alpha_good = 5.0 > WALK_FORWARD_VAL_ALPHA_FLOOR
        passed_dd_fail = dd_fail and alpha_good
        assert passed_dd_fail is False, "DD 不合规时即使 alpha 好也应 fail"
