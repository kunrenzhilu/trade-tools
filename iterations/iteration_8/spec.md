# Iteration #8 Spec — Trend-Filtered Mean Reversion Strategy

> 日期：2026-07-04  
> Meta-Agent：GLM  
> 输入依据：Iter #7 reoptimize 结果（alpha=-11.34%, SPY return=19.36% vs 策略 8.02%）、`mytrader/mytrader/strategy/strategies/`、`ideas.md`（海龟交易法 + 多因子）、`alignment/ai_constitution.md` L1  
> 风险等级：低（新增策略，不修改现有策略/风控/执行逻辑）  
> 核心目标：增加趋势过滤的均值回归策略，在保持震荡市 Sortino 的同时避免趋势市逆势亏损

---

## 1. 背景

Iter #7 reoptimize 暴露了根本问题：

| 指标 | 策略 | SPY | Gap |
|------|------|-----|-----|
| Annual Return | 8.02% | 19.36% | **-11.34%** |
| Sortino | 1.03 | — | < 2.0 目标 |
| Alpha | -11.34% | — | **负 alpha** |
| IR | -0.87 | — | **策略在摧毁价值** |

原因分析：
1. **4 个策略全是单指标单信号**：rsi_mean_revert / bollinger_band（均值回归）+ dual_ma / macd_cross（趋势跟踪）
2. **均值回归主导**：最终权重中 rsi + bollinger 占 >80%，在趋势市（如 2025-2026 美股牛市）逆势亏损
3. **趋势策略缺席**：dual_ma / macd_cross 的 Sortino 在大多数组中低于均值回归，无法进入最终权重
4. **无 regime detection**：系统不知道当前是趋势市还是震荡市，无法切换策略

## 2. Problem Statement

### P0：均值回归策略在趋势市亏损

当前 rsi_mean_revert 在 RSI < 30 时买入，但如果市场处于强趋势中，RSI 可以长期处于超卖区域，导致连续逆势买入。

**解决方案**：新增 `rsi_trend_filter` 策略——RSI 均值回归 + 200 日 SMA 趋势过滤：
- 仅当价格 > 200 日 SMA（长期上升趋势）时，才接受 RSI 超卖买入信号
- 仅当价格 < 200 日 SMA（长期下降趋势）时，才接受 RSI 超买卖出信号
- 在趋势不明朗时（价格接近 200 日 SMA）减少交易

这保持了均值回归的高 Sortino（震荡市有效），同时避免在趋势市中逆势（降低 DD 和负 alpha）。

---

## 3. Scope

### 本次要做

1. 新增策略文件 `mytrader/mytrader/strategy/strategies/rsi_trend_filter.py`
2. 在 `mytrader/main.py` 的 `REOPTIMIZE_STRATEGIES` 和 `REOPTIMIZE_PARAM_GRIDS` 中注册新策略
3. 在 `mytrader/mytrader/strategy/matrix_runner.py` 中确保新策略被正确加载（如有注册机制依赖）
4. 新增测试 `mytrader/tests/test_strategy_rsi_trend_filter.py`
5. 更新设计文档 `mytrader/designs/design_v2/02-strategy-engine.md`
6. 更新 trajectory / CODEBUDDY

### 本次不做

1. 不修改现有 4 个策略的任何代码
2. 不修改 SignalRanker / CandidateSelector / RiskManager
3. 不修改 DD 阈值 / 仓位上限 / 止损止盈
4. 不运行 `--reoptimize`（由 Meta-Agent 在验收阶段独立运行）
5. 不触发真实交易

---

## 4. Detailed Design

## 4.1 策略实现

### 文件：`mytrader/mytrader/strategy/strategies/rsi_trend_filter.py`

```python
"""RSI 均值回归 + 趋势过滤策略。

信号规则：
    - 价格 > SMA(trend_period) 且 RSI < oversold → BUY  (+1)
      （长期上升趋势中的超卖反弹）
    - 价格 < SMA(trend_period) 且 RSI > overbought → SELL  (-1)
      （长期下降趋势中的超买回落）
    - 否则 → HOLD  (0)

设计理由：
    纯均值回归在趋势市中逆势亏损（Iter #7 alpha=-11.34%）。
    加入 200 日 SMA 过滤后，只在长期趋势方向上做均值回归，
    避免在熊市中抄底、在牛市中逃顶。

适用场景：
    - 震荡市：与纯 RSI 策略表现接近（趋势过滤不频繁触发）
    - 趋势市：显著减少逆势交易（核心改进点）
"""
```

### 函数签名

```python
@register_strategy("rsi_trend_filter")
def rsi_trend_filter_signal(
    close: pd.Series,
    period: int = 14,
    oversold: float = 30.0,
    overbought: float = 70.0,
    trend_period: int = 200,
) -> pd.Series:
    """RSI 均值回归 + SMA 趋势过滤信号。

    Args:
        close:        收盘价 Series
        period:       RSI 计算周期（默认 14）
        oversold:     RSI 超卖阈值（默认 30）
        overbought:   RSI 超买阈值（默认 70）
        trend_period: 长期趋势 SMA 周期（默认 200）

    Returns:
        信号 Series：1=BUY, -1=SELL, 0=HOLD
    """
```

### 信号逻辑

```python
rsi_values = rsi(close, period)
trend_sma = sma(close, trend_period)

signal = pd.Series(0, index=close.index, dtype=int)

# BUY: 价格在 SMA 之上（上升趋势）+ RSI 超卖
uptrend = close > trend_sma
downtrend = close < trend_sma

signal[(uptrend) & (rsi_values < oversold)] = 1    # 上升趋势中的超卖反弹
signal[(downtrend) & (rsi_values > overbought)] = -1  # 下降趋势中的超买回落

# shift(1) 避免前视偏差
return signal.shift(1).fillna(0).astype(int)
```

### 关键设计决策

1. **只用 SMA 方向，不用 SMA 斜率**：斜率判断会增加参数和过拟合风险，方向已足够
2. **trend_period=200 是业界标准**：200 日 SMA 是最常用的长期趋势指标，不需要调参
3. **BUY 和 SELL 不对称**：
   - BUY = 上升趋势 + RSI 超卖（顺势抄底）
   - SELL = 下降趋势 + RSI 超买（顺势逃顶）
   - 不做"上升趋势 + RSI 超买"的 SELL（可能在牛市中过早卖出）
4. **trend_period 前期数据不足时**：SMA 为 NaN，`close > NaN` 为 False，不产生信号（安全降级）

---

## 4.2 参数网格

### 在 `main.py` 中注册

```python
REOPTIMIZE_STRATEGIES = ["dual_ma", "rsi_mean_revert", "macd_cross", "bollinger_band", "rsi_trend_filter"]

REOPTIMIZE_PARAM_GRIDS = {
    # ... 现有 4 个策略不变 ...
    "rsi_trend_filter": [
        {"period": 14, "oversold": 25, "overbought": 65, "trend_period": 200},
        {"period": 14, "oversold": 25, "overbought": 70, "trend_period": 200},
        {"period": 14, "oversold": 30, "overbought": 65, "trend_period": 200},
        {"period": 14, "oversold": 30, "overbought": 70, "trend_period": 200},
        {"period": 14, "oversold": 30, "overbought": 75, "trend_period": 200},
        {"period": 14, "oversold": 35, "overbought": 65, "trend_period": 200},
        {"period": 14, "oversold": 35, "overbought": 70, "trend_period": 200},
        {"period": 14, "oversold": 35, "overbought": 75, "trend_period": 200},
        {"period": 21, "oversold": 25, "overbought": 65, "trend_period": 200},
        {"period": 21, "oversold": 25, "overbought": 70, "trend_period": 200},
        {"period": 21, "oversold": 30, "overbought": 65, "trend_period": 200},
        {"period": 21, "oversold": 30, "overbought": 70, "trend_period": 200},
        {"period": 21, "oversold": 30, "overbought": 75, "trend_period": 200},
        {"period": 21, "oversold": 35, "overbought": 65, "trend_period": 200},
        {"period": 21, "oversold": 35, "overbought": 70, "trend_period": 200},
        {"period": 21, "oversold": 35, "overbought": 75, "trend_period": 200},
    ],
}
```

设计理由：
- `trend_period` 固定为 200（业界标准，不调参）
- `period` / `oversold` / `overbought` 与 rsi_mean_revert 的参数网格一致（便于对比）
- 16 个组合（2 period × 3 oversold × 3 overbought ≈ 18，去掉极端组合 = 16）

---

## 4.3 测试计划

### 文件：`mytrader/tests/test_strategy_rsi_trend_filter.py`

至少覆盖：

1. **test_buy_signal_in_uptrend_oversold**：构造价格 > SMA200 + RSI < 30 → BUY
2. **test_sell_signal_in_downtrend_overbought**：构造价格 < SMA200 + RSI > 70 → SELL
3. **test_no_buy_in_downtrend_oversold**：价格 < SMA200 + RSI < 30 → HOLD（不逆势抄底）
4. **test_no_sell_in_uptrend_overbought**：价格 > SMA200 + RSI > 70 → HOLD（不在牛市中逃顶）
5. **test_hold_when_no_clear_trend**：价格 ≈ SMA200 → HOLD
6. **test_shift_prevents_lookahead**：信号 shift(1)，当日信号用昨日数据
7. **test_insufficient_data_returns_hold**：数据 < 200 天 → 全部 HOLD（SMA200 为 NaN）
8. **test_registered_in_registry**：`@register_strategy("rsi_trend_filter")` 正确注册
9. **test_param_sweep**：不同 period/oversold/overbought 组合都能运行不报错

---

## 5. Success Criteria

1. `rsi_trend_filter` 策略注册成功，`STRATEGY_REGISTRY` 包含该 key
2. 策略函数是纯函数，包含 `shift(1)`，无前视偏差
3. 趋势过滤逻辑正确：上升趋势超卖才 BUY，下降趋势超买才 SELL
4. `REOPTIMIZE_PARAM_GRIDS` 包含新策略的参数网格
5. 新增测试 ≥ 8 个，全部通过
6. 默认 pytest 通过（574+ 测试，0 failed）
7. 不修改现有 4 个策略的任何代码
8. 更新 trajectory / design docs / CODEBUDDY

---

## 6. Implementation Order

1. 读 spec + `rsi_mean_revert.py`（参考实现）+ `indicators.py`（rsi/sma 函数）+ `registry.py`
2. 创建 `rsi_trend_filter.py`
3. 创建 `test_strategy_rsi_trend_filter.py`
4. 在 `main.py` 中注册策略和参数网格
5. 运行 targeted tests：`python -m pytest tests/test_strategy_rsi_trend_filter.py -q`
6. 运行默认 pytest：`python -m pytest -q`
7. 更新 `designs/design_v2/02-strategy-engine.md`
8. 更新 trajectory / CODEBUDDY

---

## 7. Risk Classification

- **低风险**：新增策略文件，不修改现有代码
- **Constitution 合规**：纯函数、shift(1)、可解释、无黑箱、无 RL
- **不触及**：risk/execution/portfolio 模块
- **后续验证**：Meta-Agent 在验收阶段运行 `--reoptimize`，观察新策略是否进入最终权重以及 alpha 是否改善
