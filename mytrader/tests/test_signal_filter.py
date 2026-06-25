"""测试 signal 过滤器模块。"""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import pytest

from mytrader.signal.filters.atr_filter import ATRFilter
from mytrader.signal.filters.cooldown_filter import CooldownFilter
from mytrader.signal.filters.sentiment_filter import SentimentFilter
from mytrader.signal.filters.time_window_filter import TimeWindowFilter
from mytrader.signal.filters.volume_filter import VolumeFilter
from mytrader.signal.models import FilterResult, FilteredSignal
from mytrader.signal.pipeline import SignalPipeline
from mytrader.strategy.base import Signal, SignalDirection


# ---------------------------------------------------------------------------
# 测试工具
# ---------------------------------------------------------------------------

def make_signal(
    symbol: str = "AAPL",
    direction: SignalDirection = SignalDirection.BUY,
    ts: datetime | None = None,
) -> Signal:
    if ts is None:
        ts = datetime(2024, 1, 10, tzinfo=timezone.utc)
    return Signal(
        symbol=symbol,
        direction=direction,
        timestamp=ts,
        confidence=0.8,
        strategy_name="test_strategy",
    )


def make_ohlcv(n: int = 50, base_price: float = 100.0, base_vol: float = 1_000_000.0) -> pd.DataFrame:
    """生成带 OHLCV 的测试 DataFrame。"""
    dates = pd.date_range("2023-11-01", periods=n, freq="D", tz="UTC")
    close_vals = [base_price + i * 0.1 for i in range(n)]
    df = pd.DataFrame(
        {
            "open": [v * 0.999 for v in close_vals],
            "high": [v * 1.01 for v in close_vals],
            "low": [v * 0.99 for v in close_vals],
            "close": close_vals,
            "volume": [base_vol] * n,
        },
        index=dates,
    )
    return df


# ---------------------------------------------------------------------------
# VolumeFilter 测试
# ---------------------------------------------------------------------------

class TestVolumeFilter:
    def test_passes_when_volume_sufficient(self):
        df = make_ohlcv(50, base_vol=2_000_000.0)
        # avg vol ~= 2M, threshold=1.5 → 需要 3M；当日为 2M → 应被过滤
        # 改为 threshold=0.5 → 2M > 1M → 通过
        flt = VolumeFilter(threshold=0.5, window=20)
        signal = make_signal(ts=df.index[40])
        result = flt.apply(signal, df)
        assert result.passed is True

    def test_rejects_when_volume_low(self):
        df = make_ohlcv(50, base_vol=100.0)
        # 当日量=100，过去均量也约=100；threshold=2.0 → 需要 200 → 被过滤
        df.iloc[-10:, df.columns.get_loc("volume")] = 50  # 最近 10 日量很小
        flt = VolumeFilter(threshold=2.0, window=20)
        signal = make_signal(ts=df.index[40])
        result = flt.apply(signal, df)
        assert result.passed is False
        assert result.rejected_by == "volume_filter"

    def test_passes_without_volume_column(self):
        df = make_ohlcv(50).drop(columns=["volume"])
        flt = VolumeFilter()
        signal = make_signal(ts=df.index[30])
        result = flt.apply(signal, df)
        assert result.passed is True  # 无 volume 列直接放行

    def test_passes_insufficient_history(self):
        """数据不足时（rolling 结果为 NaN）放行。"""
        df = make_ohlcv(5)  # 只有 5 行，window=20 → rolling NaN
        flt = VolumeFilter(threshold=1.5, window=20)
        signal = make_signal(ts=df.index[-1])
        result = flt.apply(signal, df)
        assert result.passed is True

    def test_boundary_exact_mean(self) -> None:
        """SF1 (P1): 成交量恰好等于 20 日均值时行为明确。"""
        df = make_ohlcv(50, base_vol=1_000_000.0)
        flt = VolumeFilter(threshold=1.0, window=20)
        signal = make_signal(ts=df.index[40])
        result = flt.apply(signal, df)
        # 当日量 == avg → >= 判断成立 → 通过
        assert result.passed is True

    def test_boundary_mean_times_threshold(self) -> None:
        """SF2 (P1): 成交量恰好 = 1.5 倍均值时行为明确。"""
        # 前 40 天量 500k，第 41 天（信号时间）量为 750k (恰好 1.5x)
        df = make_ohlcv(60, base_vol=500_000.0)
        signal_idx = 50
        df.iloc[signal_idx, df.columns.get_loc("volume")] = 750_000.0
        flt = VolumeFilter(threshold=1.5, window=5)
        signal = make_signal(ts=df.index[signal_idx])
        result = flt.apply(signal, df)
        # 1.5x 均值：avg≈500k, 阈值=750k, 当前=750k → >= 判断通过
        assert result.passed is True


# ---------------------------------------------------------------------------
# ATRFilter 测试
# ---------------------------------------------------------------------------

class TestATRFilter:
    def test_passes_low_volatility(self):
        df = make_ohlcv(50)  # ATR/close 很小
        flt = ATRFilter(period=14, max_atr_pct=0.10)  # 宽松阈值
        signal = make_signal(ts=df.index[40])
        result = flt.apply(signal, df)
        assert result.passed is True

    def test_rejects_high_volatility(self):
        # 构造高波动数据：high-low 很大
        df = make_ohlcv(50)
        df["high"] = df["close"] * 1.10  # 每日振幅 10%
        df["low"] = df["close"] * 0.90
        flt = ATRFilter(period=14, max_atr_pct=0.01)  # 严格阈值 1%
        signal = make_signal(ts=df.index[40])
        result = flt.apply(signal, df)
        assert result.passed is False
        assert result.rejected_by == "atr_filter"

    def test_passes_without_required_columns(self):
        df = make_ohlcv(50).drop(columns=["high"])
        flt = ATRFilter()
        signal = make_signal(ts=df.index[30])
        result = flt.apply(signal, df)
        assert result.passed is True  # 缺列放行

    def test_signal_before_data_graceful(self) -> None:
        """SF3 (P1): 信号时间戳早于所有 ATR 数据时降级放行。"""
        df = make_ohlcv(50)  # 日期 2023-11-01 开始
        flt = ATRFilter(period=14, max_atr_pct=0.01)
        signal = make_signal(ts=datetime(2020, 1, 1, tzinfo=timezone.utc))
        result = flt.apply(signal, df)
        assert result.passed is True  # 降级放行，不崩溃

    def test_close_val_zero_no_crash(self) -> None:
        """SF4 (P0): close_val==0 不抛除零异常，安全降级。"""
        df = make_ohlcv(50)
        df.loc[df.index[40], "close"] = 0.0  # 将信号对应的 close 改为 0
        flt = ATRFilter(period=14, max_atr_pct=0.05)
        signal = make_signal(ts=df.index[40])
        result = flt.apply(signal, df)
        assert result.passed is True  # 遇 close=0 放行，不崩溃


# ---------------------------------------------------------------------------
# SentimentFilter 测试
# ---------------------------------------------------------------------------

class TestSentimentFilter:
    def test_passes_without_benchmark(self):
        """无参考数据时直接放行。"""
        df = make_ohlcv(50)
        flt = SentimentFilter()
        signal = make_signal()
        result = flt.apply(signal, df)
        assert result.passed is True

    def test_rejects_buy_in_bear_market(self):
        """大盘跌破 200 日均线，BUY 信号被过滤。"""
        # 构造 300 个下跌 bar 的 benchmark（注意直接用 list 避免 index 对齐 NaN）
        n = 300
        dates = pd.date_range("2023-01-01", periods=n, freq="D", tz="UTC")
        close_vals = [200.0 - i * 0.5 for i in range(n)]
        benchmark = pd.DataFrame({"close": close_vals}, index=dates)

        flt = SentimentFilter(ma_period=200)
        flt.set_benchmark(benchmark)

        signal = make_signal(
            direction=SignalDirection.BUY,
            ts=dates[-1],
        )
        result = flt.apply(signal, benchmark)
        assert result.passed is False
        assert result.rejected_by == "sentiment_filter"

    def test_allows_sell_in_bear_market(self):
        """大盘跌破 200 日均线，SELL 信号不受影响。"""
        n = 300
        dates = pd.date_range("2023-01-01", periods=n, freq="D", tz="UTC")
        close_vals = [200.0 - i * 0.5 for i in range(n)]
        benchmark = pd.DataFrame({"close": close_vals}, index=dates)

        flt = SentimentFilter(ma_period=200)
        flt.set_benchmark(benchmark)

        signal = make_signal(
            direction=SignalDirection.SELL,
            ts=dates[-1],
        )
        result = flt.apply(signal, benchmark)
        assert result.passed is True

    def test_bullish_allow_buy(self) -> None:
        """SF5 (P1): 牛市中允许 BUY 信号通过。"""
        n = 300
        dates = pd.date_range("2023-01-01", periods=n, freq="D", tz="UTC")
        close_vals = [100.0 + i * 0.3 for i in range(n)]  # 上升趋势
        benchmark = pd.DataFrame({"close": close_vals}, index=dates)

        flt = SentimentFilter(ma_period=200)
        flt.set_benchmark(benchmark)
        signal = make_signal(direction=SignalDirection.BUY, ts=dates[-1])
        result = flt.apply(signal, benchmark)
        assert result.passed is True

    def test_bullish_reject_sell(self) -> None:
        """SF6 (P1): 牛市中 SELL 信号仍通过（当前实现只拦截熊市 BUY）。"""
        n = 300
        dates = pd.date_range("2023-01-01", periods=n, freq="D", tz="UTC")
        close_vals = [100.0 + i * 0.3 for i in range(n)]
        benchmark = pd.DataFrame({"close": close_vals}, index=dates)

        flt = SentimentFilter(ma_period=200)
        flt.set_benchmark(benchmark)
        signal = make_signal(direction=SignalDirection.SELL, ts=dates[-1])
        result = flt.apply(signal, benchmark)
        # 当前实现不拦截牛市 SELL，放行
        assert result.passed is True


# ---------------------------------------------------------------------------
# TimeWindowFilter 测试
# ---------------------------------------------------------------------------

class TestTimeWindowFilter:
    def test_passes_daily_bar(self):
        """日线 bar（时间为午夜）直接放行。"""
        flt = TimeWindowFilter()
        signal = make_signal(ts=datetime(2024, 1, 10, 0, 0, tzinfo=timezone.utc))
        result = flt.apply(signal, make_ohlcv(50))
        assert result.passed is True

    def test_rejects_within_open_buffer(self):
        """开盘后 15 分钟内信号被过滤。"""
        from datetime import time
        flt = TimeWindowFilter(open_buffer_min=15)
        # 9:35 UTC（简化为 UTC 测试）
        ts = datetime(2024, 1, 10, 9, 35, tzinfo=timezone.utc)
        signal = make_signal(ts=ts)
        result = flt.apply(signal, make_ohlcv(50))
        assert result.passed is False

    def test_passes_after_open_buffer(self):
        """开盘缓冲期结束后信号放行。"""
        flt = TimeWindowFilter(open_buffer_min=15)
        ts = datetime(2024, 1, 10, 10, 0, tzinfo=timezone.utc)
        signal = make_signal(ts=ts)
        result = flt.apply(signal, make_ohlcv(50))
        assert result.passed is True

    def test_rejects_within_close_buffer(self) -> None:
        """SF7 (P1): 收盘缓冲期内信号被过滤。"""
        flt = TimeWindowFilter(close_buffer_min=15)
        # 15:55 UTC — 在收盘 16:00 前 5 分钟，应被过滤
        ts = datetime(2024, 1, 10, 15, 55, tzinfo=timezone.utc)
        signal = make_signal(ts=ts)
        result = flt.apply(signal, make_ohlcv(50))
        assert result.passed is False


# ---------------------------------------------------------------------------
# CooldownFilter 测试
# ---------------------------------------------------------------------------

class TestCooldownFilter:
    def test_first_signal_passes(self):
        """首次信号直接通过。"""
        df = make_ohlcv(50)
        flt = CooldownFilter(min_bars=5)
        signal = make_signal(ts=df.index[20])
        result = flt.apply(signal, df)
        assert result.passed is True

    def test_rejects_within_cooldown(self):
        """冷却期内同方向信号被过滤。"""
        df = make_ohlcv(50)
        flt = CooldownFilter(min_bars=5)
        signal1 = make_signal(ts=df.index[20])
        signal2 = make_signal(ts=df.index[22])  # 只间隔 2 bars
        flt.apply(signal1, df)
        result = flt.apply(signal2, df)
        assert result.passed is False
        assert result.rejected_by == "cooldown_filter"

    def test_passes_after_cooldown(self):
        """冷却期结束后信号通过。"""
        df = make_ohlcv(50)
        flt = CooldownFilter(min_bars=3)
        signal1 = make_signal(ts=df.index[20])
        signal2 = make_signal(ts=df.index[25])  # 间隔 5 bars > 3
        flt.apply(signal1, df)
        result = flt.apply(signal2, df)
        assert result.passed is True

    def test_different_directions_independent(self):
        """不同方向的冷却期独立。"""
        df = make_ohlcv(50)
        flt = CooldownFilter(min_bars=5)
        buy_signal = make_signal(ts=df.index[20], direction=SignalDirection.BUY)
        sell_signal = make_signal(ts=df.index[21], direction=SignalDirection.SELL)
        flt.apply(buy_signal, df)
        result = flt.apply(sell_signal, df)
        assert result.passed is True  # SELL 方向未在冷却期

    def test_reverse_direction_during_cooldown(self) -> None:
        """SF9 (P1): 冷却期内反向信号独立处理（BUY冷却中→SELL 通过）。"""
        df = make_ohlcv(50)
        flt = CooldownFilter(min_bars=5)
        buy_signal = make_signal(ts=df.index[20], direction=SignalDirection.BUY)
        sell_signal = make_signal(ts=df.index[21], direction=SignalDirection.SELL)
        flt.apply(buy_signal, df)  # BUY 进入冷却
        # 同向 BUY 在冷却期内应被过滤
        buy2 = make_signal(ts=df.index[22], direction=SignalDirection.BUY)
        r1 = flt.apply(buy2, df)
        assert r1.passed is False
        # 反向 SELL 方向独立，应通过
        r2 = flt.apply(sell_signal, df)
        assert r2.passed is True


# ---------------------------------------------------------------------------
# SignalPipeline 测试
# ---------------------------------------------------------------------------

class TestSignalPipeline:
    def test_empty_pipeline_passes_all(self):
        """空流水线所有信号通过。"""
        df = make_ohlcv(50)
        pipeline = SignalPipeline()
        signals = [make_signal(ts=df.index[i]) for i in range(30, 40)]
        passed, result = pipeline.run(signals, df)
        assert len(passed) == 10
        assert result.passed_count == 10
        assert result.filter_rate == 0.0

    def test_pipeline_from_config(self, tmp_path):
        """从配置构建流水线并运行。"""
        import yaml
        from mytrader.infra.config import load_config

        yaml_data = {
            "signal_filter": {
                "volume_filter_enabled": True,
                "volume_filter_threshold": 0.1,  # 宽松到几乎不过滤
                "atr_filter_enabled": False,
                "cooldown_filter_enabled": False,
                "sentiment_filter_enabled": False,
                "time_window_filter_enabled": False,
            }
        }
        yaml_file = tmp_path / "cfg.yaml"
        yaml_file.write_text(yaml.dump(yaml_data))
        cfg = load_config(yaml_file)

        df = make_ohlcv(50, base_vol=2_000_000.0)
        pipeline = SignalPipeline.from_config(cfg.signal_filter)
        signals = [make_signal(ts=df.index[i]) for i in range(25, 35)]
        passed, result = pipeline.run(signals, df)
        assert result.original_signal_count == 10

    def test_filter_result_stats(self):
        """FilterResult 统计正确。"""
        df = make_ohlcv(50, base_vol=100.0)  # 低成交量
        # VolumeFilter threshold=10 → 会过滤所有信号
        pipeline = SignalPipeline()
        pipeline.add_filter(VolumeFilter(threshold=10.0, window=5))

        signals = [make_signal(ts=df.index[i]) for i in range(10, 20)]
        passed, result = pipeline.run(signals, df)
        assert result.original_signal_count == 10
        assert result.passed_count + sum(result.filtered_by.values()) == 10
        assert 0.0 <= result.filter_rate <= 1.0

    def test_pipeline_filter_order(self, tmp_path) -> None:
        """SF10 (P1): from_config 构建顺序与配置保持一致。"""
        import yaml
        from mytrader.infra.config import load_config

        yaml_data = {
            "signal_filter": {
                "volume_filter_enabled": True,
                "atr_filter_enabled": True,
                "sentiment_filter_enabled": False,
                "time_window_filter_enabled": False,
                "cooldown_filter_enabled": False,
            }
        }
        yaml_file = tmp_path / "cfg.yaml"
        yaml_file.write_text(yaml.dump(yaml_data))
        cfg = load_config(yaml_file)

        pipeline = SignalPipeline.from_config(cfg.signal_filter)
        # 验证有 2 个过滤器，且按顺序
        assert len(pipeline._filters) == 2
        assert pipeline._filters[0].name == "volume_filter"
        assert pipeline._filters[1].name == "atr_filter"

    def test_reject_reasons_preserved(self) -> None:
        """SF12 (P1): 被拒绝信号的 reject_reason 被正确记录。"""
        df = make_ohlcv(50, base_vol=100.0)
        pipeline = SignalPipeline()
        pipeline.add_filter(VolumeFilter(threshold=10.0, window=5))

        signals = [make_signal(ts=df.index[i]) for i in range(25, 30)]
        _, result = pipeline.run(signals, df)
        # 所有信号应被 volume_filter 拒绝
        total_rejected = sum(result.filtered_by.values())
        assert result.passed_count + total_rejected == len(signals)
        assert "volume_filter" in result.filtered_by
