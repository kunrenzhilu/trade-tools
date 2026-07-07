# Iteration #7 Spec — SignalRanker Sortino Priority + Benchmark Comparison

> 日期：2026-07-04  
> Meta-Agent：GLM  
> 输入依据：`iterations/iteration_5/summary.md`、`iterations/iteration_6/summary.md`、`alignment/ai_constitution.md` L1（Sortino 首要 KPI）、`mytrader/mytrader/signal/ranker.py`、`mytrader/mytrader/backtest/portfolio_backtest.py`  
> 风险等级：中（修改信号评分逻辑，但不修改风控参数、DD 阈值、仓位上限、下单逻辑）  
> 核心目标：将 SignalRanker 评分从 Sharpe 切换为 Sortino（Constitution L1 首要 KPI），并为 PortfolioBacktest 加入 SPY benchmark 对比，使收益可归因。

---

## 1. 背景

当前系统状态（Iteration #6 后）：

| 指标 | 当前值 | 目标 | Gap |
|------|--------|------|-----|
| Sortino | 1.98 | > 2.0 | -1% |
| Annual Return | 15.17% | 20-30% | -5pp |
| Max DD | 6.65% | ≤ 20% | ✅ |
| Walk-Forward | 4/4 pass | 4/4 | ✅ |

关键发现：

1. **SignalRanker 仍用 `backtest_sharpe` 评分**（`ranker.py:202`），而 Constitution L1 明确 Sortino 是首要 KPI。Iter #5 已为 signal indicators 添加了 `backtest_sortino` 字段，但 ranker 没有使用它。
2. **无 benchmark 对比**：PortfolioBacktest 只计算组合自身指标，不知道 15.17% 年化是跑赢还是跑输 SPY。如果 SPY 同期涨 25%，则策略实际在损失 alpha。
3. **均值回归主导**：当前权重中 rsi_mean_revert 和 bollinger_band 占绝大多数，趋势/动量策略（dual_ma, macd_cross）几乎缺席。这在趋势市中是结构性弱点。

本次迭代聚焦前两个问题（评分切换 + benchmark），第三个（策略多样性）留待后续。

---

## 2. Problem Statement

### P0：SignalRanker 评分未使用 Sortino

`ranker.py::_score()` 当前评分因子：

```python
factors = {
    "strategy_weight":   float(ind.get("weight", 0.5)),       # 0.35
    "signal_confidence": float(signal.confidence),             # 0.25
    "backtest_win_rate": float(ind.get("backtest_win_rate", 0.5)),  # 0.20
    "backtest_sharpe":   min(float(ind.get("backtest_sharpe", 0.0)) / 3.0, 1.0),  # 0.20
}
```

问题：
- `backtest_sharpe` 用 Sharpe Ratio 排名，而 Constitution L1 要求 Sortino 优先
- signal indicators 已包含 `backtest_sortino`（Iter #5 添加），但 ranker 未读取
- 缺少下行风险惩罚（`backtest_max_drawdown` 也在 indicators 中但未被使用）

### P1：PortfolioBacktest 无 benchmark 对比

`PortfolioBacktestResult` 只有组合自身指标，缺少：
- SPY buy-and-hold 同期收益
- Alpha（超额收益 = 组合收益 - benchmark 收益）
- Benchmark Sortino / Max DD
- 信息比率（Information Ratio）

无法判断 15.17% 年化是 alpha 还是 beta。

---

## 3. Scope

### 本次要做

1. **SignalRanker 评分切换**：
   - 将 `backtest_sharpe` 因子替换为 `backtest_sortino`（归一化方式：`min(sortino / 3.0, 1.0)`）
   - 新增 `backtest_max_drawdown` 作为风险惩罚因子（归一化：`max(1.0 - dd / 20.0, 0.0)`，DD 越低分越高）
   - 调整 `DEFAULT_SCORE_WEIGHTS` 权重分配
   - 保持向后兼容：旧的 `score_weights` 参数仍可传入自定义权重

2. **PortfolioBacktest benchmark 对比**：
   - 在 `PortfolioBacktestResult` 新增 benchmark 字段
   - 在 `PortfolioBacktester.run()` 中拉取 SPY 同期数据并计算 buy-and-hold 指标
   - 计算 alpha 和信息比率

3. **测试与验证**：
   - 更新 SignalRanker 测试覆盖 Sortino 因子
   - 新增 PortfolioBacktest benchmark 测试
   - 运行默认 pytest 确认无回归

4. **更新文档**：
   - `designs/design_v2/13-signal-ranker.md` — 评分因子更新
   - `alignment/iteration_trajectory.md` — 迭代记录
   - `.codebuddy/CODEBUDDY.md` — 如有结构变化

### 本次不做

1. 不新增策略（海龟、WorldQuant Alpha101 等留后续）
2. 不修改 DD 20% 阈值、仓位上限、止损止盈
3. 不修改 CandidateSelector 约束逻辑
4. 不修改 AlpacaBroker 下单逻辑
5. 不运行 `--reoptimize`（耗时 18min+，由 Meta-Agent 在验收阶段独立运行）
6. 不触发真实交易

---

## 4. Detailed Design

## 4.1 SignalRanker 评分切换

### 修改文件

- `mytrader/mytrader/signal/ranker.py`
- `mytrader/tests/test_strategy_matrix_ranker.py`

### 新的 DEFAULT_SCORE_WEIGHTS

```python
DEFAULT_SCORE_WEIGHTS = {
    "strategy_weight":      0.30,
    "signal_confidence":    0.20,
    "backtest_win_rate":    0.15,
    "backtest_sortino":     0.25,   # ← 替换 backtest_sharpe，权重提高（Constitution L1 首要 KPI）
    "backtest_dd_penalty":  0.10,   # ← 新增：DD 越低分越高
}
```

设计理由：
- Sortino 权重 0.25（最高单因子），体现 Constitution L1 优先级
- DD 惩罚 0.10：DD 0% 时因子=1.0（满分），DD 20% 时因子=0.0（零分）
- 其余因子权重略微下调以保持总和=1.0
- 保持 5 因子结构，不引入更多维度（避免过拟合，spec §8.3 原则）

### 新的 _score() 实现

```python
def _score(self, signal: Signal) -> tuple[float, dict[str, float]]:
    ind = signal.indicators
    factors = {
        "strategy_weight":     float(ind.get("weight", 0.5)),
        "signal_confidence":   float(signal.confidence),
        "backtest_win_rate":   float(ind.get("backtest_win_rate", 0.5)),
        "backtest_sortino":    min(max(float(ind.get("backtest_sortino", 0.0)) / 3.0, 0.0), 1.0),
        "backtest_dd_penalty": max(1.0 - float(ind.get("backtest_max_drawdown", 0.0)) / 20.0, 0.0),
    }
    w = self._score_weights
    score = sum(w.get(k, 0.0) * v for k, v in factors.items())
    return score, factors
```

归一化说明：
- `backtest_sortino`：Sortino 通常 0~3，除以 3.0 截断到 [0, 1]
- `backtest_dd_penalty`：DD 0~20%+，`1 - dd/20` 截断到 [0, 1]；DD=0 → 1.0，DD=20 → 0.0，DD>20 → 0.0
- 负 Sortino 会被 `max(..., 0.0)` 截断为 0

### 向后兼容

- `score_weights` 参数仍接受自定义 dict
- 如果传入的 dict 包含 `backtest_sharpe` 但不包含 `backtest_sortino`，不报错（`w.get(k, 0.0)` 返回 0）
- `score_breakdown` dict 中不再有 `backtest_sharpe` key，改为 `backtest_sortino` 和 `backtest_dd_penalty`

### 测试要求

1. **test_score_uses_sortino_not_sharpe**：构造 signal indicators 含 `backtest_sortino=2.0` 但 `backtest_sharpe=0.0`，断言 score > 0 且 score_breakdown 包含 `backtest_sortino`
2. **test_score_dd_penalty**：构造两个 signal，A 的 `backtest_max_drawdown=5`，B 的 `backtest_max_drawdown=18`，其余相同，断言 A.score > B.score
3. **test_score_sortino_normalization**：`backtest_sortino=3.0` → factor=1.0；`backtest_sortino=6.0` → factor=1.0（截断）；`backtest_sortino=-1.0` → factor=0.0
4. **test_custom_score_weights_still_work**：传入 `{"strategy_weight": 1.0}` → 只用该因子
5. **test_ranking_order_changed_by_sortino**：两个 signal，A 的 Sharpe 高但 Sortino 低，B 的 Sharpe 低但 Sortino 高 → B 排名应高于 A（证明评分确实切换了）
6. 现有测试不破坏（`backtest_sharpe` 字段在 indicators 中仍存在但不影响评分）

---

## 4.2 PortfolioBacktest Benchmark 对比

### 修改文件

- `mytrader/mytrader/backtest/portfolio_backtest.py`
- `mytrader/tests/test_portfolio_backtest.py`

### PortfolioBacktestResult 新增字段

```python
@dataclass
class PortfolioBacktestResult:
    # ... 现有字段 ...
    
    # Benchmark 对比（Iteration #7 新增）
    benchmark_symbol: str = "SPY"
    benchmark_total_return_pct: float = 0.0       # SPY 同期总收益
    benchmark_annualized_return_pct: float = 0.0   # SPY 年化收益
    benchmark_sortino_ratio: float = 0.0           # SPY Sortino
    benchmark_max_drawdown_pct: float = 0.0        # SPY 最大回撤
    alpha_pct: float = 0.0                         # 超额收益 = 组合年化 - benchmark 年化
    information_ratio: float = 0.0                  # IR = mean(excess_returns) / std(excess_returns)
```

### PortfolioBacktester.run() 中的 benchmark 计算

在 `run()` 方法的末尾（计算完组合指标后），加入 benchmark 计算：

```python
# ── Benchmark: SPY buy-and-hold ──
benchmark_result = self._compute_benchmark(start, end, daily_returns_list, date_list)
result.benchmark_symbol = benchmark_result.get("symbol", "SPY")
result.benchmark_total_return_pct = benchmark_result.get("total_return_pct", 0.0)
result.benchmark_annualized_return_pct = benchmark_result.get("annualized_return_pct", 0.0)
result.benchmark_sortino_ratio = benchmark_result.get("sortino_ratio", 0.0)
result.benchmark_max_drawdown_pct = benchmark_result.get("max_drawdown_pct", 0.0)
result.alpha_pct = result.annualized_return_pct - result.benchmark_annualized_return_pct
result.information_ratio = benchmark_result.get("information_ratio", 0.0)
```

### _compute_benchmark() 方法

```python
def _compute_benchmark(
    self,
    start: date,
    end: date,
    portfolio_daily_returns: list[float],
    dates: list[date],
) -> dict[str, Any]:
    """计算 SPY buy-and-hold benchmark 指标。
    
    Returns:
        dict with benchmark metrics, or zeros if SPY data unavailable.
    """
    benchmark_symbol = "SPY"
    try:
        spy_bars = self._store.get_bars_multi([benchmark_symbol], start, end)
        spy_df = spy_bars.get(benchmark_symbol)
        if spy_df is None or spy_df.empty:
            logger.warning("[PortfolioBacktest] SPY data unavailable, benchmark skipped")
            return {"symbol": benchmark_symbol}
        
        spy_close = spy_df["close"].astype(float)
        spy_returns = spy_close.pct_change().dropna()
        
        # Align dates with portfolio
        # ... compute total_return, annualized_return, sortino, max_dd ...
        # ... compute information_ratio from excess returns ...
        
        return {
            "symbol": benchmark_symbol,
            "total_return_pct": ...,
            "annualized_return_pct": ...,
            "sortino_ratio": ...,
            "max_drawdown_pct": ...,
            "information_ratio": ...,
        }
    except Exception as e:
        logger.warning(f"[PortfolioBacktest] benchmark computation failed: {e}")
        return {"symbol": benchmark_symbol}
```

### 设计要求

- SPY 数据从 `MarketDataStore` 获取（与组合标的数据同源）
- 如果 SPY 数据不可用，所有 benchmark 字段保持默认 0.0，不抛异常（降级处理）
- Sortino / Max DD 计算方式与组合层一致（复用现有 helper 函数）
- Information Ratio = mean(portfolio_returns - spy_returns) / std(portfolio_returns - spy_returns) * sqrt(252)
- alpha_pct = portfolio_annualized_return - benchmark_annualized_return（正值=跑赢 benchmark）

### 测试要求

1. **test_benchmark_fields_exist**：`PortfolioBacktestResult` 实例包含所有新增 benchmark 字段
2. **test_benchmark_computed_with_spy_data**：mock store 返回 SPY 数据，验证 benchmark_total_return_pct > 0
3. **test_benchmark_zero_when_no_spy**：mock store 不返回 SPY，验证所有 benchmark 字段 = 0.0，不抛异常
4. **test_alpha_calculation**：组合年化 15%，benchmark 年化 10% → alpha = 5.0
5. **test_information_ratio**：构造已知 excess returns，验证 IR 计算正确
6. **test_benchmark_max_drawdown**：构造 SPY 先涨后跌，验证 DD 为正值

---

## 4.3 main.py 日志增强

### 修改文件

- `mytrader/main.py`

在 `_run_reoptimize()` 中 PortfolioBacktester 运行后的日志行，增加 benchmark 信息：

```python
# 现有
logger.info(f"[Portfolio Backtest] DD={dd}%, Sortino={sortino}, Sharpe={sharpe}, Annual Return={annual}%")

# 改为
logger.info(
    f"[Portfolio Backtest] DD={dd}%, Sortino={sortino}, Sharpe={sharpe}, "
    f"Annual Return={annual}%, "
    f"Benchmark(SPY) Return={benchmark_return}%, Alpha={alpha}%, IR={ir}"
)
```

---

## 5. Success Criteria

1. `SignalRanker._score()` 使用 `backtest_sortino` 而非 `backtest_sharpe`
2. `SignalRanker._score()` 包含 `backtest_dd_penalty` 因子
3. `PortfolioBacktestResult` 包含 7 个 benchmark 字段
4. SPY 数据不可用时 benchmark 字段降级为 0.0，不抛异常
5. 默认 pytest 通过（562+ 测试，0 failed）
6. 新增测试 ≥ 8 个（SignalRanker 5 + PortfolioBacktest benchmark 3+）
7. 两份 orchestrator 副本保持同步
8. 更新 trajectory / design docs

---

## 6. Implementation Order

1. 读 spec + `ranker.py` + `portfolio_backtest.py` + `experience.md`
2. 修改 `ranker.py`：DEFAULT_SCORE_WEIGHTS + _score()
3. 更新 `test_strategy_matrix_ranker.py`：新增 Sortino/DD penalty 测试
4. 修改 `portfolio_backtest.py`：PortfolioBacktestResult 新增字段 + _compute_benchmark()
5. 更新 `test_portfolio_backtest.py`：新增 benchmark 测试
6. 修改 `main.py`：日志增强
7. 运行 targeted tests：
   ```bash
   cd mytrader && python -m pytest tests/test_strategy_matrix_ranker.py tests/test_portfolio_backtest.py -q
   ```
8. 运行默认 pytest：
   ```bash
   cd mytrader && python -m pytest -q
   ```
9. 更新 `designs/design_v2/13-signal-ranker.md` + trajectory + CODEBUDDY

---

## 7. Risk Classification

- **中风险**：修改 SignalRanker 评分逻辑会改变选股排名，进而影响 PortfolioBacktest 和实盘选股
- **低风险**：benchmark 对比是只读计算，不影响交易逻辑
- **不在 scope**：不修改风控参数、不下单、不部署
- **Constitution L8 判定**：评分权重调整不属于"高风险变更"（高风险 = risk param / execution logic / validation thresholds），但应在 decision_log 中记录
