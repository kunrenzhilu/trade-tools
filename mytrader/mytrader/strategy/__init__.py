"""Strategy engine package."""

from mytrader.strategy.base import Signal, SignalDirection
from mytrader.strategy.registry import STRATEGY_REGISTRY, register_strategy
from mytrader.strategy.ensemble import ensemble_signal

# 注册内置策略（import 触发 @register_strategy 装饰器）
import mytrader.strategy.strategies.dual_ma          # noqa: F401
import mytrader.strategy.strategies.rsi_mean_revert  # noqa: F401
import mytrader.strategy.strategies.bollinger_band   # noqa: F401
import mytrader.strategy.strategies.macd_cross       # noqa: F401

__all__ = [
    "Signal",
    "SignalDirection",
    "STRATEGY_REGISTRY",
    "register_strategy",
    "ensemble_signal",
]
