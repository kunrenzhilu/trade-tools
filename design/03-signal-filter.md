# Module 03 — Signal Filter（信号过滤器）

> 上级文档：[00-overview.md](./00-overview.md)

---

## 1. 职责

- 接收 Strategy Engine 输出的原始 Signal
- 通过多维度条件过滤，剔除低质量信号
- 控制信号频率，避免过度交易
- 输出经过验证的 FilteredSignal，传递给 Risk Manager

Signal Filter 的核心价值是**减少假信号**，提高信号的胜率，而不是增加信号数量。

---

## 2. 过滤维度

### 2.1 成交量确认过滤

信号有效性应得到成交量支撑：

```python
def volume_filter(df: pd.DataFrame, signal: pd.Series, threshold: float = 1.5) -> pd.Series:
    """
    只接受当日成交量 > N日平均成交量 * threshold 的信号
    """
    avg_volume = df['volume'].rolling(20).mean()
    volume_confirm = df['volume'] > avg_volume * threshold
    return signal.where(volume_confirm, 0)
```

| 场景 | 说明 |
|------|------|
| 放量突破 | 有效信号，允许通过 |
| 缩量突破 | 可疑，过滤掉 |
| 量价背离 | 价格新高但成交量下降，过滤卖出信号 |

### 2.2 波动率过滤（ATR Filter）

极端波动环境下，信号可靠性下降：

```python
def atr_filter(df: pd.DataFrame, signal: pd.Series,
               atr_period: int = 14, max_atr_pct: float = 0.05) -> pd.Series:
    """
    当 ATR / close > max_atr_pct（如 5%）时，市场过于波动，过滤所有信号
    """
    atr = compute_atr(df, atr_period)
    atr_pct = atr / df['close']
    too_volatile = atr_pct > max_atr_pct
    return signal.where(~too_volatile, 0)
```

### 2.3 市场情绪过滤

参考宏观/市场情绪指标，决定是否允许开仓：

| 指标 | 说明 | 阈值示例 |
|------|------|---------|
| VIX（恐慌指数） | VIX > 30 时市场极度恐慌 | VIX > 30 时禁止做多 |
| 大盘趋势 | SPY/HSI 均线方向 | 大盘跌破 200 日均线时只做空 |
| 板块相对强度 | 个股所在板块是否强势 | 板块弱于大盘时降低信号权重 |

### 2.4 信号频率控制（Cooldown）

防止在同一方向上短时间内重复开仓：

```python
def cooldown_filter(signal: pd.Series, min_bars: int = 5) -> pd.Series:
    """
    同向信号之间至少间隔 min_bars 根 K 线
    """
    result = signal.copy()
    last_signal_bar = -min_bars
    for i in range(len(signal)):
        if signal.iloc[i] != 0:
            if i - last_signal_bar < min_bars:
                result.iloc[i] = 0
            else:
                last_signal_bar = i
    return result
```

### 2.5 时间窗口过滤

避开已知的高风险时间段：

| 时间段 | 原因 | 处理 |
|--------|------|------|
| 开盘前 15 分钟 | 流动性差，价格跳动大 | 不开仓 |
| 收盘前 15 分钟 | 机构调仓，方向不稳 | 不开新仓，只平仓 |
| 财报发布前后 | 信息不对称风险 | 标记高风险，降低仓位 |
| 美联储议息日 | 波动率突变 | 暂停交易 |

---

## 3. 过滤器流水线（Pipeline）

```
原始 Signal
    │
    ▼
[成交量确认过滤] ──▶ 剔除缩量信号
    │
    ▼
[ATR 波动率过滤] ──▶ 剔除极端波动期信号
    │
    ▼
[市场情绪过滤]   ──▶ 剔除逆大盘方向信号
    │
    ▼
[时间窗口过滤]   ──▶ 剔除危险时段信号
    │
    ▼
[冷却期过滤]     ──▶ 剔除过于频繁的信号
    │
    ▼
FilteredSignal（最终输出）
```

每个过滤器都是可插拔的，通过配置文件开启/关闭：

```yaml
signal_filter:
  volume_filter:
    enabled: true
    threshold: 1.5
  atr_filter:
    enabled: true
    max_atr_pct: 0.05
  cooldown_filter:
    enabled: true
    min_bars: 5
  time_window_filter:
    enabled: true
    market_open_buffer_min: 15
    market_close_buffer_min: 15
```

---

## 4. 过滤统计与监控

每次过滤都应记录被过滤的原因，用于复盘：

```python
@dataclass
class FilterResult:
    original_signal_count: int
    passed_count: int
    filtered_by: dict[str, int]  # {"volume_filter": 3, "atr_filter": 1, ...}
    filter_rate: float            # 过滤率
```

---

## 5. 注意点

### 5.1 过滤过度 vs 过滤不足
- 过滤过度：信号太少，错过机会，策略退化为 HOLD
- 过滤不足：假信号太多，交易成本高，亏损
- 建议在回测中逐步增加过滤条件，观察每个过滤器对 Sharpe Ratio 的影响

### 5.2 过滤条件本身也可能过拟合
- 不要为了让回测数据好看而过度定制过滤条件
- 过滤条件应有经济学或统计学上的逻辑支撑

### 5.3 实盘和回测的过滤条件必须完全一致
- 如果回测中用了成交量过滤，实盘也必须用
- 任何只在回测中有效、实盘无法获取的数据，绝对不能用作过滤条件

### 5.4 过滤器顺序影响结果
- 应先做廉价的过滤（时间窗口），再做计算复杂的过滤（ATR）
- 各过滤器之间有时存在相关性，注意避免重复过滤

---

## 6. 风险点

| 风险 | 级别 | 缓解措施 |
|------|------|---------|
| 过滤条件过拟合 | 高 | 保持过滤条件的经济学逻辑，Out-of-Sample 验证 |
| 过滤掉真实有效信号 | 中 | 记录被过滤信号，定期复盘是否应调整阈值 |
| 实盘无法获取过滤所需数据 | 中 | 回测时只使用实盘可获取的数据 |
| 时间窗口在不同市场不一致 | 低 | 按市场配置不同的时间规则（美股/港股） |

---

## 7. 目录结构

```
mytrader/
└── signal/
    ├── __init__.py
    ├── models.py            # FilteredSignal 数据结构
    ├── pipeline.py          # 过滤器流水线
    └── filters/
        ├── volume_filter.py
        ├── atr_filter.py
        ├── sentiment_filter.py
        ├── time_window_filter.py
        └── cooldown_filter.py
```

---

## 参考来源

- *Algorithmic Trading*, Ch.4 — Execution and Slippage (Ernest Chan)
- [Volume-Price Analysis — Wyckoff Method](https://school.stockcharts.com/doku.php?id=market_analysis:wyckoff_stock_market_method)
- [VIX as Market Sentiment Indicator](https://www.cboe.com/tradable_products/vix/)
- *Advances in Financial Machine Learning*, Ch.7 — Cross-Validation in Finance (de Prado)
