# Iteration #12 Summary — Alpha>0 硬门槛（Reject Negative-Alpha Strategies）

## Requested

[Spec](spec.md) — 在 `_run_group` Tier 1/2/3 排序之前加 alpha>0 硬门槛（剔除跑不赢 SPY 的策略）；全负 alpha 组返回空权重；修 `_optimize_ensemble_weights` 的 `max(alpha,0.01)` 归一化 bug。

## Delivered

### 文件改动（6 files, +100/-19 core + 新增测试）

| 文件 | 改动 | 说明 |
|------|------|------|
| `mytrader/backtest/matrix_backtest.py` | +68/-19 | `no_positive_alpha` 字段 + alpha>0 硬门槛 + ensemble 归一化修复 |
| `mytrader/tests/test_alpha_gate.py` | 新增 | 13 个测试用例（字段 + 门槛集成 + 协同 + ensemble 归一化） |
| `mytrader/tests/test_batch_backtest.py` | +13/-6 | SPY benchmark 数据调整（trend="down" 确保 alpha>0） |
| `mytrader/tests/test_degenerate_filter.py` | +17/-1 | 同上 SPY benchmark 调整 |
| `mytrader/tests/test_matrix_backtest.py` | +21/-10 | 同上 SPY benchmark 调整 |
| `mytrader/designs/design_v2/07-backtest-module.md` | 更新 | alpha>0 门槛设计记录（健全性 → alpha>0 → Tier 1/2/3） |
| `alignment/iteration_trajectory.md` | 更新 | Iter #12 完整记录 |
| `alignment/decision_log.md` | 更新 | 两处模糊决策（门槛位置 + ensemble 归一化） |
| `.codebuddy/CODEBUDDY.md` | 更新 | Iter #12 状态 |

### 测试

- **646 → 659 passed, 0 failed**（+13 新测试用例）
- 独立 pytest 验证通过（22.21s）

### 代码实现（完全吻合 spec）

1. ✅ `GroupBacktestResult.no_positive_alpha: bool = False` 字段
2. ✅ `_run_group` 在 candidates 构建后、Tier 1 前插入 alpha>0 硬门槛
3. ✅ 全负 alpha 组返回空权重 + `no_positive_alpha=True` 标记
4. ✅ `_optimize_ensemble_weights` 修 `max(alpha, 0.01)` → `max(alpha, 0.0)`，负 alpha 权重为 0
5. ✅ 全负 alpha ensemble 等权 fallback + WARNING（防御性设计）

## Meta-Agent Judgment

### Technical: PASS

- 659 passed, 0 failed（独立验证）
- 代码实现 1:1 吻合 spec 5 个设计点
- 健全性门槛 + alpha>0 门槛协同测试覆盖（退化策略先被健全性剔除，负 alpha 再被 alpha 门槛剔除）
- 现有 mock 测试正确调整 SPY benchmark 数据（trend="down" 确保策略 alpha>0，避免被新门槛误杀）
- 无 Constitution 违规

### Business Impact: HIGH（待 reoptimize 完整验证）

**预期 reoptimize 结果**（基于 Iter #11 strategy_weights.json 数据推断）：

| 组 | Iter #11 alpha | Iter #12 预期 |
|----|---------------|---------------|
| SPX_mid_vol | -5.22, -6.75 | **空仓** |
| SPX_high_vol | -4.41, -6.11 | **空仓** |
| NDX_high_vol | +6.50 | ✅ 保留 |
| SPX_low_vol | -4.49, -6.10 | **空仓** |
| NDX_low_vol | +1.58, -1.49 | ✅ 保留 rsi_mean_revert |
| NDX_mid_vol | -2.78, -7.79 | **空仓** |

4/6 组空仓，2/6 组保留正 alpha 策略。组合 alpha 应大幅改善（9 条负 alpha 策略不再拖累）。

### Strategic Fit: GOOD

- 直接实施 `experience.md #8` 的完整门槛顺序：健全性 → 风险 → 正超额 → 排序
- 修复审计报告 §5 第 2-3 点（无 alpha>0 硬门槛 + 负 alpha 归一化 bug）
- 低风险（仅改 `matrix_backtest.py` 选择器逻辑 + ensemble 权重）
- 诊断工具：如果 4/6 组空仓，说明策略池在 SPX 组跑不赢 SPY → Iter #13 方向明确

## Gate Status

| Gate | 条件 | 结果 |
|------|------|------|
| 技术门 | pytest 0 failed | ✅ 659 passed, 0 failed |
| alpha>0 门 | 负 alpha 策略不进权重 | ✅ 代码验证通过，待 reoptimize 实证 |
| ensemble 门 | 负 alpha 不被 max(0.01) 掩盖 | ✅ 权重为 0 |
| 协同门 | 健全性 + alpha 门槛协同 | ✅ 退化先剔除，负 alpha 再剔除 |
| 组合 alpha | 从 -21% 改善 | 🔄 reoptimize 后台运行中 |

## Next Steps

1. **等 reoptimize 完成**（后台 PID=71935）— 验证 4/6 组空仓、2/6 组保留正 alpha、组合 alpha 改善
2. **Iter #13 候选方向**：
   - 如果 4/6 组空仓 → 策略池需要改进（新策略 or 修 rsi_trend_filter 出场逻辑）
   - alpha 排序改为 OOS/Walk-Forward 验证期 alpha（experience.md #7）
   - WF gate 增加 alpha 校验（审计 §5 第 5-6 点）
3. **Paper Trading 准入评估**：取决于 reoptimize 结果

## Lessons Learned

1. **门槛顺序很重要**：alpha>0 放在 Tier 1 前（排序前）比放在 top-K 后（排序后）更符合 experience.md #8，避免遗漏正 alpha 策略。
2. **`max(x, ε)` 是危险的归一化模式**：把负 alpha 都变成 0.01 → 等权，掩盖"都不好"。正确做法是让坏值权重为 0，只有好值参与归一化。
3. **新增门槛需要同步调整现有测试的 benchmark 数据**：alpha>0 门槛要求 mock 测试中的策略 alpha>0，否则被新门槛误杀。CodeBuddy 正确识别并调整了 3 个测试文件的 SPY benchmark 数据。
4. **CodeBuddy 漏文档更新**：spec §7 第 8 步要求更新 design 07 + trajectory + decision_log + CODEBUDDY，但 CodeBuddy 没做。Meta-Agent 补上了。后续 spec 应把文档更新作为更显眼的检查点。
