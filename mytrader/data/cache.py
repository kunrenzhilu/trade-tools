"""本地 Parquet 缓存管理。

缓存目录结构：
    ~/.mytrader/cache/{provider}/{symbol}/{timeframe}/{YYYY-MM-DD}.parquet

过期策略：
    - 日线（1d）：当天 18:00 之后刷新
    - 分钟级（< 1d）：30 分钟后刷新
    - 历史数据（end 距今 > 365 天）：永不过期
"""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
from loguru import logger


class DataCache:
    """Parquet 文件缓存，对 OHLCV DataFrame 做读写。"""

    def __init__(
        self,
        cache_dir: str = "~/.mytrader/cache",
        ttl_daily_hour: int = 18,
        ttl_intraday_minutes: int = 30,
    ) -> None:
        self._root = Path(cache_dir).expanduser().resolve()
        self._ttl_daily_hour = ttl_daily_hour
        self._ttl_intraday_minutes = ttl_intraday_minutes

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(
        self,
        provider: str,
        symbol: str,
        start: date,
        end: date,
        timeframe: str,
    ) -> pd.DataFrame | None:
        """读取缓存。若不存在或已过期，返回 None。"""
        path = self._path(provider, symbol, start, end, timeframe)
        if not path.exists():
            return None

        if self._is_expired(path, end, timeframe):
            logger.debug(f"Cache expired: {path.name}")
            return None

        try:
            df = pd.read_parquet(path)
            logger.debug(f"Cache hit: {path.name} ({len(df)} rows)")
            return df
        except Exception as exc:
            logger.warning(f"Failed to read cache {path}: {exc}")
            return None

    def set(
        self,
        provider: str,
        symbol: str,
        start: date,
        end: date,
        timeframe: str,
        df: pd.DataFrame,
    ) -> None:
        """写入缓存。"""
        path = self._path(provider, symbol, start, end, timeframe)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            df.to_parquet(path, index=True)
            logger.debug(f"Cache written: {path.name} ({len(df)} rows)")
        except Exception as exc:
            logger.warning(f"Failed to write cache {path}: {exc}")

    def invalidate(
        self,
        provider: str,
        symbol: str,
        start: date,
        end: date,
        timeframe: str,
    ) -> None:
        """强制删除某个缓存文件。"""
        path = self._path(provider, symbol, start, end, timeframe)
        if path.exists():
            path.unlink()
            logger.debug(f"Cache invalidated: {path.name}")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _path(
        self,
        provider: str,
        symbol: str,
        start: date,
        end: date,
        timeframe: str,
    ) -> Path:
        safe_symbol = symbol.replace("/", "_").replace(".", "_")
        filename = f"{start}_{end}.parquet"
        return self._root / provider / safe_symbol / timeframe / filename

    def _is_expired(self, path: Path, end: date, timeframe: str) -> bool:
        """判断缓存文件是否过期。"""
        now = datetime.now(tz=timezone.utc)
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)

        # 历史数据（end 距今超过 365 天）永不过期
        end_dt = datetime(end.year, end.month, end.day, tzinfo=timezone.utc)
        if (now - end_dt).days > 365:
            return False

        if timeframe == "1d":
            # 日线：当天 18:00 UTC 之后需要刷新（确保收盘后数据完整）
            today_18 = now.replace(hour=self._ttl_daily_hour, minute=0, second=0, microsecond=0)
            if now >= today_18 and mtime < today_18:
                return True
            return False
        else:
            # 分钟级：30 分钟 TTL
            return (now - mtime) > timedelta(minutes=self._ttl_intraday_minutes)
