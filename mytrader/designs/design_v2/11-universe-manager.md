# Module 11 — Universe Manager（标的池管理）

> 上级文档：[00-overview.md](./00-overview.md)  
> Phase 5 新增模块

---

## 1. 职责

- 维护可交易标的池：**S&P 500 + Nasdaq 100**（去重后约 550 只）
- 定期更新指数成分股（成分股会调整）
- 按标的特征**分组**（波动率 / 行业 / 市值），供分组参数和分组策略使用
- 向 Strategy Matrix Runner 提供"标的 → 所属组"的映射

> Universe Manager 是 v2 引入"大规模标的扫描"的入口。
> v1 没有此模块（标的手动配 6 只），v2 把标的从配置项升级为受管理的动态池。

---

## 2. 为什么需要分组（核心设计）

### 2.1 S&P 500 vs Nasdaq 100 的策略适配差异

| 维度 | S&P 500 | Nasdaq 100 |
|------|---------|-----------|
| 行业集中度 | 分散（11 行业） | 科技股占 ~57% |
| 平均波动率 β | ~1.0 | ~1.2-1.3 |
| 动量持续性 | 中等 | **强**（科技股强者恒强） |
| 均值回归特征 | 明显 | 弱 |

**策略适配规律**（Ernie Chan / de Prado 实证）：

```
S&P 500 成分 → 均值回归策略（RSI、布林带）表现更好
Nasdaq 100 成分（科技股）→ 趋势/动量策略（双均线、MACD）表现更好
```

> 同一策略在两组上的 Sharpe 可能差 2-3 倍。这不是策略问题，是**策略×市场结构适配**问题。

### 2.2 分组解决两个问题

```
问题 1：策略↔标的匹配
  → 按组回测，每组选出最适合的策略（数据驱动，非手动 mapping）

问题 2：参数过拟合
  → 按组共用参数（而非单只优化），控制自由度，防过拟合
```

---

## 3. 分组维度

| 分组维度 | 分组方式 | 用途 |
|---------|---------|------|
| **波动率** | 按 ATR%/close 分位：高(>3%) / 中(1-3%) / 低(<1%) | 参数分组（高波动用更长慢均线） |
| **指数归属** | S&P 500 / Nasdaq 100 / 两者都属 | 策略分组（动量 vs 均值回归） |
| **行业** | GICS 11 大板块 | 板块轮动、相关性控制 |
| **市值** | 大盘 / 中盘分位 | 流动性、冲击成本评估 |

> Phase 5 初期建议**先用"波动率 × 指数归属"二维分组**（最影响策略适配），
> 行业/市值作为后续扩展。

### 分组示例

```
Group A: Nasdaq 高波动（如 TSLA, NVDA）→ 趋势策略 + 长周期参数
Group B: Nasdaq 中波动（如 AAPL, MSFT）→ 趋势策略 + 中周期参数
Group C: S&P 低波动（如 JNJ, PG）   → 均值回归策略 + 短周期参数
...
```

---

## 4. 成分股数据来源

| 来源 | 内容 | 更新频率 |
|------|------|---------|
| Wikipedia S&P 500 列表 | 成分股 + 行业 | 季度调整 |
| Nasdaq 100 官方列表 | 成分股 | 年度调整 |
| 静态 CSV（手动维护） | 兜底，避免依赖网络 | 手动 |

> 成分股变动不频繁（季度/年度），可缓存到本地，定期（如每月）刷新一次。
> 避免每次扫描都去抓取成分股列表。

---

## 5. 模块接口设计

```python
@dataclass
class SymbolMeta:
    symbol: str
    index_membership: list[str]    # ["SP500"] / ["NASDAQ100"] / ["SP500","NASDAQ100"]
    sector: str                    # GICS 板块
    market_cap_tier: str           # "large" / "mid"
    volatility_tier: str           # "high" / "mid" / "low"（动态计算）
    group_id: str                  # 综合分组 ID，如 "NDX_high_vol"


class UniverseManager:
    """标的池管理器。"""

    def __init__(self, store: MarketDataStore,
                 universe_file: str = "config/universe.csv") -> None: ...

    def get_universe(self) -> list[str]:
        """返回当前全部可交易标的（去重后 ~550 只）。"""

    def get_symbol_meta(self, symbol: str) -> SymbolMeta:
        """返回单只标的的元信息（含所属组）。"""

    def get_groups(self) -> dict[str, list[str]]:
        """返回 {group_id: [symbols]} 分组映射。"""

    def refresh_constituents(self) -> None:
        """刷新指数成分股（每月调用）。"""

    def recompute_volatility_tiers(self, lookback_days: int = 60) -> None:
        """基于近 60 天数据重算波动率分层（动态，随行情变化）。"""

    def recompute_volatility_tiers_at(self, as_of_date: date,
                                       lookback_days: int = 60) -> dict[str, str]:
        """历史时点波动率分层（供矩阵回测 point-in-time 使用）。
        返回 {symbol: volatility_tier}，而非修改当前状态。
        """
```

---

## 6. 波动率分层流程（动态）

```
recompute_volatility_tiers():
    for symbol in universe:
        df = store.get_latest_n_bars(symbol, n=60)   # 读本地库
        atr_pct = compute_atr(df, 14) / df["close"]
        recent_atr_pct = atr_pct.iloc[-20:].mean()    # 近 20 日均值
        tier = classify(recent_atr_pct)               # high/mid/low

    # 按分位数划分，保证各组样本量均衡（如三分位）
```

> 波动率分层是**动态**的——一只股票可能从"中波动"变成"高波动"（如临近财报）。
> 建议每周或每月重算一次，与策略权重更新同频。

---

## 7. 与下游的交互

```
UniverseManager.get_groups()
        ↓
{
  "NDX_high_vol": ["TSLA", "NVDA", ...],
  "NDX_mid_vol":  ["AAPL", "MSFT", ...],
  "SPX_low_vol":  ["JNJ", "PG", ...],
  ...
}
        ↓
Strategy Matrix Runner 读 strategy_weights.json：
  "NDX_high_vol" → [dual_ma(5,60 权重0.6), macd(权重0.4)]
  "SPX_low_vol"  → [rsi(权重0.7), bollinger(权重0.3)]
        ↓
对每只标的运行其所属组的策略
```

---

## 8. 注意点

### 8.1 去重
- 同时属于 S&P 500 和 Nasdaq 100 的标的（如 AAPL）只交易一次
- `index_membership` 记录全部归属，但 `group_id` 唯一

### 8.2 成分股变动的幸存者偏差
- 回测时若只用**当前**成分股，会引入幸存者偏差（剔除了被踢出指数的标的）
- **偏差规模评估**：S&P 500 年均调整 ~20 只，5 年累计约 100 只（~20% 成分变动）
  - 对 SPX_low_vol（均值回归）组影响最大：被踢出的标的往往经历暴跌，不纳入会系统性高估均值回归策略的胜率
  - 对 NDX_high_vol（趋势动量）组影响相对较小（强者恒强，踢出的标的通常已止损）
- **Phase 5 初期可接受当前成分股**（简化），但须在 MatrixBacktest 报告中输出偏差提示
- 严格做法：回测用历史时点的成分股快照（需第三方数据源，如 Polygon.io 历史成分股 API）

### 8.3 新上市/退市标的
- 新纳入指数的标的本地库无历史 → DataSyncService 需触发回填
- 退市标的从 universe 移除，但保留历史数据用于回测

---

## 9. 风险点

| 风险 | 级别 | 缓解措施 |
|------|------|---------|
| 幸存者偏差 | 中 | 后续接入历史成分股快照 |
| 成分股列表抓取失败 | 低 | 本地 CSV 兜底 |
| 分组样本不均衡 | 低 | 按分位数分组，保证各组样本量 |

---

## 10. 目录结构（Phase 5 待实现）

```
mytrader/
└── universe/
    ├── __init__.py
    ├── manager.py              # UniverseManager
    ├── constituents.py         # 成分股抓取（Wikipedia/官方/CSV）
    ├── grouping.py             # 分组逻辑（波动率/行业/市值）
    └── models.py               # SymbolMeta
config/
└── universe.csv               # 成分股 + 元信息缓存
```

---

## 参考来源

- *Algorithmic Trading*, Ch.3 — Mean-Reverting vs Momentum (Ernest Chan)
- [S&P 500 Constituents — Wikipedia](https://en.wikipedia.org/wiki/List_of_S%26P_500_companies)
- *Advances in Financial Machine Learning*, Ch.7 — Survivorship Bias (de Prado)
