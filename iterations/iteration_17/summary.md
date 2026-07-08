# Iteration #17 Summary — Sortino Exemption for Alpha Gate

## Requested
[spec.md](spec.md) — Add Sortino exemption: Sortino > 1.5 bypasses alpha gate

## Delivered
- Files changed: 6 (matrix_backtest.py + tests)
- Tests: 744 → 751 (+7 new tests, all passed)
- Key change: `SORTINO_ALPHA_EXEMPTION = 1.5` constant + gate logic update
- Reoptimize: running in background (PID 39360)

## Meta-Agent Judgment

### Technical: PASS
- 751 passed, 0 failed
- Sortino exemption logic correctly integrated
- DD ≤ 20% still enforced for all paths
- Sortino > 0.5 minimum still enforced

### Business Impact: PENDING (reoptimize in progress)
- SPX unblocking depends on reoptimize results
- If SPX groups still empty → need different approach (per-group benchmark)

### Strategic Fit: GOOD
- Constitution-aligned: Sortino is primary KPI (L1), alpha is secondary
- This is the right fix — let the primary KPI override secondary when it's clearly excellent

## Next Steps
1. Check reoptimize results when done
2. If SPX still empty → try per-group benchmark approach
3. Otherwise → evaluate portfolio-level performance

## Iteration Progress Summary (14→17)

| Iter | Focus | Test Δ | Key Result |
|------|-------|--------|-----------|
| #14 | Fix rsi_trend_filter + 2 multi-factor strategies | +32 | 9 strategies, no regression |
| #15 | ADX indicator + 2 more strategies | +30 | Pool=9, momentum/ADX strategies added |
| #16 | Alpha gate -2% | +7 | **momentum_roc enters NDX_high_vol** (S=1.80, DD=9.60%) |
| #17 | Sortino exemption | +7 | Gate improvement, reoptimize pending |

**Net progress**: 675 → 751 tests (+76), strategy pool 5→9 (+4 multi-factor strategies), **momentum_roc in NDX_high_vol is the first multi-factor strategy in weights**.
