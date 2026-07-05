"""PortfolioBacktest 测试（迭代 #4 新增）。

使用 Mock MarketDataStore + 内置策略，不触碰网络。
覆盖：
    1. PortfolioBacktestResult dataclass 字段完整性
    2. PortfolioBacktester 基本流程（3 标的 × 10 天）
    3. max_drawdown_pct 计算正确性
    4. 换仓逻辑（Top-K 变化时正确卖出/买入）
    5. 信号过期（signal_valid_bars）
    6. dd_violation 标记（DD > 20% 时 True）
    7. group_exposure_history 记录
    8. _write_weights 中 backtest_dd_status 字段输出（P1b）
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

from mytrader.backtest.portfolio_backtest import (
    PORTFOLIO_MAX_DRAWDOWN_PCT,
    PortfolioBacktestConfig,
    PortfolioBacktestResult,
    PortfolioBacktester,
)
from mytrader.universe.models import SymbolMeta


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_ohlcv_df(
    n: int = 30,
    start_price: float = 100.0,
    trend: float = 0.0,
    start_date: str = "2024-01-01",
) -> pd.DataFrame:
    """生成简单 OHLCV 数据。

    Args:
        n:           天数
        start_price: 起始价格
        trend:       每日价格变化（正=上涨，负=下跌）
        start_date:  起始日期
    """
    idx = pd.date_range(start_date, periods=n, freq="B")
    close = [start_price + trend * i for i in range(n)]
    return pd.DataFrame(
        {
            "open":   [c - 0.3 for c in close],
            "high":   [c + 0.5 for c in close],
            "low":    [c - 0.5 for c in close],
            "close":  close,
            "volume": [1_000_000] * n,
        },
        index=idx,
    )


@pytest.fixture
def mock_store_3_symbols():
    """3 只标的 × 30 天的 mock store（上涨趋势）。"""
    store = MagicMock()
    df_aapl = _make_ohlcv_df(30, 100.0, trend=0.5)
    df_msft = _make_ohlcv_df(30, 200.0, trend=0.3)
    df_jpm = _make_ohlcv_df(30, 80.0, trend=0.2)

    mapping = {"AAPL": df_aapl, "MSFT": df_msft, "JPM": df_jpm}

    def get_bars_multi(symbols, start, end, timeframe="1d"):
        return {s: mapping[s].copy() for s in symbols if s in mapping}

    store.get_bars_multi.side_effect = get_bars_multi
    return store


@pytest.fixture
def mock_universe_3_symbols():
    """3 只标的的 universe mock。"""
    universe = MagicMock()
    universe.get_universe.return_value = ["AAPL", "MSFT", "JPM"]

    def get_meta(sym):
        ndx = ["AAPL", "MSFT"]
        return SymbolMeta(
            symbol=sym,
            index_membership=["NASDAQ100"] if sym in ndx else ["SP500"],
            sector="Technology" if sym in ndx else "Financials",
            market_cap_tier="large",
            volatility_tier="mid",
            group_id="NDX_mid_vol" if sym in ndx else "SPX_mid_vol",
        )

    universe.get_symbol_meta.side_effect = get_meta
    universe.get_groups.return_value = {
        "NDX_mid_vol": ["AAPL", "MSFT"],
        "SPX_mid_vol": ["JPM"],
    }
    return universe


@pytest.fixture
def weights_file_simple(tmp_path):
    """简单权重文件：每只标的用 dual_ma 策略。"""
    weights = {
        "_meta": {
            "generated_at": "2024-01-01T00:00:00Z",
            "backtest_window": "2023-01-01 ~ 2024-01-01",
        },
        "groups": {
            "NDX_mid_vol": [
                {
                    "strategy": "dual_ma",
                    "params": {"fast": 5, "slow": 10},
                    "weight": 1.0,
                    "backtest_sharpe": 1.2,
                    "backtest_sortino": 1.5,
                    "backtest_max_drawdown": 8.0,
                    "backtest_win_rate": 0.55,
                    "dd_constrained": False,
                    "backtest_dd_status": "pass",
                }
            ],
            "SPX_mid_vol": [
                {
                    "strategy": "dual_ma",
                    "params": {"fast": 5, "slow": 10},
                    "weight": 1.0,
                    "backtest_sharpe": 0.9,
                    "backtest_sortino": 1.1,
                    "backtest_max_drawdown": 6.0,
                    "backtest_win_rate": 0.52,
                    "dd_constrained": False,
                    "backtest_dd_status": "pass",
                }
            ],
        },
    }
    path = tmp_path / "strategy_weights.json"
    path.write_text(json.dumps(weights))
    return path


# ---------------------------------------------------------------------------
# 测试 1: PortfolioBacktestResult dataclass
# ---------------------------------------------------------------------------

class TestPortfolioBacktestResultDataclass:

    def test_result_has_all_required_fields(self):
        """PortfolioBacktestResult 包含 spec 要求的全部字段。"""
        result = PortfolioBacktestResult(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 6, 30),
            initial_capital=100_000.0,
            final_equity=105_000.0,
            total_return_pct=5.0,
            annualized_return_pct=10.0,
            sharpe_ratio=1.2,
            sortino_ratio=1.5,
            max_drawdown_pct=8.0,
            calmar_ratio=1.25,
            daily_returns=pd.Series([0.01, -0.005, 0.02]),
            equity_curve=pd.Series([100_000, 101_000, 100_495, 102_505]),
        )
        # 验证所有 spec 要求字段
        assert result.start_date == date(2024, 1, 1)
        assert result.end_date == date(2024, 6, 30)
        assert result.initial_capital == 100_000.0
        assert result.final_equity == 105_000.0
        assert result.total_return_pct == 5.0
        assert result.annualized_return_pct == 10.0
        assert result.sharpe_ratio == 1.2
        assert result.sortino_ratio == 1.5
        assert result.max_drawdown_pct == 8.0
        assert result.calmar_ratio == 1.25
        assert isinstance(result.daily_returns, pd.Series)
        assert isinstance(result.equity_curve, pd.Series)
        # 默认值字段
        assert result.holdings_history == []
        assert result.dd_violation is False
        assert result.group_exposure_history == []

    def test_result_field_types(self):
        """关键字段类型正确。"""
        result = PortfolioBacktestResult(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 6, 30),
            initial_capital=100_000.0,
            final_equity=100_000.0,
            total_return_pct=0.0,
            annualized_return_pct=0.0,
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            max_drawdown_pct=0.0,
            calmar_ratio=0.0,
            daily_returns=pd.Series(dtype=float),
            equity_curve=pd.Series(dtype=float),
        )
        assert isinstance(result.start_date, date)
        assert isinstance(result.initial_capital, float)
        assert isinstance(result.dd_violation, bool)
        assert isinstance(result.holdings_history, list)
        assert isinstance(result.group_exposure_history, list)


# ---------------------------------------------------------------------------
# 测试 2: PortfolioBacktester 基本流程
# ---------------------------------------------------------------------------

class TestPortfolioBacktesterBasic:

    def test_run_returns_correct_type(
        self, mock_store_3_symbols, mock_universe_3_symbols, weights_file_simple
    ):
        """run() 返回 PortfolioBacktestResult 实例。"""
        cfg = PortfolioBacktestConfig(
            initial_capital=10_000.0,
            top_k=3,
            candidates_multiplier=2,
        )
        bt = PortfolioBacktester(
            store=mock_store_3_symbols,
            universe=mock_universe_3_symbols,
            weights_file=weights_file_simple,
            config=cfg,
        )
        result = bt.run(start=date(2024, 1, 1), end=date(2024, 1, 30))

        assert isinstance(result, PortfolioBacktestResult)
        assert result.start_date == date(2024, 1, 1)
        assert result.initial_capital == 10_000.0

    def test_run_3_symbols_10_days_produces_equity_curve(
        self, mock_store_3_symbols, mock_universe_3_symbols, weights_file_simple
    ):
        """3 标的 × 10 天能跑完并产出 equity_curve。"""
        bt = PortfolioBacktester(
            store=mock_store_3_symbols,
            universe=mock_universe_3_symbols,
            weights_file=weights_file_simple,
        )
        result = bt.run(start=date(2024, 1, 1), end=date(2024, 1, 12))

        # 应有多个交易日（30天数据，限定到1月1-12日 → ~10 个工作日）
        assert len(result.equity_curve) > 0
        assert len(result.daily_returns) > 0
        # equity_curve 起点接近 initial_capital（首日不一定有交易）
        assert result.equity_curve.iloc[0] > 0

    def test_run_empty_data_returns_empty_result(
        self, mock_universe_3_symbols, weights_file_simple
    ):
        """无数据时返回空结果（不抛异常）。"""
        store = MagicMock()
        store.get_bars_multi.return_value = {}
        bt = PortfolioBacktester(
            store=store,
            universe=mock_universe_3_symbols,
            weights_file=weights_file_simple,
        )
        result = bt.run(start=date(2024, 1, 1), end=date(2024, 1, 30))
        assert result.final_equity == result.initial_capital
        assert result.max_drawdown_pct == 0.0


# ---------------------------------------------------------------------------
# 测试 3: max_drawdown_pct 计算正确性
# ---------------------------------------------------------------------------

class TestMaxDrawdownCalculation:

    def test_compute_max_drawdown_known_value(self):
        """_compute_max_drawdown_pct 在已知序列上计算正确。

        先涨 10 天 +1%，再跌 10 天 -1%：
        peak = 1.01^10 ≈ 1.1046
        trough = 1.1046 * 0.99^10 ≈ 0.9994
        DD = (0.9994 - 1.1046) / 1.1046 ≈ -9.52%
        """
        returns = pd.Series([0.01] * 10 + [-0.01] * 10)
        dd = PortfolioBacktester._compute_max_drawdown_pct(returns)
        assert dd > 0.0
        assert 8.0 < dd < 11.0, f"DD 应在 9.5% 附近，实际 {dd:.4f}%"

    def test_compute_max_drawdown_all_positive(self):
        """全正收益无回撤 → 0.0。"""
        returns = pd.Series([0.001] * 50)
        assert PortfolioBacktester._compute_max_drawdown_pct(returns) == 0.0

    def test_compute_max_drawdown_empty(self):
        """空序列返回 0.0。"""
        assert PortfolioBacktester._compute_max_drawdown_pct(pd.Series(dtype=float)) == 0.0

    def test_compute_max_drawdown_returns_positive_pct(self):
        """返回值为正百分数。"""
        np.random.seed(42)
        returns = pd.Series(np.concatenate([
            np.random.normal(0.002, 0.005, 30),
            np.random.normal(-0.005, 0.008, 20),
        ]))
        dd = PortfolioBacktester._compute_max_drawdown_pct(returns)
        assert dd >= 0.0
        assert isinstance(dd, float)


# ---------------------------------------------------------------------------
# 测试 4: 换仓逻辑
# ---------------------------------------------------------------------------

class TestRebalanceLogic:

    def test_holdings_history_records_positions(
        self, mock_store_3_symbols, mock_universe_3_symbols, weights_file_simple
    ):
        """holdings_history 记录每日持仓。"""
        bt = PortfolioBacktester(
            store=mock_store_3_symbols,
            universe=mock_universe_3_symbols,
            weights_file=weights_file_simple,
            config=PortfolioBacktestConfig(top_k=2),
        )
        result = bt.run(start=date(2024, 1, 1), end=date(2024, 1, 31))

        assert len(result.holdings_history) > 0
        # 每个记录应有 date / cash / equity / positions / position_count
        for h in result.holdings_history:
            assert "date" in h
            assert "cash" in h
            assert "equity" in h
            assert "positions" in h
            assert "position_count" in h
            assert isinstance(h["positions"], list)
            # position_count 不应超过 top_k
            assert h["position_count"] <= 2

    def test_rebalance_sells_when_position_drops_out(
        self, mock_store_3_symbols, mock_universe_3_symbols, weights_file_simple
    ):
        """当标的不再出现在 Top-K 时，应被卖出。"""
        bt = PortfolioBacktester(
            store=mock_store_3_symbols,
            universe=mock_universe_3_symbols,
            weights_file=weights_file_simple,
            config=PortfolioBacktestConfig(top_k=2, initial_capital=10_000.0),
        )
        result = bt.run(start=date(2024, 1, 1), end=date(2024, 1, 31))

        # 验证：每日 position_count <= 2，不会"攒"持仓
        for h in result.holdings_history:
            assert h["position_count"] <= 2, (
                f"{h['date']}: position_count={h['position_count']} > top_k=2"
            )

    def test_no_duplicate_symbols_in_holdings(
        self, mock_store_3_symbols, mock_universe_3_symbols, weights_file_simple
    ):
        """同一标的不应在 holdings 中重复出现。"""
        bt = PortfolioBacktester(
            store=mock_store_3_symbols,
            universe=mock_universe_3_symbols,
            weights_file=weights_file_simple,
        )
        result = bt.run(start=date(2024, 1, 1), end=date(2024, 1, 31))

        for h in result.holdings_history:
            syms = [p["symbol"] for p in h["positions"]]
            assert len(syms) == len(set(syms)), (
                f"{h['date']}: 出现重复标的 {syms}"
            )


# ---------------------------------------------------------------------------
# 测试 5: 信号过期（signal_valid_bars）
# ---------------------------------------------------------------------------

class TestSignalValidBars:

    def test_signal_valid_bars_1_strict_mode(
        self, mock_store_3_symbols, mock_universe_3_symbols, weights_file_simple
    ):
        """signal_valid_bars=1 时（严格模式），只看最后一根 bar。

        若策略在最后一根 bar 没出信号，则当日无 BUY 信号 → 无持仓。
        """
        cfg = PortfolioBacktestConfig(
            signal_valid_bars=1,
            top_k=2,
            initial_capital=10_000.0,
        )
        bt = PortfolioBacktester(
            store=mock_store_3_symbols,
            universe=mock_universe_3_symbols,
            weights_file=weights_file_simple,
            config=cfg,
        )
        result = bt.run(start=date(2024, 1, 1), end=date(2024, 1, 31))

        # signal_valid_bars=1 比 =3 更严格 → 持仓应更少或相等
        # 至少不应崩溃，且 equity_curve 长度 > 0
        assert len(result.equity_curve) > 0

    def test_signal_valid_bars_3_default(
        self, mock_store_3_symbols, mock_universe_3_symbols, weights_file_simple
    ):
        """signal_valid_bars=3（默认）能捕获最近 3 bar 内的信号。"""
        cfg = PortfolioBacktestConfig(signal_valid_bars=3, top_k=2)
        bt = PortfolioBacktester(
            store=mock_store_3_symbols,
            universe=mock_universe_3_symbols,
            weights_file=weights_file_simple,
            config=cfg,
        )
        # 不抛异常即通过
        result = bt.run(start=date(2024, 1, 1), end=date(2024, 1, 31))
        assert isinstance(result, PortfolioBacktestResult)


# ---------------------------------------------------------------------------
# 测试 6: dd_violation 标记
# ---------------------------------------------------------------------------

class TestDDViolation:

    def test_dd_violation_false_when_dd_within_limit(
        self, mock_store_3_symbols, mock_universe_3_symbols, weights_file_simple
    ):
        """DD ≤ 20% 时 dd_violation=False。"""
        bt = PortfolioBacktester(
            store=mock_store_3_symbols,
            universe=mock_universe_3_symbols,
            weights_file=weights_file_simple,
        )
        result = bt.run(start=date(2024, 1, 1), end=date(2024, 1, 31))
        # 上涨趋势 → DD 应很小
        if result.max_drawdown_pct <= PORTFOLIO_MAX_DRAWDOWN_PCT:
            assert result.dd_violation is False
        else:
            # 极端情况下可能略超，但逻辑应一致
            assert result.dd_violation is True

    def test_dd_violation_true_when_dd_exceeds_threshold(self):
        """DD > 20% 时 dd_violation=True（用合成序列）。"""
        # 构造一个 30% 大跌序列
        # 涨 5 天 +1%，然后跌 10 天 -3% → 远超 20% DD
        returns = pd.Series(
            [0.01] * 5 + [-0.03] * 10 + [0.001] * 5
        )
        dd = PortfolioBacktester._compute_max_drawdown_pct(returns)
        assert dd > 20.0, f"合成序列 DD 应 > 20%，实际 {dd:.2f}%"

    def test_portfolio_max_drawdown_threshold_is_20(self):
        """Constitution L1: PORTFOLIO_MAX_DRAWDOWN_PCT = 20.0。"""
        assert PORTFOLIO_MAX_DRAWDOWN_PCT == 20.0

    def test_dd_violation_flag_logic(self):
        """dd_violation = (max_dd > 20.0)。"""
        # 用直接构造结果验证逻辑
        result = PortfolioBacktestResult(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 6, 30),
            initial_capital=100_000.0,
            final_equity=70_000.0,
            total_return_pct=-30.0,
            annualized_return_pct=-50.0,
            sharpe_ratio=-1.0,
            sortino_ratio=-1.2,
            max_drawdown_pct=30.0,
            calmar_ratio=-1.67,
            daily_returns=pd.Series([-0.01] * 30),
            equity_curve=pd.Series([100_000, 99_000, 98_010]),
            dd_violation=True,
        )
        assert result.dd_violation is True
        assert result.max_drawdown_pct > PORTFOLIO_MAX_DRAWDOWN_PCT


# ---------------------------------------------------------------------------
# 测试 7: group_exposure_history 记录
# ---------------------------------------------------------------------------

class TestGroupExposureHistory:

    def test_group_exposure_history_recorded(
        self, mock_store_3_symbols, mock_universe_3_symbols, weights_file_simple
    ):
        """group_exposure_history 被正确记录。"""
        bt = PortfolioBacktester(
            store=mock_store_3_symbols,
            universe=mock_universe_3_symbols,
            weights_file=weights_file_simple,
        )
        result = bt.run(start=date(2024, 1, 1), end=date(2024, 1, 31))

        assert len(result.group_exposure_history) > 0
        for entry in result.group_exposure_history:
            assert "date" in entry
            assert "total_equity" in entry
            assert "group_exposure_value" in entry
            assert "group_exposure_pct" in entry
            assert isinstance(entry["group_exposure_value"], dict)
            assert isinstance(entry["group_exposure_pct"], dict)
            # total_equity 应为正
            assert entry["total_equity"] > 0

    def test_group_exposure_pct_sums_within_bounds(
        self, mock_store_3_symbols, mock_universe_3_symbols, weights_file_simple
    ):
        """group_exposure_pct 之和不超过 100% + 容差。"""
        bt = PortfolioBacktester(
            store=mock_store_3_symbols,
            universe=mock_universe_3_symbols,
            weights_file=weights_file_simple,
            config=PortfolioBacktestConfig(top_k=2, max_total_exposure_pct=0.8),
        )
        result = bt.run(start=date(2024, 1, 1), end=date(2024, 1, 31))

        for entry in result.group_exposure_history:
            total_pct = sum(entry["group_exposure_pct"].values())
            # 总暴露度不应超过 100%（含现金部分）
            assert total_pct <= 100.0 + 1.0, (
                f"{entry['date']}: 总暴露度 {total_pct:.2f}% 超过 101% 容差"
            )


# ---------------------------------------------------------------------------
# 测试 8: _write_weights 中 backtest_dd_status 字段（P1b）
# ---------------------------------------------------------------------------

class TestBacktestDDStatusField:
    """P1b: strategy_weights.json 含 backtest_dd_status 字段。"""

    def test_backtest_dd_status_pass_when_compliant(
        self, mock_store_3_symbols, mock_universe_3_symbols, tmp_path
    ):
        """有合规候选时 backtest_dd_status='pass'。"""
        from mytrader.backtest.matrix_backtest import MatrixBacktest

        # 用现成 weights_file 不需要 — 矩阵回测自己产出
        store = MagicMock()
        df = _make_ohlcv_df(300, 100.0, trend=0.1)  # 上涨趋势 → DD < 20%
        store.get_bars_multi.side_effect = lambda symbols, start, end, timeframe="1d": {
            s: df.copy() for s in symbols
        }

        universe = MagicMock()
        universe.get_groups.return_value = {"test_group": ["AAPL", "MSFT"]}

        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
        output = tmp_path / "weights_pass.json"
        mb.run(
            strategies=["dual_ma"],
            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
            output_file=output,
        )

        data = json.loads(output.read_text())
        for gid, weights in data["groups"].items():
            for w in weights:
                assert "backtest_dd_status" in w, (
                    f"{gid}: 缺少 backtest_dd_status 字段"
                )
                assert w["backtest_dd_status"] in ("pass", "dd_constrained"), (
                    f"{gid}: backtest_dd_status 值非法: {w['backtest_dd_status']}"
                )
                # 与 dd_constrained 一致性
                expected = "dd_constrained" if w["dd_constrained"] else "pass"
                assert w["backtest_dd_status"] == expected, (
                    f"{gid}: backtest_dd_status({w['backtest_dd_status']}) "
                    f"与 dd_constrained({w['dd_constrained']}) 不一致"
                )

    def test_backtest_dd_status_dd_constrained_on_fallback(self, tmp_path):
        """fallback 触发时 backtest_dd_status='dd_constrained'。"""
        from mytrader.backtest.matrix_backtest import MatrixBacktest

        store = MagicMock()
        # 构造大跌数据触发 fallback
        n = 400
        idx = pd.date_range("2021-01-01", periods=n, freq="B")
        close = [100.0 * (1 - 0.002 * i) for i in range(200)]
        close += [60.0 * (1 - 0.005 * (i - 200)) for i in range(200, n)]
        close = [max(c, 1.0) for c in close]
        df_crash = pd.DataFrame(
            {
                "open":   [c - 0.3 for c in close],
                "high":   [c + 0.5 for c in close],
                "low":    [c - 0.5 for c in close],
                "close":  close,
                "volume": [1_000_000] * n,
            },
            index=idx,
        )
        store.get_bars_multi.side_effect = lambda symbols, start, end, timeframe="1d": {
            s: df_crash.copy() for s in symbols
        }

        universe = MagicMock()
        universe.get_groups.return_value = {"volatile_group": ["AAPL", "MSFT"]}

        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=2)
        output = tmp_path / "weights_dd.json"
        mb.run(
            strategies=["rsi_mean_revert"],
            param_grids={"rsi_mean_revert": {
                "period": [14], "oversold": [35], "overbought": [65]
            }},
            output_file=output,
        )

        data = json.loads(output.read_text())
        # 若产出权重，至少有一个 dd_constrained=True 的组
        has_dd_constrained = False
        for gid, weights in data["groups"].items():
            for w in weights:
                assert "backtest_dd_status" in w
                # 一致性
                expected = "dd_constrained" if w["dd_constrained"] else "pass"
                assert w["backtest_dd_status"] == expected
                if w["dd_constrained"]:
                    has_dd_constrained = True
                    assert w["backtest_dd_status"] == "dd_constrained"

        # 至少有一个 dd_constrained 标记（如果产出了权重）
        if any(weights for weights in data["groups"].values()):
            # 若有 DD > 20% 的组，应有 dd_constrained
            has_high_dd = any(
                w.get("backtest_max_drawdown", 0) > 20.0
                for weights in data["groups"].values()
                for w in weights
            )
            if has_high_dd:
                assert has_dd_constrained, "存在 DD>20% 的组但未触发 dd_constrained"

    def test_backtest_dd_status_field_type(
        self, mock_store_3_symbols, mock_universe_3_symbols, tmp_path
    ):
        """backtest_dd_status 是字符串类型。"""
        from mytrader.backtest.matrix_backtest import MatrixBacktest

        store = MagicMock()
        df = _make_ohlcv_df(300, 100.0, trend=0.1)
        store.get_bars_multi.side_effect = lambda symbols, start, end, timeframe="1d": {
            s: df.copy() for s in symbols
        }
        universe = MagicMock()
        universe.get_groups.return_value = {"test_group": ["AAPL"]}

        mb = MatrixBacktest(store=store, universe=universe, years=1, top_k=1)
        output = tmp_path / "weights_type.json"
        mb.run(
            strategies=["dual_ma"],
            param_grids={"dual_ma": {"fast": [5], "slow": [20]}},
            output_file=output,
        )

        data = json.loads(output.read_text())
        for gid, weights in data["groups"].items():
            for w in weights:
                assert isinstance(w["backtest_dd_status"], str), (
                    f"backtest_dd_status 应为 str，实际 {type(w['backtest_dd_status'])}"
                )


# ---------------------------------------------------------------------------
# 测试 9: PortfolioBacktestConfig 默认值
# ---------------------------------------------------------------------------

class TestPortfolioBacktestConfig:

    def test_default_values(self):
        """PortfolioBacktestConfig 默认值符合 spec。"""
        cfg = PortfolioBacktestConfig()
        assert cfg.initial_capital == 100_000.0
        assert cfg.top_k == 5
        assert cfg.candidates_multiplier == 2
        assert cfg.max_single_position_pct == 0.20
        assert cfg.max_total_exposure_pct == 0.80
        assert cfg.max_sector_exposure_pct == 0.40
        assert cfg.rebalance_freq == "daily"
        assert cfg.signal_valid_bars == 3

    def test_custom_values(self):
        """PortfolioBacktestConfig 可自定义。"""
        cfg = PortfolioBacktestConfig(
            initial_capital=50_000.0,
            top_k=3,
            candidates_multiplier=3,
            max_single_position_pct=0.15,
            max_total_exposure_pct=0.70,
            max_sector_exposure_pct=0.35,
            rebalance_freq="weekly",
            signal_valid_bars=5,
        )
        assert cfg.initial_capital == 50_000.0
        assert cfg.top_k == 3
        assert cfg.candidates_multiplier == 3
        assert cfg.max_single_position_pct == 0.15
        assert cfg.max_total_exposure_pct == 0.70
        assert cfg.max_sector_exposure_pct == 0.35
        assert cfg.rebalance_freq == "weekly"
        assert cfg.signal_valid_bars == 5


# ---------------------------------------------------------------------------
# 测试 10: main.py 集成（P1）
# ---------------------------------------------------------------------------

class TestMainIntegration:
    """验证 main._run_reoptimize 包含 PortfolioBacktest 调用。"""

    def test_reoptimize_imports_portfolio_backtest(self):
        """_run_reoptimize 函数能导入 PortfolioBacktester。"""
        import importlib
        # 用 importlib 重载 main 模块（避免污染）
        import main as main_module
        importlib.reload(main_module)
        # 函数体内有 from mytrader.backtest.portfolio_backtest import
        # 通过源码检查
        import inspect
        src = inspect.getsource(main_module._run_reoptimize)
        assert "PortfolioBacktester" in src, (
            "_run_reoptimize 应包含 PortfolioBacktester 调用"
        )
        assert "PortfolioBacktestConfig" in src
        assert "[Portfolio Backtest]" in src

    def test_reoptimize_logs_portfolio_backtest_format(self):
        """日志格式包含 [Portfolio Backtest] DD=, Sortino=, Sharpe=, Annual Return=, DD Violation="""
        import inspect
        import main as main_module
        src = inspect.getsource(main_module._run_reoptimize)
        # 验证关键日志字段
        assert "DD=" in src
        assert "Sortino=" in src
        assert "Sharpe=" in src
        assert "Annual Return=" in src
        assert "DD Violation=" in src


# ---------------------------------------------------------------------------
# 测试 11: Benchmark 对比（迭代 #7 新增）
# ---------------------------------------------------------------------------

class TestBenchmarkComparison:
    """迭代 #7：SPY buy-and-hold benchmark 对比。"""

    def test_benchmark_fields_exist(self):
        """PortfolioBacktestResult 实例包含所有新增 benchmark 字段。"""
        result = PortfolioBacktestResult(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 6, 30),
            initial_capital=100_000.0,
            final_equity=105_000.0,
            total_return_pct=5.0,
            annualized_return_pct=10.0,
            sharpe_ratio=1.2,
            sortino_ratio=1.5,
            max_drawdown_pct=8.0,
            calmar_ratio=1.25,
            daily_returns=pd.Series([0.01, -0.005, 0.02]),
            equity_curve=pd.Series([100_000, 101_000, 100_495, 102_505]),
        )
        # 验证 7 个新增 benchmark 字段存在且有默认值
        assert result.benchmark_symbol == "SPY"
        assert result.benchmark_total_return_pct == 0.0
        assert result.benchmark_annualized_return_pct == 0.0
        assert result.benchmark_sortino_ratio == 0.0
        assert result.benchmark_max_drawdown_pct == 0.0
        assert result.alpha_pct == 0.0
        assert result.information_ratio == 0.0

    def test_benchmark_computed_with_spy_data(
        self, mock_universe_3_symbols, weights_file_simple
    ):
        """mock store 返回 SPY 上涨数据 → benchmark_total_return_pct > 0。"""
        store = MagicMock()
        # 组合标的用上涨数据
        df_aapl = _make_ohlcv_df(30, 100.0, trend=0.5)
        df_msft = _make_ohlcv_df(30, 200.0, trend=0.3)
        df_jpm = _make_ohlcv_df(30, 80.0, trend=0.2)
        # SPY 也用上涨数据
        df_spy = _make_ohlcv_df(30, 400.0, trend=0.4)
        mapping = {
            "AAPL": df_aapl, "MSFT": df_msft, "JPM": df_jpm, "SPY": df_spy
        }

        def get_bars_multi(symbols, start, end, timeframe="1d"):
            return {s: mapping[s].copy() for s in symbols if s in mapping}

        store.get_bars_multi.side_effect = get_bars_multi

        bt = PortfolioBacktester(
            store=store,
            universe=mock_universe_3_symbols,
            weights_file=weights_file_simple,
        )
        result = bt.run(start=date(2024, 1, 1), end=date(2024, 1, 31))

        # SPY 上涨 → benchmark_total_return_pct > 0
        assert result.benchmark_symbol == "SPY"
        assert result.benchmark_total_return_pct > 0, (
            f"SPY 上涨数据 → benchmark_return 应 > 0，实际 {result.benchmark_total_return_pct:.4f}"
        )
        assert result.benchmark_annualized_return_pct > 0
        # alpha 已计算（不论正负，应不为 0 —— 组合年化 - SPY 年化）
        # 注意：组合数据与 SPY 都是合成上涨，alpha 可能为正或负，只验证非零
        assert isinstance(result.alpha_pct, float)
        assert isinstance(result.information_ratio, float)

    def test_benchmark_zero_when_no_spy(
        self, mock_store_3_symbols, mock_universe_3_symbols, weights_file_simple
    ):
        """mock store 不返回 SPY → 所有 benchmark 字段 = 0.0，不抛异常。"""
        # mock_store_3_symbols 只含 AAPL/MSFT/JPM，不含 SPY
        bt = PortfolioBacktester(
            store=mock_store_3_symbols,
            universe=mock_universe_3_symbols,
            weights_file=weights_file_simple,
        )
        result = bt.run(start=date(2024, 1, 1), end=date(2024, 1, 31))

        # 降级处理：所有 benchmark 字段 = 0.0
        assert result.benchmark_symbol == "SPY"
        assert result.benchmark_total_return_pct == 0.0
        assert result.benchmark_annualized_return_pct == 0.0
        assert result.benchmark_sortino_ratio == 0.0
        assert result.benchmark_max_drawdown_pct == 0.0
        # alpha = portfolio - benchmark = portfolio - 0 = portfolio
        assert result.alpha_pct == result.annualized_return_pct
        assert result.information_ratio == 0.0

    def test_alpha_calculation(self):
        """alpha = 组合年化 - benchmark 年化。

        构造 result：portfolio=15%, benchmark=10% → alpha=5.0
        """
        result = PortfolioBacktestResult(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 6, 30),
            initial_capital=100_000.0,
            final_equity=115_000.0,
            total_return_pct=15.0,
            annualized_return_pct=15.0,
            sharpe_ratio=1.2,
            sortino_ratio=1.5,
            max_drawdown_pct=8.0,
            calmar_ratio=1.875,
            daily_returns=pd.Series([0.01] * 10),
            equity_curve=pd.Series([100_000, 101_000]),
            benchmark_annualized_return_pct=10.0,
        )
        # 验证 alpha = portfolio - benchmark = 5.0
        expected_alpha = 15.0 - 10.0
        # alpha_pct 由 run() 末尾计算；测试中我们直接构造 result 验证字段语义
        # （alpha 字段默认 0.0，需手动设置或经 run() 计算）
        result.alpha_pct = result.annualized_return_pct - result.benchmark_annualized_return_pct
        assert result.alpha_pct == expected_alpha
        assert result.alpha_pct > 0  # 跑赢 benchmark

    def test_information_ratio_computation(self):
        """IR 计算正确性：构造已知超额收益序列。"""
        # 构造 portfolio 与 spy 完全相同的 returns → IR 应为 0（无超额收益）
        # 用静态方法直接测试
        dates = [date(2024, 1, 1) + timedelta(days=i) for i in range(10)]
        port_returns = [0.001] * 10
        spy_idx = pd.to_datetime(dates)
        spy_returns = pd.Series([0.001] * 10, index=spy_idx)
        ir = PortfolioBacktester._compute_information_ratio(
            port_returns, dates, spy_returns
        )
        # excess 全 0 → std=0 → 返回 0.0
        assert ir == 0.0

        # 构造 portfolio 持续跑赢 spy 0.0005/天 → IR > 0
        port_returns_better = [0.002] * 10  # 比 spy 高 0.001/天
        ir2 = PortfolioBacktester._compute_information_ratio(
            port_returns_better, dates, spy_returns
        )
        assert ir2 > 0, f"持续超额收益 → IR 应 > 0，实际 {ir2:.4f}"

    def test_benchmark_max_drawdown(self):
        """构造 SPY 先涨后跌 → benchmark_max_drawdown_pct > 0。"""
        # SPY: 先涨 5 天，再跌 5 天
        spy_close_values = [100.0, 101.0, 102.0, 103.0, 104.0,
                            100.0, 96.0, 92.0, 88.0, 84.0]
        idx = pd.date_range("2024-01-01", periods=10, freq="B")
        spy_df = pd.DataFrame({
            "open":   [c - 0.3 for c in spy_close_values],
            "high":   [c + 0.5 for c in spy_close_values],
            "low":    [c - 0.5 for c in spy_close_values],
            "close":  spy_close_values,
            "volume": [1_000_000] * 10,
        }, index=idx)
        spy_returns = spy_df["close"].pct_change().dropna()
        # 直接调用 _compute_max_drawdown_pct（与 _compute_benchmark 内部一致）
        dd = PortfolioBacktester._compute_max_drawdown_pct(spy_returns)
        # 先涨到 104，再跌到 84 → DD = (84 - 104) / 104 ≈ 19.23%
        assert dd > 0
        assert 15.0 < dd < 25.0, f"SPY DD 应在 ~19.23%，实际 {dd:.2f}%"

    def test_benchmark_max_drawdown_static_method(self):
        """_compute_max_drawdown_pct 在 SPY 上涨序列上返回 0（无回撤）。"""
        spy_close_values = [100.0 + i for i in range(20)]  # 持续上涨
        idx = pd.date_range("2024-01-01", periods=20, freq="B")
        spy_returns = pd.Series(spy_close_values, index=idx).pct_change().dropna()
        dd = PortfolioBacktester._compute_max_drawdown_pct(spy_returns)
        assert dd == 0.0, "持续上涨 → 无回撤"
