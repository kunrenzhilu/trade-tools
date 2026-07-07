# 迭代 #4 Spec — Portfolio Backtest + 临时 Guardrail

> **日期**: 2026-07-02
> **状态**: spec（待开发）
> **前置**: 迭代 #3（DD 约束过滤 + Walk-Forward 4 轮）
> **决策来源**: GPT + DeepSeek 讨论反馈（`tmp/gpt_feedback.md`）
> **风险等级**: 中（新增模块，不改 risk/execution 逻辑）

---

## 1. 背景与问题

### 1.1 当前架构缺陷

```
现有 Pipeline:
  Strategy Matrix (per-group 回测)
    → strategy_weights.json
      → SignalRanker (跨组选 Top-2K)
        → CandidateSelector (风控约束选 Top-5)
          → 上线 ← ❌ 缺少验证层

应有 Pipeline:
  Strategy Matrix
    → strategy_weights.json
      → SignalRanker
        → CandidateSelector
          → ★ Portfolio Backtest ★  ← 新增
            → Portfolio DD ≤ 20% ?
              → Paper Trading
                → Live Trading
```

### 1.2 核心洞察（GPT 反馈）

1. **DD 约束位置错误**：DD≤20% 应约束**最终投资组合**（5 只股票组合），而非 per-group 等权组合（62 只等权）
2. **per-group DD 是 Risk Characteristic，不是 Constraint**：它是策略属性，不是组合合规判定
3. **per-group DD ≠ portfolio DD**：无理论保证方向。NDX_high_vol 62 只等权 DD=22%，但实盘只选 5 只，portfolio DD 可能 < 22% 也可能 > 22%
4. **选项 A/B/D 都是补丁**：在缺少 Portfolio Backtest 的情况下做约束，无理论依据
5. **正确做法**：补 Portfolio Backtest 层，用历史数据完整模拟 SignalRanker + CandidateSelector 选股，计算真正的 Portfolio DD

### 1.3 当前 per-group DD 处理

迭代 #3 已实现 `dd_constrained` 标记：若某组所有参数组合 DD > 20%，fallback 选 DD 最低的 top-K 并标记 `dd_constrained=True`。NDX_high_vol 是唯一超标组（22.22%），62 只高波动 NASDAQ 股的结构性问题。

---

## 2. 开发目标

### 2.1 P0: Portfolio Backtest 模块（新增）

**目标**：用历史数据完整模拟"SignalRanker + CandidateSelector → Top-5 持仓"的全链路，计算真正的 Portfolio DD/Sortino/Sharpe/年化收益。

**这是 Constitution L7 验证流水线中缺失的关键层**：
```
Backtest (≥5年) → Walk-Forward (4轮) → Portfolio Backtest (NEW) → Paper Trade → Live
```

### 2.2 P1: per-group DD 降级为 Risk Signal

**目标**：`dd_constrained` 不再阻塞 Gate 1，而是作为 Portfolio Construction 层的风险输入信号。

### 2.3 P2: 临时 Guardrail（可逆）

**目标**：在 Portfolio Backtest 完成前，增加一个简单可逆的风险护栏——限制来自 `dd_constrained=True` 组的总风险暴露（基于 ATR），而非固定数量限制。

---

## 3. 详细设计

### 3.1 Portfolio Backtest 模块

**新增文件**: `mytrader/mytrader/backtest/portfolio_backtest.py`

**核心类与函数**:

```python
@dataclass
class PortfolioBacktestConfig:
    """Portfolio Backtest 配置"""
    initial_capital: float = 100_000.0
    top_k: int = 5                    # 最终持仓数（与 SignalRanker 一致）
    candidates_multiplier: int = 2    # 候选倍数（与 SignalRanker 一致）
    max_single_position_pct: float = 0.20   # 与 CandidateSelector 一致
    max_total_exposure_pct: float = 0.80
    max_sector_exposure_pct: float = 0.40
    rebalance_freq: str = "daily"    # daily / weekly
    signal_valid_bars: int = 3        # 信号有效期（与 StrategyMatrixRunner 一致）

@dataclass
class PortfolioBacktestResult:
    """Portfolio Backtest 结果"""
    start_date: date
    end_date: date
    initial_capital: float
    final_equity: float
    total_return_pct: float
    annualized_return_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown_pct: float           # ← Constitution L1 硬约束
    calmar_ratio: float
    daily_returns: pd.Series          # 每日收益率序列
    equity_curve: pd.Series           # 净值曲线
    holdings_history: list[dict]      # 每日持仓快照
    dd_violation: bool                # max_drawdown_pct > 20.0
    # 按组的暴露统计
    group_exposure_history: list[dict]  # 每日各组的仓位占比

class PortfolioBacktester:
    """Portfolio Backtest 引擎

    模拟全链路：
    1. 每个交易日：StrategyMatrixRunner 用历史数据生成信号
    2. SignalRanker 聚合评分，输出 Top-2K 候选
    3. CandidateSelector 风控约束，选出 Top-5 下单
    4. 模拟持仓 + 换仓，计算组合净值
    5. 输出 Portfolio DD / Sortino / Sharpe / 年化收益
    """

    def __init__(
        self,
        store: MarketDataStore,
        universe: UniverseManager,
        weights_file: str | Path,
        config: PortfolioBacktestConfig | None = None,
    ) -> None: ...

    def run(
        self,
        start: date,
        end: date,
    ) -> PortfolioBacktestResult:
        """执行完整 Portfolio Backtest

        每日流程：
        1. 从 MarketDataStore 读取截至当日的历史数据
        2. StrategyMatrixRunner.run() 生成信号（用 strategy_weights.json）
        3. SignalRanker.rank() → Top-2K 候选
        4. CandidateSelector.select_orders_from_candidates() → Top-5 订单
        5. 模拟执行：卖掉不在新 Top-5 中的持仓，买入新选入的
        6. 更新组合净值

        返回 PortfolioBacktestResult，包含 Portfolio DD
        """
        ...
```

**关键设计决策**:

1. **复用现有组件**：StrategyMatrixRunner、SignalRanker、CandidateSelector 全部复用，不重写
2. **历史数据重放**：按日期遍历，每个交易日"假装"只知道截至当日的数据（防前视偏差）
3. **换仓成本**：考虑手续费和滑点（复用 matrix_backtest 中的 fees/slippage 参数）
4. **信号有效期**：signal_valid_bars=3（与实盘一致），过期信号丢弃
5. **sector_exposure**：CandidateSelector 已有 `max_sector_exposure_pct=0.40` 约束，Portfolio Backtest 中需提供 sector 信息（可从 symbol metadata 获取或简化为 group_id）

**输出**:
- `PortfolioBacktestResult` 结构化结果
- 日志中输出关键指标：Portfolio DD, Sortino, Sharpe, 年化收益, Calmar
- 若 DD > 20%，标记 `dd_violation=True` 并 WARNING

### 3.2 main.py 集成

在 `--reoptimize` 流程中，MatrixBacktest + Walk-Forward 之后，自动运行 Portfolio Backtest：

```python
# main.py::_run_reoptimize 中新增
# ... 已有 MatrixBacktest.run() + run_walk_forward() ...

# Portfolio Backtest（新增）
pb = PortfolioBacktester(
    store=store,
    universe=universe,
    weights_file="config/strategy_weights.json",
    config=PortfolioBacktestConfig(),
)
pb_result = pb.run(start=start_date, end=today)
logger.info(f"[Portfolio Backtest] DD={pb_result.max_drawdown_pct:.2f}%, "
            f"Sortino={pb_result.sortino_ratio:.2f}, "
            f"Sharpe={pb_result.sharpe_ratio:.2f}, "
            f"Annual Return={pb_result.annualized_return_pct:.1f}%, "
            f"DD Violation={'YES' if pb_result.dd_violation else 'NO'}")
```

### 3.3 per-group DD 降级

**修改文件**: `mytrader/mytrader/backtest/matrix_backtest.py`

1. `dd_constrained` 字段保留，语义不变（标记该组无 DD≤20% 合规候选）
2. `_run_group` 中的 fallback 逻辑保留（仍选 DD 最低的 top-K）
3. **移除**：Gate 1 判定中"per-group DD > 20% = FAIL"的逻辑
4. **改为**：per-group DD 作为 `strategy_weights.json` 中的 risk metadata 字段输出，供 Portfolio Backtest 和 CandidateSelector 参考

### 3.4 临时 Guardrail（P2）

**修改文件**: `mytrader/mytrader/risk/candidate_selector.py`

新增约束：**Volatility Budget Guardrail**

```python
# CandidateSelector 新增参数
max_vol_budget_pct: float = 0.25  # 组合总波动率预算

# 约束逻辑：对 dd_constrained=True 的组，
# 限制其持仓的 Σ(weight_i × ATR_i / close_i) ≤ max_vol_budget_pct
# 而非固定数量限制
```

**设计原则**（GPT 反馈）：
- 不限制"最多 2 只"——数量 ≠ 风险
- 限制的是**风险暴露**（ATR 加权），而非来源组
- 明确标注为临时措施，未来用 Risk Budget 替代
- 可逆：通过 config 参数 `max_vol_budget_pct` 控制，设为 None 可禁用

---

## 4. 测试计划

### 4.1 Portfolio Backtest 单元测试

| 测试 | 说明 |
|------|------|
| test_portfolio_backtest_basic | 基本流程：3 只标的 × 10 天数据，验证 equity_curve 和 daily_returns |
| test_portfolio_backtest_dd_calculation | 验证 max_drawdown_pct 计算正确（构造已知 DD 场景） |
| test_portfolio_backtest_rebalance | 验证换仓逻辑：Top-5 变化时正确卖出/买入 |
| test_portfolio_backtest_signal_expiry | 验证过期信号（>signal_valid_bars）被丢弃 |
| test_portfolio_backtest_dd_violation | 构造 DD>20% 场景，验证 dd_violation=True |
| test_portfolio_backtest_group_exposure | 验证 group_exposure_history 正确记录 |

### 4.2 临时 Guardrail 测试

| 测试 | 说明 |
|------|------|
| test_vol_budget_constraint | dd_constrained 组的 ATR 加权暴露超限时被拒绝 |
| test_vol_budget_disabled | max_vol_budget_pct=None 时约束不生效 |
| test_vol_budget_within_limit | 合规暴露通过 |

### 4.3 集成测试

| 测试 | 说明 |
|------|------|
| test_reoptimize_runs_portfolio_backtest | `--reoptimize` 后日志中出现 Portfolio Backtest 结果 |
| test_end_to_end_portfolio_dd | 用 mock 数据跑完整流程，验证 Portfolio DD 输出 |

---

## 5. Constitution 合规

### 5.1 L7 验证流水线更新

```
Backtest (≥5年)
  → Walk-Forward (4轮, 无单轮 >15% loss)
    → Portfolio Backtest (Portfolio DD ≤ 20%)  ← NEW
      → Paper Trade (≥1月)
        → Live
```

### 5.2 L1 DD 约束位置修正

| 之前 | 之后 |
|------|------|
| per-group DD ≤ 20% = Gate 1 阻塞 | per-group DD = risk metadata |
| NDX_high_vol DD 22% = Gate 1 FAIL | Portfolio DD ≤ 20% = Gate 1 检查项 |
| DD 约束在 Strategy Discovery 层 | DD 约束在 Portfolio Construction 层 |

### 5.3 L8 风险分级

| 变更 | 风险等级 | 理由 |
|------|---------|------|
| 新增 Portfolio Backtest 模块 | 低 | 新增模块，不改现有逻辑 |
| per-group DD 降级为 metadata | 低 | 不改策略选择逻辑，只改 Gate 判定语义 |
| 临时 Volatility Budget Guardrail | **中** | 修改 CandidateSelector 约束逻辑 |

**临时 Guardrail 的风险**：修改 `candidate_selector.py` 中的选股约束逻辑，属于执行逻辑变更（L8 高风险）。但因为有 `max_vol_budget_pct=None` 开关可禁用，且是临时措施，建议作为**用户审批后实施**的子任务。

---

## 6. 实施顺序

| 步骤 | 任务 | 依赖 | 预估时间 |
|------|------|------|---------|
| 1 | Portfolio Backtest 模块 + 测试 | 无 | CodeBuddy ~1h + 测试 |
| 2 | main.py 集成（--reoptimize 后自动运行） | 步骤 1 | 10 min |
| 3 | per-group DD 降级（移除 Gate 1 阻塞） | 步骤 1 验证后 | 10 min |
| 4 | 运行 --reoptimize + Portfolio Backtest | 步骤 1-3 | ~30 min 运行 |
| 5 | 分析 Portfolio DD 结果 | 步骤 4 | Meta-Agent 评估 |
| 6 | 临时 Guardrail（需用户审批后） | 步骤 5 结果 | ~30 min |

**步骤 1-3 可在一次 CodeBuddy 迭代中完成**，步骤 4-5 由 Meta-Agent 独立验证，步骤 6 根据结果决定是否需要。

---

## 7. 成功标准

1. `pytest` 全部通过，测试数 ≥ 498 + 8（新增）= 506
2. `--reoptimize` 运行后日志中出现 `[Portfolio Backtest]` 行，含 DD/Sortino/Sharpe/年化收益
3. `strategy_weights.json` 中 `dd_constrained` 字段保留作为 metadata
4. **关键指标**：Portfolio DD ≤ 20% → Gate 1 PASS；Portfolio DD > 20% → Gate 1 FAIL，需进一步处理
5. iteration_trajectory.md 更新
6. decision_log.md 更新（DD 约束位置变更属于架构决策）

---

## 8. 后续演进路线（GPT 建议，不在本次迭代）

| 阶段 | 目标 | 时间 |
|------|------|------|
| 短期 | Portfolio Backtest + 临时 Guardrail | 本次迭代 |
| 中期 | Risk Budget（目标波动率、相关性约束） | 下次迭代 |
| 长期 | 实时风险监控 + 自适应仓位 | 未来 |
