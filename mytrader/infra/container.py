"""Container — 依赖注入工厂，根据配置装配所有模块。

设计原则：
- 唯一入口：所有模块实例化均通过 Container 完成
- 模式切换：execution.mode 控制 Broker 选择
  - paper:     PaperBroker（无需外部连接）
  - semi_auto: AlpacaBroker(mode="semi_auto")（推送通知，人工确认）
  - auto:      AlpacaBroker(mode="auto") 或 IBKRBroker(mode="auto")
- 测试友好：支持注入 mock 依赖
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from loguru import logger

from mytrader.infra.config import AppConfig, load_config
from mytrader.infra.event_bus import EventBus
from mytrader.execution.base import BrokerProtocol
from mytrader.execution.paper_broker import PaperBroker
from mytrader.execution.notification import NotificationService
from mytrader.monitor.health_checker import HealthChecker
from mytrader.portfolio.tracker import PortfolioTracker
from mytrader.portfolio.persistence import PortfolioPersistence


@dataclass
class AppComponents:
    """所有装配完毕的应用组件。

    Attributes:
        config:       全局配置
        bus:          事件总线
        broker:       当前模式对应的经纪商
        tracker:      持仓追踪器
        notification: 通知服务
        health:       健康检查器
        persistence:  数据库持久化（可选）
    """

    config: AppConfig
    bus: EventBus
    broker: BrokerProtocol
    tracker: PortfolioTracker
    notification: NotificationService
    health: HealthChecker
    persistence: PortfolioPersistence | None = None


class Container:
    """依赖注入容器。

    用法：
        config = load_config()
        components = Container.build(config)
        # components.broker, components.tracker, ...
    """

    @staticmethod
    def build(
        config: AppConfig | None = None,
        *,
        broker_override: BrokerProtocol | None = None,
        db_url: str = "sqlite:///mytrader.db",
    ) -> AppComponents:
        """装配所有模块依赖。

        Args:
            config:          AppConfig（None 时自动加载）
            broker_override: 注入自定义 Broker（测试用）
            db_url:          SQLite 路径（":memory:" 用于测试）
        """
        if config is None:
            config = load_config()

        logger.info(
            f"Container.build: mode={config.execution.mode}, "
            f"broker={config.execution.broker}"
        )

        # 1. 基础设施
        bus = EventBus()

        # 2. 选择 Broker
        if broker_override is not None:
            broker = broker_override
            logger.info("Container: using broker_override")
        else:
            broker = Container._create_broker(config)

        # 3. 通知服务
        notification = NotificationService(config.notification)

        # 4. 持久化
        persistence = None
        if db_url != ":memory:":
            try:
                persistence = PortfolioPersistence(db_url)
            except Exception as exc:
                logger.warning(f"Container: persistence init failed ({exc}), running without DB")

        # 5. 持仓追踪器
        tracker = PortfolioTracker(
            initial_cash=config.backtest.init_cash,
            persistence=persistence,
        )

        # 6. 健康检查器（注册基本检查项）
        health = HealthChecker()
        health.register_data_feed()

        logger.info("Container.build complete")
        return AppComponents(
            config=config,
            bus=bus,
            broker=broker,
            tracker=tracker,
            notification=notification,
            health=health,
            persistence=persistence,
        )

    @staticmethod
    def _create_broker(config: AppConfig) -> BrokerProtocol:
        """根据 execution.mode 和 execution.broker 创建对应 Broker。"""
        mode = config.execution.mode
        broker_name = config.execution.broker.lower()

        if mode == "paper":
            logger.info("Container: creating PaperBroker")
            return PaperBroker(
                slippage_pct=config.execution.slippage_pct,
                commission_pct=config.execution.commission_pct,
            )

        if mode in ("semi_auto", "auto"):
            if broker_name == "alpaca":
                from mytrader.execution.alpaca_broker import AlpacaBroker
                logger.info(
                    f"Container: creating AlpacaBroker(paper={config.alpaca.paper}, mode={mode})"
                )
                return AlpacaBroker(
                    api_key=config.alpaca.api_key,
                    secret_key=config.alpaca.secret_key,
                    paper=config.alpaca.paper,
                    mode=mode,
                )
            if broker_name == "ibkr":
                from mytrader.execution.ibkr_broker import IBKRBroker
                logger.info(
                    f"Container: creating IBKRBroker(host={config.ibkr.host}, "
                    f"port={config.ibkr.port}, mode={mode})"
                )
                return IBKRBroker(
                    host=config.ibkr.host,
                    port=config.ibkr.port,
                    client_id=config.ibkr.client_id,
                    timeout=config.ibkr.timeout,
                    readonly=config.ibkr.readonly,
                    mode=mode,
                )

        # 兜底：使用 PaperBroker
        logger.warning(
            f"Container: unknown mode={mode!r}/broker={broker_name!r}, "
            f"falling back to PaperBroker"
        )
        return PaperBroker(
            slippage_pct=config.execution.slippage_pct,
            commission_pct=config.execution.commission_pct,
        )
