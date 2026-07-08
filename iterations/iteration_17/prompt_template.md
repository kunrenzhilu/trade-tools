# 迭代 #17 Prompt

**任务**: 按 iterations/iteration_17/spec.md 进行开发。关键目标：通过 Sortino 豁免让高 Sortino 策略绕过 alpha 门槛，解锁 SPX 策略组。按 Implementation Order（§6）逐步实施：1) 读取 matrix_backtest.py::_run_group 定位 alpha gate；2) 添加 SORTINO_ALPHA_EXEMPTION = 1.5 常量；3) 修改 Tier 1 过滤：alpha > -2% OR sortino > 1.5；4) 写 ~7 个新测试（高 Sortino 豁免、低 Sortino 仍需 alpha、DD 仍强制、最低 Sortino 仍强制、边界测试）；5) 运行全部测试；6) 运行 --reoptimize；7) 验证 strategy_weights.json 至少 1 个 SPX 组非空；8) 更新 trajectory + CODEBUDDY。严格遵守 scope：不改策略/indicators/risk/execution/main.py。

**时间**: 2026-07-08T09:42:10.365500+00:00

**注**: 完整 prompt 由 build_constitution_prompt() 动态生成，注入了 ai_constitution.md 的禁止行为、验证流水线、代码规范等规则。
