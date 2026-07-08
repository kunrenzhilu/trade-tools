# 迭代 #13 Prompt

**任务**: 按 iterations/iteration_13/spec.md 进行开发。先读 spec 文件理解完整需求，然后阅读 mytrader/mytrader/backtest/matrix_backtest.py（重点 run_walk_forward 函数 line 785-930、WalkForwardRound/WalkForwardReport dataclass line 114-155、_get_spy_returns line 1036、_compute_alpha）和 mytrader/main.py（_run_reoptimize line 364-396）和 .codebuddy/notes/experience.md #8。实施步骤：1) 加 WALK_FORWARD_VAL_ALPHA_FLOOR 常量 2) WalkForwardRound 加 val_alpha 字段 3) WalkForwardReport 加 avg_val_alpha/min_val_alpha 4) run_walk_forward 验证期计算 alpha + gate 加 alpha 校验 + 汇总加 alpha 聚合 5) main.py WF 日志增加 alpha 6) 写测试 7) 检查现有 WF 测试是否需调整 8) pytest 9) 更新 design 07 + trajectory + decision_log + CODEBUDDY。注意 spec scope：不做 per-group OOS alpha 反馈、不改选择器逻辑、不改 WF 训练期、不改 PortfolioBacktest。

**时间**: 2026-07-07T16:12:16.305861+00:00

**注**: 完整 prompt 由 build_constitution_prompt() 动态生成，注入了 ai_constitution.md 的禁止行为、验证流水线、代码规范等规则。
