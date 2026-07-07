# 迭代 #3 Prompt

**任务**: P0+P1 两项改动，合并为一次迭代以减少 reoptimize 次数。

## P0: 修复 NDX_high_vol DD 超标（Gate 1 阻塞项）

问题背景：matrix_backtest.py 的 _run_group 在选 top-K 策略时只按 Sortino 排序，没有 DD 约束。NDX_high_vol 组（62只高波动NASDAQ股）当前 top-2 策略的 portfolio DD 均超过 20%（22.22% 和 21.96%），违反 Constitution L1 硬约束。

需要改动（仅修改 matrix_backtest.py）：
1. 在 _run_group 中，对该组内所有参数组合的 portfolio_max_drawdown 计算完成后，先过滤出 DD <= 20.0 的候选（合规集），再在合规集中按 Sortino 选 top-K。
2. 如果某组完全没有 DD<=20% 的合规候选（可能是结构性问题），fallback：保留 DD 最低的 top-K 候选并记录 WARNING，不抛异常（让 reoptimize 继续跑完其他组）。
3. 在 GroupBacktestResult 中新增 bool 字段 dd_constrained: bool = False，标记该组是否用了 fallback（即没有任何合规候选）。
4. _write_weights 输出中新增 dd_constrained 字段。
5. 补充对应单元测试（至少3个：有合规候选/无合规候选fallback/dd_constrained字段输出）。

## P1: Walk-Forward 4轮验证（L7 流水线硬要求）

问题背景：Constitution L7 要求 Backtest(>=5年) → Walk-Forward(4轮) → Paper Trade(>=1月) → Live。当前 MatrixBacktest 只做单窗口5年回测，未做 Walk-Forward。

数据已确认（5年数据 2021-07-02 ~ 2026-07-01），4轮时间窗口：
- 轮1：训练 2021-07-02~2023-01-02 | 验证 2023-01-02~2023-07-02
- 轮2：训练 2022-01-02~2023-07-02 | 验证 2023-07-02~2024-01-02
- 轮3：训练 2022-07-02~2024-01-02 | 验证 2024-01-02~2024-07-02
- 轮4：训练 2023-01-02~2024-07-02 | 验证 2024-07-02~2025-01-02

需要改动（仅修改 matrix_backtest.py，不改 MatrixBacktest 主类接口）：
1. 新增函数 run_walk_forward(matrix_backtest_instance, strategies, param_grids, rounds=4, train_months=18, val_months=6) -> WalkForwardReport。
2. WalkForwardReport dataclass 包含：rounds: list[WalkForwardRound]，pass_all_rounds: bool，max_val_dd: float。
3. WalkForwardRound dataclass 包含：round_num, train_start, train_end, val_start, val_end, val_sortino: float, val_max_dd: float, passed: bool（passed = val_max_dd <= 15.0，Constitution 门槛）。
4. 实现逻辑：对每轮，用训练期数据跑矩阵回测找最优参数，然后用验证期数据用同参数回测，记录验证期的 Sortino 和 portfolio DD。
5. WalkForwardReport.pass_all_rounds = all(r.passed for r in rounds)。
6. main.py 的 --reoptimize 流程中，在 MatrixBacktest.run() 之后调用 run_walk_forward()，将结果输出到日志（不影响 strategy_weights.json，WF 是验证步骤不是优化步骤）。
7. 补充单元测试（至少4个：WalkForwardRound/WalkForwardReport dataclass/passed判定/run_walk_forward mock集成测试）。

## 完成标准
- pytest 全部通过（测试数不得下降）
- --reoptimize 运行成功，日志中出现 Walk-Forward 的 4 轮结果
- strategy_weights.json 中 NDX_high_vol 的 dd_constrained 字段正确
- 更新 alignment/iteration_trajectory.md 和 alignment/decision_log.md
- 低风险变更，不触及 risk/execution 模块

**时间**: 2026-07-01T03:35:42.587074+00:00

**注**: 完整 prompt 由 build_constitution_prompt() 动态生成，注入了 ai_constitution.md 的禁止行为、验证流水线、代码规范等规则。
