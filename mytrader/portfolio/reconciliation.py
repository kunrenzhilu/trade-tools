"""ReconciliationService — 本地持仓与券商真实持仓的对账服务。

对账流程：
1. 获取本地 Portfolio 的持仓快照
2. 获取券商（Alpaca / IBKR）的真实持仓
3. 逐 symbol 比对数量，记录差异
4. 差异超阈值时：告警 + 可选自动修正（以券商为准）

设计原则：
- 差异类型：数量不符 / 本地多余 / 券商多余
- 自动修正只更新本地记录，不修改券商侧
- 告警通过 EventBus 发布 RECONCILIATION_DIFF 事件
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from loguru import logger


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------

@dataclass
class PositionDiff:
    """单标的持仓差异描述。"""

    symbol: str
    local_qty: int
    broker_qty: int
    diff_type: str  # "local_only" | "broker_only" | "qty_mismatch"

    @property
    def diff_abs(self) -> int:
        return abs(self.local_qty - self.broker_qty)

    def __str__(self) -> str:
        return (
            f"{self.symbol}: local={self.local_qty} broker={self.broker_qty} "
            f"type={self.diff_type} diff={self.diff_abs}"
        )


@dataclass
class ReconciliationReport:
    """对账报告。

    Attributes:
        checked_at:   对账时间
        diffs:        所有差异列表
        total_local:  本地持仓标的数
        total_broker: 券商持仓标的数
        is_clean:     是否无差异
    """

    checked_at: datetime
    diffs: list[PositionDiff] = field(default_factory=list)
    total_local: int = 0
    total_broker: int = 0

    @property
    def is_clean(self) -> bool:
        return len(self.diffs) == 0

    def summary(self) -> str:
        if self.is_clean:
            return f"✅ Reconciliation CLEAN at {self.checked_at.isoformat()}"
        lines = [f"⚠️  Reconciliation DIFF ({len(self.diffs)} items) at {self.checked_at.isoformat()}"]
        for d in self.diffs:
            lines.append(f"  - {d}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# ReconciliationService
# ---------------------------------------------------------------------------

class ReconciliationService:
    """对账服务。

    Args:
        portfolio_tracker: PortfolioTracker（提供本地持仓）
        broker:            实现 get_positions() 的经纪商（AlpacaBroker / IBKRBroker）
        event_bus:         EventBus（可选，发布 RECONCILIATION_DIFF 事件）
        min_diff_to_alert: 最小数量差异触发告警（默认 1）
        auto_sync:         差异时是否自动更新本地记录（以券商为准）
    """

    def __init__(
        self,
        portfolio_tracker: Any,
        broker: Any,
        event_bus: Any | None = None,
        min_diff_to_alert: int = 1,
        auto_sync: bool = False,
    ) -> None:
        self._tracker = portfolio_tracker
        self._broker = broker
        self._bus = event_bus
        self._min_diff_to_alert = min_diff_to_alert
        self._auto_sync = auto_sync

    def run(self) -> ReconciliationReport:
        """执行一次完整对账，返回对账报告。"""
        now = datetime.now(timezone.utc)

        # 1. 获取本地持仓
        local_positions: dict[str, int] = {
            symbol: pos.quantity
            for symbol, pos in self._tracker.open_positions.items()
            if pos.quantity > 0
        }

        # 2. 获取券商持仓
        broker_positions: dict[str, int] = {}
        try:
            raw = self._broker.get_positions()
            for item in raw:
                symbol = item.get("symbol", "")
                qty = int(item.get("quantity", 0))
                if symbol and qty != 0:
                    broker_positions[symbol] = qty
        except AttributeError:
            # Broker 不支持 get_positions（如 PaperBroker），跳过对账
            logger.info("ReconciliationService: broker does not support get_positions, skipping")
            return ReconciliationReport(
                checked_at=now,
                total_local=len(local_positions),
                total_broker=0,
            )
        except Exception as exc:
            logger.error(f"ReconciliationService: failed to get broker positions: {exc}")
            return ReconciliationReport(checked_at=now)

        # 3. 比对差异
        diffs: list[PositionDiff] = []
        all_symbols = set(local_positions) | set(broker_positions)

        for symbol in sorted(all_symbols):
            local_qty = local_positions.get(symbol, 0)
            broker_qty = broker_positions.get(symbol, 0)

            if local_qty == broker_qty:
                continue

            if broker_qty == 0:
                diff_type = "local_only"
            elif local_qty == 0:
                diff_type = "broker_only"
            else:
                diff_type = "qty_mismatch"

            diff = PositionDiff(
                symbol=symbol,
                local_qty=local_qty,
                broker_qty=broker_qty,
                diff_type=diff_type,
            )
            if diff.diff_abs >= self._min_diff_to_alert:
                diffs.append(diff)

        report = ReconciliationReport(
            checked_at=now,
            diffs=diffs,
            total_local=len(local_positions),
            total_broker=len(broker_positions),
        )

        # 4. 记录日志
        logger.info(report.summary())

        # 5. 差异告警
        if not report.is_clean:
            if self._bus is not None:
                from mytrader.infra.event_bus import Events
                self._bus.publish(Events.RECONCILIATION_DIFF, report)

            # 可选：自动同步（以券商为准，更新本地 quantity）
            if self._auto_sync:
                self._sync_from_broker(broker_positions, diffs)

        return report

    def _sync_from_broker(
        self,
        broker_positions: dict[str, int],
        diffs: list[PositionDiff],
    ) -> None:
        """以券商持仓为准，更新本地记录（仅修改 quantity，不改变 avg_cost）。"""
        for diff in diffs:
            symbol = diff.symbol
            broker_qty = broker_positions.get(symbol, 0)

            if symbol in self._tracker.portfolio.positions:
                pos = self._tracker.portfolio.positions[symbol]
                old_qty = pos.quantity
                pos.quantity = broker_qty
                logger.warning(
                    f"ReconciliationService auto-sync: {symbol} "
                    f"local {old_qty} -> broker {broker_qty}"
                )
            else:
                logger.warning(
                    f"ReconciliationService: {symbol} exists in broker but not local, "
                    f"cannot auto-sync (no cost basis)"
                )
