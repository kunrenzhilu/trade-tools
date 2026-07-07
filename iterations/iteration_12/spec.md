# Iteration #12 Spec — Alpha>0 硬门槛（Reject Negative-Alpha Strategies）

> 日期：2026-07-07
> Meta-Agent：GLM
> 输入依据：`iterations/iteration_11/summary.md`（reoptimize 完整结果）、`tmp/iteration10_audit.md` §5 第 2-3 点、`.codebuddy/notes/experience.md` #8、`mytrader/config/strategy_weights.json`（11 条权重 9 条负 alpha）
> 风险等级：**低**（仅修改 `mytrader/backtest/matrix_backtest.py` 选择器逻辑 + ensemble 权重，不触及 risk/execution/strategy/策略代码）
> 核心目标：在 `_run_group` 的 Tier 1/2/3 排序**之前**，剔除 alpha≤0 的候选（跑不赢 SPY 的策略不应进权重）；全负 alpha 组返回空权重（持仓现金）。同时修 `_optimize_ensemble_weights` 的负 alpha 归一化 bug（`max(alpha, 0.01)` 掩盖坏策略）。

---

## 1. 背景

Iter #11 的健全性门槛成功剔除了退化策略（rsi_trend_filter 从 4/6 组降到 1/6 组），但 reoptimize 完整结果显示：

| 指标 | Iter #7 | Iter #10 | Iter #11 |
|------|---------|----------|----------|
| 年化 | 8.02% | -4.88% | **-1.03%** |
| Sortino | 1.03 | -0.66 | **-0.08** |
| Alpha vs SPY | -11.34% | -25.26% | **-21.41%** |
| WF | 4/4 pass | 4/4 pass | **4/4 pass** |

WF 4/4 全过（Sortino 1.56~2.09，max DD 6.36%），但 PortfolioBacktest 近 1 年 alpha=-21.41%。根因：当前 11 条权重中 **9 条负 alpha**（in-sample），系统正在用 9 个"5 年跑不赢 SPY"的策略组合去交易。

当前 `strategy_weights.json` 的 alpha 分布：

| 组 | 策略 | alpha | 正? |
|----|------|-------|-----|
| SPX_mid_vol | rsi_mean_revert | -5.22 | ❌ |
| SPX_mid_vol | bollinger_band | -6.75 | ❌ |
| SPX_high_vol | rsi_mean_revert | -4.41 | ❌ |
| SPX_high_vol | bollinger_band | -6.11 | ❌ |
| **NDX_high_vol** | **rsi_trend_filter** | **+6.50** | **✅** |
| SPX_low_vol | rsi_mean_revert | -4.49 | ❌ |
| SPX_low_vol | bollinger_band | -6.10 | ❌ |
| **NDX_low_vol** | **rsi_mean_revert** | **+1.58** | **✅** |
| NDX_low_vol | bollinger_band | -1.49 | ❌ |
| NDX_mid_vol | rsi_mean_revert | -2.78 | ❌ |
| NDX_mid_vol | bollinger_band | -7.79 | ❌ |

**关键教训（experience.md #8）**：排序前必须先过硬门槛，顺序为 ① 健全性 → ② 风险(DD) → ③ 正超额(alpha>0) → 最后才排序。Iter #11 补了 ①，本轮补 ③。

---

## 2. Problem Statement

### 当前代码缺陷 1：`_run_group` 无 alpha>0 硬门槛

`matrix_backtest.py::_run_group`（约 line 1219-1284）的 Tier 1/2/3 fallback 允许负 alpha 策略进入权重：

```python
# 当前流程（Iter #11 后）：
# 1. 健全性过滤（Iter #11）→ sane_results
# 2. candidates 构建（含 alpha 计算）
# 3. Tier 1: DD≤20% AND Sortino>0.5 → Alpha 降序
# 4. Tier 2: DD≤20% → Alpha 降序
# 5. Tier 3: 按 DD 升序
# 6. top_results = ranked[:top_k]
# 7. ensemble 权重优化
```

缺失的步骤：在 Tier 1/2/3 **之前**加 alpha>0 硬门槛。没有这一步，alpha=-7.79% 的 bollinger_band 仍能凭"DD 合规 + Sortino>0.5"进入 top-K，然后进权重。

### 当前代码缺陷 2：`_optimize_ensemble_weights` 负 alpha 归一化

`matrix_backtest.py::_optimize_ensemble_weights`（约 line 684-690）：

```python
alphas.append(max(alpha, 0.01))  # 避免负/零权重
```

这把 alpha=-7.79 和 alpha=-1.49 都变成 0.01，然后归一化成 50/50 等权——**审计报告 §5 第 3 点**指出这掩盖了坏策略，把"都不好"变成"等权都要"。

---

## 3. Scope

### 本次要做

1. `GroupBacktestResult` 新增 `no_positive_alpha: bool = False` 字段。
2. `_run_group` 在 candidates 构建后、Tier 1/2/3 之前，插入 alpha>0 硬门槛过滤。
3. 全负 alpha 组返回空权重 + `no_positive_alpha=True` 标记（与 Iter #11 的 `no_valid_strategy` 同模式）。
4. `_optimize_ensemble_weights` 修负 alpha 归一化：负 alpha 策略权重为 0，只有正 alpha 参与归一化。
5. 新增/更新测试。
6. 更新 `designs/design_v2/07-backtest-module.md` + trajectory + decision_log + CODEBUDDY。

### 本次不做（明确排除，留给后续迭代）

1. **不**改 alpha 排序为 OOS/Walk-Forward 验证期 alpha（→ Iter #13，experience.md #7）。
2. **不**加 WF gate alpha 校验（→ Iter #13，审计 §5 第 5-6 点）。
3. **不**修 `rsi_trend_filter` 出场逻辑（独立策略重设计任务）。
4. **不**触及 `mytrader/risk/`、`mytrader/execution/`、任何策略文件、指标文件。
5. **不**改 DD 阈值 / 仓位上限 / 止损止盈。
6. **不**运行 `--reoptimize`（由 Meta-Agent 验收时独立运行）。

---

## 4. Detailed Design

### 4.1 `GroupBacktestResult` 新增字段

`matrix_backtest.py`（约 line 95，`no_valid_strategy` 附近）：

```python
@dataclass
class GroupBacktestResult:
    # ... 现有字段 ...
    backtest_alpha: float = 0.0              # 迭代 #9
    no_valid_strategy: bool = False         # 迭代 #11：全退化空仓
    no_positive_alpha: bool = False         # 迭代 #12：全负 alpha 空仓（hold cash）
```

### 4.2 `_run_group` 集成 alpha>0 硬门槛

在 candidates 构建完成（约 line 1236）、Tier 1 过滤（约 line 1238）**之前**插入：

```python
# 迭代 #12：alpha>0 硬门槛（experience.md #8：正超额是排序前的硬门槛）
# 在 Tier 1/2/3 fallback 之前，剔除 alpha≤0 的候选。
# 理由：跑不赢 SPY 的策略不应进入权重，无论 DD/Sortino 多好。
# 顺序：健全性（Iter #11）→ 风险（DD，Tier 1/2/3）→ 正超额（alpha>0，本步）→ 排序
#
# 注意：这一步在 candidates 构建后、Tier 1 前，确保 Tier 1/2/3 只在正 alpha 候选中进行。
# 如果某组所有候选 alpha≤0，该组空仓（hold cash），不强行选负 alpha 策略。
positive_alpha_candidates = [
    c for c in candidates if c[5] > 0  # c[5] = alpha
]

if not positive_alpha_candidates:
    # 全组 alpha≤0 → 空权重（持仓现金），标记 no_positive_alpha
    alpha_strs = [f"{c[0]}({c[5]:.2f}%)" for c in candidates]
    logger.warning(
        f"[MatrixBacktest] {group_id}: ALL {len(candidates)} candidates have "
        f"alpha <= 0 (cannot beat SPY) — {alpha_strs}. "
        f"Group produces EMPTY weights (hold cash). Marked no_positive_alpha."
    )
    report.warnings.append(
        f"{group_id}: no_positive_alpha (all {len(candidates)} candidates alpha <= 0)"
    )
    # 标记已 append 的 GroupBacktestResult 条目（供审计追溯）
    for gr in report.group_results:
        if gr.group_id == group_id:
            gr.no_positive_alpha = True
    return []

# 后续 Tier 1/2/3 在正 alpha 候选中进行
candidates = positive_alpha_candidates
```

> 注意：Tier 1/2/3 的 `len(candidates)` 日志会反映过滤后的数量。`ranked` 列表从正 alpha 候选中产生，top-K 从中选取。

### 4.3 `_optimize_ensemble_weights` 修负 alpha 归一化

`matrix_backtest.py`（约 line 684-693），将：

```python
# 旧代码（Iter #9）：
alphas = []
for strategy, params, results in group_results:
    combined = _combine_daily_returns(results)
    alpha = _compute_alpha(combined, spy_returns)
    alphas.append(max(alpha, 0.01))  # 避免负/零权重

total = sum(alphas)
weights = [a / total for a in alphas]
```

改为：

```python
# 迭代 #12：负 alpha 策略不参与 ensemble（experience.md #8：负分不能用 max(x, ε) 掩盖）
# 只有正 alpha 的策略参与归一化；负 alpha 策略权重为 0。
# 上游 _run_group 的 alpha>0 门槛应已拦截全负 alpha 情形，
# 这里是防御性设计：即使上游漏过负 alpha，也不会被 max(0.01) 掩盖成等权。
raw_alphas = []
for strategy, params, results in group_results:
    combined = _combine_daily_returns(results)
    alpha = _compute_alpha(combined, spy_returns)
    raw_alphas.append(alpha)

# 负 alpha → 权重 0；正 alpha → 参与归一化
positive_alphas = [max(a, 0.0) for a in raw_alphas]
total = sum(positive_alphas)

if total > 0:
    weights = [a / total for a in positive_alphas]
else:
    # 防御性 fallback：全负 alpha 或全零时等权
    # （上游 alpha>0 门槛应已拦截，此处不应到达）
    n = len(group_results)
    weights = [1.0 / n] * n if n > 0 else []
    logger.warning(
        f"[ensemble_weights] all alphas <= 0 ({raw_alphas}), "
        f"falling back to equal weight. This should not happen if "
        f"alpha>0 gate is active upstream."
    )
```

### 4.4 设计动机与 experience.md #8 的映射

experience.md #8 的完整门槛顺序：

```
① 健全性（closed_trades / win_rate 非退化）    ← Iter #11 已做
② 风险（DD ≤ 20%）                              ← Tier 1/2/3 已做
③ 正超额（alpha > 0）                            ← Iter #12 本轮
④ 排序（Alpha 降序选 top-K）                     ← Iter #9 已做
```

Iter #12 补的是 ③，插在 ② 和 ④ 之间。

---

## 5. 测试计划

新增 `tests/test_alpha_gate.py`（或扩展 `test_matrix_backtest.py`）：

1. **test_positive_alpha_candidates_pass** — 全正 alpha 候选组正常产出权重，`no_positive_alpha=False`。
2. **test_negative_alpha_excluded** — mock candidates 中有正有负 alpha，验证负 alpha 不出现在 weights_list。
3. **test_all_negative_alpha_group_empty** — 全负 alpha 组返回空权重 + `no_positive_alpha=True` + report.warnings 含标记。
4. **test_no_positive_alpha_field_default** — `GroupBacktestResult.no_positive_alpha` 默认 False。
5. **test_ensemble_negative_alpha_zero_weight** — `_optimize_ensemble_weights` 中负 alpha 策略权重为 0。
6. **test_ensemble_all_positive_normalizes** — 全正 alpha 正常归一化（权重和=1.0）。
7. **test_ensemble_mixed_alpha_only_positive_weighted** — 混合 alpha 只正 alpha 参与归一化，负 alpha 权重=0。
8. **test_ensemble_all_negative_fallback_equal** — 全负 alpha 退化为等权 + WARNING（防御性 fallback）。
9. **test_alpha_gate_after_sanity_gate** — 健全性门槛 + alpha>0 门槛协同工作（退化策略先被健全性剔除，负 alpha 策略再被 alpha 门槛剔除）。

### 回归

- 现有 `tests/test_matrix_backtest.py`、`tests/test_batch_backtest.py`、`tests/test_degenerate_filter.py` 全部通过。
- **重要**：现有 mock 测试中 `SingleBacktestResult` 的 `closed_trades` 已在 Iter #11 显式传值。本轮新增 alpha>0 门槛后，mock 的 `_backtest_batch` 返回的 `SingleBacktestResult` 需要有正 alpha 的 daily_returns（否则会被 alpha>0 门槛拦截）。检查 `test_matrix_backtest.py::TestAlphaBasedTopKSelection` 中的 mock 是否需要调整 daily_returns 以产生正 alpha。

---

## 6. Success Criteria

1. `GroupBacktestResult.no_positive_alpha` 字段存在。
2. `_run_group` 在 Tier 1/2/3 之前剔除 alpha≤0 的候选。
3. 全负 alpha 组返回空权重 + `no_positive_alpha=True` 标记。
4. `_optimize_ensemble_weights` 负 alpha 策略权重为 0，不用 `max(alpha, 0.01)` 掩盖。
5. 默认 pytest 通过（646+ 测试，0 failed）；新增测试 ≥ 8 个。
6. 不修改 risk/execution/策略/指标代码；不改 alpha 排序为 OOS；不加 WF alpha 校验。
7. 更新 `designs/design_v2/07-backtest-module.md` + trajectory + decision_log + CODEBUDDY。

### 验收阶段（Meta-Agent 独立执行）

- 运行 `python main.py --reoptimize`，验证：
  - 4/6 组空仓（SPX_mid_vol, SPX_high_vol, SPX_low_vol, NDX_mid_vol — 当前全负 alpha）
  - 2/6 组保留正 alpha 策略（NDX_high_vol: rsi_trend_filter +6.50, NDX_low_vol: rsi_mean_revert +1.58）
  - PortfolioBacktest 组合 alpha 从 -21.41% 改善（负 alpha 策略不再拖累）
  - 若组合 alpha 仍为负，说明 2/6 组的正 alpha 不足以覆盖 SPY 涨幅 → 策略池需要改进（Iter #13 方向明确）

---

## 7. Implementation Order

1. 读 spec + `matrix_backtest.py`（重点 `_run_group` line 1219-1284 + `_optimize_ensemble_weights` line 658-698）+ `experience.md` #8 + `iterations/iteration_11/summary.md`。
2. 给 `GroupBacktestResult` 加 `no_positive_alpha` 字段。
3. `_run_group` 在 candidates 构建后、Tier 1 前插入 alpha>0 硬门槛 + 全负 alpha 空仓分支。
4. `_optimize_ensemble_weights` 修负 alpha 归一化（`max(alpha, 0.01)` → `max(alpha, 0.0)` + 全零 fallback）。
5. 写 alpha>0 门槛测试（含与健全性门槛协同测试）。
6. 检查并更新现有 mock 测试（确保 mock 的 daily_returns 产生正 alpha，避免被新门槛误杀）。
7. 运行 targeted tests + 默认 pytest。
8. 更新 `designs/design_v2/07-backtest-module.md` + trajectory + decision_log + CODEBUDDY。

---

## 8. Risk Classification

- **低风险**：仅改 `mytrader/backtest/matrix_backtest.py`（非 Constitution L8 高风险目录）。
- **行为变更**：alpha>0 门槛会改变 `strategy_weights.json` 输出（4/6 组可能空仓）。这是**预期且正确**的行为——系统拒绝交易跑不赢 SPY 的策略，优于交易 -21% alpha 的垃圾组合（experience.md #8："没有候选满足门槛时，正确动作是空仓/降现金/回退 benchmark，不是矬子里拔将军"）。
- **缓解**：alpha>0 门槛是可调的（可改为 `alpha > -benchmark_margin` 允许小幅跑输）；测试覆盖正/负/混合/全负场景。
- **Constitution 合规**：alpha>0 门槛不违反 L1（Sortino 仍是 KPI）；DD 硬约束不变；不引入 RL/黑箱。
- **回滚**：若 alpha>0 门槛过于激进（大面积空仓），可改为 `alpha > -2.0`（允许小幅跑输 SPY 2%）或临时禁用。
