# Iteration #10 Spec — vectorbt Batch Backtest Optimization

> 日期：2026-07-05
> Meta-Agent：GLM
> 输入依据：`tmp/reoptimize.md`、Iter #7 reoptimize 耗时分析（~4 小时）、`matrix_backtest.py` 当前实现
> 风险等级：中高（重构回测核心路径，必须保证数值一致性）
> 核心目标：将 `_backtest_one` 的 for-symbol 循环改为 vectorbt 矩阵化调用，预计 10-20x 提速

---

## 1. 背景

当前 `--reoptimize` 耗时 ~4 小时（Iter #7 实测）。瓶颈分析：

```
每次 reoptimize 的 vbt.Portfolio.from_signals 调用次数：
  MatrixBacktest:  6 组 × 110 参数 × ~60 标的 ≈ 40,000 次
  Walk-Forward:    4 轮 × 40,000 ≈ 160,000 次
  总计：           ~200,000 次 × 30-50ms = 100-170 分钟
```

vectorbt 的设计精髓是矩阵化——一次传 N 个标的，内部并行计算。当前代码把 vectorbt 当成"单标的回测器在 for 循环里调"，完全没用到这个特性。

---

## 2. Problem Statement

### 当前代码结构（`matrix_backtest.py:903-916`）

```python
for params in param_combos:        # 110 次/组
    for sym in symbols:            # ~60 次
        r = _backtest_one(df, ...)  # ← 每次 1 个 vbt.Portfolio.from_signals
```

### 目标结构

```python
for params in param_combos:        # 110 次/组
    results = _backtest_batch(data, strategy, params, ...)
    # ↑ 内部：1 次 vbt.Portfolio.from_signals 处理所有 ~60 个标的
```

调用次数从 ~40,000 降到 ~660（110 参数 × 6 组），**60x 减少**。

---

## 3. Scope

### 本次要做

1. 新增 `_backtest_batch()` 函数：一次处理组内所有标的
2. 修改 `_run_group()` 中的 for-symbol 循环，改为调用 `_backtest_batch()`
3. 修改 Walk-Forward 中的 `_backtest_with_params_on_period()` 同样使用 batch
4. **数值一致性验证**：新旧实现在相同输入下产出相同的 daily_returns
5. 新增进度日志（每组/每策略完成时输出耗时）
6. 新增/更新测试

### 本次不做

1. 不修改策略函数（5 个策略文件不动）
2. 不修改指标函数（`indicators.py` 不动）
3. 不修改 SignalRanker / CandidateSelector / RiskManager
4. 不修改 Alpha 排序逻辑（Iter #9 的改动不动）
5. 不缩短回测窗口（Constitution L7 要求 ≥5 年）
6. 不移除 rsi_trend_filter（Iter #9 Alpha 排序下可能进入权重）
7. 不做 joblib 并行（先做 vectorbt 批量化，验证后再考虑）

---

## 4. Detailed Design

## 4.1 `_backtest_batch()` 函数

### 文件：`mytrader/mytrader/backtest/matrix_backtest.py`

```python
def _backtest_batch(
    data: dict[str, pd.DataFrame],
    strategy_name: str,
    params: dict,
    init_cash: float = 100_000.0,
    fees: float = 0.001,
    slippage: float = 0.001,
) -> list[SingleBacktestResult]:
    """对组内所有标的批量执行回测（迭代 #10 新增）。

    核心优化：用一次 vbt.Portfolio.from_signals 处理所有标的，
    替代 for symbol: vbt.Portfolio.from_signals 的逐标的循环。

    Args:
        data: {symbol: OHLCV DataFrame} 字典
        strategy_name: 策略名
        params: 策略参数
        init_cash / fees / slippage: 回测参数

    Returns:
        SingleBacktestResult 列表（与 _backtest_one 输出格式一致）
    """
```

### 实现步骤

1. **构建 close/open 矩阵**：
   ```python
   symbols = list(data.keys())
   close_matrix = pd.DataFrame({sym: data[sym]["close"] for sym in symbols})
   open_matrix = pd.DataFrame({sym: data[sym]["open"] for sym in symbols})
   ```

2. **逐标的调用策略函数**（策略函数接受 Series，不改）：
   ```python
   signal_columns = {}
   for sym in symbols:
       df = data[sym]
       if len(df) < 30:
           continue
       close = df["close"]
       try:
           sig = strategy_fn(close, df=df, **params)
       except TypeError:
           sig = strategy_fn(close, **params)
       signal_columns[sym] = sig
   signal_matrix = pd.DataFrame(signal_columns)
   ```

3. **一次 vbt 调用处理所有标的**：
   ```python
   entries = signal_matrix == 1
   exits = signal_matrix == -1

   pf = vbt.Portfolio.from_signals(
       close=close_matrix,
       open=open_matrix,
       entries=entries,
       exits=exits,
       init_cash=init_cash,
       fees=fees,
       slippage=slippage,
       size=0.95,
       size_type="Percent",
       freq="D",
   )
   ```

4. **提取 per-symbol 结果**：
   ```python
   results = []
   for i, sym in enumerate(signal_matrix.columns):
       # vbt Portfolio 支持按 column group 提取单个标的的 stats
       pf_sym = pf[:, i]  # 或用 pf.trades(symbol=sym) 等 API
       stats = pf_sym.stats()
       daily_returns = pf_sym.returns()
       results.append(SingleBacktestResult(...))
   return results
   ```

### 关键注意事项

- **对齐问题**：不同标的的交易日可能不完全对齐。`pd.DataFrame` 构造时会自动对齐索引，缺失值填 NaN。vbt 对 NaN 的处理需要验证。
- **init_cash 分配**：批量模式下 vbt 给每个 column 分配独立的 init_cash。需验证 `init_cash=100000` 是否是"每标的 10 万"还是"总共 10 万"——应该是每标的独立。
- **stats 提取**：`pf[:, i].stats()` 的输出格式需与 `_backtest_one` 中的 `pf.stats()` 一致。

---

## 4.2 数值一致性验证

### 验证方法

在测试中构造一个已知数据集（3-5 个标的 × 100 天），分别用旧 `_backtest_one` 和新 `_backtest_batch` 回测，对比：

```python
def test_batch_matches_single_symbol_results():
    """批量化回测与逐标的回测的数值一致性验证。"""
    data = make_test_data(symbols=["A", "B", "C"], days=100)

    # 旧方式：逐标的回测
    old_results = [_backtest_one(data[s], "rsi_mean_revert", {"period": 14, "oversold": 30, "overbought": 70}) for s in data]

    # 新方式：批量回测
    new_results = _backtest_batch(data, "rsi_mean_revert", {"period": 14, "oversold": 30, "overbought": 70})

    # 对比每个标的的 daily_returns
    for old, new in zip(old_results, new_results):
        assert old.symbol == new.symbol
        np.testing.assert_allclose(
            old.daily_returns.values,
            new.daily_returns.values,
            rtol=1e-6, atol=1e-8,
            err_msg=f"{old.symbol}: daily_returns mismatch"
        )
        # stats 对比（允许浮点误差）
        assert abs(old.sharpe - new.sharpe) < 1e-4
        assert abs(old.total_return_pct - new.total_return_pct) < 1e-2
        assert abs(old.max_drawdown_pct - new.max_drawdown_pct) < 1e-2
```

### 必须覆盖的测试场景

1. **所有 5 个策略**：dual_ma, rsi_mean_revert, rsi_trend_filter, macd_cross, bollinger_band
2. **不同参数组合**：至少 2 组参数 per 策略
3. **边界情况**：
   - 数据不足的标的（< 30 天）应被跳过
   - 全 NaN 的标的应被跳过
   - 单标的组（只有 1 个标的）
   - 标的数不对齐（不同起始日期）

---

## 4.3 进度日志

### 在 `_run_group` 中增加

```python
import time
group_start = time.time()
# ... 现有代码 ...
for strategy in strategies:
    strat_start = time.time()
    # ... batch backtest ...
    logger.info(
        f"[MatrixBacktest] {group_id}: {strategy} done in {time.time()-strat_start:.1f}s "
        f"({len(param_combos)} param combos × {len(symbols)} symbols)"
    )
logger.info(f"[MatrixBacktest] {group_id}: all strategies done in {time.time()-group_start:.1f}s")
```

---

## 4.4 Walk-Forward 中的同步修改

### `_backtest_with_params_on_period()`

当前这个函数也用 for-symbol 循环。同样改为调用 `_backtest_batch`。

### 验证

Walk-Forward 的数值一致性同样需要验证——4 轮的 Sortino/DD 结果应与修改前一致（允许浮点误差）。

---

## 5. 测试计划

### 新增测试文件：`tests/test_batch_backtest.py`

1. **test_batch_matches_single_rsi** — RSI 策略 batch vs single 数值一致性
2. **test_batch_matches_single_dual_ma** — dual_ma 策略一致性
3. **test_batch_matches_single_bollinger** — bollinger 策略一致性
4. **test_batch_matches_single_macd** — MACD 策略一致性
5. **test_batch_matches_single_rsi_trend_filter** — rsi_trend_filter 一致性
6. **test_batch_skips_short_data** — 数据 < 30 天的标的被跳过
7. **test_batch_single_symbol** — 只有 1 个标的时正常工作
8. **test_batch_misaligned_dates** — 不同起始日期的标的对齐处理
9. **test_batch_empty_data** — 全空数据返回空列表
10. **test_batch_progress_logging** — 日志包含耗时信息（可选）

### 回归测试

现有 `tests/test_matrix_backtest.py` 中的所有测试必须仍然通过——这验证了 batch 改动没有破坏 top-K 选择、DD 过滤、Alpha 排序等逻辑。

---

## 6. Success Criteria

1. `_backtest_batch()` 实现完成，与 `_backtest_one` 数值一致（np.allclose, rtol=1e-6）
2. 所有 5 个策略的 batch vs single 一致性测试通过
3. `_run_group` 和 Walk-Forward 使用 `_backtest_batch` 替代 for-symbol 循环
4. 现有测试全部通过（602+ 测试，0 failed）
5. 新增测试 ≥ 10 个
6. 进度日志包含每策略耗时
7. 不修改策略代码 / 指标代码 / Alpha 排序逻辑
8. 更新 trajectory / design docs / CODEBUDDY

### 性能验证（Meta-Agent 验收阶段）

- 在验收阶段运行一次小规模 reoptimize（如只跑 1 个组），对比新旧耗时
- 预期：单组从 ~6 分钟降到 < 1 分钟

---

## 7. Implementation Order

1. 读 spec + `matrix_backtest.py`（重点 `_backtest_one` / `_run_group`）+ `indicators.py` + 一个策略文件
2. 实现 `_backtest_batch()`
3. 写数值一致性测试（先跑一个策略验证，再扩展到 5 个）
4. 修改 `_run_group` 使用 `_backtest_batch`
5. 修改 Walk-Forward 中的 `_backtest_with_params_on_period`
6. 添加进度日志
7. 运行 targeted tests：`python -m pytest tests/test_batch_backtest.py tests/test_matrix_backtest.py -q`
8. 运行默认 pytest：`python -m pytest -q`
9. 更新 `designs/design_v2/07-backtest-module.md` + trajectory + CODEBUDDY

---

## 8. Risk Classification

- **中高风险**：重构回测核心路径，如果数值不一致会导致策略选择结果变化
- **缓解措施**：严格的数值一致性测试（np.allclose + 5 策略 × 2 参数 × 边界场景）
- **不触及**：策略代码 / 指标 / 风控 / 执行 / Alpha 排序
- **回滚方案**：如果 batch 版本数值不一致且无法修复，保留 `_backtest_one` 作为 fallback
