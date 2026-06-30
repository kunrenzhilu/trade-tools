"""Signal Pipeline — 链式过滤器流水线。

从 AppConfig（signal_filter 节）读取各过滤器的启用状态和参数，
依次对每个信号执行过滤，返回 (list[FilteredSignal], FilterResult)。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd
from loguru import logger

from mytrader.signal.filters.atr_filter import ATRFilter
from mytrader.signal.filters.cooldown_filter import CooldownFilter
from mytrader.signal.filters.sentiment_filter import SentimentFilter
from mytrader.signal.filters.time_window_filter import TimeWindowFilter
from mytrader.signal.filters.volume_filter import VolumeFilter
from mytrader.signal.models import FilterResult, FilteredSignal

if TYPE_CHECKING:
    from mytrader.infra.config import SignalFilterConfig
    from mytrader.strategy.base import Signal


class SignalPipeline:
    """信号过滤器流水线。

    根据 SignalFilterConfig 动态构建过滤链，顺序为：
        volume → atr → sentiment → time_window → cooldown

    使用示例：
        pipeline = SignalPipeline.from_config(cfg.signal_filter)
        filtered_signals, result = pipeline.run(signals, df)
    """

    def __init__(self) -> None:
        self._filters: list = []

    def add_filter(self, f) -> "SignalPipeline":
        """添加过滤器（支持链式调用）。"""
        self._filters.append(f)
        return self

    @classmethod
    def from_config(cls, cfg: "SignalFilterConfig") -> "SignalPipeline":
        """从配置构建流水线。"""
        pipeline = cls()

        if cfg.volume_filter_enabled:
            pipeline.add_filter(
                VolumeFilter(
                    threshold=cfg.volume_filter_threshold,
                    window=cfg.volume_filter_window,
                )
            )

        if cfg.atr_filter_enabled:
            pipeline.add_filter(
                ATRFilter(
                    period=cfg.atr_filter_period,
                    max_atr_pct=cfg.atr_filter_max_atr_pct,
                )
            )

        if cfg.sentiment_filter_enabled:
            pipeline.add_filter(SentimentFilter())

        if cfg.time_window_filter_enabled:
            pipeline.add_filter(
                TimeWindowFilter(
                    open_buffer_min=cfg.time_window_market_open_buffer_min,
                    close_buffer_min=cfg.time_window_market_close_buffer_min,
                )
            )

        if cfg.cooldown_filter_enabled:
            pipeline.add_filter(
                CooldownFilter(min_bars=cfg.cooldown_filter_min_bars)
            )

        return pipeline

    def run(
        self,
        signals: list["Signal"],
        df: pd.DataFrame,
    ) -> tuple[list[FilteredSignal], FilterResult]:
        """执行流水线，返回 (过滤后信号列表, 统计结果)。

        Args:
            signals: 原始信号列表
            df:      行情 DataFrame（OHLCV，index 为 DatetimeIndex）

        Returns:
            (filtered_signals, result)
            filtered_signals 只包含 passed=True 的信号
        """
        result = FilterResult(original_signal_count=len(signals))
        passed: list[FilteredSignal] = []

        # 统一 df.index 为 tz-naive，避免各过滤器中 datetime 比较报错
        # （MarketDataStore 读出的 index 是 tz-naive datetime64[ns]，
        #  但 signal.timestamp 可能是 tz-aware datetime）
        if hasattr(df.index, 'tz') and df.index.tz is not None:
            df = df.copy()
            df.index = df.index.tz_localize(None)

        for signal in signals:
            # 将 signal.timestamp 转为与 df.index 兼容的 tz-naive
            ts = signal.timestamp
            if ts is not None and hasattr(ts, 'tzinfo') and ts.tzinfo is not None:
                signal.timestamp = ts.replace(tzinfo=None)

            current = signal
            rejected = False

            for f in self._filters:
                fs = f.apply(current, df)
                if not fs.passed:
                    result.record_filtered(fs.rejected_by or f.name)
                    logger.warning(
                        f"[SignalFilter] {signal.symbol} {signal.direction.value} "
                        f"rejected by {fs.rejected_by or f.name}: "
                        f"{fs.rejection_reason}"
                    )
                    rejected = True
                    break
                current = signal

            if not rejected:
                result.passed_count += 1
                passed.append(FilteredSignal(source_signal=signal))

        return passed, result
