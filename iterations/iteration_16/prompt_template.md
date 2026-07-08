# 迭代 #16 Prompt

**任务**: 按 iterations/iteration_16/spec.md 进行开发。关键目标：修复 alpha>0 gate 阻塞 SPX 策略组的问题。按 Implementation Order（§6）逐步实施：1) 读取 matrix_backtest.py::_run_group 找到 alpha gate 位置；2) 添加 ALPHA_GATE_THRESHOLD = -2.0 常量；3) 替换 alpha > 0 为 alpha > ALPHA_GATE_THRESHOLD；4) 检查 _optimize_ensemble_weights 中是否有 alpha > 0 引用；5) 更新相关测试 + 新增 ~7 个 gate 测试；6) 运行全部测试确保通过；7) 运行 --reoptimize 验证 SPX 组不再全部为空；8) 更新 trajectory + CODEBUDDY。严格遵守 scope：不修改策略/indicators/risk/execution/main.py。

**时间**: 2026-07-08T08:14:53.277735+00:00

**注**: 完整 prompt 由 build_constitution_prompt() 动态生成，注入了 ai_constitution.md 的禁止行为、验证流水线、代码规范等规则。
