# 迭代 #9 Prompt

**任务**: 按 iterations/iteration_9/spec.md 进行开发。先读 spec 文件理解完整需求，然后实现 MatrixBacktest Alpha-Based Strategy Selection：新增 SPY benchmark 数据获取和 alpha 计算；将 _run_group 的 top-K 排序从 Sortino 改为 Alpha；新增 Sortino > 0.5 最低质量过滤；将 per-strategy best params 和 ensemble weights 从 Sharpe 改为 Alpha；在 GroupBacktestResult 和 strategy_weights.json 中新增 backtest_alpha 字段；补充测试并更新文档。严格遵守 spec scope；不修改策略代码/风控/执行逻辑；不触发真实交易；完成后运行 targeted tests 和默认 pytest，并更新 trajectory / design docs / CODEBUDDY。

**时间**: 2026-07-05T06:53:25.194831+00:00

**注**: 完整 prompt 由 build_constitution_prompt() 动态生成，注入了 ai_constitution.md 的禁止行为、验证流水线、代码规范等规则。
