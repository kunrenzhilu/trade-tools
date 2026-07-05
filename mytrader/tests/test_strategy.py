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
        expected = {"dual_ma", "rsi_mean_revert", "rsi_trend_filter", "bollinger_band", "macd_cross"}
        assert expected.issubset(set(STRATEGY_REGISTRY.keys()))

    def test_strategy_callable(self):
        for name, fn in STRATEGY_REGISTRY.items():
            assert callable(fn), f"{name} is not callable"


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
# RSI Trend Filter 策略测试（迭代 #8）
# ---------------------------------------------------------------------------

class TestRSITrendFilter:
    """T1-T5: RSI 趋势过滤策略测试。"""

    def test_signal_values(self):
        """T1: 信号值仅在 {-1, 0, 1} 范围内。"""
        from mytrader.strategy.strategies.rsi_trend_filter import rsi_trend_filter_signal
        close = make_oscillating_close(300)
        signal = rsi_trend_filter_signal(close)
        assert set(signal.unique()).issubset({-1, 0, 1})

    def test_custom_params(self):
        """T2: 非默认参数正常工作。"""
        from mytrader.strategy.strategies.rsi_trend_filter import rsi_trend_filter_signal
        close = make_oscillating_close(300)
        signal = rsi_trend_filter_signal(
            close, rsi_period=7, oversold=25.0, overbought=75.0, trend_period=100,
        )
        assert set(signal.unique()).issubset({-1, 0, 1})

    def test_uptrend_only_buy(self):
        """T3: 强上升趋势中不产生 SELL 信号。"""
        from mytrader.strategy.strategies.rsi_trend_filter import rsi_trend_filter_signal
        n = 300
        idx = pd.date_range("2023-01-01", periods=n, freq="B")
        # 强上升趋势：价格持续上涨，始终在 SMA(200) 上方
        rng = np.random.default_rng(42)
        prices = 100.0 * np.exp(np.cumsum(0.005 + 0.005 * rng.standard_normal(n)))
        close = pd.Series(prices, index=idx, name="close")
        signal = rsi_trend_filter_signal(close, oversold=35.0, overbought=65.0)
        # 上升趋势中 SELL 被 SMA 过滤，不应出现 -1
        unique_vals = set(signal.values)
        assert -1 not in unique_vals, f"Found SELL signal in uptrend: {unique_vals}"

    def test_downtrend_only_sell(self):
        """T4: 强下降趋势中不产生 BUY 信号。"""
        from mytrader.strategy.strategies.rsi_trend_filter import rsi_trend_filter_signal
        n = 300
        idx = pd.date_range("2023-01-01", periods=n, freq="B")
        # 强下降趋势：价格持续下跌，始终在 SMA(200) 下方
        rng = np.random.default_rng(42)
        prices = 100.0 * np.exp(np.cumsum(-0.005 + 0.005 * rng.standard_normal(n)))
        close = pd.Series(prices, index=idx, name="close")
        signal = rsi_trend_filter_signal(close, oversold=35.0, overbought=65.0)
        # 下降趋势中 BUY 被 SMA 过滤，不应出现 +1
        unique_vals = set(signal.values)
        assert 1 not in unique_vals, f"Found BUY signal in downtrend: {unique_vals}"

    def test_insufficient_data(self):
        """T5: 数据不足 trend_period 时返回全零（不崩溃）。"""
        from mytrader.strategy.strategies.rsi_trend_filter import rsi_trend_filter_signal
        close = make_oscillating_close(50)
        signal = rsi_trend_filter_signal(close)
        assert (signal == 0).all()


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
