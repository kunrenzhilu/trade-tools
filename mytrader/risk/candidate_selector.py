"""Risk Manager 候选递补选股 — 从 Top-2K 候选中逐个尝试，递补直到约束满足。

约束优先级（从高到低）：
    1. max_total_exposure_pct    → 全局上限，最优先（拒绝）
    2. max_sector_exposure_pct   → 板块约束（拒绝，递补）
    3. max_concurrent_positions  → 持仓数量上限（拒绝）
    4. max_single_position_pct   → ATR 仓位法结果截断（min），不拒绝
    5. min_order_value           → 最小订单金额（拒绝）
"""

from __future__ import annotations

from dataclasses import dataclass, field

from mytrader.risk.constraints import (
    ConstraintCheckResult,
    check_max_positions,
    check_min_order_value,
    check_single_position_limit,
    check_total_exposure,
)
from mytrader.signal.ranker import RankedSignal
from mytrader.strategy.base import Signal


@dataclass
class AccountState:
    """当前账户状态快照（供约束检查使用）。"""

    total_capital: float = 100_000.0
    current_exposure: float = 0.0          # 当前总持仓市值
    current_position_count: int = 0        # 当前持仓标的数
    sector_exposure: dict[str, float] = field(default_factory=dict)  # {sector: market_value}


@dataclass
class CandidateOrder:
    """从候选中选出的待下单信息。"""

    signal: Signal
    order_value: float          # 建议下单金额（已应用约束截断）
    rejection_reason: str = ""  # 空字符串 = 通过


def select_orders_from_candidates(
    candidates: list[RankedSignal],
    account: AccountState,
    max_orders: int = 5,
    max_single_position_pct: float = 0.20,
    max_total_exposure_pct: float = 0.80,
    max_sector_exposure_pct: float = 0.40,
    max_concurrent_positions: int = 5,
    min_order_value: float = 500.0,
    target_position_pct: float = 0.20,     # 目标仓位（ATR 未计算时的默认值）
) -> tuple[list[CandidateOrder], list[str]]:
    """从 Top-2K 候选中逐个尝试，递补直到约束用尽或候选耗尽。

    Args:
        candidates:              排名后的候选信号列表（Top-2K）
        account:                 当前账户状态
        max_orders:              本次最多下单数（通常等于 top_k=5）
        ...                      各约束参数

    Returns:
        (approved_orders, rejection_log)
        approved_orders: 通过约束的订单列表（按候选排名顺序）
        rejection_log:   被拒绝的 symbol + 原因列表
    """
    approved: list[CandidateOrder] = []
    rejection_log: list[str] = []

    # 模拟递增的账户状态
    simulated_exposure = account.current_exposure
    simulated_position_count = account.current_position_count
    simulated_sector_exp = dict(account.sector_exposure)

    for candidate in candidates:
        if len(approved) >= max_orders:
            break

        sig = candidate.signal
        symbol = sig.symbol

        # 计算建议下单金额（目标仓位 × 资本，后续可替换为 ATR 仓位法）
        raw_order_value = account.total_capital * target_position_pct

        # 约束 4：单标的仓位截断（取 min，不拒绝）
        max_single_value = account.total_capital * max_single_position_pct
        order_value = min(raw_order_value, max_single_value)

        # 约束 1：总持仓上限（最高优先级，全局检查）
        chk = check_total_exposure(
            simulated_exposure, order_value, account.total_capital, max_total_exposure_pct
        )
        if not chk.passed:
            rejection_log.append(f"{symbol}: total_exposure — {chk.reason}")
            continue

        # 约束 2：板块持仓上限
        sector = sig.indicators.get("sector", "Unknown")
        sector_current = simulated_sector_exp.get(sector, 0.0)
        sector_new = sector_current + order_value
        sector_pct = sector_new / account.total_capital if account.total_capital > 0 else 0.0
        if sector_pct > max_sector_exposure_pct:
            rejection_log.append(
                f"{symbol}: sector_exposure({sector}) {sector_pct:.1%} > {max_sector_exposure_pct:.1%}, "
                f"next candidate"
            )
            continue

        # 约束 3：持仓数量上限
        chk = check_max_positions(simulated_position_count, max_concurrent_positions)
        if not chk.passed:
            rejection_log.append(f"{symbol}: max_positions — {chk.reason}")
            break  # 已达上限，后续候选也不会通过

        # 约束 5：最小订单金额
        # 简化：假设价格 = order_value（取整数量时再精确计算）
        if order_value < min_order_value:
            rejection_log.append(
                f"{symbol}: min_order_value {order_value:.2f} < {min_order_value:.2f}"
            )
            continue

        # 通过所有约束 → 接受
        approved.append(CandidateOrder(signal=sig, order_value=order_value))

        # 更新模拟账户状态（供后续候选检查）
        simulated_exposure += order_value
        simulated_position_count += 1
        simulated_sector_exp[sector] = simulated_sector_exp.get(sector, 0.0) + order_value

    return approved, rejection_log
