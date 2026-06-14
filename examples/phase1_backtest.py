"""Phase 1 快速回测示例。

运行方式：
    cd mytrader
    python examples/phase1_backtest.py

功能：
    1. 拉取 AAPL 3 年日线数据（带本地缓存）
    2. 分别跑 4 个策略的回测
    3. 输出关键指标对比
    4. 双均线策略参数优化（网格搜索）
    5. 生成 HTML 报告
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

# 确保 mytrader 包可导入
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

from mytrader.backtest.runner import BacktestConfig, BacktestRunner
from mytrader.backtest.report import BacktestReport

logger.remove()
logger.add(sys.stderr, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")


def main():
    runner = BacktestRunner()
    report_gen = BacktestReport(output_dir="reports")

    # --------------------------------------------------------
    # 1. 各策略单独回测 (AAPL 2022-2025)
    # --------------------------------------------------------
    symbols = ["AAPL"]
    strategies = [
        ("dual_ma",        {"fast": 10, "slow": 30}),
        ("macd_cross",     {"fast": 12, "slow": 26, "signal_period": 9}),
        ("rsi_mean_revert",{"period": 14, "oversold": 30, "overbought": 70}),
        ("bollinger_band", {"period": 20, "std_dev": 2.0}),
    ]

    print("\n" + "=" * 60)
    print("Phase 1 — Strategy Backtest Comparison")
    print("=" * 60)

    results = {}
    for symbol in symbols:
        for strategy_name, params in strategies:
            config = BacktestConfig(
                symbol=symbol,
                start=date(2022, 1, 1),
                end=date(2025, 1, 1),
                timeframe="1d",
                strategy_name=strategy_name,
                strategy_params=params,
                init_cash=100_000,
                fees=0.001,
                slippage=0.001,
            )
            try:
                result = runner.run(config)
                results[(symbol, strategy_name)] = result
                # 生成 HTML 报告
                report_gen.generate(result)
            except Exception as exc:
                logger.error(f"Backtest failed for {symbol}/{strategy_name}: {exc}")

    # --------------------------------------------------------
    # 2. 双均线参数优化（网格搜索）
    # --------------------------------------------------------
    print("\n" + "=" * 60)
    print("Dual MA — Parameter Grid Search (AAPL 2022-2025)")
    print("=" * 60)

    try:
        opt_result = runner.run_optimize(
            symbol="AAPL",
            start=date(2022, 1, 1),
            end=date(2025, 1, 1),
            strategy_name="dual_ma",
            param_grid={
                "fast": [5, 10, 15, 20],
                "slow": [20, 30, 40, 50, 60],
            },
        )
        print("\nTop 5 parameter combinations by Sharpe Ratio:")
        print(opt_result.head(10).to_string(index=False))

        opt_result.to_csv("reports/dual_ma_optimization.csv", index=False)
        print("\nFull results saved to: reports/dual_ma_optimization.csv")
    except Exception as exc:
        logger.error(f"Optimization failed: {exc}")

    print("\n✓ Phase 1 backtest complete. Check reports/ for HTML charts.")


if __name__ == "__main__":
    main()
