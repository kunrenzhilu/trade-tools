"""AppConfig — 统一配置管理（Pydantic BaseSettings + YAML + .env）。

加载优先级（从低到高）：
    代码默认值 < config/default.yaml < 环境变量 / .env 文件

使用方法：
    from mytrader.infra.config import load_config
    cfg = load_config()            # 自动寻找 config/default.yaml
    cfg = load_config("path/to/config.yaml")
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# ---------------------------------------------------------------------------
# 子配置块
# ---------------------------------------------------------------------------

class SystemConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    env: Literal["paper", "live"] = "paper"
    timezone: str = "America/New_York"
    log_level: str = "INFO"


class DataConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    provider: str = "yfinance"
    cache_dir: str = "~/.mytrader/cache"
    cache_ttl_daily_hour: int = 18
    cache_ttl_intraday_minutes: int = 30


class StrategyConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    name: str = "dual_ma"
    params: dict[str, Any] = Field(default_factory=dict)


class BacktestConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    init_cash: float = 100_000.0
    fees: float = 0.001
    slippage: float = 0.001
    fill_price: str = "next_open"


class CircuitBreakerConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    daily_loss_limit: float = Field(0.02, ge=0.001, le=0.5)
    weekly_loss_limit: float = Field(0.05, ge=0.001, le=0.5)
    monthly_loss_limit: float = Field(0.10, ge=0.001, le=0.5)


class RiskConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    risk_per_trade: float = Field(0.01, ge=0.001, le=0.05)
    max_position_pct: float = Field(0.20, ge=0.05, le=0.50)
    max_total_exposure_pct: float = Field(0.80, ge=0.20, le=1.0)
    max_concurrent_positions: int = Field(5, ge=1, le=20)
    max_single_position_pct: float = Field(0.20, ge=0.05, le=0.50)
    min_order_value: float = Field(500.0, ge=0.0)
    circuit_breaker: CircuitBreakerConfig = Field(default_factory=CircuitBreakerConfig)


class SignalFilterConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    volume_filter_enabled: bool = True
    volume_filter_threshold: float = 1.5
    volume_filter_window: int = 20

    atr_filter_enabled: bool = True
    atr_filter_period: int = 14
    atr_filter_max_atr_pct: float = 0.05

    sentiment_filter_enabled: bool = False

    time_window_filter_enabled: bool = False
    time_window_market_open_buffer_min: int = 15
    time_window_market_close_buffer_min: int = 15

    cooldown_filter_enabled: bool = True
    cooldown_filter_min_bars: int = 5


class ExecutionConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    mode: Literal["paper", "semi_auto", "auto"] = "paper"
    broker: str = "alpaca"
    slippage_pct: float = Field(0.001, ge=0.0, le=0.05)
    commission_pct: float = Field(0.001, ge=0.0, le=0.05)
    limit_order_timeout_min: int = 5


class TelegramConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    enabled: bool = False
    alert_levels: list[str] = Field(default_factory=lambda: ["WARN", "ERROR", "CRITICAL"])


class MonitorConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    telegram: TelegramConfig = Field(default_factory=TelegramConfig)


class AlpacaConfig(BaseSettings):
    """Alpaca 美股 API 配置（敏感信息通过环境变量注入）。"""

    model_config = SettingsConfigDict(extra="ignore")

    api_key: str = ""
    secret_key: str = ""
    paper: bool = True  # True=沙盒；False=真实账户


class IBKRConfig(BaseSettings):
    """Interactive Brokers TWS/Gateway 连接配置。"""

    model_config = SettingsConfigDict(extra="ignore")

    host: str = "127.0.0.1"
    port: int = 7497          # 7497=TWS纸面交易；7496=TWS实盘；4002=IB Gateway纸面；4001=IB Gateway实盘
    client_id: int = 1
    timeout: int = 10         # 连接超时（秒）
    readonly: bool = True     # Phase 3 初期只读，避免误下单


class NotificationConfig(BaseSettings):
    """通知推送配置（Telegram + 企业微信）。"""

    model_config = SettingsConfigDict(extra="ignore")

    # Telegram Bot
    telegram_enabled: bool = False
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # 企业微信 Webhook
    wechat_work_enabled: bool = False
    wechat_work_webhook_url: str = ""

    # 告警冷却：同类告警最小间隔（秒），防骚扰
    alert_cooldown_seconds: int = 300

    # 最低发送级别：INFO / WARN / ERROR / CRITICAL
    min_alert_level: str = "WARN"


class SchedulerConfig(BaseSettings):
    """APScheduler 定时任务配置（美股时区 ET）。"""

    model_config = SettingsConfigDict(extra="ignore")

    enabled: bool = True
    timezone: str = "America/New_York"

    # 盘前扫描（跳过开盘前 5 分钟噪音）
    morning_scan_hour: int = 9
    morning_scan_minute: int = 35

    # 盘中扫描间隔（分钟）
    intraday_interval_minutes: int = 30

    # 收盘前检查
    eod_check_hour: int = 15
    eod_check_minute: int = 45

    # 盘后对账
    reconciliation_hour: int = 16
    reconciliation_minute: int = 30

    # 任务宽限期（秒）：错过触发后最多延迟执行
    misfire_grace_time: int = 60


# ---------------------------------------------------------------------------
# 顶层 AppConfig
# ---------------------------------------------------------------------------

class AppConfig(BaseSettings):
    """应用全局配置，支持 YAML 文件 + .env 环境变量覆盖。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        extra="ignore",
    )

    system: SystemConfig = Field(default_factory=SystemConfig)
    data: DataConfig = Field(default_factory=DataConfig)
    strategy: StrategyConfig = Field(default_factory=StrategyConfig)
    backtest: BacktestConfig = Field(default_factory=BacktestConfig)
    risk: RiskConfig = Field(default_factory=RiskConfig)
    signal_filter: SignalFilterConfig = Field(default_factory=SignalFilterConfig)
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)
    monitor: MonitorConfig = Field(default_factory=MonitorConfig)

    # Phase 3 新增子配置
    alpaca: AlpacaConfig = Field(default_factory=AlpacaConfig)
    ibkr: IBKRConfig = Field(default_factory=IBKRConfig)
    notification: NotificationConfig = Field(default_factory=NotificationConfig)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)

    @field_validator("risk", mode="before")
    @classmethod
    def _parse_risk(cls, v: Any) -> Any:
        if isinstance(v, dict):
            cb = v.pop("circuit_breaker", {})
            if cb:
                v["circuit_breaker"] = CircuitBreakerConfig.model_validate(cb)
        return v

    @field_validator("monitor", mode="before")
    @classmethod
    def _parse_monitor(cls, v: Any) -> Any:
        if isinstance(v, dict):
            tg = v.pop("telegram", {})
            if tg:
                v["telegram"] = TelegramConfig.model_validate(tg)
        return v


# ---------------------------------------------------------------------------
# 工厂函数
# ---------------------------------------------------------------------------

def _find_default_yaml() -> Path | None:
    """从当前目录向上查找 config/default.yaml。"""
    here = Path.cwd()
    for parent in [here, *here.parents]:
        candidate = parent / "config" / "default.yaml"
        if candidate.exists():
            return candidate
    return None


def _flatten_yaml(d: dict, prefix: str = "") -> dict[str, Any]:
    """将嵌套 YAML dict 展平，供 AppConfig 解析（非破坏性，保留原层级）。"""
    # 我们直接传整个嵌套 dict 给 model_validate，不需要展平
    return d


def load_config(yaml_path: str | Path | None = None) -> AppConfig:
    """加载配置。

    Args:
        yaml_path: YAML 配置文件路径。None 时自动向上查找 config/default.yaml。

    Returns:
        AppConfig 实例。
    """
    raw: dict[str, Any] = {}

    # 1. 读取 YAML 文件
    if yaml_path is None:
        yaml_path = _find_default_yaml()

    if yaml_path is not None:
        yaml_path = Path(yaml_path)
        if yaml_path.exists():
            with yaml_path.open("r", encoding="utf-8") as f:
                raw = yaml.safe_load(f) or {}

    # 2. 用 YAML 值构造 AppConfig（Pydantic 会自动再用环境变量覆盖）
    return AppConfig.model_validate(raw)
