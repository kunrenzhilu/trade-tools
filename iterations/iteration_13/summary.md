# Iteration #13 Summary — WF Gate 加 Alpha 校验（目标一致性修复）

## Requested

[Spec](spec.md) — 给 WF gate 加 alpha 校验，使 WF 的验证目标与 matrix_backtest 的选择目标（alpha）一致。当前 WF 只校验 DD，WF 通过 ≠ 跑赢 SPY。

## Delivered

### 文件改动（8 modified + 2 new）

| 文件 | 改动 | 说明 |
|------|------|------|
| `mytrader/backtest/matrix_backtest.py` | +60/-20 | `WALK_FORWARD_VAL_ALPHA_FLOOR` + `WalkForwardRound.val_alpha` + `WalkForwardReport.avg/min_val_alpha` + WF 验证期计算 alpha + gate 加 alpha 校验 |
| `mytrader/tests/test_wf_alpha_gate.py` | 新增 | 16 个测试（字段 + gate + 边界 + 降级 + 汇总） |
| `mytrader/tests/test_matrix_backtest.py` | 更新 | 现有 WF 测试适配 alpha 字段 |
| `mytrader/main.py` | +4/-2 | WF 日志增加 alpha 输出 |
| `mytrader/designs/design_v2/07-backtest-module.md` | +46 | WF alpha gate 设计记录 |
| `alignment/iteration_trajectory.md` | +74 | Iter #13 完整记录 |
| `alignment/decision_log.md` | +39 | 两处决策（单轮 floor + 汇总 avg 两层 / 字段位置） |
| `.codebuddy/CODEBUDDY.md` | 更新 | Iter #13 状态 |

### 测试

- **659 → 675 passed, 0 failed**（+16 新测试用例）
- 独立 pytest 验证通过（22.17s）

### 代码实现（完全吻合 spec）

1. ✅ `WALK_FORWARD_VAL_ALPHA_FLOOR = -5.0` 常量
2. ✅ `WalkForwardRound.val_alpha: float = 0.0` 字段
3. ✅ `WalkForwardReport.avg_val_alpha` + `min_val_alpha` 字段
4. ✅ `run_walk_forward` 验证期计算 alpha vs SPY（复用 `_get_spy_returns` + `_compute_alpha`）
5. ✅ 单轮 gate：`DD ≤ 15% AND alpha > -5%`
6. ✅ 汇总 gate：`all rounds passed AND avg_val_alpha > 0`
7. ✅ SPY 不可用时 val_alpha=0.0 + WARNING（降级不阻塞）
8. ✅ `main.py` WF 日志输出 alpha

## Meta-Agent Judgment

### Technical: PASS

- 675 passed, 0 failed（独立验证）
- 代码实现 1:1 吻合 spec 8 个设计点
- SPY 降级处理正确（不可用时 alpha=0 + WARNING）
- 现有 WF 测试正确适配新字段
- 无 Constitution 违规

### Business Impact: HIGH

**修复了审计报告 §5 第 6 点（WF gate 不校验 alpha）——evaluation layer 最后一个核心方法论缺陷。**

Iter #11 的灾难精确复现了这个问题：WF 4/4 pass（Sortino 1.56~2.09，DD 2~6%）但 PortfolioBacktest alpha=-21.41%。修复后，同样的场景 WF 会在 alpha gate 处 fail（avg alpha < 0 → pass_all_rounds=False），阻止系统进入 paper trading。

**审计报告 §5 漏洞清单最终状态**：

| # | 漏洞 | 状态 |
|---|------|------|
| 1 | 无健全性门槛 | ✅ Iter #11 |
| 2 | 无 alpha>0 硬门槛 | ✅ Iter #12 |
| 3 | 负 alpha 归一化 | ✅ Iter #12 |
| 4 | 样本内选择 = 过拟合 | ⚠️ 部分缓解（WF alpha gate 是 OOS 验证，但选择仍用 in-sample alpha） |
| 5 | WF 只做 pass/fail 不做 selector | ⚠️ 部分缓解（WF 现在校验 alpha，但未回传选择器） |
| 6 | **WF gate 不校验 alpha** | ✅ **Iter #13 修复** |
| 7 | 幸存者偏差 | ❌ P3（需额外数据源） |

### Strategic Fit: GOOD

- 直接修复用户识别的核心问题（"WF 与 matrix_backtest 目标不一致"）
- 低风险（仅改 WF 验证逻辑 + 数据结构字段 + 日志）
- 不需要特制 OOS 数据集——WF 验证期本身就是 OOS
- 与 experience.md #8 完全一致："验收 gate 必须校验跑赢 benchmark（正 alpha）"

## Gate Status

| Gate | 条件 | 结果 |
|------|------|------|
| 技术门 | pytest 0 failed | ✅ 675 passed, 0 failed |
| WF alpha gate | 单轮 alpha > -5% + avg > 0 | ✅ 代码验证通过，待 reoptimize 实证 |
| 目标一致性 | WF gate 校验 alpha | ✅ WF 与 matrix_backtest 目标一致 |
| SPY 降级 | 不可用时 alpha=0 + WARNING | ✅ 不阻塞 WF |

## Next Steps

1. **等 reoptimize 验证**（如有）— 验证 WF 日志输出 alpha + gate 生效
2. **Evaluation layer 核心缺陷已清除**：
   - 选择器治理：健全性门槛（#11）+ alpha>0 门槛（#12）+ ensemble 修复（#12）
   - WF 验证：alpha gate（#13）
   - 剩余：#4（样本内选择）和 #5（WF 不做 selector）部分缓解，#7（幸存者偏差）P3
3. **可以开始专心迭代策略**：
   - 当前策略池在 SPX 组全负 alpha（Iter #12 reoptimize 4/6 组空仓）
   - 需要：新策略 / 修 rsi_trend_filter 出场逻辑 / 改进现有策略参数
   - 每次新策略验证流程：pytest → reoptimize（in-sample alpha>0）→ WF（OOS alpha>0）→ PortfolioBacktest

## Lessons Learned

1. **目标一致性是验证层的核心原则**：matrix_backtest 用 alpha 选策略，WF 也必须校验 alpha。两者目标不一致时，WF 通过毫无意义（Iter #11: WF 4/4 pass 但 alpha=-21%）。
2. **WF 验证期本身就是 OOS**：不需要特制 OOS 数据集——WF 的验证期相对训练期就是样本外。只需在验证期计算 alpha 并加入 gate，就实现了 OOS alpha 验证。
3. **两层 gate 设计（单轮 floor + 汇总 avg）**：单轮允许小幅跑输（-5%），但 4 轮平均必须跑赢（>0）。这平衡了"容忍市场噪音"和"确保整体有效"。
4. **CodeBuddy 这次文档更新完整**：design 07 + trajectory + decision_log + CODEBUDDY 全部更新（Iter #12 漏了文档，这次没有）。
