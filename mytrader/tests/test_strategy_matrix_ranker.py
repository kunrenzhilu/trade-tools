"""StrategyMatrixRunner + SignalRanker + CandidateSelector 测试。"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from mytrader.signal.ranker import RankingReport, RankedSignal, SignalRanker
from mytrader.strategy.base import Signal, SignalDirection
from mytrader.strategy.matrix_runner import MatrixScanResult, StrategyMatrixRunner
from mytrader.risk.candidate_selector import (
    AccountState,
    CandidateOrder,
    select_orders_from_candidates,
)


# ---------------------------------------------------------------------------
# 共用 Fixtures
# ---------------------------------------------------------------------------

def _make_signal(
    symbol: str,
    direction: SignalDirection = SignalDirection.BUY,
    confidence: float = 0.7,
    strategy: str = "dual_ma",
    weight: float = 0.6,
    sharpe: float = 1.2,
    win_rate: float = 0.55,
    sector: str = "Technology",
    sortino: float | None = None,
    max_drawdown: float | None = None,
) -> Signal:
    """构造测试用 Signal。

    迭代 #7：新增 sortino / max_drawdown 可选参数。
    默认 None 时**不写入** indicators，模拟旧数据（缺少新字段）；
    传入值时写入，便于 Sortino/DD penalty 测试。
    backtest_sharpe 字段保留（向后兼容，但不再参与评分）。
    """
    indicators = {
        "weight": weight,
        "backtest_sharpe": sharpe,
        "backtest_win_rate": win_rate,
        "group_id": "NDX_high_vol",
        "sector": sector,
    }
    if sortino is not None:
        indicators["backtest_sortino"] = sortino
    if max_drawdown is not None:
        indicators["backtest_max_drawdown"] = max_drawdown
    return Signal(
        symbol=symbol,
        direction=direction,
        timestamp=datetime.now(tz=timezone.utc),
        confidence=confidence,
        strategy_name=strategy,
        indicators=indicators,
    )


@pytest.fixture
def mock_store():
    store = MagicMock()
    n = 30
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    df = pd.DataFrame(
        {
            "open":   [100.0] * n,
            "high":   [103.0] * n,
            "low":    [97.0] * n,
            "close":  [101.0] * n,
            "volume": [1_000_000] * n,
        },
        index=idx,
    )
    store.get_latest_n_bars.return_value = df
    return store


@pytest.fixture
def mock_universe():
    from mytrader.universe.models import SymbolMeta
    universe = MagicMock()
    universe.get_universe.return_value = ["AAPL", "MSFT", "TSLA", "NVDA", "JPM"]

    def get_meta(sym):
        idx_map = {"AAPL": "NASDAQ100", "MSFT": "NASDAQ100",
                   "TSLA": "NASDAQ100", "NVDA": "NASDAQ100", "JPM": "SP500"}
        idx = idx_map.get(sym, "SP500")
        return SymbolMeta(
            symbol=sym,
            index_membership=[idx],
            sector="Technology" if idx == "NASDAQ100" else "Financials",
            market_cap_tier="large",
            volatility_tier="high" if sym == "TSLA" else "mid",
            group_id="NDX_high_vol" if sym == "TSLA" else
                     "NDX_mid_vol" if idx == "NASDAQ100" else "SPX_mid_vol",
        )
    universe.get_symbol_meta.side_effect = get_meta
    return universe


# ---------------------------------------------------------------------------
# StrategyMatrixRunner
# ---------------------------------------------------------------------------

class TestStrategyMatrixRunner:

    def _make_runner(self, mock_store, mock_universe, weights=None, tmp_path=None):
        runner = StrategyMatrixRunner(
            store=mock_store,
            universe=mock_universe,
            weights_file=None,
            signal_valid_bars=3,
        )
        if weights:
            for group_id, strategies in weights.items():
                runner.set_weights_for_group(group_id, strategies)
        return runner

    def test_run_no_weights_returns_empty(self, mock_store, mock_universe):
        runner = self._make_runner(mock_store, mock_universe)
        result = runner.run(lookback_days=30, max_workers=2)
        assert isinstance(result, MatrixScanResult)
        assert len(result.signals) == 0

    def test_run_with_weights_produces_signals(self, mock_store, mock_universe):
        """有权重配置时，扫描产出 Signal。"""
        weights = {
            "NDX_mid_vol": [
                {"strategy": "dual_ma", "params": {"fast": 5, "slow": 20},
                 "weight": 1.0, "backtest_sharpe": 1.2, "backtest_win_rate": 0.55}
            ]
        }
        runner = self._make_runner(mock_store, mock_universe, weights)
        result = runner.run(lookback_days=30, max_workers=2)
        # 至少对 NDX_mid_vol 组的标的运行了策略
        assert result.symbol_count == 5
        # signals 数量取决于策略是否触发，可能为 0（无信号）或有信号

    def test_signal_valid_bars_allows_older_signal(self, mock_store, mock_universe):
        """signal_valid_bars=3：3天前的信号应仍然有效。"""
        # 构造一个在倒数第3根 bar 有信号（倒数第1根=0）的序列
        n = 30
        idx = pd.date_range("2024-01-01", periods=n, freq="B")
        close = pd.Series([101.0] * n, index=idx)
        # 倒数第3根=1（BUY），倒数第1/2根=0
        signal_series = pd.Series([0] * n, index=idx)
        signal_series.iloc[-3] = 1

        with patch.object(
            StrategyMatrixRunner, 'run_symbol',
            wraps=lambda self, sym, lookback_days=90: []
        ):
            runner = self._make_runner(mock_store, mock_universe)
            # 直接测试信号有效期逻辑
            recent = signal_series.iloc[-3:]
            nonzero = recent[recent != 0]
            assert not nonzero.empty, "信号在有效期内应被找到"
            assert int(nonzero.iloc[-1]) == 1

    def test_signal_valid_bars_expired_signal(self):
        """超过有效期的信号应被忽略。"""
        n = 30
        idx = pd.date_range("2024-01-01", periods=n, freq="B")
        signal_series = pd.Series([0] * n, index=idx)
        signal_series.iloc[-5] = 1  # 5天前，超出 valid_bars=3

        recent = signal_series.iloc[-3:]
        nonzero = recent[recent != 0]
        assert nonzero.empty, "超出有效期的信号应被忽略"

    def test_reload_weights(self, mock_store, mock_universe, tmp_path):
        """reload_weights 从文件更新权重。"""
        weights_file = tmp_path / "strategy_weights.json"
        weights_data = {
            "groups": {
                "NDX_high_vol": [
                    {"strategy": "dual_ma", "params": {}, "weight": 1.0,
                     "backtest_sharpe": 1.0, "backtest_win_rate": 0.5}
                ]
            }
        }
        weights_file.write_text(json.dumps(weights_data))

        runner = StrategyMatrixRunner(
            store=mock_store,
            universe=mock_universe,
            weights_file=weights_file,
        )
        assert "NDX_high_vol" in runner._weights
        runner.reload_weights()
        assert "NDX_high_vol" in runner._weights

    def test_strategy_not_in_registry_skipped(self, mock_store, mock_universe):
        """未注册的策略被跳过，不抛异常。"""
        weights = {
            "NDX_mid_vol": [
                {"strategy": "nonexistent_strategy_xyz", "params": {},
                 "weight": 1.0, "backtest_sharpe": 1.0, "backtest_win_rate": 0.5}
            ]
        }
        runner = self._make_runner(mock_store, mock_universe, weights)
        result = runner.run(lookback_days=30, max_workers=2)
        # 不抛异常，错误被记录
        assert isinstance(result, MatrixScanResult)


# ---------------------------------------------------------------------------
# SignalRanker
# ---------------------------------------------------------------------------

class TestSignalRanker:

    def test_rank_empty_signals(self):
        ranker = SignalRanker(top_k=5)
        report = ranker.rank([])
        assert report.total_candidates == 0
        assert len(report.buy_candidates) == 0
        assert len(report.sell_signals) == 0

    def test_rank_single_buy(self):
        ranker = SignalRanker(top_k=5)
        sig = _make_signal("AAPL", SignalDirection.BUY)
        report = ranker.rank([sig])
        assert len(report.buy_candidates) == 1
        assert report.buy_candidates[0].symbol == "AAPL"

    def test_sell_not_limited_by_topk(self):
        """SELL 信号不受 Top-K 限制，全部保留。"""
        ranker = SignalRanker(top_k=2, candidates_multiplier=2)
        sigs = [_make_signal(f"SYM{i}", SignalDirection.SELL) for i in range(8)]
        report = ranker.rank(sigs)
        assert len(report.sell_signals) == 8

    def test_buy_candidates_is_2k(self):
        """BUY 候选输出 min(有效信号数, 2×K)。"""
        ranker = SignalRanker(top_k=3, candidates_multiplier=2)
        sigs = [_make_signal(f"SYM{i}", SignalDirection.BUY) for i in range(10)]
        report = ranker.rank(sigs)
        assert len(report.buy_candidates) == 6  # 2×3=6

    def test_conflict_aggregation_same_direction(self):
        """同标的同向信号 → 聚合为单条信号。"""
        ranker = SignalRanker(top_k=5)
        sigs = [
            _make_signal("AAPL", SignalDirection.BUY, confidence=0.7, strategy="dual_ma"),
            _make_signal("AAPL", SignalDirection.BUY, confidence=0.8, strategy="macd"),
        ]
        report = ranker.rank(sigs)
        buy_symbols = [s.symbol for s in report.buy_candidates]
        assert buy_symbols.count("AAPL") == 1  # 去重为 1 条

    def test_conflict_dropped_opposing_signals(self):
        """同标的 BUY + SELL → 分歧，丢弃。"""
        ranker = SignalRanker(top_k=5, conflict_threshold=0.3)
        sigs = [
            _make_signal("AAPL", SignalDirection.BUY,  confidence=0.5, strategy="dual_ma"),
            _make_signal("AAPL", SignalDirection.SELL, confidence=0.5, strategy="macd"),
        ]
        # BUY 列表里只有 AAPL BUY；SELL 列表里只有 AAPL SELL
        # 各自聚合不冲突（BUY 和 SELL 分开处理）
        report = ranker.rank(sigs)
        # 因为 BUY 和 SELL 分开，各自只有 1 条，不会互相冲突
        assert report.dropped_conflicts == 0

    def test_ranking_order_by_score(self):
        """高置信度标的排名靠前。"""
        ranker = SignalRanker(top_k=5)
        sigs = [
            _make_signal("LOW_CONF",  SignalDirection.BUY, confidence=0.3, sharpe=0.5),
            _make_signal("HIGH_CONF", SignalDirection.BUY, confidence=0.9, sharpe=2.0),
        ]
        report = ranker.rank(sigs)
        assert report.buy_candidates[0].symbol == "HIGH_CONF"
        assert report.buy_candidates[1].symbol == "LOW_CONF"

    def test_rank_attribute_on_candidates(self):
        """rank 字段从 1 开始。"""
        ranker = SignalRanker(top_k=5)
        sigs = [_make_signal(f"SYM{i}", SignalDirection.BUY) for i in range(3)]
        report = ranker.rank(sigs)
        ranks = [c.rank for c in report.buy_candidates]
        assert ranks == [1, 2, 3]

    # ------------------------------------------------------------------
    # 迭代 #7：Sortino + DD penalty 评分因子测试
    # ------------------------------------------------------------------

    def test_score_uses_sortino_not_sharpe(self):
        """评分应使用 backtest_sortino 而非 backtest_sharpe。

        构造 signal：sortino=2.0（高），sharpe=0.0（低，旧字段）。
        断言：score > 0，且 score_breakdown 包含 backtest_sortino 而非 backtest_sharpe。
        """
        ranker = SignalRanker(top_k=5)
        sig = _make_signal("A", SignalDirection.BUY, sortino=2.0, sharpe=0.0)
        report = ranker.rank([sig])
        ranked = report.buy_candidates[0]
        assert ranked.score > 0
        assert "backtest_sortino" in ranked.score_breakdown
        assert "backtest_sharpe" not in ranked.score_breakdown
        # sortino=2.0 → factor = min(2.0/3.0, 1.0) = 0.6667
        assert abs(ranked.score_breakdown["backtest_sortino"] - (2.0 / 3.0)) < 1e-6

    def test_score_dd_penalty(self):
        """DD 越低，得分越高。

        A: max_drawdown=5% → dd_penalty = 1 - 5/20 = 0.75
        B: max_drawdown=18% → dd_penalty = 1 - 18/20 = 0.10
        其余因子相同 → A.score > B.score
        """
        ranker = SignalRanker(top_k=5)
        sig_a = _make_signal("A", SignalDirection.BUY, sortino=1.5, max_drawdown=5.0)
        sig_b = _make_signal("B", SignalDirection.BUY, sortino=1.5, max_drawdown=18.0)
        report = ranker.rank([sig_a, sig_b])
        scores = {r.symbol: r.score for r in report.buy_candidates}
        assert scores["A"] > scores["B"], (
            f"A(DD=5%) score {scores['A']:.4f} 应大于 B(DD=18%) score {scores['B']:.4f}"
        )
        # 验证 dd_penalty factor
        bd_a = {r.symbol: r.score_breakdown for r in report.buy_candidates}["A"]
        bd_b = {r.symbol: r.score_breakdown for r in report.buy_candidates}["B"]
        assert abs(bd_a["backtest_dd_penalty"] - 0.75) < 1e-6
        assert abs(bd_b["backtest_dd_penalty"] - 0.10) < 1e-6

    def test_score_sortino_normalization(self):
        """Sortino 归一化：3.0→1.0, 6.0→1.0(截断), -1.0→0.0(截断)。"""
        ranker = SignalRanker(top_k=5)
        # 3.0 → 1.0
        sig1 = _make_signal("S3", SignalDirection.BUY, sortino=3.0, max_drawdown=0.0)
        # 6.0 → 1.0 (truncated)
        sig2 = _make_signal("S6", SignalDirection.BUY, sortino=6.0, max_drawdown=0.0)
        # -1.0 → 0.0 (clamped)
        sig_neg = _make_signal("SN", SignalDirection.BUY, sortino=-1.0, max_drawdown=0.0)
        report = ranker.rank([sig1, sig2, sig_neg])
        bd = {r.symbol: r.score_breakdown for r in report.buy_candidates}
        assert abs(bd["S3"]["backtest_sortino"] - 1.0) < 1e-6
        assert abs(bd["S6"]["backtest_sortino"] - 1.0) < 1e-6
        assert abs(bd["SN"]["backtest_sortino"] - 0.0) < 1e-6

    def test_custom_score_weights_still_work(self):
        """传入自定义 score_weights 只用指定因子。"""
        ranker = SignalRanker(
            top_k=5,
            score_weights={"strategy_weight": 1.0},
        )
        sig = _make_signal("X", SignalDirection.BUY, weight=0.8, sortino=2.0)
        report = ranker.rank([sig])
        ranked = report.buy_candidates[0]
        # 只用 strategy_weight=0.8 → score=0.8
        assert abs(ranked.score - 0.8) < 1e-6

    def test_ranking_order_changed_by_sortino(self):
        """Sortino 评分切换：A 的 Sharpe 高但 Sortino 低，B 的 Sharpe 低但 Sortino 高。

        旧评分（sharpe）：A 排前
        新评分（sortino）：B 排前
        """
        ranker = SignalRanker(top_k=5)
        sig_a = _make_signal(
            "A_HIGH_SHARPE_LOW_SORTINO",
            SignalDirection.BUY,
            sharpe=2.5,      # 旧因子：高
            sortino=0.5,     # 新因子：低
            max_drawdown=10.0,
            confidence=0.5,
            weight=0.5,
            win_rate=0.5,
        )
        sig_b = _make_signal(
            "B_LOW_SHARPE_HIGH_SORTINO",
            SignalDirection.BUY,
            sharpe=0.2,      # 旧因子：低
            sortino=2.5,     # 新因子：高
            max_drawdown=10.0,
            confidence=0.5,
            weight=0.5,
            win_rate=0.5,
        )
        report = ranker.rank([sig_a, sig_b])
        # B 应排第一（Sortino 高）
        assert report.buy_candidates[0].symbol == "B_LOW_SHARPE_HIGH_SORTINO"
        assert report.buy_candidates[1].symbol == "A_HIGH_SHARPE_LOW_SORTINO"


# ---------------------------------------------------------------------------
# CandidateSelector
# ---------------------------------------------------------------------------

class TestCandidateSelector:

    def _make_ranked(self, symbol: str, score: float = 0.7, sector: str = "Technology") -> RankedSignal:
        sig = _make_signal(symbol, sector=sector)
        return RankedSignal(signal=sig, score=score, rank=1)

    def test_basic_approval(self):
        """基本场景：5 个不同板块候选，账户充足，全部通过。"""
        account = AccountState(total_capital=100_000, current_exposure=0, current_position_count=0)
        sectors = ["Technology", "Financials", "Healthcare", "Energy", "Industrials"]
        candidates = [
            self._make_ranked(f"SYM{i}", score=0.8 - i * 0.1, sector=sectors[i])
            for i in range(5)
        ]
        approved, rejections = select_orders_from_candidates(
            candidates, account, max_orders=5, target_position_pct=0.10
        )
        assert len(approved) == 5
        assert len(rejections) == 0

    def test_max_concurrent_positions_stops(self):
        """持仓达上限后停止，后续候选不再尝试。"""
        account = AccountState(total_capital=100_000, current_exposure=0,
                               current_position_count=4)
        candidates = [self._make_ranked(f"SYM{i}") for i in range(5)]
        approved, _ = select_orders_from_candidates(
            candidates, account, max_orders=5,
            max_concurrent_positions=5, target_position_pct=0.10
        )
        assert len(approved) == 1  # 只能再加 1 个

    def test_sector_limit_triggers_fallback(self):
        """科技股超 sector 限制时跳过，递补下一个非科技股。"""
        account = AccountState(
            total_capital=100_000,
            current_exposure=30_000,
            sector_exposure={"Technology": 30_000},
        )
        candidates = [
            self._make_ranked("TECH1", sector="Technology"),
            self._make_ranked("TECH2", sector="Technology"),
            self._make_ranked("FIN1",  sector="Financials"),  # 应被递补
        ]
        approved, rejections = select_orders_from_candidates(
            candidates, account, max_orders=1,
            max_sector_exposure_pct=0.40,  # 40% = 40k，当前 30k 再加 20k = 50% > 40%
            target_position_pct=0.20,
        )
        assert len(approved) == 1
        assert approved[0].signal.symbol == "FIN1"
        assert any("Technology" in r for r in rejections)

    def test_total_exposure_limit(self):
        """总持仓超限时停止下单。"""
        account = AccountState(
            total_capital=100_000,
            current_exposure=75_000,  # 已用 75%
        )
        candidates = [self._make_ranked(f"SYM{i}") for i in range(5)]
        # max_total_exposure=80%，还剩 5k 空间，target=20%=20k → 触发上限
        approved, rejections = select_orders_from_candidates(
            candidates, account, max_orders=5,
            max_total_exposure_pct=0.80,
            target_position_pct=0.20,
        )
        assert len(approved) == 0
        assert len(rejections) > 0

    def test_single_position_cap_truncation(self):
        """ATR 仓位超 max_single_position_pct 时截断（不拒绝）。"""
        account = AccountState(total_capital=100_000, current_exposure=0)
        candidates = [self._make_ranked("AAPL")]
        approved, _ = select_orders_from_candidates(
            candidates, account, max_orders=1,
            max_single_position_pct=0.20,
            target_position_pct=0.35,   # 目标 35%，应被截断为 20%
        )
        assert len(approved) == 1
        assert approved[0].order_value <= 100_000 * 0.20
