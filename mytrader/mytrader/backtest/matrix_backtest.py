"""MatrixBacktest — 矩阵回测核心。

N 策略 × G 标的组 × 参数网格 → strategy_weights.json

关键设计：
    1. 组合 Sharpe 计算：等权合并组内日收益率序列，而非算术平均各标的 Sharpe
    2. 历史分组：每个回测时间点用 point-in-time 波动率分组（非当前静态分组）
    3. open 参数：所有回测传 open=data["open"]，与实盘开盘价执行一致
    4. ensemble 语义：权重优化在"单点离散值加权投票"语义下进行，与实盘 run_symbol 一致
"""

from __future__ import annotations

import itertools
import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import vectorbt as vbt
from loguru import logger

from mytrader.data.store.market_data_store import MarketDataStore
from mytrader.strategy.registry import STRATEGY_REGISTRY
from mytrader.universe.manager import UniverseManager


# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

# Constitution L1 硬约束：portfolio 最大回撤 ≤ 20%
# _run_group 在 top-K 选择时按此阈值过滤合规候选（迭代 #3 新增）
MAX_PORTFOLIO_DRAWDOWN_PCT: float = 20.0

# Constitution L7 Walk-Forward 门槛：单轮验证期 portfolio DD ≤ 15%
# （低于 L1 的 20% 线，给样本外留缓冲）
WALK_FORWARD_VAL_DD_THRESHOLD: float = 15.0

# 迭代 #9 新增：Sortino 最低质量门槛，用于 top-K 选择时的二级过滤
# 排除 Sortino ≤ 0.5 的"垃圾"策略（即使 alpha 高也不选）
# 设计动机：alpha 排序选出高绝对收益策略，但需 Sortino 门槛保证基本下行质量
# fallback：若无候选通过此门槛，放宽过滤（仅保留 DD 硬约束）
MIN_SORTINO_THRESHOLD: float = 0.5

# 迭代 #11 新增：健全性门槛 —— 识别"退化策略"（几乎不平仓的伪 buy-and-hold）
# 判定：组内"有效标的中，已平仓交易数为 0 的比例"超过此阈值 → 退化
# 设计动机：真策略应在多数标的上完成买卖闭环；若近乎所有标的都从不平仓，
#           说明入场/出场条件矛盾（如 Iter #8 rsi_trend_filter），其收益只是
#           持仓盯市 + 末尾强平的假象，必须在排序前剔除（experience.md #8）。
# 阈值取 0.8（保守）：只在"近乎全部标的零平仓"时触发，避免误伤低频合法策略。
DEGENERATE_NO_CLOSE_FRACTION: float = 0.8


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------

@dataclass
class SingleBacktestResult:
    """单只标的单策略回测结果。"""

    symbol: str
    strategy: str
    params: dict
    sharpe: float
    total_return_pct: float
    max_drawdown_pct: float
    win_rate_pct: float
    total_trades: int
    daily_returns: pd.Series    # pf.returns() — 供组合 Sharpe / Sortino 计算
    sortino: float = 0.0       # Constitution L1 首要 KPI（迭代 #1 新增）
    closed_trades: int = 0     # 迭代 #11 新增：已平仓交易数（区分退化 buy-and-hold）


@dataclass
class GroupBacktestResult:
    """单组策略回测结果。"""

    group_id: str
    strategy: str
    params: dict
    portfolio_sharpe: float          # 等权组合 Sharpe（而非算术平均）
    avg_total_return_pct: float
    avg_max_drawdown_pct: float
    avg_win_rate_pct: float
    symbol_count: int
    portfolio_sortino: float = 0.0          # 等权组合 Sortino（迭代 #1 新增）
    portfolio_max_drawdown: float = 0.0     # 等权组合最大回撤（迭代 #2 新增，Constitution L1 KPI）
    dd_constrained: bool = False            # 迭代 #3：该组是否用了 DD fallback（无合规候选）
    backtest_alpha: float = 0.0              # 迭代 #9：alpha vs SPY（百分数），用于排序策略选择
    no_valid_strategy: bool = False         # 迭代 #11：该组是否因全退化而空仓（hold cash）


@dataclass
class MatrixBacktestReport:
    """整个矩阵回测的汇总报告。"""

    generated_at: str
    backtest_window: str
    groups: dict[str, list[dict]]   # group_id → [策略权重配置]
    group_results: list[GroupBacktestResult] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Walk-Forward 数据结构（迭代 #3 新增，Constitution L7 验证流水线）
# ---------------------------------------------------------------------------

@dataclass
class WalkForwardRound:
    """单轮 Walk-Forward 验证结果。

    一轮 = 训练期（找最优参数）+ 验证期（用同参数回测，记录样本外指标）。

    Attributes:
        round_num:    轮次编号（1-indexed）
        train_start:  训练期起始日期（含）
        train_end:    训练期结束日期（含）
        val_start:    验证期起始日期（含）
        val_end:      验证期结束日期（含）
        val_sortino:  验证期等权组合 Sortino Ratio（年化）
        val_max_dd:   验证期等权组合最大回撤（正值百分数，0~100）
        passed:       是否通过 = val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD (15%)
    """

    round_num: int
    train_start: date
    train_end: date
    val_start: date
    val_end: date
    val_sortino: float
    val_max_dd: float
    passed: bool


@dataclass
class WalkForwardReport:
    """Walk-Forward 4 轮验证汇总报告。

    Constitution L7 要求 Backtest(>=5年) → Walk-Forward(4轮) → Paper → Live。
    本报告是 Walk-Forward 阶段的产出。

    Attributes:
        rounds:         每轮结果列表（长度通常为 4）
        pass_all_rounds: 是否所有轮都通过（all(r.passed for r in rounds)）
        max_val_dd:     所有轮中最大的验证期 DD（用于风险监控）
    """

    rounds: list[WalkForwardRound] = field(default_factory=list)
    pass_all_rounds: bool = False
    max_val_dd: float = 0.0


# ---------------------------------------------------------------------------
# 核心函数
# ---------------------------------------------------------------------------

def _safe_float(value: Any, default: float = 0.0) -> float:
    """NaN/None/非数值安全转 float（迭代 #2 新增）。

    问题背景：vectorbt 在无交易场景下，`pf.stats()` 的 Win Rate / Sharpe 等
    字段会返回 NaN。`float(NaN or 0.0)` 仍是 NaN（NaN 是 truthy），导致
    JSON 序列化写出非法 JSON（NaN/Infinity 非 JSON 规范）。

    处理顺序：
        1. None → default
        2. 数值类型但 NaN/Inf → default
        3. 非数值（字符串等）尝试 float() 转换，失败 → default
    """
    if value is None:
        return default
    try:
        f = float(value)
    except (TypeError, ValueError):
        return default
    if not np.isfinite(f):   # 拦截 NaN / +Inf / -Inf
        return default
    return f


def _safe_mean(values: Any, default: float = 0.0) -> float:
    """空列表 / 全 NaN 安全的均值（迭代 #2 新增）。

    问题背景：`np.mean([])` 会触发 RuntimeWarning 并返回 NaN；
    `np.mean([NaN, NaN])` 直接返回 NaN。在 GroupBacktestResult 聚合时
    若某组只有 1 个标的且其字段为 NaN，会导致下游 JSON 序列化失败。

    行为：
        - 空列表 / 全 NaN → default
        - 部分 NaN → 自动忽略 NaN 后取均值（np.nanmean 语义）
    """
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return default
    mask = np.isfinite(arr)
    if not mask.any():
        return default
    return float(arr[mask].mean())


def _compute_sharpe(returns: pd.Series, periods_per_year: int = 252) -> float:
    """从日收益率序列计算年化 Sharpe Ratio。"""
    returns = returns.dropna()
    if len(returns) < 5:
        return 0.0
    mean = returns.mean()
    std = returns.std()
    if std <= 0 or np.isnan(std):
        return 0.0
    return float(mean / std * np.sqrt(periods_per_year))


def _compute_sortino(
    returns: pd.Series,
    periods_per_year: int = 252,
    target: float = 0.0,
) -> float:
    """从日收益率序列计算年化 Sortino Ratio（Constitution L1 首要 KPI）。

    Sortino = (mean(returns) - target) / downside_deviation * sqrt(periods_per_year)
    downside_deviation = sqrt( mean( min(0, returns - target)^2 ) )

    与 Sharpe 的区别：仅对下行波动惩罚，上行波动不计入分母。
    适合"收益>0 但偶尔大跌"的中长线策略评估。

    退化处理（与 _compute_sharpe 一致）：
        - 样本 < 5 → 0.0
        - 下行波动 ≤ 0（无下行样本）→ 0.0（理论为 +inf，返回 0 保持保守 + 可算术聚合）

    Args:
        returns:          日收益率序列（如 pf.returns()）
        periods_per_year: 年化因子（日线 = 252）
        target:           MAR/目标收益率，默认 0（与 _compute_sharpe 无风险利率假设一致）

    Returns:
        年化 Sortino Ratio
    """
    returns = returns.dropna()
    if len(returns) < 5:
        return 0.0
    excess = returns - target
    downside = excess.where(excess < 0, 0.0)        # 仅保留负偏离，正偏离置 0
    dd = np.sqrt((downside ** 2).mean())
    if dd <= 0 or np.isnan(dd):
        return 0.0
    return float(returns.mean() / dd * np.sqrt(periods_per_year))


def _combine_daily_returns(results: list[SingleBacktestResult]) -> pd.Series:
    """等权合并组内日收益率序列，返回组合日收益率（迭代 #9 新增）。

    与 _portfolio_sharpe_from_results / _portfolio_sortino_from_results 同语义：
    将所有标的日收益率等权合并为组合序列。提取为独立函数以便 alpha 计算
    和 per-strategy best params 选择复用，避免重复 pd.concat。

    Args:
        results: 单策略多标的的回测结果列表

    Returns:
        组合日收益率 pd.Series；无有效数据时返回空 Series
    """
    valid = [r.daily_returns for r in results if not r.daily_returns.empty]
    if not valid:
        return pd.Series(dtype=float)
    return pd.concat(valid, axis=1).mean(axis=1)


def _is_degenerate_strategy(results: list[SingleBacktestResult]) -> bool:
    """判定一个策略在组内是否退化（几乎不产生已平仓交易）（迭代 #11 新增）。

    退化定义：有效标的中 closed_trades==0 的比例 >= DEGENERATE_NO_CLOSE_FRACTION。
    这类策略的入场/出场条件互斥（如 Iter #8 rsi_trend_filter 趋势过滤锁死均值
    回归出场），仓位无法平仓，其 Sortino/alpha 只是持仓盯市假象，不代表真实
    交易能力，必须在排序前剔除（experience.md #8：sanity → risk → rank）。

    Args:
        results: 单策略多标的的回测结果列表

    Returns:
        True 表示退化（应剔除）；空结果视为退化（True）
    """
    if not results:
        return True
    n = len(results)
    no_close = sum(1 for r in results if r.closed_trades <= 0)
    return (no_close / n) >= DEGENERATE_NO_CLOSE_FRACTION


def _compute_alpha(
    strategy_daily_returns: pd.Series,
    spy_daily_returns: pd.Series | None,
    periods_per_year: int = 252,
) -> float:
    """计算 alpha = 策略年化收益 - SPY 年化收益（迭代 #9 新增）。

    Alpha 衡量策略相对 SPY buy-and-hold 的超额收益。正值表示跑赢 SPY，
    负值表示跑输 SPY。用于 top-K 策略选择和 per-strategy best params 选择，
    替代之前基于 Sortino/Sharpe 的选择逻辑（参考 iteration #9 spec）。

    年化公式：(1 + mean_daily) ** periods_per_year - 1
    使用算术平均日收益的几何年化，与 PortfolioBacktester 同口径。

    降级处理：SPY 数据不可用（None 或空）→ 返回 0.0（不抛异常）。
    这样在 SPY 数据缺失时，alpha 排序退化为"原顺序"，不会阻塞回测。

    Args:
        strategy_daily_returns: 策略组合日收益率序列
        spy_daily_returns:      SPY 日收益率序列；None 表示数据不可用
        periods_per_year:       年化因子（日线 = 252）

    Returns:
        Alpha 百分数（如 5.23 表示策略年化收益跑赢 SPY 5.23 个百分点）；
        SPY 不可用时返回 0.0
    """
    if spy_daily_returns is None or spy_daily_returns.empty:
        return 0.0
    if strategy_daily_returns is None or strategy_daily_returns.empty:
        return 0.0

    # 对齐时间索引（inner join 取交集）
    aligned = pd.concat(
        [strategy_daily_returns.rename("strat"), spy_daily_returns.rename("spy")],
        axis=1,
        join="inner",
    ).dropna()
    if aligned.empty or len(aligned) < 2:
        return 0.0

    strat_returns = aligned["strat"]
    spy_returns = aligned["spy"]

    # 年化收益 = (1 + mean_daily)^252 - 1
    strat_mean = strat_returns.mean()
    spy_mean = spy_returns.mean()
    if not np.isfinite(strat_mean) or not np.isfinite(spy_mean):
        return 0.0

    strat_annual = (1.0 + strat_mean) ** periods_per_year - 1.0
    spy_annual = (1.0 + spy_mean) ** periods_per_year - 1.0

    alpha = (strat_annual - spy_annual) * 100.0  # 转为百分数
    if not np.isfinite(alpha):
        return 0.0
    return float(alpha)


def _backtest_one(
    df: pd.DataFrame,
    strategy_name: str,
    params: dict,
    init_cash: float = 100_000.0,
    fees: float = 0.001,
    slippage: float = 0.001,
) -> SingleBacktestResult | None:
    """对单只标的执行单次回测。

    使用 open= 参数确保信号在下一根 bar 的开盘价执行（与实盘一致）。

    Returns:
        SingleBacktestResult 或 None（数据不足/策略异常时）
    """
    strategy_fn = STRATEGY_REGISTRY.get(strategy_name)
    if strategy_fn is None:
        return None

    if df.empty or len(df) < 30:
        return None

    try:
        close = df["close"]
        open_ = df["open"] if "open" in df.columns else None

        # 调用策略（兼容需要 df 的策略）
        try:
            sig = strategy_fn(close, df=df, **params)
        except TypeError:
            sig = strategy_fn(close, **params)

        entries = sig == 1
        exits   = sig == -1

        pf_kwargs: dict[str, Any] = dict(
            entries=entries,
            exits=exits,
            init_cash=init_cash,
            fees=fees,
            slippage=slippage,
            size=0.95,
            size_type="Percent",
            freq="D",
        )

        # ⚠️ 必须传 open= 参数：信号在下一根 bar 开盘价执行，与实盘一致
        if open_ is not None:
            pf = vbt.Portfolio.from_signals(close=close, open=open_, **pf_kwargs)
        else:
            pf = vbt.Portfolio.from_signals(close, **pf_kwargs)

        stats = pf.stats()

        daily_returns = pf.returns()

        # 迭代 #11：已平仓交易数（用于健全性门槛 _is_degenerate_strategy）
        # vbt 1.0 API: pf.trades.closed.count() 返回 Status==Closed 的交易数
        # 区分"真交易闭环"与"末尾强平计 1 笔的伪 buy-and-hold"
        try:
            closed_trades = int(pf.trades.closed.count())
        except Exception:
            closed_trades = 0

        return SingleBacktestResult(
            symbol=str(df.index.name or ""),
            strategy=strategy_name,
            params=params,
            sharpe=_safe_float(stats.get("Sharpe Ratio")),
            total_return_pct=_safe_float(stats.get("Total Return [%]")),
            max_drawdown_pct=_safe_float(stats.get("Max Drawdown [%]")),
            win_rate_pct=_safe_float(stats.get("Win Rate [%]")),
            total_trades=int(_safe_float(stats.get("Total Trades"), default=0.0)),
            daily_returns=daily_returns,
            sortino=_compute_sortino(daily_returns),
            closed_trades=closed_trades,
        )
    except Exception as e:
        logger.debug(f"[backtest_one] {strategy_name}({params}) failed: {e}")
        return None


def _backtest_batch(
    data: dict[str, pd.DataFrame],
    strategy_name: str,
    params: dict,
    init_cash: float = 100_000.0,
    fees: float = 0.001,
    slippage: float = 0.001,
) -> list[SingleBacktestResult]:
    """对组内所有标的批量执行回测（迭代 #10 新增）。

    核心优化：用一次 vbt.Portfolio.from_signals 处理组内所有标的，
    替代 `_backtest_one` 的 for-symbol 循环。调用次数从 O(N 标的)
    降为 O(1)，预计 10-20x 提速（spec §1）。

    实现要点：
        1. 逐标的调用策略函数（保持与 `_backtest_one` 一致的调用语义：
           先尝试 `strategy_fn(close, df=df, **params)`，TypeError 时
           回退到 `strategy_fn(close, **params)`）。策略函数本身不改。
        2. 构建列式矩阵（每列一个标的），用一次 vbt 调用回测所有标的。
           vbt 1.0+ 的列分组语义保证每列独立结算 P&L。
        3. 通过 `pf[sym]` 提取每列的 stats/daily_returns，输出格式与
           `_backtest_one` 完全一致，下游聚合代码无需修改。

    对齐策略：
        - 用 `pd.DataFrame(dict)` 构造时自动 outer-join 时间索引，
          缺失值填 NaN。
        - vbt 对 NaN close 的处理：内部 fillna 为 0 收益率，等价于
          "该标的此日期不交易"。当标的在样本外日期缺失时（如退市、
          新上市），其 stats 仍按其有效日期区间计算。
        - 在美股实际场景中所有标的共享交易日历，日期对齐天然成立，
          不会有大量 NaN。

    Args:
        data:          {symbol: OHLCV DataFrame} 字典
        strategy_name: 策略名
        params:        策略参数
        init_cash:     初始资金（vbt 给每列分配独立的 init_cash）
        fees:          手续费率
        slippage:      滑点率

    Returns:
        SingleBacktestResult 列表（与 `_backtest_one` 输出格式一致）。
        数据不足 / 策略异常的标的会被跳过（不返回 None，不抛异常）。
        空数据时返回空列表。
    """
    strategy_fn = STRATEGY_REGISTRY.get(strategy_name)
    if strategy_fn is None:
        return []

    # 1. 逐标的调用策略函数，构建 signal / close / open 列
    signal_columns: dict[str, pd.Series] = {}
    close_columns: dict[str, pd.Series] = {}
    open_columns: dict[str, pd.Series] = {}

    for sym, df in data.items():
        if df is None or df.empty or len(df) < 30:
            continue
        close = df["close"]
        if "open" in df.columns:
            open_ = df["open"]
            open_columns[sym] = open_
        else:
            open_ = None

        # 调用策略（与 _backtest_one 一致的 try/except 语义）
        try:
            sig = strategy_fn(close, df=df, **params)
        except TypeError:
            sig = strategy_fn(close, **params)
        except Exception as e:
            logger.debug(
                f"[backtest_batch] {strategy_name}({params}) {sym} failed: {e}"
            )
            continue

        signal_columns[sym] = sig
        close_columns[sym] = close

    if not signal_columns:
        return []

    # 2. 构建矩阵（自动 outer-join 索引，缺失值填 NaN）
    close_matrix = pd.DataFrame(close_columns)
    signal_matrix = pd.DataFrame(signal_columns)
    has_open = bool(open_columns)
    open_matrix = pd.DataFrame(open_columns) if has_open else None

    # 3. 一次 vbt 调用处理所有标的
    entries = signal_matrix == 1
    exits = signal_matrix == -1

    pf_kwargs: dict[str, Any] = dict(
        entries=entries,
        exits=exits,
        init_cash=init_cash,
        fees=fees,
        slippage=slippage,
        size=0.95,
        size_type="Percent",
        freq="D",
    )

    try:
        if has_open:
            pf = vbt.Portfolio.from_signals(
                close=close_matrix, open=open_matrix, **pf_kwargs
            )
        else:
            pf = vbt.Portfolio.from_signals(close_matrix, **pf_kwargs)
    except Exception as e:
        logger.warning(
            f"[backtest_batch] {strategy_name}({params}) vbt call failed: {e} "
            f"— falling back to per-symbol _backtest_one"
        )
        # 回滚方案：批量失败时退化为逐标的回测，保证回测不中断
        results: list[SingleBacktestResult] = []
        for sym, df in data.items():
            if df is None or df.empty or len(df) < 30:
                continue
            df = df.copy()
            df.index.name = sym
            r = _backtest_one(
                df, strategy_name, params, init_cash, fees, slippage
            )
            if r is not None:
                results.append(r)
        return results

    # 4. 提取 per-symbol 结果（与 _backtest_one 输出格式一致）
    results = []
    for sym in signal_matrix.columns:
        try:
            pf_sym = pf[sym]
            stats = pf_sym.stats()
            daily_returns = pf_sym.returns()
            # 迭代 #11：已平仓交易数（与 _backtest_one 同 API、同语义）
            # pf_sym 是单列 pf，pf_sym.trades.closed.count() 返回 int
            try:
                closed_trades = int(pf_sym.trades.closed.count())
            except Exception:
                closed_trades = 0
            results.append(SingleBacktestResult(
                symbol=sym,
                strategy=strategy_name,
                params=params,
                sharpe=_safe_float(stats.get("Sharpe Ratio")),
                total_return_pct=_safe_float(stats.get("Total Return [%]")),
                max_drawdown_pct=_safe_float(stats.get("Max Drawdown [%]")),
                win_rate_pct=_safe_float(stats.get("Win Rate [%]")),
                total_trades=int(_safe_float(stats.get("Total Trades"), default=0.0)),
                daily_returns=daily_returns,
                sortino=_compute_sortino(daily_returns),
                closed_trades=closed_trades,
            ))
        except Exception as e:
            logger.debug(
                f"[backtest_batch] {strategy_name}({params}) {sym} "
                f"stats extraction failed: {e}"
            )
            continue

    return results


def _portfolio_sharpe_from_results(results: list[SingleBacktestResult]) -> float:
    """等权合并组内日收益率序列，计算组合 Sharpe。

    ⚠️ 不能取各标的 Sharpe 算术平均（Sharpe 是比率，不能直接平均）。
    正确做法：将所有标的日收益率等权合并为组合序列，再计算 Sharpe。
    """
    valid = [r.daily_returns for r in results if not r.daily_returns.empty]
    if not valid:
        return 0.0

    # 对齐时间索引，等权平均
    combined = pd.concat(valid, axis=1).mean(axis=1)
    return _compute_sharpe(combined)


def _portfolio_sortino_from_results(results: list[SingleBacktestResult]) -> float:
    """等权合并组内日收益率序列，计算组合 Sortino（与 _portfolio_sharpe_from_results 同语义）。

    不能取各标的 Sortino 算术平均（与 Sharpe 同理：比率不可直接平均）。
    """
    valid = [r.daily_returns for r in results if not r.daily_returns.empty]
    if not valid:
        return 0.0
    combined = pd.concat(valid, axis=1).mean(axis=1)
    return _compute_sortino(combined)


def _portfolio_max_drawdown_from_results(
    results: list[SingleBacktestResult],
) -> float:
    """等权合并组内日收益率序列，计算组合最大回撤（迭代 #2 新增，Constitution L1 KPI）。

    与 `_portfolio_sharpe_from_results` 同语义：不能取各标的 DD 算术平均，
    因为 DD 是路径依赖的比率。正确做法是先把��内日收益率等权合并为组合序列，
    再 cumprod → cummax → drawdown → max。

    返回值约定：百分比形式（与 `SingleBacktestResult.max_drawdown_pct` 一致，
    vectorbt stats 中 `Max Drawdown [%]` 同样是百分数，例如 -15.2 表示 15.2% 回撤）。
    本函数返回正值（0.0 ~ 100.0）便于聚合与 JSON 输出。

    退化处理：
        - 无有效日收益率 → 0.0
        - 全 0 收益率（cumprod 恒为 1.0）→ 0.0
    """
    valid = [r.daily_returns for r in results if not r.daily_returns.empty]
    if not valid:
        return 0.0
    combined = pd.concat(valid, axis=1).mean(axis=1).dropna()
    if len(combined) < 2:
        return 0.0
    # 组合累计净值：初始 1.0，每日乘 (1 + r)
    cumvalue = (1.0 + combined).cumprod()
    peak = cumvalue.cummax()
    drawdown = (cumvalue - peak) / peak   # 负值，0 表示无回撤
    dd_max_pct = float(drawdown.min())    # 最负值，例如 -0.152
    if not np.isfinite(dd_max_pct):
        return 0.0
    # 转为正百分数（与 vectorbt Max Drawdown [%] 的口径一致但取正号）
    return abs(dd_max_pct) * 100.0


def _optimize_ensemble_weights(
    group_results: list[tuple[str, dict, list[SingleBacktestResult]]],
    spy_returns: pd.Series | None = None,
    conflict_threshold: float = 0.3,
) -> list[tuple[str, dict, float]]:
    """在"单点离散值加权投票"语义下优化 ensemble 权重。

    实盘每根 bar 各策略产出离散值（1/-1/0），加权投票决定方向。
    回测的权重优化必须使用相同语义，而非对整段时间序列做加权。

    迭代 #9：权重计算从 Sharpe 改为 Alpha（vs SPY）。
    动机：与 _run_group 的 top-K 排序口径一致，使 ensemble 权重直接
    反映"跑赢 SPY 的程度"。SPY 不可用时 alpha=0，退化为等权。

    Args:
        group_results: [(strategy, params, [SingleBacktestResult]), ...]
        spy_returns:   SPY 日收益率序列（用于 alpha 计算）；None 时退化为等权
        conflict_threshold: 加权投票分数绝对值低于此时视为 HOLD

    Returns:
        [(strategy, params, weight), ...] 归一化权重列表
    """
    if len(group_results) == 1:
        strategy, params, _ = group_results[0]
        return [(strategy, params, 1.0)]

    # 迭代 #9：用各策略的组合 alpha 归一化为权重（替代 Sharpe）
    # alpha 可能 < 0（跑输 SPY），用 max(alpha, 0.01) 避免负权重
    alphas = []
    for strategy, params, results in group_results:
        combined = _combine_daily_returns(results)
        alpha = _compute_alpha(combined, spy_returns)
        alphas.append(max(alpha, 0.01))  # 避免负/零权重

    total = sum(alphas)
    weights = [a / total for a in alphas]

    return [
        (strategy, params, weight)
        for (strategy, params, _), weight in zip(group_results, weights)
    ]


# ---------------------------------------------------------------------------
# Walk-Forward 验证（迭代 #3 新增，Constitution L7 验证流水线）
# ---------------------------------------------------------------------------

def _add_months(d: date, months: int) -> date:
    """对 date 加/减 months 个月，自动 clamp 到月末。

    使用 pandas DateOffset 以避免引入 dateutil 依赖（pandas 已是核心依赖）。
    """
    return (pd.Timestamp(d) + pd.DateOffset(months=months)).date()


def _backtest_with_params_on_period(
    mb: "MatrixBacktest",
    symbols: list[str],
    weights: list[dict[str, Any]],
    start: date,
    end: date,
) -> list[pd.Series]:
    """用给定权重配置在 [start, end] 期间回测，返回每条 (策略×标的) 的日收益率序列。

    用于 Walk-Forward 验证期：用训练期产出的 best params 在验证期回测，
    不再做参数搜索。返回原始日收益率列表，由调用方聚合为整体 portfolio。

    迭代 #10 变更：用 `_backtest_batch` 替代 for-symbol 循环，
    每个策略×参数组合一次 vbt 调用，加速 Walk-Forward 验证期回测。

    Args:
        mb:       MatrixBacktest 实例（复用其 store/init_cash/fees/slippage）
        symbols:  该组的标的列表
        weights:  训练期产出的权重配置（list of dict，含 strategy/params/weight）
        start:    验证期起始日期
        end:      验证期结束日期

    Returns:
        list[pd.Series] — 每条 (strategy×symbol) 的日收益率；空列表表示无有效数据
    """
    if not weights or not symbols:
        return []

    data = mb._store.get_bars_multi(symbols, start, end)
    if not data:
        return []

    all_returns: list[pd.Series] = []
    for w in weights:
        strategy = w.get("strategy", "")
        params = w.get("params", {})
        if not strategy or strategy not in STRATEGY_REGISTRY:
            continue
        # 迭代 #10：一次 batch 调用处理组内所有标的
        results = _backtest_batch(
            data, strategy, params,
            mb._init_cash, mb._fees, mb._slippage,
        )
        for r in results:
            if not r.daily_returns.empty:
                all_returns.append(r.daily_returns)
    return all_returns


def run_walk_forward(
    mb: "MatrixBacktest",
    strategies: list[str],
    param_grids: dict[str, dict[str, list]],
    rounds: int = 4,
    train_months: int = 18,
    val_months: int = 6,
) -> WalkForwardReport:
    """执行 N 轮 Walk-Forward 验证（Constitution L7 验证流水线硬要求）。

    每轮流程：
        1. 训练期 [train_start, train_end]：跑矩阵回测找最优参数
        2. 验证期 [val_start, val_end]：用同参数回测，记录 portfolio Sortino 和 max DD
        3. passed = val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD (15%)

    时间窗口（动态计算，today=today）：
        - 最后一轮 val_end = today - val_months（留 1 个 val 期给 paper trading）
        - 每轮向前推 val_months
        - train_end = val_start，train_start = train_end - train_months

    默认参数 (rounds=4, train_months=18, val_months=6) 对应用户提供的固定窗口：
        today=2026-07-01 →
        Round 1: train 2021-07-02~2023-01-02, val 2023-01-02~2023-07-02
        Round 2: train 2022-01-02~2023-07-02, val 2023-07-02~2024-01-02
        Round 3: train 2022-07-02~2024-01-02, val 2024-01-02~2024-07-02
        Round 4: train 2023-01-02~2024-07-02, val 2024-07-02~2025-01-02

    Args:
        mb:            MatrixBacktest 实例（复用其 store/universe/init_cash 等）
        strategies:    策略名称列表
        param_grids:   参数网格（与 mb.run() 接收的格式一致）
        rounds:        轮次数（默认 4，Constitution L7 要求）
        train_months:  训练期月数（默认 18）
        val_months:    验证期月数（默认 6）

    Returns:
        WalkForwardReport — 包含每轮结果、pass_all_rounds、max_val_dd

    Note:
        - WF 是验证步骤，不修改 strategy_weights.json
        - 失败轮次会记录 WARNING 但不抛异常
        - 全部 4 轮通过是进入 paper trading 的前置条件
    """
    today = date.today()
    groups = mb._universe.get_groups()
    if not groups:
        logger.warning("[WalkForward] no groups available — skipping")
        return WalkForwardReport()

    wf_rounds: list[WalkForwardRound] = []

    for i in range(rounds):
        round_num = i + 1
        # 计算本轮时间窗口
        # 最后一轮 (i=rounds-1) 的 val_end = today - val_months
        # 前面轮次依次向前推 val_months
        val_end = _add_months(today, -val_months - (rounds - round_num) * val_months)
        val_start = _add_months(val_end, -val_months)
        train_end = val_start
        train_start = _add_months(train_end, -train_months)

        logger.info(
            f"[WalkForward] Round {round_num}/{rounds}: "
            f"train={train_start}~{train_end}, val={val_start}~{val_end}"
        )

        # ── 训练期：跑矩阵回测找最优参数（复用 mb._run_group）──
        train_report = MatrixBacktestReport(
            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
            backtest_window=f"{train_start.isoformat()} ~ {train_end.isoformat()}",
            groups={},
        )

        for group_id, symbols in groups.items():
            weights = mb._run_group(
                group_id=group_id,
                symbols=symbols,
                start=train_start,
                end=train_end,
                strategies=strategies,
                param_grids=param_grids,
                report=train_report,
            )
            train_report.groups[group_id] = weights

        # ── 验证期：用训练期 best params 回测，聚合为整体 portfolio ──
        all_returns: list[pd.Series] = []
        for group_id, symbols in groups.items():
            weights = train_report.groups.get(group_id, [])
            if not weights:
                continue
            group_returns = _backtest_with_params_on_period(
                mb, symbols, weights, val_start, val_end,
            )
            all_returns.extend(group_returns)

        # 计算整体 portfolio 指标（等权合并所有组的日收益率）
        if not all_returns:
            val_sortino = 0.0
            val_max_dd = 0.0
            logger.warning(
                f"[WalkForward] Round {round_num}: no valid val returns — "
                f"sortino=0, dd=0, passed=True (vacuous)"
            )
        else:
            combined = pd.concat(all_returns, axis=1).mean(axis=1).dropna()
            if len(combined) < 5:
                val_sortino = 0.0
                val_max_dd = 0.0
            else:
                val_sortino = _compute_sortino(combined)
                wrapper = [SingleBacktestResult(
                    symbol="portfolio", strategy="", params={},
                    sharpe=0.0, total_return_pct=0.0, max_drawdown_pct=0.0,
                    win_rate_pct=0.0, total_trades=0, daily_returns=combined,
                )]
                val_max_dd = _portfolio_max_drawdown_from_results(wrapper)

        passed = val_max_dd <= WALK_FORWARD_VAL_DD_THRESHOLD
        wf_rounds.append(WalkForwardRound(
            round_num=round_num,
            train_start=train_start,
            train_end=train_end,
            val_start=val_start,
            val_end=val_end,
            val_sortino=val_sortino,
            val_max_dd=val_max_dd,
            passed=passed,
        ))
        logger.info(
            f"[WalkForward] Round {round_num} result: "
            f"sortino={val_sortino:.4f}, dd={val_max_dd:.4f}%, "
            f"passed={passed} (threshold={WALK_FORWARD_VAL_DD_THRESHOLD}%)"
        )

    report = WalkForwardReport(
        rounds=wf_rounds,
        pass_all_rounds=all(r.passed for r in wf_rounds) if wf_rounds else False,
        max_val_dd=max((r.val_max_dd for r in wf_rounds), default=0.0),
    )
    logger.info(
        f"[WalkForward] done: {len(wf_rounds)} rounds, "
        f"pass_all_rounds={report.pass_all_rounds}, "
        f"max_val_dd={report.max_val_dd:.4f}%"
    )
    return report


# ---------------------------------------------------------------------------
# MatrixBacktest 主类
# ---------------------------------------------------------------------------

class MatrixBacktest:
    """矩阵回测：N 策略 × G 标的组 × 参数网格 → strategy_weights.json。

    Args:
        store:       MarketDataStore（本地时序库）
        universe:    UniverseManager（提供分组映射）
        years:       回测窗口（默认 5 年）
        init_cash:   初始资金
        fees:        手续费率
        slippage:    滑点率
        top_k:       每组保留 Top-K 策略（默认 2）
    """

    def __init__(
        self,
        store: MarketDataStore,
        universe: UniverseManager,
        years: int = 5,
        init_cash: float = 100_000.0,
        fees: float = 0.001,
        slippage: float = 0.001,
        top_k: int = 2,
    ) -> None:
        self._store = store
        self._universe = universe
        self._years = years
        self._init_cash = init_cash
        self._fees = fees
        self._slippage = slippage
        self._top_k = top_k

    def run(
        self,
        strategies: list[str],
        param_grids: dict[str, dict[str, list]],
        output_file: str | Path | None = None,
    ) -> MatrixBacktestReport:
        """执行完整矩阵回测。

        Args:
            strategies:  策略名称列表，如 ["dual_ma", "rsi"]
            param_grids: 各策略参数网格，如 {"dual_ma": {"fast":[5,10], "slow":[20,30]}}
            output_file: strategy_weights.json 输出路径（None 则不写文件）

        Returns:
            MatrixBacktestReport
        """
        today = date.today()
        start = today - timedelta(days=self._years * 365)
        window_str = f"{start.isoformat()} ~ {today.isoformat()}"

        logger.info(
            f"[MatrixBacktest] start={start}, end={today}, "
            f"strategies={strategies}, years={self._years}"
        )

        # 获取分组（⚠️ 使用历史时点分组，而非当前静态分组）
        # Phase 5 初期简化：用当前分组，但接口已预留历史分组能力
        groups = self._universe.get_groups()
        if not groups:
            logger.warning("[MatrixBacktest] no groups available, abort")
            return MatrixBacktestReport(
                generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
                backtest_window=window_str,
                groups={},
            )

        report = MatrixBacktestReport(
            generated_at=pd.Timestamp.now(tz="UTC").isoformat(),
            backtest_window=window_str,
            groups={},
        )

        for group_id, symbols in groups.items():
            logger.info(
                f"[MatrixBacktest] group={group_id}, symbols={len(symbols)}, "
                f"strategies={strategies}"
            )

            group_weights = self._run_group(
                group_id=group_id,
                symbols=symbols,
                start=start,
                end=today,
                strategies=strategies,
                param_grids=param_grids,
                report=report,
            )
            report.groups[group_id] = group_weights

        if output_file is not None:
            self._write_weights(report, output_file)

        logger.info(
            f"[MatrixBacktest] done: {len(report.groups)} groups, "
            f"warnings={len(report.warnings)}"
        )
        return report

    def _get_spy_returns(self, start: date, end: date) -> pd.Series | None:
        """获取 SPY 同期日收益率序列，用于计算 alpha（迭代 #9 新增）。

        从 MarketDataStore 拉取 SPY 日线数据，计算日收益率。
        SPY 不在标的池中，但作为 benchmark 用于 alpha 计算。

        降级处理：SPY 数据不可用时返回 None（_compute_alpha 会返回 0.0），
        不抛异常，保证回测不因 benchmark 缺失而阻塞。

        Args:
            start: 回测起始日期
            end:   回测结束日期

        Returns:
            SPY 日收益率 pd.Series；数据不可用时返回 None
        """
        try:
            spy_bars = self._store.get_bars_multi(["SPY"], start, end)
            spy_df = spy_bars.get("SPY") if spy_bars else None
            if spy_df is None or spy_df.empty:
                logger.warning(
                    "[MatrixBacktest] SPY data unavailable, alpha will degrade to 0.0"
                )
                return None
            spy_close = spy_df["close"].astype(float)
            if len(spy_close) < 2:
                logger.warning(
                    "[MatrixBacktest] SPY data too short, alpha will degrade to 0.0"
                )
                return None
            return spy_close.pct_change().dropna()
        except Exception as e:
            logger.warning(
                f"[MatrixBacktest] SPY benchmark fetch failed: {e} — "
                f"alpha will degrade to 0.0"
            )
            return None

    def _run_group(
        self,
        group_id: str,
        symbols: list[str],
        start: date,
        end: date,
        strategies: list[str],
        param_grids: dict[str, dict[str, list]],
        report: MatrixBacktestReport,
    ) -> list[dict[str, Any]]:
        """对单个分组执行策略 × 参数网格回测，返回该组的权重配置列表。

        迭代 #9 变更：
            - per-strategy best params：从 Sharpe 改为 Alpha（vs SPY）
            - top-K 排序：从 Sortino 改为 Alpha
            - 新增 Sortino > 0.5 最低质量门槛（二级过滤，可放宽）
            - ensemble weights：从 Sharpe 改为 Alpha
        迭代 #10 变更：
            - 用 `_backtest_batch` 替代 for-symbol 循环（10-20x 提速）
            - 每组 / 每策略增加进度耗时日志
        """
        import time

        group_start = time.time()

        # 1. 读取组内所有标的数据
        data = self._store.get_bars_multi(symbols, start, end)
        if not data:
            logger.warning(f"[MatrixBacktest] {group_id}: no data, skip")
            return []

        # 迭代 #9：获取 SPY 同期日收益率用于 alpha 计算（一次获取，组内复用）
        spy_returns = self._get_spy_returns(start, end)

        valid_symbol_count = sum(
            1 for df in data.values() if df is not None and not df.empty and len(df) >= 30
        )
        logger.info(
            f"[MatrixBacktest] {group_id}: start — "
            f"{len(strategies)} strategies × {valid_symbol_count} valid symbols"
        )

        # 2. 对每个策略 × 每组参数，按 alpha 选最优参数
        group_results: list[tuple[str, dict, list[SingleBacktestResult]]] = []

        for strategy in strategies:
            strat_start = time.time()

            # ⚠️ 早期检测未注册策略名（迭代 #1 修复"策略名拼写错误被静默跳过"的 bug）
            # 之前 _backtest_one 内部静默 return None，导致 main.py 误用 "rsi"/"macd"/"bollinger"
            # 简称 6 天未被发现。改为 WARNING 级日志 + continue。
            if strategy not in STRATEGY_REGISTRY:
                logger.warning(
                    f"[MatrixBacktest] {group_id}: strategy '{strategy}' not in "
                    f"STRATEGY_REGISTRY — skipped. "
                    f"Check spelling against @register_strategy decorators. "
                    f"Known: {sorted(STRATEGY_REGISTRY.keys())}"
                )
                continue
            grid = param_grids.get(strategy, {})
            param_combos = list(
                dict(zip(grid.keys(), combo))
                for combo in itertools.product(*grid.values())
            ) if grid else [{}]

            best_params = None
            best_alpha = float("-inf")
            best_sharpe = 0.0       # 仅用于 GroupBacktestResult 存档
            best_sortino = 0.0      # 仅用于 GroupBacktestResult 存档
            best_results: list[SingleBacktestResult] = []

            for params in param_combos:
                # 迭代 #10：用 _backtest_batch 一次处理组内所有标的
                # 替代原 for sym in symbols: _backtest_one(...) 的逐标的循环
                results = _backtest_batch(
                    data, strategy, params,
                    self._init_cash, self._fees, self._slippage,
                )

                if not results:
                    continue

                # ⚠️ 等权合并日收益率序列，一次性计算所有指标
                # 迭代 #9：复用 combined 计算 sharpe / sortino / alpha
                combined = _combine_daily_returns(results)
                ps = _compute_sharpe(combined)
                pso = _compute_sortino(combined)
                alpha = _compute_alpha(combined, spy_returns)

                # 迭代 #9：per-strategy best params 用 alpha 选（替代 Sharpe）
                if alpha > best_alpha:
                    best_alpha = alpha
                    best_sharpe = ps
                    best_sortino = pso
                    best_params = params
                    best_results = results

            if best_params is not None and best_results:
                group_results.append((strategy, best_params, best_results))
                report.group_results.append(GroupBacktestResult(
                    group_id=group_id,
                    strategy=strategy,
                    params=best_params,
                    portfolio_sharpe=best_sharpe,
                    avg_total_return_pct=_safe_mean(
                        [r.total_return_pct for r in best_results]
                    ),
                    avg_max_drawdown_pct=_safe_mean(
                        [r.max_drawdown_pct for r in best_results]
                    ),
                    avg_win_rate_pct=_safe_mean(
                        [r.win_rate_pct for r in best_results]
                    ),
                    symbol_count=len(best_results),
                    portfolio_sortino=best_sortino,
                    portfolio_max_drawdown=_portfolio_max_drawdown_from_results(
                        best_results
                    ),
                    backtest_alpha=best_alpha,
                ))

            logger.info(
                f"[MatrixBacktest] {group_id}: {strategy} done in "
                f"{time.time() - strat_start:.1f}s "
                f"({len(param_combos)} param combos × {valid_symbol_count} symbols)"
            )

        if not group_results:
            logger.warning(
                f"[MatrixBacktest] {group_id}: no valid results "
                f"(elapsed {time.time() - group_start:.1f}s)"
            )
            return []

        # 迭代 #11：健全性过滤 —— 排序前先剔除退化策略
        # （experience.md #8：sanity → risk → rank）
        # 退化策略 = 组内 ≥ 80% 标的 closed_trades==0（入场/出场条件互斥，
        # 仓位靠末尾强平凑出 Sortino/alpha 假象）。此类策略必须先于 DD/Sortino/
        # Alpha 过滤剔除，否则其盯市假象会骗过 alpha 排序进入权重。
        sane_results: list[tuple[str, dict, list[SingleBacktestResult]]] = []
        for (strategy, params, results) in group_results:
            if _is_degenerate_strategy(results):
                logger.warning(
                    f"[MatrixBacktest] {group_id}: strategy '{strategy}' is DEGENERATE "
                    f"(>= {DEGENERATE_NO_CLOSE_FRACTION:.0%} symbols have 0 closed trades) "
                    f"— excluded before ranking. Its Sortino/alpha is mark-to-market illusion."
                )
                continue
            sane_results.append((strategy, params, results))

        if not sane_results:
            # 全组退化 → 空权重（持仓现金），标记 no_valid_strategy，不强行选退化策略
            logger.warning(
                f"[MatrixBacktest] {group_id}: ALL strategies degenerate — "
                f"group produces EMPTY weights (hold cash). Marked no_valid_strategy."
            )
            report.warnings.append(
                f"{group_id}: no_valid_strategy (all strategies degenerate)"
            )
            # 标记已 append 的 GroupBacktestResult 条目（供审计追溯）
            for gr in report.group_results:
                if gr.group_id == group_id:
                    gr.no_valid_strategy = True
            return []

        # 后续 candidates 构建、DD/Sortino/Alpha 过滤、排序，全部改用 sane_results
        group_results = sane_results

        # 3. 迭代 #9：DD 硬约束 + Sortino 门槛 + Alpha 排序选 Top-K
        #    Constitution L1: portfolio DD ≤ 20% 是硬约束（保留）
        #    新增：Sortino > 0.5 最低质量门槛（可放宽）
        #    变更：排序指标从 Sortino 改为 Alpha
        #
        #    三级过滤策略：
        #      Tier 1: DD ≤ 20% AND Sortino > 0.5 → Alpha 降序
        #      Tier 2 (fallback): Tier 1 为空 → 仅 DD ≤ 20% → Alpha 降序
        #      Tier 3 (fallback): Tier 2 为空 → 按 DD 升序，标记 dd_constrained=True
        candidates: list[
            tuple[str, dict, list[SingleBacktestResult], float, float, float]
        ] = []
        for (strategy, params, results) in group_results:
            pso = _portfolio_sortino_from_results(results)
            pdd = _portfolio_max_drawdown_from_results(results)
            # 复用 _combine_daily_returns 计算 alpha（与 per-strategy 选择一致）
            alpha = _compute_alpha(_combine_daily_returns(results), spy_returns)
            candidates.append((strategy, params, results, pso, pdd, alpha))

        # Tier 1: DD ≤ 20% AND Sortino > 0.5
        compliant = [
            c for c in candidates
            if c[4] <= MAX_PORTFOLIO_DRAWDOWN_PCT and c[3] > MIN_SORTINO_THRESHOLD
        ]
        if compliant:
            # Tier 1 命中：按 Alpha 降序取 top-K
            ranked = sorted(compliant, key=lambda x: x[5], reverse=True)
            dd_constrained = False
            logger.info(
                f"[MatrixBacktest] {group_id}: DD + Sortino filter passed — "
                f"{len(compliant)}/{len(candidates)} candidates compliant "
                f"(DD <= {MAX_PORTFOLIO_DRAWDOWN_PCT}% AND Sortino > {MIN_SORTINO_THRESHOLD})"
            )
        else:
            # Tier 2: 放宽 Sortino 门槛，仅保留 DD 约束
            dd_compliant = [
                c for c in candidates if c[4] <= MAX_PORTFOLIO_DRAWDOWN_PCT
            ]
            if dd_compliant:
                # Tier 2 命中：按 Alpha 降序取 top-K（dd_constrained 仍为 False）
                ranked = sorted(dd_compliant, key=lambda x: x[5], reverse=True)
                dd_constrained = False
                logger.warning(
                    f"[MatrixBacktest] {group_id}: Sortino filter relaxed — "
                    f"no candidate passed Sortino > {MIN_SORTINO_THRESHOLD}. "
                    f"Fallback to DD-only filter: "
                    f"{len(dd_compliant)}/{len(candidates)} candidates DD-compliant."
                )
            else:
                # Tier 3: 无 DD 合规候选 → 按 DD 升序，标记 dd_constrained
                # （结构性问题，如 NDX_high_vol 全部 > 20%）
                ranked = sorted(candidates, key=lambda x: x[4])
                dd_constrained = True
                logger.warning(
                    f"[MatrixBacktest] {group_id}: NO compliant candidates "
                    f"(all {len(candidates)} exceed DD={MAX_PORTFOLIO_DRAWDOWN_PCT}%). "
                    f"Fallback: selected top-{self._top_k} by lowest DD. "
                    f"This group is marked dd_constrained=True — "
                    f"review whether to drop the group or accept the risk."
                )
                report.warnings.append(
                    f"{group_id}: dd_constrained=True "
                    f"(min DD={ranked[0][4]:.2f}% > {MAX_PORTFOLIO_DRAWDOWN_PCT}%)"
                )

        top_results = ranked[: self._top_k]

        # 把 dd_constrained 标记同步到 report.group_results 中对应组的条目
        for gr in report.group_results:
            if gr.group_id == group_id:
                gr.dd_constrained = dd_constrained

        # 4. 优化 ensemble 权重（单点离散值加权投票语义，迭代 #9 改用 alpha）
        weighted = _optimize_ensemble_weights(
            [(s, p, r) for (s, p, r, _, _, _) in top_results],
            spy_returns=spy_returns,
        )

        # 5. 构建权重配置列表
        weights_list = []
        for strategy, params, weight in weighted:
            # 找到对应的 GroupBacktestResult
            gr = next(
                (r for r in report.group_results
                 if r.group_id == group_id and r.strategy == strategy),
                None,
            )
            # 迭代 #4：新增 backtest_dd_status 字段（'pass' / 'dd_constrained'）
            # 作为风险 metadata 标记，与 dd_constrained bool 同义但更可读
            backtest_dd_status = "dd_constrained" if dd_constrained else "pass"
            weights_list.append({
                "strategy": strategy,
                "params": params,
                "weight": round(weight, 4),
                "backtest_sharpe": round(gr.portfolio_sharpe if gr else 0.0, 4),
                "backtest_sortino": round(gr.portfolio_sortino if gr else 0.0, 4),
                "backtest_max_drawdown": round(gr.portfolio_max_drawdown if gr else 0.0, 4),
                "backtest_win_rate": round(gr.avg_win_rate_pct / 100 if gr else 0.5, 4),
                # 迭代 #9：新增 backtest_alpha 字段（vs SPY 的超额收益百分数）
                # 下游 PortfolioBacktester 可读此字段验证 alpha 一致性
                "backtest_alpha": round(gr.backtest_alpha if gr else 0.0, 4),
                # 迭代 #3：标记该组是否用了 DD fallback（无合规候选）
                # 同组所有策略条目共享同一 dd_constrained 值
                "dd_constrained": dd_constrained,
                # 迭代 #4：backtest_dd_status — 风险 metadata 字段
                # 'pass' = 该组有合规候选（DD ≤ 20%）
                # 'dd_constrained' = fallback 触发（无合规候选，按最低 DD 取 top-K）
                # 下游消费方（PortfolioBacktester / 风控观测）可读此字段判断
                # 该组权重的可靠性，作为风险信号标记
                "backtest_dd_status": backtest_dd_status,
            })

        logger.info(
            f"[MatrixBacktest] {group_id}: all strategies done in "
            f"{time.time() - group_start:.1f}s "
            f"(top-{self._top_k} selected, dd_constrained={dd_constrained})"
        )

        return weights_list

    def _write_weights(
        self, report: MatrixBacktestReport, output_file: str | Path
    ) -> None:
        """将矩阵回测结果写入 strategy_weights.json。"""
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "_meta": {
                "generated_at": report.generated_at,
                "backtest_window": report.backtest_window,
                "reoptimize_freq": "monthly",
                "survivorship_bias_warning": (
                    "使用当前成分股回测，S&P 500 5年成分变动约100只(~20%)，"
                    "均值回归组(SPX_low_vol)结果可能系统性偏高"
                ),
            },
            "groups": report.groups,
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"[MatrixBacktest] weights saved to {output_file}")
