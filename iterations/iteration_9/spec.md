# Iteration #9 Spec — MatrixBacktest Alpha-Based Strategy Selection

> 日期：2026-07-05
> Meta-Agent：GLM
> 输入依据：Iter #7 reoptimize（alpha=-11.34%）、Iter #8（rsi_trend_filter 未进入权重）、用户确认目标不变（年化 20-30%）
> 风险等级：中（修改策略选择逻辑，不修改策略代码/风控/执行）
> 核心目标：将 MatrixBacktest 的 top-K 策略选择从 Sortino 排序改为 Alpha 排序，使选出的策略直接优化超额收益

---

## 1. 背景

Iter #7 的 reoptimize 暴露了根本矛盾：

```
Constitution 目标：年化 20-30%（需要 alpha +10~20%）
MatrixBacktest 排序：Sortino 降序
结果：选出 Sortino 最高的均值回归策略 → 年化 8.02% → alpha = -11.34%
```

**Sortino 高 ≠ 年化高。** 均值回归策略天然有高 Sortino（低下行波动）但低绝对收益。用 Sortino 排序会系统性地排除能跑赢 SPY 的趋势策略。

Iter #8 新增的 `rsi_trend_filter` 也因此未能进入权重——它的 Sortino 低于纯 `rsi_mean_revert`。

---

## 2. Problem Statement

### 当前代码流程（`matrix_backtest.py::_run_group`）

1. **Per-strategy best params**：按 **Sharpe** 选每个策略的最优参数（line 785）
2. **Top-K selection**：DD ≤ 20% 过滤 → 按 **Sortino** 降序取 top-K（line 830-833）
3. **Ensemble weights**：按 **Sharpe** 归一化为权重（line 394）

### 问题

- Top-K 用 Sortino 排序 → 永远选均值回归 → alpha 为负
- Per-strategy 用 Sharpe 选 params → 也偏好低波动 → 进一步偏向均值回归

### 解决方案

将 top-K 排序从 Sortino 改为 **Alpha**（策略年化收益 - SPY 同期年化收益）：
- DD ≤ 20%：硬约束过滤（不变）
- Sortino > 0.5：最低质量门槛（新增，排除垃圾策略）
- **Alpha 降序**：排序指标（替换 Sortino）
- Per-strategy best params：从 Sharpe 改为 Alpha（可选，建议同步改）

---

## 3. Scope

### 本次要做

1. 在 MatrixBacktest 中新增 SPY benchmark 数据获取和 alpha 计算
2. 将 `_run_group` 的 top-K 排序从 Sortino 改为 Alpha
3. 新增 Sortino > 0.5 作为最低质量过滤
4. 在 `GroupBacktestResult` 和 `strategy_weights.json` 中新增 `backtest_alpha` 字段
5. 将 per-strategy best params 选择从 Sharpe 改为 Alpha（保持一致性）
6. 将 ensemble weights 计算从 Sharpe 改为 Alpha
7. 新增/更新测试
8. 更新设计文档和 trajectory

### 本次不做

1. 不修改任何策略代码（5 个策略文件不动）
2. 不修改 SignalRanker / CandidateSelector / RiskManager
3. 不修改 DD 阈值 / 仓位上限 / 止损止盈
4. 不修改 AlpacaBroker / 下单逻辑
5. 不运行 `--reoptimize`（由 Meta-Agent 验收时独立运行）
6. 不触发真实交易

---

## 4. Detailed Design

## 4.1 SPY Benchmark 数据获取

### 新增方法

在 `MatrixBacktest` 类中新增：

```python
def _get_spy_returns(self, start: date, end: date) -> pd.Series | None:
    """获取 SPY 同期日收益率序列，用于计算 alpha。
    
    从 MarketDataStore 拉取 SPY 日线数据，计算日收益率。
    如果 SPY 数据不可用，返回 None（alpha 降级为 0）。
    """
    try:
        spy_bars = self._store.get_bars_multi(["SPY"], start, end)
        spy_df = spy_bars.get("SPY")
        if spy_df is None or spy_df.empty:
            logger.warning("[MatrixBacktest] SPY data unavailable, alpha will be 0")
            return None
        spy_close = spy_df["close"].astype(float)
        return spy_close.pct_change().dropna()
    except Exception as e:
        logger.warning(f"[MatrixBacktest] SPY benchmark fetch failed: {e}")
        return None
```

### Alpha 计算

```python
def _compute_alpha(
    strategy_daily_returns: pd.Series,
    spy_daily_returns: pd.Series | None,
) -> float:
    """计算 alpha = 策略年化收益 - SPY 年化收益。
    
    如果 SPY 数据不可用，返回 0.0（降级）。
    """
    if spy_daily_returns is None or spy_daily_returns.empty:
        return 0.0
    
    # 对齐时间索引
    aligned = pd.concat([strategy_daily_returns, spy_daily_returns], 
                        axis=1, join="inner").dropna()
    if aligned.empty:
        return 0.0
    
    strat_returns = aligned.iloc[:, 0]
    spy_returns = aligned.iloc[:, 1]
    
    # 年化收益 = (1 + mean_daily)^252 - 1
    strat_annual = (1 + strat_returns.mean()) ** 252 - 1
    spy_annual = (1 + spy_returns.mean()) ** 252 - 1
    
    return (strat_annual - spy_annual) * 100  # 百分数
```

## 4.2 Top-K 选择逻辑修改

### 当前代码（line 818-857）

```python
# 当前：DD 过滤 → Sortino 降序
compliant = [c for c in candidates if c[4] <= MAX_PORTFOLIO_DRAWDOWN_PCT]
if compliant:
    ranked = sorted(compliant, key=lambda x: x[3], reverse=True)  # x[3] = Sortino
```

### 修改后

```python
# 新增：Sortino 最低质量门槛
MIN_SORTINO_THRESHOLD = 0.5

# 修改：DD 过滤 + Sortino 门槛 → Alpha 降序
candidates_with_alpha = []
for (strategy, params, results, pso, pdd) in candidates:
    alpha = _compute_alpha(
        _combine_daily_returns(results),
        spy_returns,
    )
    candidates_with_alpha.append((strategy, params, results, pso, pdd, alpha))

# 两级过滤：DD ≤ 20% AND Sortino > 0.5
compliant = [
    c for c in candidates_with_alpha
    if c[4] <= MAX_PORTFOLIO_DRAWDOWN_PCT and c[3] > MIN_SORTINO_THRESHOLD
]

if compliant:
    # Alpha 降序取 top-K
    ranked = sorted(compliant, key=lambda x: x[5], reverse=True)  # x[5] = alpha
    dd_constrained = False
else:
    # Fallback 1: 放宽 Sortino 门槛，只保留 DD 约束
    dd_compliant = [c for c in candidates_with_alpha if c[4] <= MAX_PORTFOLIO_DRAWDOWN_PCT]
    if dd_compliant:
        ranked = sorted(dd_compliant, key=lambda x: x[5], reverse=True)
        dd_constrained = False
        logger.warning(f"[MatrixBacktest] {group_id}: Sortino filter relaxed (no candidate passed Sortino > {MIN_SORTINO_THRESHOLD})")
    else:
        # Fallback 2: 无 DD 合规候选 → 按 DD 升序（保持现有逻辑）
        ranked = sorted(candidates_with_alpha, key=lambda x: x[4])
        dd_constrained = True
```

## 4.3 Per-Strategy Best Params 修改

### 当前代码（line 785）

```python
if ps > best_sharpe:  # 用 Sharpe 选 best params
    best_sharpe = ps
```

### 修改后

```python
alpha = _compute_alpha(
    _combine_daily_returns(results),
    spy_returns,
)
if alpha > best_alpha:  # 用 Alpha 选 best params
    best_alpha = alpha
```

## 4.4 Ensemble Weights 修改

### 当前代码（line 390-398）

```python
sharpes = []
for strategy, params, results in group_results:
    ps = _portfolio_sharpe_from_results(results)
    sharpes.append(max(ps, 0.01))
total = sum(sharpes)
weights = [s / total for s in sharpes]
```

### 修改后

```python
alphas = []
for strategy, params, results in group_results:
    alpha = _compute_alpha(_combine_daily_returns(results), spy_returns)
    alphas.append(max(alpha, 0.01))  # 避免负权重
total = sum(alphas)
weights = [a / total for a in alphas]
```

## 4.5 新增字段

### GroupBacktestResult

```python
@dataclass
class GroupBacktestResult:
    # ... 现有字段 ...
    backtest_alpha: float = 0.0  # 新增：alpha vs SPY（百分数）
```

### strategy_weights.json

每个权重条目新增：

```json
{
    "strategy": "rsi_mean_revert",
    "params": {...},
    "weight": 0.5,
    "backtest_sharpe": 1.03,
    "backtest_sortino": 1.61,
    "backtest_max_drawdown": 1.78,
    "backtest_win_rate": 0.50,
    "backtest_alpha": 2.35,  // ← 新增
    "dd_constrained": false,
    "backtest_dd_status": "pass"
}
```

---

## 5. 测试计划

### 新增测试文件或扩展现有测试

1. **test_compute_alpha_basic**：构造已知策略收益和 SPY 收益，验证 alpha 计算正确
2. **test_compute_alpha_spy_unavailable**：SPY 数据为 None → alpha = 0.0
3. **test_top_k_selection_uses_alpha**：构造 2 个候选，A 的 Sortino 高但 alpha 低，B 的 Sortino 低但 alpha 高 → B 应被选中
4. **test_sortino_filter_excludes_garbage**：Sortino < 0.5 的候选被过滤
5. **test_dd_filter_still_applies**：DD > 20% 的候选被过滤（不因 alpha 高而通过）
6. **test_fallback_when_no_sortino_compliant**：所有候选 Sortino < 0.5 → 放宽 Sortino 门槛
7. **test_fallback_when_no_dd_compliant**：所有候选 DD > 20% → 按 DD 升序（保持现有逻辑）
8. **test_alpha_field_in_weights_json**：输出的 JSON 包含 `backtest_alpha` 字段
9. **test_per_strategy_best_params_uses_alpha**：验证 params 选择从 Sharpe 改为 Alpha

---

## 6. Success Criteria

1. `_run_group` 的 top-K 排序使用 Alpha（非 Sortino）
2. DD ≤ 20% 硬约束保留
3. Sortino > 0.5 最低质量门槛新增
4. `strategy_weights.json` 每条目包含 `backtest_alpha` 字段
5. SPY 数据不可用时 alpha 降级为 0（不崩溃）
6. 默认 pytest 通过（585+ 测试，0 failed）
7. 新增测试 ≥ 8 个
8. 不修改策略代码 / 风控 / 执行逻辑
9. 更新 trajectory / design docs / CODEBUDDY

---

## 7. Implementation Order

1. 读 spec + `matrix_backtest.py` + `portfolio_backtest.py`（参考 benchmark 实现）+ `experience.md`
2. 实现 `_get_spy_returns()` 和 `_compute_alpha()`
3. 修改 `_run_group`：top-K 排序从 Sortino → Alpha + Sortino 门槛
4. 修改 per-strategy best params：Sharpe → Alpha
5. 修改 `_optimize_ensemble_weights`：Sharpe → Alpha
6. 在 `GroupBacktestResult` 和 weights JSON 中新增 `backtest_alpha`
7. 新增/更新测试
8. 运行 targeted tests + 默认 pytest
9. 更新 `designs/design_v2/07-backtest-module.md` + trajectory + CODEBUDDY

---

## 8. Risk Classification

- **中风险**：修改策略选择逻辑会改变 `strategy_weights.json` 输出，影响后续 PortfolioBacktest 和实盘
- **低风险**：SPY 数据获取是只读操作，不影响交易
- **不触及**：策略代码 / risk / execution / portfolio 模块
- **Constitution 合规**：Alpha 作为排序指标不违反 L1（Sortino 仍是 KPI，只是从排序变成过滤）；DD 硬约束不变
