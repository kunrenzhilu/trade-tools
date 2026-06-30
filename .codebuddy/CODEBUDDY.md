# Trade-Tools 项目核心参考文档

> 最后更新：2026-06-30 (新增 Orchestrator 监控循环)  
> 本文是项目规范 + 关键索引，供 AI 助手快速建立项目上下文。  
> **各阶段开发详情见** → [`.codebuddy/notes/dev_records.md`](.codebuddy/notes/dev_records.md)

---

## ⚖️ AI Constitution（最高行为准则）

> **AI 在此项目中的所有决策，必须以 `alignment/ai_constitution.md` 为最高准则。**
>
> 该文件通过 9 层对齐访谈（L0 Vision → L9 Evolution）建立，覆盖：
> - 目标体系（年化 20-30%，DD≤20%，Sortino 优先）
> - 交易哲学（Hybrid 混合系统，AI 持续进化策略）
> - 架构边界（Trading System 纯规则 / Agent System 研究层）
> - 决策权重矩阵（15 项优先级排序）
> - 运行时故障处理策略
> - 代码规范与测试纪律
> - 策略上线验证流水线
> - AI 自主权矩阵 + 禁止行为清单
>
> **🔗 全文** → [`alignment/ai_constitution.md`](../alignment/ai_constitution.md)
>
> **AI 遇到模糊决策时必须记录决策日志** → `alignment/decision_log.md`  
> **每次策略迭代必须留痕** → `alignment/iteration_trajectory.md`

---

## 1. 项目概述

**trade-tools** 是一个量化交易工具集，分为两个独立子项目：

| 子项目 | 状态 | 说明 |
|--------|------|------|
| `mytrader/` | **主力开发中** | 全自动量化交易系统，面向美股（S&P 500 + Nasdaq 100） |
| `trader-skills/` + `backtest/` | **作为参考** | OpenClaw Skills 体系，基于 Backtrader，不新增功能 |

---

## 2. 开发环境（mytrader）

### Python 环境（必须使用，不得新建 venv）

```
/Users/rickouyang/miniforge3/envs/py312trade/bin/python
```

**执行命令统一用绝对路径：**

```bash
/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest
/Users/rickouyang/miniforge3/envs/py312trade/bin/pip install <pkg>
```

### 已安装包版本（py312trade）

| 包 | 版本 | 说明 |
|----|------|------|
| Python | 3.12.13 | 需 3.12+（pandas-ta 兼容性） |
| pandas-ta | 0.4.71b0 | 技术指标，`indicators.py` 底层实现 |
| vectorbt | 1.0.0 | 回测框架，API 与旧版有破坏性变更 |
| yfinance | 1.4.1 | 数据源（fallback / 回填补缺） |
| pandas | 2.3.3 | |
| numpy | 2.2.6 | |
| pyarrow | 24.0.0 | Parquet 缓存 |
| plotly | 6.8.0 | HTML 报告可视化 |
| loguru | 0.7.3 | 结构化日志 |
| sqlalchemy | ≥2.0 | SQLite 持久化 |
| pydantic-settings | ≥2.6.0 | AppConfig env 覆盖 |
| httpx | ≥0.27.0 | Telegram/企业微信通知推送 |
| apscheduler | ≥3.10.0 | 定时任务调度 |
| duckdb | 1.5.4 | 回测批量列式读取（Phase 5 新增） |
| lxml | ≥5.0.0 | Wikipedia 成分股抓取（Phase 5 新增） |

### 待安装（需 API 账户）

| 包 | 用途 | 状态 |
|----|------|------|
| `alpaca-py` | Alpaca 美股真实 API（auto 模式） | 待安装 |
| `ib_insync` | IBKR 港美股 API | 待安装 |

---

## 3. 项目根目录结构

```
/Users/rickouyang/Github/trade-tools/mytrader/
```

```
mytrader/
├── pyproject.toml
├── main.py                     # 启动入口（--mode/--dry-run/--scan-now/--reoptimize/--backfill）
├── config/
│   ├── default.yaml            # 默认配置（含 v2 新增配置节）
│   └── strategy_weights.json   # MatrixBacktest 产出（--reoptimize 生成）
├── designs/
│   ├── design_v1/              # 历史设计（9 份，v1 参考）
│   └── design_v2/              # 当前设计（15 份，v2.1 版本）
│       └── claude_review.md    # 设计审查报告（审查 glm_review.md 所有问题）
├── doc/                        # 开发总结（phase1~5-summary.md）
├── examples/
│   ├── phase1_backtest.py
│   └── phase5_e2e.py           # [Phase 5] 端到端干跑脚本
├── reports/                    # 回测输出（.gitignore）
├── tests/                      # 467 个测试
└── mytrader/
    ├── data/                   # Module 01 — Data Layer ✅
    │   ├── providers/
    │   │   ├── yfinance_provider.py
    │   │   └── alpaca_provider.py      # [Phase 4]
    │   └── store/                      # [Phase 5] 本地时序库
    │       ├── market_data_store.py    # SQLite + DuckDB
    │       └── sync_service.py         # 增量同步
    ├── universe/                       # [Phase 5] 标的池管理
    │   ├── manager.py                  # UniverseManager
    │   ├── constituents.py             # 成分股抓取
    │   └── grouping.py                 # 波动率分层
    ├── strategy/               # Module 02 — Strategy Engine ✅
    │   ├── strategies/         # dual_ma / rsi / macd / bollinger
    │   ├── ensemble.py
    │   └── matrix_runner.py    # [Phase 5] StrategyMatrixRunner
    ├── backtest/               # Module 07 — Backtest ✅
    │   ├── runner.py           # BacktestRunner（含 daily_returns）
    │   └── matrix_backtest.py  # [Phase 5] MatrixBacktest
    ├── signal/                 # Module 03 — Signal Filter ✅
    │   ├── filters/
    │   └── ranker.py           # [Phase 5] SignalRanker
    ├── risk/                   # Module 04 — Risk Manager ✅
    │   ├── position_sizer.py
    │   ├── constraints.py
    │   └── candidate_selector.py  # [Phase 5] 约束递补选股
    ├── execution/              # Module 05 — Execution Engine ✅
    │   ├── alpaca_broker.py
    │   ├── ibkr_broker.py
    │   └── notification.py
    ├── portfolio/              # Module 06 — Portfolio Tracker ✅
    │   └── reconciliation.py
    ├── infra/                  # Module 09 — Infrastructure ✅
    │   ├── config.py           # AppConfig（含 v2 新增配置节）
    │   ├── container.py
    │   └── scheduler.py        # 含月度 Walk-Forward job
    ├── monitor/                # Module 08 — Monitor Layer ✅
    │   └── dashboard/app.py    # [Phase 4] Streamlit Dashboard
    └── scan_orchestrator.py    # [Phase 4] 扫描编排器
```

---

## 4. 系统架构（v2 双层）

```
┌─────────────── 离线回测层（Monthly Walk-Forward）──────────────────┐
│  MarketDataStore → MatrixBacktest（N策略×G组×参数网格）             │
│                           ↓ strategy_weights.json（每月更新）       │
└────────────────────────────┬───────────────────────────────────────┘
                             │ 热加载
                             ▼
┌─────────────── 在线交易层（每日 16 次扫描）────────────────────────┐
│  DataSyncService → MarketDataStore → UniverseManager               │
│                                          ↓ {group_id: [symbols]}   │
│                              StrategyMatrixRunner（信号有效期3bar） │
│                                          ↓ M×N 条 Signal           │
│                              SignalRanker（聚合 + Top-2K 候选）     │
│                                          ↓                         │
│                              CandidateSelector（5级约束递补）       │
│                                          ↓ Top-5 OrderIntent        │
│          Signal Filter → Risk Manager → Execution → Portfolio       │
│                                                                      │
│  ──── 横切：Config / Logger / EventBus / Container / Scheduler ────│
└────────────────────────────────────────────────────────────────────┘
```

---

## 5. 开发阶段

| 阶段 | 状态 | 测试数 | 说明 |
|------|------|--------|------|
| **Phase 1** | ✅ 完成 | 108 | Data Layer + Strategy Engine + VectorBT 回测 |
| **Phase 2** | ✅ 完成 | 94 | Signal Filter + Risk Manager + Paper Broker + Portfolio Tracker |
| **Phase 3** | ✅ 完成 | 142 | AlpacaBroker + IBKRBroker + 通知 + 调度器 + Monitor + 对账 |
| **Phase 4** | ✅ 完成 | 38 | AlpacaDataProvider + ScanOrchestrator + Streamlit Dashboard |
| **Phase 5** | ✅ 完成 | 85 | MarketDataStore + UniverseManager + 矩阵扫描 + 矩阵回测 + Walk-Forward |
| **Phase 6** | 🔲 待开发 | — | AlpacaBroker auto 端到端验证 + 对账真实集成 + 港股支持 |

**当前总测试数：467 passed，0 failed**

> 各阶段详细实现见 **[dev_records.md](.codebuddy/notes/dev_records.md)**

---

## 6. 代码规范

- Python 3.12，类型注解全覆盖
- 策略函数必须是**纯函数**（无副作用），必须包含 `shift(1)` 防前视偏差
- 所有时间统一 UTC，仅在输出层转换本地时区
- 缓存目录：`~/.mytrader/cache/`（旧版 Parquet 缓存）
- 本地时序库：`~/.mytrader/market_data.db`（Phase 5 新增，SQLite）
- 报告输出：`mytrader/reports/`

### VectorBT 1.0.0 关键用法

```python
# size_type 枚举值
size_type="Percent"          # ✅ 正确
size_type="valuepercent"     # ❌ 旧版，不可用

# 必须传 open= 参数（信号在下一 bar 开盘价执行）
pf = vbt.Portfolio.from_signals(close=close, open=open_, ...)

# stats 字段名
pf.stats()["Sharpe Ratio"]         # ✅
pf.stats()["Annualized Return [%]"] # ❌ 1.0.0 已移除
```

### .env 变量格式（Pydantic nested 风格）

```bash
ALPACA__API_KEY=xxx
ALPACA__SECRET_KEY=xxx
NOTIFICATION__TELEGRAM_ENABLED=true
EXECUTION__MODE=semi_auto
```

---

## 7. 启动命令

```bash
cd /Users/rickouyang/Github/trade-tools/mytrader

# 首次初始化（按顺序）
python main.py --backfill                    # 回填 5 年历史数据
python main.py --reoptimize                  # 产出 strategy_weights.json

# 日常调试
python main.py --mode paper --dry-run        # 干跑（仅检查配置）
python main.py --scan-now morning            # 立即执行一次盘前扫描
python examples/phase5_e2e.py               # 端到端干跑验证

# 生产运行
python main.py --mode paper                  # 全自动调度（paper 模式）
python main.py --mode semi_auto              # 半自动（推送通知，人工确认）
```

---

## 8. 设计文档索引

### AI 行为准则
| 文件 | 内容 |
|------|------|
| [`alignment/ai_constitution.md`](../alignment/ai_constitution.md) | **AI Constitution** — 9 层对齐访谈产物，Agent System 最高行为准则 |
| [`alignment/orchestrator_design.md`](../alignment/orchestrator_design.md) | **Orchestrator 设计** — GLM 监控 CodeBuddy 的循环架构方案 |
| [`alignment/orchestrator.py`](../alignment/orchestrator.py) | **Orchestrator 实现** — ACP 客户端，驱动 CodeBuddy 迭代开发 |

### 系统设计文档
路径：`mytrader/designs/design_v2/`（当前版本 v2.1）

| 文件 | 内容 |
|------|------|
| `00-overview.md` | 总架构、技术选型、双层架构 |
| `01-data-layer.md` | 缓存路径格式、TTL 策略 |
| `02-strategy-engine.md` | 策略纯函数设计、信号语义 |
| `03-signal-filter.md` | 信号过滤器设计 |
| `04-risk-manager.md` | 仓位计算、止损止盈、三层熔断、隔夜风险 |
| `05-execution-engine.md` | 半自动执行、券商接口 |
| `06-portfolio-tracker.md` | 持仓追踪、盈亏计算 |
| `07-backtest-module.md` | VectorBT 1.0.0 用法、矩阵回测（Walk-Forward） |
| `08-monitor-layer.md` | 告警、日志、健康检查 |
| `09-infrastructure.md` | Config / EventBus / Logger / Scheduler（含 v2 配置节） |
| `10-market-data-store.md` | 本地时序库（SQLite + DuckDB）+ DataSyncService |
| `11-universe-manager.md` | S&P 500 + Nasdaq 100 成分股 + 波动率分层 |
| `12-strategy-matrix.md` | StrategyMatrixRunner（信号有效期、ensemble 语义） |
| `13-signal-ranker.md` | SignalRanker（Top-2K 候选、SELL 优先） |
| `claude_review.md` | 设计审查报告（18 个问题逐条核实 + 修改建议） |
| `CHANGELOG.md` | 版本变更记录（v2.0 → v2.1） |

> **开发前必须先阅读对应模块的设计文档。**

---

## 9. 旧版子项目（维护模式，不新增功能）

```
trade-tools/
├── trader-skills/
│   ├── hk-quant-advisor/   # HK 港股 AI 交易决策（prompt-based）
│   ├── westock-data/       # 腾讯 WeStock API 数据查询（Node.js）
│   ├── westock-tool/       # 选股/筛股工具（Node.js，A 股 only）
│   └── westock-partner/    # 6 专家圆桌投资分析
└── backtest/
    ├── stock-strategy-backtester/  # SMA/RSI/突破策略，CSV 数据输入
    ├── quant-trading-backtrader/   # Backtrader 封装
    └── pair-trade-screener/        # ADF 协整 + z-score 配对交易
```

---

## 10. Skills

| Skill | 位置 | 说明 |
|------|------|------|
| `meta-agent` | `.codebuddy/skills/meta-agent/` | **Meta Agent（策略层）** — 站在用户角度监督 CodeBuddy 迭代，负责目标评估、任务定义、结果判断、下一步决策。判断标准是"是否离盈利目标更近"，不只是"代码是否正确" |
| `cb-acp-dev` | `.codebuddy/skills/cb-acp-dev/` | **CodeBuddy ACP Orchestrator（执行层）** — 通过 ACP 协议驱动 CodeBuddy 实例开发 mytrader，含 Constitution 合规检查、Agent Teams 支持、迭代轨迹记录 |

### Skill 层级

```
meta-agent（策略层：决定做什么、判断结果好不好）
  ↓ 委托执行
cb-acp-dev（执行层：ACP 协议、监控、合规检查）
  ↓ 驱动
CodeBuddy（开发者：写代码、测试、文档）
```

- 用户说"启动迭代"、"下一步做什么"、"复盘结果"时 → 先加载 `meta-agent`
- 需要实际运行 ACP 调用时 → meta-agent 引用 `cb-acp-dev`

### 核心脚本

```bash
# 运行一次开发迭代
/Users/rickouyang/miniforge3/envs/py312trade/bin/python alignment/orchestrator.py --task "任务描述"

# 带并行 Agent Teams 调研
/Users/rickouyang/miniforge3/envs/py312trade/bin/python alignment/orchestrator.py --task "任务" --team-research
```

---

## 11. 参考链接

- [VectorBT 文档](https://vectorbt.dev/)
- [pandas-ta](https://github.com/twopirllc/pandas-ta)
- [Alpaca Python SDK](https://alpaca.markets/sdks/python/)
- [ib_insync](https://ib-insync.readthedocs.io/)
- [DuckDB SQLite Extension](https://duckdb.org/docs/extensions/sqlite)
- *Advances in Financial Machine Learning* — Marcos López de Prado
- [ACP 协议规范](https://github.com/agentclientprotocol/agent-client-protocol)
- [CodeBuddy CLI 文档](https://www.codebuddy.ai/docs/zh/cli/headless)
