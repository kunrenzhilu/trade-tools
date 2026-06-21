"""MyTrader 系统启动入口。

用法：
    python main.py                        # paper 模式，默认配置
    python main.py --mode semi_auto       # 半自动（推送通知，人工确认）
    python main.py --mode auto            # 全自动（直接下单）
    python main.py --config path/to.yaml  # 自定义配置文件
    python main.py --dry-run              # 仅检查配置和依赖，不启动调度器

环境变量覆盖（通过 .env 文件）：
    EXECUTION__MODE=semi_auto
    ALPACA__API_KEY=your_key
    NOTIFICATION__TELEGRAM_ENABLED=true
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
        f"scheduler.enabled={config.scheduler.enabled}"
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

    if args.dry_run:
        logger.info("Dry-run complete. Exiting.")
        return

    # 5. 启动调度器
    from mytrader.infra.scheduler import TradingScheduler

    scheduler = TradingScheduler(
        config=config.scheduler,
        # 回调函数：Phase 3 中实际实现各扫描逻辑
        on_morning_scan=lambda: logger.info("[Callback] Morning scan triggered"),
        on_intraday_scan=lambda: logger.info("[Callback] Intraday scan triggered"),
        on_eod_check=lambda: logger.info("[Callback] EOD check triggered"),
        on_reconciliation=lambda: logger.info("[Callback] Reconciliation triggered"),
    )

    logger.info("Starting scheduler... (Ctrl+C to stop)")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutdown signal received")
    finally:
        scheduler.shutdown(wait=False)
        logger.info("MyTrader stopped")


if __name__ == "__main__":
    main()
