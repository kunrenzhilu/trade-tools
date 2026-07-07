# Iteration #11 Summary — 选择器健全性门槛（Reject Degenerate Strategies）

## Requested

[Spec](spec.md) — 给 `SingleBacktestResult` 新增 `closed_trades` 字段，在 `_run_group` 排序前加健全性门槛剔除退化策略（≥80% 标的零平仓），全退化组返回空权重 + `no_valid_strategy` 标记。

## Delivered

### 文件改动（9 files, +318/-11）

| 文件 | 改动 | 说明 |
|------|------|------|
| `mytrader/backtest/matrix_backtest.py` | +81 | `closed_trades` 字段 + `_is_degenerate_strategy()` + `_run_group` 健全性过滤 + `no_valid_strategy` 标记 |
| `mytrader/tests/test_degenerate_filter.py` | 新增 | 20 个测试用例（字段填充 + batch/single 一致性 + 退化判定 + 集成 + 边界） |
| `mytrader/tests/test_batch_backtest.py` | +7 | `closed_trades` 一致性断言 + 字段类型校验 |
| `mytrader/tests/test_matrix_backtest.py` | +21/-11 | 4 处 mock `SingleBacktestResult` 显式传 `closed_trades` |
| `mytrader/designs/design_v2/07-backtest-module.md` | +12 | 健全性门槛设计记录（Tier 1-3 之前） |
| `alignment/iteration_trajectory.md` | +101 | Iter #11 完整记录 |
| `alignment/decision_log.md` | +48 | 三处模糊决策（vbt API / 阈值取值 / mock 同步） |
| `.codebuddy/CODEBUDDY.md` | +8/-3 | Iter #11 状态更新 |

### 测试

- **626 → 646 passed, 0 failed**（+20 新测试用例，16 deselected live 测试）
- 独立 pytest 验证通过（22.70s）

### 代码实现（完全吻合 spec）

1. ✅ `DEGENERATE_NO_CLOSE_FRACTION = 0.8` 常量（保守阈值，注释说明设计动机）
2. ✅ `SingleBacktestResult.closed_trades: int = 0` 字段
3. ✅ `GroupBacktestResult.no_valid_strategy: bool = False` 标记
4. ✅ `_is_degenerate_strategy()` — 空列表→True，≥80% 标的 closed_trades==0→True
5. ✅ `_backtest_one` 用 `pf.trades.closed.count()`（vbt 1.0 实际 API，spec 预见的 `status_closed` 不存在）
6. ✅ `_backtest_batch` 用 `pf_sym.trades.closed.count()`（与 single 一致）
7. ✅ `_run_group` 在 candidates 构建前插入健全性过滤，全退化→空权重 + `no_valid_strategy=True`

## Meta-Agent Judgment

### Technical: PASS

- 646 passed, 0 failed（独立验证）
- 代码实现 1:1 吻合 spec 设计（7 个实现点全部验证）
- vbt API 差异（`status_closed` → `closed`）被 spec 预见，CodeBuddy 正确查证并使用 `pf.trades.closed.count()`
- batch vs single `closed_trades` 一致性测试覆盖 4 策略 × 多标的
- 边界测试覆盖 0.8 阈值（4/5=0.8 触发、3/5=0.6 不触发、低频不误伤）
- 无 Constitution 违规（未触及 risk/execution/策略代码，DD 约束不变）

### Business Impact: HIGH

**reoptimize 独立验证（2021-07 ~ 2026-07，515 symbols，5 年数据）**：

| 指标 | Iter #10 | Iter #11 | 改善 |
|------|----------|----------|------|
| rsi_trend_filter 入选组数 | 4/6 | **1/6**（仅 NDX_high_vol） | -75% |
| 各组 win_rate | ≈0.0053（退化） | **0.66~0.86**（正常） | 退化策略已清除 |
| rsi_trend_filter DEGENERATE 标记 | 无 | **5/6 组**（SPX_mid/high/low_vol + NDX_mid_vol） | 健全性门槛生效 |

**关键发现**：
- `rsi_trend_filter` 在 NDX_high_vol 保留是**正确的** — win_rate=0.6581 说明该组它确实完成了交易闭环（68 只高波动纳斯达克股票中足够比例有平仓交易）。0.8 阈值没有误杀局部有效的策略，**保守阈值设计验证成功**。
- 5/6 组权重变为 `bollinger_band` + `rsi_mean_revert` 组合，win_rate 0.66~0.86，不再是 Iter #10 的退化值。
- 完整组合 alpha 验证（对比 Iter #10 的 -25.26%）待 WF + PortfolioBacktest 完成（后台运行中）。基于权重变化推断：rsi_trend_filter 从 4/6 组降到 1/6 组且该组有真实交易，组合 alpha 应大幅改善。

### Strategic Fit: GOOD

- 直接实施 `experience.md #8`（sanity → risk → rank，排序前必须先过硬门槛）
- 修复 Iter #10 灾难的根因（退化策略骗过 alpha 排序）
- 低风险（仅改 `matrix_backtest.py` 选择器逻辑，不触及策略/风险/执行代码）
- 没有越界（不改 alpha 排序为 OOS、不加 alpha>0 门槛、不改策略代码 — 全部留给 Iter #12）
- 0.8 保守阈值 + 边界测试 = 可调可回滚

## Bugs Fixed by Meta-Agent

无。CodeBuddy 的实现质量高，无需 meta-agent 修 bug。

## Gate Status

| Gate | 条件 | 结果 |
|------|------|------|
| 技术门 | pytest 0 failed | ✅ 646 passed, 0 failed |
| 健全性门 | rsi_trend_filter 不再退化入选 | ✅ 5/6 组剔除，1 组保留但有真实交易（win_rate=0.66） |
| win_rate 门 | 不再是 ≈0 退化值 | ✅ 全部 0.66~0.86 |
| 阈值精度门 | 不误杀合法低频策略 | ✅ NDX_high_vol rsi_trend_filter 保留（0.8 阈值正确） |
| 组合 alpha | 从 -25% 恢复 | 🔄 待 WF + PortfolioBacktest 完成（后台运行中） → **已完成：alpha=-21.41%**（见下） |

## Next Steps

### reoptimize 完整结果（2026-07-07 15:51 完成）

**Walk-Forward 4 轮：全部通过 ✅**

| 轮次 | 验证期 | Sortino | Max DD | 结果 |
|------|--------|---------|--------|------|
| R1 | 2024-01~2024-07 | 1.79 | 2.06% | passed |
| R2 | 2024-07~2025-01 | 1.56 | 3.03% | passed |
| R3 | 2025-01~2025-07 | 2.09 | 6.36% | passed |
| R4 | 2025-07~2026-01 | 1.98 | 3.01% | passed |

**PortfolioBacktest（近 1 年 2025-07~2026-07）：跑输 SPY ❌**

| 指标 | Iter #7 | Iter #10 | **Iter #11** |
|------|---------|----------|-------------|
| 年化 | 8.02% | -4.88% | **-1.03%** |
| Sortino | 1.03 | -0.66 | **-0.08** |
| Alpha vs SPY | -11.34% | -25.26% | **-21.41%** |
| Max DD | 5.95% | 8.39% | **7.58%** |
| SPY 同期 | — | — | 20.38% |

**分析**：健全性门槛修复了退化策略灾难（alpha -25% → -21%），但策略组合（bollinger_band + rsi_mean_revert）在近 1 年仍跑输 SPY 21%。WF 4/4 pass 但 OOS alpha=-21%，精确复现审计报告 §5 第 6 点"WF gate 不校验 alpha"。

当前 11 条权重中 9 条负 alpha（in-sample），仅 NDX_high_vol（rsi_trend_filter +6.50）和 NDX_low_vol（rsi_mean_revert +1.58）有正 alpha。

1. **Iter #12 候选方向**（审计报告 P1 修复）：
   - **alpha>0 硬门槛**（P1-1，最高 ROI）：`_run_group` 排序后剔除 alpha≤0 的候选，全负 alpha 组空仓。预期 4/6 组空仓，2/6 组保留正 alpha 策略。这是诊断工具——结果会告诉我们策略池是否需要改进。
   - alpha 排序改为 OOS/Walk-Forward 验证期 alpha（P1-2，experience.md #7：同段数据参数搜索+策略选择必然过拟合）→ Iter #13
   - WF gate 增加 alpha 校验（P1-3，WF 4/4 pass 但 alpha=-21% 的直接修复）→ Iter #13
   - 修复 `rsi_trend_filter` 出场逻辑（P0-3，独立策略重设计任务）
2. **Paper Trading 准入评估**：当前 alpha=-21%，Gate 1 失败，不进 paper

## Lessons Learned

1. **spec 预见 API 差异是规范做法**：spec §4.2 明确写"若 vbt API 名称不同，实现者需查 vbt 1.0.0 实际 API"，省去了与 spec 作者反复确认的成本。CodeBuddy 正确查证并使用 `pf.trades.closed.count()`。
2. **保守阈值 + 边界测试**：0.8 阈值在真实数据上验证了正确性 — 5/6 组的 rsi_trend_filter 被剔除（退化），但 NDX_high_vol 的保留（有真实交易）证明阈值不误杀。4/5=0.8 触发、3/5=0.6 不触发的边界测试在真实场景中得到印证。
3. **"被选中" ≠ "有效"的再次验证**：rsi_trend_filter 在 NDX_high_vol 被"选中"是**正确的**（它在该组有真实交易闭环），与 Iter #10 在 4/6 组被"选中"（靠盯市假象骗过 alpha 排序）性质完全不同。健全性门槛区分了这两种"被选中"。
4. **monitor.py 误报教训**：CB 短暂 idle ≠ 完成。monitor.py 的 `agent idle > 120 秒` 判定在 CB 短暂 idle 时会误报 completed。后续应结合 `tools` 计数和 `updates` 增量判断（CB idle 但 tools 不再增长才是真完成）。
5. **orchestrator timeout 等待**：CodeBuddy 退出后 orchestrator 会等 timeout 到期（7200s）才写 snapshot 并退出。这导致 snapshot 文件（result.json/full_response.md/code_diff.patch）延迟 ~2 小时。meta-agent 可独立验证不等 snapshot。

---

> reoptimize 已于 2026-07-07 15:51 完整完成（WF 4/4 pass + PortfolioBacktest alpha=-21.41%）。完整结果已补充到上方"Next Steps"章节。
