# Iteration #9 Summary

> **Spec**: `iterations/iteration_9/spec.md`
> **日期**: 2026-07-05 UTC
> **Meta-Agent**: GLM

## Requested

将 MatrixBacktest 的 top-K 策略选择从 Sortino 排序改为 Alpha 排序，使选出的策略直接优化超额收益。

## Delivered

### 关键改动

| 组件 | Before | After |
|------|--------|-------|
| top-K 排序 | Sortino 降序 | **Alpha 降序** |
| 质量门槛 | 无 | **Sortino > 0.5** |
| DD 过滤 | ≤ 20% | ≤ 20%（不变） |
| per-strategy best params | Sharpe | **Alpha** |
| ensemble weights | Sharpe 归一化 | **Alpha 归一化** |
| GroupBacktestResult | 无 alpha | **backtest_alpha 字段** |
| strategy_weights.json | 无 alpha | **backtest_alpha 字段** |

### 三级 Fallback 设计

```
Tier 1: DD ≤ 20% AND Sortino > 0.5 → Alpha 降序选 top-K
Tier 2: DD ≤ 20% but Sortino 全 < 0.5 → 放宽 Sortino，Alpha 降序
Tier 3: DD 全 > 20% → 按 DD 升序（标记 dd_constrained）
```

### Tests

- **Before**: 585
- **After**: **602**（+17 新测试）
- **exit_code**: 0
- **违规**: **0**（首次零违规！）

## Meta-Agent Judgment

### Technical: PASS

- Alpha 计算正确：`alpha = (strat_annual - spy_annual) * 100`
- SPY 数据不可用时降级为 0（不崩溃）
- 三级 fallback 设计合理
- GroupBacktestResult + JSON 新增 backtest_alpha
- 602 测试全通过

### Business Impact: HIGH（待 reoptimize 验证）

这是从"Sortino 优化"到"Alpha 优化"的根本性转变。如果下一轮 reoptimize 选出的策略组合 alpha > 0，就证明这个改动有效。

### Orchestrator Harness 验证

| 验证项 | 结果 |
|--------|:----:|
| status | **passed** ✅ |
| violations | **0** ✅（Iter #8 false positive 修复生效） |
| count_tests | 585 → 602 ✅ |
| exit_code | 0 ✅ |
| 两份副本同步 | IDENTICAL ✅ |

**首次 orchestrator 零误报迭代！** Iter #6-#8 的 harness 修复全部生效。

## Next Steps

1. **运行 `--reoptimize`**：用 Alpha 排序重新选策略，观察：
   - 是否有趋势策略（dual_ma, macd_cross, rsi_trend_filter）进入权重
   - PortfolioBacktest 的 alpha 是否改善（从 -11.34% 向 0 靠拢）
2. 如果 alpha 仍为负，考虑增加突破策略或改变参数网格
3. 真实 paper 运行验证
