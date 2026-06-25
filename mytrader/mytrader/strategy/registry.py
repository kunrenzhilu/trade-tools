"""策略注册表。

使用 @register_strategy("name") 装饰器注册策略函数，
通过 STRATEGY_REGISTRY["name"] 获取对应函数。
"""

from __future__ import annotations

from typing import Callable

import pandas as pd

# 策略函数签名：(close: pd.Series, **params) -> pd.Series
# 返回的 pd.Series：1=BUY, -1=SELL, 0=HOLD，索引与 close 相同
StrategyFn = Callable[..., pd.Series]

STRATEGY_REGISTRY: dict[str, StrategyFn] = {}


def register_strategy(name: str) -> Callable[[StrategyFn], StrategyFn]:
    """策略注册装饰器。

    Example::

        @register_strategy("my_strategy")
        def my_strategy(close: pd.Series, period: int = 14) -> pd.Series:
            ...
    """
    def decorator(fn: StrategyFn) -> StrategyFn:
        if name in STRATEGY_REGISTRY:
            raise ValueError(f"Strategy '{name}' is already registered")
        STRATEGY_REGISTRY[name] = fn
        return fn

    return decorator
