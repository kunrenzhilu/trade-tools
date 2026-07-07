# Iteration #13 Spec — WF Gate 加 Alpha 校验（目标一致性修复）

> 日期：2026-07-08
> Meta-Agent：GLM
> 输入依据：用户方法论分析（WF 与 matrix_backtest 目标不一致）、`tmp/iteration10_audit.md` §5 第 6 点、`iterations/iteration_12/summary.md`（WF 4/4 pass 但 alpha=-21%）、`.codebuddy/notes/experience.md` #8
> 风险等级：**低**（仅修改 `matrix_backtest.py` 的 WF 验证逻辑 + `main.py` 日志，不触及选择器/策略/risk/execution）
> 核心目标：给 WF gate 加 alpha 校验，使 WF 的验证目标与 matrix_backtest 的选择目标（alpha）一致。当前 matrix_backtest 用 alpha 选策略，但 WF 只校验 DD——WF 通过 ≠ 跑赢 SPY。Iter #11 的 WF 4/4 pass 但组合 alpha=-21% 就是这个不一致的直接后果。

---

## 1. 背景

### 问题：WF 与 matrix_backtest 目标不一致

当前系统的三层流程：

```
matrix_backtest（选策略）
  目标：alpha（选跑赢 SPY 的策略）
  门槛：健全性 → DD → alpha>0 → 排序选 top-K
    ↓ 产出 strategy_weights.json
WF（验证）
  目标：DD（检查不爆仓）  ← ⚠️ 与选择目标不一致
  门槛：val DD ≤ 15%（Sortino 算了但不 gate；alpha 根本没算）
    ↓ pass/fail
PortfolioBacktest（最终权重验证）
  目标：alpha + Sortino + DD
```

**Iter #11 的实证**：WF 4/4 pass（Sortino 1.56~2.09，max DD 6.36%），但 PortfolioBacktest alpha=-21.41%。WF 通过只说明"策略没爆仓"，不说明"策略跑赢 SPY"。

### 根因（代码级）

`matrix_backtest.py::run_walk_forward`（line 903）：
```python
passed = val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD  # 只看 DD！
```

WF 验证期已经计算了 portfolio 的 combined returns（line 890），但只用它算 Sortino 和 DD，没算 alpha。`_compute_alpha()` 和 `_get_spy_returns()` 都已存在（Iter #9 新增），只是 WF 没调用。

### 修复思路

不需要特制 OOS 数据集——**WF 的验证期本身就是 OOS**（相对训练期）。只需在 WF 验证期计算 alpha vs SPY，并加入 gate，就实现了 OOS alpha 验证。这与 matrix_backtest 的 alpha 选择目标一致。

---

## 2. Problem Statement

### 当前代码缺陷

1. **`WalkForwardRound` 缺 `val_alpha` 字段**：只有 `val_sortino` 和 `val_max_dd`，没有验证期 alpha。
2. **WF gate 只校验 DD**：`passed = val_max_dd <= 15%`，不校验 alpha。
3. **`WalkForwardReport` 缺 alpha 聚合**：只有 `max_val_dd`，没有 `avg_val_alpha` 或 `min_val_alpha`。
4. **`main.py` WF 日志不输出 alpha**：只输出 sortino/dd/passed，不输出 alpha。

---

## 3. Scope

### 本次要做

1. `WalkForwardRound` 新增 `val_alpha: float = 0.0` 字段。
2. `WalkForwardReport` 新增 `avg_val_alpha: float = 0.0` 和 `min_val_alpha: float = 0.0` 字段。
3. `run_walk_forward` 在验证期计算 portfolio-level alpha vs SPY（复用 `_get_spy_returns` + `_compute_alpha`）。
4. WF gate 加 alpha 校验：
   - 单轮：`passed = val_max_dd ≤ 15% AND val_alpha > -5%`（允许单轮小幅跑输，但不容忍灾难性跑输）
   - 汇总：`pass_all_rounds = all rounds passed AND avg_val_alpha > 0`（平均必须跑赢 SPY）
5. 新增常量 `WALK_FORWARD_VAL_ALPHA_FLOOR: float = -5.0`（单轮 alpha 下限）。
6. `main.py` WF 日志增加 alpha 输出。
7. 新增/更新测试。
8. 更新 `designs/design_v2/07-backtest-module.md` + trajectory + decision_log + CODEBUDDY。

### 本次不做（明确排除）

1. **不**做 per-group OOS alpha 反馈（用 WF alpha 清除个别组的权重）→ Iter #14，需要更大的架构改动。
2. **不**改 matrix_backtest 的选择逻辑（in-sample alpha 排序保持不变）。
3. **不**改 WF 的训练期逻辑（仍然用 `_run_group` 做参数搜索 + 选择）。
4. **不**改 PortfolioBacktest（保持原样，定位调整为"生产权重 sanity check"在文档中说明）。
5. **不**触及策略代码、risk、execution。
6. **不**运行 `--reoptimize`（由 Meta-Agent 验收时独立运行）。

---

## 4. Detailed Design

### 4.1 新增常量

`matrix_backtest.py`（约 line 41，`WALK_FORWARD_VAL_DD_THRESHOLD` 附近）：

```python
# 迭代 #13：WF 验证期 alpha 单轮下限
# 单轮允许小幅跑输 SPY（-5%），但平均必须跑赢（avg > 0）
# 设计动机：WF 与 matrix_backtest 目标一致性——matrix_backtest 用 alpha 选策略，
# WF 也必须校验 alpha，否则 WF 通过 ≠ 跑赢 SPY（Iter #11: WF 4/4 pass 但 alpha=-21%）
WALK_FORWARD_VAL_ALPHA_FLOOR: float = -5.0
```

### 4.2 `WalkForwardRound` 新增字段

`matrix_backtest.py`（约 line 131）：

```python
@dataclass
class WalkForwardRound:
    # ... 现有字段 ...
    val_sortino: float
    val_max_dd: float
    val_alpha: float = 0.0     # 迭代 #13：验证期 portfolio alpha vs SPY（百分数）
    passed: bool
```

### 4.3 `WalkForwardReport` 新增字段

`matrix_backtest.py`（约 line 152）：

```python
@dataclass
class WalkForwardReport:
    # ... 现有字段 ...
    rounds: list[WalkForwardRound]
    pass_all_rounds: bool
    max_val_dd: float
    avg_val_alpha: float = 0.0   # 迭代 #13：4 轮平均验证期 alpha
    min_val_alpha: float = 0.0   # 迭代 #13：4 轮中最差的验证期 alpha
```

### 4.4 `run_walk_forward` 计算 val alpha + 加 gate

`matrix_backtest.py`（约 line 889-903），在现有 `combined` 计算后加 alpha：

```python
# 现有代码（line 890-901）：
combined = pd.concat(all_returns, axis=1).mean(axis=1).dropna()
if len(combined) < 5:
    val_sortino = 0.0
    val_max_dd = 0.0
else:
    val_sortino = _compute_sortino(combined)
    wrapper = [SingleBacktestResult(...)]
    val_max_dd = _portfolio_max_drawdown_from_results(wrapper)

# ── 迭代 #13 新增：计算验证期 alpha vs SPY ──
# 与 matrix_backtest 的 alpha 选择目标一致（目标一致性修复）
# SPY 不可用时 alpha=0.0（与 _compute_alpha 的降级语义一致）
spy_val_returns = mb._get_spy_returns(val_start, val_end)
if len(combined) >= 5 and spy_val_returns is not None:
    val_alpha = _compute_alpha(combined, spy_val_returns)
else:
    val_alpha = 0.0
    if spy_val_returns is None:
        logger.warning(
            f"[WalkForward] Round {round_num}: SPY data unavailable for "
            f"val period {val_start}~{val_end} — val_alpha=0 (degraded)"
        )

# ── 迭代 #13：gate 加 alpha 校验 ──
# 单轮：DD ≤ 15% AND alpha > -5%（允许小幅跑输，不容忍灾难）
# 汇总：all rounds passed AND avg alpha > 0（平均必须跑赢 SPY）
dd_passed = val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD
alpha_passed = val_alpha > WALK_FORWARD_VAL_ALPHA_FLOOR
passed = dd_passed and alpha_passed
```

### 4.5 `WalkForwardReport` 汇总加 alpha 聚合

`matrix_backtest.py`（约 line 920-924）：

```python
# 迭代 #13：汇总 alpha 聚合
val_alphas = [r.val_alpha for r in wf_rounds]
avg_val_alpha = sum(val_alphas) / len(val_alphas) if val_alphas else 0.0
min_val_alpha = min(val_alphas) if val_alphas else 0.0

# 迭代 #13：pass_all_rounds 加 avg alpha > 0 条件
# 单轮 all passed + 平均 alpha > 0（平均必须跑赢 SPY）
all_rounds_passed = all(r.passed for r in wf_rounds) if wf_rounds else False
avg_alpha_positive = avg_val_alpha > 0
pass_all = all_rounds_passed and avg_alpha_positive

report = WalkForwardReport(
    rounds=wf_rounds,
    pass_all_rounds=pass_all,
    max_val_dd=max((r.val_max_dd for r in wf_rounds), default=0.0),
    avg_val_alpha=avg_val_alpha,
    min_val_alpha=min_val_alpha,
)
```

日志增加 alpha：
```python
logger.info(
    f"[WalkForward] done: {len(wf_rounds)} rounds, "
    f"pass_all_rounds={report.pass_all_rounds}, "
    f"max_val_dd={report.max_val_dd:.4f}%, "
    f"avg_val_alpha={report.avg_val_alpha:.4f}%, "
    f"min_val_alpha={report.min_val_alpha:.4f}%"
)
```

### 4.6 `main.py` WF 日志增加 alpha

`main.py`（约 line 378-388），WF round 和 summary 日志增加 alpha：

```python
for r in wf_report.rounds:
    logger.info(
        f"[WalkForward] Round {r.round_num}/4: "
        f"train={r.train_start}~{r.train_end}, "
        f"val={r.val_start}~{r.val_end}, "
        f"sortino={r.val_sortino:.4f}, "
        f"dd={r.val_max_dd:.4f}%, "
        f"alpha={r.val_alpha:.4f}%, "     # 迭代 #13 新增
        f"passed={r.passed}"
    )
logger.info(
    f"[WalkForward] Summary: pass_all_rounds={wf_report.pass_all_rounds}, "
    f"max_val_dd={wf_report.max_val_dd:.4f}%, "
    f"avg_val_alpha={wf_report.avg_val_alpha:.4f}%, "   # 迭代 #13 新增
    f"min_val_alpha={wf_report.min_val_alpha:.4f}%"     # 迭代 #13 新增
)
if not wf_report.pass_all_rounds:
    logger.warning(
        "[WalkForward] NOT all rounds passed — "
        "Constitution L7 requires all 4 rounds DD<=15% AND avg alpha>0 "
        "before paper trading."
    )
```

### 4.7 Gate 逻辑总结

| 层级 | 条件 | 常量 |
|------|------|------|
| 单轮 | `val_max_dd ≤ 15% AND val_alpha > -5%` | `WALK_FORWARD_VAL_DD_THRESHOLD=15.0`, `WALK_FORWARD_VAL_ALPHA_FLOOR=-5.0` |
| 汇总 | `all rounds passed AND avg_val_alpha > 0` | （硬编码 avg > 0） |

**设计动机**：
- 单轮允许 alpha 在 -5%~0%（小幅跑输 SPY 可能是市场噪音）
- 但 4 轮平均必须 > 0（整体必须跑赢 SPY）
- 这与 matrix_backtest 的 alpha>0 门槛呼应：in-sample alpha>0 是入选条件，OOS avg alpha>0 是验证条件

---

## 5. 测试计划

新增 `tests/test_wf_alpha_gate.py`：

1. **test_wf_round_has_val_alpha_field** — `WalkForwardRound.val_alpha` 字段存在且默认 0.0。
2. **test_wf_report_has_alpha_aggregation** — `WalkForwardReport.avg_val_alpha` 和 `min_val_alpha` 字段存在。
3. **test_wf_gate_rejects_negative_alpha** — 单轮 alpha < -5% → `passed=False`（即使 DD 合规）。
4. **test_wf_gate_passes_positive_alpha** — 单轮 alpha > 0 且 DD ≤ 15% → `passed=True`。
5. **test_wf_gate_allows_small_negative_alpha** — 单轮 alpha = -3%（> -5%）且 DD 合规 → `passed=True`。
6. **test_wf_summary_avg_alpha_negative_fails** — 4 轮全 pass 但 avg alpha < 0 → `pass_all_rounds=False`。
7. **test_wf_summary_avg_alpha_positive_passes** — 4 轮全 pass 且 avg alpha > 0 → `pass_all_rounds=True`。
8. **test_wf_spy_unavailable_alpha_zero** — SPY 不可用时 val_alpha=0.0 + WARNING（降级不阻塞）。
9. **test_wf_alpha_computed_correctly** — 用已知 returns + spy_returns 验证 val_alpha 值正确。

### 回归

- 现有 `tests/test_matrix_backtest.py` 中 WF 相关测试全部通过。
- **注意**：现有 WF 测试可能没有 SPY 数据 → val_alpha=0 → avg_alpha=0 → `pass_all_rounds=False`（因为 avg > 0 不满足）。需要检查现有测试是否依赖 `pass_all_rounds=True`，如果是，需要在测试中提供 SPY 数据或 mock alpha > 0。

---

## 6. Success Criteria

1. `WalkForwardRound.val_alpha` 和 `WalkForwardReport.avg_val_alpha`/`min_val_alpha` 字段存在。
2. `run_walk_forward` 在验证期计算 portfolio-level alpha vs SPY。
3. WF gate：单轮 `DD ≤ 15% AND alpha > -5%`；汇总 `all passed AND avg alpha > 0`。
4. `main.py` WF 日志输出 alpha。
5. 默认 pytest 通过（659+ 测试，0 failed）；新增测试 ≥ 8 个。
6. 不修改选择器/策略/risk/execution 代码。
7. 更新 `designs/design_v2/07-backtest-module.md` + trajectory + decision_log + CODEBUDDY。

### 验收阶段（Meta-Agent 独立执行）

- 运行 `python main.py --reoptimize`，验证：
  - WF 每轮日志输出 alpha
  - WF summary 输出 avg_val_alpha 和 min_val_alpha
  - 若 avg alpha < 0 → `pass_all_rounds=False` + WARNING（与 Iter #11 的 alpha=-21% 场景一致）
  - matrix_backtest 产出的 weights 不受影响（WF 是验证步骤，不修改 weights）

---

## 7. Implementation Order

1. 读 spec + `matrix_backtest.py`（重点 `run_walk_forward` line 785-930 + `WalkForwardRound`/`WalkForwardReport` line 114-155 + `_get_spy_returns` line 1036）+ `experience.md` #8 + `main.py::_run_reoptimize` line 364-396。
2. 加 `WALK_FORWARD_VAL_ALPHA_FLOOR` 常量。
3. `WalkForwardRound` 加 `val_alpha` 字段。
4. `WalkForwardReport` 加 `avg_val_alpha` + `min_val_alpha` 字段。
5. `run_walk_forward` 验证期计算 alpha + gate 加 alpha 校验 + 汇总加 alpha 聚合。
6. `main.py` WF 日志增加 alpha。
7. 写测试（含 SPY 不可用降级、alpha 边界、汇总逻辑）。
8. 检查现有 WF 测试是否需要调整（SPY 数据 / mock alpha）。
9. 运行 targeted tests + 默认 pytest。
10. 更新 `designs/design_v2/07-backtest-module.md` + trajectory + decision_log + CODEBUDDY。

---

## 8. Risk Classification

- **低风险**：仅改 WF 验证逻辑（`run_walk_forward`）+ 数据结构字段 + 日志，不触及选择器/策略/risk/execution。
- **行为变更**：WF gate 变严了（加了 alpha 校验）。之前 DD-only pass 的策略现在可能因 alpha<0 而 fail。这是**预期且正确**的——WF 通过应该意味着"OOS 跑赢 SPY"，不只是"OOS 没爆仓"。
- **降级处理**：SPY 不可用时 val_alpha=0.0（不阻塞 WF），但汇总 avg_alpha=0 → `pass_all_rounds=False`（保守拒绝）。
- **Constitution 合规**：WF alpha 校验直接满足 experience.md #8 的"验收 gate 必须校验跑赢 benchmark（正 alpha）"。
- **回滚**：若 alpha gate 过严（大面积 WF fail），可下调 `WALK_FORWARD_VAL_ALPHA_FLOOR` 或临时设为 -100（禁用 alpha gate）。
