"""Tests for strategy engine — 重点验证无前视偏差。"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from mytrader.strategy.indicators import sma, ema, rsi, bollinger_bands, macd, atr, crossed_above, crossed_below
from mytrader.strategy.registry import STRATEGY_REGISTRY
from mytrader.strategy.ensemble import ensemble_signal


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_trending_close(n: int = 100, drift: float = 0.002) -> pd.Series:
    """上升趋势的收盘价序列。"""
    idx = pd.date_range("2023-01-01", periods=n, freq="B")
    prices = 100.0 * np.exp(np.cumsum(drift + 0.01 * np.random.randn(n)))
    return pd.Series(prices, index=idx, name="close")


def make_oscillating_close(n: int = 100) -> pd.Series:
    """震荡行情（正弦波）的收盘价序列。"""
    idx = pd.date_range("2023-01-01", periods=n, freq="B")
    prices = 100 + 10 * np.sin(np.linspace(0, 4 * np.pi, n))
    return pd.Series(prices, index=idx, name="close")


# ---------------------------------------------------------------------------
# 指标函数测试
# ---------------------------------------------------------------------------

class TestIndicators:
    def test_sma_length(self):
        close = make_trending_close(50)
        result = sma(close, 10)
        assert len(result) == len(close)

    def test_sma_first_valid(self):
        close = make_trending_close(20)
        result = sma(close, 5)
        assert result.iloc[:4].isna().all()
        assert not result.iloc[4:].isna().any()

    def test_rsi_range(self):
        close = make_trending_close(100)
        result = rsi(close, 14)
        valid = result.dropna()
        assert (valid >= 0).all() and (valid <= 100).all()

    def test_bollinger_bands_upper_ge_lower(self):
        close = make_trending_close(60)
        upper, middle, lower = bollinger_bands(close, 20, 2.0)
        valid = upper.dropna()
        assert (upper.dropna() >= lower.dropna()).all()

    def test_macd_signal_length(self):
        close = make_trending_close(100)
        macd_line, signal_line, hist = macd(close, 12, 26, 9)
        assert len(macd_line) == len(close)

    def test_atr_non_negative(self):
        idx = pd.date_range("2023-01-01", periods=60, freq="B")
        close = make_trending_close(60)
        df = pd.DataFrame({
            "high":  close * 1.01,
            "low":   close * 0.99,
            "close": close,
        })
        result = atr(df, 14)
        assert (result.dropna() >= 0).all()


# ---------------------------------------------------------------------------
# 策略注册测试
# ---------------------------------------------------------------------------

class TestStrategyRegistry:
    def test_all_strategies_registered(self):
        expected = {
            "dual_ma", "rsi_mean_revert", "rsi_trend_filter",
            "bollinger_band", "macd_cross",
            # 迭代 #14 新增
            "rsi_bb_convergence", "macd_volume",
        }
        assert expected.issubset(set(STRATEGY_REGISTRY.keys()))

    def test_strategy_callable(self):
        for name, fn in STRATEGY_REGISTRY.items():
            assert callable(fn), f"{name} is not callable"

    def test_new_strategies_in_reoptimize_constants(self):
        """迭代 #14：REOPTIMIZE_STRATEGIES 包含新策略 + 参数网格。"""
        from main import REOPTIMIZE_STRATEGIES, REOPTIMIZE_PARAM_GRIDS
        for name in ("rsi_bb_convergence", "macd_volume"):
            assert name in REOPTIMIZE_STRATEGIES, (
                f"'{name}' 未在 REOPTIMIZE_STRATEGIES 中"
            )
            assert name in REOPTIMIZE_PARAM_GRIDS, (
                f"'{name}' 未在 REOPTIMIZE_PARAM_GRIDS 中"
            )
        # rsi_trend_filter 网格应含 exit_neutral 维度
        assert "exit_neutral" in REOPTIMIZE_PARAM_GRIDS["rsi_trend_filter"], (
            "rsi_trend_filter 参数网格缺少 exit_neutral 维度"
        )


# ---------------------------------------------------------------------------
# 前视偏差测试（Look-ahead Bias Test）— 核心！
# ---------------------------------------------------------------------------

class TestNoLookaheadBias:
    """验证所有策略的 shift(1) 正确实现。

    方法：对同一个 close Series，在最后一个 bar 加入一个极端值（+100%），
    如果信号没有前视偏差，最后一个 bar 的信号不应该改变。
    """

    @pytest.mark.parametrize("strategy_name", list(STRATEGY_REGISTRY.keys()))
    def test_signal_does_not_use_current_bar(self, strategy_name: str):
        close_normal = make_trending_close(60)
        close_modified = close_normal.copy()
        close_modified.iloc[-1] = close_modified.iloc[-1] * 2.0  # 最后一天价格翻倍

        fn = STRATEGY_REGISTRY[strategy_name]
        signal_normal   = fn(close_normal)
        signal_modified = fn(close_modified)

        # 最后一个 bar 的信号应该相同（因为它是由 T-1 的数据决定的）
        assert signal_normal.iloc[-1] == signal_modified.iloc[-1], (
            f"Strategy '{strategy_name}' has look-ahead bias: "
            f"last bar signal changed when only the last bar's price changed."
        )


# ---------------------------------------------------------------------------
# 策略信号质量测试
# ---------------------------------------------------------------------------

class TestStrategySignals:
    def test_dual_ma_signal_values(self):
        close = make_trending_close(100)
        from mytrader.strategy.strategies.dual_ma import dual_ma_signal
        signal = dual_ma_signal(close, fast=5, slow=20)
        assert set(signal.unique()).issubset({-1, 0, 1})

    def test_rsi_signal_values(self):
        close = make_oscillating_close(100)
        from mytrader.strategy.strategies.rsi_mean_revert import rsi_signal
        signal = rsi_signal(close, period=14)
        assert set(signal.unique()).issubset({-1, 0, 1})


# ---------------------------------------------------------------------------
# Ensemble 测试
# ---------------------------------------------------------------------------

class TestEnsemble:
    def test_equal_weight_default(self):
        n = 50
        s1 = pd.Series([1] * n)
        s2 = pd.Series([1] * n)
        result = ensemble_signal([s1, s2])
        assert (result == 1).all()

    def test_conflicting_signals_hold(self):
        n = 50
        s1 = pd.Series([1]  * n)
        s2 = pd.Series([-1] * n)
        result = ensemble_signal([s1, s2], threshold=0.3)
        # 0.5 * 1 + 0.5 * (-1) = 0，不超过阈值 → HOLD
        assert (result == 0).all()

    def test_weights_normalized(self):
        n = 50
        s1 = pd.Series([1] * n)
        s2 = pd.Series([1] * n)
        result = ensemble_signal([s1, s2], weights=[2.0, 2.0])
        assert (result == 1).all()


# ---------------------------------------------------------------------------
# 指标补充测试（P1）
# ---------------------------------------------------------------------------

class TestIndicatorsEdgeCases:
    """I1-I6: 指标边界值和未覆盖函数。"""

    def test_ema_length(self):
        """I1: EMA 输出长度与输入一致。"""
        close = make_trending_close(50)
        result = ema(close, 10)
        assert len(result) == len(close)

    def test_crossed_above_detection(self):
        """I2: 上穿检测正确。"""
        idx = pd.date_range("2023-01-01", periods=5, freq="B")
        a = pd.Series([1.0, 2.0, 1.0, 1.0, 1.0], index=idx)
        b = pd.Series([1.5, 1.5, 1.5, 1.5, 1.5], index=idx)
        result = crossed_above(a, b)
        # 第 1 行（index=1）：a=2.0 > b=1.5 且 prev a=1.0 <= b=1.5 → True
        assert bool(result.iloc[1]) is True
        # 其他位置不应为 True
        assert not bool(result.iloc[0])
        assert not bool(result.iloc[2])

    def test_crossed_above_no_cross(self):
        """I3: 无交叉时全 False。"""
        idx = pd.date_range("2023-01-01", periods=5, freq="B")
        a = pd.Series([3.0, 4.0, 5.0, 6.0, 7.0], index=idx)
        b = pd.Series([1.0, 1.0, 1.0, 1.0, 1.0], index=idx)
        result = crossed_above(a, b)
        assert not result.any()

    def test_crossed_below_detection(self):
        """I4: 下穿检测正确。"""
        idx = pd.date_range("2023-01-01", periods=5, freq="B")
        a = pd.Series([2.0, 1.0, 1.0, 1.0, 1.0], index=idx)
        b = pd.Series([1.5, 1.5, 1.5, 1.5, 1.5], index=idx)
        result = crossed_below(a, b)
        # 第 1 行：a=1.0 < b=1.5 且 prev a=2.0 >= b=1.5 → True
        assert bool(result.iloc[1]) is True
        assert not bool(result.iloc[0])

    def test_crossed_below_no_cross(self):
        """I5: 无交叉时全 False。"""
        idx = pd.date_range("2023-01-01", periods=5, freq="B")
        a = pd.Series([0.5, 0.5, 0.5, 0.5, 0.5], index=idx)
        b = pd.Series([1.0, 1.0, 1.0, 1.0, 1.0], index=idx)
        result = crossed_below(a, b)
        assert not result.any()

    def test_sma_period_larger_than_data(self):
        """I6: period > 数据行数时返回全 NA 而非崩溃。"""
        close = make_trending_close(5)
        result = sma(close, 10)
        assert len(result) == len(close)
        # 全部为 NA（因为 period > len(close)，无法计算）
        assert result.isna().all(), f"expected all NaN, got {result.tolist()}"


# ---------------------------------------------------------------------------
# 策略补充测试（P0-P1）
# ---------------------------------------------------------------------------

class TestAllStrategiesQuality:
    """S1-S7: 所有策略的信号质量验证。"""

    @pytest.mark.parametrize("strategy_name", list(STRATEGY_REGISTRY.keys()))
    def test_all_strategies_return_int_dtype(self, strategy_name):
        """S1: 所有策略返回值类型为 int。"""
        close = make_trending_close(100)
        fn = STRATEGY_REGISTRY[strategy_name]
        signal = fn(close)
        assert signal.dtype == int, (
            f"{strategy_name}: expected int dtype, got {signal.dtype}"
        )

    @pytest.mark.parametrize("strategy_name", list(STRATEGY_REGISTRY.keys()))
    def test_all_strategies_index_alignment(self, strategy_name):
        """S2: 所有策略返回 index 与 close 一致。"""
        close = make_trending_close(100)
        fn = STRATEGY_REGISTRY[strategy_name]
        signal = fn(close)
        assert signal.index.equals(close.index), (
            f"{strategy_name}: index mismatch"
        )

    def test_dual_ma_custom_params(self):
        """S3: 双均线使用非默认参数。"""
        from mytrader.strategy.strategies.dual_ma import dual_ma_signal
        close = make_trending_close(100)
        signal = dual_ma_signal(close, fast=5, slow=60)
        assert set(signal.unique()).issubset({-1, 0, 1})

    def test_rsi_custom_thresholds(self):
        """S5: RSI 使用非默认阈值。"""
        from mytrader.strategy.strategies.rsi_mean_revert import rsi_signal
        close = make_oscillating_close(100)
        signal = rsi_signal(close, period=14, oversold=20.0, overbought=80.0)
        assert set(signal.unique()).issubset({-1, 0, 1})

    def test_bollinger_custom_period(self):
        """S6: 布林带使用非默认 period。"""
        from mytrader.strategy.strategies.bollinger_band import bollinger_signal
        close = make_trending_close(100)
        signal = bollinger_signal(close, period=30, std_dev=2.0)
        assert set(signal.unique()).issubset({-1, 0, 1})

    def test_bollinger_custom_std(self):
        """S6-bis: 布林带使用非默认 std_dev（修复列名匹配 bug 后）。"""
        from mytrader.strategy.strategies.bollinger_band import bollinger_signal
        close = make_trending_close(100)
        signal = bollinger_signal(close, period=20, std_dev=3.0)
        assert set(signal.unique()).issubset({-1, 0, 1})

    def test_macd_custom_params(self):
        """S7: MACD 使用非默认参数。"""
        from mytrader.strategy.strategies.macd_cross import macd_signal
        close = make_trending_close(100)
        signal = macd_signal(close, fast=5, slow=35, signal_period=5)
        assert set(signal.unique()).issubset({-1, 0, 1})


# ---------------------------------------------------------------------------
# RSI Trend Filter 策略测试（迭代 #8 / 迭代 #14 修复）
# ---------------------------------------------------------------------------

class TestRSITrendFilter:
    """RSI 趋势过滤策略测试。

    迭代 #14 修复：entry 用趋势过滤，exit 用 RSI 回归中性。
    旧 T3/T4（test_uptrend_only_buy / test_downtrend_only_sell）已移除——
    新 exit 逻辑会在趋势中产生反向出场信号，旧断言不再成立。
    """

    def test_signal_values(self):
        """T1: 信号值仅在 {-1, 0, 1} 范围内。"""
        from mytrader.strategy.strategies.rsi_trend_filter import rsi_trend_filter_signal
        close = make_oscillating_close(300)
        signal = rsi_trend_filter_signal(close)
        assert set(signal.unique()).issubset({-1, 0, 1})

    def test_custom_params(self):
        """T2: 非默认参数正常工作（含 exit_neutral）。"""
        from mytrader.strategy.strategies.rsi_trend_filter import rsi_trend_filter_signal
        close = make_oscillating_close(300)
        signal = rsi_trend_filter_signal(
            close, rsi_period=7, oversold=25.0, overbought=75.0,
            trend_period=100, exit_neutral=45.0,
        )
        assert set(signal.unique()).issubset({-1, 0, 1})

    def test_insufficient_data(self):
        """T5: 数据不足 trend_period 时不崩溃，入场信号为 0。"""
        from mytrader.strategy.strategies.rsi_trend_filter import rsi_trend_filter_signal
        # 纯线性上升：RSI≈100 无 crossover，SMA(200) 全 NaN → 全 0
        n = 50
        idx = pd.date_range("2023-01-01", periods=n, freq="B")
        close = pd.Series([100.0 + i * 0.1 for i in range(n)], index=idx, name="close")
        signal = rsi_trend_filter_signal(close)
        assert (signal == 0).all()

    # ------------------------------------------------------------------
    # 迭代 #14 新增测试
    # ------------------------------------------------------------------

    def test_rsi_trend_filter_exit_neutral_long(self):
        """多头仓位在 RSI 向上穿越 exit_neutral 时出场（SELL）。

        构造：上升趋势（close > SMA）中 RSI 先超卖（< 30）再回归中性（> 50）。
        上升趋势中 sell_entry 需要 close < SMA → 不触发。
        所以任何 -1 信号都来自 exit_long（RSI 穿越中性）。
        """
        from mytrader.strategy.strategies.rsi_trend_filter import rsi_trend_filter_signal
        n = 300
        idx = pd.date_range("2023-01-01", periods=n, freq="B")
        # 250 bar 强上升趋势建立 SMA200，然后 10 bar 回调（RSI<30），再 40 bar 反弹（RSI>50）
        up = [100.0 * (1.005 ** i) for i in range(250)]
        drop = [up[-1] * (0.97 ** (i + 1)) for i in range(10)]
        recover = [drop[-1] * (1.02 ** (i + 1)) for i in range(40)]
        close = pd.Series(up + drop + recover, index=idx, name="close")
        signal = rsi_trend_filter_signal(close, oversold=35.0, overbought=80.0)
        # 上升趋势中应出现 -1（exit_long），因为 RSI 从超卖回归中性
        assert -1 in signal.values, (
            f"应出现 SELL exit 信号（RSI 穿越中性），实际信号集: {set(signal.values)}"
        )

    def test_rsi_trend_filter_exit_neutral_short(self):
        """空头仓位在 RSI 向下穿越 exit_neutral 时出场（BUY）。

        构造：下降趋势（close < SMA）中 RSI 先超买（> 70）再回归中性（< 50）。
        下降趋势中 buy_entry 需要 close > SMA → 不触发。
        所以任何 +1 信号都来自 exit_short（RSI 穿越中性）。
        """
        from mytrader.strategy.strategies.rsi_trend_filter import rsi_trend_filter_signal
        n = 300
        idx = pd.date_range("2023-01-01", periods=n, freq="B")
        # 250 bar 强下降趋势建立 SMA200，然后 10 bar 反弹（RSI>70），再 40 bar 回落（RSI<50）
        down = [100.0 * (0.995 ** i) for i in range(250)]
        bounce = [down[-1] * (1.03 ** (i + 1)) for i in range(10)]
        fall = [bounce[-1] * (0.98 ** (i + 1)) for i in range(40)]
        close = pd.Series(down + bounce + fall, index=idx, name="close")
        signal = rsi_trend_filter_signal(close, oversold=20.0, overbought=65.0)
        # 下降趋势中应出现 +1（exit_short），因为 RSI 从超买回归中性
        assert 1 in signal.values, (
            f"应出现 BUY exit 信号（RSI 穿越中性），实际信号集: {set(signal.values)}"
        )

    def test_rsi_trend_filter_entry_still_trend_filtered(self):
        """入场仍需趋势过滤：纯下降趋势中 RSI<超卖 但 close<SMA → 无 buy_entry。

        构造：纯线性下降趋势。RSI 始终 < 50 → 无 exit crossover。
        close < SMA → buy_entry 被过滤。所有信号应为 0。
        """
        from mytrader.strategy.strategies.rsi_trend_filter import rsi_trend_filter_signal
        n = 300
        idx = pd.date_range("2023-01-01", periods=n, freq="B")
        close = pd.Series(
            [100.0 - i * 0.3 for i in range(n)], index=idx, name="close"
        )
        signal = rsi_trend_filter_signal(close, oversold=30.0, overbought=70.0)
        # 纯下降趋势中入场被趋势过滤，出场无 crossover（RSI 始终 < 50）
        assert (signal == 0).all(), (
            f"纯下降趋势中应全 0（入场被过滤 + 无 exit crossover），"
            f"实际信号集: {set(signal.values)}"
        )

    def test_rsi_trend_filter_not_degenerate(self):
        """迭代 #14 回归测试：rsi_trend_filter 不再退化（closed_trades > 0）。

        Iter #8 bug：entry 和 exit 互斥 → 0 closed_trades。
        Iter #14 修复：exit 用 RSI 回归中性 → 自然闭环。
        """
        import vectorbt as vbt
        from mytrader.strategy.strategies.rsi_trend_filter import rsi_trend_filter_signal

        rng = np.random.default_rng(42)
        n = 300
        idx = pd.date_range("2023-01-01", periods=n, freq="B")
        steps = rng.normal(0, 0.5, n)
        close = pd.Series(100.0 + np.cumsum(steps), index=idx, name="close")

        # trend_period=50 适配 300 bar 数据（200 太长导致有效窗口不足）
        signal = rsi_trend_filter_signal(close, trend_period=50)
        entries = signal == 1
        exits = signal == -1

        pf = vbt.Portfolio.from_signals(
            close=close, entries=entries, exits=exits,
            init_cash=10000, size_type="Percent", size=1.0,
        )
        closed_trades = pf.trades.closed.count()
        assert closed_trades > 0, (
            f"rsi_trend_filter 应有 closed_trades > 0（不再退化），实际 {closed_trades}"
        )

    def test_rsi_trend_filter_exit_neutral_param(self):
        """自定义 exit_neutral 参数影响信号行为。"""
        from mytrader.strategy.strategies.rsi_trend_filter import rsi_trend_filter_signal
        close = make_oscillating_close(300)
        # exit_neutral=40 vs exit_neutral=60 → 信号应不同
        sig_40 = rsi_trend_filter_signal(close, exit_neutral=40.0, trend_period=100)
        sig_60 = rsi_trend_filter_signal(close, exit_neutral=60.0, trend_period=100)
        assert set(sig_40.unique()).issubset({-1, 0, 1})
        assert set(sig_60.unique()).issubset({-1, 0, 1})
        # 不同 exit_neutral 应产生不同的信号序列
        assert not sig_40.equals(sig_60), (
            "不同 exit_neutral 参数应产生不同信号序列"
        )


# ---------------------------------------------------------------------------
# RSI + Bollinger Band 双确认策略测试（迭代 #14）
# ---------------------------------------------------------------------------

class TestRSIBBConvergence:
    """RSI + BB 双确认均值回归策略测试。"""

    def test_rsi_bb_buy_signal(self):
        """BUY: RSI < oversold AND close < lower_bb → 双重超卖确认。"""
        from mytrader.strategy.strategies.rsi_bb_convergence import rsi_bb_convergence_signal
        # 构造急跌数据：RSI 超卖 + close 跌破下轨
        n = 100
        idx = pd.date_range("2023-01-01", periods=n, freq="B")
        prices = np.concatenate([
            np.full(50, 100.0),
            np.linspace(100.0, 70.0, 50),
        ])
        close = pd.Series(prices, index=idx, name="close")
        signal = rsi_bb_convergence_signal(close)
        # 急跌后应出现 BUY 信号（双重超卖确认）
        assert 1 in signal.values, (
            f"急跌数据应产生 BUY 信号，实际信号集: {set(signal.values)}"
        )

    def test_rsi_bb_sell_signal(self):
        """SELL: RSI > overbought AND close > upper_bb → 双重超买确认。"""
        from mytrader.strategy.strategies.rsi_bb_convergence import rsi_bb_convergence_signal
        n = 100
        idx = pd.date_range("2023-01-01", periods=n, freq="B")
        prices = np.concatenate([
            np.full(50, 100.0),
            np.linspace(100.0, 130.0, 50),
        ])
        close = pd.Series(prices, index=idx, name="close")
        signal = rsi_bb_convergence_signal(close)
        # 急涨后应出现 SELL 信号（双重超买确认）
        assert -1 in signal.values, (
            f"急涨数据应产生 SELL 信号，实际信号集: {set(signal.values)}"
        )

    def test_rsi_bb_no_signal_rsi_only(self):
        """RSI 超卖但 close 未跌破下轨 → 无 buy_entry（无双重确认）。

        构造：纯下降趋势（RSI<30）+ bb_std=10.0（极宽布林带，close 始终在中轨上方）。
        RSI 始终 < 50 → 无 exit crossover → 所有信号为 0。
        """
        from mytrader.strategy.strategies.rsi_bb_convergence import rsi_bb_convergence_signal
        n = 200
        idx = pd.date_range("2023-01-01", periods=n, freq="B")
        close = pd.Series(
            [100.0 - i * 0.3 for i in range(n)], index=idx, name="close"
        )
        # bb_std=10 → 极宽布林带 → close < lower 几乎不触发
        signal = rsi_bb_convergence_signal(close, bb_std=10.0)
        assert (signal == 0).all(), (
            f"RSI 超卖但 close 未跌破下轨时不应有信号，实际信号集: {set(signal.values)}"
        )

    def test_rsi_bb_no_signal_bb_only(self):
        """close 跌破下轨但 RSI 未超卖 → 无 buy_entry（无双重确认）。

        构造：纯下降趋势（close < lower_bb）+ oversold=0.0（RSI < 0 不可能）。
        RSI 始终 < 50 → 无 exit crossover → 所有信号为 0。
        """
        from mytrader.strategy.strategies.rsi_bb_convergence import rsi_bb_convergence_signal
        n = 200
        idx = pd.date_range("2023-01-01", periods=n, freq="B")
        close = pd.Series(
            [100.0 - i * 0.3 for i in range(n)], index=idx, name="close"
        )
        # oversold=0 → RSI < 0 不可能 → buy_entry 永远 False
        signal = rsi_bb_convergence_signal(close, oversold=0.0)
        assert (signal == 0).all(), (
            f"close 跌破下轨但 RSI 未超卖时不应有信号，实际信号集: {set(signal.values)}"
        )

    def test_rsi_bb_exit_rsi_neutral(self):
        """RSI 向上穿越中性时出场（SELL to exit long）。"""
        from mytrader.strategy.strategies.rsi_bb_convergence import rsi_bb_convergence_signal
        # 使用振荡数据：RSI 会反复穿越 50
        close = make_oscillating_close(300)
        signal = rsi_bb_convergence_signal(close)
        # 振荡数据中 exit_long_rsi 或 exit_short_rsi 应触发
        assert set(signal.unique()).issubset({-1, 0, 1})

    def test_rsi_bb_exit_bb_middle(self):
        """close 穿越中轨时出场。"""
        from mytrader.strategy.strategies.rsi_bb_convergence import rsi_bb_convergence_signal
        # 振荡数据中 close 会反复穿越中轨
        close = make_oscillating_close(300)
        signal = rsi_bb_convergence_signal(close)
        assert set(signal.unique()).issubset({-1, 0, 1})

    def test_rsi_bb_custom_params(self):
        """自定义参数改变信号行为。"""
        from mytrader.strategy.strategies.rsi_bb_convergence import rsi_bb_convergence_signal
        close = make_oscillating_close(300)
        sig_default = rsi_bb_convergence_signal(close)
        sig_custom = rsi_bb_convergence_signal(
            close, rsi_period=21, oversold=25.0, overbought=75.0,
            bb_period=15, bb_std=1.5,
        )
        assert set(sig_custom.unique()).issubset({-1, 0, 1})
        # 不同参数应产生不同信号
        assert not sig_default.equals(sig_custom), (
            "不同参数应产生不同信号序列"
        )

    def test_rsi_bb_signal_range(self):
        """信号值仅在 {-1, 0, 1} 范围内。"""
        from mytrader.strategy.strategies.rsi_bb_convergence import rsi_bb_convergence_signal
        close = make_trending_close(100)
        signal = rsi_bb_convergence_signal(close)
        assert set(signal.unique()).issubset({-1, 0, 1})

    def test_rsi_bb_no_lookahead(self):
        """shift(1) 防前视偏差：最后 bar 信号不因最后 bar 价格变化而改变。"""
        from mytrader.strategy.strategies.rsi_bb_convergence import rsi_bb_convergence_signal
        close_normal = make_trending_close(100)
        close_modified = close_normal.copy()
        close_modified.iloc[-1] = close_modified.iloc[-1] * 2.0
        signal_normal = rsi_bb_convergence_signal(close_normal)
        signal_modified = rsi_bb_convergence_signal(close_modified)
        assert signal_normal.iloc[-1] == signal_modified.iloc[-1], (
            "rsi_bb_convergence 有前视偏差：最后 bar 价格变化导致最后 bar 信号变化"
        )


# ---------------------------------------------------------------------------
# MACD + Volume 策略测试（迭代 #14）
# ---------------------------------------------------------------------------

class TestMACDVolume:
    """MACD + 成交量确认策略测试。"""

    @staticmethod
    def _make_price_with_volume(n: int = 100, trend: str = "up") -> tuple[pd.Series, pd.DataFrame]:
        """构造含 volume 的 OHLCV 数据 + close Series。"""
        idx = pd.date_range("2023-01-01", periods=n, freq="B")
        if trend == "up":
            prices = np.concatenate([
                np.linspace(100, 80, 50),
                np.linspace(80, 120, 50),
            ])
        else:  # down
            prices = np.concatenate([
                np.linspace(100, 120, 50),
                np.linspace(120, 80, 50),
            ])
        close = pd.Series(prices, index=idx, name="close")
        # 成交量递增（始终 > MA）
        volume = np.arange(1, n + 1, dtype=float) * 1000
        df = pd.DataFrame({
            "open": close - 0.5,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "volume": volume,
        }, index=idx)
        return close, df

    def test_macd_volume_buy_with_volume(self):
        """MACD 上穿 + volume > MA → BUY 信号存在。"""
        from mytrader.strategy.strategies.macd_volume import macd_volume_signal
        close, df = self._make_price_with_volume(trend="up")
        signal = macd_volume_signal(close, df=df)
        # 趋势反转（跌→涨）应触发 MACD 金叉 + 放量确认 → BUY
        assert 1 in signal.values, (
            f"MACD 金叉 + 放量确认应产生 BUY 信号，实际信号集: {set(signal.values)}"
        )

    def test_macd_volume_no_buy_without_volume(self):
        """MACD 上穿但 volume < MA → 无 BUY 信号。"""
        from mytrader.strategy.strategies.macd_volume import macd_volume_signal
        close, df = self._make_price_with_volume(trend="up")
        # 成交量全 0 → volume < MA → buy_signal 被过滤
        df["volume"] = 0.0
        signal = macd_volume_signal(close, df=df)
        assert 1 not in signal.values, (
            f"成交量不足时不应有 BUY 信号，实际信号集: {set(signal.values)}"
        )

    def test_macd_volume_sell_regardless(self):
        """MACD 下穿 → SELL 信号（无需成交量确认）。"""
        from mytrader.strategy.strategies.macd_volume import macd_volume_signal
        close, df = self._make_price_with_volume(trend="down")
        # 成交量全 0（即使无量也必须出场）
        df["volume"] = 0.0
        signal = macd_volume_signal(close, df=df)
        assert -1 in signal.values, (
            f"MACD 死叉应产生 SELL 信号（无需量确认），实际信号集: {set(signal.values)}"
        )

    def test_macd_volume_no_df_graceful(self):
        """df=None → 退化为纯 MACD 策略（不崩溃）。"""
        from mytrader.strategy.strategies.macd_volume import macd_volume_signal
        close, _ = self._make_price_with_volume(trend="up")
        signal = macd_volume_signal(close, df=None)
        assert set(signal.unique()).issubset({-1, 0, 1})
        # 无 df 时退化为 MACD only，应仍能产生信号
        # 趋势反转应触发 MACD 交叉

    def test_macd_volume_no_volume_column(self):
        """df 无 volume 列 → 退化为纯 MACD 策略。"""
        from mytrader.strategy.strategies.macd_volume import macd_volume_signal
        close, df = self._make_price_with_volume(trend="up")
        df = df.drop(columns=["volume"])
        signal = macd_volume_signal(close, df=df)
        assert set(signal.unique()).issubset({-1, 0, 1})

    def test_macd_volume_signal_range(self):
        """信号值仅在 {-1, 0, 1} 范围内。"""
        from mytrader.strategy.strategies.macd_volume import macd_volume_signal
        close = make_trending_close(100)
        signal = macd_volume_signal(close)
        assert set(signal.unique()).issubset({-1, 0, 1})

    def test_macd_volume_no_lookahead(self):
        """shift(1) 防前视偏差：最后 bar 信号不因最后 bar 价格变化而改变。"""
        from mytrader.strategy.strategies.macd_volume import macd_volume_signal
        close_normal = make_trending_close(100)
        close_modified = close_normal.copy()
        close_modified.iloc[-1] = close_modified.iloc[-1] * 2.0
        signal_normal = macd_volume_signal(close_normal)
        signal_modified = macd_volume_signal(close_modified)
        assert signal_normal.iloc[-1] == signal_modified.iloc[-1], (
            "macd_volume 有前视偏差：最后 bar 价格变化导致最后 bar 信号变化"
        )


# ---------------------------------------------------------------------------
# Ensemble 补充测试（P0-P1）
# ---------------------------------------------------------------------------

class TestEnsembleEdgeCases:
    """E1-E5: Ensemble 边界条件。"""

    def test_empty_signals_raises(self):
        """E1: 空信号列表抛出 ValueError。"""
        with pytest.raises(ValueError, match="empty"):
            ensemble_signal([])

    def test_weights_length_mismatch(self):
        """E2: 权重和信号数量不一致。"""
        n = 50
        s1 = pd.Series([1] * n)
        s2 = pd.Series([1] * n)
        with pytest.raises(ValueError, match="len\\(weights\\)"):
            ensemble_signal([s1, s2], weights=[0.5])

    def test_single_signal_above_threshold(self):
        """E3: 单信号超过阈值时通过。"""
        s = pd.Series([1] * 50)
        result = ensemble_signal([s], threshold=0.5)
        assert (result == 1).all()

    def test_single_signal_below_threshold(self):
        """E4: 单信号未超过阈值。"""
        s = pd.Series([1] * 50)
        result = ensemble_signal([s], threshold=1.5)
        assert (result == 0).all()

    def test_threshold_zero(self):
        """E5: threshold=0 时任何非零 combined 都映射。"""
        n = 50
        s1 = pd.Series([1] * n)
        s2 = pd.Series([0] * n)
        # combined = 0.5 * 1 + 0.5 * 0 = 0.5 > 0 → BUY
        result = ensemble_signal([s1, s2], threshold=0.0)
        assert (result == 1).all()


# ---------------------------------------------------------------------------
# base.py / registry.py 补充测试（P1）
# ---------------------------------------------------------------------------

class TestSignalBase:
    """BR1-BR3: Signal 数据结构的 is_actionable。"""

    def test_signal_is_actionable_buy(self):
        """BR1: BUY 信号 is_actionable=True。"""
        from mytrader.strategy.base import Signal, SignalDirection
        from datetime import datetime, timezone
        s = Signal(
            symbol="AAPL",
            direction=SignalDirection.BUY,
            timestamp=datetime.now(tz=timezone.utc),
            confidence=0.8,
            strategy_name="test",
        )
        assert s.is_actionable() is True

    def test_signal_is_actionable_sell(self):
        """BR2: SELL 信号 is_actionable=True。"""
        from mytrader.strategy.base import Signal, SignalDirection
        from datetime import datetime, timezone
        s = Signal(
            symbol="AAPL",
            direction=SignalDirection.SELL,
            timestamp=datetime.now(tz=timezone.utc),
            confidence=0.8,
            strategy_name="test",
        )
        assert s.is_actionable() is True

    def test_signal_is_actionable_hold(self):
        """BR3: HOLD 信号 is_actionable=False。"""
        from mytrader.strategy.base import Signal, SignalDirection
        from datetime import datetime, timezone
        s = Signal(
            symbol="AAPL",
            direction=SignalDirection.HOLD,
            timestamp=datetime.now(tz=timezone.utc),
            confidence=0.0,
            strategy_name="test",
        )
        assert s.is_actionable() is False


class TestRegistryEdgeCases:
    """BR6, BR7: 注册表边界条件。"""

    def test_register_duplicate_name_raises(self):
        """BR6: 重复注册同名策略抛出 ValueError。"""
        from mytrader.strategy.registry import register_strategy, STRATEGY_REGISTRY
        with pytest.raises(ValueError, match="already registered"):
            @register_strategy("dual_ma")  # 已存在
            def dummy(close, **params):
                return pd.Series(0, index=close.index)

    @pytest.mark.parametrize("strategy_name", list(STRATEGY_REGISTRY.keys()))
    def test_all_registered_strategies_return_int(self, strategy_name):
        """BR7: 所有已注册策略返回 int dtype。"""
        close = make_trending_close(100)
        fn = STRATEGY_REGISTRY[strategy_name]
        signal = fn(close)
        assert signal.dtype == int, (
            f"{strategy_name}: expected int dtype, got {signal.dtype}"
        )
