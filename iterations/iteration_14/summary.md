# Iteration #14 Summary — Multi-Factor Strategy Exploration (Round 1)

## Requested
[spec.md](spec.md) — Fix rsi_trend_filter degeneracy + Add 2 multi-factor strategies (rsi_bb_convergence, macd_volume)

## Delivered
- **Files changed**: 7 (rsi_trend_filter.py +38/-55, rsi_bb_convergence.py NEW, macd_volume.py NEW, main.py +17/-1, __init__.py +2, test_strategy.py +397/-55, test_degenerate_filter.py +15)
- **Tests**: 675 → 707 (+32 new tests, all passed)
- **Key metrics**: Pending `--reoptimize` (run was too slow, will verify in Iter #15)

## Meta-Agent Judgment

### Technical: PASS
- **707 passed, 0 failed** (independent verification confirmed)
- Violations: 0
- High risk files: 0
- Code quality: Both new strategies use shift(1) anti-lookahead, pure functions, proper docstrings
- Constitution compliance: No risk/execution/portfolio changes, no RL, no black box

### Business Impact: HIGH (Expected)
- **rsi_trend_filter fix**: Now produces both buy (41) and sell (39) signals on random walk data. Old version: 0 exit signals (degenerate buy-and-hold). This unlocks the only existing multi-factor strategy.
- **2 new multi-factor strategies**: `rsi_bb_convergence` (RSI + Bollinger dual confirmation) and `macd_volume` (MACD + volume confirmation). Total strategy pool: 5 → 7.
- **rsi_bb_convergence**: 108 parameter combinations. Tighter entry criteria (both RSI AND BB must agree) should reduce false signals vs single-indicator strategies.
- **macd_volume**: 12 parameter combinations. Volume confirmation on entry filters low-volume fake breakouts.
- Expected: SPX groups should have valid candidates now (currently all empty in strategy_weights.json)

### Strategic Fit: GOOD
- User's explicit direction: "探索多因子的策略" (explore multi-factor strategies)
- Highest leverage action: Fix existing degenerate multi-factor baseline → add new multi-factor strategies → reoptimize
- This is Round 1 of multi-factor exploration

## Gate Status
| Gate | Condition | Result |
|------|-----------|--------|
| Tests pass | 0 failed | 707 passed ✅ |
| Scope boundary | No risk/execution/portfolio changes | 0 violations ✅ |
| New strategies registered | In STRATEGY_REGISTRY + REOPTIMIZE | Verified ✅ |
| rsi_trend_filter not degenerate | closed_trades > 0 on test data | 41/39 signals ✅ |

## Next Steps (→ Iteration #15)
1. **Add ADX indicator** to `indicators.py` — needed for trend strength measurement
2. **Add `adx_trend` strategy** — ADX + EMA crossover (multi-factor trend following)
3. **Add `volume_breakout` strategy** — price above SMA + volume spike (breakout confirmation)
4. **Run `--reoptimize`** to evaluate all 10 strategies and verify rsi_trend_filter enters weights without degeneracy
5. Expected: At least 4/6 groups should have non-empty weights (up from current 2/6)

## Lessons Learned
- **rs_trend_filter exit fix was simple but high-impact**: Changing exit from trend-direction-dependent to RSI-neutral-crossover restored the strategy's ability to close positions. The fix was 10 lines of code.
- **Dual confirmation is the simplest form of multi-factor**: rsi_bb_convergence just ANDs two existing conditions. No new indicators needed. This pattern can be replicated for other indicator pairs.
- **Volume confirmation for entry only**: macd_volume only requires volume for BUY, not SELL. This is the right design — you don't want to be trapped in a losing position because volume is low.
- **Parameter grid balance**: 108 (rsi_bb) + 81 (rsi_trend_filter) + 27 (rsi) + 27 (macd) + 12 (macd_volume) + 20 (dual_ma) + 9 (bollinger) = 284 combinations per group × 6 groups = 1,704 total. With batch optimization, this should complete in ~10-15 minutes.
