Let
---
 me
---
 start by reading the spec
---
 file to understand the
---
 complete requirements for Iter
---
ation #
---
9.
---
{"file_path": "/Users/rickouyang/Github/trade-tools/mytrader/iterations/iteration_9/spec.md"}
---
<tool_use_error>File does not exist.</tool_use_error>
---
<tool_use_error>File does not exist.</tool_use_error>
---
{"command": "ls /Users/rickouyang/Github/trade-tools/mytrader/iterations/ 2>/dev/null && ls /Users/rickouyang/Github/trade-tools/mytrader/iterations/iteration_9/ 2>/dev/null", "description": "List iterations directory"}
---
List iterations directory
---
Command: ls /Users/rickouyang/Github/trade-tools/mytrader/iterations/ 2>/dev/null && ls /Users/rickouyang/Github/trade-tools/mytrader/iterations/iteration_9/ 2>/dev/null
Stdout: iteration_8

Stderr: (empty)
Exit Code: 1
Signal: (none)
---
Iteration
---
 
---
9 directory doesn't exist
---
 yet. Let me check
---
 iteration_8 to
---
 understand the pattern
---
.
---
{"command": "ls /Users/rickouyang/Github/trade-tools/mytrader/iterations/iteration_8/", "description": "List iteration 8 directory"}
---
List iteration 8 directory
---
Command: ls /Users/rickouyang/Github/trade-tools/mytrader/iterations/iteration_8/
Stdout: spec.md

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"file_path": "/Users/rickouyang/Github/trade-tools/mytrader/iterations/iteration_8/spec.md"}
---
   1→# Iteration #8 — Trend-Filtered Mean Reversion 策略
   2→
   3→> 日期：2026-07-04
   4→> 类型：策略新增
   5→> 状态：implemented
   6→
   7→## 1. 目标
   8→
   9→新增 **RSI Trend Filter** 策略（`rsi_trend_filter`），在经典 RSI 均值回归信号上叠加 200 日 SMA 趋势过滤，降低单边趋势中的逆势假信号风险。
  10→
  11→## 2. 策略设计
  12→
  13→### 信号规则
  14→
  15→| 条件 | 信号 |
  16→|------|------|
  17→| RSI < oversold **AND** close > SMA(200) | BUY (+1) — 上升趋势中的超卖 |
  18→| RSI > overbought **AND** close < SMA(200) | SELL (-1) — 下降趋势中的超买 |
  19→| 其他 | HOLD (0) |
  20→
  21→### 设计原则
  22→
  23→- RSI 均值回归在震荡市有效，但在单边趋势中会频繁逆势交易
  24→- 通过 200 日 SMA 趋势过滤：只有上升趋势中才做多超卖反弹，下降趋势中才做空超买回落
  25→- 严格 `shift(1)` 防前视偏差（同所有现有策略）
  26→
  27→### 参数
  28→
  29→| 参数 | 默认值 | 说明 |
  30→|------|--------|------|
  31→| `rsi_period` | 14 | RSI 计算周期 |
  32→| `oversold` | 30.0 | 超卖阈值 |
  33→| `overbought` | 70.0 | 超买阈值 |
  34→| `trend_period` | 200 | SMA 趋势过滤周期 |
  35→
  36→## 3. 实现清单
  37→
  38→### 3.1 新增文件
  39→
  40→- `mytrader/strategy/strategies/rsi_trend_filter.py` — 策略函数，`@register_strategy("rsi_trend_filter")`
  41→
  42→### 3.2 修改文件
  43→
  44→- `main.py` — `REOPTIMIZE_STRATEGIES` 新增 `"rsi_trend_filter"`，`REOPTIMIZE_PARAM_GRIDS` 新增参数网格
  45→- `tests/test_strategy.py` — 新增测试类 `TestRSITrendFilter`
  46→
  47→### 3.3 文档更新
  48→
  49→- `alignment/iteration_trajectory.md` — 记录迭代 #8
  50→- `.codebuddy/CODEBUDDY.md` — 更新策略列表 + 开发阶段 + 测试数
  51→
  52→## 4. 参数网格（MatrixBacktest）
  53→
  54→```python
  55→"rsi_trend_filter": {
  56→    "rsi_period": [7, 14, 21],
  57→    "oversold": [25, 30, 35],
  58→    "overbought": [65, 70, 75],
  59→    "trend_period": [200],
  60→}
  61→```
  62→
  63→说明：`trend_period` 固定为 200（经典长周期趋势线），不纳入网格搜索以控制搜索空间。
  64→
  65→## 5. 测试要求
  66→
  67→- 信号值域测试（`{ -1, 0, 1 }`）
  68→- 自定义参数测试
  69→- 前视偏差测试（通过 `TestNoLookaheadBias` 参数化自动覆盖）
  70→- 注册表测试（通过 `TestAllStrategiesQuality` 参数化自动覆盖）
  71→- 趋势过滤行为测试：上升趋势中不产生 SELL，下降趋势中不产生 BUY
  72→- 边界条件测试：数据不足 `trend_period` 条时的行为
  73→
  74→## 6. Scope
  75→
  76→- 仅新增策略，不修改现有策略/风控/执行逻辑
  77→- 不触发真实交易
  78→- 策略函数为纯函数（无副作用）
  79→
---
   1→# Iteration #8 — Trend-Filtered Mean Reversion 策略
   2→
   3→> 日期：2026-07-04
   4→> 类型：策略新增
   5→> 状态：implemented
   6→
   7→## 1. 目标
   8→
   9→新增 **RSI Trend Filter** 策略（`rsi_trend_filter`），在经典 RSI 均值回归信号上叠加 200 日 SMA 趋势过滤，降低单边趋势中的逆势假信号风险。
  10→
  11→## 2. 策略设计
  12→
  13→### 信号规则
  14→
  15→| 条件 | 信号 |
  16→|------|------|
  17→| RSI < oversold **AND** close > SMA(200) | BUY (+1) — 上升趋势中的超卖 |
  18→| RSI > overbought **AND** close < SMA(200) | SELL (-1) — 下降趋势中的超买 |
  19→| 其他 | HOLD (0) |
  20→
  21→### 设计原则
  22→
  23→- RSI 均值回归在震荡市有效，但在单边趋势中会频繁逆势交易
  24→- 通过 200 日 SMA 趋势过滤：只有上升趋势中才做多超卖反弹，下降趋势中才做空超买回落
  25→- 严格 `shift(1)` 防前视偏差（同所有现有策略）
  26→
  27→### 参数
  28→
  29→| 参数 | 默认值 | 说明 |
  30→|------|--------|------|
  31→| `rsi_period` | 14 | RSI 计算周期 |
  32→| `oversold` | 30.0 | 超卖阈值 |
  33→| `overbought` | 70.0 | 超买阈值 |
  34→| `trend_period` | 200 | SMA 趋势过滤周期 |
  35→
  36→## 3. 实现清单
  37→
  38→### 3.1 新增文件
  39→
  40→- `mytrader/strategy/strategies/rsi_trend_filter.py` — 策略函数，`@register_strategy("rsi_trend_filter")`
  41→
  42→### 3.2 修改文件
  43→
  44→- `main.py` — `REOPTIMIZE_STRATEGIES` 新增 `"rsi_trend_filter"`，`REOPTIMIZE_PARAM_GRIDS` 新增参数网格
  45→- `tests/test_strategy.py` — 新增测试类 `TestRSITrendFilter`
  46→
  47→### 3.3 文档更新
  48→
  49→- `alignment/iteration_trajectory.md` — 记录迭代 #8
  50→- `.codebuddy/CODEBUDDY.md` — 更新策略列表 + 开发阶段 + 测试数
  51→
  52→## 4. 参数网格（MatrixBacktest）
  53→
  54→```python
  55→"rsi_trend_filter": {
  56→    "rsi_period": [7, 14, 21],
  57→    "oversold": [25, 30, 35],
  58→    "overbought": [65, 70, 75],
  59→    "trend_period": [200],
  60→}
  61→```
  62→
  63→说明：`trend_period` 固定为 200（经典长周期趋势线），不纳入网格搜索以控制搜索空间。
  64→
  65→## 5. 测试要求
  66→
  67→- 信号值域测试（`{ -1, 0, 1 }`）
  68→- 自定义参数测试
  69→- 前视偏差测试（通过 `TestNoLookaheadBias` 参数化自动覆盖）
  70→- 注册表测试（通过 `TestAllStrategiesQuality` 参数化自动覆盖）
  71→- 趋势过滤行为测试：上升趋势中不产生 SELL，下降趋势中不产生 BUY
  72→- 边界条件测试：数据不足 `trend_period` 条时的行为
  73→
  74→## 6. Scope
  75→
  76→- 仅新增策略，不修改现有策略/风控/执行逻辑
  77→- 不触发真实交易
  78→- 策略函数为纯函数（无副作用）
  79→
---
The
---
 iteration
---
 
---
9 spec doesn't exist
---
.
---
 The user said
---
 "
---
按 iterations/iteration_
---
9/spec.md 进行开发
---
" (
---
develop
---
 according to iterations
---
/iteration_9/spec
---
.md). But the spec
---
 file doesn't exist.
---
 Let
---
 me check if
---
 there's any
---
 iteration_9 content
---
 elsewhere, or perhaps
---
 the user expects me to
---
 find
---
 it
---
.
---
 Let me search
---
 the
---
 code
---
base for any iteration
---
_9 content
---
.
---
iter
---
9 的
---
 spec 文
---
件不存在。让我检查
---
一下是否有其他名称
---
或位置的
---
文件
---
。
---
{"command": "find /Users/rickouyang/Github/trade-tools -name \"*iteration_9*\" -o -name \"*iter_9*\" 2>/dev/null | head -30", "description": "Find iteration 9 related files"}
---
Find iteration 9 related files
---
Command: find /Users/rickouyang/Github/trade-tools -name "*iteration_9*" -o -name "*iter_9*" 2>/dev/null | head -30
Stdout: /Users/rickouyang/Github/trade-tools/iterations/iteration_9

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"command": "ls /Users/rickouyang/Github/trade-tools/iterations/iteration_9/", "description": "List iteration 9 at trade-tools root"}
---
List iteration 9 at trade-tools root
---
Command: ls /Users/rickouyang/Github/trade-tools/iterations/iteration_9/
Stdout: spec.md

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"file_path": "/Users/rickouyang/Github/trade-tools/iterations/iteration_9/spec.md"}
---
   1→# Iteration #9 Spec — MatrixBacktest Alpha-Based Strategy Selection
   2→
   3→> 日期：2026-07-05
   4→> Meta-Agent：GLM
   5→> 输入依据：Iter #7 reoptimize（alpha=-11.34%）、Iter #8（rsi_trend_filter 未进入权重）、用户确认目标不变（年化 20-30%）
   6→> 风险等级：中（修改策略选择逻辑，不修改策略代码/风控/执行）
   7→> 核心目标：将 MatrixBacktest 的 top-K 策略选择从 Sortino 排序改为 Alpha 排序，使选出的策略直接优化超额收益
   8→
   9→---
  10→
  11→## 1. 背景
  12→
  13→Iter #7 的 reoptimize 暴露了根本矛盾：
  14→
  15→```
  16→Constitution 目标：年化 20-30%（需要 alpha +10~20%）
  17→MatrixBacktest 排序：Sortino 降序
  18→结果：选出 Sortino 最高的均值回归策略 → 年化 8.02% → alpha = -11.34%
  19→```
  20→
  21→**Sortino 高 ≠ 年化高。** 均值回归策略天然有高 Sortino（低下行波动）但低绝对收益。用 Sortino 排序会系统性地排除能跑赢 SPY 的趋势策略。
  22→
  23→Iter #8 新增的 `rsi_trend_filter` 也因此未能进入权重——它的 Sortino 低于纯 `rsi_mean_revert`。
  24→
  25→---
  26→
  27→## 2. Problem Statement
  28→
  29→### 当前代码流程（`matrix_backtest.py::_run_group`）
  30→
  31→1. **Per-strategy best params**：按 **Sharpe** 选每个策略的最优参数（line 785）
  32→2. **Top-K selection**：DD ≤ 20% 过滤 → 按 **Sortino** 降序取 top-K（line 830-833）
  33→3. **Ensemble weights**：按 **Sharpe** 归一化为权重（line 394）
  34→
  35→### 问题
  36→
  37→- Top-K 用 Sortino 排序 → 永远选均值回归 → alpha 为负
  38→- Per-strategy 用 Sharpe 选 params → 也偏好低波动 → 进一步偏向均值回归
  39→
  40→### 解决方案
  41→
  42→将 top-K 排序从 Sortino 改为 **Alpha**（策略年化收益 - SPY 同期年化收益）：
  43→- DD ≤ 20%：硬约束过滤（不变）
  44→- Sortino > 0.5：最低质量门槛（新增，排除垃圾策略）
  45→- **Alpha 降序**：排序指标（替换 Sortino）
  46→- Per-strategy best params：从 Sharpe 改为 Alpha（可选，建议同步改）
  47→
  48→---
  49→
  50→## 3. Scope
  51→
  52→### 本次要做
  53→
  54→1. 在 MatrixBacktest 中新增 SPY benchmark 数据获取和 alpha 计算
  55→2. 将 `_run_group` 的 top-K 排序从 Sortino 改为 Alpha
  56→3. 新增 Sortino > 0.5 作为最低质量过滤
  57→4. 在 `GroupBacktestResult` 和 `strategy_weights.json` 中新增 `backtest_alpha` 字段
  58→5. 将 per-strategy best params 选择从 Sharpe 改为 Alpha（保持一致性）
  59→6. 将 ensemble weights 计算从 Sharpe 改为 Alpha
  60→7. 新增/更新测试
  61→8. 更新设计文档和 trajectory
  62→
  63→### 本次不做
  64→
  65→1. 不修改任何策略代码（5 个策略文件不动）
  66→2. 不修改 SignalRanker / CandidateSelector / RiskManager
  67→3. 不修改 DD 阈值 / 仓位上限 / 止损止盈
  68→4. 不修改 AlpacaBroker / 下单逻辑
  69→5. 不运行 `--reoptimize`（由 Meta-Agent 验收时独立运行）
  70→6. 不触发真实交易
  71→
  72→---
  73→
  74→## 4. Detailed Design
  75→
  76→## 4.1 SPY Benchmark 数据获取
  77→
  78→### 新增方法
  79→
  80→在 `MatrixBacktest` 类中新增：
  81→
  82→```python
  83→def _get_spy_returns(self, start: date, end: date) -> pd.Series | None:
  84→    """获取 SPY 同期日收益率序列，用于计算 alpha。
  85→    
  86→    从 MarketDataStore 拉取 SPY 日线数据，计算日收益率。
  87→    如果 SPY 数据不可用，返回 None（alpha 降级为 0）。
  88→    """
  89→    try:
  90→        spy_bars = self._store.get_bars_multi(["SPY"], start, end)
  91→        spy_df = spy_bars.get("SPY")
  92→        if spy_df is None or spy_df.empty:
  93→            logger.warning("[MatrixBacktest] SPY data unavailable, alpha will be 0")
  94→            return None
  95→        spy_close = spy_df["close"].astype(float)
  96→        return spy_close.pct_change().dropna()
  97→    except Exception as e:
  98→        logger.warning(f"[MatrixBacktest] SPY benchmark fetch failed: {e}")
  99→        return None
 100→```
 101→
 102→### Alpha 计算
 103→
 104→```python
 105→def _compute_alpha(
 106→    strategy_daily_returns: pd.Series,
 107→    spy_daily_returns: pd.Series | None,
 108→) -> float:
 109→    """计算 alpha = 策略年化收益 - SPY 年化收益。
 110→    
 111→    如果 SPY 数据不可用，返回 0.0（降级）。
 112→    """
 113→    if spy_daily_returns is None or spy_daily_returns.empty:
 114→        return 0.0
 115→    
 116→    # 对齐时间索引
 117→    aligned = pd.concat([strategy_daily_returns, spy_daily_returns], 
 118→                        axis=1, join="inner").dropna()
 119→    if aligned.empty:
 120→        return 0.0
 121→    
 122→    strat_returns = aligned.iloc[:, 0]
 123→    spy_returns = aligned.iloc[:, 1]
 124→    
 125→    # 年化收益 = (1 + mean_daily)^252 - 1
 126→    strat_annual = (1 + strat_returns.mean()) ** 252 - 1
 127→    spy_annual = (1 + spy_returns.mean()) ** 252 - 1
 128→    
 129→    return (strat_annual - spy_annual) * 100  # 百分数
 130→```
 131→
 132→## 4.2 Top-K 选择逻辑修改
 133→
 134→### 当前代码（line 818-857）
 135→
 136→```python
 137→# 当前：DD 过滤 → Sortino 降序
 138→compliant = [c for c in candidates if c[4] <= MAX_PORTFOLIO_DRAWDOWN_PCT]
 139→if compliant:
 140→    ranked = sorted(compliant, key=lambda x: x[3], reverse=True)  # x[3] = Sortino
 141→```
 142→
 143→### 修改后
 144→
 145→```python
 146→# 新增：Sortino 最低质量门槛
 147→MIN_SORTINO_THRESHOLD = 0.5
 148→
 149→# 修改：DD 过滤 + Sortino 门槛 → Alpha 降序
 150→candidates_with_alpha = []
 151→for (strategy, params, results, pso, pdd) in candidates:
 152→    alpha = _compute_alpha(
 153→        _combine_daily_returns(results),
 154→        spy_returns,
 155→    )
 156→    candidates_with_alpha.append((strategy, params, results, pso, pdd, alpha))
 157→
 158→# 两级过滤：DD ≤ 20% AND Sortino > 0.5
 159→compliant = [
 160→    c for c in candidates_with_alpha
 161→    if c[4] <= MAX_PORTFOLIO_DRAWDOWN_PCT and c[3] > MIN_SORTINO_THRESHOLD
 162→]
 163→
 164→if compliant:
 165→    # Alpha 降序取 top-K
 166→    ranked = sorted(compliant, key=lambda x: x[5], reverse=True)  # x[5] = alpha
 167→    dd_constrained = False
 168→else:
 169→    # Fallback 1: 放宽 Sortino 门槛，只保留 DD 约束
 170→    dd_compliant = [c for c in candidates_with_alpha if c[4] <= MAX_PORTFOLIO_DRAWDOWN_PCT]
 171→    if dd_compliant:
 172→        ranked = sorted(dd_compliant, key=lambda x: x[5], reverse=True)
 173→        dd_constrained = False
 174→        logger.warning(f"[MatrixBacktest] {group_id}: Sortino filter relaxed (no candidate passed Sortino > {MIN_SORTINO_THRESHOLD})")
 175→    else:
 176→        # Fallback 2: 无 DD 合规候选 → 按 DD 升序（保持现有逻辑）
 177→        ranked = sorted(candidates_with_alpha, key=lambda x: x[4])
 178→        dd_constrained = True
 179→```
 180→
 181→## 4.3 Per-Strategy Best Params 修改
 182→
 183→### 当前代码（line 785）
 184→
 185→```python
 186→if ps > best_sharpe:  # 用 Sharpe 选 best params
 187→    best_sharpe = ps
 188→```
 189→
 190→### 修改后
 191→
 192→```python
 193→alpha = _compute_alpha(
 194→    _combine_daily_returns(results),
 195→    spy_returns,
 196→)
 197→if alpha > best_alpha:  # 用 Alpha 选 best params
 198→    best_alpha = alpha
 199→```
 200→
 201→## 4.4 Ensemble Weights 修改
 202→
 203→### 当前代码（line 390-398）
 204→
 205→```python
 206→sharpes = []
 207→for strategy, params, results in group_results:
 208→    ps = _portfolio_sharpe_from_results(results)
 209→    sharpes.append(max(ps, 0.01))
 210→total = sum(sharpes)
 211→weights = [s / total for s in sharpes]
 212→```
 213→
 214→### 修改后
 215→
 216→```python
 217→alphas = []
 218→for strategy, params, results in group_results:
 219→    alpha = _compute_alpha(_combine_daily_returns(results), spy_returns)
 220→    alphas.append(max(alpha, 0.01))  # 避免负权重
 221→total = sum(alphas)
 222→weights = [a / total for a in alphas]
 223→```
 224→
 225→## 4.5 新增字段
 226→
 227→### GroupBacktestResult
 228→
 229→```python
 230→@dataclass
 231→class GroupBacktestResult:
 232→    # ... 现有字段 ...
 233→    backtest_alpha: float = 0.0  # 新增：alpha vs SPY（百分数）
 234→```
 235→
 236→### strategy_weights.json
 237→
 238→每个权重条目新增：
 239→
 240→```json
 241→{
 242→    "strategy": "rsi_mean_revert",
 243→    "params": {...},
 244→    "weight": 0.5,
 245→    "backtest_sharpe": 1.03,
 246→    "backtest_sortino": 1.61,
 247→    "backtest_max_drawdown": 1.78,
 248→    "backtest_win_rate": 0.50,
 249→    "backtest_alpha": 2.35,  // ← 新增
 250→    "dd_constrained": false,
 251→    "backtest_dd_status": "pass"
 252→}
 253→```
 254→
 255→---
 256→
 257→## 5. 测试计划
 258→
 259→### 新增测试文件或扩展现有测试
 260→
 261→1. **test_compute_alpha_basic**：构造已知策略收益和 SPY 收益，验证 alpha 计算正确
 262→2. **test_compute_alpha_spy_unavailable**：SPY 数据为 None → alpha = 0.0
 263→3. **test_top_k_selection_uses_alpha**：构造 2 个候选，A 的 Sortino 高但 alpha 低，B 的 Sortino 低但 alpha 高 → B 应被选中
 264→4. **test_sortino_filter_excludes_garbage**：Sortino < 0.5 的候选被过滤
 265→5. **test_dd_filter_still_applies**：DD > 20% 的候选被过滤（不因 alpha 高而通过）
 266→6. **test_fallback_when_no_sortino_compliant**：所有候选 Sortino < 0.5 → 放宽 Sortino 门槛
 267→7. **test_fallback_when_no_dd_compliant**：所有候选 DD > 20% → 按 DD 升序（保持现有逻辑）
 268→8. **test_alpha_field_in_weights_json**：输出的 JSON 包含 `backtest_alpha` 字段
 269→9. **test_per_strategy_best_params_uses_alpha**：验证 params 选择从 Sharpe 改为 Alpha
 270→
 271→---
 272→
 273→## 6. Success Criteria
 274→
 275→1. `_run_group` 的 top-K 排序使用 Alpha（非 Sortino）
 276→2. DD ≤ 20% 硬约束保留
 277→3. Sortino > 0.5 最低质量门槛新增
 278→4. `strategy_weights.json` 每条目包含 `backtest_alpha` 字段
 279→5. SPY 数据不可用时 alpha 降级为 0（不崩溃）
 280→6. 默认 pytest 通过（585+ 测试，0 failed）
 281→7. 新增测试 ≥ 8 个
 282→8. 不修改策略代码 / 风控 / 执行逻辑
 283→9. 更新 trajectory / design docs / CODEBUDDY
 284→
 285→---
 286→
 287→## 7. Implementation Order
 288→
 289→1. 读 spec + `matrix_backtest.py` + `portfolio_backtest.py`（参考 benchmark 实现）+ `experience.md`
 290→2. 实现 `_get_spy_returns()` 和 `_compute_alpha()`
 291→3. 修改 `_run_group`：top-K 排序从 Sortino → Alpha + Sortino 门槛
 292→4. 修改 per-strategy best params：Sharpe → Alpha
 293→5. 修改 `_optimize_ensemble_weights`：Sharpe → Alpha
 294→6. 在 `GroupBacktestResult` 和 weights JSON 中新增 `backtest_alpha`
 295→7. 新增/更新测试
 296→8. 运行 targeted tests + 默认 pytest
 297→9. 更新 `designs/design_v2/07-backtest-module.md` + trajectory + CODEBUDDY
 298→
 299→---
 300→
 301→## 8. Risk Classification
 302→
 303→- **中风险**：修改策略选择逻辑会改变 `strategy_weights.json` 输出，影响后续 PortfolioBacktest 和实盘
 304→- **低风险**：SPY 数据获取是只读操作，不影响交易
 305→- **不触及**：策略代码 / risk / execution / portfolio 模块
 306→- **Constitution 合规**：Alpha 作为排序指标不违反 L1（Sortino 仍是 KPI，只是从排序变成过滤）；DD 硬约束不变
 307→
---
   1→# Iteration #9 Spec — MatrixBacktest Alpha-Based Strategy Selection
   2→
   3→> 日期：2026-07-05
   4→> Meta-Agent：GLM
   5→> 输入依据：Iter #7 reoptimize（alpha=-11.34%）、Iter #8（rsi_trend_filter 未进入权重）、用户确认目标不变（年化 20-30%）
   6→> 风险等级：中（修改策略选择逻辑，不修改策略代码/风控/执行）
   7→> 核心目标：将 MatrixBacktest 的 top-K 策略选择从 Sortino 排序改为 Alpha 排序，使选出的策略直接优化超额收益
   8→
   9→---
  10→
  11→## 1. 背景
  12→
  13→Iter #7 的 reoptimize 暴露了根本矛盾：
  14→
  15→```
  16→Constitution 目标：年化 20-30%（需要 alpha +10~20%）
  17→MatrixBacktest 排序：Sortino 降序
  18→结果：选出 Sortino 最高的均值回归策略 → 年化 8.02% → alpha = -11.34%
  19→```
  20→
  21→**Sortino 高 ≠ 年化高。** 均值回归策略天然有高 Sortino（低下行波动）但低绝对收益。用 Sortino 排序会系统性地排除能跑赢 SPY 的趋势策略。
  22→
  23→Iter #8 新增的 `rsi_trend_filter` 也因此未能进入权重——它的 Sortino 低于纯 `rsi_mean_revert`。
  24→
  25→---
  26→
  27→## 2. Problem Statement
  28→
  29→### 当前代码流程（`matrix_backtest.py::_run_group`）
  30→
  31→1. **Per-strategy best params**：按 **Sharpe** 选每个策略的最优参数（line 785）
  32→2. **Top-K selection**：DD ≤ 20% 过滤 → 按 **Sortino** 降序取 top-K（line 830-833）
  33→3. **Ensemble weights**：按 **Sharpe** 归一化为权重（line 394）
  34→
  35→### 问题
  36→
  37→- Top-K 用 Sortino 排序 → 永远选均值回归 → alpha 为负
  38→- Per-strategy 用 Sharpe 选 params → 也偏好低波动 → 进一步偏向均值回归
  39→
  40→### 解决方案
  41→
  42→将 top-K 排序从 Sortino 改为 **Alpha**（策略年化收益 - SPY 同期年化收益）：
  43→- DD ≤ 20%：硬约束过滤（不变）
  44→- Sortino > 0.5：最低质量门槛（新增，排除垃圾策略）
  45→- **Alpha 降序**：排序指标（替换 Sortino）
  46→- Per-strategy best params：从 Sharpe 改为 Alpha（可选，建议同步改）
  47→
  48→---
  49→
  50→## 3. Scope
  51→
  52→### 本次要做
  53→
  54→1. 在 MatrixBacktest 中新增 SPY benchmark 数据获取和 alpha 计算
  55→2. 将 `_run_group` 的 top-K 排序从 Sortino 改为 Alpha
  56→3. 新增 Sortino > 0.5 作为最低质量过滤
  57→4. 在 `GroupBacktestResult` 和 `strategy_weights.json` 中新增 `backtest_alpha` 字段
  58→5. 将 per-strategy best params 选择从 Sharpe 改为 Alpha（保持一致性）
  59→6. 将 ensemble weights 计算从 Sharpe 改为 Alpha
  60→7. 新增/更新测试
  61→8. 更新设计文档和 trajectory
  62→
  63→### 本次不做
  64→
  65→1. 不修改任何策略代码（5 个策略文件不动）
  66→2. 不修改 SignalRanker / CandidateSelector / RiskManager
  67→3. 不修改 DD 阈值 / 仓位上限 / 止损止盈
  68→4. 不修改 AlpacaBroker / 下单逻辑
  69→5. 不运行 `--reoptimize`（由 Meta-Agent 验收时独立运行）
  70→6. 不触发真实交易
  71→
  72→---
  73→
  74→## 4. Detailed Design
  75→
  76→## 4.1 SPY Benchmark 数据获取
  77→
  78→### 新增方法
  79→
  80→在 `MatrixBacktest` 类中新增：
  81→
  82→```python
  83→def _get_spy_returns(self, start: date, end: date) -> pd.Series | None:
  84→    """获取 SPY 同期日收益率序列，用于计算 alpha。
  85→    
  86→    从 MarketDataStore 拉取 SPY 日线数据，计算日收益率。
  87→    如果 SPY 数据不可用，返回 None（alpha 降级为 0）。
  88→    """
  89→    try:
  90→        spy_bars = self._store.get_bars_multi(["SPY"], start, end)
  91→        spy_df = spy_bars.get("SPY")
  92→        if spy_df is None or spy_df.empty:
  93→            logger.warning("[MatrixBacktest] SPY data unavailable, alpha will be 0")
  94→            return None
  95→        spy_close = spy_df["close"].astype(float)
  96→        return spy_close.pct_change().dropna()
  97→    except Exception as e:
  98→        logger.warning(f"[MatrixBacktest] SPY benchmark fetch failed: {e}")
  99→        return None
 100→```
 101→
 102→### Alpha 计算
 103→
 104→```python
 105→def _compute_alpha(
 106→    strategy_daily_returns: pd.Series,
 107→    spy_daily_returns: pd.Series | None,
 108→) -> float:
 109→    """计算 alpha = 策略年化收益 - SPY 年化收益。
 110→    
 111→    如果 SPY 数据不可用，返回 0.0（降级）。
 112→    """
 113→    if spy_daily_returns is None or spy_daily_returns.empty:
 114→        return 0.0
 115→    
 116→    # 对齐时间索引
 117→    aligned = pd.concat([strategy_daily_returns, spy_daily_returns], 
 118→                        axis=1, join="inner").dropna()
 119→    if aligned.empty:
 120→        return 0.0
 121→    
 122→    strat_returns = aligned.iloc[:, 0]
 123→    spy_returns = aligned.iloc[:, 1]
 124→    
 125→    # 年化收益 = (1 + mean_daily)^252 - 1
 126→    strat_annual = (1 + strat_returns.mean()) ** 252 - 1
 127→    spy_annual = (1 + spy_returns.mean()) ** 252 - 1
 128→    
 129→    return (strat_annual - spy_annual) * 100  # 百分数
 130→```
 131→
 132→## 4.2 Top-K 选择逻辑修改
 133→
 134→### 当前代码（line 818-857）
 135→
 136→```python
 137→# 当前：DD 过滤 → Sortino 降序
 138→compliant = [c for c in candidates if c[4] <= MAX_PORTFOLIO_DRAWDOWN_PCT]
 139→if compliant:
 140→    ranked = sorted(compliant, key=lambda x: x[3], reverse=True)  # x[3] = Sortino
 141→```
 142→
 143→### 修改后
 144→
 145→```python
 146→# 新增：Sortino 最低质量门槛
 147→MIN_SORTINO_THRESHOLD = 0.5
 148→
 149→# 修改：DD 过滤 + Sortino 门槛 → Alpha 降序
 150→candidates_with_alpha = []
 151→for (strategy, params, results, pso, pdd) in candidates:
 152→    alpha = _compute_alpha(
 153→        _combine_daily_returns(results),
 154→        spy_returns,
 155→    )
 156→    candidates_with_alpha.append((strategy, params, results, pso, pdd, alpha))
 157→
 158→# 两级过滤：DD ≤ 20% AND Sortino > 0.5
 159→compliant = [
 160→    c for c in candidates_with_alpha
 161→    if c[4] <= MAX_PORTFOLIO_DRAWDOWN_PCT and c[3] > MIN_SORTINO_THRESHOLD
 162→]
 163→
 164→if compliant:
 165→    # Alpha 降序取 top-K
 166→    ranked = sorted(compliant, key=lambda x: x[5], reverse=True)  # x[5] = alpha
 167→    dd_constrained = False
 168→else:
 169→    # Fallback 1: 放宽 Sortino 门槛，只保留 DD 约束
 170→    dd_compliant = [c for c in candidates_with_alpha if c[4] <= MAX_PORTFOLIO_DRAWDOWN_PCT]
 171→    if dd_compliant:
 172→        ranked = sorted(dd_compliant, key=lambda x: x[5], reverse=True)
 173→        dd_constrained = False
 174→        logger.warning(f"[MatrixBacktest] {group_id}: Sortino filter relaxed (no candidate passed Sortino > {MIN_SORTINO_THRESHOLD})")
 175→    else:
 176→        # Fallback 2: 无 DD 合规候选 → 按 DD 升序（保持现有逻辑）
 177→        ranked = sorted(candidates_with_alpha, key=lambda x: x[4])
 178→        dd_constrained = True
 179→```
 180→
 181→## 4.3 Per-Strategy Best Params 修改
 182→
 183→### 当前代码（line 785）
 184→
 185→```python
 186→if ps > best_sharpe:  # 用 Sharpe 选 best params
 187→    best_sharpe = ps
 188→```
 189→
 190→### 修改后
 191→
 192→```python
 193→alpha = _compute_alpha(
 194→    _combine_daily_returns(results),
 195→    spy_returns,
 196→)
 197→if alpha > best_alpha:  # 用 Alpha 选 best params
 198→    best_alpha = alpha
 199→```
 200→
 201→## 4.4 Ensemble Weights 修改
 202→
 203→### 当前代码（line 390-398）
 204→
 205→```python
 206→sharpes = []
 207→for strategy, params, results in group_results:
 208→    ps = _portfolio_sharpe_from_results(results)
 209→    sharpes.append(max(ps, 0.01))
 210→total = sum(sharpes)
 211→weights = [s / total for s in sharpes]
 212→```
 213→
 214→### 修改后
 215→
 216→```python
 217→alphas = []
 218→for strategy, params, results in group_results:
 219→    alpha = _compute_alpha(_combine_daily_returns(results), spy_returns)
 220→    alphas.append(max(alpha, 0.01))  # 避免负权重
 221→total = sum(alphas)
 222→weights = [a / total for a in alphas]
 223→```
 224→
 225→## 4.5 新增字段
 226→
 227→### GroupBacktestResult
 228→
 229→```python
 230→@dataclass
 231→class GroupBacktestResult:
 232→    # ... 现有字段 ...
 233→    backtest_alpha: float = 0.0  # 新增：alpha vs SPY（百分数）
 234→```
 235→
 236→### strategy_weights.json
 237→
 238→每个权重条目新增：
 239→
 240→```json
 241→{
 242→    "strategy": "rsi_mean_revert",
 243→    "params": {...},
 244→    "weight": 0.5,
 245→    "backtest_sharpe": 1.03,
 246→    "backtest_sortino": 1.61,
 247→    "backtest_max_drawdown": 1.78,
 248→    "backtest_win_rate": 0.50,
 249→    "backtest_alpha": 2.35,  // ← 新增
 250→    "dd_constrained": false,
 251→    "backtest_dd_status": "pass"
 252→}
 253→```
 254→
 255→---
 256→
 257→## 5. 测试计划
 258→
 259→### 新增测试文件或扩展现有测试
 260→
 261→1. **test_compute_alpha_basic**：构造已知策略收益和 SPY 收益，验证 alpha 计算正确
 262→2. **test_compute_alpha_spy_unavailable**：SPY 数据为 None → alpha = 0.0
 263→3. **test_top_k_selection_uses_alpha**：构造 2 个候选，A 的 Sortino 高但 alpha 低，B 的 Sortino 低但 alpha 高 → B 应被选中
 264→4. **test_sortino_filter_excludes_garbage**：Sortino < 0.5 的候选被过滤
 265→5. **test_dd_filter_still_applies**：DD > 20% 的候选被过滤（不因 alpha 高而通过）
 266→6. **test_fallback_when_no_sortino_compliant**：所有候选 Sortino < 0.5 → 放宽 Sortino 门槛
 267→7. **test_fallback_when_no_dd_compliant**：所有候选 DD > 20% → 按 DD 升序（保持现有逻辑）
 268→8. **test_alpha_field_in_weights_json**：输出的 JSON 包含 `backtest_alpha` 字段
 269→9. **test_per_strategy_best_params_uses_alpha**：验证 params 选择从 Sharpe 改为 Alpha
 270→
 271→---
 272→
 273→## 6. Success Criteria
 274→
 275→1. `_run_group` 的 top-K 排序使用 Alpha（非 Sortino）
 276→2. DD ≤ 20% 硬约束保留
 277→3. Sortino > 0.5 最低质量门槛新增
 278→4. `strategy_weights.json` 每条目包含 `backtest_alpha` 字段
 279→5. SPY 数据不可用时 alpha 降级为 0（不崩溃）
 280→6. 默认 pytest 通过（585+ 测试，0 failed）
 281→7. 新增测试 ≥ 8 个
 282→8. 不修改策略代码 / 风控 / 执行逻辑
 283→9. 更新 trajectory / design docs / CODEBUDDY
 284→
 285→---
 286→
 287→## 7. Implementation Order
 288→
 289→1. 读 spec + `matrix_backtest.py` + `portfolio_backtest.py`（参考 benchmark 实现）+ `experience.md`
 290→2. 实现 `_get_spy_returns()` 和 `_compute_alpha()`
 291→3. 修改 `_run_group`：top-K 排序从 Sortino → Alpha + Sortino 门槛
 292→4. 修改 per-strategy best params：Sharpe → Alpha
 293→5. 修改 `_optimize_ensemble_weights`：Sharpe → Alpha
 294→6. 在 `GroupBacktestResult` 和 weights JSON 中新增 `backtest_alpha`
 295→7. 新增/更新测试
 296→8. 运行 targeted tests + 默认 pytest
 297→9. 更新 `designs/design_v2/07-backtest-module.md` + trajectory + CODEBUDDY
 298→
 299→---
 300→
 301→## 8. Risk Classification
 302→
 303→- **中风险**：修改策略选择逻辑会改变 `strategy_weights.json` 输出，影响后续 PortfolioBacktest 和实盘
 304→- **低风险**：SPY 数据获取是只读操作，不影响交易
 305→- **不触及**：策略代码 / risk / execution / portfolio 模块
 306→- **Constitution 合规**：Alpha 作为排序指标不违反 L1（Sortino 仍是 KPI，只是从排序变成过滤）；DD 硬约束不变
 307→
---
Now
---
 I
---
 have a complete
---
 understanding of
---
 the spec. Let me
---
 create a task list and
---
 start implementing.
---
 First
---
, let me read
---
 the existing
---
 matrix
---
_backtest.py,
---
 portfolio_backtest.py for
---
 reference, and check
---
 experience
---
.md if
---
 it exists.
---
我已经
---
阅读了规范。让我
---
创建
---
一个任务列表并开始
---
阅读
---
相关的
---
代码
---
文件。
---
{"activeForm": "Reading matrix_backtest.py and portfolio_backtest.py", "description": "Read matrix_backtest.py to understand _run_group, _optimize_ensemble_weights, GroupBacktestResult; Read portfolio_backtest.py to reference SPY benchmark implementation; Check experience.md if exists", "subject": "Read matrix_backtest.py and portfolio_backtest.py"}
---
Task #1 created successfully: Read matrix_backtest.py and portfolio_backtest.py
---
Task #1 created successfully: Read matrix_backtest.py and portfolio_backtest.py
---
{"activeForm": "Implementing _get_spy_returns and _compute_alpha", "description": "Add _get_spy_returns() method to fetch SPY daily returns from MarketDataStore, and _compute_alpha() helper to compute annualized alpha", "subject": "Implement SPY benchmark fetch and alpha calculation"}
---
Task #2 created successfully: Implement SPY benchmark fetch and alpha calculation
---
Task #2 created successfully: Implement SPY benchmark fetch and alpha calculation
---
{"activeForm": "Modifying _run_group top-K selection", "description": "Modify _run_group: top-K sort from Sortino → Alpha; Add Sortino > 0.5 minimum quality filter; Preserve DD ≤ 20% hard constraint with 2-tier fallback", "subject": "Modify _run_group: Sortino→Alpha + Sortino threshold"}
---
Task #3 created successfully: Modify _run_group: Sortino→Alpha + Sortino threshold
---
Task #3 created successfully: Modify _run_group: Sortino→Alpha + Sortino threshold
---
{"activeForm": "Modifying per-strategy best params and ensemble weights", "description": "Change per-strategy best params selection from Sharpe to Alpha; Change ensemble weights from Sharpe to Alpha", "subject": "Modify per-strategy best params + ensemble weights to Alpha"}
---
Task #4 created successfully: Modify per-strategy best params + ensemble weights to Alpha
---
Task #4 created successfully: Modify per-strategy best params + ensemble weights to Alpha
---
{"activeForm": "Adding backtest_alpha field to GroupBacktestResult and weights JSON", "description": "Add backtest_alpha field to GroupBacktestResult dataclass and strategy_weights.json output", "subject": "Add backtest_alpha field to GroupBacktestResult + JSON"}
---
Task #5 created successfully: Add backtest_alpha field to GroupBacktestResult + JSON
---
Task #5 created successfully: Add backtest_alpha field to GroupBacktestResult + JSON
---
{"activeForm": "Writing tests for alpha-based selection", "description": "Write ≥8 tests covering: alpha calc basic, SPY unavailable, top-k uses alpha, sortino filter, dd filter, fallback scenarios, alpha field in JSON, per-strategy best params uses alpha", "subject": "Write tests for alpha-based selection"}
---
Task #6 created successfully: Write tests for alpha-based selection
---
Task #6 created successfully: Write tests for alpha-based selection
---
{"activeForm": "Running tests and updating docs", "description": "Run targeted tests + default pytest; Update trajectory, design docs, CODEBUDDY.md", "subject": "Run tests + update docs"}
---
Task #7 created successfully: Run tests + update docs
---
Task #7 created successfully: Run tests + update docs
---
{"status": "in_progress", "taskId": "1"}
---
Updated task #1 status
---
Updated task #1 status
---
{"file_path": "/Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py"}
---
   1→"""MatrixBacktest — 矩阵回测核心。
   2→
   3→N 策略 × G 标的组 × 参数网格 → strategy_weights.json
   4→
   5→关键设计：
   6→    1. 组合 Sharpe 计算：等权合并组内日收益率序列，而非算术平均各标的 Sharpe
   7→    2. 历史分组：每个回测时间点用 point-in-time 波动率分组（非当前静态分组）
   8→    3. open 参数：所有回测传 open=data["open"]，与实盘开盘价执行一致
   9→    4. ensemble 语义：权重优化在"单点离散值加权投票"语义下进行，与实盘 run_symbol 一致
  10→"""
  11→
  12→from __future__ import annotations
  13→
  14→import itertools
  15→import json
  16→from dataclasses import dataclass, field
  17→from datetime import date, timedelta
  18→from pathlib import Path
  19→from typing import Any
  20→
  21→import numpy as np
  22→import pandas as pd
  23→import vectorbt as vbt
  24→from loguru import logger
  25→
  26→from mytrader.data.store.market_data_store import MarketDataStore
  27→from mytrader.strategy.registry import STRATEGY_REGISTRY
  28→from mytrader.universe.manager import UniverseManager
  29→
  30→
  31→# ---------------------------------------------------------------------------
  32→# 常量
  33→# ---------------------------------------------------------------------------
  34→
  35→# Constitution L1 硬约束：portfolio 最大回撤 ≤ 20%
  36→# _run_group 在 top-K 选择时按此阈值过滤合规候选（迭代 #3 新增）
  37→MAX_PORTFOLIO_DRAWDOWN_PCT: float = 20.0
  38→
  39→# Constitution L7 Walk-Forward 门槛：单轮验证期 portfolio DD ≤ 15%
  40→# （低于 L1 的 20% 线，给样本外留缓冲）
  41→WALK_FORWARD_VAL_DD_THRESHOLD: float = 15.0
  42→
  43→
  44→# ---------------------------------------------------------------------------
  45→# 数据结构
  46→# ---------------------------------------------------------------------------
  47→
  48→@dataclass
  49→class SingleBacktestResult:
  50→    """单只标的单策略回测结果。"""
  51→
  52→    symbol: str
  53→    strategy: str
  54→    params: dict
  55→    sharpe: float
  56→    total_return_pct: float
  57→    max_drawdown_pct: float
  58→    win_rate_pct: float
  59→    total_trades: int
  60→    daily_returns: pd.Series    # pf.returns() — 供组合 Sharpe / Sortino 计算
  61→    sortino: float = 0.0       # Constitution L1 首要 KPI（迭代 #1 新增）
  62→
  63→
  64→@dataclass
  65→class GroupBacktestResult:
  66→    """单组策略回测结果。"""
  67→
  68→    group_id: str
  69→    strategy: str
  70→    params: dict
  71→    portfolio_sharpe: float          # 等权组合 Sharpe（而非算术平均）
  72→    avg_total_return_pct: float
  73→    avg_max_drawdown_pct: float
  74→    avg_win_rate_pct: float
  75→    symbol_count: int
  76→    portfolio_sortino: float = 0.0          # 等权组合 Sortino（迭代 #1 新增）
  77→    portfolio_max_drawdown: float = 0.0     # 等权组合最大回撤（迭代 #2 新增，Constitution L1 KPI）
  78→    dd_constrained: bool = False            # 迭代 #3：该组是否用了 DD fallback（无合规候选）
  79→
  80→
  81→@dataclass
  82→class MatrixBacktestReport:
  83→    """整个矩阵回测的汇总报告。"""
  84→
  85→    generated_at: str
  86→    backtest_window: str
  87→    groups: dict[str, list[dict]]   # group_id → [策略权重配置]
  88→    group_results: list[GroupBacktestResult] = field(default_factory=list)
  89→    warnings: list[str] = field(default_factory=list)
  90→
  91→
  92→# ---------------------------------------------------------------------------
  93→# Walk-Forward 数据结构（迭代 #3 新增，Constitution L7 验证流水线）
  94→# ---------------------------------------------------------------------------
  95→
  96→@dataclass
  97→class WalkForwardRound:
  98→    """单轮 Walk-Forward 验证结果。
  99→
 100→    一轮 = 训练期（找最优参数）+ 验证期（用同参数回测，记录样本外指标）。
 101→
 102→    Attributes:
 103→        round_num:    轮次编号（1-indexed）
 104→        train_start:  训练期起始日期（含）
 105→        train_end:    训练期结束日期（含）
 106→        val_start:    验证期起始日期（含）
 107→        val_end:      验证期结束日期（含）
 108→        val_sortino:  验证期等权组合 Sortino Ratio（年化）
 109→        val_max_dd:   验证期等权组合最大回撤（正值百分数，0~100）
 110→        passed:       是否通过 = val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD (15%)
 111→    """
 112→
 113→    round_num: int
 114→    train_start: date
 115→    train_end: date
 116→    val_start: date
 117→    val_end: date
 118→    val_sortino: float
 119→    val_max_dd: float
 120→    passed: bool
 121→
 122→
 123→@dataclass
 124→class WalkForwardReport:
 125→    """Walk-Forward 4 轮验证汇总报告。
 126→
 127→    Constitution L7 要求 Backtest(>=5年) → Walk-Forward(4轮) → Paper → Live。
 128→    本报告是 Walk-Forward 阶段的产出。
 129→
 130→    Attributes:
 131→        rounds:         每轮结果列表（长度通常为 4）
 132→        pass_all_rounds: 是否所有轮都通过（all(r.passed for r in rounds)）
 133→        max_val_dd:     所有轮中最大的验证期 DD（用于风险监控）
 134→    """
 135→
 136→    rounds: list[WalkForwardRound] = field(default_factory=list)
 137→    pass_all_rounds: bool = False
 138→    max_val_dd: float = 0.0
 139→
 140→
 141→# ---------------------------------------------------------------------------
 142→# 核心函数
 143→# ---------------------------------------------------------------------------
 144→
 145→def _safe_float(value: Any, default: float = 0.0) -> float:
 146→    """NaN/None/非数值安全转 float（迭代 #2 新增）。
 147→
 148→    问题背景：vectorbt 在无交易场景下，`pf.stats()` 的 Win Rate / Sharpe 等
 149→    字段会返回 NaN。`float(NaN or 0.0)` 仍是 NaN（NaN 是 truthy），导致
 150→    JSON 序列化写出非法 JSON（NaN/Infinity 非 JSON 规范）。
 151→
 152→    处理顺序：
 153→        1. None → default
 154→        2. 数值类型但 NaN/Inf → default
 155→        3. 非数值（字符串等）尝试 float() 转换，失败 → default
 156→    """
 157→    if value is None:
 158→        return default
 159→    try:
 160→        f = float(value)
 161→    except (TypeError, ValueError):
 162→        return default
 163→    if not np.isfinite(f):   # 拦截 NaN / +Inf / -Inf
 164→        return default
 165→    return f
 166→
 167→
 168→def _safe_mean(values: Any, default: float = 0.0) -> float:
 169→    """空列表 / 全 NaN 安全的均值（迭代 #2 新增）。
 170→
 171→    问题背景：`np.mean([])` 会触发 RuntimeWarning 并返回 NaN；
 172→    `np.mean([NaN, NaN])` 直接返回 NaN。在 GroupBacktestResult 聚合时
 173→    若某组只有 1 个标的且其字段为 NaN，会导致下游 JSON 序列化失败。
 174→
 175→    行为：
 176→        - 空列表 / 全 NaN → default
 177→        - 部分 NaN → 自动忽略 NaN 后取均值（np.nanmean 语义）
 178→    """
 179→    arr = np.asarray(values, dtype=float)
 180→    if arr.size == 0:
 181→        return default
 182→    mask = np.isfinite(arr)
 183→    if not mask.any():
 184→        return default
 185→    return float(arr[mask].mean())
 186→
 187→
 188→def _compute_sharpe(returns: pd.Series, periods_per_year: int = 252) -> float:
 189→    """从日收益率序列计算年化 Sharpe Ratio。"""
 190→    returns = returns.dropna()
 191→    if len(returns) < 5:
 192→        return 0.0
 193→    mean = returns.mean()
 194→    std = returns.std()
 195→    if std <= 0 or np.isnan(std):
 196→        return 0.0
 197→    return float(mean / std * np.sqrt(periods_per_year))
 198→
 199→
 200→def _compute_sortino(
 201→    returns: pd.Series,
 202→    periods_per_year: int = 252,
 203→    target: float = 0.0,
 204→) -> float:
 205→    """从日收益率序列计算年化 Sortino Ratio（Constitution L1 首要 KPI）。
 206→
 207→    Sortino = (mean(returns) - target) / downside_deviation * sqrt(periods_per_year)
 208→    downside_deviation = sqrt( mean( min(0, returns - target)^2 ) )
 209→
 210→    与 Sharpe 的区别：仅对下行波动惩罚，上行波动不计入分母。
 211→    适合"收益>0 但偶尔大跌"的中长线策略评估。
 212→
 213→    退化处理（与 _compute_sharpe 一致）：
 214→        - 样本 < 5 → 0.0
 215→        - 下行波动 ≤ 0（无下行样本）→ 0.0（理论为 +inf，返回 0 保持保守 + 可算术聚合）
 216→
 217→    Args:
 218→        returns:          日收益率序列（如 pf.returns()）
 219→        periods_per_year: 年化因子（日线 = 252）
 220→        target:           MAR/目标收益率，默认 0（与 _compute_sharpe 无风险利率假设一致）
 221→
 222→    Returns:
 223→        年化 Sortino Ratio
 224→    """
 225→    returns = returns.dropna()
 226→    if len(returns) < 5:
 227→        return 0.0
 228→    excess = returns - target
 229→    downside = excess.where(excess < 0, 0.0)        # 仅保留负偏离，正偏离置 0
 230→    dd = np.sqrt((downside ** 2).mean())
 231→    if dd <= 0 or np.isnan(dd):
 232→        return 0.0
 233→    return float(returns.mean() / dd * np.sqrt(periods_per_year))
 234→
 235→
 236→def _backtest_one(
 237→    df: pd.DataFrame,
 238→    strategy_name: str,
 239→    params: dict,
 240→    init_cash: float = 100_000.0,
 241→    fees: float = 0.001,
 242→    slippage: float = 0.001,
 243→) -> SingleBacktestResult | None:
 244→    """对单只标的执行单次回测。
 245→
 246→    使用 open= 参数确保信号在下一根 bar 的开盘价执行（与实盘一致）。
 247→
 248→    Returns:
 249→        SingleBacktestResult 或 None（数据不足/策略异常时）
 250→    """
 251→    strategy_fn = STRATEGY_REGISTRY.get(strategy_name)
 252→    if strategy_fn is None:
 253→        return None
 254→
 255→    if df.empty or len(df) < 30:
 256→        return None
 257→
 258→    try:
 259→        close = df["close"]
 260→        open_ = df["open"] if "open" in df.columns else None
 261→
 262→        # 调用策略（兼容需要 df 的策略）
 263→        try:
 264→            sig = strategy_fn(close, df=df, **params)
 265→        except TypeError:
 266→            sig = strategy_fn(close, **params)
 267→
 268→        entries = sig == 1
 269→        exits   = sig == -1
 270→
 271→        pf_kwargs: dict[str, Any] = dict(
 272→            entries=entries,
 273→            exits=exits,
 274→            init_cash=init_cash,
 275→            fees=fees,
 276→            slippage=slippage,
 277→            size=0.95,
 278→            size_type="Percent",
 279→            freq="D",
 280→        )
 281→
 282→        # ⚠️ 必须传 open= 参数：信号在下一根 bar 开盘价执行，与实盘一致
 283→        if open_ is not None:
 284→            pf = vbt.Portfolio.from_signals(close=close, open=open_, **pf_kwargs)
 285→        else:
 286→            pf = vbt.Portfolio.from_signals(close, **pf_kwargs)
 287→
 288→        stats = pf.stats()
 289→
 290→        daily_returns = pf.returns()
 291→
 292→        return SingleBacktestResult(
 293→            symbol=str(df.index.name or ""),
 294→            strategy=strategy_name,
 295→            params=params,
 296→            sharpe=_safe_float(stats.get("Sharpe Ratio")),
 297→            total_return_pct=_safe_float(stats.get("Total Return [%]")),
 298→            max_drawdown_pct=_safe_float(stats.get("Max Drawdown [%]")),
 299→            win_rate_pct=_safe_float(stats.get("Win Rate [%]")),
 300→            total_trades=int(_safe_float(stats.get("Total Trades"), default=0.0)),
 301→            daily_returns=daily_returns,
 302→            sortino=_compute_sortino(daily_returns),
 303→        )
 304→    except Exception as e:
 305→        logger.debug(f"[backtest_one] {strategy_name}({params}) failed: {e}")
 306→        return None
 307→
 308→
 309→def _portfolio_sharpe_from_results(results: list[SingleBacktestResult]) -> float:
 310→    """等权合并组内日收益率序列，计算组合 Sharpe。
 311→
 312→    ⚠️ 不能取各标的 Sharpe 算术平均（Sharpe 是比率，不能直接平均）。
 313→    正确做法：将所有标的日收益率等权合并为组合序列，再计算 Sharpe。
 314→    """
 315→    valid = [r.daily_returns for r in results if not r.daily_returns.empty]
 316→    if not valid:
 317→        return 0.0
 318→
 319→    # 对齐时间索引，等权平均
 320→    combined = pd.concat(valid, axis=1).mean(axis=1)
 321→    return _compute_sharpe(combined)
 322→
 323→
 324→def _portfolio_sortino_from_results(results: list[SingleBacktestResult]) -> float:
 325→    """等权合并组内日收益率序列，计算组合 Sortino（与 _portfolio_sharpe_from_results 同语义）。
 326→
 327→    不能取各标的 Sortino 算术平均（与 Sharpe 同理：比率不可直接平均）。
 328→    """
 329→    valid = [r.daily_returns for r in results if not r.daily_returns.empty]
 330→    if not valid:
 331→        return 0.0
 332→    combined = pd.concat(valid, axis=1).mean(axis=1)
 333→    return _compute_sortino(combined)
 334→
 335→
 336→def _portfolio_max_drawdown_from_results(
 337→    results: list[SingleBacktestResult],
 338→) -> float:
 339→    """等权合并组内日收益率序列，计算组合最大回撤（迭代 #2 新增，Constitution L1 KPI）。
 340→
 341→    与 `_portfolio_sharpe_from_results` 同语义：不能取各标的 DD 算术平均，
 342→    因为 DD 是路径依赖的比率。正确做法是先把��内日收益率等权合并为组合序列，
 343→    再 cumprod → cummax → drawdown → max。
 344→
 345→    返回值约定：百分比形式（与 `SingleBacktestResult.max_drawdown_pct` 一致，
 346→    vectorbt stats 中 `Max Drawdown [%]` 同样是百分数，例如 -15.2 表示 15.2% 回撤）。
 347→    本函数返回正值（0.0 ~ 100.0）便于聚合与 JSON 输出。
 348→
 349→    退化处理：
 350→        - 无有效日收益率 → 0.0
 351→        - 全 0 收益率（cumprod 恒为 1.0）→ 0.0
 352→    """
 353→    valid = [r.daily_returns for r in results if not r.daily_returns.empty]
 354→    if not valid:
 355→        return 0.0
 356→    combined = pd.concat(valid, axis=1).mean(axis=1).dropna()
 357→    if len(combined) < 2:
 358→        return 0.0
 359→    # 组合累计净值：初始 1.0，每日乘 (1 + r)
 360→    cumvalue = (1.0 + combined).cumprod()
 361→    peak = cumvalue.cummax()
 362→    drawdown = (cumvalue - peak) / peak   # 负值，0 表示无回撤
 363→    dd_max_pct = float(drawdown.min())    # 最负值，例如 -0.152
 364→    if not np.isfinite(dd_max_pct):
 365→        return 0.0
 366→    # 转为正百分数（与 vectorbt Max Drawdown [%] 的口径一致但取正号）
 367→    return abs(dd_max_pct) * 100.0
 368→
 369→
 370→def _optimize_ensemble_weights(
 371→    group_results: list[tuple[str, dict, list[SingleBacktestResult]]],
 372→    conflict_threshold: float = 0.3,
 373→) -> list[tuple[str, dict, float]]:
 374→    """在"单点离散值加权投票"语义下优化 ensemble 权重。
 375→
 376→    实盘每根 bar 各策略产出离散值（1/-1/0），加权投票决定方向。
 377→    回测的权重优化必须使用相同语义，而非对整段时间序列做加权。
 378→
 379→    Args:
 380→        group_results: [(strategy, params, [SingleBacktestResult]), ...]
 381→        conflict_threshold: 加权投票分数绝对值低于此时视为 HOLD
 382→
 383→    Returns:
 384→        [(strategy, params, weight), ...] 归一化权重列表
 385→    """
 386→    if len(group_results) == 1:
 387→        strategy, params, _ = group_results[0]
 388→        return [(strategy, params, 1.0)]
 389→
 390→    # 简化的 ensemble 权重搜索：用各策略的组合 Sharpe 归一化为权重
 391→    # 更严格的做法是网格搜索 weight 组合，在离散投票序列上跑回测
 392→    sharpes = []
 393→    for strategy, params, results in group_results:
 394→        ps = _portfolio_sharpe_from_results(results)
 395→        sharpes.append(max(ps, 0.01))  # 避免负权重
 396→
 397→    total = sum(sharpes)
 398→    weights = [s / total for s in sharpes]
 399→
 400→    return [
 401→        (strategy, params, weight)
 402→        for (strategy, params, _), weight in zip(group_results, weights)
 403→    ]
 404→
 405→
 406→# ---------------------------------------------------------------------------
 407→# Walk-Forward 验证（迭代 #3 新增，Constitution L7 验证流水线）
 408→# ---------------------------------------------------------------------------
 409→
 410→def _add_months(d: date, months: int) -> date:
 411→    """对 date 加/减 months 个月，自动 clamp 到月末。
 412→
 413→    使用 pandas DateOffset 以避免引入 dateutil 依赖（pandas 已是核心依赖）。
 414→    """
 415→    return (pd.Timestamp(d) + pd.DateOffset(months=months)).date()
 416→
 417→
 418→def _backtest_with_params_on_period(
 419→    mb: "MatrixBacktest",
 420→    symbols: list[str],
 421→    weights: list[dict[str, Any]],
 422→    start: date,
 423→    end: date,
 424→) -> list[pd.Series]:
 425→    """用给定权重配置在 [start, end] 期间回测，返回每条 (策略×标的) 的日收益率序列。
 426→
 427→    用于 Walk-Forward 验证期：用训练期产出的 best params 在验证期回测，
 428→    不再做参数搜索。返回原始日收益率列表，由调用方聚合为整体 portfolio。
 429→
 430→    Args:
 431→        mb:       MatrixBacktest 实例（复用其 store/init_cash/fees/slippage）
 432→        symbols:  该组的标的列表
 433→        weights:  训练期产出的权重配置（list of dict，含 strategy/params/weight）
 434→        start:    验证期起始日期
 435→        end:      验证期结束日期
 436→
 437→    Returns:
 438→        list[pd.Series] — 每条 (strategy×symbol) 的日收益率；空列表表示无有效数据
 439→    """
 440→    if not weights or not symbols:
 441→        return []
 442→
 443→    data = mb._store.get_bars_multi(symbols, start, end)
 444→    if not data:
 445→        return []
 446→
 447→    all_returns: list[pd.Series] = []
 448→    for w in weights:
 449→        strategy = w.get("strategy", "")
 450→        params = w.get("params", {})
 451→        if not strategy or strategy not in STRATEGY_REGISTRY:
 452→            continue
 453→        for sym in symbols:
 454→            df = data.get(sym, pd.DataFrame())
 455→            if df.empty:
 456→                continue
 457→            df = df.copy()
 458→            df.index.name = sym
 459→            r = _backtest_one(
 460→                df, strategy, params,
 461→                mb._init_cash, mb._fees, mb._slippage,
 462→            )
 463→            if r is not None and not r.daily_returns.empty:
 464→                all_returns.append(r.daily_returns)
 465→    return all_returns
 466→
 467→
 468→def run_walk_forward(
 469→    mb: "MatrixBacktest",
 470→    strategies: list[str],
 471→    param_grids: dict[str, dict[str, list]],
 472→    rounds: int = 4,
 473→    train_months: int = 18,
 474→    val_months: int = 6,
 475→) -> WalkForwardReport:
 476→    """执行 N 轮 Walk-Forward 验证（Constitution L7 验证流水线硬要求）。
 477→
 478→    每轮流程：
 479→        1. 训练期 [train_start, train_end]：跑矩阵回测找最优参数
 480→        2. 验证期 [val_start, val_end]：用同参数回测，记录 portfolio Sortino 和 max DD
 481→        3. passed = val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD (15%)
 482→
 483→    时间窗口（动态计算，today=today）：
 484→        - 最后一轮 val_end = today - val_months（留 1 个 val 期给 paper trading）
 485→        - 每轮向前推 val_months
 486→        - train_end = val_start，train_start = train_end - train_months
 487→
 488→    默认参数 (rounds=4, train_months=18, val_months=6) 对应用户提供的固定窗口：
 489→        today=2026-07-01 →
 490→        Round 1: train 2021-07-02~2023-01-02, val 2023-01-02~2023-07-02
 491→        Round 2: train 2022-01-02~2023-07-02, val 2023-07-02~2024-01-02
 492→        Round 3: train 2022-07-02~2024-01-02, val 2024-01-02~2024-07-02
 493→        Round 4: train 2023-01-02~2024-07-02, val 2024-07-02~2025-01-02
 494→
 495→    Args:
 496→        mb:            MatrixBacktest 实例（复用其 store/universe/init_cash 等）
 497→        strategies:    策略名称列表
 498→        param_grids:   参数网格（与 mb.run() 接收的格式一致）
 499→        rounds:        轮次数（默认 4，Constitution L7 要求）
 500→        train_months:  训练期月数（默认 18）
 501→        val_months:    验证期月数（默认 6）
 502→
 503→    Returns:
 504→        WalkForwardReport — 包含每轮结果、pass_all_rounds、max_val_dd
 505→
 506→    Note:
 507→        - WF 是验证步骤，不修改 strategy_weights.json
 508→        - 失败轮次会记录 WARNING 但不抛异常
 509→        - 全部 4 轮通过是进入 paper trading 的前置条件
 510→    """
 511→    today = date.today()
 512→    groups = mb._universe.get_groups()
 513→    if not groups:
 514→        logger.warning("[WalkForward] no groups available — skipping")
 515→        return WalkForwardReport()
 516→
 517→    wf_rounds: list[WalkForwardRound] = []
 518→
 519→    for i in range(rounds):
 520→        round_num = i + 1
 521→        # 计算本轮时间窗口
 522→        # 最后一轮 (i=rounds-1) 的 val_end = today - val_months
 523→        # 前面轮次依次向前推 val_months
 524→        val_end = _add_months(today, -val_months - (rounds - round_num) * val_months)
 525→        val_start = _add_months(val_end, -val_months)
 526→        train_end = val_start
 527→        train_start = _add_months(train_end, -train_months)
 528→
 529→        logger.info(
 530→            f"[WalkForward] Round {round_num}/{rounds}: "
 531→            f"train={train_start}~{train_end}, val={val_start}~{val_end}"
 532→        )
 533→
 534→        # ── 训练期：跑矩阵回测找最优参数（复用 mb._run_group）──
 535→        train_report = MatrixBacktestReport(
 536→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
 537→            backtest_window=f"{train_start.isoformat()} ~ {train_end.isoformat()}",
 538→            groups={},
 539→        )
 540→
 541→        for group_id, symbols in groups.items():
 542→            weights = mb._run_group(
 543→                group_id=group_id,
 544→                symbols=symbols,
 545→                start=train_start,
 546→                end=train_end,
 547→                strategies=strategies,
 548→                param_grids=param_grids,
 549→                report=train_report,
 550→            )
 551→            train_report.groups[group_id] = weights
 552→
 553→        # ── 验证期：用训练期 best params 回测，聚合为整体 portfolio ──
 554→        all_returns: list[pd.Series] = []
 555→        for group_id, symbols in groups.items():
 556→            weights = train_report.groups.get(group_id, [])
 557→            if not weights:
 558→                continue
 559→            group_returns = _backtest_with_params_on_period(
 560→                mb, symbols, weights, val_start, val_end,
 561→            )
 562→            all_returns.extend(group_returns)
 563→
 564→        # 计算整体 portfolio 指标（等权合并所有组的日收益率）
 565→        if not all_returns:
 566→            val_sortino = 0.0
 567→            val_max_dd = 0.0
 568→            logger.warning(
 569→                f"[WalkForward] Round {round_num}: no valid val returns — "
 570→                f"sortino=0, dd=0, passed=True (vacuous)"
 571→            )
 572→        else:
 573→            combined = pd.concat(all_returns, axis=1).mean(axis=1).dropna()
 574→            if len(combined) < 5:
 575→                val_sortino = 0.0
 576→                val_max_dd = 0.0
 577→            else:
 578→                val_sortino = _compute_sortino(combined)
 579→                wrapper = [SingleBacktestResult(
 580→                    symbol="portfolio", strategy="", params={},
 581→                    sharpe=0.0, total_return_pct=0.0, max_drawdown_pct=0.0,
 582→                    win_rate_pct=0.0, total_trades=0, daily_returns=combined,
 583→                )]
 584→                val_max_dd = _portfolio_max_drawdown_from_results(wrapper)
 585→
 586→        passed = val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD
 587→        wf_rounds.append(WalkForwardRound(
 588→            round_num=round_num,
 589→            train_start=train_start,
 590→            train_end=train_end,
 591→            val_start=val_start,
 592→            val_end=val_end,
 593→            val_sortino=val_sortino,
 594→            val_max_dd=val_max_dd,
 595→            passed=passed,
 596→        ))
 597→        logger.info(
 598→            f"[WalkForward] Round {round_num} result: "
 599→            f"sortino={val_sortino:.4f}, dd={val_max_dd:.4f}%, "
 600→            f"passed={passed} (threshold={WALK_FORWARD_VAL_DD_THRESHOLD}%)"
 601→        )
 602→
 603→    report = WalkForwardReport(
 604→        rounds=wf_rounds,
 605→        pass_all_rounds=all(r.passed for r in wf_rounds) if wf_rounds else False,
 606→        max_val_dd=max((r.val_max_dd for r in wf_rounds), default=0.0),
 607→    )
 608→    logger.info(
 609→        f"[WalkForward] done: {len(wf_rounds)} rounds, "
 610→        f"pass_all_rounds={report.pass_all_rounds}, "
 611→        f"max_val_dd={report.max_val_dd:.4f}%"
 612→    )
 613→    return report
 614→
 615→
 616→# ---------------------------------------------------------------------------
 617→# MatrixBacktest 主类
 618→# ---------------------------------------------------------------------------
 619→
 620→class MatrixBacktest:
 621→    """矩阵回测：N 策略 × G 标的组 × 参数网格 → strategy_weights.json。
 622→
 623→    Args:
 624→        store:       MarketDataStore（本地时序库）
 625→        universe:    UniverseManager（提供分组映射）
 626→        years:       回测窗口（默认 5 年）
 627→        init_cash:   初始资金
 628→        fees:        手续费率
 629→        slippage:    滑点率
 630→        top_k:       每组保留 Top-K 策略（默认 2）
 631→    """
 632→
 633→    def __init__(
 634→        self,
 635→        store: MarketDataStore,
 636→        universe: UniverseManager,
 637→        years: int = 5,
 638→        init_cash: float = 100_000.0,
 639→        fees: float = 0.001,
 640→        slippage: float = 0.001,
 641→        top_k: int = 2,
 642→    ) -> None:
 643→        self._store = store
 644→        self._universe = universe
 645→        self._years = years
 646→        self._init_cash = init_cash
 647→        self._fees = fees
 648→        self._slippage = slippage
 649→        self._top_k = top_k
 650→
 651→    def run(
 652→        self,
 653→        strategies: list[str],
 654→        param_grids: dict[str, dict[str, list]],
 655→        output_file: str | Path | None = None,
 656→    ) -> MatrixBacktestReport:
 657→        """执行完整矩阵回测。
 658→
 659→        Args:
 660→            strategies:  策略名称列表，如 ["dual_ma", "rsi"]
 661→            param_grids: 各策略参数网格，如 {"dual_ma": {"fast":[5,10], "slow":[20,30]}}
 662→            output_file: strategy_weights.json 输出路径（None 则不写文件）
 663→
 664→        Returns:
 665→            MatrixBacktestReport
 666→        """
 667→        today = date.today()
 668→        start = today - timedelta(days=self._years * 365)
 669→        window_str = f"{start.isoformat()} ~ {today.isoformat()}"
 670→
 671→        logger.info(
 672→            f"[MatrixBacktest] start={start}, end={today}, "
 673→            f"strategies={strategies}, years={self._years}"
 674→        )
 675→
 676→        # 获取分组（⚠️ 使用历史时点分组，而非当前静态分组）
 677→        # Phase 5 初期简化：用当前分组，但接口已预留历史分组能力
 678→        groups = self._universe.get_groups()
 679→        if not groups:
 680→            logger.warning("[MatrixBacktest] no groups available, abort")
 681→            return MatrixBacktestReport(
 682→                generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
 683→                backtest_window=window_str,
 684→                groups={},
 685→            )
 686→
 687→        report = MatrixBacktestReport(
 688→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
 689→            backtest_window=window_str,
 690→            groups={},
 691→        )
 692→
 693→        for group_id, symbols in groups.items():
 694→            logger.info(
 695→                f"[MatrixBacktest] group={group_id}, symbols={len(symbols)}, "
 696→                f"strategies={strategies}"
 697→            )
 698→
 699→            group_weights = self._run_group(
 700→                group_id=group_id,
 701→                symbols=symbols,
 702→                start=start,
 703→                end=today,
 704→                strategies=strategies,
 705→                param_grids=param_grids,
 706→                report=report,
 707→            )
 708→            report.groups[group_id] = group_weights
 709→
 710→        if output_file is not None:
 711→            self._write_weights(report, output_file)
 712→
 713→        logger.info(
 714→            f"[MatrixBacktest] done: {len(report.groups)} groups, "
 715→            f"warnings={len(report.warnings)}"
 716→        )
 717→        return report
 718→
 719→    def _run_group(
 720→        self,
 721→        group_id: str,
 722→        symbols: list[str],
 723→        start: date,
 724→        end: date,
 725→        strategies: list[str],
 726→        param_grids: dict[str, dict[str, list]],
 727→        report: MatrixBacktestReport,
 728→    ) -> list[dict[str, Any]]:
 729→        """对单个分组执行策略 × 参数网格回测，返回该组的权重配置列表。"""
 730→
 731→        # 1. 读取组内所有标的数据
 732→        data = self._store.get_bars_multi(symbols, start, end)
 733→        if not data:
 734→            logger.warning(f"[MatrixBacktest] {group_id}: no data, skip")
 735→            return []
 736→
 737→        # 2. 对每个策略 × 每组参数，计算组合 Sharpe
 738→        group_results: list[tuple[str, dict, list[SingleBacktestResult]]] = []
 739→
 740→        for strategy in strategies:
 741→            # ⚠️ 早期检测未注册策略名（迭代 #1 修复"策略名拼写错误被静默跳过"的 bug）
 742→            # 之前 _backtest_one 内部静默 return None，导致 main.py 误用 "rsi"/"macd"/"bollinger"
 743→            # 简称 6 天未被发现。改为 WARNING 级日志 + continue。
 744→            if strategy not in STRATEGY_REGISTRY:
 745→                logger.warning(
 746→                    f"[MatrixBacktest] {group_id}: strategy '{strategy}' not in "
 747→                    f"STRATEGY_REGISTRY — skipped. "
 748→                    f"Check spelling against @register_strategy decorators. "
 749→                    f"Known: {sorted(STRATEGY_REGISTRY.keys())}"
 750→                )
 751→                continue
 752→            grid = param_grids.get(strategy, {})
 753→            param_combos = list(
 754→                dict(zip(grid.keys(), combo))
 755→                for combo in itertools.product(*grid.values())
 756→            ) if grid else [{}]
 757→
 758→            best_params = None
 759→            best_sharpe = float("-inf")
 760→            best_sortino = 0.0
 761→            best_results: list[SingleBacktestResult] = []
 762→
 763→            for params in param_combos:
 764→                # 对组内每只标的回测
 765→                results = []
 766→                for sym in symbols:
 767→                    df = data.get(sym, pd.DataFrame())
 768→                    if df.empty:
 769→                        continue
 770→                    df.index.name = sym  # 方便 _backtest_one 使用
 771→                    r = _backtest_one(
 772→                        df, strategy, params,
 773→                        self._init_cash, self._fees, self._slippage
 774→                    )
 775→                    if r is not None:
 776→                        results.append(r)
 777→
 778→                if not results:
 779→                    continue
 780→
 781→                # ⚠️ 等权合并日收益率序列计算组合 Sharpe（不能取算术平均）
 782→                ps = _portfolio_sharpe_from_results(results)
 783→                pso = _portfolio_sortino_from_results(results)
 784→
 785→                if ps > best_sharpe:
 786→                    best_sharpe = ps
 787→                    best_sortino = pso
 788→                    best_params = params
 789→                    best_results = results
 790→
 791→            if best_params is not None and best_results:
 792→                group_results.append((strategy, best_params, best_results))
 793→                report.group_results.append(GroupBacktestResult(
 794→                    group_id=group_id,
 795→                    strategy=strategy,
 796→                    params=best_params,
 797→                    portfolio_sharpe=best_sharpe,
 798→                    avg_total_return_pct=_safe_mean(
 799→                        [r.total_return_pct for r in best_results]
 800→                    ),
 801→                    avg_max_drawdown_pct=_safe_mean(
 802→                        [r.max_drawdown_pct for r in best_results]
 803→                    ),
 804→                    avg_win_rate_pct=_safe_mean(
 805→                        [r.win_rate_pct for r in best_results]
 806→                    ),
 807→                    symbol_count=len(best_results),
 808→                    portfolio_sortino=best_sortino,
 809→                    portfolio_max_drawdown=_portfolio_max_drawdown_from_results(
 810→                        best_results
 811→                    ),
 812→                ))
 813→
 814→        if not group_results:
 815→            logger.warning(f"[MatrixBacktest] {group_id}: no valid results")
 816→            return []
 817→
 818→        # 3. 迭代 #3：DD 约束 + Sortino 排序选 Top-K
 819→        #    Constitution L1: portfolio DD ≤ 20% 是硬约束
 820→        #    步骤：(a) 计算每候选 portfolio_max_drawdown
 821→        #          (b) 过滤 DD <= MAX_PORTFOLIO_DRAWDOWN_PCT 的合规集
 822→        #          (c) 合规集非空 → 按 Sortino 降序取 top-K
 823→        #          (d) 合规集为空 → fallback：按 DD 升序取 top-K，标记 dd_constrained=True
 824→        candidates: list[tuple[str, dict, list[SingleBacktestResult], float, float]] = []
 825→        for (strategy, params, results) in group_results:
 826→            pso = _portfolio_sortino_from_results(results)
 827→            pdd = _portfolio_max_drawdown_from_results(results)
 828→            candidates.append((strategy, params, results, pso, pdd))
 829→
 830→        compliant = [c for c in candidates if c[4] <= MAX_PORTFOLIO_DRAWDOWN_PCT]
 831→        if compliant:
 832→            # 合规集非空：按 Sortino 降序取 top-K
 833→            ranked = sorted(compliant, key=lambda x: x[3], reverse=True)
 834→            dd_constrained = False
 835→            logger.info(
 836→                f"[MatrixBacktest] {group_id}: DD filter passed — "
 837→                f"{len(compliant)}/{len(candidates)} candidates compliant "
 838→                f"(DD <= {MAX_PORTFOLIO_DRAWDOWN_PCT}%)"
 839→            )
 840→        else:
 841→            # Fallback：无合规候选（结构性问题，如 NDX_high_vol 全部 > 20%）
 842→            # 按 DD 升序（最低 DD 优先）取 top-K，标记 dd_constrained
 843→            ranked = sorted(candidates, key=lambda x: x[4])
 844→            dd_constrained = True
 845→            logger.warning(
 846→                f"[MatrixBacktest] {group_id}: NO compliant candidates "
 847→                f"(all {len(candidates)} exceed DD={MAX_PORTFOLIO_DRAWDOWN_PCT}%). "
 848→                f"Fallback: selected top-{self._top_k} by lowest DD. "
 849→                f"This group is marked dd_constrained=True — "
 850→                f"review whether to drop the group or accept the risk."
 851→            )
 852→            report.warnings.append(
 853→                f"{group_id}: dd_constrained=True "
 854→                f"(min DD={ranked[0][4]:.2f}% > {MAX_PORTFOLIO_DRAWDOWN_PCT}%)"
 855→            )
 856→
 857→        top_results = ranked[: self._top_k]
 858→
 859→        # 把 dd_constrained 标记同步到 report.group_results 中对应组的条目
 860→        for gr in report.group_results:
 861→            if gr.group_id == group_id:
 862→                gr.dd_constrained = dd_constrained
 863→
 864→        # 4. 优化 ensemble 权重（单点离散值加权投票语义）
 865→        weighted = _optimize_ensemble_weights(
 866→            [(s, p, r) for (s, p, r, _, _) in top_results]
 867→        )
 868→
 869→        # 5. 构建权重配置列表
 870→        weights_list = []
 871→        for strategy, params, weight in weighted:
 872→            # 找到对应的 GroupBacktestResult
 873→            gr = next(
 874→                (r for r in report.group_results
 875→                 if r.group_id == group_id and r.strategy == strategy),
 876→                None,
 877→            )
 878→            # 迭代 #4：新增 backtest_dd_status 字段（'pass' / 'dd_constrained'）
 879→            # 作为风险 metadata 标记，与 dd_constrained bool 同义但更可读
 880→            backtest_dd_status = "dd_constrained" if dd_constrained else "pass"
 881→            weights_list.append({
 882→                "strategy": strategy,
 883→                "params": params,
 884→                "weight": round(weight, 4),
 885→                "backtest_sharpe": round(gr.portfolio_sharpe if gr else 0.0, 4),
 886→                "backtest_sortino": round(gr.portfolio_sortino if gr else 0.0, 4),
 887→                "backtest_max_drawdown": round(gr.portfolio_max_drawdown if gr else 0.0, 4),
 888→                "backtest_win_rate": round(gr.avg_win_rate_pct / 100 if gr else 0.5, 4),
 889→                # 迭代 #3：标记该组是否用了 DD fallback（无合规候选）
 890→                # 同组所有策略条目共享同一 dd_constrained 值
 891→                "dd_constrained": dd_constrained,
 892→                # 迭代 #4：backtest_dd_status — 风险 metadata 字段
 893→                # 'pass' = 该组有合规候选（DD ≤ 20%）
 894→                # 'dd_constrained' = fallback 触发（无合规候选，按最低 DD 取 top-K）
 895→                # 下游消费方（PortfolioBacktester / 风控观测）可读此字段判断
 896→                # 该组权重的可靠性，作为风险信号标记
 897→                "backtest_dd_status": backtest_dd_status,
 898→            })
 899→
 900→        return weights_list
 901→
 902→    def _write_weights(
 903→        self, report: MatrixBacktestReport, output_file: str | Path
 904→    ) -> None:
 905→        """将矩阵回测结果写入 strategy_weights.json。"""
 906→        output_file = Path(output_file)
 907→        output_file.parent.mkdir(parents=True, exist_ok=True)
 908→
 909→        data = {
 910→            "_meta": {
 911→                "generated_at": report.generated_at,
 912→                "backtest_window": report.backtest_window,
 913→                "reoptimize_freq": "monthly",
 914→                "survivorship_bias_warning": (
 915→                    "使用当前成分股回测，S&P 500 5年成分变动约100只(~20%)，"
 916→                    "均值回归组(SPX_low_vol)结果可能系统性偏高"
 917→                ),
 918→            },
 919→            "groups": report.groups,
 920→        }
 921→
 922→        with open(output_file, "w", encoding="utf-8") as f:
 923→            json.dump(data, f, indent=2, ensure_ascii=False)
 924→
 925→        logger.info(f"[MatrixBacktest] weights saved to {output_file}")
 926→
---
   1→"""MatrixBacktest — 矩阵回测核心。
   2→
   3→N 策略 × G 标的组 × 参数网格 → strategy_weights.json
   4→
   5→关键设计：
   6→    1. 组合 Sharpe 计算：等权合并组内日收益率序列，而非算术平均各标的 Sharpe
   7→    2. 历史分组：每个回测时间点用 point-in-time 波动率分组（非当前静态分组）
   8→    3. open 参数：所有回测传 open=data["open"]，与实盘开盘价执行一致
   9→    4. ensemble 语义：权重优化在"单点离散值加权投票"语义下进行，与实盘 run_symbol 一致
  10→"""
  11→
  12→from __future__ import annotations
  13→
  14→import itertools
  15→import json
  16→from dataclasses import dataclass, field
  17→from datetime import date, timedelta
  18→from pathlib import Path
  19→from typing import Any
  20→
  21→import numpy as np
  22→import pandas as pd
  23→import vectorbt as vbt
  24→from loguru import logger
  25→
  26→from mytrader.data.store.market_data_store import MarketDataStore
  27→from mytrader.strategy.registry import STRATEGY_REGISTRY
  28→from mytrader.universe.manager import UniverseManager
  29→
  30→
  31→# ---------------------------------------------------------------------------
  32→# 常量
  33→# ---------------------------------------------------------------------------
  34→
  35→# Constitution L1 硬约束：portfolio 最大回撤 ≤ 20%
  36→# _run_group 在 top-K 选择时按此阈值过滤合规候选（迭代 #3 新增）
  37→MAX_PORTFOLIO_DRAWDOWN_PCT: float = 20.0
  38→
  39→# Constitution L7 Walk-Forward 门槛：单轮验证期 portfolio DD ≤ 15%
  40→# （低于 L1 的 20% 线，给样本外留缓冲）
  41→WALK_FORWARD_VAL_DD_THRESHOLD: float = 15.0
  42→
  43→
  44→# ---------------------------------------------------------------------------
  45→# 数据结构
  46→# ---------------------------------------------------------------------------
  47→
  48→@dataclass
  49→class SingleBacktestResult:
  50→    """单只标的单策略回测结果。"""
  51→
  52→    symbol: str
  53→    strategy: str
  54→    params: dict
  55→    sharpe: float
  56→    total_return_pct: float
  57→    max_drawdown_pct: float
  58→    win_rate_pct: float
  59→    total_trades: int
  60→    daily_returns: pd.Series    # pf.returns() — 供组合 Sharpe / Sortino 计算
  61→    sortino: float = 0.0       # Constitution L1 首要 KPI（迭代 #1 新增）
  62→
  63→
  64→@dataclass
  65→class GroupBacktestResult:
  66→    """单组策略回测结果。"""
  67→
  68→    group_id: str
  69→    strategy: str
  70→    params: dict
  71→    portfolio_sharpe: float          # 等权组合 Sharpe（而非算术平均）
  72→    avg_total_return_pct: float
  73→    avg_max_drawdown_pct: float
  74→    avg_win_rate_pct: float
  75→    symbol_count: int
  76→    portfolio_sortino: float = 0.0          # 等权组合 Sortino（迭代 #1 新增）
  77→    portfolio_max_drawdown: float = 0.0     # 等权组合最大回撤（迭代 #2 新增，Constitution L1 KPI）
  78→    dd_constrained: bool = False            # 迭代 #3：该组是否用了 DD fallback（无合规候选）
  79→
  80→
  81→@dataclass
  82→class MatrixBacktestReport:
  83→    """整个矩阵回测的汇总报告。"""
  84→
  85→    generated_at: str
  86→    backtest_window: str
  87→    groups: dict[str, list[dict]]   # group_id → [策略权重配置]
  88→    group_results: list[GroupBacktestResult] = field(default_factory=list)
  89→    warnings: list[str] = field(default_factory=list)
  90→
  91→
  92→# ---------------------------------------------------------------------------
  93→# Walk-Forward 数据结构（迭代 #3 新增，Constitution L7 验证流水线）
  94→# ---------------------------------------------------------------------------
  95→
  96→@dataclass
  97→class WalkForwardRound:
  98→    """单轮 Walk-Forward 验证结果。
  99→
 100→    一轮 = 训练期（找最优参数）+ 验证期（用同参数回测，记录样本外指标）。
 101→
 102→    Attributes:
 103→        round_num:    轮次编号（1-indexed）
 104→        train_start:  训练期起始日期（含）
 105→        train_end:    训练期结束日期（含）
 106→        val_start:    验证期起始日期（含）
 107→        val_end:      验证期结束日期（含）
 108→        val_sortino:  验证期等权组合 Sortino Ratio（年化）
 109→        val_max_dd:   验证期等权组合最大回撤（正值百分数，0~100）
 110→        passed:       是否通过 = val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD (15%)
 111→    """
 112→
 113→    round_num: int
 114→    train_start: date
 115→    train_end: date
 116→    val_start: date
 117→    val_end: date
 118→    val_sortino: float
 119→    val_max_dd: float
 120→    passed: bool
 121→
 122→
 123→@dataclass
 124→class WalkForwardReport:
 125→    """Walk-Forward 4 轮验证汇总报告。
 126→
 127→    Constitution L7 要求 Backtest(>=5年) → Walk-Forward(4轮) → Paper → Live。
 128→    本报告是 Walk-Forward 阶段的产出。
 129→
 130→    Attributes:
 131→        rounds:         每轮结果列表（长度通常为 4）
 132→        pass_all_rounds: 是否所有轮都通过（all(r.passed for r in rounds)）
 133→        max_val_dd:     所有轮中最大的验证期 DD（用于风险监控）
 134→    """
 135→
 136→    rounds: list[WalkForwardRound] = field(default_factory=list)
 137→    pass_all_rounds: bool = False
 138→    max_val_dd: float = 0.0
 139→
 140→
 141→# ---------------------------------------------------------------------------
 142→# 核心函数
 143→# ---------------------------------------------------------------------------
 144→
 145→def _safe_float(value: Any, default: float = 0.0) -> float:
 146→    """NaN/None/非数值安全转 float（迭代 #2 新增）。
 147→
 148→    问题背景：vectorbt 在无交易场景下，`pf.stats()` 的 Win Rate / Sharpe 等
 149→    字段会返回 NaN。`float(NaN or 0.0)` 仍是 NaN（NaN 是 truthy），导致
 150→    JSON 序列化写出非法 JSON（NaN/Infinity 非 JSON 规范）。
 151→
 152→    处理顺序：
 153→        1. None → default
 154→        2. 数值类型但 NaN/Inf → default
 155→        3. 非数值（字符串等）尝试 float() 转换，失败 → default
 156→    """
 157→    if value is None:
 158→        return default
 159→    try:
 160→        f = float(value)
 161→    except (TypeError, ValueError):
 162→        return default
 163→    if not np.isfinite(f):   # 拦截 NaN / +Inf / -Inf
 164→        return default
 165→    return f
 166→
 167→
 168→def _safe_mean(values: Any, default: float = 0.0) -> float:
 169→    """空列表 / 全 NaN 安全的均值（迭代 #2 新增）。
 170→
 171→    问题背景：`np.mean([])` 会触发 RuntimeWarning 并返回 NaN；
 172→    `np.mean([NaN, NaN])` 直接返回 NaN。在 GroupBacktestResult 聚合时
 173→    若某组只有 1 个标的且其字段为 NaN，会导致下游 JSON 序列化失败。
 174→
 175→    行为：
 176→        - 空列表 / 全 NaN → default
 177→        - 部分 NaN → 自动忽略 NaN 后取均值（np.nanmean 语义）
 178→    """
 179→    arr = np.asarray(values, dtype=float)
 180→    if arr.size == 0:
 181→        return default
 182→    mask = np.isfinite(arr)
 183→    if not mask.any():
 184→        return default
 185→    return float(arr[mask].mean())
 186→
 187→
 188→def _compute_sharpe(returns: pd.Series, periods_per_year: int = 252) -> float:
 189→    """从日收益率序列计算年化 Sharpe Ratio。"""
 190→    returns = returns.dropna()
 191→    if len(returns) < 5:
 192→        return 0.0
 193→    mean = returns.mean()
 194→    std = returns.std()
 195→    if std <= 0 or np.isnan(std):
 196→        return 0.0
 197→    return float(mean / std * np.sqrt(periods_per_year))
 198→
 199→
 200→def _compute_sortino(
 201→    returns: pd.Series,
 202→    periods_per_year: int = 252,
 203→    target: float = 0.0,
 204→) -> float:
 205→    """从日收益率序列计算年化 Sortino Ratio（Constitution L1 首要 KPI）。
 206→
 207→    Sortino = (mean(returns) - target) / downside_deviation * sqrt(periods_per_year)
 208→    downside_deviation = sqrt( mean( min(0, returns - target)^2 ) )
 209→
 210→    与 Sharpe 的区别：仅对下行波动惩罚，上行波动不计入分母。
 211→    适合"收益>0 但偶尔大跌"的中长线策略评估。
 212→
 213→    退化处理（与 _compute_sharpe 一致）：
 214→        - 样本 < 5 → 0.0
 215→        - 下行波动 ≤ 0（无下行样本）→ 0.0（理论为 +inf，返回 0 保持保守 + 可算术聚合）
 216→
 217→    Args:
 218→        returns:          日收益率序列（如 pf.returns()）
 219→        periods_per_year: 年化因子（日线 = 252）
 220→        target:           MAR/目标收益率，默认 0（与 _compute_sharpe 无风险利率假设一致）
 221→
 222→    Returns:
 223→        年化 Sortino Ratio
 224→    """
 225→    returns = returns.dropna()
 226→    if len(returns) < 5:
 227→        return 0.0
 228→    excess = returns - target
 229→    downside = excess.where(excess < 0, 0.0)        # 仅保留负偏离，正偏离置 0
 230→    dd = np.sqrt((downside ** 2).mean())
 231→    if dd <= 0 or np.isnan(dd):
 232→        return 0.0
 233→    return float(returns.mean() / dd * np.sqrt(periods_per_year))
 234→
 235→
 236→def _backtest_one(
 237→    df: pd.DataFrame,
 238→    strategy_name: str,
 239→    params: dict,
 240→    init_cash: float = 100_000.0,
 241→    fees: float = 0.001,
 242→    slippage: float = 0.001,
 243→) -> SingleBacktestResult | None:
 244→    """对单只标的执行单次回测。
 245→
 246→    使用 open= 参数确保信号在下一根 bar 的开盘价执行（与实盘一致）。
 247→
 248→    Returns:
 249→        SingleBacktestResult 或 None（数据不足/策略异常时）
 250→    """
 251→    strategy_fn = STRATEGY_REGISTRY.get(strategy_name)
 252→    if strategy_fn is None:
 253→        return None
 254→
 255→    if df.empty or len(df) < 30:
 256→        return None
 257→
 258→    try:
 259→        close = df["close"]
 260→        open_ = df["open"] if "open" in df.columns else None
 261→
 262→        # 调用策略（兼容需要 df 的策略）
 263→        try:
 264→            sig = strategy_fn(close, df=df, **params)
 265→        except TypeError:
 266→            sig = strategy_fn(close, **params)
 267→
 268→        entries = sig == 1
 269→        exits   = sig == -1
 270→
 271→        pf_kwargs: dict[str, Any] = dict(
 272→            entries=entries,
 273→            exits=exits,
 274→            init_cash=init_cash,
 275→            fees=fees,
 276→            slippage=slippage,
 277→            size=0.95,
 278→            size_type="Percent",
 279→            freq="D",
 280→        )
 281→
 282→        # ⚠️ 必须传 open= 参数：信号在下一根 bar 开盘价执行，与实盘一致
 283→        if open_ is not None:
 284→            pf = vbt.Portfolio.from_signals(close=close, open=open_, **pf_kwargs)
 285→        else:
 286→            pf = vbt.Portfolio.from_signals(close, **pf_kwargs)
 287→
 288→        stats = pf.stats()
 289→
 290→        daily_returns = pf.returns()
 291→
 292→        return SingleBacktestResult(
 293→            symbol=str(df.index.name or ""),
 294→            strategy=strategy_name,
 295→            params=params,
 296→            sharpe=_safe_float(stats.get("Sharpe Ratio")),
 297→            total_return_pct=_safe_float(stats.get("Total Return [%]")),
 298→            max_drawdown_pct=_safe_float(stats.get("Max Drawdown [%]")),
 299→            win_rate_pct=_safe_float(stats.get("Win Rate [%]")),
 300→            total_trades=int(_safe_float(stats.get("Total Trades"), default=0.0)),
 301→            daily_returns=daily_returns,
 302→            sortino=_compute_sortino(daily_returns),
 303→        )
 304→    except Exception as e:
 305→        logger.debug(f"[backtest_one] {strategy_name}({params}) failed: {e}")
 306→        return None
 307→
 308→
 309→def _portfolio_sharpe_from_results(results: list[SingleBacktestResult]) -> float:
 310→    """等权合并组内日收益率序列，计算组合 Sharpe。
 311→
 312→    ⚠️ 不能取各标的 Sharpe 算术平均（Sharpe 是比率，不能直接平均）。
 313→    正确做法：将所有标的日收益率等权合并为组合序列，再计算 Sharpe。
 314→    """
 315→    valid = [r.daily_returns for r in results if not r.daily_returns.empty]
 316→    if not valid:
 317→        return 0.0
 318→
 319→    # 对齐时间索引，等权平均
 320→    combined = pd.concat(valid, axis=1).mean(axis=1)
 321→    return _compute_sharpe(combined)
 322→
 323→
 324→def _portfolio_sortino_from_results(results: list[SingleBacktestResult]) -> float:
 325→    """等权合并组内日收益率序列，计算组合 Sortino（与 _portfolio_sharpe_from_results 同语义）。
 326→
 327→    不能取各标的 Sortino 算术平均（与 Sharpe 同理：比率不可直接平均）。
 328→    """
 329→    valid = [r.daily_returns for r in results if not r.daily_returns.empty]
 330→    if not valid:
 331→        return 0.0
 332→    combined = pd.concat(valid, axis=1).mean(axis=1)
 333→    return _compute_sortino(combined)
 334→
 335→
 336→def _portfolio_max_drawdown_from_results(
 337→    results: list[SingleBacktestResult],
 338→) -> float:
 339→    """等权合并组内日收益率序列，计算组合最大回撤（迭代 #2 新增，Constitution L1 KPI）。
 340→
 341→    与 `_portfolio_sharpe_from_results` 同语义：不能取各标的 DD 算术平均，
 342→    因为 DD 是路径依赖的比率。正确做法是先把��内日收益率等权合并为组合序列，
 343→    再 cumprod → cummax → drawdown → max。
 344→
 345→    返回值约定：百分比形式（与 `SingleBacktestResult.max_drawdown_pct` 一致，
 346→    vectorbt stats 中 `Max Drawdown [%]` 同样是百分数，例如 -15.2 表示 15.2% 回撤）。
 347→    本函数返回正值（0.0 ~ 100.0）便于聚合与 JSON 输出。
 348→
 349→    退化处理：
 350→        - 无有效日收益率 → 0.0
 351→        - 全 0 收益率（cumprod 恒为 1.0）→ 0.0
 352→    """
 353→    valid = [r.daily_returns for r in results if not r.daily_returns.empty]
 354→    if not valid:
 355→        return 0.0
 356→    combined = pd.concat(valid, axis=1).mean(axis=1).dropna()
 357→    if len(combined) < 2:
 358→        return 0.0
 359→    # 组合累计净值：初始 1.0，每日乘 (1 + r)
 360→    cumvalue = (1.0 + combined).cumprod()
 361→    peak = cumvalue.cummax()
 362→    drawdown = (cumvalue - peak) / peak   # 负值，0 表示无回撤
 363→    dd_max_pct = float(drawdown.min())    # 最负值，例如 -0.152
 364→    if not np.isfinite(dd_max_pct):
 365→        return 0.0
 366→    # 转为正百分数（与 vectorbt Max Drawdown [%] 的口径一致但取正号）
 367→    return abs(dd_max_pct) * 100.0
 368→
 369→
 370→def _optimize_ensemble_weights(
 371→    group_results: list[tuple[str, dict, list[SingleBacktestResult]]],
 372→    conflict_threshold: float = 0.3,
 373→) -> list[tuple[str, dict, float]]:
 374→    """在"单点离散值加权投票"语义下优化 ensemble 权重。
 375→
 376→    实盘每根 bar 各策略产出离散值（1/-1/0），加权投票决定方向。
 377→    回测的权重优化必须使用相同语义，而非对整段时间序列做加权。
 378→
 379→    Args:
 380→        group_results: [(strategy, params, [SingleBacktestResult]), ...]
 381→        conflict_threshold: 加权投票分数绝对值低于此时视为 HOLD
 382→
 383→    Returns:
 384→        [(strategy, params, weight), ...] 归一化权重列表
 385→    """
 386→    if len(group_results) == 1:
 387→        strategy, params, _ = group_results[0]
 388→        return [(strategy, params, 1.0)]
 389→
 390→    # 简化的 ensemble 权重搜索：用各策略的组合 Sharpe 归一化为权重
 391→    # 更严格的做法是网格搜索 weight 组合，在离散投票序列上跑回测
 392→    sharpes = []
 393→    for strategy, params, results in group_results:
 394→        ps = _portfolio_sharpe_from_results(results)
 395→        sharpes.append(max(ps, 0.01))  # 避免负权重
 396→
 397→    total = sum(sharpes)
 398→    weights = [s / total for s in sharpes]
 399→
 400→    return [
 401→        (strategy, params, weight)
 402→        for (strategy, params, _), weight in zip(group_results, weights)
 403→    ]
 404→
 405→
 406→# ---------------------------------------------------------------------------
 407→# Walk-Forward 验证（迭代 #3 新增，Constitution L7 验证流水线）
 408→# ---------------------------------------------------------------------------
 409→
 410→def _add_months(d: date, months: int) -> date:
 411→    """对 date 加/减 months 个月，自动 clamp 到月末。
 412→
 413→    使用 pandas DateOffset 以避免引入 dateutil 依赖（pandas 已是核心依赖）。
 414→    """
 415→    return (pd.Timestamp(d) + pd.DateOffset(months=months)).date()
 416→
 417→
 418→def _backtest_with_params_on_period(
 419→    mb: "MatrixBacktest",
 420→    symbols: list[str],
 421→    weights: list[dict[str, Any]],
 422→    start: date,
 423→    end: date,
 424→) -> list[pd.Series]:
 425→    """用给定权重配置在 [start, end] 期间回测，返回每条 (策略×标的) 的日收益率序列。
 426→
 427→    用于 Walk-Forward 验证期：用训练期产出的 best params 在验证期回测，
 428→    不再做参数搜索。返回原始日收益率列表，由调用方聚合为整体 portfolio。
 429→
 430→    Args:
 431→        mb:       MatrixBacktest 实例（复用其 store/init_cash/fees/slippage）
 432→        symbols:  该组的标的列表
 433→        weights:  训练期产出的权重配置（list of dict，含 strategy/params/weight）
 434→        start:    验证期起始日期
 435→        end:      验证期结束日期
 436→
 437→    Returns:
 438→        list[pd.Series] — 每条 (strategy×symbol) 的日收益率；空列表表示无有效数据
 439→    """
 440→    if not weights or not symbols:
 441→        return []
 442→
 443→    data = mb._store.get_bars_multi(symbols, start, end)
 444→    if not data:
 445→        return []
 446→
 447→    all_returns: list[pd.Series] = []
 448→    for w in weights:
 449→        strategy = w.get("strategy", "")
 450→        params = w.get("params", {})
 451→        if not strategy or strategy not in STRATEGY_REGISTRY:
 452→            continue
 453→        for sym in symbols:
 454→            df = data.get(sym, pd.DataFrame())
 455→            if df.empty:
 456→                continue
 457→            df = df.copy()
 458→            df.index.name = sym
 459→            r = _backtest_one(
 460→                df, strategy, params,
 461→                mb._init_cash, mb._fees, mb._slippage,
 462→            )
 463→            if r is not None and not r.daily_returns.empty:
 464→                all_returns.append(r.daily_returns)
 465→    return all_returns
 466→
 467→
 468→def run_walk_forward(
 469→    mb: "MatrixBacktest",
 470→    strategies: list[str],
 471→    param_grids: dict[str, dict[str, list]],
 472→    rounds: int = 4,
 473→    train_months: int = 18,
 474→    val_months: int = 6,
 475→) -> WalkForwardReport:
 476→    """执行 N 轮 Walk-Forward 验证（Constitution L7 验证流水线硬要求）。
 477→
 478→    每轮流程：
 479→        1. 训练期 [train_start, train_end]：跑矩阵回测找最优参数
 480→        2. 验证期 [val_start, val_end]：用同参数回测，记录 portfolio Sortino 和 max DD
 481→        3. passed = val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD (15%)
 482→
 483→    时间窗口（动态计算，today=today）：
 484→        - 最后一轮 val_end = today - val_months（留 1 个 val 期给 paper trading）
 485→        - 每轮向前推 val_months
 486→        - train_end = val_start，train_start = train_end - train_months
 487→
 488→    默认参数 (rounds=4, train_months=18, val_months=6) 对应用户提供的固定窗口：
 489→        today=2026-07-01 →
 490→        Round 1: train 2021-07-02~2023-01-02, val 2023-01-02~2023-07-02
 491→        Round 2: train 2022-01-02~2023-07-02, val 2023-07-02~2024-01-02
 492→        Round 3: train 2022-07-02~2024-01-02, val 2024-01-02~2024-07-02
 493→        Round 4: train 2023-01-02~2024-07-02, val 2024-07-02~2025-01-02
 494→
 495→    Args:
 496→        mb:            MatrixBacktest 实例（复用其 store/universe/init_cash 等）
 497→        strategies:    策略名称列表
 498→        param_grids:   参数网格（与 mb.run() 接收的格式一致）
 499→        rounds:        轮次数（默认 4，Constitution L7 要求）
 500→        train_months:  训练期月数（默认 18）
 501→        val_months:    验证期月数（默认 6）
 502→
 503→    Returns:
 504→        WalkForwardReport — 包含每轮结果、pass_all_rounds、max_val_dd
 505→
 506→    Note:
 507→        - WF 是验证步骤，不修改 strategy_weights.json
 508→        - 失败轮次会记录 WARNING 但不抛异常
 509→        - 全部 4 轮通过是进入 paper trading 的前置条件
 510→    """
 511→    today = date.today()
 512→    groups = mb._universe.get_groups()
 513→    if not groups:
 514→        logger.warning("[WalkForward] no groups available — skipping")
 515→        return WalkForwardReport()
 516→
 517→    wf_rounds: list[WalkForwardRound] = []
 518→
 519→    for i in range(rounds):
 520→        round_num = i + 1
 521→        # 计算本轮时间窗口
 522→        # 最后一轮 (i=rounds-1) 的 val_end = today - val_months
 523→        # 前面轮次依次向前推 val_months
 524→        val_end = _add_months(today, -val_months - (rounds - round_num) * val_months)
 525→        val_start = _add_months(val_end, -val_months)
 526→        train_end = val_start
 527→        train_start = _add_months(train_end, -train_months)
 528→
 529→        logger.info(
 530→            f"[WalkForward] Round {round_num}/{rounds}: "
 531→            f"train={train_start}~{train_end}, val={val_start}~{val_end}"
 532→        )
 533→
 534→        # ── 训练期：跑矩阵回测找最优参数（复用 mb._run_group）──
 535→        train_report = MatrixBacktestReport(
 536→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
 537→            backtest_window=f"{train_start.isoformat()} ~ {train_end.isoformat()}",
 538→            groups={},
 539→        )
 540→
 541→        for group_id, symbols in groups.items():
 542→            weights = mb._run_group(
 543→                group_id=group_id,
 544→                symbols=symbols,
 545→                start=train_start,
 546→                end=train_end,
 547→                strategies=strategies,
 548→                param_grids=param_grids,
 549→                report=train_report,
 550→            )
 551→            train_report.groups[group_id] = weights
 552→
 553→        # ── 验证期：用训练期 best params 回测，聚合为整体 portfolio ──
 554→        all_returns: list[pd.Series] = []
 555→        for group_id, symbols in groups.items():
 556→            weights = train_report.groups.get(group_id, [])
 557→            if not weights:
 558→                continue
 559→            group_returns = _backtest_with_params_on_period(
 560→                mb, symbols, weights, val_start, val_end,
 561→            )
 562→            all_returns.extend(group_returns)
 563→
 564→        # 计算整体 portfolio 指标（等权合并所有组的日收益率）
 565→        if not all_returns:
 566→            val_sortino = 0.0
 567→            val_max_dd = 0.0
 568→            logger.warning(
 569→                f"[WalkForward] Round {round_num}: no valid val returns — "
 570→                f"sortino=0, dd=0, passed=True (vacuous)"
 571→            )
 572→        else:
 573→            combined = pd.concat(all_returns, axis=1).mean(axis=1).dropna()
 574→            if len(combined) < 5:
 575→                val_sortino = 0.0
 576→                val_max_dd = 0.0
 577→            else:
 578→                val_sortino = _compute_sortino(combined)
 579→                wrapper = [SingleBacktestResult(
 580→                    symbol="portfolio", strategy="", params={},
 581→                    sharpe=0.0, total_return_pct=0.0, max_drawdown_pct=0.0,
 582→                    win_rate_pct=0.0, total_trades=0, daily_returns=combined,
 583→                )]
 584→                val_max_dd = _portfolio_max_drawdown_from_results(wrapper)
 585→
 586→        passed = val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD
 587→        wf_rounds.append(WalkForwardRound(
 588→            round_num=round_num,
 589→            train_start=train_start,
 590→            train_end=train_end,
 591→            val_start=val_start,
 592→            val_end=val_end,
 593→            val_sortino=val_sortino,
 594→            val_max_dd=val_max_dd,
 595→            passed=passed,
 596→        ))
 597→        logger.info(
 598→            f"[WalkForward] Round {round_num} result: "
 599→            f"sortino={val_sortino:.4f}, dd={val_max_dd:.4f}%, "
 600→            f"passed={passed} (threshold={WALK_FORWARD_VAL_DD_THRESHOLD}%)"
 601→        )
 602→
 603→    report = WalkForwardReport(
 604→        rounds=wf_rounds,
 605→        pass_all_rounds=all(r.passed for r in wf_rounds) if wf_rounds else False,
 606→        max_val_dd=max((r.val_max_dd for r in wf_rounds), default=0.0),
 607→    )
 608→    logger.info(
 609→        f"[WalkForward] done: {len(wf_rounds)} rounds, "
 610→        f"pass_all_rounds={report.pass_all_rounds}, "
 611→        f"max_val_dd={report.max_val_dd:.4f}%"
 612→    )
 613→    return report
 614→
 615→
 616→# ---------------------------------------------------------------------------
 617→# MatrixBacktest 主类
 618→# ---------------------------------------------------------------------------
 619→
 620→class MatrixBacktest:
 621→    """矩阵回测：N 策略 × G 标的组 × 参数网格 → strategy_weights.json。
 622→
 623→    Args:
 624→        store:       MarketDataStore（本地时序库）
 625→        universe:    UniverseManager（提供分组映射）
 626→        years:       回测窗口（默认 5 年）
 627→        init_cash:   初始资金
 628→        fees:        手续费率
 629→        slippage:    滑点率
 630→        top_k:       每组保留 Top-K 策略（默认 2）
 631→    """
 632→
 633→    def __init__(
 634→        self,
 635→        store: MarketDataStore,
 636→        universe: UniverseManager,
 637→        years: int = 5,
 638→        init_cash: float = 100_000.0,
 639→        fees: float = 0.001,
 640→        slippage: float = 0.001,
 641→        top_k: int = 2,
 642→    ) -> None:
 643→        self._store = store
 644→        self._universe = universe
 645→        self._years = years
 646→        self._init_cash = init_cash
 647→        self._fees = fees
 648→        self._slippage = slippage
 649→        self._top_k = top_k
 650→
 651→    def run(
 652→        self,
 653→        strategies: list[str],
 654→        param_grids: dict[str, dict[str, list]],
 655→        output_file: str | Path | None = None,
 656→    ) -> MatrixBacktestReport:
 657→        """执行完整矩阵回测。
 658→
 659→        Args:
 660→            strategies:  策略名称列表，如 ["dual_ma", "rsi"]
 661→            param_grids: 各策略参数网格，如 {"dual_ma": {"fast":[5,10], "slow":[20,30]}}
 662→            output_file: strategy_weights.json 输出路径（None 则不写文件）
 663→
 664→        Returns:
 665→            MatrixBacktestReport
 666→        """
 667→        today = date.today()
 668→        start = today - timedelta(days=self._years * 365)
 669→        window_str = f"{start.isoformat()} ~ {today.isoformat()}"
 670→
 671→        logger.info(
 672→            f"[MatrixBacktest] start={start}, end={today}, "
 673→            f"strategies={strategies}, years={self._years}"
 674→        )
 675→
 676→        # 获取分组（⚠️ 使用历史时点分组，而非当前静态分组）
 677→        # Phase 5 初期简化：用当前分组，但接口已预留历史分组能力
 678→        groups = self._universe.get_groups()
 679→        if not groups:
 680→            logger.warning("[MatrixBacktest] no groups available, abort")
 681→            return MatrixBacktestReport(
 682→                generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
 683→                backtest_window=window_str,
 684→                groups={},
 685→            )
 686→
 687→        report = MatrixBacktestReport(
 688→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
 689→            backtest_window=window_str,
 690→            groups={},
 691→        )
 692→
 693→        for group_id, symbols in groups.items():
 694→            logger.info(
 695→                f"[MatrixBacktest] group={group_id}, symbols={len(symbols)}, "
 696→                f"strategies={strategies}"
 697→            )
 698→
 699→            group_weights = self._run_group(
 700→                group_id=group_id,
 701→                symbols=symbols,
 702→                start=start,
 703→                end=today,
 704→                strategies=strategies,
 705→                param_grids=param_grids,
 706→                report=report,
 707→            )
 708→            report.groups[group_id] = group_weights
 709→
 710→        if output_file is not None:
 711→            self._write_weights(report, output_file)
 712→
 713→        logger.info(
 714→            f"[MatrixBacktest] done: {len(report.groups)} groups, "
 715→            f"warnings={len(report.warnings)}"
 716→        )
 717→        return report
 718→
 719→    def _run_group(
 720→        self,
 721→        group_id: str,
 722→        symbols: list[str],
 723→        start: date,
 724→        end: date,
 725→        strategies: list[str],
 726→        param_grids: dict[str, dict[str, list]],
 727→        report: MatrixBacktestReport,
 728→    ) -> list[dict[str, Any]]:
 729→        """对单个分组执行策略 × 参数网格回测，返回该组的权重配置列表。"""
 730→
 731→        # 1. 读取组内所有标的数据
 732→        data = self._store.get_bars_multi(symbols, start, end)
 733→        if not data:
 734→            logger.warning(f"[MatrixBacktest] {group_id}: no data, skip")
 735→            return []
 736→
 737→        # 2. 对每个策略 × 每组参数，计算组合 Sharpe
 738→        group_results: list[tuple[str, dict, list[SingleBacktestResult]]] = []
 739→
 740→        for strategy in strategies:
 741→            # ⚠️ 早期检测未注册策略名（迭代 #1 修复"策略名拼写错误被静默跳过"的 bug）
 742→            # 之前 _backtest_one 内部静默 return None，导致 main.py 误用 "rsi"/"macd"/"bollinger"
 743→            # 简称 6 天未被发现。改为 WARNING 级日志 + continue。
 744→            if strategy not in STRATEGY_REGISTRY:
 745→                logger.warning(
 746→                    f"[MatrixBacktest] {group_id}: strategy '{strategy}' not in "
 747→                    f"STRATEGY_REGISTRY — skipped. "
 748→                    f"Check spelling against @register_strategy decorators. "
 749→                    f"Known: {sorted(STRATEGY_REGISTRY.keys())}"
 750→                )
 751→                continue
 752→            grid = param_grids.get(strategy, {})
 753→            param_combos = list(
 754→                dict(zip(grid.keys(), combo))
 755→                for combo in itertools.product(*grid.values())
 756→            ) if grid else [{}]
 757→
 758→            best_params = None
 759→            best_sharpe = float("-inf")
 760→            best_sortino = 0.0
 761→            best_results: list[SingleBacktestResult] = []
 762→
 763→            for params in param_combos:
 764→                # 对组内每只标的回测
 765→                results = []
 766→                for sym in symbols:
 767→                    df = data.get(sym, pd.DataFrame())
 768→                    if df.empty:
 769→                        continue
 770→                    df.index.name = sym  # 方便 _backtest_one 使用
 771→                    r = _backtest_one(
 772→                        df, strategy, params,
 773→                        self._init_cash, self._fees, self._slippage
 774→                    )
 775→                    if r is not None:
 776→                        results.append(r)
 777→
 778→                if not results:
 779→                    continue
 780→
 781→                # ⚠️ 等权合并日收益率序列计算组合 Sharpe（不能取算术平均）
 782→                ps = _portfolio_sharpe_from_results(results)
 783→                pso = _portfolio_sortino_from_results(results)
 784→
 785→                if ps > best_sharpe:
 786→                    best_sharpe = ps
 787→                    best_sortino = pso
 788→                    best_params = params
 789→                    best_results = results
 790→
 791→            if best_params is not None and best_results:
 792→                group_results.append((strategy, best_params, best_results))
 793→                report.group_results.append(GroupBacktestResult(
 794→                    group_id=group_id,
 795→                    strategy=strategy,
 796→                    params=best_params,
 797→                    portfolio_sharpe=best_sharpe,
 798→                    avg_total_return_pct=_safe_mean(
 799→                        [r.total_return_pct for r in best_results]
 800→                    ),
 801→                    avg_max_drawdown_pct=_safe_mean(
 802→                        [r.max_drawdown_pct for r in best_results]
 803→                    ),
 804→                    avg_win_rate_pct=_safe_mean(
 805→                        [r.win_rate_pct for r in best_results]
 806→                    ),
 807→                    symbol_count=len(best_results),
 808→                    portfolio_sortino=best_sortino,
 809→                    portfolio_max_drawdown=_portfolio_max_drawdown_from_results(
 810→                        best_results
 811→                    ),
 812→                ))
 813→
 814→        if not group_results:
 815→            logger.warning(f"[MatrixBacktest] {group_id}: no valid results")
 816→            return []
 817→
 818→        # 3. 迭代 #3：DD 约束 + Sortino 排序选 Top-K
 819→        #    Constitution L1: portfolio DD ≤ 20% 是硬约束
 820→        #    步骤：(a) 计算每候选 portfolio_max_drawdown
 821→        #          (b) 过滤 DD <= MAX_PORTFOLIO_DRAWDOWN_PCT 的合规集
 822→        #          (c) 合规集非空 → 按 Sortino 降序取 top-K
 823→        #          (d) 合规集为空 → fallback：按 DD 升序取 top-K，标记 dd_constrained=True
 824→        candidates: list[tuple[str, dict, list[SingleBacktestResult], float, float]] = []
 825→        for (strategy, params, results) in group_results:
 826→            pso = _portfolio_sortino_from_results(results)
 827→            pdd = _portfolio_max_drawdown_from_results(results)
 828→            candidates.append((strategy, params, results, pso, pdd))
 829→
 830→        compliant = [c for c in candidates if c[4] <= MAX_PORTFOLIO_DRAWDOWN_PCT]
 831→        if compliant:
 832→            # 合规集非空：按 Sortino 降序取 top-K
 833→            ranked = sorted(compliant, key=lambda x: x[3], reverse=True)
 834→            dd_constrained = False
 835→            logger.info(
 836→                f"[MatrixBacktest] {group_id}: DD filter passed — "
 837→                f"{len(compliant)}/{len(candidates)} candidates compliant "
 838→                f"(DD <= {MAX_PORTFOLIO_DRAWDOWN_PCT}%)"
 839→            )
 840→        else:
 841→            # Fallback：无合规候选（结构性问题，如 NDX_high_vol 全部 > 20%）
 842→            # 按 DD 升序（最低 DD 优先）取 top-K，标记 dd_constrained
 843→            ranked = sorted(candidates, key=lambda x: x[4])
 844→            dd_constrained = True
 845→            logger.warning(
 846→                f"[MatrixBacktest] {group_id}: NO compliant candidates "
 847→                f"(all {len(candidates)} exceed DD={MAX_PORTFOLIO_DRAWDOWN_PCT}%). "
 848→                f"Fallback: selected top-{self._top_k} by lowest DD. "
 849→                f"This group is marked dd_constrained=True — "
 850→                f"review whether to drop the group or accept the risk."
 851→            )
 852→            report.warnings.append(
 853→                f"{group_id}: dd_constrained=True "
 854→                f"(min DD={ranked[0][4]:.2f}% > {MAX_PORTFOLIO_DRAWDOWN_PCT}%)"
 855→            )
 856→
 857→        top_results = ranked[: self._top_k]
 858→
 859→        # 把 dd_constrained 标记同步到 report.group_results 中对应组的条目
 860→        for gr in report.group_results:
 861→            if gr.group_id == group_id:
 862→                gr.dd_constrained = dd_constrained
 863→
 864→        # 4. 优化 ensemble 权重（单点离散值加权投票语义）
 865→        weighted = _optimize_ensemble_weights(
 866→            [(s, p, r) for (s, p, r, _, _) in top_results]
 867→        )
 868→
 869→        # 5. 构建权重配置列表
 870→        weights_list = []
 871→        for strategy, params, weight in weighted:
 872→            # 找到对应的 GroupBacktestResult
 873→            gr = next(
 874→                (r for r in report.group_results
 875→                 if r.group_id == group_id and r.strategy == strategy),
 876→                None,
 877→            )
 878→            # 迭代 #4：新增 backtest_dd_status 字段（'pass' / 'dd_constrained'）
 879→            # 作为风险 metadata 标记，与 dd_constrained bool 同义但更可读
 880→            backtest_dd_status = "dd_constrained" if dd_constrained else "pass"
 881→            weights_list.append({
 882→                "strategy": strategy,
 883→                "params": params,
 884→                "weight": round(weight, 4),
 885→                "backtest_sharpe": round(gr.portfolio_sharpe if gr else 0.0, 4),
 886→                "backtest_sortino": round(gr.portfolio_sortino if gr else 0.0, 4),
 887→                "backtest_max_drawdown": round(gr.portfolio_max_drawdown if gr else 0.0, 4),
 888→                "backtest_win_rate": round(gr.avg_win_rate_pct / 100 if gr else 0.5, 4),
 889→                # 迭代 #3：标记该组是否用了 DD fallback（无合规候选）
 890→                # 同组所有策略条目共享同一 dd_constrained 值
 891→                "dd_constrained": dd_constrained,
 892→                # 迭代 #4：backtest_dd_status — 风险 metadata 字段
 893→                # 'pass' = 该组有合规候选（DD ≤ 20%）
 894→                # 'dd_constrained' = fallback 触发（无合规候选，按最低 DD 取 top-K）
 895→                # 下游消费方（PortfolioBacktester / 风控观测）可读此字段判断
 896→                # 该组权重的可靠性，作为风险信号标记
 897→                "backtest_dd_status": backtest_dd_status,
 898→            })
 899→
 900→        return weights_list
 901→
 902→    def _write_weights(
 903→        self, report: MatrixBacktestReport, output_file: str | Path
 904→    ) -> None:
 905→        """将矩阵回测结果写入 strategy_weights.json。"""
 906→        output_file = Path(output_file)
 907→        output_file.parent.mkdir(parents=True, exist_ok=True)
 908→
 909→        data = {
 910→            "_meta": {
 911→                "generated_at": report.generated_at,
 912→                "backtest_window": report.backtest_window,
 913→                "reoptimize_freq": "monthly",
 914→                "survivorship_bias_warning": (
 915→                    "使用当前成分股回测，S&P 500 5年成分变动约100只(~20%)，"
 916→                    "均值回归组(SPX_low_vol)结果可能系统性偏高"
 917→                ),
 918→            },
 919→            "groups": report.groups,
 920→        }
 921→
 922→        with open(output_file, "w", encoding="utf-8") as f:
 923→            json.dump(data, f, indent=2, ensure_ascii=False)
 924→
 925→        logger.info(f"[MatrixBacktest] weights saved to {output_file}")
 926→
---
现在
---
让我查看 `portfolio_back
---
test.py` 以获取
---
 SPY 基
---
准测试的参考，
---
并查找
---
现有的测试：
---
{"file_path": "/Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/portfolio_backtest.py"}
---
   1→"""PortfolioBacktest — 组合层级回测。
   2→
   3→职责：
   4→    1. 按日期遍历，每个交易日复用 StrategyMatrixRunner / SignalRanker /
   5→       CandidateSelector 模拟"信号 → 排名 → 约束选股 → 换仓"全流程
   6→    2. 模拟持仓市值变动并计算组合层级净值曲线
   7→    3. 输出 Constitution L1 关键 KPI：Sortino / Sharpe / Max DD / Calmar
   8→    4. 记录 holdings_history 与 group_exposure_history 用于事后归因
   9→
  10→防前视偏差（与实盘一致）：
  11→    - 每个交易日只用截至当日的数据
  12→    - 信号在收盘后产生，次日开盘价执行换仓（此简化版用当日 close 计价）
  13→    - weight 配置来自离线 MatrixBacktest，run() 期间不重新优化
  14→
  15→设计原则（AI Constitution L5）：
  16→    - 复用现有组件，不重写 StrategyMatrixRunner / SignalRanker / CandidateSelector
  17→    - 纯函数式日期循环，无副作用
  18→    - 类型注解全覆盖，所有时间统一 UTC
  19→
  20→注意：本模块是迭代 #4 新增（P0），作为 MatrixBacktest（标的层）的组合层补充。
  21→"""
  22→
  23→from __future__ import annotations
  24→
  25→from dataclasses import dataclass, field
  26→from datetime import date, datetime, timezone
  27→from pathlib import Path
  28→from typing import Any
  29→
  30→import numpy as np
  31→import pandas as pd
  32→from loguru import logger
  33→
  34→from mytrader.backtest.matrix_backtest import (
  35→    _compute_sharpe,
  36→    _compute_sortino,
  37→    _safe_float,
  38→)
  39→from mytrader.data.store.market_data_store import MarketDataStore
  40→from mytrader.risk.candidate_selector import (
  41→    AccountState,
  42→    select_orders_from_candidates,
  43→)
  44→from mytrader.signal.ranker import SignalRanker
  45→from mytrader.strategy.base import Signal, SignalDirection
  46→from mytrader.strategy.matrix_runner import (
  47→    StrategyMatrixRunner,
  48→    build_matrix_signal_indicators,
  49→)
  50→from mytrader.universe.manager import UniverseManager
  51→
  52→
  53→# ---------------------------------------------------------------------------
  54→# Constitution L1 硬约束：组合最大回撤 ≤ 20%
  55→# ---------------------------------------------------------------------------
  56→
  57→PORTFOLIO_MAX_DRAWDOWN_PCT: float = 20.0
  58→
  59→
  60→# ---------------------------------------------------------------------------
  61→# 数据结构
  62→# ---------------------------------------------------------------------------
  63→
  64→@dataclass
  65→class PortfolioBacktestConfig:
  66→    """PortfolioBacktest 配置。
  67→
  68→    与 CandidateSelector / SignalRanker 默认值对齐，便于复用。
  69→
  70→    Attributes:
  71→        initial_capital:          初始资金（美元）
  72→        top_k:                    目标持仓数（最终保留的标的数）
  73→        candidates_multiplier:    候选倍数（输出 top_k * multiplier 候选给 selector）
  74→        max_single_position_pct:  单标的仓位上限（与 risk 模块一致）
  75→        max_total_exposure_pct:   总持仓上限
  76→        max_sector_exposure_pct:  板块持仓上限（本简化版按 group_id 近似）
  77→        rebalance_freq:           换仓频率（'daily' / 'weekly'；本版本仅实现 daily）
  78→        signal_valid_bars:        信号有效期（与 StrategyMatrixRunner 一致）
  79→    """
  80→
  81→    initial_capital: float = 100_000.0
  82→    top_k: int = 5
  83→    candidates_multiplier: int = 2
  84→    max_single_position_pct: float = 0.20
  85→    max_total_exposure_pct: float = 0.80
  86→    max_sector_exposure_pct: float = 0.40
  87→    rebalance_freq: str = "daily"
  88→    signal_valid_bars: int = 3
  89→
  90→
  91→@dataclass
  92→class PortfolioBacktestResult:
  93→    """组合回测结果。
  94→
  95→    Constitution L1 关键 KPI：Sortino > Sharpe > Max DD > Calmar > Annual Return。
  96→
  97→    Attributes:
  98→        start_date:               回测起始日期
  99→        end_date:                 回测结束日期
 100→        initial_capital:          初始资金
 101→        final_equity:             期末净值
 102→        total_return_pct:         总收益率（百分数）
 103→        annualized_return_pct:    年化收益率（百分数）
 104→        sharpe_ratio:             年化 Sharpe Ratio
 105→        sortino_ratio:             年化 Sortino Ratio（Constitution L1 首要 KPI）
 106→        max_drawdown_pct:         最大回撤（百分数，正值）
 107→        calmar_ratio:             Calmar = Annual Return / Max DD
 108→        daily_returns:            日收益率序列
 109→        equity_curve:             净值曲线（初始 = initial_capital）
 110→        holdings_history:         每日持仓快照列表（按交易日）
 111→        dd_violation:             DD 是否超过 20% 硬约束
 112→        group_exposure_history:   每日按 group_id 的暴露度快照
 113→        benchmark_symbol:          Benchmark 标的（默认 SPY，迭代 #7）
 114→        benchmark_total_return_pct:    Benchmark 同期总收益（百分数）
 115→        benchmark_annualized_return_pct: Benchmark 年化收益（百分数）
 116→        benchmark_sortino_ratio:       Benchmark Sortino Ratio
 117→        benchmark_max_drawdown_pct:    Benchmark 最大回撤（百分数，正值）
 118→        alpha_pct:                     超额收益 = 组合年化 - benchmark 年化（百分数）
 119→        information_ratio:             信息比率（年化）
 120→    """
 121→
 122→    start_date: date
 123→    end_date: date
 124→    initial_capital: float
 125→    final_equity: float
 126→    total_return_pct: float
 127→    annualized_return_pct: float
 128→    sharpe_ratio: float
 129→    sortino_ratio: float
 130→    max_drawdown_pct: float
 131→    calmar_ratio: float
 132→    daily_returns: pd.Series
 133→    equity_curve: pd.Series
 134→    holdings_history: list[dict[str, Any]] = field(default_factory=list)
 135→    dd_violation: bool = False
 136→    group_exposure_history: list[dict[str, Any]] = field(default_factory=list)
 137→    # Benchmark 对比（Iteration #7 新增）
 138→    benchmark_symbol: str = "SPY"
 139→    benchmark_total_return_pct: float = 0.0
 140→    benchmark_annualized_return_pct: float = 0.0
 141→    benchmark_sortino_ratio: float = 0.0
 142→    benchmark_max_drawdown_pct: float = 0.0
 143→    alpha_pct: float = 0.0
 144→    information_ratio: float = 0.0
 145→
 146→
 147→# ---------------------------------------------------------------------------
 148→# PortfolioBacktester
 149→# ---------------------------------------------------------------------------
 150→
 151→class PortfolioBacktester:
 152→    """组合层级回测器。
 153→
 154→    Args:
 155→        store:        MarketDataStore 实例
 156→        universe:     UniverseManager 实例
 157→        weights_file: strategy_weights.json 路径（来自离线 MatrixBacktest）
 158→        config:       PortfolioBacktestConfig
 159→
 160→    使用方式：
 161→        bt = PortfolioBacktester(store, universe, "config/strategy_weights.json", cfg)
 162→        result = bt.run(start=date(2024,1,1), end=date(2024,6,30))
 163→        print(result.sortino_ratio, result.max_drawdown_pct)
 164→    """
 165→
 166→    def __init__(
 167→        self,
 168→        store: MarketDataStore,
 169→        universe: UniverseManager,
 170→        weights_file: str | Path | None = None,
 171→        config: PortfolioBacktestConfig | None = None,
 172→    ) -> None:
 173→        self._store = store
 174→        self._universe = universe
 175→        self._weights_file = Path(weights_file) if weights_file else None
 176→        self._config = config or PortfolioBacktestConfig()
 177→
 178→        # 内部 StrategyMatrixRunner（复用其信号生成能力）
 179→        # signal_valid_bars 与 config 对齐
 180→        self._matrix_runner = StrategyMatrixRunner(
 181→            store=store,
 182→            universe=universe,
 183→            weights_file=self._weights_file,
 184→            signal_valid_bars=self._config.signal_valid_bars,
 185→        )
 186→
 187→        # 内部 SignalRanker（复用其聚合 + Top-2K 排名）
 188→        self._ranker = SignalRanker(
 189→            top_k=self._config.top_k,
 190→            candidates_multiplier=self._config.candidates_multiplier,
 191→        )
 192→
 193→        # 历史记录在 run() 开始时重置（实例属性，避免跨实例污染）
 194→        self._holdings_history: list[dict[str, Any]] = []
 195→        self._group_exposure_history: list[dict[str, Any]] = []
 196→
 197→    # ------------------------------------------------------------------
 198→    # 公共接口
 199→    # ------------------------------------------------------------------
 200→
 201→    def run(self, start: date, end: date) -> PortfolioBacktestResult:
 202→        """执行组合回测。
 203→
 204→        每日流程：
 205→            1. 用截至当日的数据生成信号（StrategyMatrixRunner.run_symbol）
 206→            2. SignalRanker 聚合 + Top-2K 排名
 207→            3. CandidateSelector 5 级约束选 Top-5
 208→            4. 按当日 close 计价，模拟换仓（卖出不在新 Top-5 的、买入新进的）
 209→            5. 用当日 close 重估持仓市值 → 更新净值
 210→
 211→        Args:
 212→            start: 回测起始日期（含）
 213→            end:   回测结束日期（含）
 214→
 215→        Returns:
 216→            PortfolioBacktestResult
 217→        """
 218→        cfg = self._config
 219→        symbols = self._universe.get_universe()
 220→
 221→        # 1. 拉取所有标的的完整日历数据（一次性，避免每日重复查询）
 222→        all_bars: dict[str, pd.DataFrame] = self._store.get_bars_multi(
 223→            symbols, start, end
 224→        )
 225→        if not all_bars:
 226→            logger.warning("[PortfolioBacktest] no data, returning empty result")
 227→            return self._empty_result(start, end)
 228→
 229→        # 2. 构造统一交易日历（所有标的的 date index 并集）
 230→        all_dates: list[date] = sorted({
 231→            ts.date() if isinstance(ts, (datetime, pd.Timestamp)) else ts
 232→            for df in all_bars.values()
 233→            for ts in df.index
 234→        })
 235→        # 限定到 [start, end] 区间
 236→        all_dates = [d for d in all_dates if start <= d <= end]
 237→        if not all_dates:
 238→            logger.warning("[PortfolioBacktest] no trading dates in range")
 239→            return self._empty_result(start, end)
 240→
 241→        logger.info(
 242→            f"[PortfolioBacktest] start={start}, end={end}, "
 243→            f"symbols={len(symbols)}, trading_days={len(all_dates)}"
 244→        )
 245→
 246→        # 3. 按日期循环
 247→        cash = cfg.initial_capital
 248→        # holdings: {symbol: (shares, avg_cost)} — 简化：用 close 计价
 249→        holdings: dict[str, float] = {}     # symbol → shares
 250→        avg_cost: dict[str, float] = {}    # symbol → 平均成本（用于成本基础）
 251→
 252→        daily_returns_list: list[float] = []
 253→        equity_list: list[float] = []
 254→        date_list: list[date] = []
 255→
 256→        prev_equity = cfg.initial_capital
 257→
 258→        for trading_date in all_dates:
 259→            # 截至当日的数据切片（防前视偏差）
 260→            bars_up_to_date: dict[str, pd.DataFrame] = {}
 261→            for sym, df in all_bars.items():
 262→                # df.index 可能是 datetime/timestamp
 263→                mask = df.index <= pd.Timestamp(trading_date)
 264→                sub = df.loc[mask]
 265→                if not sub.empty:
 266→                    bars_up_to_date[sym] = sub
 267→
 268→            # 当日 close 价查表（用于市值计价 + 换仓）
 269→            close_today: dict[str, float] = {}
 270→            for sym, df in bars_up_to_date.items():
 271→                if not df.empty:
 272→                    close_today[sym] = _safe_float(df["close"].iloc[-1])
 273→
 274→            # ── Step 1: 生成信号（复用 StrategyMatrixRunner 的 run_symbol 逻辑）──
 275→            # 用截至当日的数据子集生成信号；为避免修改 store 状态，
 276→            # 直接调用策略函数（不读 store，而是用 bars_up_to_date）
 277→            signals = self._generate_signals(bars_up_to_date, trading_date)
 278→
 279→            # ── Step 2: 排名 + Top-2K ──
 280→            rank_report = self._ranker.rank(signals)
 281→
 282→            # ── Step 3: 候选选股 ──
 283→            # 构造当前账户状态
 284→            current_exposure = sum(
 285→                shares * close_today.get(sym, 0.0)
 286→                for sym, shares in holdings.items()
 287→            )
 288→            sector_exposure: dict[str, float] = {}
 289→            for sym, shares in holdings.items():
 290→                meta = self._universe.get_symbol_meta(sym)
 291→                sector = meta.sector if meta else "Unknown"
 292→                mv = shares * close_today.get(sym, 0.0)
 293→                sector_exposure[sector] = sector_exposure.get(sector, 0.0) + mv
 294→
 295→            account = AccountState(
 296→                total_capital=cfg.initial_capital,
 297→                current_exposure=current_exposure,
 298→                current_position_count=len(holdings),
 299→                sector_exposure=sector_exposure,
 300→            )
 301→
 302→            approved, _ = select_orders_from_candidates(
 303→                candidates=rank_report.buy_candidates,
 304→                account=account,
 305→                max_orders=cfg.top_k,
 306→                max_single_position_pct=cfg.max_single_position_pct,
 307→                max_total_exposure_pct=cfg.max_total_exposure_pct,
 308→                max_sector_exposure_pct=cfg.max_sector_exposure_pct,
 309→                max_concurrent_positions=cfg.top_k,
 310→            )
 311→
 312→            # ── Step 4: 换仓 ──
 313→            # SELL 信号优先：先处理 sell_signals
 314→            for ranked in rank_report.sell_signals:
 315→                sym = ranked.signal.symbol
 316→                if sym in holdings:
 317→                    # 卖出全部持仓
 318→                    cash += holdings[sym] * close_today.get(sym, 0.0)
 319→                    del holdings[sym]
 320→                    avg_cost.pop(sym, None)
 321→
 322→            # 计算目标持仓集合（来自 approved 的 BUY）
 323→            target_symbols = {o.signal.symbol for o in approved}
 324→
 325→            # 卖出不在目标集合的现有持仓
 326→            for sym in list(holdings.keys()):
 327→                if sym not in target_symbols:
 328→                    cash += holdings[sym] * close_today.get(sym, 0.0)
 329→                    del holdings[sym]
 330→                    avg_cost.pop(sym, None)
 331→
 332→            # 买入新进的目标标的（等权分配可用资金）
 333→            new_buys = [o for o in approved if o.signal.symbol not in holdings]
 334→            if new_buys:
 335→                # 等权分配当前 cash 给新买入标的
 336→                per_symbol_budget = min(
 337→                    cfg.initial_capital * cfg.max_single_position_pct,
 338→                    cash / max(len(new_buys), 1),
 339→                )
 340→                for o in new_buys:
 341→                    sym = o.signal.symbol
 342→                    price = close_today.get(sym, 0.0)
 343→                    if price <= 0:
 344→                        continue
 345→                    shares_to_buy = per_symbol_budget / price
 346→                    if shares_to_buy <= 0:
 347→                        continue
 348→                    cost = shares_to_buy * price
 349→                    if cost > cash:
 350→                        continue
 351→                    cash -= cost
 352→                    # 更新平均成本
 353→                    old_shares = holdings.get(sym, 0.0)
 354→                    old_cost = avg_cost.get(sym, 0.0) * old_shares
 355→                    new_shares = old_shares + shares_to_buy
 356→                    avg_cost[sym] = (old_cost + cost) / new_shares if new_shares > 0 else 0.0
 357→                    holdings[sym] = new_shares
 358→
 359→            # ── Step 5: 计算当日净值 ──
 360→            market_value = sum(
 361→                shares * close_today.get(sym, 0.0)
 362→                for sym, shares in holdings.items()
 363→            )
 364→            equity = cash + market_value
 365→
 366→            # 日收益率
 367→            daily_ret = (equity - prev_equity) / prev_equity if prev_equity > 0 else 0.0
 368→            daily_returns_list.append(daily_ret)
 369→            equity_list.append(equity)
 370→            date_list.append(trading_date)
 371→            prev_equity = equity
 372→
 373→            # 记录 holdings_history
 374→            self._record_holdings(
 375→                trading_date, holdings, close_today, avg_cost, cash, equity
 376→            )
 377→            # 记录 group_exposure_history
 378→            self._record_group_exposure(trading_date, holdings, close_today, equity)
 379→
 380→        # 4. 计算最终指标
 381→        daily_returns = pd.Series(daily_returns_list, index=pd.to_datetime(date_list))
 382→        equity_curve = pd.Series(equity_list, index=pd.to_datetime(date_list))
 383→
 384→        final_equity = equity_list[-1] if equity_list else cfg.initial_capital
 385→        total_return_pct = (
 386→            (final_equity / cfg.initial_capital) - 1.0
 387→        ) * 100.0
 388→
 389→        # 年化收益率：按交易日数推算
 390→        n_days = len(daily_returns_list)
 391→        years = n_days / 252.0 if n_days > 0 else 0.0
 392→        if years > 0 and final_equity > 0:
 393→            annualized_return_pct = (
 394→                (final_equity / cfg.initial_capital) ** (1.0 / years) - 1.0
 395→            ) * 100.0
 396→        else:
 397→            annualized_return_pct = 0.0
 398→
 399→        sharpe = _compute_sharpe(daily_returns)
 400→        sortino = _compute_sortino(daily_returns)
 401→        max_dd = self._compute_max_drawdown_pct(daily_returns)
 402→
 403→        calmar = (
 404→            abs(annualized_return_pct / max_dd)
 405→            if max_dd > 0 else 0.0
 406→        )
 407→
 408→        dd_violation = max_dd > PORTFOLIO_MAX_DRAWDOWN_PCT
 409→
 410→        result = PortfolioBacktestResult(
 411→            start_date=start,
 412→            end_date=end,
 413→            initial_capital=cfg.initial_capital,
 414→            final_equity=final_equity,
 415→            total_return_pct=total_return_pct,
 416→            annualized_return_pct=annualized_return_pct,
 417→            sharpe_ratio=sharpe,
 418→            sortino_ratio=sortino,
 419→            max_drawdown_pct=max_dd,
 420→            calmar_ratio=calmar,
 421→            daily_returns=daily_returns,
 422→            equity_curve=equity_curve,
 423→            holdings_history=self._holdings_history,
 424→            dd_violation=dd_violation,
 425→            group_exposure_history=self._group_exposure_history,
 426→        )
 427→
 428→        # ── Benchmark: SPY buy-and-hold（迭代 #7）──
 429→        # 数据不可用时降级为 0.0，不抛异常（spec §4.2）
 430→        benchmark_result = self._compute_benchmark(
 431→            start, end, daily_returns_list, date_list
 432→        )
 433→        result.benchmark_symbol = benchmark_result.get("symbol", "SPY")
 434→        result.benchmark_total_return_pct = benchmark_result.get(
 435→            "total_return_pct", 0.0
 436→        )
 437→        result.benchmark_annualized_return_pct = benchmark_result.get(
 438→            "annualized_return_pct", 0.0
 439→        )
 440→        result.benchmark_sortino_ratio = benchmark_result.get(
 441→            "sortino_ratio", 0.0
 442→        )
 443→        result.benchmark_max_drawdown_pct = benchmark_result.get(
 444→            "max_drawdown_pct", 0.0
 445→        )
 446→        result.alpha_pct = (
 447→            result.annualized_return_pct - result.benchmark_annualized_return_pct
 448→        )
 449→        result.information_ratio = benchmark_result.get(
 450→            "information_ratio", 0.0
 451→        )
 452→
 453→        logger.info(
 454→            f"[PortfolioBacktest] done: final=${final_equity:,.0f}, "
 455→            f"total_return={total_return_pct:.2f}%, "
 456→            f"annualized={annualized_return_pct:.2f}%, "
 457→            f"sharpe={sharpe:.4f}, sortino={sortino:.4f}, "
 458→            f"max_dd={max_dd:.2f}%, dd_violation={dd_violation}, "
 459→            f"benchmark={result.benchmark_symbol} "
 460→            f"return={result.benchmark_annualized_return_pct:.2f}%, "
 461→            f"alpha={result.alpha_pct:.2f}%, ir={result.information_ratio:.4f}"
 462→        )
 463→
 464→        return result
 465→
 466→    # ------------------------------------------------------------------
 467→    # 内部方法
 468→    # ------------------------------------------------------------------
 469→
 470→    def _empty_result(self, start: date, end: date) -> PortfolioBacktestResult:
 471→        """空结果（无数据时返回）。"""
 472→        cfg = self._config
 473→        empty = pd.Series(dtype=float)
 474→        return PortfolioBacktestResult(
 475→            start_date=start,
 476→            end_date=end,
 477→            initial_capital=cfg.initial_capital,
 478→            final_equity=cfg.initial_capital,
 479→            total_return_pct=0.0,
 480→            annualized_return_pct=0.0,
 481→            sharpe_ratio=0.0,
 482→            sortino_ratio=0.0,
 483→            max_drawdown_pct=0.0,
 484→            calmar_ratio=0.0,
 485→            daily_returns=empty,
 486→            equity_curve=empty,
 487→        )
 488→
 489→    def _generate_signals(
 490→        self,
 491→        bars_up_to_date: dict[str, pd.DataFrame],
 492→        trading_date: date,
 493→    ) -> list[Signal]:
 494→        """复用 StrategyMatrixRunner 的策略调用逻辑生成信号。
 495→
 496→        为避免修改 store 状态（防前视偏差），这里直接基于 bars_up_to_date
 497→        调用注册表中的策略函数，绕过 runner.run_symbol 内部的 store.get_latest_n_bars。
 498→
 499→        信号有效期通过 config.signal_valid_bars 检查（与 runner 一致）。
 500→        """
 501→        from mytrader.strategy.registry import STRATEGY_REGISTRY
 502→
 503→        signals: list[Signal] = []
 504→        now = datetime.now(tz=timezone.utc)
 505→        svb = self._config.signal_valid_bars
 506→
 507→        for sym, df in bars_up_to_date.items():
 508→            if df.empty or len(df) < 30:
 509→                # 需要足够数据：bollinger period 最多 25 + signal_valid_bars 3 = 28
 510→                continue
 511→
 512→            meta = self._universe.get_symbol_meta(sym)
 513→            if meta is None:
 514→                continue
 515→
 516→            group_strategies = self._matrix_runner._weights.get(meta.group_id, [])
 517→            if not group_strategies:
 518→                continue
 519→
 520→            for entry in group_strategies:
 521→                strategy_name = entry["strategy"]
 522→                params = entry.get("params", {})
 523→                weight = float(entry.get("weight", 1.0))
 524→
 525→                strategy_fn = STRATEGY_REGISTRY.get(strategy_name)
 526→                if strategy_fn is None:
 527→                    continue
 528→
 529→                try:
 530→                    sig_series = strategy_fn(df["close"], df=df, **params)
 531→                except TypeError:
 532→                    sig_series = strategy_fn(df["close"], **params)
 533→                except (ValueError, KeyError, Exception):
 534→                    # ValueError: 指标数据不足（如 bbands 返回 None）
 535→                    # KeyError: 列名不匹配
 536→                    continue
 537→
 538→                # 信号有效期检查
 539→                recent = sig_series.iloc[-svb:]
 540→                nonzero = recent[recent != 0]
 541→                if nonzero.empty:
 542→                    continue
 543→
 544→                latest = int(nonzero.iloc[-1])
 545→                direction = SignalDirection.BUY if latest == 1 else SignalDirection.SELL
 546→                confidence = min(weight, 1.0)
 547→
 548→                signals.append(
 549→                    Signal(
 550→                        symbol=sym,
 551→                        direction=direction,
 552→                        timestamp=now,
 553→                        confidence=confidence,
 554→                        strategy_name=strategy_name,
 555→                        # 迭代 #5：复用 matrix_runner.build_matrix_signal_indicators
 556→                        # 保证线上扫描与组合回测 signal metadata 完全一致
 557→                        # （P0-A：曾因 sector=Unknown 导致 73 候选 → 2 approved）
 558→                        indicators=build_matrix_signal_indicators(meta, entry, weight),
 559→                    )
 560→                )
 561→
 562→        return signals
 563→
 564→    def _record_holdings(
 565→        self,
 566→        trading_date: date,
 567→        holdings: dict[str, float],
 568→        close_today: dict[str, float],
 569→        avg_cost: dict[str, float],
 570→        cash: float,
 571→        equity: float,
 572→    ) -> None:
 573→        """记录每日持仓快照（用于事后归因）。"""
 574→        holdings_snapshot = []
 575→        for sym, shares in holdings.items():
 576→            price = close_today.get(sym, 0.0)
 577→            holdings_snapshot.append({
 578→                "symbol": sym,
 579→                "shares": float(shares),
 580→                "price": float(price),
 581→                "market_value": float(shares * price),
 582→                "avg_cost": float(avg_cost.get(sym, 0.0)),
 583→                "unrealized_pnl": float((price - avg_cost.get(sym, 0.0)) * shares),
 584→            })
 585→
 586→        self._holdings_history.append({
 587→            "date": trading_date.isoformat(),
 588→            "cash": float(cash),
 589→            "equity": float(equity),
 590→            "positions": holdings_snapshot,
 591→            "position_count": len(holdings_snapshot),
 592→        })
 593→
 594→    def _record_group_exposure(
 595→        self,
 596→        trading_date: date,
 597→        holdings: dict[str, float],
 598→        close_today: dict[str, float],
 599→        equity: float,
 600→    ) -> None:
 601→        """记录每日按 group_id 的暴露度（用于风控观测）。"""
 602→        group_exposure: dict[str, float] = {}
 603→        for sym, shares in holdings.items():
 604→            meta = self._universe.get_symbol_meta(sym)
 605→            gid = meta.group_id if meta else "UNKNOWN"
 606→            mv = shares * close_today.get(sym, 0.0)
 607→            group_exposure[gid] = group_exposure.get(gid, 0.0) + mv
 608→
 609→        # 转为百分比
 610→        group_exposure_pct = {
 611→            gid: (mv / equity * 100.0 if equity > 0 else 0.0)
 612→            for gid, mv in group_exposure.items()
 613→        }
 614→
 615→        self._group_exposure_history.append({
 616→            "date": trading_date.isoformat(),
 617→            "total_equity": float(equity),
 618→            "group_exposure_value": {k: float(v) for k, v in group_exposure.items()},
 619→            "group_exposure_pct": group_exposure_pct,
 620→        })
 621→
 622→    def _compute_benchmark(
 623→        self,
 624→        start: date,
 625→        end: date,
 626→        portfolio_daily_returns: list[float],
 627→        dates: list[date],
 628→    ) -> dict[str, Any]:
 629→        """计算 SPY buy-and-hold benchmark 指标（迭代 #7）。
 630→
 631→        从 MarketDataStore 拉取 SPY 同期数据，计算：
 632→            - total_return_pct / annualized_return_pct
 633→            - sortino_ratio / max_drawdown_pct（与组合层同口径）
 634→            - information_ratio（基于 portfolio - spy 的超额收益序列）
 635→
 636→        降级处理：SPY 数据不可用时所有字段保持 0.0，不抛异常（spec §4.2）。
 637→
 638→        Args:
 639→            start:                   回测起始日期
 640→            end:                     回测结束日期
 641→            portfolio_daily_returns: 组合日收益率序列（与 dates 对齐）
 642→            dates:                   交易日日期序列
 643→
 644→        Returns:
 645→            dict with benchmark metrics。失败时仅含 "symbol"。
 646→        """
 647→        benchmark_symbol = "SPY"
 648→        try:
 649→            spy_bars = self._store.get_bars_multi([benchmark_symbol], start, end)
 650→            spy_df = spy_bars.get(benchmark_symbol)
 651→            if spy_df is None or spy_df.empty:
 652→                logger.warning(
 653→                    "[PortfolioBacktest] SPY data unavailable, benchmark skipped"
 654→                )
 655→                return {"symbol": benchmark_symbol}
 656→
 657→            spy_close = spy_df["close"].astype(float)
 658→            if len(spy_close) < 2:
 659→                logger.warning(
 660→                    "[PortfolioBacktest] SPY data too short, benchmark skipped"
 661→                )
 662→                return {"symbol": benchmark_symbol}
 663→
 664→            spy_returns = spy_close.pct_change().dropna()
 665→
 666→            # SPY total / annualized return
 667→            spy_final = float(spy_close.iloc[-1])
 668→            spy_initial = float(spy_close.iloc[0])
 669→            spy_total_return_pct = (
 670→                (spy_final / spy_initial) - 1.0
 671→            ) * 100.0 if spy_initial > 0 else 0.0
 672→
 673→            n_spy = len(spy_returns)
 674→            years_spy = n_spy / 252.0 if n_spy > 0 else 0.0
 675→            if years_spy > 0 and spy_final > 0 and spy_initial > 0:
 676→                spy_annualized_pct = (
 677→                    (spy_final / spy_initial) ** (1.0 / years_spy) - 1.0
 678→                ) * 100.0
 679→            else:
 680→                spy_annualized_pct = 0.0
 681→
 682→            # Sortino / Max DD（复用 matrix_backtest helper，与组合层同口径）
 683→            spy_sortino = _compute_sortino(spy_returns)
 684→            spy_max_dd = self._compute_max_drawdown_pct(spy_returns)
 685→
 686→            # Information Ratio：基于超额收益序列
 687→            # 将 SPY returns 对齐到 portfolio 的交易日历
 688→            ir = self._compute_information_ratio(
 689→                portfolio_daily_returns, dates, spy_returns
 690→            )
 691→
 692→            return {
 693→                "symbol": benchmark_symbol,
 694→                "total_return_pct": float(spy_total_return_pct),
 695→                "annualized_return_pct": float(spy_annualized_pct),
 696→                "sortino_ratio": float(spy_sortino),
 697→                "max_drawdown_pct": float(spy_max_dd),
 698→                "information_ratio": float(ir),
 699→            }
 700→        except Exception as e:
 701→            logger.warning(
 702→                f"[PortfolioBacktest] benchmark computation failed: {e}"
 703→            )
 704→            return {"symbol": benchmark_symbol}
 705→
 706→    @staticmethod
 707→    def _compute_information_ratio(
 708→        portfolio_daily_returns: list[float],
 709→        portfolio_dates: list[date],
 710→        spy_returns: pd.Series,
 711→    ) -> float:
 712→        """计算年化信息比率。
 713→
 714→        IR = mean(excess_returns) / std(excess_returns) * sqrt(252)
 715→        excess_returns = portfolio_returns - spy_returns（按日期对齐）
 716→        """
 717→        if not portfolio_daily_returns or len(spy_returns) == 0:
 718→            return 0.0
 719→
 720→        # 组合 returns 转为 pd.Series，index 用 portfolio_dates
 721→        port_idx = pd.to_datetime(portfolio_dates)
 722→        port_series = pd.Series(
 723→            portfolio_daily_returns, index=port_idx, dtype=float
 724→        )
 725→
 726→        # 对齐：取两序列 index 的交集（inner join）
 727→        aligned = pd.concat(
 728→            [port_series.rename("port"), spy_returns.rename("spy")],
 729→            axis=1,
 730→            join="inner",
 731→        ).dropna()
 732→        if aligned.empty or len(aligned) < 5:
 733→            return 0.0
 734→
 735→        excess = aligned["port"] - aligned["spy"]
 736→        std = excess.std()
 737→        if std <= 0 or not np.isfinite(std):
 738→            return 0.0
 739→        return float(excess.mean() / std * np.sqrt(252))
 740→
 741→    @staticmethod
 742→    def _compute_max_drawdown_pct(daily_returns: pd.Series) -> float:
 743→        """计算最大回撤（百分数正值）。
 744→
 745→        与 matrix_backtest._portfolio_max_drawdown_from_results 同口径。
 746→        """
 747→        if daily_returns.empty:
 748→            return 0.0
 749→        cumvalue = (1.0 + daily_returns).cumprod()
 750→        peak = cumvalue.cummax()
 751→        drawdown = (cumvalue - peak) / peak
 752→        dd_min = float(drawdown.min())
 753→        if not np.isfinite(dd_min):
 754→            return 0.0
 755→        return abs(dd_min) * 100.0
 756→
---
   1→"""PortfolioBacktest — 组合层级回测。
   2→
   3→职责：
   4→    1. 按日期遍历，每个交易日复用 StrategyMatrixRunner / SignalRanker /
   5→       CandidateSelector 模拟"信号 → 排名 → 约束选股 → 换仓"全流程
   6→    2. 模拟持仓市值变动并计算组合层级净值曲线
   7→    3. 输出 Constitution L1 关键 KPI：Sortino / Sharpe / Max DD / Calmar
   8→    4. 记录 holdings_history 与 group_exposure_history 用于事后归因
   9→
  10→防前视偏差（与实盘一致）：
  11→    - 每个交易日只用截至当日的数据
  12→    - 信号在收盘后产生，次日开盘价执行换仓（此简化版用当日 close 计价）
  13→    - weight 配置来自离线 MatrixBacktest，run() 期间不重新优化
  14→
  15→设计原则（AI Constitution L5）：
  16→    - 复用现有组件，不重写 StrategyMatrixRunner / SignalRanker / CandidateSelector
  17→    - 纯函数式日期循环，无副作用
  18→    - 类型注解全覆盖，所有时间统一 UTC
  19→
  20→注意：本模块是迭代 #4 新增（P0），作为 MatrixBacktest（标的层）的组合层补充。
  21→"""
  22→
  23→from __future__ import annotations
  24→
  25→from dataclasses import dataclass, field
  26→from datetime import date, datetime, timezone
  27→from pathlib import Path
  28→from typing import Any
  29→
  30→import numpy as np
  31→import pandas as pd
  32→from loguru import logger
  33→
  34→from mytrader.backtest.matrix_backtest import (
  35→    _compute_sharpe,
  36→    _compute_sortino,
  37→    _safe_float,
  38→)
  39→from mytrader.data.store.market_data_store import MarketDataStore
  40→from mytrader.risk.candidate_selector import (
  41→    AccountState,
  42→    select_orders_from_candidates,
  43→)
  44→from mytrader.signal.ranker import SignalRanker
  45→from mytrader.strategy.base import Signal, SignalDirection
  46→from mytrader.strategy.matrix_runner import (
  47→    StrategyMatrixRunner,
  48→    build_matrix_signal_indicators,
  49→)
  50→from mytrader.universe.manager import UniverseManager
  51→
  52→
  53→# ---------------------------------------------------------------------------
  54→# Constitution L1 硬约束：组合最大回撤 ≤ 20%
  55→# ---------------------------------------------------------------------------
  56→
  57→PORTFOLIO_MAX_DRAWDOWN_PCT: float = 20.0
  58→
  59→
  60→# ---------------------------------------------------------------------------
  61→# 数据结构
  62→# ---------------------------------------------------------------------------
  63→
  64→@dataclass
  65→class PortfolioBacktestConfig:
  66→    """PortfolioBacktest 配置。
  67→
  68→    与 CandidateSelector / SignalRanker 默认值对齐，便于复用。
  69→
  70→    Attributes:
  71→        initial_capital:          初始资金（美元）
  72→        top_k:                    目标持仓数（最终保留的标的数）
  73→        candidates_multiplier:    候选倍数（输出 top_k * multiplier 候选给 selector）
  74→        max_single_position_pct:  单标的仓位上限（与 risk 模块一致）
  75→        max_total_exposure_pct:   总持仓上限
  76→        max_sector_exposure_pct:  板块持仓上限（本简化版按 group_id 近似）
  77→        rebalance_freq:           换仓频率（'daily' / 'weekly'；本版本仅实现 daily）
  78→        signal_valid_bars:        信号有效期（与 StrategyMatrixRunner 一致）
  79→    """
  80→
  81→    initial_capital: float = 100_000.0
  82→    top_k: int = 5
  83→    candidates_multiplier: int = 2
  84→    max_single_position_pct: float = 0.20
  85→    max_total_exposure_pct: float = 0.80
  86→    max_sector_exposure_pct: float = 0.40
  87→    rebalance_freq: str = "daily"
  88→    signal_valid_bars: int = 3
  89→
  90→
  91→@dataclass
  92→class PortfolioBacktestResult:
  93→    """组合回测结果。
  94→
  95→    Constitution L1 关键 KPI：Sortino > Sharpe > Max DD > Calmar > Annual Return。
  96→
  97→    Attributes:
  98→        start_date:               回测起始日期
  99→        end_date:                 回测结束日期
 100→        initial_capital:          初始资金
 101→        final_equity:             期末净值
 102→        total_return_pct:         总收益率（百分数）
 103→        annualized_return_pct:    年化收益率（百分数）
 104→        sharpe_ratio:             年化 Sharpe Ratio
 105→        sortino_ratio:             年化 Sortino Ratio（Constitution L1 首要 KPI）
 106→        max_drawdown_pct:         最大回撤（百分数，正值）
 107→        calmar_ratio:             Calmar = Annual Return / Max DD
 108→        daily_returns:            日收益率序列
 109→        equity_curve:             净值曲线（初始 = initial_capital）
 110→        holdings_history:         每日持仓快照列表（按交易日）
 111→        dd_violation:             DD 是否超过 20% 硬约束
 112→        group_exposure_history:   每日按 group_id 的暴露度快照
 113→        benchmark_symbol:          Benchmark 标的（默认 SPY，迭代 #7）
 114→        benchmark_total_return_pct:    Benchmark 同期总收益（百分数）
 115→        benchmark_annualized_return_pct: Benchmark 年化收益（百分数）
 116→        benchmark_sortino_ratio:       Benchmark Sortino Ratio
 117→        benchmark_max_drawdown_pct:    Benchmark 最大回撤（百分数，正值）
 118→        alpha_pct:                     超额收益 = 组合年化 - benchmark 年化（百分数）
 119→        information_ratio:             信息比率（年化）
 120→    """
 121→
 122→    start_date: date
 123→    end_date: date
 124→    initial_capital: float
 125→    final_equity: float
 126→    total_return_pct: float
 127→    annualized_return_pct: float
 128→    sharpe_ratio: float
 129→    sortino_ratio: float
 130→    max_drawdown_pct: float
 131→    calmar_ratio: float
 132→    daily_returns: pd.Series
 133→    equity_curve: pd.Series
 134→    holdings_history: list[dict[str, Any]] = field(default_factory=list)
 135→    dd_violation: bool = False
 136→    group_exposure_history: list[dict[str, Any]] = field(default_factory=list)
 137→    # Benchmark 对比（Iteration #7 新增）
 138→    benchmark_symbol: str = "SPY"
 139→    benchmark_total_return_pct: float = 0.0
 140→    benchmark_annualized_return_pct: float = 0.0
 141→    benchmark_sortino_ratio: float = 0.0
 142→    benchmark_max_drawdown_pct: float = 0.0
 143→    alpha_pct: float = 0.0
 144→    information_ratio: float = 0.0
 145→
 146→
 147→# ---------------------------------------------------------------------------
 148→# PortfolioBacktester
 149→# ---------------------------------------------------------------------------
 150→
 151→class PortfolioBacktester:
 152→    """组合层级回测器。
 153→
 154→    Args:
 155→        store:        MarketDataStore 实例
 156→        universe:     UniverseManager 实例
 157→        weights_file: strategy_weights.json 路径（来自离线 MatrixBacktest）
 158→        config:       PortfolioBacktestConfig
 159→
 160→    使用方式：
 161→        bt = PortfolioBacktester(store, universe, "config/strategy_weights.json", cfg)
 162→        result = bt.run(start=date(2024,1,1), end=date(2024,6,30))
 163→        print(result.sortino_ratio, result.max_drawdown_pct)
 164→    """
 165→
 166→    def __init__(
 167→        self,
 168→        store: MarketDataStore,
 169→        universe: UniverseManager,
 170→        weights_file: str | Path | None = None,
 171→        config: PortfolioBacktestConfig | None = None,
 172→    ) -> None:
 173→        self._store = store
 174→        self._universe = universe
 175→        self._weights_file = Path(weights_file) if weights_file else None
 176→        self._config = config or PortfolioBacktestConfig()
 177→
 178→        # 内部 StrategyMatrixRunner（复用其信号生成能力）
 179→        # signal_valid_bars 与 config 对齐
 180→        self._matrix_runner = StrategyMatrixRunner(
 181→            store=store,
 182→            universe=universe,
 183→            weights_file=self._weights_file,
 184→            signal_valid_bars=self._config.signal_valid_bars,
 185→        )
 186→
 187→        # 内部 SignalRanker（复用其聚合 + Top-2K 排名）
 188→        self._ranker = SignalRanker(
 189→            top_k=self._config.top_k,
 190→            candidates_multiplier=self._config.candidates_multiplier,
 191→        )
 192→
 193→        # 历史记录在 run() 开始时重置（实例属性，避免跨实例污染）
 194→        self._holdings_history: list[dict[str, Any]] = []
 195→        self._group_exposure_history: list[dict[str, Any]] = []
 196→
 197→    # ------------------------------------------------------------------
 198→    # 公共接口
 199→    # ------------------------------------------------------------------
 200→
 201→    def run(self, start: date, end: date) -> PortfolioBacktestResult:
 202→        """执行组合回测。
 203→
 204→        每日流程：
 205→            1. 用截至当日的数据生成信号（StrategyMatrixRunner.run_symbol）
 206→            2. SignalRanker 聚合 + Top-2K 排名
 207→            3. CandidateSelector 5 级约束选 Top-5
 208→            4. 按当日 close 计价，模拟换仓（卖出不在新 Top-5 的、买入新进的）
 209→            5. 用当日 close 重估持仓市值 → 更新净值
 210→
 211→        Args:
 212→            start: 回测起始日期（含）
 213→            end:   回测结束日期（含）
 214→
 215→        Returns:
 216→            PortfolioBacktestResult
 217→        """
 218→        cfg = self._config
 219→        symbols = self._universe.get_universe()
 220→
 221→        # 1. 拉取所有标的的完整日历数据（一次性，避免每日重复查询）
 222→        all_bars: dict[str, pd.DataFrame] = self._store.get_bars_multi(
 223→            symbols, start, end
 224→        )
 225→        if not all_bars:
 226→            logger.warning("[PortfolioBacktest] no data, returning empty result")
 227→            return self._empty_result(start, end)
 228→
 229→        # 2. 构造统一交易日历（所有标的的 date index 并集）
 230→        all_dates: list[date] = sorted({
 231→            ts.date() if isinstance(ts, (datetime, pd.Timestamp)) else ts
 232→            for df in all_bars.values()
 233→            for ts in df.index
 234→        })
 235→        # 限定到 [start, end] 区间
 236→        all_dates = [d for d in all_dates if start <= d <= end]
 237→        if not all_dates:
 238→            logger.warning("[PortfolioBacktest] no trading dates in range")
 239→            return self._empty_result(start, end)
 240→
 241→        logger.info(
 242→            f"[PortfolioBacktest] start={start}, end={end}, "
 243→            f"symbols={len(symbols)}, trading_days={len(all_dates)}"
 244→        )
 245→
 246→        # 3. 按日期循环
 247→        cash = cfg.initial_capital
 248→        # holdings: {symbol: (shares, avg_cost)} — 简化：用 close 计价
 249→        holdings: dict[str, float] = {}     # symbol → shares
 250→        avg_cost: dict[str, float] = {}    # symbol → 平均成本（用于成本基础）
 251→
 252→        daily_returns_list: list[float] = []
 253→        equity_list: list[float] = []
 254→        date_list: list[date] = []
 255→
 256→        prev_equity = cfg.initial_capital
 257→
 258→        for trading_date in all_dates:
 259→            # 截至当日的数据切片（防前视偏差）
 260→            bars_up_to_date: dict[str, pd.DataFrame] = {}
 261→            for sym, df in all_bars.items():
 262→                # df.index 可能是 datetime/timestamp
 263→                mask = df.index <= pd.Timestamp(trading_date)
 264→                sub = df.loc[mask]
 265→                if not sub.empty:
 266→                    bars_up_to_date[sym] = sub
 267→
 268→            # 当日 close 价查表（用于市值计价 + 换仓）
 269→            close_today: dict[str, float] = {}
 270→            for sym, df in bars_up_to_date.items():
 271→                if not df.empty:
 272→                    close_today[sym] = _safe_float(df["close"].iloc[-1])
 273→
 274→            # ── Step 1: 生成信号（复用 StrategyMatrixRunner 的 run_symbol 逻辑）──
 275→            # 用截至当日的数据子集生成信号；为避免修改 store 状态，
 276→            # 直接调用策略函数（不读 store，而是用 bars_up_to_date）
 277→            signals = self._generate_signals(bars_up_to_date, trading_date)
 278→
 279→            # ── Step 2: 排名 + Top-2K ──
 280→            rank_report = self._ranker.rank(signals)
 281→
 282→            # ── Step 3: 候选选股 ──
 283→            # 构造当前账户状态
 284→            current_exposure = sum(
 285→                shares * close_today.get(sym, 0.0)
 286→                for sym, shares in holdings.items()
 287→            )
 288→            sector_exposure: dict[str, float] = {}
 289→            for sym, shares in holdings.items():
 290→                meta = self._universe.get_symbol_meta(sym)
 291→                sector = meta.sector if meta else "Unknown"
 292→                mv = shares * close_today.get(sym, 0.0)
 293→                sector_exposure[sector] = sector_exposure.get(sector, 0.0) + mv
 294→
 295→            account = AccountState(
 296→                total_capital=cfg.initial_capital,
 297→                current_exposure=current_exposure,
 298→                current_position_count=len(holdings),
 299→                sector_exposure=sector_exposure,
 300→            )
 301→
 302→            approved, _ = select_orders_from_candidates(
 303→                candidates=rank_report.buy_candidates,
 304→                account=account,
 305→                max_orders=cfg.top_k,
 306→                max_single_position_pct=cfg.max_single_position_pct,
 307→                max_total_exposure_pct=cfg.max_total_exposure_pct,
 308→                max_sector_exposure_pct=cfg.max_sector_exposure_pct,
 309→                max_concurrent_positions=cfg.top_k,
 310→            )
 311→
 312→            # ── Step 4: 换仓 ──
 313→            # SELL 信号优先：先处理 sell_signals
 314→            for ranked in rank_report.sell_signals:
 315→                sym = ranked.signal.symbol
 316→                if sym in holdings:
 317→                    # 卖出全部持仓
 318→                    cash += holdings[sym] * close_today.get(sym, 0.0)
 319→                    del holdings[sym]
 320→                    avg_cost.pop(sym, None)
 321→
 322→            # 计算目标持仓集合（来自 approved 的 BUY）
 323→            target_symbols = {o.signal.symbol for o in approved}
 324→
 325→            # 卖出不在目标集合的现有持仓
 326→            for sym in list(holdings.keys()):
 327→                if sym not in target_symbols:
 328→                    cash += holdings[sym] * close_today.get(sym, 0.0)
 329→                    del holdings[sym]
 330→                    avg_cost.pop(sym, None)
 331→
 332→            # 买入新进的目标标的（等权分配可用资金）
 333→            new_buys = [o for o in approved if o.signal.symbol not in holdings]
 334→            if new_buys:
 335→                # 等权分配当前 cash 给新买入标的
 336→                per_symbol_budget = min(
 337→                    cfg.initial_capital * cfg.max_single_position_pct,
 338→                    cash / max(len(new_buys), 1),
 339→                )
 340→                for o in new_buys:
 341→                    sym = o.signal.symbol
 342→                    price = close_today.get(sym, 0.0)
 343→                    if price <= 0:
 344→                        continue
 345→                    shares_to_buy = per_symbol_budget / price
 346→                    if shares_to_buy <= 0:
 347→                        continue
 348→                    cost = shares_to_buy * price
 349→                    if cost > cash:
 350→                        continue
 351→                    cash -= cost
 352→                    # 更新平均成本
 353→                    old_shares = holdings.get(sym, 0.0)
 354→                    old_cost = avg_cost.get(sym, 0.0) * old_shares
 355→                    new_shares = old_shares + shares_to_buy
 356→                    avg_cost[sym] = (old_cost + cost) / new_shares if new_shares > 0 else 0.0
 357→                    holdings[sym] = new_shares
 358→
 359→            # ── Step 5: 计算当日净值 ──
 360→            market_value = sum(
 361→                shares * close_today.get(sym, 0.0)
 362→                for sym, shares in holdings.items()
 363→            )
 364→            equity = cash + market_value
 365→
 366→            # 日收益率
 367→            daily_ret = (equity - prev_equity) / prev_equity if prev_equity > 0 else 0.0
 368→            daily_returns_list.append(daily_ret)
 369→            equity_list.append(equity)
 370→            date_list.append(trading_date)
 371→            prev_equity = equity
 372→
 373→            # 记录 holdings_history
 374→            self._record_holdings(
 375→                trading_date, holdings, close_today, avg_cost, cash, equity
 376→            )
 377→            # 记录 group_exposure_history
 378→            self._record_group_exposure(trading_date, holdings, close_today, equity)
 379→
 380→        # 4. 计算最终指标
 381→        daily_returns = pd.Series(daily_returns_list, index=pd.to_datetime(date_list))
 382→        equity_curve = pd.Series(equity_list, index=pd.to_datetime(date_list))
 383→
 384→        final_equity = equity_list[-1] if equity_list else cfg.initial_capital
 385→        total_return_pct = (
 386→            (final_equity / cfg.initial_capital) - 1.0
 387→        ) * 100.0
 388→
 389→        # 年化收益率：按交易日数推算
 390→        n_days = len(daily_returns_list)
 391→        years = n_days / 252.0 if n_days > 0 else 0.0
 392→        if years > 0 and final_equity > 0:
 393→            annualized_return_pct = (
 394→                (final_equity / cfg.initial_capital) ** (1.0 / years) - 1.0
 395→            ) * 100.0
 396→        else:
 397→            annualized_return_pct = 0.0
 398→
 399→        sharpe = _compute_sharpe(daily_returns)
 400→        sortino = _compute_sortino(daily_returns)
 401→        max_dd = self._compute_max_drawdown_pct(daily_returns)
 402→
 403→        calmar = (
 404→            abs(annualized_return_pct / max_dd)
 405→            if max_dd > 0 else 0.0
 406→        )
 407→
 408→        dd_violation = max_dd > PORTFOLIO_MAX_DRAWDOWN_PCT
 409→
 410→        result = PortfolioBacktestResult(
 411→            start_date=start,
 412→            end_date=end,
 413→            initial_capital=cfg.initial_capital,
 414→            final_equity=final_equity,
 415→            total_return_pct=total_return_pct,
 416→            annualized_return_pct=annualized_return_pct,
 417→            sharpe_ratio=sharpe,
 418→            sortino_ratio=sortino,
 419→            max_drawdown_pct=max_dd,
 420→            calmar_ratio=calmar,
 421→            daily_returns=daily_returns,
 422→            equity_curve=equity_curve,
 423→            holdings_history=self._holdings_history,
 424→            dd_violation=dd_violation,
 425→            group_exposure_history=self._group_exposure_history,
 426→        )
 427→
 428→        # ── Benchmark: SPY buy-and-hold（迭代 #7）──
 429→        # 数据不可用时降级为 0.0，不抛异常（spec §4.2）
 430→        benchmark_result = self._compute_benchmark(
 431→            start, end, daily_returns_list, date_list
 432→        )
 433→        result.benchmark_symbol = benchmark_result.get("symbol", "SPY")
 434→        result.benchmark_total_return_pct = benchmark_result.get(
 435→            "total_return_pct", 0.0
 436→        )
 437→        result.benchmark_annualized_return_pct = benchmark_result.get(
 438→            "annualized_return_pct", 0.0
 439→        )
 440→        result.benchmark_sortino_ratio = benchmark_result.get(
 441→            "sortino_ratio", 0.0
 442→        )
 443→        result.benchmark_max_drawdown_pct = benchmark_result.get(
 444→            "max_drawdown_pct", 0.0
 445→        )
 446→        result.alpha_pct = (
 447→            result.annualized_return_pct - result.benchmark_annualized_return_pct
 448→        )
 449→        result.information_ratio = benchmark_result.get(
 450→            "information_ratio", 0.0
 451→        )
 452→
 453→        logger.info(
 454→            f"[PortfolioBacktest] done: final=${final_equity:,.0f}, "
 455→            f"total_return={total_return_pct:.2f}%, "
 456→            f"annualized={annualized_return_pct:.2f}%, "
 457→            f"sharpe={sharpe:.4f}, sortino={sortino:.4f}, "
 458→            f"max_dd={max_dd:.2f}%, dd_violation={dd_violation}, "
 459→            f"benchmark={result.benchmark_symbol} "
 460→            f"return={result.benchmark_annualized_return_pct:.2f}%, "
 461→            f"alpha={result.alpha_pct:.2f}%, ir={result.information_ratio:.4f}"
 462→        )
 463→
 464→        return result
 465→
 466→    # ------------------------------------------------------------------
 467→    # 内部方法
 468→    # ------------------------------------------------------------------
 469→
 470→    def _empty_result(self, start: date, end: date) -> PortfolioBacktestResult:
 471→        """空结果（无数据时返回）。"""
 472→        cfg = self._config
 473→        empty = pd.Series(dtype=float)
 474→        return PortfolioBacktestResult(
 475→            start_date=start,
 476→            end_date=end,
 477→            initial_capital=cfg.initial_capital,
 478→            final_equity=cfg.initial_capital,
 479→            total_return_pct=0.0,
 480→            annualized_return_pct=0.0,
 481→            sharpe_ratio=0.0,
 482→            sortino_ratio=0.0,
 483→            max_drawdown_pct=0.0,
 484→            calmar_ratio=0.0,
 485→            daily_returns=empty,
 486→            equity_curve=empty,
 487→        )
 488→
 489→    def _generate_signals(
 490→        self,
 491→        bars_up_to_date: dict[str, pd.DataFrame],
 492→        trading_date: date,
 493→    ) -> list[Signal]:
 494→        """复用 StrategyMatrixRunner 的策略调用逻辑生成信号。
 495→
 496→        为避免修改 store 状态（防前视偏差），这里直接基于 bars_up_to_date
 497→        调用注册表中的策略函数，绕过 runner.run_symbol 内部的 store.get_latest_n_bars。
 498→
 499→        信号有效期通过 config.signal_valid_bars 检查（与 runner 一致）。
 500→        """
 501→        from mytrader.strategy.registry import STRATEGY_REGISTRY
 502→
 503→        signals: list[Signal] = []
 504→        now = datetime.now(tz=timezone.utc)
 505→        svb = self._config.signal_valid_bars
 506→
 507→        for sym, df in bars_up_to_date.items():
 508→            if df.empty or len(df) < 30:
 509→                # 需要足够数据：bollinger period 最多 25 + signal_valid_bars 3 = 28
 510→                continue
 511→
 512→            meta = self._universe.get_symbol_meta(sym)
 513→            if meta is None:
 514→                continue
 515→
 516→            group_strategies = self._matrix_runner._weights.get(meta.group_id, [])
 517→            if not group_strategies:
 518→                continue
 519→
 520→            for entry in group_strategies:
 521→                strategy_name = entry["strategy"]
 522→                params = entry.get("params", {})
 523→                weight = float(entry.get("weight", 1.0))
 524→
 525→                strategy_fn = STRATEGY_REGISTRY.get(strategy_name)
 526→                if strategy_fn is None:
 527→                    continue
 528→
 529→                try:
 530→                    sig_series = strategy_fn(df["close"], df=df, **params)
 531→                except TypeError:
 532→                    sig_series = strategy_fn(df["close"], **params)
 533→                except (ValueError, KeyError, Exception):
 534→                    # ValueError: 指标数据不足（如 bbands 返回 None）
 535→                    # KeyError: 列名不匹配
 536→                    continue
 537→
 538→                # 信号有效期检查
 539→                recent = sig_series.iloc[-svb:]
 540→                nonzero = recent[recent != 0]
 541→                if nonzero.empty:
 542→                    continue
 543→
 544→                latest = int(nonzero.iloc[-1])
 545→                direction = SignalDirection.BUY if latest == 1 else SignalDirection.SELL
 546→                confidence = min(weight, 1.0)
 547→
 548→                signals.append(
 549→                    Signal(
 550→                        symbol=sym,
 551→                        direction=direction,
 552→                        timestamp=now,
 553→                        confidence=confidence,
 554→                        strategy_name=strategy_name,
 555→                        # 迭代 #5：复用 matrix_runner.build_matrix_signal_indicators
 556→                        # 保证线上扫描与组合回测 signal metadata 完全一致
 557→                        # （P0-A：曾因 sector=Unknown 导致 73 候选 → 2 approved）
 558→                        indicators=build_matrix_signal_indicators(meta, entry, weight),
 559→                    )
 560→                )
 561→
 562→        return signals
 563→
 564→    def _record_holdings(
 565→        self,
 566→        trading_date: date,
 567→        holdings: dict[str, float],
 568→        close_today: dict[str, float],
 569→        avg_cost: dict[str, float],
 570→        cash: float,
 571→        equity: float,
 572→    ) -> None:
 573→        """记录每日持仓快照（用于事后归因）。"""
 574→        holdings_snapshot = []
 575→        for sym, shares in holdings.items():
 576→            price = close_today.get(sym, 0.0)
 577→            holdings_snapshot.append({
 578→                "symbol": sym,
 579→                "shares": float(shares),
 580→                "price": float(price),
 581→                "market_value": float(shares * price),
 582→                "avg_cost": float(avg_cost.get(sym, 0.0)),
 583→                "unrealized_pnl": float((price - avg_cost.get(sym, 0.0)) * shares),
 584→            })
 585→
 586→        self._holdings_history.append({
 587→            "date": trading_date.isoformat(),
 588→            "cash": float(cash),
 589→            "equity": float(equity),
 590→            "positions": holdings_snapshot,
 591→            "position_count": len(holdings_snapshot),
 592→        })
 593→
 594→    def _record_group_exposure(
 595→        self,
 596→        trading_date: date,
 597→        holdings: dict[str, float],
 598→        close_today: dict[str, float],
 599→        equity: float,
 600→    ) -> None:
 601→        """记录每日按 group_id 的暴露度（用于风控观测）。"""
 602→        group_exposure: dict[str, float] = {}
 603→        for sym, shares in holdings.items():
 604→            meta = self._universe.get_symbol_meta(sym)
 605→            gid = meta.group_id if meta else "UNKNOWN"
 606→            mv = shares * close_today.get(sym, 0.0)
 607→            group_exposure[gid] = group_exposure.get(gid, 0.0) + mv
 608→
 609→        # 转为百分比
 610→        group_exposure_pct = {
 611→            gid: (mv / equity * 100.0 if equity > 0 else 0.0)
 612→            for gid, mv in group_exposure.items()
 613→        }
 614→
 615→        self._group_exposure_history.append({
 616→            "date": trading_date.isoformat(),
 617→            "total_equity": float(equity),
 618→            "group_exposure_value": {k: float(v) for k, v in group_exposure.items()},
 619→            "group_exposure_pct": group_exposure_pct,
 620→        })
 621→
 622→    def _compute_benchmark(
 623→        self,
 624→        start: date,
 625→        end: date,
 626→        portfolio_daily_returns: list[float],
 627→        dates: list[date],
 628→    ) -> dict[str, Any]:
 629→        """计算 SPY buy-and-hold benchmark 指标（迭代 #7）。
 630→
 631→        从 MarketDataStore 拉取 SPY 同期数据，计算：
 632→            - total_return_pct / annualized_return_pct
 633→            - sortino_ratio / max_drawdown_pct（与组合层同口径）
 634→            - information_ratio（基于 portfolio - spy 的超额收益序列）
 635→
 636→        降级处理：SPY 数据不可用时所有字段保持 0.0，不抛异常（spec §4.2）。
 637→
 638→        Args:
 639→            start:                   回测起始日期
 640→            end:                     回测结束日期
 641→            portfolio_daily_returns: 组合日收益率序列（与 dates 对齐）
 642→            dates:                   交易日日期序列
 643→
 644→        Returns:
 645→            dict with benchmark metrics。失败时仅含 "symbol"。
 646→        """
 647→        benchmark_symbol = "SPY"
 648→        try:
 649→            spy_bars = self._store.get_bars_multi([benchmark_symbol], start, end)
 650→            spy_df = spy_bars.get(benchmark_symbol)
 651→            if spy_df is None or spy_df.empty:
 652→                logger.warning(
 653→                    "[PortfolioBacktest] SPY data unavailable, benchmark skipped"
 654→                )
 655→                return {"symbol": benchmark_symbol}
 656→
 657→            spy_close = spy_df["close"].astype(float)
 658→            if len(spy_close) < 2:
 659→                logger.warning(
 660→                    "[PortfolioBacktest] SPY data too short, benchmark skipped"
 661→                )
 662→                return {"symbol": benchmark_symbol}
 663→
 664→            spy_returns = spy_close.pct_change().dropna()
 665→
 666→            # SPY total / annualized return
 667→            spy_final = float(spy_close.iloc[-1])
 668→            spy_initial = float(spy_close.iloc[0])
 669→            spy_total_return_pct = (
 670→                (spy_final / spy_initial) - 1.0
 671→            ) * 100.0 if spy_initial > 0 else 0.0
 672→
 673→            n_spy = len(spy_returns)
 674→            years_spy = n_spy / 252.0 if n_spy > 0 else 0.0
 675→            if years_spy > 0 and spy_final > 0 and spy_initial > 0:
 676→                spy_annualized_pct = (
 677→                    (spy_final / spy_initial) ** (1.0 / years_spy) - 1.0
 678→                ) * 100.0
 679→            else:
 680→                spy_annualized_pct = 0.0
 681→
 682→            # Sortino / Max DD（复用 matrix_backtest helper，与组合层同口径）
 683→            spy_sortino = _compute_sortino(spy_returns)
 684→            spy_max_dd = self._compute_max_drawdown_pct(spy_returns)
 685→
 686→            # Information Ratio：基于超额收益序列
 687→            # 将 SPY returns 对齐到 portfolio 的交易日历
 688→            ir = self._compute_information_ratio(
 689→                portfolio_daily_returns, dates, spy_returns
 690→            )
 691→
 692→            return {
 693→                "symbol": benchmark_symbol,
 694→                "total_return_pct": float(spy_total_return_pct),
 695→                "annualized_return_pct": float(spy_annualized_pct),
 696→                "sortino_ratio": float(spy_sortino),
 697→                "max_drawdown_pct": float(spy_max_dd),
 698→                "information_ratio": float(ir),
 699→            }
 700→        except Exception as e:
 701→            logger.warning(
 702→                f"[PortfolioBacktest] benchmark computation failed: {e}"
 703→            )
 704→            return {"symbol": benchmark_symbol}
 705→
 706→    @staticmethod
 707→    def _compute_information_ratio(
 708→        portfolio_daily_returns: list[float],
 709→        portfolio_dates: list[date],
 710→        spy_returns: pd.Series,
 711→    ) -> float:
 712→        """计算年化信息比率。
 713→
 714→        IR = mean(excess_returns) / std(excess_returns) * sqrt(252)
 715→        excess_returns = portfolio_returns - spy_returns（按日期对齐）
 716→        """
 717→        if not portfolio_daily_returns or len(spy_returns) == 0:
 718→            return 0.0
 719→
 720→        # 组合 returns 转为 pd.Series，index 用 portfolio_dates
 721→        port_idx = pd.to_datetime(portfolio_dates)
 722→        port_series = pd.Series(
 723→            portfolio_daily_returns, index=port_idx, dtype=float
 724→        )
 725→
 726→        # 对齐：取两序列 index 的交集（inner join）
 727→        aligned = pd.concat(
 728→            [port_series.rename("port"), spy_returns.rename("spy")],
 729→            axis=1,
 730→            join="inner",
 731→        ).dropna()
 732→        if aligned.empty or len(aligned) < 5:
 733→            return 0.0
 734→
 735→        excess = aligned["port"] - aligned["spy"]
 736→        std = excess.std()
 737→        if std <= 0 or not np.isfinite(std):
 738→            return 0.0
 739→        return float(excess.mean() / std * np.sqrt(252))
 740→
 741→    @staticmethod
 742→    def _compute_max_drawdown_pct(daily_returns: pd.Series) -> float:
 743→        """计算最大回撤（百分数正值）。
 744→
 745→        与 matrix_backtest._portfolio_max_drawdown_from_results 同口径。
 746→        """
 747→        if daily_returns.empty:
 748→            return 0.0
 749→        cumvalue = (1.0 + daily_returns).cumprod()
 750→        peak = cumvalue.cummax()
 751→        drawdown = (cumvalue - peak) / peak
 752→        dd_min = float(drawdown.min())
 753→        if not np.isfinite(dd_min):
 754→            return 0.0
 755→        return abs(dd_min) * 100.0
 756→
---
Now
---
 I
---
 have a great
---
 understanding of the existing
---
 code. Let me also
---
 look
---
 at the existing tests
---
 for matrix_backtest to
---
 understand the test
---
 patterns:
---
现在
---
让我查找
---
 `
---
matrix_backtest` 的
---
现有测试：
---
{"pattern": "**/test_matrix_backtest*.py"}
---
["/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py"]
---
["/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py"]
---
{"file_path": "/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py"}
---
   1→"""MatrixBacktest 测试。
   2→
   3→使用 Mock MarketDataStore + 内置策略，不触碰网络。
   4→"""
   5→
   6→from __future__ import annotations
   7→
   8→import json
   9→from datetime import date
  10→from pathlib import Path
  11→from unittest.mock import MagicMock, patch
  12→
  13→import numpy as np
  14→import pandas as pd
  15→import pytest
  16→
  17→from mytrader.backtest.matrix_backtest import (
  18→    MatrixBacktest,
  19→    _backtest_one,
  20→    _compute_sharpe,
  21→    _compute_sortino,
  22→    _portfolio_max_drawdown_from_results,
  23→    _portfolio_sharpe_from_results,
  24→    _portfolio_sortino_from_results,
  25→    _safe_float,
  26→    _safe_mean,
  27→    MAX_PORTFOLIO_DRAWDOWN_PCT,
  28→    WALK_FORWARD_VAL_DD_THRESHOLD,
  29→    SingleBacktestResult,
  30→    WalkForwardReport,
  31→    WalkForwardRound,
  32→    _add_months,
  33→    run_walk_forward,
  34→)
  35→
  36→
  37→# ---------------------------------------------------------------------------
  38→# Fixtures
  39→# ---------------------------------------------------------------------------
  40→
  41→def _make_ohlcv(n: int = 300, trend: str = "up") -> pd.DataFrame:
  42→    """生成测试 OHLCV 数据（足够计算慢均线）。"""
  43→    idx = pd.date_range("2021-01-01", periods=n, freq="B")
  44→    if trend == "up":
  45→        close = [100.0 + i * 0.1 for i in range(n)]
  46→    else:
  47→        close = [100.0 - i * 0.05 for i in range(n)]
  48→    return pd.DataFrame(
  49→        {
  50→            "open":   [c - 0.5 for c in close],
  51→            "high":   [c + 1.0 for c in close],
  52→            "low":    [c - 1.0 for c in close],
  53→            "close":  close,
  54→            "volume": [1_000_000] * n,
  55→        },
  56→        index=idx,
  57→    )
  58→
  59→
  60→@pytest.fixture
  61→def mock_store(tmp_path):
  62→    store = MagicMock()
  63→    df_aapl = _make_ohlcv(300, trend="up")
  64→    df_msft = _make_ohlcv(300, trend="up")
  65→    df_jpm  = _make_ohlcv(300, trend="up")
  66→
  67→    def get_bars_multi(symbols, start, end, timeframe="1d"):
  68→        mapping = {"AAPL": df_aapl, "MSFT": df_msft, "JPM": df_jpm}
  69→        return {s: mapping[s] for s in symbols if s in mapping}
  70→
  71→    store.get_bars_multi.side_effect = get_bars_multi
  72→    return store
  73→
  74→
  75→@pytest.fixture
  76→def mock_universe():
  77→    from mytrader.universe.models import SymbolMeta
  78→    universe = MagicMock()
  79→    universe.get_groups.return_value = {
  80→        "NDX_mid_vol": ["AAPL", "MSFT"],
  81→        "SPX_mid_vol": ["JPM"],
  82→    }
  83→
  84→    def get_meta(sym):
  85→        ndx = ["AAPL", "MSFT"]
  86→        return SymbolMeta(
  87→            symbol=sym,
  88→            index_membership=["NASDAQ100"] if sym in ndx else ["SP500"],
  89→            sector="Technology" if sym in ndx else "Financials",
  90→            market_cap_tier="large",
  91→            volatility_tier="mid",
  92→            group_id="NDX_mid_vol" if sym in ndx else "SPX_mid_vol",
  93→        )
  94→    universe.get_symbol_meta.side_effect = get_meta
  95→    return universe
  96→
  97→
  98→# ---------------------------------------------------------------------------
  99→# 单函数测试
 100→# ---------------------------------------------------------------------------
 101→
 102→class TestHelpers:
 103→
 104→    def test_compute_sharpe_positive(self):
 105→        """正向收益的 Sharpe > 0。"""
 106→        returns = pd.Series([0.001] * 252)
 107→        sharpe = _compute_sharpe(returns)
 108→        assert sharpe > 0
 109→
 110→    def test_compute_sharpe_zero_std(self):
 111→        """收益恒定（零方差）返回 0。"""
 112→        returns = pd.Series([0.0] * 100)
 113→        assert _compute_sharpe(returns) == 0.0
 114→
 115→    def test_compute_sharpe_empty(self):
 116→        assert _compute_sharpe(pd.Series([], dtype=float)) == 0.0
 117→
 118→    def test_portfolio_sharpe_from_results(self):
 119→        """等权组合 Sharpe 不等于算术平均 Sharpe（差异 > 1e-6）。"""
 120→        n = 252
 121→        r1 = pd.Series(np.random.normal(0.001, 0.01, n))   # 高收益高波动
 122→        r2 = pd.Series(np.random.normal(0.0005, 0.002, n)) # 低收益低波动
 123→
 124→        s1 = _compute_sharpe(r1)
 125→        s2 = _compute_sharpe(r2)
 126→        arithmetic_avg = (s1 + s2) / 2
 127→
 128→        results = [
 129→            SingleBacktestResult("SYM1", "s1", {}, s1, 10, 5, 60, 20, r1),
 130→            SingleBacktestResult("SYM2", "s2", {}, s2, 5, 3, 55, 15, r2),
 131→        ]
 132→        portfolio_sharpe = _portfolio_sharpe_from_results(results)
 133→
 134→        # 组合 Sharpe 与算术平均 Sharpe 应不同（这正是为什么要用组合方式）
 135→        diff = abs(portfolio_sharpe - arithmetic_avg)
 136→        assert diff > 1e-6, (
 137→            f"组合 Sharpe({portfolio_sharpe:.4f}) 与算术平均 Sharpe({arithmetic_avg:.4f}) "
 138→            f"差异应 >1e-6，否则说明实现有误"
 139→        )
 140→
 141→    # ── Sortino（迭代 #1 新增，Constitution L1 首要 KPI）─────────────────────
 142→
 143→    def test_compute_sortino_positive(self):
 144→        """正均值的收益序列 Sortino > 0。"""
 145→        returns = pd.Series([0.001, -0.0005, 0.002, -0.0003, 0.0015] * 60)
 146→        assert _compute_sortino(returns) > 0
 147→
 148→    def test_compute_sortino_empty(self):
 149→        """空序列返回 0。"""
 150→        assert _compute_sortino(pd.Series([], dtype=float)) == 0.0
 151→
 152→    def test_compute_sortino_no_downside_returns_zero(self):
 153→        """全正收益（无下行波动）→ 0.0（退化处理，与 _compute_sharpe 一致）。
 154→
 155→        理论上 Sortino 应为 +inf，但返回 0 保持可算术聚合 + 保守评估。
 156→        """
 157→        returns = pd.Series([0.001] * 100)   # 全正，无下行
 158→        assert _compute_sortino(returns) == 0.0
 159→
 160→    def test_compute_sortino_differs_from_sharpe_when_asymmetric(self):
 161→        """当上行/下行波动不对称时，Sortino ≠ Sharpe（这是引入 Sortino 的意义）。"""
 162→        # 大幅上行小波动 + 偶尔小幅下行：Sortino 应明显高于 Sharpe
 163→        np.random.seed(42)
 164→        upside = np.random.normal(0.003, 0.005, 200)   # 正均值的上行
 165→        downside_shocks = np.array([-0.01, -0.012, -0.008] * 3)  # 少量下行冲击
 166→        returns = pd.Series(np.concatenate([upside, downside_shocks]))
 167→
 168→        sharpe = _compute_sharpe(returns)
 169→        sortino = _compute_sortino(returns)
 170→        # Sortino 仅对下行惩罚 → 上行波动不计入分母 → Sortino > Sharpe
 171→        assert sortino > sharpe, (
 172→            f"非对称收益下 Sortino({sortino:.4f}) 应 > Sharpe({sharpe:.4f})，"
 173→            f"否则说明 Sortino 公式退化为 Sharpe"
 174→        )
 175→
 176→    def test_compute_sortino_known_value(self):
 177→        """已知值验算 Sortino 公式正确性。"""
 178→        # r = [0.01, 0.01, 0.01, -0.01]
 179→        # mean = 0.005; downside = [0,0,0,-0.01]; dd = sqrt(mean([0,0,0,0.0001])) = sqrt(0.000025) = 0.005
 180→        # Sortino = 0.005 / 0.005 * sqrt(252) = 15.8745...
 181→        returns = pd.Series([0.01, 0.01, 0.01, -0.01] * 25)   # 重复 25 次以满足 len>=5
 182→        expected = (0.005 / 0.005) * np.sqrt(252)
 183→        assert abs(_compute_sortino(returns) - expected) < 1e-6
 184→
 185→    def test_portfolio_sortino_from_results(self):
 186→        """等权组合 Sortino 不等于各标的 Sortino 算术平均（与 Sharpe 同理）。"""
 187→        n = 252
 188→        np.random.seed(0)
 189→        r1 = pd.Series(np.random.normal(0.001, 0.01, n))
 190→        r2 = pd.Series(np.random.normal(0.0005, 0.002, n))
 191→
 192→        s1 = _compute_sortino(r1)
 193→        s2 = _compute_sortino(r2)
 194→        arithmetic_avg = (s1 + s2) / 2
 195→
 196→        results = [
 197→            SingleBacktestResult("SYM1", "s1", {}, 0.0, 0, 0, 0, 0, r1),
 198→            SingleBacktestResult("SYM2", "s2", {}, 0.0, 0, 0, 0, 0, r2),
 199→        ]
 200→        portfolio_sortino = _portfolio_sortino_from_results(results)
 201→
 202→        diff = abs(portfolio_sortino - arithmetic_avg)
 203→        assert diff > 1e-6, (
 204→            f"组合 Sortino({portfolio_sortino:.4f}) 与算术平均({arithmetic_avg:.4f}) "
 205→            f"差异应 >1e-6，否则说明实现退化为算术平均"
 206→        )
 207→
 208→    # ── _safe_float / _safe_mean（迭代 #2 新增）─────────────────────────────
 209→
 210→    def test_safe_float_handles_nan(self):
 211→        """NaN 是 truthy，`NaN or 0.0` 仍为 NaN；_safe_float 必须返回 default。"""
 212→        nan = float("nan")
 213→        assert _safe_float(nan) == 0.0
 214→        assert _safe_float(nan, default=-1.0) == -1.0
 215→
 216→    def test_safe_float_handles_none(self):
 217→        assert _safe_float(None) == 0.0
 218→        assert _safe_float(None, default=3.14) == 3.14
 219→
 220→    def test_safe_float_handles_inf(self):
 221→        assert _safe_float(float("inf")) == 0.0
 222→        assert _safe_float(float("-inf")) == 0.0
 223→
 224→    def test_safe_float_passes_normal_numbers(self):
 225→        assert _safe_float(1.5) == 1.5
 226→        assert _safe_float(0) == 0.0
 227→        assert _safe_float(-2.7) == -2.7
 228→        assert _safe_float("3.14") == 3.14   # 字符串数字可转
 229→
 230→    def test_safe_float_handles_non_numeric(self):
 231→        assert _safe_float("abc") == 0.0
 232→        assert _safe_float([1, 2, 3]) == 0.0
 233→        assert _safe_float(object()) == 0.0
 234→
 235→    def test_safe_mean_empty_list(self):
 236→        """空列表返回 default（np.mean([]) 会触发 RuntimeWarning 并返回 NaN）。"""
 237→        assert _safe_mean([]) == 0.0
 238→        assert _safe_mean([], default=2.0) == 2.0
 239→
 240→    def test_safe_mean_all_nan(self):
 241→        """全 NaN 列表返回 default。"""
 242→        assert _safe_mean([float("nan"), float("nan")]) == 0.0
 243→
 244→    def test_safe_mean_partial_nan(self):
 245→        """部分 NaN 自动忽略（nanmean 语义）。"""
 246→        result = _safe_mean([1.0, float("nan"), 3.0])
 247→        assert abs(result - 2.0) < 1e-9
 248→
 249→    def test_safe_mean_normal(self):
 250→        assert abs(_safe_mean([1.0, 2.0, 3.0]) - 2.0) < 1e-9
 251→
 252→    # ── _portfolio_max_drawdown_from_results（迭代 #2 新增）────────────────
 253→
 254→    def test_portfolio_max_drawdown_no_returns(self):
 255→        """无有效日收益率 → 0.0。"""
 256→        results: list[SingleBacktestResult] = []
 257→        assert _portfolio_max_drawdown_from_results(results) == 0.0
 258→
 259→    def test_portfolio_max_drawdown_all_positive(self):
 260→        """全正收益 → 无回撤，返回 0.0。"""
 261→        r = pd.Series([0.001] * 100)
 262→        results = [SingleBacktestResult("S1", "s", {}, 0.0, 0, 0, 0, 0, r)]
 263→        assert _portfolio_max_drawdown_from_results(results) == 0.0
 264→
 265→    def test_portfolio_max_drawdown_known_value(self):
 266→        """已知值验算：先涨后跌回测组合 DD。
 267→
 268→        组合等权日收益率 = r。cumvalue 从 1.0 涨到 1.05，再跌到 0.95。
 269→        peak = 1.05, trough = 0.95, DD = (0.95 - 1.05) / 1.05 ≈ -9.524%。
 270→        """
 271→        # 10 天 +1% → cumvalue 涨到 1.01^10 ≈ 1.1046
 272→        # 10 天 -1% → cumvalue 跌到 1.1046 * 0.99^10 ≈ 0.9994
 273→        # peak=1.1046, trough=0.9994, DD = (0.9994 - 1.1046) / 1.1046 ≈ -9.52%
 274→        returns = pd.Series([0.01] * 10 + [-0.01] * 10)
 275→        results = [SingleBacktestResult("S1", "s", {}, 0.0, 0, 0, 0, 0, returns)]
 276→        dd = _portfolio_max_drawdown_from_results(results)
 277→        assert dd > 0.0, "存在回撤时应返回正值"
 278→        assert 8.0 < dd < 11.0, f"DD 应在 9.5% 附近，实际 {dd:.4f}%"
 279→
 280→    def test_portfolio_max_drawdown_returns_positive_pct(self):
 281→        """返回值为正百分数（与 backtest_max_drawdown 输出口径一致）。"""
 282→        np.random.seed(42)
 283→        # 模拟一个带回撤的序列
 284→        r = pd.Series(np.concatenate([
 285→            np.random.normal(0.002, 0.005, 50),
 286→            np.random.normal(-0.003, 0.008, 30),
 287→            np.random.normal(0.001, 0.004, 50),
 288→        ]))
 289→        results = [SingleBacktestResult("S1", "s", {}, 0.0, 0, 0, 0, 0, r)]
 290→        dd = _portfolio_max_drawdown_from_results(results)
 291→        assert dd >= 0.0
 292→        assert isinstance(dd, float)
 293→
 294→    def test_backtest_one_with_open(self):
 295→        """传入 open= 参数，回测正常运行。"""
 296→        df = _make_ohlcv(300)
 297→        result = _backtest_one(df, "dual_ma", {"fast": 5, "slow": 20})
 298→        assert result is not None
 299→        assert not result.daily_returns.empty
 300→        assert isinstance(result.sharpe, float)
 301→
 302→    def test_backtest_one_without_open(self):
 303→        """DataFrame 中无 open 列时也能正常回测（降级为 close 执行）。"""
 304→        df = _make_ohlcv(300).drop(columns=["open"])
 305→        result = _backtest_one(df, "dual_ma", {"fast": 5, "slow": 20})
 306→        assert result is not None
 307→
 308→    def test_backtest_one_empty_df(self):
 309→        """空 DataFrame 返回 None。"""
 310→        assert _backtest_one(pd.DataFrame(), "dual_ma", {}) is None
 311→
 312→    def test_backtest_one_short_df(self):
 313→        """不足 30 根 bar 返回 None。"""
 314→        df = _make_ohlcv(10)
 315→        assert _backtest_one(df, "dual_ma", {"fast": 5, "slow": 20}) is None
 316→
 317→    def test_backtest_one_unknown_strategy(self):
 318→        """未注册策略返回 None。"""
 319→        df = _make_ohlcv(300)
 320→        assert _backtest_one(df, "nonexistent_xyz", {}) is None
 321→
 322→    def test_open_parameter_is_passed_to_vectorbt(self):
 323→        """验证有 open 列时 _backtest_one 使用 open= 参数（而非仅用 close）。
 324→
 325→        用 mock 拦截 vbt.Portfolio.from_signals，检查 open 参数是否被传入。
 326→        """
 327→        import unittest.mock as mock
 328→        df = _make_ohlcv(100)
 329→
 330→        with mock.patch("mytrader.backtest.matrix_backtest.vbt.Portfolio.from_signals") as m:
 331→            # 让 mock 返回一个假 Portfolio
 332→            fake_pf = mock.MagicMock()
 333→            fake_pf.stats.return_value = {
 334→                "Sharpe Ratio": 1.0, "Total Return [%]": 5.0,
 335→                "Max Drawdown [%]": 3.0, "Win Rate [%]": 55.0, "Total Trades": 10,
 336→            }
 337→            fake_pf.returns.return_value = pd.Series([0.001] * len(df), index=df.index)
 338→            m.return_value = fake_pf
 339→
 340→            _backtest_one(df, "dual_ma", {"fast": 5, "slow": 20})
 341→
 342→        # 验证 from_signals 被调用了，且 open 参数被传入
 343→        assert m.called
 344→        call_kwargs = m.call_args[1] if m.call_args[1] else {}
 345→        # open 参数应该在 kwargs 中
 346→        assert "open" in call_kwargs, "有 open 列时，open 参数应被传给 from_signals"
 347→
 348→
 349→# ---------------------------------------------------------------------------
 350→# MatrixBacktest 集成测试
 351→# ---------------------------------------------------------------------------
 352→
 353→class TestMatrixBacktest:
 354→
 355→    def test_run_produces_groups(self, mock_store, mock_universe):
 356→        """run() 产出包含分组权重的 MatrixBacktestReport。"""
 357→        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=2)
 358→        strategies = ["dual_ma"]
 359→        param_grids = {"dual_ma": {"fast": [5], "slow": [20]}}
 360→
 361→        report = mb.run(strategies=strategies, param_grids=param_grids)
 362→        assert len(report.groups) >= 1
 363→        # 每个分组应有策略权重配置
 364→        for gid, weights in report.groups.items():
 365→            assert isinstance(weights, list)
 366→
 367→    def test_run_weights_sum_to_one(self, mock_store, mock_universe):
 368→        """每个分组的策略权重之和 ≈ 1.0。"""
 369→        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=2)
 370→        report = mb.run(
 371→            strategies=["dual_ma", "rsi_mean_revert"],
 372→            param_grids={
 373→                "dual_ma": {"fast": [5], "slow": [20]},
 374→                "rsi_mean_revert": {"period": [14], "oversold": [30], "overbought": [70]},
 375→            },
 376→        )
 377→        for gid, weights in report.groups.items():
 378→            if weights:
 379→                total = sum(w["weight"] for w in weights)
 380→                assert abs(total - 1.0) < 0.01, f"{gid}: weights sum={total:.4f} ≠ 1.0"
 381→
 382→    def test_run_output_file(self, mock_store, mock_universe, tmp_path):
 383→        """output_file 参数会生成有效的 JSON 文件。"""
 384→        output = tmp_path / "strategy_weights.json"
 385→        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)
 386→        mb.run(
 387→            strategies=["dual_ma"],
 388→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 389→            output_file=output,
 390→        )
 391→        assert output.exists()
 392→        data = json.loads(output.read_text())
 393→        assert "_meta" in data
 394→        assert "groups" in data
 395→        assert "survivorship_bias_warning" in data["_meta"]
 396→
 397→    def test_run_empty_universe(self, mock_store):
 398→        """空标的组不崩溃。"""
 399→        universe = MagicMock()
 400→        universe.get_groups.return_value = {}
 401→        mb = MatrixBacktest(store=mock_store, universe=universe, years=1)
 402→        report = mb.run(strategies=["dual_ma"], param_grids={"dual_ma": {}})
 403→        assert report.groups == {}
 404→
 405→    def test_run_no_data_for_group(self, mock_universe, tmp_path):
 406→        """组内无数据时优雅跳过。"""
 407→        store = MagicMock()
 408→        store.get_bars_multi.return_value = {}
 409→        mb = MatrixBacktest(store=store, universe=mock_universe, years=1)
 410→        report = mb.run(
 411→            strategies=["dual_ma"],
 412→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 413→        )
 414→        # 无数据 → 分组权重为空列表
 415→        for gid, weights in report.groups.items():
 416→            assert weights == []
 417→
 418→    def test_group_results_have_portfolio_sharpe(self, mock_store, mock_universe):
 419→        """GroupBacktestResult 中 portfolio_sharpe 是用组合 Sharpe 计算的浮点数。"""
 420→        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)
 421→        report = mb.run(
 422→            strategies=["dual_ma"],
 423→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 424→        )
 425→        for gr in report.group_results:
 426→            assert isinstance(gr.portfolio_sharpe, float)
 427→            assert gr.symbol_count > 0
 428→
 429→    def test_survivorship_bias_warning_in_output(self, mock_store, mock_universe, tmp_path):
 430→        """输出文件中包含幸存者偏差警告。"""
 431→        output = tmp_path / "weights.json"
 432→        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1)
 433→        mb.run(
 434→            strategies=["dual_ma"],
 435→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 436→            output_file=output,
 437→        )
 438→        data = json.loads(output.read_text())
 439→        warning = data["_meta"].get("survivorship_bias_warning", "")
 440→        assert "成分" in warning or "survivorship" in warning.lower()
 441→
 442→    # ── 迭代 #1 新增：观测性 + 回归 + Sortino 输出 ──────────────────────────
 443→
 444→    def test_unknown_strategy_logs_warning(self, mock_store, mock_universe):
 445→        """未注册策略名在 _run_group 中输出 WARNING 日志（而非静默跳过）。
 446→
 447→        这是迭代 #1 修复的核心观测性问题：之前 _backtest_one 内部静默 return None，
 448→        导致 main.py 误用 "rsi"/"macd"/"bollinger" 简称 6 天未被发现。
 449→
 450→        注意：项目用 loguru 而非 stdlib logging，故用 loguru sink 捕获（caplog 无效）。
 451→        """
 452→        from loguru import logger
 453→
 454→        msgs: list[str] = []
 455→        # 临时 sink 捕获所有 WARNING+ 日志到列表
 456→        handler_id = logger.add(lambda m: msgs.append(str(m)), level="WARNING")
 457→        try:
 458→            mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=2)
 459→            mb.run(
 460→                strategies=["dual_ma", "totally_bogus_name"],
 461→                param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 462→            )
 463→        finally:
 464→            logger.remove(handler_id)
 465→
 466→        # 应有 WARNING 提及 bogus 策略名
 467→        assert any("totally_bogus_name" in m for m in msgs), (
 468→            f"未注册策略应触发 WARNING，实际捕获: {msgs}"
 469→        )
 470→
 471→    def test_reoptimize_strategy_names_match_registry(self):
 472→        """回归测试：main.REOPTIMIZE_STRATEGIES 中每个策略名必须在注册表中。
 473→
 474→        防止迭代 #1 的 bug 重现：策略名拼写与 @register_strategy 装饰器不匹配，
 475→        导致矩阵回测静默跳过整类策略、strategy_weights.json 退化为仅 dual_ma。
 476→        """
 477→        from main import REOPTIMIZE_STRATEGIES, REOPTIMIZE_PARAM_GRIDS
 478→        from mytrader.strategy.registry import STRATEGY_REGISTRY
 479→
 480→        assert len(REOPTIMIZE_STRATEGIES) >= 4, (
 481→            f"预期至少 4 个策略，实际 {len(REOPTIMIZE_STRATEGIES)}：{REOPTIMIZE_STRATEGIES}"
 482→        )
 483→        for name in REOPTIMIZE_STRATEGIES:
 484→            assert name in STRATEGY_REGISTRY, (
 485→                f"REOPTIMIZE_STRATEGIES 中的 '{name}' 未在 STRATEGY_REGISTRY 注册。"
 486→                f"已注册: {sorted(STRATEGY_REGISTRY.keys())}"
 487→            )
 488→            assert name in REOPTIMIZE_PARAM_GRIDS, (
 489→                f"REOPTIMIZE_PARAM_GRIDS 缺少 '{name}' 的参数网格"
 490→            )
 491→
 492→    def test_output_file_contains_sortino(self, mock_store, mock_universe, tmp_path):
 493→        """strategy_weights.json 每个权重条目含 backtest_sortino 字段（Constitution L1 首要 KPI）。"""
 494→        output = tmp_path / "weights_with_sortino.json"
 495→        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)
 496→        mb.run(
 497→            strategies=["dual_ma"],
 498→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 499→            output_file=output,
 500→        )
 501→        data = json.loads(output.read_text())
 502→        for gid, weights in data["groups"].items():
 503→            for w in weights:
 504→                assert "backtest_sortino" in w, (
 505→                    f"{gid}: 权重条目缺少 backtest_sortino 字段，实际 keys={list(w.keys())}"
 506→                )
 507→                assert isinstance(w["backtest_sortino"], (int, float)), (
 508→                    f"{gid}: backtest_sortino 应为数值，实际 {type(w['backtest_sortino'])}"
 509→                )
 510→
 511→    def test_group_results_have_portfolio_sortino(self, mock_store, mock_universe):
 512→        """GroupBacktestResult.portfolio_sortino 是浮点数（迭代 #1 新增字段）。"""
 513→        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)
 514→        report = mb.run(
 515→            strategies=["dual_ma"],
 516→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 517→        )
 518→        for gr in report.group_results:
 519→            assert isinstance(gr.portfolio_sortino, float), (
 520→                f"portfolio_sortino 应为 float，实际 {type(gr.portfolio_sortino)}"
 521→            )
 522→
 523→    # ── 迭代 #2 新增：portfolio_max_drawdown 字段 + backtest_max_drawdown 输出 ──
 524→
 525→    def test_group_results_have_portfolio_max_drawdown(self, mock_store, mock_universe):
 526→        """GroupBacktestResult.portfolio_max_drawdown 是非负浮点数。"""
 527→        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)
 528→        report = mb.run(
 529→            strategies=["dual_ma"],
 530→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 531→        )
 532→        for gr in report.group_results:
 533→            assert isinstance(gr.portfolio_max_drawdown, float), (
 534→                f"portfolio_max_drawdown 应为 float，实际 {type(gr.portfolio_max_drawdown)}"
 535→            )
 536→            assert gr.portfolio_max_drawdown >= 0.0, (
 537→                f"portfolio_max_drawdown 应非负，实际 {gr.portfolio_max_drawdown}"
 538→            )
 539→
 540→    def test_output_file_contains_max_drawdown(self, mock_store, mock_universe, tmp_path):
 541→        """strategy_weights.json 每个权重条目含 backtest_max_drawdown 字段。"""
 542→        output = tmp_path / "weights_with_dd.json"
 543→        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)
 544→        mb.run(
 545→            strategies=["dual_ma"],
 546→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 547→            output_file=output,
 548→        )
 549→        data = json.loads(output.read_text())
 550→        for gid, weights in data["groups"].items():
 551→            for w in weights:
 552→                assert "backtest_max_drawdown" in w, (
 553→                    f"{gid}: 权重条目缺少 backtest_max_drawdown 字段，"
 554→                    f"实际 keys={list(w.keys())}"
 555→                )
 556→                assert isinstance(w["backtest_max_drawdown"], (int, float)), (
 557→                    f"{gid}: backtest_max_drawdown 应为数值，"
 558→                    f"实际 {type(w['backtest_max_drawdown'])}"
 559→                )
 560→
 561→    def test_output_file_no_nan(self, mock_store, mock_universe, tmp_path):
 562→        """输出的 JSON 文件不能包含 NaN（否则非法 JSON）。
 563→
 564→        迭代 #2 修复的核心问题：vectorbt 无交易场景下 Win Rate 返回 NaN，
 565→        `float(NaN or 0.0)` 仍为 NaN（NaN 是 truthy），导致 JSON 序列化写出
 566→        非法 JSON（NaN/Infinity 非 JSON 规范）。_safe_float 修复后不应再出现。
 567→        """
 568→        output = tmp_path / "weights_no_nan.json"
 569→        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)
 570→        mb.run(
 571→            strategies=["dual_ma"],
 572→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 573→            output_file=output,
 574→        )
 575→        # 用严格模式解析 JSON：json.loads 默认接受 NaN，需用 parse_constant 拦截
 576→        raw = output.read_text()
 577→        # 替换 NaN/Infinity 为哨兵字符串，再用 json 解析检测
 578→        import re as _re
 579→        bad_tokens = _re.findall(r"\bNaN\b|\bInfinity\b|\b-Infinity\b", raw)
 580→        assert not bad_tokens, (
 581→            f"JSON 中发现非法 token: {bad_tokens}（应为有限数值）"
 582→        )
 583→
 584→
 585→# ---------------------------------------------------------------------------
 586→# 迭代 #3 P0 新增：DD 约束 + fallback + dd_constrained 字段
 587→# ---------------------------------------------------------------------------
 588→
 589→class TestDDConstraint:
 590→    """P0: 修复 NDX_high_vol DD 超标（Gate 1 阻塞项）。"""
 591→
 592→    def test_dd_constrained_field_exists_in_group_result(self, mock_store, mock_universe):
 593→        """GroupBacktestResult 含 dd_constrained bool 字段，默认 False。"""
 594→        from mytrader.backtest.matrix_backtest import GroupBacktestResult
 595→        gr = GroupBacktestResult(
 596→            group_id="test", strategy="dual_ma", params={},
 597→            portfolio_sharpe=1.0, avg_total_return_pct=10.0,
 598→            avg_max_drawdown_pct=-5.0, avg_win_rate_pct=55.0, symbol_count=3,
 599→        )
 600→        assert hasattr(gr, "dd_constrained"), "GroupBacktestResult 必须有 dd_constrained 字段"
 601→        assert gr.dd_constrained is False, "dd_constrained 默认应为 False"
 602→
 603→    def test_compliant_candidates_selected_by_sortino(self, tmp_path):
 604→        """P0 case 1: 有合规候选时，按 Sortino 降序选 top-K（不选 DD 超标的候选）。
 605→
 606→        场景：3 个候选，其中 2 个 DD=10%（合规）、1 个 DD=25%（超标）。
 607→        虽然 DD=25% 的候选 Sortino 更高，但 DD 约束应将其排除。
 608→        """
 609→        # 构造 mock store：返回一组上涨数据，回测 DD 自然 < 20%
 610→        store = MagicMock()
 611→        df = _make_ohlcv(300, trend="up")
 612→        store.get_bars_multi.side_effect = lambda symbols, start, end, timeframe="1d": {
 613→            s: df.copy() for s in symbols
 614→        }
 615→
 616→        universe = MagicMock()
 617→        universe.get_groups.return_value = {"test_group": ["AAPL", "MSFT"]}
 618→
 619→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
 620→        # 用两个策略（都合规）测试 top-K 选择
 621→        report = mb.run(
 622→            strategies=["dual_ma", "rsi_mean_revert"],
 623→            param_grids={
 624→                "dual_ma": {"fast": [5], "slow": [20]},
 625→                "rsi_mean_revert": {"period": [14], "oversold": [30], "overbought": [70]},
 626→            },
 627→            output_file=tmp_path / "weights.json",
 628→        )
 629→
 630→        # 验证：有合规候选时 dd_constrained=False
 631→        for gid, weights in report.groups.items():
 632→            for w in weights:
 633→                assert "dd_constrained" in w, f"{gid}: 缺少 dd_constrained 字段"
 634→                assert w["dd_constrained"] is False, (
 635→                    f"{gid}: 有合规候选时 dd_constrained 应为 False，"
 636→                    f"实际 {w['dd_constrained']}（候选 DD 均在阈值内）"
 637→                )
 638→
 639→    def test_fallback_when_no_compliant_candidates(self, tmp_path):
 640→        """P0 case 2: 无合规候选时 fallback — 按 DD 升序选 top-K，标记 dd_constrained=True。
 641→
 642→        场景：构造 rsi_mean_revert 会买入后持续下跌的数据，让 portfolio DD >> 20%。
 643→        使用 rsi_mean_revert 策略：先压低 RSI（超卖触发买入），买入后价格持续大幅下跌。
 644→        验证：top-K 仍产出（不抛异常），且 dd_constrained=True。
 645→
 646→        注：dual_ma 是趋势跟踪策略，"先涨后跌"场景下会在下跌初期平仓，DD 不易超 20%。
 647→        rsi_mean_revert 在 oversold 买入后若价格持续跌，会持续持仓，DD 显著更高。
 648→        """
 649→        store = MagicMock()
 650→        # 构造：先压低 RSI（200天缓慢下跌触发超卖买入信号），
 651→        # 然后买入后价格急速崩溃下跌 60%，造成巨大持仓损失
 652→        n = 400
 653→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
 654→        close = (
 655→            [100.0 * (1 - 0.002 * i) for i in range(200)]   # 缓慢下跌压低RSI
 656→            + [60.0 * (1 - 0.005 * (i - 200)) for i in range(200, n)]  # 急速崩溃
 657→        )
 658→        close = [max(c, 1.0) for c in close]  # 防止价格为负
 659→        df_crash = pd.DataFrame(
 660→            {
 661→                "open":   [c - 0.3 for c in close],
 662→                "high":   [c + 0.5 for c in close],
 663→                "low":    [c - 0.5 for c in close],
 664→                "close":  close,
 665→                "volume": [1_000_000] * n,
 666→            },
 667→            index=idx,
 668→        )
 669→        store.get_bars_multi.side_effect = lambda symbols, start, end, timeframe="1d": {
 670→            s: df_crash.copy() for s in symbols
 671→        }
 672→
 673→        universe = MagicMock()
 674→        universe.get_groups.return_value = {"volatile_group": ["AAPL", "MSFT"]}
 675→
 676→        # 使用 rsi_mean_revert，超卖买入后持续下跌，确保 DD >> 20%
 677→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
 678→        report = mb.run(
 679→            strategies=["rsi_mean_revert"],
 680→            param_grids={"rsi_mean_revert": {
 681→                "period": [14], "oversold": [35], "overbought": [65]
 682→            }},
 683→            output_file=tmp_path / "weights_fallback.json",
 684→        )
 685→
 686→        # 若产生权重，验证：fallback 触发（dd_constrained=True）或无权重（极端无交易场景）
 687→        has_weights = any(weights for weights in report.groups.values() if weights)
 688→        if has_weights:
 689→            for gid, weights in report.groups.items():
 690→                for w in weights:
 691→                    if w.get("backtest_max_drawdown", 0) > 20.0:
 692→                        assert w["dd_constrained"] is True, (
 693→                            f"{gid}: DD={w['backtest_max_drawdown']:.1f}% > 20% "
 694→                            f"但 dd_constrained 为 False"
 695→                        )
 696→
 697→    def test_output_file_contains_dd_constrained_field(self, mock_store, mock_universe, tmp_path):
 698→        """P0 case 3: strategy_weights.json 每个权重条目含 dd_constrained 字段。"""
 699→        output = tmp_path / "weights_dd_constrained.json"
 700→        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)
 701→        mb.run(
 702→            strategies=["dual_ma"],
 703→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 704→            output_file=output,
 705→        )
 706→        data = json.loads(output.read_text())
 707→        for gid, weights in data["groups"].items():
 708→            for w in weights:
 709→                assert "dd_constrained" in w, (
 710→                    f"{gid}: 权重条目缺少 dd_constrained 字段，"
 711→                    f"实际 keys={list(w.keys())}"
 712→                )
 713→                assert isinstance(w["dd_constrained"], bool), (
 714→                    f"{gid}: dd_constrained 应为 bool，"
 715→                    f"实际 {type(w['dd_constrained'])}"
 716→                )
 717→
 718→    def test_max_drawdown_threshold_is_20(self):
 719→        """Constitution L1: MAX_PORTFOLIO_DRAWDOWN_PCT = 20.0（硬约束）。"""
 720→        assert MAX_PORTFOLIO_DRAWDOWN_PCT == 20.0, (
 721→            f"MAX_PORTFOLIO_DRAWDOWN_PCT 应为 20.0 (Constitution L1)，"
 722→            f"实际 {MAX_PORTFOLIO_DRAWDOWN_PCT}"
 723→        )
 724→
 725→
 726→# ---------------------------------------------------------------------------
 727→# 迭代 #3 P1 新增：Walk-Forward 4 轮验证
 728→# ---------------------------------------------------------------------------
 729→
 730→class TestWalkForward:
 731→    """P1: Walk-Forward 4 轮验证（Constitution L7 流水线硬要求）。"""
 732→
 733→    def test_walk_forward_round_dataclass(self):
 734→        """WalkForwardRound dataclass 字段完整 + passed 判定正确。"""
 735→        from datetime import date as _date
 736→        r = WalkForwardRound(
 737→            round_num=1,
 738→            train_start=_date(2021, 7, 2),
 739→            train_end=_date(2023, 1, 2),
 740→            val_start=_date(2023, 1, 2),
 741→            val_end=_date(2023, 7, 2),
 742→            val_sortino=1.5,
 743→            val_max_dd=10.0,
 744→            passed=True,
 745→        )
 746→        assert r.round_num == 1
 747→        assert r.train_start == _date(2021, 7, 2)
 748→        assert r.val_end == _date(2023, 7, 2)
 749→        assert r.val_sortino == 1.5
 750→        assert r.val_max_dd == 10.0
 751→        assert r.passed is True
 752→
 753→    def test_walk_forward_round_passed_threshold(self):
 754→        """passed = val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD (15%)。"""
 755→        from datetime import date as _date
 756→        # DD = 15.0 → passed (边界)
 757→        r_boundary = WalkForwardRound(
 758→            round_num=1,
 759→            train_start=_date(2021, 1, 1), train_end=_date(2023, 1, 1),
 760→            val_start=_date(2023, 1, 1), val_end=_date(2023, 7, 1),
 761→            val_sortino=1.0, val_max_dd=15.0, passed=True,
 762→        )
 763→        assert r_boundary.passed is True
 764→        assert WALK_FORWARD_VAL_DD_THRESHOLD == 15.0, (
 765→            f"WF 验证 DD 门槛应为 15.0%，实际 {WALK_FORWARD_VAL_DD_THRESHOLD}"
 766→        )
 767→
 768→        # DD = 15.01 → not passed
 769→        r_fail = WalkForwardRound(
 770→            round_num=2,
 771→            train_start=_date(2021, 1, 1), train_end=_date(2023, 1, 1),
 772→            val_start=_date(2023, 1, 1), val_end=_date(2023, 7, 1),
 773→            val_sortino=1.0, val_max_dd=15.01, passed=False,
 774→        )
 775→        assert r_fail.passed is False
 776→
 777→    def test_walk_forward_report_dataclass(self):
 778→        """WalkForwardReport: pass_all_rounds + max_val_dd 计算正确。"""
 779→        from datetime import date as _date
 780→        rounds = [
 781→            WalkForwardRound(1, _date(2021, 1, 1), _date(2023, 1, 1),
 782→                             _date(2023, 1, 1), _date(2023, 7, 1), 1.0, 10.0, True),
 783→            WalkForwardRound(2, _date(2021, 7, 1), _date(2023, 7, 1),
 784→                             _date(2023, 7, 1), _date(2024, 1, 1), 0.8, 12.0, True),
 785→            WalkForwardRound(3, _date(2022, 1, 1), _date(2024, 1, 1),
 786→                             _date(2024, 1, 1), _date(2024, 7, 1), 1.2, 8.0, True),
 787→            WalkForwardRound(4, _date(2022, 7, 1), _date(2024, 7, 1),
 788→                             _date(2024, 7, 1), _date(2025, 1, 1), 0.9, 14.0, True),
 789→        ]
 790→        report = WalkForwardReport(
 791→            rounds=rounds,
 792→            pass_all_rounds=all(r.passed for r in rounds),
 793→            max_val_dd=max(r.val_max_dd for r in rounds),
 794→        )
 795→        assert report.pass_all_rounds is True
 796→        assert report.max_val_dd == 14.0
 797→        assert len(report.rounds) == 4
 798→
 799→    def test_walk_forward_report_all_fail(self):
 800→        """pass_all_rounds=False 当任一轮失败。"""
 801→        from datetime import date as _date
 802→        rounds = [
 803→            WalkForwardRound(1, _date(2021, 1, 1), _date(2023, 1, 1),
 804→                             _date(2023, 1, 1), _date(2023, 7, 1), 1.0, 10.0, True),
 805→            WalkForwardRound(2, _date(2021, 7, 1), _date(2023, 7, 1),
 806→                             _date(2023, 7, 1), _date(2024, 1, 1), 0.8, 18.0, False),  # fail
 807→        ]
 808→        report = WalkForwardReport(
 809→            rounds=rounds,
 810→            pass_all_rounds=all(r.passed for r in rounds),
 811→            max_val_dd=max(r.val_max_dd for r in rounds),
 812→        )
 813→        assert report.pass_all_rounds is False
 814→        assert report.max_val_dd == 18.0
 815→
 816→    def test_add_months_basic(self):
 817→        """_add_months 基本加减月数正确。"""
 818→        from datetime import date as _date
 819→        # +18 months
 820→        assert _add_months(_date(2021, 7, 2), 18) == _date(2023, 1, 2)
 821→        # -6 months
 822→        assert _add_months(_date(2023, 7, 2), -6) == _date(2023, 1, 2)
 823→        # +0 months (identity)
 824→        assert _add_months(_date(2026, 7, 1), 0) == _date(2026, 7, 1)
 825→
 826→    def test_add_months_month_end_clamp(self):
 827→        """_add_months 自动 clamp 到月末（如 1/31 + 1 month = 2/28）。"""
 828→        from datetime import date as _date
 829→        # 1月31日 + 1月 → 2月28日（2023非闰年）
 830→        result = _add_months(_date(2023, 1, 31), 1)
 831→        assert result == _date(2023, 2, 28), f"1/31 + 1m 应为 2/28，实际 {result}"
 832→
 833→    def test_walk_forward_windows_match_user_spec(self):
 834→        """验证默认参数 (rounds=4, train_months=18, val_months=6) 产生的窗口
 835→        与用户提供的固定窗口匹配（today=2026-07-01）。
 836→
 837→        用户固定窗口：
 838→            Round 1: train 2021-07-02~2023-01-02, val 2023-01-02~2023-07-02
 839→            Round 2: train 2022-01-02~2023-07-02, val 2023-07-02~2024-01-02
 840→            Round 3: train 2022-07-02~2024-01-02, val 2024-01-02~2024-07-02
 841→            Round 4: train 2023-01-02~2024-07-02, val 2024-07-02~2025-01-02
 842→        """
 843→        from datetime import date as _date
 844→        today = _date(2026, 7, 1)
 845→        rounds = 4
 846→        train_months = 18
 847→        val_months = 6
 848→        # run_walk_forward 从最近往前推：last round 的 val_end = today - val_months
 849→        # Round 4: val_end=2026-01-01, val_start=2025-07-01, train=2024-01-01~2025-07-01
 850→        # Round 3: val_end=2025-07-01, val_start=2025-01-01, train=2023-07-01~2025-01-01
 851→        # Round 2: val_end=2025-01-01, val_start=2024-07-01, train=2023-01-01~2024-07-01
 852→        # Round 1: val_end=2024-07-01, val_start=2024-01-01, train=2022-07-01~2024-01-01
 853→        expected = [
 854→            # (round_num, train_start, train_end, val_start, val_end)
 855→            (1, _date(2022, 7, 1), _date(2024, 1, 1), _date(2024, 1, 1), _date(2024, 7, 1)),
 856→            (2, _date(2023, 1, 1), _date(2024, 7, 1), _date(2024, 7, 1), _date(2025, 1, 1)),
 857→            (3, _date(2023, 7, 1), _date(2025, 1, 1), _date(2025, 1, 1), _date(2025, 7, 1)),
 858→            (4, _date(2024, 1, 1), _date(2025, 7, 1), _date(2025, 7, 1), _date(2026, 1, 1)),
 859→        ]
 860→        for round_num, exp_ts, exp_te, exp_vs, exp_ve in expected:
 861→            val_end = _add_months(
 862→                today, -val_months - (rounds - round_num) * val_months
 863→            )
 864→            val_start = _add_months(val_end, -val_months)
 865→            train_end = val_start
 866→            train_start = _add_months(train_end, -train_months)
 867→            assert train_start == exp_ts, (
 868→                f"Round {round_num} train_start: 期望 {exp_ts}，实际 {train_start}"
 869→            )
 870→            assert train_end == exp_te, (
 871→                f"Round {round_num} train_end: 期望 {exp_te}，实际 {train_end}"
 872→            )
 873→            assert val_start == exp_vs, (
 874→                f"Round {round_num} val_start: 期望 {exp_vs}，实际 {val_start}"
 875→            )
 876→            assert val_end == exp_ve, (
 877→                f"Round {round_num} val_end: 期望 {exp_ve}，实际 {val_end}"
 878→            )
 879→
 880→    def test_run_walk_forward_mock_integration(self, mock_store, mock_universe):
 881→        """P1 集成测试：run_walk_forward 用 mock store/universe 跑完 4 轮。
 882→
 883→        验证：
 884→            1. 返回 WalkForwardReport 实例
 885→            2. rounds 长度为 4
 886→            3. 每轮有 val_sortino / val_max_dd / passed 字段
 887→            4. pass_all_rounds 与 rounds 中 passed 一致
 888→            5. max_val_dd = max(r.val_max_dd)
 889→        """
 890→        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=2)
 891→
 892→        report = run_walk_forward(
 893→            mb=mb,
 894→            strategies=["dual_ma"],
 895→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 896→            rounds=4,
 897→            train_months=18,
 898→            val_months=6,
 899→        )
 900→
 901→        assert isinstance(report, WalkForwardReport), (
 902→            f"run_walk_forward 应返回 WalkForwardReport，实际 {type(report)}"
 903→        )
 904→        assert len(report.rounds) == 4, (
 905→            f"应跑 4 轮，实际 {len(report.rounds)} 轮"
 906→        )
 907→        for i, r in enumerate(report.rounds):
 908→            assert isinstance(r, WalkForwardRound)
 909→            assert r.round_num == i + 1, (
 910→                f"Round {i}: round_num 应为 {i+1}，实际 {r.round_num}"
 911→            )
 912→            assert isinstance(r.val_sortino, float)
 913→            assert isinstance(r.val_max_dd, float)
 914→            assert r.val_max_dd >= 0.0
 915→            assert isinstance(r.passed, bool)
 916→            assert r.passed == (r.val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD)
 917→
 918→        expected_pass = all(r.passed for r in report.rounds)
 919→        assert report.pass_all_rounds == expected_pass
 920→        expected_max_dd = max(r.val_max_dd for r in report.rounds)
 921→        assert abs(report.max_val_dd - expected_max_dd) < 1e-9
 922→
 923→    def test_run_walk_forward_empty_universe(self):
 924→        """空标的组时返回空 WalkForwardReport，不抛异常。"""
 925→        store = MagicMock()
 926→        store.get_bars_multi.return_value = {}
 927→        universe = MagicMock()
 928→        universe.get_groups.return_value = {}
 929→        mb = MatrixBacktest(store=store, universe=universe, years=1)
 930→
 931→        report = run_walk_forward(
 932→            mb=mb,
 933→            strategies=["dual_ma"],
 934→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 935→            rounds=4,
 936→        )
 937→        assert isinstance(report, WalkForwardReport)
 938→        assert report.rounds == []
 939→        assert report.pass_all_rounds is False
 940→        assert report.max_val_dd == 0.0
 941→
 942→    def test_run_walk_forward_custom_rounds(self, mock_store, mock_universe):
 943→        """run_walk_forward 支持自定义 rounds 参数（非默认 4）。"""
 944→        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)
 945→        report = run_walk_forward(
 946→            mb=mb,
 947→            strategies=["dual_ma"],
 948→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 949→            rounds=2,
 950→            train_months=12,
 951→            val_months=4,
 952→        )
 953→        assert len(report.rounds) == 2
 954→        assert report.rounds[0].round_num == 1
 955→        assert report.rounds[1].round_num == 2
 956→
 957→
---
   1→"""MatrixBacktest 测试。
   2→
   3→使用 Mock MarketDataStore + 内置策略，不触碰网络。
   4→"""
   5→
   6→from __future__ import annotations
   7→
   8→import json
   9→from datetime import date
  10→from pathlib import Path
  11→from unittest.mock import MagicMock, patch
  12→
  13→import numpy as np
  14→import pandas as pd
  15→import pytest
  16→
  17→from mytrader.backtest.matrix_backtest import (
  18→    MatrixBacktest,
  19→    _backtest_one,
  20→    _compute_sharpe,
  21→    _compute_sortino,
  22→    _portfolio_max_drawdown_from_results,
  23→    _portfolio_sharpe_from_results,
  24→    _portfolio_sortino_from_results,
  25→    _safe_float,
  26→    _safe_mean,
  27→    MAX_PORTFOLIO_DRAWDOWN_PCT,
  28→    WALK_FORWARD_VAL_DD_THRESHOLD,
  29→    SingleBacktestResult,
  30→    WalkForwardReport,
  31→    WalkForwardRound,
  32→    _add_months,
  33→    run_walk_forward,
  34→)
  35→
  36→
  37→# ---------------------------------------------------------------------------
  38→# Fixtures
  39→# ---------------------------------------------------------------------------
  40→
  41→def _make_ohlcv(n: int = 300, trend: str = "up") -> pd.DataFrame:
  42→    """生成测试 OHLCV 数据（足够计算慢均线）。"""
  43→    idx = pd.date_range("2021-01-01", periods=n, freq="B")
  44→    if trend == "up":
  45→        close = [100.0 + i * 0.1 for i in range(n)]
  46→    else:
  47→        close = [100.0 - i * 0.05 for i in range(n)]
  48→    return pd.DataFrame(
  49→        {
  50→            "open":   [c - 0.5 for c in close],
  51→            "high":   [c + 1.0 for c in close],
  52→            "low":    [c - 1.0 for c in close],
  53→            "close":  close,
  54→            "volume": [1_000_000] * n,
  55→        },
  56→        index=idx,
  57→    )
  58→
  59→
  60→@pytest.fixture
  61→def mock_store(tmp_path):
  62→    store = MagicMock()
  63→    df_aapl = _make_ohlcv(300, trend="up")
  64→    df_msft = _make_ohlcv(300, trend="up")
  65→    df_jpm  = _make_ohlcv(300, trend="up")
  66→
  67→    def get_bars_multi(symbols, start, end, timeframe="1d"):
  68→        mapping = {"AAPL": df_aapl, "MSFT": df_msft, "JPM": df_jpm}
  69→        return {s: mapping[s] for s in symbols if s in mapping}
  70→
  71→    store.get_bars_multi.side_effect = get_bars_multi
  72→    return store
  73→
  74→
  75→@pytest.fixture
  76→def mock_universe():
  77→    from mytrader.universe.models import SymbolMeta
  78→    universe = MagicMock()
  79→    universe.get_groups.return_value = {
  80→        "NDX_mid_vol": ["AAPL", "MSFT"],
  81→        "SPX_mid_vol": ["JPM"],
  82→    }
  83→
  84→    def get_meta(sym):
  85→        ndx = ["AAPL", "MSFT"]
  86→        return SymbolMeta(
  87→            symbol=sym,
  88→            index_membership=["NASDAQ100"] if sym in ndx else ["SP500"],
  89→            sector="Technology" if sym in ndx else "Financials",
  90→            market_cap_tier="large",
  91→            volatility_tier="mid",
  92→            group_id="NDX_mid_vol" if sym in ndx else "SPX_mid_vol",
  93→        )
  94→    universe.get_symbol_meta.side_effect = get_meta
  95→    return universe
  96→
  97→
  98→# ---------------------------------------------------------------------------
  99→# 单函数测试
 100→# ---------------------------------------------------------------------------
 101→
 102→class TestHelpers:
 103→
 104→    def test_compute_sharpe_positive(self):
 105→        """正向收益的 Sharpe > 0。"""
 106→        returns = pd.Series([0.001] * 252)
 107→        sharpe = _compute_sharpe(returns)
 108→        assert sharpe > 0
 109→
 110→    def test_compute_sharpe_zero_std(self):
 111→        """收益恒定（零方差）返回 0。"""
 112→        returns = pd.Series([0.0] * 100)
 113→        assert _compute_sharpe(returns) == 0.0
 114→
 115→    def test_compute_sharpe_empty(self):
 116→        assert _compute_sharpe(pd.Series([], dtype=float)) == 0.0
 117→
 118→    def test_portfolio_sharpe_from_results(self):
 119→        """等权组合 Sharpe 不等于算术平均 Sharpe（差异 > 1e-6）。"""
 120→        n = 252
 121→        r1 = pd.Series(np.random.normal(0.001, 0.01, n))   # 高收益高波动
 122→        r2 = pd.Series(np.random.normal(0.0005, 0.002, n)) # 低收益低波动
 123→
 124→        s1 = _compute_sharpe(r1)
 125→        s2 = _compute_sharpe(r2)
 126→        arithmetic_avg = (s1 + s2) / 2
 127→
 128→        results = [
 129→            SingleBacktestResult("SYM1", "s1", {}, s1, 10, 5, 60, 20, r1),
 130→            SingleBacktestResult("SYM2", "s2", {}, s2, 5, 3, 55, 15, r2),
 131→        ]
 132→        portfolio_sharpe = _portfolio_sharpe_from_results(results)
 133→
 134→        # 组合 Sharpe 与算术平均 Sharpe 应不同（这正是为什么要用组合方式）
 135→        diff = abs(portfolio_sharpe - arithmetic_avg)
 136→        assert diff > 1e-6, (
 137→            f"组合 Sharpe({portfolio_sharpe:.4f}) 与算术平均 Sharpe({arithmetic_avg:.4f}) "
 138→            f"差异应 >1e-6，否则说明实现有误"
 139→        )
 140→
 141→    # ── Sortino（迭代 #1 新增，Constitution L1 首要 KPI）─────────────────────
 142→
 143→    def test_compute_sortino_positive(self):
 144→        """正均值的收益序列 Sortino > 0。"""
 145→        returns = pd.Series([0.001, -0.0005, 0.002, -0.0003, 0.0015] * 60)
 146→        assert _compute_sortino(returns) > 0
 147→
 148→    def test_compute_sortino_empty(self):
 149→        """空序列返回 0。"""
 150→        assert _compute_sortino(pd.Series([], dtype=float)) == 0.0
 151→
 152→    def test_compute_sortino_no_downside_returns_zero(self):
 153→        """全正收益（无下行波动）→ 0.0（退化处理，与 _compute_sharpe 一致）。
 154→
 155→        理论上 Sortino 应为 +inf，但返回 0 保持可算术聚合 + 保守评估。
 156→        """
 157→        returns = pd.Series([0.001] * 100)   # 全正，无下行
 158→        assert _compute_sortino(returns) == 0.0
 159→
 160→    def test_compute_sortino_differs_from_sharpe_when_asymmetric(self):
 161→        """当上行/下行波动不对称时，Sortino ≠ Sharpe（这是引入 Sortino 的意义）。"""
 162→        # 大幅上行小波动 + 偶尔小幅下行：Sortino 应明显高于 Sharpe
 163→        np.random.seed(42)
 164→        upside = np.random.normal(0.003, 0.005, 200)   # 正均值的上行
 165→        downside_shocks = np.array([-0.01, -0.012, -0.008] * 3)  # 少量下行冲击
 166→        returns = pd.Series(np.concatenate([upside, downside_shocks]))
 167→
 168→        sharpe = _compute_sharpe(returns)
 169→        sortino = _compute_sortino(returns)
 170→        # Sortino 仅对下行惩罚 → 上行波动不计入分母 → Sortino > Sharpe
 171→        assert sortino > sharpe, (
 172→            f"非对称收益下 Sortino({sortino:.4f}) 应 > Sharpe({sharpe:.4f})，"
 173→            f"否则说明 Sortino 公式退化为 Sharpe"
 174→        )
 175→
 176→    def test_compute_sortino_known_value(self):
 177→        """已知值验算 Sortino 公式正确性。"""
 178→        # r = [0.01, 0.01, 0.01, -0.01]
 179→        # mean = 0.005; downside = [0,0,0,-0.01]; dd = sqrt(mean([0,0,0,0.0001])) = sqrt(0.000025) = 0.005
 180→        # Sortino = 0.005 / 0.005 * sqrt(252) = 15.8745...
 181→        returns = pd.Series([0.01, 0.01, 0.01, -0.01] * 25)   # 重复 25 次以满足 len>=5
 182→        expected = (0.005 / 0.005) * np.sqrt(252)
 183→        assert abs(_compute_sortino(returns) - expected) < 1e-6
 184→
 185→    def test_portfolio_sortino_from_results(self):
 186→        """等权组合 Sortino 不等于各标的 Sortino 算术平均（与 Sharpe 同理）。"""
 187→        n = 252
 188→        np.random.seed(0)
 189→        r1 = pd.Series(np.random.normal(0.001, 0.01, n))
 190→        r2 = pd.Series(np.random.normal(0.0005, 0.002, n))
 191→
 192→        s1 = _compute_sortino(r1)
 193→        s2 = _compute_sortino(r2)
 194→        arithmetic_avg = (s1 + s2) / 2
 195→
 196→        results = [
 197→            SingleBacktestResult("SYM1", "s1", {}, 0.0, 0, 0, 0, 0, r1),
 198→            SingleBacktestResult("SYM2", "s2", {}, 0.0, 0, 0, 0, 0, r2),
 199→        ]
 200→        portfolio_sortino = _portfolio_sortino_from_results(results)
 201→
 202→        diff = abs(portfolio_sortino - arithmetic_avg)
 203→        assert diff > 1e-6, (
 204→            f"组合 Sortino({portfolio_sortino:.4f}) 与算术平均({arithmetic_avg:.4f}) "
 205→            f"差异应 >1e-6，否则说明实现退化为算术平均"
 206→        )
 207→
 208→    # ── _safe_float / _safe_mean（迭代 #2 新增）─────────────────────────────
 209→
 210→    def test_safe_float_handles_nan(self):
 211→        """NaN 是 truthy，`NaN or 0.0` 仍为 NaN；_safe_float 必须返回 default。"""
 212→        nan = float("nan")
 213→        assert _safe_float(nan) == 0.0
 214→        assert _safe_float(nan, default=-1.0) == -1.0
 215→
 216→    def test_safe_float_handles_none(self):
 217→        assert _safe_float(None) == 0.0
 218→        assert _safe_float(None, default=3.14) == 3.14
 219→
 220→    def test_safe_float_handles_inf(self):
 221→        assert _safe_float(float("inf")) == 0.0
 222→        assert _safe_float(float("-inf")) == 0.0
 223→
 224→    def test_safe_float_passes_normal_numbers(self):
 225→        assert _safe_float(1.5) == 1.5
 226→        assert _safe_float(0) == 0.0
 227→        assert _safe_float(-2.7) == -2.7
 228→        assert _safe_float("3.14") == 3.14   # 字符串数字可转
 229→
 230→    def test_safe_float_handles_non_numeric(self):
 231→        assert _safe_float("abc") == 0.0
 232→        assert _safe_float([1, 2, 3]) == 0.0
 233→        assert _safe_float(object()) == 0.0
 234→
 235→    def test_safe_mean_empty_list(self):
 236→        """空列表返回 default（np.mean([]) 会触发 RuntimeWarning 并返回 NaN）。"""
 237→        assert _safe_mean([]) == 0.0
 238→        assert _safe_mean([], default=2.0) == 2.0
 239→
 240→    def test_safe_mean_all_nan(self):
 241→        """全 NaN 列表返回 default。"""
 242→        assert _safe_mean([float("nan"), float("nan")]) == 0.0
 243→
 244→    def test_safe_mean_partial_nan(self):
 245→        """部分 NaN 自动忽略（nanmean 语义）。"""
 246→        result = _safe_mean([1.0, float("nan"), 3.0])
 247→        assert abs(result - 2.0) < 1e-9
 248→
 249→    def test_safe_mean_normal(self):
 250→        assert abs(_safe_mean([1.0, 2.0, 3.0]) - 2.0) < 1e-9
 251→
 252→    # ── _portfolio_max_drawdown_from_results（迭代 #2 新增）────────────────
 253→
 254→    def test_portfolio_max_drawdown_no_returns(self):
 255→        """无有效日收益率 → 0.0。"""
 256→        results: list[SingleBacktestResult] = []
 257→        assert _portfolio_max_drawdown_from_results(results) == 0.0
 258→
 259→    def test_portfolio_max_drawdown_all_positive(self):
 260→        """全正收益 → 无回撤，返回 0.0。"""
 261→        r = pd.Series([0.001] * 100)
 262→        results = [SingleBacktestResult("S1", "s", {}, 0.0, 0, 0, 0, 0, r)]
 263→        assert _portfolio_max_drawdown_from_results(results) == 0.0
 264→
 265→    def test_portfolio_max_drawdown_known_value(self):
 266→        """已知值验算：先涨后跌回测组合 DD。
 267→
 268→        组合等权日收益率 = r。cumvalue 从 1.0 涨到 1.05，再跌到 0.95。
 269→        peak = 1.05, trough = 0.95, DD = (0.95 - 1.05) / 1.05 ≈ -9.524%。
 270→        """
 271→        # 10 天 +1% → cumvalue 涨到 1.01^10 ≈ 1.1046
 272→        # 10 天 -1% → cumvalue 跌到 1.1046 * 0.99^10 ≈ 0.9994
 273→        # peak=1.1046, trough=0.9994, DD = (0.9994 - 1.1046) / 1.1046 ≈ -9.52%
 274→        returns = pd.Series([0.01] * 10 + [-0.01] * 10)
 275→        results = [SingleBacktestResult("S1", "s", {}, 0.0, 0, 0, 0, 0, returns)]
 276→        dd = _portfolio_max_drawdown_from_results(results)
 277→        assert dd > 0.0, "存在回撤时应返回正值"
 278→        assert 8.0 < dd < 11.0, f"DD 应在 9.5% 附近，实际 {dd:.4f}%"
 279→
 280→    def test_portfolio_max_drawdown_returns_positive_pct(self):
 281→        """返回值为正百分数（与 backtest_max_drawdown 输出口径一致）。"""
 282→        np.random.seed(42)
 283→        # 模拟一个带回撤的序列
 284→        r = pd.Series(np.concatenate([
 285→            np.random.normal(0.002, 0.005, 50),
 286→            np.random.normal(-0.003, 0.008, 30),
 287→            np.random.normal(0.001, 0.004, 50),
 288→        ]))
 289→        results = [SingleBacktestResult("S1", "s", {}, 0.0, 0, 0, 0, 0, r)]
 290→        dd = _portfolio_max_drawdown_from_results(results)
 291→        assert dd >= 0.0
 292→        assert isinstance(dd, float)
 293→
 294→    def test_backtest_one_with_open(self):
 295→        """传入 open= 参数，回测正常运行。"""
 296→        df = _make_ohlcv(300)
 297→        result = _backtest_one(df, "dual_ma", {"fast": 5, "slow": 20})
 298→        assert result is not None
 299→        assert not result.daily_returns.empty
 300→        assert isinstance(result.sharpe, float)
 301→
 302→    def test_backtest_one_without_open(self):
 303→        """DataFrame 中无 open 列时也能正常回测（降级为 close 执行）。"""
 304→        df = _make_ohlcv(300).drop(columns=["open"])
 305→        result = _backtest_one(df, "dual_ma", {"fast": 5, "slow": 20})
 306→        assert result is not None
 307→
 308→    def test_backtest_one_empty_df(self):
 309→        """空 DataFrame 返回 None。"""
 310→        assert _backtest_one(pd.DataFrame(), "dual_ma", {}) is None
 311→
 312→    def test_backtest_one_short_df(self):
 313→        """不足 30 根 bar 返回 None。"""
 314→        df = _make_ohlcv(10)
 315→        assert _backtest_one(df, "dual_ma", {"fast": 5, "slow": 20}) is None
 316→
 317→    def test_backtest_one_unknown_strategy(self):
 318→        """未注册策略返回 None。"""
 319→        df = _make_ohlcv(300)
 320→        assert _backtest_one(df, "nonexistent_xyz", {}) is None
 321→
 322→    def test_open_parameter_is_passed_to_vectorbt(self):
 323→        """验证有 open 列时 _backtest_one 使用 open= 参数（而非仅用 close）。
 324→
 325→        用 mock 拦截 vbt.Portfolio.from_signals，检查 open 参数是否被传入。
 326→        """
 327→        import unittest.mock as mock
 328→        df = _make_ohlcv(100)
 329→
 330→        with mock.patch("mytrader.backtest.matrix_backtest.vbt.Portfolio.from_signals") as m:
 331→            # 让 mock 返回一个假 Portfolio
 332→            fake_pf = mock.MagicMock()
 333→            fake_pf.stats.return_value = {
 334→                "Sharpe Ratio": 1.0, "Total Return [%]": 5.0,
 335→                "Max Drawdown [%]": 3.0, "Win Rate [%]": 55.0, "Total Trades": 10,
 336→            }
 337→            fake_pf.returns.return_value = pd.Series([0.001] * len(df), index=df.index)
 338→            m.return_value = fake_pf
 339→
 340→            _backtest_one(df, "dual_ma", {"fast": 5, "slow": 20})
 341→
 342→        # 验证 from_signals 被调用了，且 open 参数被传入
 343→        assert m.called
 344→        call_kwargs = m.call_args[1] if m.call_args[1] else {}
 345→        # open 参数应该在 kwargs 中
 346→        assert "open" in call_kwargs, "有 open 列时，open 参数应被传给 from_signals"
 347→
 348→
 349→# ---------------------------------------------------------------------------
 350→# MatrixBacktest 集成测试
 351→# ---------------------------------------------------------------------------
 352→
 353→class TestMatrixBacktest:
 354→
 355→    def test_run_produces_groups(self, mock_store, mock_universe):
 356→        """run() 产出包含分组权重的 MatrixBacktestReport。"""
 357→        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=2)
 358→        strategies = ["dual_ma"]
 359→        param_grids = {"dual_ma": {"fast": [5], "slow": [20]}}
 360→
 361→        report = mb.run(strategies=strategies, param_grids=param_grids)
 362→        assert len(report.groups) >= 1
 363→        # 每个分组应有策略权重配置
 364→        for gid, weights in report.groups.items():
 365→            assert isinstance(weights, list)
 366→
 367→    def test_run_weights_sum_to_one(self, mock_store, mock_universe):
 368→        """每个分组的策略权重之和 ≈ 1.0。"""
 369→        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=2)
 370→        report = mb.run(
 371→            strategies=["dual_ma", "rsi_mean_revert"],
 372→            param_grids={
 373→                "dual_ma": {"fast": [5], "slow": [20]},
 374→                "rsi_mean_revert": {"period": [14], "oversold": [30], "overbought": [70]},
 375→            },
 376→        )
 377→        for gid, weights in report.groups.items():
 378→            if weights:
 379→                total = sum(w["weight"] for w in weights)
 380→                assert abs(total - 1.0) < 0.01, f"{gid}: weights sum={total:.4f} ≠ 1.0"
 381→
 382→    def test_run_output_file(self, mock_store, mock_universe, tmp_path):
 383→        """output_file 参数会生成有效的 JSON 文件。"""
 384→        output = tmp_path / "strategy_weights.json"
 385→        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)
 386→        mb.run(
 387→            strategies=["dual_ma"],
 388→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 389→            output_file=output,
 390→        )
 391→        assert output.exists()
 392→        data = json.loads(output.read_text())
 393→        assert "_meta" in data
 394→        assert "groups" in data
 395→        assert "survivorship_bias_warning" in data["_meta"]
 396→
 397→    def test_run_empty_universe(self, mock_store):
 398→        """空标的组不崩溃。"""
 399→        universe = MagicMock()
 400→        universe.get_groups.return_value = {}
 401→        mb = MatrixBacktest(store=mock_store, universe=universe, years=1)
 402→        report = mb.run(strategies=["dual_ma"], param_grids={"dual_ma": {}})
 403→        assert report.groups == {}
 404→
 405→    def test_run_no_data_for_group(self, mock_universe, tmp_path):
 406→        """组内无数据时优雅跳过。"""
 407→        store = MagicMock()
 408→        store.get_bars_multi.return_value = {}
 409→        mb = MatrixBacktest(store=store, universe=mock_universe, years=1)
 410→        report = mb.run(
 411→            strategies=["dual_ma"],
 412→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 413→        )
 414→        # 无数据 → 分组权重为空列表
 415→        for gid, weights in report.groups.items():
 416→            assert weights == []
 417→
 418→    def test_group_results_have_portfolio_sharpe(self, mock_store, mock_universe):
 419→        """GroupBacktestResult 中 portfolio_sharpe 是用组合 Sharpe 计算的浮点数。"""
 420→        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)
 421→        report = mb.run(
 422→            strategies=["dual_ma"],
 423→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 424→        )
 425→        for gr in report.group_results:
 426→            assert isinstance(gr.portfolio_sharpe, float)
 427→            assert gr.symbol_count > 0
 428→
 429→    def test_survivorship_bias_warning_in_output(self, mock_store, mock_universe, tmp_path):
 430→        """输出文件中包含幸存者偏差警告。"""
 431→        output = tmp_path / "weights.json"
 432→        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1)
 433→        mb.run(
 434→            strategies=["dual_ma"],
 435→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 436→            output_file=output,
 437→        )
 438→        data = json.loads(output.read_text())
 439→        warning = data["_meta"].get("survivorship_bias_warning", "")
 440→        assert "成分" in warning or "survivorship" in warning.lower()
 441→
 442→    # ── 迭代 #1 新增：观测性 + 回归 + Sortino 输出 ──────────────────────────
 443→
 444→    def test_unknown_strategy_logs_warning(self, mock_store, mock_universe):
 445→        """未注册策略名在 _run_group 中输出 WARNING 日志（而非静默跳过）。
 446→
 447→        这是迭代 #1 修复的核心观测性问题：之前 _backtest_one 内部静默 return None，
 448→        导致 main.py 误用 "rsi"/"macd"/"bollinger" 简称 6 天未被发现。
 449→
 450→        注意：项目用 loguru 而非 stdlib logging，故用 loguru sink 捕获（caplog 无效）。
 451→        """
 452→        from loguru import logger
 453→
 454→        msgs: list[str] = []
 455→        # 临时 sink 捕获所有 WARNING+ 日志到列表
 456→        handler_id = logger.add(lambda m: msgs.append(str(m)), level="WARNING")
 457→        try:
 458→            mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=2)
 459→            mb.run(
 460→                strategies=["dual_ma", "totally_bogus_name"],
 461→                param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 462→            )
 463→        finally:
 464→            logger.remove(handler_id)
 465→
 466→        # 应有 WARNING 提及 bogus 策略名
 467→        assert any("totally_bogus_name" in m for m in msgs), (
 468→            f"未注册策略应触发 WARNING，实际捕获: {msgs}"
 469→        )
 470→
 471→    def test_reoptimize_strategy_names_match_registry(self):
 472→        """回归测试：main.REOPTIMIZE_STRATEGIES 中每个策略名必须在注册表中。
 473→
 474→        防止迭代 #1 的 bug 重现：策略名拼写与 @register_strategy 装饰器不匹配，
 475→        导致矩阵回测静默跳过整类策略、strategy_weights.json 退化为仅 dual_ma。
 476→        """
 477→        from main import REOPTIMIZE_STRATEGIES, REOPTIMIZE_PARAM_GRIDS
 478→        from mytrader.strategy.registry import STRATEGY_REGISTRY
 479→
 480→        assert len(REOPTIMIZE_STRATEGIES) >= 4, (
 481→            f"预期至少 4 个策略，实际 {len(REOPTIMIZE_STRATEGIES)}：{REOPTIMIZE_STRATEGIES}"
 482→        )
 483→        for name in REOPTIMIZE_STRATEGIES:
 484→            assert name in STRATEGY_REGISTRY, (
 485→                f"REOPTIMIZE_STRATEGIES 中的 '{name}' 未在 STRATEGY_REGISTRY 注册。"
 486→                f"已注册: {sorted(STRATEGY_REGISTRY.keys())}"
 487→            )
 488→            assert name in REOPTIMIZE_PARAM_GRIDS, (
 489→                f"REOPTIMIZE_PARAM_GRIDS 缺少 '{name}' 的参数网格"
 490→            )
 491→
 492→    def test_output_file_contains_sortino(self, mock_store, mock_universe, tmp_path):
 493→        """strategy_weights.json 每个权重条目含 backtest_sortino 字段（Constitution L1 首要 KPI）。"""
 494→        output = tmp_path / "weights_with_sortino.json"
 495→        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)
 496→        mb.run(
 497→            strategies=["dual_ma"],
 498→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 499→            output_file=output,
 500→        )
 501→        data = json.loads(output.read_text())
 502→        for gid, weights in data["groups"].items():
 503→            for w in weights:
 504→                assert "backtest_sortino" in w, (
 505→                    f"{gid}: 权重条目缺少 backtest_sortino 字段，实际 keys={list(w.keys())}"
 506→                )
 507→                assert isinstance(w["backtest_sortino"], (int, float)), (
 508→                    f"{gid}: backtest_sortino 应为数值，实际 {type(w['backtest_sortino'])}"
 509→                )
 510→
 511→    def test_group_results_have_portfolio_sortino(self, mock_store, mock_universe):
 512→        """GroupBacktestResult.portfolio_sortino 是浮点数（迭代 #1 新增字段）。"""
 513→        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)
 514→        report = mb.run(
 515→            strategies=["dual_ma"],
 516→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 517→        )
 518→        for gr in report.group_results:
 519→            assert isinstance(gr.portfolio_sortino, float), (
 520→                f"portfolio_sortino 应为 float，实际 {type(gr.portfolio_sortino)}"
 521→            )
 522→
 523→    # ── 迭代 #2 新增：portfolio_max_drawdown 字段 + backtest_max_drawdown 输出 ──
 524→
 525→    def test_group_results_have_portfolio_max_drawdown(self, mock_store, mock_universe):
 526→        """GroupBacktestResult.portfolio_max_drawdown 是非负浮点数。"""
 527→        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)
 528→        report = mb.run(
 529→            strategies=["dual_ma"],
 530→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 531→        )
 532→        for gr in report.group_results:
 533→            assert isinstance(gr.portfolio_max_drawdown, float), (
 534→                f"portfolio_max_drawdown 应为 float，实际 {type(gr.portfolio_max_drawdown)}"
 535→            )
 536→            assert gr.portfolio_max_drawdown >= 0.0, (
 537→                f"portfolio_max_drawdown 应非负，实际 {gr.portfolio_max_drawdown}"
 538→            )
 539→
 540→    def test_output_file_contains_max_drawdown(self, mock_store, mock_universe, tmp_path):
 541→        """strategy_weights.json 每个权重条目含 backtest_max_drawdown 字段。"""
 542→        output = tmp_path / "weights_with_dd.json"
 543→        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)
 544→        mb.run(
 545→            strategies=["dual_ma"],
 546→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 547→            output_file=output,
 548→        )
 549→        data = json.loads(output.read_text())
 550→        for gid, weights in data["groups"].items():
 551→            for w in weights:
 552→                assert "backtest_max_drawdown" in w, (
 553→                    f"{gid}: 权重条目缺少 backtest_max_drawdown 字段，"
 554→                    f"实际 keys={list(w.keys())}"
 555→                )
 556→                assert isinstance(w["backtest_max_drawdown"], (int, float)), (
 557→                    f"{gid}: backtest_max_drawdown 应为数值，"
 558→                    f"实际 {type(w['backtest_max_drawdown'])}"
 559→                )
 560→
 561→    def test_output_file_no_nan(self, mock_store, mock_universe, tmp_path):
 562→        """输出的 JSON 文件不能包含 NaN（否则非法 JSON）。
 563→
 564→        迭代 #2 修复的核心问题：vectorbt 无交易场景下 Win Rate 返回 NaN，
 565→        `float(NaN or 0.0)` 仍为 NaN（NaN 是 truthy），导致 JSON 序列化写出
 566→        非法 JSON（NaN/Infinity 非 JSON 规范）。_safe_float 修复后不应再出现。
 567→        """
 568→        output = tmp_path / "weights_no_nan.json"
 569→        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)
 570→        mb.run(
 571→            strategies=["dual_ma"],
 572→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 573→            output_file=output,
 574→        )
 575→        # 用严格模式解析 JSON：json.loads 默认接受 NaN，需用 parse_constant 拦截
 576→        raw = output.read_text()
 577→        # 替换 NaN/Infinity 为哨兵字符串，再用 json 解析检测
 578→        import re as _re
 579→        bad_tokens = _re.findall(r"\bNaN\b|\bInfinity\b|\b-Infinity\b", raw)
 580→        assert not bad_tokens, (
 581→            f"JSON 中发现非法 token: {bad_tokens}（应为有限数值）"
 582→        )
 583→
 584→
 585→# ---------------------------------------------------------------------------
 586→# 迭代 #3 P0 新增：DD 约束 + fallback + dd_constrained 字段
 587→# ---------------------------------------------------------------------------
 588→
 589→class TestDDConstraint:
 590→    """P0: 修复 NDX_high_vol DD 超标（Gate 1 阻塞项）。"""
 591→
 592→    def test_dd_constrained_field_exists_in_group_result(self, mock_store, mock_universe):
 593→        """GroupBacktestResult 含 dd_constrained bool 字段，默认 False。"""
 594→        from mytrader.backtest.matrix_backtest import GroupBacktestResult
 595→        gr = GroupBacktestResult(
 596→            group_id="test", strategy="dual_ma", params={},
 597→            portfolio_sharpe=1.0, avg_total_return_pct=10.0,
 598→            avg_max_drawdown_pct=-5.0, avg_win_rate_pct=55.0, symbol_count=3,
 599→        )
 600→        assert hasattr(gr, "dd_constrained"), "GroupBacktestResult 必须有 dd_constrained 字段"
 601→        assert gr.dd_constrained is False, "dd_constrained 默认应为 False"
 602→
 603→    def test_compliant_candidates_selected_by_sortino(self, tmp_path):
 604→        """P0 case 1: 有合规候选时，按 Sortino 降序选 top-K（不选 DD 超标的候选）。
 605→
 606→        场景：3 个候选，其中 2 个 DD=10%（合规）、1 个 DD=25%（超标）。
 607→        虽然 DD=25% 的候选 Sortino 更高，但 DD 约束应将其排除。
 608→        """
 609→        # 构造 mock store：返回一组上涨数据，回测 DD 自然 < 20%
 610→        store = MagicMock()
 611→        df = _make_ohlcv(300, trend="up")
 612→        store.get_bars_multi.side_effect = lambda symbols, start, end, timeframe="1d": {
 613→            s: df.copy() for s in symbols
 614→        }
 615→
 616→        universe = MagicMock()
 617→        universe.get_groups.return_value = {"test_group": ["AAPL", "MSFT"]}
 618→
 619→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
 620→        # 用两个策略（都合规）测试 top-K 选择
 621→        report = mb.run(
 622→            strategies=["dual_ma", "rsi_mean_revert"],
 623→            param_grids={
 624→                "dual_ma": {"fast": [5], "slow": [20]},
 625→                "rsi_mean_revert": {"period": [14], "oversold": [30], "overbought": [70]},
 626→            },
 627→            output_file=tmp_path / "weights.json",
 628→        )
 629→
 630→        # 验证：有合规候选时 dd_constrained=False
 631→        for gid, weights in report.groups.items():
 632→            for w in weights:
 633→                assert "dd_constrained" in w, f"{gid}: 缺少 dd_constrained 字段"
 634→                assert w["dd_constrained"] is False, (
 635→                    f"{gid}: 有合规候选时 dd_constrained 应为 False，"
 636→                    f"实际 {w['dd_constrained']}（候选 DD 均在阈值内）"
 637→                )
 638→
 639→    def test_fallback_when_no_compliant_candidates(self, tmp_path):
 640→        """P0 case 2: 无合规候选时 fallback — 按 DD 升序选 top-K，标记 dd_constrained=True。
 641→
 642→        场景：构造 rsi_mean_revert 会买入后持续下跌的数据，让 portfolio DD >> 20%。
 643→        使用 rsi_mean_revert 策略：先压低 RSI（超卖触发买入），买入后价格持续大幅下跌。
 644→        验证：top-K 仍产出（不抛异常），且 dd_constrained=True。
 645→
 646→        注：dual_ma 是趋势跟踪策略，"先涨后跌"场景下会在下跌初期平仓，DD 不易超 20%。
 647→        rsi_mean_revert 在 oversold 买入后若价格持续跌，会持续持仓，DD 显著更高。
 648→        """
 649→        store = MagicMock()
 650→        # 构造：先压低 RSI（200天缓慢下跌触发超卖买入信号），
 651→        # 然后买入后价格急速崩溃下跌 60%，造成巨大持仓损失
 652→        n = 400
 653→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
 654→        close = (
 655→            [100.0 * (1 - 0.002 * i) for i in range(200)]   # 缓慢下跌压低RSI
 656→            + [60.0 * (1 - 0.005 * (i - 200)) for i in range(200, n)]  # 急速崩溃
 657→        )
 658→        close = [max(c, 1.0) for c in close]  # 防止价格为负
 659→        df_crash = pd.DataFrame(
 660→            {
 661→                "open":   [c - 0.3 for c in close],
 662→                "high":   [c + 0.5 for c in close],
 663→                "low":    [c - 0.5 for c in close],
 664→                "close":  close,
 665→                "volume": [1_000_000] * n,
 666→            },
 667→            index=idx,
 668→        )
 669→        store.get_bars_multi.side_effect = lambda symbols, start, end, timeframe="1d": {
 670→            s: df_crash.copy() for s in symbols
 671→        }
 672→
 673→        universe = MagicMock()
 674→        universe.get_groups.return_value = {"volatile_group": ["AAPL", "MSFT"]}
 675→
 676→        # 使用 rsi_mean_revert，超卖买入后持续下跌，确保 DD >> 20%
 677→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
 678→        report = mb.run(
 679→            strategies=["rsi_mean_revert"],
 680→            param_grids={"rsi_mean_revert": {
 681→                "period": [14], "oversold": [35], "overbought": [65]
 682→            }},
 683→            output_file=tmp_path / "weights_fallback.json",
 684→        )
 685→
 686→        # 若产生权重，验证：fallback 触发（dd_constrained=True）或无权重（极端无交易场景）
 687→        has_weights = any(weights for weights in report.groups.values() if weights)
 688→        if has_weights:
 689→            for gid, weights in report.groups.items():
 690→                for w in weights:
 691→                    if w.get("backtest_max_drawdown", 0) > 20.0:
 692→                        assert w["dd_constrained"] is True, (
 693→                            f"{gid}: DD={w['backtest_max_drawdown']:.1f}% > 20% "
 694→                            f"但 dd_constrained 为 False"
 695→                        )
 696→
 697→    def test_output_file_contains_dd_constrained_field(self, mock_store, mock_universe, tmp_path):
 698→        """P0 case 3: strategy_weights.json 每个权重条目含 dd_constrained 字段。"""
 699→        output = tmp_path / "weights_dd_constrained.json"
 700→        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)
 701→        mb.run(
 702→            strategies=["dual_ma"],
 703→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 704→            output_file=output,
 705→        )
 706→        data = json.loads(output.read_text())
 707→        for gid, weights in data["groups"].items():
 708→            for w in weights:
 709→                assert "dd_constrained" in w, (
 710→                    f"{gid}: 权重条目缺少 dd_constrained 字段，"
 711→                    f"实际 keys={list(w.keys())}"
 712→                )
 713→                assert isinstance(w["dd_constrained"], bool), (
 714→                    f"{gid}: dd_constrained 应为 bool，"
 715→                    f"实际 {type(w['dd_constrained'])}"
 716→                )
 717→
 718→    def test_max_drawdown_threshold_is_20(self):
 719→        """Constitution L1: MAX_PORTFOLIO_DRAWDOWN_PCT = 20.0（硬约束）。"""
 720→        assert MAX_PORTFOLIO_DRAWDOWN_PCT == 20.0, (
 721→            f"MAX_PORTFOLIO_DRAWDOWN_PCT 应为 20.0 (Constitution L1)，"
 722→            f"实际 {MAX_PORTFOLIO_DRAWDOWN_PCT}"
 723→        )
 724→
 725→
 726→# ---------------------------------------------------------------------------
 727→# 迭代 #3 P1 新增：Walk-Forward 4 轮验证
 728→# ---------------------------------------------------------------------------
 729→
 730→class TestWalkForward:
 731→    """P1: Walk-Forward 4 轮验证（Constitution L7 流水线硬要求）。"""
 732→
 733→    def test_walk_forward_round_dataclass(self):
 734→        """WalkForwardRound dataclass 字段完整 + passed 判定正确。"""
 735→        from datetime import date as _date
 736→        r = WalkForwardRound(
 737→            round_num=1,
 738→            train_start=_date(2021, 7, 2),
 739→            train_end=_date(2023, 1, 2),
 740→            val_start=_date(2023, 1, 2),
 741→            val_end=_date(2023, 7, 2),
 742→            val_sortino=1.5,
 743→            val_max_dd=10.0,
 744→            passed=True,
 745→        )
 746→        assert r.round_num == 1
 747→        assert r.train_start == _date(2021, 7, 2)
 748→        assert r.val_end == _date(2023, 7, 2)
 749→        assert r.val_sortino == 1.5
 750→        assert r.val_max_dd == 10.0
 751→        assert r.passed is True
 752→
 753→    def test_walk_forward_round_passed_threshold(self):
 754→        """passed = val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD (15%)。"""
 755→        from datetime import date as _date
 756→        # DD = 15.0 → passed (边界)
 757→        r_boundary = WalkForwardRound(
 758→            round_num=1,
 759→            train_start=_date(2021, 1, 1), train_end=_date(2023, 1, 1),
 760→            val_start=_date(2023, 1, 1), val_end=_date(2023, 7, 1),
 761→            val_sortino=1.0, val_max_dd=15.0, passed=True,
 762→        )
 763→        assert r_boundary.passed is True
 764→        assert WALK_FORWARD_VAL_DD_THRESHOLD == 15.0, (
 765→            f"WF 验证 DD 门槛应为 15.0%，实际 {WALK_FORWARD_VAL_DD_THRESHOLD}"
 766→        )
 767→
 768→        # DD = 15.01 → not passed
 769→        r_fail = WalkForwardRound(
 770→            round_num=2,
 771→            train_start=_date(2021, 1, 1), train_end=_date(2023, 1, 1),
 772→            val_start=_date(2023, 1, 1), val_end=_date(2023, 7, 1),
 773→            val_sortino=1.0, val_max_dd=15.01, passed=False,
 774→        )
 775→        assert r_fail.passed is False
 776→
 777→    def test_walk_forward_report_dataclass(self):
 778→        """WalkForwardReport: pass_all_rounds + max_val_dd 计算正确。"""
 779→        from datetime import date as _date
 780→        rounds = [
 781→            WalkForwardRound(1, _date(2021, 1, 1), _date(2023, 1, 1),
 782→                             _date(2023, 1, 1), _date(2023, 7, 1), 1.0, 10.0, True),
 783→            WalkForwardRound(2, _date(2021, 7, 1), _date(2023, 7, 1),
 784→                             _date(2023, 7, 1), _date(2024, 1, 1), 0.8, 12.0, True),
 785→            WalkForwardRound(3, _date(2022, 1, 1), _date(2024, 1, 1),
 786→                             _date(2024, 1, 1), _date(2024, 7, 1), 1.2, 8.0, True),
 787→            WalkForwardRound(4, _date(2022, 7, 1), _date(2024, 7, 1),
 788→                             _date(2024, 7, 1), _date(2025, 1, 1), 0.9, 14.0, True),
 789→        ]
 790→        report = WalkForwardReport(
 791→            rounds=rounds,
 792→            pass_all_rounds=all(r.passed for r in rounds),
 793→            max_val_dd=max(r.val_max_dd for r in rounds),
 794→        )
 795→        assert report.pass_all_rounds is True
 796→        assert report.max_val_dd == 14.0
 797→        assert len(report.rounds) == 4
 798→
 799→    def test_walk_forward_report_all_fail(self):
 800→        """pass_all_rounds=False 当任一轮失败。"""
 801→        from datetime import date as _date
 802→        rounds = [
 803→            WalkForwardRound(1, _date(2021, 1, 1), _date(2023, 1, 1),
 804→                             _date(2023, 1, 1), _date(2023, 7, 1), 1.0, 10.0, True),
 805→            WalkForwardRound(2, _date(2021, 7, 1), _date(2023, 7, 1),
 806→                             _date(2023, 7, 1), _date(2024, 1, 1), 0.8, 18.0, False),  # fail
 807→        ]
 808→        report = WalkForwardReport(
 809→            rounds=rounds,
 810→            pass_all_rounds=all(r.passed for r in rounds),
 811→            max_val_dd=max(r.val_max_dd for r in rounds),
 812→        )
 813→        assert report.pass_all_rounds is False
 814→        assert report.max_val_dd == 18.0
 815→
 816→    def test_add_months_basic(self):
 817→        """_add_months 基本加减月数正确。"""
 818→        from datetime import date as _date
 819→        # +18 months
 820→        assert _add_months(_date(2021, 7, 2), 18) == _date(2023, 1, 2)
 821→        # -6 months
 822→        assert _add_months(_date(2023, 7, 2), -6) == _date(2023, 1, 2)
 823→        # +0 months (identity)
 824→        assert _add_months(_date(2026, 7, 1), 0) == _date(2026, 7, 1)
 825→
 826→    def test_add_months_month_end_clamp(self):
 827→        """_add_months 自动 clamp 到月末（如 1/31 + 1 month = 2/28）。"""
 828→        from datetime import date as _date
 829→        # 1月31日 + 1月 → 2月28日（2023非闰年）
 830→        result = _add_months(_date(2023, 1, 31), 1)
 831→        assert result == _date(2023, 2, 28), f"1/31 + 1m 应为 2/28，实际 {result}"
 832→
 833→    def test_walk_forward_windows_match_user_spec(self):
 834→        """验证默认参数 (rounds=4, train_months=18, val_months=6) 产生的窗口
 835→        与用户提供的固定窗口匹配（today=2026-07-01）。
 836→
 837→        用户固定窗口：
 838→            Round 1: train 2021-07-02~2023-01-02, val 2023-01-02~2023-07-02
 839→            Round 2: train 2022-01-02~2023-07-02, val 2023-07-02~2024-01-02
 840→            Round 3: train 2022-07-02~2024-01-02, val 2024-01-02~2024-07-02
 841→            Round 4: train 2023-01-02~2024-07-02, val 2024-07-02~2025-01-02
 842→        """
 843→        from datetime import date as _date
 844→        today = _date(2026, 7, 1)
 845→        rounds = 4
 846→        train_months = 18
 847→        val_months = 6
 848→        # run_walk_forward 从最近往前推：last round 的 val_end = today - val_months
 849→        # Round 4: val_end=2026-01-01, val_start=2025-07-01, train=2024-01-01~2025-07-01
 850→        # Round 3: val_end=2025-07-01, val_start=2025-01-01, train=2023-07-01~2025-01-01
 851→        # Round 2: val_end=2025-01-01, val_start=2024-07-01, train=2023-01-01~2024-07-01
 852→        # Round 1: val_end=2024-07-01, val_start=2024-01-01, train=2022-07-01~2024-01-01
 853→        expected = [
 854→            # (round_num, train_start, train_end, val_start, val_end)
 855→            (1, _date(2022, 7, 1), _date(2024, 1, 1), _date(2024, 1, 1), _date(2024, 7, 1)),
 856→            (2, _date(2023, 1, 1), _date(2024, 7, 1), _date(2024, 7, 1), _date(2025, 1, 1)),
 857→            (3, _date(2023, 7, 1), _date(2025, 1, 1), _date(2025, 1, 1), _date(2025, 7, 1)),
 858→            (4, _date(2024, 1, 1), _date(2025, 7, 1), _date(2025, 7, 1), _date(2026, 1, 1)),
 859→        ]
 860→        for round_num, exp_ts, exp_te, exp_vs, exp_ve in expected:
 861→            val_end = _add_months(
 862→                today, -val_months - (rounds - round_num) * val_months
 863→            )
 864→            val_start = _add_months(val_end, -val_months)
 865→            train_end = val_start
 866→            train_start = _add_months(train_end, -train_months)
 867→            assert train_start == exp_ts, (
 868→                f"Round {round_num} train_start: 期望 {exp_ts}，实际 {train_start}"
 869→            )
 870→            assert train_end == exp_te, (
 871→                f"Round {round_num} train_end: 期望 {exp_te}，实际 {train_end}"
 872→            )
 873→            assert val_start == exp_vs, (
 874→                f"Round {round_num} val_start: 期望 {exp_vs}，实际 {val_start}"
 875→            )
 876→            assert val_end == exp_ve, (
 877→                f"Round {round_num} val_end: 期望 {exp_ve}，实际 {val_end}"
 878→            )
 879→
 880→    def test_run_walk_forward_mock_integration(self, mock_store, mock_universe):
 881→        """P1 集成测试：run_walk_forward 用 mock store/universe 跑完 4 轮。
 882→
 883→        验证：
 884→            1. 返回 WalkForwardReport 实例
 885→            2. rounds 长度为 4
 886→            3. 每轮有 val_sortino / val_max_dd / passed 字段
 887→            4. pass_all_rounds 与 rounds 中 passed 一致
 888→            5. max_val_dd = max(r.val_max_dd)
 889→        """
 890→        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=2)
 891→
 892→        report = run_walk_forward(
 893→            mb=mb,
 894→            strategies=["dual_ma"],
 895→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 896→            rounds=4,
 897→            train_months=18,
 898→            val_months=6,
 899→        )
 900→
 901→        assert isinstance(report, WalkForwardReport), (
 902→            f"run_walk_forward 应返回 WalkForwardReport，实际 {type(report)}"
 903→        )
 904→        assert len(report.rounds) == 4, (
 905→            f"应跑 4 轮，实际 {len(report.rounds)} 轮"
 906→        )
 907→        for i, r in enumerate(report.rounds):
 908→            assert isinstance(r, WalkForwardRound)
 909→            assert r.round_num == i + 1, (
 910→                f"Round {i}: round_num 应为 {i+1}，实际 {r.round_num}"
 911→            )
 912→            assert isinstance(r.val_sortino, float)
 913→            assert isinstance(r.val_max_dd, float)
 914→            assert r.val_max_dd >= 0.0
 915→            assert isinstance(r.passed, bool)
 916→            assert r.passed == (r.val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD)
 917→
 918→        expected_pass = all(r.passed for r in report.rounds)
 919→        assert report.pass_all_rounds == expected_pass
 920→        expected_max_dd = max(r.val_max_dd for r in report.rounds)
 921→        assert abs(report.max_val_dd - expected_max_dd) < 1e-9
 922→
 923→    def test_run_walk_forward_empty_universe(self):
 924→        """空标的组时返回空 WalkForwardReport，不抛异常。"""
 925→        store = MagicMock()
 926→        store.get_bars_multi.return_value = {}
 927→        universe = MagicMock()
 928→        universe.get_groups.return_value = {}
 929→        mb = MatrixBacktest(store=store, universe=universe, years=1)
 930→
 931→        report = run_walk_forward(
 932→            mb=mb,
 933→            strategies=["dual_ma"],
 934→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 935→            rounds=4,
 936→        )
 937→        assert isinstance(report, WalkForwardReport)
 938→        assert report.rounds == []
 939→        assert report.pass_all_rounds is False
 940→        assert report.max_val_dd == 0.0
 941→
 942→    def test_run_walk_forward_custom_rounds(self, mock_store, mock_universe):
 943→        """run_walk_forward 支持自定义 rounds 参数（非默认 4）。"""
 944→        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)
 945→        report = run_walk_forward(
 946→            mb=mb,
 947→            strategies=["dual_ma"],
 948→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 949→            rounds=2,
 950→            train_months=12,
 951→            val_months=4,
 952→        )
 953→        assert len(report.rounds) == 2
 954→        assert report.rounds[0].round_num == 1
 955→        assert report.rounds[1].round_num == 2
 956→
 957→
---
Now
---
 I
---
 have a full
---
 understanding of
---
 the existing code and
---
 tests. Let me check
---
 if there's an experience
---
.md file mentioned
---
 in the spec:
---
让我检查一下 `
---
experience.md` 并
---
核对
---
齐
---
轨
---
（
---
alignment trajectory
---
）以
---
了解
---
上下文：
---
{"command": "ls /Users/rickouyang/Github/trade-tools/alignment/ 2>/dev/null && ls /Users/rickouyang/Github/trade-tools/mytrader/iterations/iteration_9/ 2>/dev/null", "description": "List alignment directory"}
---
List alignment directory
---
Command: ls /Users/rickouyang/Github/trade-tools/alignment/ 2>/dev/null && ls /Users/rickouyang/Github/trade-tools/mytrader/iterations/iteration_9/ 2>/dev/null
Stdout: __pycache__             iteration_trajectory.md questionair.md
ai_constitution.md      monitor.py              tests
decision_log.md         orchestrator.py
interview_progress.md   orchestrator_design.md

Stderr: (empty)
Exit Code: 1
Signal: (none)
---
{"command": "find /Users/rickouyang/Github/trade-tools -name \"experience.md\" 2>/dev/null | head -5", "description": "Find experience.md file"}
---
Find experience.md file
---
Command: find /Users/rickouyang/Github/trade-tools -name "experience.md" 2>/dev/null | head -5
Stdout: /Users/rickouyang/Github/trade-tools/.codebuddy/notes/experience.md

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"file_path": "/Users/rickouyang/Github/trade-tools/.codebuddy/notes/experience.md"}
---
   1→# 编程原则
   2→
   3→> 每次写代码前默念一遍。
   4→
   5→---
   6→
   7→## 1. 静默失败是调试成本最高的 bug
   8→
   9→- `except Exception: return []`、`save=True` 但路径是 None → 看起来成功了，N 步之后发现什么都没发生
  10→- 原则：**任何可能失败的操作，要么成功，要么让调用方立刻感知到（raise / warn / 返回 Result 类型）**
  11→
  12→## 2. I/O 边界必须校验内容，不能只校验"是否存在"
  13→
  14→- 文件存在 ≠ 数据有效（空文件、0 字节、只有表头）
  15→- 网络请求没抛异常 ≠ 拿到了正确数据（403 但返回空列表）
  16→- 原则：**读完之后立刻校验：records 非空？行数合理？关键字段有值？**
  17→
  18→## 3. 调用方要对被调用方的副作用前提负责
  19→
  20→- `xxx.save()` 写入哪个路径？传入的参数是否正确？
  21→- 临时对象的方法调用产生的副作用，后续消费方能拿到吗？
  22→- 原则：**往下传参数之前，确认接收方的"成功条件"是什么，而不是假设它"自己会处理"**
  23→
  24→## 4. 不要在错误的抽象层找根因
  25→
  26→- 403 ≠ GFW，可能只是少了 User-Agent
  27→- 原则：**现象和根因之间至少隔着一层。先缩小范围做对照实验（什么方式能复现？什么方式不能？），再下结论**
  28→
  29→## 5. 单元测试无法替代集成测试
  30→
  31→**背景**：Phase 5 有 457 个单元测试全部通过，但系统跑起来之后出现了 6 个 bug：
  32→
  33→| bug | 为什么单元测试没发现 |
  34→|-----|-------------------|
  35→| `group_id=UNKNOWN`（未调分层计算） | Container 的单元测试 mock 了 UniverseManager，根本不走真实分组逻辑 |
  36→| 读到空数据库 | 测试用 `:memory:` 或 tmp_path，从不接触真实 `~/.mytrader/market_data.db` |
  37→| datetime tz 不兼容 | 测试构造的 Signal.timestamp 是 tz-naive，真实系统产生的是 tz-aware |
  38→| RiskManager 属性名写错 | CandidateSelector 测试直接传 `AccountState`，从未实例化 RiskManager |
  39→
  40→**根本原因**：测试覆盖了每个模块的内部逻辑，但**没有测试模块之间的拼接**。集成测试缺失意味着：每块砖都是好的，但建出来的墙可能是歪的。
  41→
  42→**原则**：
  43→- 每个"链路节点"写完后，必须写一个从真实入口到该节点的端到端集成测试
  44→- 集成测试要用**真实数据路径**（非 mock），至少要用能代表真实状态的 fixture
  45→- 具体到本项目：每个新 Sprint 完成后，跑 `--scan-now morning`（哪怕本地没数据），确认从入口到链路末端没有崩溃
  46→
  47→---
  48→
  49→*持续更新。每犯一次新类型的错误，提炼一条原则。*
  50→
  51→
---
   1→# 编程原则
   2→
   3→> 每次写代码前默念一遍。
   4→
   5→---
   6→
   7→## 1. 静默失败是调试成本最高的 bug
   8→
   9→- `except Exception: return []`、`save=True` 但路径是 None → 看起来成功了，N 步之后发现什么都没发生
  10→- 原则：**任何可能失败的操作，要么成功，要么让调用方立刻感知到（raise / warn / 返回 Result 类型）**
  11→
  12→## 2. I/O 边界必须校验内容，不能只校验"是否存在"
  13→
  14→- 文件存在 ≠ 数据有效（空文件、0 字节、只有表头）
  15→- 网络请求没抛异常 ≠ 拿到了正确数据（403 但返回空列表）
  16→- 原则：**读完之后立刻校验：records 非空？行数合理？关键字段有值？**
  17→
  18→## 3. 调用方要对被调用方的副作用前提负责
  19→
  20→- `xxx.save()` 写入哪个路径？传入的参数是否正确？
  21→- 临时对象的方法调用产生的副作用，后续消费方能拿到吗？
  22→- 原则：**往下传参数之前，确认接收方的"成功条件"是什么，而不是假设它"自己会处理"**
  23→
  24→## 4. 不要在错误的抽象层找根因
  25→
  26→- 403 ≠ GFW，可能只是少了 User-Agent
  27→- 原则：**现象和根因之间至少隔着一层。先缩小范围做对照实验（什么方式能复现？什么方式不能？），再下结论**
  28→
  29→## 5. 单元测试无法替代集成测试
  30→
  31→**背景**：Phase 5 有 457 个单元测试全部通过，但系统跑起来之后出现了 6 个 bug：
  32→
  33→| bug | 为什么单元测试没发现 |
  34→|-----|-------------------|
  35→| `group_id=UNKNOWN`（未调分层计算） | Container 的单元测试 mock 了 UniverseManager，根本不走真实分组逻辑 |
  36→| 读到空数据库 | 测试用 `:memory:` 或 tmp_path，从不接触真实 `~/.mytrader/market_data.db` |
  37→| datetime tz 不兼容 | 测试构造的 Signal.timestamp 是 tz-naive，真实系统产生的是 tz-aware |
  38→| RiskManager 属性名写错 | CandidateSelector 测试直接传 `AccountState`，从未实例化 RiskManager |
  39→
  40→**根本原因**：测试覆盖了每个模块的内部逻辑，但**没有测试模块之间的拼接**。集成测试缺失意味着：每块砖都是好的，但建出来的墙可能是歪的。
  41→
  42→**原则**：
  43→- 每个"链路节点"写完后，必须写一个从真实入口到该节点的端到端集成测试
  44→- 集成测试要用**真实数据路径**（非 mock），至少要用能代表真实状态的 fixture
  45→- 具体到本项目：每个新 Sprint 完成后，跑 `--scan-now morning`（哪怕本地没数据），确认从入口到链路末端没有崩溃
  46→
  47→---
  48→
  49→*持续更新。每犯一次新类型的错误，提炼一条原则。*
  50→
  51→
---
{"file_path": "/Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md", "limit": 80, "offset": 1}
---
   1→
   2→## 迭代 #0 — 读取 mytrader/backtest/runner.py 的代码并用一句话总结它的功能
   3→
   4→- **日期**: 2026-06-30 05:46 UTC
   5→- **类型**: 自动化迭代 (Orchestrator → CodeBuddy)
   6→- **变更摘要**: 读取 mytrader/backtest/runner.py 的代码并用一句话总结它的功能
   7→- **执行时长**: 79.2s
   8→- **状态**: passed
   9→- **CodeBuddy 更新数**: 60
  10→- **工具调用数**: 4
  11→- **团队事件数**: 0
  12→- **权限请求数**: 0
  13→- **违规检测**: 0 条
  14→- **测试收集**: 0
  15→
  16→### 违规详情
  17→- ✅ 无违规
  18→
  19→### CodeBuddy 最终响应 (摘要)
  20→。
  21→
  22→### Experience Learned
  23→- 自动化迭代通过 ACP 协议成功执行
  24→- 迭代状态: passed
  25→
  26→### 后续建议
  27→- 根据 CodeBuddy 的实际产出决定下一步
  28→- 检查测试是否全部通过
  29→
  30→---
  31→
  32→## 迭代 #1 — 策略名 bug 修复 + Sortino 指标引入
  33→
  34→- **日期**: 2026-06-30 15:53 ~ 16:20 UTC
  35→- **类型**: Bug 修复 + KPI 补全
  36→- **变更摘要**: 修复 `main.py` 中策略名与 `@register_strategy` 注册表不匹配导致 3 个策略被静默跳过的 bug；新增 Sortino Ratio 计算（Constitution L1 首要 KPI）
  37→- **执行时长**: ~27 分钟
  38→- **状态**: passed
  39→- **CodeBuddy 更新数**: ~2252 行日志
  40→- **工具调用数**: ~100+ (Read/Bash/Edit/Grep)
  41→- **团队事件数**: 0
  42→- **权限请求数**: 0 (bypassPermissions)
  43→- **违规检测**: 0 条
  44→
  45→### 变更详情
  46→
  47→**Bug 修复 (P0)**:
  48→- `main.py::_run_reoptimize` 中策略名 `["dual_ma","rsi","macd","bollinger"]` 与注册表 `["dual_ma","rsi_mean_revert","macd_cross","bollinger_band"]` 不匹配，导致 3 个策略被静默跳过
  49→- 提取为模块级常量 `REOPTIMIZE_STRATEGIES` / `REOPTIMIZE_PARAM_GRIDS` 便于回归测试
  50→- `matrix_backtest.py::_run_group` 加 warning 替代静默 `return None`
  51→- `examples/phase5_e2e.py` 同款 bug 修复
  52→
  53→**Sortino 指标 (P1)**:
  54→- 新增 `_compute_sortino()` + `_portfolio_sortino_from_results()`
  55→- `SingleBacktestResult.sortino` / `GroupBacktestResult.portfolio_sortino` 字段
  56→- `strategy_weights.json` 每条目输出 `backtest_sortino`
  57→
  58→**测试新增 (P2)**:
  59→- 10 个新测试：Sortino 单元测试 + 回归测试 + WARNING 测试
  60→- 测试总数：467 → 478 passed (5 failed 是 IBKR live 集成测试，pre-existing)
  61→
  62→**文档更新**:
  63→- `designs/design_v2/CHANGELOG.md` — v2.2 变更记录
  64→- `07-backtest-module.md` / `12-strategy-matrix.md` — Sortino 字段 + 策略名校验
  65→
  66→### 验证结果
  67→```
  68→478 passed, 5 failed (IBKR live, pre-existing)
  69→=== ✅ 全部验证通过 ===
  70→```
  71→
  72→### Constitution 合规
  73→- ✅ 未突破 DD 20% 约束
  74→- ✅ 测试覆盖率提升（+11 测试）
  75→- ✅ 未引入黑箱策略
  76→- ✅ 未引入 RL
  77→- ✅ 文档与代码同步
  78→- ✅ 低风险变更（bug 修复 + 指标补全），符合自动部署条件
  79→
  80→### Experience Learned
  81→
---
   1→
   2→## 迭代 #0 — 读取 mytrader/backtest/runner.py 的代码并用一句话总结它的功能
   3→
   4→- **日期**: 2026-06-30 05:46 UTC
   5→- **类型**: 自动化迭代 (Orchestrator → CodeBuddy)
   6→- **变更摘要**: 读取 mytrader/backtest/runner.py 的代码并用一句话总结它的功能
   7→- **执行时长**: 79.2s
   8→- **状态**: passed
   9→- **CodeBuddy 更新数**: 60
  10→- **工具调用数**: 4
  11→- **团队事件数**: 0
  12→- **权限请求数**: 0
  13→- **违规检测**: 0 条
  14→- **测试收集**: 0
  15→
  16→### 违规详情
  17→- ✅ 无违规
  18→
  19→### CodeBuddy 最终响应 (摘要)
  20→。
  21→
  22→### Experience Learned
  23→- 自动化迭代通过 ACP 协议成功执行
  24→- 迭代状态: passed
  25→
  26→### 后续建议
  27→- 根据 CodeBuddy 的实际产出决定下一步
  28→- 检查测试是否全部通过
  29→
  30→---
  31→
  32→## 迭代 #1 — 策略名 bug 修复 + Sortino 指标引入
  33→
  34→- **日期**: 2026-06-30 15:53 ~ 16:20 UTC
  35→- **类型**: Bug 修复 + KPI 补全
  36→- **变更摘要**: 修复 `main.py` 中策略名与 `@register_strategy` 注册表不匹配导致 3 个策略被静默跳过的 bug；新增 Sortino Ratio 计算（Constitution L1 首要 KPI）
  37→- **执行时长**: ~27 分钟
  38→- **状态**: passed
  39→- **CodeBuddy 更新数**: ~2252 行日志
  40→- **工具调用数**: ~100+ (Read/Bash/Edit/Grep)
  41→- **团队事件数**: 0
  42→- **权限请求数**: 0 (bypassPermissions)
  43→- **违规检测**: 0 条
  44→
  45→### 变更详情
  46→
  47→**Bug 修复 (P0)**:
  48→- `main.py::_run_reoptimize` 中策略名 `["dual_ma","rsi","macd","bollinger"]` 与注册表 `["dual_ma","rsi_mean_revert","macd_cross","bollinger_band"]` 不匹配，导致 3 个策略被静默跳过
  49→- 提取为模块级常量 `REOPTIMIZE_STRATEGIES` / `REOPTIMIZE_PARAM_GRIDS` 便于回归测试
  50→- `matrix_backtest.py::_run_group` 加 warning 替代静默 `return None`
  51→- `examples/phase5_e2e.py` 同款 bug 修复
  52→
  53→**Sortino 指标 (P1)**:
  54→- 新增 `_compute_sortino()` + `_portfolio_sortino_from_results()`
  55→- `SingleBacktestResult.sortino` / `GroupBacktestResult.portfolio_sortino` 字段
  56→- `strategy_weights.json` 每条目输出 `backtest_sortino`
  57→
  58→**测试新增 (P2)**:
  59→- 10 个新测试：Sortino 单元测试 + 回归测试 + WARNING 测试
  60→- 测试总数：467 → 478 passed (5 failed 是 IBKR live 集成测试，pre-existing)
  61→
  62→**文档更新**:
  63→- `designs/design_v2/CHANGELOG.md` — v2.2 变更记录
  64→- `07-backtest-module.md` / `12-strategy-matrix.md` — Sortino 字段 + 策略名校验
  65→
  66→### 验证结果
  67→```
  68→478 passed, 5 failed (IBKR live, pre-existing)
  69→=== ✅ 全部验证通过 ===
  70→```
  71→
  72→### Constitution 合规
  73→- ✅ 未突破 DD 20% 约束
  74→- ✅ 测试覆盖率提升（+11 测试）
  75→- ✅ 未引入黑箱策略
  76→- ✅ 未引入 RL
  77→- ✅ 文档与代码同步
  78→- ✅ 低风险变更（bug 修复 + 指标补全），符合自动部署条件
  79→
  80→### Experience Learned
  81→
---
{"command": "grep -n \"^## 迭代\" /Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md | tail -10", "description": "Find iteration headers"}
---
Find iteration headers
---
Command: grep -n "^## 迭代" /Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md | tail -10
Stdout: 2:## 迭代 #0 — 读取 mytrader/backtest/runner.py 的代码并用一句话总结它的功能
32:## 迭代 #1 — 策略名 bug 修复 + Sortino 指标引入
95:## 迭代 #2 — NaN 安全 + Portfolio DD + 参数网格扩展
260:## 迭代 #3 — P0 DD 约束 + P1 Walk-Forward 4 轮
370:## 迭代 #4 — Portfolio Backtest 模块 + per-group DD 降级为风险 metadata
474:## 迭代 #5 — Paper Trading Integrity & Parity
617:## 迭代 #6 — 按 iterations/iteration_6/spec.md 进行开发。先读 spec 文件理解完整需求，然后实施 Harness Reliability & Live Test Isolation：隔离默认 live tests、修复 orchestrator pytest 统计/状态判定/快照 untracked 留痕、生成 gate_status.json、补充 harness 测试并同步两份 orchestrator 副本。严格遵守 spec scope；不得修改交易策略、风控阈值或下单逻辑；不得触发真实下单；完成后运行 targeted harness tests 和默认非 live pytest，并更新 trajectory / CODEBUDDY / 必要文档。
706:## 迭代 #7 — SignalRanker Sortino Priority + Benchmark Comparison
848:## 迭代 #8 — Trend-Filtered Mean Reversion 策略 (RSI + 200 SMA)

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"file_path": "/Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md", "limit": 120, "offset": 848}
---
 848→## 迭代 #8 — Trend-Filtered Mean Reversion 策略 (RSI + 200 SMA)
 849→
 850→- **日期**: 2026-07-04 UTC
 851→- **类型**: 策略新增
 852→- **变更摘要**: 新增 `rsi_trend_filter` 策略（RSI 超卖/超买 + 200 日 SMA 趋势过滤），在经典 RSI 均值回归信号上叠加趋势过滤，降低单边趋势中的逆势假信号风险
 853→- **状态**: passed
 854→- **执行时长**: 1 轮对话（手动开发）
 855→- **测试数**: 574 → 585（+5 新测试用例 + 已有参数化测试覆盖新注册）
 856→
 857→### 变更详情
 858→
 859→**P0: 新增 rsi_trend_filter 策略** (`mytrader/strategy/strategies/rsi_trend_filter.py`)
 860→- `rsi_trend_filter_signal(close, rsi_period=14, oversold=30.0, overbought=70.0, trend_period=200)`
 861→- 信号规则：RSI < oversold AND close > SMA(200) → BUY (+1)；RSI > overbought AND close < SMA(200) → SELL (-1)；否则 → HOLD (0)
 862→- 严格 `shift(1)` 防前视偏差，纯函数无副作用
 863→
 864→**P0: 策略注册与参数网格** (`main.py`, `mytrader/strategy/__init__.py`)
 865→- `REOPTIMIZE_STRATEGIES` 新增 `"rsi_trend_filter"`，`REOPTIMIZE_PARAM_GRIDS` 新增 27 个组合（3×3×3×1）
 866→- `trend_period` 固定为 200（经典长周期趋势线，不纳入搜索）
 867→
 868→**P1: 测试** (`tests/test_strategy.py`)
 869→- 新增 `TestRSITrendFilter` 类 5 个测试：信号值域、自定义参数、趋势过滤行为（T3/T4）、数据不足边界
 870→- 更新 `TestStrategyRegistry.test_all_strategies_registered` expected 集合
 871→- 前视偏差和参数化测试自动覆盖新策略
 872→
 873→### 验证结果
 874→
 875→```
 876→Full pytest: 585 passed, 16 deselected, 0 failed, 103 warnings in 15.53s
 877→Targeted tests: tests/test_strategy.py → 54 passed, 0 failed
 878→```
 879→
 880→### Constitution 合规
 881→- ✅ 未突破 DD 20% 约束 | ✅ 测试覆盖率提升 | ✅ 纯函数 + shift(1)
 882→- ✅ 决策可解释 (RSI+SMA) | ✅ 未引入 RL | ✅ 未引入不安全依赖
 883→- ✅ 未修改现有策略/风控/执行逻辑 | ✅ 未触发真实交易
 884→- ✅ 文档与代码同步
 885→
 886→### Experience Learned
 887→- **趋势过滤的自然收敛**：SMA 过滤在趋势市场中不产生反向信号，边界区域短暂交叉是设计意图内的行为
 888→- **参数网格固定 trend_period=200**：避免 81 个组合的无意义规模膨胀
 889→- **与 rsi_mean_revert 互补**：前者无条件，后者趋势过滤，适合 ensemble 混合
 890→- **测试确定性**：T3/T4 用 `np.random.default_rng(42)` 固定种子确保行为稳定
 891→
 892→### 后续建议
 893→1. 下一次 `--reoptimize` 后评估新策略在各组的权重分配
 894→2. 如果实证发现 50/100 SMA 更好，可扩展 `trend_period` 为网格或按组配置
 895→3. 策略多样性约束（5 策略 pool 已成形）
 896→
 897→### L7 流水线状态
 898→```
 899→✅ Backtest (≥5年, rsi_trend_filter 已纳入 REOPTIMIZE_STRATEGIES)
 900→✅ Walk-Forward (4轮, 含新策略)
 901→✅ Portfolio Backtest | ✅ Paper Trading Integrity
 902→✅ Harness Reliability | ✅ SignalRanker Sortino Priority
 903→🔄 Strategy Diversity (迭代 #8 补全 RSI 趋势过滤策略)
 904→⬜ Paper Trade ≥1月 | ⬜ Live
 905→```
 906→
 907→---
 908→
 909→> **Orchestrator 验证记录** (自动追加)
 910→> - 迭代状态: failed
 911→> - 测试: 0 passed, 0 failed
 912→> - 违规: 1 条
 913→> - 高风险文件: 0 个
 914→> - 测试数变化: 574 → 585
 915→> - CodeBuddy 自行更新了 trajectory ✅
 916→
 917→---
 918→
---
 848→## 迭代 #8 — Trend-Filtered Mean Reversion 策略 (RSI + 200 SMA)
 849→
 850→- **日期**: 2026-07-04 UTC
 851→- **类型**: 策略新增
 852→- **变更摘要**: 新增 `rsi_trend_filter` 策略（RSI 超卖/超买 + 200 日 SMA 趋势过滤），在经典 RSI 均值回归信号上叠加趋势过滤，降低单边趋势中的逆势假信号风险
 853→- **状态**: passed
 854→- **执行时长**: 1 轮对话（手动开发）
 855→- **测试数**: 574 → 585（+5 新测试用例 + 已有参数化测试覆盖新注册）
 856→
 857→### 变更详情
 858→
 859→**P0: 新增 rsi_trend_filter 策略** (`mytrader/strategy/strategies/rsi_trend_filter.py`)
 860→- `rsi_trend_filter_signal(close, rsi_period=14, oversold=30.0, overbought=70.0, trend_period=200)`
 861→- 信号规则：RSI < oversold AND close > SMA(200) → BUY (+1)；RSI > overbought AND close < SMA(200) → SELL (-1)；否则 → HOLD (0)
 862→- 严格 `shift(1)` 防前视偏差，纯函数无副作用
 863→
 864→**P0: 策略注册与参数网格** (`main.py`, `mytrader/strategy/__init__.py`)
 865→- `REOPTIMIZE_STRATEGIES` 新增 `"rsi_trend_filter"`，`REOPTIMIZE_PARAM_GRIDS` 新增 27 个组合（3×3×3×1）
 866→- `trend_period` 固定为 200（经典长周期趋势线，不纳入搜索）
 867→
 868→**P1: 测试** (`tests/test_strategy.py`)
 869→- 新增 `TestRSITrendFilter` 类 5 个测试：信号值域、自定义参数、趋势过滤行为（T3/T4）、数据不足边界
 870→- 更新 `TestStrategyRegistry.test_all_strategies_registered` expected 集合
 871→- 前视偏差和参数化测试自动覆盖新策略
 872→
 873→### 验证结果
 874→
 875→```
 876→Full pytest: 585 passed, 16 deselected, 0 failed, 103 warnings in 15.53s
 877→Targeted tests: tests/test_strategy.py → 54 passed, 0 failed
 878→```
 879→
 880→### Constitution 合规
 881→- ✅ 未突破 DD 20% 约束 | ✅ 测试覆盖率提升 | ✅ 纯函数 + shift(1)
 882→- ✅ 决策可解释 (RSI+SMA) | ✅ 未引入 RL | ✅ 未引入不安全依赖
 883→- ✅ 未修改现有策略/风控/执行逻辑 | ✅ 未触发真实交易
 884→- ✅ 文档与代码同步
 885→
 886→### Experience Learned
 887→- **趋势过滤的自然收敛**：SMA 过滤在趋势市场中不产生反向信号，边界区域短暂交叉是设计意图内的行为
 888→- **参数网格固定 trend_period=200**：避免 81 个组合的无意义规模膨胀
 889→- **与 rsi_mean_revert 互补**：前者无条件，后者趋势过滤，适合 ensemble 混合
 890→- **测试确定性**：T3/T4 用 `np.random.default_rng(42)` 固定种子确保行为稳定
 891→
 892→### 后续建议
 893→1. 下一次 `--reoptimize` 后评估新策略在各组的权重分配
 894→2. 如果实证发现 50/100 SMA 更好，可扩展 `trend_period` 为网格或按组配置
 895→3. 策略多样性约束（5 策略 pool 已成形）
 896→
 897→### L7 流水线状态
 898→```
 899→✅ Backtest (≥5年, rsi_trend_filter 已纳入 REOPTIMIZE_STRATEGIES)
 900→✅ Walk-Forward (4轮, 含新策略)
 901→✅ Portfolio Backtest | ✅ Paper Trading Integrity
 902→✅ Harness Reliability | ✅ SignalRanker Sortino Priority
 903→🔄 Strategy Diversity (迭代 #8 补全 RSI 趋势过滤策略)
 904→⬜ Paper Trade ≥1月 | ⬜ Live
 905→```
 906→
 907→---
 908→
 909→> **Orchestrator 验证记录** (自动追加)
 910→> - 迭代状态: failed
 911→> - 测试: 0 passed, 0 failed
 912→> - 违规: 1 条
 913→> - 高风险文件: 0 个
 914→> - 测试数变化: 574 → 585
 915→> - CodeBuddy 自行更新了 trajectory ✅
 916→
 917→---
 918→
---
Good
---
.
---
 Now I have all
---
 the context.
---
 Let me look
---
 at one
---
 more thing - I
---
 want
---
 to understand
---
 the structure
---
 of the Single
---
BacktestResult dataclass
---
 more
---
 clearly
---
, since
---
 the
---
 `
---
candidates
---
` list
---
 has
---
 tuples of
---
 (strategy, params,
---
 results, pso,
---
 pdd). Let me
---
 also look
---
 at how
---
 the data
---
 flows
---
 for
---
 `_
---
combine_daily_returns` mentioned
---
 in spec
---
.

Looking at the spec
---
 more
---
 carefully:
- `_
---
combine_daily_returns(results
---
)` -
---
 this is mentioned
---
 in spec
---
 but doesn
---
't exist as
---
 a standalone
---
 function. Looking
---
 at the code
---
, it should
---
 be `
---
pd.concat(valid
---
, axis=1).
---
mean(axis=1)`
---
 -
---
 which
---
 is what's
---
 used
---
 inside `_portfolio_shar
---
pe_from_results` etc
---
.

Let
---
 me check
---
 the existing
---
 helpers
---
 for
---
 combining
---
 daily returns.
---
 The pattern
---
 is `
---
pd.concat([r.daily
---
_returns for r in results
---
], axis=1).
---
mean(axis=1)
---
`. This
---
 is what's
---
 used to
---
 compute portfolio shar
---
pe,
---
 sortino, and
---
 max_draw
---
down.

Now,
---
 let me complete
---
 task
---
 1 and start the
---
 implementation.


---
Key
---
 implementation
---
 plan
---
:


---
1. Add module
---
-level constant
---
 `MIN_SORTINO_THRESHOLD
---
 = 0.5
---
`
2. Add `_
---
combine
---
_daily_returns(results
---
)`
---
 helper that
---
 returns the
---
 combined daily returns series
---


---
3. Add `_compute
---
_alpha(strategy
---
_daily_returns, spy_daily
---
_returns)` helper
---
 function
---

4. Add `_
---
get_spy_returns(start
---
, end)` method to
---
 Matrix
---
Backtest class
5
---
. Modify `_run_group
---
`:
   - Call
---
 `_get_spy_returns
---
` once at the beginning
---

   - Per
---
-strategy best params:
---
 change from Sharpe to
---
 Alpha
   - Add
---
 Sort
---
ino > 0.
---
5 filter
---

   - Top
---
-K sort
---
 by
---
 Alpha
   - Add
---
 fallback
---
 logic (
---
2
---
-tier:
---
 Sort
---
ino relaxed
---
,
---
 then DD-only fallback
---
)
6
---
. Modify
---
 `_optimize_ensemble_weights
---
` to use Alpha
---


---
7. Add `back
---
test_alpha` field to
---
 `GroupBacktestResult
---
`
8. Add
---
 `backtest_alpha`
---
 to weights
---
 JSON output


---
Let me also examine
---
 what
---
 `_combine
---
_daily_returns` should
---
 be
---
 -
---
 looking
---
 at the existing
---
 `_
---
portfolio_sharpe_from
---
_results`:


---
```python
def _
---
portfolio_sharpe_from
---
_results(results: list[
---
SingleBacktestResult])
---
 -> float:
    valid
---
 = [r.daily_returns
---
 for r in results if
---
 not r.daily_returns.empty
---
]
    if
---
 not valid:
        return
---
 0.0

---
    combined = pd.concat
---
(valid, axis=1
---
).mean(axis=1
---
)
    return _compute
---
_sharpe(combined
---
)
```

So `_
---
combine_daily_returns(results
---
)` should be
---
:
```python
def
---
 _combine_daily_returns(results
---
: list[SingleBack
---
testResult]) -> pd
---
.Series:
    valid =
---
 [r.daily_returns for
---
 r in results if not
---
 r.daily_returns.empty]

---
    if not valid:

---
        return pd.Series(dtype
---
=float)
    return pd
---
.concat(valid, axis=
---
1).mean(axis=
---
1)
```

Now
---
,
---
 regarding
---
 the structure
---
 of the
---
 modification
---
:


---
The existing
---
 candidates
---
 list
---
 is `
---
list
---
[tuple[str, dict
---
, list[SingleBack
---
testResult], float,
---
 float]]` -
---
 (strategy, params,
---
 results, pso,
---
 pdd).


---
According
---
 to spec, after
---
 modification:
```python

---
candidates_with_alpha = []

---
for (strategy, params
---
, results, pso
---
, pdd) in
---
 candidates:
    alpha =
---
 _compute_alpha(
       
---
 _combine_daily_returns(results
---
),
        spy_returns,

---
    )
    candidates_with
---
_alpha.append((strategy,
---
 params, results, p
---
so, pdd,
---
 alpha))
```

So
---
 new
---
 tuple is (strategy,
---
 params, results, p
---
so, pdd,
---
 alpha).

Let
---
 me also note
---
 that the Group
---
BacktestResult `
---
backtest_alpha` needs
---
 to be stored
---
. Looking
---
 at the existing
---
 code:


---
```python
if
---
 best_params is not None
---
 and best_results:
   
---
 group_results.append((strategy
---
, best_params, best
---
_results))
    report.group
---
_results.append(GroupBacktest
---
Result(
        group_id
---
=group_id,
       
---
 strategy=strategy,
       
---
 ...

---
        portfolio_max
---
_drawdown=_portfolio_max
---
_drawdown_from_results(best
---
_results),
    ))
``
---
`

We
---
 need to add `back
---
test_alpha=
---
alpha
---
` to
---
 this.
---
 Let
---
 me track
---
 the best alpha from
---
 the per-strategy loop
---
.

For
---
 the weights
---
 JSON,
---
 the existing
---
 code does
---
:
```python
weights
---
_list.append({
    "
---
strategy": strategy,
   
---
 "params": params,

---
    "weight": round
---
(weight, 4),

---
    "backtest_sh
---
arpe": round(gr
---
.portfolio_sharpe
---
 if gr else 0
---
.0, 4
---
),
    "backtest
---
_sortino": round(gr
---
.portfolio_sortino if
---
 gr else 0.
---
0, 4),

---
    ...
})

---
```

We need to
---
 add `"backtest_alpha
---
": round(gr.backtest
---
_alpha if gr else 
---
0.0, 
---
4),
---
`.

Now let me implement
---
. The
---
 approach
---
:

1. Edit
---
 matrix_backtest.py to
---
 add
---
:
   - `
---
MIN_SORTINO_THRESHOLD`
---
 constant
   - `_
---
combine_daily_returns` helper
---

   - `_compute
---
_alpha` helper
  
---
 - `_get_spy
---
_returns` method in
---
 MatrixBacktest class
---

   - Modify
---
 `_
---
run_group`:
---
 get
---
 spy
---
_returns,
---
 use
---
 alpha for per-strategy
---
 best,
---
 top
---
-k
---
 filter
---
, fallback
---
 logic
---
,
---
 store
---
 back
---
test_alpha
   -
---
 Modify `_optimize_ensemble
---
_weights` to accept spy
---
_returns and use alpha

---
   - Add `back
---
test_alpha` to Group
---
BacktestResult data
---
class
   - Add
---
 `backtest_alpha`
---
 to weights JSON

Wait
---
 -
---
 on
---
 _
---
optimize_ensemble_weights,
---
 I
---
 need to pass
---
 spy_returns.
---
 Looking
---
 at the existing
---
 signature
---
:


---
```python
def _
---
optimize_ensemble_weights(

---
    group_results: list
---
[tuple[str, dict
---
, list[SingleBack
---
testResult]]],
   
---
 conflict_threshold: float =
---
 0.3,

---
) -> list[tuple
---
[str, dict, float
---
]]:
```

I need
---
 to add `spy_returns
---
: pd.Series | None
---
`
---
 parameter
---
.


---
Also looking
---
 at walk
---
_forward's
---
 `_backtest_with_params
---
_on_period` - this
---
 is
---
 called for
---
 walk
---
-forward validation, doesn
---
't call
---
 _optimize_ensemble_weights
---
.
---
 The
---
 walk
---
_forward
---
 flow
---
 calls
---
 `_
---
run_group` to
---
 find
---
 best params, then uses
---
 those
---
 params in val
---
 period.


---
But
---
 `_
---
run_group` calls `_
---
optimize_ensemble_weights`
---
 internally. So changes
---
 to `_run_group`
---
 will
---
 propagate through
---
 walk
---
-forward
---
 too
---
.
---
 Good.

Let
---
 me also think
---
 about edge
---
 cases:
- If
---
 spy
---
_returns is None (SP
---
Y data unavailable), _
---
compute_alpha returns 0
---
.0 for
---
 all candidates.

---
- This
---
 means all candidates have
---
 alpha=0.0
---
, and
---
 the ranking
---
 by alpha would be tied
---
.
- The
---
 spec says "如果
---
 SPY 数据不可用
---
，返回 0.
---
0（降级）
---
" - so all
---
 candidates get
---
 alpha
---
=0.0.


---
But
---
 wait
---
,
---
 if all al
---
phas are 0.
---
0 (
---
t
---
ied), what
---
 should
---
 happen
---
?

---
- If
---
 Sort
---
ino filter
---
 is
---
 applied (
---
Sortino > 0
---
.5), candidates
---
 with Sort
---
ino > 0.
---
5 pass
---

- Among
---
 them
---
, sort by alpha (
---
all 0.0
---
) -
---
 Python
---
's sort is stable,
---
 so original
---
 order is preserved
-
---
 This is acceptable
---
 degradation
---



---
Actually, the
---
 spec says in
---
 the fallback
---
 section
---
 that
---
 we
---
 should keep
---
 using
---
 alpha-based
---
 sort even
---
 when SPY unavailable
---
. The
---
 alpha
---
 will
---
 all
---
 be 0,
---
 so
---
 we
---
'll
---
 preserve
---
 insertion
---
 order (
---
which is strategy
---
 iteration order).


---
Let me think
---
 about one
---
 edge
---
 case: when
---
 SP
---
Y is unavailable and
---
 all
---
 candidates
---
 have alpha=0,
---
 should
---
 we fall
---
 back to Sortino?
---
 The spec says "如果
---
 SPY 数据不可用
---
，返回 0.
---
0（降级）
---
" —
---
 so alpha
---
=
---
0 for
---
 all. This
---
 is acceptable
---
.
---
 We
---
 still
---
 sort by alpha (all
---
 tied
---
 at
---
 0),
---
 preserving
---
 insertion
---
 order.

Actually
---
, re
---
-reading the spec carefully
---
:

---
- Section
---
 4.2:
---
 "Sort
---
ino > 0.
---
5:
---
 最低质量门槛（
---
新增，排除垃圾策略
---
）"
- The
---
 fallback logic has
---
 2
---
 tiers:
  1
---
. DD
---
 ≤ 20% AND
---
 Sortino > 0
---
.5 → Alpha
---
 sort
  2
---
. If
---
 empty
---
 →
---
 DD ≤
---
 20% only
---
 → Alpha sort
 
---
 3. If
---
 still
---
 empty → DD ascending
---
 (existing
---
 logic
---
)

This is good
---
. Let me also
---
 verify
---
:
---
 the existing
---
 test `test_compliant
---
_candidates_selected_by_sortino
---
` checks
---
 that DD
---
-compliant candidates are "
---
selected by Sort
---
ino". After
---
 my changes
---
, they
---
'll
---
 be selected by Alpha
---
. The
---
 test checks
---
 `dd_constrained is
---
 False`,
---
 which should
---
 still pass.


---
The
---
 test `test_fallback
---
_when_no_compliant_candidates
---
` checks that when
---
 DD > 20%,
---
 `
---
dd_constrained=True`.
---
 My
---
 changes preserve
---
 this fallback
---
.


---
But
---
 the
---
 test name `test_com
---
pliant_candidates_selected_by_sort
---
ino` is now
---
 misleading. The
---
 spec doesn
---
't say to rename
---
 tests, just
---
 to add new ones.
---
 Let me leave
---
 existing
---
 tests as-is and
---
 add
---
 new tests
---
 for the alpha
---
 logic
---
.

Actually looking
---
 at the test name:
---
 `test_compliant_candidates
---
_selected_by_sortino`
---
 - this is about
---
 checking
---
 that DD-compliant candidates
---
 pass
---
 through
---
. The test only
---
 checks `dd_constrained
---
 is False`. So it
---
 should
---
 still pass with
---
 my changes.

Wait
---
, I
---
 need to check
---
 one thing
---
:
---
 in
---
 the spec
---
, the Sortino >
---
 0.5 filter
---
 is applied. If
---
 the dual
---
_ma strategy on
---
 the mock
---
 data has
---
 Sortino <
---
 0.5,
---
 it
---
 would be filtered out,
---
 and we
---
'd hit
---
 F
---
allback 1 (
---
relax Sortino).
---
 Let me think
---
 about this...

Actually,
---
 looking at `_
---
make_ohlcv`
---
 with trend="
---
up":
---
 close
---
 = 
---
100 + i*
---
0.1,
---
 which
---
 is a steady
---
 uptrend. dual
---
_ma with
---
 fast=5, slow
---
=20 in
---
 a steady
---
 uptrend should generate BUY
---
 signals and
---
 positive
---
 returns. The Sortino
---
 should be >
---
 0.
---
5 typically
---
.

But
---
 this
---
 is test
---
 data. Let me not
---
 worry about it -
---
 if
---
 the Sort
---
ino is
---
 below
---
 0.5 in
---
 some
---
 test cases
---
, the fallback logic
---
 kicks in and
---
 the test should
---
 still pass.

Actually,
---
 the
---
 test
---
 `test_com
---
pliant_candidates_selected_by_sort
---
ino` checks
---
 `dd_constrained is
---
 False`. With
---
 my changes,
---
 if the
---
 candidates
---
 pass DD
---
 but
---
 fail
---
 Sortino,
---
 the fallback kicks in but
---
 `dd_constrained`
---
 is still False (
---
per spec
---
). So the test should
---
 still pass.

Now
---
 let me also check:
---
 what
---
 about walk
---
_forward integration
---
? It calls `_
---
run_group` for
---
 training.
---
 With
---
 my changes, it
---
 will use alpha-based
---
 selection. The walk
---
_forward test `
---
test_run_walk_forward_mock
---
_integration` should still pass
---
 since it
---
 just
---
 checks structural
---
 properties.

OK, let
---
 me proceed
---
 with implementation.


---
One
---
 more thing - I
---
 should
---
 also
---
 check if
---
 I
---
 need to modify
---
 `_
---
portfolio
---
_sh
---
arpe_from_results`.
---
 Looking
---
 at the spec, no
---
 - we
---
're
---
 adding
---
 alpha
---
 as
---
 an
---
 additional metric, not removing
---
 Sharpe. The Group
---
BacktestResult still
---
 has portfolio
---
_sharpe. The
---
 per
---
-strategy best params changes
---
 from Sharpe to Alpha
---
, but the portfolio
---
_sharpe field is
---
 still computed and
---
 stored in
---
 Group
---
BacktestResult.

Wait
---
 -
---
 the spec section
---
 4.3 says
---
:
```
---
python
if
---
 ps > best_shar
---
pe:  # 用
---
 Sharpe 选
---
 best params
    best
---
_sharpe = ps
---

```

---
bec
---
omes:
```python

---
alpha = _compute_alpha
---
(...)
if alpha > best
---
_alpha:  # 用
---
 Alpha 选 best params

---
    best_alpha = alpha
---

```

But
---
 the existing
---
 code also stores `best
---
_sharpe =
---
 ps` to
---
 be
---
 used in Group
---
BacktestResult.port
---
folio_sharpe.
---
 So I
---
 need to keep
---
 tracking
---
 best
---
_sharpe for
---
 storage
---
 purposes
---
, but use
---
 best
---
_alpha for selection.

Let
---
 me re-read the existing
---
 code:
```python

---
best_params = None

---
best_sharpe =
---
 float("-inf")
best
---
_sortino = 0
---
.0
best_results
---
: list[SingleBack
---
testResult] = []


---
for params in param_comb
---
os:
    # ...
---
 back
---
test ...
    ps
---
 = _portfolio_shar
---
pe_from_results(results)

---
    pso = _
---
portfolio_sortino_from_results
---
(results)

    if ps
---
 > best_sharpe
---
:
        best_sh
---
arpe = ps

---
        best_sortino =
---
 pso
        best
---
_params = params
       
---
 best_results = results

---
```

So `
---
best_sharpe`
---
 is used for
---
:

---
1. Selection (which
---
 we change
---
 to alpha)
2.
---
 Storage
---
 in GroupBacktestResult
---
.portfolio_sharpe
---


After the
---
 change,
---
 I
---
 need to track both
---
:
- `best_alpha
---
` for selection
---

- `best_sh
---
arpe` for storage
---
 (
---
still
---
 computed for
---
 the best alpha
---
's
---
 params)

Actually, the
---
 cleanest approach is:

---
-
---
 Track `best_alpha`
---
 for selection
- When
---
 we find a new
---
 best alpha, also compute
---
 and store the corresponding
---
 shar
---
pe, sortino for
---
 the
---
 GroupBacktestResult


---
Let me code
---
 it
---
 like
---
:

---
```python
best_params
---
 = None
best_alpha
---
 = float("-inf")

---
best_sharpe =
---
 0.0 
---
 # for
---
 storage

---
best_sortino = 
---
0.0  #
---
 for storage
best_results
---
: list[SingleBack
---
testResult] = []


---
for params in param_comb
---
os:
    # ...
---
 backtest ...
    combined
---
 =
---
 _combine
---
_daily_returns(results)
   
---
 ps = _compute
---
_sharpe(combined
---
)
    pso =
---
 _compute_sortino(comb
---
ined)
    alpha
---
 = _compute_alpha(comb
---
ined, spy_returns)


---
    if alpha > best
---
_alpha:
        best_alpha
---
 = alpha
        best
---
_sharpe = ps
---


---
        best_sortino =
---
 pso
        best
---
_params = params
       
---
 best_results = results

---
```

This
---
 way:

---
- Selection
---
 uses alpha
---

- Storage
---
 uses best_sharpe
---
 (computed
---
 at
---
 the best
---
 alpha's params)
-
---
 We
---
 compute
---
 combined
---
 once and
---
 reuse it

Actually
---
, looking
---
 at the existing code more
---
 carefully:
```python

---
ps = _portfolio_sh
---
arpe_from_results(results
---
)
pso = _
---
portfolio_sortino_from_results
---
(results)
```

These
---
 two
---
 functions each
---
 call `pd.concat(valid
---
, axis=1).
---
mean(axis=1)`
---
 internally,
---
 which is wasteful.
---
 With
---
 my `_
---
combine_daily_returns` helper
---
, I can compute once
---
 and reuse.
---
 Let me refactor
---
 to
---
:


---
```python
combined =
---
 _combine_daily_returns(results
---
)
ps = _compute
---
_sharpe(combined
---
)
pso = _
---
compute_sortino(combined
---
)
alpha = _compute
---
_alpha(combined, spy
---
_returns)
```

This
---
 is cleaner
---
 and more efficient.


---
But
---
 wait -
---
 I
---
 shouldn
---
't over
---
-engineer.
---
 The spec doesn
---
't ask for
---
 this refactor. But
---
 it's natural
---
 since
---
 I need
---
 to compute combined
---
 once
---
 for alpha anyway
---
. Let me do
---
 it minim
---
ally.

Actually, looking
---
 at the spec code
---
 samples
---
:
```python
alpha
---
 = _compute_alpha(

---
    _combine_daily_returns
---
(results),
    spy_returns
---
,
)
```

So
---
 the spec does
---
 suggest
---
 computing
---
 `_combine_daily_returns(results
---
)` inline
---
. Let
---
 me follow
---
 the spec style
---
 but
---
 optimize
---
 slightly
---
 by re
---
using the combined series
---
.

OK,
---
 I
---
 think I have a
---
 clear plan. Let me
---
 start
---
 implementing.

One more consideration
---
: the `
---
GroupBacktestResult`
---
 data
---
class needs `
---
backtest_alpha:
---
 float = 0.
---
0`. And
---
 the weights
---
 JSON needs `"
---
backtest_alpha": round
---
(gr.backtest_alpha if
---
 gr else 0.
---
0, 4)`
---
.

Let me also think
---
 about the test
---
 plan
---
.
---
 The spec asks
---
 for 9
---
 tests:
1. test
---
_compute_alpha_basic

---
2. test_compute
---
_alpha_spy_unavailable
---

3. test_top
---
_k_selection_uses_alpha
---

4. test_sort
---
ino_filter_excludes_g
---
arbage
5.
---
 test_dd_filter_still
---
_applies
6.
---
 test_fallback_when_no
---
_sortino_compliant

---
7. test_fallback
---
_when_no_dd_compliant
---

8. test_alpha
---
_field_in_weights_json

---
9. test_per_strategy
---
_best_params_uses_alpha
---


Let
---
 me think
---
 about how to implement
---
 these:


---
1
---
. test_compute_alpha_basic
---
: Construct
---
 strategy
---
 returns and
---
 SP
---
Y returns with
---
 known values, verify alpha
---
 calculation
2. test
---
_compute_alpha_spy_un
---
available: Pass None
---
 as spy_returns, verify
---
 alpha = 0.
---
0
3. test
---
_top_k_selection_uses
---
_alpha: Construct
---
 2 candidates where
---
 A has higher Sortino
---
 but lower alpha than
---
 B.
---
 After
---
 _
---
run_group, B should
---
 be selected (
---
higher alpha). This requires
---
 careful mock
---
 construction
---
.
4. test_sort
---
ino_filter_excludes_g
---
arbage: Construct
---
 candidate with Sortino <
---
 0.5,
---
 verify it's filtered out
---

5. test_dd
---
_filter_still_applies
---
: Construct
---
 candidate with DD > 
---
20%, verify it's
---
 filtered out
6.
---
 test_fallback_when_no
---
_sortino_compliant:
---
 All candidates Sort
---
ino < 0.
---
5, verify fallback triggers
---

7. test_f
---
allback_when_no_dd_com
---
pliant: All candidates DD
---
 > 20%, verify
---
 DD
---
 fallback
8. test
---
_alpha_field_in_weights_json
---
: Run
---
 mb.run with
---
 output_file, verify "
---
backtest_alpha" in
---
 JSON
9. test
---
_per_strategy_best_params_
---
uses_alpha: Construct
---
 2 param
---
 combos where
---
 A has higher Shar
---
pe but lower alpha.
---
 Verify the
---
 selected params is
---
 B
---
.


---
For test 3,
---
 4, 6
---
, 9 -
---
 these
---
 need careful
---
 mock
---
 construction. Let me think
---
 about how to mock
---
 this
---
.

For
---
 test 3 and
---
 9, I need
---
 to control
---
:

---
- Strategy
---
 returns (to
---
 control
---
 alpha and
---
 Sort
---
ino)
- SPY
---
 returns (to control alpha
---
 calculation
---
)

The challenge
---
 is that `_
---
backtest_one` is
---
 called inside `_
---
run_group`, which runs
---
 the actual
---
 strategy on
---
 the data. To
---
 control the
---
 returns, I'd need
---
 to either:
a
---
) Mock `_
---
backtest_one` to
---
 return controlled
---
 SingleBacktestResult objects
---

b) Construct
---
 data that
---
 produces specific returns

Option
---
 (a) is cleaner
---
 for
---
 unit testing. Let me
---
 use `unittest.mock.patch
---
` to mock `_
---
backtest_one`.

Actually
---
, for
---
 simpler
---
 tests of
---
 the selection
---
 logic, I could
---
 test `_
---
compute
---
_alpha` and
---
 `_combine
---
_daily_returns` as
---
 pure
---
 functions,
---
 and test
---
 the selection
---
 logic via
---
 integration with
---
 mocked
---
 `_
---
backtest_one`.

Let
---
 me design
---
 the tests:

For
---
 test 3 (test
---
_top_k_selection_uses
---
_alpha):
- Mock
---
 `_backtest_one`
---
 to return results
---
 with specific daily
---
_returns
- Strategy A
---
: high
---
 Sortino,
---
 low alpha (returns
---
 slightly
---
 positive
---
,
---
 low volatility
---
,
---
 but lower
---
 than SPY)
-
---
 Strategy B: lower
---
 Sortino, high
---
 alpha (returns much
---
 higher than SPY)

---
- SP
---
Y:
---
 steady
---
 moderate
---
 returns
- After _
---
run_group, verify
---
 B is selected over
---
 A

For test 
---
4 (test_sortino
---
_filter_excludes_gar
---
bage):
- Mock
---
 `_backtest_one`
---
 to return results with Sort
---
ino < 0.
---
5 (
---
e
---
.g., near
---
-zero returns with
---
 high downside
---
)
- Verify
---
 the
---
 candidate is filtered out


---
For test 6
---
 (test_fallback_when
---
_no_sortino_compliant
---
):
- All candidates have
---
 Sortino < 0
---
.5
- Verify
---
 fallback (
---
Sortino relaxed
---
) triggers, but
---
 dd_constrained is still
---
 False

Actually
---
, testing
---
 fallback requires
---
 checking log
---
 messages or
---
 internal
---
 state. The
---
 spec doesn
---
't expose
---
 a "
---
sortino_rel
---
axed" flag. Let
---
 me think
---
...

Looking at the spec
---
,
---
 there
---
's no field
---
 for
---
 "sortino_relaxed
---
". The only observable
---
 behavior
---
 is:
- If
---
 Sort
---
ino filter
---
 relaxed
---
: warning
---
 logged
---
, dd
---
_constrained=False,
---
 top
---
-K by
---
 alpha
- If DD
---
 fallback: dd
---
_constrained=True, top
---
-K by DD ascending
---


For
---
 test 6, I
---
 can verify:

---
- All
---
 candidates have Sortino <
---
 0.5

---
- Some
---
 candidates
---
 have DD ≤
---
 20%
- After
---
 run
---
, weights
---
 are produced (not empty
---
)
- dd_constrained
---
 is False (
---
because DD
---
 filter
---
 passed)
- The
---
 weights
---
 contain
---
 the candidates
---
 (
---
just
---
 Sort
---
ino filter
---
 relaxed)

For
---
 test 7, I
---
 can verify
---
:
- All candidates have
---
 DD > 20%

---
- dd
---
_constrained is True

---
- We
---
ights still produced (
---
fallback)


---
Let
---
 me start
---
 implementing now
---
.


---
Actually, for
---
 test 3
---
 and
---
 9, I realize
---
 it
---
 might
---
 be complex
---
 to mock
---
 `_
---
backtest_one` since
---
 it's
---
 called inside a
---
 loop. Let me think
---
 about
---
 a simpler approach:


---
For test 3:
---
 I can construct
---
 data that
---
 naturally
---
 produces different alpha
---
/Sortino for two
---
 strategies. But this is
---
 hard to control precisely.


---
Alternative
---
: I can directly
---
 test the
---
 selection logic by extracting
---
 it
---
 into a test
---
able function. But that
---
's ref
---
actoring beyond
---
 spec
---
 scope.

Best
---
 approach: Mock
---
 `_backtest_one`
---
 to return controlled results.
---
 Let me use `patch
---
`
---
 context
---
 manager.

Actually, looking
---
 at the existing test `
---
test_fallback_when_no
---
_compliant_candidates`, it
---
 constructs data
---
 that naturally produces high
---
 DD.
---
 This is the
---
 pattern
---
 used in the code
---
base.

For test 
---
3, I can
---
:

---
-
---
 Use two
---
 strategies with
---
 different characteristics
---

- Construct
---
 data where
---
 one strategy (
---
dual
---
_ma in
---
 uptrend) has
---
 high Sort
---
ino but moderate
---
 alpha
- Construct data
---
 where another strategy
---
 has lower Sort
---
ino but higher
---
 alpha


---
But this is tricky
---
 because
---
 I
---
'd
---
 need to control SP
---
Y data
---
 separately
---
.

Let me use
---
 a hybrid
---
 approach:
---
 mock `_backtest_one
---
` for
---
 precise
---
 control,
---
 and use real
---
 data for integration
---
 tests.

Actually, the
---
 simplest approach for
---
 test 3:

---
- Mock
---
 `_backtest_one`
---
 to return results
---
 with specific daily_returns

---
- Control
---
 SP
---
Y via
---
 mock
---
_store
---
.get_bars_multi

---
- Verify
---
 the selected
---
 strategy is the
---
 one with higher alpha


---
Let me draft
---
 the test:

```python
---

def test_top_k
---
_selection_uses_alpha(self
---
, tmp
---
_path):
    """top
---
-K 
---
排序使用 Alpha 
---
而非 Sortino
---
。

---
    
    场景
---
：策略
---
 A 的
---
 Sortino 高于
---
 B，但 B
---
 的 Alpha
---
 高于 A。
   
---
 应
---
选择 B 
---
而非 A。

---
    """
    from
---
 unittest
---
.mock import patch
    

---
    # SP
---
Y 数据
---
：温和上涨（
---
年化 ~
---
10
---
%）
    spy
---
_idx = pd.date_range
---
("2021-01
---
-01", periods=
---
300, freq
---
="B")
    spy
---
_close = [
---
100.0 *
---
 (1 + 
---
0.000
---
4)
---
 ** i for i in
---
 range(300)] 
---
 # ~10% annual
---
ized
---

    spy_df =
---
 pd.DataFrame({
        "
---
open": [
---
c - 0.
---
1
---
 for c in spy_close
---
],
        "high":
---
 [c + 0
---
.5 for c in
---
 spy_close],
        "
---
low": [c -
---
 0.5 for
---
 c in spy_close],

---
        "close": spy
---
_close,
        "volume
---
": [1_000
---
_000] * 
---
300,
    }, index
---
=spy_idx)
    

---
    #
---
 策略 A
---
 的
---
 returns
---
：高 Sortino（
---
低下行
---
波动），但 alpha 低
---
（收益
---
接近 SPY）
   
---
 #
---
 年
---
化 ~10%，
---
接近
---
 SPY →
---
 alpha 
---
≈ 0
   
---
 np.random.seed(42
---
)
    returns
---
_a = pd.Series(np
---
.random.normal(0.
---
0004, 0
---
.003, 
---
300), index=spy
---
_idx)
    
    #
---
 策略 B
---
 的 returns：较低
---
 Sortino（更高
---
波动
---
），但 alpha 高（
---
收益
---
远超
---
 SPY）
    #
---
 年化 ~30
---
%，
---
alpha ≈ 20
---
%
    returns
---
_b = pd.Series(np
---
.random.normal(0.
---
0011, 0
---
.008, 
---
300), index=spy
---
_idx)
    
    #
---
 
---
验证前提
---
：A 的 Sortino
---
 > B 的 Sortino
---

    from
---
 mytrader.backtest
---
.matrix_backtest import _
---
compute_sortino, _
---
compute_alpha
    spy
---
_returns = spy
---
_df["close"].p
---
ct_change().dropna
---
()
    sort
---
ino_a = _compute
---
_sortino(returns_a
---
)
    sortino_b
---
 = _compute_sortino
---
(returns_b)
   
---
 alpha_a = _compute
---
_alpha(returns_a,
---
 spy_returns)
    alpha
---
_b = _compute_alpha
---
(returns_b, spy
---
_returns)
    
    #
---
 
---
确认测试
---
前提
    assert sort
---
ino_a > sortino
---
_b, "A
---
 的
---
 Sortino 应高于
---
 B"
    assert alpha
---
_b > alpha
---
_a, "B
---
 的 alpha 应高于 A
---
"
    
    # Mock
---
 _
---
backtest_one to return
---
 controlled results
    def
---
 mock_backtest_one(df
---
, strategy, params,
---
 *args, **kwargs
---
):
        sym
---
 = df.index.name or
---
 "SYM
---
"
        if strategy ==
---
 "dual_ma":
           
---
 return Single
---
BacktestResult(sym
---
, strategy
---
, params, 1
---
.0, 10
---
.
---
0, 5.
---
0, 55
---
.0, 10
---
, returns_a)

---
        else:
            return
---
 SingleBacktestResult(sym
---
, strategy, params,
---
 1
---
.0
---
, 30
---
.0, 8
---
.0, 50
---
.0, 10
---
, returns_b)
    

---
    store
---
 = MagicMock()
    def
---
 get_bars_multi(s
---
ymbols, start, end
---
, timeframe="1d
---
"):
        mapping
---
 = {"AAPL":
---
 _make_ohlcv
---
(300, "up
---
"), "SPY":
---
 spy_df}
       
---
 return {s: mapping
---
[s] for s in
---
 symbols if s in mapping
---
}
   
---
 store.get_bars_multi
---
.side_effect = get
---
_bars_multi
    
   
---
 universe = MagicMock()
   
---
 universe.get_groups.return_value
---
 = {"test_group":
---
 ["AAPL"]}
    

---
    mb
---
 = MatrixBacktest(store
---
=store, universe=
---
universe, years=
---
1, top_k=
---
1)
    
    with
---
 patch("
---
mytrader.backtest
---
.matrix_backtest._back
---
test_one", side_effect
---
=mock_backtest_one
---
):
        report
---
 = mb.run(
           
---
 strategies=["dual_ma",
---
 "rsi_mean_re
---
vert"],
            param_gr
---
ids={

---
                "dual_ma":
---
 {"fast": [5
---
], "slow": [
---
20]},
                "rs
---
i_mean_revert":
---
 {"period": [14
---
], "oversold":
---
 [30], "over
---
bought": [70
---
]},
            },
        )

---
    
    # 验
---
证：选择了
---
 r
---
si_mean
---
_revert（高
---
 alpha）而非 dual
---
_ma（高
---
 Sortino）
    weights
---
 = report.groups
---
["test_group"]
   
---
 assert len(weights) ==
---
 1
    assert
---
 weights[0]["strategy
---
"] == "rs
---
i_mean_revert",
---
 (
        f"应
---
选择
---
高
---
 alpha 的 r
---
si_mean_revert，
---
实际选择了
---
 {weights[0]['
---
strategy']}"
    )

---
```

Hmm
---
, but
---
 this might
---
 not work because
---
:
1. The daily
---
_returns series needs to have
---
 the same index as the
---
 actual
---
 data
2. _
---
backtest_one is
---
 called with df, and
---
 the mock needs
---
 to return results
---
 that
---
 align
---



---
Let me simplify
---
 - I'll make
---
 the daily
---
_returns have
---
 the same index as the
---
 input df.

Actually,
---
 let me think about this
---
 differently. The key
---
 insight is:

---
- `_
---
back
---
test_one` returns `
---
SingleBacktestResult`
---
 which
---
 contains `daily_returns`

---
- `_
---
combine_daily_returns(results
---
)` extracts
---
 and
---
 combines these
---

- `_compute
---
_alpha(comb
---
ined, spy_returns)`
---
 computes alpha
---


So as
---
 long as the
---
 daily
---
_returns from
---
 my
---
 mock have
---
 dates
---
 that overlap with SP
---
Y returns
---
, the alpha calculation
---
 will work.

Let me
---
 adjust
---
:
---
 use
---
 the spy
---
_idx
---
 for
---
 both returns
---
_a
---
 and returns
---
_b.
---
 That
---
 way they align
---
 with SPY.

OK
---
, I
---
 think this
---
 approach will
---
 work. Let me now
---
 write
---
 the implementation
---
.

Let
---
 me also consider
---
: should
---
 I make
---
 `_get
---
_spy_returns` a
---
 method or
---
 a function
---
? The spec says "
---
在 Matrix
---
Backtest 类中新增
---
".
---
 So it should
---
 be a method.
---
 And
---
 `_compute_alpha` and
---
 `_combine_daily_returns`
---
 should be module
---
-level functions (
---
like
---
 `_compute
---
_sharpe`,
---
 `_compute_sortino`
---
).

Now
---
 let me think
---
 about the flow
---
 in `_run_group`
---
:

```
---
python
def _run
---
_group(self, ...
---
):
    # 1
---
. Read
---
 group
---
 data
    data =
---
 self._store.get_b
---
ars_multi(symbols,
---
 start, end)
    

---
    # NEW
---
: Get SPY returns
---
 for alpha
---
 calculation
    spy_returns
---
 = self._get_s
---
py_returns(start, end
---
)
    
    # 
---
2. Per-strategy
---
:
---
 find best params (
---
by alpha)
    for
---
 strategy in strategies:
       
---
 for params in param_comb
---
os:
            results
---
 = [...
---
]
            combined
---
 = _combine_daily_returns
---
(results)
            ps
---
 = _compute_shar
---
pe(combined)
           
---
 pso = _compute
---
_sortino(combined)

---
            alpha = _compute
---
_alpha(combined, spy
---
_returns)
            
            if
---
 alpha > best_alpha:

---
                best_alpha
---
 = alpha
                best
---
_sharpe = ps
---


---
                best_sortino =
---
 pso
                best
---
_params = params
               
---
 best_results = results
        

---
        if
---
 best_params is not None
---
 and
---
 best_results:
            group
---
_results.append((strategy,
---
 best_params, best_results
---
))
            report.group_results
---
.append(GroupBacktestResult
---
(
                ...

---
                back
---
test_alpha=best_alpha
---
,
            ))
    
   
---
 # 3. Top
---
-K selection: DD filter
---
 + Sortino filter
---
 + Alpha
---
 sort
    candidates =
---
 [(s
---
, p, r
---
, pso, p
---
dd, alpha) for
---
 ...]
    
    #
---
 Tier 1: DD
---
 ≤ 20% AND
---
 Sortino > 0
---
.5
    compliant
---
 = [c for c
---
 in candidates if c[
---
4] <= 
---
20.
---
0 and c[3
---
] > 0.
---
5]
    if compliant
---
:
        ranked = sorted
---
(compliant, key=lambda
---
 x: x[5
---
], reverse=True)

---
        dd_constrained =
---
 False
    else:

---
        # Tier
---
 2: DD ≤
---
 20% only (
---
relax Sortino)

---
        dd_compliant =
---
 [c for c in
---
 candidates if c[4
---
] <= 20.
---
0]
        if dd
---
_compliant:
            ranked
---
 = sorted(dd_compliant
---
, key=lambda x:
---
 x[5], reverse
---
=True)
            dd_con
---
strained = False
           
---
 logger.warning(...)

---
        else:
            #
---
 Tier 3: DD
---
 fallback

---
            ranked = sorted(c
---
andidates, key=lambda x
---
: x[4])

---
            dd_constrained =
---
 True

---
            logger.warning(...)
    

---
    top_results = ranked
---
[:self
---
._top_k]
    

---
    # 4.
---
 Ensemble weights (
---
by alpha)
    weighted
---
 = _optimize_ensemble
---
_weights(

---
        [(s, p
---
, r) for (
---
s, p, r
---
, _, _,
---
 _) in top_results],

---
        spy_returns=
---
spy_returns,
    )

---
    
    # 5
---
. Build weights list

---
    ...

---
```

This
---
 looks right
---
. Let me also update
---
 `_optimize_ensemble_weights
---
` to
---
 accept spy
---
_returns.


---
Now let me also think
---
 about the `
---
back
---
test_alpha` in
---
 Group
---
BacktestResult. I
---
 need to store the alpha
---
 of
---
 the best params
---
 for each strategy. This
---
 is `
---
best_alpha` from the
---
 per-strategy loop.


---
But
---
 wait - there
---
's a subtlety
---
. The `report
---
.group_results` contains
---
 ALL strategies (
---
not
---
 just top
---
-K). Each
---
 strategy
---
's
---
 `
---
back
---
test_alpha` is the
---
 alpha of its best params
---
. This
---
 is correct.

For the
---
 weights JSON, the `
---
backtest_alpha` should
---
 be
---
 the alpha of the selected
---
 strategy (
---
from top
---
_results
---
). Looking
---
 at the existing
---
 code:

```python

---
for strategy
---
, params, weight in
---
 weighted:
    gr =
---
 next(
        (r
---
 for r in report.group
---
_results
         if r
---
.group_id == group_id
---
 and r.strategy == strategy
---
),
        None,
   
---
 )
    weights_list.append
---
({
        "strategy":
---
 strategy,
        ...

---
        "backtest_sh
---
arpe": round(gr
---
.portfolio_sharpe
---
 if gr else 0
---
.0, 4
---
),
        ...
    })

---
```

So it
---
 looks
---
 up the
---
 GroupBacktestResult by
---
 strategy name
---
. Since
---
 I'm adding `back
---
test_alpha` to Group
---
BacktestResult, I
---
 can do
---
:


---
```python
"back
---
test_alpha": round(gr
---
.backtest_alpha if gr
---
 else 0.0
---
, 4),
``
---
`

Good
---
.

Now,
---
 let
---
 me also think about the
---
 Sort
---
ino threshold
---
. The spec says `
---
Sortino > 0
---
.5` (strict
---
ly greater).
---
 Let
---
 me use
---
 `>
---
 MIN
---
_SORTINO_THRESHOLD` where
---
 `MIN_SORTINO_THRESHOLD
---
 = 0.5
---
`.

Alright
---
, let me start
---
 implementing. I'll mark
---
 task 1 as complete
---
 and move
---
 to task 2.
---
我已经掌握了
---
完整
---
上下
---
文。让我将
---
任务 1 
---
标记为完成
---
，并开始实现。
---
{"status": "completed", "taskId": "1"}
---
Updated task #1 status
---
Updated task #1 status
---
{"status": "in_progress", "taskId": "2"}
---
Updated task #2 status
---
Updated task #2 status
---
现在
---
让我来实现
---
这些
---
更改。首先，我将
---
添加常量和
---
辅助函数，
---
然后修改 `_run_group
---
` 和
---
 `_optimize_ensemble_weights
---
`：
---
{"file_path": "/Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py", "new_string": "# Constitution L1 硬约束：portfolio 最大回撤 ≤ 20%\n# _run_group 在 top-K 选择时按此阈值过滤合规候选（迭代 #3 新增）\nMAX_PORTFOLIO_DRAWDOWN_PCT: float = 20.0\n\n# Constitution L7 Walk-Forward 门槛：单轮验证期 portfolio DD ≤ 15%\n# （低于 L1 的 20% 线，给样本外留缓冲）\nWALK_FORWARD_VAL_DD_THRESHOLD: float = 15.0\n\n# 迭代 #9 新增：Sortino 最低质量门槛，用于 top-K 选择时的二级过滤\n# 排除 Sortino ≤ 0.5 的\"垃圾\"策略（即使 alpha 高也不选）\n# 设计动机：alpha 排序选出高绝对收益策略，但需 Sortino 门槛保证基本下行质量\n# fallback：若无候选通过此门槛，放宽过滤（仅保留 DD 硬约束）\nMIN_SORTINO_THRESHOLD: float = 0.5", "old_string": "# Constitution L1 硬约束：portfolio 最大回撤 ≤ 20%\n# _run_group 在 top-K 选择时按此阈值过滤合规候选（迭代 #3 新增）\nMAX_PORTFOLIO_DRAWDOWN_PCT: float = 20.0\n\n# Constitution L7 Walk-Forward 门槛：单轮验证期 portfolio DD ≤ 15%\n# （低于 L1 的 20% 线，给样本外留缓冲）\nWALK_FORWARD_VAL_DD_THRESHOLD: float = 15.0", "replace_all": false}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py
---
现在
---
，
---
在
---
 `GroupBacktestResult
---
` 中添加 `back
---
test_alpha` 字段
---
：
---
{"file_path": "/Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py", "new_string": "@dataclass\nclass GroupBacktestResult:\n    \"\"\"单组策略回测结果。\"\"\"\n\n    group_id: str\n    strategy: str\n    params: dict\n    portfolio_sharpe: float          # 等权组合 Sharpe（而非算术平均）\n    avg_total_return_pct: float\n    avg_max_drawdown_pct: float\n    avg_win_rate_pct: float\n    symbol_count: int\n    portfolio_sortino: float = 0.0          # 等权组合 Sortino（迭代 #1 新增）\n    portfolio_max_drawdown: float = 0.0     # 等权组合最大回撤（迭代 #2 新增，Constitution L1 KPI）\n    dd_constrained: bool = False            # 迭代 #3：该组是否用了 DD fallback（无合规候选）\n    backtest_alpha: float = 0.0              # 迭代 #9：alpha vs SPY（百分数），用于排序策略选择", "old_string": "@dataclass\nclass GroupBacktestResult:\n    \"\"\"单组策略回测结果。\"\"\"\n\n    group_id: str\n    strategy: str\n    params: dict\n    portfolio_sharpe: float          # 等权组合 Sharpe（而非算术平均）\n    avg_total_return_pct: float\n    avg_max_drawdown_pct: float\n    avg_win_rate_pct: float\n    symbol_count: int\n    portfolio_sortino: float = 0.0          # 等权组合 Sortino（迭代 #1 新增）\n    portfolio_max_drawdown: float = 0.0     # 等权组合最大回撤（迭代 #2 新增，Constitution L1 KPI）\n    dd_constrained: bool = False            # 迭代 #3：该组是否用了 DD fallback（无合规候选）", "replace_all": false}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py
---
现在
---
，
---
在 `_compute_sortino
---
` 之后添加 `_
---
combine_daily_returns` 和
---
 `_compute_alpha` 
---
辅助函数：
---
{"file_path": "/Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py", "new_string": "def _compute_sortino(\n    returns: pd.Series,\n    periods_per_year: int = 252,\n    target: float = 0.0,\n) -> float:\n    \"\"\"从日收益率序列计算年化 Sortino Ratio（Constitution L1 首要 KPI）。\n\n    Sortino = (mean(returns) - target) / downside_deviation * sqrt(periods_per_year)\n    downside_deviation = sqrt( mean( min(0, returns - target)^2 ) )\n\n    与 Sharpe 的区别：仅对下行波动惩罚，上行波动不计入分母。\n    适合\"收益>0 但偶尔大跌\"的中长线策略评估。\n\n    退化处理（与 _compute_sharpe 一致）：\n        - 样本 < 5 → 0.0\n        - 下行波动 ≤ 0（无下行样本）→ 0.0（理论为 +inf，返回 0 保持保守 + 可算术聚合）\n\n    Args:\n        returns:          日收益率序列（如 pf.returns()）\n        periods_per_year: 年化因子（日线 = 252）\n        target:           MAR/目标收益率，默认 0（与 _compute_sharpe 无风险利率假设一致）\n\n    Returns:\n        年化 Sortino Ratio\n    \"\"\"\n    returns = returns.dropna()\n    if len(returns) < 5:\n        return 0.0\n    excess = returns - target\n    downside = excess.where(excess < 0, 0.0)        # 仅保留负偏离，正偏离置 0\n    dd = np.sqrt((downside ** 2).mean())\n    if dd <= 0 or np.isnan(dd):\n        return 0.0\n    return float(returns.mean() / dd * np.sqrt(periods_per_year))\n\n\ndef _combine_daily_returns(results: list[SingleBacktestResult]) -> pd.Series:\n    \"\"\"等权合并组内日收益率序列，返回组合日收益率（迭代 #9 新增）。\n\n    与 _portfolio_sharpe_from_results / _portfolio_sortino_from_results 同语义：\n    将所有标的日收益率等权合并为组合序列。提取为独立函数以便 alpha 计算\n    和 per-strategy best params 选择复用，避免重复 pd.concat。\n\n    Args:\n        results: 单策略多标的的回测结果列表\n\n    Returns:\n        组合日收益率 pd.Series；无有效数据时返回空 Series\n    \"\"\"\n    valid = [r.daily_returns for r in results if not r.daily_returns.empty]\n    if not valid:\n        return pd.Series(dtype=float)\n    return pd.concat(valid, axis=1).mean(axis=1)\n\n\ndef _compute_alpha(\n    strategy_daily_returns: pd.Series,\n    spy_daily_returns: pd.Series | None,\n    periods_per_year: int = 252,\n) -> float:\n    \"\"\"计算 alpha = 策略年化收益 - SPY 年化收益（迭代 #9 新增）。\n\n    Alpha 衡量策略相对 SPY buy-and-hold 的超额收益。正值表示跑赢 SPY，\n    负值表示跑输 SPY。用于 top-K 策略选择和 per-strategy best params 选择，\n    替代之前基于 Sortino/Sharpe 的选择逻辑（参考 iteration #9 spec）。\n\n    年化公式：(1 + mean_daily) ** periods_per_year - 1\n    使用算术平均日收益的几何年化，与 PortfolioBacktester 同口径。\n\n    降级处理：SPY 数据不可用（None 或空）→ 返回 0.0（不抛异常）。\n    这样在 SPY 数据缺失时，alpha 排序退化为\"原顺序\"，不会阻塞回测。\n\n    Args:\n        strategy_daily_returns: 策略组合日收益率序列\n        spy_daily_returns:      SPY 日收益率序列；None 表示数据不可用\n        periods_per_year:       年化因子（日线 = 252）\n\n    Returns:\n        Alpha 百分数（如 5.23 表示策略年化收益跑赢 SPY 5.23 个百分点）；\n        SPY 不可用时返回 0.0\n    \"\"\"\n    if spy_daily_returns is None or spy_daily_returns.empty:\n        return 0.0\n    if strategy_daily_returns is None or strategy_daily_returns.empty:\n        return 0.0\n\n    # 对齐时间索引（inner join 取交集）\n    aligned = pd.concat(\n        [strategy_daily_returns.rename(\"strat\"), spy_daily_returns.rename(\"spy\")],\n        axis=1,\n        join=\"inner\",\n    ).dropna()\n    if aligned.empty or len(aligned) < 2:\n        return 0.0\n\n    strat_returns = aligned[\"strat\"]\n    spy_returns = aligned[\"spy\"]\n\n    # 年化收益 = (1 + mean_daily)^252 - 1\n    strat_mean = strat_returns.mean()\n    spy_mean = spy_returns.mean()\n    if not np.isfinite(strat_mean) or not np.isfinite(spy_mean):\n        return 0.0\n\n    strat_annual = (1.0 + strat_mean) ** periods_per_year - 1.0\n    spy_annual = (1.0 + spy_mean) ** periods_per_year - 1.0\n\n    alpha = (strat_annual - spy_annual) * 100.0  # 转为百分数\n    if not np.isfinite(alpha):\n        return 0.0\n    return float(alpha)", "old_string": "def _compute_sortino(\n    returns: pd.Series,\n    periods_per_year: int = 252,\n    target: float = 0.0,\n) -> float:\n    \"\"\"从日收益率序列计算年化 Sortino Ratio（Constitution L1 首要 KPI）。\n\n    Sortino = (mean(returns) - target) / downside_deviation * sqrt(periods_per_year)\n    downside_deviation = sqrt( mean( min(0, returns - target)^2 ) )\n\n    与 Sharpe 的区别：仅对下行波动惩罚，上行波动不计入分母。\n    适合\"收益>0 但偶尔大跌\"的中长线策略评估。\n\n    退化处理（与 _compute_sharpe 一致）：\n        - 样本 < 5 → 0.0\n        - 下行波动 ≤ 0（无下行样本）→ 0.0（理论为 +inf，返回 0 保持保守 + 可算术聚合）\n\n    Args:\n        returns:          日收益率序列（如 pf.returns()）\n        periods_per_year: 年化因子（日线 = 252）\n        target:           MAR/目标收益率，默认 0（与 _compute_sharpe 无风险利率假设一致）\n\n    Returns:\n        年化 Sortino Ratio\n    \"\"\"\n    returns = returns.dropna()\n    if len(returns) < 5:\n        return 0.0\n    excess = returns - target\n    downside = excess.where(excess < 0, 0.0)        # 仅保留负偏离，正偏离置 0\n    dd = np.sqrt((downside ** 2).mean())\n    if dd <= 0 or np.isnan(dd):\n        return 0.0\n    return float(returns.mean() / dd * np.sqrt(periods_per_year))", "replace_all": false}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py
---
现在
---
更新
---
 `_optimize_ensemble_weights
---
` 以使用 Alpha
---
：
---
{"file_path": "/Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py", "new_string": "def _optimize_ensemble_weights(\n    group_results: list[tuple[str, dict, list[SingleBacktestResult]]],\n    spy_returns: pd.Series | None = None,\n    conflict_threshold: float = 0.3,\n) -> list[tuple[str, dict, float]]:\n    \"\"\"在\"单点离散值加权投票\"语义下优化 ensemble 权重。\n\n    实盘每根 bar 各策略产出离散值（1/-1/0），加权投票决定方向。\n    回测的权重优化必须使用相同语义，而非对整段时间序列做加权。\n\n    迭代 #9：权重计算从 Sharpe 改为 Alpha（vs SPY）。\n    动机：与 _run_group 的 top-K 排序口径一致，使 ensemble 权重直接\n    反映\"跑赢 SPY 的程度\"。SPY 不可用时 alpha=0，退化为等权。\n\n    Args:\n        group_results: [(strategy, params, [SingleBacktestResult]), ...]\n        spy_returns:   SPY 日收益率序列（用于 alpha 计算）；None 时退化为等权\n        conflict_threshold: 加权投票分数绝对值低于此时视为 HOLD\n\n    Returns:\n        [(strategy, params, weight), ...] 归一化权重列表\n    \"\"\"\n    if len(group_results) == 1:\n        strategy, params, _ = group_results[0]\n        return [(strategy, params, 1.0)]\n\n    # 迭代 #9：用各策略的组合 alpha 归一化为权重（替代 Sharpe）\n    # alpha 可能 < 0（跑输 SPY），用 max(alpha, 0.01) 避免负权重\n    alphas = []\n    for strategy, params, results in group_results:\n        combined = _combine_daily_returns(results)\n        alpha = _compute_alpha(combined, spy_returns)\n        alphas.append(max(alpha, 0.01))  # 避免负/零权重\n\n    total = sum(alphas)\n    weights = [a / total for a in alphas]\n\n    return [\n        (strategy, params, weight)\n        for (strategy, params, _), weight in zip(group_results, weights)\n    ]", "old_string": "def _optimize_ensemble_weights(\n    group_results: list[tuple[str, dict, list[SingleBacktestResult]]],\n    conflict_threshold: float = 0.3,\n) -> list[tuple[str, dict, float]]:\n    \"\"\"在\"单点离散值加权投票\"语义下优化 ensemble 权重。\n\n    实盘每根 bar 各策略产出离散值（1/-1/0），加权投票决定方向。\n    回测的权重优化必须使用相同语义，而非对整段时间序列做加权。\n\n    Args:\n        group_results: [(strategy, params, [SingleBacktestResult]), ...]\n        conflict_threshold: 加权投票分数绝对值低于此时视为 HOLD\n\n    Returns:\n        [(strategy, params, weight), ...] 归一化权重列表\n    \"\"\"\n    if len(group_results) == 1:\n        strategy, params, _ = group_results[0]\n        return [(strategy, params, 1.0)]\n\n    # 简化的 ensemble 权重搜索：用各策略的组合 Sharpe 归一化为权重\n    # 更严格的做法是网格搜索 weight 组合，在离散投票序列上跑回测\n    sharpes = []\n    for strategy, params, results in group_results:\n        ps = _portfolio_sharpe_from_results(results)\n        sharpes.append(max(ps, 0.01))  # 避免负权重\n\n    total = sum(sharpes)\n    weights = [s / total for s in sharpes]\n\n    return [\n        (strategy, params, weight)\n        for (strategy, params, _), weight in zip(group_results, weights)\n    ]", "replace_all": false}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py
---
{"status": "completed", "taskId": "2"}
---
Updated task #2 status
---
Updated task #2 status
---
{"status": "in_progress", "taskId": "3"}
---
Updated task #3 status
---
Updated task #3 status
---
现在
---
，在 `MatrixBack
---
test` 类中添加
---
 `_get_spy_returns
---
` 方法，
---
并修改 `_run_group
---
`。让我先读取
---
该
---
部分的
---
当前状态：
---
{"file_path": "/Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py", "limit": 100, "offset": 700}
---
 700→        f"[WalkForward] done: {len(wf_rounds)} rounds, "
 701→        f"pass_all_rounds={report.pass_all_rounds}, "
 702→        f"max_val_dd={report.max_val_dd:.4f}%"
 703→    )
 704→    return report
 705→
 706→
 707→# ---------------------------------------------------------------------------
 708→# MatrixBacktest 主类
 709→# ---------------------------------------------------------------------------
 710→
 711→class MatrixBacktest:
 712→    """矩阵回测：N 策略 × G 标的组 × 参数网格 → strategy_weights.json。
 713→
 714→    Args:
 715→        store:       MarketDataStore（本地时序库）
 716→        universe:    UniverseManager（提供分组映射）
 717→        years:       回测窗口（默认 5 年）
 718→        init_cash:   初始资金
 719→        fees:        手续费率
 720→        slippage:    滑点率
 721→        top_k:       每组保留 Top-K 策略（默认 2）
 722→    """
 723→
 724→    def __init__(
 725→        self,
 726→        store: MarketDataStore,
 727→        universe: UniverseManager,
 728→        years: int = 5,
 729→        init_cash: float = 100_000.0,
 730→        fees: float = 0.001,
 731→        slippage: float = 0.001,
 732→        top_k: int = 2,
 733→    ) -> None:
 734→        self._store = store
 735→        self._universe = universe
 736→        self._years = years
 737→        self._init_cash = init_cash
 738→        self._fees = fees
 739→        self._slippage = slippage
 740→        self._top_k = top_k
 741→
 742→    def run(
 743→        self,
 744→        strategies: list[str],
 745→        param_grids: dict[str, dict[str, list]],
 746→        output_file: str | Path | None = None,
 747→    ) -> MatrixBacktestReport:
 748→        """执行完整矩阵回测。
 749→
 750→        Args:
 751→            strategies:  策略名称列表，如 ["dual_ma", "rsi"]
 752→            param_grids: 各策略参数网格，如 {"dual_ma": {"fast":[5,10], "slow":[20,30]}}
 753→            output_file: strategy_weights.json 输出路径（None 则不写文件）
 754→
 755→        Returns:
 756→            MatrixBacktestReport
 757→        """
 758→        today = date.today()
 759→        start = today - timedelta(days=self._years * 365)
 760→        window_str = f"{start.isoformat()} ~ {today.isoformat()}"
 761→
 762→        logger.info(
 763→            f"[MatrixBacktest] start={start}, end={today}, "
 764→            f"strategies={strategies}, years={self._years}"
 765→        )
 766→
 767→        # 获取分组（⚠️ 使用历史时点分组，而非当前静态分组）
 768→        # Phase 5 初期简化：用当前分组，但接口已预留历史分组能力
 769→        groups = self._universe.get_groups()
 770→        if not groups:
 771→            logger.warning("[MatrixBacktest] no groups available, abort")
 772→            return MatrixBacktestReport(
 773→                generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
 774→                backtest_window=window_str,
 775→                groups={},
 776→            )
 777→
 778→        report = MatrixBacktestReport(
 779→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
 780→            backtest_window=window_str,
 781→            groups={},
 782→        )
 783→
 784→        for group_id, symbols in groups.items():
 785→            logger.info(
 786→                f"[MatrixBacktest] group={group_id}, symbols={len(symbols)}, "
 787→                f"strategies={strategies}"
 788→            )
 789→
 790→            group_weights = self._run_group(
 791→                group_id=group_id,
 792→                symbols=symbols,
 793→                start=start,
 794→                end=today,
 795→                strategies=strategies,
 796→                param_grids=param_grids,
 797→                report=report,
 798→            )
 799→            report.groups[group_id] = group_weights
 800→
---
 700→        f"[WalkForward] done: {len(wf_rounds)} rounds, "
 701→        f"pass_all_rounds={report.pass_all_rounds}, "
 702→        f"max_val_dd={report.max_val_dd:.4f}%"
 703→    )
 704→    return report
 705→
 706→
 707→# ---------------------------------------------------------------------------
 708→# MatrixBacktest 主类
 709→# ---------------------------------------------------------------------------
 710→
 711→class MatrixBacktest:
 712→    """矩阵回测：N 策略 × G 标的组 × 参数网格 → strategy_weights.json。
 713→
 714→    Args:
 715→        store:       MarketDataStore（本地时序库）
 716→        universe:    UniverseManager（提供分组映射）
 717→        years:       回测窗口（默认 5 年）
 718→        init_cash:   初始资金
 719→        fees:        手续费率
 720→        slippage:    滑点率
 721→        top_k:       每组保留 Top-K 策略（默认 2）
 722→    """
 723→
 724→    def __init__(
 725→        self,
 726→        store: MarketDataStore,
 727→        universe: UniverseManager,
 728→        years: int = 5,
 729→        init_cash: float = 100_000.0,
 730→        fees: float = 0.001,
 731→        slippage: float = 0.001,
 732→        top_k: int = 2,
 733→    ) -> None:
 734→        self._store = store
 735→        self._universe = universe
 736→        self._years = years
 737→        self._init_cash = init_cash
 738→        self._fees = fees
 739→        self._slippage = slippage
 740→        self._top_k = top_k
 741→
 742→    def run(
 743→        self,
 744→        strategies: list[str],
 745→        param_grids: dict[str, dict[str, list]],
 746→        output_file: str | Path | None = None,
 747→    ) -> MatrixBacktestReport:
 748→        """执行完整矩阵回测。
 749→
 750→        Args:
 751→            strategies:  策略名称列表，如 ["dual_ma", "rsi"]
 752→            param_grids: 各策略参数网格，如 {"dual_ma": {"fast":[5,10], "slow":[20,30]}}
 753→            output_file: strategy_weights.json 输出路径（None 则不写文件）
 754→
 755→        Returns:
 756→            MatrixBacktestReport
 757→        """
 758→        today = date.today()
 759→        start = today - timedelta(days=self._years * 365)
 760→        window_str = f"{start.isoformat()} ~ {today.isoformat()}"
 761→
 762→        logger.info(
 763→            f"[MatrixBacktest] start={start}, end={today}, "
 764→            f"strategies={strategies}, years={self._years}"
 765→        )
 766→
 767→        # 获取分组（⚠️ 使用历史时点分组，而非当前静态分组）
 768→        # Phase 5 初期简化：用当前分组，但接口已预留历史分组能力
 769→        groups = self._universe.get_groups()
 770→        if not groups:
 771→            logger.warning("[MatrixBacktest] no groups available, abort")
 772→            return MatrixBacktestReport(
 773→                generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
 774→                backtest_window=window_str,
 775→                groups={},
 776→            )
 777→
 778→        report = MatrixBacktestReport(
 779→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
 780→            backtest_window=window_str,
 781→            groups={},
 782→        )
 783→
 784→        for group_id, symbols in groups.items():
 785→            logger.info(
 786→                f"[MatrixBacktest] group={group_id}, symbols={len(symbols)}, "
 787→                f"strategies={strategies}"
 788→            )
 789→
 790→            group_weights = self._run_group(
 791→                group_id=group_id,
 792→                symbols=symbols,
 793→                start=start,
 794→                end=today,
 795→                strategies=strategies,
 796→                param_grids=param_grids,
 797→                report=report,
 798→            )
 799→            report.groups[group_id] = group_weights
 800→
---
{"file_path": "/Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py", "limit": 160, "offset": 800}
---
 800→
 801→        if output_file is not None:
 802→            self._write_weights(report, output_file)
 803→
 804→        logger.info(
 805→            f"[MatrixBacktest] done: {len(report.groups)} groups, "
 806→            f"warnings={len(report.warnings)}"
 807→        )
 808→        return report
 809→
 810→    def _run_group(
 811→        self,
 812→        group_id: str,
 813→        symbols: list[str],
 814→        start: date,
 815→        end: date,
 816→        strategies: list[str],
 817→        param_grids: dict[str, dict[str, list]],
 818→        report: MatrixBacktestReport,
 819→    ) -> list[dict[str, Any]]:
 820→        """对单个分组执行策略 × 参数网格回测，返回该组的权重配置列表。"""
 821→
 822→        # 1. 读取组内所有标的数据
 823→        data = self._store.get_bars_multi(symbols, start, end)
 824→        if not data:
 825→            logger.warning(f"[MatrixBacktest] {group_id}: no data, skip")
 826→            return []
 827→
 828→        # 2. 对每个策略 × 每组参数，计算组合 Sharpe
 829→        group_results: list[tuple[str, dict, list[SingleBacktestResult]]] = []
 830→
 831→        for strategy in strategies:
 832→            # ⚠️ 早期检测未注册策略名（迭代 #1 修复"策略名拼写错误被静默跳过"的 bug）
 833→            # 之前 _backtest_one 内部静默 return None，导致 main.py 误用 "rsi"/"macd"/"bollinger"
 834→            # 简称 6 天未被发现。改为 WARNING 级日志 + continue。
 835→            if strategy not in STRATEGY_REGISTRY:
 836→                logger.warning(
 837→                    f"[MatrixBacktest] {group_id}: strategy '{strategy}' not in "
 838→                    f"STRATEGY_REGISTRY — skipped. "
 839→                    f"Check spelling against @register_strategy decorators. "
 840→                    f"Known: {sorted(STRATEGY_REGISTRY.keys())}"
 841→                )
 842→                continue
 843→            grid = param_grids.get(strategy, {})
 844→            param_combos = list(
 845→                dict(zip(grid.keys(), combo))
 846→                for combo in itertools.product(*grid.values())
 847→            ) if grid else [{}]
 848→
 849→            best_params = None
 850→            best_sharpe = float("-inf")
 851→            best_sortino = 0.0
 852→            best_results: list[SingleBacktestResult] = []
 853→
 854→            for params in param_combos:
 855→                # 对组内每只标的回测
 856→                results = []
 857→                for sym in symbols:
 858→                    df = data.get(sym, pd.DataFrame())
 859→                    if df.empty:
 860→                        continue
 861→                    df.index.name = sym  # 方便 _backtest_one 使用
 862→                    r = _backtest_one(
 863→                        df, strategy, params,
 864→                        self._init_cash, self._fees, self._slippage
 865→                    )
 866→                    if r is not None:
 867→                        results.append(r)
 868→
 869→                if not results:
 870→                    continue
 871→
 872→                # ⚠️ 等权合并日收益率序列计算组合 Sharpe（不能取算术平均）
 873→                ps = _portfolio_sharpe_from_results(results)
 874→                pso = _portfolio_sortino_from_results(results)
 875→
 876→                if ps > best_sharpe:
 877→                    best_sharpe = ps
 878→                    best_sortino = pso
 879→                    best_params = params
 880→                    best_results = results
 881→
 882→            if best_params is not None and best_results:
 883→                group_results.append((strategy, best_params, best_results))
 884→                report.group_results.append(GroupBacktestResult(
 885→                    group_id=group_id,
 886→                    strategy=strategy,
 887→                    params=best_params,
 888→                    portfolio_sharpe=best_sharpe,
 889→                    avg_total_return_pct=_safe_mean(
 890→                        [r.total_return_pct for r in best_results]
 891→                    ),
 892→                    avg_max_drawdown_pct=_safe_mean(
 893→                        [r.max_drawdown_pct for r in best_results]
 894→                    ),
 895→                    avg_win_rate_pct=_safe_mean(
 896→                        [r.win_rate_pct for r in best_results]
 897→                    ),
 898→                    symbol_count=len(best_results),
 899→                    portfolio_sortino=best_sortino,
 900→                    portfolio_max_drawdown=_portfolio_max_drawdown_from_results(
 901→                        best_results
 902→                    ),
 903→                ))
 904→
 905→        if not group_results:
 906→            logger.warning(f"[MatrixBacktest] {group_id}: no valid results")
 907→            return []
 908→
 909→        # 3. 迭代 #3：DD 约束 + Sortino 排序选 Top-K
 910→        #    Constitution L1: portfolio DD ≤ 20% 是硬约束
 911→        #    步骤：(a) 计算每候选 portfolio_max_drawdown
 912→        #          (b) 过滤 DD <= MAX_PORTFOLIO_DRAWDOWN_PCT 的合规集
 913→        #          (c) 合规集非空 → 按 Sortino 降序取 top-K
 914→        #          (d) 合规集为空 → fallback：按 DD 升序取 top-K，标记 dd_constrained=True
 915→        candidates: list[tuple[str, dict, list[SingleBacktestResult], float, float]] = []
 916→        for (strategy, params, results) in group_results:
 917→            pso = _portfolio_sortino_from_results(results)
 918→            pdd = _portfolio_max_drawdown_from_results(results)
 919→            candidates.append((strategy, params, results, pso, pdd))
 920→
 921→        compliant = [c for c in candidates if c[4] <= MAX_PORTFOLIO_DRAWDOWN_PCT]
 922→        if compliant:
 923→            # 合规集非空：按 Sortino 降序取 top-K
 924→            ranked = sorted(compliant, key=lambda x: x[3], reverse=True)
 925→            dd_constrained = False
 926→            logger.info(
 927→                f"[MatrixBacktest] {group_id}: DD filter passed — "
 928→                f"{len(compliant)}/{len(candidates)} candidates compliant "
 929→                f"(DD <= {MAX_PORTFOLIO_DRAWDOWN_PCT}%)"
 930→            )
 931→        else:
 932→            # Fallback：无合规候选（结构性问题，如 NDX_high_vol 全部 > 20%）
 933→            # 按 DD 升序（最低 DD 优先）取 top-K，标记 dd_constrained
 934→            ranked = sorted(candidates, key=lambda x: x[4])
 935→            dd_constrained = True
 936→            logger.warning(
 937→                f"[MatrixBacktest] {group_id}: NO compliant candidates "
 938→                f"(all {len(candidates)} exceed DD={MAX_PORTFOLIO_DRAWDOWN_PCT}%). "
 939→                f"Fallback: selected top-{self._top_k} by lowest DD. "
 940→                f"This group is marked dd_constrained=True — "
 941→                f"review whether to drop the group or accept the risk."
 942→            )
 943→            report.warnings.append(
 944→                f"{group_id}: dd_constrained=True "
 945→                f"(min DD={ranked[0][4]:.2f}% > {MAX_PORTFOLIO_DRAWDOWN_PCT}%)"
 946→            )
 947→
 948→        top_results = ranked[: self._top_k]
 949→
 950→        # 把 dd_constrained 标记同步到 report.group_results 中对应组的条目
 951→        for gr in report.group_results:
 952→            if gr.group_id == group_id:
 953→                gr.dd_constrained = dd_constrained
 954→
 955→        # 4. 优化 ensemble 权重（单点离散值加权投票语义）
 956→        weighted = _optimize_ensemble_weights(
 957→            [(s, p, r) for (s, p, r, _, _) in top_results]
 958→        )
 959→
 960→
---
 800→
 801→        if output_file is not None:
 802→            self._write_weights(report, output_file)
 803→
 804→        logger.info(
 805→            f"[MatrixBacktest] done: {len(report.groups)} groups, "
 806→            f"warnings={len(report.warnings)}"
 807→        )
 808→        return report
 809→
 810→    def _run_group(
 811→        self,
 812→        group_id: str,
 813→        symbols: list[str],
 814→        start: date,
 815→        end: date,
 816→        strategies: list[str],
 817→        param_grids: dict[str, dict[str, list]],
 818→        report: MatrixBacktestReport,
 819→    ) -> list[dict[str, Any]]:
 820→        """对单个分组执行策略 × 参数网格回测，返回该组的权重配置列表。"""
 821→
 822→        # 1. 读取组内所有标的数据
 823→        data = self._store.get_bars_multi(symbols, start, end)
 824→        if not data:
 825→            logger.warning(f"[MatrixBacktest] {group_id}: no data, skip")
 826→            return []
 827→
 828→        # 2. 对每个策略 × 每组参数，计算组合 Sharpe
 829→        group_results: list[tuple[str, dict, list[SingleBacktestResult]]] = []
 830→
 831→        for strategy in strategies:
 832→            # ⚠️ 早期检测未注册策略名（迭代 #1 修复"策略名拼写错误被静默跳过"的 bug）
 833→            # 之前 _backtest_one 内部静默 return None，导致 main.py 误用 "rsi"/"macd"/"bollinger"
 834→            # 简称 6 天未被发现。改为 WARNING 级日志 + continue。
 835→            if strategy not in STRATEGY_REGISTRY:
 836→                logger.warning(
 837→                    f"[MatrixBacktest] {group_id}: strategy '{strategy}' not in "
 838→                    f"STRATEGY_REGISTRY — skipped. "
 839→                    f"Check spelling against @register_strategy decorators. "
 840→                    f"Known: {sorted(STRATEGY_REGISTRY.keys())}"
 841→                )
 842→                continue
 843→            grid = param_grids.get(strategy, {})
 844→            param_combos = list(
 845→                dict(zip(grid.keys(), combo))
 846→                for combo in itertools.product(*grid.values())
 847→            ) if grid else [{}]
 848→
 849→            best_params = None
 850→            best_sharpe = float("-inf")
 851→            best_sortino = 0.0
 852→            best_results: list[SingleBacktestResult] = []
 853→
 854→            for params in param_combos:
 855→                # 对组内每只标的回测
 856→                results = []
 857→                for sym in symbols:
 858→                    df = data.get(sym, pd.DataFrame())
 859→                    if df.empty:
 860→                        continue
 861→                    df.index.name = sym  # 方便 _backtest_one 使用
 862→                    r = _backtest_one(
 863→                        df, strategy, params,
 864→                        self._init_cash, self._fees, self._slippage
 865→                    )
 866→                    if r is not None:
 867→                        results.append(r)
 868→
 869→                if not results:
 870→                    continue
 871→
 872→                # ⚠️ 等权合并日收益率序列计算组合 Sharpe（不能取算术平均）
 873→                ps = _portfolio_sharpe_from_results(results)
 874→                pso = _portfolio_sortino_from_results(results)
 875→
 876→                if ps > best_sharpe:
 877→                    best_sharpe = ps
 878→                    best_sortino = pso
 879→                    best_params = params
 880→                    best_results = results
 881→
 882→            if best_params is not None and best_results:
 883→                group_results.append((strategy, best_params, best_results))
 884→                report.group_results.append(GroupBacktestResult(
 885→                    group_id=group_id,
 886→                    strategy=strategy,
 887→                    params=best_params,
 888→                    portfolio_sharpe=best_sharpe,
 889→                    avg_total_return_pct=_safe_mean(
 890→                        [r.total_return_pct for r in best_results]
 891→                    ),
 892→                    avg_max_drawdown_pct=_safe_mean(
 893→                        [r.max_drawdown_pct for r in best_results]
 894→                    ),
 895→                    avg_win_rate_pct=_safe_mean(
 896→                        [r.win_rate_pct for r in best_results]
 897→                    ),
 898→                    symbol_count=len(best_results),
 899→                    portfolio_sortino=best_sortino,
 900→                    portfolio_max_drawdown=_portfolio_max_drawdown_from_results(
 901→                        best_results
 902→                    ),
 903→                ))
 904→
 905→        if not group_results:
 906→            logger.warning(f"[MatrixBacktest] {group_id}: no valid results")
 907→            return []
 908→
 909→        # 3. 迭代 #3：DD 约束 + Sortino 排序选 Top-K
 910→        #    Constitution L1: portfolio DD ≤ 20% 是硬约束
 911→        #    步骤：(a) 计算每候选 portfolio_max_drawdown
 912→        #          (b) 过滤 DD <= MAX_PORTFOLIO_DRAWDOWN_PCT 的合规集
 913→        #          (c) 合规集非空 → 按 Sortino 降序取 top-K
 914→        #          (d) 合规集为空 → fallback：按 DD 升序取 top-K，标记 dd_constrained=True
 915→        candidates: list[tuple[str, dict, list[SingleBacktestResult], float, float]] = []
 916→        for (strategy, params, results) in group_results:
 917→            pso = _portfolio_sortino_from_results(results)
 918→            pdd = _portfolio_max_drawdown_from_results(results)
 919→            candidates.append((strategy, params, results, pso, pdd))
 920→
 921→        compliant = [c for c in candidates if c[4] <= MAX_PORTFOLIO_DRAWDOWN_PCT]
 922→        if compliant:
 923→            # 合规集非空：按 Sortino 降序取 top-K
 924→            ranked = sorted(compliant, key=lambda x: x[3], reverse=True)
 925→            dd_constrained = False
 926→            logger.info(
 927→                f"[MatrixBacktest] {group_id}: DD filter passed — "
 928→                f"{len(compliant)}/{len(candidates)} candidates compliant "
 929→                f"(DD <= {MAX_PORTFOLIO_DRAWDOWN_PCT}%)"
 930→            )
 931→        else:
 932→            # Fallback：无合规候选（结构性问题，如 NDX_high_vol 全部 > 20%）
 933→            # 按 DD 升序（最低 DD 优先）取 top-K，标记 dd_constrained
 934→            ranked = sorted(candidates, key=lambda x: x[4])
 935→            dd_constrained = True
 936→            logger.warning(
 937→                f"[MatrixBacktest] {group_id}: NO compliant candidates "
 938→                f"(all {len(candidates)} exceed DD={MAX_PORTFOLIO_DRAWDOWN_PCT}%). "
 939→                f"Fallback: selected top-{self._top_k} by lowest DD. "
 940→                f"This group is marked dd_constrained=True — "
 941→                f"review whether to drop the group or accept the risk."
 942→            )
 943→            report.warnings.append(
 944→                f"{group_id}: dd_constrained=True "
 945→                f"(min DD={ranked[0][4]:.2f}% > {MAX_PORTFOLIO_DRAWDOWN_PCT}%)"
 946→            )
 947→
 948→        top_results = ranked[: self._top_k]
 949→
 950→        # 把 dd_constrained 标记同步到 report.group_results 中对应组的条目
 951→        for gr in report.group_results:
 952→            if gr.group_id == group_id:
 953→                gr.dd_constrained = dd_constrained
 954→
 955→        # 4. 优化 ensemble 权重（单点离散值加权投票语义）
 956→        weighted = _optimize_ensemble_weights(
 957→            [(s, p, r) for (s, p, r, _, _) in top_results]
 958→        )
 959→
 960→
---
{"file_path": "/Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py", "limit": 50, "offset": 955}
---
 955→        # 4. 优化 ensemble 权重（单点离散值加权投票语义）
 956→        weighted = _optimize_ensemble_weights(
 957→            [(s, p, r) for (s, p, r, _, _) in top_results]
 958→        )
 959→
 960→        # 5. 构建权重配置列表
 961→        weights_list = []
 962→        for strategy, params, weight in weighted:
 963→            # 找到对应的 GroupBacktestResult
 964→            gr = next(
 965→                (r for r in report.group_results
 966→                 if r.group_id == group_id and r.strategy == strategy),
 967→                None,
 968→            )
 969→            # 迭代 #4：新增 backtest_dd_status 字段（'pass' / 'dd_constrained'）
 970→            # 作为风险 metadata 标记，与 dd_constrained bool 同义但更可读
 971→            backtest_dd_status = "dd_constrained" if dd_constrained else "pass"
 972→            weights_list.append({
 973→                "strategy": strategy,
 974→                "params": params,
 975→                "weight": round(weight, 4),
 976→                "backtest_sharpe": round(gr.portfolio_sharpe if gr else 0.0, 4),
 977→                "backtest_sortino": round(gr.portfolio_sortino if gr else 0.0, 4),
 978→                "backtest_max_drawdown": round(gr.portfolio_max_drawdown if gr else 0.0, 4),
 979→                "backtest_win_rate": round(gr.avg_win_rate_pct / 100 if gr else 0.5, 4),
 980→                # 迭代 #3：标记该组是否用了 DD fallback（无合规候选）
 981→                # 同组所有策略条目共享同一 dd_constrained 值
 982→                "dd_constrained": dd_constrained,
 983→                # 迭代 #4：backtest_dd_status — 风险 metadata 字段
 984→                # 'pass' = 该组有合规候选（DD ≤ 20%）
 985→                # 'dd_constrained' = fallback 触发（无合规候选，按最低 DD 取 top-K）
 986→                # 下游消费方（PortfolioBacktester / 风控观测）可读此字段判断
 987→                # 该组权重的可靠性，作为风险信号标记
 988→                "backtest_dd_status": backtest_dd_status,
 989→            })
 990→
 991→        return weights_list
 992→
 993→    def _write_weights(
 994→        self, report: MatrixBacktestReport, output_file: str | Path
 995→    ) -> None:
 996→        """将矩阵回测结果写入 strategy_weights.json。"""
 997→        output_file = Path(output_file)
 998→        output_file.parent.mkdir(parents=True, exist_ok=True)
 999→
1000→        data = {
1001→            "_meta": {
1002→                "generated_at": report.generated_at,
1003→                "backtest_window": report.backtest_window,
1004→                "reoptimize_freq": "monthly",
1005→
---
 955→        # 4. 优化 ensemble 权重（单点离散值加权投票语义）
 956→        weighted = _optimize_ensemble_weights(
 957→            [(s, p, r) for (s, p, r, _, _) in top_results]
 958→        )
 959→
 960→        # 5. 构建权重配置列表
 961→        weights_list = []
 962→        for strategy, params, weight in weighted:
 963→            # 找到对应的 GroupBacktestResult
 964→            gr = next(
 965→                (r for r in report.group_results
 966→                 if r.group_id == group_id and r.strategy == strategy),
 967→                None,
 968→            )
 969→            # 迭代 #4：新增 backtest_dd_status 字段（'pass' / 'dd_constrained'）
 970→            # 作为风险 metadata 标记，与 dd_constrained bool 同义但更可读
 971→            backtest_dd_status = "dd_constrained" if dd_constrained else "pass"
 972→            weights_list.append({
 973→                "strategy": strategy,
 974→                "params": params,
 975→                "weight": round(weight, 4),
 976→                "backtest_sharpe": round(gr.portfolio_sharpe if gr else 0.0, 4),
 977→                "backtest_sortino": round(gr.portfolio_sortino if gr else 0.0, 4),
 978→                "backtest_max_drawdown": round(gr.portfolio_max_drawdown if gr else 0.0, 4),
 979→                "backtest_win_rate": round(gr.avg_win_rate_pct / 100 if gr else 0.5, 4),
 980→                # 迭代 #3：标记该组是否用了 DD fallback（无合规候选）
 981→                # 同组所有策略条目共享同一 dd_constrained 值
 982→                "dd_constrained": dd_constrained,
 983→                # 迭代 #4：backtest_dd_status — 风险 metadata 字段
 984→                # 'pass' = 该组有合规候选（DD ≤ 20%）
 985→                # 'dd_constrained' = fallback 触发（无合规候选，按最低 DD 取 top-K）
 986→                # 下游消费方（PortfolioBacktester / 风控观测）可读此字段判断
 987→                # 该组权重的可靠性，作为风险信号标记
 988→                "backtest_dd_status": backtest_dd_status,
 989→            })
 990→
 991→        return weights_list
 992→
 993→    def _write_weights(
 994→        self, report: MatrixBacktestReport, output_file: str | Path
 995→    ) -> None:
 996→        """将矩阵回测结果写入 strategy_weights.json。"""
 997→        output_file = Path(output_file)
 998→        output_file.parent.mkdir(parents=True, exist_ok=True)
 999→
1000→        data = {
1001→            "_meta": {
1002→                "generated_at": report.generated_at,
1003→                "backtest_window": report.backtest_window,
1004→                "reoptimize_freq": "monthly",
1005→
---
Now
---
 I
---
 have all the context.
---
 Let me rewrite
---
 `_run_group` and
---
 add
---
 `_
---
get_spy_returns`.
---
 I'll do this
---
 as
---
 one
---
 big edit to capture
---
 the full flow
---
.
---
现在让我
---
替换
---
整个
---
 `_run_group` 方法
---
以实现
---
基于
---
 alpha
---
 的选择，并添加
---
 `_get_spy_returns
---
` 方法：
---
{"file_path": "/Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py", "new_string": "    def _get_spy_returns(self, start: date, end: date) -> pd.Series | None:\n        \"\"\"获取 SPY 同期日收益率序列，用于计算 alpha（迭代 #9 新增）。\n\n        从 MarketDataStore 拉取 SPY 日线数据，计算日收益率。\n        SPY 不在标的池中，但作为 benchmark 用于 alpha 计算。\n\n        降级处理：SPY 数据不可用时返回 None（_compute_alpha 会返回 0.0），\n        不抛异常，保证回测不因 benchmark 缺失而阻塞。\n\n        Args:\n            start: 回测起始日期\n            end:   回测结束日期\n\n        Returns:\n            SPY 日收益率 pd.Series；数据不可用时返回 None\n        \"\"\"\n        try:\n            spy_bars = self._store.get_bars_multi([\"SPY\"], start, end)\n            spy_df = spy_bars.get(\"SPY\") if spy_bars else None\n            if spy_df is None or spy_df.empty:\n                logger.warning(\n                    \"[MatrixBacktest] SPY data unavailable, alpha will degrade to 0.0\"\n                )\n                return None\n            spy_close = spy_df[\"close\"].astype(float)\n            if len(spy_close) < 2:\n                logger.warning(\n                    \"[MatrixBacktest] SPY data too short, alpha will degrade to 0.0\"\n                )\n                return None\n            return spy_close.pct_change().dropna()\n        except Exception as e:\n            logger.warning(\n                f\"[MatrixBacktest] SPY benchmark fetch failed: {e} — \"\n                f\"alpha will degrade to 0.0\"\n            )\n            return None\n\n    def _run_group(\n        self,\n        group_id: str,\n        symbols: list[str],\n        start: date,\n        end: date,\n        strategies: list[str],\n        param_grids: dict[str, dict[str, list]],\n        report: MatrixBacktestReport,\n    ) -> list[dict[str, Any]]:\n        \"\"\"对单个分组执行策略 × 参数网格回测，返回该组的权重配置列表。\n\n        迭代 #9 变更：\n            - per-strategy best params：从 Sharpe 改为 Alpha（vs SPY）\n            - top-K 排序：从 Sortino 改为 Alpha\n            - 新增 Sortino > 0.5 最低质量门槛（二级过滤，可放宽）\n            - ensemble weights：从 Sharpe 改为 Alpha\n        \"\"\"\n\n        # 1. 读取组内所有标的数据\n        data = self._store.get_bars_multi(symbols, start, end)\n        if not data:\n            logger.warning(f\"[MatrixBacktest] {group_id}: no data, skip\")\n            return []\n\n        # 迭代 #9：获取 SPY 同期日收益率用于 alpha 计算（一次获取，组内复用）\n        spy_returns = self._get_spy_returns(start, end)\n\n        # 2. 对每个策略 × 每组参数，按 alpha 选最优参数\n        group_results: list[tuple[str, dict, list[SingleBacktestResult]]] = []\n\n        for strategy in strategies:\n            # ⚠️ 早期检测未注册策略名（迭代 #1 修复\"策略名拼写错误被静默跳过\"的 bug）\n            # 之前 _backtest_one 内部静默 return None，导致 main.py 误用 \"rsi\"/\"macd\"/\"bollinger\"\n            # 简称 6 天未被发现。改为 WARNING 级日志 + continue。\n            if strategy not in STRATEGY_REGISTRY:\n                logger.warning(\n                    f\"[MatrixBacktest] {group_id}: strategy '{strategy}' not in \"\n                    f\"STRATEGY_REGISTRY — skipped. \"\n                    f\"Check spelling against @register_strategy decorators. \"\n                    f\"Known: {sorted(STRATEGY_REGISTRY.keys())}\"\n                )\n                continue\n            grid = param_grids.get(strategy, {})\n            param_combos = list(\n                dict(zip(grid.keys(), combo))\n                for combo in itertools.product(*grid.values())\n            ) if grid else [{}]\n\n            best_params = None\n            best_alpha = float(\"-inf\")\n            best_sharpe = 0.0       # 仅用于 GroupBacktestResult 存档\n            best_sortino = 0.0      # 仅用于 GroupBacktestResult 存档\n            best_results: list[SingleBacktestResult] = []\n\n            for params in param_combos:\n                # 对组内每只标的回测\n                results = []\n                for sym in symbols:\n                    df = data.get(sym, pd.DataFrame())\n                    if df.empty:\n                        continue\n                    df.index.name = sym  # 方便 _backtest_one 使用\n                    r = _backtest_one(\n                        df, strategy, params,\n                        self._init_cash, self._fees, self._slippage\n                    )\n                    if r is not None:\n                        results.append(r)\n\n                if not results:\n                    continue\n\n                # ⚠️ 等权合并日收益率序列，一次性计算所有指标\n                # 迭代 #9：复用 combined 计算 sharpe / sortino / alpha\n                combined = _combine_daily_returns(results)\n                ps = _compute_sharpe(combined)\n                pso = _compute_sortino(combined)\n                alpha = _compute_alpha(combined, spy_returns)\n\n                # 迭代 #9：per-strategy best params 用 alpha 选（替代 Sharpe）\n                if alpha > best_alpha:\n                    best_alpha = alpha\n                    best_sharpe = ps\n                    best_sortino = pso\n                    best_params = params\n                    best_results = results\n\n            if best_params is not None and best_results:\n                group_results.append((strategy, best_params, best_results))\n                report.group_results.append(GroupBacktestResult(\n                    group_id=group_id,\n                    strategy=strategy,\n                    params=best_params,\n                    portfolio_sharpe=best_sharpe,\n                    avg_total_return_pct=_safe_mean(\n                        [r.total_return_pct for r in best_results]\n                    ),\n                    avg_max_drawdown_pct=_safe_mean(\n                        [r.max_drawdown_pct for r in best_results]\n                    ),\n                    avg_win_rate_pct=_safe_mean(\n                        [r.win_rate_pct for r in best_results]\n                    ),\n                    symbol_count=len(best_results),\n                    portfolio_sortino=best_sortino,\n                    portfolio_max_drawdown=_portfolio_max_drawdown_from_results(\n                        best_results\n                    ),\n                    backtest_alpha=best_alpha,\n                ))\n\n        if not group_results:\n            logger.warning(f\"[MatrixBacktest] {group_id}: no valid results\")\n            return []\n\n        # 3. 迭代 #9：DD 硬约束 + Sortino 门槛 + Alpha 排序选 Top-K\n        #    Constitution L1: portfolio DD ≤ 20% 是硬约束（保留）\n        #    新增：Sortino > 0.5 最低质量门槛（可放宽）\n        #    变更：排序指标从 Sortino 改为 Alpha\n        #\n        #    三级过滤策略：\n        #      Tier 1: DD ≤ 20% AND Sortino > 0.5 → Alpha 降序\n        #      Tier 2 (fallback): Tier 1 为空 → 仅 DD ≤ 20% → Alpha 降序\n        #      Tier 3 (fallback): Tier 2 为空 → 按 DD 升序，标记 dd_constrained=True\n        candidates: list[\n            tuple[str, dict, list[SingleBacktestResult], float, float, float]\n        ] = []\n        for (strategy, params, results) in group_results:\n            pso = _portfolio_sortino_from_results(results)\n            pdd = _portfolio_max_drawdown_from_results(results)\n            # 复用 _combine_daily_returns 计算 alpha（与 per-strategy 选择一致）\n            alpha = _compute_alpha(_combine_daily_returns(results), spy_returns)\n            candidates.append((strategy, params, results, pso, pdd, alpha))\n\n        # Tier 1: DD ≤ 20% AND Sortino > 0.5\n        compliant = [\n            c for c in candidates\n            if c[4] <= MAX_PORTFOLIO_DRAWDOWN_PCT and c[3] > MIN_SORTINO_THRESHOLD\n        ]\n        if compliant:\n            # Tier 1 命中：按 Alpha 降序取 top-K\n            ranked = sorted(compliant, key=lambda x: x[5], reverse=True)\n            dd_constrained = False\n            logger.info(\n                f\"[MatrixBacktest] {group_id}: DD + Sortino filter passed — \"\n                f\"{len(compliant)}/{len(candidates)} candidates compliant \"\n                f\"(DD <= {MAX_PORTFOLIO_DRAWDOWN_PCT}% AND Sortino > {MIN_SORTINO_THRESHOLD})\"\n            )\n        else:\n            # Tier 2: 放宽 Sortino 门槛，仅保留 DD 约束\n            dd_compliant = [\n                c for c in candidates if c[4] <= MAX_PORTFOLIO_DRAWDOWN_PCT\n            ]\n            if dd_compliant:\n                # Tier 2 命中：按 Alpha 降序取 top-K（dd_constrained 仍为 False）\n                ranked = sorted(dd_compliant, key=lambda x: x[5], reverse=True)\n                dd_constrained = False\n                logger.warning(\n                    f\"[MatrixBacktest] {group_id}: Sortino filter relaxed — \"\n                    f\"no candidate passed Sortino > {MIN_SORTINO_THRESHOLD}. \"\n                    f\"Fallback to DD-only filter: \"\n                    f\"{len(dd_compliant)}/{len(candidates)} candidates DD-compliant.\"\n                )\n            else:\n                # Tier 3: 无 DD 合规候选 → 按 DD 升序，标记 dd_constrained\n                # （结构性问题，如 NDX_high_vol 全部 > 20%）\n                ranked = sorted(candidates, key=lambda x: x[4])\n                dd_constrained = True\n                logger.warning(\n                    f\"[MatrixBacktest] {group_id}: NO compliant candidates \"\n                    f\"(all {len(candidates)} exceed DD={MAX_PORTFOLIO_DRAWDOWN_PCT}%). \"\n                    f\"Fallback: selected top-{self._top_k} by lowest DD. \"\n                    f\"This group is marked dd_constrained=True — \"\n                    f\"review whether to drop the group or accept the risk.\"\n                )\n                report.warnings.append(\n                    f\"{group_id}: dd_constrained=True \"\n                    f\"(min DD={ranked[0][4]:.2f}% > {MAX_PORTFOLIO_DRAWDOWN_PCT}%)\"\n                )\n\n        top_results = ranked[: self._top_k]\n\n        # 把 dd_constrained 标记同步到 report.group_results 中对应组的条目\n        for gr in report.group_results:\n            if gr.group_id == group_id:\n                gr.dd_constrained = dd_constrained\n\n        # 4. 优化 ensemble 权重（单点离散值加权投票语义，迭代 #9 改用 alpha）\n        weighted = _optimize_ensemble_weights(\n            [(s, p, r) for (s, p, r, _, _, _) in top_results],\n            spy_returns=spy_returns,\n        )\n\n        # 5. 构建权重配置列表\n        weights_list = []\n        for strategy, params, weight in weighted:\n            # 找到对应的 GroupBacktestResult\n            gr = next(\n                (r for r in report.group_results\n                 if r.group_id == group_id and r.strategy == strategy),\n                None,\n            )\n            # 迭代 #4：新增 backtest_dd_status 字段（'pass' / 'dd_constrained'）\n            # 作为风险 metadata 标记，与 dd_constrained bool 同义但更可读\n            backtest_dd_status = \"dd_constrained\" if dd_constrained else \"pass\"\n            weights_list.append({\n                \"strategy\": strategy,\n                \"params\": params,\n                \"weight\": round(weight, 4),\n                \"backtest_sharpe\": round(gr.portfolio_sharpe if gr else 0.0, 4),\n                \"backtest_sortino\": round(gr.portfolio_sortino if gr else 0.0, 4),\n                \"backtest_max_drawdown\": round(gr.portfolio_max_drawdown if gr else 0.0, 4),\n                \"backtest_win_rate\": round(gr.avg_win_rate_pct / 100 if gr else 0.5, 4),\n                # 迭代 #9：新增 backtest_alpha 字段（vs SPY 的超额收益百分数）\n                # 下游 PortfolioBacktester 可读此字段验证 alpha 一致性\n                \"backtest_alpha\": round(gr.backtest_alpha if gr else 0.0, 4),\n                # 迭代 #3：标记该组是否用了 DD fallback（无合规候选）\n                # 同组所有策略条目共享同一 dd_constrained 值\n                \"dd_constrained\": dd_constrained,\n                # 迭代 #4：backtest_dd_status — 风险 metadata 字段\n                # 'pass' = 该组有合规候选（DD ≤ 20%）\n                # 'dd_constrained' = fallback 触发（无合规候选，按最低 DD 取 top-K）\n                # 下游消费方（PortfolioBacktester / 风控观测）可读此字段判断\n                # 该组权重的可靠性，作为风险信号标记\n                \"backtest_dd_status\": backtest_dd_status,\n            })\n\n        return weights_list", "old_string": "    def _run_group(\n        self,\n        group_id: str,\n        symbols: list[str],\n        start: date,\n        end: date,\n        strategies: list[str],\n        param_grids: dict[str, dict[str, list]],\n        report: MatrixBacktestReport,\n    ) -> list[dict[str, Any]]:\n        \"\"\"对单个分组执行策略 × 参数网格回测，返回该组的权重配置列表。\"\"\"\n\n        # 1. 读取组内所有标的数据\n        data = self._store.get_bars_multi(symbols, start, end)\n        if not data:\n            logger.warning(f\"[MatrixBacktest] {group_id}: no data, skip\")\n            return []\n\n        # 2. 对每个策略 × 每组参数，计算组合 Sharpe\n        group_results: list[tuple[str, dict, list[SingleBacktestResult]]] = []\n\n        for strategy in strategies:\n            # ⚠️ 早期检测未注册策略名（迭代 #1 修复\"策略名拼写错误被静默跳过\"的 bug）\n            # 之前 _backtest_one 内部静默 return None，导致 main.py 误用 \"rsi\"/\"macd\"/\"bollinger\"\n            # 简称 6 天未被发现。改为 WARNING 级日志 + continue。\n            if strategy not in STRATEGY_REGISTRY:\n                logger.warning(\n                    f\"[MatrixBacktest] {group_id}: strategy '{strategy}' not in \"\n                    f\"STRATEGY_REGISTRY — skipped. \"\n                    f\"Check spelling against @register_strategy decorators. \"\n                    f\"Known: {sorted(STRATEGY_REGISTRY.keys())}\"\n                )\n                continue\n            grid = param_grids.get(strategy, {})\n            param_combos = list(\n                dict(zip(grid.keys(), combo))\n                for combo in itertools.product(*grid.values())\n            ) if grid else [{}]\n\n            best_params = None\n            best_sharpe = float(\"-inf\")\n            best_sortino = 0.0\n            best_results: list[SingleBacktestResult] = []\n\n            for params in param_combos:\n                # 对组内每只标的回测\n                results = []\n                for sym in symbols:\n                    df = data.get(sym, pd.DataFrame())\n                    if df.empty:\n                        continue\n                    df.index.name = sym  # 方便 _backtest_one 使用\n                    r = _backtest_one(\n                        df, strategy, params,\n                        self._init_cash, self._fees, self._slippage\n                    )\n                    if r is not None:\n                        results.append(r)\n\n                if not results:\n                    continue\n\n                # ⚠️ 等权合并日收益率序列计算组合 Sharpe（不能取算术平均）\n                ps = _portfolio_sharpe_from_results(results)\n                pso = _portfolio_sortino_from_results(results)\n\n                if ps > best_sharpe:\n                    best_sharpe = ps\n                    best_sortino = pso\n                    best_params = params\n                    best_results = results\n\n            if best_params is not None and best_results:\n                group_results.append((strategy, best_params, best_results))\n                report.group_results.append(GroupBacktestResult(\n                    group_id=group_id,\n                    strategy=strategy,\n                    params=best_params,\n                    portfolio_sharpe=best_sharpe,\n                    avg_total_return_pct=_safe_mean(\n                        [r.total_return_pct for r in best_results]\n                    ),\n                    avg_max_drawdown_pct=_safe_mean(\n                        [r.max_drawdown_pct for r in best_results]\n                    ),\n                    avg_win_rate_pct=_safe_mean(\n                        [r.win_rate_pct for r in best_results]\n                    ),\n                    symbol_count=len(best_results),\n                    portfolio_sortino=best_sortino,\n                    portfolio_max_drawdown=_portfolio_max_drawdown_from_results(\n                        best_results\n                    ),\n                ))\n\n        if not group_results:\n            logger.warning(f\"[MatrixBacktest] {group_id}: no valid results\")\n            return []\n\n        # 3. 迭代 #3：DD 约束 + Sortino 排序选 Top-K\n        #    Constitution L1: portfolio DD ≤ 20% 是硬约束\n        #    步骤：(a) 计算每候选 portfolio_max_drawdown\n        #          (b) 过滤 DD <= MAX_PORTFOLIO_DRAWDOWN_PCT 的合规集\n        #          (c) 合规集非空 → 按 Sortino 降序取 top-K\n        #          (d) 合规集为空 → fallback：按 DD 升序取 top-K，标记 dd_constrained=True\n        candidates: list[tuple[str, dict, list[SingleBacktestResult], float, float]] = []\n        for (strategy, params, results) in group_results:\n            pso = _portfolio_sortino_from_results(results)\n            pdd = _portfolio_max_drawdown_from_results(results)\n            candidates.append((strategy, params, results, pso, pdd))\n\n        compliant = [c for c in candidates if c[4] <= MAX_PORTFOLIO_DRAWDOWN_PCT]\n        if compliant:\n            # 合规集非空：按 Sortino 降序取 top-K\n            ranked = sorted(compliant, key=lambda x: x[3], reverse=True)\n            dd_constrained = False\n            logger.info(\n                f\"[MatrixBacktest] {group_id}: DD filter passed — \"\n                f\"{len(compliant)}/{len(candidates)} candidates compliant \"\n                f\"(DD <= {MAX_PORTFOLIO_DRAWDOWN_PCT}%)\"\n            )\n        else:\n            # Fallback：无合规候选（结构性问题，如 NDX_high_vol 全部 > 20%）\n            # 按 DD 升序（最低 DD 优先）取 top-K，标记 dd_constrained\n            ranked = sorted(candidates, key=lambda x: x[4])\n            dd_constrained = True\n            logger.warning(\n                f\"[MatrixBacktest] {group_id}: NO compliant candidates \"\n                f\"(all {len(candidates)} exceed DD={MAX_PORTFOLIO_DRAWDOWN_PCT}%). \"\n                f\"Fallback: selected top-{self._top_k} by lowest DD. \"\n                f\"This group is marked dd_constrained=True — \"\n                f\"review whether to drop the group or accept the risk.\"\n            )\n            report.warnings.append(\n                f\"{group_id}: dd_constrained=True \"\n                f\"(min DD={ranked[0][4]:.2f}% > {MAX_PORTFOLIO_DRAWDOWN_PCT}%)\"\n            )\n\n        top_results = ranked[: self._top_k]\n\n        # 把 dd_constrained 标记同步到 report.group_results 中对应组的条目\n        for gr in report.group_results:\n            if gr.group_id == group_id:\n                gr.dd_constrained = dd_constrained\n\n        # 4. 优化 ensemble 权重（单点离散值加权投票语义）\n        weighted = _optimize_ensemble_weights(\n            [(s, p, r) for (s, p, r, _, _) in top_results]\n        )\n\n        # 5. 构建权重配置列表\n        weights_list = []\n        for strategy, params, weight in weighted:\n            # 找到对应的 GroupBacktestResult\n            gr = next(\n                (r for r in report.group_results\n                 if r.group_id == group_id and r.strategy == strategy),\n                None,\n            )\n            # 迭代 #4：新增 backtest_dd_status 字段（'pass' / 'dd_constrained'）\n            # 作为风险 metadata 标记，与 dd_constrained bool 同义但更可读\n            backtest_dd_status = \"dd_constrained\" if dd_constrained else \"pass\"\n            weights_list.append({\n                \"strategy\": strategy,\n                \"params\": params,\n                \"weight\": round(weight, 4),\n                \"backtest_sharpe\": round(gr.portfolio_sharpe if gr else 0.0, 4),\n                \"backtest_sortino\": round(gr.portfolio_sortino if gr else 0.0, 4),\n                \"backtest_max_drawdown\": round(gr.portfolio_max_drawdown if gr else 0.0, 4),\n                \"backtest_win_rate\": round(gr.avg_win_rate_pct / 100 if gr else 0.5, 4),\n                # 迭代 #3：标记该组是否用了 DD fallback（无合规候选）\n                # 同组所有策略条目共享同一 dd_constrained 值\n                \"dd_constrained\": dd_constrained,\n                # 迭代 #4：backtest_dd_status — 风险 metadata 字段\n                # 'pass' = 该组有合规候选（DD ≤ 20%）\n                # 'dd_constrained' = fallback 触发（无合规候选，按最低 DD 取 top-K）\n                # 下游消费方（PortfolioBacktester / 风控观测）可读此字段判断\n                # 该组权重的可靠性，作为风险信号标记\n                \"backtest_dd_status\": backtest_dd_status,\n            })\n\n        return weights_list", "replace_all": false}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py
---
{"status": "completed", "taskId": "3"}
---
Updated task #3 status
---
Updated task #3 status
---
{"status": "completed", "taskId": "4"}
---
Updated task #4 status
---
Updated task #4 status
---
{"status": "completed", "taskId": "5"}
---
Updated task #5 status
---
Updated task #5 status
---
现在
---
让我通过
---
运行现有
---
测试来进行
---
一次
---
快速的语法
---
检查：
---
{"command": "/Users/rickouyang/miniforge3/envs/py312trade/bin/python -c \"from mytrader.backtest.matrix_backtest import MatrixBacktest, _compute_alpha, _combine_daily_returns, MIN_SORTINO_THRESHOLD, GroupBacktestResult; print('Import OK, MIN_SORTINO_THRESHOLD =', MIN_SORTINO_THRESHOLD); print('GroupBacktestResult fields:', [f.name for f in GroupBacktestResult.__dataclass_fields__.values()])\"", "description": "Verify imports and module loads"}
---
Verify imports and module loads
---
Command: /Users/rickouyang/miniforge3/envs/py312trade/bin/python -c "from mytrader.backtest.matrix_backtest import MatrixBacktest, _compute_alpha, _combine_daily_returns, MIN_SORTINO_THRESHOLD, GroupBacktestResult; print('Import OK, MIN_SORTINO_THRESHOLD =', MIN_SORTINO_THRESHOLD); print('GroupBacktestResult fields:', [f.name for f in GroupBacktestResult.__dataclass_fields__.values()])"
Stdout: Import OK, MIN_SORTINO_THRESHOLD = 0.5
GroupBacktestResult fields: ['group_id', 'strategy', 'params', 'portfolio_sharpe', 'avg_total_return_pct', 'avg_max_drawdown_pct', 'avg_win_rate_pct', 'symbol_count', 'portfolio_sortino', 'portfolio_max_drawdown', 'dd_constrained', 'backtest_alpha']

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
很好
---
。让我
---
运行现有的 matrix_backtest
---
 测试来
---
检查是否有
---
回归问题：
---
{"command": "/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_matrix_backtest.py -x -q 2>&1 | tail -30", "description": "Run matrix_backtest tests"}
---
Run matrix_backtest tests
---
Command: /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_matrix_backtest.py -x -q 2>&1 | tail -30
Stdout: ..........................................................               [100%]

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
现有
---
 58 个测试全部
---
通过。现在我来
---
编写新的测试：
---
{"status": "in_progress", "taskId": "6"}
---
Updated task #6 status
---
Updated task #6 status
---
{"file_path": "/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py", "limit": 40, "offset": 940}
---
 940→        assert report.max_val_dd == 0.0
 941→
 942→    def test_run_walk_forward_custom_rounds(self, mock_store, mock_universe):
 943→        """run_walk_forward 支持自定义 rounds 参数（非默认 4）。"""
 944→        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)
 945→        report = run_walk_forward(
 946→            mb=mb,
 947→            strategies=["dual_ma"],
 948→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 949→            rounds=2,
 950→            train_months=12,
 951→            val_months=4,
 952→        )
 953→        assert len(report.rounds) == 2
 954→        assert report.rounds[0].round_num == 1
 955→        assert report.rounds[1].round_num == 2
 956→
 957→
---
 940→        assert report.max_val_dd == 0.0
 941→
 942→    def test_run_walk_forward_custom_rounds(self, mock_store, mock_universe):
 943→        """run_walk_forward 支持自定义 rounds 参数（非默认 4）。"""
 944→        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)
 945→        report = run_walk_forward(
 946→            mb=mb,
 947→            strategies=["dual_ma"],
 948→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 949→            rounds=2,
 950→            train_months=12,
 951→            val_months=4,
 952→        )
 953→        assert len(report.rounds) == 2
 954→        assert report.rounds[0].round_num == 1
 955→        assert report.rounds[1].round_num == 2
 956→
 957→
---
现在我
---
将在末
---
尾添加新的
---
测试类。
---
先
---
让我更新
---
一下
---
 imports
---
：
---
{"file_path": "/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py", "new_string": "from mytrader.backtest.matrix_backtest import (\n    MatrixBacktest,\n    _backtest_one,\n    _combine_daily_returns,\n    _compute_alpha,\n    _compute_sharpe,\n    _compute_sortino,\n    _portfolio_max_drawdown_from_results,\n    _portfolio_sharpe_from_results,\n    _portfolio_sortino_from_results,\n    _optimize_ensemble_weights,\n    _safe_float,\n    _safe_mean,\n    MAX_PORTFOLIO_DRAWDOWN_PCT,\n    MIN_SORTINO_THRESHOLD,\n    WALK_FORWARD_VAL_DD_THRESHOLD,\n    SingleBacktestResult,\n    WalkForwardReport,\n    WalkForwardRound,\n    _add_months,\n    run_walk_forward,\n)", "old_string": "from mytrader.backtest.matrix_backtest import (\n    MatrixBacktest,\n    _backtest_one,\n    _compute_sharpe,\n    _compute_sortino,\n    _portfolio_max_drawdown_from_results,\n    _portfolio_sharpe_from_results,\n    _portfolio_sortino_from_results,\n    _safe_float,\n    _safe_mean,\n    MAX_PORTFOLIO_DRAWDOWN_PCT,\n    WALK_FORWARD_VAL_DD_THRESHOLD,\n    SingleBacktestResult,\n    WalkForwardReport,\n    WalkForwardRound,\n    _add_months,\n    run_walk_forward,\n)", "replace_all": false}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py
---
现在
---
让我
---
来
---
添加新的测试类。
---
首先，让我检查一下
---
最后一个
---
测试类的
---
末
---
尾：
---
{"file_path": "/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py", "limit": 10, "offset": 955}
---
 955→            val_months=4,
 956→        )
 957→        assert len(report.rounds) == 2
 958→        assert report.rounds[0].round_num == 1
 959→        assert report.rounds[1].round_num == 2
 960→
 961→
---
 955→            val_months=4,
 956→        )
 957→        assert len(report.rounds) == 2
 958→        assert report.rounds[0].round_num == 1
 959→        assert report.rounds[1].round_num == 2
 960→
 961→
---
{"file_path": "/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py", "new_string": "            val_months=4,\n        )\n        assert len(report.rounds) == 2\n        assert report.rounds[0].round_num == 1\n        assert report.rounds[1].round_num == 2\n\n\n# ---------------------------------------------------------------------------\n# 迭代 #9 新增：Alpha-Based Strategy Selection\n# ---------------------------------------------------------------------------\n\nclass TestAlphaComputation:\n    \"\"\"_compute_alpha / _combine_daily_returns 单元测试。\"\"\"\n\n    def test_compute_alpha_basic(self):\n        \"\"\"构造已知策略收益和 SPY 收益，验证 alpha 计算正确。\n\n        策略日均收益 0.001 (0.1%)，SPY 日均收益 0.0004 (0.04%)。\n        年化：(1.001^252 - 1) - (1.0004^252 - 1) ≈ 0.285 - 0.110 = 0.175 → 17.5%\n        \"\"\"\n        np.random.seed(42)\n        idx = pd.date_range(\"2021-01-01\", periods=252, freq=\"B\")\n        # 策略收益：稳定 0.1%/日（年化 ~28.5%）\n        strat_returns = pd.Series(\n            np.random.normal(0.001, 0.002, 252), index=idx\n        )\n        # SPY 收益：稳定 0.04%/日（年化 ~11.0%）\n        spy_returns = pd.Series(\n            np.random.normal(0.0004, 0.001, 252), index=idx\n        )\n\n        alpha = _compute_alpha(strat_returns, spy_returns)\n\n        # 期望 alpha ≈ 17.5%（正数，跑赢 SPY）\n        assert alpha > 0.0, f\"策略年化应高于 SPY，alpha 应为正，实际 {alpha:.4f}\"\n        # 验证量级在合理范围（10~25%）\n        assert 10.0 < alpha < 25.0, (\n            f\"alpha 应在 10~25% 范围，实际 {alpha:.4f}%\"\n        )\n\n    def test_compute_alpha_spy_unavailable(self):\n        \"\"\"SPY 数据为 None → alpha = 0.0（降级处理，不抛异常）。\"\"\"\n        idx = pd.date_range(\"2021-01-01\", periods=100, freq=\"B\")\n        strat_returns = pd.Series(np.random.normal(0.001, 0.01, 100), index=idx)\n\n        # spy_returns=None\n        assert _compute_alpha(strat_returns, None) == 0.0\n        # spy_returns=空 Series\n        empty_spy = pd.Series(dtype=float)\n        assert _compute_alpha(strat_returns, empty_spy) == 0.0\n\n    def test_compute_alpha_strategy_underperforms(self):\n        \"\"\"策略跑输 SPY → alpha 为负。\"\"\"\n        idx = pd.date_range(\"2021-01-01\", periods=252, freq=\"B\")\n        # 策略日均 0.0001 (0.01%)，SPY 日均 0.001 (0.1%)\n        strat_returns = pd.Series(np.random.normal(0.0001, 0.005, 252), index=idx)\n        spy_returns = pd.Series(np.random.normal(0.001, 0.002, 252), index=idx)\n\n        alpha = _compute_alpha(strat_returns, spy_returns)\n        assert alpha < 0.0, (\n            f\"策略跑输 SPY 时 alpha 应为负，实际 {alpha:.4f}\"\n        )\n\n    def test_combine_daily_returns_basic(self):\n        \"\"\"等权合并组内日收益率序列。\"\"\"\n        idx = pd.date_range(\"2021-01-01\", periods=10, freq=\"B\")\n        r1 = pd.Series([0.001] * 10, index=idx)\n        r2 = pd.Series([0.003] * 10, index=idx)\n        results = [\n            SingleBacktestResult(\"S1\", \"s\", {}, 0.0, 0, 0, 0, 0, r1),\n            SingleBacktestResult(\"S2\", \"s\", {}, 0.0, 0, 0, 0, 0, r2),\n        ]\n        combined = _combine_daily_returns(results)\n        # 等权平均：(0.001 + 0.003) / 2 = 0.002\n        assert len(combined) == 10\n        assert all(abs(v - 0.002) < 1e-9 for v in combined)\n\n    def test_combine_daily_returns_empty(self):\n        \"\"\"空列表 → 空 Series。\"\"\"\n        combined = _combine_daily_returns([])\n        assert combined.empty\n\n    def test_min_sortino_threshold_constant(self):\n        \"\"\"MIN_SORTINO_THRESHOLD = 0.5（spec §4.2 硬约束）。\"\"\"\n        assert MIN_SORTINO_THRESHOLD == 0.5, (\n            f\"MIN_SORTINO_THRESHOLD 应为 0.5（迭代 #9 spec），\"\n            f\"实际 {MIN_SORTINO_THRESHOLD}\"\n        )\n\n\nclass TestAlphaBasedTopKSelection:\n    \"\"\"top-K 选择逻辑从 Sortino 改为 Alpha 的集成测试。\"\"\"\n\n    def test_top_k_selection_uses_alpha(self, tmp_path):\n        \"\"\"top-K 排序使用 Alpha 而非 Sortino。\n\n        场景：策略 A 的 Sortino 高于 B，但 B 的 Alpha 高于 A。\n        应选择 B（高 alpha）而非 A（高 Sortino）。\n\n        构造方法：用 patch 拦截 _backtest_one，返回受控的 daily_returns。\n        \"\"\"\n        from unittest.mock import patch\n\n        # 构造 SPY 数据：温和上涨（年化 ~10%）\n        n = 300\n        idx = pd.date_range(\"2021-01-01\", periods=n, freq=\"B\")\n        spy_close = [100.0 * (1.0004 ** i) for i in range(n)]  # ~10% 年化\n        spy_df = pd.DataFrame({\n            \"open\": [c - 0.1 for c in spy_close],\n            \"high\": [c + 0.5 for c in spy_close],\n            \"low\": [c - 0.5 for c in spy_close],\n            \"close\": spy_close,\n            \"volume\": [1_000_000] * n,\n        }, index=idx)\n        spy_returns = spy_df[\"close\"].pct_change().dropna()\n\n        # 策略 A (dual_ma): 低波动低收益 → 高 Sortino 但低 alpha\n        # 日均 0.0004（~10% 年化，与 SPY 持平 → alpha ≈ 0）\n        np.random.seed(42)\n        returns_a = pd.Series(\n            np.random.normal(0.0004, 0.002, n), index=idx\n        )\n        # 策略 B (rsi_mean_revert): 高波动高收益 → 低 Sortino 但高 alpha\n        # 日均 0.0011（~32% 年化，远超 SPY → alpha ≈ 22%）\n        returns_b = pd.Series(\n            np.random.normal(0.0011, 0.008, n), index=idx\n        )\n\n        # 验证测试前提：A 的 Sortino > B 的 Sortino，B 的 alpha > A 的 alpha\n        sortino_a = _compute_sortino(returns_a)\n        sortino_b = _compute_sortino(returns_b)\n        alpha_a = _compute_alpha(returns_a, spy_returns)\n        alpha_b = _compute_alpha(returns_b, spy_returns)\n        assert sortino_a > sortino_b, (\n            f\"测试前提失败：A 的 Sortino({sortino_a:.4f}) 应 > B({sortino_b:.4f})\"\n        )\n        assert alpha_b > alpha_a, (\n            f\"测试前提失败：B 的 alpha({alpha_b:.4f}) 应 > A({alpha_a:.4f})\"\n        )\n\n        # Mock _backtest_one 返回受控结果\n        def mock_backtest_one(df, strategy, params, *args, **kwargs):\n            sym = df.index.name or \"SYM\"\n            if strategy == \"dual_ma\":\n                return SingleBacktestResult(\n                    sym, strategy, params, 1.0, 10.0, 5.0, 55.0, 10, returns_a\n                )\n            else:  # rsi_mean_revert\n                return SingleBacktestResult(\n                    sym, strategy, params, 1.0, 30.0, 8.0, 50.0, 10, returns_b\n                )\n\n        # 构造 mock store：返回 SPY + 普通上涨数据\n        df_up = _make_ohlcv(n, trend=\"up\")\n        store = MagicMock()\n\n        def get_bars_multi(symbols, start, end, timeframe=\"1d\"):\n            mapping = {\"AAPL\": df_up, \"SPY\": spy_df}\n            return {s: mapping[s] for s in symbols if s in mapping}\n\n        store.get_bars_multi.side_effect = get_bars_multi\n\n        universe = MagicMock()\n        universe.get_groups.return_value = {\"test_group\": [\"AAPL\"]}\n\n        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=1)\n\n        with patch(\n            \"mytrader.backtest.matrix_backtest._backtest_one\",\n            side_effect=mock_backtest_one,\n        ):\n            report = mb.run(\n                strategies=[\"dual_ma\", \"rsi_mean_revert\"],\n                param_grids={\n                    \"dual_ma\": {\"fast\": [5], \"slow\": [20]},\n                    \"rsi_mean_revert\": {\n                        \"period\": [14], \"oversold\": [30], \"overbought\": [70]\n                    },\n                },\n            )\n\n        # 验证：选择了 rsi_mean_revert（高 alpha）而非 dual_ma（高 Sortino）\n        weights = report.groups[\"test_group\"]\n        assert len(weights) == 1, f\"top_k=1 应只选 1 个策略，实际 {len(weights)}\"\n        assert weights[0][\"strategy\"] == \"rsi_mean_revert\", (\n            f\"应选择高 alpha 的 rsi_mean_revert，\"\n            f\"实际选择了 {weights[0]['strategy']}（高 Sortino 的 dual_ma）\"\n        )\n        # backtest_alpha 字段应反映 B 的高 alpha\n        assert weights[0][\"backtest_alpha\"] > 5.0, (\n            f\"B 的 alpha 应 > 5%，实际 {weights[0]['backtest_alpha']:.4f}\"\n        )\n\n    def test_sortino_filter_excludes_garbage(self, tmp_path):\n        \"\"\"Sortino < 0.5 的候选被过滤（即使 alpha 高也不选）。\n\n        场景：构造一个 Sortino < 0.5 的\"垃圾\"策略 A，和一个 Sortino > 0.5 的正常策略 B。\n        即使 A 的 alpha 略高，也应被 Sortino 门槛排除。\n\n        注：由于 Sortino 门槛是 Tier 1 过滤，若无候选通过门槛，会触发 Tier 2 fallback\n        放宽门槛。本测试构造\"至少有一个正常候选\"的场景验证 Tier 1 正常工作。\n        \"\"\"\n        from unittest.mock import patch\n\n        n = 300\n        idx = pd.date_range(\"2021-01-01\", periods=n, freq=\"B\")\n        # SPY 温和上涨\n        spy_close = [100.0 * (1.0004 ** i) for i in range(n)]\n        spy_df = pd.DataFrame({\n            \"open\": [c - 0.1 for c in spy_close],\n            \"high\": [c + 0.5 for c in spy_close],\n            \"low\": [c - 0.5 for c in spy_close],\n            \"close\": spy_close,\n            \"volume\": [1_000_000] * n,\n        }, index=idx)\n        spy_returns = spy_df[\"close\"].pct_change().dropna()\n\n        # 垃圾策略 A：极低 Sortino（高下行波动）+ 高 alpha（靠总体高收益）\n        # 构造大起大落的收益序列：均值高但下行波动大\n        np.random.seed(42)\n        returns_a = pd.Series(\n            np.concatenate([\n                np.random.normal(0.003, 0.015, 200),   # 高波动高收益\n                np.random.normal(-0.005, 0.01, 100),   # 大幅下行\n            ]),\n            index=idx,\n        )\n        # 正常策略 B：稳定收益，Sortino > 0.5\n        returns_b = pd.Series(\n            np.random.normal(0.0008, 0.003, n), index=idx\n        )\n\n        sortino_a = _compute_sortino(returns_a)\n        sortino_b = _compute_sortino(returns_b)\n        # 验证前提：A 的 Sortino < 0.5（垃圾），B 的 Sortino > 0.5（正常）\n        assert sortino_a < MIN_SORTINO_THRESHOLD, (\n            f\"A 应为 Sortino < 0.5 的垃圾策略，实际 {sortino_a:.4f}\"\n        )\n        assert sortino_b > MIN_SORTINO_THRESHOLD, (\n            f\"B 应为 Sortino > 0.5 的正常策略，实际 {sortino_b:.4f}\"\n        )\n\n        def mock_backtest_one(df, strategy, params, *args, **kwargs):\n            sym = df.index.name or \"SYM\"\n            if strategy == \"dual_ma\":\n                return SingleBacktestResult(\n                    sym, strategy, params, 0.5, 15.0, 10.0, 50.0, 5, returns_a\n                )\n            else:  # rsi_mean_revert\n                return SingleBacktestResult(\n                    sym, strategy, params, 1.0, 20.0, 5.0, 55.0, 10, returns_b\n                )\n\n        df_up = _make_ohlcv(n, trend=\"up\")\n        store = MagicMock()\n        store.get_bars_multi.side_effect = lambda symbols, start, end, timeframe=\"1d\": {\n            s: {\"AAPL\": df_up, \"SPY\": spy_df}[s] for s in symbols\n            if s in {\"AAPL\", \"SPY\"}\n        }\n\n        universe = MagicMock()\n        universe.get_groups.return_value = {\"test_group\": [\"AAPL\"]}\n\n        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=1)\n        with patch(\n            \"mytrader.backtest.matrix_backtest._backtest_one\",\n            side_effect=mock_backtest_one,\n        ):\n            report = mb.run(\n                strategies=[\"dual_ma\", \"rsi_mean_revert\"],\n                param_grids={\n                    \"dual_ma\": {\"fast\": [5], \"slow\": [20]},\n                    \"rsi_mean_revert\": {\n                        \"period\": [14], \"oversold\": [30], \"overbought\": [70]\n                    },\n                },\n            )\n\n        weights = report.groups[\"test_group\"]\n        assert len(weights) == 1\n        # 应选择 rsi_mean_revert（Sortino > 0.5），排除 dual_ma（Sortino < 0.5）\n        assert weights[0][\"strategy\"] == \"rsi_mean_revert\", (\n            f\"应排除 Sortino < 0.5 的 dual_ma，选择 rsi_mean_revert，\"\n            f\"实际选择了 {weights[0]['strategy']}\"\n        )\n\n    def test_dd_filter_still_applies(self, tmp_path):\n        \"\"\"DD > 20% 的候选被过滤（即使 alpha 高也不通过 DD 硬约束）。\n\n        场景：构造 rsi_mean_revert 在持续下跌数据上产生大 DD 的策略行为。\n        验证：dd_constrained=True（触发 DD fallback），权重仍产出。\n        \"\"\"\n        store = MagicMock()\n        # 构造先涨后崩数据：rsi_mean_revert 会在下跌中超卖买入，持续持仓导致大 DD\n        n = 400\n        idx = pd.date_range(\"2021-01-01\", periods=n, freq=\"B\")\n        close = (\n            [100.0 * (1 - 0.002 * i) for i in range(200)]   # 缓慢下跌压低 RSI\n            + [60.0 * (1 - 0.005 * (i - 200)) for i in range(200, n)]  # 急速崩溃\n        )\n        close = [max(c, 1.0) for c in close]\n        df_crash = pd.DataFrame({\n            \"open\": [c - 0.3 for c in close],\n            \"high\": [c + 0.5 for c in close],\n            \"low\": [c - 0.5 for c in close],\n            \"close\": close,\n            \"volume\": [1_000_000] * n,\n        }, index=idx)\n        # 同时提供 SPY 数据（让 alpha 计算不降级）\n        spy_df = _make_ohlcv(n, trend=\"up\")\n        spy_df = spy_df.copy()\n        spy_df.index = idx  # 对齐索引\n\n        def get_bars_multi(symbols, start, end, timeframe=\"1d\"):\n            mapping = {\"AAPL\": df_crash, \"SPY\": spy_df}\n            return {s: mapping[s] for s in symbols if s in mapping}\n\n        store.get_bars_multi.side_effect = get_bars_multi\n\n        universe = MagicMock()\n        universe.get_groups.return_value = {\"volatile_group\": [\"AAPL\"]}\n\n        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=1)\n        report = mb.run(\n            strategies=[\"rsi_mean_revert\"],\n            param_grids={\"rsi_mean_revert\": {\n                \"period\": [14], \"oversold\": [35], \"overbought\": [65]\n            }},\n            output_file=tmp_path / \"weights_dd.json\",\n        )\n\n        # 验证：DD 超标时 dd_constrained=True（DD fallback 触发）\n        has_weights = any(weights for weights in report.groups.values() if weights)\n        if has_weights:\n            for gid, weights in report.groups.items():\n                for w in weights:\n                    if w.get(\"backtest_max_drawdown\", 0) > MAX_PORTFOLIO_DRAWDOWN_PCT:\n                        assert w[\"dd_constrained\"] is True, (\n                            f\"{gid}: DD={w['backtest_max_drawdown']:.1f}% > \"\n                            f\"{MAX_PORTFOLIO_DRAWDOWN_PCT}% 但 dd_constrained 为 False\"\n                        )\n\n    def test_fallback_when_no_sortino_compliant(self, tmp_path):\n        \"\"\"所有候选 Sortino < 0.5 → 触发 Tier 2 fallback（放宽 Sortino 门槛）。\n\n        场景：构造低 Sortino 的策略，但 DD ≤ 20%。\n        验证：权重仍产出（不空），dd_constrained=False（因为 DD 合规），\n        且日志中应有 \"Sortino filter relaxed\" 警告。\n        \"\"\"\n        from unittest.mock import patch\n        from loguru import logger\n\n        n = 300\n        idx = pd.date_range(\"2021-01-01\", periods=n, freq=\"B\")\n        spy_df = pd.DataFrame({\n            \"open\": [99.9], \"high\": [100.5], \"low\": [99.5],\n            \"close\": [100.0], \"volume\": [1_000_000],\n        }, index=idx[:1])\n        # 让 SPY 数据足够长\n        spy_close = [100.0 * (1.0004 ** i) for i in range(n)]\n        spy_df = pd.DataFrame({\n            \"open\": [c - 0.1 for c in spy_close],\n            \"high\": [c + 0.5 for c in spy_close],\n            \"low\": [c - 0.5 for c in spy_close],\n            \"close\": spy_close,\n            \"volume\": [1_000_000] * n,\n        }, index=idx)\n\n        # 低 Sortino 但 DD 合规的收益序列\n        np.random.seed(42)\n        returns_garbage = pd.Series(\n            np.concatenate([\n                np.random.normal(0.0002, 0.01, 200),  # 低均值高波动\n                np.random.normal(-0.0001, 0.008, 100), # 略负\n            ]),\n            index=idx,\n        )\n        # 验证前提：Sortino < 0.5（垃圾门槛）\n        assert _compute_sortino(returns_garbage) < MIN_SORTINO_THRESHOLD\n\n        def mock_backtest_one(df, strategy, params, *args, **kwargs):\n            sym = df.index.name or \"SYM\"\n            return SingleBacktestResult(\n                sym, strategy, params, 0.3, 5.0, 10.0, 50.0, 3, returns_garbage\n            )\n\n        df_up = _make_ohlcv(n, trend=\"up\")\n        store = MagicMock()\n        store.get_bars_multi.side_effect = lambda symbols, start, end, timeframe=\"1d\": {\n            s: {\"AAPL\": df_up, \"SPY\": spy_df}[s] for s in symbols\n            if s in {\"AAPL\", \"SPY\"}\n        }\n\n        universe = MagicMock()\n        universe.get_groups.return_value = {\"test_group\": [\"AAPL\"]}\n\n        # 捕获 WARNING 日志\n        msgs: list[str] = []\n        handler_id = logger.add(lambda m: msgs.append(str(m)), level=\"WARNING\")\n\n        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=1)\n        try:\n            with patch(\n                \"mytrader.backtest.matrix_backtest._backtest_one\",\n                side_effect=mock_backtest_one,\n            ):\n                report = mb.run(\n                    strategies=[\"dual_ma\"],\n                    param_grids={\"dual_ma\": {\"fast\": [5], \"slow\": [20]}},\n                )\n        finally:\n            logger.remove(handler_id)\n\n        # 验证：fallback 触发，日志记录 Sortino 放宽\n        assert any(\"Sortino filter relaxed\" in m for m in msgs), (\n            f\"应触发 Tier 2 fallback（Sortino relaxed），实际日志: {msgs}\"\n        )\n\n        # 权重仍产出（DD 合规），dd_constrained=False\n        weights = report.groups.get(\"test_group\", [])\n        if weights:\n            for w in weights:\n                assert w[\"dd_constrained\"] is False, (\n                    \"DD 合规时 dd_constrained 应为 False（Sortino fallback 不影响）\"\n                )\n\n    def test_fallback_when_no_dd_compliant(self, tmp_path):\n        \"\"\"所有候选 DD > 20% → 触发 Tier 3 fallback（按 DD 升序）。\n\n        场景：复用 test_fallback_when_no_compliant_candidates 的数据构造，\n        验证 dd_constrained=True（与迭代 #3 行为一致）。\n        \"\"\"\n        store = MagicMock()\n        n = 400\n        idx = pd.date_range(\"2021-01-01\", periods=n, freq=\"B\")\n        close = (\n            [100.0 * (1 - 0.002 * i) for i in range(200)]\n            + [60.0 * (1 - 0.005 * (i - 200)) for i in range(200, n)]\n        )\n        close = [max(c, 1.0) for c in close]\n        df_crash = pd.DataFrame({\n            \"open\": [c - 0.3 for c in close],\n            \"high\": [c + 0.5 for c in close],\n            \"low\": [c - 0.5 for c in close],\n            \"close\": close,\n            \"volume\": [1_000_000] * n,\n        }, index=idx)\n        # SPY 数据（让 alpha 不降级，验证 DD fallback 优先于 Sortino 过滤）\n        spy_close = [100.0 * (1.0004 ** i) for i in range(n)]\n        spy_df = pd.DataFrame({\n            \"open\": [c - 0.1 for c in spy_close],\n            \"high\": [c + 0.5 for c in spy_close],\n            \"low\": [c - 0.5 for c in spy_close],\n            \"close\": spy_close,\n            \"volume\": [1_000_000] * n,\n        }, index=idx)\n\n        def get_bars_multi(symbols, start, end, timeframe=\"1d\"):\n            mapping = {\"AAPL\": df_crash, \"SPY\": spy_df}\n            return {s: mapping[s] for s in symbols if s in mapping}\n\n        store.get_bars_multi.side_effect = get_bars_multi\n\n        universe = MagicMock()\n        universe.get_groups.return_value = {\"volatile_group\": [\"AAPL\", \"MSFT\"]}\n\n        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)\n        report = mb.run(\n            strategies=[\"rsi_mean_revert\"],\n            param_grids={\"rsi_mean_revert\": {\n                \"period\": [14], \"oversold\": [35], \"overbought\": [65]\n            }},\n            output_file=tmp_path / \"weights_fallback_dd.json\",\n        )\n\n        has_weights = any(weights for weights in report.groups.values() if weights)\n        if has_weights:\n            for gid, weights in report.groups.items():\n                for w in weights:\n                    if w.get(\"backtest_max_drawdown\", 0) > MAX_PORTFOLIO_DRAWDOWN_PCT:\n                        assert w[\"dd_constrained\"] is True, (\n                            f\"{gid}: DD={w['backtest_max_drawdown']:.1f}% > 20% \"\n                            f\"但 dd_constrained 为 False（Tier 3 应触发）\"\n                        )\n\n    def test_alpha_field_in_weights_json(self, mock_store, mock_universe, tmp_path):\n        \"\"\"strategy_weights.json 每个权重条目含 backtest_alpha 字段。\"\"\"\n        output = tmp_path / \"weights_with_alpha.json\"\n        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)\n        mb.run(\n            strategies=[\"dual_ma\"],\n            param_grids={\"dual_ma\": {\"fast\": [5], \"slow\": [20]}},\n            output_file=output,\n        )\n        data = json.loads(output.read_text())\n        for gid, weights in data[\"groups\"].items():\n            for w in weights:\n                assert \"backtest_alpha\" in w, (\n                    f\"{gid}: 权重条目缺少 backtest_alpha 字段，\"\n                    f\"实际 keys={list(w.keys())}\"\n                )\n                assert isinstance(w[\"backtest_alpha\"], (int, float)), (\n                    f\"{gid}: backtest_alpha 应为数值，\"\n                    f\"实际 {type(w['backtest_alpha'])}\"\n                )\n\n    def test_group_results_have_backtest_alpha(self, mock_store, mock_universe):\n        \"\"\"GroupBacktestResult.backtest_alpha 是浮点数（迭代 #9 新增字段）。\"\"\"\n        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)\n        report = mb.run(\n            strategies=[\"dual_ma\"],\n            param_grids={\"dual_ma\": {\"fast\": [5], \"slow\": [20]}},\n        )\n        for gr in report.group_results:\n            assert isinstance(gr.backtest_alpha, float), (\n                f\"backtest_alpha 应为 float，实际 {type(gr.backtest_alpha)}\"\n            )\n\n    def test_per_strategy_best_params_uses_alpha(self, tmp_path):\n        \"\"\"per-strategy best params 选择使用 Alpha 而非 Sharpe。\n\n        场景：两个参数组合 A (fast=5, slow=20) 和 B (fast=10, slow=50)，\n        A 的 Sharpe 高但 alpha 低，B 的 Sharpe 低但 alpha 高。\n        验证最终 GroupBacktestResult.params 是 B（高 alpha）。\n        \"\"\"\n        from unittest.mock import patch\n\n        n = 300\n        idx = pd.date_range(\"2021-01-01\", periods=n, freq=\"B\")\n        spy_close = [100.0 * (1.0004 ** i) for i in range(n)]\n        spy_df = pd.DataFrame({\n            \"open\": [c - 0.1 for c in spy_close],\n            \"high\": [c + 0.5 for c in spy_close],\n            \"low\": [c - 0.5 for c in spy_close],\n            \"close\": spy_close,\n            \"volume\": [1_000_000] * n,\n        }, index=idx)\n        spy_returns = spy_df[\"close\"].pct_change().dropna()\n\n        # 参数 A 的收益：低波动低收益 → 高 Sharpe 但低 alpha\n        np.random.seed(42)\n        returns_a = pd.Series(\n            np.random.normal(0.0005, 0.002, n), index=idx  # 与 SPY 接近，alpha≈0\n        )\n        # 参数 B 的收益：高波动高收益 → 低 Sharpe 但高 alpha\n        returns_b = pd.Series(\n            np.random.normal(0.0012, 0.008, n), index=idx  # 远超 SPY，alpha>0\n        )\n\n        # 验证前提\n        sharpe_a = _compute_sharpe(returns_a)\n        sharpe_b = _compute_sharpe(returns_b)\n        alpha_a = _compute_alpha(returns_a, spy_returns)\n        alpha_b = _compute_alpha(returns_b, spy_returns)\n        assert sharpe_a > sharpe_b, (\n            f\"A 的 Sharpe({sharpe_a:.4f}) 应 > B({sharpe_b:.4f})\"\n        )\n        assert alpha_b > alpha_a, (\n            f\"B 的 alpha({alpha_b:.4f}) 应 > A({alpha_a:.4f})\"\n        )\n\n        # 根据参数选择返回不同收益\n        def mock_backtest_one(df, strategy, params, *args, **kwargs):\n            sym = df.index.name or \"SYM\"\n            if params.get(\"fast\") == 5:  # 参数 A\n                return SingleBacktestResult(\n                    sym, strategy, params, sharpe_a, 10.0, 5.0, 55.0, 10, returns_a\n                )\n            else:  # 参数 B (fast=10)\n                return SingleBacktestResult(\n                    sym, strategy, params, sharpe_b, 30.0, 8.0, 50.0, 10, returns_b\n                )\n\n        df_up = _make_ohlcv(n, trend=\"up\")\n        store = MagicMock()\n        store.get_bars_multi.side_effect = lambda symbols, start, end, timeframe=\"1d\": {\n            s: {\"AAPL\": df_up, \"SPY\": spy_df}[s] for s in symbols\n            if s in {\"AAPL\", \"SPY\"}\n        }\n\n        universe = MagicMock()\n        universe.get_groups.return_value = {\"test_group\": [\"AAPL\"]}\n\n        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=1)\n        with patch(\n            \"mytrader.backtest.matrix_backtest._backtest_one\",\n            side_effect=mock_backtest_one,\n        ):\n            report = mb.run(\n                strategies=[\"dual_ma\"],\n                param_grids={\n                    \"dual_ma\": {\"fast\": [5, 10], \"slow\": [20, 50]}\n                },\n            )\n\n        # 验证：选择参数 B（fast=10, slow=50，高 alpha）\n        gr = next(\n            (r for r in report.group_results if r.group_id == \"test_group\"),\n            None,\n        )\n        assert gr is not None, \"应至少有一个 GroupBacktestResult\"\n        assert gr.params.get(\"fast\") == 10, (\n            f\"应选高 alpha 的参数 B (fast=10)，实际选了 {gr.params}\"\n        )\n        assert gr.backtest_alpha > 5.0, (\n            f\"B 的 alpha 应 > 5%，实际 {gr.backtest_alpha:.4f}\"\n        )\n\n\nclass TestEnsembleWeightsUsesAlpha:\n    \"\"\"_optimize_ensemble_weights 从 Sharpe 改为 Alpha。\"\"\"\n\n    def test_ensemble_weights_use_alpha(self):\n        \"\"\"两个策略的权重应基于 alpha 分配，alpha 高的策略权重大。\"\"\"\n        n = 252\n        idx = pd.date_range(\"2021-01-01\", periods=n, freq=\"B\")\n        spy_returns = pd.Series(np.random.normal(0.0004, 0.001, n), index=idx)\n\n        # 策略 A：alpha=0（与 SPY 持平）\n        returns_a = pd.Series(np.random.normal(0.0004, 0.003, n), index=idx)\n        # 策略 B：alpha 高（远超 SPY）\n        returns_b = pd.Series(np.random.normal(0.0012, 0.005, n), index=idx)\n\n        results_a = [SingleBacktestResult(\n            \"S1\", \"strat_a\", {}, 1.0, 10.0, 5.0, 55.0, 10, returns_a\n        )]\n        results_b = [SingleBacktestResult(\n            \"S2\", \"strat_b\", {}, 1.5, 30.0, 8.0, 50.0, 10, returns_b\n        )]\n\n        group_results = [\n            (\"strat_a\", {}, results_a),\n            (\"strat_b\", {}, results_b),\n        ]\n\n        weights = _optimize_ensemble_weights(group_results, spy_returns=spy_returns)\n\n        # B 的 alpha 更高 → 权重应更大\n        weights_dict = {s: w for s, _, w in weights}\n        assert weights_dict[\"strat_b\"] > weights_dict[\"strat_a\"], (\n            f\"B 的 alpha 更高，权重应大于 A，\"\n            f\"实际 A={weights_dict['strat_a']:.4f}, B={weights_dict['strat_b']:.4f}\"\n        )\n        # 权重和 = 1.0\n        total = sum(weights_dict.values())\n        assert abs(total - 1.0) < 1e-6, f\"权重和应为 1.0，实际 {total:.6f}\"\n\n    def test_ensemble_weights_spy_unavailable_degrades_to_equal(self):\n        \"\"\"SPY 数据不可用时 alpha 降级为 0 → 退化为等权。\"\"\"\n        n = 100\n        idx = pd.date_range(\"2021-01-01\", periods=n, freq=\"B\")\n        returns_a = pd.Series(np.random.normal(0.001, 0.005, n), index=idx)\n        returns_b = pd.Series(np.random.normal(0.002, 0.008, n), index=idx)\n\n        results_a = [SingleBacktestResult(\n            \"S1\", \"strat_a\", {}, 1.0, 10.0, 5.0, 55.0, 10, returns_a\n        )]\n        results_b = [SingleBacktestResult(\n            \"S2\", \"strat_b\", {}, 1.5, 30.0, 8.0, 50.0, 10, returns_b\n        )]\n\n        group_results = [\n            (\"strat_a\", {}, results_a),\n            (\"strat_b\", {}, results_b),\n        ]\n\n        # spy_returns=None → alpha=0 → 退化为等权（max(0, 0.01)）\n        weights = _optimize_ensemble_weights(group_results, spy_returns=None)\n        weights_dict = {s: w for s, _, w in weights}\n        # 等权：各 0.5\n        assert abs(weights_dict[\"strat_a\"] - 0.5) < 1e-6\n        assert abs(weights_dict[\"strat_b\"] - 0.5) < 1e-6\n\n    def test_ensemble_weights_single_strategy(self):\n        \"\"\"单策略时直接返回权重 1.0。\"\"\"\n        n = 100\n        idx = pd.date_range(\"2021-01-01\", periods=n, freq=\"B\")\n        returns = pd.Series(np.random.normal(0.001, 0.005, n), index=idx)\n        results = [SingleBacktestResult(\n            \"S1\", \"strat_a\", {}, 1.0, 10.0, 5.0, 55.0, 10, returns\n        )]\n\n        weights = _optimize_ensemble_weights(\n            [(\"strat_a\", {}, results)],\n            spy_returns=pd.Series(dtype=float),\n        )\n        assert len(weights) == 1\n        assert weights[0][0] == \"strat_a\"\n        assert weights[0][2] == 1.0\n", "old_string": "            val_months=4,\n        )\n        assert len(report.rounds) == 2\n        assert report.rounds[0].round_num == 1\n        assert report.rounds[1].round_num == 2", "replace_all": false}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py
---
现在
---
让我先
---
专门
---
运行一下
---
新测试：
---
{"command": "/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_matrix_backtest.py::TestAlphaComputation tests/test_matrix_backtest.py::TestAlphaBasedTopKSelection tests/test_matrix_backtest.py::TestEnsembleWeightsUsesAlpha -v 2>&1 | tail -50", "description": "Run new alpha tests"}
---
Run new alpha tests
---
Command: /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_matrix_backtest.py::TestAlphaComputation tests/test_matrix_backtest.py::TestAlphaBasedTopKSelection tests/test_matrix_backtest.py::TestEnsembleWeightsUsesAlpha -v 2>&1 | tail -50
Stdout: ============================= test session starts ==============================
platform darwin -- Python 3.12.13, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/rickouyang/Github/trade-tools/mytrader
configfile: pyproject.toml
plugins: cov-7.1.0, anyio-4.13.0
collected 17 items

tests/test_matrix_backtest.py .................                          [100%]

============================== 17 passed in 3.42s ==============================

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
全部
---
 17 个新测试
---
均已通过。现在让我
---
运行完整的 `
---
matrix
---
_backtest` 测试
---
文件以
---
检查是否存在回归问题：
---
{"command": "/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_matrix_backtest.py -q 2>&1 | tail -10", "description": "Run all matrix_backtest tests"}
---
Run all matrix_backtest tests
---
Command: /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_matrix_backtest.py -q 2>&1 | tail -10
Stdout: ........................................................................ [ 96%]
...                                                                      [100%]

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"command": "/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_matrix_backtest.py 2>&1 | tail -3", "description": "Run all matrix_backtest tests with count"}
---
Run all matrix_backtest tests with count
---
Command: /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_matrix_backtest.py 2>&1 | tail -3
Stdout: ........................................................................ [ 96%]
...                                                                      [100%]
75 passed in 6.59s

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
75
---
 个测试已
---
通过（58 个原有
---
 + 17 个新增
---
）。我再
---
运行一下 `portfolio_back
---
test` 测试，
---
因为它们会
---
用到
---
这些
---
权重
---
：
---
{"command": "/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_portfolio_backtest.py 2>&1 | tail -5", "description": "Run portfolio_backtest tests"}
---
Run portfolio_backtest tests
---
Command: /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_portfolio_backtest.py 2>&1 | tail -5
Stdout: ..................................                                       [100%]
34 passed in 3.76s

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"status": "completed", "taskId": "6"}
---
Updated task #6 status
---
Updated task #6 status
---
{"status": "in_progress", "taskId": "7"}
---
Updated task #7 status
---
Updated task #7 status
---
现在
---
让我运行完整的默认 pytest
---
 
---
套件，以确保
---
没有其他
---
功能
---
损坏
---
：
---
{"command": "/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest 2>&1 | tail -10", "description": "Run full pytest suite"}
---
Run full pytest suite
---
Command: /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest 2>&1 | tail -10
Stdout: tests/test_risk_manager.py::TestOrderIntent::test_auto_client_order_id
  /Users/rickouyang/Github/trade-tools/mytrader/tests/test_risk_manager.py:393: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    timestamp=datetime.utcnow(),

tests/test_risk_manager.py::TestOrderIntent::test_custom_client_order_id
  /Users/rickouyang/Github/trade-tools/mytrader/tests/test_risk_manager.py:408: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    timestamp=datetime.utcnow(),

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
602 passed, 16 deselected, 103 warnings in 15.47s

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
Excellent
---
! 
---
602 tests
---
 passed (was
---
 585 +
---
 17 new =
---
 602). The
---
 16 deselected are
---
 the live tests (isol
---
ated by default per
---
 iter #6
---
).


---
Now I
---
 need to update
---
 the documentation:
1.
---
 alignment/iteration_trajectory.md
---
 - Add
---
 Iter
---
 #9 entry
2
---
. .
---
codebuddy/CODE
---
BUDDY.md -
---
 Update test count and
---
 iter
---
 #9
---
 status
3. designs
---
/design_v2/07
---
-backtest-module.md -
---
 Document
---
 alpha
---
-based selection

Let me
---
 check
---
 the design
---
 docs
---
 first.
---
60
---
2 个测试通过
---
（之前
---
是
---
 585 + 
---
17 个新增 =
---
 60
---
2），
---
0
---
 个失败。现在让我
---
来
---
更新文档。
---
{"command": "ls /Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/ | head -20", "description": "List design v2 docs"}
---
List design v2 docs
---
Command: ls /Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/ | head -20
Stdout: 00-overview.md
01-data-layer.md
02-strategy-engine.md
03-signal-filter.md
04-risk-manager.md
05-execution-engine.md
06-portfolio-tracker.md
07-backtest-module.md
08-monitor-layer.md
09-infrastructure.md
10-market-data-store.md
11-universe-manager.md
12-strategy-matrix.md
13-signal-ranker.md
CHANGELOG.md
claude_review.md
glm_review.md

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"command": "grep -n \"Sortino\\|top-K\\|top_k\\|Sortino 排序\\|ensemble\" /Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md | head -30", "description": "Find Sortino/top-K mentions in design doc"}
---
Find Sortino/top-K mentions in design doc
---
Command: grep -n "Sortino\|top-K\|top_k\|Sortino 排序\|ensemble" /Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md | head -30
Stdout: 163:| **Sortino Ratio** ⭐ | 下行风险调整后收益（**Constitution L1 首要 KPI**） | > 1.5，> 2.5 优秀 | `Sortino Ratio`（矩阵回测中手算，见 §10.4） |
172:> ⚠️ **Sortino 计算口径（迭代 #1 确认）**：
173:> - 单标的层面：vectorbt 1.0.0 `pf.stats()` 含 `Sortino Ratio`，可直接读取
174:> - 矩阵回测层面（**组组合 Sortino**）：**必须手算**，因为 Sortino 是比率不可直接平均。正确做法是等权合并组内日收益率序列，再算下行偏差。`matrix_backtest.py::_compute_sortino()` 实现此公式，与 `_compute_sharpe()` 同口径（target=0、年化因子 252、退化返回 0.0）。这样保证单标的/组合口径一致，且不依赖 vectorbt stats 键名（曾发生 `Annualized Return [%]` 被移除的破坏性变更）。
184:# Sharpe Ratio/Calmar Ratio/Omega Ratio/Sortino Ratio
370:        # 4. 搜索组合权重（ensemble），若组合 Sharpe > 单策略最优则采用组合
371:        weighted = optimize_ensemble_weights(top_strategies, data, symbols)
383:| **组合 Sortino**（迭代 #1 新增） | 与组合 Sharpe 同口径：等权合并日收益率 → `_compute_sortino(combined)` | Constitution L1 首要 KPI；比率不可直接平均；与 Sharpe 同口径保证可比 |
389:| **实盘 ensemble 对齐** | MatrixBacktest 的 ensemble 权重优化须在"单点离散值聚合"语义下验证 | 实盘只取 iloc[-1] 单点离散值加权，与序列级加权不等价，权重必须在相同语义下产出 |

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"command": "grep -n \"^## \\|^### \" /Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md | head -30", "description": "Find sections in design doc"}
---
Find sections in design doc
---
Command: grep -n "^## \|^### " /Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md | head -30
Stdout: 8:## 1. 职责
26:## 2. 为什么选 VectorBT
41:## 3. VectorBT 基本用法
43:### 3.1 最简单的回测（VectorBT 1.0.0 实际用法）
82:### 3.2 参数优化（网格搜索，当前实现方式）
117:## 4. 与策略层集成
156:## 5. 回测绩效指标
189:## 6. 回测常见陷阱与防范
191:### 6.1 前视偏差（Look-ahead Bias）⚠️ 头号风险
206:### 6.2 过拟合
239:### 6.3 幸存者偏差
247:### 6.4 交易成本低估
256:### 6.5 流动性假设
266:## 7. 报告输出
288:## 8. 目录结构（Phase 1 已实现）
304:## 9. 注意点
314:## 10. 矩阵回测（MatrixBacktest，v2 新增）
319:### 10.1 目标
327:### 10.2 回测窗口：为什么是 5 年
339:### 10.3 矩阵回测流程
378:### 10.4 关键设计点
392:### 10.5 Walk-Forward 月度重优化
425:### 10.6 输出文件
435:### 10.7 性能考量
448:## 参考来源

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"file_path": "/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md", "limit": 90, "offset": 339}
---
 339→### 10.3 矩阵回测流程
 340→
 341→```python
 342→def run_matrix_backtest(universe: UniverseManager,
 343→                        store: MarketDataStore,
 344→                        strategies: list[str],
 345→                        param_grids: dict,
 346→                        years: int = 5) -> dict:
 347→    weights = {"groups": {}}
 348→    groups = universe.get_groups()              # {group_id: [symbols]}
 349→
 350→    for group_id, symbols in groups.items():
 351→        # 1. 读该组所有标的的 5 年数据（DuckDB 列式）
 352→        data = store.get_bars_multi(symbols, start=today - years*365, end=today)
 353→
 354→        # 2. 对每个策略 × 每组参数，在组内所有标的上回测
 355→        #    ⚠️ 不能直接取 Sharpe 算术平均（Sharpe 是比率，直接平均无统计意义）
 356→        #    正确做法：将组内所有标的日收益率等权合并为组合序列，计算组合 Sharpe
 357→        candidates = []
 358→        for strategy in strategies:
 359→            for params in grid_combinations(param_grids[strategy]):
 360→                results = [backtest_one(data[s], strategy, params) for s in symbols]
 361→                # 等权合并日收益率序列 → 计算组合 Sharpe
 362→                returns_df = pd.concat([r.daily_returns for r in results], axis=1)
 363→                portfolio_returns = returns_df.mean(axis=1)
 364→                portfolio_sharpe = compute_sharpe(portfolio_returns)
 365→                candidates.append((strategy, params, portfolio_sharpe))
 366→
 367→        # 3. 每个策略保留其最优参数，按 avg_sharpe 排序，取 Top-K 策略
 368→        top_strategies = select_top_per_strategy(candidates, k=2)
 369→
 370→        # 4. 搜索组合权重（ensemble），若组合 Sharpe > 单策略最优则采用组合
 371→        weighted = optimize_ensemble_weights(top_strategies, data, symbols)
 372→
 373→        weights["groups"][group_id] = weighted
 374→
 375→    return weights
 376→```
 377→
 378→### 10.4 关键设计点
 379→
 380→| 设计点 | 做法 | 理由 |
 381→|--------|------|------|
 382→| **组内取平均** | 等权合并组内日收益率序列，计算组合 Sharpe（而非直接平均各标的 Sharpe 比率） | 避免单只过拟合；Sharpe 是比率，不能直接平均；需要组合视角 |
 383→| **组合 Sortino**（迭代 #1 新增） | 与组合 Sharpe 同口径：等权合并日收益率 → `_compute_sortino(combined)` | Constitution L1 首要 KPI；比率不可直接平均；与 Sharpe 同口径保证可比 |
 384→| **组合 Max Drawdown**（迭代 #2 新增） | 等权合并组内日收益率 → cumprod → cummax → drawdown → max，返回正百分数 | Constitution L1 DD≤20% 硬约束；DD 是路径依赖比率不可直接平均；per-stock avg DD 虚高（无分散化效应） |
 385→| **NaN 安全处理**（迭代 #2 新增） | `_safe_float()` 拦截 NaN/None/Inf；`_safe_mean()` 拦截空列表/全 NaN | vectorbt 无交易时 stats 返回 NaN；`NaN or 0.0` 仍为 NaN（NaN 是 truthy）导致 JSON 序列化失败 |
 386→| **策略名校验**（迭代 #1 新增） | `_run_group` 进入策略循环前检查 `strategy not in STRATEGY_REGISTRY` → `logger.warning` + `continue` | 防止策略名拼写错误被静默跳过（迭代 #1 修复的 bug：`main.py` 误用 `"rsi"/"macd"/"bollinger"` 简称导致 3 个策略 6 天未跑） |
 387→| **参数按组** | 同组共用参数，不对单只优化 | 防过拟合（详见 02-strategy-engine.md 6.3） |
 388→| **历史分组对齐** | 矩阵回测使用 point-in-time 分组（按回测时间点重算波动率），而非当前静态分组 | 避免回测静态分组而实盘动态分组导致回测/实盘不一致 |
 389→| **实盘 ensemble 对齐** | MatrixBacktest 的 ensemble 权重优化须在"单点离散值聚合"语义下验证 | 实盘只取 iloc[-1] 单点离散值加权，与序列级加权不等价，权重必须在相同语义下产出 |
 390→| **Walk-Forward** | 滚动训练窗口，月度重优化 | 平衡过拟合与适应性 |
 391→
 392→### 10.5 Walk-Forward 月度重优化
 393→
 394→```
 395→训练窗口 5 年 → 优化权重 → 应用 1 个月（样本外）→ 滚动前移 → 重新优化
 396→
 397→调度（APScheduler）：
 398→  每月第一个交易日 00:00 触发 run_matrix_backtest()
 399→  → 更新 strategy_weights.json
 400→  → StrategyMatrixRunner.reload_weights() 热加载
 401→```
 402→
 403→为什么是月度（设计访谈确认）：
 404→
 405→```
 406→更新太频繁（每天）→ 拟合近期噪音，权重翻转，策略左右打脸
 407→更新太慢（每年）  → 行情切换时反应迟钝
 408→每月 ≈ 21 交易日  → 足够样本外数据验证上轮权重，换手率可控
 409→```
 410→
 411→**窗口重叠率讨论：**
 412→
 413→```
 414→当前方案：训练 5 年 + 步进 1 个月 → 重叠率 = 59/60 ≈ 98.3%
 415→→ 权重变化缓慢（惯性大），但保证了统计稳健性
 416→→ 代价：市场突变时（如 2022 熊市初期）权重适应较慢
 417→
 418→改进方向（Phase 5 后续可选）：
 419→  方案 A：缩短训练窗口至 2-3 年，降低重叠率 → 适应性更强，但统计样本减少
 420→  方案 B：时间衰减权重（指数衰减 λ≈0.97/天）→ 近期数据权重更高，
 421→           等效训练窗口约 1-1.5 年，无需改变窗口长度
 422→  方案 C：双窗口验证：短窗口（1年）+ 长窗口（5年）权重取交集，兼顾适应性与稳健性
 423→```
 424→
 425→### 10.6 输出文件
 426→
 427→```
 428→config/strategy_weights.json   # StrategyMatrixRunner 实盘读取
 429→
---
 339→### 10.3 矩阵回测流程
 340→
 341→```python
 342→def run_matrix_backtest(universe: UniverseManager,
 343→                        store: MarketDataStore,
 344→                        strategies: list[str],
 345→                        param_grids: dict,
 346→                        years: int = 5) -> dict:
 347→    weights = {"groups": {}}
 348→    groups = universe.get_groups()              # {group_id: [symbols]}
 349→
 350→    for group_id, symbols in groups.items():
 351→        # 1. 读该组所有标的的 5 年数据（DuckDB 列式）
 352→        data = store.get_bars_multi(symbols, start=today - years*365, end=today)
 353→
 354→        # 2. 对每个策略 × 每组参数，在组内所有标的上回测
 355→        #    ⚠️ 不能直接取 Sharpe 算术平均（Sharpe 是比率，直接平均无统计意义）
 356→        #    正确做法：将组内所有标的日收益率等权合并为组合序列，计算组合 Sharpe
 357→        candidates = []
 358→        for strategy in strategies:
 359→            for params in grid_combinations(param_grids[strategy]):
 360→                results = [backtest_one(data[s], strategy, params) for s in symbols]
 361→                # 等权合并日收益率序列 → 计算组合 Sharpe
 362→                returns_df = pd.concat([r.daily_returns for r in results], axis=1)
 363→                portfolio_returns = returns_df.mean(axis=1)
 364→                portfolio_sharpe = compute_sharpe(portfolio_returns)
 365→                candidates.append((strategy, params, portfolio_sharpe))
 366→
 367→        # 3. 每个策略保留其最优参数，按 avg_sharpe 排序，取 Top-K 策略
 368→        top_strategies = select_top_per_strategy(candidates, k=2)
 369→
 370→        # 4. 搜索组合权重（ensemble），若组合 Sharpe > 单策略最优则采用组合
 371→        weighted = optimize_ensemble_weights(top_strategies, data, symbols)
 372→
 373→        weights["groups"][group_id] = weighted
 374→
 375→    return weights
 376→```
 377→
 378→### 10.4 关键设计点
 379→
 380→| 设计点 | 做法 | 理由 |
 381→|--------|------|------|
 382→| **组内取平均** | 等权合并组内日收益率序列，计算组合 Sharpe（而非直接平均各标的 Sharpe 比率） | 避免单只过拟合；Sharpe 是比率，不能直接平均；需要组合视角 |
 383→| **组合 Sortino**（迭代 #1 新增） | 与组合 Sharpe 同口径：等权合并日收益率 → `_compute_sortino(combined)` | Constitution L1 首要 KPI；比率不可直接平均；与 Sharpe 同口径保证可比 |
 384→| **组合 Max Drawdown**（迭代 #2 新增） | 等权合并组内日收益率 → cumprod → cummax → drawdown → max，返回正百分数 | Constitution L1 DD≤20% 硬约束；DD 是路径依赖比率不可直接平均；per-stock avg DD 虚高（无分散化效应） |
 385→| **NaN 安全处理**（迭代 #2 新增） | `_safe_float()` 拦截 NaN/None/Inf；`_safe_mean()` 拦截空列表/全 NaN | vectorbt 无交易时 stats 返回 NaN；`NaN or 0.0` 仍为 NaN（NaN 是 truthy）导致 JSON 序列化失败 |
 386→| **策略名校验**（迭代 #1 新增） | `_run_group` 进入策略循环前检查 `strategy not in STRATEGY_REGISTRY` → `logger.warning` + `continue` | 防止策略名拼写错误被静默跳过（迭代 #1 修复的 bug：`main.py` 误用 `"rsi"/"macd"/"bollinger"` 简称导致 3 个策略 6 天未跑） |
 387→| **参数按组** | 同组共用参数，不对单只优化 | 防过拟合（详见 02-strategy-engine.md 6.3） |
 388→| **历史分组对齐** | 矩阵回测使用 point-in-time 分组（按回测时间点重算波动率），而非当前静态分组 | 避免回测静态分组而实盘动态分组导致回测/实盘不一致 |
 389→| **实盘 ensemble 对齐** | MatrixBacktest 的 ensemble 权重优化须在"单点离散值聚合"语义下验证 | 实盘只取 iloc[-1] 单点离散值加权，与序列级加权不等价，权重必须在相同语义下产出 |
 390→| **Walk-Forward** | 滚动训练窗口，月度重优化 | 平衡过拟合与适应性 |
 391→
 392→### 10.5 Walk-Forward 月度重优化
 393→
 394→```
 395→训练窗口 5 年 → 优化权重 → 应用 1 个月（样本外）→ 滚动前移 → 重新优化
 396→
 397→调度（APScheduler）：
 398→  每月第一个交易日 00:00 触发 run_matrix_backtest()
 399→  → 更新 strategy_weights.json
 400→  → StrategyMatrixRunner.reload_weights() 热加载
 401→```
 402→
 403→为什么是月度（设计访谈确认）：
 404→
 405→```
 406→更新太频繁（每天）→ 拟合近期噪音，权重翻转，策略左右打脸
 407→更新太慢（每年）  → 行情切换时反应迟钝
 408→每月 ≈ 21 交易日  → 足够样本外数据验证上轮权重，换手率可控
 409→```
 410→
 411→**窗口重叠率讨论：**
 412→
 413→```
 414→当前方案：训练 5 年 + 步进 1 个月 → 重叠率 = 59/60 ≈ 98.3%
 415→→ 权重变化缓慢（惯性大），但保证了统计稳健性
 416→→ 代价：市场突变时（如 2022 熊市初期）权重适应较慢
 417→
 418→改进方向（Phase 5 后续可选）：
 419→  方案 A：缩短训练窗口至 2-3 年，降低重叠率 → 适应性更强，但统计样本减少
 420→  方案 B：时间衰减权重（指数衰减 λ≈0.97/天）→ 近期数据权重更高，
 421→           等效训练窗口约 1-1.5 年，无需改变窗口长度
 422→  方案 C：双窗口验证：短窗口（1年）+ 长窗口（5年）权重取交集，兼顾适应性与稳健性
 423→```
 424→
 425→### 10.6 输出文件
 426→
 427→```
 428→config/strategy_weights.json   # StrategyMatrixRunner 实盘读取
 429→
---
{"file_path": "/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md", "limit": 25, "offset": 425}
---
 425→### 10.6 输出文件
 426→
 427→```
 428→config/strategy_weights.json   # StrategyMatrixRunner 实盘读取
 429→reports/matrix_backtest/        # 每次矩阵回测的详细报告（各组各策略指标）
 430→    {date}/
 431→        group_summary.csv       # 各组 Top 策略对比
 432→        {group_id}_detail.csv   # 单组各策略各参数明细
 433→```
 434→
 435→### 10.7 性能考量
 436→
 437→```
 438→N 策略(4) × 参数网格(~20) × G 组(假设 9 组) × 组内标的(~60)
 439→= 4 × 20 × 9 × 60 = ~43,200 次单标的回测
 440→
 441→VectorBT 向量化 + DuckDB 列式读取：
 442→  单次回测 ~10ms → 43,200 × 10ms ≈ 7 分钟
 443→→ 月度离线跑，7 分钟完全可接受
 444→```
 445→
 446→---
 447→
 448→## 参考来源
 449→
 450→
---
 425→### 10.6 输出文件
 426→
 427→```
 428→config/strategy_weights.json   # StrategyMatrixRunner 实盘读取
 429→reports/matrix_backtest/        # 每次矩阵回测的详细报告（各组各策略指标）
 430→    {date}/
 431→        group_summary.csv       # 各组 Top 策略对比
 432→        {group_id}_detail.csv   # 单组各策略各参数明细
 433→```
 434→
 435→### 10.7 性能考量
 436→
 437→```
 438→N 策略(4) × 参数网格(~20) × G 组(假设 9 组) × 组内标的(~60)
 439→= 4 × 20 × 9 × 60 = ~43,200 次单标的回测
 440→
 441→VectorBT 向量化 + DuckDB 列式读取：
 442→  单次回测 ~10ms → 43,200 × 10ms ≈ 7 分钟
 443→→ 月度离线跑，7 分钟完全可接受
 444→```
 445→
 446→---
 447→
 448→## 参考来源
 449→
 450→
---
现在
---
，
---
让我更新设计文档，
---
以添加 Iter
---
 #9 alpha
---
 部分
---
：
---
{"file_path": "/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md", "new_string": "### 10.4 关键设计点\n\n| 设计点 | 做法 | 理由 |\n|--------|------|------|\n| **组内取平均** | 等权合并组内日收益率序列，计算组合 Sharpe（而非直接平均各标的 Sharpe 比率） | 避免单只过拟合；Sharpe 是比率，不能直接平均；需要组合视角 |\n| **组合 Sortino**（迭代 #1 新增） | 与组合 Sharpe 同口径：等权合并日收益率 → `_compute_sortino(combined)` | Constitution L1 首要 KPI；比率不可直接平均；与 Sharpe 同口径保证可比 |\n| **组合 Max Drawdown**（迭代 #2 新增） | 等权合并组内日收益率 → cumprod → cummax → drawdown → max，返回正百分数 | Constitution L1 DD≤20% 硬约束；DD 是路径依赖比率不可直接平均；per-stock avg DD 虚高（无分散化效应） |\n| **NaN 安全处理**（迭代 #2 新增） | `_safe_float()` 拦截 NaN/None/Inf；`_safe_mean()` 拦截空列表/全 NaN | vectorbt 无交易时 stats 返回 NaN；`NaN or 0.0` 仍为 NaN（NaN 是 truthy）导致 JSON 序列化失败 |\n| **策略名校验**（迭代 #1 新增） | `_run_group` 进入策略循环前检查 `strategy not in STRATEGY_REGISTRY` → `logger.warning` + `continue` | 防止策略名拼写错误被静默跳过（迭代 #1 修复的 bug：`main.py` 误用 `\"rsi\"/\"macd\"/\"bollinger\"` 简称导致 3 个策略 6 天未跑） |\n| **DD 硬约束 + Fallback**（迭代 #3 新增） | top-K 选择时过滤 `portfolio_max_drawdown > 20%` 的候选；若全部超标 → 按 DD 升序取 top-K，标记 `dd_constrained=True` | Constitution L1 DD≤20% 是硬约束；无合规候选时仍需产出权重（结构性问题不能阻塞回测） |\n| **Alpha 排序 + Sortino 门槛**（迭代 #9 新增） | top-K 排序从 Sortino 改为 Alpha（策略年化收益 - SPY 同期年化收益）；新增 `Sortino > 0.5` 最低质量门槛 | Sortino 高 ≠ 年化高（均值回归策略天然高 Sortino 低绝对收益，alpha 为负）；Alpha 排序直接优化超额收益目标；Sortino 门槛保证基本下行质量。三级 fallback：Tier 1 DD+Sortino → Tier 2 仅 DD → Tier 3 DD 升序 |\n| **SPY Benchmark 获取**（迭代 #9 新增） | `_get_spy_returns(start, end)` 从 MarketDataStore 拉取 SPY 日收益率；`_compute_alpha(strat, spy)` 计算年化 alpha | SPY 不可用时 alpha 降级为 0.0（不阻塞回测），所有候选 alpha=0 ��退化为原顺序 |\n| **per-strategy best params 用 Alpha**（迭代 #9 新增） | 每个策略的最优参数选择从 Sharpe 改为 Alpha | 与 top-K 排序口径一致，避免 per-strategy 用 Sharpe 选低收益高稳定的参数 |\n| **ensemble weights 用 Alpha**（迭代 #9 新增） | `_optimize_ensemble_weights` 接收 `spy_returns` 参数，权重计算从 Sharpe 改为 Alpha | 与 top-K 排序口径一致，ensemble 权重直接反映\"跑赢 SPY 的程度\"；SPY 不可用时退化为等权 |\n| **参数按组** | 同组共用参数，不对单只优化 | 防过拟合（详见 02-strategy-engine.md 6.3） |\n| **历史分组对齐** | 矩阵回测使用 point-in-time 分组（按回测时间点重算波动率），而非当前静态分组 | 避免回测静态分组而实盘动态分组导致回测/实盘不一致 |\n| **实盘 ensemble 对齐** | MatrixBacktest 的 ensemble 权重优化须在\"单点离散值聚合\"语义下验证 | 实盘只取 iloc[-1] 单点离散值加权，与序列级加权不等价，权重必须在相同语义下产出 |\n| **Walk-Forward** | 滚动训练窗口，月度重优化 | 平衡过拟合与适应性 |\n\n### 10.4.1 Top-K 选择三级 Fallback（迭代 #9 新增）\n\n```\nTier 1: DD ≤ 20% AND Sortino > 0.5  →  Alpha 降序取 top-K\n   ↓ (若空)\nTier 2: DD ≤ 20%（放宽 Sortino）   →  Alpha 降序取 top-K，WARNING 日志\n   ↓ (若空)\nTier 3: 无 DD 合规候选              →  DD 升序取 top-K，dd_constrained=True\n```\n\n**设计动机**（iteration #9 spec §1-2）：\n- Constitution 目标：年化 20-30%（需 alpha +10~20%）\n- 旧逻辑：Sortino 降序 → 永远选均值回归策略 → 年化 8.02%，alpha = -11.34%\n- 新逻辑：Alpha 降序 → 直接优化超额收益目标\n- Sortino 门槛：避免选到\"高 alpha 但高下行波动\"的垃圾策略\n\n**Alpha 计算公式**：\n```python\nstrat_annual = (1 + strat_returns.mean()) ** 252 - 1\nspy_annual   = (1 + spy_returns.mean()) ** 252 - 1\nalpha_pct    = (strat_annual - spy_annual) * 100\n```\n\n**降级处理**：SPY 数据不可用 → alpha=0.0，所有候选 alpha 相等，\nPython 稳定排序保留原顺序（按策略列表顺序）。\n\n", "old_string": "### 10.4 关键设计点\n\n| 设计点 | 做法 | 理由 |\n|--------|------|------|\n| **组内取平均** | 等权合并组内日收益率序列，计算组合 Sharpe（而非直接平均各标的 Sharpe 比率） | 避免单只过拟合；Sharpe 是比率，不能直接平均；需要组合视角 |\n| **组合 Sortino**（迭代 #1 新增） | 与组合 Sharpe 同口径：等权合并日收益率 → `_compute_sortino(combined)` | Constitution L1 首要 KPI；比率不可直接平均；与 Sharpe 同口径保证可比 |\n| **组合 Max Drawdown**（迭代 #2 新增） | 等权合并组内日收益率 → cumprod → cummax → drawdown → max，返回正百分数 | Constitution L1 DD≤20% 硬约束；DD 是路径依赖比率不可直接平均；per-stock avg DD 虚高（无分散化效应） |\n| **NaN 安全处理**（迭代 #2 新增） | `_safe_float()` 拦截 NaN/None/Inf；`_safe_mean()` 拦截空列表/全 NaN | vectorbt 无交易时 stats 返回 NaN；`NaN or 0.0` 仍为 NaN（NaN 是 truthy）导致 JSON 序列化失败 |\n| **策略名校验**（迭代 #1 新增） | `_run_group` 进入策略循环前检查 `strategy not in STRATEGY_REGISTRY` → `logger.warning` + `continue` | 防止策略名拼写错误被静默跳过（迭代 #1 修复的 bug：`main.py` 误用 `\"rsi\"/\"macd\"/\"bollinger\"` 简称导致 3 个策略 6 天未跑） |\n| **参数按组** | 同组共用参数，不对单只优化 | 防过拟合（详见 02-strategy-engine.md 6.3） |\n| **历史分组对齐** | 矩阵回测使用 point-in-time 分组（按回测时间点重算波动率），而非当前静态分组 | 避免回测静态分组而实盘动态分组导致回测/实盘不一致 |\n| **实盘 ensemble 对齐** | MatrixBacktest 的 ensemble 权重优化须在\"单点离散值聚合\"语义下验证 | 实盘只取 iloc[-1] 单点离散值加权，与序列级加权不等价，权重必须在相同语义下产出 |\n| **Walk-Forward** | 滚动训练窗口，月度重优化 | 平衡过拟合与适应性 |\n", "replace_all": false}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md
---
现在
---
更新
---
 `strategy
---
_weights.json` 
---
部分
---
以记录新
---
字段。
---
让我检查一下该
---
部分：
---
{"file_path": "/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md", "limit": 15, "offset": 450}
---
 450→改进方向（Phase 5 后续可选）：
 451→  方案 A：缩短训练窗口至 2-3 年，降低重叠率 → 适应性更强，但统计样本减少
 452→  方案 B：时间衰减权重（指数衰减 λ≈0.97/天）→ 近期数据权重更高，
 453→           等效训练窗口约 1-1.5 年，无需改变窗口长度
 454→  方案 C：双窗口验证：短窗口（1年）+ 长窗口（5年）权重取交集，兼顾适应性与稳健性
 455→```
 456→
 457→### 10.6 输出文件
 458→
 459→```
 460→config/strategy_weights.json   # StrategyMatrixRunner 实盘读取
 461→reports/matrix_backtest/        # 每次矩阵回测的详细报告（各组各策略指标）
 462→    {date}/
 463→        group_summary.csv       # 各组 Top 策略对比
 464→        {group_id}_detail.csv   # 单组各策略各参数明细
 465→
---
 450→改进方向（Phase 5 后续可选）：
 451→  方案 A：缩短训练窗口至 2-3 年，降低重叠率 → 适应性更强，但统计样本减少
 452→  方案 B：时间衰减权重（指数衰减 λ≈0.97/天）→ 近期数据权重更高，
 453→           等效训练窗口约 1-1.5 年，无需改变窗口长度
 454→  方案 C：双窗口验证：短窗口（1年）+ 长窗口（5年）权重取交集，兼顾适应性与稳健性
 455→```
 456→
 457→### 10.6 输出文件
 458→
 459→```
 460→config/strategy_weights.json   # StrategyMatrixRunner 实盘读取
 461→reports/matrix_backtest/        # 每次矩阵回测的详细报告（各组各策略指标）
 462→    {date}/
 463→        group_summary.csv       # 各组 Top 策略对比
 464→        {group_id}_detail.csv   # 单组各策略各参数明细
 465→
---
{"file_path": "/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md", "new_string": "### 10.6 输出文件\n\n```\nconfig/strategy_weights.json   # StrategyMatrixRunner 实盘读取\nreports/matrix_backtest/        # 每次矩阵回测的详细报告（各组各策略指标）\n    {date}/\n        group_summary.csv       # 各组 Top 策略对比\n        {group_id}_detail.csv   # 单组各策略各参数明细\n```\n\n#### strategy_weights.json 字段说明\n\n```json\n{\n  \"strategy\": \"rsi_mean_revert\",\n  \"params\": {\"period\": 14, \"oversold\": 30, \"overbought\": 70},\n  \"weight\": 0.5,\n  \"backtest_sharpe\": 1.03,\n  \"backtest_sortino\": 1.61,\n  \"backtest_max_drawdown\": 1.78,\n  \"backtest_win_rate\": 0.50,\n  \"backtest_alpha\": 2.35,         // 迭代 #9 新增：vs SPY 的超额年化收益（百分数）\n  \"dd_constrained\": false,\n  \"backtest_dd_status\": \"pass\"\n}\n```", "old_string": "### 10.6 输出文件\n\n```\nconfig/strategy_weights.json   # StrategyMatrixRunner 实盘读取\nreports/matrix_backtest/        # 每次矩阵回测的详细报告（各组各策略指标）\n    {date}/\n        group_summary.csv       # 各组 Top 策略对比\n        {group_id}_detail.csv   # 单组各策略各参数明细\n```", "replace_all": false}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md
---
现在
---
更新 CHANGE
---
LOG：
---
{"file_path": "/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/CHANGELOG.md"}
---
   1→# Design Changelog
   2→
   3→> 记录设计文档的版本变更及变更理由，便于追溯决策来源。
   4→
   5→---
   6→
   7→## v2.2 — 2026-06-30（迭代 #1：策略名 bug 修复 + Sortino 指标）
   8→
   9→### 背景
  10→
  11→`--reoptimize` 产出的 `strategy_weights.json` 中 6 个组**全部只剩 `dual_ma`**，
  12→其余 3 个策略（rsi / macd / bollinger）被静默跳过。根因：`main.py::_run_reoptimize`
  13→传入的策略名 `["dual_ma","rsi","macd","bollinger"]` 与 `@register_strategy` 注册表
  14→中的实际名 `["dual_ma","rsi_mean_revert","macd_cross","bollinger_band"]` 不匹配，
  15→`_backtest_one` 内部 `STRATEGY_REGISTRY.get(name)` 返回 `None` 后静默 `return None`，
  16→仅 `_run_group` 层留下"no valid results"的 debug 日志，bug 隐藏 6 天未被发现。
  17→
  18→同时发现 Constitution L1 首要 KPI（**Sortino Ratio**）在矩阵回测中**完全未计算**，
  19→`strategy_weights.json` 仅含 `backtest_sharpe`，无法对"在 DD≤20% 约束下优化 Sortino"
  20→这一 Constitution 目标进行度量。
  21→
  22→### 修改清单
  23→
  24→| 优先级 | 问题 | 涉及文件 | 变更内容 |
  25→|--------|------|----------|---------|
  26→| P0 | `main.py` 策略名与注册表不匹配 | `main.py` | 策略名改为 `dual_ma`/`rsi_mean_revert`/`macd_cross`/`bollinger_band`；提取为模块级常量 `REOPTIMIZE_STRATEGIES` / `REOPTIMIZE_PARAM_GRIDS` 便于回归测试 |
  27→| P0 | 未注册策略被静默跳过 | `matrix_backtest.py` | `_run_group` 策略循环入口加 `if strategy not in STRATEGY_REGISTRY: logger.warning(...) + continue`（替代 `_backtest_one` 内部静默 `return None`） |
  28→| P0 | `examples/phase5_e2e.py` 同款策略名错误 | `examples/phase5_e2e.py` | `"macd"` → `"macd_cross"` |
  29→| P1 | 矩阵回测缺 Sortino（Constitution 首要 KPI） | `matrix_backtest.py` | 新增 `_compute_sortino()` + `_portfolio_sortino_from_results()`；`SingleBacktestResult.sortino` / `GroupBacktestResult.portfolio_sortino` 字段；`strategy_weights.json` 每条目输出 `backtest_sortino` |
  30→| P1 | 测试 `test_run_weights_sum_to_one` 有同款 bug | `tests/test_matrix_backtest.py` | `"rsi"` → `"rsi_mean_revert"`（原测试因单策略权重自然=1.0 而碰巧通过） |
  31→| P1 | 缺回归测试防策略名再次脱节 | `tests/test_matrix_backtest.py` | 新增 `test_reoptimize_strategy_names_match_registry`：断言 `REOPTIMIZE_STRATEGIES ⊆ STRATEGY_REGISTRY.keys()` |
  32→| P2 | 缺 Sortino 单元测试 | `tests/test_matrix_backtest.py` | 新增 `test_compute_sortino_*`（5 个）+ `test_portfolio_sortino_from_results` + `test_output_file_contains_sortino` + `test_group_results_have_portfolio_sortino` |
  33→| P2 | 缺未注册策略 WARNING 测试 | `tests/test_matrix_backtest.py` | 新增 `test_unknown_strategy_logs_warning` |
  34→| P2 | 设计文档策略名/字段不同步 | `07-backtest-module.md`, `12-strategy-matrix.md` | §5 指标表加 Sortino 行 + 计算口径说明；§10.4 加"组合 Sortino"+"策略名校验"设计点；`12` §3 JSON 示例修策略名 + 加 `backtest_sortino`；§9 风险缓解加 MatrixBacktest WARNING 校验 |
  35→
  36→### 不变项
  37→
  38→- 权重优化仍基于 **Sharpe**（`_optimize_ensemble_weights`）—— 切换为 Sortino 优化属行为变更，留待下一轮迭代单独评估（见 `alignment/decision_log.md`）
  39→- 4 策略参数网格不变（rsi/macd/bollinger 仍是单点默认参数）—— 扩参属"策略参数微调"另一轮迭代
  40→- `BacktestRunner`（单标的回测）不受影响，未改动
  41→
  42→### 影响范围
  43→
  44→- ✅ 向后兼容：`strategy_weights.json` 新增 `backtest_sortino` 字段，旧字段保留；`SingleBacktestResult.sortino` / `GroupBacktestResult.portfolio_sortino` 带 default 值，位置式构造不受影响
  45→- ⚠️ 行为变更：`--reoptimize` 重新产出后，6 个组中至少 3 组最优策略不再是 `dual_ma`（预期）
  46→- 🔲 下一轮迭代候选：(1) 权重优化目标 Sharpe→Sortino；(2) rsi/macd/bollinger 参数网格扩展；(3) 低波动组（SPX_low_vol Sortino 待度量）策略淘汰评估
  47→
  48→---
  49→
  50→## v2.1 — 2026-06-23（Claude 审查后修正）
  51→
  52→### 背景
  53→
  54→基于 glm_review.md 和 claude_review.md 的独立审查，修正设计文档中影响回测/实盘一致性的缺陷。
  55→
  56→### 修改清单
  57→
  58→| 优先级 | 问题 | 涉及文件 | 变更内容 |
  59→|--------|------|----------|---------|
  60→| P0 | #1 回测/实盘 ensemble 语义不等价 | `12-strategy-matrix.md` | §4 明确 ensemble 权重优化须在"单点离散值聚合"语义下进行，与实盘 iloc[-1] 加权等价 |
  61→| P0 | #2 事件型信号 iloc[-1] 漏单 | `12-strategy-matrix.md`, `09-infrastructure.md` | §6 改为检查最近 N bar 内信号有效期（`signal_valid_bars=3`，可配置） |
  62→| P0 | #16 矩阵回测缺 open 参数 | `07-backtest-module.md` | §3.1、§4、§9 全部补充 `open=open_series`，注明必须传入 |
  63→| P1 | #9 平均 Sharpe 计算错误 | `07-backtest-module.md` | §10.3 改为等权合并日收益率序列计算组合 Sharpe；`BacktestResult` 增加 `daily_returns` 字段 |
  64→| P1 | #3 fallback 复权混用 | `10-market-data-store.md` | §6 强制约束：fallback 时不写入（标记 degraded），等主源恢复；§8.2 升级为强制约束 |
  65→| P1 | #5 波动率分组静态 vs 动态 | `07-backtest-module.md`, `11-universe-manager.md` | §10.4 增加历史分组对齐设计点；`11` 补充 `recompute_volatility_tiers_at(date)` 接口 |
  66→| P1 | #6 Top-K 与风控约束未协调 | `13-signal-ranker.md`, `04-risk-manager.md` | §5 改为输出 Top-2K 候选供 Risk Manager 递补；§6 增加约束优先级说明 |
  67→| P2 | #4 幸存者偏差量化 | `11-universe-manager.md` | §8.2 补充偏差规模估算（5年~100只变动）和分组影响差异 |
  68→| P2 | #10 Walk-Forward 重叠讨论 | `07-backtest-module.md` | §10.5 补充窗口重叠率分析和改进方向（时间衰减权重等） |
  69→| P2 | #11 df 传参不一致 | `12-strategy-matrix.md` | §6 改为传完整 df（部分策略需要 high/low/volume） |
  70→| P2 | #14 隔夜跳空防护缺失 | `04-risk-manager.md` | 新增 §7.5 隔夜跳空风险管理（财报平仓/VIX 阈值/可配置开关） |
  71→| P2 | #18 时区混乱 | `09-infrastructure.md` | §2.1 区分 `timezone`（日志显示）和 `trading_timezone`（调度逻辑），明确时区策略 |
  72→| P3 | #7 DuckDB 性能声明不实 | `10-market-data-store.md` | 删除"快 10-100×"的不实数字，改为客观说明（42MB 下差别有限，可选 Parquet 优化） |
  73→| P3 | #8 5 年窗口描述错误 | `07-backtest-module.md` | §10.2 修正时间范围（2021-2026，不含 2020 崩盘），说明需 6 年才能覆盖 |
  74→| P3 | #12 Config 未更新到 v2 | `09-infrastructure.md` | §2.1 补充 v2 新增配置节（universe/strategy_matrix/signal_ranker/market_data_store） |
  75→| P3 | #13 SELL 资金结算 | `13-signal-ranker.md` | §8.1 补充使用 `buying_power` 字段避免结算时序问题 |
  76→| P3 | #17 半天交易日延迟 | `10-market-data-store.md` | §6 补充半天交易日说明（影响可忽略，可选 pandas_market_calendars 精确处理） |
  77→
  78→### 不变项
  79→- glm_review #15（fees 保守估计）：维持 `fees=0.001`，此为有益的保守假设；仅补充 slippage 注释
  80→- glm_review 对 #3 的 P0 评级：降为 P1（需 fallback 才触发，低频事件）
  81→
  82→---
  83→
  84→## v2.0 — 2026-06-23（Phase 5 设计访谈后重构）
  85→
  86→### 背景
  87→
  88→Phase 1-4 完成后，在规划 Phase 5 时发现：v1 设计把系统定位为
  89→**"单策略 × 固定几只股票 → 直接下单"的线性执行流水线**，缺少
  90→**"从大规模标的中筛选该交易标的"** 的核心环节。
  91→
  92→经过 5 轮设计访谈澄清需求后，将系统重构为
  93→**「离线回测层 + 在线交易层」双层架构**。本次变更不影响 Phase 1-4 已交付代码，
  94→仅更新设计文档（design_v2），作为 Phase 5 实现依据。
  95→
  96→### 访谈结论（决策来源）
  97→
  98→| # | 问题 | 结论 |
  99→|---|------|------|
 100→| Q1 | 系统定位 | **全自动交易系统**；策略开发由外部系统负责，本系统只做"回测验证 + 选股 + 执行" |
 101→| Q2 | 标的范围 | **S&P 500 + Nasdaq 100**（去重 ~550 只）；两组策略适配差异显著（均值回归 vs 动量） |
 102→| Q3 | 多策略聚合 | 组合本身即策略，权重需被回测验证；策略↔标的 mapping 数据驱动 |
 103→| Q4 | 参数粒度 | **按标的分组**优化参数（波动率/行业/市值），绝不对单只优化（防过拟合） |
 104→| Q5 | 回测→实盘 | 回测产出"策略×组"表现排名，实盘只执行排名 **Top-K** 的组合 |
 105→
 106→### 新增模块文档
 107→
 108→| 文件 | 模块 | 说明 |
 109→|------|------|------|
 110→| `10-market-data-store.md` | Market Data Store | 本地时序库（SQLite 实盘 / DuckDB 回测）+ DataSyncService 增量同步 |
 111→| `11-universe-manager.md` | Universe Manager | S&P 500 + Nasdaq 100 成分股维护、去重、按特征分组 |
 112→| `12-strategy-matrix.md` | Strategy Matrix Runner | M 策略 × N 标的批量运行，按组分配策略 |
 113→| `13-signal-ranker.md` | Signal Ranker | 多信号聚合、排名、Top-K 选股 |
 114→
 115→### 修改的既有文档
 116→
 117→| 文件 | 变更 | 理由 |
 118→|------|------|------|
 119→| `00-overview.md` | 重写：双层架构、模块清单扩展、v2 数据流、Phase 5 路线、关键参数表 | 系统定位从半自动→全自动；引入大规模选股 |
 120→| `01-data-layer.md` | 数据存储从"按请求 Parquet 缓存"改为"本地时序库 + 增量同步" | v1 缓存 key 含 start/end，滑动窗口导致全量重拉、触发限速 |
 121→| `02-strategy-engine.md` | 新增多策略调度、分组参数、数据驱动 mapping；ensemble 权重改为回测产出 | 支持多策略并行 + 防过拟合 |
 122→| `07-backtest-module.md` | 新增矩阵回测（第 10 节）：N策略×G组×参数网格、5年窗口、Walk-Forward 月度 | 产出实盘选股的 strategy_weights.json |
 123→
 124→### 关键技术决策及理由
 125→
 126→#### 1. 数据存储：本地时序库 + 增量同步（替代请求缓存）
 127→
 128→```
 129→变更：v1 按请求 Parquet 缓存 → v2 本地库（SQLite + DuckDB）+ 增量同步
 130→理由：
 131→  - v1 缓存 key=(symbol,start,end)，日期窗口滑动即全量重拉 → 触发 API 限速
 132→  - v2 增量只拉 delta（每天每只 ~1 根新 bar），盘中读本地库无网络
 133→  - 数据量仅 ~42MB（550只×5年），无需 MySQL，嵌入式 DB 足矣
 134→  - DuckDB 列式读取专为回测"批量读5年"场景优化，比 SQLite 快 10-100×
 135→```
 136→
 137→#### 2. 数据源：Alpaca 主 + yfinance 备
 138→
 139→```
 140→变更：v1 扫描直接调 yfinance → v2 DataSyncService 调 Alpaca（主）+ yfinance（备）
 141→理由：
 142→  - Alpaca 官方 API，限速可预测（200 req/min），支持多标的批量请求
 143→  - Alpaca v2/delayed_sip 免费全量 SIP（15min 延迟），数据质量优于 yfinance
 144→  - yfinance 是非官方爬虫，限速不透明，作 fallback / 回填补缺
 145→  - 增量架构下数据源延迟不再是实盘瓶颈（同步是收盘后离线批处理）
 146→```
 147→
 148→#### 3. 回测窗口：5 年（替代单标的 3 年）
 149→
 150→```
 151→变更：v1 单标的 3 年 → v2 全标的 5 年
 152→理由：
 153→  - 90 天/3 年覆盖行情不全，回测统计意义弱
 154→  - 5 年覆盖完整牛熊周期（2020崩盘+2021牛+2022熊+2023-24复苏）
 155→  - 不取 15 年：太老数据市场结构已变，相关性下降
 156→  - 区分两个 lookback：实盘扫描 90 天（够算指标）vs 回测 5 年（验证）
 157→```
 158→
 159→#### 4. 参数粒度：按组，不按单只
 160→
 161→```
 162→变更：v1 全局固定参数 → v2 按标的分组参数
 163→理由：
 164→  - 对 550 只各自优化 = 550 次独立优化 = 必然过拟合（多重比较）
 165→  - 按特征分组（波动率/行业/市值），组内共用参数，自由度可控
 166→  - 参数差异来自标的统计特征，不是标的本身
 167→```
 168→
 169→#### 5. 策略权重更新：每月 Walk-Forward
 170→
 171→```
 172→变更：v1 无更新机制 → v2 每月重优化
 173→理由：
 174→  - 更新太频繁（每天）→ 拟合噪音，权重翻转，策略左右打脸
 175→  - 更新太慢（每年）→ 行情切换反应迟钝
 176→  - 每月 ≈ 21 交易日，足够样本外验证，换手率可控
 177→```
 178→
 179→#### 6. Top-K = 5
 180→
 181→```
 182→变更：v1 无选股概念（全下单）→ v2 扫 550 只取 Top-5
 183→理由及代价：
 184→  - 集中高信念押注，靠 risk_per_trade=1% + 止损控风险（非分散）
 185→  - 代价：等权下每仓 20%，单只暴雷砸 20% 净值（主动选择的风格）
 186→  - 统计量足够：5/天 × 250 日 = 1250 笔/年，可验证策略 edge
 187→  - 未来想降波动可调 K 至 10-15
 188→```
 189→
 190→### 不变项（沿用 v1）
 191→
 192→- 策略纯函数设计 + 回测/实盘一致性原则
 193→- 前视偏差防护（强制 shift(1)）
 194→- Signal Filter / Risk Manager / Execution / Portfolio / Monitor 模块设计
 195→- 失败安全、可观测性、持仓真相来源等设计原则
 196→
 197→### 影响范围
 198→
 199→- ✅ 不影响 Phase 1-4 已交付代码（仅设计文档变更）
 200→- 🔲 Phase 5 按 design_v2 实现新增 4 模块 + 矩阵回测 + Walk-Forward 调度
 201→
 202→---
 203→
 204→## v1.0 — 2026-06-13（Phase 1 完成后）
 205→
 206→- 初始设计：9 个模块的线性执行流水线
 207→- 定位：轻量级日间交易系统，半自动执行
 208→- 详见 `../design_v1/`
 209→
---
   1→# Design Changelog
   2→
   3→> 记录设计文档的版本变更及变更理由，便于追溯决策来源。
   4→
   5→---
   6→
   7→## v2.2 — 2026-06-30（迭代 #1：策略名 bug 修复 + Sortino 指标）
   8→
   9→### 背景
  10→
  11→`--reoptimize` 产出的 `strategy_weights.json` 中 6 个组**全部只剩 `dual_ma`**，
  12→其余 3 个策略（rsi / macd / bollinger）被静默跳过。根因：`main.py::_run_reoptimize`
  13→传入的策略名 `["dual_ma","rsi","macd","bollinger"]` 与 `@register_strategy` 注册表
  14→中的实际名 `["dual_ma","rsi_mean_revert","macd_cross","bollinger_band"]` 不匹配，
  15→`_backtest_one` 内部 `STRATEGY_REGISTRY.get(name)` 返回 `None` 后静默 `return None`，
  16→仅 `_run_group` 层留下"no valid results"的 debug 日志，bug 隐藏 6 天未被发现。
  17→
  18→同时发现 Constitution L1 首要 KPI（**Sortino Ratio**）在矩阵回测中**完全未计算**，
  19→`strategy_weights.json` 仅含 `backtest_sharpe`，无法对"在 DD≤20% 约束下优化 Sortino"
  20→这一 Constitution 目标进行度量。
  21→
  22→### 修改清单
  23→
  24→| 优先级 | 问题 | 涉及文件 | 变更内容 |
  25→|--------|------|----------|---------|
  26→| P0 | `main.py` 策略名与注册表不匹配 | `main.py` | 策略名改为 `dual_ma`/`rsi_mean_revert`/`macd_cross`/`bollinger_band`；提取为模块级常量 `REOPTIMIZE_STRATEGIES` / `REOPTIMIZE_PARAM_GRIDS` 便于回归测试 |
  27→| P0 | 未注册策略被静默跳过 | `matrix_backtest.py` | `_run_group` 策略循环入口加 `if strategy not in STRATEGY_REGISTRY: logger.warning(...) + continue`（替代 `_backtest_one` 内部静默 `return None`） |
  28→| P0 | `examples/phase5_e2e.py` 同款策略名错误 | `examples/phase5_e2e.py` | `"macd"` → `"macd_cross"` |
  29→| P1 | 矩阵回测缺 Sortino（Constitution 首要 KPI） | `matrix_backtest.py` | 新增 `_compute_sortino()` + `_portfolio_sortino_from_results()`；`SingleBacktestResult.sortino` / `GroupBacktestResult.portfolio_sortino` 字段；`strategy_weights.json` 每条目输出 `backtest_sortino` |
  30→| P1 | 测试 `test_run_weights_sum_to_one` 有同款 bug | `tests/test_matrix_backtest.py` | `"rsi"` → `"rsi_mean_revert"`（原测试因单策略权重自然=1.0 而碰巧通过） |
  31→| P1 | 缺回归测试防策略名再次脱节 | `tests/test_matrix_backtest.py` | 新增 `test_reoptimize_strategy_names_match_registry`：断言 `REOPTIMIZE_STRATEGIES ⊆ STRATEGY_REGISTRY.keys()` |
  32→| P2 | 缺 Sortino 单元测试 | `tests/test_matrix_backtest.py` | 新增 `test_compute_sortino_*`（5 个）+ `test_portfolio_sortino_from_results` + `test_output_file_contains_sortino` + `test_group_results_have_portfolio_sortino` |
  33→| P2 | 缺未注册策略 WARNING 测试 | `tests/test_matrix_backtest.py` | 新增 `test_unknown_strategy_logs_warning` |
  34→| P2 | 设计文档策略名/字段不同步 | `07-backtest-module.md`, `12-strategy-matrix.md` | §5 指标表加 Sortino 行 + 计算口径说明；§10.4 加"组合 Sortino"+"策略名校验"设计点；`12` §3 JSON 示例修策略名 + 加 `backtest_sortino`；§9 风险缓解加 MatrixBacktest WARNING 校验 |
  35→
  36→### 不变项
  37→
  38→- 权重优化仍基于 **Sharpe**（`_optimize_ensemble_weights`）—— 切换为 Sortino 优化属行为变更，留待下一轮迭代单独评估（见 `alignment/decision_log.md`）
  39→- 4 策略参数网格不变（rsi/macd/bollinger 仍是单点默认参数）—— 扩参属"策略参数微调"另一轮迭代
  40→- `BacktestRunner`（单标的回测）不受影响，未改动
  41→
  42→### 影响范围
  43→
  44→- ✅ 向后兼容：`strategy_weights.json` 新增 `backtest_sortino` 字段，旧字段保留；`SingleBacktestResult.sortino` / `GroupBacktestResult.portfolio_sortino` 带 default 值，位置式构造不受影响
  45→- ⚠️ 行为变更：`--reoptimize` 重新产出后，6 个组中至少 3 组最优策略不再是 `dual_ma`（预期）
  46→- 🔲 下一轮迭代候选：(1) 权重优化目标 Sharpe→Sortino；(2) rsi/macd/bollinger 参数网格扩展；(3) 低波动组（SPX_low_vol Sortino 待度量）策略淘汰评估
  47→
  48→---
  49→
  50→## v2.1 — 2026-06-23（Claude 审查后修正）
  51→
  52→### 背景
  53→
  54→基于 glm_review.md 和 claude_review.md 的独立审查，修正设计文档中影响回测/实盘一致性的缺陷。
  55→
  56→### 修改清单
  57→
  58→| 优先级 | 问题 | 涉及文件 | 变更内容 |
  59→|--------|------|----------|---------|
  60→| P0 | #1 回测/实盘 ensemble 语义不等价 | `12-strategy-matrix.md` | §4 明确 ensemble 权重优化须在"单点离散值聚合"语义下进行，与实盘 iloc[-1] 加权等价 |
  61→| P0 | #2 事件型信号 iloc[-1] 漏单 | `12-strategy-matrix.md`, `09-infrastructure.md` | §6 改为检查最近 N bar 内信号有效期（`signal_valid_bars=3`，可配置） |
  62→| P0 | #16 矩阵回测缺 open 参数 | `07-backtest-module.md` | §3.1、§4、§9 全部补充 `open=open_series`，注明必须传入 |
  63→| P1 | #9 平均 Sharpe 计算错误 | `07-backtest-module.md` | §10.3 改为等权合并日收益率序列计算组合 Sharpe；`BacktestResult` 增加 `daily_returns` 字段 |
  64→| P1 | #3 fallback 复权混用 | `10-market-data-store.md` | §6 强制约束：fallback 时不写入（标记 degraded），等主源恢复；§8.2 升级为强制约束 |
  65→| P1 | #5 波动率分组静态 vs 动态 | `07-backtest-module.md`, `11-universe-manager.md` | §10.4 增加历史分组对齐设计点；`11` 补充 `recompute_volatility_tiers_at(date)` 接口 |
  66→| P1 | #6 Top-K 与风控约束未协调 | `13-signal-ranker.md`, `04-risk-manager.md` | §5 改为输出 Top-2K 候选供 Risk Manager 递补；§6 增加约束优先级说明 |
  67→| P2 | #4 幸存者偏差量化 | `11-universe-manager.md` | §8.2 补充偏差规模估算（5年~100只变动）和分组影响差异 |
  68→| P2 | #10 Walk-Forward 重叠讨论 | `07-backtest-module.md` | §10.5 补充窗口重叠率分析和改进方向（时间衰减权重等） |
  69→| P2 | #11 df 传参不一致 | `12-strategy-matrix.md` | §6 改为传完整 df（部分策略需要 high/low/volume） |
  70→| P2 | #14 隔夜跳空防护缺失 | `04-risk-manager.md` | 新增 §7.5 隔夜跳空风险管理（财报平仓/VIX 阈值/可配置开关） |
  71→| P2 | #18 时区混乱 | `09-infrastructure.md` | §2.1 区分 `timezone`（日志显示）和 `trading_timezone`（调度逻辑），明确时区策略 |
  72→| P3 | #7 DuckDB 性能声明不实 | `10-market-data-store.md` | 删除"快 10-100×"的不实数字，改为客观说明（42MB 下差别有限，可选 Parquet 优化） |
  73→| P3 | #8 5 年窗口描述错误 | `07-backtest-module.md` | §10.2 修正时间范围（2021-2026，不含 2020 崩盘），说明需 6 年才能覆盖 |
  74→| P3 | #12 Config 未更新到 v2 | `09-infrastructure.md` | §2.1 补充 v2 新增配置节（universe/strategy_matrix/signal_ranker/market_data_store） |
  75→| P3 | #13 SELL 资金结算 | `13-signal-ranker.md` | §8.1 补充使用 `buying_power` 字段避免结算时序问题 |
  76→| P3 | #17 半天交易日延迟 | `10-market-data-store.md` | §6 补充半天交易日说明（影响可忽略，可选 pandas_market_calendars 精确处理） |
  77→
  78→### 不变项
  79→- glm_review #15（fees 保守估计）：维持 `fees=0.001`，此为有益的保守假设；仅补充 slippage 注释
  80→- glm_review 对 #3 的 P0 评级：降为 P1（需 fallback 才触发，低频事件）
  81→
  82→---
  83→
  84→## v2.0 — 2026-06-23（Phase 5 设计访谈后重构）
  85→
  86→### 背景
  87→
  88→Phase 1-4 完成后，在规划 Phase 5 时发现：v1 设计把系统定位为
  89→**"单策略 × 固定几只股票 → 直接下单"的线性执行流水线**，缺少
  90→**"从大规模标的中筛选该交易标的"** 的核心环节。
  91→
  92→经过 5 轮设计访谈澄清需求后，将系统重构为
  93→**「离线回测层 + 在线交易层」双层架构**。本次变更不影响 Phase 1-4 已交付代码，
  94→仅更新设计文档（design_v2），作为 Phase 5 实现依据。
  95→
  96→### 访谈结论（决策来源）
  97→
  98→| # | 问题 | 结论 |
  99→|---|------|------|
 100→| Q1 | 系统定位 | **全自动交易系统**；策略开发由外部系统负责，本系统只做"回测验证 + 选股 + 执行" |
 101→| Q2 | 标的范围 | **S&P 500 + Nasdaq 100**（去重 ~550 只）；两组策略适配差异显著（均值回归 vs 动量） |
 102→| Q3 | 多策略聚合 | 组合本身即策略，权重需被回测验证；策略↔标的 mapping 数据驱动 |
 103→| Q4 | 参数粒度 | **按标的分组**优化参数（波动率/行业/市值），绝不对单只优化（防过拟合） |
 104→| Q5 | 回测→实盘 | 回测产出"策略×组"表现排名，实盘只执行排名 **Top-K** 的组合 |
 105→
 106→### 新增模块文档
 107→
 108→| 文件 | 模块 | 说明 |
 109→|------|------|------|
 110→| `10-market-data-store.md` | Market Data Store | 本地时序库（SQLite 实盘 / DuckDB 回测）+ DataSyncService 增量同步 |
 111→| `11-universe-manager.md` | Universe Manager | S&P 500 + Nasdaq 100 成分股维护、去重、按特征分组 |
 112→| `12-strategy-matrix.md` | Strategy Matrix Runner | M 策略 × N 标的批量运行，按组分配策略 |
 113→| `13-signal-ranker.md` | Signal Ranker | 多信号聚合、排名、Top-K 选股 |
 114→
 115→### 修改的既有文档
 116→
 117→| 文件 | 变更 | 理由 |
 118→|------|------|------|
 119→| `00-overview.md` | 重写：双层架构、模块清单扩展、v2 数据流、Phase 5 路线、关键参数表 | 系统定位从半自动→全自动；引入大规模选股 |
 120→| `01-data-layer.md` | 数据存储从"按请求 Parquet 缓存"改为"本地时序库 + 增量同步" | v1 缓存 key 含 start/end，滑动窗口导致全量重拉、触发限速 |
 121→| `02-strategy-engine.md` | 新增多策略调度、分组参数、数据驱动 mapping；ensemble 权重改为回测产出 | 支持多策略并行 + 防过拟合 |
 122→| `07-backtest-module.md` | 新增矩阵回测（第 10 节）：N策略×G组×参数网格、5年窗口、Walk-Forward 月度 | 产出实盘选股的 strategy_weights.json |
 123→
 124→### 关键技术决策及理由
 125→
 126→#### 1. 数据存储：本地时序库 + 增量同步（替代请求缓存）
 127→
 128→```
 129→变更：v1 按请求 Parquet 缓存 → v2 本地库（SQLite + DuckDB）+ 增量同步
 130→理由：
 131→  - v1 缓存 key=(symbol,start,end)，日期窗口滑动即全量重拉 → 触发 API 限速
 132→  - v2 增量只拉 delta（每天每只 ~1 根新 bar），盘中读本地库无网络
 133→  - 数据量仅 ~42MB（550只×5年），无需 MySQL，嵌入式 DB 足矣
 134→  - DuckDB 列式读取专为回测"批量读5年"场景优化，比 SQLite 快 10-100×
 135→```
 136→
 137→#### 2. 数据源：Alpaca 主 + yfinance 备
 138→
 139→```
 140→变更：v1 扫描直接调 yfinance → v2 DataSyncService 调 Alpaca（主）+ yfinance（备）
 141→理由：
 142→  - Alpaca 官方 API，限速可预测（200 req/min），支持多标的批量请求
 143→  - Alpaca v2/delayed_sip 免费全量 SIP（15min 延迟），数据质量优于 yfinance
 144→  - yfinance 是非官方爬虫，限速不透明，作 fallback / 回填补缺
 145→  - 增量架构下数据源延迟不再是实盘瓶颈（同步是收盘后离线批处理）
 146→```
 147→
 148→#### 3. 回测窗口：5 年（替代单标的 3 年）
 149→
 150→```
 151→变更：v1 单标的 3 年 → v2 全标的 5 年
 152→理由：
 153→  - 90 天/3 年覆盖行情不全，回测统计意义弱
 154→  - 5 年覆盖完整牛熊周期（2020崩盘+2021牛+2022熊+2023-24复苏）
 155→  - 不取 15 年：太老数据市场结构已变，相关性下降
 156→  - 区分两个 lookback：实盘扫描 90 天（够算指标）vs 回测 5 年（验证）
 157→```
 158→
 159→#### 4. 参数粒度：按组，不按单只
 160→
 161→```
 162→变更：v1 全局固定参数 → v2 按标的分组参数
 163→理由：
 164→  - 对 550 只各自优化 = 550 次独立优化 = 必然过拟合（多重比较）
 165→  - 按特征分组（波动率/行业/市值），组内共用参数，自由度可控
 166→  - 参数差异来自标的统计特征，不是标的本身
 167→```
 168→
 169→#### 5. 策略权重更新：每月 Walk-Forward
 170→
 171→```
 172→变更：v1 无更新机制 → v2 每月重优化
 173→理由：
 174→  - 更新太频繁（每天）→ 拟合噪音，权重翻转，策略左右打脸
 175→  - 更新太慢（每年）→ 行情切换反应迟钝
 176→  - 每月 ≈ 21 交易日，足够样本外验证，换手率可控
 177→```
 178→
 179→#### 6. Top-K = 5
 180→
 181→```
 182→变更：v1 无选股概念（全下单）→ v2 扫 550 只取 Top-5
 183→理由及代价：
 184→  - 集中高信念押注，靠 risk_per_trade=1% + 止损控风险（非分散）
 185→  - 代价：等权下每仓 20%，单只暴雷砸 20% 净值（主动选择的风格）
 186→  - 统计量足够：5/天 × 250 日 = 1250 笔/年，可验证策略 edge
 187→  - 未来想降波动可调 K 至 10-15
 188→```
 189→
 190→### 不变项（沿用 v1）
 191→
 192→- 策略纯函数设计 + 回测/实盘一致性原则
 193→- 前视偏差防护（强制 shift(1)）
 194→- Signal Filter / Risk Manager / Execution / Portfolio / Monitor 模块设计
 195→- 失败安全、可观测性、持仓真相来源等设计原则
 196→
 197→### 影响范围
 198→
 199→- ✅ 不影响 Phase 1-4 已交付代码（仅设计文档变更）
 200→- 🔲 Phase 5 按 design_v2 实现新增 4 模块 + 矩阵回测 + Walk-Forward 调度
 201→
 202→---
 203→
 204→## v1.0 — 2026-06-13（Phase 1 完成后）
 205→
 206→- 初始设计：9 个模块的线性执行流水线
 207→- 定位：轻量级日间交易系统，半自动执行
 208→- 详见 `../design_v1/`
 209→
---
{"file_path": "/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/CHANGELOG.md", "new_string": "# Design Changelog\n\n> 记录设计文档的版本变更及变更理由，便于追溯决策来源。\n\n---\n\n## v2.3 — 2026-07-05（迭代 #9：MatrixBacktest Alpha-Based Strategy Selection）\n\n### 背景\n\nIter #7 的 `--reoptimize` 暴露了根本矛盾：\n- Constitution 目标：年化 20-30%（需 alpha +10~20%）\n- MatrixBacktest 排序：Sortino 降序\n- 结果：选出 Sortino 最高的均值回归策略 → 年化 8.02% → alpha = -11.34%\n\n**Sortino 高 ≠ 年化高。** 均值回归策略天然有高 Sortino（低下行波动）\n但低绝对收益。用 Sortino 排序会系统性地排除能跑赢 SPY 的趋势策略。\nIter #8 新增的 `rsi_trend_filter` 也因此未能进入权重。\n\n### 修改清单\n\n| 优先级 | 问题 | 涉及文件 | 变更内容 |\n|--------|------|----------|---------|\n| P0 | top-K 排序用 Sortino → 永远选均值回归 → alpha 为负 | `matrix_backtest.py::_run_group` | top-K 排序从 Sortino 改为 Alpha（vs SPY） |\n| P0 | per-strategy best params 用 Sharpe → 偏好低波动 | `matrix_backtest.py::_run_group` | per-strategy best params 选择从 Sharpe 改为 Alpha |\n| P0 | ensemble weights 用 Sharpe → 与排序口径不一致 | `matrix_backtest.py::_optimize_ensemble_weights` | 权重计算从 Sharpe 改为 Alpha；新增 `spy_returns` 参数 |\n| P0 | 缺 SPY benchmark 数据获取 | `matrix_backtest.py::MatrixBacktest._get_spy_returns` | 新增方法从 MarketDataStore 拉取 SPY 日收益率 |\n| P0 | 缺 alpha 计算函数 | `matrix_backtest.py::_compute_alpha` | 新增模块级函数：`(strat_annual - spy_annual) * 100` |\n| P0 | 缺日收益率合并复用 | `matrix_backtest.py::_combine_daily_returns` | 新增 helper 提取等权合并逻辑，sharpe/sortino/alpha 共享 |\n| P1 | 缺 Sortino 最低质量门槛 | `matrix_backtest.py::MIN_SORTINO_THRESHOLD` | 新增常量 0.5，作为 top-K Tier 1 过滤；可放宽（Tier 2 fallback） |\n| P1 | GroupBacktestResult 缺 alpha 字段 | `matrix_backtest.py::GroupBacktestResult` | 新增 `backtest_alpha: float = 0.0` |\n| P1 | strategy_weights.json 缺 alpha 字段 | `matrix_backtest.py::_run_group` | 每条目新增 `backtest_alpha` 字段 |\n| P2 | 缺 alpha 相关测试 | `tests/test_matrix_backtest.py` | 新增 17 个测试：alpha 计算、top-K 用 alpha、Sortino 门槛、三级 fallback、ensemble weights |\n| P2 | 设计文档与代码不同步 | `07-backtest-module.md` | §10.4 加\"Alpha 排序 + Sortino 门槛\"等设计点；新增 §10.4.1 三级 Fallback 说明；§10.6 加 JSON 字段说明 |\n\n### 不变项\n\n- DD ≤ 20% 硬约束保留（Constitution L1）\n- 策略代码 / 风控 / 执行逻辑未修改\n- Walk-Forward 4 轮验证流程不变（内部复用 `_run_group`，自动继承 alpha 排序）\n- `backtest_sharpe` / `backtest_sortino` / `backtest_max_drawdown` 字段保留\n- 5 个策略文件未修改\n\n### 降级处理\n\nSPY 数据不可用时：\n- `_get_spy_returns` 返回 None\n- `_compute_alpha` 返回 0.0\n- 所有候选 alpha=0 → Python 稳定排序保留原顺序（按策略列表）\n- ensemble weights 退化为等权（`max(0, 0.01)` 归一化）\n- 不抛异常，不阻塞回测\n\n### 影响范围\n\n- ✅ 向后兼容：`backtest_alpha` 带 default 值；`_optimize_ensemble_weights` 的 `spy_returns` 参数带 default None\n- ⚠️ 行为变更：`--reoptimize` 重新产出后，top-K 策略选择会变化（趋势策略可能进入权重）\n- 🔲 下一轮迭代候选：用户独立运行 `--reoptimize` 验证 alpha 改善\n\n---\n\n## v2.2 — 2026-06-30（迭代 #1：策略名 bug 修复 + Sortino 指标）", "old_string": "# Design Changelog\n\n> 记录设计文档的版本变更及变更理由，便于追溯决策来源。\n\n---\n\n## v2.2 — 2026-06-30（迭代 #1：策略名 bug 修复 + Sortino 指标）", "replace_all": false}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/CHANGELOG.md
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/CHANGELOG.md
---
现在
---
更新迭代
---
轨迹。
---
让我读取
---
最后一个
---
条目，
---
以便
---
在
---
它之后
---
添加：
---
{"file_path": "/Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md", "limit": 15, "offset": 906}
---
 906→
 907→---
 908→
 909→> **Orchestrator 验证记录** (自动追加)
 910→> - 迭代状态: failed
 911→> - 测试: 0 passed, 0 failed
 912→> - 违规: 1 条
 913→> - 高风险文件: 0 个
 914→> - 测试数变化: 574 → 585
 915→> - CodeBuddy 自行更新了 trajectory ✅
 916→
 917→---
 918→
---
 906→
 907→---
 908→
 909→> **Orchestrator 验证记录** (自动追加)
 910→> - 迭代状态: failed
 911→> - 测试: 0 passed, 0 failed
 912→> - 违规: 1 条
 913→> - 高风险文件: 0 个
 914→> - 测试数变化: 574 → 585
 915→> - CodeBuddy 自行更新了 trajectory ✅
 916→
 917→---
 918→
---
{"file_path": "/Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md", "new_string": "---\n\n> **Orchestrator 验证记录** (自动追加)\n> - 迭代状态: failed\n> - 测试: 0 passed, 0 failed\n> - 违规: 1 条\n> - 高风险文件: 0 个\n> - 测试数变化: 574 → 585\n> - CodeBuddy 自行更新了 trajectory ✅\n\n---\n\n## 迭代 #9 — MatrixBacktest Alpha-Based Strategy Selection\n\n- **日期**: 2026-07-05 UTC\n- **类型**: 策略选择逻辑重构（中风险）\n- **变更摘要**: 将 MatrixBacktest 的 top-K 策略选择从 Sortino 排序改为 Alpha（vs SPY）排序；新增 Sortino > 0.5 最低质量门槛；per-strategy best params 和 ensemble weights 从 Sharpe 改为 Alpha\n- **状态**: passed\n- **执行时长**: 1 轮对话（手动开发）\n- **测试数**: 585 → 602（+17 新测试用例）\n\n### 背景\n\nIter #7 的 `--reoptimize` 暴露了根本矛盾：\n- Constitution 目标：年化 20-30%（需 alpha +10~20%）\n- MatrixBacktest 排序：Sortino 降序\n- 结果：选出 Sortino 最高的均值回归策略 → 年化 8.02% → alpha = -11.34%\n\n**Sortino 高 ≠ 年化高。** 均值回归策略天然有高 Sortino（低下行波动）但低绝对收益。\nIter #8 新增的 `rsi_trend_filter` 也因此未能进入权重。\n\n### 变更详情\n\n**P0: SPY Benchmark 数据获取 + Alpha 计算** (`matrix_backtest.py`)\n- 新增 `MatrixBacktest._get_spy_returns(start, end)` 方法：从 MarketDataStore 拉取 SPY 日收益率\n- 新增模块级函数 `_compute_alpha(strat_returns, spy_returns)`：计算 `(strat_annual - spy_annual) * 100`\n- 新增 `_combine_daily_returns(results)` helper：提取等权合并逻辑供 sharpe/sortino/alpha 复用\n- 降级处理：SPY 不可用时 alpha=0.0，不阻塞回测\n\n**P0: Top-K 选择逻辑修改** (`matrix_backtest.py::_run_group`)\n- 三级 Fallback 策略：\n  - Tier 1: DD ≤ 20% AND Sortino > 0.5 → Alpha 降序\n  - Tier 2 (fallback): Tier 1 空 → 仅 DD ≤ 20% → Alpha 降序 + WARNING\n  - Tier 3 (fallback): Tier 2 空 → DD 升序 + dd_constrained=True\n- 新增常量 `MIN_SORTINO_THRESHOLD = 0.5`\n\n**P0: Per-Strategy Best Params 修改** (`matrix_backtest.py::_run_group`)\n- 每个策略的最优参数选择从 Sharpe 改为 Alpha\n- 与 top-K 排序口径一致，避免 per-strategy 用 Sharpe 选低收益高稳定的参数\n\n**P0: Ensemble Weights 修改** (`matrix_backtest.py::_optimize_ensemble_weights`)\n- 权重计算从 Sharpe 改为 Alpha\n- 新增 `spy_returns: pd.Series | None` 参数\n- SPY 不可用时退化为等权（`max(0, 0.01)` 归一化）\n\n**P1: 新增字段**\n- `GroupBacktestResult.backtest_alpha: float = 0.0`\n- `strategy_weights.json` 每条目新增 `backtest_alpha` 字段\n\n**P2: 测试** (`tests/test_matrix_backtest.py`)\n- 新增 3 个测试类共 17 个测试：\n  - `TestAlphaComputation` (6): alpha 计算、SPY 不可用、策略跑输、combine helper、常量\n  - `TestAlphaBasedTopKSelection` (7): top-K 用 alpha、Sortino 门槛、DD 过滤、Tier 2/3 fallback、JSON 字段、per-strategy best params\n  - `TestEnsembleWeightsUsesAlpha` (3): ensemble �� alpha、SPY 不可用降级、单策略\n\n### 验证结果\n\n```\nTargeted tests: tests/test_matrix_backtest.py → 75 passed, 0 failed\nFull pytest: 602 passed, 16 deselected, 0 failed, 103 warnings in 15.47s\n```\n\n### Constitution 合规\n- ✅ 未突破 DD 20% 约束（硬约束保留）\n- ✅ 测试覆盖率提升（+17 测试，585 → 602）\n- ✅ 决策可解释（alpha = 年化收益差，公式明确）\n- ✅ 未引入 RL\n- ✅ 未引入不安全依赖\n- ✅ 未修改策略代码 / 风控 / 执行逻辑\n- ✅ 未触发真实交易\n- ✅ 文档与代码同步（07-backtest-module.md + CHANGELOG v2.3）\n\n### Experience Learned\n- **Sortino 高 ≠ 年化高**：均值回归策略天然高 Sortino 低绝对收益，用 Sortino 排序会系统性排除趋势策略\n- **Alpha 作为排序指标不违反 Constitution L1**：Sortino 仍是 KPI（从排序变成过滤），DD 硬约束不变\n- **三级 Fallback 设计**：Tier 1 严格（DD+Sortino）→ Tier 2 放宽 Sortino → Tier 3 DD fallback，保证回测不阻塞\n- **SPY 降级处理**：数据不可用时 alpha=0，所有候选 alpha 相等 → Python 稳定排序保留原顺序，退化为等权\n- **复用 `_combine_daily_returns`**：提取等权合并逻辑供 sharpe/sortino/alpha 共享，避免重复 `pd.concat`\n\n### 后续建议\n1. 用户独立运行 `--reoptimize` 验证 alpha 改善（预期 alpha 从 -11.34% 提升）\n2. 评估 `rsi_trend_filter` 是否能进入权重（之前因 Sortino 低被排除）\n3. 如果 Sortino > 0.5 门槛过严，可考虑调整为 0.3 或按组分配置\n4. 后续可考虑在 PortfolioBacktest 层验证 alpha 一致性（MatrixBacktest alpha vs PortfolioBacktest alpha_pct）\n\n### L7 流水线状态\n```\n✅ Backtest (≥5年, alpha-based selection)\n✅ Walk-Forward (4轮, 自动继承 alpha 排序)\n✅ Portfolio Backtest | ✅ Paper Trading Integrity\n✅ Harness Reliability | ✅ SignalRanker Sortino Priority\n✅ Strategy Diversity (5 策略 pool)\n🔄 Alpha-Based Selection (迭代 #9 完成，待 --reoptimize 验证)\n⬜ Paper Trade ≥1月 | ⬜ Live\n```\n\n---\n\n", "old_string": "---\n\n> **Orchestrator 验证记录** (自动追加)\n> - 迭代状态: failed\n> - 测试: 0 passed, 0 failed\n> - 违规: 1 条\n> - 高风险文件: 0 个\n> - 测试数变化: 574 → 585\n> - CodeBuddy 自行更新了 trajectory ✅\n\n---\n", "replace_all": false}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md
---
现在
---
让我
---
更新 `.
---
codebuddy/CODE
---
BUDDY.md`
---
 以反映迭代
---
 #9 的
---
变更
---
：
---
{"file_path": "/Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md", "limit": 15, "offset": 1}
---
   1→# Trade-Tools 项目核心参考文档
   2→
   3→> 最后更新：2026-07-04 (Iter #8: RSI Trend-Filtered Mean Reversion 策略)  
   4→> 本文是项目规范 + 关键索引，供 AI 助手快速建立项目上下文。  
   5→> **各阶段开发详情见** → [`.codebuddy/notes/dev_records.md`](.codebuddy/notes/dev_records.md)
   6→
   7→---
   8→
   9→## ⚖️ AI Constitution（最高行为准则）
  10→
  11→> **AI 在此项目中的所有决策，必须以 `alignment/ai_constitution.md` 为最高准则。**
  12→>
  13→> 该文件通过 9 层对齐访谈（L0 Vision → L9 Evolution）建立，覆盖：
  14→> - 目标体系（年化 20-30%，DD≤20%，Sortino 优先）
  15→> - 交易哲学（Hybrid 混合系统，AI 持续进化策略）
  16→
---
   1→# Trade-Tools 项目核心参考文档
   2→
   3→> 最后更新：2026-07-04 (Iter #8: RSI Trend-Filtered Mean Reversion 策略)  
   4→> 本文是项目规范 + 关键索引，供 AI 助手快速建立项目上下文。  
   5→> **各阶段开发详情见** → [`.codebuddy/notes/dev_records.md`](.codebuddy/notes/dev_records.md)
   6→
   7→---
   8→
   9→## ⚖️ AI Constitution（最高行为准则）
  10→
  11→> **AI 在此项目中的所有决策，必须以 `alignment/ai_constitution.md` 为最高准则。**
  12→>
  13→> 该文件通过 9 层对齐访谈（L0 Vision → L9 Evolution）建立，覆盖：
  14→> - 目标体系（年化 20-30%，DD≤20%，Sortino 优先）
  15→> - 交易哲学（Hybrid 混合系统，AI 持续进化策略）
  16→
---
{"file_path": "/Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md", "new_string": "# Trade-Tools 项目核心参考文档\n\n> 最后更新：2026-07-05 (Iter #9: MatrixBacktest Alpha-Based Strategy Selection)  \n> 本文是项目规范 + 关键索引，供 AI 助手快速建立项目上下文。  \n> **各阶段开发详情见** → [`.codebuddy/notes/dev_records.md`](.codebuddy/notes/dev_records.md)", "old_string": "# Trade-Tools 项目核心参考文档\n\n> 最后更新：2026-07-04 (Iter #8: RSI Trend-Filtered Mean Reversion 策略)  \n> 本文是项目规范 + 关键索引，供 AI 助手快速建立项目上下文。  \n> **各阶段开发详情见** → [`.codebuddy/notes/dev_records.md`](.codebuddy/notes/dev_records.md)", "replace_all": false}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md
---
现在
---
请
---
更新
---
 CODE
---
BUDDY.md 
---
中的开发
---
阶段表格：
---
{"file_path": "/Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md", "new_string": "| **Iter #8** | ✅ 完成 | 11 | RSI Trend-Filtered Mean Reversion 策略（RSI 超卖/超买 + 200日SMA趋势过滤，5新测试） |\n| **Iter #9** | ✅ 完成 | 17 | MatrixBacktest Alpha-Based Strategy Selection（SPY benchmark + alpha 计算 + top-K/per-strategy/ensemble 从 Sortino/Sharpe 改为 Alpha + Sortino > 0.5 门槛 + 三级 fallback） |\n| **Phase 6** | 🔲 待开发 | — | AlpacaBroker auto 端到端验证 + 对账真实集成 + 港股支持 |\n\n**当前总测试数：602 passed，0 failed**（live 测试默认隔离，迭代 #9 后；harness 测试 38 个在 `alignment/tests/`）", "old_string": "| **Iter #8** | ✅ 完成 | 11 | RSI Trend-Filtered Mean Reversion 策略（RSI 超卖/超买 + 200日SMA趋势过滤，5新测试） |\n| **Phase 6** | 🔲 待开发 | — | AlpacaBroker auto 端到端验证 + 对账真实集成 + 港股支持 |\n\n**当前总测试数：585 passed，0 failed**（live 测试默认隔离，迭代 #8 后；harness 测试 38 个在 `alignment/tests/`）", "replace_all": false}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md
---
现在
---
更新
---
 CODE
---
BUDDY.md 
---
中的目录
---
结构部分
---
，以反映新的 `
---
backtest_alpha` 字
---
段：
---
{"command": "grep -n \"matrix_backtest.py\\|backtest_dd_status\" /Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md | head -10", "description": "Find matrix_backtest references in CODEBUDDY.md"}
---
Find matrix_backtest references in CODEBUDDY.md
---
Command: grep -n "matrix_backtest.py\|backtest_dd_status" /Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md | head -10
Stdout: 128:    │   ├── matrix_backtest.py  # [Phase 5] MatrixBacktest（含 backtest_dd_status 风险 metadata）

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"file_path": "/Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md", "new_string": "    │   ├── matrix_backtest.py  # [Phase 5] MatrixBacktest（含 backtest_dd_status 风险 metadata + [Iter #9] backtest_alpha / alpha-based selection）", "old_string": "    │   ├── matrix_backtest.py  # [Phase 5] MatrixBacktest（含 backtest_dd_status 风险 metadata）", "replace_all": false}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md
---
现在
---
让我检查一下 `decision
---
_log.md`，看看
---
是否
---
需要添加
---
任何决策记录
---
：
---
{"command": "tail -50 /Users/rickouyang/Github/trade-tools/alignment/decision_log.md 2>/dev/null | head -60", "description": "Check decision log tail"}
---
Check decision log tail
---
Command: tail -50 /Users/rickouyang/Github/trade-tools/alignment/decision_log.md 2>/dev/null | head -60
Stdout:   1. **评分权重不属于 risk param**：risk param 指的是 DD 阈值（20%）、仓位上限（20%）、止损止盈等直接影响单笔交易风险的参数。评分权重是"选股排名的内部权重"，影响候选顺序但不直接决定下单数量或止损位。
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

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"command": "grep -n \"^## \\|^### \" /Users/rickouyang/Github/trade-tools/alignment/decision_log.md | tail -10", "description": "Find decision log sections"}
---
Find decision log sections
---
Command: grep -n "^## \|^### " /Users/rickouyang/Github/trade-tools/alignment/decision_log.md | tail -10
Stdout: 7:### [2026-06-30 16:20 UTC] 迭代 #1 — test_integration_live.py 触发真实 Telegram 消息
29:### [2026-07-01 UTC] 迭代 #2 — portfolio_max_drawdown 符号约定
51:### [2026-07-01 UTC] 迭代 #3 — P0 DD 约束应用层级 + P1 Walk-Forward 窗口语义
105:### [2026-07-02 UTC] 迭代 #4 — PortfolioBacktest 复用 vs 重写 + backtest_dd_status 字段位置
158:### [2026-07-03 UTC] 迭代 #5 — metadata parity 实现位置 + pending order 刷新策略
212:### [2026-07-03 12:01 UTC] 迭代 #5 — 高风险文件触及
223:### [2026-07-04 UTC] 迭代 #7 — SignalRanker 评分权重调整的边界判定
247:### [2026-07-04 UTC] 迭代 #7 — benchmark 降级时的 alpha 语义
265:### [2026-07-04 UTC] 迭代 #8 — trend_period 参数网格固定为 [200]

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
Let
---
 me
---
 add a decision log entry
---
 for Iter #9.
---
 The key decision
---
 is:

---
1. Sort
---
ino > 0.
---
5 threshold
---
 value
---
 (
---
why
---
 0.5,
---
 not 0.3
---
 or 1.0
---
?)

---
2. Three
---
-tier fallback design (why
---
 not just strict
---
 Tier
---
 1 only?)

---
3. SP
---
Y degradation
---
 to
---
 alpha
---
=0 (consistent
---
 with Iter
---
 #7 decision
---
)

Let me add a
---
 decision log entry.
---
让我
---
为 Iter #9 
---
添加一个决策日志条
---
目：
---
{"command": "tail -5 /Users/rickouyang/Github/trade-tools/alignment/decision_log.md", "description": "Check decision log tail"}
---
Check decision log tail
---
Command: tail -5 /Users/rickouyang/Github/trade-tools/alignment/decision_log.md
Stdout:   4. 如果后续实证发现 50/100 在特定波动率组中表现更好，可改为按组配置（group-based），而不是全局搜索

- **决策结果**: `REOPTIMIZE_PARAM_GRIDS["rsi_trend_filter"]` 中 `trend_period` 固定为 `[200]`。后续实证可扩展为按组配置。

---

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"file_path": "/Users/rickouyang/Github/trade-tools/alignment/decision_log.md", "new_string": "- **决策结果**: `REOPTIMIZE_PARAM_GRIDS[\"rsi_trend_filter\"]` 中 `trend_period` 固定为 `[200]`。后续实证可扩展为按组配置。\n\n---\n\n### [2026-07-05 UTC] 迭代 #9 — Sortino > 0.5 门槛值选择 + 三级 Fallback 设计\n\n- **困境描述**: 将 top-K 排序从 Sortino 改为 Alpha 后，需要决定是否保留 Sortino 作为过滤条件，以及门槛值取多少。同时需要决定当无候选通过门槛时的降级策略。\n\n- **涉及 AI Constitution 条款**:\n  - L1: KPI — Sortino 仍是 Constitution L1 首要 KPI，不能完全弃用\n  - L5: 不过度工程 — 三级 fallback 是否过度复杂？\n  - Decision Weight Matrix: 实证优先 > 理论完备\n\n- **决策逻辑**:\n\n  1. **保留 Sortino 作为过滤而非排序**：\n     - Alpha 排序直接优化超额收益目标（年化 20-30%）\n     - 但 Alpha 高不等于下行质量好（可能\"高 alpha 高下行波动\"）\n     - Sortino > 0.5 作为最低质量门槛，排除垃圾策略\n     - 这不违反 L1：Sortino 仍是 KPI，只是从\"排序指标\"变成\"过滤指标\"\n\n  2. **门槛值 0.5 的依据**：\n     - Sortino > 1.5 是优秀策略标准（design_v2 §5）\n     - Sortino > 0.5 是\"基本可用\"的下限（低于 0.5 说明下行风险未被充分补偿）\n     - 0.5 不是硬约束，而是 Tier 1 过滤条件；Tier 2 会放宽\n     - 如实证发现 0.5 过严（排除太多候选），可调整为 0.3 或按组分配置\n\n  3. **三级 Fallback 设计**：\n     - Tier 1: DD ≤ 20% AND Sortino > 0.5 → Alpha 降序（理想路径）\n     - Tier 2: 仅 DD ≤ 20% → Alpha 降序（放宽 Sortino，WARNING 日志）\n     - Tier 3: DD 升序 → dd_constrained=True（DD fallback，与迭代 #3 一致）\n     - 为什么不只用 Tier 1？因为 Sortino > 0.5 可能全部候选都不满足（如熊市期间），\n       需要 fallback 保证回测不阻塞\n     - 为什么不直接用 Tier 2？因为 Sortino 门槛在正常市场环境下能过滤垃圾策略\n     - 三级设计在\"严格性\"和\"鲁棒性\"之间平衡\n\n- **决策结果**: \n  - 保留 Sortino 作为过滤指标（门槛 0.5）\n  - 三级 Fallback：Tier 1 严格 → Tier 2 放宽 Sortino → Tier 3 DD fallback\n  - 门槛值 0.5 可配置（`MIN_SORTINO_THRESHOLD` 常量），后续实证可调整\n\n---\n\n### [2026-07-05 UTC] 迭代 #9 — SPY 降级时 alpha=0 的语义一致性\n\n- **困境描述**: 当 SPY 数据不可用时，`_compute_alpha` 返回 0.0。所有候选 alpha=0 → 排序退化为原顺序。这与迭代 #7 的 PortfolioBacktest 降级决策一致，但需确认 MatrixBacktest 层的语义。\n\n- **涉及 AI Constitution 条款**:\n  - L7: 代码规范 — 降级语义应明确\n  - L1: KPI 必须可解释\n\n- **决策逻辑**:\n  1. **与迭代 #7 一致**：PortfolioBacktest 在 SPY 不可用时 benchmark=0，alpha=portfolio_return。\n     MatrixBacktest 层同理：alpha=0 表示\"无法计算超额收益\"\n  2. **不抛异常**：spec §4.1 明确要求降级不阻塞回测\n  3. **退化为原顺序**：Python `sorted` 是稳定排序，所有 alpha=0 时保持策略列表顺序\n     （`strategies=[\"dual_ma\", \"rsi_mean_revert\", ...]` 的顺序），这是可接受的降级\n  4. **ensemble weights 退化**：`max(0, 0.01)` 归一化 → 等权，符合直觉\n  5. **日志可识别**：`_get_spy_returns` 在 SPY 不可用时输出 WARNING\n\n- **决策结果**: SPY 不可用时 alpha=0.0，所有候选 alpha 相等 → 稳定排序保留原顺序 → ensemble 退化为等权。与迭代 #7 降级策略一致。\n\n---\n", "old_string": "- **决策结果**: `REOPTIMIZE_PARAM_GRIDS[\"rsi_trend_filter\"]` 中 `trend_period` 固定为 `[200]`。后续实证可扩展为按组配置。\n\n---\n", "replace_all": false}
---
Error: File has not been read yet: /Users/rickouyang/Github/trade-tools/alignment/decision_log.md. Read it first before writing to it.
---
Error: File has not been read yet: /Users/rickouyang/Github/trade-tools/alignment/decision_log.md. Read it first before writing to it.
---
{"file_path": "/Users/rickouyang/Github/trade-tools/alignment/decision_log.md", "limit": 5, "offset": 265}
---
 265→### [2026-07-04 UTC] 迭代 #8 — trend_period 参数网格固定为 [200]
 266→
 267→- **困境描述**: `rsi_trend_filter` 策略的参数网格设计中，`trend_period`（SMA 趋势过滤周期）是否应纳入参数网格搜索。常见趋势周期有 50/100/200，全搜索（4 参数 3×3×3×3=81 组合）会大幅膨胀计算规模，但固定为 200 可能错过更优的趋势周期。
 268→
 269→- **涉及 AI Constitution 条款**:
 270→
---
 265→### [2026-07-04 UTC] 迭代 #8 — trend_period 参数网格固定为 [200]
 266→
 267→- **困境描述**: `rsi_trend_filter` 策略的参数网格设计中，`trend_period`（SMA 趋势过滤周期）是否应纳入参数网格搜索。常见趋势周期有 50/100/200，全搜索（4 参数 3×3×3×3=81 组合）会大幅膨胀计算规模，但固定为 200 可能错过更优的趋势周期。
 268→
 269→- **涉及 AI Constitution 条款**:
 270→
---
{"file_path": "/Users/rickouyang/Github/trade-tools/alignment/decision_log.md", "limit": 10, "offset": 275}
---
 275→  1. 200 日 SMA 是市场共识的趋势判定线（年线），无需网格搜索
 276→  2. 50/100/200 的行为差异主要反映趋势时滞（越短越敏感，越长越滞后），不是策略品质差异——这不是需要搜索的"最优参数"，而是"你想跟踪多长周期的趋势"的策略选择
 277→  3. 如果纳入搜索，81 个组合规模膨胀 3 倍（27 vs 81），ROI 低
 278→  4. 如果后续实证发现 50/100 在特定波动率组中表现更好，可改为按组配置（group-based），而不是全局搜索
 279→
 280→- **决策结果**: `REOPTIMIZE_PARAM_GRIDS["rsi_trend_filter"]` 中 `trend_period` 固定为 `[200]`。后续实证可扩展为按组配置。
 281→
 282→---
 283→
---
 275→  1. 200 日 SMA 是市场共识的趋势判定线（年线），无需网格搜索
 276→  2. 50/100/200 的行为差异主要反映趋势时滞（越短越敏感，越长越滞后），不是策略品质差异——这不是需要搜索的"最优参数"，而是"你想跟踪多长周期的趋势"的策略选择
 277→  3. 如果纳入搜索，81 个组合规模膨胀 3 倍（27 vs 81），ROI 低
 278→  4. 如果后续实证发现 50/100 在特定波动率组中表现更好，可改为按组配置（group-based），而不是全局搜索
 279→
 280→- **决策结果**: `REOPTIMIZE_PARAM_GRIDS["rsi_trend_filter"]` 中 `trend_period` 固定为 `[200]`。后续实证可扩展为按组配置。
 281→
 282→---
 283→
---
{"file_path": "/Users/rickouyang/Github/trade-tools/alignment/decision_log.md", "new_string": "- **决策结果**: `REOPTIMIZE_PARAM_GRIDS[\"rsi_trend_filter\"]` 中 `trend_period` 固定为 `[200]`。后续实证可扩展为按组配置。\n\n---\n\n### [2026-07-05 UTC] 迭代 #9 — Sortino > 0.5 门槛值选择 + 三级 Fallback 设计\n\n- **困境描述**: 将 top-K 排序从 Sortino 改为 Alpha 后，需要决定是否保留 Sortino 作为过滤条件，以及门槛值取多少。同时需要决定当无候选通过门槛时的降级策略。\n\n- **涉及 AI Constitution 条款**:\n  - L1: KPI — Sortino 仍是 Constitution L1 首要 KPI，不能完全弃用\n  - L5: 不过度工程 — 三级 fallback 是否过度复杂？\n  - Decision Weight Matrix: 实证优先 > 理论完备\n\n- **决策逻辑**:\n\n  1. **保留 Sortino 作为过滤而非排序**：\n     - Alpha 排序直接优化超额收益目标（年化 20-30%）\n     - 但 Alpha 高不等于下行质量好（可能\"高 alpha 高下行波动\"）\n     - Sortino > 0.5 作为最低质量门槛，排除垃圾策略\n     - 这不违反 L1：Sortino 仍是 KPI，只是从\"排序指标\"变成\"过滤指标\"\n\n  2. **门槛值 0.5 的依据**：\n     - Sortino > 1.5 是优秀策略标准（design_v2 §5）\n     - Sortino > 0.5 是\"基本可用\"的下限（低于 0.5 说明下行风险未被充分补偿）\n     - 0.5 不是硬约束，而是 Tier 1 过滤条件；Tier 2 会放宽\n     - 如实证发现 0.5 过严（排除太多候选），可调整为 0.3 或按组分配置\n\n  3. **三级 Fallback 设计**：\n     - Tier 1: DD ≤ 20% AND Sortino > 0.5 → Alpha 降序（理想路径）\n     - Tier 2: 仅 DD ≤ 20% → Alpha 降序（放宽 Sortino，WARNING 日志）\n     - Tier 3: DD 升序 → dd_constrained=True（DD fallback，与迭代 #3 一致）\n     - 为什么不只用 Tier 1？因为 Sortino > 0.5 可能全部候选都不满足（如熊市期间），需要 fallback 保证回测不阻塞\n     - 为什么不直接用 Tier 2？因为 Sortino 门槛在正常市场环境下能过滤垃圾策略\n     - 三级设计在\"严格性\"和\"鲁棒性\"之间平衡\n\n- **决策结果**: \n  - 保留 Sortino 作为过滤指标（门槛 0.5）\n  - 三级 Fallback：Tier 1 严格 → Tier 2 放宽 Sortino → Tier 3 DD fallback\n  - 门槛值 0.5 可配置（`MIN_SORTINO_THRESHOLD` 常量），后续实证可调整\n\n---\n\n### [2026-07-05 UTC] 迭代 #9 — SPY 降级时 alpha=0 的语义一致性\n\n- **困境描述**: 当 SPY 数据不可用时，`_compute_alpha` 返回 0.0。所有候选 alpha=0 → 排序退化为原顺序。这与迭代 #7 的 PortfolioBacktest 降级决策一致，但需确认 MatrixBacktest 层的语义。\n\n- **涉及 AI Constitution 条款**:\n  - L7: 代码规范 — 降级语义应明确\n  - L1: KPI 必须可解释\n\n- **决策逻辑**:\n  1. **与迭代 #7 一致**：PortfolioBacktest 在 SPY 不可用时 benchmark=0，alpha=portfolio_return。MatrixBacktest 层同理：alpha=0 表示\"无法计算超额收益\"\n  2. **不抛异常**：spec §4.1 明确要求降级不阻塞回测\n  3. **退化为原顺序**：Python `sorted` 是稳定排序，所有 alpha=0 时保持策略列表顺序（`strategies=[\"dual_ma\", \"rsi_mean_revert\", ...]` 的顺序），这是可接受的降级\n  4. **ensemble weights 退化**：`max(0, 0.01)` 归一化 → 等权，符合直觉\n  5. **日志可识别**：`_get_spy_returns` 在 SPY 不可用时输出 WARNING\n\n- **决策结果**: SPY 不可用时 alpha=0.0，所有候选 alpha 相等 → 稳定排序保留原顺序 → ensemble 退化为等权。与迭代 #7 降级策略一致。\n\n---\n", "old_string": "- **决策结果**: `REOPTIMIZE_PARAM_GRIDS[\"rsi_trend_filter\"]` 中 `trend_period` 固定为 `[200]`。后续实证可扩展为按组配置。\n\n---\n", "replace_all": false}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/alignment/decision_log.md
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/alignment/decision_log.md
---
现在
---
让我进行
---
最后一次验证
---
，
---
再次
---
运行完整的测试套件
---
：
---
{"command": "/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest 2>&1 | tail -5", "description": "Final full pytest run"}
---
Final full pytest run
---
Command: /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest 2>&1 | tail -5
Stdout:   /Users/rickouyang/Github/trade-tools/mytrader/tests/test_risk_manager.py:408: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    timestamp=datetime.utcnow(),

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
602 passed, 16 deselected, 103 warnings in 15.94s

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
所有
---
 602 个测试
---
均已通过。让我再
---
通过
---
在
---
测试
---
数据
---
上运行 `Matrix
---
Backtest` 来
---
验证
---
新
---
字段
---
是否已
---
正确输出，
---
以此
---
对
---
 JSON
---
 输出进行一次
---
快速完整性
---
检查：
---
{"command": "/Users/rickouyang/miniforge3/envs/py312trade/bin/python -c \"\nimport json\nfrom datetime import date\nfrom unittest.mock import MagicMock\nimport pandas as pd\nfrom mytrader.backtest.matrix_backtest import MatrixBacktest\n\n# minimal mock\ndef _make_ohlcv(n=300, trend='up'):\n    idx = pd.date_range('2021-01-01', periods=n, freq='B')\n    if trend == 'up':\n        close = [100.0 + i * 0.1 for i in range(n)]\n    else:\n        close = [100.0 - i * 0.05 for i in range(n)]\n    return pd.DataFrame({\n        'open': [c - 0.5 for c in close],\n        'high': [c + 1.0 for c in close],\n        'low': [c - 1.0 for c in close],\n        'close': close,\n        'volume': [1_000_000] * n,\n    }, index=idx)\n\nstore = MagicMock()\ndf = _make_ohlcv(300, 'up')\nspy_df = _make_ohlcv(300, 'up')\ndef get_bars_multi(symbols, start, end, timeframe='1d'):\n    m = {'AAPL': df, 'MSFT': df, 'SPY': spy_df}\n    return {s: m[s] for s in symbols if s in m}\nstore.get_bars_multi.side_effect = get_bars_multi\n\nuniverse = MagicMock()\nuniverse.get_groups.return_value = {'NDX_mid_vol': ['AAPL', 'MSFT']}\n\nmb = MatrixBacktest(store=store, universe=universe, years=1, top_k=1)\nimport tempfile\nwith tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:\n    out = f.name\nreport = mb.run(strategies=['dual_ma'], param_grids={'dual_ma': {'fast': [5], 'slow': [20]}}, output_file=out)\ndata = json.loads(open(out).read())\nprint('JSON keys:', list(data['groups']['NDX_mid_vol'][0].keys()))\nprint('backtest_alpha:', data['groups']['NDX_mid_vol'][0]['backtest_alpha'])\nprint('GroupBacktestResult.backtest_alpha:', report.group_results[0].backtest_alpha)\n\" 2>&1 | tail -5", "description": "Sanity check JSON output includes backtest_alpha"}
---
Sanity check JSON output includes backtest_alpha
---
Command: /Users/rickouyang/miniforge3/envs/py312trade/bin/python -c "
import json
from datetime import date
from unittest.mock import MagicMock
import pandas as pd
from mytrader.backtest.matrix_backtest import MatrixBacktest

# minimal mock
def _make_ohlcv(n=300, trend='up'):
    idx = pd.date_range('2021-01-01', periods=n, freq='B')
    if trend == 'up':
        close = [100.0 + i * 0.1 for i in range(n)]
    else:
        close = [100.0 - i * 0.05 for i in range(n)]
    return pd.DataFrame({
        'open': [c - 0.5 for c in close],
        'high': [c + 1.0 for c in close],
        'low': [c - 1.0 for c in close],
        'close': close,
        'volume': [1_000_000] * n,
    }, index=idx)

store = MagicMock()
df = _make_ohlcv(300, 'up')
spy_df = _make_ohlcv(300, 'up')
def get_bars_multi(symbols, start, end, timeframe='1d'):
    m = {'AAPL': df, 'MSFT': df, 'SPY': spy_df}
    return {s: m[s] for s in symbols if s in m}
store.get_bars_multi.side_effect = get_bars_multi

universe = MagicMock()
universe.get_groups.return_value = {'NDX_mid_vol': ['AAPL', 'MSFT']}

mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=1)
import tempfile
with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
    out = f.name
report = mb.run(strategies=['dual_ma'], param_grids={'dual_ma': {'fast': [5], 'slow': [20]}}, output_file=out)
data = json.loads(open(out).read())
print('JSON keys:', list(data['groups']['NDX_mid_vol'][0].keys()))
print('backtest_alpha:', data['groups']['NDX_mid_vol'][0]['backtest_alpha'])
print('GroupBacktestResult.backtest_alpha:', report.group_results[0].backtest_alpha)
" 2>&1 | tail -5
Stdout: 2026-07-05 15:04:45.924 | INFO     | mytrader.backtest.matrix_backtest:_write_weights:1101 - [MatrixBacktest] weights saved to /tmp/tmpr6m1g27b.json
2026-07-05 15:04:45.924 | INFO     | mytrader.backtest.matrix_backtest:run:804 - [MatrixBacktest] done: 1 groups, warnings=0
JSON keys: ['strategy', 'params', 'weight', 'backtest_sharpe', 'backtest_sortino', 'backtest_max_drawdown', 'backtest_win_rate', 'backtest_alpha', 'dd_constrained', 'backtest_dd_status']
backtest_alpha: -24.6669
GroupBacktestResult.backtest_alpha: -24.666881484269055

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
`
---
backtest_alpha` 字
---
段已正确出现在
---
 JSON 中
---
。
---
让我
---
再验证
---
一下 Walk
---
-Forward 
---
集成是否
---
仍然有效
---
：
---
{"command": "/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_matrix_backtest.py::TestWalkForward -v 2>&1 | tail -15", "description": "Run Walk-Forward tests to verify integration"}
---
Run Walk-Forward tests to verify integration
---
Command: /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_matrix_backtest.py::TestWalkForward -v 2>&1 | tail -15
Stdout: ============================= test session starts ==============================
platform darwin -- Python 3.12.13, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/rickouyang/Github/trade-tools/mytrader
configfile: pyproject.toml
plugins: cov-7.1.0, anyio-4.13.0
collected 10 items

tests/test_matrix_backtest.py ..........                                 [100%]

============================== 10 passed in 4.08s ==============================

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
Walk
---
-Forward 
---
测试已通过（
---
它们在
---
内部使用了
---
 `_run_group`，
---
该
---
部分
---
继承了
---
基于
---
 Alpha
---
 的选择）。我来
---
检查
---
一下最终的
---
测试
---
计数
---
细分
---
：
---
{"command": "/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_matrix_backtest.py --co -q 2>&1 | tail -5", "description": "Count matrix_backtest tests"}
---
Count matrix_backtest tests
---
Command: /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_matrix_backtest.py --co -q 2>&1 | tail -5
Stdout: tests/test_matrix_backtest.py: 75


Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"status": "completed", "taskId": "7"}
---
Updated task #7 status
---
Updated task #7 status
---
让我
---
对所有
---
文件
---
进行最后的
---
审查
---
，以确保
---
一切内容
---
保持一致：
---
{"command": "git diff --stat 2>&1 | tail -15", "description": "Show diff stats"}
---
Show diff stats
---
Command: git diff --stat 2>&1 | tail -15
Stdout:  mytrader/designs/design_v2/07-backtest-module.md   |  49 ++
 mytrader/designs/design_v2/13-signal-ranker.md     |  42 +-
 mytrader/designs/design_v2/CHANGELOG.md            |  54 ++
 mytrader/main.py                                   |   9 +
 mytrader/mytrader/backtest/matrix_backtest.py      | 268 +++++--
 mytrader/mytrader/backtest/portfolio_backtest.py   | 164 ++++-
 mytrader/mytrader/signal/ranker.py                 |  34 +-
 mytrader/mytrader/strategy/__init__.py             |   9 +-
 mytrader/pyproject.toml                            |   7 +-
 mytrader/tests/test_integration_live.py            |  20 +-
 mytrader/tests/test_matrix_backtest.py             | 689 ++++++++++++++++++
 mytrader/tests/test_portfolio_backtest.py          | 170 +++++
 mytrader/tests/test_strategy.py                    |  61 +-
 mytrader/tests/test_strategy_matrix_ranker.py      | 128 +++-
 20 files changed, 3424 insertions(+), 262 deletions(-)

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
There
---
 are
---
 many
---
 files changed
---
 -
---
 some
---
 are
---
 pre
---
-existing changes
---
 from previous iterations that
---
 weren't committed. Let
---
 me check
---
 the
---
 git status to see what
---
's staged
---
 vs unst
---
aged:
---
{"command": "git status 2>&1 | head -30", "description": "Check git status"}
---
Check git status
---
Command: git status 2>&1 | head -30
Stdout: On branch master
Your branch is up to date with 'origin/master'.

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   ../.codebuddy/CODEBUDDY.md
	modified:   ../.codebuddy/skills/cb-acp-dev/scripts/orchestrator.py
	modified:   ../alignment/decision_log.md
	modified:   ../alignment/iteration_trajectory.md
	modified:   ../alignment/orchestrator.py
	modified:   config/strategy_weights.json
	modified:   designs/design_v2/07-backtest-module.md
	modified:   designs/design_v2/13-signal-ranker.md
	modified:   designs/design_v2/CHANGELOG.md
	modified:   main.py
	modified:   mytrader/backtest/matrix_backtest.py
	modified:   mytrader/backtest/portfolio_backtest.py
	modified:   mytrader/signal/ranker.py
	modified:   mytrader/strategy/__init__.py
	modified:   pyproject.toml
	modified:   tests/test_integration_live.py
	modified:   tests/test_matrix_backtest.py
	modified:   tests/test_portfolio_backtest.py
	modified:   tests/test_strategy.py
	modified:   tests/test_strategy_matrix_ranker.py

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	../alignment/tests/

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
所有
---
更改
---
均
---
已完成。让我再
---
进行
---
最后一次
---
核实
---
，以确认 Iter
---
 #9 的特定
---
更改
---
运行
---
正常：
---
{"command": "git diff mytrader/backtest/matrix_backtest.py 2>&1 | head -100", "description": "Review matrix_backtest.py changes"}
---
Review matrix_backtest.py changes
---
Command: git diff mytrader/backtest/matrix_backtest.py 2>&1 | head -100
Stdout: diff --git a/mytrader/mytrader/backtest/matrix_backtest.py b/mytrader/mytrader/backtest/matrix_backtest.py
index 269160d..0fbb3bb 100644
--- a/mytrader/mytrader/backtest/matrix_backtest.py
+++ b/mytrader/mytrader/backtest/matrix_backtest.py
@@ -40,6 +40,12 @@ MAX_PORTFOLIO_DRAWDOWN_PCT: float = 20.0
 # （低于 L1 的 20% 线，给样本外留缓冲）
 WALK_FORWARD_VAL_DD_THRESHOLD: float = 15.0
 
+# 迭代 #9 新增：Sortino 最低质量门槛，用于 top-K 选择时的二级过滤
+# 排除 Sortino ≤ 0.5 的"垃圾"策略（即使 alpha 高也不选）
+# 设计动机：alpha 排序选出高绝对收益策略，但需 Sortino 门槛保证基本下行质量
+# fallback：若无候选通过此门槛，放宽过滤（仅保留 DD 硬约束）
+MIN_SORTINO_THRESHOLD: float = 0.5
+
 
 # ---------------------------------------------------------------------------
 # 数据结构
@@ -76,6 +82,7 @@ class GroupBacktestResult:
     portfolio_sortino: float = 0.0          # 等权组合 Sortino（迭代 #1 新增）
     portfolio_max_drawdown: float = 0.0     # 等权组合最大回撤（迭代 #2 新增，Constitution L1 KPI）
     dd_constrained: bool = False            # 迭代 #3：该组是否用了 DD fallback（无合规候选）
+    backtest_alpha: float = 0.0              # 迭代 #9：alpha vs SPY（百分数），用于排序策略选择
 
 
 @dataclass
@@ -233,6 +240,83 @@ def _compute_sortino(
     return float(returns.mean() / dd * np.sqrt(periods_per_year))
 
 
+def _combine_daily_returns(results: list[SingleBacktestResult]) -> pd.Series:
+    """等权合并组内日收益率序列，返回组合日收益率（迭代 #9 新增）。
+
+    与 _portfolio_sharpe_from_results / _portfolio_sortino_from_results 同语义：
+    将所有标的日收益率等权合并为组合序列。提取为独立函数以便 alpha 计算
+    和 per-strategy best params 选择复用，避免重复 pd.concat。
+
+    Args:
+        results: 单策略多标的的回测结果列表
+
+    Returns:
+        组合日收益率 pd.Series；无有效数据时返回空 Series
+    """
+    valid = [r.daily_returns for r in results if not r.daily_returns.empty]
+    if not valid:
+        return pd.Series(dtype=float)
+    return pd.concat(valid, axis=1).mean(axis=1)
+
+
+def _compute_alpha(
+    strategy_daily_returns: pd.Series,
+    spy_daily_returns: pd.Series | None,
+    periods_per_year: int = 252,
+) -> float:
+    """计算 alpha = 策略年化收益 - SPY 年化收益（迭代 #9 新增）。
+
+    Alpha 衡量策略相对 SPY buy-and-hold 的超额收益。正值表示跑赢 SPY，
+    负值表示跑输 SPY。用于 top-K 策略选择和 per-strategy best params 选择，
+    替代之前基于 Sortino/Sharpe 的选择逻辑（参考 iteration #9 spec）。
+
+    年化公式：(1 + mean_daily) ** periods_per_year - 1
+    使用算术平均日收益的几何年化，与 PortfolioBacktester 同口径。
+
+    降级处理：SPY 数据不可用（None 或空）→ 返回 0.0（不抛异常）。
+    这样在 SPY 数据缺失时，alpha 排序退化为"原顺序"，不会阻塞回测。
+
+    Args:
+        strategy_daily_returns: 策略组合日收益率序列
+        spy_daily_returns:      SPY 日收益率序列；None 表示数据不可用
+        periods_per_year:       年化因子（日线 = 252）
+
+    Returns:
+        Alpha 百分数（如 5.23 表示策略年化收益跑赢 SPY 5.23 个百分点）；
+        SPY 不可用时返回 0.0
+    """
+    if spy_daily_returns is None or spy_daily_returns.empty:
+        return 0.0
+    if strategy_daily_returns is None or strategy_daily_returns.empty:
+        return 0.0
+
+    # 对齐时间索引（inner join 取交集）
+    aligned = pd.concat(
+        [strategy_daily_returns.rename("strat"), spy_daily_returns.rename("spy")],
+        axis=1,
+        join="inner",
+    ).dropna()
+    if aligned.empty or len(aligned) < 2:
+        return 0.0
+
+    strat_returns = aligned["strat"]
+    spy_returns = aligned["spy"]
+
+    # 年化收益 = (1 + mean_daily)^252 - 1
+    strat_mean = strat_returns.mean()
+    spy_mean = spy_returns.mean()
+    if not np.isfinite(strat_mean) or not np.isfinite(spy_mean):
+        return 0.0
+
+    strat_annual = (1.0 + strat_mean) ** periods_per_year - 1.0
+    spy_annual = (1.0 + spy_mean) ** periods_per_year - 1.0
+

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
实现
---
看起来不错
---
。让我最后
---
再运行一次完整的测试
---
套件，以确认
---
一切都能
---
端
---
到端正常
---
工作：
---
{"command": "/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_matrix_backtest.py tests/test_portfolio_backtest.py tests/test_strategy.py -q 2>&1 | tail -5", "description": "Final targeted test run"}
---
Final targeted test run
---
Command: /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_matrix_backtest.py tests/test_portfolio_backtest.py tests/test_strategy.py -q 2>&1 | tail -5
Stdout: ........................................................................ [ 43%]
........................................................................ [ 86%]
.......................                                                  [100%]

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"command": "/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_matrix_backtest.py tests/test_portfolio_backtest.py tests/test_strategy.py 2>&1 | tail -3", "description": "Get test count"}
---
Get test count
---
Command: /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_matrix_backtest.py tests/test_portfolio_backtest.py tests/test_strategy.py 2>&1 | tail -3
Stdout: ........................................................................ [ 86%]
.......................                                                  [100%]
167 passed in 7.33s

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
All
---
 
---
167 targeted tests pass.
---
 Let me provide
---
 a final summary:


---
## Iteration #9
---
 完成总结


---
### 
---
实现内容

按
---
 `
---
iterations/iteration_9
---
/spec.md` 完成
---
 **MatrixBacktest Alpha
---
-Based Strategy Selection**：


---
####
---
 代码
---
变更 (`my
---
trader/backtest/m
---
atrix_backtest.py`
---
)

1. **新增
---
常量** `
---
MIN_SORTINO_THRESHOLD =
---
 0.5`
---
 — Sortino 最低
---
质量门槛
2.
---
 **新增字段** `
---
GroupBacktestResult.back
---
test_alpha: float =
---
 0.0`

---
3. **新增函数
---
**：

---
   - `_combine_daily
---
_returns(results)` — 
---
等权合并日
---
收益率 helper
---
（复
---
用给
---
 sharpe/sortino
---
/alpha）
   -
---
 `_compute_alpha(str
---
at,
---
 spy)`
---
 — 
---
计算年
---
化 alpha 百
---
分数

---
4. **新增方法
---
** `MatrixBacktest
---
._get_spy_returns
---
(start, end)` —
---
 从 MarketDataStore 
---
拉取 SPY
---
 日收益率
5.
---
 **修改 `_run_group
---
`**：
   -
---
 
---
获取 SPY returns
---
（一次获取组
---
内复用）
  
---
 - per-strategy best
---
 params：
---
Shar
---
pe → Alpha
  
---
 - 三
---
级 Fallback top
---
-K 选择
---
：Tier 1 (
---
DD+Sortino)
---
 → Tier 2 (
---
仅 DD) → Tier
---
 3 (DD 
---
升序)
   -
---
 ensemble weights 
---
传
---
 `
---
spy_returns` 参数

---
  
---
 - JSON
---
 输出新增
---
 `backtest_alpha`
---
 字段
6.
---
 **修改 `_optimize_
---
ensemble_weights`**：
---
新增
---
 `spy_returns` 参数
---
，权重从 Sharpe
---
 →
---
 Alpha（
---
SPY 不可用
---
退
---
化为等权）

####
---
 测试新增
---
 (`tests/test_matrix_back
---
test.py`)

17
---
 个新测试，3
---
 个测试类：
-
---
 `TestAlphaComputation
---
` (6)
---
 — alpha 计算、SP
---
Y 不可
---
用降
---
级、combine
---
 helper

---
- `TestAlphaBased
---
TopKSelection` (
---
7) — top-K
---
 用 alpha、Sortino
---
 门槛、DD 过
---
滤、三级 fallback、
---
JSON 字段、per
---
-strategy best params

---
- `TestEnsemble
---
WeightsUsesAlpha` (
---
3) — ensemble
---
 用
---
 alpha、SPY 
---
不可
---
用
---
降级、单策略
---


#### 文档更新
---


---
- `design
---
s/design_v2/
---
07-backtest-module.md
---
` — §10.
---
4 加
---
 
---
4 个新
---
设计点 +
---
 §10.4.
---
1 三级 Fallback
---
 说明 + §
---
10.6 JSON 字
---
段说明
- `
---
designs/design_v2
---
/CHANGELOG.md`
---
 — v2.3
---
 变更记录

---
- `alignment/iteration
---
_trajectory.md` — 
---
迭代 #9 
---
完整记录（
---
L9 格式）

---
- `alignment/decision
---
_log.md` — 
---
2 条决策记录（
---
Sortino 门槛值
---
 + SP
---
Y 降级语义
---
）
- `.codeb
---
uddy/CODEBUDD
---
Y.md` — 更
---
新最后
---
更新日期
---
、Iter
---
 #9 行
---
、测试数 
---
585→602
---


### 验证
---
结果

```
Target
---
ed tests: 
---
167 passed (
---
matrix_backtest +
---
 portfolio_backtest + strategy
---
)
Full pytest: 
---
602 passed, 
---
16 deselected, 
---
0 failed, 103
---
 warnings in 15.
---
94s
```


---
### Constitution 合规

---
- ✅ 未突破
---
 DD 20% 
---
硬约束（保留
---
）
- ✅ 
---
测试覆盖率提升（58
---
5 → 602
---
，+17 新测试
---
）
- ✅ 未
---
修改策略代码 / 
---
风控 / 
---
执行逻辑
- 
---
✅ 未触发真实交易
---

- ✅ 文
---
档与代码同步

---
- ✅ 决
---
策可解释（alpha
---
 =
---
 年化收益差，
---
公式明确）

---
- ✅ 
---
模糊决策已
---
记录到 `
---
decision_log.md`

###
---
 关
---
键设计点


---
**
---
Alpha
---
 
---
计算公式**（
---
与 Portfolio
---
Backtester 同口径）
---
：
``
---
`
strat_annual
---
 = (1 + strat
---
_returns
---
.mean()) ** 25
---
2 - 1

---
spy_annual  
---
 = (1 + spy
---
_returns.mean()) ** 
---
252 - 1
---

alpha_pct
---
    = (strat
---
_annual - spy_ann
---
ual) * 100
---

```

**三级
---
 Fallback**：

---
```
Tier 1
---
: DD ≤ 20
---
% AND Sortino >
---
 0.5 
---
 →  Alpha 降
---
序
Tier 2
---
: DD
---
 ≤ 20%（
---
放宽 Sortino）  
---
 →  Alpha 降
---
序 + WARNING
Tier
---
 3: 无
---
 DD 合规候选             
---
 →  DD 升
---
序 + dd_constrained
---
=True
```

**
---
降级处理**：
---
SPY 数据
---
不可用时 alpha=
---
0.0，所有
---
候选 alpha 相
---
等 → Python
---
 稳定排序
---
保留原顺序 → ensemble
---
 退化为等权
---
，
---
不阻塞
---
回测。