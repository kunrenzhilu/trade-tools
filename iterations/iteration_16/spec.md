# Iteration #16 Spec — Relax Alpha>0 Gate (Unblock SPX Groups)

> **Date**: 2026-07-08
> **Type**: Selection Gate Adjustment (Low Risk)
> **Risk**: Low — only changes a single threshold in matrix_backtest.py, no strategy/logic changes

---

## 1. Background

Iter #12 added `alpha > 0` as a hard gate in `_run_group` to prevent selecting strategies that underperform SPY. This was correct in principle, but the threshold is too strict:

**Problem**: SPX stocks vs SPY benchmark have structurally near-zero alpha because SPY IS the S&P 500. Trading SPX components vs SPY means you're trying to beat yourself. A strategy with alpha=-1% (barely underperforming SPY) gets rejected even if it has excellent Sortino/DD.

**Evidence** (Iter #15 reoptimize):
- 4/6 groups have empty weights (SPX_mid_vol, SPX_high_vol, SPX_low_vol, NDX_mid_vol)
- 9 strategies exist, but only rsi_mean_revert passes the alpha>0 gate in any group
- NDX_high_vol only has 1 candidate (DD=29.89% — dd_constrained)

**Constitution alignment**: 
- "年化 20%左右（比大盘好即可）" — the goal is to beat the market, but -1% vs +0.5% alpha is not a meaningful distinction at the in-sample selection stage
- Walk-Forward already validates OOS alpha with `WALK_FORWARD_VAL_ALPHA_FLOOR=-5.0` (Iter #13)
- Relaxing in-sample alpha gate from 0 to -2% doesn't weaken the OOS validation

## 2. Design

### Change: Relax alpha>0 to alpha > -2.0%

**File**: `mytrader/backtest/matrix_backtest.py`

**Target**: `_run_group` method, the Tier 1 candidate filtering logic

**Current code** (approximate location in `_run_group`):
```python
# Tier 1: alpha > 0 AND DD <= 20% AND Sortino > 0.5
tier1 = [c for c in candidates if c.alpha > 0 and c.max_dd <= 20.0 and c.sortino > 0.5]
```

**New code**:
```python
# Iter #16: Relax alpha gate from 0 to -2% to unblock SPX groups.
# SPX stocks vs SPY benchmark have structurally near-zero alpha.
# -2% means "not significantly worse than SPY" — still a valid selection signal.
# Walk-Forward (Iter #13) validates OOS alpha with -5% floor.
ALPHA_GATE_THRESHOLD = -2.0  # Minimum in-sample alpha to pass selection gate

# Tier 1: alpha > ALPHA_GATE_THRESHOLD AND DD <= 20% AND Sortino > 0.5
tier1 = [c for c in candidates 
         if c.alpha > ALPHA_GATE_THRESHOLD 
         and c.max_dd <= 20.0 
         and c.sortino > 0.5]
```

Also update `_optimize_ensemble_weights` to use the same threshold:
```python
# Current: max(alpha, 0.0) — negative alpha gets zero weight
# New: max(alpha - ALPHA_GATE_THRESHOLD, 0.0) — anchor at threshold, not at 0
# This means alpha=-1% gets weight=1.0 (1% above threshold), alpha=-3% gets weight=0
```

Actually, the simplest change is just the threshold. The ensemble weights already use `max(alpha, 0.0)` which is fine for now.

### Constant

Add module-level constant:
```python
# Iter #16: Relaxed alpha gate threshold.
# SPX stocks vs SPY benchmark have structurally near-zero alpha.
# -2% allows strategies that are "not significantly worse than SPY".
# Walk-Forward OOS validation (Iter #13) uses stricter -5% floor.
ALPHA_GATE_THRESHOLD: float = -2.0
```

## 3. Test Plan

1. `test_alpha_gate_relaxed_negative_alpha_passes` — alpha=-1% passes (above -2%, below old 0%)
2. `test_alpha_gate_very_negative_fails` — alpha=-5% still fails
3. `test_alpha_gate_threshold_boundary` — alpha=-2.0% is at boundary (use `>` check)
4. `test_alpha_gate_positive_alpha_passes` — alpha=+1% still passes (no regression)
5. `test_alpha_gate_constant_exists` — ALPHA_GATE_THRESHOLD constant is defined and equals -2.0
6. `test_alpha_gate_relaxed_unblocks_spx` — integration test: SPX group with alpha=-1.5% strategy is included in tier1 (was excluded in old gate)
7. `test_ensemble_weights_with_negative_alpha` — negative alpha above threshold gets positive weight

**Existing test updates**: 
- Update `test_alpha_gate.py` tests that hardcode `alpha > 0` to use `ALPHA_GATE_THRESHOLD`
- Check `test_matrix_backtest.py` for affected tests

**Total new/updated tests**: ~7

## 4. Success Criteria

| # | Criterion | Verification |
|---|-----------|-------------|
| 1 | Alpha gate uses ALPHA_GATE_THRESHOLD=-2.0 | Code review + constant test |
| 2 | Alpha=-1% passes the gate | Unit test |
| 3 | Alpha=-5% still fails the gate | Unit test |
| 4 | All existing tests pass | `pytest --ignore=tests/test_integration_live.py` |
| 5 | `--reoptimize` shows >2 groups with weights | Run reoptimize, check strategy_weights.json |
| 6 | SPX groups no longer all empty | Verify weights.json |

## 5. Scope Boundary

- ✅ Only modify `ALPHA_GATE_THRESHOLD` in `matrix_backtest.py`
- ✅ Update test files that reference the old `alpha > 0` gate
- ❌ Do NOT modify strategies, indicators, main.py, risk, execution
- ❌ Do NOT change Walk-Forward validation (OOS stays at -5%)
- ❌ Do NOT change DD 20% hard constraint
- ❌ Do NOT change Sortino 0.5 threshold

## 6. Implementation Order

1. Read `matrix_backtest.py::_run_group` to locate alpha gate
2. Add `ALPHA_GATE_THRESHOLD = -2.0` constant
3. Replace `alpha > 0` with `alpha > ALPHA_GATE_THRESHOLD` in `_run_group`
4. Update any other `alpha > 0` references in the same file (check `_optimize_ensemble_weights`)
5. Update tests that reference the old gate
6. Add new tests for relaxed gate behavior
7. Run all tests
8. Run `--reoptimize`
9. Verify strategy_weights.json has >2 active groups
10. Update trajectory + CODEBUDDY
