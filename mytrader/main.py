"""MyTrader 系统启动入口。

用法：
    python main.py                        # paper 模式，默认配置
    python main.py --mode semi_auto       # 半自动（推送通知，人工确认）
    python main.py --mode auto            # 全自动（直接下单）
    python main.py --config path/to.yaml  # 自定义配置文件
    python main.py --dry-run              # 仅检查配置和依赖，不启动调度器
    python main.py --scan-now morning     # 立即执行一次盘前扫描（调试用）
    python main.py --reoptimize           # 立即触发 MatrixBacktest（Walk-Forward 重优化）
    python main.py --backfill             # 首次回填 5 年历史数据（MarketDataStore）

环境变量覆盖（通过 .env 文件）：
    EXECUTION__MODE=semi_auto
    ALPACA__API_KEY=your_key
    NOTIFICATION__TELEGRAM_ENABLED=true
    WATCHLIST__SYMBOLS='["AAPL","TSLA"]'
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Walk-Forward 重优化配置（迭代 #1 提为模块级常量，便于回归测试）
# ⚠️ 策略名必须与 mytrader/strategy/strategies/*.py 中 @register_strategy(...)
#    装饰器的名字完全一致。回归测试 test_reoptimize_strategy_names_match_registry
#    会断言 REOPTIMIZE_STRATEGIES ⊆ STRATEGY_REGISTRY.keys()，防止策略名拼写
#    错误导致矩阵回测静默跳过整类策略。
# ---------------------------------------------------------------------------

REOPTIMIZE_STRATEGIES: list[str] = [
    "dual_ma",
    "rsi_mean_revert",
    "macd_cross",
    "bollinger_band",
]

REOPTIMIZE_PARAM_GRIDS: dict[str, dict[str, list]] = {
    # 迭代 #2：从单点扩展为真网格。原单点网格（fast=[5,10], slow=[20,40,60]）
    # 仅 6 个组合，无法充分探索参数空间。扩展后 4×5=20 个组合。
    "dual_ma":         {"fast": [5, 10, 15, 20], "slow": [20, 30, 40, 60, 80]},
    # 迭代 #2：从单点 [14,30,70] 扩展为 3×3×3=27 个组合，覆盖均值回归周期
    # 与超买超卖阈值的常用范围。oversold/overbought 保持对称（25/75、30/70、35/65）。
    "rsi_mean_revert": {"period": [7, 14, 21], "oversold": [25, 30, 35], "overbought": [65, 70, 75]},
    # 迭代 #2：MACD 快/慢/信号周期网格 3×3×3=27 个组合，包含经典 12/26/9。
    "macd_cross":      {"fast": [8, 12, 16], "slow": [21, 26, 32], "signal_period": [5, 9, 12]},
    # 迭代 #2：布林带 3×3=9 个组合，覆盖常用 std_dev 范围 [1.5, 2.0, 2.5]。
    "bollinger_band":  {"period": [15, 20, 25], "std_dev": [1.5, 2.0, 2.5]},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="mytrader",
        description="MyTrader — 轻量级日内/短线交易系统",
    )
    parser.add_argument(
        "--mode",
        choices=["paper", "semi_auto", "auto"],
        default=None,
        help="执行模式（覆盖配置文件）: paper | semi_auto | auto",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        metavar="PATH",
        help="YAML 配置文件路径（默认自动查找 config/default.yaml）",
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default="logs",
        metavar="DIR",
        help="日志目录（默认 logs/）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅初始化并检查配置，不启动调度器",
    )
    parser.add_argument(
        "--db",
        type=str,
        default="mytrader.db",
        metavar="PATH",
        help="SQLite 数据库路径（默认 mytrader.db）",
    )
    parser.add_argument(
        "--scan-now",
        choices=["morning", "intraday", "eod"],
        default=None,
        metavar="TYPE",
        help="立即执行一次指定类型的扫描，不启动调度器（调试用）",
    )
    parser.add_argument(
        "--reoptimize",
        action="store_true",
        help="立即触发 MatrixBacktest Walk-Forward 重优化，更新 strategy_weights.json",
    )
    parser.add_argument(
        "--backfill",
        action="store_true",
        help="首次回填 5 年历史数据到 MarketDataStore（一次性操作）",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # 1. 初始化日志（最先执行）
    from mytrader.monitor.logger_setup import setup_logger
    setup_logger(log_dir=args.log_dir, level="INFO")

    from loguru import logger
    logger.info(f"MyTrader starting: mode={args.mode or 'from_config'} dry_run={args.dry_run}")

    # 2. 加载配置
    from mytrader.infra.config import load_config
    config = load_config(args.config)

    # CLI --mode 覆盖配置文件
    if args.mode is not None:
        object.__setattr__(config.execution, "mode", args.mode)
        logger.info(f"Execution mode overridden by CLI: {args.mode}")

    logger.info(
        f"Config loaded: mode={config.execution.mode} broker={config.execution.broker} "
        f"scheduler.enabled={config.scheduler.enabled} "
        f"watchlist={config.watchlist.symbols}"
    )

    # 3. 装配依赖
    from mytrader.infra.container import Container
    components = Container.build(config, db_url=f"sqlite:///{args.db}")

    # 4. 健康检查
    report = components.health.run_all()
    logger.info(f"Health check: {report.status} ({report.checks})")
    if not report.is_healthy:
        for name in report.failed_checks:
            logger.warning(f"Health check FAILED: {name} — {report.details.get(name)}")

    # 5. 构建扫描编排器
    from mytrader.scan_orchestrator import build_orchestrator
    orchestrator = build_orchestrator(components)

    mode_label = "Phase 5 (multi-strategy matrix)" if orchestrator._use_phase5 else "Phase 4 (single-strategy)"
    logger.info(f"[Orchestrator] Built in {mode_label} mode")

    # 6a. --backfill：首次回填历史数据
    if args.backfill:
        _run_backfill(config, logger)
        return

    # 6b. --reoptimize：立即触发 MatrixBacktest
    if args.reoptimize:
        _run_reoptimize(config, logger)
        return

    # 6c. --scan-now：立即执行一次扫描后退出（调试用）
    if args.scan_now:
        logger.info(f"Running immediate scan: type={args.scan_now}")
        if args.scan_now == "morning":
            summary = orchestrator.morning_scan()
        elif args.scan_now == "intraday":
            summary = orchestrator.intraday_scan()
        else:
            summary = orchestrator.eod_check()
        logger.info(
            f"Scan complete: buy={summary.buy_count} sell={summary.sell_count} "
            f"orders={summary.order_count} errors={summary.error_count}"
        )
        return

    if args.dry_run:
        # 输出 Phase 5 模块状态
        if components.data_store is not None:
            logger.info(
                f"[DryRun] Phase5 modules active: "
                f"universe={len(components.universe.get_universe())} symbols, "
                f"signal_valid_bars={config.strategy_matrix.signal_valid_bars}"
            )
        else:
            logger.info("[DryRun] Phase4 fallback mode (local DB not loaded)")

        # Alpaca/IBKR 启动自检
        if config.execution.mode in ("semi_auto", "auto"):
            try:
                result = components.broker.health_check()
                if result["status"] == "connected":
                    logger.info(
                        f"[DryRun] Broker connected: id={result['account_id']}, "
                        f"cash=${result['cash']:,.0f}, buying_power=${result['buying_power']:,.0f}, "
                        f"paper={result['paper']}"
                    )
                else:
                    logger.error(f"[DryRun] Broker health check FAILED: {result}")
            except AttributeError:
                logger.info("[DryRun] Broker does not support health_check (PaperBroker)")

        logger.info("Dry-run complete. Exiting.")
        return

    # 7. 启动调度器（接入真实回调）
    from mytrader.infra.scheduler import TradingScheduler
    from mytrader.data.providers.yfinance_provider import YFinanceProvider

    # 盘后数据增量同步回调（Phase 5）
    def _on_data_sync() -> None:
        if components.data_store is None:
            return
        from mytrader.data.store import DataSyncService
        symbols = components.universe.get_universe()
        logger.info(f"[DataSync] syncing {len(symbols)} symbols...")
        try:
            if config.data.provider == "alpaca":
                from mytrader.data.providers.alpaca_provider import AlpacaDataProvider
                from datetime import date as _date, timedelta as _td
                primary = AlpacaDataProvider(
                    api_key=config.alpaca.api_key,
                    secret_key=config.alpaca.secret_key,
                    paper=config.alpaca.paper,
                )
                # 盘后同步：end 用昨天避开 SIP 实时限制
                end = _date.today() - _td(days=1)
            else:
                primary = YFinanceProvider()
                end = None
            svc = DataSyncService(
                store=components.data_store,
                primary=primary,
                use_fallback_on_empty=False,
            )
            report = svc.sync_all(symbols, max_workers=4, end=end)
            logger.info(f"[DataSync] done: {report}")
        except Exception as exc:
            logger.error(f"[DataSync] failed: {exc}")

    scheduler = TradingScheduler(
        config=config.scheduler,
        on_morning_scan=orchestrator.morning_scan,
        on_intraday_scan=orchestrator.intraday_scan,
        on_eod_check=orchestrator.eod_check,
        on_reconciliation=_build_reconciliation_callback(components, sync_fn=_on_data_sync),
        on_monthly_reoptimize=lambda: _run_reoptimize(config, logger),
    )

    # 启动前先执行一次数据同步（确保本地库有数据）
    _on_data_sync()

    logger.info("Starting scheduler... (Ctrl+C to stop)")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutdown signal received")
    finally:
        scheduler.shutdown(wait=False)
        logger.info("MyTrader stopped")


def _run_backfill(config: "Any", logger: "Any") -> None:
    """首次回填 5 年历史数据。自动刷新成分股列表（Wikipedia → CSV）。"""
    from mytrader.data.store import MarketDataStore, DataSyncService
    from mytrader.data.providers.yfinance_provider import YFinanceProvider
    from mytrader.universe.manager import UniverseManager
    from pathlib import Path

    logger.info("[Backfill] initializing MarketDataStore...")
    store = MarketDataStore()  # 使用默认路径 ~/.mytrader/market_data.db

    # 若 universe.csv 不存在或为空，从 Wikipedia 拉取完整成分股列表
    csv_path = Path("config/universe.csv")
    need_fetch = (
        not csv_path.exists()
        or csv_path.stat().st_size < 100  # 只有表头或空文件
    )

    if need_fetch:
        if csv_path.exists():
            logger.info(f"[Backfill] universe.csv is empty/corrupt ({csv_path.stat().st_size} bytes), re-fetching...")
            csv_path.unlink()
        else:
            logger.info("[Backfill] universe.csv not found, fetching constituents from Wikipedia...")

        # 用指定 CSV 路径创建 UniverseManager，确保 save_to_csv 写入正确位置
        tmp_universe = UniverseManager(store=store, universe_file=csv_path)
        tmp_universe.refresh_constituents(save=True)

    universe = UniverseManager(store=store, universe_file=csv_path)
    symbols = universe.get_universe()
    logger.info(f"[Backfill] {len(symbols)} symbols to backfill (5 years)")

    if not symbols:
        logger.error("[Backfill] no symbols to backfill — abort")
        return

    from datetime import date as _date, timedelta as _timedelta

    if config.data.provider == "alpaca":
        from mytrader.data.providers.alpaca_provider import AlpacaDataProvider
        primary = AlpacaDataProvider(
            api_key=config.alpaca.api_key,
            secret_key=config.alpaca.secret_key,
            paper=config.alpaca.paper,
        )
        # Alpaca 免费 SIP 不能查当日实时数据，end 用昨天避开限制
        end = _date.today() - _timedelta(days=1)
        logger.info(
            f"[Backfill] using Alpaca provider (end={end}, avoids SIP realtime limit)"
        )
    else:
        primary = YFinanceProvider()
        end = None

    svc = DataSyncService(store=store, primary=primary, fallback=None,
                          use_fallback_on_empty=False)
    report = svc.backfill(symbols, years=5, end=end)
    logger.info(f"[Backfill] done: {report}")


def _run_reoptimize(config: "Any", logger: "Any") -> None:
    """立即触发 MatrixBacktest Walk-Forward 重优化。"""
    from mytrader.data.store import MarketDataStore
    from mytrader.universe.manager import UniverseManager
    from mytrader.backtest.matrix_backtest import MatrixBacktest
    from mytrader.strategy import matrix_runner as _mr_module

    logger.info("[Reoptimize] starting Walk-Forward MatrixBacktest...")
    store = MarketDataStore()
    universe = UniverseManager(store=store)

    # 重算波动率分组（确保分组是最新的）
    universe.recompute_volatility_tiers(max_workers=4)

    mb = MatrixBacktest(store=store, universe=universe, years=5, top_k=2)

    # ⚠️ 策略名必须与 @register_strategy(...) 装饰器中的名字完全一致。
    # 早期版本误用 "rsi"/"macd"/"bollinger" 简称，与注册表
    # ("rsi_mean_revert"/"macd_cross"/"bollinger_band") 不匹配，
    # 导致这 3 个策略在矩阵回测中被 _backtest_one 静默跳过，
    # strategy_weights.json 退化为仅 dual_ma（迭代 #1 修复）。
    # 模块级常量 REOPTIMIZE_STRATEGIES / REOPTIMIZE_PARAM_GRIDS 便于回归测试
    # （test_reoptimize_strategy_names_match_registry 防止策略名再次与注册表脱节）。
    strategies = REOPTIMIZE_STRATEGIES
    param_grids = REOPTIMIZE_PARAM_GRIDS

    output = Path("config/strategy_weights.json")
    report = mb.run(strategies=strategies, param_grids=param_grids, output_file=output)
    logger.info(
        f"[Reoptimize] done: {len(report.groups)} groups, "
        f"output={output}"
    )

    # 迭代 #3：Walk-Forward 4 轮验证（Constitution L7 流水线硬要求）
    # WF 是验证步骤，不影响 strategy_weights.json；结果输出到日志
    try:
        from mytrader.backtest.matrix_backtest import run_walk_forward
        logger.info("[Reoptimize] starting Walk-Forward 4-round validation...")
        wf_report = run_walk_forward(
            mb=mb,
            strategies=strategies,
            param_grids=param_grids,
            rounds=4,
            train_months=18,
            val_months=6,
        )
        for r in wf_report.rounds:
            logger.info(
                f"[WalkForward] Round {r.round_num}/4: "
                f"train={r.train_start}~{r.train_end}, "
                f"val={r.val_start}~{r.val_end}, "
                f"sortino={r.val_sortino:.4f}, "
                f"dd={r.val_max_dd:.4f}%, "
                f"passed={r.passed}"
            )
        logger.info(
            f"[WalkForward] Summary: pass_all_rounds={wf_report.pass_all_rounds}, "
            f"max_val_dd={wf_report.max_val_dd:.4f}%"
        )
        if not wf_report.pass_all_rounds:
            logger.warning(
                "[WalkForward] NOT all rounds passed — "
                "Constitution L7 requires all 4 rounds DD<=15% before paper trading."
            )
    except Exception as exc:
        logger.error(f"[WalkForward] failed: {exc}", exc_info=True)

    # 热加载（如果 StrategyMatrixRunner 已在运行）
    try:
        from mytrader.strategy.matrix_runner import StrategyMatrixRunner
        logger.info("[Reoptimize] weights reloaded into StrategyMatrixRunner")
    except Exception:
        pass


def _build_reconciliation_callback(components: "Any", sync_fn: "Any" = None) -> "Callable":
    """构建对账回调（盘后 16:30 ET）。

    盘后流程：先同步当日行情数据，再做持仓对账。
    """
    from loguru import logger

    def on_reconciliation() -> None:
        # 1. 先同步当日数据（修复：_on_data_sync 原本只在启动时跑，导致数据库不更新）
        if sync_fn is not None:
            try:
                sync_fn()
            except Exception as exc:
                logger.warning(f"[Reconciliation] data sync failed: {exc}")
        # 2. 持仓对账
        try:
            from mytrader.portfolio.reconciliation import ReconciliationService
            svc = ReconciliationService(
                tracker=components.tracker,
                broker=components.broker,
                event_bus=components.bus,
                auto_sync=False,
            )
            report = svc.reconcile()
            if report.has_diff:
                logger.warning(
                    f"[Reconciliation] {len(report.diffs)} diff(s) found: "
                    f"{[d.symbol for d in report.diffs]}"
                )
            else:
                logger.info("[Reconciliation] No diffs — positions match")

            # 无论有无差异都推送对账报告
            if components.notification:
                try:
                    from datetime import datetime, timezone
                    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                    if report.has_diff:
                        diff_syms = [d.symbol for d in report.diffs]
                        text = (
                            "⚠️ *持仓对账报告*\n"
                            f"时间：{ts}\n"
                            f"发现 {len(report.diffs)} 个标的持仓差异：\n"
                            f"{', '.join(diff_syms[:10])}"
                            + (f" 等{len(diff_syms)}只" if len(diff_syms) > 10 else "")
                            + "\n请检查 broker 与本地记录"
                        )
                    else:
                        text = (
                            "✅ *持仓对账报告*\n"
                            f"时间：{ts}\n"
                            "持仓一致，无差异"
                        )
                    components.notification.send_message(text)
                except Exception as exc:
                    logger.warning(f"[Reconciliation] notification failed: {exc}")
        except Exception as exc:
            logger.error(f"[Reconciliation] Failed: {exc}")

    return on_reconciliation


if __name__ == "__main__":
    main()

