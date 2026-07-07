"""迭代 #11：选择器健全性门槛测试（Reject Degenerate Strategies）。

验证：
    1. `SingleBacktestResult.closed_trades` 字段被正确填充（normal 策略 > 0）
    2. `_backtest_batch` 与 `_backtest_one` 对同一标的的 `closed_trades` 一致
    3. `_is_degenerate_strategy` 正确识别"近乎全标的零平仓"的退化策略
    4. 正常闭环策略不被误判为退化
    5. `_run_group` 在排序前剔除退化策略（不出现在返回的 weights_list）
    6. 全退化组返回空权重 + `no_valid_strategy=True` 标记
    7. 低频但有平仓交易的策略不被误伤（0.8 阈值边界）

背景见 `iterations/iteration_11/spec.md` + `tmp/iteration10_audit.md`。
"""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from mytrader.backtest.matrix_backtest import (
    DEGENERATE_NO_CLOSE_FRACTION,
    GroupBacktestResult,
    MatrixBacktest,
    MatrixBacktestReport,
    SingleBacktestResult,
    _backtest_batch,
    _backtest_one,
    _is_degenerate_strategy,
)


# ---------------------------------------------------------------------------
# Test data generators（与 test_batch_backtest.py 同风格）
# ---------------------------------------------------------------------------

def _make_ohlcv(
    n: int = 300,
    trend: str = "random",
    seed: int | None = None,
    start: str = "2021-01-01",
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


def _make_multi_symbol_data(
    symbols: list[str],
    n: int = 300,
    trend: str = "random",
    seed: int = 42,
) -> dict[str, pd.DataFrame]:
    """生成多标的 OHLCV 数据字典（每标的独立生成、起始日期对齐）。"""
    return {
        sym: _make_ohlcv(n=n, trend=trend, seed=seed + i)
        for i, sym in enumerate(symbols)
    }


def _make_mock_store(data_by_symbol: dict[str, pd.DataFrame]) -> MagicMock:
    """构造 Mock MarketDataStore，get_bars_multi 返回指定数据。"""
    store = MagicMock()

    def get_bars_multi(symbols, start, end, timeframe="1d"):
        return {
            s: data_by_symbol[s] for s in symbols if s in data_by_symbol
        }

    store.get_bars_multi.side_effect = get_bars_multi
    return store


def _make_mock_universe(groups: dict[str, list[str]]) -> MagicMock:
    """构造 Mock UniverseManager，get_groups 返回指定分组。"""
    universe = MagicMock()
    universe.get_groups.return_value = groups
    return universe


# ---------------------------------------------------------------------------
# Test 1: closed_trades 字段被正确填充
# ---------------------------------------------------------------------------

class TestClosedTradesPopulated:
    """验证 SingleBacktestResult.closed_trades 字段被正确填充。"""

    def test_closed_trades_field_exists_with_default(self):
        """SingleBacktestResult 默认 closed_trades=0。"""
        r = SingleBacktestResult(
            symbol="X", strategy="s", params={}, sharpe=0.0,
            total_return_pct=0.0, max_drawdown_pct=0.0, win_rate_pct=0.0,
            total_trades=0, daily_returns=pd.Series(dtype=float),
        )
        assert hasattr(r, "closed_trades")
        assert r.closed_trades == 0

    def test_closed_trades_populated_normal_strategy(self):
        """正常策略（dual_ma）在 random walk 数据上应有 closed_trades > 0。"""
        df = _make_ohlcv(300, trend="random", seed=42)
        df.index.name = "AAA"
        r = _backtest_one(df, "dual_ma", {"fast": 5, "slow": 20})
        assert r is not None, "_backtest_one 应返回结果（非 None）"
        assert r.closed_trades > 0, (
            f"dual_ma 在 300 bar random walk 上应有已平仓交易，"
            f"实际 closed_trades={r.closed_trades}"
        )
        # closed_trades 不应超过 total_trades
        assert r.closed_trades <= r.total_trades, (
            f"closed_trades({r.closed_trades}) 应 <= total_trades({r.total_trades})"
        )

    def test_closed_trades_zero_for_entries_only_strategy(self):
        """只有 entry 信号没有 exit 信号的策略 closed_trades=0。

        构造方法：用 rsi_trend_filter 在强趋势上涨数据上跑 —— 趋势过滤锁死
        出场条件，仓位只能挂到末尾被 vbt 强平。
        """
        # 强趋势上涨数据：close > SMA200 全程成立 → SELL 信号几乎不触发
        df = _make_ohlcv(400, trend="up")
        df.index.name = "UPTREND"
        r = _backtest_one(
            df, "rsi_trend_filter",
            {"rsi_period": 14, "oversold": 30, "overbought": 70, "trend_period": 200},
        )
        # rsi_trend_filter 在强上涨趋势中可能 rsi 一直不超卖 → 0 entries → 0 trades
        # 或者偶尔超卖买入但无法触发 SELL（出场需 close<SMA200）→ 0 closed_trades
        if r is not None:
            # 退化情形：closed_trades 应为 0（无法完成交易闭环）
            assert r.closed_trades == 0, (
                f"rsi_trend_filter 在强上涨趋势上 closed_trades 应为 0（退化），"
                f"实际 {r.closed_trades}"
            )


# ---------------------------------------------------------------------------
# Test 2: batch vs single 一致性（closed_trades）
# ---------------------------------------------------------------------------

class TestClosedTradesBatchConsistency:
    """验证 _backtest_batch 与 _backtest_one 对同一标的 closed_trades 一致。"""

    @pytest.mark.parametrize(
        "strategy_name, params",
        [
            ("dual_ma", {"fast": 5, "slow": 20}),
            ("rsi_mean_revert", {"period": 14, "oversold": 30, "overbought": 70}),
            ("macd_cross", {"fast": 12, "slow": 26, "signal_period": 9}),
            ("bollinger_band", {"period": 20, "std_dev": 2.0}),
        ],
    )
    def test_closed_trades_batch_matches_single(
        self, strategy_name: str, params: dict
    ) -> None:
        """每个策略 batch 与 single 的 closed_trades 严格一致。"""
        data = _make_multi_symbol_data(
            ["AAA", "BBB", "CCC"], n=300, trend="random", seed=200
        )

        # 逐标的 single
        single_results: dict[str, SingleBacktestResult | None] = {}
        for sym, df in data.items():
            df = df.copy()
            df.index.name = sym
            single_results[sym] = _backtest_one(df, strategy_name, params)

        # batch
        batch_results_list = _backtest_batch(data, strategy_name, params)
        batch_results = {r.symbol: r for r in batch_results_list}

        for sym, single_r in single_results.items():
            if single_r is None:
                assert sym not in batch_results, (
                    f"{strategy_name}/{params} {sym}: single=None but batch returned result"
                )
                continue
            assert sym in batch_results, (
                f"{strategy_name}/{params} {sym}: single returned result but batch dropped"
            )
            batch_r = batch_results[sym]
            assert single_r.closed_trades == batch_r.closed_trades, (
                f"{strategy_name}/{params} {sym}: closed_trades mismatch — "
                f"single={single_r.closed_trades}, batch={batch_r.closed_trades}"
            )

    def test_closed_trades_batch_matches_single_multi_symbol(self):
        """多标的（5 个）下 batch 的 closed_trades 与 single 逐一一致。"""
        data = _make_multi_symbol_data(
            ["AAA", "BBB", "CCC", "DDD", "EEE"], n=400, trend="random", seed=300
        )

        single_closed: dict[str, int] = {}
        for sym, df in data.items():
            df = df.copy()
            df.index.name = sym
            r = _backtest_one(df, "dual_ma", {"fast": 5, "slow": 20})
            single_closed[sym] = r.closed_trades if r is not None else -1

        batch_results = _backtest_batch(data, "dual_ma", {"fast": 5, "slow": 20})
        batch_closed = {r.symbol: r.closed_trades for r in batch_results}

        for sym, expected in single_closed.items():
            if expected == -1:
                assert sym not in batch_closed
            else:
                assert sym in batch_closed, f"{sym} missing from batch results"
                assert batch_closed[sym] == expected, (
                    f"{sym}: single closed_trades={expected}, "
                    f"batch closed_trades={batch_closed[sym]}"
                )


# ---------------------------------------------------------------------------
# Test 3-4: _is_degenerate_strategy 函数行为
# ---------------------------------------------------------------------------

class TestIsDegenerateStrategy:
    """_is_degenerate_strategy 单元测试。"""

    def test_empty_results_is_degenerate(self):
        """空结果列表视为退化（True）—— 没有数据不应强行选策略。"""
        assert _is_degenerate_strategy([]) is True

    def test_all_zero_closed_is_degenerate(self):
        """所有标的 closed_trades=0 → 退化。"""
        results = [
            SingleBacktestResult(
                f"S{i}", "s", {}, 0.0, 0.0, 0.0, 0.0, 0,
                pd.Series(dtype=float), closed_trades=0,
            )
            for i in range(5)
        ]
        assert _is_degenerate_strategy(results) is True

    def test_normal_closed_trades_not_degenerate(self):
        """所有标的都有平仓交易 → 不退化。"""
        results = [
            SingleBacktestResult(
                f"S{i}", "s", {}, 0.0, 0.0, 0.0, 0.0, 5,
                pd.Series(dtype=float), closed_trades=5,
            )
            for i in range(5)
        ]
        assert _is_degenerate_strategy(results) is False

    def test_threshold_boundary_80pct(self):
        """边界：5 标的中有 4 个 closed=0（4/5=0.8）→ 退化（>= 阈值）。"""
        # DEGENERATE_NO_CLOSE_FRACTION = 0.8, 边界 4/5=0.8 应触发
        results = [
            SingleBacktestResult(
                f"S{i}", "s", {}, 0.0, 0.0, 0.0, 0.0, 0,
                pd.Series(dtype=float), closed_trades=0,
            )
            for i in range(4)
        ] + [
            SingleBacktestResult(
                "S4", "s", {}, 0.0, 0.0, 0.0, 0.0, 3,
                pd.Series(dtype=float), closed_trades=3,
            )
        ]
        assert _is_degenerate_strategy(results) is True, (
            f"4/5 = 0.8 应触发退化（>= {DEGENERATE_NO_CLOSE_FRACTION}）"
        )

    def test_below_threshold_not_degenerate(self):
        """边界：5 标的中有 3 个 closed=0（3/5=0.6）→ 不退化。"""
        results = [
            SingleBacktestResult(
                f"S{i}", "s", {}, 0.0, 0.0, 0.0, 0.0, 0,
                pd.Series(dtype=float), closed_trades=0,
            )
            for i in range(3)
        ] + [
            SingleBacktestResult(
                f"S{i}", "s", {}, 0.0, 0.0, 0.0, 0.0, 3,
                pd.Series(dtype=float), closed_trades=3,
            )
            for i in range(2)
        ]
        assert _is_degenerate_strategy(results) is False, (
            f"3/5 = 0.6 < {DEGENERATE_NO_CLOSE_FRACTION}，不应触发退化"
        )

    def test_low_frequency_strategy_not_falsely_excluded(self):
        """低频但闭环的策略（每标的 2-3 笔 closed_trades）不被误伤。

        这是 spec §5.7 的边界测试：0.8 阈值应只拦"近乎全标的零平仓"，
        不应误伤合法低频策略（如 monthly rebalance 类）。
        """
        # 5 个标的，每个都有 2-3 笔平仓交易（典型低频合法策略）
        results = [
            SingleBacktestResult(
                f"S{i}", "low_freq", {}, 0.5, 8.0, 5.0, 55.0, 2,
                pd.Series(dtype=float), closed_trades=2,
            )
            for i in range(5)
        ]
        assert _is_degenerate_strategy(results) is False, (
            "低频但每标的都有平仓交易的策略不应被误判为退化"
        )

    def test_mixed_one_zero_not_degenerate(self):
        """5 标的中 1 个 closed=0（1/5=0.2）→ 不退化。

        单只标的无平仓（如刚上市数据不足）不应牵连整组判定。
        """
        results = [
            SingleBacktestResult(
                "S0", "s", {}, 0.0, 0.0, 0.0, 0.0, 0,
                pd.Series(dtype=float), closed_trades=0,
            )
        ] + [
            SingleBacktestResult(
                f"S{i}", "s", {}, 0.0, 0.0, 0.0, 0.0, 5,
                pd.Series(dtype=float), closed_trades=5,
            )
            for i in range(1, 5)
        ]
        assert _is_degenerate_strategy(results) is False

    def test_degenerate_threshold_constant_value(self):
        """DEGENERATE_NO_CLOSE_FRACTION 常量值为 0.8（保守阈值）。"""
        assert DEGENERATE_NO_CLOSE_FRACTION == 0.8


# ---------------------------------------------------------------------------
# Test 5-6: _run_group 集成（剔除退化 + 全退化空仓）
# ---------------------------------------------------------------------------

class TestRunGroupDegenerateIntegration:
    """_run_group 集成健全性门槛测试。"""

    def test_degenerate_excluded_from_weights(self):
        """退化策略不出现在返回的 weights_list。

        场景：mock _backtest_batch 让 dual_ma 退化（closed_trades=0），
        rsi_mean_revert 正常（closed_trades>0）。top_k=2 时应只选
        rsi_mean_revert，dual_ma 被健全性门槛剔除。
        """
        n = 300
        idx = pd.date_range("2021-01-01", periods=n, freq="B")
        np.random.seed(42)
        returns_a = pd.Series(np.random.normal(0.001, 0.005, n), index=idx)
        returns_b = pd.Series(np.random.normal(0.0008, 0.003, n), index=idx)

        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
            results = []
            for sym, df in data.items():
                if df is None or df.empty or len(df) < 30:
                    continue
                if strategy_name == "dual_ma":
                    # 退化：closed_trades=0（mock 模拟 rsi_trend_filter 退化行为）
                    results.append(SingleBacktestResult(
                        sym, strategy_name, params, 1.0, 10.0, 5.0, 55.0, 1, returns_a,
                        closed_trades=0,
                    ))
                else:  # rsi_mean_revert
                    results.append(SingleBacktestResult(
                        sym, strategy_name, params, 1.0, 20.0, 5.0, 55.0, 10, returns_b,
                        closed_trades=10,
                    ))
            return results

        # 5 标的让退化比例 5/5=100% ≥ 0.8
        data = _make_multi_symbol_data(
            ["AAA", "BBB", "CCC", "DDD", "EEE"], n=300, trend="random", seed=11
        )
        # 迭代 #12：alpha>0 门槛需要 SPY benchmark 数据。
        # rsi_mean_revert 的 mock returns 均值 0.0008（年化 ~22%），
        # 用 trend="down" 的 SPY（年化 ~-13%）确保 alpha > 0。
        data_with_spy = dict(data)
        data_with_spy["SPY"] = _make_ohlcv(300, trend="down")
        store = _make_mock_store(data_with_spy)
        universe = _make_mock_universe({"test_group": list(data.keys())})

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
                symbols=list(data.keys()),
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

        # 退化策略 dual_ma 不应在权重中
        strategies_in_weights = [w["strategy"] for w in weights]
        assert "dual_ma" not in strategies_in_weights, (
            f"dual_ma（退化）不应出现在权重中，实际 weights={strategies_in_weights}"
        )
        assert "rsi_mean_revert" in strategies_in_weights, (
            f"rsi_mean_revert（正常）应在权重中，实际 weights={strategies_in_weights}"
        )

    def test_all_degenerate_group_returns_empty_weights(self):
        """全退化组返回空权重 + no_valid_strategy 标记。

        场景：mock _backtest_batch 让所有策略 closed_trades=0（全退化）。
        验证：返回空 weights_list，report.group_results 中对应组条目
        被标记 no_valid_strategy=True，report.warnings 含标记。
        """
        n = 300
        idx = pd.date_range("2021-01-01", periods=n, freq="B")
        np.random.seed(42)
        returns_a = pd.Series(np.random.normal(0.001, 0.005, n), index=idx)
        returns_b = pd.Series(np.random.normal(0.0008, 0.003, n), index=idx)

        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
            results = []
            for sym, df in data.items():
                if df is None or df.empty or len(df) < 30:
                    continue
                if strategy_name == "dual_ma":
                    results.append(SingleBacktestResult(
                        sym, strategy_name, params, 1.0, 10.0, 5.0, 55.0, 1, returns_a,
                        closed_trades=0,
                    ))
                else:
                    results.append(SingleBacktestResult(
                        sym, strategy_name, params, 1.0, 20.0, 5.0, 55.0, 1, returns_b,
                        closed_trades=0,
                    ))
            return results

        data = _make_multi_symbol_data(
            ["AAA", "BBB", "CCC", "DDD", "EEE"], n=300, trend="random", seed=22
        )
        store = _make_mock_store(data)
        universe = _make_mock_universe({"test_group": list(data.keys())})

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
                symbols=list(data.keys()),
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
        assert weights == [], (
            f"全退化组应返回空权重，实际 weights={weights}"
        )
        # report.warnings 含 no_valid_strategy 标记
        warning_text = " ".join(report.warnings)
        assert "no_valid_strategy" in warning_text, (
            f"report.warnings 应含 no_valid_strategy 标记，实际 warnings={report.warnings}"
        )
        assert "test_group" in warning_text
        # 对应 group_results 条目被标记 no_valid_strategy=True
        # （健全性过滤发生在 candidates 构建前，但 group_results 在
        # per-strategy best params 阶段已 append，应被标记）
        test_group_results = [
            gr for gr in report.group_results if gr.group_id == "test_group"
        ]
        assert len(test_group_results) > 0, (
            "test_group 应在 report.group_results 中有存档条目（供审计追溯）"
        )
        for gr in test_group_results:
            assert gr.no_valid_strategy is True, (
                f"test_group 的 GroupBacktestResult.no_valid_strategy 应为 True，"
                f"实际 {gr.no_valid_strategy}"
            )

    def test_no_valid_strategy_field_default_false(self):
        """GroupBacktestResult.no_valid_strategy 默认 False。"""
        gr = GroupBacktestResult(
            group_id="g", strategy="s", params={}, portfolio_sharpe=0.0,
            avg_total_return_pct=0.0, avg_max_drawdown_pct=0.0,
            avg_win_rate_pct=0.0, symbol_count=0,
        )
        assert gr.no_valid_strategy is False

    def test_normal_strategies_unaffected_by_filter(self):
        """正常策略（都有平仓交易）不被健全性门槛影响，权重正常产出。

        验证健全性门槛不会误伤正常策略 —— 用真实 _backtest_batch（不 mock）
        跑 dual_ma 在 random walk 数据上，应正常产出权重，且不触发
        no_valid_strategy 标记。

        迭代 #12：新增 alpha>0 门槛后，需确保 mock 的策略 alpha > 0。
        用 trend="down" 的 SPY（负收益）确保 dual_ma 在 random walk 上
        的收益跑赢 SPY（alpha > 0）。
        """
        data = _make_multi_symbol_data(
            ["AAA", "BBB", "CCC"], n=300, trend="random", seed=33
        )
        # 迭代 #12：加 SPY benchmark（trend="down" → 负收益），
        # 确保 dual_ma 的 random walk 收益跑赢 SPY（alpha > 0）
        data_with_spy = dict(data)
        data_with_spy["SPY"] = _make_ohlcv(300, trend="down")
        store = _make_mock_store(data_with_spy)
        universe = _make_mock_universe({"test_group": list(data.keys())})

        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
        report = MatrixBacktestReport(
            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
            backtest_window="2021-01-01 ~ 2022-01-01",
            groups={},
        )

        weights = mb._run_group(
            group_id="test_group",
            symbols=list(data.keys()),
            start=date(2021, 1, 1),
            end=date(2022, 1, 1),
            strategies=["dual_ma"],
            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
            report=report,
        )

        # 正常策略应产出权重
        assert len(weights) >= 1, (
            f"dual_ma 在 random walk 上应正常产出权重，实际 weights={weights}"
        )
        # 不应触发 no_valid_strategy
        for gr in report.group_results:
            if gr.group_id == "test_group":
                assert gr.no_valid_strategy is False, (
                    "正常策略组不应被标记 no_valid_strategy=True"
                )
        # weights 中应有 backtest_dd_status 字段（验证下游逻辑未被破坏）
        for w in weights:
            assert "strategy" in w
            assert "weight" in w
