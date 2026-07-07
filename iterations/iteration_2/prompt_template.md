# 迭代 #2 Prompt

任务: 为 matrix_backtest.py 补全核心 KPI 计算(NaN安全处理+Sortino+PortfolioDD+输出字段+stats安全化), main.py参数网格扩展, grouping.py低波动阈值0.01->0.02. 完成后运行 python main.py --reoptimize 生成新weights, 运行 pytest 确认通过, 更新 iteration_trajectory.md 和 decision_log.md. 风险等级低, 不触及risk/execution模块.

时间: 2026-07-01T08:11:00Z
注: 完整 prompt 由 build_constitution_prompt() 动态生成，注入了 ai_constitution.md 的禁止行为、验证流水线、代码规范等规则。
