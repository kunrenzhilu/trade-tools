Let
---
 me start by reading the spec
---
 file
---
 to understand the
---
 requirements
---
 for iteration
---
 17
---
.
---
{"file_path": "/Users/rickouyang/Github/trade-tools/mytrader/iterations/iteration_17/spec.md"}
---
<tool_use_error>File does not exist.</tool_use_error>
---
<tool_use_error>File does not exist.</tool_use_error>
---
Let
---
 me check the iterations
---
 directory structure.
---
{"command": "ls /Users/rickouyang/Github/trade-tools/mytrader/iterations/ 2>/dev/null || ls /Users/rickouyang/Github/trade-tools/mytrader/ | head -30", "description": "List iterations directory"}
---
List iterations directory
---
Command: ls /Users/rickouyang/Github/trade-tools/mytrader/iterations/ 2>/dev/null || ls /Users/rickouyang/Github/trade-tools/mytrader/ | head -30
Stdout: iteration_8

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
Only
---
 iteration_
---
8 exists. Let me check
---
 the alignment
---
 folder
---
 for iteration
---
_trajectory
---
.md
---
 to understand
---
 the iteration
---
 format
---
 and see
---
 if there's a spec
---
 somewhere
---
 else.
---
{"command": "ls /Users/rickouyang/Github/trade-tools/mytrader/iterations/iteration_8/ && echo \"---\" && ls /Users/rickouyang/Github/trade-tools/alignment/ 2>/dev/null", "description": "List iteration_8 and alignment directories"}
---
List iteration_8 and alignment directories
---
Command: ls /Users/rickouyang/Github/trade-tools/mytrader/iterations/iteration_8/ && echo "---" && ls /Users/rickouyang/Github/trade-tools/alignment/ 2>/dev/null
Stdout: spec.md
---
__pycache__             iteration_trajectory.md questionair.md
ai_constitution.md      monitor.py              tests
decision_log.md         orchestrator.py
interview_progress.md   orchestrator_design.md

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
The
---
 spec
---
 file
---
 for iteration
---
_
---
17 doesn't
---
 exist. The user wants
---
 me to follow
---
 the spec at
---
 `iterations/iteration_17
---
/spec.md`, but it
---
 doesn't exist. The user
---
 has provided
---
 the
---
 key goals
---
 in
---
 the query
---
 itself:

1. Read
---
 `
---
matrix_backtest.py
---
::_
---
run_group
---
` to locate
---
 the alpha gate
---

2. Add
---
 `SORT
---
INO_ALPHA
---
_EXEM
---
PTION = 
---
1.5` constant
---

3. Modify
---
 Tier
---
 1 filter
---
: `alpha
---
 > -
---
2%
---
 OR sort
---
ino > 1.5
---
`
4. Write
---
 ~
---
7 new
---
 tests (high
---
 Sortino exemption
---
, low Sortino still needs
---
 alpha, DD
---
 still mandatory
---
, min
---
 Sortino still mandatory
---
, boundary
---
 tests)
5. Run
---
 all tests
6. Run
---
 `--re
---
optimize
---
`
7. Verify
---
 `strategy_weights.json
---
` has at least 1
---
 SP
---
X group
---
 non-empty
---

8. Update
---
 trajectory +
---
 CODEBU
---
DDY
---


Scope
---
:
---
 Don
---
't modify strategy
---
/ind
---
icators/risk/execution
---
/main.py

Let me first
---
 read
---
 the current
---
 state of matrix
---
_backtest.py to understand the
---
 alpha gate logic
---
, and also
---
 check the iteration_trajectory
---
.md format
---
.
---
 Let me also
---
 read
---
 the iteration
---
_8 spec
---
 for
---
 reference
---
 format
---
.

Let
---
 me also
---
 check memory
---
 for any
---
 pytest
---
 sandbox
---
 workaround
---
.
---
迭代
---
 
---
17 的规范
---
文件尚
---
不存在。用户
---
已在
---
查询中提供了关键需求
---
。让我先
---
设置
---
任务
---
，
---
并读取
---
相关
---
文件的当前状态。
---
{"activeForm": "Reading _run_group alpha gate", "description": "Read mytrader/backtest/matrix_backtest.py::_run_group to locate the alpha gate (ALPHA_GATE_THRESHOLD=-2.0 from Iter #16)", "subject": "Read matrix_backtest.py _run_group to locate alpha gate"}
---
Task #1 created successfully: Read matrix_backtest.py _run_group to locate alpha gate
---
Task #1 created successfully: Read matrix_backtest.py _run_group to locate alpha gate
---
{"activeForm": "Adding SORTINO_ALPHA_EXEMPTION constant", "description": "Add SORTINO_ALPHA_EXEMPTION = 1.5 constant to matrix_backtest.py near ALPHA_GATE_THRESHOLD", "subject": "Add SORTINO_ALPHA_EXEMPTION constant"}
---
Task #2 created successfully: Add SORTINO_ALPHA_EXEMPTION constant
---
Task #2 created successfully: Add SORTINO_ALPHA_EXEMPTION constant
---
{"activeForm": "Modifying Tier 1 filter for Sortino exemption", "description": "Modify Tier 1 filter in _run_group: alpha > -2% OR sortino > 1.5 (Sortino exemption)", "subject": "Modify Tier 1 filter for Sortino exemption"}
---
Task #3 created successfully: Modify Tier 1 filter for Sortino exemption
---
Task #3 created successfully: Modify Tier 1 filter for Sortino exemption
---
{"activeForm": "Writing ~7 new tests for Sortino exemption", "description": "Write ~7 new tests covering: high Sortino exemption, low Sortino still needs alpha, DD still mandatory, min Sortino still mandatory, boundary tests", "subject": "Write ~7 new tests for Sortino exemption"}
---
Task #4 created successfully: Write ~7 new tests for Sortino exemption
---
Task #4 created successfully: Write ~7 new tests for Sortino exemption
---
{"activeForm": "Running all tests", "description": "Run pytest to confirm all tests pass (use pytest sandbox workaround: PYTHONPATH= + NUMBA_DISABLE_CACHE=1 + dangerouslyDisableSandbox)", "subject": "Run all tests to confirm passing"}
---
Task #5 created successfully: Run all tests to confirm passing
---
Task #5 created successfully: Run all tests to confirm passing
---
{"activeForm": "Running --reoptimize", "description": "Run python main.py --reoptimize to regenerate strategy_weights.json", "subject": "Run --reoptimize to regenerate weights"}
---
Task #6 created successfully: Run --reoptimize to regenerate weights
---
Task #6 created successfully: Run --reoptimize to regenerate weights
---
{"activeForm": "Verifying SPX groups in strategy_weights.json", "description": "Verify strategy_weights.json has at least 1 SPX group non-empty (unblocked by Sortino exemption)", "subject": "Verify SPX groups non-empty in weights"}
---
Task #7 created successfully: Verify SPX groups non-empty in weights
---
Task #7 created successfully: Verify SPX groups non-empty in weights
---
{"activeForm": "Updating trajectory + CODEBUDDY", "description": "Update alignment/iteration_trajectory.md (L9 format) and .codebuddy/CODEBUDDY.md with Iter #17 changes", "subject": "Update trajectory + CODEBUDDY docs"}
---
Task #8 created successfully: Update trajectory + CODEBUDDY docs
---
Task #8 created successfully: Update trajectory + CODEBUDDY docs
---
现在
---
让我开始
---
读取相关
---
文件。
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
  43→# 迭代 #13 新增：WF 验证期 alpha 单轮下限（百分数）
  44→# 单轮允许小幅跑输 SPY（alpha > -5%），但 4 轮平均必须跑赢（avg > 0）
  45→# 设计动机：WF 与 matrix_backtest 目标一致性——matrix_backtest 用 alpha 选策略，
  46→# WF 也必须校验 alpha，否则 WF 通过 ≠ 跑赢 SPY
  47→# （Iter #11 实证：WF 4/4 pass 但组合 alpha=-21%，因为 WF gate 只校验 DD 不校验 alpha）
  48→# 详见 experience.md #8："验收 gate 必须校验跑赢 benchmark（正 alpha）"
  49→WALK_FORWARD_VAL_ALPHA_FLOOR: float = -5.0
  50→
  51→# 迭代 #9 新增：Sortino 最低质量门槛，用于 top-K 选择时的二级过滤
  52→# 排除 Sortino ≤ 0.5 的"垃圾"策略（即使 alpha 高也不选）
  53→# 设计动机：alpha 排序选出高绝对收益策略，但需 Sortino 门槛保证基本下行质量
  54→# fallback：若无候选通过此门槛，放宽过滤（仅保留 DD 硬约束）
  55→MIN_SORTINO_THRESHOLD: float = 0.5
  56→
  57→# 迭代 #16 新增：alpha gate 门槛（in-sample），用于 _run_group 排序前的硬门槛。
  58→# Iter #12 原值为 0（alpha>0 才入选），Iter #16 放宽至 -2%。
  59→# 设计动机：SPX 成分股 vs SPY benchmark 存在结构性近零 alpha —— SPY 即 S&P 500
  60→# 本身，交易 SPX 组件 vs SPY 相当于"和自己赛跑"。alpha=-1%（小幅跑输 SPY）的
  61→# 策略仍可能有出色的 Sortino / DD，不应被一刀切拒绝。
  62→# 与 WF OOS 校验的关系：Walk-Forward（Iter #13）仍用 -5% 单轮下限 + avg>0 汇总
  63→# 门槛，放宽 in-sample gate 不会削弱 OOS 验证强度。
  64→# 取 -2% 的理由：足以过滤"灾难性跑输"（如 -5% 以下），但保留"小幅跑输"的
  65→# 合理候选；阈值与 WALK_FORWARD_VAL_ALPHA_FLOOR=-5% 形成 3% 缓冲带。
  66→ALPHA_GATE_THRESHOLD: float = -2.0
  67→
  68→# 迭代 #11 新增：健全性门槛 —— 识别"退化策略"（几乎不平仓的伪 buy-and-hold）
  69→# 判定：组内"有效标的中，已平仓交易数为 0 的比例"超过此阈值 → 退化
  70→# 设计动机：真策略应在多数标的上完成买卖闭环；若近乎所有标的都从不平仓，
  71→#           说明入场/出场条件矛盾（如 Iter #8 rsi_trend_filter），其收益只是
  72→#           持仓盯市 + 末尾强平的假象，必须在排序前剔除（experience.md #8）。
  73→# 阈值取 0.8（保守）：只在"近乎全部标的零平仓"时触发，避免误伤低频合法策略。
  74→DEGENERATE_NO_CLOSE_FRACTION: float = 0.8
  75→
  76→
  77→# ---------------------------------------------------------------------------
  78→# 数据结构
  79→# ---------------------------------------------------------------------------
  80→
  81→@dataclass
  82→class SingleBacktestResult:
  83→    """单只标的单策略回测结果。"""
  84→
  85→    symbol: str
  86→    strategy: str
  87→    params: dict
  88→    sharpe: float
  89→    total_return_pct: float
  90→    max_drawdown_pct: float
  91→    win_rate_pct: float
  92→    total_trades: int
  93→    daily_returns: pd.Series    # pf.returns() — 供组合 Sharpe / Sortino 计算
  94→    sortino: float = 0.0       # Constitution L1 首要 KPI（迭代 #1 新增）
  95→    closed_trades: int = 0     # 迭代 #11 新增：已平仓交易数（区分退化 buy-and-hold）
  96→
  97→
  98→@dataclass
  99→class GroupBacktestResult:
 100→    """单组策略回测结果。"""
 101→
 102→    group_id: str
 103→    strategy: str
 104→    params: dict
 105→    portfolio_sharpe: float          # 等权组合 Sharpe（而非算术平均）
 106→    avg_total_return_pct: float
 107→    avg_max_drawdown_pct: float
 108→    avg_win_rate_pct: float
 109→    symbol_count: int
 110→    portfolio_sortino: float = 0.0          # 等权组合 Sortino（迭代 #1 新增）
 111→    portfolio_max_drawdown: float = 0.0     # 等权组合最大回撤（迭代 #2 新增，Constitution L1 KPI）
 112→    dd_constrained: bool = False            # 迭代 #3：该组是否用了 DD fallback（无合规候选）
 113→    backtest_alpha: float = 0.0              # 迭代 #9：alpha vs SPY（百分数），用于排序策略选择
 114→    no_valid_strategy: bool = False         # 迭代 #11：该组是否因全退化而空仓（hold cash）
 115→    no_positive_alpha: bool = False         # 迭代 #12：该组是否因全负 alpha 而空仓（hold cash）
 116→
 117→
 118→@dataclass
 119→class MatrixBacktestReport:
 120→    """整个矩阵回测的汇总报告。"""
 121→
 122→    generated_at: str
 123→    backtest_window: str
 124→    groups: dict[str, list[dict]]   # group_id → [策略权重配置]
 125→    group_results: list[GroupBacktestResult] = field(default_factory=list)
 126→    warnings: list[str] = field(default_factory=list)
 127→
 128→
 129→# ---------------------------------------------------------------------------
 130→# Walk-Forward 数据结构（迭代 #3 新增，Constitution L7 验证流水线）
 131→# ---------------------------------------------------------------------------
 132→
 133→@dataclass
 134→class WalkForwardRound:
 135→    """单轮 Walk-Forward 验证结果。
 136→
 137→    一轮 = 训练期（找最优参数）+ 验证期（用同参数回测，记录样本外指标）。
 138→
 139→    Attributes:
 140→        round_num:    轮次编号（1-indexed）
 141→        train_start:  训练期起始日期（含）
 142→        train_end:    训练期结束日期（含）
 143→        val_start:    验证期起始日期（含）
 144→        val_end:      验证期结束日期（含）
 145→        val_sortino:  验证期等权组合 Sortino Ratio（年化）
 146→        val_max_dd:   验证期等权组合最大回撤（正值百分数，0~100）
 147→        val_alpha:    验证期等权组合 alpha vs SPY（百分数，迭代 #13 新增）
 148→                      与 matrix_backtest 的 alpha 选择目标一致（目标一致性修复）
 149→        passed:       是否通过 = val_max_dd <= 15% AND val_alpha > -5%
 150→    """
 151→
 152→    round_num: int
 153→    train_start: date
 154→    train_end: date
 155→    val_start: date
 156→    val_end: date
 157→    val_sortino: float
 158→    val_max_dd: float
 159→    passed: bool
 160→    # 迭代 #13：验证期 portfolio alpha vs SPY（百分数）
 161→    # 放在 passed 之后以保持与现有位置参数调用的向后兼容
 162→    # （现有测试用 8 个位置参数：round_num...passed）
 163→    val_alpha: float = 0.0
 164→
 165→
 166→@dataclass
 167→class WalkForwardReport:
 168→    """Walk-Forward 4 轮验证汇总报告。
 169→
 170→    Constitution L7 要求 Backtest(>=5年) → Walk-Forward(4轮) → Paper → Live。
 171→    本报告是 Walk-Forward 阶段的产出。
 172→
 173→    Attributes:
 174→        rounds:         每轮结果列表（长度通常为 4）
 175→        pass_all_rounds: 是否所有轮都通过 AND avg_val_alpha > 0
 176→                         （迭代 #13：加 avg alpha > 0 条件，要求 OOS 平均跑赢 SPY）
 177→        max_val_dd:     所有轮中最大的验证期 DD（用于风险监控）
 178→        avg_val_alpha:  所有轮验证期 alpha 的平均值（迭代 #13 新增，百分数）
 179→        min_val_alpha:  所有轮中最差的验证期 alpha（迭代 #13 新增，百分数）
 180→    """
 181→
 182→    rounds: list[WalkForwardRound] = field(default_factory=list)
 183→    pass_all_rounds: bool = False
 184→    max_val_dd: float = 0.0
 185→    avg_val_alpha: float = 0.0   # 迭代 #13：4 轮平均验证期 alpha（百分数）
 186→    min_val_alpha: float = 0.0   # 迭代 #13：4 轮中最差的验证期 alpha（百分数）
 187→
 188→
 189→# ---------------------------------------------------------------------------
 190→# 核心函数
 191→# ---------------------------------------------------------------------------
 192→
 193→def _safe_float(value: Any, default: float = 0.0) -> float:
 194→    """NaN/None/非数值安全转 float（迭代 #2 新增）。
 195→
 196→    问题背景：vectorbt 在无交易场景下，`pf.stats()` 的 Win Rate / Sharpe 等
 197→    字段会返回 NaN。`float(NaN or 0.0)` 仍是 NaN（NaN 是 truthy），导致
 198→    JSON 序列化写出非法 JSON（NaN/Infinity 非 JSON 规范）。
 199→
 200→    处理顺序：
 201→        1. None → default
 202→        2. 数值类型但 NaN/Inf → default
 203→        3. 非数值（字符串等）尝试 float() 转换，失败 → default
 204→    """
 205→    if value is None:
 206→        return default
 207→    try:
 208→        f = float(value)
 209→    except (TypeError, ValueError):
 210→        return default
 211→    if not np.isfinite(f):   # 拦截 NaN / +Inf / -Inf
 212→        return default
 213→    return f
 214→
 215→
 216→def _safe_mean(values: Any, default: float = 0.0) -> float:
 217→    """空列表 / 全 NaN 安全的均值（迭代 #2 新增）。
 218→
 219→    问题背景：`np.mean([])` 会触发 RuntimeWarning 并返回 NaN；
 220→    `np.mean([NaN, NaN])` 直接返回 NaN。在 GroupBacktestResult 聚合时
 221→    若某组只有 1 个标的且其字段为 NaN，会导致下游 JSON 序列化失败。
 222→
 223→    行为：
 224→        - 空列表 / 全 NaN → default
 225→        - 部分 NaN → 自动忽略 NaN 后取均值（np.nanmean 语义）
 226→    """
 227→    arr = np.asarray(values, dtype=float)
 228→    if arr.size == 0:
 229→        return default
 230→    mask = np.isfinite(arr)
 231→    if not mask.any():
 232→        return default
 233→    return float(arr[mask].mean())
 234→
 235→
 236→def _compute_sharpe(returns: pd.Series, periods_per_year: int = 252) -> float:
 237→    """从日收益率序列计算年化 Sharpe Ratio。"""
 238→    returns = returns.dropna()
 239→    if len(returns) < 5:
 240→        return 0.0
 241→    mean = returns.mean()
 242→    std = returns.std()
 243→    if std <= 0 or np.isnan(std):
 244→        return 0.0
 245→    return float(mean / std * np.sqrt(periods_per_year))
 246→
 247→
 248→def _compute_sortino(
 249→    returns: pd.Series,
 250→    periods_per_year: int = 252,
 251→    target: float = 0.0,
 252→) -> float:
 253→    """从日收益率序列计算年化 Sortino Ratio（Constitution L1 首要 KPI）。
 254→
 255→    Sortino = (mean(returns) - target) / downside_deviation * sqrt(periods_per_year)
 256→    downside_deviation = sqrt( mean( min(0, returns - target)^2 ) )
 257→
 258→    与 Sharpe 的区别：仅对下行波动惩罚，上行波动不计入分母。
 259→    适合"收益>0 但偶尔大跌"的中长线策略评估。
 260→
 261→    退化处理（与 _compute_sharpe 一致）：
 262→        - 样本 < 5 → 0.0
 263→        - 下行波动 ≤ 0（无下行样本）→ 0.0（理论为 +inf，返回 0 保持保守 + 可算术聚合）
 264→
 265→    Args:
 266→        returns:          日收益率序列（如 pf.returns()）
 267→        periods_per_year: 年化因子（日线 = 252）
 268→        target:           MAR/目标收益率，默认 0（与 _compute_sharpe 无风险利率假设一致）
 269→
 270→    Returns:
 271→        年化 Sortino Ratio
 272→    """
 273→    returns = returns.dropna()
 274→    if len(returns) < 5:
 275→        return 0.0
 276→    excess = returns - target
 277→    downside = excess.where(excess < 0, 0.0)        # 仅保留负偏离，正偏离置 0
 278→    dd = np.sqrt((downside ** 2).mean())
 279→    if dd <= 0 or np.isnan(dd):
 280→        return 0.0
 281→    return float(returns.mean() / dd * np.sqrt(periods_per_year))
 282→
 283→
 284→def _combine_daily_returns(results: list[SingleBacktestResult]) -> pd.Series:
 285→    """等权合并组内日收益率序列，返回组合日收益率（迭代 #9 新增）。
 286→
 287→    与 _portfolio_sharpe_from_results / _portfolio_sortino_from_results 同语义：
 288→    将所有标的日收益率等权合并为组合序列。提取为独立函数以便 alpha 计算
 289→    和 per-strategy best params 选择复用，避免重复 pd.concat。
 290→
 291→    Args:
 292→        results: 单策略多标的的回测结果列表
 293→
 294→    Returns:
 295→        组合日收益率 pd.Series；无有效数据时返回空 Series
 296→    """
 297→    valid = [r.daily_returns for r in results if not r.daily_returns.empty]
 298→    if not valid:
 299→        return pd.Series(dtype=float)
 300→    return pd.concat(valid, axis=1).mean(axis=1)
 301→
 302→
 303→def _is_degenerate_strategy(results: list[SingleBacktestResult]) -> bool:
 304→    """判定一个策略在组内是否退化（几乎不产生已平仓交易）（迭代 #11 新增）。
 305→
 306→    退化定义：有效标的中 closed_trades==0 的比例 >= DEGENERATE_NO_CLOSE_FRACTION。
 307→    这类策略的入场/出场条件互斥（如 Iter #8 rsi_trend_filter 趋势过滤锁死均值
 308→    回归出场），仓位无法平仓，其 Sortino/alpha 只是持仓盯市假象，不代表真实
 309→    交易能力，必须在排序前剔除（experience.md #8：sanity → risk → rank）。
 310→
 311→    Args:
 312→        results: 单策略多标的的回测结果列表
 313→
 314→    Returns:
 315→        True 表示退化（应剔除）；空结果视为退化（True）
 316→    """
 317→    if not results:
 318→        return True
 319→    n = len(results)
 320→    no_close = sum(1 for r in results if r.closed_trades <= 0)
 321→    return (no_close / n) >= DEGENERATE_NO_CLOSE_FRACTION
 322→
 323→
 324→def _compute_alpha(
 325→    strategy_daily_returns: pd.Series,
 326→    spy_daily_returns: pd.Series | None,
 327→    periods_per_year: int = 252,
 328→) -> float:
 329→    """计算 alpha = 策略年化收益 - SPY 年化收益（迭代 #9 新增）。
 330→
 331→    Alpha 衡量策略相对 SPY buy-and-hold 的超额收益。正值表示跑赢 SPY，
 332→    负值表示跑输 SPY。用于 top-K 策略选择和 per-strategy best params 选择，
 333→    替代之前基于 Sortino/Sharpe 的选择逻辑（参考 iteration #9 spec）。
 334→
 335→    年化公式：(1 + mean_daily) ** periods_per_year - 1
 336→    使用算术平均日收益的几何年化，与 PortfolioBacktester 同口径。
 337→
 338→    降级处理：SPY 数据不可用（None 或空）→ 返回 0.0（不抛异常）。
 339→    这样在 SPY 数据缺失时，alpha 排序退化为"原顺序"，不会阻塞回测。
 340→
 341→    Args:
 342→        strategy_daily_returns: 策略组合日收益率序列
 343→        spy_daily_returns:      SPY 日收益率序列；None 表示数据不可用
 344→        periods_per_year:       年化因子（日线 = 252）
 345→
 346→    Returns:
 347→        Alpha 百分数（如 5.23 表示策略年化收益跑赢 SPY 5.23 个百分点）；
 348→        SPY 不可用时返回 0.0
 349→    """
 350→    if spy_daily_returns is None or spy_daily_returns.empty:
 351→        return 0.0
 352→    if strategy_daily_returns is None or strategy_daily_returns.empty:
 353→        return 0.0
 354→
 355→    # 对齐时间索引（inner join 取交集）
 356→    aligned = pd.concat(
 357→        [strategy_daily_returns.rename("strat"), spy_daily_returns.rename("spy")],
 358→        axis=1,
 359→        join="inner",
 360→    ).dropna()
 361→    if aligned.empty or len(aligned) < 2:
 362→        return 0.0
 363→
 364→    strat_returns = aligned["strat"]
 365→    spy_returns = aligned["spy"]
 366→
 367→    # 年化收益 = (1 + mean_daily)^252 - 1
 368→    strat_mean = strat_returns.mean()
 369→    spy_mean = spy_returns.mean()
 370→    if not np.isfinite(strat_mean) or not np.isfinite(spy_mean):
 371→        return 0.0
 372→
 373→    strat_annual = (1.0 + strat_mean) ** periods_per_year - 1.0
 374→    spy_annual = (1.0 + spy_mean) ** periods_per_year - 1.0
 375→
 376→    alpha = (strat_annual - spy_annual) * 100.0  # 转为百分数
 377→    if not np.isfinite(alpha):
 378→        return 0.0
 379→    return float(alpha)
 380→
 381→
 382→def _backtest_one(
 383→    df: pd.DataFrame,
 384→    strategy_name: str,
 385→    params: dict,
 386→    init_cash: float = 100_000.0,
 387→    fees: float = 0.001,
 388→    slippage: float = 0.001,
 389→) -> SingleBacktestResult | None:
 390→    """对单只标的执行单次回测。
 391→
 392→    使用 open= 参数确保信号在下一根 bar 的开盘价执行（与实盘一致）。
 393→
 394→    Returns:
 395→        SingleBacktestResult 或 None（数据不足/策略异常时）
 396→    """
 397→    strategy_fn = STRATEGY_REGISTRY.get(strategy_name)
 398→    if strategy_fn is None:
 399→        return None
 400→
 401→    if df.empty or len(df) < 30:
 402→        return None
 403→
 404→    try:
 405→        close = df["close"]
 406→        open_ = df["open"] if "open" in df.columns else None
 407→
 408→        # 调用策略（兼容需要 df 的策略）
 409→        try:
 410→            sig = strategy_fn(close, df=df, **params)
 411→        except TypeError:
 412→            sig = strategy_fn(close, **params)
 413→
 414→        entries = sig == 1
 415→        exits   = sig == -1
 416→
 417→        pf_kwargs: dict[str, Any] = dict(
 418→            entries=entries,
 419→            exits=exits,
 420→            init_cash=init_cash,
 421→            fees=fees,
 422→            slippage=slippage,
 423→            size=0.95,
 424→            size_type="Percent",
 425→            freq="D",
 426→        )
 427→
 428→        # ⚠️ 必须传 open= 参数：信号在下一根 bar 开盘价执行，与实盘一致
 429→        if open_ is not None:
 430→            pf = vbt.Portfolio.from_signals(close=close, open=open_, **pf_kwargs)
 431→        else:
 432→            pf = vbt.Portfolio.from_signals(close, **pf_kwargs)
 433→
 434→        stats = pf.stats()
 435→
 436→        daily_returns = pf.returns()
 437→
 438→        # 迭代 #11：已平仓交易数（用于健全性门槛 _is_degenerate_strategy）
 439→        # vbt 1.0 API: pf.trades.closed.count() 返回 Status==Closed 的交易数
 440→        # 区分"真交易闭环"与"末尾强平计 1 笔的伪 buy-and-hold"
 441→        try:
 442→            closed_trades = int(pf.trades.closed.count())
 443→        except Exception:
 444→            closed_trades = 0
 445→
 446→        return SingleBacktestResult(
 447→            symbol=str(df.index.name or ""),
 448→            strategy=strategy_name,
 449→            params=params,
 450→            sharpe=_safe_float(stats.get("Sharpe Ratio")),
 451→            total_return_pct=_safe_float(stats.get("Total Return [%]")),
 452→            max_drawdown_pct=_safe_float(stats.get("Max Drawdown [%]")),
 453→            win_rate_pct=_safe_float(stats.get("Win Rate [%]")),
 454→            total_trades=int(_safe_float(stats.get("Total Trades"), default=0.0)),
 455→            daily_returns=daily_returns,
 456→            sortino=_compute_sortino(daily_returns),
 457→            closed_trades=closed_trades,
 458→        )
 459→    except Exception as e:
 460→        logger.debug(f"[backtest_one] {strategy_name}({params}) failed: {e}")
 461→        return None
 462→
 463→
 464→def _backtest_batch(
 465→    data: dict[str, pd.DataFrame],
 466→    strategy_name: str,
 467→    params: dict,
 468→    init_cash: float = 100_000.0,
 469→    fees: float = 0.001,
 470→    slippage: float = 0.001,
 471→) -> list[SingleBacktestResult]:
 472→    """对组内所有标的批量执行回测（迭代 #10 新增）。
 473→
 474→    核心优化：用一次 vbt.Portfolio.from_signals 处理组内所有标的，
 475→    替代 `_backtest_one` 的 for-symbol 循环。调用次数从 O(N 标的)
 476→    降为 O(1)，预计 10-20x 提速（spec §1）。
 477→
 478→    实现要点：
 479→        1. 逐标的调用策略函数（保持与 `_backtest_one` 一致的调用语义：
 480→           先尝试 `strategy_fn(close, df=df, **params)`，TypeError 时
 481→           回退到 `strategy_fn(close, **params)`）。策略函数本身不改。
 482→        2. 构建列式矩阵（每列一个标的），用一次 vbt 调用回测所有标的。
 483→           vbt 1.0+ 的列分组语义保证每列独立结算 P&L。
 484→        3. 通过 `pf[sym]` 提取每列的 stats/daily_returns，输出格式与
 485→           `_backtest_one` 完全一致，下游聚合代码无需修改。
 486→
 487→    对齐策略：
 488→        - 用 `pd.DataFrame(dict)` 构造时自动 outer-join 时间索引，
 489→          缺失值填 NaN。
 490→        - vbt 对 NaN close 的处理：内部 fillna 为 0 收益率，等价于
 491→          "该标的此日期不交易"。当标的在样本外日期缺失时（如退市、
 492→          新上市），其 stats 仍按其有效日期区间计算。
 493→        - 在美股实际场景中所有标的共享交易日历，日期对齐天然成立，
 494→          不会有大量 NaN。
 495→
 496→    Args:
 497→        data:          {symbol: OHLCV DataFrame} 字典
 498→        strategy_name: 策略名
 499→        params:        策略参数
 500→        init_cash:     初始资金（vbt 给每列分配独立的 init_cash）
 501→        fees:          手续费率
 502→        slippage:      滑点率
 503→
 504→    Returns:
 505→        SingleBacktestResult 列表（与 `_backtest_one` 输出格式一致）。
 506→        数据不足 / 策略异常的标的会被跳过（不返回 None，不抛异常）。
 507→        空数据时返回空列表。
 508→    """
 509→    strategy_fn = STRATEGY_REGISTRY.get(strategy_name)
 510→    if strategy_fn is None:
 511→        return []
 512→
 513→    # 1. 逐标的调用策略函数，构建 signal / close / open 列
 514→    signal_columns: dict[str, pd.Series] = {}
 515→    close_columns: dict[str, pd.Series] = {}
 516→    open_columns: dict[str, pd.Series] = {}
 517→
 518→    for sym, df in data.items():
 519→        if df is None or df.empty or len(df) < 30:
 520→            continue
 521→        close = df["close"]
 522→        if "open" in df.columns:
 523→            open_ = df["open"]
 524→            open_columns[sym] = open_
 525→        else:
 526→            open_ = None
 527→
 528→        # 调用策略（与 _backtest_one 一致的 try/except 语义）
 529→        try:
 530→            sig = strategy_fn(close, df=df, **params)
 531→        except TypeError:
 532→            sig = strategy_fn(close, **params)
 533→        except Exception as e:
 534→            logger.debug(
 535→                f"[backtest_batch] {strategy_name}({params}) {sym} failed: {e}"
 536→            )
 537→            continue
 538→
 539→        signal_columns[sym] = sig
 540→        close_columns[sym] = close
 541→
 542→    if not signal_columns:
 543→        return []
 544→
 545→    # 2. 构建矩阵（自动 outer-join 索引，缺失值填 NaN）
 546→    close_matrix = pd.DataFrame(close_columns)
 547→    signal_matrix = pd.DataFrame(signal_columns)
 548→    has_open = bool(open_columns)
 549→    open_matrix = pd.DataFrame(open_columns) if has_open else None
 550→
 551→    # 3. 一次 vbt 调用处理所有标的
 552→    entries = signal_matrix == 1
 553→    exits = signal_matrix == -1
 554→
 555→    pf_kwargs: dict[str, Any] = dict(
 556→        entries=entries,
 557→        exits=exits,
 558→        init_cash=init_cash,
 559→        fees=fees,
 560→        slippage=slippage,
 561→        size=0.95,
 562→        size_type="Percent",
 563→        freq="D",
 564→    )
 565→
 566→    try:
 567→        if has_open:
 568→            pf = vbt.Portfolio.from_signals(
 569→                close=close_matrix, open=open_matrix, **pf_kwargs
 570→            )
 571→        else:
 572→            pf = vbt.Portfolio.from_signals(close_matrix, **pf_kwargs)
 573→    except Exception as e:
 574→        logger.warning(
 575→            f"[backtest_batch] {strategy_name}({params}) vbt call failed: {e} "
 576→            f"— falling back to per-symbol _backtest_one"
 577→        )
 578→        # 回滚方案：批量失败时退化为逐标的回测，保证回测不中断
 579→        results: list[SingleBacktestResult] = []
 580→        for sym, df in data.items():
 581→            if df is None or df.empty or len(df) < 30:
 582→                continue
 583→            df = df.copy()
 584→            df.index.name = sym
 585→            r = _backtest_one(
 586→                df, strategy_name, params, init_cash, fees, slippage
 587→            )
 588→            if r is not None:
 589→                results.append(r)
 590→        return results
 591→
 592→    # 4. 提取 per-symbol 结果（与 _backtest_one 输出格式一致）
 593→    results = []
 594→    for sym in signal_matrix.columns:
 595→        try:
 596→            pf_sym = pf[sym]
 597→            stats = pf_sym.stats()
 598→            daily_returns = pf_sym.returns()
 599→            # 迭代 #11：已平仓交易数（与 _backtest_one 同 API、同语义）
 600→            # pf_sym 是单列 pf，pf_sym.trades.closed.count() 返回 int
 601→            try:
 602→                closed_trades = int(pf_sym.trades.closed.count())
 603→            except Exception:
 604→                closed_trades = 0
 605→            results.append(SingleBacktestResult(
 606→                symbol=sym,
 607→                strategy=strategy_name,
 608→                params=params,
 609→                sharpe=_safe_float(stats.get("Sharpe Ratio")),
 610→                total_return_pct=_safe_float(stats.get("Total Return [%]")),
 611→                max_drawdown_pct=_safe_float(stats.get("Max Drawdown [%]")),
 612→                win_rate_pct=_safe_float(stats.get("Win Rate [%]")),
 613→                total_trades=int(_safe_float(stats.get("Total Trades"), default=0.0)),
 614→                daily_returns=daily_returns,
 615→                sortino=_compute_sortino(daily_returns),
 616→                closed_trades=closed_trades,
 617→            ))
 618→        except Exception as e:
 619→            logger.debug(
 620→                f"[backtest_batch] {strategy_name}({params}) {sym} "
 621→                f"stats extraction failed: {e}"
 622→            )
 623→            continue
 624→
 625→    return results
 626→
 627→
 628→def _portfolio_sharpe_from_results(results: list[SingleBacktestResult]) -> float:
 629→    """等权合并组内日收益率序列，计算组合 Sharpe。
 630→
 631→    ⚠️ 不能取各标的 Sharpe 算术平均（Sharpe 是比率，不能直接平均）。
 632→    正确做法：将所有标的日收益率等权合并为组合序列，再计算 Sharpe。
 633→    """
 634→    valid = [r.daily_returns for r in results if not r.daily_returns.empty]
 635→    if not valid:
 636→        return 0.0
 637→
 638→    # 对齐时间索引，等权平均
 639→    combined = pd.concat(valid, axis=1).mean(axis=1)
 640→    return _compute_sharpe(combined)
 641→
 642→
 643→def _portfolio_sortino_from_results(results: list[SingleBacktestResult]) -> float:
 644→    """等权合并组内日收益率序列，计算组合 Sortino（与 _portfolio_sharpe_from_results 同语义）。
 645→
 646→    不能取各标的 Sortino 算术平均（与 Sharpe 同理：比率不可直接平均）。
 647→    """
 648→    valid = [r.daily_returns for r in results if not r.daily_returns.empty]
 649→    if not valid:
 650→        return 0.0
 651→    combined = pd.concat(valid, axis=1).mean(axis=1)
 652→    return _compute_sortino(combined)
 653→
 654→
 655→def _portfolio_max_drawdown_from_results(
 656→    results: list[SingleBacktestResult],
 657→) -> float:
 658→    """等权合并组内日收益率序列，计算组合最大回撤（迭代 #2 新增，Constitution L1 KPI）。
 659→
 660→    与 `_portfolio_sharpe_from_results` 同语义：不能取各标的 DD 算术平均，
 661→    因为 DD 是路径依赖的比率。正确做法是先把��内日收益率等权合并为组合序列，
 662→    再 cumprod → cummax → drawdown → max。
 663→
 664→    返回值约定：百分比形式（与 `SingleBacktestResult.max_drawdown_pct` 一致，
 665→    vectorbt stats 中 `Max Drawdown [%]` 同样是百分数，例如 -15.2 表示 15.2% 回撤）。
 666→    本函数返回正值（0.0 ~ 100.0）便于聚合与 JSON 输出。
 667→
 668→    退化处理：
 669→        - 无有效日收益率 → 0.0
 670→        - 全 0 收益率（cumprod 恒为 1.0）→ 0.0
 671→    """
 672→    valid = [r.daily_returns for r in results if not r.daily_returns.empty]
 673→    if not valid:
 674→        return 0.0
 675→    combined = pd.concat(valid, axis=1).mean(axis=1).dropna()
 676→    if len(combined) < 2:
 677→        return 0.0
 678→    # 组合累计净值：初始 1.0，每日乘 (1 + r)
 679→    cumvalue = (1.0 + combined).cumprod()
 680→    peak = cumvalue.cummax()
 681→    drawdown = (cumvalue - peak) / peak   # 负值，0 表示无回撤
 682→    dd_max_pct = float(drawdown.min())    # 最负值，例如 -0.152
 683→    if not np.isfinite(dd_max_pct):
 684→        return 0.0
 685→    # 转为正百分数（与 vectorbt Max Drawdown [%] 的口径一致但取正号）
 686→    return abs(dd_max_pct) * 100.0
 687→
 688→
 689→def _optimize_ensemble_weights(
 690→    group_results: list[tuple[str, dict, list[SingleBacktestResult]]],
 691→    spy_returns: pd.Series | None = None,
 692→    conflict_threshold: float = 0.3,
 693→) -> list[tuple[str, dict, float]]:
 694→    """在"单点离散值加权投票"语义下优化 ensemble 权重。
 695→
 696→    实盘每根 bar 各策略产出离散值（1/-1/0），加权投票决定方向。
 697→    回测的权重优化必须使用相同语义，而非对整段时间序列做加权。
 698→
 699→    迭代 #9：权重计算从 Sharpe 改为 Alpha（vs SPY）。
 700→    动机：与 _run_group 的 top-K 排序口径一致，使 ensemble 权重直接
 701→    反映"跑赢 SPY 的程度"。SPY 不可用时 alpha=0，退化为等权。
 702→
 703→    迭代 #12：修负 alpha 归一化 bug。
 704→    旧代码 `max(alpha, 0.01)` 把负 alpha 都变成 0.01，归一化后等权，
 705→    掩盖"都不好"的事实（experience.md #8）。新逻辑：负 alpha 权重为 0，
 706→    只有正 alpha 参与归一化；全负 alpha 时等权 fallback + WARNING
 707→    （上游 alpha gate 应已拦截，此处为防御性设计）。
 708→
 709→    迭代 #16 注：上游 alpha gate 从 alpha>0 放宽至 alpha > ALPHA_GATE_THRESHOLD (-2%)，
 710→    允许小幅负 alpha 候选进入 ensemble。本函数仍用 max(a, 0.0) 作为权重下限，
 711→    意味着 ensemble 内负 alpha 策略权重仍为 0（被正 alpha 策略"覆盖"）。
 712→    这是保守设计：在多策略 ensemble 中，正 alpha 策略应主导权重；
 713→    单策略场景由 `len == 1` 早返回得到 weight=1.0。
 714→    若未来需要让小幅负 alpha 也贡献权重，可改为 `max(a - ALPHA_GATE_THRESHOLD, 0.0)`。
 715→
 716→    Args:
 717→        group_results: [(strategy, params, [SingleBacktestResult]), ...]
 718→        spy_returns:   SPY 日收益率序列（用于 alpha 计算）；None 时退化为等权
 719→        conflict_threshold: 加权投票分数绝对值低于此时视为 HOLD
 720→
 721→    Returns:
 722→        [(strategy, params, weight), ...] 归一化权重列表
 723→    """
 724→    if len(group_results) == 1:
 725→        strategy, params, _ = group_results[0]
 726→        return [(strategy, params, 1.0)]
 727→
 728→    # 迭代 #12：负 alpha 策略不参与 ensemble（experience.md #8：负分不能用 max(x, ε) 掩盖）
 729→    # 只有正 alpha 的策略参与归一化；负 alpha 策略权重为 0。
 730→    # 上游 _run_group 的 alpha gate（Iter #16: alpha > ALPHA_GATE_THRESHOLD=-2%）
 731→    # 应已拦截严重跑输的候选，这里是防御性设计：即使上游漏过负 alpha，
 732→    # 也不会被 max(0.01) 掩盖成等权。
 733→    raw_alphas = []
 734→    for strategy, params, results in group_results:
 735→        combined = _combine_daily_returns(results)
 736→        alpha = _compute_alpha(combined, spy_returns)
 737→        raw_alphas.append(alpha)
 738→
 739→    # 负 alpha → 权重 0；正 alpha → 参与归一化
 740→    positive_alphas = [max(a, 0.0) for a in raw_alphas]
 741→    total = sum(positive_alphas)
 742→
 743→    if total > 0:
 744→        weights = [a / total for a in positive_alphas]
 745→    else:
 746→        # 防御性 fallback：全负 alpha 或全零时等权
 747→        # （上游 alpha gate 应已拦截，此处不应到达）
 748→        n = len(group_results)
 749→        weights = [1.0 / n] * n if n > 0 else []
 750→        logger.warning(
 751→            f"[ensemble_weights] all alphas <= 0 ({raw_alphas}), "
 752→            f"falling back to equal weight. This should not happen if "
 753→            f"alpha gate (threshold={ALPHA_GATE_THRESHOLD}%) is active upstream."
 754→        )
 755→
 756→    return [
 757→        (strategy, params, weight)
 758→        for (strategy, params, _), weight in zip(group_results, weights)
 759→    ]
 760→
 761→
 762→# ---------------------------------------------------------------------------
 763→# Walk-Forward 验证（迭代 #3 新增，Constitution L7 验证流水线）
 764→# ---------------------------------------------------------------------------
 765→
 766→def _add_months(d: date, months: int) -> date:
 767→    """对 date 加/减 months 个月，自动 clamp 到月末。
 768→
 769→    使用 pandas DateOffset 以避免引入 dateutil 依赖（pandas 已是核心依赖）。
 770→    """
 771→    return (pd.Timestamp(d) + pd.DateOffset(months=months)).date()
 772→
 773→
 774→def _backtest_with_params_on_period(
 775→    mb: "MatrixBacktest",
 776→    symbols: list[str],
 777→    weights: list[dict[str, Any]],
 778→    start: date,
 779→    end: date,
 780→) -> list[pd.Series]:
 781→    """用给定权重配置在 [start, end] 期间回测，返回每条 (策略×标的) 的日收益率序列。
 782→
 783→    用于 Walk-Forward 验证期：用训练期产出的 best params 在验证期回测，
 784→    不再做参数搜索。返回原始日收益率列表，由调用方聚合为整体 portfolio。
 785→
 786→    迭代 #10 变更：用 `_backtest_batch` 替代 for-symbol 循环，
 787→    每个策略×参数组合一次 vbt 调用，加速 Walk-Forward 验证期回测。
 788→
 789→    Args:
 790→        mb:       MatrixBacktest 实例（复用其 store/init_cash/fees/slippage）
 791→        symbols:  该组的标的列表
 792→        weights:  训练期产出的权重配置（list of dict，含 strategy/params/weight）
 793→        start:    验证期起始日期
 794→        end:      验证期结束日期
 795→
 796→    Returns:
 797→        list[pd.Series] — 每条 (strategy×symbol) 的日收益率；空列表表示无有效数据
 798→    """
 799→    if not weights or not symbols:
 800→        return []
 801→
 802→    data = mb._store.get_bars_multi(symbols, start, end)
 803→    if not data:
 804→        return []
 805→
 806→    all_returns: list[pd.Series] = []
 807→    for w in weights:
 808→        strategy = w.get("strategy", "")
 809→        params = w.get("params", {})
 810→        if not strategy or strategy not in STRATEGY_REGISTRY:
 811→            continue
 812→        # 迭代 #10：一次 batch 调用处理组内所有标的
 813→        results = _backtest_batch(
 814→            data, strategy, params,
 815→            mb._init_cash, mb._fees, mb._slippage,
 816→        )
 817→        for r in results:
 818→            if not r.daily_returns.empty:
 819→                all_returns.append(r.daily_returns)
 820→    return all_returns
 821→
 822→
 823→def run_walk_forward(
 824→    mb: "MatrixBacktest",
 825→    strategies: list[str],
 826→    param_grids: dict[str, dict[str, list]],
 827→    rounds: int = 4,
 828→    train_months: int = 18,
 829→    val_months: int = 6,
 830→) -> WalkForwardReport:
 831→    """执行 N 轮 Walk-Forward 验证（Constitution L7 验证流水线硬要求）。
 832→
 833→    每轮流程：
 834→        1. 训练期 [train_start, train_end]：跑矩阵回测找最优参数
 835→        2. 验证期 [val_start, val_end]：用同参数回测，记录 portfolio Sortino 和 max DD
 836→        3. passed = val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD (15%)
 837→
 838→    时间窗口（动态计算，today=today）：
 839→        - 最后一轮 val_end = today - val_months（留 1 个 val 期给 paper trading）
 840→        - 每轮向前推 val_months
 841→        - train_end = val_start，train_start = train_end - train_months
 842→
 843→    默认参数 (rounds=4, train_months=18, val_months=6) 对应用户提供的固定窗口：
 844→        today=2026-07-01 →
 845→        Round 1: train 2021-07-02~2023-01-02, val 2023-01-02~2023-07-02
 846→        Round 2: train 2022-01-02~2023-07-02, val 2023-07-02~2024-01-02
 847→        Round 3: train 2022-07-02~2024-01-02, val 2024-01-02~2024-07-02
 848→        Round 4: train 2023-01-02~2024-07-02, val 2024-07-02~2025-01-02
 849→
 850→    Args:
 851→        mb:            MatrixBacktest 实例（复用其 store/universe/init_cash 等）
 852→        strategies:    策略名称列表
 853→        param_grids:   参数网格（与 mb.run() 接收的格式一致）
 854→        rounds:        轮次数（默认 4，Constitution L7 要求）
 855→        train_months:  训练期月数（默认 18）
 856→        val_months:    验证期月数（默认 6）
 857→
 858→    Returns:
 859→        WalkForwardReport — 包含每轮结果、pass_all_rounds、max_val_dd
 860→
 861→    Note:
 862→        - WF 是验证步骤，不修改 strategy_weights.json
 863→        - 失败轮次会记录 WARNING 但不抛异常
 864→        - 全部 4 轮通过是进入 paper trading 的前置条件
 865→    """
 866→    today = date.today()
 867→    groups = mb._universe.get_groups()
 868→    if not groups:
 869→        logger.warning("[WalkForward] no groups available — skipping")
 870→        return WalkForwardReport()
 871→
 872→    wf_rounds: list[WalkForwardRound] = []
 873→
 874→    for i in range(rounds):
 875→        round_num = i + 1
 876→        # 计算本轮时间窗口
 877→        # 最后一轮 (i=rounds-1) 的 val_end = today - val_months
 878→        # 前面轮次依次向前推 val_months
 879→        val_end = _add_months(today, -val_months - (rounds - round_num) * val_months)
 880→        val_start = _add_months(val_end, -val_months)
 881→        train_end = val_start
 882→        train_start = _add_months(train_end, -train_months)
 883→
 884→        logger.info(
 885→            f"[WalkForward] Round {round_num}/{rounds}: "
 886→            f"train={train_start}~{train_end}, val={val_start}~{val_end}"
 887→        )
 888→
 889→        # ── 训练期：跑矩阵回测找最优参数（复用 mb._run_group）──
 890→        train_report = MatrixBacktestReport(
 891→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
 892→            backtest_window=f"{train_start.isoformat()} ~ {train_end.isoformat()}",
 893→            groups={},
 894→        )
 895→
 896→        for group_id, symbols in groups.items():
 897→            weights = mb._run_group(
 898→                group_id=group_id,
 899→                symbols=symbols,
 900→                start=train_start,
 901→                end=train_end,
 902→                strategies=strategies,
 903→                param_grids=param_grids,
 904→                report=train_report,
 905→            )
 906→            train_report.groups[group_id] = weights
 907→
 908→        # ── 验证期：用训练期 best params 回测，聚合为整体 portfolio ──
 909→        all_returns: list[pd.Series] = []
 910→        for group_id, symbols in groups.items():
 911→            weights = train_report.groups.get(group_id, [])
 912→            if not weights:
 913→                continue
 914→            group_returns = _backtest_with_params_on_period(
 915→                mb, symbols, weights, val_start, val_end,
 916→            )
 917→            all_returns.extend(group_returns)
 918→
 919→        # 计算整体 portfolio 指标（等权合并所有组的日收益率）
 920→        if not all_returns:
 921→            val_sortino = 0.0
 922→            val_max_dd = 0.0
 923→            val_alpha = 0.0
 924→            logger.warning(
 925→                f"[WalkForward] Round {round_num}: no valid val returns — "
 926→                f"sortino=0, dd=0, alpha=0, passed=True (vacuous)"
 927→            )
 928→        else:
 929→            combined = pd.concat(all_returns, axis=1).mean(axis=1).dropna()
 930→            if len(combined) < 5:
 931→                val_sortino = 0.0
 932→                val_max_dd = 0.0
 933→                val_alpha = 0.0
 934→            else:
 935→                val_sortino = _compute_sortino(combined)
 936→                wrapper = [SingleBacktestResult(
 937→                    symbol="portfolio", strategy="", params={},
 938→                    sharpe=0.0, total_return_pct=0.0, max_drawdown_pct=0.0,
 939→                    win_rate_pct=0.0, total_trades=0, daily_returns=combined,
 940→                )]
 941→                val_max_dd = _portfolio_max_drawdown_from_results(wrapper)
 942→
 943→                # ── 迭代 #13：计算验证期 alpha vs SPY ──
 944→                # 与 matrix_backtest 的 alpha 选择目标一致（目标一致性修复）
 945→                # SPY 不可用时 alpha=0.0（与 _compute_alpha 的降级语义一致）
 946→                spy_val_returns = mb._get_spy_returns(val_start, val_end)
 947→                if spy_val_returns is not None:
 948→                    val_alpha = _compute_alpha(combined, spy_val_returns)
 949→                else:
 950→                    val_alpha = 0.0
 951→                    logger.warning(
 952→                        f"[WalkForward] Round {round_num}: SPY data unavailable for "
 953→                        f"val period {val_start}~{val_end} — val_alpha=0 (degraded)"
 954→                    )
 955→
 956→        # ── 迭代 #13：gate 加 alpha 校验 ──
 957→        # 单轮：DD ≤ 15% AND alpha > -5%（允许小幅跑输，不容忍灾难性跑输）
 958→        # 汇总（在 report 构建时）：all rounds passed AND avg_val_alpha > 0
 959→        dd_passed = val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD
 960→        alpha_passed = val_alpha > WALK_FORWARD_VAL_ALPHA_FLOOR
 961→        passed = dd_passed and alpha_passed
 962→        wf_rounds.append(WalkForwardRound(
 963→            round_num=round_num,
 964→            train_start=train_start,
 965→            train_end=train_end,
 966→            val_start=val_start,
 967→            val_end=val_end,
 968→            val_sortino=val_sortino,
 969→            val_max_dd=val_max_dd,
 970→            val_alpha=val_alpha,
 971→            passed=passed,
 972→        ))
 973→        logger.info(
 974→            f"[WalkForward] Round {round_num} result: "
 975→            f"sortino={val_sortino:.4f}, dd={val_max_dd:.4f}%, "
 976→            f"alpha={val_alpha:.4f}%, passed={passed} "
 977→            f"(dd_threshold={WALK_FORWARD_VAL_DD_THRESHOLD}%, "
 978→            f"alpha_floor={WALK_FORWARD_VAL_ALPHA_FLOOR}%)"
 979→        )
 980→
 981→    # ── 迭代 #13：汇总 alpha 聚合 + pass_all_rounds 加 avg alpha > 0 条件 ──
 982→    val_alphas = [r.val_alpha for r in wf_rounds]
 983→    avg_val_alpha = sum(val_alphas) / len(val_alphas) if val_alphas else 0.0
 984→    min_val_alpha = min(val_alphas) if val_alphas else 0.0
 985→
 986→    # 单轮全过 AND 平均 alpha > 0（OOS 平均必须跑赢 SPY）
 987→    all_rounds_passed = all(r.passed for r in wf_rounds) if wf_rounds else False
 988→    avg_alpha_positive = avg_val_alpha > 0
 989→    pass_all = all_rounds_passed and avg_alpha_positive
 990→
 991→    report = WalkForwardReport(
 992→        rounds=wf_rounds,
 993→        pass_all_rounds=pass_all,
 994→        max_val_dd=max((r.val_max_dd for r in wf_rounds), default=0.0),
 995→        avg_val_alpha=avg_val_alpha,
 996→        min_val_alpha=min_val_alpha,
 997→    )
 998→    logger.info(
 999→        f"[WalkForward] done: {len(wf_rounds)} rounds, "
1000→        f"pass_all_rounds={report.pass_all_rounds}, "
1001→        f"max_val_dd={report.max_val_dd:.4f}%, "
1002→        f"avg_val_alpha={report.avg_val_alpha:.4f}%, "
1003→        f"min_val_alpha={report.min_val_alpha:.4f}%"
1004→    )
1005→    return report
1006→
1007→
1008→# ---------------------------------------------------------------------------
1009→# MatrixBacktest 主类
1010→# ---------------------------------------------------------------------------
1011→
1012→class MatrixBacktest:
1013→    """矩阵回测：N 策略 × G 标的组 × 参数网格 → strategy_weights.json。
1014→
1015→    Args:
1016→        store:       MarketDataStore（本地时序库）
1017→        universe:    UniverseManager（提供分组映射）
1018→        years:       回测窗口（默认 5 年）
1019→        init_cash:   初始资金
1020→        fees:        手续费率
1021→        slippage:    滑点率
1022→        top_k:       每组保留 Top-K 策略（默认 2）
1023→    """
1024→
1025→    def __init__(
1026→        self,
1027→        store: MarketDataStore,
1028→        universe: UniverseManager,
1029→        years: int = 5,
1030→        init_cash: float = 100_000.0,
1031→        fees: float = 0.001,
1032→        slippage: float = 0.001,
1033→        top_k: int = 2,
1034→    ) -> None:
1035→        self._store = store
1036→        self._universe = universe
1037→        self._years = years
1038→        self._init_cash = init_cash
1039→        self._fees = fees
1040→        self._slippage = slippage
1041→        self._top_k = top_k
1042→
1043→    def run(
1044→        self,
1045→        strategies: list[str],
1046→        param_grids: dict[str, dict[str, list]],
1047→        output_file: str | Path | None = None,
1048→    ) -> MatrixBacktestReport:
1049→        """执行完整矩阵回测。
1050→
1051→        Args:
1052→            strategies:  策略名称列表，如 ["dual_ma", "rsi"]
1053→            param_grids: 各策略参数网格，如 {"dual_ma": {"fast":[5,10], "slow":[20,30]}}
1054→            output_file: strategy_weights.json 输出路径（None 则不写文件）
1055→
1056→        Returns:
1057→            MatrixBacktestReport
1058→        """
1059→        today = date.today()
1060→        start = today - timedelta(days=self._years * 365)
1061→        window_str = f"{start.isoformat()} ~ {today.isoformat()}"
1062→
1063→        logger.info(
1064→            f"[MatrixBacktest] start={start}, end={today}, "
1065→            f"strategies={strategies}, years={self._years}"
1066→        )
1067→
1068→        # 获取分组（⚠️ 使用历史时点分组，而非当前静态分组）
1069→        # Phase 5 初期简化：用当前分组，但接口已预留历史分组能力
1070→        groups = self._universe.get_groups()
1071→        if not groups:
1072→            logger.warning("[MatrixBacktest] no groups available, abort")
1073→            return MatrixBacktestReport(
1074→                generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
1075→                backtest_window=window_str,
1076→                groups={},
1077→            )
1078→
1079→        report = MatrixBacktestReport(
1080→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
1081→            backtest_window=window_str,
1082→            groups={},
1083→        )
1084→
1085→        for group_id, symbols in groups.items():
1086→            logger.info(
1087→                f"[MatrixBacktest] group={group_id}, symbols={len(symbols)}, "
1088→                f"strategies={strategies}"
1089→            )
1090→
1091→            group_weights = self._run_group(
1092→                group_id=group_id,
1093→                symbols=symbols,
1094→                start=start,
1095→                end=today,
1096→                strategies=strategies,
1097→                param_grids=param_grids,
1098→                report=report,
1099→            )
1100→            report.groups[group_id] = group_weights
1101→
1102→        if output_file is not None:
1103→            self._write_weights(report, output_file)
1104→
1105→        logger.info(
1106→            f"[MatrixBacktest] done: {len(report.groups)} groups, "
1107→            f"warnings={len(report.warnings)}"
1108→        )
1109→        return report
1110→
1111→    def _get_spy_returns(self, start: date, end: date) -> pd.Series | None:
1112→        """获取 SPY 同期日收益率序列，用于计算 alpha（迭代 #9 新增）。
1113→
1114→        从 MarketDataStore 拉取 SPY 日线数据，计算日收益率。
1115→        SPY 不在标的池中，但作为 benchmark 用于 alpha 计算。
1116→
1117→        降级处理：SPY 数据不可用时返回 None（_compute_alpha 会返回 0.0），
1118→        不抛异常，保证回测不因 benchmark 缺失而阻塞。
1119→
1120→        Args:
1121→            start: 回测起始日期
1122→            end:   回测结束日期
1123→
1124→        Returns:
1125→            SPY 日收益率 pd.Series；数据不可用时返回 None
1126→        """
1127→        try:
1128→            spy_bars = self._store.get_bars_multi(["SPY"], start, end)
1129→            spy_df = spy_bars.get("SPY") if spy_bars else None
1130→            if spy_df is None or spy_df.empty:
1131→                logger.warning(
1132→                    "[MatrixBacktest] SPY data unavailable, alpha will degrade to 0.0"
1133→                )
1134→                return None
1135→            spy_close = spy_df["close"].astype(float)
1136→            if len(spy_close) < 2:
1137→                logger.warning(
1138→                    "[MatrixBacktest] SPY data too short, alpha will degrade to 0.0"
1139→                )
1140→                return None
1141→            return spy_close.pct_change().dropna()
1142→        except Exception as e:
1143→            logger.warning(
1144→                f"[MatrixBacktest] SPY benchmark fetch failed: {e} — "
1145→                f"alpha will degrade to 0.0"
1146→            )
1147→            return None
1148→
1149→    def _run_group(
1150→        self,
1151→        group_id: str,
1152→        symbols: list[str],
1153→        start: date,
1154→        end: date,
1155→        strategies: list[str],
1156→        param_grids: dict[str, dict[str, list]],
1157→        report: MatrixBacktestReport,
1158→    ) -> list[dict[str, Any]]:
1159→        """对单个分组执行策略 × 参数网格回测，返回该组的权重配置列表。
1160→
1161→        迭代 #9 变更：
1162→            - per-strategy best params：从 Sharpe 改为 Alpha（vs SPY）
1163→            - top-K 排序：从 Sortino 改为 Alpha
1164→            - 新增 Sortino > 0.5 最低质量门槛（二级过滤，可放宽）
1165→            - ensemble weights：从 Sharpe 改为 Alpha
1166→        迭代 #10 变更：
1167→            - 用 `_backtest_batch` 替代 for-symbol 循环（10-20x 提速）
1168→            - 每组 / 每策略增加进度耗时日志
1169→        """
1170→        import time
1171→
1172→        group_start = time.time()
1173→
1174→        # 1. 读取组内所有标的数据
1175→        data = self._store.get_bars_multi(symbols, start, end)
1176→        if not data:
1177→            logger.warning(f"[MatrixBacktest] {group_id}: no data, skip")
1178→            return []
1179→
1180→        # 迭代 #9：获取 SPY 同期日收益率用于 alpha 计算（一次获取，组内复用）
1181→        spy_returns = self._get_spy_returns(start, end)
1182→
1183→        valid_symbol_count = sum(
1184→            1 for df in data.values() if df is not None and not df.empty and len(df) >= 30
1185→        )
1186→        logger.info(
1187→            f"[MatrixBacktest] {group_id}: start — "
1188→            f"{len(strategies)} strategies × {valid_symbol_count} valid symbols"
1189→        )
1190→
1191→        # 2. 对每个策略 × 每组参数，按 alpha 选最优参数
1192→        group_results: list[tuple[str, dict, list[SingleBacktestResult]]] = []
1193→
1194→        for strategy in strategies:
1195→            strat_start = time.time()
1196→
1197→            # ⚠️ 早期检测未注册策略名（迭代 #1 修复"策略名拼写错误被静默跳过"的 bug）
1198→            # 之前 _backtest_one 内部静默 return None，导致 main.py 误用 "rsi"/"macd"/"bollinger"
1199→            # 简称 6 天未被发现。改为 WARNING 级日志 + continue。
1200→            if strategy not in STRATEGY_REGISTRY:
1201→                logger.warning(
1202→                    f"[MatrixBacktest] {group_id}: strategy '{strategy}' not in "
1203→                    f"STRATEGY_REGISTRY — skipped. "
1204→                    f"Check spelling against @register_strategy decorators. "
1205→                    f"Known: {sorted(STRATEGY_REGISTRY.keys())}"
1206→                )
1207→                continue
1208→            grid = param_grids.get(strategy, {})
1209→            param_combos = list(
1210→                dict(zip(grid.keys(), combo))
1211→                for combo in itertools.product(*grid.values())
1212→            ) if grid else [{}]
1213→
1214→            best_params = None
1215→            best_alpha = float("-inf")
1216→            best_sharpe = 0.0       # 仅用于 GroupBacktestResult 存档
1217→            best_sortino = 0.0      # 仅用于 GroupBacktestResult 存档
1218→            best_results: list[SingleBacktestResult] = []
1219→
1220→            for params in param_combos:
1221→                # 迭代 #10：用 _backtest_batch 一次处理组内所有标的
1222→                # 替代原 for sym in symbols: _backtest_one(...) 的逐标的循环
1223→                results = _backtest_batch(
1224→                    data, strategy, params,
1225→                    self._init_cash, self._fees, self._slippage,
1226→                )
1227→
1228→                if not results:
1229→                    continue
1230→
1231→                # ⚠️ 等权合并日收益率序列，一次性计算所有指标
1232→                # 迭代 #9：复用 combined 计算 sharpe / sortino / alpha
1233→                combined = _combine_daily_returns(results)
1234→                ps = _compute_sharpe(combined)
1235→                pso = _compute_sortino(combined)
1236→                alpha = _compute_alpha(combined, spy_returns)
1237→
1238→                # 迭代 #9：per-strategy best params 用 alpha 选（替代 Sharpe）
1239→                if alpha > best_alpha:
1240→                    best_alpha = alpha
1241→                    best_sharpe = ps
1242→                    best_sortino = pso
1243→                    best_params = params
1244→                    best_results = results
1245→
1246→            if best_params is not None and best_results:
1247→                group_results.append((strategy, best_params, best_results))
1248→                report.group_results.append(GroupBacktestResult(
1249→                    group_id=group_id,
1250→                    strategy=strategy,
1251→                    params=best_params,
1252→                    portfolio_sharpe=best_sharpe,
1253→                    avg_total_return_pct=_safe_mean(
1254→                        [r.total_return_pct for r in best_results]
1255→                    ),
1256→                    avg_max_drawdown_pct=_safe_mean(
1257→                        [r.max_drawdown_pct for r in best_results]
1258→                    ),
1259→                    avg_win_rate_pct=_safe_mean(
1260→                        [r.win_rate_pct for r in best_results]
1261→                    ),
1262→                    symbol_count=len(best_results),
1263→                    portfolio_sortino=best_sortino,
1264→                    portfolio_max_drawdown=_portfolio_max_drawdown_from_results(
1265→                        best_results
1266→                    ),
1267→                    backtest_alpha=best_alpha,
1268→                ))
1269→
1270→            logger.info(
1271→                f"[MatrixBacktest] {group_id}: {strategy} done in "
1272→                f"{time.time() - strat_start:.1f}s "
1273→                f"({len(param_combos)} param combos × {valid_symbol_count} symbols)"
1274→            )
1275→
1276→        if not group_results:
1277→            logger.warning(
1278→                f"[MatrixBacktest] {group_id}: no valid results "
1279→                f"(elapsed {time.time() - group_start:.1f}s)"
1280→            )
1281→            return []
1282→
1283→        # 迭代 #11：健全性过滤 —— 排序前先剔除退化策略
1284→        # （experience.md #8：sanity → risk → rank）
1285→        # 退化策略 = 组内 ≥ 80% 标的 closed_trades==0（入场/出场条件互斥，
1286→        # 仓位靠末尾强平凑出 Sortino/alpha 假象）。此类策略必须先于 DD/Sortino/
1287→        # Alpha 过滤剔除，否则其盯市假象会骗过 alpha 排序进入权重。
1288→        sane_results: list[tuple[str, dict, list[SingleBacktestResult]]] = []
1289→        for (strategy, params, results) in group_results:
1290→            if _is_degenerate_strategy(results):
1291→                logger.warning(
1292→                    f"[MatrixBacktest] {group_id}: strategy '{strategy}' is DEGENERATE "
1293→                    f"(>= {DEGENERATE_NO_CLOSE_FRACTION:.0%} symbols have 0 closed trades) "
1294→                    f"— excluded before ranking. Its Sortino/alpha is mark-to-market illusion."
1295→                )
1296→                continue
1297→            sane_results.append((strategy, params, results))
1298→
1299→        if not sane_results:
1300→            # 全组退化 → 空权重（持仓现金），标记 no_valid_strategy，不强行选退化策略
1301→            logger.warning(
1302→                f"[MatrixBacktest] {group_id}: ALL strategies degenerate — "
1303→                f"group produces EMPTY weights (hold cash). Marked no_valid_strategy."
1304→            )
1305→            report.warnings.append(
1306→                f"{group_id}: no_valid_strategy (all strategies degenerate)"
1307→            )
1308→            # 标记已 append 的 GroupBacktestResult 条目（供审计追溯）
1309→            for gr in report.group_results:
1310→                if gr.group_id == group_id:
1311→                    gr.no_valid_strategy = True
1312→            return []
1313→
1314→        # 后续 candidates 构建、DD/Sortino/Alpha 过滤、排序，全部改用 sane_results
1315→        group_results = sane_results
1316→
1317→        # 3. 迭代 #9：DD 硬约束 + Sortino 门槛 + Alpha 排序选 Top-K
1318→        #    Constitution L1: portfolio DD ≤ 20% 是硬约束（保留）
1319→        #    新增：Sortino > 0.5 最低质量门槛（可放宽）
1320→        #    变更：排序指标从 Sortino 改为 Alpha
1321→        #
1322→        #    三级过滤策略：
1323→        #      Tier 1: DD ≤ 20% AND Sortino > 0.5 → Alpha 降序
1324→        #      Tier 2 (fallback): Tier 1 为空 → 仅 DD ≤ 20% → Alpha 降序
1325→        #      Tier 3 (fallback): Tier 2 为空 → 按 DD 升序，标记 dd_constrained=True
1326→        candidates: list[
1327→            tuple[str, dict, list[SingleBacktestResult], float, float, float]
1328→        ] = []
1329→        for (strategy, params, results) in group_results:
1330→            pso = _portfolio_sortino_from_results(results)
1331→            pdd = _portfolio_max_drawdown_from_results(results)
1332→            # 复用 _combine_daily_returns 计算 alpha（与 per-strategy 选择一致）
1333→            alpha = _compute_alpha(_combine_daily_returns(results), spy_returns)
1334→            candidates.append((strategy, params, results, pso, pdd, alpha))
1335→
1336→        # 迭代 #12：alpha 硬门槛（experience.md #8：正超额是排序前的硬门槛）
1337→        # 迭代 #16：阈值从 alpha>0 放宽至 alpha > ALPHA_GATE_THRESHOLD (-2%)。
1338→        #   动机：SPX 成分股 vs SPY 存在结构性近零 alpha，严格 alpha>0 门槛导致
1339→        #   4/6 组空仓（Iter #15 reoptimize 实证）。-2% 仍过滤"灾难性跑输"，
1340→        #   同时保留"小幅跑输 SPY 但 Sortino/DD 优秀"的候选。
1341→        #   Walk-Forward（Iter #13）仍用 -5% 单轮下限 + avg>0 汇总门槛作 OOS 校验，
1342→        #   放宽 in-sample gate 不削弱 OOS 验证强度。
1343→        # 顺序：健全性（Iter #11）→ 风险（DD，Tier 1/2/3）→ alpha 门槛（本步）→ 排序
1344→        #
1345→        # 注意：这一步在 candidates 构建后、Tier 1 前，确保 Tier 1/2/3 只在合格 alpha 候选中进行。
1346→        # 如果某组所有候选 alpha ≤ ALPHA_GATE_THRESHOLD，该组空仓（hold cash），
1347→        # 不强行选严重跑输 SPY 的策略
1348→        # （experience.md #8："没有候选满足门槛时，正确动作是空仓/降现金/回退 benchmark，
1349→        #   不是矬子里拔将军"）。
1350→        alpha_qualified_candidates = [
1351→            c for c in candidates if c[5] > ALPHA_GATE_THRESHOLD
1352→        ]
1353→
1354→        if not alpha_qualified_candidates:
1355→            # 全组 alpha ≤ threshold → 空权重（持仓现金），标记 no_positive_alpha
1356→            # 字段名保留 no_positive_alpha（向下兼容下游消费方），语义为"无合格 alpha 候选"
1357→            alpha_strs = [f"{c[0]}({c[5]:.2f}%)" for c in candidates]
1358→            logger.warning(
1359→                f"[MatrixBacktest] {group_id}: ALL {len(candidates)} candidates have "
1360→                f"alpha <= {ALPHA_GATE_THRESHOLD}% (cannot beat SPY within tolerance) — "
1361→                f"{alpha_strs}. "
1362→                f"Group produces EMPTY weights (hold cash). Marked no_positive_alpha."
1363→            )
1364→            report.warnings.append(
1365→                f"{group_id}: no_positive_alpha "
1366→                f"(all {len(candidates)} candidates alpha <= {ALPHA_GATE_THRESHOLD}%)"
1367→            )
1368→            # 标记已 append 的 GroupBacktestResult 条目（供审计追溯）
1369→            for gr in report.group_results:
1370→                if gr.group_id == group_id:
1371→                    gr.no_positive_alpha = True
1372→            return []
1373→
1374→        # 后续 Tier 1/2/3 在合格 alpha 候选中进行
1375→        candidates = alpha_qualified_candidates
1376→
1377→        # Tier 1: DD ≤ 20% AND Sortino > 0.5
1378→        compliant = [
1379→            c for c in candidates
1380→            if c[4] <= MAX_PORTFOLIO_DRAWDOWN_PCT and c[3] > MIN_SORTINO_THRESHOLD
1381→        ]
1382→        if compliant:
1383→            # Tier 1 命中：按 Alpha 降序取 top-K
1384→            ranked = sorted(compliant, key=lambda x: x[5], reverse=True)
1385→            dd_constrained = False
1386→            logger.info(
1387→                f"[MatrixBacktest] {group_id}: DD + Sortino filter passed — "
1388→                f"{len(compliant)}/{len(candidates)} candidates compliant "
1389→                f"(DD <= {MAX_PORTFOLIO_DRAWDOWN_PCT}% AND Sortino > {MIN_SORTINO_THRESHOLD})"
1390→            )
1391→        else:
1392→            # Tier 2: 放宽 Sortino 门槛，仅保留 DD 约束
1393→            dd_compliant = [
1394→                c for c in candidates if c[4] <= MAX_PORTFOLIO_DRAWDOWN_PCT
1395→            ]
1396→            if dd_compliant:
1397→                # Tier 2 命中：按 Alpha 降序取 top-K（dd_constrained 仍为 False）
1398→                ranked = sorted(dd_compliant, key=lambda x: x[5], reverse=True)
1399→                dd_constrained = False
1400→                logger.warning(
1401→                    f"[MatrixBacktest] {group_id}: Sortino filter relaxed — "
1402→                    f"no candidate passed Sortino > {MIN_SORTINO_THRESHOLD}. "
1403→                    f"Fallback to DD-only filter: "
1404→                    f"{len(dd_compliant)}/{len(candidates)} candidates DD-compliant."
1405→                )
1406→            else:
1407→                # Tier 3: 无 DD 合规候选 → 按 DD 升序，标记 dd_constrained
1408→                # （结构性问题，如 NDX_high_vol 全部 > 20%）
1409→                ranked = sorted(candidates, key=lambda x: x[4])
1410→                dd_constrained = True
1411→                logger.warning(
1412→                    f"[MatrixBacktest] {group_id}: NO compliant candidates "
1413→                    f"(all {len(candidates)} exceed DD={MAX_PORTFOLIO_DRAWDOWN_PCT}%). "
1414→                    f"Fallback: selected top-{self._top_k} by lowest DD. "
1415→                    f"This group is marked dd_constrained=True — "
1416→                    f"review whether to drop the group or accept the risk."
1417→                )
1418→                report.warnings.append(
1419→                    f"{group_id}: dd_constrained=True "
1420→                    f"(min DD={ranked[0][4]:.2f}% > {MAX_PORTFOLIO_DRAWDOWN_PCT}%)"
1421→                )
1422→
1423→        top_results = ranked[: self._top_k]
1424→
1425→        # 把 dd_constrained 标记同步到 report.group_results 中对应组的条目
1426→        for gr in report.group_results:
1427→            if gr.group_id == group_id:
1428→                gr.dd_constrained = dd_constrained
1429→
1430→        # 4. 优化 ensemble 权重（单点离散值加权投票语义，迭代 #9 改用 alpha）
1431→        weighted = _optimize_ensemble_weights(
1432→            [(s, p, r) for (s, p, r, _, _, _) in top_results],
1433→            spy_returns=spy_returns,
1434→        )
1435→
1436→        # 5. 构建权重配置列表
1437→        weights_list = []
1438→        for strategy, params, weight in weighted:
1439→            # 找到对应的 GroupBacktestResult
1440→            gr = next(
1441→                (r for r in report.group_results
1442→                 if r.group_id == group_id and r.strategy == strategy),
1443→                None,
1444→            )
1445→            # 迭代 #4：新增 backtest_dd_status 字段（'pass' / 'dd_constrained'）
1446→            # 作为风险 metadata 标记，与 dd_constrained bool 同义但更可读
1447→            backtest_dd_status = "dd_constrained" if dd_constrained else "pass"
1448→            weights_list.append({
1449→                "strategy": strategy,
1450→                "params": params,
1451→                "weight": round(weight, 4),
1452→                "backtest_sharpe": round(gr.portfolio_sharpe if gr else 0.0, 4),
1453→                "backtest_sortino": round(gr.portfolio_sortino if gr else 0.0, 4),
1454→                "backtest_max_drawdown": round(gr.portfolio_max_drawdown if gr else 0.0, 4),
1455→                "backtest_win_rate": round(gr.avg_win_rate_pct / 100 if gr else 0.5, 4),
1456→                # 迭代 #9：新增 backtest_alpha 字段（vs SPY 的超额收益百分数）
1457→                # 下游 PortfolioBacktester 可读此字段验证 alpha 一致性
1458→                "backtest_alpha": round(gr.backtest_alpha if gr else 0.0, 4),
1459→                # 迭代 #3：标记该组是否用了 DD fallback（无合规候选）
1460→                # 同组所有策略条目共享同一 dd_constrained 值
1461→                "dd_constrained": dd_constrained,
1462→                # 迭代 #4：backtest_dd_status — 风险 metadata 字段
1463→                # 'pass' = 该组有合规候选（DD ≤ 20%）
1464→                # 'dd_constrained' = fallback 触发（无合规候选，按最低 DD 取 top-K）
1465→                # 下游消费方（PortfolioBacktester / 风控观测）可读此字段判断
1466→                # 该组权重的可靠性，作为风险信号标记
1467→                "backtest_dd_status": backtest_dd_status,
1468→            })
1469→
1470→        logger.info(
1471→            f"[MatrixBacktest] {group_id}: all strategies done in "
1472→            f"{time.time() - group_start:.1f}s "
1473→            f"(top-{self._top_k} selected, dd_constrained={dd_constrained})"
1474→        )
1475→
1476→        return weights_list
1477→
1478→    def _write_weights(
1479→        self, report: MatrixBacktestReport, output_file: str | Path
1480→    ) -> None:
1481→        """将矩阵回测结果写入 strategy_weights.json。"""
1482→        output_file = Path(output_file)
1483→        output_file.parent.mkdir(parents=True, exist_ok=True)
1484→
1485→        data = {
1486→            "_meta": {
1487→                "generated_at": report.generated_at,
1488→                "backtest_window": report.backtest_window,
1489→                "reoptimize_freq": "monthly",
1490→                "survivorship_bias_warning": (
1491→                    "使用当前成分股回测，S&P 500 5年成分变动约100只(~20%)，"
1492→                    "均值回归组(SPX_low_vol)结果可能系统性偏高"
1493→                ),
1494→            },
1495→            "groups": report.groups,
1496→        }
1497→
1498→        with open(output_file, "w", encoding="utf-8") as f:
1499→            json.dump(data, f, indent=2, ensure_ascii=False)
1500→
1501→        logger.info(f"[MatrixBacktest] weights saved to {output_file}")
1502→
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
  43→# 迭代 #13 新增：WF 验证期 alpha 单轮下限（百分数）
  44→# 单轮允许小幅跑输 SPY（alpha > -5%），但 4 轮平均必须跑赢（avg > 0）
  45→# 设计动机：WF 与 matrix_backtest 目标一致性——matrix_backtest 用 alpha 选策略，
  46→# WF 也必须校验 alpha，否则 WF 通过 ≠ 跑赢 SPY
  47→# （Iter #11 实证：WF 4/4 pass 但组合 alpha=-21%，因为 WF gate 只校验 DD 不校验 alpha）
  48→# 详见 experience.md #8："验收 gate 必须校验跑赢 benchmark（正 alpha）"
  49→WALK_FORWARD_VAL_ALPHA_FLOOR: float = -5.0
  50→
  51→# 迭代 #9 新增：Sortino 最低质量门槛，用于 top-K 选择时的二级过滤
  52→# 排除 Sortino ≤ 0.5 的"垃圾"策略（即使 alpha 高也不选）
  53→# 设计动机：alpha 排序选出高绝对收益策略，但需 Sortino 门槛保证基本下行质量
  54→# fallback：若无候选通过此门槛，放宽过滤（仅保留 DD 硬约束）
  55→MIN_SORTINO_THRESHOLD: float = 0.5
  56→
  57→# 迭代 #16 新增：alpha gate 门槛（in-sample），用于 _run_group 排序前的硬门槛。
  58→# Iter #12 原值为 0（alpha>0 才入选），Iter #16 放宽至 -2%。
  59→# 设计动机：SPX 成分股 vs SPY benchmark 存在结构性近零 alpha —— SPY 即 S&P 500
  60→# 本身，交易 SPX 组件 vs SPY 相当于"和自己赛跑"。alpha=-1%（小幅跑输 SPY）的
  61→# 策略仍可能有出色的 Sortino / DD，不应被一刀切拒绝。
  62→# 与 WF OOS 校验的关系：Walk-Forward（Iter #13）仍用 -5% 单轮下限 + avg>0 汇总
  63→# 门槛，放宽 in-sample gate 不会削弱 OOS 验证强度。
  64→# 取 -2% 的理由：足以过滤"灾难性跑输"（如 -5% 以下），但保留"小幅跑输"的
  65→# 合理候选；阈值与 WALK_FORWARD_VAL_ALPHA_FLOOR=-5% 形成 3% 缓冲带。
  66→ALPHA_GATE_THRESHOLD: float = -2.0
  67→
  68→# 迭代 #11 新增：健全性门槛 —— 识别"退化策略"（几乎不平仓的伪 buy-and-hold）
  69→# 判定：组内"有效标的中，已平仓交易数为 0 的比例"超过此阈值 → 退化
  70→# 设计动机：真策略应在多数标的上完成买卖闭环；若近乎所有标的都从不平仓，
  71→#           说明入场/出场条件矛盾（如 Iter #8 rsi_trend_filter），其收益只是
  72→#           持仓盯市 + 末尾强平的假象，必须在排序前剔除（experience.md #8）。
  73→# 阈值取 0.8（保守）：只在"近乎全部标的零平仓"时触发，避免误伤低频合法策略。
  74→DEGENERATE_NO_CLOSE_FRACTION: float = 0.8
  75→
  76→
  77→# ---------------------------------------------------------------------------
  78→# 数据结构
  79→# ---------------------------------------------------------------------------
  80→
  81→@dataclass
  82→class SingleBacktestResult:
  83→    """单只标的单策略回测结果。"""
  84→
  85→    symbol: str
  86→    strategy: str
  87→    params: dict
  88→    sharpe: float
  89→    total_return_pct: float
  90→    max_drawdown_pct: float
  91→    win_rate_pct: float
  92→    total_trades: int
  93→    daily_returns: pd.Series    # pf.returns() — 供组合 Sharpe / Sortino 计算
  94→    sortino: float = 0.0       # Constitution L1 首要 KPI（迭代 #1 新增）
  95→    closed_trades: int = 0     # 迭代 #11 新增：已平仓交易数（区分退化 buy-and-hold）
  96→
  97→
  98→@dataclass
  99→class GroupBacktestResult:
 100→    """单组策略回测结果。"""
 101→
 102→    group_id: str
 103→    strategy: str
 104→    params: dict
 105→    portfolio_sharpe: float          # 等权组合 Sharpe（而非算术平均）
 106→    avg_total_return_pct: float
 107→    avg_max_drawdown_pct: float
 108→    avg_win_rate_pct: float
 109→    symbol_count: int
 110→    portfolio_sortino: float = 0.0          # 等权组合 Sortino（迭代 #1 新增）
 111→    portfolio_max_drawdown: float = 0.0     # 等权组合最大回撤（迭代 #2 新增，Constitution L1 KPI）
 112→    dd_constrained: bool = False            # 迭代 #3：该组是否用了 DD fallback（无合规候选）
 113→    backtest_alpha: float = 0.0              # 迭代 #9：alpha vs SPY（百分数），用于排序策略选择
 114→    no_valid_strategy: bool = False         # 迭代 #11：该组是否因全退化而空仓（hold cash）
 115→    no_positive_alpha: bool = False         # 迭代 #12：该组是否因全负 alpha 而空仓（hold cash）
 116→
 117→
 118→@dataclass
 119→class MatrixBacktestReport:
 120→    """整个矩阵回测的汇总报告。"""
 121→
 122→    generated_at: str
 123→    backtest_window: str
 124→    groups: dict[str, list[dict]]   # group_id → [策略权重配置]
 125→    group_results: list[GroupBacktestResult] = field(default_factory=list)
 126→    warnings: list[str] = field(default_factory=list)
 127→
 128→
 129→# ---------------------------------------------------------------------------
 130→# Walk-Forward 数据结构（迭代 #3 新增，Constitution L7 验证流水线）
 131→# ---------------------------------------------------------------------------
 132→
 133→@dataclass
 134→class WalkForwardRound:
 135→    """单轮 Walk-Forward 验证结果。
 136→
 137→    一轮 = 训练期（找最优参数）+ 验证期（用同参数回测，记录样本外指标）。
 138→
 139→    Attributes:
 140→        round_num:    轮次编号（1-indexed）
 141→        train_start:  训练期起始日期（含）
 142→        train_end:    训练期结束日期（含）
 143→        val_start:    验证期起始日期（含）
 144→        val_end:      验证期结束日期（含）
 145→        val_sortino:  验证期等权组合 Sortino Ratio（年化）
 146→        val_max_dd:   验证期等权组合最大回撤（正值百分数，0~100）
 147→        val_alpha:    验证期等权组合 alpha vs SPY（百分数，迭代 #13 新增）
 148→                      与 matrix_backtest 的 alpha 选择目标一致（目标一致性修复）
 149→        passed:       是否通过 = val_max_dd <= 15% AND val_alpha > -5%
 150→    """
 151→
 152→    round_num: int
 153→    train_start: date
 154→    train_end: date
 155→    val_start: date
 156→    val_end: date
 157→    val_sortino: float
 158→    val_max_dd: float
 159→    passed: bool
 160→    # 迭代 #13：验证期 portfolio alpha vs SPY（百分数）
 161→    # 放在 passed 之后以保持与现有位置参数调用的向后兼容
 162→    # （现有测试用 8 个位置参数：round_num...passed）
 163→    val_alpha: float = 0.0
 164→
 165→
 166→@dataclass
 167→class WalkForwardReport:
 168→    """Walk-Forward 4 轮验证汇总报告。
 169→
 170→    Constitution L7 要求 Backtest(>=5年) → Walk-Forward(4轮) → Paper → Live。
 171→    本报告是 Walk-Forward 阶段的产出。
 172→
 173→    Attributes:
 174→        rounds:         每轮结果列表（长度通常为 4）
 175→        pass_all_rounds: 是否所有轮都通过 AND avg_val_alpha > 0
 176→                         （迭代 #13：加 avg alpha > 0 条件，要求 OOS 平均跑赢 SPY）
 177→        max_val_dd:     所有轮中最大的验证期 DD（用于风险监控）
 178→        avg_val_alpha:  所有轮验证期 alpha 的平均值（迭代 #13 新增，百分数）
 179→        min_val_alpha:  所有轮中最差的验证期 alpha（迭代 #13 新增，百分数）
 180→    """
 181→
 182→    rounds: list[WalkForwardRound] = field(default_factory=list)
 183→    pass_all_rounds: bool = False
 184→    max_val_dd: float = 0.0
 185→    avg_val_alpha: float = 0.0   # 迭代 #13：4 轮平均验证期 alpha（百分数）
 186→    min_val_alpha: float = 0.0   # 迭代 #13：4 轮中最差的验证期 alpha（百分数）
 187→
 188→
 189→# ---------------------------------------------------------------------------
 190→# 核心函数
 191→# ---------------------------------------------------------------------------
 192→
 193→def _safe_float(value: Any, default: float = 0.0) -> float:
 194→    """NaN/None/非数值安全转 float（迭代 #2 新增）。
 195→
 196→    问题背景：vectorbt 在无交易场景下，`pf.stats()` 的 Win Rate / Sharpe 等
 197→    字段会返回 NaN。`float(NaN or 0.0)` 仍是 NaN（NaN 是 truthy），导致
 198→    JSON 序列化写出非法 JSON（NaN/Infinity 非 JSON 规范）。
 199→
 200→    处理顺序：
 201→        1. None → default
 202→        2. 数值类型但 NaN/Inf → default
 203→        3. 非数值（字符串等）尝试 float() 转换，失败 → default
 204→    """
 205→    if value is None:
 206→        return default
 207→    try:
 208→        f = float(value)
 209→    except (TypeError, ValueError):
 210→        return default
 211→    if not np.isfinite(f):   # 拦截 NaN / +Inf / -Inf
 212→        return default
 213→    return f
 214→
 215→
 216→def _safe_mean(values: Any, default: float = 0.0) -> float:
 217→    """空列表 / 全 NaN 安全的均值（迭代 #2 新增）。
 218→
 219→    问题背景：`np.mean([])` 会触发 RuntimeWarning 并返回 NaN；
 220→    `np.mean([NaN, NaN])` 直接返回 NaN。在 GroupBacktestResult 聚合时
 221→    若某组只有 1 个标的且其字段为 NaN，会导致下游 JSON 序列化失败。
 222→
 223→    行为：
 224→        - 空列表 / 全 NaN → default
 225→        - 部分 NaN → 自动忽略 NaN 后取均值（np.nanmean 语义）
 226→    """
 227→    arr = np.asarray(values, dtype=float)
 228→    if arr.size == 0:
 229→        return default
 230→    mask = np.isfinite(arr)
 231→    if not mask.any():
 232→        return default
 233→    return float(arr[mask].mean())
 234→
 235→
 236→def _compute_sharpe(returns: pd.Series, periods_per_year: int = 252) -> float:
 237→    """从日收益率序列计算年化 Sharpe Ratio。"""
 238→    returns = returns.dropna()
 239→    if len(returns) < 5:
 240→        return 0.0
 241→    mean = returns.mean()
 242→    std = returns.std()
 243→    if std <= 0 or np.isnan(std):
 244→        return 0.0
 245→    return float(mean / std * np.sqrt(periods_per_year))
 246→
 247→
 248→def _compute_sortino(
 249→    returns: pd.Series,
 250→    periods_per_year: int = 252,
 251→    target: float = 0.0,
 252→) -> float:
 253→    """从日收益率序列计算年化 Sortino Ratio（Constitution L1 首要 KPI）。
 254→
 255→    Sortino = (mean(returns) - target) / downside_deviation * sqrt(periods_per_year)
 256→    downside_deviation = sqrt( mean( min(0, returns - target)^2 ) )
 257→
 258→    与 Sharpe 的区别：仅对下行波动惩罚，上行波动不计入分母。
 259→    适合"收益>0 但偶尔大跌"的中长线策略评估。
 260→
 261→    退化处理（与 _compute_sharpe 一致）：
 262→        - 样本 < 5 → 0.0
 263→        - 下行波动 ≤ 0（无下行样本）→ 0.0（理论为 +inf，返回 0 保持保守 + 可算术聚合）
 264→
 265→    Args:
 266→        returns:          日收益率序列（如 pf.returns()）
 267→        periods_per_year: 年化因子（日线 = 252）
 268→        target:           MAR/目标收益率，默认 0（与 _compute_sharpe 无风险利率假设一致）
 269→
 270→    Returns:
 271→        年化 Sortino Ratio
 272→    """
 273→    returns = returns.dropna()
 274→    if len(returns) < 5:
 275→        return 0.0
 276→    excess = returns - target
 277→    downside = excess.where(excess < 0, 0.0)        # 仅保留负偏离，正偏离置 0
 278→    dd = np.sqrt((downside ** 2).mean())
 279→    if dd <= 0 or np.isnan(dd):
 280→        return 0.0
 281→    return float(returns.mean() / dd * np.sqrt(periods_per_year))
 282→
 283→
 284→def _combine_daily_returns(results: list[SingleBacktestResult]) -> pd.Series:
 285→    """等权合并组内日收益率序列，返回组合日收益率（迭代 #9 新增）。
 286→
 287→    与 _portfolio_sharpe_from_results / _portfolio_sortino_from_results 同语义：
 288→    将所有标的日收益率等权合并为组合序列。提取为独立函数以便 alpha 计算
 289→    和 per-strategy best params 选择复用，避免重复 pd.concat。
 290→
 291→    Args:
 292→        results: 单策略多标的的回测结果列表
 293→
 294→    Returns:
 295→        组合日收益率 pd.Series；无有效数据时返回空 Series
 296→    """
 297→    valid = [r.daily_returns for r in results if not r.daily_returns.empty]
 298→    if not valid:
 299→        return pd.Series(dtype=float)
 300→    return pd.concat(valid, axis=1).mean(axis=1)
 301→
 302→
 303→def _is_degenerate_strategy(results: list[SingleBacktestResult]) -> bool:
 304→    """判定一个策略在组内是否退化（几乎不产生已平仓交易）（迭代 #11 新增）。
 305→
 306→    退化定义：有效标的中 closed_trades==0 的比例 >= DEGENERATE_NO_CLOSE_FRACTION。
 307→    这类策略的入场/出场条件互斥（如 Iter #8 rsi_trend_filter 趋势过滤锁死均值
 308→    回归出场），仓位无法平仓，其 Sortino/alpha 只是持仓盯市假象，不代表真实
 309→    交易能力，必须在排序前剔除（experience.md #8：sanity → risk → rank）。
 310→
 311→    Args:
 312→        results: 单策略多标的的回测结果列表
 313→
 314→    Returns:
 315→        True 表示退化（应剔除）；空结果视为退化（True）
 316→    """
 317→    if not results:
 318→        return True
 319→    n = len(results)
 320→    no_close = sum(1 for r in results if r.closed_trades <= 0)
 321→    return (no_close / n) >= DEGENERATE_NO_CLOSE_FRACTION
 322→
 323→
 324→def _compute_alpha(
 325→    strategy_daily_returns: pd.Series,
 326→    spy_daily_returns: pd.Series | None,
 327→    periods_per_year: int = 252,
 328→) -> float:
 329→    """计算 alpha = 策略年化收益 - SPY 年化收益（迭代 #9 新增）。
 330→
 331→    Alpha 衡量策略相对 SPY buy-and-hold 的超额收益。正值表示跑赢 SPY，
 332→    负值表示跑输 SPY。用于 top-K 策略选择和 per-strategy best params 选择，
 333→    替代之前基于 Sortino/Sharpe 的选择逻辑（参考 iteration #9 spec）。
 334→
 335→    年化公式：(1 + mean_daily) ** periods_per_year - 1
 336→    使用算术平均日收益的几何年化，与 PortfolioBacktester 同口径。
 337→
 338→    降级处理：SPY 数据不可用（None 或空）→ 返回 0.0（不抛异常）。
 339→    这样在 SPY 数据缺失时，alpha 排序退化为"原顺序"，不会阻塞回测。
 340→
 341→    Args:
 342→        strategy_daily_returns: 策略组合日收益率序列
 343→        spy_daily_returns:      SPY 日收益率序列；None 表示数据不可用
 344→        periods_per_year:       年化因子（日线 = 252）
 345→
 346→    Returns:
 347→        Alpha 百分数（如 5.23 表示策略年化收益跑赢 SPY 5.23 个百分点）；
 348→        SPY 不可用时返回 0.0
 349→    """
 350→    if spy_daily_returns is None or spy_daily_returns.empty:
 351→        return 0.0
 352→    if strategy_daily_returns is None or strategy_daily_returns.empty:
 353→        return 0.0
 354→
 355→    # 对齐时间索引（inner join 取交集）
 356→    aligned = pd.concat(
 357→        [strategy_daily_returns.rename("strat"), spy_daily_returns.rename("spy")],
 358→        axis=1,
 359→        join="inner",
 360→    ).dropna()
 361→    if aligned.empty or len(aligned) < 2:
 362→        return 0.0
 363→
 364→    strat_returns = aligned["strat"]
 365→    spy_returns = aligned["spy"]
 366→
 367→    # 年化收益 = (1 + mean_daily)^252 - 1
 368→    strat_mean = strat_returns.mean()
 369→    spy_mean = spy_returns.mean()
 370→    if not np.isfinite(strat_mean) or not np.isfinite(spy_mean):
 371→        return 0.0
 372→
 373→    strat_annual = (1.0 + strat_mean) ** periods_per_year - 1.0
 374→    spy_annual = (1.0 + spy_mean) ** periods_per_year - 1.0
 375→
 376→    alpha = (strat_annual - spy_annual) * 100.0  # 转为百分数
 377→    if not np.isfinite(alpha):
 378→        return 0.0
 379→    return float(alpha)
 380→
 381→
 382→def _backtest_one(
 383→    df: pd.DataFrame,
 384→    strategy_name: str,
 385→    params: dict,
 386→    init_cash: float = 100_000.0,
 387→    fees: float = 0.001,
 388→    slippage: float = 0.001,
 389→) -> SingleBacktestResult | None:
 390→    """对单只标的执行单次回测。
 391→
 392→    使用 open= 参数确保信号在下一根 bar 的开盘价执行（与实盘一致）。
 393→
 394→    Returns:
 395→        SingleBacktestResult 或 None（数据不足/策略异常时）
 396→    """
 397→    strategy_fn = STRATEGY_REGISTRY.get(strategy_name)
 398→    if strategy_fn is None:
 399→        return None
 400→
 401→    if df.empty or len(df) < 30:
 402→        return None
 403→
 404→    try:
 405→        close = df["close"]
 406→        open_ = df["open"] if "open" in df.columns else None
 407→
 408→        # 调用策略（兼容需要 df 的策略）
 409→        try:
 410→            sig = strategy_fn(close, df=df, **params)
 411→        except TypeError:
 412→            sig = strategy_fn(close, **params)
 413→
 414→        entries = sig == 1
 415→        exits   = sig == -1
 416→
 417→        pf_kwargs: dict[str, Any] = dict(
 418→            entries=entries,
 419→            exits=exits,
 420→            init_cash=init_cash,
 421→            fees=fees,
 422→            slippage=slippage,
 423→            size=0.95,
 424→            size_type="Percent",
 425→            freq="D",
 426→        )
 427→
 428→        # ⚠️ 必须传 open= 参数：信号在下一根 bar 开盘价执行，与实盘一致
 429→        if open_ is not None:
 430→            pf = vbt.Portfolio.from_signals(close=close, open=open_, **pf_kwargs)
 431→        else:
 432→            pf = vbt.Portfolio.from_signals(close, **pf_kwargs)
 433→
 434→        stats = pf.stats()
 435→
 436→        daily_returns = pf.returns()
 437→
 438→        # 迭代 #11：已平仓交易数（用于健全性门槛 _is_degenerate_strategy）
 439→        # vbt 1.0 API: pf.trades.closed.count() 返回 Status==Closed 的交易数
 440→        # 区分"真交易闭环"与"末尾强平计 1 笔的伪 buy-and-hold"
 441→        try:
 442→            closed_trades = int(pf.trades.closed.count())
 443→        except Exception:
 444→            closed_trades = 0
 445→
 446→        return SingleBacktestResult(
 447→            symbol=str(df.index.name or ""),
 448→            strategy=strategy_name,
 449→            params=params,
 450→            sharpe=_safe_float(stats.get("Sharpe Ratio")),
 451→            total_return_pct=_safe_float(stats.get("Total Return [%]")),
 452→            max_drawdown_pct=_safe_float(stats.get("Max Drawdown [%]")),
 453→            win_rate_pct=_safe_float(stats.get("Win Rate [%]")),
 454→            total_trades=int(_safe_float(stats.get("Total Trades"), default=0.0)),
 455→            daily_returns=daily_returns,
 456→            sortino=_compute_sortino(daily_returns),
 457→            closed_trades=closed_trades,
 458→        )
 459→    except Exception as e:
 460→        logger.debug(f"[backtest_one] {strategy_name}({params}) failed: {e}")
 461→        return None
 462→
 463→
 464→def _backtest_batch(
 465→    data: dict[str, pd.DataFrame],
 466→    strategy_name: str,
 467→    params: dict,
 468→    init_cash: float = 100_000.0,
 469→    fees: float = 0.001,
 470→    slippage: float = 0.001,
 471→) -> list[SingleBacktestResult]:
 472→    """对组内所有标的批量执行回测（迭代 #10 新增）。
 473→
 474→    核心优化：用一次 vbt.Portfolio.from_signals 处理组内所有标的，
 475→    替代 `_backtest_one` 的 for-symbol 循环。调用次数从 O(N 标的)
 476→    降为 O(1)，预计 10-20x 提速（spec §1）。
 477→
 478→    实现要点：
 479→        1. 逐标的调用策略函数（保持与 `_backtest_one` 一致的调用语义：
 480→           先尝试 `strategy_fn(close, df=df, **params)`，TypeError 时
 481→           回退到 `strategy_fn(close, **params)`）。策略函数本身不改。
 482→        2. 构建列式矩阵（每列一个标的），用一次 vbt 调用回测所有标的。
 483→           vbt 1.0+ 的列分组语义保证每列独立结算 P&L。
 484→        3. 通过 `pf[sym]` 提取每列的 stats/daily_returns，输出格式与
 485→           `_backtest_one` 完全一致，下游聚合代码无需修改。
 486→
 487→    对齐策略：
 488→        - 用 `pd.DataFrame(dict)` 构造时自动 outer-join 时间索引，
 489→          缺失值填 NaN。
 490→        - vbt 对 NaN close 的处理：内部 fillna 为 0 收益率，等价于
 491→          "该标的此日期不交易"。当标的在样本外日期缺失时（如退市、
 492→          新上市），其 stats 仍按其有效日期区间计算。
 493→        - 在美股实际场景中所有标的共享交易日历，日期对齐天然成立，
 494→          不会有大量 NaN。
 495→
 496→    Args:
 497→        data:          {symbol: OHLCV DataFrame} 字典
 498→        strategy_name: 策略名
 499→        params:        策略参数
 500→        init_cash:     初始资金（vbt 给每列分配独立的 init_cash）
 501→        fees:          手续费率
 502→        slippage:      滑点率
 503→
 504→    Returns:
 505→        SingleBacktestResult 列表（与 `_backtest_one` 输出格式一致）。
 506→        数据不足 / 策略异常的标的会被跳过（不返回 None，不抛异常）。
 507→        空数据时返回空列表。
 508→    """
 509→    strategy_fn = STRATEGY_REGISTRY.get(strategy_name)
 510→    if strategy_fn is None:
 511→        return []
 512→
 513→    # 1. 逐标的调用策略函数，构建 signal / close / open 列
 514→    signal_columns: dict[str, pd.Series] = {}
 515→    close_columns: dict[str, pd.Series] = {}
 516→    open_columns: dict[str, pd.Series] = {}
 517→
 518→    for sym, df in data.items():
 519→        if df is None or df.empty or len(df) < 30:
 520→            continue
 521→        close = df["close"]
 522→        if "open" in df.columns:
 523→            open_ = df["open"]
 524→            open_columns[sym] = open_
 525→        else:
 526→            open_ = None
 527→
 528→        # 调用策略（与 _backtest_one 一致的 try/except 语义）
 529→        try:
 530→            sig = strategy_fn(close, df=df, **params)
 531→        except TypeError:
 532→            sig = strategy_fn(close, **params)
 533→        except Exception as e:
 534→            logger.debug(
 535→                f"[backtest_batch] {strategy_name}({params}) {sym} failed: {e}"
 536→            )
 537→            continue
 538→
 539→        signal_columns[sym] = sig
 540→        close_columns[sym] = close
 541→
 542→    if not signal_columns:
 543→        return []
 544→
 545→    # 2. 构建矩阵（自动 outer-join 索引，缺失值填 NaN）
 546→    close_matrix = pd.DataFrame(close_columns)
 547→    signal_matrix = pd.DataFrame(signal_columns)
 548→    has_open = bool(open_columns)
 549→    open_matrix = pd.DataFrame(open_columns) if has_open else None
 550→
 551→    # 3. 一次 vbt 调用处理所有标的
 552→    entries = signal_matrix == 1
 553→    exits = signal_matrix == -1
 554→
 555→    pf_kwargs: dict[str, Any] = dict(
 556→        entries=entries,
 557→        exits=exits,
 558→        init_cash=init_cash,
 559→        fees=fees,
 560→        slippage=slippage,
 561→        size=0.95,
 562→        size_type="Percent",
 563→        freq="D",
 564→    )
 565→
 566→    try:
 567→        if has_open:
 568→            pf = vbt.Portfolio.from_signals(
 569→                close=close_matrix, open=open_matrix, **pf_kwargs
 570→            )
 571→        else:
 572→            pf = vbt.Portfolio.from_signals(close_matrix, **pf_kwargs)
 573→    except Exception as e:
 574→        logger.warning(
 575→            f"[backtest_batch] {strategy_name}({params}) vbt call failed: {e} "
 576→            f"— falling back to per-symbol _backtest_one"
 577→        )
 578→        # 回滚方案：批量失败时退化为逐标的回测，保证回测不中断
 579→        results: list[SingleBacktestResult] = []
 580→        for sym, df in data.items():
 581→            if df is None or df.empty or len(df) < 30:
 582→                continue
 583→            df = df.copy()
 584→            df.index.name = sym
 585→            r = _backtest_one(
 586→                df, strategy_name, params, init_cash, fees, slippage
 587→            )
 588→            if r is not None:
 589→                results.append(r)
 590→        return results
 591→
 592→    # 4. 提取 per-symbol 结果（与 _backtest_one 输出格式一致）
 593→    results = []
 594→    for sym in signal_matrix.columns:
 595→        try:
 596→            pf_sym = pf[sym]
 597→            stats = pf_sym.stats()
 598→            daily_returns = pf_sym.returns()
 599→            # 迭代 #11：已平仓交易数（与 _backtest_one 同 API、同语义）
 600→            # pf_sym 是单列 pf，pf_sym.trades.closed.count() 返回 int
 601→            try:
 602→                closed_trades = int(pf_sym.trades.closed.count())
 603→            except Exception:
 604→                closed_trades = 0
 605→            results.append(SingleBacktestResult(
 606→                symbol=sym,
 607→                strategy=strategy_name,
 608→                params=params,
 609→                sharpe=_safe_float(stats.get("Sharpe Ratio")),
 610→                total_return_pct=_safe_float(stats.get("Total Return [%]")),
 611→                max_drawdown_pct=_safe_float(stats.get("Max Drawdown [%]")),
 612→                win_rate_pct=_safe_float(stats.get("Win Rate [%]")),
 613→                total_trades=int(_safe_float(stats.get("Total Trades"), default=0.0)),
 614→                daily_returns=daily_returns,
 615→                sortino=_compute_sortino(daily_returns),
 616→                closed_trades=closed_trades,
 617→            ))
 618→        except Exception as e:
 619→            logger.debug(
 620→                f"[backtest_batch] {strategy_name}({params}) {sym} "
 621→                f"stats extraction failed: {e}"
 622→            )
 623→            continue
 624→
 625→    return results
 626→
 627→
 628→def _portfolio_sharpe_from_results(results: list[SingleBacktestResult]) -> float:
 629→    """等权合并组内日收益率序列，计算组合 Sharpe。
 630→
 631→    ⚠️ 不能取各标的 Sharpe 算术平均（Sharpe 是比率，不能直接平均）。
 632→    正确做法：将所有标的日收益率等权合并为组合序列，再计算 Sharpe。
 633→    """
 634→    valid = [r.daily_returns for r in results if not r.daily_returns.empty]
 635→    if not valid:
 636→        return 0.0
 637→
 638→    # 对齐时间索引，等权平均
 639→    combined = pd.concat(valid, axis=1).mean(axis=1)
 640→    return _compute_sharpe(combined)
 641→
 642→
 643→def _portfolio_sortino_from_results(results: list[SingleBacktestResult]) -> float:
 644→    """等权合并组内日收益率序列，计算组合 Sortino（与 _portfolio_sharpe_from_results 同语义）。
 645→
 646→    不能取各标的 Sortino 算术平均（与 Sharpe 同理：比率不可直接平均）。
 647→    """
 648→    valid = [r.daily_returns for r in results if not r.daily_returns.empty]
 649→    if not valid:
 650→        return 0.0
 651→    combined = pd.concat(valid, axis=1).mean(axis=1)
 652→    return _compute_sortino(combined)
 653→
 654→
 655→def _portfolio_max_drawdown_from_results(
 656→    results: list[SingleBacktestResult],
 657→) -> float:
 658→    """等权合并组内日收益率序列，计算组合最大回撤（迭代 #2 新增，Constitution L1 KPI）。
 659→
 660→    与 `_portfolio_sharpe_from_results` 同语义：不能取各标的 DD 算术平均，
 661→    因为 DD 是路径依赖的比率。正确做法是先把��内日收益率等权合并为组合序列，
 662→    再 cumprod → cummax → drawdown → max。
 663→
 664→    返回值约定：百分比形式（与 `SingleBacktestResult.max_drawdown_pct` 一致，
 665→    vectorbt stats 中 `Max Drawdown [%]` 同样是百分数，例如 -15.2 表示 15.2% 回撤）。
 666→    本函数返回正值（0.0 ~ 100.0）便于聚合与 JSON 输出。
 667→
 668→    退化处理：
 669→        - 无有效日收益率 → 0.0
 670→        - 全 0 收益率（cumprod 恒为 1.0）→ 0.0
 671→    """
 672→    valid = [r.daily_returns for r in results if not r.daily_returns.empty]
 673→    if not valid:
 674→        return 0.0
 675→    combined = pd.concat(valid, axis=1).mean(axis=1).dropna()
 676→    if len(combined) < 2:
 677→        return 0.0
 678→    # 组合累计净值：初始 1.0，每日乘 (1 + r)
 679→    cumvalue = (1.0 + combined).cumprod()
 680→    peak = cumvalue.cummax()
 681→    drawdown = (cumvalue - peak) / peak   # 负值，0 表示无回撤
 682→    dd_max_pct = float(drawdown.min())    # 最负值，例如 -0.152
 683→    if not np.isfinite(dd_max_pct):
 684→        return 0.0
 685→    # 转为正百分数（与 vectorbt Max Drawdown [%] 的口径一致但取正号）
 686→    return abs(dd_max_pct) * 100.0
 687→
 688→
 689→def _optimize_ensemble_weights(
 690→    group_results: list[tuple[str, dict, list[SingleBacktestResult]]],
 691→    spy_returns: pd.Series | None = None,
 692→    conflict_threshold: float = 0.3,
 693→) -> list[tuple[str, dict, float]]:
 694→    """在"单点离散值加权投票"语义下优化 ensemble 权重。
 695→
 696→    实盘每根 bar 各策略产出离散值（1/-1/0），加权投票决定方向。
 697→    回测的权重优化必须使用相同语义，而非对整段时间序列做加权。
 698→
 699→    迭代 #9：权重计算从 Sharpe 改为 Alpha（vs SPY）。
 700→    动机：与 _run_group 的 top-K 排序口径一致，使 ensemble 权重直接
 701→    反映"跑赢 SPY 的程度"。SPY 不可用时 alpha=0，退化为等权。
 702→
 703→    迭代 #12：修负 alpha 归一化 bug。
 704→    旧代码 `max(alpha, 0.01)` 把负 alpha 都变成 0.01，归一化后等权，
 705→    掩盖"都不好"的事实（experience.md #8）。新逻辑：负 alpha 权重为 0，
 706→    只有正 alpha 参与归一化；全负 alpha 时等权 fallback + WARNING
 707→    （上游 alpha gate 应已拦截，此处为防御性设计）。
 708→
 709→    迭代 #16 注：上游 alpha gate 从 alpha>0 放宽至 alpha > ALPHA_GATE_THRESHOLD (-2%)，
 710→    允许小幅负 alpha 候选进入 ensemble。本函数仍用 max(a, 0.0) 作为权重下限，
 711→    意味着 ensemble 内负 alpha 策略权重仍为 0（被正 alpha 策略"覆盖"）。
 712→    这是保守设计：在多策略 ensemble 中，正 alpha 策略应主导权重；
 713→    单策略场景由 `len == 1` 早返回得到 weight=1.0。
 714→    若未来需要让小幅负 alpha 也贡献权重，可改为 `max(a - ALPHA_GATE_THRESHOLD, 0.0)`。
 715→
 716→    Args:
 717→        group_results: [(strategy, params, [SingleBacktestResult]), ...]
 718→        spy_returns:   SPY 日收益率序列（用于 alpha 计算）；None 时退化为等权
 719→        conflict_threshold: 加权投票分数绝对值低于此时视为 HOLD
 720→
 721→    Returns:
 722→        [(strategy, params, weight), ...] 归一化权重列表
 723→    """
 724→    if len(group_results) == 1:
 725→        strategy, params, _ = group_results[0]
 726→        return [(strategy, params, 1.0)]
 727→
 728→    # 迭代 #12：负 alpha 策略不参与 ensemble（experience.md #8：负分不能用 max(x, ε) 掩盖）
 729→    # 只有正 alpha 的策略参与归一化；负 alpha 策略权重为 0。
 730→    # 上游 _run_group 的 alpha gate（Iter #16: alpha > ALPHA_GATE_THRESHOLD=-2%）
 731→    # 应已拦截严重跑输的候选，这里是防御性设计：即使上游漏过负 alpha，
 732→    # 也不会被 max(0.01) 掩盖成等权。
 733→    raw_alphas = []
 734→    for strategy, params, results in group_results:
 735→        combined = _combine_daily_returns(results)
 736→        alpha = _compute_alpha(combined, spy_returns)
 737→        raw_alphas.append(alpha)
 738→
 739→    # 负 alpha → 权重 0；正 alpha → 参与归一化
 740→    positive_alphas = [max(a, 0.0) for a in raw_alphas]
 741→    total = sum(positive_alphas)
 742→
 743→    if total > 0:
 744→        weights = [a / total for a in positive_alphas]
 745→    else:
 746→        # 防御性 fallback：全负 alpha 或全零时等权
 747→        # （上游 alpha gate 应已拦截，此处不应到达）
 748→        n = len(group_results)
 749→        weights = [1.0 / n] * n if n > 0 else []
 750→        logger.warning(
 751→            f"[ensemble_weights] all alphas <= 0 ({raw_alphas}), "
 752→            f"falling back to equal weight. This should not happen if "
 753→            f"alpha gate (threshold={ALPHA_GATE_THRESHOLD}%) is active upstream."
 754→        )
 755→
 756→    return [
 757→        (strategy, params, weight)
 758→        for (strategy, params, _), weight in zip(group_results, weights)
 759→    ]
 760→
 761→
 762→# ---------------------------------------------------------------------------
 763→# Walk-Forward 验证（迭代 #3 新增，Constitution L7 验证流水线）
 764→# ---------------------------------------------------------------------------
 765→
 766→def _add_months(d: date, months: int) -> date:
 767→    """对 date 加/减 months 个月，自动 clamp 到月末。
 768→
 769→    使用 pandas DateOffset 以避免引入 dateutil 依赖（pandas 已是核心依赖）。
 770→    """
 771→    return (pd.Timestamp(d) + pd.DateOffset(months=months)).date()
 772→
 773→
 774→def _backtest_with_params_on_period(
 775→    mb: "MatrixBacktest",
 776→    symbols: list[str],
 777→    weights: list[dict[str, Any]],
 778→    start: date,
 779→    end: date,
 780→) -> list[pd.Series]:
 781→    """用给定权重配置在 [start, end] 期间回测，返回每条 (策略×标的) 的日收益率序列。
 782→
 783→    用于 Walk-Forward 验证期：用训练期产出的 best params 在验证期回测，
 784→    不再做参数搜索。返回原始日收益率列表，由调用方聚合为整体 portfolio。
 785→
 786→    迭代 #10 变更：用 `_backtest_batch` 替代 for-symbol 循环，
 787→    每个策略×参数组合一次 vbt 调用，加速 Walk-Forward 验证期回测。
 788→
 789→    Args:
 790→        mb:       MatrixBacktest 实例（复用其 store/init_cash/fees/slippage）
 791→        symbols:  该组的标的列表
 792→        weights:  训练期产出的权重配置（list of dict，含 strategy/params/weight）
 793→        start:    验证期起始日期
 794→        end:      验证期结束日期
 795→
 796→    Returns:
 797→        list[pd.Series] — 每条 (strategy×symbol) 的日收益率；空列表表示无有效数据
 798→    """
 799→    if not weights or not symbols:
 800→        return []
 801→
 802→    data = mb._store.get_bars_multi(symbols, start, end)
 803→    if not data:
 804→        return []
 805→
 806→    all_returns: list[pd.Series] = []
 807→    for w in weights:
 808→        strategy = w.get("strategy", "")
 809→        params = w.get("params", {})
 810→        if not strategy or strategy not in STRATEGY_REGISTRY:
 811→            continue
 812→        # 迭代 #10：一次 batch 调用处理组内所有标的
 813→        results = _backtest_batch(
 814→            data, strategy, params,
 815→            mb._init_cash, mb._fees, mb._slippage,
 816→        )
 817→        for r in results:
 818→            if not r.daily_returns.empty:
 819→                all_returns.append(r.daily_returns)
 820→    return all_returns
 821→
 822→
 823→def run_walk_forward(
 824→    mb: "MatrixBacktest",
 825→    strategies: list[str],
 826→    param_grids: dict[str, dict[str, list]],
 827→    rounds: int = 4,
 828→    train_months: int = 18,
 829→    val_months: int = 6,
 830→) -> WalkForwardReport:
 831→    """执行 N 轮 Walk-Forward 验证（Constitution L7 验证流水线硬要求）。
 832→
 833→    每轮流程：
 834→        1. 训练期 [train_start, train_end]：跑矩阵回测找最优参数
 835→        2. 验证期 [val_start, val_end]：用同参数回测，记录 portfolio Sortino 和 max DD
 836→        3. passed = val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD (15%)
 837→
 838→    时间窗口（动态计算，today=today）：
 839→        - 最后一轮 val_end = today - val_months（留 1 个 val 期给 paper trading）
 840→        - 每轮向前推 val_months
 841→        - train_end = val_start，train_start = train_end - train_months
 842→
 843→    默认参数 (rounds=4, train_months=18, val_months=6) 对应用户提供的固定窗口：
 844→        today=2026-07-01 →
 845→        Round 1: train 2021-07-02~2023-01-02, val 2023-01-02~2023-07-02
 846→        Round 2: train 2022-01-02~2023-07-02, val 2023-07-02~2024-01-02
 847→        Round 3: train 2022-07-02~2024-01-02, val 2024-01-02~2024-07-02
 848→        Round 4: train 2023-01-02~2024-07-02, val 2024-07-02~2025-01-02
 849→
 850→    Args:
 851→        mb:            MatrixBacktest 实例（复用其 store/universe/init_cash 等）
 852→        strategies:    策略名称列表
 853→        param_grids:   参数网格（与 mb.run() 接收的格式一致）
 854→        rounds:        轮次数（默认 4，Constitution L7 要求）
 855→        train_months:  训练期月数（默认 18）
 856→        val_months:    验证期月数（默认 6）
 857→
 858→    Returns:
 859→        WalkForwardReport — 包含每轮结果、pass_all_rounds、max_val_dd
 860→
 861→    Note:
 862→        - WF 是验证步骤，不修改 strategy_weights.json
 863→        - 失败轮次会记录 WARNING 但不抛异常
 864→        - 全部 4 轮通过是进入 paper trading 的前置条件
 865→    """
 866→    today = date.today()
 867→    groups = mb._universe.get_groups()
 868→    if not groups:
 869→        logger.warning("[WalkForward] no groups available — skipping")
 870→        return WalkForwardReport()
 871→
 872→    wf_rounds: list[WalkForwardRound] = []
 873→
 874→    for i in range(rounds):
 875→        round_num = i + 1
 876→        # 计算本轮时间窗口
 877→        # 最后一轮 (i=rounds-1) 的 val_end = today - val_months
 878→        # 前面轮次依次向前推 val_months
 879→        val_end = _add_months(today, -val_months - (rounds - round_num) * val_months)
 880→        val_start = _add_months(val_end, -val_months)
 881→        train_end = val_start
 882→        train_start = _add_months(train_end, -train_months)
 883→
 884→        logger.info(
 885→            f"[WalkForward] Round {round_num}/{rounds}: "
 886→            f"train={train_start}~{train_end}, val={val_start}~{val_end}"
 887→        )
 888→
 889→        # ── 训练期：跑矩阵回测找最优参数（复用 mb._run_group）──
 890→        train_report = MatrixBacktestReport(
 891→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
 892→            backtest_window=f"{train_start.isoformat()} ~ {train_end.isoformat()}",
 893→            groups={},
 894→        )
 895→
 896→        for group_id, symbols in groups.items():
 897→            weights = mb._run_group(
 898→                group_id=group_id,
 899→                symbols=symbols,
 900→                start=train_start,
 901→                end=train_end,
 902→                strategies=strategies,
 903→                param_grids=param_grids,
 904→                report=train_report,
 905→            )
 906→            train_report.groups[group_id] = weights
 907→
 908→        # ── 验证期：用训练期 best params 回测，聚合为整体 portfolio ──
 909→        all_returns: list[pd.Series] = []
 910→        for group_id, symbols in groups.items():
 911→            weights = train_report.groups.get(group_id, [])
 912→            if not weights:
 913→                continue
 914→            group_returns = _backtest_with_params_on_period(
 915→                mb, symbols, weights, val_start, val_end,
 916→            )
 917→            all_returns.extend(group_returns)
 918→
 919→        # 计算整体 portfolio 指标（等权合并所有组的日收益率）
 920→        if not all_returns:
 921→            val_sortino = 0.0
 922→            val_max_dd = 0.0
 923→            val_alpha = 0.0
 924→            logger.warning(
 925→                f"[WalkForward] Round {round_num}: no valid val returns — "
 926→                f"sortino=0, dd=0, alpha=0, passed=True (vacuous)"
 927→            )
 928→        else:
 929→            combined = pd.concat(all_returns, axis=1).mean(axis=1).dropna()
 930→            if len(combined) < 5:
 931→                val_sortino = 0.0
 932→                val_max_dd = 0.0
 933→                val_alpha = 0.0
 934→            else:
 935→                val_sortino = _compute_sortino(combined)
 936→                wrapper = [SingleBacktestResult(
 937→                    symbol="portfolio", strategy="", params={},
 938→                    sharpe=0.0, total_return_pct=0.0, max_drawdown_pct=0.0,
 939→                    win_rate_pct=0.0, total_trades=0, daily_returns=combined,
 940→                )]
 941→                val_max_dd = _portfolio_max_drawdown_from_results(wrapper)
 942→
 943→                # ── 迭代 #13：计算验证期 alpha vs SPY ──
 944→                # 与 matrix_backtest 的 alpha 选择目标一致（目标一致性修复）
 945→                # SPY 不可用时 alpha=0.0（与 _compute_alpha 的降级语义一致）
 946→                spy_val_returns = mb._get_spy_returns(val_start, val_end)
 947→                if spy_val_returns is not None:
 948→                    val_alpha = _compute_alpha(combined, spy_val_returns)
 949→                else:
 950→                    val_alpha = 0.0
 951→                    logger.warning(
 952→                        f"[WalkForward] Round {round_num}: SPY data unavailable for "
 953→                        f"val period {val_start}~{val_end} — val_alpha=0 (degraded)"
 954→                    )
 955→
 956→        # ── 迭代 #13：gate 加 alpha 校验 ──
 957→        # 单轮：DD ≤ 15% AND alpha > -5%（允许小幅跑输，不容忍灾难性跑输）
 958→        # 汇总（在 report 构建时）：all rounds passed AND avg_val_alpha > 0
 959→        dd_passed = val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD
 960→        alpha_passed = val_alpha > WALK_FORWARD_VAL_ALPHA_FLOOR
 961→        passed = dd_passed and alpha_passed
 962→        wf_rounds.append(WalkForwardRound(
 963→            round_num=round_num,
 964→            train_start=train_start,
 965→            train_end=train_end,
 966→            val_start=val_start,
 967→            val_end=val_end,
 968→            val_sortino=val_sortino,
 969→            val_max_dd=val_max_dd,
 970→            val_alpha=val_alpha,
 971→            passed=passed,
 972→        ))
 973→        logger.info(
 974→            f"[WalkForward] Round {round_num} result: "
 975→            f"sortino={val_sortino:.4f}, dd={val_max_dd:.4f}%, "
 976→            f"alpha={val_alpha:.4f}%, passed={passed} "
 977→            f"(dd_threshold={WALK_FORWARD_VAL_DD_THRESHOLD}%, "
 978→            f"alpha_floor={WALK_FORWARD_VAL_ALPHA_FLOOR}%)"
 979→        )
 980→
 981→    # ── 迭代 #13：汇总 alpha 聚合 + pass_all_rounds 加 avg alpha > 0 条件 ──
 982→    val_alphas = [r.val_alpha for r in wf_rounds]
 983→    avg_val_alpha = sum(val_alphas) / len(val_alphas) if val_alphas else 0.0
 984→    min_val_alpha = min(val_alphas) if val_alphas else 0.0
 985→
 986→    # 单轮全过 AND 平均 alpha > 0（OOS 平均必须跑赢 SPY）
 987→    all_rounds_passed = all(r.passed for r in wf_rounds) if wf_rounds else False
 988→    avg_alpha_positive = avg_val_alpha > 0
 989→    pass_all = all_rounds_passed and avg_alpha_positive
 990→
 991→    report = WalkForwardReport(
 992→        rounds=wf_rounds,
 993→        pass_all_rounds=pass_all,
 994→        max_val_dd=max((r.val_max_dd for r in wf_rounds), default=0.0),
 995→        avg_val_alpha=avg_val_alpha,
 996→        min_val_alpha=min_val_alpha,
 997→    )
 998→    logger.info(
 999→        f"[WalkForward] done: {len(wf_rounds)} rounds, "
1000→        f"pass_all_rounds={report.pass_all_rounds}, "
1001→        f"max_val_dd={report.max_val_dd:.4f}%, "
1002→        f"avg_val_alpha={report.avg_val_alpha:.4f}%, "
1003→        f"min_val_alpha={report.min_val_alpha:.4f}%"
1004→    )
1005→    return report
1006→
1007→
1008→# ---------------------------------------------------------------------------
1009→# MatrixBacktest 主类
1010→# ---------------------------------------------------------------------------
1011→
1012→class MatrixBacktest:
1013→    """矩阵回测：N 策略 × G 标的组 × 参数网格 → strategy_weights.json。
1014→
1015→    Args:
1016→        store:       MarketDataStore（本地时序库）
1017→        universe:    UniverseManager（提供分组映射）
1018→        years:       回测窗口（默认 5 年）
1019→        init_cash:   初始资金
1020→        fees:        手续费率
1021→        slippage:    滑点率
1022→        top_k:       每组保留 Top-K 策略（默认 2）
1023→    """
1024→
1025→    def __init__(
1026→        self,
1027→        store: MarketDataStore,
1028→        universe: UniverseManager,
1029→        years: int = 5,
1030→        init_cash: float = 100_000.0,
1031→        fees: float = 0.001,
1032→        slippage: float = 0.001,
1033→        top_k: int = 2,
1034→    ) -> None:
1035→        self._store = store
1036→        self._universe = universe
1037→        self._years = years
1038→        self._init_cash = init_cash
1039→        self._fees = fees
1040→        self._slippage = slippage
1041→        self._top_k = top_k
1042→
1043→    def run(
1044→        self,
1045→        strategies: list[str],
1046→        param_grids: dict[str, dict[str, list]],
1047→        output_file: str | Path | None = None,
1048→    ) -> MatrixBacktestReport:
1049→        """执行完整矩阵回测。
1050→
1051→        Args:
1052→            strategies:  策略名称列表，如 ["dual_ma", "rsi"]
1053→            param_grids: 各策略参数网格，如 {"dual_ma": {"fast":[5,10], "slow":[20,30]}}
1054→            output_file: strategy_weights.json 输出路径（None 则不写文件）
1055→
1056→        Returns:
1057→            MatrixBacktestReport
1058→        """
1059→        today = date.today()
1060→        start = today - timedelta(days=self._years * 365)
1061→        window_str = f"{start.isoformat()} ~ {today.isoformat()}"
1062→
1063→        logger.info(
1064→            f"[MatrixBacktest] start={start}, end={today}, "
1065→            f"strategies={strategies}, years={self._years}"
1066→        )
1067→
1068→        # 获取分组（⚠️ 使用历史时点分组，而非当前静态分组）
1069→        # Phase 5 初期简化：用当前分组，但接口已预留历史分组能力
1070→        groups = self._universe.get_groups()
1071→        if not groups:
1072→            logger.warning("[MatrixBacktest] no groups available, abort")
1073→            return MatrixBacktestReport(
1074→                generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
1075→                backtest_window=window_str,
1076→                groups={},
1077→            )
1078→
1079→        report = MatrixBacktestReport(
1080→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
1081→            backtest_window=window_str,
1082→            groups={},
1083→        )
1084→
1085→        for group_id, symbols in groups.items():
1086→            logger.info(
1087→                f"[MatrixBacktest] group={group_id}, symbols={len(symbols)}, "
1088→                f"strategies={strategies}"
1089→            )
1090→
1091→            group_weights = self._run_group(
1092→                group_id=group_id,
1093→                symbols=symbols,
1094→                start=start,
1095→                end=today,
1096→                strategies=strategies,
1097→                param_grids=param_grids,
1098→                report=report,
1099→            )
1100→            report.groups[group_id] = group_weights
1101→
1102→        if output_file is not None:
1103→            self._write_weights(report, output_file)
1104→
1105→        logger.info(
1106→            f"[MatrixBacktest] done: {len(report.groups)} groups, "
1107→            f"warnings={len(report.warnings)}"
1108→        )
1109→        return report
1110→
1111→    def _get_spy_returns(self, start: date, end: date) -> pd.Series | None:
1112→        """获取 SPY 同期日收益率序列，用于计算 alpha（迭代 #9 新增）。
1113→
1114→        从 MarketDataStore 拉取 SPY 日线数据，计算日收益率。
1115→        SPY 不在标的池中，但作为 benchmark 用于 alpha 计算。
1116→
1117→        降级处理：SPY 数据不可用时返回 None（_compute_alpha 会返回 0.0），
1118→        不抛异常，保证回测不因 benchmark 缺失而阻塞。
1119→
1120→        Args:
1121→            start: 回测起始日期
1122→            end:   回测结束日期
1123→
1124→        Returns:
1125→            SPY 日收益率 pd.Series；数据不可用时返回 None
1126→        """
1127→        try:
1128→            spy_bars = self._store.get_bars_multi(["SPY"], start, end)
1129→            spy_df = spy_bars.get("SPY") if spy_bars else None
1130→            if spy_df is None or spy_df.empty:
1131→                logger.warning(
1132→                    "[MatrixBacktest] SPY data unavailable, alpha will degrade to 0.0"
1133→                )
1134→                return None
1135→            spy_close = spy_df["close"].astype(float)
1136→            if len(spy_close) < 2:
1137→                logger.warning(
1138→                    "[MatrixBacktest] SPY data too short, alpha will degrade to 0.0"
1139→                )
1140→                return None
1141→            return spy_close.pct_change().dropna()
1142→        except Exception as e:
1143→            logger.warning(
1144→                f"[MatrixBacktest] SPY benchmark fetch failed: {e} — "
1145→                f"alpha will degrade to 0.0"
1146→            )
1147→            return None
1148→
1149→    def _run_group(
1150→        self,
1151→        group_id: str,
1152→        symbols: list[str],
1153→        start: date,
1154→        end: date,
1155→        strategies: list[str],
1156→        param_grids: dict[str, dict[str, list]],
1157→        report: MatrixBacktestReport,
1158→    ) -> list[dict[str, Any]]:
1159→        """对单个分组执行策略 × 参数网格回测，返回该组的权重配置列表。
1160→
1161→        迭代 #9 变更：
1162→            - per-strategy best params：从 Sharpe 改为 Alpha（vs SPY）
1163→            - top-K 排序：从 Sortino 改为 Alpha
1164→            - 新增 Sortino > 0.5 最低质量门槛（二级过滤，可放宽）
1165→            - ensemble weights：从 Sharpe 改为 Alpha
1166→        迭代 #10 变更：
1167→            - 用 `_backtest_batch` 替代 for-symbol 循环（10-20x 提速）
1168→            - 每组 / 每策略增加进度耗时日志
1169→        """
1170→        import time
1171→
1172→        group_start = time.time()
1173→
1174→        # 1. 读取组内所有标的数据
1175→        data = self._store.get_bars_multi(symbols, start, end)
1176→        if not data:
1177→            logger.warning(f"[MatrixBacktest] {group_id}: no data, skip")
1178→            return []
1179→
1180→        # 迭代 #9：获取 SPY 同期日收益率用于 alpha 计算（一次获取，组内复用）
1181→        spy_returns = self._get_spy_returns(start, end)
1182→
1183→        valid_symbol_count = sum(
1184→            1 for df in data.values() if df is not None and not df.empty and len(df) >= 30
1185→        )
1186→        logger.info(
1187→            f"[MatrixBacktest] {group_id}: start — "
1188→            f"{len(strategies)} strategies × {valid_symbol_count} valid symbols"
1189→        )
1190→
1191→        # 2. 对每个策略 × 每组参数，按 alpha 选最优参数
1192→        group_results: list[tuple[str, dict, list[SingleBacktestResult]]] = []
1193→
1194→        for strategy in strategies:
1195→            strat_start = time.time()
1196→
1197→            # ⚠️ 早期检测未注册策略名（迭代 #1 修复"策略名拼写错误被静默跳过"的 bug）
1198→            # 之前 _backtest_one 内部静默 return None，导致 main.py 误用 "rsi"/"macd"/"bollinger"
1199→            # 简称 6 天未被发现。改为 WARNING 级日志 + continue。
1200→            if strategy not in STRATEGY_REGISTRY:
1201→                logger.warning(
1202→                    f"[MatrixBacktest] {group_id}: strategy '{strategy}' not in "
1203→                    f"STRATEGY_REGISTRY — skipped. "
1204→                    f"Check spelling against @register_strategy decorators. "
1205→                    f"Known: {sorted(STRATEGY_REGISTRY.keys())}"
1206→                )
1207→                continue
1208→            grid = param_grids.get(strategy, {})
1209→            param_combos = list(
1210→                dict(zip(grid.keys(), combo))
1211→                for combo in itertools.product(*grid.values())
1212→            ) if grid else [{}]
1213→
1214→            best_params = None
1215→            best_alpha = float("-inf")
1216→            best_sharpe = 0.0       # 仅用于 GroupBacktestResult 存档
1217→            best_sortino = 0.0      # 仅用于 GroupBacktestResult 存档
1218→            best_results: list[SingleBacktestResult] = []
1219→
1220→            for params in param_combos:
1221→                # 迭代 #10：用 _backtest_batch 一次处理组内所有标的
1222→                # 替代原 for sym in symbols: _backtest_one(...) 的逐标的循环
1223→                results = _backtest_batch(
1224→                    data, strategy, params,
1225→                    self._init_cash, self._fees, self._slippage,
1226→                )
1227→
1228→                if not results:
1229→                    continue
1230→
1231→                # ⚠️ 等权合并日收益率序列，一次性计算所有指标
1232→                # 迭代 #9：复用 combined 计算 sharpe / sortino / alpha
1233→                combined = _combine_daily_returns(results)
1234→                ps = _compute_sharpe(combined)
1235→                pso = _compute_sortino(combined)
1236→                alpha = _compute_alpha(combined, spy_returns)
1237→
1238→                # 迭代 #9：per-strategy best params 用 alpha 选（替代 Sharpe）
1239→                if alpha > best_alpha:
1240→                    best_alpha = alpha
1241→                    best_sharpe = ps
1242→                    best_sortino = pso
1243→                    best_params = params
1244→                    best_results = results
1245→
1246→            if best_params is not None and best_results:
1247→                group_results.append((strategy, best_params, best_results))
1248→                report.group_results.append(GroupBacktestResult(
1249→                    group_id=group_id,
1250→                    strategy=strategy,
1251→                    params=best_params,
1252→                    portfolio_sharpe=best_sharpe,
1253→                    avg_total_return_pct=_safe_mean(
1254→                        [r.total_return_pct for r in best_results]
1255→                    ),
1256→                    avg_max_drawdown_pct=_safe_mean(
1257→                        [r.max_drawdown_pct for r in best_results]
1258→                    ),
1259→                    avg_win_rate_pct=_safe_mean(
1260→                        [r.win_rate_pct for r in best_results]
1261→                    ),
1262→                    symbol_count=len(best_results),
1263→                    portfolio_sortino=best_sortino,
1264→                    portfolio_max_drawdown=_portfolio_max_drawdown_from_results(
1265→                        best_results
1266→                    ),
1267→                    backtest_alpha=best_alpha,
1268→                ))
1269→
1270→            logger.info(
1271→                f"[MatrixBacktest] {group_id}: {strategy} done in "
1272→                f"{time.time() - strat_start:.1f}s "
1273→                f"({len(param_combos)} param combos × {valid_symbol_count} symbols)"
1274→            )
1275→
1276→        if not group_results:
1277→            logger.warning(
1278→                f"[MatrixBacktest] {group_id}: no valid results "
1279→                f"(elapsed {time.time() - group_start:.1f}s)"
1280→            )
1281→            return []
1282→
1283→        # 迭代 #11：健全性过滤 —— 排序前先剔除退化策略
1284→        # （experience.md #8：sanity → risk → rank）
1285→        # 退化策略 = 组内 ≥ 80% 标的 closed_trades==0（入场/出场条件互斥，
1286→        # 仓位靠末尾强平凑出 Sortino/alpha 假象）。此类策略必须先于 DD/Sortino/
1287→        # Alpha 过滤剔除，否则其盯市假象会骗过 alpha 排序进入权重。
1288→        sane_results: list[tuple[str, dict, list[SingleBacktestResult]]] = []
1289→        for (strategy, params, results) in group_results:
1290→            if _is_degenerate_strategy(results):
1291→                logger.warning(
1292→                    f"[MatrixBacktest] {group_id}: strategy '{strategy}' is DEGENERATE "
1293→                    f"(>= {DEGENERATE_NO_CLOSE_FRACTION:.0%} symbols have 0 closed trades) "
1294→                    f"— excluded before ranking. Its Sortino/alpha is mark-to-market illusion."
1295→                )
1296→                continue
1297→            sane_results.append((strategy, params, results))
1298→
1299→        if not sane_results:
1300→            # 全组退化 → 空权重（持仓现金），标记 no_valid_strategy，不强行选退化策略
1301→            logger.warning(
1302→                f"[MatrixBacktest] {group_id}: ALL strategies degenerate — "
1303→                f"group produces EMPTY weights (hold cash). Marked no_valid_strategy."
1304→            )
1305→            report.warnings.append(
1306→                f"{group_id}: no_valid_strategy (all strategies degenerate)"
1307→            )
1308→            # 标记已 append 的 GroupBacktestResult 条目（供审计追溯）
1309→            for gr in report.group_results:
1310→                if gr.group_id == group_id:
1311→                    gr.no_valid_strategy = True
1312→            return []
1313→
1314→        # 后续 candidates 构建、DD/Sortino/Alpha 过滤、排序，全部改用 sane_results
1315→        group_results = sane_results
1316→
1317→        # 3. 迭代 #9：DD 硬约束 + Sortino 门槛 + Alpha 排序选 Top-K
1318→        #    Constitution L1: portfolio DD ≤ 20% 是硬约束（保留）
1319→        #    新增：Sortino > 0.5 最低质量门槛（可放宽）
1320→        #    变更：排序指标从 Sortino 改为 Alpha
1321→        #
1322→        #    三级过滤策略：
1323→        #      Tier 1: DD ≤ 20% AND Sortino > 0.5 → Alpha 降序
1324→        #      Tier 2 (fallback): Tier 1 为空 → 仅 DD ≤ 20% → Alpha 降序
1325→        #      Tier 3 (fallback): Tier 2 为空 → 按 DD 升序，标记 dd_constrained=True
1326→        candidates: list[
1327→            tuple[str, dict, list[SingleBacktestResult], float, float, float]
1328→        ] = []
1329→        for (strategy, params, results) in group_results:
1330→            pso = _portfolio_sortino_from_results(results)
1331→            pdd = _portfolio_max_drawdown_from_results(results)
1332→            # 复用 _combine_daily_returns 计算 alpha（与 per-strategy 选择一致）
1333→            alpha = _compute_alpha(_combine_daily_returns(results), spy_returns)
1334→            candidates.append((strategy, params, results, pso, pdd, alpha))
1335→
1336→        # 迭代 #12：alpha 硬门槛（experience.md #8：正超额是排序前的硬门槛）
1337→        # 迭代 #16：阈值从 alpha>0 放宽至 alpha > ALPHA_GATE_THRESHOLD (-2%)。
1338→        #   动机：SPX 成分股 vs SPY 存在结构性近零 alpha，严格 alpha>0 门槛导致
1339→        #   4/6 组空仓（Iter #15 reoptimize 实证）。-2% 仍过滤"灾难性跑输"，
1340→        #   同时保留"小幅跑输 SPY 但 Sortino/DD 优秀"的候选。
1341→        #   Walk-Forward（Iter #13）仍用 -5% 单轮下限 + avg>0 汇总门槛作 OOS 校验，
1342→        #   放宽 in-sample gate 不削弱 OOS 验证强度。
1343→        # 顺序：健全性（Iter #11）→ 风险（DD，Tier 1/2/3）→ alpha 门槛（本步）→ 排序
1344→        #
1345→        # 注意：这一步在 candidates 构建后、Tier 1 前，确保 Tier 1/2/3 只在合格 alpha 候选中进行。
1346→        # 如果某组所有候选 alpha ≤ ALPHA_GATE_THRESHOLD，该组空仓（hold cash），
1347→        # 不强行选严重跑输 SPY 的策略
1348→        # （experience.md #8："没有候选满足门槛时，正确动作是空仓/降现金/回退 benchmark，
1349→        #   不是矬子里拔将军"）。
1350→        alpha_qualified_candidates = [
1351→            c for c in candidates if c[5] > ALPHA_GATE_THRESHOLD
1352→        ]
1353→
1354→        if not alpha_qualified_candidates:
1355→            # 全组 alpha ≤ threshold → 空权重（持仓现金），标记 no_positive_alpha
1356→            # 字段名保留 no_positive_alpha（向下兼容下游消费方），语义为"无合格 alpha 候选"
1357→            alpha_strs = [f"{c[0]}({c[5]:.2f}%)" for c in candidates]
1358→            logger.warning(
1359→                f"[MatrixBacktest] {group_id}: ALL {len(candidates)} candidates have "
1360→                f"alpha <= {ALPHA_GATE_THRESHOLD}% (cannot beat SPY within tolerance) — "
1361→                f"{alpha_strs}. "
1362→                f"Group produces EMPTY weights (hold cash). Marked no_positive_alpha."
1363→            )
1364→            report.warnings.append(
1365→                f"{group_id}: no_positive_alpha "
1366→                f"(all {len(candidates)} candidates alpha <= {ALPHA_GATE_THRESHOLD}%)"
1367→            )
1368→            # 标记已 append 的 GroupBacktestResult 条目（供审计追溯）
1369→            for gr in report.group_results:
1370→                if gr.group_id == group_id:
1371→                    gr.no_positive_alpha = True
1372→            return []
1373→
1374→        # 后续 Tier 1/2/3 在合格 alpha 候选中进行
1375→        candidates = alpha_qualified_candidates
1376→
1377→        # Tier 1: DD ≤ 20% AND Sortino > 0.5
1378→        compliant = [
1379→            c for c in candidates
1380→            if c[4] <= MAX_PORTFOLIO_DRAWDOWN_PCT and c[3] > MIN_SORTINO_THRESHOLD
1381→        ]
1382→        if compliant:
1383→            # Tier 1 命中：按 Alpha 降序取 top-K
1384→            ranked = sorted(compliant, key=lambda x: x[5], reverse=True)
1385→            dd_constrained = False
1386→            logger.info(
1387→                f"[MatrixBacktest] {group_id}: DD + Sortino filter passed — "
1388→                f"{len(compliant)}/{len(candidates)} candidates compliant "
1389→                f"(DD <= {MAX_PORTFOLIO_DRAWDOWN_PCT}% AND Sortino > {MIN_SORTINO_THRESHOLD})"
1390→            )
1391→        else:
1392→            # Tier 2: 放宽 Sortino 门槛，仅保留 DD 约束
1393→            dd_compliant = [
1394→                c for c in candidates if c[4] <= MAX_PORTFOLIO_DRAWDOWN_PCT
1395→            ]
1396→            if dd_compliant:
1397→                # Tier 2 命中：按 Alpha 降序取 top-K（dd_constrained 仍为 False）
1398→                ranked = sorted(dd_compliant, key=lambda x: x[5], reverse=True)
1399→                dd_constrained = False
1400→                logger.warning(
1401→                    f"[MatrixBacktest] {group_id}: Sortino filter relaxed — "
1402→                    f"no candidate passed Sortino > {MIN_SORTINO_THRESHOLD}. "
1403→                    f"Fallback to DD-only filter: "
1404→                    f"{len(dd_compliant)}/{len(candidates)} candidates DD-compliant."
1405→                )
1406→            else:
1407→                # Tier 3: 无 DD 合规候选 → 按 DD 升序，标记 dd_constrained
1408→                # （结构性问题，如 NDX_high_vol 全部 > 20%）
1409→                ranked = sorted(candidates, key=lambda x: x[4])
1410→                dd_constrained = True
1411→                logger.warning(
1412→                    f"[MatrixBacktest] {group_id}: NO compliant candidates "
1413→                    f"(all {len(candidates)} exceed DD={MAX_PORTFOLIO_DRAWDOWN_PCT}%). "
1414→                    f"Fallback: selected top-{self._top_k} by lowest DD. "
1415→                    f"This group is marked dd_constrained=True — "
1416→                    f"review whether to drop the group or accept the risk."
1417→                )
1418→                report.warnings.append(
1419→                    f"{group_id}: dd_constrained=True "
1420→                    f"(min DD={ranked[0][4]:.2f}% > {MAX_PORTFOLIO_DRAWDOWN_PCT}%)"
1421→                )
1422→
1423→        top_results = ranked[: self._top_k]
1424→
1425→        # 把 dd_constrained 标记同步到 report.group_results 中对应组的条目
1426→        for gr in report.group_results:
1427→            if gr.group_id == group_id:
1428→                gr.dd_constrained = dd_constrained
1429→
1430→        # 4. 优化 ensemble 权重（单点离散值加权投票语义，迭代 #9 改用 alpha）
1431→        weighted = _optimize_ensemble_weights(
1432→            [(s, p, r) for (s, p, r, _, _, _) in top_results],
1433→            spy_returns=spy_returns,
1434→        )
1435→
1436→        # 5. 构建权重配置列表
1437→        weights_list = []
1438→        for strategy, params, weight in weighted:
1439→            # 找到对应的 GroupBacktestResult
1440→            gr = next(
1441→                (r for r in report.group_results
1442→                 if r.group_id == group_id and r.strategy == strategy),
1443→                None,
1444→            )
1445→            # 迭代 #4：新增 backtest_dd_status 字段（'pass' / 'dd_constrained'）
1446→            # 作为风险 metadata 标记，与 dd_constrained bool 同义但更可读
1447→            backtest_dd_status = "dd_constrained" if dd_constrained else "pass"
1448→            weights_list.append({
1449→                "strategy": strategy,
1450→                "params": params,
1451→                "weight": round(weight, 4),
1452→                "backtest_sharpe": round(gr.portfolio_sharpe if gr else 0.0, 4),
1453→                "backtest_sortino": round(gr.portfolio_sortino if gr else 0.0, 4),
1454→                "backtest_max_drawdown": round(gr.portfolio_max_drawdown if gr else 0.0, 4),
1455→                "backtest_win_rate": round(gr.avg_win_rate_pct / 100 if gr else 0.5, 4),
1456→                # 迭代 #9：新增 backtest_alpha 字段（vs SPY 的超额收益百分数）
1457→                # 下游 PortfolioBacktester 可读此字段验证 alpha 一致性
1458→                "backtest_alpha": round(gr.backtest_alpha if gr else 0.0, 4),
1459→                # 迭代 #3：标记该组是否用了 DD fallback（无合规候选）
1460→                # 同组所有策略条目共享同一 dd_constrained 值
1461→                "dd_constrained": dd_constrained,
1462→                # 迭代 #4：backtest_dd_status — 风险 metadata 字段
1463→                # 'pass' = 该组有合规候选（DD ≤ 20%）
1464→                # 'dd_constrained' = fallback 触发（无合规候选，按最低 DD 取 top-K）
1465→                # 下游消费方（PortfolioBacktester / 风控观测）可读此字段判断
1466→                # 该组权重的可靠性，作为风险信号标记
1467→                "backtest_dd_status": backtest_dd_status,
1468→            })
1469→
1470→        logger.info(
1471→            f"[MatrixBacktest] {group_id}: all strategies done in "
1472→            f"{time.time() - group_start:.1f}s "
1473→            f"(top-{self._top_k} selected, dd_constrained={dd_constrained})"
1474→        )
1475→
1476→        return weights_list
1477→
1478→    def _write_weights(
1479→        self, report: MatrixBacktestReport, output_file: str | Path
1480→    ) -> None:
1481→        """将矩阵回测结果写入 strategy_weights.json。"""
1482→        output_file = Path(output_file)
1483→        output_file.parent.mkdir(parents=True, exist_ok=True)
1484→
1485→        data = {
1486→            "_meta": {
1487→                "generated_at": report.generated_at,
1488→                "backtest_window": report.backtest_window,
1489→                "reoptimize_freq": "monthly",
1490→                "survivorship_bias_warning": (
1491→                    "使用当前成分股回测，S&P 500 5年成分变动约100只(~20%)，"
1492→                    "均值回归组(SPX_low_vol)结果可能系统性偏高"
1493→                ),
1494→            },
1495→            "groups": report.groups,
1496→        }
1497→
1498→        with open(output_file, "w", encoding="utf-8") as f:
1499→            json.dump(data, f, indent=2, ensure_ascii=False)
1500→
1501→        logger.info(f"[MatrixBacktest] weights saved to {output_file}")
1502→
---
Now
---
 I have a full
---
 understanding of the alpha
---
 gate logic
---
. Let me look
---
 at the key
---
 parts
---
:

1. `
---
ALPHA_GATE_THRESHOLD
---
:
---
 float = -2.0
---
` at
---
 line 66

---
2. The alpha
---
 gate filter at
---
 line 135
---
0-1352
---
:
```python
alpha
---
_
---
qualified_candidates
---
 = [
    c
---
 for c
---
 in candidates
---
 if c[
---
5] > ALPHA
---
_GATE_THRESHOLD
]
```

---
Where
---
 `c[
---
5]` is the alpha
---
 and `c[3]
---
` is the sortino (
---
from
---
 `
---
candidates.append
---
((
---
strategy, params
---
, results,
---
 pso, p
---
dd, alpha
---
))` at line 133
---
4).

So
---
 I
---
 need to:

---
1. Add `SORTINO
---
_ALPHA
---
_EXEMPTION =
---
 1.
---
5` constant
2.
---
 Modify the alpha
---
 gate filter to:
---
 `alpha >
---
 ALPHA
---
_GATE_THRESHOLD OR
---
 sortino > SORT
---
INO_ALPHA_EXEMPTION`


---
Let me also check the existing
---
 tests for the alpha
---
 gate to understand the test
---
 patterns. Let
---
 me find
---
 the test file.
---
现在
---
我已经理解
---
了 alpha
---
 gate。让我查看
---
一下现有的测试，
---
以了解其
---
模式
---
。
---
{"status": "completed", "taskId": "1"}
---
Updated task #1 status
---
Updated task #1 status
---
{"command": "ls /Users/rickouyang/Github/trade-tools/mytrader/tests/ | grep -i matrix", "description": "Find matrix_backtest test files"}
---
Find matrix_backtest test files
---
Command: ls /Users/rickouyang/Github/trade-tools/mytrader/tests/ | grep -i matrix
Stdout: test_matrix_backtest.py
test_strategy_matrix_ranker.py

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"command": "grep -n \"ALPHA_GATE\\|no_positive_alpha\\|alpha_gate\\|SORTINO_ALPHA\\|sortino.*exemp\\|Iter.*16\\|Iteration.*16\\|iteration.*16\\|iter.*16\" /Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py | head -50", "description": "Find alpha gate tests"}
---
Find alpha gate tests
---
Command: grep -n "ALPHA_GATE\|no_positive_alpha\|alpha_gate\|SORTINO_ALPHA\|sortino.*exemp\|Iter.*16\|Iteration.*16\|iteration.*16\|iter.*16" /Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py | head -50
Stdout: (empty)
Stderr: (empty)
Exit Code: 0
Signal: (none)
---
The
---
 memory
---
 note
---
 mentioned
---
 a
---
 pytest sandbox workaround
---
. Let me also
---
 check the test
---
 file to
---
 find existing
---
 alpha
---
 gate tests.
---
{"command": "grep -n \"alpha\\|Alpha\\|ALPHA\\|sortino\\|Sortino\\|SORTINO\\|exemp\\|gate\\|no_positive\" /Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py | head -80", "description": "Find alpha/sortino/gate tests"}
---
Find alpha/sortino/gate tests
---
Command: grep -n "alpha\|Alpha\|ALPHA\|sortino\|Sortino\|SORTINO\|exemp\|gate\|no_positive" /Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py | head -80
Stdout: 21:    _compute_alpha,
23:    _compute_sortino,
26:    _portfolio_sortino_from_results,
31:    MIN_SORTINO_THRESHOLD,
32:    WALK_FORWARD_VAL_ALPHA_FLOOR,
146:    # ── Sortino（迭代 #1 新增，Constitution L1 首要 KPI）─────────────────────
148:    def test_compute_sortino_positive(self):
149:        """正均值的收益序列 Sortino > 0。"""
151:        assert _compute_sortino(returns) > 0
153:    def test_compute_sortino_empty(self):
155:        assert _compute_sortino(pd.Series([], dtype=float)) == 0.0
157:    def test_compute_sortino_no_downside_returns_zero(self):
160:        理论上 Sortino 应为 +inf，但返回 0 保持可算术聚合 + 保守评估。
163:        assert _compute_sortino(returns) == 0.0
165:    def test_compute_sortino_differs_from_sharpe_when_asymmetric(self):
166:        """当上行/下行波动不对称时，Sortino ≠ Sharpe（这是引入 Sortino 的意义）。"""
167:        # 大幅上行小波动 + 偶尔小幅下行：Sortino 应明显高于 Sharpe
174:        sortino = _compute_sortino(returns)
175:        # Sortino 仅对下行惩罚 → 上行波动不计入分母 → Sortino > Sharpe
176:        assert sortino > sharpe, (
177:            f"非对称收益下 Sortino({sortino:.4f}) 应 > Sharpe({sharpe:.4f})，"
178:            f"否则说明 Sortino 公式退化为 Sharpe"
181:    def test_compute_sortino_known_value(self):
182:        """已知值验算 Sortino 公式正确性。"""
185:        # Sortino = 0.005 / 0.005 * sqrt(252) = 15.8745...
188:        assert abs(_compute_sortino(returns) - expected) < 1e-6
190:    def test_portfolio_sortino_from_results(self):
191:        """等权组合 Sortino 不等于各标的 Sortino 算术平均（与 Sharpe 同理）。"""
197:        s1 = _compute_sortino(r1)
198:        s2 = _compute_sortino(r2)
205:        portfolio_sortino = _portfolio_sortino_from_results(results)
207:        diff = abs(portfolio_sortino - arithmetic_avg)
209:            f"组合 Sortino({portfolio_sortino:.4f}) 与算术平均({arithmetic_avg:.4f}) "
447:    # ── 迭代 #1 新增：观测性 + 回归 + Sortino 输出 ──────────────────────────
497:    def test_output_file_contains_sortino(self, mock_store, mock_universe, tmp_path):
498:        """strategy_weights.json 每个权重条目含 backtest_sortino 字段（Constitution L1 首要 KPI）。"""
499:        output = tmp_path / "weights_with_sortino.json"
509:                assert "backtest_sortino" in w, (
510:                    f"{gid}: 权重条目缺少 backtest_sortino 字段，实际 keys={list(w.keys())}"
512:                assert isinstance(w["backtest_sortino"], (int, float)), (
513:                    f"{gid}: backtest_sortino 应为数值，实际 {type(w['backtest_sortino'])}"
516:    def test_group_results_have_portfolio_sortino(self, mock_store, mock_universe):
517:        """GroupBacktestResult.portfolio_sortino 是浮点数（迭代 #1 新增字段）。"""
524:            assert isinstance(gr.portfolio_sortino, float), (
525:                f"portfolio_sortino 应为 float，实际 {type(gr.portfolio_sortino)}"
608:    def test_compliant_candidates_selected_by_sortino(self, tmp_path):
609:        """P0 case 1: 有合规候选时，按 Sortino 降序选 top-K（不选 DD 超标的候选）。
612:        虽然 DD=25% 的候选 Sortino 更高，但 DD 约束应将其排除。
747:            val_sortino=1.5,
754:        assert r.val_sortino == 1.5
766:            val_sortino=1.0, val_max_dd=15.0, passed=True,
778:            val_sortino=1.0, val_max_dd=15.01, passed=False,
891:            3. 每轮有 val_sortino / val_max_dd / passed 字段
917:            assert isinstance(r.val_sortino, float)
920:            assert isinstance(r.val_alpha, float)  # 迭代 #13：val_alpha 字段
922:            # 迭代 #13：passed = DD ≤ 15% AND alpha > -5%
925:                and r.val_alpha > WALK_FORWARD_VAL_ALPHA_FLOOR
929:        # 迭代 #13：pass_all_rounds = all rounds passed AND avg_val_alpha > 0
932:            and report.avg_val_alpha > 0
974:# 迭代 #9 新增：Alpha-Based Strategy Selection
977:class TestAlphaComputation:
978:    """_compute_alpha / _combine_daily_returns 单元测试。"""
980:    def test_compute_alpha_basic(self):
981:        """构造已知策略收益和 SPY 收益，验证 alpha 计算正确。
997:        alpha = _compute_alpha(strat_returns, spy_returns)
999:        # 期望 alpha ≈ 17.5%（正数，跑赢 SPY）
1000:        assert alpha > 0.0, f"策略年化应高于 SPY，alpha 应为正，实际 {alpha:.4f}"
1002:        assert 10.0 < alpha < 25.0, (
1003:            f"alpha 应在 10~25% 范围，实际 {alpha:.4f}%"
1006:    def test_compute_alpha_spy_unavailable(self):
1007:        """SPY 数据为 None → alpha = 0.0（降级处理，不抛异常）。"""
1012:        assert _compute_alpha(strat_returns, None) == 0.0
1015:        assert _compute_alpha(strat_returns, empty_spy) == 0.0
1017:    def test_compute_alpha_strategy_underperforms(self):
1018:        """策略跑输 SPY → alpha 为负。"""
1024:        alpha = _compute_alpha(strat_returns, spy_returns)
1025:        assert alpha < 0.0, (
1026:            f"策略跑输 SPY 时 alpha 应为负，实际 {alpha:.4f}"
1048:    def test_min_sortino_threshold_constant(self):
1049:        """MIN_SORTINO_THRESHOLD = 0.5（spec §4.2 硬约束）。"""

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"command": "grep -n \"ALPHA_GATE\\|no_positive_alpha\\|Iter.*16\\|Iteration.*16\\|iteration.*16\\|iter.*16\\|alpha.*gate\\|alpha_gate\" /Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py | head -50", "description": "Find alpha gate tests"}
---
Find alpha gate tests
---
Command: grep -n "ALPHA_GATE\|no_positive_alpha\|Iter.*16\|Iteration.*16\|iteration.*16\|iter.*16\|alpha.*gate\|alpha_gate" /Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py | head -50
Stdout: (empty)
Stderr: (empty)
Exit Code: 0
Signal: (none)
---
Hmm
---
,
---
 no ALPHA
---
_GATE tests
---
 found
---
. Let me search
---
 more
---
 broadly.
---
{"command": "grep -rn \"ALPHA_GATE\\|no_positive_alpha\\|Iter.*16\\|Iteration.*16\\|iteration.*16\\|iter.*16\" /Users/rickouyang/Github/trade-tools/mytrader/tests/ | head -50", "description": "Find alpha gate tests across all test files"}
---
Find alpha gate tests across all test files
---
Command: grep -rn "ALPHA_GATE\|no_positive_alpha\|Iter.*16\|Iteration.*16\|iteration.*16\|iter.*16" /Users/rickouyang/Github/trade-tools/mytrader/tests/ | head -50
Stdout: /Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:3:迭代 #16 更新：alpha gate 从 alpha>0 放宽至 alpha > ALPHA_GATE_THRESHOLD (-2%)。
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:9:    1. `GroupBacktestResult.no_positive_alpha` 字段默认 False
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:10:    2. `_run_group` 在 candidates 构建后、Tier 1 剔除 alpha ≤ ALPHA_GATE_THRESHOLD 的候选
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:11:    3. 全负 alpha（< -2%）组返回空权重 + `no_positive_alpha=True` 标记
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:16:    8. [Iter #16] ALPHA_GATE_THRESHOLD 常量存在且等于 -2.0
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:17:    9. [Iter #16] alpha=-1% 通过 gate（在 -2% 与 0% 之间）
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:18:    10. [Iter #16] alpha=-5% 仍被拒绝
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:19:    11. [Iter #16] alpha=-2.0% 边界值被拒绝（使用 > 严格比较）
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:20:    12. [Iter #16] alpha=+1% 仍通过（无回归）
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:21:    13. [Iter #16] 集成场景：SPX 组 alpha=-1.5% 策略入选 tier1
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:22:    14. [Iter #16] 单策略 ensemble 负 alpha（> -2%）仍得 weight=1.0（早返回）
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:24:背景见 `iterations/iteration_16/spec.md` + `.codebuddy/notes/experience.md` #8。
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:37:    ALPHA_GATE_THRESHOLD,
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:149:# Test 1: no_positive_alpha 字段
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:153:    """GroupBacktestResult.no_positive_alpha 字段测试。"""
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:155:    def test_no_positive_alpha_field_default_false(self):
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:156:        """GroupBacktestResult.no_positive_alpha 默认 False。"""
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:162:        assert hasattr(gr, "no_positive_alpha"), (
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:163:            "GroupBacktestResult 必须有 no_positive_alpha 字段"
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:165:        assert gr.no_positive_alpha is False, (
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:166:            "no_positive_alpha 默认应为 False"
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:169:    def test_no_positive_alpha_field_settable(self):
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:170:        """no_positive_alpha 可被设置为 True。"""
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:175:            no_positive_alpha=True,
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:177:        assert gr.no_positive_alpha is True
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:188:        """全正 alpha 候选组正常产出权重，no_positive_alpha=False。
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:191:        验证：权重正常产出，no_positive_alpha 不被标记。
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:253:        # no_positive_alpha 不应被标记
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:256:                assert gr.no_positive_alpha is False, (
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:257:                    "全正 alpha 组不应标记 no_positive_alpha=True"
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:259:        # report.warnings 不含 no_positive_alpha
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:261:        assert "no_positive_alpha" not in warning_text, (
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:262:            f"全正 alpha 组不应有 no_positive_alpha 警告，实际 warnings={report.warnings}"
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:266:        """全负 alpha 组返回空权重 + no_positive_alpha=True 标记。
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:269:        验证：返回空 weights，report.warnings 含 no_positive_alpha 标记，
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:270:              group_results 条目 no_positive_alpha=True。
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:332:        # report.warnings 含 no_positive_alpha 标记
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:334:        assert "no_positive_alpha" in warning_text, (
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:335:            f"report.warnings 应含 no_positive_alpha 标记，"
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:339:        # group_results 条目被标记 no_positive_alpha=True
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:347:            assert gr.no_positive_alpha is True, (
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:348:                f"test_group 的 no_positive_alpha 应为 True，"
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:349:                f"实际 {gr.no_positive_alpha}"
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:426:        # no_positive_alpha 不应被标记（因为有正 alpha 候选通过）
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:429:                assert gr.no_positive_alpha is False
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:542:        """全退化组触发 no_valid_strategy（先于 alpha 门槛），不触发 no_positive_alpha。
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:545:        验证：返回空权重，标记 no_valid_strategy=True，no_positive_alpha=False
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:606:        # alpha 门槛未到达 → no_positive_alpha 不应被标记
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:607:        assert "no_positive_alpha" not in warning_text, (
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py:609:            f"不应触发 no_positive_alpha，warnings={report.warnings}"

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
There
---
's a test
---
_alpha
---
_gate
---
.py file
---
 specifically
---
 for the alpha
---
 gate. Let me read it
---
 fully
---
 to understand the test
---
 patterns.
---
{"file_path": "/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py"}
---
   1→"""迭代 #12：alpha>0 硬门槛测试（Reject Negative-Alpha Strategies）。
   2→
   3→迭代 #16 更新：alpha gate 从 alpha>0 放宽至 alpha > ALPHA_GATE_THRESHOLD (-2%)。
   4→动机：SPX 成分股 vs SPY benchmark 存在结构性近零 alpha，严格 alpha>0 门槛导致
   5→4/6 组空仓。放宽至 -2% 仍过滤"灾难性跑输"，但保留"小幅跑输 SPY 但 Sortino/DD
   6→优秀"的候选。WF OOS 校验仍用 -5% 单轮下限 + avg>0 汇总门槛，不削弱 OOS 验证。
   7→
   8→验证：
   9→    1. `GroupBacktestResult.no_positive_alpha` 字段默认 False
  10→    2. `_run_group` 在 candidates 构建后、Tier 1 剔除 alpha ≤ ALPHA_GATE_THRESHOLD 的候选
  11→    3. 全负 alpha（< -2%）组返回空权重 + `no_positive_alpha=True` 标记
  12→    4. 混合 alpha 组只保留 alpha > -2% 的候选
  13→    5. `_optimize_ensemble_weights` 负 alpha 策略权重为 0（不再 max(0.01) 掩盖）
  14→    6. 全负 alpha ensemble 退化为等权 + WARNING（防御性 fallback）
  15→    7. 健全性门槛 + alpha 门槛协同工作
  16→    8. [Iter #16] ALPHA_GATE_THRESHOLD 常量存在且等于 -2.0
  17→    9. [Iter #16] alpha=-1% 通过 gate（在 -2% 与 0% 之间）
  18→    10. [Iter #16] alpha=-5% 仍被拒绝
  19→    11. [Iter #16] alpha=-2.0% 边界值被拒绝（使用 > 严格比较）
  20→    12. [Iter #16] alpha=+1% 仍通过（无回归）
  21→    13. [Iter #16] 集成场景：SPX 组 alpha=-1.5% 策略入选 tier1
  22→    14. [Iter #16] 单策略 ensemble 负 alpha（> -2%）仍得 weight=1.0（早返回）
  23→
  24→背景见 `iterations/iteration_16/spec.md` + `.codebuddy/notes/experience.md` #8。
  25→"""
  26→
  27→from __future__ import annotations
  28→
  29→from datetime import date
  30→from unittest.mock import MagicMock, patch
  31→
  32→import numpy as np
  33→import pandas as pd
  34→import pytest
  35→
  36→from mytrader.backtest.matrix_backtest import (
  37→    ALPHA_GATE_THRESHOLD,
  38→    GroupBacktestResult,
  39→    MatrixBacktest,
  40→    MatrixBacktestReport,
  41→    SingleBacktestResult,
  42→    _combine_daily_returns,
  43→    _compute_alpha,
  44→    _optimize_ensemble_weights,
  45→)
  46→
  47→
  48→# ---------------------------------------------------------------------------
  49→# Test data generators（与 test_degenerate_filter.py / test_matrix_backtest.py 同风格）
  50→# ---------------------------------------------------------------------------
  51→
  52→def _make_ohlcv(
  53→    n: int = 300,
  54→    trend: str = "up",
  55→    start: str = "2021-01-01",
  56→    seed: int | None = None,
  57→) -> pd.DataFrame:
  58→    """生成测试 OHLCV 数据。"""
  59→    idx = pd.date_range(start, periods=n, freq="B")
  60→    if trend == "up":
  61→        close = np.array([100.0 + i * 0.1 for i in range(n)])
  62→    elif trend == "down":
  63→        close = np.array([100.0 - i * 0.05 for i in range(n)])
  64→    elif trend == "random":
  65→        rng = np.random.default_rng(seed if seed is not None else 42)
  66→        steps = rng.normal(0, 0.5, n)
  67→        close = np.cumsum(np.concatenate([[100.0], steps]))[1:]
  68→    else:
  69→        raise ValueError(f"unknown trend: {trend}")
  70→
  71→    return pd.DataFrame(
  72→        {
  73→            "open":   close - 0.5,
  74→            "high":   close + 1.0,
  75→            "low":    close - 1.0,
  76→            "close":  close,
  77→            "volume": [1_000_000] * n,
  78→        },
  79→        index=idx,
  80→    )
  81→
  82→
  83→def _make_spy_df(n: int = 300, annual_return: float = 0.10) -> pd.DataFrame:
  84→    """生成 SPY benchmark 数据，年化收益可调。
  85→
  86→    annual_return=0.10 → 日均收益 ≈ 0.00038（对数展开近似）。
  87→    annual_return=0.30 → 日均收益 ≈ 0.00107（高涨幅，策略难跑赢）。
  88→    """
  89→    idx = pd.date_range("2021-01-01", periods=n, freq="B")
  90→    daily_rate = (1.0 + annual_return) ** (1.0 / 252) - 1.0
  91→    close = [100.0 * ((1.0 + daily_rate) ** i) for i in range(n)]
  92→    return pd.DataFrame(
  93→        {
  94→            "open":   [c - 0.1 for c in close],
  95→            "high":   [c + 0.5 for c in close],
  96→            "low":    [c - 0.5 for c in close],
  97→            "close":  close,
  98→            "volume": [1_000_000] * n,
  99→        },
 100→        index=idx,
 101→    )
 102→
 103→
 104→def _make_store_with_spy(
 105→    symbols_data: dict[str, pd.DataFrame],
 106→    spy_df: pd.DataFrame,
 107→) -> MagicMock:
 108→    """构造 Mock MarketDataStore，含 SPY benchmark 数据。"""
 109→    store = MagicMock()
 110→    mapping = dict(symbols_data)
 111→    mapping["SPY"] = spy_df
 112→
 113→    def get_bars_multi(symbols, start, end, timeframe="1d"):
 114→        return {s: mapping[s] for s in symbols if s in mapping}
 115→
 116→    store.get_bars_multi.side_effect = get_bars_multi
 117→    return store
 118→
 119→
 120→def _make_mock_universe(groups: dict[str, list[str]]) -> MagicMock:
 121→    """构造 Mock UniverseManager。"""
 122→    universe = MagicMock()
 123→    universe.get_groups.return_value = groups
 124→    return universe
 125→
 126→
 127→def _make_result(
 128→    symbol: str,
 129→    strategy: str,
 130→    daily_returns: pd.Series,
 131→    closed_trades: int = 10,
 132→) -> SingleBacktestResult:
 133→    """快捷构造 SingleBacktestResult（带默认字段）。"""
 134→    return SingleBacktestResult(
 135→        symbol=symbol,
 136→        strategy=strategy,
 137→        params={},
 138→        sharpe=1.0,
 139→        total_return_pct=10.0,
 140→        max_drawdown_pct=5.0,
 141→        win_rate_pct=55.0,
 142→        total_trades=10,
 143→        daily_returns=daily_returns,
 144→        closed_trades=closed_trades,
 145→    )
 146→
 147→
 148→# ---------------------------------------------------------------------------
 149→# Test 1: no_positive_alpha 字段
 150→# ---------------------------------------------------------------------------
 151→
 152→class TestNoPositiveAlphaField:
 153→    """GroupBacktestResult.no_positive_alpha 字段测试。"""
 154→
 155→    def test_no_positive_alpha_field_default_false(self):
 156→        """GroupBacktestResult.no_positive_alpha 默认 False。"""
 157→        gr = GroupBacktestResult(
 158→            group_id="g", strategy="s", params={}, portfolio_sharpe=0.0,
 159→            avg_total_return_pct=0.0, avg_max_drawdown_pct=0.0,
 160→            avg_win_rate_pct=0.0, symbol_count=0,
 161→        )
 162→        assert hasattr(gr, "no_positive_alpha"), (
 163→            "GroupBacktestResult 必须有 no_positive_alpha 字段"
 164→        )
 165→        assert gr.no_positive_alpha is False, (
 166→            "no_positive_alpha 默认应为 False"
 167→        )
 168→
 169→    def test_no_positive_alpha_field_settable(self):
 170→        """no_positive_alpha 可被设置为 True。"""
 171→        gr = GroupBacktestResult(
 172→            group_id="g", strategy="s", params={}, portfolio_sharpe=0.0,
 173→            avg_total_return_pct=0.0, avg_max_drawdown_pct=0.0,
 174→            avg_win_rate_pct=0.0, symbol_count=0,
 175→            no_positive_alpha=True,
 176→        )
 177→        assert gr.no_positive_alpha is True
 178→
 179→
 180→# ---------------------------------------------------------------------------
 181→# Test 2-3: _run_group alpha>0 门槛集成
 182→# ---------------------------------------------------------------------------
 183→
 184→class TestRunGroupAlphaGate:
 185→    """_run_group alpha>0 硬门槛集成测试。"""
 186→
 187→    def test_positive_alpha_candidates_pass(self):
 188→        """全正 alpha 候选组正常产出权重，no_positive_alpha=False。
 189→
 190→        场景：两个策略都跑赢 SPY（正 alpha），健全性门槛通过。
 191→        验证：权重正常产出，no_positive_alpha 不被标记。
 192→        """
 193→        n = 300
 194→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
 195→        # SPY 年化 ~10%
 196→        spy_df = _make_spy_df(n, annual_return=0.10)
 197→        spy_returns = spy_df["close"].pct_change().dropna()
 198→
 199→        # 策略收益：日均 0.0012（年化 ~35%）→ 正 alpha
 200→        np.random.seed(42)
 201→        returns_a = pd.Series(np.random.normal(0.0012, 0.005, n), index=idx)
 202→        returns_b = pd.Series(np.random.normal(0.0010, 0.004, n), index=idx)
 203→
 204→        # 验证前提：两个策略 alpha 都 > 0
 205→        alpha_a = _compute_alpha(returns_a, spy_returns)
 206→        alpha_b = _compute_alpha(returns_b, spy_returns)
 207→        assert alpha_a > 0, f"策略 A alpha 应 > 0，实际 {alpha_a:.4f}"
 208→        assert alpha_b > 0, f"策略 B alpha 应 > 0，实际 {alpha_b:.4f}"
 209→
 210→        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
 211→            results = []
 212→            for sym, df in data.items():
 213→                if df is None or df.empty or len(df) < 30:
 214→                    continue
 215→                returns = returns_a if strategy_name == "dual_ma" else returns_b
 216→                results.append(_make_result(sym, strategy_name, returns, closed_trades=10))
 217→            return results
 218→
 219→        df_up = _make_ohlcv(n, trend="up")
 220→        store = _make_store_with_spy({"AAA": df_up, "BBB": df_up}, spy_df)
 221→        universe = _make_mock_universe({"test_group": ["AAA", "BBB"]})
 222→
 223→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
 224→        report = MatrixBacktestReport(
 225→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
 226→            backtest_window="2021-01-01 ~ 2022-01-01",
 227→            groups={},
 228→        )
 229→
 230→        with patch(
 231→            "mytrader.backtest.matrix_backtest._backtest_batch",
 232→            side_effect=mock_backtest_batch,
 233→        ):
 234→            weights = mb._run_group(
 235→                group_id="test_group",
 236→                symbols=["AAA", "BBB"],
 237→                start=date(2021, 1, 1),
 238→                end=date(2022, 1, 1),
 239→                strategies=["dual_ma", "rsi_mean_revert"],
 240→                param_grids={
 241→                    "dual_ma": {"fast": [5], "slow": [20]},
 242→                    "rsi_mean_revert": {
 243→                        "period": [14], "oversold": [30], "overbought": [70]
 244→                    },
 245→                },
 246→                report=report,
 247→            )
 248→
 249→        # 正 alpha 候选 → 权重正常产出
 250→        assert len(weights) > 0, (
 251→            f"全正 alpha 组应产出权重，实际 weights={weights}"
 252→        )
 253→        # no_positive_alpha 不应被标记
 254→        for gr in report.group_results:
 255→            if gr.group_id == "test_group":
 256→                assert gr.no_positive_alpha is False, (
 257→                    "全正 alpha 组不应标记 no_positive_alpha=True"
 258→                )
 259→        # report.warnings 不含 no_positive_alpha
 260→        warning_text = " ".join(report.warnings)
 261→        assert "no_positive_alpha" not in warning_text, (
 262→            f"全正 alpha 组不应有 no_positive_alpha 警告，实际 warnings={report.warnings}"
 263→        )
 264→
 265→    def test_all_negative_alpha_group_empty(self):
 266→        """全负 alpha 组返回空权重 + no_positive_alpha=True 标记。
 267→
 268→        场景：两个策略都跑输 SPY（负 alpha），健全性门槛通过。
 269→        验证：返回空 weights，report.warnings 含 no_positive_alpha 标记，
 270→              group_results 条目 no_positive_alpha=True。
 271→        """
 272→        n = 300
 273→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
 274→        # SPY 年化 ~30%（高涨幅，策略难跑赢）
 275→        spy_df = _make_spy_df(n, annual_return=0.30)
 276→        spy_returns = spy_df["close"].pct_change().dropna()
 277→
 278→        # 策略收益：日均 0.0003（年化 ~8%）→ 负 alpha（跑输 SPY 30%）
 279→        np.random.seed(42)
 280→        returns_a = pd.Series(np.random.normal(0.0003, 0.005, n), index=idx)
 281→        returns_b = pd.Series(np.random.normal(0.0002, 0.004, n), index=idx)
 282→
 283→        # 验证前提：两个策略 alpha 都 < 0
 284→        alpha_a = _compute_alpha(returns_a, spy_returns)
 285→        alpha_b = _compute_alpha(returns_b, spy_returns)
 286→        assert alpha_a < 0, f"策略 A alpha 应 < 0，实际 {alpha_a:.4f}"
 287→        assert alpha_b < 0, f"策略 B alpha 应 < 0，实际 {alpha_b:.4f}"
 288→
 289→        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
 290→            results = []
 291→            for sym, df in data.items():
 292→                if df is None or df.empty or len(df) < 30:
 293→                    continue
 294→                returns = returns_a if strategy_name == "dual_ma" else returns_b
 295→                results.append(_make_result(sym, strategy_name, returns, closed_trades=10))
 296→            return results
 297→
 298→        df_up = _make_ohlcv(n, trend="up")
 299→        store = _make_store_with_spy({"AAA": df_up, "BBB": df_up}, spy_df)
 300→        universe = _make_mock_universe({"test_group": ["AAA", "BBB"]})
 301→
 302→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
 303→        report = MatrixBacktestReport(
 304→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
 305→            backtest_window="2021-01-01 ~ 2022-01-01",
 306→            groups={},
 307→        )
 308→
 309→        with patch(
 310→            "mytrader.backtest.matrix_backtest._backtest_batch",
 311→            side_effect=mock_backtest_batch,
 312→        ):
 313→            weights = mb._run_group(
 314→                group_id="test_group",
 315→                symbols=["AAA", "BBB"],
 316→                start=date(2021, 1, 1),
 317→                end=date(2022, 1, 1),
 318→                strategies=["dual_ma", "rsi_mean_revert"],
 319→                param_grids={
 320→                    "dual_ma": {"fast": [5], "slow": [20]},
 321→                    "rsi_mean_revert": {
 322→                        "period": [14], "oversold": [30], "overbought": [70]
 323→                    },
 324→                },
 325→                report=report,
 326→            )
 327→
 328→        # 全负 alpha → 空权重
 329→        assert weights == [], (
 330→            f"全负 alpha 组应返回空权重，实际 weights={weights}"
 331→        )
 332→        # report.warnings 含 no_positive_alpha 标记
 333→        warning_text = " ".join(report.warnings)
 334→        assert "no_positive_alpha" in warning_text, (
 335→            f"report.warnings 应含 no_positive_alpha 标记，"
 336→            f"实际 warnings={report.warnings}"
 337→        )
 338→        assert "test_group" in warning_text
 339→        # group_results 条目被标记 no_positive_alpha=True
 340→        test_group_results = [
 341→            gr for gr in report.group_results if gr.group_id == "test_group"
 342→        ]
 343→        assert len(test_group_results) > 0, (
 344→            "test_group 应在 report.group_results 中有存档条目（供审计追溯）"
 345→        )
 346→        for gr in test_group_results:
 347→            assert gr.no_positive_alpha is True, (
 348→                f"test_group 的 no_positive_alpha 应为 True，"
 349→                f"实际 {gr.no_positive_alpha}"
 350→            )
 351→            # no_valid_strategy 应仍为 False（健全性门槛没触发）
 352→            assert gr.no_valid_strategy is False, (
 353→                "全负 alpha 但非退化组，no_valid_strategy 应为 False"
 354→            )
 355→
 356→    def test_negative_alpha_excluded(self):
 357→        """混合 alpha 候选组：负 alpha 不出现在 weights_list。
 358→
 359→        场景：dual_ma 负 alpha，rsi_mean_revert 正 alpha。
 360→        验证：只有 rsi_mean_revert 出现在 weights，dual_ma 被 alpha 门槛剔除。
 361→        """
 362→        n = 300
 363→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
 364→        spy_df = _make_spy_df(n, annual_return=0.10)
 365→        spy_returns = spy_df["close"].pct_change().dropna()
 366→
 367→        # dual_ma：日均 0.0002（年化 ~5%）→ 负 alpha（跑输 SPY 10%）
 368→        np.random.seed(42)
 369→        returns_a = pd.Series(np.random.normal(0.0002, 0.005, n), index=idx)
 370→        # rsi_mean_revert：日均 0.0015（年化 ~45%）→ 正 alpha
 371→        returns_b = pd.Series(np.random.normal(0.0015, 0.006, n), index=idx)
 372→
 373→        # 验证前提
 374→        alpha_a = _compute_alpha(returns_a, spy_returns)
 375→        alpha_b = _compute_alpha(returns_b, spy_returns)
 376→        assert alpha_a < 0, f"dual_ma alpha 应 < 0，实际 {alpha_a:.4f}"
 377→        assert alpha_b > 0, f"rsi_mean_revert alpha 应 > 0，实际 {alpha_b:.4f}"
 378→
 379→        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
 380→            results = []
 381→            for sym, df in data.items():
 382→                if df is None or df.empty or len(df) < 30:
 383→                    continue
 384→                returns = returns_a if strategy_name == "dual_ma" else returns_b
 385→                results.append(_make_result(sym, strategy_name, returns, closed_trades=10))
 386→            return results
 387→
 388→        df_up = _make_ohlcv(n, trend="up")
 389→        store = _make_store_with_spy({"AAA": df_up, "BBB": df_up}, spy_df)
 390→        universe = _make_mock_universe({"test_group": ["AAA", "BBB"]})
 391→
 392→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
 393→        report = MatrixBacktestReport(
 394→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
 395→            backtest_window="2021-01-01 ~ 2022-01-01",
 396→            groups={},
 397→        )
 398→
 399→        with patch(
 400→            "mytrader.backtest.matrix_backtest._backtest_batch",
 401→            side_effect=mock_backtest_batch,
 402→        ):
 403→            weights = mb._run_group(
 404→                group_id="test_group",
 405→                symbols=["AAA", "BBB"],
 406→                start=date(2021, 1, 1),
 407→                end=date(2022, 1, 1),
 408→                strategies=["dual_ma", "rsi_mean_revert"],
 409→                param_grids={
 410→                    "dual_ma": {"fast": [5], "slow": [20]},
 411→                    "rsi_mean_revert": {
 412→                        "period": [14], "oversold": [30], "overbought": [70]
 413→                    },
 414→                },
 415→                report=report,
 416→            )
 417→
 418→        # 负 alpha 的 dual_ma 不应在权重中
 419→        strategies_in_weights = [w["strategy"] for w in weights]
 420→        assert "dual_ma" not in strategies_in_weights, (
 421→            f"dual_ma（负 alpha）不应出现在权重中，实际 weights={strategies_in_weights}"
 422→        )
 423→        assert "rsi_mean_revert" in strategies_in_weights, (
 424→            f"rsi_mean_revert（正 alpha）应在权重中，实际 weights={strategies_in_weights}"
 425→        )
 426→        # no_positive_alpha 不应被标记（因为有正 alpha 候选通过）
 427→        for gr in report.group_results:
 428→            if gr.group_id == "test_group":
 429→                assert gr.no_positive_alpha is False
 430→
 431→
 432→# ---------------------------------------------------------------------------
 433→# Test 4: 健全性门槛 + alpha>0 门槛协同
 434→# ---------------------------------------------------------------------------
 435→
 436→class TestSanityGateAndAlphaGateCoordination:
 437→    """健全性门槛（Iter #11）+ alpha>0 门槛（Iter #12）协同工作。"""
 438→
 439→    def test_alpha_gate_after_sanity_gate(self):
 440→        """健全性门槛先剔除退化策略，alpha 门槛再剔除负 alpha 策略。
 441→
 442→        场景：3 个策略
 443→          - dual_ma: 退化（closed_trades=0）→ 健全性门槛剔除
 444→          - rsi_mean_revert: 正常但负 alpha → alpha 门槛剔除
 445→          - bollinger_band: 正常且正 alpha → 应入选
 446→
 447→        验证：只有 bollinger_band 出现在 weights。
 448→        """
 449→        n = 300
 450→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
 451→        spy_df = _make_spy_df(n, annual_return=0.10)
 452→        spy_returns = spy_df["close"].pct_change().dropna()
 453→
 454→        np.random.seed(42)
 455→        # dual_ma: 退化（closed_trades=0）+ 正 alpha（但健全性门槛先剔除）
 456→        returns_degenerate = pd.Series(np.random.normal(0.0015, 0.005, n), index=idx)
 457→        # rsi_mean_revert: 正常（closed_trades>0）+ 负 alpha
 458→        returns_negative_alpha = pd.Series(np.random.normal(0.0002, 0.004, n), index=idx)
 459→        # bollinger_band: 正常（closed_trades>0）+ 正 alpha
 460→        returns_positive_alpha = pd.Series(np.random.normal(0.0014, 0.005, n), index=idx)
 461→
 462→        # 验证前提
 463→        alpha_neg = _compute_alpha(returns_negative_alpha, spy_returns)
 464→        alpha_pos = _compute_alpha(returns_positive_alpha, spy_returns)
 465→        assert alpha_neg < 0, f"rsi_mean_revert alpha 应 < 0，实际 {alpha_neg:.4f}"
 466→        assert alpha_pos > 0, f"bollinger_band alpha 应 > 0，实际 {alpha_pos:.4f}"
 467→
 468→        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
 469→            results = []
 470→            for sym, df in data.items():
 471→                if df is None or df.empty or len(df) < 30:
 472→                    continue
 473→                if strategy_name == "dual_ma":
 474→                    # 退化：closed_trades=0
 475→                    results.append(_make_result(
 476→                        sym, strategy_name, returns_degenerate, closed_trades=0
 477→                    ))
 478→                elif strategy_name == "rsi_mean_revert":
 479→                    # 正常但负 alpha
 480→                    results.append(_make_result(
 481→                        sym, strategy_name, returns_negative_alpha, closed_trades=10
 482→                    ))
 483→                else:  # bollinger_band
 484→                    # 正常且正 alpha
 485→                    results.append(_make_result(
 486→                        sym, strategy_name, returns_positive_alpha, closed_trades=10
 487→                    ))
 488→            return results
 489→
 490→        df_up = _make_ohlcv(n, trend="up")
 491→        # 5 标的让退化比例 5/5=100% ≥ 0.8
 492→        store = _make_store_with_spy(
 493→            {"AAA": df_up, "BBB": df_up, "CCC": df_up, "DDD": df_up, "EEE": df_up},
 494→            spy_df,
 495→        )
 496→        universe = _make_mock_universe(
 497→            {"test_group": ["AAA", "BBB", "CCC", "DDD", "EEE"]}
 498→        )
 499→
 500→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=3)
 501→        report = MatrixBacktestReport(
 502→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
 503→            backtest_window="2021-01-01 ~ 2022-01-01",
 504→            groups={},
 505→        )
 506→
 507→        with patch(
 508→            "mytrader.backtest.matrix_backtest._backtest_batch",
 509→            side_effect=mock_backtest_batch,
 510→        ):
 511→            weights = mb._run_group(
 512→                group_id="test_group",
 513→                symbols=["AAA", "BBB", "CCC", "DDD", "EEE"],
 514→                start=date(2021, 1, 1),
 515→                end=date(2022, 1, 1),
 516→                strategies=["dual_ma", "rsi_mean_revert", "bollinger_band"],
 517→                param_grids={
 518→                    "dual_ma": {"fast": [5], "slow": [20]},
 519→                    "rsi_mean_revert": {
 520→                        "period": [14], "oversold": [30], "overbought": [70]
 521→                    },
 522→                    "bollinger_band": {"period": [20], "std_dev": [2.0]},
 523→                },
 524→                report=report,
 525→            )
 526→
 527→        # 只有 bollinger_band 应出现在权重中
 528→        strategies_in_weights = [w["strategy"] for w in weights]
 529→        assert "dual_ma" not in strategies_in_weights, (
 530→            f"dual_ma（退化）应被健全性门槛剔除，实际 weights={strategies_in_weights}"
 531→        )
 532→        assert "rsi_mean_revert" not in strategies_in_weights, (
 533→            f"rsi_mean_revert（负 alpha）应被 alpha 门槛剔除，"
 534→            f"实际 weights={strategies_in_weights}"
 535→        )
 536→        assert "bollinger_band" in strategies_in_weights, (
 537→            f"bollinger_band（正常 + 正 alpha）应入选，"
 538→            f"实际 weights={strategies_in_weights}"
 539→        )
 540→
 541→    def test_degenerate_takes_precedence_over_alpha_gate(self):
 542→        """全退化组触发 no_valid_strategy（先于 alpha 门槛），不触发 no_positive_alpha。
 543→
 544→        场景：所有策略都退化（closed_trades=0）。
 545→        验证：返回空权重，标记 no_valid_strategy=True，no_positive_alpha=False
 546→              （健全性门槛先返回，alpha 门槛未到达）。
 547→        """
 548→        n = 300
 549→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
 550→        spy_df = _make_spy_df(n, annual_return=0.10)
 551→
 552→        np.random.seed(42)
 553→        returns_a = pd.Series(np.random.normal(0.001, 0.005, n), index=idx)
 554→        returns_b = pd.Series(np.random.normal(0.0008, 0.003, n), index=idx)
 555→
 556→        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
 557→            results = []
 558→            for sym, df in data.items():
 559→                if df is None or df.empty or len(df) < 30:
 560→                    continue
 561→                returns = returns_a if strategy_name == "dual_ma" else returns_b
 562→                # 全退化：closed_trades=0
 563→                results.append(_make_result(sym, strategy_name, returns, closed_trades=0))
 564→            return results
 565→
 566→        df_up = _make_ohlcv(n, trend="up")
 567→        store = _make_store_with_spy(
 568→            {"AAA": df_up, "BBB": df_up, "CCC": df_up, "DDD": df_up, "EEE": df_up},
 569→            spy_df,
 570→        )
 571→        universe = _make_mock_universe(
 572→            {"test_group": ["AAA", "BBB", "CCC", "DDD", "EEE"]}
 573→        )
 574→
 575→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
 576→        report = MatrixBacktestReport(
 577→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
 578→            backtest_window="2021-01-01 ~ 2022-01-01",
 579→            groups={},
 580→        )
 581→
 582→        with patch(
 583→            "mytrader.backtest.matrix_backtest._backtest_batch",
 584→            side_effect=mock_backtest_batch,
 585→        ):
 586→            weights = mb._run_group(
 587→                group_id="test_group",
 588→                symbols=["AAA", "BBB", "CCC", "DDD", "EEE"],
 589→                start=date(2021, 1, 1),
 590→                end=date(2022, 1, 1),
 591→                strategies=["dual_ma", "rsi_mean_revert"],
 592→                param_grids={
 593→                    "dual_ma": {"fast": [5], "slow": [20]},
 594→                    "rsi_mean_revert": {
 595→                        "period": [14], "oversold": [30], "overbought": [70]
 596→                    },
 597→                },
 598→                report=report,
 599→            )
 600→
 601→        # 全退化 → 空权重
 602→        assert weights == []
 603→        # 健全性门槛先返回 → no_valid_strategy=True
 604→        warning_text = " ".join(report.warnings)
 605→        assert "no_valid_strategy" in warning_text
 606→        # alpha 门槛未到达 → no_positive_alpha 不应被标记
 607→        assert "no_positive_alpha" not in warning_text, (
 608→            f"全退化组应触发 no_valid_strategy（先于 alpha 门槛），"
 609→            f"不应触发 no_positive_alpha，warnings={report.warnings}"
 610→        )
 611→        for gr in report.group_results:
 612→            if gr.group_id == "test_group":
 613→                assert gr.no_valid_strategy is True
 614→                assert gr.no_positive_alpha is False
 615→
 616→
 617→# ---------------------------------------------------------------------------
 618→# Test 5-8: _optimize_ensemble_weights 负 alpha 归一化
 619→# ---------------------------------------------------------------------------
 620→
 621→class TestEnsembleWeightsNegativeAlpha:
 622→    """_optimize_ensemble_weights 负 alpha 归一化测试（迭代 #12 修复）。"""
 623→
 624→    def test_ensemble_negative_alpha_zero_weight(self):
 625→        """负 alpha 策略权重为 0（不再被 max(0.01) 掩盖成等权）。
 626→
 627→        场景：策略 A 正 alpha=10%，策略 B 负 alpha=-5%。
 628→        旧代码：max(-5, 0.01)=0.01, max(10, 0.01)=10 → 权重 ≈ 0.001 / 0.999
 629→        新代码：max(-5, 0)=0, max(10, 0)=10 → 权重 = 0.0 / 1.0
 630→        验证：B 的权重严格为 0，A 的权重为 1.0。
 631→        """
 632→        n = 252
 633→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
 634→        spy_returns = pd.Series(np.random.normal(0.0004, 0.001, n), index=idx)
 635→
 636→        # A: 正 alpha（日均 0.0012 >> SPY 0.0004）
 637→        returns_a = pd.Series(np.random.normal(0.0012, 0.005, n), index=idx)
 638→        # B: 负 alpha（日均 0.0001 << SPY 0.0004）
 639→        returns_b = pd.Series(np.random.normal(0.0001, 0.005, n), index=idx)
 640→
 641→        results_a = [_make_result("S1", "strat_a", returns_a)]
 642→        results_b = [_make_result("S2", "strat_b", returns_b)]
 643→
 644→        group_results = [
 645→            ("strat_a", {}, results_a),
 646→            ("strat_b", {}, results_b),
 647→        ]
 648→
 649→        weights = _optimize_ensemble_weights(group_results, spy_returns=spy_returns)
 650→        weights_dict = {s: w for s, _, w in weights}
 651→
 652→        # 验证前提：A 的 alpha > 0，B 的 alpha < 0
 653→        alpha_a = _compute_alpha(
 654→            _combine_daily_returns(results_a), spy_returns
 655→        )
 656→        alpha_b = _compute_alpha(
 657→            _combine_daily_returns(results_b), spy_returns
 658→        )
 659→        assert alpha_a > 0, f"A 的 alpha 应 > 0，实际 {alpha_a:.4f}"
 660→        assert alpha_b < 0, f"B 的 alpha 应 < 0，实际 {alpha_b:.4f}"
 661→
 662→        # B（负 alpha）权重应为 0
 663→        assert weights_dict["strat_b"] == 0.0, (
 664→            f"负 alpha 策略权重应为 0，实际 {weights_dict['strat_b']:.6f}"
 665→        )
 666→        # A（正 alpha）权重应为 1.0
 667→        assert abs(weights_dict["strat_a"] - 1.0) < 1e-9, (
 668→            f"全正 alpha 归一化后 A 权重应为 1.0，"
 669→            f"实际 {weights_dict['strat_a']:.6f}"
 670→        )
 671→        # 权重和 = 1.0
 672→        total = sum(weights_dict.values())
 673→        assert abs(total - 1.0) < 1e-9
 674→
 675→    def test_ensemble_all_positive_normalizes(self):
 676→        """全正 alpha 正常归一化（权重和=1.0，高 alpha 权重大）。"""
 677→        n = 252
 678→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
 679→        spy_returns = pd.Series(np.random.normal(0.0004, 0.001, n), index=idx)
 680→
 681→        # A: 高 alpha（日均 0.0015）
 682→        returns_a = pd.Series(np.random.normal(0.0015, 0.005, n), index=idx)
 683→        # B: 低 alpha（日均 0.0008，仍 > SPY 0.0004）
 684→        returns_b = pd.Series(np.random.normal(0.0008, 0.003, n), index=idx)
 685→
 686→        results_a = [_make_result("S1", "strat_a", returns_a)]
 687→        results_b = [_make_result("S2", "strat_b", returns_b)]
 688→
 689→        group_results = [
 690→            ("strat_a", {}, results_a),
 691→            ("strat_b", {}, results_b),
 692→        ]
 693→
 694→        weights = _optimize_ensemble_weights(group_results, spy_returns=spy_returns)
 695→        weights_dict = {s: w for s, _, w in weights}
 696→
 697→        # 验证前提：两个策略 alpha 都 > 0
 698→        alpha_a = _compute_alpha(_combine_daily_returns(results_a), spy_returns)
 699→        alpha_b = _compute_alpha(_combine_daily_returns(results_b), spy_returns)
 700→        assert alpha_a > 0 and alpha_b > 0
 701→
 702→        # A 的 alpha 更高 → 权重更大
 703→        assert weights_dict["strat_a"] > weights_dict["strat_b"], (
 704→            f"A 的 alpha 更高，权重应大于 B，"
 705→            f"实际 A={weights_dict['strat_a']:.4f}, B={weights_dict['strat_b']:.4f}"
 706→        )
 707→        # 权重和 = 1.0
 708→        total = sum(weights_dict.values())
 709→        assert abs(total - 1.0) < 1e-9, f"权重和应为 1.0，实际 {total:.6f}"
 710→        # 两个权重都 > 0（不是 0）
 711→        assert weights_dict["strat_a"] > 0
 712→        assert weights_dict["strat_b"] > 0
 713→
 714→    def test_ensemble_mixed_alpha_only_positive_weighted(self):
 715→        """混合 alpha：只正 alpha 参与归一化，负 alpha 权重=0。
 716→
 717→        场景：3 个策略，2 正 alpha + 1 负 alpha。
 718→        验证：负 alpha 权重=0，两个正 alpha 按比例分配，权重和=1.0。
 719→        """
 720→        n = 252
 721→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
 722→        spy_returns = pd.Series(np.random.normal(0.0004, 0.001, n), index=idx)
 723→
 724→        # A: 强正 alpha（日均 0.0020）
 725→        returns_a = pd.Series(np.random.normal(0.0020, 0.005, n), index=idx)
 726→        # B: 弱正 alpha（日均 0.0006，略 > SPY 0.0004）
 727→        returns_b = pd.Series(np.random.normal(0.0006, 0.003, n), index=idx)
 728→        # C: 负 alpha（日均 0.0001 << SPY）
 729→        returns_c = pd.Series(np.random.normal(0.0001, 0.005, n), index=idx)
 730→
 731→        results_a = [_make_result("S1", "strat_a", returns_a)]
 732→        results_b = [_make_result("S2", "strat_b", returns_b)]
 733→        results_c = [_make_result("S3", "strat_c", returns_c)]
 734→
 735→        group_results = [
 736→            ("strat_a", {}, results_a),
 737→            ("strat_b", {}, results_b),
 738→            ("strat_c", {}, results_c),
 739→        ]
 740→
 741→        # 验证前提
 742→        alpha_a = _compute_alpha(_combine_daily_returns(results_a), spy_returns)
 743→        alpha_b = _compute_alpha(_combine_daily_returns(results_b), spy_returns)
 744→        alpha_c = _compute_alpha(_combine_daily_returns(results_c), spy_returns)
 745→        assert alpha_a > 0, f"A alpha 应 > 0，实际 {alpha_a:.4f}"
 746→        assert alpha_b > 0, f"B alpha 应 > 0，实际 {alpha_b:.4f}"
 747→        assert alpha_c < 0, f"C alpha 应 < 0，实际 {alpha_c:.4f}"
 748→
 749→        weights = _optimize_ensemble_weights(group_results, spy_returns=spy_returns)
 750→        weights_dict = {s: w for s, _, w in weights}
 751→
 752→        # C（负 alpha）权重 = 0
 753→        assert weights_dict["strat_c"] == 0.0, (
 754→            f"负 alpha 策略 C 权重应为 0，实际 {weights_dict['strat_c']:.6f}"
 755→        )
 756→        # A 和 B 权重都 > 0
 757→        assert weights_dict["strat_a"] > 0
 758→        assert weights_dict["strat_b"] > 0
 759→        # A 的 alpha > B 的 alpha → A 权重 > B 权重
 760→        assert weights_dict["strat_a"] > weights_dict["strat_b"]
 761→        # 权重和 = 1.0（C=0，A+B=1.0）
 762→        total = sum(weights_dict.values())
 763→        assert abs(total - 1.0) < 1e-9
 764→
 765→    def test_ensemble_all_negative_fallback_equal(self):
 766→        """全负 alpha 退化为等权 + WARNING（防御性 fallback）。
 767→
 768→        场景：两个策略都负 alpha。
 769→        验证：权重等权（各 0.5），WARNING 日志触发。
 770→        注：上游 alpha>0 门槛应已拦截此情形，此处为防御性设计测试。
 771→        """
 772→        from loguru import logger
 773→
 774→        n = 252
 775→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
 776→        spy_returns = pd.Series(np.random.normal(0.001, 0.001, n), index=idx)
 777→
 778→        # A: 负 alpha（日均 0.0001 << SPY 0.001）
 779→        returns_a = pd.Series(np.random.normal(0.0001, 0.005, n), index=idx)
 780→        # B: 负 alpha（日均 0.0002 << SPY 0.001）
 781→        returns_b = pd.Series(np.random.normal(0.0002, 0.005, n), index=idx)
 782→
 783→        results_a = [_make_result("S1", "strat_a", returns_a)]
 784→        results_b = [_make_result("S2", "strat_b", returns_b)]
 785→
 786→        group_results = [
 787→            ("strat_a", {}, results_a),
 788→            ("strat_b", {}, results_b),
 789→        ]
 790→
 791→        # 验证前提：两个策略 alpha 都 < 0
 792→        alpha_a = _compute_alpha(_combine_daily_returns(results_a), spy_returns)
 793→        alpha_b = _compute_alpha(_combine_daily_returns(results_b), spy_returns)
 794→        assert alpha_a < 0, f"A alpha 应 < 0，实际 {alpha_a:.4f}"
 795→        assert alpha_b < 0, f"B alpha 应 < 0，实际 {alpha_b:.4f}"
 796→
 797→        # 捕获 WARNING 日志
 798→        msgs: list[str] = []
 799→        handler_id = logger.add(lambda m: msgs.append(str(m)), level="WARNING")
 800→
 801→        try:
 802→            weights = _optimize_ensemble_weights(
 803→                group_results, spy_returns=spy_returns
 804→            )
 805→        finally:
 806→            logger.remove(handler_id)
 807→
 808→        weights_dict = {s: w for s, _, w in weights}
 809→
 810→        # 全负 alpha → 等权 fallback
 811→        assert abs(weights_dict["strat_a"] - 0.5) < 1e-9, (
 812→            f"全负 alpha fallback 应等权 0.5，实际 {weights_dict['strat_a']:.6f}"
 813→        )
 814→        assert abs(weights_dict["strat_b"] - 0.5) < 1e-9, (
 815→            f"全负 alpha fallback 应等权 0.5，实际 {weights_dict['strat_b']:.6f}"
 816→        )
 817→        # WARNING 日志触发
 818→        assert any("alphas <= 0" in m for m in msgs), (
 819→            f"全负 alpha 应触发 WARNING 日志，实际捕获: {msgs}"
 820→        )
 821→
 822→    def test_ensemble_spy_unavailable_degrades_to_equal(self):
 823→        """SPY 数据不可用时 alpha=0 → 全零 alpha → 等权 fallback。
 824→
 825→        注：Iter #9 旧代码 max(0, 0.01)=0.01 也是等权，但语义是"避免零权重"。
 826→        Iter #12 新代码 max(0, 0)=0 → total=0 → 等权 fallback。
 827→        行为一致（等权），但路径不同（fallback 而非归一化）。
 828→        """
 829→        n = 100
 830→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
 831→        returns_a = pd.Series(np.random.normal(0.001, 0.005, n), index=idx)
 832→        returns_b = pd.Series(np.random.normal(0.002, 0.008, n), index=idx)
 833→
 834→        results_a = [_make_result("S1", "strat_a", returns_a)]
 835→        results_b = [_make_result("S2", "strat_b", returns_b)]
 836→
 837→        group_results = [
 838→            ("strat_a", {}, results_a),
 839→            ("strat_b", {}, results_b),
 840→        ]
 841→
 842→        # spy_returns=None → alpha=0 → 全零 → 等权 fallback
 843→        weights = _optimize_ensemble_weights(group_results, spy_returns=None)
 844→        weights_dict = {s: w for s, _, w in weights}
 845→        # 等权：各 0.5
 846→        assert abs(weights_dict["strat_a"] - 0.5) < 1e-9
 847→        assert abs(weights_dict["strat_b"] - 0.5) < 1e-9
 848→
 849→    def test_ensemble_single_strategy_returns_one(self):
 850→        """单策略时直接返回权重 1.0（与 Iter #9 行为一致）。"""
 851→        n = 100
 852→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
 853→        returns = pd.Series(np.random.normal(0.001, 0.005, n), index=idx)
 854→        results = [_make_result("S1", "strat_a", returns)]
 855→
 856→        weights = _optimize_ensemble_weights(
 857→            [("strat_a", {}, results)],
 858→            spy_returns=pd.Series(dtype=float),
 859→        )
 860→        assert len(weights) == 1
 861→        assert weights[0][0] == "strat_a"
 862→        assert weights[0][2] == 1.0
 863→
 864→
 865→# ---------------------------------------------------------------------------
 866→# Iter #16: Relaxed alpha gate (ALPHA_GATE_THRESHOLD = -2.0)
 867→# ---------------------------------------------------------------------------
 868→
 869→class TestAlphaGateRelaxedThreshold:
 870→    """迭代 #16：alpha gate 从 alpha>0 放宽至 alpha > ALPHA_GATE_THRESHOLD (-2%)。
 871→
 872→    动机见 spec §1：SPX 成分股 vs SPY 存在结构性近零 alpha，严格 alpha>0 门槛
 873→    导致 4/6 组空仓。放宽至 -2% 仍过滤"灾难性跑输"，但保留"小幅跑输"候选。
 874→    """
 875→
 876→    def test_alpha_gate_constant_exists(self):
 877→        """ALPHA_GATE_THRESHOLD 常量存在且等于 -2.0。"""
 878→        assert hasattr(
 879→            __import__("mytrader.backtest.matrix_backtest", fromlist=["matrix_backtest"]),
 880→            "ALPHA_GATE_THRESHOLD",
 881→        ), "matrix_backtest 必须导出 ALPHA_GATE_THRESHOLD 常量"
 882→        assert ALPHA_GATE_THRESHOLD == -2.0, (
 883→            f"ALPHA_GATE_THRESHOLD 应为 -2.0，实际 {ALPHA_GATE_THRESHOLD}"
 884→        )
 885→
 886→    def test_alpha_gate_relaxed_negative_alpha_passes(self):
 887→        """alpha=-1% 通过 gate（在 -2% 与 0% 之间，旧 gate 会拒绝，新 gate 通过）。
 888→
 889→        场景：单策略 alpha=-1%，健全性通过。
 890→        验证：权重正常产出（非空），no_positive_alpha=False。
 891→
 892→        实现注：用 patch _compute_alpha 返回精确 -1.0%，避免随机收益序列的方差干扰。
 893→        重点测试 gate 逻辑，不测试 alpha 计算本身（后者在 test_matrix_backtest 覆盖）。
 894→        """
 895→        n = 300
 896→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
 897→        spy_df = _make_spy_df(n, annual_return=0.10)
 898→
 899→        # 用任意正收益序列（健全性门槛需要 closed_trades>0，已由 _make_result 默认值满足）
 900→        np.random.seed(42)
 901→        returns_a = pd.Series(np.random.normal(0.0004, 0.004, n), index=idx)
 902→
 903→        # 通过 mock 精确控制 alpha = -1.0%（在 -2% 与 0% 之间）
 904→        mock_alpha = -1.0
 905→        assert ALPHA_GATE_THRESHOLD < mock_alpha < 0, (
 906→            f"测试前提失败：mock alpha 应在 (-2%, 0) 之间"
 907→        )
 908→
 909→        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
 910→            results = []
 911→            for sym, df in data.items():
 912→                if df is None or df.empty or len(df) < 30:
 913→                    continue
 914→                results.append(_make_result(sym, strategy_name, returns_a, closed_trades=10))
 915→            return results
 916→
 917→        df_up = _make_ohlcv(n, trend="up")
 918→        store = _make_store_with_spy({"AAA": df_up, "BBB": df_up}, spy_df)
 919→        universe = _make_mock_universe({"test_group": ["AAA", "BBB"]})
 920→
 921→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
 922→        report = MatrixBacktestReport(
 923→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
 924→            backtest_window="2021-01-01 ~ 2022-01-01",
 925→            groups={},
 926→        )
 927→
 928→        with patch(
 929→            "mytrader.backtest.matrix_backtest._backtest_batch",
 930→            side_effect=mock_backtest_batch,
 931→        ), patch(
 932→            "mytrader.backtest.matrix_backtest._compute_alpha",
 933→            return_value=mock_alpha,
 934→        ):
 935→            weights = mb._run_group(
 936→                group_id="test_group",
 937→                symbols=["AAA", "BBB"],
 938→                start=date(2021, 1, 1),
 939→                end=date(2022, 1, 1),
 940→                strategies=["dual_ma"],
 941→                param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 942→                report=report,
 943→            )
 944→
 945→        # 关键断言：alpha=-1% 应通过 gate（旧 gate 会拒绝）
 946→        assert len(weights) > 0, (
 947→            f"alpha=-1% 应通过 Iter #16 放宽后的 gate，实际 weights={weights}"
 948→        )
 949→        # no_positive_alpha 不应被标记
 950→        for gr in report.group_results:
 951→            if gr.group_id == "test_group":
 952→                assert gr.no_positive_alpha is False, (
 953→                    "alpha=-1% 组不应标记 no_positive_alpha=True（Iter #16 放宽后）"
 954→                )
 955→        warning_text = " ".join(report.warnings)
 956→        assert "no_positive_alpha" not in warning_text, (
 957→            f"alpha=-1% 组不应有 no_positive_alpha 警告，warnings={report.warnings}"
 958→        )
 959→
 960→    def test_alpha_gate_very_negative_fails(self):
 961→        """alpha=-5% 仍被拒绝（远低于 -2% 阈值）。
 962→
 963→        场景：单策略 alpha=-5%，健全性通过。
 964→        验证：返回空权重，no_positive_alpha=True。
 965→        """
 966→        n = 300
 967→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
 968→        spy_df = _make_spy_df(n, annual_return=0.10)
 969→
 970→        np.random.seed(42)
 971→        returns_a = pd.Series(np.random.normal(0.0004, 0.004, n), index=idx)
 972→
 973→        # mock alpha = -5.0%（远低于 -2% 阈值）
 974→        mock_alpha = -5.0
 975→        assert mock_alpha < ALPHA_GATE_THRESHOLD, (
 976→            f"测试前提失败：mock alpha 应 < {ALPHA_GATE_THRESHOLD}%"
 977→        )
 978→
 979→        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
 980→            results = []
 981→            for sym, df in data.items():
 982→                if df is None or df.empty or len(df) < 30:
 983→                    continue
 984→                results.append(_make_result(sym, strategy_name, returns_a, closed_trades=10))
 985→            return results
 986→
 987→        df_up = _make_ohlcv(n, trend="up")
 988→        store = _make_store_with_spy({"AAA": df_up, "BBB": df_up}, spy_df)
 989→        universe = _make_mock_universe({"test_group": ["AAA", "BBB"]})
 990→
 991→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
 992→        report = MatrixBacktestReport(
 993→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
 994→            backtest_window="2021-01-01 ~ 2022-01-01",
 995→            groups={},
 996→        )
 997→
 998→        with patch(
 999→            "mytrader.backtest.matrix_backtest._backtest_batch",
1000→            side_effect=mock_backtest_batch,
1001→        ), patch(
1002→            "mytrader.backtest.matrix_backtest._compute_alpha",
1003→            return_value=mock_alpha,
1004→        ):
1005→            weights = mb._run_group(
1006→                group_id="test_group",
1007→                symbols=["AAA", "BBB"],
1008→                start=date(2021, 1, 1),
1009→                end=date(2022, 1, 1),
1010→                strategies=["dual_ma"],
1011→                param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
1012→                report=report,
1013→            )
1014→
1015→        # 关键断言：alpha=-5% 应被拒绝
1016→        assert weights == [], (
1017→            f"alpha={mock_alpha}% 应被拒绝（< {ALPHA_GATE_THRESHOLD}%），实际 weights={weights}"
1018→        )
1019→        warning_text = " ".join(report.warnings)
1020→        assert "no_positive_alpha" in warning_text
1021→        for gr in report.group_results:
1022→            if gr.group_id == "test_group":
1023→                assert gr.no_positive_alpha is True
1024→
1025→    def test_alpha_gate_threshold_boundary(self):
1026→        """alpha=-2.0% 恰好在阈值边界 → 被拒绝（使用 > 严格比较）。
1027→
1028→        场景：alpha 精确等于 -2.0%（边界值）。
1029→        验证：返回空权重（因为 `c[5] > ALPHA_GATE_THRESHOLD` 是严格大于）。
1030→        """
1031→        n = 300
1032→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
1033→        spy_df = _make_spy_df(n, annual_return=0.10)
1034→
1035→        np.random.seed(42)
1036→        returns_a = pd.Series(np.random.normal(0.0004, 0.004, n), index=idx)
1037→
1038→        # mock alpha 精确等于阈值边界
1039→        mock_alpha = ALPHA_GATE_THRESHOLD  # -2.0
1040→
1041→        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
1042→            results = []
1043→            for sym, df in data.items():
1044→                if df is None or df.empty or len(df) < 30:
1045→                    continue
1046→                results.append(_make_result(sym, strategy_name, returns_a, closed_trades=10))
1047→            return results
1048→
1049→        df_up = _make_ohlcv(n, trend="up")
1050→        store = _make_store_with_spy({"AAA": df_up, "BBB": df_up}, spy_df)
1051→        universe = _make_mock_universe({"test_group": ["AAA", "BBB"]})
1052→
1053→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
1054→        report = MatrixBacktestReport(
1055→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
1056→            backtest_window="2021-01-01 ~ 2022-01-01",
1057→            groups={},
1058→        )
1059→
1060→        # patch _compute_alpha 返回精确 -2.0%（边界值）
1061→        with patch(
1062→            "mytrader.backtest.matrix_backtest._backtest_batch",
1063→            side_effect=mock_backtest_batch,
1064→        ), patch(
1065→            "mytrader.backtest.matrix_backtest._compute_alpha",
1066→            return_value=mock_alpha,
1067→        ):
1068→            weights = mb._run_group(
1069→                group_id="test_group",
1070→                symbols=["AAA", "BBB"],
1071→                start=date(2021, 1, 1),
1072→                end=date(2022, 1, 1),
1073→                strategies=["dual_ma"],
1074→                param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
1075→                report=report,
1076→            )
1077→
1078→        # 关键断言：alpha == threshold 应被拒绝（因为 c[5] > ALPHA_GATE_THRESHOLD 是严格大于）
1079→        assert weights == [], (
1080→            f"alpha == {ALPHA_GATE_THRESHOLD}% 应被拒绝（使用 > 严格比较），"
1081→            f"实际 weights={weights}"
1082→        )
1083→        warning_text = " ".join(report.warnings)
1084→        assert "no_positive_alpha" in warning_text
1085→
1086→    def test_alpha_gate_positive_alpha_passes(self):
1087→        """alpha=+1% 仍通过 gate（无回归，正 alpha 行为不变）。
1088→
1089→        场景：单策略 alpha=+1%（正 alpha）。
1090→        验证：权重正常产出，no_positive_alpha=False。
1091→        这是回归测试，确保 Iter #16 放宽不破坏正 alpha 行为。
1092→        """
1093→        n = 300
1094→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
1095→        spy_df = _make_spy_df(n, annual_return=0.10)
1096→
1097→        np.random.seed(42)
1098→        returns_a = pd.Series(np.random.normal(0.0004, 0.004, n), index=idx)
1099→
1100→        # mock alpha = +1.0%（正 alpha）
1101→        mock_alpha = 1.0
1102→        assert mock_alpha > 0
1103→
1104→        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
1105→            results = []
1106→            for sym, df in data.items():
1107→                if df is None or df.empty or len(df) < 30:
1108→                    continue
1109→                results.append(_make_result(sym, strategy_name, returns_a, closed_trades=10))
1110→            return results
1111→
1112→        df_up = _make_ohlcv(n, trend="up")
1113→        store = _make_store_with_spy({"AAA": df_up, "BBB": df_up}, spy_df)
1114→        universe = _make_mock_universe({"test_group": ["AAA", "BBB"]})
1115→
1116→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
1117→        report = MatrixBacktestReport(
1118→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
1119→            backtest_window="2021-01-01 ~ 2022-01-01",
1120→            groups={},
1121→        )
1122→
1123→        with patch(
1124→            "mytrader.backtest.matrix_backtest._backtest_batch",
1125→            side_effect=mock_backtest_batch,
1126→        ), patch(
1127→            "mytrader.backtest.matrix_backtest._compute_alpha",
1128→            return_value=mock_alpha,
1129→        ):
1130→            weights = mb._run_group(
1131→                group_id="test_group",
1132→                symbols=["AAA", "BBB"],
1133→                start=date(2021, 1, 1),
1134→                end=date(2022, 1, 1),
1135→                strategies=["dual_ma"],
1136→                param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
1137→                report=report,
1138→            )
1139→
1140→        # 正 alpha 应���常通过
1141→        assert len(weights) > 0, (
1142→            f"正 alpha 应通过 gate（无回归），实际 weights={weights}"
1143→        )
1144→        for gr in report.group_results:
1145→            if gr.group_id == "test_group":
1146→                assert gr.no_positive_alpha is False
1147→
1148→    def test_alpha_gate_relaxed_unblocks_spx(self):
1149→        """集成场景：SPX 组 alpha=-1.5% 策略入选 tier1（旧 gate 会拒绝）。
1150→
1151→        场景：模拟 Iter #15 reoptimize 中 SPX 组的情况——
1152→        策略 alpha=-1.5%（在 -2% 与 0% 之间），DD ≤ 20%，Sortino > 0.5。
1153→        验证：
1154→          - 旧 gate（alpha>0）会拒绝 → 空权重
1155→          - 新 gate（alpha>-2%）通过 → 权重非空
1156→        """
1157→        n = 300
1158→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
1159→        spy_df = _make_spy_df(n, annual_return=0.10)
1160→
1161→        np.random.seed(42)
1162→        returns_a = pd.Series(np.random.normal(0.0004, 0.004, n), index=idx)
1163→
1164→        # mock alpha = -1.5%（在 -2% 与 0% 之间，模拟 SPX near-zero alpha 场景）
1165→        mock_alpha = -1.5
1166→        assert ALPHA_GATE_THRESHOLD < mock_alpha < 0
1167→
1168→        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
1169→            results = []
1170→            for sym, df in data.items():
1171→                if df is None or df.empty or len(df) < 30:
1172→                    continue
1173→                results.append(_make_result(sym, strategy_name, returns_a, closed_trades=10))
1174→            return results
1175→
1176→        df_up = _make_ohlcv(n, trend="up")
1177→        store = _make_store_with_spy({"AAA": df_up, "BBB": df_up}, spy_df)
1178→        # 模拟 SPX 组名（仅用于语义清晰，不影响逻辑）
1179→        universe = _make_mock_universe({"SPX_mid_vol": ["AAA", "BBB"]})
1180→
1181→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
1182→        report = MatrixBacktestReport(
1183→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
1184→            backtest_window="2021-01-01 ~ 2022-01-01",
1185→            groups={},
1186→        )
1187→
1188→        with patch(
1189→            "mytrader.backtest.matrix_backtest._backtest_batch",
1190→            side_effect=mock_backtest_batch,
1191→        ), patch(
1192→            "mytrader.backtest.matrix_backtest._compute_alpha",
1193→            return_value=mock_alpha,
1194→        ):
1195→            weights = mb._run_group(
1196→                group_id="SPX_mid_vol",
1197→                symbols=["AAA", "BBB"],
1198→                start=date(2021, 1, 1),
1199→                end=date(2022, 1, 1),
1200→                strategies=["dual_ma"],
1201→                param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
1202→                report=report,
1203→            )
1204→
1205→        # 关键断言：SPX 组不再空仓
1206→        assert len(weights) > 0, (
1207→            f"SPX 组 alpha={mock_alpha}%（> {ALPHA_GATE_THRESHOLD}%）应通过 gate，"
1208→            f"实际 weights={weights}（Iter #15 此场景被 alpha>0 gate 阻塞）"
1209→        )
1210→        # backtest_alpha 字段应存在
1211→        for w in weights:
1212→            assert "backtest_alpha" in w
1213→        # no_positive_alpha 不应被标记
1214→        warning_text = " ".join(report.warnings)
1215→        assert "no_positive_alpha" not in warning_text
1216→
1217→    def test_ensemble_weights_with_negative_alpha_single_strategy(self):
1218→        """单策略 ensemble 负 alpha（> -2%）仍得 weight=1.0（早返回）。
1219→
1220→        场景：单策略 alpha=-1%（通过 Iter #16 gate），进入 ensemble。
1221→        验证：`_optimize_ensemble_weights` 的 `len == 1` 早返回路径给 weight=1.0。
1222→
1223→        注：多策略 ensemble 中负 alpha 权重仍为 0（max(a, 0.0)），
1224→        这是保守设计——正 alpha 策略应主导权重。单策略场景是特例。
1225→        """
1226→        n = 252
1227→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
1228→        spy_returns = pd.Series(np.random.normal(0.0004, 0.001, n), index=idx)
1229→
1230→        # 策略收益序列（alpha 值由 mock 控制，这里只需要非空序列）
1231→        np.random.seed(42)
1232→        returns_a = pd.Series(np.random.normal(0.00035, 0.004, n), index=idx)
1233→
1234→        results_a = [_make_result("S1", "strat_a", returns_a)]
1235→
1236→        # 单策略 ensemble（早返回路径，不计算 alpha）
1237→        weights = _optimize_ensemble_weights(
1238→            [("strat_a", {}, results_a)],
1239→            spy_returns=spy_returns,
1240→        )
1241→
1242→        # 早返回路径 → weight=1.0
1243→        assert len(weights) == 1
1244→        assert weights[0][0] == "strat_a"
1245→        assert weights[0][2] == 1.0, (
1246→            f"单策略 ensemble 应早返回 weight=1.0（不依赖 alpha 值），"
1247→            f"实际 {weights[0][2]}"
1248→        )
1249→
---
   1→"""迭代 #12：alpha>0 硬门槛测试（Reject Negative-Alpha Strategies）。
   2→
   3→迭代 #16 更新：alpha gate 从 alpha>0 放宽至 alpha > ALPHA_GATE_THRESHOLD (-2%)。
   4→动机：SPX 成分股 vs SPY benchmark 存在结构性近零 alpha，严格 alpha>0 门槛导致
   5→4/6 组空仓。放宽至 -2% 仍过滤"灾难性跑输"，但保留"小幅跑输 SPY 但 Sortino/DD
   6→优秀"的候选。WF OOS 校验仍用 -5% 单轮下限 + avg>0 汇总门槛，不削弱 OOS 验证。
   7→
   8→验证：
   9→    1. `GroupBacktestResult.no_positive_alpha` 字段默认 False
  10→    2. `_run_group` 在 candidates 构建后、Tier 1 剔除 alpha ≤ ALPHA_GATE_THRESHOLD 的候选
  11→    3. 全负 alpha（< -2%）组返回空权重 + `no_positive_alpha=True` 标记
  12→    4. 混合 alpha 组只保留 alpha > -2% 的候选
  13→    5. `_optimize_ensemble_weights` 负 alpha 策略权重为 0（不再 max(0.01) 掩盖）
  14→    6. 全负 alpha ensemble 退化为等权 + WARNING（防御性 fallback）
  15→    7. 健全性门槛 + alpha 门槛协同工作
  16→    8. [Iter #16] ALPHA_GATE_THRESHOLD 常量存在且等于 -2.0
  17→    9. [Iter #16] alpha=-1% 通过 gate（在 -2% 与 0% 之间）
  18→    10. [Iter #16] alpha=-5% 仍被拒绝
  19→    11. [Iter #16] alpha=-2.0% 边界值被拒绝（使用 > 严格比较）
  20→    12. [Iter #16] alpha=+1% 仍通过（无回归）
  21→    13. [Iter #16] 集成场景：SPX 组 alpha=-1.5% 策略入选 tier1
  22→    14. [Iter #16] 单策略 ensemble 负 alpha（> -2%）仍得 weight=1.0（早返回）
  23→
  24→背景见 `iterations/iteration_16/spec.md` + `.codebuddy/notes/experience.md` #8。
  25→"""
  26→
  27→from __future__ import annotations
  28→
  29→from datetime import date
  30→from unittest.mock import MagicMock, patch
  31→
  32→import numpy as np
  33→import pandas as pd
  34→import pytest
  35→
  36→from mytrader.backtest.matrix_backtest import (
  37→    ALPHA_GATE_THRESHOLD,
  38→    GroupBacktestResult,
  39→    MatrixBacktest,
  40→    MatrixBacktestReport,
  41→    SingleBacktestResult,
  42→    _combine_daily_returns,
  43→    _compute_alpha,
  44→    _optimize_ensemble_weights,
  45→)
  46→
  47→
  48→# ---------------------------------------------------------------------------
  49→# Test data generators（与 test_degenerate_filter.py / test_matrix_backtest.py 同风格）
  50→# ---------------------------------------------------------------------------
  51→
  52→def _make_ohlcv(
  53→    n: int = 300,
  54→    trend: str = "up",
  55→    start: str = "2021-01-01",
  56→    seed: int | None = None,
  57→) -> pd.DataFrame:
  58→    """生成测试 OHLCV 数据。"""
  59→    idx = pd.date_range(start, periods=n, freq="B")
  60→    if trend == "up":
  61→        close = np.array([100.0 + i * 0.1 for i in range(n)])
  62→    elif trend == "down":
  63→        close = np.array([100.0 - i * 0.05 for i in range(n)])
  64→    elif trend == "random":
  65→        rng = np.random.default_rng(seed if seed is not None else 42)
  66→        steps = rng.normal(0, 0.5, n)
  67→        close = np.cumsum(np.concatenate([[100.0], steps]))[1:]
  68→    else:
  69→        raise ValueError(f"unknown trend: {trend}")
  70→
  71→    return pd.DataFrame(
  72→        {
  73→            "open":   close - 0.5,
  74→            "high":   close + 1.0,
  75→            "low":    close - 1.0,
  76→            "close":  close,
  77→            "volume": [1_000_000] * n,
  78→        },
  79→        index=idx,
  80→    )
  81→
  82→
  83→def _make_spy_df(n: int = 300, annual_return: float = 0.10) -> pd.DataFrame:
  84→    """生成 SPY benchmark 数据，年化收益可调。
  85→
  86→    annual_return=0.10 → 日均收益 ≈ 0.00038（对数展开近似）。
  87→    annual_return=0.30 → 日均收益 ≈ 0.00107（高涨幅，策略难跑赢）。
  88→    """
  89→    idx = pd.date_range("2021-01-01", periods=n, freq="B")
  90→    daily_rate = (1.0 + annual_return) ** (1.0 / 252) - 1.0
  91→    close = [100.0 * ((1.0 + daily_rate) ** i) for i in range(n)]
  92→    return pd.DataFrame(
  93→        {
  94→            "open":   [c - 0.1 for c in close],
  95→            "high":   [c + 0.5 for c in close],
  96→            "low":    [c - 0.5 for c in close],
  97→            "close":  close,
  98→            "volume": [1_000_000] * n,
  99→        },
 100→        index=idx,
 101→    )
 102→
 103→
 104→def _make_store_with_spy(
 105→    symbols_data: dict[str, pd.DataFrame],
 106→    spy_df: pd.DataFrame,
 107→) -> MagicMock:
 108→    """构造 Mock MarketDataStore，含 SPY benchmark 数据。"""
 109→    store = MagicMock()
 110→    mapping = dict(symbols_data)
 111→    mapping["SPY"] = spy_df
 112→
 113→    def get_bars_multi(symbols, start, end, timeframe="1d"):
 114→        return {s: mapping[s] for s in symbols if s in mapping}
 115→
 116→    store.get_bars_multi.side_effect = get_bars_multi
 117→    return store
 118→
 119→
 120→def _make_mock_universe(groups: dict[str, list[str]]) -> MagicMock:
 121→    """构造 Mock UniverseManager。"""
 122→    universe = MagicMock()
 123→    universe.get_groups.return_value = groups
 124→    return universe
 125→
 126→
 127→def _make_result(
 128→    symbol: str,
 129→    strategy: str,
 130→    daily_returns: pd.Series,
 131→    closed_trades: int = 10,
 132→) -> SingleBacktestResult:
 133→    """快捷构造 SingleBacktestResult（带默认字段）。"""
 134→    return SingleBacktestResult(
 135→        symbol=symbol,
 136→        strategy=strategy,
 137→        params={},
 138→        sharpe=1.0,
 139→        total_return_pct=10.0,
 140→        max_drawdown_pct=5.0,
 141→        win_rate_pct=55.0,
 142→        total_trades=10,
 143→        daily_returns=daily_returns,
 144→        closed_trades=closed_trades,
 145→    )
 146→
 147→
 148→# ---------------------------------------------------------------------------
 149→# Test 1: no_positive_alpha 字段
 150→# ---------------------------------------------------------------------------
 151→
 152→class TestNoPositiveAlphaField:
 153→    """GroupBacktestResult.no_positive_alpha 字段测试。"""
 154→
 155→    def test_no_positive_alpha_field_default_false(self):
 156→        """GroupBacktestResult.no_positive_alpha 默认 False。"""
 157→        gr = GroupBacktestResult(
 158→            group_id="g", strategy="s", params={}, portfolio_sharpe=0.0,
 159→            avg_total_return_pct=0.0, avg_max_drawdown_pct=0.0,
 160→            avg_win_rate_pct=0.0, symbol_count=0,
 161→        )
 162→        assert hasattr(gr, "no_positive_alpha"), (
 163→            "GroupBacktestResult 必须有 no_positive_alpha 字段"
 164→        )
 165→        assert gr.no_positive_alpha is False, (
 166→            "no_positive_alpha 默认应为 False"
 167→        )
 168→
 169→    def test_no_positive_alpha_field_settable(self):
 170→        """no_positive_alpha 可被设置为 True。"""
 171→        gr = GroupBacktestResult(
 172→            group_id="g", strategy="s", params={}, portfolio_sharpe=0.0,
 173→            avg_total_return_pct=0.0, avg_max_drawdown_pct=0.0,
 174→            avg_win_rate_pct=0.0, symbol_count=0,
 175→            no_positive_alpha=True,
 176→        )
 177→        assert gr.no_positive_alpha is True
 178→
 179→
 180→# ---------------------------------------------------------------------------
 181→# Test 2-3: _run_group alpha>0 门槛集成
 182→# ---------------------------------------------------------------------------
 183→
 184→class TestRunGroupAlphaGate:
 185→    """_run_group alpha>0 硬门槛集成测试。"""
 186→
 187→    def test_positive_alpha_candidates_pass(self):
 188→        """全正 alpha 候选组正常产出权重，no_positive_alpha=False。
 189→
 190→        场景：两个策略都跑赢 SPY（正 alpha），健全性门槛通过。
 191→        验证：权重正常产出，no_positive_alpha 不被标记。
 192→        """
 193→        n = 300
 194→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
 195→        # SPY 年化 ~10%
 196→        spy_df = _make_spy_df(n, annual_return=0.10)
 197→        spy_returns = spy_df["close"].pct_change().dropna()
 198→
 199→        # 策略收益：日均 0.0012（年化 ~35%）→ 正 alpha
 200→        np.random.seed(42)
 201→        returns_a = pd.Series(np.random.normal(0.0012, 0.005, n), index=idx)
 202→        returns_b = pd.Series(np.random.normal(0.0010, 0.004, n), index=idx)
 203→
 204→        # 验证前提：两个策略 alpha 都 > 0
 205→        alpha_a = _compute_alpha(returns_a, spy_returns)
 206→        alpha_b = _compute_alpha(returns_b, spy_returns)
 207→        assert alpha_a > 0, f"策略 A alpha 应 > 0，实际 {alpha_a:.4f}"
 208→        assert alpha_b > 0, f"策略 B alpha 应 > 0，实际 {alpha_b:.4f}"
 209→
 210→        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
 211→            results = []
 212→            for sym, df in data.items():
 213→                if df is None or df.empty or len(df) < 30:
 214→                    continue
 215→                returns = returns_a if strategy_name == "dual_ma" else returns_b
 216→                results.append(_make_result(sym, strategy_name, returns, closed_trades=10))
 217→            return results
 218→
 219→        df_up = _make_ohlcv(n, trend="up")
 220→        store = _make_store_with_spy({"AAA": df_up, "BBB": df_up}, spy_df)
 221→        universe = _make_mock_universe({"test_group": ["AAA", "BBB"]})
 222→
 223→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
 224→        report = MatrixBacktestReport(
 225→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
 226→            backtest_window="2021-01-01 ~ 2022-01-01",
 227→            groups={},
 228→        )
 229→
 230→        with patch(
 231→            "mytrader.backtest.matrix_backtest._backtest_batch",
 232→            side_effect=mock_backtest_batch,
 233→        ):
 234→            weights = mb._run_group(
 235→                group_id="test_group",
 236→                symbols=["AAA", "BBB"],
 237→                start=date(2021, 1, 1),
 238→                end=date(2022, 1, 1),
 239→                strategies=["dual_ma", "rsi_mean_revert"],
 240→                param_grids={
 241→                    "dual_ma": {"fast": [5], "slow": [20]},
 242→                    "rsi_mean_revert": {
 243→                        "period": [14], "oversold": [30], "overbought": [70]
 244→                    },
 245→                },
 246→                report=report,
 247→            )
 248→
 249→        # 正 alpha 候选 → 权重正常产出
 250→        assert len(weights) > 0, (
 251→            f"全正 alpha 组应产出权重，实际 weights={weights}"
 252→        )
 253→        # no_positive_alpha 不应被标记
 254→        for gr in report.group_results:
 255→            if gr.group_id == "test_group":
 256→                assert gr.no_positive_alpha is False, (
 257→                    "全正 alpha 组不应标记 no_positive_alpha=True"
 258→                )
 259→        # report.warnings 不含 no_positive_alpha
 260→        warning_text = " ".join(report.warnings)
 261→        assert "no_positive_alpha" not in warning_text, (
 262→            f"全正 alpha 组不应有 no_positive_alpha 警告，实际 warnings={report.warnings}"
 263→        )
 264→
 265→    def test_all_negative_alpha_group_empty(self):
 266→        """全负 alpha 组返回空权重 + no_positive_alpha=True 标记。
 267→
 268→        场景：两个策略都跑输 SPY（负 alpha），健全性门槛通过。
 269→        验证：返回空 weights，report.warnings 含 no_positive_alpha 标记，
 270→              group_results 条目 no_positive_alpha=True。
 271→        """
 272→        n = 300
 273→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
 274→        # SPY 年化 ~30%（高涨幅，策略难跑赢）
 275→        spy_df = _make_spy_df(n, annual_return=0.30)
 276→        spy_returns = spy_df["close"].pct_change().dropna()
 277→
 278→        # 策略收益：日均 0.0003（年化 ~8%）→ 负 alpha（跑输 SPY 30%）
 279→        np.random.seed(42)
 280→        returns_a = pd.Series(np.random.normal(0.0003, 0.005, n), index=idx)
 281→        returns_b = pd.Series(np.random.normal(0.0002, 0.004, n), index=idx)
 282→
 283→        # 验证前提：两个策略 alpha 都 < 0
 284→        alpha_a = _compute_alpha(returns_a, spy_returns)
 285→        alpha_b = _compute_alpha(returns_b, spy_returns)
 286→        assert alpha_a < 0, f"策略 A alpha 应 < 0，实际 {alpha_a:.4f}"
 287→        assert alpha_b < 0, f"策略 B alpha 应 < 0，实际 {alpha_b:.4f}"
 288→
 289→        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
 290→            results = []
 291→            for sym, df in data.items():
 292→                if df is None or df.empty or len(df) < 30:
 293→                    continue
 294→                returns = returns_a if strategy_name == "dual_ma" else returns_b
 295→                results.append(_make_result(sym, strategy_name, returns, closed_trades=10))
 296→            return results
 297→
 298→        df_up = _make_ohlcv(n, trend="up")
 299→        store = _make_store_with_spy({"AAA": df_up, "BBB": df_up}, spy_df)
 300→        universe = _make_mock_universe({"test_group": ["AAA", "BBB"]})
 301→
 302→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
 303→        report = MatrixBacktestReport(
 304→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
 305→            backtest_window="2021-01-01 ~ 2022-01-01",
 306→            groups={},
 307→        )
 308→
 309→        with patch(
 310→            "mytrader.backtest.matrix_backtest._backtest_batch",
 311→            side_effect=mock_backtest_batch,
 312→        ):
 313→            weights = mb._run_group(
 314→                group_id="test_group",
 315→                symbols=["AAA", "BBB"],
 316→                start=date(2021, 1, 1),
 317→                end=date(2022, 1, 1),
 318→                strategies=["dual_ma", "rsi_mean_revert"],
 319→                param_grids={
 320→                    "dual_ma": {"fast": [5], "slow": [20]},
 321→                    "rsi_mean_revert": {
 322→                        "period": [14], "oversold": [30], "overbought": [70]
 323→                    },
 324→                },
 325→                report=report,
 326→            )
 327→
 328→        # 全负 alpha → 空权重
 329→        assert weights == [], (
 330→            f"全负 alpha 组应返回空权重，实际 weights={weights}"
 331→        )
 332→        # report.warnings 含 no_positive_alpha 标记
 333→        warning_text = " ".join(report.warnings)
 334→        assert "no_positive_alpha" in warning_text, (
 335→            f"report.warnings 应含 no_positive_alpha 标记，"
 336→            f"实际 warnings={report.warnings}"
 337→        )
 338→        assert "test_group" in warning_text
 339→        # group_results 条目被标记 no_positive_alpha=True
 340→        test_group_results = [
 341→            gr for gr in report.group_results if gr.group_id == "test_group"
 342→        ]
 343→        assert len(test_group_results) > 0, (
 344→            "test_group 应在 report.group_results 中有存档条目（供审计追溯）"
 345→        )
 346→        for gr in test_group_results:
 347→            assert gr.no_positive_alpha is True, (
 348→                f"test_group 的 no_positive_alpha 应为 True，"
 349→                f"实际 {gr.no_positive_alpha}"
 350→            )
 351→            # no_valid_strategy 应仍为 False（健全性门槛没触发）
 352→            assert gr.no_valid_strategy is False, (
 353→                "全负 alpha 但非退化组，no_valid_strategy 应为 False"
 354→            )
 355→
 356→    def test_negative_alpha_excluded(self):
 357→        """混合 alpha 候选组：负 alpha 不出现在 weights_list。
 358→
 359→        场景：dual_ma 负 alpha，rsi_mean_revert 正 alpha。
 360→        验证：只有 rsi_mean_revert 出现在 weights，dual_ma 被 alpha 门槛剔除。
 361→        """
 362→        n = 300
 363→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
 364→        spy_df = _make_spy_df(n, annual_return=0.10)
 365→        spy_returns = spy_df["close"].pct_change().dropna()
 366→
 367→        # dual_ma：日均 0.0002（年化 ~5%）→ 负 alpha（跑输 SPY 10%）
 368→        np.random.seed(42)
 369→        returns_a = pd.Series(np.random.normal(0.0002, 0.005, n), index=idx)
 370→        # rsi_mean_revert：日均 0.0015（年化 ~45%）→ 正 alpha
 371→        returns_b = pd.Series(np.random.normal(0.0015, 0.006, n), index=idx)
 372→
 373→        # 验证前提
 374→        alpha_a = _compute_alpha(returns_a, spy_returns)
 375→        alpha_b = _compute_alpha(returns_b, spy_returns)
 376→        assert alpha_a < 0, f"dual_ma alpha 应 < 0，实际 {alpha_a:.4f}"
 377→        assert alpha_b > 0, f"rsi_mean_revert alpha 应 > 0，实际 {alpha_b:.4f}"
 378→
 379→        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
 380→            results = []
 381→            for sym, df in data.items():
 382→                if df is None or df.empty or len(df) < 30:
 383→                    continue
 384→                returns = returns_a if strategy_name == "dual_ma" else returns_b
 385→                results.append(_make_result(sym, strategy_name, returns, closed_trades=10))
 386→            return results
 387→
 388→        df_up = _make_ohlcv(n, trend="up")
 389→        store = _make_store_with_spy({"AAA": df_up, "BBB": df_up}, spy_df)
 390→        universe = _make_mock_universe({"test_group": ["AAA", "BBB"]})
 391→
 392→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
 393→        report = MatrixBacktestReport(
 394→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
 395→            backtest_window="2021-01-01 ~ 2022-01-01",
 396→            groups={},
 397→        )
 398→
 399→        with patch(
 400→            "mytrader.backtest.matrix_backtest._backtest_batch",
 401→            side_effect=mock_backtest_batch,
 402→        ):
 403→            weights = mb._run_group(
 404→                group_id="test_group",
 405→                symbols=["AAA", "BBB"],
 406→                start=date(2021, 1, 1),
 407→                end=date(2022, 1, 1),
 408→                strategies=["dual_ma", "rsi_mean_revert"],
 409→                param_grids={
 410→                    "dual_ma": {"fast": [5], "slow": [20]},
 411→                    "rsi_mean_revert": {
 412→                        "period": [14], "oversold": [30], "overbought": [70]
 413→                    },
 414→                },
 415→                report=report,
 416→            )
 417→
 418→        # 负 alpha 的 dual_ma 不应在权重中
 419→        strategies_in_weights = [w["strategy"] for w in weights]
 420→        assert "dual_ma" not in strategies_in_weights, (
 421→            f"dual_ma（负 alpha）不应出现在权重中，实际 weights={strategies_in_weights}"
 422→        )
 423→        assert "rsi_mean_revert" in strategies_in_weights, (
 424→            f"rsi_mean_revert（正 alpha）应在权重中，实际 weights={strategies_in_weights}"
 425→        )
 426→        # no_positive_alpha 不应被标记（因为有正 alpha 候选通过）
 427→        for gr in report.group_results:
 428→            if gr.group_id == "test_group":
 429→                assert gr.no_positive_alpha is False
 430→
 431→
 432→# ---------------------------------------------------------------------------
 433→# Test 4: 健全性门槛 + alpha>0 门槛协同
 434→# ---------------------------------------------------------------------------
 435→
 436→class TestSanityGateAndAlphaGateCoordination:
 437→    """健全性门槛（Iter #11）+ alpha>0 门槛（Iter #12）协同工作。"""
 438→
 439→    def test_alpha_gate_after_sanity_gate(self):
 440→        """健全性门槛先剔除退化策略，alpha 门槛再剔除负 alpha 策略。
 441→
 442→        场景：3 个策略
 443→          - dual_ma: 退化（closed_trades=0）→ 健全性门槛剔除
 444→          - rsi_mean_revert: 正常但负 alpha → alpha 门槛剔除
 445→          - bollinger_band: 正常且正 alpha → 应入选
 446→
 447→        验证：只有 bollinger_band 出现在 weights。
 448→        """
 449→        n = 300
 450→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
 451→        spy_df = _make_spy_df(n, annual_return=0.10)
 452→        spy_returns = spy_df["close"].pct_change().dropna()
 453→
 454→        np.random.seed(42)
 455→        # dual_ma: 退化（closed_trades=0）+ 正 alpha（但健全性门槛先剔除）
 456→        returns_degenerate = pd.Series(np.random.normal(0.0015, 0.005, n), index=idx)
 457→        # rsi_mean_revert: 正常（closed_trades>0）+ 负 alpha
 458→        returns_negative_alpha = pd.Series(np.random.normal(0.0002, 0.004, n), index=idx)
 459→        # bollinger_band: 正常（closed_trades>0）+ 正 alpha
 460→        returns_positive_alpha = pd.Series(np.random.normal(0.0014, 0.005, n), index=idx)
 461→
 462→        # 验证前提
 463→        alpha_neg = _compute_alpha(returns_negative_alpha, spy_returns)
 464→        alpha_pos = _compute_alpha(returns_positive_alpha, spy_returns)
 465→        assert alpha_neg < 0, f"rsi_mean_revert alpha 应 < 0，实际 {alpha_neg:.4f}"
 466→        assert alpha_pos > 0, f"bollinger_band alpha 应 > 0，实际 {alpha_pos:.4f}"
 467→
 468→        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
 469→            results = []
 470→            for sym, df in data.items():
 471→                if df is None or df.empty or len(df) < 30:
 472→                    continue
 473→                if strategy_name == "dual_ma":
 474→                    # 退化：closed_trades=0
 475→                    results.append(_make_result(
 476→                        sym, strategy_name, returns_degenerate, closed_trades=0
 477→                    ))
 478→                elif strategy_name == "rsi_mean_revert":
 479→                    # 正常但负 alpha
 480→                    results.append(_make_result(
 481→                        sym, strategy_name, returns_negative_alpha, closed_trades=10
 482→                    ))
 483→                else:  # bollinger_band
 484→                    # 正常且正 alpha
 485→                    results.append(_make_result(
 486→                        sym, strategy_name, returns_positive_alpha, closed_trades=10
 487→                    ))
 488→            return results
 489→
 490→        df_up = _make_ohlcv(n, trend="up")
 491→        # 5 标的让退化比例 5/5=100% ≥ 0.8
 492→        store = _make_store_with_spy(
 493→            {"AAA": df_up, "BBB": df_up, "CCC": df_up, "DDD": df_up, "EEE": df_up},
 494→            spy_df,
 495→        )
 496→        universe = _make_mock_universe(
 497→            {"test_group": ["AAA", "BBB", "CCC", "DDD", "EEE"]}
 498→        )
 499→
 500→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=3)
 501→        report = MatrixBacktestReport(
 502→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
 503→            backtest_window="2021-01-01 ~ 2022-01-01",
 504→            groups={},
 505→        )
 506→
 507→        with patch(
 508→            "mytrader.backtest.matrix_backtest._backtest_batch",
 509→            side_effect=mock_backtest_batch,
 510→        ):
 511→            weights = mb._run_group(
 512→                group_id="test_group",
 513→                symbols=["AAA", "BBB", "CCC", "DDD", "EEE"],
 514→                start=date(2021, 1, 1),
 515→                end=date(2022, 1, 1),
 516→                strategies=["dual_ma", "rsi_mean_revert", "bollinger_band"],
 517→                param_grids={
 518→                    "dual_ma": {"fast": [5], "slow": [20]},
 519→                    "rsi_mean_revert": {
 520→                        "period": [14], "oversold": [30], "overbought": [70]
 521→                    },
 522→                    "bollinger_band": {"period": [20], "std_dev": [2.0]},
 523→                },
 524→                report=report,
 525→            )
 526→
 527→        # 只有 bollinger_band 应出现在权重中
 528→        strategies_in_weights = [w["strategy"] for w in weights]
 529→        assert "dual_ma" not in strategies_in_weights, (
 530→            f"dual_ma（退化）应被健全性门槛剔除，实际 weights={strategies_in_weights}"
 531→        )
 532→        assert "rsi_mean_revert" not in strategies_in_weights, (
 533→            f"rsi_mean_revert（负 alpha）应被 alpha 门槛剔除，"
 534→            f"实际 weights={strategies_in_weights}"
 535→        )
 536→        assert "bollinger_band" in strategies_in_weights, (
 537→            f"bollinger_band（正常 + 正 alpha）应入选，"
 538→            f"实际 weights={strategies_in_weights}"
 539→        )
 540→
 541→    def test_degenerate_takes_precedence_over_alpha_gate(self):
 542→        """全退化组触发 no_valid_strategy（先于 alpha 门槛），不触发 no_positive_alpha。
 543→
 544→        场景：所有策略都退化（closed_trades=0）。
 545→        验证：返回空权重，标记 no_valid_strategy=True，no_positive_alpha=False
 546→              （健全性门槛先返回，alpha 门槛未到达）。
 547→        """
 548→        n = 300
 549→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
 550→        spy_df = _make_spy_df(n, annual_return=0.10)
 551→
 552→        np.random.seed(42)
 553→        returns_a = pd.Series(np.random.normal(0.001, 0.005, n), index=idx)
 554→        returns_b = pd.Series(np.random.normal(0.0008, 0.003, n), index=idx)
 555→
 556→        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
 557→            results = []
 558→            for sym, df in data.items():
 559→                if df is None or df.empty or len(df) < 30:
 560→                    continue
 561→                returns = returns_a if strategy_name == "dual_ma" else returns_b
 562→                # 全退化：closed_trades=0
 563→                results.append(_make_result(sym, strategy_name, returns, closed_trades=0))
 564→            return results
 565→
 566→        df_up = _make_ohlcv(n, trend="up")
 567→        store = _make_store_with_spy(
 568→            {"AAA": df_up, "BBB": df_up, "CCC": df_up, "DDD": df_up, "EEE": df_up},
 569→            spy_df,
 570→        )
 571→        universe = _make_mock_universe(
 572→            {"test_group": ["AAA", "BBB", "CCC", "DDD", "EEE"]}
 573→        )
 574→
 575→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
 576→        report = MatrixBacktestReport(
 577→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
 578→            backtest_window="2021-01-01 ~ 2022-01-01",
 579→            groups={},
 580→        )
 581→
 582→        with patch(
 583→            "mytrader.backtest.matrix_backtest._backtest_batch",
 584→            side_effect=mock_backtest_batch,
 585→        ):
 586→            weights = mb._run_group(
 587→                group_id="test_group",
 588→                symbols=["AAA", "BBB", "CCC", "DDD", "EEE"],
 589→                start=date(2021, 1, 1),
 590→                end=date(2022, 1, 1),
 591→                strategies=["dual_ma", "rsi_mean_revert"],
 592→                param_grids={
 593→                    "dual_ma": {"fast": [5], "slow": [20]},
 594→                    "rsi_mean_revert": {
 595→                        "period": [14], "oversold": [30], "overbought": [70]
 596→                    },
 597→                },
 598→                report=report,
 599→            )
 600→
 601→        # 全退化 → 空权重
 602→        assert weights == []
 603→        # 健全性门槛先返回 → no_valid_strategy=True
 604→        warning_text = " ".join(report.warnings)
 605→        assert "no_valid_strategy" in warning_text
 606→        # alpha 门槛未到达 → no_positive_alpha 不应被标记
 607→        assert "no_positive_alpha" not in warning_text, (
 608→            f"全退化组应触发 no_valid_strategy（先于 alpha 门槛），"
 609→            f"不应触发 no_positive_alpha，warnings={report.warnings}"
 610→        )
 611→        for gr in report.group_results:
 612→            if gr.group_id == "test_group":
 613→                assert gr.no_valid_strategy is True
 614→                assert gr.no_positive_alpha is False
 615→
 616→
 617→# ---------------------------------------------------------------------------
 618→# Test 5-8: _optimize_ensemble_weights 负 alpha 归一化
 619→# ---------------------------------------------------------------------------
 620→
 621→class TestEnsembleWeightsNegativeAlpha:
 622→    """_optimize_ensemble_weights 负 alpha 归一化测试（迭代 #12 修复）。"""
 623→
 624→    def test_ensemble_negative_alpha_zero_weight(self):
 625→        """负 alpha 策略权重为 0（不再被 max(0.01) 掩盖成等权）。
 626→
 627→        场景：策略 A 正 alpha=10%，策略 B 负 alpha=-5%。
 628→        旧代码：max(-5, 0.01)=0.01, max(10, 0.01)=10 → 权重 ≈ 0.001 / 0.999
 629→        新代码：max(-5, 0)=0, max(10, 0)=10 → 权重 = 0.0 / 1.0
 630→        验证：B 的权重严格为 0，A 的权重为 1.0。
 631→        """
 632→        n = 252
 633→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
 634→        spy_returns = pd.Series(np.random.normal(0.0004, 0.001, n), index=idx)
 635→
 636→        # A: 正 alpha（日均 0.0012 >> SPY 0.0004）
 637→        returns_a = pd.Series(np.random.normal(0.0012, 0.005, n), index=idx)
 638→        # B: 负 alpha（日均 0.0001 << SPY 0.0004）
 639→        returns_b = pd.Series(np.random.normal(0.0001, 0.005, n), index=idx)
 640→
 641→        results_a = [_make_result("S1", "strat_a", returns_a)]
 642→        results_b = [_make_result("S2", "strat_b", returns_b)]
 643→
 644→        group_results = [
 645→            ("strat_a", {}, results_a),
 646→            ("strat_b", {}, results_b),
 647→        ]
 648→
 649→        weights = _optimize_ensemble_weights(group_results, spy_returns=spy_returns)
 650→        weights_dict = {s: w for s, _, w in weights}
 651→
 652→        # 验证前提：A 的 alpha > 0，B 的 alpha < 0
 653→        alpha_a = _compute_alpha(
 654→            _combine_daily_returns(results_a), spy_returns
 655→        )
 656→        alpha_b = _compute_alpha(
 657→            _combine_daily_returns(results_b), spy_returns
 658→        )
 659→        assert alpha_a > 0, f"A 的 alpha 应 > 0，实际 {alpha_a:.4f}"
 660→        assert alpha_b < 0, f"B 的 alpha 应 < 0，实际 {alpha_b:.4f}"
 661→
 662→        # B（负 alpha）权重应为 0
 663→        assert weights_dict["strat_b"] == 0.0, (
 664→            f"负 alpha 策略权重应为 0，实际 {weights_dict['strat_b']:.6f}"
 665→        )
 666→        # A（正 alpha）权重应为 1.0
 667→        assert abs(weights_dict["strat_a"] - 1.0) < 1e-9, (
 668→            f"全正 alpha 归一化后 A 权重应为 1.0，"
 669→            f"实际 {weights_dict['strat_a']:.6f}"
 670→        )
 671→        # 权重和 = 1.0
 672→        total = sum(weights_dict.values())
 673→        assert abs(total - 1.0) < 1e-9
 674→
 675→    def test_ensemble_all_positive_normalizes(self):
 676→        """全正 alpha 正常归一化（权重和=1.0，高 alpha 权重大）。"""
 677→        n = 252
 678→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
 679→        spy_returns = pd.Series(np.random.normal(0.0004, 0.001, n), index=idx)
 680→
 681→        # A: 高 alpha（日均 0.0015）
 682→        returns_a = pd.Series(np.random.normal(0.0015, 0.005, n), index=idx)
 683→        # B: 低 alpha（日均 0.0008，仍 > SPY 0.0004）
 684→        returns_b = pd.Series(np.random.normal(0.0008, 0.003, n), index=idx)
 685→
 686→        results_a = [_make_result("S1", "strat_a", returns_a)]
 687→        results_b = [_make_result("S2", "strat_b", returns_b)]
 688→
 689→        group_results = [
 690→            ("strat_a", {}, results_a),
 691→            ("strat_b", {}, results_b),
 692→        ]
 693→
 694→        weights = _optimize_ensemble_weights(group_results, spy_returns=spy_returns)
 695→        weights_dict = {s: w for s, _, w in weights}
 696→
 697→        # 验证前提：两个策略 alpha 都 > 0
 698→        alpha_a = _compute_alpha(_combine_daily_returns(results_a), spy_returns)
 699→        alpha_b = _compute_alpha(_combine_daily_returns(results_b), spy_returns)
 700→        assert alpha_a > 0 and alpha_b > 0
 701→
 702→        # A 的 alpha 更高 → 权重更大
 703→        assert weights_dict["strat_a"] > weights_dict["strat_b"], (
 704→            f"A 的 alpha 更高，权重应大于 B，"
 705→            f"实际 A={weights_dict['strat_a']:.4f}, B={weights_dict['strat_b']:.4f}"
 706→        )
 707→        # 权重和 = 1.0
 708→        total = sum(weights_dict.values())
 709→        assert abs(total - 1.0) < 1e-9, f"权重和应为 1.0，实际 {total:.6f}"
 710→        # 两个权重都 > 0（不是 0）
 711→        assert weights_dict["strat_a"] > 0
 712→        assert weights_dict["strat_b"] > 0
 713→
 714→    def test_ensemble_mixed_alpha_only_positive_weighted(self):
 715→        """混合 alpha：只正 alpha 参与归一化，负 alpha 权重=0。
 716→
 717→        场景：3 个策略，2 正 alpha + 1 负 alpha。
 718→        验证：负 alpha 权重=0，两个正 alpha 按比例分配，权重和=1.0。
 719→        """
 720→        n = 252
 721→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
 722→        spy_returns = pd.Series(np.random.normal(0.0004, 0.001, n), index=idx)
 723→
 724→        # A: 强正 alpha（日均 0.0020）
 725→        returns_a = pd.Series(np.random.normal(0.0020, 0.005, n), index=idx)
 726→        # B: 弱正 alpha（日均 0.0006，略 > SPY 0.0004）
 727→        returns_b = pd.Series(np.random.normal(0.0006, 0.003, n), index=idx)
 728→        # C: 负 alpha（日均 0.0001 << SPY）
 729→        returns_c = pd.Series(np.random.normal(0.0001, 0.005, n), index=idx)
 730→
 731→        results_a = [_make_result("S1", "strat_a", returns_a)]
 732→        results_b = [_make_result("S2", "strat_b", returns_b)]
 733→        results_c = [_make_result("S3", "strat_c", returns_c)]
 734→
 735→        group_results = [
 736→            ("strat_a", {}, results_a),
 737→            ("strat_b", {}, results_b),
 738→            ("strat_c", {}, results_c),
 739→        ]
 740→
 741→        # 验证前提
 742→        alpha_a = _compute_alpha(_combine_daily_returns(results_a), spy_returns)
 743→        alpha_b = _compute_alpha(_combine_daily_returns(results_b), spy_returns)
 744→        alpha_c = _compute_alpha(_combine_daily_returns(results_c), spy_returns)
 745→        assert alpha_a > 0, f"A alpha 应 > 0，实际 {alpha_a:.4f}"
 746→        assert alpha_b > 0, f"B alpha 应 > 0，实际 {alpha_b:.4f}"
 747→        assert alpha_c < 0, f"C alpha 应 < 0，实际 {alpha_c:.4f}"
 748→
 749→        weights = _optimize_ensemble_weights(group_results, spy_returns=spy_returns)
 750→        weights_dict = {s: w for s, _, w in weights}
 751→
 752→        # C（负 alpha）权重 = 0
 753→        assert weights_dict["strat_c"] == 0.0, (
 754→            f"负 alpha 策略 C 权重应为 0，实际 {weights_dict['strat_c']:.6f}"
 755→        )
 756→        # A 和 B 权重都 > 0
 757→        assert weights_dict["strat_a"] > 0
 758→        assert weights_dict["strat_b"] > 0
 759→        # A 的 alpha > B 的 alpha → A 权重 > B 权重
 760→        assert weights_dict["strat_a"] > weights_dict["strat_b"]
 761→        # 权重和 = 1.0（C=0，A+B=1.0）
 762→        total = sum(weights_dict.values())
 763→        assert abs(total - 1.0) < 1e-9
 764→
 765→    def test_ensemble_all_negative_fallback_equal(self):
 766→        """全负 alpha 退化为等权 + WARNING（防御性 fallback）。
 767→
 768→        场景：两个策略都负 alpha。
 769→        验证：权重等权（各 0.5），WARNING 日志触发。
 770→        注：上游 alpha>0 门槛应已拦截此情形，此处为防御性设计测试。
 771→        """
 772→        from loguru import logger
 773→
 774→        n = 252
 775→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
 776→        spy_returns = pd.Series(np.random.normal(0.001, 0.001, n), index=idx)
 777→
 778→        # A: 负 alpha（日均 0.0001 << SPY 0.001）
 779→        returns_a = pd.Series(np.random.normal(0.0001, 0.005, n), index=idx)
 780→        # B: 负 alpha（日均 0.0002 << SPY 0.001）
 781→        returns_b = pd.Series(np.random.normal(0.0002, 0.005, n), index=idx)
 782→
 783→        results_a = [_make_result("S1", "strat_a", returns_a)]
 784→        results_b = [_make_result("S2", "strat_b", returns_b)]
 785→
 786→        group_results = [
 787→            ("strat_a", {}, results_a),
 788→            ("strat_b", {}, results_b),
 789→        ]
 790→
 791→        # 验证前提：两个策略 alpha 都 < 0
 792→        alpha_a = _compute_alpha(_combine_daily_returns(results_a), spy_returns)
 793→        alpha_b = _compute_alpha(_combine_daily_returns(results_b), spy_returns)
 794→        assert alpha_a < 0, f"A alpha 应 < 0，实际 {alpha_a:.4f}"
 795→        assert alpha_b < 0, f"B alpha 应 < 0，实际 {alpha_b:.4f}"
 796→
 797→        # 捕获 WARNING 日志
 798→        msgs: list[str] = []
 799→        handler_id = logger.add(lambda m: msgs.append(str(m)), level="WARNING")
 800→
 801→        try:
 802→            weights = _optimize_ensemble_weights(
 803→                group_results, spy_returns=spy_returns
 804→            )
 805→        finally:
 806→            logger.remove(handler_id)
 807→
 808→        weights_dict = {s: w for s, _, w in weights}
 809→
 810→        # 全负 alpha → 等权 fallback
 811→        assert abs(weights_dict["strat_a"] - 0.5) < 1e-9, (
 812→            f"全负 alpha fallback 应等权 0.5，实际 {weights_dict['strat_a']:.6f}"
 813→        )
 814→        assert abs(weights_dict["strat_b"] - 0.5) < 1e-9, (
 815→            f"全负 alpha fallback 应等权 0.5，实际 {weights_dict['strat_b']:.6f}"
 816→        )
 817→        # WARNING 日志触发
 818→        assert any("alphas <= 0" in m for m in msgs), (
 819→            f"全负 alpha 应触发 WARNING 日志，实际捕获: {msgs}"
 820→        )
 821→
 822→    def test_ensemble_spy_unavailable_degrades_to_equal(self):
 823→        """SPY 数据不可用时 alpha=0 → 全零 alpha → 等权 fallback。
 824→
 825→        注：Iter #9 旧代码 max(0, 0.01)=0.01 也是等权，但语义是"避免零权重"。
 826→        Iter #12 新代码 max(0, 0)=0 → total=0 → 等权 fallback。
 827→        行为一致（等权），但路径不同（fallback 而非归一化）。
 828→        """
 829→        n = 100
 830→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
 831→        returns_a = pd.Series(np.random.normal(0.001, 0.005, n), index=idx)
 832→        returns_b = pd.Series(np.random.normal(0.002, 0.008, n), index=idx)
 833→
 834→        results_a = [_make_result("S1", "strat_a", returns_a)]
 835→        results_b = [_make_result("S2", "strat_b", returns_b)]
 836→
 837→        group_results = [
 838→            ("strat_a", {}, results_a),
 839→            ("strat_b", {}, results_b),
 840→        ]
 841→
 842→        # spy_returns=None → alpha=0 → 全零 → 等权 fallback
 843→        weights = _optimize_ensemble_weights(group_results, spy_returns=None)
 844→        weights_dict = {s: w for s, _, w in weights}
 845→        # 等权：各 0.5
 846→        assert abs(weights_dict["strat_a"] - 0.5) < 1e-9
 847→        assert abs(weights_dict["strat_b"] - 0.5) < 1e-9
 848→
 849→    def test_ensemble_single_strategy_returns_one(self):
 850→        """单策略时直接返回权重 1.0（与 Iter #9 行为一致）。"""
 851→        n = 100
 852→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
 853→        returns = pd.Series(np.random.normal(0.001, 0.005, n), index=idx)
 854→        results = [_make_result("S1", "strat_a", returns)]
 855→
 856→        weights = _optimize_ensemble_weights(
 857→            [("strat_a", {}, results)],
 858→            spy_returns=pd.Series(dtype=float),
 859→        )
 860→        assert len(weights) == 1
 861→        assert weights[0][0] == "strat_a"
 862→        assert weights[0][2] == 1.0
 863→
 864→
 865→# ---------------------------------------------------------------------------
 866→# Iter #16: Relaxed alpha gate (ALPHA_GATE_THRESHOLD = -2.0)
 867→# ---------------------------------------------------------------------------
 868→
 869→class TestAlphaGateRelaxedThreshold:
 870→    """迭代 #16：alpha gate 从 alpha>0 放宽至 alpha > ALPHA_GATE_THRESHOLD (-2%)。
 871→
 872→    动机见 spec §1：SPX 成分股 vs SPY 存在结构性近零 alpha，严格 alpha>0 门槛
 873→    导致 4/6 组空仓。放宽至 -2% 仍过滤"灾难性跑输"，但保留"小幅跑输"候选。
 874→    """
 875→
 876→    def test_alpha_gate_constant_exists(self):
 877→        """ALPHA_GATE_THRESHOLD 常量存在且等于 -2.0。"""
 878→        assert hasattr(
 879→            __import__("mytrader.backtest.matrix_backtest", fromlist=["matrix_backtest"]),
 880→            "ALPHA_GATE_THRESHOLD",
 881→        ), "matrix_backtest 必须导出 ALPHA_GATE_THRESHOLD 常量"
 882→        assert ALPHA_GATE_THRESHOLD == -2.0, (
 883→            f"ALPHA_GATE_THRESHOLD 应为 -2.0，实际 {ALPHA_GATE_THRESHOLD}"
 884→        )
 885→
 886→    def test_alpha_gate_relaxed_negative_alpha_passes(self):
 887→        """alpha=-1% 通过 gate（在 -2% 与 0% 之间，旧 gate 会拒绝，新 gate 通过）。
 888→
 889→        场景：单策略 alpha=-1%，健全性通过。
 890→        验证：权重正常产出（非空），no_positive_alpha=False。
 891→
 892→        实现注：用 patch _compute_alpha 返回精确 -1.0%，避免随机收益序列的方差干扰。
 893→        重点测试 gate 逻辑，不测试 alpha 计算本身（后者在 test_matrix_backtest 覆盖）。
 894→        """
 895→        n = 300
 896→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
 897→        spy_df = _make_spy_df(n, annual_return=0.10)
 898→
 899→        # 用任意正收益序列（健全性门槛需要 closed_trades>0，已由 _make_result 默认值满足）
 900→        np.random.seed(42)
 901→        returns_a = pd.Series(np.random.normal(0.0004, 0.004, n), index=idx)
 902→
 903→        # 通过 mock 精确控制 alpha = -1.0%（在 -2% 与 0% 之间）
 904→        mock_alpha = -1.0
 905→        assert ALPHA_GATE_THRESHOLD < mock_alpha < 0, (
 906→            f"测试前提失败：mock alpha 应在 (-2%, 0) 之间"
 907→        )
 908→
 909→        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
 910→            results = []
 911→            for sym, df in data.items():
 912→                if df is None or df.empty or len(df) < 30:
 913→                    continue
 914→                results.append(_make_result(sym, strategy_name, returns_a, closed_trades=10))
 915→            return results
 916→
 917→        df_up = _make_ohlcv(n, trend="up")
 918→        store = _make_store_with_spy({"AAA": df_up, "BBB": df_up}, spy_df)
 919→        universe = _make_mock_universe({"test_group": ["AAA", "BBB"]})
 920→
 921→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
 922→        report = MatrixBacktestReport(
 923→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
 924→            backtest_window="2021-01-01 ~ 2022-01-01",
 925→            groups={},
 926→        )
 927→
 928→        with patch(
 929→            "mytrader.backtest.matrix_backtest._backtest_batch",
 930→            side_effect=mock_backtest_batch,
 931→        ), patch(
 932→            "mytrader.backtest.matrix_backtest._compute_alpha",
 933→            return_value=mock_alpha,
 934→        ):
 935→            weights = mb._run_group(
 936→                group_id="test_group",
 937→                symbols=["AAA", "BBB"],
 938→                start=date(2021, 1, 1),
 939→                end=date(2022, 1, 1),
 940→                strategies=["dual_ma"],
 941→                param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 942→                report=report,
 943→            )
 944→
 945→        # 关键断言：alpha=-1% 应通过 gate（旧 gate 会拒绝）
 946→        assert len(weights) > 0, (
 947→            f"alpha=-1% 应通过 Iter #16 放宽后的 gate，实际 weights={weights}"
 948→        )
 949→        # no_positive_alpha 不应被标记
 950→        for gr in report.group_results:
 951→            if gr.group_id == "test_group":
 952→                assert gr.no_positive_alpha is False, (
 953→                    "alpha=-1% 组不应标记 no_positive_alpha=True（Iter #16 放宽后）"
 954→                )
 955→        warning_text = " ".join(report.warnings)
 956→        assert "no_positive_alpha" not in warning_text, (
 957→            f"alpha=-1% 组不应有 no_positive_alpha 警告，warnings={report.warnings}"
 958→        )
 959→
 960→    def test_alpha_gate_very_negative_fails(self):
 961→        """alpha=-5% 仍被拒绝（远低于 -2% 阈值）。
 962→
 963→        场景：单策略 alpha=-5%，健全性通过。
 964→        验证：返回空权重，no_positive_alpha=True。
 965→        """
 966→        n = 300
 967→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
 968→        spy_df = _make_spy_df(n, annual_return=0.10)
 969→
 970→        np.random.seed(42)
 971→        returns_a = pd.Series(np.random.normal(0.0004, 0.004, n), index=idx)
 972→
 973→        # mock alpha = -5.0%（远低于 -2% 阈值）
 974→        mock_alpha = -5.0
 975→        assert mock_alpha < ALPHA_GATE_THRESHOLD, (
 976→            f"测试前提失败：mock alpha 应 < {ALPHA_GATE_THRESHOLD}%"
 977→        )
 978→
 979→        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
 980→            results = []
 981→            for sym, df in data.items():
 982→                if df is None or df.empty or len(df) < 30:
 983→                    continue
 984→                results.append(_make_result(sym, strategy_name, returns_a, closed_trades=10))
 985→            return results
 986→
 987→        df_up = _make_ohlcv(n, trend="up")
 988→        store = _make_store_with_spy({"AAA": df_up, "BBB": df_up}, spy_df)
 989→        universe = _make_mock_universe({"test_group": ["AAA", "BBB"]})
 990→
 991→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
 992→        report = MatrixBacktestReport(
 993→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
 994→            backtest_window="2021-01-01 ~ 2022-01-01",
 995→            groups={},
 996→        )
 997→
 998→        with patch(
 999→            "mytrader.backtest.matrix_backtest._backtest_batch",
1000→            side_effect=mock_backtest_batch,
1001→        ), patch(
1002→            "mytrader.backtest.matrix_backtest._compute_alpha",
1003→            return_value=mock_alpha,
1004→        ):
1005→            weights = mb._run_group(
1006→                group_id="test_group",
1007→                symbols=["AAA", "BBB"],
1008→                start=date(2021, 1, 1),
1009→                end=date(2022, 1, 1),
1010→                strategies=["dual_ma"],
1011→                param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
1012→                report=report,
1013→            )
1014→
1015→        # 关键断言：alpha=-5% 应被拒绝
1016→        assert weights == [], (
1017→            f"alpha={mock_alpha}% 应被拒绝（< {ALPHA_GATE_THRESHOLD}%），实际 weights={weights}"
1018→        )
1019→        warning_text = " ".join(report.warnings)
1020→        assert "no_positive_alpha" in warning_text
1021→        for gr in report.group_results:
1022→            if gr.group_id == "test_group":
1023→                assert gr.no_positive_alpha is True
1024→
1025→    def test_alpha_gate_threshold_boundary(self):
1026→        """alpha=-2.0% 恰好在阈值边界 → 被拒绝（使用 > 严格比较）。
1027→
1028→        场景：alpha 精确等于 -2.0%（边界值）。
1029→        验证：返回空权重（因为 `c[5] > ALPHA_GATE_THRESHOLD` 是严格大于）。
1030→        """
1031→        n = 300
1032→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
1033→        spy_df = _make_spy_df(n, annual_return=0.10)
1034→
1035→        np.random.seed(42)
1036→        returns_a = pd.Series(np.random.normal(0.0004, 0.004, n), index=idx)
1037→
1038→        # mock alpha 精确等于阈值边界
1039→        mock_alpha = ALPHA_GATE_THRESHOLD  # -2.0
1040→
1041→        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
1042→            results = []
1043→            for sym, df in data.items():
1044→                if df is None or df.empty or len(df) < 30:
1045→                    continue
1046→                results.append(_make_result(sym, strategy_name, returns_a, closed_trades=10))
1047→            return results
1048→
1049→        df_up = _make_ohlcv(n, trend="up")
1050→        store = _make_store_with_spy({"AAA": df_up, "BBB": df_up}, spy_df)
1051→        universe = _make_mock_universe({"test_group": ["AAA", "BBB"]})
1052→
1053→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
1054→        report = MatrixBacktestReport(
1055→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
1056→            backtest_window="2021-01-01 ~ 2022-01-01",
1057→            groups={},
1058→        )
1059→
1060→        # patch _compute_alpha 返回精确 -2.0%（边界值）
1061→        with patch(
1062→            "mytrader.backtest.matrix_backtest._backtest_batch",
1063→            side_effect=mock_backtest_batch,
1064→        ), patch(
1065→            "mytrader.backtest.matrix_backtest._compute_alpha",
1066→            return_value=mock_alpha,
1067→        ):
1068→            weights = mb._run_group(
1069→                group_id="test_group",
1070→                symbols=["AAA", "BBB"],
1071→                start=date(2021, 1, 1),
1072→                end=date(2022, 1, 1),
1073→                strategies=["dual_ma"],
1074→                param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
1075→                report=report,
1076→            )
1077→
1078→        # 关键断言：alpha == threshold 应被拒绝（因为 c[5] > ALPHA_GATE_THRESHOLD 是严格大于）
1079→        assert weights == [], (
1080→            f"alpha == {ALPHA_GATE_THRESHOLD}% 应被拒绝（使用 > 严格比较），"
1081→            f"实际 weights={weights}"
1082→        )
1083→        warning_text = " ".join(report.warnings)
1084→        assert "no_positive_alpha" in warning_text
1085→
1086→    def test_alpha_gate_positive_alpha_passes(self):
1087→        """alpha=+1% 仍通过 gate（无回归，正 alpha 行为不变）。
1088→
1089→        场景：单策略 alpha=+1%（正 alpha）。
1090→        验证：权重正常产出，no_positive_alpha=False。
1091→        这是回归测试，确保 Iter #16 放宽不破坏正 alpha 行为。
1092→        """
1093→        n = 300
1094→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
1095→        spy_df = _make_spy_df(n, annual_return=0.10)
1096→
1097→        np.random.seed(42)
1098→        returns_a = pd.Series(np.random.normal(0.0004, 0.004, n), index=idx)
1099→
1100→        # mock alpha = +1.0%（正 alpha）
1101→        mock_alpha = 1.0
1102→        assert mock_alpha > 0
1103→
1104→        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
1105→            results = []
1106→            for sym, df in data.items():
1107→                if df is None or df.empty or len(df) < 30:
1108→                    continue
1109→                results.append(_make_result(sym, strategy_name, returns_a, closed_trades=10))
1110→            return results
1111→
1112→        df_up = _make_ohlcv(n, trend="up")
1113→        store = _make_store_with_spy({"AAA": df_up, "BBB": df_up}, spy_df)
1114→        universe = _make_mock_universe({"test_group": ["AAA", "BBB"]})
1115→
1116→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
1117→        report = MatrixBacktestReport(
1118→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
1119→            backtest_window="2021-01-01 ~ 2022-01-01",
1120→            groups={},
1121→        )
1122→
1123→        with patch(
1124→            "mytrader.backtest.matrix_backtest._backtest_batch",
1125→            side_effect=mock_backtest_batch,
1126→        ), patch(
1127→            "mytrader.backtest.matrix_backtest._compute_alpha",
1128→            return_value=mock_alpha,
1129→        ):
1130→            weights = mb._run_group(
1131→                group_id="test_group",
1132→                symbols=["AAA", "BBB"],
1133→                start=date(2021, 1, 1),
1134→                end=date(2022, 1, 1),
1135→                strategies=["dual_ma"],
1136→                param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
1137→                report=report,
1138→            )
1139→
1140→        # 正 alpha 应���常通过
1141→        assert len(weights) > 0, (
1142→            f"正 alpha 应通过 gate（无回归），实际 weights={weights}"
1143→        )
1144→        for gr in report.group_results:
1145→            if gr.group_id == "test_group":
1146→                assert gr.no_positive_alpha is False
1147→
1148→    def test_alpha_gate_relaxed_unblocks_spx(self):
1149→        """集成场景：SPX 组 alpha=-1.5% 策略入选 tier1（旧 gate 会拒绝）。
1150→
1151→        场景：模拟 Iter #15 reoptimize 中 SPX 组的情况——
1152→        策略 alpha=-1.5%（在 -2% 与 0% 之间），DD ≤ 20%，Sortino > 0.5。
1153→        验证：
1154→          - 旧 gate（alpha>0）会拒绝 → 空权重
1155→          - 新 gate（alpha>-2%）通过 → 权重非空
1156→        """
1157→        n = 300
1158→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
1159→        spy_df = _make_spy_df(n, annual_return=0.10)
1160→
1161→        np.random.seed(42)
1162→        returns_a = pd.Series(np.random.normal(0.0004, 0.004, n), index=idx)
1163→
1164→        # mock alpha = -1.5%（在 -2% 与 0% 之间，模拟 SPX near-zero alpha 场景）
1165→        mock_alpha = -1.5
1166→        assert ALPHA_GATE_THRESHOLD < mock_alpha < 0
1167→
1168→        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
1169→            results = []
1170→            for sym, df in data.items():
1171→                if df is None or df.empty or len(df) < 30:
1172→                    continue
1173→                results.append(_make_result(sym, strategy_name, returns_a, closed_trades=10))
1174→            return results
1175→
1176→        df_up = _make_ohlcv(n, trend="up")
1177→        store = _make_store_with_spy({"AAA": df_up, "BBB": df_up}, spy_df)
1178→        # 模拟 SPX 组名（仅用于语义清晰，不影响逻辑）
1179→        universe = _make_mock_universe({"SPX_mid_vol": ["AAA", "BBB"]})
1180→
1181→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
1182→        report = MatrixBacktestReport(
1183→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
1184→            backtest_window="2021-01-01 ~ 2022-01-01",
1185→            groups={},
1186→        )
1187→
1188→        with patch(
1189→            "mytrader.backtest.matrix_backtest._backtest_batch",
1190→            side_effect=mock_backtest_batch,
1191→        ), patch(
1192→            "mytrader.backtest.matrix_backtest._compute_alpha",
1193→            return_value=mock_alpha,
1194→        ):
1195→            weights = mb._run_group(
1196→                group_id="SPX_mid_vol",
1197→                symbols=["AAA", "BBB"],
1198→                start=date(2021, 1, 1),
1199→                end=date(2022, 1, 1),
1200→                strategies=["dual_ma"],
1201→                param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
1202→                report=report,
1203→            )
1204→
1205→        # 关键断言：SPX 组不再空仓
1206→        assert len(weights) > 0, (
1207→            f"SPX 组 alpha={mock_alpha}%（> {ALPHA_GATE_THRESHOLD}%）应通过 gate，"
1208→            f"实际 weights={weights}（Iter #15 此场景被 alpha>0 gate 阻塞）"
1209→        )
1210→        # backtest_alpha 字段应存在
1211→        for w in weights:
1212→            assert "backtest_alpha" in w
1213→        # no_positive_alpha 不应被标记
1214→        warning_text = " ".join(report.warnings)
1215→        assert "no_positive_alpha" not in warning_text
1216→
1217→    def test_ensemble_weights_with_negative_alpha_single_strategy(self):
1218→        """单策略 ensemble 负 alpha（> -2%）仍得 weight=1.0（早返回）。
1219→
1220→        场景：单策略 alpha=-1%（通过 Iter #16 gate），进入 ensemble。
1221→        验证：`_optimize_ensemble_weights` 的 `len == 1` 早返回路径给 weight=1.0。
1222→
1223→        注：多策略 ensemble 中负 alpha 权重仍为 0（max(a, 0.0)），
1224→        这是保守设计——正 alpha 策略应主导权重。单策略场景是特例。
1225→        """
1226→        n = 252
1227→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
1228→        spy_returns = pd.Series(np.random.normal(0.0004, 0.001, n), index=idx)
1229→
1230→        # 策略收益序列（alpha 值由 mock 控制，这里只需要非空序列）
1231→        np.random.seed(42)
1232→        returns_a = pd.Series(np.random.normal(0.00035, 0.004, n), index=idx)
1233→
1234→        results_a = [_make_result("S1", "strat_a", returns_a)]
1235→
1236→        # 单策略 ensemble（早返回路径，不计算 alpha）
1237→        weights = _optimize_ensemble_weights(
1238→            [("strat_a", {}, results_a)],
1239→            spy_returns=spy_returns,
1240→        )
1241→
1242→        # 早返回路径 → weight=1.0
1243→        assert len(weights) == 1
1244→        assert weights[0][0] == "strat_a"
1245→        assert weights[0][2] == 1.0, (
1246→            f"单策略 ensemble 应早返回 weight=1.0（不依赖 alpha 值），"
1247→            f"实际 {weights[0][2]}"
1248→        )
1249→
---
Now
---
 I have a clear
---
 understanding of the existing
---
 tests
---
.
---
 Let
---
 me check
---
 the iteration
---
_trajectory.md to
---
 understand the L
---
9 format for
---
 documenting
---
 iterations
---
.
---
现在
---
让我检查一下 trajectory
---
 format
---
 和 iteration
---
_
---
16
---
 spec，
---
以了解相关的
---
惯例
---
。
---
{"command": "grep -n \"Iter.*16\\|Iteration.*16\\|iteration.*16\\|iter.*16\" /Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md | head -20", "description": "Find iter 16 in trajectory"}
---
Find iter 16 in trajectory
---
Command: grep -n "Iter.*16\|Iteration.*16\|iteration.*16\|iter.*16" /Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md | head -20
Stdout: 1531:- 新增 Iter #16 注释：说明上游 alpha gate 已放宽至 -2%，本函数的 `max(a, 0.0)` 是保守设计
1546:- 更新 `designs/design_v2/07-backtest-module.md` §10.4.1：新增 Iter #16 放宽说明
1547:- 更新 `.codebuddy/CODEBUDDY.md`：新增 Iter #16 条目 + 测试数 707→744
1560:**Iter #16 --reoptimize 结果**（完整，reoptimize 已完成）:
1562:| 组 | Baseline | Iter #16 | 变化 |
1604:- **in-sample vs OOS 阈值分层设计**：Iter #16 的 -2% in-sample gate 与 Iter #13 的 -5% OOS floor 形成 3% 缓冲带。这种分层设计允许 in-sample 稍宽松（让候选进入 OOS 验证），OOS 仍严格把关（avg alpha > 0）
1606:- **并发 reoptimize 进程冲突**：发现一个 4h47m 前启动的旧 reoptimize 进程（pre-Iter-16 代码）仍在运行，与我新启动的 reoptimize 竞争 CPU/IO 并可能覆盖 weights 文件。教训：启动 reoptimize 前应检查是否有残留进程
1633:✅ Iter #16 reoptimize 完成 (2/6 组有权重, -2% gate 解锁 2 策略)

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"file_path": "/Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md", "limit": 130, "offset": 1510}
---
1510→
1511→### 背景
1512→
1513→Iter #12 引入 `alpha > 0` 硬门槛后，Iter #15 reoptimize 发现 4/6 组空仓（SPX_mid_vol / SPX_high_vol / SPX_low_vol / NDX_mid_vol）。spec 假设 SPX 成分股 vs SPY 存在结构性近零 alpha（-1% ~ 0%），alpha>0 门槛过于严格，应放宽至 -2%。
1514→
1515→### 变更详情
1516→
1517→**P0: 新增 `ALPHA_GATE_THRESHOLD` 常量** (`mytrader/backtest/matrix_backtest.py`)
1518→- 模块级常量 `ALPHA_GATE_THRESHOLD: float = -2.0`
1519→- 设计动机：SPX 成分股 vs SPY benchmark 存在结构性近零 alpha；-2% 过滤"灾难性跑输"但保留"小幅跑输 SPY 但 Sortino/DD 优秀"的候选
1520→- 与 WF OOS 校验的关系：Walk-Forward（Iter #13）仍用 -5% 单轮下限 + avg>0 汇总门槛，放宽 in-sample gate 不削弱 OOS 验证强度
1521→
1522→**P0: 放宽 `_run_group` alpha gate** (`matrix_backtest.py::_run_group`)
1523→- 旧：`positive_alpha_candidates = [c for c in candidates if c[5] > 0]`
1524→- 新：`alpha_qualified_candidates = [c for c in candidates if c[5] > ALPHA_GATE_THRESHOLD]`
1525→- 变量名从 `positive_alpha_candidates` 改为 `alpha_qualified_candidates`（语义更准确）
1526→- 警告信息更新：`alpha <= 0 (cannot beat SPY)` → `alpha <= {ALPHA_GATE_THRESHOLD}% (cannot beat SPY within tolerance)`
1527→- `no_positive_alpha` 字段名保留（向下兼容下游消费方），语义为"无合格 alpha 候选"
1528→
1529→**P1: 更新 `_optimize_ensemble_weights` 注释** (`matrix_backtest.py::_optimize_ensemble_weights`)
1530→- 逻辑不变：仍用 `max(a, 0.0)` 作为权重下限（负 alpha 在多策略 ensemble 中权重为 0）
1531→- 新增 Iter #16 注释：说明上游 alpha gate 已放宽至 -2%，本函数的 `max(a, 0.0)` 是保守设计
1532→- 注释提示：若未来需让小幅负 alpha 贡献权重，可改为 `max(a - ALPHA_GATE_THRESHOLD, 0.0)`
1533→
1534→**P1: 测试** (`tests/test_alpha_gate.py`, +7 新测试)
1535→- `TestAlphaGateRelaxedThreshold` 类，7 个测试：
1536→  1. `test_alpha_gate_constant_exists` — 常量存在且等于 -2.0
1537→  2. `test_alpha_gate_relaxed_negative_alpha_passes` — alpha=-1% 通过 gate
1538→  3. `test_alpha_gate_very_negative_fails` — alpha=-5% 仍被拒绝
1539→  4. `test_alpha_gate_threshold_boundary` — alpha=-2.0% 边界被拒绝（>严格比较）
1540→  5. `test_alpha_gate_positive_alpha_passes` — alpha=+1% 仍通过（无回归）
1541→  6. `test_alpha_gate_relaxed_unblocks_spx` — SPX 组 alpha=-1.5% 入选 tier1
1542→  7. `test_ensemble_weights_with_negative_alpha_single_strategy` — 单策略 ensemble 负 alpha 得 weight=1.0
1543→- 测试技巧：用 `patch _compute_alpha` 返回精确 alpha 值，避免随机收益序列的方差干扰；重点测 gate 逻辑而非 alpha 计算
1544→
1545→**P2: 文档同步**
1546→- 更新 `designs/design_v2/07-backtest-module.md` §10.4.1：新增 Iter #16 放宽说明
1547→- 更新 `.codebuddy/CODEBUDDY.md`：新增 Iter #16 条目 + 测试数 707→744
1548→
1549→### 验证结果
1550→
1551→```
1552→tests/test_alpha_gate.py: 20 passed, 0 failed (13 旧 + 7 新)
1553→Full pytest (excluding live): 744 passed, 0 failed, 103 warnings in 25.00s
1554→```
1555→
1556→### --reoptimize 验证结果
1557→
1558→**Baseline (Iter #15)**: 2/6 组有权重（NDX_high_vol: rsi_mean_revert, NDX_low_vol: rsi_mean_revert），4/6 组空仓
1559→
1560→**Iter #16 --reoptimize 结果**（完整，reoptimize 已完成）:
1561→
1562→| 组 | Baseline | Iter #16 | 变化 |
1563→|----|----------|----------|------|
1564→| SPX_mid_vol | EMPTY | EMPTY | 无变化（所有 alpha < -4.69%） |
1565→| SPX_high_vol | EMPTY | EMPTY | 无变化（所有 alpha < -3.61%） |
1566→| NDX_high_vol | rsi_mean_revert (alpha=+0.40%) | momentum_roc (alpha=-1.84%) | **CHANGED**: momentum_roc 被 -2% gate 解锁 |
1567→| SPX_low_vol | EMPTY | EMPTY | 无变化（所有 alpha < -4.01%） |
1568→| NDX_low_vol | rsi_mean_revert (alpha=+1.77%) | rsi_mean_revert + bollinger_band (alpha=-1.24%) | **CHANGED**: bollinger_band 被 -2% gate 解锁 |
1569→| NDX_mid_vol | EMPTY | EMPTY | 无变化（所有 alpha < -2.48%，差 0.48%） |
1570→
1571→**-2% gate 解锁的策略**（alpha 在 (-2%, 0) 区间，旧 alpha>0 gate 会拒绝）:
1572→1. NDX_high_vol: momentum_roc (alpha=-1.8369%)
1573→2. NDX_low_vol: bollinger_band (alpha=-1.2414%, weight=0.0 — ensemble 中负 alpha 权重为 0)
1574→
1575→**关键发现**: spec §1 假设"SPX 成分股 vs SPY 存在结构性近零 alpha（-1% ~ 0%）"，但实际 SPX 组的 alpha 范围为 -3.61% ~ -15.35%。-2% 阈值对 SPX 组完全不够。NDX 组的 alpha 更接近 spec 假设（-1.84% ~ -2.48%）。
1576→
1577→### Constitution 合规
1578→
1579→- ✅ 未突破 DD 20% 约束（未修改 DD 阈值）
1580→- ✅ 测试覆盖率提升（+7 测试，737 → 744）
1581→- ✅ 未引入黑箱逻辑（ALPHA_GATE_THRESHOLD 是透明常量）
1582→- ✅ 未修改 WF OOS 校验（仍用 -5% 单轮下限 + avg>0）
1583→- ✅ 未修改 Sortino 0.5 门槛
1584→- ✅ 未修改 strategies / indicators / risk / execution / main.py（spec §5 scope boundary 遵守）
1585→- ✅ 文档与代码同步（trajectory + CODEBUDDY + design_v2/07 更新）
1586→
1587→### Success Criteria 对照（spec §4）
1588→
1589→| # | 条件 | 状态 |
1590→|---|------|:----:|
1591→| 1 | Alpha gate uses ALPHA_GATE_THRESHOLD=-2.0 | ✅ 常量测试 + 代码审查 |
1592→| 2 | Alpha=-1% passes the gate | ✅ test_alpha_gate_relaxed_negative_alpha_passes |
1593→| 3 | Alpha=-5% still fails the gate | ✅ test_alpha_gate_very_negative_fails |
1594→| 4 | All existing tests pass | ✅ 744 passed |
1595→| 5 | `--reoptimize` shows >2 groups with weights | ❌ NOT MET — 2/6 groups（与 baseline 相同） |
1596→| 6 | SPX groups no longer all empty | ❌ NOT MET — 3/3 SPX 组仍空仓（alpha 范围 -3.61% ~ -15.35%） |
1597→
1598→**注**: 虽然成功标准 5/6 未完全满足，但 -2% gate 确实解锁了 2 个策略（momentum_roc alpha=-1.84%, bollinger_band alpha=-1.24%），这些在旧 alpha>0 gate 下会被拒绝。未满足的原因是 spec 对 SPX 组 alpha 的假设（-1% ~ 0%）与实际数据（-3.61% ~ -15.35%）不符。
1599→
1600→### Experience Learned
1601→
1602→- **spec 假设 vs 实际 alpha 差距**：spec §1 假设"SPX 成分股 vs SPY 存在结构性近零 alpha（-1% ~ 0%）"，但实际 SPX 组的 alpha 范围为 -3.61% ~ -15.35%。NDX 组的 alpha 更接近 spec 假设（-1.84% ~ -2.48%）。这说明 spec 的根因分析是基于直觉而非数据，实际运行后需要修正。阈值放宽是正确方向，但 -2% 对 SPX 组不够
1603→- **-2% gate 确实有效**：虽然 SPX 组未解锁，但 NDX 组有 2 个策略被解锁（momentum_roc alpha=-1.84%, bollinger_band alpha=-1.24%），这些在旧 alpha>0 gate 下会被拒绝。gate 逻辑本身是正确的
1604→- **in-sample vs OOS 阈值分层设计**：Iter #16 的 -2% in-sample gate 与 Iter #13 的 -5% OOS floor 形成 3% 缓冲带。这种分层设计允许 in-sample 稍宽松（让候选进入 OOS 验证），OOS 仍严格把关（avg alpha > 0）
1605→- **NDX_mid_vol 差 0.48% 未解锁**：NDX_mid_vol 最佳策略 rsi_mean_revert alpha=-2.48%，差 -2% 阈值仅 0.48%。若阈值放宽至 -3%，NDX_mid_vol 将解锁，总组数升至 3/6。但进一步放宽需评估是否与 WF -5% floor 过度接近
1606→- **并发 reoptimize 进程冲突**：发现一个 4h47m 前启动的旧 reoptimize 进程（pre-Iter-16 代码）仍在运行，与我新启动的 reoptimize 竞争 CPU/IO 并可能覆盖 weights 文件。教训：启动 reoptimize 前应检查是否有残留进程
1607→- **测试用 mock 控制精确 alpha 值**：随机收益序列的方差会导致 alpha 计算结果波动，使边界测试（如 alpha=-2.0%）不稳定。用 `patch _compute_alpha return_value=mock_alpha` 可以精确控制 alpha 值，使测试聚焦于 gate 逻辑而非 alpha 计算
1608→
1609→### 后续建议
1610→
1611→1. **考虑将 ALPHA_GATE_THRESHOLD 进一步降至 -3% 或 -5%**：
1612→   - -3% 会解锁 NDX_mid_vol（最佳 alpha -2.48%），总组数升至 3/6
1613→   - -5%（与 WF floor 一致）可能解锁部分 SPX 组（SPX_high_vol 最佳 alpha -3.61%）
1614→   - 风险：进一步放宽会削弱 in-sample vs OOS 的分层设计，更多低质量候选进入 OOS 验证
1615→2. **策略 pool 在 SPX 上的 alpha 改进**：当前 9 策略在 SPX 组上 alpha 均 < -3.61%，说明策略逻辑不适配 SPX 成分股的低波动率特征。可考虑增加 SPX-specific 策略（如低波动率均值回归 + 质量因子过滤）
1616→3. **SPX 组使用组内 benchmark**：SPX 成分股 vs SPY 存在结构性 alpha 偏差。可考虑对 SPX 组使用 SPXEW（equal-weight S&P 500）或 VOO（Vanguard S&P 500 ETF）作为 benchmark，而非 SPY
1617→4. **ensemble weights 与 gate 一致性**：当前 `_optimize_ensemble_weights` 仍用 `max(a, 0.0)`，多策略 ensemble 中负 alpha（但 > -2%）权重为 0。NDX_low_vol 的 bollinger_band（alpha=-1.24%）就是此例——通过 gate 但 ensemble weight=0。若未来希望让小幅负 alpha 策略也贡献权重，可改为 `max(a - ALPHA_GATE_THRESHOLD, 0.0)`
1618→5. **reoptimize 性能优化**：9 策略 × 284 参数组合 × 6 组 × 5 年，总耗时 ~65 分钟。可考虑按组并行化（每组独立进程）或缓存策略信号矩阵
1619→
1620→### L7 流水线状态
1621→
1622→```
1623→✅ Backtest (≥5年, alpha-based selection, batch-optimized, sanity-gated, alpha-gate-relaxed)
1624→✅ Walk-Forward (4轮, alpha gate, OOS -5% floor + avg>0)
1625→✅ Portfolio Backtest | ✅ Paper Trading Integrity
1626→✅ Harness Reliability | ✅ SignalRanker Sortino Priority
1627→✅ Strategy Diversity (9 策略 pool, 迭代 #14-15 扩展)
1628→✅ Alpha-Based Selection (迭代 #9)
1629→✅ Batch Backtest Optimization (迭代 #10)
1630→✅ Sanity Gate / Reject Degenerate (迭代 #11)
1631→✅ Alpha Gate (迭代 #12 引入, 迭代 #16 放宽至 -2%)
1632→✅ WF Gate Alpha Validation (迭代 #13)
1633→✅ Iter #16 reoptimize 完成 (2/6 组有权重, -2% gate 解锁 2 策略)
1634→⬜ Paper Trade ≥1月 | ⬜ Live
1635→```
1636→
1637→---
1638→
1639→> **Orchestrator 验证记录** (自动追加)
1640→
---
1510→
1511→### 背景
1512→
1513→Iter #12 引入 `alpha > 0` 硬门槛后，Iter #15 reoptimize 发现 4/6 组空仓（SPX_mid_vol / SPX_high_vol / SPX_low_vol / NDX_mid_vol）。spec 假设 SPX 成分股 vs SPY 存在结构性近零 alpha（-1% ~ 0%），alpha>0 门槛过于严格，应放宽至 -2%。
1514→
1515→### 变更详情
1516→
1517→**P0: 新增 `ALPHA_GATE_THRESHOLD` 常量** (`mytrader/backtest/matrix_backtest.py`)
1518→- 模块级常量 `ALPHA_GATE_THRESHOLD: float = -2.0`
1519→- 设计动机：SPX 成分股 vs SPY benchmark 存在结构性近零 alpha；-2% 过滤"灾难性跑输"但保留"小幅跑输 SPY 但 Sortino/DD 优秀"的候选
1520→- 与 WF OOS 校验的关系：Walk-Forward（Iter #13）仍用 -5% 单轮下限 + avg>0 汇总门槛，放宽 in-sample gate 不削弱 OOS 验证强度
1521→
1522→**P0: 放宽 `_run_group` alpha gate** (`matrix_backtest.py::_run_group`)
1523→- 旧：`positive_alpha_candidates = [c for c in candidates if c[5] > 0]`
1524→- 新：`alpha_qualified_candidates = [c for c in candidates if c[5] > ALPHA_GATE_THRESHOLD]`
1525→- 变量名从 `positive_alpha_candidates` 改为 `alpha_qualified_candidates`（语义更准确）
1526→- 警告信息更新：`alpha <= 0 (cannot beat SPY)` → `alpha <= {ALPHA_GATE_THRESHOLD}% (cannot beat SPY within tolerance)`
1527→- `no_positive_alpha` 字段名保留（向下兼容下游消费方），语义为"无合格 alpha 候选"
1528→
1529→**P1: 更新 `_optimize_ensemble_weights` 注释** (`matrix_backtest.py::_optimize_ensemble_weights`)
1530→- 逻辑不变：仍用 `max(a, 0.0)` 作为权重下限（负 alpha 在多策略 ensemble 中权重为 0）
1531→- 新增 Iter #16 注释：说明上游 alpha gate 已放宽至 -2%，本函数的 `max(a, 0.0)` 是保守设计
1532→- 注释提示：若未来需让小幅负 alpha 贡献权重，可改为 `max(a - ALPHA_GATE_THRESHOLD, 0.0)`
1533→
1534→**P1: 测试** (`tests/test_alpha_gate.py`, +7 新测试)
1535→- `TestAlphaGateRelaxedThreshold` 类，7 个测试：
1536→  1. `test_alpha_gate_constant_exists` — 常量存在且等于 -2.0
1537→  2. `test_alpha_gate_relaxed_negative_alpha_passes` — alpha=-1% 通过 gate
1538→  3. `test_alpha_gate_very_negative_fails` — alpha=-5% 仍被拒绝
1539→  4. `test_alpha_gate_threshold_boundary` — alpha=-2.0% 边界被拒绝（>严格比较）
1540→  5. `test_alpha_gate_positive_alpha_passes` — alpha=+1% 仍通过（无回归）
1541→  6. `test_alpha_gate_relaxed_unblocks_spx` — SPX 组 alpha=-1.5% 入选 tier1
1542→  7. `test_ensemble_weights_with_negative_alpha_single_strategy` — 单策略 ensemble 负 alpha 得 weight=1.0
1543→- 测试技巧：用 `patch _compute_alpha` 返回精确 alpha 值，避免随机收益序列的方差干扰；重点测 gate 逻辑而非 alpha 计算
1544→
1545→**P2: 文档同步**
1546→- 更新 `designs/design_v2/07-backtest-module.md` §10.4.1：新增 Iter #16 放宽说明
1547→- 更新 `.codebuddy/CODEBUDDY.md`：新增 Iter #16 条目 + 测试数 707→744
1548→
1549→### 验证结果
1550→
1551→```
1552→tests/test_alpha_gate.py: 20 passed, 0 failed (13 旧 + 7 新)
1553→Full pytest (excluding live): 744 passed, 0 failed, 103 warnings in 25.00s
1554→```
1555→
1556→### --reoptimize 验证结果
1557→
1558→**Baseline (Iter #15)**: 2/6 组有权重（NDX_high_vol: rsi_mean_revert, NDX_low_vol: rsi_mean_revert），4/6 组空仓
1559→
1560→**Iter #16 --reoptimize 结果**（完整，reoptimize 已完成）:
1561→
1562→| 组 | Baseline | Iter #16 | 变化 |
1563→|----|----------|----------|------|
1564→| SPX_mid_vol | EMPTY | EMPTY | 无变化（所有 alpha < -4.69%） |
1565→| SPX_high_vol | EMPTY | EMPTY | 无变化（所有 alpha < -3.61%） |
1566→| NDX_high_vol | rsi_mean_revert (alpha=+0.40%) | momentum_roc (alpha=-1.84%) | **CHANGED**: momentum_roc 被 -2% gate 解锁 |
1567→| SPX_low_vol | EMPTY | EMPTY | 无变化（所有 alpha < -4.01%） |
1568→| NDX_low_vol | rsi_mean_revert (alpha=+1.77%) | rsi_mean_revert + bollinger_band (alpha=-1.24%) | **CHANGED**: bollinger_band 被 -2% gate 解锁 |
1569→| NDX_mid_vol | EMPTY | EMPTY | 无变化（所有 alpha < -2.48%，差 0.48%） |
1570→
1571→**-2% gate 解锁的策略**（alpha 在 (-2%, 0) 区间，旧 alpha>0 gate 会拒绝）:
1572→1. NDX_high_vol: momentum_roc (alpha=-1.8369%)
1573→2. NDX_low_vol: bollinger_band (alpha=-1.2414%, weight=0.0 — ensemble 中负 alpha 权重为 0)
1574→
1575→**关键发现**: spec §1 假设"SPX 成分股 vs SPY 存在结构性近零 alpha（-1% ~ 0%）"，但实际 SPX 组的 alpha 范围为 -3.61% ~ -15.35%。-2% 阈值对 SPX 组完全不够。NDX 组的 alpha 更接近 spec 假设（-1.84% ~ -2.48%）。
1576→
1577→### Constitution 合规
1578→
1579→- ✅ 未突破 DD 20% 约束（未修改 DD 阈值）
1580→- ✅ 测试覆盖率提升（+7 测试，737 → 744）
1581→- ✅ 未引入黑箱逻辑（ALPHA_GATE_THRESHOLD 是透明常量）
1582→- ✅ 未修改 WF OOS 校验（仍用 -5% 单轮下限 + avg>0）
1583→- ✅ 未修改 Sortino 0.5 门槛
1584→- ✅ 未修改 strategies / indicators / risk / execution / main.py（spec §5 scope boundary 遵守）
1585→- ✅ 文档与代码同步（trajectory + CODEBUDDY + design_v2/07 更新）
1586→
1587→### Success Criteria 对照（spec §4）
1588→
1589→| # | 条件 | 状态 |
1590→|---|------|:----:|
1591→| 1 | Alpha gate uses ALPHA_GATE_THRESHOLD=-2.0 | ✅ 常量测试 + 代码审查 |
1592→| 2 | Alpha=-1% passes the gate | ✅ test_alpha_gate_relaxed_negative_alpha_passes |
1593→| 3 | Alpha=-5% still fails the gate | ✅ test_alpha_gate_very_negative_fails |
1594→| 4 | All existing tests pass | ✅ 744 passed |
1595→| 5 | `--reoptimize` shows >2 groups with weights | ❌ NOT MET — 2/6 groups（与 baseline 相同） |
1596→| 6 | SPX groups no longer all empty | ❌ NOT MET — 3/3 SPX 组仍空仓（alpha 范围 -3.61% ~ -15.35%） |
1597→
1598→**注**: 虽然成功标准 5/6 未完全满足，但 -2% gate 确实解锁了 2 个策略（momentum_roc alpha=-1.84%, bollinger_band alpha=-1.24%），这些在旧 alpha>0 gate 下会被拒绝。未满足的原因是 spec 对 SPX 组 alpha 的假设（-1% ~ 0%）与实际数据（-3.61% ~ -15.35%）不符。
1599→
1600→### Experience Learned
1601→
1602→- **spec 假设 vs 实际 alpha 差距**：spec §1 假设"SPX 成分股 vs SPY 存在结构性近零 alpha（-1% ~ 0%）"，但实际 SPX 组的 alpha 范围为 -3.61% ~ -15.35%。NDX 组的 alpha 更接近 spec 假设（-1.84% ~ -2.48%）。这说明 spec 的根因分析是基于直觉而非数据，实际运行后需要修正。阈值放宽是正确方向，但 -2% 对 SPX 组不够
1603→- **-2% gate 确实有效**：虽然 SPX 组未解锁，但 NDX 组有 2 个策略被解锁（momentum_roc alpha=-1.84%, bollinger_band alpha=-1.24%），这些在旧 alpha>0 gate 下会被拒绝。gate 逻辑本身是正确的
1604→- **in-sample vs OOS 阈值分层设计**：Iter #16 的 -2% in-sample gate 与 Iter #13 的 -5% OOS floor 形成 3% 缓冲带。这种分层设计允许 in-sample 稍宽松（让候选进入 OOS 验证），OOS 仍严格把关（avg alpha > 0）
1605→- **NDX_mid_vol 差 0.48% 未解锁**：NDX_mid_vol 最佳策略 rsi_mean_revert alpha=-2.48%，差 -2% 阈值仅 0.48%。若阈值放宽至 -3%，NDX_mid_vol 将解锁，总组数升至 3/6。但进一步放宽需评估是否与 WF -5% floor 过度接近
1606→- **并发 reoptimize 进程冲突**：发现一个 4h47m 前启动的旧 reoptimize 进程（pre-Iter-16 代码）仍在运行，与我新启动的 reoptimize 竞争 CPU/IO 并可能覆盖 weights 文件。教训：启动 reoptimize 前应检查是否有残留进程
1607→- **测试用 mock 控制精确 alpha 值**：随机收益序列的方差会导致 alpha 计算结果波动，使边界测试（如 alpha=-2.0%）不稳定。用 `patch _compute_alpha return_value=mock_alpha` 可以精确控制 alpha 值，使测试聚焦于 gate 逻辑而非 alpha 计算
1608→
1609→### 后续建议
1610→
1611→1. **考虑将 ALPHA_GATE_THRESHOLD 进一步降至 -3% 或 -5%**：
1612→   - -3% 会解锁 NDX_mid_vol（最佳 alpha -2.48%），总组数升至 3/6
1613→   - -5%（与 WF floor 一致）可能解锁部分 SPX 组（SPX_high_vol 最佳 alpha -3.61%）
1614→   - 风险：进一步放宽会削弱 in-sample vs OOS 的分层设计，更多低质量候选进入 OOS 验证
1615→2. **策略 pool 在 SPX 上的 alpha 改进**：当前 9 策略在 SPX 组上 alpha 均 < -3.61%，说明策略逻辑不适配 SPX 成分股的低波动率特征。可考虑增加 SPX-specific 策略（如低波动率均值回归 + 质量因子过滤）
1616→3. **SPX 组使用组内 benchmark**：SPX 成分股 vs SPY 存在结构性 alpha 偏差。可考虑对 SPX 组使用 SPXEW（equal-weight S&P 500）或 VOO（Vanguard S&P 500 ETF）作为 benchmark，而非 SPY
1617→4. **ensemble weights 与 gate 一致性**：当前 `_optimize_ensemble_weights` 仍用 `max(a, 0.0)`，多策略 ensemble 中负 alpha（但 > -2%）权重为 0。NDX_low_vol 的 bollinger_band（alpha=-1.24%）就是此例——通过 gate 但 ensemble weight=0。若未来希望让小幅负 alpha 策略也贡献权重，可改为 `max(a - ALPHA_GATE_THRESHOLD, 0.0)`
1618→5. **reoptimize 性能优化**：9 策略 × 284 参数组合 × 6 组 × 5 年，总耗时 ~65 分钟。可考虑按组并行化（每组独立进程）或缓存策略信号矩阵
1619→
1620→### L7 流水线状态
1621→
1622→```
1623→✅ Backtest (≥5年, alpha-based selection, batch-optimized, sanity-gated, alpha-gate-relaxed)
1624→✅ Walk-Forward (4轮, alpha gate, OOS -5% floor + avg>0)
1625→✅ Portfolio Backtest | ✅ Paper Trading Integrity
1626→✅ Harness Reliability | ✅ SignalRanker Sortino Priority
1627→✅ Strategy Diversity (9 策略 pool, 迭代 #14-15 扩展)
1628→✅ Alpha-Based Selection (迭代 #9)
1629→✅ Batch Backtest Optimization (迭代 #10)
1630→✅ Sanity Gate / Reject Degenerate (迭代 #11)
1631→✅ Alpha Gate (迭代 #12 引入, 迭代 #16 放宽至 -2%)
1632→✅ WF Gate Alpha Validation (迭代 #13)
1633→✅ Iter #16 reoptimize 完成 (2/6 组有权重, -2% gate 解锁 2 策略)
1634→⬜ Paper Trade ≥1月 | ⬜ Live
1635→```
1636→
1637→---
1638→
1639→> **Orchestrator 验证记录** (自动追加)
1640→
---
Now
---
 I have a complete
---
 picture
---
. The
---
 key finding
---
 from Iter #
---
16 is that
---
 the SP
---
X groups have
---
 alpha in the range
---
 -3.61% to
---
 -15.35
---
%, so
---
 the -2% alpha
---
 gate didn
---
't un
---
block them. Iter
---
 #17
---
 introduces
---
 a
---
 Sort
---
ino-based
---
 exemption: high
---
 Sortino strategies
---
 (>1
---
.5) bypass
---
 the alpha gate entirely
---
.

Let me also
---
 check the iteration
---
_trajectory.md
---
 format for the L9
---
 structure
---
,
---
 then
---
 look
---
 at the existing
---
 iterations
---
 folder
---
.
---
我来
---
检查
---
一下轨迹
---
格式头部
---
和
---
 iteration
---
_16 
---
规范
---
。
---
{"file_path": "/Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md", "limit": 50}
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
  51→
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
  51→
---
现在
---
我已经
---
掌握了所需
---
的所有上下
---
文信息
---
。让我开始
---
实施开发
---
。首先，添加
---
该常
---
量。
---
{"status": "in_progress", "taskId": "2"}
---
Updated task #2 status
---
Updated task #2 status
---
{"file_path": "/Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py", "new_string": "# 迭代 #16 新增：alpha gate 门槛（in-sample），用于 _run_group 排序前的硬门槛。\n# Iter #12 原值为 0（alpha>0 才入选），Iter #16 放宽至 -2%。\n# 设计动机：SPX 成分股 vs SPY benchmark 存在结构性近零 alpha —— SPY 即 S&P 500\n# 本身，交易 SPX 组件 vs SPY 相当于\"和自己赛跑\"。alpha=-1%（小幅跑输 SPY）的\n# 策略仍可能有出色的 Sortino / DD，不应被一刀切拒绝。\n# 与 WF OOS 校验的关系：Walk-Forward（Iter #13）仍用 -5% 单轮下限 + avg>0 汇总\n# 门槛，放宽 in-sample gate 不会削弱 OOS 验证强度。\n# 取 -2% 的理由：足以过滤\"灾难性跑输\"（如 -5% 以下），但保留\"小幅跑输\"的\n# 合理候选；阈值与 WALK_FORWARD_VAL_ALPHA_FLOOR=-5% 形成 3% 缓冲带。\nALPHA_GATE_THRESHOLD: float = -2.0\n\n# 迭代 #17 新增：Sortino 豁免门槛（in-sample），允许高 Sortino 策略绕过 alpha gate。\n# 设计动机：Iter #16 reoptimize 实证 SPX 组 alpha 范围 -3.61% ~ -15.35%（远低于\n# -2% gate），3/3 SPX 组空仓。但其中部分策略 Sortino 极佳（> 1.5），下行风险\n# 控制优秀，只因\"vs SPY 的相对收益\"不合格被拒。Constitution L1 首要 KPI 是\n# Sortino（而非 alpha），alpha 是 Iter #9 引入的二级排序指标。本豁免让\"Sortino\n# 优秀但 alpha 跑输 SPY\"的策略进入 Tier 1/2/3 过滤，不再被 alpha gate 一刀切。\n# 取 1.5 的理由：高于 MIN_SORTINO_THRESHOLD=0.5（Tier 1 合规线）和 1.0（普通优秀），\n# 是\"卓越 Sortino\"门槛；避免豁免过宽（若设为 0.5 则等于 Tier 1 的 Sortino 门槛，\n# 豁免失去意义）。WF OOS 校验仍用 -5% 单轮下限 + avg>0，本豁免不削弱 OOS 验证。\nSORTINO_ALPHA_EXEMPTION: float = 1.5", "old_string": "# 迭代 #16 新增：alpha gate 门槛（in-sample），用于 _run_group 排序前的硬门槛。\n# Iter #12 原值为 0（alpha>0 才入选），Iter #16 放宽至 -2%。\n# 设计动机：SPX 成分股 vs SPY benchmark 存在结构性近零 alpha —— SPY 即 S&P 500\n# 本身，交易 SPX 组件 vs SPY 相当于\"和自己赛跑\"。alpha=-1%（小幅跑输 SPY）的\n# 策略仍可能有出色的 Sortino / DD，不应被一刀切拒绝。\n# 与 WF OOS 校验的关系：Walk-Forward（Iter #13）仍用 -5% 单轮下限 + avg>0 汇总\n# 门槛，放宽 in-sample gate 不会削弱 OOS 验证强度。\n# 取 -2% 的理由：足以过滤\"灾难性跑输\"（如 -5% 以下），但保留\"小幅跑输\"的\n# 合理候选；阈值与 WALK_FORWARD_VAL_ALPHA_FLOOR=-5% 形成 3% 缓冲带。\nALPHA_GATE_THRESHOLD: float = -2.0"}
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
现在修改
---
一级
---
过滤器
---
（alpha
---
 gate），
---
以增加
---
 Sort
---
ino 
---
豁
---
免。
---
{"status": "in_progress", "taskId": "3"}
---
Updated task #3 status
---
Updated task #3 status
---
{"file_path": "/Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py", "new_string": "        # 迭代 #12：alpha 硬门槛（experience.md #8：正超额是排序前的硬门槛）\n        # 迭代 #16：阈值从 alpha>0 放宽至 alpha > ALPHA_GATE_THRESHOLD (-2%)。\n        #   动机：SPX 成分股 vs SPY 存在结构性近零 alpha，严格 alpha>0 门槛导致\n        #   4/6 组空仓（Iter #15 reoptimize 实证）。-2% 仍过滤\"灾难性跑输\"，\n        #   同时保留\"小幅跑输 SPY 但 Sortino/DD 优秀\"的候选。\n        #   Walk-Forward（Iter #13）仍用 -5% 单轮下限 + avg>0 汇总门槛作 OOS 校验，\n        #   放宽 in-sample gate 不削弱 OOS 验证强度。\n        # 迭代 #17：Sortino 豁免 —— 高 Sortino (> SORTINO_ALPHA_EXEMPTION=1.5)\n        #   的策略绕过 alpha gate。动机：Iter #16 reoptimize 实证 SPX 组 alpha\n        #   范围 -3.61% ~ -15.35%，-2% gate 仍不解锁 SPX 组；但部分策略 Sortino\n        #   极佳（下行风险控制优秀），只因\"vs SPY 相对收益\"不合格被拒。Constitution\n        #   L1 首要 KPI 是 Sortino（而非 alpha），本豁免让\"Sortino 卓越但 alpha 跑输\n        #   SPY\"的策略进入 Tier 1/2/3，不再被 alpha gate 一刀切。WF OOS 校验仍用\n        #   -5% 单轮下限 + avg>0，本豁免不削弱 OOS 验证强度。\n        # 顺序：健全性（Iter #11）→ 风险（DD，Tier 1/2/3）→ alpha 门槛（本步）→ 排序\n        #\n        # 注意：这一步在 candidates 构建后、Tier 1 前，确保 Tier 1/2/3 只在合格候选中进行。\n        # 合格定义：alpha > ALPHA_GATE_THRESHOLD  OR  sortino > SORTINO_ALPHA_EXEMPTION\n        # （二者满足其一即进入 Tier 1/2/3）\n        # 如果某组所有候选都不满足（alpha ≤ threshold 且 sortino ≤ exemption），\n        # 该组空仓（hold cash），不强行选严重跑输 SPY 且 Sortino 平庸的策略\n        # （experience.md #8：\"没有候选满足门槛时，正确动作是空仓/降现金/回退 benchmark，\n        #   不是矬子里拔将军\"）。\n        alpha_qualified_candidates = [\n            c for c in candidates\n            if c[5] > ALPHA_GATE_THRESHOLD or c[3] > SORTINO_ALPHA_EXEMPTION\n        ]\n\n        if not alpha_qualified_candidates:\n            # 全组候选 alpha ≤ threshold 且 sortino ≤ exemption → 空权重（持仓现金），\n            # 标记 no_positive_alpha\n            # 字段名保留 no_positive_alpha（向下兼容下游消费方），语义为\"无合格 alpha/Sortino 候选\"\n            alpha_strs = [\n                f\"{c[0]}(alpha={c[5]:.2f}%, sortino={c[3]:.4f})\" for c in candidates\n            ]\n            logger.warning(\n                f\"[MatrixBacktest] {group_id}: ALL {len(candidates)} candidates have \"\n                f\"alpha <= {ALPHA_GATE_THRESHOLD}% AND sortino <= {SORTINO_ALPHA_EXEMPTION} \"\n                f\"(cannot beat SPY within tolerance, no Sortino exemption) — \"\n                f\"{alpha_strs}. \"\n                f\"Group produces EMPTY weights (hold cash). Marked no_positive_alpha.\"\n            )\n            report.warnings.append(\n                f\"{group_id}: no_positive_alpha \"\n                f\"(all {len(candidates)} candidates alpha <= {ALPHA_GATE_THRESHOLD}% \"\n                f\"AND sortino <= {SORTINO_ALPHA_EXEMPTION})\"\n            )\n            # 标记已 append 的 GroupBacktestResult 条目（供审计追溯）\n            for gr in report.group_results:\n                if gr.group_id == group_id:\n                    gr.no_positive_alpha = True\n            return []", "old_string": "        # 迭代 #12：alpha 硬门槛（experience.md #8：正超额是排序前的硬门槛）\n        # 迭代 #16：阈值从 alpha>0 放宽至 alpha > ALPHA_GATE_THRESHOLD (-2%)。\n        #   动机：SPX 成分股 vs SPY 存在结构性近零 alpha，严格 alpha>0 门槛导致\n        #   4/6 组空仓（Iter #15 reoptimize 实证）。-2% 仍过滤\"灾难性跑输\"，\n        #   同时保留\"小幅跑输 SPY 但 Sortino/DD 优秀\"的候选。\n        #   Walk-Forward（Iter #13）仍用 -5% 单轮下限 + avg>0 汇总门槛作 OOS 校验，\n        #   放宽 in-sample gate 不削弱 OOS 验证强度。\n        # 顺序：健全性（Iter #11）→ 风险（DD，Tier 1/2/3）→ alpha 门槛（本步）→ 排序\n        #\n        # 注意：这一步在 candidates 构建后、Tier 1 前，确保 Tier 1/2/3 只在合格 alpha 候选中进行。\n        # 如果某组所有候选 alpha ≤ ALPHA_GATE_THRESHOLD，该组空仓（hold cash），\n        # 不强行选严重跑输 SPY 的策略\n        # （experience.md #8：\"没有候选满足门槛时，正确动作是空仓/降现金/回退 benchmark，\n        #   不是矬子里拔将军\"）。\n        alpha_qualified_candidates = [\n            c for c in candidates if c[5] > ALPHA_GATE_THRESHOLD\n        ]\n\n        if not alpha_qualified_candidates:\n            # 全组 alpha ≤ threshold → 空权重（持仓现金），标记 no_positive_alpha\n            # 字段名保留 no_positive_alpha（向下兼容下游消费方），语义为\"无合格 alpha 候选\"\n            alpha_strs = [f\"{c[0]}({c[5]:.2f}%)\" for c in candidates]\n            logger.warning(\n                f\"[MatrixBacktest] {group_id}: ALL {len(candidates)} candidates have \"\n                f\"alpha <= {ALPHA_GATE_THRESHOLD}% (cannot beat SPY within tolerance) — \"\n                f\"{alpha_strs}. \"\n                f\"Group produces EMPTY weights (hold cash). Marked no_positive_alpha.\"\n            )\n            report.warnings.append(\n                f\"{group_id}: no_positive_alpha \"\n                f\"(all {len(candidates)} candidates alpha <= {ALPHA_GATE_THRESHOLD}%)\"\n            )\n            # 标记已 append 的 GroupBacktestResult 条目（供审计追溯）\n            for gr in report.group_results:\n                if gr.group_id == group_id:\n                    gr.no_positive_alpha = True\n            return []"}
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
Now
---
 I
---
 need to verify
---
 my
---
 understanding
---
 of `
---
c[3
---
]` and
---
 `c[5]`.
---
 Looking
---
 at the candidates
---
 construction
---
 (
---
line 133
---
4):

```python
candidates
---
.append
---
((strategy
---
, params, results
---
, pso
---
, pdd
---
, alpha
---
))
```

So the
---
 tuple is
---
:
- c
---
[0]
---
 = strategy
- c[
---
1] = params
---

- c[2]
---
 = results
- c[
---
3] = p
---
so (portfolio
---
 sortino)
- c[
---
4] = pdd
---
 (portfolio max
---
 drawdown)
- c[
---
5] = alpha
---


Good
---
, my edit using
---
 `c[5
---
]` for
---
 alpha and `c[3
---
]` for sortino is
---
 correct.

Now let me write
---
 the tests.
---
 I'll
---
 add them
---
 to the test
---
_alpha_gate
---
.py file. Let
---
 me also
---
 check the existing test
---
 file to
---
 follow
---
 its
---
 conventions
---
.
---
现在让我来编写测试
---
。首先
---
，让我
---
验证
---
一下修改
---
是否
---
正确。
---
{"file_path": "/Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py", "limit": 90, "offset": 1336}
---
1336→        #      Tier 3 (fallback): Tier 2 为空 → 按 DD 升序，标记 dd_constrained=True
1337→        candidates: list[
1338→            tuple[str, dict, list[SingleBacktestResult], float, float, float]
1339→        ] = []
1340→        for (strategy, params, results) in group_results:
1341→            pso = _portfolio_sortino_from_results(results)
1342→            pdd = _portfolio_max_drawdown_from_results(results)
1343→            # 复用 _combine_daily_returns 计算 alpha（与 per-strategy 选择一致）
1344→            alpha = _compute_alpha(_combine_daily_returns(results), spy_returns)
1345→            candidates.append((strategy, params, results, pso, pdd, alpha))
1346→
1347→        # 迭代 #12：alpha 硬门槛（experience.md #8：正超额是排序前的硬门槛）
1348→        # 迭代 #16：阈值从 alpha>0 放宽至 alpha > ALPHA_GATE_THRESHOLD (-2%)。
1349→        #   动机：SPX 成分股 vs SPY 存在结构性近零 alpha，严格 alpha>0 门槛导致
1350→        #   4/6 组空仓（Iter #15 reoptimize 实证）。-2% 仍过滤"灾难性跑输"，
1351→        #   同时保留"小幅跑输 SPY 但 Sortino/DD 优秀"的候选。
1352→        #   Walk-Forward（Iter #13）仍用 -5% 单轮下限 + avg>0 汇总门槛作 OOS 校验，
1353→        #   放宽 in-sample gate 不削弱 OOS 验证强度。
1354→        # 迭代 #17：Sortino 豁免 —— 高 Sortino (> SORTINO_ALPHA_EXEMPTION=1.5)
1355→        #   的策略绕过 alpha gate。动机：Iter #16 reoptimize 实证 SPX 组 alpha
1356→        #   范围 -3.61% ~ -15.35%，-2% gate 仍不解锁 SPX 组；但部分策略 Sortino
1357→        #   极佳（下行风险控制优秀），只因"vs SPY 相对收益"不合格被拒。Constitution
1358→        #   L1 首要 KPI 是 Sortino（而非 alpha），本豁免让"Sortino 卓越但 alpha 跑输
1359→        #   SPY"的策略进入 Tier 1/2/3，不再被 alpha gate 一刀切。WF OOS 校验仍用
1360→        #   -5% 单轮下限 + avg>0，本豁免不削弱 OOS 验证强度。
1361→        # 顺序：健全性（Iter #11）→ 风险（DD，Tier 1/2/3）→ alpha 门槛（本步）→ 排序
1362→        #
1363→        # 注意：这一步在 candidates 构建后、Tier 1 前，确保 Tier 1/2/3 只在合格候选中进行。
1364→        # 合格定义：alpha > ALPHA_GATE_THRESHOLD  OR  sortino > SORTINO_ALPHA_EXEMPTION
1365→        # （二者满足其一即进入 Tier 1/2/3）
1366→        # 如果某组所有候选都不满足（alpha ≤ threshold 且 sortino ≤ exemption），
1367→        # 该组空仓（hold cash），不强行选严重跑输 SPY 且 Sortino 平庸的策略
1368→        # （experience.md #8："没有候选满足门槛时，正确动作是空仓/降现金/回退 benchmark，
1369→        #   不是矬子里拔将军"）。
1370→        alpha_qualified_candidates = [
1371→            c for c in candidates
1372→            if c[5] > ALPHA_GATE_THRESHOLD or c[3] > SORTINO_ALPHA_EXEMPTION
1373→        ]
1374→
1375→        if not alpha_qualified_candidates:
1376→            # 全组候选 alpha ≤ threshold 且 sortino ≤ exemption → 空权重（持仓现金），
1377→            # 标记 no_positive_alpha
1378→            # 字段名保留 no_positive_alpha（向下兼容下游消费方），语义为"无合格 alpha/Sortino 候选"
1379→            alpha_strs = [
1380→                f"{c[0]}(alpha={c[5]:.2f}%, sortino={c[3]:.4f})" for c in candidates
1381→            ]
1382→            logger.warning(
1383→                f"[MatrixBacktest] {group_id}: ALL {len(candidates)} candidates have "
1384→                f"alpha <= {ALPHA_GATE_THRESHOLD}% AND sortino <= {SORTINO_ALPHA_EXEMPTION} "
1385→                f"(cannot beat SPY within tolerance, no Sortino exemption) — "
1386→                f"{alpha_strs}. "
1387→                f"Group produces EMPTY weights (hold cash). Marked no_positive_alpha."
1388→            )
1389→            report.warnings.append(
1390→                f"{group_id}: no_positive_alpha "
1391→                f"(all {len(candidates)} candidates alpha <= {ALPHA_GATE_THRESHOLD}% "
1392→                f"AND sortino <= {SORTINO_ALPHA_EXEMPTION})"
1393→            )
1394→            # 标记已 append 的 GroupBacktestResult 条目（供审计追溯）
1395→            for gr in report.group_results:
1396→                if gr.group_id == group_id:
1397→                    gr.no_positive_alpha = True
1398→            return []
1399→
1400→        # 后续 Tier 1/2/3 在合格 alpha 候选中进行
1401→        candidates = alpha_qualified_candidates
1402→
1403→        # Tier 1: DD ≤ 20% AND Sortino > 0.5
1404→        compliant = [
1405→            c for c in candidates
1406→            if c[4] <= MAX_PORTFOLIO_DRAWDOWN_PCT and c[3] > MIN_SORTINO_THRESHOLD
1407→        ]
1408→        if compliant:
1409→            # Tier 1 命中：按 Alpha 降序取 top-K
1410→            ranked = sorted(compliant, key=lambda x: x[5], reverse=True)
1411→            dd_constrained = False
1412→            logger.info(
1413→                f"[MatrixBacktest] {group_id}: DD + Sortino filter passed — "
1414→                f"{len(compliant)}/{len(candidates)} candidates compliant "
1415→                f"(DD <= {MAX_PORTFOLIO_DRAWDOWN_PCT}% AND Sortino > {MIN_SORTINO_THRESHOLD})"
1416→            )
1417→        else:
1418→            # Tier 2: 放宽 Sortino 门槛，仅保留 DD 约束
1419→            dd_compliant = [
1420→                c for c in candidates if c[4] <= MAX_PORTFOLIO_DRAWDOWN_PCT
1421→            ]
1422→            if dd_compliant:
1423→                # Tier 2 命中：按 Alpha 降序取 top-K（dd_constrained 仍为 False）
1424→                ranked = sorted(dd_compliant, key=lambda x: x[5], reverse=True)
1425→                dd_constrained = False
1426→
---
1336→        #      Tier 3 (fallback): Tier 2 为空 → 按 DD 升序，标记 dd_constrained=True
1337→        candidates: list[
1338→            tuple[str, dict, list[SingleBacktestResult], float, float, float]
1339→        ] = []
1340→        for (strategy, params, results) in group_results:
1341→            pso = _portfolio_sortino_from_results(results)
1342→            pdd = _portfolio_max_drawdown_from_results(results)
1343→            # 复用 _combine_daily_returns 计算 alpha（与 per-strategy 选择一致）
1344→            alpha = _compute_alpha(_combine_daily_returns(results), spy_returns)
1345→            candidates.append((strategy, params, results, pso, pdd, alpha))
1346→
1347→        # 迭代 #12：alpha 硬门槛（experience.md #8：正超额是排序前的硬门槛）
1348→        # 迭代 #16：阈值从 alpha>0 放宽至 alpha > ALPHA_GATE_THRESHOLD (-2%)。
1349→        #   动机：SPX 成分股 vs SPY 存在结构性近零 alpha，严格 alpha>0 门槛导致
1350→        #   4/6 组空仓（Iter #15 reoptimize 实证）。-2% 仍过滤"灾难性跑输"，
1351→        #   同时保留"小幅跑输 SPY 但 Sortino/DD 优秀"的候选。
1352→        #   Walk-Forward（Iter #13）仍用 -5% 单轮下限 + avg>0 汇总门槛作 OOS 校验，
1353→        #   放宽 in-sample gate 不削弱 OOS 验证强度。
1354→        # 迭代 #17：Sortino 豁免 —— 高 Sortino (> SORTINO_ALPHA_EXEMPTION=1.5)
1355→        #   的策略绕过 alpha gate。动机：Iter #16 reoptimize 实证 SPX 组 alpha
1356→        #   范围 -3.61% ~ -15.35%，-2% gate 仍不解锁 SPX 组；但部分策略 Sortino
1357→        #   极佳（下行风险控制优秀），只因"vs SPY 相对收益"不合格被拒。Constitution
1358→        #   L1 首要 KPI 是 Sortino（而非 alpha），本豁免让"Sortino 卓越但 alpha 跑输
1359→        #   SPY"的策略进入 Tier 1/2/3，不再被 alpha gate 一刀切。WF OOS 校验仍用
1360→        #   -5% 单轮下限 + avg>0，本豁免不削弱 OOS 验证强度。
1361→        # 顺序：健全性（Iter #11）→ 风险（DD，Tier 1/2/3）→ alpha 门槛（本步）→ 排序
1362→        #
1363→        # 注意：这一步在 candidates 构建后、Tier 1 前，确保 Tier 1/2/3 只在合格候选中进行。
1364→        # 合格定义：alpha > ALPHA_GATE_THRESHOLD  OR  sortino > SORTINO_ALPHA_EXEMPTION
1365→        # （二者满足其一即进入 Tier 1/2/3）
1366→        # 如果某组所有候选都不满足（alpha ≤ threshold 且 sortino ≤ exemption），
1367→        # 该组空仓（hold cash），不强行选严重跑输 SPY 且 Sortino 平庸的策略
1368→        # （experience.md #8："没有候选满足门槛时，正确动作是空仓/降现金/回退 benchmark，
1369→        #   不是矬子里拔将军"）。
1370→        alpha_qualified_candidates = [
1371→            c for c in candidates
1372→            if c[5] > ALPHA_GATE_THRESHOLD or c[3] > SORTINO_ALPHA_EXEMPTION
1373→        ]
1374→
1375→        if not alpha_qualified_candidates:
1376→            # 全组候选 alpha ≤ threshold 且 sortino ≤ exemption → 空权重（持仓现金），
1377→            # 标记 no_positive_alpha
1378→            # 字段名保留 no_positive_alpha（向下兼容下游消费方），语义为"无合格 alpha/Sortino 候选"
1379→            alpha_strs = [
1380→                f"{c[0]}(alpha={c[5]:.2f}%, sortino={c[3]:.4f})" for c in candidates
1381→            ]
1382→            logger.warning(
1383→                f"[MatrixBacktest] {group_id}: ALL {len(candidates)} candidates have "
1384→                f"alpha <= {ALPHA_GATE_THRESHOLD}% AND sortino <= {SORTINO_ALPHA_EXEMPTION} "
1385→                f"(cannot beat SPY within tolerance, no Sortino exemption) — "
1386→                f"{alpha_strs}. "
1387→                f"Group produces EMPTY weights (hold cash). Marked no_positive_alpha."
1388→            )
1389→            report.warnings.append(
1390→                f"{group_id}: no_positive_alpha "
1391→                f"(all {len(candidates)} candidates alpha <= {ALPHA_GATE_THRESHOLD}% "
1392→                f"AND sortino <= {SORTINO_ALPHA_EXEMPTION})"
1393→            )
1394→            # 标记已 append 的 GroupBacktestResult 条目（供审计追溯）
1395→            for gr in report.group_results:
1396→                if gr.group_id == group_id:
1397→                    gr.no_positive_alpha = True
1398→            return []
1399→
1400→        # 后续 Tier 1/2/3 在合格 alpha 候选中进行
1401→        candidates = alpha_qualified_candidates
1402→
1403→        # Tier 1: DD ≤ 20% AND Sortino > 0.5
1404→        compliant = [
1405→            c for c in candidates
1406→            if c[4] <= MAX_PORTFOLIO_DRAWDOWN_PCT and c[3] > MIN_SORTINO_THRESHOLD
1407→        ]
1408→        if compliant:
1409→            # Tier 1 命中：按 Alpha 降序取 top-K
1410→            ranked = sorted(compliant, key=lambda x: x[5], reverse=True)
1411→            dd_constrained = False
1412→            logger.info(
1413→                f"[MatrixBacktest] {group_id}: DD + Sortino filter passed — "
1414→                f"{len(compliant)}/{len(candidates)} candidates compliant "
1415→                f"(DD <= {MAX_PORTFOLIO_DRAWDOWN_PCT}% AND Sortino > {MIN_SORTINO_THRESHOLD})"
1416→            )
1417→        else:
1418→            # Tier 2: 放宽 Sortino 门槛，仅保留 DD 约束
1419→            dd_compliant = [
1420→                c for c in candidates if c[4] <= MAX_PORTFOLIO_DRAWDOWN_PCT
1421→            ]
1422→            if dd_compliant:
1423→                # Tier 2 命中：按 Alpha 降序取 top-K（dd_constrained 仍为 False）
1424→                ranked = sorted(dd_compliant, key=lambda x: x[5], reverse=True)
1425→                dd_constrained = False
1426→
---
The
---
 edit is correct
---
. Now
---
 let
---
 me write the tests. I
---
 need to handle
---
 the fact
---
 that the Sort
---
ino value
---
 comes
---
 from `_portfolio_sortino_from
---
_results
---
(results
---
)
---
`, not
---
 from `_
---
compute_alpha`. So
---
 to
---
 mock the Sortino,
---
 I need to either
---
:
1. Construct
---
 returns
---
 series
---
 that produce
---
 a
---
 specific Sortino value (
---
hard,
---
 due to variance
---
)
2. Patch
---
 `_portfolio_sortino_from_results
---
` to return
---
 a specific value
---


Looking
---
 at the existing tests, they
---
 patch
---
 `_compute_alpha` to control
---
 alpha
---
 precisely
---
. For Sortino, I
---
 should patch `_portfolio_sortino
---
_from_results` to control
---
 the Sortino value precisely
---
.

Wait
---
, but `_
---
portfolio_sortino_from_results`
---
 is called in the
---
 candidates construction loop
---
. If
---
 I patch
---
 it globally
---
, it would
---
 return
---
 the same value
---
 for all strategies
---
. That
---
's fine
---
 for single
---
-str
---
ategy tests.
---
 For multi-strategy tests,
---
 I might
---
 need a
---
 side_effect.

Let me think
---
 about the test
---
 scenarios
---
:

1. **High
---
 Sortino exem
---
pts
---
 from alpha gate
---
**:
---
 alpha
---
=-5%
---
 (below -
---
2%
---
 gate
---
), sort
---
ino=2
---
.0 (above
---
 1.5
---
 exemption) → should
---
 pass gate
---
, weights
---
 non-empty
2. **
---
Low Sortino still
---
 needs
---
 alpha**:
---
 alpha=-5
---
% (below -2%
---
 gate), sortino=0
---
.3
---
 (below 1
---
.5 exemption) → should
---
 be
---
 rejected, empty
---
 weights
3. **DD
---
 still mandatory
---
**: alpha=-5%,
---
 sortino=2.0
---
 (ex
---
empt
---
ed), but DD
---
=25% (>
---
 20
---
%) → should still
---
 be filtered
---
 by
---
 DD
---
 (Tier
---
 2
---
 fallback
---
 or
---
 dd
---
_con
---
strained). Actually, with
---
 DD=25%,
---
 Tier
---
 1 fails
---
 (DD>
---
20%), Tier 2 fails
---
 (DD>20%),
---
 Tier 3 fallback
---
 selects
---
 by
---
 lowest
---
 DD and
---
 marks dd
---
_constrained. So
---
 the strategy would
---
 still be selected
---
 but
---
 marked
---
 dd_constrained. Hmm
---
, let me re
---
-read the spec
---
.

The
---
 user
---
 said
---
: "DD
---
 
---
仍强制" (DD still
---
 mandatory). Let
---
 me think about what
---
 this
---
 means. The DD
---
 constraint is in
---
 Tier 1/
---
2/
---
3,
---
 not in the alpha
---
 gate. The Sort
---
ino exemption only bypass
---
es the alpha gate. After
---
 that, the candidate
---
 still
---
 goes through Tier
---
 1/2/
---
3 which
---
 has
---
 DD
---
 constraints.
---
 But
---
 Tier
---
 3 is
---
 a fallback that
---
 selects
---
 by lowest DD even
---
 if all exceed
---
 20%.
---
 So "
---
DD still mandatory" might mean
---
:

---
- If
---
 all
---
 candidates have DD >
---
 20%, the group
---
 still
---
 goes
---
 to
---
 Tier 3 fallback
---
 (dd_constrained=True
---
), not empty
---
.


---
Actually, looking
---
 more
---
 carefully,
---
 the DD "
---
硬
---
约束
---
" (hard constraint
---
) is in Tier 1
---
 (DD ≤
---
 20%),
---
 but there
---
's
---
 a Tier
---
 3
---
 fallback.
---
 So DD
---
 is not strictly
---
 mandatory
---
 in the sense of "
---
empty weights
---
 if DD > 20%
---
". 


---
Let me reconsider
---
.
---
 The test
---
 "DD 
---
仍强制" probably
---
 means: the Sort
---
ino
---
 exemption does
---
 NOT bypass the DD check
---
. A
---
 candidate with high
---
 Sortino +
---
 bad
---
 alpha + bad
---
 DD should
---
 still be handled
---
 by the
---
 DD filter (Tier 1
---
/2/3),
---
 not get
---
 a free
---
 pass. 


---
Let
---
 me think about a
---
 cleaner
---
 test:
---
 
- Candidate
---
:
---
 alpha=-5% (below
---
 gate), sortino=2
---
.0 (ex
---
empt
---
ed by
---
 Sortino), DD=25
---
% (>
---
 20%)
- Expected
---
: passes
---
 alpha
---
 gate (due
---
 to Sortino exemption
---
), but Tier 1 fails
---
 (DD>20%),
---
 Tier 2 fails (DD
---
>20%), Tier 3
---
 fallback selects
---
 it
---
 with dd_constrained=True

---
- So
---
 weights
---
 non-empty but
---
 dd
---
_constrained=True

This
---
 shows
---
 DD
---
 filter
---
 still applies
---
 after
---
 the Sortino exemption. That
---
's a
---
 good test for
---
 "DD 
---
仍强制".

Actually
---
, wait
---
. Let me re-read:
---
 the
---
 spec
---
 says "DD 仍强制
---
" —
---
 DD still mandatory. The most
---
 meaningful
---
 interpretation
---
 is that the Sort
---
ino exemption ONLY
---
 bypasses the alpha
---
 gate, NOT
---
 the DD filter. So
---
 a
---
 high
---
-S
---
ortino,
---
 bad-alpha,
---
 bad-DD candidate
---
 would
---
 still hit
---
 the DD filter.


---
Let me design
---
 the tests
---
:


---
1. **test
---
_sortino_exemption_constant
---
_exists
---
**: SORT
---
INO_ALPHA_EXEMPTION =
---
 1.5

---
2. **test_high
---
_sortino_exem
---
pts_alpha
---
_gate**: alpha=-5%
---
 (fails
---
 gate
---
), sortino=2.
---
0 (exempt
---
ed),
---
 DD=10
---
% (good
---
) → weights
---
 non-empty, no
---
_positive_alpha
---
=False
3. **test
---
_low_sortino_st
---
ill_ne
---
eds_alpha**: alpha=-5
---
% (fails
---
 gate), sortino=0
---
.3 (not
---
 exempt
---
ed), DD=10%
---
 → empty
---
 weights, no_positive_alpha=True
---

4. **test_dd
---
_still_mandatory_with
---
_ex
---
emption**: alpha=-5%,
---
 sortino=2.0
---
 (exempted),
---
 DD=25% (>
---
20%) → passes
---
 alpha gate but
---
 DD
---
 filter applies
---
;
---
 weights
---
 non-empty but dd_constrained
---
=True (Tier
---
 3 fallback)
5.
---
 **test_min
---
_sortino_st
---
ill_mandatory**: This
---
 is about
---
 the MIN
---
_SORTINO_THRESHOLD
---
=0.5 in
---
 Tier 1. A
---
 candidate with alpha
---
=-5%,
---
 sortino=2.0
---
 (exempted), DD
---
=10% should
---
 pass Tier
---
 1 (sort
---
ino>
---
0.5).
---
 But
---
 what about a candidate with alpha
---
=
---
+
---
1% (passes alpha
---
 gate), sortino=0
---
.3 (below
---
 MIN_SORTINO_THRESHOLD),
---
 DD=10%?
---
 This
---
 candidate
---
 passes
---
 alpha gate (
---
alpha
---
>-
---
2%)
---
 but fails Tier 1 Sort
---
ino>
---
0.5.
---
 It would go to Tier 
---
2 (DD-only
---
).
---
 Hmm
---
, this tests
---
 that
---
 MIN
---
_SORTINO
---
_THRESHOLD
---
 still applies in
---
 Tier 1 even
---
 with
---
 the
---
 exemption.

Actually, let me
---
 reconsider
---
 "
---
最低
---
 Sortino 
---
仍强制" (min
---
 Sortino
---
 still mandatory). The Sort
---
ino exemption (
---
1.5
---
) is for
---
 bypass
---
ing the alpha gate. The
---
 MIN_SORTINO_THRESHOLD (0
---
.5) is for Tier
---
 1 compliance
---
. These are different
---
 thresholds
---
. The
---
 test should verify that the MIN
---
_SORTINO_THRESHOLD in
---
 Tier 1 is not
---
 removed
---
/b
---
ypassed by
---
 the Sort
---
ino exemption.

A
---
 candidate
---
 with: alpha=-5%
---
 (fails gate), sortino
---
=0.6
---
 (above
---
 MIN_SORTINO_THRESHOLD 
---
0.5
---
 but below exemption
---
 1.5)
---
 → NOT
---
 exempted (
---
sortino <
---
 1.5),
---
 so fails
---
 alpha gate →
---
 empty weights. This shows that
---
 just
---
 passing
---
 MIN
---
_SORTINO_THRESHOLD is
---
 not enough to
---
 be
---
 exempted;
---
 you need sortino > 
---
1.5 for
---
 exemption.

Alternatively
---
:
---
 alpha=
---
+1% (passes gate
---
 normally
---
), sortino=0.
---
3 (below MIN_SORTINO
---
_THRESHOLD),
---
 DD=10% → passes
---
 alpha gate,
---
 but Tier
---
 1 fails (sortino
---
 ≤
---
 0.5), Tier
---
 2 (
---
DD-only)
---
 passes →
---
 weights non-empty.
---
 This shows MIN
---
_SORTINO_THRESHOLD still
---
 filters
---
 in Tier 1.

Hmm
---
, let
---
 me think about which
---
 is more
---
 meaningful. The spec
---
 says "最低 Sortino 
---
仍强制" —
---
 this
---
 likely
---
 means the MIN_SORTINO_THRESHOLD
---
=0.5 in Tier
---
 1 is still enforced
---
. The
---
 Sort
---
ino exemption (
---
1.5) is a
---
 higher bar
---
 that
---
 bypass
---
es the alpha gate,
---
 but once
---
 past
---
 the gate
---
, the Tier
---
 1 filter
---
 still requires
---
 sort
---
ino > 0.5
---
 (and
---
 DD ≤
---
 20%).


---
Actually, re-reading:
---
 if
---
 a candidate has
---
 sortino=
---
2.0 (exempt
---
ed), it automatically
---
 passes sortino > 
---
0.5
---
 in Tier 1. So
---
 the MIN
---
_SORTINO_THRESHOLD is automatically
---
 satisfied for
---
 exempt
---
ed candidates. The test
---
 "最低 Sortino 
---
仍强制" might be testing
---
 that a candidate with sort
---
ino between
---
 0.5 and
---
 1.5 (
---
passes
---
 MIN_SORTINO_THRESHOLD but
---
 not exemption
---
) still
---
 needs alpha >
---
 -
---
2% to
---
 pass the gate
---
. This is the "
---
low
---
 Sortino still needs alpha"
---
 test #
---
3
---
.

Let me reconsider
---
.
---
 Maybe
---
 "
---
最低 Sortino 
---
仍强制" means:
---
 the
---
 MIN
---
_SORTINO_THRESHOLD=
---
0.5 in Tier 
---
1 is still applied
---
.
---
 So
---
 a candidate with:

---
- alpha=+1%
---
 (passes alpha gate)

---
- sortino=0
---
.3 (below MIN_SORT
---
INO_THRESHOLD 0.5
---
)
- DD=10%

---
→ passes
---
 alpha gate,
---
 but Tier 1 rejects
---
 (sortino ≤
---
 0.5), falls
---
 to Tier 2 (DD
---
-only),
---
 weights non-empty.


---
This shows MIN_SORTINO_THRESHOLD
---
 still filters in Tier 1
---
. This
---
 is a
---
 regression
---
 test to
---
 ensure the Sort
---
ino exemption change
---
 didn't accidentally
---
 remove
---
 the MIN
---
_SORTINO_THRESHOLD filter
---
.

6
---
. **test_sortino_ex
---
emption_boundary**: alpha=-5
---
% (fails gate), sort
---
ino=1
---
.5 (ex
---
actly at exemption
---
 boundary) → rejected
---
 (using
---
 > strict
---
 comparison, sort
---
ino must
---
 be > 1.5
---
)
7. **test_sort
---
ino_exemption_
---
just_above_boundary
---
**: alpha=-5% (
---
fails gate), sortino=
---
1.51
---
 (just
---
 above exemption
---
) → passes
---
 gate
---
,
---
 weights non-empty

Let me
---
 also think
---
 about how
---
 to mock sort
---
ino. The sort
---
ino is
---
 computed by
---
 `_portfolio_sortino_from_results
---
(results)`. I
---
 need
---
 to patch this
---
 function. For
---
 single-strategy tests, I
---
 can use
---
 `return_value`.
---
 For the
---
 test
---
 with
---
 DD, I also
---
 need to control
---
 `_portfolio_max
---
_draw
---
down_from
---
_results`.

Actually, looking
---
 at the existing tests, they
---
 patch `_compute_alpha` with
---
 `return_value=
---
mock_alpha
---
`. But
---
 `_compute
---
_alpha` is called
---
 in multiple
---
 places:
1. In the
---
 per-str
---
ategy best
---
 params
---
 selection
---
 (
---
line 124
---
4):
---
 `alpha = _compute_alpha
---
(comb
---
ined, spy
---
_returns)` 

---
2. In the candidates construction
---
 (line 134
---
4): `alpha = _
---
compute_alpha(_
---
combine_daily_returns(results
---
), spy_returns)
---
`

If I patch `_compute
---
_alpha` with
---
 a
---
 constant `
---
return_value`, both
---
 calls get
---
 the same value. That's
---
 fine for single-strategy tests
---
.

For Sort
---
ino, `_
---
portfolio_sortino_from_results`
---
 is called:

---
1. In the per
---
-strategy best params selection (
---
line 124
---
1): `p
---
so
---
 = _compute_sort
---
ino(comb
---
ined)` — wait, this
---
 is `_
---
compute_sortino`,
---
 not `_portfolio_sortino_from
---
_results`
2. In the
---
 candidates construction (line 134
---
1): `p
---
so = _portfolio
---
_sortino_from_results(results)
---
`

Wait
---
, let
---
 me re
---
-check
---
. Line
---
 123
---
5
---
: `pso = _
---
compute_sortino(combined)`
---
 — this is in
---
 the per-strategy best params
---
 loop. Line 134
---
1: `pso =
---
 _portfolio_sortino_from_results
---
(results)` — this is in
---
 the candidates construction.

So in
---
 the candidates
---
 construction, it
---
's `_
---
portfolio_sortino_from_results`.
---
 I should patch that
---
.

Similarly
---
 for
---
 DD:
---
 `_portfolio_max_drawdown_from
---
_results` is called at
---
 line 1342
---
 in
---
 candidates
---
 construction.

Let me design
---
 the tests with
---
 patching:

---
- `
---
patch _
---
compute_alpha` with `return
---
_value`
---
 for alpha
---

- `patch _portfolio
---
_sortino_from_results` with
---
 `return_value` for sort
---
ino
- `patch _
---
portfolio_max_drawdown_from_results
---
` with
---
 `return_value` for DD
---
 (when
---
 needed)

But
---
 wait, `_
---
portfolio_sortino_from_results`
---
 is also used in the `
---
Group
---
Back
---
testResult
---
` construction
---
?
---
 No, looking
---
 at line 126
---
2
---
-1268, the
---
 `
---
GroupBacktestResult` uses
---
 `best_sort
---
ino` which
---
 comes
---
 from `_compute_sortino(comb
---
ined)` at
---
 line 124
---
1. So patch
---
ing `_portfolio_sortino_from
---
_results` only
---
 affects the candidates construction,
---
 which is what
---
 I want.

Actually, wait
---
. Let me re-read
---
 lines
---
 1240
---
-1244
---
:
```python
combined
---
 = _combine
---
_daily_returns(results
---
)
ps
---
 = _compute_sh
---
arpe
---
(combined)
p
---
so = _compute_sortino
---
(combined)
alpha
---
 = _compute_alpha(combined
---
, spy_returns)
```


---
This is in the per-str
---
ategy best params loop.
---
 Here
---
 `pso`
---
 is from `_compute_sortino
---
`.


---
Then at
---
 line 1263
---
: `portfolio
---
_sortino=
---
best_sortino` —
---
 uses
---
 `
---
best_sortino` which
---
 is `
---
pso` from above
---
.

So the `
---
GroupBacktestResult.port
---
folio_sortino` comes
---
 from `_compute_sortino(comb
---
ined)`, not
---
 `_
---
portfolio_sortino_from_results`.


---
But in the candidates construction (
---
line 1341):
---
 `pso = _portfolio
---
_sortino_from_results(results)`
---
 — this is the Sort
---
ino used
---
 for
---
 the alpha gate exemption
---
 and
---
 Tier 1 filter
---
.

So I
---
 need to patch
---
 `_portfolio_sortino_from_results
---
` to control the Sort
---
ino in
---
 the candidates
---
 construction. And `_compute_alpha
---
` to
---
 control alpha
---
.

Let
---
 me also check
---
 if
---
 `_portfolio_sortino_from_results
---
` is called
---
 anywhere
---
 else that
---
 might
---
 interfere
---
. Let
---
 me search
---
.


---
Actually, looking
---
 at the code, `_
---
portfolio_sortino_from_results`
---
 is only
---
 called once
---
 in `_
---
run_group
---
` at
---
 line 1341. And
---
 `_compute
---
_sortino` is called
---
 in the per
---
-strategy best params loop.
---
 So patch
---
ing `_portfolio_sortino_from
---
_results` is safe.


---
However
---
, there
---
's a subt
---
lety:
---
 if
---
 I patch `_compute_alpha
---
` with a constant return
---
_value, it will also
---
 affect the per
---
-strategy best params selection (
---
line 1244
---
). For
---
 single-strategy tests, this
---
 is
---
 fine (only
---
 one strategy,
---
 so best params selection
---
 is trivial). For multi-str
---
ategy tests, all
---
 strategies would have
---
 the same alpha, which might
---
 cause
---
 issues
---
 with the "
---
best alpha
---
" selection. But since
---
 I
---
'm doing
---
 single-strategy tests
---
 mostly
---
, this
---
 should
---
 be fine.

Let me also
---
 consider
---
: do
---
 I need to patch
---
 `_compute
---
_sortino` (
---
used
---
 in per
---
-strategy best params)?
---
 For
---
 the
---
 alpha
---
 gate exemption, the
---
 Sortino comes
---
 from `_portfolio_sortino_from
---
_results` in
---
 the candidates construction. The
---
 `_
---
compute_sortino` in the
---
 per-strategy best params loop
---
 only
---
 affects `
---
best_sortino` which is
---
 stored in `
---
GroupBacktestResult.port
---
folio_sortino`.
---
 It doesn't affect
---
 the gate
---
 logic
---
. So I don't need
---
 to patch `_compute_sortino
---
`.

OK
---
, let me write the tests
---
 now. I'll add a
---
 new test
---
 class `TestSortinoAlpha
---
Exemption` to `
---
test_alpha
---
_gate.py`.


---
Let me also update the module
---
 doc
---
string of
---
 test
---
_alpha_gate.py to mention
---
 Iter #
---
17.

Here
---
's
---
 my plan for 
---
7 tests:

1. `
---
test_sortino_exemption_constant
---
_exists`
---
 — SORTINO_ALPHA_EXEM
---
PTION = 1.5
---

2. `test_high
---
_sortino_exempts_negative
---
_alpha` — alpha=-5
---
%,
---
 sortino=2.0
---
,
---
 DD=10% → weights
---
 non-empty

---
3. `test_low
---
_sortino_does
---
_not_exempt`
---
 — alpha=-5%, sort
---
ino=0.3,
---
 DD=10% → empty
---
 weights, no_positive_alpha=True
---

4. `test_dd
---
_still_mandatory_with
---
_sortino_ex
---
emption` — alpha=-5
---
%, sortino=2.
---
0, DD=25
---
% →
---
 passes gate
---
,
---
 but DD
---
 filter applies
---
 (Tier 3 fallback,
---
 dd_constrained=True)
5
---
. `test_min
---
_sortino_threshold
---
_st
---
ill_en
---
forced
---
_in
---
_tier1` — alpha
---
=+
---
1%, sortino=0
---
.3, DD
---
=10% → passes
---
 alpha gate, but
---
 Tier 1 rejects
---
 (sortino ≤
---
 0.5), Tier
---
 2 (DD-only)
---
 passes → weights non-empty,
---
 dd_constrained=False (
---
Tier
---
 2 is
---
 not dd
---
_constrained)


---
Hmm
---
, wait
---
. Test
---
 
---
5 is
---
 a
---
 bit confusing. Let me reconsider
---
. "
---
最低 Sortino 仍强制
---
" (
---
min Sortino still
---
 mandatory).
---
 The MIN_SORTINO_THRESHOLD=
---
0.5 in Tier 
---
1. 


---
Actually, maybe
---
 the intent
---
 is:
---
 a candidate with sortino just
---
 above MIN
---
_SORTINO_THRESHOLD (0
---
.5) but
---
 below the
---
 exemption (1
---
.5) should
---
 NOT
---
 be
---
 exempted from
---
 the
---
 alpha gate. So
---
:

---
- alpha=-5% (
---
fails gate), sortino=
---
0.6 (above
---
 MIN_SORTINO_THRESHOLD but
---
 below exemption)
---
 → NOT
---
 exempted →
---
 empty weights


---
This shows that passing the
---
 MIN_SORTINO_THRESHOLD doesn
---
't give
---
 you
---
 an
---
 exemption; you need sortino
---
 > 1.5 for
---
 that
---
. This is the
---
 "low Sortino does
---
 not exempt" test.

But
---
 "
---
最低 Sortino 
---
仍强制" might
---
 also mean
---
: the Tier 1 MIN
---
_SORTINO_THRESHOLD filter
---
 is still applied. So
---
 even
---
 with the exemption, a
---
 candidate needs
---
 sortino > 0.
---
5 to pass Tier
---
 1. But
---
 if
---
 sortino > 1
---
.5 (exemption),
---
 it's
---
 automatically > 0.5
---
, so this
---
 is trivial
---
ly satisfied.

I
---
 think the most
---
 meaningful test for
---
 "最低 Sortino 
---
仍强制" is: a
---
 candidate that
---
 passes the
---
 alpha gate (via
---
 positive
---
 alpha)
---
 but has
---
 sortino <
---
 MIN_SORTINO_THRESHOLD should
---
 still be filtered out
---
 of
---
 Tier 1 (
---
fall
---
 to Tier 2). This
---
 is a
---
 regression test to ensure the Sort
---
ino
---
 exemption change
---
 didn't break
---
 the Tier 1 filter
---
.

Let me design
---
:

---
-
---
 alpha=+1% (
---
passes alpha
---
 gate normally,
---
 no
---
 exemption
---
 needed)
- sortino=
---
0.3 (below MIN
---
_SORTINO_THRESHOLD 0.
---
5)
- DD=10
---
%
→ passes
---
 alpha gate, Tier
---
 1 rejects (sortino
---
 ≤ 0.5),
---
 Tier 2 (DD-only
---
) passes → weights non-empty
---


This verifies
---
 MIN
---
_SORTINO_THRESHOLD still
---
 filters
---
 in Tier 1.


---
Actually, let
---
 me reconsider the
---
 
---
7 tests based
---
 on the user's spec:

---
- 高
---
 Sortino 
---
豁
---
免 (high
---
 Sortino exemption)
- 低
---
 Sortino 
---
仍需 alpha (low Sort
---
ino still needs alpha)
-
---
 DD 仍强制 (DD
---
 still mandatory)
- 
---
最低 Sortino 仍强制
---
 (min Sortino
---
 still mandatory)
- 
---
边界测试
---
 (boundary tests)

So that
---
's 5
---
 categories.
---
 The user said ~
---
7 tests. Let me do
---
:

1. `test_sort
---
ino_exemption_constant_exists`
---
 — constant
---
 =
---
 1.5
2
---
. `test_high
---
_sortino_exempts_negative
---
_alpha` — high
---
 Sortino
---
 exem
---
pts alpha
---
 gate (alpha
---
=-5%,
---
 sortino=2.0
---
 →
---
 passes)
3. `test
---
_low_sortino_does
---
_not_exempt` — low Sort
---
ino still needs alpha (
---
alpha=-5%, sortino
---
=0.3 → rejected
---
)

---
4. `test_dd
---
_still_mandatory_with_sort
---
ino_exemption` — DD
---
 still mandatory
---
 (alpha=-5%, sort
---
ino=2.0,
---
 DD=25% → DD
---
 filter applies)

---
5. `test_min
---
_sortino_threshold
---
_still_enforced`
---
 — min
---
 Sortino
---
 still enforced
---
 in
---
 Tier 1 (alpha=
---
+1%, sortino=
---
0.3 → Tier
---
 1 rejects,
---
 Tier 2 passes)
6
---
. `test_sortino_ex
---
emption_boundary_re
---
jected` — sort
---
ino=1.5 (
---
exactly
---
 at boundary) → rejected (>
---
strict
---
 comparison)
7. `test
---
_sortino_exemption_just
---
_above_boundary` — sortino
---
=1.51 (
---
just above)
---
 → passes

That
---
's 7 tests. Let
---
 me write
---
 them.

For
---
 the DD test (#
---
4), I need to think
---
 about what "DD
---
 still mandatory" means. With
---
 DD=25% (>
---
20
---
%):
- Tier 1
---
: DD ≤
---
 20% AND
---
 Sort
---
ino > 0.5
---
 → fails (DD > 
---
20%)
- Tier 
---
2: DD
---
 ≤
---
 20% → fails (
---
DD > 20%)

---
- Tier 3: fallback
---
,
---
 select by lowest DD,
---
 mark
---
 dd_constrained=True

So
---
 the candidate
---
 would still be selected
---
 (Tier
---
 3 fallback) but
---
 marked dd_constrained=True.
---
 The
---
 weights
---
 would
---
 be non-empty but dd_con
---
strained=True.


---
But
---
 is
---
 this "
---
DD still mandatory"? The Tier
---
 3 fallback means
---
 DD is not strictly mandatory (
---
a
---
 candidate with DD
---
 > 20% can
---
 still be selected). But
---
 the DD
---
 filter is
---
 still applied (
---
Tier 1 and
---
 2 reject
---
 it
---
). 


---
Actually
---
, I think the more
---
 meaningful test is: with
---
 multiple
---
 candidates, one
---
 with high Sortino +
---
 bad alpha
---
 + bad
---
 DD, and one with good
---
 alpha
---
 + good DD. The good
---
 candidate
---
 should be selected over
---
 the bad
---
-DD
---
 one
---
. But that
---
's complex.

Let me simplify
---
: the test should
---
 show
---
 that the Sortino exemption ONLY
---
 bypasses the alpha
---
 gate, not the DD filter
---
. A candidate with high
---
 Sortino + bad alpha
---
 + bad DD should
---
 still hit
---
 the DD filter (Tier 
---
1/2 reject
---
,
---
 Tier 3 fallback). The
---
 key
---
 assertion is that
---
 dd
---
_constrained=True (DD
---
 filter was
---
 triggered
---
),
---
 not that the candidate gets
---
 a free pass.

Actually,
---
 let me think
---
 about this
---
 differently. What
---
 if I
---
 test:
---
 a candidate with high Sortino
---
 + bad alpha
---
 + bad DD (
---
25%)
---
 and
---
 verify
---
 that it
---
 goes
---
 through
---
 the
---
 DD filter (dd_constrained
---
=True). This shows
---
 the
---
 DD
---
 filter is still applied after
---
 the Sortino
---
 exemption.

But
---
 wait, Tier
---
 3 fallback
---
 still selects the
---
 candidate. So the candidate
---
 is selected
---
 but
---
 marked
---
 dd_constrained. That
---
's not
---
 "DD mandatory
---
" in
---
 the strict
---
 sense.
---
 

Hmm
---
, let me re-read the
---
 Constitution
---
:
---
 "Con
---
stitution L
---
1: portfolio
---
 DD
---
 ≤ 20% 是
---
硬
---
约束". But
---
 the
---
 code has a
---
 Tier 3 fallback that selects
---
 even if DD
---
 > 20%.
---
 So the "
---
硬
---
约束" is more like "
---
strongly
---
 preferred,
---
 with fallback".
---
 

I think the test should
---
 verify
---
:
---
 the Sortino exemption does
---
 NOT bypass the DD check
---
 in
---
 Tier 1. A candidate
---
 with high Sortino + bad
---
 alpha + bad DD should NOT
---
 automatically
---
 pass Tier 1;
---
 it should still
---
 be filtered by DD.
---
 The
---
 assertion is that
---
 Tier
---
 1 rejects
---
 it (due
---
 to DD >
---
 20%), and it
---
 falls to Tier 3
---
 (dd_constrained=True).


---
Let me write the test
---
 this
---
 way:

---
- Single
---
 strategy
---
, alpha=-5% (
---
fails gate), sortino=
---
2.0 (exempt
---
ed), DD=25
---
%
- Expected: passes alpha
---
 gate (ex
---
empt
---
ed), Tier
---
 1 rejects (DD
---
 >
---
 20%), Tier 2
---
 rejects (DD > 20
---
%), Tier 3 fallback selects
---
 with
---
 dd_constrained=True
-
---
 Assertions
---
: weights
---
 non-empty, dd_constrained
---
=True,
---
 back
---
test
---
_dd_status
---
="dd_constrained"


---
This shows the DD
---
 filter is still applied (
---
dd
---
_constrained=True),
---
 not bypass
---
ed by
---
 the Sortino exemption.

OK
---
 let
---
 me write
---
 the tests now.


---
Actually
---
, I realize
---
 I need to be
---
 careful about
---
 patch
---
ing. Let
---
 me check
---
 if
---
 `_portfolio
---
_sortino_from_results` and
---
 `_portfolio
---
_max_drawdown_from_results`
---
 are module
---
-level functions
---
.
---
 Yes, they
---
 are. So I
---
 can patch them at
---
 `
---
mytrader.back
---
test.matrix_backtest._
---
portfolio_sortino_from_results`
---
 and `mytrader.back
---
test.matrix_backtest._portfolio
---
_max_drawdown_from_results`.


---
But wait, there's also
---
 `_compute_sortino` which
---
 is used in the per
---
-strategy best params loop.
---
 If I don
---
't patch it
---
, it
---
 will compute
---
 the real
---
 Sortino from the returns
---
 series. That
---
's fine for the per
---
-strategy best params (
---
it only
---
 affects `best
---
_sortino` stored
---
 in Group
---
BacktestResult,
---
 not the
---
 gate logic). But
---
 I need to make
---
 sure the per
---
-strategy best
---
 params selection
---
 still
---
 works. Since
---
 I'm using
---
 single
---
-strategy tests,
---
 there
---
's only
---
 one param
---
 combo
---
, so best params selection is
---
 trivial.

Let
---
 me also check: in
---
 the candidates construction,
---
 `_portfolio
---
_sortino_from_results(results
---
)` is called. If I
---
 patch it
---
 with
---
 a constant, all
---
 candidates get
---
 the same Sortino. For
---
 single-strategy tests, that
---
's fine.

Now
---
,
---
 one more thing: the `_
---
compute_alpha
---
` is called
---
 in two
---
 places:
1. Per
---
-strategy best params (
---
line 1244
---
): `alpha = _compute
---
_alpha(combined, spy_returns
---
)`
2. Candidates
---
 construction (line 1344
---
): `alpha = _compute
---
_alpha(_combine_daily_returns(results
---
), spy_returns)`

If
---
 I patch `_compute_alpha`
---
 with `
---
return_value=mock_alpha`,
---
 both calls return
---
 `
---
mock_alpha`. For single-str
---
ategy tests, this is fine
---
.

Let
---
 me write
---
 the tests now. I'll
---
 follow
---
 the existing patterns
---
 in test
---
_alpha_gate.py.

Let me
---
 also think
---
 about the `
---
test_min
---
_sortino_threshold
---
_still_enforced` test
---
. The
---
 scenario
---
:
- alpha=+1
---
% (passes alpha gate normally
---
)

---
- sortino=0.
---
3 (below MIN_SORTINO
---
_THRESHOLD 0.5)

---
- DD=10%

---
-
---
 Expected: passes alpha gate (
---
alpha >
---
 -2%), Tier 1
---
 rejects (sortino ≤ 
---
0.5), Tier 
---
2 (DD-only) passes
---
 → weights non-empty,
---
 dd_constrained=False


---
For
---
 this test, I need to
---
 patch:

---
- `_
---
compute_alpha` →
---
 return 
---
1.0 (positive
---
 alpha
---
)
- `_portfolio_sortino
---
_from_results` → return
---
 0.3 (below
---
 MIN_SORTINO_THRESHOLD)
-
---
 `_portfolio_max_drawdown_from
---
_results` → return 10
---
.0 (good
---
 DD
---
)

Wait
---
, but
---
 if
---
 sort
---
ino=0.3 and
---
 alpha
---
=+
---
1%, the
---
 candidate passes the alpha gate (
---
alpha >
---
 -2%). Then
---
 in
---
 Tier 1,
---
 sortino ≤
---
 0.5 →
---
 rejected
---
. Tier 2 (DD
---
-only) → DD
---
=10%
---
 ≤ 20% → passes
---
. So weights non
---
-empty, dd_constrained=False
---
 (
---
Tier 2 is not dd
---
_constrained).

But
---
 how
---
 do I verify
---
 "
---
MIN_SORTINO_THRESHOLD still
---
 enforced"? I can
---
 check that
---
 the candidate went
---
 to Tier 2 (not
---
 Tier
---
 1). But
---
 there
---
's no direct flag
---
 for that
---
. The
---
 `
---
dd_constrained`
---
 flag is only for Tier
---
 3. 


---
Hmm, let
---
 me think of
---
 a better
---
 assertion
---
. If
---
 MIN
---
_SORTINO_THRESHOLD were
---
 removed
---
 (
---
reg
---
ression), the candidate would pass
---
 Tier 1 (since
---
 DD
---
=10% ≤
---
 20% and
---
 sortino >
---
 0 would
---
 be the
---
 only check
---
). But with
---
 MIN
---
_SORTINO_THRESHOLD enforced
---
, it goes to Tier 
---
2. The
---
 difference
---
 is not
---
 directly
---
 observable from
---
 the output
---
.

Actually, I can check
---
 the warning
---
 logs
---
. When
---
 Tier 1
---
 fails
---
 and
---
 Tier 2 is
---
 used
---
, there
---
's a WARNING
---
 log:
---
 "Sortino filter
---
 relaxed". I
---
 can capture
---
 this log
---
 and
---
 verify it was
---
 triggered.

Alternatively
---
, I can use
---
 a different scenario
---
: two
---
 candidates, one with sort
---
ino=
---
0.3 and
---
 alpha
---
=+2
---
%, another
---
 with sortino=0.
---
8
---
 and alpha=+1%.
---
 If MIN_SORTINO_THRESHOLD is
---
 enforced, the second
---
 candidate (sortino >
---
 0.5
---
) should be in
---
 Tier 1 and
---
 selected
---
 over the
---
 first (which
---
 has higher
---
 alpha
---
 but sortino ≤
---
 0.5
---
). If MIN_SORTINO_THRESHOLD
---
 were
---
 removed, the first candidate
---
 (higher
---
 alpha) would be selected
---
.

This
---
 is getting complex. Let
---
 me simplify the
---
 test. The
---
 key
---
 point
---
 of
---
 "最低 Sortino 
---
仍强制" is that
---
 the Sortino exemption (
---
1.5) doesn
---
't replace
---
 or
---
 override
---
 the MIN_SORTINO_THRESHOLD (
---
0.5)
---
 in Tier 1. They
---
 are separate checks
---
:
- Alpha
---
 gate: alpha
---
 > -2% OR
---
 sortino > 1
---
.5

---
- Tier
---
 1: DD
---
 ≤ 20% AND
---
 sortino > 0.
---
5

A candidate with sort
---
ino > 1
---
.5 (exempt
---
ed) automatically passes Tier
---
 1's
---
 sortino > 0.
---
5. So the MIN_SORT
---
INO_THRESHOLD is not bypass
---
ed;
---
 it's just
---
 that exempt
---
ed candidates have
---
 sortino > 1
---
.5 >
---
 0.5.


---
I think the most
---
 meaningful test is
---
: a candidate with sortino
---
 between 0.5 and
---
 1.5 (passes
---
 MIN_SORTINO_THRESHOLD but
---
 not exemption) and
---
 alpha <
---
 -2% (
---
fails gate) →
---
 should be rejected (
---
not exempted). This is
---
 the "low Sortino does
---
 not exempt" test.

Actually
---
, I already
---
 have that
---
 as
---
 test #3 (
---
sort
---
ino=0.3).
---
 Let me make
---
 test
---
 #3
---
 use
---
 sortino=0.6
---
 (above
---
 MIN_SORTINO_THRESHOLD but
---
 below exemption) to be
---
 more precise: even
---
 if
---
 you
---
 pass the
---
 MIN
---
_SORTINO_THRESHOLD,
---
 you still need alpha
---
 > -2% unless
---
 sort
---
ino > 1.5
---
.

Let me revise
---
:

---
-
---
 test #
---
3: alpha
---
=-5%,
---
 sortino=0.6
---
 (above MIN_SORTINO_THRESHOLD
---
 0.5 but
---
 below exemption 
---
1.5),
---
 DD=10% → NOT
---
 exempted →
---
 empty weights

And
---
 for "
---
最低 Sortino 
---
仍强制",
---
 I'll
---
 test: alpha
---
=+1% (passes
---
 gate), sortino=0
---
.3 (below MIN_SORT
---
INO_THRESHOLD), DD=10
---
% → Tier 1 rejects
---
, Tier 2 passes
---
. I'll
---
 verify via
---
 the
---
 "
---
Sortino filter
---
 relaxed" warning that
---
 Tier
---
 1 failed
---
 and
---
 Tier 2 was used
---
.

Actually, let
---
 me just
---
 capture
---
 the log
---
 and check
---
. Let
---
 me look
---
 at the existing
---
 test
---
 patterns for
---
 log capture.
---
 In test
---
_alpha_gate.py line
---
 7
---
99, they
---
 use:

---
```python
handler_id
---
 = logger.add(lambda
---
 m
---
: msgs
---
.append(str
---
(m)), level
---
="WARNING
---
")
```

I
---
 can do
---
 the same for
---
 the "Sortino filter relaxed
---
" warning.

OK, let
---
 me finalize
---
 the 
---
7 tests:

1. `
---
test_sortino_exemption_constant
---
_exists` — SORTINO_ALPHA
---
_EXEMPTION = 1
---
.5
2. `
---
test_high_sortino_exem
---
pts_negative_alpha` — alpha
---
=-5%, sortino=
---
2.0, DD=
---
10% → weights
---
 non-empty

---
3. `test_low_sort
---
ino_does_not_exempt` —
---
 alpha=-5%, sortino
---
=0.6,
---
 DD=10% → empty
---
 weights (
---
sortino <
---
 1
---
.5, not exempted
---
)
4. `test_dd
---
_still_mandatory_with_sort
---
ino_exemption` — alpha
---
=-5%, sortino=
---
2.0, DD=
---
25% → passes
---
 gate, DD
---
 filter applies (dd_constrained
---
=True)
5. `test
---
_min_sortino_threshold_still
---
_enforced_in
---
_tier1` — alpha
---
=+1%, sortino
---
=0.3,
---
 DD=10% → passes
---
 gate, Tier 1 rejects
---
 (sortino ≤ 0
---
.5), Tier 2
---
 passes (warning
---
 "
---
Sortino filter relaxed")
6
---
. `test_sortino_ex
---
emption_boundary_rejected` —
---
 alpha=-5%, sortino
---
=1.5 (ex
---
actly at boundary) → rejected
---
 (>strict comparison)
7.
---
 `test_sortino_exemption
---
_just_above_boundary` —
---
 alpha=-5%, sortino
---
=1.51 →
---
 passes


---
Let me write these
---
 now
---
.
---
 I'll append
---
 to
---
 the test
---
_alpha_gate.py file.

Actually
---
, let
---
 me reconsider
---
 test
---
 #5
---
. The sort
---
ino=
---
0.3 is
---
 below MIN_SORTINO_THRESHOLD.
---
 But I
---
 also need to make
---
 sure the candidate passes
---
 the alpha gate. With
---
 alpha=+1% (>
---
 -2%), it
---
 passes.
---
 Then
---
 Tier
---
 1 checks
---
 sortino > 0.
---
5 → 
---
0.3 ≤
---
 0.5 →
---
 fails. Tier 2 checks
---
 DD ≤
---
 20% → 10
---
%
---
 ≤ 20% → passes
---
. So weights non-empty,
---
 and the "Sortino filter
---
 relaxed" warning should
---
 be logged
---
.

But wait, there
---
's a subt
---
lety.
---
 The
---
 `_
---
portfolio
---
_sortino_from_results` is
---
 called in the candidates construction.
---
 If I patch it to
---
 return 0.3,
---
 the
---
 candidate
---
's
---
 sortino in
---
 the candidates
---
 tuple is 0.3
---
. Then
---
:

---
- Alpha
---
 gate: alpha
---
=+1% >
---
 -2% →
---
 passes (no
---
 exemption
---
 needed)
- Tier
---
 1: DD
---
=10% ≤ 20
---
% AND sortino=
---
0.3 > 0
---
.5 → False
---
 (sortino ≤
---
 0.5
---
) → Tier
---
 1 fails

---
- Tier 2: DD
---
=10% ≤
---
 20% → True
---
 → passes
---


So
---
 weights
---
 non-empty, and the "
---
Sortino filter relaxed" warning
---
 is logged. I
---
 can verify this.

But there
---
's another issue: the `_
---
compute_sortino` (
---
not
---
 `_portfolio_sortino_from_results
---
`) is called in the per
---
-strategy best params loop.
---
 This
---
 would
---
 compute
---
 the real sort
---
ino from the returns series.
---
 But
---
 this
---
 only
---
 affects `best_sortino`
---
 stored in `
---
GroupBacktestResult.port
---
folio_sortino`, not the
---
 gate/T
---
ier logic
---
. So it
---
's fine.

Let
---
 me also think about whether
---
 I
---
 need to patch `_compute_sort
---
ino` to
---
 avoid issues
---
. In
---
 the per
---
-strategy best params loop,
---
 `_
---
compute_sortino` is called
---
 to
---
 compute `
---
pso` (best
---
_sortino). This
---
 value
---
 is stored in `
---
GroupBacktestResult.portfolio
---
_sortino`.
---
 It doesn't affect the gate
---
 or
---
 Tier logic
---
. So I
---
 don't need to patch it
---
.

But
---
 wait, there's a subtle
---
 issue:
---
 in the per
---
-strategy best params loop,
---
 the `
---
best_sort
---
ino` is updated
---
 based
---
 on `
---
alpha > best_alpha
---
`. Since
---
 I'm patch
---
ing `_compute
---
_alpha` with
---
 a constant, all
---
 param
---
 combos have the same alpha,
---
 so the first
---
 combo
---
 is always
---
 the "
---
best".
---
 That
---
's fine for single-param
---
 tests
---
.

OK, let me write
---
 the tests now.


---
One
---
 more thing: for
---
 the DD
---
 test (#
---
4), I need to patch
---
 `_portfolio_max_drawdown_from
---
_results`.
---
 But
---
 this
---
 function
---
 is also called in the `
---
GroupBacktestResult` construction
---
 (line 1266
---
). If I patch it with
---
 a constant, the
---
 `GroupBacktestResult.port
---
folio_max_draw
---
down` would
---
 also be that
---
 constant. That
---
's fine.


---
Wait
---
, actually line
---
 1266
---
 is in
---
 the per
---
-strategy best params loop
---
:

---
```python
portfolio
---
_max_drawdown=_
---
portfolio_max_drawdown_from_results
---
(best_results
---
)
```

And
---
 line 134
---
2 is in the
---
 candidates construction:
```python

---
pdd
---
 = _portfolio_max_drawdown
---
_from_results(results)
```


---
Both
---
 would
---
 be patched
---
.
---
 That
---
's fine.

Let me also
---
 check: in
---
 the candidates construction, `
---
results` is the
---
 `
---
best_results` from
---
 the per-strategy loop
---
. So patch
---
ing `_portfolio_max_drawdown
---
_from_results` affects
---
 both places
---
 consistently.

OK, I
---
'm ready
---
 to write the tests. Let
---
 me append
---
 them
---
 to test
---
_alpha_gate.py.

Let
---
 me also update the module doc
---
string of test_alpha_gate.py
---
 to mention Iter #17.
---
现在让我
---
来编写测试。首先
---
，更新
---
模块的
---
 docstring 并
---
添加新的测试类。
---
{"status": "in_progress", "taskId": "4"}
---
Updated task #4 status
---
Updated task #4 status
---
{"file_path": "/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py", "new_string": "\"\"\"迭代 #12：alpha>0 硬门槛测试（Reject Negative-Alpha Strategies）。\n\n迭代 #16 更新：alpha gate 从 alpha>0 放宽至 alpha > ALPHA_GATE_THRESHOLD (-2%)。\n动机：SPX 成分股 vs SPY benchmark 存在结构性近零 alpha，严格 alpha>0 门槛导致\n4/6 组空仓。放宽至 -2% 仍过滤\"灾难性跑输\"，但保留\"小幅跑输 SPY 但 Sortino/DD\n优秀\"的候选。WF OOS 校验仍用 -5% 单轮下限 + avg>0 汇总门槛，不削弱 OOS 验证。\n\n迭代 #17 更新：新增 Sortino 豁免 —— 高 Sortino (> SORTINO_ALPHA_EXEMPTION=1.5)\n的策略绕过 alpha gate。动机：Iter #16 reoptimize 实证 SPX 组 alpha 范围 -3.61% ~\n-15.35%，-2% gate 仍不解锁 SPX 组；但部分策略 Sortino 极佳，只因\"vs SPY 相对收益\"\n不合格被拒。Constitution L1 首要 KPI 是 Sortino，本豁免让\"Sortino 卓越但 alpha 跑输\nSPY\"的策略进入 Tier 1/2/3。WF OOS 校验不变。\n\n验证：\n    1. `GroupBacktestResult.no_positive_alpha` 字段默认 False\n    2. `_run_group` 在 candidates 构建后、Tier 1 剔除 alpha ≤ ALPHA_GATE_THRESHOLD 的候选\n    3. 全负 alpha（< -2%）组返回空权重 + `no_positive_alpha=True` 标记\n    4. 混合 alpha 组只保留 alpha > -2% 的候选\n    5. `_optimize_ensemble_weights` 负 alpha 策略权重为 0（不再 max(0.01) 掩盖）\n    6. 全负 alpha ensemble 退化为等权 + WARNING（防御性 fallback）\n    7. 健全性门槛 + alpha 门槛协同工作\n    8. [Iter #16] ALPHA_GATE_THRESHOLD 常量存在且等于 -2.0\n    9. [Iter #16] alpha=-1% 通过 gate（在 -2% 与 0% 之间）\n    10. [Iter #16] alpha=-5% 仍被拒绝\n    11. [Iter #16] alpha=-2.0% 边界值被拒绝（使用 > 严格比较）\n    12. [Iter #16] alpha=+1% 仍通过（无回归）\n    13. [Iter #16] 集成场景：SPX 组 alpha=-1.5% 策略入选 tier1\n    14. [Iter #16] 单策略 ensemble 负 alpha（> -2%）仍得 weight=1.0（早返回）\n    15. [Iter #17] SORTINO_ALPHA_EXEMPTION 常量存在且等于 1.5\n    16. [Iter #17] 高 Sortino (2.0) 豁免 alpha gate（alpha=-5% 仍通过）\n    17. [Iter #17] 低 Sortino (0.6) 不豁免（仍需 alpha > -2%）\n    18. [Iter #17] DD 仍强制（高 Sortino 豁免后仍经 Tier 1/2/3 DD 过滤）\n    19. [Iter #17] MIN_SORTINO_THRESHOLD 在 Tier 1 仍强制（正 alpha + 低 Sortino → Tier 2）\n    20. [Iter #17] Sortino=1.5 边界值不豁免（> 严格比较）\n    21. [Iter #17] Sortino=1.51 刚过边界豁免通过\n\n背景见 `iterations/iteration_16/spec.md` + `iterations/iteration_17/spec.md` +\n`.codebuddy/notes/experience.md` #8。\n\"\"\"", "old_string": "\"\"\"迭代 #12：alpha>0 硬门槛测试（Reject Negative-Alpha Strategies）。\n\n迭代 #16 更新：alpha gate 从 alpha>0 放宽至 alpha > ALPHA_GATE_THRESHOLD (-2%)。\n动机：SPX 成分股 vs SPY benchmark 存在结构性近零 alpha，严格 alpha>0 门槛导致\n4/6 组空仓。放宽至 -2% 仍过滤\"灾难性跑输\"，但保留\"小幅跑输 SPY 但 Sortino/DD\n优秀\"的候选。WF OOS 校验仍用 -5% 单轮下限 + avg>0 汇总门槛，不削弱 OOS 验证。\n\n验证：\n    1. `GroupBacktestResult.no_positive_alpha` 字段默认 False\n    2. `_run_group` 在 candidates 构建后、Tier 1 剔除 alpha ≤ ALPHA_GATE_THRESHOLD 的候选\n    3. 全负 alpha（< -2%）组返回空权重 + `no_positive_alpha=True` 标记\n    4. 混合 alpha 组只保留 alpha > -2% 的候选\n    5. `_optimize_ensemble_weights` 负 alpha 策略权重为 0（不再 max(0.01) 掩盖）\n    6. 全负 alpha ensemble 退化为等权 + WARNING（防御性 fallback）\n    7. 健全性门槛 + alpha 门槛协同工作\n    8. [Iter #16] ALPHA_GATE_THRESHOLD 常量存在且等于 -2.0\n    9. [Iter #16] alpha=-1% 通过 gate（在 -2% 与 0% 之间）\n    10. [Iter #16] alpha=-5% 仍被拒绝\n    11. [Iter #16] alpha=-2.0% 边界值被拒绝（使用 > 严格比较）\n    12. [Iter #16] alpha=+1% 仍通过（无回归）\n    13. [Iter #16] 集成场景：SPX 组 alpha=-1.5% 策略入选 tier1\n    14. [Iter #16] 单策略 ensemble 负 alpha（> -2%）仍得 weight=1.0（早返回）\n\n背景见 `iterations/iteration_16/spec.md` + `.codebuddy/notes/experience.md` #8。\n\"\"\""}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py
---
现在请
---
更新 import
---
，加入
---
 `
---
SORTINO_ALPHA
---
_EXEMPTION`：
---
{"file_path": "/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py", "new_string": "from mytrader.backtest.matrix_backtest import (\n    ALPHA_GATE_THRESHOLD,\n    SORTINO_ALPHA_EXEMPTION,\n    GroupBacktestResult,\n    MatrixBacktest,\n    MatrixBacktestReport,\n    SingleBacktestResult,\n    _combine_daily_returns,\n    _compute_alpha,\n    _optimize_ensemble_weights,\n)", "old_string": "from mytrader.backtest.matrix_backtest import (\n    ALPHA_GATE_THRESHOLD,\n    GroupBacktestResult,\n    MatrixBacktest,\n    MatrixBacktestReport,\n    SingleBacktestResult,\n    _combine_daily_returns,\n    _compute_alpha,\n    _optimize_ensemble_weights,\n)"}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py
---
Now
---
 let me append
---
 the new
---
 test class
---
 at
---
 the end of the file.
---
 Let me read
---
 the end of the file to
---
 find the exact
---
 location
---
.
---
现在
---
在
---
文件
---
末尾追加
---
新的测试类。
---
{"file_path": "/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py", "limit": 15, "offset": 1245}
---
1245→        # 策略收益序列（alpha 值由 mock 控制，这里只需要非空序列）
1246→        np.random.seed(42)
1247→        returns_a = pd.Series(np.random.normal(0.00035, 0.004, n), index=idx)
1248→
1249→        results_a = [_make_result("S1", "strat_a", returns_a)]
1250→
1251→        # 单策略 ensemble（早返回路径，不计算 alpha）
1252→        weights = _optimize_ensemble_weights(
1253→            [("strat_a", {}, results_a)],
1254→            spy_returns=spy_returns,
1255→        )
1256→
1257→        # 早返回路径 → weight=1.0
1258→        assert len(weights) == 1
1259→        assert weights[0][0] == "strat_a"
1260→
---
1245→        # 策略收益序列（alpha 值由 mock 控制，这里只需要非空序列）
1246→        np.random.seed(42)
1247→        returns_a = pd.Series(np.random.normal(0.00035, 0.004, n), index=idx)
1248→
1249→        results_a = [_make_result("S1", "strat_a", returns_a)]
1250→
1251→        # 单策略 ensemble（早返回路径，不计算 alpha）
1252→        weights = _optimize_ensemble_weights(
1253→            [("strat_a", {}, results_a)],
1254→            spy_returns=spy_returns,
1255→        )
1256→
1257→        # 早返回路径 → weight=1.0
1258→        assert len(weights) == 1
1259→        assert weights[0][0] == "strat_a"
1260→
---
{"file_path": "/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py", "limit": 10, "offset": 1258}
---
1258→        assert len(weights) == 1
1259→        assert weights[0][0] == "strat_a"
1260→        assert weights[0][2] == 1.0, (
1261→            f"单策略 ensemble 应早返回 weight=1.0（不依赖 alpha 值），"
1262→            f"实际 {weights[0][2]}"
1263→        )
1264→
---
1258→        assert len(weights) == 1
1259→        assert weights[0][0] == "strat_a"
1260→        assert weights[0][2] == 1.0, (
1261→            f"单策略 ensemble 应早返回 weight=1.0（不依赖 alpha 值），"
1262→            f"实际 {weights[0][2]}"
1263→        )
1264→
---
{"file_path": "/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py", "new_string": "        assert len(weights) == 1\n        assert weights[0][0] == \"strat_a\"\n        assert weights[0][2] == 1.0, (\n            f\"单策略 ensemble 应早返回 weight=1.0（不依赖 alpha 值），\"\n            f\"实际 {weights[0][2]}\"\n        )\n\n\n# ---------------------------------------------------------------------------\n# Iter #17: Sortino alpha exemption (SORTINO_ALPHA_EXEMPTION = 1.5)\n# ---------------------------------------------------------------------------\n\nclass TestSortinoAlphaExemption:\n    \"\"\"迭代 #17：Sortino 豁免 —— 高 Sortino (> 1.5) 的策略绕过 alpha gate。\n\n    动机见 spec：Iter #16 reoptimize 实证 SPX 组 alpha 范围 -3.61% ~ -15.35%，\n    -2% gate 仍不解锁 SPX 组；但部分策略 Sortino 极佳（下行风险控制优秀），\n    只因\"vs SPY 相对收益\"不合格被拒。Constitution L1 首要 KPI 是 Sortino，\n    本豁免让\"Sortino 卓越但 alpha 跑输 SPY\"的策略进入 Tier 1/2/3。\n\n    合格定义：alpha > ALPHA_GATE_THRESHOLD (-2%)  OR  sortino > SORTINO_ALPHA_EXEMPTION (1.5)\n    \"\"\"\n\n    def test_sortino_exemption_constant_exists(self):\n        \"\"\"SORTINO_ALPHA_EXEMPTION 常量存在且等于 1.5。\"\"\"\n        assert hasattr(\n            __import__(\"mytrader.backtest.matrix_backtest\", fromlist=[\"matrix_backtest\"]),\n            \"SORTINO_ALPHA_EXEMPTION\",\n        ), \"matrix_backtest 必须导出 SORTINO_ALPHA_EXEMPTION 常量\"\n        assert SORTINO_ALPHA_EXEMPTION == 1.5, (\n            f\"SORTINO_ALPHA_EXEMPTION 应为 1.5，实际 {SORTINO_ALPHA_EXEMPTION}\"\n        )\n\n    def test_high_sortino_exempts_negative_alpha(self):\n        \"\"\"高 Sortino (2.0) 豁免 alpha gate：alpha=-5% 仍通过。\n\n        场景：单策略 alpha=-5%（远低于 -2% gate），sortino=2.0（高于 1.5 豁免），\n              DD=10%（合规），健全性通过。\n        验证：权重正常产出（非空），no_positive_alpha=False。\n        旧逻辑（无豁免）：alpha=-5% 被拒绝 → 空权重。\n        \"\"\"\n        n = 300\n        idx = pd.date_range(\"2021-01-01\", periods=n, freq=\"B\")\n        spy_df = _make_spy_df(n, annual_return=0.10)\n\n        np.random.seed(42)\n        returns_a = pd.Series(np.random.normal(0.0004, 0.004, n), index=idx)\n\n        mock_alpha = -5.0  # 远低于 -2% gate\n        mock_sortino = 2.0  # 高于 1.5 豁免\n        assert mock_alpha < ALPHA_GATE_THRESHOLD\n        assert mock_sortino > SORTINO_ALPHA_EXEMPTION\n\n        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):\n            results = []\n            for sym, df in data.items():\n                if df is None or df.empty or len(df) < 30:\n                    continue\n                results.append(_make_result(sym, strategy_name, returns_a, closed_trades=10))\n            return results\n\n        df_up = _make_ohlcv(n, trend=\"up\")\n        store = _make_store_with_spy({\"AAA\": df_up, \"BBB\": df_up}, spy_df)\n        universe = _make_mock_universe({\"test_group\": [\"AAA\", \"BBB\"]})\n\n        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)\n        report = MatrixBacktestReport(\n            generated_at=pd.Timestamp.now(tz=\"UTC\").isoformat(),\n            backtest_window=\"2021-01-01 ~ 2022-01-01\",\n            groups={},\n        )\n\n        with patch(\n            \"mytrader.backtest.matrix_backtest._backtest_batch\",\n            side_effect=mock_backtest_batch,\n        ), patch(\n            \"mytrader.backtest.matrix_backtest._compute_alpha\",\n            return_value=mock_alpha,\n        ), patch(\n            \"mytrader.backtest.matrix_backtest._portfolio_sortino_from_results\",\n            return_value=mock_sortino,\n        ):\n            weights = mb._run_group(\n                group_id=\"test_group\",\n                symbols=[\"AAA\", \"BBB\"],\n                start=date(2021, 1, 1),\n                end=date(2022, 1, 1),\n                strategies=[\"dual_ma\"],\n                param_grids={\"dual_ma\": {\"fast\": [5], \"slow\": [20]}},\n                report=report,\n            )\n\n        # 关键断言：高 Sortino 豁免 alpha gate → 权重非空\n        assert len(weights) > 0, (\n            f\"alpha={mock_alpha}% 但 sortino={mock_sortino} > {SORTINO_ALPHA_EXEMPTION} \"\n            f\"应通过 Sortino 豁免，实际 weights={weights}\"\n        )\n        # no_positive_alpha 不应被标记\n        for gr in report.group_results:\n            if gr.group_id == \"test_group\":\n                assert gr.no_positive_alpha is False, (\n                    \"高 Sortino 豁免组不应标记 no_positive_alpha=True\"\n                )\n        warning_text = \" \".join(report.warnings)\n        assert \"no_positive_alpha\" not in warning_text, (\n            f\"高 Sortino 豁免组不应有 no_positive_alpha 警告，warnings={report.warnings}\"\n        )\n\n    def test_low_sortino_does_not_exempt(self):\n        \"\"\"低 Sortino (0.6) 不豁免：alpha=-5% 仍被拒绝。\n\n        场景：单策略 alpha=-5%（低于 -2% gate），sortino=0.6（高于 MIN_SORTINO_THRESHOLD 0.5\n              但低于豁免 1.5），DD=10%，健全性通过。\n        验证：返回空权重，no_positive_alpha=True。\n        说明：sortino=0.6 通过 Tier 1 的 MIN_SORTINO_THRESHOLD 但不构成豁免，\n              证明\"过 Tier 1 Sortino 门槛\"≠\"豁免 alpha gate\"。\n        \"\"\"\n        n = 300\n        idx = pd.date_range(\"2021-01-01\", periods=n, freq=\"B\")\n        spy_df = _make_spy_df(n, annual_return=0.10)\n\n        np.random.seed(42)\n        returns_a = pd.Series(np.random.normal(0.0004, 0.004, n), index=idx)\n\n        mock_alpha = -5.0\n        mock_sortino = 0.6  # 高于 MIN_SORTINO_THRESHOLD(0.5) 但低于豁免(1.5)\n        assert mock_alpha < ALPHA_GATE_THRESHOLD\n        assert MIN_SORTINO_THRESHOLD < mock_sortino <= SORTINO_ALPHA_EXEMPTION\n\n        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):\n            results = []\n            for sym, df in data.items():\n                if df is None or df.empty or len(df) < 30:\n                    continue\n                results.append(_make_result(sym, strategy_name, returns_a, closed_trades=10))\n            return results\n\n        df_up = _make_ohlcv(n, trend=\"up\")\n        store = _make_store_with_spy({\"AAA\": df_up, \"BBB\": df_up}, spy_df)\n        universe = _make_mock_universe({\"test_group\": [\"AAA\", \"BBB\"]})\n\n        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)\n        report = MatrixBacktestReport(\n            generated_at=pd.Timestamp.now(tz=\"UTC\").isoformat(),\n            backtest_window=\"2021-01-01 ~ 2022-01-01\",\n            groups={},\n        )\n\n        with patch(\n            \"mytrader.backtest.matrix_backtest._backtest_batch\",\n            side_effect=mock_backtest_batch,\n        ), patch(\n            \"mytrader.backtest.matrix_backtest._compute_alpha\",\n            return_value=mock_alpha,\n        ), patch(\n            \"mytrader.backtest.matrix_backtest._portfolio_sortino_from_results\",\n            return_value=mock_sortino,\n        ):\n            weights = mb._run_group(\n                group_id=\"test_group\",\n                symbols=[\"AAA\", \"BBB\"],\n                start=date(2021, 1, 1),\n                end=date(2022, 1, 1),\n                strategies=[\"dual_ma\"],\n                param_grids={\"dual_ma\": {\"fast\": [5], \"slow\": [20]}},\n                report=report,\n            )\n\n        # 关键断言：低 Sortino 不豁免 → 空权重\n        assert weights == [], (\n            f\"alpha={mock_alpha}% 且 sortino={mock_sortino} ≤ {SORTINO_ALPHA_EXEMPTION} \"\n            f\"不应豁免，实际 weights={weights}\"\n        )\n        warning_text = \" \".join(report.warnings)\n        assert \"no_positive_alpha\" in warning_text\n        for gr in report.group_results:\n            if gr.group_id == \"test_group\":\n                assert gr.no_positive_alpha is True\n\n    def test_dd_still_mandatory_with_sortino_exemption(self):\n        \"\"\"DD 仍强制：高 Sortino 豁免 alpha gate 后，仍经 Tier 1/2/3 DD 过滤。\n\n        场景：单策略 alpha=-5%（gate 拒绝），sortino=2.0（豁免通过），\n              DD=25%（超 20% 硬约束），健全性通过。\n        验证：通过 alpha gate（豁免），但 Tier 1 DD 拒绝、Tier 2 DD 拒绝、\n              Tier 3 fallback 选中并标记 dd_constrained=True。\n        说明：证明 Sortino 豁免只绕过 alpha gate，不绕过 DD 过滤。\n        \"\"\"\n        n = 300\n        idx = pd.date_range(\"2021-01-01\", periods=n, freq=\"B\")\n        spy_df = _make_spy_df(n, annual_return=0.10)\n\n        np.random.seed(42)\n        returns_a = pd.Series(np.random.normal(0.0004, 0.004, n), index=idx)\n\n        mock_alpha = -5.0\n        mock_sortino = 2.0  # 豁免\n        mock_dd = 25.0  # 超 20% 硬约束\n        assert mock_alpha < ALPHA_GATE_THRESHOLD\n        assert mock_sortino > SORTINO_ALPHA_EXEMPTION\n        assert mock_dd > 20.0\n\n        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):\n            results = []\n            for sym, df in data.items():\n                if df is None or df.empty or len(df) < 30:\n                    continue\n                results.append(_make_result(sym, strategy_name, returns_a, closed_trades=10))\n            return results\n\n        df_up = _make_ohlcv(n, trend=\"up\")\n        store = _make_store_with_spy({\"AAA\": df_up, \"BBB\": df_up}, spy_df)\n        universe = _make_mock_universe({\"test_group\": [\"AAA\", \"BBB\"]})\n\n        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)\n        report = MatrixBacktestReport(\n            generated_at=pd.Timestamp.now(tz=\"UTC\").isoformat(),\n            backtest_window=\"2021-01-01 ~ 2022-01-01\",\n            groups={},\n        )\n\n        with patch(\n            \"mytrader.backtest.matrix_backtest._backtest_batch\",\n            side_effect=mock_backtest_batch,\n        ), patch(\n            \"mytrader.backtest.matrix_backtest._compute_alpha\",\n            return_value=mock_alpha,\n        ), patch(\n            \"mytrader.backtest.matrix_backtest._portfolio_sortino_from_results\",\n            return_value=mock_sortino,\n        ), patch(\n            \"mytrader.backtest.matrix_backtest._portfolio_max_drawdown_from_results\",\n            return_value=mock_dd,\n        ):\n            weights = mb._run_group(\n                group_id=\"test_group\",\n                symbols=[\"AAA\", \"BBB\"],\n                start=date(2021, 1, 1),\n                end=date(2022, 1, 1),\n                strategies=[\"dual_ma\"],\n                param_grids={\"dual_ma\": {\"fast\": [5], \"slow\": [20]}},\n                report=report,\n            )\n\n        # 通过 alpha gate（豁免），但 DD 过滤仍生效 → Tier 3 fallback\n        assert len(weights) > 0, (\n            f\"高 Sortino 豁免应通过 alpha gate；DD=25% 触发 Tier 3 fallback \"\n            f\"仍应产出权重（dd_constrained），实际 weights={weights}\"\n        )\n        # dd_constrained=True（DD 过滤触发 Tier 3 fallback）\n        assert weights[0][\"dd_constrained\"] is True, (\n            f\"DD=25% > 20% 应触发 Tier 3 fallback，dd_constrained=True，\"\n            f\"实际 dd_constrained={weights[0]['dd_constrained']}\"\n        )\n        assert weights[0][\"backtest_dd_status\"] == \"dd_constrained\"\n        # no_positive_alpha 不应被标记（Sortino 豁免通过了 alpha gate）\n        warning_text = \" \".join(report.warnings)\n        assert \"no_positive_alpha\" not in warning_text, (\n            f\"高 Sortino 豁免通过 alpha gate，不应触发 no_positive_alpha，\"\n            f\"warnings={report.warnings}\"\n        )\n        # dd_constrained 警告应存在\n        assert \"dd_constrained\" in warning_text\n\n    def test_min_sortino_threshold_still_enforced_in_tier1(self):\n        \"\"\"MIN_SORTINO_THRESHOLD 在 Tier 1 仍强制（正 alpha + 低 Sortino → Tier 2）。\n\n        场景：单策略 alpha=+1%（正 alpha，过 gate 无需豁免），sortino=0.3\n              （低于 MIN_SORTINO_THRESHOLD 0.5），DD=10%（合规）。\n        验证：过 alpha gate，但 Tier 1 拒绝（sortino ≤ 0.5）→ Tier 2 (DD-only) 通过；\n              权重非空，且日志含 \"Sortino filter relaxed\" 警告。\n        说明：证明 Iter #17 的 Sortino 豁免（1.5）不破坏 Iter #9 的 Tier 1\n              MIN_SORTINO_THRESHOLD 过滤——二者是不同层级的检查。\n        \"\"\"\n        from loguru import logger\n\n        n = 300\n        idx = pd.date_range(\"2021-01-01\", periods=n, freq=\"B\")\n        spy_df = _make_spy_df(n, annual_return=0.10)\n\n        np.random.seed(42)\n        returns_a = pd.Series(np.random.normal(0.0004, 0.004, n), index=idx)\n\n        mock_alpha = 1.0  # 正 alpha，过 gate\n        mock_sortino = 0.3  # 低于 MIN_SORTINO_THRESHOLD 0.5\n        assert mock_alpha > ALPHA_GATE_THRESHOLD\n        assert mock_sortino <= MIN_SORTINO_THRESHOLD\n\n        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):\n            results = []\n            for sym, df in data.items():\n                if df is None or df.empty or len(df) < 30:\n                    continue\n                results.append(_make_result(sym, strategy_name, returns_a, closed_trades=10))\n            return results\n\n        df_up = _make_ohlcv(n, trend=\"up\")\n        store = _make_store_with_spy({\"AAA\": df_up, \"BBB\": df_up}, spy_df)\n        universe = _make_mock_universe({\"test_group\": [\"AAA\", \"BBB\"]})\n\n        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)\n        report = MatrixBacktestReport(\n            generated_at=pd.Timestamp.now(tz=\"UTC\").isoformat(),\n            backtest_window=\"2021-01-01 ~ 2022-01-01\",\n            groups={},\n        )\n\n        msgs: list[str] = []\n        handler_id = logger.add(lambda m: msgs.append(str(m)), level=\"WARNING\")\n\n        try:\n            with patch(\n                \"mytrader.backtest.matrix_backtest._backtest_batch\",\n                side_effect=mock_backtest_batch,\n            ), patch(\n                \"mytrader.backtest.matrix_backtest._compute_alpha\",\n                return_value=mock_alpha,\n            ), patch(\n                \"mytrader.backtest.matrix_backtest._portfolio_sortino_from_results\",\n                return_value=mock_sortino,\n            ):\n                weights = mb._run_group(\n                    group_id=\"test_group\",\n                    symbols=[\"AAA\", \"BBB\"],\n                    start=date(2021, 1, 1),\n                    end=date(2022, 1, 1),\n                    strategies=[\"dual_ma\"],\n                    param_grids={\"dual_ma\": {\"fast\": [5], \"slow\": [20]}},\n                    report=report,\n                )\n        finally:\n            logger.remove(handler_id)\n\n        # 权重非空（Tier 2 DD-only fallback 选中）\n        assert len(weights) > 0, (\n            f\"正 alpha 过 gate；Tier 1 拒绝（sortino ≤ {MIN_SORTINO_THRESHOLD}）→ \"\n            f\"Tier 2 (DD-only) 应选中，实际 weights={weights}\"\n        )\n        # Tier 1 失败 → Tier 2 触发 \"Sortino filter relaxed\" 警告\n        assert any(\"Sortino filter relaxed\" in m for m in msgs), (\n            f\"sortino={mock_sortino} ≤ {MIN_SORTINO_THRESHOLD} 应触发 Tier 1 失败 + \"\n            f\"Tier 2 'Sortino filter relaxed' 警告，实际捕获: {msgs}\"\n        )\n        # Tier 2 不是 dd_constrained（DD 合规）\n        assert weights[0][\"dd_constrained\"] is False\n        # no_positive_alpha 不触发（正 alpha）\n        warning_text = \" \".join(report.warnings)\n        assert \"no_positive_alpha\" not in warning_text\n\n    def test_sortino_exemption_boundary_rejected(self):\n        \"\"\"Sortino=1.5 恰好在豁免边界 → 不豁免（> 严格比较）。\n\n        场景：alpha=-5%（gate 拒绝），sortino=1.5（恰好等于豁免阈值）。\n        验证：返回空权重（因为 `c[3] > SORTINO_ALPHA_EXEMPTION` 是严格大于）。\n        \"\"\"\n        n = 300\n        idx = pd.date_range(\"2021-01-01\", periods=n, freq=\"B\")\n        spy_df = _make_spy_df(n, annual_return=0.10)\n\n        np.random.seed(42)\n        returns_a = pd.Series(np.random.normal(0.0004, 0.004, n), index=idx)\n\n        mock_alpha = -5.0\n        mock_sortino = SORTINO_ALPHA_EXEMPTION  # 1.5 边界\n\n        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):\n            results = []\n            for sym, df in data.items():\n                if df is None or df.empty or len(df) < 30:\n                    continue\n                results.append(_make_result(sym, strategy_name, returns_a, closed_trades=10))\n            return results\n\n        df_up = _make_ohlcv(n, trend=\"up\")\n        store = _make_store_with_spy({\"AAA\": df_up, \"BBB\": df_up}, spy_df)\n        universe = _make_mock_universe({\"test_group\": [\"AAA\", \"BBB\"]})\n\n        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)\n        report = MatrixBacktestReport(\n            generated_at=pd.Timestamp.now(tz=\"UTC\").isoformat(),\n            backtest_window=\"2021-01-01 ~ 2022-01-01\",\n            groups={},\n        )\n\n        with patch(\n            \"mytrader.backtest.matrix_backtest._backtest_batch\",\n            side_effect=mock_backtest_batch,\n        ), patch(\n            \"mytrader.backtest.matrix_backtest._compute_alpha\",\n            return_value=mock_alpha,\n        ), patch(\n            \"mytrader.backtest.matrix_backtest._portfolio_sortino_from_results\",\n            return_value=mock_sortino,\n        ):\n            weights = mb._run_group(\n                group_id=\"test_group\",\n                symbols=[\"AAA\", \"BBB\"],\n                start=date(2021, 1, 1),\n                end=date(2022, 1, 1),\n                strategies=[\"dual_ma\"],\n                param_grids={\"dual_ma\": {\"fast\": [5], \"slow\": [20]}},\n                report=report,\n            )\n\n        # 关键断言：sortino == 豁免阈值 → 不豁免（> 严格比较）\n        assert weights == [], (\n            f\"sortino == {SORTINO_ALPHA_EXEMPTION} 应不豁免（使用 > 严格比较），\"\n            f\"实际 weights={weights}\"\n        )\n        warning_text = \" \".join(report.warnings)\n        assert \"no_positive_alpha\" in warning_text\n\n    def test_sortino_exemption_just_above_boundary(self):\n        \"\"\"Sortino=1.51 刚过豁免边界 → 豁免通过。\n\n        场景：alpha=-5%（gate 拒绝），sortino=1.51（刚高于豁免阈值 1.5）。\n        验证：权重非空（豁免通过）。\n        \"\"\"\n        n = 300\n        idx = pd.date_range(\"2021-01-01\", periods=n, freq=\"B\")\n        spy_df = _make_spy_df(n, annual_return=0.10)\n\n        np.random.seed(42)\n        returns_a = pd.Series(np.random.normal(0.0004, 0.004, n), index=idx)\n\n        mock_alpha = -5.0\n        mock_sortino = 1.51  # 刚高于 1.5\n        assert mock_sortino > SORTINO_ALPHA_EXEMPTION\n\n        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):\n            results = []\n            for sym, df in data.items():\n                if df is None or df.empty or len(df) < 30:\n                    continue\n                results.append(_make_result(sym, strategy_name, returns_a, closed_trades=10))\n            return results\n\n        df_up = _make_ohlcv(n, trend=\"up\")\n        store = _make_store_with_spy({\"AAA\": df_up, \"BBB\": df_up}, spy_df)\n        universe = _make_mock_universe({\"test_group\": [\"AAA\", \"BBB\"]})\n\n        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)\n        report = MatrixBacktestReport(\n            generated_at=pd.Timestamp.now(tz=\"UTC\").isoformat(),\n            backtest_window=\"2021-01-01 ~ 2022-01-01\",\n            groups={},\n        )\n\n        with patch(\n            \"mytrader.backtest.matrix_backtest._backtest_batch\",\n            side_effect=mock_backtest_batch,\n        ), patch(\n            \"mytrader.backtest.matrix_backtest._compute_alpha\",\n            return_value=mock_alpha,\n        ), patch(\n            \"mytrader.backtest.matrix_backtest._portfolio_sortino_from_results\",\n            return_value=mock_sortino,\n        ):\n            weights = mb._run_group(\n                group_id=\"test_group\",\n                symbols=[\"AAA\", \"BBB\"],\n                start=date(2021, 1, 1),\n                end=date(2022, 1, 1),\n                strategies=[\"dual_ma\"],\n                param_grids={\"dual_ma\": {\"fast\": [5], \"slow\": [20]}},\n                report=report,\n            )\n\n        # 关键断言：sortino=1.51 > 1.5 → 豁免通过\n        assert len(weights) > 0, (\n            f\"sortino={mock_sortino} > {SORTINO_ALPHA_EXEMPTION} 应豁免通过，\"\n            f\"实际 weights={weights}\"\n        )\n        for gr in report.group_results:\n            if gr.group_id == \"test_group\":\n                assert gr.no_positive_alpha is False", "old_string": "        assert len(weights) == 1\n        assert weights[0][0] == \"strat_a\"\n        assert weights[0][2] == 1.0, (\n            f\"单策略 ensemble 应早返回 weight=1.0（不依赖 alpha 值），\"\n            f\"实际 {weights[0][2]}\"\n        )"}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py
---
I
---
 need to import
---
 `
---
MIN_SORTINO_THRESHOLD
---
` in the test file
---
 since
---
 I use
---
 it in test
---
 #
---
5
---
. Let me check the
---
 current imports.
---
我
---
需要将
---
 `MIN_SORTINO_THRESHOLD`
---
 添加到 imports
---
 中，
---
因为我在测试
---
 #
---
5 中用
---
到了它
---
。
---
{"file_path": "/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py", "new_string": "from mytrader.backtest.matrix_backtest import (\n    ALPHA_GATE_THRESHOLD,\n    MIN_SORTINO_THRESHOLD,\n    SORTINO_ALPHA_EXEMPTION,\n    GroupBacktestResult,\n    MatrixBacktest,\n    MatrixBacktestReport,\n    SingleBacktestResult,\n    _combine_daily_returns,\n    _compute_alpha,\n    _optimize_ensemble_weights,\n)", "old_string": "from mytrader.backtest.matrix_backtest import (\n    ALPHA_GATE_THRESHOLD,\n    SORTINO_ALPHA_EXEMPTION,\n    GroupBacktestResult,\n    MatrixBacktest,\n    MatrixBacktestReport,\n    SingleBacktestResult,\n    _combine_daily_returns,\n    _compute_alpha,\n    _optimize_ensemble_weights,\n)"}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py
---
{"status": "completed", "taskId": "4"}
---
Updated task #4 status
---
Updated task #4 status
---
现在让我先
---
运行一下
---
新
---
测试，以验证
---
它们是否
---
通过。
---
{"status": "in_progress", "taskId": "5"}
---
Updated task #5 status
---
Updated task #5 status
---
{"command": "PYTHONPATH=/Users/rickouyang/Github/trade-tools/mytrader NUMBA_DISABLE_CACHE=1 /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_alpha_gate.py::TestSortinoAlphaExemption -v 2>&1 | tail -40", "dangerouslyDisableSandbox": true, "description": "Run new Sortino exemption tests"}
---
Run new Sortino exemption tests
---
Command: PYTHONPATH=/Users/rickouyang/Github/trade-tools/mytrader NUMBA_DISABLE_CACHE=1 /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_alpha_gate.py::TestSortinoAlphaExemption -v 2>&1 | tail -40
Stdout: ============================= test session starts ==============================
platform darwin -- Python 3.12.13, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/rickouyang/Github/trade-tools/mytrader
configfile: pyproject.toml
plugins: cov-7.1.0, anyio-4.13.0
collected 7 items

tests/test_alpha_gate.py .......                                         [100%]

============================== 7 passed in 2.12s ===============================

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
7 个新
---
测试已
---
全部通过。现在
---
让我
---
运行完整的
---
测试套
---
件，
---
以确保没有引入
---
回归问题
---
。
---
{"command": "PYTHONPATH=/Users/rickouyang/Github/trade-tools/mytrader NUMBA_DISABLE_CACHE=1 /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest --ignore=tests/live -q 2>&1 | tail -30", "dangerouslyDisableSandbox": true, "description": "Run full test suite excluding live", "timeout": 300000}
---
Run full test suite excluding live
---
Command: PYTHONPATH=/Users/rickouyang/Github/trade-tools/mytrader NUMBA_DISABLE_CACHE=1 /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest --ignore=tests/live -q 2>&1 | tail -30
Stdout: tests/test_portfolio.py::TestPersistence::test_save_and_load_snapshot
  /Users/rickouyang/Github/trade-tools/mytrader/mytrader/portfolio/persistence.py:116: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    snapshot_at = datetime.utcnow()

tests/test_portfolio.py::TestPersistence::test_filter_by_symbol
tests/test_portfolio.py::TestPersistence::test_filter_by_symbol
tests/test_portfolio.py::TestPersistence::test_filter_by_symbol
  /Users/rickouyang/Github/trade-tools/mytrader/tests/test_portfolio.py:281: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    filled_at=datetime.utcnow(),

tests/test_portfolio.py::TestPersistenceAdvanced::test_connection_failure_graceful
  /Users/rickouyang/Github/trade-tools/mytrader/tests/test_portfolio.py:478: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    filled_at=datetime.utcnow(),

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
=========================== short test summary info ============================
FAILED tests/test_alpha_gate.py::TestAlphaGateRelaxedThreshold::test_alpha_gate_very_negative_fails
FAILED tests/test_alpha_gate.py::TestAlphaGateRelaxedThreshold::test_alpha_gate_threshold_boundary

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
There
---
 are 2 failures
---
 in
---
 the existing tests
---
. Let me look
---
 at these
---
 tests
---
:

1. `test_alpha
---
_gate_
---
very_negative
---
_f
---
ails` —
---
 alpha=-
---
5% should
---
 be
---
 rejected

---
2. `test_alpha_gate
---
_threshold_boundary
---
` — alpha=-2.
---
0%
---
 (
---
boundary) should be rejected


---
The
---
 issue is that these
---
 tests patch
---
 `_
---
compute_alpha` with
---
 a
---
 fixed
---
 value, but they
---
 DON
---
'T patch `_portfolio
---
_sortino_from
---
_results`. So
---
 the real Sort
---
ino is computed from the returns
---
 series
---
. With the Iter
---
 #
---
17 change
---
, if
---
 the real
---
 Sortino >
---
 1.5, the
---
 candidate would
---
 be exempted even
---
 with
---
 alpha=-5%.

Let me
---
 check the returns
---
 used
---
 in these
---
 tests:
```python
np
---
.random.seed
---
(42)
returns_a
---
 = pd
---
.Series(np.random.normal(0
---
.0004, 0
---
.00
---
4, n
---
), index=idx)
``
---
`

This is
---
 a normal
---
 distribution
---
 with mean=
---
0.0004 and
---
 std=0.00
---
4. The Sortino of
---
 this series
---
 might
---
 be > 1.5
---
 because
---
 the mean is positive
---
 and the downside
---
 deviation
---
 is small.

Let me check
---
:
---
 `_
---
portfolio_sortino_from_results
---
` computes
---
 the Sort
---
ino from
---
 the combined daily
---
 returns. With
---
 
---
2 symbols
---
 both
---
 having the same returns, the
---
 combined is the same series
---
. The Sortino would be
---
:
- mean =
---
 0.0004

---
- downside
---
 deviation = sqrt(mean
---
(min
---
(0,
---
 r)^2))
---
 where r ~
---
 N
---
(0.
---
0004, 0.
---
004)
- About
---
 half the
---
 returns are negative
---
 (since mean
---
 is close
---
 to 0),
---
 so downside
---
 deviation 
---
≈ 0.00
---
4 * sqrt(0.
---
5) ≈ 0
---
.00283
---

- Sortino = 
---
0.0004 /
---
 0.002
---
83 * sqrt
---
(25
---
2) 
---
≈ 0.141
---
4
---
 * 15
---
.87
---
 ≈ 2.24
---


So the Sortino is
---
 about 2.24,
---
 which is > 1.
---
5. That
---
's why the candidate
---
 is being
---
 exempted even with alpha=-
---
5%.

I
---
 need to fix these
---
 existing tests. The options
---
 are:
1. Patch
---
 `_portfolio
---
_sortino_from_results` to
---
 return a low Sort
---
ino (e
---
.g., 0.0
---
 or
---
 0.3
---
) in these
---
 tests,
---
 so the
---
 exemption
---
 doesn't apply
2.
---
 Use returns
---
 that
---
 produce
---
 a Sort
---
ino < 1.5
---


Option
---
 1 is cleaner
---
 and consistent with the Iter
---
 #17 testing
---
 pattern
---
. Let me patch `_portfolio
---
_sortino_from_results` in
---
 these two
---
 tests to
---
 return a low Sort
---
ino,
---
 making
---
 clear
---
 that the Sort
---
ino
---
 exemption
---
 doesn't apply.


---
But
---
 wait, I
---
 need
---
 to be careful. The spec
---
 says
---
 "
---
不改
---
策略
---
/ind
---
icators/r
---
isk/execution
---
/main.py
---
" — but modifying
---
 tests
---
 is allowed
---
 (
---
the user
---
 asked
---
 me to write
---
 ~
---
7 new tests,
---
 and fixing
---
 existing tests that
---
 break
---
 due to the new
---
 logic is part of the implementation
---
).

Let me look
---
 at these
---
 two
---
 failing
---
 tests and add
---
 the
---
 patch
---
.


---
Actually, let
---
 me think about
---
 this more carefully. The existing
---
 tests `
---
test_alpha_gate_very_negative
---
_fails` and `test
---
_alpha_gate_threshold_boundary` are
---
 testing the
---
 alpha gate behavior.
---
 With the Iter
---
 #17 Sort
---
ino exemption
---
, the alpha
---
 gate is
---
 now `alpha >
---
 -
---
2
---
% OR sort
---
ino > 1.5
---
`. These
---
 tests use
---
 alpha=-5% and
---
 alpha=-2.0%
---
 respectively, which
---
 should be
---
 rejected by the alpha
---
 gate. But if
---
 the Sortino is > 
---
1.5, the candidate
---
 is exempted.

The fix
---
 is to ensure
---
 these
---
 tests'
---
 Sortino is below
---
 1.5 so
---
 the exemption doesn't apply.
---
 The
---
 cleanest way is
---
 to patch `_portfolio_sortino
---
_from_results` to return
---
 a value
---
 below 
---
1.5 (e.g
---
., 0.0 or
---
 0.3).


---
Let me update
---
 these
---
 two tests to
---
 add
---
 the patch.
---
 This is a
---
 legitimate
---
 change
---
 because the Iter
---
 #17 logic
---
 change
---
 requires
---
 the Sort
---
ino
---
 to be controlled
---
 in
---
 alpha
---
-g
---
ate-only
---
 tests.

Let
---
 me read
---
 the two
---
 failing tests more
---
 carefully and
---
 add the patch.
---
有两个
---
现有的
---
测试失败了
---
，因为
---
测试
---
中的
---
随机
---
收益率
---
序列产生的
---
 Sortino > 1.
---
5，触
---
发了新的豁
---
免规则
---
。我需要在这些
---
 alpha
---
-gate 
---
测试中 patch
---
 `_portfolio_sortino_from
---
_results` 以控制
---
 Sortino（
---
低于
---
豁
---
免阈值），
---
从而使
---
它们能
---
正确
---
测试
---
 alpha gate
---
。让我
---
来修复它们
---
。
---
{"file_path": "/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py", "limit": 30, "offset": 960}
---
 960→
 961→        # 关键断言：alpha=-1% 应通过 gate（旧 gate 会拒绝）
 962→        assert len(weights) > 0, (
 963→            f"alpha=-1% 应通过 Iter #16 放宽后的 gate，实际 weights={weights}"
 964→        )
 965→        # no_positive_alpha 不应被标记
 966→        for gr in report.group_results:
 967→            if gr.group_id == "test_group":
 968→                assert gr.no_positive_alpha is False, (
 969→                    "alpha=-1% 组不应标记 no_positive_alpha=True（Iter #16 放宽后）"
 970→                )
 971→        warning_text = " ".join(report.warnings)
 972→        assert "no_positive_alpha" not in warning_text, (
 973→            f"alpha=-1% 组不应有 no_positive_alpha 警告，warnings={report.warnings}"
 974→        )
 975→
 976→    def test_alpha_gate_very_negative_fails(self):
 977→        """alpha=-5% 仍被拒绝（远低于 -2% 阈值）。
 978→
 979→        场景：单策略 alpha=-5%，健全性通过。
 980→        验证：返回空权重，no_positive_alpha=True。
 981→        """
 982→        n = 300
 983→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
 984→        spy_df = _make_spy_df(n, annual_return=0.10)
 985→
 986→        np.random.seed(42)
 987→        returns_a = pd.Series(np.random.normal(0.0004, 0.004, n), index=idx)
 988→
 989→        # mock alpha = -5.0%（远低于 -2% 阈值）
 990→
---
 960→
 961→        # 关键断言：alpha=-1% 应通过 gate（旧 gate 会拒绝）
 962→        assert len(weights) > 0, (
 963→            f"alpha=-1% 应通过 Iter #16 放宽后的 gate，实际 weights={weights}"
 964→        )
 965→        # no_positive_alpha 不应被标记
 966→        for gr in report.group_results:
 967→            if gr.group_id == "test_group":
 968→                assert gr.no_positive_alpha is False, (
 969→                    "alpha=-1% 组不应标记 no_positive_alpha=True（Iter #16 放宽后）"
 970→                )
 971→        warning_text = " ".join(report.warnings)
 972→        assert "no_positive_alpha" not in warning_text, (
 973→            f"alpha=-1% 组不应有 no_positive_alpha 警告，warnings={report.warnings}"
 974→        )
 975→
 976→    def test_alpha_gate_very_negative_fails(self):
 977→        """alpha=-5% 仍被拒绝（远低于 -2% 阈值）。
 978→
 979→        场景：单策略 alpha=-5%，健全性通过。
 980→        验证：返回空权重，no_positive_alpha=True。
 981→        """
 982→        n = 300
 983→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
 984→        spy_df = _make_spy_df(n, annual_return=0.10)
 985→
 986→        np.random.seed(42)
 987→        returns_a = pd.Series(np.random.normal(0.0004, 0.004, n), index=idx)
 988→
 989→        # mock alpha = -5.0%（远低于 -2% 阈值）
 990→
---
{"file_path": "/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py", "limit": 70, "offset": 976}
---
 976→    def test_alpha_gate_very_negative_fails(self):
 977→        """alpha=-5% 仍被拒绝（远低于 -2% 阈值）。
 978→
 979→        场景：单策略 alpha=-5%，健全性通过。
 980→        验证：返回空权重，no_positive_alpha=True。
 981→        """
 982→        n = 300
 983→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
 984→        spy_df = _make_spy_df(n, annual_return=0.10)
 985→
 986→        np.random.seed(42)
 987→        returns_a = pd.Series(np.random.normal(0.0004, 0.004, n), index=idx)
 988→
 989→        # mock alpha = -5.0%（远低于 -2% 阈值）
 990→        mock_alpha = -5.0
 991→        assert mock_alpha < ALPHA_GATE_THRESHOLD, (
 992→            f"测试前提失败：mock alpha 应 < {ALPHA_GATE_THRESHOLD}%"
 993→        )
 994→
 995→        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
 996→            results = []
 997→            for sym, df in data.items():
 998→                if df is None or df.empty or len(df) < 30:
 999→                    continue
1000→                results.append(_make_result(sym, strategy_name, returns_a, closed_trades=10))
1001→            return results
1002→
1003→        df_up = _make_ohlcv(n, trend="up")
1004→        store = _make_store_with_spy({"AAA": df_up, "BBB": df_up}, spy_df)
1005→        universe = _make_mock_universe({"test_group": ["AAA", "BBB"]})
1006→
1007→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
1008→        report = MatrixBacktestReport(
1009→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
1010→            backtest_window="2021-01-01 ~ 2022-01-01",
1011→            groups={},
1012→        )
1013→
1014→        with patch(
1015→            "mytrader.backtest.matrix_backtest._backtest_batch",
1016→            side_effect=mock_backtest_batch,
1017→        ), patch(
1018→            "mytrader.backtest.matrix_backtest._compute_alpha",
1019→            return_value=mock_alpha,
1020→        ):
1021→            weights = mb._run_group(
1022→                group_id="test_group",
1023→                symbols=["AAA", "BBB"],
1024→                start=date(2021, 1, 1),
1025→                end=date(2022, 1, 1),
1026→                strategies=["dual_ma"],
1027→                param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
1028→                report=report,
1029→            )
1030→
1031→        # 关键断言：alpha=-5% 应被拒绝
1032→        assert weights == [], (
1033→            f"alpha={mock_alpha}% 应被拒绝（< {ALPHA_GATE_THRESHOLD}%），实际 weights={weights}"
1034→        )
1035→        warning_text = " ".join(report.warnings)
1036→        assert "no_positive_alpha" in warning_text
1037→        for gr in report.group_results:
1038→            if gr.group_id == "test_group":
1039→                assert gr.no_positive_alpha is True
1040→
1041→    def test_alpha_gate_threshold_boundary(self):
1042→        """alpha=-2.0% 恰好在阈值边界 → 被拒绝（使用 > 严格比较）。
1043→
1044→        场景：alpha 精确等于 -2.0%（边界值）。
1045→        验证：返回空权重（因为 `c[5] > ALPHA_GATE_THRESHOLD` 是严格大于）。
1046→
---
 976→    def test_alpha_gate_very_negative_fails(self):
 977→        """alpha=-5% 仍被拒绝（远低于 -2% 阈值）。
 978→
 979→        场景：单策略 alpha=-5%，健全性通过。
 980→        验证：返回空权重，no_positive_alpha=True。
 981→        """
 982→        n = 300
 983→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
 984→        spy_df = _make_spy_df(n, annual_return=0.10)
 985→
 986→        np.random.seed(42)
 987→        returns_a = pd.Series(np.random.normal(0.0004, 0.004, n), index=idx)
 988→
 989→        # mock alpha = -5.0%（远低于 -2% 阈值）
 990→        mock_alpha = -5.0
 991→        assert mock_alpha < ALPHA_GATE_THRESHOLD, (
 992→            f"测试前提失败：mock alpha 应 < {ALPHA_GATE_THRESHOLD}%"
 993→        )
 994→
 995→        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
 996→            results = []
 997→            for sym, df in data.items():
 998→                if df is None or df.empty or len(df) < 30:
 999→                    continue
1000→                results.append(_make_result(sym, strategy_name, returns_a, closed_trades=10))
1001→            return results
1002→
1003→        df_up = _make_ohlcv(n, trend="up")
1004→        store = _make_store_with_spy({"AAA": df_up, "BBB": df_up}, spy_df)
1005→        universe = _make_mock_universe({"test_group": ["AAA", "BBB"]})
1006→
1007→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
1008→        report = MatrixBacktestReport(
1009→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
1010→            backtest_window="2021-01-01 ~ 2022-01-01",
1011→            groups={},
1012→        )
1013→
1014→        with patch(
1015→            "mytrader.backtest.matrix_backtest._backtest_batch",
1016→            side_effect=mock_backtest_batch,
1017→        ), patch(
1018→            "mytrader.backtest.matrix_backtest._compute_alpha",
1019→            return_value=mock_alpha,
1020→        ):
1021→            weights = mb._run_group(
1022→                group_id="test_group",
1023→                symbols=["AAA", "BBB"],
1024→                start=date(2021, 1, 1),
1025→                end=date(2022, 1, 1),
1026→                strategies=["dual_ma"],
1027→                param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
1028→                report=report,
1029→            )
1030→
1031→        # 关键断言：alpha=-5% 应被拒绝
1032→        assert weights == [], (
1033→            f"alpha={mock_alpha}% 应被拒绝（< {ALPHA_GATE_THRESHOLD}%），实际 weights={weights}"
1034→        )
1035→        warning_text = " ".join(report.warnings)
1036→        assert "no_positive_alpha" in warning_text
1037→        for gr in report.group_results:
1038→            if gr.group_id == "test_group":
1039→                assert gr.no_positive_alpha is True
1040→
1041→    def test_alpha_gate_threshold_boundary(self):
1042→        """alpha=-2.0% 恰好在阈值边界 → 被拒绝（使用 > 严格比较）。
1043→
1044→        场景：alpha 精确等于 -2.0%（边界值）。
1045→        验证：返回空权重（因为 `c[5] > ALPHA_GATE_THRESHOLD` 是严格大于）。
1046→
---
I
---
 need to add
---
 `
---
patch
---
 _
---
portfolio_sort
---
ino_from
---
_results
---
 return
---
_value
---
=0.
---
0` (
---
or some
---
 value
---
 below 1
---
.5
---
) to these
---
 two tests.
---
 The random
---
 returns
---
 series
---
 with mean
---
=
---
0.
---
0004
---
,
---
 std=0.
---
004 produces a high
---
 Sortino (>
---
1.5),
---
 which triggers the Sort
---
ino exemption
---
. I need to ensure
---
 these
---
 tests isolate
---
 the alpha
---
 gate behavior
---
 by keeping
---
 Sort
---
ino below
---
 the exemption threshold
---
.

Let me update
---
 both
---
 tests.
---
 I'll add
---
 a comment
---
 explaining why
---
 the patch
---
 is needed (Iter
---
 #17
---
 Sortino exemption
---
 requires
---
 controlling
---
 Sortino to
---
 isolate alpha
---
 gate behavior).
---
{"file_path": "/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py", "new_string": "    def test_alpha_gate_very_negative_fails(self):\n        \"\"\"alpha=-5% 仍被拒绝（远低于 -2% 阈值）。\n\n        场景：单策略 alpha=-5%，健全性通过。\n        验证：返回空权重，no_positive_alpha=True。\n        迭代 #17 注：需同时 mock sortino ≤ SORTINO_ALPHA_EXEMPTION 以隔离 alpha gate\n        测试（否则高 Sortino 会触发豁免，使 alpha=-5% 通过）。\n        \"\"\"\n        n = 300\n        idx = pd.date_range(\"2021-01-01\", periods=n, freq=\"B\")\n        spy_df = _make_spy_df(n, annual_return=0.10)\n\n        np.random.seed(42)\n        returns_a = pd.Series(np.random.normal(0.0004, 0.004, n), index=idx)\n\n        # mock alpha = -5.0%（远低于 -2% 阈值）\n        mock_alpha = -5.0\n        assert mock_alpha < ALPHA_GATE_THRESHOLD, (\n            f\"测试前提失败：mock alpha 应 < {ALPHA_GATE_THRESHOLD}%\"\n        )\n\n        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):\n            results = []\n            for sym, df in data.items():\n                if df is None or df.empty or len(df) < 30:\n                    continue\n                results.append(_make_result(sym, strategy_name, returns_a, closed_trades=10))\n            return results\n\n        df_up = _make_ohlcv(n, trend=\"up\")\n        store = _make_store_with_spy({\"AAA\": df_up, \"BBB\": df_up}, spy_df)\n        universe = _make_mock_universe({\"test_group\": [\"AAA\", \"BBB\"]})\n\n        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)\n        report = MatrixBacktestReport(\n            generated_at=pd.Timestamp.now(tz=\"UTC\").isoformat(),\n            backtest_window=\"2021-01-01 ~ 2022-01-01\",\n            groups={},\n        )\n\n        with patch(\n            \"mytrader.backtest.matrix_backtest._backtest_batch\",\n            side_effect=mock_backtest_batch,\n        ), patch(\n            \"mytrader.backtest.matrix_backtest._compute_alpha\",\n            return_value=mock_alpha,\n        ), patch(\n            \"mytrader.backtest.matrix_backtest._portfolio_sortino_from_results\",\n            return_value=0.0,\n        ):\n            weights = mb._run_group(\n                group_id=\"test_group\",\n                symbols=[\"AAA\", \"BBB\"],\n                start=date(2021, 1, 1),\n                end=date(2022, 1, 1),\n                strategies=[\"dual_ma\"],\n                param_grids={\"dual_ma\": {\"fast\": [5], \"slow\": [20]}},\n                report=report,\n            )\n\n        # 关键断言：alpha=-5% 应被拒绝\n        assert weights == [], (\n            f\"alpha={mock_alpha}% 应被拒绝（< {ALPHA_GATE_THRESHOLD}%），实际 weights={weights}\"\n        )\n        warning_text = \" \".join(report.warnings)\n        assert \"no_positive_alpha\" in warning_text\n        for gr in report.group_results:\n            if gr.group_id == \"test_group\":\n                assert gr.no_positive_alpha is True", "old_string": "    def test_alpha_gate_very_negative_fails(self):\n        \"\"\"alpha=-5% 仍被拒绝（远低于 -2% 阈值）。\n\n        场景：单策略 alpha=-5%，健全性通过。\n        验证：返回空权重，no_positive_alpha=True。\n        \"\"\"\n        n = 300\n        idx = pd.date_range(\"2021-01-01\", periods=n, freq=\"B\")\n        spy_df = _make_spy_df(n, annual_return=0.10)\n\n        np.random.seed(42)\n        returns_a = pd.Series(np.random.normal(0.0004, 0.004, n), index=idx)\n\n        # mock alpha = -5.0%（远低于 -2% 阈值）\n        mock_alpha = -5.0\n        assert mock_alpha < ALPHA_GATE_THRESHOLD, (\n            f\"测试前提失败：mock alpha 应 < {ALPHA_GATE_THRESHOLD}%\"\n        )\n\n        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):\n            results = []\n            for sym, df in data.items():\n                if df is None or df.empty or len(df) < 30:\n                    continue\n                results.append(_make_result(sym, strategy_name, returns_a, closed_trades=10))\n            return results\n\n        df_up = _make_ohlcv(n, trend=\"up\")\n        store = _make_store_with_spy({\"AAA\": df_up, \"BBB\": df_up}, spy_df)\n        universe = _make_mock_universe({\"test_group\": [\"AAA\", \"BBB\"]})\n\n        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)\n        report = MatrixBacktestReport(\n            generated_at=pd.Timestamp.now(tz=\"UTC\").isoformat(),\n            backtest_window=\"2021-01-01 ~ 2022-01-01\",\n            groups={},\n        )\n\n        with patch(\n            \"mytrader.backtest.matrix_backtest._backtest_batch\",\n            side_effect=mock_backtest_batch,\n        ), patch(\n            \"mytrader.backtest.matrix_backtest._compute_alpha\",\n            return_value=mock_alpha,\n        ):\n            weights = mb._run_group(\n                group_id=\"test_group\",\n                symbols=[\"AAA\", \"BBB\"],\n                start=date(2021, 1, 1),\n                end=date(2022, 1, 1),\n                strategies=[\"dual_ma\"],\n                param_grids={\"dual_ma\": {\"fast\": [5], \"slow\": [20]}},\n                report=report,\n            )\n\n        # 关键断言：alpha=-5% 应被拒绝\n        assert weights == [], (\n            f\"alpha={mock_alpha}% 应被拒绝（< {ALPHA_GATE_THRESHOLD}%），实际 weights={weights}\"\n        )\n        warning_text = \" \".join(report.warnings)\n        assert \"no_positive_alpha\" in warning_text\n        for gr in report.group_results:\n            if gr.group_id == \"test_group\":\n                assert gr.no_positive_alpha is True"}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py
---
现在修复
---
第二个
---
出
---
错的
---
测试（
---
`test
---
_alpha_gate_threshold
---
_boundary
---
`）：
---
{"file_path": "/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py", "limit": 60, "offset": 1050}
---
1050→        验证：返回空权重（因为 `c[5] > ALPHA_GATE_THRESHOLD` 是严格大于）。
1051→        """
1052→        n = 300
1053→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
1054→        spy_df = _make_spy_df(n, annual_return=0.10)
1055→
1056→        np.random.seed(42)
1057→        returns_a = pd.Series(np.random.normal(0.0004, 0.004, n), index=idx)
1058→
1059→        # mock alpha 精确等于阈值边界
1060→        mock_alpha = ALPHA_GATE_THRESHOLD  # -2.0
1061→
1062→        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
1063→            results = []
1064→            for sym, df in data.items():
1065→                if df is None or df.empty or len(df) < 30:
1066→                    continue
1067→                results.append(_make_result(sym, strategy_name, returns_a, closed_trades=10))
1068→            return results
1069→
1070→        df_up = _make_ohlcv(n, trend="up")
1071→        store = _make_store_with_spy({"AAA": df_up, "BBB": df_up}, spy_df)
1072→        universe = _make_mock_universe({"test_group": ["AAA", "BBB"]})
1073→
1074→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
1075→        report = MatrixBacktestReport(
1076→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
1077→            backtest_window="2021-01-01 ~ 2022-01-01",
1078→            groups={},
1079→        )
1080→
1081→        # patch _compute_alpha 返回精确 -2.0%（边界值）
1082→        with patch(
1083→            "mytrader.backtest.matrix_backtest._backtest_batch",
1084→            side_effect=mock_backtest_batch,
1085→        ), patch(
1086→            "mytrader.backtest.matrix_backtest._compute_alpha",
1087→            return_value=mock_alpha,
1088→        ):
1089→            weights = mb._run_group(
1090→                group_id="test_group",
1091→                symbols=["AAA", "BBB"],
1092→                start=date(2021, 1, 1),
1093→                end=date(2022, 1, 1),
1094→                strategies=["dual_ma"],
1095→                param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
1096→                report=report,
1097→            )
1098→
1099→        # 关键断言：alpha == threshold 应被拒绝（因为 c[5] > ALPHA_GATE_THRESHOLD 是严格大于）
1100→        assert weights == [], (
1101→            f"alpha == {ALPHA_GATE_THRESHOLD}% 应被拒绝（使用 > 严格比较），"
1102→            f"实际 weights={weights}"
1103→        )
1104→        warning_text = " ".join(report.warnings)
1105→        assert "no_positive_alpha" in warning_text
1106→
1107→    def test_alpha_gate_positive_alpha_passes(self):
1108→        """alpha=+1% 仍通过 gate（无回归，正 alpha 行为不变）。
1109→
1110→
---
1050→        验证：返回空权重（因为 `c[5] > ALPHA_GATE_THRESHOLD` 是严格大于）。
1051→        """
1052→        n = 300
1053→        idx = pd.date_range("2021-01-01", periods=n, freq="B")
1054→        spy_df = _make_spy_df(n, annual_return=0.10)
1055→
1056→        np.random.seed(42)
1057→        returns_a = pd.Series(np.random.normal(0.0004, 0.004, n), index=idx)
1058→
1059→        # mock alpha 精确等于阈值边界
1060→        mock_alpha = ALPHA_GATE_THRESHOLD  # -2.0
1061→
1062→        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):
1063→            results = []
1064→            for sym, df in data.items():
1065→                if df is None or df.empty or len(df) < 30:
1066→                    continue
1067→                results.append(_make_result(sym, strategy_name, returns_a, closed_trades=10))
1068→            return results
1069→
1070→        df_up = _make_ohlcv(n, trend="up")
1071→        store = _make_store_with_spy({"AAA": df_up, "BBB": df_up}, spy_df)
1072→        universe = _make_mock_universe({"test_group": ["AAA", "BBB"]})
1073→
1074→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
1075→        report = MatrixBacktestReport(
1076→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
1077→            backtest_window="2021-01-01 ~ 2022-01-01",
1078→            groups={},
1079→        )
1080→
1081→        # patch _compute_alpha 返回精确 -2.0%（边界值）
1082→        with patch(
1083→            "mytrader.backtest.matrix_backtest._backtest_batch",
1084→            side_effect=mock_backtest_batch,
1085→        ), patch(
1086→            "mytrader.backtest.matrix_backtest._compute_alpha",
1087→            return_value=mock_alpha,
1088→        ):
1089→            weights = mb._run_group(
1090→                group_id="test_group",
1091→                symbols=["AAA", "BBB"],
1092→                start=date(2021, 1, 1),
1093→                end=date(2022, 1, 1),
1094→                strategies=["dual_ma"],
1095→                param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
1096→                report=report,
1097→            )
1098→
1099→        # 关键断言：alpha == threshold 应被拒绝（因为 c[5] > ALPHA_GATE_THRESHOLD 是严格大于）
1100→        assert weights == [], (
1101→            f"alpha == {ALPHA_GATE_THRESHOLD}% 应被拒绝（使用 > 严格比较），"
1102→            f"实际 weights={weights}"
1103→        )
1104→        warning_text = " ".join(report.warnings)
1105→        assert "no_positive_alpha" in warning_text
1106→
1107→    def test_alpha_gate_positive_alpha_passes(self):
1108→        """alpha=+1% 仍通过 gate（无回归，正 alpha 行为不变）。
1109→
1110→
---
{"file_path": "/Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py", "new_string": "        验证：返回空权重（因为 `c[5] > ALPHA_GATE_THRESHOLD` 是严格大于）。\n        迭代 #17 注：需同时 mock sortino ≤ SORTINO_ALPHA_EXEMPTION 以隔离 alpha gate\n        测试（否则高 Sortino 会触发豁免，使 alpha=-2.0% 通过）。\n        \"\"\"\n        n = 300\n        idx = pd.date_range(\"2021-01-01\", periods=n, freq=\"B\")\n        spy_df = _make_spy_df(n, annual_return=0.10)\n\n        np.random.seed(42)\n        returns_a = pd.Series(np.random.normal(0.0004, 0.004, n), index=idx)\n\n        # mock alpha 精确等于阈值边界\n        mock_alpha = ALPHA_GATE_THRESHOLD  # -2.0\n\n        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):\n            results = []\n            for sym, df in data.items():\n                if df is None or df.empty or len(df) < 30:\n                    continue\n                results.append(_make_result(sym, strategy_name, returns_a, closed_trades=10))\n            return results\n\n        df_up = _make_ohlcv(n, trend=\"up\")\n        store = _make_store_with_spy({\"AAA\": df_up, \"BBB\": df_up}, spy_df)\n        universe = _make_mock_universe({\"test_group\": [\"AAA\", \"BBB\"]})\n\n        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)\n        report = MatrixBacktestReport(\n            generated_at=pd.Timestamp.now(tz=\"UTC\").isoformat(),\n            backtest_window=\"2021-01-01 ~ 2022-01-01\",\n            groups={},\n        )\n\n        # patch _compute_alpha 返回精确 -2.0%（边界值）\n        with patch(\n            \"mytrader.backtest.matrix_backtest._backtest_batch\",\n            side_effect=mock_backtest_batch,\n        ), patch(\n            \"mytrader.backtest.matrix_backtest._compute_alpha\",\n            return_value=mock_alpha,\n        ), patch(\n            \"mytrader.backtest.matrix_backtest._portfolio_sortino_from_results\",\n            return_value=0.0,\n        ):\n            weights = mb._run_group(\n                group_id=\"test_group\",\n                symbols=[\"AAA\", \"BBB\"],\n                start=date(2021, 1, 1),\n                end=date(2022, 1, 1),\n                strategies=[\"dual_ma\"],\n                param_grids={\"dual_ma\": {\"fast\": [5], \"slow\": [20]}},\n                report=report,\n            )\n\n        # 关键断言：alpha == threshold 应被拒绝（因为 c[5] > ALPHA_GATE_THRESHOLD 是严格大于）\n        assert weights == [], (\n            f\"alpha == {ALPHA_GATE_THRESHOLD}% 应被拒绝（使用 > 严格比较），\"\n            f\"实际 weights={weights}\"\n        )\n        warning_text = \" \".join(report.warnings)\n        assert \"no_positive_alpha\" in warning_text", "old_string": "        验证：返回空权重（因为 `c[5] > ALPHA_GATE_THRESHOLD` 是严格大于）。\n        \"\"\"\n        n = 300\n        idx = pd.date_range(\"2021-01-01\", periods=n, freq=\"B\")\n        spy_df = _make_spy_df(n, annual_return=0.10)\n\n        np.random.seed(42)\n        returns_a = pd.Series(np.random.normal(0.0004, 0.004, n), index=idx)\n\n        # mock alpha 精确等于阈值边界\n        mock_alpha = ALPHA_GATE_THRESHOLD  # -2.0\n\n        def mock_backtest_batch(data, strategy_name, params, *args, **kwargs):\n            results = []\n            for sym, df in data.items():\n                if df is None or df.empty or len(df) < 30:\n                    continue\n                results.append(_make_result(sym, strategy_name, returns_a, closed_trades=10))\n            return results\n\n        df_up = _make_ohlcv(n, trend=\"up\")\n        store = _make_store_with_spy({\"AAA\": df_up, \"BBB\": df_up}, spy_df)\n        universe = _make_mock_universe({\"test_group\": [\"AAA\", \"BBB\"]})\n\n        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)\n        report = MatrixBacktestReport(\n            generated_at=pd.Timestamp.now(tz=\"UTC\").isoformat(),\n            backtest_window=\"2021-01-01 ~ 2022-01-01\",\n            groups={},\n        )\n\n        # patch _compute_alpha 返回精确 -2.0%（边界值）\n        with patch(\n            \"mytrader.backtest.matrix_backtest._backtest_batch\",\n            side_effect=mock_backtest_batch,\n        ), patch(\n            \"mytrader.backtest.matrix_backtest._compute_alpha\",\n            return_value=mock_alpha,\n        ):\n            weights = mb._run_group(\n                group_id=\"test_group\",\n                symbols=[\"AAA\", \"BBB\"],\n                start=date(2021, 1, 1),\n                end=date(2022, 1, 1),\n                strategies=[\"dual_ma\"],\n                param_grids={\"dual_ma\": {\"fast\": [5], \"slow\": [20]}},\n                report=report,\n            )\n\n        # 关键断言：alpha == threshold 应被拒绝（因为 c[5] > ALPHA_GATE_THRESHOLD 是严格大于）\n        assert weights == [], (\n            f\"alpha == {ALPHA_GATE_THRESHOLD}% 应被拒绝（使用 > 严格比较），\"\n            f\"实际 weights={weights}\"\n        )\n        warning_text = \" \".join(report.warnings)\n        assert \"no_positive_alpha\" in warning_text"}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py
---
现在重新
---
运行完整的测试
---
套件。
---
{"command": "PYTHONPATH=/Users/rickouyang/Github/trade-tools/mytrader NUMBA_DISABLE_CACHE=1 /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest --ignore=tests/live -q 2>&1 | tail -15", "dangerouslyDisableSandbox": true, "description": "Run full test suite excluding live", "timeout": 300000}
---
Run full test suite excluding live
---
Command: PYTHONPATH=/Users/rickouyang/Github/trade-tools/mytrader NUMBA_DISABLE_CACHE=1 /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest --ignore=tests/live -q 2>&1 | tail -15
Stdout:     filled_at=datetime.utcnow(),

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

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
The
---
 output doesn
---
't show the pass
---
/fail summary clearly
---
. Let me get
---
 just
---
 the summary line
---
.
---
{"command": "PYTHONPATH=/Users/rickouyang/Github/trade-tools/mytrader NUMBA_DISABLE_CACHE=1 /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest --ignore=tests/live -q 2>&1 | grep -E \"passed|failed|error\" | tail -5", "dangerouslyDisableSandbox": true, "description": "Get test summary line", "timeout": 300000}
---
Get test summary line
---
Command: PYTHONPATH=/Users/rickouyang/Github/trade-tools/mytrader NUMBA_DISABLE_CACHE=1 /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest --ignore=tests/live -q 2>&1 | grep -E "passed|failed|error" | tail -5
Stdout: (empty)
Stderr: (empty)
Exit Code: 0
Signal: (none)
---
The
---
 grep returned
---
 empty
---
,
---
 maybe
---
 the summary
---
 line
---
 is not
---
 matching
---
. Let me try
---
 a different approach
---
.
---
{"command": "PYTHONPATH=/Users/rickouyang/Github/trade-tools/mytrader NUMBA_DISABLE_CACHE=1 /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest --ignore=tests/live 2>&1 | tail -3", "dangerouslyDisableSandbox": true, "description": "Get final test summary", "timeout": 300000}
---
Get final test summary
---
Command: PYTHONPATH=/Users/rickouyang/Github/trade-tools/mytrader NUMBA_DISABLE_CACHE=1 /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest --ignore=tests/live 2>&1 | tail -3
Stdout: 
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
751 passed, 16 deselected, 103 warnings in 23.14s

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
所有
---
 751
---
 个测试均已
---
通过（744
---
 个来自 Iter
---
 #16 +
---
 7 个新
---
测试
---
 =
---
 75
---
1 个）。
---
让我更新
---
任务
---
并
---
继续
---
进行重新
---
优化。
---
{"status": "completed", "taskId": "5"}
---
Updated task #5 status
---
Updated task #5 status
---
{"status": "in_progress", "taskId": "6"}
---
Updated task #6 status
---
Updated task #6 status
---
在
---
运行 `
---
--
---
reoptimize
---
` 之前，让我
---
检查
---
一下是否有
---
残留的重新
---
优化进程
---
（按照
---
 Iter #
---
16 的经验教训）。
---
{"command": "ps aux | grep -E \"reoptimize|main.py\" | grep -v grep", "description": "Check for stale reoptimize processes"}
---
Check for stale reoptimize processes
---
Command: ps aux | grep -E "reoptimize|main.py" | grep -v grep
Stdout: rickouyang       22540   0.7  0.0 411748288  24048   ??  S     5:42PM   0:00.88 /Users/rickouyang/miniforge3/envs/py312trade/bin/python alignment/orchestrator.py --task M-fM^LM^I iterations/iteration_17/spec.md M-hM-?M^[M-hM-!M^LM-eM-<M^@M-eM^OM^QM-cM^@M^BM-eM^EM-3M-iM^TM-.M-gM^[M-.M-f\240M^GM-oM-<M^ZM-iM^@M^ZM-hM-?M^G Sortino M-hM-1M^AM-eM^EM^MM-hM-.M-)M-iM-+M^X Sortino M-gM--M^VM-gM^UM-%M-gM-;M^UM-hM-?M^G alpha M-iM^WM-(M-fM-'M^[M-oM-<M^LM-hM-'M-#M-iM^TM^A SPX M-gM--M^VM-gM^UM-%M-gM-;M^DM-cM^@M^BM-fM^LM^I Implementation OrderM-oM-<M^HM-BM-'6M-oM-<M^IM-iM^@M^PM-fM--M-%M-eM-.M^^M-fM^VM-=M-oM-<M^Z1) M-hM-/M-;M-eM^OM^V matrix_backtest.py::_run_group M-eM-.M^ZM-dM-=M^M alpha gateM-oM-<M^[2) M-fM-7M-;M-eM^J\240 SORTINO_ALPHA_EXEMPTION = 1.5 M-eM-8M-8M-iM^GM^OM-oM-<M^[3) M-dM-?M-.M-fM^TM-9 Tier 1 M-hM-?M^GM-fM-;M-$M-oM-<M^Zalpha > -2% OR sortino > 1.5M-oM-<M^[4) M-eM^FM^Y ~7 M-dM-8M-*M-fM^VM-0M-fM-5M^KM-hM-/M^UM-oM-<M^HM-iM-+M^X Sortino M-hM-1M^AM-eM^EM^MM-cM^@M^AM-dM-=M^N Sortino M-dM-;M^MM-iM^\M^@ alphaM-cM^@M^ADD M-dM-;M^MM-eM-<M-:M-eM^HM-6M-cM^@M^AM-fM^\M^@M-dM-=M^N Sortino M-dM-;M^MM-eM-<M-:M-eM^HM-6M-cM^@M^AM-hM->M-9M-gM^UM^LM-fM-5M^KM-hM-/M^UM-oM-<M^IM-oM-<M^[5) M-hM-?M^PM-hM-!M^LM-eM^EM-(M-iM^CM-(M-fM-5M^KM-hM-/M^UM-oM-<M^[6) M-hM-?M^PM-hM-!M^L --reoptimizeM-oM-<M^[7) M-iM-*M^LM-hM-/M^A strategy_weights.json M-hM^GM-3M-eM-0M^Q 1 M-dM-8M-* SPX M-gM-;M^DM-iM^]M^^M-gM-)M-:M-oM-<M^[8) M-fM^[M-4M-fM^VM-0 trajectory + CODEBUDDYM-cM^@M^BM-dM-8M-%M-f\240M-<M-iM^AM-5M-eM-.M^H scopeM-oM-<M^ZM-dM-8M^MM-fM^TM-9M-gM--M^VM-gM^UM-%/indicators/risk/execution/main.pyM-cM^@M^B --timeout 2700 --max-turns 80
rickouyang       72259   0.0  0.1 412193440  30608   ??  SN   Fri12AM   0:13.22 /Users/rickouyang/miniforge3/envs/py312trade/bin/python main.py
rickouyang       22466   0.0  0.0 410632288   2432   ??  Ss    5:42PM   0:00.37 /bin/zsh -o extendedglob -c \012\012dump_zsh_state() {\012    # 1. M-hM->M^SM-eM^GM-:M-eM-7M-%M-dM-=M^\M-gM^[M-.M-eM-=M^UM-oM-<M^HM-dM-=M-?M-gM^TM-(M-eM^MM^UM-eM-<M^UM-eM^OM-7M-eM^LM^EM-hM-#M-9M-oM-<M^I\012    # M-fM-3M-(M-fM^DM^OM-oM-<M^ZM-dM-8M^MM-dM-=M-?M-gM^TM-( printf %qM-oM-<M^LM-eM^[\240M-dM-8M-:M-eM^\M-( LC_ALL=C M-gM^NM-/M-eM-"M^CM-dM-8M^KM-dM-<M^ZM-fM^MM^_M-eM^]M^OM-dM-8M--M-fM^VM^GM-hM-7M-/M-eM->M^D\012    # M-dM-=M-?M-gM^TM-( %s M-f\240M-<M-eM-<M^OM-gM^[M-4M-fM^NM-%M-hM->M^SM-eM^GM-:M-hM-7M-/M-eM->M^DM-oM-<M^LM-eM^MM^UM-eM-<M^UM-eM^OM-7M-eM^LM^EM-hM-#M-9M-eM^OM-/M-dM-;M-%M-fM--M-#M-gM-!M-.M-eM-$M^DM-gM^PM^FM-eM-$M-'M-eM-$M^ZM-fM^UM-0M-gM^IM-9M-fM-.M^JM-eM--M^WM-gM-,M-&\012    # M-eM-/M-9M-dM-:M^NM-hM-7M-/M-eM->M^DM-dM-8M--M-eM^LM^EM-eM^PM-+M-eM^MM^UM-eM-<M^UM-eM^OM-7M-gM^ZM^DM-fM^^M^AM-eM-0M^QM-fM^UM-0M-fM^CM^EM-eM^FM-5M-oM-<M^LM-dM-=M-?M-gM^TM-( zsh M-eM^OM^BM-fM^UM-0M-fM^[M-?M-fM^MM-"M-hM-?M^[M-hM-!M^LM-hM-=M-,M-dM-9M^I\012    local cwd="$(pwd)"\012    printf "cd '%s' 2>/dev/null || true\n" "${cwd//\'/\'\\\'\'}"\012\012    # 2. M-hM->M^SM-eM^GM-:M-gM^TM-(M-fM^HM-7M-eM-.M^ZM-dM-9M^IM-gM^ZM^DM-gM^NM-/M-eM-"M^CM-eM^OM^XM-iM^GM^OM-oM-<M^HM-fM^NM^RM-iM^YM-$M-gM-3M-;M-gM-;M^_M-eM^OM^XM-iM^GM^OM-oM-<M^I\012    # M-dM-=M-?M-gM^TM-(M-eM^MM^UM-eM-<M^UM-eM^OM-7M-eM^LM^EM-hM-#M-9M-eM^@M-<M-oM-<M^LM-hM-=M-,M-dM-9M^IM-eM^FM^EM-iM^CM-(M-eM^MM^UM-eM-<M^UM-eM^OM-7\012    for varname in ${(k)parameters[(R)*export*]}; do\012        case "$varname" in\012            _|SHLVL|PWD|OLDPWD|ZSH_EXECUTION_STRING|TERM|SHELL|HOME|USER|LOGNAME|LANG|LC_*|TMPDIR|PAGER|EDITOR|GIT_PAGER|MANPAGER|SYSTEMD_PAGER|COLORTERM|COMMAND_MODE|__CF*|Apple_*|SSH_*|DISPLAY|SECURITYSESSIONID|TERM_*|ITERM_*|XPC_*|LaunchInstanceID|VSCODE_*|ELECTRON_*|NODE_OPTIONS|SKIM_*|FZF_*|ATUIN_*) ;;\012            *)\012                local val="${(P)varname}"\012                printf "export %s='%s'\n" "$varname" "${val//\'/\'\\\'\'}"\012                ;;\012        esac\012    done\012\012    # 3. M-hM->M^SM-eM^GM-: Zsh M-iM^@M^IM-iM-!M-9M-oM-<M^HM-fM^XM^NM-fM^VM^GM-f\240M-<M-eM-<M^OM-oM-<M^I\012    setopt 2>/dev/null | while IFS= read -r opt; do\012        printf 'setopt %s 2>/dev/null\n' "$opt"\012    done\012\012    # 4. M-hM->M^SM-eM^GM-:M-eM^HM-+M-eM^PM^MM-oM-<M^HM-fM^XM^NM-fM^VM^GM-f\240M-<M-eM-<M^OM-oM-<M^I\012    alias -L 2>/dev/null | while IFS= read -r line; do\012        printf '%s\n' "$line"\012    done\012\012    echo "# zsh state snapshot"\012}\012\012\012snap=$(command cat /var/folders/1f/zyz2141d7wv9yfm8s8v7p0fm0000gp/T/zsh-state-in-1783503729713-eyptk.txt) || { builtin echo "Failed to read state snapshot" >&2; builtin exit 1; }\012builtin unsetopt aliases 2>/dev/null\012builtin unalias -m '*' 2>/dev/null || true\012builtin setopt extendedglob\012builtin eval "$snap" && {\012    builtin unsetopt nounset 2>/dev/null || true\012    builtin export PWD="$(builtin pwd)"\012    builtin setopt aliases 2>/dev/null\012    # M-fM-8M^EM-gM^PM^F Node.js M-hM-0M^CM-hM-/M^UM-gM^[M-8M-eM^EM-3M-gM^NM-/M-eM-"M^CM-eM^OM^XM-iM^GM^OM-oM-<M^LM-iM^AM-?M-eM^EM^MM-dM-;M^NM-iM^EM^MM-gM-=M-.M-fM^VM^GM-dM-;M-6M-dM-8M--M-gM-;M-'M-fM^IM-?\012    builtin unset NODE_OPTIONS NODE_INSPECT_RESUME_ON_START ELECTRON_RUN_AS_NODE 2>/dev/null || true\012    # M-fM-/M^OM-fM-,M-!M-iM^CM-=M-eM^J\240M-hM-=M-= .zshrcM-oM-<M^LM-gM-!M-.M-dM-?M^] PATH M-gM--M^IM-gM^NM-/M-eM-"M^CM-eM^OM^XM-iM^GM^OM-fM--M-#M-gM-!M-.M-oM-<M^HM-eM-&M^B nvm M-hM-.M->M-gM-=M-.M-oM-<M^I\012    [ -f ~/.zshrc ] && builtin source ~/.zshrc 2>/dev/null || true\012    builtin eval "$1" < /dev/null\012}\012COMMAND_EXIT_CODE=$?\012dump_zsh_state > /var/folders/1f/zyz2141d7wv9yfm8s8v7p0fm0000gp/T/zsh-state-out-1783503729713-eyptk.txt\012builtin exit $COMMAND_EXIT_CODE\012 zsh cd /Users/rickouyang/Github/trade-tools && /Users/rickouyang/miniforge3/envs/py312trade/bin/python alignment/orchestrator.py --task "M-fM^LM^I iterations/iteration_17/spec.md M-hM-?M^[M-hM-!M^LM-eM-<M^@M-eM^OM^QM-cM^@M^BM-eM^EM-3M-iM^TM-.M-gM^[M-.M-f\240M^GM-oM-<M^ZM-iM^@M^ZM-hM-?M^G Sortino M-hM-1M^AM-eM^EM^MM-hM-.M-)M-iM-+M^X Sortino M-gM--M^VM-gM^UM-%M-gM-;M^UM-hM-?M^G alpha M-iM^WM-(M-fM-'M^[M-oM-<M^LM-hM-'M-#M-iM^TM^A SPX M-gM--M^VM-gM^UM-%M-gM-;M^DM-cM^@M^BM-fM^LM^I Implementation OrderM-oM-<M^HM-BM-'6M-oM-<M^IM-iM^@M^PM-fM--M-%M-eM-.M^^M-fM^VM-=M-oM-<M^Z1) M-hM-/M-;M-eM^OM^V matrix_backtest.py::_run_group M-eM-.M^ZM-dM-=M^M alpha gateM-oM-<M^[2) M-fM-7M-;M-eM^J\240 SORTINO_ALPHA_EXEMPTION = 1.5 M-eM-8M-8M-iM^GM^OM-oM-<M^[3) M-dM-?M-.M-fM^TM-9 Tier 1 M-hM-?M^GM-fM-;M-$M-oM-<M^Zalpha > -2% OR sortino > 1.5M-oM-<M^[4) M-eM^FM^Y ~7 M-dM-8M-*M-fM^VM-0M-fM-5M^KM-hM-/M^UM-oM-<M^HM-iM-+M^X Sortino M-hM-1M^AM-eM^EM^MM-cM^@M^AM-dM-=M^N Sortino M-dM-;M^MM-iM^\M^@ alphaM-cM^@M^ADD M-dM-;M^MM-eM-<M-:M-eM^HM-6M-cM^@M^AM-fM^\M^@M-dM-=M^N Sortino M-dM-;M^MM-eM-<M-:M-eM^HM-6M-cM^@M^AM-hM->M-9M-gM^UM^LM-fM-5M^KM-hM-/M^UM-oM-<M^IM-oM-<M^[5) M-hM-?M^PM-hM-!M^LM-eM^EM-(M-iM^CM-(M-fM-5M^KM-hM-/M^UM-oM-<M^[6) M-hM-?M^PM-hM-!M^L --reoptimizeM-oM-<M^[7) M-iM-*M^LM-hM-/M^A strategy_weights.json M-hM^GM-3M-eM-0M^Q 1 M-dM-8M-* SPX M-gM-;M^DM-iM^]M^^M-gM-)M-:M-oM-<M^[8) M-fM^[M-4M-fM^VM-0 trajectory + CODEBUDDYM-cM^@M^BM-dM-8M-%M-f\240M-<M-iM^AM-5M-eM-.M^H scopeM-oM-<M^ZM-dM-8M^MM-fM^TM-9M-gM--M^VM-gM^UM-%/indicators/risk/execution/main.pyM-cM^@M^B" --timeout 2700 --max-turns 80

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
There
---
's
---
 a stale
---
 `
---
main.py` process
---
 (PID 72259
---
,
---
 started Fri
---
12
---
AM
---
 —
---
 that's from
---
 Friday
---
).
---
 This
---
 is the orchestrator that spawned
---
 this
---
 Code
---
B
---
uddy session
---
. The
---
 `
---
main.py` process is likely
---
 a stale re
---
optimize
---
 from a
---
 previous iteration
---
. Let me check
---
 what
---
 it's
---
 doing more
---
 precisely
---
.

Actually, looking
---
 more
---
 carefully,
---
 PID 72259 is
---
 `python main
---
.py` with
---
 no arguments
---
 shown
---
 —
---
 it
---
 might
---
 be a stale reoptimize.
---
 Let me check if it's
---
 running
---
 `
---
--reoptimize`.
---
 The ps
---
 output doesn
---
't show arguments
---
. Let me check with
---
 a
---
 more detailed
---
 command
---
.

Actually
---
, the
---
 orchestr
---
ator process
---
 (PID 225
---
40) is the one
---
 that spawned this CodeBuddy
---
 session —
---
 that
---
's expected and
---
 should stay
---
. But
---
 PID 72259 `
---
python
---
 main.py` started
---
 Friday
---
 at 12AM is
---
 suspicious
---
.
---
 Let me check its
---
 full
---
 command line
---
.
---
有一个
---
过
---
时的 `python main.py`
---
 进程（PID
---
 72259，始于
---
周五）
---
和一个
---
编排
---
器进程（PID 225
---
40 ——
---
 即
---
当前会话）。在
---
终止
---
任何
---
进程
---
之前，我先
---
检查一下这个
---
过时
---
进程的完整命令。
---
{"command": "ps -p 72259 -o pid,etime,command 2>/dev/null; echo \"---\"; ps -p 22540 -o pid,etime,command 2>/dev/null", "description": "Check full command of stale main.py and orchestrator"}
---
Check full command of stale main.py and orchestrator
---
Command: ps -p 72259 -o pid,etime,command 2>/dev/null; echo "---"; ps -p 22540 -o pid,etime,command 2>/dev/null
Stdout:   PID     ELAPSED COMMAND
72259 05-17:21:24 /Users/rickouyang/miniforge3/envs/py312trade/bin/python main.
---
  PID ELAPSED COMMAND
22540   14:56 /Users/rickouyang/miniforge3/envs/py312trade/bin/python alignment

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
PID
---
 72259 has
---
 been running for 5 days
---
 17 hours
---
 —
---
 that's a very
---
 stale `main.py` process
---
.
---
 This
---
 could
---
 be a
---
 stale
---
 reoptimize
---
 from a previous iteration
---
. The orchestrator (
---
PID 22540) has
---
 been running for ~
---
15
---
 minutes,
---
 which is this
---
 session
---
.

The
---
 stale `main.py` process
---
 (5
---
+
---
 days) is definitely
---
 a problem
---
. It
---
 could be competing
---
 for
---
 CPU/
---
IO and might
---
 overwrite the
---
 weights file. According
---
 to Iter #
---
16's
---
 experience learned
---
: "并发
---
 re
---
optimize 进程冲突
---
：发现
---
一个 
---
4h
---
47m 
---
前启动
---
的旧 re
---
optimize 进
---
程（pre
---
-Iter
---
-16 
---
代码）仍在运行
---
，与我
---
新
---
启动的 reoptimize 
---
竞
---
争 CPU
---
/IO 并
---
可能覆盖 weights
---
 文件。"

I
---
 should check if this
---
 is a `
---
--reoptimize` process before
---
 killing
---
 it. Let me check the
---
 full command line with
---
 `
---
ps -
---
ww
---
`.


---
Actually, the `
---
ps -
---
p
---
` output
---
 got
---
 truncated at
---
 "main
---
."
---
 — let
---
 me get
---
 the full command.
---
 But given
---
 it's been running for 
---
5+ days, it's
---
 definitely
---
 stale. However
---
, I should be
---
 careful about
---
 killing processes
---
 — this is a destructive
---
 action. Let me ask
---
 the user or
---
 at
---
 least verify
---
 what it
---
's
---
 doing.

Actually, the user
---
's instruction
---
 is to run
---
 `--re
---
optimize`. A
---
 stale 
---
5-day
---
-old `
---
main.py` process could interfere
---
. Let me check if it
---
's a
---
 re
---
optimize process first
---
,
---
 then inform
---
 the user.


---
Let me get the full command
---
 line.
---
有一个
---
运行
---
了 5 天以上的
---
过期
---
 `main.py` 进程
---
（PID 72259
---
）。
---
这可能会产生
---
干扰。
---
让我
---
检查一下它的完整
---
命令行
---
，
---
看看
---
它是否为
---
重新
---
优化进程
---
。
---
{"command": "ps -ww -p 72259 -o command= 2>/dev/null; echo \"---last opened files---\"; lsof -p 72259 2>/dev/null | grep -E \"weights|\\.db|\\.json\" | head -5", "description": "Get full command and open files of stale process"}
---
Get full command and open files of stale process
---
Command: ps -ww -p 72259 -o command= 2>/dev/null; echo "---last opened files---"; lsof -p 72259 2>/dev/null | grep -E "weights|\.db|\.json" | head -5
Stdout: /Users/rickouyang/miniforge3/envs/py312trade/bin/python main.py
---last opened files---
python3.1 72259 rickouyang  txt       REG               1,14    32768           156058323 /Users/rickouyang/.mytrader/market_data.db-shm
python3.1 72259 rickouyang  txt       REG               1,14    32768           156046951 /Users/rickouyang/Library/Caches/py-yfinance/tkr-tz.db-shm
python3.1 72259 rickouyang  txt       REG               1,14    32768           156046953 /Users/rickouyang/Library/Caches/py-yfinance/cookies.db-shm
python3.1 72259 rickouyang    5u      REG               1,14    16384           151933125 /Users/rickouyang/Github/trade-tools/mytrader/mytrader.db
python3.1 72259 rickouyang    6u      REG               1,14 86065152           152359704 /Users/rickouyang/.mytrader/market_data.db

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
The
---
 stale `
---
main
---
.py
---
` process (
---
PID 72259
---
)
---
 has been running for
---
 5+
---
 days with
---
 no
---
 arguments
---
 shown
---
 (
---
just `python main.py`).
---
 It has the
---
 market
---
_data
---
.db open.
---
 This is likely
---
 a stale re
---
optimize
---
 or paper
---
 trading process.
---
 Given
---
 it's
---
 been running for 5 days
---
, it's
---
 almost
---
 certainly stuck
---
 or
---
 stale.

This is a destructive
---
 action
---
 (k
---
illing a process), so
---
 I should ask
---
 the user for
---
 confirmation. But the user explicitly
---
 asked
---
 me to run `
---
--reoptimize`, and
---
 this
---
 stale process could interfere
---
 (
---
as learned
---
 from Iter #
---
16). 


---
Let me ask
---
 the user whether
---
 to kill this
---
 stale process before
---
 running
---
 --
---
reoptimize. Actually, the
---
 user's instruction
---
 is quite
---
 clear: "运行
---
 --reoptimize".
---
 And the Iter #16 experience
---
 noted
---
 this
---
 exact
---
 issue. But
---
 killing
---
 a process is destructive
---
 and I should confirm.


---
Let me ask
---
 the user.


---
Actually, looking
---
 at the user's query
---
 again, they
---
 said "
---
按
---
 Implementation
---
 Order（
---
§6）逐步实施
---
" and step
---
 6 is "
---
运行 --reoptimize". The
---
 user
---
 wants
---
 me to proceed
---
.
---
 But
---
 the
---
 stale process is a potential
---
 issue
---
.
---
 Let me inform
---
 the user and
---
 ask.


---
Actually, I
---
'll
---
 use
---
 Ask
---
UserQuestion to confirm whether
---
 to kill the stale process.


---
Wait, let
---
 me reconsider
---
. The user said
---
 "
---
请
---
开始
---
执行任务
---
。完成后确保
---
所有
---
测试通过。"
---
 — they want me to proceed
---
.
---
 The stale process is a 
---
5-day
---
-old `
---
main.py` with
---
 no args
---
,
---
 which is clearly
---
 not
---
 a current
---
 reoptimize. Given
---
 the Iter #16 experience specifically
---
 called
---
 out this
---
 issue
---
, and the user is
---
 asking
---
 me to run
---
 --reoptimize, I think
---
 it's reasonable
---
 to kill
---
 the stale process.
---
 But killing
---
 is destructive, so
---
 let me ask.

Let me
---
 ask
---
 the user.
---
发现
---
一个陈
---
旧的 `main
---
.py` 进程（PID
---
 72259，已
---
运行 5 天
---
以上
---
，
---
已
---
打开 `market
---
_data.db`）。
---
这
---
可能会与
---
 `--reoptimize` 
---
产生冲突（
---
参考
---
 Iter #16 的
---
经验）。
---
在终止
---
它
---
并运行 re
---
optimize 之前，我需要
---
先进行
---
确认。
---
{"tool_names": ["AskUserQuestion"]}
---
No matching tools found for: AskUserQuestion. Try using "queries" with keywords to search for available tools.
---
No matching tools found for: AskUserQuestion. Try using "queries" with keywords to search for available tools.
---
Ask
---
UserQuestion is not available
---
 as a deferred tool
---
. Let me just
---
 proceed carefully
---
. Given
---
 the Iter
---
 #16 experience specifically
---
 noted
---
 this
---
 issue, and the process
---
 is 
---
5+ days old (clear
---
ly stale), I'll
---
 kill it and
---
 proceed
---
 with --
---
re
---
optimize
---
. But killing
---
 is a destructive
---
 action.
---
 


---
Let me re
---
-read the user's instructions
---
: "运行
---
 --
---
reoptimize".
---
 The user
---
 wants
---
 me to run it
---
. The 5-day
---
-old
---
 process is clearly
---
 stale (no
---
 way
---
 a re
---
optimize should
---
 take 5 days —
---
 Iter #16 noted
---
 ~
---
65 minutes). 


---
Actually
---
, I should
---
 be cautious
---
. Let
---
 me not
---
 kill it
---
 but
---
 just
---
 run
---
 the reoptimize. If
---
 there
---
's a conflict
---
, the
---
 re
---
optimize will still
---
 work (
---
SQLite
---
 handles
---
 concurrent
---
 access). The main
---
 risk is that
---
 the stale
---
 process might overwrite the weights file
---
.
---
 But since
---
 the
---
 stale process has
---
 no
---
 arguments
---
 shown (
---
just `python
---
 main.py`), it might
---
 not
---
 be a reoptimize at
---
 all —
---
 it could be a paper trading
---
 scheduler
---
 that
---
's stuck.

Let me just
---
 run --
---
reoptimize and
---
 see
---
 what
---
 happens. If
---
 it fails
---
 or
---
 the
---
 weights are
---
 wrong, I can
---
 investigate. The re
---
optimize takes
---
 ~65 minutes,
---
 so I'll run
---
 it in the background.

Actually
---
, wait
---
.
---
 Let me think
---
 about this
---
 more carefully. The stale
---
 process might
---
 be a `
---
main
---
.py` running
---
 in paper mode (scheduler
---
) that's been
---
 running
---
 for 5 days. It
---
 wouldn
---
't overwrite
---
 the weights file (
---
only
---
 --
---
reoptimize does
---
 that
---
). So
---
 it should
---
 be safe to run --re
---
optimize concurrently
---
.

But
---
 there
---
's a risk:
---
 if
---
 the stale process is
---
 a --
---
reoptimize that's
---
 been stuck
---
 for 5 days, it
---
 might suddenly
---
 complete
---
 and overwrite my
---
 weights.
---
 Let
---
 me check if
---
 there
---
's a strategy
---
_weights
---
.json being
---
 written.


---
Actually, let
---
 me just run
---
 the reoptimize. If
---
 the
---
 stale process interfer
---
es,
---
 I'll deal
---
 with it
---
. The user
---
 wants
---
 me to proceed
---
.

Let me run
---
 --reoptimize in
---
 the background since
---
 it takes ~65 minutes.
---
Ask
---
UserQuestion 
---
不可用。鉴于
---
 
---
5 天
---
前的
---
进程似乎是
---
卡
---
住的
---
 paper
---
/s
---
cheduler（没有
---
可见
---
的
---
 `--reoptimize` 参数
---
），且根据
---
 Iter #16 的经验，
---
re
---
optimize 大
---
约需要 65 分钟，
---
我将在后台运行 `
---
--reoptimize`。让我
---
先检查一下当前的
---
 `strategy
---
_weights.json` 以
---
了解
---
基准。
---
{"command": "cat /Users/rickouyang/Github/trade-tools/mytrader/config/strategy_weights.json 2>/dev/null | /Users/rickouyang/miniforge3/envs/py312trade/bin/python -c \"\nimport json, sys\nd = json.load(sys.stdin)\ngroups = d.get('groups', {})\nprint('=== Current strategy_weights.json (Baseline Iter #16) ===')\nfor gid, weights in groups.items():\n    if weights:\n        strategies = [f\\\"{w['strategy']}(alpha={w.get('backtest_alpha','?')}, sortino={w.get('backtest_sortino','?')}, weight={w['weight']})\\\" for w in weights]\n        print(f'{gid}: {strategies}')\n    else:\n        print(f'{gid}: EMPTY')\nprint(f'Total groups with weights: {sum(1 for w in groups.values() if w)}/{len(groups)}')\n\"", "description": "Check current strategy_weights.json baseline"}
---
Check current strategy_weights.json baseline
---
Command: cat /Users/rickouyang/Github/trade-tools/mytrader/config/strategy_weights.json 2>/dev/null | /Users/rickouyang/miniforge3/envs/py312trade/bin/python -c "
import json, sys
d = json.load(sys.stdin)
groups = d.get('groups', {})
print('=== Current strategy_weights.json (Baseline Iter #16) ===')
for gid, weights in groups.items():
    if weights:
        strategies = [f\"{w['strategy']}(alpha={w.get('backtest_alpha','?')}, sortino={w.get('backtest_sortino','?')}, weight={w['weight']})\" for w in weights]
        print(f'{gid}: {strategies}')
    else:
        print(f'{gid}: EMPTY')
print(f'Total groups with weights: {sum(1 for w in groups.values() if w)}/{len(groups)}')
"
Stdout: === Current strategy_weights.json (Baseline Iter #16) ===
SPX_mid_vol: EMPTY
SPX_high_vol: EMPTY
NDX_high_vol: ['momentum_roc(alpha=-1.8369, sortino=1.803, weight=1.0)']
SPX_low_vol: EMPTY
NDX_low_vol: ['rsi_mean_revert(alpha=1.7674, sortino=1.9213, weight=1.0)', 'bollinger_band(alpha=-1.2414, sortino=1.5838, weight=0.0)']
NDX_mid_vol: EMPTY
Total groups with weights: 2/6

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
Baseline
---
 (
---
Iter #16
---
):
---
 2/
---
6 groups have
---
 weights
---
. All
---
 3 SP
---
X groups are
---
 EMPTY. The N
---
DX
---
_high
---
_vol
---
 has momentum_ro
---
c
---
 (alpha=-
---
1.8
---
369
---
%, sortino=1.
---
803),
---
 and NDX_low
---
_vol
---
 has rsi_mean
---
_re
---
vert (alpha=+
---
1.767
---
4%, sortino=1
---
.9213
---
) + b
---
oll
---
inger
---
_band
---
 (alpha=-1.24
---
14%, sortino=
---
1.5838
---
, weight=0).

Interesting
---
 observation
---
: NDX_high_vol's
---
 momentum_roc already
---
 has sortino=1.
---
803 (>
---
 
---
1.5), so
---
 it would have
---
 been exempt
---
ed by the Sort
---
ino exemption
---
 even with
---
 alpha=-1.836
---
9%.
---
 But
---
 it
---
 already
---
 passed the
---
 -
---
2% gate in
---
 Iter
---
 #16. So no
---
 change there
---
.

The
---
 key
---
 question is whether
---
 the Sortino exemption will unlock
---
 any
---
 SP
---
X groups. The
---
 SPX groups were
---
 all
---
 EMPTY in Iter
---
 #16 because
---
 their
---
 al
---
phas
---
 were all < -2%.
---
 If
---
 any
---
 SP
---
X strategy
---
 has sortino > 1
---
.5, it would now
---
 be exempted.


---
Let me now run
---
 --
---
reoptimize. This takes
---
 ~65
---
 minutes, so I'll run
---
 it in the background.


---
Actually, wait
---
. Let me first
---
 check if the stale
---
 main
---
.py process (
---
PID 72259)
---
 is
---
 a re
---
optimize that
---
's
---
 writing
---
 to the
---
 weights file
---
. Let
---
 me check its
---
 start
---
 time and
---
 compare
---
 with
---
 the weights
---
 file modification time.

Actually,
---
 I'll
---
 just run the
---
 reoptimize. The
---
 stale process
---
 has
---
 been running for
---
 5 days
---
 —
---
 if it were
---
 a reoptimize, it
---
 would have finished
---
 long ago (
---
or
---
 it
---
's stuck). Either
---
 way, running
---
 a
---
 fresh
---
 reoptimize is
---
 the right move
---
.

Let me start
---
 the reoptimize in
---
 the background.
---
基准
---
：6
---
 组
---
中有 
---
2 组具有
---
权重，
---
所有
---
 3 个 SPX 组
---
均为空
---
。现在让我
---
运行 `--reoptimize`
---
（
---
大约需要
---
 65 分钟）。
---
我将在后台运行它。
---
{"command": "PYTHONPATH=/Users/rickouyang/Github/trade-tools/mytrader NUMBA_DISABLE_CACHE=1 /Users/rickouyang/miniforge3/envs/py312trade/bin/python main.py --reoptimize 2>&1", "dangerouslyDisableSandbox": true, "description": "Run --reoptimize to regenerate strategy_weights.json", "run_in_background": true, "timeout": 600000}
---
Run --reoptimize to regenerate strategy_weights.json
---
Command: PYTHONPATH=/Users/rickouyang/Github/trade-tools/mytrader NUMBA_DISABLE_CACHE=1 /Users/rickouyang/miniforge3/envs/py312trade/bin/python main.py --reoptimize 2>&1
Status: Running in background with task_id: da1zX9
Reason: Launched directly in background (run_in_background=true).
Next step: Use the TaskOutput tool with this task_id to poll progress or fetch the completed output.
Current Output (partial): (no output yet)
---
The
---
 reoptimize
---
 is running in the background.
---
 While
---
 it runs
---
 (~
---
65
---
 minutes), I can
---
 work
---
 on the documentation
---
 updates
---
 (trajectory +
---
 CODEBUDDY). Let
---
 me update those
---
 now
---
, and I'll be notified
---
 when the re
---
optimize completes.


---
Let me start
---
 with the iteration
---
_trajectory
---
.md update
---
. I'll follow
---
 the L
---
9
---
 format from Iter
---
 #16
---
.

But
---
 first
---
, let me also
---
 create
---
 the spec
---
 file
---
 for iteration
---
_17 since
---
 it
---
 doesn't exist, and the
---
 test
---
 file references it
---
. Actually, the spec file
---
 is
---
 referenced in the test doc
---
string: "背景
---
见
---
 `iterations
---
/iteration
---
_17/spec
---
.md`". Let me create
---
 it for
---
 consistency
---
.

Actually, the user
---
 said
---
 "按
---
 iterations/iteration
---
_17/spec
---
.md 进行
---
开发
---
" — implying
---
 the spec should
---
 exist
---
. Since
---
 it doesn't,
---
 I should create it to
---
 document the
---
 iteration. But
---
 the user's
---
 main focus
---
 is the implementation
---
,
---
 not the spec.
---
 Let me create a
---
 minimal
---
 spec for documentation
---
 consistency
---
.

Actually
---
, let me focus
---
 on the core
---
 deliver
---
ables first:
---
 trajectory
---
 + CODEBUDDY.
---
 The spec
---
 can
---
 be created after
---
.
---
 Let me work
---
 on the trajectory
---
 while the reoptimize runs
---
.

Let me read
---
 the end
---
 of the
---
 trajectory file
---
 to know
---
 where to append.
---
重新
---
优化正在
---
后台运行。在它
---
运行的同时
---
（约 65 分钟），
---
让我
---
来处理
---
文档更新
---
。首先
---
，让我读取
---
轨迹
---
文件的末尾。
---
{"command": "wc -l /Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md", "description": "Get trajectory file line count"}
---
Get trajectory file line count
---
Command: wc -l /Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md
Stdout:     1667 /Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"file_path": "/Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md", "limit": 40, "offset": 1630}
---
1630→✅ Sanity Gate / Reject Degenerate (迭代 #11)
1631→✅ Alpha Gate (迭代 #12 引入, 迭代 #16 放宽至 -2%)
1632→✅ WF Gate Alpha Validation (迭代 #13)
1633→✅ Iter #16 reoptimize 完成 (2/6 组有权重, -2% gate 解锁 2 策略)
1634→⬜ Paper Trade ≥1月 | ⬜ Live
1635→```
1636→
1637→---
1638→
1639→> **Orchestrator 验证记录** (自动追加)
1640→> - 迭代状态: passed
1641→> - 测试: 707 passed, 0 failed
1642→> - 违规: 0 条
1643→> - 高风险文件: 0 个
1644→> - 测试数变化: 675 → 707
1645→> - CodeBuddy 自行更新了 trajectory ✅
1646→
1647→---
1648→
1649→> **Orchestrator 验证记录** (自动追加)
1650→> - 迭代状态: passed
1651→> - 测试: 0 passed, 0 failed
1652→> - 违规: 0 条
1653→> - 高风险文件: 0 个
1654→> - 测试数变化: 675 → 707
1655→> - CodeBuddy 自行更新了 trajectory ✅
1656→
1657→---
1658→
1659→> **Orchestrator 验证记录** (自动追加)
1660→> - 迭代状态: passed
1661→> - 测试: 0 passed, 0 failed
1662→> - 违规: 0 条
1663→> - 高风险文件: 0 个
1664→> - 测试数变化: 737 → 744
1665→> - CodeBuddy 自行更新了 trajectory ✅
1666→
1667→---
1668→
---
1630→✅ Sanity Gate / Reject Degenerate (迭代 #11)
1631→✅ Alpha Gate (迭代 #12 引入, 迭代 #16 放宽至 -2%)
1632→✅ WF Gate Alpha Validation (迭代 #13)
1633→✅ Iter #16 reoptimize 完成 (2/6 组有权重, -2% gate 解锁 2 策略)
1634→⬜ Paper Trade ≥1月 | ⬜ Live
1635→```
1636→
1637→---
1638→
1639→> **Orchestrator 验证记录** (自动追加)
1640→> - 迭代状态: passed
1641→> - 测试: 707 passed, 0 failed
1642→> - 违规: 0 条
1643→> - 高风险文件: 0 个
1644→> - 测试数变化: 675 → 707
1645→> - CodeBuddy 自行更新了 trajectory ✅
1646→
1647→---
1648→
1649→> **Orchestrator 验证记录** (自动追加)
1650→> - 迭代状态: passed
1651→> - 测试: 0 passed, 0 failed
1652→> - 违规: 0 条
1653→> - 高风险文件: 0 个
1654→> - 测试数变化: 675 → 707
1655→> - CodeBuddy 自行更新了 trajectory ✅
1656→
1657→---
1658→
1659→> **Orchestrator 验证记录** (自动追加)
1660→> - 迭代状态: passed
1661→> - 测试: 0 passed, 0 failed
1662→> - 违规: 0 条
1663→> - 高风险文件: 0 个
1664→> - 测试数变化: 737 → 744
1665→> - CodeBuddy 自行更新了 trajectory ✅
1666→
1667→---
1668→
---
Now
---
 let
---
 me also
---
 create
---
 the spec file for iteration
---
_17
---
 (
---
refer
---
enced in the test doc
---
string
---
),
---
 and then update the trajectory
---
. Let
---
 me first
---
 create
---
 the spec file
---
.
---
让我
---
先创建 Iter
---
ation 17 的 spec 文
---
件（在
---
测试 doc
---
string 中引用），然后
---
更新
---
 trajectory
---
。
---
{"command": "ls /Users/rickouyang/Github/trade-tools/mytrader/iterations/", "description": "Check iterations directory"}
---
Check iterations directory
---
Command: ls /Users/rickouyang/Github/trade-tools/mytrader/iterations/
Stdout: iteration_8

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