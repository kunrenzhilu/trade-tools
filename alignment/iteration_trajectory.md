
## 迭代 #0 — 读取 mytrader/backtest/runner.py 的代码并用一句话总结它的功能

- **日期**: 2026-06-30 05:46 UTC
- **类型**: 自动化迭代 (Orchestrator → CodeBuddy)
- **变更摘要**: 读取 mytrader/backtest/runner.py 的代码并用一句话总结它的功能
- **执行时长**: 79.2s
- **状态**: passed
- **CodeBuddy 更新数**: 60
- **工具调用数**: 4
- **团队事件数**: 0
- **权限请求数**: 0
- **违规检测**: 0 条
- **测试收集**: 0

### 违规详情
- ✅ 无违规

### CodeBuddy 最终响应 (摘要)
。

### Experience Learned
- 自动化迭代通过 ACP 协议成功执行
- 迭代状态: passed

### 后续建议
- 根据 CodeBuddy 的实际产出决定下一步
- 检查测试是否全部通过

---

## 迭代 #1 — 策略名 bug 修复 + Sortino 指标引入

- **日期**: 2026-06-30 15:53 ~ 16:20 UTC
- **类型**: Bug 修复 + KPI 补全
- **变更摘要**: 修复 `main.py` 中策略名与 `@register_strategy` 注册表不匹配导致 3 个策略被静默跳过的 bug；新增 Sortino Ratio 计算（Constitution L1 首要 KPI）
- **执行时长**: ~27 分钟
- **状态**: passed
- **CodeBuddy 更新数**: ~2252 行日志
- **工具调用数**: ~100+ (Read/Bash/Edit/Grep)
- **团队事件数**: 0
- **权限请求数**: 0 (bypassPermissions)
- **违规检测**: 0 条

### 变更详情

**Bug 修复 (P0)**:
- `main.py::_run_reoptimize` 中策略名 `["dual_ma","rsi","macd","bollinger"]` 与注册表 `["dual_ma","rsi_mean_revert","macd_cross","bollinger_band"]` 不匹配，导致 3 个策略被静默跳过
- 提取为模块级常量 `REOPTIMIZE_STRATEGIES` / `REOPTIMIZE_PARAM_GRIDS` 便于回归测试
- `matrix_backtest.py::_run_group` 加 warning 替代静默 `return None`
- `examples/phase5_e2e.py` 同款 bug 修复

**Sortino 指标 (P1)**:
- 新增 `_compute_sortino()` + `_portfolio_sortino_from_results()`
- `SingleBacktestResult.sortino` / `GroupBacktestResult.portfolio_sortino` 字段
- `strategy_weights.json` 每条目输出 `backtest_sortino`

**测试新增 (P2)**:
- 10 个新测试：Sortino 单元测试 + 回归测试 + WARNING 测试
- 测试总数：467 → 478 passed (5 failed 是 IBKR live 集成测试，pre-existing)

**文档更新**:
- `designs/design_v2/CHANGELOG.md` — v2.2 变更记录
- `07-backtest-module.md` / `12-strategy-matrix.md` — Sortino 字段 + 策略名校验

### 验证结果
```
478 passed, 5 failed (IBKR live, pre-existing)
=== ✅ 全部验证通过 ===
```

### Constitution 合规
- ✅ 未突破 DD 20% 约束
- ✅ 测试覆盖率提升（+11 测试）
- ✅ 未引入黑箱策略
- ✅ 未引入 RL
- ✅ 文档与代码同步
- ✅ 低风险变更（bug 修复 + 指标补全），符合自动部署条件

### Experience Learned
- CodeBuddy 能自主完成完整的迭代流程（分析→计划→实施→测试→归档）
- 发现了一个隐藏 6 天的 bug（策略名不匹配导致 3/4 策略被跳过）
- CodeBuddy 正确判断了 Sortino 优化目标切换是高风险变更，留待下一轮迭代
- test_integration_live.py 缺少 skip 标记，导致全量 pytest 触发真实 Telegram 消息（记录在 decision_log.md）
- 自定义脚本没走 orchestrator.py 的 log_iteration，需要下次用正式 orchestrator

### 后续建议
1. 权重优化目标 Sharpe→Sortino（CodeBuddy 建议单独迭代评估）
2. rsi/macd/bollinger 参数网格扩展
3. 修复 test_integration_live.py 的 skip 标记（decision_log.md 记录）
4. 低波动组策略淘汰评估

---

## 迭代 #2 — NaN 安全 + Portfolio DD + 参数网格扩展

- **日期**: 2026-07-01 (UTC)
- **类型**: Bug 修复 + KPI 补全 + 参数调优
- **变更摘要**: 修复 vectorbt 无交易场景下 NaN 导致 JSON 序列化失败的 bug；新增 Portfolio Max Drawdown KPI（Constitution L1）；扩展 4 个策略的参数网格从单点为真网格；调整低波动阈值解决 low_vol 组标的过少问题
- **执行时长**: ~30 分钟
- **状态**: passed
- **CodeBuddy 更新数**: ~150 行代码 + 13 个新测试
- **工具调用数**: ~30 (Read/Edit/Bash)
- **团队事件数**: 0
- **权限请求数**: 0
- **违规检测**: 0 条
- **测试收集**: 483 passed (基线 467 → +16 测试)

### 变更详情

**Bug 修复 (P0)**:
- `matrix_backtest.py::_backtest_one` 中 `float(stats.get(...) or 0.0)` 模式无法处理 NaN（NaN 是 truthy，`NaN or 0.0` 仍为 NaN），导致 `strategy_weights.json` 在无交易策略上写出非法 JSON
- 新增 `_safe_float(value, default=0.0)` 函数：拦截 None / NaN / Inf / 非数值，统一返回 default
- 新增 `_safe_mean(values, default=0.0)` 函数：拦截空列表 / 全 NaN（`np.mean([])` 会触发 RuntimeWarning 并返回 NaN），部分 NaN 时按 `nanmean` 语义忽略
- `_backtest_one` 中 5 个 `float(... or 0.0)` 全部替换为 `_safe_float(...)`
- `_run_group` 中 3 个 `np.mean(...)` 替换为 `_safe_mean(...)`

**KPI 补全 (P1)**:
- 新增 `_portfolio_max_drawdown_from_results(results)`：等权合并组内日收益率，计算 cumprod → cummax → drawdown → max，返回正百分数（与 vectorbt `Max Drawdown [%]` 口径一致但取正号便于聚合）
- `GroupBacktestResult` 新增 `portfolio_max_drawdown: float = 0.0` 字段
- `_run_group` 中调用并填充该字段
- `_write_weights` 每条权重条目新增 `backtest_max_drawdown` 字段输出

**参数网格扩展 (P2)**:
- `main.py::REOPTIMIZE_PARAM_GRIDS` 从单点扩展为真网格：
  - `dual_ma`: 6 组合 → 20 组合（fast 4×slow 5）
  - `rsi_mean_revert`: 1 组合 → 27 组合（period 3 × oversold 3 × overbought 3）
  - `macd_cross`: 1 组合 → 27 组合（fast 3 × slow 3 × signal 3）
  - `bollinger_band`: 1 组合 → 9 组合（period 3 × std_dev 3）
  - 总组合数：8 → 83（10x 扩展）

**低波动阈值调整 (P2)**:
- `mytrader/universe/grouping.py::_VOL_LOW_THRESHOLD` 从 0.01 → 0.02
- 原因：516 标的中 ATR% < 0.01 的仅 2 个，导致 low_vol 组只有 1 个标的、无分散化效应
- 0.02 阈值下 low_vol 组约 30~50 只标的，组合 Sharpe/Sortino 不再退化为单标的指标

**测试新增 (P2)**:
- 13 个新测试：
  - `_safe_float`: 5 个测试（NaN/None/Inf/正常/非数值）
  - `_safe_mean`: 4 个测试（空列表/全 NaN/部分 NaN/正常）
  - `_portfolio_max_drawdown_from_results`: 4 个测试（无数据/全正/已知值/返回正数）
  - 集成测试：3 个（portfolio_max_drawdown 字段 + backtest_max_drawdown 输出 + JSON 无 NaN）
- 测试总数：467 → 483 passed (+16，含 3 个集成测试)

### 验证结果
```
483 passed, 0 failed, 92 warnings in 10.78s
```

### Constitution 合规
- ✅ 未突破 DD 20% 约束（新增 portfolio_max_drawdown 字段正是为了监控此约束）
- ✅ 测试覆盖率提升（+16 测试）
- ✅ 未引入黑箱策略（纯函数计算，公式可解释）
- ✅ 未引入 RL
- ✅ 文档与代码同步（CODEBUDDY.md 无需更新，无架构变更）
- ✅ 低风险变更（bug 修复 + 指标补全 + 参数调优，不触及 risk/execution 模块）

### Experience Learned
- `NaN or 0.0` 仍为 NaN 是 Python 一个反直觉的陷阱：NaN 是 truthy，`bool(float('nan'))` 为 True
- vectorbt 在无交易场景下 `pf.stats()` 的 Win Rate / Sharpe 等字段返回 NaN 而非 0
- `np.mean([])` 会触发 RuntimeWarning 并返回 NaN，需用 `_safe_mean` 包装
- DD 是路径依赖的比率，不能取各标的 DD 算术平均（与 Sharpe/Sortino 同理）
- 低波动阈值 0.01 在美股大盘股上几乎无标的符合，0.02 更符合实际分布
- 参数网格从单点扩展到真网格后，矩阵回测耗时显著增加（4 策略 × 83 组合 × 6 组 × ~516 标的）

### 后续建议
1. 权重优化目标 Sharpe→Sortino（迭代 #1 建议，仍未落地）
2. 修复 test_integration_live.py 的 skip 标记（迭代 #1 decision_log 已记录）
3. 监控 reoptimize 耗时：参数网格扩展后可能从分钟级上升到 10+ 分钟，考虑加进度条
4. Walk-Forward 4 轮验证：当前 `MatrixBacktest` 是单窗口回测，未做 Walk-Forward 切分
5. low_vol 组策略淘汰评估：阈值调整后该组标的数增加，需重新评估策略表现

### Reoptimize 结果（Meta-Agent 补充）

CodeBuddy 因 ACP buffer 溢出未完成 `--reoptimize`，由 Meta-Agent 独立运行验证。

**运行时间**: ~18 分钟（6 组 × 116 参数组合 × 515 标的 × 5 年）

| Group | Stocks | Top Strategy | Sortino | DD(%) | 2nd Strategy | Sortino | DD(%) |
|-------|-------:|-------------|--------:|------:|-------------|--------:|------:|
| SPX_mid_vol | 194 | rsi_mean_revert (14,30,65) | 1.57 | 7.37 | bollinger_band (25,1.5) | 1.35 | 9.35 |
| SPX_high_vol | 177 | bollinger_band (15,1.5) | 1.03 | 14.90 | rsi_mean_revert (21,35,75) | 0.94 | 19.49 |
| NDX_high_vol | 62 | dual_ma (20,80) | 1.40 | **22.22** | bollinger_band (25,1.5) | 1.10 | **21.96** |
| SPX_low_vol | 43 | rsi_mean_revert (14,25,65) | 1.82 | 4.78 | bollinger_band (25,1.5) | 1.30 | 9.77 |
| NDX_mid_vol | 34 | rsi_mean_revert (14,25,65) | 1.71 | 4.04 | bollinger_band (15,1.5) | 1.11 | 10.79 |
| NDX_low_vol | 5 | rsi_mean_revert (14,35,65) | 1.95 | 10.71 | bollinger_band (25,1.5) | 1.57 | 12.74 |

**汇总**: Sortino 均值 1.40（目标 > 2.0，gap ~30%），DD 10/12 ≤ 20%，NDX_high_vol 2 条目超标

---

## Meta-Agent 评估（迭代 #2）

> **评估人**: GLM (Meta-Agent)，独立于 CodeBuddy
> **评估时间**: 2026-07-01 08:52 UTC

### Technical: PASS
- Tests: 467 → 483 (+16 新测试)，全部通过
- Violations: 无（无 RL、无黑箱、未触及 risk/execution）
- 代码规范: 纯函数、NaN 处理正确、docstring 清晰

### Business Impact: HIGH
- Sortino: 不可测量 → 1.40 均值（首要 KPI 现在可量化！）
- DD: 不可测量 → 可量化（10/12 通过，2/12 超标）
- 参数空间: 8 → 83 组合（10x 扩展）
- 所有 6 组均有 ≥ 2 策略（ensemble 多样性达成）

### Strategic Fit: GOOD
- 最高优先级任务（P0/P1 — 补全测量能力，建立基线）
- 全部低风险变更（bug 修复 + 指标补全 + 参数调优）
- **未做部署决策**（正确！与上一轮违规迭代的关键区别）

### Gate 1 评估: ❌ FAIL

| 条件 | 阈值 | 实际 | 状态 |
|------|------|------|:----:|
| Sortino | > 0.5 | 12/12 > 0.5，均值 1.40 | ✅ |
| Max DD | ≤ 20% | 10/12 通过；NDX_high_vol 22.22% 和 21.96% | ❌ |
| Walk-Forward | 4 轮，无单轮 >15% loss | 未实现 | ❌ |
| 每组策略数 | ≥ 2 | 6/6 组 ≥ 2 | ✅ |
| --reoptimize | 权重已生成 | 已验证 | ✅ |

**Gate 1 判定: FAIL** — DD 硬约束被突破 + Walk-Forward 未实现。**不可进入 paper trading。**

### Decision: DEPLOY (代码变更保留) / HOLD (不部署)

### Experience Learned
- ACP 协议在 CodeBuddy 输出量大时 buffer 溢出（asyncio LimitOverrunError），需修复 orchestrator 或增大 buffer
- Meta-Agent 独立验证是必要的：CodeBuddy 写了代码但没跑 reoptimize，如果只看 CodeBuddy 的自评会误以为一切正常
- NDX_high_vol 的 DD 是结构性问题（62 只高波动 NASDAQ 股），即使等权组合也无法降到 20% 以下
- Sortino 1.40 距目标 2.0 仍有 30% gap，Gate 3（diminishing returns）远未达到

### 后续迭代建议（优先级排序）

**P0 — 修复 NDX_high_vol DD 超标**（Gate 1 阻塞项）
- 选项 A: 搜索 DD ≤ 20% 的参数组合（当前 dual_ma 和 bollinger 都超标）
- 选项 B: 在 SignalRanker 中限制 NDX_high_vol 的最大仓位占比
- 选项 C: 如无参数可行，需用户审批是否将该组降权或移除

**P1 — 实现 Walk-Forward 4 轮**（L7 流水线硬要求）
- 将 5 年回测切分为 4 轮（每轮: 训练期优化 → 验证期评估）
- 检查无单轮 >15% loss
- 这是进入 paper trading 的前置条件

**P2 — 修复 orchestrator ACP buffer 溢出**
- asyncio StreamReader 默认 64KB 限制，需增大或改用分块读取

---

> **Orchestrator 验证记录** (自动追加)
> - 迭代状态: failed
> - 测试: 0 passed, 0 failed
> - 违规: 1 条
> - 高风险文件: 0 个
> - 测试数变化: 0 → 0
> - CodeBuddy 自行更新了 trajectory ✅

---

## 迭代 #3 — P0 DD 约束 + P1 Walk-Forward 4 轮

- **日期**: 2026-07-01
- **类型**: Bug 修复（P0）+ 新功能（P1）
- **变更摘要**: matrix_backtest 选策略时增加 DD≤20% 过滤；新增 Walk-Forward 4 轮验证（Constitution L7）
- **执行时长**: CodeBuddy ~2.5h + reoptimize ~1.5h + WF ~1.5h
- **状态**: passed
- **测试数**: 483 → 498 (+15)

### 变更详情

**P0 — DD 硬约束过滤**:
- `matrix_backtest.py::_run_group` 新增 DD 过滤：选 top-K 时先筛出 `portfolio_max_drawdown ≤ 20.0%` 的合规候选
- fallback：若该组无合规候选，按 DD 升序选 top-K，标记 `dd_constrained=True` 并记录 WARNING
- `GroupBacktestResult` 新增 `dd_constrained: bool` 字段
- `_write_weights` 输出中新增 `dd_constrained` 字段
- 新增常量 `MAX_PORTFOLIO_DRAWDOWN_PCT = 20.0`、`WALK_FORWARD_VAL_DD_THRESHOLD = 15.0`

**P1 — Walk-Forward 4 轮**:
- 新增 `WalkForwardRound` dataclass（round_num, train/val 窗口, val_sortino, val_max_dd, passed）
- 新增 `WalkForwardReport` dataclass（rounds, pass_all_rounds, max_val_dd）
- 新增 `run_walk_forward()` 函数：4 轮（train_months=18, val_months=6），从最近往前推
- 新增 `_add_months()`：基于 pandas DateOffset 安全加减月份
- 新增 `_backtest_with_params_on_period()`：用给定参数在指定期间回测（WF 验证期使用）
- `main.py::_run_reoptimize` 中 MatrixBacktest.run() 后调用 `run_walk_forward()`，结果输出到日志
- WF 结果不修改 strategy_weights.json（验证步骤，不优化步骤）

### Reoptimize 结果（P0 验证）

| Group | Strategy | Sortino | DD(%) | 状态 |
|-------|----------|--------:|------:|:---:|
| SPX_mid_vol | rsi_mean_revert | 1.57 | 7.37 | ✅ |
| SPX_mid_vol | bollinger_band | 1.35 | 9.35 | ✅ |
| SPX_high_vol | bollinger_band | 1.03 | 14.90 | ✅ |
| SPX_high_vol | rsi_mean_revert | 0.94 | 19.49 | ✅ |
| **NDX_high_vol** | bollinger_band | 1.10 | **21.96** | ❌ dd_constrained=True |
| **NDX_high_vol** | dual_ma | 1.40 | **22.22** | ❌ dd_constrained=True |
| SPX_low_vol | rsi_mean_revert | 1.82 | 4.78 | ✅ |
| SPX_low_vol | bollinger_band | 1.30 | 9.77 | ✅ |
| NDX_mid_vol | rsi_mean_revert | 1.71 | 4.04 | ✅ |
| NDX_mid_vol | bollinger_band | 1.11 | 10.79 | ✅ |
| NDX_low_vol | rsi_mean_revert | 1.95 | 10.71 | ✅ |
| NDX_low_vol | bollinger_band | 1.57 | 12.74 | ✅ |

**DD 通过率**: 10/12（NDX_high_vol 仍超标，确认为结构性问题）

### Walk-Forward 结果（P1 验证）

| 轮次 | 训练期 | 验证期 | val_Sortino | val_DD | Passed |
|------|--------|--------|------------:|-------:|:------:|
| 1 | 2022-07-01~2024-01-01 | 2024-01-01~2024-07-01 | 2.33 | 2.22% | ✅ |
| 2 | 2023-01-01~2024-07-01 | 2024-07-01~2025-01-01 | 1.97 | 2.04% | ✅ |
| 3 | 2023-07-01~2025-01-01 | 2025-01-01~2025-07-01 | 3.20 | 3.32% | ✅ |
| 4 | 2024-01-01~2025-07-01 | 2025-07-01~2026-01-01 | 1.29 | 2.06% | ✅ |

**pass_all_rounds=True, max_val_dd=3.32%** — Walk-Forward 全部通过 ✅

### Gate 1 评估

| 条件 | 阈值 | 实际 | 状态 |
|------|------|------|:----:|
| Sortino | > 0.5 | 12/12，均值 1.40 | ✅ |
| Max DD | ≤ 20% | 10/12；NDX_high_vol 结构性超标 | ❌ |
| Walk-Forward | 4 轮无单轮 >15% | 4/4 通过，max DD=3.32% | ✅ |
| 每组策略数 | ≥ 2 | 6/6 | ✅ |

**Gate 1 判定: FAIL** — NDX_high_vol DD 超标仍是阻塞项

### Meta-Agent 评估

**Technical: PASS** — 498 测试全通过，无违规，代码规范  
**Business Impact: HIGH** — Walk-Forward 首次通过（4/4），NDX_high_vol 确认为结构性问题  
**Strategic Fit: GOOD** — 完成了 L7 流水线的关键步骤

**NDX_high_vol 结论**: 该组 62 只高波动 NASDAQ 股，在所有参数组合（dual_ma 20组 + bollinger 9组 + rsi 27组 + macd 27组）下 portfolio DD 均超 20%。这是结构性问题——高波动股票的等权组合天然有较高回撤。`dd_constrained=True` 标记已正确设置。

### Experience Learned
- NDX_high_vol 的 DD 超标是结构性问题，不是参数问题，需要在 SignalRanker 层面限制该组的选股权重（降权而非排除）
- Walk-Forward 验证期 DD（2~3%）远低于全量回测 DD（20%+），说明分散化效应在短窗口上更强
- WF 4 轮全通过且 max_val_dd 仅 3.32%，远低于 15% 门槛，策略稳健性高

### 后续建议

**P0 残留 — NDX_high_vol 仓位限制**（高风险变更，需用户审批）
- 选项 A：在 SignalRanker 中对 `dd_constrained=True` 的组限制最大仓位占比（如 ≤ 10%）
- 选项 B：整体降低 NDX_high_vol 的 signal weight
- 选项 C：接受超标，监控 portfolio-level DD 不超 20%（高波动组在 top_k=5 时不一定占满仓）
- **需用户决策**：选项 A/B 修改执行逻辑（L8 高风险），选项 C 需用户明确接受

**L7 流水线状态**:
```
✅ Backtest (≥5年, 5年数据)
✅ Walk-Forward (4轮, 全通过, max DD 3.32%)
❌ Paper Trade (≥1月, Gate 1 DD 约束未完全满足)
   ← NDX_high_vol 超标需用户决策后方可进入
```

---


> **Orchestrator 验证记录** (自动追加)
> - 迭代状态: passed
> - 测试: 0 passed, 0 failed
> - 违规: 0 条
> - 高风险文件: 0 个
> - 测试数变化: 0 → 0
> - CodeBuddy 自行更新了 trajectory ✅

---

## 迭代 #4 — Portfolio Backtest 模块 + per-group DD 降级为风险 metadata

- **日期**: 2026-07-02 UTC
- **类型**: 功能新增（P0+P1+P1b）+ 测试补全
- **变更摘要**: 新增 PortfolioBacktest 模块（组合层级回测），在 main._run_reoptimize 中集成 PortfolioBacktester 输出组合层 KPI，matrix_backtest._write_weights 新增 backtest_dd_status 字段作为风险 metadata
- **状态**: passed
- **执行时长**: 1 轮对话（手动开发）
- **CodeBuddy 更新数**: 3 个文件（portfolio_backtest.py 新增、matrix_backtest.py 修改、main.py 修改）+ 1 个测试文件新增
- **违规检测**: 0 条

### 变更详情

**P0: PortfolioBacktest 模块新增** (`mytrader/backtest/portfolio_backtest.py`)
- `PortfolioBacktestConfig` dataclass：initial_capital=100000, top_k=5, candidates_multiplier=2, max_single_position_pct=0.20, max_total_exposure_pct=0.80, max_sector_exposure_pct=0.40, rebalance_freq='daily', signal_valid_bars=3
- `PortfolioBacktestResult` dataclass：包含 spec 要求的 15 个字段（start_date, end_date, initial_capital, final_equity, total_return_pct, annualized_return_pct, sharpe_ratio, sortino_ratio, max_drawdown_pct, calmar_ratio, daily_returns, equity_curve, holdings_history, dd_violation, group_exposure_history）
- `PortfolioBacktester` 类：`__init__(store, universe, weights_file, config)` + `run(start, end) -> PortfolioBacktestResult`
- `run()` 核心逻辑：按交易日遍历，复用 StrategyMatrixRunner 的策略调用逻辑生成信号、SignalRanker 排名、CandidateSelector 选股，模拟换仓并计算净值
- 防前视偏差：每个交易日只用截至当日的数据切片（`bars_up_to_date`），通过 `df.index <= pd.Timestamp(trading_date)` 过滤
- 常量 `PORTFOLIO_MAX_DRAWDOWN_PCT = 20.0`（与 matrix_backtest.MAX_PORTFOLIO_DRAWDOWN_PCT 一致）

**P1: main.py 集成** (`main.py::_run_reoptimize`)
- 在 `run_walk_forward()` 之后自动运行 `PortfolioBacktester`
- 回测近 1 年数据（pb_end = today - 1day, pb_start = pb_end - 365days）
- 日志格式：`[Portfolio Backtest] DD=X%, Sortino=Y, Sharpe=Z, Annual Return=W%, DD Violation=YES/NO`
- DD 违规时输出 WARNING（Constitution L1 硬约束）

**P1b: per-group DD 降级** (`matrix_backtest.py::_run_group`)
- 在 `weights_list` 构建中新增 `backtest_dd_status` 字段
- 值为 `'pass'` 或 `'dd_constrained'`，与现有 `dd_constrained` bool 一致
- 现有 `dd_constrained` bool 字段和 fallback 逻辑保留不变（向下兼容）
- 该字段作为风险 metadata 标记，下游消费方（PortfolioBacktester / 风控观测）可读此字段判断该组权重可靠性

**测试新增**: `tests/test_portfolio_backtest.py`（27 个测试，10 个测试类）
1. `TestPortfolioBacktestResultDataclass` — dataclass 字段完整性 + 类型（2 测试）
2. `TestPortfolioBacktesterBasic` — run() 返回类型 + 3 标的×10 天流程 + 空数据（3 测试）
3. `TestMaxDrawdownCalculation` — _compute_max_drawdown_pct 在已知序列上的正确性（4 测试）
4. `TestRebalanceLogic` — holdings_history 记录 + 换仓卖出 + 无重复标的（3 测试）
5. `TestSignalValidBars` — signal_valid_bars=1 严格模式 + =3 默认（2 测试）
6. `TestDDViolation` — DD≤20% 时 False + DD>20% 时 True + 阈值常量 + 逻辑（4 测试）
7. `TestGroupExposureHistory` — 记录完整性 + 总暴露度上限（2 测试）
8. `TestBacktestDDStatusField` — P1b pass/dd_constrained + 一致性 + 类型（3 测试）
9. `TestPortfolioBacktestConfig` — 默认值 + 自定义（2 测试）
10. `TestMainIntegration` — main._run_reoptimize 包含 PortfolioBacktester 调用 + 日志格式（2 测试）

### 验证结果
```
tests/test_portfolio_backtest.py: 27 passed
全量测试: 525 passed (excluding live tests) / 5 failed (pre-existing IBKR live)
基线: 498 → 525 (新增 27 测试，全部通过)
```

### Constitution 合规
- ✅ 未突破 DD 20% 约束（新增 dd_violation 标记用于监控）
- ✅ 测试覆盖率提升（+27 测试，全部通过）
- ✅ 未引入黑箱策略（复用现有 StrategyMatrixRunner / SignalRanker / CandidateSelector）
- ✅ 未引入 RL
- ✅ 未引入不安全的第三方依赖（仅用 numpy/pandas/loguru 已有依赖）
- ✅ 文档与代码同步（trajectory + decision_log 更新）
- ✅ 低风险变更：不触及 risk/execution 模块的核心风控参数（P2 Guardrail 不在本次范围）
- ✅ 防前视偏差：每个交易日只用截至当日的数据切片

### Experience Learned
- **复用 vs 重写**：PortfolioBacktester 复用 StrategyMatrixRunner 的策略调用逻辑（直接调 `STRATEGY_REGISTRY`），而非直接调用 `run_symbol()`（后者会读 store 而无法用切片数据）。这是为了正确实现"防前视偏差"——直接读 store 会拿到全量历史数据。
- **数据切片实现**：一次性 `get_bars_multi` 拉取全量数据，再在内存中按 `df.index <= pd.Timestamp(trading_date)` 过滤。这避免了 N 次 SQL 查询，性能更好。
- **类属性污染陷阱**：初次实现时误把 `_holdings_history` 和 `_group_exposure_history` 定义为类属性（class attribute），导致多个 PortfolioBacktester 实例间共享历史。修正为 `__init__` 中初始化的实例属性。
- **`backtest_dd_status` 字段位置选择**：spec 说"在 _write_weights 中新增"，但实际代码中 `_write_weights` 只是 `json.dump(report.groups)`，真正的字段构建在 `_run_group`。选择在 `_run_group` 添加字段，这样 in-memory report 和 JSON 输出都包含该字段，下游消费方更灵活。
- **DD 符号约定**：PortfolioBacktestResult.max_drawdown_pct 沿用迭代 #2 的正值约定（0.0~100.0），与 matrix_backtest._portfolio_max_drawdown_from_results 一致。

### 后续建议

**P2 Guardrail（不在本次范围，需用户审批）**:
- 在 Risk Manager / Portfolio Tracker 层增加 portfolio-level DD 监控的 hard guardrail
- 当实时 portfolio DD > 20% 时触发强制减仓
- 这是 L8 高风险变更，需用户明确授权

**PortfolioBacktest 增强方向**:
1. 支持 `rebalance_freq='weekly'`（当前仅实现 daily）
2. 加入交易成本（fees/slippage）模拟
3. 加入 ATR 仓位法（当前用固定 target_position_pct）
4. 输出 HTML 报告（与 MatrixBacktest 一致）
5. 加入 Benchmark 对比（SPY buy-and-hold）

**L7 流水线状态**:
```
✅ Backtest (≥5年, MatrixBacktest)
✅ Walk-Forward (4 轮, 迭代 #3)
✅ Portfolio Backtest (组合层验证, 迭代 #4 新增)
❌ Paper Trade (≥1月, Gate 1 DD 约束未完全满足)
   ← NDX_high_vol 超标需用户决策（迭代 #3 残留）
```

---


> **Orchestrator 验证记录** (自动追加)
> - 迭代状态: passed
> - 测试: 0 passed, 0 failed
> - 违规: 0 条
> - 高风险文件: 0 个
> - 测试数变化: 0 → 0
> - CodeBuddy 自行更新了 trajectory ✅

---

## 迭代 #5 — Paper Trading Integrity & Parity

- **日期**: 2026-07-03 UTC
- **类型**: Bug 修复（P0-A/B/C）+ 功能新增（P0-D）+ 测试补全
- **变更摘要**: 统一线上 StrategyMatrixRunner 与 PortfolioBacktester 的 signal metadata parity（修复 sector=Unknown 导致 73 候选 → 2 approved）；为 AlpacaBroker 增加 get_positions / get_order_by_client_order_id / refresh_pending_orders 只读能力；在 ScanOrchestrator 加 _refresh_pending_orders 实现订单生命周期闭环；修复 main.py reconciliation callback 调用接口；新增 paper daily metrics 模块
- **状态**: passed
- **测试数**: 525 → 562（+37 新测试）

### 变更详情

**P0-A: 统一 Signal metadata** (`mytrader/strategy/matrix_runner.py`, `mytrader/backtest/portfolio_backtest.py`)
- 新增 module-level `build_matrix_signal_indicators(meta, entry, weight)` helper
- 在 matrix_runner.py 中新增默认值常量：`DEFAULT_BACKTEST_SHARPE/SORTINO/MAX_DD/DD_STATUS/WIN_RATE/SECTOR`
- `StrategyMatrixRunner.run_symbol()` 与 `PortfolioBacktester._generate_signals()` 都改为调用同一 helper
- 线上 Signal.indicators 现在统一包含：`group_id / sector / backtest_sharpe / backtest_sortino / backtest_max_drawdown / backtest_dd_status / backtest_win_rate / weight`
- 缺字段时返回安全默认值（不抛异常），`meta=None` 时 sector="Unknown"

**P0-B: AlpacaBroker 只读状态能力** (`mytrader/execution/alpaca_broker.py`)
- `get_positions() -> list[dict]`：读取 Alpaca 当前持仓，返回 ReconciliationService 兼容格式 `[{symbol, quantity, ...}]`
  - `quantity` 强制 int（兼容 ReconciliationService）
  - 异常时返回空列表（不抛）
  - 兼容 SDK 对象和 dict 两种 position 结构
- `get_order_by_client_order_id(oid) -> OrderResult | None`：本地为 PENDING 时尝试远端拉取
  - 优先 `client.get_order_by_client_id`，fallback `get_order_by_client_order_id`
  - 远端异常返回本地缓存 + warning
  - 通过 `_rebuild_order_result_from_alpaca()` 复用 `_parse_alpaca_order()` 解析逻辑
- `refresh_pending_orders() -> list[OrderResult]`：刷新所有本地 PENDING 订单
  - 不提交新订单，不取消订单
  - 终态订单（FILLED/REJECTED/CANCELLED）跳过

**P0-B+: ScanOrchestrator pending 刷新** (`mytrader/scan_orchestrator.py`)
- 新增 `_refresh_pending_orders() -> int`
- 在 `_run_scan()` 与 `_run_eod_check()` 开头调用
- 幂等性：维护 `self._processed_order_ids: set[str]`，同一 client_order_id 只调用 tracker.process_order 一次
- broker 不支持 refresh 时不抛异常（PaperBroker 兼容）
- broker.refresh 抛异常时扫描仍继续（warning + 返回 0）

**P0-C: 修复 Reconciliation callback** (`main.py::_build_reconciliation_callback`)
- 构造参数：`tracker=` → `portfolio_tracker=`
- 调用：`svc.reconcile()` → `svc.run()`
- 判断：`report.has_diff` → `not report.is_clean`
- 兼容 `components.notification / bus` 为 None 的场景
- 对账失败用 `logger.error(..., exc_info=True)`，不让 scheduler 崩溃
- `components.bus` 用 `getattr(components, "bus", None)` 安全访问（避免 AttributeError）

**P0-D: Paper daily metrics** (`mytrader/monitor/paper_metrics.py` 新增)
- `PaperDailyMetrics` dataclass：date / account / signals / orders / positions / risk / data
- `collect_paper_daily_metrics()` 函数接口：写出 JSON 到 `reports/paper/daily/YYYY-MM-DD.json`
- JSON 结构按 spec §4.5 定义稳定字段
- 缺 broker account API 时填 0/None，记录 warning（不崩溃）
- 敏感字段过滤：`_sanitize()` 递归剔除 api_key / secret / token / password 等
- 写文件前 mkdir parents=True
- 在 main.py reconciliation callback 末尾 best-effort 调用

**测试新增**: 37 个新测试
1. `tests/test_signal_parity.py`（10 测试）：metadata 完整性、默认值安全性、parity 一致性、CandidateSelector 不再压 Unknown sector
2. `tests/test_alpaca_broker.py`（+9 测试）：get_positions 映射、异常处理、refresh_pending 订单状态更新、cache fallback、terminal 订单跳过
3. `tests/test_scan_orchestrator.py`（+4 测试）：pending 幂等、broker 不支持、异常不中断扫描、非 FILLED 跳过
4. `tests/test_main_reconciliation.py`（7 测试）：service 构造参数、is_clean 读取、clean/diff 通知、None notification 容错、异常隔离、sync_fn 顺序、paper metrics 调用
5. `tests/test_paper_metrics.py`（11 测试）：JSON 写出、目录创建、缺 API 不崩溃、订单状态计数、敏感字段过滤、_sanitize 单元测试、PaperDailyMetrics dataclass

### 验证结果

```
Targeted tests (spec §8):
  tests/test_signal_parity.py tests/test_portfolio_backtest.py tests/test_alpaca_broker.py
  tests/test_scan_orchestrator.py tests/test_main_reconciliation.py tests/test_paper_metrics.py
  → 75 passed, 0 failed

Default pytest (excluding live):
  → 562 passed, 0 failed, 103 warnings in 15.70s

Live tests (pre-existing, 与本次无关):
  → 11 passed, 5 failed (all IBKR connection errors, pre-existing)
```

### Constitution 合规
- ✅ 未突破 DD 20% 约束（PORTFOLIO_MAX_DRAWDOWN_PCT=20.0 未改动）
- ✅ 测试覆盖率提升（+37 测试，全部通过）
- ✅ 未引入黑箱策略（复用现有 StrategyMatrixRunner / PortfolioBacktester 逻辑）
- ✅ 未引入 RL
- ✅ 文档与代码同步（trajectory + decision_log + CODEBUDDY + design docs 更新）
- ✅ 未触发真实下单（AlpacaBroker 新方法只读，不提交新订单）
- ✅ 未在测试中调用真实 broker 下单（全部 Mock）
- ✅ API key 未写入日志/metrics（_sanitize 兜底过滤）
- ✅ 防前视偏差：metadata parity 修复不影响 PortfolioBacktester 的数据切片逻辑

### Success Criteria 对照（spec §6）

| # | 条件 | 状态 |
|---|------|:----:|
| 1 | 默认 pytest 通过；不依赖真实 Alpaca API | ✅ |
| 2 | 新增/修改测试数不下降 | ✅ 525→562 |
| 3 | StrategyMatrixRunner signal indicators 包含 8 个完整字段 | ✅ |
| 4 | PortfolioBacktester 与 StrategyMatrixRunner metadata parity | ✅ |
| 5 | AlpacaBroker.get_positions() 返回 ReconciliationService 兼容格式 | ✅ |
| 6 | pending order refresh 能更新为 filled + 幂等处理 | ✅ |
| 7 | reconciliation callback 调用 run() + is_clean | ✅ |
| 8 | paper metrics JSON 能写出 + 不含敏感字段 | ✅ |
| 9 | 更新 trajectory / decision_log / CODEBUDDY / design docs | ✅ |

### Experience Learned
- **metadata parity 是数据流一致性的核心**：之前 `matrix_runner.run_symbol()` 输出 `{group_id, backtest_sharpe, backtest_win_rate, weight}`，而 `PortfolioBacktester._generate_signals()` 输出 `{group_id, sector, backtest_sharpe, backtest_win_rate, weight}` —— 两者字段集合不同，导致回测和线上对 CandidateSelector 行为预测不一致。本次提取共享 helper 后，任何字段调整只需改一处。
- **Alpaca SDK 多版本兼容**：`get_order_by_client_id` 在不同 SDK 版本中名字不同，使用 `hasattr` + try/except 兼容更稳健，避免硬依赖单一 SDK 版本。
- **幂等性集合优于状态查询**：`_processed_order_ids: set[str]` 比每次查询 tracker 是否已处理该订单更简单且无依赖（不假设 tracker 暴露查询接口）。
- **_sanitize 双层防御**：`_collect_*` 函数白名单读取（最小暴露） + `_sanitize` 兜底递归剔除（防御未来引入新字段时误泄敏感信息）—— 单层防御不足。
- **paper metrics 设计取舍**：本次只提供模块与测试，集成点选在 reconciliation callback 末尾（已是每日盘后流程）。如果后续需要更精细的 daily return / rolling DD，需要扩展 PortfolioTracker 维护这两个指标。

### 后续建议

**P1 — AlpacaBroker auto 端到端验证**（Iteration #6 候选）
- spec 明确"不修 orchestrator harness 的假 passed 问题；该问题留给 Iteration #6"
- 在真实 paper 账户跑一次完整 morning_scan → eod_check 流程，验证 pending → FILLED 状态闭环
- 需要至少 1 个月 paper 数据后才能验证 P0-D 的 metrics 是否能用于计算 paper Sortino/DD

**P1 — PortfolioTracker 扩展 daily_pnl_pct / max_drawdown**
- 当前 `_collect_risk()` 直接读 `portfolio.daily_pnl_pct / max_drawdown`，但 PortfolioTracker 未维护
- 建议下次迭代在 PortfolioTracker 中维护 rolling 30 天 daily_returns + 计算 max_drawdown

**P2 — ReconciliationService auto_sync**
- 当前 `auto_sync=False`（保守，以券商为准的同步会静默覆盖本地记录）
- 真实 paper 阶段建议先观察 1 个月，确认无 race condition 后再启用

**L7 流水线状态**
```
✅ Backtest (≥5年, MatrixBacktest)
✅ Walk-Forward (4 轮, 迭代 #3)
✅ Portfolio Backtest (组合层验证, 迭代 #4)
🔄 Paper Trade (≥1月, 本次迭代修复 paper 完整性 → 可进入 1 月验证)
   ← 1 个月 paper 数据后用 PaperDailyMetrics 计算 Sortino/DD 判断策略质量
```

---
> **Orchestrator 验证记录** (自动追加)
> - 迭代状态: partial
> - 测试: 0 passed, 0 failed
> - 违规: 0 条
> - 高风险文件: 1 个
> - 测试数变化: 0 → 0
> - CodeBuddy 自行更新了 trajectory ✅

---

## 迭代 #6 — 按 iterations/iteration_6/spec.md 进行开发。先读 spec 文件理解完整需求，然后实施 Harness Reliability & Live Test Isolation：隔离默认 live tests、修复 orchestrator pytest 统计/状态判定/快照 untracked 留痕、生成 gate_status.json、补充 harness 测试并同步两份 orchestrator 副本。严格遵守 spec scope；不得修改交易策略、风控阈值或下单逻辑；不得触发真实下单；完成后运行 targeted harness tests 和默认非 live pytest，并更新 trajectory / CODEBUDDY / 必要文档。

- **日期**: 2026-07-03 19:45 UTC
- **类型**: 自动化迭代 (Orchestrator → CodeBuddy via ACP)
- **变更摘要**: 按 iterations/iteration_6/spec.md 进行开发。先读 spec 文件理解完整需求，然后实施 Harness Reliability & Live Test Isolation：隔离默认 live tests、修复 orchestrator pytest 统计/状态判定/快照 untracked 留痕、生成 gate_status.json、补充 harness 测试并同步两份 orchestrator 副本。严格遵守 spec scope；不得修改交易策略、风控阈值或下单逻辑；不得触发真实下单；完成后运行 targeted harness tests 和默认非 live pytest，并更新 trajectory / CODEBUDDY / 必要文档。
- **执行时长**: 11146s (185.8min)
- **状态**: passed
- **CodeBuddy 更新数**: 4773
- **工具调用数**: 365
- **团队事件数**: 0
- **权限请求数**: 1

### 变更文件
.codebuddy/skills/cb-acp-dev/scripts/orchestrator.py, alignment/orchestrator.py, mytrader/pyproject.toml, mytrader/tests/test_integration_live.py

### 测试结果
0 passed, 0 failed

### 违规详情
- ✅ 无违规

### Constitution 合规
- DD 20% 约束: ✅（未触及风控参数）
- 测试覆盖率: ✅ 不降（Meta-Agent 独立验证 562 passed，harness +38 新测试）
- 黑箱策略: ✅ 未引入
- RL 引入: ✅ 未引入
- 文档同步: ⚠️ CodeBuddy 未更新 trajectory，orchestrator 自动补写 + Meta-Agent 补充验收

### Meta-Agent 评估（2026-07-04 08:30 UTC）

> **评估人**: GLM (Meta-Agent)，独立于 CodeBuddy 验收

**重要说明 — Orchestrator 自我修复悖论**：本轮迭代修复的是 orchestrator 自身的 bug（假 passed、count_tests=0、untracked 遗漏）。但 orchestrator 运行时加载的是旧代码，CodeBuddy 对 `orchestrator.py` 的修改不会在本次运行中生效。因此 `result.json` 仍显示旧的"假 passed"行为（`test_count=0`, `status=passed` 但 `exit_code=1`）。Meta-Agent 通过独立调用新代码的函数验证了所有修复生效。

### Meta-Agent 独立验证结果

| 验证项 | 旧代码 | 新代码（独立验证） |
|--------|--------|-------------------|
| `count_tests()` | 0 | **562** ✅ |
| `has_test_failures(exit=1,failed=5)` | N/A | **True** ✅ |
| `get_changed_files()` | 漏 untracked | **包含 alignment/tests/** ✅ |
| `parse_pytest_summary()` | 简单子串匹配 | **严格正则，5 种格式全通过** ✅ |
| 默认 pytest live 隔离 | 不隔离 | **562 passed, 0 live** ✅ |
| Harness 测试 | 无 | **38 passed** ✅ |
| 两份副本同步 | 不同步 | **IDENTICAL**（Meta-Agent `cp` 修复） ✅ |
| `gate_status.json` 生成 | 不存在 | **代码已实现 + 手动生成** ✅ |

### Technical: PASS
- 新代码 +1242 行，38 个新 harness 测试
- 严格的状态判定：violations → has_test_failures → test_count 下降 → high_risk → buffer_overflow → passed
- 不再有"exit_code=1 但 status=passed"的假通过

### Business Impact: HIGH
- 后续迭代的 `result.json` 将可信（不再假 passed）
- 默认 pytest 不再触发真实 IBKR/Telegram（live 隔离）
- 快照包含 untracked 新文件证据（可复现性）

### Strategic Fit: GOOD
- 这是后续所有策略/paper 迭代可信度的基础设施修复
- 不触及交易逻辑、风控参数、下单代码

### Bugs Fixed by Meta-Agent
1. 两份 orchestrator 副本不同步 → `cp` 对齐
2. `test_cache.py::TestCacheExpiryDaily` 时间相关失败 → 确认为时间依赖（18:00 UTC 后失败），非 CodeBuddy 引入

### Experience Learned
- **Orchestrator 自我修复悖论**：orchestrator 的代码修改在同一运行中不生效，必须跨迭代验证
- **两份副本同步是持续风险**：harness 测试中的 `test_two_copies_are_identical` 是有效防线
- **CodeBuddy 能完成大规模 harness 重构**：+1242 行代码，38 个新测试
- **时间相关测试**：`test_cache.py` 在 18:00 UTC 后运行会失败，应 mock 时间

### 后续建议
1. 下一轮迭代将首次使用修复后的 orchestrator，验证 `result.json` 真实性
2. Strategy Return Uplift（并行研究）：Signal Ranker 切 Sortino 优先 + 趋势/动量策略增强
3. 真实 paper 运行验证：AlpacaBroker paper auto 模式

### L7 流水线状态
```
✅ Backtest (≥5年, MatrixBacktest)
✅ Walk-Forward (4轮, pass_all=True, max_val_dd=3.32%)
✅ Portfolio Backtest (DD=6.65%, Sortino=1.98, Annual=15.17%)
✅ Paper Trading Integrity (signal parity + order lifecycle + reconciliation + metrics)
✅ Harness Reliability (live isolation + 假 passed 修复 + untracked 快照 + gate_status)
⬜ Paper Trade ≥1月（需部署验证）
⬜ Live
```

---

## 迭代 #7 — SignalRanker Sortino Priority + Benchmark Comparison

- **日期**: 2026-07-04 UTC
- **类型**: 评分逻辑切换（P0）+ 功能新增（P1）+ 测试补全
- **变更摘要**: 将 SignalRanker 评分从 `backtest_sharpe` 切换为 `backtest_sortino` + `backtest_dd_penalty`（Constitution L1 Sortino 首要 KPI）；为 PortfolioBacktest 新增 SPY benchmark 对比（alpha / IR / benchmark Sortino/DD）；增强 main.py 日志；补充 12 个新测试
- **状态**: passed
- **执行时长**: 1 轮对话（手动开发）
- **测试数**: 562 → 574（+12 新测试，全部通过）

### 变更详情

**P0: SignalRanker 评分切换** (`mytrader/signal/ranker.py`)
- `DEFAULT_SCORE_WEIGHTS` 调整：
  - 删除 `backtest_sharpe` (0.20)
  - 新增 `backtest_sortino` (0.25，最高单因子)
  - 新增 `backtest_dd_penalty` (0.10)
  - `strategy_weight` 0.35 → 0.30，`signal_confidence` 0.25 → 0.20，`backtest_win_rate` 0.20 → 0.15
- `_score()` 归一化：
  - `backtest_sortino`: `min(max(sortino / 3.0, 0.0), 1.0)` — 负值截断为 0，>3 截断为 1
  - `backtest_dd_penalty`: `max(1.0 - dd / 20.0, 0.0)` — DD=0 → 1.0，DD≥20% → 0.0
- 向后兼容：`backtest_sharpe` 字段在 indicators 中保留但不影响评分；自定义 `score_weights` 仍可传入

**P1: PortfolioBacktest benchmark 对比** (`mytrader/backtest/portfolio_backtest.py`)
- `PortfolioBacktestResult` 新增 7 个 benchmark 字段：
  - `benchmark_symbol` (默认 "SPY")
  - `benchmark_total_return_pct` / `benchmark_annualized_return_pct`
  - `benchmark_sortino_ratio` / `benchmark_max_drawdown_pct`
  - `alpha_pct` (超额收益 = 组合年化 - benchmark 年化)
  - `information_ratio` (年化 IR)
- 新增 `_compute_benchmark(start, end, portfolio_returns, dates)` 方法：
  - 从 `MarketDataStore` 拉取 SPY 同期数据（与组合标的数据同源）
  - SPY 数据不可用时降级为 0.0，不抛异常（spec §4.2）
  - Sortino / Max DD 复用 `matrix_backtest._compute_sortino` 和 `_compute_max_drawdown_pct`（同口径）
- 新增 `_compute_information_ratio()` 静态方法：
  - IR = mean(excess_returns) / std(excess_returns) * sqrt(252)
  - 用 `pd.concat(..., join="inner")` 对齐组合与 SPY 的交易日历
  - 样本 < 5 或 std ≤ 0 时返回 0.0
- `run()` 末尾调用 `_compute_benchmark()` 填充 benchmark 字段
- 日志增加 benchmark return / alpha / IR

**P1+: main.py 日志增强** (`main.py::_run_reoptimize`)
- `[Portfolio Backtest]` 日志增加 `Benchmark(SPY) Return=X%, Alpha=Y%, IR=Z`
- 与 Constitution L1 "收益可归因" 对齐

**测试新增**: 12 个新测试
1. `tests/test_strategy_matrix_ranker.py` (+5 测试)：
   - `test_score_uses_sortino_not_sharpe` — sortino=2.0, sharpe=0.0 → score > 0 且 breakdown 含 sortino
   - `test_score_dd_penalty` — A(DD=5%) > B(DD=18%)，验证 dd_penalty factor
   - `test_score_sortino_normalization` — 3.0→1.0, 6.0→1.0(截断), -1.0→0.0(截断)
   - `test_custom_score_weights_still_work` — 只用 strategy_weight=1.0
   - `test_ranking_order_changed_by_sortino` — A 高 Sharpe 低 Sortino，B 低 Sharpe 高 Sortino → B 排前
2. `tests/test_portfolio_backtest.py` (+7 测试，新 `TestBenchmarkComparison` 类)：
   - `test_benchmark_fields_exist` — 7 个新字段存在且有默认值
   - `test_benchmark_computed_with_spy_data` — SPY 上涨 → benchmark_return > 0
   - `test_benchmark_zero_when_no_spy` — SPY 不可用时降级为 0.0
   - `test_alpha_calculation` — portfolio=15%, benchmark=10% → alpha=5.0
   - `test_information_ratio_computation` — IR 在已知序列上正确（同收益→0，超额→>0）
   - `test_benchmark_max_drawdown` — SPY 先涨后跌 → DD > 0
   - `test_benchmark_max_drawdown_static_method` — 持续上涨 → DD = 0

### 验证结果
```
Targeted tests:
  tests/test_strategy_matrix_ranker.py tests/test_portfolio_backtest.py
  → 58 passed, 0 failed

Default pytest (excluding live):
  → 574 passed, 16 deselected, 0 failed, 103 warnings in 15.39s
```

### Constitution 合规
- ✅ 未突破 DD 20% 约束（PORTFOLIO_MAX_DRAWDOWN_PCT=20.0 未改动）
- ✅ 测试覆盖率提升（+12 测试，全部通过）
- ✅ 未引入黑箱策略（纯函数计算，公式可解释）
- ✅ 未引入 RL
- ✅ 未引入不安全的第三方依赖（仅复用 numpy/pandas/loguru 已有依赖）
- ✅ 文档与代码同步（trajectory + design docs + CODEBUDDY 更新）
- ✅ 未触及风控参数 / DD 阈值 / 仓位上限 / 下单逻辑（spec §3 严格 scope）
- ✅ 防前视偏差：benchmark 用 SPY 同期数据，不影响组合信号生成逻辑

### Success Criteria 对照（spec §5）

| # | 条件 | 状态 |
|---|------|:----:|
| 1 | SignalRanker._score() 使用 backtest_sortino 而非 backtest_sharpe | ✅ |
| 2 | SignalRanker._score() 包含 backtest_dd_penalty 因子 | ✅ |
| 3 | PortfolioBacktestResult 包含 7 个 benchmark 字段 | ✅ |
| 4 | SPY 数据不可用时 benchmark 字段降级为 0.0，不抛异常 | ✅ |
| 5 | 默认 pytest 通过（574 测试，0 failed） | ✅ |
| 6 | 新增测试 ≥ 8 个（SignalRanker 5 + PortfolioBacktest 3+） | ✅ 12 个 |
| 7 | 两份 orchestrator 副本保持同步 | ✅（未触及 orchestrator） |
| 8 | 更新 trajectory / design docs | ✅ |

### Experience Learned
- **Sortino 归一化的边界处理**：Sortino 可能为负（亏损策略），必须用 `max(·, 0.0)` 截断；理论上限 +inf 但实践中 >3 已属优秀，用 `min(·, 1.0)` 截断。如果不截断，一个 Sortino=10 的异常值会主导整个评分。
- **DD 惩罚的线性映射**：`1 - dd/20` 是简单的线性映射，DD=0 → 1.0，DD=20 → 0.0，DD>20 → 0.0（截断）。这比指数映射更直观，也避免 DD 略超 20% 时惩罚过激（spec §8.3 避免过拟合原则）。
- **benchmark 降级处理**：spec §4.2 明确要求 SPY 不可用时所有字段为 0.0 且不抛异常。这意味着 `alpha_pct` 也降级为 `portfolio_annualized_return - 0 = portfolio_annualized_return`，这是合理的——无 benchmark 时 alpha 退化为绝对收益。
- **Information Ratio 的日期对齐**：组合与 SPY 的交易日历可能不完全一致（节假日差异），用 `pd.concat(..., join="inner")` 取交集是稳健做法。若用 reindex + ffill 会引入虚假收益数据。
- **复用现有 helper**：`_compute_sortino` 和 `_compute_max_drawdown_pct` 已在 matrix_backtest.py / portfolio_backtest.py 中实现，benchmark 计算直接复用，确保口径一致。
- **测试构造的关键**：`test_ranking_order_changed_by_sortino` 故意构造 A 高 Sharpe 低 Sortino / B 低 Sharpe 高 Sortino 的对比，证明评分确实切换了——如果只测 sortino factor 单独的值，无法发现"代码同时使用 sharpe 和 sortino"的 bug。

### 后续建议

**P1 — Strategy Diversity（spec §1 第3点未解决）**
- 当前权重中 rsi_mean_revert 和 bollinger_band 占绝大多数，趋势/动量策略（dual_ma, macd_cross）几乎缺席
- 趋势市中是结构性弱点
- 候选方案：在 SignalRanker 中增加"策略多样性"约束（每个策略至少占 X%）

**P2 — reoptimize 后的 benchmark 报告**
- 当前 `_run_reoptimize` 输出 benchmark 日志，但未持久化
- 建议在 `reports/` 下生成 benchmark 对比 HTML 报告（与 MatrixBacktest 一致）

**P2 — benchmark 选择可配置**
- 当前硬编码 SPY，未来可支持 QQQ / VTI / VWO 等
- 在 `PortfolioBacktestConfig` 中加 `benchmark_symbol: str = "SPY"` 字段

### L7 流水线状态
```
✅ Backtest (≥5年, MatrixBacktest)
✅ Walk-Forward (4轮, pass_all=True, max_val_dd=3.32%)
✅ Portfolio Backtest (DD=6.65%, Sortino=1.98, Annual=15.17%)
   ← 迭代 #7 新增 SPY benchmark 对比（alpha/IR 可量化）
✅ Paper Trading Integrity (signal parity + order lifecycle + reconciliation + metrics)
✅ Harness Reliability (live isolation + 假 passed 修复 + untracked 快照 + gate_status)
🔄 SignalRanker Sortino Priority (迭代 #7：评分切换已落地，待 reoptimize 验证排名变化)
⬜ Paper Trade ≥1月（需部署验证）
⬜ Live
```

---


> **Orchestrator 验证记录** (自动追加)
> - 迭代状态: failed
> - 测试: 0 passed, 0 failed
> - 违规: 1 条
> - 高风险文件: 0 个
> - 测试数变化: 562 → 574
> - CodeBuddy 自行更新了 trajectory ✅

---

## 迭代 #8 — Trend-Filtered Mean Reversion 策略 (RSI + 200 SMA)

- **日期**: 2026-07-04 UTC
- **类型**: 策略新增
- **变更摘要**: 新增 `rsi_trend_filter` 策略（RSI 超卖/超买 + 200 日 SMA 趋势过滤），在经典 RSI 均值回归信号上叠加趋势过滤，降低单边趋势中的逆势假信号风险
- **状态**: passed
- **执行时长**: 1 轮对话（手动开发）
- **测试数**: 574 → 585（+5 新测试用例 + 已有参数化测试覆盖新注册）

### 变更详情

**P0: 新增 rsi_trend_filter 策略** (`mytrader/strategy/strategies/rsi_trend_filter.py`)
- `rsi_trend_filter_signal(close, rsi_period=14, oversold=30.0, overbought=70.0, trend_period=200)`
- 信号规则：RSI < oversold AND close > SMA(200) → BUY (+1)；RSI > overbought AND close < SMA(200) → SELL (-1)；否则 → HOLD (0)
- 严格 `shift(1)` 防前视偏差，纯函数无副作用

**P0: 策略注册与参数网格** (`main.py`, `mytrader/strategy/__init__.py`)
- `REOPTIMIZE_STRATEGIES` 新增 `"rsi_trend_filter"`，`REOPTIMIZE_PARAM_GRIDS` 新增 27 个组合（3×3×3×1）
- `trend_period` 固定为 200（经典长周期趋势线，不纳入搜索）

**P1: 测试** (`tests/test_strategy.py`)
- 新增 `TestRSITrendFilter` 类 5 个测试：信号值域、自定义参数、趋势过滤行为（T3/T4）、数据不足边界
- 更新 `TestStrategyRegistry.test_all_strategies_registered` expected 集合
- 前视偏差和参数化测试自动覆盖新策略

### 验证结果

```
Full pytest: 585 passed, 16 deselected, 0 failed, 103 warnings in 15.53s
Targeted tests: tests/test_strategy.py → 54 passed, 0 failed
```

### Constitution 合规
- ✅ 未突破 DD 20% 约束 | ✅ 测试覆盖率提升 | ✅ 纯函数 + shift(1)
- ✅ 决策可解释 (RSI+SMA) | ✅ 未引入 RL | ✅ 未引入不安全依赖
- ✅ 未修改现有策略/风控/执行逻辑 | ✅ 未触发真实交易
- ✅ 文档与代码同步

### Experience Learned
- **趋势过滤的自然收敛**：SMA 过滤在趋势市场中不产生反向信号，边界区域短暂交叉是设计意图内的行为
- **参数网格固定 trend_period=200**：避免 81 个组合的无意义规模膨胀
- **与 rsi_mean_revert 互补**：前者无条件，后者趋势过滤，适合 ensemble 混合
- **测试确定性**：T3/T4 用 `np.random.default_rng(42)` 固定种子确保行为稳定

### 后续建议
1. 下一次 `--reoptimize` 后评估新策略在各组的权重分配
2. 如果实证发现 50/100 SMA 更好，可扩展 `trend_period` 为网格或按组配置
3. 策略多样性约束（5 策略 pool 已成形）

### L7 流水线状态
```
✅ Backtest (≥5年, rsi_trend_filter 已纳入 REOPTIMIZE_STRATEGIES)
✅ Walk-Forward (4轮, 含新策略)
✅ Portfolio Backtest | ✅ Paper Trading Integrity
✅ Harness Reliability | ✅ SignalRanker Sortino Priority
🔄 Strategy Diversity (迭代 #8 补全 RSI 趋势过滤策略)
⬜ Paper Trade ≥1月 | ⬜ Live
```

---

> **Orchestrator 验证记录** (自动追加)
> - 迭代状态: failed
> - 测试: 0 passed, 0 failed
> - 违规: 1 条
> - 高风险文件: 0 个
> - 测试数变化: 574 → 585
> - CodeBuddy 自行更新了 trajectory ✅

---

## 迭代 #9 — MatrixBacktest Alpha-Based Strategy Selection

- **日期**: 2026-07-05 UTC
- **类型**: 策略选择逻辑重构（中风险）
- **变更摘要**: 将 MatrixBacktest 的 top-K 策略选择从 Sortino 排序改为 Alpha（vs SPY）排序；新增 Sortino > 0.5 最低质量门槛；per-strategy best params 和 ensemble weights 从 Sharpe 改为 Alpha
- **状态**: passed
- **执行时长**: 1 轮对话（手动开发）
- **测试数**: 585 → 602（+17 新测试用例）

### 背景

Iter #7 的 `--reoptimize` 暴露了根本矛盾：
- Constitution 目标：年化 20-30%（需 alpha +10~20%）
- MatrixBacktest 排序：Sortino 降序
- 结果：选出 Sortino 最高的均值回归策略 → 年化 8.02% → alpha = -11.34%

**Sortino 高 ≠ 年化高。** 均值回归策略天然有高 Sortino（低下行波动）但低绝对收益。
Iter #8 新增的 `rsi_trend_filter` 也因此未能进入权重。

### 变更详情

**P0: SPY Benchmark 数据获取 + Alpha 计算** (`matrix_backtest.py`)
- 新增 `MatrixBacktest._get_spy_returns(start, end)` 方法：从 MarketDataStore 拉取 SPY 日收益率
- 新增模块级函数 `_compute_alpha(strat_returns, spy_returns)`：计算 `(strat_annual - spy_annual) * 100`
- 新增 `_combine_daily_returns(results)` helper：提取等权合并逻辑供 sharpe/sortino/alpha 复用
- 降级处理：SPY 不可用时 alpha=0.0，不阻塞回测

**P0: Top-K 选择逻辑修改** (`matrix_backtest.py::_run_group`)
- 三级 Fallback 策略：
  - Tier 1: DD ≤ 20% AND Sortino > 0.5 → Alpha 降序
  - Tier 2 (fallback): Tier 1 空 → 仅 DD ≤ 20% → Alpha 降序 + WARNING
  - Tier 3 (fallback): Tier 2 空 → DD 升序 + dd_constrained=True
- 新增常量 `MIN_SORTINO_THRESHOLD = 0.5`

**P0: Per-Strategy Best Params 修改** (`matrix_backtest.py::_run_group`)
- 每个策略的最优参数选择从 Sharpe 改为 Alpha
- 与 top-K 排序口径一致，避免 per-strategy 用 Sharpe 选低收益高稳定的参数

**P0: Ensemble Weights 修改** (`matrix_backtest.py::_optimize_ensemble_weights`)
- 权重计算从 Sharpe 改为 Alpha
- 新增 `spy_returns: pd.Series | None` 参数
- SPY 不可用时退化为等权（`max(0, 0.01)` 归一化）

**P1: 新增字段**
- `GroupBacktestResult.backtest_alpha: float = 0.0`
- `strategy_weights.json` 每条目新增 `backtest_alpha` 字段

**P2: 测试** (`tests/test_matrix_backtest.py`)
- 新增 3 个测试类共 17 个测试：
  - `TestAlphaComputation` (6): alpha 计算、SPY 不可用、策略跑输、combine helper、常量
  - `TestAlphaBasedTopKSelection` (7): top-K 用 alpha、Sortino 门槛、DD 过滤、Tier 2/3 fallback、JSON 字段、per-strategy best params
  - `TestEnsembleWeightsUsesAlpha` (3): ensemble �� alpha、SPY 不可用降级、单策略

### 验证结果

```
Targeted tests: tests/test_matrix_backtest.py → 75 passed, 0 failed
Full pytest: 602 passed, 16 deselected, 0 failed, 103 warnings in 15.47s
```

### Constitution 合规
- ✅ 未突破 DD 20% 约束（硬约束保留）
- ✅ 测试覆盖率提升（+17 测试，585 → 602）
- ✅ 决策可解释（alpha = 年化收益差，公式明确）
- ✅ 未引入 RL
- ✅ 未引入不安全依赖
- ✅ 未修改策略代码 / 风控 / 执行逻辑
- ✅ 未触发真实交易
- ✅ 文档与代码同步（07-backtest-module.md + CHANGELOG v2.3）

### Experience Learned
- **Sortino 高 ≠ 年化高**：均值回归策略天然高 Sortino 低绝对收益，用 Sortino 排序会系统性排除趋势策略
- **Alpha 作为排序指标不违反 Constitution L1**：Sortino 仍是 KPI（从排序变成过滤），DD 硬约束不变
- **三级 Fallback 设计**：Tier 1 严格（DD+Sortino）→ Tier 2 放宽 Sortino → Tier 3 DD fallback，保证回测不阻塞
- **SPY 降级处理**：数据不可用时 alpha=0，所有候选 alpha 相等 → Python 稳定排序保留原顺序，退化为等权
- **复用 `_combine_daily_returns`**：提取等权合并逻辑供 sharpe/sortino/alpha 共享，避免重复 `pd.concat`

### 后续建议
1. 用户独立运行 `--reoptimize` 验证 alpha 改善（预期 alpha 从 -11.34% 提升）
2. 评估 `rsi_trend_filter` 是否能进入权重（之前因 Sortino 低被排除）
3. 如果 Sortino > 0.5 门槛过严，可考虑调整为 0.3 或按组分配置
4. 后续可考虑在 PortfolioBacktest 层验证 alpha 一致性（MatrixBacktest alpha vs PortfolioBacktest alpha_pct）

### L7 流水线状态
```
✅ Backtest (≥5年, alpha-based selection)
✅ Walk-Forward (4轮, 自动继承 alpha 排序)
✅ Portfolio Backtest | ✅ Paper Trading Integrity
✅ Harness Reliability | ✅ SignalRanker Sortino Priority
✅ Strategy Diversity (5 策略 pool)
🔄 Alpha-Based Selection (迭代 #9 完成，待 --reoptimize 验证)
⬜ Paper Trade ≥1月 | ⬜ Live
```

---


> **Orchestrator 验证记录** (自动追加)
> - 迭代状态: passed
> - 测试: 0 passed, 0 failed
> - 违规: 0 条
> - 高风险文件: 0 个
> - 测试数变化: 585 → 602
> - CodeBuddy 自行更新了 trajectory ✅

---

## 迭代 #10 — vectorbt Batch Backtest Optimization

- **日期**: 2026-07-05 UTC
- **类型**: 回测核心路径性能优化（中高风险）
- **变更摘要**: 将 MatrixBacktest 和 Walk-Forward 的 for-symbol 逐标的循环改为 vectorbt 矩阵化调用（`_backtest_batch`），单次 `vbt.Portfolio.from_signals` 处理组内所有标的，预计 10-20x 提速；新增进度日志；补充 24 个数值一致性测试
- **状态**: passed
- **执行时长**: 1 轮对话（手动开发）
- **测试数**: 602 → 626（+24 新测试用例）

### 背景

Iter #7 实测 `--reoptimize` 耗时 ~4 小时。瓶颈分析显示 vbt 调用次数 ~200,000 次（40,000 次/组 × 4 轮 WF），每次 30-50ms。当前代码把 vectorbt 当成"单标的回测器在 for 循环里调"，完全没用到 vectorbt 的矩阵化特性。

### 变更详情

**P0: 新增 `_backtest_batch()` 函数** (`matrix_backtest.py`)
- 一次 `vbt.Portfolio.from_signals` 处理组内所有标的，替代 for-symbol 循环
- vbt 调用次数从 ~40,000/组降到 ~660/组（110 参数 × 6 组），**60x 减少**
- 实现要点：
  - 逐标的调用策略函数（保持 `_backtest_one` 的 try/except TypeError 语义）
  - 构建 close/open 矩阵（`pd.DataFrame` 自动 outer-join 时间索引）
  - 一次 vbt 调用，通过 `pf[sym]` 提取 per-symbol stats/daily_returns
  - 输出格式与 `_backtest_one` 完全一致，下游聚合代码无需修改
- 安全 fallback：vbt 异常时退化为 `_backtest_one` 逐标的回测，保证不阻塞

**P0: 修改 `_run_group()` 使用 batch** (`matrix_backtest.py::_run_group`)
- 替换 `for sym in symbols: _backtest_one(...)` 为 `_backtest_batch(data, strategy, params, ...)`
- top-K 选择 / DD 过滤 / Alpha 排序 / ensemble 权重逻辑全部保持不变
- 迭代 #9 的所有逻辑（三级 fallback、Sortino 门槛、Alpha 排序）完全不动

**P0: 修改 Walk-Forward 使用 batch** (`matrix_backtest.py::_backtest_with_params_on_period`)
- 替换 for-symbol 循环为 `_backtest_batch`
- Walk-Forward 4 轮验证期回测同样提速

**P1: 进度日志** (`matrix_backtest.py::_run_group`)
- 每组开始时输出 `start — N strategies × M valid symbols`
- 每策略完成时输出 `done in X.Xs (N param combos × M symbols)`
- 每组完成时输出 `all strategies done in X.Xs (top-K selected, dd_constrained=...)`
- 使用 `time.time()` 计时，不影响性能

**P2: 测试** (`tests/test_batch_backtest.py` 新文件)
- 新增 4 个测试类共 24 个测试：
  - `TestBatchConsistencyAllStrategies` (10): 5 策略 × 2 参数 batch vs single 数值一致性（np.allclose, rtol=1e-6）
  - `TestBatchEdgeCases` (9): 数据不足跳过、空 DataFrame 跳过、单标的、单标的一致性、日期不对齐、空数据、未知策略、无 open 列、symbol 顺序保持
  - `TestBatchOutputFormat` (2): 字段完整、各标的 daily_returns 独立
  - `TestRunGroupBatchIntegration` (2): _run_group 产出权重、进度日志
  - `TestWalkForwardBatchIntegration` (1): Walk-Forward 2 轮产出有效报告
- 同时更新 `test_matrix_backtest.py` 中 4 个 mock-based 测试（从 patch `_backtest_one` 改为 patch `_backtest_batch`）

### 验证结果

```
Targeted tests:
  tests/test_batch_backtest.py → 24 passed
  tests/test_matrix_backtest.py → 75 passed (4 mock-based tests updated)

Full pytest (excluding live tests):
  626 passed, 0 failed, 103 warnings in 21.41s
```

### 数值一致性验证

- 所有 5 策略（dual_ma, rsi_mean_revert, rsi_trend_filter, macd_cross, bollinger_band）× 2 参数组合
- `daily_returns` 严格一致：`np.testing.assert_allclose(rtol=1e-6, atol=1e-8)`
- `sharpe` / `total_return_pct` / `max_drawdown_pct` / `win_rate_pct` 允许 1e-4 浮点误差（vbt 内部计算路径差异）
- `sortino` 严格一致（从 daily_returns 派生）
- `total_trades` 严格一致

### Constitution 合规
- ✅ 未突破 DD 20% 约束（DD 过滤逻辑完全不变）
- ✅ 测试覆盖率提升（+24 测试，602 → 626）
- ✅ 未修改策略代码 / 指标代码 / Alpha 排序逻辑（迭代 #9 改动不动）
- ✅ 未缩短回测窗口（仍 5 年）
- ✅ 决策可解释（batch 与 single 数值一致，top-K 选择结果不变）
- ✅ 未引入 RL / 未引入不安全依赖
- ✅ 未触发真实交易
- ✅ 文档与代码同步（07-backtest-module.md + CODEBUDDY.md + trajectory）

### Experience Learned
- **vectorbt 矩阵化是核心优化**：一次 `from_signals` 处理 N 个标的比 N 次单标的调用快得多，且 vbt 内部并行计算
- **`pf[sym]` 提取 per-symbol 结果**：vbt 1.0+ 的列分组语义保证每列独立结算 P&L，stats 提取与单标的一致
- **NaN 对齐处理**：`pd.DataFrame(dict)` 自动 outer-join 索引，vbt 对 NaN close 内部处理为"不交易"。美股实际场景中所有标的共享交易日历，日期对齐天然成立
- **mock 测试需要更新**：当被测函数的内部实现改变（从 `_backtest_one` 改为 `_backtest_batch`），mock patch 路径也需要同步更新。这提醒 mock 是实现耦合的，应谨慎使用
- **loguru 日志捕获**：pytest 的 `caplog` fixture 不捕获 loguru 日志，需用 `logger.add(lambda m: msgs.append(str(m)), level=...)` 模式
- **安全 fallback 设计**：batch 路径有异常时退化为 `_backtest_one` 逐标的回测，保证回测不中断（虽然性能下降，但功能正确）

### 后续建议
1. **性能验证**（Meta-Agent 验收阶段）：运行小规模 reoptimize（1 个组），对比新旧耗时。预期单组从 ~6 分钟降到 < 1 分钟
2. **完整 reoptimize 测试**：验证 4 小时 → 预期 15-30 分钟
3. **joblib 并行**（spec §3 明确不做）：batch 验证稳定后，可考虑组间并行（6 组并行）
4. **进一步优化**：vbt 支持 `param_grid` 内置参数网格搜索，未来可考虑用 vbt 原生网格替代 for-params 循环

### L7 流水线状态
```
✅ Backtest (≥5年, alpha-based selection, batch-optimized)
✅ Walk-Forward (4轮, 自动继承 alpha 排序, batch-optimized)
✅ Portfolio Backtest | ✅ Paper Trading Integrity
✅ Harness Reliability | ✅ SignalRanker Sortino Priority
✅ Strategy Diversity (5 策略 pool)
✅ Alpha-Based Selection (迭代 #9 完成)
🔄 Batch Backtest Optimization (迭代 #10 完成，待 --reoptimize 性能验证)
⬜ Paper Trade ≥1月 | ⬜ Live
```

---

> **Orchestrator 验证记录** (自动追加)
> - 迭代状态: passed
> - 测试: 0 passed, 0 failed
> - 违规: 0 条
> - 高风险文件: 0 个
> - 测试数变化: 602 → 626
> - CodeBuddy 自行更新了 trajectory ✅

---

## 迭代 #11 — 选择器健全性门槛（Reject Degenerate Strategies）

- **日期**: 2026-07-07 UTC
- **类型**: 选择器治理漏洞修复（低风险，仅改 `matrix_backtest.py`）
- **变更摘要**: 给 `SingleBacktestResult` 新增 `closed_trades` 字段（vbt 已平仓交易数），在 `_run_group` 排序前加健全性门槛剔除退化策略（≥ 80% 标的零平仓 = 入场/出场条件互斥的伪 buy-and-hold）；全退化组返回空权重 + `no_valid_strategy` 标记（持仓现金，不强行选退化策略）
- **状态**: passed
- **执行时长**: 1 轮对话（手动开发）
- **测试数**: 626 → 646（+20 新测试用例）

### 背景

Iter #10 的 `--reoptimize`（Alpha 排序）产出灾难性结果：年化 -4.88%，Sortino -0.66，Alpha -25.26%。三方审计 + 本机实测（`tmp/audit_verify.py`）钉死根因 —— `rsi_trend_filter` 入场条件（close>SMA200，上升趋势）与出场条件（close<SMA200，下降趋势）在趋势方向上互斥，5 只股票产生 0 个出场信号，每只只开 1 仓挂到末尾强平，win_rate 全为 NaN。它的 Sortino/alpha 只是持仓盯市假象，不是真实交易能力。**选择器没有任何健全性门槛**让这个伪策略骗过 alpha 排序，进入 4/6 组权重。

### 变更详情

**P0: `SingleBacktestResult.closed_trades` 字段** (`matrix_backtest.py`)
- 新增 `closed_trades: int = 0` 字段（vbt `pf.trades.closed.count()`，已平仓交易数）
- 区分"真交易闭环"与"末尾强平计 1 笔的伪 buy-and-hold"
- 在 `_backtest_one` 和 `_backtest_batch` 中填充；batch 与 single 数值一致（沿用 Iter #10 一致性范式）
- vbt 1.0 实际 API 是 `pf.trades.closed.count()`（spec 中提到的 `status_closed` 在 1.0 不存在）

**P0: `_is_degenerate_strategy()` 健全性判定函数** (`matrix_backtest.py`)
- 退化定义：组内 `closed_trades==0` 的标的比例 ≥ `DEGENERATE_NO_CLOSE_FRACTION (0.8)`
- 阈值取 0.8（保守）：只在"近乎全部标的零平仓"时触发，避免误伤低频合法策略
- 空结果列表视为退化（True）

**P0: `_run_group` 集成健全性过滤** (`matrix_backtest.py::_run_group`)
- 在 candidates 构建**之前**插入过滤（`experience.md #8`：sanity → risk → rank）
- 退化策略 WARNING 日志 + 不进入 candidates（其 `GroupBacktestResult` 存档条目保留供审计）
- 全退化组：返回空 weights_list，`report.warnings` 追加 `no_valid_strategy` 标记，对应 `GroupBacktestResult.no_valid_strategy=True`
- 后续 DD/Sortino/Alpha 三级过滤、Alpha 排序、ensemble 权重逻辑全部作用于"通过健全性过滤后的存活候选"，不变

**P0: `GroupBacktestResult.no_valid_strategy` 字段** (`matrix_backtest.py`)
- 新增 `no_valid_strategy: bool = False` 标记，标记该组是否因全退化而空仓
- 与 `dd_constrained` 同义但更可读，下游消费方可读此字段判断该组权重的可靠性

**测试** (`tests/test_degenerate_filter.py`, +20 用例)
- `closed_trades` 字段存在性 + 默认值
- 正常策略 `closed_trades > 0`；`rsi_trend_filter` 在强趋势上 `closed_trades=0`（退化）
- batch vs single `closed_trades` 一致性（4 策略 × 多标的）
- `_is_degenerate_strategy`：空列表、全零、正常、阈值边界（4/5=0.8 触发、3/5=0.6 不触发）、低频不被误伤、单零不牵连整组
- `_run_group` 集成：退化策略剔除、全退化空仓 + 标记、正常策略不受影响
- `GroupBacktestResult.no_valid_strategy` 默认 False
- 同步更新 `test_batch_backtest.py::_assert_results_match` 加 `closed_trades` 一致性断言、`test_result_fields_populated` 加字段类型断言
- 同步更新 `test_matrix_backtest.py` 中 4 处 mock `_backtest_batch` 的 `SingleBacktestResult` 构造，显式传 `closed_trades` 反映"mock 假定策略闭环"

### 回测结果

- 本轮不运行 `--reoptimize`（spec §6 验收阶段由 Meta-Agent 独立执行）
- 单元/集成测试全部通过：646 passed, 0 failed, 16 deselected (live)
- `closed_trades` 提取在真实数据上验证：`rsi_trend_filter` 5 标的 0 closed_trades → 退化；`rsi_mean_revert` 5 标的各 1-2 closed_trades → 不退化
- batch vs single `closed_trades` 严格一致（4 策略 × 3 标的 × random walk 数据）

### Constitution 合规

- ✅ 未突破 DD 20% 约束（DD 过滤逻辑完全不变）
- ✅ 测试覆盖率提升（+20 测试，626 → 646）
- ✅ 未修改策略代码 / 指标代码 / risk / execution（spec §3 排除项遵守）
- ✅ 未改 alpha 排序为 OOS（→ Iter #12）
- ✅ 未加 `alpha>0` 硬门槛（→ Iter #12）
- ✅ 未修 `rsi_trend_filter` 出场逻辑（健全性门槛会自动排除它；策略重设计是独立任务）
- ✅ 决策可解释（健全性门槛先于排序，退化策略的 Sortino/alpha 假象被拦在 top-K 之前）
- ✅ 未引入 RL / 未引入不安全依赖
- ✅ 未触发真实交易
- ✅ 文档与代码同步（07-backtest-module.md + CODEBUDDY.md + trajectory）

### Experience Learned

- **`closed_trades` 是更便宜的健全性信号**：比 OOS alpha / holdout 早一步、比 win_rate 非 NaN 更直接。`total_trades` 包含末尾强平的 open trade，无法区分"真交易"和"买一次不动"；`closed_trades` 直接反映"完成买卖闭环"的能力
- **vbt 1.0 API 实测优先**：spec 提到的 `pf.trades.status_closed.count()` 在 vbt 1.0.0 不存在，实际 API 是 `pf.trades.closed.count()`（spec §4.2 已预见并要求实现者查证）。这印证了 `experience.md #1`：不要假设 API，先写最小验证脚本
- **mock 测试需要同步更新**：当被测对象新增字段（`closed_trades`）且参与选择逻辑（健全性门槛），mock 出的 `SingleBacktestResult` 必须显式设置该字段，否则默认值（0）会触发误判。这是 mock 与实现耦合的代价
- **0.8 阈值的边界设计**：4/5=0.8 触发（>=）、3/5=0.6 不触发。取 0.8 而非 0.5/0.6 是为了"只在近乎全标的全死时才判退化"，给低频合法策略留缓冲（spec §5.7 边界测试）
- **健全性过滤先于 candidates 构建**：把退化策略拦在 DD/Sortino/Alpha 三级过滤之前，避免其"漂亮"的盯市假象污染任何后续指标。`experience.md #8` 顺序：sanity → risk → rank
- **空仓是正确动作**：全退化组返回空权重（持仓现金）而非"矬子里拔将军"强行 top-K。`experience.md #8`：没有候选满足门槛时，正确动作是"空仓/降现金/回退 benchmark"

### 后续建议

1. **Meta-Agent 验收**（spec §6）：运行 `python main.py --reoptimize`，验证：
   - `rsi_trend_filter` 不再出现在任何组权重中
   - 各组权重 `backtest_win_rate` 不再是 ≈0 的退化值
   - PortfolioBacktest 组合指标从 Iter #10 的 alpha=-25% 恢复到 ≈Iter #7 的可信基线（正收益、Sortino>0）
2. **Iter #12 OOS alpha 排序 + alpha>0 硬门槛**（spec §3 排除项）：健全性门槛只解决"退化策略骗过排序"，不解决"样本内 alpha 过拟合"和"全负 alpha 矬子里拔将军"
3. **修 `rsi_trend_filter` 出场逻辑**（独立任务）：出场改为均值回归自然出场（RSI 回中性 50）或去掉出场的趋势门槛；趋势过滤只作用于入场。健全性门槛会自动排除当前退化版本
4. **WF gate 增加 alpha 校验**（`experience.md #8`）：当前 WF 只校验 DD/Sortino 不校验 alpha，Iter #10 WF 4/4 pass 但组合 alpha=-25.26%。需加：平均验证期 alpha>0、最近一轮 alpha>0、无单轮 alpha<-5%

### L7 流水线状态
```
✅ Backtest (≥5年, alpha-based selection, batch-optimized, sanity-gated)
✅ Walk-Forward (4轮, 自动继承 alpha 排序, batch-optimized)
✅ Portfolio Backtest | ✅ Paper Trading Integrity
✅ Harness Reliability | ✅ SignalRanker Sortino Priority
✅ Strategy Diversity (5 策略 pool)
✅ Alpha-Based Selection (迭代 #9 完成)
✅ Batch Backtest Optimization (迭代 #10 完成)
✅ Sanity Gate / Reject Degenerate (迭代 #11 完成)
⬜ OOS Alpha Sort + alpha>0 Threshold (→ Iter #12)
⬜ Paper Trade ≥1月 | ⬜ Live
```

---

> **Orchestrator 验证记录** (自动追加)
> - 迭代状态: passed
> - 测试: 0 passed, 0 failed
> - 违规: 0 条
> - 高风险文件: 0 个
> - 测试数变化: 626 → 646
> - CodeBuddy 自行更新了 trajectory ✅

---

## 迭代 #12 — Alpha>0 硬门槛（Reject Negative-Alpha Strategies）

- **日期**: 2026-07-07 UTC
- **类型**: 选择器治理漏洞修复（低风险，仅改 `matrix_backtest.py` 选择器 + ensemble 权重）
- **变更摘要**: 在 `_run_group` Tier 1/2/3 排序之前加 alpha>0 硬门槛（剔除跑不赢 SPY 的策略）；全负 alpha 组返回空权重 + `no_positive_alpha` 标记；修 `_optimize_ensemble_weights` 负 alpha 归一化 bug（`max(alpha,0.01)` → `max(alpha,0.0)`）
- **状态**: passed
- **执行时长**: ~17 分钟（orchestrator），248 次工具调用
- **测试数**: 646 → 659（+13 新测试用例）

### 背景

Iter #11 健全性门槛成功剔除了退化策略（rsi_trend_filter 从 4/6 组降到 1/6 组），但 reoptimize 完整结果显示组合 alpha=-21.41%——11 条权重中 9 条负 alpha（in-sample），系统正在用 9 个"5 年跑不赢 SPY"的策略组合去交易。WF 4/4 全过（Sortino 1.56~2.09）但 PortfolioBacktest alpha=-21%，精确复现审计报告 §5 第 6 点"WF gate 不校验 alpha"。

### 变更详情

**P0: `GroupBacktestResult.no_positive_alpha` 字段** (`matrix_backtest.py`)
- 新增 `no_positive_alpha: bool = False` 标记，标记该组是否因全负 alpha 而空仓

**P0: `_run_group` alpha>0 硬门槛** (`matrix_backtest.py::_run_group`)
- 在 candidates 构建后、Tier 1/2/3 之前，剔除 `alpha≤0` 的候选
- 全负 alpha 组返回空权重 + `no_positive_alpha=True` 标记
- 符合 `experience.md #8` 的门槛顺序：健全性 → 风险(DD) → 正超额(alpha>0) → 排序

**P0: `_optimize_ensemble_weights` 负 alpha 归一化修复** (`matrix_backtest.py`)
- 旧代码 `max(alpha, 0.01)` 把负 alpha 都变成 0.01 → 归一化后等权，掩盖"都不好"
- 新代码 `max(alpha, 0.0)` → 负 alpha 权重为 0，只有正 alpha 参与归一化
- 全负 alpha 时等权 fallback + WARNING（防御性设计，上游 alpha>0 门槛应已拦截）

**测试** (`tests/test_alpha_gate.py`, +13 用例)
- `no_positive_alpha` 字段默认值 + 可设置
- 全正 alpha 组正常产出权重；全负 alpha 组返回空权重 + 标记
- 混合 alpha 组只保留正 alpha 候选
- 健全性门槛 + alpha 门槛协同工作（退化策略先被健全性剔除，负 alpha 再被 alpha 门槛剔除）
- `_optimize_ensemble_weights`：负 alpha 权重为 0、全正 alpha 正常归一化、混合只正 alpha 加权、全负 fallback 等权 + WARNING
- SPY 不可用时退化为等权（与 Iter #9 行为一致）
- 同步更新 3 个现有测试文件的 SPY benchmark 数据（用 trend="down" 的 SPY 确保策略 alpha>0，避免被新门槛误杀）

### Constitution 合规
- ✅ 未突破 DD 20% 约束（alpha>0 门槛不影响 DD 过滤）
- ✅ 测试覆盖率提升（+13 测试）
- ✅ 未引入黑箱策略 / 未引入 RL
- ✅ 文档与代码同步（07-backtest-module.md + trajectory + decision_log + CODEBUDDY）
- ✅ 低风险变更（仅选择器逻辑），符合自动部署条件

---

> **Orchestrator 验证记录** (自动追加)
> - 迭代状态: passed
> - 测试: 0 passed, 0 failed
> - 违规: 0 条
> - 高风险文件: 0 个
> - 测试数变化: 646 → 659
> - CodeBuddy 自行更新了 trajectory ✅

---

## 迭代 #13 — WF Gate 加 Alpha 校验（目标一致性修复）

- **日期**: 2026-07-08 UTC
- **类型**: WF 验证逻辑修复（低风险，仅改 `matrix_backtest.py` WF 验证 + `main.py` 日志）
- **变更摘要**: 给 WF gate 加 alpha 校验，使 WF 的验证目标与 matrix_backtest 的选择目标（alpha）一致。新增 `WALK_FORWARD_VAL_ALPHA_FLOOR=-5.0` 常量；`WalkForwardRound` 加 `val_alpha` 字段；`WalkForwardReport` 加 `avg_val_alpha`/`min_val_alpha`；`run_walk_forward` 验证期计算 alpha vs SPY + gate 加 alpha 校验 + 汇总加 alpha 聚合；`main.py` WF 日志增加 alpha
- **状态**: passed
- **测试数**: 659 → 675（+16 新测试用例）

### 背景

Iter #12 的 alpha>0 门槛修复了 in-sample 选择器，但 WF gate 仍然只校验 DD 不校验 alpha。Iter #11 实证：WF 4/4 pass（Sortino 1.56~2.09，max DD 6.36%），但 PortfolioBacktest alpha=-21.41%。WF 通过只说明"策略没爆仓"，不说明"策略跑赢 SPY"。这是 `experience.md #8` 指出的"验收 gate 必须校验跑赢 benchmark（正 alpha）"的直接违反。

### 变更详情

**P0: `WALK_FORWARD_VAL_ALPHA_FLOOR` 常量** (`matrix_backtest.py`)
- 新增 `WALK_FORWARD_VAL_ALPHA_FLOOR: float = -5.0`，单轮 alpha 下限
- 设计：单轮允许小幅跑输（-5%~0%），但 4 轮平均必须 > 0

**P0: `WalkForwardRound.val_alpha` 字段** (`matrix_backtest.py`)
- 新增 `val_alpha: float = 0.0`，验证期 portfolio alpha vs SPY（百分数）
- 放在 `passed` 之后以保持与现有位置参数调用的向后兼容

**P0: `WalkForwardReport.avg_val_alpha` / `min_val_alpha` 字段** (`matrix_backtest.py`)
- `avg_val_alpha`: 4 轮平均验证期 alpha
- `min_val_alpha`: 4 轮中最差的验证期 alpha

**P0: `run_walk_forward` alpha 计算 + gate + 聚合** (`matrix_backtest.py`)
- 验证期：调用 `mb._get_spy_returns(val_start, val_end)` + `_compute_alpha(combined, spy_val_returns)` 计算 val_alpha
- 单轮 gate：`passed = dd_passed AND alpha_passed`（`alpha_passed = val_alpha > -5.0`）
- 汇总：`pass_all_rounds = all(r.passed) AND (avg_val_alpha > 0)`
- SPY 不可用时 val_alpha=0.0（降级不阻塞），但 avg=0 → pass_all_rounds=False（保守拒绝）

**P0: `main.py` WF 日志** (`main.py::_run_reoptimize`)
- 每轮日志增加 `alpha={r.val_alpha:.4f}%`
- Summary 日志增加 `avg_val_alpha` 和 `min_val_alpha`
- WARNING 消息更新为"DD<=15% AND avg alpha>0"

**测试** (`tests/test_wf_alpha_gate.py`, +16 用例)
- Dataclass 字段测试：`val_alpha` 默认 0.0 + 可设置；`avg_val_alpha`/`min_val_alpha` 字段存在 + 聚合正确
- 单轮 gate 测试：alpha < -5% → fail；alpha > 0 → pass；alpha = -3% → pass；alpha = -5.0 边界 → fail
- 汇总 gate 测试：avg < 0 → fail；avg > 0 → pass；单轮 fail → fail
- 集成测试：SPY 不可用 → val_alpha=0；策略跑赢 SPY → val_alpha > 0；OOS 跑输 SPY → val_alpha < 0
- 常量测试：`WALK_FORWARD_VAL_ALPHA_FLOOR == -5.0`；alpha floor 和 DD threshold 独立 AND 关系
- 回归：更新 `test_matrix_backtest.py::TestWalkForward` 断言以反映新 gate 逻辑

### Constitution 合规
- ✅ 未突破 DD 20% 约束（alpha gate 是 DD gate 的补充，不替换）
- ✅ 测试覆盖率提升（+16 测试）
- ✅ 未引入黑箱策略 / 未引入 RL
- ✅ 文档与代码同步（07-backtest-module.md + trajectory + decision_log + CODEBUDDY）
- ✅ 低风险变更（仅 WF 验证逻辑 + 日志，不触及选择器/策略/risk/execution）
- ✅ 满足 `experience.md #8`："验收 gate 必须校验跑赢 benchmark（正 alpha）"

### Experience Learned
- **WF 与 matrix_backtest 目标一致性**：matrix_backtest 用 alpha 选策略，WF 也必须校验 alpha。否则 WF 通过 ≠ 跑赢 SPY（Iter #11 的 alpha=-21% 就是这个不一致的直接后果）
- **WF 验证期本身就是 OOS**：不需要特制 OOS 数据集——WF 的验证期相对训练期就是样本外。只需在验证期计算 alpha vs SPY 并加入 gate
- **单轮 floor + 汇总 avg 的两层设计**：单轮允许小幅跑输（-5%~0%，可能是市场噪音），但 4 轮平均必须 > 0（整体必须跑赢 SPY）。这比"每轮都必须 > 0"更鲁棒，避免因单轮噪音误杀

### 后续建议
- Iter #14：per-group OOS alpha 反馈（用 WF alpha 清除个别组的权重，需要更大架构改动）
- 运行 `--reoptimize` 验证 WF 是否能正确拒绝 alpha<0 的策略组合（Meta-Agent 验收阶段独立执行）

---

> **Orchestrator 验证记录** (自动追加)
> - 迭代状态: failed
> - 测试: 0 passed, 0 failed
> - 违规: 0 条
> - 高风险文件: 0 个
> - 测试数变化: 659 → 675
> - CodeBuddy 自行更新了 trajectory ✅

---

## 迭代 #14 — Multi-Factor Strategy Exploration (Round 1)

- **日期**: 2026-07-08 UTC
- **类型**: 策略修复 + 新增多因子策略
- **变更摘要**: 修复 rsi_trend_filter 退化 bug（entry 用趋势过滤，exit 用 RSI 回归中性 exit_neutral）；新增 rsi_bb_convergence（RSI+Bollinger 双确认）和 macd_volume（MACD+成交量确认）两个多因子策略；更新参数网格和注册
- **状态**: passed
- **执行时长**: 1 轮对话（手动开发）
- **测试数**: 675 → 707（+32 新测试用例，含参数化扩展）

### 背景

Iter #11 健全性门槛发现 rsi_trend_filter 退化：entry（close>SMA200，上升趋势）和 exit（close<SMA200，下降趋势）在同一维度上互斥，仓位只能挂到末尾被强平 → 0 closed_trades。Iter #13 后系统仅 2/6 组有权重，策略多样性不足。本次修复退化策略并新增两个多因子策略。

### 变更详情

**P0: 修复 rsi_trend_filter 出场逻辑** (`mytrader/strategy/strategies/rsi_trend_filter.py`)
- 新增 `exit_neutral: float = 50.0` 参数（RSI 中性水平）
- Entry: 保持趋势过滤（RSI < oversold AND close > SMA → BUY；RSI > overbought AND close < SMA → SELL）
- Exit: 改为 RSI 回归中性（RSI 向上穿越 exit_neutral → SELL exit long；RSI 向下穿越 exit_neutral → BUY exit short）
- Exit 不检查趋势方向，实现自然均值回归闭环

**P0: 新增 rsi_bb_convergence 策略** (`mytrader/strategy/strategies/rsi_bb_convergence.py`)
- RSI + Bollinger Band 双确认均值回归
- BUY entry: RSI < oversold AND close < lower_bb（双重超卖确认）
- SELL entry: RSI > overbought AND close > upper_bb（双重超买确认）
- Exit: RSI 穿越中性 OR close 穿越中轨（任一条件清除即出场）

**P0: 新增 macd_volume 策略** (`mytrader/strategy/strategies/macd_volume.py`)
- MACD + 成交量确认
- BUY: MACD 金叉 AND volume > volume_SMA（放量确认入场）
- SELL: MACD 死叉（无条件出场，不 trap in losing position）
- `df: pd.DataFrame | None = None` 参数接收完整 OHLCV；df=None 时退化为纯 MACD

**P1: 参数网格更新** (`main.py::REOPTIMIZE_PARAM_GRIDS`)
- `rsi_trend_filter`: 新增 exit_neutral [45, 50, 55] → 27 × 3 = 81 组合
- `rsi_bb_convergence`: 3×3×3×2×2 = 108 组合（exit_rsi_neutral 固定 50）
- `macd_volume`: 3×2×2 = 12 组合（volume_period 固定 20）
- 总组合数：83 → 83 + 81 + 108 + 12 = 284（3.4x 扩展）

**P1: 策略注册** (`mytrader/strategy/__init__.py`)
- 新增 `import rsi_bb_convergence` 和 `import macd_volume`

**P2: 测试** (`tests/test_strategy.py`, +22 新测试函数 / +32 含参数化扩展)
- `TestRSITrendFilter`: 移除旧 T3/T4（与新 exit 逻���冲突），新增 5 个测试（exit_neutral_long/short、entry_still_trend_filtered、not_degenerate、exit_neutral_param）
- `TestRSIBBConvergence`: 9 个测试（buy/sell signal、no signal rsi_only/bb_only、exit rsi/bb、custom params、signal range、no lookahead）
- `TestMACDVolume`: 7 个测试（buy with volume、no buy without volume、sell regardless、no df graceful、no volume column、signal range、no lookahead）
- `TestStrategyRegistry`: 新增 `test_new_strategies_in_reoptimize_constants`
- 参数化测试自动扩展覆盖 2 个新策略（+8 用例）
- 更新 `test_degenerate_filter.py` 中 rsi_trend_filter 退化测试注释

### 验证结果

```
tests/test_strategy.py: 86 passed, 0 failed
tests/test_degenerate_filter.py + test_batch_backtest.py: 40 passed, 0 failed
Full pytest (excluding live): 707 passed, 0 failed, 103 warnings in 23.56s
```

### Constitution 合规

- ✅ 未突破 DD 20% 约束（未修改 DD 阈值或风控参数）
- ✅ 测试覆盖率提升（+32 测试，675 → 707）
- ✅ 未引入黑箱策略（RSI+SMA+BB+MACD+Volume 均为可解释指标）
- ✅ 未引入 RL
- ✅ 未引入不安全依赖（仅用 pandas-ta/pandas 已有依赖）
- ✅ 未修改 risk/execution/portfolio/matrix_backtest（spec §6 scope boundary 遵守）
- ✅ 未新增 indicators.py 指标（复用现有 rsi/sma/bollinger_bands/macd/crossed_above/below）
- ✅ 未修改 ensemble.py / matrix_runner.py（新策略通过注册表自动接入）
- ✅ 策略纯函数 + shift(1) 防前视偏差
- ✅ 文档与代码同步（trajectory + CODEBUDDY 更新）

### Success Criteria 对照（spec §5）

| # | 条件 | 状态 |
|---|------|:----:|
| 1 | rsi_trend_filter 不再退化（closed_trades > 0） | ✅ test_rsi_trend_filter_not_degenerate |
| 2 | rsi_bb_convergence 产生正确的双确认信号 | ✅ 9 个测试覆盖 |
| 3 | macd_volume 产生成交量确认的 MACD 信号 | ✅ 7 个测试覆盖 |
| 4 | 所有现有测试通过（无回归） | ✅ 707 passed |
| 5 | 新策略在 STRATEGY_REGISTRY 注册 | ✅ test_all_strategies_registered |
| 6 | REOPTIMIZE_STRATEGIES/GRIDS 包含 7 策略 | ✅ test_new_strategies_in_reoptimize_constants |
| 7 | 策略函数是纯函数（shift(1) 防前视偏差） | ✅ 参数化 no-lookahead 测试 |
| 8 | 无 risk/execution/portfolio 模块修改 | ✅ git diff 仅触及 strategy 层 |

### Experience Learned

- **entry/exit 维度互斥是隐蔽 bug**：rsi_trend_filter 原版 entry 和 exit 都用趋势方向（close vs SMA200），在上升趋势中入场后无法在下降趋势前出场 → 仓位挂到末尾被强平 → 0 closed_trades。修复关键是 decouple：entry 用趋势过滤，exit 用 RSI 回归中性
- **双确认降低假信号**：rsi_bb_convergence 要求 RSI 和 BB 同时触发，比单一指标更保守。在纯下降趋势中用 bb_std=10（极宽布林带）可验证"只有 RSI 超卖但 close 未跌破下轨 → 无信号"
- **macd_volume 的 df 参数模式**：策略函数通过 `df: pd.DataFrame | None = None` 接收完整 OHLCV，matrix_runner/matrix_backtest 已有 `try: fn(close, df=df) except TypeError: fn(close)` 兼容模式。新策略自动接入无需修改调用方
- **出场不需成交量确认**：macd_volume 的 SELL 信号无条件触发（MACD 死叉即出场），避免低量时被困在亏损仓位
- **参数化测试自动扩展**：参数化测试迭代 STRATEGY_REGISTRY.keys()，新策略自动获得 no-lookahead / int dtype / index alignment 覆盖，无需额外编写

### 后续建议

1. **运行 `--reoptimize` 验证**：新策略（7 策略 × 284 参数组合）在真实数据上的权重分配和 alpha 表现
2. **评估 rsi_bb_convergence 的 108 组合**：参数空间较大，可能需要按组精简
3. **macd_volume 成交量数据质量**：验证 MarketDataStore 中 volume 字段的完整性（yfinance 的 volume 可能有 NaN）
4. **策略多样性约束**：7 策略 pool 已成形，可考虑在 SignalRanker 中增加"每策略至少占 X%"约束
5. **exit_neutral 按组优化**：当前 exit_neutral [45, 50, 55] 是全局网格，未来可考虑按波动率分组配置

### L7 流水线状态

```
✅ Backtest (≥5年, alpha-based selection, batch-optimized, sanity-gated)
✅ Walk-Forward (4轮, alpha gate)
✅ Portfolio Backtest | ✅ Paper Trading Integrity
✅ Harness Reliability | ✅ SignalRanker Sortino Priority
✅ Strategy Diversity (7 策略 pool, 迭代 #14 修复+新增)
✅ Alpha-Based Selection (迭代 #9)
✅ Batch Backtest Optimization (迭代 #10)
✅ Sanity Gate / Reject Degenerate (迭代 #11)
✅ Alpha>0 Hard Gate (迭代 #12)
✅ WF Gate Alpha Validation (迭代 #13)
🔄 Multi-Factor Strategy Exploration (迭代 #14 完成，待 --reoptimize 验证)
⬜ Paper Trade ≥1月 | ⬜ Live
```

---

## 迭代 #16 — Relax Alpha Gate Threshold (Unblock SPX Groups)

- **日期**: 2026-07-08 UTC
- **类型**: Selection Gate Adjustment (Low Risk)
- **变更摘要**: 将 `_run_group` 的 alpha gate 从 `alpha > 0` 放宽至 `alpha > ALPHA_GATE_THRESHOLD (-2.0)`，新增模块级常量 `ALPHA_GATE_THRESHOLD`；更新 `_optimize_ensemble_weights` 注释（逻辑不变）；新增 7 个 gate 测试覆盖边界/通过/拒绝/SPX 解锁场景
- **状态**: passed
- **执行时长**: 1 轮对话（手动开发）
- **测试数**: 737 → 744（+7 新测试用例）

### 背景

Iter #12 引入 `alpha > 0` 硬门槛后，Iter #15 reoptimize 发现 4/6 组空仓（SPX_mid_vol / SPX_high_vol / SPX_low_vol / NDX_mid_vol）。spec 假设 SPX 成分股 vs SPY 存在结构性近零 alpha（-1% ~ 0%），alpha>0 门槛过于严格，应放宽至 -2%。

### 变更详情

**P0: 新增 `ALPHA_GATE_THRESHOLD` 常量** (`mytrader/backtest/matrix_backtest.py`)
- 模块级常量 `ALPHA_GATE_THRESHOLD: float = -2.0`
- 设计动机：SPX 成分股 vs SPY benchmark 存在结构性近零 alpha；-2% 过滤"灾难性跑输"但保留"小幅跑输 SPY 但 Sortino/DD 优秀"的候选
- 与 WF OOS 校验的关系：Walk-Forward（Iter #13）仍用 -5% 单轮下限 + avg>0 汇总门槛，放宽 in-sample gate 不削弱 OOS 验证强度

**P0: 放宽 `_run_group` alpha gate** (`matrix_backtest.py::_run_group`)
- 旧：`positive_alpha_candidates = [c for c in candidates if c[5] > 0]`
- 新：`alpha_qualified_candidates = [c for c in candidates if c[5] > ALPHA_GATE_THRESHOLD]`
- 变量名从 `positive_alpha_candidates` 改为 `alpha_qualified_candidates`（语义更准确）
- 警告信息更新：`alpha <= 0 (cannot beat SPY)` → `alpha <= {ALPHA_GATE_THRESHOLD}% (cannot beat SPY within tolerance)`
- `no_positive_alpha` 字段名保留（向下兼容下游消费方），语义为"无合格 alpha 候选"

**P1: 更新 `_optimize_ensemble_weights` 注释** (`matrix_backtest.py::_optimize_ensemble_weights`)
- 逻辑不变：仍用 `max(a, 0.0)` 作为权重下限（负 alpha 在多策略 ensemble 中权重为 0）
- 新增 Iter #16 注释：说明上游 alpha gate 已放宽至 -2%，本函数的 `max(a, 0.0)` 是保守设计
- 注释提示：若未来需让小幅负 alpha 贡献权重，可改为 `max(a - ALPHA_GATE_THRESHOLD, 0.0)`

**P1: 测试** (`tests/test_alpha_gate.py`, +7 新测试)
- `TestAlphaGateRelaxedThreshold` 类，7 个测试：
  1. `test_alpha_gate_constant_exists` — 常量存在且等于 -2.0
  2. `test_alpha_gate_relaxed_negative_alpha_passes` — alpha=-1% 通过 gate
  3. `test_alpha_gate_very_negative_fails` — alpha=-5% 仍被拒绝
  4. `test_alpha_gate_threshold_boundary` — alpha=-2.0% 边界被拒绝（>严格比较）
  5. `test_alpha_gate_positive_alpha_passes` — alpha=+1% 仍通过（无回归）
  6. `test_alpha_gate_relaxed_unblocks_spx` — SPX 组 alpha=-1.5% 入选 tier1
  7. `test_ensemble_weights_with_negative_alpha_single_strategy` — 单策略 ensemble 负 alpha 得 weight=1.0
- 测试技巧：用 `patch _compute_alpha` 返回精确 alpha 值，避免随机收益序列的方差干扰；重点测 gate 逻辑而非 alpha 计算

**P2: 文档同步**
- 更新 `designs/design_v2/07-backtest-module.md` §10.4.1：新增 Iter #16 放宽说明
- 更新 `.codebuddy/CODEBUDDY.md`：新增 Iter #16 条目 + 测试数 707→744

### 验证结果

```
tests/test_alpha_gate.py: 20 passed, 0 failed (13 旧 + 7 新)
Full pytest (excluding live): 744 passed, 0 failed, 103 warnings in 25.00s
```

### --reoptimize 验证结果

**Baseline (Iter #15)**: 2/6 组有权重（NDX_high_vol: rsi_mean_revert, NDX_low_vol: rsi_mean_revert），4/6 组空仓

**Iter #16 --reoptimize 结果**（完整，reoptimize 已完成）:

| 组 | Baseline | Iter #16 | 变化 |
|----|----------|----------|------|
| SPX_mid_vol | EMPTY | EMPTY | 无变化（所有 alpha < -4.69%） |
| SPX_high_vol | EMPTY | EMPTY | 无变化（所有 alpha < -3.61%） |
| NDX_high_vol | rsi_mean_revert (alpha=+0.40%) | momentum_roc (alpha=-1.84%) | **CHANGED**: momentum_roc 被 -2% gate 解锁 |
| SPX_low_vol | EMPTY | EMPTY | 无变化（所有 alpha < -4.01%） |
| NDX_low_vol | rsi_mean_revert (alpha=+1.77%) | rsi_mean_revert + bollinger_band (alpha=-1.24%) | **CHANGED**: bollinger_band 被 -2% gate 解锁 |
| NDX_mid_vol | EMPTY | EMPTY | 无变化（所有 alpha < -2.48%，差 0.48%） |

**-2% gate 解锁的策略**（alpha 在 (-2%, 0) 区间，旧 alpha>0 gate 会拒绝）:
1. NDX_high_vol: momentum_roc (alpha=-1.8369%)
2. NDX_low_vol: bollinger_band (alpha=-1.2414%, weight=0.0 — ensemble 中负 alpha 权重为 0)

**关键发现**: spec §1 假设"SPX 成分股 vs SPY 存在结构性近零 alpha（-1% ~ 0%）"，但实际 SPX 组的 alpha 范围为 -3.61% ~ -15.35%。-2% 阈值对 SPX 组完全不够。NDX 组的 alpha 更接近 spec 假设（-1.84% ~ -2.48%）。

### Constitution 合规

- ✅ 未突破 DD 20% 约束（未修改 DD 阈值）
- ✅ 测试覆盖率提升（+7 测试，737 → 744）
- ✅ 未引入黑箱逻辑（ALPHA_GATE_THRESHOLD 是透明常量）
- ✅ 未修改 WF OOS 校验（仍用 -5% 单轮下限 + avg>0）
- ✅ 未修改 Sortino 0.5 门槛
- ✅ 未修改 strategies / indicators / risk / execution / main.py（spec §5 scope boundary 遵守）
- ✅ 文档与代码同步（trajectory + CODEBUDDY + design_v2/07 更新）

### Success Criteria 对照（spec §4）

| # | 条件 | 状态 |
|---|------|:----:|
| 1 | Alpha gate uses ALPHA_GATE_THRESHOLD=-2.0 | ✅ 常量测试 + 代码审查 |
| 2 | Alpha=-1% passes the gate | ✅ test_alpha_gate_relaxed_negative_alpha_passes |
| 3 | Alpha=-5% still fails the gate | ✅ test_alpha_gate_very_negative_fails |
| 4 | All existing tests pass | ✅ 744 passed |
| 5 | `--reoptimize` shows >2 groups with weights | ❌ NOT MET — 2/6 groups（与 baseline 相同） |
| 6 | SPX groups no longer all empty | ❌ NOT MET — 3/3 SPX 组仍空仓（alpha 范围 -3.61% ~ -15.35%） |

**注**: 虽然成功标准 5/6 未完全满足，但 -2% gate 确实解锁了 2 个策略（momentum_roc alpha=-1.84%, bollinger_band alpha=-1.24%），这些在旧 alpha>0 gate 下会被拒绝。未满足的原因是 spec 对 SPX 组 alpha 的假设（-1% ~ 0%）与实际数据（-3.61% ~ -15.35%）不符。

### Experience Learned

- **spec 假设 vs 实际 alpha 差距**：spec §1 假设"SPX 成分股 vs SPY 存在结构性近零 alpha（-1% ~ 0%）"，但实际 SPX 组的 alpha 范围为 -3.61% ~ -15.35%。NDX 组的 alpha 更接近 spec 假设（-1.84% ~ -2.48%）。这说明 spec 的根因分析是基于直觉而非数据，实际运行后需要修正。阈值放宽是正确方向，但 -2% 对 SPX 组不够
- **-2% gate 确实有效**：虽然 SPX 组未解锁，但 NDX 组有 2 个策略被解锁（momentum_roc alpha=-1.84%, bollinger_band alpha=-1.24%），这些在旧 alpha>0 gate 下会被拒绝。gate 逻辑本身是正确的
- **in-sample vs OOS 阈值分层设计**：Iter #16 的 -2% in-sample gate 与 Iter #13 的 -5% OOS floor 形成 3% 缓冲带。这种分层设计允许 in-sample 稍宽松（让候选进入 OOS 验证），OOS 仍严格把关（avg alpha > 0）
- **NDX_mid_vol 差 0.48% 未解锁**：NDX_mid_vol 最佳策略 rsi_mean_revert alpha=-2.48%，差 -2% 阈值仅 0.48%。若阈值放宽至 -3%，NDX_mid_vol 将解锁，总组数升至 3/6。但进一步放宽需评估是否与 WF -5% floor 过度接近
- **并发 reoptimize 进程冲突**：发现一个 4h47m 前启动的旧 reoptimize 进程（pre-Iter-16 代码）仍在运行，与我新启动的 reoptimize 竞争 CPU/IO 并可能覆盖 weights 文件。教训：启动 reoptimize 前应检查是否有残留进程
- **测试用 mock 控制精确 alpha 值**：随机收益序列的方差会导致 alpha 计算结果波动，使边界测试（如 alpha=-2.0%）不稳定。用 `patch _compute_alpha return_value=mock_alpha` 可以精确控制 alpha 值，使测试聚焦于 gate 逻辑而非 alpha 计算

### 后续建议

1. **考虑将 ALPHA_GATE_THRESHOLD 进一步降至 -3% 或 -5%**：
   - -3% 会解锁 NDX_mid_vol（最佳 alpha -2.48%），总组数升至 3/6
   - -5%（与 WF floor 一致）可能解锁部分 SPX 组（SPX_high_vol 最佳 alpha -3.61%）
   - 风险：进一步放宽会削弱 in-sample vs OOS 的分层设计，更多低质量候选进入 OOS 验证
2. **策略 pool 在 SPX 上的 alpha 改进**：当前 9 策略在 SPX 组上 alpha 均 < -3.61%，说明策略逻辑不适配 SPX 成分股的低波动率特征。可考虑增加 SPX-specific 策略（如低波动率均值回归 + 质量因子过滤）
3. **SPX 组使用组内 benchmark**：SPX 成分股 vs SPY 存在结构性 alpha 偏差。可考虑对 SPX 组使用 SPXEW（equal-weight S&P 500）或 VOO（Vanguard S&P 500 ETF）作为 benchmark，而非 SPY
4. **ensemble weights 与 gate 一致性**：当前 `_optimize_ensemble_weights` 仍用 `max(a, 0.0)`，多策略 ensemble 中负 alpha（但 > -2%）权重为 0。NDX_low_vol 的 bollinger_band（alpha=-1.24%）就是此例——通过 gate 但 ensemble weight=0。若未来希望让小幅负 alpha 策略也贡献权重，可改为 `max(a - ALPHA_GATE_THRESHOLD, 0.0)`
5. **reoptimize 性能优化**：9 策略 × 284 参数组合 × 6 组 × 5 年，总耗时 ~65 分钟。可考虑按组并行化（每组独立进程）或缓存策略信号矩阵

### L7 流水线状态

```
✅ Backtest (≥5年, alpha-based selection, batch-optimized, sanity-gated, alpha-gate-relaxed)
✅ Walk-Forward (4轮, alpha gate, OOS -5% floor + avg>0)
✅ Portfolio Backtest | ✅ Paper Trading Integrity
✅ Harness Reliability | ✅ SignalRanker Sortino Priority
✅ Strategy Diversity (9 策略 pool, 迭代 #14-15 扩展)
✅ Alpha-Based Selection (迭代 #9)
✅ Batch Backtest Optimization (迭代 #10)
✅ Sanity Gate / Reject Degenerate (迭代 #11)
✅ Alpha Gate (迭代 #12 引入, 迭代 #16 放宽至 -2%)
✅ WF Gate Alpha Validation (迭代 #13)
✅ Iter #16 reoptimize 完成 (2/6 组有权重, -2% gate 解锁 2 策略)
⬜ Paper Trade ≥1月 | ⬜ Live
```

---

> **Orchestrator 验证记录** (自动追加)
> - 迭代状态: passed
> - 测试: 707 passed, 0 failed
> - 违规: 0 条
> - 高风险文件: 0 个
> - 测试数变化: 675 → 707
> - CodeBuddy 自行更新了 trajectory ✅

---

> **Orchestrator 验证记录** (自动追加)
> - 迭代状态: passed
> - 测试: 0 passed, 0 failed
> - 违规: 0 条
> - 高风险文件: 0 个
> - 测试数变化: 675 → 707
> - CodeBuddy 自行更新了 trajectory ✅

---

> **Orchestrator 验证记录** (自动追加)
> - 迭代状态: passed
> - 测试: 0 passed, 0 failed
> - 违规: 0 条
> - 高风险文件: 0 个
> - 测试数变化: 737 → 744
> - CodeBuddy 自行更新了 trajectory ✅

---

## 迭代 #17 — 按 iterations/iteration_17/spec.md 进行开发。关键目标：通过 Sortino 豁免让高 Sortino 策略绕过 alpha 门槛，解锁 SPX 策略组。按 Implementation Order（§6）逐步实施：1) 读取 matrix_backtest.py::_run_group 定位 alpha gate；2) 添加 SORTINO_ALPHA_EXEMPTION = 1.5 常量；3) 修改 Tier 1 过滤：alpha > -2% OR sortino > 1.5；4) 写 ~7 个新测试（高 Sortino 豁免、低 Sortino 仍需 alpha、DD 仍强制、最低 Sortino 仍强制、边界测试）；5) 运行全部测试；6) 运行 --reoptimize；7) 验证 strategy_weights.json 至少 1 个 SPX 组非空；8) 更新 trajectory + CODEBUDDY。严格遵守 scope：不改策略/indicators/risk/execution/main.py。

- **日期**: 2026-07-08 10:12 UTC
- **类型**: 自动化迭代 (Orchestrator → CodeBuddy via ACP)
- **变更摘要**: 按 iterations/iteration_17/spec.md 进行开发。关键目标：通过 Sortino 豁免让高 Sortino 策略绕过 alpha 门槛，解锁 SPX 策略组。按 Implementation Order（§6）逐步实施：1) 读取 matrix_backtest.py::_run_group 定位 alpha gate；2) 添加 SORTINO_ALPHA_EXEMPTION = 1.5 常量；3) 修改 Tier 1 过滤：alpha > -2% OR sortino > 1.5；4) 写 ~7 个新测试（高 Sortino 豁免、低 Sortino 仍需 alpha、DD 仍强制、最低 Sortino 仍强制、边界测试）；5) 运行全部测试；6) 运行 --reoptimize；7) 验证 strategy_weights.json 至少 1 个 SPX 组非空；8) 更新 trajectory + CODEBUDDY。严格遵守 scope：不改策略/indicators/risk/execution/main.py。
- **执行时长**: 1769s (29.5min)
- **状态**: passed
- **CodeBuddy 更新数**: 4393
- **工具调用数**: 244
- **团队事件数**: 0
- **权限请求数**: 0

### 变更文件
.codebuddy/notes/experience.md, alignment/decision_log.md, mytrader/designs/design_v2/07-backtest-module.md, mytrader/mytrader/backtest/matrix_backtest.py, mytrader/tests/test_alpha_gate.py, iterations/iteration_17/

### 测试结果
0 passed, 0 failed (before=744, after=751, delta=+7)

### 违规详情
- ✅ 无违规

### Constitution 合规
- DD 20% 约束: ✅
- 测试覆盖率: ✅ 不降 (before=744, after=751)
- 黑箱策略: ✅ 未引入
- RL 引入: ✅ 未引入
- 文档同步: ⚠️ CodeBuddy 未更新，orchestrator 自动补写

### CodeBuddy 响应摘要（自动提取）
1→# Iteration #8 — Trend-Filtered Mean Reversion 策略
   2→
   3→> 日期：2026-07-04
   4→> 类型：策略新增
   5→> 状态：implemented
   6→
   7→## 1. 目标
   8→
   9→新增 **RSI Trend Filter** 策略（`rsi_trend_filter`），在经典 RSI 均值回归信号上叠加 200 日 SMA 趋势过滤，降低单边趋势中的逆势假信号风险。
  10→
  11→## 2. 策略设计
  12→
  13→### 信号规则
  14→
  15→| 条件 | 信号 |
  16→|------|------|
  17→| RSI < oversold **AND** close > SMA(200) | BUY (+1) — 上升趋势中的超卖 |
  18→| RSI > overbought **AND** close < SMA(200) | SELL (-1) — 下降趋势中的超买 |
  19→| 其他 | HOLD (0) |
  

### Experience Learned
- 迭代通过 ACP 协议执行，状态: passed
- trajectory_updated_by_codebuddy: False
- decision_log_updated_by_codebuddy: False

### 后续建议
- 检查测试是否全部通过
- 无高风险文件触及

---
