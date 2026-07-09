"""简单均线趋势跟踪策略（SMA Trend Following）。

信号规则（持续型，非事件型）：
    - BUY:  close > SMA(period) → 在均线上方持续保持多头信号 +1
    - SELL: close < SMA(period) → 跌破均线时退出（转为空头信号）-1
    - close == SMA → HOLD (0)

设计动机：当前 9 个策略中，均值回归占多数，牛市中频繁零信号。
事件型趋势策略（dual_ma / macd_cross / adx_trend）仅在交叉/触发当日产生信号，
即使 `signal_valid_bars=3` 也只能延长 3 bar，无法在整段趋势中持续持仓。

本策略为**持续型顺势策略**：只要 close 在 SMA 之上就每天产生 BUY 信号，
趋势反转（close 跌破 SMA）才退出。最简单有效的趋势跟踪设计。
参数网格仅 period 一个维度（[50, 100, 200]），对应短/中/长期趋势线。

注意：信号强制 shift(1)，使用前一根 K 线的 close vs SMA 状态做决策，
      避免前视偏差（不在当前 bar 收盘后再回头下单）。
"""

from __future__ import annotations

import pandas as pd

from mytrader.strategy.indicators import sma
from mytrader.strategy.registry import register_strategy


@register_strategy("sma_trend")
def sma_trend_signal(
    close: pd.Series,
    period: int = 50,
) -> pd.Series:
    """简单均线趋势跟踪信号（持续型）。

    Args:
        close:  收盘价 Series
        period: SMA 计算周期（默认 50；网格 50/100/200 对应短/中/长期趋势）

    Returns:
        信号 Series：1=BUY, -1=SELL, 0=HOLD，与 close 同索引
    """
    ma = sma(close, period)

    # 持续型信号：close 在均线之上 → BUY，之下 → SELL
    # 相等时 HOLD（罕见，仅在价格横盘且 exactly equal SMA 时出现）
    signal = pd.Series(0, index=close.index, dtype=int)
    signal[close > ma] = 1
    signal[close < ma] = -1

    # ⚠️ shift(1) 避免前视偏差：
    # 使用前一根 K 线确认的 close vs SMA 状态，在当前 K 线开盘时执行
    return signal.shift(1).fillna(0).astype(int)
