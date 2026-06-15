"""仓位约束检查 — 单标的仓位上限 / 总持仓上限 / 最小订单金额。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ConstraintCheckResult:
    """约束检查结果。"""

    passed: bool
    reason: str = ""


def check_min_order_value(
    quantity: int,
    entry_price: float,
    min_order_value: float = 500.0,
) -> ConstraintCheckResult:
    """检查订单金额是否达到最小值。"""
    order_value = quantity * entry_price
    if order_value < min_order_value:
        return ConstraintCheckResult(
            passed=False,
            reason=(
                f"Order value {order_value:.2f} < min_order_value={min_order_value:.2f}, "
                f"quantity={quantity}, price={entry_price:.2f}"
            ),
        )
    return ConstraintCheckResult(passed=True)


def check_single_position_limit(
    order_value: float,
    total_capital: float,
    max_single_position_pct: float = 0.20,
) -> ConstraintCheckResult:
    """检查单标的仓位是否超过总资产比例上限。"""
    pct = order_value / total_capital if total_capital > 0 else 0.0
    if pct > max_single_position_pct:
        return ConstraintCheckResult(
            passed=False,
            reason=(
                f"Single position {pct:.1%} > limit={max_single_position_pct:.1%}, "
                f"order_value={order_value:.2f}, capital={total_capital:.2f}"
            ),
        )
    return ConstraintCheckResult(passed=True)


def check_total_exposure(
    current_exposure: float,
    new_order_value: float,
    total_capital: float,
    max_total_exposure_pct: float = 0.80,
) -> ConstraintCheckResult:
    """检查增加新订单后，总持仓是否超过总资产比例上限。"""
    new_total = current_exposure + new_order_value
    pct = new_total / total_capital if total_capital > 0 else 0.0
    if pct > max_total_exposure_pct:
        return ConstraintCheckResult(
            passed=False,
            reason=(
                f"Total exposure after order {pct:.1%} > limit={max_total_exposure_pct:.1%}, "
                f"current={current_exposure:.2f}, new_order={new_order_value:.2f}, capital={total_capital:.2f}"
            ),
        )
    return ConstraintCheckResult(passed=True)


def check_max_positions(
    current_position_count: int,
    max_concurrent_positions: int = 5,
) -> ConstraintCheckResult:
    """检查当前持仓标的数是否达到上限。"""
    if current_position_count >= max_concurrent_positions:
        return ConstraintCheckResult(
            passed=False,
            reason=(
                f"Position count {current_position_count} >= limit={max_concurrent_positions}"
            ),
        )
    return ConstraintCheckResult(passed=True)
