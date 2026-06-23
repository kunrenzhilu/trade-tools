"""DataSyncService — 增量同步器。

从外部数据源拉取 delta，写入 MarketDataStore。

数据源优先级：Alpaca（主）→ yfinance（fallback）

Fallback 策略：
    Alpaca 无数据时，**不直接写入** yfinance 数据（防止复权基准不同导致价格跳变）。
    而是：记录 WARN，标记 data_quality=degraded，等主源恢复后补拉。
    yfinance 数据作为"知情后兜底"，仅在首次回填或主源长期不可用时使用。
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from typing import Protocol

import pandas as pd
from loguru import logger

from mytrader.data.store.market_data_store import MarketDataStore
from mytrader.data.store.models import SyncReport


# ---------------------------------------------------------------------------
# DataProvider Protocol（鸭子类型，兼容 YFinanceProvider / AlpacaDataProvider）
# ---------------------------------------------------------------------------

class DataProvider(Protocol):
    def get_ohlcv(
        self,
        symbol: str,
        start: date,
        end: date,
        timeframe: str = "1d",
    ) -> pd.DataFrame: ...


# ---------------------------------------------------------------------------
# DataSyncService
# ---------------------------------------------------------------------------

class DataSyncService:
    """增量同步器：从外部源拉 delta，写入 MarketDataStore。

    Args:
        store:    MarketDataStore 实例
        primary:  主数据源（AlpacaDataProvider）
        fallback: 备用数据源（YFinanceProvider），仅在明确启用时使用
        use_fallback_on_empty: True = 主源无数据时用 fallback（标记 degraded）
                               False = 主源无数据则跳过（保持主源纯净）
    """

    def __init__(
        self,
        store: MarketDataStore,
        primary: DataProvider,
        fallback: DataProvider | None = None,
        use_fallback_on_empty: bool = True,
    ) -> None:
        self._store = store
        self._primary = primary
        self._fallback = fallback
        self._use_fallback = use_fallback_on_empty

    # ------------------------------------------------------------------
    # 单只同步
    # ------------------------------------------------------------------

    def sync_symbol(
        self,
        symbol: str,
        timeframe: str = "1d",
    ) -> int:
        """同步单只标的：查本地最新日期 → 拉 [last+1, today] → upsert。

        Returns:
            新增 bar 数（0 表示已是最新）
        """
        today = date.today()
        last = self._store.get_last_synced(symbol, timeframe)

        if last is None:
            # 首次同步：回填 5 年
            start = today - timedelta(days=5 * 365)
            logger.info(f"[sync] {symbol}: first sync, backfill from {start}")
        else:
            if last >= today:
                logger.debug(f"[sync] {symbol}: already up-to-date ({last})")
                return 0
            start = last + timedelta(days=1)

        return self._pull_and_store(symbol, start, today, timeframe)

    # ------------------------------------------------------------------
    # 批量同步
    # ------------------------------------------------------------------

    def sync_all(
        self,
        symbols: list[str],
        timeframe: str = "1d",
        max_workers: int = 8,
        sleep_between_batches: float = 0.3,
    ) -> SyncReport:
        """并发同步全部标的（收盘后调用）。

        Args:
            symbols:               标的列表
            max_workers:           并发线程数
            sleep_between_batches: 每批次后休眠秒数（避免限速）
        """
        report = SyncReport(total_symbols=len(symbols))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.sync_symbol, sym, timeframe): sym
                for sym in symbols
            }
            for future in as_completed(futures):
                sym = futures[future]
                try:
                    new_bars = future.result()
                    quality = self._store.get_data_quality(sym, timeframe)
                    if quality == "degraded":
                        report.synced_degraded += 1
                    else:
                        report.synced_ok += 1
                    report.total_new_bars += new_bars
                except Exception as e:
                    report.failed += 1
                    report.errors[sym] = str(e)
                    logger.warning(f"[sync_all] {sym} failed: {e}")

        logger.info(f"[sync_all] {report}")
        return report

    # ------------------------------------------------------------------
    # 首次回填
    # ------------------------------------------------------------------

    def backfill(
        self,
        symbols: list[str],
        years: int = 5,
        timeframe: str = "1d",
        max_workers: int = 8,
        batch_size: int = 50,
        sleep_between_batches: float = 1.0,
    ) -> SyncReport:
        """首次回填 N 年历史（一次性操作）。

        分批处理（每批 batch_size 只），批次间 sleep 避免触发限速。
        """
        report = SyncReport(total_symbols=len(symbols))
        today = date.today()
        start = today - timedelta(days=years * 365)

        logger.info(
            f"[backfill] {len(symbols)} symbols × {years}y from {start}, "
            f"batch_size={batch_size}"
        )

        # 分批处理
        batches = [
            symbols[i : i + batch_size]
            for i in range(0, len(symbols), batch_size)
        ]

        for batch_idx, batch in enumerate(batches):
            logger.info(
                f"[backfill] batch {batch_idx+1}/{len(batches)}: {len(batch)} symbols"
            )
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(
                        self._pull_and_store, sym, start, today, timeframe
                    ): sym
                    for sym in batch
                }
                for future in as_completed(futures):
                    sym = futures[future]
                    try:
                        new_bars = future.result()
                        quality = self._store.get_data_quality(sym, timeframe)
                        if quality == "degraded":
                            report.synced_degraded += 1
                        else:
                            report.synced_ok += 1
                        report.total_new_bars += new_bars
                    except Exception as e:
                        report.failed += 1
                        report.errors[sym] = str(e)
                        logger.warning(f"[backfill] {sym} failed: {e}")

            if batch_idx < len(batches) - 1:
                time.sleep(sleep_between_batches)

        logger.info(f"[backfill] done: {report}")
        return report

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _pull_and_store(
        self,
        symbol: str,
        start: date,
        end: date,
        timeframe: str,
    ) -> int:
        """从主源（或 fallback）拉取并写入，返回新增行数。

        Fallback 策略：
            主源有数据 → 写入，quality=ok
            主源无数据 → 尝试 fallback（若启用），写入但 quality=degraded
            两源均无数据 → 不写入，quality=degraded，记录警告
        """
        # 1. 主源
        df = pd.DataFrame()
        source = "unknown"
        quality = "ok"

        try:
            df = self._primary.get_ohlcv(symbol, start, end, timeframe)
            source = "alpaca"
        except Exception as e:
            logger.warning(f"[sync] {symbol}: primary failed ({e})")

        # 2. Fallback
        if df.empty:
            if self._use_fallback and self._fallback is not None:
                logger.warning(
                    f"[sync] {symbol}: primary empty, fallback to yfinance "
                    f"(data_quality=degraded)"
                )
                try:
                    df = self._fallback.get_ohlcv(symbol, start, end, timeframe)
                    source = "yfinance"
                    quality = "degraded"
                except Exception as e:
                    logger.warning(f"[sync] {symbol}: fallback also failed ({e})")
            else:
                logger.warning(
                    f"[sync] {symbol}: primary empty, fallback disabled, "
                    f"skipping write (data_quality=degraded)"
                )
                quality = "degraded"

        # 3. 写入
        new_bars = 0
        if not df.empty:
            new_bars = self._store.upsert_bars(symbol, df, timeframe, source=source)

        # 4. 更新 sync_state（无论有无数据都更新，避免重复拉取）
        self._store.set_last_synced(symbol, end, timeframe, data_quality=quality)

        return new_bars
