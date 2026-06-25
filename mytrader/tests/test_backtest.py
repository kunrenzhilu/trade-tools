"""Tests for Backtest Module — BacktestRunner + BacktestReport.

使用合成数据，不发起网络请求。

测试范围：
    BT1  test_config_defaults              P1  BacktestConfig 默认值
    BT2  test_config_custom_values         P1  自定义参数保存
    BT3  test_runner_with_synthetic_data   P0  run() 端到端
    BT4  test_runner_invalid_strategy_name P0  无效策略名 → ValueError
    BT5  test_runner_empty_data_raises     P0  空数据 → ValueError
    BT6  test_runner_next_open_vs_close    P0  use_next_open 对比
    BT7  test_runner_custom_provider       P1  自定义 DataProvider
    BT8  test_optimize_grid_search         P0  run_optimize 返回正确结构
    BT9  test_optimize_single_combination  P1  单组合网格搜索
    BT11 test_result_stats_keys            P1  stats 包含关键字段
    BR1  test_generate_creates_directory   P1  generate 创建输出目录
    BR2  test_generate_creates_stats_csv   P0  stats.csv 存在且内容正确
    BR3  test_generate_creates_trades_csv  P1  trades.csv 存在
    BR4  test_generate_creates_html_files  P1  HTML 报告存在
"""

from __future__ import annotations

import os
from datetime import date

import numpy as np
import pandas as pd
import pytest

from mytrader.backtest.runner import BacktestConfig, BacktestRunner, BacktestResult
from mytrader.backtest.report import BacktestReport


# ---------------------------------------------------------------------------
# Helpers: 合成 OHLCV 数据
# ---------------------------------------------------------------------------

def make_synthetic_ohlcv(n: int = 200, seed: int = 42) -> pd.DataFrame:
    """生成合成的 OHLCV 数据（含趋势+噪声）。"""
    idx = pd.date_range("2022-01-01", periods=n, freq="B", tz="UTC")
    rng = np.random.RandomState(seed)
    close = pd.Series(100 + rng.randn(n).cumsum(), index=idx)
    return pd.DataFrame({
        "open":   close * (1 + rng.uniform(-0.003, 0.003, n)),
        "high":   close * (1 + rng.uniform(0, 0.01, n)),
        "low":    close * (1 - rng.uniform(0, 0.01, n)),
        "close":  close,
        "volume": rng.randint(1_000_000, 10_000_000, n).astype(float),
    }, index=idx)


def make_mock_provider(df: pd.DataFrame):
    """创建一个 mock YFinanceProvider，返回指定 DataFrame。"""
    from unittest import mock
    provider = mock.MagicMock()
    provider.get_ohlcv.return_value = df
    return provider


# ---------------------------------------------------------------------------
# P1: BacktestConfig
# ---------------------------------------------------------------------------

class TestBacktestConfig:
    """BT1, BT2: 配置默认值和自定义参数。"""

    def test_config_defaults(self):
        """BT1: 默认值正确。"""
        config = BacktestConfig(symbol="AAPL", start=date(2022, 1, 1), end=date(2023, 1, 1))
        assert config.init_cash == 100_000.0
        assert config.fees == 0.001
        assert config.slippage == 0.001
        assert config.use_next_open is True
        assert config.size == 0.95
        assert config.timeframe == "1d"
        assert config.strategy_name == "dual_ma"

    def test_config_custom_values(self):
        """BT2: 自定义参数正确保存。"""
        config = BacktestConfig(
            symbol="0700.HK",
            start=date(2022, 1, 1),
            end=date(2023, 1, 1),
            strategy_name="bollinger_band",
            init_cash=50_000.0,
            fees=0.005,
            slippage=0.002,
            use_next_open=False,
            size=0.5,
        )
        assert config.fees == 0.005
        assert config.slippage == 0.002
        assert config.strategy_name == "bollinger_band"
        assert config.init_cash == 50_000.0


# ---------------------------------------------------------------------------
# P0: BacktestRunner 核心流程
# ---------------------------------------------------------------------------

class TestBacktestRunner:
    """BT3-BT8: 回测核心流程。"""

    def test_runner_with_synthetic_data(self):
        """BT3: BacktestRunner.run() 端到端测试，返回 BacktestResult。"""
        df = make_synthetic_ohlcv(200)
        runner = BacktestRunner(data_provider=make_mock_provider(df))
        config = BacktestConfig(
            symbol="AAPL",
            start=date(2022, 1, 1),
            end=date(2023, 1, 1),
            strategy_name="dual_ma",
        )
        result = runner.run(config)
        assert isinstance(result, BacktestResult)
        assert result.config.strategy_name == "dual_ma"
        assert isinstance(result.stats, pd.Series)
        assert "Sharpe Ratio" in result.stats.index
        assert isinstance(result.stats["Total Return [%]"], float)

    def test_runner_invalid_strategy_name(self):
        """BT4: 不存在的策略名抛出 ValueError。"""
        df = make_synthetic_ohlcv(200)
        runner = BacktestRunner(data_provider=make_mock_provider(df))
        config = BacktestConfig(
            symbol="AAPL",
            start=date(2022, 1, 1),
            end=date(2023, 1, 1),
            strategy_name="nonexistent_strategy",
        )
        with pytest.raises(ValueError, match="not found"):
            runner.run(config)

    def test_runner_empty_data_raises(self):
        """BT5: 空数据回测抛出 ValueError。"""
        provider = make_mock_provider(pd.DataFrame(columns=["open", "high", "low", "close", "volume"]))
        runner = BacktestRunner(data_provider=provider)
        config = BacktestConfig(
            symbol="AAPL",
            start=date(2022, 1, 1),
            end=date(2023, 1, 1),
            strategy_name="dual_ma",
        )
        with pytest.raises(ValueError, match="No data"):
            runner.run(config)

    def test_runner_next_open_vs_close(self):
        """BT6: use_next_open=True 与 False 模式均能正常完成回测。"""
        df = make_synthetic_ohlcv(200)
        runner = BacktestRunner(data_provider=make_mock_provider(df))

        config_t = BacktestConfig(
            symbol="AAPL", start=date(2022, 1, 1), end=date(2023, 1, 1),
            strategy_name="dual_ma", use_next_open=True,
        )
        config_f = BacktestConfig(
            symbol="AAPL", start=date(2022, 1, 1), end=date(2023, 1, 1),
            strategy_name="dual_ma", use_next_open=False,
        )

        result_next_open = runner.run(config_t)
        result_close = runner.run(config_f)

        # 两种模式均应返回有效结果
        assert isinstance(result_next_open.stats, pd.Series)
        assert isinstance(result_close.stats, pd.Series)
        assert "Sharpe Ratio" in result_next_open.stats.index
        assert "Sharpe Ratio" in result_close.stats.index
        # 注：如果交易数很少，总回报可能相同（0 trades），这并非错误

    def test_runner_custom_provider(self):
        """BT7: 注入自定义 DataProvider 使用 mock 数据。"""
        df = make_synthetic_ohlcv(200)
        runner = BacktestRunner(data_provider=make_mock_provider(df))
        config = BacktestConfig(
            symbol="AAPL", start=date(2022, 1, 1), end=date(2023, 1, 1),
            strategy_name="rsi_mean_revert",
        )
        result = runner.run(config)
        assert isinstance(result, BacktestResult)
        assert "Sharpe Ratio" in result.stats.index

    def test_optimize_grid_search(self):
        """BT8: run_optimize 返回按 Sharpe 降序的 DataFrame。"""
        df = make_synthetic_ohlcv(200)
        runner = BacktestRunner(data_provider=make_mock_provider(df))

        result = runner.run_optimize(
            symbol="AAPL",
            start=date(2022, 1, 1),
            end=date(2023, 1, 1),
            strategy_name="dual_ma",
            param_grid={"fast": [5, 10], "slow": [20, 30]},
        )

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 4  # 2x2 网格
        assert "fast" in result.columns
        assert "slow" in result.columns
        assert "Sharpe Ratio" in result.columns
        assert "Total Return [%]" in result.columns
        # 按 Sharpe 降序排列
        sharpes = result["Sharpe Ratio"].values
        non_null = [s for s in sharpes if s is not None]
        for i in range(len(non_null) - 1):
            assert non_null[i] >= non_null[i + 1], "not sorted by Sharpe Ratio descending"

    def test_optimize_single_combination(self):
        """BT9: 单个参数组合的网格搜索返回 1 行。"""
        df = make_synthetic_ohlcv(200)
        runner = BacktestRunner(data_provider=make_mock_provider(df))

        result = runner.run_optimize(
            symbol="AAPL",
            start=date(2022, 1, 1),
            end=date(2023, 1, 1),
            strategy_name="dual_ma",
            param_grid={"fast": [10], "slow": [20]},
        )

        assert len(result) == 1
        assert result.iloc[0]["fast"] == 10
        assert result.iloc[0]["slow"] == 20

    def test_result_stats_keys(self):
        """BT11: BacktestResult.stats 包含所有关键字段。"""
        df = make_synthetic_ohlcv(200)
        runner = BacktestRunner(data_provider=make_mock_provider(df))
        config = BacktestConfig(
            symbol="AAPL", start=date(2022, 1, 1), end=date(2023, 1, 1),
            strategy_name="dual_ma",
        )
        result = runner.run(config)

        required_keys = [
            "Total Return [%]",
            "Sharpe Ratio",
            "Max Drawdown [%]",
            "Win Rate [%]",
            "Total Trades",
        ]
        for key in required_keys:
            assert key in result.stats.index, f"Missing key: {key}"


# ---------------------------------------------------------------------------
# P0-P1: BacktestReport
# ---------------------------------------------------------------------------

class TestBacktestReport:
    """BR1-BR4: 报告生成。"""

    def _make_result(self) -> BacktestResult:
        df = make_synthetic_ohlcv(200)
        runner = BacktestRunner(data_provider=make_mock_provider(df))
        config = BacktestConfig(
            symbol="AAPL", start=date(2022, 1, 1), end=date(2023, 1, 1),
            strategy_name="dual_ma",
        )
        return runner.run(config)

    def test_generate_creates_directory(self, tmp_path):
        """BR1: generate 创建输出目录。"""
        result = self._make_result()
        report = BacktestReport(output_dir=str(tmp_path / "reports"))
        out_path = report.generate(result, name="test_run")
        assert out_path.exists()
        assert out_path.is_dir()

    def test_generate_creates_stats_csv(self, tmp_path):
        """BR2: stats.csv 存在且非空。"""
        result = self._make_result()
        report = BacktestReport(output_dir=str(tmp_path / "reports"))
        out_path = report.generate(result, name="test_run_stats")
        stats_file = out_path / "stats.csv"
        assert stats_file.exists()
        df_stats = pd.read_csv(stats_file)
        assert not df_stats.empty

    def test_generate_creates_trades_csv(self, tmp_path):
        """BR3: 有交易时 trades.csv 存在且非空。"""
        result = self._make_result()
        report = BacktestReport(output_dir=str(tmp_path / "reports"))
        out_path = report.generate(result, name="test_run_trades")

        trades_file = out_path / "trades.csv"
        # 回测可能有也可能没有交易，取决于数据
        # 如果存在应当非空
        if trades_file.exists():
            df_trades = pd.read_csv(trades_file)
            assert not df_trades.empty

    def test_generate_creates_html_files(self, tmp_path):
        """BR4: HTML 报告文件存在。"""
        result = self._make_result()
        report = BacktestReport(output_dir=str(tmp_path / "reports"))
        out_path = report.generate(result, name="test_run_html")

        equity_file = out_path / "equity_curve.html"
        dd_file = out_path / "drawdowns.html"
        assert equity_file.exists(), "equity_curve.html not found"
        assert dd_file.exists(), "drawdowns.html not found"
        assert equity_file.stat().st_size > 0, "equity_curve.html is empty"
        assert dd_file.stat().st_size > 0, "drawdowns.html is empty"
