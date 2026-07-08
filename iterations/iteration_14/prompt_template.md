# 迭代 #14 Prompt

**任务**: 按 iterations/iteration_14/spec.md 进行开发。先读 spec 文件理解完整需求，然后按 Implementation Order（§7）逐步实施：1) 修复 rsi_trend_filter_signal 的出场逻辑（entry用趋势过滤，exit用RSI回归中性）；2) 更新 rsi_trend_filter 参数网格（加 exit_neutral）；3) 新建 rsi_bb_convergence 策略（RSI+Bollinger双确认）；4) 新建 macd_volume 策略（MACD+成交量确认）；5) 更新 __init__.py 注册 + main.py REOPTIMIZE 常量；6) 写 ~23 个测试（spec §4）；7) 运行测试验证全部通过；8) 更新 trajectory + CODEBUDDY。严格遵守 spec §6 scope boundary：不修改 risk/execution/portfolio/matrix_backtest，不新增 indicators.py 指标。

**时间**: 2026-07-08T02:59:40.538999+00:00

**注**: 完整 prompt 由 build_constitution_prompt() 动态生成，注入了 ai_constitution.md 的禁止行为、验证流水线、代码规范等规则。
