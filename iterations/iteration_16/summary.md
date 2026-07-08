# Iteration #16 Summary — Relax Alpha>0 Gate to -2%

## Requested
[spec.md](spec.md) — Relax alpha>0 gate to alpha > -2% to unblock SPX groups

## Delivered
- **Files changed**: 9 (matrix_backtest.py + tests)
- **Tests**: 737 → 744 (+7 new tests, all passed)
- **Key change**: `ALPHA_GATE_THRESHOLD = -2.0` replacing hard-coded `alpha > 0`

## Reoptimize Results

| Group | Strategy | Sortino | DD(%) | Alpha(%) | Status |
|-------|----------|---------|-------|----------|--------|
| **NDX_high_vol** | **momentum_roc** 🆕 | 1.80 | 9.60 | -1.84 | ✅ |
| NDX_low_vol | rsi_mean_revert | 1.92 | 13.68 | 1.77 | ✅ |
| NDX_low_vol | bollinger_band | 1.58 | 14.90 | -1.24 | ✅ (w=0) |
| SPX_mid_vol | — | — | — | — | ❌ |
| SPX_high_vol | — | — | — | — | ❌ |
| SPX_low_vol | — | — | — | — | ❌ |
| NDX_mid_vol | — | — | — | — | ❌ |

## Meta-Agent Judgment

### Technical: PASS
- 744 passed, 0 failed
- `ALPHA_GATE_THRESHOLD = -2.0` constant properly integrated
- All existing alpha gate tests updated
- No violations, no high-risk files

### Business Impact: PARTIAL (breakthrough in NDX, SPX still blocked)

**Breakthrough**: momentum_roc is the FIRST multi-factor strategy to enter weights!
- Sortino=1.80, DD=9.60% (excellent risk-adjusted)
- Alpha=-1.84% (passed the relaxed -2% gate, would have been rejected by old >0 gate)
- win_rate=37.96% (low but acceptable for momentum strategy)

**Regression vs Iter #15**: NDX_high_vol improved dramatically:
- Before: rsi_mean_revert, DD=29.89%, dd_constrained
- After: momentum_roc, DD=9.60%, pass ✅

**SPX still blocked**: -2% threshold not enough for SPX stocks vs SPY. All SPX candidates have alpha < -2%.

### Strategic Fit: GOOD
- momentum_roc proves the multi-factor approach works
- Gate relaxation was the right call — unlocked a genuine improvement
- But one group improvement is not enough. Need another round for SPX.

## Next Steps (→ Iteration #17)

### Option A: Sortino Exemption (Recommended)
Add a quality exemption to the alpha gate: `alpha > ALPHA_GATE_THRESHOLD OR sortino > SORTINO_EXEMPTION`
- If Sortino > 1.5 → skip alpha check (strategy is high-quality regardless of benchmark comparison)
- Rationale: A strategy with Sortino>1.5 is profitable on its own even if it doesn't beat SPY

### Option B: Further relax SPX threshold
- ALPHA_GATE_THRESHOLD = -3% or -4% for SPX groups only

### Option C: Per-group benchmarks
- SPX groups use equal-weight S&P 500 or sector ETF
- More work but structurally correct

**Recommended**: Start with Option A (Sortino exemption at 1.5) — minimal change, maximal impact.

## Lessons Learned
- **momentum_roc works**: A multi-factor strategy (RoC + SMA trend filter) made it into weights with excellent Sortino/DD. This validates the multi-factor exploration direction.
- **-2% threshold hit the sweet spot for NDX**: Not too loose (alpha=-5% still fails), not too strict (alpha=-1.84% passes).
- **SPX needs a different approach**: SPX vs SPY is structurally near-zero alpha. Threshold relaxation alone won't fix it. Need a quality exemption or different benchmark.
- **The iter #12 alpha>0 gate was correct in principle but too strict in practice**: momentum_roc (Sortino=1.80, DD=9.60%) is clearly a good strategy but would have been rejected because of minor SPY underperformance. Sortino exemption would fix this.
