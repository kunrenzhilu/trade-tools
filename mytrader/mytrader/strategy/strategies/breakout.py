"""N 日价格通道突破策略（Donchian-style Breakout）。

信号规则（持续型顺势）：
    - BUY:  close > highest(high, N)[shift(1)]  → 突破近期阻力位 +1
    - SELL: close < lowest(low, N)[shift(1)]    → 跌破近期支撑位 -1
    - 其他 → HOLD (0)

设计动机：经典 Turtle/Donchian Channel 突破策略。与 `sma_trend` 互补——
SMA 跟踪均线斜率，突破策略捕捉横盘区间突破的瞬间。两者组合覆盖"趋势中持续持仓"
与"突破时入场"两种顺势场景，解决牛市零信号问题。

注意点：
    1. highest/lowest 用 `df["high"]`/`df["low"]`（通过 df= 参数传入）。
       若 df 缺失（仅传 close），则退化为 close vs rolling max/min(close)，
       仍可工作但失去真实 high/low 通道信息。
    2. 比较 `close` vs `rolling_max.shift(1)`——即"今天收盘"突破"截至昨日的
       N 日高点"。shift 在 rolling 之后应用，避免当日高点参与当日突破判定
       （那是前视偏差）。最终信号再 shift(1) 一次，使用前一根 K 线的确认状态
       在当前 bar 开盘时执行，与项目其他策略一致。

参数网格：period = [20, 50, 100]（短/中/长期突破）。
"""

from __future__ import annotations

import pandas as pd

from mytrader.strategy.registry import register_strategy


@register_strategy("breakout")
def breakout_signal(
    close: pd.Series,
    period: int = 20,
    df: pd.DataFrame | None = None,
) -> pd.Series:
    """N 日价格通道突破信号（持续型顺势）。

    Args:
        close:  收盘价 Series
        period: 通道回看周期（默认 20；网格 20/50/100）
        df:     完整 OHLCV DataFrame，用于读取 high/low 计算通道；
                None 时退化为 close vs rolling max/min(close)

    Returns:
        信号 Series：1=BUY, -1=SELL, 0=HOLD，与 close 同索引
    """
    # 使用 high/low 计算通道（若提供），否则退化为 close 通道
    if df is not None and all(c in df.columns for c in ["high", "low"]):
        high = df["high"]
        low = df["low"]
    else:
        high = close
        low = close

    # N 日最高/最低（不含当日 → shift(1) 避免前视：今天只能突破"截至昨日"的通道）
    upper = high.rolling(period).max().shift(1)
    lower = low.rolling(period).min().shift(1)

    signal = pd.Series(0, index=close.index, dtype=int)
    signal[close > upper] = 1
    signal[close < lower] = -1

    # ⚠️ 再 shift(1) 一次，与项目其他策略一致：
    # 使用前一根 K 线确认的突破状态，在当前 K 线开盘时执行
    return signal.shift(1).fillna(0).astype(int)
