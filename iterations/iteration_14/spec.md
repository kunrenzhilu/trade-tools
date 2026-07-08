# Iteration #14 Spec — Multi-Factor Strategy Exploration (Round 1)

> **Date**: 2026-07-08
> **Type**: Strategy Fix + New Multi-Factor Strategies
> **Risk**: Low (only modifies strategy layer, no risk/execution changes)

---

## 1. Background

### Current State (Iter #13)

After #11 (sanity gate) + #12 (alpha>0 gate) + #13 (WF alpha gate), the system's gates are solid, but:

1. **rsi_trend_filter is degenerate** — entry and exit conditions are mutually exclusive on the same dimension (trend direction). Positions opened in an uptrend can never close until trend reverses → 0 closed trades → degenerate buy-and-hold
2. **Strategy diversity is broken** — `strategy_weights.json` shows only 2/6 groups have weights, and SPX groups are all empty (alpha>0 gate eliminates all SPX candidates)
3. **No true multi-factor strategies** — only `rsi_trend_filter` attempts multi-factor, and it's broken
4. **Only 5 strategies total** — bollinger_band, dual_ma, macd_cross, rsi_mean_revert, rsi_trend_filter

### Goal

Fix the degenerate strategy and add new multi-factor strategies to improve strategy diversity and trading performance.

---

## 2. Problem Statement

### Problem A: rsi_trend_filter Degeneracy

**Root cause**: Entry uses `close > SMA200` (uptrend) and exit uses `close < SMA200` (downtrend). These are the same dimension in opposite directions — a position entered during uptrend can never exit until the trend reverses, by which point profits are gone.

**Fix**: Decouple exit from trend direction. The trend filter should gate ENTRY only. Exit should be natural mean reversion:
- **BUY entry**: RSI < oversold AND close > SMA(trend_period) → trend filter on entry only
- **SELL to exit long**: RSI crosses back above RSI neutral (e.g., 50) → mean reversion exit
- **SELL entry**: RSI > overbought AND close < SMA(trend_period) → trend filter on entry only  
- **BUY to exit short**: RSI crosses back below neutral (e.g., 50) → mean reversion exit

### Problem B: No RSI + Bollinger Band Convergence Strategy

RSI and Bollinger Bands are both mean-reversion indicators, but no strategy combines them for stronger signals. A dual-confirmation approach should reduce false signals.

### Problem C: No Volume-Confirmed MACD Strategy

MACD crossover signals are noisy without volume confirmation. Adding volume as a filter should improve signal quality.

---

## 3. Design

### 3A. Fix `rsi_trend_filter_signal`

**File**: `mytrader/strategy/strategies/rsi_trend_filter.py`

**New parameter**: `exit_neutral: float = 50.0` — RSI level at which to exit (mean reversion target)

**New signal logic**:

```python
def rsi_trend_filter_signal(
    close: pd.Series,
    rsi_period: int = 14,
    oversold: float = 30.0,
    overbought: float = 70.0,
    trend_period: int = 200,
    exit_neutral: float = 50.0,
) -> pd.Series:
    """
    RSI mean reversion with trend filter.
    
    Entry: RSI extreme + trend alignment
    Exit: RSI returns to neutral (natural mean reversion)
    """
    rsi_series = rsi(close, period=rsi_period)
    sma_series = sma(close, period=trend_period)
    
    # Entry signals (trend-filtered)
    buy_entry = (rsi_series.shift(1) < oversold) & (close.shift(1) > sma_series.shift(1))
    sell_entry = (rsi_series.shift(1) > overbought) & (close.shift(1) < sma_series.shift(1))
    
    # Exit signals (RSI returning to neutral, no trend filter)
    # Exit a long: RSI crosses above neutral
    exit_long = (rsi_series.shift(1) > exit_neutral) & (rsi_series.shift(2) <= exit_neutral)
    # Exit a short: RSI crosses below neutral
    exit_short = (rsi_series.shift(1) < exit_neutral) & (rsi_series.shift(2) >= exit_neutral)
    
    signal = pd.Series(0, index=close.index)
    signal[buy_entry] = 1
    signal[sell_entry] = -1
    signal[exit_long] = -1  # SELL to exit long
    signal[exit_short] = 1   # BUY to exit short
    # Note: exit signals may overlap with entry signals on the same bar.
    # Entry takes priority (applied first, exit overwrites if different direction)
    
    return signal.astype(int)
```

**Parameter grid update** (`main.py::REOPTIMIZE_PARAM_GRIDS`):
- `rsi_trend_filter`: add `exit_neutral` dimension: `[45, 50, 55]` → 27 × 3 = 81 combinations
  - But trend_period is fixed at 200, so: rsi_period(3) × oversold(3) × overbought(3) × exit_neutral(3) = 81

### 3B. New Strategy: `rsi_bb_convergence` — RSI + Bollinger Band Dual Confirmation

**File**: `mytrader/strategy/strategies/rsi_bb_convergence.py` (new)

**Design**:
- Both RSI and Bollinger Band must agree for a signal
- BUY: RSI < oversold AND close < lower_bb (double confirmation of oversold)
- SELL: RSI > overbought AND close > upper_bb (double confirmation of overbought)
- Pure mean reversion — sell when either condition clears (RSI crosses neutral OR close crosses middle band)

```python
@register_strategy("rsi_bb_convergence")
def rsi_bb_convergence_signal(
    close: pd.Series,
    rsi_period: int = 14,
    oversold: float = 30.0,
    overbought: float = 70.0,
    bb_period: int = 20,
    bb_std: float = 2.0,
    exit_rsi_neutral: float = 50.0,
) -> pd.Series:
    """
    RSI + Bollinger Band dual confirmation mean reversion.
    
    BUY: RSI oversold AND price below lower band → strong mean reversion buy
    SELL (exit): RSI crosses above neutral OR price crosses above middle band
    SELL (short): RSI overbought AND price above upper band → strong mean reversion sell
    BUY (exit): RSI crosses below neutral OR price crosses below middle band
    """
    rsi_series = rsi(close, period=rsi_period)
    upper, middle, lower = bollinger_bands(close, period=bb_period, std_dev=bb_std)
    
    close_s1 = close.shift(1)
    rsi_s1 = rsi_series.shift(1)
    
    # Entry: dual confirmation
    buy_entry = (rsi_s1 < oversold) & (close_s1 < lower.shift(1))
    sell_entry = (rsi_s1 > overbought) & (close_s1 > upper.shift(1))
    
    # Exit: either condition clears
    exit_long_rsi = (rsi_s1 > exit_rsi_neutral) & (rsi_s1.shift(1) <= exit_rsi_neutral)
    exit_long_bb = crossed_above(close, middle)
    exit_short_rsi = (rsi_s1 < exit_rsi_neutral) & (rsi_s1.shift(1) >= exit_rsi_neutral)
    exit_short_bb = crossed_below(close, middle)
    
    signal = pd.Series(0, index=close.index)
    signal[buy_entry] = 1
    signal[sell_entry] = -1
    signal[exit_long_rsi | exit_long_bb] = -1
    signal[exit_short_rsi | exit_short_bb] = 1
    
    return signal.astype(int)
```

### 3C. New Strategy: `macd_volume` — MACD + Volume Confirmation

**File**: `mytrader/strategy/strategies/macd_volume.py` (new)

**Design**:
- MACD crossover confirmed by above-average volume
- BUY: MACD crosses above signal AND volume > volume_SMA(20)
- SELL: MACD crosses below signal AND volume < volume_SMA(20) — OR — MACD crosses below signal regardless (exit shouldn't need volume confirmation)
- Using `**kwargs` to receive `df` for volume data

Actually, simpler approach: MACD crossover + volume expansion (volume > its own SMA) for entry only. Exit is MACD crossunder regardless.

```python
@register_strategy("macd_volume")
def macd_volume_signal(
    close: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal_period: int = 9,
    volume_period: int = 20,
    df: pd.DataFrame | None = None,
) -> pd.Series:
    """
    MACD crossover with volume confirmation.
    
    BUY: MACD crosses above signal AND volume > volume SMA(20) — trend confirmed by volume
    SELL: MACD crosses below signal — exit regardless of volume (don't trap in losing position)
    """
    macd_line, signal_line, _ = macd(close, fast=fast, slow=slow, signal_period=signal_period)
    
    buy_signal = crossed_above(macd_line, signal_line)
    sell_signal = crossed_below(macd_line, signal_line)
    
    # Volume confirmation for entry only
    if df is not None and "volume" in df.columns and len(df) > volume_period:
        volume_ma = sma(df["volume"], period=volume_period)
        vol_confirm = df["volume"] > volume_ma
        buy_signal = buy_signal & vol_confirm
    # If no volume data, use MACD crossover as-is (graceful degradation)
    
    signal = pd.Series(0, index=close.index)
    signal[buy_signal] = 1
    signal[sell_signal] = -1
    
    return signal.astype(int)
```

### 3D. `main.py` Integration

**REOPTIMIZE_STRATEGIES**: Add `"rsi_bb_convergence"` and `"macd_volume"` (total: 5 → 7 strategies)

**REOPTIMIZE_PARAM_GRIDS**: Add grids for new strategies:
- `rsi_bb_convergence`: rsi_period(3) × oversold(3) × overbought(3) × bb_period(2) × bb_std(2) = 108 combinations
  - rsi_period: [7, 14, 21]
  - oversold: [25, 30, 35]
  - overbought: [65, 70, 75]
  - bb_period: [15, 20]
  - bb_std: [1.5, 2.0]
  - exit_rsi_neutral: fixed 50 (not in grid, keep simple)
- `macd_volume`: fast(3) × slow(2) × signal_period(2) × volume_period(1) = 12 combinations
  - fast: [8, 12, 16]
  - slow: [21, 26]
  - signal_period: [7, 9]
  - volume_period: fixed 20

Update rsi_trend_filter grid: add exit_neutral [45, 50, 55] → 27 × 3 = 81 combinations

### 3E. Strategy Registration

**File**: `mytrader/strategy/__init__.py` — ensure `rsi_bb_convergence` and `macd_volume` modules are imported

**File**: `mytrader/strategy/strategies/__init__.py` — add imports for new strategy modules

---

## 4. Test Plan

### Tests for rsi_trend_filter fix

1. `test_rsi_trend_filter_exit_neutral_long` — long position exits when RSI crosses above neutral (50)
2. `test_rsi_trend_filter_exit_neutral_short` — short position exits when RSI crosses below neutral
3. `test_rsi_trend_filter_entry_still_trend_filtered` — entry still requires trend filter
4. `test_rsi_trend_filter_not_degenerate` — on random walk data, closed_trades > 0 (regression test vs Iter #8 bug)
5. `test_rsi_trend_filter_exit_neutral_param` — custom exit_neutral parameter works

### Tests for rsi_bb_convergence

6. `test_rsi_bb_buy_signal` — RSI < oversold AND close < lower_bb → BUY
7. `test_rsi_bb_sell_signal` — RSI > overbought AND close > upper_bb → SELL
8. `test_rsi_bb_no_signal_rsi_only` — RSI oversold but close above lower_bb → no signal (no confirmation)
9. `test_rsi_bb_no_signal_bb_only` — close below lower_bb but RSI not oversold → no signal
10. `test_rsi_bb_exit_rsi_neutral` — exit when RSI crosses above 50
11. `test_rsi_bb_exit_bb_middle` — exit when price crosses above middle band
12. `test_rsi_bb_custom_params` — custom parameters change signal behavior
13. `test_rsi_bb_signal_range` — signal values are in {-1, 0, 1}
14. `test_rsi_bb_no_lookahead` — uses shift(1), no future data leakage

### Tests for macd_volume

15. `test_macd_volume_buy_with_volume` — MACD cross + volume > MA → BUY
16. `test_macd_volume_no_buy_without_volume` — MACD cross but volume < MA → no BUY
17. `test_macd_volume_sell_regardless` — MACD crossunder → SELL regardless of volume
18. `test_macd_volume_no_df_graceful` — df=None → graceful degradation (MACD only)
19. `test_macd_volume_no_volume_column` — df without "volume" column → graceful degradation
20. `test_macd_volume_signal_range` — signal values are in {-1, 0, 1}
21. `test_macd_volume_no_lookahead` — uses shift(1), no future data leakage

### Registration tests

22. `test_all_strategies_registered` — update expected set to include new strategies
23. `test_new_strategies_in_reoptimize_constants` — verify REOPTIMIZE_STRATEGIES includes new strategies

**Total new tests**: ~23

---

## 5. Success Criteria

| # | Criterion | Verification |
|---|-----------|-------------|
| 1 | `rsi_trend_filter` no longer degenerate (closed_trades > 0 on test data) | Unit test + backtest verification |
| 2 | `rsi_bb_convergence` produces correct dual-confirmation signals | Unit tests 6-14 |
| 3 | `macd_volume` produces volume-confirmed MACD signals | Unit tests 15-21 |
| 4 | All existing tests still pass (no regressions) | `pytest --ignore=tests/test_integration_live.py` |
| 5 | New strategies registered in STRATEGY_REGISTRY | test_all_strategies_registered |
| 6 | REOPTIMIZE_STRATEGIES/GRIDS include all 7 strategies | test_new_strategies_in_reoptimize_constants |
| 7 | Strategy functions are pure (no side effects, shift(1) anti-lookahead) | Manual review |
| 8 | No risk/execution/portfolio module changes | `git diff --stat` |

---

## 6. Scope Boundary (What NOT to do)

- ❌ Do NOT modify risk manager, execution engine, or portfolio tracker
- ❌ Do NOT run `--reoptimize` (Meta-Agent will run in Phase 3)
- ❌ Do NOT modify matrix_backtest.py or any gate logic
- ❌ Do NOT modify SignalRanker, CandidateSelector, or any scoring logic
- ❌ Do NOT add new indicators to indicators.py (use existing: RSI, SMA, BB, MACD, crossed_above/below, volume SMA via existing SMA function)
- ❌ Do NOT modify ensemble.py or matrix_runner.py (they handle new strategies automatically via registry)

---

## 7. Implementation Order

1. Fix `rsi_trend_filter_signal` — exit logic change + exit_neutral parameter
2. Update `rsi_trend_filter` param grid in `main.py`
3. Create `rsi_bb_convergence.py` — new strategy file
4. Create `macd_volume.py` — new strategy file (note: needs df access for volume)
5. Update `__init__.py` files for strategy registration
6. Update `main.py::REOPTIMIZE_STRATEGIES` and `REOPTIMIZE_PARAM_GRIDS`
7. Write tests (in `tests/test_strategy.py`)
8. Run tests to verify
9. Update trajectory and CODEBUDDY.md
