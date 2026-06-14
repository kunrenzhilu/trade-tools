"""多策略加权投票聚合（Ensemble）。

将多个策略信号按权重合并，提高信号可靠性，降低单策略的假信号影响。
"""

from __future__ import annotations

import pandas as pd


def ensemble_signal(
    signals: list[pd.Series],
    weights: list[float] | None = None,
    threshold: float = 0.3,
) -> pd.Series:
    """加权投票，合并多个策略信号。

    Args:
        signals:   各策略的信号 Series 列表（1=BUY, -1=SELL, 0=HOLD）
        weights:   各策略权重（默认等权）；会自动归一化，无需预先归一化
        threshold: 合并分数的绝对值超过此值才发出信号（默认 0.3）

    Returns:
        合并后的信号 Series：1=BUY, -1=SELL, 0=HOLD
    """
    if not signals:
        raise ValueError("signals list is empty")

    n = len(signals)
    if weights is None:
        weights = [1.0 / n] * n
    else:
        if len(weights) != n:
            raise ValueError(f"len(weights)={len(weights)} != len(signals)={n}")
        total = sum(weights)
        weights = [w / total for w in weights]  # 归一化

    combined = sum(s * w for s, w in zip(signals, weights))

    result = pd.Series(0, index=combined.index, dtype=int)
    result[combined >  threshold] =  1   # BUY
    result[combined < -threshold] = -1   # SELL

    return result
