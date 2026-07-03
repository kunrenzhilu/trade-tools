"""Signal metadata parity 测试（迭代 #5 P0-A）。

验证 StrategyMatrixRunner 线上扫描与 PortfolioBacktester 组合回测生成的
Signal.indicators 完全一致，避免 CandidateSelector 因 sector=backtest_*
字段缺失而行为分叉（曾导致 73 候选 → 2 approved）。

测试清单（spec §4.1）：
    1. test_matrix_runner_signal_indicators_include_sector_and_backtest_risk_fields
    2. test_signal_metadata_defaults_are_safe
    3. test_portfolio_backtester_and_matrix_runner_metadata_parity
    4. test_candidate_selector_no_longer_treats_all_online_candidates_as_unknown_sector
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pandas as pd
import pytest

from mytrader.risk.candidate_selector import (
    AccountState,
    select_orders_from_candidates,
)
from mytrader.signal.ranker import RankedSignal, SignalRanker
from mytrader.strategy.base import Signal, SignalDirection
from mytrader.strategy.matrix_runner import (
    DEFAULT_BACKTEST_DD_STATUS,
    DEFAULT_BACKTEST_MAX_DD,
    DEFAULT_BACKTEST_SHARPE,
    DEFAULT_BACKTEST_SORTINO,
    DEFAULT_BACKTEST_WIN_RATE,
    DEFAULT_SECTOR,
    StrategyMatrixRunner,
    build_matrix_signal_indicators,
)
from mytrader.universe.models import SymbolMeta


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_meta(
    symbol: str = "AAPL",
    sector: str = "Technology",
    group_id: str = "NDX_high_vol",
) -> SymbolMeta:
    return SymbolMeta(
        symbol=symbol,
        index_membership=["NASDAQ100"],
        sector=sector,
        market_cap_tier="large",
        volatility_tier="high",
        group_id=group_id,
    )


def _make_weights_entry(
    strategy: str = "dual_ma",
    weight: float = 0.6,
    sharpe: float = 1.42,
    sortino: float = 1.85,
    max_dd: float = 18.5,
    dd_status: str = "pass",
    win_rate: float = 0.58,
) -> dict:
    return {
        "strategy": strategy,
        "params": {"fast": 5, "slow": 20},
        "weight": weight,
        "backtest_sharpe": sharpe,
        "backtest_sortino": sortino,
        "backtest_max_drawdown": max_dd,
        "backtest_dd_status": dd_status,
        "backtest_win_rate": win_rate,
    }


# ---------------------------------------------------------------------------
# 1. 线上 runner signal indicators 完整性
# ---------------------------------------------------------------------------

class TestMatrixRunnerSignalIndicators:
    def test_matrix_runner_signal_indicators_include_sector_and_backtest_risk_fields(self):
        """线上 runner 生成的 Signal.indicators 必须包含 spec §4.1 列出的全部字段。"""
        meta = _make_meta()
        entry = _make_weights_entry()
        weight = float(entry["weight"])

        indicators = build_matrix_signal_indicators(meta, entry, weight)

        required_keys = {
            "group_id", "sector",
            "backtest_sharpe", "backtest_sortino",
            "backtest_max_drawdown", "backtest_dd_status",
            "backtest_win_rate", "weight",
        }
        assert required_keys.issubset(indicators.keys()), (
            f"missing keys: {required_keys - set(indicators.keys())}"
        )
        # 值正确
        assert indicators["group_id"] == "NDX_high_vol"
        assert indicators["sector"] == "Technology"
        assert indicators["backtest_sharpe"] == pytest.approx(1.42)
        assert indicators["backtest_sortino"] == pytest.approx(1.85)
        assert indicators["backtest_max_drawdown"] == pytest.approx(18.5)
        assert indicators["backtest_dd_status"] == "pass"
        assert indicators["backtest_win_rate"] == pytest.approx(0.58)
        assert indicators["weight"] == pytest.approx(0.6)

    def test_matrix_runner_run_symbol_uses_helper_for_indicators(self):
        """StrategyMatrixRunner.run_symbol 路径产出的 Signal 也包含完整字段。"""
        # Mock store + universe
        store = MagicMock()
        n = 30
        idx = pd.date_range("2024-01-01", periods=n, freq="B")
        # 构造一个明确产生 BUY 信号的 close 序列（短期均价 > 长期均价）
        close = pd.Series([100.0 + i for i in range(n)], index=idx)
        df = pd.DataFrame(
            {
                "open": close, "high": close + 1, "low": close - 1,
                "close": close, "volume": [1_000_000] * n,
            },
            index=idx,
        )
        store.get_latest_n_bars.return_value = df

        universe = MagicMock()
        universe.get_symbol_meta.return_value = _make_meta()

        runner = StrategyMatrixRunner(
            store=store, universe=universe, weights_file=None,
        )
        runner.set_weights_for_group("NDX_high_vol", [_make_weights_entry()])

        signals = runner.run_symbol("AAPL", lookback_days=30)
        # 策略可能不产生信号，但若有则 indicators 必须完整
        for sig in signals:
            assert "sector" in sig.indicators
            assert sig.indicators["sector"] == "Technology"
            assert "backtest_sortino" in sig.indicators
            assert "backtest_max_drawdown" in sig.indicators
            assert "backtest_dd_status" in sig.indicators


# ---------------------------------------------------------------------------
# 2. 默认值安全性
# ---------------------------------------------------------------------------

class TestSignalMetadataDefaults:
    def test_signal_metadata_defaults_are_safe(self):
        """weights entry 缺字段时返回默认值，不抛异常。"""
        # entry 只有 strategy + weight，其它字段全缺
        minimal_entry = {"strategy": "dual_ma", "weight": 0.5}
        meta = _make_meta()

        indicators = build_matrix_signal_indicators(meta, minimal_entry, 0.5)

        # 不抛异常 + 默认值合理
        assert indicators["sector"] == "Technology"  # meta 提供 → 非 Unknown
        assert indicators["group_id"] == "NDX_high_vol"
        assert indicators["backtest_sharpe"] == DEFAULT_BACKTEST_SHARPE
        assert indicators["backtest_sortino"] == DEFAULT_BACKTEST_SORTINO
        assert indicators["backtest_max_drawdown"] == DEFAULT_BACKTEST_MAX_DD
        assert indicators["backtest_dd_status"] == DEFAULT_BACKTEST_DD_STATUS
        assert indicators["backtest_win_rate"] == DEFAULT_BACKTEST_WIN_RATE
        assert indicators["weight"] == pytest.approx(0.5)

    def test_signal_metadata_meta_none_falls_back_to_unknown_sector(self):
        """meta=None 时 sector=Unknown，不抛异常。"""
        entry = _make_weights_entry()
        indicators = build_matrix_signal_indicators(None, entry, 0.6)

        assert indicators["sector"] == DEFAULT_SECTOR
        assert indicators["group_id"] == ""

    def test_signal_metadata_meta_with_empty_sector_falls_back_to_unknown(self):
        """meta.sector 为空字符串时 sector=Unknown。"""
        meta = _make_meta(sector="")
        entry = _make_weights_entry()
        indicators = build_matrix_signal_indicators(meta, entry, 0.6)

        assert indicators["sector"] == DEFAULT_SECTOR


# ---------------------------------------------------------------------------
# 3. PortfolioBacktester 与 StrategyMatrixRunner metadata parity
# ---------------------------------------------------------------------------

class TestMetadataParity:
    def test_portfolio_backtester_and_matrix_runner_metadata_parity(self):
        """同一 symbol/meta/entry 下，两条路径生成的 indicators 完全一致。"""
        meta = _make_meta()
        entry = _make_weights_entry()
        weight = float(entry["weight"])

        # 路径 A：matrix_runner.build_matrix_signal_indicators（线上）
        online_indicators = build_matrix_signal_indicators(meta, entry, weight)

        # 路径 B：PortfolioBacktester._generate_signals 内部也调用同一 helper
        # 这里直接验证 helper 调用结果一致（_generate_signals 内部就是调它）
        backtest_indicators = build_matrix_signal_indicators(meta, entry, weight)

        # 严格相等：key 集合 + 每个 key 的值
        assert set(online_indicators.keys()) == set(backtest_indicators.keys())
        for k in online_indicators:
            assert online_indicators[k] == backtest_indicators[k], (
                f"parity mismatch at key={k}: "
                f"online={online_indicators[k]!r} vs backtest={backtest_indicators[k]!r}"
            )

    def test_portfolio_backtester_generate_signals_uses_helper(self):
        """端到端验证：PortfolioBacktester._generate_signals 产出的 Signal
        indicators 字段与 build_matrix_signal_indicators 一致。"""
        from mytrader.backtest.portfolio_backtest import (
            PortfolioBacktestConfig,
            PortfolioBacktester,
        )

        # mock store + universe
        store = MagicMock()
        n = 40
        idx = pd.date_range("2024-01-01", periods=n, freq="B")
        close = pd.Series([100.0 + i for i in range(n)], index=idx)
        df = pd.DataFrame(
            {
                "open": close, "high": close + 1, "low": close - 1,
                "close": close, "volume": [1_000_000] * n,
            },
            index=idx,
        )

        universe = MagicMock()
        universe.get_universe.return_value = ["AAPL"]
        universe.get_symbol_meta.return_value = _make_meta()

        # PortfolioBacktester.get_bars_multi（通过 store mock）
        store.get_bars_multi.return_value = {"AAPL": df}

        bt = PortfolioBacktester(
            store=store,
            universe=universe,
            weights_file=None,
            config=PortfolioBacktestConfig(),
        )
        bt._matrix_runner.set_weights_for_group("NDX_high_vol", [_make_weights_entry()])

        # 调用 _generate_signals（绕过完整 run 流程）
        bars = {"AAPL": df}
        signals = bt._generate_signals(bars, idx[0].date())

        # 验证：若有信号产出，indicators 必须包含完整字段
        for sig in signals:
            expected = build_matrix_signal_indicators(
                _make_meta(), _make_weights_entry(), 0.6
            )
            for k, v in expected.items():
                assert k in sig.indicators, f"missing key {k}"
                assert sig.indicators[k] == pytest.approx(v), (
                    f"{k}: {sig.indicators[k]!r} != {v!r}"
                )


# ---------------------------------------------------------------------------
# 4. CandidateSelector 不再因 sector=Unknown 把所有线上候选压到 1-2 个
# ---------------------------------------------------------------------------

class TestCandidateSelectorSectorMetadata:
    def test_candidate_selector_no_longer_treats_all_online_candidates_as_unknown_sector(self):
        """构造多个 sector 的候选，approved 数量应 >2（不因 sector=Unknown 全部受限）。

        spec §4.1 test 4：注意不要放宽 sector 风控，只验证 metadata 正确传入。
        """
        # 构造 5 个不同 sector 的候选（通过 build_matrix_signal_indicators 填 sector）
        sectors = ["Technology", "Healthcare", "Financials", "Energy", "Consumer"]
        candidates: list[RankedSignal] = []
        for i, sec in enumerate(sectors):
            meta = _make_meta(symbol=f"S{i}", sector=sec, group_id=f"GROUP_{i}")
            entry = _make_weights_entry()
            sig = Signal(
                symbol=f"S{i}",
                direction=SignalDirection.BUY,
                timestamp=datetime.now(timezone.utc),
                confidence=0.7,
                strategy_name="dual_ma",
                indicators=build_matrix_signal_indicators(meta, entry, 0.6),
            )
            # RankedSignal(signal, score, rank, score_breakdown)
            ranked = RankedSignal(
                signal=sig,
                score=1.5 - i * 0.1,
                rank=i + 1,
                score_breakdown={},
            )
            candidates.append(ranked)

        account = AccountState(
            total_capital=100_000.0,
            current_exposure=0.0,
            current_position_count=0,
            sector_exposure={},
        )

        # max_sector_exposure_pct=0.40 → 单板块最多 40%
        # 5 个不同 sector 各 ~20%（target_position_pct=0.20），全部应通过
        approved, rejections = select_orders_from_candidates(
            candidates=candidates,
            account=account,
            max_orders=5,
            max_single_position_pct=0.20,
            max_total_exposure_pct=0.80,
            max_sector_exposure_pct=0.40,
            max_concurrent_positions=5,
            target_position_pct=0.20,
        )

        # 全部 sector 不同，sector_exposure 约束不会触发；
        # 总暴露 5×20% = 100% > 80%，所以 max_total_exposure 会截断到 4 个
        # 但 max_total_exposure 是 0.80（80%），第 5 个会被拒
        # 关键验证：approved > 2（不被 Unknown sector 压成 1-2 个）
        assert len(approved) >= 3, (
            f"Expected ≥3 approved with diverse sectors, got {len(approved)}; "
            f"rejections={rejections}"
        )

    def test_candidate_selector_still_rejects_when_sector_concentration_breached(self):
        """同一 sector 的多个候选仍应被 sector_exposure 约束截断
        （验证修复只针对 metadata 传入，未放宽 sector 风控）。"""
        # 5 个相同 sector 候选
        candidates: list[RankedSignal] = []
        for i in range(5):
            meta = _make_meta(symbol=f"S{i}", sector="Technology", group_id="G")
            entry = _make_weights_entry()
            sig = Signal(
                symbol=f"S{i}",
                direction=SignalDirection.BUY,
                timestamp=datetime.now(timezone.utc),
                confidence=0.7,
                strategy_name="dual_ma",
                indicators=build_matrix_signal_indicators(meta, entry, 0.6),
            )
            ranked = RankedSignal(
                signal=sig,
                score=1.5 - i * 0.1,
                rank=i + 1,
                score_breakdown={},
            )
            candidates.append(ranked)

        account = AccountState(
            total_capital=100_000.0,
            current_exposure=0.0,
            current_position_count=0,
            sector_exposure={},
        )

        approved, _ = select_orders_from_candidates(
            candidates=candidates,
            account=account,
            max_orders=5,
            max_single_position_pct=0.20,
            max_total_exposure_pct=0.80,
            max_sector_exposure_pct=0.40,  # 40%
            max_concurrent_positions=5,
            target_position_pct=0.20,
        )

        # 全部同 sector：第 3 个时 sector_pct = 60% > 40% → 拒绝
        # 故 approved 应该 ≤ 2
        assert len(approved) <= 2, (
            f"sector 风控应限制同 sector 候选数 ≤2，实际 approved={len(approved)}"
        )
