# MyTrader 系统设计总览

> 版本：v2.0（Phase 5 设计访谈后重构）  
> 时间：2026-06-23  
> 定位：**全自动量化交易系统**，面向美股（S&P 500 + Nasdaq 100），用于持续验证策略有效性并自动执行  
> 回测框架：VectorBT 1.0.0

---

## 0. v2 设计的核心变化（相对 v1）

> v1 把系统设计成"单策略 × 固定几只股票 → 直接下单"的**线性执行流水线**，缺少"从大规模标的中筛选该交易标的"的环节。
> v2 将系统重构为**「离线回测层 + 在线交易层」双层架构**，引入数据驱动的"策略×标的"匹配。

| 维度 | v1（旧） | v2（新） |
|------|---------|---------|
| 系统定位 | 半自动执行 | **全自动**（策略开发由外部系统负责） |
| 标的范围 | 手动配置 6 只 | **S&P 500 + Nasdaq 100（去重 ~550 只）** |
| 策略数量 | 全局 1 个 | **多策略并行**，按标的分组分配 |
| 策略↔标的 | 无概念 | **数据驱动 mapping**（回测产出，非手动） |
| 信号→下单 | 信号直接下单 | **信号排名 → Top-K 才下单** |
| 数据存储 | 按请求 Parquet 缓存 | **本地时序库 + 增量同步**（SQLite 实盘 / DuckDB 回测） |
| 回测范围 | 单标的 3 年 | **全标的 5 年（覆盖完整牛熊周期）** |
| 参数 | 全局固定 | **按标的分组**（波动率/行业/市值），非单只优化 |

---

## 1. 设计目标

| 目标 | 说明 |
|------|------|
| **持仓周期** | 日内到短线（持仓 1–5 天） |
| **核心用途** | **持续测试新策略的有效性**，并将验证有效的策略自动投入实盘 |
| **自动化程度** | 全自动：扫描 → 信号 → 排名 → 风控 → 下单 全链路无人值守 |
| **标的覆盖** | S&P 500 + Nasdaq 100（约 550 只，去重后） |
| **策略来源** | **外部系统开发新策略**，本系统只负责"已有策略的回测验证 + 选股 + 执行" |
| **回测一致性** | 回测与实盘共用同一套策略纯函数 |

---

## 2. 系统架构图（v2 双层架构）

```
┌──────────────────────────── 离线回测层（Offline）────────────────────────────┐
│                                                                              │
│   MarketDataStore ──▶ MatrixBacktest（N策略 × G组 × 参数网格）                 │
│   （本地时序库）          │                                                    │
│                          ▼                                                    │
│                   strategy_weights.json  ← 每组保留 Top-K 策略 + 权重          │
│                   （Walk-Forward 每月更新）                                    │
└──────────────────────────────────┬───────────────────────────────────────────┘
                                    │ 实盘读取权重
                                    ▼
┌──────────────────────────── 在线交易层（Live）──────────────────────────────┐
│                                                                              │
│  DataSyncService ──▶ MarketDataStore ──▶ Universe Manager                     │
│  （增量同步，收盘后）    （SQLite）          （S&P500+Nasdaq100 → 分组）         │
│                                                  │                            │
│                                                  ▼                            │
│                                        Strategy Matrix Runner                 │
│                                        （按组分配策略，输出 M×N 信号）          │
│                                                  │                            │
│                                                  ▼                            │
│                                          Signal Ranker                        │
│                                        （排名 → Top-K 标的）                   │
│                                                  │                            │
│                                                  ▼                            │
│              Signal Filter ──▶ Risk Manager ──▶ Execution ──▶ Portfolio        │
│                                                  │                            │
│                                          Monitor Layer（全程监听）             │
│                                                                              │
│  ──────── 横切关注点：Config / Logger / EventBus / Container / Scheduler ──────│
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 模块清单

### 3.1 已有模块（Phase 1-4）

| # | 模块 | 文档 | 核心职责 |
|---|------|------|---------|
| 1 | Data Layer | [01-data-layer.md](./01-data-layer.md) | 行情获取、清洗、**本地时序库 + 增量同步** |
| 2 | Strategy Engine | [02-strategy-engine.md](./02-strategy-engine.md) | 指标计算、**多策略信号生成、分组参数** |
| 3 | Signal Filter | [03-signal-filter.md](./03-signal-filter.md) | 信号确认、去噪、频率控制 |
| 4 | Risk Manager | [04-risk-manager.md](./04-risk-manager.md) | 仓位计算、止损止盈、熔断 |
| 5 | Execution Engine | [05-execution-engine.md](./05-execution-engine.md) | 券商 API、订单管理、滑点 |
| 6 | Portfolio Tracker | [06-portfolio-tracker.md](./06-portfolio-tracker.md) | 持仓记录、盈亏计算、对账 |
| 7 | Backtest Module | [07-backtest-module.md](./07-backtest-module.md) | **矩阵回测、Walk-Forward、参数网格** |
| 8 | Monitor Layer | [08-monitor-layer.md](./08-monitor-layer.md) | 告警、日志、健康检查 |
| 9 | Infrastructure | [09-infrastructure.md](./09-infrastructure.md) | Config / EventBus / Logger / Scheduler |

### 3.2 Phase 5 新增模块

| # | 模块 | 文档 | 核心职责 |
|---|------|------|---------|
| 10 | **Market Data Store** | [10-market-data-store.md](./10-market-data-store.md) | 本地时序库（SQLite 实盘 / DuckDB 回测）+ DataSyncService 增量同步 |
| 11 | **Universe Manager** | [11-universe-manager.md](./11-universe-manager.md) | S&P 500 + Nasdaq 100 成分股维护、去重、按特征分组 |
| 12 | **Strategy Matrix** | [12-strategy-matrix.md](./12-strategy-matrix.md) | M 策略 × N 标的批量运行，按组分配策略 |
| 13 | **Signal Ranker** | [13-signal-ranker.md](./13-signal-ranker.md) | 多信号聚合、排名、Top-K 选股 |

> 矩阵回测（MatrixBacktest）作为 Backtest Module 的扩展，详见 [07-backtest-module.md](./07-backtest-module.md)。

---

## 4. 数据流说明（v2）

### 4.1 离线回测层（每月触发 / 手动触发）

```
1. MarketDataStore 提供 5 年历史数据（DuckDB 列式读取，向量化回测）
2. Universe Manager 把标的按特征分组（高/中/低波动 × 行业 × 市值）
3. MatrixBacktest 跑 N 策略 × G 组 × 参数网格
4. 每组按 Sharpe/Calmar 排名，保留 Top-K 策略及其参数、权重
5. 输出 strategy_weights.json，供实盘层读取
```

### 4.2 在线交易层（每个交易日）

```
1. DataSyncService 收盘后增量同步当天新 bar → MarketDataStore（只拉 delta）
2. 盘前/盘中扫描时：
   a. Universe Manager 给出当前标的池 + 每只所属组
   b. Strategy Matrix Runner 按组分配策略（读 strategy_weights.json），
      对每只标的运行对应策略，输出带 strategy_name + confidence 的 Signal
   c. Signal Ranker 聚合所有 Signal，按 (策略权重 × 置信度 × 历史胜率) 排名，取 Top-K
   d. Signal Filter 对 Top-K 信号二次过滤
   e. Risk Manager 计算仓位 + 止损，输出 OrderIntent
   f. Execution Engine 提交订单
   g. Portfolio Tracker 更新持仓
3. Monitor Layer 全程监听，推送告警
```

---

## 5. 技术选型

| 层次 | 技术 | 版本 | 理由 |
|------|------|------|------|
| 语言 | Python 3.12+ | 3.12.13 | pandas-ta 需 3.12+ |
| 回测 | VectorBT | 1.0.0 | 向量化，参数优化原生支持 |
| **数据存储（实盘）** | **SQLite + SQLAlchemy** | ≥2.0 | 已有技术栈，单文件，事务安全 |
| **数据存储（回测）** | **DuckDB** | 最新 | 列式存储，5年×550只向量化回测读取快 10-100× |
| 数据获取（主） | **Alpaca `v2/delayed_sip`** | — | 官方 API、批量请求、全量 SIP、免费（15min 延迟） |
| 数据获取（备） | `yfinance` | 1.4.1 | fallback / 回填补缺 |
| 数据处理 | `pandas` + `numpy` | 2.3.3 / 2.2.6 | 标准 |
| 技术指标 | `pandas-ta` | 0.4.71b0 | 130+ 指标，`indicators.py` 封装 |
| 可视化 | `plotly` + `streamlit` | 6.8.0 | 回测报告 + Dashboard |
| 配置 | YAML + Pydantic | — | 类型安全 |
| 日志 | `loguru` | 0.7.3 | 结构化日志 |
| 券商执行 | `alpaca-py` / `ib_insync` | — | 美股 / 港美股 |
| 调度 | `APScheduler` | ≥3.10 | 定时任务 |

> **Python 环境**：`/Users/rickouyang/miniforge3/envs/py312trade`

---

## 6. 关键设计参数（v2 访谈确认）

| 参数 | 取值 | 理由 |
|------|------|------|
| **实盘扫描 lookback** | 90 天 | 够算最慢指标（slow=60 均线 + 预热） |
| **回测 lookback** | **5 年** | 覆盖完整牛熊周期；更久则市场结构相关性下降 |
| **数据同步方式** | 增量（只拉 delta） | 避免重复拉历史 → 避免限速；盘中读本地库 |
| **数据库** | SQLite（实盘）+ DuckDB（回测） | 数据量仅 ~42MB，无需 MySQL 服务器 |
| **首次回填** | 5 年日线（~550 只） | 一次性，约几分钟 |
| **策略权重更新** | **每月**（Walk-Forward） | 平衡过拟合与适应性，月度有足够样本外数据验证 |
| **参数粒度** | **按组**（波动率/行业/市值），非单只 | 单只优化必过拟合；分组控制自由度 |
| **Top-K 持仓** | 5 | 集中高信念押注，靠 `risk_per_trade=1%` + 止损控风险（非分散） |
| **扫描频次** | 盘前1 + 盘中~13（每30min）+ 盘后2 ≈ 16次/天 | 盘中读本地库，无网络瓶颈 |

> **Top-K=5 的代价**：等权下每仓占 20% 资金，高度集中，单只暴雷砸 20% 净值。这是"少而精"风格的主动选择，未来若想降波动可调至 10-15。

---

## 7. 关键设计原则

1. **回测/实盘一致性**：策略逻辑写在纯函数中，回测和实盘调用同一套函数。
2. **数据单一来源**：所有下游（扫描/回测）只读 MarketDataStore，不直接调外部 API。
3. **策略↔标的数据驱动**：策略与标的的匹配来自回测结果（strategy_weights.json），不手动配置。
4. **参数防过拟合**：按标的分组优化参数，绝不对单只股票单独优化。
5. **失败安全（Fail-Safe）**：任一模块崩溃则停止下单，而非带错运行。
6. **可观测性优先**：所有关键决策点留日志。
7. **持仓真相来源**：以券商账户为唯一 Source of Truth，本地记录仅参考。

---

## 8. 分阶段实施路线

### Phase 1-4（✅ 已完成）
- Phase 1：Data Layer + Strategy Engine + VectorBT 回测
- Phase 2：Signal Filter + Risk Manager + Paper Broker + Portfolio Tracker
- Phase 3：AlpacaBroker + IBKRBroker + 通知 + 调度器 + Monitor + 对账
- Phase 4：AlpacaDataProvider + ScanOrchestrator + Streamlit Dashboard

### Phase 5 — 大规模选股与全自动执行（🔲 本次设计）
- [ ] **Market Data Store**：本地时序库（SQLite + DuckDB）+ DataSyncService 增量同步
- [ ] **Universe Manager**：S&P 500 + Nasdaq 100 成分股 + 特征分组
- [ ] **Strategy Matrix Runner**：多策略 × 多标的批量运行
- [ ] **Signal Ranker**：信号聚合 + 排名 + Top-K
- [ ] **MatrixBacktest**：N策略 × G组 × 参数网格 → strategy_weights.json
- [ ] **Walk-Forward 调度**：每月重优化策略权重
- [ ] 输出：扫描 550 只 → 选 Top-5 → 全自动执行

---

## 参考来源

- [VectorBT 官方文档](https://vectorbt.dev/)
- [DuckDB 文档](https://duckdb.org/docs/)
- [Alpaca Markets Python SDK](https://alpaca.markets/sdks/python/)
- [ib_insync 文档](https://ib-insync.readthedocs.io/)
- *Advances in Financial Machine Learning* — Marcos López de Prado（Ch.7 交叉验证、Ch.11 Sharpe）
- *Algorithmic Trading: Winning Strategies* — Ernest Chan（均值回归 vs 动量）
