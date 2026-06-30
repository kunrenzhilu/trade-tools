# Decision Log — AI Constitution 决策记录

> 根据 ai_constitution.md L8 要求，记录所有模糊决策及其逻辑。

---

### [2026-06-30 16:20 UTC] 迭代 #1 — test_integration_live.py 触发真实 Telegram 消息

- **困境描述**: CodeBuddy 在迭代 #1 中运行 `pytest` 时，`tests/test_integration_live.py::TestTelegramBot::test_send_test_message` 真实调用了 Telegram Bot API，向用户发送了测试消息。这暴露了测试隔离问题：live 集成测试没有被正确标记为 skip-by-default，导致全量 pytest 运行时触发了真实外部 API 调用。

- **涉及 AI Constitution 条款**:
  - L8 #8: "默默执行重大决策（须 Telegram Bot 通知）" — 虽然 Telegram 通知本身是 Constitution 要求的，但测试环境中意外触发通知不是"有意义的决策通知"
  - L7: 测试纪律 — "测试失败不允许 Merge"，但这里的测试实际上通过了（消息发送成功），问题是它不应该在非 live 测试场景下运行

- **决策逻辑**: 这是一个测试隔离缺陷，不是 CodeBuddy 的错误。`test_integration_live.py` 应该有 `@pytest.mark.live` 标记，且 `pytest.ini` 默认跳过 live 测试。当前迭代 #1 不中断，此问题记录到下次迭代处理。

- **决策结果**: 记录问题，不中断当前迭代。下次迭代优先修复。

- **待修复项**:
  1. `tests/test_integration_live.py` 添加 `@pytest.mark.live` 标记到所有测试类
  2. `pytest.ini` 或 `conftest.py` 配置默认跳过 `live` 标记的测试
  3. `test_send_test_message` 中的硬编码日期 `2026-06-20` 改为 `datetime.now().strftime("%Y-%m-%d")`
  4. 考虑将 `test_send_test_message` 改为 mock 或移到单独的 smoke test 目录

- **用户反馈**: 用户在 16:12 收到两条 Telegram 消息，要求记录问题，不中断当前迭代。
