# Questionnaire.md

# AI Alignment Interview v2

## Purpose

本问卷用于让 AI Agent 与用户建立长期开发共识（Alignment）。

目标不是收集答案，而是建立一套能够指导未来所有开发决策的 Mental Model。

Interview 完成后，AI 应生成：

* Alignment_Result.md
* AI_Rubrics.json（内部）
* Interview Summary

---

# Interview Rules

AI 必须遵守：

1. 一次只提一个问题。
2. 不允许一次展示整个问卷。
3. 每个 Layer 完成后必须总结自己的理解。
4. 用户确认之后才能进入下一 Layer。
5. 如果回答模糊，必须继续追问。
6. 能推断出的答案，不再重复询问。
7. 所有 Trade-off 只记录偏好，不进行争论。
8. 若后续回答与前面冲突，应重新确认相关 Layer。

---

# L0 — Vision

> Goal：
>
> 理解为什么要做这个平台。

### Direct Questions

Q1

一句话描述这个平台。

---

Q2

最终希望它变成什么？

* 自用工具
* 自动交易平台
* AI Research Platform
* Hedge Fund Infrastructure
* 其它

---

Q3

一年后什么叫成功？

---

Q4

如果未来只能保留一个价值：

* 收益
* 风险
* 自动化
* 可扩展
* 可维护
* 可研究

---

### Inference Questions

Scenario V1

为了实现最终目标。

需要重构整个系统。

是否接受？

---

### Layer Summary

AI 输出：

```text
Vision Model

Mission:
...

North Star:
...

Primary Value:
...
```

用户确认。

---

# L1 — Objectives

> Goal：
>
> 定义所有优化目标。

### Direct Questions

目标市场：

目标 Broker：

目标交易频率：

目标收益：

最大 DD：

最重要 KPI：

---

### Inference Questions

Scenario O1

收益增加 20%。

最大 DD 增加 8%。

接受吗？

---

Scenario O2

收益下降。

稳定性提高很多。

接受吗？

---

Scenario O3

收益不变。

维护成本下降。

接受吗？

---

Layer Summary

Objective Model

---

# L2 — Constraints

> Goal：
>
> AI 必须知道哪些边界不能碰。

### Direct Questions

必须支持：

Live？

Backtest？

Replay？

Paper？

Broker？

OS？

GPU？

Cloud？

Database？

Latency？

Budget？

---

### Inference Questions

Scenario C1

增加 GPU。

收益明显提升。

接受吗？

---

Scenario C2

增加云服务。

开发速度提升。

接受吗？

---

Scenario C3

增加外部依赖。

维护复杂度增加。

接受吗？

---

Layer Summary

Constraint Model

---

# L3 — Trading Philosophy

> Goal：
>
> AI 理解交易思想，而不是交易规则。

### Direct Questions

Alpha 来源：

更相信：

Trend

MR

Momentum

ML

RL

Portfolio

Execution

Hybrid

是否允许 AI 提出新策略？

是否允许 AI 调参？

是否允许 AI 淘汰策略？

---

### Inference Questions

Scenario T1

新策略历史收益明显更高。

但不可解释。

接受吗？

---

Scenario T2

一个老策略收益下降。

是否保留研究价值？

---

Scenario T3

RL 收益高于 Rule-Based。

接受迁移吗？

---

Layer Summary

Trading Philosophy Model

---

# L4 — System Architecture

> Goal：
>
> AI 学习软件架构偏好。

### Direct Questions

Architecture：

Event？

Actor？

Plugin？

Layered？

Monolith？

Microservice？

DDD？

Modular？

---

### Inference Questions

Scenario A1

为了未来扩展。

增加 30% 代码。

接受吗？

---

Scenario A2

为了减少复杂度。

牺牲未来扩展。

接受吗？

---

Scenario A3

是否允许 AI 主动重构？

---

Layer Summary

Architecture Model

---

# L5 — Runtime Behaviour

> Goal：
>
> 定义系统运行原则。

### Direct Questions

Broker Disconnect：

Market Data Disconnect：

Order Reject：

Clock Drift：

Restart：

Recovery：

Logging：

Monitoring：

Alert：

---

### Inference Questions

Scenario R1

未知错误。

继续运行？

停止？

---

Scenario R2

数据异常。

是否暂停交易？

---

Scenario R3

低信心状态。

是否停止所有交易？

---

Layer Summary

Runtime Model

---

# L6 — Code Principles

> Goal：
>
> AI 学习工程哲学。

### Direct Questions

OOP？

FP？

Hybrid？

Dependency？

Testing？

Logging？

Naming？

Documentation？

Comment？

Code Review？

---

### Inference Questions

Scenario P1

性能提高。

复杂度增加。

接受？

---

Scenario P2

第三方库减少 3000 行代码。

接受？

---

Scenario P3

重构没有功能收益。

是否做？

---

Layer Summary

Engineering Model

---

# L7 — Testing & Verification

> Goal：
>
> AI 学习交付标准。

### Direct Questions

Unit Test？

Integration？

Regression？

Benchmark？

Simulation？

Walk Forward？

Paper Trade？

Coverage？

---

### Inference Questions

Scenario TV1

收益提高。

测试覆盖下降。

接受？

---

Scenario TV2

Benchmark 变慢。

代码更简单。

接受？

---

Scenario TV3

测试失败。

是否允许 Merge？

---

Layer Summary

Testing Model

---

# L8 — AI Decision Rubrics

> Goal：
>
> 建立所有 Trade-off 权重。

以下问题全部采用：

Yes

No

Depends

并追问原因。

Trade-offs：

* Performance vs Readability
* Performance vs Maintainability
* Simplicity vs Flexibility
* Flexibility vs Stability
* Speed vs Safety
* Automation vs Human Approval
* ML vs Explainability
* Dependency vs Self-Implemented
* Short-term vs Long-term
* Refactor vs Stability
* Research vs Production
* Latency vs Memory
* Feature Richness vs Simplicity
* Generality vs Optimization
* Innovation vs Reliability

Layer Summary：

Decision Rubrics

（自动生成权重）

---

# L9 — Evolution Strategy

> Goal：
>
> 定义 AI 在未来拥有多少自主权。

### Direct Questions

AI 是否允许：

新增模块？

删除模块？

自动调参？

自动重构？

自动升级依赖？

自动新增日志？

自动新增测试？

自动生成文档？

自动修改目录？

自动修改 API？

自动停止交易？

自动恢复交易？

哪些事情必须经过你的批准？

---

### Inference Questions

Scenario E1

AI 发现一个明显更好的架构。

应该？

---

Scenario E2

AI 发现一个长期技术债。

应该？

---

Scenario E3

AI 发现一个收益更高的新方向。

应该？

---

Layer Summary

Evolution Model

---

# Final Alignment

Interview 完成后，AI 自动生成：

* Vision Model
* Objective Model
* Constraint Model
* Trading Philosophy Model
* Architecture Model
* Runtime Model
* Engineering Model
* Testing Model
* Decision Rubrics
* Evolution Strategy

然后生成：

Alignment_Result.md

作为未来所有开发工作的唯一事实来源（Single Source of Truth）。
