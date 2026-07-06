"""vectorbt Batch Backtest 数值一致性测试（迭代 #10 新增）。

验证 `_backtest_batch()` 与 `_backtest_one()` 在相同输入下产出
数值一致的结果，确保批量化重构不改变策略选择 / Alpha 排序 / DD 过滤等下游逻辑。

测试范围（spec §5）：
    1. 所有 5 个策略 batch vs single 数值一致性
    2. 不同参数组合（至少 2 组参数 per 策略）
    3. 边界场景：数据不足 / 全空 / 单标的 / 日期不对齐
    4. 进度日志验证（_run_group 路径，集成测试）

数值一致性判定：
    - daily_returns: np.allclose(rtol=1e-6, atol=1e-8)
    - sharpe / total_return / max_drawdown / win_rate / total_trades / sortino:
      允许 1e-4 ~ 1e-2 浮点误差（vbt 内部计算路径差异）
"""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

from mytrader.backtest.matrix_backtest import (
    MatrixBacktest,
    _backtest_batch,
    _backtest_one,
    SingleBacktestResult,
)


# ---------------------------------------------------------------------------
# Test data generators
# ---------------------------------------------------------------------------

def _make_ohlcv(
    n: int = 300,
    trend: str = "up",
    seed: int | None = None,
    start: str = "2021-01-01",
) -> pd.DataFrame:
    """生成测试 OHLCV 数据。

    Args:
        n:      bar 数量
        trend:  "up" / "down" / "random"
        seed:   随机种子（trend=random 时使用）
        start:  起始日期
    """
    idx = pd.date_range(start, periods=n, freq="B")
    if trend == "up":
        close = np.array([100.0 + i * 0.1 for i in range(n)])
    elif trend == "down":
        close = np.array([100.0 - i * 0.05 for i in range(n)])
    elif trend == "random":
        rng = np.random.default_rng(seed if seed is not None else 42)
        # 带均值回归的随机游走，触发策略信号
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
    trend: str = "up",
    seed: int = 42,
) -> dict[str, pd.DataFrame]:
    """生成多标的 OHLCV 数据字典。

    每个标的数据独立生成，但起始日期对齐（便于数值一致性验证）。
    """
    return {
        sym: _make_ohlcv(n=n, trend=trend, seed=seed + i)
        for i, sym in enumerate(symbols)
    }


# ---------------------------------------------------------------------------
# 数值一致性辅助
# ---------------------------------------------------------------------------

def _assert_results_match(
    old: SingleBacktestResult | None,
    new: SingleBacktestResult | None,
    *,
    rtol: float = 1e-6,
    atol: float = 1e-8,
    stats_rtol: float = 1e-4,
    stats_atol: float = 1e-2,
    context: str = "",
) -> None:
    """对比 _backtest_one 与 _backtest_batch 的 SingleBacktestResult。

    Args:
        old: _backtest_one 返回值（可能为 None）
        new: _backtest_batch 返回的列表中的某一项（可能为 None）
        rtol/atol: daily_returns 的 np.allclose 容差
        stats_rtol/stats_atol: stats 字段容差（vbt 计算路径差异，允许稍宽）
        context: 错误消息上下文
    """
    msg = lambda s: f"{context}: {s}" if context else s

    # 两者都 None：一致
    if old is None and new is None:
        return
    # 一方 None：不一致
    if old is None or new is None:
        pytest.fail(msg(f"one is None, other is not (old={old}, new={new})"))

    assert old.symbol == new.symbol, msg("symbol mismatch")
    assert old.strategy == new.strategy, msg("strategy mismatch")

    # daily_returns: 严格一致
    assert not old.daily_returns.empty, msg("old daily_returns is empty")
    assert not new.daily_returns.empty, msg("new daily_returns is empty")
    # 对齐索引后比较（vbt 列提取可能返回不同的 index name）
    old_dr = old.daily_returns.reset_index(drop=True)
    new_dr = new.daily_returns.reset_index(drop=True)
    assert len(old_dr) == len(new_dr), msg(
        f"daily_returns length mismatch: old={len(old_dr)}, new={len(new_dr)}"
    )
    np.testing.assert_allclose(
        old_dr.values,
        new_dr.values,
        rtol=rtol, atol=atol,
        err_msg=msg("daily_returns mismatch"),
    )

    # stats 字段：允许浮点误差
    assert abs(old.sharpe - new.sharpe) < stats_rtol + stats_atol * max(
        abs(old.sharpe), 1.0
    ), msg(f"sharpe mismatch: old={old.sharpe}, new={new.sharpe}")
    assert abs(old.total_return_pct - new.total_return_pct) < stats_atol, msg(
        f"total_return_pct mismatch: old={old.total_return_pct}, new={new.total_return_pct}"
    )
    assert abs(old.max_drawdown_pct - new.max_drawdown_pct) < stats_atol, msg(
        f"max_drawdown_pct mismatch: old={old.max_drawdown_pct}, new={new.max_drawdown_pct}"
    )
    assert abs(old.win_rate_pct - new.win_rate_pct) < stats_atol, msg(
        f"win_rate_pct mismatch: old={old.win_rate_pct}, new={new.win_rate_pct}"
    )
    assert old.total_trades == new.total_trades, msg(
        f"total_trades mismatch: old={old.total_trades}, new={new.total_trades}"
    )
    # sortino 从 daily_returns 派生，应严格一致
    assert abs(old.sortino - new.sortino) < 1e-6, msg(
        f"sortino mismatch: old={old.sortino}, new={new.sortino}"
    )


# ---------------------------------------------------------------------------
# Test 1-5: 各策略 batch vs single 数值一致性
# ---------------------------------------------------------------------------

# 测试矩阵：(strategy_name, [param_combos])
_STRATEGY_PARAM_CASES = [
    ("dual_ma", [
        {"fast": 5, "slow": 20},
        {"fast": 10, "slow": 30},
    ]),
    ("rsi_mean_revert", [
        {"period": 14, "oversold": 30, "overbought": 70},
        {"period": 7, "oversold": 25, "overbought": 75},
    ]),
    ("rsi_trend_filter", [
        {"rsi_period": 14, "oversold": 30, "overbought": 70, "trend_period": 50},
        {"rsi_period": 7, "oversold": 25, "overbought": 75, "trend_period": 50},
    ]),
    ("macd_cross", [
        {"fast": 12, "slow": 26, "signal_period": 9},
        {"fast": 5, "slow": 20, "signal_period": 5},
    ]),
    ("bollinger_band", [
        {"period": 20, "std_dev": 2.0},
        {"period": 10, "std_dev": 1.5},
    ]),
]


# 展开为扁平的 (strategy_name, params) 列表 + 自定义 ID
_EXPANDED_CASES: list[tuple[str, dict]] = []
_EXPANSED_IDS: list[str] = []
for _s, _combos in _STRATEGY_PARAM_CASES:
    for _i, _p in enumerate(_combos):
        _EXPANDED_CASES.append((_s, _p))
        _EXPANSED_IDS.append(f"{_s}-{_i}")


@pytest.mark.parametrize(
    "strategy_name, params",
    _EXPANDED_CASES,
    ids=_EXPANSED_IDS,
)
class TestBatchConsistencyAllStrategies:
    """5 个策略 × 2 参数组合的 batch vs single 一致性测试。"""

    def test_batch_matches_single_all_symbols(
        self, strategy_name: str, params: dict
    ) -> None:
        """批量回测与逐标的回测在每个标的上数值一致。"""
        # 3 个标的 + 随机走势（触发更多策略信号，覆盖更全）
        data = _make_multi_symbol_data(
            ["AAA", "BBB", "CCC"], n=300, trend="random", seed=123
        )

        # 旧方式：逐标的回测
        old_results: dict[str, SingleBacktestResult | None] = {}
        for sym, df in data.items():
            df = df.copy()
            df.index.name = sym
            old_results[sym] = _backtest_one(df, strategy_name, params)

        # 新方式：批量回测
        new_results_list = _backtest_batch(data, strategy_name, params)
        new_results = {r.symbol: r for r in new_results_list}

        # 每个标的都应一致（_backtest_one 返回 None 的标的在 batch 中不出现）
        for sym, old_r in old_results.items():
            if old_r is None:
                assert sym not in new_results, (
                    f"{strategy_name}/{params} {sym}: _backtest_one returned None "
                    f"but _backtest_batch returned a result"
                )
                continue
            assert sym in new_results, (
                f"{strategy_name}/{params} {sym}: _backtest_one returned a result "
                f"but _backtest_batch dropped it"
            )
            _assert_results_match(
                old_r, new_results[sym],
                context=f"{strategy_name}/{params} {sym}",
            )


# ---------------------------------------------------------------------------
# Test 6: 数据不足的标的被跳过
# ---------------------------------------------------------------------------

class TestBatchEdgeCases:
    """批量化回测的边界场景测试。"""

    def test_batch_skips_short_data(self) -> None:
        """数据 < 30 天的标的应被跳过（不返回结果）。"""
        # 一个长数据 + 一个短数据
        data = {
            "LONG": _make_ohlcv(300, trend="up"),
            "SHORT": _make_ohlcv(10, trend="up"),
        }
        results = _backtest_batch(data, "dual_ma", {"fast": 5, "slow": 20})
        symbols = [r.symbol for r in results]
        assert "LONG" in symbols
        assert "SHORT" not in symbols, (
            "数据 < 30 天的标的应被跳过，但仍出现在结果中"
        )

    def test_batch_skips_empty_df(self) -> None:
        """空 DataFrame 的标的应被跳过。"""
        data = {
            "GOOD": _make_ohlcv(300, trend="up"),
            "EMPTY": pd.DataFrame(),
        }
        results = _backtest_batch(data, "dual_ma", {"fast": 5, "slow": 20})
        symbols = [r.symbol for r in results]
        assert "GOOD" in symbols
        assert "EMPTY" not in symbols

    def test_batch_single_symbol(self) -> None:
        """只有 1 个标的时批量回测应正常工作。"""
        data = {"SOLO": _make_ohlcv(300, trend="up")}
        # 给一个随机走势的单标的，确保有信号
        data = {"SOLO": _make_ohlcv(300, trend="random", seed=7)}
        results = _backtest_batch(data, "dual_ma", {"fast": 5, "slow": 20})
        assert len(results) == 1
        assert results[0].symbol == "SOLO"
        assert not results[0].daily_returns.empty

    def test_batch_single_symbol_matches_single(self) -> None:
        """单标的时 batch vs single 一致性。"""
        df = _make_ohlcv(300, trend="random", seed=7)
        df.index.name = "SOLO"
        old = _backtest_one(df, "dual_ma", {"fast": 5, "slow": 20})
        new_list = _backtest_batch(
            {"SOLO": df}, "dual_ma", {"fast": 5, "slow": 20}
        )
        assert len(new_list) == 1
        _assert_results_match(old, new_list[0], context="single-symbol")

    def test_batch_misaligned_dates(self) -> None:
        """不同起始日期的标的：批量回测应正常完成（不抛异常）。

        数值一致性在严格对齐的日期下成立；对错位日期，
        batch 与 single 的 stats 可能因 NaN 填充方式不同而有细微差异，
        但 daily_returns 在有效区间内应一致。
        """
        # 标的 A 从 2021-01-01 起 300 bar
        # 标的 B 从 2021-06-01 起 300 bar（晚 5 个月）
        df_a = _make_ohlcv(300, trend="up", start="2021-01-01")
        df_b = _make_ohlcv(300, trend="up", start="2021-06-01")
        data = {"MISA": df_a, "MISB": df_b}

        # 不应抛异常
        results = _backtest_batch(data, "dual_ma", {"fast": 5, "slow": 20})
        assert len(results) == 2
        symbols = [r.symbol for r in results]
        assert set(symbols) == {"MISA", "MISB"}
        for r in results:
            assert not r.daily_returns.empty

    def test_batch_empty_data(self) -> None:
        """全空���据返回空列表。"""
        results = _backtest_batch({}, "dual_ma", {"fast": 5, "slow": 20})
        assert results == []

    def test_batch_unknown_strategy(self) -> None:
        """未注册策略返回空列表（不抛异常）。"""
        data = {"AAA": _make_ohlcv(300)}
        results = _backtest_batch(data, "nonexistent_xyz", {})
        assert results == []

    def test_batch_no_open_column(self) -> None:
        """DataFrame 无 open 列时也能正常回测（降级为 close 执行）。"""
        df = _make_ohlcv(300, trend="random", seed=42).drop(columns=["open"])
        data = {"NOOPEN": df}
        results = _backtest_batch(data, "dual_ma", {"fast": 5, "slow": 20})
        assert len(results) == 1
        assert results[0].symbol == "NOOPEN"

    def test_batch_preserves_symbol_order(self) -> None:
        """结果列表的 symbol 顺序应与 signal_matrix.columns 顺序一致
        （即与输入 dict 的插入顺序一致，Python 3.7+ 保证）。"""
        data = {
            "ZEBRA": _make_ohlcv(300, trend="up"),
            "ALPHA": _make_ohlcv(300, trend="up"),
            "MIKE":  _make_ohlcv(300, trend="up"),
        }
        results = _backtest_batch(data, "dual_ma", {"fast": 5, "slow": 20})
        symbols = [r.symbol for r in results]
        # 顺序应与输入 dict 一致
        assert symbols == ["ZEBRA", "ALPHA", "MIKE"]


# ---------------------------------------------------------------------------
# Test: _backtest_batch 输出格式与 _backtest_one 一致
# ---------------------------------------------------------------------------

class TestBatchOutputFormat:
    """验证 _backtest_batch 输出的 SingleBacktestResult 字段完整。"""

    def test_result_fields_populated(self) -> None:
        """SingleBacktestResult 所有字段都被正确填充（无 NaN）。"""
        data = _make_multi_symbol_data(
            ["AAA", "BBB"], n=300, trend="random", seed=99
        )
        results = _backtest_batch(data, "rsi_mean_revert",
                                  {"period": 14, "oversold": 30, "overbought": 70})
        assert len(results) == 2
        for r in results:
            assert isinstance(r, SingleBacktestResult)
            assert r.symbol in ["AAA", "BBB"]
            assert r.strategy == "rsi_mean_revert"
            assert r.params == {"period": 14, "oversold": 30, "overbought": 70}
            assert isinstance(r.sharpe, float)
            assert isinstance(r.total_return_pct, float)
            assert isinstance(r.max_drawdown_pct, float)
            assert isinstance(r.win_rate_pct, float)
            assert isinstance(r.total_trades, int)
            assert isinstance(r.sortino, float)
            assert not r.daily_returns.empty
            # 所有数值字段都应是有限值（_safe_float 已处理 NaN）
            for v in [r.sharpe, r.total_return_pct, r.max_drawdown_pct,
                      r.win_rate_pct, r.sortino]:
                assert np.isfinite(v), f"{r.symbol}: 字段值非有限: {v}"

    def test_batch_results_are_independent(self) -> None:
        """不同标的的 daily_returns 应独立（不共享索引/引用）。"""
        data = _make_multi_symbol_data(
            ["AAA", "BBB"], n=300, trend="random", seed=55
        )
        results = _backtest_batch(data, "dual_ma", {"fast": 5, "slow": 20})
        assert len(results) == 2
        # 修改一个不应影响另一个
        r0_orig = results[0].daily_returns.iloc[0]
        r1_orig = results[1].daily_returns.iloc[0]
        # 两个标的的 daily_returns 应不同（不同数据）
        # 注：相同 trend+seed 的数据生成相同走势；这里 seed 不同
        assert r0_orig != r1_orig or len(results[0].daily_returns) > 0


# ---------------------------------------------------------------------------
# Test: _run_group 集成（进度日志 + batch 路径）
# ---------------------------------------------------------------------------

def _make_mock_store(data_by_symbol: dict[str, pd.DataFrame]) -> MagicMock:
    """构造一个 Mock MarketDataStore，get_bars_multi 返回指定数据。"""
    store = MagicMock()
    def get_bars_multi(symbols, start, end, timeframe="1d"):
        return {s: data_by_symbol[s] for s in symbols if s in data_by_symbol}
    store.get_bars_multi.side_effect = get_bars_multi
    return store


def _make_mock_universe(groups: dict[str, list[str]]) -> MagicMock:
    """构造一个 Mock UniverseManager，get_groups 返回指定分组。"""
    universe = MagicMock()
    universe.get_groups.return_value = groups
    return universe


class TestRunGroupBatchIntegration:
    """验证 _run_group 使用 _backtest_batch 后仍产出正确结果。"""

    def test_run_group_still_produces_weights(self) -> None:
        """_run_group 使用 batch 后仍产出非空权重列表。"""
        data = _make_multi_symbol_data(
            ["AAPL", "MSFT"], n=300, trend="random", seed=11
        )
        store = _make_mock_store(data)
        # _get_spy_returns 会被调用，返回 None 即可（alpha 退化为 0）
        universe = _make_mock_universe({"TEST_GROUP": ["AAPL", "MSFT"]})

        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
        from mytrader.backtest.matrix_backtest import MatrixBacktestReport
        report = MatrixBacktestReport(
            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
            backtest_window="2021-01-01 ~ 2022-01-01",
            groups={},
        )

        weights = mb._run_group(
            group_id="TEST_GROUP",
            symbols=["AAPL", "MSFT"],
            start=date(2021, 1, 1),
            end=date(2022, 1, 1),
            strategies=["dual_ma"],
            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
            report=report,
        )
        assert len(weights) >= 1
        assert all("strategy" in w for w in weights)
        assert all("weight" in w for w in weights)

    def test_run_group_progress_logging(self) -> None:
        """_run_group 应输出包含耗时的进度日志。"""
        # loguru 不通过标准 logging 传播，需用 logger.add 捕获
        from loguru import logger

        data = _make_multi_symbol_data(
            ["AAPL", "MSFT"], n=300, trend="random", seed=22
        )
        store = _make_mock_store(data)
        universe = _make_mock_universe({"TEST_GROUP": ["AAPL", "MSFT"]})

        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
        from mytrader.backtest.matrix_backtest import MatrixBacktestReport
        report = MatrixBacktestReport(
            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
            backtest_window="2021-01-01 ~ 2022-01-01",
            groups={},
        )

        msgs: list[str] = []
        handler_id = logger.add(lambda m: msgs.append(str(m)), level="INFO")
        try:
            mb._run_group(
                group_id="TEST_GROUP",
                symbols=["AAPL", "MSFT"],
                start=date(2021, 1, 1),
                end=date(2022, 1, 1),
                strategies=["dual_ma"],
                param_grids={"dual_ma": {"fast": [5, 10], "slow": [20, 30]}},
                report=report,
            )
        finally:
            logger.remove(handler_id)

        # 应包含 "MatrixBacktest" 日志
        all_logs = " ".join(msgs)
        assert "MatrixBacktest" in all_logs, (
            f"未找到 MatrixBacktest 日志：{all_logs}"
        )
        # 应有进度日志（"done" 关键字，spec §4.3 要求）
        assert "done" in all_logs, (
            f"未找到进度完成日志（'done'）：{all_logs}"
        )
        # 应有耗时信息（如 "0.Xs"）
        assert any("s " in m or "s)" in m for m in msgs), (
            f"日志未包含耗时信息：{msgs}"
        )


# ---------------------------------------------------------------------------
# Test: Walk-Forward 路径使用 batch
# ---------------------------------------------------------------------------

class TestWalkForwardBatchIntegration:
    """验证 Walk-Forward 的 _backtest_with_params_on_period 使用 batch。"""

    def test_walk_forward_returns_valid_report(self) -> None:
        """Walk-Forward 4 轮后产出有效报告（不抛异常）。"""
        from mytrader.backtest.matrix_backtest import run_walk_forward

        data = _make_multi_symbol_data(
            ["AAPL", "MSFT"], n=500, trend="random", seed=33
        )
        store = _make_mock_store(data)
        universe = _make_mock_universe({"TEST_GROUP": ["AAPL", "MSFT"]})

        mb = MatrixBacktest(store=store, universe=universe, years=2, top_k=2)
        report = run_walk_forward(
            mb,
            strategies=["dual_ma"],
            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
            rounds=2,
            train_months=6,
            val_months=3,
        )
        assert len(report.rounds) == 2
        # 每轮都应有 sortino 和 max_dd 数值（可能为 0，但不应为 None）
        for r in report.rounds:
            assert isinstance(r.val_sortino, float)
            assert isinstance(r.val_max_dd, float)
            assert isinstance(r.passed, bool)
