# Iteration #5 Spec — Paper Trading Integrity & Parity

> 日期：2026-07-03  
> Meta-Agent：GLM  
> 输入依据：`tmp/gpt_explore.md`、`alignment/ai_constitution.md`、`alignment/iteration_trajectory.md`、`.codebuddy/notes/experience.md`  
> 风险等级：高（触及 `execution` / paper 对账链路），但仅限 paper trading 完整性修复；不得触发 live 交易。  
> 核心目标：让 paper trading 产生的数据可信、可对账、可复盘，使后续一个月 paper 结果能用于判断策略与系统质量。

---

## 1. 背景

Iteration #4 补齐了 Portfolio Backtest，并记录组合层指标：

- Portfolio DD：6.65%
- Sortino：1.98
- Sharpe：1.33
- 年化收益：15.17%

但 2026-07-03 的系统审计发现：当前 paper trading 阶段仍存在链路可信度问题。主要问题不是策略验证层，而是线上 paper 链路与 PortfolioBacktest 不完全一致，订单生命周期和对账不闭环，导致 paper 运行一个月后也可能无法判断收益/回撤来自策略、执行、数据还是记录错误。

本次迭代只解决 **Paper Trading Integrity & Parity**，不做新策略、不改 DD 阈值、不引入 live 交易。

---

## 2. Problem Statement

### P0-A：线上扫描与 PortfolioBacktest 的信号语义不一致

当前 `StrategyMatrixRunner.run_symbol()` 生成的 `Signal.indicators` 缺少：

- `sector`
- `backtest_sortino`
- `backtest_max_drawdown`
- `backtest_dd_status`

而 `PortfolioBacktester._generate_signals()` 会写入 `sector`。`CandidateSelector` 使用 `sector` 做 `max_sector_exposure_pct` 约束，缺失时全部归为 `Unknown`。这会导致线上 paper approved 数量与 PortfolioBacktest 不一致。

部署报告中曾出现：`73 候选 → 2 approved`，高度疑似由 `sector=Unknown` 触发。

### P0-B：Alpaca paper 订单生命周期不闭环

当前 `AlpacaBroker._submit_auto()` 提交订单后只解析一次状态。若订单初始状态是 `new/accepted/pending_new`，返回 `PENDING`，而 `ScanOrchestrator` 只有 `FILLED` 才更新 `PortfolioTracker`。

结果：真实 Alpaca paper 账户可能已经成交，但本地 tracker 仍为空仓，风控状态失真。

### P0-C：对账 callback 与 `ReconciliationService` 接口不匹配

当前 `main.py::_build_reconciliation_callback()` 调用：

- `ReconciliationService(tracker=...)`
- `svc.reconcile()`
- `report.has_diff`

但实际实现是：

- `ReconciliationService(portfolio_tracker=...)`
- `svc.run()`
- `report.is_clean`

同时 `AlpacaBroker` 缺少 `get_positions()`，无法支撑真实 paper 持仓对账。

### P0-D：缺少 paper daily metrics 结构化归档

Paper 期间需要每日记录 account、signals、orders、positions、risk、data freshness，否则一个月后无法计算 paper Sortino/DD，也无法区分策略问题与系统问题。

---

## 3. Scope

### 本次要做

1. 统一线上 `StrategyMatrixRunner` 与 `PortfolioBacktester` 的 signal indicators 语义。
2. 增加 parity 测试，证明同一数据/权重下线上 runner 与 backtest signal metadata 一致。
3. 为 `AlpacaBroker` 增加只读/状态类能力：`get_positions()`、订单查询/刷新 pending 订单。
4. 修复 `main.py` reconciliation callback，确保调用 `ReconciliationService.run()` 并正确读取 `is_clean`。
5. 增加 paper daily metrics 模块，能生成一份结构化 JSON 日报。
6. 更新相关测试与文档/trajectory/decision_log。

### 本次不做

1. 不新增策略。
2. 不切换优化目标（Sharpe→Sortino）的大逻辑。
3. 不修改 Portfolio DD 20% 阈值。
4. 不触发 live 交易。
5. 不做实盘自动减仓 guardrail。
6. 不要求真实 Alpaca API 测试在默认 pytest 中执行；真实 API 只能作为 skip-by-default smoke/live 测试。
7. 不修 orchestrator harness 的假 passed 问题；该问题留给 Iteration #6。

---

## 4. Detailed Design

## 4.1 统一 Signal metadata

### 修改文件

- `mytrader/mytrader/strategy/matrix_runner.py`
- `mytrader/mytrader/backtest/portfolio_backtest.py`
- 测试文件：优先新增或扩展 `mytrader/tests/test_strategy_matrix_runner.py`、`mytrader/tests/test_portfolio_backtest.py` 或新增 `mytrader/tests/test_signal_parity.py`

### 设计

在 `StrategyMatrixRunner` 中抽出一个共享 metadata 构建方法，例如：

```python
def _build_signal_indicators(self, meta: Any, entry: dict[str, Any], weight: float) -> dict[str, Any]:
    return {
        "group_id": meta.group_id,
        "sector": getattr(meta, "sector", "Unknown") or "Unknown",
        "backtest_sharpe": entry.get("backtest_sharpe", 0.0),
        "backtest_sortino": entry.get("backtest_sortino", 0.0),
        "backtest_max_drawdown": entry.get("backtest_max_drawdown", 0.0),
        "backtest_dd_status": entry.get("backtest_dd_status", "unknown"),
        "backtest_win_rate": entry.get("backtest_win_rate", 0.0),
        "weight": weight,
    }
```

如不方便作为实例方法，可使用 module-level helper；但必须避免线上与 backtest 分叉。

### 兼容要求

- 缺字段时返回安全默认值，不抛异常。
- 不改变 `Signal` dataclass。
- 不改变策略输出语义。
- 不改变 `CandidateSelector` 的约束算法，只修正 metadata 输入。

### PortfolioBacktester 调整

`PortfolioBacktester._generate_signals()` 应复用同一 metadata 构建逻辑，或至少保证输出字段和默认值完全一致。

如需避免访问 private 方法，可将 helper 设计为 module-level function，例如：

```python
def build_matrix_signal_indicators(meta: Any, entry: dict[str, Any], weight: float) -> dict[str, Any]: ...
```

然后两处共同调用。

### 测试

新增测试：

1. `test_matrix_runner_signal_indicators_include_sector_and_backtest_risk_fields`
   - 构造 mock universe meta，含 `group_id` 和 `sector`。
   - 构造 weights entry，含 `backtest_sortino`、`backtest_max_drawdown`、`backtest_dd_status`。
   - 断言线上 runner 生成的 Signal indicators 包含完整字段。

2. `test_signal_metadata_defaults_are_safe`
   - weights entry 缺少新增字段时，断言默认值合理，不抛异常。

3. `test_portfolio_backtester_and_matrix_runner_metadata_parity`
   - 同一个 symbol、同一个 universe meta、同一个 weights entry，比较两条路径生成的 indicators key/value 是否一致。

4. `test_candidate_selector_no_longer_treats_all_online_candidates_as_unknown_sector`
   - 构造多个 sector 的 signals，断言 approved 数量不因全部 `Unknown` 被限制到 2 个。
   - 注意不要放宽 sector 风控，只验证 metadata 正确传入。

---

## 4.2 AlpacaBroker 订单状态与持仓读取

### 修改文件

- `mytrader/mytrader/execution/alpaca_broker.py`
- 测试文件：`mytrader/tests/test_alpaca_broker.py` 或现有 execution 测试

### 新增/修改接口

#### 4.2.1 `get_positions()`

增加：

```python
def get_positions(self) -> list[dict[str, Any]]:
    """读取 Alpaca 当前持仓，返回 ReconciliationService 兼容结构。"""
```

返回格式必须兼容 `ReconciliationService.run()`：

```python
[
    {"symbol": "AAPL", "quantity": 10},
    {"symbol": "MSFT", "quantity": 5},
]
```

兼容 Alpaca position 字段：

- `symbol`
- `qty`
- 可选 `market_value` / `avg_entry_price` 可放入返回 dict，但 `quantity` 必须存在。

#### 4.2.2 订单查询

增加：

```python
def get_order_by_client_order_id(self, client_order_id: str) -> OrderResult | None:
    """优先查询本地缓存；如果本地是 PENDING，尝试从 Alpaca 拉取最新状态。"""
```

实现要点：

- 如果 client 不支持对应 API，保守返回本地缓存并记录 warning/debug。
- 可尝试 Alpaca SDK 的 `get_order_by_client_id(client_order_id)`；如 API 名称不同，使用 `hasattr` 兼容 mock。
- 解析结果复用 `_parse_alpaca_order()`。
- 如果远端变为 `FILLED`，更新 `self._submitted[client_order_id]`。

#### 4.2.3 pending 刷新

增加：

```python
def refresh_pending_orders(self) -> list[OrderResult]:
    """刷新所有本地 PENDING 订单，返回刷新后的订单列表。"""
```

实现要点：

- 遍历 `self._submitted` 中 `status == OrderStatus.PENDING` 的订单。
- 调用 `get_order_by_client_order_id()`。
- 不提交新订单，不取消订单。
- 不触发 live 风险行为，只做状态同步。

### 测试

1. `test_get_positions_maps_alpaca_positions_to_reconciliation_format`
   - mock client `get_all_positions()` 返回对象/简单对象，含 `symbol`/`qty`。
   - 断言返回 `quantity` 为 int。

2. `test_refresh_pending_orders_updates_filled_order`
   - mock submit 后本地为 pending。
   - mock `get_order_by_client_id()` 返回 filled + filled_avg_price。
   - 断言本地缓存变 `FILLED`。

3. `test_get_order_by_client_order_id_falls_back_to_cache_when_remote_query_fails`
   - 远端异常时不崩溃，返回缓存。

---

## 4.3 ScanOrchestrator pending 成交同步

### 修改文件

- `mytrader/mytrader/scan_orchestrator.py`
- 测试文件：`mytrader/tests/test_scan_orchestrator.py`

### 设计

在扫描开始或结束时，如果 broker 支持 `refresh_pending_orders()`，刷新 pending，并对变为 `FILLED` 的订单调用 `PortfolioTracker.process_order()`。

建议新增内部方法：

```python
def _refresh_pending_orders(self) -> int:
    """刷新 broker pending 订单；对新变为 FILLED 的订单更新 tracker；返回 filled_count。"""
```

注意幂等性：

- 同一个 `OrderResult.client_order_id` 不应重复 `process_order()`。
- 如果 tracker 本身不提供订单去重，需要在 orchestrator 内维护 `_processed_order_ids: set[str]`，或查询 tracker 现有记录。
- 不要让刷新失败中断扫描；记录 warning。

调用位置：

- `morning_scan()` / `intraday_scan()` / `eod_check()` 开始前调用一次。
- 或 `_run_scan()` 开头调用一次。
- 本次不要求做后台 polling 线程。

### 测试

1. `test_refresh_pending_orders_processes_newly_filled_order_once`
   - mock broker 第一次返回 FILLED，第二次仍返回同一订单。
   - 断言 tracker.process_order 只调用一次。

2. `test_refresh_pending_orders_noop_when_broker_not_supported`
   - PaperBroker 或普通 mock 无方法时不抛异常。

3. `test_refresh_pending_orders_warning_but_scan_continues_on_broker_error`
   - broker refresh 抛异常，扫描仍继续。

---

## 4.4 修复 Reconciliation callback

### 修改文件

- `mytrader/main.py`
- 测试文件：可新增/扩展 `mytrader/tests/test_main_reconciliation.py`

### 设计

修复 `_build_reconciliation_callback()`：

- 构造参数：`portfolio_tracker=components.tracker`
- 调用：`report = svc.run()`
- 判断：`if not report.is_clean:`
- 无差异：输出 clean 日志与通知
- 有差异：输出 diff 日志与通知

兼容性要求：

- `components.notification` 可为 None。
- `components.bus` 可为 None。
- 对账失败不能让 scheduler 崩溃，但必须 logger.exception 或 logger.error 记录清楚。

### 测试

1. `test_reconciliation_callback_calls_service_run_with_correct_args`
   - monkeypatch `ReconciliationService`，断言收到 `portfolio_tracker`。

2. `test_reconciliation_callback_uses_is_clean_not_has_diff`
   - fake report 含 `is_clean`，不含 `has_diff`，callback 不应报错。

3. `test_reconciliation_callback_sends_clean_notification`
   - clean report 时 notification.send_message 被调用。

4. `test_reconciliation_callback_sends_diff_notification`
   - diffs 非空时内容包含 diff symbols。

---

## 4.5 Paper daily metrics

### 新增文件

建议新增：

- `mytrader/mytrader/monitor/paper_metrics.py`
- 测试：`mytrader/tests/test_paper_metrics.py`

### 数据结构

```python
@dataclass
class PaperDailyMetrics:
    date: str
    account: dict[str, Any]
    signals: dict[str, int]
    orders: dict[str, int]
    positions: dict[str, int]
    risk: dict[str, float]
    data: dict[str, Any]
```

或直接提供函数也可以；重点是结构化输出稳定。

### 函数接口

```python
def collect_paper_daily_metrics(
    *,
    broker: Any,
    tracker: Any,
    scan_summary: Any | None = None,
    data_status: dict[str, Any] | None = None,
    output_dir: str | Path = "reports/paper/daily",
    today: date | None = None,
) -> Path:
    """采集并写出 paper daily metrics JSON，返回文件路径。"""
```

### JSON 结构

必须至少包含：

```json
{
  "date": "YYYY-MM-DD",
  "account": {"equity": 0.0, "cash": 0.0, "buying_power": 0.0},
  "signals": {"raw": 0, "buy_candidates": 0, "sell": 0, "approved": 0},
  "orders": {"submitted": 0, "filled": 0, "pending": 0, "rejected": 0},
  "positions": {"local_count": 0, "broker_count": 0, "diff_count": 0},
  "risk": {"daily_return": 0.0, "rolling_dd": 0.0},
  "data": {"symbols": 0, "latest_bar": "YYYY-MM-DD"}
}
```

### 实现要求

- 缺 broker account API 时不要崩溃，填 0 或 `None`，同时记录 warning/debug。
- 写文件前创建目录。
- 使用 UTF-8、indent=2、ensure_ascii=False。
- 不把敏感 API key 写入 metrics。

### 集成

在 `main.py` reconciliation callback 或 EOD 流程中，至少调用一次 metrics 写出函数。优先放在 reconciliation callback 末尾，因为它是每日盘后流程。

如果集成成本过高，本次至少提供模块与测试，并在 callback 中 best-effort 调用。

### 测试

1. `test_collect_paper_daily_metrics_writes_json`
2. `test_metrics_no_credentials_or_account_api_does_not_crash`
3. `test_metrics_counts_order_statuses`
4. `test_metrics_does_not_include_sensitive_fields`

---

## 5. Documentation Requirements

必须更新：

1. `alignment/iteration_trajectory.md`
   - 记录 Iteration #5：目标、变更、测试结果、Experience Learned、后续建议。

2. `alignment/decision_log.md`
   - 记录至少两个决策：
     - 线上与 PortfolioBacktest metadata parity 的实现位置。
     - pending order 刷新策略（为何只刷新、不自动做额外交易）。

3. `.codebuddy/CODEBUDDY.md`
   - 如新增 `monitor/paper_metrics.py` 或 tests 数量变化，更新 session 3 的目录结构和测试数。
   - 若新增 paper metrics 报告位置，也更新相关说明。

4. 相关 design doc
   - 如果修改 `05-execution-engine.md` / `08-monitor-layer.md` / `12-strategy-matrix.md` 的语义，必须更新对应文档。
   - 至少更新 `mytrader/designs/design_v2/12-strategy-matrix.md` 中 Signal metadata 字段说明。
   - 至少更新 `mytrader/designs/design_v2/05-execution-engine.md` 中 Alpaca pending refresh / positions 读取说明。

---

## 6. Success Criteria

### 必须满足

1. 默认 pytest 通过；不得依赖真实 Alpaca API。
2. 新增/修改测试数不下降。
3. `StrategyMatrixRunner` 线上 signal indicators 包含完整 metadata：
   - `group_id`
   - `sector`
   - `backtest_sharpe`
   - `backtest_sortino`
   - `backtest_win_rate`
   - `backtest_max_drawdown`
   - `backtest_dd_status`
   - `weight`
4. PortfolioBacktester 与 StrategyMatrixRunner metadata parity 测试通过。
5. `AlpacaBroker.get_positions()` 返回 `ReconciliationService` 兼容格式。
6. pending order refresh 能把本地 cached pending 更新为 filled，并能被 orchestrator 幂等处理。
7. reconciliation callback 不再调用不存在的 `reconcile()` / `has_diff` / `tracker=`。
8. paper metrics JSON 能写出，且不含敏感字段。
9. 更新 trajectory / decision_log / CODEBUDDY / design docs。

### 明确禁止

1. 不得修改 `MAX_PORTFOLIO_DRAWDOWN_PCT=20.0` 或其它 DD 阈值。
2. 不得引入 RL、黑箱策略、深度学习策略。
3. 不得在测试中调用真实 broker 下单。
4. 不得把 API key、secret、token 写入日志或 metrics。
5. 不得删除 `.codebuddy` 目录。
6. 不得提交 git commit。

---

## 7. Recommended Implementation Order

1. 先改 `StrategyMatrixRunner` metadata helper，并让 PortfolioBacktester 复用。
2. 写 metadata parity 测试。
3. 实现 `AlpacaBroker.get_positions()` / order query / refresh pending，并写 mock tests。
4. 在 `ScanOrchestrator` 加 `_refresh_pending_orders()` 并写幂等测试。
5. 修复 `main.py` reconciliation callback，并写 callback tests。
6. 新增 `monitor/paper_metrics.py` 与 tests。
7. 更新文档。
8. 跑 targeted tests。
9. 跑默认 pytest。

---

## 8. Validation Commands

使用项目指定 Python：

```bash
cd /Users/rickouyang/Github/trade-tools/mytrader
/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_strategy_matrix_runner.py tests/test_portfolio_backtest.py tests/test_alpaca_broker.py tests/test_scan_orchestrator.py tests/test_main_reconciliation.py tests/test_paper_metrics.py -q
/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest -q
```

若默认 pytest 包含 live tests 或 pre-existing time-sensitive failure，必须在 summary 中明确区分：

- 本次新增/修改测试是否通过；
- 默认 unit tests 是否通过；
- live/pre-existing failures 是否与本次无关；
- 不得把 `exit_code != 0` 说成完全通过。
