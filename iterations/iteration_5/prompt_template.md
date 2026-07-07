# 迭代 #5 Prompt

**任务**: 按 iterations/iteration_5/spec.md 进行开发。先读 spec 文件理解完整需求，再实施 Paper Trading Integrity & Parity：统一线上与 PortfolioBacktest signal metadata、实现 AlpacaBroker 持仓/订单状态刷新、修复 reconciliation callback、增加 paper daily metrics、补充测试和文档。严格遵守 spec 的 scope 与禁止事项；不得触发真实下单；完成后运行 targeted tests 和默认 pytest，并更新 trajectory / decision_log / CODEBUDDY / design docs。

**时间**: 2026-07-03T09:26:49.222517+00:00

**注**: 完整 prompt 由 build_constitution_prompt() 动态生成，注入了 ai_constitution.md 的禁止行为、验证流水线、代码规范等规则。
