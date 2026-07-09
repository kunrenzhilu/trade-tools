# Iteration #18 Spec — Trend-Following Strategies for Bull Markets

> **Date**: 2026-07-09
> **Type**: New Strategies (Low Risk)
> **Problem**: Portfolio Backtest 12个月零信号 — 9个策略在牛市中静默

---

## 1. Background

当前 9 个策略中，均值回归占多数（rsi, rsi_trend_filter, rsi_bb_convergence, bollinger_band）。牛市中这些策略不产生信号。趋势策略（dual_ma, macd_cross, adx_trend）是**事件型**（仅在交叉日触发），`signal_valid_bars=3` 延长有限。

需要**持续型顺势策略**：在趋势中保持持仓，趋势反转时才退出。

## 2. Design

### 2A. `sma_trend` — 简单均线趋势跟踪

最简单有效的趋势策略：价格在均线上方就做多，跌破就退出。

```
BUY:  close > SMA(period)  → 在趋势中持续保持 BUY 信号
SELL: close < SMA(period)  → 趋势破位时退出
```

- 连续信号型（非事件型），在趋势中每天产生信号
- 参数网格：period = [50, 100, 200]（短/中/长期趋势线）

### 2B. `breakout` — N日价格通道突破

经典突破策略（Donchian Channel 风格）：突破N日高点做多，跌破N日低点退出。

```
BUY:  close > highest(high, N)  → 突破近期阻力位
SELL: close < lowest(low, N)    → 跌破近期支撑位
```

- 需要 high/low 数据（通过 df= 参数访问）
- 参数网格：period = [20, 50, 100]（短/中/长期突破）
- 无 df 时退化为 close-breakout（close vs close percentile）

### 2C. 参数网格

```
sma_trend:  period=[50, 100, 200]  → 3 组合
breakout:   period=[20, 50, 100]   → 3 组合
```

简单网格，因为这类策略参数少且直观。

### 2D. main.py 集成

REOPTIMIZE_STRATEGIES 从 9 → 11：
```
"sma_trend", "breakout"
```

## 3. Test Plan (~12 测试)

sma_trend: 信号范围、趋势中持续BUY、趋势反转SELL、参数自定义、前视偏差
breakout: 突破BUY、跌破SELL、无df退化、信号范围、前视偏差、自定义参数

## 4. Success Criteria
- 所有测试通过
- --reoptimize 产生权重
- sma_trend 或 breakout 进入至少 1 个 SPX 组权重

## 5. Scope
- ✅ 新建 2 个策略文件
- ✅ 更新 __init__.py + main.py
- ❌ 不改其他策略/indicators/risk/execution
