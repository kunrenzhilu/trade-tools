"""MarketDataStore 数据模型。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class SyncReport:
    """DataSyncService.sync_all() / backfill() 的汇总报告。"""

    total_symbols: int = 0
    synced_ok: int = 0
    synced_degraded: int = 0   # fallback 到 yfinance，数据质量降级
    failed: int = 0
    total_new_bars: int = 0
    errors: dict[str, str] = field(default_factory=dict)  # {symbol: error_msg}

    @property
    def success_rate(self) -> float:
        if self.total_symbols == 0:
            return 0.0
        return self.synced_ok / self.total_symbols

    def __repr__(self) -> str:
        return (
            f"SyncReport(total={self.total_symbols}, ok={self.synced_ok}, "
            f"degraded={self.synced_degraded}, failed={self.failed}, "
            f"new_bars={self.total_new_bars})"
        )
