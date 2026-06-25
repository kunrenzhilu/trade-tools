# Module 09 — Infrastructure（基础设施）

> 上级文档：[00-overview.md](./00-overview.md)  
> 本文档覆盖：Config Manager / EventBus / Logger / Scheduler

---

## 1. 职责

基础设施模块是贯穿所有业务模块的**横切关注点（Cross-Cutting Concerns）**：

| 组件 | 职责 |
|------|------|
| **Config Manager** | 统一管理配置，支持环境变量覆盖，类型安全 |
| **EventBus** | 模块间解耦通信，发布/订阅事件 |
| **Logger** | 结构化日志（见 Module 08） |
| **Scheduler** | 定时任务管理（行情拉取、定时下单、对账） |
| **DI Container** | 依赖注入，方便测试时替换实现 |

---

## 2. Config Manager

### 2.1 配置文件结构

```yaml
# config/default.yaml —— 默认配置（提交到 Git，不含敏感信息）
system:
  env: "paper"             # paper | live
  timezone: "Asia/Shanghai"
  log_level: "INFO"

data:
  provider: "yfinance"
  cache_dir: "~/.mytrader/cache"
  cache_ttl_minutes: 30

strategy:
  name: "dual_ma"
  params:
    fast: 10
    slow: 30

risk:
  risk_per_trade: 0.01          # 每次交易承担账户的 1% 风险
  max_position_pct: 0.20
  max_total_exposure_pct: 0.80
  circuit_breaker:
    daily_loss_limit: 0.02
    weekly_loss_limit: 0.05

execution:
  mode: "paper"                  # paper | semi-auto | auto
  broker: "alpaca"
  limit_order_timeout_min: 5
  slippage_pct: 0.001
  commission_pct: 0.001

monitor:
  telegram:
    enabled: true
    alert_levels: ["WARN", "ERROR", "CRITICAL"]
```

```bash
# .env —— 敏感信息（不提交到 Git）
ALPACA_API_KEY=xxxxx
ALPACA_SECRET_KEY=xxxxx
IBKR_HOST=127.0.0.1
IBKR_PORT=7497
TELEGRAM_BOT_TOKEN=xxxxx
TELEGRAM_CHAT_ID=xxxxx
```

### 2.2 Config 类设计（Pydantic）

```python
from pydantic import BaseSettings, Field
from typing import Literal

class RiskConfig(BaseSettings):
    risk_per_trade: float = Field(0.01, ge=0.001, le=0.05)
    max_position_pct: float = Field(0.20, ge=0.05, le=0.50)
    max_total_exposure_pct: float = Field(0.80, ge=0.20, le=1.0)

class AppConfig(BaseSettings):
    env: Literal["paper", "live"] = "paper"
    risk: RiskConfig = RiskConfig()
    # ...

    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"  # 支持 RISK__RISK_PER_TRADE=0.02 格式的环境变量覆盖

# 单例，全局访问
config = AppConfig()
```

### 2.3 环境变量覆盖优先级

```
代码中的默认值 < config/default.yaml < config/{env}.yaml < 环境变量(.env)
```

---

## 3. EventBus（事件总线）

### 3.1 为什么需要 EventBus

没有 EventBus 时（紧耦合）：
```python
# Strategy 直接调用 RiskManager，Risk 直接调用 Broker
# 模块间形成强依赖，难以独立测试
class StrategyEngine:
    def __init__(self):
        self.risk = RiskManager()  # 强依赖
        self.broker = Broker()     # 强依赖
```

有 EventBus 时（松耦合）：
```python
# 每个模块只与 EventBus 交互
class StrategyEngine:
    def __init__(self, bus: EventBus):
        self.bus = bus
        self.bus.subscribe("bar_received", self.on_new_bar)

    def on_new_bar(self, bar: Bar):
        signal = self._compute_signal(bar)
        self.bus.publish("signal_generated", signal)

class RiskManager:
    def __init__(self, bus: EventBus):
        self.bus = bus
        self.bus.subscribe("signal_generated", self.on_signal)

    def on_signal(self, signal: Signal):
        intent = self._calculate_intent(signal)
        self.bus.publish("order_intent_created", intent)
```

### 3.2 EventBus 实现

```python
from typing import Callable, Any
from collections import defaultdict

class EventBus:
    def __init__(self):
        self._handlers: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: Callable):
        self._handlers[event_type].append(handler)

    def publish(self, event_type: str, payload: Any):
        for handler in self._handlers.get(event_type, []):
            try:
                handler(payload)
            except Exception as e:
                logger.exception(f"EventBus handler error: {event_type} -> {handler.__name__}: {e}")
                # 单个 handler 的异常不应阻止其他 handler

# 全局事件类型常量
class Events:
    BAR_RECEIVED          = "bar_received"
    SIGNAL_GENERATED      = "signal_generated"
    SIGNAL_FILTERED       = "signal_filtered"
    ORDER_INTENT_CREATED  = "order_intent_created"
    ORDER_SUBMITTED       = "order_submitted"
    ORDER_FILLED          = "order_filled"
    POSITION_UPDATED      = "position_updated"
    CIRCUIT_BREAKER_TRIGGERED = "circuit_breaker_triggered"
    ALERT                 = "alert"
```

### 3.3 同步 vs 异步 EventBus

- **同步（当前推荐）**：handler 在 `publish()` 调用栈内同步执行，简单可预期
- **异步（未来扩展）**：handler 放入队列后台执行，适合高频场景
  - 注意：异步 EventBus 需要处理背压（back pressure）和错误恢复

---

## 4. Scheduler（任务调度器）

使用 `APScheduler` 管理定时任务：

```python
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

class TradingScheduler:
    def __init__(self, config: AppConfig):
        self.scheduler = BlockingScheduler(timezone=config.timezone)
        self._setup_jobs()

    def _setup_jobs(self):
        # 美股市场（ET 时区）
        # 09:35 拉取数据 + 生成信号（跳过开盘前 5 分钟噪音）
        self.scheduler.add_job(
            self.run_morning_scan,
            CronTrigger(day_of_week="mon-fri", hour=9, minute=35, timezone="America/New_York")
        )

        # 盘中每 30 分钟更新信号
        self.scheduler.add_job(
            self.run_intraday_scan,
            CronTrigger(day_of_week="mon-fri", hour="10-15", minute="*/30", timezone="America/New_York")
        )

        # 15:45 收盘前检查，决定是否平仓
        self.scheduler.add_job(
            self.run_end_of_day_check,
            CronTrigger(day_of_week="mon-fri", hour=15, minute=45, timezone="America/New_York")
        )

        # 每日 16:30 盘后对账
        self.scheduler.add_job(
            self.run_reconciliation,
            CronTrigger(day_of_week="mon-fri", hour=16, minute=30, timezone="America/New_York")
        )

    def start(self):
        logger.info("Scheduler started")
        self.scheduler.start()
```

### 4.1 任务执行保护

```python
def run_morning_scan(self):
    """每个定时任务都需要保护"""
    try:
        if self.circuit_breaker.is_triggered():
            logger.warning("Circuit breaker active, skipping morning scan")
            return
        # 正常执行
        self.strategy_engine.run(...)
    except Exception as e:
        logger.exception(f"Morning scan failed: {e}")
        self.alerter.send(f"Morning scan error: {e}", level="ERROR")
        # 不 re-raise，让 Scheduler 继续运行
```

---

## 5. 依赖注入（DI）

简单的构造器注入，便于测试时替换：

```python
# 生产环境启动
def build_app(config: AppConfig) -> TradingApp:
    bus = EventBus()
    data_provider = YFinanceProvider(config.data)
    strategy_engine = StrategyEngine(bus, data_provider, config.strategy)
    risk_manager = RiskManager(bus, config.risk)
    broker = AlpacaBroker(config.execution) if config.env == "live" else PaperBroker(config.execution)
    portfolio_tracker = PortfolioTracker(bus, broker)
    return TradingApp(bus, strategy_engine, risk_manager, broker, portfolio_tracker)

# 测试环境
def build_test_app() -> TradingApp:
    bus = EventBus()
    data_provider = MockDataProvider()   # 替换为 Mock
    broker = PaperBroker(...)            # 使用 Paper Broker
    ...
```

---

## 6. 注意点

### 6.1 配置热更新
- 不建议实现配置热更新（运行中修改参数），容易引入不一致状态
- 修改配置后重启进程，以确保状态一致

### 6.2 EventBus 中的循环依赖
- 如果 A 发布事件 → B 处理后发布事件 → A 再次响应，可能造成无限循环
- 设计时明确事件流方向（单向流动）

### 6.3 Scheduler 时区问题
- 明确指定每个 Job 的时区，不要依赖系统时区（可能在服务器上不同）
- 港股（HKT）和美股（ET）要分别配置

### 6.4 进程异常重启
- 使用 `supervisor` 或 `systemd` 管理进程，崩溃后自动重启
- 重启后应重新从券商同步持仓状态，而不是依赖内存中的旧状态

---

## 7. 风险点

| 风险 | 级别 | 缓解措施 |
|------|------|---------|
| 敏感配置提交到 Git | 极高 | `.env` 加入 `.gitignore`，使用 pre-commit hook 检查 |
| EventBus handler 异常阻塞主流程 | 高 | 每个 handler 独立 try-except |
| 定时任务跳过（任务耗时 > 间隔） | 中 | APScheduler 设置 `misfire_grace_time`，记录跳过的任务 |
| 时区配置错误导致盘后下单 | 中 | 单元测试覆盖时区逻辑；下单前验证当前时间是否在交易时间内 |

---

## 8. 目录结构

```
mytrader/
└── infra/
    ├── __init__.py
    ├── config.py              # AppConfig（Pydantic）
    ├── event_bus.py           # EventBus + Events 常量
    ├── scheduler.py           # APScheduler 封装
    └── container.py           # 依赖注入容器

config/
├── default.yaml               # 默认配置（提交 Git）
├── paper.yaml                 # Paper Trading 覆盖配置
└── live.yaml                  # 实盘覆盖配置（提交 Git，不含敏感信息）

.env                           # 敏感信息（不提交 Git）
.env.example                   # 模板（提交 Git，供参考）
```

---

## 参考来源

- [Pydantic BaseSettings 文档](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [APScheduler 文档](https://apscheduler.readthedocs.io/)
- [The Twelve-Factor App — Config](https://12factor.net/config)
- [Event-Driven Architecture — Martin Fowler](https://martinfowler.com/articles/201701-event-driven.html)
