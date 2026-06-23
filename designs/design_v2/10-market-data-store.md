# Module 10 — Market Data Store（本地时序数据库）

> 上级文档：[00-overview.md](./00-overview.md)  
> Phase 5 新增模块

---

## 1. 职责

- 作为**全系统唯一的行情数据来源**（Single Source of Truth）
- 本地持久化 OHLCV 时序数据（~550 只 × 5 年日线）
- 提供增量同步：每天收盘后只拉取新增 bar，写入本地库
- 向下游（扫描链路、回测）提供统一的本地读取接口

> **核心思想**：外部 API（Alpaca/yfinance）**只被 DataSyncService 调用**，且只请求增量数据。
> 所有扫描和回测都读本地库，不碰网络 → 避免限速，盘中读取微秒级。

---

## 2. 为什么需要本地库（而非 v1 的请求缓存）

### v1 请求缓存的缺陷

```
v1 缓存 key = (symbol, start, end, timeframe)
今天问 [3/1~5/30] → 缓存 A
明天问 [3/2~5/31] → key 变了 → 缓存未命中 → 整段 90 天重拉 ⚠️
→ 日期窗口一滑动就全量重拉 → 触发 API 限速
```

### v2 本地库 + 增量同步

```
首次：    回填 5 年（550 只 × 一次性）
每天：    每只只拉 [最新日期+1, 今天] = 通常 1 根新 bar
盘中扫描： 完全读本地库，不碰外部 API ✅
回测：    读本地库 5 年，DuckDB 列式向量化 ✅
```

**数据量评估**（证明无需 MySQL）：

```
550 只 × 5 年 × 252 交易日 = 693,000 行
每行 ≈ 60 字节 → 总计 ≈ 42 MB（极小）
```

42 MB 用嵌入式数据库（SQLite/DuckDB）足矣，无需起 MySQL 服务器。

---

## 3. 双数据库选型

| 用途 | 数据库 | 理由 |
|------|--------|------|
| **实盘扫描读取** | **SQLite** | 已在技术栈（portfolio 持久化），单文件，事务安全，行式读取适合"取单只最近 90 天" |
| **回测批量读取** | **DuckDB** | 列式存储，通过 `sqlite_scan()` 直接读 SQLite；对 42MB 数据量性能差别有限，但提供便捷的 SQL 向量化接口。若回测成为性能瓶颈，可 export Parquet 给 DuckDB 原生读取 |

> **DuckDB 写入是相对弱项**，但本系统写入是**低频**的（最快每 15 分钟一次增量），写入瓶颈可忽略。
> 读取（回测）才是性能关键路径，DuckDB 的列式读取在此场景压倒性优势。

### 两库如何协同

```
DataSyncService 写入时：
    同时 upsert 到 SQLite（实盘库）和 DuckDB（回测库）
    或：SQLite 为主库，DuckDB 定期从 SQLite 全量重建（更简单）

推荐方案（简单）：
    SQLite 为唯一写入目标（实盘 + 增量同步都写它）
    DuckDB 在回测前从 SQLite ATTACH 读取，或定期 export parquet 给 DuckDB
    （DuckDB 可直接 SELECT * FROM sqlite_scan('mytrader.db', 'bars')）
```

> DuckDB 原生支持 `sqlite_scan()` 直接查询 SQLite 文件，**可避免数据双写**——
> 实盘只写 SQLite，回测时 DuckDB 直接读 SQLite 表做列式分析。这是首选方案。

---

## 4. 数据模型

### 4.1 bars 表（OHLCV 主表）

```sql
CREATE TABLE bars (
    symbol      TEXT     NOT NULL,
    timestamp   TIMESTAMP NOT NULL,   -- UTC
    timeframe   TEXT     NOT NULL,    -- '1d' / '1h' / '15m' ...
    open        REAL     NOT NULL,
    high        REAL     NOT NULL,
    low         REAL     NOT NULL,
    close       REAL     NOT NULL,
    volume      REAL     NOT NULL,
    adjusted    INTEGER  DEFAULT 1,   -- 是否后复权
    source      TEXT,                 -- 'alpaca' / 'yfinance'
    PRIMARY KEY (symbol, timestamp, timeframe)
);

CREATE INDEX idx_bars_symbol_tf ON bars(symbol, timeframe, timestamp);
```

> PRIMARY KEY `(symbol, timestamp, timeframe)` 保证 upsert 去重——
> 同一根 bar 重复写入时覆盖而非重复插入。

### 4.2 sync_state 表（同步状态）

```sql
CREATE TABLE sync_state (
    symbol         TEXT NOT NULL,
    timeframe      TEXT NOT NULL,
    last_synced_ts TIMESTAMP,          -- 该标的已同步到的最新时间
    last_sync_run  TIMESTAMP,          -- 上次同步任务运行时间
    PRIMARY KEY (symbol, timeframe)
);
```

> 增量同步靠 `last_synced_ts` 判断从哪开始拉，避免每次都查 bars 表的 MAX(timestamp)。

---

## 5. 模块接口设计

### 5.1 MarketDataStore（本地库读写）

```python
class MarketDataStore:
    """本地时序库，统一读写接口。"""

    def __init__(self, db_url: str = "sqlite:///mytrader_data.db") -> None: ...

    # ---- 写入 ----
    def upsert_bars(self, symbol: str, df: pd.DataFrame, timeframe: str = "1d",
                    source: str = "alpaca") -> int:
        """增量写入（按主键去重），返回新增行数。"""

    # ---- 读取（实盘） ----
    def get_bars(self, symbol: str, start: date, end: date,
                 timeframe: str = "1d") -> pd.DataFrame:
        """读取单只标的指定区间（本地，无网络）。"""

    def get_latest_n_bars(self, symbol: str, n: int = 90,
                          timeframe: str = "1d") -> pd.DataFrame:
        """读取最近 N 根 bar（实盘扫描用，等价 90 天 lookback）。"""

    # ---- 读取（回测，批量） ----
    def get_bars_multi(self, symbols: list[str], start: date, end: date,
                       timeframe: str = "1d") -> dict[str, pd.DataFrame]:
        """批量读取多只标的（回测用，DuckDB 列式加速）。"""

    # ---- 同步状态 ----
    def get_last_synced(self, symbol: str, timeframe: str = "1d") -> date | None: ...
    def set_last_synced(self, symbol: str, ts: date, timeframe: str = "1d") -> None: ...
```

### 5.2 DataSyncService（增量同步器）

```python
class DataSyncService:
    """增量同步器：从外部源拉 delta，写入 MarketDataStore。

    数据源优先级：Alpaca（主） → yfinance（fallback）
    """

    def __init__(self, store: MarketDataStore,
                 primary: DataProvider,    # AlpacaDataProvider
                 fallback: DataProvider) -> None: ...   # YFinanceProvider

    def sync_symbol(self, symbol: str, timeframe: str = "1d") -> int:
        """同步单只标的：查本地最新日期 → 拉 [last+1, today] → upsert。"""

    def sync_all(self, symbols: list[str], timeframe: str = "1d",
                 max_workers: int = 8) -> SyncReport:
        """并发同步全部标的（收盘后调用）。"""

    def backfill(self, symbols: list[str], years: int = 5,
                 timeframe: str = "1d") -> SyncReport:
        """首次回填 N 年历史（一次性）。"""
```

---

## 6. 增量同步流程

```
sync_symbol(symbol):
    last = store.get_last_synced(symbol)        # 本地已同步到的日期
    if last is None:
        start = today - 5*365                    # 首次：回填 5 年
    else:
        start = last + 1 day                     # 增量：只拉新增

    df = primary.get_ohlcv(symbol, start, today) # Alpaca 主源
    if df.empty:
        # ⚠️ fallback 时不直接写入，避免复权基准不同导致价格跳变
        # 记录 WARN 日志，在 sync_state 中标记 data_quality=degraded
        # 等主源恢复后补拉（当日数据延迟不影响交易，次日正常同步即可）
        logger.warning(f"[sync] {symbol}: Alpaca 无数据，fallback yfinance（标记 degraded）")
        df = fallback.get_ohlcv(symbol, start, today)
        quality_flag = "degraded"   # 写入时附带来源标记
    else:
        quality_flag = "ok"

    n = store.upsert_bars(symbol, df, source="alpaca" if quality_flag=="ok" else "yfinance")
    store.set_last_synced(symbol, today, data_quality=quality_flag)
    return n
```

**调度时机**（接入 APScheduler）：

| 任务 | 时间（ET） | 说明 |
|------|-----------|------|
| 收盘后全量增量同步 | 16:30 | 每只拉当天新 bar，写本地库 |
| 首次回填 | 手动触发一次 | 550 只 × 5 年，约几分钟 |

> **半天交易日处理**：美股每年约 4-5 个半天交易日（感恩节次日等）13:00 收盘，16:30 同步有 3.5 小时延迟。
> 对策略无实质影响（这些日子成交量极低），但若需精确处理，可引入 `pandas_market_calendars` 库判断当日收盘时间。

---

## 7. 数据源在 v2 中的角色变化

```
v1：扫描链路 ──直接调──▶ YFinanceProvider / AlpacaDataProvider
v2：扫描链路 ──读──▶ MarketDataStore（本地）
                          ▲
                          │ 增量写入
                  DataSyncService ──调──▶ AlpacaDataProvider（主）
                                          YFinanceProvider（备）
```

> 现有的 `YFinanceProvider` / `AlpacaDataProvider` **降级为只被 DataSyncService 调用**，
> 不再被扫描链路或回测直接调用。它们的职责收窄为"从外部 API 拉原始数据"。

---

## 8. 注意点

### 8.1 Alpaca 批量请求
- Alpaca `StockBarsRequest` 支持 `symbol_or_symbols=[多只]`，一次请求多只标的
- 增量同步 550 只时，可分批（如每批 50 只）批量请求，大幅减少请求数

### 8.2 复权一致性（⚠️ 重要约束）
- Alpaca `adjustment="all"` 与 yfinance `auto_adjust=True` 都做后复权
- 但两源复权算法可能有细微差异 → 混用同一标的会导致历史价格跳变 → 均线/MACD 计算出错 → 假信号
- **强制约束**：同一标的 fallback 到 yfinance 时，当日数据不写入（标记 degraded，等主源恢复补拉）
- `source` 字段记录每根 bar 的来源，供数据质量审计

### 8.3 DuckDB 读 SQLite
- DuckDB `INSTALL sqlite; LOAD sqlite;` 后可 `sqlite_scan('mytrader_data.db', 'bars')`
- 回测时无需数据双写，DuckDB 直接列式读取 SQLite 表

### 8.4 首次回填的限速
- 首次回填 550 只 × 5 年是唯一的大批量请求场景
- 用 Alpaca 批量请求 + 适当 sleep，避免触发限速
- 回填是一次性操作，可接受较慢

---

## 9. 风险点

| 风险 | 级别 | 缓解措施 |
|------|------|---------|
| 数据源复权不一致 | 中 | source 字段标记，同标的固定数据源 |
| 增量同步遗漏交易日 | 中 | sync_state 记录 last_synced，对账时校验连续性 |
| 本地库损坏 | 低 | 定期备份 SQLite 文件；可从外部源全量重建 |
| 首次回填限速 | 低 | 批量请求 + sleep，一次性操作 |

---

## 10. 目录结构（Phase 5 待实现）

```
mytrader/
└── data/
    ├── store/
    │   ├── __init__.py
    │   ├── market_data_store.py    # MarketDataStore（SQLite + DuckDB 读取）
    │   ├── sync_service.py         # DataSyncService（增量同步）
    │   └── models.py               # SyncReport / bars schema
    ├── providers/                  # 角色收窄：只被 sync_service 调用
    │   ├── yfinance_provider.py    # fallback
    │   └── alpaca_provider.py      # primary
    ├── cleaner.py                  # 复用
    └── validator.py                # 复用
```

---

## 参考来源

- [DuckDB SQLite Extension](https://duckdb.org/docs/extensions/sqlite)
- [Alpaca Multi-Symbol Bars](https://docs.alpaca.markets/reference/stockbars)
- *Advances in Financial Machine Learning*, Ch.2 — Bars (de Prado)
