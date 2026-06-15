"""过滤器基类 Protocol。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    import pandas as pd
    from mytrader.strategy.base import Signal
    from mytrader.signal.models import FilteredSignal


class BaseFilter(Protocol):
    """所有过滤器必须实现的接口。"""

    name: str

    def apply(
        self,
        signal: "Signal",
        df: "pd.DataFrame",
    ) -> "FilteredSignal":
        """对单个信号执行过滤判断。

        Args:
            signal: 原始策略信号
            df:     包含 OHLCV 数据的 DataFrame（index 为 DatetimeIndex）

        Returns:
            FilteredSignal，passed=True 表示通过，False 表示被过滤
        """
        ...
