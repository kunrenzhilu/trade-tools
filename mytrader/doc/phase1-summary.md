# Phase 1 开发总结 & Phase 2 TODO

> 日期：2026-06-13  
> Python 环境：`/Users/rickouyang/miniforge3/envs/py312trade`（Python 3.12.13）

---

## 1. Phase 1 已完成

### 1.1 项目骨架

```
mytrader/
├── pyproject.toml                     # 依赖管理（setuptools editable install）
├── config/default.yaml                # 默认配置（策略 / 回测 / 风控参数）
├── .env.example                       # 环境变量模板（API Key 等敏感信息）
├── .gitignore
├── examples/phase1_backtest.py        # 端到端演示脚本
├── tests/
│   ├── test_data_layer.py             # 12 个测试
│   └── test_strategy.py               # 17 个测试（含 4 个前视偏差专项）
└── mytrader/
    ├── __init__.py
    ├── data/                          # Module 01 — Data Layer
    │   ├── base.py                    #   DataProvider Protocol + OHLCVFrame 类型
    │   ├── cache.py                   #   Parquet 本地缓存（TTL 策略，单文件按日期范围）
    │   ├── cleaner.py                 #   数据清洗（列名小写/UTC 时区/去重/NaN前向填充/异常标记）
    │   ├── validator.py               #   质量校验（DataQualityReport：价格逻辑/负价/最少行数）
    │   └── providers/
    │       └── yfinance_provider.py   #   YFinance 数据源（auto_adjust 后复权 + 重试 + 缓存集成）
    ├── strategy/                      # Module 02 — Strategy Engine
    │   ├── base.py                    #   Signal / SignalDirection 数据结构
    │   ├── registry.py                #   @register_strategy 装饰器 + STRATEGY_REGISTRY
    │   ├── indicators.py              #   技术指标（底层：pandas-ta 0.4.71b0）
    │   ├── ensemble.py                #   加权投票聚合（自动归一化 + 阈值控制）
    │   └── strategies/
    │       ├── dual_ma.py             #   双均线交叉
    │       ├── rsi_mean_revert.py     #   RSI 超买超卖
    │       ├── bollinger_band.py      #   布林带均值回归
    │       └── macd_cross.py          #   MACD 信号线交叉
    └── backtest/                      # Module 07 — Backtest
        ├── runner.py                  #   BacktestRunner: 单次回测 + run_optimize 网格搜索
        └── report.py                  #   BacktestReport: 生成 stats.csv / trades.csv / HTML 图表
```

### 1.2 关键设计决策

| 决策 | 说明 |
|------|------|
| **策略函数签名** | `(close: pd.Series, **params) -> pd.Series`，纯函数，不依赖外部状态 |
| **前视偏差防护** | 所有策略强制 `shift(1)`，4 个专项测试验证，破坏性测试（篡改最后 bar 不应影响信号） |
| **回测/实盘一致性** | 策略函数同时被 `BacktestRunner`（全量历史）和未来实盘引擎（滚动增量）调用 |
| **指标库** | pandas-ta 0.4.71b0（需 Python 3.12+），`indicators.py` 封装其接口 |
| **VectorBT 1.0.0 适配** | `size_type="Percent"`（非旧版 `ValuePercent`），`pf.stats()` 无 `Annualized Return` 字段 |
| **数据缓存** | Parquet 格式，目录 `~/.mytrader/cache/yfinance/{symbol}/{timeframe}/`，日线 18:00 过期，历史数据永不过期 |
| **执行价格** | 回测中使用 `open=open_series` 参数，信号在下一 bar 开盘价执行 |
| **Signal 数据结构** | 1=BUY，-1=SELL，0=HOLD，统一 int 类型，含 timestamp、confidence、indicators 快照 |

### 1.3 测试覆盖

**共 29 个测试，全部通过。**

| 测试文件 | 测试数 | 覆盖内容 |
|----------|--------|---------|
| `test_data_layer.py` | 12 | 清洗：列名/时区/排序/去重/NaN填充/异常标记/低流动性/空输入；校验：合法/空/行数不足/负价 |
| `test_strategy.py` | 17 | 指标：SMA长度/首有效值/RSI范围/布林带上下轨/ MACD维度/ATR非负；注册表：完整性/可调用；**前视偏差：4策略逐策略破坏性测试**；信号值域；Ensemble：等权/冲突/归一化 |

### 1.4 回测验证结果（AAPL 2022-01-01 ~ 2025-01-01）

| 策略 | 总回报 | Sharpe | MaxDD | Calmar | 交易次数 |
|------|--------|--------|-------|--------|---------|
| 布林带均值回归 | +44.5% | 0.96 | 20.5% | 0.95 | 9 |
| MACD 交叉 | +36.9% | 0.87 | 20.0% | 0.83 | 29 |
| RSI 均值回归 | +19.3% | 0.47 | 26.0% | 0.34 | 4 |
| 双均线 | +15.9% | 0.46 | 20.7% | 0.36 | 14 |
| **买入持有基准** | +39.8% | — | — | — | — |

双均线参数优化（网格搜索）：最优组合 `fast=5, slow=60`，Sharpe 1.06，Calmar 1.17。

---

## 2. Phase 2 — 半自动执行（TODO）

目标：**人工辅助执行，积累真实交易数据**，不涉及自动下单。

### 2.1 Signal Filter（信号过滤器）— 设计文档：`design/03-signal-filter.md`

**新增目录**：`mytrader/signal/`

| 任务 | 说明 | 优先级 |
|------|------|--------|
| `signal/pipeline.py` | 过滤器流水线（链式调用，通过 YAML 配置启用/关闭） | P0 |
| `signal/filters/volume_filter.py` | 成交量确认：成交量 > N日均量 * 阈值，剔除缩量信号 | P1 |
| `signal/filters/time_window_filter.py` | 时间窗口过滤：跳过开盘/收盘前 N 分钟、财报日、议息日 | P1 |
| `signal/filters/cooldown_filter.py` | 冷却期过滤：同向信号之间至少间隔 N 根 K 线 | P1 |
| `signal/filters/atr_filter.py` | 波动率过滤：ATR/close > 阈值时，暂停交易 | P2 |
| `signal/models.py` | FilterResult 数据结构（原始/通过/各过滤原因统计） | P0 |

**注意点**：过滤条件可能过拟合 → 回测中逐步增加，观察每个过滤对 Sharpe 的独立贡献。

### 2.2 Risk Manager（风险管理器）— 设计文档：`design/04-risk-manager.md`

**新增目录**：`mytrader/risk/`

| 任务 | 说明 | 优先级 |
|------|------|--------|
| `risk/models.py` | OrderIntent 数据结构（symbol/direction/quantity/止损价/止盈价/risk_amount） | P0 |
| `risk/position_sizer.py` | 仓位计算：固定金额法 + ATR 波动率仓位法（推荐） | P0 |
| `risk/stop_loss.py` | 固定止损止盈（入场价 * (1±pct)）+ 时间止损（持仓超 N 天平仓） | P1 |
| `risk/circuit_breaker.py` | 三层熔断：日亏 2% 暂停 / 周亏 5% 减仓 / 月亏 10% 全停 | P1 |
| `risk/constraints.py` | 仓位约束：单标的不超 20%、总持仓不超 80%、最多 5 个持仓 | P1 |

**注意点**：ATR 止损距离 × 每笔风险金额 = 仓位大小，确保不同波动率的股票风险可比。

### 2.3 Execution Engine（半自动模式）— 设计文档：`design/05-execution-engine.md`

**新增目录**：`mytrader/execution/`

| 任务 | 说明 | 优先级 |
|------|------|--------|
| `execution/models.py` | OrderResult 数据结构（order_id/fill_price/commission/status） | P0 |
| `execution/paper_broker.py` | Paper Trading：在下一 bar 开盘价模拟成交，扣除模拟费用和滑点 | P0 |
| `execution/slippage.py` | 固定比例滑点模型（base_slippage_pct + commission_pct） | P1 |
| `execution/order_manager.py` | 订单状态管理：Idempotent Client Order ID + 未成交超时取消 | P2 |
| **通知机制** | 生成订单 JSON → Telegram/企业微信发送通知 → 人工点击确认后下单 | P0 |

**注意点**：半自动模式下，订单**不自动提交**到券商，只生成 JSON + 通知，人工决策是否执行。

### 2.4 Portfolio Tracker（持仓追踪）— 设计文档：`design/06-portfolio-tracker.md`

**新增目录**：`mytrader/portfolio/` | **新增依赖**：SQLite + SQLAlchemy

| 任务 | 说明 | 优先级 |
|------|------|--------|
| `portfolio/models.py` | Position / Portfolio / TradeRecord 数据结构 | P0 |
| `portfolio/tracker.py` | 持仓状态管理：消费 OrderResult → 更新 Position → 更新 Portfolio | P0 |
| `portfolio/pnl_calculator.py` | 盈亏计算：未实现（mark-to-market）、已实现（FIFO 成本法） | P1 |
| `portfolio/persistence.py` | SQLite 持久化：trades 表 + portfolio_snapshots 表（SQLAlchemy） | P1 |
| `portfolio/reconciliation.py` | 对账服务：定期核对本地记录与券商（Paper Broker）数据 | P2 |

**注意点**：Phase 2 中 Portfolio Tracker 的"真相来源"就是 Paper Broker，因为还没接真实券商。

### 2.5 Infrastructure（基础设施）— 设计文档：`design/09-infrastructure.md`

**新增目录**：`mytrader/infra/` | **新增依赖**：APScheduler

| 任务 | 说明 | 优先级 |
|------|------|--------|
| `infra/config.py` | AppConfig（Pydantic），读取 `config/default.yaml` + `.env` 环境变量覆盖 | P0 |
| `infra/event_bus.py` | EventBus（发布/订阅），解耦模块间通信 | P1 |
| `infra/container.py` | 依赖注入：组装组件，支持 Paper/Live 模式切换 | P1 |
| `infra/scheduler.py` | APScheduler 定时任务：盘前信号扫描 / 盘中更新 / 收盘前检查 / 盘后对账 | P2 |

---

## 3. Phase 2 关键技术依赖

| 包 | 用途 | Phase 1 已装 |
|----|------|------------|
| `pandas-ta` 0.4.71b0 | 技术指标 | ✅ |
| `vectorbt` 1.0.0 | 回测 | ✅ |
| `yfinance` 1.4.1 | 数据源 | ✅ |
| `APScheduler` | 定时任务（Phase 2 新增） | ❌ |
| `SQLAlchemy` | ORM 持久化（Phase 2 新增） | ❌ |
| `requests` / `httpx` | HTTP 通知（Phase 2 新增） | ❌ |

---

## 4. Phase 2 启动建议

**推荐顺序**（按依赖关系排列）：

```
1. infra/config.py        — 所有模块都依赖配置
2. signal/models.py       — 定义 FilterResult（纯数据类，无外部依赖）
3. signal/pipeline.py     — 流水线框架 + 一个最简单的过滤（如时间窗口过滤）
4. risk/models.py         — 定义 OrderIntent（纯数据类）
5. risk/position_sizer.py — 固定金额仓位法（最简单，可立刻用）
6. execution/models.py    — 定义 OrderResult（纯数据类）
7. execution/paper_broker.py — 模拟执行（下一 bar 开盘价成交 + 费用）
8. portfolio/models.py    — 定义 Position/Portfolio/TradeRecord
9. portfolio/tracker.py   — 消费 OrderResult，更新持仓
10. infra/event_bus.py    — 串联所有模块（发布/订阅）
```

Phase 2 完成后，系统的数据流就完整了：

```
Data Layer → Strategy Engine → Signal Filter → Risk Manager → Execution Engine → Portfolio Tracker
```

但执行层仍为 **Paper Trading + 人工确认**，不涉及真实资金。
