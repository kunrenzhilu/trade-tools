"""回测运行器（Backtest Runner）。

将 Data Layer 和 Strategy Layer 对接到 VectorBT，
共用同一套策略函数保证回测/实盘一致性。

关键设计：
    - 信号在收盘后产生，下一根 bar 的开盘价执行（next_open=True）
    - 费用和滑点均配置在 BacktestConfig 中，统一管理
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

import pandas as pd
import vectorbt as vbt
from loguru import logger

from mytrader.data.providers.yfinance_provider import YFinanceProvider
from mytrader.strategy.registry import STRATEGY_REGISTRY


@dataclass
class BacktestConfig:
    """回测参数配置。"""

    symbol: str
    start: date
    end: date
    timeframe: str = "1d"

    # 策略
    strategy_name: str = "dual_ma"
    strategy_params: dict = field(default_factory=dict)

    # 资金与成本
    init_cash: float = 100_000.0
    fees: float = 0.001        # 0.1% 手续费
    slippage: float = 0.001    # 0.1% 滑点

    # 执行价格：True = 下一 bar 开盘价（推荐），False = 当前 bar 收盘价（有前视偏差风险）
    use_next_open: bool = True

    # 仓位：每次信号使用账户的百分比（0~1）
    size: float = 0.95         # 每次最多用 95% 的资金，留少量现金


@dataclass
class BacktestResult:
    """回测结果容器。"""

    config: BacktestConfig
    portfolio: vbt.Portfolio
    stats: pd.Series

    def print_stats(self) -> None:
        """打印关键绩效指标。"""
        key_stats = [
            "Start", "End", "Period",
            "Total Return [%]",
            "Benchmark Return [%]",
            "Sharpe Ratio",
            "Max Drawdown [%]",
            "Calmar Ratio",
            "Win Rate [%]",
            "Profit Factor",
            "Total Trades",
            "Avg Winning Trade [%]",
            "Avg Losing Trade [%]",
        ]
        available = [s for s in key_stats if s in self.stats.index]
        print(f"\n{'='*50}")
        print(f"Backtest: {self.config.symbol} | {self.config.strategy_name}")
        print(f"Period:   {self.config.start} ~ {self.config.end}")
        print(f"{'='*50}")
        print(self.stats[available].to_string())
        print(f"{'='*50}\n")


class BacktestRunner:
    """回测运行器，连接数据、策略和 VectorBT。

    Example::

        config = BacktestConfig(
            symbol="AAPL",
            start=date(2022, 1, 1),
            end=date(2024, 1, 1),
            strategy_name="dual_ma",
            strategy_params={"fast": 10, "slow": 30},
        )
        runner = BacktestRunner()
        result = runner.run(config)
        result.print_stats()
    """

    def __init__(self, data_provider: YFinanceProvider | None = None) -> None:
        self._provider = data_provider or YFinanceProvider()

    def run(self, config: BacktestConfig) -> BacktestResult:
        """执行单次回测。

        Args:
            config: 回测配置

        Returns:
            BacktestResult，含 VectorBT Portfolio 对象
        """
        # 1. 获取数据
        logger.info(
            f"[Backtest] {config.symbol} | {config.strategy_name} | "
            f"{config.start}~{config.end} | {config.timeframe}"
        )
        df = self._provider.get_ohlcv(
            config.symbol, config.start, config.end, config.timeframe
        )

        if df.empty:
            raise ValueError(f"No data for {config.symbol} {config.start}~{config.end}")

        close = df["close"]
        open_ = df["open"] if "open" in df.columns else None

        # 2. 生成信号（调用策略层纯函数）
        strategy_fn = STRATEGY_REGISTRY.get(config.strategy_name)
        if strategy_fn is None:
            available = list(STRATEGY_REGISTRY.keys())
            raise ValueError(
                f"Strategy '{config.strategy_name}' not found. "
                f"Available: {available}"
            )

        signal = strategy_fn(close, **config.strategy_params)
        # signal: 1=BUY, -1=SELL, 0=HOLD（已内含 shift(1)）

        entries = signal == 1
        exits   = signal == -1

        logger.info(
            f"[Backtest] Entries: {entries.sum()}, Exits: {exits.sum()}, "
            f"Total bars: {len(close)}"
        )

        # 3. VectorBT Portfolio
        # vectorbt 1.x: size_type 使用字符串枚举 "Percent"（按账户价值百分比）
        pf_kwargs = dict(
            entries=entries,
            exits=exits,
            init_cash=config.init_cash,
            fees=config.fees,
            slippage=config.slippage,
            size=config.size,
            size_type="Percent",
            freq="D" if config.timeframe == "1d" else config.timeframe,
        )

        if config.use_next_open and open_ is not None:
            # 在下一根 bar 的开盘价执行，更接近真实情况
            pf = vbt.Portfolio.from_signals(
                close=close,
                open=open_,
                **pf_kwargs,
            )
        else:
            pf = vbt.Portfolio.from_signals(close, **pf_kwargs)

        stats = pf.stats()

        result = BacktestResult(config=config, portfolio=pf, stats=stats)
        result.print_stats()
        return result

    def run_optimize(
        self,
        symbol: str,
        start: date,
        end: date,
        strategy_name: str,
        param_grid: dict[str, list],
        timeframe: str = "1d",
        init_cash: float = 100_000.0,
        fees: float = 0.001,
        slippage: float = 0.001,
    ) -> pd.DataFrame:
        """参数网格搜索优化。

        Args:
            param_grid: 参数搜索空间，如 {"fast": [5,10,15], "slow": [20,30,40]}

        Returns:
            DataFrame，每行一个参数组合，含 Sharpe/MaxDD/Return 等指标
        """
        import itertools

        df = self._provider.get_ohlcv(symbol, start, end, timeframe)
        if df.empty:
            raise ValueError(f"No data for {symbol}")

        close = df["close"]
        strategy_fn = STRATEGY_REGISTRY[strategy_name]

        # 生成所有参数组合
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        combinations = list(itertools.product(*param_values))

        logger.info(
            f"[Optimize] {symbol} | {strategy_name} | "
            f"{len(combinations)} parameter combinations"
        )

        rows = []
        for combo in combinations:
            params = dict(zip(param_names, combo))
            try:
                signal = strategy_fn(close, **params)
                pf = vbt.Portfolio.from_signals(
                    close,
                    entries=signal == 1,
                    exits=signal == -1,
                    init_cash=init_cash,
                    fees=fees,
                    slippage=slippage,
                    size=0.95,
                    size_type="Percent",
                    freq="D",
                )
                stats = pf.stats()
                row = {**params}
                for metric in ["Total Return [%]", "Sharpe Ratio", "Max Drawdown [%]",
                               "Calmar Ratio", "Win Rate [%]", "Total Trades"]:
                    row[metric] = stats.get(metric, None)
                rows.append(row)
            except Exception as exc:
                logger.warning(f"[Optimize] params={params} failed: {exc}")

        result_df = pd.DataFrame(rows)
        result_df = result_df.sort_values("Sharpe Ratio", ascending=False)
        return result_df
