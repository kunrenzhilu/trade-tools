# 迭代 #12 Prompt

**任务**: 按 iterations/iteration_12/spec.md 进行开发。先读 spec 文件理解完整需求，然后阅读 .codebuddy/notes/experience.md 和 mytrader/mytrader/backtest/matrix_backtest.py（重点 _run_group 和 _optimize_ensemble_weights）。实施步骤：1) GroupBacktestResult 加 no_positive_alpha 字段 2) _run_group 在 candidates 构建后 Tier 1 前插入 alpha>0 硬门槛 3) _optimize_ensemble_weights 修负 alpha 归一化 4) 写测试 5) 检查现有 mock 测试是否需要调整 6) 运行 pytest 7) 更新 design 07 + trajectory + decision_log + CODEBUDDY。注意 spec scope：不改 alpha 排序为 OOS、不加 WF alpha 校验、不改策略代码、不触及 risk/execution。batch vs single 一致性不能破坏。

**时间**: 2026-07-07T10:22:53.680076+00:00

**注**: 完整 prompt 由 build_constitution_prompt() 动态生成，注入了 ai_constitution.md 的禁止行为、验证流水线、代码规范等规则。
