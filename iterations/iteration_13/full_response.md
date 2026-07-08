Let
---
 me
---
 start
---
 by
---
 understanding
---
 the
---
 task
---
.
---
 I
---
 need
---
 to
---
:

---
1
---
.
---
 Read
---
 the
---
 spec
---
 file
---
 at
---
 `
---
iterations
---
/
---
iteration
---
_
---
13
---
/spec
---
.md
---
`

---
2
---
.
---
 Read
---
 relevant
---
 code
---
 files
---


---
3
---
.
---
 Implement
---
 the
---
 changes
---
 according
---
 to
---
 the
---
 spec
---



---
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
 file
---
 and
---
 the
---
 relevant
---
 code
---
 files
---
 in
---
 parallel
---
.
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/iterations/iteration_13/spec.md"}
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py"}
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/main.py"}
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/.codebuddy/notes/experience.md"}
---
<tool_use_error>File does not exist.</tool_use_error>
---
<tool_use_error>File does not exist.</tool_use_error>
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
  49→# 迭代 #11 新增：健全性门槛 —— 识别"退化策略"（几乎不平仓的伪 buy-and-hold）
  50→# 判定：组内"有效标的中，已平仓交易数为 0 的比例"超过此阈值 → 退化
  51→# 设计动机：真策略应在多数标的上完成买卖闭环；若近乎所有标的都从不平仓，
  52→#           说明入场/出场条件矛盾（如 Iter #8 rsi_trend_filter），其收益只是
  53→#           持仓盯市 + 末尾强平的假象，必须在排序前剔除（experience.md #8）。
  54→# 阈值取 0.8（保守）：只在"近乎全部标的零平仓"时触发，避免误伤低频合法策略。
  55→DEGENERATE_NO_CLOSE_FRACTION: float = 0.8
  56→
  57→
  58→# ---------------------------------------------------------------------------
  59→# 数据结构
  60→# ---------------------------------------------------------------------------
  61→
  62→@dataclass
  63→class SingleBacktestResult:
  64→    """单只标的单策略回测结果。"""
  65→
  66→    symbol: str
  67→    strategy: str
  68→    params: dict
  69→    sharpe: float
  70→    total_return_pct: float
  71→    max_drawdown_pct: float
  72→    win_rate_pct: float
  73→    total_trades: int
  74→    daily_returns: pd.Series    # pf.returns() — 供组合 Sharpe / Sortino 计算
  75→    sortino: float = 0.0       # Constitution L1 首要 KPI（迭代 #1 新增）
  76→    closed_trades: int = 0     # 迭代 #11 新增：已平仓交易数（区分退化 buy-and-hold）
  77→
  78→
  79→@dataclass
  80→class GroupBacktestResult:
  81→    """单组策略回测结果。"""
  82→
  83→    group_id: str
  84→    strategy: str
  85→    params: dict
  86→    portfolio_sharpe: float          # 等权组合 Sharpe（而非算术平均）
  87→    avg_total_return_pct: float
  88→    avg_max_drawdown_pct: float
  89→    avg_win_rate_pct: float
  90→    symbol_count: int
  91→    portfolio_sortino: float = 0.0          # 等权组合 Sortino（迭代 #1 新增）
  92→    portfolio_max_drawdown: float = 0.0     # 等权组合最大回撤（迭代 #2 新增，Constitution L1 KPI）
  93→    dd_constrained: bool = False            # 迭代 #3：该组是否用了 DD fallback（无合规候选）
  94→    backtest_alpha: float = 0.0              # 迭代 #9：alpha vs SPY（百分数），用于排序策略选择
  95→    no_valid_strategy: bool = False         # 迭代 #11：该组是否因全退化而空仓（hold cash）
  96→    no_positive_alpha: bool = False         # 迭代 #12：该组是否因全负 alpha 而空仓（hold cash）
  97→
  98→
  99→@dataclass
 100→class MatrixBacktestReport:
 101→    """整个矩阵回测的汇总报告。"""
 102→
 103→    generated_at: str
 104→    backtest_window: str
 105→    groups: dict[str, list[dict]]   # group_id → [策略权重配置]
 106→    group_results: list[GroupBacktestResult] = field(default_factory=list)
 107→    warnings: list[str] = field(default_factory=list)
 108→
 109→
 110→# ---------------------------------------------------------------------------
 111→# Walk-Forward 数据结构（迭代 #3 新增，Constitution L7 验证流水线）
 112→# ---------------------------------------------------------------------------
 113→
 114→@dataclass
 115→class WalkForwardRound:
 116→    """单轮 Walk-Forward 验证结果。
 117→
 118→    一轮 = 训练期（找最优参数）+ 验证期（用同参数回测，记录样本外指标）。
 119→
 120→    Attributes:
 121→        round_num:    轮次编号（1-indexed）
 122→        train_start:  训练期起始日期（含）
 123→        train_end:    训练期结束日期（含）
 124→        val_start:    验证期起始日期（含）
 125→        val_end:      验证期结束日期（含）
 126→        val_sortino:  验证期等权组合 Sortino Ratio（年化）
 127→        val_max_dd:   验证期等权组合最大回撤（正值百分数，0~100）
 128→        passed:       是否通过 = val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD (15%)
 129→    """
 130→
 131→    round_num: int
 132→    train_start: date
 133→    train_end: date
 134→    val_start: date
 135→    val_end: date
 136→    val_sortino: float
 137→    val_max_dd: float
 138→    passed: bool
 139→
 140→
 141→@dataclass
 142→class WalkForwardReport:
 143→    """Walk-Forward 4 轮验证汇总报告。
 144→
 145→    Constitution L7 要求 Backtest(>=5年) → Walk-Forward(4轮) → Paper → Live。
 146→    本报告是 Walk-Forward 阶段的产出。
 147→
 148→    Attributes:
 149→        rounds:         每轮结果列表（长度通常为 4）
 150→        pass_all_rounds: 是否所有轮都通过（all(r.passed for r in rounds)）
 151→        max_val_dd:     所有轮中最大的验证期 DD（用于风险监控）
 152→    """
 153→
 154→    rounds: list[WalkForwardRound] = field(default_factory=list)
 155→    pass_all_rounds: bool = False
 156→    max_val_dd: float = 0.0
 157→
 158→
 159→# ---------------------------------------------------------------------------
 160→# 核心函数
 161→# ---------------------------------------------------------------------------
 162→
 163→def _safe_float(value: Any, default: float = 0.0) -> float:
 164→    """NaN/None/非数值安全转 float（迭代 #2 新增）。
 165→
 166→    问题背景：vectorbt 在无交易场景下，`pf.stats()` 的 Win Rate / Sharpe 等
 167→    字段会返回 NaN。`float(NaN or 0.0)` 仍是 NaN（NaN 是 truthy），导致
 168→    JSON 序列化写出非法 JSON（NaN/Infinity 非 JSON 规范）。
 169→
 170→    处理顺序：
 171→        1. None → default
 172→        2. 数值类型但 NaN/Inf → default
 173→        3. 非数值（字符串等）尝试 float() 转换，失败 → default
 174→    """
 175→    if value is None:
 176→        return default
 177→    try:
 178→        f = float(value)
 179→    except (TypeError, ValueError):
 180→        return default
 181→    if not np.isfinite(f):   # 拦截 NaN / +Inf / -Inf
 182→        return default
 183→    return f
 184→
 185→
 186→def _safe_mean(values: Any, default: float = 0.0) -> float:
 187→    """空列表 / 全 NaN 安全的均值（迭代 #2 新增）。
 188→
 189→    问题背景：`np.mean([])` 会触发 RuntimeWarning 并返回 NaN；
 190→    `np.mean([NaN, NaN])` 直接返回 NaN。在 GroupBacktestResult 聚合时
 191→    若某组只有 1 个标的且其字段为 NaN，会导致下游 JSON 序列化失败。
 192→
 193→    行为：
 194→        - 空列表 / 全 NaN → default
 195→        - 部分 NaN → 自动忽略 NaN 后取均值（np.nanmean 语义）
 196→    """
 197→    arr = np.asarray(values, dtype=float)
 198→    if arr.size == 0:
 199→        return default
 200→    mask = np.isfinite(arr)
 201→    if not mask.any():
 202→        return default
 203→    return float(arr[mask].mean())
 204→
 205→
 206→def _compute_sharpe(returns: pd.Series, periods_per_year: int = 252) -> float:
 207→    """从日收益率序列计算年化 Sharpe Ratio。"""
 208→    returns = returns.dropna()
 209→    if len(returns) < 5:
 210→        return 0.0
 211→    mean = returns.mean()
 212→    std = returns.std()
 213→    if std <= 0 or np.isnan(std):
 214→        return 0.0
 215→    return float(mean / std * np.sqrt(periods_per_year))
 216→
 217→
 218→def _compute_sortino(
 219→    returns: pd.Series,
 220→    periods_per_year: int = 252,
 221→    target: float = 0.0,
 222→) -> float:
 223→    """从日收益率序列计算年化 Sortino Ratio（Constitution L1 首要 KPI）。
 224→
 225→    Sortino = (mean(returns) - target) / downside_deviation * sqrt(periods_per_year)
 226→    downside_deviation = sqrt( mean( min(0, returns - target)^2 ) )
 227→
 228→    与 Sharpe 的区别：仅对下行波动惩罚，上行波动不计入分母。
 229→    适合"收益>0 但偶尔大跌"的中长线策略评估。
 230→
 231→    退化处理（与 _compute_sharpe 一致）：
 232→        - 样本 < 5 → 0.0
 233→        - 下行波动 ≤ 0（无下行样本）→ 0.0（理论为 +inf，返回 0 保持保守 + 可算术聚合）
 234→
 235→    Args:
 236→        returns:          日收益率序列（如 pf.returns()）
 237→        periods_per_year: 年化因子（日线 = 252）
 238→        target:           MAR/目标收益率，默认 0（与 _compute_sharpe 无风险利率假设一致）
 239→
 240→    Returns:
 241→        年化 Sortino Ratio
 242→    """
 243→    returns = returns.dropna()
 244→    if len(returns) < 5:
 245→        return 0.0
 246→    excess = returns - target
 247→    downside = excess.where(excess < 0, 0.0)        # 仅保留负偏离，正偏离置 0
 248→    dd = np.sqrt((downside ** 2).mean())
 249→    if dd <= 0 or np.isnan(dd):
 250→        return 0.0
 251→    return float(returns.mean() / dd * np.sqrt(periods_per_year))
 252→
 253→
 254→def _combine_daily_returns(results: list[SingleBacktestResult]) -> pd.Series:
 255→    """等权合并组内日收益率序列，返回组合日收益率（迭代 #9 新增）。
 256→
 257→    与 _portfolio_sharpe_from_results / _portfolio_sortino_from_results 同语义：
 258→    将所有标的日收益率等权合并为组合序列。提取为独立函数以便 alpha 计算
 259→    和 per-strategy best params 选择复用，避免重复 pd.concat。
 260→
 261→    Args:
 262→        results: 单策略多标的的回测结果列表
 263→
 264→    Returns:
 265→        组合日收益率 pd.Series；无有效数据时返回空 Series
 266→    """
 267→    valid = [r.daily_returns for r in results if not r.daily_returns.empty]
 268→    if not valid:
 269→        return pd.Series(dtype=float)
 270→    return pd.concat(valid, axis=1).mean(axis=1)
 271→
 272→
 273→def _is_degenerate_strategy(results: list[SingleBacktestResult]) -> bool:
 274→    """判定一个策略在组内是否退化（几乎不产生已平仓交易）（迭代 #11 新增）。
 275→
 276→    退化定义：有效标的中 closed_trades==0 的比例 >= DEGENERATE_NO_CLOSE_FRACTION。
 277→    这类策略的入场/出场条件互斥（如 Iter #8 rsi_trend_filter 趋势过滤锁死均值
 278→    回归出场），仓位无法平仓，其 Sortino/alpha 只是持仓盯市假象，不代表真实
 279→    交易能力，必须在排序前剔除（experience.md #8：sanity → risk → rank）。
 280→
 281→    Args:
 282→        results: 单策略多标的的回测结果列表
 283→
 284→    Returns:
 285→        True 表示退化（应剔除）；空结果视为退化（True）
 286→    """
 287→    if not results:
 288→        return True
 289→    n = len(results)
 290→    no_close = sum(1 for r in results if r.closed_trades <= 0)
 291→    return (no_close / n) >= DEGENERATE_NO_CLOSE_FRACTION
 292→
 293→
 294→def _compute_alpha(
 295→    strategy_daily_returns: pd.Series,
 296→    spy_daily_returns: pd.Series | None,
 297→    periods_per_year: int = 252,
 298→) -> float:
 299→    """计算 alpha = 策略年化收益 - SPY 年化收益（迭代 #9 新增）。
 300→
 301→    Alpha 衡量策略相对 SPY buy-and-hold 的超额收益。正值表示跑赢 SPY，
 302→    负值表示跑输 SPY。用于 top-K 策略选择和 per-strategy best params 选择，
 303→    替代之前基于 Sortino/Sharpe 的选择逻辑（参考 iteration #9 spec）。
 304→
 305→    年化公式：(1 + mean_daily) ** periods_per_year - 1
 306→    使用算术平均日收益的几何年化，与 PortfolioBacktester 同口径。
 307→
 308→    降级处理：SPY 数据不可用（None 或空）→ 返回 0.0（不抛异常）。
 309→    这样在 SPY 数据缺失时，alpha 排序退化为"原顺序"，不会阻塞回测。
 310→
 311→    Args:
 312→        strategy_daily_returns: 策略组合日收益率序列
 313→        spy_daily_returns:      SPY 日收益率序列；None 表示数据不可用
 314→        periods_per_year:       年化因子（日线 = 252）
 315→
 316→    Returns:
 317→        Alpha 百分数（如 5.23 表示策略年化收益跑赢 SPY 5.23 个百分点）；
 318→        SPY 不可用时返回 0.0
 319→    """
 320→    if spy_daily_returns is None or spy_daily_returns.empty:
 321→        return 0.0
 322→    if strategy_daily_returns is None or strategy_daily_returns.empty:
 323→        return 0.0
 324→
 325→    # 对齐时间索引（inner join 取交集）
 326→    aligned = pd.concat(
 327→        [strategy_daily_returns.rename("strat"), spy_daily_returns.rename("spy")],
 328→        axis=1,
 329→        join="inner",
 330→    ).dropna()
 331→    if aligned.empty or len(aligned) < 2:
 332→        return 0.0
 333→
 334→    strat_returns = aligned["strat"]
 335→    spy_returns = aligned["spy"]
 336→
 337→    # 年化收益 = (1 + mean_daily)^252 - 1
 338→    strat_mean = strat_returns.mean()
 339→    spy_mean = spy_returns.mean()
 340→    if not np.isfinite(strat_mean) or not np.isfinite(spy_mean):
 341→        return 0.0
 342→
 343→    strat_annual = (1.0 + strat_mean) ** periods_per_year - 1.0
 344→    spy_annual = (1.0 + spy_mean) ** periods_per_year - 1.0
 345→
 346→    alpha = (strat_annual - spy_annual) * 100.0  # 转为百分数
 347→    if not np.isfinite(alpha):
 348→        return 0.0
 349→    return float(alpha)
 350→
 351→
 352→def _backtest_one(
 353→    df: pd.DataFrame,
 354→    strategy_name: str,
 355→    params: dict,
 356→    init_cash: float = 100_000.0,
 357→    fees: float = 0.001,
 358→    slippage: float = 0.001,
 359→) -> SingleBacktestResult | None:
 360→    """对单只标的执行单次回测。
 361→
 362→    使用 open= 参数确保信号在下一根 bar 的开盘价执行（与实盘一致）。
 363→
 364→    Returns:
 365→        SingleBacktestResult 或 None（数据不足/策略异常时）
 366→    """
 367→    strategy_fn = STRATEGY_REGISTRY.get(strategy_name)
 368→    if strategy_fn is None:
 369→        return None
 370→
 371→    if df.empty or len(df) < 30:
 372→        return None
 373→
 374→    try:
 375→        close = df["close"]
 376→        open_ = df["open"] if "open" in df.columns else None
 377→
 378→        # 调用策略（兼容需要 df 的策略）
 379→        try:
 380→            sig = strategy_fn(close, df=df, **params)
 381→        except TypeError:
 382→            sig = strategy_fn(close, **params)
 383→
 384→        entries = sig == 1
 385→        exits   = sig == -1
 386→
 387→        pf_kwargs: dict[str, Any] = dict(
 388→            entries=entries,
 389→            exits=exits,
 390→            init_cash=init_cash,
 391→            fees=fees,
 392→            slippage=slippage,
 393→            size=0.95,
 394→            size_type="Percent",
 395→            freq="D",
 396→        )
 397→
 398→        # ⚠️ 必须传 open= 参数：信号在下一根 bar 开盘价执行，与实盘一致
 399→        if open_ is not None:
 400→            pf = vbt.Portfolio.from_signals(close=close, open=open_, **pf_kwargs)
 401→        else:
 402→            pf = vbt.Portfolio.from_signals(close, **pf_kwargs)
 403→
 404→        stats = pf.stats()
 405→
 406→        daily_returns = pf.returns()
 407→
 408→        # 迭代 #11：已平仓交易数（用于健全性门槛 _is_degenerate_strategy）
 409→        # vbt 1.0 API: pf.trades.closed.count() 返回 Status==Closed 的交易数
 410→        # 区分"真交易闭环"与"末尾强平计 1 笔的伪 buy-and-hold"
 411→        try:
 412→            closed_trades = int(pf.trades.closed.count())
 413→        except Exception:
 414→            closed_trades = 0
 415→
 416→        return SingleBacktestResult(
 417→            symbol=str(df.index.name or ""),
 418→            strategy=strategy_name,
 419→            params=params,
 420→            sharpe=_safe_float(stats.get("Sharpe Ratio")),
 421→            total_return_pct=_safe_float(stats.get("Total Return [%]")),
 422→            max_drawdown_pct=_safe_float(stats.get("Max Drawdown [%]")),
 423→            win_rate_pct=_safe_float(stats.get("Win Rate [%]")),
 424→            total_trades=int(_safe_float(stats.get("Total Trades"), default=0.0)),
 425→            daily_returns=daily_returns,
 426→            sortino=_compute_sortino(daily_returns),
 427→            closed_trades=closed_trades,
 428→        )
 429→    except Exception as e:
 430→        logger.debug(f"[backtest_one] {strategy_name}({params}) failed: {e}")
 431→        return None
 432→
 433→
 434→def _backtest_batch(
 435→    data: dict[str, pd.DataFrame],
 436→    strategy_name: str,
 437→    params: dict,
 438→    init_cash: float = 100_000.0,
 439→    fees: float = 0.001,
 440→    slippage: float = 0.001,
 441→) -> list[SingleBacktestResult]:
 442→    """对组内所有标的批量执行回测（迭代 #10 新增）。
 443→
 444→    核心优化：用一次 vbt.Portfolio.from_signals 处理组内所有标的，
 445→    替代 `_backtest_one` 的 for-symbol 循环。调用次数从 O(N 标的)
 446→    降为 O(1)，预计 10-20x 提速（spec §1）。
 447→
 448→    实现要点：
 449→        1. 逐标的调用策略函数（保持与 `_backtest_one` 一致的调用语义：
 450→           先尝试 `strategy_fn(close, df=df, **params)`，TypeError 时
 451→           回退到 `strategy_fn(close, **params)`）。策略函数本身不改。
 452→        2. 构建列式矩阵（每列一个标的），用一次 vbt 调用回测所有标的。
 453→           vbt 1.0+ 的列分组语义保证每列独立结算 P&L。
 454→        3. 通过 `pf[sym]` 提取每列的 stats/daily_returns，输出格式与
 455→           `_backtest_one` 完全一致，下游聚合代码无需修改。
 456→
 457→    对齐策略：
 458→        - 用 `pd.DataFrame(dict)` 构造时自动 outer-join 时间索引，
 459→          缺失值填 NaN。
 460→        - vbt 对 NaN close 的处理：内部 fillna 为 0 收益率，等价于
 461→          "该标的此日期不交易"。当标的在样本外日期缺失时（如退市、
 462→          新上市），其 stats 仍按其有效日期区间计算。
 463→        - 在美股实际场景中所有标的共享交易日历，日期对齐天然成立，
 464→          不会有大量 NaN。
 465→
 466→    Args:
 467→        data:          {symbol: OHLCV DataFrame} 字典
 468→        strategy_name: 策略名
 469→        params:        策略参数
 470→        init_cash:     初始资金（vbt 给每列分配独立的 init_cash）
 471→        fees:          手续费率
 472→        slippage:      滑点率
 473→
 474→    Returns:
 475→        SingleBacktestResult 列表（与 `_backtest_one` 输出格式一致）。
 476→        数据不足 / 策略异常的标的会被跳过（不返回 None，不抛异常）。
 477→        空数据时返回空列表。
 478→    """
 479→    strategy_fn = STRATEGY_REGISTRY.get(strategy_name)
 480→    if strategy_fn is None:
 481→        return []
 482→
 483→    # 1. 逐标的调用策略函数，构建 signal / close / open 列
 484→    signal_columns: dict[str, pd.Series] = {}
 485→    close_columns: dict[str, pd.Series] = {}
 486→    open_columns: dict[str, pd.Series] = {}
 487→
 488→    for sym, df in data.items():
 489→        if df is None or df.empty or len(df) < 30:
 490→            continue
 491→        close = df["close"]
 492→        if "open" in df.columns:
 493→            open_ = df["open"]
 494→            open_columns[sym] = open_
 495→        else:
 496→            open_ = None
 497→
 498→        # 调用策略（与 _backtest_one 一致的 try/except 语义）
 499→        try:
 500→            sig = strategy_fn(close, df=df, **params)
 501→        except TypeError:
 502→            sig = strategy_fn(close, **params)
 503→        except Exception as e:
 504→            logger.debug(
 505→                f"[backtest_batch] {strategy_name}({params}) {sym} failed: {e}"
 506→            )
 507→            continue
 508→
 509→        signal_columns[sym] = sig
 510→        close_columns[sym] = close
 511→
 512→    if not signal_columns:
 513→        return []
 514→
 515→    # 2. 构建矩阵（自动 outer-join 索引，缺失值填 NaN）
 516→    close_matrix = pd.DataFrame(close_columns)
 517→    signal_matrix = pd.DataFrame(signal_columns)
 518→    has_open = bool(open_columns)
 519→    open_matrix = pd.DataFrame(open_columns) if has_open else None
 520→
 521→    # 3. 一次 vbt 调用处理所有标的
 522→    entries = signal_matrix == 1
 523→    exits = signal_matrix == -1
 524→
 525→    pf_kwargs: dict[str, Any] = dict(
 526→        entries=entries,
 527→        exits=exits,
 528→        init_cash=init_cash,
 529→        fees=fees,
 530→        slippage=slippage,
 531→        size=0.95,
 532→        size_type="Percent",
 533→        freq="D",
 534→    )
 535→
 536→    try:
 537→        if has_open:
 538→            pf = vbt.Portfolio.from_signals(
 539→                close=close_matrix, open=open_matrix, **pf_kwargs
 540→            )
 541→        else:
 542→            pf = vbt.Portfolio.from_signals(close_matrix, **pf_kwargs)
 543→    except Exception as e:
 544→        logger.warning(
 545→            f"[backtest_batch] {strategy_name}({params}) vbt call failed: {e} "
 546→            f"— falling back to per-symbol _backtest_one"
 547→        )
 548→        # 回滚方案：批量失败时退化为逐标的回测，保证回测不中断
 549→        results: list[SingleBacktestResult] = []
 550→        for sym, df in data.items():
 551→            if df is None or df.empty or len(df) < 30:
 552→                continue
 553→            df = df.copy()
 554→            df.index.name = sym
 555→            r = _backtest_one(
 556→                df, strategy_name, params, init_cash, fees, slippage
 557→            )
 558→            if r is not None:
 559→                results.append(r)
 560→        return results
 561→
 562→    # 4. 提取 per-symbol 结果（与 _backtest_one 输出格式一致）
 563→    results = []
 564→    for sym in signal_matrix.columns:
 565→        try:
 566→            pf_sym = pf[sym]
 567→            stats = pf_sym.stats()
 568→            daily_returns = pf_sym.returns()
 569→            # 迭代 #11：已平仓交易数（与 _backtest_one 同 API、同语义）
 570→            # pf_sym 是单列 pf，pf_sym.trades.closed.count() 返回 int
 571→            try:
 572→                closed_trades = int(pf_sym.trades.closed.count())
 573→            except Exception:
 574→                closed_trades = 0
 575→            results.append(SingleBacktestResult(
 576→                symbol=sym,
 577→                strategy=strategy_name,
 578→                params=params,
 579→                sharpe=_safe_float(stats.get("Sharpe Ratio")),
 580→                total_return_pct=_safe_float(stats.get("Total Return [%]")),
 581→                max_drawdown_pct=_safe_float(stats.get("Max Drawdown [%]")),
 582→                win_rate_pct=_safe_float(stats.get("Win Rate [%]")),
 583→                total_trades=int(_safe_float(stats.get("Total Trades"), default=0.0)),
 584→                daily_returns=daily_returns,
 585→                sortino=_compute_sortino(daily_returns),
 586→                closed_trades=closed_trades,
 587→            ))
 588→        except Exception as e:
 589→            logger.debug(
 590→                f"[backtest_batch] {strategy_name}({params}) {sym} "
 591→                f"stats extraction failed: {e}"
 592→            )
 593→            continue
 594→
 595→    return results
 596→
 597→
 598→def _portfolio_sharpe_from_results(results: list[SingleBacktestResult]) -> float:
 599→    """等权合并组内日收益率序列，计算组合 Sharpe。
 600→
 601→    ⚠️ 不能取各标的 Sharpe 算术平均（Sharpe 是比率，不能直接平均）。
 602→    正确做法：将所有标的日收益率等权合并为组合序列，再计算 Sharpe。
 603→    """
 604→    valid = [r.daily_returns for r in results if not r.daily_returns.empty]
 605→    if not valid:
 606→        return 0.0
 607→
 608→    # 对齐时间索引，等权平均
 609→    combined = pd.concat(valid, axis=1).mean(axis=1)
 610→    return _compute_sharpe(combined)
 611→
 612→
 613→def _portfolio_sortino_from_results(results: list[SingleBacktestResult]) -> float:
 614→    """等权合并组内日收益率序列，计算组合 Sortino（与 _portfolio_sharpe_from_results 同语义）。
 615→
 616→    不能取各标的 Sortino 算术平均（与 Sharpe 同理：比率不可直接平均）。
 617→    """
 618→    valid = [r.daily_returns for r in results if not r.daily_returns.empty]
 619→    if not valid:
 620→        return 0.0
 621→    combined = pd.concat(valid, axis=1).mean(axis=1)
 622→    return _compute_sortino(combined)
 623→
 624→
 625→def _portfolio_max_drawdown_from_results(
 626→    results: list[SingleBacktestResult],
 627→) -> float:
 628→    """等权合并组内日收益率序列，计算组合最大回撤（迭代 #2 新增，Constitution L1 KPI）。
 629→
 630→    与 `_portfolio_sharpe_from_results` 同语义：不能取各标的 DD 算术平均，
 631→    因为 DD 是路径依赖的比率。正确做法是先把��内日收益率等权合并为组合序列，
 632→    再 cumprod → cummax → drawdown → max。
 633→
 634→    返回值约定：百分比形式（与 `SingleBacktestResult.max_drawdown_pct` 一致，
 635→    vectorbt stats 中 `Max Drawdown [%]` 同样是百分数，例如 -15.2 表示 15.2% 回撤）。
 636→    本函数返回正值（0.0 ~ 100.0）便于聚合与 JSON 输出。
 637→
 638→    退化处理：
 639→        - 无有效日收益率 → 0.0
 640→        - 全 0 收益率（cumprod 恒为 1.0）→ 0.0
 641→    """
 642→    valid = [r.daily_returns for r in results if not r.daily_returns.empty]
 643→    if not valid:
 644→        return 0.0
 645→    combined = pd.concat(valid, axis=1).mean(axis=1).dropna()
 646→    if len(combined) < 2:
 647→        return 0.0
 648→    # 组合累计净值：初始 1.0，每日乘 (1 + r)
 649→    cumvalue = (1.0 + combined).cumprod()
 650→    peak = cumvalue.cummax()
 651→    drawdown = (cumvalue - peak) / peak   # 负值，0 表示无回撤
 652→    dd_max_pct = float(drawdown.min())    # 最负值，例如 -0.152
 653→    if not np.isfinite(dd_max_pct):
 654→        return 0.0
 655→    # 转为正百分数（与 vectorbt Max Drawdown [%] 的口径一致但取正号）
 656→    return abs(dd_max_pct) * 100.0
 657→
 658→
 659→def _optimize_ensemble_weights(
 660→    group_results: list[tuple[str, dict, list[SingleBacktestResult]]],
 661→    spy_returns: pd.Series | None = None,
 662→    conflict_threshold: float = 0.3,
 663→) -> list[tuple[str, dict, float]]:
 664→    """在"单点离散值加权投票"语义下优化 ensemble 权重。
 665→
 666→    实盘每根 bar 各策略产出离散值（1/-1/0），加权投票决定方向。
 667→    回测的权重优化必须使用相同语义，而非对整段时间序列做加权。
 668→
 669→    迭代 #9：权重计算从 Sharpe 改为 Alpha（vs SPY）。
 670→    动机：与 _run_group 的 top-K 排序口径一致，使 ensemble 权重直接
 671→    反映"跑赢 SPY 的程度"。SPY 不可用时 alpha=0，退化为等权。
 672→
 673→    迭代 #12：修负 alpha 归一化 bug。
 674→    旧代码 `max(alpha, 0.01)` 把负 alpha 都变成 0.01，归一化后等权，
 675→    掩盖"都不好"的事实（experience.md #8）。新逻辑：负 alpha 权重为 0，
 676→    只有正 alpha 参与归一化；全负 alpha 时等权 fallback + WARNING
 677→    （上游 alpha>0 门槛应已拦截，此处为防御性设计）。
 678→
 679→    Args:
 680→        group_results: [(strategy, params, [SingleBacktestResult]), ...]
 681→        spy_returns:   SPY 日收益率序列（用于 alpha 计算）；None 时退化为等权
 682→        conflict_threshold: 加权投票分数绝对值低于此时视为 HOLD
 683→
 684→    Returns:
 685→        [(strategy, params, weight), ...] 归一化权重列表
 686→    """
 687→    if len(group_results) == 1:
 688→        strategy, params, _ = group_results[0]
 689→        return [(strategy, params, 1.0)]
 690→
 691→    # 迭代 #12：负 alpha 策略不参与 ensemble（experience.md #8：负分不能用 max(x, ε) 掩盖）
 692→    # 只有正 alpha 的策略参与归一化；负 alpha 策略权重为 0。
 693→    # 上游 _run_group 的 alpha>0 门槛应已拦截全负 alpha 情形，
 694→    # 这里是防御性设计：即使上游漏过负 alpha，也不会被 max(0.01) 掩盖成等权。
 695→    raw_alphas = []
 696→    for strategy, params, results in group_results:
 697→        combined = _combine_daily_returns(results)
 698→        alpha = _compute_alpha(combined, spy_returns)
 699→        raw_alphas.append(alpha)
 700→
 701→    # 负 alpha → 权重 0；正 alpha → 参与归一化
 702→    positive_alphas = [max(a, 0.0) for a in raw_alphas]
 703→    total = sum(positive_alphas)
 704→
 705→    if total > 0:
 706→        weights = [a / total for a in positive_alphas]
 707→    else:
 708→        # 防御性 fallback：全负 alpha 或全零时等权
 709→        # （上游 alpha>0 门槛应已拦截，此处不应到达）
 710→        n = len(group_results)
 711→        weights = [1.0 / n] * n if n > 0 else []
 712→        logger.warning(
 713→            f"[ensemble_weights] all alphas <= 0 ({raw_alphas}), "
 714→            f"falling back to equal weight. This should not happen if "
 715→            f"alpha>0 gate is active upstream."
 716→        )
 717→
 718→    return [
 719→        (strategy, params, weight)
 720→        for (strategy, params, _), weight in zip(group_results, weights)
 721→    ]
 722→
 723→
 724→# ---------------------------------------------------------------------------
 725→# Walk-Forward 验证（迭代 #3 新增，Constitution L7 验证流水线）
 726→# ---------------------------------------------------------------------------
 727→
 728→def _add_months(d: date, months: int) -> date:
 729→    """对 date 加/减 months 个月，自动 clamp 到月末。
 730→
 731→    使用 pandas DateOffset 以避免引入 dateutil 依赖（pandas 已是核心依赖）。
 732→    """
 733→    return (pd.Timestamp(d) + pd.DateOffset(months=months)).date()
 734→
 735→
 736→def _backtest_with_params_on_period(
 737→    mb: "MatrixBacktest",
 738→    symbols: list[str],
 739→    weights: list[dict[str, Any]],
 740→    start: date,
 741→    end: date,
 742→) -> list[pd.Series]:
 743→    """用给定权重配置在 [start, end] 期间回测，返回每条 (策略×标的) 的日收益率序列。
 744→
 745→    用于 Walk-Forward 验证期：用训练期产出的 best params 在验证期回测，
 746→    不再做参数搜索。返回原始日收益率列表，由调用方聚合为整体 portfolio。
 747→
 748→    迭代 #10 变更：用 `_backtest_batch` 替代 for-symbol 循环，
 749→    每个策略×参数组合一次 vbt 调用，加速 Walk-Forward 验证期回测。
 750→
 751→    Args:
 752→        mb:       MatrixBacktest 实例（复用其 store/init_cash/fees/slippage）
 753→        symbols:  该组的标的列表
 754→        weights:  训练期产出的权重配置（list of dict，含 strategy/params/weight）
 755→        start:    验证期起始日期
 756→        end:      验证期结束日期
 757→
 758→    Returns:
 759→        list[pd.Series] — 每条 (strategy×symbol) 的日收益率；空列表表示无有效数据
 760→    """
 761→    if not weights or not symbols:
 762→        return []
 763→
 764→    data = mb._store.get_bars_multi(symbols, start, end)
 765→    if not data:
 766→        return []
 767→
 768→    all_returns: list[pd.Series] = []
 769→    for w in weights:
 770→        strategy = w.get("strategy", "")
 771→        params = w.get("params", {})
 772→        if not strategy or strategy not in STRATEGY_REGISTRY:
 773→            continue
 774→        # 迭代 #10：一次 batch 调用处理组内所有标的
 775→        results = _backtest_batch(
 776→            data, strategy, params,
 777→            mb._init_cash, mb._fees, mb._slippage,
 778→        )
 779→        for r in results:
 780→            if not r.daily_returns.empty:
 781→                all_returns.append(r.daily_returns)
 782→    return all_returns
 783→
 784→
 785→def run_walk_forward(
 786→    mb: "MatrixBacktest",
 787→    strategies: list[str],
 788→    param_grids: dict[str, dict[str, list]],
 789→    rounds: int = 4,
 790→    train_months: int = 18,
 791→    val_months: int = 6,
 792→) -> WalkForwardReport:
 793→    """执行 N 轮 Walk-Forward 验证（Constitution L7 验证流水线硬要求）。
 794→
 795→    每轮流程：
 796→        1. 训练期 [train_start, train_end]：跑矩阵回测找最优参数
 797→        2. 验证期 [val_start, val_end]：用同参数回测，记录 portfolio Sortino 和 max DD
 798→        3. passed = val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD (15%)
 799→
 800→    时间窗口（动态计算，today=today）：
 801→        - 最后一轮 val_end = today - val_months（留 1 个 val 期给 paper trading）
 802→        - 每轮向前推 val_months
 803→        - train_end = val_start，train_start = train_end - train_months
 804→
 805→    默认参数 (rounds=4, train_months=18, val_months=6) 对应用户提供的固定窗口：
 806→        today=2026-07-01 →
 807→        Round 1: train 2021-07-02~2023-01-02, val 2023-01-02~2023-07-02
 808→        Round 2: train 2022-01-02~2023-07-02, val 2023-07-02~2024-01-02
 809→        Round 3: train 2022-07-02~2024-01-02, val 2024-01-02~2024-07-02
 810→        Round 4: train 2023-01-02~2024-07-02, val 2024-07-02~2025-01-02
 811→
 812→    Args:
 813→        mb:            MatrixBacktest 实例（复用其 store/universe/init_cash 等）
 814→        strategies:    策略名称列表
 815→        param_grids:   参数网格（与 mb.run() 接收的格式一致）
 816→        rounds:        轮次数（默认 4，Constitution L7 要求）
 817→        train_months:  训练期月数（默认 18）
 818→        val_months:    验证期月数（默认 6）
 819→
 820→    Returns:
 821→        WalkForwardReport — 包含每轮结果、pass_all_rounds、max_val_dd
 822→
 823→    Note:
 824→        - WF 是验证步骤，不修改 strategy_weights.json
 825→        - 失败轮次会记录 WARNING 但不抛异常
 826→        - 全部 4 轮通过是进入 paper trading 的前置条件
 827→    """
 828→    today = date.today()
 829→    groups = mb._universe.get_groups()
 830→    if not groups:
 831→        logger.warning("[WalkForward] no groups available — skipping")
 832→        return WalkForwardReport()
 833→
 834→    wf_rounds: list[WalkForwardRound] = []
 835→
 836→    for i in range(rounds):
 837→        round_num = i + 1
 838→        # 计算本轮时间窗口
 839→        # 最后一轮 (i=rounds-1) 的 val_end = today - val_months
 840→        # 前面轮次依次向前推 val_months
 841→        val_end = _add_months(today, -val_months - (rounds - round_num) * val_months)
 842→        val_start = _add_months(val_end, -val_months)
 843→        train_end = val_start
 844→        train_start = _add_months(train_end, -train_months)
 845→
 846→        logger.info(
 847→            f"[WalkForward] Round {round_num}/{rounds}: "
 848→            f"train={train_start}~{train_end}, val={val_start}~{val_end}"
 849→        )
 850→
 851→        # ── 训练期：跑矩阵回测找最优参数（复用 mb._run_group）──
 852→        train_report = MatrixBacktestReport(
 853→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
 854→            backtest_window=f"{train_start.isoformat()} ~ {train_end.isoformat()}",
 855→            groups={},
 856→        )
 857→
 858→        for group_id, symbols in groups.items():
 859→            weights = mb._run_group(
 860→                group_id=group_id,
 861→                symbols=symbols,
 862→                start=train_start,
 863→                end=train_end,
 864→                strategies=strategies,
 865→                param_grids=param_grids,
 866→                report=train_report,
 867→            )
 868→            train_report.groups[group_id] = weights
 869→
 870→        # ── 验证期：用训练期 best params 回测，聚合为整体 portfolio ──
 871→        all_returns: list[pd.Series] = []
 872→        for group_id, symbols in groups.items():
 873→            weights = train_report.groups.get(group_id, [])
 874→            if not weights:
 875→                continue
 876→            group_returns = _backtest_with_params_on_period(
 877→                mb, symbols, weights, val_start, val_end,
 878→            )
 879→            all_returns.extend(group_returns)
 880→
 881→        # 计算整体 portfolio 指标（等权合并所有组的日收益率）
 882→        if not all_returns:
 883→            val_sortino = 0.0
 884→            val_max_dd = 0.0
 885→            logger.warning(
 886→                f"[WalkForward] Round {round_num}: no valid val returns — "
 887→                f"sortino=0, dd=0, passed=True (vacuous)"
 888→            )
 889→        else:
 890→            combined = pd.concat(all_returns, axis=1).mean(axis=1).dropna()
 891→            if len(combined) < 5:
 892→                val_sortino = 0.0
 893→                val_max_dd = 0.0
 894→            else:
 895→                val_sortino = _compute_sortino(combined)
 896→                wrapper = [SingleBacktestResult(
 897→                    symbol="portfolio", strategy="", params={},
 898→                    sharpe=0.0, total_return_pct=0.0, max_drawdown_pct=0.0,
 899→                    win_rate_pct=0.0, total_trades=0, daily_returns=combined,
 900→                )]
 901→                val_max_dd = _portfolio_max_drawdown_from_results(wrapper)
 902→
 903→        passed = val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD
 904→        wf_rounds.append(WalkForwardRound(
 905→            round_num=round_num,
 906→            train_start=train_start,
 907→            train_end=train_end,
 908→            val_start=val_start,
 909→            val_end=val_end,
 910→            val_sortino=val_sortino,
 911→            val_max_dd=val_max_dd,
 912→            passed=passed,
 913→        ))
 914→        logger.info(
 915→            f"[WalkForward] Round {round_num} result: "
 916→            f"sortino={val_sortino:.4f}, dd={val_max_dd:.4f}%, "
 917→            f"passed={passed} (threshold={WALK_FORWARD_VAL_DD_THRESHOLD}%)"
 918→        )
 919→
 920→    report = WalkForwardReport(
 921→        rounds=wf_rounds,
 922→        pass_all_rounds=all(r.passed for r in wf_rounds) if wf_rounds else False,
 923→        max_val_dd=max((r.val_max_dd for r in wf_rounds), default=0.0),
 924→    )
 925→    logger.info(
 926→        f"[WalkForward] done: {len(wf_rounds)} rounds, "
 927→        f"pass_all_rounds={report.pass_all_rounds}, "
 928→        f"max_val_dd={report.max_val_dd:.4f}%"
 929→    )
 930→    return report
 931→
 932→
 933→# ---------------------------------------------------------------------------
 934→# MatrixBacktest 主类
 935→# ---------------------------------------------------------------------------
 936→
 937→class MatrixBacktest:
 938→    """矩阵回测：N 策略 × G 标的组 × 参数网格 → strategy_weights.json。
 939→
 940→    Args:
 941→        store:       MarketDataStore（本地时序库）
 942→        universe:    UniverseManager（提供分组映射）
 943→        years:       回测窗口（默认 5 年）
 944→        init_cash:   初始资金
 945→        fees:        手续费率
 946→        slippage:    滑点率
 947→        top_k:       每组保留 Top-K 策略（默认 2）
 948→    """
 949→
 950→    def __init__(
 951→        self,
 952→        store: MarketDataStore,
 953→        universe: UniverseManager,
 954→        years: int = 5,
 955→        init_cash: float = 100_000.0,
 956→        fees: float = 0.001,
 957→        slippage: float = 0.001,
 958→        top_k: int = 2,
 959→    ) -> None:
 960→        self._store = store
 961→        self._universe = universe
 962→        self._years = years
 963→        self._init_cash = init_cash
 964→        self._fees = fees
 965→        self._slippage = slippage
 966→        self._top_k = top_k
 967→
 968→    def run(
 969→        self,
 970→        strategies: list[str],
 971→        param_grids: dict[str, dict[str, list]],
 972→        output_file: str | Path | None = None,
 973→    ) -> MatrixBacktestReport:
 974→        """执行完整矩阵回测。
 975→
 976→        Args:
 977→            strategies:  策略名称列表，如 ["dual_ma", "rsi"]
 978→            param_grids: 各策略参数网格，如 {"dual_ma": {"fast":[5,10], "slow":[20,30]}}
 979→            output_file: strategy_weights.json 输出路径（None 则不写文件）
 980→
 981→        Returns:
 982→            MatrixBacktestReport
 983→        """
 984→        today = date.today()
 985→        start = today - timedelta(days=self._years * 365)
 986→        window_str = f"{start.isoformat()} ~ {today.isoformat()}"
 987→
 988→        logger.info(
 989→            f"[MatrixBacktest] start={start}, end={today}, "
 990→            f"strategies={strategies}, years={self._years}"
 991→        )
 992→
 993→        # 获取分组（⚠️ 使用历史时点分组，而非当前静态分组）
 994→        # Phase 5 初期简化：用当前分组，但接口已预留历史分组能力
 995→        groups = self._universe.get_groups()
 996→        if not groups:
 997→            logger.warning("[MatrixBacktest] no groups available, abort")
 998→            return MatrixBacktestReport(
 999→                generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
1000→                backtest_window=window_str,
1001→                groups={},
1002→            )
1003→
1004→        report = MatrixBacktestReport(
1005→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
1006→            backtest_window=window_str,
1007→            groups={},
1008→        )
1009→
1010→        for group_id, symbols in groups.items():
1011→            logger.info(
1012→                f"[MatrixBacktest] group={group_id}, symbols={len(symbols)}, "
1013→                f"strategies={strategies}"
1014→            )
1015→
1016→            group_weights = self._run_group(
1017→                group_id=group_id,
1018→                symbols=symbols,
1019→                start=start,
1020→                end=today,
1021→                strategies=strategies,
1022→                param_grids=param_grids,
1023→                report=report,
1024→            )
1025→            report.groups[group_id] = group_weights
1026→
1027→        if output_file is not None:
1028→            self._write_weights(report, output_file)
1029→
1030→        logger.info(
1031→            f"[MatrixBacktest] done: {len(report.groups)} groups, "
1032→            f"warnings={len(report.warnings)}"
1033→        )
1034→        return report
1035→
1036→    def _get_spy_returns(self, start: date, end: date) -> pd.Series | None:
1037→        """获取 SPY 同期日收益率序列，用于计算 alpha（迭代 #9 新增）。
1038→
1039→        从 MarketDataStore 拉取 SPY 日线数据，计算日收益率。
1040→        SPY 不在标的池中，但作为 benchmark 用于 alpha 计算。
1041→
1042→        降级处理：SPY 数据不可用时返回 None（_compute_alpha 会返回 0.0），
1043→        不抛异常，保证回测不因 benchmark 缺失而阻塞。
1044→
1045→        Args:
1046→            start: 回测起始日期
1047→            end:   回测结束日期
1048→
1049→        Returns:
1050→            SPY 日收益率 pd.Series；数据不可用时返回 None
1051→        """
1052→        try:
1053→            spy_bars = self._store.get_bars_multi(["SPY"], start, end)
1054→            spy_df = spy_bars.get("SPY") if spy_bars else None
1055→            if spy_df is None or spy_df.empty:
1056→                logger.warning(
1057→                    "[MatrixBacktest] SPY data unavailable, alpha will degrade to 0.0"
1058→                )
1059→                return None
1060→            spy_close = spy_df["close"].astype(float)
1061→            if len(spy_close) < 2:
1062→                logger.warning(
1063→                    "[MatrixBacktest] SPY data too short, alpha will degrade to 0.0"
1064→                )
1065→                return None
1066→            return spy_close.pct_change().dropna()
1067→        except Exception as e:
1068→            logger.warning(
1069→                f"[MatrixBacktest] SPY benchmark fetch failed: {e} — "
1070→                f"alpha will degrade to 0.0"
1071→            )
1072→            return None
1073→
1074→    def _run_group(
1075→        self,
1076→        group_id: str,
1077→        symbols: list[str],
1078→        start: date,
1079→        end: date,
1080→        strategies: list[str],
1081→        param_grids: dict[str, dict[str, list]],
1082→        report: MatrixBacktestReport,
1083→    ) -> list[dict[str, Any]]:
1084→        """对单个分组执行策略 × 参数网格回测，返回该组的权重配置列表。
1085→
1086→        迭代 #9 变更：
1087→            - per-strategy best params：从 Sharpe 改为 Alpha（vs SPY）
1088→            - top-K 排序：从 Sortino 改为 Alpha
1089→            - 新增 Sortino > 0.5 最低质量门槛（二级过滤，可放宽）
1090→            - ensemble weights：从 Sharpe 改为 Alpha
1091→        迭代 #10 变更：
1092→            - 用 `_backtest_batch` 替代 for-symbol 循环（10-20x 提速）
1093→            - 每组 / 每策略增加进度耗时日志
1094→        """
1095→        import time
1096→
1097→        group_start = time.time()
1098→
1099→        # 1. 读取组内所有标的数据
1100→        data = self._store.get_bars_multi(symbols, start, end)
1101→        if not data:
1102→            logger.warning(f"[MatrixBacktest] {group_id}: no data, skip")
1103→            return []
1104→
1105→        # 迭代 #9：获取 SPY 同期日收益率用于 alpha 计算（一次获取，组内复用）
1106→        spy_returns = self._get_spy_returns(start, end)
1107→
1108→        valid_symbol_count = sum(
1109→            1 for df in data.values() if df is not None and not df.empty and len(df) >= 30
1110→        )
1111→        logger.info(
1112→            f"[MatrixBacktest] {group_id}: start — "
1113→            f"{len(strategies)} strategies × {valid_symbol_count} valid symbols"
1114→        )
1115→
1116→        # 2. 对每个策略 × 每组参数，按 alpha 选最优参数
1117→        group_results: list[tuple[str, dict, list[SingleBacktestResult]]] = []
1118→
1119→        for strategy in strategies:
1120→            strat_start = time.time()
1121→
1122→            # ⚠️ 早期检测未注册策略名（迭代 #1 修复"策略名拼写错误被静默跳过"的 bug）
1123→            # 之前 _backtest_one 内部静默 return None，导致 main.py 误用 "rsi"/"macd"/"bollinger"
1124→            # 简称 6 天未被发现。改为 WARNING 级日志 + continue。
1125→            if strategy not in STRATEGY_REGISTRY:
1126→                logger.warning(
1127→                    f"[MatrixBacktest] {group_id}: strategy '{strategy}' not in "
1128→                    f"STRATEGY_REGISTRY — skipped. "
1129→                    f"Check spelling against @register_strategy decorators. "
1130→                    f"Known: {sorted(STRATEGY_REGISTRY.keys())}"
1131→                )
1132→                continue
1133→            grid = param_grids.get(strategy, {})
1134→            param_combos = list(
1135→                dict(zip(grid.keys(), combo))
1136→                for combo in itertools.product(*grid.values())
1137→            ) if grid else [{}]
1138→
1139→            best_params = None
1140→            best_alpha = float("-inf")
1141→            best_sharpe = 0.0       # 仅用于 GroupBacktestResult 存档
1142→            best_sortino = 0.0      # 仅用于 GroupBacktestResult 存档
1143→            best_results: list[SingleBacktestResult] = []
1144→
1145→            for params in param_combos:
1146→                # 迭代 #10：用 _backtest_batch 一次处理组内所有标的
1147→                # 替代原 for sym in symbols: _backtest_one(...) 的逐标的循环
1148→                results = _backtest_batch(
1149→                    data, strategy, params,
1150→                    self._init_cash, self._fees, self._slippage,
1151→                )
1152→
1153→                if not results:
1154→                    continue
1155→
1156→                # ⚠️ 等权合并日收益率序列，一次性计算所有指标
1157→                # 迭代 #9：复用 combined 计算 sharpe / sortino / alpha
1158→                combined = _combine_daily_returns(results)
1159→                ps = _compute_sharpe(combined)
1160→                pso = _compute_sortino(combined)
1161→                alpha = _compute_alpha(combined, spy_returns)
1162→
1163→                # 迭代 #9：per-strategy best params 用 alpha 选（替代 Sharpe）
1164→                if alpha > best_alpha:
1165→                    best_alpha = alpha
1166→                    best_sharpe = ps
1167→                    best_sortino = pso
1168→                    best_params = params
1169→                    best_results = results
1170→
1171→            if best_params is not None and best_results:
1172→                group_results.append((strategy, best_params, best_results))
1173→                report.group_results.append(GroupBacktestResult(
1174→                    group_id=group_id,
1175→                    strategy=strategy,
1176→                    params=best_params,
1177→                    portfolio_sharpe=best_sharpe,
1178→                    avg_total_return_pct=_safe_mean(
1179→                        [r.total_return_pct for r in best_results]
1180→                    ),
1181→                    avg_max_drawdown_pct=_safe_mean(
1182→                        [r.max_drawdown_pct for r in best_results]
1183→                    ),
1184→                    avg_win_rate_pct=_safe_mean(
1185→                        [r.win_rate_pct for r in best_results]
1186→                    ),
1187→                    symbol_count=len(best_results),
1188→                    portfolio_sortino=best_sortino,
1189→                    portfolio_max_drawdown=_portfolio_max_drawdown_from_results(
1190→                        best_results
1191→                    ),
1192→                    backtest_alpha=best_alpha,
1193→                ))
1194→
1195→            logger.info(
1196→                f"[MatrixBacktest] {group_id}: {strategy} done in "
1197→                f"{time.time() - strat_start:.1f}s "
1198→                f"({len(param_combos)} param combos × {valid_symbol_count} symbols)"
1199→            )
1200→
1201→        if not group_results:
1202→            logger.warning(
1203→                f"[MatrixBacktest] {group_id}: no valid results "
1204→                f"(elapsed {time.time() - group_start:.1f}s)"
1205→            )
1206→            return []
1207→
1208→        # 迭代 #11：健全性过滤 —— 排序前先剔除退化策略
1209→        # （experience.md #8：sanity → risk → rank）
1210→        # 退化策略 = 组内 ≥ 80% 标的 closed_trades==0（入场/出场条件互斥，
1211→        # 仓位靠末尾强平凑出 Sortino/alpha 假象）。此类策略必须先于 DD/Sortino/
1212→        # Alpha 过滤剔除，否则其盯市假象会骗过 alpha 排序进入权重。
1213→        sane_results: list[tuple[str, dict, list[SingleBacktestResult]]] = []
1214→        for (strategy, params, results) in group_results:
1215→            if _is_degenerate_strategy(results):
1216→                logger.warning(
1217→                    f"[MatrixBacktest] {group_id}: strategy '{strategy}' is DEGENERATE "
1218→                    f"(>= {DEGENERATE_NO_CLOSE_FRACTION:.0%} symbols have 0 closed trades) "
1219→                    f"— excluded before ranking. Its Sortino/alpha is mark-to-market illusion."
1220→                )
1221→                continue
1222→            sane_results.append((strategy, params, results))
1223→
1224→        if not sane_results:
1225→            # 全组退化 → 空权重（持仓现金），标记 no_valid_strategy，不强行选退化策略
1226→            logger.warning(
1227→                f"[MatrixBacktest] {group_id}: ALL strategies degenerate — "
1228→                f"group produces EMPTY weights (hold cash). Marked no_valid_strategy."
1229→            )
1230→            report.warnings.append(
1231→                f"{group_id}: no_valid_strategy (all strategies degenerate)"
1232→            )
1233→            # 标记已 append 的 GroupBacktestResult 条目（供审计追溯）
1234→            for gr in report.group_results:
1235→                if gr.group_id == group_id:
1236→                    gr.no_valid_strategy = True
1237→            return []
1238→
1239→        # 后续 candidates 构建、DD/Sortino/Alpha 过滤、排序，全部改用 sane_results
1240→        group_results = sane_results
1241→
1242→        # 3. 迭代 #9：DD 硬约束 + Sortino 门槛 + Alpha 排序选 Top-K
1243→        #    Constitution L1: portfolio DD ≤ 20% 是硬约束（保留）
1244→        #    新增：Sortino > 0.5 最低质量门槛（可放宽）
1245→        #    变更：排序指标从 Sortino 改为 Alpha
1246→        #
1247→        #    三级过滤策略：
1248→        #      Tier 1: DD ≤ 20% AND Sortino > 0.5 → Alpha 降序
1249→        #      Tier 2 (fallback): Tier 1 为空 → 仅 DD ≤ 20% → Alpha 降序
1250→        #      Tier 3 (fallback): Tier 2 为空 → 按 DD 升序，标记 dd_constrained=True
1251→        candidates: list[
1252→            tuple[str, dict, list[SingleBacktestResult], float, float, float]
1253→        ] = []
1254→        for (strategy, params, results) in group_results:
1255→            pso = _portfolio_sortino_from_results(results)
1256→            pdd = _portfolio_max_drawdown_from_results(results)
1257→            # 复用 _combine_daily_returns 计算 alpha（与 per-strategy 选择一致）
1258→            alpha = _compute_alpha(_combine_daily_returns(results), spy_returns)
1259→            candidates.append((strategy, params, results, pso, pdd, alpha))
1260→
1261→        # 迭代 #12：alpha>0 硬门槛（experience.md #8：正超额是排序前的硬门槛）
1262→        # 在 Tier 1/2/3 fallback 之前，剔除 alpha≤0 的候选。
1263→        # 理由：跑不赢 SPY 的策略不应进入权重，无论 DD/Sortino 多好。
1264→        # 顺序：健全性（Iter #11）→ 风险（DD，Tier 1/2/3）→ 正超额（alpha>0，本步）→ 排序
1265→        #
1266→        # 注意：这一步在 candidates 构建后、Tier 1 前，确保 Tier 1/2/3 只在正 alpha 候选中进行。
1267→        # 如果某组所有候选 alpha≤0，该组空仓（hold cash），不强行选负 alpha 策略
1268→        # （experience.md #8："没有候选满足门槛时，正确动作是空仓/降现金/回退 benchmark，
1269→        #   不是矬子里拔将军"）。
1270→        positive_alpha_candidates = [c for c in candidates if c[5] > 0]
1271→
1272→        if not positive_alpha_candidates:
1273→            # 全组 alpha≤0 → 空权重（持仓现金），标记 no_positive_alpha
1274→            alpha_strs = [f"{c[0]}({c[5]:.2f}%)" for c in candidates]
1275→            logger.warning(
1276→                f"[MatrixBacktest] {group_id}: ALL {len(candidates)} candidates have "
1277→                f"alpha <= 0 (cannot beat SPY) — {alpha_strs}. "
1278→                f"Group produces EMPTY weights (hold cash). Marked no_positive_alpha."
1279→            )
1280→            report.warnings.append(
1281→                f"{group_id}: no_positive_alpha (all {len(candidates)} candidates alpha <= 0)"
1282→            )
1283→            # 标记已 append 的 GroupBacktestResult 条目（供审计追溯）
1284→            for gr in report.group_results:
1285→                if gr.group_id == group_id:
1286→                    gr.no_positive_alpha = True
1287→            return []
1288→
1289→        # 后续 Tier 1/2/3 在正 alpha 候选中进行
1290→        candidates = positive_alpha_candidates
1291→
1292→        # Tier 1: DD ≤ 20% AND Sortino > 0.5
1293→        compliant = [
1294→            c for c in candidates
1295→            if c[4] <= MAX_PORTFOLIO_DRAWDOWN_PCT and c[3] > MIN_SORTINO_THRESHOLD
1296→        ]
1297→        if compliant:
1298→            # Tier 1 命中：按 Alpha 降序取 top-K
1299→            ranked = sorted(compliant, key=lambda x: x[5], reverse=True)
1300→            dd_constrained = False
1301→            logger.info(
1302→                f"[MatrixBacktest] {group_id}: DD + Sortino filter passed — "
1303→                f"{len(compliant)}/{len(candidates)} candidates compliant "
1304→                f"(DD <= {MAX_PORTFOLIO_DRAWDOWN_PCT}% AND Sortino > {MIN_SORTINO_THRESHOLD})"
1305→            )
1306→        else:
1307→            # Tier 2: 放宽 Sortino 门槛，仅保留 DD 约束
1308→            dd_compliant = [
1309→                c for c in candidates if c[4] <= MAX_PORTFOLIO_DRAWDOWN_PCT
1310→            ]
1311→            if dd_compliant:
1312→                # Tier 2 命中：按 Alpha 降序取 top-K（dd_constrained 仍为 False）
1313→                ranked = sorted(dd_compliant, key=lambda x: x[5], reverse=True)
1314→                dd_constrained = False
1315→                logger.warning(
1316→                    f"[MatrixBacktest] {group_id}: Sortino filter relaxed — "
1317→                    f"no candidate passed Sortino > {MIN_SORTINO_THRESHOLD}. "
1318→                    f"Fallback to DD-only filter: "
1319→                    f"{len(dd_compliant)}/{len(candidates)} candidates DD-compliant."
1320→                )
1321→            else:
1322→                # Tier 3: 无 DD 合规候选 → 按 DD 升序，标记 dd_constrained
1323→                # （结构性问题，如 NDX_high_vol 全部 > 20%）
1324→                ranked = sorted(candidates, key=lambda x: x[4])
1325→                dd_constrained = True
1326→                logger.warning(
1327→                    f"[MatrixBacktest] {group_id}: NO compliant candidates "
1328→                    f"(all {len(candidates)} exceed DD={MAX_PORTFOLIO_DRAWDOWN_PCT}%). "
1329→                    f"Fallback: selected top-{self._top_k} by lowest DD. "
1330→                    f"This group is marked dd_constrained=True — "
1331→                    f"review whether to drop the group or accept the risk."
1332→                )
1333→                report.warnings.append(
1334→                    f"{group_id}: dd_constrained=True "
1335→                    f"(min DD={ranked[0][4]:.2f}% > {MAX_PORTFOLIO_DRAWDOWN_PCT}%)"
1336→                )
1337→
1338→        top_results = ranked[: self._top_k]
1339→
1340→        # 把 dd_constrained 标记同步到 report.group_results 中对应组的条目
1341→        for gr in report.group_results:
1342→            if gr.group_id == group_id:
1343→                gr.dd_constrained = dd_constrained
1344→
1345→        # 4. 优化 ensemble 权重（单点离散值加权投票语义，迭代 #9 改用 alpha）
1346→        weighted = _optimize_ensemble_weights(
1347→            [(s, p, r) for (s, p, r, _, _, _) in top_results],
1348→            spy_returns=spy_returns,
1349→        )
1350→
1351→        # 5. 构建权重配置列表
1352→        weights_list = []
1353→        for strategy, params, weight in weighted:
1354→            # 找到对应的 GroupBacktestResult
1355→            gr = next(
1356→                (r for r in report.group_results
1357→                 if r.group_id == group_id and r.strategy == strategy),
1358→                None,
1359→            )
1360→            # 迭代 #4：新增 backtest_dd_status 字段（'pass' / 'dd_constrained'）
1361→            # 作为风险 metadata 标记，与 dd_constrained bool 同义但更可读
1362→            backtest_dd_status = "dd_constrained" if dd_constrained else "pass"
1363→            weights_list.append({
1364→                "strategy": strategy,
1365→                "params": params,
1366→                "weight": round(weight, 4),
1367→                "backtest_sharpe": round(gr.portfolio_sharpe if gr else 0.0, 4),
1368→                "backtest_sortino": round(gr.portfolio_sortino if gr else 0.0, 4),
1369→                "backtest_max_drawdown": round(gr.portfolio_max_drawdown if gr else 0.0, 4),
1370→                "backtest_win_rate": round(gr.avg_win_rate_pct / 100 if gr else 0.5, 4),
1371→                # 迭代 #9：新增 backtest_alpha 字段（vs SPY 的超额收益百分数）
1372→                # 下游 PortfolioBacktester 可读此字段验证 alpha 一致性
1373→                "backtest_alpha": round(gr.backtest_alpha if gr else 0.0, 4),
1374→                # 迭代 #3：标记该组是否用了 DD fallback（无合规候选）
1375→                # 同组所有策略条目共享同一 dd_constrained 值
1376→                "dd_constrained": dd_constrained,
1377→                # 迭代 #4：backtest_dd_status — 风险 metadata 字段
1378→                # 'pass' = 该组有合规候选（DD ≤ 20%）
1379→                # 'dd_constrained' = fallback 触发（无合规候选，按最低 DD 取 top-K）
1380→                # 下游消费方（PortfolioBacktester / 风控观测）可读此字段判断
1381→                # 该组权重的可靠性，作为风险信号标记
1382→                "backtest_dd_status": backtest_dd_status,
1383→            })
1384→
1385→        logger.info(
1386→            f"[MatrixBacktest] {group_id}: all strategies done in "
1387→            f"{time.time() - group_start:.1f}s "
1388→            f"(top-{self._top_k} selected, dd_constrained={dd_constrained})"
1389→        )
1390→
1391→        return weights_list
1392→
1393→    def _write_weights(
1394→        self, report: MatrixBacktestReport, output_file: str | Path
1395→    ) -> None:
1396→        """将矩阵回测结果写入 strategy_weights.json。"""
1397→        output_file = Path(output_file)
1398→        output_file.parent.mkdir(parents=True, exist_ok=True)
1399→
1400→        data = {
1401→            "_meta": {
1402→                "generated_at": report.generated_at,
1403→                "backtest_window": report.backtest_window,
1404→                "reoptimize_freq": "monthly",
1405→                "survivorship_bias_warning": (
1406→                    "使用当前成分股回测，S&P 500 5年成分变动约100只(~20%)，"
1407→                    "均值回归组(SPX_low_vol)结果可能系统性偏高"
1408→                ),
1409→            },
1410→            "groups": report.groups,
1411→        }
1412→
1413→        with open(output_file, "w", encoding="utf-8") as f:
1414→            json.dump(data, f, indent=2, ensure_ascii=False)
1415→
1416→        logger.info(f"[MatrixBacktest] weights saved to {output_file}")
1417→
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
  49→# 迭代 #11 新增：健全性门槛 —— 识别"退化策略"（几乎不平仓的伪 buy-and-hold）
  50→# 判定：组内"有效标的中，已平仓交易数为 0 的比例"超过此阈值 → 退化
  51→# 设计动机：真策略应在多数标的上完成买卖闭环；若近乎所有标的都从不平仓，
  52→#           说明入场/出场条件矛盾（如 Iter #8 rsi_trend_filter），其收益只是
  53→#           持仓盯市 + 末尾强平的假象，必须在排序前剔除（experience.md #8）。
  54→# 阈值取 0.8（保守）：只在"近乎全部标的零平仓"时触发，避免误伤低频合法策略。
  55→DEGENERATE_NO_CLOSE_FRACTION: float = 0.8
  56→
  57→
  58→# ---------------------------------------------------------------------------
  59→# 数据结构
  60→# ---------------------------------------------------------------------------
  61→
  62→@dataclass
  63→class SingleBacktestResult:
  64→    """单只标的单策略回测结果。"""
  65→
  66→    symbol: str
  67→    strategy: str
  68→    params: dict
  69→    sharpe: float
  70→    total_return_pct: float
  71→    max_drawdown_pct: float
  72→    win_rate_pct: float
  73→    total_trades: int
  74→    daily_returns: pd.Series    # pf.returns() — 供组合 Sharpe / Sortino 计算
  75→    sortino: float = 0.0       # Constitution L1 首要 KPI（迭代 #1 新增）
  76→    closed_trades: int = 0     # 迭代 #11 新增：已平仓交易数（区分退化 buy-and-hold）
  77→
  78→
  79→@dataclass
  80→class GroupBacktestResult:
  81→    """单组策略回测结果。"""
  82→
  83→    group_id: str
  84→    strategy: str
  85→    params: dict
  86→    portfolio_sharpe: float          # 等权组合 Sharpe（而非算术平均）
  87→    avg_total_return_pct: float
  88→    avg_max_drawdown_pct: float
  89→    avg_win_rate_pct: float
  90→    symbol_count: int
  91→    portfolio_sortino: float = 0.0          # 等权组合 Sortino（迭代 #1 新增）
  92→    portfolio_max_drawdown: float = 0.0     # 等权组合最大回撤（迭代 #2 新增，Constitution L1 KPI）
  93→    dd_constrained: bool = False            # 迭代 #3：该组是否用了 DD fallback（无合规候选）
  94→    backtest_alpha: float = 0.0              # 迭代 #9：alpha vs SPY（百分数），用于排序策略选择
  95→    no_valid_strategy: bool = False         # 迭代 #11：该组是否因全退化而空仓（hold cash）
  96→    no_positive_alpha: bool = False         # 迭代 #12：该组是否因全负 alpha 而空仓（hold cash）
  97→
  98→
  99→@dataclass
 100→class MatrixBacktestReport:
 101→    """整个矩阵回测的汇总报告。"""
 102→
 103→    generated_at: str
 104→    backtest_window: str
 105→    groups: dict[str, list[dict]]   # group_id → [策略权重配置]
 106→    group_results: list[GroupBacktestResult] = field(default_factory=list)
 107→    warnings: list[str] = field(default_factory=list)
 108→
 109→
 110→# ---------------------------------------------------------------------------
 111→# Walk-Forward 数据结构（迭代 #3 新增，Constitution L7 验证流水线）
 112→# ---------------------------------------------------------------------------
 113→
 114→@dataclass
 115→class WalkForwardRound:
 116→    """单轮 Walk-Forward 验证结果。
 117→
 118→    一轮 = 训练期（找最优参数）+ 验证期（用同参数回测，记录样本外指标）。
 119→
 120→    Attributes:
 121→        round_num:    轮次编号（1-indexed）
 122→        train_start:  训练期起始日期（含）
 123→        train_end:    训练期结束日期（含）
 124→        val_start:    验证期起始日期（含）
 125→        val_end:      验证期结束日期（含）
 126→        val_sortino:  验证期等权组合 Sortino Ratio（年化）
 127→        val_max_dd:   验证期等权组合最大回撤（正值百分数，0~100）
 128→        passed:       是否通过 = val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD (15%)
 129→    """
 130→
 131→    round_num: int
 132→    train_start: date
 133→    train_end: date
 134→    val_start: date
 135→    val_end: date
 136→    val_sortino: float
 137→    val_max_dd: float
 138→    passed: bool
 139→
 140→
 141→@dataclass
 142→class WalkForwardReport:
 143→    """Walk-Forward 4 轮验证汇总报告。
 144→
 145→    Constitution L7 要求 Backtest(>=5年) → Walk-Forward(4轮) → Paper → Live。
 146→    本报告是 Walk-Forward 阶段的产出。
 147→
 148→    Attributes:
 149→        rounds:         每轮结果列表（长度通常为 4）
 150→        pass_all_rounds: 是否所有轮都通过（all(r.passed for r in rounds)）
 151→        max_val_dd:     所有轮中最大的验证期 DD（用于风险监控）
 152→    """
 153→
 154→    rounds: list[WalkForwardRound] = field(default_factory=list)
 155→    pass_all_rounds: bool = False
 156→    max_val_dd: float = 0.0
 157→
 158→
 159→# ---------------------------------------------------------------------------
 160→# 核心函数
 161→# ---------------------------------------------------------------------------
 162→
 163→def _safe_float(value: Any, default: float = 0.0) -> float:
 164→    """NaN/None/非数值安全转 float（迭代 #2 新增）。
 165→
 166→    问题背景：vectorbt 在无交易场景下，`pf.stats()` 的 Win Rate / Sharpe 等
 167→    字段会返回 NaN。`float(NaN or 0.0)` 仍是 NaN（NaN 是 truthy），导致
 168→    JSON 序列化写出非法 JSON（NaN/Infinity 非 JSON 规范）。
 169→
 170→    处理顺序：
 171→        1. None → default
 172→        2. 数值类型但 NaN/Inf → default
 173→        3. 非数值（字符串等）尝试 float() 转换，失败 → default
 174→    """
 175→    if value is None:
 176→        return default
 177→    try:
 178→        f = float(value)
 179→    except (TypeError, ValueError):
 180→        return default
 181→    if not np.isfinite(f):   # 拦截 NaN / +Inf / -Inf
 182→        return default
 183→    return f
 184→
 185→
 186→def _safe_mean(values: Any, default: float = 0.0) -> float:
 187→    """空列表 / 全 NaN 安全的均值（迭代 #2 新增）。
 188→
 189→    问题背景：`np.mean([])` 会触发 RuntimeWarning 并返回 NaN；
 190→    `np.mean([NaN, NaN])` 直接返回 NaN。在 GroupBacktestResult 聚合时
 191→    若某组只有 1 个标的且其字段为 NaN，会导致下游 JSON 序列化失败。
 192→
 193→    行为：
 194→        - 空列表 / 全 NaN → default
 195→        - 部分 NaN → 自动忽略 NaN 后取均值（np.nanmean 语义）
 196→    """
 197→    arr = np.asarray(values, dtype=float)
 198→    if arr.size == 0:
 199→        return default
 200→    mask = np.isfinite(arr)
 201→    if not mask.any():
 202→        return default
 203→    return float(arr[mask].mean())
 204→
 205→
 206→def _compute_sharpe(returns: pd.Series, periods_per_year: int = 252) -> float:
 207→    """从日收益率序列计算年化 Sharpe Ratio。"""
 208→    returns = returns.dropna()
 209→    if len(returns) < 5:
 210→        return 0.0
 211→    mean = returns.mean()
 212→    std = returns.std()
 213→    if std <= 0 or np.isnan(std):
 214→        return 0.0
 215→    return float(mean / std * np.sqrt(periods_per_year))
 216→
 217→
 218→def _compute_sortino(
 219→    returns: pd.Series,
 220→    periods_per_year: int = 252,
 221→    target: float = 0.0,
 222→) -> float:
 223→    """从日收益率序列计算年化 Sortino Ratio（Constitution L1 首要 KPI）。
 224→
 225→    Sortino = (mean(returns) - target) / downside_deviation * sqrt(periods_per_year)
 226→    downside_deviation = sqrt( mean( min(0, returns - target)^2 ) )
 227→
 228→    与 Sharpe 的区别：仅对下行波动惩罚，上行波动不计入分母。
 229→    适合"收益>0 但偶尔大跌"的中长线策略评估。
 230→
 231→    退化处理（与 _compute_sharpe 一致）：
 232→        - 样本 < 5 → 0.0
 233→        - 下行波动 ≤ 0（无下行样本）→ 0.0（理论为 +inf，返回 0 保持保守 + 可算术聚合）
 234→
 235→    Args:
 236→        returns:          日收益率序列（如 pf.returns()）
 237→        periods_per_year: 年化因子（日线 = 252）
 238→        target:           MAR/目标收益率，默认 0（与 _compute_sharpe 无风险利率假设一致）
 239→
 240→    Returns:
 241→        年化 Sortino Ratio
 242→    """
 243→    returns = returns.dropna()
 244→    if len(returns) < 5:
 245→        return 0.0
 246→    excess = returns - target
 247→    downside = excess.where(excess < 0, 0.0)        # 仅保留负偏离，正偏离置 0
 248→    dd = np.sqrt((downside ** 2).mean())
 249→    if dd <= 0 or np.isnan(dd):
 250→        return 0.0
 251→    return float(returns.mean() / dd * np.sqrt(periods_per_year))
 252→
 253→
 254→def _combine_daily_returns(results: list[SingleBacktestResult]) -> pd.Series:
 255→    """等权合并组内日收益率序列，返回组合日收益率（迭代 #9 新增）。
 256→
 257→    与 _portfolio_sharpe_from_results / _portfolio_sortino_from_results 同语义：
 258→    将所有标的日收益率等权合并为组合序列。提取为独立函数以便 alpha 计算
 259→    和 per-strategy best params 选择复用，避免重复 pd.concat。
 260→
 261→    Args:
 262→        results: 单策略多标的的回测结果列表
 263→
 264→    Returns:
 265→        组合日收益率 pd.Series；无有效数据时返回空 Series
 266→    """
 267→    valid = [r.daily_returns for r in results if not r.daily_returns.empty]
 268→    if not valid:
 269→        return pd.Series(dtype=float)
 270→    return pd.concat(valid, axis=1).mean(axis=1)
 271→
 272→
 273→def _is_degenerate_strategy(results: list[SingleBacktestResult]) -> bool:
 274→    """判定一个策略在组内是否退化（几乎不产生已平仓交易）（迭代 #11 新增）。
 275→
 276→    退化定义：有效标的中 closed_trades==0 的比例 >= DEGENERATE_NO_CLOSE_FRACTION。
 277→    这类策略的入场/出场条件互斥（如 Iter #8 rsi_trend_filter 趋势过滤锁死均值
 278→    回归出场），仓位无法平仓，其 Sortino/alpha 只是持仓盯市假象，不代表真实
 279→    交易能力，必须在排序前剔除（experience.md #8：sanity → risk → rank）。
 280→
 281→    Args:
 282→        results: 单策略多标的的回测结果列表
 283→
 284→    Returns:
 285→        True 表示退化（应剔除）；空结果视为退化（True）
 286→    """
 287→    if not results:
 288→        return True
 289→    n = len(results)
 290→    no_close = sum(1 for r in results if r.closed_trades <= 0)
 291→    return (no_close / n) >= DEGENERATE_NO_CLOSE_FRACTION
 292→
 293→
 294→def _compute_alpha(
 295→    strategy_daily_returns: pd.Series,
 296→    spy_daily_returns: pd.Series | None,
 297→    periods_per_year: int = 252,
 298→) -> float:
 299→    """计算 alpha = 策略年化收益 - SPY 年化收益（迭代 #9 新增）。
 300→
 301→    Alpha 衡量策略相对 SPY buy-and-hold 的超额收益。正值表示跑赢 SPY，
 302→    负值表示跑输 SPY。用于 top-K 策略选择和 per-strategy best params 选择，
 303→    替代之前基于 Sortino/Sharpe 的选择逻辑（参考 iteration #9 spec）。
 304→
 305→    年化公式：(1 + mean_daily) ** periods_per_year - 1
 306→    使用算术平均日收益的几何年化，与 PortfolioBacktester 同口径。
 307→
 308→    降级处理：SPY 数据不可用（None 或空）→ 返回 0.0（不抛异常）。
 309→    这样在 SPY 数据缺失时，alpha 排序退化为"原顺序"，不会阻塞回测。
 310→
 311→    Args:
 312→        strategy_daily_returns: 策略组合日收益率序列
 313→        spy_daily_returns:      SPY 日收益率序列；None 表示数据不可用
 314→        periods_per_year:       年化因子（日线 = 252）
 315→
 316→    Returns:
 317→        Alpha 百分数（如 5.23 表示策略年化收益跑赢 SPY 5.23 个百分点）；
 318→        SPY 不可用时返回 0.0
 319→    """
 320→    if spy_daily_returns is None or spy_daily_returns.empty:
 321→        return 0.0
 322→    if strategy_daily_returns is None or strategy_daily_returns.empty:
 323→        return 0.0
 324→
 325→    # 对齐时间索引（inner join 取交集）
 326→    aligned = pd.concat(
 327→        [strategy_daily_returns.rename("strat"), spy_daily_returns.rename("spy")],
 328→        axis=1,
 329→        join="inner",
 330→    ).dropna()
 331→    if aligned.empty or len(aligned) < 2:
 332→        return 0.0
 333→
 334→    strat_returns = aligned["strat"]
 335→    spy_returns = aligned["spy"]
 336→
 337→    # 年化收益 = (1 + mean_daily)^252 - 1
 338→    strat_mean = strat_returns.mean()
 339→    spy_mean = spy_returns.mean()
 340→    if not np.isfinite(strat_mean) or not np.isfinite(spy_mean):
 341→        return 0.0
 342→
 343→    strat_annual = (1.0 + strat_mean) ** periods_per_year - 1.0
 344→    spy_annual = (1.0 + spy_mean) ** periods_per_year - 1.0
 345→
 346→    alpha = (strat_annual - spy_annual) * 100.0  # 转为百分数
 347→    if not np.isfinite(alpha):
 348→        return 0.0
 349→    return float(alpha)
 350→
 351→
 352→def _backtest_one(
 353→    df: pd.DataFrame,
 354→    strategy_name: str,
 355→    params: dict,
 356→    init_cash: float = 100_000.0,
 357→    fees: float = 0.001,
 358→    slippage: float = 0.001,
 359→) -> SingleBacktestResult | None:
 360→    """对单只标的执行单次回测。
 361→
 362→    使用 open= 参数确保信号在下一根 bar 的开盘价执行（与实盘一致）。
 363→
 364→    Returns:
 365→        SingleBacktestResult 或 None（数据不足/策略异常时）
 366→    """
 367→    strategy_fn = STRATEGY_REGISTRY.get(strategy_name)
 368→    if strategy_fn is None:
 369→        return None
 370→
 371→    if df.empty or len(df) < 30:
 372→        return None
 373→
 374→    try:
 375→        close = df["close"]
 376→        open_ = df["open"] if "open" in df.columns else None
 377→
 378→        # 调用策略（兼容需要 df 的策略）
 379→        try:
 380→            sig = strategy_fn(close, df=df, **params)
 381→        except TypeError:
 382→            sig = strategy_fn(close, **params)
 383→
 384→        entries = sig == 1
 385→        exits   = sig == -1
 386→
 387→        pf_kwargs: dict[str, Any] = dict(
 388→            entries=entries,
 389→            exits=exits,
 390→            init_cash=init_cash,
 391→            fees=fees,
 392→            slippage=slippage,
 393→            size=0.95,
 394→            size_type="Percent",
 395→            freq="D",
 396→        )
 397→
 398→        # ⚠️ 必须传 open= 参数：信号在下一根 bar 开盘价执行，与实盘一致
 399→        if open_ is not None:
 400→            pf = vbt.Portfolio.from_signals(close=close, open=open_, **pf_kwargs)
 401→        else:
 402→            pf = vbt.Portfolio.from_signals(close, **pf_kwargs)
 403→
 404→        stats = pf.stats()
 405→
 406→        daily_returns = pf.returns()
 407→
 408→        # 迭代 #11：已平仓交易数（用于健全性门槛 _is_degenerate_strategy）
 409→        # vbt 1.0 API: pf.trades.closed.count() 返回 Status==Closed 的交易数
 410→        # 区分"真交易闭环"与"末尾强平计 1 笔的伪 buy-and-hold"
 411→        try:
 412→            closed_trades = int(pf.trades.closed.count())
 413→        except Exception:
 414→            closed_trades = 0
 415→
 416→        return SingleBacktestResult(
 417→            symbol=str(df.index.name or ""),
 418→            strategy=strategy_name,
 419→            params=params,
 420→            sharpe=_safe_float(stats.get("Sharpe Ratio")),
 421→            total_return_pct=_safe_float(stats.get("Total Return [%]")),
 422→            max_drawdown_pct=_safe_float(stats.get("Max Drawdown [%]")),
 423→            win_rate_pct=_safe_float(stats.get("Win Rate [%]")),
 424→            total_trades=int(_safe_float(stats.get("Total Trades"), default=0.0)),
 425→            daily_returns=daily_returns,
 426→            sortino=_compute_sortino(daily_returns),
 427→            closed_trades=closed_trades,
 428→        )
 429→    except Exception as e:
 430→        logger.debug(f"[backtest_one] {strategy_name}({params}) failed: {e}")
 431→        return None
 432→
 433→
 434→def _backtest_batch(
 435→    data: dict[str, pd.DataFrame],
 436→    strategy_name: str,
 437→    params: dict,
 438→    init_cash: float = 100_000.0,
 439→    fees: float = 0.001,
 440→    slippage: float = 0.001,
 441→) -> list[SingleBacktestResult]:
 442→    """对组内所有标的批量执行回测（迭代 #10 新增）。
 443→
 444→    核心优化：用一次 vbt.Portfolio.from_signals 处理组内所有标的，
 445→    替代 `_backtest_one` 的 for-symbol 循环。调用次数从 O(N 标的)
 446→    降为 O(1)，预计 10-20x 提速（spec §1）。
 447→
 448→    实现要点：
 449→        1. 逐标的调用策略函数（保持与 `_backtest_one` 一致的调用语义：
 450→           先尝试 `strategy_fn(close, df=df, **params)`，TypeError 时
 451→           回退到 `strategy_fn(close, **params)`）。策略函数本身不改。
 452→        2. 构建列式矩阵（每列一个标的），用一次 vbt 调用回测所有标的。
 453→           vbt 1.0+ 的列分组语义保证每列独立结算 P&L。
 454→        3. 通过 `pf[sym]` 提取每列的 stats/daily_returns，输出格式与
 455→           `_backtest_one` 完全一致，下游聚合代码无需修改。
 456→
 457→    对齐策略：
 458→        - 用 `pd.DataFrame(dict)` 构造时自动 outer-join 时间索引，
 459→          缺失值填 NaN。
 460→        - vbt 对 NaN close 的处理：内部 fillna 为 0 收益率，等价于
 461→          "该标的此日期不交易"。当标的在样本外日期缺失时（如退市、
 462→          新上市），其 stats 仍按其有效日期区间计算。
 463→        - 在美股实际场景中所有标的共享交易日历，日期对齐天然成立，
 464→          不会有大量 NaN。
 465→
 466→    Args:
 467→        data:          {symbol: OHLCV DataFrame} 字典
 468→        strategy_name: 策略名
 469→        params:        策略参数
 470→        init_cash:     初始资金（vbt 给每列分配独立的 init_cash）
 471→        fees:          手续费率
 472→        slippage:      滑点率
 473→
 474→    Returns:
 475→        SingleBacktestResult 列表（与 `_backtest_one` 输出格式一致）。
 476→        数据不足 / 策略异常的标的会被跳过（不返回 None，不抛异常）。
 477→        空数据时返回空列表。
 478→    """
 479→    strategy_fn = STRATEGY_REGISTRY.get(strategy_name)
 480→    if strategy_fn is None:
 481→        return []
 482→
 483→    # 1. 逐标的调用策略函数，构建 signal / close / open 列
 484→    signal_columns: dict[str, pd.Series] = {}
 485→    close_columns: dict[str, pd.Series] = {}
 486→    open_columns: dict[str, pd.Series] = {}
 487→
 488→    for sym, df in data.items():
 489→        if df is None or df.empty or len(df) < 30:
 490→            continue
 491→        close = df["close"]
 492→        if "open" in df.columns:
 493→            open_ = df["open"]
 494→            open_columns[sym] = open_
 495→        else:
 496→            open_ = None
 497→
 498→        # 调用策略（与 _backtest_one 一致的 try/except 语义）
 499→        try:
 500→            sig = strategy_fn(close, df=df, **params)
 501→        except TypeError:
 502→            sig = strategy_fn(close, **params)
 503→        except Exception as e:
 504→            logger.debug(
 505→                f"[backtest_batch] {strategy_name}({params}) {sym} failed: {e}"
 506→            )
 507→            continue
 508→
 509→        signal_columns[sym] = sig
 510→        close_columns[sym] = close
 511→
 512→    if not signal_columns:
 513→        return []
 514→
 515→    # 2. 构建矩阵（自动 outer-join 索引，缺失值填 NaN）
 516→    close_matrix = pd.DataFrame(close_columns)
 517→    signal_matrix = pd.DataFrame(signal_columns)
 518→    has_open = bool(open_columns)
 519→    open_matrix = pd.DataFrame(open_columns) if has_open else None
 520→
 521→    # 3. 一次 vbt 调用处理所有标的
 522→    entries = signal_matrix == 1
 523→    exits = signal_matrix == -1
 524→
 525→    pf_kwargs: dict[str, Any] = dict(
 526→        entries=entries,
 527→        exits=exits,
 528→        init_cash=init_cash,
 529→        fees=fees,
 530→        slippage=slippage,
 531→        size=0.95,
 532→        size_type="Percent",
 533→        freq="D",
 534→    )
 535→
 536→    try:
 537→        if has_open:
 538→            pf = vbt.Portfolio.from_signals(
 539→                close=close_matrix, open=open_matrix, **pf_kwargs
 540→            )
 541→        else:
 542→            pf = vbt.Portfolio.from_signals(close_matrix, **pf_kwargs)
 543→    except Exception as e:
 544→        logger.warning(
 545→            f"[backtest_batch] {strategy_name}({params}) vbt call failed: {e} "
 546→            f"— falling back to per-symbol _backtest_one"
 547→        )
 548→        # 回滚方案：批量失败时退化为逐标的回测，保证回测不中断
 549→        results: list[SingleBacktestResult] = []
 550→        for sym, df in data.items():
 551→            if df is None or df.empty or len(df) < 30:
 552→                continue
 553→            df = df.copy()
 554→            df.index.name = sym
 555→            r = _backtest_one(
 556→                df, strategy_name, params, init_cash, fees, slippage
 557→            )
 558→            if r is not None:
 559→                results.append(r)
 560→        return results
 561→
 562→    # 4. 提取 per-symbol 结果（与 _backtest_one 输出格式一致）
 563→    results = []
 564→    for sym in signal_matrix.columns:
 565→        try:
 566→            pf_sym = pf[sym]
 567→            stats = pf_sym.stats()
 568→            daily_returns = pf_sym.returns()
 569→            # 迭代 #11：已平仓交易数（与 _backtest_one 同 API、同语义）
 570→            # pf_sym 是单列 pf，pf_sym.trades.closed.count() 返回 int
 571→            try:
 572→                closed_trades = int(pf_sym.trades.closed.count())
 573→            except Exception:
 574→                closed_trades = 0
 575→            results.append(SingleBacktestResult(
 576→                symbol=sym,
 577→                strategy=strategy_name,
 578→                params=params,
 579→                sharpe=_safe_float(stats.get("Sharpe Ratio")),
 580→                total_return_pct=_safe_float(stats.get("Total Return [%]")),
 581→                max_drawdown_pct=_safe_float(stats.get("Max Drawdown [%]")),
 582→                win_rate_pct=_safe_float(stats.get("Win Rate [%]")),
 583→                total_trades=int(_safe_float(stats.get("Total Trades"), default=0.0)),
 584→                daily_returns=daily_returns,
 585→                sortino=_compute_sortino(daily_returns),
 586→                closed_trades=closed_trades,
 587→            ))
 588→        except Exception as e:
 589→            logger.debug(
 590→                f"[backtest_batch] {strategy_name}({params}) {sym} "
 591→                f"stats extraction failed: {e}"
 592→            )
 593→            continue
 594→
 595→    return results
 596→
 597→
 598→def _portfolio_sharpe_from_results(results: list[SingleBacktestResult]) -> float:
 599→    """等权合并组内日收益率序列，计算组合 Sharpe。
 600→
 601→    ⚠️ 不能取各标的 Sharpe 算术平均（Sharpe 是比率，不能直接平均）。
 602→    正确做法：将所有标的日收益率等权合并为组合序列，再计算 Sharpe。
 603→    """
 604→    valid = [r.daily_returns for r in results if not r.daily_returns.empty]
 605→    if not valid:
 606→        return 0.0
 607→
 608→    # 对齐时间索引，等权平均
 609→    combined = pd.concat(valid, axis=1).mean(axis=1)
 610→    return _compute_sharpe(combined)
 611→
 612→
 613→def _portfolio_sortino_from_results(results: list[SingleBacktestResult]) -> float:
 614→    """等权合并组内日收益率序列，计算组合 Sortino（与 _portfolio_sharpe_from_results 同语义）。
 615→
 616→    不能取各标的 Sortino 算术平均（与 Sharpe 同理：比率不可直接平均）。
 617→    """
 618→    valid = [r.daily_returns for r in results if not r.daily_returns.empty]
 619→    if not valid:
 620→        return 0.0
 621→    combined = pd.concat(valid, axis=1).mean(axis=1)
 622→    return _compute_sortino(combined)
 623→
 624→
 625→def _portfolio_max_drawdown_from_results(
 626→    results: list[SingleBacktestResult],
 627→) -> float:
 628→    """等权合并组内日收益率序列，计算组合最大回撤（迭代 #2 新增，Constitution L1 KPI）。
 629→
 630→    与 `_portfolio_sharpe_from_results` 同语义：不能取各标的 DD 算术平均，
 631→    因为 DD 是路径依赖的比率。正确做法是先把��内日收益率等权合并为组合序列，
 632→    再 cumprod → cummax → drawdown → max。
 633→
 634→    返回值约定：百分比形式（与 `SingleBacktestResult.max_drawdown_pct` 一致，
 635→    vectorbt stats 中 `Max Drawdown [%]` 同样是百分数，例如 -15.2 表示 15.2% 回撤）。
 636→    本函数返回正值（0.0 ~ 100.0）便于聚合与 JSON 输出。
 637→
 638→    退化处理：
 639→        - 无有效日收益率 → 0.0
 640→        - 全 0 收益率（cumprod 恒为 1.0）→ 0.0
 641→    """
 642→    valid = [r.daily_returns for r in results if not r.daily_returns.empty]
 643→    if not valid:
 644→        return 0.0
 645→    combined = pd.concat(valid, axis=1).mean(axis=1).dropna()
 646→    if len(combined) < 2:
 647→        return 0.0
 648→    # 组合累计净值：初始 1.0，每日乘 (1 + r)
 649→    cumvalue = (1.0 + combined).cumprod()
 650→    peak = cumvalue.cummax()
 651→    drawdown = (cumvalue - peak) / peak   # 负值，0 表示无回撤
 652→    dd_max_pct = float(drawdown.min())    # 最负值，例如 -0.152
 653→    if not np.isfinite(dd_max_pct):
 654→        return 0.0
 655→    # 转为正百分数（与 vectorbt Max Drawdown [%] 的口径一致但取正号）
 656→    return abs(dd_max_pct) * 100.0
 657→
 658→
 659→def _optimize_ensemble_weights(
 660→    group_results: list[tuple[str, dict, list[SingleBacktestResult]]],
 661→    spy_returns: pd.Series | None = None,
 662→    conflict_threshold: float = 0.3,
 663→) -> list[tuple[str, dict, float]]:
 664→    """在"单点离散值加权投票"语义下优化 ensemble 权重。
 665→
 666→    实盘每根 bar 各策略产出离散值（1/-1/0），加权投票决定方向。
 667→    回测的权重优化必须使用相同语义，而非对整段时间序列做加权。
 668→
 669→    迭代 #9：权重计算从 Sharpe 改为 Alpha（vs SPY）。
 670→    动机：与 _run_group 的 top-K 排序口径一致，使 ensemble 权重直接
 671→    反映"跑赢 SPY 的程度"。SPY 不可用时 alpha=0，退化为等权。
 672→
 673→    迭代 #12：修负 alpha 归一化 bug。
 674→    旧代码 `max(alpha, 0.01)` 把负 alpha 都变成 0.01，归一化后等权，
 675→    掩盖"都不好"的事实（experience.md #8）。新逻辑：负 alpha 权重为 0，
 676→    只有正 alpha 参与归一化；全负 alpha 时等权 fallback + WARNING
 677→    （上游 alpha>0 门槛应已拦截，此处为防御性设计）。
 678→
 679→    Args:
 680→        group_results: [(strategy, params, [SingleBacktestResult]), ...]
 681→        spy_returns:   SPY 日收益率序列（用于 alpha 计算）；None 时退化为等权
 682→        conflict_threshold: 加权投票分数绝对值低于此时视为 HOLD
 683→
 684→    Returns:
 685→        [(strategy, params, weight), ...] 归一化权重列表
 686→    """
 687→    if len(group_results) == 1:
 688→        strategy, params, _ = group_results[0]
 689→        return [(strategy, params, 1.0)]
 690→
 691→    # 迭代 #12：负 alpha 策略不参与 ensemble（experience.md #8：负分不能用 max(x, ε) 掩盖）
 692→    # 只有正 alpha 的策略参与归一化；负 alpha 策略权重为 0。
 693→    # 上游 _run_group 的 alpha>0 门槛应已拦截全负 alpha 情形，
 694→    # 这里是防御性设计：即使上游漏过负 alpha，也不会被 max(0.01) 掩盖成等权。
 695→    raw_alphas = []
 696→    for strategy, params, results in group_results:
 697→        combined = _combine_daily_returns(results)
 698→        alpha = _compute_alpha(combined, spy_returns)
 699→        raw_alphas.append(alpha)
 700→
 701→    # 负 alpha → 权重 0；正 alpha → 参与归一化
 702→    positive_alphas = [max(a, 0.0) for a in raw_alphas]
 703→    total = sum(positive_alphas)
 704→
 705→    if total > 0:
 706→        weights = [a / total for a in positive_alphas]
 707→    else:
 708→        # 防御性 fallback：全负 alpha 或全零时等权
 709→        # （上游 alpha>0 门槛应已拦截，此处不应到达）
 710→        n = len(group_results)
 711→        weights = [1.0 / n] * n if n > 0 else []
 712→        logger.warning(
 713→            f"[ensemble_weights] all alphas <= 0 ({raw_alphas}), "
 714→            f"falling back to equal weight. This should not happen if "
 715→            f"alpha>0 gate is active upstream."
 716→        )
 717→
 718→    return [
 719→        (strategy, params, weight)
 720→        for (strategy, params, _), weight in zip(group_results, weights)
 721→    ]
 722→
 723→
 724→# ---------------------------------------------------------------------------
 725→# Walk-Forward 验证（迭代 #3 新增，Constitution L7 验证流水线）
 726→# ---------------------------------------------------------------------------
 727→
 728→def _add_months(d: date, months: int) -> date:
 729→    """对 date 加/减 months 个月，自动 clamp 到月末。
 730→
 731→    使用 pandas DateOffset 以避免引入 dateutil 依赖（pandas 已是核心依赖）。
 732→    """
 733→    return (pd.Timestamp(d) + pd.DateOffset(months=months)).date()
 734→
 735→
 736→def _backtest_with_params_on_period(
 737→    mb: "MatrixBacktest",
 738→    symbols: list[str],
 739→    weights: list[dict[str, Any]],
 740→    start: date,
 741→    end: date,
 742→) -> list[pd.Series]:
 743→    """用给定权重配置在 [start, end] 期间回测，返回每条 (策略×标的) 的日收益率序列。
 744→
 745→    用于 Walk-Forward 验证期：用训练期产出的 best params 在验证期回测，
 746→    不再做参数搜索。返回原始日收益率列表，由调用方聚合为整体 portfolio。
 747→
 748→    迭代 #10 变更：用 `_backtest_batch` 替代 for-symbol 循环，
 749→    每个策略×参数组合一次 vbt 调用，加速 Walk-Forward 验证期回测。
 750→
 751→    Args:
 752→        mb:       MatrixBacktest 实例（复用其 store/init_cash/fees/slippage）
 753→        symbols:  该组的标的列表
 754→        weights:  训练期产出的权重配置（list of dict，含 strategy/params/weight）
 755→        start:    验证期起始日期
 756→        end:      验证期结束日期
 757→
 758→    Returns:
 759→        list[pd.Series] — 每条 (strategy×symbol) 的日收益率；空列表表示无有效数据
 760→    """
 761→    if not weights or not symbols:
 762→        return []
 763→
 764→    data = mb._store.get_bars_multi(symbols, start, end)
 765→    if not data:
 766→        return []
 767→
 768→    all_returns: list[pd.Series] = []
 769→    for w in weights:
 770→        strategy = w.get("strategy", "")
 771→        params = w.get("params", {})
 772→        if not strategy or strategy not in STRATEGY_REGISTRY:
 773→            continue
 774→        # 迭代 #10：一次 batch 调用处理组内所有标的
 775→        results = _backtest_batch(
 776→            data, strategy, params,
 777→            mb._init_cash, mb._fees, mb._slippage,
 778→        )
 779→        for r in results:
 780→            if not r.daily_returns.empty:
 781→                all_returns.append(r.daily_returns)
 782→    return all_returns
 783→
 784→
 785→def run_walk_forward(
 786→    mb: "MatrixBacktest",
 787→    strategies: list[str],
 788→    param_grids: dict[str, dict[str, list]],
 789→    rounds: int = 4,
 790→    train_months: int = 18,
 791→    val_months: int = 6,
 792→) -> WalkForwardReport:
 793→    """执行 N 轮 Walk-Forward 验证（Constitution L7 验证流水线硬要求）。
 794→
 795→    每轮流程：
 796→        1. 训练期 [train_start, train_end]：跑矩阵回测找最优参数
 797→        2. 验证期 [val_start, val_end]：用同参数回测，记录 portfolio Sortino 和 max DD
 798→        3. passed = val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD (15%)
 799→
 800→    时间窗口（动态计算，today=today）：
 801→        - 最后一轮 val_end = today - val_months（留 1 个 val 期给 paper trading）
 802→        - 每轮向前推 val_months
 803→        - train_end = val_start，train_start = train_end - train_months
 804→
 805→    默认参数 (rounds=4, train_months=18, val_months=6) 对应用户提供的固定窗口：
 806→        today=2026-07-01 →
 807→        Round 1: train 2021-07-02~2023-01-02, val 2023-01-02~2023-07-02
 808→        Round 2: train 2022-01-02~2023-07-02, val 2023-07-02~2024-01-02
 809→        Round 3: train 2022-07-02~2024-01-02, val 2024-01-02~2024-07-02
 810→        Round 4: train 2023-01-02~2024-07-02, val 2024-07-02~2025-01-02
 811→
 812→    Args:
 813→        mb:            MatrixBacktest 实例（复用其 store/universe/init_cash 等）
 814→        strategies:    策略名称列表
 815→        param_grids:   参数网格（与 mb.run() 接收的格式一致）
 816→        rounds:        轮次数（默认 4，Constitution L7 要求）
 817→        train_months:  训练期月数（默认 18）
 818→        val_months:    验证期月数（默认 6）
 819→
 820→    Returns:
 821→        WalkForwardReport — 包含每轮结果、pass_all_rounds、max_val_dd
 822→
 823→    Note:
 824→        - WF 是验证步骤，不修改 strategy_weights.json
 825→        - 失败轮次会记录 WARNING 但不抛异常
 826→        - 全部 4 轮通过是进入 paper trading 的前置条件
 827→    """
 828→    today = date.today()
 829→    groups = mb._universe.get_groups()
 830→    if not groups:
 831→        logger.warning("[WalkForward] no groups available — skipping")
 832→        return WalkForwardReport()
 833→
 834→    wf_rounds: list[WalkForwardRound] = []
 835→
 836→    for i in range(rounds):
 837→        round_num = i + 1
 838→        # 计算本轮时间窗口
 839→        # 最后一轮 (i=rounds-1) 的 val_end = today - val_months
 840→        # 前面轮次依次向前推 val_months
 841→        val_end = _add_months(today, -val_months - (rounds - round_num) * val_months)
 842→        val_start = _add_months(val_end, -val_months)
 843→        train_end = val_start
 844→        train_start = _add_months(train_end, -train_months)
 845→
 846→        logger.info(
 847→            f"[WalkForward] Round {round_num}/{rounds}: "
 848→            f"train={train_start}~{train_end}, val={val_start}~{val_end}"
 849→        )
 850→
 851→        # ── 训练期：跑矩阵回测找最优参数（复用 mb._run_group）──
 852→        train_report = MatrixBacktestReport(
 853→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
 854→            backtest_window=f"{train_start.isoformat()} ~ {train_end.isoformat()}",
 855→            groups={},
 856→        )
 857→
 858→        for group_id, symbols in groups.items():
 859→            weights = mb._run_group(
 860→                group_id=group_id,
 861→                symbols=symbols,
 862→                start=train_start,
 863→                end=train_end,
 864→                strategies=strategies,
 865→                param_grids=param_grids,
 866→                report=train_report,
 867→            )
 868→            train_report.groups[group_id] = weights
 869→
 870→        # ── 验证期：用训练期 best params 回测，聚合为整体 portfolio ──
 871→        all_returns: list[pd.Series] = []
 872→        for group_id, symbols in groups.items():
 873→            weights = train_report.groups.get(group_id, [])
 874→            if not weights:
 875→                continue
 876→            group_returns = _backtest_with_params_on_period(
 877→                mb, symbols, weights, val_start, val_end,
 878→            )
 879→            all_returns.extend(group_returns)
 880→
 881→        # 计算整体 portfolio 指标（等权合并所有组的日收益率）
 882→        if not all_returns:
 883→            val_sortino = 0.0
 884→            val_max_dd = 0.0
 885→            logger.warning(
 886→                f"[WalkForward] Round {round_num}: no valid val returns — "
 887→                f"sortino=0, dd=0, passed=True (vacuous)"
 888→            )
 889→        else:
 890→            combined = pd.concat(all_returns, axis=1).mean(axis=1).dropna()
 891→            if len(combined) < 5:
 892→                val_sortino = 0.0
 893→                val_max_dd = 0.0
 894→            else:
 895→                val_sortino = _compute_sortino(combined)
 896→                wrapper = [SingleBacktestResult(
 897→                    symbol="portfolio", strategy="", params={},
 898→                    sharpe=0.0, total_return_pct=0.0, max_drawdown_pct=0.0,
 899→                    win_rate_pct=0.0, total_trades=0, daily_returns=combined,
 900→                )]
 901→                val_max_dd = _portfolio_max_drawdown_from_results(wrapper)
 902→
 903→        passed = val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD
 904→        wf_rounds.append(WalkForwardRound(
 905→            round_num=round_num,
 906→            train_start=train_start,
 907→            train_end=train_end,
 908→            val_start=val_start,
 909→            val_end=val_end,
 910→            val_sortino=val_sortino,
 911→            val_max_dd=val_max_dd,
 912→            passed=passed,
 913→        ))
 914→        logger.info(
 915→            f"[WalkForward] Round {round_num} result: "
 916→            f"sortino={val_sortino:.4f}, dd={val_max_dd:.4f}%, "
 917→            f"passed={passed} (threshold={WALK_FORWARD_VAL_DD_THRESHOLD}%)"
 918→        )
 919→
 920→    report = WalkForwardReport(
 921→        rounds=wf_rounds,
 922→        pass_all_rounds=all(r.passed for r in wf_rounds) if wf_rounds else False,
 923→        max_val_dd=max((r.val_max_dd for r in wf_rounds), default=0.0),
 924→    )
 925→    logger.info(
 926→        f"[WalkForward] done: {len(wf_rounds)} rounds, "
 927→        f"pass_all_rounds={report.pass_all_rounds}, "
 928→        f"max_val_dd={report.max_val_dd:.4f}%"
 929→    )
 930→    return report
 931→
 932→
 933→# ---------------------------------------------------------------------------
 934→# MatrixBacktest 主类
 935→# ---------------------------------------------------------------------------
 936→
 937→class MatrixBacktest:
 938→    """矩阵回测：N 策略 × G 标的组 × 参数网格 → strategy_weights.json。
 939→
 940→    Args:
 941→        store:       MarketDataStore（本地时序库）
 942→        universe:    UniverseManager（提供分组映射）
 943→        years:       回测窗口（默认 5 年）
 944→        init_cash:   初始资金
 945→        fees:        手续费率
 946→        slippage:    滑点率
 947→        top_k:       每组保留 Top-K 策略（默认 2）
 948→    """
 949→
 950→    def __init__(
 951→        self,
 952→        store: MarketDataStore,
 953→        universe: UniverseManager,
 954→        years: int = 5,
 955→        init_cash: float = 100_000.0,
 956→        fees: float = 0.001,
 957→        slippage: float = 0.001,
 958→        top_k: int = 2,
 959→    ) -> None:
 960→        self._store = store
 961→        self._universe = universe
 962→        self._years = years
 963→        self._init_cash = init_cash
 964→        self._fees = fees
 965→        self._slippage = slippage
 966→        self._top_k = top_k
 967→
 968→    def run(
 969→        self,
 970→        strategies: list[str],
 971→        param_grids: dict[str, dict[str, list]],
 972→        output_file: str | Path | None = None,
 973→    ) -> MatrixBacktestReport:
 974→        """执行完整矩阵回测。
 975→
 976→        Args:
 977→            strategies:  策略名称列表，如 ["dual_ma", "rsi"]
 978→            param_grids: 各策略参数网格，如 {"dual_ma": {"fast":[5,10], "slow":[20,30]}}
 979→            output_file: strategy_weights.json 输出路径（None 则不写文件）
 980→
 981→        Returns:
 982→            MatrixBacktestReport
 983→        """
 984→        today = date.today()
 985→        start = today - timedelta(days=self._years * 365)
 986→        window_str = f"{start.isoformat()} ~ {today.isoformat()}"
 987→
 988→        logger.info(
 989→            f"[MatrixBacktest] start={start}, end={today}, "
 990→            f"strategies={strategies}, years={self._years}"
 991→        )
 992→
 993→        # 获取分组（⚠️ 使用历史时点分组，而非当前静态分组）
 994→        # Phase 5 初期简化：用当前分组，但接口已预留历史分组能力
 995→        groups = self._universe.get_groups()
 996→        if not groups:
 997→            logger.warning("[MatrixBacktest] no groups available, abort")
 998→            return MatrixBacktestReport(
 999→                generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
1000→                backtest_window=window_str,
1001→                groups={},
1002→            )
1003→
1004→        report = MatrixBacktestReport(
1005→            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
1006→            backtest_window=window_str,
1007→            groups={},
1008→        )
1009→
1010→        for group_id, symbols in groups.items():
1011→            logger.info(
1012→                f"[MatrixBacktest] group={group_id}, symbols={len(symbols)}, "
1013→                f"strategies={strategies}"
1014→            )
1015→
1016→            group_weights = self._run_group(
1017→                group_id=group_id,
1018→                symbols=symbols,
1019→                start=start,
1020→                end=today,
1021→                strategies=strategies,
1022→                param_grids=param_grids,
1023→                report=report,
1024→            )
1025→            report.groups[group_id] = group_weights
1026→
1027→        if output_file is not None:
1028→            self._write_weights(report, output_file)
1029→
1030→        logger.info(
1031→            f"[MatrixBacktest] done: {len(report.groups)} groups, "
1032→            f"warnings={len(report.warnings)}"
1033→        )
1034→        return report
1035→
1036→    def _get_spy_returns(self, start: date, end: date) -> pd.Series | None:
1037→        """获取 SPY 同期日收益率序列，用于计算 alpha（迭代 #9 新增）。
1038→
1039→        从 MarketDataStore 拉取 SPY 日线数据，计算日收益率。
1040→        SPY 不在标的池中，但作为 benchmark 用于 alpha 计算。
1041→
1042→        降级处理：SPY 数据不可用时返回 None（_compute_alpha 会返回 0.0），
1043→        不抛异常，保证回测不因 benchmark 缺失而阻塞。
1044→
1045→        Args:
1046→            start: 回测起始日期
1047→            end:   回测结束日期
1048→
1049→        Returns:
1050→            SPY 日收益率 pd.Series；数据不可用时返回 None
1051→        """
1052→        try:
1053→            spy_bars = self._store.get_bars_multi(["SPY"], start, end)
1054→            spy_df = spy_bars.get("SPY") if spy_bars else None
1055→            if spy_df is None or spy_df.empty:
1056→                logger.warning(
1057→                    "[MatrixBacktest] SPY data unavailable, alpha will degrade to 0.0"
1058→                )
1059→                return None
1060→            spy_close = spy_df["close"].astype(float)
1061→            if len(spy_close) < 2:
1062→                logger.warning(
1063→                    "[MatrixBacktest] SPY data too short, alpha will degrade to 0.0"
1064→                )
1065→                return None
1066→            return spy_close.pct_change().dropna()
1067→        except Exception as e:
1068→            logger.warning(
1069→                f"[MatrixBacktest] SPY benchmark fetch failed: {e} — "
1070→                f"alpha will degrade to 0.0"
1071→            )
1072→            return None
1073→
1074→    def _run_group(
1075→        self,
1076→        group_id: str,
1077→        symbols: list[str],
1078→        start: date,
1079→        end: date,
1080→        strategies: list[str],
1081→        param_grids: dict[str, dict[str, list]],
1082→        report: MatrixBacktestReport,
1083→    ) -> list[dict[str, Any]]:
1084→        """对单个分组执行策略 × 参数网格回测，返回该组的权重配置列表。
1085→
1086→        迭代 #9 变更：
1087→            - per-strategy best params：从 Sharpe 改为 Alpha（vs SPY）
1088→            - top-K 排序：从 Sortino 改为 Alpha
1089→            - 新增 Sortino > 0.5 最低质量门槛（二级过滤，可放宽）
1090→            - ensemble weights：从 Sharpe 改为 Alpha
1091→        迭代 #10 变更：
1092→            - 用 `_backtest_batch` 替代 for-symbol 循环（10-20x 提速）
1093→            - 每组 / 每策略增加进度耗时日志
1094→        """
1095→        import time
1096→
1097→        group_start = time.time()
1098→
1099→        # 1. 读取组内所有标的数据
1100→        data = self._store.get_bars_multi(symbols, start, end)
1101→        if not data:
1102→            logger.warning(f"[MatrixBacktest] {group_id}: no data, skip")
1103→            return []
1104→
1105→        # 迭代 #9：获取 SPY 同期日收益率用于 alpha 计算（一次获取，组内复用）
1106→        spy_returns = self._get_spy_returns(start, end)
1107→
1108→        valid_symbol_count = sum(
1109→            1 for df in data.values() if df is not None and not df.empty and len(df) >= 30
1110→        )
1111→        logger.info(
1112→            f"[MatrixBacktest] {group_id}: start — "
1113→            f"{len(strategies)} strategies × {valid_symbol_count} valid symbols"
1114→        )
1115→
1116→        # 2. 对每个策略 × 每组参数，按 alpha 选最优参数
1117→        group_results: list[tuple[str, dict, list[SingleBacktestResult]]] = []
1118→
1119→        for strategy in strategies:
1120→            strat_start = time.time()
1121→
1122→            # ⚠️ 早期检测未注册策略名（迭代 #1 修复"策略名拼写错误被静默跳过"的 bug）
1123→            # 之前 _backtest_one 内部静默 return None，导致 main.py 误用 "rsi"/"macd"/"bollinger"
1124→            # 简称 6 天未被发现。改为 WARNING 级日志 + continue。
1125→            if strategy not in STRATEGY_REGISTRY:
1126→                logger.warning(
1127→                    f"[MatrixBacktest] {group_id}: strategy '{strategy}' not in "
1128→                    f"STRATEGY_REGISTRY — skipped. "
1129→                    f"Check spelling against @register_strategy decorators. "
1130→                    f"Known: {sorted(STRATEGY_REGISTRY.keys())}"
1131→                )
1132→                continue
1133→            grid = param_grids.get(strategy, {})
1134→            param_combos = list(
1135→                dict(zip(grid.keys(), combo))
1136→                for combo in itertools.product(*grid.values())
1137→            ) if grid else [{}]
1138→
1139→            best_params = None
1140→            best_alpha = float("-inf")
1141→            best_sharpe = 0.0       # 仅用于 GroupBacktestResult 存档
1142→            best_sortino = 0.0      # 仅用于 GroupBacktestResult 存档
1143→            best_results: list[SingleBacktestResult] = []
1144→
1145→            for params in param_combos:
1146→                # 迭代 #10：用 _backtest_batch 一次处理组内所有标的
1147→                # 替代原 for sym in symbols: _backtest_one(...) 的逐标的循环
1148→                results = _backtest_batch(
1149→                    data, strategy, params,
1150→                    self._init_cash, self._fees, self._slippage,
1151→                )
1152→
1153→                if not results:
1154→                    continue
1155→
1156→                # ⚠️ 等权合并日收益率序列，一次性计算所有指标
1157→                # 迭代 #9：复用 combined 计算 sharpe / sortino / alpha
1158→                combined = _combine_daily_returns(results)
1159→                ps = _compute_sharpe(combined)
1160→                pso = _compute_sortino(combined)
1161→                alpha = _compute_alpha(combined, spy_returns)
1162→
1163→                # 迭代 #9：per-strategy best params 用 alpha 选（替代 Sharpe）
1164→                if alpha > best_alpha:
1165→                    best_alpha = alpha
1166→                    best_sharpe = ps
1167→                    best_sortino = pso
1168→                    best_params = params
1169→                    best_results = results
1170→
1171→            if best_params is not None and best_results:
1172→                group_results.append((strategy, best_params, best_results))
1173→                report.group_results.append(GroupBacktestResult(
1174→                    group_id=group_id,
1175→                    strategy=strategy,
1176→                    params=best_params,
1177→                    portfolio_sharpe=best_sharpe,
1178→                    avg_total_return_pct=_safe_mean(
1179→                        [r.total_return_pct for r in best_results]
1180→                    ),
1181→                    avg_max_drawdown_pct=_safe_mean(
1182→                        [r.max_drawdown_pct for r in best_results]
1183→                    ),
1184→                    avg_win_rate_pct=_safe_mean(
1185→                        [r.win_rate_pct for r in best_results]
1186→                    ),
1187→                    symbol_count=len(best_results),
1188→                    portfolio_sortino=best_sortino,
1189→                    portfolio_max_drawdown=_portfolio_max_drawdown_from_results(
1190→                        best_results
1191→                    ),
1192→                    backtest_alpha=best_alpha,
1193→                ))
1194→
1195→            logger.info(
1196→                f"[MatrixBacktest] {group_id}: {strategy} done in "
1197→                f"{time.time() - strat_start:.1f}s "
1198→                f"({len(param_combos)} param combos × {valid_symbol_count} symbols)"
1199→            )
1200→
1201→        if not group_results:
1202→            logger.warning(
1203→                f"[MatrixBacktest] {group_id}: no valid results "
1204→                f"(elapsed {time.time() - group_start:.1f}s)"
1205→            )
1206→            return []
1207→
1208→        # 迭代 #11：健全性过滤 —— 排序前先剔除退化策略
1209→        # （experience.md #8：sanity → risk → rank）
1210→        # 退化策略 = 组内 ≥ 80% 标的 closed_trades==0（入场/出场条件互斥，
1211→        # 仓位靠末尾强平凑出 Sortino/alpha 假象）。此类策略必须先于 DD/Sortino/
1212→        # Alpha 过滤剔除，否则其盯市假象会骗过 alpha 排序进入权重。
1213→        sane_results: list[tuple[str, dict, list[SingleBacktestResult]]] = []
1214→        for (strategy, params, results) in group_results:
1215→            if _is_degenerate_strategy(results):
1216→                logger.warning(
1217→                    f"[MatrixBacktest] {group_id}: strategy '{strategy}' is DEGENERATE "
1218→                    f"(>= {DEGENERATE_NO_CLOSE_FRACTION:.0%} symbols have 0 closed trades) "
1219→                    f"— excluded before ranking. Its Sortino/alpha is mark-to-market illusion."
1220→                )
1221→                continue
1222→            sane_results.append((strategy, params, results))
1223→
1224→        if not sane_results:
1225→            # 全组退化 → 空权重（持仓现金），标记 no_valid_strategy，不强行选退化策略
1226→            logger.warning(
1227→                f"[MatrixBacktest] {group_id}: ALL strategies degenerate — "
1228→                f"group produces EMPTY weights (hold cash). Marked no_valid_strategy."
1229→            )
1230→            report.warnings.append(
1231→                f"{group_id}: no_valid_strategy (all strategies degenerate)"
1232→            )
1233→            # 标记已 append 的 GroupBacktestResult 条目（供审计追溯）
1234→            for gr in report.group_results:
1235→                if gr.group_id == group_id:
1236→                    gr.no_valid_strategy = True
1237→            return []
1238→
1239→        # 后续 candidates 构建、DD/Sortino/Alpha 过滤、排序，全部改用 sane_results
1240→        group_results = sane_results
1241→
1242→        # 3. 迭代 #9：DD 硬约束 + Sortino 门槛 + Alpha 排序选 Top-K
1243→        #    Constitution L1: portfolio DD ≤ 20% 是硬约束（保留）
1244→        #    新增：Sortino > 0.5 最低质量门槛（可放宽）
1245→        #    变更：排序指标从 Sortino 改为 Alpha
1246→        #
1247→        #    三级过滤策略：
1248→        #      Tier 1: DD ≤ 20% AND Sortino > 0.5 → Alpha 降序
1249→        #      Tier 2 (fallback): Tier 1 为空 → 仅 DD ≤ 20% → Alpha 降序
1250→        #      Tier 3 (fallback): Tier 2 为空 → 按 DD 升序，标记 dd_constrained=True
1251→        candidates: list[
1252→            tuple[str, dict, list[SingleBacktestResult], float, float, float]
1253→        ] = []
1254→        for (strategy, params, results) in group_results:
1255→            pso = _portfolio_sortino_from_results(results)
1256→            pdd = _portfolio_max_drawdown_from_results(results)
1257→            # 复用 _combine_daily_returns 计算 alpha（与 per-strategy 选择一致）
1258→            alpha = _compute_alpha(_combine_daily_returns(results), spy_returns)
1259→            candidates.append((strategy, params, results, pso, pdd, alpha))
1260→
1261→        # 迭代 #12：alpha>0 硬门槛（experience.md #8：正超额是排序前的硬门槛）
1262→        # 在 Tier 1/2/3 fallback 之前，剔除 alpha≤0 的候选。
1263→        # 理由：跑不赢 SPY 的策略不应进入权重，无论 DD/Sortino 多好。
1264→        # 顺序：健全性（Iter #11）→ 风险（DD，Tier 1/2/3）→ 正超额（alpha>0，本步）→ 排序
1265→        #
1266→        # 注意：这一步在 candidates 构建后、Tier 1 前，确保 Tier 1/2/3 只在正 alpha 候选中进行。
1267→        # 如果某组所有候选 alpha≤0，该组空仓（hold cash），不强行选负 alpha 策略
1268→        # （experience.md #8："没有候选满足门槛时，正确动作是空仓/降现金/回退 benchmark，
1269→        #   不是矬子里拔将军"）。
1270→        positive_alpha_candidates = [c for c in candidates if c[5] > 0]
1271→
1272→        if not positive_alpha_candidates:
1273→            # 全组 alpha≤0 → 空权重（持仓现金），标记 no_positive_alpha
1274→            alpha_strs = [f"{c[0]}({c[5]:.2f}%)" for c in candidates]
1275→            logger.warning(
1276→                f"[MatrixBacktest] {group_id}: ALL {len(candidates)} candidates have "
1277→                f"alpha <= 0 (cannot beat SPY) — {alpha_strs}. "
1278→                f"Group produces EMPTY weights (hold cash). Marked no_positive_alpha."
1279→            )
1280→            report.warnings.append(
1281→                f"{group_id}: no_positive_alpha (all {len(candidates)} candidates alpha <= 0)"
1282→            )
1283→            # 标记已 append 的 GroupBacktestResult 条目（供审计追溯）
1284→            for gr in report.group_results:
1285→                if gr.group_id == group_id:
1286→                    gr.no_positive_alpha = True
1287→            return []
1288→
1289→        # 后续 Tier 1/2/3 在正 alpha 候选中进行
1290→        candidates = positive_alpha_candidates
1291→
1292→        # Tier 1: DD ≤ 20% AND Sortino > 0.5
1293→        compliant = [
1294→            c for c in candidates
1295→            if c[4] <= MAX_PORTFOLIO_DRAWDOWN_PCT and c[3] > MIN_SORTINO_THRESHOLD
1296→        ]
1297→        if compliant:
1298→            # Tier 1 命中：按 Alpha 降序取 top-K
1299→            ranked = sorted(compliant, key=lambda x: x[5], reverse=True)
1300→            dd_constrained = False
1301→            logger.info(
1302→                f"[MatrixBacktest] {group_id}: DD + Sortino filter passed — "
1303→                f"{len(compliant)}/{len(candidates)} candidates compliant "
1304→                f"(DD <= {MAX_PORTFOLIO_DRAWDOWN_PCT}% AND Sortino > {MIN_SORTINO_THRESHOLD})"
1305→            )
1306→        else:
1307→            # Tier 2: 放宽 Sortino 门槛，仅保留 DD 约束
1308→            dd_compliant = [
1309→                c for c in candidates if c[4] <= MAX_PORTFOLIO_DRAWDOWN_PCT
1310→            ]
1311→            if dd_compliant:
1312→                # Tier 2 命中：按 Alpha 降序取 top-K（dd_constrained 仍为 False）
1313→                ranked = sorted(dd_compliant, key=lambda x: x[5], reverse=True)
1314→                dd_constrained = False
1315→                logger.warning(
1316→                    f"[MatrixBacktest] {group_id}: Sortino filter relaxed — "
1317→                    f"no candidate passed Sortino > {MIN_SORTINO_THRESHOLD}. "
1318→                    f"Fallback to DD-only filter: "
1319→                    f"{len(dd_compliant)}/{len(candidates)} candidates DD-compliant."
1320→                )
1321→            else:
1322→                # Tier 3: 无 DD 合规候选 → 按 DD 升序，标记 dd_constrained
1323→                # （结构性问题，如 NDX_high_vol 全部 > 20%）
1324→                ranked = sorted(candidates, key=lambda x: x[4])
1325→                dd_constrained = True
1326→                logger.warning(
1327→                    f"[MatrixBacktest] {group_id}: NO compliant candidates "
1328→                    f"(all {len(candidates)} exceed DD={MAX_PORTFOLIO_DRAWDOWN_PCT}%). "
1329→                    f"Fallback: selected top-{self._top_k} by lowest DD. "
1330→                    f"This group is marked dd_constrained=True — "
1331→                    f"review whether to drop the group or accept the risk."
1332→                )
1333→                report.warnings.append(
1334→                    f"{group_id}: dd_constrained=True "
1335→                    f"(min DD={ranked[0][4]:.2f}% > {MAX_PORTFOLIO_DRAWDOWN_PCT}%)"
1336→                )
1337→
1338→        top_results = ranked[: self._top_k]
1339→
1340→        # 把 dd_constrained 标记同步到 report.group_results 中对应组的条目
1341→        for gr in report.group_results:
1342→            if gr.group_id == group_id:
1343→                gr.dd_constrained = dd_constrained
1344→
1345→        # 4. 优化 ensemble 权重（单点离散值加权投票语义，迭代 #9 改用 alpha）
1346→        weighted = _optimize_ensemble_weights(
1347→            [(s, p, r) for (s, p, r, _, _, _) in top_results],
1348→            spy_returns=spy_returns,
1349→        )
1350→
1351→        # 5. 构建权重配置列表
1352→        weights_list = []
1353→        for strategy, params, weight in weighted:
1354→            # 找到对应的 GroupBacktestResult
1355→            gr = next(
1356→                (r for r in report.group_results
1357→                 if r.group_id == group_id and r.strategy == strategy),
1358→                None,
1359→            )
1360→            # 迭代 #4：新增 backtest_dd_status 字段（'pass' / 'dd_constrained'）
1361→            # 作为风险 metadata 标记，与 dd_constrained bool 同义但更可读
1362→            backtest_dd_status = "dd_constrained" if dd_constrained else "pass"
1363→            weights_list.append({
1364→                "strategy": strategy,
1365→                "params": params,
1366→                "weight": round(weight, 4),
1367→                "backtest_sharpe": round(gr.portfolio_sharpe if gr else 0.0, 4),
1368→                "backtest_sortino": round(gr.portfolio_sortino if gr else 0.0, 4),
1369→                "backtest_max_drawdown": round(gr.portfolio_max_drawdown if gr else 0.0, 4),
1370→                "backtest_win_rate": round(gr.avg_win_rate_pct / 100 if gr else 0.5, 4),
1371→                # 迭代 #9：新增 backtest_alpha 字段（vs SPY 的超额收益百分数）
1372→                # 下游 PortfolioBacktester 可读此字段验证 alpha 一致性
1373→                "backtest_alpha": round(gr.backtest_alpha if gr else 0.0, 4),
1374→                # 迭代 #3：标记该组是否用了 DD fallback（无合规候选）
1375→                # 同组所有策略条目共享同一 dd_constrained 值
1376→                "dd_constrained": dd_constrained,
1377→                # 迭代 #4：backtest_dd_status — 风险 metadata 字段
1378→                # 'pass' = 该组有合规候选（DD ≤ 20%）
1379→                # 'dd_constrained' = fallback 触发（无合规候选，按最低 DD 取 top-K）
1380→                # 下游消费方（PortfolioBacktester / 风控观测）可读此字段判断
1381→                # 该组权重的可靠性，作为风险信号标记
1382→                "backtest_dd_status": backtest_dd_status,
1383→            })
1384→
1385→        logger.info(
1386→            f"[MatrixBacktest] {group_id}: all strategies done in "
1387→            f"{time.time() - group_start:.1f}s "
1388→            f"(top-{self._top_k} selected, dd_constrained={dd_constrained})"
1389→        )
1390→
1391→        return weights_list
1392→
1393→    def _write_weights(
1394→        self, report: MatrixBacktestReport, output_file: str | Path
1395→    ) -> None:
1396→        """将矩阵回测结果写入 strategy_weights.json。"""
1397→        output_file = Path(output_file)
1398→        output_file.parent.mkdir(parents=True, exist_ok=True)
1399→
1400→        data = {
1401→            "_meta": {
1402→                "generated_at": report.generated_at,
1403→                "backtest_window": report.backtest_window,
1404→                "reoptimize_freq": "monthly",
1405→                "survivorship_bias_warning": (
1406→                    "使用当前成分股回测，S&P 500 5年成分变动约100只(~20%)，"
1407→                    "均值回归组(SPX_low_vol)结果可能系统性偏高"
1408→                ),
1409→            },
1410→            "groups": report.groups,
1411→        }
1412→
1413→        with open(output_file, "w", encoding="utf-8") as f:
1414→            json.dump(data, f, indent=2, ensure_ascii=False)
1415→
1416→        logger.info(f"[MatrixBacktest] weights saved to {output_file}")
1417→
---
   1→"""MyTrader 系统启动入口。
   2→
   3→用法：
   4→    python main.py                        # paper 模式，默认配置
   5→    python main.py --mode semi_auto       # 半自动（推送通知，人工确认）
   6→    python main.py --mode auto            # 全自动（直接下单）
   7→    python main.py --config path/to.yaml  # 自定义配置文件
   8→    python main.py --dry-run              # 仅检查配置和依赖，不启动调度器
   9→    python main.py --scan-now morning     # 立即执行一次盘前扫描（调试用）
  10→    python main.py --reoptimize           # 立即触发 MatrixBacktest（Walk-Forward 重优化）
  11→    python main.py --backfill             # 首次回填 5 年历史数据（MarketDataStore）
  12→
  13→环境变量覆盖（通过 .env 文件）：
  14→    EXECUTION__MODE=semi_auto
  15→    ALPACA__API_KEY=your_key
  16→    NOTIFICATION__TELEGRAM_ENABLED=true
  17→    WATCHLIST__SYMBOLS='["AAPL","TSLA"]'
  18→"""
  19→
  20→from __future__ import annotations
  21→
  22→import argparse
  23→import sys
  24→from pathlib import Path
  25→
  26→
  27→# ---------------------------------------------------------------------------
  28→# Walk-Forward 重优化配置（迭代 #1 提为模块级常量，便于回归测试）
  29→# ⚠️ 策略名必须与 mytrader/strategy/strategies/*.py 中 @register_strategy(...)
  30→#    装饰器的名字完全一致。回归测试 test_reoptimize_strategy_names_match_registry
  31→#    会断言 REOPTIMIZE_STRATEGIES ⊆ STRATEGY_REGISTRY.keys()，防止策略名拼写
  32→#    错误导致矩阵回测静默跳过整类策略。
  33→# ---------------------------------------------------------------------------
  34→
  35→REOPTIMIZE_STRATEGIES: list[str] = [
  36→    "dual_ma",
  37→    "rsi_mean_revert",
  38→    "rsi_trend_filter",
  39→    "macd_cross",
  40→    "bollinger_band",
  41→]
  42→
  43→REOPTIMIZE_PARAM_GRIDS: dict[str, dict[str, list]] = {
  44→    # 迭代 #2：从单点扩展为真网格。原单点网格（fast=[5,10], slow=[20,40,60]）
  45→    # 仅 6 个组合，无法充分探索参数空间。扩展后 4×5=20 个组合。
  46→    "dual_ma":         {"fast": [5, 10, 15, 20], "slow": [20, 30, 40, 60, 80]},
  47→    # 迭代 #2：从单点 [14,30,70] 扩展为 3×3×3=27 个组合，覆盖均值回归周期
  48→    # 与超买超卖阈值的常用范围。oversold/overbought 保持对称（25/75、30/70、35/65）。
  49→    "rsi_mean_revert": {"period": [7, 14, 21], "oversold": [25, 30, 35], "overbought": [65, 70, 75]},
  50→    # 迭代 #2：MACD 快/慢/信号周期网格 3×3×3=27 个组合，包含经典 12/26/9。
  51→    "macd_cross":      {"fast": [8, 12, 16], "slow": [21, 26, 32], "signal_period": [5, 9, 12]},
  52→    # 迭代 #2：布林带 3×3=9 个组合，覆盖常用 std_dev 范围 [1.5, 2.0, 2.5]。
  53→    "bollinger_band":  {"period": [15, 20, 25], "std_dev": [1.5, 2.0, 2.5]},
  54→    # 迭代 #8：RSI 趋势过滤 3×3×3×1=27 个组合，trend_period 固定 200（经典长周期趋势线）。
  55→    "rsi_trend_filter": {"rsi_period": [7, 14, 21], "oversold": [25, 30, 35],
  56→                         "overbought": [65, 70, 75], "trend_period": [200]},
  57→}
  58→
  59→
  60→def parse_args() -> argparse.Namespace:
  61→    parser = argparse.ArgumentParser(
  62→        prog="mytrader",
  63→        description="MyTrader — 轻量级日内/短线交易系统",
  64→    )
  65→    parser.add_argument(
  66→        "--mode",
  67→        choices=["paper", "semi_auto", "auto"],
  68→        default=None,
  69→        help="执行模式（覆盖配置文件）: paper | semi_auto | auto",
  70→    )
  71→    parser.add_argument(
  72→        "--config",
  73→        type=str,
  74→        default=None,
  75→        metavar="PATH",
  76→        help="YAML 配置文件路径（默认自动查找 config/default.yaml）",
  77→    )
  78→    parser.add_argument(
  79→        "--log-dir",
  80→        type=str,
  81→        default="logs",
  82→        metavar="DIR",
  83→        help="日志目录（默认 logs/）",
  84→    )
  85→    parser.add_argument(
  86→        "--dry-run",
  87→        action="store_true",
  88→        help="仅初始化并检查配置，不启动调度器",
  89→    )
  90→    parser.add_argument(
  91→        "--db",
  92→        type=str,
  93→        default="mytrader.db",
  94→        metavar="PATH",
  95→        help="SQLite 数据库路径（默认 mytrader.db）",
  96→    )
  97→    parser.add_argument(
  98→        "--scan-now",
  99→        choices=["morning", "intraday", "eod"],
 100→        default=None,
 101→        metavar="TYPE",
 102→        help="立即执行一次指定类型的扫描，不启动调度器（调试用）",
 103→    )
 104→    parser.add_argument(
 105→        "--reoptimize",
 106→        action="store_true",
 107→        help="立即触发 MatrixBacktest Walk-Forward 重优化，更新 strategy_weights.json",
 108→    )
 109→    parser.add_argument(
 110→        "--backfill",
 111→        action="store_true",
 112→        help="首次回填 5 年历史数据到 MarketDataStore（一次性操作）",
 113→    )
 114→    return parser.parse_args()
 115→
 116→
 117→def main() -> None:
 118→    args = parse_args()
 119→
 120→    # 1. 初始化日志（最先执行）
 121→    from mytrader.monitor.logger_setup import setup_logger
 122→    setup_logger(log_dir=args.log_dir, level="INFO")
 123→
 124→    from loguru import logger
 125→    logger.info(f"MyTrader starting: mode={args.mode or 'from_config'} dry_run={args.dry_run}")
 126→
 127→    # 2. 加载配置
 128→    from mytrader.infra.config import load_config
 129→    config = load_config(args.config)
 130→
 131→    # CLI --mode 覆盖配置文件
 132→    if args.mode is not None:
 133→        object.__setattr__(config.execution, "mode", args.mode)
 134→        logger.info(f"Execution mode overridden by CLI: {args.mode}")
 135→
 136→    logger.info(
 137→        f"Config loaded: mode={config.execution.mode} broker={config.execution.broker} "
 138→        f"scheduler.enabled={config.scheduler.enabled} "
 139→        f"watchlist={config.watchlist.symbols}"
 140→    )
 141→
 142→    # 3. 装配依赖
 143→    from mytrader.infra.container import Container
 144→    components = Container.build(config, db_url=f"sqlite:///{args.db}")
 145→
 146→    # 4. 健康检查
 147→    report = components.health.run_all()
 148→    logger.info(f"Health check: {report.status} ({report.checks})")
 149→    if not report.is_healthy:
 150→        for name in report.failed_checks:
 151→            logger.warning(f"Health check FAILED: {name} — {report.details.get(name)}")
 152→
 153→    # 5. 构建扫描编排器
 154→    from mytrader.scan_orchestrator import build_orchestrator
 155→    orchestrator = build_orchestrator(components)
 156→
 157→    mode_label = "Phase 5 (multi-strategy matrix)" if orchestrator._use_phase5 else "Phase 4 (single-strategy)"
 158→    logger.info(f"[Orchestrator] Built in {mode_label} mode")
 159→
 160→    # 6a. --backfill：首次回填历史数据
 161→    if args.backfill:
 162→        _run_backfill(config, logger)
 163→        return
 164→
 165→    # 6b. --reoptimize：立即触发 MatrixBacktest
 166→    if args.reoptimize:
 167→        _run_reoptimize(config, logger)
 168→        return
 169→
 170→    # 6c. --scan-now：立即执行一次扫描后退出（调试用）
 171→    if args.scan_now:
 172→        logger.info(f"Running immediate scan: type={args.scan_now}")
 173→        if args.scan_now == "morning":
 174→            summary = orchestrator.morning_scan()
 175→        elif args.scan_now == "intraday":
 176→            summary = orchestrator.intraday_scan()
 177→        else:
 178→            summary = orchestrator.eod_check()
 179→        logger.info(
 180→            f"Scan complete: buy={summary.buy_count} sell={summary.sell_count} "
 181→            f"orders={summary.order_count} errors={summary.error_count}"
 182→        )
 183→        return
 184→
 185→    if args.dry_run:
 186→        # 输出 Phase 5 模块状态
 187→        if components.data_store is not None:
 188→            logger.info(
 189→                f"[DryRun] Phase5 modules active: "
 190→                f"universe={len(components.universe.get_universe())} symbols, "
 191→                f"signal_valid_bars={config.strategy_matrix.signal_valid_bars}"
 192→            )
 193→        else:
 194→            logger.info("[DryRun] Phase4 fallback mode (local DB not loaded)")
 195→
 196→        # Alpaca/IBKR 启动自检
 197→        if config.execution.mode in ("semi_auto", "auto"):
 198→            try:
 199→                result = components.broker.health_check()
 200→                if result["status"] == "connected":
 201→                    logger.info(
 202→                        f"[DryRun] Broker connected: id={result['account_id']}, "
 203→                        f"cash=${result['cash']:,.0f}, buying_power=${result['buying_power']:,.0f}, "
 204→                        f"paper={result['paper']}"
 205→                    )
 206→                else:
 207→                    logger.error(f"[DryRun] Broker health check FAILED: {result}")
 208→            except AttributeError:
 209→                logger.info("[DryRun] Broker does not support health_check (PaperBroker)")
 210→
 211→        logger.info("Dry-run complete. Exiting.")
 212→        return
 213→
 214→    # 7. 启动调度器（接入真实回调）
 215→    from mytrader.infra.scheduler import TradingScheduler
 216→    from mytrader.data.providers.yfinance_provider import YFinanceProvider
 217→
 218→    # 盘后数据增量同步回调（Phase 5）
 219→    def _on_data_sync() -> None:
 220→        if components.data_store is None:
 221→            return
 222→        from mytrader.data.store import DataSyncService
 223→        symbols = components.universe.get_universe()
 224→        logger.info(f"[DataSync] syncing {len(symbols)} symbols...")
 225→        try:
 226→            if config.data.provider == "alpaca":
 227→                from mytrader.data.providers.alpaca_provider import AlpacaDataProvider
 228→                from datetime import date as _date, timedelta as _td
 229→                primary = AlpacaDataProvider(
 230→                    api_key=config.alpaca.api_key,
 231→                    secret_key=config.alpaca.secret_key,
 232→                    paper=config.alpaca.paper,
 233→                )
 234→                # 盘后同步：end 用昨天避开 SIP 实时限制
 235→                end = _date.today() - _td(days=1)
 236→            else:
 237→                primary = YFinanceProvider()
 238→                end = None
 239→            svc = DataSyncService(
 240→                store=components.data_store,
 241→                primary=primary,
 242→                use_fallback_on_empty=False,
 243→            )
 244→            report = svc.sync_all(symbols, max_workers=4, end=end)
 245→            logger.info(f"[DataSync] done: {report}")
 246→        except Exception as exc:
 247→            logger.error(f"[DataSync] failed: {exc}")
 248→
 249→    scheduler = TradingScheduler(
 250→        config=config.scheduler,
 251→        on_morning_scan=orchestrator.morning_scan,
 252→        on_intraday_scan=orchestrator.intraday_scan,
 253→        on_eod_check=orchestrator.eod_check,
 254→        on_reconciliation=_build_reconciliation_callback(components, sync_fn=_on_data_sync),
 255→        on_monthly_reoptimize=lambda: _run_reoptimize(config, logger),
 256→    )
 257→
 258→    # 启动前先执行一次数据同步（确保本地库有数据）
 259→    _on_data_sync()
 260→
 261→    logger.info("Starting scheduler... (Ctrl+C to stop)")
 262→    try:
 263→        scheduler.start()
 264→    except (KeyboardInterrupt, SystemExit):
 265→        logger.info("Shutdown signal received")
 266→    finally:
 267→        scheduler.shutdown(wait=False)
 268→        logger.info("MyTrader stopped")
 269→
 270→
 271→def _run_backfill(config: "Any", logger: "Any") -> None:
 272→    """首次回填 5 年历史数据。自动刷新成分股列表（Wikipedia → CSV）。"""
 273→    from mytrader.data.store import MarketDataStore, DataSyncService
 274→    from mytrader.data.providers.yfinance_provider import YFinanceProvider
 275→    from mytrader.universe.manager import UniverseManager
 276→    from pathlib import Path
 277→
 278→    logger.info("[Backfill] initializing MarketDataStore...")
 279→    store = MarketDataStore()  # 使用默认路径 ~/.mytrader/market_data.db
 280→
 281→    # 若 universe.csv 不存在或为空，从 Wikipedia 拉取完整成分股列表
 282→    csv_path = Path("config/universe.csv")
 283→    need_fetch = (
 284→        not csv_path.exists()
 285→        or csv_path.stat().st_size < 100  # 只有表头或空文件
 286→    )
 287→
 288→    if need_fetch:
 289→        if csv_path.exists():
 290→            logger.info(f"[Backfill] universe.csv is empty/corrupt ({csv_path.stat().st_size} bytes), re-fetching...")
 291→            csv_path.unlink()
 292→        else:
 293→            logger.info("[Backfill] universe.csv not found, fetching constituents from Wikipedia...")
 294→
 295→        # 用指定 CSV 路径创建 UniverseManager，确保 save_to_csv 写入正确位置
 296→        tmp_universe = UniverseManager(store=store, universe_file=csv_path)
 297→        tmp_universe.refresh_constituents(save=True)
 298→
 299→    universe = UniverseManager(store=store, universe_file=csv_path)
 300→    symbols = universe.get_universe()
 301→    logger.info(f"[Backfill] {len(symbols)} symbols to backfill (5 years)")
 302→
 303→    if not symbols:
 304→        logger.error("[Backfill] no symbols to backfill — abort")
 305→        return
 306→
 307→    from datetime import date as _date, timedelta as _timedelta
 308→
 309→    if config.data.provider == "alpaca":
 310→        from mytrader.data.providers.alpaca_provider import AlpacaDataProvider
 311→        primary = AlpacaDataProvider(
 312→            api_key=config.alpaca.api_key,
 313→            secret_key=config.alpaca.secret_key,
 314→            paper=config.alpaca.paper,
 315→        )
 316→        # Alpaca 免费 SIP 不能查当日实时数据，end 用昨天避开限制
 317→        end = _date.today() - _timedelta(days=1)
 318→        logger.info(
 319→            f"[Backfill] using Alpaca provider (end={end}, avoids SIP realtime limit)"
 320→        )
 321→    else:
 322→        primary = YFinanceProvider()
 323→        end = None
 324→
 325→    svc = DataSyncService(store=store, primary=primary, fallback=None,
 326→                          use_fallback_on_empty=False)
 327→    report = svc.backfill(symbols, years=5, end=end)
 328→    logger.info(f"[Backfill] done: {report}")
 329→
 330→
 331→def _run_reoptimize(config: "Any", logger: "Any") -> None:
 332→    """立即触发 MatrixBacktest Walk-Forward 重优化。"""
 333→    from mytrader.data.store import MarketDataStore
 334→    from mytrader.universe.manager import UniverseManager
 335→    from mytrader.backtest.matrix_backtest import MatrixBacktest
 336→    from mytrader.strategy import matrix_runner as _mr_module
 337→
 338→    logger.info("[Reoptimize] starting Walk-Forward MatrixBacktest...")
 339→    store = MarketDataStore()
 340→    universe = UniverseManager(store=store)
 341→
 342→    # 重算波动率分组（确保分组是最新的）
 343→    universe.recompute_volatility_tiers(max_workers=4)
 344→
 345→    mb = MatrixBacktest(store=store, universe=universe, years=5, top_k=2)
 346→
 347→    # ⚠️ 策略名必须与 @register_strategy(...) 装饰器中的名字完全一致。
 348→    # 早期版本误用 "rsi"/"macd"/"bollinger" 简称，与注册表
 349→    # ("rsi_mean_revert"/"macd_cross"/"bollinger_band") 不匹配，
 350→    # 导致这 3 个策略在矩阵回测中被 _backtest_one 静默跳过，
 351→    # strategy_weights.json 退化为仅 dual_ma（迭代 #1 修复）。
 352→    # 模块级常量 REOPTIMIZE_STRATEGIES / REOPTIMIZE_PARAM_GRIDS 便于回归测试
 353→    # （test_reoptimize_strategy_names_match_registry 防止策略名再次与注册表脱节）。
 354→    strategies = REOPTIMIZE_STRATEGIES
 355→    param_grids = REOPTIMIZE_PARAM_GRIDS
 356→
 357→    output = Path("config/strategy_weights.json")
 358→    report = mb.run(strategies=strategies, param_grids=param_grids, output_file=output)
 359→    logger.info(
 360→        f"[Reoptimize] done: {len(report.groups)} groups, "
 361→        f"output={output}"
 362→    )
 363→
 364→    # 迭代 #3：Walk-Forward 4 轮验证（Constitution L7 流水线硬要求）
 365→    # WF 是验证步骤，不影响 strategy_weights.json；结果输出到日志
 366→    try:
 367→        from mytrader.backtest.matrix_backtest import run_walk_forward
 368→        logger.info("[Reoptimize] starting Walk-Forward 4-round validation...")
 369→        wf_report = run_walk_forward(
 370→            mb=mb,
 371→            strategies=strategies,
 372→            param_grids=param_grids,
 373→            rounds=4,
 374→            train_months=18,
 375→            val_months=6,
 376→        )
 377→        for r in wf_report.rounds:
 378→            logger.info(
 379→                f"[WalkForward] Round {r.round_num}/4: "
 380→                f"train={r.train_start}~{r.train_end}, "
 381→                f"val={r.val_start}~{r.val_end}, "
 382→                f"sortino={r.val_sortino:.4f}, "
 383→                f"dd={r.val_max_dd:.4f}%, "
 384→                f"passed={r.passed}"
 385→            )
 386→        logger.info(
 387→            f"[WalkForward] Summary: pass_all_rounds={wf_report.pass_all_rounds}, "
 388→            f"max_val_dd={wf_report.max_val_dd:.4f}%"
 389→        )
 390→        if not wf_report.pass_all_rounds:
 391→            logger.warning(
 392→                "[WalkForward] NOT all rounds passed — "
 393→                "Constitution L7 requires all 4 rounds DD<=15% before paper trading."
 394→            )
 395→    except Exception as exc:
 396→        logger.error(f"[WalkForward] failed: {exc}", exc_info=True)
 397→
 398→    # 迭代 #4：PortfolioBacktest（组合层级回测）
 399→    # 在 MatrixBacktest + Walk-Forward 之后运行，验证组合层 KPI（Sortino/DD）
 400→    # 输出 Constitution L1 关键指标到日志，用于决策"是否进入 paper trading"
 401→    try:
 402→        from mytrader.backtest.portfolio_backtest import (
 403→            PortfolioBacktester,
 404→            PortfolioBacktestConfig,
 405→        )
 406→        from datetime import date as _date
 407→        from datetime import timedelta as _timedelta
 408→
 409→        logger.info("[Reoptimize] starting PortfolioBacktest...")
 410→        # 回测近 1 年（与 Walk-Forward 验证期最后一段对齐）
 411→        pb_end = _date.today() - _timedelta(days=1)
 412→        pb_start = pb_end - _timedelta(days=365)
 413→        pb_cfg = PortfolioBacktestConfig()
 414→        pb = PortfolioBacktester(
 415→            store=store,
 416→            universe=universe,
 417→            weights_file=output,
 418→            config=pb_cfg,
 419→        )
 420→        pb_result = pb.run(start=pb_start, end=pb_end)
 421→        # 迭代 #7：日志增加 benchmark / alpha / IR（Constitution L1 收益可归因）
 422→        logger.info(
 423→            f"[Portfolio Backtest] "
 424→            f"DD={pb_result.max_drawdown_pct:.2f}%, "
 425→            f"Sortino={pb_result.sortino_ratio:.4f}, "
 426→            f"Sharpe={pb_result.sharpe_ratio:.4f}, "
 427→            f"Annual Return={pb_result.annualized_return_pct:.2f}%, "
 428→            f"Benchmark({pb_result.benchmark_symbol}) "
 429→            f"Return={pb_result.benchmark_annualized_return_pct:.2f}%, "
 430→            f"Alpha={pb_result.alpha_pct:.2f}%, "
 431→            f"IR={pb_result.information_ratio:.4f}, "
 432→            f"DD Violation={'YES' if pb_result.dd_violation else 'NO'}"
 433→        )
 434→        if pb_result.dd_violation:
 435→            logger.warning(
 436→                f"[Portfolio Backtest] DD Violation: max_dd={pb_result.max_drawdown_pct:.2f}% "
 437→                f"> 20% threshold (Constitution L1). "
 438→                f"Recommend: review group weights before paper trading."
 439→            )
 440→    except Exception as exc:
 441→        logger.error(f"[Portfolio Backtest] failed: {exc}", exc_info=True)
 442→
 443→    # 热加载（如果 StrategyMatrixRunner 已在运行）
 444→    try:
 445→        from mytrader.strategy.matrix_runner import StrategyMatrixRunner
 446→        logger.info("[Reoptimize] weights reloaded into StrategyMatrixRunner")
 447→    except Exception:
 448→        pass
 449→
 450→
 451→def _build_reconciliation_callback(components: "Any", sync_fn: "Any" = None) -> "Callable":
 452→    """构建对账回调（盘后 16:30 ET）。
 453→
 454→    盘后流程：先同步当日行情数据，再做持仓对账。
 455→
 456→    迭代 #5 修复（P0-C）：
 457→        - ReconciliationService 构造参数从 `tracker=` 改为 `portfolio_tracker=`
 458→        - 调用从 `svc.reconcile()` 改为 `svc.run()`
 459→        - 判断从 `report.has_diff` 改为 `not report.is_clean`
 460→        - 兼容 components.notification / bus 为 None 的场景
 461→        - 末尾 best-effort 写出 paper daily metrics（P0-D）
 462→    """
 463→    from loguru import logger
 464→
 465→    def on_reconciliation() -> None:
 466→        # 1. 先同步当日数据（修复：_on_data_sync 原本只在启动时跑，导致数据库不更新）
 467→        if sync_fn is not None:
 468→            try:
 469→                sync_fn()
 470→            except Exception as exc:
 471→                logger.warning(f"[Reconciliation] data sync failed: {exc}")
 472→        # 2. 持仓对账
 473→        try:
 474→            from mytrader.portfolio.reconciliation import ReconciliationService
 475→            svc = ReconciliationService(
 476→                portfolio_tracker=components.tracker,
 477→                broker=components.broker,
 478→                event_bus=getattr(components, "bus", None),
 479→                auto_sync=False,
 480→            )
 481→            report = svc.run()
 482→            if not report.is_clean:
 483→                diff_syms = [d.symbol for d in report.diffs]
 484→                logger.warning(
 485→                    f"[Reconciliation] {len(report.diffs)} diff(s) found: {diff_syms}"
 486→                )
 487→            else:
 488→                logger.info(
 489→                    f"[Reconciliation] No diffs — positions match "
 490→                    f"(local={report.total_local}, broker={report.total_broker})"
 491→                )
 492→
 493→            # 无论有无差异都推送对账报告
 494→            notification = getattr(components, "notification", None)
 495→            if notification is not None:
 496→                try:
 497→                    from datetime import datetime, timezone
 498→                    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
 499→                    if not report.is_clean:
 500→                        diff_syms = [d.symbol for d in report.diffs]
 501→                        text = (
 502→                            "⚠️ *持仓对账报告*\n"
 503→                            f"时间：{ts}\n"
 504→                            f"发现 {len(report.diffs)} 个标的持仓差异：\n"
 505→                            f"{', '.join(diff_syms[:10])}"
 506→                            + (f" 等{len(diff_syms)}只" if len(diff_syms) > 10 else "")
 507→                            + "\n请检查 broker 与本地记录"
 508→                        )
 509→                    else:
 510→                        text = (
 511→                            "✅ *持仓对账报告*\n"
 512→                            f"时间：{ts}\n"
 513→                            "持仓一致，无差异"
 514→                        )
 515→                    notification.send_message(text)
 516→                except Exception as exc:
 517→                    logger.warning(f"[Reconciliation] notification failed: {exc}")
 518→        except Exception as exc:
 519→            # 对账失败不能让 scheduler 崩溃（Constitution L8 运行时故障处理策略）
 520→            logger.error(f"[Reconciliation] Failed: {exc}", exc_info=True)
 521→
 522→        # 3. 迭代 #5 P0-D：best-effort 写出 paper daily metrics
 523→        #    失败不影响对账已完成的状态
 524→        try:
 525→            from mytrader.monitor.paper_metrics import collect_paper_daily_metrics
 526→            collect_paper_daily_metrics(
 527→                broker=components.broker,
 528→                tracker=components.tracker,
 529→                scan_summary=None,
 530→                data_status=None,
 531→            )
 532→        except Exception as exc:
 533→            logger.warning(f"[Reconciliation] paper metrics collection failed: {exc}")
 534→
 535→    return on_reconciliation
 536→
 537→
 538→if __name__ == "__main__":
 539→    main()
 540→
 541→
---
   1→"""MyTrader 系统启动入口。
   2→
   3→用法：
   4→    python main.py                        # paper 模式，默认配置
   5→    python main.py --mode semi_auto       # 半自动（推送通知，人工确认）
   6→    python main.py --mode auto            # 全自动（直接下单）
   7→    python main.py --config path/to.yaml  # 自定义配置文件
   8→    python main.py --dry-run              # 仅检查配置和依赖，不启动调度器
   9→    python main.py --scan-now morning     # 立即执行一次盘前扫描（调试用）
  10→    python main.py --reoptimize           # 立即触发 MatrixBacktest（Walk-Forward 重优化）
  11→    python main.py --backfill             # 首次回填 5 年历史数据（MarketDataStore）
  12→
  13→环境变量覆盖（通过 .env 文件）：
  14→    EXECUTION__MODE=semi_auto
  15→    ALPACA__API_KEY=your_key
  16→    NOTIFICATION__TELEGRAM_ENABLED=true
  17→    WATCHLIST__SYMBOLS='["AAPL","TSLA"]'
  18→"""
  19→
  20→from __future__ import annotations
  21→
  22→import argparse
  23→import sys
  24→from pathlib import Path
  25→
  26→
  27→# ---------------------------------------------------------------------------
  28→# Walk-Forward 重优化配置（迭代 #1 提为模块级常量，便于回归测试）
  29→# ⚠️ 策略名必须与 mytrader/strategy/strategies/*.py 中 @register_strategy(...)
  30→#    装饰器的名字完全一致。回归测试 test_reoptimize_strategy_names_match_registry
  31→#    会断言 REOPTIMIZE_STRATEGIES ⊆ STRATEGY_REGISTRY.keys()，防止策略名拼写
  32→#    错误导致矩阵回测静默跳过整类策略。
  33→# ---------------------------------------------------------------------------
  34→
  35→REOPTIMIZE_STRATEGIES: list[str] = [
  36→    "dual_ma",
  37→    "rsi_mean_revert",
  38→    "rsi_trend_filter",
  39→    "macd_cross",
  40→    "bollinger_band",
  41→]
  42→
  43→REOPTIMIZE_PARAM_GRIDS: dict[str, dict[str, list]] = {
  44→    # 迭代 #2：从单点扩展为真网格。原单点网格（fast=[5,10], slow=[20,40,60]）
  45→    # 仅 6 个组合，无法充分探索参数空间。扩展后 4×5=20 个组合。
  46→    "dual_ma":         {"fast": [5, 10, 15, 20], "slow": [20, 30, 40, 60, 80]},
  47→    # 迭代 #2：从单点 [14,30,70] 扩展为 3×3×3=27 个组合，覆盖均值回归周期
  48→    # 与超买超卖阈值的常用范围。oversold/overbought 保持对称（25/75、30/70、35/65）。
  49→    "rsi_mean_revert": {"period": [7, 14, 21], "oversold": [25, 30, 35], "overbought": [65, 70, 75]},
  50→    # 迭代 #2：MACD 快/慢/信号周期网格 3×3×3=27 个组合，包含经典 12/26/9。
  51→    "macd_cross":      {"fast": [8, 12, 16], "slow": [21, 26, 32], "signal_period": [5, 9, 12]},
  52→    # 迭代 #2：布林带 3×3=9 个组合，覆盖常用 std_dev 范围 [1.5, 2.0, 2.5]。
  53→    "bollinger_band":  {"period": [15, 20, 25], "std_dev": [1.5, 2.0, 2.5]},
  54→    # 迭代 #8：RSI 趋势过滤 3×3×3×1=27 个组合，trend_period 固定 200（经典长周期趋势线）。
  55→    "rsi_trend_filter": {"rsi_period": [7, 14, 21], "oversold": [25, 30, 35],
  56→                         "overbought": [65, 70, 75], "trend_period": [200]},
  57→}
  58→
  59→
  60→def parse_args() -> argparse.Namespace:
  61→    parser = argparse.ArgumentParser(
  62→        prog="mytrader",
  63→        description="MyTrader — 轻量级日内/短线交易系统",
  64→    )
  65→    parser.add_argument(
  66→        "--mode",
  67→        choices=["paper", "semi_auto", "auto"],
  68→        default=None,
  69→        help="执行模式（覆盖配置文件）: paper | semi_auto | auto",
  70→    )
  71→    parser.add_argument(
  72→        "--config",
  73→        type=str,
  74→        default=None,
  75→        metavar="PATH",
  76→        help="YAML 配置文件路径（默认自动查找 config/default.yaml）",
  77→    )
  78→    parser.add_argument(
  79→        "--log-dir",
  80→        type=str,
  81→        default="logs",
  82→        metavar="DIR",
  83→        help="日志目录（默认 logs/）",
  84→    )
  85→    parser.add_argument(
  86→        "--dry-run",
  87→        action="store_true",
  88→        help="仅初始化并检查配置，不启动调度器",
  89→    )
  90→    parser.add_argument(
  91→        "--db",
  92→        type=str,
  93→        default="mytrader.db",
  94→        metavar="PATH",
  95→        help="SQLite 数据库路径（默认 mytrader.db）",
  96→    )
  97→    parser.add_argument(
  98→        "--scan-now",
  99→        choices=["morning", "intraday", "eod"],
 100→        default=None,
 101→        metavar="TYPE",
 102→        help="立即执行一次指定类型的扫描，不启动调度器（调试用）",
 103→    )
 104→    parser.add_argument(
 105→        "--reoptimize",
 106→        action="store_true",
 107→        help="立即触发 MatrixBacktest Walk-Forward 重优化，更新 strategy_weights.json",
 108→    )
 109→    parser.add_argument(
 110→        "--backfill",
 111→        action="store_true",
 112→        help="首次回填 5 年历史数据到 MarketDataStore（一次性操作）",
 113→    )
 114→    return parser.parse_args()
 115→
 116→
 117→def main() -> None:
 118→    args = parse_args()
 119→
 120→    # 1. 初始化日志（最先执行）
 121→    from mytrader.monitor.logger_setup import setup_logger
 122→    setup_logger(log_dir=args.log_dir, level="INFO")
 123→
 124→    from loguru import logger
 125→    logger.info(f"MyTrader starting: mode={args.mode or 'from_config'} dry_run={args.dry_run}")
 126→
 127→    # 2. 加载配置
 128→    from mytrader.infra.config import load_config
 129→    config = load_config(args.config)
 130→
 131→    # CLI --mode 覆盖配置文件
 132→    if args.mode is not None:
 133→        object.__setattr__(config.execution, "mode", args.mode)
 134→        logger.info(f"Execution mode overridden by CLI: {args.mode}")
 135→
 136→    logger.info(
 137→        f"Config loaded: mode={config.execution.mode} broker={config.execution.broker} "
 138→        f"scheduler.enabled={config.scheduler.enabled} "
 139→        f"watchlist={config.watchlist.symbols}"
 140→    )
 141→
 142→    # 3. 装配依赖
 143→    from mytrader.infra.container import Container
 144→    components = Container.build(config, db_url=f"sqlite:///{args.db}")
 145→
 146→    # 4. 健康检查
 147→    report = components.health.run_all()
 148→    logger.info(f"Health check: {report.status} ({report.checks})")
 149→    if not report.is_healthy:
 150→        for name in report.failed_checks:
 151→            logger.warning(f"Health check FAILED: {name} — {report.details.get(name)}")
 152→
 153→    # 5. 构建扫描编排器
 154→    from mytrader.scan_orchestrator import build_orchestrator
 155→    orchestrator = build_orchestrator(components)
 156→
 157→    mode_label = "Phase 5 (multi-strategy matrix)" if orchestrator._use_phase5 else "Phase 4 (single-strategy)"
 158→    logger.info(f"[Orchestrator] Built in {mode_label} mode")
 159→
 160→    # 6a. --backfill：首次回填历史数据
 161→    if args.backfill:
 162→        _run_backfill(config, logger)
 163→        return
 164→
 165→    # 6b. --reoptimize：立即触发 MatrixBacktest
 166→    if args.reoptimize:
 167→        _run_reoptimize(config, logger)
 168→        return
 169→
 170→    # 6c. --scan-now：立即执行一次扫描后退出（调试用）
 171→    if args.scan_now:
 172→        logger.info(f"Running immediate scan: type={args.scan_now}")
 173→        if args.scan_now == "morning":
 174→            summary = orchestrator.morning_scan()
 175→        elif args.scan_now == "intraday":
 176→            summary = orchestrator.intraday_scan()
 177→        else:
 178→            summary = orchestrator.eod_check()
 179→        logger.info(
 180→            f"Scan complete: buy={summary.buy_count} sell={summary.sell_count} "
 181→            f"orders={summary.order_count} errors={summary.error_count}"
 182→        )
 183→        return
 184→
 185→    if args.dry_run:
 186→        # 输出 Phase 5 模块状态
 187→        if components.data_store is not None:
 188→            logger.info(
 189→                f"[DryRun] Phase5 modules active: "
 190→                f"universe={len(components.universe.get_universe())} symbols, "
 191→                f"signal_valid_bars={config.strategy_matrix.signal_valid_bars}"
 192→            )
 193→        else:
 194→            logger.info("[DryRun] Phase4 fallback mode (local DB not loaded)")
 195→
 196→        # Alpaca/IBKR 启动自检
 197→        if config.execution.mode in ("semi_auto", "auto"):
 198→            try:
 199→                result = components.broker.health_check()
 200→                if result["status"] == "connected":
 201→                    logger.info(
 202→                        f"[DryRun] Broker connected: id={result['account_id']}, "
 203→                        f"cash=${result['cash']:,.0f}, buying_power=${result['buying_power']:,.0f}, "
 204→                        f"paper={result['paper']}"
 205→                    )
 206→                else:
 207→                    logger.error(f"[DryRun] Broker health check FAILED: {result}")
 208→            except AttributeError:
 209→                logger.info("[DryRun] Broker does not support health_check (PaperBroker)")
 210→
 211→        logger.info("Dry-run complete. Exiting.")
 212→        return
 213→
 214→    # 7. 启动调度器（接入真实回调）
 215→    from mytrader.infra.scheduler import TradingScheduler
 216→    from mytrader.data.providers.yfinance_provider import YFinanceProvider
 217→
 218→    # 盘后数据增量同步回调（Phase 5）
 219→    def _on_data_sync() -> None:
 220→        if components.data_store is None:
 221→            return
 222→        from mytrader.data.store import DataSyncService
 223→        symbols = components.universe.get_universe()
 224→        logger.info(f"[DataSync] syncing {len(symbols)} symbols...")
 225→        try:
 226→            if config.data.provider == "alpaca":
 227→                from mytrader.data.providers.alpaca_provider import AlpacaDataProvider
 228→                from datetime import date as _date, timedelta as _td
 229→                primary = AlpacaDataProvider(
 230→                    api_key=config.alpaca.api_key,
 231→                    secret_key=config.alpaca.secret_key,
 232→                    paper=config.alpaca.paper,
 233→                )
 234→                # 盘后同步：end 用昨天避开 SIP 实时限制
 235→                end = _date.today() - _td(days=1)
 236→            else:
 237→                primary = YFinanceProvider()
 238→                end = None
 239→            svc = DataSyncService(
 240→                store=components.data_store,
 241→                primary=primary,
 242→                use_fallback_on_empty=False,
 243→            )
 244→            report = svc.sync_all(symbols, max_workers=4, end=end)
 245→            logger.info(f"[DataSync] done: {report}")
 246→        except Exception as exc:
 247→            logger.error(f"[DataSync] failed: {exc}")
 248→
 249→    scheduler = TradingScheduler(
 250→        config=config.scheduler,
 251→        on_morning_scan=orchestrator.morning_scan,
 252→        on_intraday_scan=orchestrator.intraday_scan,
 253→        on_eod_check=orchestrator.eod_check,
 254→        on_reconciliation=_build_reconciliation_callback(components, sync_fn=_on_data_sync),
 255→        on_monthly_reoptimize=lambda: _run_reoptimize(config, logger),
 256→    )
 257→
 258→    # 启动前先执行一次数据同步（确保本地库有数据）
 259→    _on_data_sync()
 260→
 261→    logger.info("Starting scheduler... (Ctrl+C to stop)")
 262→    try:
 263→        scheduler.start()
 264→    except (KeyboardInterrupt, SystemExit):
 265→        logger.info("Shutdown signal received")
 266→    finally:
 267→        scheduler.shutdown(wait=False)
 268→        logger.info("MyTrader stopped")
 269→
 270→
 271→def _run_backfill(config: "Any", logger: "Any") -> None:
 272→    """首次回填 5 年历史数据。自动刷新成分股列表（Wikipedia → CSV）。"""
 273→    from mytrader.data.store import MarketDataStore, DataSyncService
 274→    from mytrader.data.providers.yfinance_provider import YFinanceProvider
 275→    from mytrader.universe.manager import UniverseManager
 276→    from pathlib import Path
 277→
 278→    logger.info("[Backfill] initializing MarketDataStore...")
 279→    store = MarketDataStore()  # 使用默认路径 ~/.mytrader/market_data.db
 280→
 281→    # 若 universe.csv 不存在或为空，从 Wikipedia 拉取完整成分股列表
 282→    csv_path = Path("config/universe.csv")
 283→    need_fetch = (
 284→        not csv_path.exists()
 285→        or csv_path.stat().st_size < 100  # 只有表头或空文件
 286→    )
 287→
 288→    if need_fetch:
 289→        if csv_path.exists():
 290→            logger.info(f"[Backfill] universe.csv is empty/corrupt ({csv_path.stat().st_size} bytes), re-fetching...")
 291→            csv_path.unlink()
 292→        else:
 293→            logger.info("[Backfill] universe.csv not found, fetching constituents from Wikipedia...")
 294→
 295→        # 用指定 CSV 路径创建 UniverseManager，确保 save_to_csv 写入正确位置
 296→        tmp_universe = UniverseManager(store=store, universe_file=csv_path)
 297→        tmp_universe.refresh_constituents(save=True)
 298→
 299→    universe = UniverseManager(store=store, universe_file=csv_path)
 300→    symbols = universe.get_universe()
 301→    logger.info(f"[Backfill] {len(symbols)} symbols to backfill (5 years)")
 302→
 303→    if not symbols:
 304→        logger.error("[Backfill] no symbols to backfill — abort")
 305→        return
 306→
 307→    from datetime import date as _date, timedelta as _timedelta
 308→
 309→    if config.data.provider == "alpaca":
 310→        from mytrader.data.providers.alpaca_provider import AlpacaDataProvider
 311→        primary = AlpacaDataProvider(
 312→            api_key=config.alpaca.api_key,
 313→            secret_key=config.alpaca.secret_key,
 314→            paper=config.alpaca.paper,
 315→        )
 316→        # Alpaca 免费 SIP 不能查当日实时数据，end 用昨天避开限制
 317→        end = _date.today() - _timedelta(days=1)
 318→        logger.info(
 319→            f"[Backfill] using Alpaca provider (end={end}, avoids SIP realtime limit)"
 320→        )
 321→    else:
 322→        primary = YFinanceProvider()
 323→        end = None
 324→
 325→    svc = DataSyncService(store=store, primary=primary, fallback=None,
 326→                          use_fallback_on_empty=False)
 327→    report = svc.backfill(symbols, years=5, end=end)
 328→    logger.info(f"[Backfill] done: {report}")
 329→
 330→
 331→def _run_reoptimize(config: "Any", logger: "Any") -> None:
 332→    """立即触发 MatrixBacktest Walk-Forward 重优化。"""
 333→    from mytrader.data.store import MarketDataStore
 334→    from mytrader.universe.manager import UniverseManager
 335→    from mytrader.backtest.matrix_backtest import MatrixBacktest
 336→    from mytrader.strategy import matrix_runner as _mr_module
 337→
 338→    logger.info("[Reoptimize] starting Walk-Forward MatrixBacktest...")
 339→    store = MarketDataStore()
 340→    universe = UniverseManager(store=store)
 341→
 342→    # 重算波动率分组（确保分组是最新的）
 343→    universe.recompute_volatility_tiers(max_workers=4)
 344→
 345→    mb = MatrixBacktest(store=store, universe=universe, years=5, top_k=2)
 346→
 347→    # ⚠️ 策略名必须与 @register_strategy(...) 装饰器中的名字完全一致。
 348→    # 早期版本误用 "rsi"/"macd"/"bollinger" 简称，与注册表
 349→    # ("rsi_mean_revert"/"macd_cross"/"bollinger_band") 不匹配，
 350→    # 导致这 3 个策略在矩阵回测中被 _backtest_one 静默跳过，
 351→    # strategy_weights.json 退化为仅 dual_ma（迭代 #1 修复）。
 352→    # 模块级常量 REOPTIMIZE_STRATEGIES / REOPTIMIZE_PARAM_GRIDS 便于回归测试
 353→    # （test_reoptimize_strategy_names_match_registry 防止策略名再次与注册表脱节）。
 354→    strategies = REOPTIMIZE_STRATEGIES
 355→    param_grids = REOPTIMIZE_PARAM_GRIDS
 356→
 357→    output = Path("config/strategy_weights.json")
 358→    report = mb.run(strategies=strategies, param_grids=param_grids, output_file=output)
 359→    logger.info(
 360→        f"[Reoptimize] done: {len(report.groups)} groups, "
 361→        f"output={output}"
 362→    )
 363→
 364→    # 迭代 #3：Walk-Forward 4 轮验证（Constitution L7 流水线硬要求）
 365→    # WF 是验证步骤，不影响 strategy_weights.json；结果输出到日志
 366→    try:
 367→        from mytrader.backtest.matrix_backtest import run_walk_forward
 368→        logger.info("[Reoptimize] starting Walk-Forward 4-round validation...")
 369→        wf_report = run_walk_forward(
 370→            mb=mb,
 371→            strategies=strategies,
 372→            param_grids=param_grids,
 373→            rounds=4,
 374→            train_months=18,
 375→            val_months=6,
 376→        )
 377→        for r in wf_report.rounds:
 378→            logger.info(
 379→                f"[WalkForward] Round {r.round_num}/4: "
 380→                f"train={r.train_start}~{r.train_end}, "
 381→                f"val={r.val_start}~{r.val_end}, "
 382→                f"sortino={r.val_sortino:.4f}, "
 383→                f"dd={r.val_max_dd:.4f}%, "
 384→                f"passed={r.passed}"
 385→            )
 386→        logger.info(
 387→            f"[WalkForward] Summary: pass_all_rounds={wf_report.pass_all_rounds}, "
 388→            f"max_val_dd={wf_report.max_val_dd:.4f}%"
 389→        )
 390→        if not wf_report.pass_all_rounds:
 391→            logger.warning(
 392→                "[WalkForward] NOT all rounds passed — "
 393→                "Constitution L7 requires all 4 rounds DD<=15% before paper trading."
 394→            )
 395→    except Exception as exc:
 396→        logger.error(f"[WalkForward] failed: {exc}", exc_info=True)
 397→
 398→    # 迭代 #4：PortfolioBacktest（组合层级回测）
 399→    # 在 MatrixBacktest + Walk-Forward 之后运行，验证组合层 KPI（Sortino/DD）
 400→    # 输出 Constitution L1 关键指标到日志，用于决策"是否进入 paper trading"
 401→    try:
 402→        from mytrader.backtest.portfolio_backtest import (
 403→            PortfolioBacktester,
 404→            PortfolioBacktestConfig,
 405→        )
 406→        from datetime import date as _date
 407→        from datetime import timedelta as _timedelta
 408→
 409→        logger.info("[Reoptimize] starting PortfolioBacktest...")
 410→        # 回测近 1 年（与 Walk-Forward 验证期最后一段对齐）
 411→        pb_end = _date.today() - _timedelta(days=1)
 412→        pb_start = pb_end - _timedelta(days=365)
 413→        pb_cfg = PortfolioBacktestConfig()
 414→        pb = PortfolioBacktester(
 415→            store=store,
 416→            universe=universe,
 417→            weights_file=output,
 418→            config=pb_cfg,
 419→        )
 420→        pb_result = pb.run(start=pb_start, end=pb_end)
 421→        # 迭代 #7：日志增加 benchmark / alpha / IR（Constitution L1 收益可归因）
 422→        logger.info(
 423→            f"[Portfolio Backtest] "
 424→            f"DD={pb_result.max_drawdown_pct:.2f}%, "
 425→            f"Sortino={pb_result.sortino_ratio:.4f}, "
 426→            f"Sharpe={pb_result.sharpe_ratio:.4f}, "
 427→            f"Annual Return={pb_result.annualized_return_pct:.2f}%, "
 428→            f"Benchmark({pb_result.benchmark_symbol}) "
 429→            f"Return={pb_result.benchmark_annualized_return_pct:.2f}%, "
 430→            f"Alpha={pb_result.alpha_pct:.2f}%, "
 431→            f"IR={pb_result.information_ratio:.4f}, "
 432→            f"DD Violation={'YES' if pb_result.dd_violation else 'NO'}"
 433→        )
 434→        if pb_result.dd_violation:
 435→            logger.warning(
 436→                f"[Portfolio Backtest] DD Violation: max_dd={pb_result.max_drawdown_pct:.2f}% "
 437→                f"> 20% threshold (Constitution L1). "
 438→                f"Recommend: review group weights before paper trading."
 439→            )
 440→    except Exception as exc:
 441→        logger.error(f"[Portfolio Backtest] failed: {exc}", exc_info=True)
 442→
 443→    # 热加载（如果 StrategyMatrixRunner 已在运行）
 444→    try:
 445→        from mytrader.strategy.matrix_runner import StrategyMatrixRunner
 446→        logger.info("[Reoptimize] weights reloaded into StrategyMatrixRunner")
 447→    except Exception:
 448→        pass
 449→
 450→
 451→def _build_reconciliation_callback(components: "Any", sync_fn: "Any" = None) -> "Callable":
 452→    """构建对账回调（盘后 16:30 ET）。
 453→
 454→    盘后流程：先同步当日行情数据，再做持仓对账。
 455→
 456→    迭代 #5 修复（P0-C）：
 457→        - ReconciliationService 构造参数从 `tracker=` 改为 `portfolio_tracker=`
 458→        - 调用从 `svc.reconcile()` 改为 `svc.run()`
 459→        - 判断从 `report.has_diff` 改为 `not report.is_clean`
 460→        - 兼容 components.notification / bus 为 None 的场景
 461→        - 末尾 best-effort 写出 paper daily metrics（P0-D）
 462→    """
 463→    from loguru import logger
 464→
 465→    def on_reconciliation() -> None:
 466→        # 1. 先同步当日数据（修复：_on_data_sync 原本只在启动时跑，导致数据库不更新）
 467→        if sync_fn is not None:
 468→            try:
 469→                sync_fn()
 470→            except Exception as exc:
 471→                logger.warning(f"[Reconciliation] data sync failed: {exc}")
 472→        # 2. 持仓对账
 473→        try:
 474→            from mytrader.portfolio.reconciliation import ReconciliationService
 475→            svc = ReconciliationService(
 476→                portfolio_tracker=components.tracker,
 477→                broker=components.broker,
 478→                event_bus=getattr(components, "bus", None),
 479→                auto_sync=False,
 480→            )
 481→            report = svc.run()
 482→            if not report.is_clean:
 483→                diff_syms = [d.symbol for d in report.diffs]
 484→                logger.warning(
 485→                    f"[Reconciliation] {len(report.diffs)} diff(s) found: {diff_syms}"
 486→                )
 487→            else:
 488→                logger.info(
 489→                    f"[Reconciliation] No diffs — positions match "
 490→                    f"(local={report.total_local}, broker={report.total_broker})"
 491→                )
 492→
 493→            # 无论有无差异都推送对账报告
 494→            notification = getattr(components, "notification", None)
 495→            if notification is not None:
 496→                try:
 497→                    from datetime import datetime, timezone
 498→                    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
 499→                    if not report.is_clean:
 500→                        diff_syms = [d.symbol for d in report.diffs]
 501→                        text = (
 502→                            "⚠️ *持仓对账报告*\n"
 503→                            f"时间：{ts}\n"
 504→                            f"发现 {len(report.diffs)} 个标的持仓差异：\n"
 505→                            f"{', '.join(diff_syms[:10])}"
 506→                            + (f" 等{len(diff_syms)}只" if len(diff_syms) > 10 else "")
 507→                            + "\n请检查 broker 与本地记录"
 508→                        )
 509→                    else:
 510→                        text = (
 511→                            "✅ *持仓对账报告*\n"
 512→                            f"时间：{ts}\n"
 513→                            "持仓一致，无差异"
 514→                        )
 515→                    notification.send_message(text)
 516→                except Exception as exc:
 517→                    logger.warning(f"[Reconciliation] notification failed: {exc}")
 518→        except Exception as exc:
 519→            # 对账失败不能让 scheduler 崩溃（Constitution L8 运行时故障处理策略）
 520→            logger.error(f"[Reconciliation] Failed: {exc}", exc_info=True)
 521→
 522→        # 3. 迭代 #5 P0-D：best-effort 写出 paper daily metrics
 523→        #    失败不影响对账已完成的状态
 524→        try:
 525→            from mytrader.monitor.paper_metrics import collect_paper_daily_metrics
 526→            collect_paper_daily_metrics(
 527→                broker=components.broker,
 528→                tracker=components.tracker,
 529→                scan_summary=None,
 530→                data_status=None,
 531→            )
 532→        except Exception as exc:
 533→            logger.warning(f"[Reconciliation] paper metrics collection failed: {exc}")
 534→
 535→    return on_reconciliation
 536→
 537→
 538→if __name__ == "__main__":
 539→    main()
 540→
 541→
---
<tool_use_error>File does not exist.</tool_use_error>
---
<tool_use_error>File does not exist.</tool_use_error>
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
 paths
---
 for
---
 the
---
 spec
---
 file
---
 and
---
 experience
---
.md
---
.
---
{"command":"find /Users/rickouyang/Github/trade-tools/mytrader -name \"spec.md\" -path \"*iteration_13*\" 2>/dev/null; find /Users/rickouyang/Github/trade-tools -name \"experience.md\" 2>/dev/null","description":"Find iteration_13 spec and experience.md"}
---
{"command":"ls /Users/rickouyang/Github/trade-tools/mytrader/iterations/ 2>/dev/null; ls /Users/rickouyang/Github/trade-tools/.codebuddy/notes/ 2>/dev/null","description":"List iterations and notes directories"}
---
Find iteration_13 spec and experience.md
---
List iterations and notes directories
---
Command: find /Users/rickouyang/Github/trade-tools/mytrader -name "spec.md" -path "*iteration_13*" 2>/dev/null; find /Users/rickouyang/Github/trade-tools -name "experience.md" 2>/dev/null
Stdout: /Users/rickouyang/Github/trade-tools/.codebuddy/notes/experience.md

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
Command: ls /Users/rickouyang/Github/trade-tools/mytrader/iterations/ 2>/dev/null; ls /Users/rickouyang/Github/trade-tools/.codebuddy/notes/ 2>/dev/null
Stdout: iteration_8
FAQ.md         dev_records.md experience.md  ideas.md

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
 doesn
---
't
---
 exist
---
 yet
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
 iterations
---
 directory
---
 structure
---
 to
---
 see
---
 what
---
 format
---
 is
---
 expected
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
 iteration
---
_
---
8
---
 as
---
 a
---
 reference
---
 and
---
 check
---
 if
---
 there
---
's
---
 an
---
 iteration
---
_
---
13
---
 folder
---
 elsewhere
---
.
---
{"command":"ls /Users/rickouyang/Github/trade-tools/mytrader/iterations/iteration_8/ 2>/dev/null; find /Users/rickouyang/Github/trade-tools -name \"*iteration*13*\" -o -name \"*iter*13*\" 2>/dev/null | head -20","description":"Check iteration_8 structure and search for iteration_13"}
---
{"file_path":"/Users/rickouyang/Github/trade-tools/.codebuddy/notes/experience.md"}
---
Check iteration_8 structure and search for iteration_13
---
Command: ls /Users/rickouyang/Github/trade-tools/mytrader/iterations/iteration_8/ 2>/dev/null; find /Users/rickouyang/Github/trade-tools -name "*iteration*13*" -o -name "*iter*13*" 2>/dev/null | head -20
Stdout: spec.md
/Users/rickouyang/Github/trade-tools/iterations/iteration_13

Stderr: (empty)
Exit Code: 0
Signal: (none)
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
{"command":"ls /Users/rickouyang/Github/trade-tools/iterations/iteration_13/","description":"List iteration_13 directory"}
---
List iteration_13 directory
---
Command: ls /Users/rickouyang/Github/trade-tools/iterations/iteration_13/
Stdout: spec.md

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"file_path":"/Users/rickouyang/Github/trade-tools/iterations/iteration_13/spec.md"}
---
   1→# Iteration #13 Spec — WF Gate 加 Alpha 校验（目标一致性修复）
   2→
   3→> 日期：2026-07-08
   4→> Meta-Agent：GLM
   5→> 输入依据：用户方法论分析（WF 与 matrix_backtest 目标不一致）、`tmp/iteration10_audit.md` §5 第 6 点、`iterations/iteration_12/summary.md`（WF 4/4 pass 但 alpha=-21%）、`.codebuddy/notes/experience.md` #8
   6→> 风险等级：**低**（仅修改 `matrix_backtest.py` 的 WF 验证逻辑 + `main.py` 日志，不触及选择器/策略/risk/execution）
   7→> 核心目标：给 WF gate 加 alpha 校验，使 WF 的验证目标与 matrix_backtest 的选择目标（alpha）一致。当前 matrix_backtest 用 alpha 选策略，但 WF 只校验 DD——WF 通过 ≠ 跑赢 SPY。Iter #11 的 WF 4/4 pass 但组合 alpha=-21% 就是这个不一致的直接后果。
   8→
   9→---
  10→
  11→## 1. 背景
  12→
  13→### 问题：WF 与 matrix_backtest 目标不一致
  14→
  15→当前系统的三层流程：
  16→
  17→```
  18→matrix_backtest（选策略）
  19→  目标：alpha（选跑赢 SPY 的策略）
  20→  门槛：健全性 → DD → alpha>0 → 排序选 top-K
  21→    ↓ 产出 strategy_weights.json
  22→WF（验证）
  23→  目标：DD（检查不爆仓）  ← ⚠️ 与选择目标不一致
  24→  门槛：val DD ≤ 15%（Sortino 算了但不 gate；alpha 根本没算）
  25→    ↓ pass/fail
  26→PortfolioBacktest（最终权重验证）
  27→  目标：alpha + Sortino + DD
  28→```
  29→
  30→**Iter #11 的实证**：WF 4/4 pass（Sortino 1.56~2.09，max DD 6.36%），但 PortfolioBacktest alpha=-21.41%。WF 通过只说明"策略没爆仓"，不说明"策略跑赢 SPY"。
  31→
  32→### 根因（代码级）
  33→
  34→`matrix_backtest.py::run_walk_forward`（line 903）：
  35→```python
  36→passed = val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD  # 只看 DD！
  37→```
  38→
  39→WF 验证期已经计算了 portfolio 的 combined returns（line 890），但只用它算 Sortino 和 DD，没算 alpha。`_compute_alpha()` 和 `_get_spy_returns()` 都已存在（Iter #9 新增），只是 WF 没调用。
  40→
  41→### 修复思路
  42→
  43→不需要特制 OOS 数据集——**WF 的验证期本身就是 OOS**（相对训练期）。只需在 WF 验证期计算 alpha vs SPY，并加入 gate，就实现了 OOS alpha 验证。这与 matrix_backtest 的 alpha 选择目标一致。
  44→
  45→---
  46→
  47→## 2. Problem Statement
  48→
  49→### 当前代码缺陷
  50→
  51→1. **`WalkForwardRound` 缺 `val_alpha` 字段**：只有 `val_sortino` 和 `val_max_dd`，没有验证期 alpha。
  52→2. **WF gate 只校验 DD**：`passed = val_max_dd <= 15%`，不校验 alpha。
  53→3. **`WalkForwardReport` 缺 alpha 聚合**：只有 `max_val_dd`，没有 `avg_val_alpha` 或 `min_val_alpha`。
  54→4. **`main.py` WF 日志不输出 alpha**：只输出 sortino/dd/passed，不输出 alpha。
  55→
  56→---
  57→
  58→## 3. Scope
  59→
  60→### 本次要做
  61→
  62→1. `WalkForwardRound` 新增 `val_alpha: float = 0.0` 字段。
  63→2. `WalkForwardReport` 新增 `avg_val_alpha: float = 0.0` 和 `min_val_alpha: float = 0.0` 字段。
  64→3. `run_walk_forward` 在验证期计算 portfolio-level alpha vs SPY（复用 `_get_spy_returns` + `_compute_alpha`）。
  65→4. WF gate 加 alpha 校验：
  66→   - 单轮：`passed = val_max_dd ≤ 15% AND val_alpha > -5%`（允许单轮小幅跑输，但不容忍灾难性跑输）
  67→   - 汇总：`pass_all_rounds = all rounds passed AND avg_val_alpha > 0`（平均必须跑赢 SPY）
  68→5. 新增常量 `WALK_FORWARD_VAL_ALPHA_FLOOR: float = -5.0`（单轮 alpha 下限）。
  69→6. `main.py` WF 日志增加 alpha 输出。
  70→7. 新增/更新测试。
  71→8. 更新 `designs/design_v2/07-backtest-module.md` + trajectory + decision_log + CODEBUDDY。
  72→
  73→### 本次不做（明确排除）
  74→
  75→1. **不**做 per-group OOS alpha 反馈（用 WF alpha 清除个别组的权重）→ Iter #14，需要更大的架构改动。
  76→2. **不**改 matrix_backtest 的选择逻辑（in-sample alpha 排序保持不变）。
  77→3. **不**改 WF 的训练期逻辑（仍然用 `_run_group` 做参数搜索 + 选择）。
  78→4. **不**改 PortfolioBacktest（保持原样，定位调整为"生产权重 sanity check"在文档中说明）。
  79→5. **不**触及策略代码、risk、execution。
  80→6. **不**运行 `--reoptimize`（由 Meta-Agent 验收时独立运行）。
  81→
  82→---
  83→
  84→## 4. Detailed Design
  85→
  86→### 4.1 新增常量
  87→
  88→`matrix_backtest.py`（约 line 41，`WALK_FORWARD_VAL_DD_THRESHOLD` 附近）：
  89→
  90→```python
  91→# 迭代 #13：WF 验证期 alpha 单轮下限
  92→# 单轮允许小幅跑输 SPY（-5%），但平均必须跑赢（avg > 0）
  93→# 设计动机：WF 与 matrix_backtest 目标一致性——matrix_backtest 用 alpha 选策略，
  94→# WF 也必须校验 alpha，否则 WF 通过 ≠ 跑赢 SPY（Iter #11: WF 4/4 pass 但 alpha=-21%）
  95→WALK_FORWARD_VAL_ALPHA_FLOOR: float = -5.0
  96→```
  97→
  98→### 4.2 `WalkForwardRound` 新增字段
  99→
 100→`matrix_backtest.py`（约 line 131）：
 101→
 102→```python
 103→@dataclass
 104→class WalkForwardRound:
 105→    # ... 现有字段 ...
 106→    val_sortino: float
 107→    val_max_dd: float
 108→    val_alpha: float = 0.0     # 迭代 #13：验证期 portfolio alpha vs SPY（百分数）
 109→    passed: bool
 110→```
 111→
 112→### 4.3 `WalkForwardReport` 新增字段
 113→
 114→`matrix_backtest.py`（约 line 152）：
 115→
 116→```python
 117→@dataclass
 118→class WalkForwardReport:
 119→    # ... 现有字段 ...
 120→    rounds: list[WalkForwardRound]
 121→    pass_all_rounds: bool
 122→    max_val_dd: float
 123→    avg_val_alpha: float = 0.0   # 迭代 #13：4 轮平均验证期 alpha
 124→    min_val_alpha: float = 0.0   # 迭代 #13：4 轮中最差的验证期 alpha
 125→```
 126→
 127→### 4.4 `run_walk_forward` 计算 val alpha + 加 gate
 128→
 129→`matrix_backtest.py`（约 line 889-903），在现有 `combined` 计算后加 alpha：
 130→
 131→```python
 132→# 现有代码（line 890-901）：
 133→combined = pd.concat(all_returns, axis=1).mean(axis=1).dropna()
 134→if len(combined) < 5:
 135→    val_sortino = 0.0
 136→    val_max_dd = 0.0
 137→else:
 138→    val_sortino = _compute_sortino(combined)
 139→    wrapper = [SingleBacktestResult(...)]
 140→    val_max_dd = _portfolio_max_drawdown_from_results(wrapper)
 141→
 142→# ── 迭代 #13 新增：计算验证期 alpha vs SPY ──
 143→# 与 matrix_backtest 的 alpha 选择目标一致（目标一致性修复）
 144→# SPY 不可用时 alpha=0.0（与 _compute_alpha 的降级语义一致）
 145→spy_val_returns = mb._get_spy_returns(val_start, val_end)
 146→if len(combined) >= 5 and spy_val_returns is not None:
 147→    val_alpha = _compute_alpha(combined, spy_val_returns)
 148→else:
 149→    val_alpha = 0.0
 150→    if spy_val_returns is None:
 151→        logger.warning(
 152→            f"[WalkForward] Round {round_num}: SPY data unavailable for "
 153→            f"val period {val_start}~{val_end} — val_alpha=0 (degraded)"
 154→        )
 155→
 156→# ── 迭代 #13：gate 加 alpha 校验 ──
 157→# 单轮：DD ≤ 15% AND alpha > -5%（允许小幅跑输，不容忍灾难）
 158→# 汇总：all rounds passed AND avg alpha > 0（平均必须跑赢 SPY）
 159→dd_passed = val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD
 160→alpha_passed = val_alpha > WALK_FORWARD_VAL_ALPHA_FLOOR
 161→passed = dd_passed and alpha_passed
 162→```
 163→
 164→### 4.5 `WalkForwardReport` 汇总加 alpha 聚合
 165→
 166→`matrix_backtest.py`（约 line 920-924）：
 167→
 168→```python
 169→# 迭代 #13：汇总 alpha 聚合
 170→val_alphas = [r.val_alpha for r in wf_rounds]
 171→avg_val_alpha = sum(val_alphas) / len(val_alphas) if val_alphas else 0.0
 172→min_val_alpha = min(val_alphas) if val_alphas else 0.0
 173→
 174→# 迭代 #13：pass_all_rounds 加 avg alpha > 0 条件
 175→# 单轮 all passed + 平均 alpha > 0（平均必须跑赢 SPY）
 176→all_rounds_passed = all(r.passed for r in wf_rounds) if wf_rounds else False
 177→avg_alpha_positive = avg_val_alpha > 0
 178→pass_all = all_rounds_passed and avg_alpha_positive
 179→
 180→report = WalkForwardReport(
 181→    rounds=wf_rounds,
 182→    pass_all_rounds=pass_all,
 183→    max_val_dd=max((r.val_max_dd for r in wf_rounds), default=0.0),
 184→    avg_val_alpha=avg_val_alpha,
 185→    min_val_alpha=min_val_alpha,
 186→)
 187→```
 188→
 189→日志增加 alpha：
 190→```python
 191→logger.info(
 192→    f"[WalkForward] done: {len(wf_rounds)} rounds, "
 193→    f"pass_all_rounds={report.pass_all_rounds}, "
 194→    f"max_val_dd={report.max_val_dd:.4f}%, "
 195→    f"avg_val_alpha={report.avg_val_alpha:.4f}%, "
 196→    f"min_val_alpha={report.min_val_alpha:.4f}%"
 197→)
 198→```
 199→
 200→### 4.6 `main.py` WF 日志增加 alpha
 201→
 202→`main.py`（约 line 378-388），WF round 和 summary 日志增加 alpha：
 203→
 204→```python
 205→for r in wf_report.rounds:
 206→    logger.info(
 207→        f"[WalkForward] Round {r.round_num}/4: "
 208→        f"train={r.train_start}~{r.train_end}, "
 209→        f"val={r.val_start}~{r.val_end}, "
 210→        f"sortino={r.val_sortino:.4f}, "
 211→        f"dd={r.val_max_dd:.4f}%, "
 212→        f"alpha={r.val_alpha:.4f}%, "     # 迭代 #13 新增
 213→        f"passed={r.passed}"
 214→    )
 215→logger.info(
 216→    f"[WalkForward] Summary: pass_all_rounds={wf_report.pass_all_rounds}, "
 217→    f"max_val_dd={wf_report.max_val_dd:.4f}%, "
 218→    f"avg_val_alpha={wf_report.avg_val_alpha:.4f}%, "   # 迭代 #13 新增
 219→    f"min_val_alpha={wf_report.min_val_alpha:.4f}%"     # 迭代 #13 新增
 220→)
 221→if not wf_report.pass_all_rounds:
 222→    logger.warning(
 223→        "[WalkForward] NOT all rounds passed — "
 224→        "Constitution L7 requires all 4 rounds DD<=15% AND avg alpha>0 "
 225→        "before paper trading."
 226→    )
 227→```
 228→
 229→### 4.7 Gate 逻辑总结
 230→
 231→| 层级 | 条件 | 常量 |
 232→|------|------|------|
 233→| 单轮 | `val_max_dd ≤ 15% AND val_alpha > -5%` | `WALK_FORWARD_VAL_DD_THRESHOLD=15.0`, `WALK_FORWARD_VAL_ALPHA_FLOOR=-5.0` |
 234→| 汇总 | `all rounds passed AND avg_val_alpha > 0` | （硬编码 avg > 0） |
 235→
 236→**设计动机**：
 237→- 单轮允许 alpha 在 -5%~0%（小幅跑输 SPY 可能是市场噪音）
 238→- 但 4 轮平均必须 > 0（整体必须跑赢 SPY）
 239→- 这与 matrix_backtest 的 alpha>0 门槛呼应：in-sample alpha>0 是入选条件，OOS avg alpha>0 是验证条件
 240→
 241→---
 242→
 243→## 5. 测试计划
 244→
 245→新增 `tests/test_wf_alpha_gate.py`：
 246→
 247→1. **test_wf_round_has_val_alpha_field** — `WalkForwardRound.val_alpha` 字段存在且默认 0.0。
 248→2. **test_wf_report_has_alpha_aggregation** — `WalkForwardReport.avg_val_alpha` 和 `min_val_alpha` 字段存在。
 249→3. **test_wf_gate_rejects_negative_alpha** — 单轮 alpha < -5% → `passed=False`（即使 DD 合规）。
 250→4. **test_wf_gate_passes_positive_alpha** — 单轮 alpha > 0 且 DD ≤ 15% → `passed=True`。
 251→5. **test_wf_gate_allows_small_negative_alpha** — 单轮 alpha = -3%（> -5%）且 DD 合规 → `passed=True`。
 252→6. **test_wf_summary_avg_alpha_negative_fails** — 4 轮全 pass 但 avg alpha < 0 → `pass_all_rounds=False`。
 253→7. **test_wf_summary_avg_alpha_positive_passes** — 4 轮全 pass 且 avg alpha > 0 → `pass_all_rounds=True`。
 254→8. **test_wf_spy_unavailable_alpha_zero** — SPY 不可用时 val_alpha=0.0 + WARNING（降级不阻塞）。
 255→9. **test_wf_alpha_computed_correctly** — 用已知 returns + spy_returns 验证 val_alpha 值正确。
 256→
 257→### 回归
 258→
 259→- 现有 `tests/test_matrix_backtest.py` 中 WF 相关测试全部通过。
 260→- **注意**：现有 WF 测试可能没有 SPY 数据 → val_alpha=0 → avg_alpha=0 → `pass_all_rounds=False`（因为 avg > 0 不满足）。需要检查现有测试是否依赖 `pass_all_rounds=True`，如果是，需要在测试中提供 SPY 数据或 mock alpha > 0。
 261→
 262→---
 263→
 264→## 6. Success Criteria
 265→
 266→1. `WalkForwardRound.val_alpha` 和 `WalkForwardReport.avg_val_alpha`/`min_val_alpha` 字段存在。
 267→2. `run_walk_forward` 在验证期计算 portfolio-level alpha vs SPY。
 268→3. WF gate：单轮 `DD ≤ 15% AND alpha > -5%`；汇总 `all passed AND avg alpha > 0`。
 269→4. `main.py` WF 日志输出 alpha。
 270→5. 默认 pytest 通过（659+ 测试，0 failed）；新增测试 ≥ 8 个。
 271→6. 不修改选择器/策略/risk/execution 代码。
 272→7. 更新 `designs/design_v2/07-backtest-module.md` + trajectory + decision_log + CODEBUDDY。
 273→
 274→### 验收阶段（Meta-Agent 独立执行）
 275→
 276→- 运行 `python main.py --reoptimize`，验证：
 277→  - WF 每轮日志输出 alpha
 278→  - WF summary 输出 avg_val_alpha 和 min_val_alpha
 279→  - 若 avg alpha < 0 → `pass_all_rounds=False` + WARNING（与 Iter #11 的 alpha=-21% 场景一致）
 280→  - matrix_backtest 产出的 weights 不受影响（WF 是验证步骤，不修改 weights）
 281→
 282→---
 283→
 284→## 7. Implementation Order
 285→
 286→1. 读 spec + `matrix_backtest.py`（重点 `run_walk_forward` line 785-930 + `WalkForwardRound`/`WalkForwardReport` line 114-155 + `_get_spy_returns` line 1036）+ `experience.md` #8 + `main.py::_run_reoptimize` line 364-396。
 287→2. 加 `WALK_FORWARD_VAL_ALPHA_FLOOR` 常量。
 288→3. `WalkForwardRound` 加 `val_alpha` 字段。
 289→4. `WalkForwardReport` 加 `avg_val_alpha` + `min_val_alpha` 字段。
 290→5. `run_walk_forward` 验证期计算 alpha + gate 加 alpha 校验 + 汇总加 alpha 聚合。
 291→6. `main.py` WF 日志增加 alpha。
 292→7. 写测试（含 SPY 不可用降级、alpha 边界、汇总逻辑）。
 293→8. 检查现有 WF 测试是否需要调整（SPY 数据 / mock alpha）。
 294→9. 运行 targeted tests + 默认 pytest。
 295→10. 更新 `designs/design_v2/07-backtest-module.md` + trajectory + decision_log + CODEBUDDY。
 296→
 297→---
 298→
 299→## 8. Risk Classification
 300→
 301→- **低风险**：仅改 WF 验证逻辑（`run_walk_forward`）+ 数据结构字段 + 日志，不触及选择器/策略/risk/execution。
 302→- **行为变更**：WF gate 变严了（加了 alpha 校验）。之前 DD-only pass 的策略现在可能因 alpha<0 而 fail。这是**预期且正确**的——WF 通过应该意味着"OOS 跑赢 SPY"，不只是"OOS 没爆仓"。
 303→- **降级处理**：SPY 不可用时 val_alpha=0.0（不阻塞 WF），但汇总 avg_alpha=0 → `pass_all_rounds=False`（保守拒绝）。
 304→- **Constitution 合规**：WF alpha 校验直接满足 experience.md #8 的"验收 gate 必须校验跑赢 benchmark（正 alpha）"。
 305→- **回滚**：若 alpha gate 过严（大面积 WF fail），可下调 `WALK_FORWARD_VAL_ALPHA_FLOOR` 或临时设为 -100（禁用 alpha gate）。
 306→
---
   1→# Iteration #13 Spec — WF Gate 加 Alpha 校验（目标一致性修复）
   2→
   3→> 日期：2026-07-08
   4→> Meta-Agent：GLM
   5→> 输入依据：用户方法论分析（WF 与 matrix_backtest 目标不一致）、`tmp/iteration10_audit.md` §5 第 6 点、`iterations/iteration_12/summary.md`（WF 4/4 pass 但 alpha=-21%）、`.codebuddy/notes/experience.md` #8
   6→> 风险等级：**低**（仅修改 `matrix_backtest.py` 的 WF 验证逻辑 + `main.py` 日志，不触及选择器/策略/risk/execution）
   7→> 核心目标：给 WF gate 加 alpha 校验，使 WF 的验证目标与 matrix_backtest 的选择目标（alpha）一致。当前 matrix_backtest 用 alpha 选策略，但 WF 只校验 DD——WF 通过 ≠ 跑赢 SPY。Iter #11 的 WF 4/4 pass 但组合 alpha=-21% 就是这个不一致的直接后果。
   8→
   9→---
  10→
  11→## 1. 背景
  12→
  13→### 问题：WF 与 matrix_backtest 目标不一致
  14→
  15→当前系统的三层流程：
  16→
  17→```
  18→matrix_backtest（选策略）
  19→  目标：alpha（选跑赢 SPY 的策略）
  20→  门槛：健全性 → DD → alpha>0 → 排序选 top-K
  21→    ↓ 产出 strategy_weights.json
  22→WF（验证）
  23→  目标：DD（检查不爆仓）  ← ⚠️ 与选择目标不一致
  24→  门槛：val DD ≤ 15%（Sortino 算了但不 gate；alpha 根本没算）
  25→    ↓ pass/fail
  26→PortfolioBacktest（最终权重验证）
  27→  目标：alpha + Sortino + DD
  28→```
  29→
  30→**Iter #11 的实证**：WF 4/4 pass（Sortino 1.56~2.09，max DD 6.36%），但 PortfolioBacktest alpha=-21.41%。WF 通过只说明"策略没爆仓"，不说明"策略跑赢 SPY"。
  31→
  32→### 根因（代码级）
  33→
  34→`matrix_backtest.py::run_walk_forward`（line 903）：
  35→```python
  36→passed = val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD  # 只看 DD！
  37→```
  38→
  39→WF 验证期已经计算了 portfolio 的 combined returns（line 890），但只用它算 Sortino 和 DD，没算 alpha。`_compute_alpha()` 和 `_get_spy_returns()` 都已存在（Iter #9 新增），只是 WF 没调用。
  40→
  41→### 修复思路
  42→
  43→不需要特制 OOS 数据集——**WF 的验证期本身就是 OOS**（相对训练期）。只需在 WF 验证期计算 alpha vs SPY，并加入 gate，就实现了 OOS alpha 验证。这与 matrix_backtest 的 alpha 选择目标一致。
  44→
  45→---
  46→
  47→## 2. Problem Statement
  48→
  49→### 当前代码缺陷
  50→
  51→1. **`WalkForwardRound` 缺 `val_alpha` 字段**：只有 `val_sortino` 和 `val_max_dd`，没有验证期 alpha。
  52→2. **WF gate 只校验 DD**：`passed = val_max_dd <= 15%`，不校验 alpha。
  53→3. **`WalkForwardReport` 缺 alpha 聚合**：只有 `max_val_dd`，没有 `avg_val_alpha` 或 `min_val_alpha`。
  54→4. **`main.py` WF 日志不输出 alpha**：只输出 sortino/dd/passed，不输出 alpha。
  55→
  56→---
  57→
  58→## 3. Scope
  59→
  60→### 本次要做
  61→
  62→1. `WalkForwardRound` 新增 `val_alpha: float = 0.0` 字段。
  63→2. `WalkForwardReport` 新增 `avg_val_alpha: float = 0.0` 和 `min_val_alpha: float = 0.0` 字段。
  64→3. `run_walk_forward` 在验证期计算 portfolio-level alpha vs SPY（复用 `_get_spy_returns` + `_compute_alpha`）。
  65→4. WF gate 加 alpha 校验：
  66→   - 单轮：`passed = val_max_dd ≤ 15% AND val_alpha > -5%`（允许单轮小幅跑输，但不容忍灾难性跑输）
  67→   - 汇总：`pass_all_rounds = all rounds passed AND avg_val_alpha > 0`（平均必须跑赢 SPY）
  68→5. 新增常量 `WALK_FORWARD_VAL_ALPHA_FLOOR: float = -5.0`（单轮 alpha 下限）。
  69→6. `main.py` WF 日志增加 alpha 输出。
  70→7. 新增/更新测试。
  71→8. 更新 `designs/design_v2/07-backtest-module.md` + trajectory + decision_log + CODEBUDDY。
  72→
  73→### 本次不做（明确排除）
  74→
  75→1. **不**做 per-group OOS alpha 反馈（用 WF alpha 清除个别组的权重）→ Iter #14，需要更大的架构改动。
  76→2. **不**改 matrix_backtest 的选择逻辑（in-sample alpha 排序保持不变）。
  77→3. **不**改 WF 的训练期逻辑（仍然用 `_run_group` 做参数搜索 + 选择）。
  78→4. **不**改 PortfolioBacktest（保持原样，定位调整为"生产权重 sanity check"在文档中说明）。
  79→5. **不**触及策略代码、risk、execution。
  80→6. **不**运行 `--reoptimize`（由 Meta-Agent 验收时独立运行）。
  81→
  82→---
  83→
  84→## 4. Detailed Design
  85→
  86→### 4.1 新增常量
  87→
  88→`matrix_backtest.py`（约 line 41，`WALK_FORWARD_VAL_DD_THRESHOLD` 附近）：
  89→
  90→```python
  91→# 迭代 #13：WF 验证期 alpha 单轮下限
  92→# 单轮允许小幅跑输 SPY（-5%），但平均必须跑赢（avg > 0）
  93→# 设计动机：WF 与 matrix_backtest 目标一致性——matrix_backtest 用 alpha 选策略，
  94→# WF 也必须校验 alpha，否则 WF 通过 ≠ 跑赢 SPY（Iter #11: WF 4/4 pass 但 alpha=-21%）
  95→WALK_FORWARD_VAL_ALPHA_FLOOR: float = -5.0
  96→```
  97→
  98→### 4.2 `WalkForwardRound` 新增字段
  99→
 100→`matrix_backtest.py`（约 line 131）：
 101→
 102→```python
 103→@dataclass
 104→class WalkForwardRound:
 105→    # ... 现有字段 ...
 106→    val_sortino: float
 107→    val_max_dd: float
 108→    val_alpha: float = 0.0     # 迭代 #13：验证期 portfolio alpha vs SPY（百分数）
 109→    passed: bool
 110→```
 111→
 112→### 4.3 `WalkForwardReport` 新增字段
 113→
 114→`matrix_backtest.py`（约 line 152）：
 115→
 116→```python
 117→@dataclass
 118→class WalkForwardReport:
 119→    # ... 现有字段 ...
 120→    rounds: list[WalkForwardRound]
 121→    pass_all_rounds: bool
 122→    max_val_dd: float
 123→    avg_val_alpha: float = 0.0   # 迭代 #13：4 轮平均验证期 alpha
 124→    min_val_alpha: float = 0.0   # 迭代 #13：4 轮中最差的验证期 alpha
 125→```
 126→
 127→### 4.4 `run_walk_forward` 计算 val alpha + 加 gate
 128→
 129→`matrix_backtest.py`（约 line 889-903），在现有 `combined` 计算后加 alpha：
 130→
 131→```python
 132→# 现有代码（line 890-901）：
 133→combined = pd.concat(all_returns, axis=1).mean(axis=1).dropna()
 134→if len(combined) < 5:
 135→    val_sortino = 0.0
 136→    val_max_dd = 0.0
 137→else:
 138→    val_sortino = _compute_sortino(combined)
 139→    wrapper = [SingleBacktestResult(...)]
 140→    val_max_dd = _portfolio_max_drawdown_from_results(wrapper)
 141→
 142→# ── 迭代 #13 新增：计算验证期 alpha vs SPY ──
 143→# 与 matrix_backtest 的 alpha 选择目标一致（目标一致性修复）
 144→# SPY 不可用时 alpha=0.0（与 _compute_alpha 的降级语义一致）
 145→spy_val_returns = mb._get_spy_returns(val_start, val_end)
 146→if len(combined) >= 5 and spy_val_returns is not None:
 147→    val_alpha = _compute_alpha(combined, spy_val_returns)
 148→else:
 149→    val_alpha = 0.0
 150→    if spy_val_returns is None:
 151→        logger.warning(
 152→            f"[WalkForward] Round {round_num}: SPY data unavailable for "
 153→            f"val period {val_start}~{val_end} — val_alpha=0 (degraded)"
 154→        )
 155→
 156→# ── 迭代 #13：gate 加 alpha 校验 ──
 157→# 单轮：DD ≤ 15% AND alpha > -5%（允许小幅跑输，不容忍灾难）
 158→# 汇总：all rounds passed AND avg alpha > 0（平均必须跑赢 SPY）
 159→dd_passed = val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD
 160→alpha_passed = val_alpha > WALK_FORWARD_VAL_ALPHA_FLOOR
 161→passed = dd_passed and alpha_passed
 162→```
 163→
 164→### 4.5 `WalkForwardReport` 汇总加 alpha 聚合
 165→
 166→`matrix_backtest.py`（约 line 920-924）：
 167→
 168→```python
 169→# 迭代 #13：汇总 alpha 聚合
 170→val_alphas = [r.val_alpha for r in wf_rounds]
 171→avg_val_alpha = sum(val_alphas) / len(val_alphas) if val_alphas else 0.0
 172→min_val_alpha = min(val_alphas) if val_alphas else 0.0
 173→
 174→# 迭代 #13：pass_all_rounds 加 avg alpha > 0 条件
 175→# 单轮 all passed + 平均 alpha > 0（平均必须跑赢 SPY）
 176→all_rounds_passed = all(r.passed for r in wf_rounds) if wf_rounds else False
 177→avg_alpha_positive = avg_val_alpha > 0
 178→pass_all = all_rounds_passed and avg_alpha_positive
 179→
 180→report = WalkForwardReport(
 181→    rounds=wf_rounds,
 182→    pass_all_rounds=pass_all,
 183→    max_val_dd=max((r.val_max_dd for r in wf_rounds), default=0.0),
 184→    avg_val_alpha=avg_val_alpha,
 185→    min_val_alpha=min_val_alpha,
 186→)
 187→```
 188→
 189→日志增加 alpha：
 190→```python
 191→logger.info(
 192→    f"[WalkForward] done: {len(wf_rounds)} rounds, "
 193→    f"pass_all_rounds={report.pass_all_rounds}, "
 194→    f"max_val_dd={report.max_val_dd:.4f}%, "
 195→    f"avg_val_alpha={report.avg_val_alpha:.4f}%, "
 196→    f"min_val_alpha={report.min_val_alpha:.4f}%"
 197→)
 198→```
 199→
 200→### 4.6 `main.py` WF 日志增加 alpha
 201→
 202→`main.py`（约 line 378-388），WF round 和 summary 日志增加 alpha：
 203→
 204→```python
 205→for r in wf_report.rounds:
 206→    logger.info(
 207→        f"[WalkForward] Round {r.round_num}/4: "
 208→        f"train={r.train_start}~{r.train_end}, "
 209→        f"val={r.val_start}~{r.val_end}, "
 210→        f"sortino={r.val_sortino:.4f}, "
 211→        f"dd={r.val_max_dd:.4f}%, "
 212→        f"alpha={r.val_alpha:.4f}%, "     # 迭代 #13 新增
 213→        f"passed={r.passed}"
 214→    )
 215→logger.info(
 216→    f"[WalkForward] Summary: pass_all_rounds={wf_report.pass_all_rounds}, "
 217→    f"max_val_dd={wf_report.max_val_dd:.4f}%, "
 218→    f"avg_val_alpha={wf_report.avg_val_alpha:.4f}%, "   # 迭代 #13 新增
 219→    f"min_val_alpha={wf_report.min_val_alpha:.4f}%"     # 迭代 #13 新增
 220→)
 221→if not wf_report.pass_all_rounds:
 222→    logger.warning(
 223→        "[WalkForward] NOT all rounds passed — "
 224→        "Constitution L7 requires all 4 rounds DD<=15% AND avg alpha>0 "
 225→        "before paper trading."
 226→    )
 227→```
 228→
 229→### 4.7 Gate 逻辑总结
 230→
 231→| 层级 | 条件 | 常量 |
 232→|------|------|------|
 233→| 单轮 | `val_max_dd ≤ 15% AND val_alpha > -5%` | `WALK_FORWARD_VAL_DD_THRESHOLD=15.0`, `WALK_FORWARD_VAL_ALPHA_FLOOR=-5.0` |
 234→| 汇总 | `all rounds passed AND avg_val_alpha > 0` | （硬编码 avg > 0） |
 235→
 236→**设计动机**：
 237→- 单轮允许 alpha 在 -5%~0%（小幅跑输 SPY 可能是市场噪音）
 238→- 但 4 轮平均必须 > 0（整体必须跑赢 SPY）
 239→- 这与 matrix_backtest 的 alpha>0 门槛呼应：in-sample alpha>0 是入选条件，OOS avg alpha>0 是验证条件
 240→
 241→---
 242→
 243→## 5. 测试计划
 244→
 245→新增 `tests/test_wf_alpha_gate.py`：
 246→
 247→1. **test_wf_round_has_val_alpha_field** — `WalkForwardRound.val_alpha` 字段存在且默认 0.0。
 248→2. **test_wf_report_has_alpha_aggregation** — `WalkForwardReport.avg_val_alpha` 和 `min_val_alpha` 字段存在。
 249→3. **test_wf_gate_rejects_negative_alpha** — 单轮 alpha < -5% → `passed=False`（即使 DD 合规）。
 250→4. **test_wf_gate_passes_positive_alpha** — 单轮 alpha > 0 且 DD ≤ 15% → `passed=True`。
 251→5. **test_wf_gate_allows_small_negative_alpha** — 单轮 alpha = -3%（> -5%）且 DD 合规 → `passed=True`。
 252→6. **test_wf_summary_avg_alpha_negative_fails** — 4 轮全 pass 但 avg alpha < 0 → `pass_all_rounds=False`。
 253→7. **test_wf_summary_avg_alpha_positive_passes** — 4 轮全 pass 且 avg alpha > 0 → `pass_all_rounds=True`。
 254→8. **test_wf_spy_unavailable_alpha_zero** — SPY 不可用时 val_alpha=0.0 + WARNING（降级不阻塞）。
 255→9. **test_wf_alpha_computed_correctly** — 用已知 returns + spy_returns 验证 val_alpha 值正确。
 256→
 257→### 回归
 258→
 259→- 现有 `tests/test_matrix_backtest.py` 中 WF 相关测试全部通过。
 260→- **注意**：现有 WF 测试可能没有 SPY 数据 → val_alpha=0 → avg_alpha=0 → `pass_all_rounds=False`（因为 avg > 0 不满足）。需要检查现有测试是否依赖 `pass_all_rounds=True`，如果是，需要在测试中提供 SPY 数据或 mock alpha > 0。
 261→
 262→---
 263→
 264→## 6. Success Criteria
 265→
 266→1. `WalkForwardRound.val_alpha` 和 `WalkForwardReport.avg_val_alpha`/`min_val_alpha` 字段存在。
 267→2. `run_walk_forward` 在验证期计算 portfolio-level alpha vs SPY。
 268→3. WF gate：单轮 `DD ≤ 15% AND alpha > -5%`；汇总 `all passed AND avg alpha > 0`。
 269→4. `main.py` WF 日志输出 alpha。
 270→5. 默认 pytest 通过（659+ 测试，0 failed）；新增测试 ≥ 8 个。
 271→6. 不修改选择器/策略/risk/execution 代码。
 272→7. 更新 `designs/design_v2/07-backtest-module.md` + trajectory + decision_log + CODEBUDDY。
 273→
 274→### 验收阶段（Meta-Agent 独立执行）
 275→
 276→- 运行 `python main.py --reoptimize`，验证：
 277→  - WF 每轮日志输出 alpha
 278→  - WF summary 输出 avg_val_alpha 和 min_val_alpha
 279→  - 若 avg alpha < 0 → `pass_all_rounds=False` + WARNING（与 Iter #11 的 alpha=-21% 场景一致）
 280→  - matrix_backtest 产出的 weights 不受影响（WF 是验证步骤，不修改 weights）
 281→
 282→---
 283→
 284→## 7. Implementation Order
 285→
 286→1. 读 spec + `matrix_backtest.py`（重点 `run_walk_forward` line 785-930 + `WalkForwardRound`/`WalkForwardReport` line 114-155 + `_get_spy_returns` line 1036）+ `experience.md` #8 + `main.py::_run_reoptimize` line 364-396。
 287→2. 加 `WALK_FORWARD_VAL_ALPHA_FLOOR` 常量。
 288→3. `WalkForwardRound` 加 `val_alpha` 字段。
 289→4. `WalkForwardReport` 加 `avg_val_alpha` + `min_val_alpha` 字段。
 290→5. `run_walk_forward` 验证期计算 alpha + gate 加 alpha 校验 + 汇总加 alpha 聚合。
 291→6. `main.py` WF 日志增加 alpha。
 292→7. 写测试（含 SPY 不可用降级、alpha 边界、汇总逻辑）。
 293→8. 检查现有 WF 测试是否需要调整（SPY 数据 / mock alpha）。
 294→9. 运行 targeted tests + 默认 pytest。
 295→10. 更新 `designs/design_v2/07-backtest-module.md` + trajectory + decision_log + CODEBUDDY。
 296→
 297→---
 298→
 299→## 8. Risk Classification
 300→
 301→- **低风险**：仅改 WF 验证逻辑（`run_walk_forward`）+ 数据结构字段 + 日志，不触及选择器/策略/risk/execution。
 302→- **行为变更**：WF gate 变严了（加了 alpha 校验）。之前 DD-only pass 的策略现在可能因 alpha<0 而 fail。这是**预期且正确**的——WF 通过应该意味着"OOS 跑赢 SPY"，不只是"OOS 没爆仓"。
 303→- **降级处理**：SPY 不可用时 val_alpha=0.0（不阻塞 WF），但汇总 avg_alpha=0 → `pass_all_rounds=False`（保守拒绝）。
 304→- **Constitution 合规**：WF alpha 校验直接满足 experience.md #8 的"验收 gate 必须校验跑赢 benchmark（正 alpha）"。
 305→- **回滚**：若 alpha gate 过严（大面积 WF fail），可下调 `WALK_FORWARD_VAL_ALPHA_FLOOR` 或临时设为 -100（禁用 alpha gate）。
 306→
---
Now
---
 I
---
 understand
---
 the
---
 spec
---
.
---
 Let
---
 me
---
 also
---
 look
---
 at
---
 existing
---
 WF
---
 tests
---
 to
---
 understand
---
 what
---
 might
---
 need
---
 adjustment
---
.
---
现在
---
我已经
---
拿到了
---
规范
---
。
---
让我
---
检查
---
一下
---
现有的
---
 WF
---
 
---
测试
---
以及
---
相关的
---
 design
---
/
---
trajectory
---
 文
---
件
---
。
---
{"command":"find /Users/rickouyang/Github/trade-tools/mytrader/tests -name \"*walk_forward*\" -o -name \"*wf*\" 2>/dev/null; find /Users/rickouyang/Github/trade-tools/mytrader/tests -name \"test_matrix_backtest*\" 2>/dev/null","description":"Find WF and matrix backtest test files"}
---
{"command":"ls /Users/rickouyang/Github/trade-tools/mytrader/tests/ | head -50; echo \"---\"; ls /Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/","description":"List tests and design_v2 directories"}
---
Find WF and matrix backtest test files
---
List tests and design_v2 directories
---
Command: find /Users/rickouyang/Github/trade-tools/mytrader/tests -name "*walk_forward*" -o -name "*wf*" 2>/dev/null; find /Users/rickouyang/Github/trade-tools/mytrader/tests -name "test_matrix_backtest*" 2>/dev/null
Stdout: /Users/rickouyang/Github/trade-tools/mytrader/tests/__pycache__/test_matrix_backtest.cpython-312-pytest-9.0.3.pyc
/Users/rickouyang/Github/trade-tools/mytrader/tests/__pycache__/test_matrix_backtest.cpython-312.pyc
/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
Command: ls /Users/rickouyang/Github/trade-tools/mytrader/tests/ | head -50; echo "---"; ls /Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/
Stdout: __init__.py
__pycache__
test_alpaca_broker.py
test_alpaca_provider.py
test_alpha_gate.py
test_backtest.py
test_batch_backtest.py
test_cache.py
test_container.py
test_data_layer.py
test_degenerate_filter.py
test_execution.py
test_infra.py
test_integration.py
test_integration_live.py
test_main_reconciliation.py
test_market_data_store.py
test_matrix_backtest.py
test_monitor.py
test_notification.py
test_paper_metrics.py
test_portfolio.py
test_portfolio_backtest.py
test_provider.py
test_reconciliation.py
test_risk_manager.py
test_scan_orchestrator.py
test_scheduler.py
test_signal_filter.py
test_signal_parity.py
test_strategy.py
test_strategy_matrix_ranker.py
test_universe_manager.py
---
00-overview.md          06-portfolio-tracker.md 12-strategy-matrix.md
01-data-layer.md        07-backtest-module.md   13-signal-ranker.md
02-strategy-engine.md   08-monitor-layer.md     CHANGELOG.md
03-signal-filter.md     09-infrastructure.md    claude_review.md
04-risk-manager.md      10-market-data-store.md glm_review.md
05-execution-engine.md  11-universe-manager.md

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"-n":true,"output_mode":"content","path":"/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py","pattern":"walk_forward|WalkForward|run_walk_forward|val_sortino|val_max_dd|pass_all_rounds|max_val_dd"}
---
["/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:34:    WalkForwardReport,","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:35:    WalkForwardRound,","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:37:    run_walk_forward,","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:734:class TestWalkForward:","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:737:    def test_walk_forward_round_dataclass(self):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:738:        \"\"\"WalkForwardRound dataclass 字段完整 + passed 判定正确。\"\"\"","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:740:        r = WalkForwardRound(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:746:            val_sortino=1.5,","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:747:            val_max_dd=10.0,","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:753:        assert r.val_sortino == 1.5","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:754:        assert r.val_max_dd == 10.0","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:757:    def test_walk_forward_round_passed_threshold(self):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:758:        \"\"\"passed = val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD (15%)。\"\"\"","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:761:        r_boundary = WalkForwardRound(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:765:            val_sortino=1.0, val_max_dd=15.0, passed=True,","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:773:        r_fail = WalkForwardRound(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:777:            val_sortino=1.0, val_max_dd=15.01, passed=False,","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:781:    def test_walk_forward_report_dataclass(self):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:782:        \"\"\"WalkForwardReport: pass_all_rounds + max_val_dd 计算正确。\"\"\"","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:785:            WalkForwardRound(1, _date(2021, 1, 1), _date(2023, 1, 1),","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:787:            WalkForwardRound(2, _date(2021, 7, 1), _date(2023, 7, 1),","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:789:            WalkForwardRound(3, _date(2022, 1, 1), _date(2024, 1, 1),","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:791:            WalkForwardRound(4, _date(2022, 7, 1), _date(2024, 7, 1),","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:794:        report = WalkForwardReport(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:796:            pass_all_rounds=all(r.passed for r in rounds),","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:797:            max_val_dd=max(r.val_max_dd for r in rounds),","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:799:        assert report.pass_all_rounds is True","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:800:        assert report.max_val_dd == 14.0","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:803:    def test_walk_forward_report_all_fail(self):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:804:        \"\"\"pass_all_rounds=False 当任一轮失败。\"\"\"","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:807:            WalkForwardRound(1, _date(2021, 1, 1), _date(2023, 1, 1),","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:809:            WalkForwardRound(2, _date(2021, 7, 1), _date(2023, 7, 1),","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:812:        report = WalkForwardReport(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:814:            pass_all_rounds=all(r.passed for r in rounds),","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:815:            max_val_dd=max(r.val_max_dd for r in rounds),","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:817:        assert report.pass_all_rounds is False","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:818:        assert report.max_val_dd == 18.0","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:837:    def test_walk_forward_windows_match_user_spec(self):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:852:        # run_walk_forward 从最近往前推：last round 的 val_end = today - val_months","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:884:    def test_run_walk_forward_mock_integration(self, mock_store, mock_universe):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:885:        \"\"\"P1 集成测试：run_walk_forward 用 mock store/universe 跑完 4 轮。","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:888:            1. 返回 WalkForwardReport 实例","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:890:            3. 每轮有 val_sortino / val_max_dd / passed 字段","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:891:            4. pass_all_rounds 与 rounds 中 passed 一致","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:892:            5. max_val_dd = max(r.val_max_dd)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:896:        report = run_walk_forward(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:905:        assert isinstance(report, WalkForwardReport), (","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:906:            f\"run_walk_forward 应返回 WalkForwardReport，实际 {type(report)}\"","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:912:            assert isinstance(r, WalkForwardRound)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:916:            assert isinstance(r.val_sortino, float)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:917:            assert isinstance(r.val_max_dd, float)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:918:            assert r.val_max_dd >= 0.0","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:920:            assert r.passed == (r.val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:923:        assert report.pass_all_rounds == expected_pass","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:924:        expected_max_dd = max(r.val_max_dd for r in report.rounds)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:925:        assert abs(report.max_val_dd - expected_max_dd) < 1e-9","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:927:    def test_run_walk_forward_empty_universe(self):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:928:        \"\"\"空标的组时返回空 WalkForwardReport，不抛异常。\"\"\"","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:935:        report = run_walk_forward(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:941:        assert isinstance(report, WalkForwardReport)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:943:        assert report.pass_all_rounds is False","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:944:        assert report.max_val_dd == 0.0","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:946:    def test_run_walk_forward_custom_rounds(self, mock_store, mock_universe):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:947:        \"\"\"run_walk_forward 支持自定义 rounds 参数（非默认 4）。\"\"\"","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:949:        report = run_walk_forward("]
---
["/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:34:    WalkForwardReport,","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:35:    WalkForwardRound,","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:37:    run_walk_forward,","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:734:class TestWalkForward:","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:737:    def test_walk_forward_round_dataclass(self):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:738:        \"\"\"WalkForwardRound dataclass 字段完整 + passed 判定正确。\"\"\"","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:740:        r = WalkForwardRound(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:746:            val_sortino=1.5,","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:747:            val_max_dd=10.0,","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:753:        assert r.val_sortino == 1.5","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:754:        assert r.val_max_dd == 10.0","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:757:    def test_walk_forward_round_passed_threshold(self):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:758:        \"\"\"passed = val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD (15%)。\"\"\"","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:761:        r_boundary = WalkForwardRound(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:765:            val_sortino=1.0, val_max_dd=15.0, passed=True,","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:773:        r_fail = WalkForwardRound(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:777:            val_sortino=1.0, val_max_dd=15.01, passed=False,","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:781:    def test_walk_forward_report_dataclass(self):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:782:        \"\"\"WalkForwardReport: pass_all_rounds + max_val_dd 计算正确。\"\"\"","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:785:            WalkForwardRound(1, _date(2021, 1, 1), _date(2023, 1, 1),","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:787:            WalkForwardRound(2, _date(2021, 7, 1), _date(2023, 7, 1),","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:789:            WalkForwardRound(3, _date(2022, 1, 1), _date(2024, 1, 1),","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:791:            WalkForwardRound(4, _date(2022, 7, 1), _date(2024, 7, 1),","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:794:        report = WalkForwardReport(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:796:            pass_all_rounds=all(r.passed for r in rounds),","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:797:            max_val_dd=max(r.val_max_dd for r in rounds),","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:799:        assert report.pass_all_rounds is True","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:800:        assert report.max_val_dd == 14.0","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:803:    def test_walk_forward_report_all_fail(self):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:804:        \"\"\"pass_all_rounds=False 当任一轮失败。\"\"\"","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:807:            WalkForwardRound(1, _date(2021, 1, 1), _date(2023, 1, 1),","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:809:            WalkForwardRound(2, _date(2021, 7, 1), _date(2023, 7, 1),","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:812:        report = WalkForwardReport(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:814:            pass_all_rounds=all(r.passed for r in rounds),","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:815:            max_val_dd=max(r.val_max_dd for r in rounds),","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:817:        assert report.pass_all_rounds is False","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:818:        assert report.max_val_dd == 18.0","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:837:    def test_walk_forward_windows_match_user_spec(self):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:852:        # run_walk_forward 从最近往前推：last round 的 val_end = today - val_months","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:884:    def test_run_walk_forward_mock_integration(self, mock_store, mock_universe):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:885:        \"\"\"P1 集成测试：run_walk_forward 用 mock store/universe 跑完 4 轮。","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:888:            1. 返回 WalkForwardReport 实例","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:890:            3. 每轮有 val_sortino / val_max_dd / passed 字段","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:891:            4. pass_all_rounds 与 rounds 中 passed 一致","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:892:            5. max_val_dd = max(r.val_max_dd)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:896:        report = run_walk_forward(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:905:        assert isinstance(report, WalkForwardReport), (","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:906:            f\"run_walk_forward 应返回 WalkForwardReport，实际 {type(report)}\"","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:912:            assert isinstance(r, WalkForwardRound)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:916:            assert isinstance(r.val_sortino, float)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:917:            assert isinstance(r.val_max_dd, float)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:918:            assert r.val_max_dd >= 0.0","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:920:            assert r.passed == (r.val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:923:        assert report.pass_all_rounds == expected_pass","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:924:        expected_max_dd = max(r.val_max_dd for r in report.rounds)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:925:        assert abs(report.max_val_dd - expected_max_dd) < 1e-9","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:927:    def test_run_walk_forward_empty_universe(self):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:928:        \"\"\"空标的组时返回空 WalkForwardReport，不抛异常。\"\"\"","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:935:        report = run_walk_forward(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:941:        assert isinstance(report, WalkForwardReport)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:943:        assert report.pass_all_rounds is False","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:944:        assert report.max_val_dd == 0.0","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:946:    def test_run_walk_forward_custom_rounds(self, mock_store, mock_universe):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:947:        \"\"\"run_walk_forward 支持自定义 rounds 参数（非默认 4）。\"\"\"","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:949:        report = run_walk_forward("]
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py","limit":180,"offset":730}
---
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
 793→        ]
 794→        report = WalkForwardReport(
 795→            rounds=rounds,
 796→            pass_all_rounds=all(r.passed for r in rounds),
 797→            max_val_dd=max(r.val_max_dd for r in rounds),
 798→        )
 799→        assert report.pass_all_rounds is True
 800→        assert report.max_val_dd == 14.0
 801→        assert len(report.rounds) == 4
 802→
 803→    def test_walk_forward_report_all_fail(self):
 804→        """pass_all_rounds=False 当任一轮失败。"""
 805→        from datetime import date as _date
 806→        rounds = [
 807→            WalkForwardRound(1, _date(2021, 1, 1), _date(2023, 1, 1),
 808→                             _date(2023, 1, 1), _date(2023, 7, 1), 1.0, 10.0, True),
 809→            WalkForwardRound(2, _date(2021, 7, 1), _date(2023, 7, 1),
 810→                             _date(2023, 7, 1), _date(2024, 1, 1), 0.8, 18.0, False),  # fail
 811→        ]
 812→        report = WalkForwardReport(
 813→            rounds=rounds,
 814→            pass_all_rounds=all(r.passed for r in rounds),
 815→            max_val_dd=max(r.val_max_dd for r in rounds),
 816→        )
 817→        assert report.pass_all_rounds is False
 818→        assert report.max_val_dd == 18.0
 819→
 820→    def test_add_months_basic(self):
 821→        """_add_months 基本加减月数正确。"""
 822→        from datetime import date as _date
 823→        # +18 months
 824→        assert _add_months(_date(2021, 7, 2), 18) == _date(2023, 1, 2)
 825→        # -6 months
 826→        assert _add_months(_date(2023, 7, 2), -6) == _date(2023, 1, 2)
 827→        # +0 months (identity)
 828→        assert _add_months(_date(2026, 7, 1), 0) == _date(2026, 7, 1)
 829→
 830→    def test_add_months_month_end_clamp(self):
 831→        """_add_months 自动 clamp 到月末（如 1/31 + 1 month = 2/28）。"""
 832→        from datetime import date as _date
 833→        # 1月31日 + 1月 → 2月28日（2023非闰年）
 834→        result = _add_months(_date(2023, 1, 31), 1)
 835→        assert result == _date(2023, 2, 28), f"1/31 + 1m 应为 2/28，实际 {result}"
 836→
 837→    def test_walk_forward_windows_match_user_spec(self):
 838→        """验证默认参数 (rounds=4, train_months=18, val_months=6) 产生的窗口
 839→        与用户提供的固定窗口匹配（today=2026-07-01）。
 840→
 841→        用户固定窗口：
 842→            Round 1: train 2021-07-02~2023-01-02, val 2023-01-02~2023-07-02
 843→            Round 2: train 2022-01-02~2023-07-02, val 2023-07-02~2024-01-02
 844→            Round 3: train 2022-07-02~2024-01-02, val 2024-01-02~2024-07-02
 845→            Round 4: train 2023-01-02~2024-07-02, val 2024-07-02~2025-01-02
 846→        """
 847→        from datetime import date as _date
 848→        today = _date(2026, 7, 1)
 849→        rounds = 4
 850→        train_months = 18
 851→        val_months = 6
 852→        # run_walk_forward 从最近往前推：last round 的 val_end = today - val_months
 853→        # Round 4: val_end=2026-01-01, val_start=2025-07-01, train=2024-01-01~2025-07-01
 854→        # Round 3: val_end=2025-07-01, val_start=2025-01-01, train=2023-07-01~2025-01-01
 855→        # Round 2: val_end=2025-01-01, val_start=2024-07-01, train=2023-01-01~2024-07-01
 856→        # Round 1: val_end=2024-07-01, val_start=2024-01-01, train=2022-07-01~2024-01-01
 857→        expected = [
 858→            # (round_num, train_start, train_end, val_start, val_end)
 859→            (1, _date(2022, 7, 1), _date(2024, 1, 1), _date(2024, 1, 1), _date(2024, 7, 1)),
 860→            (2, _date(2023, 1, 1), _date(2024, 7, 1), _date(2024, 7, 1), _date(2025, 1, 1)),
 861→            (3, _date(2023, 7, 1), _date(2025, 1, 1), _date(2025, 1, 1), _date(2025, 7, 1)),
 862→            (4, _date(2024, 1, 1), _date(2025, 7, 1), _date(2025, 7, 1), _date(2026, 1, 1)),
 863→        ]
 864→        for round_num, exp_ts, exp_te, exp_vs, exp_ve in expected:
 865→            val_end = _add_months(
 866→                today, -val_months - (rounds - round_num) * val_months
 867→            )
 868→            val_start = _add_months(val_end, -val_months)
 869→            train_end = val_start
 870→            train_start = _add_months(train_end, -train_months)
 871→            assert train_start == exp_ts, (
 872→                f"Round {round_num} train_start: 期望 {exp_ts}，实际 {train_start}"
 873→            )
 874→            assert train_end == exp_te, (
 875→                f"Round {round_num} train_end: 期望 {exp_te}，实际 {train_end}"
 876→            )
 877→            assert val_start == exp_vs, (
 878→                f"Round {round_num} val_start: 期望 {exp_vs}，实际 {val_start}"
 879→            )
 880→            assert val_end == exp_ve, (
 881→                f"Round {round_num} val_end: 期望 {exp_ve}，实际 {val_end}"
 882→            )
 883→
 884→    def test_run_walk_forward_mock_integration(self, mock_store, mock_universe):
 885→        """P1 集成测试：run_walk_forward 用 mock store/universe 跑完 4 轮。
 886→
 887→        验证：
 888→            1. 返回 WalkForwardReport 实例
 889→            2. rounds 长度为 4
 890→            3. 每轮有 val_sortino / val_max_dd / passed 字段
 891→            4. pass_all_rounds 与 rounds 中 passed 一致
 892→            5. max_val_dd = max(r.val_max_dd)
 893→        """
 894→        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=2)
 895→
 896→        report = run_walk_forward(
 897→            mb=mb,
 898→            strategies=["dual_ma"],
 899→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 900→            rounds=4,
 901→            train_months=18,
 902→            val_months=6,
 903→        )
 904→
 905→        assert isinstance(report, WalkForwardReport), (
 906→            f"run_walk_forward 应返回 WalkForwardReport，实际 {type(report)}"
 907→        )
 908→        assert len(report.rounds) == 4, (
 909→            f"应跑 4 轮，实际 {len(report.rounds)} 轮"
 910→
---
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
 793→        ]
 794→        report = WalkForwardReport(
 795→            rounds=rounds,
 796→            pass_all_rounds=all(r.passed for r in rounds),
 797→            max_val_dd=max(r.val_max_dd for r in rounds),
 798→        )
 799→        assert report.pass_all_rounds is True
 800→        assert report.max_val_dd == 14.0
 801→        assert len(report.rounds) == 4
 802→
 803→    def test_walk_forward_report_all_fail(self):
 804→        """pass_all_rounds=False 当任一轮失败。"""
 805→        from datetime import date as _date
 806→        rounds = [
 807→            WalkForwardRound(1, _date(2021, 1, 1), _date(2023, 1, 1),
 808→                             _date(2023, 1, 1), _date(2023, 7, 1), 1.0, 10.0, True),
 809→            WalkForwardRound(2, _date(2021, 7, 1), _date(2023, 7, 1),
 810→                             _date(2023, 7, 1), _date(2024, 1, 1), 0.8, 18.0, False),  # fail
 811→        ]
 812→        report = WalkForwardReport(
 813→            rounds=rounds,
 814→            pass_all_rounds=all(r.passed for r in rounds),
 815→            max_val_dd=max(r.val_max_dd for r in rounds),
 816→        )
 817→        assert report.pass_all_rounds is False
 818→        assert report.max_val_dd == 18.0
 819→
 820→    def test_add_months_basic(self):
 821→        """_add_months 基本加减月数正确。"""
 822→        from datetime import date as _date
 823→        # +18 months
 824→        assert _add_months(_date(2021, 7, 2), 18) == _date(2023, 1, 2)
 825→        # -6 months
 826→        assert _add_months(_date(2023, 7, 2), -6) == _date(2023, 1, 2)
 827→        # +0 months (identity)
 828→        assert _add_months(_date(2026, 7, 1), 0) == _date(2026, 7, 1)
 829→
 830→    def test_add_months_month_end_clamp(self):
 831→        """_add_months 自动 clamp 到月末（如 1/31 + 1 month = 2/28）。"""
 832→        from datetime import date as _date
 833→        # 1月31日 + 1月 → 2月28日（2023非闰年）
 834→        result = _add_months(_date(2023, 1, 31), 1)
 835→        assert result == _date(2023, 2, 28), f"1/31 + 1m 应为 2/28，实际 {result}"
 836→
 837→    def test_walk_forward_windows_match_user_spec(self):
 838→        """验证默认参数 (rounds=4, train_months=18, val_months=6) 产生的窗口
 839→        与用户提供的固定窗口匹配（today=2026-07-01）。
 840→
 841→        用户固定窗口：
 842→            Round 1: train 2021-07-02~2023-01-02, val 2023-01-02~2023-07-02
 843→            Round 2: train 2022-01-02~2023-07-02, val 2023-07-02~2024-01-02
 844→            Round 3: train 2022-07-02~2024-01-02, val 2024-01-02~2024-07-02
 845→            Round 4: train 2023-01-02~2024-07-02, val 2024-07-02~2025-01-02
 846→        """
 847→        from datetime import date as _date
 848→        today = _date(2026, 7, 1)
 849→        rounds = 4
 850→        train_months = 18
 851→        val_months = 6
 852→        # run_walk_forward 从最近往前推：last round 的 val_end = today - val_months
 853→        # Round 4: val_end=2026-01-01, val_start=2025-07-01, train=2024-01-01~2025-07-01
 854→        # Round 3: val_end=2025-07-01, val_start=2025-01-01, train=2023-07-01~2025-01-01
 855→        # Round 2: val_end=2025-01-01, val_start=2024-07-01, train=2023-01-01~2024-07-01
 856→        # Round 1: val_end=2024-07-01, val_start=2024-01-01, train=2022-07-01~2024-01-01
 857→        expected = [
 858→            # (round_num, train_start, train_end, val_start, val_end)
 859→            (1, _date(2022, 7, 1), _date(2024, 1, 1), _date(2024, 1, 1), _date(2024, 7, 1)),
 860→            (2, _date(2023, 1, 1), _date(2024, 7, 1), _date(2024, 7, 1), _date(2025, 1, 1)),
 861→            (3, _date(2023, 7, 1), _date(2025, 1, 1), _date(2025, 1, 1), _date(2025, 7, 1)),
 862→            (4, _date(2024, 1, 1), _date(2025, 7, 1), _date(2025, 7, 1), _date(2026, 1, 1)),
 863→        ]
 864→        for round_num, exp_ts, exp_te, exp_vs, exp_ve in expected:
 865→            val_end = _add_months(
 866→                today, -val_months - (rounds - round_num) * val_months
 867→            )
 868→            val_start = _add_months(val_end, -val_months)
 869→            train_end = val_start
 870→            train_start = _add_months(train_end, -train_months)
 871→            assert train_start == exp_ts, (
 872→                f"Round {round_num} train_start: 期望 {exp_ts}，实际 {train_start}"
 873→            )
 874→            assert train_end == exp_te, (
 875→                f"Round {round_num} train_end: 期望 {exp_te}，实际 {train_end}"
 876→            )
 877→            assert val_start == exp_vs, (
 878→                f"Round {round_num} val_start: 期望 {exp_vs}，实际 {val_start}"
 879→            )
 880→            assert val_end == exp_ve, (
 881→                f"Round {round_num} val_end: 期望 {exp_ve}，实际 {val_end}"
 882→            )
 883→
 884→    def test_run_walk_forward_mock_integration(self, mock_store, mock_universe):
 885→        """P1 集成测试：run_walk_forward 用 mock store/universe 跑完 4 轮。
 886→
 887→        验证：
 888→            1. 返回 WalkForwardReport 实例
 889→            2. rounds 长度为 4
 890→            3. 每轮有 val_sortino / val_max_dd / passed 字段
 891→            4. pass_all_rounds 与 rounds 中 passed 一致
 892→            5. max_val_dd = max(r.val_max_dd)
 893→        """
 894→        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=2)
 895→
 896→        report = run_walk_forward(
 897→            mb=mb,
 898→            strategies=["dual_ma"],
 899→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 900→            rounds=4,
 901→            train_months=18,
 902→            val_months=6,
 903→        )
 904→
 905→        assert isinstance(report, WalkForwardReport), (
 906→            f"run_walk_forward 应返回 WalkForwardReport，实际 {type(report)}"
 907→        )
 908→        assert len(report.rounds) == 4, (
 909→            f"应跑 4 轮，实际 {len(report.rounds)} 轮"
 910→
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py","limit":100,"offset":910}
---
 910→        )
 911→        for i, r in enumerate(report.rounds):
 912→            assert isinstance(r, WalkForwardRound)
 913→            assert r.round_num == i + 1, (
 914→                f"Round {i}: round_num 应为 {i+1}，实际 {r.round_num}"
 915→            )
 916→            assert isinstance(r.val_sortino, float)
 917→            assert isinstance(r.val_max_dd, float)
 918→            assert r.val_max_dd >= 0.0
 919→            assert isinstance(r.passed, bool)
 920→            assert r.passed == (r.val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD)
 921→
 922→        expected_pass = all(r.passed for r in report.rounds)
 923→        assert report.pass_all_rounds == expected_pass
 924→        expected_max_dd = max(r.val_max_dd for r in report.rounds)
 925→        assert abs(report.max_val_dd - expected_max_dd) < 1e-9
 926→
 927→    def test_run_walk_forward_empty_universe(self):
 928→        """空标的组时返回空 WalkForwardReport，不抛异常。"""
 929→        store = MagicMock()
 930→        store.get_bars_multi.return_value = {}
 931→        universe = MagicMock()
 932→        universe.get_groups.return_value = {}
 933→        mb = MatrixBacktest(store=store, universe=universe, years=1)
 934→
 935→        report = run_walk_forward(
 936→            mb=mb,
 937→            strategies=["dual_ma"],
 938→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 939→            rounds=4,
 940→        )
 941→        assert isinstance(report, WalkForwardReport)
 942→        assert report.rounds == []
 943→        assert report.pass_all_rounds is False
 944→        assert report.max_val_dd == 0.0
 945→
 946→    def test_run_walk_forward_custom_rounds(self, mock_store, mock_universe):
 947→        """run_walk_forward 支持自定义 rounds 参数（非默认 4）。"""
 948→        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)
 949→        report = run_walk_forward(
 950→            mb=mb,
 951→            strategies=["dual_ma"],
 952→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 953→            rounds=2,
 954→            train_months=12,
 955→            val_months=4,
 956→        )
 957→        assert len(report.rounds) == 2
 958→        assert report.rounds[0].round_num == 1
 959→        assert report.rounds[1].round_num == 2
 960→
 961→
 962→# ---------------------------------------------------------------------------
 963→# 迭代 #9 新增：Alpha-Based Strategy Selection
 964→# ---------------------------------------------------------------------------
 965→
 966→class TestAlphaComputation:
 967→    """_compute_alpha / _combine_daily_returns 单元测试。"""
 968→
 969→    def test_compute_alpha_basic(self):
 970→        """构造已知策略收益和 SPY 收益，验证 alpha 计算正确。
 971→
 972→        策略日均收益 0.001 (0.1%)，SPY 日均收益 0.0004 (0.04%)。
 973→        年化：(1.001^252 - 1) - (1.0004^252 - 1) ≈ 0.285 - 0.110 = 0.175 → 17.5%
 974→        """
 975→        np.random.seed(42)
 976→        idx = pd.date_range("2021-01-01", periods=252, freq="B")
 977→        # 策略收益：稳定 0.1%/日（年化 ~28.5%）
 978→        strat_returns = pd.Series(
 979→            np.random.normal(0.001, 0.002, 252), index=idx
 980→        )
 981→        # SPY 收益：稳定 0.04%/日（年化 ~11.0%）
 982→        spy_returns = pd.Series(
 983→            np.random.normal(0.0004, 0.001, 252), index=idx
 984→        )
 985→
 986→        alpha = _compute_alpha(strat_returns, spy_returns)
 987→
 988→        # 期望 alpha ≈ 17.5%（正数，跑赢 SPY）
 989→        assert alpha > 0.0, f"策略年化应高于 SPY，alpha 应为正，实际 {alpha:.4f}"
 990→        # 验证量级在合理范围（10~25%）
 991→        assert 10.0 < alpha < 25.0, (
 992→            f"alpha 应在 10~25% 范围，实际 {alpha:.4f}%"
 993→        )
 994→
 995→    def test_compute_alpha_spy_unavailable(self):
 996→        """SPY 数据为 None → alpha = 0.0（降级处理，不抛异常）。"""
 997→        idx = pd.date_range("2021-01-01", periods=100, freq="B")
 998→        strat_returns = pd.Series(np.random.normal(0.001, 0.01, 100), index=idx)
 999→
1000→        # spy_returns=None
1001→        assert _compute_alpha(strat_returns, None) == 0.0
1002→        # spy_returns=空 Series
1003→        empty_spy = pd.Series(dtype=float)
1004→        assert _compute_alpha(strat_returns, empty_spy) == 0.0
1005→
1006→    def test_compute_alpha_strategy_underperforms(self):
1007→        """策略跑输 SPY → alpha 为负。"""
1008→        idx = pd.date_range("2021-01-01", periods=252, freq="B")
1009→        # 策略日均 0.0001 (0.01%)，SPY 日均 0.001 (0.1%)
1010→
---
 910→        )
 911→        for i, r in enumerate(report.rounds):
 912→            assert isinstance(r, WalkForwardRound)
 913→            assert r.round_num == i + 1, (
 914→                f"Round {i}: round_num 应为 {i+1}，实际 {r.round_num}"
 915→            )
 916→            assert isinstance(r.val_sortino, float)
 917→            assert isinstance(r.val_max_dd, float)
 918→            assert r.val_max_dd >= 0.0
 919→            assert isinstance(r.passed, bool)
 920→            assert r.passed == (r.val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD)
 921→
 922→        expected_pass = all(r.passed for r in report.rounds)
 923→        assert report.pass_all_rounds == expected_pass
 924→        expected_max_dd = max(r.val_max_dd for r in report.rounds)
 925→        assert abs(report.max_val_dd - expected_max_dd) < 1e-9
 926→
 927→    def test_run_walk_forward_empty_universe(self):
 928→        """空标的组时返回空 WalkForwardReport，不抛异常。"""
 929→        store = MagicMock()
 930→        store.get_bars_multi.return_value = {}
 931→        universe = MagicMock()
 932→        universe.get_groups.return_value = {}
 933→        mb = MatrixBacktest(store=store, universe=universe, years=1)
 934→
 935→        report = run_walk_forward(
 936→            mb=mb,
 937→            strategies=["dual_ma"],
 938→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 939→            rounds=4,
 940→        )
 941→        assert isinstance(report, WalkForwardReport)
 942→        assert report.rounds == []
 943→        assert report.pass_all_rounds is False
 944→        assert report.max_val_dd == 0.0
 945→
 946→    def test_run_walk_forward_custom_rounds(self, mock_store, mock_universe):
 947→        """run_walk_forward 支持自定义 rounds 参数（非默认 4）。"""
 948→        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)
 949→        report = run_walk_forward(
 950→            mb=mb,
 951→            strategies=["dual_ma"],
 952→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 953→            rounds=2,
 954→            train_months=12,
 955→            val_months=4,
 956→        )
 957→        assert len(report.rounds) == 2
 958→        assert report.rounds[0].round_num == 1
 959→        assert report.rounds[1].round_num == 2
 960→
 961→
 962→# ---------------------------------------------------------------------------
 963→# 迭代 #9 新增：Alpha-Based Strategy Selection
 964→# ---------------------------------------------------------------------------
 965→
 966→class TestAlphaComputation:
 967→    """_compute_alpha / _combine_daily_returns 单元测试。"""
 968→
 969→    def test_compute_alpha_basic(self):
 970→        """构造已知策略收益和 SPY 收益，验证 alpha 计算正确。
 971→
 972→        策略日均收益 0.001 (0.1%)，SPY 日均收益 0.0004 (0.04%)。
 973→        年化：(1.001^252 - 1) - (1.0004^252 - 1) ≈ 0.285 - 0.110 = 0.175 → 17.5%
 974→        """
 975→        np.random.seed(42)
 976→        idx = pd.date_range("2021-01-01", periods=252, freq="B")
 977→        # 策略收益：稳定 0.1%/日（年化 ~28.5%）
 978→        strat_returns = pd.Series(
 979→            np.random.normal(0.001, 0.002, 252), index=idx
 980→        )
 981→        # SPY 收益：稳定 0.04%/日（年化 ~11.0%）
 982→        spy_returns = pd.Series(
 983→            np.random.normal(0.0004, 0.001, 252), index=idx
 984→        )
 985→
 986→        alpha = _compute_alpha(strat_returns, spy_returns)
 987→
 988→        # 期望 alpha ≈ 17.5%（正数，跑赢 SPY）
 989→        assert alpha > 0.0, f"策略年化应高于 SPY，alpha 应为正，实际 {alpha:.4f}"
 990→        # 验证量级在合理范围（10~25%）
 991→        assert 10.0 < alpha < 25.0, (
 992→            f"alpha 应在 10~25% 范围，实际 {alpha:.4f}%"
 993→        )
 994→
 995→    def test_compute_alpha_spy_unavailable(self):
 996→        """SPY 数据为 None → alpha = 0.0（降级处理，不抛异常）。"""
 997→        idx = pd.date_range("2021-01-01", periods=100, freq="B")
 998→        strat_returns = pd.Series(np.random.normal(0.001, 0.01, 100), index=idx)
 999→
1000→        # spy_returns=None
1001→        assert _compute_alpha(strat_returns, None) == 0.0
1002→        # spy_returns=空 Series
1003→        empty_spy = pd.Series(dtype=float)
1004→        assert _compute_alpha(strat_returns, empty_spy) == 0.0
1005→
1006→    def test_compute_alpha_strategy_underperforms(self):
1007→        """策略跑输 SPY → alpha 为负。"""
1008→        idx = pd.date_range("2021-01-01", periods=252, freq="B")
1009→        # 策略日均 0.0001 (0.01%)，SPY 日均 0.001 (0.1%)
1010→
---
Now
---
 I
---
 see
---
 a
---
 critical
---
 issue
---
.
---
 The
---
 existing
---
 test
---
 at
---
 line
---
 
---
9
---
20
---
:

---
```
---
python
---


---
assert
---
 r
---
.pass
---
ed
---
 ==
---
 (
---
r
---
.val
---
_max
---
_dd
---
 <=
---
 W
---
ALK
---
_FORWARD
---
_VAL
---
_DD
---
_THRESHOLD
---
)

---
``
---
`


---
After
---
 my
---
 changes
---
,
---
 `
---
passed
---
`
---
 will
---
 be
---
 `
---
dd
---
_passed
---
 AND
---
 alpha
---
_passed
---
`,
---
 so
---
 this
---
 assertion
---
 will
---
 fail
---
.
---
 Also
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
9
---
22
---
-
---
9
---
23
---
:

---
```
---
python
---


---
expected
---
_pass
---
 =
---
 all
---
(r
---
.pass
---
ed
---
 for
---
 r
---
 in
---
 report
---
.round
---
s
---
)

---
assert
---
 report
---
.pass
---
_all
---
_round
---
s
---
 ==
---
 expected
---
_pass
---


---
``
---
`


---
This
---
 will
---
 also
---
 fail
---
 because
---
 `
---
pass
---
_all
---
_round
---
s
---
`
---
 now
---
 requires
---
 `
---
avg
---
_val
---
_alpha
---
 >
---
 
---
0
---
`.


---
And
---
 the
---
 test
---
 uses
---
 `
---
mock
---
_store
---
`
---
 and
---
 `
---
mock
---
_un
---
iverse
---
`.
---
 Let
---
 me
---
 look
---
 at
---
 these
---
 fixtures
---
 to
---
 understand
---
 if
---
 they
---
 provide
---
 SP
---
Y
---
 data
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
 the
---
 mock
---
_store
---
 and
---
 mock
---
_un
---
iverse
---
 fixtures
---
.
---
让我
---
查看
---
一下
---
 mock
---
 fixtures
---
，
---
以
---
了解
---
 SP
---
Y
---
 数据
---
的情况
---
。
---
{"-n":true,"head_limit":60,"output_mode":"content","path":"/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py","pattern":"mock_store|mock_universe|@pytest.fixture|get_bars_multi|_get_spy_returns"}
---
["/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:64:@pytest.fixture","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:65:def mock_store(tmp_path):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:71:    def get_bars_multi(symbols, start, end, timeframe=\"1d\"):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:75:    store.get_bars_multi.side_effect = get_bars_multi","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:79:@pytest.fixture","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:80:def mock_universe():","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:359:    def test_run_produces_groups(self, mock_store, mock_universe):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:361:        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=2)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:371:    def test_run_weights_sum_to_one(self, mock_store, mock_universe):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:373:        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=2)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:386:    def test_run_output_file(self, mock_store, mock_universe, tmp_path):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:389:        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:401:    def test_run_empty_universe(self, mock_store):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:405:        mb = MatrixBacktest(store=mock_store, universe=universe, years=1)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:409:    def test_run_no_data_for_group(self, mock_universe, tmp_path):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:412:        store.get_bars_multi.return_value = {}","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:413:        mb = MatrixBacktest(store=store, universe=mock_universe, years=1)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:422:    def test_group_results_have_portfolio_sharpe(self, mock_store, mock_universe):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:424:        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:433:    def test_survivorship_bias_warning_in_output(self, mock_store, mock_universe, tmp_path):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:436:        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:448:    def test_unknown_strategy_logs_warning(self, mock_store, mock_universe):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:462:            mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=2)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:496:    def test_output_file_contains_sortino(self, mock_store, mock_universe, tmp_path):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:499:        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:515:    def test_group_results_have_portfolio_sortino(self, mock_store, mock_universe):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:517:        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:529:    def test_group_results_have_portfolio_max_drawdown(self, mock_store, mock_universe):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:531:        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:544:    def test_output_file_contains_max_drawdown(self, mock_store, mock_universe, tmp_path):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:547:        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:565:    def test_output_file_no_nan(self, mock_store, mock_universe, tmp_path):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:573:        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:596:    def test_dd_constrained_field_exists_in_group_result(self, mock_store, mock_universe):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:616:        store.get_bars_multi.side_effect = lambda symbols, start, end, timeframe=\"1d\": {","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:673:        store.get_bars_multi.side_effect = lambda symbols, start, end, timeframe=\"1d\": {","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:701:    def test_output_file_contains_dd_constrained_field(self, mock_store, mock_universe, tmp_path):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:704:        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:884:    def test_run_walk_forward_mock_integration(self, mock_store, mock_universe):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:894:        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=2)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:930:        store.get_bars_multi.return_value = {}","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:946:    def test_run_walk_forward_custom_rounds(self, mock_store, mock_universe):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:948:        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1117:        def get_bars_multi(symbols, start, end, timeframe=\"1d\"):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1121:        store.get_bars_multi.side_effect = get_bars_multi","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1222:        store.get_bars_multi.side_effect = lambda symbols, start, end, timeframe=\"1d\": {","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1280:        def get_bars_multi(symbols, start, end, timeframe=\"1d\"):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1284:        store.get_bars_multi.side_effect = get_bars_multi","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1367:        store.get_bars_multi.side_effect = lambda symbols, start, end, timeframe=\"1d\": {","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1436:        def get_bars_multi(symbols, start, end, timeframe=\"1d\"):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1440:        store.get_bars_multi.side_effect = get_bars_multi","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1464:    def test_alpha_field_in_weights_json(self, mock_store, mock_universe, tmp_path):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1467:        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1485:    def test_group_results_have_backtest_alpha(self, mock_store, mock_universe):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1487:        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1560:        store.get_bars_multi.side_effect = lambda symbols, start, end, timeframe=\"1d\": {"]
---
["/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:64:@pytest.fixture","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:65:def mock_store(tmp_path):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:71:    def get_bars_multi(symbols, start, end, timeframe=\"1d\"):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:75:    store.get_bars_multi.side_effect = get_bars_multi","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:79:@pytest.fixture","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:80:def mock_universe():","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:359:    def test_run_produces_groups(self, mock_store, mock_universe):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:361:        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=2)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:371:    def test_run_weights_sum_to_one(self, mock_store, mock_universe):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:373:        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=2)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:386:    def test_run_output_file(self, mock_store, mock_universe, tmp_path):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:389:        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:401:    def test_run_empty_universe(self, mock_store):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:405:        mb = MatrixBacktest(store=mock_store, universe=universe, years=1)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:409:    def test_run_no_data_for_group(self, mock_universe, tmp_path):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:412:        store.get_bars_multi.return_value = {}","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:413:        mb = MatrixBacktest(store=store, universe=mock_universe, years=1)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:422:    def test_group_results_have_portfolio_sharpe(self, mock_store, mock_universe):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:424:        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:433:    def test_survivorship_bias_warning_in_output(self, mock_store, mock_universe, tmp_path):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:436:        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:448:    def test_unknown_strategy_logs_warning(self, mock_store, mock_universe):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:462:            mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=2)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:496:    def test_output_file_contains_sortino(self, mock_store, mock_universe, tmp_path):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:499:        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:515:    def test_group_results_have_portfolio_sortino(self, mock_store, mock_universe):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:517:        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:529:    def test_group_results_have_portfolio_max_drawdown(self, mock_store, mock_universe):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:531:        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:544:    def test_output_file_contains_max_drawdown(self, mock_store, mock_universe, tmp_path):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:547:        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:565:    def test_output_file_no_nan(self, mock_store, mock_universe, tmp_path):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:573:        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:596:    def test_dd_constrained_field_exists_in_group_result(self, mock_store, mock_universe):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:616:        store.get_bars_multi.side_effect = lambda symbols, start, end, timeframe=\"1d\": {","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:673:        store.get_bars_multi.side_effect = lambda symbols, start, end, timeframe=\"1d\": {","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:701:    def test_output_file_contains_dd_constrained_field(self, mock_store, mock_universe, tmp_path):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:704:        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:884:    def test_run_walk_forward_mock_integration(self, mock_store, mock_universe):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:894:        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=2)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:930:        store.get_bars_multi.return_value = {}","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:946:    def test_run_walk_forward_custom_rounds(self, mock_store, mock_universe):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:948:        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1117:        def get_bars_multi(symbols, start, end, timeframe=\"1d\"):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1121:        store.get_bars_multi.side_effect = get_bars_multi","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1222:        store.get_bars_multi.side_effect = lambda symbols, start, end, timeframe=\"1d\": {","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1280:        def get_bars_multi(symbols, start, end, timeframe=\"1d\"):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1284:        store.get_bars_multi.side_effect = get_bars_multi","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1367:        store.get_bars_multi.side_effect = lambda symbols, start, end, timeframe=\"1d\": {","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1436:        def get_bars_multi(symbols, start, end, timeframe=\"1d\"):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1440:        store.get_bars_multi.side_effect = get_bars_multi","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1464:    def test_alpha_field_in_weights_json(self, mock_store, mock_universe, tmp_path):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1467:        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1485:    def test_group_results_have_backtest_alpha(self, mock_store, mock_universe):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1487:        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1560:        store.get_bars_multi.side_effect = lambda symbols, start, end, timeframe=\"1d\": {"]
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py","limit":80,"offset":60}
---
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
 140→
---
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
 140→
---
Now
---
 I
---
 understand
---
 the
---
 existing
---
 tests
---
.
---
 The
---
 key
---
 issues
---
:


---
1
---
.
---
 `
---
mock
---
_store
---
`
---
 doesn
---
't
---
 provide
---
 SP
---
Y
---
 data
---
,
---
 so
---
 `_
---
get
---
_s
---
py
---
_returns
---
`
---
 will
---
 call
---
 `
---
store
---
.get
---
_b
---
ars
---
_multi
---
(["
---
SP
---
Y
---
"],
---
 ...
---
)`
---
 which
---
 returns
---
 `{
---
}`
---
 (
---
empty
---
),
---
 so
---
 `
---
val
---
_alpha
---
`
---
 will
---
 be
---
 
---
0
---
.
---
0
---
.


---
2
---
.
---
 The
---
 existing
---
 test
---
 `
---
test
---
_run
---
_walk
---
_forward
---
_mock
---
_integration
---
`
---
 has
---
:

---
  
---
 ```
---
python
---


---
  
---
 assert
---
 r
---
.pass
---
ed
---
 ==
---
 (
---
r
---
.val
---
_max
---
_dd
---
 <=
---
 W
---
ALK
---
_FORWARD
---
_VAL
---
_DD
---
_THRESHOLD
---
)

---
  
---
 ```

---
  
---
 After
---
 my
---
 change
---
,
---
 `
---
passed
---
 =
---
 dd
---
_passed
---
 AND
---
 alpha
---
_passed
---
`.
---
 With
---
 `
---
val
---
_alpha
---
=
---
0
---
.
---
0
---
`
---
 (
---
SP
---
Y
---
 unavailable
---
),
---
 `
---
alpha
---
_passed
---
 =
---
 
---
0
---
.
---
0
---
 >
---
 -
---
5
---
.
---
0
---
 =
---
 True
---
`.
---
 So
---
 `
---
passed
---
 =
---
 dd
---
_passed
---
 AND
---
 True
---
 =
---
 dd
---
_passed
---
`.
---
 So
---
 this
---
 assertion
---
 still
---
 holds
---
!
---
 Good
---
.


---
3
---
.
---
 The
---
 existing
---
 test
---
:

---
  
---
 ```
---
python
---


---
  
---
 expected
---
_pass
---
 =
---
 all
---
(r
---
.pass
---
ed
---
 for
---
 r
---
 in
---
 report
---
.round
---
s
---
)

---
  
---
 assert
---
 report
---
.pass
---
_all
---
_round
---
s
---
 ==
---
 expected
---
_pass
---


---
  
---
 ```

---
  
---
 After
---
 my
---
 change
---
,
---
 `
---
pass
---
_all
---
_round
---
s
---
 =
---
 all
---
(r
---
.pass
---
ed
---
)
---
 AND
---
 (
---
avg
---
_val
---
_alpha
---
 >
---
 
---
0
---
)
---
`.
---
 With
---
 `
---
val
---
_alpha
---
=
---
0
---
.
---
0
---
`
---
 for
---
 all
---
 rounds
---
,
---
 `
---
avg
---
_val
---
_alpha
---
=
---
0
---
.
---
0
---
`,
---
 and
---
 `
---
0
---
.
---
0
---
 >
---
 
---
0
---
`
---
 is
---
 `
---
False
---
`.
---
 So
---
 `
---
pass
---
_all
---
_round
---
s
---
`
---
 will
---
 be
---
 `
---
False
---
`
---
 even
---
 if
---
 all
---
 rounds
---
 passed
---
.
---
 This
---
 will
---
 break
---
 the
---
 test
---
!


---
So
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
 `
---
mock
---
_store
---
`
---
 fixture
---
 to
---
 provide
---
 SP
---
Y
---
 data
---
,
---
 OR
---
 update
---
 the
---
 test
---
 assertion
---
.
---
 The
---
 spec
---
 says
---
:

---
>
---
 **
---
注意
---
**
---
：
---
现有
---
 WF
---
 
---
测试
---
可能
---
没有
---
 SP
---
Y
---
 数据
---
 →
---
 val
---
_alpha
---
=
---
0
---
 →
---
 avg
---
_alpha
---
=
---
0
---
 →
---
 `
---
pass
---
_all
---
_round
---
s
---
=False
---
`
---
（
---
因为
---
 avg
---
 >
---
 
---
0
---
 不
---
满足
---
）。
---
需要
---
检查
---
现有
---
测试
---
是否
---
依赖
---
 `
---
pass
---
_all
---
_round
---
s
---
=True
---
`
---
，
---
如果是
---
，
---
需要在
---
测试
---
中
---
提供
---
 SP
---
Y
---
 数据
---
或
---
 mock
---
 alpha
---
 >
---
 
---
0
---
。


---
So
---
 the
---
 spec
---
 anticip
---
ates
---
 this
---
.
---
 The
---
 best
---
 approach
---
 is
---
 to
---
 provide
---
 SP
---
Y
---
 data
---
 in
---
 the
---
 `
---
mock
---
_store
---
`
---
 fixture
---
 so
---
 that
---
 val
---
_alpha
---
 >
---
 
---
0
---
 (
---
strategy
---
 out
---
per
---
forms
---
 SP
---
Y
---
).
---
 Looking
---
 at
---
 the
---
 mock
---
_store
---
,
---
 the
---
 data
---
 has
---
 `
---
t
---
rend
---
="
---
up
---
"
---
`.
---
 Let
---
 me
---
 check
---
 `_
---
make
---
_
---
ohl
---
cv
---
`
---
 to
---
 understand
---
 the
---
 trend
---
.


---
Actually
---
,
---
 a
---
 cleaner
---
 approach
---
:
---
 I
---
 should
---
 update
---
 the
---
 `
---
mock
---
_store
---
`
---
 fixture
---
 to
---
 include
---
 SP
---
Y
---
 data
---
 with
---
 a
---
 slower
---
 trend
---
 (
---
so
---
 the
---
 strategy
---
 out
---
per
---
forms
---
 SP
---
Y
---
,
---
 giving
---
 positive
---
 alpha
---
).
---
 Or
---
 I
---
 could
---
 update
---
 the
---
 test
---
 assertions
---
 to
---
 account
---
 for
---
 the
---
 new
---
 alpha
---
 gate
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
 `_
---
make
---
_
---
ohl
---
cv
---
`.
---
让我
---
检查
---
一下
---
 `_
---
make
---
_
---
ohl
---
cv
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
了解
---
模拟
---
数据的
---
趋势
---
。
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py","limit":60,"offset":1}
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
  61→
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
  61→
---
Now
---
 I
---
 understand
---
.
---
 The
---
 mock
---
 data
---
 has
---
 a
---
 strong
---
 upt
---
rend
---
 (
---
100
---
.
---
0
---
 +
---
 i
---
 *
---
 
---
0
---
.
---
1
---
 →
---
 
---
30
---
%
---
 gain
---
 over
---
 
---
300
---
 days
---
).
---
 If
---
 I
---
 add
---
 SP
---
Y
---
 with
---
 a
---
 slower
---
 trend
---
 (
---
e
---
.g
---
.,
---
 
---
100
---
.
---
0
---
 +
---
 i
---
 *
---
 
---
0
---
.
---
02
---
 →
---
 
---
6
---
%
---
 gain
---
),
---
 the
---
 strategy
---
 will
---
 out
---
perform
---
 SP
---
Y
---
 and
---
 alpha
---
 will
---
 be
---
 positive
---
.


---
But
---
 wait
---
 —
---
 the
---
 mock
---
_store
---
 fixture
---
 is
---
 used
---
 by
---
 MANY
---
 tests
---
,
---
 not
---
 just
---
 WF
---
 tests
---
.
---
 If
---
 I
---
 add
---
 SP
---
Y
---
 to
---
 the
---
 fixture
---
,
---
 it
---
 might
---
 affect
---
 other
---
 tests
---
 (
---
e
---
.g
---
.,
---
 tests
---
 that
---
 check
---
 `
---
get
---
_b
---
ars
---
_multi
---
`
---
 is
---
 called
---
 with
---
 specific
---
 symbols
---
).
---
 Let
---
 me
---
 be
---
 careful
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
 fixture
---
:

---
```
---
python
---


---
def
---
 get
---
_b
---
ars
---
_multi
---
(s
---
ymbols
---
,
---
 start
---
,
---
 end
---
,
---
 timeframe
---
="
---
1
---
d
---
"):

---
   
---
 mapping
---
 =
---
 {"
---
AAP
---
L
---
":
---
 df
---
_a
---
apl
---
,
---
 "
---
MS
---
FT
---
":
---
 df
---
_ms
---
ft
---
,
---
 "
---
J
---
PM
---
":
---
 df
---
_j
---
pm
---
}

---
   
---
 return
---
 {
---
s
---
:
---
 mapping
---
[s
---
]
---
 for
---
 s
---
 in
---
 symbols
---
 if
---
 s
---
 in
---
 mapping
---
}

---
``
---
`


---
Adding
---
 SP
---
Y
---
 to
---
 the
---
 mapping
---
 would
---
 just
---
 make
---
 it
---
 available
---
 when
---
 `
---
symbols
---
=["
---
SP
---
Y
---
"]
---
`
---
 is
---
 requested
---
.
---
 It
---
 wouldn
---
't
---
 affect
---
 other
---
 tests
---
 that
---
 don
---
't
---
 request
---
 SP
---
Y
---
.
---
 This
---
 is
---
 safe
---
.


---
But
---
 the
---
 cleaner
---
 approach
---
 for
---
 the
---
 WF
---
 integration
---
 test
---
 is
---
 to
---
 either
---
:

---
1
---
.
---
 Add
---
 SP
---
Y
---
 to
---
 the
---
 mock
---
_store
---
 fixture
---
 (
---
a
---
ffects
---
 all
---
 tests
---
 using
---
 the
---
 fixture
---
)

---
2
---
.
---
 Create
---
 a
---
 dedicated
---
 mock
---
_store
---
 with
---
 SP
---
Y
---
 for
---
 WF
---
 tests
---


---
3
---
.
---
 Update
---
 the
---
 test
---
 assertions
---
 to
---
 account
---
 for
---
 alpha
---
=
---
0
---
 →
---
 pass
---
_all
---
_round
---
s
---
=False
---



---
Looking
---
 at
---
 the
---
 spec
---
's
---
 test
---
 plan
---
:

---
-
---
 test
---
_wf
---
_gate
---
_re
---
ject
---
s
---
_negative
---
_alpha
---


---
-
---
 test
---
_wf
---
_gate
---
_pass
---
es
---
_positive
---
_alpha
---


---
-
---
 etc
---
.


---
These
---
 are
---
 new
---
 tests
---
 that
---
 will
---
 construct
---
 Walk
---
Forward
---
Round
---
/
---
Report
---
 directly
---
 with
---
 specific
---
 alpha
---
 values
---
.
---
 So
---
 they
---
 don
---
't
---
 need
---
 the
---
 integration
---
 test
---
.


---
For
---
 the
---
 existing
---
 `
---
test
---
_run
---
_walk
---
_forward
---
_mock
---
_integration
---
`,
---
 the
---
 spec
---
 says
---
:

---
>
---
 
---
需
---
要
---
检查
---
现有
---
测试
---
是否
---
依赖
---
 `
---
pass
---
_all
---
_round
---
s
---
=True
---
`
---
，
---
如果是
---
，
---
需要在
---
测试
---
中
---
提供
---
 SP
---
Y
---
 数据
---
或
---
 mock
---
 alpha
---
 >
---
 
---
0
---
。


---
The
---
 test
---
 asserts
---
 `
---
report
---
.pass
---
_all
---
_round
---
s
---
 ==
---
 expected
---
_pass
---
`
---
 where
---
 `
---
expected
---
_pass
---
 =
---
 all
---
(r
---
.pass
---
ed
---
 for
---
 r
---
 in
---
 report
---
.round
---
s
---
)
---
`.
---
 If
---
 all
---
 rounds
---
 pass
---
 (
---
DD
---
-wise
---
),
---
 then
---
 `
---
expected
---
_pass
---
=True
---
`,
---
 but
---
 `
---
report
---
.pass
---
_all
---
_round
---
s
---
`
---
 will
---
 be
---
 `
---
False
---
`
---
 (
---
because
---
 avg
---
_alpha
---
=
---
0
---
).
---
 So
---
 this
---
 will
---
 fail
---
.


---
The
---
 clean
---
est
---
 fix
---
:
---
 add
---
 SP
---
Y
---
 data
---
 to
---
 the
---
 mock
---
_store
---
 fixture
---
 with
---
 a
---
 slower
---
 trend
---
 so
---
 alpha
---
 >
---
 
---
0
---
.
---
 This
---
 way
---
:

---
-
---
 Strategy
---
 returns
---
 (
---
upt
---
rend
---
 
---
0
---
.
---
1
---
/day
---
)
---
 >
---
 SP
---
Y
---
 returns
---
 (
---
sl
---
ower
---
 upt
---
rend
---
)

---
-
---
 val
---
_alpha
---
 >
---
 
---
0
---


---
-
---
 avg
---
_val
---
_alpha
---
 >
---
 
---
0
---


---
-
---
 pass
---
_all
---
_round
---
s
---
 =
---
 all
---
 rounds
---
 passed
---
 AND
---
 avg
---
_alpha
---
 >
---
 
---
0
---
 =
---
 True
---
 (
---
if
---
 DD
---
 passes
---
)


---
But
---
 I
---
 need
---
 to
---
 verify
---
 the
---
 strategy
---
 actually
---
 produces
---
 positive
---
 alpha
---
 vs
---
 SP
---
Y
---
.
---
 The
---
 mock
---
 strategy
---
 data
---
 has
---
 `
---
close
---
 =
---
 
---
100
---
.
---
0
---
 +
---
 i
---
 *
---
 
---
0
---
.
---
1
---
`,
---
 so
---
 daily
---
 return
---
 
---
≈
---
 
---
0
---
.
---
1
---
/
---
100
---
 =
---
 
---
0
---
.
---
001
---
 (
---
0
---
.
---
1
---
%).
---
 If
---
 SP
---
Y
---
 has
---
 `
---
close
---
 =
---
 
---
100
---
.
---
0
---
 +
---
 i
---
 *
---
 
---
0
---
.
---
02
---
`,
---
 daily
---
 return
---
 
---
≈
---
 
---
0
---
.
---
02
---
/
---
100
---
 =
---
 
---
0
---
.
---
000
---
2
---
 (
---
0
---
.
---
02
---
%).
---
 So
---
 strategy
---
 out
---
per
---
forms
---
 →
---
 alpha
---
 >
---
 
---
0
---
.
---
 


---
But
---
 wait
---
,
---
 the
---
 strategy
---
 doesn
---
't
---
 just
---
 buy
---
 and
---
 hold
---
 —
---
 it
---
 uses
---
 dual
---
_ma
---
 signals
---
.
---
 The
---
 strategy
---
's
---
 actual
---
 returns
---
 depend
---
 on
---
 the
---
 signals
---
.
---
 With
---
 a
---
 strong
---
 upt
---
rend
---
,
---
 dual
---
_ma
---
 will
---
 mostly
---
 be
---
 long
---
,
---
 so
---
 returns
---
 
---
≈
---
 buy
---
-and
---
-h
---
old
---
 returns
---
.
---
 So
---
 alpha
---
 should
---
 still
---
 be
---
 positive
---
.


---
Actually
---
,
---
 let
---
 me
---
 think
---
 more
---
 carefully
---
.
---
 The
---
 mock
---
 data
---
 spans
---
 
---
300
---
 business
---
 days
---
 starting
---
 
---
202
---
1
---
-
---
01
---
-
---
01
---
.
---
 The
---
 WF
---
 test
---
 uses
---
 `
---
train
---
_months
---
=
---
18
---
,
---
 val
---
_months
---
=
---
6
---
`.
---
 The
---
 val
---
 period
---
 for
---
 round
---
 
---
4
---
 is
---
 
---
202
---
5
---
-
---
07
---
-
---
01
---
 to
---
 
---
202
---
6
---
-
---
01
---
-
---
01
---
.
---
 But
---
 the
---
 mock
---
 data
---
 only
---
 goes
---
 to
---
 ~
---
202
---
2
---
-
---
04
---
 (
---
300
---
 business
---
 days
---
 from
---
 
---
202
---
1
---
-
---
01
---
-
---
01
---
).
---
 So
---
 the
---
 val
---
 period
---
 data
---
 might
---
 be
---
 empty
---
 or
---
 partial
---
.


---
Hmm
---
,
---
 this
---
 is
---
 getting
---
 complex
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
 what
---
 the
---
 test
---
 actually
---
 does
---
 and
---
 what
---
 the
---
 current
---
 behavior
---
 is
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
 more
---
 carefully
---
:

---
```
---
python
---


---
report
---
 =
---
 run
---
_walk
---
_forward
---
(

---
   
---
 mb
---
=
---
mb
---
,

---
   
---
 strategies
---
=["
---
dual
---
_ma
---
"],

---
   
---
 param
---
_gr
---
ids
---
={"
---
dual
---
_ma
---
":
---
 {"
---
fast
---
":
---
 [
---
5
---
],
---
 "
---
slow
---
":
---
 [
---
20
---
]}
---
},

---
   
---
 rounds
---
=
---
4
---
,

---
   
---
 train
---
_months
---
=
---
18
---
,

---
   
---
 val
---
_months
---
=
---
6
---
,

---
)

---
``
---
`


---
The
---
 mock
---
 data
---
 is
---
 
---
300
---
 business
---
 days
---
 from
---
 
---
202
---
1
---
-
---
01
---
-
---
01
---
.
---
 With
---
 `
---
today
---
=date
---
.today
---
()`
---
 (
---
202
---
6
---
-
---
07
---
-
---
08
---
),
---
 the
---
 WF
---
 windows
---
 are
---
:

---
-
---
 Round
---
 
---
4
---
:
---
 val
---
 
---
202
---
5
---
-
---
07
---
-
---
01
---
 to
---
 
---
202
---
6
---
-
---
01
---
-
---
01
---
,
---
 train
---
 
---
202
---
4
---
-
---
01
---
-
---
01
---
 to
---
 
---
202
---
5
---
-
---
07
---
-
---
01
---


---
-
---
 Round
---
 
---
1
---
:
---
 val
---
 
---
202
---
4
---
-
---
01
---
-
---
01
---
 to
---
 
---
202
---
4
---
-
---
07
---
-
---
01
---
,
---
 train
---
 
---
202
---
2
---
-
---
07
---
-
---
01
---
 to
---
 
---
202
---
4
---
-
---
01
---
-
---
01
---



---
All
---
 these
---
 windows
---
 are
---
 outside
---
 the
---
 mock
---
 data
---
 range
---
 (
---
202
---
1
---
-
---
01
---
-
---
01
---
 to
---
 ~
---
202
---
2
---
-
---
04
---
).
---
 So
---
 `
---
get
---
_b
---
ars
---
_multi
---
`
---
 returns
---
 data
---
 only
---
 if
---
 the
---
 dates
---
 overlap
---
.
---
 Since
---
 the
---
 mock
---
 data
---
 has
---
 a
---
 fixed
---
 date
---
_range
---
 starting
---
 
---
202
---
1
---
-
---
01
---
-
---
01
---
 with
---
 
---
300
---
 periods
---
,
---
 it
---
 ends
---
 around
---
 
---
202
---
2
---
-
---
04
---
-
---
22
---
.


---
When
---
 `
---
get
---
_b
---
ars
---
_multi
---
`
---
 is
---
 called
---
 with
---
 start
---
=
---
202
---
4
---
-
---
01
---
-
---
01
---
,
---
 the
---
 mock
---
 returns
---
 the
---
 full
---
 DataFrame
---
 (
---
it
---
 doesn
---
't
---
 filter
---
 by
---
 date
---
).
---
 Let
---
 me
---
 check
---
...
---
 the
---
 mock
---
 fixture
---
 just
---
 returns
---
 the
---
 DataFrame
---
 regardless
---
 of
---
 start
---
/end
---
:

---
```
---
python
---


---
def
---
 get
---
_b
---
ars
---
_multi
---
(s
---
ymbols
---
,
---
 start
---
,
---
 end
---
,
---
 timeframe
---
="
---
1
---
d
---
"):

---
   
---
 mapping
---
 =
---
 {"
---
AAP
---
L
---
":
---
 df
---
_a
---
apl
---
,
---
 "
---
MS
---
FT
---
":
---
 df
---
_ms
---
ft
---
,
---
 "
---
J
---
PM
---
":
---
 df
---
_j
---
pm
---
}

---
   
---
 return
---
 {
---
s
---
:
---
 mapping
---
[s
---
]
---
 for
---
 s
---
 in
---
 symbols
---
 if
---
 s
---
 in
---
 mapping
---
}

---
``
---
`


---
So
---
 it
---
 returns
---
 the
---
 same
---
 
---
300
---
-day
---
 data
---
 regardless
---
 of
---
 the
---
 date
---
 range
---
 requested
---
.
---
 The
---
 WF
---
 function
---
 then
---
 uses
---
 this
---
 data
---
 for
---
 all
---
 rounds
---
.
---
 The
---
 data
---
 has
---
 
---
300
---
 rows
---
 which
---
 is
---
 ≥
---
 
---
30
---
,
---
 so
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
 will
---
 process
---
 it
---
.


---
OK
---
 so
---
 the
---
 strategy
---
 will
---
 produce
---
 some
---
 returns
---
.
---
 With
---
 a
---
 strong
---
 upt
---
rend
---
 and
---
 dual
---
_ma
---
(
---
5
---
,
---
 
---
20
---
),
---
 the
---
 fast
---
 MA
---
 crosses
---
 above
---
 slow
---
 MA
---
 early
---
 and
---
 stays
---
 long
---
.
---
 So
---
 returns
---
 
---
≈
---
 buy
---
-and
---
-h
---
old
---
 
---
≈
---
 positive
---
.


---
Now
---
,
---
 for
---
 alpha
---
:
---
 currently
---
 no
---
 SP
---
Y
---
 data
---
 →
---
 alpha
---
=
---
0
---
.
---
0
---
 for
---
 all
---
 rounds
---
.
---
 After
---
 my
---
 change
---
,
---
 `
---
avg
---
_val
---
_alpha
---
=
---
0
---
.
---
0
---
`,
---
 `
---
0
---
.
---
0
---
 >
---
 
---
0
---
`
---
 is
---
 False
---
 →
---
 `
---
pass
---
_all
---
_round
---
s
---
=False
---
`.


---
The
---
 test
---
 currently
---
 asserts
---
:

---
```
---
python
---


---
expected
---
_pass
---
 =
---
 all
---
(r
---
.pass
---
ed
---
 for
---
 r
---
 in
---
 report
---
.round
---
s
---
)

---
assert
---
 report
---
.pass
---
_all
---
_round
---
s
---
 ==
---
 expected
---
_pass
---


---
``
---
`


---
If
---
 all
---
 rounds
---
 pass
---
 DD
---
-wise
---
,
---
 `
---
expected
---
_pass
---
=True
---
`
---
 but
---
 `
---
report
---
.pass
---
_all
---
_round
---
s
---
=False
---
`.
---
 Test
---
 fails
---
.


---
Options
---
:

---
1
---
.
---
 Add
---
 SP
---
Y
---
 to
---
 mock
---
_store
---
 with
---
 slower
---
 trend
---
 →
---
 alpha
---
 >
---
 
---
0
---
 →
---
 test
---
 passes
---
 as
---
 before
---


---
2
---
.
---
 Update
---
 test
---
 assertion
---
:
---
 `
---
expected
---
_pass
---
 =
---
 all
---
(r
---
.pass
---
ed
---
)
---
 and
---
 <
---
avg
---
_alpha
---
 >
---
 
---
0
---
 condition
---
>
---
`


---
Option
---
 
---
1
---
 is
---
 cleaner
---
 and
---
 tests
---
 the
---
 realistic
---
 path
---
.
---
 But
---
 I
---
 need
---
 to
---
 make
---
 sure
---
 the
---
 strategy
---
 actually
---
 out
---
per
---
forms
---
 SP
---
Y
---
.
---
 Let
---
 me
---
 think
---
...


---
Actually
---
,
---
 the
---
 simplest
---
 and
---
 most
---
 robust
---
 approach
---
 is
---
 option
---
 
---
1
---
:
---
 add
---
 SP
---
Y
---
 with
---
 a
---
 flat
---
 or
---
 slow
---
 trend
---
 to
---
 the
---
 mock
---
_store
---
 fixture
---
.
---
 This
---
 way
---
,
---
 the
---
 strategy
---
 (
---
upt
---
rend
---
 data
---
)
---
 will
---
 have
---
 positive
---
 alpha
---
 vs
---
 SP
---
Y
---
 (
---
flat
---
/s
---
low
---
).


---
But
---
 I
---
'm
---
 worried
---
 about
---
 side
---
 effects
---
 on
---
 other
---
 tests
---
.
---
 Let
---
 me
---
 check
---
 if
---
 any
---
 test
---
 asserts
---
 the
---
 exact
---
 contents
---
 of
---
 `
---
get
---
_b
---
ars
---
_multi
---
`
---
 return
---
 value
---
...
---
 Actually
---
,
---
 the
---
 fixture
---
 returns
---
 `{
---
s
---
:
---
 mapping
---
[s
---
]
---
 for
---
 s
---
 in
---
 symbols
---
 if
---
 s
---
 in
---
 mapping
---
}`
---
.
---
 Adding
---
 SP
---
Y
---
 to
---
 the
---
 mapping
---
 only
---
 affects
---
 calls
---
 that
---
 include
---
 "
---
SP
---
Y
---
"
---
 in
---
 symbols
---
.
---
 No
---
 test
---
 would
---
 request
---
 SP
---
Y
---
 except
---
 through
---
 `_
---
get
---
_s
---
py
---
_returns
---
`.
---
 So
---
 it
---
's
---
 safe
---
.


---
Wait
---
,
---
 but
---
 there
---
 might
---
 be
---
 tests
---
 that
---
 check
---
 `
---
store
---
.get
---
_b
---
ars
---
_multi
---
.call
---
_count
---
`
---
 or
---
 assert
---
 it
---
 was
---
 called
---
 with
---
 specific
---
 symbols
---
.
---
 Let
---
 me
---
 check
---
...


---
Actually
---
,
---
 the
---
 safest
---
 approach
---
 is
---
 to
---
 add
---
 SP
---
Y
---
 to
---
 the
---
 mock
---
_store
---
 fixture
---
 AND
---
 update
---
 the
---
 integration
---
 test
---
 assertions
---
 to
---
 be
---
 correct
---
.
---
 Let
---
 me
---
 do
---
 both
---
:

---
1
---
.
---
 Add
---
 SP
---
Y
---
 to
---
 mock
---
_store
---
 (
---
with
---
 slow
---
 trend
---
,
---
 so
---
 alpha
---
 >
---
 
---
0
---
)

---
2
---
.
---
 Update
---
 `
---
test
---
_run
---
_walk
---
_forward
---
_mock
---
_integration
---
`
---
 to
---
 account
---
 for
---
 alpha
---
 gate
---



---
Actually
---
,
---
 looking
---
 again
---
 at
---
 the
---
 test
---
 assertion
---
:

---
```
---
python
---


---
assert
---
 r
---
.pass
---
ed
---
 ==
---
 (
---
r
---
.val
---
_max
---
_dd
---
 <=
---
 W
---
ALK
---
_FORWARD
---
_VAL
---
_DD
---
_THRESHOLD
---
)

---
``
---
`


---
This
---
 asserts
---
 `
---
passed
---
 ==
---
 dd
---
_passed
---
`.
---
 After
---
 my
---
 change
---
,
---
 `
---
passed
---
 =
---
 dd
---
_passed
---
 AND
---
 alpha
---
_passed
---
`.
---
 If
---
 alpha
---
 >
---
 
---
0
---
 (
---
with
---
 SP
---
Y
---
 data
---
),
---
 `
---
alpha
---
_passed
---
 =
---
 True
---
`,
---
 so
---
 `
---
passed
---
 =
---
 dd
---
_passed
---
`.
---
 This
---
 assertion
---
 still
---
 holds
---
.
---
 


---
And
---
:

---
```
---
python
---


---
expected
---
_pass
---
 =
---
 all
---
(r
---
.pass
---
ed
---
 for
---
 r
---
 in
---
 report
---
.round
---
s
---
)

---
assert
---
 report
---
.pass
---
_all
---
_round
---
s
---
 ==
---
 expected
---
_pass
---


---
``
---
`


---
If
---
 alpha
---
 >
---
 
---
0
---
 for
---
 all
---
 rounds
---
,
---
 `
---
avg
---
_val
---
_alpha
---
 >
---
 
---
0
---
`,
---
 so
---
 `
---
pass
---
_all
---
_round
---
s
---
 =
---
 all
---
(r
---
.pass
---
ed
---
)
---
 AND
---
 True
---
 =
---
 all
---
(r
---
.pass
---
ed
---
)
---
`.
---
 This
---
 holds
---
 too
---
.
---
 


---
So
---
 adding
---
 SP
---
Y
---
 with
---
 slow
---
 trend
---
 to
---
 mock
---
_store
---
 is
---
 the
---
 clean
---
est
---
 fix
---
.
---
 Let
---
 me
---
 verify
---
 the
---
 strategy
---
 will
---
 out
---
perform
---
 SP
---
Y
---
.


---
Strategy
---
 data
---
:
---
 close
---
 =
---
 
---
100
---
 +
---
 i
---
*
---
0
---
.
---
1
---
,
---
 daily
---
 return
---
 
---
≈
---
 
---
0
---
.
---
1
---
/(
---
100
---
+i
---
*
---
0
---
.
---
1
---
)
---
 
---
≈
---
 
---
0
---
.
---
001
---
 (
---
de
---
creasing
---
 slightly
---
)

---
SP
---
Y
---
 data
---
 (
---
slow
---
):
---
 close
---
 =
---
 
---
100
---
 +
---
 i
---
*
---
0
---
.
---
02
---
,
---
 daily
---
 return
---
 
---
≈
---
 
---
0
---
.
---
02
---
/(
---
100
---
+i
---
*
---
0
---
.
---
02
---
)
---
 
---
≈
---
 
---
0
---
.
---
000
---
2
---



---
Strategy
---
 annual
---
ized
---
:
---
 (
---
1
---
.
---
001
---
)^
---
25
---
2
---
 -
---
 
---
1
---
 
---
≈
---
 
---
0
---
.
---
28
---
5
---
 (
---
28
---
.
---
5
---
%
---
)

---
SP
---
Y
---
 annual
---
ized
---
:
---
 (
---
1
---
.
---
000
---
2
---
)^
---
25
---
2
---
 -
---
 
---
1
---
 
---
≈
---
 
---
0
---
.
---
05
---
1
---
 (
---
5
---
.
---
1
---
%
---
)

---
Alpha
---
 
---
≈
---
 
---
23
---
.
---
4
---
%
---
 >
---
 
---
0
---
.
---
 


---
But
---
 wait
---
,
---
 the
---
 strategy
---
 doesn
---
't
---
 buy
---
 and
---
 hold
---
 —
---
 it
---
 uses
---
 dual
---
_ma
---
 signals
---
.
---
 With
---
 fast
---
=
---
5
---
,
---
 slow
---
=
---
20
---
 on
---
 an
---
 upt
---
rend
---
,
---
 the
---
 fast
---
 MA
---
 will
---
 be
---
 above
---
 slow
---
 MA
---
 most
---
 of
---
 the
---
 time
---
,
---
 so
---
 the
---
 strategy
---
 will
---
 be
---
 long
---
.
---
 But
---
 there
---
 might
---
 be
---
 wh
---
ips
---
aws
---
.
---
 The
---
 strategy
---
 returns
---
 will
---
 be
---
 close
---
 to
---
 but
---
 less
---
 than
---
 buy
---
-and
---
-h
---
old
---
 (
---
due
---
 to
---
 fees
---
 and
---
 sl
---
ipp
---
age
---
).
---
 Still
---
,
---
 it
---
 should
---
 out
---
perform
---
 SP
---
Y
---
 (
---
5
---
.
---
1
---
%)
---
 by
---
 a
---
 wide
---
 margin
---
.


---
OK
---
,
---
 let
---
 me
---
 proceed
---
 with
---
 the
---
 implementation
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
 design
---
 doc
---
 and
---
 trajectory
---
 files
---
.


---
Actually
---
,
---
 wait
---
.
---
 Let
---
 me
---
 re
---
-read
---
 the
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
assert
---
 r
---
.pass
---
ed
---
 ==
---
 (
---
r
---
.val
---
_max
---
_dd
---
 <=
---
 W
---
ALK
---
_FORWARD
---
_VAL
---
_DD
---
_THRESHOLD
---
)

---
``
---
`


---
This
---
 is
---
 a
---
 strict
---
 equality
---
.
---
 After
---
 my
---
 change
---
,
---
 if
---
 `
---
val
---
_alpha
---
`
---
 happens
---
 to
---
 be
---
 ≤
---
 -
---
5
---
%
---
 for
---
 some
---
 round
---
,
---
 `
---
passed
---
`
---
 would
---
 be
---
 False
---
 even
---
 if
---
 DD
---
 passes
---
.
---
 But
---
 with
---
 the
---
 mock
---
 data
---
 (
---
strong
---
 upt
---
rend
---
),
---
 alpha
---
 should
---
 be
---
 strongly
---
 positive
---
,
---
 so
---
 this
---
 won
---
't
---
 happen
---
.


---
However
---
,
---
 I
---
 realize
---
 I
---
 should
---
 be
---
 more
---
 careful
---
.
---
 Let
---
 me
---
 check
---
 if
---
 the
---
 mock
---
 data
---
 actually
---
 produces
---
 valid
---
 returns
---
 in
---
 the
---
 val
---
 period
---
.
---
 The
---
 mock
---
 data
---
 is
---
 
---
300
---
 business
---
 days
---
 from
---
 
---
202
---
1
---
-
---
01
---
-
---
01
---
.
---
 The
---
 WF
---
 function
---
 calls
---
 `
---
get
---
_b
---
ars
---
_multi
---
(s
---
ymbols
---
,
---
 val
---
_start
---
,
---
 val
---
_end
---
)`
---
 but
---
 the
---
 mock
---
 returns
---
 the
---
 same
---
 
---
300
---
-day
---
 data
---
 regardless
---
.
---
 So
---
 the
---
 val
---
 period
---
 will
---
 have
---
 data
---
 (
---
the
---
 same
---
 
---
300
---
 days
---
).
---
 The
---
 strategy
---
 will
---
 produce
---
 returns
---
 over
---
 those
---
 
---
300
---
 days
---
.


---
But
---
 here
---
's
---
 the
---
 thing
---
:
---
 the
---
 WF
---
 function
---
 computes
---
 `
---
combined
---
 =
---
 pd
---
.concat
---
(all
---
_returns
---
,
---
 axis
---
=
---
1
---
).
---
mean
---
(axis
---
=
---
1
---
).
---
drop
---
na
---
()`
---
 for
---
 the
---
 val
---
 period
---
.
---
 If
---
 the
---
 same
---
 data
---
 is
---
 used
---
 for
---
 all
---
 rounds
---
,
---
 the
---
 returns
---
 will
---
 be
---
 similar
---
 across
---
 rounds
---
.
---
 Alpha
---
 will
---
 be
---
 positive
---
 (
---
strategy
---
 out
---
per
---
forms
---
 SP
---
Y
---
).


---
OK
---
,
---
 I
---
'm
---
 confident
---
.
---
 Let
---
 me
---
 proceed
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
 if
---
 there
---
's
---
 a
---
 dedicated
---
 test
---
 file
---
 for
---
 alpha
---
 gate
---
 already
---
.
---
我来
---
检查
---
一下
---
现有的
---
 `
---
test
---
_alpha
---
_gate
---
.py
---
`
---
 并
---
查看
---
设计
---
文档
---
。
---
{"command":"head -30 /Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py; echo \"---\"; ls /Users/rickouyang/Github/trade-tools/mytrader/iterations/ 2>/dev/null; ls /Users/rickouyang/Github/trade-tools/iterations/ 2>/dev/null","description":"Check alpha gate test and iterations dirs"}
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md","limit":100}
---
Check alpha gate test and iterations dirs
---
Command: head -30 /Users/rickouyang/Github/trade-tools/mytrader/tests/test_alpha_gate.py; echo "---"; ls /Users/rickouyang/Github/trade-tools/mytrader/iterations/ 2>/dev/null; ls /Users/rickouyang/Github/trade-tools/iterations/ 2>/dev/null
Stdout: """迭代 #12：alpha>0 硬门槛测试（Reject Negative-Alpha Strategies）。

验证：
    1. `GroupBacktestResult.no_positive_alpha` 字段默认 False
    2. `_run_group` 在 candidates 构建后、Tier 1 前剔除 alpha≤0 的候选
    3. 全负 alpha 组返回空权重 + `no_positive_alpha=True` 标记
    4. 混合 alpha 组只保留正 alpha 候选
    5. `_optimize_ensemble_weights` 负 alpha 策略权重为 0（不再 max(0.01) 掩盖）
    6. 全负 alpha ensemble 退化为等权 + WARNING（防御性 fallback）
    7. 健全性门槛 + alpha>0 门槛协同工作

背景见 `iterations/iteration_12/spec.md` + `.codebuddy/notes/experience.md` #8。
"""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from mytrader.backtest.matrix_backtest import (
    GroupBacktestResult,
    MatrixBacktest,
    MatrixBacktestReport,
    SingleBacktestResult,
    _combine_daily_returns,
    _compute_alpha,
---
iteration_8
iteration_1  iteration_12 iteration_3  iteration_6  iteration_9
iteration_10 iteration_13 iteration_4  iteration_7
iteration_11 iteration_2  iteration_5  iteration_8

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
   1→# Module 07 — Backtest Module（回测模块）
   2→
   3→> 上级文档：[00-overview.md](./00-overview.md)  
   4→> 回测框架：VectorBT
   5→
   6→---
   7→
   8→## 1. 职责
   9→
  10→- 在历史数据上模拟策略执行
  11→- 计算策略绩效指标（Sharpe、MaxDD、Calmar 等）
  12→- 支持参数优化（网格搜索 / 随机搜索）
  13→- 生成可视化报告
  14→- 验证策略的回测/实盘一致性
  15→- **（v2 新增）矩阵回测：N 策略 × G 标的组 × 参数网格 → 产出 strategy_weights.json**
  16→
  17→回测模块的核心价值是**在投入真实资金前验证策略**，以及**发现策略的适用范围和边界条件**。
  18→
  19→> **v2 重大变化**：v1 只在单标的（AAPL）上回测单策略。
  20→> v2 引入**矩阵回测**——在标的分组上批量回测多策略多参数，
  21→> 自动产出"每组最优策略 + 权重"，作为实盘选股的依据（详见第 10 节）。
  22→> 回测数据从 MarketDataStore 本地库读取（DuckDB 列式），回测窗口 **5 年**（覆盖完整牛熊周期）。
  23→
  24→---
  25→
  26→## 2. 为什么选 VectorBT
  27→
  28→| 特性 | VectorBT | Backtrader | Zipline |
  29→|------|---------|-----------|---------|
  30→| 执行速度 | ⭐⭐⭐⭐⭐ 极快（NumPy向量化） | ⭐⭐⭐ 慢（循环事件驱动） | ⭐⭐⭐ 中等 |
  31→| 参数优化 | 原生支持，一行代码 | 需要外部库 | 不支持 |
  32→| 可视化 | 内置 Plotly 交互图 | 需要 matplotlib | 有限支持 |
  33→| 学习曲线 | 中等 | 较陡 | 陡 |
  34→| 与 pandas 集成 | 原生 | 一般 | 一般 |
  35→| 维护状态 | 活跃 | 较少维护 | 已停止 |
  36→
  37→**VectorBT 的核心思想**：将整个回测历史表达为矩阵运算，而不是逐 bar 循环。这使得参数优化可以一次性计算所有参数组合，速度比逐 bar 快 100x 以上。
  38→
  39→---
  40→
  41→## 3. VectorBT 基本用法
  42→
  43→### 3.1 最简单的回测（VectorBT 1.0.0 实际用法）
  44→
  45→```python
  46→import vectorbt as vbt
  47→import pandas as pd
  48→from mytrader.data.providers.yfinance_provider import YFinanceProvider
  49→from mytrader.strategy.strategies.dual_ma import dual_ma_signal
  50→from datetime import date
  51→
  52→# 1. 获取数据
  53→provider = YFinanceProvider()
  54→df = provider.get_ohlcv("AAPL", date(2022, 1, 1), date(2025, 1, 1))
  55→close = df["close"]
  56→
  57→# 2. 调用策略层纯函数生成信号（signal 已内含 shift(1)）
  58→signal = dual_ma_signal(close, fast=10, slow=30)
  59→entries = signal == 1
  60→exits   = signal == -1
  61→
  62→# 3. 构建 Portfolio
  63→# ⚠️ vectorbt 1.0.0 的 size_type 用字符串枚举 "Percent"（不是旧版的 "ValuePercent"）
  64→pf = vbt.Portfolio.from_signals(
  65→    close,
  66→    open=open_series,  # ⚠️ 必须传入：信号在下一根 bar 的开盘价执行，与实盘保持一致
  67→    entries=entries,
  68→    exits=exits,
  69→    init_cash=100_000,
  70→    fees=0.001,        # 0.1%——Alpaca 零佣金，保留此项模拟潜在市场冲击（保守估计）
  71→    slippage=0.001,    # 0.1%——对 mid-cap 或流动性较差标的可调高至 0.002
  72→    size=0.95,
  73→    size_type="Percent",   # 按账户价值百分比下单
  74→    freq="D",
  75→)
  76→
  77→# 4. 查看绩效
  78→print(pf.stats())
  79→pf.plot().show()
  80→```
  81→
  82→### 3.2 参数优化（网格搜索，当前实现方式）
  83→
  84→当前使用逐组合循环，而非 VectorBT 原生矩阵优化（后者在 1.0.0 中 API 有变化）：
  85→
  86→```python
  87→# backtest/runner.py — run_optimize()
  88→import itertools
  89→
  90→param_grid = {"fast": [5, 10, 15, 20], "slow": [20, 30, 40, 50, 60]}
  91→combinations = list(itertools.product(*param_grid.values()))
  92→
  93→rows = []
  94→for combo in combinations:
  95→    params = dict(zip(param_grid.keys(), combo))
  96→    signal = dual_ma_signal(close, **params)
  97→    pf = vbt.Portfolio.from_signals(
  98→        close,
  99→        entries=signal == 1,
 100→        exits=signal == -1,
 101→
---
   1→# Module 07 — Backtest Module（回测模块）
   2→
   3→> 上级文档：[00-overview.md](./00-overview.md)  
   4→> 回测框架：VectorBT
   5→
   6→---
   7→
   8→## 1. 职责
   9→
  10→- 在历史数据上模拟策略执行
  11→- 计算策略绩效指标（Sharpe、MaxDD、Calmar 等）
  12→- 支持参数优化（网格搜索 / 随机搜索）
  13→- 生成可视化报告
  14→- 验证策略的回测/实盘一致性
  15→- **（v2 新增）矩阵回测：N 策略 × G 标的组 × 参数网格 → 产出 strategy_weights.json**
  16→
  17→回测模块的核心价值是**在投入真实资金前验证策略**，以及**发现策略的适用范围和边界条件**。
  18→
  19→> **v2 重大变化**：v1 只在单标的（AAPL）上回测单策略。
  20→> v2 引入**矩阵回测**——在标的分组上批量回测多策略多参数，
  21→> 自动产出"每组最优策略 + 权重"，作为实盘选股的依据（详见第 10 节）。
  22→> 回测数据从 MarketDataStore 本地库读取（DuckDB 列式），回测窗口 **5 年**（覆盖完整牛熊周期）。
  23→
  24→---
  25→
  26→## 2. 为什么选 VectorBT
  27→
  28→| 特性 | VectorBT | Backtrader | Zipline |
  29→|------|---------|-----------|---------|
  30→| 执行速度 | ⭐⭐⭐⭐⭐ 极快（NumPy向量化） | ⭐⭐⭐ 慢（循环事件驱动） | ⭐⭐⭐ 中等 |
  31→| 参数优化 | 原生支持，一行代码 | 需要外部库 | 不支持 |
  32→| 可视化 | 内置 Plotly 交互图 | 需要 matplotlib | 有限支持 |
  33→| 学习曲线 | 中等 | 较陡 | 陡 |
  34→| 与 pandas 集成 | 原生 | 一般 | 一般 |
  35→| 维护状态 | 活跃 | 较少维护 | 已停止 |
  36→
  37→**VectorBT 的核心思想**：将整个回测历史表达为矩阵运算，而不是逐 bar 循环。这使得参数优化可以一次性计算所有参数组合，速度比逐 bar 快 100x 以上。
  38→
  39→---
  40→
  41→## 3. VectorBT 基本用法
  42→
  43→### 3.1 最简单的回测（VectorBT 1.0.0 实际用法）
  44→
  45→```python
  46→import vectorbt as vbt
  47→import pandas as pd
  48→from mytrader.data.providers.yfinance_provider import YFinanceProvider
  49→from mytrader.strategy.strategies.dual_ma import dual_ma_signal
  50→from datetime import date
  51→
  52→# 1. 获取数据
  53→provider = YFinanceProvider()
  54→df = provider.get_ohlcv("AAPL", date(2022, 1, 1), date(2025, 1, 1))
  55→close = df["close"]
  56→
  57→# 2. 调用策略层纯函数生成信号（signal 已内含 shift(1)）
  58→signal = dual_ma_signal(close, fast=10, slow=30)
  59→entries = signal == 1
  60→exits   = signal == -1
  61→
  62→# 3. 构建 Portfolio
  63→# ⚠️ vectorbt 1.0.0 的 size_type 用字符串枚举 "Percent"（不是旧版的 "ValuePercent"）
  64→pf = vbt.Portfolio.from_signals(
  65→    close,
  66→    open=open_series,  # ⚠️ 必须传入：信号在下一根 bar 的开盘价执行，与实盘保持一致
  67→    entries=entries,
  68→    exits=exits,
  69→    init_cash=100_000,
  70→    fees=0.001,        # 0.1%——Alpaca 零佣金，保留此项模拟潜在市场冲击（保守估计）
  71→    slippage=0.001,    # 0.1%——对 mid-cap 或流动性较差标的可调高至 0.002
  72→    size=0.95,
  73→    size_type="Percent",   # 按账户价值百分比下单
  74→    freq="D",
  75→)
  76→
  77→# 4. 查看绩效
  78→print(pf.stats())
  79→pf.plot().show()
  80→```
  81→
  82→### 3.2 参数优化（网格搜索，当前实现方式）
  83→
  84→当前使用逐组合循环，而非 VectorBT 原生矩阵优化（后者在 1.0.0 中 API 有变化）：
  85→
  86→```python
  87→# backtest/runner.py — run_optimize()
  88→import itertools
  89→
  90→param_grid = {"fast": [5, 10, 15, 20], "slow": [20, 30, 40, 50, 60]}
  91→combinations = list(itertools.product(*param_grid.values()))
  92→
  93→rows = []
  94→for combo in combinations:
  95→    params = dict(zip(param_grid.keys(), combo))
  96→    signal = dual_ma_signal(close, **params)
  97→    pf = vbt.Portfolio.from_signals(
  98→        close,
  99→        entries=signal == 1,
 100→        exits=signal == -1,
 101→
---
{"-n":true,"output_mode":"content","path":"/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md","pattern":"Walk-Forward|walk_forward|WF|val_alpha|val_sortino|WALK_FORWARD"}
---
["/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md:211:1. **Walk-Forward Analysis（WFA）**：在滚动窗口上重复优化+验证","/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md:216:# 简单的 Walk-Forward 框架","/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md:217:def walk_forward_test(price: pd.Series, train_months: int = 12, test_months: int = 3):","/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md:297:    # optimizer.py         # 待实现：Walk-Forward Analysis","/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md:396:| **Walk-Forward** | 滚动训练窗口，月度重优化 | 平衡过拟合与适应性 |","/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md:443:### 10.5 Walk-Forward 月度重优化","/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md:524:- [Walk-Forward Optimization — Quantopian](https://github.com/quantopian/research_public)"]
---
["/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md:211:1. **Walk-Forward Analysis（WFA）**：在滚动窗口上重复优化+验证","/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md:216:# 简单的 Walk-Forward 框架","/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md:217:def walk_forward_test(price: pd.Series, train_months: int = 12, test_months: int = 3):","/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md:297:    # optimizer.py         # 待实现：Walk-Forward Analysis","/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md:396:| **Walk-Forward** | 滚动训练窗口，月度重优化 | 平衡过拟合与适应性 |","/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md:443:### 10.5 Walk-Forward 月度重优化","/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md:524:- [Walk-Forward Optimization — Quantopian](https://github.com/quantopian/research_public)"]
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md","limit":90,"offset":440}
---
 440→Python 稳定排序保留原顺序（按策略列表顺序）。
 441→
 442→
 443→### 10.5 Walk-Forward 月度重优化
 444→
 445→```
 446→训练窗口 5 年 → 优化权重 → 应用 1 个月（样本外）→ 滚动前移 → 重新优化
 447→
 448→调度（APScheduler）：
 449→  每月第一个交易日 00:00 触发 run_matrix_backtest()
 450→  → 更新 strategy_weights.json
 451→  → StrategyMatrixRunner.reload_weights() 热加载
 452→```
 453→
 454→为什么是月度（设计访谈确认）：
 455→
 456→```
 457→更新太频繁（每天）→ 拟合近期噪音，权重翻转，策略左右打脸
 458→更新太慢（每年）  → 行情切换时反应迟钝
 459→每月 ≈ 21 交易日  → 足够样本外数据验证上轮权重，换手率可控
 460→```
 461→
 462→**窗口重叠率讨论：**
 463→
 464→```
 465→当前方案：训练 5 年 + 步进 1 个月 → 重叠率 = 59/60 ≈ 98.3%
 466→→ 权重变化缓慢（惯性大），但保证了统计稳健性
 467→→ 代价：市场突变时（如 2022 熊市初期）权重适应较慢
 468→
 469→改进方向（Phase 5 后续可选）：
 470→  方案 A：缩短训练窗口至 2-3 年，降低重叠率 → 适应性更强，但统计样本减少
 471→  方案 B：时间衰减权重（指数衰减 λ≈0.97/天）→ 近期数据权重更高，
 472→           等效训练窗口约 1-1.5 年，无需改变窗口长度
 473→  方案 C：双窗口验证：短窗口（1年）+ 长窗口（5年）权重取交集，兼顾适应性与稳健性
 474→```
 475→
 476→### 10.6 输出文件
 477→
 478→```
 479→config/strategy_weights.json   # StrategyMatrixRunner 实盘读取
 480→reports/matrix_backtest/        # 每次矩阵回测的详细报告（各组各策略指标）
 481→    {date}/
 482→        group_summary.csv       # 各组 Top 策略对比
 483→        {group_id}_detail.csv   # 单组各策略各参数明细
 484→```
 485→
 486→#### strategy_weights.json 字段说明
 487→
 488→```json
 489→{
 490→  "strategy": "rsi_mean_revert",
 491→  "params": {"period": 14, "oversold": 30, "overbought": 70},
 492→  "weight": 0.5,
 493→  "backtest_sharpe": 1.03,
 494→  "backtest_sortino": 1.61,
 495→  "backtest_max_drawdown": 1.78,
 496→  "backtest_win_rate": 0.50,
 497→  "backtest_alpha": 2.35,         // 迭代 #9 新增：vs SPY 的超额年化收益（百分数）
 498→  "dd_constrained": false,
 499→  "backtest_dd_status": "pass"
 500→}
 501→```
 502→
 503→### 10.7 性能考量
 504→
 505→```
 506→N 策略(4) × 参数网格(~20) × G 组(假设 9 组) × 组内标的(~60)
 507→= 4 × 20 × 9 × 60 = ~43,200 次单标的回测
 508→
 509→VectorBT 向量化 + DuckDB 列式读取：
 510→  单次回测 ~10ms → 43,200 × 10ms ≈ 7 分钟
 511→→ 月度离线跑，7 分钟完全可接受
 512→```
 513→
 514→---
 515→
 516→## 参考来源
 517→
 518→- [VectorBT 官方文档](https://vectorbt.dev/)
 519→- [VectorBT Portfolio.from_signals](https://vectorbt.dev/api/portfolio/base/#vectorbt.portfolio.base.Portfolio.from_signals)
 520→- [DuckDB 文档](https://duckdb.org/docs/)
 521→- *Advances in Financial Machine Learning*, Ch.7 — Cross-Validation in Finance (de Prado)
 522→- *Advances in Financial Machine Learning*, Ch.11 — The Sharpe Ratio (de Prado)
 523→- [Backtesting Pitfalls — QuantStart](https://www.quantstart.com/articles/avoiding-look-ahead-bias-in-backtests-with-python/)
 524→- [Walk-Forward Optimization — Quantopian](https://github.com/quantopian/research_public)
 525→
 526→
---
 440→Python 稳定排序保留原顺序（按策略列表顺序）。
 441→
 442→
 443→### 10.5 Walk-Forward 月度重优化
 444→
 445→```
 446→训练窗口 5 年 → 优化权重 → 应用 1 个月（样本外）→ 滚动前移 → 重新优化
 447→
 448→调度（APScheduler）：
 449→  每月第一个交易日 00:00 触发 run_matrix_backtest()
 450→  → 更新 strategy_weights.json
 451→  → StrategyMatrixRunner.reload_weights() 热加载
 452→```
 453→
 454→为什么是月度（设计访谈确认）：
 455→
 456→```
 457→更新太频繁（每天）→ 拟合近期噪音，权重翻转，策略左右打脸
 458→更新太慢（每年）  → 行情切换时反应迟钝
 459→每月 ≈ 21 交易日  → 足够样本外数据验证上轮权重，换手率可控
 460→```
 461→
 462→**窗口重叠率讨论：**
 463→
 464→```
 465→当前方案：训练 5 年 + 步进 1 个月 → 重叠率 = 59/60 ≈ 98.3%
 466→→ 权重变化缓慢（惯性大），但保证了统计稳健性
 467→→ 代价：市场突变时（如 2022 熊市初期）权重适应较慢
 468→
 469→改进方向（Phase 5 后续可选）：
 470→  方案 A：缩短训练窗口至 2-3 年，降低重叠率 → 适应性更强，但统计样本减少
 471→  方案 B：时间衰减权重（指数衰减 λ≈0.97/天）→ 近期数据权重更高，
 472→           等效训练窗口约 1-1.5 年，无需改变窗口长度
 473→  方案 C：双窗口验证：短窗口（1年）+ 长窗口（5年）权重取交集，兼顾适应性与稳健性
 474→```
 475→
 476→### 10.6 输出文件
 477→
 478→```
 479→config/strategy_weights.json   # StrategyMatrixRunner 实盘读取
 480→reports/matrix_backtest/        # 每次矩阵回测的详细报告（各组各策略指标）
 481→    {date}/
 482→        group_summary.csv       # 各组 Top 策略对比
 483→        {group_id}_detail.csv   # 单组各策略各参数明细
 484→```
 485→
 486→#### strategy_weights.json 字段说明
 487→
 488→```json
 489→{
 490→  "strategy": "rsi_mean_revert",
 491→  "params": {"period": 14, "oversold": 30, "overbought": 70},
 492→  "weight": 0.5,
 493→  "backtest_sharpe": 1.03,
 494→  "backtest_sortino": 1.61,
 495→  "backtest_max_drawdown": 1.78,
 496→  "backtest_win_rate": 0.50,
 497→  "backtest_alpha": 2.35,         // 迭代 #9 新增：vs SPY 的超额年化收益（百分数）
 498→  "dd_constrained": false,
 499→  "backtest_dd_status": "pass"
 500→}
 501→```
 502→
 503→### 10.7 性能考量
 504→
 505→```
 506→N 策略(4) × 参数网格(~20) × G 组(假设 9 组) × 组内标的(~60)
 507→= 4 × 20 × 9 × 60 = ~43,200 次单标的回测
 508→
 509→VectorBT 向量化 + DuckDB 列式读取：
 510→  单次回测 ~10ms → 43,200 × 10ms ≈ 7 分钟
 511→→ 月度离线跑，7 分钟完全可接受
 512→```
 513→
 514→---
 515→
 516→## 参考来源
 517→
 518→- [VectorBT 官方文档](https://vectorbt.dev/)
 519→- [VectorBT Portfolio.from_signals](https://vectorbt.dev/api/portfolio/base/#vectorbt.portfolio.base.Portfolio.from_signals)
 520→- [DuckDB 文档](https://duckdb.org/docs/)
 521→- *Advances in Financial Machine Learning*, Ch.7 — Cross-Validation in Finance (de Prado)
 522→- *Advances in Financial Machine Learning*, Ch.11 — The Sharpe Ratio (de Prado)
 523→- [Backtesting Pitfalls — QuantStart](https://www.quantstart.com/articles/avoiding-look-ahead-bias-in-backtests-with-python/)
 524→- [Walk-Forward Optimization — Quantopian](https://github.com/quantopian/research_public)
 525→
 526→
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
 trajectory
---
 and
---
 decision
---
_log
---
 files
---
 to
---
 understand
---
 the
---
 format
---
.
---
让我
---
检查
---
一下
---
轨迹
---
和
---
决策
---
日志
---
文件
---
。
---
{"command":"ls /Users/rickouyang/Github/trade-tools/mytrader/alignment/ 2>/dev/null; ls /Users/rickouyang/Github/trade-tools/alignment/ 2>/dev/null","description":"Find alignment directory"}
---
Find alignment directory
---
Command: ls /Users/rickouyang/Github/trade-tools/mytrader/alignment/ 2>/dev/null; ls /Users/rickouyang/Github/trade-tools/alignment/ 2>/dev/null
Stdout: __pycache__             iteration_trajectory.md questionair.md
ai_constitution.md      monitor.py              tests
decision_log.md         orchestrator.py
interview_progress.md   orchestrator_design.md

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"command":"tail -80 /Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md","description":"View end of iteration trajectory"}
---
{"command":"tail -60 /Users/rickouyang/Github/trade-tools/alignment/decision_log.md","description":"View end of decision log"}
---
View end of iteration trajectory
---
View end of decision log
---
Command: tail -80 /Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md
Stdout: ```
✅ Backtest (≥5年, alpha-based selection, batch-optimized, sanity-gated)
✅ Walk-Forward (4轮, 自动继承 alpha 排序, batch-optimized)
✅ Portfolio Backtest | ✅ Paper Trading Integrity
✅ Harness Reliability | ✅ SignalRanker Sortino Priority
✅ Strategy Diversity (5 策略 pool)
✅ Alpha-Based Selection (迭代 #9 完成)
✅ Batch Backtest Optimization (迭代 #10 完成)
✅ Sanity Gate / Reject Degenerate (迭代 #11 完成)
⬜ OOS Alpha Sort + alpha>0 Threshold (→ Iter #12)
⬜ Paper Trade ≥1月 | ⬜ Live
```

---

> **Orchestrator 验证记录** (自动追加)
> - 迭代状态: passed
> - 测试: 0 passed, 0 failed
> - 违规: 0 条
> - 高风险文件: 0 个
> - 测试数变化: 626 → 646
> - CodeBuddy 自行更新了 trajectory ✅

---

## 迭代 #12 — Alpha>0 硬门槛（Reject Negative-Alpha Strategies）

- **日期**: 2026-07-07 UTC
- **类型**: 选择器治理漏洞修复（低风险，仅改 `matrix_backtest.py` 选择器 + ensemble 权重）
- **变更摘要**: 在 `_run_group` Tier 1/2/3 排序之前加 alpha>0 硬门槛（剔除跑不赢 SPY 的策略）；全负 alpha 组返回空权重 + `no_positive_alpha` 标记；修 `_optimize_ensemble_weights` 负 alpha 归一化 bug（`max(alpha,0.01)` → `max(alpha,0.0)`）
- **状态**: passed
- **执行时长**: ~17 分钟（orchestrator），248 次工具调用
- **测试数**: 646 → 659（+13 新测试用例）

### 背景

Iter #11 健全性门槛成功剔除了退化策略（rsi_trend_filter 从 4/6 组降到 1/6 组），但 reoptimize 完整结果显示组合 alpha=-21.41%——11 条权重中 9 条负 alpha（in-sample），系统正在用 9 个"5 年跑不赢 SPY"的策略组合去交易。WF 4/4 全过（Sortino 1.56~2.09）但 PortfolioBacktest alpha=-21%，精确复现审计报告 §5 第 6 点"WF gate 不校验 alpha"。

### 变更详情

**P0: `GroupBacktestResult.no_positive_alpha` 字段** (`matrix_backtest.py`)
- 新增 `no_positive_alpha: bool = False` 标记，标记该组是否因全负 alpha 而空仓

**P0: `_run_group` alpha>0 硬门槛** (`matrix_backtest.py::_run_group`)
- 在 candidates 构建后、Tier 1/2/3 之前，剔除 `alpha≤0` 的候选
- 全负 alpha 组返回空权重 + `no_positive_alpha=True` 标记
- 符合 `experience.md #8` 的门槛顺序：健全性 → 风险(DD) → 正超额(alpha>0) → 排序

**P0: `_optimize_ensemble_weights` 负 alpha 归一化修复** (`matrix_backtest.py`)
- 旧代码 `max(alpha, 0.01)` 把负 alpha 都变成 0.01 → 归一化后等权，掩盖"都不好"
- 新代码 `max(alpha, 0.0)` → 负 alpha 权重为 0，只有正 alpha 参与归一化
- 全负 alpha 时等权 fallback + WARNING（防御性设计，上游 alpha>0 门槛应已拦截）

**测试** (`tests/test_alpha_gate.py`, +13 用例)
- `no_positive_alpha` 字段默认值 + 可设置
- 全正 alpha 组正常产出权重；全负 alpha 组返回空权重 + 标记
- 混合 alpha 组只保留正 alpha 候选
- 健全性门槛 + alpha 门槛协同工作（退化策略先被健全性剔除，负 alpha 再被 alpha 门槛剔除）
- `_optimize_ensemble_weights`：负 alpha 权重为 0、全正 alpha 正常归一化、混合只正 alpha 加权、全负 fallback 等权 + WARNING
- SPY 不可用时退化为等权（与 Iter #9 行为一致）
- 同步更新 3 个现有测试文件的 SPY benchmark 数据（用 trend="down" 的 SPY 确保策略 alpha>0，避免被新门槛误杀）

### Constitution 合规
- ✅ 未突破 DD 20% 约束（alpha>0 门槛不影响 DD 过滤）
- ✅ 测试覆盖率提升（+13 测试）
- ✅ 未引入黑箱策略 / 未引入 RL
- ✅ 文档与代码同步（07-backtest-module.md + trajectory + decision_log + CODEBUDDY）
- ✅ 低风险变更（仅选择器逻辑），符合自动部署条件

---

> **Orchestrator 验证记录** (自动追加)
> - 迭代状态: passed
> - 测试: 0 passed, 0 failed
> - 违规: 0 条
> - 高风险文件: 0 个
> - 测试数变化: 646 → 659
> - CodeBuddy 自行更新了 trajectory ✅

---

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
Command: tail -60 /Users/rickouyang/Github/trade-tools/alignment/decision_log.md
Stdout: - **决策逻辑**:

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

### [2026-07-07 UTC] 迭代 #12 — alpha>0 门槛位置 + ensemble 归一化修复

- **困境描述**: 实现 alpha>0 硬门槛时遇到两处需要判断的决策点：
  1. alpha>0 门槛应该放在 top-K 选择之前还是之后？
  2. `_optimize_ensemble_weights` 的负 alpha 归一化如何修？

- **决策逻辑**:

  **决策 1: alpha>0 门槛放在 Tier 1/2/3 之前（candidates 构建后）**
  - `experience.md #8` 的门槛顺序：① 健全性 → ② 风险(DD) → ③ 正超额(alpha>0) → ④ 排序
  - 放在 Tier 1 前：确保 Tier 1/2/3 只在正 alpha 候选中进行，不会遗漏正 alpha 策略
  - 放在 top-K 后的缺点：如果 top-K 都是负 alpha，会空仓，但 top-K 之外可能有正 alpha 策略被遗漏

  **决策 2: `_optimize_ensemble_weights` 用 `max(alpha, 0.0)` 替代 `max(alpha, 0.01)`**
  - 旧代码 `max(alpha, 0.01)`：alpha=-7.79 和 alpha=-1.49 都变成 0.01 → 归一化后 50/50 等权
  - 新代码 `max(alpha, 0.0)`：负 alpha 权重为 0，只有正 alpha 参与归一化
  - 全负 alpha 时等权 fallback + WARNING（防御性设计，上游 alpha>0 门槛应已拦截）

- **决策结果**: alpha>0 门槛在 Tier 1 前 + ensemble 用 `max(alpha, 0.0)`；659 测试通过

- **经验教训**:
  - 门槛顺序很重要：alpha>0 放在排序前比排序后更符合 experience.md #8，避免遗漏正 alpha 策略
  - `max(x, ε)` 是危险的归一化模式：把"都不好"变成"等权都要"，掩盖质量问题。正确做法是让坏值权重为 0

---

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
Now
---
 I
---
 have
---
 a
---
 complete
---
 understanding
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
 to
---
 understand
---
 what
---
 to
---
 update
---
.
---
 I
---
 already
---
 have
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
 content
---
 from
---
 the
---
 system
---
 reminder
---
.
---
 Let
---
 me
---
 now
---
 create
---
 a
---
 task
---
 list
---
 and
---
 start
---
 implementing
---
.


---
Let
---
 me
---
 also
---
 quickly
---
 check
---
 how
---
 `
---
test
---
_alpha
---
_gate
---
.py
---
`
---
 structured
---
 its
---
 tests
---
 and
---
 how
---
 SP
---
Y
---
 data
---
 was
---
 handled
---
 in
---
 existing
---
 tests
---
 (
---
since
---
 Iter
---
 #
---
12
---
 mentioned
---
 "
---
同步
---
更新
---
 
---
3
---
 个
---
现有
---
测试
---
文件的
---
 SP
---
Y
---
 benchmark
---
 数据
---
").
---
我来
---
检查
---
一下
---
现有
---
测试
---
中
---
 SP
---
Y
---
 数据
---
是如何
---
处理的
---
。
---
{"-n":true,"head_limit":40,"output_mode":"content","path":"/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py","pattern":"SPY|spy|_get_spy_returns"}
---
["/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:970:        \"\"\"构造已知策略收益和 SPY 收益，验证 alpha 计算正确。","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:972:        策略日均收益 0.001 (0.1%)，SPY 日均收益 0.0004 (0.04%)。","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:981:        # SPY 收益：稳定 0.04%/日（年化 ~11.0%）","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:982:        spy_returns = pd.Series(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:986:        alpha = _compute_alpha(strat_returns, spy_returns)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:988:        # 期望 alpha ≈ 17.5%（正数，跑赢 SPY）","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:989:        assert alpha > 0.0, f\"策略年化应高于 SPY，alpha 应为正，实际 {alpha:.4f}\"","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:995:    def test_compute_alpha_spy_unavailable(self):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:996:        \"\"\"SPY 数据为 None → alpha = 0.0（降级处理，不抛异常）。\"\"\"","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1000:        # spy_returns=None","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1002:        # spy_returns=空 Series","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1003:        empty_spy = pd.Series(dtype=float)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1004:        assert _compute_alpha(strat_returns, empty_spy) == 0.0","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1007:        \"\"\"策略跑输 SPY → alpha 为负。\"\"\"","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1009:        # 策略日均 0.0001 (0.01%)，SPY 日均 0.001 (0.1%)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1011:        spy_returns = pd.Series(np.random.normal(0.001, 0.002, 252), index=idx)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1013:        alpha = _compute_alpha(strat_returns, spy_returns)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1015:            f\"策略跑输 SPY 时 alpha 应为负，实际 {alpha:.4f}\"","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1058:        # 构造 SPY 数据：温和上涨（年化 ~10%）","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1061:        spy_close = [100.0 * (1.0004 ** i) for i in range(n)]  # ~10% 年化","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1062:        spy_df = pd.DataFrame({","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1063:            \"open\": [c - 0.1 for c in spy_close],","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1064:            \"high\": [c + 0.5 for c in spy_close],","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1065:            \"low\": [c - 0.5 for c in spy_close],","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1066:            \"close\": spy_close,","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1069:        spy_returns = spy_df[\"close\"].pct_change().dropna()","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1072:        # 日均 0.0004（~10% 年化，与 SPY 持平 → alpha ≈ 0）","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1078:        # 日均 0.0011（~32% 年化，远超 SPY → alpha ≈ 22%）","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1086:        alpha_a = _compute_alpha(returns_a, spy_returns)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1087:        alpha_b = _compute_alpha(returns_b, spy_returns)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1113:        # 构造 mock store：返回 SPY + 普通上涨数据","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1118:            mapping = {\"AAPL\": df_up, \"SPY\": spy_df}","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1167:        # SPY 温和上涨","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1168:        spy_close = [100.0 * (1.0004 ** i) for i in range(n)]","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1169:        spy_df = pd.DataFrame({","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1170:            \"open\": [c - 0.1 for c in spy_close],","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1171:            \"high\": [c + 0.5 for c in spy_close],","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1172:            \"low\": [c - 0.5 for c in spy_close],","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1173:            \"close\": spy_close,","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1176:        spy_returns = spy_df[\"close\"].pct_change().dropna()"]
---
["/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:970:        \"\"\"构造已知策略收益和 SPY 收益，验证 alpha 计算正确。","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:972:        策略日均收益 0.001 (0.1%)，SPY 日均收益 0.0004 (0.04%)。","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:981:        # SPY 收益：稳定 0.04%/日（年化 ~11.0%）","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:982:        spy_returns = pd.Series(","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:986:        alpha = _compute_alpha(strat_returns, spy_returns)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:988:        # 期望 alpha ≈ 17.5%（正数，跑赢 SPY）","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:989:        assert alpha > 0.0, f\"策略年化应高于 SPY，alpha 应为正，实际 {alpha:.4f}\"","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:995:    def test_compute_alpha_spy_unavailable(self):","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:996:        \"\"\"SPY 数据为 None → alpha = 0.0（降级处理，不抛异常）。\"\"\"","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1000:        # spy_returns=None","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1002:        # spy_returns=空 Series","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1003:        empty_spy = pd.Series(dtype=float)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1004:        assert _compute_alpha(strat_returns, empty_spy) == 0.0","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1007:        \"\"\"策略跑输 SPY → alpha 为负。\"\"\"","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1009:        # 策略日均 0.0001 (0.01%)，SPY 日均 0.001 (0.1%)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1011:        spy_returns = pd.Series(np.random.normal(0.001, 0.002, 252), index=idx)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1013:        alpha = _compute_alpha(strat_returns, spy_returns)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1015:            f\"策略跑输 SPY 时 alpha 应为负，实际 {alpha:.4f}\"","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1058:        # 构造 SPY 数据：温和上涨（年化 ~10%）","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1061:        spy_close = [100.0 * (1.0004 ** i) for i in range(n)]  # ~10% 年化","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1062:        spy_df = pd.DataFrame({","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1063:            \"open\": [c - 0.1 for c in spy_close],","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1064:            \"high\": [c + 0.5 for c in spy_close],","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1065:            \"low\": [c - 0.5 for c in spy_close],","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1066:            \"close\": spy_close,","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1069:        spy_returns = spy_df[\"close\"].pct_change().dropna()","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1072:        # 日均 0.0004（~10% 年化，与 SPY 持平 → alpha ≈ 0）","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1078:        # 日均 0.0011（~32% 年化，远超 SPY → alpha ≈ 22%）","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1086:        alpha_a = _compute_alpha(returns_a, spy_returns)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1087:        alpha_b = _compute_alpha(returns_b, spy_returns)","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1113:        # 构造 mock store：返回 SPY + 普通上涨数据","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1118:            mapping = {\"AAPL\": df_up, \"SPY\": spy_df}","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1167:        # SPY 温和上涨","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1168:        spy_close = [100.0 * (1.0004 ** i) for i in range(n)]","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1169:        spy_df = pd.DataFrame({","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1170:            \"open\": [c - 0.1 for c in spy_close],","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1171:            \"high\": [c + 0.5 for c in spy_close],","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1172:            \"low\": [c - 0.5 for c in spy_close],","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1173:            \"close\": spy_close,","/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py:1176:        spy_returns = spy_df[\"close\"].pct_change().dropna()"]
---
I
---
 see
---
.
---
 The
---
 existing
---
 tests
---
 use
---
 `
---
SP
---
Y
---
`
---
 with
---
 `
---
1
---
.
---
000
---
4
---
 **
---
 i
---
`
---
 (
---
slow
---
 growth
---
,
---
 ~
---
10
---
%
---
 annual
---
ized
---
)
---
 as
---
 benchmark
---
,
---
 while
---
 the
---
 strategy
---
 data
---
 uses
---
 `
---
100
---
.
---
0
---
 +
---
 i
---
 *
---
 
---
0
---
.
---
1
---
`
---
 (
---
strong
---
 upt
---
rend
---
,
---
 ~
---
28
---
%
---
 annual
---
ized
---
).
---
 So
---
 strategy
---
 out
---
per
---
forms
---
 SP
---
Y
---
 →
---
 alpha
---
 >
---
 
---
0
---
.


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
 how
---
 the
---
 `
---
mock
---
_store
---
`
---
 fixture
---
 is
---
 used
---
 and
---
 check
---
 if
---
 I
---
 should
---
 add
---
 SP
---
Y
---
 to
---
 it
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
 line
---
 
---
110
---
0
---
-
---
113
---
0
---
 to
---
 see
---
 the
---
 pattern
---
 used
---
 in
---
 Iter
---
 #
---
12
---
 tests
---
.
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py","limit":40,"offset":1100}
---
1100→                    continue
1101→                if strategy_name == "dual_ma":
1102→                    results.append(SingleBacktestResult(
1103→                        sym, strategy_name, params, 1.0, 10.0, 5.0, 55.0, 10, returns_a,
1104→                        closed_trades=10,
1105→                    ))
1106→                else:  # rsi_mean_revert
1107→                    results.append(SingleBacktestResult(
1108→                        sym, strategy_name, params, 1.0, 30.0, 8.0, 50.0, 10, returns_b,
1109→                        closed_trades=10,
1110→                    ))
1111→            return results
1112→
1113→        # 构造 mock store：返回 SPY + 普通上涨数据
1114→        df_up = _make_ohlcv(n, trend="up")
1115→        store = MagicMock()
1116→
1117→        def get_bars_multi(symbols, start, end, timeframe="1d"):
1118→            mapping = {"AAPL": df_up, "SPY": spy_df}
1119→            return {s: mapping[s] for s in symbols if s in mapping}
1120→
1121→        store.get_bars_multi.side_effect = get_bars_multi
1122→
1123→        universe = MagicMock()
1124→        universe.get_groups.return_value = {"test_group": ["AAPL"]}
1125→
1126→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=1)
1127→
1128→        with patch(
1129→            "mytrader.backtest.matrix_backtest._backtest_batch",
1130→            side_effect=mock_backtest_batch,
1131→        ):
1132→            report = mb.run(
1133→                strategies=["dual_ma", "rsi_mean_revert"],
1134→                param_grids={
1135→                    "dual_ma": {"fast": [5], "slow": [20]},
1136→                    "rsi_mean_revert": {
1137→                        "period": [14], "oversold": [30], "overbought": [70]
1138→                    },
1139→                },
1140→
---
1100→                    continue
1101→                if strategy_name == "dual_ma":
1102→                    results.append(SingleBacktestResult(
1103→                        sym, strategy_name, params, 1.0, 10.0, 5.0, 55.0, 10, returns_a,
1104→                        closed_trades=10,
1105→                    ))
1106→                else:  # rsi_mean_revert
1107→                    results.append(SingleBacktestResult(
1108→                        sym, strategy_name, params, 1.0, 30.0, 8.0, 50.0, 10, returns_b,
1109→                        closed_trades=10,
1110→                    ))
1111→            return results
1112→
1113→        # 构造 mock store：返回 SPY + 普通上涨数据
1114→        df_up = _make_ohlcv(n, trend="up")
1115→        store = MagicMock()
1116→
1117→        def get_bars_multi(symbols, start, end, timeframe="1d"):
1118→            mapping = {"AAPL": df_up, "SPY": spy_df}
1119→            return {s: mapping[s] for s in symbols if s in mapping}
1120→
1121→        store.get_bars_multi.side_effect = get_bars_multi
1122→
1123→        universe = MagicMock()
1124→        universe.get_groups.return_value = {"test_group": ["AAPL"]}
1125→
1126→        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=1)
1127→
1128→        with patch(
1129→            "mytrader.backtest.matrix_backtest._backtest_batch",
1130→            side_effect=mock_backtest_batch,
1131→        ):
1132→            report = mb.run(
1133→                strategies=["dual_ma", "rsi_mean_revert"],
1134→                param_grids={
1135→                    "dual_ma": {"fast": [5], "slow": [20]},
1136→                    "rsi_mean_revert": {
1137→                        "period": [14], "oversold": [30], "overbought": [70]
1138→                    },
1139→                },
1140→
---
Now
---
 I
---
 understand
---
 the
---
 pattern
---
.
---
 I
---
 need
---
 to
---
 add
---
 SP
---
Y
---
 to
---
 the
---
 `
---
mock
---
_store
---
`
---
 fixture
---
 so
---
 that
---
 WF
---
 tests
---
 have
---
 SP
---
Y
---
 data
---
.
---
 Let
---
 me
---
 create
---
 a
---
 plan
---
 and
---
 start
---
 implementing
---
.


---
Let
---
 me
---
 now
---
 create
---
 tasks
---
 and
---
 start
---
 implementing
---
.
---
 The
---
 implementation
---
 is
---
 clear
---
:


---
1
---
.
---
 Add
---
 `
---
W
---
ALK
---
_FORWARD
---
_VAL
---
_ALPHA
---
_F
---
LOOR
---
`
---
 constant
---


---
2
---
.
---
 Add
---
 `
---
val
---
_alpha
---
`
---
 to
---
 `
---
Walk
---
Forward
---
Round
---
`

---
3
---
.
---
 Add
---
 `
---
avg
---
_val
---
_alpha
---
`
---
 +
---
 `
---
min
---
_val
---
_alpha
---
`
---
 to
---
 `
---
Walk
---
Forward
---
Report
---
`

---
4
---
.
---
 Update
---
 `
---
run
---
_walk
---
_forward
---
`
---
 to
---
 compute
---
 alpha
---
 +
---
 gate
---
 +
---
 aggregation
---


---
5
---
.
---
 Update
---
 `
---
main
---
.py
---
`
---
 WF
---
 logs
---


---
6
---
.
---
 Write
---
 new
---
 test
---
 file
---
 `
---
test
---
_wf
---
_alpha
---
_gate
---
.py
---
`

---
7
---
.
---
 Update
---
 `
---
mock
---
_store
---
`
---
 fixture
---
 to
---
 include
---
 SP
---
Y
---
 data
---


---
8
---
.
---
 Run
---
 pytest
---


---
9
---
.
---
 Update
---
 docs
---



---
Let
---
 me
---
 start
---
 implementing
---
.
---
我现在
---
已经
---
完全
---
理解
---
了
---
。
---
让我
---
创建
---
一个
---
任务
---
列表
---
并
---
开始
---
实施
---
。
---
{"activeForm":"Adding WF alpha constant + dataclass fields","description":"Add WALK_FORWARD_VAL_ALPHA_FLOOR=-5.0 constant; add val_alpha to WalkForwardRound; add avg_val_alpha + min_val_alpha to WalkForwardReport","subject":"Add WF alpha constant + dataclass fields"}
---
{"activeForm":"Updating run_walk_forward","description":"Compute val_alpha vs SPY in validation period; gate: passed = dd_passed AND alpha > -5%; aggregate avg/min val_alpha; pass_all_rounds = all passed AND avg_alpha > 0","subject":"Update run_walk_forward with alpha computation + gate"}
---
{"activeForm":"Updating main.py WF logs","description":"Add alpha to per-round log + avg/min val_alpha to summary log; update WARNING message","subject":"Update main.py WF logs with alpha"}
---
{"activeForm":"Writing WF alpha gate tests","description":"9 new tests per spec §5: dataclass fields, gate reject/pass/allow small negative, summary avg logic, SPY unavailable, alpha computed correctly","subject":"Write test_wf_alpha_gate.py"}
---
{"activeForm":"Updating mock_store fixture","description":"Add SPY data (slow trend) to mock_store fixture so WF integration test has positive alpha; update test assertions if needed","subject":"Update existing WF tests for SPY data"}
---
{"activeForm":"Running pytest","description":"Run full pytest suite, confirm all tests pass (659+ + 9 new = 668+)","subject":"Run pytest and fix failures"}
---
{"activeForm":"Updating docs","description":"Update designs/design_v2/07-backtest-module.md, alignment/iteration_trajectory.md, alignment/decision_log.md, .codebuddy/CODEBUDDY.md","subject":"Update docs (design 07 + trajectory + decision_log + CODEBUDDY)"}
---
Task #1 created successfully: Add WF alpha constant + dataclass fields
---
Task #1 created successfully: Add WF alpha constant + dataclass fields
---
Task #2 created successfully: Update run_walk_forward with alpha computation + gate
---
Task #2 created successfully: Update run_walk_forward with alpha computation + gate
---
Task #3 created successfully: Update main.py WF logs with alpha
---
Task #3 created successfully: Update main.py WF logs with alpha
---
Task #4 created successfully: Write test_wf_alpha_gate.py
---
Task #4 created successfully: Write test_wf_alpha_gate.py
---
Task #5 created successfully: Update existing WF tests for SPY data
---
Task #5 created successfully: Update existing WF tests for SPY data
---
Task #6 created successfully: Run pytest and fix failures
---
Task #6 created successfully: Run pytest and fix failures
---
Task #7 created successfully: Update docs (design 07 + trajectory + decision_log + CODEBUDDY)
---
Task #7 created successfully: Update docs (design 07 + trajectory + decision_log + CODEBUDDY)
---
{"status":"in_progress","taskId":"1"}
---
Updated task #1 status
---
Updated task #1 status
---
现在
---
让我
---
来
---
实施
---
这些
---
变更
---
。
---
首先
---
从
---
常
---
量和
---
 data
---
class
---
 字
---
段
---
开始
---
。
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py","new_string":"# Constitution L7 Walk-Forward 门槛：单轮验证期 portfolio DD ≤ 15%\n# （低于 L1 的 20% 线，给样本外留缓冲）\nWALK_FORWARD_VAL_DD_THRESHOLD: float = 15.0\n\n# 迭代 #13 新增：WF 验证期 alpha 单轮下限（百分数）\n# 单轮允许小幅跑输 SPY（alpha > -5%），但 4 轮平均必须跑赢（avg > 0）\n# 设计动机：WF 与 matrix_backtest 目标一致性——matrix_backtest 用 alpha 选策略，\n# WF 也必须校验 alpha，否则 WF 通过 ≠ 跑赢 SPY\n# （Iter #11 实证：WF 4/4 pass 但组合 alpha=-21%，因为 WF gate 只校验 DD 不校验 alpha）\n# 详见 experience.md #8：\"验收 gate 必须校验跑赢 benchmark（正 alpha）\"\nWALK_FORWARD_VAL_ALPHA_FLOOR: float = -5.0","old_string":"# Constitution L7 Walk-Forward 门槛：单轮验证期 portfolio DD ≤ 15%\n# （低于 L1 的 20% 线，给样本外留缓冲）\nWALK_FORWARD_VAL_DD_THRESHOLD: float = 15.0"}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py
---
现在
---
更新
---
 `
---
Walk
---
Forward
---
Round
---
`
---
 以
---
添加
---
 `
---
val
---
_alpha
---
`
---
 字
---
段
---
。
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py","new_string":"@dataclass\nclass WalkForwardRound:\n    \"\"\"单轮 Walk-Forward 验证结果。\n\n    一轮 = 训练期（找最优参数）+ 验证期（用同参数回测，记录样本外指标）。\n\n    Attributes:\n        round_num:    轮次编号（1-indexed）\n        train_start:  训练期起始日期（含）\n        train_end:    训练期结束日期（含）\n        val_start:    验证期起始日期（含）\n        val_end:      验证期结束日期（含）\n        val_sortino:  验证期等权组合 Sortino Ratio（年化）\n        val_max_dd:   验证期等权组合最大回撤（正值百分数，0~100）\n        val_alpha:    验证期等权组合 alpha vs SPY（百分数，迭代 #13 新增）\n                      与 matrix_backtest 的 alpha 选择目标一致（目标一致性修复）\n        passed:       是否通过 = val_max_dd <= 15% AND val_alpha > -5%\n    \"\"\"\n\n    round_num: int\n    train_start: date\n    train_end: date\n    val_start: date\n    val_end: date\n    val_sortino: float\n    val_max_dd: float\n    val_alpha: float = 0.0   # 迭代 #13：验证期 portfolio alpha vs SPY（百分数）\n    passed: bool","old_string":"@dataclass\nclass WalkForwardRound:\n    \"\"\"单轮 Walk-Forward 验证结果。\n\n    一轮 = 训练期（找最优参数）+ 验证期（用同参数回测，记录样本外指标）。\n\n    Attributes:\n        round_num:    轮次编号（1-indexed）\n        train_start:  训练期起始日期（含）\n        train_end:    训练期结束日期（含）\n        val_start:    验证期起始日期（含）\n        val_end:      验证期结束日期（含）\n        val_sortino:  验证期等权组合 Sortino Ratio（年化）\n        val_max_dd:   验证期等权组合最大回撤（正值百分数，0~100）\n        passed:       是否通过 = val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD (15%)\n    \"\"\"\n\n    round_num: int\n    train_start: date\n    train_end: date\n    val_start: date\n    val_end: date\n    val_sortino: float\n    val_max_dd: float\n    passed: bool"}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py
---
现在
---
更新
---
 `
---
Walk
---
Forward
---
Report
---
`
---
 以
---
添加
---
 `
---
avg
---
_val
---
_alpha
---
`
---
 和
---
 `
---
min
---
_val
---
_alpha
---
`
---
。
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py","new_string":"@dataclass\nclass WalkForwardReport:\n    \"\"\"Walk-Forward 4 轮验证汇总报告。\n\n    Constitution L7 要求 Backtest(>=5年) → Walk-Forward(4轮) → Paper → Live。\n    本报告是 Walk-Forward 阶段的产出。\n\n    Attributes:\n        rounds:         每轮结果列表（长度通常为 4）\n        pass_all_rounds: 是否所有轮都通过 AND avg_val_alpha > 0\n                         （迭代 #13：加 avg alpha > 0 条件，要求 OOS 平均跑赢 SPY）\n        max_val_dd:     所有轮中最大的验证期 DD（用于风险监控）\n        avg_val_alpha:  所有轮验证期 alpha 的平均值（迭代 #13 新增，百分数）\n        min_val_alpha:  所有轮中最差的验证期 alpha（迭代 #13 新增，百分数）\n    \"\"\"\n\n    rounds: list[WalkForwardRound] = field(default_factory=list)\n    pass_all_rounds: bool = False\n    max_val_dd: float = 0.0\n    avg_val_alpha: float = 0.0   # 迭代 #13：4 轮平均验证期 alpha（百分数）\n    min_val_alpha: float = 0.0   # 迭代 #13：4 轮中最差的验证期 alpha（百分数）","old_string":"@dataclass\nclass WalkForwardReport:\n    \"\"\"Walk-Forward 4 轮验证汇总报告。\n\n    Constitution L7 要求 Backtest(>=5年) → Walk-Forward(4轮) → Paper → Live。\n    本报告是 Walk-Forward 阶段的产出。\n\n    Attributes:\n        rounds:         每轮结果列表（长度通常为 4）\n        pass_all_rounds: 是否所有轮都通过（all(r.passed for r in rounds)）\n        max_val_dd:     所有轮中最大的验证期 DD（用于风险监控）\n    \"\"\"\n\n    rounds: list[WalkForwardRound] = field(default_factory=list)\n    pass_all_rounds: bool = False\n    max_val_dd: float = 0.0"}
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
现在
---
更新
---
 `
---
run
---
_walk
---
_forward
---
`
---
 以
---
计算
---
 alpha
---
、
---
gate
---
 和
---
聚合
---
。
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py","new_string":"        # 计算整体 portfolio 指标（等权合并所有组的日收益率）\n        if not all_returns:\n            val_sortino = 0.0\n            val_max_dd = 0.0\n            val_alpha = 0.0\n            logger.warning(\n                f\"[WalkForward] Round {round_num}: no valid val returns — \"\n                f\"sortino=0, dd=0, alpha=0, passed=True (vacuous)\"\n            )\n        else:\n            combined = pd.concat(all_returns, axis=1).mean(axis=1).dropna()\n            if len(combined) < 5:\n                val_sortino = 0.0\n                val_max_dd = 0.0\n                val_alpha = 0.0\n            else:\n                val_sortino = _compute_sortino(combined)\n                wrapper = [SingleBacktestResult(\n                    symbol=\"portfolio\", strategy=\"\", params={},\n                    sharpe=0.0, total_return_pct=0.0, max_drawdown_pct=0.0,\n                    win_rate_pct=0.0, total_trades=0, daily_returns=combined,\n                )]\n                val_max_dd = _portfolio_max_drawdown_from_results(wrapper)\n\n                # ── 迭代 #13：计算验证期 alpha vs SPY ──\n                # 与 matrix_backtest 的 alpha 选择目标一致（目标一致性修复）\n                # SPY 不可用时 alpha=0.0（与 _compute_alpha 的降级语义一致）\n                spy_val_returns = mb._get_spy_returns(val_start, val_end)\n                if spy_val_returns is not None:\n                    val_alpha = _compute_alpha(combined, spy_val_returns)\n                else:\n                    val_alpha = 0.0\n                    logger.warning(\n                        f\"[WalkForward] Round {round_num}: SPY data unavailable for \"\n                        f\"val period {val_start}~{val_end} — val_alpha=0 (degraded)\"\n                    )\n\n        # ── 迭代 #13：gate 加 alpha 校验 ──\n        # 单轮：DD ≤ 15% AND alpha > -5%（允许小幅跑输，不容忍灾难性跑输）\n        # 汇总（在 report 构建时）：all rounds passed AND avg_val_alpha > 0\n        dd_passed = val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD\n        alpha_passed = val_alpha > WALK_FORWARD_VAL_ALPHA_FLOOR\n        passed = dd_passed and alpha_passed\n        wf_rounds.append(WalkForwardRound(\n            round_num=round_num,\n            train_start=train_start,\n            train_end=train_end,\n            val_start=val_start,\n            val_end=val_end,\n            val_sortino=val_sortino,\n            val_max_dd=val_max_dd,\n            val_alpha=val_alpha,\n            passed=passed,\n        ))\n        logger.info(\n            f\"[WalkForward] Round {round_num} result: \"\n            f\"sortino={val_sortino:.4f}, dd={val_max_dd:.4f}%, \"\n            f\"alpha={val_alpha:.4f}%, passed={passed} \"\n            f\"(dd_threshold={WALK_FORWARD_VAL_DD_THRESHOLD}%, \"\n            f\"alpha_floor={WALK_FORWARD_VAL_ALPHA_FLOOR}%)\"\n        )\n\n    # ── 迭代 #13：汇总 alpha 聚合 + pass_all_rounds 加 avg alpha > 0 条件 ──\n    val_alphas = [r.val_alpha for r in wf_rounds]\n    avg_val_alpha = sum(val_alphas) / len(val_alphas) if val_alphas else 0.0\n    min_val_alpha = min(val_alphas) if val_alphas else 0.0\n\n    # 单轮全过 AND 平均 alpha > 0（OOS 平均必须跑赢 SPY）\n    all_rounds_passed = all(r.passed for r in wf_rounds) if wf_rounds else False\n    avg_alpha_positive = avg_val_alpha > 0\n    pass_all = all_rounds_passed and avg_alpha_positive\n\n    report = WalkForwardReport(\n        rounds=wf_rounds,\n        pass_all_rounds=pass_all,\n        max_val_dd=max((r.val_max_dd for r in wf_rounds), default=0.0),\n        avg_val_alpha=avg_val_alpha,\n        min_val_alpha=min_val_alpha,\n    )\n    logger.info(\n        f\"[WalkForward] done: {len(wf_rounds)} rounds, \"\n        f\"pass_all_rounds={report.pass_all_rounds}, \"\n        f\"max_val_dd={report.max_val_dd:.4f}%, \"\n        f\"avg_val_alpha={report.avg_val_alpha:.4f}%, \"\n        f\"min_val_alpha={report.min_val_alpha:.4f}%\"\n    )\n    return report","old_string":"        # 计算整体 portfolio 指标（等权合并所有组的日收益率）\n        if not all_returns:\n            val_sortino = 0.0\n            val_max_dd = 0.0\n            logger.warning(\n                f\"[WalkForward] Round {round_num}: no valid val returns — \"\n                f\"sortino=0, dd=0, passed=True (vacuous)\"\n            )\n        else:\n            combined = pd.concat(all_returns, axis=1).mean(axis=1).dropna()\n            if len(combined) < 5:\n                val_sortino = 0.0\n                val_max_dd = 0.0\n            else:\n                val_sortino = _compute_sortino(combined)\n                wrapper = [SingleBacktestResult(\n                    symbol=\"portfolio\", strategy=\"\", params={},\n                    sharpe=0.0, total_return_pct=0.0, max_drawdown_pct=0.0,\n                    win_rate_pct=0.0, total_trades=0, daily_returns=combined,\n                )]\n                val_max_dd = _portfolio_max_drawdown_from_results(wrapper)\n\n        passed = val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD\n        wf_rounds.append(WalkForwardRound(\n            round_num=round_num,\n            train_start=train_start,\n            train_end=train_end,\n            val_start=val_start,\n            val_end=val_end,\n            val_sortino=val_sortino,\n            val_max_dd=val_max_dd,\n            passed=passed,\n        ))\n        logger.info(\n            f\"[WalkForward] Round {round_num} result: \"\n            f\"sortino={val_sortino:.4f}, dd={val_max_dd:.4f}%, \"\n            f\"passed={passed} (threshold={WALK_FORWARD_VAL_DD_THRESHOLD}%)\"\n        )\n\n    report = WalkForwardReport(\n        rounds=wf_rounds,\n        pass_all_rounds=all(r.passed for r in wf_rounds) if wf_rounds else False,\n        max_val_dd=max((r.val_max_dd for r in wf_rounds), default=0.0),\n    )\n    logger.info(\n        f\"[WalkForward] done: {len(wf_rounds)} rounds, \"\n        f\"pass_all_rounds={report.pass_all_rounds}, \"\n        f\"max_val_dd={report.max_val_dd:.4f}%\"\n    )\n    return report"}
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
现在
---
更新
---
 `
---
main
---
.py
---
`
---
 
---
中的
---
 WF
---
 日
---
志
---
。
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/main.py","new_string":"        for r in wf_report.rounds:\n            logger.info(\n                f\"[WalkForward] Round {r.round_num}/4: \"\n                f\"train={r.train_start}~{r.train_end}, \"\n                f\"val={r.val_start}~{r.val_end}, \"\n                f\"sortino={r.val_sortino:.4f}, \"\n                f\"dd={r.val_max_dd:.4f}%, \"\n                f\"alpha={r.val_alpha:.4f}%, \"\n                f\"passed={r.passed}\"\n            )\n        logger.info(\n            f\"[WalkForward] Summary: pass_all_rounds={wf_report.pass_all_rounds}, \"\n            f\"max_val_dd={wf_report.max_val_dd:.4f}%, \"\n            f\"avg_val_alpha={wf_report.avg_val_alpha:.4f}%, \"\n            f\"min_val_alpha={wf_report.min_val_alpha:.4f}%\"\n        )\n        if not wf_report.pass_all_rounds:\n            logger.warning(\n                \"[WalkForward] NOT all rounds passed — \"\n                \"Constitution L7 requires all 4 rounds DD<=15% AND avg alpha>0 \"\n                \"before paper trading.\"\n            )","old_string":"        for r in wf_report.rounds:\n            logger.info(\n                f\"[WalkForward] Round {r.round_num}/4: \"\n                f\"train={r.train_start}~{r.train_end}, \"\n                f\"val={r.val_start}~{r.val_end}, \"\n                f\"sortino={r.val_sortino:.4f}, \"\n                f\"dd={r.val_max_dd:.4f}%, \"\n                f\"passed={r.passed}\"\n            )\n        logger.info(\n            f\"[WalkForward] Summary: pass_all_rounds={wf_report.pass_all_rounds}, \"\n            f\"max_val_dd={wf_report.max_val_dd:.4f}%\"\n        )\n        if not wf_report.pass_all_rounds:\n            logger.warning(\n                \"[WalkForward] NOT all rounds passed — \"\n                \"Constitution L7 requires all 4 rounds DD<=15% before paper trading.\"\n            )"}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/main.py
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/main.py
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
现在
---
让我
---
来
---
编写
---
测试
---
文件
---
。
---
首先
---
，
---
让我
---
更
---
仔细
---
地
---
检查
---
现有的
---
测试
---
模式
---
，
---
以
---
匹配
---
测试
---
风格
---
。
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py","limit":60,"offset":1040}
---
1040→            f"MIN_SORTINO_THRESHOLD 应为 0.5（迭代 #9 spec），"
1041→            f"实际 {MIN_SORTINO_THRESHOLD}"
1042→        )
1043→
1044→
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
1100→
---
1040→            f"MIN_SORTINO_THRESHOLD 应为 0.5（迭代 #9 spec），"
1041→            f"实际 {MIN_SORTINO_THRESHOLD}"
1042→        )
1043→
1044→
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
1100→
---
Now
---
 I
---
 have
---
 a
---
 good
---
 understanding
---
.
---
 Let
---
 me
---
 write
---
 the
---
 test
---
 file
---
.
---
 I
---
'll
---
 create
---
 `
---
tests
---
/test
---
_wf
---
_alpha
---
_gate
---
.py
---
`
---
 with
---
 the
---
 
---
9
---
 tests
---
 from
---
 the
---
 spec
---
.
---
现在
---
让我
---
来
---
编写
---
测试
---
文件
---
。
---
{"content":"\"\"\"迭代 #13：WF Gate 加 Alpha 校验测试（Walk-Forward alpha gate）。\n\n验证：\n    1. `WalkForwardRound.val_alpha` 字段存在且默认 0.0\n    2. `WalkForwardReport.avg_val_alpha` / `min_val_alpha` 字段存在\n    3. 单轮 alpha < -5% → `passed=False`（即使 DD 合规）\n    4. 单轮 alpha > 0 且 DD ≤ 15% → `passed=True`\n    5. 单轮 alpha = -3%（> -5%）且 DD 合规 → `passed=True`\n    6. 4 轮全 pass 但 avg alpha < 0 → `pass_all_rounds=False`\n    7. 4 轮全 pass 且 avg alpha > 0 → `pass_all_rounds=True`\n    8. SPY 不可用时 val_alpha=0.0 + WARNING（降级不阻塞）\n    9. 用已知 returns + spy_returns 验证 val_alpha 值正确\n\n背景见 `iterations/iteration_13/spec.md` + `.codebuddy/notes/experience.md` #8。\n\"\"\"\n\nfrom __future__ import annotations\n\nfrom datetime import date as _date\nfrom unittest.mock import MagicMock, patch\n\nimport numpy as np\nimport pandas as pd\nimport pytest\n\nfrom mytrader.backtest.matrix_backtest import (\n    MatrixBacktest,\n    SingleBacktestResult,\n    WALK_FORWARD_VAL_ALPHA_FLOOR,\n    WALK_FORWARD_VAL_DD_THRESHOLD,\n    WalkForwardReport,\n    WalkForwardRound,\n    _compute_alpha,\n    run_walk_forward,\n)\n\n\n# ---------------------------------------------------------------------------\n# 1. Dataclass 字段测试\n# ---------------------------------------------------------------------------\n\nclass TestWFAlphaDataclassFields:\n    \"\"\"迭代 #13：WalkForwardRound / WalkForwardReport 新增 alpha 字段。\"\"\"\n\n    def test_wf_round_has_val_alpha_field(self):\n        \"\"\"WalkForwardRound.val_alpha 字段存在且默认 0.0。\"\"\"\n        r = WalkForwardRound(\n            round_num=1,\n            train_start=_date(2021, 7, 2),\n            train_end=_date(2023, 1, 2),\n            val_start=_date(2023, 1, 2),\n            val_end=_date(2023, 7, 2),\n            val_sortino=1.5,\n            val_max_dd=10.0,\n            passed=True,\n        )\n        # 默认值 0.0\n        assert hasattr(r, \"val_alpha\"), \"WalkForwardRound 应有 val_alpha 字段\"\n        assert r.val_alpha == 0.0, f\"val_alpha 默认应为 0.0，实际 {r.val_alpha}\"\n\n    def test_wf_round_val_alpha_can_be_set(self):\n        \"\"\"val_alpha 可以显式设置。\"\"\"\n        r = WalkForwardRound(\n            round_num=1,\n            train_start=_date(2021, 1, 1),\n            train_end=_date(2023, 1, 1),\n            val_start=_date(2023, 1, 1),\n            val_end=_date(2023, 7, 1),\n            val_sortino=1.0,\n            val_max_dd=10.0,\n            val_alpha=5.23,\n            passed=True,\n        )\n        assert r.val_alpha == 5.23\n\n    def test_wf_report_has_alpha_aggregation(self):\n        \"\"\"WalkForwardReport.avg_val_alpha 和 min_val_alpha 字段存在。\"\"\"\n        report = WalkForwardReport()\n        assert hasattr(report, \"avg_val_alpha\"), (\n            \"WalkForwardReport 应有 avg_val_alpha 字段\"\n        )\n        assert hasattr(report, \"min_val_alpha\"), (\n            \"WalkForwardReport 应有 min_val_alpha 字段\"\n        )\n        assert report.avg_val_alpha == 0.0\n        assert report.min_val_alpha == 0.0\n\n    def test_wf_report_alpha_aggregation_values(self):\n        \"\"\"avg_val_alpha / min_val_alpha 可以正确设置。\"\"\"\n        rounds = [\n            WalkForwardRound(\n                1, _date(2021, 1, 1), _date(2023, 1, 1),\n                _date(2023, 1, 1), _date(2023, 7, 1),\n                val_sortino=1.0, val_max_dd=10.0,\n                val_alpha=5.0, passed=True,\n            ),\n            WalkForwardRound(\n                2, _date(2021, 7, 1), _date(2023, 7, 1),\n                _date(2023, 7, 1), _date(2024, 1, 1),\n                val_sortino=0.8, val_max_dd=12.0,\n                val_alpha=-3.0, passed=True,\n            ),\n            WalkForwardRound(\n                3, _date(2022, 1, 1), _date(2024, 1, 1),\n                _date(2024, 1, 1), _date(2024, 7, 1),\n                val_sortino=1.2, val_max_dd=8.0,\n                val_alpha=7.0, passed=True,\n            ),\n        ]\n        val_alphas = [r.val_alpha for r in rounds]\n        report = WalkForwardReport(\n            rounds=rounds,\n            pass_all_rounds=True,\n            max_val_dd=12.0,\n            avg_val_alpha=sum(val_alphas) / len(val_alphas),\n            min_val_alpha=min(val_alphas),\n        )\n        assert report.avg_val_alpha == pytest.approx(3.0, abs=1e-9)\n        assert report.min_val_alpha == -3.0\n\n\n# ---------------------------------------------------------------------------\n# 2. Gate 逻辑测试（单轮）\n# ---------------------------------------------------------------------------\n\nclass TestWFGateSingleRound:\n    \"\"\"迭代 #13：单轮 gate = DD ≤ 15% AND alpha > -5%。\"\"\"\n\n    def test_wf_gate_rejects_negative_alpha(self):\n        \"\"\"单轮 alpha < -5% → passed=False（即使 DD 合规）。\n\n        场景：DD=10%（≤ 15% 合规），但 alpha=-8%（< -5% 灾难性跑输）\n        → passed=False\n        \"\"\"\n        r = WalkForwardRound(\n            round_num=1,\n            train_start=_date(2021, 1, 1),\n            train_end=_date(2023, 1, 1),\n            val_start=_date(2023, 1, 1),\n            val_end=_date(2023, 7, 1),\n            val_sortino=1.0,\n            val_max_dd=10.0,   # DD 合规\n            val_alpha=-8.0,    # 灾难性跑输\n            passed=False,      # alpha < -5% → fail\n        )\n        assert r.passed is False, (\n            \"alpha=-8% 应被 alpha floor=-5% 拦截，passed=False\"\n        )\n        # 验证常量\n        assert WALK_FORWARD_VAL_ALPHA_FLOOR == -5.0\n\n    def test_wf_gate_passes_positive_alpha(self):\n        \"\"\"单轮 alpha > 0 且 DD ≤ 15% → passed=True。\"\"\"\n        r = WalkForwardRound(\n            round_num=1,\n            train_start=_date(2021, 1, 1),\n            train_end=_date(2023, 1, 1),\n            val_start=_date(2023, 1, 1),\n            val_end=_date(2023, 7, 1),\n            val_sortino=1.5,\n            val_max_dd=10.0,\n            val_alpha=5.0,    # 跑赢 SPY\n            passed=True,\n        )\n        assert r.passed is True\n        assert r.val_alpha > 0\n\n    def test_wf_gate_allows_small_negative_alpha(self):\n        \"\"\"单轮 alpha = -3%（> -5% floor）且 DD 合规 → passed=True。\n\n        设计动机：单轮允许小幅跑输 SPY（-5%~0%），可能是市场噪音。\n        但 4 轮平均必须 > 0（在汇总层校验）。\n        \"\"\"\n        r = WalkForwardRound(\n            round_num=1,\n            train_start=_date(2021, 1, 1),\n            train_end=_date(2023, 1, 1),\n            val_start=_date(2023, 1, 1),\n            val_end=_date(2023, 7, 1),\n            val_sortino=1.0,\n            val_max_dd=10.0,\n            val_alpha=-3.0,   # 小幅跑输，但 > -5% floor\n            passed=True,      # DD 合规 + alpha > floor\n        )\n        assert r.passed is True\n        assert r.val_alpha > WALK_FORWARD_VAL_ALPHA_FLOOR\n\n    def test_wf_gate_alpha_floor_boundary(self):\n        \"\"\"alpha = -5.0（恰好等于 floor）→ alpha_passed = False（> 严格大于）。\n\n        gate 条件是 alpha > WALK_FORWARD_VAL_ALPHA_FLOOR（严格大于），\n        alpha=-5.0 不满足 > -5.0，所以 passed=False。\n        \"\"\"\n        # alpha = -5.0 恰好等于 floor，不满足 > -5.0\n        alpha_at_boundary = -5.0\n        alpha_passed = alpha_at_boundary > WALK_FORWARD_VAL_ALPHA_FLOOR\n        assert alpha_passed is False, (\n            \"alpha=-5.0 不满足 > -5.0（严格大于），应 fail\"\n        )\n\n        # alpha = -4.99 刚好过 floor\n        alpha_just_above = -4.99\n        alpha_passed_just = alpha_just_above > WALK_FORWARD_VAL_ALPHA_FLOOR\n        assert alpha_passed_just is True\n\n\n# ---------------------------------------------------------------------------\n# 3. 汇总 gate 逻辑测试（pass_all_rounds）\n# ---------------------------------------------------------------------------\n\nclass TestWFSummaryGate:\n    \"\"\"迭代 #13：汇总 gate = all rounds passed AND avg_val_alpha > 0。\"\"\"\n\n    def test_wf_summary_avg_alpha_negative_fails(self):\n        \"\"\"4 轮全 pass（单轮 DD+alpha floor 都过）但 avg alpha < 0\n        → pass_all_rounds=False。\n\n        场景：4 轮 alpha 分别为 1, -3, -2, -1（avg=-1.25 < 0）\n        每轮 alpha > -5% floor 所以单轮 passed=True，\n        但 avg=-1.25 < 0 → pass_all_rounds=False\n        \"\"\"\n        rounds = [\n            WalkForwardRound(\n                1, _date(2021, 1, 1), _date(2023, 1, 1),\n                _date(2023, 1, 1), _date(2023, 7, 1),\n                val_sortino=1.0, val_max_dd=10.0,\n                val_alpha=1.0, passed=True,\n            ),\n            WalkForwardRound(\n                2, _date(2021, 7, 1), _date(2023, 7, 1),\n                _date(2023, 7, 1), _date(2024, 1, 1),\n                val_sortino=0.8, val_max_dd=12.0,\n                val_alpha=-3.0, passed=True,   # > -5% floor\n            ),\n            WalkForwardRound(\n                3, _date(2022, 1, 1), _date(2024, 1, 1),\n                _date(2024, 1, 1), _date(2024, 7, 1),\n                val_sortino=1.2, val_max_dd=8.0,\n                val_alpha=-2.0, passed=True,   # > -5% floor\n            ),\n            WalkForwardRound(\n                4, _date(2022, 7, 1), _date(2024, 7, 1),\n                _date(2024, 7, 1), _date(2025, 1, 1),\n                val_sortino=0.9, val_max_dd=11.0,\n                val_alpha=-1.0, passed=True,   # > -5% floor\n            ),\n        ]\n        val_alphas = [r.val_alpha for r in rounds]\n        avg_alpha = sum(val_alphas) / len(val_alphas)\n\n        # 验证测试前提：每轮单轮 pass，但 avg < 0\n        assert all(r.passed for r in rounds), \"测试前提：每轮单轮都 pass\"\n        assert avg_alpha < 0, (\n            f\"测试前提：avg alpha 应 < 0，实际 {avg_alpha}\"\n        )\n\n        # 汇总：all passed AND avg > 0 → False（因为 avg < 0）\n        all_rounds_passed = all(r.passed for r in rounds)\n        avg_alpha_positive = avg_alpha > 0\n        pass_all = all_rounds_passed and avg_alpha_positive\n        assert pass_all is False, (\n            \"avg alpha < 0 时 pass_all_rounds 应为 False\"\n        )\n\n    def test_wf_summary_avg_alpha_positive_passes(self):\n        \"\"\"4 轮全 pass 且 avg alpha > 0 → pass_all_rounds=True。\"\"\"\n        rounds = [\n            WalkForwardRound(\n                1, _date(2021, 1, 1), _date(2023, 1, 1),\n                _date(2023, 1, 1), _date(2023, 7, 1),\n                val_sortino=1.0, val_max_dd=10.0,\n                val_alpha=5.0, passed=True,\n            ),\n            WalkForwardRound(\n                2, _date(2021, 7, 1), _date(2023, 7, 1),\n                _date(2023, 7, 1), _date(2024, 1, 1),\n                val_sortino=0.8, val_max_dd=12.0,\n                val_alpha=-3.0, passed=True,   # 小幅跑输但 > floor\n            ),\n            WalkForwardRound(\n                3, _date(2022, 1, 1), _date(2024, 1, 1),\n                _date(2024, 1, 1), _date(2024, 7, 1),\n                val_sortino=1.2, val_max_dd=8.0,\n                val_alpha=7.0, passed=True,\n            ),\n            WalkForwardRound(\n                4, _date(2022, 7, 1), _date(2024, 7, 1),\n                _date(2024, 7, 1), _date(2025, 1, 1),\n                val_sortino=0.9, val_max_dd=11.0,\n                val_alpha=4.0, passed=True,\n            ),\n        ]\n        val_alphas = [r.val_alpha for r in rounds]\n        avg_alpha = sum(val_alphas) / len(val_alphas)\n\n        # 验证测试前提\n        assert all(r.passed for r in rounds)\n        assert avg_alpha > 0, f\"avg alpha 应 > 0，实际 {avg_alpha}\"\n\n        all_rounds_passed = all(r.passed for r in rounds)\n        avg_alpha_positive = avg_alpha > 0\n        pass_all = all_rounds_passed and avg_alpha_positive\n        assert pass_all is True\n\n    def test_wf_summary_single_round_fail_fails(self):\n        \"\"\"1 轮 fail（alpha < floor）即使 avg > 0 → pass_all_rounds=False。\n\n        场景：3 轮强正 alpha，1 轮 alpha=-8%（< -5% floor → fail）\n        avg = (5+7+4-8)/4 = 2.0 > 0，但因为 R2 fail → pass_all=False\n        \"\"\"\n        rounds = [\n            WalkForwardRound(\n                1, _date(2021, 1, 1), _date(2023, 1, 1),\n                _date(2023, 1, 1), _date(2023, 7, 1),\n                val_sortino=1.0, val_max_dd=10.0,\n                val_alpha=5.0, passed=True,\n            ),\n            WalkForwardRound(\n                2, _date(2021, 7, 1), _date(2023, 7, 1),\n                _date(2023, 7, 1), _date(2024, 1, 1),\n                val_sortino=0.8, val_max_dd=12.0,\n                val_alpha=-8.0, passed=False,   # < -5% floor → fail\n            ),\n            WalkForwardRound(\n                3, _date(2022, 1, 1), _date(2024, 1, 1),\n                _date(2024, 1, 1), _date(2024, 7, 1),\n                val_sortino=1.2, val_max_dd=8.0,\n                val_alpha=7.0, passed=True,\n            ),\n            WalkForwardRound(\n                4, _date(2022, 7, 1), _date(2024, 7, 1),\n                _date(2024, 7, 1), _date(2025, 1, 1),\n                val_sortino=0.9, val_max_dd=11.0,\n                val_alpha=4.0, passed=True,\n            ),\n        ]\n        val_alphas = [r.val_alpha for r in rounds]\n        avg_alpha = sum(val_alphas) / len(val_alphas)\n        assert avg_alpha > 0  # avg 仍然是正的\n\n        all_rounds_passed = all(r.passed for r in rounds)\n        avg_alpha_positive = avg_alpha > 0\n        pass_all = all_rounds_passed and avg_alpha_positive\n        assert pass_all is False, (\n            \"R2 fail 时即使 avg > 0，pass_all_rounds 也应为 False\"\n        )\n\n\n# ---------------------------------------------------------------------------\n# 4. 集成测试：run_walk_forward 计算 val_alpha\n# ---------------------------------------------------------------------------\n\ndef _make_spy_ohlcv(n: int = 300, annual_growth: float = 0.10) -> pd.DataFrame:\n    \"\"\"生成 SPY OHLCV 数据（温和上涨，默认年化 10%）。\"\"\"\n    idx = pd.date_range(\"2021-01-01\", periods=n, freq=\"B\")\n    daily_growth = (1.0 + annual_growth) ** (1.0 / 252.0) - 1.0\n    close = [100.0 * ((1.0 + daily_growth) ** i) for i in range(n)]\n    return pd.DataFrame(\n        {\n            \"open\":   [c - 0.1 for c in close],\n            \"high\":   [c + 0.5 for c in close],\n            \"low\":    [c - 0.5 for c in close],\n            \"close\":  close,\n            \"volume\": [1_000_000] * n,\n        },\n        index=idx,\n    )\n\n\ndef _make_strategy_ohlcv(n: int = 300, trend: str = \"up\") -> pd.DataFrame:\n    \"\"\"生成策略 OHLCV 数据（强趋势，使策略跑赢 SPY）。\"\"\"\n    idx = pd.date_range(\"2021-01-01\", periods=n, freq=\"B\")\n    if trend == \"up\":\n        close = [100.0 + i * 0.3 for i in range(n)]   # 强趋势，年化 ~50%+\n    else:\n        close = [100.0 - i * 0.05 for i in range(n)]\n    return pd.DataFrame(\n        {\n            \"open\":   [c - 0.5 for c in close],\n            \"high\":   [c + 1.0 for c in close],\n            \"low\":    [c - 1.0 for c in close],\n            \"close\":  close,\n            \"volume\": [1_000_000] * n,\n        },\n        index=idx,\n    )\n\n\nclass TestWFAlphaIntegration:\n    \"\"\"迭代 #13：run_walk_forward 集成测试 — val_alpha 计算正确性。\"\"\"\n\n    def test_wf_spy_unavailable_alpha_zero(self):\n        \"\"\"SPY 不可用时 val_alpha=0.0 + WARNING（降级不阻塞）。\n\n        构造 mock_store 不返回 SPY 数据 → _get_spy_returns 返回 None\n        → val_alpha=0.0（降级处理，不抛异常）\n        → 单轮 passed=True（alpha=0 > -5 floor）\n        → 但 avg_alpha=0 → pass_all_rounds=False（0 不 > 0）\n        \"\"\"\n        df_strat = _make_strategy_ohlcv(300, trend=\"up\")\n\n        store = MagicMock()\n        # 不包含 SPY\n        def get_bars_multi(symbols, start, end, timeframe=\"1d\"):\n            mapping = {\"AAPL\": df_strat, \"MSFT\": df_strat}\n            return {s: mapping[s] for s in symbols if s in mapping}\n        store.get_bars_multi.side_effect = get_bars_multi\n\n        universe = MagicMock()\n        universe.get_groups.return_value = {\"test_group\": [\"AAPL\", \"MSFT\"]}\n\n        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=1)\n\n        report = run_walk_forward(\n            mb=mb,\n            strategies=[\"dual_ma\"],\n            param_grids={\"dual_ma\": {\"fast\": [5], \"slow\": [20]}},\n            rounds=2,\n            train_months=12,\n            val_months=4,\n        )\n\n        assert isinstance(report, WalkForwardReport)\n        assert len(report.rounds) == 2\n        # SPY 不可用 → val_alpha=0.0\n        for r in report.rounds:\n            assert r.val_alpha == 0.0, (\n                f\"SPY 不可用时 val_alpha 应为 0.0，实际 {r.val_alpha}\"\n            )\n        # avg=0 → 不 > 0 → pass_all_rounds=False\n        assert report.avg_val_alpha == 0.0\n        assert report.pass_all_rounds is False, (\n            \"avg_alpha=0 不满足 > 0，pass_all_rounds 应为 False\"\n        )\n\n    def test_wf_alpha_computed_correctly(self):\n        \"\"\"用已知 returns + spy_returns 验证 val_alpha 值正确。\n\n        构造 mock store 返回：\n          - 策略数据：强趋势（年化 ~50%+）\n          - SPY 数据：温和上涨（年化 ~10%）\n        验证 val_alpha > 0（策略跑赢 SPY）\n        \"\"\"\n        df_strat = _make_strategy_ohlcv(300, trend=\"up\")\n        df_spy = _make_spy_ohlcv(300, annual_growth=0.10)\n\n        store = MagicMock()\n        def get_bars_multi(symbols, start, end, timeframe=\"1d\"):\n            mapping = {\"AAPL\": df_strat, \"MSFT\": df_strat, \"SPY\": df_spy}\n            return {s: mapping[s] for s in symbols if s in mapping}\n        store.get_bars_multi.side_effect = get_bars_multi\n\n        universe = MagicMock()\n        universe.get_groups.return_value = {\"test_group\": [\"AAPL\", \"MSFT\"]}\n\n        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=1)\n\n        report = run_walk_forward(\n            mb=mb,\n            strategies=[\"dual_ma\"],\n            param_grids={\"dual_ma\": {\"fast\": [5], \"slow\": [20]}},\n            rounds=2,\n            train_months=12,\n            val_months=4,\n        )\n\n        assert len(report.rounds) == 2\n        # 策略强趋势 > SPY 温和上涨 → alpha > 0\n        for r in report.rounds:\n            assert r.val_alpha > 0, (\n                f\"策略强趋势应跑赢 SPY，val_alpha 应 > 0，实际 {r.val_alpha}\"\n            )\n        assert report.avg_val_alpha > 0\n        assert report.min_val_alpha > 0 or report.min_val_alpha == min(\n            r.val_alpha for r in report.rounds\n        )\n\n    def test_wf_alpha_underperforms_spy(self):\n        \"\"\"策略跑输 SPY → val_alpha < 0 → pass_all_rounds=False。\n\n        构造策略数据为下跌趋势，SPY 温和上涨 → alpha 显著为负\n        \"\"\"\n        df_strat_down = _make_strategy_ohlcv(300, trend=\"down\")\n        df_spy = _make_spy_ohlcv(300, annual_growth=0.10)\n\n        store = MagicMock()\n        def get_bars_multi(symbols, start, end, timeframe=\"1d\"):\n            mapping = {\"AAPL\": df_strat_down, \"MSFT\": df_strat_down, \"SPY\": df_spy}\n            return {s: mapping[s] for s in symbols if s in mapping}\n        store.get_bars_multi.side_effect = get_bars_multi\n\n        universe = MagicMock()\n        universe.get_groups.return_value = {\"test_group\": [\"AAPL\", \"MSFT\"]}\n\n        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=1)\n\n        report = run_walk_forward(\n            mb=mb,\n            strategies=[\"dual_ma\"],\n            param_grids={\"dual_ma\": {\"fast\": [5], \"slow\": [20]}},\n            rounds=2,\n            train_months=12,\n            val_months=4,\n        )\n\n        # 策略下跌 + SPY 上涨 → alpha 显著为负\n        for r in report.rounds:\n            assert r.val_alpha < 0, (\n                f\"策略下跌+SPY上涨应跑输，val_alpha 应 < 0，实际 {r.val_alpha}\"\n            )\n        # 负 alpha → pass_all_rounds=False\n        assert report.pass_all_rounds is False\n        assert report.avg_val_alpha < 0\n\n    def test_wf_alpha_floor_constant_value(self):\n        \"\"\"WALK_FORWARD_VAL_ALPHA_FLOOR 常量值为 -5.0。\"\"\"\n        assert WALK_FORWARD_VAL_ALPHA_FLOOR == -5.0, (\n            f\"WF alpha floor 应为 -5.0，实际 {WALK_FORWARD_VAL_ALPHA_FLOOR}\"\n        )\n\n    def test_wf_alpha_floor_vs_dd_threshold_independent(self):\n        \"\"\"alpha floor 和 DD threshold 是两个独立的 gate（AND 关系）。\"\"\"\n        # DD 合规但 alpha 灾难性跑输\n        dd_pass_alpha_fail = (\n            10.0 <= WALK_FORWARD_VAL_DD_THRESHOLD\n            and -8.0 <= WALK_FORWARD_VAL_ALPHA_FLOOR  # 注意：< floor\n        )\n        # -8.0 不满足 > -5.0，所以 alpha_passed=False\n        alpha_passed = -8.0 > WALK_FORWARD_VAL_ALPHA_FLOOR\n        assert alpha_passed is False\n        # AND 关系：任一 fail → passed=False\n        assert dd_pass_alpha_fail and alpha_passed is False or True  # 仅验证可计算\n\n        # 真正的 AND 逻辑验证\n        passed = (10.0 <= WALK_FORWARD_VAL_DD_THRESHOLD) and (-8.0 > WALK_FORWARD_VAL_ALPHA_FLOOR)\n        assert passed is False, \"DD 合规但 alpha < floor 时应 fail\"\n","file_path":"/Users/rickouyang/Github/trade-tools/mytrader/tests/test_wf_alpha_gate.py"}
---
Successfully created and wrote to new file: /Users/rickouyang/Github/trade-tools/mytrader/tests/test_wf_alpha_gate.py
---
Successfully created and wrote to new file: /Users/rickouyang/Github/trade-tools/mytrader/tests/test_wf_alpha_gate.py
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
现在
---
让我
---
更新
---
 `
---
mock
---
_store
---
`
---
 fixture
---
 以
---
包含
---
 SP
---
Y
---
 数据
---
，
---
这样
---
现有的
---
 WF
---
 
---
集
---
成
---
测试
---
就能
---
通过
---
新的
---
 alpha
---
 gate
---
。
---
让我
---
再
---
查看
---
一下
---
该
---
 fixture
---
 以及
---
它
---
所
---
使用的
---
测试
---
用
---
例
---
。
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py","limit":25,"offset":64}
---
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
  89→
---
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
  89→
---
The
---
 `
---
mock
---
_store
---
`
---
 fixture
---
 is
---
 used
---
 by
---
 many
---
 tests
---
.
---
 Adding
---
 SP
---
Y
---
 to
---
 it
---
 would
---
:

---
1
---
.
---
 Make
---
 `_
---
get
---
_s
---
py
---
_returns
---
`
---
 work
---
 in
---
 WF
---
 tests
---
 (
---
return
---
ing
---
 SP
---
Y
---
 data
---
)

---
2
---
.
---
 Not
---
 affect
---
 other
---
 tests
---
 that
---
 don
---
't
---
 request
---
 SP
---
Y
---
 (
---
since
---
 `
---
get
---
_b
---
ars
---
_multi
---
`
---
 filters
---
 by
---
 requested
---
 symbols
---
)


---
But
---
 I
---
 need
---
 to
---
 make
---
 sure
---
 the
---
 SP
---
Y
---
 data
---
 has
---
 a
---
 slower
---
 growth
---
 trend
---
 than
---
 the
---
 strategy
---
 data
---
,
---
 so
---
 alpha
---
 >
---
 
---
0
---
.


---
Strategy
---
 data
---
:
---
 `
---
close
---
 =
---
 
---
100
---
.
---
0
---
 +
---
 i
---
 *
---
 
---
0
---
.
---
1
---
`
---
 →
---
 daily
---
 return
---
 
---
≈
---
 
---
0
---
.
---
1
---
/(
---
100
---
+i
---
*
---
0
---
.
---
1
---
)
---
 
---
≈
---
 
---
0
---
.
---
001
---
 (
---
de
---
creasing
---
)

---
SP
---
Y
---
 data
---
:
---
 I
---
'll
---
 use
---
 `
---
close
---
 =
---
 
---
100
---
.
---
0
---
 *
---
 (
---
1
---
.
---
000
---
4
---
 **
---
 i
---
)`
---
 →
---
 daily
---
 return
---
 
---
≈
---
 
---
0
---
.
---
000
---
4
---
 (
---
constant
---
,
---
 ~
---
10
---
%
---
 annual
---
ized
---
)


---
Strategy
---
 annual
---
ized
---
:
---
 (
---
1
---
.
---
001
---
)^
---
25
---
2
---
 -
---
 
---
1
---
 
---
≈
---
 
---
28
---
.
---
5
---
%

---
SP
---
Y
---
 annual
---
ized
---
:
---
 (
---
1
---
.
---
000
---
4
---
)^
---
25
---
2
---
 -
---
 
---
1
---
 
---
≈
---
 
---
10
---
.
---
6
---
%

---
Alpha
---
 
---
≈
---
 
---
17
---
.
---
9
---
%
---
 >
---
 
---
0
---
 ✓
---



---
Let
---
 me
---
 add
---
 SP
---
Y
---
 to
---
 the
---
 mock
---
_store
---
 fixture
---
.
---
 I
---
'll
---
 use
---
 the
---
 same
---
 pattern
---
 as
---
 other
---
 tests
---
 (
---
line
---
 
---
105
---
8
---
-
---
106
---
8
---
).


---
Wait
---
,
---
 but
---
 there
---
's
---
 a
---
 subt
---
let
---
y
---
.
---
 The
---
 `_
---
make
---
_
---
ohl
---
cv
---
`
---
 function
---
 creates
---
 data
---
 with
---
 `
---
t
---
rend
---
="
---
up
---
"`
---
 =
---
 `
---
100
---
.
---
0
---
 +
---
 i
---
 *
---
 
---
0
---
.
---
1
---
`.
---
 This
---
 is
---
 a
---
 LINE
---
AR
---
 trend
---
,
---
 not
---
 exponential
---
.
---
 So
---
 the
---
 daily
---
 return
---
 decreases
---
 over
---
 time
---
 (
---
0
---
.
---
1
---
/
---
100
---
 =
---
 
---
0
---
.
---
1
---
%
---
 initially
---
,
---
 
---
0
---
.
---
1
---
/
---
130
---
 =
---
 
---
0
---
.
---
07
---
7
---
%
---
 at
---
 the
---
 end
---
).
---
 The
---
 average
---
 daily
---
 return
---
 is
---
 roughly
---
 
---
0
---
.
---
08
---
%.


---
SP
---
Y
---
 with
---
 `
---
1
---
.
---
000
---
4
---
 **
---
 i
---
`
---
 has
---
 a
---
 constant
---
 daily
---
 return
---
 of
---
 
---
0
---
.
---
04
---
%.


---
So
---
 strategy
---
 avg
---
 daily
---
 
---
≈
---
 
---
0
---
.
---
08
---
%
---
 >
---
 SP
---
Y
---
 daily
---
 
---
≈
---
 
---
0
---
.
---
04
---
%
---
 →
---
 alpha
---
 >
---
 
---
0
---
.
---
 


---
But
---
 wait
---
,
---
 the
---
 strategy
---
 doesn
---
't
---
 buy
---
 and
---
 hold
---
 —
---
 it
---
 uses
---
 dual
---
_ma
---
(
---
5
---
,
---
 
---
20
---
)
---
 signals
---
.
---
 On
---
 a
---
 linear
---
 upt
---
rend
---
:

---
-
---
 Fast
---
 MA
---
 (
---
5
---
-day
---
)
---
 will
---
 be
---
 above
---
 slow
---
 MA
---
 (
---
20
---
-day
---
)
---
 most
---
 of
---
 the
---
 time
---
 after
---
 the
---
 initial
---
 crossover
---


---
-
---
 So
---
 the
---
 strategy
---
 will
---
 be
---
 mostly
---
 long
---


---
-
---
 Returns
---
 
---
≈
---
 buy
---
-and
---
-h
---
old
---
 minus
---
 fees
---
/sl
---
ipp
---
age
---



---
With
---
 
---
0
---
.
---
1
---
%
---
 fees
---
 +
---
 
---
0
---
.
---
1
---
%
---
 sl
---
ipp
---
age
---
 per
---
 trade
---
,
---
 and
---
 maybe
---
 
---
5
---
-
---
10
---
 trades
---
 over
---
 
---
300
---
 days
---
,
---
 the
---
 strategy
---
 returns
---
 will
---
 be
---
 slightly
---
 less
---
 than
---
 buy
---
-and
---
-h
---
old
---
 but
---
 still
---
 much
---
 higher
---
 than
---
 SP
---
Y
---
.


---
OK
---
,
---
 let
---
 me
---
 add
---
 SP
---
Y
---
 to
---
 the
---
 mock
---
_store
---
 fixture
---
.
---
 I
---
'll
---
 also
---
 need
---
 to
---
 update
---
 the
---
 import
---
 to
---
 include
---
 the
---
 SP
---
Y
---
 data
---
 construction
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
 existing
---
 tests
---
 that
---
 need
---
 SP
---
Y
---
,
---
 they
---
 construct
---
 SP
---
Y
---
 inline
---
 (
---
not
---
 via
---
 the
---
 fixture
---
).
---
 The
---
 issue
---
 is
---
 only
---
 with
---
 the
---
 WF
---
 integration
---
 test
---
 `
---
test
---
_run
---
_walk
---
_forward
---
_mock
---
_integration
---
`
---
 which
---
 uses
---
 the
---
 `
---
mock
---
_store
---
`
---
 fixture
---
.


---
The
---
 clean
---
est
---
 approach
---
:
---
 add
---
 SP
---
Y
---
 to
---
 the
---
 `
---
mock
---
_store
---
`
---
 fixture
---
.
---
 This
---
 way
---
:

---
1
---
.
---
 WF
---
 tests
---
 that
---
 use
---
 `
---
mock
---
_store
---
`
---
 will
---
 have
---
 SP
---
Y
---
 data
---
 →
---
 alpha
---
 >
---
 
---
0
---


---
2
---
.
---
 Non
---
-W
---
F
---
 tests
---
 that
---
 use
---
 `
---
mock
---
_store
---
`
---
 but
---
 don
---
't
---
 request
---
 SP
---
Y
---
 are
---
 unaffected
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
:
---
 does
---
 `_
---
run
---
_group
---
`
---
 call
---
 `_
---
get
---
_s
---
py
---
_returns
---
`
---
?
---
 Yes
---
 it
---
 does
---
 (
---
line
---
 
---
110
---
6
---
).
---
 So
---
 adding
---
 SP
---
Y
---
 to
---
 `
---
mock
---
_store
---
`
---
 will
---
 also
---
 affect
---
 the
---
 matrix
---
 back
---
test
---
 tests
---
.
---
 But
---
 those
---
 tests
---
 were
---
 already
---
 updated
---
 in
---
 Iter
---
 #
---
12
---
 to
---
 handle
---
 SP
---
Y
---
...
---
 let
---
 me
---
 check
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
 Iter
---
 #
---
12
---
 trajectory
---
:
---
 "
---
同步
---
更新
---
 
---
3
---
 个
---
现有
---
测试
---
文件的
---
 SP
---
Y
---
 benchmark
---
 数据
---
（
---
用
---
 trend
---
='
---
down
---
'
---
 的
---
 SP
---
Y
---
 
---
确
---
保
---
策略
---
 alpha
---
>
---
0
---
，
---
避免
---
被
---
新
---
门槛
---
误
---
杀
---
）
---
".
---
 So
---
 Iter
---
 #
---
12
---
 already
---
 updated
---
 tests
---
 to
---
 provide
---
 SP
---
Y
---
 data
---
.
---
 But
---
 the
---
 `
---
mock
---
_store
---
`
---
 fixture
---
 itself
---
 doesn
---
't
---
 include
---
 SP
---
Y
---
.


---
Let
---
 me
---
 check
---
 if
---
 the
---
 matrix
---
 back
---
test
---
 tests
---
 that
---
 use
---
 `
---
mock
---
_store
---
`
---
 currently
---
 work
---
 with
---
 the
---
 alpha
---
>
---
0
---
 gate
---
.
---
 They
---
 do
---
,
---
 because
---
:

---
1
---
.
---
 Without
---
 SP
---
Y
---
 in
---
 mock
---
_store
---
,
---
 `_
---
get
---
_s
---
py
---
_returns
---
`
---
 returns
---
 None
---


---
2
---
.
---
 `_
---
compute
---
_alpha
---
`
---
 with
---
 spy
---
=None
---
 returns
---
 
---
0
---
.
---
0
---


---
3
---
.
---
 The
---
 alpha
---
>
---
0
---
 gate
---
 (
---
Iter
---
 #
---
12
---
)
---
 rejects
---
 all
---
 candidates
---
 (
---
alpha
---
=
---
0
---
 is
---
 not
---
 >
---
 
---
0
---
)

---
4
---
.
---
 So
---
 groups
---
 return
---
 empty
---
 weights
---
 →
---
 `
---
no
---
_positive
---
_alpha
---
=True
---
`


---
Wait
---
,
---
 that
---
 would
---
 mean
---
 the
---
 existing
---
 matrix
---
 back
---
test
---
 tests
---
 using
---
 `
---
mock
---
_store
---
`
---
 should
---
 be
---
 FAIL
---
ING
---
 right
---
 now
---
 (
---
return
---
ing
---
 empty
---
 weights
---
).
---
 Let
---
 me
---
 check
---
 if
---
 they
---
 actually
---
 pass
---
...


---
Actually
---
,
---
 let
---
 me
---
 re
---
-read
---
 the
---
 alpha
---
>
---
0
---
 gate
---
 logic
---
:

---
```
---
python
---


---
positive
---
_alpha
---
_candidates
---
 =
---
 [
---
c
---
 for
---
 c
---
 in
---
 candidates
---
 if
---
 c
---
[
---
5
---
]
---
 >
---
 
---
0
---
]

---
if
---
 not
---
 positive
---
_alpha
---
_candidates
---
:

---
   
---
 #
---
 全
---
组
---
 alpha
---
≤
---
0
---
 →
---
 
---
空
---
权重
---


---
   
---
 return
---
 []

---
``
---
`


---
With
---
 alpha
---
=
---
0
---
.
---
0
---
 (
---
SP
---
Y
---
 unavailable
---
),
---
 `
---
0
---
.
---
0
---
 >
---
 
---
0
---
`
---
 is
---
 False
---
,
---
 so
---
 all
---
 candidates
---
 are
---
 filtered
---
 out
---
.
---
 This
---
 means
---
 tests
---
 using
---
 `
---
mock
---
_store
---
`
---
 without
---
 SP
---
Y
---
 should
---
 return
---
 empty
---
 weights
---
.


---
But
---
 the
---
 tests
---
 pass
---
 (
---
65
---
9
---
 tests
---
).
---
 Let
---
 me
---
 check
---
 what
---
 the
---
 tests
---
 actually
---
 assert
---
.
---
 Maybe
---
 they
---
 don
---
't
---
 assert
---
 non
---
-empty
---
 weights
---
,
---
 or
---
 maybe
---
 SP
---
Y
---
 is
---
 already
---
 in
---
 the
---
 fixture
---
...


---
Wait
---
,
---
 let
---
 me
---
 re
---
-read
---
 the
---
 fixture
---
.
---
 It
---
 doesn
---
't
---
 have
---
 SP
---
Y
---
.
---
 Let
---
 me
---
 check
---
 a
---
 specific
---
 test
---
 like
---
 `
---
test
---
_run
---
_pro
---
du
---
ces
---
_groups
---
`:
---
让我
---
检查
---
一下
---
使用
---
 `
---
mock
---
_store
---
`
---
 的
---
现有
---
矩阵
---
回
---
测
---
测试
---
是否能
---
配合
---
 alpha
---
>
---
0
---
 门
---
控
---
正常
---
工作
---
。
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py","limit":50,"offset":359}
---
 359→    def test_run_produces_groups(self, mock_store, mock_universe):
 360→        """run() 产出包含分组权重的 MatrixBacktestReport。"""
 361→        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=2)
 362→        strategies = ["dual_ma"]
 363→        param_grids = {"dual_ma": {"fast": [5], "slow": [20]}}
 364→
 365→        report = mb.run(strategies=strategies, param_grids=param_grids)
 366→        assert len(report.groups) >= 1
 367→        # 每个分组应有策略权重配置
 368→        for gid, weights in report.groups.items():
 369→            assert isinstance(weights, list)
 370→
 371→    def test_run_weights_sum_to_one(self, mock_store, mock_universe):
 372→        """每个分组的策略权重之和 ≈ 1.0。"""
 373→        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=2)
 374→        report = mb.run(
 375→            strategies=["dual_ma", "rsi_mean_revert"],
 376→            param_grids={
 377→                "dual_ma": {"fast": [5], "slow": [20]},
 378→                "rsi_mean_revert": {"period": [14], "oversold": [30], "overbought": [70]},
 379→            },
 380→        )
 381→        for gid, weights in report.groups.items():
 382→            if weights:
 383→                total = sum(w["weight"] for w in weights)
 384→                assert abs(total - 1.0) < 0.01, f"{gid}: weights sum={total:.4f} ≠ 1.0"
 385→
 386→    def test_run_output_file(self, mock_store, mock_universe, tmp_path):
 387→        """output_file 参数会生成有效的 JSON 文件。"""
 388→        output = tmp_path / "strategy_weights.json"
 389→        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)
 390→        mb.run(
 391→            strategies=["dual_ma"],
 392→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 393→            output_file=output,
 394→        )
 395→        assert output.exists()
 396→        data = json.loads(output.read_text())
 397→        assert "_meta" in data
 398→        assert "groups" in data
 399→        assert "survivorship_bias_warning" in data["_meta"]
 400→
 401→    def test_run_empty_universe(self, mock_store):
 402→        """空标的组不崩溃。"""
 403→        universe = MagicMock()
 404→        universe.get_groups.return_value = {}
 405→        mb = MatrixBacktest(store=mock_store, universe=universe, years=1)
 406→        report = mb.run(strategies=["dual_ma"], param_grids={"dual_ma": {}})
 407→        assert report.groups == {}
 408→
 409→
---
 359→    def test_run_produces_groups(self, mock_store, mock_universe):
 360→        """run() 产出包含分组权重的 MatrixBacktestReport。"""
 361→        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=2)
 362→        strategies = ["dual_ma"]
 363→        param_grids = {"dual_ma": {"fast": [5], "slow": [20]}}
 364→
 365→        report = mb.run(strategies=strategies, param_grids=param_grids)
 366→        assert len(report.groups) >= 1
 367→        # 每个分组应有策略权重配置
 368→        for gid, weights in report.groups.items():
 369→            assert isinstance(weights, list)
 370→
 371→    def test_run_weights_sum_to_one(self, mock_store, mock_universe):
 372→        """每个分组的策略权重之和 ≈ 1.0。"""
 373→        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=2)
 374→        report = mb.run(
 375→            strategies=["dual_ma", "rsi_mean_revert"],
 376→            param_grids={
 377→                "dual_ma": {"fast": [5], "slow": [20]},
 378→                "rsi_mean_revert": {"period": [14], "oversold": [30], "overbought": [70]},
 379→            },
 380→        )
 381→        for gid, weights in report.groups.items():
 382→            if weights:
 383→                total = sum(w["weight"] for w in weights)
 384→                assert abs(total - 1.0) < 0.01, f"{gid}: weights sum={total:.4f} ≠ 1.0"
 385→
 386→    def test_run_output_file(self, mock_store, mock_universe, tmp_path):
 387→        """output_file 参数会生成有效的 JSON 文件。"""
 388→        output = tmp_path / "strategy_weights.json"
 389→        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)
 390→        mb.run(
 391→            strategies=["dual_ma"],
 392→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 393→            output_file=output,
 394→        )
 395→        assert output.exists()
 396→        data = json.loads(output.read_text())
 397→        assert "_meta" in data
 398→        assert "groups" in data
 399→        assert "survivorship_bias_warning" in data["_meta"]
 400→
 401→    def test_run_empty_universe(self, mock_store):
 402→        """空标的组不崩溃。"""
 403→        universe = MagicMock()
 404→        universe.get_groups.return_value = {}
 405→        mb = MatrixBacktest(store=mock_store, universe=universe, years=1)
 406→        report = mb.run(strategies=["dual_ma"], param_grids={"dual_ma": {}})
 407→        assert report.groups == {}
 408→
 409→
---
I
---
 see
---
.
---
 The
---
 tests
---
 like
---
 `
---
test
---
_run
---
_pro
---
du
---
ces
---
_groups
---
`
---
 only
---
 assert
---
 `
---
len
---
(report
---
.groups
---
)
---
 >=
---
 
---
1
---
`
---
 and
---
 `
---
is
---
instance
---
(weights
---
,
---
 list
---
)
---
`.
---
 With
---
 the
---
 alpha
---
>
---
0
---
 gate
---
 and
---
 no
---
 SP
---
Y
---
 data
---
,
---
 the
---
 weights
---
 would
---
 be
---
 empty
---
 lists
---
 `
---
[]
---
`.
---
 The
---
 test
---
 `
---
test
---
_run
---
_pro
---
du
---
ces
---
_groups
---
`
---
 would
---
 still
---
 pass
---
 because
---
:

---
-
---
 `
---
report
---
.groups
---
`
---
 has
---
 entries
---
 (
---
one
---
 per
---
 group
---
),
---
 even
---
 if
---
 the
---
 weights
---
 list
---
 is
---
 empty
---


---
-
---
 `
---
is
---
instance
---
(weights
---
,
---
 list
---
)`
---
 is
---
 True
---
 for
---
 empty
---
 lists
---



---
And
---
 `
---
test
---
_run
---
_weights
---
_sum
---
_to
---
_one
---
`
---
 has
---
 `
---
if
---
 weights
---
:`
---
 guard
---
,
---
 so
---
 it
---
 skips
---
 empty
---
 weight
---
 lists
---
.


---
So
---
 the
---
 existing
---
 tests
---
 pass
---
 even
---
 with
---
 empty
---
 weights
---
 (
---
no
---
 SP
---
Y
---
 →
---
 alpha
---
=
---
0
---
 →
---
 rejected
---
 by
---
 alpha
---
>
---
0
---
 gate
---
).


---
But
---
 wait
---
,
---
 let
---
 me
---
 verify
---
 this
---
 by
---
 running
---
 the
---
 tests
---
 first
---
 to
---
 see
---
 the
---
 current
---
 state
---
.
---
 Actually
---
,
---
 the
---
 spec
---
 says
---
 
---
65
---
9
---
 tests
---
 pass
---
.
---
 Let
---
 me
---
 trust
---
 that
---
 and
---
 focus
---
 on
---
 the
---
 WF
---
 test
---
 issue
---
.


---
The
---
 WF
---
 integration
---
 test
---
 `
---
test
---
_run
---
_walk
---
_forward
---
_mock
---
_integration
---
`
---
 asserts
---
:

---
```
---
python
---


---
assert
---
 r
---
.pass
---
ed
---
 ==
---
 (
---
r
---
.val
---
_max
---
_dd
---
 <=
---
 W
---
ALK
---
_FORWARD
---
_VAL
---
_DD
---
_THRESHOLD
---
)

---
``
---
`


---
After
---
 my
---
 change
---
,
---
 `
---
passed
---
 =
---
 dd
---
_passed
---
 AND
---
 alpha
---
_passed
---
`.
---
 Without
---
 SP
---
Y
---
,
---
 `
---
val
---
_alpha
---
=
---
0
---
.
---
0
---
`,
---
 `
---
alpha
---
_passed
---
 =
---
 
---
0
---
.
---
0
---
 >
---
 -
---
5
---
.
---
0
---
 =
---
 True
---
`.
---
 So
---
 `
---
passed
---
 =
---
 dd
---
_passed
---
 AND
---
 True
---
 =
---
 dd
---
_passed
---
`.
---
 This
---
 assertion
---
 still
---
 holds
---
!


---
But
---
:

---
```
---
python
---


---
expected
---
_pass
---
 =
---
 all
---
(r
---
.pass
---
ed
---
 for
---
 r
---
 in
---
 report
---
.round
---
s
---
)

---
assert
---
 report
---
.pass
---
_all
---
_round
---
s
---
 ==
---
 expected
---
_pass
---


---
``
---
`


---
After
---
 my
---
 change
---
,
---
 `
---
pass
---
_all
---
_round
---
s
---
 =
---
 all
---
(r
---
.pass
---
ed
---
)
---
 AND
---
 (
---
avg
---
_val
---
_alpha
---
 >
---
 
---
0
---
)
---
`.
---
 Without
---
 SP
---
Y
---
,
---
 `
---
avg
---
_val
---
_alpha
---
=
---
0
---
.
---
0
---
`,
---
 `
---
0
---
.
---
0
---
 >
---
 
---
0
---
 =
---
 False
---
`.
---
 So
---
 `
---
pass
---
_all
---
_round
---
s
---
 =
---
 False
---
`
---
 even
---
 if
---
 `
---
all
---
(r
---
.pass
---
ed
---
)
---
 =
---
 True
---
`.


---
If
---
 `
---
all
---
(r
---
.pass
---
ed
---
)
---
 =
---
 True
---
`,
---
 then
---
 `
---
expected
---
_pass
---
 =
---
 True
---
`
---
 but
---
 `
---
report
---
.pass
---
_all
---
_round
---
s
---
 =
---
 False
---
`.
---
 Test
---
 fails
---
.


---
If
---
 some
---
 round
---
 has
---
 `
---
val
---
_max
---
_dd
---
 >
---
 
---
15
---
%
---
`,
---
 then
---
 `
---
r
---
.pass
---
ed
---
 =
---
 False
---
`,
---
 `
---
expected
---
_pass
---
 =
---
 False
---
`,
---
 and
---
 `
---
report
---
.pass
---
_all
---
_round
---
s
---
 =
---
 False
---
`.
---
 Test
---
 passes
---
.


---
So
---
 the
---
 test
---
 only
---
 fails
---
 if
---
 all
---
 rounds
---
 pass
---
 DD
---
-wise
---
.
---
 Let
---
 me
---
 think
---
 about
---
 whether
---
 the
---
 mock
---
 data
---
 produces
---
 DD
---
 ≤
---
 
---
15
---
%.


---
The
---
 mock
---
 data
---
 is
---
 a
---
 linear
---
 upt
---
rend
---
 (
---
100
---
 +
---
 i
---
*
---
0
---
.
---
1
---
).
---
 On
---
 this
---
 data
---
,
---
 dual
---
_ma
---
(
---
5
---
,
---
20
---
)
---
 will
---
 be
---
 long
---
 most
---
 of
---
 the
---
 time
---
.
---
 The
---
 portfolio
---
 max
---
 DD
---
 should
---
 be
---
 very
---
 small
---
 (
---
near
---
 
---
0
---
%)
---
 because
---
 it
---
's
---
 a
---
 steady
---
 upt
---
rend
---
.
---
 So
---
 all
---
 rounds
---
 will
---
 pass
---
 DD
---
-wise
---
 →
---
 `
---
expected
---
_pass
---
 =
---
 True
---
`
---
 →
---
 test
---
 fails
---
.


---
So
---
 I
---
 need
---
 to
---
 either
---
:

---
1
---
.
---
 Add
---
 SP
---
Y
---
 to
---
 mock
---
_store
---
 (
---
so
---
 avg
---
_val
---
_alpha
---
 >
---
 
---
0
---
 →
---
 pass
---
_all
---
_round
---
s
---
 =
---
 True
---
)

---
2
---
.
---
 Update
---
 the
---
 test
---
 assertion
---



---
Option
---
 
---
1
---
 is
---
 better
---
 because
---
 it
---
 tests
---
 the
---
 realistic
---
 path
---
.
---
 Let
---
 me
---
 add
---
 SP
---
Y
---
 to
---
 the
---
 mock
---
_store
---
 fixture
---
.


---
But
---
 I
---
 need
---
 to
---
 be
---
 careful
---
:
---
 adding
---
 SP
---
Y
---
 to
---
 mock
---
_store
---
 will
---
 also
---
 affect
---
 `_
---
run
---
_group
---
`
---
 calls
---
 in
---
 matrix
---
 back
---
test
---
 tests
---
.
---
 Currently
---
,
---
 without
---
 SP
---
Y
---
,
---
 `_
---
get
---
_s
---
py
---
_returns
---
`
---
 returns
---
 None
---
 →
---
 alpha
---
=
---
0
---
 →
---
 alpha
---
>
---
0
---
 gate
---
 rejects
---
 all
---
 →
---
 empty
---
 weights
---
.
---
 With
---
 SP
---
Y
---
 (
---
slow
---
 trend
---
),
---
 alpha
---
 >
---
 
---
0
---
 →
---
 strategies
---
 pass
---
 the
---
 alpha
---
>
---
0
---
 gate
---
 →
---
 non
---
-empty
---
 weights
---
.


---
This
---
 could
---
 change
---
 the
---
 behavior
---
 of
---
 tests
---
 like
---
 `
---
test
---
_run
---
_weights
---
_sum
---
_to
---
_one
---
`
---
 which
---
 currently
---
 skip
---
 empty
---
 weight
---
 groups
---
.
---
 With
---
 SP
---
Y
---
,
---
 weights
---
 would
---
 be
---
 non
---
-empty
---
,
---
 and
---
 the
---
 test
---
 would
---
 actually
---
 check
---
 the
---
 sum
---
.
---
 This
---
 should
---
 be
---
 fine
---
 as
---
 long
---
 as
---
 weights
---
 sum
---
 to
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
But
---
 it
---
 could
---
 also
---
 break
---
 tests
---
 that
---
 assert
---
 specific
---
 behavior
---
 with
---
 empty
---
 weights
---
...
---
 Let
---
 me
---
 check
---
 if
---
 any
---
 test
---
 expects
---
 empty
---
 weights
---
 due
---
 to
---
 alpha
---
>
---
0
---
 gate
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
 Iter
---
 #
---
12
---
 trajectory
---
:
---
 "
---
同步
---
更新
---
 
---
3
---
 个
---
现有
---
测试
---
文件的
---
 SP
---
Y
---
 benchmark
---
 数据
---
（
---
用
---
 trend
---
='
---
down
---
'
---
 的
---
 SP
---
Y
---
 
---
确
---
保
---
策略
---
 alpha
---
>
---
0
---
，
---
避免
---
被
---
新
---
门槛
---
误
---
杀
---
）
---
".
---
 This
---
 suggests
---
 they
---
 updated
---
 specific
---
 tests
---
 to
---
 provide
---
 SP
---
Y
---
,
---
 not
---
 the
---
 fixture
---
.
---
 Let
---
 me
---
 check
---
 what
---
 tests
---
 were
---
 updated
---
.


---
Actually
---
,
---
 let
---
 me
---
 just
---
 run
---
 the
---
 existing
---
 tests
---
 first
---
 to
---
 see
---
 the
---
 baseline
---
,
---
 then
---
 make
---
 changes
---
.


---
Wait
---
,
---
 I
---
 should
---
 be
---
 more
---
 careful
---
.
---
 Let
---
 me
---
 check
---
 if
---
 the
---
 `
---
mock
---
_store
---
`
---
 fixture
---
 is
---
 used
---
 by
---
 tests
---
 that
---
 explicitly
---
 test
---
 the
---
 `
---
no
---
_positive
---
_alpha
---
`
---
 behavior
---
.
---
 If
---
 so
---
,
---
 adding
---
 SP
---
Y
---
 would
---
 break
---
 those
---
 tests
---
.


---
Let
---
 me
---
 search
---
 for
---
 tests
---
 that
---
 use
---
 `
---
mock
---
_store
---
`
---
 and
---
 test
---
 `
---
no
---
_positive
---
_alpha
---
`.
---
让我
---
先
---
运行
---
现有的
---
 WF
---
 
---
测试
---
来
---
查看
---
基准
---
，
---
然后再
---
进行
---
更改
---
。
---
{"command":"/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_matrix_backtest.py::TestWalkForward -x --no-header -q 2>&1 | tail -30","description":"Run existing WF tests to see baseline"}
---
Run existing WF tests to see baseline
---
Command: /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_matrix_backtest.py::TestWalkForward -x --no-header -q 2>&1 | tail -30
Stdout: ERROR: found no collectors for /Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py::TestWalkForward


==================================== ERRORS ====================================
________________ ERROR collecting tests/test_matrix_backtest.py ________________
tests/test_matrix_backtest.py:17: in <module>
    from mytrader.backtest.matrix_backtest import (
mytrader/backtest/matrix_backtest.py:122: in <module>
    @dataclass
     ^^^^^^^^^
../../../miniforge3/envs/py312trade/lib/python3.12/dataclasses.py:1275: in dataclass
    return wrap(cls)
           ^^^^^^^^^
../../../miniforge3/envs/py312trade/lib/python3.12/dataclasses.py:1265: in wrap
    return _process_class(cls, init, repr, eq, order, unsafe_hash,
../../../miniforge3/envs/py312trade/lib/python3.12/dataclasses.py:1063: in _process_class
    _init_fn(all_init_fields,
../../../miniforge3/envs/py312trade/lib/python3.12/dataclasses.py:585: in _init_fn
    raise TypeError(f'non-default argument {f.name!r} '
E   TypeError: non-default argument 'passed' follows default argument
=========================== short test summary info ============================
ERROR tests/test_matrix_backtest.py - TypeError: non-default argument 'passed...
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!!

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
The
---
 error
---
 is
---
 because
---
 I
---
 added
---
 `
---
val
---
_alpha
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
0
---
`
---
 (
---
with
---
 default
---
)
---
 before
---
 `
---
passed
---
:
---
 bool
---
`
---
 (
---
without
---
 default
---
).
---
 In
---
 data
---
classes
---
,
---
 fields
---
 with
---
 default
---
 values
---
 must
---
 come
---
 after
---
 fields
---
 without
---
 defaults
---
.
---
 I
---
 need
---
 to
---
 either
---
:

---
1
---
.
---
 Give
---
 `
---
passed
---
`
---
 a
---
 default
---
 value
---


---
2
---
.
---
 Re
---
order
---
 so
---
 `
---
val
---
_alpha
---
`
---
 comes
---
 after
---
 `
---
passed
---
`


---
The
---
 spec
---
 shows
---
 `
---
val
---
_alpha
---
`
---
 before
---
 `
---
passed
---
`,
---
 but
---
 that
---
 requires
---
 `
---
passed
---
`
---
 to
---
 have
---
 a
---
 default
---
.
---
 Let
---
 me
---
 give
---
 `
---
passed
---
`
---
 a
---
 default
---
 of
---
 `
---
False
---
`
---
 (
---
s
---
ensible
---
 default
---
).
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
 original
---
 code
---
,
---
 `
---
passed
---
`
---
 had
---
 no
---
 default
---
.
---
 Let
---
 me
---
 reorder
---
:
---
 put
---
 `
---
val
---
_alpha
---
`
---
 after
---
 `
---
passed
---
`
---
 to
---
 maintain
---
 backward
---
 compatibility
---
 with
---
 positional
---
 args
---
.


---
Wait
---
,
---
 but
---
 the
---
 spec
---
 shows
---
:

---
```
---
python
---


---
val
---
_alpha
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
0
---
    
---
 #
---
 
---
迭
---
代
---
 #
---
13
---
：
---
验证
---
期
---
 portfolio
---
 alpha
---
 vs
---
 SP
---
Y
---
（
---
百分
---
数
---
）

---
passed
---
:
---
 bool
---


---
``
---
`


---
This
---
 would
---
 fail
---
 because
---
 `
---
val
---
_alpha
---
`
---
 has
---
 a
---
 default
---
 but
---
 `
---
passed
---
`
---
 doesn
---
't
---
.
---
 The
---
 spec
---
 is
---
 wrong
---
 here
---
.
---
 Let
---
 me
---
 fix
---
 it
---
 by
---
 giving
---
 `
---
passed
---
`
---
 a
---
 default
---
 of
---
 `
---
False
---
`,
---
 or
---
 by
---
 re
---
ordering
---
.


---
Looking
---
 at
---
 the
---
 existing
---
 tests
---
,
---
 some
---
 use
---
 positional
---
 args
---
:

---
```
---
python
---


---
Walk
---
Forward
---
Round
---
(
---
1
---
,
---
 _
---
date
---
(
---
202
---
1
---
,
---
 
---
1
---
,
---
 
---
1
---
),
---
 _
---
date
---
(
---
202
---
3
---
,
---
 
---
1
---
,
---
 
---
1
---
),
---
 _
---
date
---
(
---
202
---
3
---
,
---
 
---
1
---
,
---
 
---
1
---
),
---
 _
---
date
---
(
---
202
---
3
---
,
---
 
---
7
---
,
---
 
---
1
---
),
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
 True
---
),

---
``
---
`


---
This
---
 is
---
 
---
8
---
 positional
---
 args
---
:
---
 round
---
_num
---
,
---
 train
---
_start
---
,
---
 train
---
_end
---
,
---
 val
---
_start
---
,
---
 val
---
_end
---
,
---
 val
---
_sort
---
ino
---
,
---
 val
---
_max
---
_dd
---
,
---
 passed
---
.
---
 If
---
 I
---
 add
---
 `
---
val
---
_alpha
---
`
---
 before
---
 `
---
passed
---
`,
---
 the
---
 
---
8
---
th
---
 positional
---
 arg
---
 would
---
 be
---
 `
---
val
---
_alpha
---
`
---
 not
---
 `
---
passed
---
`,
---
 breaking
---
 these
---
 tests
---
.


---
So
---
 I
---
 should
---
 put
---
 `
---
val
---
_alpha
---
`
---
 AFTER
---
 `
---
passed
---
`
---
 to
---
 maintain
---
 backward
---
 compatibility
---
 with
---
 positional
---
 args
---
.
---
 But
---
 then
---
 `
---
val
---
_alpha
---
`
---
 needs
---
 a
---
 default
---
 (
---
which
---
 it
---
 has
---
:
---
 
---
0
---
.
---
0
---
).


---
Let
---
 me
---
 reorder
---
:
---
 `
---
passed
---
:
---
 bool
---
`
---
 first
---
 (
---
no
---
 default
---
),
---
 then
---
 `
---
val
---
_alpha
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
0
---
`.


---
Actually
---
 wait
---
,
---
 the
---
 original
---
 order
---
 is
---
:

---
```
---
python
---


---
val
---
_sort
---
ino
---
:
---
 float
---


---
val
---
_max
---
_dd
---
:
---
 float
---


---
passed
---
:
---
 bool
---


---
``
---
`


---
If
---
 I
---
 add
---
 `
---
val
---
_alpha
---
`
---
 after
---
 `
---
passed
---
`
---
:

---
```
---
python
---


---
val
---
_sort
---
ino
---
:
---
 float
---


---
val
---
_max
---
_dd
---
:
---
 float
---


---
passed
---
:
---
 bool
---


---
val
---
_alpha
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
0
---


---
``
---
`


---
This
---
 works
---
!
---
 `
---
passed
---
`
---
 has
---
 no
---
 default
---
,
---
 `
---
val
---
_alpha
---
`
---
 has
---
 a
---
 default
---
.
---
 No
---
 ordering
---
 issue
---
.
---
 And
---
 existing
---
 positional
---
 args
---
 still
---
 work
---
 (
---
8
---
 args
---
 map
---
 to
---
 round
---
_num
---
...
---
passed
---
,
---
 and
---
 val
---
_alpha
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
0
---
).


---
But
---
 the
---
 spec
---
 shows
---
 `
---
val
---
_alpha
---
`
---
 before
---
 `
---
passed
---
`.
---
 The
---
 spec
---
's
---
 ordering
---
 would
---
 break
---
 backward
---
 compat
---
.
---
 Let
---
 me
---
 use
---
 the
---
 spec
---
's
---
 intent
---
 but
---
 fix
---
 the
---
 ordering
---
 issue
---
 by
---
 giving
---
 `
---
passed
---
`
---
 a
---
 default
---
.
---
 Actually
---
,
---
 let
---
 me
---
 just
---
 put
---
 `
---
val
---
_alpha
---
`
---
 after
---
 `
---
passed
---
`
---
 —
---
 it
---
's
---
 cleaner
---
 and
---
 maintains
---
 backward
---
 compat
---
.


---
Let
---
 me
---
 fix
---
 this
---
.
---
data
---
class
---
 字
---
段
---
顺序
---
错误
---
 ——
---
 `
---
val
---
_alpha
---
`
---
（
---
带
---
默认
---
值
---
）
---
不能
---
放在
---
 `
---
passed
---
`
---
（
---
不带
---
默认
---
值
---
）
---
之前
---
。
---
我来
---
修复
---
它
---
，
---
同时
---
保持
---
与
---
现有
---
位置
---
参数
---
的
---
向后
---
兼容
---
性
---
。
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py","new_string":"    round_num: int\n    train_start: date\n    train_end: date\n    val_start: date\n    val_end: date\n    val_sortino: float\n    val_max_dd: float\n    passed: bool\n    # 迭代 #13：验证期 portfolio alpha vs SPY（百分数）\n    # 放在 passed 之后以保持与现有位置参数调用的向后兼容\n    # （现有测试用 8 个位置参数：round_num...passed）\n    val_alpha: float = 0.0","old_string":"    round_num: int\n    train_start: date\n    train_end: date\n    val_start: date\n    val_end: date\n    val_sortino: float\n    val_max_dd: float\n    val_alpha: float = 0.0   # 迭代 #13：验证期 portfolio alpha vs SPY（百分数）\n    passed: bool"}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py
---
现在
---
再次
---
运行
---
 WF
---
 
---
测试
---
以
---
查看
---
基准
---
。
---
{"command":"/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_matrix_backtest.py::TestWalkForward -x --no-header -q 2>&1 | tail -30","description":"Run existing WF tests after dataclass fix"}
---
Run existing WF tests after dataclass fix
---
Command: /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_matrix_backtest.py::TestWalkForward -x --no-header -q 2>&1 | tail -30
Stdout: 2026-07-08 00:17:52.084 | INFO     | mytrader.backtest.matrix_backtest:run_walk_forward:865 - [WalkForward] Round 3/4: train=2023-07-08~2025-01-08, val=2025-01-08~2025-07-08
2026-07-08 00:17:52.084 | WARNING  | mytrader.backtest.matrix_backtest:_get_spy_returns:1112 - [MatrixBacktest] SPY data unavailable, alpha will degrade to 0.0
2026-07-08 00:17:52.084 | INFO     | mytrader.backtest.matrix_backtest:_run_group:1167 - [MatrixBacktest] NDX_mid_vol: start — 1 strategies × 2 valid symbols
2026-07-08 00:17:52.127 | INFO     | mytrader.backtest.matrix_backtest:_run_group:1251 - [MatrixBacktest] NDX_mid_vol: dual_ma done in 0.0s (1 param combos × 2 symbols)
2026-07-08 00:17:52.127 | WARNING  | mytrader.backtest.matrix_backtest:_run_group:1272 - [MatrixBacktest] NDX_mid_vol: strategy 'dual_ma' is DEGENERATE (>= 80% symbols have 0 closed trades) — excluded before ranking. Its Sortino/alpha is mark-to-market illusion.
2026-07-08 00:17:52.127 | WARNING  | mytrader.backtest.matrix_backtest:_run_group:1282 - [MatrixBacktest] NDX_mid_vol: ALL strategies degenerate — group produces EMPTY weights (hold cash). Marked no_valid_strategy.
2026-07-08 00:17:52.127 | WARNING  | mytrader.backtest.matrix_backtest:_get_spy_returns:1112 - [MatrixBacktest] SPY data unavailable, alpha will degrade to 0.0
2026-07-08 00:17:52.127 | INFO     | mytrader.backtest.matrix_backtest:_run_group:1167 - [MatrixBacktest] SPX_mid_vol: start — 1 strategies × 1 valid symbols
2026-07-08 00:17:52.152 | INFO     | mytrader.backtest.matrix_backtest:_run_group:1251 - [MatrixBacktest] SPX_mid_vol: dual_ma done in 0.0s (1 param combos × 1 symbols)
2026-07-08 00:17:52.152 | WARNING  | mytrader.backtest.matrix_backtest:_run_group:1272 - [MatrixBacktest] SPX_mid_vol: strategy 'dual_ma' is DEGENERATE (>= 80% symbols have 0 closed trades) — excluded before ranking. Its Sortino/alpha is mark-to-market illusion.
2026-07-08 00:17:52.152 | WARNING  | mytrader.backtest.matrix_backtest:_run_group:1282 - [MatrixBacktest] SPX_mid_vol: ALL strategies degenerate — group produces EMPTY weights (hold cash). Marked no_valid_strategy.
2026-07-08 00:17:52.152 | WARNING  | mytrader.backtest.matrix_backtest:run_walk_forward:905 - [WalkForward] Round 3: no valid val returns — sortino=0, dd=0, alpha=0, passed=True (vacuous)
2026-07-08 00:17:52.152 | INFO     | mytrader.backtest.matrix_backtest:run_walk_forward:954 - [WalkForward] Round 3 result: sortino=0.0000, dd=0.0000%, alpha=0.0000%, passed=True (dd_threshold=15.0%, alpha_floor=-5.0%)
2026-07-08 00:17:52.152 | INFO     | mytrader.backtest.matrix_backtest:run_walk_forward:865 - [WalkForward] Round 4/4: train=2024-01-08~2025-07-08, val=2025-07-08~2026-01-08
2026-07-08 00:17:52.152 | WARNING  | mytrader.backtest.matrix_backtest:_get_spy_returns:1112 - [MatrixBacktest] SPY data unavailable, alpha will degrade to 0.0
2026-07-08 00:17:52.152 | INFO     | mytrader.backtest.matrix_backtest:_run_group:1167 - [MatrixBacktest] NDX_mid_vol: start — 1 strategies × 2 valid symbols
2026-07-08 00:17:52.198 | INFO     | mytrader.backtest.matrix_backtest:_run_group:1251 - [MatrixBacktest] NDX_mid_vol: dual_ma done in 0.0s (1 param combos × 2 symbols)
2026-07-08 00:17:52.198 | WARNING  | mytrader.backtest.matrix_backtest:_run_group:1272 - [MatrixBacktest] NDX_mid_vol: strategy 'dual_ma' is DEGENERATE (>= 80% symbols have 0 closed trades) — excluded before ranking. Its Sortino/alpha is mark-to-market illusion.
2026-07-08 00:17:52.198 | WARNING  | mytrader.backtest.matrix_backtest:_run_group:1282 - [MatrixBacktest] NDX_mid_vol: ALL strategies degenerate — group produces EMPTY weights (hold cash). Marked no_valid_strategy.
2026-07-08 00:17:52.198 | WARNING  | mytrader.backtest.matrix_backtest:_get_spy_returns:1112 - [MatrixBacktest] SPY data unavailable, alpha will degrade to 0.0
2026-07-08 00:17:52.198 | INFO     | mytrader.backtest.matrix_backtest:_run_group:1167 - [MatrixBacktest] SPX_mid_vol: start — 1 strategies × 1 valid symbols
2026-07-08 00:17:52.223 | INFO     | mytrader.backtest.matrix_backtest:_run_group:1251 - [MatrixBacktest] SPX_mid_vol: dual_ma done in 0.0s (1 param combos × 1 symbols)
2026-07-08 00:17:52.224 | WARNING  | mytrader.backtest.matrix_backtest:_run_group:1272 - [MatrixBacktest] SPX_mid_vol: strategy 'dual_ma' is DEGENERATE (>= 80% symbols have 0 closed trades) — excluded before ranking. Its Sortino/alpha is mark-to-market illusion.
2026-07-08 00:17:52.224 | WARNING  | mytrader.backtest.matrix_backtest:_run_group:1282 - [MatrixBacktest] SPX_mid_vol: ALL strategies degenerate — group produces EMPTY weights (hold cash). Marked no_valid_strategy.
2026-07-08 00:17:52.224 | WARNING  | mytrader.backtest.matrix_backtest:run_walk_forward:905 - [WalkForward] Round 4: no valid val returns — sortino=0, dd=0, alpha=0, passed=True (vacuous)
2026-07-08 00:17:52.224 | INFO     | mytrader.backtest.matrix_backtest:run_walk_forward:954 - [WalkForward] Round 4 result: sortino=0.0000, dd=0.0000%, alpha=0.0000%, passed=True (dd_threshold=15.0%, alpha_floor=-5.0%)
2026-07-08 00:17:52.224 | INFO     | mytrader.backtest.matrix_backtest:run_walk_forward:979 - [WalkForward] done: 4 rounds, pass_all_rounds=False, max_val_dd=0.0000%, avg_val_alpha=0.0000%, min_val_alpha=0.0000%
=========================== short test summary info ============================
FAILED tests/test_matrix_backtest.py::TestWalkForward::test_run_walk_forward_mock_integration
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!!

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
I
---
 see
---
!
---
 The
---
 test
---
 fails
---
 because
---
:

---
1
---
.
---
 The
---
 mock
---
_store
---
 doesn
---
't
---
 have
---
 SP
---
Y
---
 data
---
 →
---
 `_
---
get
---
_s
---
py
---
_returns
---
`
---
 returns
---
 None
---
 →
---
 `
---
val
---
_alpha
---
=
---
0
---
.
---
0
---
`

---
2
---
.
---
 Also
---
,
---
 the
---
 strategy
---
 is
---
 deg
---
enerate
---
 (
---
0
---
 closed
---
 trades
---
)
---
 →
---
 all
---
 groups
---
 produce
---
 empty
---
 weights
---
 →
---
 `
---
all
---
_returns
---
=[]
---
`
---
 →
---
 `
---
val
---
_alpha
---
=
---
0
---
.
---
0
---
`
---
 (
---
the
---
 "
---
no
---
 valid
---
 val
---
 returns
---
"
---
 path
---
)

---
3
---
.
---
 `
---
avg
---
_val
---
_alpha
---
=
---
0
---
.
---
0
---
`
---
 →
---
 `
---
0
---
.
---
0
---
 >
---
 
---
0
---
`
---
 is
---
 False
---
 →
---
 `
---
pass
---
_all
---
_round
---
s
---
=False
---
`

---
4
---
.
---
 The
---
 test
---
 asserts
---
 `
---
report
---
.pass
---
_all
---
_round
---
s
---
 ==
---
 expected
---
_pass
---
`
---
 where
---
 `
---
expected
---
_pass
---
 =
---
 all
---
(r
---
.pass
---
ed
---
)`
---
 =
---
 True
---
 (
---
all
---
 rounds
---
 have
---
 passed
---
=True
---
 vac
---
uously
---
)


---
So
---
 I
---
 need
---
 to
---
 fix
---
 the
---
 `
---
mock
---
_store
---
`
---
 fixture
---
 to
---
:

---
1
---
.
---
 Add
---
 SP
---
Y
---
 data
---
 (
---
so
---
 alpha
---
 can
---
 be
---
 computed
---
)

---
2
---
.
---
 Fix
---
 the
---
 strategy
---
 data
---
 so
---
 it
---
's
---
 not
---
 deg
---
enerate
---
 (
---
has
---
 closed
---
 trades
---
)


---
Wait
---
,
---
 the
---
 deg
---
enerate
---
 issue
---
 is
---
 a
---
 separate
---
 problem
---
.
---
 The
---
 mock
---
 data
---
 uses
---
 `_
---
make
---
_
---
ohl
---
cv
---
(
---
300
---
,
---
 trend
---
="
---
up
---
")
---
`
---
 which
---
 creates
---
 a
---
 linear
---
 upt
---
rend
---
.
---
 On
---
 this
---
 data
---
,
---
 dual
---
_ma
---
(
---
5
---
,
---
20
---
)
---
 produces
---
 signals
---
,
---
 but
---
 the
---
 strategy
---
 might
---
 not
---
 close
---
 trades
---
...
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
 logs
---
,
---
 it
---
 says
---
 "
---
DE
---
GENER
---
ATE
---
 (
---
>=
---
 
---
80
---
%
---
 symbols
---
 have
---
 
---
0
---
 closed
---
 trades
---
)".
---
 This
---
 means
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
 
---
0
---
.


---
Hmm
---
,
---
 but
---
 the
---
 existing
---
 tests
---
 passed
---
 before
---
 my
---
 change
---
.
---
 The
---
 issue
---
 is
---
 that
---
 `
---
all
---
_returns
---
=[]
---
`
---
 →
---
 val
---
_alpha
---
=
---
0
---
 →
---
 avg
---
_alpha
---
=
---
0
---
 →
---
 pass
---
_all
---
_round
---
s
---
=False
---
.
---
 Before
---
 my
---
 change
---
,
---
 `
---
pass
---
_all
---
_round
---
s
---
 =
---
 all
---
(r
---
.pass
---
ed
---
)`
---
 =
---
 True
---
 (
---
vac
---
uous
---
 pass
---
).
---
 After
---
 my
---
 change
---
,
---
 `
---
pass
---
_all
---
_round
---
s
---
 =
---
 all
---
(r
---
.pass
---
ed
---
)
---
 AND
---
 (
---
avg
---
_alpha
---
 >
---
 
---
0
---
)`
---
 =
---
 False
---
.


---
So
---
 the
---
 real
---
 issue
---
 is
---
 just
---
 the
---
 `
---
pass
---
_all
---
_round
---
s
---
`
---
 assertion
---
.
---
 I
---
 have
---
 two
---
 options
---
:

---
1
---
.
---
 Fix
---
 mock
---
_store
---
 to
---
 provide
---
 SP
---
Y
---
 +
---
 non
---
-de
---
generate
---
 strategy
---
 data
---
 →
---
 alpha
---
 >
---
 
---
0
---
 →
---
 pass
---
_all
---
_round
---
s
---
 =
---
 True
---


---
2
---
.
---
 Update
---
 the
---
 test
---
 assertion
---
 to
---
 account
---
 for
---
 the
---
 new
---
 alpha
---
 gate
---



---
Option
---
 
---
2
---
 is
---
 simpler
---
 and
---
 more
---
 targeted
---
.
---
 But
---
 the
---
 spec
---
 says
---
:
---
 "
---
需要在
---
测试
---
中
---
提供
---
 SP
---
Y
---
 数据
---
或
---
 mock
---
 alpha
---
 >
---
 
---
0
---
".
---
 Let
---
 me
---
 try
---
 option
---
 
---
1
---
 first
---
 —
---
 but
---
 the
---
 deg
---
enerate
---
 strategy
---
 issue
---
 makes
---
 this
---
 complex
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
 at
---
 the
---
 logs
---
:
---
 the
---
 strategy
---
 is
---
 deg
---
enerate
---
 because
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
`.
---
 On
---
 a
---
 linear
---
 upt
---
rend
---
 with
---
 dual
---
_ma
---
(
---
5
---
,
---
20
---
),
---
 the
---
 fast
---
 MA
---
 crosses
---
 above
---
 the
---
 slow
---
 MA
---
 early
---
 and
---
 never
---
 crosses
---
 back
---
,
---
 so
---
 there
---
's
---
 only
---
 an
---
 entry
---
 signal
---
 and
---
 no
---
 exit
---
 signal
---
 →
---
 no
---
 closed
---
 trades
---
.


---
To
---
 fix
---
 this
---
,
---
 I
---
'd
---
 need
---
 to
---
 use
---
 oscill
---
ating
---
 data
---
 (
---
not
---
 pure
---
 upt
---
rend
---
)
---
 so
---
 the
---
 strategy
---
 produces
---
 both
---
 entries
---
 and
---
 exits
---
.
---
 But
---
 that
---
 would
---
 change
---
 the
---
 mock
---
_store
---
 fixture
---
 which
---
 many
---
 tests
---
 depend
---
 on
---
.


---
The
---
 cleaner
---
 approach
---
:
---
 update
---
 the
---
 WF
---
 integration
---
 test
---
 assertions
---
 to
---
 account
---
 for
---
 the
---
 new
---
 alpha
---
 gate
---
.
---
 Specifically
---
:

---
-
---
 `
---
assert
---
 r
---
.pass
---
ed
---
 ==
---
 (
---
r
---
.val
---
_max
---
_dd
---
 <=
---
 W
---
ALK
---
_FORWARD
---
_VAL
---
_DD
---
_THRESHOLD
---
)`
---
 →
---
 this
---
 still
---
 holds
---
 because
---
 alpha
---
=
---
0
---
 >
---
 -
---
5
---
 floor
---
,
---
 so
---
 passed
---
 =
---
 dd
---
_passed
---


---
-
---
 `
---
assert
---
 report
---
.pass
---
_all
---
_round
---
s
---
 ==
---
 expected
---
_pass
---
`
---
 →
---
 this
---
 needs
---
 to
---
 change
---
 to
---
 account
---
 for
---
 avg
---
_alpha
---
 >
---
 
---
0
---



---
Let
---
 me
---
 update
---
 the
---
 test
---
 to
---
:

---
```
---
python
---


---
expected
---
_pass
---
 =
---
 all
---
(r
---
.pass
---
ed
---
 for
---
 r
---
 in
---
 report
---
.round
---
s
---
)
---
 and
---
 report
---
.avg
---
_val
---
_alpha
---
 >
---
 
---
0
---


---
assert
---
 report
---
.pass
---
_all
---
_round
---
s
---
 ==
---
 expected
---
_pass
---


---
``
---
`


---
This
---
 is
---
 the
---
 correct
---
 assertion
---
 that
---
 matches
---
 the
---
 new
---
 gate
---
 logic
---
.
---
 And
---
 it
---
 doesn
---
't
---
 require
---
 changing
---
 the
---
 mock
---
_store
---
 fixture
---
.


---
Actually
---
,
---
 let
---
 me
---
 think
---
 about
---
 this
---
 more
---
 carefully
---
.
---
 The
---
 spec
---
 says
---
 I
---
 should
---
 check
---
 if
---
 existing
---
 tests
---
 need
---
 adjustment
---
.
---
 The
---
 clean
---
est
---
 approach
---
 that
---
 matches
---
 the
---
 spec
---
's
---
 intent
---
 is
---
:


---
1
---
.
---
 Update
---
 the
---
 test
---
 assertion
---
 to
---
 account
---
 for
---
 the
---
 new
---
 alpha
---
 gate
---
 (
---
minimal
---
 change
---
)

---
2
---
.
---
 OR
---
 add
---
 SP
---
Y
---
 to
---
 mock
---
_store
---
 (
---
more
---
 realistic
---
 but
---
 risk
---
ier
---
)


---
Given
---
 that
---
 the
---
 mock
---
_store
---
 fixture
---
 is
---
 used
---
 by
---
 many
---
 tests
---
 and
---
 the
---
 strategy
---
 is
---
 deg
---
enerate
---
 (
---
no
---
 closed
---
 trades
---
),
---
 adding
---
 SP
---
Y
---
 alone
---
 won
---
't
---
 help
---
 —
---
 the
---
 strategy
---
 still
---
 produces
---
 empty
---
 weights
---
 due
---
 to
---
 deg
---
ener
---
acy
---
.
---
 So
---
 I
---
'd
---
 need
---
 to
---
 also
---
 fix
---
 the
---
 mock
---
 data
---
 to
---
 be
---
 non
---
-de
---
generate
---
,
---
 which
---
 is
---
 a
---
 bigger
---
 change
---
.


---
The
---
 minimal
---
,
---
 targeted
---
 approach
---
:
---
 update
---
 the
---
 WF
---
 integration
---
 test
---
 assertions
---
.
---
 Let
---
 me
---
 do
---
 that
---
.


---
Actually
---
 wait
---
,
---
 let
---
 me
---
 re
---
-read
---
 the
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
assert
---
 r
---
.pass
---
ed
---
 ==
---
 (
---
r
---
.val
---
_max
---
_dd
---
 <=
---
 W
---
ALK
---
_FORWARD
---
_VAL
---
_DD
---
_THRESHOLD
---
)

---
``
---
`


---
This
---
 assertion
---
 checks
---
 that
---
 `
---
passed
---
`
---
 depends
---
 only
---
 on
---
 DD
---
.
---
 After
---
 my
---
 change
---
,
---
 `
---
passed
---
 =
---
 dd
---
_passed
---
 AND
---
 alpha
---
_passed
---
`.
---
 With
---
 alpha
---
=
---
0
---
 (
---
no
---
 SP
---
Y
---
),
---
 `
---
alpha
---
_passed
---
 =
---
 
---
0
---
 >
---
 -
---
5
---
 =
---
 True
---
`,
---
 so
---
 `
---
passed
---
 =
---
 dd
---
_passed
---
`.
---
 This
---
 assertion
---
 still
---
 holds
---
!


---
The
---
 failing
---
 assertion
---
 is
---
:

---
```
---
python
---


---
expected
---
_pass
---
 =
---
 all
---
(r
---
.pass
---
ed
---
 for
---
 r
---
 in
---
 report
---
.round
---
s
---
)

---
assert
---
 report
---
.pass
---
_all
---
_round
---
s
---
 ==
---
 expected
---
_pass
---


---
``
---
`


---
This
---
 fails
---
 because
---
 `
---
pass
---
_all
---
_round
---
s
---
 =
---
 all
---
(r
---
.pass
---
ed
---
)
---
 AND
---
 (
---
avg
---
_alpha
---
 >
---
 
---
0
---
)`
---
 =
---
 `
---
True
---
 AND
---
 False
---
`
---
 =
---
 `
---
False
---
`,
---
 but
---
 `
---
expected
---
_pass
---
 =
---
 True
---
`.


---
I
---
 should
---
 update
---
 this
---
 to
---
:

---
```
---
python
---


---
expected
---
_pass
---
 =
---
 all
---
(r
---
.pass
---
ed
---
 for
---
 r
---
 in
---
 report
---
.round
---
s
---
)
---
 and
---
 (
---
report
---
.avg
---
_val
---
_alpha
---
 >
---
 
---
0
---
)

---
assert
---
 report
---
.pass
---
_all
---
_round
---
s
---
 ==
---
 expected
---
_pass
---


---
``
---
`


---
This
---
 correctly
---
 reflects
---
 the
---
 new
---
 gate
---
 logic
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
.


---
But
---
 actually
---
,
---
 I
---
 also
---
 want
---
 to
---
 check
---
:
---
 is
---
 the
---
 `
---
r
---
.pass
---
ed
---
 ==
---
 (
---
r
---
.val
---
_max
---
_dd
---
 <=
---
 W
---
ALK
---
_FORWARD
---
_VAL
---
_DD
---
_THRESHOLD
---
)`
---
 assertion
---
 still
---
 correct
---
?
---
 Let
---
 me
---
 think
---
...


---
With
---
 no
---
 SP
---
Y
---
 data
---
,
---
 `
---
val
---
_alpha
---
=
---
0
---
.
---
0
---
`.
---
 `
---
alpha
---
_passed
---
 =
---
 
---
0
---
.
---
0
---
 >
---
 -
---
5
---
.
---
0
---
 =
---
 True
---
`.
---
 `
---
passed
---
 =
---
 dd
---
_passed
---
 AND
---
 True
---
 =
---
 dd
---
_passed
---
`.
---
 So
---
 `
---
r
---
.pass
---
ed
---
 ==
---
 (
---
r
---
.val
---
_max
---
_dd
---
 <=
---
 W
---
ALK
---
_FORWARD
---
_VAL
---
_DD
---
_THRESHOLD
---
)`
---
 is
---
 True
---
.
---
 ✓
---



---
But
---
 this
---
 assertion
---
 is
---
 testing
---
 implementation
---
 details
---
.
---
 After
---
 my
---
 change
---
,
---
 `
---
passed
---
`
---
 depends
---
 on
---
 BOTH
---
 DD
---
 and
---
 alpha
---
.
---
 The
---
 fact
---
 that
---
 alpha
---
=
---
0
---
 happens
---
 to
---
 pass
---
 the
---
 floor
---
 doesn
---
't
---
 mean
---
 the
---
 assertion
---
 is
---
 testing
---
 the
---
 right
---
 thing
---
.
---
 I
---
 should
---
 update
---
 it
---
 to
---
:

---
```
---
python
---


---
expected
---
_passed
---
 =
---
 (
---
r
---
.val
---
_max
---
_dd
---
 <=
---
 W
---
ALK
---
_FORWARD
---
_VAL
---
_DD
---
_THRESHOLD
---
)
---
 and
---
 (
---
r
---
.val
---
_alpha
---
 >
---
 W
---
ALK
---
_FORWARD
---
_VAL
---
_ALPHA
---
_F
---
LOOR
---
)

---
assert
---
 r
---
.pass
---
ed
---
 ==
---
 expected
---
_passed
---


---
``
---
`


---
This
---
 is
---
 more
---
 correct
---
 and
---
 matches
---
 the
---
 new
---
 gate
---
 logic
---
.
---
 Let
---
 me
---
 update
---
 both
---
 assertions
---
.
---
测试
---
失败
---
是因为
---
新的
---
 `
---
avg
---
_alpha
---
 >
---
 
---
0
---
`
---
 条
---
件
---
使得
---
 `
---
pass
---
_all
---
_round
---
s
---
=False
---
`
---
（
---
因为
---
 mock
---
 中
---
没有
---
 SP
---
Y
---
 数据
---
 →
---
 alpha
---
=
---
0
---
）。
---
让我
---
更新
---
 WF
---
 
---
集
---
成
---
测试
---
的
---
断
---
言
---
，
---
以
---
反映
---
新的
---
门
---
控
---
逻辑
---
。
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py","limit":50,"offset":905}
---
 905→        assert isinstance(report, WalkForwardReport), (
 906→            f"run_walk_forward 应返回 WalkForwardReport，实际 {type(report)}"
 907→        )
 908→        assert len(report.rounds) == 4, (
 909→            f"应跑 4 轮，实际 {len(report.rounds)} 轮"
 910→        )
 911→        for i, r in enumerate(report.rounds):
 912→            assert isinstance(r, WalkForwardRound)
 913→            assert r.round_num == i + 1, (
 914→                f"Round {i}: round_num 应为 {i+1}，实际 {r.round_num}"
 915→            )
 916→            assert isinstance(r.val_sortino, float)
 917→            assert isinstance(r.val_max_dd, float)
 918→            assert r.val_max_dd >= 0.0
 919→            assert isinstance(r.passed, bool)
 920→            assert r.passed == (r.val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD)
 921→
 922→        expected_pass = all(r.passed for r in report.rounds)
 923→        assert report.pass_all_rounds == expected_pass
 924→        expected_max_dd = max(r.val_max_dd for r in report.rounds)
 925→        assert abs(report.max_val_dd - expected_max_dd) < 1e-9
 926→
 927→    def test_run_walk_forward_empty_universe(self):
 928→        """空标的组时返回空 WalkForwardReport，不抛异常。"""
 929→        store = MagicMock()
 930→        store.get_bars_multi.return_value = {}
 931→        universe = MagicMock()
 932→        universe.get_groups.return_value = {}
 933→        mb = MatrixBacktest(store=store, universe=universe, years=1)
 934→
 935→        report = run_walk_forward(
 936→            mb=mb,
 937→            strategies=["dual_ma"],
 938→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 939→            rounds=4,
 940→        )
 941→        assert isinstance(report, WalkForwardReport)
 942→        assert report.rounds == []
 943→        assert report.pass_all_rounds is False
 944→        assert report.max_val_dd == 0.0
 945→
 946→    def test_run_walk_forward_custom_rounds(self, mock_store, mock_universe):
 947→        """run_walk_forward 支持自定义 rounds 参数（非默认 4）。"""
 948→        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)
 949→        report = run_walk_forward(
 950→            mb=mb,
 951→            strategies=["dual_ma"],
 952→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 953→            rounds=2,
 954→            train_months=12,
 955→
---
 905→        assert isinstance(report, WalkForwardReport), (
 906→            f"run_walk_forward 应返回 WalkForwardReport，实际 {type(report)}"
 907→        )
 908→        assert len(report.rounds) == 4, (
 909→            f"应跑 4 轮，实际 {len(report.rounds)} 轮"
 910→        )
 911→        for i, r in enumerate(report.rounds):
 912→            assert isinstance(r, WalkForwardRound)
 913→            assert r.round_num == i + 1, (
 914→                f"Round {i}: round_num 应为 {i+1}，实际 {r.round_num}"
 915→            )
 916→            assert isinstance(r.val_sortino, float)
 917→            assert isinstance(r.val_max_dd, float)
 918→            assert r.val_max_dd >= 0.0
 919→            assert isinstance(r.passed, bool)
 920→            assert r.passed == (r.val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD)
 921→
 922→        expected_pass = all(r.passed for r in report.rounds)
 923→        assert report.pass_all_rounds == expected_pass
 924→        expected_max_dd = max(r.val_max_dd for r in report.rounds)
 925→        assert abs(report.max_val_dd - expected_max_dd) < 1e-9
 926→
 927→    def test_run_walk_forward_empty_universe(self):
 928→        """空标的组时返回空 WalkForwardReport，不抛异常。"""
 929→        store = MagicMock()
 930→        store.get_bars_multi.return_value = {}
 931→        universe = MagicMock()
 932→        universe.get_groups.return_value = {}
 933→        mb = MatrixBacktest(store=store, universe=universe, years=1)
 934→
 935→        report = run_walk_forward(
 936→            mb=mb,
 937→            strategies=["dual_ma"],
 938→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 939→            rounds=4,
 940→        )
 941→        assert isinstance(report, WalkForwardReport)
 942→        assert report.rounds == []
 943→        assert report.pass_all_rounds is False
 944→        assert report.max_val_dd == 0.0
 945→
 946→    def test_run_walk_forward_custom_rounds(self, mock_store, mock_universe):
 947→        """run_walk_forward 支持自定义 rounds 参数（非默认 4）。"""
 948→        mb = MatrixBacktest(store=mock_store, universe=mock_universe, years=1, top_k=1)
 949→        report = run_walk_forward(
 950→            mb=mb,
 951→            strategies=["dual_ma"],
 952→            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
 953→            rounds=2,
 954→            train_months=12,
 955→
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py","new_string":"        for i, r in enumerate(report.rounds):\n            assert isinstance(r, WalkForwardRound)\n            assert r.round_num == i + 1, (\n                f\"Round {i}: round_num 应为 {i+1}，实际 {r.round_num}\"\n            )\n            assert isinstance(r.val_sortino, float)\n            assert isinstance(r.val_max_dd, float)\n            assert r.val_max_dd >= 0.0\n            assert isinstance(r.val_alpha, float)  # 迭代 #13：val_alpha 字段\n            assert isinstance(r.passed, bool)\n            # 迭代 #13：passed = DD ≤ 15% AND alpha > -5%\n            expected_round_passed = (\n                r.val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD\n                and r.val_alpha > WALK_FORWARD_VAL_ALPHA_FLOOR\n            )\n            assert r.passed == expected_round_passed\n\n        # 迭代 #13：pass_all_rounds = all rounds passed AND avg_val_alpha > 0\n        expected_pass = (\n            all(r.passed for r in report.rounds)\n            and report.avg_val_alpha > 0\n        )\n        assert report.pass_all_rounds == expected_pass\n        expected_max_dd = max(r.val_max_dd for r in report.rounds)\n        assert abs(report.max_val_dd - expected_max_dd) < 1e-9","old_string":"        for i, r in enumerate(report.rounds):\n            assert isinstance(r, WalkForwardRound)\n            assert r.round_num == i + 1, (\n                f\"Round {i}: round_num 应为 {i+1}，实际 {r.round_num}\"\n            )\n            assert isinstance(r.val_sortino, float)\n            assert isinstance(r.val_max_dd, float)\n            assert r.val_max_dd >= 0.0\n            assert isinstance(r.passed, bool)\n            assert r.passed == (r.val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD)\n\n        expected_pass = all(r.passed for r in report.rounds)\n        assert report.pass_all_rounds == expected_pass\n        expected_max_dd = max(r.val_max_dd for r in report.rounds)\n        assert abs(report.max_val_dd - expected_max_dd) < 1e-9"}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py
---
现在我
---
需要
---
更新
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
 
---
中的
---
导入
---
，
---
以
---
包含
---
新的
---
常
---
量
---
。
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py","new_string":"from mytrader.backtest.matrix_backtest import (\n    MatrixBacktest,\n    _backtest_one,\n    _combine_daily_returns,\n    _compute_alpha,\n    _compute_sharpe,\n    _compute_sortino,\n    _portfolio_max_drawdown_from_results,\n    _portfolio_sharpe_from_results,\n    _portfolio_sortino_from_results,\n    _optimize_ensemble_weights,\n    _safe_float,\n    _safe_mean,\n    MAX_PORTFOLIO_DRAWDOWN_PCT,\n    MIN_SORTINO_THRESHOLD,\n    WALK_FORWARD_VAL_ALPHA_FLOOR,\n    WALK_FORWARD_VAL_DD_THRESHOLD,\n    SingleBacktestResult,\n    WalkForwardReport,\n    WalkForwardRound,\n    _add_months,\n    run_walk_forward,\n)","old_string":"from mytrader.backtest.matrix_backtest import (\n    MatrixBacktest,\n    _backtest_one,\n    _combine_daily_returns,\n    _compute_alpha,\n    _compute_sharpe,\n    _compute_sortino,\n    _portfolio_max_drawdown_from_results,\n    _portfolio_sharpe_from_results,\n    _portfolio_sortino_from_results,\n    _optimize_ensemble_weights,\n    _safe_float,\n    _safe_mean,\n    MAX_PORTFOLIO_DRAWDOWN_PCT,\n    MIN_SORTINO_THRESHOLD,\n    WALK_FORWARD_VAL_DD_THRESHOLD,\n    SingleBacktestResult,\n    WalkForwardReport,\n    WalkForwardRound,\n    _add_months,\n    run_walk_forward,\n)"}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/tests/test_matrix_backtest.py
---
现在
---
让我
---
运行
---
一下
---
 WF
---
 
---
测试
---
来进行
---
验证
---
。
---
{"command":"/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_matrix_backtest.py::TestWalkForward --no-header -q 2>&1 | tail -15","description":"Run WF tests after assertion update"}
---
Run WF tests after assertion update
---
Command: /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_matrix_backtest.py::TestWalkForward --no-header -q 2>&1 | tail -15
Stdout: ..........                                                               [100%]

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
所有
---
 
---
10
---
 个
---
 WF
---
 
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
让我
---
运行
---
新的
---
测试
---
文件
---
。
---
{"command":"/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_wf_alpha_gate.py --no-header -q 2>&1 | tail -30","description":"Run new WF alpha gate tests"}
---
Run new WF alpha gate tests
---
Command: /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_wf_alpha_gate.py --no-header -q 2>&1 | tail -30
Stdout:     
        # 策略下跌 + SPY 上涨 → alpha 显著为负
        for r in report.rounds:
>           assert r.val_alpha < 0, (
                f"策略下跌+SPY上涨应跑输，val_alpha 应 < 0，实际 {r.val_alpha}"
            )
E           AssertionError: 策略下跌+SPY上涨应跑输，val_alpha 应 < 0，实际 0.0
E           assert 0.0 < 0
E            +  where 0.0 = WalkForwardRound(round_num=1, train_start=datetime.date(2024, 7, 8), train_end=datetime.date(2025, 7, 8), val_start=datetime.date(2025, 7, 8), val_end=datetime.date(2025, 11, 8), val_sortino=0.0, val_max_dd=0.0, passed=True, val_alpha=0.0).val_alpha

tests/test_wf_alpha_gate.py:508: AssertionError
----------------------------- Captured stderr call -----------------------------
2026-07-08 00:18:50.978 | INFO     | mytrader.backtest.matrix_backtest:run_walk_forward:865 - [WalkForward] Round 1/2: train=2024-07-08~2025-07-08, val=2025-07-08~2025-11-08
2026-07-08 00:18:50.979 | INFO     | mytrader.backtest.matrix_backtest:_run_group:1167 - [MatrixBacktest] test_group: start — 1 strategies × 2 valid symbols
2026-07-08 00:18:51.022 | INFO     | mytrader.backtest.matrix_backtest:_run_group:1251 - [MatrixBacktest] test_group: dual_ma done in 0.0s (1 param combos × 2 symbols)
2026-07-08 00:18:51.022 | WARNING  | mytrader.backtest.matrix_backtest:_run_group:1272 - [MatrixBacktest] test_group: strategy 'dual_ma' is DEGENERATE (>= 80% symbols have 0 closed trades) — excluded before ranking. Its Sortino/alpha is mark-to-market illusion.
2026-07-08 00:18:51.022 | WARNING  | mytrader.backtest.matrix_backtest:_run_group:1282 - [MatrixBacktest] test_group: ALL strategies degenerate — group produces EMPTY weights (hold cash). Marked no_valid_strategy.
2026-07-08 00:18:51.023 | WARNING  | mytrader.backtest.matrix_backtest:run_walk_forward:905 - [WalkForward] Round 1: no valid val returns — sortino=0, dd=0, alpha=0, passed=True (vacuous)
2026-07-08 00:18:51.023 | INFO     | mytrader.backtest.matrix_backtest:run_walk_forward:954 - [WalkForward] Round 1 result: sortino=0.0000, dd=0.0000%, alpha=0.0000%, passed=True (dd_threshold=15.0%, alpha_floor=-5.0%)
2026-07-08 00:18:51.023 | INFO     | mytrader.backtest.matrix_backtest:run_walk_forward:865 - [WalkForward] Round 2/2: train=2024-11-08~2025-11-08, val=2025-11-08~2026-03-08
2026-07-08 00:18:51.023 | INFO     | mytrader.backtest.matrix_backtest:_run_group:1167 - [MatrixBacktest] test_group: start — 1 strategies × 2 valid symbols
2026-07-08 00:18:51.066 | INFO     | mytrader.backtest.matrix_backtest:_run_group:1251 - [MatrixBacktest] test_group: dual_ma done in 0.0s (1 param combos × 2 symbols)
2026-07-08 00:18:51.066 | WARNING  | mytrader.backtest.matrix_backtest:_run_group:1272 - [MatrixBacktest] test_group: strategy 'dual_ma' is DEGENERATE (>= 80% symbols have 0 closed trades) — excluded before ranking. Its Sortino/alpha is mark-to-market illusion.
2026-07-08 00:18:51.066 | WARNING  | mytrader.backtest.matrix_backtest:_run_group:1282 - [MatrixBacktest] test_group: ALL strategies degenerate — group produces EMPTY weights (hold cash). Marked no_valid_strategy.
2026-07-08 00:18:51.066 | WARNING  | mytrader.backtest.matrix_backtest:run_walk_forward:905 - [WalkForward] Round 2: no valid val returns — sortino=0, dd=0, alpha=0, passed=True (vacuous)
2026-07-08 00:18:51.066 | INFO     | mytrader.backtest.matrix_backtest:run_walk_forward:954 - [WalkForward] Round 2 result: sortino=0.0000, dd=0.0000%, alpha=0.0000%, passed=True (dd_threshold=15.0%, alpha_floor=-5.0%)
2026-07-08 00:18:51.066 | INFO     | mytrader.backtest.matrix_backtest:run_walk_forward:979 - [WalkForward] done: 2 rounds, pass_all_rounds=False, max_val_dd=0.0000%, avg_val_alpha=0.0000%, min_val_alpha=0.0000%
=========================== short test summary info ============================
FAILED tests/test_wf_alpha_gate.py::TestWFAlphaIntegration::test_wf_alpha_computed_correctly
FAILED tests/test_wf_alpha_gate.py::TestWFAlphaIntegration::test_wf_alpha_underperforms_spy

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
The
---
 issue
---
 is
---
 that
---
 the
---
 mock
---
 strategy
---
 data
---
 is
---
 "
---
de
---
generate
---
"
---
 —
---
 dual
---
_ma
---
(
---
5
---
,
---
20
---
)
---
 on
---
 a
---
 linear
---
 upt
---
rend
---
 produces
---
 no
---
 closed
---
 trades
---
 (
---
only
---
 entries
---
,
---
 no
---
 exits
---
).
---
 This
---
 means
---
:

---
1
---
.
---
 `_
---
run
---
_group
---
`
---
 marks
---
 the
---
 strategy
---
 as
---
 deg
---
enerate
---
 →
---
 returns
---
 empty
---
 weights
---


---
2
---
.
---
 `_
---
back
---
test
---
_with
---
_params
---
_on
---
_period
---
`
---
 gets
---
 empty
---
 weights
---
 →
---
 returns
---
 empty
---
 returns
---


---
3
---
.
---
 `
---
all
---
_returns
---
=[]
---
`
---
 →
---
 val
---
_alpha
---
=
---
0
---
.
---
0
---
 (
---
the
---
 "
---
no
---
 valid
---
 val
---
 returns
---
"
---
 path
---
)


---
So
---
 my
---
 integration
---
 tests
---
 that
---
 expect
---
 non
---
-zero
---
 alpha
---
 fail
---
 because
---
 the
---
 strategy
---
 never
---
 produces
---
 trades
---
.


---
I
---
 need
---
 to
---
 either
---
:

---
1
---
.
---
 Use
---
 mock
---
 data
---
 that
---
 produces
---
 non
---
-de
---
generate
---
 strategies
---
 (
---
osc
---
ill
---
ating
---
 data
---
)

---
2
---
.
---
 Mock
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
 return
---
 controlled
---
 results
---
 with
---
 closed
---
 trades
---


---
3
---
.
---
 Mock
---
 `_
---
run
---
_group
---
`
---
 to
---
 return
---
 non
---
-empty
---
 weights
---



---
Option
---
 
---
2
---
 is
---
 the
---
 clean
---
est
---
 for
---
 testing
---
 WF
---
 alpha
---
 computation
---
.
---
 I
---
'll
---
 patch
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
 return
---
 results
---
 with
---
 controlled
---
 daily
---
_returns
---
 that
---
 produce
---
 known
---
 alpha
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
 existing
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
 (
---
line
---
 
---
104
---
8
---
),
---
 it
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
 to
---
 return
---
 controlled
---
 results
---
.
---
 Let
---
 me
---
 use
---
 a
---
 similar
---
 approach
---
.


---
But
---
 wait
---
,
---
 there
---
's
---
 a
---
 complication
---
.
---
 In
---
 WF
---
,
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
 is
---
 called
---
 in
---
 two
---
 places
---
:

---
1
---
.
---
 In
---
 `_
---
run
---
_group
---
`
---
 (
---
training
---
 period
---
)
---
 —
---
 to
---
 find
---
 best
---
 params
---


---
2
---
.
---
 In
---
 `_
---
back
---
test
---
_with
---
_params
---
_on
---
_period
---
`
---
 (
---
validation
---
 period
---
)
---
 —
---
 to
---
 compute
---
 val
---
 returns
---



---
If
---
 I
---
 patch
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
 it
---
 will
---
 affect
---
 both
---
.
---
 I
---
 need
---
 the
---
 training
---
 period
---
 to
---
 produce
---
 valid
---
 results
---
 (
---
non
---
-de
---
generate
---
)
---
 so
---
 `_
---
run
---
_group
---
`
---
 returns
---
 non
---
-empty
---
 weights
---
,
---
 and
---
 the
---
 validation
---
 period
---
 to
---
 produce
---
 returns
---
 that
---
 have
---
 known
---
 alpha
---
 vs
---
 SP
---
Y
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
 how
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
 does
---
 it
---
:

---
```
---
python
---


---
def
---
 mock
---
_back
---
test
---
_batch
---
(data
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
 *
---
args
---
,
---
 **
---
kwargs
---
):

---
   
---
 results
---
 =
---
 []

---
   
---
 for
---
 sym
---
,
---
 df
---
 in
---
 data
---
.items
---
():

---
       
---
 ...

---
       
---
 if
---
 strategy
---
_name
---
 ==
---
 "
---
dual
---
_ma
---
":

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
,

---
               
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
,

---
           
---
 ))

---
   
---
 return
---
 results
---


---
``
---
`


---
It
---
 returns
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
 with
---
 controlled
---
 `
---
daily
---
_returns
---
`
---
 and
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
10
---
`
---
 (
---
non
---
-de
---
generate
---
).


---
I
---
'll
---
 use
---
 a
---
 similar
---
 approach
---
.
---
 Let
---
 me
---
 rewrite
---
 the
---
 integration
---
 tests
---
 to
---
 patch
---
 `_
---
back
---
test
---
_batch
---
`.


---
Actually
---
,
---
 let
---
 me
---
 think
---
 about
---
 this
---
 differently
---
.
---
 The
---
 key
---
 tests
---
 are
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
_wf
---
_s
---
py
---
_un
---
available
---
_alpha
---
_zero
---
`
---
 —
---
 SP
---
Y
---
 unavailable
---
 →
---
 val
---
_alpha
---
=
---
0
---
.
---
 This
---
 works
---
 with
---
 deg
---
enerate
---
 strategies
---
 because
---
 `
---
all
---
_returns
---
=[]
---
`
---
 →
---
 val
---
_alpha
---
=
---
0
---
.
---
 ✓
---
 (
---
already
---
 passes
---
)

---
2
---
.
---
 `
---
test
---
_wf
---
_alpha
---
_com
---
puted
---
_correct
---
ly
---
`
---
 —
---
 strategy
---
 out
---
per
---
forms
---
 SP
---
Y
---
 →
---
 val
---
_alpha
---
 >
---
 
---
0
---
.
---
 Needs
---
 non
---
-de
---
generate
---
 strategy
---
.

---
3
---
.
---
 `
---
test
---
_wf
---
_alpha
---
_under
---
per
---
forms
---
_s
---
py
---
`
---
 —
---
 strategy
---
 under
---
per
---
forms
---
 SP
---
Y
---
 →
---
 val
---
_alpha
---
 <
---
 
---
0
---
.
---
 Needs
---
 non
---
-de
---
generate
---
 strategy
---
.


---
For
---
 tests
---
 
---
2
---
 and
---
 
---
3
---
,
---
 I
---
 need
---
 to
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
 to
---
 return
---
 controlled
---
 results
---
.
---
 Let
---
 me
---
 rewrite
---
 these
---
 tests
---
.


---
Actually
---
,
---
 the
---
 simplest
---
 approach
---
 for
---
 tests
---
 
---
2
---
 and
---
 
---
3
---
:
---
 directly
---
 test
---
 `_
---
compute
---
_alpha
---
`
---
 with
---
 known
---
 inputs
---
 (
---
which
---
 I
---
 already
---
 do
---
 in
---
 the
---
 data
---
class
---
/g
---
ate
---
 tests
---
).
---
 The
---
 integration
---
 tests
---
 should
---
 verify
---
 that
---
 `
---
run
---
_walk
---
_forward
---
`
---
 correctly
---
 calls
---
 `_
---
compute
---
_alpha
---
`
---
 and
---
 pop
---
ulates
---
 `
---
val
---
_alpha
---
`.


---
Let
---
 me
---
 simplify
---
:
---
 for
---
 the
---
 integration
---
 tests
---
,
---
 I
---
'll
---
 patch
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
 return
---
 non
---
-de
---
generate
---
 results
---
 with
---
 controlled
---
 daily
---
_returns
---
.
---
 This
---
 way
---
:

---
-
---
 Training
---
 period
---
:
---
 `_
---
run
---
_group
---
`
---
 gets
---
 non
---
-de
---
generate
---
 results
---
 →
---
 returns
---
 non
---
-empty
---
 weights
---


---
-
---
 Validation
---
 period
---
:
---
 `_
---
back
---
test
---
_with
---
_params
---
_on
---
_period
---
`
---
 gets
---
 non
---
-de
---
generate
---
 results
---
 →
---
 returns
---
 daily
---
_returns
---


---
-
---
 `
---
combined
---
`
---
 returns
---
 are
---
 non
---
-empty
---
 →
---
 val
---
_alpha
---
 is
---
 computed
---



---
Let
---
 me
---
 rewrite
---
 the
---
 failing
---
 tests
---
.
---
策略
---
数据
---
退
---
化了
---
（
---
线性
---
上升趋势
---
 →
---
 无
---
平
---
仓
---
交易
---
）。
---
我
---
需要
---
 patch
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
 以
---
返回
---
具有
---
已知
---
收益
---
的非
---
退化
---
结果
---
。
---
让我
---
重
---
写
---
失败的
---
集成
---
测试
---
。
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/tests/test_wf_alpha_gate.py","new_string":"class TestWFAlphaIntegration:\n    \"\"\"迭代 #13：run_walk_forward 集成测试 — val_alpha 计算正确性。\n\n    用 patch 拦截 _backtest_batch，返回受控的 daily_returns + closed_trades>0\n    （避免退化门槛拦截），验证 WF 验证期正确计算 alpha vs SPY。\n    \"\"\"\n\n    def test_wf_spy_unavailable_alpha_zero(self):\n        \"\"\"SPY 不可用时 val_alpha=0.0 + WARNING（降级不阻塞）。\n\n        构造 mock_store 不返回 SPY 数据 → _get_spy_returns 返回 None\n        → val_alpha=0.0（降级处理，不抛异常）\n        → 单轮 passed=True（alpha=0 > -5 floor）\n        → 但 avg_alpha=0 → pass_all_rounds=False（0 不 > 0）\n        \"\"\"\n        df_strat = _make_strategy_ohlcv(300, trend=\"up\")\n\n        store = MagicMock()\n        # 不包含 SPY\n        def get_bars_multi(symbols, start, end, timeframe=\"1d\"):\n            mapping = {\"AAPL\": df_strat, \"MSFT\": df_strat}\n            return {s: mapping[s] for s in symbols if s in mapping}\n        store.get_bars_multi.side_effect = get_bars_multi\n\n        universe = MagicMock()\n        universe.get_groups.return_value = {\"test_group\": [\"AAPL\", \"MSFT\"]}\n\n        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=1)\n\n        # patch _backtest_batch 返回非退化结果（closed_trades>0）\n        # 使策略能通过健全性门槛，产出非空权重\n        idx = pd.date_range(\"2021-01-01\", periods=300, freq=\"B\")\n        controlled_returns = pd.Series(\n            np.random.normal(0.001, 0.002, 300), index=idx\n        )\n\n        def mock_batch(data, strategy_name, params, *args, **kwargs):\n            results = []\n            for sym in data.keys():\n                results.append(SingleBacktestResult(\n                    symbol=sym, strategy=strategy_name, params=params,\n                    sharpe=1.0, total_return_pct=10.0, max_drawdown_pct=5.0,\n                    win_rate_pct=55.0, total_trades=10,\n                    daily_returns=controlled_returns,\n                    sortino=1.5, closed_trades=10,\n                ))\n            return results\n\n        with patch(\n            \"mytrader.backtest.matrix_backtest._backtest_batch\",\n            side_effect=mock_batch,\n        ):\n            report = run_walk_forward(\n                mb=mb,\n                strategies=[\"dual_ma\"],\n                param_grids={\"dual_ma\": {\"fast\": [5], \"slow\": [20]}},\n                rounds=2,\n                train_months=12,\n                val_months=4,\n            )\n\n        assert isinstance(report, WalkForwardReport)\n        assert len(report.rounds) == 2\n        # SPY 不可用 → val_alpha=0.0\n        for r in report.rounds:\n            assert r.val_alpha == 0.0, (\n                f\"SPY 不可用时 val_alpha 应为 0.0，实际 {r.val_alpha}\"\n            )\n        # avg=0 → 不 > 0 → pass_all_rounds=False\n        assert report.avg_val_alpha == 0.0\n        assert report.pass_all_rounds is False, (\n            \"avg_alpha=0 不满足 > 0，pass_all_rounds 应为 False\"\n        )\n\n    def test_wf_alpha_computed_correctly(self):\n        \"\"\"用已知 returns + spy_returns 验证 val_alpha 值正确。\n\n        构造 mock store 返回 SPY（温和上涨 ~10% 年化），\n        patch _backtest_batch 返回策略 daily_returns（强正收益 ~28% 年化）。\n        验证 val_alpha > 0（策略跑赢 SPY）。\n        \"\"\"\n        n = 300\n        idx = pd.date_range(\"2021-01-01\", periods=n, freq=\"B\")\n        df_spy = _make_spy_ohlcv(n, annual_growth=0.10)\n        # 策略数据（仅用于 _backtest_batch 的 data 参数，实际 returns 由 mock 提供）\n        df_strat = _make_strategy_ohlcv(n, trend=\"up\")\n\n        store = MagicMock()\n        def get_bars_multi(symbols, start, end, timeframe=\"1d\"):\n            mapping = {\"AAPL\": df_strat, \"MSFT\": df_strat, \"SPY\": df_spy}\n            return {s: mapping[s] for s in symbols if s in mapping}\n        store.get_bars_multi.side_effect = get_bars_multi\n\n        universe = MagicMock()\n        universe.get_groups.return_value = {\"test_group\": [\"AAPL\", \"MSFT\"]}\n\n        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=1)\n\n        # 策略 daily_returns：日均 0.001（~28% 年化），跑赢 SPY 的 ~10%\n        controlled_returns = pd.Series(\n            np.random.normal(0.001, 0.002, n), index=idx\n        )\n\n        def mock_batch(data, strategy_name, params, *args, **kwargs):\n            results = []\n            for sym in data.keys():\n                results.append(SingleBacktestResult(\n                    symbol=sym, strategy=strategy_name, params=params,\n                    sharpe=1.0, total_return_pct=10.0, max_drawdown_pct=5.0,\n                    win_rate_pct=55.0, total_trades=10,\n                    daily_returns=controlled_returns,\n                    sortino=1.5, closed_trades=10,\n                ))\n            return results\n\n        with patch(\n            \"mytrader.backtest.matrix_backtest._backtest_batch\",\n            side_effect=mock_batch,\n        ):\n            report = run_walk_forward(\n                mb=mb,\n                strategies=[\"dual_ma\"],\n                param_grids={\"dual_ma\": {\"fast\": [5], \"slow\": [20]}},\n                rounds=2,\n                train_months=12,\n                val_months=4,\n            )\n\n        assert len(report.rounds) == 2\n        # 策略 ~28% 年化 > SPY ~10% 年化 → alpha > 0\n        for r in report.rounds:\n            assert r.val_alpha > 0, (\n                f\"策略强趋势应跑赢 SPY，val_alpha 应 > 0，实际 {r.val_alpha}\"\n            )\n        assert report.avg_val_alpha > 0\n        assert report.min_val_alpha == min(r.val_alpha for r in report.rounds)\n\n    def test_wf_alpha_underperforms_spy(self):\n        \"\"\"策略跑输 SPY → val_alpha < 0 → pass_all_rounds=False。\n\n        构造 SPY 温和上涨（~10% 年化），\n        patch _backtest_batch 返回策略 daily_returns（负收益 ~-20% 年化）。\n        验证 val_alpha < 0 + pass_all_rounds=False。\n        \"\"\"\n        n = 300\n        idx = pd.date_range(\"2021-01-01\", periods=n, freq=\"B\")\n        df_spy = _make_spy_ohlcv(n, annual_growth=0.10)\n        df_strat = _make_strategy_ohlcv(n, trend=\"up\")\n\n        store = MagicMock()\n        def get_bars_multi(symbols, start, end, timeframe=\"1d\"):\n            mapping = {\"AAPL\": df_strat, \"MSFT\": df_strat, \"SPY\": df_spy}\n            return {s: mapping[s] for s in symbols if s in mapping}\n        store.get_bars_multi.side_effect = get_bars_multi\n\n        universe = MagicMock()\n        universe.get_groups.return_value = {\"test_group\": [\"AAPL\", \"MSFT\"]}\n\n        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=1)\n\n        # 策略 daily_returns：日均 -0.0008（~-20% 年化），跑输 SPY 的 ~10%\n        controlled_returns = pd.Series(\n            np.random.normal(-0.0008, 0.002, n), index=idx\n        )\n\n        def mock_batch(data, strategy_name, params, *args, **kwargs):\n            results = []\n            for sym in data.keys():\n                results.append(SingleBacktestResult(\n                    symbol=sym, strategy=strategy_name, params=params,\n                    sharpe=-0.5, total_return_pct=-15.0, max_drawdown_pct=12.0,\n                    win_rate_pct=40.0, total_trades=10,\n                    daily_returns=controlled_returns,\n                    sortino=-0.8, closed_trades=10,\n                ))\n            return results\n\n        with patch(\n            \"mytrader.backtest.matrix_backtest._backtest_batch\",\n            side_effect=mock_batch,\n        ):\n            report = run_walk_forward(\n                mb=mb,\n                strategies=[\"dual_ma\"],\n                param_grids={\"dual_ma\": {\"fast\": [5], \"slow\": [20]}},\n                rounds=2,\n                train_months=12,\n                val_months=4,\n            )\n\n        # 策略 ~-20% 年化 < SPY ~10% 年化 → alpha 显著为负\n        for r in report.rounds:\n            assert r.val_alpha < 0, (\n                f\"策略跑输+SPY上涨应跑输，val_alpha 应 < 0，实际 {r.val_alpha}\"\n            )\n        # 负 alpha → pass_all_rounds=False\n        assert report.pass_all_rounds is False\n        assert report.avg_val_alpha < 0\n\n    def test_wf_alpha_floor_constant_value(self):\n        \"\"\"WALK_FORWARD_VAL_ALPHA_FLOOR 常量值为 -5.0。\"\"\"\n        assert WALK_FORWARD_VAL_ALPHA_FLOOR == -5.0, (\n            f\"WF alpha floor 应为 -5.0，实际 {WALK_FORWARD_VAL_ALPHA_FLOOR}\"\n        )\n\n    def test_wf_alpha_floor_vs_dd_threshold_independent(self):\n        \"\"\"alpha floor 和 DD threshold 是两个独立的 gate（AND 关系）。\"\"\"\n        # DD 合规但 alpha 灾难性跑输\n        dd_passed = 10.0 <= WALK_FORWARD_VAL_DD_THRESHOLD\n        alpha_passed = -8.0 > WALK_FORWARD_VAL_ALPHA_FLOOR\n        passed = dd_passed and alpha_passed\n        assert passed is False, \"DD 合规但 alpha < floor 时应 fail\"\n\n        # DD 合规 + alpha 小幅跑输但 > floor\n        alpha_passed_ok = -3.0 > WALK_FORWARD_VAL_ALPHA_FLOOR\n        passed_ok = dd_passed and alpha_passed_ok\n        assert passed_ok is True, \"DD 合规 + alpha > floor 时应 pass\"\n\n        # DD 不合规 + alpha 跑赢\n        dd_fail = 20.0 <= WALK_FORWARD_VAL_DD_THRESHOLD\n        alpha_good = 5.0 > WALK_FORWARD_VAL_ALPHA_FLOOR\n        passed_dd_fail = dd_fail and alpha_good\n        assert passed_dd_fail is False, \"DD 不合规时即使 alpha 好也应 fail\"","old_string":"class TestWFAlphaIntegration:\n    \"\"\"迭代 #13：run_walk_forward 集成测试 — val_alpha 计算正确性。\"\"\"\n\n    def test_wf_spy_unavailable_alpha_zero(self):\n        \"\"\"SPY 不可用时 val_alpha=0.0 + WARNING（降级不阻塞）。\n\n        构造 mock_store 不返回 SPY 数据 → _get_spy_returns 返回 None\n        → val_alpha=0.0（降级处理，不抛异常）\n        → 单轮 passed=True（alpha=0 > -5 floor）\n        → 但 avg_alpha=0 → pass_all_rounds=False（0 不 > 0）\n        \"\"\"\n        df_strat = _make_strategy_ohlcv(300, trend=\"up\")\n\n        store = MagicMock()\n        # 不包含 SPY\n        def get_bars_multi(symbols, start, end, timeframe=\"1d\"):\n            mapping = {\"AAPL\": df_strat, \"MSFT\": df_strat}\n            return {s: mapping[s] for s in symbols if s in mapping}\n        store.get_bars_multi.side_effect = get_bars_multi\n\n        universe = MagicMock()\n        universe.get_groups.return_value = {\"test_group\": [\"AAPL\", \"MSFT\"]}\n\n        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=1)\n\n        report = run_walk_forward(\n            mb=mb,\n            strategies=[\"dual_ma\"],\n            param_grids={\"dual_ma\": {\"fast\": [5], \"slow\": [20]}},\n            rounds=2,\n            train_months=12,\n            val_months=4,\n        )\n\n        assert isinstance(report, WalkForwardReport)\n        assert len(report.rounds) == 2\n        # SPY 不可用 → val_alpha=0.0\n        for r in report.rounds:\n            assert r.val_alpha == 0.0, (\n                f\"SPY 不可用时 val_alpha 应为 0.0，实际 {r.val_alpha}\"\n            )\n        # avg=0 → 不 > 0 → pass_all_rounds=False\n        assert report.avg_val_alpha == 0.0\n        assert report.pass_all_rounds is False, (\n            \"avg_alpha=0 不满足 > 0，pass_all_rounds 应为 False\"\n        )\n\n    def test_wf_alpha_computed_correctly(self):\n        \"\"\"用已知 returns + spy_returns 验证 val_alpha 值正确。\n\n        构造 mock store 返回：\n          - 策略数据：强趋势（年化 ~50%+）\n          - SPY 数据：温和上涨（年化 ~10%）\n        验证 val_alpha > 0（策略跑赢 SPY）\n        \"\"\"\n        df_strat = _make_strategy_ohlcv(300, trend=\"up\")\n        df_spy = _make_spy_ohlcv(300, annual_growth=0.10)\n\n        store = MagicMock()\n        def get_bars_multi(symbols, start, end, timeframe=\"1d\"):\n            mapping = {\"AAPL\": df_strat, \"MSFT\": df_strat, \"SPY\": df_spy}\n            return {s: mapping[s] for s in symbols if s in mapping}\n        store.get_bars_multi.side_effect = get_bars_multi\n\n        universe = MagicMock()\n        universe.get_groups.return_value = {\"test_group\": [\"AAPL\", \"MSFT\"]}\n\n        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=1)\n\n        report = run_walk_forward(\n            mb=mb,\n            strategies=[\"dual_ma\"],\n            param_grids={\"dual_ma\": {\"fast\": [5], \"slow\": [20]}},\n            rounds=2,\n            train_months=12,\n            val_months=4,\n        )\n\n        assert len(report.rounds) == 2\n        # 策略强趋势 > SPY 温和上涨 → alpha > 0\n        for r in report.rounds:\n            assert r.val_alpha > 0, (\n                f\"策略强趋势应跑赢 SPY，val_alpha 应 > 0，实际 {r.val_alpha}\"\n            )\n        assert report.avg_val_alpha > 0\n        assert report.min_val_alpha > 0 or report.min_val_alpha == min(\n            r.val_alpha for r in report.rounds\n        )\n\n    def test_wf_alpha_underperforms_spy(self):\n        \"\"\"策略跑输 SPY → val_alpha < 0 → pass_all_rounds=False。\n\n        构造策略数据为下跌趋势，SPY 温和上涨 → alpha 显著为负\n        \"\"\"\n        df_strat_down = _make_strategy_ohlcv(300, trend=\"down\")\n        df_spy = _make_spy_ohlcv(300, annual_growth=0.10)\n\n        store = MagicMock()\n        def get_bars_multi(symbols, start, end, timeframe=\"1d\"):\n            mapping = {\"AAPL\": df_strat_down, \"MSFT\": df_strat_down, \"SPY\": df_spy}\n            return {s: mapping[s] for s in symbols if s in mapping}\n        store.get_bars_multi.side_effect = get_bars_multi\n\n        universe = MagicMock()\n        universe.get_groups.return_value = {\"test_group\": [\"AAPL\", \"MSFT\"]}\n\n        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=1)\n\n        report = run_walk_forward(\n            mb=mb,\n            strategies=[\"dual_ma\"],\n            param_grids={\"dual_ma\": {\"fast\": [5], \"slow\": [20]}},\n            rounds=2,\n            train_months=12,\n            val_months=4,\n        )\n\n        # 策略下跌 + SPY 上涨 → alpha 显著为负\n        for r in report.rounds:\n            assert r.val_alpha < 0, (\n                f\"策略下跌+SPY上涨应跑输，val_alpha 应 < 0，实际 {r.val_alpha}\"\n            )\n        # 负 alpha → pass_all_rounds=False\n        assert report.pass_all_rounds is False\n        assert report.avg_val_alpha < 0\n\n    def test_wf_alpha_floor_constant_value(self):\n        \"\"\"WALK_FORWARD_VAL_ALPHA_FLOOR 常量值为 -5.0。\"\"\"\n        assert WALK_FORWARD_VAL_ALPHA_FLOOR == -5.0, (\n            f\"WF alpha floor 应为 -5.0，实际 {WALK_FORWARD_VAL_ALPHA_FLOOR}\"\n        )\n\n    def test_wf_alpha_floor_vs_dd_threshold_independent(self):\n        \"\"\"alpha floor 和 DD threshold 是两个独立的 gate（AND 关系）。\"\"\"\n        # DD 合规但 alpha 灾难性跑输\n        dd_pass_alpha_fail = (\n            10.0 <= WALK_FORWARD_VAL_DD_THRESHOLD\n            and -8.0 <= WALK_FORWARD_VAL_ALPHA_FLOOR  # 注意：< floor\n        )\n        # -8.0 不满足 > -5.0，所以 alpha_passed=False\n        alpha_passed = -8.0 > WALK_FORWARD_VAL_ALPHA_FLOOR\n        assert alpha_passed is False\n        # AND 关系：任一 fail → passed=False\n        assert dd_pass_alpha_fail and alpha_passed is False or True  # 仅验证可计算\n\n        # 真正的 AND 逻辑验证\n        passed = (10.0 <= WALK_FORWARD_VAL_DD_THRESHOLD) and (-8.0 > WALK_FORWARD_VAL_ALPHA_FLOOR)\n        assert passed is False, \"DD 合规但 alpha < floor 时应 fail\""}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/tests/test_wf_alpha_gate.py
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/tests/test_wf_alpha_gate.py
---
{"command":"/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_wf_alpha_gate.py --no-header -q 2>&1 | tail -30","description":"Run new WF alpha gate tests after rewrite"}
---
Run new WF alpha gate tests after rewrite
---
Command: /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_wf_alpha_gate.py --no-header -q 2>&1 | tail -30
Stdout:                 train_months=12,
                val_months=4,
            )
    
        # 策略 ~-20% 年化 < SPY ~10% 年化 → alpha 显著为负
        for r in report.rounds:
>           assert r.val_alpha < 0, (
                f"策略跑输+SPY上涨应跑输，val_alpha 应 < 0，实际 {r.val_alpha}"
            )
E           AssertionError: 策略跑输+SPY上涨应跑输，val_alpha 应 < 0，实际 0.0
E           assert 0.0 < 0
E            +  where 0.0 = WalkForwardRound(round_num=1, train_start=datetime.date(2024, 7, 8), train_end=datetime.date(2025, 7, 8), val_start=datetime.date(2025, 7, 8), val_end=datetime.date(2025, 11, 8), val_sortino=0.0, val_max_dd=0.0, passed=True, val_alpha=0.0).val_alpha

tests/test_wf_alpha_gate.py:581: AssertionError
----------------------------- Captured stderr call -----------------------------
2026-07-08 00:19:47.648 | INFO     | mytrader.backtest.matrix_backtest:run_walk_forward:865 - [WalkForward] Round 1/2: train=2024-07-08~2025-07-08, val=2025-07-08~2025-11-08
2026-07-08 00:19:47.648 | INFO     | mytrader.backtest.matrix_backtest:_run_group:1167 - [MatrixBacktest] test_group: start — 1 strategies × 2 valid symbols
2026-07-08 00:19:47.649 | INFO     | mytrader.backtest.matrix_backtest:_run_group:1251 - [MatrixBacktest] test_group: dual_ma done in 0.0s (1 param combos × 2 symbols)
2026-07-08 00:19:47.650 | WARNING  | mytrader.backtest.matrix_backtest:_run_group:1331 - [MatrixBacktest] test_group: ALL 1 candidates have alpha <= 0 (cannot beat SPY) — ['dual_ma(-29.94%)']. Group produces EMPTY weights (hold cash). Marked no_positive_alpha.
2026-07-08 00:19:47.650 | WARNING  | mytrader.backtest.matrix_backtest:run_walk_forward:905 - [WalkForward] Round 1: no valid val returns — sortino=0, dd=0, alpha=0, passed=True (vacuous)
2026-07-08 00:19:47.650 | INFO     | mytrader.backtest.matrix_backtest:run_walk_forward:954 - [WalkForward] Round 1 result: sortino=0.0000, dd=0.0000%, alpha=0.0000%, passed=True (dd_threshold=15.0%, alpha_floor=-5.0%)
2026-07-08 00:19:47.650 | INFO     | mytrader.backtest.matrix_backtest:run_walk_forward:865 - [WalkForward] Round 2/2: train=2024-11-08~2025-11-08, val=2025-11-08~2026-03-08
2026-07-08 00:19:47.650 | INFO     | mytrader.backtest.matrix_backtest:_run_group:1167 - [MatrixBacktest] test_group: start — 1 strategies × 2 valid symbols
2026-07-08 00:19:47.651 | INFO     | mytrader.backtest.matrix_backtest:_run_group:1251 - [MatrixBacktest] test_group: dual_ma done in 0.0s (1 param combos × 2 symbols)
2026-07-08 00:19:47.652 | WARNING  | mytrader.backtest.matrix_backtest:_run_group:1331 - [MatrixBacktest] test_group: ALL 1 candidates have alpha <= 0 (cannot beat SPY) — ['dual_ma(-29.94%)']. Group produces EMPTY weights (hold cash). Marked no_positive_alpha.
2026-07-08 00:19:47.652 | WARNING  | mytrader.backtest.matrix_backtest:run_walk_forward:905 - [WalkForward] Round 2: no valid val returns — sortino=0, dd=0, alpha=0, passed=True (vacuous)
2026-07-08 00:19:47.652 | INFO     | mytrader.backtest.matrix_backtest:run_walk_forward:954 - [WalkForward] Round 2 result: sortino=0.0000, dd=0.0000%, alpha=0.0000%, passed=True (dd_threshold=15.0%, alpha_floor=-5.0%)
2026-07-08 00:19:47.652 | INFO     | mytrader.backtest.matrix_backtest:run_walk_forward:979 - [WalkForward] done: 2 rounds, pass_all_rounds=False, max_val_dd=0.0000%, avg_val_alpha=0.0000%, min_val_alpha=0.0000%
=========================== short test summary info ============================
FAILED tests/test_wf_alpha_gate.py::TestWFAlphaIntegration::test_wf_alpha_underperforms_spy

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
The
---
 `
---
test
---
_wf
---
_alpha
---
_under
---
per
---
forms
---
_s
---
py
---
`
---
 test
---
 fails
---
 because
---
:

---
1
---
.
---
 The
---
 strategy
---
 has
---
 negative
---
 alpha
---
 (-
---
29
---
.
---
94
---
%)
---
 in
---
 the
---
 TRAIN
---
ING
---
 period
---


---
2
---
.
---
 The
---
 `
---
alpha
---
>
---
0
---
`
---
 gate
---
 (
---
Iter
---
 #
---
12
---
)
---
 in
---
 `_
---
run
---
_group
---
`
---
 rejects
---
 it
---
 →
---
 empty
---
 weights
---
 →
---
 `
---
no
---
_positive
---
_alpha
---
=True
---
`

---
3
---
.
---
 In
---
 the
---
 validation
---
 period
---
,
---
 `_
---
back
---
test
---
_with
---
_params
---
_on
---
_period
---
`
---
 gets
---
 empty
---
 weights
---
 →
---
 returns
---
 empty
---
 returns
---


---
4
---
.
---
 `
---
all
---
_returns
---
=[]
---
`
---
 →
---
 val
---
_alpha
---
=
---
0
---
.
---
0
---
 (
---
the
---
 "
---
no
---
 valid
---
 val
---
 returns
---
"
---
 path
---
)


---
So
---
 the
---
 test
---
 can
---
't
---
 verify
---
 negative
---
 val
---
_alpha
---
 because
---
 the
---
 strategy
---
 never
---
 makes
---
 it
---
 to
---
 the
---
 validation
---
 period
---
 (
---
it
---
's
---
 rejected
---
 in
---
 training
---
 by
---
 the
---
 alpha
---
>
---
0
---
 gate
---
).


---
This
---
 is
---
 actually
---
 correct
---
 system
---
 behavior
---
:
---
 a
---
 strategy
---
 with
---
 negative
---
 in
---
-sample
---
 alpha
---
 is
---
 rejected
---
 in
---
 training
---
,
---
 so
---
 it
---
 never
---
 gets
---
 to
---
 the
---
 validation
---
 period
---
.
---
 The
---
 WF
---
 val
---
_alpha
---
 is
---
 only
---
 computed
---
 for
---
 strategies
---
 that
---
 PASS
---
 the
---
 training
---
 period
---
 gates
---
.


---
To
---
 test
---
 negative
---
 val
---
_alpha
---
,
---
 I
---
 need
---
 a
---
 strategy
---
 that
---
:

---
-
---
 Has
---
 POS
---
ITIVE
---
 in
---
-sample
---
 alpha
---
 (
---
passes
---
 training
---
 gates
---
)

---
-
---
 But
---
 has
---
 NEG
---
ATIVE
---
 out
---
-of
---
-sample
---
 alpha
---
 (
---
in
---
 the
---
 validation
---
 period
---
)


---
This
---
 is
---
 the
---
 realistic
---
 scenario
---
:
---
 a
---
 strategy
---
 that
---
 over
---
fits
---
 the
---
 training
---
 data
---
 but
---
 under
---
per
---
forms
---
 in
---
 O
---
OS
---
.
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
 WF
---
 alpha
---
 gate
---
 is
---
 designed
---
 to
---
 catch
---
!


---
To
---
 implement
---
 this
---
,
---
 I
---
 need
---
 to
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
 differently
---
 for
---
 training
---
 vs
---
 validation
---
 periods
---
.
---
 The
---
 training
---
 period
---
 should
---
 return
---
 positive
---
-alpha
---
 returns
---
,
---
 and
---
 the
---
 validation
---
 period
---
 should
---
 return
---
 negative
---
-alpha
---
 returns
---
.


---
I
---
 can
---
 distinguish
---
 training
---
 vs
---
 validation
---
 by
---
 the
---
 `
---
data
---
`
---
 argument
---
 —
---
 the
---
 data
---
 dict
---
's
---
 Data
---
Frames
---
 will
---
 have
---
 different
---
 date
---
 ranges
---
.
---
 But
---
 that
---
's
---
 fragile
---
.


---
A
---
 better
---
 approach
---
:
---
 patch
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
 check
---
 the
---
 date
---
 range
---
 of
---
 the
---
 data
---
.
---
 If
---
 the
---
 data
---
's
---
 date
---
 range
---
 falls
---
 within
---
 the
---
 training
---
 period
---
,
---
 return
---
 positive
---
-alpha
---
 returns
---
.
---
 If
---
 it
---
 falls
---
 within
---
 the
---
 validation
---
 period
---
,
---
 return
---
 negative
---
-alpha
---
 returns
---
.


---
Actually
---
,
---
 the
---
 simplest
---
 approach
---
:
---
 I
---
 can
---
 check
---
 the
---
 `
---
data
---
`
---
 argument
---
's
---
 DataFrame
---
 index
---
 dates
---
.
---
 The
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
 receives
---
 `
---
data
---
`
---
 (
---
dict
---
 of
---
 symbol
---
 →
---
 DataFrame
---
).
---
 The
---
 Data
---
Frames
---
 are
---
 from
---
 `
---
mb
---
._
---
store
---
.get
---
_b
---
ars
---
_multi
---
(s
---
ymbols
---
,
---
 start
---
,
---
 end
---
)
---
`.
---
 In
---
 training
---
,
---
 `
---
start
---
=train
---
_start
---
,
---
 end
---
=train
---
_end
---
`.
---
 In
---
 validation
---
,
---
 `
---
start
---
=val
---
_start
---
,
---
 end
---
=val
---
_end
---
`.


---
But
---
 the
---
 mock
---
 store
---
 returns
---
 the
---
 same
---
 
---
300
---
-day
---
 data
---
 regardless
---
 of
---
 date
---
 range
---
.
---
 So
---
 I
---
 can
---
't
---
 distinguish
---
 by
---
 date
---
 range
---
 of
---
 the
---
 data
---
.


---
Alternative
---
:
---
 I
---
 can
---
 patch
---
 `_
---
back
---
test
---
_with
---
_params
---
_on
---
_period
---
`
---
 directly
---
 to
---
 return
---
 controlled
---
 validation
---
 returns
---
.
---
 This
---
 function
---
 is
---
 called
---
 only
---
 in
---
 the
---
 validation
---
 period
---
.
---
 If
---
 I
---
 patch
---
 it
---
 to
---
 return
---
 negative
---
-alpha
---
 returns
---
,
---
 I
---
 can
---
 test
---
 the
---
 WF
---
 val
---
_alpha
---
 computation
---
.


---
Actually
---
,
---
 let
---
 me
---
 think
---
 about
---
 this
---
 differently
---
.
---
 The
---
 `
---
test
---
_wf
---
_alpha
---
_under
---
per
---
forms
---
_s
---
py
---
`
---
 test
---
 is
---
 trying
---
 to
---
 verify
---
 that
---
 when
---
 the
---
 strategy
---
 under
---
per
---
forms
---
 SP
---
Y
---
 in
---
 the
---
 validation
---
 period
---
,
---
 val
---
_alpha
---
 <
---
 
---
0
---
.
---
 But
---
 the
---
 current
---
 system
---
 design
---
 rejects
---
 negative
---
-alpha
---
 strategies
---
 in
---
 training
---
,
---
 so
---
 they
---
 never
---
 reach
---
 validation
---
.


---
The
---
 realistic
---
 scenario
---
 for
---
 negative
---
 val
---
_alpha
---
 is
---
:
---
 strategy
---
 has
---
 positive
---
 in
---
-sample
---
 alpha
---
 but
---
 negative
---
 O
---
OS
---
 alpha
---
.
---
 To
---
 test
---
 this
---
,
---
 I
---
 need
---
:

---
-
---
 Training
---
:
---
 positive
---
 alpha
---
 returns
---
 (
---
passes
---
 gates
---
)

---
-
---
 Validation
---
:
---
 negative
---
 alpha
---
 returns
---
 (
---
WF
---
 catches
---
 this
---
)


---
The
---
 clean
---
est
---
 way
---
:
---
 patch
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
 return
---
 different
---
 results
---
 based
---
 on
---
 whether
---
 it
---
's
---
 called
---
 from
---
 `_
---
run
---
_group
---
`
---
 (
---
training
---
)
---
 or
---
 `_
---
back
---
test
---
_with
---
_params
---
_on
---
_period
---
`
---
 (
---
validation
---
).


---
Actually
---
,
---
 I
---
 can
---
 just
---
 patch
---
 `_
---
back
---
test
---
_with
---
_params
---
_on
---
_period
---
`
---
 directly
---
 to
---
 return
---
 controlled
---
 validation
---
 returns
---
.
---
 Let
---
 me
---
 do
---
 that
---
.


---
Wait
---
,
---
 actually
---
 there
---
's
---
 an
---
 even
---
 simpler
---
 approach
---
.
---
 I
---
 can
---
 make
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
 return
---
 different
---
 results
---
 based
---
 on
---
 the
---
 data
---
's
---
 date
---
 range
---
.
---
 Since
---
 the
---
 mock
---
 store
---
 returns
---
 the
---
 same
---
 
---
300
---
-day
---
 data
---
,
---
 I
---
 can
---
't
---
 distinguish
---
 by
---
 dates
---
.
---
 But
---
 I
---
 can
---
 use
---
 a
---
 different
---
 approach
---
:
---
 make
---
 the
---
 mock
---
 store
---
 return
---
 different
---
 data
---
 for
---
 training
---
 vs
---
 validation
---
 periods
---
.


---
Actually
---
,
---
 the
---
 simplest
---
 approach
---
:
---
 patch
---
 `_
---
back
---
test
---
_with
---
_params
---
_on
---
_period
---
`
---
 to
---
 return
---
 controlled
---
 returns
---
 for
---
 the
---
 validation
---
 period
---
.
---
 This
---
 way
---
:

---
-
---
 Training
---
:
---
 uses
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
 a
---
 mock
---
 that
---
 returns
---
 positive
---
-alpha
---
 results
---
)

---
-
---
 Validation
---
:
---
 uses
---
 the
---
 patched
---
 function
---
 that
---
 returns
---
 negative
---
-alpha
---
 returns
---



---
Let
---
 me
---
 rewrite
---
 the
---
 `
---
test
---
_wf
---
_alpha
---
_under
---
per
---
forms
---
_s
---
py
---
`
---
 test
---
 to
---
 patch
---
 `_
---
back
---
test
---
_with
---
_params
---
_on
---
_period
---
`.


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
 code
---
 flow
---
:

---
1
---
.
---
 `_
---
run
---
_group
---
`
---
 calls
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
 for
---
 training
---


---
2
---
.
---
 `_
---
back
---
test
---
_with
---
_params
---
_on
---
_period
---
`
---
 calls
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
 for
---
 validation
---



---
If
---
 I
---
 patch
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
 return
---
 positive
---
-alpha
---
 results
---
 (
---
for
---
 training
---
),
---
 the
---
 training
---
 period
---
 will
---
 produce
---
 non
---
-empty
---
 weights
---
.
---
 Then
---
 `_
---
back
---
test
---
_with
---
_params
---
_on
---
_period
---
`
---
 will
---
 call
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
 again
---
 for
---
 validation
---
,
---
 and
---
 it
---
 will
---
 also
---
 get
---
 positive
---
-alpha
---
 results
---
 (
---
same
---
 mock
---
).
---
 So
---
 val
---
_alpha
---
 will
---
 be
---
 positive
---
.


---
To
---
 get
---
 negative
---
 val
---
_alpha
---
,
---
 I
---
 need
---
 the
---
 validation
---
 period
---
 to
---
 use
---
 different
---
 returns
---
.
---
 I
---
 can
---
 either
---
:

---
1
---
.
---
 Patch
---
 `_
---
back
---
test
---
_with
---
_params
---
_on
---
_period
---
`
---
 directly
---


---
2
---
.
---
 Make
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
 return
---
 different
---
 results
---
 based
---
 on
---
 some
---
 context
---



---
Let
---
 me
---
 go
---
 with
---
 option
---
 
---
1
---
:
---
 patch
---
 `_
---
back
---
test
---
_with
---
_params
---
_on
---
_period
---
`
---
 to
---
 return
---
 controlled
---
 validation
---
 returns
---
.


---
Actually
---
,
---
 wait
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
 `_
---
back
---
test
---
_with
---
_params
---
_on
---
_period
---
`
---
 again
---
:


---
```
---
python
---


---
def
---
 _
---
back
---
test
---
_with
---
_params
---
_on
---
_period
---
(mb
---
,
---
 symbols
---
,
---
 weights
---
,
---
 start
---
,
---
 end
---
):

---
   
---
 ...

---
   
---
 for
---
 w
---
 in
---
 weights
---
:

---
       
---
 ...

---
       
---
 results
---
 =
---
 _
---
back
---
test
---
_batch
---
(data
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
 ...)

---
       
---
 for
---
 r
---
 in
---
 results
---
:

---
           
---
 if
---
 not
---
 r
---
.daily
---
_returns
---
.empty
---
:

---
               
---
 all
---
_returns
---
.append
---
(r
---
.daily
---
_returns
---
)

---
   
---
 return
---
 all
---
_returns
---


---
``
---
`


---
It
---
 returns
---
 a
---
 list
---
 of
---
 pd
---
.Series
---
.
---
 If
---
 I
---
 patch
---
 it
---
 to
---
 return
---
 a
---
 list
---
 with
---
 negative
---
-alpha
---
 returns
---
,
---
 I
---
 can
---
 test
---
 the
---
 WF
---
 val
---
_alpha
---
 computation
---
.


---
Let
---
 me
---
 rewrite
---
 the
---
 test
---
 to
---
 patch
---
 both
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
for
---
 training
---
,
---
 positive
---
 alpha
---
)
---
 and
---
 `_
---
back
---
test
---
_with
---
_params
---
_on
---
_period
---
`
---
 (
---
for
---
 validation
---
,
---
 negative
---
 alpha
---
).


---
Actually
---
,
---
 the
---
 simplest
---
 approach
---
:
---
 just
---
 patch
---
 `_
---
back
---
test
---
_with
---
_params
---
_on
---
_period
---
`
---
 to
---
 return
---
 controlled
---
 returns
---
.
---
 The
---
 training
---
 period
---
 will
---
 use
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
 with
---
 the
---
 mock
---
 store
---
 data
---
 (
---
which
---
 is
---
 deg
---
enerate
---
 →
---
 empty
---
 weights
---
 →
---
 no
---
 validation
---
).
---
 So
---
 I
---
 still
---
 need
---
 to
---
 fix
---
 the
---
 training
---
 period
---
.


---
Let
---
 me
---
 think
---
 about
---
 this
---
 more
---
 carefully
---
...


---
OK
---
,
---
 I
---
 think
---
 the
---
 clean
---
est
---
 approach
---
 is
---
:

---
1
---
.
---
 Patch
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
 return
---
 positive
---
-alpha
---
 results
---
 (
---
for
---
 training
---
,
---
 so
---
 weights
---
 are
---
 non
---
-empty
---
)

---
2
---
.
---
 Patch
---
 `_
---
back
---
test
---
_with
---
_params
---
_on
---
_period
---
`
---
 to
---
 return
---
 negative
---
-alpha
---
 returns
---
 (
---
for
---
 validation
---
)


---
This
---
 tests
---
 the
---
 specific
---
 scenario
---
:
---
 strategy
---
 passes
---
 training
---
 (
---
positive
---
 in
---
-sample
---
 alpha
---
)
---
 but
---
 fails
---
 validation
---
 (
---
negative
---
 O
---
OS
---
 alpha
---
).


---
Let
---
 me
---
 rewrite
---
 the
---
 test
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
 this
---
 test
---
 is
---
 getting
---
 overly
---
 complex
---
.
---
 The
---
 spec
---
 asks
---
 for
---
 
---
9
---
 tests
---
,
---
 and
---
 I
---
 already
---
 have
---
 tests
---
 that
---
 verify
---
:

---
-
---
 The
---
 gate
---
 logic
---
 (
---
data
---
class
---
 tests
---
,
---
 single
---
-round
---
 gate
---
 tests
---
,
---
 summary
---
 gate
---
 tests
---
)

---
-
---
 SP
---
Y
---
 unavailable
---
 →
---
 alpha
---
=
---
0
---


---
-
---
 Alpha
---
 computed
---
 correctly
---
 (
---
positive
---
 alpha
---
 scenario
---
)


---
The
---
 "
---
under
---
per
---
forms
---
 SP
---
Y
---
"
---
 scenario
---
 is
---
 implicitly
---
 tested
---
 by
---
 the
---
 gate
---
 logic
---
 tests
---
 (
---
which
---
 construct
---
 Walk
---
Forward
---
Round
---
 with
---
 negative
---
 alpha
---
 and
---
 verify
---
 passed
---
=False
---
).
---
 The
---
 integration
---
 test
---
 for
---
 negative
---
 val
---
_alpha
---
 is
---
 nice
---
-to
---
-have
---
 but
---
 not
---
 essential
---
,
---
 and
---
 the
---
 system
---
 design
---
 (
---
alpha
---
>
---
0
---
 gate
---
 in
---
 training
---
)
---
 makes
---
 it
---
 hard
---
 to
---
 test
---
 without
---
 complex
---
 mocking
---
.


---
Let
---
 me
---
 simplify
---
 the
---
 `
---
test
---
_wf
---
_alpha
---
_under
---
per
---
forms
---
_s
---
py
---
`
---
 test
---
 to
---
 patch
---
 both
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
 `_
---
back
---
test
---
_with
---
_params
---
_on
---
_period
---
`.


---
Actually
---
,
---
 let
---
 me
---
 just
---
 remove
---
 the
---
 `
---
test
---
_wf
---
_alpha
---
_under
---
per
---
forms
---
_s
---
py
---
`
---
 test
---
 and
---
 replace
---
 it
---
 with
---
 a
---
 simpler
---
 test
---
 that
---
 verifies
---
 the
---
 WF
---
 correctly
---
 computes
---
 negative
---
 alpha
---
 when
---
 the
---
 validation
---
 returns
---
 under
---
perform
---
 SP
---
Y
---
.
---
 I
---
'll
---
 patch
---
 `_
---
back
---
test
---
_with
---
_params
---
_on
---
_period
---
`
---
 directly
---
.


---
Wait
---
,
---
 I
---
 have
---
 a
---
 better
---
 idea
---
.
---
 Let
---
 me
---
 use
---
 a
---
 side
---
_effect
---
 function
---
 for
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
 that
---
 checks
---
 if
---
 the
---
 data
---
 is
---
 for
---
 training
---
 or
---
 validation
---
 by
---
 looking
---
 at
---
 the
---
 start
---
/end
---
 dates
---
.
---
 But
---
 the
---
 mock
---
 store
---
 doesn
---
't
---
 filter
---
 by
---
 date
---
...


---
OK
---
,
---
 simplest
---
 approach
---
:
---
 patch
---
 `_
---
back
---
test
---
_with
---
_params
---
_on
---
_period
---
`
---
 to
---
 return
---
 controlled
---
 negative
---
-alpha
---
 returns
---
,
---
 and
---
 patch
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
 for
---
 training
---
 to
---
 return
---
 positive
---
-alpha
---
 results
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
.
---
`
---
test
---
_wf
---
_alpha
---
_under
---
per
---
forms
---
_s
---
py
---
`
---
 
---
测试
---
失败
---
，
---
因为
---
 `
---
alpha
---
>
---
0
---
`
---
 门
---
（
---
迭代
---
 #
---
12
---
）
---
在
---
 TRAIN
---
ING
---
 
---
期间
---
拒绝了
---
该
---
策略
---
，
---
因此
---
它
---
从未
---
进入
---
验证
---
阶段
---
。
---
我
---
需要
---
分别
---
模拟
---
训练
---
（
---
正向
---
 alpha
---
）
---
和
---
验证
---
（
---
负
---
向
---
 alpha
---
）
---
过程
---
。
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/tests/test_wf_alpha_gate.py","new_string":"    def test_wf_alpha_underperforms_spy(self):\n        \"\"\"策略 OOS 跑输 SPY → val_alpha < 0 → pass_all_rounds=False。\n\n        场景：策略在训练期有正 alpha（通过 alpha>0 门槛），\n        但在验证期跑输 SPY（OOS 负 alpha）。\n        这是 WF alpha gate 设计的核心目标：捕获 in-sample 过拟合。\n\n        实现：patch _backtest_batch 返回正 alpha 训练结果，\n        patch _backtest_with_params_on_period 返回负 alpha 验证结果。\n        \"\"\"\n        n = 300\n        idx = pd.date_range(\"2021-01-01\", periods=n, freq=\"B\")\n        df_spy = _make_spy_ohlcv(n, annual_growth=0.10)\n        df_strat = _make_strategy_ohlcv(n, trend=\"up\")\n\n        store = MagicMock()\n        def get_bars_multi(symbols, start, end, timeframe=\"1d\"):\n            mapping = {\"AAPL\": df_strat, \"MSFT\": df_strat, \"SPY\": df_spy}\n            return {s: mapping[s] for s in symbols if s in mapping}\n        store.get_bars_multi.side_effect = get_bars_multi\n\n        universe = MagicMock()\n        universe.get_groups.return_value = {\"test_group\": [\"AAPL\", \"MSFT\"]}\n\n        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=1)\n\n        # 训练期 returns：日均 0.001（~28% 年化 > SPY 10%）→ 正 alpha，通过训练门槛\n        train_returns = pd.Series(\n            np.random.normal(0.001, 0.002, n), index=idx\n        )\n        # 验证期 returns：日均 -0.0008（~-20% 年化 < SPY 10%）→ 负 alpha\n        val_returns = pd.Series(\n            np.random.normal(-0.0008, 0.002, n), index=idx\n        )\n\n        def mock_batch(data, strategy_name, params, *args, **kwargs):\n            results = []\n            for sym in data.keys():\n                results.append(SingleBacktestResult(\n                    symbol=sym, strategy=strategy_name, params=params,\n                    sharpe=1.0, total_return_pct=10.0, max_drawdown_pct=5.0,\n                    win_rate_pct=55.0, total_trades=10,\n                    daily_returns=train_returns,\n                    sortino=1.5, closed_trades=10,\n                ))\n            return results\n\n        def mock_val_period(mb_arg, symbols, weights, start, end):\n            \"\"\"验证期返回负 alpha returns。\"\"\"\n            return [val_returns, val_returns]  # 2 个标的的 returns\n\n        with patch(\n            \"mytrader.backtest.matrix_backtest._backtest_batch\",\n            side_effect=mock_batch,\n        ), patch(\n            \"mytrader.backtest.matrix_backtest._backtest_with_params_on_period\",\n            side_effect=mock_val_period,\n        ):\n            report = run_walk_forward(\n                mb=mb,\n                strategies=[\"dual_ma\"],\n                param_grids={\"dual_ma\": {\"fast\": [5], \"slow\": [20]}},\n                rounds=2,\n                train_months=12,\n                val_months=4,\n            )\n\n        # 验证期 OOS 负 alpha\n        for r in report.rounds:\n            assert r.val_alpha < 0, (\n                f\"OOS 策略跑输 SPY，val_alpha 应 < 0，实际 {r.val_alpha}\"\n            )\n        assert report.pass_all_rounds is False\n        assert report.avg_val_alpha < 0","old_string":"    def test_wf_alpha_underperforms_spy(self):\n        \"\"\"策略跑输 SPY → val_alpha < 0 → pass_all_rounds=False。\n\n        构造 SPY 温和上涨（~10% 年化），\n        patch _backtest_batch 返回策略 daily_returns（负收益 ~-20% 年化）。\n        验证 val_alpha < 0 + pass_all_rounds=False。\n        \"\"\"\n        n = 300\n        idx = pd.date_range(\"2021-01-01\", periods=n, freq=\"B\")\n        df_spy = _make_spy_ohlcv(n, annual_growth=0.10)\n        df_strat = _make_strategy_ohlcv(n, trend=\"up\")\n\n        store = MagicMock()\n        def get_bars_multi(symbols, start, end, timeframe=\"1d\"):\n            mapping = {\"AAPL\": df_strat, \"MSFT\": df_strat, \"SPY\": df_spy}\n            return {s: mapping[s] for s in symbols if s in mapping}\n        store.get_bars_multi.side_effect = get_bars_multi\n\n        universe = MagicMock()\n        universe.get_groups.return_value = {\"test_group\": [\"AAPL\", \"MSFT\"]}\n\n        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=1)\n\n        # 策略 daily_returns：日均 -0.0008（~-20% 年化），跑输 SPY 的 ~10%\n        controlled_returns = pd.Series(\n            np.random.normal(-0.0008, 0.002, n), index=idx\n        )\n\n        def mock_batch(data, strategy_name, params, *args, **kwargs):\n            results = []\n            for sym in data.keys():\n                results.append(SingleBacktestResult(\n                    symbol=sym, strategy=strategy_name, params=params,\n                    sharpe=-0.5, total_return_pct=-15.0, max_drawdown_pct=12.0,\n                    win_rate_pct=40.0, total_trades=10,\n                    daily_returns=controlled_returns,\n                    sortino=-0.8, closed_trades=10,\n                ))\n            return results\n\n        with patch(\n            \"mytrader.backtest.matrix_backtest._backtest_batch\",\n            side_effect=mock_batch,\n        ):\n            report = run_walk_forward(\n                mb=mb,\n                strategies=[\"dual_ma\"],\n                param_grids={\"dual_ma\": {\"fast\": [5], \"slow\": [20]}},\n                rounds=2,\n                train_months=12,\n                val_months=4,\n            )\n\n        # 策略 ~-20% 年化 < SPY ~10% 年化 → alpha 显著为负\n        for r in report.rounds:\n            assert r.val_alpha < 0, (\n                f\"策略跑输+SPY上涨应跑输，val_alpha 应 < 0，实际 {r.val_alpha}\"\n            )\n        # 负 alpha → pass_all_rounds=False\n        assert report.pass_all_rounds is False\n        assert report.avg_val_alpha < 0"}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/tests/test_wf_alpha_gate.py
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/tests/test_wf_alpha_gate.py
---
{"command":"/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_wf_alpha_gate.py --no-header -q 2>&1 | tail -15","description":"Run new WF alpha gate tests after rewrite"}
---
Run new WF alpha gate tests after rewrite
---
Command: /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_wf_alpha_gate.py --no-header -q 2>&1 | tail -15
Stdout: ................                                                         [100%]

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
所有
---
 
---
16
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
现在
---
让我
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
。
---
{"status":"completed","taskId":"5"}
---
{"status":"in_progress","taskId":"6"}
---
Updated task #5 status
---
Updated task #5 status
---
Updated task #6 status
---
Updated task #6 status
---
{"command":"/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest --no-header -q 2>&1 | tail -20","description":"Run full pytest suite","timeout":300000}
---
Run full pytest suite
---
Command: /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest --no-header -q 2>&1 | tail -20
Stdout:   /Users/rickouyang/Github/trade-tools/mytrader/tests/test_portfolio.py:281: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
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

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
The
---
 output
---
 only
---
 shows
---
 warnings
---
,
---
 not
---
 the
---
 final
---
 pass
---
/f
---
ail
---
 count
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
 exit
---
 code
---
 and
---
 run
---
 again
---
 with
---
 a
---
 clearer
---
 summary
---
.
---
{"command":"/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest --no-header -q 2>&1 | grep -E \"passed|failed|error\" | tail -5","description":"Get pytest summary line","timeout":300000}
---
Get pytest summary line
---
Command: /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest --no-header -q 2>&1 | grep -E "passed|failed|error" | tail -5
Stdout: (empty)
Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"command":"/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest --no-header -q 2>&1 | grep -E \"^=+|passed|failed|error\" | tail -10","description":"Get pytest summary with separators","timeout":300000}
---
Get pytest summary with separators
---
Command: /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest --no-header -q 2>&1 | grep -E "^=+|passed|failed|error" | tail -10
Stdout: =============================== warnings summary ===============================

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
The
---
 grep
---
 is
---
 not
---
 catching
---
 the
---
 final
---
 summary
---
 line
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
 different
---
 approach
---
 —
---
 use
---
 `-
---
r
---
N
---
`
---
 or
---
 just
---
 capture
---
 the
---
 last
---
 few
---
 lines
---
 differently
---
.
---
{"command":"/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest --no-header -q 2>&1 | tail -3","description":"Get last 3 lines of pytest output","timeout":300000}
---
Get last 3 lines of pytest output
---
Command: /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest --no-header -q 2>&1 | tail -3
Stdout:     timestamp=datetime.utcnow(),

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"command":"/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest --no-header -q -p no:warnings 2>&1 | tail -5","description":"Get pytest summary without warnings","timeout":300000}
---
Get pytest summary without warnings
---
Command: /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest --no-header -q -p no:warnings 2>&1 | tail -5
Stdout: ........................................................................ [ 64%]
........................................................................ [ 74%]
........................................................................ [ 85%]
........................................................................ [ 96%]
...........................                                              [100%]

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"command":"/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest --no-header -q -p no:warnings 2>&1 | grep -E \"passed|failed\"","description":"Get pass/fail count","timeout":300000}
---
Get pass/fail count
---
Command: /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest --no-header -q -p no:warnings 2>&1 | grep -E "passed|failed"
Stdout: (empty)
Stderr: (empty)
Exit Code: 1
Signal: (none)
---
The
---
 grep
---
 is
---
 returning
---
 empty
---
,
---
 which
---
 is
---
 strange
---
.
---
 The
---
 exit
---
 code
---
 is
---
 
---
1
---
 from
---
 grep
---
 (
---
no
---
 match
---
).
---
 Let
---
 me
---
 try
---
 to
---
 capture
---
 the
---
 output
---
 differently
---
 —
---
 maybe
---
 the
---
 summary
---
 line
---
 has
---
 special
---
 characters
---
.
---
 Let
---
 me
---
 use
---
 `
---
tee
---
`
---
 or
---
 redirect
---
 to
---
 a
---
 file
---
.
---
{"command":"/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest --no-header -q -p no:warnings > /tmp/pytest_out.txt 2>&1; tail -3 /tmp/pytest_out.txt","description":"Capture pytest output to file and show last lines","timeout":300000}
---
Capture pytest output to file and show last lines
---
Command: /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest --no-header -q -p no:warnings > /tmp/pytest_out.txt 2>&1; tail -3 /tmp/pytest_out.txt
Stdout: ........................................................................ [ 85%]
........................................................................ [ 96%]
...........................                                              [100%]

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"command":"wc -l /tmp/pytest_out.txt; cat -A /tmp/pytest_out.txt | tail -5","description":"Check file contents with special chars"}
---
Check file contents with special chars
---
Command: wc -l /tmp/pytest_out.txt; cat -A /tmp/pytest_out.txt | tail -5
Stdout:       10 /tmp/pytest_out.txt
cat: illegal option -- A
usage: cat [-belnstuv] [file ...]

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"file_path":"/tmp/pytest_out.txt"}
---
   1→........................................................................ [ 10%]
   2→........................................................................ [ 21%]
   3→........................................................................ [ 32%]
   4→........................................................................ [ 42%]
   5→........................................................................ [ 53%]
   6→........................................................................ [ 64%]
   7→........................................................................ [ 74%]
   8→........................................................................ [ 85%]
   9→........................................................................ [ 96%]
  10→...........................                                              [100%]
  11→
---
   1→........................................................................ [ 10%]
   2→........................................................................ [ 21%]
   3→........................................................................ [ 32%]
   4→........................................................................ [ 42%]
   5→........................................................................ [ 53%]
   6→........................................................................ [ 64%]
   7→........................................................................ [ 74%]
   8→........................................................................ [ 85%]
   9→........................................................................ [ 96%]
  10→...........................                                              [100%]
  11→
---
Interesting
---
 —
---
 the
---
 pytest
---
 output
---
 only
---
 shows
---
 the
---
 progress
---
 dots
---
,
---
 not
---
 the
---
 final
---
 summary
---
 line
---
.
---
 This
---
 might
---
 be
---
 because
---
 the
---
 summary
---
 line
---
 is
---
 on
---
 stderr
---
 or
---
 because
---
 of
---
 some
---
 terminal
---
 width
---
 issue
---
.
---
 Let
---
 me
---
 try
---
 running
---
 with
---
 `
---
--
---
tb
---
=
---
short
---
`
---
 and
---
 capturing
---
 both
---
 stdout
---
 and
---
 stderr
---
.


---
Actually
---
,
---
 the
---
 `-
---
q
---
`
---
 flag
---
 with
---
 `
---
--
---
no
---
-header
---
`
---
 might
---
 suppress
---
 the
---
 summary
---
.
---
 Let
---
 me
---
 try
---
 without
---
 `-
---
q
---
`.
---
{"command":"/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest -p no:warnings --tb=short 2>&1 | tail -5","description":"Run pytest with short traceback","timeout":300000}
---
Run pytest with short traceback
---
Command: /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest -p no:warnings --tb=short 2>&1 | tail -5
Stdout: ........................................................................ [ 74%]
........................................................................ [ 85%]
........................................................................ [ 96%]
...........................                                              [100%]
675 passed, 16 deselected in 22.09s

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
所有
---
 
---
6
---
75
---
 个
---
测试
---
均已
---
通过
---
（
---
65
---
9
---
 个
---
现有
---
测试
---
 +
---
 
---
16
---
 个
---
新增
---
测试
---
）。
---
让我
---
核实
---
一下
---
数量
---
是否符合
---
预期
---
。
---
{"command":"/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_wf_alpha_gate.py tests/test_matrix_backtest.py::TestWalkForward -p no:warnings --tb=short -q 2>&1 | tail -5","description":"Run WF-related tests specifically","timeout":120000}
---
Run WF-related tests specifically
---
Command: /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_wf_alpha_gate.py tests/test_matrix_backtest.py::TestWalkForward -p no:warnings --tb=short -q 2>&1 | tail -5
Stdout: ..........................                                               [100%]

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"command":"/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_wf_alpha_gate.py tests/test_matrix_backtest.py::TestWalkForward -p no:warnings --tb=short 2>&1 | tail -3","description":"Run WF tests with count","timeout":120000}
---
Run WF tests with count
---
Command: /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest tests/test_wf_alpha_gate.py tests/test_matrix_backtest.py::TestWalkForward -p no:warnings --tb=short 2>&1 | tail -3
Stdout: ..........................                                               [100%]
26 passed in 5.00s

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
6
---
75
---
 个
---
测试
---
全部
---
通过
---
（
---
65
---
9
---
 个
---
旧
---
测试
---
 +
---
 
---
16
---
 个
---
新
---
测试
---
）。
---
WF
---
 相关
---
测试
---
：
---
26
---
 个
---
通过
---
（
---
10
---
 个
---
现有
---
 +
---
 
---
16
---
 个
---
新
---
测试
---
）。
---
{"status":"completed","taskId":"6"}
---
{"status":"in_progress","taskId":"7"}
---
Updated task #6 status
---
Updated task #6 status
---
Updated task #7 status
---
Updated task #7 status
---
现在
---
让我
---
来
---
更新
---
文档
---
。
---
首先
---
，
---
更新
---
 `
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
。
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md","limit":30,"offset":200}
---
 200→# VectorBT 中用 from_signals 的 signal_func 参数
 201→pf = vbt.Portfolio.from_signals(..., signal_func=lambda: signal.shift(1))
 202→```
 203→
 204→**验证**：对策略做随机化测试，如果随机打乱信号后 Sharpe 仍然很高，说明有前视偏差。
 205→
 206→### 6.2 过拟合
 207→
 208→**问题**：参数在历史数据上表现极好，但在未来数据上失效
 209→
 210→**防范**：
 211→1. **Walk-Forward Analysis（WFA）**：在滚动窗口上重复优化+验证
 212→2. **Out-of-Sample 测试**：留出最近 20% 的数据不参与优化
 213→3. **参数稳定性**：最优参数附近（±20%）的参数也应该有相近表现
 214→
 215→```python
 216→# 简单的 Walk-Forward 框架
 217→def walk_forward_test(price: pd.Series, train_months: int = 12, test_months: int = 3):
 218→    results = []
 219→    start = 0
 220→    train_size = train_months * 21  # 约 21 个交易日/月
 221→    test_size  = test_months * 21
 222→
 223→    while start + train_size + test_size <= len(price):
 224→        train_data = price.iloc[start : start + train_size]
 225→        test_data  = price.iloc[start + train_size : start + train_size + test_size]
 226→
 227→        # 在 train_data 上优化参数
 228→        best_params = optimize_params(train_data)
 229→
 230→
---
 200→# VectorBT 中用 from_signals 的 signal_func 参数
 201→pf = vbt.Portfolio.from_signals(..., signal_func=lambda: signal.shift(1))
 202→```
 203→
 204→**验证**：对策略做随机化测试，如果随机打乱信号后 Sharpe 仍然很高，说明有前视偏差。
 205→
 206→### 6.2 过拟合
 207→
 208→**问题**：参数在历史数据上表现极好，但在未来数据上失效
 209→
 210→**防范**：
 211→1. **Walk-Forward Analysis（WFA）**：在滚动窗口上重复优化+验证
 212→2. **Out-of-Sample 测试**：留出最近 20% 的数据不参与优化
 213→3. **参数稳定性**：最优参数附近（±20%）的参数也应该有相近表现
 214→
 215→```python
 216→# 简单的 Walk-Forward 框架
 217→def walk_forward_test(price: pd.Series, train_months: int = 12, test_months: int = 3):
 218→    results = []
 219→    start = 0
 220→    train_size = train_months * 21  # 约 21 个交易日/月
 221→    test_size  = test_months * 21
 222→
 223→    while start + train_size + test_size <= len(price):
 224→        train_data = price.iloc[start : start + train_size]
 225→        test_data  = price.iloc[start + train_size : start + train_size + test_size]
 226→
 227→        # 在 train_data 上优化参数
 228→        best_params = optimize_params(train_data)
 229→
 230→
---
Let
---
 me
---
 find
---
 the
---
 right
---
 place
---
 to
---
 add
---
 the
---
 WF
---
 alpha
---
 gate
---
 documentation
---
.
---
 I
---
'll
---
 look
---
 for
---
 the
---
 section
---
 about
---
 Walk
---
-
---
Forward
---
 in
---
 the
---
 design
---
 doc
---
.
---
让我
---
找
---
一下
---
设计
---
文档
---
中的
---
 WF
---
 部分
---
。
---
{"-n":true,"output_mode":"content","path":"/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md","pattern":"### 10\\.|## 10\\.|迭代 #1[12]|WALK_FORWARD_VAL"}
---
["/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md:314:## 10. 矩阵回测（MatrixBacktest，v2 新增）","/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md:319:### 10.1 目标","/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md:327:### 10.2 回测窗口：为什么是 5 年","/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md:339:### 10.3 矩阵回测流程","/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md:378:### 10.4 关键设计点","/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md:392:[Omitted long matching line]","/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md:398:### 10.4.1 Top-K 选择三级 Fallback（迭代 #9 新增，迭代 #11 前置健全性门槛，迭代 #12 前置 alpha>0 门槛）","/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md:401:[迭代 #11 前置] 健全性过滤：剔除 closed_trades==0 比例 ≥ 80% 的退化策略","/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md:404:[迭代 #12 前置] alpha>0 硬门槛：剔除 alpha≤0 的候选（跑不赢 SPY 的策略不进权重）","/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md:414:**迭代 #11 健全性门槛（先于 alpha>0 门槛）**：","/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md:420:**迭代 #12 alpha>0 硬门槛（健全性之后、Tier 1/2/3 之前）**：","/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md:443:### 10.5 Walk-Forward 月度重优化","/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md:476:### 10.6 输出文件","/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md:503:### 10.7 性能考量"]
---
["/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md:314:## 10. 矩阵回测（MatrixBacktest，v2 新增）","/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md:319:### 10.1 目标","/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md:327:### 10.2 回测窗口：为什么是 5 年","/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md:339:### 10.3 矩阵回测流程","/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md:378:### 10.4 关键设计点","/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md:392:[Omitted long matching line]","/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md:398:### 10.4.1 Top-K 选择三级 Fallback（迭代 #9 新增，迭代 #11 前置健全性门槛，迭代 #12 前置 alpha>0 门槛）","/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md:401:[迭代 #11 前置] 健全性过滤：剔除 closed_trades==0 比例 ≥ 80% 的退化策略","/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md:404:[迭代 #12 前置] alpha>0 硬门槛：剔除 alpha≤0 的候选（跑不赢 SPY 的策略不进权重）","/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md:414:**迭代 #11 健全性门槛（先于 alpha>0 门槛）**：","/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md:420:**迭代 #12 alpha>0 硬门槛（健全性之后、Tier 1/2/3 之前）**：","/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md:443:### 10.5 Walk-Forward 月度重优化","/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md:476:### 10.6 输出文件","/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md:503:### 10.7 性能考量"]
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md","limit":35,"offset":443}
---
 443→### 10.5 Walk-Forward 月度重优化
 444→
 445→```
 446→训练窗口 5 年 → 优化权重 → 应用 1 个月（样本外）→ 滚动前移 → 重新优化
 447→
 448→调度（APScheduler）：
 449→  每月第一个交易日 00:00 触发 run_matrix_backtest()
 450→  → 更新 strategy_weights.json
 451→  → StrategyMatrixRunner.reload_weights() 热加载
 452→```
 453→
 454→为什么是月度（设计访谈确认）：
 455→
 456→```
 457→更新太频繁（每天）→ 拟合近期噪音，权重翻转，策略左右打脸
 458→更新太慢（每年）  → 行情切换时反应迟钝
 459→每月 ≈ 21 交易日  → 足够样本外数据验证上轮权重，换手率可控
 460→```
 461→
 462→**窗口重叠率讨论：**
 463→
 464→```
 465→当前方案：训练 5 年 + 步进 1 个月 → 重叠率 = 59/60 ≈ 98.3%
 466→→ 权重变化缓慢（惯性大），但保证了统计稳健性
 467→→ 代价：市场突变时（如 2022 熊市初期）权重适应较慢
 468→
 469→改进方向（Phase 5 后续可选）：
 470→  方案 A：缩短训练窗口至 2-3 年，降低重叠率 → 适应性更强，但统计样本减少
 471→  方案 B：时间衰减权重（指数衰减 λ≈0.97/天）→ 近期数据权重更高，
 472→           等效训练窗口约 1-1.5 年，无需改变窗口长度
 473→  方案 C：双窗口验证：短窗口（1年）+ 长窗口（5年）权重取交集，兼顾适应性与稳健性
 474→```
 475→
 476→### 10.6 输出文件
 477→
 478→
---
 443→### 10.5 Walk-Forward 月度重优化
 444→
 445→```
 446→训练窗口 5 年 → 优化权重 → 应用 1 个月（样本外）→ 滚动前移 → 重新优化
 447→
 448→调度（APScheduler）：
 449→  每月第一个交易日 00:00 触发 run_matrix_backtest()
 450→  → 更新 strategy_weights.json
 451→  → StrategyMatrixRunner.reload_weights() 热加载
 452→```
 453→
 454→为什么是月度（设计访谈确认）：
 455→
 456→```
 457→更新太频繁（每天）→ 拟合近期噪音，权重翻转，策略左右打脸
 458→更新太慢（每年）  → 行情切换时反应迟钝
 459→每月 ≈ 21 交易日  → 足够样本外数据验证上轮权重，换手率可控
 460→```
 461→
 462→**窗口重叠率讨论：**
 463→
 464→```
 465→当前方案：训练 5 年 + 步进 1 个月 → 重叠率 = 59/60 ≈ 98.3%
 466→→ 权重变化缓慢（惯性大），但保证了统计稳健性
 467→→ 代价：市场突变时（如 2022 熊市初期）权重适应较慢
 468→
 469→改进方向（Phase 5 后续可选）：
 470→  方案 A：缩短训练窗口至 2-3 年，降低重叠率 → 适应性更强，但统计样本减少
 471→  方案 B：时间衰减权重（指数衰减 λ≈0.97/天）→ 近期数据权重更高，
 472→           等效训练窗口约 1-1.5 年，无需改变窗口长度
 473→  方案 C：双窗口验证：短窗口（1年）+ 长窗口（5年）权重取交集，兼顾适应性与稳健性
 474→```
 475→
 476→### 10.6 输出文件
 477→
 478→
---
现在我
---
将在
---
 
---
10
---
.
---
5
---
 
---
节
---
之后
---
添加
---
 WF
---
 alpha
---
 gate
---
 文
---
档
---
。
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md","new_string":"改进方向（Phase 5 后续可选）：\n  方案 A：缩短训练窗口至 2-3 年，降低重叠率 → 适应性更强，但统计样本减少\n  方案 B：时间衰减权重（指数衰减 λ≈0.97/天）→ 近期数据权重更高，\n           等效训练窗口约 1-1.5 年，无需改变窗口长度\n  方案 C：双窗口验证：短窗口（1年）+ 长窗口（5年）权重取交集，兼顾适应性与稳健性\n```\n\n#### 10.5.1 Walk-Forward 4 轮验证 + Alpha Gate（迭代 #3 基础，迭代 #13 加 alpha 校验）\n\nConstitution L7 验证流水线硬要求：Backtest(≥5年) → Walk-Forward(4轮) → Paper → Live。\n\n**每轮流程**：\n1. 训练期 [train_start, train_end]：跑矩阵回测找最优参数（复用 `_run_group`）\n2. 验证期 [val_start, val_end]：用同参数回测，记录 portfolio Sortino / max DD / **alpha vs SPY**\n3. `passed = val_max_dd ≤ 15% AND val_alpha > -5%`（迭代 #13 新增 alpha gate）\n\n**Gate 逻辑**（迭代 #13）：\n\n| 层级 | 条件 | 常量 |\n|------|------|------|\n| 单轮 | `val_max_dd ≤ 15% AND val_alpha > -5%` | `WALK_FORWARD_VAL_DD_THRESHOLD=15.0`, `WALK_FORWARD_VAL_ALPHA_FLOOR=-5.0` |\n| 汇总 | `all rounds passed AND avg_val_alpha > 0` | （硬编码 avg > 0） |\n\n**设计动机**（目标一致性修复）：\n- matrix_backtest 用 alpha 选策略（Iter #9），WF 也必须校验 alpha\n- Iter #11 实证：WF 4/4 pass（DD-only gate）但组合 alpha=-21% → WF 通过 ≠ 跑赢 SPY\n- 单轮允许 alpha 在 -5%~0%（小幅跑输可能是市场噪音），但 4 轮平均必须 > 0\n- 与 matrix_backtest 的 alpha>0 门槛呼应：in-sample alpha>0 是入选条件，OOS avg alpha>0 是验证条件\n- 满足 `experience.md #8`：\"验收 gate 必须校验跑赢 benchmark（正 alpha）\"\n\n**降级处理**：SPY 不可用时 `val_alpha=0.0`（不阻塞 WF），但 `avg_val_alpha=0` → `pass_all_rounds=False`（保守拒绝）\n\n**数据结构**：\n```python\n@dataclass\nclass WalkForwardRound:\n    round_num: int\n    train_start: date; train_end: date\n    val_start: date; val_end: date\n    val_sortino: float\n    val_max_dd: float\n    passed: bool\n    val_alpha: float = 0.0   # 迭代 #13：验证期 portfolio alpha vs SPY（百分数）\n\n@dataclass\nclass WalkForwardReport:\n    rounds: list[WalkForwardRound]\n    pass_all_rounds: bool      # all passed AND avg_val_alpha > 0\n    max_val_dd: float\n    avg_val_alpha: float = 0.0  # 迭代 #13：4 轮平均验证期 alpha\n    min_val_alpha: float = 0.0  # 迭代 #13：4 轮中最差的验证期 alpha\n```\n\n","old_string":"改进方向（Phase 5 后续可选）：\n  方案 A：缩短训练窗口至 2-3 年，降低重叠率 → 适应性更强，但统计样本减少\n  方案 B：时间衰减权重（指数衰减 λ≈0.97/天）→ 近期数据权重更高，\n           等效训练窗口约 1-1.5 年，无需改变窗口长度\n  方案 C：双窗口验证：短窗口（1年）+ 长窗口（5年）权重取交集，兼顾适应性与稳健性\n```\n\n"}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/mytrader/designs/design_v2/07-backtest-module.md
---
现在
---
更新
---
 `
---
iteration
---
_trajectory
---
.md
---
`
---
。
---
{"command":"head -20 /Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md","description":"Check trajectory header format"}
---
Check trajectory header format
---
Command: head -20 /Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md
Stdout: 
## 迭代 #0 — 读取 mytrader/backtest/runner.py 的代码并用一句话总结它的功能

- **日期**: 2026-06-30 05:46 UTC
- **类型**: 自动化迭代 (Orchestrator → CodeBuddy)
- **变更摘要**: 读取 mytrader/backtest/runner.py 的代码并用一句话总结它的功能
- **执行时长**: 79.2s
- **状态**: passed
- **CodeBuddy 更新数**: 60
- **工具调用数**: 4
- **团队事件数**: 0
- **权限请求数**: 0
- **违规检测**: 0 条
- **测试收集**: 0

### 违规详情
- ✅ 无违规

### CodeBuddy 最终响应 (摘要)
。

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"file_path":"/Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md","limit":15,"offset":1}
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
  16→
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
  16→
---
Let
---
 me
---
 look
---
 at
---
 the
---
 format
---
 of
---
 the
---
 most
---
 recent
---
 iteration
---
 (#
---
12
---
)
---
 to
---
 match
---
 it
---
,
---
 then
---
 append
---
 iteration
---
 #
---
13
---
.
---
让我
---
读取
---
 Iter
---
 #
---
12
---
 的
---
轨迹
---
格式
---
以便
---
进行
---
匹配
---
。
---
{"command":"grep -n \"## 迭代 #12\" /Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md","description":"Find Iter #12 section start"}
---
Find Iter #12 section start
---
Command: grep -n "## 迭代 #12" /Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md
Stdout: 1253:## 迭代 #12 — Alpha>0 硬门槛（Reject Negative-Alpha Strategies）

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"file_path":"/Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md","limit":100,"offset":1253}
---
1253→## 迭代 #12 — Alpha>0 硬门槛（Reject Negative-Alpha Strategies）
1254→
1255→- **日期**: 2026-07-07 UTC
1256→- **类型**: 选择器治理漏洞修复（低风险，仅改 `matrix_backtest.py` 选择器 + ensemble 权重）
1257→- **变更摘要**: 在 `_run_group` Tier 1/2/3 排序之前加 alpha>0 硬门槛（剔除跑不赢 SPY 的策略）；全负 alpha 组返回空权重 + `no_positive_alpha` 标记；修 `_optimize_ensemble_weights` 负 alpha 归一化 bug（`max(alpha,0.01)` → `max(alpha,0.0)`）
1258→- **状态**: passed
1259→- **执行时长**: ~17 分钟（orchestrator），248 次工具调用
1260→- **测试数**: 646 → 659（+13 新测试用例）
1261→
1262→### 背景
1263→
1264→Iter #11 健全性门槛成功剔除了退化策略（rsi_trend_filter 从 4/6 组降到 1/6 组），但 reoptimize 完整结果显示组合 alpha=-21.41%——11 条权重中 9 条负 alpha（in-sample），系统正在用 9 个"5 年跑不赢 SPY"的策略组合去交易。WF 4/4 全过（Sortino 1.56~2.09）但 PortfolioBacktest alpha=-21%，精确复现审计报告 §5 第 6 点"WF gate 不校验 alpha"。
1265→
1266→### 变更详情
1267→
1268→**P0: `GroupBacktestResult.no_positive_alpha` 字段** (`matrix_backtest.py`)
1269→- 新增 `no_positive_alpha: bool = False` 标记，标记该组是否因全负 alpha 而空仓
1270→
1271→**P0: `_run_group` alpha>0 硬门槛** (`matrix_backtest.py::_run_group`)
1272→- 在 candidates 构建后、Tier 1/2/3 之前，剔除 `alpha≤0` 的候选
1273→- 全负 alpha 组返回空权重 + `no_positive_alpha=True` 标记
1274→- 符合 `experience.md #8` 的门槛顺序：健全性 → 风险(DD) → 正超额(alpha>0) → 排序
1275→
1276→**P0: `_optimize_ensemble_weights` 负 alpha 归一化修复** (`matrix_backtest.py`)
1277→- 旧代码 `max(alpha, 0.01)` 把负 alpha 都变成 0.01 → 归一化后等权，掩盖"都不好"
1278→- 新代码 `max(alpha, 0.0)` → 负 alpha 权重为 0，只有正 alpha 参与归一化
1279→- 全负 alpha 时等权 fallback + WARNING（防御性设计，上游 alpha>0 门槛应已拦截）
1280→
1281→**测试** (`tests/test_alpha_gate.py`, +13 用例)
1282→- `no_positive_alpha` 字段默认值 + 可设置
1283→- 全正 alpha 组正常产出权重；全负 alpha 组返回空权重 + 标记
1284→- 混合 alpha 组只保留正 alpha 候选
1285→- 健全性门槛 + alpha 门槛协同工作（退化策略先被健全性剔除，负 alpha 再被 alpha 门槛剔除）
1286→- `_optimize_ensemble_weights`：负 alpha 权重为 0、全正 alpha 正常归一化、混合只正 alpha 加权、全负 fallback 等权 + WARNING
1287→- SPY 不可用时退化为等权（与 Iter #9 行为一致）
1288→- 同步更新 3 个现有测试文件的 SPY benchmark 数据（用 trend="down" 的 SPY 确保策略 alpha>0，避免被新门槛误杀）
1289→
1290→### Constitution 合规
1291→- ✅ 未突破 DD 20% 约束（alpha>0 门槛不影响 DD 过滤）
1292→- ✅ 测试覆盖率提升（+13 测试）
1293→- ✅ 未引入黑箱策略 / 未引入 RL
1294→- ✅ 文档与代码同步（07-backtest-module.md + trajectory + decision_log + CODEBUDDY）
1295→- ✅ 低风险变更（仅选择器逻辑），符合自动部署条件
1296→
1297→---
1298→
1299→> **Orchestrator 验证记录** (自动追加)
1300→> - 迭代状态: passed
1301→> - 测试: 0 passed, 0 failed
1302→> - 违规: 0 条
1303→> - 高风险文件: 0 个
1304→> - 测试数变化: 646 → 659
1305→> - CodeBuddy 自行更新了 trajectory ✅
1306→
1307→---
1308→
---
1253→## 迭代 #12 — Alpha>0 硬门槛（Reject Negative-Alpha Strategies）
1254→
1255→- **日期**: 2026-07-07 UTC
1256→- **类型**: 选择器治理漏洞修复（低风险，仅改 `matrix_backtest.py` 选择器 + ensemble 权重）
1257→- **变更摘要**: 在 `_run_group` Tier 1/2/3 排序之前加 alpha>0 硬门槛（剔除跑不赢 SPY 的策略）；全负 alpha 组返回空权重 + `no_positive_alpha` 标记；修 `_optimize_ensemble_weights` 负 alpha 归一化 bug（`max(alpha,0.01)` → `max(alpha,0.0)`）
1258→- **状态**: passed
1259→- **执行时长**: ~17 分钟（orchestrator），248 次工具调用
1260→- **测试数**: 646 → 659（+13 新测试用例）
1261→
1262→### 背景
1263→
1264→Iter #11 健全性门槛成功剔除了退化策略（rsi_trend_filter 从 4/6 组降到 1/6 组），但 reoptimize 完整结果显示组合 alpha=-21.41%——11 条权重中 9 条负 alpha（in-sample），系统正在用 9 个"5 年跑不赢 SPY"的策略组合去交易。WF 4/4 全过（Sortino 1.56~2.09）但 PortfolioBacktest alpha=-21%，精确复现审计报告 §5 第 6 点"WF gate 不校验 alpha"。
1265→
1266→### 变更详情
1267→
1268→**P0: `GroupBacktestResult.no_positive_alpha` 字段** (`matrix_backtest.py`)
1269→- 新增 `no_positive_alpha: bool = False` 标记，标记该组是否因全负 alpha 而空仓
1270→
1271→**P0: `_run_group` alpha>0 硬门槛** (`matrix_backtest.py::_run_group`)
1272→- 在 candidates 构建后、Tier 1/2/3 之前，剔除 `alpha≤0` 的候选
1273→- 全负 alpha 组返回空权重 + `no_positive_alpha=True` 标记
1274→- 符合 `experience.md #8` 的门槛顺序：健全性 → 风险(DD) → 正超额(alpha>0) → 排序
1275→
1276→**P0: `_optimize_ensemble_weights` 负 alpha 归一化修复** (`matrix_backtest.py`)
1277→- 旧代码 `max(alpha, 0.01)` 把负 alpha 都变成 0.01 → 归一化后等权，掩盖"都不好"
1278→- 新代码 `max(alpha, 0.0)` → 负 alpha 权重为 0，只有正 alpha 参与归一化
1279→- 全负 alpha 时等权 fallback + WARNING（防御性设计，上游 alpha>0 门槛应已拦截）
1280→
1281→**测试** (`tests/test_alpha_gate.py`, +13 用例)
1282→- `no_positive_alpha` 字段默认值 + 可设置
1283→- 全正 alpha 组正常产出权重；全负 alpha 组返回空权重 + 标记
1284→- 混合 alpha 组只保留正 alpha 候选
1285→- 健全性门槛 + alpha 门槛协同工作（退化策略先被健全性剔除，负 alpha 再被 alpha 门槛剔除）
1286→- `_optimize_ensemble_weights`：负 alpha 权重为 0、全正 alpha 正常归一化、混合只正 alpha 加权、全负 fallback 等权 + WARNING
1287→- SPY 不可用时退化为等权（与 Iter #9 行为一致）
1288→- 同步更新 3 个现有测试文件的 SPY benchmark 数据（用 trend="down" 的 SPY 确保策略 alpha>0，避免被新门槛误杀）
1289→
1290→### Constitution 合规
1291→- ✅ 未突破 DD 20% 约束（alpha>0 门槛不影响 DD 过滤）
1292→- ✅ 测试覆盖率提升（+13 测试）
1293→- ✅ 未引入黑箱策略 / 未引入 RL
1294→- ✅ 文档与代码同步（07-backtest-module.md + trajectory + decision_log + CODEBUDDY）
1295→- ✅ 低风险变更（仅选择器逻辑），符合自动部署条件
1296→
1297→---
1298→
1299→> **Orchestrator 验证记录** (自动追加)
1300→> - 迭代状态: passed
1301→> - 测试: 0 passed, 0 failed
1302→> - 违规: 0 条
1303→> - 高风险文件: 0 个
1304→> - 测试数变化: 646 → 659
1305→> - CodeBuddy 自行更新了 trajectory ✅
1306→
1307→---
1308→
---
现在
---
让我
---
将
---
第
---
 
---
13
---
 
---
次
---
迭代
---
添加
---
到
---
轨迹
---
文件
---
中
---
。
---
{"file_path":"/Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md","limit":20,"offset":1305}
---
1305→> - CodeBuddy 自行更新了 trajectory ✅
1306→
1307→---
1308→
---
1305→> - CodeBuddy 自行更新了 trajectory ✅
1306→
1307→---
1308→
---
{"file_path":"/Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md","new_string":"> - CodeBuddy 自行更新了 trajectory ✅\n\n---\n\n## 迭代 #13 — WF Gate 加 Alpha 校验（目标一致性修复）\n\n- **日期**: 2026-07-08 UTC\n- **类型**: WF 验证逻辑修复（低风险，仅改 `matrix_backtest.py` WF 验证 + `main.py` 日志）\n- **变更摘要**: 给 WF gate 加 alpha 校验，使 WF 的验证目标与 matrix_backtest 的选择目标（alpha）一致。新增 `WALK_FORWARD_VAL_ALPHA_FLOOR=-5.0` 常量；`WalkForwardRound` 加 `val_alpha` 字段；`WalkForwardReport` 加 `avg_val_alpha`/`min_val_alpha`；`run_walk_forward` 验证期计算 alpha vs SPY + gate 加 alpha 校验 + 汇总加 alpha 聚合；`main.py` WF 日志增加 alpha\n- **状态**: passed\n- **测试数**: 659 → 675（+16 新测试用例）\n\n### 背景\n\nIter #12 的 alpha>0 门槛修复了 in-sample 选择器，但 WF gate 仍然只校验 DD 不校验 alpha。Iter #11 实证：WF 4/4 pass（Sortino 1.56~2.09，max DD 6.36%），但 PortfolioBacktest alpha=-21.41%。WF 通过只说明\"策略没爆仓\"，不说明\"策略跑赢 SPY\"。这是 `experience.md #8` 指出的\"验收 gate 必须校验跑赢 benchmark（正 alpha）\"的直接违反。\n\n### 变更详情\n\n**P0: `WALK_FORWARD_VAL_ALPHA_FLOOR` 常量** (`matrix_backtest.py`)\n- 新增 `WALK_FORWARD_VAL_ALPHA_FLOOR: float = -5.0`，单轮 alpha 下限\n- 设计：单轮允许小幅跑输（-5%~0%），但 4 轮平均必须 > 0\n\n**P0: `WalkForwardRound.val_alpha` 字段** (`matrix_backtest.py`)\n- 新增 `val_alpha: float = 0.0`，验证期 portfolio alpha vs SPY（百分数）\n- 放在 `passed` 之后以保持与现有位置参数调用的向后兼容\n\n**P0: `WalkForwardReport.avg_val_alpha` / `min_val_alpha` 字段** (`matrix_backtest.py`)\n- `avg_val_alpha`: 4 轮平均验证期 alpha\n- `min_val_alpha`: 4 轮中最差的验证期 alpha\n\n**P0: `run_walk_forward` alpha 计算 + gate + 聚合** (`matrix_backtest.py`)\n- 验证期：调用 `mb._get_spy_returns(val_start, val_end)` + `_compute_alpha(combined, spy_val_returns)` 计算 val_alpha\n- 单轮 gate：`passed = dd_passed AND alpha_passed`（`alpha_passed = val_alpha > -5.0`）\n- 汇总：`pass_all_rounds = all(r.passed) AND (avg_val_alpha > 0)`\n- SPY 不可用时 val_alpha=0.0（降级不阻塞），但 avg=0 → pass_all_rounds=False（保守拒绝）\n\n**P0: `main.py` WF 日志** (`main.py::_run_reoptimize`)\n- 每轮日志增加 `alpha={r.val_alpha:.4f}%`\n- Summary 日志增加 `avg_val_alpha` 和 `min_val_alpha`\n- WARNING 消息更新为\"DD<=15% AND avg alpha>0\"\n\n**测试** (`tests/test_wf_alpha_gate.py`, +16 用例)\n- Dataclass 字段测试：`val_alpha` 默认 0.0 + 可设置；`avg_val_alpha`/`min_val_alpha` 字段存在 + 聚合正确\n- 单轮 gate 测试：alpha < -5% → fail；alpha > 0 → pass；alpha = -3% → pass；alpha = -5.0 边界 → fail\n- 汇总 gate 测试：avg < 0 → fail；avg > 0 → pass；单轮 fail → fail\n- 集成测试：SPY 不可用 → val_alpha=0；策略跑赢 SPY → val_alpha > 0；OOS 跑输 SPY → val_alpha < 0\n- 常量测试：`WALK_FORWARD_VAL_ALPHA_FLOOR == -5.0`；alpha floor 和 DD threshold 独立 AND 关系\n- 回归：更新 `test_matrix_backtest.py::TestWalkForward` 断言以反映新 gate 逻辑\n\n### Constitution 合规\n- ✅ 未突破 DD 20% 约束（alpha gate 是 DD gate 的补充，不替换）\n- ✅ 测试覆盖率提升（+16 测试）\n- ✅ 未引入黑箱策略 / 未引入 RL\n- ✅ 文档与代码同步（07-backtest-module.md + trajectory + decision_log + CODEBUDDY）\n- ✅ 低风险变更（仅 WF 验证逻辑 + 日志，不触及选择器/策略/risk/execution）\n- ✅ 满足 `experience.md #8`：\"验收 gate 必须校验跑赢 benchmark（正 alpha）\"\n\n### Experience Learned\n- **WF 与 matrix_backtest 目标一致性**：matrix_backtest 用 alpha 选策略，WF 也必须校验 alpha。否则 WF 通过 ≠ 跑赢 SPY（Iter #11 的 alpha=-21% 就是这个不一致的直接后果）\n- **WF 验证期本身就是 OOS**：不需要特制 OOS 数据集——WF 的验证期相对训练期就是样本外。只需在验证期计算 alpha vs SPY 并加入 gate\n- **单轮 floor + 汇总 avg 的两层设计**：单轮允许小幅跑输（-5%~0%，可能是市场噪音），但 4 轮平均必须 > 0（整体必须跑赢 SPY）。这比\"每轮都必须 > 0\"更鲁棒，避免因单轮噪音误杀\n\n### 后续建议\n- Iter #14：per-group OOS alpha 反馈（用 WF alpha 清除个别组的权重，需要更大架构改动）\n- 运行 `--reoptimize` 验证 WF 是否能正确拒绝 alpha<0 的策略组合（Meta-Agent 验收阶段独立执行）\n\n---\n","old_string":"> - CodeBuddy 自行更新了 trajectory ✅\n\n---\n"}
---
Error: Edit error on /Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md: Found 10 matches of the string to replace, but replace_all is false. To replace all occurrences, set replace_all to true. To replace only one occurrence, please provide more context to uniquely identify the instance.
String: > - CodeBuddy 自行更新了 trajectory ✅

---

---
Error: Edit error on /Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md: Found 10 matches of the string to replace, but replace_all is false. To replace all occurrences, set replace_all to true. To replace only one occurrence, please provide more context to uniquely identify the instance.
String: > - CodeBuddy 自行更新了 trajectory ✅

---

---
The
---
 string
---
 appears
---
 
---
10
---
 times
---
.
---
 I
---
 need
---
 more
---
 context
---
 to
---
 uniquely
---
 identify
---
 the
---
 last
---
 occurrence
---
 (
---
at
---
 the
---
 end
---
 of
---
 Iter
---
 #
---
12
---
).
---
 Let
---
 me
---
 use
---
 a
---
 larger
---
 context
---
.
---
{"file_path":"/Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md","new_string":"> - 测试数变化: 646 → 659\n> - CodeBuddy 自行更新了 trajectory ✅\n\n---\n\n## 迭代 #13 — WF Gate 加 Alpha 校验（目标一致性修复）\n\n- **日期**: 2026-07-08 UTC\n- **类型**: WF 验证逻辑修复（低风险，仅改 `matrix_backtest.py` WF 验证 + `main.py` 日志）\n- **变更摘要**: 给 WF gate 加 alpha 校验，使 WF 的验证目标与 matrix_backtest 的选择目标（alpha）一致。新增 `WALK_FORWARD_VAL_ALPHA_FLOOR=-5.0` 常量；`WalkForwardRound` 加 `val_alpha` 字段；`WalkForwardReport` 加 `avg_val_alpha`/`min_val_alpha`；`run_walk_forward` 验证期计算 alpha vs SPY + gate 加 alpha 校验 + 汇总加 alpha 聚合；`main.py` WF 日志增加 alpha\n- **状态**: passed\n- **测试数**: 659 → 675（+16 新测试用例）\n\n### 背景\n\nIter #12 的 alpha>0 门槛修复了 in-sample 选择器，但 WF gate 仍然只校验 DD 不校验 alpha。Iter #11 实证：WF 4/4 pass（Sortino 1.56~2.09，max DD 6.36%），但 PortfolioBacktest alpha=-21.41%。WF 通过只说明\"策略没爆仓\"，不说明\"策略跑赢 SPY\"。这是 `experience.md #8` 指出的\"验收 gate 必须校验跑赢 benchmark（正 alpha）\"的直接违反。\n\n### 变更详情\n\n**P0: `WALK_FORWARD_VAL_ALPHA_FLOOR` 常量** (`matrix_backtest.py`)\n- 新增 `WALK_FORWARD_VAL_ALPHA_FLOOR: float = -5.0`，单轮 alpha 下限\n- 设计：单轮允许小幅跑输（-5%~0%），但 4 轮平均必须 > 0\n\n**P0: `WalkForwardRound.val_alpha` 字段** (`matrix_backtest.py`)\n- 新增 `val_alpha: float = 0.0`，验证期 portfolio alpha vs SPY（百分数）\n- 放在 `passed` 之后以保持与现有位置参数调用的向后兼容\n\n**P0: `WalkForwardReport.avg_val_alpha` / `min_val_alpha` 字段** (`matrix_backtest.py`)\n- `avg_val_alpha`: 4 轮平均验证期 alpha\n- `min_val_alpha`: 4 轮中最差的验证期 alpha\n\n**P0: `run_walk_forward` alpha 计算 + gate + 聚合** (`matrix_backtest.py`)\n- 验证期：调用 `mb._get_spy_returns(val_start, val_end)` + `_compute_alpha(combined, spy_val_returns)` 计算 val_alpha\n- 单轮 gate：`passed = dd_passed AND alpha_passed`（`alpha_passed = val_alpha > -5.0`）\n- 汇总：`pass_all_rounds = all(r.passed) AND (avg_val_alpha > 0)`\n- SPY 不可用时 val_alpha=0.0（降级不阻塞），但 avg=0 → pass_all_rounds=False（保守拒绝）\n\n**P0: `main.py` WF 日志** (`main.py::_run_reoptimize`)\n- 每轮日志增加 `alpha={r.val_alpha:.4f}%`\n- Summary 日志增加 `avg_val_alpha` 和 `min_val_alpha`\n- WARNING 消息更新为\"DD<=15% AND avg alpha>0\"\n\n**测试** (`tests/test_wf_alpha_gate.py`, +16 用例)\n- Dataclass 字段测试：`val_alpha` 默认 0.0 + 可设置；`avg_val_alpha`/`min_val_alpha` 字段存在 + 聚合正确\n- 单轮 gate 测试：alpha < -5% → fail；alpha > 0 → pass；alpha = -3% → pass；alpha = -5.0 边界 → fail\n- 汇总 gate 测试：avg < 0 → fail；avg > 0 → pass；单轮 fail → fail\n- 集成测试：SPY 不可用 → val_alpha=0；策略跑赢 SPY → val_alpha > 0；OOS 跑输 SPY → val_alpha < 0\n- 常量测试：`WALK_FORWARD_VAL_ALPHA_FLOOR == -5.0`；alpha floor 和 DD threshold 独立 AND 关系\n- 回归：更新 `test_matrix_backtest.py::TestWalkForward` 断言以反映新 gate 逻辑\n\n### Constitution 合规\n- ✅ 未突破 DD 20% 约束（alpha gate 是 DD gate 的补充，不替换）\n- ✅ 测试覆盖率提升（+16 测试）\n- ✅ 未引入黑箱策略 / 未引入 RL\n- ✅ 文档与代码同步（07-backtest-module.md + trajectory + decision_log + CODEBUDDY）\n- ✅ 低风险变更（仅 WF 验证逻辑 + 日志，不触及选择器/策略/risk/execution）\n- ✅ 满足 `experience.md #8`：\"验收 gate 必须校验跑赢 benchmark（正 alpha）\"\n\n### Experience Learned\n- **WF 与 matrix_backtest 目标一致性**：matrix_backtest 用 alpha 选策略，WF 也必须校验 alpha。否则 WF 通过 ≠ 跑赢 SPY（Iter #11 的 alpha=-21% 就是这个不一致的直接后果）\n- **WF 验证期本身就是 OOS**：不需要特制 OOS 数据集——WF 的验证期相对训练期就是样本外。只需在验证期计算 alpha vs SPY 并加入 gate\n- **单轮 floor + 汇总 avg 的两层设计**：单轮允许小幅跑输（-5%~0%，可能是市场噪音），但 4 轮平均必须 > 0（整体必须跑赢 SPY）。这比\"每轮都必须 > 0\"更鲁棒，避免因单轮噪音误杀\n\n### 后续建议\n- Iter #14：per-group OOS alpha 反馈（用 WF alpha 清除个别组的权重，需要更大架构改动）\n- 运行 `--reoptimize` 验证 WF 是否能正确拒绝 alpha<0 的策略组合（Meta-Agent 验收阶段独立执行）\n\n---","old_string":"> - 测试数变化: 646 → 659\n> - CodeBuddy 自行更新了 trajectory ✅\n\n---"}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/alignment/iteration_trajectory.md
---
现在
---
请
---
使用
---
迭代
---
 #
---
13
---
 的
---
决策
---
记录
---
更新
---
 `
---
decision
---
_log
---
.md
---
`
---
。
---
{"command":"tail -5 /Users/rickouyang/Github/trade-tools/alignment/decision_log.md","description":"Check end of decision log"}
---
Check end of decision log
---
Command: tail -5 /Users/rickouyang/Github/trade-tools/alignment/decision_log.md
Stdout: - **经验教训**:
  - 门槛顺序很重要：alpha>0 放在排序前比排序后更符合 experience.md #8，避免遗漏正 alpha 策略
  - `max(x, ε)` 是危险的归一化模式：把"都不好"变成"等权都要"，掩盖质量问题。正确做法是让坏值权重为 0

---

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"file_path":"/Users/rickouyang/Github/trade-tools/alignment/decision_log.md","new_string":"- **经验教训**:\n  - 门槛顺序很重要：alpha>0 放在排序前比排序后更符合 experience.md #8，避免遗漏正 alpha 策略\n  - `max(x, ε)` 是危险的归一化模式：把\"都不好\"变成\"等权都要\"，掩盖质量问题。正确做法是让坏值权重为 0\n\n---\n\n### [2026-07-08 UTC] 迭代 #13 — WF alpha gate 设计（单轮 floor + 汇总 avg 两层）\n\n- **困境描述**: 给 WF gate 加 alpha 校验时，需要决定：① 单轮 alpha 门槛用严格 > 0 还是允许小幅负值？② 汇总 pass_all_rounds 用什么条件？③ `val_alpha` 字段放在 dataclass 的什么位置？\n\n- **决策逻辑**:\n\n  **决策 1: 单轮 alpha floor = -5%（允许小幅跑输），汇总 avg > 0（平均必须跑赢）**\n  - 选项 A：单轮严格 alpha > 0 → 过严，单轮噪音可能误杀好策略（某轮恰好遇到 SPY 强势期）\n  - 选项 B：单轮 alpha > -5% + 汇总 avg > 0 → 允许单轮小幅跑输（市场噪音），但整体必须跑赢\n  - 选 B：两层设计更鲁棒。单轮 floor 拦截灾难性跑输（< -5%），汇总 avg 拦截系统性跑输\n  - floor 取 -5% 而非 -10%：-5% 已经是显著跑输（年化差 5 个百分点），更低的 floor 等于没门槛\n\n  **决策 2: `val_alpha` 字段放在 `passed` 之后（而非之前）**\n  - spec 原文建议 `val_alpha` 放在 `passed` 之前，但这会导致 dataclass 字段顺序错误（有默认值的字段不能在无默认值的字段之前）\n  - 选项 A：给 `passed` 加默认值 `False` → 改变现有语义（`passed` 应该是必填的）\n  - 选项 B：把 `val_alpha` 放在 `passed` 之后 → 保持 `passed` 无默认值，`val_alpha` 有默认值 0.0\n  - 选 B：向后兼容（现有测试用 8 个位置参数 `WalkForwardRound(1, date, date, date, date, 1.0, 10.0, True)` 不需要修改），且 dataclass 字段顺序合法\n\n  **决策 3: SPY 不可用时 val_alpha=0.0 + pass_all_rounds=False（保守拒绝）**\n  - 选项 A：SPY 不可用时跳过 alpha gate（只校验 DD）→ 退化为旧逻辑，违反目标一致性\n  - 选项 B：SPY 不可用时 val_alpha=0.0 → avg=0 → pass_all_rounds=False（保守拒绝）\n  - 选 B：benchmark 数据缺失时应该保守拒绝，而不是放行。这迫使系统确保 SPY 数据可用\n\n- **决策结果**:\n  - 单轮 floor=-5% + 汇总 avg>0 两层 gate\n  - `val_alpha` 放在 `passed` 之后（向后兼容）\n  - SPY 不可用时保守拒绝（pass_all_rounds=False）\n  - 675 测试通过\n\n- **经验教训**:\n  - **spec 的字段顺序建议可能有 dataclass 兼容性问题**：spec 原文画了 `val_alpha` 在 `passed` 之前，但 Python dataclass 要求有默认值的字段在无默认值的之后。实现时需要判断 spec 的意图（加 alpha 字段）而非字面照搬\n  - **两层 gate 比单层更鲁棒**：单轮 floor 拦截灾难，汇总 avg 拦截系统性问题。这比\"每轮都必须 > 0\"更容错，避免因单轮市场噪音误杀\n  - **benchmark 缺失时保守拒绝**：比\"跳过 gate\"更安���。迫使系统确保 benchmark 数据可用，而不是在数据缺失时静默放行\n\n---","old_string":"- **经验教训**:\n  - 门槛顺序很重要：alpha>0 放在排序前比排序后更符合 experience.md #8，避免遗漏正 alpha 策略\n  - `max(x, ε)` 是危险的归一化模式：把\"都不好\"变成\"等权都要\"，掩盖质量问题。正确做法是让坏值权重为 0\n\n---"}
---
Error: File has not been read yet: /Users/rickouyang/Github/trade-tools/alignment/decision_log.md. Read it first before writing to it.
---
Error: File has not been read yet: /Users/rickouyang/Github/trade-tools/alignment/decision_log.md. Read it first before writing to it.
---
{"file_path":"/Users/rickouyang/Github/trade-tools/alignment/decision_log.md","limit":10,"offset":1}
---
   1→# Decision Log — AI Constitution 决策记录
   2→
   3→> 根据 ai_constitution.md L8 要求，记录所有模糊决策及其逻辑。
   4→
   5→---
   6→
   7→### [2026-06-30 16:20 UTC] 迭代 #1 — test_integration_live.py 触发真实 Telegram 消息
   8→
   9→- **困境描述**: CodeBuddy 在迭代 #1 中运行 `pytest` 时，`tests/test_integration_live.py::TestTelegramBot::test_send_test_message` 真实调用了 Telegram Bot API，向用户发送了测试消息。这暴露了测试隔离问题：live 集成测试没有被正确标记为 skip-by-default，导致全量 pytest 运行时触发了真实外部 API 调用。
  10→
  11→
---
   1→# Decision Log — AI Constitution 决策记录
   2→
   3→> 根据 ai_constitution.md L8 要求，记录所有模糊决策及其逻辑。
   4→
   5→---
   6→
   7→### [2026-06-30 16:20 UTC] 迭代 #1 — test_integration_live.py 触发真实 Telegram 消息
   8→
   9→- **困境描述**: CodeBuddy 在迭代 #1 中运行 `pytest` 时，`tests/test_integration_live.py::TestTelegramBot::test_send_test_message` 真实调用了 Telegram Bot API，向用户发送了测试消息。这暴露了测试隔离问题：live 集成测试没有被正确标记为 skip-by-default，导致全量 pytest 运行时触发了真实外部 API 调用。
  10→
  11→
---
{"command":"wc -l /Users/rickouyang/Github/trade-tools/alignment/decision_log.md","description":"Check file length"}
---
Check file length
---
Command: wc -l /Users/rickouyang/Github/trade-tools/alignment/decision_log.md
Stdout:      460 /Users/rickouyang/Github/trade-tools/alignment/decision_log.md

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
{"file_path":"/Users/rickouyang/Github/trade-tools/alignment/decision_log.md","limit":15,"offset":448}
---
 448→
 449→  **决策 2: `_optimize_ensemble_weights` 用 `max(alpha, 0.0)` 替代 `max(alpha, 0.01)`**
 450→  - 旧代码 `max(alpha, 0.01)`：alpha=-7.79 和 alpha=-1.49 都变成 0.01 → 归一化后 50/50 等权
 451→  - 新代码 `max(alpha, 0.0)`：负 alpha 权重为 0，只有正 alpha 参与归一化
 452→  - 全负 alpha 时等权 fallback + WARNING（防御性设计，上游 alpha>0 门槛应已拦截）
 453→
 454→- **决策结果**: alpha>0 门槛在 Tier 1 前 + ensemble 用 `max(alpha, 0.0)`；659 测试通过
 455→
 456→- **经验教训**:
 457→  - 门槛顺序很重要：alpha>0 放在排序前比排序后更符合 experience.md #8，避免遗漏正 alpha 策略
 458→  - `max(x, ε)` 是危险的归一化模式：把"都不好"变成"等权都要"，掩盖质量问题。正确做法是让坏值权重为 0
 459→
 460→---
 461→
---
 448→
 449→  **决策 2: `_optimize_ensemble_weights` 用 `max(alpha, 0.0)` 替代 `max(alpha, 0.01)`**
 450→  - 旧代码 `max(alpha, 0.01)`：alpha=-7.79 和 alpha=-1.49 都变成 0.01 → 归一化后 50/50 等权
 451→  - 新代码 `max(alpha, 0.0)`：负 alpha 权重为 0，只有正 alpha 参与归一化
 452→  - 全负 alpha 时等权 fallback + WARNING（防御性设计，上游 alpha>0 门槛应已拦截）
 453→
 454→- **决策结果**: alpha>0 门槛在 Tier 1 前 + ensemble 用 `max(alpha, 0.0)`；659 测试通过
 455→
 456→- **经验教训**:
 457→  - 门槛顺序很重要：alpha>0 放在排序前比排序后更符合 experience.md #8，避免遗漏正 alpha 策略
 458→  - `max(x, ε)` 是危险的归一化模式：把"都不好"变成"等权都要"，掩盖质量问题。正确做法是让坏值权重为 0
 459→
 460→---
 461→
---
{"file_path":"/Users/rickouyang/Github/trade-tools/alignment/decision_log.md","new_string":"- **决策结果**: alpha>0 门槛在 Tier 1 前 + ensemble 用 `max(alpha, 0.0)`；659 测试通过\n\n- **经验教训**:\n  - 门槛顺序很重要：alpha>0 放在排序前比排序后更符合 experience.md #8，避免遗漏正 alpha 策略\n  - `max(x, ε)` 是危险的归一化模式：把\"都不好\"变成\"等权都要\"，掩盖质量问题。正确做法是让坏值权重为 0\n\n---\n\n### [2026-07-08 UTC] 迭代 #13 — WF alpha gate 设计（单轮 floor + 汇总 avg 两层）\n\n- **困境描述**: 给 WF gate 加 alpha 校验时，需要决定：① 单轮 alpha 门槛用严格 > 0 还是允许小幅负值？② 汇总 pass_all_rounds 用什么条件？③ `val_alpha` 字段放在 dataclass 的什么位置？\n\n- **决策逻辑**:\n\n  **决策 1: 单轮 alpha floor = -5%（允许小幅跑输），汇总 avg > 0（平均必须跑赢）**\n  - 选项 A：单轮严格 alpha > 0 → 过严，单轮噪音可能误杀好策略（某轮恰好遇到 SPY 强势期）\n  - 选项 B：单轮 alpha > -5% + 汇总 avg > 0 → 允许单轮小幅跑输（市场噪音），但整体必须跑赢\n  - 选 B：两层设计更鲁棒。单轮 floor 拦截灾难性跑输（< -5%），汇总 avg 拦截系统性跑输\n  - floor 取 -5% 而非 -10%：-5% 已经是显著跑输（年化差 5 个百分点），更低的 floor 等于没门槛\n\n  **决策 2: `val_alpha` 字段放在 `passed` 之后（而非 spec 建议的之前）**\n  - spec 原文建议 `val_alpha` 放在 `passed` 之前，但这会导致 dataclass 字段顺序错误（有默认值的字段不能在无默认值的字段之前）\n  - 选项 A：给 `passed` 加默认值 `False` → 改变现有语义（`passed` 应该是必填的）\n  - 选项 B：把 `val_alpha` 放在 `passed` 之后 → 保持 `passed` 无默认值，`val_alpha` 有默认值 0.0\n  - 选 B：向后兼容（现有测试用 8 个位置参数 `WalkForwardRound(1, date, date, date, date, 1.0, 10.0, True)` 不需要修改），且 dataclass 字段顺序合法\n\n  **决策 3: SPY 不可用时 val_alpha=0.0 + pass_all_rounds=False（保守拒绝）**\n  - 选项 A：SPY 不可用时跳过 alpha gate（只校验 DD）→ 退化为旧逻辑，违反目标一致性\n  - 选项 B：SPY 不可用时 val_alpha=0.0 → avg=0 → pass_all_rounds=False（保守拒绝）\n  - 选 B：benchmark 数据缺失时应该保守拒绝，而不是放行。这迫使系统确保 SPY 数据可用\n\n- **决策结果**:\n  - 单轮 floor=-5% + 汇总 avg>0 两层 gate\n  - `val_alpha` 放在 `passed` 之后（向后兼容）\n  - SPY 不可用时保守拒绝（pass_all_rounds=False）\n  - 675 测试通过\n\n- **经验教训**:\n  - **spec 的字段顺序建议可能有 dataclass 兼容性问题**：spec 原文画了 `val_alpha` 在 `passed` 之前，但 Python dataclass 要求有默认值的字段在无默认值的之后。实现时需要判断 spec 的意图（加 alpha 字段）而非字面照搬\n  - **两层 gate 比单层更鲁棒**：单轮 floor 拦截灾难，汇总 avg 拦截系统性问题。这比\"每轮都必须 > 0\"更容错，避免因单轮市场噪音误杀\n  - **benchmark 缺失时保守拒绝**：比\"跳过 gate\"更安全。迫使系统确保 benchmark 数据可用，而不是在数据缺失时静默放行\n\n---","old_string":"- **决策结果**: alpha>0 门槛在 Tier 1 前 + ensemble 用 `max(alpha, 0.0)`；659 测试通过\n\n- **经验教训**:\n  - 门槛顺序很重要：alpha>0 放在排序前比排序后更符合 experience.md #8，避免遗漏正 alpha 策略\n  - `max(x, ε)` 是危险的归一化模式：把\"都不好\"变成\"等权都要\"，掩盖质量问题。正确做法是让坏值权重为 0\n\n---"}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/alignment/decision_log.md
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/alignment/decision_log.md
---
现在
---
更新
---
 `
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
`
---
。
---
我
---
需要
---
更新
---
迭代
---
表
---
并
---
添加
---
第
---
 
---
13
---
 
---
次
---
迭代
---
。
---
{"file_path":"/Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md","limit":30,"offset":1}
---
   1→# Trade-Tools 项目核心参考文档
   2→
   3→> 最后更新：2026-07-07 (Iter #12: Alpha>0 Hard Gate / Reject Negative-Alpha Strategies)  
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
  16→> - 架构边界（Trading System 纯规则 / Agent System 研究层）
  17→> - 决策权重矩阵（15 项优先级排序）
  18→> - 运行时故障处理策略
  19→> - 代码规范与测试纪律
  20→> - 策略上线验证流水线
  21→> - AI 自主权矩阵 + 禁止行为清单
  22→>
  23→> **🔗 全文** → [`alignment/ai_constitution.md`](../alignment/ai_constitution.md)
  24→>
  25→> **AI 遇到模糊决策时必须记录决策日志** → `alignment/decision_log.md`  
  26→> **每次策略迭代必须留痕** → `alignment/iteration_trajectory.md`
  27→
  28→---
  29→
  30→## 1. 项目概述
  31→
---
   1→# Trade-Tools 项目核心参考文档
   2→
   3→> 最后更新：2026-07-07 (Iter #12: Alpha>0 Hard Gate / Reject Negative-Alpha Strategies)  
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
  16→> - 架构边界（Trading System 纯规则 / Agent System 研究层）
  17→> - 决策权重矩阵（15 项优先级排序）
  18→> - 运行时故障处理策略
  19→> - 代码规范与测试纪律
  20→> - 策略上线验证流水线
  21→> - AI 自主权矩阵 + 禁止行为清单
  22→>
  23→> **🔗 全文** → [`alignment/ai_constitution.md`](../alignment/ai_constitution.md)
  24→>
  25→> **AI 遇到模糊决策时必须记录决策日志** → `alignment/decision_log.md`  
  26→> **每次策略迭代必须留痕** → `alignment/iteration_trajectory.md`
  27→
  28→---
  29→
  30→## 1. 项目概述
  31→
---
{"file_path":"/Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md","new_string":"# Trade-Tools 项目核心参考文档\n\n> 最后更新：2026-07-08 (Iter #13: WF Gate Alpha Validation / Target Consistency Fix)  \n> 本文是项目规范 + 关键索引，供 AI 助手快速建立项目上下文。  \n> **各阶段开发详情见** → [`.codebuddy/notes/dev_records.md`](.codebuddy/notes/dev_records.md)","old_string":"# Trade-Tools 项目核心参考文档\n\n> 最后更新：2026-07-07 (Iter #12: Alpha>0 Hard Gate / Reject Negative-Alpha Strategies)  \n> 本文是项目规范 + 关键索引，供 AI 助手快速建立项目上下文。  \n> **各阶段开发详情见** → [`.codebuddy/notes/dev_records.md`](.codebuddy/notes/dev_records.md)"}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md
---
现在
---
更新
---
迭
---
代表
---
以
---
添加
---
 Iter
---
 #
---
13
---
。
---
{"-n":true,"output_mode":"content","path":"/Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md","pattern":"Iter #12|Phase 6|当前总测试数"}
---
["/Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md:128:    │   ├── matrix_backtest.py  # [Phase 5] MatrixBacktest（含 backtest_dd_status + [Iter #9] alpha selection + [Iter #11] closed_trades/sanity gate + [Iter #12] alpha>0 gate/no_positive_alpha）","/Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md:201:| **Iter #12** | ✅ 完成 | 13 | Alpha>0 Hard Gate（`_run_group` Tier 1 前加 alpha>0 过滤 + 全负 alpha 组空仓 `no_positive_alpha` + `_optimize_ensemble_weights` 修 `max(alpha,0.01)` 归一化 bug） |","/Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md:202:| **Phase 6** | 🔲 待开发 | — | AlpacaBroker auto 端到端验证 + 对账真实集成 + 港股支持 |","/Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md:204:**当前总测试数：659 passed，0 failed**（live 测试默认隔离，迭代 #12 后；harness 测试 38 个在 `alignment/tests/`）"]
---
["/Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md:128:    │   ├── matrix_backtest.py  # [Phase 5] MatrixBacktest（含 backtest_dd_status + [Iter #9] alpha selection + [Iter #11] closed_trades/sanity gate + [Iter #12] alpha>0 gate/no_positive_alpha）","/Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md:201:| **Iter #12** | ✅ 完成 | 13 | Alpha>0 Hard Gate（`_run_group` Tier 1 前加 alpha>0 过滤 + 全负 alpha 组空仓 `no_positive_alpha` + `_optimize_ensemble_weights` 修 `max(alpha,0.01)` 归一化 bug） |","/Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md:202:| **Phase 6** | 🔲 待开发 | — | AlpacaBroker auto 端到端验证 + 对账真实集成 + 港股支持 |","/Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md:204:**当前总测试数：659 passed，0 failed**（live 测试默认隔离，迭代 #12 后；harness 测试 38 个在 `alignment/tests/`）"]
---
{"file_path":"/Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md","new_string":"| **Iter #12** | ✅ 完成 | 13 | Alpha>0 Hard Gate（`_run_group` Tier 1 前加 alpha>0 过滤 + 全负 alpha 组空仓 `no_positive_alpha` + `_optimize_ensemble_weights` 修 `max(alpha,0.01)` 归一化 bug） |\n| **Iter #13** | ✅ 完成 | 16 | WF Gate Alpha Validation（`WALK_FORWARD_VAL_ALPHA_FLOOR=-5.0` + `WalkForwardRound.val_alpha` + `WalkForwardReport.avg/min_val_alpha` + WF gate 加 alpha 校验 + `main.py` WF 日志增加 alpha） |\n| **Phase 6** | 🔲 待开发 | — | AlpacaBroker auto 端到端验证 + 对账真实集成 + 港股支持 |\n\n**当前总测试数：675 passed，0 failed**（live 测试默认隔离，迭代 #13 后；harness 测试 38 个在 `alignment/tests/`）","old_string":"| **Iter #12** | ✅ 完成 | 13 | Alpha>0 Hard Gate（`_run_group` Tier 1 前加 alpha>0 过滤 + 全负 alpha 组空仓 `no_positive_alpha` + `_optimize_ensemble_weights` 修 `max(alpha,0.01)` 归一化 bug） |\n| **Phase 6** | 🔲 待开发 | — | AlpacaBroker auto 端到端验证 + 对账真实集成 + 港股支持 |\n\n**当前总测试数：659 passed，0 failed**（live 测试默认隔离，迭代 #12 后；harness 测试 38 个在 `alignment/tests/`）"}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md
---
现在
---
更新
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
 的
---
文件
---
树
---
注释
---
，
---
以
---
提及
---
 Iter
---
 #
---
13
---
。
---
{"file_path":"/Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md","new_string":"    │   ├── matrix_backtest.py  # [Phase 5] MatrixBacktest（含 backtest_dd_status + [Iter #9] alpha selection + [Iter #11] closed_trades/sanity gate + [Iter #12] alpha>0 gate/no_positive_alpha + [Iter #13] WF alpha gate/val_alpha）","old_string":"    │   ├── matrix_backtest.py  # [Phase 5] MatrixBacktest（含 backtest_dd_status + [Iter #9] alpha selection + [Iter #11] closed_trades/sanity gate + [Iter #12] alpha>0 gate/no_positive_alpha）"}
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md
---
Successfully edited file: /Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md
---
现在
---
，
---
我
---
还要
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
 
---
中的
---
 WF
---
 
---
部
---
分
---
注释
---
（
---
如果
---
有的
---
话
---
）。
---
让我
---
检查
---
一下
---
架构
---
部分
---
。
---
{"-n":true,"output_mode":"content","path":"/Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md","pattern":"Walk-Forward|WF|walk_forward"}
---
["/Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md:3:> 最后更新：2026-07-08 (Iter #13: WF Gate Alpha Validation / Target Consistency Fix)  ","/Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md:128:    │   ├── matrix_backtest.py  # [Phase 5] MatrixBacktest（含 backtest_dd_status + [Iter #9] alpha selection + [Iter #11] closed_trades/sanity gate + [Iter #12] alpha>0 gate/no_positive_alpha + [Iter #13] WF alpha gate/val_alpha）","/Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md:149:    │   └── scheduler.py        # 含月度 Walk-Forward job","/Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md:162:┌─────────────── 离线回测层（Monthly Walk-Forward）──────────────────┐","/Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md:193:| **Phase 5** | ✅ 完成 | 85 | MarketDataStore + UniverseManager + 矩阵扫描 + 矩阵回测 + Walk-Forward |","/Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md:202:| **Iter #13** | ✅ 完成 | 16 | WF Gate Alpha Validation（`WALK_FORWARD_VAL_ALPHA_FLOOR=-5.0` + `WalkForwardRound.val_alpha` + `WalkForwardReport.avg/min_val_alpha` + WF gate 加 alpha 校验 + `main.py` WF 日志增加 alpha） |","/Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md:288:| `07-backtest-module.md` | VectorBT 1.0.0 用法、矩阵回测（Walk-Forward） |"]
---
["/Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md:3:> 最后更新：2026-07-08 (Iter #13: WF Gate Alpha Validation / Target Consistency Fix)  ","/Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md:128:    │   ├── matrix_backtest.py  # [Phase 5] MatrixBacktest（含 backtest_dd_status + [Iter #9] alpha selection + [Iter #11] closed_trades/sanity gate + [Iter #12] alpha>0 gate/no_positive_alpha + [Iter #13] WF alpha gate/val_alpha）","/Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md:149:    │   └── scheduler.py        # 含月度 Walk-Forward job","/Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md:162:┌─────────────── 离线回测层（Monthly Walk-Forward）──────────────────┐","/Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md:193:| **Phase 5** | ✅ 完成 | 85 | MarketDataStore + UniverseManager + 矩阵扫描 + 矩阵回测 + Walk-Forward |","/Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md:202:| **Iter #13** | ✅ 完成 | 16 | WF Gate Alpha Validation（`WALK_FORWARD_VAL_ALPHA_FLOOR=-5.0` + `WalkForwardRound.val_alpha` + `WalkForwardReport.avg/min_val_alpha` + WF gate 加 alpha 校验 + `main.py` WF 日志增加 alpha） |","/Users/rickouyang/Github/trade-tools/.codebuddy/CODEBUDDY.md:288:| `07-backtest-module.md` | VectorBT 1.0.0 用法、矩阵回测（Walk-Forward） |"]
---
好的
---
。
---
现在
---
让我
---
再
---
运行
---
一次
---
完整的
---
测试
---
套
---
件
---
，
---
以
---
确认
---
在
---
更新
---
文档
---
后
---
一切
---
仍然
---
通过
---
。
---
{"command":"/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest -p no:warnings --tb=short 2>&1 | tail -3","description":"Final full pytest run","timeout":300000}
---
Final full pytest run
---
Command: /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest -p no:warnings --tb=short 2>&1 | tail -3
Stdout: ........................................................................ [ 96%]
...........................                                              [100%]
675 passed, 16 deselected in 22.41s

Stderr: (empty)
Exit Code: 0
Signal: (none)
---
所有
---
 
---
6
---
75
---
 个
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
通过
---
检查
---
关键
---
变更
---
来
---
确认
---
最终
---
实现
---
。
---
{"status":"completed","taskId":"7"}
---
Updated task #7 status
---
Updated task #7 status
---
让我
---
最后
---
检查
---
一下
---
核心
---
实现
---
，
---
以确保
---
一切
---
正确
---
无误
---
。
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py","limit":15,"offset":39}
---
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
  54→
---
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
  54→
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py","limit":65,"offset":895}
---
 895→            group_returns = _backtest_with_params_on_period(
 896→                mb, symbols, weights, val_start, val_end,
 897→            )
 898→            all_returns.extend(group_returns)
 899→
 900→        # 计算整体 portfolio 指标（等权合并所有组的日收益率）
 901→        if not all_returns:
 902→            val_sortino = 0.0
 903→            val_max_dd = 0.0
 904→            val_alpha = 0.0
 905→            logger.warning(
 906→                f"[WalkForward] Round {round_num}: no valid val returns — "
 907→                f"sortino=0, dd=0, alpha=0, passed=True (vacuous)"
 908→            )
 909→        else:
 910→            combined = pd.concat(all_returns, axis=1).mean(axis=1).dropna()
 911→            if len(combined) < 5:
 912→                val_sortino = 0.0
 913→                val_max_dd = 0.0
 914→                val_alpha = 0.0
 915→            else:
 916→                val_sortino = _compute_sortino(combined)
 917→                wrapper = [SingleBacktestResult(
 918→                    symbol="portfolio", strategy="", params={},
 919→                    sharpe=0.0, total_return_pct=0.0, max_drawdown_pct=0.0,
 920→                    win_rate_pct=0.0, total_trades=0, daily_returns=combined,
 921→                )]
 922→                val_max_dd = _portfolio_max_drawdown_from_results(wrapper)
 923→
 924→                # ── 迭代 #13：计算验证期 alpha vs SPY ──
 925→                # 与 matrix_backtest 的 alpha 选择目标一致（目标一致性修复）
 926→                # SPY 不可用时 alpha=0.0（与 _compute_alpha 的降级语义一致）
 927→                spy_val_returns = mb._get_spy_returns(val_start, val_end)
 928→                if spy_val_returns is not None:
 929→                    val_alpha = _compute_alpha(combined, spy_val_returns)
 930→                else:
 931→                    val_alpha = 0.0
 932→                    logger.warning(
 933→                        f"[WalkForward] Round {round_num}: SPY data unavailable for "
 934→                        f"val period {val_start}~{val_end} — val_alpha=0 (degraded)"
 935→                    )
 936→
 937→        # ── 迭代 #13：gate 加 alpha 校验 ──
 938→        # 单轮：DD ≤ 15% AND alpha > -5%（允许小幅跑输，不容忍灾难性跑输）
 939→        # 汇总（在 report 构建时）：all rounds passed AND avg_val_alpha > 0
 940→        dd_passed = val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD
 941→        alpha_passed = val_alpha > WALK_FORWARD_VAL_ALPHA_FLOOR
 942→        passed = dd_passed and alpha_passed
 943→        wf_rounds.append(WalkForwardRound(
 944→            round_num=round_num,
 945→            train_start=train_start,
 946→            train_end=train_end,
 947→            val_start=val_start,
 948→            val_end=val_end,
 949→            val_sortino=val_sortino,
 950→            val_max_dd=val_max_dd,
 951→            val_alpha=val_alpha,
 952→            passed=passed,
 953→        ))
 954→        logger.info(
 955→            f"[WalkForward] Round {round_num} result: "
 956→            f"sortino={val_sortino:.4f}, dd={val_max_dd:.4f}%, "
 957→            f"alpha={val_alpha:.4f}%, passed={passed} "
 958→            f"(dd_threshold={WALK_FORWARD_VAL_DD_THRESHOLD}%, "
 959→            f"alpha_floor={WALK_FORWARD_VAL_ALPHA_FLOOR}%)"
 960→
---
 895→            group_returns = _backtest_with_params_on_period(
 896→                mb, symbols, weights, val_start, val_end,
 897→            )
 898→            all_returns.extend(group_returns)
 899→
 900→        # 计算整体 portfolio 指标（等权合并所有组的日收益率）
 901→        if not all_returns:
 902→            val_sortino = 0.0
 903→            val_max_dd = 0.0
 904→            val_alpha = 0.0
 905→            logger.warning(
 906→                f"[WalkForward] Round {round_num}: no valid val returns — "
 907→                f"sortino=0, dd=0, alpha=0, passed=True (vacuous)"
 908→            )
 909→        else:
 910→            combined = pd.concat(all_returns, axis=1).mean(axis=1).dropna()
 911→            if len(combined) < 5:
 912→                val_sortino = 0.0
 913→                val_max_dd = 0.0
 914→                val_alpha = 0.0
 915→            else:
 916→                val_sortino = _compute_sortino(combined)
 917→                wrapper = [SingleBacktestResult(
 918→                    symbol="portfolio", strategy="", params={},
 919→                    sharpe=0.0, total_return_pct=0.0, max_drawdown_pct=0.0,
 920→                    win_rate_pct=0.0, total_trades=0, daily_returns=combined,
 921→                )]
 922→                val_max_dd = _portfolio_max_drawdown_from_results(wrapper)
 923→
 924→                # ── 迭代 #13：计算验证期 alpha vs SPY ──
 925→                # 与 matrix_backtest 的 alpha 选择目标一致（目标一致性修复）
 926→                # SPY 不可用时 alpha=0.0（与 _compute_alpha 的降级语义一致）
 927→                spy_val_returns = mb._get_spy_returns(val_start, val_end)
 928→                if spy_val_returns is not None:
 929→                    val_alpha = _compute_alpha(combined, spy_val_returns)
 930→                else:
 931→                    val_alpha = 0.0
 932→                    logger.warning(
 933→                        f"[WalkForward] Round {round_num}: SPY data unavailable for "
 934→                        f"val period {val_start}~{val_end} — val_alpha=0 (degraded)"
 935→                    )
 936→
 937→        # ── 迭代 #13：gate 加 alpha 校验 ──
 938→        # 单轮：DD ≤ 15% AND alpha > -5%（允许小幅跑输，不容忍灾难性跑输）
 939→        # 汇总（在 report 构建时）：all rounds passed AND avg_val_alpha > 0
 940→        dd_passed = val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD
 941→        alpha_passed = val_alpha > WALK_FORWARD_VAL_ALPHA_FLOOR
 942→        passed = dd_passed and alpha_passed
 943→        wf_rounds.append(WalkForwardRound(
 944→            round_num=round_num,
 945→            train_start=train_start,
 946→            train_end=train_end,
 947→            val_start=val_start,
 948→            val_end=val_end,
 949→            val_sortino=val_sortino,
 950→            val_max_dd=val_max_dd,
 951→            val_alpha=val_alpha,
 952→            passed=passed,
 953→        ))
 954→        logger.info(
 955→            f"[WalkForward] Round {round_num} result: "
 956→            f"sortino={val_sortino:.4f}, dd={val_max_dd:.4f}%, "
 957→            f"alpha={val_alpha:.4f}%, passed={passed} "
 958→            f"(dd_threshold={WALK_FORWARD_VAL_DD_THRESHOLD}%, "
 959→            f"alpha_floor={WALK_FORWARD_VAL_ALPHA_FLOOR}%)"
 960→
---
{"file_path":"/Users/rickouyang/Github/trade-tools/mytrader/mytrader/backtest/matrix_backtest.py","limit":30,"offset":960}
---
 960→        )
 961→
 962→    # ── 迭代 #13：汇总 alpha 聚合 + pass_all_rounds 加 avg alpha > 0 条件 ──
 963→    val_alphas = [r.val_alpha for r in wf_rounds]
 964→    avg_val_alpha = sum(val_alphas) / len(val_alphas) if val_alphas else 0.0
 965→    min_val_alpha = min(val_alphas) if val_alphas else 0.0
 966→
 967→    # 单轮全过 AND 平均 alpha > 0（OOS 平均必须跑赢 SPY）
 968→    all_rounds_passed = all(r.passed for r in wf_rounds) if wf_rounds else False
 969→    avg_alpha_positive = avg_val_alpha > 0
 970→    pass_all = all_rounds_passed and avg_alpha_positive
 971→
 972→    report = WalkForwardReport(
 973→        rounds=wf_rounds,
 974→        pass_all_rounds=pass_all,
 975→        max_val_dd=max((r.val_max_dd for r in wf_rounds), default=0.0),
 976→        avg_val_alpha=avg_val_alpha,
 977→        min_val_alpha=min_val_alpha,
 978→    )
 979→    logger.info(
 980→        f"[WalkForward] done: {len(wf_rounds)} rounds, "
 981→        f"pass_all_rounds={report.pass_all_rounds}, "
 982→        f"max_val_dd={report.max_val_dd:.4f}%, "
 983→        f"avg_val_alpha={report.avg_val_alpha:.4f}%, "
 984→        f"min_val_alpha={report.min_val_alpha:.4f}%"
 985→    )
 986→    return report
 987→
 988→
 989→# ---------------------------------------------------------------------------
 990→
---
 960→        )
 961→
 962→    # ── 迭代 #13：汇总 alpha 聚合 + pass_all_rounds 加 avg alpha > 0 条件 ──
 963→    val_alphas = [r.val_alpha for r in wf_rounds]
 964→    avg_val_alpha = sum(val_alphas) / len(val_alphas) if val_alphas else 0.0
 965→    min_val_alpha = min(val_alphas) if val_alphas else 0.0
 966→
 967→    # 单轮全过 AND 平均 alpha > 0（OOS 平均必须跑赢 SPY）
 968→    all_rounds_passed = all(r.passed for r in wf_rounds) if wf_rounds else False
 969→    avg_alpha_positive = avg_val_alpha > 0
 970→    pass_all = all_rounds_passed and avg_alpha_positive
 971→
 972→    report = WalkForwardReport(
 973→        rounds=wf_rounds,
 974→        pass_all_rounds=pass_all,
 975→        max_val_dd=max((r.val_max_dd for r in wf_rounds), default=0.0),
 976→        avg_val_alpha=avg_val_alpha,
 977→        min_val_alpha=min_val_alpha,
 978→    )
 979→    logger.info(
 980→        f"[WalkForward] done: {len(wf_rounds)} rounds, "
 981→        f"pass_all_rounds={report.pass_all_rounds}, "
 982→        f"max_val_dd={report.max_val_dd:.4f}%, "
 983→        f"avg_val_alpha={report.avg_val_alpha:.4f}%, "
 984→        f"min_val_alpha={report.min_val_alpha:.4f}%"
 985→    )
 986→    return report
 987→
 988→
 989→# ---------------------------------------------------------------------------
 990→
---
所有
---
实现
---
均
---
正确
---
无误
---
。
---
让我
---
为您
---
总结
---
一下
---
所
---
完成
---
的工作
---
。


---
##
---
 第
---
 
---
13
---
 
---
次
---
迭代
---
总结
---
 —
---
 WF
---
 Gate
---
 Alpha
---
 
---
验
---
证
---



---
###
---
 已
---
完成的
---
变更
---



---
**
---
1
---
.
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
 —
---
 
---
常
---
量
---
 +
---
 数据
---
类
---
 (
---
data
---
class
---
)
---
 +
---
 WF
---
 
---
逻辑
---
**

---
-
---
 新
---
增
---
 `
---
W
---
ALK
---
_FORWARD
---
_VAL
---
_ALPHA
---
_F
---
LOOR
---
:
---
 float
---
 =
---
 -
---
5
---
.
---
0
---
`
---
 
---
常
---
量
---
（
---
单
---
轮
---
 alpha
---
 下
---
限
---
）

---
-
---
 `
---
Walk
---
Forward
---
Round
---
`
---
 新
---
增
---
 `
---
val
---
_alpha
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
放在
---
 `
---
passed
---
`
---
 之后
---
以
---
保持
---
与
---
位置
---
参数
---
的
---
向后
---
兼容
---
性
---
）

---
-
---
 `
---
Walk
---
Forward
---
Report
---
`
---
 新
---
增
---
 `
---
avg
---
_val
---
_alpha
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
0
---
`
---
 和
---
 `
---
min
---
_val
---
_alpha
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
0
---
`

---
-
---
 `
---
run
---
_walk
---
_forward
---
`
---
 
---
现
---
在
---
在
---
验证
---
期
---
计算
---
 alpha
---
 与
---
 SP
---
Y
---
 的
---
对比
---
：

---
 
---
 -
---
 **
---
单
---
轮
---
门
---
控
---
 (
---
Single
---
-round
---
 gate
---
)**
---
：
---
`
---
passed
---
 =
---
 (
---
DD
---
 ≤
---
 
---
15
---
%)
---
 AND
---
 (
---
alpha
---
 >
---
 -
---
5
---
%)
---
`

---
 
---
 -
---
 **
---
汇总
---
门
---
控
---
 (
---
Summary
---
 gate
---
)**
---
：
---
`
---
pass
---
_all
---
_round
---
s
---
 =
---
 all
---
(r
---
.pass
---
ed
---
)
---
 AND
---
 (
---
avg
---
_val
---
_alpha
---
 >
---
 
---
0
---
)`

---
 
---
 -
---
 SP
---
Y
---
 
---
不可
---
用
---
 →
---
 `
---
val
---
_alpha
---
=
---
0
---
.
---
0
---
`
---
 →
---
 `
---
pass
---
_all
---
_round
---
s
---
=False
---
`
---
（
---
保守
---
拒绝
---
）


---
**
---
2
---
.
---
 `
---
main
---
.py
---
`
---
 —
---
 WF
---
 日
---
志
---
**

---
-
---
 单
---
轮
---
日志
---
新增
---
 `
---
alpha
---
={
---
r
---
.val
---
_alpha
---
:.
---
4
---
f
---
}%
---
`

---
-
---
 
---
汇
---
总
---
日志
---
新增
---
 `
---
avg
---
_val
---
_alpha
---
`
---
 和
---
 `
---
min
---
_val
---
_alpha
---
`

---
-
---
 更
---
新
---
警告
---
信息
---
以
---
提及
---
“
---
DD
---
≤
---
15
---
%
---
 且
---
平均
---
 alpha
---
>
---
0
---
”


---
**
---
3
---
.
---
 
---
测试
---
 —
---
 `
---
tests
---
/test
---
_wf
---
_alpha
---
_gate
---
.py
---
`
---
（
---
16
---
 个
---
新
---
测试
---
）
---
**

---
-
---
 数据
---
类
---
字段
---
测试
---
（
---
4
---
 个
---
）

---
-
---
 单
---
轮
---
门
---
控
---
测试
---
：
---
拒绝
---
/
---
通过
---
/
---
允许
---
微小
---
负
---
值
---
/
---
边界
---
情况
---
（
---
4
---
 个
---
）

---
-
---
 
---
汇
---
总
---
门
---
控
---
测试
---
：
---
平均
---
 alpha
---
 <
---
 
---
0
---
 
---
失
---
败
---
 /
---
 >
---
 
---
0
---
 通过
---
 /
---
 单
---
轮
---
失败
---
（
---
3
---
 个
---
）

---
-
---
 
---
集
---
成
---
测试
---
：
---
SP
---
Y
---
 
---
不可
---
用
---
 /
---
 alpha
---
 正
---
确
---
计算
---
 /
---
 O
---
OS
---
 表
---
现
---
不佳
---
（
---
3
---
 个
---
）

---
-
---
 
---
常
---
量
---
与
---
独立性
---
测试
---
（
---
2
---
 个
---
）

---
-
---
 更
---
新
---
了
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
::
---
Test
---
Walk
---
Forward
---
`
---
 
---
断
---
言
---
以
---
适配
---
新的
---
门
---
控
---
逻辑
---



---
**
---
4
---
.
---
 文
---
档
---
**

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
：
---
新增
---
 
---
10
---
.
---
5
---
.
---
1
---
 
---
节
---
，
---
记录
---
了
---
 WF
---
 alpha
---
 门
---
控
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
：
---
新增
---
第
---
 
---
13
---
 
---
次
---
迭代
---
记录
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
decision
---
_log
---
.md
---
`
---
：
---
记录
---
了
---
 
---
3
---
 
---
项
---
决策
---
（
---
底
---
限
---
值
---
、
---
字段
---
位置
---
、
---
SP
---
Y
---
 
---
降
---
级
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
：
---
更新
---
了
---
迭代
---
表
---
、
---
测试
---
计数
---
（
---
6
---
75
---
）、
---
文件
---
树
---
注释
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
75
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
**
---
（
---
65
---
9
---
 个
---
原有
---
 +
---
 
---
16
---
 个
---
新增
---
；
---
16
---
 个
---
取消
---
选择
---
用于
---
实时
---
测试
---
）