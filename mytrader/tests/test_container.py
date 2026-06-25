"""测试 Phase 3 Container（依赖注入工厂）。"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from mytrader.infra.config import AppConfig, ExecutionConfig, load_config
from mytrader.infra.container import Container, AppComponents
from mytrader.execution.paper_broker import PaperBroker
from mytrader.portfolio.tracker import PortfolioTracker
from mytrader.execution.notification import NotificationService
from mytrader.monitor.health_checker import HealthChecker


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------

def make_config(mode: str = "paper", broker: str = "alpaca") -> AppConfig:
    cfg = AppConfig()
    # 使用 object.__setattr__ 绕过 Pydantic immutability
    object.__setattr__(cfg.execution, "mode", mode)
    object.__setattr__(cfg.execution, "broker", broker)
    return cfg


# ---------------------------------------------------------------------------
# Container.build 基本测试
# ---------------------------------------------------------------------------

class TestContainerBuild:
    def test_build_paper_mode_returns_paper_broker(self):
        """paper 模式装配 PaperBroker。"""
        cfg = make_config(mode="paper")
        components = Container.build(cfg, db_url=":memory:")

        assert isinstance(components.broker, PaperBroker)
        assert isinstance(components.tracker, PortfolioTracker)
        assert isinstance(components.notification, NotificationService)
        assert isinstance(components.health, HealthChecker)

    def test_build_returns_app_components(self):
        """返回 AppComponents dataclass。"""
        cfg = make_config()
        components = Container.build(cfg, db_url=":memory:")
        assert isinstance(components, AppComponents)
        assert components.config is cfg

    def test_build_semi_auto_alpaca(self):
        """semi_auto + alpaca 模式装配 AlpacaBroker（不建立真实连接）。"""
        from mytrader.execution.alpaca_broker import AlpacaBroker
        cfg = make_config(mode="semi_auto", broker="alpaca")
        components = Container.build(cfg, db_url=":memory:")
        # AlpacaBroker 延迟初始化，只检查类型
        assert isinstance(components.broker, AlpacaBroker)
        assert components.broker._mode == "semi_auto"

    def test_build_semi_auto_ibkr(self):
        """semi_auto + ibkr 模式装配 IBKRBroker（不建立真实连接）。"""
        from mytrader.execution.ibkr_broker import IBKRBroker
        cfg = make_config(mode="semi_auto", broker="ibkr")
        components = Container.build(cfg, db_url=":memory:")
        assert isinstance(components.broker, IBKRBroker)
        assert components.broker._mode == "semi_auto"

    def test_build_with_broker_override(self):
        """注入 broker_override 时使用覆盖的 Broker。"""
        cfg = make_config(mode="auto", broker="alpaca")
        mock_broker = MagicMock()
        components = Container.build(cfg, broker_override=mock_broker, db_url=":memory:")
        assert components.broker is mock_broker

    def test_build_unknown_broker_falls_back_to_paper(self):
        """未知 broker 名称时降级为 PaperBroker。"""
        cfg = make_config(mode="semi_auto", broker="unknown_broker")
        components = Container.build(cfg, db_url=":memory:")
        # 未知 broker 在 semi_auto 模式下降级为 PaperBroker
        assert isinstance(components.broker, PaperBroker)

    def test_build_event_bus_not_none(self):
        """EventBus 不为 None。"""
        from mytrader.infra.event_bus import EventBus
        cfg = make_config()
        components = Container.build(cfg, db_url=":memory:")
        assert isinstance(components.bus, EventBus)

    def test_build_initial_cash_from_config(self):
        """PortfolioTracker 使用配置中的 init_cash。"""
        cfg = make_config()
        object.__setattr__(cfg.backtest, "init_cash", 50_000.0)
        components = Container.build(cfg, db_url=":memory:")
        assert components.tracker.cash == pytest.approx(50_000.0)

    def test_build_persistence_none_for_memory(self):
        """db_url=':memory:' 时 persistence 应正常初始化（内存 SQLite）。"""
        cfg = make_config()
        # :memory: 传入 PortfolioPersistence 是合法的
        components = Container.build(cfg, db_url=":memory:")
        # persistence 可为 None 或有效对象，关键是不报错
        assert components is not None


# ---------------------------------------------------------------------------
# Container._create_broker 直接测试
# ---------------------------------------------------------------------------

class TestContainerCreateBroker:
    def test_paper_mode_creates_paper_broker(self):
        cfg = make_config(mode="paper")
        broker = Container._create_broker(cfg)
        assert isinstance(broker, PaperBroker)

    def test_semi_auto_alpaca_creates_alpaca_broker(self):
        from mytrader.execution.alpaca_broker import AlpacaBroker
        cfg = make_config(mode="semi_auto", broker="alpaca")
        broker = Container._create_broker(cfg)
        assert isinstance(broker, AlpacaBroker)

    def test_auto_alpaca_creates_alpaca_broker(self):
        from mytrader.execution.alpaca_broker import AlpacaBroker
        cfg = make_config(mode="auto", broker="alpaca")
        broker = Container._create_broker(cfg)
        assert isinstance(broker, AlpacaBroker)
        assert broker._mode == "auto"
