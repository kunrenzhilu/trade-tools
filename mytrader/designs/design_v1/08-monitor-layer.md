# Module 08 — Monitor Layer（监控层）

> 上级文档：[00-overview.md](./00-overview.md)

---

## 1. 职责

- 实时监控系统健康状态（各模块是否正常运行）
- 监控账户状态（资金、持仓、盈亏）
- 触发告警（价格突破止损、熔断触发、系统异常）
- 记录结构化日志，支持事后复盘
- 提供可选的 Dashboard 展示

监控层是系统的"神经系统"，让你在不盯盘的情况下也能感知系统状态。

---

## 2. 监控维度

### 2.1 系统健康监控

| 检查项 | 正常 | 告警 |
|--------|------|------|
| 数据源连接 | 正常返回数据 | 连续 2 次失败 |
| 券商 API 连接 | 心跳正常 | 断线超过 30 秒 |
| 定时任务运行 | 按时执行 | 超时或未触发 |
| 内存/CPU | < 80% | > 90% 持续 5 分钟 |
| 磁盘空间 | > 1GB 可用 | < 500MB |

### 2.2 交易状态监控

| 监控项 | 触发条件 | 处置 |
|--------|---------|------|
| 止损触及 | 持仓价格 ≤ 止损价 | 告警 + 自动平仓（如开启） |
| 订单长时间未成交 | > 5 分钟未成交 | 告警，等待人工确认 |
| 日亏损超阈值 | 日亏损 > 2% | 告警 + 触发熔断 |
| 单仓位亏损超阈值 | 单仓亏损 > 5% | 告警 |
| 意外空仓 | 预期有仓位但实际无 | 紧急告警 |

### 2.3 数据质量监控

| 监控项 | 触发条件 |
|--------|---------|
| 数据中断 | 交易时间内超过 10 分钟无新 bar |
| 价格异常 | 单 bar 涨跌 > 30% |
| 成交量异常 | 成交量 > 平均的 10 倍 |

---

## 3. 告警渠道

### 3.1 Telegram Bot（推荐）

```python
import httpx

class TelegramAlerter:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    def send(self, message: str, level: str = "INFO"):
        emoji = {"INFO": "ℹ️", "WARN": "⚠️", "ERROR": "🚨", "TRADE": "💹"}.get(level, "")
        text = f"{emoji} [{level}] {message}"
        httpx.post(f"{self.base_url}/sendMessage", json={
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown"
        })
```

### 3.2 企业微信 Webhook

```python
class WeChatWorkAlerter:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send(self, message: str):
        httpx.post(self.webhook_url, json={
            "msgtype": "text",
            "text": {"content": message}
        })
```

### 3.3 告警级别设计

| 级别 | 场景 | 渠道 |
|------|------|------|
| INFO | 交易信号生成、订单成交 | 日志文件 |
| WARN | 数据质量问题、订单延迟 | Telegram |
| ERROR | 模块异常、API 连接失败 | Telegram + 短信（可选） |
| CRITICAL | 熔断触发、大额亏损 | 所有渠道 |

---

## 4. 日志设计

使用 `loguru` 实现结构化日志：

```python
from loguru import logger
import json

# 配置日志输出
logger.add(
    "logs/mytrader_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="30 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} | {message}",
    serialize=True  # JSON 格式，方便解析
)

# 关键决策点的日志规范
def log_signal(signal: Signal):
    logger.info("SIGNAL_GENERATED", extra={
        "symbol": signal.symbol,
        "direction": signal.direction.value,
        "confidence": signal.confidence,
        "strategy": signal.strategy_name,
        "indicators": signal.indicators,
    })

def log_order(intent: OrderIntent, result: OrderResult):
    logger.info("ORDER_EXECUTED", extra={
        "symbol": intent.symbol,
        "direction": intent.direction,
        "quantity": result.quantity,
        "fill_price": result.fill_price,
        "commission": result.commission,
        "status": result.status,
    })
```

### 4.1 日志保留策略

| 日志类型 | 保留时长 | 存储位置 |
|---------|---------|---------|
| 交易日志 | 永久 | 数据库 + 文件 |
| 系统运行日志 | 30 天 | 文件 |
| 调试日志 | 7 天 | 文件 |
| 告警日志 | 90 天 | 文件 |

---

## 5. 健康检查（Health Check）

```python
class HealthChecker:
    def run_all_checks(self) -> HealthReport:
        checks = {
            "data_feed":     self._check_data_feed(),
            "broker_api":    self._check_broker_api(),
            "database":      self._check_database(),
            "scheduler":     self._check_scheduler(),
        }
        overall = "healthy" if all(v == "ok" for v in checks.values()) else "degraded"
        return HealthReport(status=overall, checks=checks, timestamp=datetime.now())

    def _check_data_feed(self) -> str:
        try:
            # 尝试获取一个简单的数据点
            data_provider.get_latest_bar("AAPL")
            return "ok"
        except Exception as e:
            return f"failed: {e}"
```

---

## 6. 可选 Dashboard

使用 `streamlit` 快速搭建本地监控面板（Phase 3 可选）：

```python
# dashboard/app.py
import streamlit as st
import pandas as pd

st.title("MyTrader Dashboard")

# 账户摘要
col1, col2, col3 = st.columns(3)
col1.metric("总资产", f"${portfolio.total_value:,.0f}", f"{portfolio.daily_pnl_pct:.2%}")
col2.metric("当日盈亏", f"${portfolio.daily_pnl:,.0f}")
col3.metric("最大回撤", f"{portfolio.max_drawdown:.2%}")

# 持仓列表
st.dataframe(positions_df)

# 最近交易
st.dataframe(recent_trades_df)

# 权益曲线
st.line_chart(equity_curve)
```

---

## 7. 注意点

### 7.1 告警疲劳（Alert Fatigue）
- 告警太多会导致忽视所有告警
- 严格控制告警阈值，只在真正需要人工干预时告警
- 日常交易通知（成交确认）用低优先级渠道（日志），不用 Telegram 打扰

### 7.2 敏感信息泄露
- 告警消息中不应包含 API Key、密码
- 账户余额信息只发到私人频道，不发群组

### 7.3 告警渠道的可靠性
- Telegram 可能在某些网络下不可用，考虑备用渠道
- 告警模块自身的异常不应导致主流程崩溃（装饰器 try-catch）

---

## 8. 风险点

| 风险 | 级别 | 缓解措施 |
|------|------|---------|
| 告警渠道失效导致错过重要通知 | 高 | 多渠道冗余，定期测试告警 |
| 日志磁盘空间耗尽 | 中 | 设置 `rotation` 和 `retention` |
| 监控模块 Bug 导致主流程崩溃 | 中 | 监控代码用 try-except 隔离 |
| 告警消息含敏感信息 | 中 | 脱敏处理，不记录完整 API Key |

---

## 9. 目录结构

```
mytrader/
└── monitor/
    ├── __init__.py
    ├── alerter.py             # 多渠道告警发送
    ├── health_checker.py      # 系统健康检查
    ├── logger_setup.py        # loguru 配置
    └── dashboard/             # 可选 Streamlit Dashboard
        └── app.py
```

---

## 参考来源

- [Loguru 文档](https://loguru.readthedocs.io/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Streamlit 文档](https://docs.streamlit.io/)
- [Alerting Best Practices — Google SRE Book](https://sre.google/sre-book/monitoring-distributed-systems/)
