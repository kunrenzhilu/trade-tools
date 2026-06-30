# AI Alignment Interview — 进度存档

> 访谈日期: 2026-06-27 / 2026-06-29  
> 状态: ✅ **全部完成（9/9 层）**
>
> 最终产物: [ai_constitution.md](./ai_constitution.md)

---

## L0 — Vision ✅

<details>
<summary>展开</summary>

```text
Vision Model

Mission:
构建一个稳定、稳健、可追溯的量化交易平台，交易美股，
策略风格为中长线，目标年化收益 ~20%（比大盘好即可）。

North Star:
一个利用 AI 持续进化交易策略的自动交易平台。

Success (1 year):
系统稳定运行，达成目标年化收益。

Primary Value (排序):
1. 收益
2. 风险控制
3. 自动化
4. 可扩展
5. 可维护
6. 可研究

战略定位: 退休后稳定被动收入

架构边界:
- Trading System = 纯规则执行，零 AI
- Agent System = 策略研发+监控（用户分身），不直接控制交易

重构态度:
- 小重构可直接做+通知
- 大规模重构需重新访谈，说明原因/问题/为何不能迭代
```
</details>

---

## L1 — Objectives ✅

<details>
<summary>展开</summary>

```text
市场: 美股
Broker: Alpaca + IBKR（双券商）
交易频率: 中长线

目标收益: 年化 20%-30%（20%为锚，稳健优先）
收益底线: 年化 10%
最大回撤: ≤ 20%（硬性约束）

首要 KPI: Sortino 比率（DD≤20% 约束下）
次要 KPI: Calmar 比率

Trade-off:
- 回撤约束 > 收益
- 可接受收益降换稳定，但不能低于 10%
- AI 运维成本不计入
```
</details>

---

## L2 — Constraints ✅

<details>
<summary>展开</summary>

```text
运行模式: Live + Paper + Backtest + Replay
环境: macOS（开发）+ 腾讯云 2C2G 服务器（运行）
延迟: 处理全链路须在扫描周期内完成
预算: 数据订阅 ≤$100/月
资源: GPU/云服务接受但需 ROI 说明
沟通: Telegram Bot 主动通知用户
```
</details>

---

## L3 — Trading Philosophy ✅

<details>
<summary>展开</summary>

```text
Alpha: Hybrid（前期简单因子，后期迭代丰富）
AI 自主权: 提出新策略✅ 调参✅ 淘汰✅
解释性: 每笔决策可解释（B级），ML 倾向 LR/Tree
RL: 前中期不考虑
老策略: 保留作研究对照，不 deploy
```
</details>

---

## L4 — System Architecture ✅

<details>
<summary>展开</summary>

```text
风格: Layered + Modular
扩展性: ✅ 但不能 over-engineering
AI 重构: ✅ 小规模，需 Git 管理
```
</details>

---

## L5 — Runtime Behaviour ✅

<details>
<summary>展开</summary>

```text
Broker 断连: 重试3次(1min间隔) → 通知+暂停
数据断连: 自动切换源 → 双 fail 暂停+通知
订单被拒: AI 修 bug → 自动重试 → 仍失败通知+暂停
重启: 自动恢复+发汇总通知
数据异常: 暂停该标的，其他继续，通知
策略老化: 继续运行，通知用户+Agent System
```
</details>

---

## L6 — Code Principles ✅

<details>
<summary>展开</summary>

```text
范式: Hybrid（数据class + 逻辑纯函数）
测试: 新功能配测试，覆盖率不降，旧测试同步清理
注释: 复杂场景充分解释，注释 why 不只是 what
文档: 每模块独立 design doc，架构变更同步更新
第三方库: 接受，需可靠（高 star）
性能: 性能优先于可读性
```
</details>

---

## L7 — Testing & Verification ✅

<details>
<summary>展开</summary>

```text
验证流水线: Backtest(≥5年) → WF(4轮) → Paper(≥1月) → Live
硬性: 完整测试后上线 / 测试失败不 Merge / 不变覆盖率换收益
```
</details>

---

## L8 — AI Decision Rubrics ✅

<details>
<summary>展开</summary>

```text
Top 10 刚性排序:
1. Safety > Speed
2. Stability > Flexibility
3. Long-term > Short-term
4. Reliability > Innovation
5. Explainability > ML
6. Stability > Refactor
7. Optimization > Generality
8. Simplicity > Feature Richness
9. Flexibility > Simplicity
10. Memory > Latency

上下文: Performance vs Maintainability 优先兼得，冲突时通知用户

低风险自动 / 高风险审批
Research 与 Production 并行
```
</details>

---

## L9 — Evolution Strategy ✅

<details>
<summary>展开</summary>

```text
AI 自主权: 提出策略/调参/淘汰/小重构/新增模块/升级依赖/日志/文档/目录/API
需审批: 删除模块
大规模架构: 需重新访谈
技术债: 记录，下次顺手修
```
</details>

---

## 产物

- [x] [ai_constitution.md](./ai_constitution.md) — AI Constitution（Agent System 最高行为准则）
- [x] 本文档 — 访谈进度存档
