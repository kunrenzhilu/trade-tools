# 迭代 #11 Prompt

**任务**: 按 iterations/iteration_11/spec.md 进行开发。先读 spec 完整理解需求，再读 .codebuddy/notes/experience.md 与 tmp/iteration10_audit.md 理解背景。实现选择器健全性门槛：给 SingleBacktestResult 加 closed_trades 字段并在 _backtest_one/_backtest_batch 填充（batch 与 single 数值必须一致），新增 DEGENERATE_NO_CLOSE_FRACTION 常量与 _is_degenerate_strategy 函数，在 _run_group 排序前剔除退化策略，全退化组返回空权重并标记 no_valid_strategy。严格遵守 spec scope：不改 alpha 排序为 OOS、不加 alpha>0 硬门槛、不修 rsi_trend_filter 策略代码、不触及 risk/execution/策略/指标代码。补充测试（含 batch vs single 一致性与低频策略不被误伤的边界）。完成后运行 targeted tests 和默认 pytest，更新 designs/design_v2/07-backtest-module.md、trajectory、decision_log、CODEBUDDY。

**时间**: 2026-07-07T02:44:39.908612+00:00

**注**: 完整 prompt 由 build_constitution_prompt() 动态生成，注入了 ai_constitution.md 的禁止行为、验证流水线、代码规范等规则。
