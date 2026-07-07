Let
---
 me
---
 start
---
 by
---
 reading
---
 the
---
 spec
---
 and
---
 background
---
 documents
---
 to
---
 understand
---
 the
---
 task
---
.
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/iterations/iteration_11/spec.md"}
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/.codebuddy/notes/experience.md"}
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/tmp/iteration10_audit.md"}
---
<tool_use_error>File does not exist.</tool_use_error>
---
<tool_use_error>File does not exist.</tool_use_error>
---
<tool_use_error>File does not exist.</tool_use_error>
---
<tool_use_error>File does not exist.</tool_use_error>
---
<tool_use_error>File does not exist.</tool_use_error>
---
<tool_use_error>File does not exist.</tool_use_error>
---
{"command":"ls /Users/rickouyang/Github/trade-tools/mytrader/iterations/ 2>/dev/null; ls /Users/rickouyang/Github/trade-tools/mytrader/.codebuddy/notes/ 2>/dev/null; ls /Users/rickouyang/Github/trade-tools/mytrader/tmp/ 2>/dev/null","description":"Check directories for iteration files"}
---
Check directories for iteration files
---
Command: ls /Users/rickouyang/Github/trade-tools/mytrader/iterations/ 2>/dev/null; ls /Users/rickouyang/Github/trade-tools/mytrader/.codebuddy/notes/ 2>/dev/null; ls /Users/rickouyang/Github/trade-tools/mytrader/tmp/ 2>/dev/null
Stdout: iteration_8

Stderr: (empty)
Exit Code: 1
Signal: (none)
---
{"command":"find /Users/rickouyang/Github/trade-tools -name \"iteration_11\" -type d 2>/dev/null; find /Users/rickouyang/Github/trade-tools -name \"spec.md\" 2>/dev/null | head -20; find /Users/rickouyang/Github/trade-tools -name \"experience.md\" 2>/dev/null | head -10; find /Users/rickouyang/Github/trade-tools -name \"iteration10_audit.md\" 2>/dev/null","description":"Find spec and background files"}
---
Find spec and background files
---
Command: find /Users/rickouyang/Github/trade-tools -name "iteration_11" -type d 2>/dev/null; find /Users/rickouyang/Github/trade-tools -name "spec.md" 2>/dev/null | head -20; find /Users/rickouyang/Github/trade-tools -name "experience.md" 2>/dev/null | head -10; find /Users/rickouyang/Github/trade-tools -name "iteration10_audit.md" 2>/dev/null
Stdout: /Users/rickouyang/Github/trade-tools/iterations/iteration_11
/Users/rickouyang/Github/trade-tools/mytrader/iterations/iteration_8/spec.md
/Users/rickouyang/Github/trade-tools/iterations/iteration_6/spec.md
/Users/rickouyang/Github/trade-tools/iterations/iteration_8/spec.md
/Users/rickouyang/Github/trade-tools/iterations/iteration_9/spec.md
/Users/rickouyang/Github/trade-tools/iterations/iteration_7/spec.md
/Users/rickouyang/Github/trade-tools/iterations/iteration_5/spec.md
/Users/rickouyang/Github/trade-tools/iterations/iteration_4/spec.md
/Users/rickouyang/Github/trade-tools/iterations/iteration_11/spec.md
/Users/rickouyang/Github/trade-tools/iterations/iteration_10/spec.md
/Users/rickouyang/Github/trade-tools/.codebuddy/notes/experience.md
/Users/rickouyang/Github/trade-tools/tmp/iteration10_audit.md

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"file_path":"/Users/rickouyang/Github/trade-tools/iterations/iteration_11/spec.md"}
---
{"file_path":"/Users/rickouyang/Github/trade-tools/.codebuddy/notes/experience.md"}
---
{"file_path":"/Users/rickouyang/Github/trade-tools/tmp/iteration10_audit.md"}
---
   1→# Iteration #11 Spec — 选择器健全性门槛（Reject Degenerate Strategies）
   2→
   3→> 日期：2026-07-07
   4→> Meta-Agent：Claude
   5→> 输入依据：`tmp/iteration10_audit.md`（三方综合审计 + 本机实测）、`iterations/iteration_10/summary.md`、`mytrader/config/strategy_weights.json`、`.codebuddy/notes/experience.md` #6-#8、meta-agent skill Gate 1（新增 Trade health 行）
   6→> 风险等级：**低**（仅修改 `mytrader/backtest/matrix_backtest.py` 选择器逻辑，不触及 risk/execution/strategy/策略代码）
   7→> 核心目标：在 MatrixBacktest 的 top-K 选择**排序之前**，剔除"退化策略"（几乎不平仓的伪 buy-and-hold），使 `strategy_weights.json` 不再包含 win_rate=NaN/≈0 的策略。
   8→
   9→---
  10→
  11→## 1. 背景
  12→
  13→Iter #10 的 reoptimize（Alpha 排序）产出灾难性结果：
  14→
  15→| 指标 | Iter #7 | Iter #10 |
  16→|------|---------|----------|
  17→| 年化 | 8.02% | **-4.88%** |
  18→| Sortino | 1.03 | **-0.66** |
  19→| Alpha | -11.34% | **-25.26%** |
  20→
  21→三方审计 + 本机实测（`tmp/audit_verify.py`）证实根因：
  22→
  23→- `rsi_trend_filter` 入场条件（`close>SMA200`）与出场条件（`close<SMA200`）在趋势方向上互斥 → 多头行情中**仓位几乎永不平仓**。真实数据上对 5 只股票产生 **0 个出场信号**，每只只开 1 仓挂到末尾强平，**win_rate 全为 NaN**（经 `_safe_float` 归零 → `strategy_weights.json` 里 `backtest_win_rate=0.0053`）。
  24→- 它的"收益/Sortino"只是持仓逐日盯市 + 末尾强平凑出来的（退化 buy-and-hold），不是策略交易能力。
  25→- **选择器没有任何健全性门槛**，让这个伪策略骗过了 alpha 排序，进入 4/6 组权重。
  26→
  27→**关键教训（experience.md #8）**：排序（选 top-K）之前必须先过硬门槛，顺序为 ① 健全性 → ② 风险(DD) → ③ 排序。本轮只补 ①（最便宜、能拦住整个灾难的 gate）。
  28→
  29→---
  30→
  31→## 2. Problem Statement
  32→
  33→### 当前代码（`matrix_backtest.py::_run_group`）
  34→
  35→`group_results` 里的每个策略无论是否真的完成交易闭环，都直接进入 candidates 参与 DD/Sortino/Alpha 三级过滤和排序。退化策略（0 平仓交易）因逐日盯市有"漂亮"的 Sortino/alpha，会被选中。
  36→
  37→### 缺失的信号
  38→
  39→`SingleBacktestResult` 目前记录了 `total_trades` 和 `win_rate_pct`，但：
  40→- `total_trades` 包含未平仓的 open trade（末尾强平计 1 笔），无法区分"真交易"和"买一次不动"。
  41→- `win_rate_pct` 在零平仓交易时被 `_safe_float(NaN)` 归零，丢失了"退化"这一信息。
  42→
  43→需要一个**明确的"已平仓交易数"**信号来识别退化策略。
  44→
  45→### 解决方案
  46→
  47→1. 给 `SingleBacktestResult` 新增 `closed_trades: int` 字段（vbt 已平仓交易数）。
  48→2. 在 `_backtest_one` 和 `_backtest_batch` 中从 vbt 提取 `pf.trades.status_closed.count()` 填充。
  49→3. 在 `_run_group` 中新增**健全性过滤**（在 DD/Sortino/Alpha 过滤之前）：剔除退化策略。
  50→4. 若某组所有策略都退化 → 该组产出空权重（持仓现金）并标记 `no_valid_strategy`，**不强行选退化策略**。
  51→
  52→---
  53→
  54→## 3. Scope
  55→
  56→### 本次要做
  57→
  58→1. `SingleBacktestResult` 新增 `closed_trades: int = 0` 字段。
  59→2. `_backtest_one` / `_backtest_batch` 提取并填充 `closed_trades`（batch 与 single 数值一致）。
  60→3. 新增常量 + 健全性判定函数 `_is_degenerate_strategy(results) -> bool`。
  61→4. `_run_group` 在候选排序前加健全性过滤；全退化时产出空权重 + `no_valid_strategy` 标记。
  62→5. `strategy_weights.json` 权重条目在全退化组体现为空列表（该组无策略）；`GroupBacktestResult` 增加可选标记字段。
  63→6. 新增/更新测试。
  64→7. 更新 `designs/design_v2/07-backtest-module.md` + trajectory + decision_log + CODEBUDDY。
  65→
  66→### 本次不做（明确排除，留给后续迭代）
  67→
  68→1. **不**改 alpha 排序为 OOS/Walk-Forward 验证期 alpha（→ Iter #12）。
  69→2. **不**新增 `alpha>0` 硬门槛（→ Iter #12）；保留现有 DD+Sortino+Alpha 排序作用于"通过健全性过滤后的存活候选"。
  70→3. **不**修 `rsi_trend_filter` 的出场逻辑（健全性门槛会自动排除它；策略重设计是独立任务）。
  71→4. **不**触及 `mytrader/risk/`、`mytrader/execution/`、任何策略文件、指标文件。
  72→5. **不**改 DD 阈值 / 仓位上限 / 止损止盈。
  73→6. **不**运行 `--reoptimize`（由 Meta-Agent 验收时独立运行）。
  74→
  75→---
  76→
  77→## 4. Detailed Design
  78→
  79→### 4.1 `SingleBacktestResult` 新增字段
  80→
  81→`matrix_backtest.py`（约 line 54）：
  82→
  83→```python
  84→@dataclass
  85→class SingleBacktestResult:
  86→    symbol: str
  87→    strategy: str
  88→    params: dict
  89→    sharpe: float
  90→    total_return_pct: float
  91→    max_drawdown_pct: float
  92→    win_rate_pct: float
  93→    total_trades: int
  94→    daily_returns: pd.Series
  95→    sortino: float = 0.0
  96→    closed_trades: int = 0    # 迭代 #11 新增：已平仓交易数（区分退化 buy-and-hold）
  97→```
  98→
  99→### 4.2 提取 closed_trades
 100→
 101→在 `_backtest_one`（约 line 372）和 `_backtest_batch`（约 line 526）提取 stats 处，新增：
 102→
 103→```python
 104→# 迭代 #11：已平仓交易数（用于健全性门槛）
 105→# vbt 1.0: pf.trades.status_closed.count() 返回已平仓交易数
 106→try:
 107→    closed_trades = int(pf.trades.status_closed.count())  # _backtest_one
 108→    # batch 模式用 pf_sym.trades.status_closed.count()
 109→except Exception:
 110→    closed_trades = 0
 111→```
 112→
 113→> 实现要求：`_backtest_batch` 的 `closed_trades` 提取必须与 `_backtest_one` 对同一标的数值一致（沿用 Iter #10 的 batch-vs-single 一致性测试范式）。若 vbt API 名称不同，实现者需查 vbt 1.0.0 实际 API（如 `pf.trades.closed.count()` 或 `pf_sym.trades.records_readable` 中 status 字段）并保证正确性；提取失败降级为 0，不抛异常。
 114→
 115→### 4.3 健全性判定函数
 116→
 117→新增常量（约 line 47，`MIN_SORTINO_THRESHOLD` 附近）：
 118→
 119→```python
 120→# 迭代 #11：健全性门槛 —— 识别"退化策略"（几乎不平仓的伪 buy-and-hold）
 121→# 判定：组内"有效标的中，已平仓交易数为 0 的比例"超过此阈值 → 退化
 122→# 设计动机：真策略应在多数标的上完成买卖闭环；若近乎所有标的都从不平仓，
 123→#           说明入场/出场条件矛盾（如 Iter #8 rsi_trend_filter），其收益只是
 124→#           持仓盯市 + 末尾强平的假象，必须在排序前剔除。
 125→# 阈值取 0.8（保守）：只在"近乎全部标的零平仓"时触发，避免误伤低频合法策略。
 126→DEGENERATE_NO_CLOSE_FRACTION: float = 0.8
 127→```
 128→
 129→函数（`_combine_daily_returns` 附近）：
 130→
 131→```python
 132→def _is_degenerate_strategy(results: list[SingleBacktestResult]) -> bool:
 133→    """判定一个策略在组内是否退化（几乎不产生已平仓交易）。
 134→
 135→    退化定义：有效标的中 closed_trades==0 的比例 >= DEGENERATE_NO_CLOSE_FRACTION。
 136→    这类策略的入场/出场条件互斥（如趋势过滤锁死了均值回归出场），仓位无法平仓，
 137→    其 Sortino/alpha 只是持仓盯市假象，不代表真实交易能力，必须在选择前剔除。
 138→
 139→    Args:
 140→        results: 单策略多标的的回测结果列表
 141→
 142→    Returns:
 143→        True 表示退化（应剔除）；空结果视为退化（True）
 144→    """
 145→    if not results:
 146→        return True
 147→    n = len(results)
 148→    no_close = sum(1 for r in results if r.closed_trades <= 0)
 149→    return (no_close / n) >= DEGENERATE_NO_CLOSE_FRACTION
 150→```
 151→
 152→### 4.4 `_run_group` 集成健全性过滤
 153→
 154→在 `group_results` 收集完成、构建 `candidates` **之前**（约 line 1131 `if not group_results` 之后、line 1147 candidates 构建之前）插入：
 155→
 156→```python
 157→# 迭代 #11：健全性过滤 —— 排序前先剔除退化策略（experience.md #8：sanity → risk → rank）
 158→sane_results = []
 159→for (strategy, params, results) in group_results:
 160→    if _is_degenerate_strategy(results):
 161→        logger.warning(
 162→            f"[MatrixBacktest] {group_id}: strategy '{strategy}' is DEGENERATE "
 163→            f"(>= {DEGENERATE_NO_CLOSE_FRACTION:.0%} symbols have 0 closed trades) "
 164→            f"— excluded before ranking. Its Sortino/alpha is mark-to-market illusion."
 165→        )
 166→        continue
 167→    sane_results.append((strategy, params, results))
 168→
 169→if not sane_results:
 170→    # 全组退化 → 空权重（持仓现金），标记 no_valid_strategy，不强行选退化策略
 171→    logger.warning(
 172→        f"[MatrixBacktest] {group_id}: ALL strategies degenerate — "
 173→        f"group produces EMPTY weights (hold cash). Marked no_valid_strategy."
 174→    )
 175→    report.warnings.append(f"{group_id}: no_valid_strategy (all strategies degenerate)")
 176→    # 标记对应 GroupBacktestResult（若已 append）
 177→    for gr in report.group_results:
 178→        if gr.group_id == group_id:
 179→            gr.no_valid_strategy = True
 180→    return []
 181→
 182→# 后续 candidates 构建、DD/Sortino/Alpha 过滤、排序，全部改用 sane_results 替代 group_results
 183→group_results = sane_results
 184→```
 185→
 186→> 注意：`report.group_results` 中已 append 的退化策略条目应保留（供审计追溯），但不进入 `weights_list`。由于健全性过滤发生在 candidates 构建前，退化策略自然不会出现在最终权重里。
 187→
 188→### 4.5 `GroupBacktestResult` 新增标记
 189→
 190→```python
 191→@dataclass
 192→class GroupBacktestResult:
 193→    # ... 现有字段 ...
 194→    backtest_alpha: float = 0.0
 195→    no_valid_strategy: bool = False   # 迭代 #11：该组是否因全退化而空仓
 196→```
 197→
 198→---
 199→
 200→## 5. 测试计划
 201→
 202→新增 `tests/test_degenerate_filter.py`（或扩展 `test_matrix_backtest.py`）：
 203→
 204→1. **test_closed_trades_populated** — 正常策略回测结果的 `closed_trades > 0`。
 205→2. **test_closed_trades_batch_matches_single** — batch 与 single 的 `closed_trades` 对同一标的一致（沿用 Iter #10 一致性范式）。
 206→3. **test_degenerate_detected** — 构造"只有 entries 无 exits"的信号（仓位挂到末尾），`_is_degenerate_strategy` 返回 True。
 207→4. **test_normal_not_degenerate** — 正常闭环策略（有平仓交易）返回 False。
 208→5. **test_degenerate_excluded_from_weights** — `_run_group` 中退化策略不出现在返回的 weights_list（用 mock/构造数据 + 真实 store fixture 二选一，参考现有 test_matrix_backtest.py 风格）。
 209→6. **test_all_degenerate_group_empty** — 组内全部策略退化 → 返回空列表 + `no_valid_strategy=True` 标记。
 210→7. **test_low_frequency_strategy_not_falsely_excluded** — 低频但有平仓交易的策略（如每标的 2-3 笔）不被误判为退化（验证 0.8 阈值不误伤）。
 211→
 212→### 回归
 213→
 214→现有 `tests/test_matrix_backtest.py`、`tests/test_batch_backtest.py` 全部通过（验证健全性过滤没破坏 DD/Sortino/Alpha 排序、batch 一致性）。
 215→
 216→---
 217→
 218→## 6. Success Criteria
 219→
 220→1. `SingleBacktestResult.closed_trades` 字段存在并被 `_backtest_one`/`_backtest_batch` 正确填充。
 221→2. `_is_degenerate_strategy` 正确识别"近乎全标的零平仓"的退化策略。
 222→3. `_run_group` 在排序前剔除退化策略；全退化组返回空权重 + `no_valid_strategy` 标记。
 223→4. 退化策略（如 `rsi_trend_filter` 当前实现）不再进入 `strategy_weights.json`。
 224→5. 默认 pytest 通过（626+ 测试，0 failed）；新增测试 ≥ 6 个。
 225→6. batch 与 single 的 `closed_trades` 数值一致。
 226→7. 不修改 risk/execution/策略/指标代码；不改 alpha 排序为 OOS；不加 alpha>0 硬门槛。
 227→8. 更新 `designs/design_v2/07-backtest-module.md` + trajectory + decision_log + CODEBUDDY。
 228→
 229→### 验收阶段（Meta-Agent 独立执行）
 230→
 231→- 运行 `python main.py --reoptimize`，验证：
 232→  - `rsi_trend_filter` 不再出现在任何组权重中；
 233→  - 各组权重 `backtest_win_rate` 不再是 ≈0 的退化值；
 234→  - PortfolioBacktest 组合指标从 Iter #10 的 alpha=-25% 恢复到 ≈Iter #7 的可信基线（正收益、Sortino>0）。
 235→
 236→---
 237→
 238→## 7. Implementation Order
 239→
 240→1. 读 spec + `matrix_backtest.py`（重点 `_backtest_one` / `_backtest_batch` / `_run_group`）+ `experience.md` + `tmp/iteration10_audit.md`。
 241→2. 查 vbt 1.0.0 已平仓交易 API，先写一个最小验证脚本确认 `closed_trades` 提取正确。
 242→3. 给 `SingleBacktestResult` 加 `closed_trades`，在 `_backtest_one`/`_backtest_batch` 填充。
 243→4. 写 `closed_trades` 一致性测试（batch vs single）。
 244→5. 加 `DEGENERATE_NO_CLOSE_FRACTION` 常量 + `_is_degenerate_strategy`。
 245→6. `_run_group` 集成健全性过滤 + 全退化空仓分支 + `GroupBacktestResult.no_valid_strategy`。
 246→7. 写健全性过滤测试（含误伤边界 test_low_frequency）。
 247→8. 运行 targeted tests + 默认 pytest。
 248→9. 更新 `designs/design_v2/07-backtest-module.md` + trajectory + decision_log + CODEBUDDY。
 249→
 250→---
 251→
 252→## 8. Risk Classification
 253→
 254→- **低风险**：仅改 `mytrader/backtest/matrix_backtest.py`（非 Constitution L8 高风险目录）。
 255→- **行为变更**：健全性过滤会改变 `strategy_weights.json` 输出（退化策略被剔除；极端情况下某组空仓）。这是**预期且正确**的行为——系统拒绝交易伪策略优于交易 -25% 的垃圾。
 256→- **缓解**：严格的 batch-vs-single 一致性测试 + 误伤边界测试（低频策略不被误判）。
 257→- **Constitution 合规**：健全性门槛不违反 L1（Sortino 仍是 KPI）；DD 硬约束不变；不引入 RL/黑箱。
 258→- **回滚**：若健全性过滤误伤合法策略，可上调 `DEGENERATE_NO_CLOSE_FRACTION` 或临时禁用过滤。
 259→
---
   1→# Iteration #11 Spec — 选择器健全性门槛（Reject Degenerate Strategies）
   2→
   3→> 日期：2026-07-07
   4→> Meta-Agent：Claude
   5→> 输入依据：`tmp/iteration10_audit.md`（三方综合审计 + 本机实测）、`iterations/iteration_10/summary.md`、`mytrader/config/strategy_weights.json`、`.codebuddy/notes/experience.md` #6-#8、meta-agent skill Gate 1（新增 Trade health 行）
   6→> 风险等级：**低**（仅修改 `mytrader/backtest/matrix_backtest.py` 选择器逻辑，不触及 risk/execution/strategy/策略代码）
   7→> 核心目标：在 MatrixBacktest 的 top-K 选择**排序之前**，剔除"退化策略"（几乎不平仓的伪 buy-and-hold），使 `strategy_weights.json` 不再包含 win_rate=NaN/≈0 的策略。
   8→
   9→---
  10→
  11→## 1. 背景
  12→
  13→Iter #10 的 reoptimize（Alpha 排序）产出灾难性结果：
  14→
  15→| 指标 | Iter #7 | Iter #10 |
  16→|------|---------|----------|
  17→| 年化 | 8.02% | **-4.88%** |
  18→| Sortino | 1.03 | **-0.66** |
  19→| Alpha | -11.34% | **-25.26%** |
  20→
  21→三方审计 + 本机实测（`tmp/audit_verify.py`）证实根因：
  22→
  23→- `rsi_trend_filter` 入场条件（`close>SMA200`）与出场条件（`close<SMA200`）在趋势方向上互斥 → 多头行情中**仓位几乎永不平仓**。真实数据上对 5 只股票产生 **0 个出场信号**，每只只开 1 仓挂到末尾强平，**win_rate 全为 NaN**（经 `_safe_float` 归零 → `strategy_weights.json` 里 `backtest_win_rate=0.0053`）。
  24→- 它的"收益/Sortino"只是持仓逐日盯市 + 末尾强平凑出来的（退化 buy-and-hold），不是策略交易能力。
  25→- **选择器没有任何健全性门槛**，让这个伪策略骗过了 alpha 排序，进入 4/6 组权重。
  26→
  27→**关键教训（experience.md #8）**：排序（选 top-K）之前必须先过硬门槛，顺序为 ① 健全性 → ② 风险(DD) → ③ 排序。本轮只补 ①（最便宜、能拦住整个灾难的 gate）。
  28→
  29→---
  30→
  31→## 2. Problem Statement
  32→
  33→### 当前代码（`matrix_backtest.py::_run_group`）
  34→
  35→`group_results` 里的每个策略无论是否真的完成交易闭环，都直接进入 candidates 参与 DD/Sortino/Alpha 三级过滤和排序。退化策略（0 平仓交易）因逐日盯市有"漂亮"的 Sortino/alpha，会被选中。
  36→
  37→### 缺失的信号
  38→
  39→`SingleBacktestResult` 目前记录了 `total_trades` 和 `win_rate_pct`，但：
  40→- `total_trades` 包含未平仓的 open trade（末尾强平计 1 笔），无法区分"真交易"和"买一次不动"。
  41→- `win_rate_pct` 在零平仓交易时被 `_safe_float(NaN)` 归零，丢失了"退化"这一信息。
  42→
  43→需要一个**明确的"已平仓交易数"**信号来识别退化策略。
  44→
  45→### 解决方案
  46→
  47→1. 给 `SingleBacktestResult` 新增 `closed_trades: int` 字段（vbt 已平仓交易数）。
  48→2. 在 `_backtest_one` 和 `_backtest_batch` 中从 vbt 提取 `pf.trades.status_closed.count()` 填充。
  49→3. 在 `_run_group` 中新增**健全性过滤**（在 DD/Sortino/Alpha 过滤之前）：剔除退化策略。
  50→4. 若某组所有策略都退化 → 该组产出空权重（持仓现金）并标记 `no_valid_strategy`，**不强行选退化策略**。
  51→
  52→---
  53→
  54→## 3. Scope
  55→
  56→### 本次要做
  57→
  58→1. `SingleBacktestResult` 新增 `closed_trades: int = 0` 字段。
  59→2. `_backtest_one` / `_backtest_batch` 提取并填充 `closed_trades`（batch 与 single 数值一致）。
  60→3. 新增常量 + 健全性判定函数 `_is_degenerate_strategy(results) -> bool`。
  61→4. `_run_group` 在候选排序前加健全性过滤；全退化时产出空权重 + `no_valid_strategy` 标记。
  62→5. `strategy_weights.json` 权重条目在全退化组体现为空列表（该组无策略）；`GroupBacktestResult` 增加可选标记字段。
  63→6. 新增/更新测试。
  64→7. 更新 `designs/design_v2/07-backtest-module.md` + trajectory + decision_log + CODEBUDDY。
  65→
  66→### 本次不做（明确排除，留给后续迭代）
  67→
  68→1. **不**改 alpha 排序为 OOS/Walk-Forward 验证期 alpha（→ Iter #12）。
  69→2. **不**新增 `alpha>0` 硬门槛（→ Iter #12）；保留现有 DD+Sortino+Alpha 排序作用于"通过健全性过滤后的存活候选"。
  70→3. **不**修 `rsi_trend_filter` 的出场逻辑（健全性门槛会自动排除它；策略重设计是独立任务）。
  71→4. **不**触及 `mytrader/risk/`、`mytrader/execution/`、任何策略文件、指标文件。
  72→5. **不**改 DD 阈值 / 仓位上限 / 止损止盈。
  73→6. **不**运行 `--reoptimize`（由 Meta-Agent 验收时独立运行）。
  74→
  75→---
  76→
  77→## 4. Detailed Design
  78→
  79→### 4.1 `SingleBacktestResult` 新增字段
  80→
  81→`matrix_backtest.py`（约 line 54）：
  82→
  83→```python
  84→@dataclass
  85→class SingleBacktestResult:
  86→    symbol: str
  87→    strategy: str
  88→    params: dict
  89→    sharpe: float
  90→    total_return_pct: float
  91→    max_drawdown_pct: float
  92→    win_rate_pct: float
  93→    total_trades: int
  94→    daily_returns: pd.Series
  95→    sortino: float = 0.0
  96→    closed_trades: int = 0    # 迭代 #11 新增：已平仓交易数（区分退化 buy-and-hold）
  97→```
  98→
  99→### 4.2 提取 closed_trades
 100→
 101→在 `_backtest_one`（约 line 372）和 `_backtest_batch`（约 line 526）提取 stats 处，新增：
 102→
 103→```python
 104→# 迭代 #11：已平仓交易数（用于健全性门槛）
 105→# vbt 1.0: pf.trades.status_closed.count() 返回已平仓交易数
 106→try:
 107→    closed_trades = int(pf.trades.status_closed.count())  # _backtest_one
 108→    # batch 模式用 pf_sym.trades.status_closed.count()
 109→except Exception:
 110→    closed_trades = 0
 111→```
 112→
 113→> 实现要求：`_backtest_batch` 的 `closed_trades` 提取必须与 `_backtest_one` 对同一标的数值一致（沿用 Iter #10 的 batch-vs-single 一致性测试范式）。若 vbt API 名称不同，实现者需查 vbt 1.0.0 实际 API（如 `pf.trades.closed.count()` 或 `pf_sym.trades.records_readable` 中 status 字段）并保证正确性；提取失败降级为 0，不抛异常。
 114→
 115→### 4.3 健全性判定函数
 116→
 117→新增常量（约 line 47，`MIN_SORTINO_THRESHOLD` 附近）：
 118→
 119→```python
 120→# 迭代 #11：健全性门槛 —— 识别"退化策略"（几乎不平仓的伪 buy-and-hold）
 121→# 判定：组内"有效标的中，已平仓交易数为 0 的比例"超过此阈值 → 退化
 122→# 设计动机：真策略应在多数标的上完成买卖闭环；若近乎所有标的都从不平仓，
 123→#           说明入场/出场条件矛盾（如 Iter #8 rsi_trend_filter），其收益只是
 124→#           持仓盯市 + 末尾强平的假象，必须在排序前剔除。
 125→# 阈值取 0.8（保守）：只在"近乎全部标的零平仓"时触发，避免误伤低频合法策略。
 126→DEGENERATE_NO_CLOSE_FRACTION: float = 0.8
 127→```
 128→
 129→函数（`_combine_daily_returns` 附近）：
 130→
 131→```python
 132→def _is_degenerate_strategy(results: list[SingleBacktestResult]) -> bool:
 133→    """判定一个策略在组内是否退化（几乎不产生已平仓交易）。
 134→
 135→    退化定义：有效标的中 closed_trades==0 的比例 >= DEGENERATE_NO_CLOSE_FRACTION。
 136→    这类策略的入场/出场条件互斥（如趋势过滤锁死了均值回归出场），仓位无法平仓，
 137→    其 Sortino/alpha 只是持仓盯市假象，不代表真实交易能力，必须在选择前剔除。
 138→
 139→    Args:
 140→        results: 单策略多标的的回测结果列表
 141→
 142→    Returns:
 143→        True 表示退化（应剔除）；空结果视为退化（True）
 144→    """
 145→    if not results:
 146→        return True
 147→    n = len(results)
 148→    no_close = sum(1 for r in results if r.closed_trades <= 0)
 149→    return (no_close / n) >= DEGENERATE_NO_CLOSE_FRACTION
 150→```
 151→
 152→### 4.4 `_run_group` 集成健全性过滤
 153→
 154→在 `group_results` 收集完成、构建 `candidates` **之前**（约 line 1131 `if not group_results` 之后、line 1147 candidates 构建之前）插入：
 155→
 156→```python
 157→# 迭代 #11：健全性过滤 —— 排序前先剔除退化策略（experience.md #8：sanity → risk → rank）
 158→sane_results = []
 159→for (strategy, params, results) in group_results:
 160→    if _is_degenerate_strategy(results):
 161→        logger.warning(
 162→            f"[MatrixBacktest] {group_id}: strategy '{strategy}' is DEGENERATE "
 163→            f"(>= {DEGENERATE_NO_CLOSE_FRACTION:.0%} symbols have 0 closed trades) "
 164→            f"— excluded before ranking. Its Sortino/alpha is mark-to-market illusion."
 165→        )
 166→        continue
 167→    sane_results.append((strategy, params, results))
 168→
 169→if not sane_results:
 170→    # 全组退化 → 空权重（持仓现金），标记 no_valid_strategy，不强行选退化策略
 171→    logger.warning(
 172→        f"[MatrixBacktest] {group_id}: ALL strategies degenerate — "
 173→        f"group produces EMPTY weights (hold cash). Marked no_valid_strategy."
 174→    )
 175→    report.warnings.append(f"{group_id}: no_valid_strategy (all strategies degenerate)")
 176→    # 标记对应 GroupBacktestResult（若已 append）
 177→    for gr in report.group_results:
 178→        if gr.group_id == group_id:
 179→            gr.no_valid_strategy = True
 180→    return []
 181→
 182→# 后续 candidates 构建、DD/Sortino/Alpha 过滤、排序，全部改用 sane_results 替代 group_results
 183→group_results = sane_results
 184→```
 185→
 186→> 注意：`report.group_results` 中已 append 的退化策略条目应保留（供审计追溯），但不进入 `weights_list`。由于健全性过滤发生在 candidates 构建前，退化策略自然不会出现在最终权重里。
 187→
 188→### 4.5 `GroupBacktestResult` 新增标记
 189→
 190→```python
 191→@dataclass
 192→class GroupBacktestResult:
 193→    # ... 现有字段 ...
 194→    backtest_alpha: float = 0.0
 195→    no_valid_strategy: bool = False   # 迭代 #11：该组是否因全退化而空仓
 196→```
 197→
 198→---
 199→
 200→## 5. 测试计划
 201→
 202→新增 `tests/test_degenerate_filter.py`（或扩展 `test_matrix_backtest.py`）：
 203→
 204→1. **test_closed_trades_populated** — 正常策略回测结果的 `closed_trades > 0`。
 205→2. **test_closed_trades_batch_matches_single** — batch 与 single 的 `closed_trades` 对同一标的一致（沿用 Iter #10 一致性范式）。
 206→3. **test_degenerate_detected** — 构造"只有 entries 无 exits"的信号（仓位挂到末尾），`_is_degenerate_strategy` 返回 True。
 207→4. **test_normal_not_degenerate** — 正常闭环策略（有平仓交易）返回 False。
 208→5. **test_degenerate_excluded_from_weights** — `_run_group` 中退化策略不出现在返回的 weights_list（用 mock/构造数据 + 真实 store fixture 二选一，参考现有 test_matrix_backtest.py 风格）。
 209→6. **test_all_degenerate_group_empty** — 组内全部策略退化 → 返回空列表 + `no_valid_strategy=True` 标记。
 210→7. **test_low_frequency_strategy_not_falsely_excluded** — 低频但有平仓交易的策略（如每标的 2-3 笔）不被误判为退化（验证 0.8 阈值不误伤）。
 211→
 212→### 回归
 213→
 214→现有 `tests/test_matrix_backtest.py`、`tests/test_batch_backtest.py` 全部通过（验证健全性过滤没破坏 DD/Sortino/Alpha 排序、batch 一致性）。
 215→
 216→---
 217→
 218→## 6. Success Criteria
 219→
 220→1. `SingleBacktestResult.closed_trades` 字段存在并被 `_backtest_one`/`_backtest_batch` 正确填充。
 221→2. `_is_degenerate_strategy` 正确识别"近乎全标的零平仓"的退化策略。
 222→3. `_run_group` 在排序前剔除退化策略；全退化组返回空权重 + `no_valid_strategy` 标记。
 223→4. 退化策略（如 `rsi_trend_filter` 当前实现）不再进入 `strategy_weights.json`。
 224→5. 默认 pytest 通过（626+ 测试，0 failed）；新增测试 ≥ 6 个。
 225→6. batch 与 single 的 `closed_trades` 数值一致。
 226→7. 不修改 risk/execution/策略/指标代码；不改 alpha 排序为 OOS；不加 alpha>0 硬门槛。
 227→8. 更新 `designs/design_v2/07-backtest-module.md` + trajectory + decision_log + CODEBUDDY。
 228→
 229→### 验收阶段（Meta-Agent 独立执行）
 230→
 231→- 运行 `python main.py --reoptimize`，验证：
 232→  - `rsi_trend_filter` 不再出现在任何组权重中；
 233→  - 各组权重 `backtest_win_rate` 不再是 ≈0 的退化值；
 234→  - PortfolioBacktest 组合指标从 Iter #10 的 alpha=-25% 恢复到 ≈Iter #7 的可信基线（正收益、Sortino>0）。
 235→
 236→---
 237→
 238→## 7. Implementation Order
 239→
 240→1. 读 spec + `matrix_backtest.py`（重点 `_backtest_one` / `_backtest_batch` / `_run_group`）+ `experience.md` + `tmp/iteration10_audit.md`。
 241→2. 查 vbt 1.0.0 已平仓交易 API，先写一个最小验证脚本确认 `closed_trades` 提取正确。
 242→3. 给 `SingleBacktestResult` 加 `closed_trades`，在 `_backtest_one`/`_backtest_batch` 填充。
 243→4. 写 `closed_trades` 一致性测试（batch vs single）。
 244→5. 加 `DEGENERATE_NO_CLOSE_FRACTION` 常量 + `_is_degenerate_strategy`。
 245→6. `_run_group` 集成健全性过滤 + 全退化空仓分支 + `GroupBacktestResult.no_valid_strategy`。
 246→7. 写健全性过滤测试（含误伤边界 test_low_frequency）。
 247→8. 运行 targeted tests + 默认 pytest。
 248→9. 更新 `designs/design_v2/07-backtest-module.md` + trajectory + decision_log + CODEBUDDY。
 249→
 250→---
 251→
 252→## 8. Risk Classification
 253→
 254→- **低风险**：仅改 `mytrader/backtest/matrix_backtest.py`（非 Constitution L8 高风险目录）。
 255→- **行为变更**：健全性过滤会改变 `strategy_weights.json` 输出（退化策略被剔除；极端情况下某组空仓）。这是**预期且正确**的行为——系统拒绝交易伪策略优于交易 -25% 的垃圾。
 256→- **缓解**：严格的 batch-vs-single 一致性测试 + 误伤边界测试（低频策略不被误判）。
 257→- **Constitution 合规**：健全性门槛不违反 L1（Sortino 仍是 KPI）；DD 硬约束不变；不引入 RL/黑箱。
 258→- **回滚**：若健全性过滤误伤合法策略，可上调 `DEGENERATE_NO_CLOSE_FRACTION` 或临时禁用过滤。
 259→
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
  47→## 6. 单元测试测"信号正确"，但不测"策略能否完成交易闭环"
  48→
  49→**背景**：Iter #8 的 `rsi_trend_filter` 单元测试全绿（信号 ∈ {-1,0,1}、上升趋势不 SELL、下降趋势不 BUY），却在真实回测中对 5 只股票产生 **0 个出场信号**——入场条件（上升趋势）和出场条件（下降趋势）在趋势方向上互斥，仓位永远无法平仓，退化成滞后 buy-and-hold。最讽刺的是：`test_uptrend_only_buy` / `test_downtrend_only_sell` 这两个"通过"的测试，验证的恰恰是导致 Bug 的那个特性，把致命缺陷当成正确行为认证了。
  50→
  51→**原则**：
  52→- 策略测试必须包含**交易闭环测试**：给一段真实/半真实数据，跑一次回测，断言 `已平仓交易数 ≥ 阈值`、`win_rate 非 NaN`、`持仓暴露时间比例合理`
  53→- 入场和出场条件不能在同一维度上互斥（否则买了卖不掉）。设计策略时先问：**"我这笔仓位靠什么信号平掉？这个信号在目标行情里会不会几乎不触发？"**
  54→- `win_rate=NaN / 交易笔数≈0` 但 Sortino/收益却正常，是"仓位不平仓、靠盯市和末尾强平凑出收益"的强信号，必须当异常查
  55→
  56→## 7. "被选中" ≠ "有效"；指标是过滤器，不是优化目标
  57→
  58→**背景**：Iter #9 为了让 `rsi_trend_filter` 能入选，把选择器从 Sortino 排序改成样本内 Alpha 排序。结果坏策略确实进了 4/6 组权重（"被选中"），但样本外组合 alpha 从 -11% 崩到 -25%。换指标只是把样本内的 regime 运气暴露出来，放大了过拟合。
  59→
  60→**原则**：
  61→- 一个策略"能进权重"不代表"有效"。判断有效的标准是**样本外表现**，不是它在选择器里排第几
  62→- **在同一段数据上同时做参数搜索 + 策略选择，无论用什么单指标（Sortino/Sharpe/Alpha）都必然过拟合**。选择必须用样本外指标（Walk-Forward 验证期），或专用 holdout（前 N 年调参、后 1 年选策略）
  63→- 遇到"结果变差"时，先质疑**输入的策略/数据是否本身就坏**，再去调选择指标。别把"策略坏了"误诊成"指标选错了"（DeepSeek 就栽在这句上）
  64→
  65→## 8. 排序前必须先过硬门槛：健全性 + 风险 + 正超额
  66→
  67→**背景**：当前 `_run_group` 的选择逻辑允许：0 平仓交易的退化策略、alpha 全负时选"没那么差"的负 alpha、负 alpha 被 `max(alpha,0.01)` 归一化成等权。WF 4/4 pass 但组合 alpha=-25%，因为 WF gate 只校验 DD/Sortino 不校验 alpha。
  68→
  69→**原则**：
  70→- 排序（选 top-K）之前，先过**硬门槛过滤**，顺序：① 健全性（交易笔数/win_rate 非退化）→ ② 风险（DD≤20%）→ ③ 正超额（alpha>0 或 >benchmark_margin）→ 最后才在合规候选里排序
  71→- **没有候选满足门槛时，正确动作是"空仓/降现金/回退 benchmark"，不是"矬子里拔将军"强行 top-K**
  72→- 验收 gate（无论 WF 还是 paper 准入）必须校验**跑赢 benchmark（正 alpha）**，DD/Sortino 达标 ≠ 有正 alpha
  73→- 归一化权重时，负分不能用 `max(x, ε)` 掩盖——那会把"都不好"变成"等权都要"
  74→
  75→---
  76→
  77→*持续更新。每犯一次新类型的错误，提炼一条原则。*
  78→
  79→
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
  47→## 6. 单元测试测"信号正确"，但不测"策略能否完成交易闭环"
  48→
  49→**背景**：Iter #8 的 `rsi_trend_filter` 单元测试全绿（信号 ∈ {-1,0,1}、上升趋势不 SELL、下降趋势不 BUY），却在真实回测中对 5 只股票产生 **0 个出场信号**——入场条件（上升趋势）和出场条件（下降趋势）在趋势方向上互斥，仓位永远无法平仓，退化成滞后 buy-and-hold。最讽刺的是：`test_uptrend_only_buy` / `test_downtrend_only_sell` 这两个"通过"的测试，验证的恰恰是导致 Bug 的那个特性，把致命缺陷当成正确行为认证了。
  50→
  51→**原则**：
  52→- 策略测试必须包含**交易闭环测试**：给一段真实/半真实数据，跑一次回测，断言 `已平仓交易数 ≥ 阈值`、`win_rate 非 NaN`、`持仓暴露时间比例合理`
  53→- 入场和出场条件不能在同一维度上互斥（否则买了卖不掉）。设计策略时先问：**"我这笔仓位靠什么信号平掉？这个信号在目标行情里会不会几乎不触发？"**
  54→- `win_rate=NaN / 交易笔数≈0` 但 Sortino/收益却正常，是"仓位不平仓、靠盯市和末尾强平凑出收益"的强信号，必须当异常查
  55→
  56→## 7. "被选中" ≠ "有效"；指标是过滤器，不是优化目标
  57→
  58→**背景**：Iter #9 为了让 `rsi_trend_filter` 能入选，把选择器从 Sortino 排序改成样本内 Alpha 排序。结果坏策略确实进了 4/6 组权重（"被选中"），但样本外组合 alpha 从 -11% 崩到 -25%。换指标只是把样本内的 regime 运气暴露出来，放大了过拟合。
  59→
  60→**原则**：
  61→- 一个策略"能进权重"不代表"有效"。判断有效的标准是**样本外表现**，不是它在选择器里排第几
  62→- **在同一段数据上同时做参数搜索 + 策略选择，无论用什么单指标（Sortino/Sharpe/Alpha）都必然过拟合**。选择必须用样本外指标（Walk-Forward 验证期），或专用 holdout（前 N 年调参、后 1 年选策略）
  63→- 遇到"结果变差"时，先质疑**输入的策略/数据是否本身就坏**，再去调选择指标。别把"策略坏了"误诊成"指标选错了"（DeepSeek 就栽在这句上）
  64→
  65→## 8. 排序前必须先过硬门槛：健全性 + 风险 + 正超额
  66→
  67→**背景**：当前 `_run_group` 的选择逻辑允许：0 平仓交易的退化策略、alpha 全负时选"没那么差"的负 alpha、负 alpha 被 `max(alpha,0.01)` 归一化成等权。WF 4/4 pass 但组合 alpha=-25%，因为 WF gate 只校验 DD/Sortino 不校验 alpha。
  68→
  69→**原则**：
  70→- 排序（选 top-K）之前，先过**硬门槛过滤**，顺序：① 健全性（交易笔数/win_rate 非退化）→ ② 风险（DD≤20%）→ ③ 正超额（alpha>0 或 >benchmark_margin）→ 最后才在合规候选里排序
  71→- **没有候选满足门槛时，正确动作是"空仓/降现金/回退 benchmark"，不是"矬子里拔将军"强行 top-K**
  72→- 验收 gate（无论 WF 还是 paper 准入）必须校验**跑赢 benchmark（正 alpha）**，DD/Sortino 达标 ≠ 有正 alpha
  73→- 归一化权重时，负分不能用 `max(x, ε)` 掩盖——那会把"都不好"变成"等权都要"
  74→
  75→---
  76→
  77→*持续更新。每犯一次新类型的错误，提炼一条原则。*
  78→
  79→
---
   1→# Iteration #8/9/10 综合审计报告
   2→
   3→> 主题：第 8 轮 `rsi_trend_filter` 方案为什么不 work？
   4→> 审计方：Claude（本机实测）、GPT、DeepSeek 三方综合
   5→> 日期：2026-07-07
   6→> 结论定性：**策略层结构性 Bug（近因，已实测证实）+ 选择器治理漏洞 + 方法论过拟合，三层叠加**
   7→
   8→---
   9→
  10→## 0. 一句话结论
  11→
  12→第 8 轮方案不 work，**不是因为"趋势过滤降低了 Sortino 所以选不进权重"**，而是因为 `rsi_trend_filter` 的入场条件（上升趋势）与出场条件（下降趋势）在趋势方向上互斥，导致多头市场里仓位**几乎永远无法平仓**——它退化成了"买一次、无限期持有"的伪 buy-and-hold；第 9 轮把排序从 Sortino 换成样本内 Alpha，不但没治病，反而把这个坏策略样本内的 regime 运气放大成了满仓押注，第 10 轮样本外 alpha 崩到 **-25.26%** 就是这条误诊链的终点。
  13→
  14→---
  15→
  16→## 1. 关键数据回顾
  17→
  18→| 指标 | Iter #7 (Sortino 排序) | Iter #10 (Alpha 排序) | 变化 |
  19→|------|----------------------|----------------------|------|
  20→| 年化收益 | 8.02% | **-4.88%** | ❌ 亏损 |
  21→| Sortino | 1.03 | **-0.66** | ❌ 负值 |
  22→| Alpha (vs SPY) | -11.34% | **-25.26%** | ❌ 更差 |
  23→| Max DD | 5.95% | 8.39% | ❌ 更大 |
  24→| Walk-Forward | 4/4 pass | 4/4 pass | ✅（但没校验 alpha） |
  25→
  26→---
  27→
  28→## 2. 实证铁证（本机实跑，非理论推断）
  29→
  30→用 `tmp/audit_verify.py` 在**真实数据**（AAPL/MSFT/NVDA/GOOGL/AMZN，2021-2026）上跑两个策略，映射 entries/exits 后过 `vbt.Portfolio.from_signals`：
  31→
  32→| 策略 | 平均入场信号 | **平均出场信号** | 每标的交易数 | win_rate 为 NaN(零平仓)标的 |
  33→|---|---|---|---|---|
  34→| `rsi_mean_revert` | 80 | 61.4 | 5.4 | **0 / 5** |
  35→| `rsi_trend_filter` | 19 | **0.0** | 1.0 | **5 / 5** |
  36→
  37→合成牛市里同样：`rsi_trend_filter` 11 入场 / **2 出场 / 1 笔交易 / win_rate 0% / 标的涨 16% 而策略亏 -18%**。
  38→
  39→**结论钉死**：真实近 5 年数据上，`rsi_trend_filter` 对 5 只股票产生 **0 个出场信号**，每只只开 1 仓、挂到回测末尾被 vbt 强平，win_rate 全为 NaN。这精确解释了 `strategy_weights.json` 里 `backtest_win_rate=0.0053`（NaN→0，与极少数熊市里偶尔触发出场的标的平均而来）。
  40→
  41→---
  42→
  43→## 3. 根因（代码级）
  44→
  45→策略源码 `mytrader/strategy/strategies/rsi_trend_filter.py`：
  46→
  47→```python
  48→signal[(rsi_values < oversold) & above_trend] = 1     # BUY：超卖 且 close > SMA200（上升趋势）
  49→signal[(rsi_values > overbought) & below_trend] = -1  # SELL：超买 且 close < SMA200（下降趋势）
  50→```
  51→
  52→回测引擎 `matrix_backtest.py`：`entries = sig==1`，`exits = sig==-1`，且 `from_signals` **未传任何 sl_stop/tp_stop** → 唯一平仓路径就是 `-1` 信号。
  53→
  54→| | 触发条件 | 趋势方向要求 |
  55→|---|---|---|
  56→| 建仓 BUY | RSI<超卖 | `close > SMA200`（上升趋势）|
  57→| 平仓 SELL | RSI>超买 | `close < SMA200`（下降趋势）|
  58→
  59→**建仓要上升趋势、平仓要下降趋势，两者互斥。** 一笔在上升趋势里开的多单，只有等价格先跌破 SMA200（趋势反转）**且同时** RSI>70 才能平——而价格跌破 200 日线时 RSI 几乎不可能超买。所以这个"趋势过滤的均值回归"实际上无法完成任何一次均值回归的买卖闭环，退化为滞后 buy-and-hold。
  60→
  61→---
  62→
  63→## 4. 三方审计对照（谁对、谁错、谁补了盲区）
  64→
  65→| 审计方 | 定位的根因 | 判定 |
  66→|--------|-----------|------|
  67→| **Claude（本报告）** | 策略层结构性 Bug：出场被入场条件锁死→几乎不平仓→伪 buy-and-hold | ✅ **被实测证实，是直接近因** |
  68→| **GPT** | 策略假设错（是过滤后的均值回归，非趋势收益捕获器）+ 选择器治理漏洞 | ⚠️ 方向对、注意到 win_rate=0.0053 与 "-1 是平多非做空"，但把机制定性为"择时跑输"，比真相软；**选择器治理漏洞是有价值的增量** |
  69→| **DeepSeek** | 方法论：样本内单指标排序必然过拟合；数据未分离；WF 只做 gate 不做 selector | ✅ 方法论正确且重要；**但明确否认"rsi_trend_filter 是坏策略"这句被实测证伪**，把二阶问题当成了主因 |
  70→
  71→### 三层因果关系（对整改最有用的框架）
  72→
  73→要分清两个不同的问题：
  74→
  75→- **策略为什么坏** → Claude 的结构性 Bug（出场条件锁死）。修它 = 改出场逻辑。
  76→- **坏东西为什么能一路进权重、还差点进 paper** → GPT + DeepSeek 的制度性缺陷。补它们 = 加 OOS-alpha 排序、alpha>0 门槛、**最小平仓交易数/win_rate 健全性门槛**。
  77→
  78→> 注意：一条"最小平仓交易数 ≥ N / win_rate 非 NaN"的健全性门槛，本可在第 8 轮当场就把 `rsi_trend_filter` 拦下——它同时来自 Claude（sanity gate）和 GPT（win_rate 观察），比 DeepSeek 主张的 holdout 更早、更便宜。
  79→
  80→---
  81→
  82→## 5. 选择器 / Gate 的制度性漏洞清单（GPT + DeepSeek + Claude 合并）
  83→
  84→1. **无健全性门槛**：策略即使 0 平仓交易、win_rate=NaN，仍能凭"逐日盯市 + 末尾强平"算出的 Sortino/alpha 进权重。
  85→2. **无 `alpha>0` 硬门槛**（`matrix_backtest.py::_run_group`）：某组所有策略 alpha 全负时，仍会选"没那么差"的负 alpha 策略。当前 11 条权重里仅 2 条正 alpha。
  86→3. **负 alpha 归一化退化为等权**（`_optimize_ensemble_weights`）：`max(alpha, 0.01)` 使两个负 alpha 策略被强行 50/50，掩盖坏策略，而不是空仓/降现金/回退 SPY。
  87→4. **样本内选择 = 过拟合**：`_run_group` 在同一段 5 年窗口上同时做参数搜索和 alpha 排序，非真正样本外。
  88→5. **WF 只做 pass/fail，不做 selector**：`run_walk_forward` 算了验证期 Sortino/DD，但没算验证期 alpha，也没把 OOS 指标回传到 top-K 选择。
  89→6. **WF gate 不校验 alpha**：Iter #10 WF 4/4 pass，但组合 alpha=-25.26% —— DD/Sortino 过关 ≠ 有正 alpha。
  90→7. **幸存者偏差**：用当前成分股回测，代码自己已 warning，alpha 被系统性高估。
  91→
  92→---
  93→
  94→## 6. 整改建议（按优先级）
  95→
  96→| 优先级 | 措施 | 归属层 |
  97→|--------|------|--------|
  98→| P0 | **冻结当前 Alpha 排序产出的权重，不作为 paper 候选**；必要时临时回退到 Iter #7 Sortino 权重（至少正收益、低 DD） | Meta-Agent 决策 |
  99→| P0 | **加策略健全性门槛**：`total_closed_trades ≥ N`（如每标的≥3）且 `win_rate` 非 NaN，否则判定退化策略，禁止进权重（无论 alpha 多高） | 选择器 / Gate |
 100→| P0 | **修 `rsi_trend_filter` 出场逻辑**：出场改为均值回归自然出场（如 RSI 回中性 50）或去掉出场的趋势门槛；趋势过滤只作用于入场 | 策略代码 |
 101→| P1 | **加 `alpha > 0`（或 > benchmark_margin）硬门槛**；无正 alpha 的组允许空仓 / 降现金 / 回退 SPY，不强行 top-K | 选择器 |
 102→| P1 | **策略选择改用样本外指标**：用 WF 4 轮验证期平均 alpha 排序，而非 5 年全量 in-sample alpha | 选择器 / WF |
 103→| P1 | **WF gate 增加 alpha 校验**：平均验证期 alpha>0、最近一轮 alpha>0、无单轮 alpha<-5%，DD≤15% 保持 | Gate |
 104→| P2 | **多指标复合评分**：如 `alpha * min(Sortino,2) / max(DD,5)`，避免单指标盲区 | 选择器 |
 105→| P2 | **专用 holdout**：前 4 年调参、第 5 年选策略，数据不重叠 | 方法论 |
 106→| P2 | 修正文档语义：`-1` 在当前回测是 exit 不是 short；若要做空需单独设计+审批 | 文档 |
 107→| P3 | 修幸存者偏差（历史成分股快照，需额外数据源） | 数据 |
 108→
 109→---
 110→
 111→## 7. 立即行动
 112→
 113→1. **不进 paper trading**：虽然 pytest 626 passed、WF DD 通过，但 PortfolioBacktest alpha=-25.26% 是 Gate 级失败。
 114→2. 下一轮迭代优先级：**先修选择器（健全性门槛 + OOS alpha + alpha>0）**，而不是继续堆 RSI 变体。
 115→3. `rsi_trend_filter` 暂标记为"退化策略"，修好出场逻辑前不参与权重。
 116→
 117→---
 118→
 119→*验证脚本：`tmp/audit_verify.py`（可复跑）。原始数据：`mytrader/config/strategy_weights.json`、`iterations/iteration_{8,9,10}/`。*
 120→
---
   1→# Iteration #8/9/10 综合审计报告
   2→
   3→> 主题：第 8 轮 `rsi_trend_filter` 方案为什么不 work？
   4→> 审计方：Claude（本机实测）、GPT、DeepSeek 三方综合
   5→> 日期：2026-07-07
   6→> 结论定性：**策略层结构性 Bug（近因，已实测证实）+ 选择器治理漏洞 + 方法论过拟合，三层叠加**
   7→
   8→---
   9→
  10→## 0. 一句话结论
  11→
  12→第 8 轮方案不 work，**不是因为"趋势过滤降低了 Sortino 所以选不进权重"**，而是因为 `rsi_trend_filter` 的入场条件（上升趋势）与出场条件（下降趋势）在趋势方向上互斥，导致多头市场里仓位**几乎永远无法平仓**——它退化成了"买一次、无限期持有"的伪 buy-and-hold；第 9 轮把排序从 Sortino 换成样本内 Alpha，不但没治病，反而把这个坏策略样本内的 regime 运气放大成了满仓押注，第 10 轮样本外 alpha 崩到 **-25.26%** 就是这条误诊链的终点。
  13→
  14→---
  15→
  16→## 1. 关键数据回顾
  17→
  18→| 指标 | Iter #7 (Sortino 排序) | Iter #10 (Alpha 排序) | 变化 |
  19→|------|----------------------|----------------------|------|
  20→| 年化收益 | 8.02% | **-4.88%** | ❌ 亏损 |
  21→| Sortino | 1.03 | **-0.66** | ❌ 负值 |
  22→| Alpha (vs SPY) | -11.34% | **-25.26%** | ❌ 更差 |
  23→| Max DD | 5.95% | 8.39% | ❌ 更大 |
  24→| Walk-Forward | 4/4 pass | 4/4 pass | ✅（但没校验 alpha） |
  25→
  26→---
  27→
  28→## 2. 实证铁证（本机实跑，非理论推断）
  29→
  30→用 `tmp/audit_verify.py` 在**真实数据**（AAPL/MSFT/NVDA/GOOGL/AMZN，2021-2026）上跑两个策略，映射 entries/exits 后过 `vbt.Portfolio.from_signals`：
  31→
  32→| 策略 | 平均入场信号 | **平均出场信号** | 每标的交易数 | win_rate 为 NaN(零平仓)标的 |
  33→|---|---|---|---|---|
  34→| `rsi_mean_revert` | 80 | 61.4 | 5.4 | **0 / 5** |
  35→| `rsi_trend_filter` | 19 | **0.0** | 1.0 | **5 / 5** |
  36→
  37→合成牛市里同样：`rsi_trend_filter` 11 入场 / **2 出场 / 1 笔交易 / win_rate 0% / 标的涨 16% 而策略亏 -18%**。
  38→
  39→**结论钉死**：真实近 5 年数据上，`rsi_trend_filter` 对 5 只股票产生 **0 个出场信号**，每只只开 1 仓、挂到回测末尾被 vbt 强平，win_rate 全为 NaN。这精确解释了 `strategy_weights.json` 里 `backtest_win_rate=0.0053`（NaN→0，与极少数熊市里偶尔触发出场的标的平均而来）。
  40→
  41→---
  42→
  43→## 3. 根因（代码级）
  44→
  45→策略源码 `mytrader/strategy/strategies/rsi_trend_filter.py`：
  46→
  47→```python
  48→signal[(rsi_values < oversold) & above_trend] = 1     # BUY：超卖 且 close > SMA200（上升趋势）
  49→signal[(rsi_values > overbought) & below_trend] = -1  # SELL：超买 且 close < SMA200（下降趋势）
  50→```
  51→
  52→回测引擎 `matrix_backtest.py`：`entries = sig==1`，`exits = sig==-1`，且 `from_signals` **未传任何 sl_stop/tp_stop** → 唯一平仓路径就是 `-1` 信号。
  53→
  54→| | 触发条件 | 趋势方向要求 |
  55→|---|---|---|
  56→| 建仓 BUY | RSI<超卖 | `close > SMA200`（上升趋势）|
  57→| 平仓 SELL | RSI>超买 | `close < SMA200`（下降趋势）|
  58→
  59→**建仓要上升趋势、平仓要下降趋势，两者互斥。** 一笔在上升趋势里开的多单，只有等价格先跌破 SMA200（趋势反转）**且同时** RSI>70 才能平——而价格跌破 200 日线时 RSI 几乎不可能超买。所以这个"趋势过滤的均值回归"实际上无法完成任何一次均值回归的买卖闭环，退化为滞后 buy-and-hold。
  60→
  61→---
  62→
  63→## 4. 三方审计对照（谁对、谁错、谁补了盲区）
  64→
  65→| 审计方 | 定位的根因 | 判定 |
  66→|--------|-----------|------|
  67→| **Claude（本报告）** | 策略层结构性 Bug：出场被入场条件锁死→几乎不平仓→伪 buy-and-hold | ✅ **被实测证实，是直接近因** |
  68→| **GPT** | 策略假设错（是过滤后的均值回归，非趋势收益捕获器）+ 选择器治理漏洞 | ⚠️ 方向对、注意到 win_rate=0.0053 与 "-1 是平多非做空"，但把机制定性为"择时跑输"，比真相软；**选择器治理漏洞是有价值的增量** |
  69→| **DeepSeek** | 方法论：样本内单指标排序必然过拟合；数据未分离；WF 只做 gate 不做 selector | ✅ 方法论正确且重要；**但明确否认"rsi_trend_filter 是坏策略"这句被实测证伪**，把二阶问题当成了主因 |
  70→
  71→### 三层因果关系（对整改最有用的框架）
  72→
  73→要分清两个不同的问题：
  74→
  75→- **策略为什么坏** → Claude 的结构性 Bug（出场条件锁死）。修它 = 改出场逻辑。
  76→- **坏东西为什么能一路进权重、还差点进 paper** → GPT + DeepSeek 的制度性缺陷。补它们 = 加 OOS-alpha 排序、alpha>0 门槛、**最小平仓交易数/win_rate 健全性门槛**。
  77→
  78→> 注意：一条"最小平仓交易数 ≥ N / win_rate 非 NaN"的健全性门槛，本可在第 8 轮当场就把 `rsi_trend_filter` 拦下——它同时来自 Claude（sanity gate）和 GPT（win_rate 观察），比 DeepSeek 主张的 holdout 更早、更便宜。
  79→
  80→---
  81→
  82→## 5. 选择器 / Gate 的制度性漏洞清单（GPT + DeepSeek + Claude 合并）
  83→
  84→1. **无健全性门槛**：策略即使 0 平仓交易、win_rate=NaN，仍能凭"逐日盯市 + 末尾强平"算出的 Sortino/alpha 进权重。
  85→2. **无 `alpha>0` 硬门槛**（`matrix_backtest.py::_run_group`）：某组所有策略 alpha 全负时，仍会选"没那么差"的负 alpha 策略。当前 11 条权重里仅 2 条正 alpha。
  86→3. **负 alpha 归一化退化为等权**（`_optimize_ensemble_weights`）：`max(alpha, 0.01)` 使两个负 alpha 策略被强行 50/50，掩盖坏策略，而不是空仓/降现金/回退 SPY。
  87→4. **样本内选择 = 过拟合**：`_run_group` 在同一段 5 年窗口上同时做参数搜索和 alpha 排序，非真正样本外。
  88→5. **WF 只做 pass/fail，不做 selector**：`run_walk_forward` 算了验证期 Sortino/DD，但没算验证期 alpha，也没把 OOS 指标回传到 top-K 选择。
  89→6. **WF gate 不校验 alpha**：Iter #10 WF 4/4 pass，但组合 alpha=-25.26% —— DD/Sortino 过关 ≠ 有正 alpha。
  90→7. **幸存者偏差**：用当前成分股回测，代码自己已 warning，alpha 被系统性高估。
  91→
  92→---
  93→
  94→## 6. 整改建议（按优先级）
  95→
  96→| 优先级 | 措施 | 归属层 |
  97→|--------|------|--------|
  98→| P0 | **冻结当前 Alpha 排序产出的权重，不作为 paper 候选**；必要时临时回退到 Iter #7 Sortino 权重（至少正收益、低 DD） | Meta-Agent 决策 |
  99→| P0 | **加策略健全性门槛**：`total_closed_trades ≥ N`（如每标的≥3）且 `win_rate` 非 NaN，否则判定退化策略，禁止进权重（无论 alpha 多高） | 选择器 / Gate |
 100→| P0 | **修 `rsi_trend_filter` 出场逻辑**：出场改为均值回归自然出场（如 RSI 回中性 50）或去掉出场的趋势门槛；趋势过滤只作用于入场 | 策略代码 |
 101→| P1 | **加 `alpha > 0`（或 > benchmark_margin）硬门槛**；无正 alpha 的组允许空仓 / 降现金 / 回退 SPY，不强行 top-K | 选择器 |
 102→| P1 | **策略选择改用样本外指标**：用 WF 4 轮验证期平均 alpha 排序，而非 5 年全量 in-sample alpha | 选择器 / WF |
 103→| P1 | **WF gate 增加 alpha 校验**：平均验证期 alpha>0、最近一轮 alpha>0、无单轮 alpha<-5%，DD≤15% 保持 | Gate |
 104→| P2 | **多指标复合评分**：如 `alpha * min(Sortino,2) / max(DD,5)`，避免单指标盲区 | 选择器 |
 105→| P2 | **专用 holdout**：前 4 年调参、第 5 年选策略，数据不重叠 | 方法论 |
 106→| P2 | 修正文档语义：`-1` 在当前回测是 exit 不是 short；若要做空需单独设计+审批 | 文档 |
 107→| P3 | 修幸存者偏差（历史成分股快照，需额外数据源） | 数据 |
 108→
 109→---
 110→
 111→## 7. 立即行动
 112→
 113→1. **不进 paper trading**：虽然 pytest 626 passed、WF DD 通过，但 PortfolioBacktest alpha=-25.26% 是 Gate 级失败。
 114→2. 下一轮迭代优先级：**先修选择器（健全性门槛 + OOS alpha + alpha>0）**，而不是继续堆 RSI 变体。
 115→3. `rsi_trend_filter` 暂标记为"退化策略"，修好出场逻辑前不参与权重。
 116→
 117→---
 118→
 119→*验证脚本：`tmp/audit_verify.py`（可复跑）。原始数据：`mytrader/config/strategy_weights.json`、`iterations/iteration_{8,9,10}/`。*
 120→
---
Now
---
 I
---
 have
---
 a
---
 clear
---
 understanding
---
 of
---
 the
---
 task
---
.
---
 Let
---
 me
---
 read
---
 the
---
 `
---
matrix
---
_back
---
test
---
.py
---
`
---
 file
---
 to
---
 understand
---
 the
---
 current
---
 structure
---
,
---
 especially
---
 `_
---
back
---
test
---
_one
---
`,
---
 `_
---
back
---
test
---
_batch
---
`,
---
 `_
---
run
---
_group
---
`,
---
 and
---
 the
---
 data
---
classes
---
.


---
Let
---
 me
---
 also
---
 check
---
 the
---
 related
---
 test
---
 files
---
 and
---
 the
---
 design
---
 doc
---
.
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py"}
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
  43→# 迭代 #9 新增：Sortino 最低质量门槛，用于 top-K 选择时的二级过滤
  44→# 排除 Sortino ≤ 0.5 的"垃圾"策略（即使 alpha 高也不选）
  45→# 设计动机：alpha 排序选出高绝对收益策略，但需 Sortino 门槛保证基本下行质量
  46→# fallback：若无候选通过此门槛，放宽过滤（仅保留 DD 硬约束）
  47→MIN_SORTINO_THRESHOLD: float = 0.5
  48→
  49→
  50→# ---------------------------------------------------------------------------
  51→# 数据结构
  52→# ---------------------------------------------------------------------------
  53→
  54→@dataclass
  55→class SingleBacktestResult:
  56→    """单只标的单策略回测结果。"""
  57→
  58→    symbol: str
  59→    strategy: str
  60→    params: dict
  61→    sharpe: float
  62→    total_return_pct: float
  63→    max_drawdown_pct: float
  64→    win_rate_pct: float
  65→    total_trades: int
  66→    daily_returns: pd.Series    # pf.returns() — 供组合 Sharpe / Sortino 计算
  67→    sortino: float = 0.0       # Constitution L1 首要 KPI（迭代 #1 新增）
  68→
  69→
  70→@dataclass
  71→class GroupBacktestResult:
  72→    """单组策略回测结果。"""
  73→
  74→    group_id: str
  75→    strategy: str
  76→    params: dict
  77→    portfolio_sharpe: float          # 等权组合 Sharpe（而非算术平均）
  78→    avg_total_return_pct: float
  79→    avg_max_drawdown_pct: float
  80→    avg_win_rate_pct: float
  81→    symbol_count: int
  82→    portfolio_sortino: float = 0.0          # 等权组合 Sortino（迭代 #1 新增）
  83→    portfolio_max_drawdown: float = 0.0     # 等权组合最大回撤（迭代 #2 新增，Constitution L1 KPI）
  84→    dd_constrained: bool = False            # 迭代 #3：该组是否用了 DD fallback（无合规候选）
  85→    backtest_alpha: float = 0.0              # 迭代 #9：alpha vs SPY（百分数），用于排序策略选择
  86→
  87→
  88→@dataclass
  89→class MatrixBacktestReport:
  90→    """整个矩阵回测的汇总报告。"""
  91→
  92→    generated_at: str
  93→    backtest_window: str
  94→    groups: dict[str, list[dict]]   # group_id → [策略权重配置]
  95→    group_results: list[GroupBacktestResult] = field(default_factory=list)
  96→    warnings: list[str] = field(default_factory=list)
  97→
  98→
  99→# ---------------------------------------------------------------------------
 100→# Walk-Forward 数据结构（迭代 #3 新增，Constitution L7 验证流水线）
 101→# ---------------------------------------------------------------------------
 102→
 103→@dataclass
 104→class WalkForwardRound:
 105→    """单轮 Walk-Forward 验证结果。
 106→
 107→    一轮 = 训练期（找最优参数）+ 验证期（用同参数回测，记录样本外指标）。
 108→
 109→    Attributes:
 110→        round_num:    轮次编号（1-indexed）
 111→        train_start:  训练期起始日期（含）
 112→        train_end:    训练期结束日期（含）
 113→        val_start:    验证期起始日期（含）
 114→        val_end:      验证期结束日期（含）
 115→        val_sortino:  验证期等权组合 Sortino Ratio（年化）
 116→        val_max_dd:   验证期等权组合最大回撤（正值百分数，0~100）
 117→        passed:       是否通过 = val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD (15%)
 118→    """
 119→
 120→    round_num: int
 121→    train_start: date
 122→    train_end: date
 123→    val_start: date
 124→    val_end: date
 125→    val_sortino: float
 126→    val_max_dd: float
 127→    passed: bool
 128→
 129→
 130→@dataclass
 131→class WalkForwardReport:
 132→    """Walk-Forward 4 轮验证汇总报告。
 133→
 134→    Constitution L7 要求 Backtest(>=5年) → Walk-Forward(4轮) → Paper → Live。
 135→    本报告是 Walk-Forward 阶段的产出。
 136→
 137→    Attributes:
 138→        rounds:         每轮结果列表（长度通常为 4）
 139→        pass_all_rounds: 是否所有轮都通过（all(r.passed for r in rounds)）
 140→        max_val_dd:     所有轮中最大的验证期 DD（用于风险监控）
 141→    """
 142→
 143→    rounds: list[WalkForwardRound] = field(default_factory=list)
 144→    pass_all_rounds: bool = False
 145→    max_val_dd: float = 0.0
 146→
 147→
 148→# ---------------------------------------------------------------------------
 149→# 核心函数
 150→# ---------------------------------------------------------------------------
 151→
 152→def _safe_float(value: Any, default: float = 0.0) -> float:
 153→    """NaN/None/非数值安全转 float（迭代 #2 新增）。
 154→
 155→    问题背景：vectorbt 在无交易场景下，`pf.stats()` 的 Win Rate / Sharpe 等
 156→    字段会返回 NaN。`float(NaN or 0.0)` 仍是 NaN（NaN 是 truthy），导致
 157→    JSON 序列化写出非法 JSON（NaN/Infinity 非 JSON 规范）。
 158→
 159→    处理顺序：
 160→        1. None → default
 161→        2. 数值类型但 NaN/Inf → default
 162→        3. 非数值（字符串等）尝试 float() 转换，失败 → default
 163→    """
 164→    if value is None:
 165→        return default
 166→    try:
 167→        f = float(value)
 168→    except (TypeError, ValueError):
 169→        return default
 170→    if not np.isfinite(f):   # 拦截 NaN / +Inf / -Inf
 171→        return default
 172→    return f
 173→
 174→
 175→def _safe_mean(values: Any, default: float = 0.0) -> float:
 176→    """空列表 / 全 NaN 安全的均值（迭代 #2 新增）。
 177→
 178→    问题背景：`np.mean([])` 会触发 RuntimeWarning 并返回 NaN；
 179→    `np.mean([NaN, NaN])` 直接返回 NaN。在 GroupBacktestResult 聚合时
 180→    若某组只有 1 个标的且其字段为 NaN，会导致下游 JSON 序列化失败。
 181→
 182→    行为：
 183→        - 空列表 / 全 NaN → default
 184→        - 部分 NaN → 自动忽略 NaN 后取均值（np.nanmean 语义）
 185→    """
 186→    arr = np.asarray(values, dtype=float)
 187→    if arr.size == 0:
 188→        return default
 189→    mask = np.isfinite(arr)
 190→    if not mask.any():
 191→        return default
 192→    return float(arr[mask].mean())
 193→
 194→
 195→def _compute_sharpe(returns: pd.Series, periods_per_year: int = 252) -> float:
 196→    """从日收益率序列计算年化 Sharpe Ratio。"""
 197→    returns = returns.dropna()
 198→    if len(returns) < 5:
 199→        return 0.0
 200→    mean = returns.mean()
 201→    std = returns.std()
 202→    if std <= 0 or np.isnan(std):
 203→        return 0.0
 204→    return float(mean / std * np.sqrt(periods_per_year))
 205→
 206→
 207→def _compute_sortino(
 208→    returns: pd.Series,
 209→    periods_per_year: int = 252,
 210→    target: float = 0.0,
 211→) -> float:
 212→    """从日收益率序列计算年化 Sortino Ratio（Constitution L1 首要 KPI）。
 213→
 214→    Sortino = (mean(returns) - target) / downside_deviation * sqrt(periods_per_year)
 215→    downside_deviation = sqrt( mean( min(0, returns - target)^2 ) )
 216→
 217→    与 Sharpe 的区别：仅对下行波动惩罚，上行波动不计入分母。
 218→    适合"收益>0 但偶尔大跌"的中长线策略评估。
 219→
 220→    退化处理（与 _compute_sharpe 一致）：
 221→        - 样本 < 5 → 0.0
 222→        - 下行波动 ≤ 0（无下行样本）→ 0.0（理论为 +inf，返回 0 保持保守 + 可算术聚合）
 223→
 224→    Args:
 225→        returns:          日收益率序列（如 pf.returns()）
 226→        periods_per_year: 年化因子（日线 = 252）
 227→        target:           MAR/目标收益率，默认 0（与 _compute_sharpe 无风险利率假设一致）
 228→
 229→    Returns:
 230→        年化 Sortino Ratio
 231→    """
 232→    returns = returns.dropna()
 233→    if len(returns) < 5:
 234→        return 0.0
 235→    excess = returns - target
 236→    downside = excess.where(excess < 0, 0.0)        # 仅保留负偏离，正偏离置 0
 237→    dd = np.sqrt((downside ** 2).mean())
 238→    if dd <= 0 or np.isnan(dd):
 239→        return 0.0
 240→    return float(returns.mean() / dd * np.sqrt(periods_per_year))
 241→
 242→
 243→def _combine_daily_returns(results: list[SingleBacktestResult]) -> pd.Series:
 244→    """等权合并组内日收益率序列，返回组合日收益率（迭代 #9 新增）。
 245→
 246→    与 _portfolio_sharpe_from_results / _portfolio_sortino_from_results 同语义：
 247→    将所有标的日收益率等权合并为组合序列。提取为独立函数以便 alpha 计算
 248→    和 per-strategy best params 选择复用，避免重复 pd.concat。
 249→
 250→    Args:
 251→        results: 单策略多标的的回测结果列表
 252→
 253→    Returns:
 254→        组合日收益率 pd.Series；无有效数据时返回空 Series
 255→    """
 256→    valid = [r.daily_returns for r in results if not r.daily_returns.empty]
 257→    if not valid:
 258→        return pd.Series(dtype=float)
 259→    return pd.concat(valid, axis=1).mean(axis=1)
 260→
 261→
 262→def _compute_alpha(
 263→    strategy_daily_returns: pd.Series,
 264→    spy_daily_returns: pd.Series | None,
 265→    periods_per_year: int = 252,
 266→) -> float:
 267→    """计算 alpha = 策略年化收益 - SPY 年化收益（迭代 #9 新增）。
 268→
 269→    Alpha 衡量策略相对 SPY buy-and-hold 的超额收益。正值表示跑赢 SPY，
 270→    负值表示跑输 SPY。用于 top-K 策略选择和 per-strategy best params 选择，
 271→    替代之前基于 Sortino/Sharpe 的选择逻辑（参考 iteration #9 spec）。
 272→
 273→    年化公式：(1 + mean_daily) ** periods_per_year - 1
 274→    使用算术平均日收益的几何年化，与 PortfolioBacktester 同口径。
 275→
 276→    降级处理：SPY 数据不可用（None 或空）→ 返回 0.0（不抛异常）。
 277→    这样在 SPY 数据缺失时，alpha 排序退化为"原顺序"，不会阻塞回测。
 278→
 279→    Args:
 280→        strategy_daily_returns: 策略组合日收益率序列
 281→        spy_daily_returns:      SPY 日收益率序列；None 表示数据不可用
 282→        periods_per_year:       年化因子（日线 = 252）
 283→
 284→    Returns:
 285→        Alpha 百分数（如 5.23 表示策略年化收益跑赢 SPY 5.23 个百分点）；
 286→        SPY 不可用时返回 0.0
 287→    """
 288→    if spy_daily_returns is None or spy_daily_returns.empty:
 289→        return 0.0
 290→    if strategy_daily_returns is None or strategy_daily_returns.empty:
 291→        return 0.0
 292→
 293→    # 对齐时间索引（inner join 取交集）
 294→    aligned = pd.concat(
 295→        [strategy_daily_returns.rename("strat"), spy_daily_returns.rename("spy")],
 296→        axis=1,
 297→        join="inner",
 298→    ).dropna()
 299→    if aligned.empty or len(aligned) < 2:
 300→        return 0.0
 301→
 302→    strat_returns = aligned["strat"]
 303→    spy_returns = aligned["spy"]
 304→
 305→    # 年化收益 = (1 + mean_daily)^252 - 1
 306→    strat_mean = strat_returns.mean()
 307→    spy_mean = spy_returns.mean()
 308→    if not np.isfinite(strat_mean) or not np.isfinite(spy_mean):
 309→        return 0.0
 310→
 311→    strat_annual = (1.0 + strat_mean) ** periods_per_year - 1.0
 312→    spy_annual = (1.0 + spy_mean) ** periods_per_year - 1.0
 313→
 314→    alpha = (strat_annual - spy_annual) * 100.0  # 转为百分数
 315→    if not np.isfinite(alpha):
 316→        return 0.0
 317→    return float(alpha)
 318→
 319→
 320→def _backtest_one(
 321→    df: pd.DataFrame,
 322→    strategy_name: str,
 323→    params: dict,
 324→    init_cash: float = 100_000.0,
 325→    fees: float = 0.001,
 326→    slippage: float = 0.001,
 327→) -> SingleBacktestResult | None:
 328→    """对单只标的执行单次回测。
 329→
 330→    使用 open= 参数确保信号在下一根 bar 的开盘价执行（与实盘一致）。
 331→
 332→    Returns:
 333→        SingleBacktestResult 或 None（数据不足/策略异常时）
 334→    """
 335→    strategy_fn = STRATEGY_REGISTRY.get(strategy_name)
 336→    if strategy_fn is None:
 337→        return None
 338→
 339→    if df.empty or len(df) < 30:
 340→        return None
 341→
 342→    try:
 343→        close = df["close"]
 344→        open_ = df["open"] if "open" in df.columns else None
 345→
 346→        # 调用策略（兼容需要 df 的策略）
 347→        try:
 348→            sig = strategy_fn(close, df=df, **params)
 349→        except TypeError:
 350→            sig = strategy_fn(close, **params)
 351→
 352→        entries = sig == 1
 353→        exits   = sig == -1
 354→
 355→        pf_kwargs: dict[str, Any] = dict(
 356→            entries=entries,
 357→            exits=exits,
 358→            init_cash=init_cash,
 359→            fees=fees,
 360→            slippage=slippage,
 361→            size=0.95,
 362→            size_type="Percent",
 363→            freq="D",
 364→        )
 365→
 366→        # ⚠️ 必须传 open= 参数：信号在下一根 bar 开盘价执行，与实盘一致
 367→        if open_ is not None:
 368→            pf = vbt.Portfolio.from_signals(close=close, open=open_, **pf_kwargs)
 369→        else:
 370→            pf = vbt.Portfolio.from_signals(close, **pf_kwargs)
 371→
 372→        stats = pf.stats()
 373→
 374→        daily_returns = pf.returns()
 375→
 376→        return SingleBacktestResult(
 377→            symbol=str(df.index.name or ""),
 378→            strategy=strategy_name,
 379→            params=params,
 380→            sharpe=_safe_float(stats.get("Sharpe Ratio")),
 381→            total_return_pct=_safe_float(stats.get("Total Return [%]")),
 382→            max_drawdown_pct=_safe_float(stats.get("Max Drawdown [%]")),
 383→            win_rate_pct=_safe_float(stats.get("Win Rate [%]")),
 384→            total_trades=int(_safe_float(stats.get("Total Trades"), default=0.0)),
 385→            daily_returns=daily_returns,
 386→            sortino=_compute_sortino(daily_returns),
 387→        )
 388→    except Exception as e:
 389→        logger.debug(f"[backtest_one] {strategy_name}({params}) failed: {e}")
 390→        return None
 391→
 392→
 393→def _backtest_batch(
 394→    data: dict[str, pd.DataFrame],
 395→    strategy_name: str,
 396→    params: dict,
 397→    init_cash: float = 100_000.0,
 398→    fees: float = 0.001,
 399→    slippage: float = 0.001,
 400→) -> list[SingleBacktestResult]:
 401→    """对组内所有标的批量执行回测（迭代 #10 新增）。
 402→
 403→    核心优化：用一次 vbt.Portfolio.from_signals 处理组内所有标的，
 404→    替代 `_backtest_one` 的 for-symbol 循环。调用次数从 O(N 标的)
 405→    降为 O(1)，预计 10-20x 提速（spec §1）。
 406→
 407→    实现要点：
 408→        1. 逐标的调用策略函数（保持与 `_backtest_one` 一致的调用语义：
 409→           先尝试 `strategy_fn(close, df=df, **params)`，TypeError 时
 410→           回退到 `strategy_fn(close, **params)`）。策略函数本身不改。
 411→        2. 构建列式矩阵（每列一个标的），用一次 vbt 调用回测所有标的。
 412→           vbt 1.0+ 的列分组语义保证每列独立结算 P&L。
 413→        3. 通过 `pf[sym]` 提取每列的 stats/daily_returns，输出格式与
 414→           `_backtest_one` 完全一致，下游聚合代码无需修改。
 415→
 416→    对齐策略：
 417→        - 用 `pd.DataFrame(dict)` 构造时自动 outer-join 时间索引，
 418→          缺失值填 NaN。
 419→        - vbt 对 NaN close 的处理：内部 fillna 为 0 收益率，等价于
 420→          "该标的此日期不交易"。当标的在样本外日期缺失时（如退市、
 421→          新上市），其 stats 仍按其有效日期区间计算。
 422→        - 在美股实际场景中所有标的共享交易日历，日期对齐天然成立，
 423→          不会有大量 NaN。
 424→
 425→    Args:
 426→        data:          {symbol: OHLCV DataFrame} 字典
 427→        strategy_name: 策略名
 428→        params:        策略参数
 429→        init_cash:     初始资金（vbt 给每列分配独立的 init_cash）
 430→        fees:          手续费率
 431→        slippage:      滑点率
 432→
 433→    Returns:
 434→        SingleBacktestResult 列表（与 `_backtest_one` 输出格式一致）。
 435→        数据不足 / 策略异常的标的会被跳过（不返回 None，不抛异常）。
 436→        空数据时返回空列表。
 437→    """
 438→    strategy_fn = STRATEGY_REGISTRY.get(strategy_name)
 439→    if strategy_fn is None:
 440→        return []
 441→
 442→    # 1. 逐标的调用策略函数，构建 signal / close / open 列
 443→    signal_columns: dict[str, pd.Series] = {}
 444→    close_columns: dict[str, pd.Series] = {}
 445→    open_columns: dict[str, pd.Series] = {}
 446→
 447→    for sym, df in data.items():
 448→        if df is None or df.empty or len(df) < 30:
 449→            continue
 450→        close = df["close"]
 451→        if "open" in df.columns:
 452→            open_ = df["open"]
 453→            open_columns[sym] = open_
 454→        else:
 455→            open_ = None
 456→
 457→        # 调用策略（与 _backtest_one 一致的 try/except 语义）
 458→        try:
 459→            sig = strategy_fn(close, df=df, **params)
 460→        except TypeError:
 461→            sig = strategy_fn(close, **params)
 462→        except Exception as e:
 463→            logger.debug(
 464→                f"[backtest_batch] {strategy_name}({params}) {sym} failed: {e}"
 465→            )
 466→            continue
 467→
 468→        signal_columns[sym] = sig
 469→        close_columns[sym] = close
 470→
 471→    if not signal_columns:
 472→        return []
 473→
 474→    # 2. 构建矩阵（自动 outer-join 索引，缺失值填 NaN）
 475→    close_matrix = pd.DataFrame(close_columns)
 476→    signal_matrix = pd.DataFrame(signal_columns)
 477→    has_open = bool(open_columns)
 478→    open_matrix = pd.DataFrame(open_columns) if has_open else None
 479→
 480→    # 3. 一次 vbt 调用处理所有标的
 481→    entries = signal_matrix == 1
 482→    exits = signal_matrix == -1
 483→
 484→    pf_kwargs: dict[str, Any] = dict(
 485→        entries=entries,
 486→        exits=exits,
 487→        init_cash=init_cash,
 488→        fees=fees,
 489→        slippage=slippage,
 490→        size=0.95,
 491→        size_type="Percent",
 492→        freq="D",
 493→    )
 494→
 495→    try:
 496→        if has_open:
 497→            pf = vbt.Portfolio.from_signals(
 498→                close=close_matrix, open=open_matrix, **pf_kwargs
 499→            )
 500→        else:
 501→            pf = vbt.Portfolio.from_signals(close_matrix, **pf_kwargs)
 502→    except Exception as e:
 503→        logger.warning(
 504→            f"[backtest_batch] {strategy_name}({params}) vbt call failed: {e} "
 505→            f"— falling back to per-symbol _backtest_one"
 506→        )
 507→        # 回滚方案：批量失败时退化为逐标的回测，保证回测不中断
 508→        results: list[SingleBacktestResult] = []
 509→        for sym, df in data.items():
 510→            if df is None or df.empty or len(df) < 30:
 511→                continue
 512→            df = df.copy()
 513→            df.index.name = sym
 514→            r = _backtest_one(
 515→                df, strategy_name, params, init_cash, fees, slippage
 516→            )
 517→            if r is not None:
 518→                results.append(r)
 519→        return results
 520→
 521→    # 4. 提取 per-symbol 结果（与 _backtest_one 输出格式一致）
 522→    results = []
 523→    for sym in signal_matrix.columns:
 524→        try:
 525→            pf_sym = pf[sym]
 526→            stats = pf_sym.stats()
 527→            daily_returns = pf_sym.returns()
 528→            results.append(SingleBacktestResult(
 529→                symbol=sym,
 530→                strategy=strategy_name,
 531→                params=params,
 532→                sharpe=_safe_float(stats.get("Sharpe Ratio")),
 533→                total_return_pct=_safe_float(stats.get("Total Return [%]")),
 534→                max_drawdown_pct=_safe_float(stats.get("Max Drawdown [%]")),
 535→                win_rate_pct=_safe_float(stats.get("Win Rate [%]")),
 536→                total_trades=int(_safe_float(stats.get("Total Trades"), default=0.0)),
 537→                daily_returns=daily_returns,
 538→                sortino=_compute_sortino(daily_returns),
 539→            ))
 540→        except Exception as e:
 541→            logger.debug(
 542→                f"[backtest_batch] {strategy_name}({params}) {sym} "
 543→                f"stats extraction failed: {e}"
 544→            )
 545→            continue
 546→
 547→    return results
 548→
 549→
 550→def _portfolio_sharpe_from_results(results: list[SingleBacktestResult]) -> float:
 551→    """等权合并组内日收益率序列，计算组合 Sharpe。
 552→
 553→    ⚠️ 不能取各标的 Sharpe 算术平均（Sharpe 是比率，不能直接平均）。
 554→    正确做法：将所有标的日收益率等权合并为组合序列，再计算 Sharpe。
 555→    """
 556→    valid = [r.daily_returns for r in results if not r.daily_returns.empty]
 557→    if not valid:
 558→        return 0.0
 559→
 560→    # 对齐时间索引，等权平均
 561→    combined = pd.concat(valid, axis=1).mean(axis=1)
 562→    return _compute_sharpe(combined)
 563→
 564→
 565→def _portfolio_sortino_from_results(results: list[SingleBacktestResult]) -> float:
 566→    """等权合并组内日收益率序列，计算组合 Sortino（与 _portfolio_sharpe_from_results 同语义）。
 567→
 568→    不能取各标的 Sortino 算术平均（与 Sharpe 同理：比率不可直接平均）。
 569→    """
 570→    valid = [r.daily_returns for r in results if not r.daily_returns.empty]
 571→    if not valid:
 572→        return 0.0
 573→    combined = pd.concat(valid, axis=1).mean(axis=1)
 574→    return _compute_sortino(combined)
 575→
 576→
 577→def _portfolio_max_drawdown_from_results(
 578→    results: list[SingleBacktestResult],
 579→) -> float:
 580→    """等权合并组内日收益率序列，计算组合最大回撤（迭代 #2 新增，Constitution L1 KPI）。
 581→
 582→    与 `_portfolio_sharpe_from_results` 同语义：不能取各标的 DD 算术平均，
 583→    因为 DD 是路径依赖的比率。正确做法是先把��内日收益率等权合并为组合序列，
 584→    再 cumprod → cummax → drawdown → max。
 585→
 586→    返回值约定：百分比形式（与 `SingleBacktestResult.max_drawdown_pct` 一致，
 587→    vectorbt stats 中 `Max Drawdown [%]` 同样是百分数，例如 -15.2 表示 15.2% 回撤）。
 588→    本函数返回正值（0.0 ~ 100.0）便于聚合与 JSON 输出。
 589→
 590→    退化处理：
 591→        - 无有效日收益率 → 0.0
 592→        - 全 0 收益率（cumprod 恒为 1.0）→ 0.0
 593→    """
 594→    valid = [r.daily_returns for r in results if not r.daily_returns.empty]
 595→    if not valid:
 596→        return 0.0
 597→    combined = pd.concat(valid, axis=1).mean(axis=1).dropna()
 598→    if len(combined) < 2:
 599→        return 0.0
 600→    # 组合累计净值：初始 1.0，每日乘 (1 + r)
 601→    cumvalue = (1.0 + combined).cumprod()
 602→    peak = cumvalue.cummax()
 603→    drawdown = (cumvalue - peak) / peak   # 负值，0 表示无回撤
 604→    dd_max_pct = float(drawdown.min())    # 最负值，例如 -0.152
 605→    if not np.isfinite(dd_max_pct):
 606→        return 0.0
 607→    # 转为正百分数（与 vectorbt Max Drawdown [%] 的口径一致但取正号）
 608→    return abs(dd_max_pct) * 100.0
 609→
 610→
 611→def _optimize_ensemble_weights(
 612→    group_results: list[tuple[str, dict, list[SingleBacktestResult]]],
 613→    spy_returns: pd.Series | None = None,
 614→    conflict_threshold: float = 0.3,
 615→) -> list[tuple[str, dict, float]]:
 616→    """在"单点离散值加权投票"语义下优化 ensemble 权重。
 617→
 618→    实盘每根 bar 各策略产出离散值（1/-1/0），加权投票决定方向。
 619→    回测的权重优化必须使用相同语义，而非对整段时间序列做加权。
 620→
 621→    迭代 #9：权重计算从 Sharpe 改为 Alpha（vs SPY）。
 622→    动机：与 _run_group 的 top-K 排序口径一致，使 ensemble 权重直接
 623→    反映"跑赢 SPY 的程度"。SPY 不可用时 alpha=0，退化为等权。
 624→
 625→    Args:
 626→        group_results: [(strategy, params, [SingleBacktestResult]), ...]
 627→        spy_returns:   SPY 日收益率序列（用于 alpha 计算）；None 时退化为等权
 628→        conflict_threshold: 加权投票分数绝对值低于此时视为 HOLD
 629→
 630→    Returns:
 631→        [(strategy, params, weight), ...] 归一化权重列表
 632→    """
 633→    if len(group_results) == 1:
 634→        strategy, params, _ = group_results[0]
 635→        return [(strategy, params, 1.0)]
 636→
 637→    # 迭代 #9：用各策略的组合 alpha 归一化为权重（替代 Sharpe）
 638→    # alpha 可能 < 0（跑输 SPY），用 max(alpha, 0.01) 避免负权重
 639→    alphas = []
 640→    for strategy, params, results in group_results:
 641→        combined = _combine_daily_returns(results)
 642→        alpha = _compute_alpha(combined, spy_returns)
 643→        alphas.append(max(alpha, 0.01))  # 避免负/零权重
 644→
 645→    total = sum(alphas)
 646→    weights = [a / total for a in alphas]
 647→
 648→    return [
 649→        (strategy, params, weight)
 650→        for (strategy, params, _), weight in zip(group_results, weights)
 651→    ]
 652→
 653→
 654→# ---------------------------------------------------------------------------
 655→# Walk-Forward 验证（迭代 #3 新增，Constitution L7 验证流水线）
 656→# ---------------------------------------------------------------------------
 657→
 658→def _add_months(d: date, months: int) -> date:
 659→    """对 date 加/减 months 个月，自动 clamp 到月末。
 660→
 661→    使用 pandas DateOffset 以避免引入 dateutil 依赖（pandas 已是核心依赖）。
 662→    """
 663→    return (pd.Timestamp(d) + pd.DateOffset(months=months)).date()
 664→
 665→
 666→def _backtest_with_params_on_period(
 667→    mb: "MatrixBacktest",
 668→    symbols: list[str],
 669→    weights: list[dict[str, Any]],
 670→    start: date,
 671→    end: date,
 672→) -> list[pd.Series]:
 673→    """用给定权重配置在 [start, end] 期间回测，返回每条 (策略×标的) 的日收益率序列。
 674→
 675→    用于 Walk-Forward 验证期：用训练期产出的 best params 在验证期回测，
 676→    不再做参数搜索。返回原始日收益率列表，由调用方聚合为整体 portfolio。
 677→
 678→    迭代 #10 变更：用 `_backtest_batch` 替代 for-symbol 循环，
 679→    每个策略×参数组合一次 vbt 调用，加速 Walk-Forward 验证期回测。
 680→
 681→    Args:
 682→        mb:       MatrixBacktest 实例（复用其 store/init_cash/fees/slippage）
 683→        symbols:  该组的标的列表
 684→        weights:  训练期产出的权重配置（list of dict，含 strategy/params/weight）
 685→        start:    验证期起始日期
 686→        end:      验证期结束日期
 687→
 688→    Returns:
 689→        list[pd.Series] — 每条 (strategy×symbol) 的日收益率；空列表表示无有效数据
 690→    """
 691→    if not weights or not symbols:
 692→        return []
 693→
 694→    data = mb._store.get_bars_multi(symbols, start, end)
 695→    if not data:
 696→        return []
 697→
 698→    all_returns: list[pd.Series] = []
 699→    for w in weights:
 700→        strategy = w.get("strategy", "")
 701→        params = w.get("params", {})
 702→        if not strategy or strategy not in STRATEGY_REGISTRY:
 703→            continue
 704→        # 迭代 #10：一次 batch 调用处理组内所有标的
 705→        results = _backtest_batch(
 706→            data, strategy, params,
 707→            mb._init_cash, mb._fees, mb._slippage,
 708→        )
 709→        for r in results:
 710→            if not r.daily_returns.empty:
 711→                all_returns.append(r.daily_returns)
 712→    return all_returns
 713→
 714→
 715→def run_walk_forward(
 716→    mb: "MatrixBacktest",
 717→    strategies: list[str],
 718→    param_grids: dict[str, dict[str, list]],
 719→    rounds: int = 4,
 720→    train_months: int = 18,
 721→    val_months: int = 6,
 722→) -> WalkForwardReport:
 723→    """执行 N 轮 Walk-Forward 验证（Constitution L7 验证流水线硬要求）。
 724→
 725→    每轮流程：
 726→        1. 训练期 [train_start, train_end]：跑矩阵回测找最优参数
 727→        2. 验证期 [val_start, val_end]：用同参数回测，记录 portfolio Sortino 和 max DD
 728→        3. passed = val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD (15%)
 729→
 730→    时间窗口（动态计算，today=today）：
 731→        - 最后一轮 val_end = today - val_months（留 1 个 val 期给 paper trading）
 732→        - 每轮向前推 val_months
 733→        - train_end = val_start，train_start = train_end - train_months
 734→
 735→    默认参数 (rounds=4, train_months=18, val_months=6) 对应用户提供的固定窗口：
 736→        today=2026-07-01 →
 737→        Round 1: train 2021-07-02~2023-01-02, val 2023-01-02~2023-07-02
 738→        Round 2: train 2022-01-02~2023-07-02, val 2023-07-02~2024-01-02
 739→        Round 3: train 2022-07-02~2024-01-02, val 2024-01-02~2024-07-02
 740→        Round 4: train 2023-01-02~2024-07-02, val 2024-07-02~2025-01-02
 741→
 742→    Args:
 743→        mb:            MatrixBacktest 实例（复用其 store/universe/init_cash 等）
 744→        strategies:    策略名称列表
 745→        param_grids:   参数网格（与 mb.run() 接收的格式一致）
 746→        rounds:        轮次数（默认 4，Constitution L7 要求）
 747→        train_months:  训练期月数（默认 18）
 748→        val_months:    验证期月数（默认 6）
 749→
 750→    Returns:
 751→        WalkForwardReport — 包含每轮结果、pass_all_rounds、max_val_dd
 752→
 753→    Note:
 754→        - WF 是验证步骤，不修改 strategy_weights.json
 755→        - 失败轮次会记录 WARNING 但不抛异常
 756→        - 全部 4 轮通过是进入 paper trading 的前置条件
 757→    """
 758→    today = date.today()
 759→    groups = mb._universe.get_groups()
 760→    if not groups:
 761→        logger.warning("[WalkForward] no groups available — skipping")
 762→        return WalkForwardReport()
 763→
 764→    wf_rounds: list[WalkForwardRound] = []
 765→
 766→    for i in range(rounds):
 767→        round_num = i + 1
 768→        # 计算本轮时间窗口
 769→        # 最后一轮 (i=rounds-1) 的 val_end = today - val_months
 770→        # 前面轮次依次向前推 val_months
 771→        val_end = _add_months(today, -val_months - (rounds - round_num) * val_months)
 772→        val_start = _add_months(val_end, -val_months)
 773→        train_end = val_start
 774→        train_start = _add_months(train_end, -train_months)
 775→
 776→        logger.info(
 777→            f"[WalkForward] Round {round_num}/{rounds}: "
 778→            f"train={train_start}~{train_end}, val={val_start}~{val_end}"
 779→        )
 780→
 781→        # ── 训练期：跑矩阵回测找最优参数（复用 mb._run_group）──
 782→        train_report = MatrixBacktestReport(
 783→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
 784→            backtest_window=f"{train_start.isoformat()} ~ {train_end.isoformat()}",
 785→            groups={},
 786→        )
 787→
 788→        for group_id, symbols in groups.items():
 789→            weights = mb._run_group(
 790→                group_id=group_id,
 791→                symbols=symbols,
 792→                start=train_start,
 793→                end=train_end,
 794→                strategies=strategies,
 795→                param_grids=param_grids,
 796→                report=train_report,
 797→            )
 798→            train_report.groups[group_id] = weights
 799→
 800→        # ── 验证期：用训练期 best params 回测，聚合为整体 portfolio ──
 801→        all_returns: list[pd.Series] = []
 802→        for group_id, symbols in groups.items():
 803→            weights = train_report.groups.get(group_id, [])
 804→            if not weights:
 805→                continue
 806→            group_returns = _backtest_with_params_on_period(
 807→                mb, symbols, weights, val_start, val_end,
 808→            )
 809→            all_returns.extend(group_returns)
 810→
 811→        # 计算整体 portfolio 指标（等权合并所有组的日收益率）
 812→        if not all_returns:
 813→            val_sortino = 0.0
 814→            val_max_dd = 0.0
 815→            logger.warning(
 816→                f"[WalkForward] Round {round_num}: no valid val returns — "
 817→                f"sortino=0, dd=0, passed=True (vacuous)"
 818→            )
 819→        else:
 820→            combined = pd.concat(all_returns, axis=1).mean(axis=1).dropna()
 821→            if len(combined) < 5:
 822→                val_sortino = 0.0
 823→                val_max_dd = 0.0
 824→            else:
 825→                val_sortino = _compute_sortino(combined)
 826→                wrapper = [SingleBacktestResult(
 827→                    symbol="portfolio", strategy="", params={},
 828→                    sharpe=0.0, total_return_pct=0.0, max_drawdown_pct=0.0,
 829→                    win_rate_pct=0.0, total_trades=0, daily_returns=combined,
 830→                )]
 831→                val_max_dd = _portfolio_max_drawdown_from_results(wrapper)
 832→
 833→        passed = val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD
 834→        wf_rounds.append(WalkForwardRound(
 835→            round_num=round_num,
 836→            train_start=train_start,
 837→            train_end=train_end,
 838→            val_start=val_start,
 839→            val_end=val_end,
 840→            val_sortino=val_sortino,
 841→            val_max_dd=val_max_dd,
 842→            passed=passed,
 843→        ))
 844→        logger.info(
 845→            f"[WalkForward] Round {round_num} result: "
 846→            f"sortino={val_sortino:.4f}, dd={val_max_dd:.4f}%, "
 847→            f"passed={passed} (threshold={WALK_FORWARD_VAL_DD_THRESHOLD}%)"
 848→        )
 849→
 850→    report = WalkForwardReport(
 851→        rounds=wf_rounds,
 852→        pass_all_rounds=all(r.passed for r in wf_rounds) if wf_rounds else False,
 853→        max_val_dd=max((r.val_max_dd for r in wf_rounds), default=0.0),
 854→    )
 855→    logger.info(
 856→        f"[WalkForward] done: {len(wf_rounds)} rounds, "
 857→        f"pass_all_rounds={report.pass_all_rounds}, "
 858→        f"max_val_dd={report.max_val_dd:.4f}%"
 859→    )
 860→    return report
 861→
 862→
 863→# ---------------------------------------------------------------------------
 864→# MatrixBacktest 主类
 865→# ---------------------------------------------------------------------------
 866→
 867→class MatrixBacktest:
 868→    """矩阵回测：N 策略 × G 标的组 × 参数网格 → strategy_weights.json。
 869→
 870→    Args:
 871→        store:       MarketDataStore（本地时序库）
 872→        universe:    UniverseManager（提供分组映射）
 873→        years:       回测窗口（默认 5 年）
 874→        init_cash:   初始资金
 875→        fees:        手续费率
 876→        slippage:    滑点率
 877→        top_k:       每组保留 Top-K 策略（默认 2）
 878→    """
 879→
 880→    def __init__(
 881→        self,
 882→        store: MarketDataStore,
 883→        universe: UniverseManager,
 884→        years: int = 5,
 885→        init_cash: float = 100_000.0,
 886→        fees: float = 0.001,
 887→        slippage: float = 0.001,
 888→        top_k: int = 2,
 889→    ) -> None:
 890→        self._store = store
 891→        self._universe = universe
 892→        self._years = years
 893→        self._init_cash = init_cash
 894→        self._fees = fees
 895→        self._slippage = slippage
 896→        self._top_k = top_k
 897→
 898→    def run(
 899→        self,
 900→        strategies: list[str],
 901→        param_grids: dict[str, dict[str, list]],
 902→        output_file: str | Path | None = None,
 903→    ) -> MatrixBacktestReport:
 904→        """执行完整矩阵回测。
 905→
 906→        Args:
 907→            strategies:  策略名称列表，如 ["dual_ma", "rsi"]
 908→            param_grids: 各策略参数网格，如 {"dual_ma": {"fast":[5,10], "slow":[20,30]}}
 909→            output_file: strategy_weights.json 输出路径（None 则不写文件）
 910→
 911→        Returns:
 912→            MatrixBacktestReport
 913→        """
 914→        today = date.today()
 915→        start = today - timedelta(days=self._years * 365)
 916→        window_str = f"{start.isoformat()} ~ {today.isoformat()}"
 917→
 918→        logger.info(
 919→            f"[MatrixBacktest] start={start}, end={today}, "
 920→            f"strategies={strategies}, years={self._years}"
 921→        )
 922→
 923→        # 获取分组（⚠️ 使用历史时点分组，而非当前静态分组）
 924→        # Phase 5 初期简化：用当前分组，但接口已预留历史分组能力
 925→        groups = self._universe.get_groups()
 926→        if not groups:
 927→            logger.warning("[MatrixBacktest] no groups available, abort")
 928→            return MatrixBacktestReport(
 929→                generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
 930→                backtest_window=window_str,
 931→                groups={},
 932→            )
 933→
 934→        report = MatrixBacktestReport(
 935→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
 936→            backtest_window=window_str,
 937→            groups={},
 938→        )
 939→
 940→        for group_id, symbols in groups.items():
 941→            logger.info(
 942→                f"[MatrixBacktest] group={group_id}, symbols={len(symbols)}, "
 943→                f"strategies={strategies}"
 944→            )
 945→
 946→            group_weights = self._run_group(
 947→                group_id=group_id,
 948→                symbols=symbols,
 949→                start=start,
 950→                end=today,
 951→                strategies=strategies,
 952→                param_grids=param_grids,
 953→                report=report,
 954→            )
 955→            report.groups[group_id] = group_weights
 956→
 957→        if output_file is not None:
 958→            self._write_weights(report, output_file)
 959→
 960→        logger.info(
 961→            f"[MatrixBacktest] done: {len(report.groups)} groups, "
 962→            f"warnings={len(report.warnings)}"
 963→        )
 964→        return report
 965→
 966→    def _get_spy_returns(self, start: date, end: date) -> pd.Series | None:
 967→        """获取 SPY 同期日收益率序列，用于计算 alpha（迭代 #9 新增）。
 968→
 969→        从 MarketDataStore 拉取 SPY 日线数据，计算日收益率。
 970→        SPY 不在标的池中，但作为 benchmark 用于 alpha 计算。
 971→
 972→        降级处理：SPY 数据不可用时返回 None（_compute_alpha 会返回 0.0），
 973→        不抛异常，保证回测不因 benchmark 缺失而阻塞。
 974→
 975→        Args:
 976→            start: 回测起始日期
 977→            end:   回测结束日期
 978→
 979→        Returns:
 980→            SPY 日收益率 pd.Series；数据不可用时返回 None
 981→        """
 982→        try:
 983→            spy_bars = self._store.get_bars_multi(["SPY"], start, end)
 984→            spy_df = spy_bars.get("SPY") if spy_bars else None
 985→            if spy_df is None or spy_df.empty:
 986→                logger.warning(
 987→                    "[MatrixBacktest] SPY data unavailable, alpha will degrade to 0.0"
 988→                )
 989→                return None
 990→            spy_close = spy_df["close"].astype(float)
 991→            if len(spy_close) < 2:
 992→                logger.warning(
 993→                    "[MatrixBacktest] SPY data too short, alpha will degrade to 0.0"
 994→                )
 995→                return None
 996→            return spy_close.pct_change().dropna()
 997→        except Exception as e:
 998→            logger.warning(
 999→                f"[MatrixBacktest] SPY benchmark fetch failed: {e} — "
1000→                f"alpha will degrade to 0.0"
1001→            )
1002→            return None
1003→
1004→    def _run_group(
1005→        self,
1006→        group_id: str,
1007→        symbols: list[str],
1008→        start: date,
1009→        end: date,
1010→        strategies: list[str],
1011→        param_grids: dict[str, dict[str, list]],
1012→        report: MatrixBacktestReport,
1013→    ) -> list[dict[str, Any]]:
1014→        """对单个分组执行策略 × 参数网格回测，返回该组的权重配置列表。
1015→
1016→        迭代 #9 变更：
1017→            - per-strategy best params：从 Sharpe 改为 Alpha（vs SPY）
1018→            - top-K 排序：从 Sortino 改为 Alpha
1019→            - 新增 Sortino > 0.5 最低质量门槛（二级过滤，可放宽）
1020→            - ensemble weights：从 Sharpe 改为 Alpha
1021→        迭代 #10 变更：
1022→            - 用 `_backtest_batch` 替代 for-symbol 循环（10-20x 提速）
1023→            - 每组 / 每策略增加进度耗时日志
1024→        """
1025→        import time
1026→
1027→        group_start = time.time()
1028→
1029→        # 1. 读取组内所有标的数据
1030→        data = self._store.get_bars_multi(symbols, start, end)
1031→        if not data:
1032→            logger.warning(f"[MatrixBacktest] {group_id}: no data, skip")
1033→            return []
1034→
1035→        # 迭代 #9：获取 SPY 同期日收益率用于 alpha 计算（一次获取，组内复用）
1036→        spy_returns = self._get_spy_returns(start, end)
1037→
1038→        valid_symbol_count = sum(
1039→            1 for df in data.values() if df is not None and not df.empty and len(df) >= 30
1040→        )
1041→        logger.info(
1042→            f"[MatrixBacktest] {group_id}: start — "
1043→            f"{len(strategies)} strategies × {valid_symbol_count} valid symbols"
1044→        )
1045→
1046→        # 2. 对每个策略 × 每组参数，按 alpha 选最优参数
1047→        group_results: list[tuple[str, dict, list[SingleBacktestResult]]] = []
1048→
1049→        for strategy in strategies:
1050→            strat_start = time.time()
1051→
1052→            # ⚠️ 早期检测未注册策略名（迭代 #1 修复"策略名拼写错误被静默跳过"的 bug）
1053→            # 之前 _backtest_one 内部静默 return None，导致 main.py 误用 "rsi"/"macd"/"bollinger"
1054→            # 简称 6 天未被发现。改为 WARNING 级日志 + continue。
1055→            if strategy not in STRATEGY_REGISTRY:
1056→                logger.warning(
1057→                    f"[MatrixBacktest] {group_id}: strategy '{strategy}' not in "
1058→                    f"STRATEGY_REGISTRY — skipped. "
1059→                    f"Check spelling against @register_strategy decorators. "
1060→                    f"Known: {sorted(STRATEGY_REGISTRY.keys())}"
1061→                )
1062→                continue
1063→            grid = param_grids.get(strategy, {})
1064→            param_combos = list(
1065→                dict(zip(grid.keys(), combo))
1066→                for combo in itertools.product(*grid.values())
1067→            ) if grid else [{}]
1068→
1069→            best_params = None
1070→            best_alpha = float("-inf")
1071→            best_sharpe = 0.0       # 仅用于 GroupBacktestResult 存档
1072→            best_sortino = 0.0      # 仅用于 GroupBacktestResult 存档
1073→            best_results: list[SingleBacktestResult] = []
1074→
1075→            for params in param_combos:
1076→                # 迭代 #10：用 _backtest_batch 一次处理组内所有标的
1077→                # 替代原 for sym in symbols: _backtest_one(...) 的逐标的循环
1078→                results = _backtest_batch(
1079→                    data, strategy, params,
1080→                    self._init_cash, self._fees, self._slippage,
1081→                )
1082→
1083→                if not results:
1084→                    continue
1085→
1086→                # ⚠️ 等权合并日收益率序列，一次性计算所有指标
1087→                # 迭代 #9：复用 combined 计算 sharpe / sortino / alpha
1088→                combined = _combine_daily_returns(results)
1089→                ps = _compute_sharpe(combined)
1090→                pso = _compute_sortino(combined)
1091→                alpha = _compute_alpha(combined, spy_returns)
1092→
1093→                # 迭代 #9：per-strategy best params 用 alpha 选（替代 Sharpe）
1094→                if alpha > best_alpha:
1095→                    best_alpha = alpha
1096→                    best_sharpe = ps
1097→                    best_sortino = pso
1098→                    best_params = params
1099→                    best_results = results
1100→
1101→            if best_params is not None and best_results:
1102→                group_results.append((strategy, best_params, best_results))
1103→                report.group_results.append(GroupBacktestResult(
1104→                    group_id=group_id,
1105→                    strategy=strategy,
1106→                    params=best_params,
1107→                    portfolio_sharpe=best_sharpe,
1108→                    avg_total_return_pct=_safe_mean(
1109→                        [r.total_return_pct for r in best_results]
1110→                    ),
1111→                    avg_max_drawdown_pct=_safe_mean(
1112→                        [r.max_drawdown_pct for r in best_results]
1113→                    ),
1114→                    avg_win_rate_pct=_safe_mean(
1115→                        [r.win_rate_pct for r in best_results]
1116→                    ),
1117→                    symbol_count=len(best_results),
1118→                    portfolio_sortino=best_sortino,
1119→                    portfolio_max_drawdown=_portfolio_max_drawdown_from_results(
1120→                        best_results
1121→                    ),
1122→                    backtest_alpha=best_alpha,
1123→                ))
1124→
1125→            logger.info(
1126→                f"[MatrixBacktest] {group_id}: {strategy} done in "
1127→                f"{time.time() - strat_start:.1f}s "
1128→                f"({len(param_combos)} param combos × {valid_symbol_count} symbols)"
1129→            )
1130→
1131→        if not group_results:
1132→            logger.warning(
1133→                f"[MatrixBacktest] {group_id}: no valid results "
1134→                f"(elapsed {time.time() - group_start:.1f}s)"
1135→            )
1136→            return []
1137→
1138→        # 3. 迭代 #9：DD 硬约束 + Sortino 门槛 + Alpha 排序选 Top-K
1139→        #    Constitution L1: portfolio DD ≤ 20% 是硬约束（保留）
1140→        #    新增：Sortino > 0.5 最低质量门槛（可放宽）
1141→        #    变更：排序指标从 Sortino 改为 Alpha
1142→        #
1143→        #    三级过滤策略：
1144→        #      Tier 1: DD ≤ 20% AND Sortino > 0.5 → Alpha 降序
1145→        #      Tier 2 (fallback): Tier 1 为空 → 仅 DD ≤ 20% → Alpha 降序
1146→        #      Tier 3 (fallback): Tier 2 为空 → 按 DD 升序，标记 dd_constrained=True
1147→        candidates: list[
1148→            tuple[str, dict, list[SingleBacktestResult], float, float, float]
1149→        ] = []
1150→        for (strategy, params, results) in group_results:
1151→            pso = _portfolio_sortino_from_results(results)
1152→            pdd = _portfolio_max_drawdown_from_results(results)
1153→            # 复用 _combine_daily_returns 计算 alpha（与 per-strategy 选择一致）
1154→            alpha = _compute_alpha(_combine_daily_returns(results), spy_returns)
1155→            candidates.append((strategy, params, results, pso, pdd, alpha))
1156→
1157→        # Tier 1: DD ≤ 20% AND Sortino > 0.5
1158→        compliant = [
1159→            c for c in candidates
1160→            if c[4] <= MAX_PORTFOLIO_DRAWDOWN_PCT and c[3] > MIN_SORTINO_THRESHOLD
1161→        ]
1162→        if compliant:
1163→            # Tier 1 命中：按 Alpha 降序取 top-K
1164→            ranked = sorted(compliant, key=lambda x: x[5], reverse=True)
1165→            dd_constrained = False
1166→            logger.info(
1167→                f"[MatrixBacktest] {group_id}: DD + Sortino filter passed — "
1168→                f"{len(compliant)}/{len(candidates)} candidates compliant "
1169→                f"(DD <= {MAX_PORTFOLIO_DRAWDOWN_PCT}% AND Sortino > {MIN_SORTINO_THRESHOLD})"
1170→            )
1171→        else:
1172→            # Tier 2: 放宽 Sortino 门槛，仅保留 DD 约束
1173→            dd_compliant = [
1174→                c for c in candidates if c[4] <= MAX_PORTFOLIO_DRAWDOWN_PCT
1175→            ]
1176→            if dd_compliant:
1177→                # Tier 2 命中：按 Alpha 降序取 top-K（dd_constrained 仍为 False）
1178→                ranked = sorted(dd_compliant, key=lambda x: x[5], reverse=True)
1179→                dd_constrained = False
1180→                logger.warning(
1181→                    f"[MatrixBacktest] {group_id}: Sortino filter relaxed — "
1182→                    f"no candidate passed Sortino > {MIN_SORTINO_THRESHOLD}. "
1183→                    f"Fallback to DD-only filter: "
1184→                    f"{len(dd_compliant)}/{len(candidates)} candidates DD-compliant."
1185→                )
1186→            else:
1187→                # Tier 3: 无 DD 合规候选 → 按 DD 升序，标记 dd_constrained
1188→                # （结构性问题，如 NDX_high_vol 全部 > 20%）
1189→                ranked = sorted(candidates, key=lambda x: x[4])
1190→                dd_constrained = True
1191→                logger.warning(
1192→                    f"[MatrixBacktest] {group_id}: NO compliant candidates "
1193→                    f"(all {len(candidates)} exceed DD={MAX_PORTFOLIO_DRAWDOWN_PCT}%). "
1194→                    f"Fallback: selected top-{self._top_k} by lowest DD. "
1195→                    f"This group is marked dd_constrained=True — "
1196→                    f"review whether to drop the group or accept the risk."
1197→                )
1198→                report.warnings.append(
1199→                    f"{group_id}: dd_constrained=True "
1200→                    f"(min DD={ranked[0][4]:.2f}% > {MAX_PORTFOLIO_DRAWDOWN_PCT}%)"
1201→                )
1202→
1203→        top_results = ranked[: self._top_k]
1204→
1205→        # 把 dd_constrained 标记同步到 report.group_results 中对应组的条目
1206→        for gr in report.group_results:
1207→            if gr.group_id == group_id:
1208→                gr.dd_constrained = dd_constrained
1209→
1210→        # 4. 优化 ensemble 权重（单点离散值加权投票语义，迭代 #9 改用 alpha）
1211→        weighted = _optimize_ensemble_weights(
1212→            [(s, p, r) for (s, p, r, _, _, _) in top_results],
1213→            spy_returns=spy_returns,
1214→        )
1215→
1216→        # 5. 构建权重配置列表
1217→        weights_list = []
1218→        for strategy, params, weight in weighted:
1219→            # 找到对应的 GroupBacktestResult
1220→            gr = next(
1221→                (r for r in report.group_results
1222→                 if r.group_id == group_id and r.strategy == strategy),
1223→                None,
1224→            )
1225→            # 迭代 #4：新增 backtest_dd_status 字段（'pass' / 'dd_constrained'）
1226→            # 作为风险 metadata 标记，与 dd_constrained bool 同义但更可读
1227→            backtest_dd_status = "dd_constrained" if dd_constrained else "pass"
1228→            weights_list.append({
1229→                "strategy": strategy,
1230→                "params": params,
1231→                "weight": round(weight, 4),
1232→                "backtest_sharpe": round(gr.portfolio_sharpe if gr else 0.0, 4),
1233→                "backtest_sortino": round(gr.portfolio_sortino if gr else 0.0, 4),
1234→                "backtest_max_drawdown": round(gr.portfolio_max_drawdown if gr else 0.0, 4),
1235→                "backtest_win_rate": round(gr.avg_win_rate_pct / 100 if gr else 0.5, 4),
1236→                # 迭代 #9：新增 backtest_alpha 字段（vs SPY 的超额收益百分数）
1237→                # 下游 PortfolioBacktester 可读此字段验证 alpha 一致性
1238→                "backtest_alpha": round(gr.backtest_alpha if gr else 0.0, 4),
1239→                # 迭代 #3：标记该组是否用了 DD fallback（无合规候选）
1240→                # 同组所有策略条目共享同一 dd_constrained 值
1241→                "dd_constrained": dd_constrained,
1242→                # 迭代 #4：backtest_dd_status — 风险 metadata 字段
1243→                # 'pass' = 该组有合规候选（DD ≤ 20%）
1244→                # 'dd_constrained' = fallback 触发（无合规候选，按最低 DD 取 top-K）
1245→                # 下游消费方（PortfolioBacktester / 风控观测）可读此字段判断
1246→                # 该组权重的可靠性，作为风险信号标记
1247→                "backtest_dd_status": backtest_dd_status,
1248→            })
1249→
1250→        logger.info(
1251→            f"[MatrixBacktest] {group_id}: all strategies done in "
1252→            f"{time.time() - group_start:.1f}s "
1253→            f"(top-{self._top_k} selected, dd_constrained={dd_constrained})"
1254→        )
1255→
1256→        return weights_list
1257→
1258→    def _write_weights(
1259→        self, report: MatrixBacktestReport, output_file: str | Path
1260→    ) -> None:
1261→        """将矩阵回测结果写入 strategy_weights.json。"""
1262→        output_file = Path(output_file)
1263→        output_file.parent.mkdir(parents=True, exist_ok=True)
1264→
1265→        data = {
1266→            "_meta": {
1267→                "generated_at": report.generated_at,
1268→                "backtest_window": report.backtest_window,
1269→                "reoptimize_freq": "monthly",
1270→                "survivorship_bias_warning": (
1271→                    "使用当前成分股回测，S&P 500 5年成分变动约100只(~20%)，"
1272→                    "均值回归组(SPX_low_vol)结果可能系统性偏高"
1273→                ),
1274→            },
1275→            "groups": report.groups,
1276→        }
1277→
1278→        with open(output_file, "w", encoding="utf-8") as f:
1279→            json.dump(data, f, indent=2, ensure_ascii=False)
1280→
1281→        logger.info(f"[MatrixBacktest] weights saved to {output_file}")
1282→
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
  43→# 迭代 #9 新增：Sortino 最低质量门槛，用于 top-K 选择时的二级过滤
  44→# 排除 Sortino ≤ 0.5 的"垃圾"策略（即使 alpha 高也不选）
  45→# 设计动机：alpha 排序选出高绝对收益策略，但需 Sortino 门槛保证基本下行质量
  46→# fallback：若无候选通过此门槛，放宽过滤（仅保留 DD 硬约束）
  47→MIN_SORTINO_THRESHOLD: float = 0.5
  48→
  49→
  50→# ---------------------------------------------------------------------------
  51→# 数据结构
  52→# ---------------------------------------------------------------------------
  53→
  54→@dataclass
  55→class SingleBacktestResult:
  56→    """单只标的单策略回测结果。"""
  57→
  58→    symbol: str
  59→    strategy: str
  60→    params: dict
  61→    sharpe: float
  62→    total_return_pct: float
  63→    max_drawdown_pct: float
  64→    win_rate_pct: float
  65→    total_trades: int
  66→    daily_returns: pd.Series    # pf.returns() — 供组合 Sharpe / Sortino 计算
  67→    sortino: float = 0.0       # Constitution L1 首要 KPI（迭代 #1 新增）
  68→
  69→
  70→@dataclass
  71→class GroupBacktestResult:
  72→    """单组策略回测结果。"""
  73→
  74→    group_id: str
  75→    strategy: str
  76→    params: dict
  77→    portfolio_sharpe: float          # 等权组合 Sharpe（而非算术平均）
  78→    avg_total_return_pct: float
  79→    avg_max_drawdown_pct: float
  80→    avg_win_rate_pct: float
  81→    symbol_count: int
  82→    portfolio_sortino: float = 0.0          # 等权组合 Sortino（迭代 #1 新增）
  83→    portfolio_max_drawdown: float = 0.0     # 等权组合最大回撤（迭代 #2 新增，Constitution L1 KPI）
  84→    dd_constrained: bool = False            # 迭代 #3：该组是否用了 DD fallback（无合规候选）
  85→    backtest_alpha: float = 0.0              # 迭代 #9：alpha vs SPY（百分数），用于排序策略选择
  86→
  87→
  88→@dataclass
  89→class MatrixBacktestReport:
  90→    """整个矩阵回测的汇总报告。"""
  91→
  92→    generated_at: str
  93→    backtest_window: str
  94→    groups: dict[str, list[dict]]   # group_id → [策略权重配置]
  95→    group_results: list[GroupBacktestResult] = field(default_factory=list)
  96→    warnings: list[str] = field(default_factory=list)
  97→
  98→
  99→# ---------------------------------------------------------------------------
 100→# Walk-Forward 数据结构（迭代 #3 新增，Constitution L7 验证流水线）
 101→# ---------------------------------------------------------------------------
 102→
 103→@dataclass
 104→class WalkForwardRound:
 105→    """单轮 Walk-Forward 验证结果。
 106→
 107→    一轮 = 训练期（找最优参数）+ 验证期（用同参数回测，记录样本外指标）。
 108→
 109→    Attributes:
 110→        round_num:    轮次编号（1-indexed）
 111→        train_start:  训练期起始日期（含）
 112→        train_end:    训练期结束日期（含）
 113→        val_start:    验证期起始日期（含）
 114→        val_end:      验证期结束日期（含）
 115→        val_sortino:  验证期等权组合 Sortino Ratio（年化）
 116→        val_max_dd:   验证期等权组合最大回撤（正值百分数，0~100）
 117→        passed:       是否通过 = val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD (15%)
 118→    """
 119→
 120→    round_num: int
 121→    train_start: date
 122→    train_end: date
 123→    val_start: date
 124→    val_end: date
 125→    val_sortino: float
 126→    val_max_dd: float
 127→    passed: bool
 128→
 129→
 130→@dataclass
 131→class WalkForwardReport:
 132→    """Walk-Forward 4 轮验证汇总报告。
 133→
 134→    Constitution L7 要求 Backtest(>=5年) → Walk-Forward(4轮) → Paper → Live。
 135→    本报告是 Walk-Forward 阶段的产出。
 136→
 137→    Attributes:
 138→        rounds:         每轮结果列表（长度通常为 4）
 139→        pass_all_rounds: 是否所有轮都通过（all(r.passed for r in rounds)）
 140→        max_val_dd:     所有轮中最大的验证期 DD（用于风险监控）
 141→    """
 142→
 143→    rounds: list[WalkForwardRound] = field(default_factory=list)
 144→    pass_all_rounds: bool = False
 145→    max_val_dd: float = 0.0
 146→
 147→
 148→# ---------------------------------------------------------------------------
 149→# 核心函数
 150→# ---------------------------------------------------------------------------
 151→
 152→def _safe_float(value: Any, default: float = 0.0) -> float:
 153→    """NaN/None/非数值安全转 float（迭代 #2 新增）。
 154→
 155→    问题背景：vectorbt 在无交易场景下，`pf.stats()` 的 Win Rate / Sharpe 等
 156→    字段会返回 NaN。`float(NaN or 0.0)` 仍是 NaN（NaN 是 truthy），导致
 157→    JSON 序列化写出非法 JSON（NaN/Infinity 非 JSON 规范）。
 158→
 159→    处理顺序：
 160→        1. None → default
 161→        2. 数值类型但 NaN/Inf → default
 162→        3. 非数值（字符串等）尝试 float() 转换，失败 → default
 163→    """
 164→    if value is None:
 165→        return default
 166→    try:
 167→        f = float(value)
 168→    except (TypeError, ValueError):
 169→        return default
 170→    if not np.isfinite(f):   # 拦截 NaN / +Inf / -Inf
 171→        return default
 172→    return f
 173→
 174→
 175→def _safe_mean(values: Any, default: float = 0.0) -> float:
 176→    """空列表 / 全 NaN 安全的均值（迭代 #2 新增）。
 177→
 178→    问题背景：`np.mean([])` 会触发 RuntimeWarning 并返回 NaN；
 179→    `np.mean([NaN, NaN])` 直接返回 NaN。在 GroupBacktestResult 聚合时
 180→    若某组只有 1 个标的且其字段为 NaN，会导致下游 JSON 序列化失败。
 181→
 182→    行为：
 183→        - 空列表 / 全 NaN → default
 184→        - 部分 NaN → 自动忽略 NaN 后取均值（np.nanmean 语义）
 185→    """
 186→    arr = np.asarray(values, dtype=float)
 187→    if arr.size == 0:
 188→        return default
 189→    mask = np.isfinite(arr)
 190→    if not mask.any():
 191→        return default
 192→    return float(arr[mask].mean())
 193→
 194→
 195→def _compute_sharpe(returns: pd.Series, periods_per_year: int = 252) -> float:
 196→    """从日收益率序列计算年化 Sharpe Ratio。"""
 197→    returns = returns.dropna()
 198→    if len(returns) < 5:
 199→        return 0.0
 200→    mean = returns.mean()
 201→    std = returns.std()
 202→    if std <= 0 or np.isnan(std):
 203→        return 0.0
 204→    return float(mean / std * np.sqrt(periods_per_year))
 205→
 206→
 207→def _compute_sortino(
 208→    returns: pd.Series,
 209→    periods_per_year: int = 252,
 210→    target: float = 0.0,
 211→) -> float:
 212→    """从日收益率序列计算年化 Sortino Ratio（Constitution L1 首要 KPI）。
 213→
 214→    Sortino = (mean(returns) - target) / downside_deviation * sqrt(periods_per_year)
 215→    downside_deviation = sqrt( mean( min(0, returns - target)^2 ) )
 216→
 217→    与 Sharpe 的区别：仅对下行波动惩罚，上行波动不计入分母。
 218→    适合"收益>0 但偶尔大跌"的中长线策略评估。
 219→
 220→    退化处理（与 _compute_sharpe 一致）：
 221→        - 样本 < 5 → 0.0
 222→        - 下行波动 ≤ 0（无下行样本）→ 0.0（理论为 +inf，返回 0 保持保守 + 可算术聚合）
 223→
 224→    Args:
 225→        returns:          日收益率序列（如 pf.returns()）
 226→        periods_per_year: 年化因子（日线 = 252）
 227→        target:           MAR/目标收益率，默认 0（与 _compute_sharpe 无风险利率假设一致）
 228→
 229→    Returns:
 230→        年化 Sortino Ratio
 231→    """
 232→    returns = returns.dropna()
 233→    if len(returns) < 5:
 234→        return 0.0
 235→    excess = returns - target
 236→    downside = excess.where(excess < 0, 0.0)        # 仅保留负偏离，正偏离置 0
 237→    dd = np.sqrt((downside ** 2).mean())
 238→    if dd <= 0 or np.isnan(dd):
 239→        return 0.0
 240→    return float(returns.mean() / dd * np.sqrt(periods_per_year))
 241→
 242→
 243→def _combine_daily_returns(results: list[SingleBacktestResult]) -> pd.Series:
 244→    """等权合并组内日收益率序列，返回组合日收益率（迭代 #9 新增）。
 245→
 246→    与 _portfolio_sharpe_from_results / _portfolio_sortino_from_results 同语义：
 247→    将所有标的日收益率等权合并为组合序列。提取为独立函数以便 alpha 计算
 248→    和 per-strategy best params 选择复用，避免重复 pd.concat。
 249→
 250→    Args:
 251→        results: 单策略多标的的回测结果列表
 252→
 253→    Returns:
 254→        组合日收益率 pd.Series；无有效数据时返回空 Series
 255→    """
 256→    valid = [r.daily_returns for r in results if not r.daily_returns.empty]
 257→    if not valid:
 258→        return pd.Series(dtype=float)
 259→    return pd.concat(valid, axis=1).mean(axis=1)
 260→
 261→
 262→def _compute_alpha(
 263→    strategy_daily_returns: pd.Series,
 264→    spy_daily_returns: pd.Series | None,
 265→    periods_per_year: int = 252,
 266→) -> float:
 267→    """计算 alpha = 策略年化收益 - SPY 年化收益（迭代 #9 新增）。
 268→
 269→    Alpha 衡量策略相对 SPY buy-and-hold 的超额收益。正值表示跑赢 SPY，
 270→    负值表示跑输 SPY。用于 top-K 策略选择和 per-strategy best params 选择，
 271→    替代之前基于 Sortino/Sharpe 的选择逻辑（参考 iteration #9 spec）。
 272→
 273→    年化公式：(1 + mean_daily) ** periods_per_year - 1
 274→    使用算术平均日收益的几何年化，与 PortfolioBacktester 同口径。
 275→
 276→    降级处理：SPY 数据不可用（None 或空）→ 返回 0.0（不抛异常）。
 277→    这样在 SPY 数据缺失时，alpha 排序退化为"原顺序"，不会阻塞回测。
 278→
 279→    Args:
 280→        strategy_daily_returns: 策略组合日收益率序列
 281→        spy_daily_returns:      SPY 日收益率序列；None 表示数据不可用
 282→        periods_per_year:       年化因子（日线 = 252）
 283→
 284→    Returns:
 285→        Alpha 百分数（如 5.23 表示策略年化收益跑赢 SPY 5.23 个百分点）；
 286→        SPY 不可用时返回 0.0
 287→    """
 288→    if spy_daily_returns is None or spy_daily_returns.empty:
 289→        return 0.0
 290→    if strategy_daily_returns is None or strategy_daily_returns.empty:
 291→        return 0.0
 292→
 293→    # 对齐时间索引（inner join 取交集）
 294→    aligned = pd.concat(
 295→        [strategy_daily_returns.rename("strat"), spy_daily_returns.rename("spy")],
 296→        axis=1,
 297→        join="inner",
 298→    ).dropna()
 299→    if aligned.empty or len(aligned) < 2:
 300→        return 0.0
 301→
 302→    strat_returns = aligned["strat"]
 303→    spy_returns = aligned["spy"]
 304→
 305→    # 年化收益 = (1 + mean_daily)^252 - 1
 306→    strat_mean = strat_returns.mean()
 307→    spy_mean = spy_returns.mean()
 308→    if not np.isfinite(strat_mean) or not np.isfinite(spy_mean):
 309→        return 0.0
 310→
 311→    strat_annual = (1.0 + strat_mean) ** periods_per_year - 1.0
 312→    spy_annual = (1.0 + spy_mean) ** periods_per_year - 1.0
 313→
 314→    alpha = (strat_annual - spy_annual) * 100.0  # 转为百分数
 315→    if not np.isfinite(alpha):
 316→        return 0.0
 317→    return float(alpha)
 318→
 319→
 320→def _backtest_one(
 321→    df: pd.DataFrame,
 322→    strategy_name: str,
 323→    params: dict,
 324→    init_cash: float = 100_000.0,
 325→    fees: float = 0.001,
 326→    slippage: float = 0.001,
 327→) -> SingleBacktestResult | None:
 328→    """对单只标的执行单次回测。
 329→
 330→    使用 open= 参数确保信号在下一根 bar 的开盘价执行（与实盘一致）。
 331→
 332→    Returns:
 333→        SingleBacktestResult 或 None（数据不足/策略异常时）
 334→    """
 335→    strategy_fn = STRATEGY_REGISTRY.get(strategy_name)
 336→    if strategy_fn is None:
 337→        return None
 338→
 339→    if df.empty or len(df) < 30:
 340→        return None
 341→
 342→    try:
 343→        close = df["close"]
 344→        open_ = df["open"] if "open" in df.columns else None
 345→
 346→        # 调用策略（兼容需要 df 的策略）
 347→        try:
 348→            sig = strategy_fn(close, df=df, **params)
 349→        except TypeError:
 350→            sig = strategy_fn(close, **params)
 351→
 352→        entries = sig == 1
 353→        exits   = sig == -1
 354→
 355→        pf_kwargs: dict[str, Any] = dict(
 356→            entries=entries,
 357→            exits=exits,
 358→            init_cash=init_cash,
 359→            fees=fees,
 360→            slippage=slippage,
 361→            size=0.95,
 362→            size_type="Percent",
 363→            freq="D",
 364→        )
 365→
 366→        # ⚠️ 必须传 open= 参数：信号在下一根 bar 开盘价执行，与实盘一致
 367→        if open_ is not None:
 368→            pf = vbt.Portfolio.from_signals(close=close, open=open_, **pf_kwargs)
 369→        else:
 370→            pf = vbt.Portfolio.from_signals(close, **pf_kwargs)
 371→
 372→        stats = pf.stats()
 373→
 374→        daily_returns = pf.returns()
 375→
 376→        return SingleBacktestResult(
 377→            symbol=str(df.index.name or ""),
 378→            strategy=strategy_name,
 379→            params=params,
 380→            sharpe=_safe_float(stats.get("Sharpe Ratio")),
 381→            total_return_pct=_safe_float(stats.get("Total Return [%]")),
 382→            max_drawdown_pct=_safe_float(stats.get("Max Drawdown [%]")),
 383→            win_rate_pct=_safe_float(stats.get("Win Rate [%]")),
 384→            total_trades=int(_safe_float(stats.get("Total Trades"), default=0.0)),
 385→            daily_returns=daily_returns,
 386→            sortino=_compute_sortino(daily_returns),
 387→        )
 388→    except Exception as e:
 389→        logger.debug(f"[backtest_one] {strategy_name}({params}) failed: {e}")
 390→        return None
 391→
 392→
 393→def _backtest_batch(
 394→    data: dict[str, pd.DataFrame],
 395→    strategy_name: str,
 396→    params: dict,
 397→    init_cash: float = 100_000.0,
 398→    fees: float = 0.001,
 399→    slippage: float = 0.001,
 400→) -> list[SingleBacktestResult]:
 401→    """对组内所有标的批量执行回测（迭代 #10 新增）。
 402→
 403→    核心优化：用一次 vbt.Portfolio.from_signals 处理组内所有标的，
 404→    替代 `_backtest_one` 的 for-symbol 循环。调用次数从 O(N 标的)
 405→    降为 O(1)，预计 10-20x 提速（spec §1）。
 406→
 407→    实现要点：
 408→        1. 逐标的调用策略函数（保持与 `_backtest_one` 一致的调用语义：
 409→           先尝试 `strategy_fn(close, df=df, **params)`，TypeError 时
 410→           回退到 `strategy_fn(close, **params)`）。策略函数本身不改。
 411→        2. 构建列式矩阵（每列一个标的），用一次 vbt 调用回测所有标的。
 412→           vbt 1.0+ 的列分组语义保证每列独立结算 P&L。
 413→        3. 通过 `pf[sym]` 提取每列的 stats/daily_returns，输出格式与
 414→           `_backtest_one` 完全一致，下游聚合代码无需修改。
 415→
 416→    对齐策略：
 417→        - 用 `pd.DataFrame(dict)` 构造时自动 outer-join 时间索引，
 418→          缺失值填 NaN。
 419→        - vbt 对 NaN close 的处理：内部 fillna 为 0 收益率，等价于
 420→          "该标的此日期不交易"。当标的在样本外日期缺失时（如退市、
 421→          新上市），其 stats 仍按其有效日期区间计算。
 422→        - 在美股实际场景中所有标的共享交易日历，日期对齐天然成立，
 423→          不会有大量 NaN。
 424→
 425→    Args:
 426→        data:          {symbol: OHLCV DataFrame} 字典
 427→        strategy_name: 策略名
 428→        params:        策略参数
 429→        init_cash:     初始资金（vbt 给每列分配独立的 init_cash）
 430→        fees:          手续费率
 431→        slippage:      滑点率
 432→
 433→    Returns:
 434→        SingleBacktestResult 列表（与 `_backtest_one` 输出格式一致）。
 435→        数据不足 / 策略异常的标的会被跳过（不返回 None，不抛异常）。
 436→        空数据时返回空列表。
 437→    """
 438→    strategy_fn = STRATEGY_REGISTRY.get(strategy_name)
 439→    if strategy_fn is None:
 440→        return []
 441→
 442→    # 1. 逐标的调用策略函数，构建 signal / close / open 列
 443→    signal_columns: dict[str, pd.Series] = {}
 444→    close_columns: dict[str, pd.Series] = {}
 445→    open_columns: dict[str, pd.Series] = {}
 446→
 447→    for sym, df in data.items():
 448→        if df is None or df.empty or len(df) < 30:
 449→            continue
 450→        close = df["close"]
 451→        if "open" in df.columns:
 452→            open_ = df["open"]
 453→            open_columns[sym] = open_
 454→        else:
 455→            open_ = None
 456→
 457→        # 调用策略（与 _backtest_one 一致的 try/except 语义）
 458→        try:
 459→            sig = strategy_fn(close, df=df, **params)
 460→        except TypeError:
 461→            sig = strategy_fn(close, **params)
 462→        except Exception as e:
 463→            logger.debug(
 464→                f"[backtest_batch] {strategy_name}({params}) {sym} failed: {e}"
 465→            )
 466→            continue
 467→
 468→        signal_columns[sym] = sig
 469→        close_columns[sym] = close
 470→
 471→    if not signal_columns:
 472→        return []
 473→
 474→    # 2. 构建矩阵（自动 outer-join 索引，缺失值填 NaN）
 475→    close_matrix = pd.DataFrame(close_columns)
 476→    signal_matrix = pd.DataFrame(signal_columns)
 477→    has_open = bool(open_columns)
 478→    open_matrix = pd.DataFrame(open_columns) if has_open else None
 479→
 480→    # 3. 一次 vbt 调用处理所有标的
 481→    entries = signal_matrix == 1
 482→    exits = signal_matrix == -1
 483→
 484→    pf_kwargs: dict[str, Any] = dict(
 485→        entries=entries,
 486→        exits=exits,
 487→        init_cash=init_cash,
 488→        fees=fees,
 489→        slippage=slippage,
 490→        size=0.95,
 491→        size_type="Percent",
 492→        freq="D",
 493→    )
 494→
 495→    try:
 496→        if has_open:
 497→            pf = vbt.Portfolio.from_signals(
 498→                close=close_matrix, open=open_matrix, **pf_kwargs
 499→            )
 500→        else:
 501→            pf = vbt.Portfolio.from_signals(close_matrix, **pf_kwargs)
 502→    except Exception as e:
 503→        logger.warning(
 504→            f"[backtest_batch] {strategy_name}({params}) vbt call failed: {e} "
 505→            f"— falling back to per-symbol _backtest_one"
 506→        )
 507→        # 回滚方案：批量失败时退化为逐标的回测，保证回测不中断
 508→        results: list[SingleBacktestResult] = []
 509→        for sym, df in data.items():
 510→            if df is None or df.empty or len(df) < 30:
 511→                continue
 512→            df = df.copy()
 513→            df.index.name = sym
 514→            r = _backtest_one(
 515→                df, strategy_name, params, init_cash, fees, slippage
 516→            )
 517→            if r is not None:
 518→                results.append(r)
 519→        return results
 520→
 521→    # 4. 提取 per-symbol 结果（与 _backtest_one 输出格式一致）
 522→    results = []
 523→    for sym in signal_matrix.columns:
 524→        try:
 525→            pf_sym = pf[sym]
 526→            stats = pf_sym.stats()
 527→            daily_returns = pf_sym.returns()
 528→            results.append(SingleBacktestResult(
 529→                symbol=sym,
 530→                strategy=strategy_name,
 531→                params=params,
 532→                sharpe=_safe_float(stats.get("Sharpe Ratio")),
 533→                total_return_pct=_safe_float(stats.get("Total Return [%]")),
 534→                max_drawdown_pct=_safe_float(stats.get("Max Drawdown [%]")),
 535→                win_rate_pct=_safe_float(stats.get("Win Rate [%]")),
 536→                total_trades=int(_safe_float(stats.get("Total Trades"), default=0.0)),
 537→                daily_returns=daily_returns,
 538→                sortino=_compute_sortino(daily_returns),
 539→            ))
 540→        except Exception as e:
 541→            logger.debug(
 542→                f"[backtest_batch] {strategy_name}({params}) {sym} "
 543→                f"stats extraction failed: {e}"
 544→            )
 545→            continue
 546→
 547→    return results
 548→
 549→
 550→def _portfolio_sharpe_from_results(results: list[SingleBacktestResult]) -> float:
 551→    """等权合并组内日收益率序列，计算组合 Sharpe。
 552→
 553→    ⚠️ 不能取各标的 Sharpe 算术平均（Sharpe 是比率，不能直接平均）。
 554→    正确做法：将所有标的日收益率等权合并为组合序列，再计算 Sharpe。
 555→    """
 556→    valid = [r.daily_returns for r in results if not r.daily_returns.empty]
 557→    if not valid:
 558→        return 0.0
 559→
 560→    # 对齐时间索引，等权平均
 561→    combined = pd.concat(valid, axis=1).mean(axis=1)
 562→    return _compute_sharpe(combined)
 563→
 564→
 565→def _portfolio_sortino_from_results(results: list[SingleBacktestResult]) -> float:
 566→    """等权合并组内日收益率序列，计算组合 Sortino（与 _portfolio_sharpe_from_results 同语义）。
 567→
 568→    不能取各标的 Sortino 算术平均（与 Sharpe 同理：比率不可直接平均）。
 569→    """
 570→    valid = [r.daily_returns for r in results if not r.daily_returns.empty]
 571→    if not valid:
 572→        return 0.0
 573→    combined = pd.concat(valid, axis=1).mean(axis=1)
 574→    return _compute_sortino(combined)
 575→
 576→
 577→def _portfolio_max_drawdown_from_results(
 578→    results: list[SingleBacktestResult],
 579→) -> float:
 580→    """等权合并组内日收益率序列，计算组合最大回撤（迭代 #2 新增，Constitution L1 KPI）。
 581→
 582→    与 `_portfolio_sharpe_from_results` 同语义：不能取各标的 DD 算术平均，
 583→    因为 DD 是路径依赖的比率。正确做法是先把��内日收益率等权合并为组合序列，
 584→    再 cumprod → cummax → drawdown → max。
 585→
 586→    返回值约定：百分比形式（与 `SingleBacktestResult.max_drawdown_pct` 一致，
 587→    vectorbt stats 中 `Max Drawdown [%]` 同样是百分数，例如 -15.2 表示 15.2% 回撤）。
 588→    本函数返回正值（0.0 ~ 100.0）便于聚合与 JSON 输出。
 589→
 590→    退化处理：
 591→        - 无有效日收益率 → 0.0
 592→        - 全 0 收益率（cumprod 恒为 1.0）→ 0.0
 593→    """
 594→    valid = [r.daily_returns for r in results if not r.daily_returns.empty]
 595→    if not valid:
 596→        return 0.0
 597→    combined = pd.concat(valid, axis=1).mean(axis=1).dropna()
 598→    if len(combined) < 2:
 599→        return 0.0
 600→    # 组合累计净值：初始 1.0，每日乘 (1 + r)
 601→    cumvalue = (1.0 + combined).cumprod()
 602→    peak = cumvalue.cummax()
 603→    drawdown = (cumvalue - peak) / peak   # 负值，0 表示无回撤
 604→    dd_max_pct = float(drawdown.min())    # 最负值，例如 -0.152
 605→    if not np.isfinite(dd_max_pct):
 606→        return 0.0
 607→    # 转为正百分数（与 vectorbt Max Drawdown [%] 的口径一致但取正号）
 608→    return abs(dd_max_pct) * 100.0
 609→
 610→
 611→def _optimize_ensemble_weights(
 612→    group_results: list[tuple[str, dict, list[SingleBacktestResult]]],
 613→    spy_returns: pd.Series | None = None,
 614→    conflict_threshold: float = 0.3,
 615→) -> list[tuple[str, dict, float]]:
 616→    """在"单点离散值加权投票"语义下优化 ensemble 权重。
 617→
 618→    实盘每根 bar 各策略产出离散值（1/-1/0），加权投票决定方向。
 619→    回测的权重优化必须使用相同语义，而非对整段时间序列做加权。
 620→
 621→    迭代 #9：权重计算从 Sharpe 改为 Alpha（vs SPY）。
 622→    动机：与 _run_group 的 top-K 排序口径一致，使 ensemble 权重直接
 623→    反映"跑赢 SPY 的程度"。SPY 不可用时 alpha=0，退化为等权。
 624→
 625→    Args:
 626→        group_results: [(strategy, params, [SingleBacktestResult]), ...]
 627→        spy_returns:   SPY 日收益率序列（用于 alpha 计算）；None 时退化为等权
 628→        conflict_threshold: 加权投票分数绝对值低于此时视为 HOLD
 629→
 630→    Returns:
 631→        [(strategy, params, weight), ...] 归一化权重列表
 632→    """
 633→    if len(group_results) == 1:
 634→        strategy, params, _ = group_results[0]
 635→        return [(strategy, params, 1.0)]
 636→
 637→    # 迭代 #9：用各策略的组合 alpha 归一化为权重（替代 Sharpe）
 638→    # alpha 可能 < 0（跑输 SPY），用 max(alpha, 0.01) 避免负权重
 639→    alphas = []
 640→    for strategy, params, results in group_results:
 641→        combined = _combine_daily_returns(results)
 642→        alpha = _compute_alpha(combined, spy_returns)
 643→        alphas.append(max(alpha, 0.01))  # 避免负/零权重
 644→
 645→    total = sum(alphas)
 646→    weights = [a / total for a in alphas]
 647→
 648→    return [
 649→        (strategy, params, weight)
 650→        for (strategy, params, _), weight in zip(group_results, weights)
 651→    ]
 652→
 653→
 654→# ---------------------------------------------------------------------------
 655→# Walk-Forward 验证（迭代 #3 新增，Constitution L7 验证流水线）
 656→# ---------------------------------------------------------------------------
 657→
 658→def _add_months(d: date, months: int) -> date:
 659→    """对 date 加/减 months 个月，自动 clamp 到月末。
 660→
 661→    使用 pandas DateOffset 以避免引入 dateutil 依赖（pandas 已是核心依赖）。
 662→    """
 663→    return (pd.Timestamp(d) + pd.DateOffset(months=months)).date()
 664→
 665→
 666→def _backtest_with_params_on_period(
 667→    mb: "MatrixBacktest",
 668→    symbols: list[str],
 669→    weights: list[dict[str, Any]],
 670→    start: date,
 671→    end: date,
 672→) -> list[pd.Series]:
 673→    """用给定权重配置在 [start, end] 期间回测，返回每条 (策略×标的) 的日收益率序列。
 674→
 675→    用于 Walk-Forward 验证期：用训练期产出的 best params 在验证期回测，
 676→    不再做参数搜索。返回原始日收益率列表，由调用方聚合为整体 portfolio。
 677→
 678→    迭代 #10 变更：用 `_backtest_batch` 替代 for-symbol 循环，
 679→    每个策略×参数组合一次 vbt 调用，加速 Walk-Forward 验证期回测。
 680→
 681→    Args:
 682→        mb:       MatrixBacktest 实例（复用其 store/init_cash/fees/slippage）
 683→        symbols:  该组的标的列表
 684→        weights:  训练期产出的权重配置（list of dict，含 strategy/params/weight）
 685→        start:    验证期起始日期
 686→        end:      验证期结束日期
 687→
 688→    Returns:
 689→        list[pd.Series] — 每条 (strategy×symbol) 的日收益率；空列表表示无有效数据
 690→    """
 691→    if not weights or not symbols:
 692→        return []
 693→
 694→    data = mb._store.get_bars_multi(symbols, start, end)
 695→    if not data:
 696→        return []
 697→
 698→    all_returns: list[pd.Series] = []
 699→    for w in weights:
 700→        strategy = w.get("strategy", "")
 701→        params = w.get("params", {})
 702→        if not strategy or strategy not in STRATEGY_REGISTRY:
 703→            continue
 704→        # 迭代 #10：一次 batch 调用处理组内所有标的
 705→        results = _backtest_batch(
 706→            data, strategy, params,
 707→            mb._init_cash, mb._fees, mb._slippage,
 708→        )
 709→        for r in results:
 710→            if not r.daily_returns.empty:
 711→                all_returns.append(r.daily_returns)
 712→    return all_returns
 713→
 714→
 715→def run_walk_forward(
 716→    mb: "MatrixBacktest",
 717→    strategies: list[str],
 718→    param_grids: dict[str, dict[str, list]],
 719→    rounds: int = 4,
 720→    train_months: int = 18,
 721→    val_months: int = 6,
 722→) -> WalkForwardReport:
 723→    """执行 N 轮 Walk-Forward 验证（Constitution L7 验证流水线硬要求）。
 724→
 725→    每轮流程：
 726→        1. 训练期 [train_start, train_end]：跑矩阵回测找最优参数
 727→        2. 验证期 [val_start, val_end]：用同参数回测，记录 portfolio Sortino 和 max DD
 728→        3. passed = val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD (15%)
 729→
 730→    时间窗口（动态计算，today=today）：
 731→        - 最后一轮 val_end = today - val_months（留 1 个 val 期给 paper trading）
 732→        - 每轮向前推 val_months
 733→        - train_end = val_start，train_start = train_end - train_months
 734→
 735→    默认参数 (rounds=4, train_months=18, val_months=6) 对应用户提供的固定窗口：
 736→        today=2026-07-01 →
 737→        Round 1: train 2021-07-02~2023-01-02, val 2023-01-02~2023-07-02
 738→        Round 2: train 2022-01-02~2023-07-02, val 2023-07-02~2024-01-02
 739→        Round 3: train 2022-07-02~2024-01-02, val 2024-01-02~2024-07-02
 740→        Round 4: train 2023-01-02~2024-07-02, val 2024-07-02~2025-01-02
 741→
 742→    Args:
 743→        mb:            MatrixBacktest 实例（复用其 store/universe/init_cash 等）
 744→        strategies:    策略名称列表
 745→        param_grids:   参数网格（与 mb.run() 接收的格式一致）
 746→        rounds:        轮次数（默认 4，Constitution L7 要求）
 747→        train_months:  训练期月数（默认 18）
 748→        val_months:    验证期月数（默认 6）
 749→
 750→    Returns:
 751→        WalkForwardReport — 包含每轮结果、pass_all_rounds、max_val_dd
 752→
 753→    Note:
 754→        - WF 是验证步骤，不修改 strategy_weights.json
 755→        - 失败轮次会记录 WARNING 但不抛异常
 756→        - 全部 4 轮通过是进入 paper trading 的前置条件
 757→    """
 758→    today = date.today()
 759→    groups = mb._universe.get_groups()
 760→    if not groups:
 761→        logger.warning("[WalkForward] no groups available — skipping")
 762→        return WalkForwardReport()
 763→
 764→    wf_rounds: list[WalkForwardRound] = []
 765→
 766→    for i in range(rounds):
 767→        round_num = i + 1
 768→        # 计算本轮时间窗口
 769→        # 最后一轮 (i=rounds-1) 的 val_end = today - val_months
 770→        # 前面轮次依次向前推 val_months
 771→        val_end = _add_months(today, -val_months - (rounds - round_num) * val_months)
 772→        val_start = _add_months(val_end, -val_months)
 773→        train_end = val_start
 774→        train_start = _add_months(train_end, -train_months)
 775→
 776→        logger.info(
 777→            f"[WalkForward] Round {round_num}/{rounds}: "
 778→            f"train={train_start}~{train_end}, val={val_start}~{val_end}"
 779→        )
 780→
 781→        # ── 训练期：跑矩阵回测找最优参数（复用 mb._run_group）──
 782→        train_report = MatrixBacktestReport(
 783→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
 784→            backtest_window=f"{train_start.isoformat()} ~ {train_end.isoformat()}",
 785→            groups={},
 786→        )
 787→
 788→        for group_id, symbols in groups.items():
 789→            weights = mb._run_group(
 790→                group_id=group_id,
 791→                symbols=symbols,
 792→                start=train_start,
 793→                end=train_end,
 794→                strategies=strategies,
 795→                param_grids=param_grids,
 796→                report=train_report,
 797→            )
 798→            train_report.groups[group_id] = weights
 799→
 800→        # ── 验证期：用训练期 best params 回测，聚合为整体 portfolio ──
 801→        all_returns: list[pd.Series] = []
 802→        for group_id, symbols in groups.items():
 803→            weights = train_report.groups.get(group_id, [])
 804→            if not weights:
 805→                continue
 806→            group_returns = _backtest_with_params_on_period(
 807→                mb, symbols, weights, val_start, val_end,
 808→            )
 809→            all_returns.extend(group_returns)
 810→
 811→        # 计算整体 portfolio 指标（等权合并所有组的日收益率）
 812→        if not all_returns:
 813→            val_sortino = 0.0
 814→            val_max_dd = 0.0
 815→            logger.warning(
 816→                f"[WalkForward] Round {round_num}: no valid val returns — "
 817→                f"sortino=0, dd=0, passed=True (vacuous)"
 818→            )
 819→        else:
 820→            combined = pd.concat(all_returns, axis=1).mean(axis=1).dropna()
 821→            if len(combined) < 5:
 822→                val_sortino = 0.0
 823→                val_max_dd = 0.0
 824→            else:
 825→                val_sortino = _compute_sortino(combined)
 826→                wrapper = [SingleBacktestResult(
 827→                    symbol="portfolio", strategy="", params={},
 828→                    sharpe=0.0, total_return_pct=0.0, max_drawdown_pct=0.0,
 829→                    win_rate_pct=0.0, total_trades=0, daily_returns=combined,
 830→                )]
 831→                val_max_dd = _portfolio_max_drawdown_from_results(wrapper)
 832→
 833→        passed = val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD
 834→        wf_rounds.append(WalkForwardRound(
 835→            round_num=round_num,
 836→            train_start=train_start,
 837→            train_end=train_end,
 838→            val_start=val_start,
 839→            val_end=val_end,
 840→            val_sortino=val_sortino,
 841→            val_max_dd=val_max_dd,
 842→            passed=passed,
 843→        ))
 844→        logger.info(
 845→            f"[WalkForward] Round {round_num} result: "
 846→            f"sortino={val_sortino:.4f}, dd={val_max_dd:.4f}%, "
 847→            f"passed={passed} (threshold={WALK_FORWARD_VAL_DD_THRESHOLD}%)"
 848→        )
 849→
 850→    report = WalkForwardReport(
 851→        rounds=wf_rounds,
 852→        pass_all_rounds=all(r.passed for r in wf_rounds) if wf_rounds else False,
 853→        max_val_dd=max((r.val_max_dd for r in wf_rounds), default=0.0),
 854→    )
 855→    logger.info(
 856→        f"[WalkForward] done: {len(wf_rounds)} rounds, "
 857→        f"pass_all_rounds={report.pass_all_rounds}, "
 858→        f"max_val_dd={report.max_val_dd:.4f}%"
 859→    )
 860→    return report
 861→
 862→
 863→# ---------------------------------------------------------------------------
 864→# MatrixBacktest 主类
 865→# ---------------------------------------------------------------------------
 866→
 867→class MatrixBacktest:
 868→    """矩阵回测：N 策略 × G 标的组 × 参数网格 → strategy_weights.json。
 869→
 870→    Args:
 871→        store:       MarketDataStore（本地时序库）
 872→        universe:    UniverseManager（提供分组映射）
 873→        years:       回测窗口（默认 5 年）
 874→        init_cash:   初始资金
 875→        fees:        手续费率
 876→        slippage:    滑点率
 877→        top_k:       每组保留 Top-K 策略（默认 2）
 878→    """
 879→
 880→    def __init__(
 881→        self,
 882→        store: MarketDataStore,
 883→        universe: UniverseManager,
 884→        years: int = 5,
 885→        init_cash: float = 100_000.0,
 886→        fees: float = 0.001,
 887→        slippage: float = 0.001,
 888→        top_k: int = 2,
 889→    ) -> None:
 890→        self._store = store
 891→        self._universe = universe
 892→        self._years = years
 893→        self._init_cash = init_cash
 894→        self._fees = fees
 895→        self._slippage = slippage
 896→        self._top_k = top_k
 897→
 898→    def run(
 899→        self,
 900→        strategies: list[str],
 901→        param_grids: dict[str, dict[str, list]],
 902→        output_file: str | Path | None = None,
 903→    ) -> MatrixBacktestReport:
 904→        """执行完整矩阵回测。
 905→
 906→        Args:
 907→            strategies:  策略名称列表，如 ["dual_ma", "rsi"]
 908→            param_grids: 各策略参数网格，如 {"dual_ma": {"fast":[5,10], "slow":[20,30]}}
 909→            output_file: strategy_weights.json 输出路径（None 则不写文件）
 910→
 911→        Returns:
 912→            MatrixBacktestReport
 913→        """
 914→        today = date.today()
 915→        start = today - timedelta(days=self._years * 365)
 916→        window_str = f"{start.isoformat()} ~ {today.isoformat()}"
 917→
 918→        logger.info(
 919→            f"[MatrixBacktest] start={start}, end={today}, "
 920→            f"strategies={strategies}, years={self._years}"
 921→        )
 922→
 923→        # 获取分组（⚠️ 使用历史时点分组，而非当前静态分组）
 924→        # Phase 5 初期简化：用当前分组，但接口已预留历史分组能力
 925→        groups = self._universe.get_groups()
 926→        if not groups:
 927→            logger.warning("[MatrixBacktest] no groups available, abort")
 928→            return MatrixBacktestReport(
 929→                generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
 930→                backtest_window=window_str,
 931→                groups={},
 932→            )
 933→
 934→        report = MatrixBacktestReport(
 935→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
 936→            backtest_window=window_str,
 937→            groups={},
 938→        )
 939→
 940→        for group_id, symbols in groups.items():
 941→            logger.info(
 942→                f"[MatrixBacktest] group={group_id}, symbols={len(symbols)}, "
 943→                f"strategies={strategies}"
 944→            )
 945→
 946→            group_weights = self._run_group(
 947→                group_id=group_id,
 948→                symbols=symbols,
 949→                start=start,
 950→                end=today,
 951→                strategies=strategies,
 952→                param_grids=param_grids,
 953→                report=report,
 954→            )
 955→            report.groups[group_id] = group_weights
 956→
 957→        if output_file is not None:
 958→            self._write_weights(report, output_file)
 959→
 960→        logger.info(
 961→            f"[MatrixBacktest] done: {len(report.groups)} groups, "
 962→            f"warnings={len(report.warnings)}"
 963→        )
 964→        return report
 965→
 966→    def _get_spy_returns(self, start: date, end: date) -> pd.Series | None:
 967→        """获取 SPY 同期日收益率序列，用于计算 alpha（迭代 #9 新增）。
 968→
 969→        从 MarketDataStore 拉取 SPY 日线数据，计算日收益率。
 970→        SPY 不在标的池中，但作为 benchmark 用于 alpha 计算。
 971→
 972→        降级处理：SPY 数据不可用时返回 None（_compute_alpha 会返回 0.0），
 973→        不抛异常，保证回测不因 benchmark 缺失而阻塞。
 974→
 975→        Args:
 976→            start: 回测起始日期
 977→            end:   回测结束日期
 978→
 979→        Returns:
 980→            SPY 日收益率 pd.Series；数据不可用时返回 None
 981→        """
 982→        try:
 983→            spy_bars = self._store.get_bars_multi(["SPY"], start, end)
 984→            spy_df = spy_bars.get("SPY") if spy_bars else None
 985→            if spy_df is None or spy_df.empty:
 986→                logger.warning(
 987→                    "[MatrixBacktest] SPY data unavailable, alpha will degrade to 0.0"
 988→                )
 989→                return None
 990→            spy_close = spy_df["close"].astype(float)
 991→            if len(spy_close) < 2:
 992→                logger.warning(
 993→                    "[MatrixBacktest] SPY data too short, alpha will degrade to 0.0"
 994→                )
 995→                return None
 996→            return spy_close.pct_change().dropna()
 997→        except Exception as e:
 998→            logger.warning(
 999→                f"[MatrixBacktest] SPY benchmark fetch failed: {e} — "
1000→                f"alpha will degrade to 0.0"
1001→            )
1002→            return None
1003→
1004→    def _run_group(
1005→        self,
1006→        group_id: str,
1007→        symbols: list[str],
1008→        start: date,
1009→        end: date,
1010→        strategies: list[str],
1011→        param_grids: dict[str, dict[str, list]],
1012→        report: MatrixBacktestReport,
1013→    ) -> list[dict[str, Any]]:
1014→        """对单个分组执行策略 × 参数网格回测，返回该组的权重配置列表。
1015→
1016→        迭代 #9 变更：
1017→            - per-strategy best params：从 Sharpe 改为 Alpha（vs SPY）
1018→            - top-K 排序：从 Sortino 改为 Alpha
1019→            - 新增 Sortino > 0.5 最低质量门槛（二级过滤，可放宽）
1020→            - ensemble weights：从 Sharpe 改为 Alpha
1021→        迭代 #10 变更：
1022→            - 用 `_backtest_batch` 替代 for-symbol 循环（10-20x 提速）
1023→            - 每组 / 每策略增加进度耗时日志
1024→        """
1025→        import time
1026→
1027→        group_start = time.time()
1028→
1029→        # 1. 读取组内所有标的数据
1030→        data = self._store.get_bars_multi(symbols, start, end)
1031→        if not data:
1032→            logger.warning(f"[MatrixBacktest] {group_id}: no data, skip")
1033→            return []
1034→
1035→        # 迭代 #9：获取 SPY 同期日收益率用于 alpha 计算（一次获取，组内复用）
1036→        spy_returns = self._get_spy_returns(start, end)
1037→
1038→        valid_symbol_count = sum(
1039→            1 for df in data.values() if df is not None and not df.empty and len(df) >= 30
1040→        )
1041→        logger.info(
1042→            f"[MatrixBacktest] {group_id}: start — "
1043→            f"{len(strategies)} strategies × {valid_symbol_count} valid symbols"
1044→        )
1045→
1046→        # 2. 对每个策略 × 每组参数，按 alpha 选最优参数
1047→        group_results: list[tuple[str, dict, list[SingleBacktestResult]]] = []
1048→
1049→        for strategy in strategies:
1050→            strat_start = time.time()
1051→
1052→            # ⚠️ 早期检测未注册策略名（迭代 #1 修复"策略名拼写错误被静默跳过"的 bug）
1053→            # 之前 _backtest_one 内部静默 return None，导致 main.py 误用 "rsi"/"macd"/"bollinger"
1054→            # 简称 6 天未被发现。改为 WARNING 级日志 + continue。
1055→            if strategy not in STRATEGY_REGISTRY:
1056→                logger.warning(
1057→                    f"[MatrixBacktest] {group_id}: strategy '{strategy}' not in "
1058→                    f"STRATEGY_REGISTRY — skipped. "
1059→                    f"Check spelling against @register_strategy decorators. "
1060→                    f"Known: {sorted(STRATEGY_REGISTRY.keys())}"
1061→                )
1062→                continue
1063→            grid = param_grids.get(strategy, {})
1064→            param_combos = list(
1065→                dict(zip(grid.keys(), combo))
1066→                for combo in itertools.product(*grid.values())
1067→            ) if grid else [{}]
1068→
1069→            best_params = None
1070→            best_alpha = float("-inf")
1071→            best_sharpe = 0.0       # 仅用于 GroupBacktestResult 存档
1072→            best_sortino = 0.0      # 仅用于 GroupBacktestResult 存档
1073→            best_results: list[SingleBacktestResult] = []
1074→
1075→            for params in param_combos:
1076→                # 迭代 #10：用 _backtest_batch 一次处理组内所有标的
1077→                # 替代原 for sym in symbols: _backtest_one(...) 的逐标的循环
1078→                results = _backtest_batch(
1079→                    data, strategy, params,
1080→                    self._init_cash, self._fees, self._slippage,
1081→                )
1082→
1083→                if not results:
1084→                    continue
1085→
1086→                # ⚠️ 等权合并日收益率序列，一次性计算所有指标
1087→                # 迭代 #9：复用 combined 计算 sharpe / sortino / alpha
1088→                combined = _combine_daily_returns(results)
1089→                ps = _compute_sharpe(combined)
1090→                pso = _compute_sortino(combined)
1091→                alpha = _compute_alpha(combined, spy_returns)
1092→
1093→                # 迭代 #9：per-strategy best params 用 alpha 选（替代 Sharpe）
1094→                if alpha > best_alpha:
1095→                    best_alpha = alpha
1096→                    best_sharpe = ps
1097→                    best_sortino = pso
1098→                    best_params = params
1099→                    best_results = results
1100→
1101→            if best_params is not None and best_results:
1102→                group_results.append((strategy, best_params, best_results))
1103→                report.group_results.append(GroupBacktestResult(
1104→                    group_id=group_id,
1105→                    strategy=strategy,
1106→                    params=best_params,
1107→                    portfolio_sharpe=best_sharpe,
1108→                    avg_total_return_pct=_safe_mean(
1109→                        [r.total_return_pct for r in best_results]
1110→                    ),
1111→                    avg_max_drawdown_pct=_safe_mean(
1112→                        [r.max_drawdown_pct for r in best_results]
1113→                    ),
1114→                    avg_win_rate_pct=_safe_mean(
1115→                        [r.win_rate_pct for r in best_results]
1116→                    ),
1117→                    symbol_count=len(best_results),
1118→                    portfolio_sortino=best_sortino,
1119→                    portfolio_max_drawdown=_portfolio_max_drawdown_from_results(
1120→                        best_results
1121→                    ),
1122→                    backtest_alpha=best_alpha,
1123→                ))
1124→
1125→            logger.info(
1126→                f"[MatrixBacktest] {group_id}: {strategy} done in "
1127→                f"{time.time() - strat_start:.1f}s "
1128→                f"({len(param_combos)} param combos × {valid_symbol_count} symbols)"
1129→            )
1130→
1131→        if not group_results:
1132→            logger.warning(
1133→                f"[MatrixBacktest] {group_id}: no valid results "
1134→                f"(elapsed {time.time() - group_start:.1f}s)"
1135→            )
1136→            return []
1137→
1138→        # 3. 迭代 #9：DD 硬约束 + Sortino 门槛 + Alpha 排序选 Top-K
1139→        #    Constitution L1: portfolio DD ≤ 20% 是硬约束（保留）
1140→        #    新增：Sortino > 0.5 最低质量门槛（可放宽）
1141→        #    变更：排序指标从 Sortino 改为 Alpha
1142→        #
1143→        #    三级过滤策略：
1144→        #      Tier 1: DD ≤ 20% AND Sortino > 0.5 → Alpha 降序
1145→        #      Tier 2 (fallback): Tier 1 为空 → 仅 DD ≤ 20% → Alpha 降序
1146→        #      Tier 3 (fallback): Tier 2 为空 → 按 DD 升序，标记 dd_constrained=True
1147→        candidates: list[
1148→            tuple[str, dict, list[SingleBacktestResult], float, float, float]
1149→        ] = []
1150→        for (strategy, params, results) in group_results:
1151→            pso = _portfolio_sortino_from_results(results)
1152→            pdd = _portfolio_max_drawdown_from_results(results)
1153→            # 复用 _combine_daily_returns 计算 alpha（与 per-strategy 选择一致）
1154→            alpha = _compute_alpha(_combine_daily_returns(results), spy_returns)
1155→            candidates.append((strategy, params, results, pso, pdd, alpha))
1156→
1157→        # Tier 1: DD ≤ 20% AND Sortino > 0.5
1158→        compliant = [
1159→            c for c in candidates
1160→            if c[4] <= MAX_PORTFOLIO_DRAWDOWN_PCT and c[3] > MIN_SORTINO_THRESHOLD
1161→        ]
1162→        if compliant:
1163→            # Tier 1 命中：按 Alpha 降序取 top-K
1164→            ranked = sorted(compliant, key=lambda x: x[5], reverse=True)
1165→            dd_constrained = False
1166→            logger.info(
1167→                f"[MatrixBacktest] {group_id}: DD + Sortino filter passed — "
1168→                f"{len(compliant)}/{len(candidates)} candidates compliant "
1169→                f"(DD <= {MAX_PORTFOLIO_DRAWDOWN_PCT}% AND Sortino > {MIN_SORTINO_THRESHOLD})"
1170→            )
1171→        else:
1172→            # Tier 2: 放宽 Sortino 门槛，仅保留 DD 约束
1173→            dd_compliant = [
1174→                c for c in candidates if c[4] <= MAX_PORTFOLIO_DRAWDOWN_PCT
1175→            ]
1176→            if dd_compliant:
1177→                # Tier 2 命中：按 Alpha 降序取 top-K（dd_constrained 仍为 False）
1178→                ranked = sorted(dd_compliant, key=lambda x: x[5], reverse=True)
1179→                dd_constrained = False
1180→                logger.warning(
1181→                    f"[MatrixBacktest] {group_id}: Sortino filter relaxed — "
1182→                    f"no candidate passed Sortino > {MIN_SORTINO_THRESHOLD}. "
1183→                    f"Fallback to DD-only filter: "
1184→                    f"{len(dd_compliant)}/{len(candidates)} candidates DD-compliant."
1185→                )
1186→            else:
1187→                # Tier 3: 无 DD 合规候选 → 按 DD 升序，标记 dd_constrained
1188→                # （结构性问题，如 NDX_high_vol 全部 > 20%）
1189→                ranked = sorted(candidates, key=lambda x: x[4])
1190→                dd_constrained = True
1191→                logger.warning(
1192→                    f"[MatrixBacktest] {group_id}: NO compliant candidates "
1193→                    f"(all {len(candidates)} exceed DD={MAX_PORTFOLIO_DRAWDOWN_PCT}%). "
1194→                    f"Fallback: selected top-{self._top_k} by lowest DD. "
1195→                    f"This group is marked dd_constrained=True — "
1196→                    f"review whether to drop the group or accept the risk."
1197→                )
1198→                report.warnings.append(
1199→                    f"{group_id}: dd_constrained=True "
1200→                    f"(min DD={ranked[0][4]:.2f}% > {MAX_PORTFOLIO_DRAWDOWN_PCT}%)"
1201→                )
1202→
1203→        top_results = ranked[: self._top_k]
1204→
1205→        # 把 dd_constrained 标记同步到 report.group_results 中对应组的条目
1206→        for gr in report.group_results:
1207→            if gr.group_id == group_id:
1208→                gr.dd_constrained = dd_constrained
1209→
1210→        # 4. 优化 ensemble 权重（单点离散值加权投票语义，迭代 #9 改用 alpha）
1211→        weighted = _optimize_ensemble_weights(
1212→            [(s, p, r) for (s, p, r, _, _, _) in top_results],
1213→            spy_returns=spy_returns,
1214→        )
1215→
1216→        # 5. 构建权重配置列表
1217→        weights_list = []
1218→        for strategy, params, weight in weighted:
1219→            # 找到对应的 GroupBacktestResult
1220→            gr = next(
1221→                (r for r in report.group_results
1222→                 if r.group_id == group_id and r.strategy == strategy),
1223→                None,
1224→            )
1225→            # 迭代 #4：新增 backtest_dd_status 字段（'pass' / 'dd_constrained'）
1226→            # 作为风险 metadata 标记，与 dd_constrained bool 同义但更可读
1227→            backtest_dd_status = "dd_constrained" if dd_constrained else "pass"
1228→            weights_list.append({
1229→                "strategy": strategy,
1230→                "params": params,
1231→                "weight": round(weight, 4),
1232→                "backtest_sharpe": round(gr.portfolio_sharpe if gr else 0.0, 4),
1233→                "backtest_sortino": round(gr.portfolio_sortino if gr else 0.0, 4),
1234→                "backtest_max_drawdown": round(gr.portfolio_max_drawdown if gr else 0.0, 4),
1235→                "backtest_win_rate": round(gr.avg_win_rate_pct / 100 if gr else 0.5, 4),
1236→                # 迭代 #9：新增 backtest_alpha 字段（vs SPY 的超额收益百分数）
1237→                # 下游 PortfolioBacktester 可读此字段验证 alpha 一致性
1238→                "backtest_alpha": round(gr.backtest_alpha if gr else 0.0, 4),
1239→                # 迭代 #3：标记该组是否用了 DD fallback（无合规候选）
1240→                # 同组所有策略条目共享同一 dd_constrained 值
1241→                "dd_constrained": dd_constrained,
1242→                # 迭代 #4：backtest_dd_status — 风险 metadata 字段
1243→                # 'pass' = 该组有合规候选（DD ≤ 20%）
1244→                # 'dd_constrained' = fallback 触发（无合规候选，按最低 DD 取 top-K）
1245→                # 下游消费方（PortfolioBacktester / 风控观测）可读此字段判断
1246→                # 该组权重的可靠性，作为风险信号标记
1247→                "backtest_dd_status": backtest_dd_status,
1248→            })
1249→
1250→        logger.info(
1251→            f"[MatrixBacktest] {group_id}: all strategies done in "
1252→            f"{time.time() - group_start:.1f}s "
1253→            f"(top-{self._top_k} selected, dd_constrained={dd_constrained})"
1254→        )
1255→
1256→        return weights_list
1257→
1258→    def _write_weights(
1259→        self, report: MatrixBacktestReport, output_file: str | Path
1260→    ) -> None:
1261→        """将矩阵回测结果写入 strategy_weights.json。"""
1262→        output_file = Path(output_file)
1263→        output_file.parent.mkdir(parents=True, exist_ok=True)
1264→
1265→        data = {
1266→            "_meta": {
1267→                "generated_at": report.generated_at,
1268→                "backtest_window": report.backtest_window,
1269→                "reoptimize_freq": "monthly",
1270→                "survivorship_bias_warning": (
1271→                    "使用当前成分股回测，S&P 500 5年成分变动约100只(~20%)，"
1272→                    "均值回归组(SPX_low_vol)结果可能系统性偏高"
1273→                ),
1274→            },
1275→            "groups": report.groups,
1276→        }
1277→
1278→        with open(output_file, "w", encoding="utf-8") as f:
1279→            json.dump(data, f, indent=2, ensure_ascii=False)
1280→
1281→        logger.info(f"[MatrixBacktest] weights saved to {output_file}")
1282→
---
Now
---
 let
---
 me
---
 look
---
 at
---
 the
---
 existing
---
 tests
---
 for
---
 matrix
---
_back
---
test
---
 to
---
 understand
---
 the
---
 test
---
 patterns
---
.
---
现在
---
让我
---
查看
---
现有的
---
测试
---
以
---
了解
---
模式
---
，
---
并
---
检查
---
 v
---
bt
---
 API
---
。
---
{"command":"ls /Users/rickouyang/Github/trade-tools/mytrader/tests/ | grep -E \"(matrix|batch|backtest)\" | head -20","description":"List matrix/batch backtest test files"}
---
List matrix/batch backtest test files
---
Command: ls /Users/rickouyang/Github/trade-tools/mytrader/tests/ | grep -E "(matrix|batch|backtest)" | head -20
Stdout: test_backtest.py
test_batch_backtest.py
test_matrix_backtest.py
test_portfolio_backtest.py
test_strategy_matrix_ranker.py

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/tests/test_batch_backtest.py"}
---
   1→"""vectorbt Batch Backtest 数值一致性测试（迭代 #10 新增）。
   2→
   3→验证 `_backtest_batch()` 与 `_backtest_one()` 在相同输入下产出
   4→数值一致的结果，确保批量化重构不改变策略选择 / Alpha 排序 / DD 过滤等下游逻辑。
   5→
   6→测试范围（spec §5）：
   7→    1. 所有 5 个策略 batch vs single 数值一致性
   8→    2. 不同参数组合（至少 2 组参数 per 策略）
   9→    3. 边界场景：数据不足 / 全空 / 单标的 / 日期不对齐
  10→    4. 进度日志验证（_run_group 路径，集成测试）
  11→
  12→数值一致性判定：
  13→    - daily_returns: np.allclose(rtol=1e-6, atol=1e-8)
  14→    - sharpe / total_return / max_drawdown / win_rate / total_trades / sortino:
  15→      允许 1e-4 ~ 1e-2 浮点误差（vbt 内部计算路径差异）
  16→"""
  17→
  18→from __future__ import annotations
  19→
  20→from datetime import date
  21→from unittest.mock import MagicMock
  22→
  23→import numpy as np
  24→import pandas as pd
  25→import pytest
  26→
  27→from mytrader.backtest.matrix_backtest import (
  28→    MatrixBacktest,
  29→    _backtest_batch,
  30→    _backtest_one,
  31→    SingleBacktestResult,
  32→)
  33→
  34→
  35→# ---------------------------------------------------------------------------
  36→# Test data generators
  37→# ---------------------------------------------------------------------------
  38→
  39→def _make_ohlcv(
  40→    n: int = 300,
  41→    trend: str = "up",
  42→    seed: int | None = None,
  43→    start: str = "2021-01-01",
  44→) -> pd.DataFrame:
  45→    """生成测试 OHLCV 数据。
  46→
  47→    Args:
  48→        n:      bar 数量
  49→        trend:  "up" / "down" / "random"
  50→        seed:   随机种子（trend=random 时使用）
  51→        start:  起始日期
  52→    """
  53→    idx = pd.date_range(start, periods=n, freq="B")
  54→    if trend == "up":
  55→        close = np.array([100.0 + i * 0.1 for i in range(n)])
  56→    elif trend == "down":
  57→        close = np.array([100.0 - i * 0.05 for i in range(n)])
  58→    elif trend == "random":
  59→        rng = np.random.default_rng(seed if seed is not None else 42)
  60→        # 带均值回归的随机游走，触发策略信号
  61→        steps = rng.normal(0, 0.5, n)
  62→        close = np.cumsum(np.concatenate([[100.0], steps]))[1:]
  63→    else:
  64→        raise ValueError(f"unknown trend: {trend}")
  65→
  66→    return pd.DataFrame(
  67→        {
  68→            "open":   close - 0.5,
  69→            "high":   close + 1.0,
  70→            "low":    close - 1.0,
  71→            "close":  close,
  72→            "volume": [1_000_000] * n,
  73→        },
  74→        index=idx,
  75→    )
  76→
  77→
  78→def _make_multi_symbol_data(
  79→    symbols: list[str],
  80→    n: int = 300,
  81→    trend: str = "up",
  82→    seed: int = 42,
  83→) -> dict[str, pd.DataFrame]:
  84→    """生成多标的 OHLCV 数据字典。
  85→
  86→    每个标的数据独立生成，但起始日期对齐（便于数值一致性验证）。
  87→    """
  88→    return {
  89→        sym: _make_ohlcv(n=n, trend=trend, seed=seed + i)
  90→        for i, sym in enumerate(symbols)
  91→    }
  92→
  93→
  94→# ---------------------------------------------------------------------------
  95→# 数值一致性辅助
  96→# ---------------------------------------------------------------------------
  97→
  98→def _assert_results_match(
  99→    old: SingleBacktestResult | None,
 100→    new: SingleBacktestResult | None,
 101→    *,
 102→    rtol: float = 1e-6,
 103→    atol: float = 1e-8,
 104→    stats_rtol: float = 1e-4,
 105→    stats_atol: float = 1e-2,
 106→    context: str = "",
 107→) -> None:
 108→    """对比 _backtest_one 与 _backtest_batch 的 SingleBacktestResult。
 109→
 110→    Args:
 111→        old: _backtest_one 返回值（可能为 None）
 112→        new: _backtest_batch 返回的列表中的某一项（可能为 None）
 113→        rtol/atol: daily_returns 的 np.allclose 容差
 114→        stats_rtol/stats_atol: stats 字段容差（vbt 计算路径差异，允许稍宽）
 115→        context: 错误消息上下文
 116→    """
 117→    msg = lambda s: f"{context}: {s}" if context else s
 118→
 119→    # 两者都 None：一致
 120→    if old is None and new is None:
 121→        return
 122→    # 一方 None：不一致
 123→    if old is None or new is None:
 124→        pytest.fail(msg(f"one is None, other is not (old={old}, new={new})"))
 125→
 126→    assert old.symbol == new.symbol, msg("symbol mismatch")
 127→    assert old.strategy == new.strategy, msg("strategy mismatch")
 128→
 129→    # daily_returns: 严格一致
 130→    assert not old.daily_returns.empty, msg("old daily_returns is empty")
 131→    assert not new.daily_returns.empty, msg("new daily_returns is empty")
 132→    # 对齐索引后比较（vbt 列提取可能返回不同的 index name）
 133→    old_dr = old.daily_returns.reset_index(drop=True)
 134→    new_dr = new.daily_returns.reset_index(drop=True)
 135→    assert len(old_dr) == len(new_dr), msg(
 136→        f"daily_returns length mismatch: old={len(old_dr)}, new={len(new_dr)}"
 137→    )
 138→    np.testing.assert_allclose(
 139→        old_dr.values,
 140→        new_dr.values,
 141→        rtol=rtol, atol=atol,
 142→        err_msg=msg("daily_returns mismatch"),
 143→    )
 144→
 145→    # stats 字段：允许浮点误差
 146→    assert abs(old.sharpe - new.sharpe) < stats_rtol + stats_atol * max(
 147→        abs(old.sharpe), 1.0
 148→    ), msg(f"sharpe mismatch: old={old.sharpe}, new={new.sharpe}")
 149→    assert abs(old.total_return_pct - new.total_return_pct) < stats_atol, msg(
 150→        f"total_return_pct mismatch: old={old.total_return_pct}, new={new.total_return_pct}"
 151→    )
 152→    assert abs(old.max_drawdown_pct - new.max_drawdown_pct) < stats_atol, msg(
 153→        f"max_drawdown_pct mismatch: old={old.max_drawdown_pct}, new={new.max_drawdown_pct}"
 154→    )
 155→    assert abs(old.win_rate_pct - new.win_rate_pct) < stats_atol, msg(
 156→        f"win_rate_pct mismatch: old={old.win_rate_pct}, new={new.win_rate_pct}"
 157→    )
 158→    assert old.total_trades == new.total_trades, msg(
 159→        f"total_trades mismatch: old={old.total_trades}, new={new.total_trades}"
 160→    )
 161→    # sortino 从 daily_returns 派生，应严格一致
 162→    assert abs(old.sortino - new.sortino) < 1e-6, msg(
 163→        f"sortino mismatch: old={old.sortino}, new={new.sortino}"
 164→    )
 165→
 166→
 167→# ---------------------------------------------------------------------------
 168→# Test 1-5: 各策略 batch vs single 数值一致性
 169→# ---------------------------------------------------------------------------
 170→
 171→# 测试矩阵：(strategy_name, [param_combos])
 172→_STRATEGY_PARAM_CASES = [
 173→    ("dual_ma", [
 174→        {"fast": 5, "slow": 20},
 175→        {"fast": 10, "slow": 30},
 176→    ]),
 177→    ("rsi_mean_revert", [
 178→        {"period": 14, "oversold": 30, "overbought": 70},
 179→        {"period": 7, "oversold": 25, "overbought": 75},
 180→    ]),
 181→    ("rsi_trend_filter", [
 182→        {"rsi_period": 14, "oversold": 30, "overbought": 70, "trend_period": 50},
 183→        {"rsi_period": 7, "oversold": 25, "overbought": 75, "trend_period": 50},
 184→    ]),
 185→    ("macd_cross", [
 186→        {"fast": 12, "slow": 26, "signal_period": 9},
 187→        {"fast": 5, "slow": 20, "signal_period": 5},
 188→    ]),
 189→    ("bollinger_band", [
 190→        {"period": 20, "std_dev": 2.0},
 191→        {"period": 10, "std_dev": 1.5},
 192→    ]),
 193→]
 194→
 195→
 196→# 展开为扁平的 (strategy_name, params) 列表 + 自定义 ID
 197→_EXPANDED_CASES: list[tuple[str, dict]] = []
 198→_EXPANSED_IDS: list[str] = []
 199→for _s, _combos in _STRATEGY_PARAM_CASES:
 200→    for _i, _p in enumerate(_combos):
 201→        _EXPANDED_CASES.append((_s, _p))
 202→        _EXPANSED_IDS.append(f"{_s}-{_i}")
 203→
 204→
 205→@pytest.mark.parametrize(
 206→    "strategy_name, params",
 207→    _EXPANDED_CASES,
 208→    ids=_EXPANSED_IDS,
 209→)
 210→class TestBatchConsistencyAllStrategies:
 211→    """5 个策略 × 2 参数组合的 batch vs single 一致性测试。"""
 212→
 213→    def test_batch_matches_single_all_symbols(
 214→        self, strategy_name: str, params: dict
 215→    ) -> None:
 216→        """批量回测与逐标的回测在每个标的上数值一致。"""
 217→        # 3 个标的 + 随机走势（触发更多策略信号，覆盖更全）
 218→        data = _make_multi_symbol_data(
 219→            ["AAA", "BBB", "CCC"], n=300, trend="random", seed=123
 220→        )
 221→
 222→        # 旧方式：逐标的回测
 223→        old_results: dict[str, SingleBacktestResult | None] = {}
 224→        for sym, df in data.items():
 225→            df = df.copy()
 226→            df.index.name = sym
 227→            old_results[sym] = _backtest_one(df, strategy_name, params)
 228→
 229→        # 新方式：批量回测
 230→        new_results_list = _backtest_batch(data, strategy_name, params)
 231→        new_results = {r.symbol: r for r in new_results_list}
 232→
 233→        # 每个标的都应一致（_backtest_one 返回 None 的标的在 batch 中不出现）
 234→        for sym, old_r in old_results.items():
 235→            if old_r is None:
 236→                assert sym not in new_results, (
 237→                    f"{strategy_name}/{params} {sym}: _backtest_one returned None "
 238→                    f"but _backtest_batch returned a result"
 239→                )
 240→                continue
 241→            assert sym in new_results, (
 242→                f"{strategy_name}/{params} {sym}: _backtest_one returned a result "
 243→                f"but _backtest_batch dropped it"
 244→            )
 245→            _assert_results_match(
 246→                old_r, new_results[sym],
 247→                context=f"{strategy_name}/{params} {sym}",
 248→            )
 249→
 250→
 251→# ---------------------------------------------------------------------------
 252→# Test 6: 数据不足的标的被跳过
 253→# ---------------------------------------------------------------------------
 254→
 255→class TestBatchEdgeCases:
 256→    """批量化回测的边界场景测试。"""
 257→
 258→    def test_batch_skips_short_data(self) -> None:
 259→        """数据 < 30 天的标的应被跳过（不返回结果）。"""
 260→        # 一个长数据 + 一个短数据
 261→        data = {
 262→            "LONG": _make_ohlcv(300, trend="up"),
 263→            "SHORT": _make_ohlcv(10, trend="up"),
 264→        }
 265→        results = _backtest_batch(data, "dual_ma", {"fast": 5, "slow": 20})
 266→        symbols = [r.symbol for r in results]
 267→        assert "LONG" in symbols
 268→        assert "SHORT" not in symbols, (
 269→            "数据 < 30 天的标的应被跳过，但仍出现在结果中"
 270→        )
 271→
 272→    def test_batch_skips_empty_df(self) -> None:
 273→        """空 DataFrame 的标的应被跳过。"""
 274→        data = {
 275→            "GOOD": _make_ohlcv(300, trend="up"),
 276→            "EMPTY": pd.DataFrame(),
 277→        }
 278→        results = _backtest_batch(data, "dual_ma", {"fast": 5, "slow": 20})
 279→        symbols = [r.symbol for r in results]
 280→        assert "GOOD" in symbols
 281→        assert "EMPTY" not in symbols
 282→
 283→    def test_batch_single_symbol(self) -> None:
 284→        """只有 1 个标的时批量回测应正常工作。"""
 285→        data = {"SOLO": _make_ohlcv(300, trend="up")}
 286→        # 给一个随机走势的单标的，确保有信号
 287→        data = {"SOLO": _make_ohlcv(300, trend="random", seed=7)}
 288→        results = _backtest_batch(data, "dual_ma", {"fast": 5, "slow": 20})
 289→        assert len(results) == 1
 290→        assert results[0].symbol == "SOLO"
 291→        assert not results[0].daily_returns.empty
 292→
 293→    def test_batch_single_symbol_matches_single(self) -> None:
 294→        """单标的时 batch vs single 一致性。"""
 295→        df = _make_ohlcv(300, trend="random", seed=7)
 296→        df.index.name = "SOLO"
 297→        old = _backtest_one(df, "dual_ma", {"fast": 5, "slow": 20})
 298→        new_list = _backtest_batch(
 299→            {"SOLO": df}, "dual_ma", {"fast": 5, "slow": 20}
 300→        )
 301→        assert len(new_list) == 1
 302→        _assert_results_match(old, new_list[0], context="single-symbol")
 303→
 304→    def test_batch_misaligned_dates(self) -> None:
 305→        """不同起始日期的标的：批量回测应正常完成（不抛异常）。
 306→
 307→        数值一致性在严格对齐的日期下成立；对错位日期，
 308→        batch 与 single 的 stats 可能因 NaN 填充方式不同而有细微差异，
 309→        但 daily_returns 在有效区间内应一致。
 310→        """
 311→        # 标的 A 从 2021-01-01 起 300 bar
 312→        # 标的 B 从 2021-06-01 起 300 bar（晚 5 个月）
 313→        df_a = _make_ohlcv(300, trend="up", start="2021-01-01")
 314→        df_b = _make_ohlcv(300, trend="up", start="2021-06-01")
 315→        data = {"MISA": df_a, "MISB": df_b}
 316→
 317→        # 不应抛异常
 318→        results = _backtest_batch(data, "dual_ma", {"fast": 5, "slow": 20})
 319→        assert len(results) == 2
 320→        symbols = [r.symbol for r in results]
 321→        assert set(symbols) == {"MISA", "MISB"}
 322→        for r in results:
 323→            assert not r.daily_returns.empty
 324→
 325→    def test_batch_empty_data(self) -> None:
 326→        """全空���据返回空列表。"""
 327→        results = _backtest_batch({}, "dual_ma", {"fast": 5, "slow": 20})
 328→        assert results == []
 329→
 330→    def test_batch_unknown_strategy(self) -> None:
 331→        """未注册策略返回空列表（不抛异常）。"""
 332→        data = {"AAA": _make_ohlcv(300)}
 333→        results = _backtest_batch(data, "nonexistent_xyz", {})
 334→        assert results == []
 335→
 336→    def test_batch_no_open_column(self) -> None:
 337→        """DataFrame 无 open 列时也能正常回测（降级为 close 执行）。"""
 338→        df = _make_ohlcv(300, trend="random", seed=42).drop(columns=["open"])
 339→        data = {"NOOPEN": df}
 340→        results = _backtest_batch(data, "dual_ma", {"fast": 5, "slow": 20})
 341→        assert len(results) == 1
 342→        assert results[0].symbol == "NOOPEN"
 343→
 344→    def test_batch_preserves_symbol_order(self) -> None:
 345→        """结果列表的 symbol 顺序应与 signal_matrix.columns 顺序一致
 346→        （即与输入 dict 的插入顺序一致，Python 3.7+ 保证）。"""
 347→        data = {
 348→            "ZEBRA": _make_ohlcv(300, trend="up"),
 349→            "ALPHA": _make_ohlcv(300, trend="up"),
 350→            "MIKE":  _make_ohlcv(300, trend="up"),
 351→        }
 352→        results = _backtest_batch(data, "dual_ma", {"fast": 5, "slow": 20})
 353→        symbols = [r.symbol for r in results]
 354→        # 顺序应与输入 dict 一致
 355→        assert symbols == ["ZEBRA", "ALPHA", "MIKE"]
 356→
 357→
 358→# ---------------------------------------------------------------------------
 359→# Test: _backtest_batch 输出格式与 _backtest_one 一致
 360→# ---------------------------------------------------------------------------
 361→
 362→class TestBatchOutputFormat:
 363→    """验证 _backtest_batch 输出的 SingleBacktestResult 字段完整。"""
 364→
 365→    def test_result_fields_populated(self) -> None:
 366→        """SingleBacktestResult 所有字段都被正确填充（无 NaN）。"""
 367→        data = _make_multi_symbol_data(
 368→            ["AAA", "BBB"], n=300, trend="random", seed=99
 369→        )
 370→        results = _backtest_batch(data, "rsi_mean_revert",
 371→                                  {"period": 14, "oversold": 30, "overbought": 70})
 372→        assert len(results) == 2
 373→        for r in results:
 374→            assert isinstance(r, SingleBacktestResult)
 375→            assert r.symbol in ["AAA", "BBB"]
 376→            assert r.strategy == "rsi_mean_revert"
 377→            assert r.params == {"period": 14, "oversold": 30, "overbought": 70}
 378→            assert isinstance(r.sharpe, float)
 379→            assert isinstance(r.total_return_pct, float)
 380→            assert isinstance(r.max_drawdown_pct, float)
 381→            assert isinstance(r.win_rate_pct, float)
 382→            assert isinstance(r.total_trades, int)
 383→            assert isinstance(r.sortino, float)
 384→            assert not r.daily_returns.empty
 385→            # 所有数值字段都应是有限值（_safe_float 已处理 NaN）
 386→            for v in [r.sharpe, r.total_return_pct, r.max_drawdown_pct,
 387→                      r.win_rate_pct, r.sortino]:
 388→                assert np.isfinite(v), f"{r.symbol}: 字段值非有限: {v}"
 389→
 390→    def test_batch_results_are_independent(self) -> None:
 391→        """不同标的的 daily_returns 应独立（不共享索引/引用）。"""
 392→        data = _make_multi_symbol_data(
 393→            ["AAA", "BBB"], n=300, trend="random", seed=55
 394→        )
 395→        results = _backtest_batch(data, "dual_ma", {"fast": 5, "slow": 20})
 396→        assert len(results) == 2
 397→        # 修改一个不应影响另一个
 398→        r0_orig = results[0].daily_returns.iloc[0]
 399→        r1_orig = results[1].daily_returns.iloc[0]
 400→        # 两个标的的 daily_returns 应不同（不同数据）
 401→        # 注：相同 trend+seed 的数据生成相同走势；这里 seed 不同
 402→        assert r0_orig != r1_orig or len(results[0].daily_returns) > 0
 403→
 404→
 405→# ---------------------------------------------------------------------------
 406→# Test: _run_group 集成（进度日志 + batch 路径）
 407→# ---------------------------------------------------------------------------
 408→
 409→def _make_mock_store(data_by_symbol: dict[str, pd.DataFrame]) -> MagicMock:
 410→    """构造一个 Mock MarketDataStore，get_bars_multi 返回指定数据。"""
 411→    store = MagicMock()
 412→    def get_bars_multi(symbols, start, end, timeframe="1d"):
 413→        return {s: data_by_symbol[s] for s in symbols if s in data_by_symbol}
 414→    store.get_bars_multi.side_effect = get_bars_multi
 415→    return store
 416→
 417→
 418→def _make_mock_universe(groups: dict[str, list[str]]) -> MagicMock:
 419→    """构造一个 Mock UniverseManager，get_groups 返回指定分组。"""
 420→    universe = MagicMock()
 421→    universe.get_groups.return_value = groups
 422→    return universe
 423→
 424→
 425→class TestRunGroupBatchIntegration:
 426→    """验证 _run_group 使用 _backtest_batch 后仍产出正确结果。"""
 427→
 428→    def test_run_group_still_produces_weights(self) -> None:
 429→        """_run_group 使用 batch 后仍产出非空权重列表。"""
 430→        data = _make_multi_symbol_data(
 431→            ["AAPL", "MSFT"], n=300, trend="random", seed=11
 432→        )
 433→        store = _make_mock_store(data)
 434→        # _get_spy_returns 会被调用，返回 None 即可（alpha 退化为 0）
 435→        universe = _make_mock_universe({"TEST_GROUP": ["AAPL", "MSFT"]})
 436→
 437→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
 438→        from mytrader.backtest.matrix_backtest import MatrixBacktestReport
 439→        report = MatrixBacktestReport(
 440→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
 441→            backtest_window="2021-01-01 ~ 2022-01-01",
 442→            groups={},
 443→        )
 444→
 445→        weights = mb._run_group(
 446→            group_id="TEST_GROUP",
 447→            symbols=["AAPL", "MSFT"],
 448→            start=date(2021, 1, 1),
 449→            end=date(2022, 1, 1),
 450→            strategies=["dual_ma"],
 451→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 452→            report=report,
 453→        )
 454→        assert len(weights) >= 1
 455→        assert all("strategy" in w for w in weights)
 456→        assert all("weight" in w for w in weights)
 457→
 458→    def test_run_group_progress_logging(self) -> None:
 459→        """_run_group 应输出包含耗时的进度日志。"""
 460→        # loguru 不通过标准 logging 传播，需用 logger.add 捕获
 461→        from loguru import logger
 462→
 463→        data = _make_multi_symbol_data(
 464→            ["AAPL", "MSFT"], n=300, trend="random", seed=22
 465→        )
 466→        store = _make_mock_store(data)
 467→        universe = _make_mock_universe({"TEST_GROUP": ["AAPL", "MSFT"]})
 468→
 469→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
 470→        from mytrader.backtest.matrix_backtest import MatrixBacktestReport
 471→        report = MatrixBacktestReport(
 472→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
 473→            backtest_window="2021-01-01 ~ 2022-01-01",
 474→            groups={},
 475→        )
 476→
 477→        msgs: list[str] = []
 478→        handler_id = logger.add(lambda m: msgs.append(str(m)), level="INFO")
 479→        try:
 480→            mb._run_group(
 481→                group_id="TEST_GROUP",
 482→                symbols=["AAPL", "MSFT"],
 483→                start=date(2021, 1, 1),
 484→                end=date(2022, 1, 1),
 485→                strategies=["dual_ma"],
 486→                param_grids={"dual_ma": {"fast": [5, 10], "slow": [20, 30]}},
 487→                report=report,
 488→            )
 489→        finally:
 490→            logger.remove(handler_id)
 491→
 492→        # 应包含 "MatrixBacktest" 日志
 493→        all_logs = " ".join(msgs)
 494→        assert "MatrixBacktest" in all_logs, (
 495→            f"未找到 MatrixBacktest 日志：{all_logs}"
 496→        )
 497→        # 应有进度日志（"done" 关键字，spec §4.3 要求）
 498→        assert "done" in all_logs, (
 499→            f"未找到进度完成日志（'done'）：{all_logs}"
 500→        )
 501→        # 应有耗时信息（如 "0.Xs"）
 502→        assert any("s " in m or "s)" in m for m in msgs), (
 503→            f"日志未包含耗时信息：{msgs}"
 504→        )
 505→
 506→
 507→# ---------------------------------------------------------------------------
 508→# Test: Walk-Forward 路径使用 batch
 509→# ---------------------------------------------------------------------------
 510→
 511→class TestWalkForwardBatchIntegration:
 512→    """验证 Walk-Forward 的 _backtest_with_params_on_period 使用 batch。"""
 513→
 514→    def test_walk_forward_returns_valid_report(self) -> None:
 515→        """Walk-Forward 4 轮后产出有效报告（不抛异常）。"""
 516→        from mytrader.backtest.matrix_backtest import run_walk_forward
 517→
 518→        data = _make_multi_symbol_data(
 519→            ["AAPL", "MSFT"], n=500, trend="random", seed=33
 520→        )
 521→        store = _make_mock_store(data)
 522→        universe = _make_mock_universe({"TEST_GROUP": ["AAPL", "MSFT"]})
 523→
 524→        mb = MatrixBacktest(store=store, universe=universe, years=2, top_k=2)
 525→        report = run_walk_forward(
 526→            mb,
 527→            strategies=["dual_ma"],
 528→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 529→            rounds=2,
 530→            train_months=6,
 531→            val_months=3,
 532→        )
 533→        assert len(report.rounds) == 2
 534→        # 每轮都应有 sortino 和 max_dd 数值（可能为 0，但不应为 None）
 535→        for r in report.rounds:
 536→            assert isinstance(r.val_sortino, float)
 537→            assert isinstance(r.val_max_dd, float)
 538→            assert isinstance(r.passed, bool)
 539→
---
   1→"""vectorbt Batch Backtest 数值一致性测试（迭代 #10 新增）。
   2→
   3→验证 `_backtest_batch()` 与 `_backtest_one()` 在相同输入下产出
   4→数值一致的结果，确保批量化重构不改变策略选择 / Alpha 排序 / DD 过滤等下游逻辑。
   5→
   6→测试范围（spec §5）：
   7→    1. 所有 5 个策略 batch vs single 数值一致性
   8→    2. 不同参数组合（至少 2 组参数 per 策略）
   9→    3. 边界场景：数据不足 / 全空 / 单标的 / 日期不对齐
  10→    4. 进度日志验证（_run_group 路径，集成测试）
  11→
  12→数值一致性判定：
  13→    - daily_returns: np.allclose(rtol=1e-6, atol=1e-8)
  14→    - sharpe / total_return / max_drawdown / win_rate / total_trades / sortino:
  15→      允许 1e-4 ~ 1e-2 浮点误差（vbt 内部计算路径差异）
  16→"""
  17→
  18→from __future__ import annotations
  19→
  20→from datetime import date
  21→from unittest.mock import MagicMock
  22→
  23→import numpy as np
  24→import pandas as pd
  25→import pytest
  26→
  27→from mytrader.backtest.matrix_backtest import (
  28→    MatrixBacktest,
  29→    _backtest_batch,
  30→    _backtest_one,
  31→    SingleBacktestResult,
  32→)
  33→
  34→
  35→# ---------------------------------------------------------------------------
  36→# Test data generators
  37→# ---------------------------------------------------------------------------
  38→
  39→def _make_ohlcv(
  40→    n: int = 300,
  41→    trend: str = "up",
  42→    seed: int | None = None,
  43→    start: str = "2021-01-01",
  44→) -> pd.DataFrame:
  45→    """生成测试 OHLCV 数据。
  46→
  47→    Args:
  48→        n:      bar 数量
  49→        trend:  "up" / "down" / "random"
  50→        seed:   随机种子（trend=random 时使用）
  51→        start:  起始日期
  52→    """
  53→    idx = pd.date_range(start, periods=n, freq="B")
  54→    if trend == "up":
  55→        close = np.array([100.0 + i * 0.1 for i in range(n)])
  56→    elif trend == "down":
  57→        close = np.array([100.0 - i * 0.05 for i in range(n)])
  58→    elif trend == "random":
  59→        rng = np.random.default_rng(seed if seed is not None else 42)
  60→        # 带均值回归的随机游走，触发策略信号
  61→        steps = rng.normal(0, 0.5, n)
  62→        close = np.cumsum(np.concatenate([[100.0], steps]))[1:]
  63→    else:
  64→        raise ValueError(f"unknown trend: {trend}")
  65→
  66→    return pd.DataFrame(
  67→        {
  68→            "open":   close - 0.5,
  69→            "high":   close + 1.0,
  70→            "low":    close - 1.0,
  71→            "close":  close,
  72→            "volume": [1_000_000] * n,
  73→        },
  74→        index=idx,
  75→    )
  76→
  77→
  78→def _make_multi_symbol_data(
  79→    symbols: list[str],
  80→    n: int = 300,
  81→    trend: str = "up",
  82→    seed: int = 42,
  83→) -> dict[str, pd.DataFrame]:
  84→    """生成多标的 OHLCV 数据字典。
  85→
  86→    每个标的数据独立生成，但起始日期对齐（便于数值一致性验证）。
  87→    """
  88→    return {
  89→        sym: _make_ohlcv(n=n, trend=trend, seed=seed + i)
  90→        for i, sym in enumerate(symbols)
  91→    }
  92→
  93→
  94→# ---------------------------------------------------------------------------
  95→# 数值一致性辅助
  96→# ---------------------------------------------------------------------------
  97→
  98→def _assert_results_match(
  99→    old: SingleBacktestResult | None,
 100→    new: SingleBacktestResult | None,
 101→    *,
 102→    rtol: float = 1e-6,
 103→    atol: float = 1e-8,
 104→    stats_rtol: float = 1e-4,
 105→    stats_atol: float = 1e-2,
 106→    context: str = "",
 107→) -> None:
 108→    """对比 _backtest_one 与 _backtest_batch 的 SingleBacktestResult。
 109→
 110→    Args:
 111→        old: _backtest_one 返回值（可能为 None）
 112→        new: _backtest_batch 返回的列表中的某一项（可能为 None）
 113→        rtol/atol: daily_returns 的 np.allclose 容差
 114→        stats_rtol/stats_atol: stats 字段容差（vbt 计算路径差异，允许稍宽）
 115→        context: 错误消息上下文
 116→    """
 117→    msg = lambda s: f"{context}: {s}" if context else s
 118→
 119→    # 两者都 None：一致
 120→    if old is None and new is None:
 121→        return
 122→    # 一方 None：不一致
 123→    if old is None or new is None:
 124→        pytest.fail(msg(f"one is None, other is not (old={old}, new={new})"))
 125→
 126→    assert old.symbol == new.symbol, msg("symbol mismatch")
 127→    assert old.strategy == new.strategy, msg("strategy mismatch")
 128→
 129→    # daily_returns: 严格一致
 130→    assert not old.daily_returns.empty, msg("old daily_returns is empty")
 131→    assert not new.daily_returns.empty, msg("new daily_returns is empty")
 132→    # 对齐索引后比较（vbt 列提取可能返回不同的 index name）
 133→    old_dr = old.daily_returns.reset_index(drop=True)
 134→    new_dr = new.daily_returns.reset_index(drop=True)
 135→    assert len(old_dr) == len(new_dr), msg(
 136→        f"daily_returns length mismatch: old={len(old_dr)}, new={len(new_dr)}"
 137→    )
 138→    np.testing.assert_allclose(
 139→        old_dr.values,
 140→        new_dr.values,
 141→        rtol=rtol, atol=atol,
 142→        err_msg=msg("daily_returns mismatch"),
 143→    )
 144→
 145→    # stats 字段：允许浮点误差
 146→    assert abs(old.sharpe - new.sharpe) < stats_rtol + stats_atol * max(
 147→        abs(old.sharpe), 1.0
 148→    ), msg(f"sharpe mismatch: old={old.sharpe}, new={new.sharpe}")
 149→    assert abs(old.total_return_pct - new.total_return_pct) < stats_atol, msg(
 150→        f"total_return_pct mismatch: old={old.total_return_pct}, new={new.total_return_pct}"
 151→    )
 152→    assert abs(old.max_drawdown_pct - new.max_drawdown_pct) < stats_atol, msg(
 153→        f"max_drawdown_pct mismatch: old={old.max_drawdown_pct}, new={new.max_drawdown_pct}"
 154→    )
 155→    assert abs(old.win_rate_pct - new.win_rate_pct) < stats_atol, msg(
 156→        f"win_rate_pct mismatch: old={old.win_rate_pct}, new={new.win_rate_pct}"
 157→    )
 158→    assert old.total_trades == new.total_trades, msg(
 159→        f"total_trades mismatch: old={old.total_trades}, new={new.total_trades}"
 160→    )
 161→    # sortino 从 daily_returns 派生，应严格一致
 162→    assert abs(old.sortino - new.sortino) < 1e-6, msg(
 163→        f"sortino mismatch: old={old.sortino}, new={new.sortino}"
 164→    )
 165→
 166→
 167→# ---------------------------------------------------------------------------
 168→# Test 1-5: 各策略 batch vs single 数值一致性
 169→# ---------------------------------------------------------------------------
 170→
 171→# 测试矩阵：(strategy_name, [param_combos])
 172→_STRATEGY_PARAM_CASES = [
 173→    ("dual_ma", [
 174→        {"fast": 5, "slow": 20},
 175→        {"fast": 10, "slow": 30},
 176→    ]),
 177→    ("rsi_mean_revert", [
 178→        {"period": 14, "oversold": 30, "overbought": 70},
 179→        {"period": 7, "oversold": 25, "overbought": 75},
 180→    ]),
 181→    ("rsi_trend_filter", [
 182→        {"rsi_period": 14, "oversold": 30, "overbought": 70, "trend_period": 50},
 183→        {"rsi_period": 7, "oversold": 25, "overbought": 75, "trend_period": 50},
 184→    ]),
 185→    ("macd_cross", [
 186→        {"fast": 12, "slow": 26, "signal_period": 9},
 187→        {"fast": 5, "slow": 20, "signal_period": 5},
 188→    ]),
 189→    ("bollinger_band", [
 190→        {"period": 20, "std_dev": 2.0},
 191→        {"period": 10, "std_dev": 1.5},
 192→    ]),
 193→]
 194→
 195→
 196→# 展开为扁平的 (strategy_name, params) 列表 + 自定义 ID
 197→_EXPANDED_CASES: list[tuple[str, dict]] = []
 198→_EXPANSED_IDS: list[str] = []
 199→for _s, _combos in _STRATEGY_PARAM_CASES:
 200→    for _i, _p in enumerate(_combos):
 201→        _EXPANDED_CASES.append((_s, _p))
 202→        _EXPANSED_IDS.append(f"{_s}-{_i}")
 203→
 204→
 205→@pytest.mark.parametrize(
 206→    "strategy_name, params",
 207→    _EXPANDED_CASES,
 208→    ids=_EXPANSED_IDS,
 209→)
 210→class TestBatchConsistencyAllStrategies:
 211→    """5 个策略 × 2 参数组合的 batch vs single 一致性测试。"""
 212→
 213→    def test_batch_matches_single_all_symbols(
 214→        self, strategy_name: str, params: dict
 215→    ) -> None:
 216→        """批量回测与逐标的回测在每个标的上数值一致。"""
 217→        # 3 个标的 + 随机走势（触发更多策略信号，覆盖更全）
 218→        data = _make_multi_symbol_data(
 219→            ["AAA", "BBB", "CCC"], n=300, trend="random", seed=123
 220→        )
 221→
 222→        # 旧方式：逐标的回测
 223→        old_results: dict[str, SingleBacktestResult | None] = {}
 224→        for sym, df in data.items():
 225→            df = df.copy()
 226→            df.index.name = sym
 227→            old_results[sym] = _backtest_one(df, strategy_name, params)
 228→
 229→        # 新方式：批量回测
 230→        new_results_list = _backtest_batch(data, strategy_name, params)
 231→        new_results = {r.symbol: r for r in new_results_list}
 232→
 233→        # 每个标的都应一致（_backtest_one 返回 None 的标的在 batch 中不出现）
 234→        for sym, old_r in old_results.items():
 235→            if old_r is None:
 236→                assert sym not in new_results, (
 237→                    f"{strategy_name}/{params} {sym}: _backtest_one returned None "
 238→                    f"but _backtest_batch returned a result"
 239→                )
 240→                continue
 241→            assert sym in new_results, (
 242→                f"{strategy_name}/{params} {sym}: _backtest_one returned a result "
 243→                f"but _backtest_batch dropped it"
 244→            )
 245→            _assert_results_match(
 246→                old_r, new_results[sym],
 247→                context=f"{strategy_name}/{params} {sym}",
 248→            )
 249→
 250→
 251→# ---------------------------------------------------------------------------
 252→# Test 6: 数据不足的标的被跳过
 253→# ---------------------------------------------------------------------------
 254→
 255→class TestBatchEdgeCases:
 256→    """批量化回测的边界场景测试。"""
 257→
 258→    def test_batch_skips_short_data(self) -> None:
 259→        """数据 < 30 天的标的应被跳过（不返回结果）。"""
 260→        # 一个长数据 + 一个短数据
 261→        data = {
 262→            "LONG": _make_ohlcv(300, trend="up"),
 263→            "SHORT": _make_ohlcv(10, trend="up"),
 264→        }
 265→        results = _backtest_batch(data, "dual_ma", {"fast": 5, "slow": 20})
 266→        symbols = [r.symbol for r in results]
 267→        assert "LONG" in symbols
 268→        assert "SHORT" not in symbols, (
 269→            "数据 < 30 天的标的应被跳过，但仍出现在结果中"
 270→        )
 271→
 272→    def test_batch_skips_empty_df(self) -> None:
 273→        """空 DataFrame 的标的应被跳过。"""
 274→        data = {
 275→            "GOOD": _make_ohlcv(300, trend="up"),
 276→            "EMPTY": pd.DataFrame(),
 277→        }
 278→        results = _backtest_batch(data, "dual_ma", {"fast": 5, "slow": 20})
 279→        symbols = [r.symbol for r in results]
 280→        assert "GOOD" in symbols
 281→        assert "EMPTY" not in symbols
 282→
 283→    def test_batch_single_symbol(self) -> None:
 284→        """只有 1 个标的时批量回测应正常工作。"""
 285→        data = {"SOLO": _make_ohlcv(300, trend="up")}
 286→        # 给一个随机走势的单标的，确保有信号
 287→        data = {"SOLO": _make_ohlcv(300, trend="random", seed=7)}
 288→        results = _backtest_batch(data, "dual_ma", {"fast": 5, "slow": 20})
 289→        assert len(results) == 1
 290→        assert results[0].symbol == "SOLO"
 291→        assert not results[0].daily_returns.empty
 292→
 293→    def test_batch_single_symbol_matches_single(self) -> None:
 294→        """单标的时 batch vs single 一致性。"""
 295→        df = _make_ohlcv(300, trend="random", seed=7)
 296→        df.index.name = "SOLO"
 297→        old = _backtest_one(df, "dual_ma", {"fast": 5, "slow": 20})
 298→        new_list = _backtest_batch(
 299→            {"SOLO": df}, "dual_ma", {"fast": 5, "slow": 20}
 300→        )
 301→        assert len(new_list) == 1
 302→        _assert_results_match(old, new_list[0], context="single-symbol")
 303→
 304→    def test_batch_misaligned_dates(self) -> None:
 305→        """不同起始日期的标的：批量回测应正常完成（不抛异常）。
 306→
 307→        数值一致性在严格对齐的日期下成立；对错位日期，
 308→        batch 与 single 的 stats 可能因 NaN 填充方式不同而有细微差异，
 309→        但 daily_returns 在有效区间内应一致。
 310→        """
 311→        # 标的 A 从 2021-01-01 起 300 bar
 312→        # 标的 B 从 2021-06-01 起 300 bar（晚 5 个月）
 313→        df_a = _make_ohlcv(300, trend="up", start="2021-01-01")
 314→        df_b = _make_ohlcv(300, trend="up", start="2021-06-01")
 315→        data = {"MISA": df_a, "MISB": df_b}
 316→
 317→        # 不应抛异常
 318→        results = _backtest_batch(data, "dual_ma", {"fast": 5, "slow": 20})
 319→        assert len(results) == 2
 320→        symbols = [r.symbol for r in results]
 321→        assert set(symbols) == {"MISA", "MISB"}
 322→        for r in results:
 323→            assert not r.daily_returns.empty
 324→
 325→    def test_batch_empty_data(self) -> None:
 326→        """全空���据返回空列表。"""
 327→        results = _backtest_batch({}, "dual_ma", {"fast": 5, "slow": 20})
 328→        assert results == []
 329→
 330→    def test_batch_unknown_strategy(self) -> None:
 331→        """未注册策略返回空列表（不抛异常）。"""
 332→        data = {"AAA": _make_ohlcv(300)}
 333→        results = _backtest_batch(data, "nonexistent_xyz", {})
 334→        assert results == []
 335→
 336→    def test_batch_no_open_column(self) -> None:
 337→        """DataFrame 无 open 列时也能正常回测（降级为 close 执行）。"""
 338→        df = _make_ohlcv(300, trend="random", seed=42).drop(columns=["open"])
 339→        data = {"NOOPEN": df}
 340→        results = _backtest_batch(data, "dual_ma", {"fast": 5, "slow": 20})
 341→        assert len(results) == 1
 342→        assert results[0].symbol == "NOOPEN"
 343→
 344→    def test_batch_preserves_symbol_order(self) -> None:
 345→        """结果列表的 symbol 顺序应与 signal_matrix.columns 顺序一致
 346→        （即与输入 dict 的插入顺序一致，Python 3.7+ 保证）。"""
 347→        data = {
 348→            "ZEBRA": _make_ohlcv(300, trend="up"),
 349→            "ALPHA": _make_ohlcv(300, trend="up"),
 350→            "MIKE":  _make_ohlcv(300, trend="up"),
 351→        }
 352→        results = _backtest_batch(data, "dual_ma", {"fast": 5, "slow": 20})
 353→        symbols = [r.symbol for r in results]
 354→        # 顺序应与输入 dict 一致
 355→        assert symbols == ["ZEBRA", "ALPHA", "MIKE"]
 356→
 357→
 358→# ---------------------------------------------------------------------------
 359→# Test: _backtest_batch 输出格式与 _backtest_one 一致
 360→# ---------------------------------------------------------------------------
 361→
 362→class TestBatchOutputFormat:
 363→    """验证 _backtest_batch 输出的 SingleBacktestResult 字段完整。"""
 364→
 365→    def test_result_fields_populated(self) -> None:
 366→        """SingleBacktestResult 所有字段都被正确填充（无 NaN）。"""
 367→        data = _make_multi_symbol_data(
 368→            ["AAA", "BBB"], n=300, trend="random", seed=99
 369→        )
 370→        results = _backtest_batch(data, "rsi_mean_revert",
 371→                                  {"period": 14, "oversold": 30, "overbought": 70})
 372→        assert len(results) == 2
 373→        for r in results:
 374→            assert isinstance(r, SingleBacktestResult)
 375→            assert r.symbol in ["AAA", "BBB"]
 376→            assert r.strategy == "rsi_mean_revert"
 377→            assert r.params == {"period": 14, "oversold": 30, "overbought": 70}
 378→            assert isinstance(r.sharpe, float)
 379→            assert isinstance(r.total_return_pct, float)
 380→            assert isinstance(r.max_drawdown_pct, float)
 381→            assert isinstance(r.win_rate_pct, float)
 382→            assert isinstance(r.total_trades, int)
 383→            assert isinstance(r.sortino, float)
 384→            assert not r.daily_returns.empty
 385→            # 所有数值字段都应是有限值（_safe_float 已处理 NaN）
 386→            for v in [r.sharpe, r.total_return_pct, r.max_drawdown_pct,
 387→                      r.win_rate_pct, r.sortino]:
 388→                assert np.isfinite(v), f"{r.symbol}: 字段值非有限: {v}"
 389→
 390→    def test_batch_results_are_independent(self) -> None:
 391→        """不同标的的 daily_returns 应独立（不共享索引/引用）。"""
 392→        data = _make_multi_symbol_data(
 393→            ["AAA", "BBB"], n=300, trend="random", seed=55
 394→        )
 395→        results = _backtest_batch(data, "dual_ma", {"fast": 5, "slow": 20})
 396→        assert len(results) == 2
 397→        # 修改一个不应影响另一个
 398→        r0_orig = results[0].daily_returns.iloc[0]
 399→        r1_orig = results[1].daily_returns.iloc[0]
 400→        # 两个标的的 daily_returns 应不同（不同数据）
 401→        # 注：相同 trend+seed 的数据生成相同走势；这里 seed 不同
 402→        assert r0_orig != r1_orig or len(results[0].daily_returns) > 0
 403→
 404→
 405→# ---------------------------------------------------------------------------
 406→# Test: _run_group 集成（进度日志 + batch 路径）
 407→# ---------------------------------------------------------------------------
 408→
 409→def _make_mock_store(data_by_symbol: dict[str, pd.DataFrame]) -> MagicMock:
 410→    """构造一个 Mock MarketDataStore，get_bars_multi 返回指定数据。"""
 411→    store = MagicMock()
 412→    def get_bars_multi(symbols, start, end, timeframe="1d"):
 413→        return {s: data_by_symbol[s] for s in symbols if s in data_by_symbol}
 414→    store.get_bars_multi.side_effect = get_bars_multi
 415→    return store
 416→
 417→
 418→def _make_mock_universe(groups: dict[str, list[str]]) -> MagicMock:
 419→    """构造一个 Mock UniverseManager，get_groups 返回指定分组。"""
 420→    universe = MagicMock()
 421→    universe.get_groups.return_value = groups
 422→    return universe
 423→
 424→
 425→class TestRunGroupBatchIntegration:
 426→    """验证 _run_group 使用 _backtest_batch 后仍产出正确结果。"""
 427→
 428→    def test_run_group_still_produces_weights(self) -> None:
 429→        """_run_group 使用 batch 后仍产出非空权重列表。"""
 430→        data = _make_multi_symbol_data(
 431→            ["AAPL", "MSFT"], n=300, trend="random", seed=11
 432→        )
 433→        store = _make_mock_store(data)
 434→        # _get_spy_returns 会被调用，返回 None 即可（alpha 退化为 0）
 435→        universe = _make_mock_universe({"TEST_GROUP": ["AAPL", "MSFT"]})
 436→
 437→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
 438→        from mytrader.backtest.matrix_backtest import MatrixBacktestReport
 439→        report = MatrixBacktestReport(
 440→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
 441→            backtest_window="2021-01-01 ~ 2022-01-01",
 442→            groups={},
 443→        )
 444→
 445→        weights = mb._run_group(
 446→            group_id="TEST_GROUP",
 447→            symbols=["AAPL", "MSFT"],
 448→            start=date(2021, 1, 1),
 449→            end=date(2022, 1, 1),
 450→            strategies=["dual_ma"],
 451→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 452→            report=report,
 453→        )
 454→        assert len(weights) >= 1
 455→        assert all("strategy" in w for w in weights)
 456→        assert all("weight" in w for w in weights)
 457→
 458→    def test_run_group_progress_logging(self) -> None:
 459→        """_run_group 应输出包含耗时的进度日志。"""
 460→        # loguru 不通过标准 logging 传播，需用 logger.add 捕获
 461→        from loguru import logger
 462→
 463→        data = _make_multi_symbol_data(
 464→            ["AAPL", "MSFT"], n=300, trend="random", seed=22
 465→        )
 466→        store = _make_mock_store(data)
 467→        universe = _make_mock_universe({"TEST_GROUP": ["AAPL", "MSFT"]})
 468→
 469→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
 470→        from mytrader.backtest.matrix_backtest import MatrixBacktestReport
 471→        report = MatrixBacktestReport(
 472→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
 473→            backtest_window="2021-01-01 ~ 2022-01-01",
 474→            groups={},
 475→        )
 476→
 477→        msgs: list[str] = []
 478→        handler_id = logger.add(lambda m: msgs.append(str(m)), level="INFO")
 479→        try:
 480→            mb._run_group(
 481→                group_id="TEST_GROUP",
 482→                symbols=["AAPL", "MSFT"],
 483→                start=date(2021, 1, 1),
 484→                end=date(2022, 1, 1),
 485→                strategies=["dual_ma"],
 486→                param_grids={"dual_ma": {"fast": [5, 10], "slow": [20, 30]}},
 487→                report=report,
 488→            )
 489→        finally:
 490→            logger.remove(handler_id)
 491→
 492→        # 应包含 "MatrixBacktest" 日志
 493→        all_logs = " ".join(msgs)
 494→        assert "MatrixBacktest" in all_logs, (
 495→            f"未找到 MatrixBacktest 日志：{all_logs}"
 496→        )
 497→        # 应有进度日志（"done" 关键字，spec §4.3 要求）
 498→        assert "done" in all_logs, (
 499→            f"未找到进度完成日志（'done'）：{all_logs}"
 500→        )
 501→        # 应有耗时信息（如 "0.Xs"）
 502→        assert any("s " in m or "s)" in m for m in msgs), (
 503→            f"日志未包含耗时信息：{msgs}"
 504→        )
 505→
 506→
 507→# ---------------------------------------------------------------------------
 508→# Test: Walk-Forward 路径使用 batch
 509→# ---------------------------------------------------------------------------
 510→
 511→class TestWalkForwardBatchIntegration:
 512→    """验证 Walk-Forward 的 _backtest_with_params_on_period 使用 batch。"""
 513→
 514→    def test_walk_forward_returns_valid_report(self) -> None:
 515→        """Walk-Forward 4 轮后产出有效报告（不抛异常）。"""
 516→        from mytrader.backtest.matrix_backtest import run_walk_forward
 517→
 518→        data = _make_multi_symbol_data(
 519→            ["AAPL", "MSFT"], n=500, trend="random", seed=33
 520→        )
 521→        store = _make_mock_store(data)
 522→        universe = _make_mock_universe({"TEST_GROUP": ["AAPL", "MSFT"]})
 523→
 524→        mb = MatrixBacktest(store=store, universe=universe, years=2, top_k=2)
 525→        report = run_walk_forward(
 526→            mb,
 527→            strategies=["dual_ma"],
 528→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 529→            rounds=2,
 530→            train_months=6,
 531→            val_months=3,
 532→        )
 533→        assert len(report.rounds) == 2
 534→        # 每轮都应有 sortino 和 max_dd 数值（可能为 0，但不应为 None）
 535→        for r in report.rounds:
 536→            assert isinstance(r.val_sortino, float)
 537→            assert isinstance(r.val_max_dd, float)
 538→            assert isinstance(r.passed, bool)
 539→
---
现在
---
让我
---
检查
---
一下
---
 v
---
bt
---
 API
---
 以
---
获取
---
已
---
平
---
仓
---
交易
---
，
---
并
---
查看
---
 matrix
---
_back
---
test
---
 的
---
现有
---
测试
---
文件
---
以
---
了解
---
测试
---
模式
---
：
---
{"command":"/Users/rickouyang/miniforge3/envs/py312trade/bin/python -c \"\nimport vectorbt as vbt\nimport pandas as pd\nimport numpy as np\n\n# Make simple data\nn = 100\nidx = pd.date_range('2021-01-01', periods=n, freq='B')\nclose = pd.Series(100 + np.cumsum(np.random.default_rng(42).normal(0, 0.5, n)), index=idx, name='AAA')\nopen_ = close - 0.5\n\n# Simple signals: enter at bar 10, exit at bar 20\nsig = pd.Series(0, index=idx)\nsig.iloc[10] = 1\nsig.iloc[20] = -1\n\nentries = sig == 1\nexits = sig == -1\n\npf = vbt.Portfolio.from_signals(close=close, open=open_, entries=entries, exits=exits, init_cash=10000, fees=0.001, size=0.95, size_type='Percent', freq='D')\n\nprint('Total Trades:', pf.stats()['Total Trades'])\nprint('trades attr:', type(pf.trades))\nprint('trades.status_closed:', type(pf.trades.status_closed))\nprint('status_closed.count():', pf.trades.status_closed.count())\nprint()\nprint('Full trades object dir (filtered):')\nprint([a for a in dir(pf.trades) if 'clos' in a.lower() or 'status' in a.lower() or 'count' in a.lower()][:30])\n\"\n","description":"Test vbt 1.0 closed trades API"}
---
Test vbt 1.0 closed trades API
---
Command: /Users/rickouyang/miniforge3/envs/py312trade/bin/python -c "
import vectorbt as vbt
import pandas as pd
import numpy as np

# Make simple data
n = 100
idx = pd.date_range('2021-01-01', periods=n, freq='B')
close = pd.Series(100 + np.cumsum(np.random.default_rng(42).normal(0, 0.5, n)), index=idx, name='AAA')
open_ = close - 0.5

# Simple signals: enter at bar 10, exit at bar 20
sig = pd.Series(0, index=idx)
sig.iloc[10] = 1
sig.iloc[20] = -1

entries = sig == 1
exits = sig == -1

pf = vbt.Portfolio.from_signals(close=close, open=open_, entries=entries, exits=exits, init_cash=10000, fees=0.001, size=0.95, size_type='Percent', freq='D')

print('Total Trades:', pf.stats()['Total Trades'])
print('trades attr:', type(pf.trades))
print('trades.status_closed:', type(pf.trades.status_closed))
print('status_closed.count():', pf.trades.status_closed.count())
print()
print('Full trades object dir (filtered):')
print([a for a in dir(pf.trades) if 'clos' in a.lower() or 'status' in a.lower() or 'count' in a.lower()][:30])
"

Stdout: Total Trades: 1
trades attr: <class 'vectorbt.portfolio.trades.ExitTrades'>
Traceback (most recent call last):
  File "<string>", line 24, in <module>
AttributeError: 'ExitTrades' object has no attribute 'status_closed'

Stderr: (empty)
Exit Code: 1
Signal: (none)
---
Let
---
 me
---
 check
---
 the
---
 actual
---
 API
---
 for
---
 v
---
bt
---
 
---
1
---
.
---
0
---
.
---
0
---
 trades
---
.
---
 The
---
 `
---
status
---
_closed
---
`
---
 attribute
---
 doesn
---
't
---
 exist
---
.
---
 Let
---
 me
---
 explore
---
.
---
{"command":"/Users/rickouyang/miniforge3/envs/py312trade/bin/python -c \"\nimport vectorbt as vbt\nimport pandas as pd\nimport numpy as np\n\nn = 100\nidx = pd.date_range('2021-01-01', periods=n, freq='B')\nclose = pd.Series(100 + np.cumsum(np.random.default_rng(42).normal(0, 0.5, n)), index=idx, name='AAA')\nopen_ = close - 0.5\n\nsig = pd.Series(0, index=idx)\nsig.iloc[10] = 1\nsig.iloc[20] = -1\n\nentries = sig == 1\nexits = sig == -1\n\npf = vbt.Portfolio.from_signals(close=close, open=open_, entries=entries, exits=exits, init_cash=10000, fees=0.001, size=0.95, size_type='Percent', freq='D')\n\nprint('Total Trades:', pf.stats()['Total Trades'])\nprint('trades attr:', type(pf.trades))\nprint()\nprint('Trades records readable:')\nprint(pf.trades.records_readable)\nprint()\nprint('Status field:')\nprint('trades.status:', pf.trades.status if hasattr(pf.trades, 'status') else 'NO status attr')\nprint()\nprint('All trades attrs:')\nfor a in dir(pf.trades):\n    if not a.startswith('_'):\n        print(' -', a)\n\"\n","description":"Explore vbt trades API"}
---
Explore vbt trades API
---
Command: /Users/rickouyang/miniforge3/envs/py312trade/bin/python -c "
import vectorbt as vbt
import pandas as pd
import numpy as np

n = 100
idx = pd.date_range('2021-01-01', periods=n, freq='B')
close = pd.Series(100 + np.cumsum(np.random.default_rng(42).normal(0, 0.5, n)), index=idx, name='AAA')
open_ = close - 0.5

sig = pd.Series(0, index=idx)
sig.iloc[10] = 1
sig.iloc[20] = -1

entries = sig == 1
exits = sig == -1

pf = vbt.Portfolio.from_signals(close=close, open=open_, entries=entries, exits=exits, init_cash=10000, fees=0.001, size=0.95, size_type='Percent', freq='D')

print('Total Trades:', pf.stats()['Total Trades'])
print('trades attr:', type(pf.trades))
print()
print('Trades records readable:')
print(pf.trades.records_readable)
print()
print('Status field:')
print('trades.status:', pf.trades.status if hasattr(pf.trades, 'status') else 'NO status attr')
print()
print('All trades attrs:')
for a in dir(pf.trades):
    if not a.startswith('_'):
        print(' -', a)
"

Stdout: Total Trades: 1
trades attr: <class 'vectorbt.portfolio.trades.ExitTrades'>

Trades records readable:
   Exit Trade Id  Column       Size  ... Direction  Status  Position Id
0              0       0  96.094901  ...      Long  Closed            0

[1 rows x 14 columns]

Status field:
trades.status: MappedArray(**Config({
    "wrapper": "<vectorbt.base.array_wrapper.ArrayWrapper object at 0x11e42dc40> of shape (100,)",
    "mapped_arr": "<numpy.ndarray object at 0x12a180810> of shape (1,)",
    "col_arr": "<numpy.ndarray object at 0x12a13f1b0> of shape (1,)",
    "id_arr": "<numpy.ndarray object at 0x12a13f750> of shape (1,)",
    "idx_arr": "<numpy.ndarray object at 0x12a13e010> of shape (1,)",
    "mapping": {
        "Open": 0,
        "Closed": 1
    },
    "col_mapper": "ColumnMapper(**Config({\n    \"wrapper\": \"<vectorbt.base.array_wrapper.ArrayWrapper object at 0x11e42dc40> of shape (100,)\",\n    \"col_arr\": \"<numpy.ndarray object at 0x12a746670> of shape (1,)\",\n    \"engine\": null\n}))",
    "engine": null
}))

All trades attrs:
 - apply
 - apply_mask
 - avg_duration
 - build_field_config_doc
 - build_metrics_doc
 - build_subplots_doc
 - close
 - closed
 - col
 - col_arr
 - col_mapper
 - config
 - copy
 - count
 - coverage
 - deep_getattr
 - direction
 - dumps
 - duration
 - end_idx
 - engine
 - entry_fees
 - entry_idx
 - entry_price
 - exit_fees
 - exit_idx
 - exit_price
 - expectancy
 - field_config
 - from_orders
 - from_ts
 - get_apply_mapping_arr
 - get_by_col_idxs
 - get_field_arr
 - get_field_mapping
 - get_field_name
 - get_field_setting
 - get_field_title
 - get_map_field
 - get_map_field_to_index
 - id
 - id_arr
 - idx_arr
 - iloc
 - indexing_func
 - indexing_func_meta
 - indexing_kwargs
 - is_sorted
 - load
 - loads
 - loc
 - long
 - losing
 - losing_streak
 - map
 - map_array
 - map_field
 - max_duration
 - metrics
 - open
 - override_field_config_doc
 - override_metrics_doc
 - override_subplots_doc
 - parent_id
 - plot
 - plot_pnl
 - plots
 - plots_defaults
 - pnl
 - post_resolve_attr
 - pre_resolve_attr
 - profit_factor
 - recarray
 - records
 - records_arr
 - records_readable
 - regroup
 - replace
 - resolve_attr
 - resolve_self
 - returns
 - save
 - select_one
 - select_one_from_obj
 - self_aliases
 - short
 - size
 - sort
 - sqn
 - start_idx
 - stats
 - stats_defaults
 - status
 - subplots
 - to_doc
 - to_mask
 - ts
 - update_config
 - values
 - win_rate
 - winning
 - winning_streak
 - wrapper
 - writeable_attrs
 - xs

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
I
---
 see
---
.
---
 The
---
 API
---
 in
---
 v
---
bt
---
 
---
1
---
.
---
0
---
.
---
0
---
 has
---
 `
---
pf
---
.tr
---
ades
---
.closed
---
`
---
 (
---
which
---
 is
---
 a
---
 Trades
---
 object
---
)
---
 and
---
 `
---
pf
---
.tr
---
ades
---
.status
---
`
---
 (
---
a
---
 M
---
apped
---
Array
---
).
---
 Let
---
 me
---
 check
---
 the
---
 `.
---
closed
---
`
---
 attribute
---
 and
---
 how
---
 to
---
 count
---
 closed
---
 trades
---
 properly
---
.


---
The
---
 `
---
closed
---
`
---
 attr
---
 seems
---
 to
---
 be
---
 the
---
 closed
---
 trades
---
 filter
---
.
---
 Let
---
 me
---
 check
---
 it
---
.


---
The
---
 `
---
status
---
`
---
 is
---
 a
---
 M
---
apped
---
Array
---
,
---
 and
---
 `
---
mapping
---
`
---
 shows
---
 `
---
{"
---
Open
---
":
---
 
---
0
---
,
---
 "
---
Closed
---
":
---
 
---
1
---
}`
---
.
---
 So
---
 I
---
 should
---
 be
---
 able
---
 to
---
 do
---
 something
---
 like
---
:

---
-
---
 `
---
pf
---
.tr
---
ades
---
.closed
---
.count
---
()`
---
 —
---
 count
---
 of
---
 closed
---
 trades
---
 (
---
using
---
 the
---
 `
---
closed
---
`
---
 filter
---
)

---
-
---
 Or
---
 filter
---
 by
---
 status
---
:
---
 `
---
pf
---
.tr
---
ades
---
.status
---
 ==
---
 "
---
Closed
---
"`
---
 and
---
 count
---



---
Let
---
 me
---
 verify
---
.
---
{"command":"/Users/rickouyang/miniforge3/envs/py312trade/bin/python -c \"\nimport vectorbt as vbt\nimport pandas as pd\nimport numpy as np\n\nn = 100\nidx = pd.date_range('2021-01-01', periods=n, freq='B')\nclose = pd.Series(100 + np.cumsum(np.random.default_rng(42).normal(0, 0.5, n)), index=idx, name='AAA')\nopen_ = close - 0.5\n\n# Test 1: with exit signal (closed trade)\nsig = pd.Series(0, index=idx)\nsig.iloc[10] = 1\nsig.iloc[20] = -1\n\nentries = sig == 1\nexits = sig == -1\n\npf = vbt.Portfolio.from_signals(close=close, open=open_, entries=entries, exits=exits, init_cash=10000, fees=0.001, size=0.95, size_type='Percent', freq='D')\n\nprint('=== Test 1: with exit signal ===')\nprint('Total Trades (stats):', pf.stats()['Total Trades'])\nprint('pf.trades.count():', pf.trades.count())\nprint('pf.trades.closed.count():', pf.trades.closed.count())\nprint('pf.trades.open.count():', pf.trades.open.count())\nprint('records_readable Status field:')\nprint(pf.trades.records_readable['Status'].value_counts().to_dict())\n\n# Test 2: Only entry, no exit (open trade at end)\nprint()\nprint('=== Test 2: only entry, no exit (degenerate) ===')\nsig2 = pd.Series(0, index=idx)\nsig2.iloc[10] = 1\nentries2 = sig2 == 1\nexits2 = sig2 == -1\n\npf2 = vbt.Portfolio.from_signals(close=close, open=open_, entries=entries2, exits=exits2, init_cash=10000, fees=0.001, size=0.95, size_type='Percent', freq='D')\nprint('Total Trades (stats):', pf2.stats()['Total Trades'])\nprint('pf2.trades.count():', pf2.trades.count())\nprint('pf2.trades.closed.count():', pf2.trades.closed.count())\nprint('pf2.trades.open.count():', pf2.trades.open.count())\nprint('records_readable Status field:')\nprint(pf2.trades.records_readable['Status'].value_counts().to_dict())\n\n# Multi-symbol test\nprint()\nprint('=== Test 3: Multi-symbol (columnar) ===')\nclose2 = pd.DataFrame({\n    'AAA': 100 + np.cumsum(np.random.default_rng(11).normal(0, 0.5, n)),\n    'BBB': 100 + np.cumsum(np.random.default_rng(22).normal(0, 0.5, n)),\n}, index=idx)\nsig3 = pd.DataFrame({\n    'AAA': sig.values,\n    'BBB': sig2.values,  # BBB only has entry, no exit\n}, index=idx)\nentries3 = sig3 == 1\nexits3 = sig3 == -1\n\npf3 = vbt.Portfolio.from_signals(close=close2, open=close2 - 0.5, entries=entries3, exits=exits3, init_cash=10000, fees=0.001, size=0.95, size_type='Percent', freq='D')\nprint('pf3.trades.count():', pf3.trades.count())\nprint('pf3.trades.closed.count():', pf3.trades.closed.count())\nprint('pf3[AAA].trades.closed.count():', pf3['AAA'].trades.closed.count())\nprint('pf3[BBB].trades.closed.count():', pf3['BBB'].trades.closed.count())\nprint('pf3[AAA].stats()[Total Trades]:', pf3['AAA'].stats()['Total Trades'])\nprint('pf3[BBB].stats()[Total Trades]:', pf3['BBB'].stats()['Total Trades'])\n\"\n","description":"Verify closed trades counting API"}
---
Verify closed trades counting API
---
Command: /Users/rickouyang/miniforge3/envs/py312trade/bin/python -c "
import vectorbt as vbt
import pandas as pd
import numpy as np

n = 100
idx = pd.date_range('2021-01-01', periods=n, freq='B')
close = pd.Series(100 + np.cumsum(np.random.default_rng(42).normal(0, 0.5, n)), index=idx, name='AAA')
open_ = close - 0.5

# Test 1: with exit signal (closed trade)
sig = pd.Series(0, index=idx)
sig.iloc[10] = 1
sig.iloc[20] = -1

entries = sig == 1
exits = sig == -1

pf = vbt.Portfolio.from_signals(close=close, open=open_, entries=entries, exits=exits, init_cash=10000, fees=0.001, size=0.95, size_type='Percent', freq='D')

print('=== Test 1: with exit signal ===')
print('Total Trades (stats):', pf.stats()['Total Trades'])
print('pf.trades.count():', pf.trades.count())
print('pf.trades.closed.count():', pf.trades.closed.count())
print('pf.trades.open.count():', pf.trades.open.count())
print('records_readable Status field:')
print(pf.trades.records_readable['Status'].value_counts().to_dict())

# Test 2: Only entry, no exit (open trade at end)
print()
print('=== Test 2: only entry, no exit (degenerate) ===')
sig2 = pd.Series(0, index=idx)
sig2.iloc[10] = 1
entries2 = sig2 == 1
exits2 = sig2 == -1

pf2 = vbt.Portfolio.from_signals(close=close, open=open_, entries=entries2, exits=exits2, init_cash=10000, fees=0.001, size=0.95, size_type='Percent', freq='D')
print('Total Trades (stats):', pf2.stats()['Total Trades'])
print('pf2.trades.count():', pf2.trades.count())
print('pf2.trades.closed.count():', pf2.trades.closed.count())
print('pf2.trades.open.count():', pf2.trades.open.count())
print('records_readable Status field:')
print(pf2.trades.records_readable['Status'].value_counts().to_dict())

# Multi-symbol test
print()
print('=== Test 3: Multi-symbol (columnar) ===')
close2 = pd.DataFrame({
    'AAA': 100 + np.cumsum(np.random.default_rng(11).normal(0, 0.5, n)),
    'BBB': 100 + np.cumsum(np.random.default_rng(22).normal(0, 0.5, n)),
}, index=idx)
sig3 = pd.DataFrame({
    'AAA': sig.values,
    'BBB': sig2.values,  # BBB only has entry, no exit
}, index=idx)
entries3 = sig3 == 1
exits3 = sig3 == -1

pf3 = vbt.Portfolio.from_signals(close=close2, open=close2 - 0.5, entries=entries3, exits=exits3, init_cash=10000, fees=0.001, size=0.95, size_type='Percent', freq='D')
print('pf3.trades.count():', pf3.trades.count())
print('pf3.trades.closed.count():', pf3.trades.closed.count())
print('pf3[AAA].trades.closed.count():', pf3['AAA'].trades.closed.count())
print('pf3[BBB].trades.closed.count():', pf3['BBB'].trades.closed.count())
print('pf3[AAA].stats()[Total Trades]:', pf3['AAA'].stats()['Total Trades'])
print('pf3[BBB].stats()[Total Trades]:', pf3['BBB'].stats()['Total Trades'])
"

Stdout: === Test 1: with exit signal ===
Total Trades (stats): 1
pf.trades.count(): 1
pf.trades.closed.count(): 1
pf.trades.open.count(): 0
records_readable Status field:
{'Closed': 1}

=== Test 2: only entry, no exit (degenerate) ===
Total Trades (stats): 1
pf2.trades.count(): 1
pf2.trades.closed.count(): 0
pf2.trades.open.count(): 1
records_readable Status field:
{'Open': 1}

=== Test 3: Multi-symbol (columnar) ===
pf3.trades.count(): AAA    1
BBB    1
Name: count, dtype: int64
pf3.trades.closed.count(): AAA    1
BBB    0
Name: count, dtype: int64
pf3[AAA].trades.closed.count(): 1
pf3[BBB].trades.closed.count(): 0
pf3[AAA].stats()[Total Trades]: 1
pf3[BBB].stats()[Total Trades]: 1

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
I
---
've
---
 confirmed
---
 the
---
 v
---
bt
---
 
---
1
---
.
---
0
---
.
---
0
---
 API
---
:

---
-
---
 `
---
pf
---
.tr
---
ades
---
.closed
---
.count
---
()`
---
 returns
---
 the
---
 count
---
 of
---
 closed
---
 trades
---
 (
---
as
---
 an
---
 int
---
 for
---
 single
---
 symbol
---
,
---
 as
---
 a
---
 Series
---
 for
---
 multi
---
-symbol
---
)

---
-
---
 For
---
 multi
---
-symbol
---
 (
---
column
---
ar
---
),
---
 `
---
pf
---
[s
---
ym
---
].
---
tr
---
ades
---
.closed
---
.count
---
()`
---
 returns
---
 the
---
 int
---
 count
---
 for
---
 that
---
 symbol
---


---
-
---
 This
---
 is
---
 exactly
---
 what
---
 the
---
 spec
---
 mentions
---
:
---
 `
---
pf
---
.tr
---
ades
---
.status
---
_closed
---
.count
---
()`
---
 —
---
 but
---
 the
---
 actual
---
 API
---
 is
---
 `
---
pf
---
.tr
---
ades
---
.closed
---
.count
---
()
---
`


---
The
---
 spec
---
 actually
---
 noted
---
 this
---
 possibility
---
:
---
 "
---
若
---
 v
---
bt
---
 API
---
 名称
---
不同
---
，
---
实现
---
者
---
需
---
查
---
 v
---
bt
---
 
---
1
---
.
---
0
---
.
---
0
---
 
---
实
---
际
---
 API
---
（
---
如
---
 `
---
pf
---
.tr
---
ades
---
.closed
---
.count
---
()`
---
...
---
）
---
并
---
保证
---
正确
---
性
---
"


---
So
---
 I
---
'll
---
 use
---
 `
---
pf
---
.tr
---
ades
---
.closed
---
.count
---
()`
---
.


---
Now
---
 let
---
 me
---
 check
---
 the
---
 existing
---
 test
---
_matrix
---
_back
---
test
---
.py
---
 for
---
 patterns
---
:
---
已
---
确认
---
 v
---
bt
---
 
---
1
---
.
---
0
---
.
---
0
---
 API
---
：
---
使用
---
 `
---
pf
---
.tr
---
ades
---
.closed
---
.count
---
()`
---
（
---
而非
---
 `
---
status
---
_closed
---
`
---
）。
---
我先
---
查看
---
现有的
---
 `
---
test
---
_matrix
---
_back
---
test
---
.py
---
`
---
 以
---
了解
---
测试
---
模式
---
：
---
{"command":"wc -l /Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py","description":"Check test_matrix_backtest.py size"}
---
Check test_matrix_backtest.py size
---
Command: wc -l /Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py
Stdout:     1661 /Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"command":"/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest /Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py --collect-only -q 2>&1 | tail -50","description":"List test cases in test_matrix_backtest.py"}
---
List test cases in test_matrix_backtest.py
---
Command: /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest /Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py --collect-only -q 2>&1 | tail -50
Stdout: tests/test_matrix_backtest.py: 75


Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"command":"/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest /Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py --collect-only 2>&1 | head -80","description":"List test cases verbose"}
---
List test cases verbose
---
Command: /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest /Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py --collect-only 2>&1 | head -80
Stdout: tests/test_matrix_backtest.py::TestHelpers::test_compute_sharpe_positive
tests/test_matrix_backtest.py::TestHelpers::test_compute_sharpe_zero_std
tests/test_matrix_backtest.py::TestHelpers::test_compute_sharpe_empty
tests/test_matrix_backtest.py::TestHelpers::test_portfolio_sharpe_from_results
tests/test_matrix_backtest.py::TestHelpers::test_compute_sortino_positive
tests/test_matrix_backtest.py::TestHelpers::test_compute_sortino_empty
tests/test_matrix_backtest.py::TestHelpers::test_compute_sortino_no_downside_returns_zero
tests/test_matrix_backtest.py::TestHelpers::test_compute_sortino_differs_from_sharpe_when_asymmetric
tests/test_matrix_backtest.py::TestHelpers::test_compute_sortino_known_value
tests/test_matrix_backtest.py::TestHelpers::test_portfolio_sortino_from_results
tests/test_matrix_backtest.py::TestHelpers::test_safe_float_handles_nan
tests/test_matrix_backtest.py::TestHelpers::test_safe_float_handles_none
tests/test_matrix_backtest.py::TestHelpers::test_safe_float_handles_inf
tests/test_matrix_backtest.py::TestHelpers::test_safe_float_passes_normal_numbers
tests/test_matrix_backtest.py::TestHelpers::test_safe_float_handles_non_numeric
tests/test_matrix_backtest.py::TestHelpers::test_safe_mean_empty_list
tests/test_matrix_backtest.py::TestHelpers::test_safe_mean_all_nan
tests/test_matrix_backtest.py::TestHelpers::test_safe_mean_partial_nan
tests/test_matrix_backtest.py::TestHelpers::test_safe_mean_normal
tests/test_matrix_backtest.py::TestHelpers::test_portfolio_max_drawdown_no_returns
tests/test_matrix_backtest.py::TestHelpers::test_portfolio_max_drawdown_all_positive
tests/test_matrix_backtest.py::TestHelpers::test_portfolio_max_drawdown_known_value
tests/test_matrix_backtest.py::TestHelpers::test_portfolio_max_drawdown_returns_positive_pct
tests/test_matrix_backtest.py::TestHelpers::test_backtest_one_with_open
tests/test_matrix_backtest.py::TestHelpers::test_backtest_one_without_open
tests/test_matrix_backtest.py::TestHelpers::test_backtest_one_empty_df
tests/test_matrix_backtest.py::TestHelpers::test_backtest_one_short_df
tests/test_matrix_backtest.py::TestHelpers::test_backtest_one_unknown_strategy
tests/test_matrix_backtest.py::TestHelpers::test_open_parameter_is_passed_to_vectorbt
tests/test_matrix_backtest.py::TestMatrixBacktest::test_run_produces_groups
tests/test_matrix_backtest.py::TestMatrixBacktest::test_run_weights_sum_to_one
tests/test_matrix_backtest.py::TestMatrixBacktest::test_run_output_file
tests/test_matrix_backtest.py::TestMatrixBacktest::test_run_empty_universe
tests/test_matrix_backtest.py::TestMatrixBacktest::test_run_no_data_for_group
tests/test_matrix_backtest.py::TestMatrixBacktest::test_group_results_have_portfolio_sharpe
tests/test_matrix_backtest.py::TestMatrixBacktest::test_survivorship_bias_warning_in_output
tests/test_matrix_backtest.py::TestMatrixBacktest::test_unknown_strategy_logs_warning
tests/test_matrix_backtest.py::TestMatrixBacktest::test_reoptimize_strategy_names_match_registry
tests/test_matrix_backtest.py::TestMatrixBacktest::test_output_file_contains_sortino
tests/test_matrix_backtest.py::TestMatrixBacktest::test_group_results_have_portfolio_sortino
tests/test_matrix_backtest.py::TestMatrixBacktest::test_group_results_have_portfolio_max_drawdown
tests/test_matrix_backtest.py::TestMatrixBacktest::test_output_file_contains_max_drawdown
tests/test_matrix_backtest.py::TestMatrixBacktest::test_output_file_no_nan
tests/test_matrix_backtest.py::TestDDConstraint::test_dd_constrained_field_exists_in_group_result
tests/test_matrix_backtest.py::TestDDConstraint::test_compliant_candidates_selected_by_sortino
tests/test_matrix_backtest.py::TestDDConstraint::test_fallback_when_no_compliant_candidates
tests/test_matrix_backtest.py::TestDDConstraint::test_output_file_contains_dd_constrained_field
tests/test_matrix_backtest.py::TestDDConstraint::test_max_drawdown_threshold_is_20
tests/test_matrix_backtest.py::TestWalkForward::test_walk_forward_round_dataclass
tests/test_matrix_backtest.py::TestWalkForward::test_walk_forward_round_passed_threshold
tests/test_matrix_backtest.py::TestWalkForward::test_walk_forward_report_dataclass
tests/test_matrix_backtest.py::TestWalkForward::test_walk_forward_report_all_fail
tests/test_matrix_backtest.py::TestWalkForward::test_add_months_basic
tests/test_matrix_backtest.py::TestWalkForward::test_add_months_month_end_clamp
tests/test_matrix_backtest.py::TestWalkForward::test_walk_forward_windows_match_user_spec
tests/test_matrix_backtest.py::TestWalkForward::test_run_walk_forward_mock_integration
tests/test_matrix_backtest.py::TestWalkForward::test_run_walk_forward_empty_universe
tests/test_matrix_backtest.py::TestWalkForward::test_run_walk_forward_custom_rounds
tests/test_matrix_backtest.py::TestAlphaComputation::test_compute_alpha_basic
tests/test_matrix_backtest.py::TestAlphaComputation::test_compute_alpha_spy_unavailable
tests/test_matrix_backtest.py::TestAlphaComputation::test_compute_alpha_strategy_underperforms
tests/test_matrix_backtest.py::TestAlphaComputation::test_combine_daily_returns_basic
tests/test_matrix_backtest.py::TestAlphaComputation::test_combine_daily_returns_empty
tests/test_matrix_backtest.py::TestAlphaComputation::test_min_sortino_threshold_constant
tests/test_matrix_backtest.py::TestAlphaBasedTopKSelection::test_top_k_selection_uses_alpha
tests/test_matrix_backtest.py::TestAlphaBasedTopKSelection::test_sortino_filter_excludes_garbage
tests/test_matrix_backtest.py::TestAlphaBasedTopKSelection::test_dd_filter_still_applies
tests/test_matrix_backtest.py::TestAlphaBasedTopKSelection::test_fallback_when_no_sortino_compliant
tests/test_matrix_backtest.py::TestAlphaBasedTopKSelection::test_fallback_when_no_dd_compliant
tests/test_matrix_backtest.py::TestAlphaBasedTopKSelection::test_alpha_field_in_weights_json
tests/test_matrix_backtest.py::TestAlphaBasedTopKSelection::test_group_results_have_backtest_alpha
tests/test_matrix_backtest.py::TestAlphaBasedTopKSelection::test_per_strategy_best_params_uses_alpha
tests/test_matrix_backtest.py::TestEnsembleWeightsUsesAlpha::test_ensemble_weights_use_alpha
tests/test_matrix_backtest.py::TestEnsembleWeightsUsesAlpha::test_ensemble_weights_spy_unavailable_degrades_to_equal
tests/test_matrix_backtest.py::TestEnsembleWeightsUsesAlpha::test_ensemble_weights_single_strategy

75 tests collected in 1.51s

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"command":"grep -n \"TestAlphaBasedTopKSelection\\|test_top_k_selection_uses_alpha\\|class TestAlpha\\|class TestEnsemble\\|_make_mock_store\\|_make_mock_universe\\|def _build_mb\\|class TestDDConstraint\" /Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py | head -30","description":"Find relevant test class structures"}
---
Find relevant test class structures
---
Command: grep -n "TestAlphaBasedTopKSelection\|test_top_k_selection_uses_alpha\|class TestAlpha\|class TestEnsemble\|_make_mock_store\|_make_mock_universe\|def _build_mb\|class TestDDConstraint" /Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py | head -30
Stdout: 593:class TestDDConstraint:
966:class TestAlphaComputation:
1045:class TestAlphaBasedTopKSelection:
1048:    def test_top_k_selection_uses_alpha(self, tmp_path):
1580:class TestEnsembleWeightsUsesAlpha:

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py","limit":200,"offset":1}
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
  20→    _combine_daily_returns,
  21→    _compute_alpha,
  22→    _compute_sharpe,
  23→    _compute_sortino,
  24→    _portfolio_max_drawdown_from_results,
  25→    _portfolio_sharpe_from_results,
  26→    _portfolio_sortino_from_results,
  27→    _optimize_ensemble_weights,
  28→    _safe_float,
  29→    _safe_mean,
  30→    MAX_PORTFOLIO_DRAWDOWN_PCT,
  31→    MIN_SORTINO_THRESHOLD,
  32→    WALK_FORWARD_VAL_DD_THRESHOLD,
  33→    SingleBacktestResult,
  34→    WalkForwardReport,
  35→    WalkForwardRound,
  36→    _add_months,
  37→    run_walk_forward,
  38→)
  39→
  40→
  41→# ---------------------------------------------------------------------------
  42→# Fixtures
  43→# ---------------------------------------------------------------------------
  44→
  45→def _make_ohlcv(n: int = 300, trend: str = "up") -> pd.DataFrame:
  46→    """生成测试 OHLCV 数据（足够计算慢均线）。"""
  47→    idx = pd.date_range("2021-01-01", periods=n, freq="B")
  48→    if trend == "up":
  49→        close = [100.0 + i * 0.1 for i in range(n)]
  50→    else:
  51→        close = [100.0 - i * 0.05 for i in range(n)]
  52→    return pd.DataFrame(
  53→        {
  54→            "open":   [c - 0.5 for c in close],
  55→            "high":   [c + 1.0 for c in close],
  56→            "low":    [c - 1.0 for c in close],
  57→            "close":  close,
  58→            "volume": [1_000_000] * n,
  59→        },
  60→        index=idx,
  61→    )
  62→
  63→
  64→@pytest.fixture
  65→def mock_store(tmp_path):
  66→    store = MagicMock()
  67→    df_aapl = _make_ohlcv(300, trend="up")
  68→    df_msft = _make_ohlcv(300, trend="up")
  69→    df_jpm  = _make_ohlcv(300, trend="up")
  70→
  71→    def get_bars_multi(symbols, start, end, timeframe="1d"):
  72→        mapping = {"AAPL": df_aapl, "MSFT": df_msft, "JPM": df_jpm}
  73→        return {s: mapping[s] for s in symbols if s in mapping}
  74→
  75→    store.get_bars_multi.side_effect = get_bars_multi
  76→    return store
  77→
  78→
  79→@pytest.fixture
  80→def mock_universe():
  81→    from mytrader.universe.models import SymbolMeta
  82→    universe = MagicMock()
  83→    universe.get_groups.return_value = {
  84→        "NDX_mid_vol": ["AAPL", "MSFT"],
  85→        "SPX_mid_vol": ["JPM"],
  86→    }
  87→
  88→    def get_meta(sym):
  89→        ndx = ["AAPL", "MSFT"]
  90→        return SymbolMeta(
  91→            symbol=sym,
  92→            index_membership=["NASDAQ100"] if sym in ndx else ["SP500"],
  93→            sector="Technology" if sym in ndx else "Financials",
  94→            market_cap_tier="large",
  95→            volatility_tier="mid",
  96→            group_id="NDX_mid_vol" if sym in ndx else "SPX_mid_vol",
  97→        )
  98→    universe.get_symbol_meta.side_effect = get_meta
  99→    return universe
 100→
 101→
 102→# ---------------------------------------------------------------------------
 103→# 单函数测试
 104→# ---------------------------------------------------------------------------
 105→
 106→class TestHelpers:
 107→
 108→    def test_compute_sharpe_positive(self):
 109→        """正向收益的 Sharpe > 0。"""
 110→        returns = pd.Series([0.001] * 252)
 111→        sharpe = _compute_sharpe(returns)
 112→        assert sharpe > 0
 113→
 114→    def test_compute_sharpe_zero_std(self):
 115→        """收益恒定（零方差）返回 0。"""
 116→        returns = pd.Series([0.0] * 100)
 117→        assert _compute_sharpe(returns) == 0.0
 118→
 119→    def test_compute_sharpe_empty(self):
 120→        assert _compute_sharpe(pd.Series([], dtype=float)) == 0.0
 121→
 122→    def test_portfolio_sharpe_from_results(self):
 123→        """等权组合 Sharpe 不等于算术平均 Sharpe（差异 > 1e-6）。"""
 124→        n = 252
 125→        r1 = pd.Series(np.random.normal(0.001, 0.01, n))   # 高收益高波动
 126→        r2 = pd.Series(np.random.normal(0.0005, 0.002, n)) # 低收益低波动
 127→
 128→        s1 = _compute_sharpe(r1)
 129→        s2 = _compute_sharpe(r2)
 130→        arithmetic_avg = (s1 + s2) / 2
 131→
 132→        results = [
 133→            SingleBacktestResult("SYM1", "s1", {}, s1, 10, 5, 60, 20, r1),
 134→            SingleBacktestResult("SYM2", "s2", {}, s2, 5, 3, 55, 15, r2),
 135→        ]
 136→        portfolio_sharpe = _portfolio_sharpe_from_results(results)
 137→
 138→        # 组合 Sharpe 与算术平均 Sharpe 应不同（这正是为什么要用组合方式）
 139→        diff = abs(portfolio_sharpe - arithmetic_avg)
 140→        assert diff > 1e-6, (
 141→            f"组合 Sharpe({portfolio_sharpe:.4f}) 与算术平均 Sharpe({arithmetic_avg:.4f}) "
 142→            f"差异应 >1e-6，否则说明实现有误"
 143→        )
 144→
 145→    # ── Sortino（迭代 #1 新增，Constitution L1 首要 KPI）─────────────────────
 146→
 147→    def test_compute_sortino_positive(self):
 148→        """正均值的收益序列 Sortino > 0。"""
 149→        returns = pd.Series([0.001, -0.0005, 0.002, -0.0003, 0.0015] * 60)
 150→        assert _compute_sortino(returns) > 0
 151→
 152→    def test_compute_sortino_empty(self):
 153→        """空序列返回 0。"""
 154→        assert _compute_sortino(pd.Series([], dtype=float)) == 0.0
 155→
 156→    def test_compute_sortino_no_downside_returns_zero(self):
 157→        """全正收益（无下行波动）→ 0.0（退化处理，与 _compute_sharpe 一致）。
 158→
 159→        理论上 Sortino 应为 +inf，但返回 0 保持可算术聚合 + 保守评估。
 160→        """
 161→        returns = pd.Series([0.001] * 100)   # 全正，无下行
 162→        assert _compute_sortino(returns) == 0.0
 163→
 164→    def test_compute_sortino_differs_from_sharpe_when_asymmetric(self):
 165→        """当上行/下行波动不对称时，Sortino ≠ Sharpe（这是引入 Sortino 的意义）。"""
 166→        # 大幅上行小波动 + 偶尔小幅下行：Sortino 应明显高于 Sharpe
 167→        np.random.seed(42)
 168→        upside = np.random.normal(0.003, 0.005, 200)   # 正均值的上行
 169→        downside_shocks = np.array([-0.01, -0.012, -0.008] * 3)  # 少量下行冲击
 170→        returns = pd.Series(np.concatenate([upside, downside_shocks]))
 171→
 172→        sharpe = _compute_sharpe(returns)
 173→        sortino = _compute_sortino(returns)
 174→        # Sortino 仅对下行惩罚 → 上行波动不计入分母 → Sortino > Sharpe
 175→        assert sortino > sharpe, (
 176→            f"非对称收益下 Sortino({sortino:.4f}) 应 > Sharpe({sharpe:.4f})，"
 177→            f"否则说明 Sortino 公式退化为 Sharpe"
 178→        )
 179→
 180→    def test_compute_sortino_known_value(self):
 181→        """已知值验算 Sortino 公式正确性。"""
 182→        # r = [0.01, 0.01, 0.01, -0.01]
 183→        # mean = 0.005; downside = [0,0,0,-0.01]; dd = sqrt(mean([0,0,0,0.0001])) = sqrt(0.000025) = 0.005
 184→        # Sortino = 0.005 / 0.005 * sqrt(252) = 15.8745...
 185→        returns = pd.Series([0.01, 0.01, 0.01, -0.01] * 25)   # 重复 25 次以满足 len>=5
 186→        expected = (0.005 / 0.005) * np.sqrt(252)
 187→        assert abs(_compute_sortino(returns) - expected) < 1e-6
 188→
 189→    def test_portfolio_sortino_from_results(self):
 190→        """等权组合 Sortino 不等于各标的 Sortino 算术平均（与 Sharpe 同理）。"""
 191→        n = 252
 192→        np.random.seed(0)
 193→        r1 = pd.Series(np.random.normal(0.001, 0.01, n))
 194→        r2 = pd.Series(np.random.normal(0.0005, 0.002, n))
 195→
 196→        s1 = _compute_sortino(r1)
 197→        s2 = _compute_sortino(r2)
 198→        arithmetic_avg = (s1 + s2) / 2
 199→
 200→        results = [
 201→
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
  20→    _combine_daily_returns,
  21→    _compute_alpha,
  22→    _compute_sharpe,
  23→    _compute_sortino,
  24→    _portfolio_max_drawdown_from_results,
  25→    _portfolio_sharpe_from_results,
  26→    _portfolio_sortino_from_results,
  27→    _optimize_ensemble_weights,
  28→    _safe_float,
  29→    _safe_mean,
  30→    MAX_PORTFOLIO_DRAWDOWN_PCT,
  31→    MIN_SORTINO_THRESHOLD,
  32→    WALK_FORWARD_VAL_DD_THRESHOLD,
  33→    SingleBacktestResult,
  34→    WalkForwardReport,
  35→    WalkForwardRound,
  36→    _add_months,
  37→    run_walk_forward,
  38→)
  39→
  40→
  41→# ---------------------------------------------------------------------------
  42→# Fixtures
  43→# ---------------------------------------------------------------------------
  44→
  45→def _make_ohlcv(n: int = 300, trend: str = "up") -> pd.DataFrame:
  46→    """生成测试 OHLCV 数据（足够计算慢均线）。"""
  47→    idx = pd.date_range("2021-01-01", periods=n, freq="B")
  48→    if trend == "up":
  49→        close = [100.0 + i * 0.1 for i in range(n)]
  50→    else:
  51→        close = [100.0 - i * 0.05 for i in range(n)]
  52→    return pd.DataFrame(
  53→        {
  54→            "open":   [c - 0.5 for c in close],
  55→            "high":   [c + 1.0 for c in close],
  56→            "low":    [c - 1.0 for c in close],
  57→            "close":  close,
  58→            "volume": [1_000_000] * n,
  59→        },
  60→        index=idx,
  61→    )
  62→
  63→
  64→@pytest.fixture
  65→def mock_store(tmp_path):
  66→    store = MagicMock()
  67→    df_aapl = _make_ohlcv(300, trend="up")
  68→    df_msft = _make_ohlcv(300, trend="up")
  69→    df_jpm  = _make_ohlcv(300, trend="up")
  70→
  71→    def get_bars_multi(symbols, start, end, timeframe="1d"):
  72→        mapping = {"AAPL": df_aapl, "MSFT": df_msft, "JPM": df_jpm}
  73→        return {s: mapping[s] for s in symbols if s in mapping}
  74→
  75→    store.get_bars_multi.side_effect = get_bars_multi
  76→    return store
  77→
  78→
  79→@pytest.fixture
  80→def mock_universe():
  81→    from mytrader.universe.models import SymbolMeta
  82→    universe = MagicMock()
  83→    universe.get_groups.return_value = {
  84→        "NDX_mid_vol": ["AAPL", "MSFT"],
  85→        "SPX_mid_vol": ["JPM"],
  86→    }
  87→
  88→    def get_meta(sym):
  89→        ndx = ["AAPL", "MSFT"]
  90→        return SymbolMeta(
  91→            symbol=sym,
  92→            index_membership=["NASDAQ100"] if sym in ndx else ["SP500"],
  93→            sector="Technology" if sym in ndx else "Financials",
  94→            market_cap_tier="large",
  95→            volatility_tier="mid",
  96→            group_id="NDX_mid_vol" if sym in ndx else "SPX_mid_vol",
  97→        )
  98→    universe.get_symbol_meta.side_effect = get_meta
  99→    return universe
 100→
 101→
 102→# ---------------------------------------------------------------------------
 103→# 单函数测试
 104→# ---------------------------------------------------------------------------
 105→
 106→class TestHelpers:
 107→
 108→    def test_compute_sharpe_positive(self):
 109→        """正向收益的 Sharpe > 0。"""
 110→        returns = pd.Series([0.001] * 252)
 111→        sharpe = _compute_sharpe(returns)
 112→        assert sharpe > 0
 113→
 114→    def test_compute_sharpe_zero_std(self):
 115→        """收益恒定（零方差）返回 0。"""
 116→        returns = pd.Series([0.0] * 100)
 117→        assert _compute_sharpe(returns) == 0.0
 118→
 119→    def test_compute_sharpe_empty(self):
 120→        assert _compute_sharpe(pd.Series([], dtype=float)) == 0.0
 121→
 122→    def test_portfolio_sharpe_from_results(self):
 123→        """等权组合 Sharpe 不等于算术平均 Sharpe（差异 > 1e-6）。"""
 124→        n = 252
 125→        r1 = pd.Series(np.random.normal(0.001, 0.01, n))   # 高收益高波动
 126→        r2 = pd.Series(np.random.normal(0.0005, 0.002, n)) # 低收益低波动
 127→
 128→        s1 = _compute_sharpe(r1)
 129→        s2 = _compute_sharpe(r2)
 130→        arithmetic_avg = (s1 + s2) / 2
 131→
 132→        results = [
 133→            SingleBacktestResult("SYM1", "s1", {}, s1, 10, 5, 60, 20, r1),
 134→            SingleBacktestResult("SYM2", "s2", {}, s2, 5, 3, 55, 15, r2),
 135→        ]
 136→        portfolio_sharpe = _portfolio_sharpe_from_results(results)
 137→
 138→        # 组合 Sharpe 与算术平均 Sharpe 应不同（这正是为什么要用组合方式）
 139→        diff = abs(portfolio_sharpe - arithmetic_avg)
 140→        assert diff > 1e-6, (
 141→            f"组合 Sharpe({portfolio_sharpe:.4f}) 与算术平均 Sharpe({arithmetic_avg:.4f}) "
 142→            f"差异应 >1e-6，否则说明实现有误"
 143→        )
 144→
 145→    # ── Sortino（迭代 #1 新增，Constitution L1 首要 KPI）─────────────────────
 146→
 147→    def test_compute_sortino_positive(self):
 148→        """正均值的收益序列 Sortino > 0。"""
 149→        returns = pd.Series([0.001, -0.0005, 0.002, -0.0003, 0.0015] * 60)
 150→        assert _compute_sortino(returns) > 0
 151→
 152→    def test_compute_sortino_empty(self):
 153→        """空序列返回 0。"""
 154→        assert _compute_sortino(pd.Series([], dtype=float)) == 0.0
 155→
 156→    def test_compute_sortino_no_downside_returns_zero(self):
 157→        """全正收益（无下行波动）→ 0.0（退化处理，与 _compute_sharpe 一致）。
 158→
 159→        理论上 Sortino 应为 +inf，但返回 0 保持可算术聚合 + 保守评估。
 160→        """
 161→        returns = pd.Series([0.001] * 100)   # 全正，无下行
 162→        assert _compute_sortino(returns) == 0.0
 163→
 164→    def test_compute_sortino_differs_from_sharpe_when_asymmetric(self):
 165→        """当上行/下行波动不对称时，Sortino ≠ Sharpe（这是引入 Sortino 的意义）。"""
 166→        # 大幅上行小波动 + 偶尔小幅下行：Sortino 应明显高于 Sharpe
 167→        np.random.seed(42)
 168→        upside = np.random.normal(0.003, 0.005, 200)   # 正均值的上行
 169→        downside_shocks = np.array([-0.01, -0.012, -0.008] * 3)  # 少量下行冲击
 170→        returns = pd.Series(np.concatenate([upside, downside_shocks]))
 171→
 172→        sharpe = _compute_sharpe(returns)
 173→        sortino = _compute_sortino(returns)
 174→        # Sortino 仅对下行惩罚 → 上行波动不计入分母 → Sortino > Sharpe
 175→        assert sortino > sharpe, (
 176→            f"非对称收益下 Sortino({sortino:.4f}) 应 > Sharpe({sharpe:.4f})，"
 177→            f"否则说明 Sortino 公式退化为 Sharpe"
 178→        )
 179→
 180→    def test_compute_sortino_known_value(self):
 181→        """已知值验算 Sortino 公式正确性。"""
 182→        # r = [0.01, 0.01, 0.01, -0.01]
 183→        # mean = 0.005; downside = [0,0,0,-0.01]; dd = sqrt(mean([0,0,0,0.0001])) = sqrt(0.000025) = 0.005
 184→        # Sortino = 0.005 / 0.005 * sqrt(252) = 15.8745...
 185→        returns = pd.Series([0.01, 0.01, 0.01, -0.01] * 25)   # 重复 25 次以满足 len>=5
 186→        expected = (0.005 / 0.005) * np.sqrt(252)
 187→        assert abs(_compute_sortino(returns) - expected) < 1e-6
 188→
 189→    def test_portfolio_sortino_from_results(self):
 190→        """等权组合 Sortino 不等于各标的 Sortino 算术平均（与 Sharpe 同理）。"""
 191→        n = 252
 192→        np.random.seed(0)
 193→        r1 = pd.Series(np.random.normal(0.001, 0.01, n))
 194→        r2 = pd.Series(np.random.normal(0.0005, 0.002, n))
 195→
 196→        s1 = _compute_sortino(r1)
 197→        s2 = _compute_sortino(r2)
 198→        arithmetic_avg = (s1 + s2) / 2
 199→
 200→        results = [
 201→
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py","limit":200,"offset":1045}
---
1045→class TestAlphaBasedTopKSelection:
1046→    """top-K 选择逻辑从 Sortino 改为 Alpha 的集成测试。"""
1047→
1048→    def test_top_k_selection_uses_alpha(self, tmp_path):
1049→        """top-K 排序使用 Alpha 而非 Sortino。
1050→
1051→        场景：策略 A 的 Sortino 高于 B，但 B 的 Alpha 高于 A。
1052→        应选择 B（高 alpha）而非 A（高 Sortino）。
1053→
1054→        构造方法：用 patch 拦截 _backtest_one，返回受控的 daily_returns。
1055→        """
1056→        from unittest.mock import patch
1057→
1058→        # 构造 SPY 数据：温和上涨（年化 ~10%）
1059→        n = 300
1060→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
1061→        spy_close = [100.0 * (1.0004 ** i) for i in range(n)]  # ~10% 年化
1062→        spy_df = pd.DataFrame({
1063→            "open": [c - 0.1 for c in spy_close],
1064→            "high": [c + 0.5 for c in spy_close],
1065→            "low": [c - 0.5 for c in spy_close],
1066→            "close": spy_close,
1067→            "volume": [1_000_000] * n,
1068→        }, index=idx)
1069→        spy_returns = spy_df["close"].pct_change().dropna()
1070→
1071→        # 策略 A (dual_ma): 低波动低收益 → 高 Sortino 但低 alpha
1072→        # 日均 0.0004（~10% 年化，与 SPY 持平 → alpha ≈ 0）
1073→        np.random.seed(42)
1074→        returns_a = pd.Series(
1075→            np.random.normal(0.0004, 0.002, n), index=idx
1076→        )
1077→        # 策略 B (rsi_mean_revert): 高波动高收益 → 低 Sortino 但高 alpha
1078→        # 日均 0.0011（~32% 年化，远超 SPY → alpha ≈ 22%）
1079→        returns_b = pd.Series(
1080→            np.random.normal(0.0011, 0.008, n), index=idx
1081→        )
1082→
1083→        # 验证测试前提：A 的 Sortino > B 的 Sortino，B 的 alpha > A 的 alpha
1084→        sortino_a = _compute_sortino(returns_a)
1085→        sortino_b = _compute_sortino(returns_b)
1086→        alpha_a = _compute_alpha(returns_a, spy_returns)
1087→        alpha_b = _compute_alpha(returns_b, spy_returns)
1088→        assert sortino_a > sortino_b, (
1089→            f"测试前提失败：A 的 Sortino({sortino_a:.4f}) 应 > B({sortino_b:.4f})"
1090→        )
1091→        assert alpha_b > alpha_a, (
1092→            f"测试前提失败：B 的 alpha({alpha_b:.4f}) 应 > A({alpha_a:.4f})"
1093→        )
1094→
1095→        # Mock _backtest_batch 返回受控结果（迭代 #10：_run_group 改用 batch）
1096→        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
1097→            results = []
1098→            for sym, df in data.items():
1099→                if df is None or df.empty or len(df) < 30:
1100→                    continue
1101→                if strategy_name == "dual_ma":
1102→                    results.append(SingleBacktestResult(
1103→                        sym, strategy_name, params, 1.0, 10.0, 5.0, 55.0, 10, returns_a
1104→                    ))
1105→                else:  # rsi_mean_revert
1106→                    results.append(SingleBacktestResult(
1107→                        sym, strategy_name, params, 1.0, 30.0, 8.0, 50.0, 10, returns_b
1108→                    ))
1109→            return results
1110→
1111→        # 构造 mock store：返回 SPY + 普通上涨数据
1112→        df_up = _make_ohlcv(n, trend="up")
1113→        store = MagicMock()
1114→
1115→        def get_bars_multi(symbols, start, end, timeframe="1d"):
1116→            mapping = {"AAPL": df_up, "SPY": spy_df}
1117→            return {s: mapping[s] for s in symbols if s in mapping}
1118→
1119→        store.get_bars_multi.side_effect = get_bars_multi
1120→
1121→        universe = MagicMock()
1122→        universe.get_groups.return_value = {"test_group": ["AAPL"]}
1123→
1124→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=1)
1125→
1126→        with patch(
1127→            "mytrader.backtest.matrix_backtest._backtest_batch",
1128→            side_effect=mock_backtest_batch,
1129→        ):
1130→            report = mb.run(
1131→                strategies=["dual_ma", "rsi_mean_revert"],
1132→                param_grids={
1133→                    "dual_ma": {"fast": [5], "slow": [20]},
1134→                    "rsi_mean_revert": {
1135→                        "period": [14], "oversold": [30], "overbought": [70]
1136→                    },
1137→                },
1138→            )
1139→
1140→        # 验证：选择了 rsi_mean_revert（高 alpha）而非 dual_ma（高 Sortino）
1141→        weights = report.groups["test_group"]
1142→        assert len(weights) == 1, f"top_k=1 应只选 1 个策略，实际 {len(weights)}"
1143→        assert weights[0]["strategy"] == "rsi_mean_revert", (
1144→            f"应选择高 alpha 的 rsi_mean_revert，"
1145→            f"实际选择了 {weights[0]['strategy']}（高 Sortino 的 dual_ma）"
1146→        )
1147→        # backtest_alpha 字段应反映 B 的高 alpha
1148→        assert weights[0]["backtest_alpha"] > 5.0, (
1149→            f"B 的 alpha 应 > 5%，实际 {weights[0]['backtest_alpha']:.4f}"
1150→        )
1151→
1152→    def test_sortino_filter_excludes_garbage(self, tmp_path):
1153→        """Sortino < 0.5 的候选被过滤（即使 alpha 高也不选）。
1154→
1155→        场景：构造一个 Sortino < 0.5 的"垃圾"策略 A，和一个 Sortino > 0.5 的正常策略 B。
1156→        即使 A 的 alpha 略高，也应被 Sortino 门槛排除。
1157→
1158→        注：由于 Sortino 门槛是 Tier 1 过滤，若无候选通过门槛，会触发 Tier 2 fallback
1159→        放宽门槛。本测试构造"至少有一个正常候选"的场景验证 Tier 1 正常工作。
1160→        """
1161→        from unittest.mock import patch
1162→
1163→        n = 300
1164→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
1165→        # SPY 温和上涨
1166→        spy_close = [100.0 * (1.0004 ** i) for i in range(n)]
1167→        spy_df = pd.DataFrame({
1168→            "open": [c - 0.1 for c in spy_close],
1169→            "high": [c + 0.5 for c in spy_close],
1170→            "low": [c - 0.5 for c in spy_close],
1171→            "close": spy_close,
1172→            "volume": [1_000_000] * n,
1173→        }, index=idx)
1174→        spy_returns = spy_df["close"].pct_change().dropna()
1175→
1176→        # 垃圾策略 A：极低 Sortino（高下行波动）+ 高 alpha（靠总体高收益）
1177→        # 构造大起大落的收益序列：均值高但下行波动大
1178→        np.random.seed(42)
1179→        returns_a = pd.Series(
1180→            np.concatenate([
1181→                np.random.normal(0.003, 0.015, 200),   # 高波动高收益
1182→                np.random.normal(-0.005, 0.01, 100),   # 大幅下行
1183→            ]),
1184→            index=idx,
1185→        )
1186→        # 正常策略 B：稳定收益，Sortino > 0.5
1187→        returns_b = pd.Series(
1188→            np.random.normal(0.0008, 0.003, n), index=idx
1189→        )
1190→
1191→        sortino_a = _compute_sortino(returns_a)
1192→        sortino_b = _compute_sortino(returns_b)
1193→        # 验证前提：A 的 Sortino < 0.5（垃圾），B 的 Sortino > 0.5（正常）
1194→        assert sortino_a < MIN_SORTINO_THRESHOLD, (
1195→            f"A 应为 Sortino < 0.5 的垃圾策略，实际 {sortino_a:.4f}"
1196→        )
1197→        assert sortino_b > MIN_SORTINO_THRESHOLD, (
1198→            f"B 应为 Sortino > 0.5 的正常策略，实际 {sortino_b:.4f}"
1199→        )
1200→
1201→        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
1202→            results = []
1203→            for sym, df in data.items():
1204→                if df is None or df.empty or len(df) < 30:
1205→                    continue
1206→                if strategy_name == "dual_ma":
1207→                    results.append(SingleBacktestResult(
1208→                        sym, strategy_name, params, 0.5, 15.0, 10.0, 50.0, 5, returns_a
1209→                    ))
1210→                else:  # rsi_mean_revert
1211→                    results.append(SingleBacktestResult(
1212→                        sym, strategy_name, params, 1.0, 20.0, 5.0, 55.0, 10, returns_b
1213→                    ))
1214→            return results
1215→
1216→        df_up = _make_ohlcv(n, trend="up")
1217→        store = MagicMock()
1218→        store.get_bars_multi.side_effect = lambda symbols, start, end, timeframe="1d": {
1219→            s: {"AAPL": df_up, "SPY": spy_df}[s] for s in symbols
1220→            if s in {"AAPL", "SPY"}
1221→        }
1222→
1223→        universe = MagicMock()
1224→        universe.get_groups.return_value = {"test_group": ["AAPL"]}
1225→
1226→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=1)
1227→        with patch(
1228→            "mytrader.backtest.matrix_backtest._backtest_batch",
1229→            side_effect=mock_backtest_batch,
1230→        ):
1231→            report = mb.run(
1232→                strategies=["dual_ma", "rsi_mean_revert"],
1233→                param_grids={
1234→                    "dual_ma": {"fast": [5], "slow": [20]},
1235→                    "rsi_mean_revert": {
1236→                        "period": [14], "oversold": [30], "overbought": [70]
1237→                    },
1238→                },
1239→            )
1240→
1241→        weights = report.groups["test_group"]
1242→        assert len(weights) == 1
1243→        # 应选择 rsi_mean_revert（Sortino > 0.5），排除 dual_ma（Sortino < 0.5）
1244→        assert weights[0]["strategy"] == "rsi_mean_revert", (
1245→
---
1045→class TestAlphaBasedTopKSelection:
1046→    """top-K 选择逻辑从 Sortino 改为 Alpha 的集成测试。"""
1047→
1048→    def test_top_k_selection_uses_alpha(self, tmp_path):
1049→        """top-K 排序使用 Alpha 而非 Sortino。
1050→
1051→        场景：策略 A 的 Sortino 高于 B，但 B 的 Alpha 高于 A。
1052→        应选择 B（高 alpha）而非 A（高 Sortino）。
1053→
1054→        构造方法：用 patch 拦截 _backtest_one，返回受控的 daily_returns。
1055→        """
1056→        from unittest.mock import patch
1057→
1058→        # 构造 SPY 数据：温和上涨（年化 ~10%）
1059→        n = 300
1060→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
1061→        spy_close = [100.0 * (1.0004 ** i) for i in range(n)]  # ~10% 年化
1062→        spy_df = pd.DataFrame({
1063→            "open": [c - 0.1 for c in spy_close],
1064→            "high": [c + 0.5 for c in spy_close],
1065→            "low": [c - 0.5 for c in spy_close],
1066→            "close": spy_close,
1067→            "volume": [1_000_000] * n,
1068→        }, index=idx)
1069→        spy_returns = spy_df["close"].pct_change().dropna()
1070→
1071→        # 策略 A (dual_ma): 低波动低收益 → 高 Sortino 但低 alpha
1072→        # 日均 0.0004（~10% 年化，与 SPY 持平 → alpha ≈ 0）
1073→        np.random.seed(42)
1074→        returns_a = pd.Series(
1075→            np.random.normal(0.0004, 0.002, n), index=idx
1076→        )
1077→        # 策略 B (rsi_mean_revert): 高波动高收益 → 低 Sortino 但高 alpha
1078→        # 日均 0.0011（~32% 年化，远超 SPY → alpha ≈ 22%）
1079→        returns_b = pd.Series(
1080→            np.random.normal(0.0011, 0.008, n), index=idx
1081→        )
1082→
1083→        # 验证测试前提：A 的 Sortino > B 的 Sortino，B 的 alpha > A 的 alpha
1084→        sortino_a = _compute_sortino(returns_a)
1085→        sortino_b = _compute_sortino(returns_b)
1086→        alpha_a = _compute_alpha(returns_a, spy_returns)
1087→        alpha_b = _compute_alpha(returns_b, spy_returns)
1088→        assert sortino_a > sortino_b, (
1089→            f"测试前提失败：A 的 Sortino({sortino_a:.4f}) 应 > B({sortino_b:.4f})"
1090→        )
1091→        assert alpha_b > alpha_a, (
1092→            f"测试前提失败：B 的 alpha({alpha_b:.4f}) 应 > A({alpha_a:.4f})"
1093→        )
1094→
1095→        # Mock _backtest_batch 返回受控结果（迭代 #10：_run_group 改用 batch）
1096→        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
1097→            results = []
1098→            for sym, df in data.items():
1099→                if df is None or df.empty or len(df) < 30:
1100→                    continue
1101→                if strategy_name == "dual_ma":
1102→                    results.append(SingleBacktestResult(
1103→                        sym, strategy_name, params, 1.0, 10.0, 5.0, 55.0, 10, returns_a
1104→                    ))
1105→                else:  # rsi_mean_revert
1106→                    results.append(SingleBacktestResult(
1107→                        sym, strategy_name, params, 1.0, 30.0, 8.0, 50.0, 10, returns_b
1108→                    ))
1109→            return results
1110→
1111→        # 构造 mock store：返回 SPY + 普通上涨数据
1112→        df_up = _make_ohlcv(n, trend="up")
1113→        store = MagicMock()
1114→
1115→        def get_bars_multi(symbols, start, end, timeframe="1d"):
1116→            mapping = {"AAPL": df_up, "SPY": spy_df}
1117→            return {s: mapping[s] for s in symbols if s in mapping}
1118→
1119→        store.get_bars_multi.side_effect = get_bars_multi
1120→
1121→        universe = MagicMock()
1122→        universe.get_groups.return_value = {"test_group": ["AAPL"]}
1123→
1124→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=1)
1125→
1126→        with patch(
1127→            "mytrader.backtest.matrix_backtest._backtest_batch",
1128→            side_effect=mock_backtest_batch,
1129→        ):
1130→            report = mb.run(
1131→                strategies=["dual_ma", "rsi_mean_revert"],
1132→                param_grids={
1133→                    "dual_ma": {"fast": [5], "slow": [20]},
1134→                    "rsi_mean_revert": {
1135→                        "period": [14], "oversold": [30], "overbought": [70]
1136→                    },
1137→                },
1138→            )
1139→
1140→        # 验证：选择了 rsi_mean_revert（高 alpha）而非 dual_ma（高 Sortino）
1141→        weights = report.groups["test_group"]
1142→        assert len(weights) == 1, f"top_k=1 应只选 1 个策略，实际 {len(weights)}"
1143→        assert weights[0]["strategy"] == "rsi_mean_revert", (
1144→            f"应选择高 alpha 的 rsi_mean_revert，"
1145→            f"实际选择了 {weights[0]['strategy']}（高 Sortino 的 dual_ma）"
1146→        )
1147→        # backtest_alpha 字段应反映 B 的高 alpha
1148→        assert weights[0]["backtest_alpha"] > 5.0, (
1149→            f"B 的 alpha 应 > 5%，实际 {weights[0]['backtest_alpha']:.4f}"
1150→        )
1151→
1152→    def test_sortino_filter_excludes_garbage(self, tmp_path):
1153→        """Sortino < 0.5 的候选被过滤（即使 alpha 高也不选）。
1154→
1155→        场景：构造一个 Sortino < 0.5 的"垃圾"策略 A，和一个 Sortino > 0.5 的正常策略 B。
1156→        即使 A 的 alpha 略高，也应被 Sortino 门槛排除。
1157→
1158→        注：由于 Sortino 门槛是 Tier 1 过滤，若无候选通过门槛，会触发 Tier 2 fallback
1159→        放宽门槛。本测试构造"至少有一个正常候选"的场景验证 Tier 1 正常工作。
1160→        """
1161→        from unittest.mock import patch
1162→
1163→        n = 300
1164→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
1165→        # SPY 温和上涨
1166→        spy_close = [100.0 * (1.0004 ** i) for i in range(n)]
1167→        spy_df = pd.DataFrame({
1168→            "open": [c - 0.1 for c in spy_close],
1169→            "high": [c + 0.5 for c in spy_close],
1170→            "low": [c - 0.5 for c in spy_close],
1171→            "close": spy_close,
1172→            "volume": [1_000_000] * n,
1173→        }, index=idx)
1174→        spy_returns = spy_df["close"].pct_change().dropna()
1175→
1176→        # 垃圾策略 A：极低 Sortino（高下行波动）+ 高 alpha（靠总体高收益）
1177→        # 构造大起大落的收益序列：均值高但下行波动大
1178→        np.random.seed(42)
1179→        returns_a = pd.Series(
1180→            np.concatenate([
1181→                np.random.normal(0.003, 0.015, 200),   # 高波动高收益
1182→                np.random.normal(-0.005, 0.01, 100),   # 大幅下行
1183→            ]),
1184→            index=idx,
1185→        )
1186→        # 正常策略 B：稳定收益，Sortino > 0.5
1187→        returns_b = pd.Series(
1188→            np.random.normal(0.0008, 0.003, n), index=idx
1189→        )
1190→
1191→        sortino_a = _compute_sortino(returns_a)
1192→        sortino_b = _compute_sortino(returns_b)
1193→        # 验证前提：A 的 Sortino < 0.5（垃圾），B 的 Sortino > 0.5（正常）
1194→        assert sortino_a < MIN_SORTINO_THRESHOLD, (
1195→            f"A 应为 Sortino < 0.5 的垃圾策略，实际 {sortino_a:.4f}"
1196→        )
1197→        assert sortino_b > MIN_SORTINO_THRESHOLD, (
1198→            f"B 应为 Sortino > 0.5 的正常策略，实际 {sortino_b:.4f}"
1199→        )
1200→
1201→        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
1202→            results = []
1203→            for sym, df in data.items():
1204→                if df is None or df.empty or len(df) < 30:
1205→                    continue
1206→                if strategy_name == "dual_ma":
1207→                    results.append(SingleBacktestResult(
1208→                        sym, strategy_name, params, 0.5, 15.0, 10.0, 50.0, 5, returns_a
1209→                    ))
1210→                else:  # rsi_mean_revert
1211→                    results.append(SingleBacktestResult(
1212→                        sym, strategy_name, params, 1.0, 20.0, 5.0, 55.0, 10, returns_b
1213→                    ))
1214→            return results
1215→
1216→        df_up = _make_ohlcv(n, trend="up")
1217→        store = MagicMock()
1218→        store.get_bars_multi.side_effect = lambda symbols, start, end, timeframe="1d": {
1219→            s: {"AAPL": df_up, "SPY": spy_df}[s] for s in symbols
1220→            if s in {"AAPL", "SPY"}
1221→        }
1222→
1223→        universe = MagicMock()
1224→        universe.get_groups.return_value = {"test_group": ["AAPL"]}
1225→
1226→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=1)
1227→        with patch(
1228→            "mytrader.backtest.matrix_backtest._backtest_batch",
1229→            side_effect=mock_backtest_batch,
1230→        ):
1231→            report = mb.run(
1232→                strategies=["dual_ma", "rsi_mean_revert"],
1233→                param_grids={
1234→                    "dual_ma": {"fast": [5], "slow": [20]},
1235→                    "rsi_mean_revert": {
1236→                        "period": [14], "oversold": [30], "overbought": [70]
1237→                    },
1238→                },
1239→            )
1240→
1241→        weights = report.groups["test_group"]
1242→        assert len(weights) == 1
1243→        # 应选择 rsi_mean_revert（Sortino > 0.5），排除 dual_ma（Sortino < 0.5）
1244→        assert weights[0]["strategy"] == "rsi_mean_revert", (
1245→
---
现在
---
让我
---
查看
---
 Test
---
DD
---
Constraint
---
 类
---
以
---
了解
---
 fallback
---
 pattern
---
 
---
测试
---
，
---
并
---
查看
---
 `
---
test
---
_f
---
allback
---
_when
---
_no
---
_dd
---
_com
---
pliant
---
`
---
 的
---
内容
---
：
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py","limit":200,"offset":593}
---
 593→class TestDDConstraint:
 594→    """P0: 修复 NDX_high_vol DD 超标（Gate 1 阻塞项）。"""
 595→
 596→    def test_dd_constrained_field_exists_in_group_result(self, mock_store, mock_universe):
 597→        """GroupBacktestResult 含 dd_constrained bool 字段，默认 False。"""
 598→        from mytrader.backtest.matrix_backtest import GroupBacktestResult
 599→        gr = GroupBacktestResult(
 600→            group_id="test", strategy="dual_ma", params={},
 601→            portfolio_sharpe=1.0, avg_total_return_pct=10.0,
 602→            avg_max_drawdown_pct=-5.0, avg_win_rate_pct=55.0, symbol_count=3,
 603→        )
 604→        assert hasattr(gr, "dd_constrained"), "GroupBacktestResult 必须有 dd_constrained 字段"
 605→        assert gr.dd_constrained is False, "dd_constrained 默认应为 False"
 606→
 607→    def test_compliant_candidates_selected_by_sortino(self, tmp_path):
 608→        """P0 case 1: 有合规候选时，按 Sortino 降序选 top-K（不选 DD 超标的候选）。
 609→
 610→        场景：3 个候选，其中 2 个 DD=10%（合规）、1 个 DD=25%（超标）。
 611→        虽然 DD=25% 的候选 Sortino 更高，但 DD 约束应将其排除。
 612→        """
 613→        # 构造 mock store：返回一组上涨数据，回测 DD 自然 < 20%
 614→        store = MagicMock()
 615→        df = _make_ohlcv(300, trend="up")
 616→        store.get_bars_multi.side_effect = lambda symbols, start, end, timeframe="1d": {
 617→            s: df.copy() for s in symbols
 618→        }
 619→
 620→        universe = MagicMock()
 621→        universe.get_groups.return_value = {"test_group": ["AAPL", "MSFT"]}
 622→
 623→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
 624→        # 用两个策略（都合规）测试 top-K 选择
 625→        report = mb.run(
 626→            strategies=["dual_ma", "rsi_mean_revert"],
 627→            param_grids={
 628→                "dual_ma": {"fast": [5], "slow": [20]},
 629→                "rsi_mean_revert": {"period": [14], "oversold": [30], "overbought": [70]},
 630→            },
 631→            output_file=tmp_path / "weights.json",
 632→        )
 633→
 634→        # 验证：有合规候选时 dd_constrained=False
 635→        for gid, weights in report.groups.items():
 636→            for w in weights:
 637→                assert "dd_constrained" in w, f"{gid}: 缺少 dd_constrained 字段"
 638→                assert w["dd_constrained"] is False, (
 639→                    f"{gid}: 有合规候选时 dd_constrained 应为 False，"
 640→                    f"实际 {w['dd_constrained']}（候选 DD 均在阈值内）"
 641→                )
 642→
 643→    def test_fallback_when_no_compliant_candidates(self, tmp_path):
 644→        """P0 case 2: 无合规候选时 fallback — 按 DD 升序选 top-K，标记 dd_constrained=True。
 645→
 646→        场景：构造 rsi_mean_revert 会买入后持续下跌的数据，让 portfolio DD >> 20%。
 647→        使用 rsi_mean_revert 策略：先压低 RSI（超卖触发买入），买入后价格持续大幅下跌。
 648→        验证：top-K 仍产出（不抛异常），且 dd_constrained=True。
 649→
 650→        注：dual_ma 是趋势跟踪策略，"先涨后跌"场景下会在下跌初期平仓，DD 不易超 20%。
 651→        rsi_mean_revert 在 oversold 买入后若价格持续跌，会持续持仓，DD 显著更高。
 652→        """
 653→        store = MagicMock()
 654→        # 构造：先压低 RSI（200天缓慢下跌触发超卖买入信号），
 655→        # 然后买入后价格急速崩溃下跌 60%，造成巨大持仓损失
 656→        n = 400
 657→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
 658→        close = (
 659→            [100.0 * (1 - 0.002 * i) for i in range(200)]   # 缓慢下跌压低RSI
 660→            + [60.0 * (1 - 0.005 * (i - 200)) for i in range(200, n)]  # 急速崩溃
 661→        )
 662→        close = [max(c, 1.0) for c in close]  # 防止价格为负
 663→        df_crash = pd.DataFrame(
 664→            {
 665→                "open":   [c - 0.3 for c in close],
 666→                "high":   [c + 0.5 for c in close],
 667→                "low":    [c - 0.5 for c in close],
 668→                "close":  close,
 669→                "volume": [1_000_000] * n,
 670→            },
 671→            index=idx,
 672→        )
 673→        store.get_bars_multi.side_effect = lambda symbols, start, end, timeframe="1d": {
 674→            s: df_crash.copy() for s in symbols
 675→        }
 676→
 677→        universe = MagicMock()
 678→        universe.get_groups.return_value = {"volatile_group": ["AAPL", "MSFT"]}
 679→
 680→        # 使用 rsi_mean_revert，超卖买入后持续下跌，确保 DD >> 20%
 681→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
 682→        report = mb.run(
 683→            strategies=["rsi_mean_revert"],
 684→            param_grids={"rsi_mean_revert": {
 685→                "period": [14], "oversold": [35], "overbought": [65]
 686→            }},
 687→            output_file=tmp_path / "weights_fallback.json",
 688→        )
 689→
 690→        # 若产生权重，验证：fallback 触发（dd_constrained=True）或无权重（极端无交易场景）
 691→        has_weights = any(weights for weights in report.groups.values() if weights)
 692→        if has_weights:
 693→            for gid, weights in report.groups.items():
 694→                for w in weights:
 695→                    if w.get("backtest_max_drawdown", 0) > 20.0:
 696→                        assert w["dd_constrained"] is True, (
 697→                            f"{gid}: DD={w['backtest_max_drawdown']:.1f}% > 20% "
 698→                            f"但 dd_constrained 为 False"
 699→                        )
 700→
 701→    def test_output_file_contains_dd_constrained_field(self, mock_store, mock_universe, tmp_path):
 702→        """P0 case 3: strategy_weights.json 每个权重条目含 dd_constrained 字段。"""
 703→        output = tmp_path / "weights_dd_constrained.json"
 704→        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)
 705→        mb.run(
 706→            strategies=["dual_ma"],
 707→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 708→            output_file=output,
 709→        )
 710→        data = json.loads(output.read_text())
 711→        for gid, weights in data["groups"].items():
 712→            for w in weights:
 713→                assert "dd_constrained" in w, (
 714→                    f"{gid}: 权重条目缺少 dd_constrained 字段，"
 715→                    f"实际 keys={list(w.keys())}"
 716→                )
 717→                assert isinstance(w["dd_constrained"], bool), (
 718→                    f"{gid}: dd_constrained 应为 bool，"
 719→                    f"实际 {type(w['dd_constrained'])}"
 720→                )
 721→
 722→    def test_max_drawdown_threshold_is_20(self):
 723→        """Constitution L1: MAX_PORTFOLIO_DRAWDOWN_PCT = 20.0（硬约束）。"""
 724→        assert MAX_PORTFOLIO_DRAWDOWN_PCT == 20.0, (
 725→            f"MAX_PORTFOLIO_DRAWDOWN_PCT 应为 20.0 (Constitution L1)，"
 726→            f"实际 {MAX_PORTFOLIO_DRAWDOWN_PCT}"
 727→        )
 728→
 729→
 730→# ---------------------------------------------------------------------------
 731→# 迭代 #3 P1 新增：Walk-Forward 4 轮验证
 732→# ---------------------------------------------------------------------------
 733→
 734→class TestWalkForward:
 735→    """P1: Walk-Forward 4 轮验证（Constitution L7 流水线硬要求）。"""
 736→
 737→    def test_walk_forward_round_dataclass(self):
 738→        """WalkForwardRound dataclass 字段完整 + passed 判定正确。"""
 739→        from datetime import date as _date
 740→        r = WalkForwardRound(
 741→            round_num=1,
 742→            train_start=_date(2021, 7, 2),
 743→            train_end=_date(2023, 1, 2),
 744→            val_start=_date(2023, 1, 2),
 745→            val_end=_date(2023, 7, 2),
 746→            val_sortino=1.5,
 747→            val_max_dd=10.0,
 748→            passed=True,
 749→        )
 750→        assert r.round_num == 1
 751→        assert r.train_start == _date(2021, 7, 2)
 752→        assert r.val_end == _date(2023, 7, 2)
 753→        assert r.val_sortino == 1.5
 754→        assert r.val_max_dd == 10.0
 755→        assert r.passed is True
 756→
 757→    def test_walk_forward_round_passed_threshold(self):
 758→        """passed = val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD (15%)。"""
 759→        from datetime import date as _date
 760→        # DD = 15.0 → passed (边界)
 761→        r_boundary = WalkForwardRound(
 762→            round_num=1,
 763→            train_start=_date(2021, 1, 1), train_end=_date(2023, 1, 1),
 764→            val_start=_date(2023, 1, 1), val_end=_date(2023, 7, 1),
 765→            val_sortino=1.0, val_max_dd=15.0, passed=True,
 766→        )
 767→        assert r_boundary.passed is True
 768→        assert WALK_FORWARD_VAL_DD_THRESHOLD == 15.0, (
 769→            f"WF 验证 DD 门槛应为 15.0%，实际 {WALK_FORWARD_VAL_DD_THRESHOLD}"
 770→        )
 771→
 772→        # DD = 15.01 → not passed
 773→        r_fail = WalkForwardRound(
 774→            round_num=2,
 775→            train_start=_date(2021, 1, 1), train_end=_date(2023, 1, 1),
 776→            val_start=_date(2023, 1, 1), val_end=_date(2023, 7, 1),
 777→            val_sortino=1.0, val_max_dd=15.01, passed=False,
 778→        )
 779→        assert r_fail.passed is False
 780→
 781→    def test_walk_forward_report_dataclass(self):
 782→        """WalkForwardReport: pass_all_rounds + max_val_dd 计算正确。"""
 783→        from datetime import date as _date
 784→        rounds = [
 785→            WalkForwardRound(1, _date(2021, 1, 1), _date(2023, 1, 1),
 786→                             _date(2023, 1, 1), _date(2023, 7, 1), 1.0, 10.0, True),
 787→            WalkForwardRound(2, _date(2021, 7, 1), _date(2023, 7, 1),
 788→                             _date(2023, 7, 1), _date(2024, 1, 1), 0.8, 12.0, True),
 789→            WalkForwardRound(3, _date(2022, 1, 1), _date(2024, 1, 1),
 790→                             _date(2024, 1, 1), _date(2024, 7, 1), 1.2, 8.0, True),
 791→            WalkForwardRound(4, _date(2022, 7, 1), _date(2024, 7, 1),
 792→                             _date(2024, 7, 1), _date(2025, 1, 1), 0.9, 14.0, True),
 793→
---
 593→class TestDDConstraint:
 594→    """P0: 修复 NDX_high_vol DD 超标（Gate 1 阻塞项）。"""
 595→
 596→    def test_dd_constrained_field_exists_in_group_result(self, mock_store, mock_universe):
 597→        """GroupBacktestResult 含 dd_constrained bool 字段，默认 False。"""
 598→        from mytrader.backtest.matrix_backtest import GroupBacktestResult
 599→        gr = GroupBacktestResult(
 600→            group_id="test", strategy="dual_ma", params={},
 601→            portfolio_sharpe=1.0, avg_total_return_pct=10.0,
 602→            avg_max_drawdown_pct=-5.0, avg_win_rate_pct=55.0, symbol_count=3,
 603→        )
 604→        assert hasattr(gr, "dd_constrained"), "GroupBacktestResult 必须有 dd_constrained 字段"
 605→        assert gr.dd_constrained is False, "dd_constrained 默认应为 False"
 606→
 607→    def test_compliant_candidates_selected_by_sortino(self, tmp_path):
 608→        """P0 case 1: 有合规候选时，按 Sortino 降序选 top-K（不选 DD 超标的候选）。
 609→
 610→        场景：3 个候选，其中 2 个 DD=10%（合规）、1 个 DD=25%（超标）。
 611→        虽然 DD=25% 的候选 Sortino 更高，但 DD 约束应将其排除。
 612→        """
 613→        # 构造 mock store：返回一组上涨数据，回测 DD 自然 < 20%
 614→        store = MagicMock()
 615→        df = _make_ohlcv(300, trend="up")
 616→        store.get_bars_multi.side_effect = lambda symbols, start, end, timeframe="1d": {
 617→            s: df.copy() for s in symbols
 618→        }
 619→
 620→        universe = MagicMock()
 621→        universe.get_groups.return_value = {"test_group": ["AAPL", "MSFT"]}
 622→
 623→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
 624→        # 用两个策略（都合规）测试 top-K 选择
 625→        report = mb.run(
 626→            strategies=["dual_ma", "rsi_mean_revert"],
 627→            param_grids={
 628→                "dual_ma": {"fast": [5], "slow": [20]},
 629→                "rsi_mean_revert": {"period": [14], "oversold": [30], "overbought": [70]},
 630→            },
 631→            output_file=tmp_path / "weights.json",
 632→        )
 633→
 634→        # 验证：有合规候选时 dd_constrained=False
 635→        for gid, weights in report.groups.items():
 636→            for w in weights:
 637→                assert "dd_constrained" in w, f"{gid}: 缺少 dd_constrained 字段"
 638→                assert w["dd_constrained"] is False, (
 639→                    f"{gid}: 有合规候选时 dd_constrained 应为 False，"
 640→                    f"实际 {w['dd_constrained']}（候选 DD 均在阈值内）"
 641→                )
 642→
 643→    def test_fallback_when_no_compliant_candidates(self, tmp_path):
 644→        """P0 case 2: 无合规候选时 fallback — 按 DD 升序选 top-K，标记 dd_constrained=True。
 645→
 646→        场景：构造 rsi_mean_revert 会买入后持续下跌的数据，让 portfolio DD >> 20%。
 647→        使用 rsi_mean_revert 策略：先压低 RSI（超卖触发买入），买入后价格持续大幅下跌。
 648→        验证：top-K 仍产出（不抛异常），且 dd_constrained=True。
 649→
 650→        注：dual_ma 是趋势跟踪策略，"先涨后跌"场景下会在下跌初期平仓，DD 不易超 20%。
 651→        rsi_mean_revert 在 oversold 买入后若价格持续跌，会持续持仓，DD 显著更高。
 652→        """
 653→        store = MagicMock()
 654→        # 构造：先压低 RSI（200天缓慢下跌触发超卖买入信号），
 655→        # 然后买入后价格急速崩溃下跌 60%，造成巨大持仓损失
 656→        n = 400
 657→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
 658→        close = (
 659→            [100.0 * (1 - 0.002 * i) for i in range(200)]   # 缓慢下跌压低RSI
 660→            + [60.0 * (1 - 0.005 * (i - 200)) for i in range(200, n)]  # 急速崩溃
 661→        )
 662→        close = [max(c, 1.0) for c in close]  # 防止价格为负
 663→        df_crash = pd.DataFrame(
 664→            {
 665→                "open":   [c - 0.3 for c in close],
 666→                "high":   [c + 0.5 for c in close],
 667→                "low":    [c - 0.5 for c in close],
 668→                "close":  close,
 669→                "volume": [1_000_000] * n,
 670→            },
 671→            index=idx,
 672→        )
 673→        store.get_bars_multi.side_effect = lambda symbols, start, end, timeframe="1d": {
 674→            s: df_crash.copy() for s in symbols
 675→        }
 676→
 677→        universe = MagicMock()
 678→        universe.get_groups.return_value = {"volatile_group": ["AAPL", "MSFT"]}
 679→
 680→        # 使用 rsi_mean_revert，超卖买入后持续下跌，确保 DD >> 20%
 681→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
 682→        report = mb.run(
 683→            strategies=["rsi_mean_revert"],
 684→            param_grids={"rsi_mean_revert": {
 685→                "period": [14], "oversold": [35], "overbought": [65]
 686→            }},
 687→            output_file=tmp_path / "weights_fallback.json",
 688→        )
 689→
 690→        # 若产生权重，验证：fallback 触发（dd_constrained=True）或无权重（极端无交易场景）
 691→        has_weights = any(weights for weights in report.groups.values() if weights)
 692→        if has_weights:
 693→            for gid, weights in report.groups.items():
 694→                for w in weights:
 695→                    if w.get("backtest_max_drawdown", 0) > 20.0:
 696→                        assert w["dd_constrained"] is True, (
 697→                            f"{gid}: DD={w['backtest_max_drawdown']:.1f}% > 20% "
 698→                            f"但 dd_constrained 为 False"
 699→                        )
 700→
 701→    def test_output_file_contains_dd_constrained_field(self, mock_store, mock_universe, tmp_path):
 702→        """P0 case 3: strategy_weights.json 每个权重条目含 dd_constrained 字段。"""
 703→        output = tmp_path / "weights_dd_constrained.json"
 704→        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)
 705→        mb.run(
 706→            strategies=["dual_ma"],
 707→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 708→            output_file=output,
 709→        )
 710→        data = json.loads(output.read_text())
 711→        for gid, weights in data["groups"].items():
 712→            for w in weights:
 713→                assert "dd_constrained" in w, (
 714→                    f"{gid}: 权重条目缺少 dd_constrained 字段，"
 715→                    f"实际 keys={list(w.keys())}"
 716→                )
 717→                assert isinstance(w["dd_constrained"], bool), (
 718→                    f"{gid}: dd_constrained 应为 bool，"
 719→                    f"实际 {type(w['dd_constrained'])}"
 720→                )
 721→
 722→    def test_max_drawdown_threshold_is_20(self):
 723→        """Constitution L1: MAX_PORTFOLIO_DRAWDOWN_PCT = 20.0（硬约束）。"""
 724→        assert MAX_PORTFOLIO_DRAWDOWN_PCT == 20.0, (
 725→            f"MAX_PORTFOLIO_DRAWDOWN_PCT 应为 20.0 (Constitution L1)，"
 726→            f"实际 {MAX_PORTFOLIO_DRAWDOWN_PCT}"
 727→        )
 728→
 729→
 730→# ---------------------------------------------------------------------------
 731→# 迭代 #3 P1 新增：Walk-Forward 4 轮验证
 732→# ---------------------------------------------------------------------------
 733→
 734→class TestWalkForward:
 735→    """P1: Walk-Forward 4 轮验证（Constitution L7 流水线硬要求）。"""
 736→
 737→    def test_walk_forward_round_dataclass(self):
 738→        """WalkForwardRound dataclass 字段完整 + passed 判定正确。"""
 739→        from datetime import date as _date
 740→        r = WalkForwardRound(
 741→            round_num=1,
 742→            train_start=_date(2021, 7, 2),
 743→            train_end=_date(2023, 1, 2),
 744→            val_start=_date(2023, 1, 2),
 745→            val_end=_date(2023, 7, 2),
 746→            val_sortino=1.5,
 747→            val_max_dd=10.0,
 748→            passed=True,
 749→        )
 750→        assert r.round_num == 1
 751→        assert r.train_start == _date(2021, 7, 2)
 752→        assert r.val_end == _date(2023, 7, 2)
 753→        assert r.val_sortino == 1.5
 754→        assert r.val_max_dd == 10.0
 755→        assert r.passed is True
 756→
 757→    def test_walk_forward_round_passed_threshold(self):
 758→        """passed = val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD (15%)。"""
 759→        from datetime import date as _date
 760→        # DD = 15.0 → passed (边界)
 761→        r_boundary = WalkForwardRound(
 762→            round_num=1,
 763→            train_start=_date(2021, 1, 1), train_end=_date(2023, 1, 1),
 764→            val_start=_date(2023, 1, 1), val_end=_date(2023, 7, 1),
 765→            val_sortino=1.0, val_max_dd=15.0, passed=True,
 766→        )
 767→        assert r_boundary.passed is True
 768→        assert WALK_FORWARD_VAL_DD_THRESHOLD == 15.0, (
 769→            f"WF 验证 DD 门槛应为 15.0%，实际 {WALK_FORWARD_VAL_DD_THRESHOLD}"
 770→        )
 771→
 772→        # DD = 15.01 → not passed
 773→        r_fail = WalkForwardRound(
 774→            round_num=2,
 775→            train_start=_date(2021, 1, 1), train_end=_date(2023, 1, 1),
 776→            val_start=_date(2023, 1, 1), val_end=_date(2023, 7, 1),
 777→            val_sortino=1.0, val_max_dd=15.01, passed=False,
 778→        )
 779→        assert r_fail.passed is False
 780→
 781→    def test_walk_forward_report_dataclass(self):
 782→        """WalkForwardReport: pass_all_rounds + max_val_dd 计算正确。"""
 783→        from datetime import date as _date
 784→        rounds = [
 785→            WalkForwardRound(1, _date(2021, 1, 1), _date(2023, 1, 1),
 786→                             _date(2023, 1, 1), _date(2023, 7, 1), 1.0, 10.0, True),
 787→            WalkForwardRound(2, _date(2021, 7, 1), _date(2023, 7, 1),
 788→                             _date(2023, 7, 1), _date(2024, 1, 1), 0.8, 12.0, True),
 789→            WalkForwardRound(3, _date(2022, 1, 1), _date(2024, 1, 1),
 790→                             _date(2024, 1, 1), _date(2024, 7, 1), 1.2, 8.0, True),
 791→            WalkForwardRound(4, _date(2022, 7, 1), _date(2024, 7, 1),
 792→                             _date(2024, 7, 1), _date(2025, 1, 1), 0.9, 14.0, True),
 793→
---
现在
---
让我
---
检查
---
一下
---
 `
---
Single
---
Back
---
test
---
Result
---
`
---
 
---
构
---
造
---
函数
---
的
---
调用
---
情况
---
——
---
我
---
需要
---
知道
---
在
---
哪些
---
地方
---
构建
---
了
---
带有
---
位置
---
参数
---
的结果
---
，
---
以便
---
我
---
添加
---
一个
---
新
---
字段
---
时
---
，
---
不会
---
破坏
---
需要
---
关键字
---
参数
---
的情况
---
：
---
{"output_mode":"files_with_matches","path":"/Users/rickouyang/Github/trade-tools/mytrader","pattern":"SingleBacktestResult\\("}
---
["/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py","/Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py"]
---
["/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py","/Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py"]
---
{"-n":true,"output_mode":"content","path":"/Users/rickouyang/Github/trade-tools/mytrader","pattern":"SingleBacktestResult\\("}
---
["/Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py:376:        return SingleBacktestResult(","/Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py:528:            results.append(SingleBacktestResult(","/Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py:826:                wrapper = [SingleBacktestResult(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:133:            SingleBacktestResult(\"SYM1\", \"s1\", {}, s1, 10, 5, 60, 20, r1),","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:134:            SingleBacktestResult(\"SYM2\", \"s2\", {}, s2, 5, 3, 55, 15, r2),","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:201:            SingleBacktestResult(\"SYM1\", \"s1\", {}, 0.0, 0, 0, 0, 0, r1),","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:202:            SingleBacktestResult(\"SYM2\", \"s2\", {}, 0.0, 0, 0, 0, 0, r2),","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:266:        results = [SingleBacktestResult(\"S1\", \"s\", {}, 0.0, 0, 0, 0, 0, r)]","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:279:        results = [SingleBacktestResult(\"S1\", \"s\", {}, 0.0, 0, 0, 0, 0, returns)]","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:293:        results = [SingleBacktestResult(\"S1\", \"s\", {}, 0.0, 0, 0, 0, 0, r)]","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1024:            SingleBacktestResult(\"S1\", \"s\", {}, 0.0, 0, 0, 0, 0, r1),","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1025:            SingleBacktestResult(\"S2\", \"s\", {}, 0.0, 0, 0, 0, 0, r2),","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1102:                    results.append(SingleBacktestResult(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1106:                    results.append(SingleBacktestResult(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1207:                    results.append(SingleBacktestResult(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1211:                    results.append(SingleBacktestResult(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1348:                results.append(SingleBacktestResult(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1535:                    results.append(SingleBacktestResult(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1539:                    results.append(SingleBacktestResult(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1594:        results_a = [SingleBacktestResult(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1597:        results_b = [SingleBacktestResult(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1625:        results_a = [SingleBacktestResult(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1628:        results_b = [SingleBacktestResult(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1649:        results = [SingleBacktestResult("]
---
["/Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py:376:        return SingleBacktestResult(","/Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py:528:            results.append(SingleBacktestResult(","/Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py:826:                wrapper = [SingleBacktestResult(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:133:            SingleBacktestResult(\"SYM1\", \"s1\", {}, s1, 10, 5, 60, 20, r1),","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:134:            SingleBacktestResult(\"SYM2\", \"s2\", {}, s2, 5, 3, 55, 15, r2),","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:201:            SingleBacktestResult(\"SYM1\", \"s1\", {}, 0.0, 0, 0, 0, 0, r1),","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:202:            SingleBacktestResult(\"SYM2\", \"s2\", {}, 0.0, 0, 0, 0, 0, r2),","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:266:        results = [SingleBacktestResult(\"S1\", \"s\", {}, 0.0, 0, 0, 0, 0, r)]","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:279:        results = [SingleBacktestResult(\"S1\", \"s\", {}, 0.0, 0, 0, 0, 0, returns)]","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:293:        results = [SingleBacktestResult(\"S1\", \"s\", {}, 0.0, 0, 0, 0, 0, r)]","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1024:            SingleBacktestResult(\"S1\", \"s\", {}, 0.0, 0, 0, 0, 0, r1),","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1025:            SingleBacktestResult(\"S2\", \"s\", {}, 0.0, 0, 0, 0, 0, r2),","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1102:                    results.append(SingleBacktestResult(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1106:                    results.append(SingleBacktestResult(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1207:                    results.append(SingleBacktestResult(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1211:                    results.append(SingleBacktestResult(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1348:                results.append(SingleBacktestResult(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1535:                    results.append(SingleBacktestResult(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1539:                    results.append(SingleBacktestResult(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1594:        results_a = [SingleBacktestResult(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1597:        results_b = [SingleBacktestResult(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1625:        results_a = [SingleBacktestResult(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1628:        results_b = [SingleBacktestResult(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1649:        results = [SingleBacktestResult("]
---
Good
---
.
---
 Now
---
 I
---
 have
---
 all
---
 the
---
 info
---
 I
---
 need
---
.
---
 Let
---
 me
---
 also
---
 verify
---
 the
---
 test
---
_batch
---
_back
---
test
---
.py
---
 `_
---
assert
---
_results
---
_match
---
`
---
 function
---
 so
---
 I
---
 can
---
 extend
---
 it
---
 for
---
 `
---
closed
---
_tr
---
ades
---
`.
---
 Let
---
 me
---
 also
---
 check
---
 the
---
 design
---
 doc
---
:
---
现在
---
让我
---
检查
---
一下
---
需要
---
更新的
---
设计
---
文档
---
：
---
{"command":"ls /Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md && wc -l /Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md","description":"Check design doc exists"}
---
Check design doc exists
---
Command: ls /Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md && wc -l /Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md
Stdout: /Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md
     506 /Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"command":"ls /Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md /Users/rickouyang/Github/trade-tools/alignment/decision_log.md 2>&1 | head -5","description":"Check alignment files"}
---
Check alignment files
---
Command: ls /Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md /Users/rickouyang/Github/trade-tools/alignment/decision_log.md 2>&1 | head -5
Stdout: /Users/rickouyang/Github/trade-tools/alignment/decision_log.md
/Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"command":"tail -50 /Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md","description":"Check iteration trajectory format"}
---
Check iteration trajectory format
---
Command: tail -50 /Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md
Stdout: - `sortino` 严格一致（从 daily_returns 派生）
- `total_trades` 严格一致

### Constitution 合规
- ✅ 未突破 DD 20% 约束（DD 过滤逻辑完全不变）
- ✅ 测试覆盖率提升（+24 测试，602 → 626）
- ✅ 未修改策略代码 / 指标代码 / Alpha 排序逻辑（迭代 #9 改动不动）
- ✅ 未缩短回测窗口（仍 5 年）
- ✅ 决策可解释（batch 与 single 数值一致，top-K 选择结果不变）
- ✅ 未引入 RL / 未引入不安全依赖
- ✅ 未触发真实交易
- ✅ 文档与代码同步（07-backtest-module.md + CODEBUDDY.md + trajectory）

### Experience Learned
- **vectorbt 矩阵化是核心优化**：一次 `from_signals` 处理 N 个标的比 N 次单标的调用快得多，且 vbt 内部并行计算
- **`pf[sym]` 提取 per-symbol 结果**：vbt 1.0+ 的列分组语义保证每列独立结算 P&L，stats 提取与单标的一致
- **NaN 对齐处理**：`pd.DataFrame(dict)` 自动 outer-join 索引，vbt 对 NaN close 内部处理为"不交易"。美股实际场景中所有标的共享交易日历，日期对齐天然成立
- **mock 测试需要更新**：当被测函数的内部实现改变（从 `_backtest_one` 改为 `_backtest_batch`），mock patch 路径也需要同步更新。这提醒 mock 是实现耦合的，应谨慎使用
- **loguru 日志捕获**：pytest 的 `caplog` fixture 不捕获 loguru 日志，需用 `logger.add(lambda m: msgs.append(str(m)), level=...)` 模式
- **安全 fallback 设计**：batch 路径有异常时退化为 `_backtest_one` 逐标的回测，保证回测不中断（虽然性能下降，但功能正确）

### 后续建议
1. **性能验证**（Meta-Agent 验收阶段）：运行小规模 reoptimize（1 个组），对比新旧耗时。预期单组从 ~6 分钟降到 < 1 分钟
2. **完整 reoptimize 测试**：验证 4 小时 → 预期 15-30 分钟
3. **joblib 并行**（spec §3 明确不做）：batch 验证稳定后，可考虑组间并行（6 组并行）
4. **进一步优化**：vbt 支持 `param_grid` 内置参数网格搜索，未来可考虑用 vbt 原生网格替代 for-params 循环

### L7 流水线状态
```
✅ Backtest (≥5年, alpha-based selection, batch-optimized)
✅ Walk-Forward (4轮, 自动继承 alpha 排序, batch-optimized)
✅ Portfolio Backtest | ✅ Paper Trading Integrity
✅ Harness Reliability | ✅ SignalRanker Sortino Priority
✅ Strategy Diversity (5 策略 pool)
✅ Alpha-Based Selection (迭代 #9 完成)
🔄 Batch Backtest Optimization (迭代 #10 完成，待 --reoptimize 性能验证)
⬜ Paper Trade ≥1月 | ⬜ Live
```

---

> **Orchestrator 验证记录** (自动追加)
> - 迭代状态: passed
> - 测试: 0 passed, 0 failed
> - 违规: 0 条
> - 高风险文件: 0 个
> - 测试数变化: 602 → 626
> - CodeBuddy 自行更新了 trajectory ✅

---

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"command":"grep -n \"^## \" /Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md | tail -15","description":"Find iteration section headers"}
---
Find iteration section headers
---
Command: grep -n "^## " /Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md | tail -15
Stdout: 2:## 迭代 #0 — 读取 mytrader/backtest/runner.py 的代码并用一句话总结它的功能
32:## 迭代 #1 — 策略名 bug 修复 + Sortino 指标引入
95:## 迭代 #2 — NaN 安全 + Portfolio DD + 参数网格扩展
192:## Meta-Agent 评估（迭代 #2）
260:## 迭代 #3 — P0 DD 约束 + P1 Walk-Forward 4 轮
370:## 迭代 #4 — Portfolio Backtest 模块 + per-group DD 降级为风险 metadata
474:## 迭代 #5 — Paper Trading Integrity & Parity
617:## 迭代 #6 — 按 iterations/iteration_6/spec.md 进行开发。先读 spec 文件理解完整需求，然后实施 Harness Reliability & Live Test Isolation：隔离默认 live tests、修复 orchestrator pytest 统计/状态判定/快照 untracked 留痕、生成 gate_status.json、补充 harness 测试并同步两份 orchestrator 副本。严格遵守 spec scope；不得修改交易策略、风控阈值或下单逻辑；不得触发真实下单；完成后运行 targeted harness tests 和默认非 live pytest，并更新 trajectory / CODEBUDDY / 必要文档。
706:## 迭代 #7 — SignalRanker Sortino Priority + Benchmark Comparison
848:## 迭代 #8 — Trend-Filtered Mean Reversion 策略 (RSI + 200 SMA)
919:## 迭代 #9 — MatrixBacktest Alpha-Based Strategy Selection
1026:## 迭代 #10 — vectorbt Batch Backtest Optimization

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"file_path":"/Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md","limit":35,"offset":1026}
---
1026→## 迭代 #10 — vectorbt Batch Backtest Optimization
1027→
1028→- **日期**: 2026-07-05 UTC
1029→- **类型**: 回测核心路径性能优化（中高风险）
1030→- **变更摘要**: 将 MatrixBacktest 和 Walk-Forward 的 for-symbol 逐标的循环改为 vectorbt 矩阵化调用（`_backtest_batch`），单次 `vbt.Portfolio.from_signals` 处理组内所有标的，预计 10-20x 提速；新增进度日志；补充 24 个数值一致性测试
1031→- **状态**: passed
1032→- **执行时长**: 1 轮对话（手动开发）
1033→- **测试数**: 602 → 626（+24 新测试用例）
1034→
1035→### 背景
1036→
1037→Iter #7 实测 `--reoptimize` 耗时 ~4 小时。瓶颈分析显示 vbt 调用次数 ~200,000 次（40,000 次/组 × 4 轮 WF），每次 30-50ms。当前代码把 vectorbt 当成"单标的回测器在 for 循环里调"，完全没用到 vectorbt 的矩阵化特性。
1038→
1039→### 变更详情
1040→
1041→**P0: 新增 `_backtest_batch()` 函数** (`matrix_backtest.py`)
1042→- 一次 `vbt.Portfolio.from_signals` 处理组内所有标的，替代 for-symbol 循环
1043→- vbt 调用次数从 ~40,000/组降到 ~660/组（110 参数 × 6 组），**60x 减少**
1044→- 实现要点：
1045→  - 逐标的调用策略函数（保持 `_backtest_one` 的 try/except TypeError 语义）
1046→  - 构建 close/open 矩阵（`pd.DataFrame` 自动 outer-join 时间索引）
1047→  - 一次 vbt 调用，通过 `pf[sym]` 提取 per-symbol stats/daily_returns
1048→  - 输出格式与 `_backtest_one` 完全一致，下游聚合代码无需修改
1049→- 安全 fallback：vbt 异常时退化为 `_backtest_one` 逐标的回测，保证不阻塞
1050→
1051→**P0: 修改 `_run_group()` 使用 batch** (`matrix_backtest.py::_run_group`)
1052→- 替换 `for sym in symbols: _backtest_one(...)` 为 `_backtest_batch(data, strategy, params, ...)`
1053→- top-K 选择 / DD 过滤 / Alpha 排序 / ensemble 权重逻辑全部保持不变
1054→- 迭代 #9 的所有逻辑（三级 fallback、Sortino 门槛、Alpha 排序）完全不动
1055→
1056→**P0: 修改 Walk-Forward 使用 batch** (`matrix_backtest.py::_backtest_with_params_on_period`)
1057→- 替换 for-symbol 循环为 `_backtest_batch`
1058→- Walk-Forward 4 轮验证期回测同样提速
1059→
1060→**P1: 进度日志** (`matrix_backtest.py::_run_group`)
1061→
---
1026→## 迭代 #10 — vectorbt Batch Backtest Optimization
1027→
1028→- **日期**: 2026-07-05 UTC
1029→- **类型**: 回测核心路径性能优化（中高风险）
1030→- **变更摘要**: 将 MatrixBacktest 和 Walk-Forward 的 for-symbol 逐标的循环改为 vectorbt 矩阵化调用（`_backtest_batch`），单次 `vbt.Portfolio.from_signals` 处理组内所有标的，预计 10-20x 提速；新增进度日志；补充 24 个数值一致性测试
1031→- **状态**: passed
1032→- **执行时长**: 1 轮对话（手动开发）
1033→- **测试数**: 602 → 626（+24 新测试用例）
1034→
1035→### 背景
1036→
1037→Iter #7 实测 `--reoptimize` 耗时 ~4 小时。瓶颈分析显示 vbt 调用次数 ~200,000 次（40,000 次/组 × 4 轮 WF），每次 30-50ms。当前代码把 vectorbt 当成"单标的回测器在 for 循环里调"，完全没用到 vectorbt 的矩阵化特性。
1038→
1039→### 变更详情
1040→
1041→**P0: 新增 `_backtest_batch()` 函数** (`matrix_backtest.py`)
1042→- 一次 `vbt.Portfolio.from_signals` 处理组内所有标的，替代 for-symbol 循环
1043→- vbt 调用次数从 ~40,000/组降到 ~660/组（110 参数 × 6 组），**60x 减少**
1044→- 实现要点：
1045→  - 逐标的调用策略函数（保持 `_backtest_one` 的 try/except TypeError 语义）
1046→  - 构建 close/open 矩阵（`pd.DataFrame` 自动 outer-join 时间索引）
1047→  - 一次 vbt 调用，通过 `pf[sym]` 提取 per-symbol stats/daily_returns
1048→  - 输出格式与 `_backtest_one` 完全一致，下游聚合代码无需修改
1049→- 安全 fallback：vbt 异常时退化为 `_backtest_one` 逐标的回测，保证不阻塞
1050→
1051→**P0: 修改 `_run_group()` 使用 batch** (`matrix_backtest.py::_run_group`)
1052→- 替换 `for sym in symbols: _backtest_one(...)` 为 `_backtest_batch(data, strategy, params, ...)`
1053→- top-K 选择 / DD 过滤 / Alpha 排序 / ensemble 权重逻辑全部保持不变
1054→- 迭代 #9 的所有逻辑（三级 fallback、Sortino 门槛、Alpha 排序）完全不动
1055→
1056→**P0: 修改 Walk-Forward 使用 batch** (`matrix_backtest.py::_backtest_with_params_on_period`)
1057→- 替换 for-symbol 循环为 `_backtest_batch`
1058→- Walk-Forward 4 轮验证期回测同样提速
1059→
1060→**P1: 进度日志** (`matrix_backtest.py::_run_group`)
1061→
---
现在
---
让我
---
查看
---
 `
---
design
---
_v
---
2
---
/
---
07
---
-back
---
test
---
-module
---
.md
---
`
---
 的
---
内容
---
，
---
以
---
了解
---
需要
---
更新
---
什么
---
：
---
{"command":"grep -n \"^## \\|^### \\|closed_trades\\|degenerate\\|健全性\" /Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md | head -30","description":"Check design doc structure"}
---
Check design doc structure
---
Command: grep -n "^## \|^### \|closed_trades\|degenerate\|健全性" /Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md | head -30
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
397:### 10.4.1 Top-K 选择三级 Fallback（迭代 #9 新增）
424:### 10.5 Walk-Forward 月度重优化
457:### 10.6 输出文件
484:### 10.7 性能考量
497:## 参考来源

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md","limit":85,"offset":378}
---
 378→### 10.4 关键设计点
 379→
 380→| 设计点 | 做法 | 理由 |
 381→|--------|------|------|
 382→| **组内取平均** | 等权合并组内日收益率序列，计算组合 Sharpe（而非直接平均各标的 Sharpe 比率） | 避免单只过拟合；Sharpe 是比率，不能直接平均；需要组合视角 |
 383→| **组合 Sortino**（迭代 #1 新增） | 与组合 Sharpe 同口径：等权合并日收益率 → `_compute_sortino(combined)` | Constitution L1 首要 KPI；比率不可直接平均；与 Sharpe 同口径保证可比 |
 384→| **组合 Max Drawdown**（迭代 #2 新增） | 等权合并组内日收益率 → cumprod → cummax → drawdown → max，返回正百分数 | Constitution L1 DD≤20% 硬约束；DD 是路径依赖比率不可直接平均；per-stock avg DD 虚高（无分散化效应） |
 385→| **NaN 安全处理**（迭代 #2 新增） | `_safe_float()` 拦截 NaN/None/Inf；`_safe_mean()` 拦截空列表/全 NaN | vectorbt 无交易时 stats 返回 NaN；`NaN or 0.0` 仍为 NaN（NaN 是 truthy）导致 JSON 序列化失败 |
 386→| **策略名校验**（迭代 #1 新增） | `_run_group` 进入策略循环前检查 `strategy not in STRATEGY_REGISTRY` → `logger.warning` + `continue` | 防止策略名拼写错误被静默跳过（迭代 #1 修复的 bug：`main.py` 误用 `"rsi"/"macd"/"bollinger"` 简称导致 3 个策略 6 天未跑） |
 387→| **DD 硬约束 + Fallback**（迭代 #3 新增） | top-K 选择时过滤 `portfolio_max_drawdown > 20%` 的候选；若全部超标 → 按 DD 升序取 top-K，标记 `dd_constrained=True` | Constitution L1 DD≤20% 是硬约束；无合规候选时仍需产出权重（结构性问题不能阻塞回测） |
 388→| **Alpha 排序 + Sortino 门槛**（迭代 #9 新增） | top-K 排序从 Sortino 改为 Alpha（策略年化收益 - SPY 同期年化收益）；新增 `Sortino > 0.5` 最低质量门槛 | Sortino 高 ≠ 年化高（均值回归策略天然高 Sortino 低绝对收益，alpha 为负）；Alpha 排序直接优化超额收益目标；Sortino 门槛保证基本下行质量。三级 fallback：Tier 1 DD+Sortino → Tier 2 仅 DD → Tier 3 DD 升序 |
 389→| **SPY Benchmark 获取**（迭代 #9 新增） | `_get_spy_returns(start, end)` 从 MarketDataStore 拉取 SPY 日收益率；`_compute_alpha(strat, spy)` 计算年化 alpha | SPY 不可用时 alpha 降级为 0.0（不阻塞回测），所有候选 alpha=0 ��退化为原顺序 |
 390→| **per-strategy best params 用 Alpha**（迭代 #9 新增） | 每个策略的最优参数选择从 Sharpe 改为 Alpha | 与 top-K 排序口径一致，避免 per-strategy 用 Sharpe 选低收益高稳定的参数 |
 391→| **ensemble weights 用 Alpha**（迭代 #9 新增） | `_optimize_ensemble_weights` 接收 `spy_returns` 参数，权重计算从 Sharpe 改为 Alpha | 与 top-K 排序口径一致，ensemble 权重直接反映"跑赢 SPY 的程度"；SPY 不可用时退化为等权 |
 392→| **参数按组** | 同组共用参数，不对单只优化 | 防过拟合（详见 02-strategy-engine.md 6.3） |
 393→| **历史分组对齐** | 矩阵回测使用 point-in-time 分组（按回测时间点重算波动率），而非当前静态分组 | 避免回测静态分组而实盘动态分组导致回测/实盘不一致 |
 394→| **实盘 ensemble 对齐** | MatrixBacktest 的 ensemble 权重优化须在"单点离散值聚合"语义下验证 | 实盘只取 iloc[-1] 单点离散值加权，与序列级加权不等价，权重必须在相同语义下产出 |
 395→| **Walk-Forward** | 滚动训练窗口，月度重优化 | 平衡过拟合与适应性 |
 396→
 397→### 10.4.1 Top-K 选择三级 Fallback（迭代 #9 新增）
 398→
 399→```
 400→Tier 1: DD ≤ 20% AND Sortino > 0.5  →  Alpha 降序取 top-K
 401→   ↓ (若空)
 402→Tier 2: DD ≤ 20%（放宽 Sortino）   →  Alpha 降序取 top-K，WARNING 日志
 403→   ↓ (若空)
 404→Tier 3: 无 DD 合规候选              →  DD 升序取 top-K，dd_constrained=True
 405→```
 406→
 407→**设计动机**（iteration #9 spec §1-2）：
 408→- Constitution 目标：年化 20-30%（需 alpha +10~20%）
 409→- 旧逻辑：Sortino 降序 → 永远选均值回归策略 → 年化 8.02%，alpha = -11.34%
 410→- 新逻辑：Alpha 降序 → 直接优化超额收益目标
 411→- Sortino 门槛：避免选到"高 alpha 但高下行波动"的垃圾策略
 412→
 413→**Alpha 计算公式**：
 414→```python
 415→strat_annual = (1 + strat_returns.mean()) ** 252 - 1
 416→spy_annual   = (1 + spy_returns.mean()) ** 252 - 1
 417→alpha_pct    = (strat_annual - spy_annual) * 100
 418→```
 419→
 420→**降级处理**：SPY 数据不可用 → alpha=0.0，所有候选 alpha 相等，
 421→Python 稳定排序保留原顺序（按策略列表顺序）。
 422→
 423→
 424→### 10.5 Walk-Forward 月度重优化
 425→
 426→```
 427→训练窗口 5 年 → 优化权重 → 应用 1 个月（样本外）→ 滚动前移 → 重新优化
 428→
 429→调度（APScheduler）：
 430→  每月第一个交易日 00:00 触发 run_matrix_backtest()
 431→  → 更新 strategy_weights.json
 432→  → StrategyMatrixRunner.reload_weights() 热加载
 433→```
 434→
 435→为什么是月度（设计访谈确认）：
 436→
 437→```
 438→更新太频繁（每天）→ 拟合近期噪音，权重翻转，策略左右打脸
 439→更新太慢（每年）  → 行情切换时反应迟钝
 440→每月 ≈ 21 交易日  → 足够样本外数据验证上轮权重，换手率可控
 441→```
 442→
 443→**窗口重叠率讨论：**
 444→
 445→```
 446→当前方案：训练 5 年 + 步进 1 个月 → 重叠率 = 59/60 ≈ 98.3%
 447→→ 权重变化缓慢（惯性大），但保证了统计稳健性
 448→→ 代价：市场突变时（如 2022 熊市初期）权重适应较慢
 449→
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
 463→
---
 378→### 10.4 关键设计点
 379→
 380→| 设计点 | 做法 | 理由 |
 381→|--------|------|------|
 382→| **组内取平均** | 等权合并组内日收益率序列，计算组合 Sharpe（而非直接平均各标的 Sharpe 比率） | 避免单只过拟合；Sharpe 是比率，不能直接平均；需要组合视角 |
 383→| **组合 Sortino**（迭代 #1 新增） | 与组合 Sharpe 同口径：等权合并日收益率 → `_compute_sortino(combined)` | Constitution L1 首要 KPI；比率不可直接平均；与 Sharpe 同口径保证可比 |
 384→| **组合 Max Drawdown**（迭代 #2 新增） | 等权合并组内日收益率 → cumprod → cummax → drawdown → max，返回正百分数 | Constitution L1 DD≤20% 硬约束；DD 是路径依赖比率不可直接平均；per-stock avg DD 虚高（无分散化效应） |
 385→| **NaN 安全处理**（迭代 #2 新增） | `_safe_float()` 拦截 NaN/None/Inf；`_safe_mean()` 拦截空列表/全 NaN | vectorbt 无交易时 stats 返回 NaN；`NaN or 0.0` 仍为 NaN（NaN 是 truthy）导致 JSON 序列化失败 |
 386→| **策略名校验**（迭代 #1 新增） | `_run_group` 进入策略循环前检查 `strategy not in STRATEGY_REGISTRY` → `logger.warning` + `continue` | 防止策略名拼写错误被静默跳过（迭代 #1 修复的 bug：`main.py` 误用 `"rsi"/"macd"/"bollinger"` 简称导致 3 个策略 6 天未跑） |
 387→| **DD 硬约束 + Fallback**（迭代 #3 新增） | top-K 选择时过滤 `portfolio_max_drawdown > 20%` 的候选；若全部超标 → 按 DD 升序取 top-K，标记 `dd_constrained=True` | Constitution L1 DD≤20% 是硬约束；无合规候选时仍需产出权重（结构性问题不能阻塞回测） |
 388→| **Alpha 排序 + Sortino 门槛**（迭代 #9 新增） | top-K 排序从 Sortino 改为 Alpha（策略年化收益 - SPY 同期年化收益）；新增 `Sortino > 0.5` 最低质量门槛 | Sortino 高 ≠ 年化高（均值回归策略天然高 Sortino 低绝对收益，alpha 为负）；Alpha 排序直接优化超额收益目标；Sortino 门槛保证基本下行质量。三级 fallback：Tier 1 DD+Sortino → Tier 2 仅 DD → Tier 3 DD 升序 |
 389→| **SPY Benchmark 获取**（迭代 #9 新增） | `_get_spy_returns(start, end)` 从 MarketDataStore 拉取 SPY 日收益率；`_compute_alpha(strat, spy)` 计算年化 alpha | SPY 不可用时 alpha 降级为 0.0（不阻塞回测），所有候选 alpha=0 ��退化为原顺序 |
 390→| **per-strategy best params 用 Alpha**（迭代 #9 新增） | 每个策略的最优参数选择从 Sharpe 改为 Alpha | 与 top-K 排序口径一致，避免 per-strategy 用 Sharpe 选低收益高稳定的参数 |
 391→| **ensemble weights 用 Alpha**（迭代 #9 新增） | `_optimize_ensemble_weights` 接收 `spy_returns` 参数，权重计算从 Sharpe 改为 Alpha | 与 top-K 排序口径一致，ensemble 权重直接反映"跑赢 SPY 的程度"；SPY 不可用时退化为等权 |
 392→| **参数按组** | 同组共用参数，不对单只优化 | 防过拟合（详见 02-strategy-engine.md 6.3） |
 393→| **历史分组对齐** | 矩阵回测使用 point-in-time 分组（按回测时间点重算波动率），而非当前静态分组 | 避免回测静态分组而实盘动态分组导致回测/实盘不一致 |
 394→| **实盘 ensemble 对齐** | MatrixBacktest 的 ensemble 权重优化须在"单点离散值聚合"语义下验证 | 实盘只取 iloc[-1] 单点离散值加权，与序列级加权不等价，权重必须在相同语义下产出 |
 395→| **Walk-Forward** | 滚动训练窗口，月度重优化 | 平衡过拟合与适应性 |
 396→
 397→### 10.4.1 Top-K 选择三级 Fallback（迭代 #9 新增）
 398→
 399→```
 400→Tier 1: DD ≤ 20% AND Sortino > 0.5  →  Alpha 降序取 top-K
 401→   ↓ (若空)
 402→Tier 2: DD ≤ 20%（放宽 Sortino）   →  Alpha 降序取 top-K，WARNING 日志
 403→   ↓ (若空)
 404→Tier 3: 无 DD 合规候选              →  DD 升序取 top-K，dd_constrained=True
 405→```
 406→
 407→**设计动机**（iteration #9 spec §1-2）：
 408→- Constitution 目标：年化 20-30%（需 alpha +10~20%）
 409→- 旧逻辑：Sortino 降序 → 永远选均值回归策略 → 年化 8.02%，alpha = -11.34%
 410→- 新逻辑：Alpha 降序 → 直接优化超额收益目标
 411→- Sortino 门槛：避免选到"高 alpha 但高下行波动"的垃圾策略
 412→
 413→**Alpha 计算公式**：
 414→```python
 415→strat_annual = (1 + strat_returns.mean()) ** 252 - 1
 416→spy_annual   = (1 + spy_returns.mean()) ** 252 - 1
 417→alpha_pct    = (strat_annual - spy_annual) * 100
 418→```
 419→
 420→**降级处理**：SPY 数据不可用 → alpha=0.0，所有候选 alpha 相等，
 421→Python 稳定排序保留原顺序（按策略列表顺序）。
 422→
 423→
 424→### 10.5 Walk-Forward 月度重优化
 425→
 426→```
 427→训练窗口 5 年 → 优化权重 → 应用 1 个月（样本外）→ 滚动前移 → 重新优化
 428→
 429→调度（APScheduler）：
 430→  每月第一个交易日 00:00 触发 run_matrix_backtest()
 431→  → 更新 strategy_weights.json
 432→  → StrategyMatrixRunner.reload_weights() 热加载
 433→```
 434→
 435→为什么是月度（设计访谈确认）：
 436→
 437→```
 438→更新太频繁（每天）→ 拟合近期噪音，权重翻转，策略左右打脸
 439→更新太慢（每年）  → 行情切换时反应迟钝
 440→每月 ≈ 21 交易日  → 足够样本外数据验证上轮权重，换手率可控
 441→```
 442→
 443→**窗口重叠率讨论：**
 444→
 445→```
 446→当前方案：训练 5 年 + 步进 1 个月 → 重叠率 = 59/60 ≈ 98.3%
 447→→ 权重变化缓慢（惯性大），但保证了统计稳健性
 448→→ 代价：市场突变时（如 2022 熊市初期）权重适应较慢
 449→
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
 463→
---
现在
---
我已经
---
掌握了
---
所需
---
的所有
---
背景
---
信息
---
。
---
让我
---
来
---
设定
---
任务
---
并
---
开始
---
实施
---
：
---
{"activeForm":"Adding closed_trades field","description":"Add `closed_trades: int = 0` field to SingleBacktestResult dataclass. Add `no_valid_strategy: bool = False` to GroupBacktestResult.","subject":"Add closed_trades field to SingleBacktestResult + GroupBacktestResult.no_valid_strategy"}
---
{"activeForm":"Populating closed_trades in backtest paths","description":"Use `pf.trades.closed.count()` (vbt 1.0 actual API) to extract closed trades count. Ensure batch vs single numerical consistency.","subject":"Populate closed_trades in _backtest_one and _backtest_batch"}
---
{"activeForm":"Adding degenerate filter logic","description":"Add DEGENERATE_NO_CLOSE_FRACTION=0.8 constant and _is_degenerate_strategy function. Integrate sanity filter in _run_group before candidates construction; all-degenerate group returns empty weights + no_valid_strategy flag.","subject":"Add DEGENERATE_NO_CLOSE_FRACTION constant + _is_degenerate_strategy function"}
---
{"activeForm":"Writing degenerate filter tests","description":"Test closed_trades populated, batch vs single consistency, degenerate detection, normal not degenerate, degenerate excluded from weights, all-degenerate empty group, low-frequency strategy not falsely excluded.","subject":"Write degenerate filter tests (7+ tests including batch-vs-single + low-frequency boundary)"}
---
{"activeForm":"Running tests and updating docs","description":"Run targeted tests (test_matrix_backtest, test_batch_backtest, new degenerate filter tests) + default pytest. Update 07-backtest-module.md, iteration_trajectory.md, decision_log.md, CODEBUDDY.md.","subject":"Run targeted tests + default pytest, update design/trajectory/decision_log/CODEBUDDY"}
---
Task #1 created successfully: Add closed_trades field to SingleBacktestResult + GroupBacktestResult.no_valid_strategy
---
Task #1 created successfully: Add closed_trades field to SingleBacktestResult + GroupBacktestResult.no_valid_strategy
---
Task #2 created successfully: Populate closed_trades in _backtest_one and _backtest_batch
---
Task #2 created successfully: Populate closed_trades in _backtest_one and _backtest_batch
---
Task #3 created successfully: Add DEGENERATE_NO_CLOSE_FRACTION constant + _is_degenerate_strategy function
---
Task #3 created successfully: Add DEGENERATE_NO_CLOSE_FRACTION constant + _is_degenerate_strategy function
---
Task #4 created successfully: Write degenerate filter tests (7+ tests including batch-vs-single + low-frequency boundary)
---
Task #4 created successfully: Write degenerate filter tests (7+ tests including batch-vs-single + low-frequency boundary)
---
Task #5 created successfully: Run targeted tests + default pytest, update design/trajectory/decision_log/CODEBUDDY
---
Task #5 created successfully: Run targeted tests + default pytest, update design/trajectory/decision_log/CODEBUDDY
---
{"status":"in_progress","taskId":"1"}
---
Updated task #1 status
---
Updated task #1 status
---
###
---
 第
---
一步
---
：
---
在
---
 data
---
classes
---
 中
---
添加
---
 `
---
closed
---
_tr
---
ades
---
`
---
 和
---
 `
---
no
---
_valid
---
_strategy
---
`
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py","new_string":"@dataclass\nclass SingleBacktestResult:\n    \"\"\"单只标的单策略回测结果。\"\"\"\n\n    symbol: str\n    strategy: str\n    params: dict\n    sharpe: float\n    total_return_pct: float\n    max_drawdown_pct: float\n    win_rate_pct: float\n    total_trades: int\n    daily_returns: pd.Series    # pf.returns() — 供组合 Sharpe / Sortino 计算\n    sortino: float = 0.0       # Constitution L1 首要 KPI（迭代 #1 新增）\n    closed_trades: int = 0     # 迭代 #11 新增：已平仓交易数（区分退化 buy-and-hold）\n\n\n@dataclass\nclass GroupBacktestResult:\n    \"\"\"单组策略回测结果。\"\"\"\n\n    group_id: str\n    strategy: str\n    params: dict\n    portfolio_sharpe: float          # 等权组合 Sharpe（而非算术平均）\n    avg_total_return_pct: float\n    avg_max_drawdown_pct: float\n    avg_win_rate_pct: float\n    symbol_count: int\n    portfolio_sortino: float = 0.0          # 等权组合 Sortino（迭代 #1 新增）\n    portfolio_max_drawdown: float = 0.0     # 等权组合最大回撤（迭代 #2 新增，Constitution L1 KPI）\n    dd_constrained: bool = False            # 迭代 #3：该组是否用了 DD fallback（无合规候选）\n    backtest_alpha: float = 0.0              # 迭代 #9：alpha vs SPY（百分数），用于排序策略选择\n    no_valid_strategy: bool = False         # 迭代 #11：该组是否因全退化而空仓（hold cash）","old_string":"@dataclass\nclass SingleBacktestResult:\n    \"\"\"单只标的单策略回测结果。\"\"\"\n\n    symbol: str\n    strategy: str\n    params: dict\n    sharpe: float\n    total_return_pct: float\n    max_drawdown_pct: float\n    win_rate_pct: float\n    total_trades: int\n    daily_returns: pd.Series    # pf.returns() — 供组合 Sharpe / Sortino 计算\n    sortino: float = 0.0       # Constitution L1 首要 KPI（迭代 #1 新增）\n\n\n@dataclass\nclass GroupBacktestResult:\n    \"\"\"单组策略回测结果。\"\"\"\n\n    group_id: str\n    strategy: str\n    params: dict\n    portfolio_sharpe: float          # 等权组合 Sharpe（而非算术平均）\n    avg_total_return_pct: float\n    avg_max_drawdown_pct: float\n    avg_win_rate_pct: float\n    symbol_count: int\n    portfolio_sortino: float = 0.0          # 等权组合 Sortino（迭代 #1 新增）\n    portfolio_max_drawdown: float = 0.0     # 等权组合最大回撤（迭代 #2 新增，Constitution L1 KPI）\n    dd_constrained: bool = False            # 迭代 #3：该组是否用了 DD fallback（无合规候选）\n    backtest_alpha: float = 0.0              # 迭代 #9：alpha vs SPY（百分数），用于排序策略选择","replace_all":false}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py
---
{"status":"completed","taskId":"1"}
---
{"status":"in_progress","taskId":"2"}
---
Updated task #1 status
---
Updated task #1 status
---
Updated task #2 status
---
Updated task #2 status
---
###
---
 第二
---
步
---
：
---
在
---
 `_
---
back
---
test
---
_one
---
`
---
 和
---
 `_
---
back
---
test
---
_batch
---
`
---
 中
---
填充
---
 `
---
closed
---
_tr
---
ades
---
`
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py","new_string":"        stats = pf.stats()\n\n        daily_returns = pf.returns()\n\n        # 迭代 #11：已平仓交易数（用于健全性门槛 _is_degenerate_strategy）\n        # vbt 1.0 API: pf.trades.closed.count() 返回 Status==Closed 的交易数\n        # 区分\"真交易闭环\"与\"末尾强平计 1 笔的伪 buy-and-hold\"\n        try:\n            closed_trades = int(pf.trades.closed.count())\n        except Exception:\n            closed_trades = 0\n\n        return SingleBacktestResult(\n            symbol=str(df.index.name or \"\"),\n            strategy=strategy_name,\n            params=params,\n            sharpe=_safe_float(stats.get(\"Sharpe Ratio\")),\n            total_return_pct=_safe_float(stats.get(\"Total Return [%]\")),\n            max_drawdown_pct=_safe_float(stats.get(\"Max Drawdown [%]\")),\n            win_rate_pct=_safe_float(stats.get(\"Win Rate [%]\")),\n            total_trades=int(_safe_float(stats.get(\"Total Trades\"), default=0.0)),\n            daily_returns=daily_returns,\n            sortino=_compute_sortino(daily_returns),\n            closed_trades=closed_trades,\n        )\n    except Exception as e:\n        logger.debug(f\"[backtest_one] {strategy_name}({params}) failed: {e}\")\n        return None","old_string":"        stats = pf.stats()\n\n        daily_returns = pf.returns()\n\n        return SingleBacktestResult(\n            symbol=str(df.index.name or \"\"),\n            strategy=strategy_name,\n            params=params,\n            sharpe=_safe_float(stats.get(\"Sharpe Ratio\")),\n            total_return_pct=_safe_float(stats.get(\"Total Return [%]\")),\n            max_drawdown_pct=_safe_float(stats.get(\"Max Drawdown [%]\")),\n            win_rate_pct=_safe_float(stats.get(\"Win Rate [%]\")),\n            total_trades=int(_safe_float(stats.get(\"Total Trades\"), default=0.0)),\n            daily_returns=daily_returns,\n            sortino=_compute_sortino(daily_returns),\n        )\n    except Exception as e:\n        logger.debug(f\"[backtest_one] {strategy_name}({params}) failed: {e}\")\n        return None","replace_all":false}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py
---
现在是
---
批量
---
处理
---
路径
---
：
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py","new_string":"    # 4. 提取 per-symbol 结果（与 _backtest_one 输出格式一致）\n    results = []\n    for sym in signal_matrix.columns:\n        try:\n            pf_sym = pf[sym]\n            stats = pf_sym.stats()\n            daily_returns = pf_sym.returns()\n            # 迭代 #11：已平仓交易数（与 _backtest_one 同 API、同语义）\n            # pf_sym 是单列 pf，pf_sym.trades.closed.count() 返回 int\n            try:\n                closed_trades = int(pf_sym.trades.closed.count())\n            except Exception:\n                closed_trades = 0\n            results.append(SingleBacktestResult(\n                symbol=sym,\n                strategy=strategy_name,\n                params=params,\n                sharpe=_safe_float(stats.get(\"Sharpe Ratio\")),\n                total_return_pct=_safe_float(stats.get(\"Total Return [%]\")),\n                max_drawdown_pct=_safe_float(stats.get(\"Max Drawdown [%]\")),\n                win_rate_pct=_safe_float(stats.get(\"Win Rate [%]\")),\n                total_trades=int(_safe_float(stats.get(\"Total Trades\"), default=0.0)),\n                daily_returns=daily_returns,\n                sortino=_compute_sortino(daily_returns),\n                closed_trades=closed_trades,\n            ))\n        except Exception as e:\n            logger.debug(\n                f\"[backtest_batch] {strategy_name}({params}) {sym} \"\n                f\"stats extraction failed: {e}\"\n            )\n            continue\n\n    return results","old_string":"    # 4. 提取 per-symbol 结果（与 _backtest_one 输出格式一致）\n    results = []\n    for sym in signal_matrix.columns:\n        try:\n            pf_sym = pf[sym]\n            stats = pf_sym.stats()\n            daily_returns = pf_sym.returns()\n            results.append(SingleBacktestResult(\n                symbol=sym,\n                strategy=strategy_name,\n                params=params,\n                sharpe=_safe_float(stats.get(\"Sharpe Ratio\")),\n                total_return_pct=_safe_float(stats.get(\"Total Return [%]\")),\n                max_drawdown_pct=_safe_float(stats.get(\"Max Drawdown [%]\")),\n                win_rate_pct=_safe_float(stats.get(\"Win Rate [%]\")),\n                total_trades=int(_safe_float(stats.get(\"Total Trades\"), default=0.0)),\n                daily_returns=daily_returns,\n                sortino=_compute_sortino(daily_returns),\n            ))\n        except Exception as e:\n            logger.debug(\n                f\"[backtest_batch] {strategy_name}({params}) {sym} \"\n                f\"stats extraction failed: {e}\"\n            )\n            continue\n\n    return results","replace_all":false}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py
---
{"status":"completed","taskId":"2"}
---
{"status":"in_progress","taskId":"3"}
---
Updated task #2 status
---
Updated task #2 status
---
Updated task #3 status
---
Updated task #3 status
---
###
---
 第三
---
步
---
：
---
添加
---
 `
---
DE
---
GENER
---
ATE
---
_NO
---
_CLOSE
---
_F
---
RA
---
CTION
---
`
---
 
---
常
---
量
---
及
---
 `_
---
is
---
_de
---
generate
---
_strategy
---
`
---
 
---
函数
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py","new_string":"# 迭代 #9 新增：Sortino 最低质量门槛，用于 top-K 选择时的二级过滤\n# 排除 Sortino ≤ 0.5 的\"垃圾\"策略（即使 alpha 高也不选）\n# 设计动机：alpha 排序选出高绝对收益策略，但需 Sortino 门槛保证基本下行质量\n# fallback：若无候选通过此门槛，放宽过滤（仅保留 DD 硬约束）\nMIN_SORTINO_THRESHOLD: float = 0.5\n\n# 迭代 #11 新增：健全性门槛 —— 识别\"退化策略\"（几乎不平仓的伪 buy-and-hold）\n# 判定：组内\"有效标的中，已平仓交易数为 0 的比例\"超过此阈值 → 退化\n# 设计动机：真策略应在多数标的上完成买卖闭环；若近乎所有标的都从不平仓，\n#           说明入场/出场条件矛盾（如 Iter #8 rsi_trend_filter），其收益只是\n#           持仓盯市 + 末尾强平的假象，必须在排序前剔除（experience.md #8）。\n# 阈值取 0.8（保守）：只在\"近乎全部标的零平仓\"时触发，避免误伤低频合法策略。\nDEGENERATE_NO_CLOSE_FRACTION: float = 0.8","old_string":"# 迭代 #9 新增：Sortino 最低质量门槛，用于 top-K 选择时的二级过滤\n# 排除 Sortino ≤ 0.5 的\"垃圾\"策略（即使 alpha 高也不选）\n# 设计动机：alpha 排序选出高绝对收益策略，但需 Sortino 门槛保证基本下行质量\n# fallback：若无候选通过此门槛，放宽过滤（仅保留 DD 硬约束）\nMIN_SORTINO_THRESHOLD: float = 0.5","replace_all":false}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py
---
现在
---
在
---
 `_
---
combine
---
_daily
---
_returns
---
`
---
 
---
附近
---
添加
---
 `_
---
is
---
_de
---
generate
---
_strategy
---
`
---
 
---
函数
---
：
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py","new_string":"def _combine_daily_returns(results: list[SingleBacktestResult]) -> pd.Series:\n    \"\"\"等权合并组内日收益率序列，返回组合日收益率（迭代 #9 新增）。\n\n    与 _portfolio_sharpe_from_results / _portfolio_sortino_from_results 同语义：\n    将所有标的日收益率等权合并为组合序列。提取为独立函数以便 alpha 计算\n    和 per-strategy best params 选择复用，避免重复 pd.concat。\n\n    Args:\n        results: 单策略多标的的回测结果列表\n\n    Returns:\n        组合日收益率 pd.Series；无有效数据时返回空 Series\n    \"\"\"\n    valid = [r.daily_returns for r in results if not r.daily_returns.empty]\n    if not valid:\n        return pd.Series(dtype=float)\n    return pd.concat(valid, axis=1).mean(axis=1)\n\n\ndef _is_degenerate_strategy(results: list[SingleBacktestResult]) -> bool:\n    \"\"\"判定一个策略在组内是否退化（几乎不产生已平仓交易）（迭代 #11 新增）。\n\n    退化定义：有效标的中 closed_trades==0 的比例 >= DEGENERATE_NO_CLOSE_FRACTION。\n    这类策略的入场/出场条件互斥（如 Iter #8 rsi_trend_filter 趋势过滤锁死均值\n    回归出场），仓位无法平仓，其 Sortino/alpha 只是持仓盯市假象，不代表真实\n    交易能力，必须在排序前剔除（experience.md #8：sanity → risk → rank）。\n\n    Args:\n        results: 单策略多标的的回测结果列表\n\n    Returns:\n        True 表示退化（应剔除）；空结果视为退化（True）\n    \"\"\"\n    if not results:\n        return True\n    n = len(results)\n    no_close = sum(1 for r in results if r.closed_trades <= 0)\n    return (no_close / n) >= DEGENERATE_NO_CLOSE_FRACTION","old_string":"def _combine_daily_returns(results: list[SingleBacktestResult]) -> pd.Series:\n    \"\"\"等权合并组内日收益率序列，返回组合日收益率（迭代 #9 新增）。\n\n    与 _portfolio_sharpe_from_results / _portfolio_sortino_from_results 同语义：\n    将所有标的日收益率等权合并为组合序列。提取为独立函数以便 alpha 计算\n    和 per-strategy best params 选择复用，避免重复 pd.concat。\n\n    Args:\n        results: 单策略多标的的回测结果列表\n\n    Returns:\n        组合日收益��� pd.Series；无有效数据时返回空 Series\n    \"\"\"\n    valid = [r.daily_returns for r in results if not r.daily_returns.empty]\n    if not valid:\n        return pd.Series(dtype=float)\n    return pd.concat(valid, axis=1).mean(axis=1)","replace_all":false}
---
Error: Edit error on /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py: String to replace not found in file.
String: "def _combine_daily_returns(results: list[SingleBacktestResult]) -> pd.Series:
    """等权合并组内日收益率序列，返回组合日收益率（迭代 #9 新增）。

    与 _portfolio_sharpe_from_results / _portfolio_sortino_from_results 同语义：
    将所有标的日收益率等权合并为组合序列。提取为独立函数以便 alpha 计算
    和 per-strategy best params 选择复用，避免重复 pd.concat。

    Args:
        results: 单策略多标的的回测结果列表

    Returns:
        组合日收益��� pd.Series；无有效数据时返回空 Series
    """
    valid = [r.daily_returns for r in results if not r.daily_returns.empty]
    if not valid:
        return pd.Series(dtype=float)
    return pd.concat(valid, axis=1).mean(axis=1)"
---
Error: Edit error on /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py: String to replace not found in file.
String: "def _combine_daily_returns(results: list[SingleBacktestResult]) -> pd.Series:
    """等权合并组内日收益率序列，返回组合日收益率（迭代 #9 新增）。

    与 _portfolio_sharpe_from_results / _portfolio_sortino_from_results 同语义：
    将所有标的日收益率等权合并为组合序列。提取为独立函数以便 alpha 计算
    和 per-strategy best params 选择复用，避免重复 pd.concat。

    Args:
        results: 单策略多标的的回测结果列表

    Returns:
        组合日收益��� pd.Series；无有效数据时返回空 Series
    """
    valid = [r.daily_returns for r in results if not r.daily_returns.empty]
    if not valid:
        return pd.Series(dtype=float)
    return pd.concat(valid, axis=1).mean(axis=1)"
---
Lik
---
ely
---
 a
---
 character
---
 encoding
---
 issue
---
 with
---
 the
---
 long
---
 comment
---
 text
---
.
---
 Let
---
 me
---
 try
---
 a
---
 smaller
---
,
---
 more
---
 targeted
---
 edit
---
:
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py","new_string":"    valid = [r.daily_returns for r in results if not r.daily_returns.empty]\n    if not valid:\n        return pd.Series(dtype=float)\n    return pd.concat(valid, axis=1).mean(axis=1)\n\n\ndef _is_degenerate_strategy(results: list[SingleBacktestResult]) -> bool:\n    \"\"\"判定一个策略在组内是否退化（几乎不产生已平仓交易）（迭代 #11 新增）。\n\n    退化定义：有效标的中 closed_trades==0 的比例 >= DEGENERATE_NO_CLOSE_FRACTION。\n    这类策略的入场/出场条件互斥（如 Iter #8 rsi_trend_filter 趋势过滤锁死均值\n    回归出场），仓位无法平仓，其 Sortino/alpha 只是持仓盯市假象，不代表真实\n    交易能力，必须在排序前剔除（experience.md #8：sanity → risk → rank）。\n\n    Args:\n        results: 单策略多标的的回测结果列表\n\n    Returns:\n        True 表示退化（应剔除）；空结果视为退化（True）\n    \"\"\"\n    if not results:\n        return True\n    n = len(results)\n    no_close = sum(1 for r in results if r.closed_trades <= 0)\n    return (no_close / n) >= DEGENERATE_NO_CLOSE_FRACTION","old_string":"    valid = [r.daily_returns for r in results if not r.daily_returns.empty]\n    if not valid:\n        return pd.Series(dtype=float)\n    return pd.concat(valid, axis=1).mean(axis=1)\n\n\ndef _compute_alpha(","replace_all":false}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py
---
Wait
---
,
---
 I
---
 replaced
---
 the
---
 wrong
---
 place
---
 —
---
 I
---
 removed
---
 `
---
def
---
 _
---
compute
---
_alpha
---
(`
---
 by
---
 mistake
---
.
---
 Let
---
 me
---
 verify
---
:
---
稍
---
等
---
，
---
我
---
需要
---
核实
---
一下
---
没有
---
删除
---
 `_
---
compute
---
_alpha
---
`
---
：
---
{"command":"grep -n \"^def _compute_alpha\\|^def _is_degenerate\\|^def _combine_daily\" /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py","description":"Verify functions still present"}
---
Verify functions still present
---
Command: grep -n "^def _compute_alpha\|^def _is_degenerate\|^def _combine_daily" /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py
Stdout: 253:def _combine_daily_returns(results: list[SingleBacktestResult]) -> pd.Series:
272:def _is_degenerate_strategy(results: list[SingleBacktestResult]) -> bool:

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
`
---
_
---
compute
---
_alpha
---
`
---
 is
---
 missing
---
!
---
 I
---
 need
---
 to
---
 restore
---
 it
---
.
---
 Let
---
 me
---
 check
---
 the
---
 file
---
:
---
我不
---
小心
---
删除
---
了
---
 `_
---
compute
---
_alpha
---
`
---
。
---
让我
---
恢复
---
它
---
：
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py","limit":30,"offset":290}
---
 290→    return (no_close / n) >= DEGENERATE_NO_CLOSE_FRACTION
 291→    strategy_daily_returns: pd.Series,
 292→    spy_daily_returns: pd.Series | None,
 293→    periods_per_year: int = 252,
 294→) -> float:
 295→    """计算 alpha = 策略年化收益 - SPY 年化收益（迭代 #9 新增）。
 296→
 297→    Alpha 衡量策略相对 SPY buy-and-hold 的超额收益。正值表示跑赢 SPY，
 298→    负值表示跑输 SPY。用于 top-K 策略选择和 per-strategy best params 选择，
 299→    替代之前基于 Sortino/Sharpe 的选择逻辑（参考 iteration #9 spec）。
 300→
 301→    年化公式：(1 + mean_daily) ** periods_per_year - 1
 302→    使用算术平均日收益的几何年化，与 PortfolioBacktester 同口径。
 303→
 304→    降级处理：SPY 数据不可用（None 或空）→ 返回 0.0（不抛异常）。
 305→    这样在 SPY 数据缺失时，alpha 排序退化为"原顺序"，不会阻塞回测。
 306→
 307→    Args:
 308→        strategy_daily_returns: 策略组合日收益率序列
 309→        spy_daily_returns:      SPY 日收益率序列；None 表示数据不可用
 310→        periods_per_year:       年化因子（日线 = 252）
 311→
 312→    Returns:
 313→        Alpha 百分数（如 5.23 表示策略年化收益跑赢 SPY 5.23 个百分点）；
 314→        SPY 不可用时返回 0.0
 315→    """
 316→    if spy_daily_returns is None or spy_daily_returns.empty:
 317→        return 0.0
 318→    if strategy_daily_returns is None or strategy_daily_returns.empty:
 319→        return 0.0
 320→
---
 290→    return (no_close / n) >= DEGENERATE_NO_CLOSE_FRACTION
 291→    strategy_daily_returns: pd.Series,
 292→    spy_daily_returns: pd.Series | None,
 293→    periods_per_year: int = 252,
 294→) -> float:
 295→    """计算 alpha = 策略年化收益 - SPY 年化收益（迭代 #9 新增）。
 296→
 297→    Alpha 衡量策略相对 SPY buy-and-hold 的超额收益。正值表示跑赢 SPY，
 298→    负值表示跑输 SPY。用于 top-K 策略选择和 per-strategy best params 选择，
 299→    替代之前基于 Sortino/Sharpe 的选择逻辑（参考 iteration #9 spec）。
 300→
 301→    年化公式：(1 + mean_daily) ** periods_per_year - 1
 302→    使用算术平均日收益的几何年化，与 PortfolioBacktester 同口径。
 303→
 304→    降级处理：SPY 数据不可用（None 或空）→ 返回 0.0（不抛异常）。
 305→    这样在 SPY 数据缺失时，alpha 排序退化为"原顺序"，不会阻塞回测。
 306→
 307→    Args:
 308→        strategy_daily_returns: 策略组合日收益率序列
 309→        spy_daily_returns:      SPY 日收益率序列；None 表示数据不可用
 310→        periods_per_year:       年化因子（日线 = 252）
 311→
 312→    Returns:
 313→        Alpha 百分数（如 5.23 表示策略年化收益跑赢 SPY 5.23 个百分点）；
 314→        SPY 不可用时返回 0.0
 315→    """
 316→    if spy_daily_returns is None or spy_daily_returns.empty:
 317→        return 0.0
 318→    if strategy_daily_returns is None or strategy_daily_returns.empty:
 319→        return 0.0
 320→
---
我
---
明白了
---
——
---
函数
---
签名
---
被
---
截
---
断了
---
。
---
我来
---
修复
---
一下
---
：
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py","new_string":"    return (no_close / n) >= DEGENERATE_NO_CLOSE_FRACTION\n\n\ndef _compute_alpha(\n    strategy_daily_returns: pd.Series,\n    spy_daily_returns: pd.Series | None,\n    periods_per_year: int = 252,\n) -> float:","old_string":"    return (no_close / n) >= DEGENERATE_NO_CLOSE_FRACTION\n    strategy_daily_returns: pd.Series,\n    spy_daily_returns: pd.Series | None,\n    periods_per_year: int = 252,\n) -> float:","replace_all":false}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py
---
现在
---
验证
---
文件
---
结构
---
是否
---
完整
---
：
---
{"command":"grep -n \"^def \\|^class \" /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py | head -25","description":"Verify all functions present"}
---
Verify all functions present
---
Command: grep -n "^def \|^class " /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py | head -25
Stdout: 63:class SingleBacktestResult:
80:class GroupBacktestResult:
99:class MatrixBacktestReport:
114:class WalkForwardRound:
141:class WalkForwardReport:
162:def _safe_float(value: Any, default: float = 0.0) -> float:
185:def _safe_mean(values: Any, default: float = 0.0) -> float:
205:def _compute_sharpe(returns: pd.Series, periods_per_year: int = 252) -> float:
217:def _compute_sortino(
253:def _combine_daily_returns(results: list[SingleBacktestResult]) -> pd.Series:
272:def _is_degenerate_strategy(results: list[SingleBacktestResult]) -> bool:
293:def _compute_alpha(
351:def _backtest_one(
433:def _backtest_batch(
597:def _portfolio_sharpe_from_results(results: list[SingleBacktestResult]) -> float:
612:def _portfolio_sortino_from_results(results: list[SingleBacktestResult]) -> float:
624:def _portfolio_max_drawdown_from_results(
658:def _optimize_ensemble_weights(
705:def _add_months(d: date, months: int) -> date:
713:def _backtest_with_params_on_period(
762:def run_walk_forward(
914:class MatrixBacktest:

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
我先
---
进行
---
一次
---
快速的
---
语法
---
检查
---
：
---
{"command":"/Users/rickouyang/miniforge3/envs/py312trade/bin/python -c \"from mytrader.backtest.matrix_backtest import SingleBacktestResult, GroupBacktestResult, _is_degenerate_strategy, DEGENERATE_NO_CLOSE_FRACTION; print('OK'); print('DEGENERATE_NO_CLOSE_FRACTION=', DEGENERATE_NO_CLOSE_FRACTION); r = SingleBacktestResult(symbol='X', strategy='s', params={}, sharpe=0.0, total_return_pct=0.0, max_drawdown_pct=0.0, win_rate_pct=0.0, total_trades=0, daily_returns=__import__('pandas').Series(dtype=float)); print('default closed_trades=', r.closed_trades); g = GroupBacktestResult(group_id='g', strategy='s', params={}, portfolio_sharpe=0.0, avg_total_return_pct=0.0, avg_max_drawdown_pct=0.0, avg_win_rate_pct=0.0, symbol_count=0); print('default no_valid_strategy=', g.no_valid_strategy)\"","description":"Verify imports and defaults"}
---
Verify imports and defaults
---
Command: /Users/rickouyang/miniforge3/envs/py312trade/bin/python -c "from mytrader.backtest.matrix_backtest import SingleBacktestResult, GroupBacktestResult, _is_degenerate_strategy, DEGENERATE_NO_CLOSE_FRACTION; print('OK'); print('DEGENERATE_NO_CLOSE_FRACTION=', DEGENERATE_NO_CLOSE_FRACTION); r = SingleBacktestResult(symbol='X', strategy='s', params={}, sharpe=0.0, total_return_pct=0.0, max_drawdown_pct=0.0, win_rate_pct=0.0, total_trades=0, daily_returns=__import__('pandas').Series(dtype=float)); print('default closed_trades=', r.closed_trades); g = GroupBacktestResult(group_id='g', strategy='s', params={}, portfolio_sharpe=0.0, avg_total_return_pct=0.0, avg_max_drawdown_pct=0.0, avg_win_rate_pct=0.0, symbol_count=0); print('default no_valid_strategy=', g.no_valid_strategy)"
Stdout: OK
DEGENERATE_NO_CLOSE_FRACTION= 0.8
default closed_trades= 0
default no_valid_strategy= False

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
###
---
 第
---
 
---
4
---
 
---
步
---
：
---
在
---
 `_
---
run
---
_group
---
`
---
 中
---
集成
---
健全
---
性
---
过滤器
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py","limit":35,"offset":1155}
---
1155→                    avg_total_return_pct=_safe_mean(
1156→                        [r.total_return_pct for r in best_results]
1157→                    ),
1158→                    avg_max_drawdown_pct=_safe_mean(
1159→                        [r.max_drawdown_pct for r in best_results]
1160→                    ),
1161→                    avg_win_rate_pct=_safe_mean(
1162→                        [r.win_rate_pct for r in best_results]
1163→                    ),
1164→                    symbol_count=len(best_results),
1165→                    portfolio_sortino=best_sortino,
1166→                    portfolio_max_drawdown=_portfolio_max_drawdown_from_results(
1167→                        best_results
1168→                    ),
1169→                    backtest_alpha=best_alpha,
1170→                ))
1171→
1172→            logger.info(
1173→                f"[MatrixBacktest] {group_id}: {strategy} done in "
1174→                f"{time.time() - strat_start:.1f}s "
1175→                f"({len(param_combos)} param combos × {valid_symbol_count} symbols)"
1176→            )
1177→
1178→        if not group_results:
1179→            logger.warning(
1180→                f"[MatrixBacktest] {group_id}: no valid results "
1181→                f"(elapsed {time.time() - group_start:.1f}s)"
1182→            )
1183→            return []
1184→
1185→        # 3. 迭代 #9：DD 硬约束 + Sortino 门槛 + Alpha 排序选 Top-K
1186→        #    Constitution L1: portfolio DD ≤ 20% 是硬约束（保留）
1187→        #    新增：Sortino > 0.5 最低质量门槛（可放宽）
1188→        #    变更：排序指标从 Sortino 改为 Alpha
1189→        #
1190→
---
1155→                    avg_total_return_pct=_safe_mean(
1156→                        [r.total_return_pct for r in best_results]
1157→                    ),
1158→                    avg_max_drawdown_pct=_safe_mean(
1159→                        [r.max_drawdown_pct for r in best_results]
1160→                    ),
1161→                    avg_win_rate_pct=_safe_mean(
1162→                        [r.win_rate_pct for r in best_results]
1163→                    ),
1164→                    symbol_count=len(best_results),
1165→                    portfolio_sortino=best_sortino,
1166→                    portfolio_max_drawdown=_portfolio_max_drawdown_from_results(
1167→                        best_results
1168→                    ),
1169→                    backtest_alpha=best_alpha,
1170→                ))
1171→
1172→            logger.info(
1173→                f"[MatrixBacktest] {group_id}: {strategy} done in "
1174→                f"{time.time() - strat_start:.1f}s "
1175→                f"({len(param_combos)} param combos × {valid_symbol_count} symbols)"
1176→            )
1177→
1178→        if not group_results:
1179→            logger.warning(
1180→                f"[MatrixBacktest] {group_id}: no valid results "
1181→                f"(elapsed {time.time() - group_start:.1f}s)"
1182→            )
1183→            return []
1184→
1185→        # 3. 迭代 #9：DD 硬约束 + Sortino 门槛 + Alpha 排序选 Top-K
1186→        #    Constitution L1: portfolio DD ≤ 20% 是硬约束（保留）
1187→        #    新增：Sortino > 0.5 最低质量门槛（可放宽）
1188→        #    变更：排序指标从 Sortino 改为 Alpha
1189→        #
1190→
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py","new_string":"        if not group_results:\n            logger.warning(\n                f\"[MatrixBacktest] {group_id}: no valid results \"\n                f\"(elapsed {time.time() - group_start:.1f}s)\"\n            )\n            return []\n\n        # 迭代 #11：健全性过滤 —— 排序前先剔除退化策略\n        # （experience.md #8：sanity → risk → rank）\n        # 退化策略 = 组内 ≥ 80% 标的 closed_trades==0（入场/出场条件互斥，\n        # 仓位靠末尾强平凑出 Sortino/alpha 假象）。此类策略必须先于 DD/Sortino/\n        # Alpha 过滤剔除，否则其盯市假象会骗过 alpha 排序进入权重。\n        sane_results: list[tuple[str, dict, list[SingleBacktestResult]]] = []\n        for (strategy, params, results) in group_results:\n            if _is_degenerate_strategy(results):\n                logger.warning(\n                    f\"[MatrixBacktest] {group_id}: strategy '{strategy}' is DEGENERATE \"\n                    f\"(>= {DEGENERATE_NO_CLOSE_FRACTION:.0%} symbols have 0 closed trades) \"\n                    f\"— excluded before ranking. Its Sortino/alpha is mark-to-market illusion.\"\n                )\n                continue\n            sane_results.append((strategy, params, results))\n\n        if not sane_results:\n            # 全组退化 → 空权重（持仓现金），标记 no_valid_strategy，不强行选退化策略\n            logger.warning(\n                f\"[MatrixBacktest] {group_id}: ALL strategies degenerate — \"\n                f\"group produces EMPTY weights (hold cash). Marked no_valid_strategy.\"\n            )\n            report.warnings.append(\n                f\"{group_id}: no_valid_strategy (all strategies degenerate)\"\n            )\n            # 标记已 append 的 GroupBacktestResult 条目（供审计追溯）\n            for gr in report.group_results:\n                if gr.group_id == group_id:\n                    gr.no_valid_strategy = True\n            return []\n\n        # 后续 candidates 构建、DD/Sortino/Alpha 过滤、排序，全部改用 sane_results\n        group_results = sane_results\n\n        # 3. 迭代 #9：DD 硬约束 + Sortino 门槛 + Alpha 排序选 Top-K\n        #    Constitution L1: portfolio DD ≤ 20% 是硬约束（保留）\n        #    新增：Sortino > 0.5 最低质量门槛（可放宽）\n        #    变更：排序指标从 Sortino 改为 Alpha\n        #","old_string":"        if not group_results:\n            logger.warning(\n                f\"[MatrixBacktest] {group_id}: no valid results \"\n                f\"(elapsed {time.time() - group_start:.1f}s)\"\n            )\n            return []\n\n        # 3. 迭代 #9：DD 硬约束 + Sortino 门槛 + Alpha 排序选 Top-K\n        #    Constitution L1: portfolio DD ≤ 20% 是硬约束（保留）\n        #    新增：Sortino > 0.5 最低质量门槛（可放宽）\n        #    变更：排序指标从 Sortino 改为 Alpha\n        #","replace_all":false}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py
---
现在
---
让我
---
来
---
验证
---
该
---
文件
---
语法
---
是否
---
正确
---
：
---
{"command":"/Users/rickouyang/miniforge3/envs/py312trade/bin/python -c \"from mytrader.backtest.matrix_backtest import MatrixBacktest, _is_degenerate_strategy, DEGENERATE_NO_CLOSE_FRACTION, SingleBacktestResult; print('OK')\"","description":"Verify module imports cleanly"}
---
Verify module imports cleanly
---
Command: /Users/rickouyang/miniforge3/envs/py312trade/bin/python -c "from mytrader.backtest.matrix_backtest import MatrixBacktest, _is_degenerate_strategy, DEGENERATE_NO_CLOSE_FRACTION, SingleBacktestResult; print('OK')"
Stdout: OK

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
现在
---
，
---
让我
---
进行
---
一次
---
快速的
---
端
---
到
---
端
---
完整性
---
检查
---
，
---
以确保
---
 `
---
closed
---
_tr
---
ades
---
`
---
 
---
获取
---
功能
---
正常
---
，
---
且
---
退化
---
策略
---
检测
---
在实际
---
中
---
能
---
发挥作用
---
：
---
{"command":"/Users/rickouyang/miniforge3/envs/py312trade/bin/python -c \"\nfrom mytrader.backtest.matrix_backtest import _backtest_one, _backtest_batch, _is_degenerate_strategy\nimport pandas as pd\nimport numpy as np\n\n# Make data\nn = 300\nidx = pd.date_range('2021-01-01', periods=n, freq='B')\nrng = np.random.default_rng(42)\nclose = 100 + np.cumsum(rng.normal(0, 0.5, n))\ndf = pd.DataFrame({\n    'open': close - 0.5, 'high': close + 1, 'low': close - 1,\n    'close': close, 'volume': [1000000]*n\n}, index=idx)\ndf.index.name = 'AAA'\n\n# Run normal strategy (dual_ma) — should have closed trades\nr = _backtest_one(df, 'dual_ma', {'fast': 5, 'slow': 20})\nprint(f'dual_ma single: total_trades={r.total_trades}, closed_trades={r.closed_trades}')\n\n# Batch\nresults = _backtest_batch({'AAA': df}, 'dual_ma', {'fast': 5, 'slow': 20})\nprint(f'dual_ma batch:  total_trades={results[0].total_trades}, closed_trades={results[0].closed_trades}')\n\n# Verify match\nassert r.closed_trades == results[0].closed_trades, f'MISMATCH: {r.closed_trades} vs {results[0].closed_trades}'\nprint('batch vs single match: OK')\n\n# Now make a degenerate strategy result list (all 0 closed_trades)\ndegenerate_results = [\n    type('R', (), {'closed_trades': 0, 'daily_returns': pd.Series(dtype=float)})() for _ in range(5)\n]\nprint(f'_is_degenerate (all 0, n=5): {_is_degenerate_strategy(degenerate_results)}')\n\n# Low frequency strategy (2 of 5 with 0 closed_trades = 0.4 < 0.8)\nlow_freq_results = [\n    type('R', (), {'closed_trades': 3, 'daily_returns': pd.Series(dtype=float)})(),\n    type('R', (), {'closed_trades': 2, 'daily_returns': pd.Series(dtype=float)})(),\n    type('R', (), {'closed_trades': 0, 'daily_returns': pd.Series(dtype=float)})(),\n    type('R', (), {'closed_trades': 4, 'daily_returns': pd.Series(dtype=float)})(),\n    type('R', (), {'closed_trades': 0, 'daily_returns': pd.Series(dtype=float)})(),\n]\nprint(f'_is_degenerate (2/5 = 0.4 < 0.8, low freq): {_is_degenerate_strategy(low_freq_results)} (should be False)')\n\n# Edge: 4 of 5 with 0 closed = 0.8 → degenerate (>=)\nedge_results = [type('R', (), {'closed_trades': 0, 'daily_returns': pd.Series(dtype=float)})() for _ in range(4)] + [type('R', (), {'closed_trades': 5, 'daily_returns': pd.Series(dtype=float)})()]\nprint(f'_is_degenerate (4/5 = 0.8 exactly): {_is_degenerate_strategy(edge_results)} (should be True, >= threshold)')\n\"\n","description":"End-to-end sanity check of degenerate filter"}
---
End-to-end sanity check of degenerate filter
---
Command: /Users/rickouyang/miniforge3/envs/py312trade/bin/python -c "
from mytrader.backtest.matrix_backtest import _backtest_one, _backtest_batch, _is_degenerate_strategy
import pandas as pd
import numpy as np

# Make data
n = 300
idx = pd.date_range('2021-01-01', periods=n, freq='B')
rng = np.random.default_rng(42)
close = 100 + np.cumsum(rng.normal(0, 0.5, n))
df = pd.DataFrame({
    'open': close - 0.5, 'high': close + 1, 'low': close - 1,
    'close': close, 'volume': [1000000]*n
}, index=idx)
df.index.name = 'AAA'

# Run normal strategy (dual_ma) — should have closed trades
r = _backtest_one(df, 'dual_ma', {'fast': 5, 'slow': 20})
print(f'dual_ma single: total_trades={r.total_trades}, closed_trades={r.closed_trades}')

# Batch
results = _backtest_batch({'AAA': df}, 'dual_ma', {'fast': 5, 'slow': 20})
print(f'dual_ma batch:  total_trades={results[0].total_trades}, closed_trades={results[0].closed_trades}')

# Verify match
assert r.closed_trades == results[0].closed_trades, f'MISMATCH: {r.closed_trades} vs {results[0].closed_trades}'
print('batch vs single match: OK')

# Now make a degenerate strategy result list (all 0 closed_trades)
degenerate_results = [
    type('R', (), {'closed_trades': 0, 'daily_returns': pd.Series(dtype=float)})() for _ in range(5)
]
print(f'_is_degenerate (all 0, n=5): {_is_degenerate_strategy(degenerate_results)}')

# Low frequency strategy (2 of 5 with 0 closed_trades = 0.4 < 0.8)
low_freq_results = [
    type('R', (), {'closed_trades': 3, 'daily_returns': pd.Series(dtype=float)})(),
    type('R', (), {'closed_trades': 2, 'daily_returns': pd.Series(dtype=float)})(),
    type('R', (), {'closed_trades': 0, 'daily_returns': pd.Series(dtype=float)})(),
    type('R', (), {'closed_trades': 4, 'daily_returns': pd.Series(dtype=float)})(),
    type('R', (), {'closed_trades': 0, 'daily_returns': pd.Series(dtype=float)})(),
]
print(f'_is_degenerate (2/5 = 0.4 < 0.8, low freq): {_is_degenerate_strategy(low_freq_results)} (should be False)')

# Edge: 4 of 5 with 0 closed = 0.8 → degenerate (>=)
edge_results = [type('R', (), {'closed_trades': 0, 'daily_returns': pd.Series(dtype=float)})() for _ in range(4)] + [type('R', (), {'closed_trades': 5, 'daily_returns': pd.Series(dtype=float)})()]
print(f'_is_degenerate (4/5 = 0.8 exactly): {_is_degenerate_strategy(edge_results)} (should be True, >= threshold)')
"

Stdout: dual_ma single: total_trades=8, closed_trades=8
dual_ma batch:  total_trades=8, closed_trades=8
batch vs single match: OK
_is_degenerate (all 0, n=5): True
_is_degenerate (2/5 = 0.4 < 0.8, low freq): False (should be False)
_is_degenerate (4/5 = 0.8 exactly): True (should be True, >= threshold)

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
所有
---
逻辑
---
校
---
验
---
均已
---
通过
---
。
---
让我
---
验证
---
一下
---
 `
---
rs
---
i
---
_t
---
rend
---
_filter
---
`
---
 是否
---
确实
---
被
---
识别
---
为
---
退化
---
策略
---
：
---
{"command":"/Users/rickouyang/miniforge3/envs/py312trade/bin/python -c \"\nfrom mytrader.backtest.matrix_backtest import _backtest_batch, _is_degenerate_strategy\nimport pandas as pd\nimport numpy as np\n\n# Make multi-symbol random-walk data\nn = 500\nidx = pd.date_range('2021-01-01', periods=n, freq='B')\ndata = {}\nfor i, sym in enumerate(['AAA', 'BBB', 'CCC', 'DDD', 'EEE']):\n    rng = np.random.default_rng(100 + i)\n    close = 100 + np.cumsum(rng.normal(0.05, 1.0, n))  # upward drift\n    df = pd.DataFrame({\n        'open': close - 0.5, 'high': close + 1, 'low': close - 1,\n        'close': close, 'volume': [1000000]*n\n    }, index=idx)\n    data[sym] = df\n\n# rsi_trend_filter (the strategy that Iter #11 spec targets)\nresults = _backtest_batch(data, 'rsi_trend_filter', {'rsi_period': 14, 'oversold': 30, 'overbought': 70, 'trend_period': 200})\nprint(f'rsi_trend_filter: {len(results)} symbols')\nfor r in results:\n    print(f'  {r.symbol}: total_trades={r.total_trades}, closed_trades={r.closed_trades}, win_rate={r.win_rate_pct:.2f}')\n\nprint(f'Is degenerate: {_is_degenerate_strategy(results)}')\n\n# Compare to rsi_mean_revert (normal)\nresults2 = _backtest_batch(data, 'rsi_mean_revert', {'period': 14, 'oversold': 30, 'overbought': 70})\nprint(f'rsi_mean_revert: {len(results2)} symbols')\nfor r in results2:\n    print(f'  {r.symbol}: total_trades={r.total_trades}, closed_trades={r.closed_trades}')\nprint(f'Is degenerate: {_is_degenerate_strategy(results2)}')\n\"\n","description":"Verify rsi_trend_filter is detected as degenerate"}
---
Verify rsi_trend_filter is detected as degenerate
---
Command: /Users/rickouyang/miniforge3/envs/py312trade/bin/python -c "
from mytrader.backtest.matrix_backtest import _backtest_batch, _is_degenerate_strategy
import pandas as pd
import numpy as np

# Make multi-symbol random-walk data
n = 500
idx = pd.date_range('2021-01-01', periods=n, freq='B')
data = {}
for i, sym in enumerate(['AAA', 'BBB', 'CCC', 'DDD', 'EEE']):
    rng = np.random.default_rng(100 + i)
    close = 100 + np.cumsum(rng.normal(0.05, 1.0, n))  # upward drift
    df = pd.DataFrame({
        'open': close - 0.5, 'high': close + 1, 'low': close - 1,
        'close': close, 'volume': [1000000]*n
    }, index=idx)
    data[sym] = df

# rsi_trend_filter (the strategy that Iter #11 spec targets)
results = _backtest_batch(data, 'rsi_trend_filter', {'rsi_period': 14, 'oversold': 30, 'overbought': 70, 'trend_period': 200})
print(f'rsi_trend_filter: {len(results)} symbols')
for r in results:
    print(f'  {r.symbol}: total_trades={r.total_trades}, closed_trades={r.closed_trades}, win_rate={r.win_rate_pct:.2f}')

print(f'Is degenerate: {_is_degenerate_strategy(results)}')

# Compare to rsi_mean_revert (normal)
results2 = _backtest_batch(data, 'rsi_mean_revert', {'period': 14, 'oversold': 30, 'overbought': 70})
print(f'rsi_mean_revert: {len(results2)} symbols')
for r in results2:
    print(f'  {r.symbol}: total_trades={r.total_trades}, closed_trades={r.closed_trades}')
print(f'Is degenerate: {_is_degenerate_strategy(results2)}')
"

Stdout: rsi_trend_filter: 5 symbols
  AAA: total_trades=1, closed_trades=0, win_rate=0.00
  BBB: total_trades=0, closed_trades=0, win_rate=0.00
  CCC: total_trades=0, closed_trades=0, win_rate=0.00
  DDD: total_trades=0, closed_trades=0, win_rate=0.00
  EEE: total_trades=1, closed_trades=0, win_rate=0.00
Is degenerate: True
rsi_mean_revert: 5 symbols
  AAA: total_trades=1, closed_trades=1
  BBB: total_trades=1, closed_trades=1
  CCC: total_trades=2, closed_trades=2
  DDD: total_trades=1, closed_trades=1
  EEE: total_trades=1, closed_trades=1
Is degenerate: False

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
`
---
rs
---
i
---
_t
---
rend
---
_filter
---
`
---
 已
---
被
---
正确
---
识别
---
为
---
退化
---
（
---
5
---
 个
---
标的
---
，
---
0
---
 个
---
已
---
平
---
仓
---
交易
---
），
---
而
---
 `
---
rs
---
i
---
_mean
---
_re
---
vert
---
`
---
 则
---
通过了
---
。
---
现在
---
我来
---
运行
---
现有的
---
测试
---
以
---
确认
---
没有
---
回归
---
问题
---
：
---
{"command":"PYTHONPATH=. /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_matrix_backtest.py tests/test_batch_backtest.py -x -q 2>&1 | tail -30","description":"Run existing matrix + batch tests"}
---
Run existing matrix + batch tests
---
Command: PYTHONPATH=. /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_matrix_backtest.py tests/test_batch_backtest.py -x -q 2>&1 | tail -30
Stdout:                 strategies=["dual_ma", "rsi_mean_revert"],
                param_grids={
                    "dual_ma": {"fast": [5], "slow": [20]},
                    "rsi_mean_revert": {
                        "period": [14], "oversold": [30], "overbought": [70]
                    },
                },
            )
    
        # 验证：选择了 rsi_mean_revert（高 alpha）而非 dual_ma（高 Sortino）
        weights = report.groups["test_group"]
>       assert len(weights) == 1, f"top_k=1 应只选 1 个策略，实际 {len(weights)}"
E       AssertionError: top_k=1 应只选 1 个策略，实际 0
E       assert 0 == 1
E        +  where 0 = len([])

tests/test_matrix_backtest.py:1142: AssertionError
----------------------------- Captured stderr call -----------------------------
2026-07-07 10:51:10.636 | INFO     | mytrader.backtest.matrix_backtest:run:965 - [MatrixBacktest] start=2025-07-07, end=2026-07-07, strategies=['dual_ma', 'rsi_mean_revert'], years=1
2026-07-07 10:51:10.636 | INFO     | mytrader.backtest.matrix_backtest:run:988 - [MatrixBacktest] group=test_group, symbols=1, strategies=['dual_ma', 'rsi_mean_revert']
2026-07-07 10:51:10.636 | INFO     | mytrader.backtest.matrix_backtest:_run_group:1088 - [MatrixBacktest] test_group: start — 2 strategies × 1 valid symbols
2026-07-07 10:51:10.637 | INFO     | mytrader.backtest.matrix_backtest:_run_group:1172 - [MatrixBacktest] test_group: dual_ma done in 0.0s (1 param combos × 1 symbols)
2026-07-07 10:51:10.638 | INFO     | mytrader.backtest.matrix_backtest:_run_group:1172 - [MatrixBacktest] test_group: rsi_mean_revert done in 0.0s (1 param combos × 1 symbols)
2026-07-07 10:51:10.638 | WARNING  | mytrader.backtest.matrix_backtest:_run_group:1193 - [MatrixBacktest] test_group: strategy 'dual_ma' is DEGENERATE (>= 80% symbols have 0 closed trades) — excluded before ranking. Its Sortino/alpha is mark-to-market illusion.
2026-07-07 10:51:10.638 | WARNING  | mytrader.backtest.matrix_backtest:_run_group:1193 - [MatrixBacktest] test_group: strategy 'rsi_mean_revert' is DEGENERATE (>= 80% symbols have 0 closed trades) — excluded before ranking. Its Sortino/alpha is mark-to-market illusion.
2026-07-07 10:51:10.638 | WARNING  | mytrader.backtest.matrix_backtest:_run_group:1203 - [MatrixBacktest] test_group: ALL strategies degenerate — group produces EMPTY weights (hold cash). Marked no_valid_strategy.
2026-07-07 10:51:10.638 | INFO     | mytrader.backtest.matrix_backtest:run:1007 - [MatrixBacktest] done: 1 groups, warnings=1
=========================== short test summary info ============================
FAILED tests/test_matrix_backtest.py::TestAlphaBasedTopKSelection::test_top_k_selection_uses_alpha
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!!

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
The
---
 test
---
 `
---
test
---
_top
---
_k
---
_selection
---
_
---
uses
---
_alpha
---
`
---
 is
---
 failing
---
 because
---
 the
---
 mock
---
 `_
---
back
---
test
---
_batch
---
`
---
 returns
---
 Single
---
Back
---
test
---
Result
---
 with
---
 `
---
closed
---
_tr
---
ades
---
=
---
0
---
`
---
 (
---
default
---
),
---
 and
---
 since
---
 the
---
 mock
---
 only
---
 provides
---
 
---
1
---
 symbol
---
,
---
 
---
1
---
/
---
1
---
 =
---
 
---
100
---
%
---
 ≥
---
 
---
80
---
%,
---
 so
---
 it
---
's
---
 marked
---
 deg
---
enerate
---
.


---
This
---
 is
---
 an
---
 expected
---
 interaction
---
 —
---
 existing
---
 tests
---
 that
---
 mock
---
 `_
---
back
---
test
---
_batch
---
`
---
 need
---
 to
---
 be
---
 updated
---
 to
---
 set
---
 `
---
closed
---
_tr
---
ades
---
 >
---
 
---
0
---
`
---
 for
---
 the
---
 strategies
---
 that
---
 should
---
 pass
---
 the
---
 sanity
---
 filter
---
.


---
Let
---
 me
---
 look
---
 at
---
 this
---
 test
---
 and
---
 the
---
 other
---
 mocked
---
 tests
---
 to
---
 understand
---
 which
---
 ones
---
 need
---
 updating
---
.
---
 The
---
 tests
---
 that
---
 mock
---
 `_
---
back
---
test
---
_batch
---
`
---
 and
---
 expect
---
 strategies
---
 to
---
 be
---
 selected
---
 need
---
 to
---
 set
---
 `
---
closed
---
_tr
---
ades
---
`
---
 >
---
 
---
0
---
 in
---
 their
---
 mocked
---
 Single
---
Back
---
test
---
Result
---
.


---
Looking
---
 at
---
 the
---
 failing
---
 test
---
:

---
```
---
python
---


---
results
---
.append
---
(S
---
ingle
---
Back
---
test
---
Result
---
(

---
   
---
 sym
---
,
---
 strategy
---
_name
---
,
---
 params
---
,
---
 
---
1
---
.
---
0
---
,
---
 
---
10
---
.
---
0
---
,
---
 
---
5
---
.
---
0
---
,
---
 
---
55
---
.
---
0
---
,
---
 
---
10
---
,
---
 returns
---
_a
---


---
))

---
``
---
`


---
This
---
 uses
---
 positional
---
 args
---
 for
---
 the
---
 Single
---
Back
---
test
---
Result
---
,
---
 which
---
 means
---
 closed
---
_tr
---
ades
---
 defaults
---
 to
---
 
---
0
---
.
---
 I
---
 need
---
 to
---
 update
---
 these
---
 mock
---
 results
---
 to
---
 set
---
 closed
---
_tr
---
ades
---
 >
---
 
---
0
---
 so
---
 they
---
 don
---
't
---
 trigger
---
 the
---
 deg
---
enerate
---
 filter
---
.


---
Let
---
 me
---
 find
---
 all
---
 such
---
 patterns
---
 in
---
 test
---
_matrix
---
_back
---
test
---
.py
---
 that
---
 use
---
 mock
---
 `_
---
back
---
test
---
_batch
---
`
---
 (
---
not
---
 the
---
 real
---
 one
---
).
---
 For
---
 tests
---
 using
---
 the
---
 real
---
 `_
---
back
---
test
---
_batch
---
`
---
 (
---
or
---
 `_
---
back
---
test
---
_one
---
`
---
),
---
 closed
---
_tr
---
ades
---
 will
---
 be
---
 populated
---
 correctly
---
.


---
Actually
---
,
---
 looking
---
 more
---
 carefully
---
:
---
 the
---
 failing
---
 test
---
 patches
---
 `_
---
back
---
test
---
_batch
---
`
---
 with
---
 a
---
 mock
---
.
---
 The
---
 mock
---
 creates
---
 `
---
Single
---
Back
---
test
---
Result
---
(sym
---
,
---
 strategy
---
_name
---
,
---
 params
---
,
---
 
---
1
---
.
---
0
---
,
---
 
---
10
---
.
---
0
---
,
---
 
---
5
---
.
---
0
---
,
---
 
---
55
---
.
---
0
---
,
---
 
---
10
---
,
---
 returns
---
_a
---
)`
---
 —
---
 this
---
 has
---
 
---
9
---
 positional
---
 args
---
 matching
---
 (
---
symbol
---
,
---
 strategy
---
,
---
 params
---
,
---
 shar
---
pe
---
,
---
 total
---
_return
---
_pct
---
,
---
 max
---
_draw
---
down
---
_pct
---
,
---
 win
---
_rate
---
_pct
---
,
---
 total
---
_tr
---
ades
---
,
---
 daily
---
_returns
---
)
---
 and
---
 closed
---
_tr
---
ades
---
 defaults
---
 to
---
 
---
0
---
.


---
I
---
 need
---
 to
---
 update
---
 the
---
 mocked
---
 tests
---
 to
---
 set
---
 `
---
closed
---
_tr
---
ades
---
`
---
 >
---
 
---
0
---
 for
---
 strategies
---
 that
---
 should
---
 pass
---
.


---
Let
---
 me
---
 look
---
 at
---
 all
---
 the
---
 mocked
---
 _
---
back
---
test
---
_batch
---
 test
---
 cases
---
:

---
1
---
.
---
 `
---
test
---
_top
---
_k
---
_selection
---
_
---
uses
---
_alpha
---
`
---
 (
---
line
---
 
---
109
---
6
---
-
---
110
---
9
---
):
---
 mock
---
 returns
---
 
---
1
---
 result
---
 per
---
 strategy
---
,
---
 all
---
 closed
---
_tr
---
ades
---
=
---
0
---
 →
---
 all
---
 deg
---
enerate
---
 →
---
 test
---
 fails
---


---
2
---
.
---
 `
---
test
---
_sort
---
ino
---
_filter
---
_ex
---
cludes
---
_g
---
ar
---
bage
---
`
---
 (
---
line
---
 
---
120
---
1
---
-
---
121
---
4
---
):
---
 same
---
 pattern
---


---
3
---
.
---
 There
---
 might
---
 be
---
 more
---
 in
---
 the
---
 file
---



---
Let
---
 me
---
 find
---
 them
---
 all
---
.
---
 I
---
 should
---
 also
---
 look
---
 at
---
 lines
---
 
---
134
---
8
---
,
---
 
---
153
---
5
---
,
---
 
---
153
---
9
---
 for
---
 the
---
 same
---
 pattern
---
.
---
现有的
---
模拟
---
 `_
---
back
---
test
---
_batch
---
`
---
 的
---
测试
---
失败
---
，
---
因为
---
模拟
---
的
---
 `
---
Single
---
Back
---
test
---
Result
---
`
---
 
---
默认
---
 `
---
closed
---
_tr
---
ades
---
=
---
0
---
`
---
，
---
导致
---
它们
---
被
---
错误
---
地
---
识别
---
为
---
退化
---
策略
---
。
---
我
---
需要
---
更新
---
这些
---
模拟
---
数据
---
以
---
包含
---
 `
---
closed
---
_tr
---
ades
---
 >
---
 
---
0
---
`
---
。
---
让我
---
来
---
查找
---
所有
---
此类
---
模拟
---
模式
---
：
---
{"-A":1,"-n":true,"output_mode":"content","path":"/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py","pattern":"mock_backtest_batch|results.append\\(SingleBacktestResult\\("}
---
["/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1096:        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py-1097-            results = []","--","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1102:                    results.append(SingleBacktestResult(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py-1103-                        sym, strategy_name, params, 1.0, 10.0, 5.0, 55.0, 10, returns_a","--","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1106:                    results.append(SingleBacktestResult(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py-1107-                        sym, strategy_name, params, 1.0, 30.0, 8.0, 50.0, 10, returns_b","--","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1128:            side_effect=mock_backtest_batch,","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py-1129-        ):","--","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1201:        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py-1202-            results = []","--","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1207:                    results.append(SingleBacktestResult(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py-1208-                        sym, strategy_name, params, 0.5, 15.0, 10.0, 50.0, 5, returns_a","--","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1211:                    results.append(SingleBacktestResult(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py-1212-                        sym, strategy_name, params, 1.0, 20.0, 5.0, 55.0, 10, returns_b","--","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1229:            side_effect=mock_backtest_batch,","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py-1230-        ):","--","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1343:        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py-1344-            results = []","--","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1348:                results.append(SingleBacktestResult(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py-1349-                    sym, strategy_name, params, 0.3, 5.0, 10.0, 50.0, 3, returns_garbage","--","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1371:                side_effect=mock_backtest_batch,","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py-1372-            ):","--","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1529:        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py-1530-            results = []","--","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1535:                    results.append(SingleBacktestResult(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py-1536-                        sym, strategy_name, params, sharpe_a, 10.0, 5.0, 55.0, 10, returns_a","--","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1539:                    results.append(SingleBacktestResult(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py-1540-                        sym, strategy_name, params, sharpe_b, 30.0, 8.0, 50.0, 10, returns_b","--","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1557:            side_effect=mock_backtest_batch,","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py-1558-        ):"]
---
["/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1096:        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py-1097-            results = []","--","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1102:                    results.append(SingleBacktestResult(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py-1103-                        sym, strategy_name, params, 1.0, 10.0, 5.0, 55.0, 10, returns_a","--","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1106:                    results.append(SingleBacktestResult(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py-1107-                        sym, strategy_name, params, 1.0, 30.0, 8.0, 50.0, 10, returns_b","--","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1128:            side_effect=mock_backtest_batch,","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py-1129-        ):","--","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1201:        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py-1202-            results = []","--","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1207:                    results.append(SingleBacktestResult(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py-1208-                        sym, strategy_name, params, 0.5, 15.0, 10.0, 50.0, 5, returns_a","--","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1211:                    results.append(SingleBacktestResult(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py-1212-                        sym, strategy_name, params, 1.0, 20.0, 5.0, 55.0, 10, returns_b","--","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1229:            side_effect=mock_backtest_batch,","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py-1230-        ):","--","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1343:        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py-1344-            results = []","--","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1348:                results.append(SingleBacktestResult(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py-1349-                    sym, strategy_name, params, 0.3, 5.0, 10.0, 50.0, 3, returns_garbage","--","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1371:                side_effect=mock_backtest_batch,","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py-1372-            ):","--","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1529:        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py-1530-            results = []","--","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1535:                    results.append(SingleBacktestResult(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py-1536-                        sym, strategy_name, params, sharpe_a, 10.0, 5.0, 55.0, 10, returns_a","--","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1539:                    results.append(SingleBacktestResult(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py-1540-                        sym, strategy_name, params, sharpe_b, 30.0, 8.0, 50.0, 10, returns_b","--","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1557:            side_effect=mock_backtest_batch,","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py-1558-        ):"]
---
I
---
 need
---
 to
---
 look
---
 at
---
 these
---
 tests
---
 more
---
 carefully
---
.
---
 Let
---
 me
---
 also
---
 check
---
 lines
---
 
---
134
---
3
---
 and
---
 
---
152
---
9
---
 for
---
 full
---
 context
---
.
---
 And
---
 lines
---
 
---
134
---
8
---
 (`
---
returns
---
_g
---
ar
---
bage
---
`)
---
 —
---
 this
---
 one
---
 might
---
 be
---
 intentionally
---
 a
---
 "
---
gar
---
bage
---
"
---
 strategy
---
,
---
 but
---
 the
---
 test
---
 expects
---
 it
---
 to
---
 be
---
 selected
---
 by
---
 some
---
 criteria
---
.
---
 Let
---
 me
---
 check
---
 the
---
 test
---
 name
---
.
---
让我
---
看一下
---
需要
---
更新的
---
测试
---
上下
---
文
---
：
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py","limit":55,"offset":1325}
---
1325→            "high": [c + 0.5 for c in spy_close],
1326→            "low": [c - 0.5 for c in spy_close],
1327→            "close": spy_close,
1328→            "volume": [1_000_000] * n,
1329→        }, index=idx)
1330→
1331→        # 低 Sortino 但 DD 合规的收益序列
1332→        np.random.seed(42)
1333→        returns_garbage = pd.Series(
1334→            np.concatenate([
1335→                np.random.normal(0.0002, 0.01, 200),  # 低均值高波动
1336→                np.random.normal(-0.0001, 0.008, 100), # 略负
1337→            ]),
1338→            index=idx,
1339→        )
1340→        # 验证前提：Sortino < 0.5（垃圾门槛）
1341→        assert _compute_sortino(returns_garbage) < MIN_SORTINO_THRESHOLD
1342→
1343→        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
1344→            results = []
1345→            for sym, df in data.items():
1346→                if df is None or df.empty or len(df) < 30:
1347→                    continue
1348→                results.append(SingleBacktestResult(
1349→                    sym, strategy_name, params, 0.3, 5.0, 10.0, 50.0, 3, returns_garbage
1350→                ))
1351→            return results
1352→
1353→        df_up = _make_ohlcv(n, trend="up")
1354→        store = MagicMock()
1355→        store.get_bars_multi.side_effect = lambda symbols, start, end, timeframe="1d": {
1356→            s: {"AAPL": df_up, "SPY": spy_df}[s] for s in symbols
1357→            if s in {"AAPL", "SPY"}
1358→        }
1359→
1360→        universe = MagicMock()
1361→        universe.get_groups.return_value = {"test_group": ["AAPL"]}
1362→
1363→        # 捕获 WARNING 日志
1364→        msgs: list[str] = []
1365→        handler_id = logger.add(lambda m: msgs.append(str(m)), level="WARNING")
1366→
1367→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=1)
1368→        try:
1369→            with patch(
1370→                "mytrader.backtest.matrix_backtest._backtest_batch",
1371→                side_effect=mock_backtest_batch,
1372→            ):
1373→                report = mb.run(
1374→                    strategies=["dual_ma"],
1375→                    param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
1376→                )
1377→        finally:
1378→            logger.remove(handler_id)
1379→
1380→
---
1325→            "high": [c + 0.5 for c in spy_close],
1326→            "low": [c - 0.5 for c in spy_close],
1327→            "close": spy_close,
1328→            "volume": [1_000_000] * n,
1329→        }, index=idx)
1330→
1331→        # 低 Sortino 但 DD 合规的收益序列
1332→        np.random.seed(42)
1333→        returns_garbage = pd.Series(
1334→            np.concatenate([
1335→                np.random.normal(0.0002, 0.01, 200),  # 低均值高波动
1336→                np.random.normal(-0.0001, 0.008, 100), # 略负
1337→            ]),
1338→            index=idx,
1339→        )
1340→        # 验证前提：Sortino < 0.5（垃圾门槛）
1341→        assert _compute_sortino(returns_garbage) < MIN_SORTINO_THRESHOLD
1342→
1343→        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
1344→            results = []
1345→            for sym, df in data.items():
1346→                if df is None or df.empty or len(df) < 30:
1347→                    continue
1348→                results.append(SingleBacktestResult(
1349→                    sym, strategy_name, params, 0.3, 5.0, 10.0, 50.0, 3, returns_garbage
1350→                ))
1351→            return results
1352→
1353→        df_up = _make_ohlcv(n, trend="up")
1354→        store = MagicMock()
1355→        store.get_bars_multi.side_effect = lambda symbols, start, end, timeframe="1d": {
1356→            s: {"AAPL": df_up, "SPY": spy_df}[s] for s in symbols
1357→            if s in {"AAPL", "SPY"}
1358→        }
1359→
1360→        universe = MagicMock()
1361→        universe.get_groups.return_value = {"test_group": ["AAPL"]}
1362→
1363→        # 捕获 WARNING 日志
1364→        msgs: list[str] = []
1365→        handler_id = logger.add(lambda m: msgs.append(str(m)), level="WARNING")
1366→
1367→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=1)
1368→        try:
1369→            with patch(
1370→                "mytrader.backtest.matrix_backtest._backtest_batch",
1371→                side_effect=mock_backtest_batch,
1372→            ):
1373→                report = mb.run(
1374→                    strategies=["dual_ma"],
1375→                    param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
1376→                )
1377→        finally:
1378→            logger.remove(handler_id)
1379→
1380→
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py","limit":85,"offset":1505}
---
1505→
1506→        # 参数 A 的收益：低波动低收益 → 高 Sharpe 但低 alpha
1507→        np.random.seed(42)
1508→        returns_a = pd.Series(
1509→            np.random.normal(0.0005, 0.002, n), index=idx  # 与 SPY 接近，alpha≈0
1510→        )
1511→        # 参数 B 的收益：高波动高收益 → 低 Sharpe 但高 alpha
1512→        returns_b = pd.Series(
1513→            np.random.normal(0.0012, 0.008, n), index=idx  # 远超 SPY，alpha>0
1514→        )
1515→
1516→        # 验证前提
1517→        sharpe_a = _compute_sharpe(returns_a)
1518→        sharpe_b = _compute_sharpe(returns_b)
1519→        alpha_a = _compute_alpha(returns_a, spy_returns)
1520→        alpha_b = _compute_alpha(returns_b, spy_returns)
1521→        assert sharpe_a > sharpe_b, (
1522→            f"A 的 Sharpe({sharpe_a:.4f}) 应 > B({sharpe_b:.4f})"
1523→        )
1524→        assert alpha_b > alpha_a, (
1525→            f"B 的 alpha({alpha_b:.4f}) 应 > A({alpha_a:.4f})"
1526→        )
1527→
1528→        # 根据参数选择返回不同收益（迭代 #10：mock _backtest_batch）
1529→        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
1530→            results = []
1531→            for sym, df in data.items():
1532→                if df is None or df.empty or len(df) < 30:
1533→                    continue
1534→                if params.get("fast") == 5:  # 参数 A
1535→                    results.append(SingleBacktestResult(
1536→                        sym, strategy_name, params, sharpe_a, 10.0, 5.0, 55.0, 10, returns_a
1537→                    ))
1538→                else:  # 参数 B (fast=10)
1539→                    results.append(SingleBacktestResult(
1540→                        sym, strategy_name, params, sharpe_b, 30.0, 8.0, 50.0, 10, returns_b
1541→                    ))
1542→            return results
1543→
1544→        df_up = _make_ohlcv(n, trend="up")
1545→        store = MagicMock()
1546→        store.get_bars_multi.side_effect = lambda symbols, start, end, timeframe="1d": {
1547→            s: {"AAPL": df_up, "SPY": spy_df}[s] for s in symbols
1548→            if s in {"AAPL", "SPY"}
1549→        }
1550→
1551→        universe = MagicMock()
1552→        universe.get_groups.return_value = {"test_group": ["AAPL"]}
1553→
1554→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=1)
1555→        with patch(
1556→            "mytrader.backtest.matrix_backtest._backtest_batch",
1557→            side_effect=mock_backtest_batch,
1558→        ):
1559→            report = mb.run(
1560→                strategies=["dual_ma"],
1561→                param_grids={
1562→                    "dual_ma": {"fast": [5, 10], "slow": [20, 50]}
1563→                },
1564→            )
1565→
1566→        # 验证：选择参数 B（fast=10, slow=50，高 alpha）
1567→        gr = next(
1568→            (r for r in report.group_results if r.group_id == "test_group"),
1569→            None,
1570→        )
1571→        assert gr is not None, "应至少有一个 GroupBacktestResult"
1572→        assert gr.params.get("fast") == 10, (
1573→            f"应选高 alpha 的参数 B (fast=10)，实际选了 {gr.params}"
1574→        )
1575→        assert gr.backtest_alpha > 5.0, (
1576→            f"B 的 alpha 应 > 5%，实际 {gr.backtest_alpha:.4f}"
1577→        )
1578→
1579→
1580→class TestEnsembleWeightsUsesAlpha:
1581→    """_optimize_ensemble_weights 从 Sharpe 改为 Alpha。"""
1582→
1583→    def test_ensemble_weights_use_alpha(self):
1584→        """两个策略的权重应基于 alpha 分配，alpha 高的策略权重大。"""
1585→        n = 252
1586→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
1587→        spy_returns = pd.Series(np.random.normal(0.0004, 0.001, n), index=idx)
1588→
1589→        # 策略 A：alpha=0（与 SPY 持平）
1590→
---
1505→
1506→        # 参数 A 的收益：低波动低收益 → 高 Sharpe 但低 alpha
1507→        np.random.seed(42)
1508→        returns_a = pd.Series(
1509→            np.random.normal(0.0005, 0.002, n), index=idx  # 与 SPY 接近，alpha≈0
1510→        )
1511→        # 参数 B 的收益：高波动高收益 → 低 Sharpe 但高 alpha
1512→        returns_b = pd.Series(
1513→            np.random.normal(0.0012, 0.008, n), index=idx  # 远超 SPY，alpha>0
1514→        )
1515→
1516→        # 验证前提
1517→        sharpe_a = _compute_sharpe(returns_a)
1518→        sharpe_b = _compute_sharpe(returns_b)
1519→        alpha_a = _compute_alpha(returns_a, spy_returns)
1520→        alpha_b = _compute_alpha(returns_b, spy_returns)
1521→        assert sharpe_a > sharpe_b, (
1522→            f"A 的 Sharpe({sharpe_a:.4f}) 应 > B({sharpe_b:.4f})"
1523→        )
1524→        assert alpha_b > alpha_a, (
1525→            f"B 的 alpha({alpha_b:.4f}) 应 > A({alpha_a:.4f})"
1526→        )
1527→
1528→        # 根据参数选择返回不同收益（迭代 #10：mock _backtest_batch）
1529→        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
1530→            results = []
1531→            for sym, df in data.items():
1532→                if df is None or df.empty or len(df) < 30:
1533→                    continue
1534→                if params.get("fast") == 5:  # 参数 A
1535→                    results.append(SingleBacktestResult(
1536→                        sym, strategy_name, params, sharpe_a, 10.0, 5.0, 55.0, 10, returns_a
1537→                    ))
1538→                else:  # 参数 B (fast=10)
1539→                    results.append(SingleBacktestResult(
1540→                        sym, strategy_name, params, sharpe_b, 30.0, 8.0, 50.0, 10, returns_b
1541→                    ))
1542→            return results
1543→
1544→        df_up = _make_ohlcv(n, trend="up")
1545→        store = MagicMock()
1546→        store.get_bars_multi.side_effect = lambda symbols, start, end, timeframe="1d": {
1547→            s: {"AAPL": df_up, "SPY": spy_df}[s] for s in symbols
1548→            if s in {"AAPL", "SPY"}
1549→        }
1550→
1551→        universe = MagicMock()
1552→        universe.get_groups.return_value = {"test_group": ["AAPL"]}
1553→
1554→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=1)
1555→        with patch(
1556→            "mytrader.backtest.matrix_backtest._backtest_batch",
1557→            side_effect=mock_backtest_batch,
1558→        ):
1559→            report = mb.run(
1560→                strategies=["dual_ma"],
1561→                param_grids={
1562→                    "dual_ma": {"fast": [5, 10], "slow": [20, 50]}
1563→                },
1564→            )
1565→
1566→        # 验证：选择参数 B（fast=10, slow=50，高 alpha）
1567→        gr = next(
1568→            (r for r in report.group_results if r.group_id == "test_group"),
1569→            None,
1570→        )
1571→        assert gr is not None, "应至少有一个 GroupBacktestResult"
1572→        assert gr.params.get("fast") == 10, (
1573→            f"应选高 alpha 的参数 B (fast=10)，实际选了 {gr.params}"
1574→        )
1575→        assert gr.backtest_alpha > 5.0, (
1576→            f"B 的 alpha 应 > 5%，实际 {gr.backtest_alpha:.4f}"
1577→        )
1578→
1579→
1580→class TestEnsembleWeightsUsesAlpha:
1581→    """_optimize_ensemble_weights 从 Sharpe 改为 Alpha。"""
1582→
1583→    def test_ensemble_weights_use_alpha(self):
1584→        """两个策略的权重应基于 alpha 分配，alpha 高的策略权重大。"""
1585→        n = 252
1586→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
1587→        spy_returns = pd.Series(np.random.normal(0.0004, 0.001, n), index=idx)
1588→
1589→        # 策略 A：alpha=0（与 SPY 持平）
1590→
---
I
---
 need
---
 to
---
 update
---
 the
---
 mocked
---
 `
---
Single
---
Back
---
test
---
Result
---
`
---
 constructions
---
 in
---
 tests
---
 that
---
 use
---
 mocked
---
 `_
---
back
---
test
---
_batch
---
`
---
 to
---
 set
---
 `
---
closed
---
_tr
---
ades
---
 >
---
 
---
0
---
`.
---
 The
---
 
---
4
---
 places
---
 are
---
 at
---
 lines
---
 
---
110
---
2
---
,
---
 
---
110
---
6
---
,
---
 
---
120
---
7
---
,
---
 
---
121
---
1
---
,
---
 
---
134
---
8
---
,
---
 
---
153
---
5
---
,
---
 
---
153
---
9
---
.


---
Each
---
 `
---
Single
---
Back
---
test
---
Result
---
(sym
---
,
---
 strategy
---
_name
---
,
---
 params
---
,
---
 shar
---
pe
---
,
---
 total
---
_return
---
_pct
---
,
---
 max
---
_draw
---
down
---
_pct
---
,
---
 win
---
_rate
---
_pct
---
,
---
 total
---
_tr
---
ades
---
,
---
 daily
---
_returns
---
)`
---
 should
---
 be
---
 updated
---
 to
---
 pass
---
 `
---
closed
---
_tr
---
ades
---
=<
---
some
---
 positive
---
 value
---
>`
---
 as
---
 a
---
 kw
---
arg
---
.


---
The
---
 simplest
---
 approach
---
:
---
 add
---
 `
---
closed
---
_tr
---
ades
---
=
---
5
---
`
---
 (
---
or
---
 matching
---
 the
---
 total
---
_tr
---
ades
---
 value
---
)
---
 to
---
 each
---
 of
---
 these
---
 mocked
---
 constructions
---
.


---
Let
---
 me
---
 do
---
 this
---
 with
---
 targeted
---
 edits
---
 for
---
 each
---
 test
---
.
---
 Since
---
 the
---
 patterns
---
 are
---
 similar
---
 (
---
some
---
 with
---
 returns
---
_a
---
,
---
 some
---
 returns
---
_b
---
,
---
 some
---
 returns
---
_g
---
ar
---
bage
---
),
---
 I
---
 need
---
 to
---
 use
---
 enough
---
 context
---
 for
---
 unique
---
 matches
---
.


---
Actually
---
,
---
 I
---
 realize
---
 there
---
's
---
 another
---
 approach
---
:
---
 I
---
 could
---
 make
---
 the
---
 deg
---
enerate
---
 filter
---
 only
---
 kick
---
 in
---
 when
---
 there
---
 are
---
 multiple
---
 symbols
---
 (
---
to
---
 avoid
---
 breaking
---
 tests
---
 that
---
 use
---
 a
---
 single
---
 symbol
---
).
---
 But
---
 that
---
 would
---
 be
---
 a
---
 hack
---
 and
---
 would
---
 weaken
---
 the
---
 filter
---
's
---
 semantics
---
.


---
The
---
 correct
---
 fix
---
 is
---
 to
---
 update
---
 the
---
 mocked
---
 tests
---
 to
---
 set
---
 `
---
closed
---
_tr
---
ades
---
 >
---
 
---
0
---
`,
---
 reflecting
---
 that
---
 the
---
 mocked
---
 strategies
---
 are
---
 assumed
---
 to
---
 have
---
 proper
---
 trade
---
 closures
---
.
---
 This
---
 is
---
 consistent
---
 with
---
 the
---
 spec
---
 —
---
 these
---
 tests
---
 are
---
 testing
---
 the
---
 alpha
---
/
---
Sort
---
ino
---
 selection
---
 logic
---
,
---
 not
---
 the
---
 deg
---
enerate
---
 filter
---
.


---
Let
---
 me
---
 update
---
 each
---
 occurrence
---
.
---
 The
---
 `
---
total
---
_tr
---
ades
---
`
---
 arg
---
 in
---
 the
---
 positional
---
 construction
---
 is
---
 the
---
 
---
8
---
th
---
 arg
---
 (
---
index
---
 
---
7
---
).
---
 So
---
 `
---
Single
---
Back
---
test
---
Result
---
(sym
---
,
---
 strategy
---
_name
---
,
---
 params
---
,
---
 
---
1
---
.
---
0
---
,
---
 
---
10
---
.
---
0
---
,
---
 
---
5
---
.
---
0
---
,
---
 
---
55
---
.
---
0
---
,
---
 
---
10
---
,
---
 returns
---
_a
---
)`
---
 —
---
 the
---
 `
---
10
---
`
---
 is
---
 total
---
_tr
---
ades
---
.
---
 I
---
'll
---
 set
---
 closed
---
_tr
---
ades
---
=
---
10
---
 as
---
 a
---
 kw
---
arg
---
 too
---
.


---
Actually
---
,
---
 looking
---
 at
---
 the
---
 test
---
 at
---
 line
---
 
---
134
---
8
---
:
---
 `
---
Single
---
Back
---
test
---
Result
---
(sym
---
,
---
 strategy
---
_name
---
,
---
 params
---
,
---
 
---
0
---
.
---
3
---
,
---
 
---
5
---
.
---
0
---
,
---
 
---
10
---
.
---
0
---
,
---
 
---
50
---
.
---
0
---
,
---
 
---
3
---
,
---
 returns
---
_g
---
ar
---
bage
---
)`
---
 —
---
 total
---
_tr
---
ades
---
=
---
3
---
.
---
 I
---
'll
---
 set
---
 closed
---
_tr
---
ades
---
=
---
3
---
.


---
Let
---
 me
---
 also
---
 check
---
 the
---
 tests
---
 that
---
 don
---
't
---
 mock
---
 —
---
 like
---
 `
---
test
---
_top
---
_k
---
_selection
---
_
---
uses
---
_alpha
---
`
---
 test
---
 setup
---
.
---
 Wait
---
,
---
 those
---
 tests
---
 DO
---
 use
---
 mock
---
.
---
 Let
---
 me
---
 check
---
 `
---
Test
---
En
---
semble
---
Weights
---
Uses
---
Alpha
---
`
---
 and
---
 other
---
 tests
---
 at
---
 line
---
 
---
159
---
4
---
,
---
 
---
162
---
5
---
,
---
 
---
164
---
9
---
:
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py","limit":70,"offset":1583}
---
1583→    def test_ensemble_weights_use_alpha(self):
1584→        """两个策略的权重应基于 alpha 分配，alpha 高的策略权重大。"""
1585→        n = 252
1586→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
1587→        spy_returns = pd.Series(np.random.normal(0.0004, 0.001, n), index=idx)
1588→
1589→        # 策略 A：alpha=0（与 SPY 持平）
1590→        returns_a = pd.Series(np.random.normal(0.0004, 0.003, n), index=idx)
1591→        # 策略 B：alpha 高（远超 SPY）
1592→        returns_b = pd.Series(np.random.normal(0.0012, 0.005, n), index=idx)
1593→
1594→        results_a = [SingleBacktestResult(
1595→            "S1", "strat_a", {}, 1.0, 10.0, 5.0, 55.0, 10, returns_a
1596→        )]
1597→        results_b = [SingleBacktestResult(
1598→            "S2", "strat_b", {}, 1.5, 30.0, 8.0, 50.0, 10, returns_b
1599→        )]
1600→
1601→        group_results = [
1602→            ("strat_a", {}, results_a),
1603→            ("strat_b", {}, results_b),
1604→        ]
1605→
1606→        weights = _optimize_ensemble_weights(group_results, spy_returns=spy_returns)
1607→
1608→        # B 的 alpha 更高 → 权重应更大
1609→        weights_dict = {s: w for s, _, w in weights}
1610→        assert weights_dict["strat_b"] > weights_dict["strat_a"], (
1611→            f"B 的 alpha 更高，权重应大于 A，"
1612→            f"实际 A={weights_dict['strat_a']:.4f}, B={weights_dict['strat_b']:.4f}"
1613→        )
1614→        # 权重和 = 1.0
1615→        total = sum(weights_dict.values())
1616→        assert abs(total - 1.0) < 1e-6, f"权重和应为 1.0，实际 {total:.6f}"
1617→
1618→    def test_ensemble_weights_spy_unavailable_degrades_to_equal(self):
1619→        """SPY 数据不可用时 alpha 降级为 0 → 退化为等权。"""
1620→        n = 100
1621→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
1622→        returns_a = pd.Series(np.random.normal(0.001, 0.005, n), index=idx)
1623→        returns_b = pd.Series(np.random.normal(0.002, 0.008, n), index=idx)
1624→
1625→        results_a = [SingleBacktestResult(
1626→            "S1", "strat_a", {}, 1.0, 10.0, 5.0, 55.0, 10, returns_a
1627→        )]
1628→        results_b = [SingleBacktestResult(
1629→            "S2", "strat_b", {}, 1.5, 30.0, 8.0, 50.0, 10, returns_b
1630→        )]
1631→
1632→        group_results = [
1633→            ("strat_a", {}, results_a),
1634→            ("strat_b", {}, results_b),
1635→        ]
1636→
1637→        # spy_returns=None → alpha=0 → 退化为等权（max(0, 0.01)）
1638→        weights = _optimize_ensemble_weights(group_results, spy_returns=None)
1639→        weights_dict = {s: w for s, _, w in weights}
1640→        # 等权：各 0.5
1641→        assert abs(weights_dict["strat_a"] - 0.5) < 1e-6
1642→        assert abs(weights_dict["strat_b"] - 0.5) < 1e-6
1643→
1644→    def test_ensemble_weights_single_strategy(self):
1645→        """单策略时直接返回权重 1.0。"""
1646→        n = 100
1647→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
1648→        returns = pd.Series(np.random.normal(0.001, 0.005, n), index=idx)
1649→        results = [SingleBacktestResult(
1650→            "S1", "strat_a", {}, 1.0, 10.0, 5.0, 55.0, 10, returns
1651→        )]
1652→
1653→
---
1583→    def test_ensemble_weights_use_alpha(self):
1584→        """两个策略的权重应基于 alpha 分配，alpha 高的策略权重大。"""
1585→        n = 252
1586→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
1587→        spy_returns = pd.Series(np.random.normal(0.0004, 0.001, n), index=idx)
1588→
1589→        # 策略 A：alpha=0（与 SPY 持平）
1590→        returns_a = pd.Series(np.random.normal(0.0004, 0.003, n), index=idx)
1591→        # 策略 B：alpha 高（远超 SPY）
1592→        returns_b = pd.Series(np.random.normal(0.0012, 0.005, n), index=idx)
1593→
1594→        results_a = [SingleBacktestResult(
1595→            "S1", "strat_a", {}, 1.0, 10.0, 5.0, 55.0, 10, returns_a
1596→        )]
1597→        results_b = [SingleBacktestResult(
1598→            "S2", "strat_b", {}, 1.5, 30.0, 8.0, 50.0, 10, returns_b
1599→        )]
1600→
1601→        group_results = [
1602→            ("strat_a", {}, results_a),
1603→            ("strat_b", {}, results_b),
1604→        ]
1605→
1606→        weights = _optimize_ensemble_weights(group_results, spy_returns=spy_returns)
1607→
1608→        # B 的 alpha 更高 → 权重应更大
1609→        weights_dict = {s: w for s, _, w in weights}
1610→        assert weights_dict["strat_b"] > weights_dict["strat_a"], (
1611→            f"B 的 alpha 更高，权重应大于 A，"
1612→            f"实际 A={weights_dict['strat_a']:.4f}, B={weights_dict['strat_b']:.4f}"
1613→        )
1614→        # 权重和 = 1.0
1615→        total = sum(weights_dict.values())
1616→        assert abs(total - 1.0) < 1e-6, f"权重和应为 1.0，实际 {total:.6f}"
1617→
1618→    def test_ensemble_weights_spy_unavailable_degrades_to_equal(self):
1619→        """SPY 数据不可用时 alpha 降级为 0 → 退化为等权。"""
1620→        n = 100
1621→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
1622→        returns_a = pd.Series(np.random.normal(0.001, 0.005, n), index=idx)
1623→        returns_b = pd.Series(np.random.normal(0.002, 0.008, n), index=idx)
1624→
1625→        results_a = [SingleBacktestResult(
1626→            "S1", "strat_a", {}, 1.0, 10.0, 5.0, 55.0, 10, returns_a
1627→        )]
1628→        results_b = [SingleBacktestResult(
1629→            "S2", "strat_b", {}, 1.5, 30.0, 8.0, 50.0, 10, returns_b
1630→        )]
1631→
1632→        group_results = [
1633→            ("strat_a", {}, results_a),
1634→            ("strat_b", {}, results_b),
1635→        ]
1636→
1637→        # spy_returns=None → alpha=0 → 退化为等权（max(0, 0.01)）
1638→        weights = _optimize_ensemble_weights(group_results, spy_returns=None)
1639→        weights_dict = {s: w for s, _, w in weights}
1640→        # 等权：各 0.5
1641→        assert abs(weights_dict["strat_a"] - 0.5) < 1e-6
1642→        assert abs(weights_dict["strat_b"] - 0.5) < 1e-6
1643→
1644→    def test_ensemble_weights_single_strategy(self):
1645→        """单策略时直接返回权重 1.0。"""
1646→        n = 100
1647→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
1648→        returns = pd.Series(np.random.normal(0.001, 0.005, n), index=idx)
1649→        results = [SingleBacktestResult(
1650→            "S1", "strat_a", {}, 1.0, 10.0, 5.0, 55.0, 10, returns
1651→        )]
1652→
1653→
---
The
---
 Test
---
En
---
semble
---
Weights
---
Uses
---
Alpha
---
 tests
---
 call
---
 `_
---
optimize
---
_
---
ensemble
---
_weights
---
`
---
 directly
---
 (
---
not
---
 through
---
 `_
---
run
---
_group
---
`
---
),
---
 so
---
 they
---
 don
---
't
---
 go
---
 through
---
 the
---
 deg
---
enerate
---
 filter
---
.
---
 Those
---
 tests
---
 should
---
 still
---
 pass
---
.


---
The
---
 failing
---
 tests
---
 are
---
 only
---
 the
---
 ones
---
 that
---
 mock
---
 `_
---
back
---
test
---
_batch
---
`
---
 AND
---
 call
---
 `
---
mb
---
.run
---
(...
---
)`
---
 (
---
which
---
 internally
---
 calls
---
 `_
---
run
---
_group
---
`
---
 with
---
 the
---
 sanity
---
 filter
---
).
---
 I
---
 need
---
 to
---
 update
---
 those
---
:


---
1
---
.
---
 `
---
test
---
_top
---
_k
---
_selection
---
_
---
uses
---
_alpha
---
`
---
 —
---
 lines
---
 
---
110
---
2
---
,
---
 
---
110
---
6
---


---
2
---
.
---
 `
---
test
---
_sort
---
ino
---
_filter
---
_ex
---
cludes
---
_g
---
ar
---
bage
---
`
---
 —
---
 lines
---
 
---
120
---
7
---
,
---
 
---
121
---
1
---


---
3
---
.
---
 `
---
test
---
_f
---
allback
---
_when
---
_no
---
_sort
---
ino
---
_com
---
pliant
---
`
---
 (
---
line
---
 
---
134
---
8
---
,
---
 the
---
 `
---
returns
---
_g
---
ar
---
bage
---
`
---
 one
---
)
---
 —
---
 line
---
 
---
134
---
8
---


---
4
---
.
---
 `
---
test
---
_per
---
_strategy
---
_best
---
_params
---
_
---
uses
---
_alpha
---
`
---
 —
---
 lines
---
 
---
153
---
5
---
,
---
 
---
153
---
9
---



---
Let
---
 me
---
 also
---
 check
---
 if
---
 there
---
's
---
 a
---
 `
---
test
---
_f
---
allback
---
_when
---
_no
---
_dd
---
_com
---
pliant
---
`
---
 test
---
 that
---
 mocks
---
 _
---
back
---
test
---
_batch
---
.
---
 Looking
---
 at
---
 line
---
 
---
143
---
0
---
+:
---
让我
---
检查
---
一下
---
第
---
 
---
5
---
 个
---
测试
---
（
---
`
---
test
---
_f
---
allback
---
_when
---
_no
---
_dd
---
_com
---
pliant
---
`
---
）：
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py","limit":70,"offset":1385}
---
1385→        # 权重仍产出（DD 合规），dd_constrained=False
1386→        weights = report.groups.get("test_group", [])
1387→        if weights:
1388→            for w in weights:
1389→                assert w["dd_constrained"] is False, (
1390→                    "DD 合规时 dd_constrained 应为 False（Sortino fallback 不影响）"
1391→                )
1392→
1393→    def test_fallback_when_no_dd_compliant(self, tmp_path):
1394→        """所有候选 DD > 20% → 触发 Tier 3 fallback（按 DD 升序）。
1395→
1396→        场景：复用 test_fallback_when_no_compliant_candidates 的数据构造，
1397→        验证 dd_constrained=True（与迭代 #3 行为一致）。
1398→        """
1399→        store = MagicMock()
1400→        n = 400
1401→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
1402→        close = (
1403→            [100.0 * (1 - 0.002 * i) for i in range(200)]
1404→            + [60.0 * (1 - 0.005 * (i - 200)) for i in range(200, n)]
1405→        )
1406→        close = [max(c, 1.0) for c in close]
1407→        df_crash = pd.DataFrame({
1408→            "open": [c - 0.3 for c in close],
1409→            "high": [c + 0.5 for c in close],
1410→            "low": [c - 0.5 for c in close],
1411→            "close": close,
1412→            "volume": [1_000_000] * n,
1413→        }, index=idx)
1414→        # SPY 数据（让 alpha 不降级，验证 DD fallback 优先于 Sortino 过滤）
1415→        spy_close = [100.0 * (1.0004 ** i) for i in range(n)]
1416→        spy_df = pd.DataFrame({
1417→            "open": [c - 0.1 for c in spy_close],
1418→            "high": [c + 0.5 for c in spy_close],
1419→            "low": [c - 0.5 for c in spy_close],
1420→            "close": spy_close,
1421→            "volume": [1_000_000] * n,
1422→        }, index=idx)
1423→
1424→        def get_bars_multi(symbols, start, end, timeframe="1d"):
1425→            mapping = {"AAPL": df_crash, "SPY": spy_df}
1426→            return {s: mapping[s] for s in symbols if s in mapping}
1427→
1428→        store.get_bars_multi.side_effect = get_bars_multi
1429→
1430→        universe = MagicMock()
1431→        universe.get_groups.return_value = {"volatile_group": ["AAPL", "MSFT"]}
1432→
1433→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
1434→        report = mb.run(
1435→            strategies=["rsi_mean_revert"],
1436→            param_grids={"rsi_mean_revert": {
1437→                "period": [14], "oversold": [35], "overbought": [65]
1438→            }},
1439→            output_file=tmp_path / "weights_fallback_dd.json",
1440→        )
1441→
1442→        has_weights = any(weights for weights in report.groups.values() if weights)
1443→        if has_weights:
1444→            for gid, weights in report.groups.items():
1445→                for w in weights:
1446→                    if w.get("backtest_max_drawdown", 0) > MAX_PORTFOLIO_DRAWDOWN_PCT:
1447→                        assert w["dd_constrained"] is True, (
1448→                            f"{gid}: DD={w['backtest_max_drawdown']:.1f}% > 20% "
1449→                            f"但 dd_constrained 为 False（Tier 3 应触发）"
1450→                        )
1451→
1452→    def test_alpha_field_in_weights_json(self, mock_store, mock_universe, tmp_path):
1453→        """strategy_weights.json 每个权重条目含 backtest_alpha 字段。"""
1454→        output = tmp_path / "weights_with_alpha.json"
1455→
---
1385→        # 权重仍产出（DD 合规），dd_constrained=False
1386→        weights = report.groups.get("test_group", [])
1387→        if weights:
1388→            for w in weights:
1389→                assert w["dd_constrained"] is False, (
1390→                    "DD 合规时 dd_constrained 应为 False（Sortino fallback 不影响）"
1391→                )
1392→
1393→    def test_fallback_when_no_dd_compliant(self, tmp_path):
1394→        """所有候选 DD > 20% → 触发 Tier 3 fallback（按 DD 升序）。
1395→
1396→        场景：复用 test_fallback_when_no_compliant_candidates 的数据构造，
1397→        验证 dd_constrained=True（与迭代 #3 行为一致）。
1398→        """
1399→        store = MagicMock()
1400→        n = 400
1401→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
1402→        close = (
1403→            [100.0 * (1 - 0.002 * i) for i in range(200)]
1404→            + [60.0 * (1 - 0.005 * (i - 200)) for i in range(200, n)]
1405→        )
1406→        close = [max(c, 1.0) for c in close]
1407→        df_crash = pd.DataFrame({
1408→            "open": [c - 0.3 for c in close],
1409→            "high": [c + 0.5 for c in close],
1410→            "low": [c - 0.5 for c in close],
1411→            "close": close,
1412→            "volume": [1_000_000] * n,
1413→        }, index=idx)
1414→        # SPY 数据（让 alpha 不降级，验证 DD fallback 优先于 Sortino 过滤）
1415→        spy_close = [100.0 * (1.0004 ** i) for i in range(n)]
1416→        spy_df = pd.DataFrame({
1417→            "open": [c - 0.1 for c in spy_close],
1418→            "high": [c + 0.5 for c in spy_close],
1419→            "low": [c - 0.5 for c in spy_close],
1420→            "close": spy_close,
1421→            "volume": [1_000_000] * n,
1422→        }, index=idx)
1423→
1424→        def get_bars_multi(symbols, start, end, timeframe="1d"):
1425→            mapping = {"AAPL": df_crash, "SPY": spy_df}
1426→            return {s: mapping[s] for s in symbols if s in mapping}
1427→
1428→        store.get_bars_multi.side_effect = get_bars_multi
1429→
1430→        universe = MagicMock()
1431→        universe.get_groups.return_value = {"volatile_group": ["AAPL", "MSFT"]}
1432→
1433→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
1434→        report = mb.run(
1435→            strategies=["rsi_mean_revert"],
1436→            param_grids={"rsi_mean_revert": {
1437→                "period": [14], "oversold": [35], "overbought": [65]
1438→            }},
1439→            output_file=tmp_path / "weights_fallback_dd.json",
1440→        )
1441→
1442→        has_weights = any(weights for weights in report.groups.values() if weights)
1443→        if has_weights:
1444→            for gid, weights in report.groups.items():
1445→                for w in weights:
1446→                    if w.get("backtest_max_drawdown", 0) > MAX_PORTFOLIO_DRAWDOWN_PCT:
1447→                        assert w["dd_constrained"] is True, (
1448→                            f"{gid}: DD={w['backtest_max_drawdown']:.1f}% > 20% "
1449→                            f"但 dd_constrained 为 False（Tier 3 应触发）"
1450→                        )
1451→
1452→    def test_alpha_field_in_weights_json(self, mock_store, mock_universe, tmp_path):
1453→        """strategy_weights.json 每个权重条目含 backtest_alpha 字段。"""
1454→        output = tmp_path / "weights_with_alpha.json"
1455→
---
`
---
test
---
_f
---
allback
---
_when
---
_no
---
_dd
---
_com
---
pliant
---
`
---
 uses
---
 real
---
 `_
---
back
---
test
---
_batch
---
`
---
 (
---
no
---
 mock
---
),
---
 so
---
 `
---
closed
---
_tr
---
ades
---
`
---
 will
---
 be
---
 populated
---
 properly
---
.
---
 Same
---
 for
---
 `
---
test
---
_alpha
---
_field
---
_in
---
_weights
---
_json
---
`,
---
 `
---
test
---
_group
---
_results
---
_have
---
_back
---
test
---
_alpha
---
`,
---
 `
---
test
---
_per
---
_strategy
---
_best
---
_params
---
_
---
uses
---
_alpha
---
`
---
 (
---
line
---
 
---
153
---
5
---
 is
---
 mocked
---
,
---
 I
---
 need
---
 to
---
 check
---
).


---
Wait
---
,
---
 I
---
 need
---
 to
---
 look
---
 at
---
 the
---
 test
---
 at
---
 line
---
 
---
149
---
2
---
+
---
 for
---
 `
---
test
---
_per
---
_strategy
---
_best
---
_params
---
_
---
uses
---
_alpha
---
`:
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py","limit":12,"offset":1485}
---
1485→    def test_per_strategy_best_params_uses_alpha(self, tmp_path):
1486→        """per-strategy best params 选择使用 Alpha 而非 Sharpe。
1487→
1488→        场景：两个参数组合 A (fast=5, slow=20) 和 B (fast=10, slow=50)，
1489→        A 的 Sharpe 高但 alpha 低，B 的 Sharpe 低但 alpha 高。
1490→        验证最终 GroupBacktestResult.params 是 B（高 alpha）。
1491→        """
1492→        from unittest.mock import patch
1493→
1494→        n = 300
1495→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
1496→        spy_close = [100.0 * (1.0004 ** i) for i in range(n)]
1497→
---
1485→    def test_per_strategy_best_params_uses_alpha(self, tmp_path):
1486→        """per-strategy best params 选择使用 Alpha 而非 Sharpe。
1487→
1488→        场景：两个参数组合 A (fast=5, slow=20) 和 B (fast=10, slow=50)，
1489→        A 的 Sharpe 高但 alpha 低，B 的 Sharpe 低但 alpha 高。
1490→        验证最终 GroupBacktestResult.params 是 B（高 alpha）。
1491→        """
1492→        from unittest.mock import patch
1493→
1494→        n = 300
1495→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
1496→        spy_close = [100.0 * (1.0004 ** i) for i in range(n)]
1497→
---
现在
---
让我
---
更新
---
那
---
 
---
4
---
 个
---
使用了
---
 mock
---
 `_
---
back
---
test
---
_batch
---
`
---
 的
---
测试
---
。
---
我
---
将在
---
每个
---
 mock
---
 的
---
 `
---
Single
---
Back
---
test
---
Result
---
`
---
 中
---
添加
---
 `
---
closed
---
_tr
---
ades
---
=<
---
value
---
>`
---
：
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py","new_string":"                if strategy_name == \"dual_ma\":\n                    results.append(SingleBacktestResult(\n                        sym, strategy_name, params, 1.0, 10.0, 5.0, 55.0, 10, returns_a,\n                        closed_trades=10,\n                    ))\n                else:  # rsi_mean_revert\n                    results.append(SingleBacktestResult(\n                        sym, strategy_name, params, 1.0, 30.0, 8.0, 50.0, 10, returns_b,\n                        closed_trades=10,\n                    ))","old_string":"                if strategy_name == \"dual_ma\":\n                    results.append(SingleBacktestResult(\n                        sym, strategy_name, params, 1.0, 10.0, 5.0, 55.0, 10, returns_a\n                    ))\n                else:  # rsi_mean_revert\n                    results.append(SingleBacktestResult(\n                        sym, strategy_name, params, 1.0, 30.0, 8.0, 50.0, 10, returns_b\n                    ))","replace_all":false}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py","new_string":"                if strategy_name == \"dual_ma\":\n                    results.append(SingleBacktestResult(\n                        sym, strategy_name, params, 0.5, 15.0, 10.0, 50.0, 5, returns_a,\n                        closed_trades=5,\n                    ))\n                else:  # rsi_mean_revert\n                    results.append(SingleBacktestResult(\n                        sym, strategy_name, params, 1.0, 20.0, 5.0, 55.0, 10, returns_b,\n                        closed_trades=10,\n                    ))","old_string":"                if strategy_name == \"dual_ma\":\n                    results.append(SingleBacktestResult(\n                        sym, strategy_name, params, 0.5, 15.0, 10.0, 50.0, 5, returns_a\n                    ))\n                else:  # rsi_mean_revert\n                    results.append(SingleBacktestResult(\n                        sym, strategy_name, params, 1.0, 20.0, 5.0, 55.0, 10, returns_b\n                    ))","replace_all":false}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py","new_string":"                results.append(SingleBacktestResult(\n                    sym, strategy_name, params, 0.3, 5.0, 10.0, 50.0, 3, returns_garbage,\n                    closed_trades=3,\n                ))","old_string":"                results.append(SingleBacktestResult(\n                    sym, strategy_name, params, 0.3, 5.0, 10.0, 50.0, 3, returns_garbage\n                ))","replace_all":false}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py","new_string":"                if params.get(\"fast\") == 5:  # 参数 A\n                    results.append(SingleBacktestResult(\n                        sym, strategy_name, params, sharpe_a, 10.0, 5.0, 55.0, 10, returns_a,\n                        closed_trades=10,\n                    ))\n                else:  # 参数 B (fast=10)\n                    results.append(SingleBacktestResult(\n                        sym, strategy_name, params, sharpe_b, 30.0, 8.0, 50.0, 10, returns_b,\n                        closed_trades=10,\n                    ))","old_string":"                if params.get(\"fast\") == 5:  # 参数 A\n                    results.append(SingleBacktestResult(\n                        sym, strategy_name, params, sharpe_a, 10.0, 5.0, 55.0, 10, returns_a\n                    ))\n                else:  # 参数 B (fast=10)\n                    results.append(SingleBacktestResult(\n                        sym, strategy_name, params, sharpe_b, 30.0, 8.0, 50.0, 10, returns_b\n                    ))","replace_all":false}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py
---
现在
---
让我
---
同时也
---
更新
---
 `
---
test
---
_batch
---
_back
---
test
---
.py
---
`
---
 
---
中的
---
 `_
---
assert
---
_results
---
_match
---
`
---
 
---
辅
---
助
---
函数
---
，
---
以
---
同时
---
检查
---
 `
---
closed
---
_tr
---
ades
---
`
---
 
---
的一致
---
性
---
（
---
根据
---
 spec
---
 要求
---
：“
---
batch
---
 与
---
 single
---
 数
---
值
---
必须
---
一致
---
”
---
）：
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/tests/test_batch_backtest.py","new_string":"    assert old.total_trades == new.total_trades, msg(\n        f\"total_trades mismatch: old={old.total_trades}, new={new.total_trades}\"\n    )\n    # 迭代 #11：closed_trades 严格一致（与 total_trades 同口径，从 vbt 提取）\n    assert old.closed_trades == new.closed_trades, msg(\n        f\"closed_trades mismatch: old={old.closed_trades}, new={new.closed_trades}\"\n    )\n    # sortino 从 daily_returns 派生，应严格一致\n    assert abs(old.sortino - new.sortino) < 1e-6, msg(\n        f\"sortino mismatch: old={old.sortino}, new={new.sortino}\"\n    )","old_string":"    assert old.total_trades == new.total_trades, msg(\n        f\"total_trades mismatch: old={old.total_trades}, new={new.total_trades}\"\n    )\n    # sortino 从 daily_returns 派生，应严格一致\n    assert abs(old.sortino - new.sortino) < 1e-6, msg(\n        f\"sortino mismatch: old={old.sortino}, new={new.sortino}\"\n    )","replace_all":false}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/tests/test_batch_backtest.py
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/tests/test_batch_backtest.py
---
同时
---
，
---
请
---
更新
---
 `
---
test
---
_batch
---
_back
---
test
---
.py
---
`
---
 
---
中的
---
 `
---
test
---
_result
---
_fields
---
_pop
---
ulated
---
`
---
，
---
以
---
包含
---
 `
---
closed
---
_tr
---
ades
---
`
---
：
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/tests/test_batch_backtest.py","new_string":"            assert isinstance(r.total_trades, int)\n            assert isinstance(r.sortino, float)\n            # 迭代 #11：closed_trades 字段必须存在且为 int\n            assert isinstance(r.closed_trades, int)\n            assert r.closed_trades >= 0\n            assert not r.daily_returns.empty","old_string":"            assert isinstance(r.total_trades, int)\n            assert isinstance(r.sortino, float)\n            assert not r.daily_returns.empty","replace_all":false}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/tests/test_batch_backtest.py
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/tests/test_batch_backtest.py
---
现在
---
让我
---
运行
---
矩阵
---
和
---
批
---
处理
---
测试
---
，
---
以
---
验证
---
现有
---
测试
---
通过
---
：
---
{"command":"PYTHONPATH=. /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_matrix_backtest.py tests/test_batch_backtest.py -q 2>&1 | tail -20","description":"Run existing matrix + batch tests after fixes"}
---
Run existing matrix + batch tests after fixes
---
Command: PYTHONPATH=. /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_matrix_backtest.py tests/test_batch_backtest.py -q 2>&1 | tail -20
Stdout: ........................................................................ [ 72%]
...........................                                              [100%]

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"command":"PYTHONPATH=. /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_matrix_backtest.py tests/test_batch_backtest.py -q 2>&1 | tail -5","description":"Get summary line"}
---
Get summary line
---
Command: PYTHONPATH=. /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_matrix_backtest.py tests/test_batch_backtest.py -q 2>&1 | tail -5
Stdout: ........................................................................ [ 72%]
...........................                                              [100%]

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"command":"PYTHONPATH=. /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_matrix_backtest.py tests/test_batch_backtest.py 2>&1 | tail -3","description":"Get pass count"}
---
Get pass count
---
Command: PYTHONPATH=. /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_matrix_backtest.py tests/test_batch_backtest.py 2>&1 | tail -3
Stdout: ........................................................................ [ 72%]
...........................                                              [100%]
99 passed in 11.99s

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
所有
---
 
---
99
---
 个
---
现有
---
测试
---
均已
---
通过
---
。
---
现在
---
我来
---
编写
---
新的
---
退化
---
过滤器
---
测试
---
：
---
{"status":"completed","taskId":"3"}
---
{"status":"in_progress","taskId":"4"}
---
Updated task #3 status
---
Updated task #3 status
---
Updated task #4 status
---
Updated task #4 status
---
###
---
 第
---
 
---
5
---
 
---
步
---
：
---
编写
---
退化
---
策略
---
过滤器
---
测试
---
{"content":"\"\"\"迭代 #11：选择器健全性门槛测试（Reject Degenerate Strategies）。\n\n验证：\n    1. `SingleBacktestResult.closed_trades` 字段被正确填充（normal 策略 > 0）\n    2. `_backtest_batch` 与 `_backtest_one` 对同一标的的 `closed_trades` 一致\n    3. `_is_degenerate_strategy` 正确识别\"近乎全标的零平仓\"的退化策略\n    4. 正常闭环策略不被误判为退化\n    5. `_run_group` 在排序前剔除退化策略（不出现在返回的 weights_list）\n    6. 全退化组返回空权重 + `no_valid_strategy=True` 标记\n    7. 低频但有平仓交易的策略不被误伤（0.8 阈值边界）\n\n背景见 `iterations/iteration_11/spec.md` + `tmp/iteration10_audit.md`。\n\"\"\"\n\nfrom __future__ import annotations\n\nfrom datetime import date\nfrom unittest.mock import MagicMock, patch\n\nimport numpy as np\nimport pandas as pd\nimport pytest\n\nfrom mytrader.backtest.matrix_backtest import (\n    DEGENERATE_NO_CLOSE_FRACTION,\n    GroupBacktestResult,\n    MatrixBacktest,\n    MatrixBacktestReport,\n    SingleBacktestResult,\n    _backtest_batch,\n    _backtest_one,\n    _is_degenerate_strategy,\n)\n\n\n# ---------------------------------------------------------------------------\n# Test data generators（与 test_batch_backtest.py 同风格）\n# ---------------------------------------------------------------------------\n\ndef _make_ohlcv(\n    n: int = 300,\n    trend: str = \"random\",\n    seed: int | None = None,\n    start: str = \"2021-01-01\",\n) -> pd.DataFrame:\n    \"\"\"生成测试 OHLCV 数据。\"\"\"\n    idx = pd.date_range(start, periods=n, freq=\"B\")\n    if trend == \"up\":\n        close = np.array([100.0 + i * 0.1 for i in range(n)])\n    elif trend == \"down\":\n        close = np.array([100.0 - i * 0.05 for i in range(n)])\n    elif trend == \"random\":\n        rng = np.random.default_rng(seed if seed is not None else 42)\n        steps = rng.normal(0, 0.5, n)\n        close = np.cumsum(np.concatenate([[100.0], steps]))[1:]\n    else:\n        raise ValueError(f\"unknown trend: {trend}\")\n\n    return pd.DataFrame(\n        {\n            \"open\":   close - 0.5,\n            \"high\":   close + 1.0,\n            \"low\":    close - 1.0,\n            \"close\":  close,\n            \"volume\": [1_000_000] * n,\n        },\n        index=idx,\n    )\n\n\ndef _make_multi_symbol_data(\n    symbols: list[str],\n    n: int = 300,\n    trend: str = \"random\",\n    seed: int = 42,\n) -> dict[str, pd.DataFrame]:\n    \"\"\"生成多标的 OHLCV 数据字典（每标的独立生成、起始日期对齐）。\"\"\"\n    return {\n        sym: _make_ohlcv(n=n, trend=trend, seed=seed + i)\n        for i, sym in enumerate(symbols)\n    }\n\n\ndef _make_mock_store(data_by_symbol: dict[str, pd.DataFrame]) -> MagicMock:\n    \"\"\"构造 Mock MarketDataStore，get_bars_multi 返回指定数据。\"\"\"\n    store = MagicMock()\n\n    def get_bars_multi(symbols, start, end, timeframe=\"1d\"):\n        return {\n            s: data_by_symbol[s] for s in symbols if s in data_by_symbol\n        }\n\n    store.get_bars_multi.side_effect = get_bars_multi\n    return store\n\n\ndef _make_mock_universe(groups: dict[str, list[str]]) -> MagicMock:\n    \"\"\"构造 Mock UniverseManager，get_groups 返回指定分组。\"\"\"\n    universe = MagicMock()\n    universe.get_groups.return_value = groups\n    return universe\n\n\n# ---------------------------------------------------------------------------\n# Test 1: closed_trades 字段被正确填充\n# ---------------------------------------------------------------------------\n\nclass TestClosedTradesPopulated:\n    \"\"\"验证 SingleBacktestResult.closed_trades 字段被正确填充。\"\"\"\n\n    def test_closed_trades_field_exists_with_default(self):\n        \"\"\"SingleBacktestResult 默认 closed_trades=0。\"\"\"\n        r = SingleBacktestResult(\n            symbol=\"X\", strategy=\"s\", params={}, sharpe=0.0,\n            total_return_pct=0.0, max_drawdown_pct=0.0, win_rate_pct=0.0,\n            total_trades=0, daily_returns=pd.Series(dtype=float),\n        )\n        assert hasattr(r, \"closed_trades\")\n        assert r.closed_trades == 0\n\n    def test_closed_trades_populated_normal_strategy(self):\n        \"\"\"正常策略（dual_ma）在 random walk 数据上应有 closed_trades > 0。\"\"\"\n        df = _make_ohlcv(300, trend=\"random\", seed=42)\n        df.index.name = \"AAA\"\n        r = _backtest_one(df, \"dual_ma\", {\"fast\": 5, \"slow\": 20})\n        assert r is not None, \"_backtest_one 应返回结果（非 None）\"\n        assert r.closed_trades > 0, (\n            f\"dual_ma 在 300 bar random walk 上应有已平仓交易，\"\n            f\"实际 closed_trades={r.closed_trades}\"\n        )\n        # closed_trades 不应超过 total_trades\n        assert r.closed_trades <= r.total_trades, (\n            f\"closed_trades({r.closed_trades}) 应 <= total_trades({r.total_trades})\"\n        )\n\n    def test_closed_trades_zero_for_entries_only_strategy(self):\n        \"\"\"只有 entry 信号没有 exit 信号的策略 closed_trades=0。\n\n        构造方法：用 rsi_trend_filter 在强趋势上涨数据上跑 —— 趋势过滤锁死\n        出场条件，仓位只能挂到末尾被 vbt 强平。\n        \"\"\"\n        # 强趋势上涨数据：close > SMA200 全程成立 → SELL 信号几乎不触发\n        df = _make_ohlcv(400, trend=\"up\")\n        df.index.name = \"UPTREND\"\n        r = _backtest_one(\n            df, \"rsi_trend_filter\",\n            {\"rsi_period\": 14, \"oversold\": 30, \"overbought\": 70, \"trend_period\": 200},\n        )\n        # rsi_trend_filter 在强上涨趋势中可能 rsi 一直不超卖 → 0 entries → 0 trades\n        # 或者偶尔超卖买入但无法触发 SELL（出场需 close<SMA200）→ 0 closed_trades\n        if r is not None:\n            # 退化情形：closed_trades 应为 0（无法完成交易闭环）\n            assert r.closed_trades == 0, (\n                f\"rsi_trend_filter 在强上涨趋势上 closed_trades 应为 0（退化），\"\n                f\"实际 {r.closed_trades}\"\n            )\n\n\n# ---------------------------------------------------------------------------\n# Test 2: batch vs single 一致性（closed_trades）\n# ---------------------------------------------------------------------------\n\nclass TestClosedTradesBatchConsistency:\n    \"\"\"验证 _backtest_batch 与 _backtest_one 对同一标的 closed_trades 一致。\"\"\"\n\n    @pytest.mark.parametrize(\n        \"strategy_name, params\",\n        [\n            (\"dual_ma\", {\"fast\": 5, \"slow\": 20}),\n            (\"rsi_mean_revert\", {\"period\": 14, \"oversold\": 30, \"overbought\": 70}),\n            (\"macd_cross\", {\"fast\": 12, \"slow\": 26, \"signal_period\": 9}),\n            (\"bollinger_band\", {\"period\": 20, \"std_dev\": 2.0}),\n        ],\n    )\n    def test_closed_trades_batch_matches_single(\n        self, strategy_name: str, params: dict\n    ) -> None:\n        \"\"\"每个策略 batch 与 single 的 closed_trades 严格一致。\"\"\"\n        data = _make_multi_symbol_data(\n            [\"AAA\", \"BBB\", \"CCC\"], n=300, trend=\"random\", seed=200\n        )\n\n        # 逐标的 single\n        single_results: dict[str, SingleBacktestResult | None] = {}\n        for sym, df in data.items():\n            df = df.copy()\n            df.index.name = sym\n            single_results[sym] = _backtest_one(df, strategy_name, params)\n\n        # batch\n        batch_results_list = _backtest_batch(data, strategy_name, params)\n        batch_results = {r.symbol: r for r in batch_results_list}\n\n        for sym, single_r in single_results.items():\n            if single_r is None:\n                assert sym not in batch_results, (\n                    f\"{strategy_name}/{params} {sym}: single=None but batch returned result\"\n                )\n                continue\n            assert sym in batch_results, (\n                f\"{strategy_name}/{params} {sym}: single returned result but batch dropped\"\n            )\n            batch_r = batch_results[sym]\n            assert single_r.closed_trades == batch_r.closed_trades, (\n                f\"{strategy_name}/{params} {sym}: closed_trades mismatch — \"\n                f\"single={single_r.closed_trades}, batch={batch_r.closed_trades}\"\n            )\n\n    def test_closed_trades_batch_matches_single_multi_symbol(self):\n        \"\"\"多标的（5 个）下 batch 的 closed_trades 与 single 逐一一致。\"\"\"\n        data = _make_multi_symbol_data(\n            [\"AAA\", \"BBB\", \"CCC\", \"DDD\", \"EEE\"], n=400, trend=\"random\", seed=300\n        )\n\n        single_closed: dict[str, int] = {}\n        for sym, df in data.items():\n            df = df.copy()\n            df.index.name = sym\n            r = _backtest_one(df, \"dual_ma\", {\"fast\": 5, \"slow\": 20})\n            single_closed[sym] = r.closed_trades if r is not None else -1\n\n        batch_results = _backtest_batch(data, \"dual_ma\", {\"fast\": 5, \"slow\": 20})\n        batch_closed = {r.symbol: r.closed_trades for r in batch_results}\n\n        for sym, expected in single_closed.items():\n            if expected == -1:\n                assert sym not in batch_closed\n            else:\n                assert sym in batch_closed, f\"{sym} missing from batch results\"\n                assert batch_closed[sym] == expected, (\n                    f\"{sym}: single closed_trades={expected}, \"\n                    f\"batch closed_trades={batch_closed[sym]}\"\n                )\n\n\n# ---------------------------------------------------------------------------\n# Test 3-4: _is_degenerate_strategy 函数行为\n# ---------------------------------------------------------------------------\n\nclass TestIsDegenerateStrategy:\n    \"\"\"_is_degenerate_strategy 单元测试。\"\"\"\n\n    def test_empty_results_is_degenerate(self):\n        \"\"\"空结果列表视为退化（True）—— 没有数据不应强行选策略。\"\"\"\n        assert _is_degenerate_strategy([]) is True\n\n    def test_all_zero_closed_is_degenerate(self):\n        \"\"\"所有标的 closed_trades=0 → 退化。\"\"\"\n        results = [\n            SingleBacktestResult(\n                f\"S{i}\", \"s\", {}, 0.0, 0.0, 0.0, 0.0, 0,\n                pd.Series(dtype=float), closed_trades=0,\n            )\n            for i in range(5)\n        ]\n        assert _is_degenerate_strategy(results) is True\n\n    def test_normal_closed_trades_not_degenerate(self):\n        \"\"\"所有标的都有平仓交易 → 不退化。\"\"\"\n        results = [\n            SingleBacktestResult(\n                f\"S{i}\", \"s\", {}, 0.0, 0.0, 0.0, 0.0, 5,\n                pd.Series(dtype=float), closed_trades=5,\n            )\n            for i in range(5)\n        ]\n        assert _is_degenerate_strategy(results) is False\n\n    def test_threshold_boundary_80pct(self):\n        \"\"\"边界：5 标的中有 4 个 closed=0（4/5=0.8）→ 退化（>= 阈值）。\"\"\"\n        # DEGENERATE_NO_CLOSE_FRACTION = 0.8, 边界 4/5=0.8 应触发\n        results = [\n            SingleBacktestResult(\n                f\"S{i}\", \"s\", {}, 0.0, 0.0, 0.0, 0.0, 0,\n                pd.Series(dtype=float), closed_trades=0,\n            )\n            for i in range(4)\n        ] + [\n            SingleBacktestResult(\n                \"S4\", \"s\", {}, 0.0, 0.0, 0.0, 0.0, 3,\n                pd.Series(dtype=float), closed_trades=3,\n            )\n        ]\n        assert _is_degenerate_strategy(results) is True, (\n            f\"4/5 = 0.8 应触发退化（>= {DEGENERATE_NO_CLOSE_FRACTION}）\"\n        )\n\n    def test_below_threshold_not_degenerate(self):\n        \"\"\"边界：5 标的中有 3 个 closed=0（3/5=0.6）→ 不退化。\"\"\"\n        results = [\n            SingleBacktestResult(\n                f\"S{i}\", \"s\", {}, 0.0, 0.0, 0.0, 0.0, 0,\n                pd.Series(dtype=float), closed_trades=0,\n            )\n            for i in range(3)\n        ] + [\n            SingleBacktestResult(\n                f\"S{i}\", \"s\", {}, 0.0, 0.0, 0.0, 0.0, 3,\n                pd.Series(dtype=float), closed_trades=3,\n            )\n            for i in range(2)\n        ]\n        assert _is_degenerate_strategy(results) is False, (\n            f\"3/5 = 0.6 < {DEGENERATE_NO_CLOSE_FRACTION}，不应触发退化\"\n        )\n\n    def test_low_frequency_strategy_not_falsely_excluded(self):\n        \"\"\"低频但闭环的策略（每标的 2-3 笔 closed_trades）不被误伤。\n\n        这是 spec §5.7 的边界测试：0.8 阈值应只拦\"近乎全标的零平仓\"，\n        不应误伤合法低频策略（如 monthly rebalance 类）。\n        \"\"\"\n        # 5 个标的，每个都有 2-3 笔平仓交易（典型低频合法策略）\n        results = [\n            SingleBacktestResult(\n                f\"S{i}\", \"low_freq\", {}, 0.5, 8.0, 5.0, 55.0, 2,\n                pd.Series(dtype=float), closed_trades=2,\n            )\n            for i in range(5)\n        ]\n        assert _is_degenerate_strategy(results) is False, (\n            \"低频但每标的都有平仓交易的策略不应被误判为退化\"\n        )\n\n    def test_mixed_one_zero_not_degenerate(self):\n        \"\"\"5 标的中 1 个 closed=0（1/5=0.2）→ 不退化。\n\n        单只标的无平仓（如刚上市数据不足）不应牵连整组判定。\n        \"\"\"\n        results = [\n            SingleBacktestResult(\n                \"S0\", \"s\", {}, 0.0, 0.0, 0.0, 0.0, 0,\n                pd.Series(dtype=float), closed_trades=0,\n            )\n        ] + [\n            SingleBacktestResult(\n                f\"S{i}\", \"s\", {}, 0.0, 0.0, 0.0, 0.0, 5,\n                pd.Series(dtype=float), closed_trades=5,\n            )\n            for i in range(1, 5)\n        ]\n        assert _is_degenerate_strategy(results) is False\n\n    def test_degenerate_threshold_constant_value(self):\n        \"\"\"DEGENERATE_NO_CLOSE_FRACTION 常量值为 0.8（保守阈值）。\"\"\"\n        assert DEGENERATE_NO_CLOSE_FRACTION == 0.8\n\n\n# ---------------------------------------------------------------------------\n# Test 5-6: _run_group 集成（剔除退化 + 全退化空仓）\n# ---------------------------------------------------------------------------\n\nclass TestRunGroupDegenerateIntegration:\n    \"\"\"_run_group 集成健全性门槛测试。\"\"\"\n\n    def test_degenerate_excluded_from_weights(self):\n        \"\"\"退化策略不出现在返回的 weights_list。\n\n        场景：mock _backtest_batch 让 dual_ma 退化（closed_trades=0），\n        rsi_mean_revert 正常（closed_trades>0）。top_k=2 时应只选\n        rsi_mean_revert，dual_ma 被健全性门槛剔除。\n        \"\"\"\n        n = 300\n        idx = pd.date_range(\"2021-01-01\", periods=n, freq=\"B\")\n        np.random.seed(42)\n        returns_a = pd.Series(np.random.normal(0.001, 0.005, n), index=idx)\n        returns_b = pd.Series(np.random.normal(0.0008, 0.003, n), index=idx)\n\n        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):\n            results = []\n            for sym, df in data.items():\n                if df is None or df.empty or len(df) < 30:\n                    continue\n                if strategy_name == \"dual_ma\":\n                    # 退化：closed_trades=0（mock 模拟 rsi_trend_filter 退化行为）\n                    results.append(SingleBacktestResult(\n                        sym, strategy_name, params, 1.0, 10.0, 5.0, 55.0, 1, returns_a,\n                        closed_trades=0,\n                    ))\n                else:  # rsi_mean_revert\n                    results.append(SingleBacktestResult(\n                        sym, strategy_name, params, 1.0, 20.0, 5.0, 55.0, 10, returns_b,\n                        closed_trades=10,\n                    ))\n            return results\n\n        # 5 标的让退化比例 5/5=100% ≥ 0.8\n        data = _make_multi_symbol_data(\n            [\"AAA\", \"BBB\", \"CCC\", \"DDD\", \"EEE\"], n=300, trend=\"random\", seed=11\n        )\n        store = _make_mock_store(data)\n        universe = _make_mock_universe({\"test_group\": list(data.keys())})\n\n        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)\n        report = MatrixBacktestReport(\n            generated_at=pd.Timestamp.now(tz=\"UTC\").isoformat(),\n            backtest_window=\"2021-01-01 ~ 2022-01-01\",\n            groups={},\n        )\n\n        with patch(\n            \"mytrader.backtest.matrix_backtest._backtest_batch\",\n            side_effect=mock_backtest_batch,\n        ):\n            weights = mb._run_group(\n                group_id=\"test_group\",\n                symbols=list(data.keys()),\n                start=date(2021, 1, 1),\n                end=date(2022, 1, 1),\n                strategies=[\"dual_ma\", \"rsi_mean_revert\"],\n                param_grids={\n                    \"dual_ma\": {\"fast\": [5], \"slow\": [20]},\n                    \"rsi_mean_revert\": {\n                        \"period\": [14], \"oversold\": [30], \"overbought\": [70]\n                    },\n                },\n                report=report,\n            )\n\n        # 退化策略 dual_ma 不应在权重中\n        strategies_in_weights = [w[\"strategy\"] for w in weights]\n        assert \"dual_ma\" not in strategies_in_weights, (\n            f\"dual_ma（退化）不应出现在权重中，实际 weights={strategies_in_weights}\"\n        )\n        assert \"rsi_mean_revert\" in strategies_in_weights, (\n            f\"rsi_mean_revert（正常）应在权重中，实际 weights={strategies_in_weights}\"\n        )\n\n    def test_all_degenerate_group_returns_empty_weights(self):\n        \"\"\"全退化组返回空权重 + no_valid_strategy 标记。\n\n        场景：mock _backtest_batch 让所有策略 closed_trades=0（全退化）。\n        验证：返回空 weights_list，report.group_results 中对应组条目\n        被标记 no_valid_strategy=True，report.warnings 含标记。\n        \"\"\"\n        n = 300\n        idx = pd.date_range(\"2021-01-01\", periods=n, freq=\"B\")\n        np.random.seed(42)\n        returns_a = pd.Series(np.random.normal(0.001, 0.005, n), index=idx)\n        returns_b = pd.Series(np.random.normal(0.0008, 0.003, n), index=idx)\n\n        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):\n            results = []\n            for sym, df in data.items():\n                if df is None or df.empty or len(df) < 30:\n                    continue\n                if strategy_name == \"dual_ma\":\n                    results.append(SingleBacktestResult(\n                        sym, strategy_name, params, 1.0, 10.0, 5.0, 55.0, 1, returns_a,\n                        closed_trades=0,\n                    ))\n                else:\n                    results.append(SingleBacktestResult(\n                        sym, strategy_name, params, 1.0, 20.0, 5.0, 55.0, 1, returns_b,\n                        closed_trades=0,\n                    ))\n            return results\n\n        data = _make_multi_symbol_data(\n            [\"AAA\", \"BBB\", \"CCC\", \"DDD\", \"EEE\"], n=300, trend=\"random\", seed=22\n        )\n        store = _make_mock_store(data)\n        universe = _make_mock_universe({\"test_group\": list(data.keys())})\n\n        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)\n        report = MatrixBacktestReport(\n            generated_at=pd.Timestamp.now(tz=\"UTC\").isoformat(),\n            backtest_window=\"2021-01-01 ~ 2022-01-01\",\n            groups={},\n        )\n\n        with patch(\n            \"mytrader.backtest.matrix_backtest._backtest_batch\",\n            side_effect=mock_backtest_batch,\n        ):\n            weights = mb._run_group(\n                group_id=\"test_group\",\n                symbols=list(data.keys()),\n                start=date(2021, 1, 1),\n                end=date(2022, 1, 1),\n                strategies=[\"dual_ma\", \"rsi_mean_revert\"],\n                param_grids={\n                    \"dual_ma\": {\"fast\": [5], \"slow\": [20]},\n                    \"rsi_mean_revert\": {\n                        \"period\": [14], \"oversold\": [30], \"overbought\": [70]\n                    },\n                },\n                report=report,\n            )\n\n        # 全退化 → 空权重\n        assert weights == [], (\n            f\"全退化组应返回空权重，实际 weights={weights}\"\n        )\n        # report.warnings 含 no_valid_strategy 标记\n        warning_text = \" \".join(report.warnings)\n        assert \"no_valid_strategy\" in warning_text, (\n            f\"report.warnings 应含 no_valid_strategy 标记，实际 warnings={report.warnings}\"\n        )\n        assert \"test_group\" in warning_text\n        # 对应 group_results 条目被标记 no_valid_strategy=True\n        # （健全性过滤发生在 candidates 构建前，但 group_results 在\n        # per-strategy best params 阶段已 append，应被标记）\n        test_group_results = [\n            gr for gr in report.group_results if gr.group_id == \"test_group\"\n        ]\n        assert len(test_group_results) > 0, (\n            \"test_group 应在 report.group_results 中有存档条目（供审计追溯）\"\n        )\n        for gr in test_group_results:\n            assert gr.no_valid_strategy is True, (\n                f\"test_group 的 GroupBacktestResult.no_valid_strategy 应为 True，\"\n                f\"实际 {gr.no_valid_strategy}\"\n            )\n\n    def test_no_valid_strategy_field_default_false(self):\n        \"\"\"GroupBacktestResult.no_valid_strategy 默认 False。\"\"\"\n        gr = GroupBacktestResult(\n            group_id=\"g\", strategy=\"s\", params={}, portfolio_sharpe=0.0,\n            avg_total_return_pct=0.0, avg_max_drawdown_pct=0.0,\n            avg_win_rate_pct=0.0, symbol_count=0,\n        )\n        assert gr.no_valid_strategy is False\n\n    def test_normal_strategies_unaffected_by_filter(self):\n        \"\"\"正常策略（都有平仓交易）不被健全性门槛影响，权重正常产出。\n\n        验证健全性门槛不会误伤正常策略 —— 用真实 _backtest_batch（不 mock）\n        跑 dual_ma 在 random walk 数据上，应正常产出权重，且不触发\n        no_valid_strategy 标记。\n        \"\"\"\n        data = _make_multi_symbol_data(\n            [\"AAA\", \"BBB\", \"CCC\"], n=300, trend=\"random\", seed=33\n        )\n        store = _make_mock_store(data)\n        universe = _make_mock_universe({\"test_group\": list(data.keys())})\n\n        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)\n        report = MatrixBacktestReport(\n            generated_at=pd.Timestamp.now(tz=\"UTC\").isoformat(),\n            backtest_window=\"2021-01-01 ~ 2022-01-01\",\n            groups={},\n        )\n\n        weights = mb._run_group(\n            group_id=\"test_group\",\n            symbols=list(data.keys()),\n            start=date(2021, 1, 1),\n            end=date(2022, 1, 1),\n            strategies=[\"dual_ma\"],\n            param_grids={\"dual_ma\": {\"fast\": [5], \"slow\": [20]}},\n            report=report,\n        )\n\n        # 正常策略应产出权重\n        assert len(weights) >= 1, (\n            f\"dual_ma 在 random walk 上应正常产出权重，实际 weights={weights}\"\n        )\n        # 不应触发 no_valid_strategy\n        for gr in report.group_results:\n            if gr.group_id == \"test_group\":\n                assert gr.no_valid_strategy is False, (\n                    \"正常策略组不应被标记 no_valid_strategy=True\"\n                )\n        # weights 中应有 backtest_dd_status 字段（验证下游逻辑未被破坏）\n        for w in weights:\n            assert \"strategy\" in w\n            assert \"weight\" in w\n","file_path":"/Users/rickouyang/Github/trade-tools/mytrader/tests/test_degenerate_filter.py"}
---
Successfully created and wrote to new file: /Users/rickouyang/Github/trade-tools/mytrader/tests/test_degenerate_filter.py
---
Successfully created and wrote to new file: /Users/rickouyang/Github/trade-tools/mytrader/tests/test_degenerate_filter.py
---
现在
---
让我
---
运行
---
新的
---
测试
---
：
---
{"command":"PYTHONPATH=. /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_degenerate_filter.py -v 2>&1 | tail -40","description":"Run new degenerate filter tests"}
---
Run new degenerate filter tests
---
Command: PYTHONPATH=. /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_degenerate_filter.py -v 2>&1 | tail -40
Stdout: ============================= test session starts ==============================
platform darwin -- Python 3.12.13, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/rickouyang/Github/trade-tools/mytrader
configfile: pyproject.toml
plugins: cov-7.1.0, anyio-4.13.0
collected 20 items

tests/test_degenerate_filter.py ....................                     [100%]

============================== 20 passed in 6.07s ==============================

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
所有
---
 
---
20
---
 个
---
新
---
测试
---
均已
---
通过
---
。
---
让我
---
检查
---
一下
---
统计
---
数量
---
：
---
{"command":"PYTHONPATH=. /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_degenerate_filter.py --collect-only -q 2>&1 | tail -25","description":"Count new tests"}
---
Count new tests
---
Command: PYTHONPATH=. /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_degenerate_filter.py --collect-only -q 2>&1 | tail -25
Stdout: tests/test_degenerate_filter.py: 20


Stderr: (empty)
Exit Code: 0
Signal: (none)
---
20
---
 tests
---
 (
---
param
---
etr
---
ized
---
 expands
---
 to
---
 
---
4
---
 +
---
 others
---
 =
---
 
---
20
---
 total
---
).
---
 Now
---
 let
---
 me
---
 run
---
 the
---
 targeted
---
 tests
---
 (
---
matrix
---
 +
---
 batch
---
 +
---
 deg
---
enerate
---
)
---
 together
---
 to
---
 confirm
---
 no
---
 regression
---
,
---
 then
---
 run
---
 the
---
 full
---
 default
---
 pytest
---
.
---
包含
---
参数
---
化
---
用
---
例
---
在内
---
，
---
共有
---
 
---
20
---
 个
---
新
---
测试
---
。
---
现在
---
运行
---
完整的
---
定向
---
测试
---
集
---
 +
---
 
---
默认
---
 pytest
---
：
---
{"status":"completed","taskId":"4"}
---
{"status":"in_progress","taskId":"5"}
---
Updated task #4 status
---
Updated task #4 status
---
Updated task #5 status
---
Updated task #5 status
---
###
---
 第
---
 
---
6
---
 
---
步
---
：
---
运行
---
针对性
---
测试
---
 +
---
 
---
默认
---
 pytest
---
{"command":"PYTHONPATH=. /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_matrix_backtest.py tests/test_batch_backtest.py tests/test_degenerate_filter.py tests/test_portfolio_backtest.py tests/test_backtest.py 2>&1 | tail -10","description":"Run all backtest-related tests"}
---
Run all backtest-related tests
---
Command: PYTHONPATH=. /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_matrix_backtest.py tests/test_batch_backtest.py tests/test_degenerate_filter.py tests/test_portfolio_backtest.py tests/test_backtest.py 2>&1 | tail -10
Stdout: ........................................................................ [ 43%]
........................................................................ [ 86%]
.......................                                                  [100%]
167 passed in 13.92s

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
所有
---
 
---
167
---
 个
---
回
---
测
---
测试
---
均已
---
通过
---
。
---
现在
---
运行
---
完整的
---
默认
---
 pytest
---
：
---
{"command":"PYTHONPATH=. /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest 2>&1 | tail -15","description":"Run full default pytest suite"}
---
Run full default pytest suite
---
Command: PYTHONPATH=. /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest 2>&1 | tail -15
Stdout: 
tests/test_risk_manager.py: 11 warnings
  /Users/rickouyang/Github/trade-tools/mytrader/mytrader/risk/circuit_breaker.py:66: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    now = datetime.utcnow()

tests/test_risk_manager.py::TestOrderIntent::test_auto_client_order_id
  /Users/rickouyang/Github/trade-tools/mytrader/tests/test_risk_manager.py:393: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    timestamp=datetime.utcnow(),

tests/test_risk_manager.py::TestOrderIntent::test_custom_client_order_id
  /Users/rickouyang/Github/trade-tools/mytrader/tests/test_risk_manager.py:408: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    timestamp=datetime.utcnow(),

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
646 passed, 16 deselected, 103 warnings in 21.94s

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
**
---
6
---
46
---
 个
---
通过
---
，
---
0
---
 个
---
失败
---
，
---
16
---
 个
---
取消
---
选择
---
（
---
实时
---
测试
---
）。
---
**
---
 
---
迭
---
代
---
 #
---
10
---
 
---
基
---
准
---
为
---
 
---
6
---
26
---
 →
---
 
---
6
---
46
---
 =
---
 新
---
增
---
 
---
20
---
 个
---
测试
---
。
---
现在
---
让我
---
更新
---
文档
---
。


---
###
---
 第
---
 
---
7
---
 
---
步
---
：
---
更新
---
设计
---
文档
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md","limit":15,"offset":385}
---
 385→| **NaN 安全处理**（迭代 #2 新增） | `_safe_float()` 拦截 NaN/None/Inf；`_safe_mean()` 拦截空列表/全 NaN | vectorbt 无交易时 stats 返回 NaN；`NaN or 0.0` 仍为 NaN（NaN 是 truthy）导致 JSON 序列化失败 |
 386→| **策略名校验**（迭代 #1 新增） | `_run_group` 进入策略循环前检查 `strategy not in STRATEGY_REGISTRY` → `logger.warning` + `continue` | 防止策略名拼写错误被静默跳过（迭代 #1 修复的 bug：`main.py` 误用 `"rsi"/"macd"/"bollinger"` 简称导致 3 个策略 6 天未跑） |
 387→| **DD 硬约束 + Fallback**（迭代 #3 新增） | top-K 选择时过滤 `portfolio_max_drawdown > 20%` 的候选；若全部超标 → 按 DD 升序取 top-K，标记 `dd_constrained=True` | Constitution L1 DD≤20% 是硬约束；无合规候选时仍需产出权重（结构性问题不能阻塞回测） |
 388→| **Alpha 排序 + Sortino 门槛**（迭代 #9 新增） | top-K 排序从 Sortino 改为 Alpha（策略年化收益 - SPY 同期年化收益）；新增 `Sortino > 0.5` 最低质量门槛 | Sortino 高 ≠ 年化高（均值回归策略天然高 Sortino 低绝对收益，alpha 为负）；Alpha 排序直接优化超额收益目标；Sortino 门槛保证基本下行质量。三级 fallback：Tier 1 DD+Sortino → Tier 2 仅 DD → Tier 3 DD 升序 |
 389→| **SPY Benchmark 获取**（迭代 #9 新增） | `_get_spy_returns(start, end)` 从 MarketDataStore 拉取 SPY 日收益率；`_compute_alpha(strat, spy)` 计算年化 alpha | SPY 不可用时 alpha 降级为 0.0（不阻塞回测），所有候选 alpha=0 ��退化为原顺序 |
 390→| **per-strategy best params 用 Alpha**（迭代 #9 新增） | 每个策略的最优参数选择从 Sharpe 改为 Alpha | 与 top-K 排序口径一致，避免 per-strategy 用 Sharpe 选低收益高稳定的参数 |
 391→| **ensemble weights 用 Alpha**（迭代 #9 新增） | `_optimize_ensemble_weights` 接收 `spy_returns` 参数，权重计算从 Sharpe 改为 Alpha | 与 top-K 排序口径一致，ensemble 权重直接反映"跑赢 SPY 的程度"；SPY 不可用时退化为等权 |
 392→| **参数按组** | 同组共用参数，不对单只优化 | 防过拟合（详见 02-strategy-engine.md 6.3） |
 393→| **历史分组对齐** | 矩阵回测使用 point-in-time 分组（按回测时间点重算波动率），而非当前静态分组 | 避免回测静态分组而实盘动态分组导致回测/实盘不一致 |
 394→| **实盘 ensemble 对齐** | MatrixBacktest 的 ensemble 权重优化须在"单点离散值聚合"语义下验证 | 实盘只取 iloc[-1] 单点离散值加权，与序列级加权不等价，权重必须在相同语义下产出 |
 395→| **Walk-Forward** | 滚动训练窗口，月度重优化 | 平衡过拟合与适应性 |
 396→
 397→### 10.4.1 Top-K 选择三级 Fallback（迭代 #9 新增）
 398→
 399→```
 400→
---
 385→| **NaN 安全处理**（迭代 #2 新增） | `_safe_float()` 拦截 NaN/None/Inf；`_safe_mean()` 拦截空列表/全 NaN | vectorbt 无交易时 stats 返回 NaN；`NaN or 0.0` 仍为 NaN（NaN 是 truthy）导致 JSON 序列化失败 |
 386→| **策略名校验**（迭代 #1 新增） | `_run_group` 进入策略循环前检查 `strategy not in STRATEGY_REGISTRY` → `logger.warning` + `continue` | 防止策略名拼写错误被静默跳过（迭代 #1 修复的 bug：`main.py` 误用 `"rsi"/"macd"/"bollinger"` 简称导致 3 个策略 6 天未跑） |
 387→| **DD 硬约束 + Fallback**（迭代 #3 新增） | top-K 选择时过滤 `portfolio_max_drawdown > 20%` 的候选；若全部超标 → 按 DD 升序取 top-K，标记 `dd_constrained=True` | Constitution L1 DD≤20% 是硬约束；无合规候选时仍需产出权重（结构性问题不能阻塞回测） |
 388→| **Alpha 排序 + Sortino 门槛**（迭代 #9 新增） | top-K 排序从 Sortino 改为 Alpha（策略年化收益 - SPY 同期年化收益）；新增 `Sortino > 0.5` 最低质量门槛 | Sortino 高 ≠ 年化高（均值回归策略天然高 Sortino 低绝对收益，alpha 为负）；Alpha 排序直接优化超额收益目标；Sortino 门槛保证基本下行质量。三级 fallback：Tier 1 DD+Sortino → Tier 2 仅 DD → Tier 3 DD 升序 |
 389→| **SPY Benchmark 获取**（迭代 #9 新增） | `_get_spy_returns(start, end)` 从 MarketDataStore 拉取 SPY 日收益率；`_compute_alpha(strat, spy)` 计算年化 alpha | SPY 不可用时 alpha 降级为 0.0（不阻塞回测），所有候选 alpha=0 ��退化为原顺序 |
 390→| **per-strategy best params 用 Alpha**（迭代 #9 新增） | 每个策略的最优参数选择从 Sharpe 改为 Alpha | 与 top-K 排序口径一致，避免 per-strategy 用 Sharpe 选低收益高稳定的参数 |
 391→| **ensemble weights 用 Alpha**（迭代 #9 新增） | `_optimize_ensemble_weights` 接收 `spy_returns` 参数，权重计算从 Sharpe 改为 Alpha | 与 top-K 排序口径一致，ensemble 权重直接反映"跑赢 SPY 的程度"；SPY 不可用时退化为等权 |
 392→| **参数按组** | 同组共用参数，不对单只优化 | 防过拟合（详见 02-strategy-engine.md 6.3） |
 393→| **历史分组对齐** | 矩阵回测使用 point-in-time 分组（按回测时间点重算波动率），而非当前静态分组 | 避免回测静态分组而实盘动态分组导致回测/实盘不一致 |
 394→| **实盘 ensemble 对齐** | MatrixBacktest 的 ensemble 权重优化须在"单点离散值聚合"语义下验证 | 实盘只取 iloc[-1] 单点离散值加权，与序列级加权不等价，权重必须在相同语义下产出 |
 395→| **Walk-Forward** | 滚动训练窗口，月度重优化 | 平衡过拟合与适应性 |
 396→
 397→### 10.4.1 Top-K 选择三级 Fallback（迭代 #9 新增）
 398→
 399→```
 400→
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md","new_string":"| **ensemble weights 用 Alpha**（迭代 #9 新增） | `_optimize_ensemble_weights` 接收 `spy_returns` 参数，权重计算从 Sharpe 改为 Alpha | 与 top-K 排序口径一致，ensemble 权重直接反映\"跑赢 SPY 的程度\"；SPY 不可用时退化为等权 |\n| **健全性门槛（Reject Degenerate）**（迭代 #11 新增） | `SingleBacktestResult.closed_trades` 字段 + `_is_degenerate_strategy()` 函数；`_run_group` 在 candidates 构建前剔除 `>= 80%` 标的 `closed_trades==0` 的退化策略；全退化组返回空权重 + `no_valid_strategy=True` 标记 | 退化策略（入场/出场条件互斥，如 Iter #8 `rsi_trend_filter`）仓位靠末尾强平凑出 Sortino/alpha 假象，会骗过 alpha 排序进入权重（Iter #10 实测 alpha=-25%）。`closed_trades` 区分\"真交易闭环\"与\"伪 buy-and-hold\"。0.8 阈值保守，只拦\"近乎全标的零平仓\"，不误伤低频合法策略。`experience.md #8`：sanity → risk → rank，排序前必须先过硬门槛 |\n| **参数按组** | 同组共用参数，不对单只优化 | 防过拟合（详见 02-strategy-engine.md 6.3） |","old_string":"| **ensemble weights 用 Alpha**（迭代 #9 新增） | `_optimize_ensemble_weights` 接收 `spy_returns` 参数，权重计算从 Sharpe 改为 Alpha | 与 top-K 排序口径一致，ensemble 权重直接反映\"跑赢 SPY 的程度\"；SPY 不可用时退化为等权 |\n| **参数按组** | 同组共用参数，不对单只优化 | 防过拟合（详见 02-strategy-engine.md 6.3） |","replace_all":false}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md
---
现在
---
更新
---
三级
---
回
---
退
---
（
---
Tier
---
 fallback
---
）
---
部分
---
，
---
以
---
提及
---
优先
---
应用
---
的新
---
合理性
---
过滤器
---
（
---
san
---
ity
---
 filter
---
）：
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md","new_string":"### 10.4.1 Top-K 选择三级 Fallback（迭代 #9 新增，迭代 #11 前置健全性门槛）\n\n```\n[迭代 #11 前置] 健全性过滤：剔除 closed_trades==0 比例 ≥ 80% 的退化策略\n                全退化组 → 空权重 + no_valid_strategy=True（hold cash）\n                    ↓\nTier 1: DD ≤ 20% AND Sortino > 0.5  →  Alpha 降序取 top-K\n   ↓ (若空)\nTier 2: DD ≤ 20%（放宽 Sortino）   →  Alpha 降序取 top-K，WARNING 日志\n   ↓ (若空)\nTier 3: 无 DD 合规候选              →  DD 升序取 top-K，dd_constrained=True\n```\n\n**迭代 #11 健全性门槛（先于 Tier 1-3）**：\n- `SingleBacktestResult.closed_trades` 字段从 vbt `pf.trades.closed.count()` 提取（区分\"真交易闭环\"与\"末尾强平计 1 笔的伪 buy-and-hold\"）\n- 退化定义：组内 `closed_trades==0` 的标的比例 ≥ `DEGENERATE_NO_CLOSE_FRACTION (0.8)`\n- 全退化组返回空权重（持仓现金），不强行选退化策略；标记 `GroupBacktestResult.no_valid_strategy=True`\n- 设计动机（`experience.md #8`）：Iter #10 `rsi_trend_filter` 凭\"持仓盯市 + 末尾强平\"的 Sortino/alpha 假象骗过 alpha 排序进入 4/6 组权重 → 组合 alpha=-25.26%。`closed_trades` 信号缺失时无健全性门槛可拦住整个灾难。0.8 阈值保守，低频合法策略（每标的 2-3 笔）不会被误伤","old_string":"### 10.4.1 Top-K 选择三级 Fallback（迭代 #9 新增）\n\n```\nTier 1: DD ≤ 20% AND Sortino > 0.5  →  Alpha 降序取 top-K\n   ↓ (若空)\nTier 2: DD ≤ 20%（放宽 Sortino）   →  Alpha 降序取 top-K，WARNING 日志\n   ↓ (若空)\nTier 3: 无 DD 合规候选              →  DD 升序取 top-K，dd_constrained=True\n```","replace_all":false}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md
---
###
---
 
---
步
---
骤
---
 
---
8
---
：
---
更新
---
 iteration
---
_trajectory
---
.md
---
{"command":"tail -5 /Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md","description":"Check end of trajectory file"}
---
Check end of trajectory file
---
Command: tail -5 /Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md
Stdout: > - 高风险文件: 0 个
> - 测试数变化: 602 → 626
> - CodeBuddy 自行更新了 trajectory ✅

---

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"file_path":"/Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md","limit":5,"offset":1}
---
   1→
   2→## 迭代 #0 — 读取 mytrader/backtest/runner.py 的代码并用一句话总结它的功能
   3→
   4→- **日期**: 2026-06-30 05:46 UTC
   5→- **类型**: 自动化迭代 (Orchestrator → CodeBuddy)
   6→
---
   1→
   2→## 迭代 #0 — 读取 mytrader/backtest/runner.py 的代码并用一句话总结它的功能
   3→
   4→- **日期**: 2026-06-30 05:46 UTC
   5→- **类型**: 自动化迭代 (Orchestrator → CodeBuddy)
   6→
---
{"file_path":"/Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md","new_string":"> - 高风险文件: 0 个\n> - 测试数变化: 602 → 626\n> - CodeBuddy 自行更新了 trajectory ✅\n\n---\n\n## 迭代 #11 — 选择器健全性门槛（Reject Degenerate Strategies）\n\n- **日期**: 2026-07-07 UTC\n- **类型**: 选择器治理漏洞修复（低风险，仅改 `matrix_backtest.py`）\n- **变更摘要**: 给 `SingleBacktestResult` 新增 `closed_trades` 字段（vbt 已平仓交易数），在 `_run_group` 排序前加健全性门槛剔除退化策略（≥ 80% 标的零平仓 = 入场/出场条件互斥的伪 buy-and-hold）；全退化组返回空权重 + `no_valid_strategy` 标记（持仓现金，不强行选退化策略）\n- **状态**: passed\n- **执行时长**: 1 轮对话（手动开发）\n- **测试数**: 626 → 646（+20 新测试用例）\n\n### 背景\n\nIter #10 的 `--reoptimize`（Alpha 排序）产出灾难性结果：年化 -4.88%，Sortino -0.66，Alpha -25.26%。三方审计 + 本机实测（`tmp/audit_verify.py`）钉死根因 —— `rsi_trend_filter` 入场条件（close>SMA200，上升趋势）与出场条件（close<SMA200，下降趋势）在趋势方向上互斥，5 只股票产生 0 个出场信号，每只只开 1 仓挂到末尾强平，win_rate 全为 NaN。它的 Sortino/alpha 只是持仓盯市假象，不是真实交易能力。**选择器没有任何健全性门槛**让这个伪策略骗过 alpha 排序，进入 4/6 组权重。\n\n### 变更详情\n\n**P0: `SingleBacktestResult.closed_trades` 字段** (`matrix_backtest.py`)\n- 新增 `closed_trades: int = 0` 字段（vbt `pf.trades.closed.count()`，已平仓交易数）\n- 区分\"真交易闭环\"与\"末尾强平计 1 笔的伪 buy-and-hold\"\n- 在 `_backtest_one` 和 `_backtest_batch` 中填充；batch 与 single 数值一致（沿用 Iter #10 一致性范式）\n- vbt 1.0 实际 API 是 `pf.trades.closed.count()`（spec 中提到的 `status_closed` 在 1.0 不存在）\n\n**P0: `_is_degenerate_strategy()` 健全性判定函数** (`matrix_backtest.py`)\n- 退化定义：组内 `closed_trades==0` 的标的比例 ≥ `DEGENERATE_NO_CLOSE_FRACTION (0.8)`\n- 阈值取 0.8（保守）：只在\"近乎全部标的零平仓\"时触发，避免误伤低频合法策略\n- 空结果列表视为退化（True）\n\n**P0: `_run_group` 集成健全性过滤** (`matrix_backtest.py::_run_group`)\n- 在 candidates 构建**之前**插入过滤（`experience.md #8`：sanity → risk → rank）\n- 退化策略 WARNING 日志 + 不进入 candidates（其 `GroupBacktestResult` 存档条目保留供审计）\n- 全退化组：返回空 weights_list，`report.warnings` 追加 `no_valid_strategy` 标记，对应 `GroupBacktestResult.no_valid_strategy=True`\n- 后续 DD/Sortino/Alpha 三级过滤、Alpha 排序、ensemble 权重逻辑全部作用于\"通过健全性过滤后的存活候选\"，不变\n\n**P0: `GroupBacktestResult.no_valid_strategy` 字段** (`matrix_backtest.py`)\n- 新增 `no_valid_strategy: bool = False` 标记，标记该组是否因全退化而空仓\n- 与 `dd_constrained` 同义但更可读，下游消费方可读此字段判断该组权重的可靠性\n\n**测试** (`tests/test_degenerate_filter.py`, +20 用例)\n- `closed_trades` 字段存在性 + 默认值\n- 正常策略 `closed_trades > 0`；`rsi_trend_filter` 在强趋势上 `closed_trades=0`（退化）\n- batch vs single `closed_trades` 一致性（4 策略 × 多标的）\n- `_is_degenerate_strategy`：空列表、全零、正常、阈值边界（4/5=0.8 触发、3/5=0.6 不触发）、低频不被误伤、单零不牵连整组\n- `_run_group` 集成：退化策略剔除、全退化空仓 + 标记、正常策略不受影响\n- `GroupBacktestResult.no_valid_strategy` 默认 False\n- 同步更新 `test_batch_backtest.py::_assert_results_match` 加 `closed_trades` 一致性断言、`test_result_fields_populated` 加字段类型断言\n- 同步更新 `test_matrix_backtest.py` 中 4 处 mock `_backtest_batch` 的 `SingleBacktestResult` 构造，显式传 `closed_trades` 反映\"mock 假定策略闭环\"\n\n### 回测结果\n\n- 本轮不运行 `--reoptimize`（spec §6 验收阶段由 Meta-Agent 独立执行）\n- 单元/集成测试全部通过：646 passed, 0 failed, 16 deselected (live)\n- `closed_trades` 提取在真实数据上验证：`rsi_trend_filter` 5 标的 0 closed_trades → 退化；`rsi_mean_revert` 5 标的各 1-2 closed_trades → 不退化\n- batch vs single `closed_trades` 严格一致（4 策略 × 3 标的 × random walk 数据）\n\n### Constitution 合规\n\n- ✅ 未突破 DD 20% 约束（DD 过滤逻辑完全不变）\n- ✅ 测试覆盖率提升（+20 测试，626 → 646）\n- ✅ 未修改策略代码 / 指标代码 / risk / execution（spec §3 排除项遵守）\n- ✅ 未改 alpha 排序为 OOS（→ Iter #12）\n- ✅ 未加 `alpha>0` 硬门槛（→ Iter #12）\n- ✅ 未修 `rsi_trend_filter` 出场逻辑（健全性门槛会自动排除它；策略重设计是独立任务）\n- ✅ 决策可解释（健全性门槛先于排序，退化策略的 Sortino/alpha 假象被拦在 top-K 之前）\n- ✅ 未引入 RL / 未引入不安全依赖\n- ✅ 未触发真实交易\n- ✅ 文档与代码同步（07-backtest-module.md + CODEBUDDY.md + trajectory）\n\n### Experience Learned\n\n- **`closed_trades` 是更便宜的健全性信号**：比 OOS alpha / holdout 早一步、比 win_rate 非 NaN 更直接。`total_trades` 包含末尾强平的 open trade，无法区分\"真交易\"和\"买一次不动\"；`closed_trades` 直接反映\"完成买卖闭环\"的能力\n- **vbt 1.0 API 实测优先**：spec 提到的 `pf.trades.status_closed.count()` 在 vbt 1.0.0 不存在，实际 API 是 `pf.trades.closed.count()`（spec §4.2 已预见并要求实现者查证）。这印证了 `experience.md #1`：不要假设 API，先写最小验证脚本\n- **mock 测试需要同步更新**：当被测对象新增字段（`closed_trades`）且参与选择逻辑（健全性门槛），mock 出的 `SingleBacktestResult` 必须显式设置该字段，否则默认值（0）会触发误判。这是 mock 与实现耦合的代价\n- **0.8 阈值的边界设计**：4/5=0.8 触发（>=）、3/5=0.6 不触发。取 0.8 而非 0.5/0.6 是为了\"只在近乎全标的全死时才判退化\"，给低频合法策略留缓冲（spec §5.7 边界测试）\n- **健全性过滤先于 candidates 构建**：把退化策略拦在 DD/Sortino/Alpha 三级过滤之前，避免其\"漂亮\"的盯市假象污染任何后续指标。`experience.md #8` 顺序：sanity → risk → rank\n- **空仓是正确动作**：全退化组返回空权重（持仓现金）而非\"矬子里拔将军\"强行 top-K。`experience.md #8`：没有候选满足门槛时，正确动作是\"空仓/降现金/回退 benchmark\"\n\n### 后续建议\n\n1. **Meta-Agent 验收**（spec §6）：运行 `python main.py --reoptimize`，验证：\n   - `rsi_trend_filter` 不再出现在任何组权重中\n   - 各组权重 `backtest_win_rate` 不再是 ≈0 的退化值\n   - PortfolioBacktest 组合指标从 Iter #10 的 alpha=-25% 恢复到 ≈Iter #7 的可信基线（正收益、Sortino>0）\n2. **Iter #12 OOS alpha 排序 + alpha>0 硬门槛**（spec §3 排除项）：健全性门槛只解决\"退化策略骗过排序\"，不解决\"样本内 alpha 过拟合\"和\"全负 alpha 矬子里拔将军\"\n3. **修 `rsi_trend_filter` 出场逻辑**（独立任务）：出场改为均值回归自然出场（RSI 回中性 50）或去掉出场的趋势门槛；趋势过滤只作用于入场。健全性门槛会自动排除当前退化版本\n4. **WF gate 增加 alpha 校验**（`experience.md #8`）：当前 WF 只校验 DD/Sortino 不校验 alpha，Iter #10 WF 4/4 pass 但组合 alpha=-25.26%。需加：平均验证期 alpha>0、最近一轮 alpha>0、无单轮 alpha<-5%\n\n### L7 流水线状态\n```\n✅ Backtest (≥5年, alpha-based selection, batch-optimized, sanity-gated)\n✅ Walk-Forward (4轮, 自动继承 alpha 排序, batch-optimized)\n✅ Portfolio Backtest | ✅ Paper Trading Integrity\n✅ Harness Reliability | ✅ SignalRanker Sortino Priority\n✅ Strategy Diversity (5 策略 pool)\n✅ Alpha-Based Selection (迭代 #9 完成)\n✅ Batch Backtest Optimization (迭代 #10 完成)\n✅ Sanity Gate / Reject Degenerate (迭代 #11 完成)\n⬜ OOS Alpha Sort + alpha>0 Threshold (→ Iter #12)\n⬜ Paper Trade ≥1月 | ⬜ Live\n```\n\n---\n\n","old_string":"> - 高风险文件: 0 个\n> - 测试数变化: 602 → 626\n> - CodeBuddy 自行更新了 trajectory ✅\n\n---\n\n","replace_all":false}
---
Error: Edit error on /Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md: String to replace not found in file.
String: "> - 高风险文件: 0 个
> - 测试数变化: 602 → 626
> - CodeBuddy 自行更新了 trajectory ✅

---

"
---
Error: Edit error on /Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md: String to replace not found in file.
String: "> - 高风险文件: 0 个
> - 测试数变化: 602 → 626
> - CodeBuddy 自行更新了 trajectory ✅

---

"
---
{"command":"tail -10 /Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md | cat -A | head -20","description":"Check exact bytes of file ending"}
---
Check exact bytes of file ending
---
Command: tail -10 /Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md | cat -A | head -20
Stdout: cat: illegal option -- A
usage: cat [-belnstuv] [file ...]

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"command":"tail -10 /Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md | od -c | head -10","description":"Check exact bytes of file ending"}
---
Check exact bytes of file ending
---
Command: tail -10 /Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md | od -c | head -10
Stdout: 0000000   \n   >       *   *   O   r   c   h   e   s   t   r   a   t   o
0000020    r     351 252 214 350 257 201 350 256 260 345 275 225   *   *
0000040        ( 350 207 252 345 212 250 350 277 275 345 212 240   )  \n
0000060    >       -     350 277 255 344 273 243 347 212 266 346 200 201
0000100    :       p   a   s   s   e   d  \n   >       -     346 265 213
0000120  350 257 225   :       0       p   a   s   s   e   d   ,       0
0000140        f   a   i   l   e   d  \n   >       -     350 277 235 350
0000160  247 204   :       0     346 235 241  \n   >       -     351 253
0000200  230 351 243 216 351 231 251 346 226 207 344 273 266   :       0
0000220      344 270 252  \n   >       -     346 265 213 350 257 225 346

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"command":"tail -3 /Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md | od -c | tail -10","description":"Check last 3 lines bytes"}
---
Check last 3 lines bytes
---
Command: tail -3 /Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md | od -c | tail -10
Stdout: 0000000    >       -       C   o   d   e   B   u   d   d   y     350 207
0000020  252 350 241 214 346 233 264 346 226 260 344 272 206       t   r
0000040    a   j   e   c   t   o   r   y     342 234 205  \n  \n   -   -
0000060    -  \n                                                        
0000062

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
The
---
 file
---
 ends
---
 with
---
 `
---
trajectory
---
 
---
✅
---
\
---
n
---
\n
---
---
---
\
---
n
---
`
---
 followed
---
 by
---
 trailing
---
 whitespace
---
 (
---
no
---
 final
---
 newline
---
).
---
 Let
---
 me
---
 append
---
 the
---
 iteration
---
 #
---
11
---
 entry
---
 to
---
 the
---
 file
---
.
---
 Since
---
 the
---
 ending
---
 is
---
 unique
---
,
---
 I
---
'll
---
 read
---
 it
---
 and
---
 use
---
 a
---
 different
---
 approach
---
 —
---
 append
---
 by
---
 reading
---
 first
---
 then
---
 writing
---
.
---
{"command":"wc -l /Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md","description":"Check line count"}
---
Check line count
---
Command: wc -l /Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md
Stdout:     1140 /Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"file_path":"/Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md","limit":8,"offset":1133}
---
1133→> - 迭代状态: passed
1134→> - 测试: 0 passed, 0 failed
1135→> - 违规: 0 条
1136→> - 高风险文件: 0 个
1137→> - 测试数变化: 602 → 626
1138→> - CodeBuddy 自行更新了 trajectory ✅
1139→
1140→---
1141→
---
1133→> - 迭代状态: passed
1134→> - 测试: 0 passed, 0 failed
1135→> - 违规: 0 条
1136→> - 高风险文件: 0 个
1137→> - 测试数变化: 602 → 626
1138→> - CodeBuddy 自行更新了 trajectory ✅
1139→
1140→---
1141→
---
{"file_path":"/Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md","new_string":"> - 测试数变化: 602 → 626\n> - CodeBuddy 自行更新了 trajectory ✅\n\n---\n\n## 迭代 #11 — 选择器健全性门槛（Reject Degenerate Strategies）\n\n- **日期**: 2026-07-07 UTC\n- **类型**: 选择器治理漏洞修复（低风险，仅改 `matrix_backtest.py`）\n- **变更摘要**: 给 `SingleBacktestResult` 新增 `closed_trades` 字段（vbt 已平仓交易数），在 `_run_group` 排序前加健全性门槛剔除退化策略（≥ 80% 标的零平仓 = 入场/出场条件互斥的伪 buy-and-hold）；全退化组返回空权重 + `no_valid_strategy` 标记（持仓现金，不强行选退化策略）\n- **状态**: passed\n- **执行时长**: 1 轮对话（手动开发）\n- **测试数**: 626 → 646（+20 新测试用例）\n\n### 背景\n\nIter #10 的 `--reoptimize`（Alpha 排序）产出灾难性结果：年化 -4.88%，Sortino -0.66，Alpha -25.26%。三方审计 + 本机实测（`tmp/audit_verify.py`）钉死根因 —— `rsi_trend_filter` 入场条件（close>SMA200，上升趋势）与出场条件（close<SMA200，下降趋势）在趋势方向上互斥，5 只股票产生 0 个出场信号，每只只开 1 仓挂到末尾强平，win_rate 全为 NaN。它的 Sortino/alpha 只是持仓盯市假象，不是真实交易能力。**选择器没有任何健全性门槛**让这个伪策略骗过 alpha 排序，进入 4/6 组权重。\n\n### 变更详情\n\n**P0: `SingleBacktestResult.closed_trades` 字段** (`matrix_backtest.py`)\n- 新增 `closed_trades: int = 0` 字段（vbt `pf.trades.closed.count()`，已平仓交易数）\n- 区分\"真交易闭环\"与\"末尾强平计 1 笔的伪 buy-and-hold\"\n- 在 `_backtest_one` 和 `_backtest_batch` 中填充；batch 与 single 数值一致（沿用 Iter #10 一致性范式）\n- vbt 1.0 实际 API 是 `pf.trades.closed.count()`（spec 中提到的 `status_closed` 在 1.0 不存在）\n\n**P0: `_is_degenerate_strategy()` 健全性判定函数** (`matrix_backtest.py`)\n- 退化定义：组内 `closed_trades==0` 的标的比例 ≥ `DEGENERATE_NO_CLOSE_FRACTION (0.8)`\n- 阈值取 0.8（保守）：只在\"近乎全部标的零平仓\"时触发，避免误伤低频合法策略\n- 空结果列表视为退化（True）\n\n**P0: `_run_group` 集成健全性过滤** (`matrix_backtest.py::_run_group`)\n- 在 candidates 构建**之前**插入过滤（`experience.md #8`：sanity → risk → rank）\n- 退化策略 WARNING 日志 + 不进入 candidates（其 `GroupBacktestResult` 存档条目保留供审计）\n- 全退化组：返回空 weights_list，`report.warnings` 追加 `no_valid_strategy` 标记，对应 `GroupBacktestResult.no_valid_strategy=True`\n- 后续 DD/Sortino/Alpha 三级过滤、Alpha 排序、ensemble 权重逻辑全部作用于\"通过健全性过滤后的存活候选\"，不变\n\n**P0: `GroupBacktestResult.no_valid_strategy` 字段** (`matrix_backtest.py`)\n- 新增 `no_valid_strategy: bool = False` 标记，标记该组是否因全退化而空仓\n- 与 `dd_constrained` 同义但更可读，下游消费方可读此字段判断该组权重的可靠性\n\n**测试** (`tests/test_degenerate_filter.py`, +20 用例)\n- `closed_trades` 字段存在性 + 默认值\n- 正常策略 `closed_trades > 0`；`rsi_trend_filter` 在强趋势上 `closed_trades=0`（退化）\n- batch vs single `closed_trades` 一致性（4 策略 × 多标的）\n- `_is_degenerate_strategy`：空列表、全零、正常、阈值边界（4/5=0.8 触发、3/5=0.6 不触发）、低频不被误伤、单零不牵连整组\n- `_run_group` 集成：退化策略剔除、全退化空仓 + 标记、正常策略不受影响\n- `GroupBacktestResult.no_valid_strategy` 默认 False\n- 同步更新 `test_batch_backtest.py::_assert_results_match` 加 `closed_trades` 一致性断言、`test_result_fields_populated` 加字段类型断言\n- 同步更新 `test_matrix_backtest.py` 中 4 处 mock `_backtest_batch` 的 `SingleBacktestResult` 构造，显式传 `closed_trades` 反映\"mock 假定策略闭环\"\n\n### 回测结果\n\n- 本轮不运行 `--reoptimize`（spec §6 验收阶段由 Meta-Agent 独立执行）\n- 单元/集成测试全部通过：646 passed, 0 failed, 16 deselected (live)\n- `closed_trades` 提取在真实数据上验证：`rsi_trend_filter` 5 标的 0 closed_trades → 退化；`rsi_mean_revert` 5 标的各 1-2 closed_trades → 不退化\n- batch vs single `closed_trades` 严格一致（4 策略 × 3 标的 × random walk 数据）\n\n### Constitution 合规\n\n- ✅ 未突破 DD 20% 约束（DD 过滤逻辑完全不变）\n- ✅ 测试覆盖率提升（+20 测试，626 → 646）\n- ✅ 未修改策略代码 / 指标代码 / risk / execution（spec §3 排除项遵守）\n- ✅ 未改 alpha 排序为 OOS（→ Iter #12）\n- ✅ 未加 `alpha>0` 硬门槛（→ Iter #12）\n- ✅ 未修 `rsi_trend_filter` 出场逻辑（健全性门槛会自动排除它；策略重设计是独立任务）\n- ✅ 决策可解释（健全性门槛先于排序，退化策略的 Sortino/alpha 假象被拦在 top-K 之前）\n- ✅ 未引入 RL / 未引入不安全依赖\n- ✅ 未触发真实交易\n- ✅ 文档与代码同步（07-backtest-module.md + CODEBUDDY.md + trajectory）\n\n### Experience Learned\n\n- **`closed_trades` 是更便宜的健全性信号**：比 OOS alpha / holdout 早一步、比 win_rate 非 NaN 更直接。`total_trades` 包含末尾强平的 open trade，无法区分\"真交易\"和\"买一次不动\"；`closed_trades` 直接反映\"完成买卖闭环\"的能力\n- **vbt 1.0 API 实测优先**：spec 提到的 `pf.trades.status_closed.count()` 在 vbt 1.0.0 不存在，实际 API 是 `pf.trades.closed.count()`（spec §4.2 已预见并要求实现者查证）。这印证了 `experience.md #1`：不要假设 API，先写最小验证脚本\n- **mock 测试需要同步更新**：当被测对象新增字段（`closed_trades`）且参与选择逻辑（健全性门槛），mock 出的 `SingleBacktestResult` 必须显式设置该字段，否则默认值（0）会触发误判。这是 mock 与实现耦合的代价\n- **0.8 阈值的边界设计**：4/5=0.8 触发（>=）、3/5=0.6 不触发。取 0.8 而非 0.5/0.6 是为了\"只在近乎全标的全死时才判退化\"，给低频合法策略留缓冲（spec §5.7 边界测试）\n- **健全性过滤先于 candidates 构建**：把退化策略拦在 DD/Sortino/Alpha 三级过滤之前，避免其\"漂亮\"的盯市假象污染任何后续指标。`experience.md #8` 顺序：sanity → risk → rank\n- **空仓是正确动作**：全退化组返回空权重（持仓现金）而非\"矬子里拔将军\"强行 top-K。`experience.md #8`：没有候选满足门槛时，正确动作是\"空仓/降现金/回退 benchmark\"\n\n### 后续建议\n\n1. **Meta-Agent 验收**（spec §6）：运行 `python main.py --reoptimize`，验证：\n   - `rsi_trend_filter` 不再出现在任何组权重中\n   - 各组权重 `backtest_win_rate` 不再是 ≈0 的退化值\n   - PortfolioBacktest 组合指标从 Iter #10 的 alpha=-25% 恢复到 ≈Iter #7 的可信基线（正收益、Sortino>0）\n2. **Iter #12 OOS alpha 排序 + alpha>0 硬门槛**（spec §3 排除项）：健全性门槛只解决\"退化策略骗过排序\"，不解决\"样本内 alpha 过拟合\"和\"全负 alpha 矬子里拔将军\"\n3. **修 `rsi_trend_filter` 出场逻辑**（独立任务）：出场改为均值回归自然出场（RSI 回中性 50）或去掉出场的趋势门槛；趋势过滤只作用于入场。健全性门槛会自动排除当前退化版本\n4. **WF gate 增加 alpha 校验**（`experience.md #8`）：当前 WF 只校验 DD/Sortino 不校验 alpha，Iter #10 WF 4/4 pass 但组合 alpha=-25.26%。需加：平均验证期 alpha>0、最近一轮 alpha>0、无单轮 alpha<-5%\n\n### L7 流水线状态\n```\n✅ Backtest (≥5年, alpha-based selection, batch-optimized, sanity-gated)\n✅ Walk-Forward (4轮, 自动继承 alpha 排序, batch-optimized)\n✅ Portfolio Backtest | ✅ Paper Trading Integrity\n✅ Harness Reliability | ✅ SignalRanker Sortino Priority\n✅ Strategy Diversity (5 策略 pool)\n✅ Alpha-Based Selection (迭代 #9 完成)\n✅ Batch Backtest Optimization (迭代 #10 完成)\n✅ Sanity Gate / Reject Degenerate (迭代 #11 完成)\n⬜ OOS Alpha Sort + alpha>0 Threshold (→ Iter #12)\n⬜ Paper Trade ≥1月 | ⬜ Live\n```\n\n---\n","old_string":"> - 测试数变化: 602 → 626\n> - CodeBuddy 自行更新了 trajectory ✅\n\n---\n","replace_all":false}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md
---
###
---
 第
---
 
---
9
---
 
---
步
---
：
---
更新
---
 decision
---
_log
---
.md
---
{"command":"tail -25 /Users/rickouyang/Github/trade-tools/alignment/decision_log.md","description":"Check decision_log format"}
---
Check decision_log format
---
Command: tail -25 /Users/rickouyang/Github/trade-tools/alignment/decision_log.md
Stdout: ---

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

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"command":"wc -l /Users/rickouyang/Github/trade-tools/alignment/decision_log.md","description":"Check decision_log line count"}
---
Check decision_log line count
---
Command: wc -l /Users/rickouyang/Github/trade-tools/alignment/decision_log.md
Stdout:      387 /Users/rickouyang/Github/trade-tools/alignment/decision_log.md

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"file_path":"/Users/rickouyang/Github/trade-tools/alignment/decision_log.md","limit":5,"offset":383}
---
 383→  - `_backtest_one` 的直接测试全部保留
 384→
 385→- **经验教训**: mock 是实现耦合的，当被测函数的内部依赖改变时，mock 需要同步更新。未来应优先用真实数据测试（如 `test_batch_backtest.py` 的数值一致性测试），减少 mock 依赖。
 386→
 387→---
 388→
---
 383→  - `_backtest_one` 的直接测试全部保留
 384→
 385→- **经验教训**: mock 是实现耦合的，当被测函数的内部依赖改变时，mock 需要同步更新。未来应优先用真实数据测试（如 `test_batch_backtest.py` 的数值一致性测试），减少 mock 依赖。
 386→
 387→---
 388→
---
{"file_path":"/Users/rickouyang/Github/trade-tools/alignment/decision_log.md","new_string":"- **经验教训**: mock 是实现耦合的，当被测函数的内部依赖改变时，mock 需要同步更新。未来应优先用真实数据测试（如 `test_batch_backtest.py` 的数值一致性测试），减少 mock 依赖。\n\n---\n\n### [2026-07-07 UTC] 迭代 #11 — 三处模糊决策（vbt API、阈值取值、mock 同步）\n\n- **困境描述**: 实现健全性门槛时遇到三处需要判断的决策点：\n  1. spec §4.2 提到的 vbt API `pf.trades.status_closed.count()` 在 vbt 1.0.0 不存在\n  2. `DEGENERATE_NO_CLOSE_FRACTION` 阈值取 0.8 还是更低/更高\n  3. 现有 mock-based 测试（`test_top_k_selection_uses_alpha` 等 4 处）的 `SingleBacktestResult` 构造默认 `closed_trades=0`，会触发新的健全性门槛误判\n\n- **涉及 AI Constitution 条款**:\n  - L1: KPI 可解释 — 健全性门槛是 KPI 之前的硬门槛\n  - L7: 测试纪律 — 新增字段不应破坏现有测试\n  - L9: 进化 — 门槛设计要考虑可调性（回滚/调整成本）\n\n- **决策逻辑**:\n\n  **决策 1: vbt API 用 `pf.trades.closed.count()`**\n  - spec §4.2 已预见并要求实现者查证 vbt 1.0.0 实际 API\n  - 用最小验证脚本确认：单标的 `pf.trades.closed.count()` 返回 int（已平仓交易数）；多标的 `pf[sym].trades.closed.count()` 返回 per-symbol int\n  - 提取失败降级为 0（不抛异常），与 `_safe_float` 同保守语义\n  - **不**用 `pf.trades.records_readable['Status'].value_counts()['Closed']`（DataFrame 路径，慢且类型不稳）\n\n  **决策 2: 阈值取 0.8（保守）**\n  - 0.8 = \"近乎全部标的零平仓\"才触发，给低频合法策略（如 monthly rebalance 每标的 2-3 笔）留缓冲\n  - 边界：4/5=0.8 触发（>=）、3/5=0.6 不触发。spec §5.7 要求边界测试覆盖\n  - 0.5/0.6 太激进：单只标的数据不足（刚上市）就可能牵连整组判定\n  - 0.9/1.0 太宽松：5 标的里 1 笔 closed_trades 就能蒙混过关，拦不住 rsi_trend_filter 这种\"少数熊市标的偶尔触发出场\"的情形\n  - 0.8 是经验值，可调（`DEGENERATE_NO_CLOSE_FRACTION` 常量），未来若发现误伤合法策略可上调\n\n  **决策 3: 同步更新 mock 测试，显式传 `closed_trades`**\n  - mock 的 `SingleBacktestResult(sym, strat, params, sharpe, ret, dd, win, trades, returns)` 默认 `closed_trades=0` → 触发健全性门槛 → 测试失败\n  - 选项 A：改健全性门槛只对\"多标的\"生效（>=2）—— 这是 hack，破坏门槛语义\n  - 选项 B：在 mock 中显式传 `closed_trades=<total_trades>` —— 反映\"mock 假定策略闭环\"的语义，正确\n  - 选 B：4 处 mock 各加 `closed_trades=` kwarg，与 `total_trades` 同值\n  - 同步更新 `test_batch_backtest.py::_assert_results_match` 加 `closed_trades` 一致性断言\n\n- **决策结果**:\n  - vbt API 用 `pf.trades.closed.count()`，单/多标的一致\n  - `DEGENERATE_NO_CLOSE_FRACTION = 0.8`，注释说明阈值设计动机\n  - 4 处 mock 测试显式传 `closed_trades`，`_assert_results_match` 加一致性断言\n  - 全部 646 测试通过\n\n- **经验教训**:\n  - **spec 预见 API 差异是规范做法**：spec §4.2 明确写了\"若 vbt API 名称不同，实现者需查 vbt 1.0.0 实际 API\"，省去了与 spec 作者反复确认的成本\n  - **保守阈值 + 边界测试**：取 0.8 而非 0.5/1.0，并在测试中覆盖 4/5=0.8 触发、3/5=0.6 不触发两个边界。阈值是可调常量，未来调整无需改逻辑\n  - **mock 与实现耦合的代价再次验证**：Iter #10 的 decision_log 已记录此教训，Iter #11 再次遇到（新增字段 → mock 默认值触发新逻辑）。强化了\"优先用真实数据测试\"的原则\n\n---\n","old_string":"- **经验教训**: mock 是实现耦合的，当被测函数的内部依赖改变时，mock 需要同步更新。未来应优先用真实数据测试（如 `test_batch_backtest.py` 的数值一致性测试），减少 mock 依赖。\n\n---","replace_all":false}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/alignment/decision_log.md
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/alignment/decision_log.md
---
###
---
 第
---
 
---
10
---
 
---
步
---
：
---
更新
---
 CODE
---
BU
---
DD
---
Y
---
.md
---
{"command":"grep -n \"Iter #9\\|迭代 #9\\|Iter #10\\|迭代 #10\\|602 passed\\|626 passed\\|Iter #11\" /Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md | head -20","description":"Find Iter references in CODEBUDDY.md"}
---
Find Iter references in CODEBUDDY.md
---
Command: grep -n "Iter #9\|迭代 #9\|Iter #10\|迭代 #10\|602 passed\|626 passed\|Iter #11" /Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md | head -20
Stdout: 3:> 最后更新：2026-07-05 (Iter #9: MatrixBacktest Alpha-Based Strategy Selection)  
128:    │   ├── matrix_backtest.py  # [Phase 5] MatrixBacktest（含 backtest_dd_status 风险 metadata + [Iter #9] backtest_alpha / alpha-based selection）
198:| **Iter #9** | ✅ 完成 | 17 | MatrixBacktest Alpha-Based Strategy Selection（SPY benchmark + alpha 计算 + top-K/per-strategy/ensemble 从 Sortino/Sharpe 改为 Alpha + Sortino > 0.5 门槛 + 三级 fallback） |
201:**当前总测试数：602 passed，0 failed**（live 测试默认隔离，迭代 #9 后；harness 测试 38 个在 `alignment/tests/`）

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
The
---
 CODE
---
BU
---
DD
---
Y
---
.md
---
 is
---
 at
---
 the
---
 parent
---
 level
---
 `/
---
Users
---
/r
---
ick
---
ou
---
yang
---
/G
---
ithub
---
/tr
---
ade
---
-tools
---
/.
---
code
---
b
---
uddy
---
/C
---
ODE
---
BU
---
DD
---
Y
---
.md
---
`.
---
 Let
---
 me
---
 update
---
:

---
1
---
.
---
 Line
---
 
---
3
---
:
---
 `
---
最后
---
更新
---
`
---
 to
---
 Iter
---
 #
---
11
---


---
2
---
.
---
 Line
---
 
---
128
---
:
---
 matrix
---
_back
---
test
---
.py
---
 description
---
 add
---
 Iter
---
 #
---
11
---


---
3
---
.
---
 Add
---
 Iter
---
 #
---
10
---
 and
---
 Iter
---
 #
---
11
---
 rows
---
 to
---
 the
---
 phase
---
 table
---
 (
---
Iter
---
 #
---
10
---
 not
---
 even
---
 listed
---
 yet
---
!)

---
4
---
.
---
 Line
---
 
---
201
---
:
---
 Update
---
 test
---
 count
---
 from
---
 
---
60
---
2
---
 to
---
 
---
6
---
46
---
{"file_path":"/Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md","limit":10,"offset":195}
---
 195→| **Iter #6** | ✅ 完成 | 38 | Harness Reliability & Live Test Isolation（live 隔离 + 假 passed 修复 + count_tests 修复 + untracked 快照 + gate_status.json） |
 196→| **Iter #7** | ✅ 完成 | 12 | SignalRanker Sortino Priority + Benchmark Comparison（sharpe→sortino 评分切换 + PortfolioBacktest SPY benchmark alpha/IR） |
 197→| **Iter #8** | ✅ 完成 | 11 | RSI Trend-Filtered Mean Reversion 策略（RSI 超卖/超买 + 200日SMA趋势过滤，5新测试） |
 198→| **Iter #9** | ✅ 完成 | 17 | MatrixBacktest Alpha-Based Strategy Selection（SPY benchmark + alpha 计算 + top-K/per-strategy/ensemble 从 Sortino/Sharpe 改为 Alpha + Sortino > 0.5 门槛 + 三级 fallback） |
 199→| **Phase 6** | 🔲 待开发 | — | AlpacaBroker auto 端到端验证 + 对账真实集成 + 港股支持 |
 200→
 201→**当前总测试数：602 passed，0 failed**（live 测试默认隔离，迭代 #9 后；harness 测试 38 个在 `alignment/tests/`）
 202→
 203→> 各阶段详细实现见 **[dev_records.md](.codebuddy/notes/dev_records.md)**
 204→
 205→
---
 195→| **Iter #6** | ✅ 完成 | 38 | Harness Reliability & Live Test Isolation（live 隔离 + 假 passed 修复 + count_tests 修复 + untracked 快照 + gate_status.json） |
 196→| **Iter #7** | ✅ 完成 | 12 | SignalRanker Sortino Priority + Benchmark Comparison（sharpe→sortino 评分切换 + PortfolioBacktest SPY benchmark alpha/IR） |
 197→| **Iter #8** | ✅ 完成 | 11 | RSI Trend-Filtered Mean Reversion 策略（RSI 超卖/超买 + 200日SMA趋势过滤，5新测试） |
 198→| **Iter #9** | ✅ 完成 | 17 | MatrixBacktest Alpha-Based Strategy Selection（SPY benchmark + alpha 计算 + top-K/per-strategy/ensemble 从 Sortino/Sharpe 改为 Alpha + Sortino > 0.5 门槛 + 三级 fallback） |
 199→| **Phase 6** | 🔲 待开发 | — | AlpacaBroker auto 端到端验证 + 对账真实集成 + 港股支持 |
 200→
 201→**当前总测试数：602 passed，0 failed**（live 测试默认隔离，迭代 #9 后；harness 测试 38 个在 `alignment/tests/`）
 202→
 203→> 各阶段详细实现见 **[dev_records.md](.codebuddy/notes/dev_records.md)**
 204→
 205→
---
I
---
 see
---
 that
---
 the
---
 CODE
---
BU
---
DD
---
Y
---
.md
---
 is
---
 missing
---
 the
---
 Iter
---
 #
---
10
---
 row
---
 (
---
it
---
 was
---
 probably
---
 added
---
 in
---
 Iter
---
 #
---
10
---
 but
---
 only
---
 the
---
 test
---
 count
---
 wasn
---
't
---
 updated
---
).
---
 Let
---
 me
---
 add
---
 both
---
 Iter
---
 #
---
10
---
 and
---
 Iter
---
 #
---
11
---
 entries
---
 and
---
 update
---
 the
---
 test
---
 count
---
.
---
{"file_path":"/Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md","new_string":"> 最后更新：2026-07-07 (Iter #11: Sanity Gate / Reject Degenerate Strategies)  ","old_string":"> 最后更新：2026-07-05 (Iter #9: MatrixBacktest Alpha-Based Strategy Selection)  ","replace_all":false}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md
---
{"file_path":"/Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md","new_string":"    │   ├── matrix_backtest.py  # [Phase 5] MatrixBacktest（含 backtest_dd_status 风险 metadata + [Iter #9] backtest_alpha / alpha-based selection + [Iter #11] closed_trades / sanity gate / no_valid_strategy）","old_string":"    │   ├── matrix_backtest.py  # [Phase 5] MatrixBacktest（含 backtest_dd_status 风险 metadata + [Iter #9] backtest_alpha / alpha-based selection）","replace_all":false}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md
---
{"file_path":"/Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md","new_string":"| **Iter #9** | ✅ 完成 | 17 | MatrixBacktest Alpha-Based Strategy Selection（SPY benchmark + alpha 计算 + top-K/per-strategy/ensemble 从 Sortino/Sharpe 改为 Alpha + Sortino > 0.5 门槛 + 三级 fallback） |\n| **Iter #10** | ✅ 完成 | 24 | vectorbt Batch Backtest Optimization（`_backtest_batch` 一次 vbt 调用处理组内所有标的 + batch vs single 数值一致性测试） |\n| **Iter #11** | ✅ 完成 | 20 | Sanity Gate / Reject Degenerate Strategies（`SingleBacktestResult.closed_trades` 字段 + `_is_degenerate_strategy` + `_run_group` 排序前剔除退化策略 + 全退化组空仓 `no_valid_strategy` 标记） |\n| **Phase 6** | 🔲 待开发 | — | AlpacaBroker auto 端到端验证 + 对账真实集成 + 港股支持 |\n\n**当前总测试数：646 passed，0 failed**（live 测试默认隔离，迭代 #11 后；harness 测试 38 个在 `alignment/tests/`）","old_string":"| **Iter #9** | ✅ 完成 | 17 | MatrixBacktest Alpha-Based Strategy Selection（SPY benchmark + alpha 计算 + top-K/per-strategy/ensemble 从 Sortino/Sharpe 改为 Alpha + Sortino > 0.5 门槛 + 三级 fallback） |\n| **Phase 6** | 🔲 待开发 | — | AlpacaBroker auto 端到端验证 + 对账真实集成 + 港股支持 |\n\n**当前总测试数：602 passed，0 failed**（live 测试默认隔离，迭代 #9 后；harness 测试 38 个在 `alignment/tests/`）","replace_all":false}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md
---
现在
---
让我
---
核实
---
一下
---
所有
---
文件
---
是否
---
整洁
---
，
---
并
---
最后一次
---
运行
---
完整的
---
测试
---
套
---
件
---
：
---
{"command":"PYTHONPATH=. /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest 2>&1 | tail -3","description":"Final full pytest run"}
---
Final full pytest run
---
Command: PYTHONPATH=. /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest 2>&1 | tail -3
Stdout: 
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
646 passed, 16 deselected, 103 warnings in 22.27s

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"status":"completed","taskId":"5"}
---
Updated task #5 status
---
Updated task #5 status
---
让我
---
进行
---
最后一次
---
核查
---
，
---
确保
---
所有
---
迭代
---
 #
---
11
---
 的
---
交付
---
成果
---
都已
---
到位
---
：
---
{"command":"echo \"=== 1. closed_trades field in SingleBacktestResult ===\" && grep -n \"closed_trades\" /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py | head -10\necho \"\"\necho \"=== 2. no_valid_strategy in GroupBacktestResult ===\" && grep -n \"no_valid_strategy\" /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py | head -10\necho \"\"\necho \"=== 3. DEGENERATE_NO_CLOSE_FRACTION constant ===\" && grep -n \"DEGENERATE_NO_CLOSE_FRACTION\" /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py | head -5\necho \"\"\necho \"=== 4. Sanity filter integration in _run_group ===\" && grep -n \"sane_results\\|健全性过滤\\|DEGENERATE\\|no_valid_strategy\" /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py | head -10","description":"Verify all code changes in place"}
---
Verify all code changes in place
---
Command: echo "=== 1. closed_trades field in SingleBacktestResult ===" && grep -n "closed_trades" /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py | head -10
echo ""
echo "=== 2. no_valid_strategy in GroupBacktestResult ===" && grep -n "no_valid_strategy" /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py | head -10
echo ""
echo "=== 3. DEGENERATE_NO_CLOSE_FRACTION constant ===" && grep -n "DEGENERATE_NO_CLOSE_FRACTION" /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py | head -5
echo ""
echo "=== 4. Sanity filter integration in _run_group ===" && grep -n "sane_results\|健全性过滤\|DEGENERATE\|no_valid_strategy" /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py | head -10
Stdout: === 1. closed_trades field in SingleBacktestResult ===
76:    closed_trades: int = 0     # 迭代 #11 新增：已平仓交易数（区分退化 buy-and-hold）
275:    退化定义：有效标的中 closed_trades==0 的比例 >= DEGENERATE_NO_CLOSE_FRACTION。
289:    no_close = sum(1 for r in results if r.closed_trades <= 0)
411:            closed_trades = int(pf.trades.closed.count())
413:            closed_trades = 0
426:            closed_trades=closed_trades,
571:                closed_trades = int(pf_sym.trades.closed.count())
573:                closed_trades = 0
585:                closed_trades=closed_trades,
1187:        # 退化策略 = 组内 ≥ 80% 标的 closed_trades==0（入场/出场条件互斥，

=== 2. no_valid_strategy in GroupBacktestResult ===
95:    no_valid_strategy: bool = False         # 迭代 #11：该组是否因全退化而空仓（hold cash）
1202:            # 全组退化 → 空权重（持仓现金），标记 no_valid_strategy，不强行选退化策略
1205:                f"group produces EMPTY weights (hold cash). Marked no_valid_strategy."
1208:                f"{group_id}: no_valid_strategy (all strategies degenerate)"
1213:                    gr.no_valid_strategy = True

=== 3. DEGENERATE_NO_CLOSE_FRACTION constant ===
55:DEGENERATE_NO_CLOSE_FRACTION: float = 0.8
275:    退化定义：有效标的中 closed_trades==0 的比例 >= DEGENERATE_NO_CLOSE_FRACTION。
290:    return (no_close / n) >= DEGENERATE_NO_CLOSE_FRACTION
1195:                    f"(>= {DEGENERATE_NO_CLOSE_FRACTION:.0%} symbols have 0 closed trades) "

=== 4. Sanity filter integration in _run_group ===
55:DEGENERATE_NO_CLOSE_FRACTION: float = 0.8
95:    no_valid_strategy: bool = False         # 迭代 #11：该组是否因全退化而空仓（hold cash）
275:    退化定义：有效标的中 closed_trades==0 的比例 >= DEGENERATE_NO_CLOSE_FRACTION。
290:    return (no_close / n) >= DEGENERATE_NO_CLOSE_FRACTION
1185:        # 迭代 #11：健全性过滤 —— 排序前先剔除退化策略
1190:        sane_results: list[tuple[str, dict, list[SingleBacktestResult]]] = []
1194:                    f"[MatrixBacktest] {group_id}: strategy '{strategy}' is DEGENERATE "
1195:                    f"(>= {DEGENERATE_NO_CLOSE_FRACTION:.0%} symbols have 0 closed trades) "
1199:            sane_results.append((strategy, params, results))
1201:        if not sane_results:

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
所有
---
交付
---
成果
---
已
---
就
---
绪
---
。
---
让我
---
核对
---
一下
---
规范
---
中的
---
成功
---
标准
---
作为
---
最终
---
检查
---
：


---
**
---
规范
---
成功
---
标准
---
验证
---
：
---
**


---
1
---
.
---
 
---
✅
---
 `
---
Single
---
Back
---
test
---
Result
---
.closed
---
_tr
---
ades
---
`
---
 字
---
段
---
存在
---
，
---
并由
---
 `_
---
back
---
test
---
_one
---
`
---
/
---
`
---
_
---
back
---
test
---
_batch
---
`
---
 
---
填
---
充
---


---
2
---
.
---
 
---
✅
---
 `_
---
is
---
_de
---
generate
---
_strategy
---
`
---
 正
---
确
---
识别
---
出
---
“
---
近乎
---
全
---
标的
---
零
---
平
---
仓
---
”
---
的
---
退化
---
策略
---


---
3
---
.
---
 
---
✅
---
 `_
---
run
---
_group
---
`
---
 在
---
排序
---
前
---
剔除
---
退化
---
策略
---
；
---
全
---
退化
---
组
---
返回
---
空
---
权重
---
 +
---
 `
---
no
---
_valid
---
_strategy
---
`
---
 
---
标
---
记
---


---
4
---
.
---
 
---
✅
---
 
---
退化
---
策略
---
（
---
如
---
 `
---
rs
---
i
---
_t
---
rend
---
_filter
---
`
---
）
---
将
---
不再
---
进入
---
 `
---
strategy
---
_weights
---
.json
---
`
---
（
---
已
---
通过
---
真实
---
数据
---
验证
---
：
---
5
---
 个
---
标的
---
，
---
0
---
 个
---
已
---
平
---
仓
---
交易
---
 →
---
 
---
退化
---
）

---
5
---
.
---
 
---
✅
---
 
---
默认
---
 pytest
---
 通过
---
：
---
**
---
6
---
46
---
 passed
---
,
---
 
---
0
---
 failed
---
**
---
（
---
6
---
26
---
 →
---
 
---
6
---
46
---
 =
---
 +
---
20
---
 个
---
新
---
测试
---
）

---
6
---
.
---
 
---
✅
---
 
---
批
---
量
---
与
---
单
---
标的
---
 `
---
closed
---
_tr
---
ades
---
`
---
 数
---
值
---
一致
---
（
---
已
---
通过
---
 `
---
test
---
_closed
---
_tr
---
ades
---
_batch
---
_matches
---
_single
---
`
---
 和
---
 `_
---
assert
---
_results
---
_match
---
`
---
 
---
扩
---
展
---
验证
---
）

---
7
---
.
---
 
---
✅
---
 
---
严格
---
遵守
---
规范
---
范围
---
：
---
未
---
修改
---
 risk
---
/
---
execution
---
/
---
strategy
---
/
---
指标
---
代码
---
；
---
alpha
---
 
---
排
---
序
---
未
---
改为
---
 O
---
OS
---
；
---
未
---
添加
---
 alpha
---
>
---
0
---
 
---
硬
---
门槛
---
；
---
`
---
rs
---
i
---
_t
---
rend
---
_filter
---
`
---
 
---
代码
---
未
---
触动
---


---
8
---
.
---
 
---
✅
---
 更
---
新
---
了
---
 `
---
design
---
s
---
/design
---
_v
---
2
---
/
---
07
---
-back
---
test
---
-module
---
.md
---
`
---
、
---
iteration
---
_trajectory
---
、
---
decision
---
_log
---
 和
---
 CODE
---
BU
---
DD
---
Y
---



---
---


---
##
---
 总结
---



---
**
---
迭代
---
 #
---
11
---
 —
---
 选择
---
器
---
健全
---
性
---
门槛
---
（
---
Reject
---
 Deg
---
enerate
---
 Strategies
---
）
---
已完成
---
。
---
**


---
###
---
 
---
代码
---
变更
---
（
---
仅
---
 `
---
my
---
tr
---
ader
---
/back
---
test
---
/m
---
atrix
---
_back
---
test
---
.py
---
`
---
）

---
-
---
 `
---
Single
---
Back
---
test
---
Result
---
.closed
---
_tr
---
ades
---
:
---
 int
---
 =
---
 
---
0
---
`
---
 字
---
段
---
（
---
v
---
bt
---
 `
---
pf
---
.tr
---
ades
---
.closed
---
.count
---
()`
---
）

---
-
---
 `
---
Group
---
Back
---
test
---
Result
---
.no
---
_valid
---
_strategy
---
:
---
 bool
---
 =
---
 False
---
`
---
 
---
标
---
记
---
字段
---


---
-
---
 `
---
DE
---
GENER
---
ATE
---
_NO
---
_CLOSE
---
_F
---
RA
---
CTION
---
:
---
 float
---
 =
---
 
---
0
---
.
---
8
---
`
---
 
---
常
---
量
---


---
-
---
 `_
---
is
---
_de
---
generate
---
_strategy
---
(results
---
)`
---
 
---
函数
---
：
---
组
---
内
---
 `
---
closed
---
_tr
---
ades
---
==
---
0
---
`
---
 
---
比
---
例
---
 ≥
---
 
---
0
---
.
---
8
---
 →
---
 
---
退化
---


---
-
---
 `_
---
run
---
_group
---
`
---
 在
---
 candidates
---
 
---
构
---
建
---
前
---
加
---
健全
---
性
---
过滤
---
；
---
全
---
退化
---
组
---
返回
---
空
---
权重
---
 +
---
 `
---
no
---
_valid
---
_strategy
---
=True
---
`


---
###
---
 
---
测试
---
（
---
`
---
tests
---
/test
---
_de
---
generate
---
_filter
---
.py
---
`,
---
 +
---
20
---
 用
---
例
---
）

---
-
---
 字
---
段
---
存在
---
性
---
 +
---
 
---
默认
---
值
---


---
-
---
 batch
---
 vs
---
 single
---
 `
---
closed
---
_tr
---
ades
---
`
---
 一
---
致
---
性
---
（
---
4
---
 
---
策
---
略
---
 ×
---
 多
---
标的
---
）

---
-
---
 `_
---
is
---
_de
---
generate
---
_strategy
---
`
---
：
---
空
---
列表
---
、
---
全
---
零
---
、
---
正常
---
、
---
阈值
---
边界
---
（
---
4
---
/
---
5
---
=
---
0
---
.
---
8
---
 
---
触
---
发
---
、
---
3
---
/
---
5
---
=
---
0
---
.
---
6
---
 不
---
触发
---
）、
---
低
---
频
---
不被
---
误
---
伤
---
、
---
单
---
零
---
不
---
牵
---
连
---
整
---
组
---


---
-
---
 `_
---
run
---
_group
---
`
---
 
---
集
---
成
---
：
---
退化
---
剔除
---
、
---
全
---
退化
---
空
---
仓
---
 +
---
 
---
标
---
记
---
、
---
正常
---
策略
---
不受
---
影响
---


---
-
---
 同
---
步
---
更新
---
 `
---
test
---
_batch
---
_back
---
test
---
.py
---
`
---
 和
---
 `
---
test
---
_matrix
---
_back
---
test
---
.py
---
`
---
 的
---
 mock
---
 数据
---



---
###
---
 
---
测试
---
结果
---


---
**
---
6
---
46
---
 passed
---
,
---
 
---
0
---
 failed
---
,
---
 
---
16
---
 dese
---
lected
---
 (
---
live
---
)**
---
 —
---
 
---
6
---
26
---
 →
---
 
---
6
---
46
---
 (+
---
20
---
)


---
###
---
 文
---
档
---
更新
---


---
-
---
 `
---
design
---
s
---
/design
---
_v
---
2
---
/
---
07
---
-back
---
test
---
-module
---
.md
---
`
---
 —
---
 新
---
增
---
健全
---
性
---
门槛
---
设计
---
点
---
 +
---
 三
---
级
---
 F
---
allback
---
 
---
前
---
置
---
说明
---


---
-
---
 `
---
alignment
---
/
---
iteration
---
_trajectory
---
.md
---
`
---
 —
---
 
---
完
---
整
---
迭代
---
 #
---
11
---
 
---
记
---
录
---
（
---
背景
---
/
---
变更
---
/
---
合规
---
/
---
Experience
---
/
---
后续
---
建议
---
）

---
-
---
 `
---
alignment
---
/
---
decision
---
_log
---
.md
---
`
---
 —
---
 三
---
处
---
模糊
---
决策
---
（
---
v
---
bt
---
 API
---
、
---
阈值
---
取
---
值
---
、
---
mock
---
 同
---
步
---
）

---
-
---
 `.
---
code
---
b
---
uddy
---
/C
---
ODE
---
BU
---
DD
---
Y
---
.md
---
`
---
 —
---
 
---
测试
---
数
---
 
---
60
---
2
---
→
---
6
---
46
---
，
---
补
---
登
---
 Iter
---
 #
---
10
---
/#
---
11
---
 行
---



---
###
---
 关
---
键
---
验证
---


---
-
---
 `
---
rs
---
i
---
_t
---
rend
---
_filter
---
`
---
（
---
Iter
---
 #
---
10
---
 
---
灾
---
难
---
根
---
因
---
）
---
在
---
真实
---
数据
---
上
---
 
---
5
---
 
---
标
---
的
---
 
---
0
---
 closed
---
_tr
---
ades
---
 →
---
 正
---
确
---
被
---
识别
---
为
---
退化
---


---
-
---
 `
---
rs
---
i
---
_mean
---
_re
---
vert
---
`
---
 
---
5
---
 
---
标
---
的
---
各
---
 
---
1
---
-
---
2
---
 closed
---
_tr
---
ades
---
 →
---
 不
---
被
---
误
---
伤
---


---
-
---
 batch
---
 vs
---
 single
---
 `
---
closed
---
_tr
---
ades
---
`
---
 
---
严格
---
一致
---
（
---
4
---
 
---
策
---
略
---
 ×
---
 
---
3
---
 
---
标
---
的
---
）

---
-
---
 
---
0
---
.
---
8
---
 
---
阈
---
值
---
边界
---
：
---
4
---
/
---
5
---
 
---
触
---
发
---
、
---
3
---
/
---
5
---
 不
---
触发
---
，
---
低
---
频
---
策略
---
（
---
每
---
标的
---
 
---
2
---
-
---
3
---
 
---
笔
---
）
---
不被
---
误
---
判
---



---
Meta
---
-Agent
---
 
---
验
---
收
---
阶段
---
（
---
spec
---
 §
---
6
---
）
---
可
---
独立
---
运行
---
 `
---
python
---
 main
---
.py
---
 --
---
re
---
optimize
---
`
---
 
---
验
---
证
---
 `
---
rs
---
i
---
_t
---
rend
---
_filter
---
`
---
 不
---
再
---
出现在
---
任何
---
组
---
权重
---
中
---
、
---
Portfolio
---
Back
---
test
---
 alpha
---
 从
---
 -
---
25
---
%
---
 
---
恢
---
复
---
到
---
可信
---
基线。