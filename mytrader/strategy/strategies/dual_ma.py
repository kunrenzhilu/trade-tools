"""双均线交叉策略（Dual MA Crossover）。

信号规则：
    - 短期均线上穿长期均线 → BUY  (+1)
    - 短期均线下穿长期均线 → SELL (-1)
    - 否则               → HOLD  (0)

注意：信号强制 shift(1)，使用前一根 K 线的均线状态做决策，
      避免前视偏差（不使用当天收盘价）。
"""

from __future__ import annotations

import pandas as pd

from mytrader.strategy.indicators import sma, crossed_above, crossed_below
from mytrader.strategy.registry import register_strategy


@register_strategy("dual_ma")
def dual_ma_signal(
    close: pd.Series,
    fast: int = 10,
    slow: int = 30,
) -> pd.Series:
    """双均线交叉信号。

    Args:
        close: 收盘价 Series
        fast:  短期均线周期（默认 10）
        slow:  长期均线周期（默认 30）

    Returns:
        信号 Series：1=BUY, -1=SELL, 0=HOLD，与 close 同索引
    """
    fast_ma = sma(close, fast)
    slow_ma = sma(close, slow)

    buy_signal  = crossed_above(fast_ma, slow_ma).astype(int)
    sell_signal = crossed_below(fast_ma, slow_ma).astype(int)

    signal = buy_signal - sell_signal  # 1, -1, 0

    # ⚠️ 关键：shift(1) 避免前视偏差
    # 使用前一根 K 线确认的均线状态，在当前 K 线开盘时执行
    return signal.shift(1).fillna(0).astype(int)
