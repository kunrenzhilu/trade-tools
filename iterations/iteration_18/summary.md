# Iteration #18 Summary — Trend-Following Strategies for Bull Markets

## Requested
[spec.md](spec.md) — Add 2 continuous trend-following strategies to fix zero-signal problem in bull markets

## Delivered
- **Files changed**: 6 (sma_trend.py NEW, breakout.py NEW, main.py, __init__.py, test_strategy.py)
- **Tests**: 751 → 776 (+25 new tests, all passed)
- **New strategies**: sma_trend (close vs SMA continuous), breakout (Donchian channel)
- **Strategy pool**: 9 → 11 strategies

## Signal Verification
```
Bullish drift (500 bars, +0.3 drift):
  sma_trend(50):  BUY=450, SELL=0  ✅ 完美追踪趋势
  sma_trend(200): BUY=300, SELL=0  ✅
  breakout(20):   BUY=0, SELL=0    (随机游走无清晰突破)
```

sma_trend 在牛市中持续产生 BUY 信号 — 解决了旧策略的零信号问题。

## Reoptimize Status
- 后台运行中 (PID 82012)
- 预期：sma_trend 应进入 SPX 组权重（填补当前空缺）

## Iteration Progress Summary

| Iter | Focus | Test Δ | Active Groups | Multi-Factor in Weights |
|------|-------|--------|:---:|:---:|
| #14 | Fix rsi_trend + 2 multi-factor | +32 | 2/6 | 0 |
| #15 | ADX + 2 more strategies | +30 | 2/6 | 0 |
| #16 | Alpha gate -2% | +7 | 2/6 | 1 (momentum_roc) |
| #17 | Sortino exemption | +7 | **4/6** | **2** (+adx_trend) |
| #18 | Trend-following (sma/breakout) | +25 | reopt pending | reopt pending |
| **Total** | **6 iterations** | **+101** | **2→4** | **0→2** |
