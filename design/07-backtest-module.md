# Module 07 — Backtest Module（回测模块）

> 上级文档：[00-overview.md](./00-overview.md)  
> 回测框架：VectorBT

---

## 1. 职责

- 在历史数据上模拟策略执行
- 计算策略绩效指标（Sharpe、MaxDD、Calmar 等）
- 支持参数优化（网格搜索 / 随机搜索）
- 生成可视化报告
- 验证策略的回测/实盘一致性

回测模块的核心价值是**在投入真实资金前验证策略**，以及**发现策略的适用范围和边界条件**。

---

## 2. 为什么选 VectorBT

| 特性 | VectorBT | Backtrader | Zipline |
|------|---------|-----------|---------|
| 执行速度 | ⭐⭐⭐⭐⭐ 极快（NumPy向量化） | ⭐⭐⭐ 慢（循环事件驱动） | ⭐⭐⭐ 中等 |
| 参数优化 | 原生支持，一行代码 | 需要外部库 | 不支持 |
| 可视化 | 内置 Plotly 交互图 | 需要 matplotlib | 有限支持 |
| 学习曲线 | 中等 | 较陡 | 陡 |
| 与 pandas 集成 | 原生 | 一般 | 一般 |
| 维护状态 | 活跃 | 较少维护 | 已停止 |

**VectorBT 的核心思想**：将整个回测历史表达为矩阵运算，而不是逐 bar 循环。这使得参数优化可以一次性计算所有参数组合，速度比逐 bar 快 100x 以上。

---

## 3. VectorBT 基本用法

### 3.1 最简单的回测（VectorBT 1.0.0 实际用法）

```python
import vectorbt as vbt
import pandas as pd
from mytrader.data.providers.yfinance_provider import YFinanceProvider
from mytrader.strategy.strategies.dual_ma import dual_ma_signal
from datetime import date

# 1. 获取数据
provider = YFinanceProvider()
df = provider.get_ohlcv("AAPL", date(2022, 1, 1), date(2025, 1, 1))
close = df["close"]

# 2. 调用策略层纯函数生成信号（signal 已内含 shift(1)）
signal = dual_ma_signal(close, fast=10, slow=30)
entries = signal == 1
exits   = signal == -1

# 3. 构建 Portfolio
# ⚠️ vectorbt 1.0.0 的 size_type 用字符串枚举 "Percent"（不是旧版的 "ValuePercent"）
pf = vbt.Portfolio.from_signals(
    close,
    entries=entries,
    exits=exits,
    init_cash=100_000,
    fees=0.001,        # 0.1% 手续费
    slippage=0.001,    # 0.1% 滑点
    size=0.95,
    size_type="Percent",   # 按账户价值百分比下单
    freq="D",
)

# 4. 查看绩效
print(pf.stats())
pf.plot().show()
```

### 3.2 参数优化（网格搜索，当前实现方式）

当前使用逐组合循环，而非 VectorBT 原生矩阵优化（后者在 1.0.0 中 API 有变化）：

```python
# backtest/runner.py — run_optimize()
import itertools

param_grid = {"fast": [5, 10, 15, 20], "slow": [20, 30, 40, 50, 60]}
combinations = list(itertools.product(*param_grid.values()))

rows = []
for combo in combinations:
    params = dict(zip(param_grid.keys(), combo))
    signal = dual_ma_signal(close, **params)
    pf = vbt.Portfolio.from_signals(
        close,
        entries=signal == 1,
        exits=signal == -1,
        init_cash=100_000,
        fees=0.001,
        size=0.95,
        size_type="Percent",
        freq="D",
    )
    stats = pf.stats()
    rows.append({**params, "Sharpe Ratio": stats["Sharpe Ratio"], ...})

result_df = pd.DataFrame(rows).sort_values("Sharpe Ratio", ascending=False)
```

> **待优化**：后续可迁移到 VectorBT 的矩阵化并行优化（`vbt.MA.run_combs`），速度更快，但需适配 1.0.0 API。

---

## 4. 与策略层集成

回测和实盘共用同一套策略函数（关键！）：

```python
# strategy/strategies/dual_ma.py — 策略层纯函数（已实现）
def dual_ma_signal(close: pd.Series, fast: int = 10, slow: int = 30) -> pd.Series:
    """
    这个函数同时被：
    - 回测模块调用（历史数据全量）
    - 实盘策略引擎调用（滚动最新数据）
    """
    fast_ma = sma(close, fast)
    slow_ma = sma(close, slow)
    signal = crossed_above(fast_ma, slow_ma).astype(int) - crossed_below(fast_ma, slow_ma).astype(int)
    return signal.shift(1).fillna(0).astype(int)  # ⚠️ shift(1) 避免前视偏差

# backtest/runner.py — BacktestRunner.run()（已实现）
from mytrader.strategy.registry import STRATEGY_REGISTRY

strategy_fn = STRATEGY_REGISTRY[config.strategy_name]
signal  = strategy_fn(close, **config.strategy_params)
entries = signal == 1
exits   = signal == -1

pf = vbt.Portfolio.from_signals(
    close, entries=entries, exits=exits,
    init_cash=100_000, fees=0.001, slippage=0.001,
    size=0.95, size_type="Percent", freq="D",
)
```

---

## 5. 回测绩效指标

| 指标 | 含义 | 良好参考值 | vectorbt 1.0.0 字段名 |
|------|------|----------|--------------------|
| **Total Return** | 总回报率 | > 基准 | `Total Return [%]` |
| **Benchmark Return** | 买入持有基准收益 | 参考对比 | `Benchmark Return [%]` |
| **Sharpe Ratio** | 风险调整后收益（年化） | > 1.0，> 2.0 优秀 | `Sharpe Ratio` |
| **Max Drawdown** | 最大回撤 | < 20% | `Max Drawdown [%]` |
| **Calmar Ratio** | 年化收益 / 最大回撤 | > 1.0 | `Calmar Ratio` |
| **Win Rate** | 盈利交易占比 | 并不是越高越好，配合 R:R 看 | `Win Rate [%]` |
| **Profit Factor** | 总盈利 / 总亏损 | > 1.5 | `Profit Factor` |
| **Total Trades** | 总交易次数 | 符合策略预期 | `Total Trades` |

> ⚠️ **注意**：vectorbt 1.0.0 的 `pf.stats()` **不包含** `Annualized Return [%]` 字段（旧文档中有，新版本已移除）。年化收益需自行从 Total Return 和 Period 计算，或使用 `Calmar Ratio × Max Drawdown` 反推。

```python
# vectorbt 1.0.0 输出所有指标
print(pf.stats())
# 输出字段包含：Start/End/Period/Start Value/End Value/Total Return [%]/
# Benchmark Return [%]/Max Gross Exposure [%]/Total Fees Paid/
# Max Drawdown [%]/Max Drawdown Duration/Total Trades/Total Closed Trades/
# Total Open Trades/Open Trade PnL/Win Rate [%]/Best Trade [%]/Worst Trade [%]/
# Avg Winning Trade [%]/Avg Losing Trade [%]/Profit Factor/Expectancy/
# Sharpe Ratio/Calmar Ratio/Omega Ratio/Sortino Ratio
```

---

## 6. 回测常见陷阱与防范

### 6.1 前视偏差（Look-ahead Bias）⚠️ 头号风险

**问题**：在 T 日的信号计算中使用了 T 日才能知道的数据（如当天收盘价）

**防范**：
```python
# 强制使用前一 bar 的数据
signal = compute_signal(df).shift(1)  # 永远不要忘记这一行

# VectorBT 中用 from_signals 的 signal_func 参数
pf = vbt.Portfolio.from_signals(..., signal_func=lambda: signal.shift(1))
```

**验证**：对策略做随机化测试，如果随机打乱信号后 Sharpe 仍然很高，说明有前视偏差。

### 6.2 过拟合

**问题**：参数在历史数据上表现极好，但在未来数据上失效

**防范**：
1. **Walk-Forward Analysis（WFA）**：在滚动窗口上重复优化+验证
2. **Out-of-Sample 测试**：留出最近 20% 的数据不参与优化
3. **参数稳定性**：最优参数附近（±20%）的参数也应该有相近表现

```python
# 简单的 Walk-Forward 框架
def walk_forward_test(price: pd.Series, train_months: int = 12, test_months: int = 3):
    results = []
    start = 0
    train_size = train_months * 21  # 约 21 个交易日/月
    test_size  = test_months * 21

    while start + train_size + test_size <= len(price):
        train_data = price.iloc[start : start + train_size]
        test_data  = price.iloc[start + train_size : start + train_size + test_size]

        # 在 train_data 上优化参数
        best_params = optimize_params(train_data)

        # 在 test_data 上验证
        test_result = run_backtest(test_data, **best_params)
        results.append(test_result.sharpe_ratio())

        start += test_size  # 滚动

    return results
```

### 6.3 幸存者偏差

**问题**：只用当前还在市场上的股票回测，排除了已退市的公司，导致结果虚高

**防范**：
- 使用包含退市公司的历史数据（Polygon.io 等数据源支持）
- 对于个股精选策略，这个问题比较严重

### 6.4 交易成本低估

**问题**：回测中假设 0 成本或极低成本，实际执行差距大

**防范**：
- 设置保守的手续费（0.1%）和滑点（0.1%）
- 对于低频策略（每月几次），这影响不大
- 对于高频策略，每次成本叠加会吞掉大部分利润

### 6.5 流动性假设

**问题**：假设所有订单都能在目标价格成交

**防范**：
- 设置成交量限制：单日成交量不超过该股票日均成交量的 5%
- vectorbt 1.0.0 中通过 `size_type="Percent"` + `size=0.95` 控制单次下单比例

---

## 7. 报告输出

```python
class BacktestReport:
    def generate(self, result: BacktestResult, name: str | None = None) -> Path:
        pf = result.portfolio

        # 1. 统计摘要 CSV
        result.stats.to_csv(f"{report_dir}/stats.csv", header=["value"])

        # 2. 逐笔交易记录 CSV
        pf.trades.records_readable.to_csv(f"{report_dir}/trades.csv", index=False)

        # 3. 权益曲线 HTML（vectorbt 1.0.0 返回 plotly Figure，需用 .write_html()）
        pf.plot().write_html(f"{report_dir}/equity_curve.html")

        # 4. 回撤分析 HTML
        pf.drawdowns.plot().write_html(f"{report_dir}/drawdowns.html")
```

---

## 8. 目录结构（Phase 1 已实现）

```
mytrader/
└── backtest/
    ├── __init__.py
    ├── runner.py          # ✅ BacktestRunner（单次回测）+ BacktestConfig/BacktestResult
    │                      #    run_optimize()：网格搜索参数优化（逐组合循环）
    └── report.py          # ✅ BacktestReport：生成 stats.csv / trades.csv / equity_curve.html / drawdowns.html
    # optimizer.py         # 待实现：Walk-Forward Analysis
    # metrics.py           # 待实现：自定义指标（年化收益等）
    # validators.py        # 待实现：前视偏差自动检测
```

---

## 9. 注意点

- VectorBT 1.0.0 的 `size_type` 枚举值为 `"Percent"`（旧版 `"ValuePercent"` 已不支持），其他值：`"Amount"`、`"Value"`、`"TargetPercent"` 等
- VectorBT 默认假设信号在收盘价执行，实盘一般在**下一根 bar 的开盘价**执行，需传 `open=open_series` 给 `from_signals()`
- vectorbt 1.0.0 `pf.stats()` 不再包含 `Annualized Return [%]`，需自行计算
- 参数优化时注意内存占用；当前逐组合循环方式对大参数空间较慢，后续可考虑迁移到 VectorBT 矩阵化优化
- `pf.plot()` 返回 plotly Figure 对象，需用 `.write_html()` 保存，不能直接 `.show()` 在无 GUI 服务器上

---

## 参考来源

- [VectorBT 官方文档](https://vectorbt.dev/)
- [VectorBT Portfolio.from_signals](https://vectorbt.dev/api/portfolio/base/#vectorbt.portfolio.base.Portfolio.from_signals)
- *Advances in Financial Machine Learning*, Ch.7 — Cross-Validation in Finance (de Prado)
- *Advances in Financial Machine Learning*, Ch.11 — The Sharpe Ratio (de Prado)
- [Backtesting Pitfalls — QuantStart](https://www.quantstart.com/articles/avoiding-look-ahead-bias-in-backtests-with-python/)
- [Walk-Forward Optimization — Quantopian](https://github.com/quantopian/research_public)
