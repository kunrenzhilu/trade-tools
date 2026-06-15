"""组合绩效指标计算：Sharpe / MaxDD / Calmar / 胜率。"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


def sharpe_ratio(
    equity_series: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
) -> float:
    """年化 Sharpe 比率。

    Args:
        equity_series:    资产净值序列（每日）
        risk_free_rate:   无风险年化收益率（默认 0）
        periods_per_year: 每年交易日（默认 252）

    Returns:
        Sharpe 比率；序列太短返回 0.0
    """
    if len(equity_series) < 2:
        return 0.0
    returns = equity_series.pct_change().dropna()
    if returns.std() == 0:
        return 0.0
    excess = returns - risk_free_rate / periods_per_year
    return float(excess.mean() / excess.std() * math.sqrt(periods_per_year))


def max_drawdown(equity_series: pd.Series) -> float:
    """最大回撤（负数，如 -0.20 = -20%）。"""
    if len(equity_series) < 2:
        return 0.0
    rolling_max = equity_series.cummax()
    dd = (equity_series - rolling_max) / rolling_max
    return float(dd.min())


def calmar_ratio(
    equity_series: pd.Series,
    periods_per_year: int = 252,
) -> float:
    """Calmar 比率 = 年化收益 / |最大回撤|。"""
    if len(equity_series) < 2:
        return 0.0
    total_return = equity_series.iloc[-1] / equity_series.iloc[0] - 1
    n_years = len(equity_series) / periods_per_year
    annualized_return = (1 + total_return) ** (1 / n_years) - 1 if n_years > 0 else 0.0
    mdd = abs(max_drawdown(equity_series))
    if mdd == 0:
        return 0.0
    return float(annualized_return / mdd)


def win_rate(realized_pnls: list[float]) -> float:
    """胜率 = 盈利笔数 / 总笔数。"""
    if not realized_pnls:
        return 0.0
    wins = sum(1 for p in realized_pnls if p > 0)
    return wins / len(realized_pnls)


def profit_factor(realized_pnls: list[float]) -> float:
    """盈亏比 = 总盈利 / |总亏损|。"""
    gross_profit = sum(p for p in realized_pnls if p > 0)
    gross_loss = abs(sum(p for p in realized_pnls if p < 0))
    if gross_loss == 0:
        return float("inf") if gross_profit > 0 else 0.0
    return gross_profit / gross_loss


def portfolio_summary(
    equity_series: pd.Series,
    realized_pnls: list[float],
    initial_capital: float,
) -> dict:
    """返回组合绩效摘要字典。"""
    total_pnl = sum(realized_pnls)
    total_return = (equity_series.iloc[-1] - initial_capital) / initial_capital if len(equity_series) > 0 else 0.0
    return {
        "total_return": round(total_return, 4),
        "sharpe_ratio": round(sharpe_ratio(equity_series), 4),
        "max_drawdown": round(max_drawdown(equity_series), 4),
        "calmar_ratio": round(calmar_ratio(equity_series), 4),
        "win_rate": round(win_rate(realized_pnls), 4),
        "profit_factor": round(profit_factor(realized_pnls), 4),
        "total_trades": len(realized_pnls),
        "total_realized_pnl": round(total_pnl, 2),
    }
