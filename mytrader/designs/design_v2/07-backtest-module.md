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
- **（v2 新增）矩阵回测：N 策略 × G 标的组 × 参数网格 → 产出 strategy_weights.json**

回测模块的核心价值是**在投入真实资金前验证策略**，以及**发现策略的适用范围和边界条件**。

> **v2 重大变化**：v1 只在单标的（AAPL）上回测单策略。
> v2 引入**矩阵回测**——在标的分组上批量回测多策略多参数，
> 自动产出"每组最优策略 + 权重"，作为实盘选股的依据（详见第 10 节）。
> 回测数据从 MarketDataStore 本地库读取（DuckDB 列式），回测窗口 **5 年**（覆盖完整牛熊周期）。

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
    open=open_series,  # ⚠️ 必须传入：信号在下一根 bar 的开盘价执行，与实盘保持一致
    entries=entries,
    exits=exits,
    init_cash=100_000,
    fees=0.001,        # 0.1%——Alpaca 零佣金，保留此项模拟潜在市场冲击（保守估计）
    slippage=0.001,    # 0.1%——对 mid-cap 或流动性较差标的可调高至 0.002
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
    open=open_series,    # ⚠️ 信号在下一根 bar 开盘价执行，回测/实盘一致
    init_cash=100_000, fees=0.001, slippage=0.001,
    size=0.95, size_type="Percent", freq="D",
)

# ⚠️ BacktestResult 须包含 daily_returns，供矩阵回测等权组合 Sharpe 计算
# daily_returns = pf.returns()  →  传入 run_matrix_backtest() 合并组合序列
```
```

---

## 5. 回测绩效指标

| 指标 | 含义 | 良好参考值 | vectorbt 1.0.0 字段名 |
|------|------|----------|--------------------|
| **Total Return** | 总回报率 | > 基准 | `Total Return [%]` |
| **Benchmark Return** | 买入持有基准收益 | 参考对比 | `Benchmark Return [%]` |
| **Sharpe Ratio** | 风险调整后收益（年化） | > 1.0，> 2.0 优秀 | `Sharpe Ratio` |
| **Sortino Ratio** ⭐ | 下行风险调整后收益（**Constitution L1 首要 KPI**） | > 1.5，> 2.5 优秀 | `Sortino Ratio`（矩阵回测中手算，见 §10.4） |
| **Max Drawdown** | 最大回撤 | < 20% | `Max Drawdown [%]` |
| **Calmar Ratio** | 年化收益 / 最大回撤 | > 1.0 | `Calmar Ratio` |
| **Win Rate** | 盈利交易占比 | 并不是越高越好，配合 R:R 看 | `Win Rate [%]` |
| **Profit Factor** | 总盈利 / 总亏损 | > 1.5 | `Profit Factor` |
| **Total Trades** | 总交易次数 | 符合策略预期 | `Total Trades` |

> ⚠️ **注意**：vectorbt 1.0.0 的 `pf.stats()` **不包含** `Annualized Return [%]` 字段（旧文档中有，新版本已移除）。年化收益需自行从 Total Return 和 Period 计算，或使用 `Calmar Ratio × Max Drawdown` 反推。
>
> ⚠️ **Sortino 计算口径（迭代 #1 确认）**：
> - 单标的层面：vectorbt 1.0.0 `pf.stats()` 含 `Sortino Ratio`，可直接读取
> - 矩阵回测层面（**组组合 Sortino**）：**必须手算**，因为 Sortino 是比率不可直接平均。正确做法是等权合并组内日收益率序列，再算下行偏差。`matrix_backtest.py::_compute_sortino()` 实现此公式，与 `_compute_sharpe()` 同口径（target=0、年化因子 252、退化返回 0.0）。这样保证单标的/组合口径一致，且不依赖 vectorbt stats 键名（曾发生 `Annualized Return [%]` 被移除的破坏性变更）。

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
- **⚠️ 必须传 `open=open_series`**：VectorBT 默认假设信号在收盘价执行，实盘在**下一根 bar 的开盘价**执行。矩阵回测和单标的回测均须传入 `open` 列，否则回测/实盘不一致
- vectorbt 1.0.0 `pf.stats()` 不再包含 `Annualized Return [%]`，需自行计算
- 参数优化时注意内存占用；当前逐组合循环方式对大参数空间较慢，后续可考虑迁移到 VectorBT 矩阵化优化
- `pf.plot()` 返回 plotly Figure 对象，需用 `.write_html()` 保存，不能直接 `.show()` 在无 GUI 服务器上

---

## 10. 矩阵回测（MatrixBacktest，v2 新增）

> 这是 v2 的核心新增能力：把"单标的单策略回测"升级为"分组多策略矩阵回测"，
> 自动产出实盘选股所需的 `strategy_weights.json`。

### 10.1 目标

```
输入：N 个策略 × G 个标的组 × 参数网格 × 5 年历史数据
输出：strategy_weights.json
      每组保留 Top-K 策略 + 最优参数 + 组合权重 + 回测指标
```

### 10.2 回测窗口：为什么是 5 年

```
✗ 90 天 → 只覆盖一种行情，回测毫无统计意义
✓ 5 年  → 覆盖重要的市场周期（当前窗口约 2021-06 ~ 2026-06）：
          2021-22 通胀收紧 + 2022 熊市 + 2023-24 复苏 + 2025-26 行情
          注：2020-03 崩盘不在此窗口内；如需覆盖，须扩展至 6 年（2020-06 起）
✗ 15 年 → 太老的数据市场结构已变（HFT 占比、做市行为不同），相关性低

→ 5 年是"覆盖完整周期"与"保持市场结构相关性"的平衡点
```

### 10.3 矩阵回测流程

```python
def run_matrix_backtest(universe: UniverseManager,
                        store: MarketDataStore,
                        strategies: list[str],
                        param_grids: dict,
                        years: int = 5) -> dict:
    weights = {"groups": {}}
    groups = universe.get_groups()              # {group_id: [symbols]}

    for group_id, symbols in groups.items():
        # 1. 读该组所有标的的 5 年数据（DuckDB 列式）
        data = store.get_bars_multi(symbols, start=today - years*365, end=today)

        # 2. 对每个策略 × 每组参数，在组内所有标的上回测
        #    ⚠️ 不能直接取 Sharpe 算术平均（Sharpe 是比率，直接平均无统计意义）
        #    正确做法：将组内所有标的日收益率等权合并为组合序列，计算组合 Sharpe
        candidates = []
        for strategy in strategies:
            for params in grid_combinations(param_grids[strategy]):
                results = [backtest_one(data[s], strategy, params) for s in symbols]
                # 等权合并日收益率序列 → 计算组合 Sharpe
                returns_df = pd.concat([r.daily_returns for r in results], axis=1)
                portfolio_returns = returns_df.mean(axis=1)
                portfolio_sharpe = compute_sharpe(portfolio_returns)
                candidates.append((strategy, params, portfolio_sharpe))

        # 3. 每个策略保留其最优参数，按 avg_sharpe 排序，取 Top-K 策略
        top_strategies = select_top_per_strategy(candidates, k=2)

        # 4. 搜索组合权重（ensemble），若组合 Sharpe > 单策略最优则采用组合
        weighted = optimize_ensemble_weights(top_strategies, data, symbols)

        weights["groups"][group_id] = weighted

    return weights
```

### 10.4 关键设计点

| 设计点 | 做法 | 理由 |
|--------|------|------|
| **组内取平均** | 等权合并组内日收益率序列，计算组合 Sharpe（而非直接平均各标的 Sharpe 比率） | 避免单只过拟合；Sharpe 是比率，不能直接平均；需要组合视角 |
| **组合 Sortino**（迭代 #1 新增） | 与组合 Sharpe 同口径：等权合并日收益率 → `_compute_sortino(combined)` | Constitution L1 首要 KPI；比率不可直接平均；与 Sharpe 同口径保证可比 |
| **组合 Max Drawdown**（迭代 #2 新增） | 等权合并组内日收益率 → cumprod → cummax → drawdown → max，返回正百分数 | Constitution L1 DD≤20% 硬约束；DD 是路径依赖比率不可直接平均；per-stock avg DD 虚高（无分散化效应） |
| **NaN 安全处理**（迭代 #2 新增） | `_safe_float()` 拦截 NaN/None/Inf；`_safe_mean()` 拦截空列表/全 NaN | vectorbt 无交易时 stats 返回 NaN；`NaN or 0.0` 仍为 NaN（NaN 是 truthy）导致 JSON 序列化失败 |
| **策略名校验**（迭代 #1 新增） | `_run_group` 进入策略循环前检查 `strategy not in STRATEGY_REGISTRY` → `logger.warning` + `continue` | 防止策略名拼写错误被静默跳过（迭代 #1 修复的 bug：`main.py` 误用 `"rsi"/"macd"/"bollinger"` 简称导致 3 个策略 6 天未跑） |
| **DD 硬约束 + Fallback**（迭代 #3 新增） | top-K 选择时过滤 `portfolio_max_drawdown > 20%` 的候选；若全部超标 → 按 DD 升序取 top-K，标记 `dd_constrained=True` | Constitution L1 DD≤20% 是硬约束；无合规候选时仍需产出权重（结构性问题不能阻塞回测） |
| **Alpha 排序 + Sortino 门槛**（迭代 #9 新增） | top-K 排序从 Sortino 改为 Alpha（策略年化收益 - SPY 同期年化收益）；新增 `Sortino > 0.5` 最低质量门槛 | Sortino 高 ≠ 年化高（均值回归策略天然高 Sortino 低绝对收益，alpha 为负）；Alpha 排序直接优化超额收益目标；Sortino 门槛保证基本下行质量。三级 fallback：Tier 1 DD+Sortino → Tier 2 仅 DD → Tier 3 DD 升序 |
| **SPY Benchmark 获取**（迭代 #9 新增） | `_get_spy_returns(start, end)` 从 MarketDataStore 拉取 SPY 日收益率；`_compute_alpha(strat, spy)` 计算年化 alpha | SPY 不可用时 alpha 降级为 0.0（不阻塞回测），所有候选 alpha=0 ��退化为原顺序 |
| **per-strategy best params 用 Alpha**（迭代 #9 新增） | 每个策略的最优参数选择从 Sharpe 改为 Alpha | 与 top-K 排序口径一致，避免 per-strategy 用 Sharpe 选低收益高稳定的参数 |
| **ensemble weights 用 Alpha**（迭代 #9 新增） | `_optimize_ensemble_weights` 接收 `spy_returns` 参数，权重计算从 Sharpe 改为 Alpha | 与 top-K 排序口径一致，ensemble 权重直接反映"跑赢 SPY 的程度"；SPY 不可用时退化为等权 |
| **健全性门槛（Reject Degenerate）**（迭代 #11 新增） | `SingleBacktestResult.closed_trades` 字段 + `_is_degenerate_strategy()` 函数；`_run_group` 在 candidates 构建前剔除 `>= 80%` 标的 `closed_trades==0` 的退化策略；全退化组返回空权重 + `no_valid_strategy=True` 标记 | 退化策略（入场/出场条件互斥，如 Iter #8 `rsi_trend_filter`）仓位靠末尾强平凑出 Sortino/alpha 假象，会骗过 alpha 排序进入权重（Iter #10 实测 alpha=-25%）。`closed_trades` 区分"真交易闭环"与"伪 buy-and-hold"。0.8 阈值保守，只拦"近乎全标的零平仓"，不误伤低频合法策略。`experience.md #8`：sanity → risk → rank，排序前必须先过硬门槛 |
| **参数按组** | 同组共用参数，不对单只优化 | 防过拟合（详见 02-strategy-engine.md 6.3） |
| **历史分组对齐** | 矩阵回测使用 point-in-time 分组（按回测时间点重算波动率），而非当前静态分组 | 避免回测静态分组而实盘动态分组导致回测/实盘不一致 |
| **实盘 ensemble 对齐** | MatrixBacktest 的 ensemble 权重优化须在"单点离散值聚合"语义下验证 | 实盘只取 iloc[-1] 单点离散值加权，与序列级加权不等价，权重必须在相同语义下产出 |
| **Walk-Forward** | 滚动训练窗口，月度重优化 | 平衡过拟合与适应性 |

### 10.4.1 Top-K 选择三级 Fallback（迭代 #9 新增，迭代 #11 前置健全性门槛，迭代 #12 前置 alpha>0 门槛）

```
[迭代 #11 前置] 健全性过滤：剔除 closed_trades==0 比例 ≥ 80% 的退化策略
                全退化组 → 空权重 + no_valid_strategy=True（hold cash）
                    ↓
[迭代 #12 前置] alpha>0 硬门槛：剔除 alpha≤0 的候选（跑不赢 SPY 的策略不进权重）
                全负 alpha 组 → 空权重 + no_positive_alpha=True（hold cash）
                    ↓
Tier 1: DD ≤ 20% AND Sortino > 0.5  →  Alpha 降序取 top-K
   ↓ (若空)
Tier 2: DD ≤ 20%（放宽 Sortino）   →  Alpha 降序取 top-K，WARNING 日志
   ↓ (若空)
Tier 3: 无 DD 合规候选              →  DD 升序取 top-K，dd_constrained=True
```

**迭代 #11 健全性门槛（先于 alpha>0 门槛）**：
- `SingleBacktestResult.closed_trades` 字段从 vbt `pf.trades.closed.count()` 提取（区分"真交易闭环"与"末尾强平计 1 笔的伪 buy-and-hold"）
- 退化定义：组内 `closed_trades==0` 的标的比例 ≥ `DEGENERATE_NO_CLOSE_FRACTION (0.8)`
- 全退化组返回空权重（持仓现金），不强行选退化策略；标记 `GroupBacktestResult.no_valid_strategy=True`
- 设计动机（`experience.md #8`）：Iter #10 `rsi_trend_filter` 凭"持仓盯市 + 末尾强平"的 Sortino/alpha 假象骗过 alpha 排序进入 4/6 组权重 → 组合 alpha=-25.26%。`closed_trades` 信号缺失时无健全性门槛可拦住整个灾难。0.8 阈值保守，低频合法策略（每标的 2-3 笔）不会被误伤

**迭代 #12 alpha>0 硬门槛（健全性之后、Tier 1/2/3 之前）**：
- 在 candidates 构建后、Tier 1/2/3 fallback 之前，剔除 `alpha≤0` 的候选
- 全负 alpha 组返回空权重（持仓现金），标记 `GroupBacktestResult.no_positive_alpha=True`
- `_optimize_ensemble_weights` 修负 alpha 归一化 bug：旧代码 `max(alpha, 0.01)` 把负 alpha 掩盖成 0.01 → 等权；新代码 `max(alpha, 0.0)` → 负 alpha 权重为 0，只有正 alpha 参与归一化
- 设计动机（`experience.md #8`：`sanity → risk → positive alpha → rank`）：Iter #11 健全性门槛修复了退化策略，但 11 条权重中 9 条负 alpha → 组合 alpha=-21.41%。alpha>0 门槛确保只有跑赢 SPY 的策略进权重。全负 alpha 组空仓（hold cash），不"矬子里拔将军"

**设计动机**（iteration #9 spec §1-2）：
- Constitution 目标：年化 20-30%（需 alpha +10~20%）
- 旧逻辑：Sortino 降序 → 永远选均值回归策略 → 年化 8.02%，alpha = -11.34%
- 新逻辑：Alpha 降序 → 直接优化超额收益目标
- Sortino 门槛：避免选到"高 alpha 但高下行波动"的垃圾策略

**Alpha 计算公式**：
```python
strat_annual = (1 + strat_returns.mean()) ** 252 - 1
spy_annual   = (1 + spy_returns.mean()) ** 252 - 1
alpha_pct    = (strat_annual - spy_annual) * 100
```

**降级处理**：SPY 数据不可用 → alpha=0.0，所有候选 alpha 相等，
Python 稳定排序保留原顺序（按策略列表顺序）。


### 10.5 Walk-Forward 月度重优化

```
训练窗口 5 年 → 优化权重 → 应用 1 个月（样本外）→ 滚动前移 → 重新优化

调度（APScheduler）：
  每月第一个交易日 00:00 触发 run_matrix_backtest()
  → 更新 strategy_weights.json
  → StrategyMatrixRunner.reload_weights() 热加载
```

为什么是月度（设计访谈确认）：

```
更新太频繁（每天）→ 拟合近期噪音，权重翻转，策略左右打脸
更新太慢（每年）  → 行情切换时反应迟钝
每月 ≈ 21 交易日  → 足够样本外数据验证上轮权重，换手率可控
```

**窗口重叠率讨论：**

```
当前方案：训练 5 年 + 步进 1 个月 → 重叠率 = 59/60 ≈ 98.3%
→ 权重变化缓慢（惯性大），但保证了统计稳健性
→ 代价：市场突变时（如 2022 熊市初期）权重适应较慢

改进方向（Phase 5 后续可选）：
  方案 A：缩短训练窗口至 2-3 年，降低重叠率 → 适应性更强，但统计样本减少
  方案 B：时间衰减权重（指数衰减 λ≈0.97/天）→ 近期数据权重更高，
           等效训练窗口约 1-1.5 年，无需改变窗口长度
  方案 C：双窗口验证：短窗口（1年）+ 长窗口（5年）权重取交集，兼顾适应性与稳健性
```

### 10.6 输出文件

```
config/strategy_weights.json   # StrategyMatrixRunner 实盘读取
reports/matrix_backtest/        # 每次矩阵回测的详细报告（各组各策略指标）
    {date}/
        group_summary.csv       # 各组 Top 策略对比
        {group_id}_detail.csv   # 单组各策略各参数明细
```

#### strategy_weights.json 字段说明

```json
{
  "strategy": "rsi_mean_revert",
  "params": {"period": 14, "oversold": 30, "overbought": 70},
  "weight": 0.5,
  "backtest_sharpe": 1.03,
  "backtest_sortino": 1.61,
  "backtest_max_drawdown": 1.78,
  "backtest_win_rate": 0.50,
  "backtest_alpha": 2.35,         // 迭代 #9 新增：vs SPY 的超额年化收益（百分数）
  "dd_constrained": false,
  "backtest_dd_status": "pass"
}
```

### 10.7 性能考量

```
N 策略(4) × 参数网格(~20) × G 组(假设 9 组) × 组内标的(~60)
= 4 × 20 × 9 × 60 = ~43,200 次单标的回测

VectorBT 向量化 + DuckDB 列式读取：
  单次回测 ~10ms → 43,200 × 10ms ≈ 7 分钟
→ 月度离线跑，7 分钟完全可接受
```

---

## 参考来源

- [VectorBT 官方文档](https://vectorbt.dev/)
- [VectorBT Portfolio.from_signals](https://vectorbt.dev/api/portfolio/base/#vectorbt.portfolio.base.Portfolio.from_signals)
- [DuckDB 文档](https://duckdb.org/docs/)
- *Advances in Financial Machine Learning*, Ch.7 — Cross-Validation in Finance (de Prado)
- *Advances in Financial Machine Learning*, Ch.11 — The Sharpe Ratio (de Prado)
- [Backtesting Pitfalls — QuantStart](https://www.quantstart.com/articles/avoiding-look-ahead-bias-in-backtests-with-python/)
- [Walk-Forward Optimization — Quantopian](https://github.com/quantopian/research_public)

