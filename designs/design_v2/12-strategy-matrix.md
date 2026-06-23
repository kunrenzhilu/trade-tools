# Module 12 — Strategy Matrix Runner（策略矩阵运行器）

> 上级文档：[00-overview.md](./00-overview.md)  
> Phase 5 新增模块

---

## 1. 职责

- 对标的池中的每只标的，运行其**所属组分配的策略**
- 支持**多策略并行**（一只标的可被多个策略评估）
- 读取 `strategy_weights.json`，按 `group_id` 决定每只标的用哪些策略及权重
- 输出带 `strategy_name` + `confidence` + `group_id` 的 Signal 列表，供 Signal Ranker 排名

> v1 只用全局 1 个策略；v2 让"标的所属组 → 该组最优策略集"由回测结果驱动。

---

## 2. 在数据流中的位置

```
Universe Manager.get_groups()
        ↓ {group_id: [symbols]}
Strategy Matrix Runner
   读 strategy_weights.json：{group_id: [(strategy, params, weight), ...]}
        ↓
   for each symbol:
       group = meta.group_id
       for (strategy, params, weight) in weights[group]:
           signal = strategy_fn(close, **params)
           → Signal(symbol, strategy_name, confidence=f(signal, weight), group_id)
        ↓ M×N 条 Signal
Signal Ranker
```

---

## 3. strategy_weights.json 结构

由离线 MatrixBacktest 产出（详见 [07-backtest-module.md](./07-backtest-module.md)）：

```json
{
  "_meta": {
    "generated_at": "2026-06-23T00:00:00Z",
    "backtest_window": "2021-06-01 ~ 2026-06-01",
    "reoptimize_freq": "monthly"
  },
  "groups": {
    "NDX_high_vol": [
      {"strategy": "dual_ma", "params": {"fast": 5, "slow": 60}, "weight": 0.6,
       "backtest_sharpe": 1.42, "backtest_win_rate": 0.58},
      {"strategy": "macd", "params": {"fast": 12, "slow": 26, "signal": 9}, "weight": 0.4,
       "backtest_sharpe": 1.18, "backtest_win_rate": 0.55}
    ],
    "SPX_low_vol": [
      {"strategy": "rsi", "params": {"period": 14, "oversold": 30, "overbought": 70}, "weight": 0.7,
       "backtest_sharpe": 1.05, "backtest_win_rate": 0.62},
      {"strategy": "bollinger", "params": {"period": 20, "std_dev": 2.0}, "weight": 0.3,
       "backtest_sharpe": 0.92, "backtest_win_rate": 0.60}
    ]
  }
}
```

> 关键字段：
> - `weight`：该策略在组内的权重（组合本身是被回测过的，权重来自回测优化）
> - `backtest_sharpe` / `backtest_win_rate`：供 Signal Ranker 计算综合得分

---

## 4. "组合即策略" 的实现

用户洞察：**策略组合本身就是一个策略，因此权重应被回测验证**。

实现方式：

```
MatrixBacktest 阶段（离线）：
  对每个 group：
    1. 单独回测组内每个候选策略 → 得到各自 Sharpe
    2. 用 ensemble_signal() 回测加权组合（搜索最优权重）
       ⚠️ ensemble 权重优化必须在与实盘相同的"单点离散值聚合"语义下进行：
          - 每根 bar 各策略产出离散值（1/-1/0）
          - 加权投票：combined = Σ(signal_i × weight_i)
          - combined > +threshold → BUY，< -threshold → SELL，否则 HOLD
          - 在此逻辑序列上运行回测，优化 weight 使组合 Sharpe 最大
          不能用"时间序列整体加权"再取均值，因为实盘只取 iloc[-1]
    3. 若组合 Sharpe > 单策略最优 → 采用组合权重
    4. 否则 → 退化为单策略（weight=1.0）
  → 写入 strategy_weights.json

Strategy Matrix Runner 阶段（实盘）：
  直接读取回测验证过的权重，不在实盘临时计算
```

> 复用 Phase 1 已实现的 `ensemble.py::ensemble_signal()`（加权投票，权重归一化）。
> 区别：v1 权重是手填的，v2 权重来自回测优化。
> **一致性保证**：离线优化与在线执行均使用"单点离散值加权投票"语义，回测验证与实盘执行等价。

---

## 5. 模块接口设计

```python
@dataclass
class MatrixScanResult:
    """单次矩阵扫描结果。"""
    signals: list[Signal]           # 所有产生的信号
    symbol_count: int
    strategy_runs: int              # 总策略运行次数 = Σ(每只的策略数)
    errors: dict[str, str]          # {symbol: error}


class StrategyMatrixRunner:
    """策略矩阵运行器。"""

    def __init__(self, store: MarketDataStore,
                 universe: UniverseManager,
                 weights_file: str = "config/strategy_weights.json") -> None: ...

    def run(self, lookback_days: int = 90,
            max_workers: int = 8) -> MatrixScanResult:
        """对全标的池运行各自分组的策略，输出信号列表。"""

    def run_symbol(self, symbol: str, lookback_days: int = 90) -> list[Signal]:
        """运行单只标的的所有分配策略。"""

    def reload_weights(self) -> None:
        """热加载 strategy_weights.json（每月更新后无需重启）。"""
```

---

## 6. 单标的运行流程

```python
def run_symbol(symbol, lookback_days=90):
    meta = universe.get_symbol_meta(symbol)
    group_strategies = weights["groups"].get(meta.group_id, [])
    if not group_strategies:
        return []   # 该组无分配策略，跳过

    df = store.get_latest_n_bars(symbol, n=lookback_days)   # 读本地库
    signals = []
    for entry in group_strategies:
        strategy_fn = STRATEGY_REGISTRY[entry["strategy"]]
        # ⚠️ 传入完整 df（部分策略需要 high/low/volume），同时传 df["close"] 保持签名兼容
        sig_series = strategy_fn(df["close"], df=df, **entry["params"])

        # ⚠️ 信号有效期处理（解决事件型信号漏单问题）
        # 策略信号是事件型：交叉/突破瞬间=1/-1，其余=0
        # 只看 iloc[-1] 会漏掉趋势中段——金叉在 3 天前，今天 signal=0 但趋势仍在
        # 方案：检查最近 N_SIGNAL_VALID_BARS 内是否出现过非零信号（N 可配置，默认 3）
        n_valid = config.signal_valid_bars  # 默认 3
        recent_signals = sig_series.iloc[-n_valid:]
        nonzero = recent_signals[recent_signals != 0]
        if nonzero.empty:
            continue   # 最近 N bar 内无信号，跳过
        latest = int(nonzero.iloc[-1])   # 取最近一次有效信号方向

        signals.append(Signal(
            symbol=symbol,
            direction=BUY if latest == 1 else SELL,
            strategy_name=entry["strategy"],
            confidence=entry["weight"] * base_confidence,   # 权重影响置信度
            group_id=meta.group_id,
            indicators={"backtest_sharpe": entry["backtest_sharpe"],
                        "backtest_win_rate": entry["backtest_win_rate"]},
        ))
    return signals
```

> **信号有效期说明**：`signal_valid_bars=3` 表示信号在发出后 3 个交易日内仍有效。
> 这与"持仓 1-5 天"的策略定位匹配：金叉信号 3 天前发出，趋势一般仍在延续，应允许入场。
> 若担心追高，可将 N 调小（N=1 即退回到只看最后一根 bar 的严格模式）。

---

## 7. 并发设计

```
550 只标的 × 平均 2 策略 = ~1100 次策略运行
全部读本地库（无网络）→ CPU 密集
→ 用线程池/进程池并发（max_workers=8）

预估：单只标的的指标计算 ~5ms × 550 / 8 workers ≈ 0.4 秒
→ 整个矩阵扫描亚秒级完成 ✅
```

> 因为数据来自本地库（Module 10），无网络 IO，矩阵扫描可在秒级完成。
> 这正是 v2 引入本地库的价值——大规模扫描才可行。

---

## 8. 注意点

### 8.1 同一标的多策略冲突
- 一只标的可能同时收到 dual_ma BUY + macd SELL（策略分歧）
- **本模块不解决冲突**，原样输出所有信号
- 冲突解决交给 Signal Ranker（按权重综合，或要求多数同向）

### 8.2 权重热加载
- 每月 MatrixBacktest 更新 strategy_weights.json 后
- Runner 通过 `reload_weights()` 热加载，无需重启系统

### 8.3 策略未注册
- weights.json 引用的策略必须已在 STRATEGY_REGISTRY 注册
- 加载时校验，缺失则告警并跳过该策略

---

## 9. 风险点

| 风险 | 级别 | 缓解措施 |
|------|------|---------|
| 权重文件与注册表不同步 | 中 | 加载时校验策略存在性 |
| 多策略信号冲突 | 中 | 交由 Signal Ranker 按权重综合 |
| 并发计算资源占用 | 低 | max_workers 限流 |

---

## 10. 目录结构（Phase 5 待实现）

```
mytrader/
└── strategy/
    ├── matrix_runner.py        # StrategyMatrixRunner（Phase 5 新增）
    ├── ensemble.py             # ✅ 复用：ensemble_signal（权重来自回测）
    ├── registry.py             # ✅ 复用
    └── strategies/             # ✅ 复用：已有 4 策略
config/
└── strategy_weights.json      # MatrixBacktest 产出，Runner 读取
```

---

## 参考来源

- *Advances in Financial Machine Learning*, Ch.6 — Ensemble Methods (de Prado)
- [VectorBT 多列向量化](https://vectorbt.dev/api/indicators/factory/)
