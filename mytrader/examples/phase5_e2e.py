"""Phase 5 端到端干跑验证脚本。

模拟一个完整的每日扫描流程（paper mode，不真实下单）：
    1. 初始化 MarketDataStore + UniverseManager
    2. 重算波动率分组
    3. 加载 strategy_weights.json（若存在），或使用内置默认权重
    4. StrategyMatrixRunner 扫描全标的
    5. SignalRanker 聚合 + Top-2K 排名
    6. CandidateSelector 递补选出 Top-5

用法：
    cd mytrader/
    /Users/rickouyang/miniforge3/envs/py312trade/bin/python examples/phase5_e2e.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# 确保 mytrader 包在路径中
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger


def main() -> None:
    logger.info("=" * 60)
    logger.info("Phase 5 端到端干跑验证（paper mode）")
    logger.info("=" * 60)

    # ------------------------------------------------------------------
    # 1. 初始化本地数据库
    # ------------------------------------------------------------------
    from mytrader.data.store import MarketDataStore
    store = MarketDataStore()
    logger.info(f"[store] db={store._db_path}")

    # ------------------------------------------------------------------
    # 2. 初始化标的池管理器
    # ------------------------------------------------------------------
    from mytrader.universe.manager import UniverseManager
    universe = UniverseManager(store=store)
    syms = universe.get_universe()
    logger.info(f"[universe] {len(syms)} symbols loaded")

    # 重算波动率分组（需要本地有数据，否则全为 unknown）
    universe.recompute_volatility_tiers(max_workers=4)
    groups = universe.get_groups()
    logger.info(f"[universe] {len(groups)} groups after vol recompute:")
    for gid, members in sorted(groups.items()):
        logger.info(f"  {gid}: {len(members)} symbols")

    # ------------------------------------------------------------------
    # 3. 注入默认权重（若无 strategy_weights.json）
    # ------------------------------------------------------------------
    from mytrader.strategy.matrix_runner import StrategyMatrixRunner

    weights_file = Path("config/strategy_weights.json")
    runner = StrategyMatrixRunner(
        store=store,
        universe=universe,
        weights_file=weights_file if weights_file.exists() else None,
        signal_valid_bars=3,
    )

    if not weights_file.exists():
        logger.warning(
            "[runner] strategy_weights.json not found, injecting default weights for demo"
        )
        # 向所有分组注入默认权重（演示用）
        default_strategies = [
            {"strategy": "dual_ma",  "params": {"fast": 5, "slow": 60},
             "weight": 0.6, "backtest_sharpe": 1.2, "backtest_win_rate": 0.55},
            {"strategy": "macd",     "params": {"fast": 12, "slow": 26, "signal_period": 9},
             "weight": 0.4, "backtest_sharpe": 1.0, "backtest_win_rate": 0.52},
        ]
        for gid in groups:
            runner.set_weights_for_group(gid, default_strategies)
        logger.info(f"[runner] default weights injected for {len(groups)} groups")

    # ------------------------------------------------------------------
    # 4. 矩阵扫描
    # ------------------------------------------------------------------
    logger.info("[scan] starting StrategyMatrixRunner.run()...")
    scan_result = runner.run(lookback_days=90, max_workers=4)
    logger.info(
        f"[scan] done: {scan_result.symbol_count} symbols scanned, "
        f"{len(scan_result.signals)} signals, "
        f"{len(scan_result.buy_signals)} BUY, "
        f"{len(scan_result.sell_signals)} SELL, "
        f"errors={len(scan_result.errors)}"
    )

    if not scan_result.signals:
        logger.info("[scan] no signals today (normal if local DB is empty)")
        logger.info("Hint: run 'python main.py --backfill' to populate the local DB first")
        return

    # ------------------------------------------------------------------
    # 5. 信号排名
    # ------------------------------------------------------------------
    from mytrader.signal.ranker import SignalRanker
    ranker = SignalRanker(top_k=5, candidates_multiplier=2)
    ranking = ranker.rank(scan_result.signals)

    logger.info(
        f"[ranker] {ranking.total_candidates} signals → "
        f"{ranking.after_aggregation} aggregated → "
        f"{len(ranking.buy_candidates)} BUY candidates, "
        f"{len(ranking.sell_signals)} SELL, "
        f"dropped={ranking.dropped_conflicts}"
    )

    logger.info("[ranker] Top BUY candidates:")
    for rc in ranking.buy_candidates[:10]:
        logger.info(
            f"  #{rc.rank} {rc.symbol:8s} | score={rc.score:.3f} | "
            f"dir={rc.direction.value} | breakdown={rc.score_breakdown}"
        )

    # ------------------------------------------------------------------
    # 6. Risk Manager 递补选出 Top-5
    # ------------------------------------------------------------------
    from mytrader.risk.candidate_selector import AccountState, select_orders_from_candidates

    account = AccountState(
        total_capital=100_000,
        current_exposure=0.0,
        current_position_count=0,
    )
    approved, rejections = select_orders_from_candidates(
        candidates=ranking.buy_candidates,
        account=account,
        max_orders=5,
        target_position_pct=0.20,
    )

    logger.info(f"[risk] approved {len(approved)} orders (from {len(ranking.buy_candidates)} candidates):")
    for order in approved:
        logger.info(f"  {order.signal.symbol:8s} | order_value=${order.order_value:,.0f}")

    if rejections:
        logger.info(f"[risk] {len(rejections)} candidates rejected:")
        for r in rejections:
            logger.info(f"  {r}")

    # ------------------------------------------------------------------
    # 总结
    # ------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info(
        f"Phase 5 E2E 干跑完成：扫描 {scan_result.symbol_count} 只 → "
        f"产生 {len(scan_result.signals)} 信号 → "
        f"排名后 {len(ranking.buy_candidates)} BUY 候选 → "
        f"风控通过 {len(approved)} 个订单"
    )
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
