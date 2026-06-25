# Phase 3 开发总结

> 日期：2026-06-21（最后更新）  
> Python 环境：`/Users/rickouyang/miniforge3/envs/py312trade`（Python 3.12.13）  
> 测试结果：**360 passed（Mock: 344 + Live: 16），0 failed**

---

## 1. Phase 3 已完成

### 1.1 新增目录结构

```
mytrader/mytrader/
├── infra/
│   ├── config.py               # [MODIFIED] 新增 AlpacaConfig/IBKRConfig/NotificationConfig/SchedulerConfig
│   ├── event_bus.py            # [MODIFIED] 新增 HEALTH_CHECK_FAILED/RECONCILIATION_DIFF/ORDER_NOTIFICATION_SENT 事件常量
│   ├── container.py            # [NEW] 依赖注入工厂：build_app()，根据 mode 装配 Broker + 全量模块
│   └── scheduler.py            # [NEW] TradingScheduler：APScheduler 封装，4 个定时 job，熔断前置检查
│
├── execution/
│   ├── alpaca_broker.py        # [NEW] AlpacaBroker：Alpaca 美股，semi_auto/auto 双模式，零佣金
│   ├── ibkr_broker.py          # [NEW] IBKRBroker：ib_insync 港美股，readonly 保护，自动重连
│   └── notification.py         # [NEW] NotificationService + TelegramAlerter + WeChatWorkAlerter
│
├── portfolio/
│   └── reconciliation.py       # [NEW] ReconciliationService：本地持仓 vs 券商持仓对账
│
└── monitor/                    # [NEW] 监控层（新增目录）
    ├── __init__.py
    ├── health_checker.py       # [NEW] HealthChecker：4 项健康检查，返回 HealthReport
    └── logger_setup.py         # [NEW] setup_logger()：loguru 配置，按日轮转，JSON 序列化

mytrader/
├── main.py                     # [NEW] 系统启动入口：argparse + 日志初始化 + Container.build + Scheduler.start
├── config/
│   └── default.yaml            # [MODIFIED] 新增 alpaca/ibkr/notification/scheduler 配置节
└── .env.example                # [MODIFIED] 新增 Phase 3 环境变量示例（Pydantic nested 格式）

mytrader/tests/
├── test_notification.py        # [NEW] 18 个测试
├── test_alpaca_broker.py       # [NEW] 13 个测试
├── test_container.py           # [NEW] 12 个测试
├── test_scheduler.py           # [NEW] 15 个测试
├── test_reconciliation.py      # [NEW] 16 个测试
└── test_monitor.py             # [NEW] 20 个测试（含 logger_setup）
```

---

## 2. 关键设计决策

| 决策 | 选择 | 原因 |
|------|------|------|
| **Broker 扩展方式** | 实现 Phase 2 定义的 `BrokerProtocol`（Protocol 接口） | 开闭原则，RiskManager/PortfolioTracker 无需改动 |
| **半自动模式** | `semi_auto`：AlpacaBroker 返回 PENDING，NotificationService 推送 JSON | 人工确认后再手动下单，避免误操作 |
| **alpaca-py 测试隔离** | `_build_market_order` 在 client 已注入时不 import alpaca；Mock client 直接注入 | alpaca-py 未安装时测试也能正常运行 |
| **通知防骚扰** | `alert_cooldown_seconds`：相同 key 的告警最小间隔 | 避免连续错误重复推送，防告警疲劳 |
| **渠道异常隔离** | 每个渠道 send 调用独立 try-except | 通知失败不影响主流程 |
| **IBKR readonly** | 初期 `readonly=True`，仅允许查询不下单 | Phase 3 初期安全保护，避免 TWS 连接后意外下单 |
| **Container 工厂** | `Container.build(config)` 一键装配，支持 `broker_override` 注入 | 测试时可注入 Mock Broker，无需真实券商连接 |
| **Scheduler 熔断** | `_is_circuit_breaker_triggered()` 前置检查，跳过信号生成任务 | 日亏损超阈值时自动停止扫描，收盘前检查不受影响（需要平仓） |
| **对账自动修正** | `auto_sync=False`（默认），只告警不修改 | 避免自动修正覆盖人工操作，以券商为准但需人工确认 |
| **health_checker 注册式** | `register(name, fn)` + 内置便捷方法 | 各模块自行注册检查项，主流程组合使用 |

---

## 3. 数据流链路（Phase 3 完成后）

```
YFinanceProvider → DataCleaner → DataValidator
        ↓
  StrategyEngine（dual_ma / bollinger / rsi / macd）
        ↓
  SignalPipeline（volume → atr → sentiment → time_window → cooldown）
        ↓
  RiskManager（position_sizer + stop_loss + circuit_breaker + constraints）
        ↓
  Broker（PaperBroker / AlpacaBroker / IBKRBroker）
    │
    ├── paper 模式：下一 bar 开盘价模拟成交
    ├── semi_auto 模式：返回 PENDING + NotificationService 推送 JSON（人工确认）
    └── auto 模式：Alpaca/IBKR API 直接下单
        ↓
  PortfolioTracker（FIFO盈亏 + SQLite持久化）
        ↓
  TradingScheduler（APScheduler 4个定时 job）
        ↓
  ReconciliationService（每日 16:30 对账）

监控层（全程）：
  HealthChecker → HealthReport → EventBus.HEALTH_CHECK_FAILED
  NotificationService → TelegramAlerter / WeChatWorkAlerter
  setup_logger() → logs/（按日轮转，保留 30 天）
```

---

## 4. 测试覆盖（Phase 3 新增 142 个 Mock + 16 个 Live 集成测试）

### 4.1 Mock 单元测试

| 测试文件 | 测试数 | 主要覆盖点 |
|----------|--------|-----------|
| `test_notification.py` | 18 | TelegramAlerter（发送/失败/HTTP错误）；WeChatWorkAlerter；NotificationService（订单通知格式/半自动JSON/冷却期去重/级别过滤/渠道异常隔离/企业微信去Markdown） |
| `test_alpaca_broker.py` | 13 | semi_auto（PENDING/幂等/meta/SELL）；auto（BUY成交/SELL/API异常→REJECTED/pending状态/幂等/meta）；cancel（PENDING取消/不存在） |
| `test_container.py` | 12 | paper模式→PaperBroker；semi_auto+alpaca→AlpacaBroker；semi_auto+ibkr→IBKRBroker；broker_override；未知broker降级；EventBus；init_cash；内存DB |
| `test_scheduler.py` | 15 | 4个job注册；幂等；running属性；熔断跳过盘前/盘中扫描；收盘前检查不受熔断影响；回调异常不传播；disabled配置 |
| `test_reconciliation.py` | 16 | clean场景；local_only/broker_only/qty_mismatch差异；多标的同时差异；事件总线发布；clean不发布；PaperBroker优雅跳过；get_positions异常优雅处理；auto_sync修正/不修正；PositionDiff/ReconciliationReport数据结构 |
| `test_monitor.py` | 20 | 空检查器healthy；全通过healthy；1失败degraded；全失败unhealthy；异常→failed；failed_checks；单项检查；DB注册（ok/fail）；Scheduler注册（running/stopped）；HealthReport属性；logger_setup（创建目录/不报错/已存在目录） |

### 4.2 真实集成测试（2026-06-21）

| 测试文件 | 测试数 | 结果 |
|----------|:--:|:--:|
| `tests/test_integration_live.py` | 16 | ✅ 全部通过 |

#### Alpaca Paper 账户（6/6）

| 测试 | 结果 |
|------|:--:|
| 账户连接 + 信息 | ✅ ACTIVE，$100,000 现金，$400,000 购买力 |
| Paper 模式确认 | ✅ |
| 当前持仓 | ✅ 0 个 |
| 订单历史 | ✅ 0 条 |
| AAPL 可交易性 | ✅ tradable=True，shortable=True |
| TSLA 可交易性 | ✅ tradable=True，fractionable=True |

#### Telegram Bot（3/3）

| 测试 | 结果 |
|------|:--:|
| Bot token 有效性（getMe） | ✅ @alp_paper_bot |
| 发送测试消息 | ✅ 消息发送成功 |
| 无效 token 检测 | ✅ 正确拒绝 |

#### Container 集成（2/2）

| 测试 | 结果 |
|------|:--:|
| semi_auto 模式装配 AlpacaBroker | ✅ Container.build 输出 6 个组件 |
| NotificationService 初始化 | ✅ Telegram enabled=True |

#### IBKR TWS Paper 账户（5/5）

| 测试 | 结果 |
|------|:--:|
| TWS 连接（127.0.0.1:7497） | ✅ 连接成功 |
| 托管账户列表 | ✅ DU9820628 |
| 账户资金（SGD 基准） | ✅ NL: 1,022,693.20 | Cash: 1,022,642.60 | BP: 6,817,954.67 |
| 当前持仓 | ✅ 0 个 |
| SPY 延迟行情 | ✅ last=746.94，close=739.06 |

**总计：360 passed（344 Mock + 16 Live），0 failed**

---

---

## 5. 新增依赖

| 包 | 版本 | 用途 |
|----|------|------|
| `httpx` | ≥0.27.0 | Telegram/企业微信 HTTP 推送 |
| `apscheduler` | ≥3.10.0 | 定时任务调度（4个交易日定时 job） |
| `alpaca-py` | 已安装 | Alpaca 美股 API（Paper 账户已验证） |
| `ib_insync` | 已安装 | IBKR TWS API（Paper 账户已验证连接 + 延迟行情） |

```bash
# 安装命令
/Users/rickouyang/miniforge3/envs/py312trade/bin/pip install httpx apscheduler alpaca-py ib_insync
```

---

## 6. 启动方式

```bash
# paper 模式（默认，不连接真实券商）
cd mytrader && /Users/rickouyang/miniforge3/envs/py312trade/bin/python main.py

# semi_auto 模式（推送通知，人工确认）
python main.py --mode semi_auto

# 仅检查配置和依赖
python main.py --dry-run

# 指定配置文件
python main.py --config config/default.yaml --mode paper
```

---

## 7. Phase 4 规划（TODO）

| 模块 | 说明 | 优先级 |
|------|------|--------|
| ✅ `alpaca-py` 安装 | 已安装，Paper 账户端到端测试通过（16 个 Live 测试） | ✅ 已完成 |
| ✅ `ib_insync` 安装 | 已安装，TWS Paper 连接验证通过，延迟行情可用 | ✅ 已完成 |
| `main.py` 回调实现 | `on_morning_scan` 真实扫描逻辑（拉取行情 + 生成信号 + semi_auto 下单） | P0 |
| `data/providers/alpaca_provider.py` | AlpacaDataProvider 对接 `v2/delayed_sip`（免费全量 SIP，15min 延迟） | P0 |
| `monitor/dashboard/` | Streamlit 可视化面板：持仓/盈亏/权益曲线 | P2 |
| `portfolio/reconciliation.py` 定时集成 | 接入真实 Alpaca/IBKR `get_positions`，盘后自动对账 | P2 |
| 开盘跳空分批执行 | 极端跳空日等待回调，VWAP/定时分批替代一次性市价单 | P3 |
| 全自动模式验证 | 完成 Alpaca semi_auto 全流程端到端测试后开启 `auto` 模式 | P3 |

Phase 4 完成后，系统将升级为：

```
人工确认半自动下单（Phase 3）→ 全自动执行（Phase 4）
```
