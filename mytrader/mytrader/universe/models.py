"""UniverseManager 数据模型。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SymbolMeta:
    """单只标的的元信息。"""

    symbol: str
    index_membership: list[str]   # ["SP500"] / ["NASDAQ100"] / ["SP500","NASDAQ100"]
    sector: str                   # GICS 板块
    market_cap_tier: str          # "large" / "mid" / "unknown"
    volatility_tier: str          # "high" / "mid" / "low" / "unknown"
    group_id: str                 # 综合分组 ID，如 "NDX_high_vol" / "SPX_low_vol"

    def __repr__(self) -> str:
        return (
            f"SymbolMeta({self.symbol}, group={self.group_id}, "
            f"sector={self.sector}, vol={self.volatility_tier})"
        )
