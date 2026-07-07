# Paper Trading 部署报告

> **日期**: 2026-07-03
> **决策**: 用户审批后部署到 Alpaca paper trading 账户
> **依据**: Gate 1 + Gate 2 + Gate 3 全部通过

---

## 执行摘要

经过 4 轮迭代（#1~#4），系统达到 paper trading 入门标准。策略 Sortino 1.98（接近目标 2.0），Portfolio DD 6.65%（远低于 20% 约束），Walk-Forward 4 轮全通过。系统端到端验证无错误。

---

## Gate 1: Strategy Is Not Broken ✅

| 条件 | 阈值 | 实际 | 状态 |
|------|------|------|:----:|
| Sortino | > 0.5 | 1.98 | ✅ |
| Portfolio DD | ≤ 20% | 6.65% | ✅ |
| Walk-Forward | 4 轮无单轮 >15% loss | 4/4, max 3.32% | ✅ |
| 每组策略数 | ≥ 2 | 6/6 | ✅ |
| Portfolio Backtest | 通过 | DD=6.65%, Sortino=1.98 | ✅ |

### Portfolio Backtest 完整结果

| 指标 | 值 | 说明 |
|------|-----|------|
| Portfolio DD | 6.65% | 远低于 20% 约束 |
| Sortino | 1.98 | 接近 2.0 目标 |
| Sharpe | 1.33 | |
| 年化收益 | 15.17% | 低于 20% 锚，但 paper 期间验证实际值 |
| DD Violation | NO | |

### per-group DD（Risk Characteristic，非阻塞）

| Group | Sortino | DD(%) | dd_constrained |
|-------|--------:|------:|:--------------:|
| SPX_mid_vol | 1.57 | 7.37 | False |
| SPX_high_vol | 1.03 | 14.90 | False |
| NDX_high_vol | 1.40 | 22.22 | True（结构性超标，portfolio DD 仅 6.65%）|
| SPX_low_vol | 1.82 | 4.78 | False |
| NDX_mid_vol | 1.71 | 4.04 | False |
| NDX_low_vol | 1.95 | 10.71 | False |

---

## Gate 2: System Is Complete ✅

| 条件 | 验证方式 | 结果 | 状态 |
|------|---------|------|:----:|
| AlpacaBroker 连接 paper 账户 | `health_check()` | connected, cash=$134,902, ACTIVE | ✅ |
| alpaca-py 已安装 | `pip list` | v0.43.4 | ✅ |
| 扫描编排器端到端运行 | `--scan-now morning` | 73 候选 → 2 approved, 0 errors | ✅ |
| Telegram 通知 | 扫描后自动发送 | 已推送 | ✅ |
| 数据源可用 | MarketDataStore | 516 symbols, 643k bars, 最新 2026-07-02 | ✅ |
| 数据同步 | `--backfill` | 515/515 ok | ✅ |
| 持仓对账 | paper 期间验证 | — | ⏳ |
| 1 小时稳定性 | paper 期间验证 | — | ⏳ |

---

## Gate 3: Diminishing Returns ✅

| 信号 | 状态 |
|------|------|
| Sortino 1.98 接近 2.0 目标 | 代码迭代 ROI 递减 |
| 下一步改进需要 live data | Volume filter 行为、实际 DD、滑点 |
| Portfolio Backtest 已完成 | 历史数据验证已到极限 |

---

## 部署详情

### 启动命令
```bash
cd /Users/rickouyang/Github/trade-tools/mytrader
python main.py
```

### Scheduler 自动执行

| 时间 (ET) | 任务 |
|-----------|------|
| 09:35 | Morning scan（盘前扫描） |
| 每 30 min | Intraday check |
| 15:45 | EOD check |
| 16:30 | 数据同步 + 持仓对账 |
| 每月 1 日 | Walk-Forward 重新优化 |

### Paper 期间监控指标

1. **每日**: Telegram 通知的信号数、下单数、错误数
2. **每周**: 实际 portfolio DD（vs backtest 的 6.65%）
3. **每月**: Sortino/Sharpe 计算并与 backtest 基线对比

### Paper 退出条件

| 条件 | 阈值 | 行动 |
|------|------|------|
| 系统崩溃 | 任何 1 次 | 立即调查，修复后继续 paper |
| Portfolio DD | > 20% | 暂停，调查原因 |
| Paper Sortino (4周) | < 0.5 | 回到策略迭代 |
| Paper Sortino (4周) | ≥ 0.5 | 准备 live |
| 稳定运行 | ≥ 1 个月 | 考虑 live 部署 |

---

## 迭代历史

| 迭代 | 类型 | 关键变更 | Portfolio DD | Sortino |
|------|------|---------|:-----------:|:-------:|
| #1 | Bug 修复 | 策略名 bug + Sortino | — | — |
| #2 | KPI 补全 | NaN 安全 + 参数网格 + low_vol 阈值 | — | 1.40 (per-group) |
| #3 | DD 约束 + WF | DD 过滤 + Walk-Forward 4 轮 | 22% (per-group) | 1.40 |
| #4 | Portfolio Backtest | 新增组合层回测 + DD 约束修正 | **6.65%** | **1.98** |

---

## Constitution 合规

| 条款 | 状态 |
|------|:----:|
| L1: Sortino 首要 KPI | ✅ 1.98 |
| L1: Portfolio DD ≤ 20% | ✅ 6.65% |
| L7: Backtest + WF + Portfolio Backtest | ✅ 全通过 |
| L7: Paper Trade ≥ 1 月 | ⏳ 本次部署 |
| L8: 高风险变更用户审批 | ✅ 用户已审批 |
| L8: 研究层 ∥ 生产层 | ✅ Paper 期间继续策略迭代 |
| 不引入 RL | ✅ |
| 不引入黑箱策略 | ✅ |
| 测试覆盖率不降 | ✅ 525 tests |
| 文档与代码同步 | ✅ |
