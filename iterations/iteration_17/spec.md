# Iteration #17 Spec — Sortino Exemption for Alpha Gate

> **Date**: 2026-07-08
> **Type**: Selection Gate Enhancement (Low Risk)
> **Risk**: Low — adds one exemption constant, no strategy/logic changes

---

## 1. Background

Iter #16 relaxed the alpha gate from 0 to -2%, which unlocked momentum_roc in NDX_high_vol (Sortino=1.80, DD=9.60%, Alpha=-1.84%). But SPX groups remain empty — all SPX candidates have alpha < -2% vs SPY.

**Root cause**: SPX stocks vs SPY benchmark have structurally near-zero alpha. A strategy can be profitable (high Sortino, low DD) but not beat SPY. The current gate rejects these strategies entirely.

**Constitution alignment**: "Sortino 比率是首要 KPI" (L1). A strategy with Sortino=1.8 should NOT be rejected just because its alpha is -3%. The alpha gate should be a filter, not a veto.

## 2. Design

### Add Sortino Exemption

**File**: `mytrader/backtest/matrix_backtest.py`

**New constant**:
```python
# Iter #17: Sortino exemption for alpha gate.
# High-Sortino strategies bypass the alpha check.
# Rationale: Sortino is the Constitution's primary KPI (L1).
# A strategy with Sortino > 1.5 is profitable on its own even if
# it slightly underperforms SPY in-sample.
SORTINO_ALPHA_EXEMPTION: float = 1.5
```

**Gate logic change** in `_run_group`:
```python
# Tier 1: (alpha > -2% OR sortino > 1.5) AND DD <= 20% AND sortino > 0.5
alpha_ok = c.backtest_alpha > ALPHA_GATE_THRESHOLD
sortino_exempt = c.backtest_sortino > SORTINO_ALPHA_EXEMPTION

tier1 = [c for c in candidates 
         if (alpha_ok or sortino_exempt)
         and c.backtest_portfolio_max_drawdown <= MAX_PORTFOLIO_DRAWDOWN_PCT
         and c.backtest_sortino > MIN_SORTINO_THRESHOLD]
```

**Rationale**: 
- Sortino > 1.5 means the strategy's risk-adjusted return is excellent — it's profitable on its own
- Sortino > 0.5 is already the minimum quality bar for Tier 1
- Sortino > 1.5 is 3x the minimum — a clear quality signal
- This does NOT weaken DD protection (DD ≤ 20% still required)

## 3. Test Plan

1. `test_sortino_exemption_high_sortino_low_alpha` — Sortino=2.0, Alpha=-3% → passes (exempt)
2. `test_sortino_exemption_low_sortino_low_alpha` — Sortino=0.6, Alpha=-3% → fails (no exemption, below threshold)
3. `test_sortino_exemption_boundary` — Sortino=1.5, Alpha=-3% → `>` means fails at boundary (1.5 is NOT > 1.5)
4. `test_sortino_exemption_high_sortino_good_alpha` — Sortino=2.0, Alpha=5% → passes (both paths)
5. `test_sortino_exemption_dd_still_required` — Sortino=2.0, DD=25% → fails (DD exceeds 20%)
6. `test_sortino_exemption_constant` — SORTINO_ALPHA_EXEMPTION = 1.5
7. `test_sortino_exemption_min_sortino_still_required` — Sortino=0.3 → fails regardless of alpha (below 0.5 minimum)

**Total new tests**: ~7

## 4. Success Criteria

| # | Criterion | Verification |
|---|-----------|-------------|
| 1 | High Sortino (>1.5) strategies bypass alpha gate | Unit tests 1,3 |
| 2 | Low Sortino (<1.5) strategies still need alpha > -2% | Unit test 2 |
| 3 | DD ≤ 20% still enforced for all paths | Unit test 5 |
| 4 | Sortino > 0.5 minimum still enforced | Unit test 7 |
| 5 | All existing tests pass | `pytest --ignore=tests/test_integration_live.py` |
| 6 | `--reoptimize` shows >2 active groups | Check strategy_weights.json |
| 7 | At least 1 SPX group has non-empty weights | Check weights.json |

## 5. Scope Boundary

- ✅ Only modify `_run_group` alpha gate logic + add `SORTINO_ALPHA_EXEMPTION` constant
- ✅ Update tests
- ❌ Do NOT modify strategies, indicators, risk, execution, main.py
- ❌ Do NOT change DD 20% constraint
- ❌ Do NOT change Sortino 0.5 minimum
- ❌ Do NOT change Walk-Forward validation

## 6. Implementation Order

1. Read `matrix_backtest.py::_run_group` to locate alpha gate
2. Add `SORTINO_ALPHA_EXEMPTION = 1.5` constant
3. Modify Tier 1 filtering to include Sortino exemption
4. Write ~7 new tests
5. Run all tests
6. Run `--reoptimize`
7. Verify strategy_weights.json
8. Update trajectory + CODEBUDDY
