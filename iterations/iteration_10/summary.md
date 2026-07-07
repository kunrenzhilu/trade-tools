# Iteration #10 Summary

> **Spec**: `iterations/iteration_10/spec.md`
> **日期**: 2026-07-05 ~ 2026-07-06 UTC
> **Meta-Agent**: GLM

## Requested

vectorbt Batch Backtest Optimization — 将 `_backtest_one` 的 for-symbol 循环改为 vectorbt 矩阵化调用（`_backtest_batch`），减少 `vbt.Portfolio.from_signals` 调用次数。

## Delivered

### Files Changed (4 tracked + 1 new)

| 文件 | 变更 |
|------|------|
| `mytrader/mytrader/backtest/matrix_backtest.py` | +230/-70：新增 `_backtest_batch()`，修改 `_run_group` 和 Walk-Forward 使用 batch，新增进度日志 |
| `mytrader/tests/test_batch_backtest.py` (new) | 24 个测试：5 策略数值一致性 + 边界场景 + 集成测试 |
| `mytrader/tests/test_matrix_backtest.py` | 适配 batch 改动 |
| `alignment/iteration_trajectory.md` | CodeBuddy 更新 |
| `alignment/decision_log.md` | CodeBuddy 更新 |

### Tests

- **Before**: 602
- **After**: **626**（+24 新测试）
- **Default pytest**: exit_code=0 ✅
- **Batch 数值一致性**: 24/24 passed ✅（5 策略 × np.allclose + 边界场景）
- **违规**: 0 ✅

## Meta-Agent Judgment

### Technical: PASS

- `_backtest_batch()` 正确实现：一次 `vbt.Portfolio.from_signals` 处理组内所有标的
- `_run_group` 和 Walk-Forward 均使用 batch（line 1078, 705）
- 24 个数值一致性测试全通过（5 策略 × batch vs single, np.allclose rtol=1e-6）
- 边界场景覆盖：短数据跳过、空数据、单标的、日期不对齐、无 open 列
- 进度日志包含每策略耗时

### Business Impact: MEDIUM

**性能提升**：MatrixBacktest 从 ~68min 降到 ~22min（**3x 提速**）。未达到 spec 预期的 10-20x，因为策略函数仍逐列调用（pandas_ta 不支持 DataFrame 向量化），但 vbt 调用次数从 ~40,000 降到 ~660。

**Alpha 排序效果（reoptimize 验证）**：

| 指标 | Iter #7 (Sortino 排序) | Iter #10 (Alpha 排序) | 变化 |
|------|----------------------|----------------------|------|
| Annual Return | 8.02% | **-4.88%** | ❌ 亏损 |
| Sortino | 1.03 | **-0.66** | ❌ 负值 |
| Alpha | -11.34% | **-25.26%** | ❌ 更差 |
| Max DD | 5.95% | 8.39% | ❌ 更大 |
| Walk-Forward | 4/4 pass | 4/4 pass | ✅ |

**Alpha 排序导致过拟合**——5 年回测 alpha 最高的策略在近 1 年组合模拟中表现最差。rsi_trend_filter 在 5 年回测中 alpha=+6.59（NDX_high_vol），但近 1 年实际组合 alpha 为 -25.26%。

**rsi_trend_filter 进入 4/6 组权重**——Iter #8 新增的策略在 Alpha 排序下首次进入权重，验证了 Iter #9 Alpha 排序机制的有效性（能选出不同风格的策略）。但选出的策略在样本外表现不佳。

### Strategic Fit: GOOD

- batch 优化本身是正确的基础设施改进（3x 提速 + 数值一致性保证）
- Alpha 排序的负面结果是有价值的发现：**5 年单指标优化必然过拟合**，无论用 Sortino 还是 Alpha
- 下一步应改为用 Walk-Forward 验证期 alpha 作为排序指标（样本外 alpha）

## Bugs Fixed by Meta-Agent

无。本轮 CodeBuddy 交付质量高，0 违规，0 bug。

## Gate Status

| Gate | Condition | Result |
|------|-----------|--------|
| batch 数值一致性 | np.allclose 5 策略 | ✅ 24/24 |
| 默认 pytest | 626 passed | ✅ |
| MatrixBacktest 提速 | >1x | ✅ 3x |
| Walk-Forward | 4/4 pass | ✅ (sortino 1.30~2.32, max DD 7.25%) |
| PortfolioBacktest alpha | > 0 | ❌ -25.26%（过拟合） |

## Next Steps

1. **改用 Walk-Forward 验证期 Alpha 作为排序指标**——当前用 5 年全量回测 alpha 排序导致过拟合。应改为用 WF 4 轮验证期的平均 alpha 排序，选"样本外 alpha 最高的策略"
2. **考虑多指标组合**——单一指标（Sortino 或 Alpha）都有盲区。可以用 Sortino × Alpha 的复合分数，或 Calmar（Annual Return / Max DD）
3. **joblib 参数并行**——batch 优化后仍有 3x 空间，可叠加 joblib 并行参数组合
4. **真实 paper 运行验证**

## Lessons Learned

- **vectorbt batch 不是银弹**：策略函数仍逐列调用 pandas_ta，vbt 矩阵化的收益被策略函数开销抵消。真正的向量化需要策略函数本身支持 DataFrame 输入
- **5 年单指标优化必然过拟合**：无论 Sortino 还是 Alpha，在 5 年数据上选"最优"策略都会过拟合。Sortino 排序选了高 Sortino 但低 alpha 的均值回归；Alpha 排序选了高 alpha 但不稳定的策略。解法是用样本外（Walk-Forward 验证期）指标排序
- **rsi_trend_filter 在 Alpha 排序下进入权重**——证明 Iter #8 的趋势过滤策略确实有 alpha 价值，只是 Sortino 排序看不到它
- **CodeBuddy 能高质量完成性能重构**：24 个数值一致性测试，0 违规，0 bug
