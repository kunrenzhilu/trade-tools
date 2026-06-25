"""回测报告生成（HTML + CSV）。"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

import pandas as pd
from loguru import logger

from mytrader.backtest.runner import BacktestResult


class BacktestReport:
    """将 BacktestResult 导出为 HTML 和 CSV 报告。

    输出目录结构：
        {output_dir}/
            stats.csv
            trades.csv
            equity_curve.html
            drawdowns.html
    """

    def __init__(self, output_dir: str = "reports") -> None:
        self._output_dir = Path(output_dir)

    def generate(self, result: BacktestResult, name: str | None = None) -> Path:
        """生成完整报告。

        Args:
            result: BacktestResult 对象
            name:   子目录名称（默认使用时间戳）

        Returns:
            报告目录路径
        """
        if name is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = f"{result.config.symbol}_{result.config.strategy_name}_{ts}"

        report_dir = self._output_dir / name
        report_dir.mkdir(parents=True, exist_ok=True)

        pf = result.portfolio

        # 1. 统计摘要 CSV
        stats_path = report_dir / "stats.csv"
        result.stats.to_csv(stats_path, header=["value"])
        logger.info(f"[Report] Stats saved: {stats_path}")

        # 2. 逐笔交易记录 CSV
        try:
            trades_path = report_dir / "trades.csv"
            pf.trades.records_readable.to_csv(trades_path, index=False)
            logger.info(f"[Report] Trades saved: {trades_path}")
        except Exception as exc:
            logger.warning(f"[Report] Could not save trades: {exc}")

        # 3. 权益曲线 HTML
        try:
            equity_path = report_dir / "equity_curve.html"
            fig = pf.plot()
            fig.write_html(str(equity_path))
            logger.info(f"[Report] Equity curve saved: {equity_path}")
        except Exception as exc:
            logger.warning(f"[Report] Could not save equity curve: {exc}")

        # 4. 回撤分析 HTML
        try:
            dd_path = report_dir / "drawdowns.html"
            pf.drawdowns.plot().write_html(str(dd_path))
            logger.info(f"[Report] Drawdowns saved: {dd_path}")
        except Exception as exc:
            logger.warning(f"[Report] Could not save drawdowns: {exc}")

        logger.info(f"[Report] Report generated at: {report_dir}")
        return report_dir
