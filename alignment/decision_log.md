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

---

### [2026-07-01 UTC] 迭代 #2 — portfolio_max_drawdown 符号约定

- **困境描述**: `_portfolio_max_drawdown_from_results` 的返回值符号选择存在歧义。vectorbt `pf.stats()["Max Drawdown [%]"]` 返回负值（例如 -15.2 表示 15.2% 回撤），而 `SingleBacktestResult.max_drawdown_pct` 沿用了这一负值约定。本次新增的 `portfolio_max_drawdown` 字段应保持一致（负值）还是取正值便于聚合和 JSON 输出？

- **涉及 AI Constitution 条款**:
  - L1: KPI 必须可解释、可比较 — 符号约定不一致会增加跨字段比较的认知负担
  - L7: 代码规范 — 一致性优先

- **决策逻辑**: 选择返回**正值百分数**（0.0 ~ 100.0），理由：
  1. Constitution L1 的 DD≤20% 约束是正数表述，正值便于直接比较（`if dd > 20: alert`）
  2. `backtest_max_drawdown` 字段输出到 JSON 供实盘监控读取，正值更符合外部消费者直觉
  3. 聚合时（如跨组比较）正值可直接取 max，避免符号混乱
  4. 与 `avg_max_drawdown_pct`（取各标的 `max_drawdown_pct` 算术平均，目前是负值）存在符号差异，但 `portfolio_max_drawdown` 是新字段，无历史包袱

  代价：与 `SingleBacktestResult.max_drawdown_pct`（负值）和 `GroupBacktestResult.avg_max_drawdown_pct`（负值）符号不一致。但这两个旧字段本次迭代不改动（避免破坏性变更），后续迭代可统一为正值约定。

- **决策结果**: `_portfolio_max_drawdown_from_results` 返回 `abs(dd_max_pct) * 100.0`（正值）。`GroupBacktestResult.portfolio_max_drawdown` 和 JSON 输出的 `backtest_max_drawdown` 均为正值。

- **后续待办**: 后续迭代可考虑统一所有 `*_max_drawdown_*` 字段为正值约定，并更新相关测试和文档。

---

### [2026-07-01 UTC] 迭代 #3 — P0 DD 约束应用层级 + P1 Walk-Forward 窗口语义

- **困境描述 (P0)**: 任务描述 "对该组内所有参数组合的 portfolio_max_drawdown 计算完成后，先过滤出 DD <= 20.0 的候选（合规集），再在合规集中按 Sortino 选 top-K" 中的"所有参数组合"存在歧义：
  - 解读 A: 所有 (strategy, params) 笛卡尔积（约 83 个候选 × 组），但这会破坏 ensemble 多样性语义（top-K 需为不同策略）
  - 解读 B: 每策略已选出 best params 后的 group_results（每策略 1 个候选，共 N 个），再过滤 + Sortino top-K

- **涉及 AI Constitution 条款**:
  - L7: 验证流水线 — 必须保证每组 top-K 是不同策略（ensemble 多样性）
  - L1: 决策可解释 — top-K 应可读为"K 个不同策略的加权组合"
  - Constitution 决策权重矩阵：策略多样性 > 参数微调

- **决策逻辑 (P0)**: 采用解读 B。理由：
  1. 现有 `_run_group` 结构是"每策略选 best params → top-K 策略"， ensemble 语义要求 top-K 为不同策略
  2. 解读 A 会让同一策略以不同 params 出现在 top-K 中，违反 ensemble 多样性设计
  3. 改动最小化（仅修改 top-K 选择步骤，不重构 per-strategy 选 best params 逻辑）
  4. "所有参数组合"指的是计算已完成的状态，不是过滤的对象

  附带决策：per-strategy best params 仍按 Sharpe 选择（不切换为 Sortino），仅 top-K 步骤切换为 Sortino + DD 约束。理由：
  - 任务描述只要求 top-K 用 Sortino，未要求 per-strategy 切换
  - per-strategy 切换为 Sortino 是更大的语义变更，应单独评估
  - 当前 NDX_high_vol 的问题不是 per-strategy 选错 params，而是该组所有 (strategy, params) 组合的 DD 都 > 20%

- **决策结果 (P0)**: 在 `_run_group` 的 top-K 选择步骤添加 DD <= 20 过滤 + Sortino 排序；fallback 时按 DD 升序取 top-K 并标记 `dd_constrained=True`。per-strategy best params 选择逻辑保持不变（仍按 Sharpe）。

- **困境描述 (P1)**: Walk-Forward 时间窗口的动态计算。任务给出了固定的 4 轮窗口，但函数签名要求 `rounds=4, train_months=18, val_months=6` 参数化。应硬编码 4 个固定窗口，还是动态计算？

- **涉及 AI Constitution 条款**:
  - L7: 验证流水线 — Walk-Forward 应可复现，且能适应未来数据扩展
  - L9: Evolution — 系统应支持参数化迭代，不写死

- **决策逻辑 (P1)**: 动态计算窗口。理由：
  1. 函数签名已参数化，硬编码 4 轮窗口与参数矛盾
  2. 未来数据扩展到 10 年时，固定窗口会失效
  3. 用户提供的 4 轮窗口可由 `train_months=18, val_months=6, rounds=4` + 起始日期计算得出，完全可复现
  4. 计算公式：last_round_val_end = today - val_months（留 1 个 val 期给 paper trading）；每轮向前推 val_months

  验证（today=2026-07-01）：
  - Round 4 val_end = 2026-07-01 - 6m ≈ 2025-01-01 ≈ 2025-01-02 ✓
  - Round 1 val_end = 2025-01-02 - 18m ≈ 2023-07-02 ✓
  - Round 1 train_start = 2023-01-02 - 18m ≈ 2021-07-02 ✓

- **决策结果 (P1)**: 动态计算窗口。`run_walk_forward()` 接受 `rounds/train_months/val_months` 参数，按公式计算每轮窗口。用户提供的固定窗口作为测试用例的 expected value 验证公式正确性。

- **困境描述 (P1.2)**: Walk-Forward 验证期的 portfolio 指标是 per-group 还是全局聚合？任务说"记录验证期的 Sortino 和 portfolio DD"，未明确范围。

- **决策逻辑 (P1.2)**: 全局聚合。理由：
  1. Constitution L1 的 DD 约束是针对整体 portfolio（"Max DD ≤ 20%"），不是 per-group
  2. 真实部署时组合所有组的策略为一个 portfolio，全局 DD 是真正的风险指标
  3. per-group DD 已在 MatrixBacktest 中记录，WF 是补充验证整体 portfolio 的样本外稳定性

- **决策结果 (P1.2)**: 验证期将所有组的回测日收益率按等权合并为一个 portfolio 序列，计算 Sortino 和 max DD。

---

### [2026-07-02 UTC] 迭代 #4 — PortfolioBacktest 复用 vs 重写 + backtest_dd_status 字段位置

- **困境描述 (P0)**: spec 要求"复用现有组件，不重写 StrategyMatrixRunner/SignalRanker/CandidateSelector"。但 PortfolioBacktester 需要在每日切片数据上生成信号（防前视偏差），而 StrategyMatrixRunner.run_symbol 内部直接读 store.get_latest_n_bars——这会拿到 store 中的全量历史数据，无法限定到"截至当日"。

  两种实现方式：
  - 解读 A: 直接调用 `self._matrix_runner.run_symbol(sym)` — 简单但破坏防前视偏差（runner 读全量数据）
  - 解读 B: 复用 runner 的策略调用逻辑（直接调 STRATEGY_REGISTRY），但用传入的切片数据 — 维持防前视偏差但代码有重复

- **涉及 AI Constitution 条款**:
  - L7: 验证流水线 — 必须保证回测防前视偏差
  - L1: 决策可解释 — 回测结果必须可信（前视偏差会让回测过于乐观）
  - Constitution 决策权重矩阵：正确性 > 代码 DRY

- **决策逻辑 (P0)**: 采用解读 B。理由：
  1. 防前视偏差是 Constitution L7 的硬要求，不能为了代码 DRY 而牺牲正确性
  2. 重复的部分仅是"策略调用 + 信号有效期检查"约 20 行，不是核心逻辑
  3. SignalRanker 和 CandidateSelector 完全复用（无重复），只有 StrategyMatrixRunner 的信号生成部分因前视偏差要求需要绕过
  4. 未来可重构 StrategyMatrixRunner.run_symbol 支持传入数据切片参数，但这是更大的变更，本次迭代不引入

- **决策结果 (P0)**: PortfolioBacktester._generate_signals 复用 STRATEGY_REGISTRY 直接调用策略函数，绕过 runner.run_symbol 的 store 读取。SignalRanker 和 CandidateSelector 完全复用。

- **困境描述 (P1b)**: spec 说"在 _write_weights 中新增 backtest_dd_status 字段"。但 _write_weights 函数体只是 `json.dump(report.groups)`，真正的字段构建在 _run_group。应该在哪里添加？

- **决策逻辑 (P1b)**: 在 `_run_group` 构建 weights_list 时添加 `backtest_dd_status` 字段。理由：
  1. _write_weights 是序列化函数，不应包含业务逻辑
  2. 在 _run_group 添加字段使 in-memory report 和 JSON 输出都包含该字段，下游消费方更灵活
  3. 与现有 `dd_constrained` bool 字段并列，一致性好
  4. spec 的"在 _write_weights 中新增"是结果导向（JSON 中要有此字段），不是实现位置约束

- **决策结果 (P1b)**: 在 _run_group 的 weights_list 构建中添加 `backtest_dd_status` 字段，值为 `'pass'` 或 `'dd_constrained'`，与现有 `dd_constrained` bool 一致。

- **困境描述 (P0.2)**: PortfolioBacktester 的 max_drawdown_pct 符号约定——正值还是负值？vectorbt 返回负值，但迭代 #2 已确定正值约定。

- **决策逻辑 (P0.2)**: 沿用迭代 #2 正值约定（0.0~100.0）。理由：
  1. 与 `matrix_backtest._portfolio_max_drawdown_from_results` 一致
  2. 与 `GroupBacktestResult.portfolio_max_drawdown` 一致
  3. dd_violation 判定 `max_dd > 20.0` 直观
  4. 避免引入新的符号约定差异

- **决策结果 (P0.2)**: `PortfolioBacktestResult.max_drawdown_pct` 返回正值百分数，与迭代 #2 决策一致。

- **困境描述 (P0.3)**: PortfolioBacktester.run() 的回测时间窗口——用近 1 年还是与 MatrixBacktest 一样 5 年？

- **决策逻辑 (P0.3)**: 近 1 年。理由：
  1. PortfolioBacktest 是验证组合层"近期"表现的工具，不是策略参数优化（MatrixBacktest 的职责）
  2. 1 年数据足以计算 Sharpe/Sortino/DD 等指标（252 个交易日）
  3. 与 Walk-Forward 最后一个验证期（6 个月）形成互补：WF 是样本外验证，PortfolioBacktest 是近期样本内验证
  4. 5 年回测会让早期信号对当前组合权重不具代表性（权重是离线优化的，会月度更新）

- **决策结果 (P0.3)**: main._run_reoptimize 中调用 PortfolioBacktester.run(start=today-365, end=today-1)，回测近 1 年数据。end 用 today-1 避免当日数据未结算。

---

### [2026-07-03 UTC] 迭代 #5 — metadata parity 实现位置 + pending order 刷新策略

- **困境描述 (P0-A)**: spec §4.1 提出统一线上与回测 signal indicators，建议 "抽出共享 metadata 构建方法"。实现位置有两种选择：
  - 解读 A: 作为 `StrategyMatrixRunner` 的实例方法 `_build_signal_indicators(self, meta, entry, weight)`，访问 `self._signal_valid_bars` 等实例状态
  - 解读 B: 作为 module-level function `build_matrix_signal_indicators(meta, entry, weight)`，无状态、可独立测试、可被任意模块（含 PortfolioBacktester）调用

- **涉及 AI Constitution 条款**:
  - L7: 验证流水线 — metadata parity 必须可独立测试
  - L5: 架构边界 — 减少模块间耦合
  - Constitution 决策权重矩阵：可测试性 > OOP 纯度

- **决策逻辑 (P0-A)**: 采用解读 B。理由：
  1. `PortfolioBacktester._generate_signals()` 不能调用 `StrategyMatrixRunner` 实例方法（防前视偏差要求 PortfolioBacktester 用切片数据，而 StrategyMatrixRunner.run_symbol 读全量 store 数据）。如果 metadata helper 是实例方法，PortfolioBacktester 仍需绕过它或构造伪实例，引入新耦合。
  2. helper 本身无状态（只读 meta + entry + weight），符合纯函数语义。
  3. module-level function 可在 `tests/test_signal_parity.py` 中直接单元测试，无需构造 StrategyMatrixRunner 实例。
  4. 默认值常量（`DEFAULT_BACKTEST_SHARPE` 等）也放 module-level，便于测试与文档引用。

- **决策结果 (P0-A)**: `build_matrix_signal_indicators()` 作为 module-level function 放在 `matrix_runner.py` 顶部，PortfolioBacktester 显式 import 调用。`StrategyMatrixRunner.run_symbol()` 内部也调用同一函数。

---

- **困境描述 (P0-B)**: spec §4.3 要求 `ScanOrchestrator._refresh_pending_orders()` 在扫描开始时刷新 pending。spec 明确"不要让刷新失败中断扫描；记录 warning"，但实现细节有两处选择：
  - 幂等性机制：在 orchestrator 内维护 `_processed_order_ids: set[str]` vs 查询 tracker 现有订单
  - 刷新失败的处理：返回 0 + warning vs 抛异常让上层处理

- **涉及 AI Constitution 条款**:
  - L8: 运行时故障处理策略 — 监控/执行链路不能因单个组件失败而崩溃
  - L7: 测试纪律 — 幂等性必须有测试覆盖
  - L1: 决策可解释 — 同一订单不应被 tracker 处理两次

- **决策逻辑 (P0-B)**:
  1. **幂等性**：使用 `_processed_order_ids: set[str]` 集合而非查询 tracker。理由：
     - tracker 当前不暴露 "已处理订单列表" 查询接口；新增查询接口会修改 PortfolioTracker 公共 API，超出本次 scope
     - 集合查找 O(1)，无性能问题
     - 集合在 orchestrator 实例生命周期内有效（一个 orchestrator 实例对应一次系统运行）��重启后会重置 — 但重启场景下 broker._submitted 也会重建，paper 账户的 FILLED 订单可由 reconciliation callback 兜底处理
  2. **刷新失败处理**：返回 0 + warning，不抛异常。理由：
     - spec 明确"不要让刷新失败中断扫描"
     - 扫描主流程（信号生成 → 风控 → 下单）与 pending 刷新是独立关注点，二者解耦更稳健
     - 下次扫描会再次尝试刷新，最终一致性可保证

  附带决策：refresh 只处理 PENDING → FILLED 转换，不处理 PENDING → CANCELLED/REJECTED。理由：
  - CANCELLED/REJECTED 不影响 tracker 持仓，无需 process_order
  - 减少代码复杂度
  - 如需观测 CANCELLED 状态，可从 broker.order_history 查询

- **决策结果 (P0-B)**:
  - `_processed_order_ids: set[str]` 在 ScanOrchestrator.__init__ 中初始化
  - `refresh_pending_orders()` 异常 → 返回 0 + logger.warning
  - broker 不支持 refresh_pending_orders（PaperBroker）→ 返回 0，不抛异常
  - 非 FILLED 状态的刷新结果不调用 tracker.process_order

---


### [2026-07-03 12:01 UTC] 迭代 #5 — 高风险文件触及

- **困境描述**: CodeBuddy 的代码变更触及了 Constitution L8 定义的高风险目录
- **涉及 AI Constitution 条款**: L8 高风险变更 / 禁止行为
- **决策逻辑**: Orchestrator 自动检测到合规风险
- **决策结果**: 需用户审批后才能合并
        - **详情**: mytrader/mytrader/execution/alpaca_broker.py
- **用户反馈**: 待用户确认

---
