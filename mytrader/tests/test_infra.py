"""测试 infra 模块：AppConfig 加载 + EventBus。"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from mytrader.infra.config import (
    AppConfig,
    BacktestConfig,
    CircuitBreakerConfig,
    DataConfig,
    ExecutionConfig,
    SystemConfig,
    _find_default_yaml,
    load_config,
)
from mytrader.infra.event_bus import EventBus, Events


# ---------------------------------------------------------------------------
# AppConfig 测试
# ---------------------------------------------------------------------------

class TestAppConfig:
    def test_default_values(self):
        """默认值加载正确。"""
        cfg = AppConfig()
        assert cfg.system.env == "paper"
        assert cfg.risk.risk_per_trade == 0.01
        assert cfg.signal_filter.cooldown_filter_enabled is True

    def test_load_from_yaml(self, tmp_path):
        """从 YAML 文件加载配置。"""
        yaml_data = {
            "system": {"env": "live", "log_level": "DEBUG"},
            "risk": {"risk_per_trade": 0.02, "max_concurrent_positions": 3},
        }
        yaml_file = tmp_path / "config.yaml"
        yaml_file.write_text(yaml.dump(yaml_data))

        cfg = load_config(yaml_file)
        assert cfg.system.env == "live"
        assert cfg.system.log_level == "DEBUG"
        assert cfg.risk.risk_per_trade == 0.02
        assert cfg.risk.max_concurrent_positions == 3

    def test_env_override(self, monkeypatch):
        """环境变量通过 AppConfig() 直接构造时可以覆盖默认值。"""
        monkeypatch.setenv("RISK__RISK_PER_TRADE", "0.03")
        cfg = AppConfig()
        assert cfg.risk.risk_per_trade == pytest.approx(0.03)

    def test_circuit_breaker_nested(self, tmp_path):
        """嵌套配置（circuit_breaker）正确解析。"""
        yaml_data = {
            "risk": {
                "circuit_breaker": {
                    "daily_loss_limit": 0.03,
                    "weekly_loss_limit": 0.08,
                }
            }
        }
        yaml_file = tmp_path / "config.yaml"
        yaml_file.write_text(yaml.dump(yaml_data))

        cfg = load_config(yaml_file)
        assert cfg.risk.circuit_breaker.daily_loss_limit == pytest.approx(0.03)
        assert cfg.risk.circuit_breaker.weekly_loss_limit == pytest.approx(0.08)

    def test_missing_yaml_uses_defaults(self):
        """不存在的 YAML 路径使用默认值，不报错。"""
        cfg = load_config("/nonexistent/path/config.yaml")
        assert cfg.system.env == "paper"

    def test_signal_filter_config(self, tmp_path):
        """信号过滤器配置解析。"""
        yaml_data = {
            "signal_filter": {
                "volume_filter_enabled": False,
                "cooldown_filter_min_bars": 10,
            }
        }
        yaml_file = tmp_path / "config.yaml"
        yaml_file.write_text(yaml.dump(yaml_data))

        cfg = load_config(yaml_file)
        assert cfg.signal_filter.volume_filter_enabled is False
        assert cfg.signal_filter.cooldown_filter_min_bars == 10


# ---------------------------------------------------------------------------
# 子配置类独立测试 (P0/P1)
# ---------------------------------------------------------------------------

class TestSubConfigs:
    """P0/P1: 各子配置类的独立默认值和字段约束。"""

    def test_system_config_defaults(self) -> None:
        """IC1: SystemConfig 独立默认值。"""
        c = SystemConfig()
        assert c.env == "paper"
        assert c.timezone == "America/New_York"
        assert c.log_level == "INFO"

    def test_data_config_defaults(self) -> None:
        """IC2: DataConfig cache_dir / ttl 默认值。"""
        c = DataConfig()
        assert c.provider == "yfinance"
        assert "cache" in c.cache_dir
        assert c.cache_ttl_daily_hour == 18
        assert c.cache_ttl_intraday_minutes == 30

    def test_execution_slippage_out_of_range_raises(self) -> None:
        """IC5: slippage_pct 为负值时抛 ValidationError。"""
        with pytest.raises(ValidationError):
            ExecutionConfig(slippage_pct=-0.01)

    def test_backtest_config_use_next_open(self) -> None:
        """IC6: BacktestConfig fill_price 默认使用 next_open。"""
        c = BacktestConfig()
        assert c.fill_price == "next_open"
        assert c.init_cash == 100_000.0

    def test_circuit_breaker_config_limits(self) -> None:
        """IC7: CircuitBreakerConfig 默认阈值。"""
        c = CircuitBreakerConfig()
        assert c.daily_loss_limit == pytest.approx(0.02)
        assert c.weekly_loss_limit == pytest.approx(0.05)
        assert c.monthly_loss_limit == pytest.approx(0.10)

    def test_find_default_yaml_cwd(self) -> None:
        """IC8: _find_default_yaml 向上查找 config/default.yaml。"""
        result = _find_default_yaml()
        # 在项目根目录运行时应能找到
        if result is not None:
            assert result.name == "default.yaml"


# ---------------------------------------------------------------------------
# Config 字段范围验证测试 (P0)
# ---------------------------------------------------------------------------

class TestConfigFieldValidation:
    """P0: Pydantic Field 约束越界测试。"""

    def test_risk_per_trade_at_lower_bound(self) -> None:
        """IC3: risk_per_trade == ge 边界（0.001）不抛异常。"""
        from mytrader.infra.config import RiskConfig
        c = RiskConfig(risk_per_trade=0.001)
        assert c.risk_per_trade == pytest.approx(0.001)

    def test_risk_per_trade_above_max_raises(self) -> None:
        """IC4: risk_per_trade=1.0（超过 le=0.05）抛 ValidationError。"""
        from mytrader.infra.config import RiskConfig
        with pytest.raises(ValidationError):
            RiskConfig(risk_per_trade=1.0)


# ---------------------------------------------------------------------------
# EventBus 测试
# ---------------------------------------------------------------------------

class TestEventBus:
    def test_subscribe_and_publish(self):
        """订阅后能收到事件。"""
        bus = EventBus()
        received = []
        bus.subscribe(Events.SIGNAL_GENERATED, received.append)
        bus.publish(Events.SIGNAL_GENERATED, {"signal": "test"})
        assert len(received) == 1
        assert received[0]["signal"] == "test"

    def test_multiple_handlers(self):
        """多个 handler 都能收到同一事件。"""
        bus = EventBus()
        log1, log2 = [], []
        bus.subscribe(Events.ORDER_FILLED, log1.append)
        bus.subscribe(Events.ORDER_FILLED, log2.append)
        bus.publish(Events.ORDER_FILLED, "payload")
        assert log1 == ["payload"]
        assert log2 == ["payload"]

    def test_handler_exception_does_not_block(self):
        """单个 handler 抛异常不影响其他 handler。"""
        bus = EventBus()
        results = []

        def bad_handler(payload):
            raise RuntimeError("intentional error")

        def good_handler(payload):
            results.append(payload)

        bus.subscribe(Events.ALERT, bad_handler)
        bus.subscribe(Events.ALERT, good_handler)
        bus.publish(Events.ALERT, "alert_data")  # 不应抛出
        assert results == ["alert_data"]

    def test_unsubscribe(self):
        """取消订阅后不再收到事件。"""
        bus = EventBus()
        log = []
        handler = log.append
        bus.subscribe(Events.BAR_RECEIVED, handler)
        bus.unsubscribe(Events.BAR_RECEIVED, handler)
        bus.publish(Events.BAR_RECEIVED, "bar")
        assert log == []

    def test_no_subscribers(self):
        """没有订阅者时发布不报错。"""
        bus = EventBus()
        bus.publish(Events.POSITION_UPDATED, None)  # should not raise

    def test_clear(self):
        """clear() 后所有订阅被清空。"""
        bus = EventBus()
        log = []
        bus.subscribe(Events.CIRCUIT_BREAKER_TRIGGERED, log.append)
        bus.clear()
        bus.publish(Events.CIRCUIT_BREAKER_TRIGGERED, "trigger")
        assert log == []
