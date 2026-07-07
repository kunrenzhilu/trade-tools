# 迭代 #6 Prompt

**任务**: 按 iterations/iteration_6/spec.md 进行开发。先读 spec 文件理解完整需求，然后实施 Harness Reliability & Live Test Isolation：隔离默认 live tests、修复 orchestrator pytest 统计/状态判定/快照 untracked 留痕、生成 gate_status.json、补充 harness 测试并同步两份 orchestrator 副本。严格遵守 spec scope；不得修改交易策略、风控阈值或下单逻辑；不得触发真实下单；完成后运行 targeted harness tests 和默认非 live pytest，并更新 trajectory / CODEBUDDY / 必要文档。

**时间**: 2026-07-03T16:39:37.582244+00:00

**注**: 完整 prompt 由 build_constitution_prompt() 动态生成，注入了 ai_constitution.md 的禁止行为、验证流水线、代码规范等规则。
