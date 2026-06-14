# Module 05 — Execution Engine（执行引擎）

> 上级文档：[00-overview.md](./00-overview.md)

---

## 1. 职责

- 接收来自 Risk Manager 的 OrderIntent
- 根据配置模式（模拟/半自动/全自动）处理订单
- 与券商 API 交互，提交、修改、取消订单
- 处理订单状态回报（成交/部分成交/拒绝）
- 控制滑点，选择最优订单类型
- 输出 OrderResult，供 Portfolio Tracker 更新持仓

执行引擎是系统中**最容易出 Bug、最难测试、Bug 代价最高**的模块。

---

## 2. 执行模式

### 2.1 Paper Trading（纸上交易，默认模式）

- 不连接真实券商，模拟订单成交
- 假设以下一根 K 线的开盘价成交（保守假设）
- 扣除模拟手续费和滑点
- 用于策略验证，不涉及真实资金

```python
class PaperBroker:
    def submit_order(self, intent: OrderIntent) -> OrderResult:
        # 下一 bar 开盘价成交
        fill_price = next_bar_open * (1 + slippage_pct)
        commission = fill_price * quantity * commission_rate
        return OrderResult(status="FILLED", fill_price=fill_price, ...)
```

### 2.2 半自动模式

- 系统生成订单并发送通知（Telegram/企业微信）
- 人工确认后，点击链接触发实际下单
- 适合 Phase 2，积累真实交易经验

### 2.3 全自动模式

- 系统直接调用券商 API 下单
- 需要严格的风控和熔断保护
- 适合经过充分验证的策略

---

## 3. 券商 API 集成

### 3.1 Alpaca（美股，推荐入门）

```python
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

class AlpacaBroker:
    def __init__(self, api_key: str, secret_key: str, paper: bool = True):
        self.client = TradingClient(api_key, secret_key, paper=paper)

    def submit_order(self, intent: OrderIntent) -> OrderResult:
        order_data = MarketOrderRequest(
            symbol=intent.symbol,
            qty=intent.quantity,
            side=OrderSide.BUY if intent.direction == "BUY" else OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
        )
        order = self.client.submit_order(order_data)
        return self._parse_result(order)
```

**Alpaca 特点**：
- 免佣金，零碎股支持
- Paper Trading 环境完善
- REST + WebSocket API
- 仅支持美股和部分加密货币

### 3.2 IBKR via ib_insync（港美股，生产推荐）

```python
from ib_insync import IB, Stock, MarketOrder

class IBKRBroker:
    def __init__(self, host: str = "127.0.0.1", port: int = 7497):
        self.ib = IB()
        self.ib.connect(host, port, clientId=1)

    def submit_order(self, intent: OrderIntent) -> OrderResult:
        contract = Stock(intent.symbol, "SMART", "USD")
        order = MarketOrder(
            action="BUY" if intent.direction == "BUY" else "SELL",
            totalQuantity=intent.quantity
        )
        trade = self.ib.placeOrder(contract, order)
        self.ib.sleep(1)  # 等待确认
        return self._parse_trade(trade)
```

**IBKR 特点**：
- 支持全球市场（美股、港股、期货、期权）
- 需要本地运行 TWS（Trader Workstation）或 IB Gateway
- 手续费较低但不为零
- API 文档相对复杂

### 3.3 券商对比

| 特性 | Alpaca | IBKR |
|------|--------|------|
| 覆盖市场 | 美股 | 全球 |
| 手续费 | 零佣金 | 较低（非零） |
| API 复杂度 | 简单 | 复杂 |
| Paper Trading | 原生支持 | 需要独立账户 |
| 最低资金 | 无要求 | $0（但功能有限制） |
| 港股 | 不支持 | 支持 |
| 推荐阶段 | Phase 2 快速验证 | Phase 3 生产 |

---

## 4. 订单类型策略

### 4.1 订单类型选择

| 场景 | 推荐订单类型 | 原因 |
|------|------------|------|
| 日间交易信号 | Limit Order（买一价附近） | 控制滑点 |
| 止损 | Stop-Market Order | 确保成交，控制最大亏损 |
| 紧急平仓（熔断） | Market Order | 优先确保成交 |
| 低流动性股票 | Limit Order | 避免大滑点 |

### 4.2 限价单策略

```python
def calculate_limit_price(signal: Signal, direction: str, spread_pct: float = 0.001) -> float:
    """
    BUY：在当前价 + 一个小溢价，确保能成交
    SELL：在当前价 - 一个小溢价
    """
    if direction == "BUY":
        return signal.price_hint * (1 + spread_pct)
    else:
        return signal.price_hint * (1 - spread_pct)
```

### 4.3 未成交订单处理

```yaml
execution:
  limit_order_timeout_min: 5    # 5分钟未成交，取消限价单
  retry_as_market: false         # 是否改为市价单重试（风险：大滑点）
  max_retry_count: 1
```

---

## 5. 滑点模型（Paper Trading 用）

在回测/纸上交易中模拟真实的执行成本：

```python
@dataclass
class SlippageModel:
    """
    固定比例滑点模型（简单且保守）
    更复杂的模型可以基于成交量和价差
    """
    base_slippage_pct: float = 0.001   # 0.1% 基础滑点
    commission_pct: float = 0.001       # 0.1% 手续费（Alpaca 为 0）

    def apply(self, price: float, quantity: int, direction: str) -> tuple[float, float]:
        """
        Returns: (fill_price, total_commission)
        """
        if direction == "BUY":
            fill_price = price * (1 + self.base_slippage_pct)
        else:
            fill_price = price * (1 - self.base_slippage_pct)
        commission = fill_price * quantity * self.commission_pct
        return fill_price, commission
```

---

## 6. OrderResult 数据结构

```python
@dataclass
class OrderResult:
    order_id: str
    symbol: str
    direction: str
    quantity: int
    fill_price: float
    fill_time: datetime
    commission: float
    status: str          # "FILLED" | "PARTIAL" | "CANCELLED" | "REJECTED"
    broker_order_id: str
    error_message: str | None
    raw_response: dict   # 原始券商响应，用于调试
```

---

## 7. 注意点

### 7.1 订单重复提交
- 网络超时后重试可能导致重复下单
- 必须使用幂等性 ID（Client Order ID），券商会自动去重

### 7.2 部分成交处理
- 订单可能只成交了一部分，剩余部分处于待成交状态
- 需要决策：等待剩余成交 or 取消剩余部分
- 日间交易中，如果接近收盘还未完全成交，应取消并以市价成交

### 7.3 TWS/IB Gateway 进程依赖（IBKR 特有）
- `ib_insync` 需要本地运行 TWS 或 IB Gateway 软件
- 软件重启或断线后需要重新连接
- 生产环境中需要自动重连机制

### 7.4 API 密钥安全
- 绝对不能把 API Key 提交到 Git
- 使用环境变量或 `.env` 文件（加入 `.gitignore`）
- 只申请必要的权限（只交易，不提款）

### 7.5 Paper Trading 的局限性
- Paper Trading 假设订单总是能成交，不反映真实流动性
- 真实交易中，在低流动性股票上大单可能无法成交或造成大滑点

---

## 8. 风险点

| 风险 | 级别 | 缓解措施 |
|------|------|---------|
| 重复下单 | 极高 | Client Order ID 幂等性 + 下单前检查未完成订单 |
| 错误方向下单（Bug） | 极高 | 下单前人工确认（Phase 2）；生产中添加断路器 |
| API Key 泄露 | 高 | 环境变量存储，不提交 Git，定期轮换 |
| 网络中断后未知状态 | 高 | 下单后主动轮询订单状态，而不是依赖回调 |
| 滑点超预期（大单/低流动性） | 中 | 设置最大可接受滑点，超过时取消订单 |

---

## 9. 目录结构

```
mytrader/
└── execution/
    ├── __init__.py
    ├── models.py              # OrderResult 数据结构
    ├── base.py                # Broker Protocol 定义
    ├── paper_broker.py        # Paper Trading 实现
    ├── brokers/
    │   ├── alpaca_broker.py
    │   └── ibkr_broker.py
    ├── slippage.py            # 滑点模型
    └── order_manager.py       # 订单状态管理、重试、去重
```

---

## 参考来源

- [Alpaca Python SDK 文档](https://alpaca.markets/sdks/python/)
- [ib_insync 文档](https://ib-insync.readthedocs.io/)
- [IBKR API 文档](https://interactivebrokers.github.io/tws-api/)
- *Algorithmic Trading*, Ch.4 — Execution and Slippage (Ernest Chan)
- [Order Types Guide — Investopedia](https://www.investopedia.com/trading/order-types/)
