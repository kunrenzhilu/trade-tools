"""MarketDataStore — 本地时序数据库（SQLite 实盘 + DuckDB 回测批量读取）。

架构：
    - SQLite 作为唯一写入目标（实盘增量同步写入）
    - DuckDB sqlite_scan() 在回测时直接列式读取 SQLite（避免双写）
    - 所有下游（扫描/回测）只读此 Store，不直接调外部 API

表结构：
    bars       — OHLCV 主表，PRIMARY KEY (symbol, timestamp, timeframe)
    sync_state — 各标的同步状态，记录 last_synced_ts 和 data_quality
"""

from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Generator

import pandas as pd
from loguru import logger

# DuckDB 可选（仅回测批量读取用）
try:
    import duckdb
    _DUCKDB_AVAILABLE = True
except ImportError:
    _DUCKDB_AVAILABLE = False
    logger.warning("duckdb not installed; get_bars_multi will fall back to sqlite")


# ---------------------------------------------------------------------------
# DDL
# ---------------------------------------------------------------------------

_DDL_BARS = """
CREATE TABLE IF NOT EXISTS bars (
    symbol      TEXT      NOT NULL,
    timestamp   TEXT      NOT NULL,   -- ISO 8601 UTC date string, e.g. '2024-01-02'
    timeframe   TEXT      NOT NULL,   -- '1d' / '1h' / '15m'
    open        REAL      NOT NULL,
    high        REAL      NOT NULL,
    low         REAL      NOT NULL,
    close       REAL      NOT NULL,
    volume      REAL      NOT NULL,
    adjusted    INTEGER   DEFAULT 1,
    source      TEXT      DEFAULT 'unknown',
    PRIMARY KEY (symbol, timestamp, timeframe)
);
CREATE INDEX IF NOT EXISTS idx_bars_sym_tf_ts
    ON bars(symbol, timeframe, timestamp);
"""

_DDL_SYNC_STATE = """
CREATE TABLE IF NOT EXISTS sync_state (
    symbol          TEXT NOT NULL,
    timeframe       TEXT NOT NULL,
    last_synced_ts  TEXT,          -- ISO 8601 date string
    last_sync_run   TEXT,          -- ISO 8601 datetime string
    data_quality    TEXT DEFAULT 'ok',  -- 'ok' | 'degraded'
    PRIMARY KEY (symbol, timeframe)
);
"""


# ---------------------------------------------------------------------------
# MarketDataStore
# ---------------------------------------------------------------------------

class MarketDataStore:
    """本地时序库，统一读写接口。

    Args:
        db_path: SQLite 文件路径，默认 ~/.mytrader/market_data.db
    """

    def __init__(self, db_path: str | Path | None = None) -> None:
        if db_path is None:
            default_dir = Path.home() / ".mytrader"
            default_dir.mkdir(parents=True, exist_ok=True)
            db_path = default_dir / "market_data.db"
        self._db_path = Path(db_path)
        self._local = threading.local()  # thread-local connections
        self._init_db()

    # ------------------------------------------------------------------
    # 连接管理
    # ------------------------------------------------------------------

    def _get_conn(self) -> sqlite3.Connection:
        """获取当前线程的 SQLite 连接（thread-local，避免多线程竞争）。"""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")   # 允许并发读
            conn.execute("PRAGMA synchronous=NORMAL")
            self._local.conn = conn
        return self._local.conn

    @contextmanager
    def _tx(self) -> Generator[sqlite3.Connection, None, None]:
        """事务上下文管理器。"""
        conn = self._get_conn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def _init_db(self) -> None:
        """建表（幂等）。"""
        with self._tx() as conn:
            conn.executescript(_DDL_BARS)
            conn.executescript(_DDL_SYNC_STATE)
        logger.debug(f"[MarketDataStore] initialized: {self._db_path}")

    # ------------------------------------------------------------------
    # 写入
    # ------------------------------------------------------------------

    def upsert_bars(
        self,
        symbol: str,
        df: pd.DataFrame,
        timeframe: str = "1d",
        source: str = "unknown",
    ) -> int:
        """增量写入（按主键 upsert 去重），返回新增行数。

        Args:
            symbol:    股票代码
            df:        含 open/high/low/close/volume 列的 DataFrame，index 为 date/datetime
            timeframe: 时间周期
            source:    数据来源标识（'alpaca' / 'yfinance'）

        Returns:
            本次实际写入的行数（已存在的行不计入）
        """
        if df.empty:
            return 0

        # 统一 index 为字符串日期
        df = df.copy()
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        ts_strings = df.index.strftime("%Y-%m-%d")

        # 标准化列名（兼容大小写）
        df.columns = [c.lower() for c in df.columns]

        rows = [
            (
                symbol,
                ts,
                timeframe,
                float(row["open"]),
                float(row["high"]),
                float(row["low"]),
                float(row["close"]),
                float(row["volume"]),
                1,      # adjusted
                source,
            )
            for ts, row in zip(ts_strings, df.to_dict(orient="records"))
        ]

        sql = """
            INSERT OR REPLACE INTO bars
                (symbol, timestamp, timeframe, open, high, low, close, volume, adjusted, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        with self._tx() as conn:
            before = conn.execute(
                "SELECT COUNT(*) FROM bars WHERE symbol=? AND timeframe=?",
                (symbol, timeframe),
            ).fetchone()[0]
            conn.executemany(sql, rows)
            after = conn.execute(
                "SELECT COUNT(*) FROM bars WHERE symbol=? AND timeframe=?",
                (symbol, timeframe),
            ).fetchone()[0]

        new_rows = after - before
        logger.debug(f"[upsert_bars] {symbol}/{timeframe}: +{new_rows} rows (total {after})")
        return new_rows

    # ------------------------------------------------------------------
    # 读取（实盘 — SQLite 行式）
    # ------------------------------------------------------------------

    def get_bars(
        self,
        symbol: str,
        start: date,
        end: date,
        timeframe: str = "1d",
    ) -> pd.DataFrame:
        """读取单只标的指定区间的 OHLCV 数据（本地，无网络）。"""
        sql = """
            SELECT timestamp, open, high, low, close, volume
            FROM bars
            WHERE symbol=? AND timeframe=?
              AND timestamp >= ? AND timestamp <= ?
            ORDER BY timestamp
        """
        conn = self._get_conn()
        rows = conn.execute(
            sql,
            (symbol, timeframe, start.isoformat(), end.isoformat()),
        ).fetchall()
        return self._rows_to_df(rows)

    def get_latest_n_bars(
        self,
        symbol: str,
        n: int = 90,
        timeframe: str = "1d",
    ) -> pd.DataFrame:
        """读取最近 N 根 bar（实盘扫描用）。"""
        sql = """
            SELECT timestamp, open, high, low, close, volume
            FROM bars
            WHERE symbol=? AND timeframe=?
            ORDER BY timestamp DESC
            LIMIT ?
        """
        conn = self._get_conn()
        rows = conn.execute(sql, (symbol, timeframe, n)).fetchall()
        df = self._rows_to_df(rows)
        return df.sort_index()  # 倒序取后恢复正序

    # ------------------------------------------------------------------
    # 读取（回测 — DuckDB 批量）
    # ------------------------------------------------------------------

    def get_bars_multi(
        self,
        symbols: list[str],
        start: date,
        end: date,
        timeframe: str = "1d",
    ) -> dict[str, pd.DataFrame]:
        """批量读取多只标的（回测用）。

        优先用 DuckDB sqlite_scan() 列式读取；若 duckdb 未安装则 fallback 到逐只 SQLite 查询。
        """
        if _DUCKDB_AVAILABLE:
            return self._get_bars_multi_duckdb(symbols, start, end, timeframe)
        else:
            return {
                s: self.get_bars(s, start, end, timeframe)
                for s in symbols
            }

    def _get_bars_multi_duckdb(
        self,
        symbols: list[str],
        start: date,
        end: date,
        timeframe: str,
    ) -> dict[str, pd.DataFrame]:
        """DuckDB sqlite_scan 批量读取。"""
        db_path_str = str(self._db_path)
        placeholders = ", ".join("?" * len(symbols))
        sql = f"""
            INSTALL sqlite;
            LOAD sqlite;
            SELECT symbol, timestamp, open, high, low, close, volume
            FROM sqlite_scan('{db_path_str}', 'bars')
            WHERE symbol IN ({placeholders})
              AND timeframe = ?
              AND timestamp >= ?
              AND timestamp <= ?
            ORDER BY symbol, timestamp
        """
        try:
            con = duckdb.connect()
            con.execute("INSTALL sqlite; LOAD sqlite;")
            df_all = con.execute(
                f"""
                SELECT symbol, timestamp, open, high, low, close, volume
                FROM sqlite_scan('{db_path_str}', 'bars')
                WHERE symbol IN ({placeholders})
                  AND timeframe = ?
                  AND timestamp >= ?
                  AND timestamp <= ?
                ORDER BY symbol, timestamp
                """,
                [*symbols, timeframe, start.isoformat(), end.isoformat()],
            ).df()
            con.close()
        except Exception as e:
            logger.warning(f"[get_bars_multi] DuckDB failed ({e}), falling back to SQLite")
            return {s: self.get_bars(s, start, end, timeframe) for s in symbols}

        result: dict[str, pd.DataFrame] = {}
        for sym, grp in df_all.groupby("symbol"):
            grp = grp.drop(columns=["symbol"]).copy()
            grp["timestamp"] = pd.to_datetime(grp["timestamp"])
            grp = grp.set_index("timestamp")
            grp.index.name = "date"
            result[str(sym)] = grp
        return result

    # ------------------------------------------------------------------
    # 同步状态
    # ------------------------------------------------------------------

    def get_last_synced(
        self, symbol: str, timeframe: str = "1d"
    ) -> date | None:
        """返回该标的已同步到的最新日期，None 表示从未同步。"""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT last_synced_ts FROM sync_state WHERE symbol=? AND timeframe=?",
            (symbol, timeframe),
        ).fetchone()
        if row is None or row[0] is None:
            return None
        return date.fromisoformat(row[0])

    def set_last_synced(
        self,
        symbol: str,
        ts: date,
        timeframe: str = "1d",
        data_quality: str = "ok",
    ) -> None:
        """更新同步状态。"""
        now = datetime.utcnow().isoformat()
        sql = """
            INSERT INTO sync_state (symbol, timeframe, last_synced_ts, last_sync_run, data_quality)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(symbol, timeframe) DO UPDATE SET
                last_synced_ts = excluded.last_synced_ts,
                last_sync_run  = excluded.last_sync_run,
                data_quality   = excluded.data_quality
        """
        with self._tx() as conn:
            conn.execute(sql, (symbol, timeframe, ts.isoformat(), now, data_quality))

    def get_data_quality(self, symbol: str, timeframe: str = "1d") -> str:
        """返回最近一次同步的数据质量标记（'ok' / 'degraded'）。"""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT data_quality FROM sync_state WHERE symbol=? AND timeframe=?",
            (symbol, timeframe),
        ).fetchone()
        return row[0] if row else "unknown"

    # ------------------------------------------------------------------
    # 辅助
    # ------------------------------------------------------------------

    @staticmethod
    def _rows_to_df(rows: list) -> pd.DataFrame:
        """将 SQLite 查询结果转为标准 DataFrame。"""
        if not rows:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
        df = pd.DataFrame(
            [(r[0], r[1], r[2], r[3], r[4], r[5]) for r in rows],
            columns=["date", "open", "high", "low", "close", "volume"],
        )
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")
        df.index.name = "date"
        return df

    def count_bars(self, symbol: str, timeframe: str = "1d") -> int:
        """返回某标的/周期的总行数（调试/测试用）。"""
        conn = self._get_conn()
        return conn.execute(
            "SELECT COUNT(*) FROM bars WHERE symbol=? AND timeframe=?",
            (symbol, timeframe),
        ).fetchone()[0]

    def close(self) -> None:
        """关闭当前线程的连接。"""
        if hasattr(self._local, "conn") and self._local.conn:
            self._local.conn.close()
            self._local.conn = None
