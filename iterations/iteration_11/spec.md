# Iteration #11 Spec — 选择器健全性门槛（Reject Degenerate Strategies）

> 日期：2026-07-07
> Meta-Agent：Claude
> 输入依据：`tmp/iteration10_audit.md`（三方综合审计 + 本机实测）、`iterations/iteration_10/summary.md`、`mytrader/config/strategy_weights.json`、`.codebuddy/notes/experience.md` #6-#8、meta-agent skill Gate 1（新增 Trade health 行）
> 风险等级：**低**（仅修改 `mytrader/backtest/matrix_backtest.py` 选择器逻辑，不触及 risk/execution/strategy/策略代码）
> 核心目标：在 MatrixBacktest 的 top-K 选择**排序之前**，剔除"退化策略"（几乎不平仓的伪 buy-and-hold），使 `strategy_weights.json` 不再包含 win_rate=NaN/≈0 的策略。

---

## 1. 背景

Iter #10 的 reoptimize（Alpha 排序）产出灾难性结果：

| 指标 | Iter #7 | Iter #10 |
|------|---------|----------|
| 年化 | 8.02% | **-4.88%** |
| Sortino | 1.03 | **-0.66** |
| Alpha | -11.34% | **-25.26%** |

三方审计 + 本机实测（`tmp/audit_verify.py`）证实根因：

- `rsi_trend_filter` 入场条件（`close>SMA200`）与出场条件（`close<SMA200`）在趋势方向上互斥 → 多头行情中**仓位几乎永不平仓**。真实数据上对 5 只股票产生 **0 个出场信号**，每只只开 1 仓挂到末尾强平，**win_rate 全为 NaN**（经 `_safe_float` 归零 → `strategy_weights.json` 里 `backtest_win_rate=0.0053`）。
- 它的"收益/Sortino"只是持仓逐日盯市 + 末尾强平凑出来的（退化 buy-and-hold），不是策略交易能力。
- **选择器没有任何健全性门槛**，让这个伪策略骗过了 alpha 排序，进入 4/6 组权重。

**关键教训（experience.md #8）**：排序（选 top-K）之前必须先过硬门槛，顺序为 ① 健全性 → ② 风险(DD) → ③ 排序。本轮只补 ①（最便宜、能拦住整个灾难的 gate）。

---

## 2. Problem Statement

### 当前代码（`matrix_backtest.py::_run_group`）

`group_results` 里的每个策略无论是否真的完成交易闭环，都直接进入 candidates 参与 DD/Sortino/Alpha 三级过滤和排序。退化策略（0 平仓交易）因逐日盯市有"漂亮"的 Sortino/alpha，会被选中。

### 缺失的信号

`SingleBacktestResult` 目前记录了 `total_trades` 和 `win_rate_pct`，但：
- `total_trades` 包含未平仓的 open trade（末尾强平计 1 笔），无法区分"真交易"和"买一次不动"。
- `win_rate_pct` 在零平仓交易时被 `_safe_float(NaN)` 归零，丢失了"退化"这一信息。

需要一个**明确的"已平仓交易数"**信号来识别退化策略。

### 解决方案

1. 给 `SingleBacktestResult` 新增 `closed_trades: int` 字段（vbt 已平仓交易数）。
2. 在 `_backtest_one` 和 `_backtest_batch` 中从 vbt 提取 `pf.trades.status_closed.count()` 填充。
3. 在 `_run_group` 中新增**健全性过滤**（在 DD/Sortino/Alpha 过滤之前）：剔除退化策略。
4. 若某组所有策略都退化 → 该组产出空权重（持仓现金）并标记 `no_valid_strategy`，**不强行选退化策略**。

---

## 3. Scope

### 本次要做

1. `SingleBacktestResult` 新增 `closed_trades: int = 0` 字段。
2. `_backtest_one` / `_backtest_batch` 提取并填充 `closed_trades`（batch 与 single 数值一致）。
3. 新增常量 + 健全性判定函数 `_is_degenerate_strategy(results) -> bool`。
4. `_run_group` 在候选排序前加健全性过滤；全退化时产出空权重 + `no_valid_strategy` 标记。
5. `strategy_weights.json` 权重条目在全退化组体现为空列表（该组无策略）；`GroupBacktestResult` 增加可选标记字段。
6. 新增/更新测试。
7. 更新 `designs/design_v2/07-backtest-module.md` + trajectory + decision_log + CODEBUDDY。

### 本次不做（明确排除，留给后续迭代）

1. **不**改 alpha 排序为 OOS/Walk-Forward 验证期 alpha（→ Iter #12）。
2. **不**新增 `alpha>0` 硬门槛（→ Iter #12）；保留现有 DD+Sortino+Alpha 排序作用于"通过健全性过滤后的存活候选"。
3. **不**修 `rsi_trend_filter` 的出场逻辑（健全性门槛会自动排除它；策略重设计是独立任务）。
4. **不**触及 `mytrader/risk/`、`mytrader/execution/`、任何策略文件、指标文件。
5. **不**改 DD 阈值 / 仓位上限 / 止损止盈。
6. **不**运行 `--reoptimize`（由 Meta-Agent 验收时独立运行）。

---

## 4. Detailed Design

### 4.1 `SingleBacktestResult` 新增字段

`matrix_backtest.py`（约 line 54）：

```python
@dataclass
class SingleBacktestResult:
    symbol: str
    strategy: str
    params: dict
    sharpe: float
    total_return_pct: float
    max_drawdown_pct: float
    win_rate_pct: float
    total_trades: int
    daily_returns: pd.Series
    sortino: float = 0.0
    closed_trades: int = 0    # 迭代 #11 新增：已平仓交易数（区分退化 buy-and-hold）
```

### 4.2 提取 closed_trades

在 `_backtest_one`（约 line 372）和 `_backtest_batch`（约 line 526）提取 stats 处，新增：

```python
# 迭代 #11：已平仓交易数（用于健全性门槛）
# vbt 1.0: pf.trades.status_closed.count() 返回已平仓交易数
try:
    closed_trades = int(pf.trades.status_closed.count())  # _backtest_one
    # batch 模式用 pf_sym.trades.status_closed.count()
except Exception:
    closed_trades = 0
```

> 实现要求：`_backtest_batch` 的 `closed_trades` 提取必须与 `_backtest_one` 对同一标的数值一致（沿用 Iter #10 的 batch-vs-single 一致性测试范式）。若 vbt API 名称不同，实现者需查 vbt 1.0.0 实际 API（如 `pf.trades.closed.count()` 或 `pf_sym.trades.records_readable` 中 status 字段）并保证正确性；提取失败降级为 0，不抛异常。

### 4.3 健全性判定函数

新增常量（约 line 47，`MIN_SORTINO_THRESHOLD` 附近）：

```python
# 迭代 #11：健全性门槛 —— 识别"退化策略"（几乎不平仓的伪 buy-and-hold）
# 判定：组内"有效标的中，已平仓交易数为 0 的比例"超过此阈值 → 退化
# 设计动机：真策略应在多数标的上完成买卖闭环；若近乎所有标的都从不平仓，
#           说明入场/出场条件矛盾（如 Iter #8 rsi_trend_filter），其收益只是
#           持仓盯市 + 末尾强平的假象，必须在排序前剔除。
# 阈值取 0.8（保守）：只在"近乎全部标的零平仓"时触发，避免误伤低频合法策略。
DEGENERATE_NO_CLOSE_FRACTION: float = 0.8
```

函数（`_combine_daily_returns` 附近）：

```python
def _is_degenerate_strategy(results: list[SingleBacktestResult]) -> bool:
    """判定一个策略在组内是否退化（几乎不产生已平仓交易）。

    退化定义：有效标的中 closed_trades==0 的比例 >= DEGENERATE_NO_CLOSE_FRACTION。
    这类策略的入场/出场条件互斥（如趋势过滤锁死了均值回归出场），仓位无法平仓，
    其 Sortino/alpha 只是持仓盯市假象，不代表真实交易能力，必须在选择前剔除。

    Args:
        results: 单策略多标的的回测结果列表

    Returns:
        True 表示退化（应剔除）；空结果视为退化（True）
    """
    if not results:
        return True
    n = len(results)
    no_close = sum(1 for r in results if r.closed_trades <= 0)
    return (no_close / n) >= DEGENERATE_NO_CLOSE_FRACTION
```

### 4.4 `_run_group` 集成健全性过滤

在 `group_results` 收集完成、构建 `candidates` **之前**（约 line 1131 `if not group_results` 之后、line 1147 candidates 构建之前）插入：

```python
# 迭代 #11：健全性过滤 —— 排序前先剔除退化策略（experience.md #8：sanity → risk → rank）
sane_results = []
for (strategy, params, results) in group_results:
    if _is_degenerate_strategy(results):
        logger.warning(
            f"[MatrixBacktest] {group_id}: strategy '{strategy}' is DEGENERATE "
            f"(>= {DEGENERATE_NO_CLOSE_FRACTION:.0%} symbols have 0 closed trades) "
            f"— excluded before ranking. Its Sortino/alpha is mark-to-market illusion."
        )
        continue
    sane_results.append((strategy, params, results))

if not sane_results:
    # 全组退化 → 空权重（持仓现金），标记 no_valid_strategy，不强行选退化策略
    logger.warning(
        f"[MatrixBacktest] {group_id}: ALL strategies degenerate — "
        f"group produces EMPTY weights (hold cash). Marked no_valid_strategy."
    )
    report.warnings.append(f"{group_id}: no_valid_strategy (all strategies degenerate)")
    # 标记对应 GroupBacktestResult（若已 append）
    for gr in report.group_results:
        if gr.group_id == group_id:
            gr.no_valid_strategy = True
    return []

# 后续 candidates 构建、DD/Sortino/Alpha 过滤、排序，全部改用 sane_results 替代 group_results
group_results = sane_results
```

> 注意：`report.group_results` 中已 append 的退化策略条目应保留（供审计追溯），但不进入 `weights_list`。由于健全性过滤发生在 candidates 构建前，退化策略自然不会出现在最终权重里。

### 4.5 `GroupBacktestResult` 新增标记

```python
@dataclass
class GroupBacktestResult:
    # ... 现有字段 ...
    backtest_alpha: float = 0.0
    no_valid_strategy: bool = False   # 迭代 #11：该组是否因全退化而空仓
```

---

## 5. 测试计划

新增 `tests/test_degenerate_filter.py`（或扩展 `test_matrix_backtest.py`）：

1. **test_closed_trades_populated** — 正常策略回测结果的 `closed_trades > 0`。
2. **test_closed_trades_batch_matches_single** — batch 与 single 的 `closed_trades` 对同一标的一致（沿用 Iter #10 一致性范式）。
3. **test_degenerate_detected** — 构造"只有 entries 无 exits"的信号（仓位挂到末尾），`_is_degenerate_strategy` 返回 True。
4. **test_normal_not_degenerate** — 正常闭环策略（有平仓交易）返回 False。
5. **test_degenerate_excluded_from_weights** — `_run_group` 中退化策略不出现在返回的 weights_list（用 mock/构造数据 + 真实 store fixture 二选一，参考现有 test_matrix_backtest.py 风格）。
6. **test_all_degenerate_group_empty** — 组内全部策略退化 → 返回空列表 + `no_valid_strategy=True` 标记。
7. **test_low_frequency_strategy_not_falsely_excluded** — 低频但有平仓交易的策略（如每标的 2-3 笔）不被误判为退化（验证 0.8 阈值不误伤）。

### 回归

现有 `tests/test_matrix_backtest.py`、`tests/test_batch_backtest.py` 全部通过（验证健全性过滤没破坏 DD/Sortino/Alpha 排序、batch 一致性）。

---

## 6. Success Criteria

1. `SingleBacktestResult.closed_trades` 字段存在并被 `_backtest_one`/`_backtest_batch` 正确填充。
2. `_is_degenerate_strategy` 正确识别"近乎全标的零平仓"的退化策略。
3. `_run_group` 在排序前剔除退化策略；全退化组返回空权重 + `no_valid_strategy` 标记。
4. 退化策略（如 `rsi_trend_filter` 当前实现）不再进入 `strategy_weights.json`。
5. 默认 pytest 通过（626+ 测试，0 failed）；新增测试 ≥ 6 个。
6. batch 与 single 的 `closed_trades` 数值一致。
7. 不修改 risk/execution/策略/指标代码；不改 alpha 排序为 OOS；不加 alpha>0 硬门槛。
8. 更新 `designs/design_v2/07-backtest-module.md` + trajectory + decision_log + CODEBUDDY。

### 验收阶段（Meta-Agent 独立执行）

- 运行 `python main.py --reoptimize`，验证：
  - `rsi_trend_filter` 不再出现在任何组权重中；
  - 各组权重 `backtest_win_rate` 不再是 ≈0 的退化值；
  - PortfolioBacktest 组合指标从 Iter #10 的 alpha=-25% 恢复到 ≈Iter #7 的可信基线（正收益、Sortino>0）。

---

## 7. Implementation Order

1. 读 spec + `matrix_backtest.py`（重点 `_backtest_one` / `_backtest_batch` / `_run_group`）+ `experience.md` + `tmp/iteration10_audit.md`。
2. 查 vbt 1.0.0 已平仓交易 API，先写一个最小验证脚本确认 `closed_trades` 提取正确。
3. 给 `SingleBacktestResult` 加 `closed_trades`，在 `_backtest_one`/`_backtest_batch` 填充。
4. 写 `closed_trades` 一致性测试（batch vs single）。
5. 加 `DEGENERATE_NO_CLOSE_FRACTION` 常量 + `_is_degenerate_strategy`。
6. `_run_group` 集成健全性过滤 + 全退化空仓分支 + `GroupBacktestResult.no_valid_strategy`。
7. 写健全性过滤测试（含误伤边界 test_low_frequency）。
8. 运行 targeted tests + 默认 pytest。
9. 更新 `designs/design_v2/07-backtest-module.md` + trajectory + decision_log + CODEBUDDY。

---

## 8. Risk Classification

- **低风险**：仅改 `mytrader/backtest/matrix_backtest.py`（非 Constitution L8 高风险目录）。
- **行为变更**：健全性过滤会改变 `strategy_weights.json` 输出（退化策略被剔除；极端情况下某组空仓）。这是**预期且正确**的行为——系统拒绝交易伪策略优于交易 -25% 的垃圾。
- **缓解**：严格的 batch-vs-single 一致性测试 + 误伤边界测试（低频策略不被误判）。
- **Constitution 合规**：健全性门槛不违反 L1（Sortino 仍是 KPI）；DD 硬约束不变；不引入 RL/黑箱。
- **回滚**：若健全性过滤误伤合法策略，可上调 `DEGENERATE_NO_CLOSE_FRACTION` 或临时禁用过滤。
