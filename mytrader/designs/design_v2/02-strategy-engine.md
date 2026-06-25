# Module 02 — Strategy Engine（策略引擎）

> 上级文档：[00-overview.md](./00-overview.md)

---

## 1. 职责

- 接收来自 Data Layer 的行情数据
- 计算技术指标
- 基于指标生成交易信号（BUY / SELL / HOLD）
- 输出带置信度和元数据的 Signal 对象

Strategy Engine 是系统的**核心业务逻辑**，也是最需要保持**回测/实盘一致性**的模块。

---

## 2. 核心设计原则：策略函数纯化

策略逻辑必须写成**纯函数**（Pure Function）：
- 输入：`pd.Series`（close 收盘价序列）
- 输出：`pd.Series`（信号序列，1=BUY, -1=SELL, 0=HOLD）
- 无副作用，不依赖任何全局状态

```python
# 好的写法 ✅（实际实现方式）
def dual_ma_signal(close: pd.Series, fast: int = 10, slow: int = 30) -> pd.Series:
    fast_ma = close.rolling(fast).mean()
    slow_ma = close.rolling(slow).mean()
    buy_signal  = (crossed_above(fast_ma, slow_ma)).astype(int)
    sell_signal = (crossed_below(fast_ma, slow_ma)).astype(int)
    signal = buy_signal - sell_signal  # 1, -1, 0
    return signal.shift(1).fillna(0).astype(int)  # 关键：避免前视偏差

# 坏的写法 ❌（依赖外部状态）
class Strategy:
    def __init__(self):
        self.current_price = None  # 全局状态，实盘和回测不一致

    def generate_signal(self):
        return 1 if self.current_price > self.ma else 0
```

> **注意**：策略函数的输入是 `pd.Series`（close），不是 `pd.DataFrame`（OHLCV）。
> 若策略需要 high/low/volume 等其他列，额外传入 `df: pd.DataFrame` 参数。

---

## 3. Signal 数据结构

```python
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

class SignalDirection(Enum):
    BUY  = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

@dataclass
class Signal:
    symbol: str
    direction: SignalDirection
    timestamp: datetime
    confidence: float        # 0.0 ~ 1.0，策略对信号的置信度
    strategy_name: str       # 哪个策略产生的
    indicators: dict         # 辅助调试：当时的指标值快照
    price_hint: float | None # 建议的入场价格（可为空，由执行层决定）
```

---

## 4. 内置策略清单（初始版本）

### 4.1 双均线交叉（Dual MA Crossover）

| 项目 | 内容 |
|------|------|
| 原理 | 短期均线上穿长期均线买入，下穿卖出 |
| 参数 | `fast_period`（默认 10），`slow_period`（默认 30） |
| 适用场景 | 趋势行情，震荡市表现差 |
| 局限 | 信号滞后，频繁假突破 |

```python
def dual_ma_signal(close: pd.Series, fast: int = 10, slow: int = 30) -> pd.Series:
    """双均线交叉信号（实际实现）。"""
    fast_ma = sma(close, fast)
    slow_ma = sma(close, slow)
    buy_signal  = crossed_above(fast_ma, slow_ma).astype(int)
    sell_signal = crossed_below(fast_ma, slow_ma).astype(int)
    signal = buy_signal - sell_signal  # 1=BUY, -1=SELL, 0=HOLD
    return signal.shift(1).fillna(0).astype(int)
```

### 4.2 RSI 超买超卖

| 项目 | 内容 |
|------|------|
| 原理 | RSI < 30 超卖买入，RSI > 70 超买卖出 |
| 参数 | `period`（默认 14），`oversold`（30），`overbought`（70） |
| 适用场景 | 震荡行情，单边趋势中会逆势 |
| 局限 | 强趋势中 RSI 会长时间停留在极值区间 |

### 4.3 布林带突破

| 项目 | 内容 |
|------|------|
| 原理 | 价格突破上轨做空，突破下轨做多（均值回归版本相反） |
| 参数 | `period`（20），`std_dev`（2.0） |
| 适用场景 | 高波动个股，需结合成交量确认 |
| 局限 | 参数对不同股票差异大，需个股优化 |

### 4.4 MACD 信号线交叉

| 项目 | 内容 |
|------|------|
| 原理 | MACD 线上穿信号线买入 |
| 参数 | `fast`（12），`slow`（26），`signal`（9） |
| 适用场景 | 中期趋势确认 |

---

## 5. 策略组合（Ensemble）

多个策略投票，提高信号可靠性。**v2 关键变化：组合权重不再手填，而是由回测优化产出**
（"组合本身就是一个被回测验证过的策略"）：

```python
def ensemble_signal(
    signals: list[pd.Series],
    weights: list[float] | None = None,  # v2：权重来自 MatrixBacktest 优化
    threshold: float = 0.3,
) -> pd.Series:
    """
    加权投票（weights 自动归一化，无需预先归一化）：
    合并分数 > threshold  → BUY  (+1)
    合并分数 < -threshold → SELL (-1)
    否则                  → HOLD  (0)
    """
    n = len(signals)
    if weights is None:
        weights = [1.0 / n] * n
    else:
        total = sum(weights)
        weights = [w / total for w in weights]  # 归一化

    combined = sum(s * w for s, w in zip(signals, weights))
    result = pd.Series(0, index=combined.index, dtype=int)
    result[combined >  threshold] =  1
    result[combined < -threshold] = -1
    return result
```

> **v1 vs v2**：v1 的 ensemble 权重是手动指定的；v2 在 MatrixBacktest 阶段
> 搜索每组的最优权重组合，只有当"组合 Sharpe > 单策略最优"时才采用组合，
> 否则退化为单策略（weight=1.0）。详见 [12-strategy-matrix.md](./12-strategy-matrix.md) 第 4 节。

---

## 6. 策略注册机制与多策略调度（v2）

```python
# 策略注册表，支持动态加载
STRATEGY_REGISTRY: dict[str, Callable] = {}

def register_strategy(name: str):
    def decorator(fn):
        STRATEGY_REGISTRY[name] = fn
        return fn
    return decorator

@register_strategy("dual_ma")
def dual_ma_strategy(...): ...
```

### 6.1 v1：单策略全局配置（已废弃）

```yaml
# v1 写法：全局只有 1 个策略，所有标的共用
strategy:
  name: dual_ma
  params: { fast: 10, slow: 30 }
```

### 6.2 v2：多策略 + 分组参数 + 数据驱动 mapping

v2 不再全局配单一策略，而是**按标的分组，每组分配回测验证过的策略集**。
配置来自离线回测产出的 `strategy_weights.json`（详见 [12-strategy-matrix.md](./12-strategy-matrix.md)）：

```json
{
  "groups": {
    "NDX_high_vol": [
      {"strategy": "dual_ma", "params": {"fast": 5, "slow": 60}, "weight": 0.6},
      {"strategy": "macd",    "params": {"fast": 12, "slow": 26, "signal": 9}, "weight": 0.4}
    ],
    "SPX_low_vol": [
      {"strategy": "rsi",       "params": {"period": 14}, "weight": 0.7},
      {"strategy": "bollinger", "params": {"period": 20, "std_dev": 2.0}, "weight": 0.3}
    ]
  }
}
```

### 6.3 参数粒度：按组，不按单只 ⚠️ 防过拟合核心

```
❌ 错误做法：对 550 只各自跑网格找最优参数
   = 550 次独立优化 = 几乎必然过拟合（多重比较问题）
   = 回测 Sharpe 3.0，实盘 Sharpe -0.5

✅ 正确做法：按标的特征分组，组内共用参数
   高波动组（ATR%>3%）  → (fast=5, slow=60)   # 慢均线更长，过滤噪音
   中波动组（1%~3%）    → (fast=10, slow=30)
   低波动组（ATR%<1%）  → (fast=15, slow=20)
   → 参数区别来自标的的统计特征，不是标的本身，自由度可控
```

### 6.4 策略↔标的 mapping 是数据驱动的

```
不是手动配：AAPL → dual_ma
而是回测产出：
  S&P 500 成分（均值回归特征强）→ RSI / 布林带表现好
  Nasdaq 100 成分（科技股动量强）→ 双均线 / MACD 表现好
  → MatrixBacktest 自动为每组选出 Top 策略，写入 weights.json
```

详见 [11-universe-manager.md](./11-universe-manager.md)（分组）与
[07-backtest-module.md](./07-backtest-module.md)（矩阵回测产出权重）。

---

## 7. 注意点

### 7.1 指标计算库
- **当前实现**：`strategy/indicators.py` 底层使用 **pandas-ta 0.4.71b0**（需 Python 3.12+，在 `py312trade` 环境可用）
- 对外接口（函数签名）保持不变，策略文件无需修改
- pandas-ta 的指标计算结果与 TradingView 等主流平台一致，经过广泛验证
- `crossed_above` / `crossed_below` 两个辅助函数仍用纯 pandas 实现（pandas-ta 无对应函数）

**pandas-ta 列名约定**（`indicators.py` 内部使用，对外已封装）：

| 指标 | pandas-ta 列名格式 |
|------|--------------------|
| RSI | `RSI_{length}` |
| BB 上轨 | `BBU_{length}_{std}_{std}` |
| BB 中轨 | `BBM_{length}_{std}_{std}` |
| BB 下轨 | `BBL_{length}_{std}_{std}` |
| MACD 线 | `MACD_{fast}_{slow}_{signal}` |
| MACD 信号线 | `MACDs_{fast}_{slow}_{signal}` |
| MACD 柱 | `MACDh_{fast}_{slow}_{signal}` |
| ATR | `ATRr_{length}` |

### 7.2 参数过拟合风险 ⚠️ 高风险
- 在回测中优化太多参数，会导致策略只在历史数据上有效（过拟合）
- 缓解方案：Walk-Forward Optimization，每隔一段时间重新优化参数
- 保持参数的经济学意义：10日均线不应优化成 11 日或 9 日

### 7.3 策略适用市场环境
- 大部分技术指标策略在**趋势市**有效，在**震荡市**亏钱
- 需要引入市场状态分类（牛市/熊市/震荡），根据状态切换策略

### 7.4 信号频率控制
- 不要在每根 K 线都触发交易，增加交易成本
- 最小持仓时间：建议至少 1 天（日间交易），避免过度交易

---

## 8. 风险点

| 风险 | 级别 | 缓解措施 |
|------|------|---------|
| 策略过拟合 | 高 | Walk-Forward 测试，Combinatorial Purged Cross-Validation (CPCV) |
| 前视偏差 | 高 | 策略函数强制 `shift(1)`，单元测试验证 |
| 市场状态切换 | 中 | 引入 Regime Detection（如 HMM 隐马尔可夫模型） |
| 多策略信号冲突 | 中 | 明确的冲突解决规则（优先级 or 权重投票） |
| 策略代码和配置不同步 | 低 | 版本号绑定，每次信号输出带策略版本号 |

---

## 9. 目录结构（Phase 1 已实现）

```
mytrader/
└── strategy/
    ├── __init__.py          # 自动注册所有内置策略
    ├── base.py              # Signal 数据结构 + SignalDirection 枚举
    ├── registry.py          # @register_strategy 装饰器 + STRATEGY_REGISTRY
    ├── indicators.py        # ✅ 纯函数指标：SMA/EMA/RSI/BB/MACD/ATR/crossed_above/crossed_below
    ├── strategies/
    │   ├── __init__.py
    │   ├── dual_ma.py         # ✅ 双均线交叉
    │   ├── rsi_mean_revert.py # ✅ RSI 超买超卖
    │   ├── bollinger_band.py  # ✅ 布林带均值回归
    │   └── macd_cross.py      # ✅ MACD 信号线交叉
    └── ensemble.py          # ✅ 加权投票聚合（权重自动归一化）
```

## 参考来源

- [VectorBT 策略开发指南](https://vectorbt.dev/api/indicators/factory/)
- *Advances in Financial Machine Learning*, Ch.5 — Fractionally Differentiated Features (de Prado)
- *Algorithmic Trading*, Ch.3 — Mean-Reverting and Momentum Strategies (Ernest Chan)
- [Regime Detection with HMM — Quantopian](https://github.com/quantopian/research_public)
