# Iteration #8 — Trend-Filtered Mean Reversion 策略

> 日期：2026-07-04
> 类型：策略新增
> 状态：implemented

## 1. 目标

新增 **RSI Trend Filter** 策略（`rsi_trend_filter`），在经典 RSI 均值回归信号上叠加 200 日 SMA 趋势过滤，降低单边趋势中的逆势假信号风险。

## 2. 策略设计

### 信号规则

| 条件 | 信号 |
|------|------|
| RSI < oversold **AND** close > SMA(200) | BUY (+1) — 上升趋势中的超卖 |
| RSI > overbought **AND** close < SMA(200) | SELL (-1) — 下降趋势中的超买 |
| 其他 | HOLD (0) |

### 设计原则

- RSI 均值回归在震荡市有效，但在单边趋势中会频繁逆势交易
- 通过 200 日 SMA 趋势过滤：只有上升趋势中才做多超卖反弹，下降趋势中才做空超买回落
- 严格 `shift(1)` 防前视偏差（同所有现有策略）

### 参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `rsi_period` | 14 | RSI 计算周期 |
| `oversold` | 30.0 | 超卖阈值 |
| `overbought` | 70.0 | 超买阈值 |
| `trend_period` | 200 | SMA 趋势过滤周期 |

## 3. 实现清单

### 3.1 新增文件

- `mytrader/strategy/strategies/rsi_trend_filter.py` — 策略函数，`@register_strategy("rsi_trend_filter")`

### 3.2 修改文件

- `main.py` — `REOPTIMIZE_STRATEGIES` 新增 `"rsi_trend_filter"`，`REOPTIMIZE_PARAM_GRIDS` 新增参数网格
- `tests/test_strategy.py` — 新增测试类 `TestRSITrendFilter`

### 3.3 文档更新

- `alignment/iteration_trajectory.md` — 记录迭代 #8
- `.codebuddy/CODEBUDDY.md` — 更新策略列表 + 开发阶段 + 测试数

## 4. 参数网格（MatrixBacktest）

```python
"rsi_trend_filter": {
    "rsi_period": [7, 14, 21],
    "oversold": [25, 30, 35],
    "overbought": [65, 70, 75],
    "trend_period": [200],
}
```

说明：`trend_period` 固定为 200（经典长周期趋势线），不纳入网格搜索以控制搜索空间。

## 5. 测试要求

- 信号值域测试（`{ -1, 0, 1 }`）
- 自定义参数测试
- 前视偏差测试（通过 `TestNoLookaheadBias` 参数化自动覆盖）
- 注册表测试（通过 `TestAllStrategiesQuality` 参数化自动覆盖）
- 趋势过滤行为测试：上升趋势中不产生 SELL，下降趋势中不产生 BUY
- 边界条件测试：数据不足 `trend_period` 条时的行为

## 6. Scope

- 仅新增策略，不修改现有策略/风控/执行逻辑
- 不触发真实交易
- 策略函数为纯函数（无副作用）
