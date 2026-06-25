# Module 04 — Risk Manager（风险管理器）

> 上级文档：[00-overview.md](./00-overview.md)

---

## 1. 职责

- 接收 FilteredSignal + 当前账户状态
- 计算合理的仓位大小
- 设定止损价、止盈价
- 全局熔断：当亏损超过阈值时，停止所有交易
- 输出 OrderIntent（意向订单，含数量、止损/止盈价格）

Risk Manager 是系统的**安全阀**，策略再好也可能遇到黑天鹅。它的首要目标是**控制最大亏损**，而不是最大化收益。

> 核心原则：**先问"如果错了会亏多少"，再问"如果对了能赚多少"**

---

## 2. 仓位计算方法

### 2.1 固定金额法（最简单，推荐新手）

每次交易使用固定金额，不考虑风险：

```python
def fixed_amount_size(account_value: float, fixed_amount: float, price: float) -> int:
    """每次买入固定金额（如 $1000）的股票"""
    return int(fixed_amount / price)
```

| 优点 | 缺点 |
|------|------|
| 简单直观 | 不考虑波动率，高波动股票风险更大 |

### 2.2 固定比例法

每次交易使用账户资产的固定比例：

```python
def fixed_fraction_size(account_value: float, fraction: float, price: float) -> int:
    """fraction = 0.1 表示每次用账户资产的 10%"""
    trade_value = account_value * fraction
    return int(trade_value / price)
```

### 2.3 ATR 波动率仓位法（推荐）

根据股票波动率动态调整仓位，风险标准化：

```python
def atr_position_size(
    account_value: float,
    risk_per_trade: float,  # 每次愿意亏损的金额，如账户的 1%
    entry_price: float,
    atr: float,
    atr_multiplier: float = 2.0
) -> tuple[int, float]:
    """
    止损距离 = ATR * multiplier
    仓位 = 愿意亏损的金额 / 止损距离（每股）
    Returns: (shares, stop_loss_price)
    """
    stop_distance = atr * atr_multiplier
    stop_loss_price = entry_price - stop_distance
    risk_amount = account_value * risk_per_trade
    shares = int(risk_amount / stop_distance)
    return shares, stop_loss_price
```

| 优点 | 缺点 |
|------|------|
| 风险标准化，不同波动率的股票风险可比 | 需要实时 ATR 计算 |
| ATR 越大，仓位越小（自动保护） | 参数（ATR 倍数）需要优化 |

### 2.4 Kelly Criterion（高级，可选）

理论最优仓位，基于历史胜率：

```
f* = (bp - q) / b
其中：b = 赔率（平均盈利/平均亏损），p = 胜率，q = 1-p
```

**注意**：Kelly Criterion 极其激进，实践中通常用 1/4 Kelly 或 1/2 Kelly。

---

## 3. 止损/止盈机制

### 3.1 固定止损（Initial Stop Loss）

```
止损价 = 入场价 × (1 - stop_loss_pct)
```

### 3.2 ATR 跟踪止损（Trailing Stop，推荐）

止损随价格上涨而移动，锁定利润：

```python
def trailing_stop(prices: pd.Series, atr: pd.Series, multiplier: float = 2.0) -> pd.Series:
    """
    当价格创新高时，止损上移到 new_high - ATR * multiplier
    价格回落触及止损时，平仓
    """
    ...
```

### 3.3 时间止损

如果持仓超过 N 天还未达到目标，强制平仓：

```yaml
risk:
  max_holding_days: 5   # 日间交易不超过 5 天
```

### 3.4 止盈（Take Profit）

```
止盈价 = 入场价 × (1 + take_profit_pct)
```

或基于风险回报比（R:R）：
```
止盈价 = 入场价 + 止损距离 × 2   # 2:1 的风险回报比
```

---

## 4. 全局熔断机制

```python
class CircuitBreaker:
    """
    三层熔断：
    1. 单日亏损超过 X% → 暂停当日交易
    2. 周亏损超过 Y% → 降低仓位至 50%
    3. 月亏损超过 Z% → 停止所有交易，等待人工审查
    """
    daily_loss_limit: float = 0.02    # 单日最大亏损 2%
    weekly_loss_limit: float = 0.05   # 周最大亏损 5%
    monthly_loss_limit: float = 0.10  # 月最大亏损 10%

    def check(self, portfolio: Portfolio) -> CircuitBreakerState:
        ...
```

---

## 5. OrderIntent 数据结构

```python
@dataclass
class OrderIntent:
    symbol: str
    direction: str           # "BUY" | "SELL"
    quantity: int            # 股数
    order_type: str          # "MARKET" | "LIMIT"
    limit_price: float | None
    stop_loss: float         # 止损价
    take_profit: float | None
    max_holding_days: int
    risk_amount: float       # 本次交易的预计最大亏损金额
    position_pct: float      # 占账户资产的比例
    reason: str              # 用于日志：为什么生成这个订单
    source_signal: Signal    # 原始信号，用于追溯
```

---

## 6. 仓位约束

```yaml
risk:
  max_single_position_pct: 0.20   # 单个标的不超过账户 20%（ATR 仓位法结果的上限，取 min）
  max_total_exposure_pct: 0.80    # 总持仓不超过账户 80%（留 20% 现金）
  max_sector_exposure_pct: 0.40   # 单板块不超过账户 40%（需板块分类数据）
  max_concurrent_positions: 5     # 最多同时持有 5 个标的
  min_order_value: 500            # 单笔订单最小金额（避免碎股费用）
```

**约束优先级（从高到低）：**

```
1. max_total_exposure_pct    → 全局上限，最优先
2. max_sector_exposure_pct   → 板块约束，被拒时从 Signal Ranker 的候选列表递补
3. max_concurrent_positions  → 持仓数量上限
4. max_single_position_pct   → ATR 仓位法计算结果与此值取 min（不是拒绝，是截断）
5. min_order_value           → 计算后仓位低于此值则跳过
```

> Signal Ranker 输出 Top-2K 候选（K=5 时输出 10 个），Risk Manager 逐个尝试下单，
> 被约束拒绝则递补下一候选，直到凑满 K 个或候选耗尽。

---

## 7. 注意点

### 7.1 仓位计算的精度问题
- 股数必须是整数（部分券商支持碎股）
- `int()` 会向下取整，应确保不超过风险上限
- 港股有最小交易单位（手）限制，需要按手数取整

### 7.2 多仓位的相关性风险
- 持有多个高相关性资产（如同板块股票），组合风险可能远超单仓位风险
- 建议计算持仓的相关系数矩阵，避免过度集中

### 7.3 流动性约束
- 订单量不应超过该股票日均成交量的 5-10%（避免影响市场）
- 小市值/港股可能流动性差，止损时可能无法成交

### 7.4 熔断触发后的处理
- 熔断时不应立即市价平仓所有仓位（可能在最低点卖出）
- 熔断应停止**开新仓**，现有仓位继续执行正常止损

### 7.5 隔夜跳空风险管理
系统定位"持仓 1-5 天"，必须持仓过夜，隔夜跳空是短线策略的主要风险来源：

```yaml
risk:
  # 可选约束（Phase 5 初期建议先启用 earnings_exit，其余观察后决定）
  max_overnight_positions: 3          # 持仓过夜上限（可选，降低同时暴露数）
  earnings_exit_days_before: 1        # 财报前 T-1 强制平仓（03-signal-filter 已标记财报日）
  vix_high_threshold: 30              # VIX 超过此值时降低 max_single_position_pct 至 10%
```

- **财报前平仓**：03-signal-filter.md §2.5 已标记财报日，建议从"标记高风险"升级为"T-1 强制平仓"
- **VIX 阈值**：VIX>30 时单仓上限从 20% 降至 10%，降低极端波动暴露
- 以上均为可配置项，Phase 5 初期可仅启用 `earnings_exit`，积累数据后再决定是否启用其他约束

---

## 8. 风险点

| 风险 | 级别 | 缓解措施 |
|------|------|---------|
| 仓位过大，单次亏损毁掉账户 | 极高 | 严格执行每次风险 ≤ 1-2%，使用 ATR 仓位法 |
| 止损单未成交（跳空） | 高 | 了解券商的止损单类型（Stop-Market vs Stop-Limit） |
| 多仓位相关性叠加风险 | 高 | 监控持仓相关系数，限制同板块持仓 |
| 熔断后情绪化操作 | 中 | 熔断自动执行，不允许人工绕过 |
| 港股手数限制导致仓位失真 | 低 | 按手数取整后重新计算实际风险 |

---

## 9. 目录结构

```
mytrader/
└── risk/
    ├── __init__.py
    ├── models.py              # OrderIntent 数据结构
    ├── position_sizer.py      # 仓位计算（固定/ATR/Kelly）
    ├── stop_loss.py           # 止损/止盈/跟踪止损计算
    ├── circuit_breaker.py     # 熔断机制
    └── constraints.py         # 仓位约束检查
```

---

## 参考来源

- *Algorithmic Trading*, Ch.6 — Risk Management (Ernest Chan)
- *The Art of Risk Management* — Christopher Culp
- [Van Tharp — Position Sizing](https://www.vantharp.com/tharp-concepts/position-sizing.asp)
- [ATR-based Position Sizing — Investopedia](https://www.investopedia.com/articles/trading/08/average-true-range.asp)
- *Advances in Financial Machine Learning*, Ch.14 — Backtesting on Synthetic Data (de Prado)
- [Kelly Criterion in Trading](https://en.wikipedia.org/wiki/Kelly_criterion)
