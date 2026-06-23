"""SignalRanker — 信号排名与选股。

职责：
    1. 接收 StrategyMatrixRunner 输出的 M×N 条 Signal
    2. 同标的多策略冲突聚合（加权投票）
    3. 按综合得分排名
    4. 输出 Top-2K 候选（供 Risk Manager 递补，而非直接输出 Top-K）
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from loguru import logger

from mytrader.strategy.base import Signal, SignalDirection


# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------

@dataclass
class RankedSignal:
    """排名后的聚合信号。"""

    signal: Signal
    score: float
    rank: int
    score_breakdown: dict[str, float] = field(default_factory=dict)

    @property
    def symbol(self) -> str:
        return self.signal.symbol

    @property
    def direction(self) -> SignalDirection:
        return self.signal.direction


@dataclass
class RankingReport:
    """SignalRanker.rank() 的完整输出。"""

    total_candidates: int = 0         # 聚合前原始信号数
    after_aggregation: int = 0        # 聚合后候选数（去冲突后）
    buy_candidates: list[RankedSignal] = field(default_factory=list)    # Top-2K BUY
    sell_signals: list[RankedSignal] = field(default_factory=list)      # 全部 SELL（不受 K 限制）
    dropped_conflicts: int = 0        # 因策略分歧丢弃的标的数

    @property
    def top_k(self) -> list[RankedSignal]:
        """兼容旧调用：返回 buy_candidates（已是 Top-2K）。"""
        return self.buy_candidates


# ---------------------------------------------------------------------------
# SignalRanker
# ---------------------------------------------------------------------------

class SignalRanker:
    """信号聚合 + 排名 + Top-2K 选取。

    Args:
        top_k:              最终目标持仓数（输出 2×top_k 候选供递补）
        candidates_multiplier: 候选倍数，默认 2
        conflict_threshold: 加权投票分数绝对值低于此阈值时丢弃（策略分歧）
        score_weights:      综合得分各因子权重 dict
    """

    DEFAULT_SCORE_WEIGHTS = {
        "strategy_weight":    0.35,
        "signal_confidence":  0.25,
        "backtest_win_rate":  0.20,
        "backtest_sharpe":    0.20,
    }

    def __init__(
        self,
        top_k: int = 5,
        candidates_multiplier: int = 2,
        conflict_threshold: float = 0.3,
        score_weights: dict[str, float] | None = None,
    ) -> None:
        self._top_k = top_k
        self._candidates_multiplier = candidates_multiplier
        self._conflict_threshold = conflict_threshold
        self._score_weights = score_weights or self.DEFAULT_SCORE_WEIGHTS

    # ------------------------------------------------------------------
    # 公共接口
    # ------------------------------------------------------------------

    def rank(self, signals: list[Signal]) -> RankingReport:
        """聚合 → 评分 → 排名 → 输出 Top-2K BUY + 全部 SELL。"""
        report = RankingReport(total_candidates=len(signals))

        # 1. 按方向分拣：先分离 SELL（优先处理）
        buy_sigs = [s for s in signals if s.direction == SignalDirection.BUY]
        sell_sigs = [s for s in signals if s.direction == SignalDirection.SELL]

        # 2. 同标的聚合（BUY 和 SELL 各自独立聚合）
        buy_agg, buy_dropped = self._aggregate_by_symbol(buy_sigs)
        sell_agg, sell_dropped = self._aggregate_by_symbol(sell_sigs)
        report.dropped_conflicts = buy_dropped + sell_dropped
        report.after_aggregation = len(buy_agg) + len(sell_agg)

        # 3. 评分
        buy_scored = [(sig, *self._score(sig)) for sig in buy_agg]
        sell_scored = [(sig, *self._score(sig)) for sig in sell_agg]

        # 4. 排名 + Top-2K（BUY）；SELL 全部保留
        buy_scored.sort(key=lambda x: x[1], reverse=True)
        sell_scored.sort(key=lambda x: x[1], reverse=True)

        max_buy_candidates = self._top_k * self._candidates_multiplier
        report.buy_candidates = [
            RankedSignal(signal=s, score=sc, rank=i + 1, score_breakdown=bd)
            for i, (s, sc, bd) in enumerate(buy_scored[:max_buy_candidates])
        ]
        report.sell_signals = [
            RankedSignal(signal=s, score=sc, rank=i + 1, score_breakdown=bd)
            for i, (s, sc, bd) in enumerate(sell_scored)
        ]

        logger.debug(
            f"[ranker] total={report.total_candidates}, "
            f"buy_candidates={len(report.buy_candidates)}, "
            f"sell={len(report.sell_signals)}, "
            f"dropped={report.dropped_conflicts}"
        )
        return report

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _aggregate_by_symbol(
        self, signals: list[Signal]
    ) -> tuple[list[Signal], int]:
        """同标的多策略聚合（加权投票 / 冲突解决）。

        Returns:
            (aggregated_signals, dropped_count)
        """
        from collections import defaultdict

        by_symbol: dict[str, list[Signal]] = defaultdict(list)
        for sig in signals:
            by_symbol[sig.symbol].append(sig)

        aggregated: list[Signal] = []
        dropped = 0

        for sym, sigs in by_symbol.items():
            if len(sigs) == 1:
                aggregated.append(sigs[0])
                continue

            # 加权投票：direction=BUY→+1，SELL→-1
            combined = 0.0
            total_weight = 0.0
            for s in sigs:
                d = 1.0 if s.direction == SignalDirection.BUY else -1.0
                w = s.confidence
                combined += d * w
                total_weight += w

            if total_weight > 0:
                combined /= total_weight

            if abs(combined) < self._conflict_threshold:
                dropped += 1
                logger.debug(f"[ranker] {sym}: conflict dropped (score={combined:.2f})")
                continue

            # 合并为单一信号
            direction = SignalDirection.BUY if combined > 0 else SignalDirection.SELL
            # 取置信度最高的信号作为代表，更新方向
            best = max(sigs, key=lambda s: s.confidence)
            merged = Signal(
                symbol=sym,
                direction=direction,
                timestamp=best.timestamp,
                confidence=abs(combined),
                strategy_name="+".join(s.strategy_name for s in sigs),
                indicators={**best.indicators, "combined_score": combined},
                price_hint=best.price_hint,
            )
            aggregated.append(merged)

        return aggregated, dropped

    def _score(self, signal: Signal) -> tuple[float, dict[str, float]]:
        """计算综合得分 + 各因子明细。"""
        ind = signal.indicators
        factors = {
            "strategy_weight":   float(ind.get("weight", 0.5)),
            "signal_confidence": float(signal.confidence),
            "backtest_win_rate": float(ind.get("backtest_win_rate", 0.5)),
            "backtest_sharpe":   min(float(ind.get("backtest_sharpe", 0.0)) / 3.0, 1.0),
        }

        w = self._score_weights
        score = sum(w.get(k, 0.0) * v for k, v in factors.items())
        return score, factors
