# Iteration #15 Spec — Multi-Factor Strategy Exploration (Round 2)

> **Date**: 2026-07-08
> **Type**: New Indicator + New Multi-Factor Strategies + Reoptimize
> **Risk**: Low (only modifies strategy layer + indicators)

---

## 1. Background

Iter #14 added 2 multi-factor strategies (rsi_bb_convergence, macd_volume) and fixed rsi_trend_filter. Strategy pool is now 7 strategies. However:

1. **Missing trend strength indicator**: No ADX (Average Directional Index) — the standard measure of whether a market is trending or ranging
2. **No momentum strategy**: All 7 strategies are either trend-following or mean-reversion. Momentum is a missing alpha source (Constitution L3: Hybrid system)
3. **No pure breakout strategy**: Bollinger Band is mean-reversion, not breakout. No strategy captures volatility breakouts
4. **Reoptimize needed**: No `--reoptimize` has been run since Iter #14. Need actual numbers to evaluate multi-factor strategies

## 2. Problem Statement

### Problem A: No ADX indicator

ADX quantifies trend strength (0-100). Values > 25 indicate a trending market (favorable for trend-following strategies), values < 20 indicate a ranging market (favorable for mean-reversion). This is a standard filter that no existing strategy uses.

### Problem B: No momentum strategy

Momentum (buy winners, sell losers) is a foundational alpha source. Rate-of-Change (RoC) is a simple, interpretable momentum measure using only close prices.

### Problem C: Need reoptimize to evaluate

The current `strategy_weights.json` has only 2/6 groups active. We need a fresh reoptimize to see if the new multi-factor strategies improve coverage and performance.

## 3. Design

### 3A. Add ADX to `indicators.py`

**File**: `mytrader/strategy/indicators.py`

ADX is calculated as:
1. True Range (TR) = max(high-low, |high-prev_close|, |low-prev_close|)
2. +DM = high - prev_high (if positive and > -DM, else 0)
3. -DM = prev_low - low (if positive and > +DM, else 0)
4. +DI = 100 * EMA(+DM, period) / ATR(period)
5. -DI = 100 * EMA(-DM, period) / ATR(period)
6. DX = 100 * |+DI - -DI| / (+DI + -DI)
7. ADX = EMA(DX, period)

We'll implement it using pandas-ta which already has ADX built-in.

```python
def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Average Directional Index (ADX).
    
    ADX > 25: strong trend
    ADX < 20: weak/ranging market
    
    Args:
        high:   最高价 Series
        low:    最低价 Series
        close:  收盘价 Series
        period: 计算周期（默认 14）
    
    Returns:
        ADX Series (0-100)
    """
    import pandas_ta as ta
    adx_df = ta.adx(high=high, low=low, close=close, length=period)
    return adx_df[f"ADX_{period}"]
```

### 3B. New Strategy: `adx_trend` — ADX Trend Strength + EMA Crossover

**File**: `mytrader/strategy/strategies/adx_trend.py` (new)

**Design**:
- Only trade when ADX > threshold (trending market)
- BUY: fast EMA crosses above slow EMA AND ADX > adx_threshold
- SELL: fast EMA crosses below slow EMA OR ADX drops below exit_threshold

```python
@register_strategy("adx_trend")
def adx_trend_signal(
    close: pd.Series,
    fast: int = 10,
    slow: int = 30,
    adx_period: int = 14,
    adx_threshold: float = 25.0,
    exit_threshold: float = 20.0,
    df: pd.DataFrame | None = None,
) -> pd.Series:
    """
    ADX + EMA Crossover trend following.
    
    BUY:  fast EMA > slow EMA AND ADX > adx_threshold (trending up)
    SELL: fast EMA < slow EMA OR ADX < exit_threshold (trend weakening)
    """
    fast_ema = ema(close, fast)
    slow_ema = ema(close, slow)
    
    buy_signal = (fast_ema > slow_ema) & (fast_ema.shift(1) <= slow_ema.shift(1))
    sell_cross = (fast_ema < slow_ema) & (fast_ema.shift(1) >= slow_ema.shift(1))
    
    if df is not None and all(c in df.columns for c in ["high", "low"]):
        adx_series = adx(df["high"], df["low"], close, period=adx_period)
        # ADX confirmation for entry
        buy_signal = buy_signal & (adx_series > adx_threshold)
        # ADX weak exit (trend fading → exit regardless of crossover)
        sell_adx = adx_series < exit_threshold
        sell_signal = sell_cross | sell_adx
    else:
        sell_signal = sell_cross
    
    signal = pd.Series(0, index=close.index, dtype=int)
    signal[buy_signal] = 1
    signal[sell_signal] = -1
    
    return signal.shift(1).fillna(0).astype(int)
```

### 3C. New Strategy: `momentum_roc` — Rate of Change Momentum

**File**: `mytrader/strategy/strategies/momentum_roc.py` (new)

**Design**:
- Uses Rate of Change (RoC) to measure momentum strength
- BUY: RoC > buy_threshold AND close > SMA(trend_period) → strong upward momentum in uptrend
- SELL: RoC < sell_threshold OR close < SMA(trend_period) → momentum fading or trend broken

```python
@register_strategy("momentum_roc")
def momentum_roc_signal(
    close: pd.Series,
    roc_period: int = 20,
    buy_threshold: float = 5.0,
    sell_threshold: float = -3.0,
    trend_period: int = 200,
) -> pd.Series:
    """
    Rate of Change momentum strategy.
    
    BUY:  RoC > buy_threshold AND close > SMA(trend) → momentum in uptrend
    SELL: RoC < sell_threshold OR close < SMA(trend) → momentum lost or trend broken
    """
    roc = (close - close.shift(roc_period)) / close.shift(roc_period) * 100
    trend_ma = sma(close, trend_period)
    
    above_trend = close > trend_ma
    below_trend = close < trend_ma
    
    buy_signal = (roc > buy_threshold) & above_trend
    sell_roc = roc < sell_threshold
    sell_trend = below_trend
    
    signal = pd.Series(0, index=close.index, dtype=int)
    signal[buy_signal] = 1
    signal[sell_roc | sell_trend] = -1
    
    return signal.shift(1).fillna(0).astype(int)
```

### 3D. `main.py` Integration

**REOPTIMIZE_STRATEGIES**: Add `"adx_trend"` and `"momentum_roc"` (total: 7 → 9 strategies)

**REOPTIMIZE_PARAM_GRIDS**: Add grids:
- `adx_trend`: fast(2) × slow(2) × adx_period(2) × adx_threshold(2) = 16 combinations
  - fast: [10, 20]
  - slow: [30, 50]
  - adx_period: [14, 21]
  - adx_threshold: [20, 25]
  - exit_threshold: fixed 20
- `momentum_roc`: roc_period(2) × buy_threshold(2) × sell_threshold(2) = 8 combinations
  - roc_period: [10, 20]
  - buy_threshold: [3, 5]
  - sell_threshold: [-5, -3]
  - trend_period: fixed 200

### 3E. Strategy Registration

Update `__init__.py` to import `adx_trend` and `momentum_roc` modules.

## 4. Test Plan

### Tests for ADX indicator

1. `test_adx_basic` — ADX returns Series of same length, values in [0, 100]
2. `test_adx_trending_vs_ranging` — Trending data → ADX > 25; ranging → ADX < 25
3. `test_adx_custom_period` — Different period parameters work
4. `test_adx_insufficient_data` — Data < period returns NaN/doesn't crash

### Tests for adx_trend strategy

5. `test_adx_trend_buy_signal` — EMA cross + ADX > threshold → BUY
6. `test_adx_trend_no_buy_without_adx` — EMA cross but ADX < threshold → no BUY
7. `test_adx_trend_sell_cross` — EMA crossunder → SELL
8. `test_adx_trend_sell_adx_weak` — ADX < exit_threshold → SELL even without cross
9. `test_adx_trend_no_df_graceful` — df=None → graceful degradation (EMA only)
10. `test_adx_trend_signal_range` — signal values in {-1, 0, 1}
11. `test_adx_trend_no_lookahead` — uses shift(1)

### Tests for momentum_roc strategy

12. `test_momentum_roc_buy_signal` — RoC > buy_threshold + above trend → BUY
13. `test_momentum_roc_sell_roc` — RoC < sell_threshold → SELL
14. `test_momentum_roc_sell_trend` — close < SMA → SELL (trend broken)
15. `test_momentum_roc_no_signal_weak` — RoC between thresholds → HOLD
16. `test_momentum_roc_signal_range` — values in {-1, 0, 1}
17. `test_momentum_roc_no_lookahead` — uses shift(1)

### Registration tests

18. `test_all_strategies_registered` — update expected set
19. `test_new_strategies_in_reoptimize_constants` — verify REOPTIMIZE includes new strategies

**Total new tests**: ~19

## 5. Success Criteria

| # | Criterion | Verification |
|---|-----------|-------------|
| 1 | ADX indicator added and working | Unit tests 1-4 |
| 2 | adx_trend strategy produces trend-filtered signals | Unit tests 5-11 |
| 3 | momentum_roc strategy produces RoC-based signals | Unit tests 12-17 |
| 4 | All existing tests still pass | `pytest --ignore=tests/test_integration_live.py` |
| 5 | 9 strategies registered | test_all_strategies_registered |
| 6 | No risk/execution changes | `git diff --stat` |
| 7 | `--reoptimize` completes successfully | Run full reoptimize, verify weights.json |

## 6. Scope Boundary

- ❌ Do NOT modify risk/execution/portfolio/matrix_backtest modules
- ❌ Do NOT modify existing strategies (rsi_trend_filter, macd_volume, etc.)
- ❌ Do NOT change scoring/ranking logic
- ✅ Add ADX to indicators.py (new indicator, not modifying existing ones)
- ✅ Add 2 new strategy files

## 7. Implementation Order

1. Add ADX to `indicators.py`
2. Create `adx_trend.py` strategy
3. Create `momentum_roc.py` strategy
4. Update `__init__.py` for registration
5. Update `main.py::REOPTIMIZE_STRATEGIES` and `REOPTIMIZE_PARAM_GRIDS`
6. Write tests (~19 new tests)
7. Run tests
8. Run `--reoptimize` to evaluate all 9 strategies
9. Update trajectory + CODEBUDDY
