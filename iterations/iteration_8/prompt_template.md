# 迭代 #8 Prompt

**任务**: 按 iterations/iteration_8/spec.md 进行开发。先读 spec 文件理解完整需求，然后实现 Trend-Filtered Mean Reversion 策略：新增 rsi_trend_filter.py 策略（RSI 超卖/超买 + 200日SMA趋势过滤），在 main.py 注册策略和参数网格，新增测试，更新文档。严格遵守 spec scope；不修改现有策略/风控/执行逻辑；不触发真实交易；完成后运行 targeted tests 和默认 pytest，并更新 trajectory / design docs / CODEBUDDY。

**时间**: 2026-07-04T11:50:05.236466+00:00

**注**: 完整 prompt 由 build_constitution_prompt() 动态生成，注入了 ai_constitution.md 的禁止行为、验证流水线、代码规范等规则。
