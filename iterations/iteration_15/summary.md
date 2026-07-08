# Iteration #15 Summary — ADX + Momentum Multi-Factor Strategies

## Requested
[spec.md](spec.md) — Add ADX indicator + adx_trend strategy + momentum_roc strategy + reoptimize

## Delivered
- **Files changed**: 7 (indicators.py +42, adx_trend.py NEW, momentum_roc.py NEW, main.py +8, __init__.py +2, test_strategy.py +new tests, strategy_weights.json reoptimized)
- **Tests**: 707 → 737 (+30 new tests, all passed)
- **Indicator**: ADX added to indicators.py (based on pandas-ta `ta.adx`)
- **New strategies**: adx_trend (ADX + EMA crossover, 16 combos), momentum_roc (RoC + SMA filter, 8 combos)
- **Strategy pool**: 7 → 9 strategies

## Reoptimize Results

| Group | Strategy | Sortino | DD(%) | Alpha(%) | Status |
|-------|----------|---------|-------|----------|--------|
| NDX_high_vol | rsi_mean_revert | 1.08 | **29.89** | 0.40 | dd_constrained ❌ |
| NDX_low_vol | rsi_mean_revert | 1.92 | 13.68 | 1.77 | pass ✅ |
| SPX_mid_vol | — | — | — | — | **空** |
| SPX_high_vol | — | — | — | — | **空** |
| SPX_low_vol | — | — | — | — | **空** |
| NDX_mid_vol | — | — | — | — | **空** |

**Critical finding**: 4/6 groups still empty. SPX groups have ZERO valid candidates passing the alpha>0 gate.

## Meta-Agent Judgment

### Technical: PASS
- 737 passed, 0 failed (independent verification)
- ADX indicator correctly delegates to pandas-ta
- adx_trend: graceful degradation when df=None
- momentum_roc: simple RoC formula, no lookahead
- All strategies use shift(1), pure functions, type hints

### Business Impact: LOW (regression detected!)

**The reoptimize results actually got WORSE vs Iter #13 baseline:**

| Metric | Iter #13 (before) | Iter #15 (after) | Change |
|--------|-------------------|------------------|--------|
| NDX_high_vol | rsi_trend_filter (DD=17%) | rsi_mean_revert (DD=30%) | ❌ DD +13% |
| Active groups | 2/6 | 2/6 | No change |
| Multi-factor in weights | 1 (degenerate) | 0 | ❌ Regressed |

**Root cause**: The alpha>0 gate (Iter #12) is too aggressive. It removes ALL SPX candidates because SPX stocks vs SPY benchmark have structurally near-zero alpha. Meanwhile in NDX_high_vol, the gate only leaves 1 candidate (rsi_mean_revert with DD=29.89%).

The 5 multi-factor strategies (rsi_trend_filter, rsi_bb_convergence, macd_volume, adx_trend, momentum_roc) have alpha < 0 or too close to 0 to pass the gate.

### Strategic Fit: PARTIAL
- ADX indicator is valuable for future strategies ✅
- momentum_roc fills a missing alpha source ✅
- But the strategies can't prove themselves because the gate is too strict ❌
- Adding more strategies WITHOUT fixing the gate is like adding more fish to a net with too-small holes

## Next Steps (→ Iteration #16) — P0: Fix the Gate

### Option A: Per-group benchmark (Recommended)
Use SPX sector ETF (e.g., XLF/XLE/XLK) or equal-weight SPX index as benchmark for SPX groups instead of SPY. SPX is cap-weighted, SPY is dominated by mega-caps — so SPX stocks naturally have near-zero alpha vs SPY.

### Option B: Relax alpha threshold
Change alpha>0 to alpha > -2% (allow slight underperformance) or add a Sortino>1.0 exemption (if Sortino is high, allow slightly negative alpha).

### Option C: Debug WHY multi-factor strategies underperform
Log per-strategy alpha/DD/Sortino for each group during reoptimize to understand why these strategies fail. Currently we only see the winner — we need to see the losers too.

### Recommended: Option B (smallest change, highest impact) first, then Option A if needed.

Lower the alpha gate from 0 to -2% for SPX groups, or replace `alpha > 0` with `alpha > -2 OR sortino > 1.5` (quality exemption).

## Lessons Learned
- **Adding strategies without fixing the gate is diminishing returns**: 9 strategies, 0 multi-factor in weights. The bottleneck is the selection gate, not the strategy pool size.
- **SPX vs SPY alpha is structurally tight**: SPY is cap-weighted S&P 500. Trading SPX components vs SPY as benchmark means you're effectively trying to beat yourself. Need a different benchmark or relaxed threshold.
- **rsi_mean_revert dominates because it's the most "conservative" strategy**: Low Sharpe but high Sortino, survives DD and alpha gates. Other strategies have higher returns but also higher DD or lower Sortino.
- **The sanity gate (Iter #11) correctly removed rsi_trend_filter from NDX_high_vol**: Old version had DD=17% (fake, due to 0 closed trades). New rsi_trend_filter with fixed exit logic apparently has alpha < 0 in NDX_high_vol. This is honest — better to have empty weight than fake weight.
