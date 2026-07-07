# 迭代 #10 Prompt

**任务**: 按 iterations/iteration_10/spec.md 进行开发。先读 spec 文件理解完整需求，然后实现 vectorbt Batch Backtest Optimization：新增 _backtest_batch() 函数用一次 vbt.Portfolio.from_signals 处理组内所有标的；修改 _run_group 和 Walk-Forward 使用 batch 替代 for-symbol 循环；严格验证数值一致性（np.allclose, 5 策略 × 多参数）；新增进度日志；补充测试。严格遵守 spec scope；不修改策略代码/指标代码/Alpha 排序逻辑；不缩短回测窗口；完成后运行 targeted tests 和默认 pytest，并更新 trajectory / design docs / CODEBUDDY。

**时间**: 2026-07-05T11:56:51.473273+00:00

**注**: 完整 prompt 由 build_constitution_prompt() 动态生成，注入了 ai_constitution.md 的禁止行为、验证流水线、代码规范等规则。
