# Orchestrator-CodeBuddy 监控循环方案

> 创建日期: 2026-06-30
> 目标: 构建 AI 监控循环，让 CodeBuddy 作为主力开发者迭代 mytrader，GLM 作为监控者

---

## 1. 架构总览

```
┌────────────────────────────────────────────────────────────────┐
│  Orchestrator (GLM-5.2 / 我)                                  │
│                                                                │
│  职责:                                                         │
│  1. 读取 ai_constitution.md → 提取规则、目标、禁止行为         │
│  2. 定义每次迭代的具体目标 (Phase 6 任务拆解)                 │
│  3. 通过 ACP 协议向 CodeBuddy 发送开发任务                    │
│  4. 实时监控 CodeBuddy 的工作（工具调用、团队事件、进度）      │
│  5. 迭代结束后验证 Constitution 合规性                          │
│  6. 记录到 iteration_trajectory.md 和 decision_log.md         │
│  7. 在需要并行调研时，指示 CodeBuddy 发起 Agent Teams          │
└──────────────────────┬─────────────────────────────────────────┘
                       │ ACP Protocol (JSON-RPC over stdio)
                       │ spawn_agent_process("codebuddy", "--acp", ...)
                       ▼
┌────────────────────────────────────────────────────────────────┐
│  CodeBuddy --acp (主力开发者)                                 │
│                                                                │
│  配置:                                                         │
│  - --permission-mode bypassPermissions (自主执行)             │
│  - --append-system-prompt (注入 Constitution 规则)             │
│  - --max-turns (限制每轮迭代范围)                              │
│                                                                │
│  能力:                                                         │
│  - 读写代码、运行测试、执行命令                                │
│  - 自主发起 Agent Teams (TeamCreate + 成员派发)               │
│  - 多轮会话 (--resume / session_id)                            │
│  - 流式输出 session_update (实时监控)                         │
└────────────────────────────────────────────────────────────────┘
```

---

## 2. 调研结论

### 2.1 CodeBuddy 能否自主发起 Agent Teams？

**结论: ✅ 可以**

测试验证：
- 通过 ACP prompt 指示 CodeBuddy 创建团队，它成功调用了 `TeamCreate` 工具
- 创建了 `research-team`，派出 `backtest-explorer` 和 `signal-explorer` 两个成员
- 成员并行工作，通过 `_meta['codebuddy.ai/teamUpdate']` 和 `_meta['codebuddy.ai/memberEvent']` 推送事件
- 工作完成后正确发送 `shutdown_request` 并等待响应

**关键前提**: 必须使用 `--permission-mode bypassPermissions`，否则 `DeferExecuteTool`（包装 TeamCreate）的权限会被拒绝

### 2.2 ACP 协议支持情况

| 能力 | 支持状态 | 说明 |
|------|----------|------|
| 多轮会话 | ✅ | 同一 session_id 可持续对话 |
| 流式更新 | ✅ | `session_update` 实时推送文本、工具调用、进度 |
| 权限控制 | ✅ | `request_permission` 回调，需返回 `SelectedPermissionOutcome` |
| Agent Teams | ✅ | 通过 `_meta` 扩展推送 team/member 事件 |
| 会话恢复 | ✅ | `loadSession` + `replayHistory` |
| 工具调用代理 | ✅ | 客户端可代理 `fs.readTextFile` 等 |

### 2.3 权限处理要点

```python
# ❌ 错误格式（会导致 deny）
return {"outcome": {"outcome": "approved"}}

# ✅ 正确格式（从 options 中选择 allow 选项）
for opt in options:
    if 'allow' in opt.kind:
        return {"outcome": {"outcome": "selected", "optionId": opt.optionId}}

# ✅ 或者直接用 --permission-mode bypassPermissions 绕过
```

---

## 3. 迭代循环设计

### 3.1 循环流程

```
┌─── 加载 Constitution & Trajectory ──────────────────────────┐
│                                                              │
│  读取 ai_constitution.md → 提取:                             │
│    - 禁止行为清单 (12条)                                    │
│    - 决策权重矩阵 (15项优先级)                               │
│    - 验证流水线门槛 (Backtest→WF→Paper→Live)               │
│    - 高/低风险变更分类                                       │
│                                                              │
│  读取 iteration_trajectory.md → 提取:                        │
│    - 上一次迭代编号                                          │
│    - 历史经验教训                                            │
│    - 后续建议                                                │
└──────────────────────────┬───────────────────────────────────┘
                           ▼
┌─── 定义迭代目标 ────────────────────────────────────────────┐
│                                                              │
│  根据 Phase 6 目标拆解:                                      │
│    1. 安装 alpaca-py，实现 AlpacaBroker auto 模式           │
│    2. 对账模块与真实券商数据集成                             │
│    3. 港股支持 (ib_insync)                                  │
│                                                              │
│  每次迭代选择一个子任务，定义:                               │
│    - 具体目标 (可验证)                                       │
│    - 预期产出 (代码/测试/文档)                               │
│    - 验证标准 (测试通过、覆盖率不降)                         │
│    - 风险等级 (低/高)                                       │
└──────────────────────────┬───────────────────────────────────┘
                           ▼
┌─── 发送任务给 CodeBuddy ────────────────────────────────────┐
│                                                              │
│  构造 prompt:                                                │
│    "你是 mytrader 的开发者，遵循 ai_constitution.md。        │
│     本次迭代目标: [具体任务]                                 │
│     约束:                                                    │
│     - 不得突破 DD 20% 约束                                  │
│     - 测试覆盖率不得下降                                     │
│     - 测试失败不允许 merge                                   │
│     - 重大决策须记录到 decision_log.md                      │
│     完成后更新 iteration_trajectory.md"                      │
│                                                              │
│  通过 ACP conn.prompt() 发送                                 │
└──────────────────────────┬───────────────────────────────────┘
                           ▼
┌─── 实时监控 ────────────────────────────────────────────────┐
│                                                              │
│  session_update 事件流:                                      │
│    - field_meta.codebuddy.ai/agentPhase → 工作阶段           │
│    - field_meta.codebuddy.ai/toolName → 工具调用              │
│    - field_meta.codebuddy.ai/teamUpdate → 团队事件           │
│    - field_meta.codebuddy.ai/memberEvent → 成员消息          │
│    - field_meta.codebuddy.ai/usageByCategory → Token 用量   │
│                                                              │
│  监控检查点:                                                 │
│    - [ ] 是否调用了禁止的工具？(RL相关)                      │
│    - [ ] 是否修改了风控参数？(高风险，需审批)               │
│    - [ ] 是否在测试失败时继续？                              │
│    - [ ] 是否默默执行重大决策？                              │
└──────────────────────────┬───────────────────────────────────┘
                           ▼
┌─── 迭代后验证 ──────────────────────────────────────────────┐
│                                                              │
│  1. 运行测试:                                                │
│     pytest --tb=short -q                                     │
│     检查: 通过数 ≥ 上次、无新增失败                          │
│                                                              │
│  2. Constitution 合规检查:                                   │
│     - git diff 检查是否触及禁止区域                          │
│     - 检查是否有黑箱策略引入                                 │
│     - 检查是否有未测试代码上线                               │
│                                                              │
│  3. 文档同步检查:                                            │
│     - CODEBUDDY.md 是否更新                                  │
│     - design doc 是否更新                                    │
│     - iteration_trajectory.md 是否记录                       │
│                                                              │
│  4. 结果分类:                                                │
│     ✅ 通过 → 记录轨迹，进入下一迭代                         │
│     ⚠️ 部分通过 → 发送修正 prompt 给 CodeBuddy              │
│     ❌ 失败 → 记录失败原因，通知用户                         │
└──────────────────────────┬───────────────────────────────────┘
                           ▼
┌─── 记录 & 决策 ─────────────────────────────────────────────┐
│                                                              │
│  更新 iteration_trajectory.md:                               │
│    ## 迭代 #N — [描述]                                       │
│    - 日期、类型、变更摘要                                    │
│    - 回测结果、WF结果、Paper结果                             │
│    - Experience Learned                                       │
│    - 后续建议                                                 │
│                                                              │
│  更新 decision_log.md (如有):                                │
│    - 困境描述、涉及条款、决策逻辑、决策结果                  │
│                                                              │
│  如果 Constitution 需要修订 → 通知用户                       │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           └──→ 回到「定义迭代目标」
```

### 3.2 Agent Teams 触发时机

| 场景 | 触发方式 | 团队配置 |
|------|----------|----------|
| 多模块并行调研 | prompt 指示 CodeBuddy 创建团队 | 每模块一个成员 |
| 策略对比实验 | prompt 指示 CodeBuddy 创建团队 | 每策略一个成员 |
| 架构重构评估 | prompt 指示 CodeBuddy 创建团队 | 调研+评估+实现 |

**触发 prompt 模板:**
```
请使用 TeamCreate 工具创建团队 '{team-name}'，
派出以下成员并行工作：
1. '{member-1-name}' — 负责调研 {module-1} 的 {task-1}
2. '{member-2-name}' — 负责调研 {module-2} 的 {task-2}
完成后汇总结果。
```

---

## 4. 技术实现

### 4.1 核心 Python 模块: `orchestrator.py`

位于: `alignment/orchestrator.py`

功能模块:
1. `ConstitutionLoader` — 加载和解析 ai_constitution.md
2. `ACPClient` — ACP 客户端，处理权限和会话更新
3. `IterationManager` — 管理迭代目标和验证
4. `ComplianceChecker` — Constitution 合规检查
5. `TrajectoryLogger` — 记录迭代轨迹和决策日志
6. `TeamMonitor` — 监控 Agent Teams 事件
7. `OrchestratorLoop` — 主循环

### 4.2 关键配置

```python
# CodeBuddy 启动参数
CB_ARGS = [
    "codebuddy", "--acp",
    "--permission-mode", "bypassPermissions",  # 自主执行
    "--max-turns", "50",                       # 限制每轮迭代
]

# Constitution 注入 prompt
SYSTEM_PROMPT_APPEND = """
你正在开发 mytrader 量化交易系统。
必须严格遵循 alignment/ai_constitution.md 中的所有规则。
关键禁止行为:
1. 不得突破最大回撤 20% 约束
2. 不得上线未通过完整验证流水线的策略
3. 测试失败时不得 merge 代码
4. 不得引入黑箱策略
5. 重大决策须记录到 alignment/decision_log.md
每次迭代后更新 alignment/iteration_trajectory.md
"""
```

### 4.3 合规检查规则

```python
FORBIDDEN_PATTERNS = {
    "rl_introduction": r"import.*stable_baselines|import.*gym|reinforcement_learning",
    "dd_threshold_change": r"max_drawdown\s*[<>!=]\s*[^2]|DD.*[<>!=].*[^2]",
    "black_box_strategy": r"class.*BlackBox|class.*DeepLearning.*Strategy",
}

HIGH_RISK_PATTERNS = {
    "risk_param_change": r"stop_loss|position_size|max_dd|circuit_breaker",
    "execution_logic": r"def.*execute_order|def.*place_trade",
    "validation_pipeline": r"BACKTEST_MIN_YEARS|WALK_FORWARD_ROUNDS",
}
```

---

## 5. 使用方式

### 5.1 启动监控循环

```bash
# 单次迭代
python alignment/orchestrator.py --iteration 1

# 持续循环
python alignment/orchestrator.py --loop

# 指定任务
python alignment/orchestrator.py --task "实现 AlpacaBroker auto 模式"
```

### 5.2 我（GLM）的操作流程

当用户要求启动迭代时，我的操作步骤:

1. 读取最新的 `ai_constitution.md` 和 `iteration_trajectory.md`
2. 确定当前迭代目标
3. 运行 `orchestrator.py` 或直接通过 ACP 发送 prompt
4. 监控 `session_update` 事件流
5. 迭代完成后运行验证
6. 更新日志文件
7. 向用户报告结果
