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

### [2026-07-04 UTC] 迭代 #7 — SignalRanker 评分权重调整的边界判定

- **困境描述**: spec §7 将本次迭代评为"中风险"（修改 SignalRanker 评分逻辑会改变选股排名），但同时声明不属于"高风险变更"（高风险 = risk param / execution logic / validation thresholds）。需要在 L8 框架下判定：评分权重从 `backtest_sharpe` 切换为 `backtest_sortino + backtest_dd_penalty` 是否需要用户审批？

- **涉及 AI Constitution 条款**:
  - L1: Sortino 首要 KPI — 当前评分用 Sharpe 与 L1 不一致
  - L7: 测试纪律 — 评分切换需测试覆盖，避免静默回归
  - L8: 高风险变更定义 — 评分权重是否属于"risk param"？

- **决策逻辑**:
  1. **评分权重不属于 risk param**：risk param 指的是 DD 阈值（20%）、仓位上限（20%）、止损止盈等直接影响单笔交易风险的参数。评分权重是"选股排名的内部权重"，影响候选顺序但不直接决定下单数量或止损位。
  2. **评分权重不属于 execution logic**：execution logic 指的是 AlpacaBroker 下单、RiskManager 仓位计算等。SignalRanker 在执行链路之前，输出 RankedSignal 候选列表，由 CandidateSelector 决定是否执行。
  3. **评分权重不属于 validation thresholds**：validation thresholds 指的是 Walk-Forward DD 15%、Gate 1 Sortino 0.5 等流水线门槛。
  4. **结论**：评分权重调整属于"中风险"变更（影响选股排名但不触及风控参数），符合 L8 自动部署条件，但应在 decision_log 中记录。

- **决策结果**: 评分权重调整属于中风险变更，自动执行；记录到 decision_log；不触发真实交易（spec §3 明确）；测试通过后即可合并。

- **后续待办**:
  1. Meta-Agent 在验收阶段运行 `--reoptimize` 验证排名变化（spec §3 明确不在本次迭代内运行）
  2. 观察评分切换后 portfolio Sortino / DD 是否有显著变化
  3. 如有显著退化（Sortino < 1.5 或 DD > 12%），考虑回退或调整权重

---

### [2026-07-04 UTC] 迭代 #7 — benchmark 降级时的 alpha 语义

- **困境描述**: 当 SPY 数据不可用时，spec §4.2 要求所有 benchmark 字段降级为 0.0。但 `alpha_pct = portfolio_annualized - benchmark_annualized` 在 benchmark=0 时退化为 `portfolio_annualized`，这是否合理？

- **涉及 AI Constitution 条款**:
  - L1: KPI 必须可解释 — "alpha=15%" 在无 benchmark 时是否误导？
  - L7: 代码规范 — 降级语义应明确

- **决策逻辑**:
  1. **降级是合理的**：无 benchmark 时，"超额收益"概念不成立，但 `alpha = portfolio - 0 = portfolio` 在数学上等价于"绝对收益"，可作为降级信号
  2. **日志可识别**：`[PortfolioBacktest]` 日志会输出 `Benchmark(SPY) Return=0.00%`，运维人员看到 benchmark=0 即可判断降级发生
  3. **不抛异常**：spec §4.2 明确要求不抛异常，降级为 0.0 是 spec 要求
  4. **测试覆盖**：`test_benchmark_zero_when_no_spy` 显式验证 `alpha == portfolio_annualized_return_pct`，语义明确

- **决策结果**: 降级时 alpha = portfolio_annualized_return（语义为"绝对收益"），不抛异常，由日志和测试覆盖。

---

### [2026-07-04 UTC] 迭代 #8 — trend_period 参数网格固定为 [200]

- **困境描述**: `rsi_trend_filter` 策略的参数网格设计中，`trend_period`（SMA 趋势过滤周期）是否应纳入参数网格搜索。常见趋势周期有 50/100/200，全搜索（4 参数 3×3×3×3=81 组合）会大幅膨胀计算规模，但固定为 200 可能错过更优的趋势周期。

- **涉及 AI Constitution 条款**:
  - L9: Evolution — 系统应支持参数化迭代，不写死
  - L5: "为未来尚未确定的需求进行 over-engineering" — 禁止
  - Decision Weight Matrix: 实证优先 > 理论完备

- **决策逻辑**: 固定 `trend_period=200`，不纳入参数网格。理由：
  1. 200 日 SMA 是市场共识的趋势判定线（年线），无需网格搜索
  2. 50/100/200 的行为差异主要反映趋势时滞（越短越敏感，越长越滞后），不是策略品质差异——这不是需要搜索的"最优参数"，而是"你想跟踪多长周期的趋势"的策略选择
  3. 如果纳入搜索，81 个组合规模膨胀 3 倍（27 vs 81），ROI 低
  4. 如果后续实证发现 50/100 在特定波动率组中表现更好，可改为按组配置（group-based），而不是全局搜索

- **决策结果**: `REOPTIMIZE_PARAM_GRIDS["rsi_trend_filter"]` 中 `trend_period` 固定为 `[200]`。后续实证可扩展为按组配置。

---

### [2026-07-05 UTC] 迭代 #9 — Sortino > 0.5 门槛值选择 + 三级 Fallback 设计

- **困境描述**: 将 top-K 排序从 Sortino 改为 Alpha 后，需要决定是否保留 Sortino 作为过滤条件，以及门槛值取多少。同时需要决定当无候选通过门槛时的降级策略。

- **涉及 AI Constitution 条款**:
  - L1: KPI — Sortino 仍是 Constitution L1 首要 KPI，不能完全弃用
  - L5: 不过度工程 — 三级 fallback 是否过度复杂？
  - Decision Weight Matrix: 实证优先 > 理论完备

- **决策逻辑**:

  1. **保留 Sortino 作为过滤而非排序**：
     - Alpha 排序直接优化超额收益目标（年化 20-30%）
     - 但 Alpha 高不等于下行质量好（可能"高 alpha 高下行波动"）
     - Sortino > 0.5 作为最低质量门槛，排除垃圾策略
     - 这不违反 L1：Sortino 仍是 KPI，只是从"排序指标"变成"过滤指标"

  2. **门槛值 0.5 的依据**：
     - Sortino > 1.5 是优秀策略标准（design_v2 §5）
     - Sortino > 0.5 是"基本可用"的下限（低于 0.5 说明下行风险未被充分补偿）
     - 0.5 不是硬约束，而是 Tier 1 过滤条件；Tier 2 会放宽
     - 如实证发现 0.5 过严（排除太多候选），可调整为 0.3 或按组分配置

  3. **三级 Fallback 设计**：
     - Tier 1: DD ≤ 20% AND Sortino > 0.5 → Alpha 降序（理想路径）
     - Tier 2: 仅 DD ≤ 20% → Alpha 降序（放宽 Sortino，WARNING 日志）
     - Tier 3: DD 升序 → dd_constrained=True（DD fallback，与迭代 #3 一致）
     - 为什么不只用 Tier 1？因为 Sortino > 0.5 可能全部候选都不满足（如熊市期间），需要 fallback 保证回测不阻塞
     - 为什么不直接用 Tier 2？因为 Sortino 门槛在正常市场环境下能过滤垃圾策略
     - 三级设计在"严格性"和"鲁棒性"之间平衡

- **决策结果**: 
  - 保留 Sortino 作为过滤指标（门槛 0.5）
  - 三级 Fallback：Tier 1 严格 → Tier 2 放宽 Sortino → Tier 3 DD fallback
  - 门槛值 0.5 可配置（`MIN_SORTINO_THRESHOLD` 常量），后续实证可调整

---

### [2026-07-05 UTC] 迭代 #9 — SPY 降级时 alpha=0 的语义一致性

- **困境描述**: 当 SPY 数据不可用时，`_compute_alpha` 返回 0.0。所有候选 alpha=0 → 排序退化为原顺序。这与迭代 #7 的 PortfolioBacktest 降级决策一致，但需确认 MatrixBacktest 层的语义。

- **涉及 AI Constitution 条款**:
  - L7: 代码规范 — 降级语义应明确
  - L1: KPI 必须可解释

- **决策逻辑**:
  1. **与迭代 #7 一致**：PortfolioBacktest 在 SPY 不可用时 benchmark=0，alpha=portfolio_return。MatrixBacktest 层同理：alpha=0 表示"无法计算超额收益"
  2. **不抛异常**：spec §4.1 明确要求降级不阻塞回测
  3. **退化为原顺序**：Python `sorted` 是稳定排序，所有 alpha=0 时保持策略列表顺序（`strategies=["dual_ma", "rsi_mean_revert", ...]` 的顺序），这是可接受的降级
  4. **ensemble weights 退化**：`max(0, 0.01)` 归一化 → 等权，符合直觉
  5. **日志可识别**：`_get_spy_returns` 在 SPY 不可用时输出 WARNING

- **决策结果**: SPY 不可用时 alpha=0.0，所有候选 alpha 相等 → 稳定排序保留原顺序 → ensemble 退化为等权。与迭代 #7 降级策略一致。

---

### [2026-07-05 UTC] 迭代 #10 — _backtest_batch vbt 异常时的安全 fallback

- **困境描述**: `_backtest_batch` 用一次 `vbt.Portfolio.from_signals` 处理组内所有标的。如果 vbt 调用因数据问题（如全 NaN、shape 不一致）抛异常，整个组的回测会失败，阻塞 `--reoptimize`。spec §8 要求"回滚方案：如果 batch 版本数值不一致且无法修复，保留 `_backtest_one` 作为 fallback"。

- **涉及 AI Constitution 条款**:
  - L7: 验证流水线 — 回测不能因实现问题阻塞
  - L1: KPI 必须可解释 — 异常时不应静默失败
  - L8: 重大决策须通知 — 但 fallback 触发是降级而非"重大决策"，用 WARNING 日志即可

- **决策逻辑**:
  1. **保留 `_backtest_one` 函数**：不删除旧实现，作为 batch 失败时的 fallback
  2. **try/except 包裹 vbt 调用**：异常时退化为逐标的 `_backtest_one`，保证回测不中断
  3. **WARNING 日志**：`_backtest_batch vbt call failed: {e} — falling back to per-symbol _backtest_one`
  4. **不抛异常**：fallback 后返回与 batch 相同格式的 `list[SingleBacktestResult]`，调用方无感知
  5. **测试验证**：`test_batch_unknown_strategy` / `test_batch_empty_data` 等边界场景测试覆盖

- **决策结果**: 
  - 保留 `_backtest_one` 作为 fallback
  - `_backtest_batch` 在 vbt 异常时 WARNING + 退化为逐标的回测
  - 不阻塞 `--reoptimize`，不抛异常给上层
  - 数值一致性测试验证 batch 正常路径与 single 一致，fallback 路径天然一致（就是 single）

---

### [2026-07-05 UTC] 迭代 #10 — mock-based 测试的 patch 路径更新

- **困境描述**: `test_matrix_backtest.py` 中 4 个测试（`test_top_k_selection_uses_alpha` 等）用 `patch("mytrader.backtest.matrix_backtest._backtest_one")` 拦截回测函数返回受控结果。迭代 #10 将 `_run_group` 从调用 `_backtest_one` 改为调用 `_backtest_batch`，这些测试的 mock 失效。

- **涉及 AI Constitution 条款**:
  - L7: 测试纪律 — 测试不能因实现重构而失效
  - L1: KPI 可解释 — mock 应验证行为，不应与实现强耦合

- **决策逻辑**:
  1. **同步更新 mock**：将 `mock_backtest_one(df, strategy, params, ...)` 改为 `mock_backtest_batch(data, strategy_name, params, ...)`，返回 `list[SingleBacktestResult]`
  2. **保留测试意图**：测试验证的是 top-K 选择 / Alpha 排序 / Sortino 过滤等行为，不是回测实现细节
  3. **mock 签名匹配新函数**：`mock_backtest_batch(data, strategy_name, params, *args, **kwargs)` 返回列表，与 `_backtest_batch` 签名一致
  4. **不删除 `_backtest_one` 测试**：`test_backtest_one_with_open` 等直接测试 `_backtest_one` 的保留，验证单标的回测逻辑

- **决策结果**: 
  - 4 个 mock-based 测试从 patch `_backtest_one` 改为 patch `_backtest_batch`
  - mock 函数签名匹配 `_backtest_batch(data, strategy_name, params, ...)`
  - 测试意图保持不变（验证 Alpha 排序、Sortino 过滤等行���）
  - `_backtest_one` 的直接测试全部保留

- **经验教训**: mock 是实现耦合的，当被测函数的内部依赖改变时，mock 需要同步更新。未来应优先用真实数据测试（如 `test_batch_backtest.py` 的数值一致性测试），减少 mock 依赖。

---

### [2026-07-07 UTC] 迭代 #11 — 三处模糊决策（vbt API、阈值取值、mock 同步）

- **困境描述**: 实现健全性门槛时遇到三处需要判断的决策点：
  1. spec §4.2 提到的 vbt API `pf.trades.status_closed.count()` 在 vbt 1.0.0 不存在
  2. `DEGENERATE_NO_CLOSE_FRACTION` 阈值取 0.8 还是更低/更高
  3. 现有 mock-based 测试（`test_top_k_selection_uses_alpha` 等 4 处）的 `SingleBacktestResult` 构造默认 `closed_trades=0`，会触发新的健全性门槛误判

- **涉及 AI Constitution 条款**:
  - L1: KPI 可解释 — 健全性门槛是 KPI 之前的硬门槛
  - L7: 测试纪律 — 新增字段不应破坏现有测试
  - L9: 进化 — 门槛设计要考虑可调性（回滚/调整成本）

- **决策逻辑**:

  **决策 1: vbt API 用 `pf.trades.closed.count()`**
  - spec §4.2 已预见并要求实现者查证 vbt 1.0.0 实际 API
  - 用最小验证脚本确认：单标的 `pf.trades.closed.count()` 返回 int（已平仓交易数）；多标的 `pf[sym].trades.closed.count()` 返回 per-symbol int
  - 提取失败降级为 0（不抛异常），与 `_safe_float` 同保守语义
  - **不**用 `pf.trades.records_readable['Status'].value_counts()['Closed']`（DataFrame 路径，慢且类型不稳）

  **决策 2: 阈值取 0.8（保守）**
  - 0.8 = "近乎全部标的零平仓"才触发，给低频合法策略（如 monthly rebalance 每标的 2-3 笔）留缓冲
  - 边界：4/5=0.8 触发（>=）、3/5=0.6 不触发。spec §5.7 要求边界测试覆盖
  - 0.5/0.6 太激进：单只标的数据不足（刚上市）就可能牵连整组判定
  - 0.9/1.0 太宽松：5 标的里 1 笔 closed_trades 就能蒙混过关，拦不住 rsi_trend_filter 这种"少数熊市标的偶尔触发出场"的情形
  - 0.8 是经验值，可调（`DEGENERATE_NO_CLOSE_FRACTION` 常量），未来若发现误伤合法策略可上调

  **决策 3: 同步更新 mock 测试，显式传 `closed_trades`**
  - mock 的 `SingleBacktestResult(sym, strat, params, sharpe, ret, dd, win, trades, returns)` 默认 `closed_trades=0` → 触发健全性门槛 → 测试失败
  - 选项 A：改健全性门槛只对"多标的"生效（>=2）—— 这是 hack，破坏门槛语义
  - 选项 B：在 mock 中显式传 `closed_trades=<total_trades>` —— 反映"mock 假定策略闭环"的语义，正确
  - 选 B：4 处 mock 各加 `closed_trades=` kwarg，与 `total_trades` 同值
  - 同步更新 `test_batch_backtest.py::_assert_results_match` 加 `closed_trades` 一致性断言

- **决策结果**:
  - vbt API 用 `pf.trades.closed.count()`，单/多标的一致
  - `DEGENERATE_NO_CLOSE_FRACTION = 0.8`，注释说明阈值设计动机
  - 4 处 mock 测试显式传 `closed_trades`，`_assert_results_match` 加一致性断言
  - 全部 646 测试通过

- **经验教训**:
  - **spec 预见 API 差异是规范做法**：spec §4.2 明确写了"若 vbt API 名称不同，实现者需查 vbt 1.0.0 实际 API"，省去了与 spec 作者反复确认的成本
  - **保守阈值 + 边界测试**：取 0.8 而非 0.5/1.0，并在测试中覆盖 4/5=0.8 触发、3/5=0.6 不触发两个边界。阈值是可调常量，未来调整无需改逻辑
  - **mock 与实现耦合的代价再次验证**：Iter #10 的 decision_log 已记录此教训，Iter #11 再次遇到（新增字段 → mock 默认值触发新逻辑）。强化了"优先用真实数据测试"的原则

---

