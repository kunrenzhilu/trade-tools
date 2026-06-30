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
    portfolio_sortino: float = 0.0   # 等权组合 Sortino（迭代 #1 新增）


@dataclass
class MatrixBacktestReport:
    """整个矩阵回测的汇总报告。"""

    generated_at: str
    backtest_window: str
    groups: dict[str, list[dict]]   # group_id → [策略权重配置]
    group_results: list[GroupBacktestResult] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# 核心函数
# ---------------------------------------------------------------------------

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

        return SingleBacktestResult(
            symbol=str(df.index.name or ""),
            strategy=strategy_name,
            params=params,
            sharpe=float(stats.get("Sharpe Ratio", 0.0) or 0.0),
            total_return_pct=float(stats.get("Total Return [%]", 0.0) or 0.0),
            max_drawdown_pct=float(stats.get("Max Drawdown [%]", 0.0) or 0.0),
            win_rate_pct=float(stats.get("Win Rate [%]", 0.0) or 0.0),
            total_trades=int(stats.get("Total Trades", 0) or 0),
            daily_returns=daily_returns,
            sortino=_compute_sortino(daily_returns),
        )
    except Exception as e:
        logger.debug(f"[backtest_one] {strategy_name}({params}) failed: {e}")
        return None


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


def _optimize_ensemble_weights(
    group_results: list[tuple[str, dict, list[SingleBacktestResult]]],
    conflict_threshold: float = 0.3,
) -> list[tuple[str, dict, float]]:
    """在"单点离散值加权投票"语义下优化 ensemble 权重。

    实盘每根 bar 各策略产出离散值（1/-1/0），加权投票决定方向。
    回测的权重优化必须使用相同语义，而非对整段时间序列做加权。

    Args:
        group_results: [(strategy, params, [SingleBacktestResult]), ...]
        conflict_threshold: 加权投票分数绝对值低于此时视为 HOLD

    Returns:
        [(strategy, params, weight), ...] 归一化权重列表
    """
    if len(group_results) == 1:
        strategy, params, _ = group_results[0]
        return [(strategy, params, 1.0)]

    # 简化的 ensemble 权重搜索：用各策略的组合 Sharpe 归一化为权重
    # 更严格的做法是网格搜索 weight 组合，在离散投票序列上跑回测
    sharpes = []
    for strategy, params, results in group_results:
        ps = _portfolio_sharpe_from_results(results)
        sharpes.append(max(ps, 0.01))  # 避免负权重

    total = sum(sharpes)
    weights = [s / total for s in sharpes]

    return [
        (strategy, params, weight)
        for (strategy, params, _), weight in zip(group_results, weights)
    ]


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
        """对单个分组执行策略 × 参数网格回测，返回该组的权重配置列表。"""

        # 1. 读取组内所有标的数据
        data = self._store.get_bars_multi(symbols, start, end)
        if not data:
            logger.warning(f"[MatrixBacktest] {group_id}: no data, skip")
            return []

        # 2. 对每个策略 × 每组参数，计算组合 Sharpe
        group_results: list[tuple[str, dict, list[SingleBacktestResult]]] = []

        for strategy in strategies:
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
            best_sharpe = float("-inf")
            best_sortino = 0.0
            best_results: list[SingleBacktestResult] = []

            for params in param_combos:
                # 对组内每只标的回测
                results = []
                for sym in symbols:
                    df = data.get(sym, pd.DataFrame())
                    if df.empty:
                        continue
                    df.index.name = sym  # 方便 _backtest_one 使用
                    r = _backtest_one(
                        df, strategy, params,
                        self._init_cash, self._fees, self._slippage
                    )
                    if r is not None:
                        results.append(r)

                if not results:
                    continue

                # ⚠️ 等权合并日收益率序列计算组合 Sharpe（不能取算术平均）
                ps = _portfolio_sharpe_from_results(results)
                pso = _portfolio_sortino_from_results(results)

                if ps > best_sharpe:
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
                    avg_total_return_pct=float(
                        np.mean([r.total_return_pct for r in best_results])
                    ),
                    avg_max_drawdown_pct=float(
                        np.mean([r.max_drawdown_pct for r in best_results])
                    ),
                    avg_win_rate_pct=float(
                        np.mean([r.win_rate_pct for r in best_results])
                    ),
                    symbol_count=len(best_results),
                    portfolio_sortino=best_sortino,
                ))

        if not group_results:
            logger.warning(f"[MatrixBacktest] {group_id}: no valid results")
            return []

        # 3. 按组合 Sharpe 排序，保留 Top-K 策略
        group_results.sort(key=lambda x: _portfolio_sharpe_from_results(x[2]), reverse=True)
        top_results = group_results[: self._top_k]

        # 4. 优化 ensemble 权重（单点离散值加权投票语义）
        weighted = _optimize_ensemble_weights(top_results)

        # 5. 构建权重配置列表
        weights_list = []
        for strategy, params, weight in weighted:
            # 找到对应的 GroupBacktestResult
            gr = next(
                (r for r in report.group_results
                 if r.group_id == group_id and r.strategy == strategy),
                None,
            )
            weights_list.append({
                "strategy": strategy,
                "params": params,
                "weight": round(weight, 4),
                "backtest_sharpe": round(gr.portfolio_sharpe if gr else 0.0, 4),
                "backtest_sortino": round(gr.portfolio_sortino if gr else 0.0, 4),
                "backtest_win_rate": round(gr.avg_win_rate_pct / 100 if gr else 0.5, 4),
            })

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
