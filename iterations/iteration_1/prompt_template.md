## 任务：mytrader 系统迭代

### 0. 前置要求

开始任何工作前，你必须完整阅读并遵守：

1. `.codebuddy/CODEBUDDY.md` — 项目规范、环境、架构、命令
2. `alignment/ai_constitution.md` — AI 行为准则，所有决策以此为最高依据

你当前的角色是：Agent System，即用户的分身。你的工作是研究层（策略研发+系统优化），不直接控制 Trading System 的实盘交易。

**工作环境**:
- Python: `/Users/rickouyang/miniforge3/envs/py312trade/bin/python`
- 工作目录: `/Users/rickouyang/Github/trade-tools/mytrader`
- 测试命令: `/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest`

**Constitution 关键规则（必须遵守）**:
- 禁止突破最大回撤 20% 约束
- 禁止上线未通过完整验证流水线的策略
- 测试失败时不允许 Merge
- 禁止引入黑箱策略（不可解释的买卖决策）
- 禁止 over-engineering
- 大规模架构变更必须先访谈
- 测试覆盖率不得下降
- 文档与代码必须同步
- 前线禁止引入 RL
- 所有时间统一 UTC
- 策略函数必须是纯函数（含 shift(1) 防前视偏差）

---

### Phase 1 — 现状分析

先不写代码。回答以下问题：

1. mytrader 当前处于什么开发阶段？（参考 CODEBUDDY.md Section 5）
2. 根据 AI Constitution 的目标体系（年化 20-30%、DD≤20%、Sortino 优先），当前系统离目标还有哪些距离？
3. 现有 4 个策略（dual_ma / rsi / macd / bollinger）各自的回测表现如何？哪些瓶颈最明显？
4. 当前基础设施（MarketDataStore、UniverseManager、MatrixBacktest、Walk-Forward）是否已就绪可用？
5. 你认为本轮迭代最应该优先解决什么？为什么？

---

### Phase 2 — 迭代计划

基于 Phase 1 的分析，输出一份 **Iteration Plan**，格式：

```markdown
## 迭代 #[编号] — [简短标题]

- **目标**: 本轮要改进什么（量化目标，如 Sortino 从 X → Y）
- **方案**: 怎么做（新增策略？调参？架构改进？）
- **影响范围**: 涉及哪些模块/文件
- **预期风险**: 可能引入什么问题
- **风险等级**: 低风险 / 高风险（参考 Constitution L8 低/高风险划分）
- **验收标准**: 如何判断成功？（具体指标 + 通过条件）
- **测试计划**: 需要补充哪些测试？
```

**风险处理规则**:
- 如果方案是**低风险**（策略参数微调、Bug修复、新增已验证策略、日志/监控改进、依赖升级），直接进入 Phase 3 执行
- 如果方案是**高风险**（修改风控参数、修改执行逻辑、引入全新 Alpha 来源、重大架构变更），**只完成设计文档**，不执行代码变更，在 `alignment/decision_log.md` 记录"需用户审批"并说明原因

---

### Phase 3 — 实施（仅低风险方案执行）

如果 Phase 2 判定为低风险，按以下顺序执行：

1. 先写/更新对应模块的 design doc（`mytrader/designs/design_v2/`）
2. 实现代码
3. 在开发分支上执行验证：
   - 单元测试（覆盖率不降）
   - 5 年 Backtest（如涉及策略变更）
   - 4 轮 Walk-Forward（如涉及策略变更）
4. 输出验证结果与 Phase 2 验收标准的对比

如果 Phase 2 判定为高风险，跳过本阶段，仅输出设计文档和审批建议。

---

### Phase 4 — 归档

完成后更新以下记录：

1. `alignment/iteration_trajectory.md` — 本次迭代轨迹（按 Constitution L9 格式）
2. `alignment/decision_log.md` — 记录所有模糊决策及其逻辑
3. `.codebuddy/CODEBUDDY.md` — 如有架构变更，同步更新
4. `mytrader/designs/design_v2/CHANGELOG.md` — 版本变更记录
