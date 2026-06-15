# Phase 2 开发总结

> 日期：2026-06-14  
> Python 环境：`/Users/rickouyang/miniforge3/envs/py312trade`（Python 3.12.13）  
> 测试结果：**202 passed（Phase 1: 108 + Phase 2: 94），0 failed**

---

## 1. Phase 2 已完成

### 1.1 新增目录结构

```
mytrader/mytrader/
├── infra/                              # Module 09 — 基础设施
│   ├── __init__.py
│   ├── config.py                       # AppConfig（Pydantic BaseSettings + YAML + .env）
│   └── event_bus.py                    # 同步 EventBus + Events 常量类
│
├── signal/                             # Module 03 — 信号过滤器
│   ├── __init__.py
│   ├── models.py                       # FilteredSignal + FilterResult 数据结构
│   ├── pipeline.py                     # SignalPipeline：链式过滤，from_config 工厂方法
│   └── filters/
│       ├── __init__.py                 # BaseFilter Protocol 定义
│       ├── volume_filter.py            # 成交量确认（rolling(20).mean().shift(1)）
│       ├── atr_filter.py               # ATR 波动率过滤（ATR/close > 阈值时拒绝）
│       ├── sentiment_filter.py         # 大盘趋势过滤（SPY 200日均线，可选）
│       ├── time_window_filter.py       # 时间窗口过滤（开盘/收盘缓冲期）
│       └── cooldown_filter.py          # 冷却期过滤（同向信号最小间隔 N bars）
│
├── risk/                               # Module 04 — 风险管理器
│   ├── __init__.py
│   ├── models.py                       # OrderIntent + CircuitBreakerState 枚举
│   ├── position_sizer.py               # fixed_amount_size + atr_position_size + fixed_fraction_size
│   ├── stop_loss.py                    # fixed_stop + fixed_take_profit + atr_stop + time_stop_bars
│   ├── circuit_breaker.py              # 三层熔断（日/周/月亏损阈值，状态内存存储）
│   ├── constraints.py                  # 约束检查（单标的上限/总持仓上限/最小订单金额/最大持仓数）
│   └── manager.py                      # RiskManager 门面：整合以上全部组件
│
├── execution/                          # Module 05 — 执行引擎
│   ├── __init__.py
│   ├── models.py                       # OrderResult + OrderStatus 枚举
│   ├── base.py                         # BrokerProtocol（Protocol 接口定义）
│   ├── slippage.py                     # SlippageModel（固定比例滑点 + 手续费计算）
│   └── paper_broker.py                 # PaperBroker：下一 bar 开盘价成交，幂等性 ID
│
└── portfolio/                          # Module 06 — 持仓追踪器
    ├── __init__.py
    ├── models.py                       # Position + Portfolio + TradeRecord 数据结构
    ├── pnl_calculator.py               # FIFO 盈亏计算（apply_buy / apply_sell）
    ├── metrics.py                      # 绩效指标（Sharpe / MaxDD / Calmar / 胜率 / 盈亏比）
    ├── persistence.py                  # SQLAlchemy 2.x Core（trades + portfolio_snapshots 表）
    └── tracker.py                      # PortfolioTracker：消费 OrderResult，更新持仓，快照持久化

mytrader/tests/
├── test_infra.py                       # 12 个测试（AppConfig 加载、env覆盖、EventBus）
├── test_signal_filter.py               # 25 个测试（5个过滤器 + pipeline）
├── test_risk_manager.py                # 22 个测试（仓位计算、止损、熔断、约束）
├── test_execution.py                   # 12 个测试（PaperBroker 成交、幂等性、滑点）
└── test_portfolio.py                   # 23 个测试（FIFO盈亏、持仓更新、指标、持久化）
```

---

## 2. 关键设计决策

| 决策 | 选择 | 原因 |
|------|------|------|
| **Config 加载** | Pydantic BaseSettings + YAML 手动 merge | pydantic-settings 已在 pyproject.toml；YAML 骨架已存在；env 变量优先级最高 |
| **过滤器架构** | Protocol + 链式调用，`from_config` 工厂方法 | 可插拔，回测/实盘完全一致；YAML 控制每个过滤器的启用/关闭 |
| **防前视偏差** | 所有过滤器使用 `.rolling(n).mean().shift(1)` | 与 Phase 1 策略层约定一致，严格消除 look-ahead |
| **仓位计算** | ATR 法为主，固定金额法为后备 | ATR 法使不同波动率标的的每笔风险可比；fixed_amount_size 作 fallback |
| **止盈比例** | `stop_distance / entry_price * 2`（2:1 风险收益比） | RiskManager 自动设置，无需手工配置 |
| **PaperBroker 成交价** | `next_bar_open * (1 ± slippage_pct)` | 与 Phase 1 回测约定一致（open=open_series），防前视偏差 |
| **幂等性** | `uuid4().hex[:16]` 生成 Client Order ID，broker 检查重复提交 | 防止网络重试导致重复成交 |
| **FIFO 盈亏** | `lots: list[(qty, cost_price)]` 队列 | 精确计算每笔卖出的已实现盈亏，支持多次部分卖出 |
| **持久化** | SQLAlchemy 2.x Core（`with engine.connect()`），不用 ORM Session | 轻量，无 Session 管理复杂度；测试用 `sqlite:///:memory:` 隔离 |
| **EventBus** | 同步字典分派，单 handler 异常不阻断其他 handler | Phase 2 单进程场景，简单可靠优先 |

---

## 3. 数据流链路（Phase 2 完成后）

```
YFinanceProvider → DataCleaner → DataValidator
        ↓
  StrategyEngine（dual_ma / bollinger / rsi / macd）
        ↓
  SignalPipeline（volume → atr → sentiment → time_window → cooldown）
        ↓
  RiskManager（position_sizer + stop_loss + circuit_breaker + constraints）
        ↓
  PaperBroker（next_bar_open * (1+slippage)）
        ↓
  PortfolioTracker（FIFO盈亏 + SQLite持久化）
```

> 执行层为 **Paper Trading**，不自动提交真实券商。  
> 所有模块通过 EventBus 解耦，可独立测试。

---

## 4. 测试覆盖（Phase 2 新增 94 个）

| 测试文件 | 测试数 | 主要覆盖点 |
|----------|--------|-----------|
| `test_infra.py` | 12 | AppConfig 默认值/YAML加载/嵌套配置/缺失文件降级；env 变量覆盖；EventBus 多handler/异常隔离/订阅取消 |
| `test_signal_filter.py` | 25 | VolumeFilter（量充足/量不足/无列/数据不足）；ATRFilter（低波/高波/缺列）；SentimentFilter（无基准/熊市BUY/熊市SELL）；TimeWindowFilter（日线/开盘缓冲/缓冲后）；CooldownFilter（首次/冷却中/冷却后/方向独立）；Pipeline（空/from_config/统计） |
| `test_risk_manager.py` | 22 | fixed_amount_size（基本/零止损距离）；atr_position_size（正值）；fixed_fraction_size（基本/零价）；fixed_stop（多/空）；atr_stop；熔断 NORMAL/DAILY/WEEKLY/RESET；约束全4种；OrderIntent 幂等ID |
| `test_execution.py` | 12 | SlippageModel（BUY加价/SELL减价/手续费）；PaperBroker（BUY成交/SELL成交/末行拒绝/幂等/手续费/历史记录/gross_value） |
| `test_portfolio.py` | 23 | apply_buy（单次/多批加权均价）；apply_sell（FIFO盈利/亏损/多批/超数报错/清仓）；PortfolioTracker（初始/现金扣减/建仓/卖出盈亏/拒绝/现金不足/快照/交易计数）；Metrics（Sharpe/MaxDD/Calmar/胜率/盈亏比/summary字段）；Persistence（存取/幂等/快照/symbol过滤） |

**Phase 1 + Phase 2 合计：202 passed，0 failed**

---

## 5. 新增依赖

| 包 | 版本 | 用途 |
|----|------|------|
| `sqlalchemy` | ≥2.0 | SQLite 持久化（Core API，`with engine.connect()`） |
| `pydantic-settings` | ≥2.6.0 | AppConfig 读取 env 文件 / 环境变量覆盖（已在 pyproject.toml） |

```bash
# 安装命令
/Users/rickouyang/miniforge3/envs/py312trade/bin/pip install sqlalchemy pydantic-settings
```

---

## 6. Phase 3 规划（TODO）

| 模块 | 说明 | 优先级 |
|------|------|--------|
| `infra/container.py` | 依赖注入容器，一键切换 Paper/Live 模式 | P0 |
| `infra/scheduler.py` | APScheduler 定时任务：盘前扫描/盘中更新/盘后对账 | P0 |
| `execution/alpaca_broker.py` | Alpaca API 真实执行（美股） | P1 |
| `execution/ibkr_broker.py` | ib_insync 接入 IBKR（港美股） | P1 |
| `execution/notification.py` | 订单 JSON 生成 + Telegram/企业微信通知 → 人工确认 | P1 |
| `portfolio/reconciliation.py` | 对账服务：本地记录 vs 券商持仓核对 | P2 |
| `infra/monitor.py` | 健康检查、告警规则、异常熔断通知 | P2 |

Phase 3 完成后，系统将升级为：

```
Paper Trading（Phase 2）→ 人工确认半自动下单（Phase 3）→ 全自动执行（未来）
```
