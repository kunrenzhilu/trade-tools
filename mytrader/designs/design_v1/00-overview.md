# MyTrader 系统设计总览

> 版本：v0.2（Phase 1 完成后更新）  
> 时间：2026-06-13  
> 定位：轻量级日间交易系统，面向港美股个人投资者  
> 回测框架：VectorBT 1.0.0

---

## 1. 设计目标

| 目标 | 说明 |
|------|------|
| **持仓周期** | 日内（当天开当天平）到短线（持仓 1–5 天） |
| **延迟要求** | 秒级，不追求微秒 |
| **自动化程度** | 信号自动生成，执行半自动（人工确认 or 全自动可配） |
| **可维护性** | 纯 Python，模块解耦，单模块可独立替换 |
| **回测一致性** | 回测与实盘共用同一套策略逻辑，避免"回测好、实盘差"的策略漂移 |

---

## 2. 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        MyTrader                             │
│                                                             │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐                │
│  │  Data    │──▶│ Strategy │──▶│  Signal  │                │
│  │  Layer   │   │  Engine  │   │  Filter  │                │
│  └──────────┘   └──────────┘   └──────────┘                │
│                                      │                      │
│                               ┌──────▼──────┐              │
│                               │    Risk     │              │
│                               │  Manager   │              │
│                               └──────┬──────┘              │
│                                      │                      │
│  ┌──────────┐   ┌──────────┐   ┌──────▼──────┐            │
│  │ Monitor  │◀──│Portfolio │◀──│  Execution  │            │
│  │  Layer   │   │ Tracker  │   │   Engine    │            │
│  └──────────┘   └──────────┘   └─────────────┘            │
│                                                             │
│  ──────────── 横切关注点 ────────────────                   │
│  │  Config Manager  │  Logger  │  EventBus  │              │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 模块清单

| # | 模块 | 文档 | 核心职责 |
|---|------|------|---------|
| 1 | Data Layer | [01-data-layer.md](./01-data-layer.md) | 行情获取、清洗、缓存 |
| 2 | Strategy Engine | [02-strategy-engine.md](./02-strategy-engine.md) | 指标计算、信号生成 |
| 3 | Signal Filter | [03-signal-filter.md](./03-signal-filter.md) | 信号确认、去噪、频率控制 |
| 4 | Risk Manager | [04-risk-manager.md](./04-risk-manager.md) | 仓位计算、止损止盈、熔断 |
| 5 | Execution Engine | [05-execution-engine.md](./05-execution-engine.md) | 券商 API、订单管理、滑点 |
| 6 | Portfolio Tracker | [06-portfolio-tracker.md](./06-portfolio-tracker.md) | 持仓记录、盈亏计算、对账 |
| 7 | Backtest Module | [07-backtest-module.md](./07-backtest-module.md) | VectorBT 回测、参数优化、报告 |
| 8 | Monitor Layer | [08-monitor-layer.md](./08-monitor-layer.md) | 告警、日志、健康检查 |
| 9 | Infrastructure | [09-infrastructure.md](./09-infrastructure.md) | Config / EventBus / Logger |

---

## 4. 数据流说明

```
1. Data Layer 拉取行情（定时或实时）
2. Strategy Engine 消费行情，输出 Signal（BUY/SELL/HOLD + 置信度）
3. Signal Filter 对 Signal 进行二次过滤，输出 FilteredSignal
4. Risk Manager 读取 FilteredSignal + 当前持仓，输出 OrderIntent（含仓位大小）
5. Execution Engine 将 OrderIntent 转换为真实订单，提交到券商，回传 OrderResult
6. Portfolio Tracker 消费 OrderResult，更新持仓状态
7. Monitor Layer 全程监听，推送告警
```

---

## 5. 技术选型

| 层次 | 技术 | 版本（已安装） | 理由 |
|------|------|--------------|------|
| 语言 | Python 3.11+ | 3.11.15 | 生态最完整 |
| 回测 | VectorBT | 1.0.0 | 向量化计算快，参数优化原生支持 |
| 数据获取 | `yfinance` | 1.4.1 | 免费，覆盖港美股，Phase 1 使用 |
| 数据处理 | `pandas` + `numpy` | 2.3.3 / 2.4.6 | 标准 |
| 数据缓存 | `pyarrow`（Parquet） | 24.0.0 | 列式存储，pandas 读写极快 |
| 技术指标 | `pandas-ta` 0.4.71b0 | 已安装 | 130+ 指标，经平台验证；`indicators.py` 封装其接口，策略层无感知；需 Python 3.12+ |
| 可视化 | `plotly` | 6.8.0 | 回测 HTML 报告 |
| 配置 | YAML + Pydantic | — | 类型安全 |
| 日志 | `loguru` | 0.7.3 | 结构化日志，比 logging 更易用 |
| 券商执行（Phase 2）| `alpaca-py` | — | Alpaca 美股，Python 友好 |
| 券商执行（Phase 3）| `ib_insync` | — | IBKR 港美股，生产推荐 |
| 调度（Phase 2+）| `APScheduler` | — | 轻量定时任务 |
| 持久化（Phase 2+）| SQLite + SQLAlchemy | — | 开发阶段 SQLite，生产可换 PostgreSQL |
| 告警（Phase 3）| Telegram Bot | — | 低成本推送 |

> **Python 环境**：`/Users/rickouyang/miniforge3/envs/py311trade`

---

## 6. 分阶段实施路线

### Phase 1 — 策略验证（✅ 已完成）
- [x] Data Layer：yfinance 数据拉取 + 本地 Parquet 缓存 + 数据清洗/校验
- [x] Strategy Engine：4 个基础策略（双均线、RSI、布林带、MACD）+ 技术指标纯函数库 + Ensemble 聚合
- [x] Backtest Module：VectorBT 集成，`BacktestRunner` 单次回测 + 网格参数优化；`BacktestReport` 生成 HTML+CSV 报告
- [x] 单元测试 29 个（含前视偏差专项测试 4 个，全部通过）
- [x] 输出：4 策略在 AAPL 2022–2025 回测有效（布林带 Sharpe 0.96，Beat 基准）

### Phase 2 — 半自动执行
- [ ] Signal Filter：过滤低质量信号
- [ ] Risk Manager：固定仓位 + 止损逻辑
- [ ] Execution Engine：手动确认模式（生成订单 JSON，人工点击）
- [ ] Portfolio Tracker：基础持仓状态记录
- [ ] 输出：人工辅助执行，积累真实交易数据

### Phase 3 — 全自动化
- [ ] Execution Engine：接入 IBKR / Alpaca 自动下单
- [ ] Monitor Layer：实时告警 + 熔断
- [ ] 完善对账和风控
- [ ] 输出：24/7 无人值守运行

---

## 7. 关键设计原则

1. **回测/实盘一致性**：策略逻辑写在独立函数中，不依赖任何框架对象，回测和实盘都调用同一套函数。
2. **模块边界清晰**：每个模块只通过定义好的 Interface 通信，不直接依赖其他模块的内部实现。
3. **失败安全（Fail-Safe）**：任何一个模块崩溃，系统应停止下单，而不是以错误状态继续执行。
4. **可观测性优先**：所有关键决策点必须留日志，方便事后复盘。
5. **单一数据源**：Portfolio 状态以券商账户为唯一真相来源（Source of Truth），本地记录只做参考。

---

## 参考来源

- [VectorBT 官方文档](https://vectorbt.dev/)
- [Alpaca Markets Python SDK](https://alpaca.markets/sdks/python/)
- [ib_insync 文档](https://ib-insync.readthedocs.io/)
- [Quantopian Lecture Series](https://github.com/quantopian/research_public)
- *Advances in Financial Machine Learning* — Marcos López de Prado
- *Algorithmic Trading: Winning Strategies* — Ernest Chan
