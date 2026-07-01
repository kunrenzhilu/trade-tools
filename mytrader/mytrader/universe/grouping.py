"""波动率分层和分组逻辑。

分组维度（Phase 5 初期）：指数归属 × 波动率层级
    group_id 格式：{INDEX}_{VOL_TIER}
    示例：NDX_high_vol / NDX_mid_vol / SPX_low_vol ...
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from mytrader.strategy.indicators import atr as compute_atr


# 波动率分层阈值（ATR% = ATR / close，近 60 日均值）
_VOL_HIGH_THRESHOLD = 0.03   # ATR% > 3% → high
# 迭代 #2：从 0.01 调到 0.02。原因：516 标的中 ATR% < 0.01 的仅 2 个，
# 导致 low_vol 组只有 1 个标的、无分散化效应，组合 Sharpe/Sortino 退化为
# 单标的指标。0.02 阈值下 low_vol 组约 30~50 只标的，分散化更充分。
_VOL_LOW_THRESHOLD  = 0.02   # ATR% < 2% → low；否则 mid


def compute_volatility_tier(df: pd.DataFrame, lookback: int = 20) -> str:
    """根据近 lookback 日 ATR% 均值计算波动率层级。

    Args:
        df:       含 high/low/close 的 OHLCV DataFrame
        lookback: 近几日均值窗口（默认 20 个交易日）

    Returns:
        'high' / 'mid' / 'low'
    """
    if df.empty or len(df) < 2:
        return "unknown"

    atr_series = compute_atr(df, period=min(14, len(df) - 1))
    if atr_series.empty or atr_series.isna().all():
        return "unknown"

    close = df["close"]
    atr_pct = atr_series / close
    recent = atr_pct.dropna().tail(lookback)
    if recent.empty:
        return "unknown"

    avg = float(recent.mean())
    if avg > _VOL_HIGH_THRESHOLD:
        return "high"
    elif avg < _VOL_LOW_THRESHOLD:
        return "low"
    else:
        return "mid"


def build_group_id(index_membership: list[str], volatility_tier: str) -> str:
    """构建分组 ID。

    规则：
        - 同时属于两个指数 → 以 NDX（Nasdaq）优先
        - group_id = {PREFIX}_{vol_tier}_vol
        - 示例：NDX_high_vol / SPX_mid_vol / SPX_low_vol
    """
    if "NASDAQ100" in index_membership:
        prefix = "NDX"
    elif "SP500" in index_membership:
        prefix = "SPX"
    else:
        prefix = "OTHER"

    tier = volatility_tier if volatility_tier in ("high", "mid", "low") else "mid"
    return f"{prefix}_{tier}_vol"
