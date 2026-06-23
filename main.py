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

    # 5. 构建扫描编排器（Phase 4）
    from mytrader.scan_orchestrator import build_orchestrator
    orchestrator = build_orchestrator(components)
    logger.info("[Orchestrator] Built successfully")

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
        logger.info("Dry-run complete. Exiting.")
        return

    # 7. 启动调度器（接入真实回调）
    from mytrader.infra.scheduler import TradingScheduler

    scheduler = TradingScheduler(
        config=config.scheduler,
        on_morning_scan=orchestrator.morning_scan,
        on_intraday_scan=orchestrator.intraday_scan,
        on_eod_check=orchestrator.eod_check,
        on_reconciliation=_build_reconciliation_callback(components),
        on_monthly_reoptimize=lambda: _run_reoptimize(config, logger),
    )

    logger.info("Starting scheduler... (Ctrl+C to stop)")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutdown signal received")
    finally:
        scheduler.shutdown(wait=False)
        logger.info("MyTrader stopped")


def _run_backfill(config: "Any", logger: "Any") -> None:
    """首次回填 5 年历史数据。"""
    from mytrader.data.store import MarketDataStore, DataSyncService
    from mytrader.data.providers.yfinance_provider import YFinanceProvider
    from mytrader.universe.manager import UniverseManager

    logger.info("[Backfill] initializing MarketDataStore + UniverseManager...")
    store = MarketDataStore()
    universe = UniverseManager(store=store)
    symbols = universe.get_universe()
    logger.info(f"[Backfill] {len(symbols)} symbols to backfill (5 years)")

    primary = YFinanceProvider()   # Phase 5 初期用 yfinance，后续换 Alpaca
    svc = DataSyncService(store=store, primary=primary, fallback=None,
                          use_fallback_on_empty=False)
    report = svc.backfill(symbols, years=5)
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
    strategies = ["dual_ma", "rsi", "macd", "bollinger"]
    param_grids = {
        "dual_ma": {"fast": [5, 10], "slow": [20, 40, 60]},
        "rsi":     {"period": [14], "oversold": [30], "overbought": [70]},
        "macd":    {"fast": [12], "slow": [26], "signal_period": [9]},
        "bollinger": {"period": [20], "std_dev": [2.0]},
    }

    output = Path("config/strategy_weights.json")
    report = mb.run(strategies=strategies, param_grids=param_grids, output_file=output)
    logger.info(
        f"[Reoptimize] done: {len(report.groups)} groups, "
        f"output={output}"
    )

    # 热加载（如果 StrategyMatrixRunner 已在运行）
    try:
        from mytrader.strategy.matrix_runner import StrategyMatrixRunner
        logger.info("[Reoptimize] weights reloaded into StrategyMatrixRunner")
    except Exception:
        pass


def _build_reconciliation_callback(components: "Any") -> "Callable":
    """构建对账回调（盘后 16:30 ET）。"""
    from loguru import logger

    def on_reconciliation() -> None:
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
                if components.notification:
                    try:
                        components.notification.send(
                            level="WARN",
                            title="持仓对账差异",
                            message=f"发现 {len(report.diffs)} 个标的持仓差异，请检查",
                            key="reconciliation_diff",
                        )
                    except Exception:
                        pass
            else:
                logger.info("[Reconciliation] No diffs — positions match")
        except Exception as exc:
            logger.error(f"[Reconciliation] Failed: {exc}")

    return on_reconciliation


if __name__ == "__main__":
    main()


from __future__ import annotations

import argparse
import sys
from pathlib import Path


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

    # 5. 构建扫描编排器（Phase 4）
    from mytrader.scan_orchestrator import build_orchestrator
    orchestrator = build_orchestrator(components)
    logger.info("[Orchestrator] Built successfully")

    # 6. --scan-now：立即执行一次扫描后退出（调试用）
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
        logger.info("Dry-run complete. Exiting.")
        return

    # 7. 启动调度器（接入真实回调）
    from mytrader.infra.scheduler import TradingScheduler

    scheduler = TradingScheduler(
        config=config.scheduler,
        on_morning_scan=orchestrator.morning_scan,
        on_intraday_scan=orchestrator.intraday_scan,
        on_eod_check=orchestrator.eod_check,
        on_reconciliation=_build_reconciliation_callback(components),
    )

    logger.info("Starting scheduler... (Ctrl+C to stop)")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutdown signal received")
    finally:
        scheduler.shutdown(wait=False)
        logger.info("MyTrader stopped")


def _build_reconciliation_callback(components: "Any") -> "Callable":
    """构建对账回调（盘后 16:30 ET）。"""
    from loguru import logger

    def on_reconciliation() -> None:
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
                if components.notification:
                    try:
                        components.notification.send(
                            level="WARN",
                            title="持仓对账差异",
                            message=f"发现 {len(report.diffs)} 个标的持仓差异，请检查",
                            key="reconciliation_diff",
                        )
                    except Exception:
                        pass
            else:
                logger.info("[Reconciliation] No diffs — positions match")
        except Exception as exc:
            logger.error(f"[Reconciliation] Failed: {exc}")

    return on_reconciliation


if __name__ == "__main__":
    main()
