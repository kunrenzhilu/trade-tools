# 迭代 #7 Prompt

**任务**: 按 iterations/iteration_7/spec.md 进行开发。先读 spec 文件理解完整需求，然后实施 SignalRanker Sortino Priority + Benchmark Comparison：将 SignalRanker 评分从 backtest_sharpe 切换为 backtest_sortino + backtest_dd_penalty；为 PortfolioBacktest 新增 SPY benchmark 对比（alpha/IR/benchmark Sortino/DD）；增强 main.py 日志；补充测试并更新文档。严格遵守 spec scope；不得修改风控参数、DD 阈值、仓位上限或下单逻辑；不得触发真实交易；完成后运行 targeted tests 和默认 pytest，并更新 trajectory / design docs / CODEBUDDY。

**时间**: 2026-07-04T00:50:08.024866+00:00

**注**: 完整 prompt 由 build_constitution_prompt() 动态生成，注入了 ai_constitution.md 的禁止行为、验证流水线、代码规范等规则。
