# Module 06 — Portfolio Tracker（持仓追踪器）

> 上级文档：[00-overview.md](./00-overview.md)

---

## 1. 职责

- 消费 OrderResult，实时更新持仓状态
- 计算盈亏（已实现 + 未实现）
- 提供当前账户状态给 Risk Manager（做仓位决策）
- 定期与券商账户数据对账，确保一致性
- 历史交易记录持久化

Portfolio Tracker 的唯一真相来源（Source of Truth）是**券商账户**，本地记录只做参考和展示用。

---

## 2. 核心数据结构

```python
@dataclass
class Position:
    symbol: str
    quantity: int              # 持有股数（负数表示空仓）
    avg_cost: float            # 平均成本价（含手续费）
    entry_time: datetime
    stop_loss: float           # 当前止损价
    take_profit: float | None
    unrealized_pnl: float      # 未实现盈亏（实时更新）
    unrealized_pnl_pct: float

@dataclass
class Portfolio:
    cash: float                # 可用现金
    total_value: float         # 总资产（现金 + 持仓市值）
    positions: dict[str, Position]  # symbol -> Position
    total_unrealized_pnl: float
    total_realized_pnl: float
    daily_pnl: float           # 当日盈亏
    max_drawdown: float        # 当前最大回撤

@dataclass
class TradeRecord:
    trade_id: str
    symbol: str
    direction: str
    quantity: int
    entry_price: float
    exit_price: float | None
    entry_time: datetime
    exit_time: datetime | None
    realized_pnl: float | None
    commission: float
    strategy_name: str         # 哪个策略触发的
    notes: str
```

---

## 3. 盈亏计算

### 3.1 未实现盈亏（Unrealized PnL）

```python
def calc_unrealized_pnl(position: Position, current_price: float) -> float:
    market_value = current_price * position.quantity
    cost_basis   = position.avg_cost * position.quantity
    return market_value - cost_basis
```

### 3.2 已实现盈亏（Realized PnL）

使用 **FIFO（先进先出）** 成本法（与大多数税务要求一致）：

```python
def calc_realized_pnl(entry_trades: list[Trade], exit_trade: Trade) -> float:
    # FIFO: 最早买入的先卖出
    remaining_qty = exit_trade.quantity
    total_cost = 0
    for entry in sorted(entry_trades, key=lambda t: t.entry_time):
        matched_qty = min(remaining_qty, entry.quantity)
        total_cost += matched_qty * entry.avg_cost
        remaining_qty -= matched_qty
        if remaining_qty == 0:
            break
    proceeds = exit_trade.fill_price * exit_trade.quantity - exit_trade.commission
    return proceeds - total_cost
```

### 3.3 平均成本更新

加仓时需要重新计算平均成本：

```python
def update_avg_cost(position: Position, new_quantity: int, new_price: float, commission: float) -> float:
    total_cost = position.avg_cost * position.quantity + new_price * new_quantity + commission
    total_quantity = position.quantity + new_quantity
    return total_cost / total_quantity
```

---

## 4. 对账机制

定期（每 5 分钟）将本地记录与券商数据对比：

```python
class ReconciliationService:
    def reconcile(self, local_portfolio: Portfolio, broker_portfolio: BrokerPortfolio):
        discrepancies = []

        for symbol, local_pos in local_portfolio.positions.items():
            broker_pos = broker_portfolio.positions.get(symbol)
            if broker_pos is None:
                discrepancies.append(f"{symbol}: 本地有持仓，券商无持仓")
            elif abs(local_pos.quantity - broker_pos.quantity) > 0:
                discrepancies.append(
                    f"{symbol}: 数量不一致 本地={local_pos.quantity} 券商={broker_pos.quantity}"
                )

        if discrepancies:
            # 以券商数据为准，更新本地记录
            self._sync_from_broker(broker_portfolio)
            # 告警
            alert_service.send(f"对账差异: {discrepancies}")
```

---

## 5. 持久化设计

### 5.1 数据库 Schema（SQLAlchemy）

```sql
-- 交易记录表
CREATE TABLE trades (
    id          TEXT PRIMARY KEY,
    symbol      TEXT NOT NULL,
    direction   TEXT NOT NULL,       -- BUY / SELL
    quantity    INTEGER NOT NULL,
    fill_price  REAL NOT NULL,
    commission  REAL NOT NULL,
    fill_time   DATETIME NOT NULL,
    strategy    TEXT,
    order_id    TEXT,
    broker      TEXT,
    notes       TEXT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 快照表（每日盘后保存账户状态）
CREATE TABLE portfolio_snapshots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_date   DATE NOT NULL,
    cash            REAL NOT NULL,
    total_value     REAL NOT NULL,
    realized_pnl    REAL NOT NULL,
    unrealized_pnl  REAL NOT NULL,
    max_drawdown    REAL NOT NULL,
    positions_json  TEXT,           -- JSON 格式的持仓快照
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 6. 关键指标计算

```python
class PortfolioMetrics:
    def sharpe_ratio(self, daily_returns: pd.Series, risk_free_rate: float = 0.0) -> float:
        excess_returns = daily_returns - risk_free_rate / 252
        return excess_returns.mean() / excess_returns.std() * np.sqrt(252)

    def max_drawdown(self, portfolio_values: pd.Series) -> float:
        peak = portfolio_values.cummax()
        drawdown = (portfolio_values - peak) / peak
        return drawdown.min()

    def calmar_ratio(self, annualized_return: float, max_drawdown: float) -> float:
        return annualized_return / abs(max_drawdown)

    def win_rate(self, trades: list[TradeRecord]) -> float:
        closed_trades = [t for t in trades if t.realized_pnl is not None]
        winning = [t for t in closed_trades if t.realized_pnl > 0]
        return len(winning) / len(closed_trades) if closed_trades else 0
```

---

## 7. 注意点

### 7.1 现金管理
- 买入时要扣除手续费后才是可用现金
- 需要预留足够现金（默认 20%）以应对追加保证金或突发机会

### 7.2 港股特殊情况
- 港股每手股数不同（如腾讯 100 股/手），持仓显示应按手数展示
- 港股印花税（0.1%）是单向的，卖出时收取

### 7.3 历史数据不可修改
- 交易记录一旦写入数据库，不应修改（只能追加注释/标注）
- 如果对账发现错误，用新的调整记录覆盖，不删除原始记录

### 7.4 分红、拆股的处理
- 分红会影响持仓成本基础的计算
- 拆股/合股会改变持仓数量
- 需要单独的企业行动（Corporate Actions）事件处理

---

## 8. 风险点

| 风险 | 级别 | 缓解措施 |
|------|------|---------|
| 本地记录与券商不一致 | 高 | 定期对账，以券商数据为准 |
| 成本基础计算错误（影响税务） | 高 | 使用 FIFO 法，关键计算写单元测试 |
| 并发更新导致数据竞争 | 中 | 使用数据库事务，单线程写入 |
| 数据库文件损坏 | 中 | 每日备份，关键操作用事务包裹 |
| 分红/拆股未处理导致持仓错误 | 低 | 订阅券商的企业行动事件通知 |

---

## 9. 目录结构

```
mytrader/
└── portfolio/
    ├── __init__.py
    ├── models.py              # Position, Portfolio, TradeRecord 数据结构
    ├── tracker.py             # Portfolio 状态管理
    ├── pnl_calculator.py      # 盈亏计算（FIFO）
    ├── metrics.py             # Sharpe, MaxDD, Calmar 等
    ├── reconciliation.py      # 对账服务
    └── persistence.py         # SQLAlchemy 持久化
```

---

## 参考来源

- [FIFO vs LIFO Cost Basis](https://www.investopedia.com/articles/personal-finance/031215/how-calculate-your-portfolios-investment-returns.asp)
- [Hong Kong Stamp Duty — HKEx](https://www.hkex.com.hk/Services/Trading/Securities/Securities-Trading/Transaction-Levy-and-Stamp-Duty?sc_lang=en)
- *Quantitative Portfolio Management* — Michael Isichenko
