# Phase 5 开发计划

> 制定日期：2026-06-23  
> 设计依据：`designs/design_v2/`（v2.1 修订版）  
> Python 环境：`/Users/rickouyang/miniforge3/envs/py312trade`  
> 当前测试基线：382 passed，0 failed

---

## 0. Phase 5 目标

扫描 S&P 500 + Nasdaq 100（约 550 只） → 每日选出 Top-5 信号 → 全自动执行

核心新增能力：
1. **本地时序数据库**（MarketDataStore）：增量同步，盘中零网络延迟读取
2. **标的池管理**（UniverseManager）：成分股维护 + 波动率分组
3. **策略矩阵运行器**（StrategyMatrixRunner）：550 只 × 多策略并行扫描（亚秒级）
4. **信号排名器**（SignalRanker）：多策略冲突聚合 + Top-2K 候选 → Risk Manager 递补
5. **矩阵回测**（MatrixBacktest）：N策略 × G组 × 参数网格 → strategy_weights.json
6. **Walk-Forward 月度调度**：每月重优化策略权重

---

## 1. 开发任务拆分

### Sprint 1 — 数据基础层（约 3-4 天）

> 目标：建立本地时序库，支持全量回填和增量同步

#### Task 1.1 MarketDataStore（`mytrader/data/store/market_data_store.py`）

```python
class MarketDataStore:
    upsert_bars(symbol, df, timeframe, source) -> int
    get_bars(symbol, start, end, timeframe) -> pd.DataFrame
    get_latest_n_bars(symbol, n, timeframe) -> pd.DataFrame
    get_bars_multi(symbols, start, end, timeframe) -> dict[str, pd.DataFrame]  # DuckDB
    get_last_synced(symbol, timeframe) -> date | None
    set_last_synced(symbol, ts, timeframe, data_quality) -> None
```

关键实现点：
- SQLite 表：`bars`（含 `source` 字段）+ `sync_state`（含 `data_quality` 字段）
- `get_bars_multi` 用 DuckDB `sqlite_scan()` 批量读取（回测专用）
- PRIMARY KEY `(symbol, timestamp, timeframe)` 保证 upsert 幂等

验收条件：
- [ ] upsert 1000 行数据，重复插入后总行数不变
- [ ] `get_latest_n_bars(n=90)` 返回正确行数
- [ ] `get_bars_multi(["AAPL","MSFT"], ...)` 返回字典，两只各有数据

#### Task 1.2 DataSyncService（`mytrader/data/store/sync_service.py`）

```python
class DataSyncService:
    sync_symbol(symbol, timeframe) -> int          # 增量同步单只
    sync_all(symbols, timeframe, max_workers) -> SyncReport   # 并发同步
    backfill(symbols, years, timeframe) -> SyncReport         # 首次回填
```

关键实现点：
- Fallback 策略：Alpaca 无数据时标记 `data_quality=degraded`，**不写入混源数据**（见 design 10-market-data-store.md §8.2）
- 并发：ThreadPoolExecutor，max_workers=8
- 限速：Alpaca 批量请求每批 50 只，批次间 sleep 0.3s

验收条件：
- [ ] sync 单只 AAPL，本地库有 5 年日线
- [ ] sync_all 10 只，耗时 < 5s（含网络）
- [ ] Alpaca 限速时 fallback 到 yfinance，data_quality 标记为 degraded

测试文件：`tests/test_market_data_store.py`（预计 15 个测试）

---

### Sprint 2 — 标的池管理（约 2 天）

> 目标：S&P 500 + Nasdaq 100 成分股管理，按波动率×指数分组

#### Task 2.1 UniverseManager（`mytrader/universe/manager.py`）

```python
class UniverseManager:
    get_universe() -> list[str]                              # ~550 只
    get_symbol_meta(symbol) -> SymbolMeta
    get_groups() -> dict[str, list[str]]                     # {group_id: [symbols]}
    refresh_constituents() -> None                           # 每月更新成分股
    recompute_volatility_tiers(lookback_days=60) -> None    # 当前时点分组
    recompute_volatility_tiers_at(as_of_date, lookback_days=60) -> dict[str, str]  # 历史分组
```

关键实现点：
- Phase 5 初期：从 Wikipedia 抓取 S&P 500，从 Nasdaq 官网抓取 Nasdaq 100
- 去重：同时属于两个指数的标的（如 AAPL）`group_id` 唯一（Nasdaq 优先）
- 波动率分层：基于 ATR(14)/close 近 60 日均值，三分位划分（high/mid/low）
- **历史分组接口** `recompute_volatility_tiers_at()` 供矩阵回测 point-in-time 使用

验收条件：
- [ ] `get_universe()` 返回 500-600 只
- [ ] `get_groups()` 返回至少 6 个 group（2个指数 × 3个波动率层）
- [ ] `recompute_volatility_tiers_at("2023-01-01")` 与今日分组可能不同（TSLA 验证）

测试文件：`tests/test_universe_manager.py`（预计 10 个测试）

---

### Sprint 3 — 策略矩阵运行器（约 2 天）

> 目标：对全标的池批量运行分组策略，亚秒级完成

#### Task 3.1 StrategyMatrixRunner（`mytrader/strategy/matrix_runner.py`）

```python
class StrategyMatrixRunner:
    run(lookback_days=90, max_workers=8) -> MatrixScanResult
    run_symbol(symbol, lookback_days=90) -> list[Signal]
    reload_weights() -> None     # 热加载 strategy_weights.json
```

关键实现点：
- 信号有效期：检查最近 `signal_valid_bars`（默认 3）个 bar 内是否有非零信号（解决事件型信号漏单）
- 传入完整 df（`strategy_fn(df["close"], df=df, **params)`），兼容需要 high/low/volume 的策略
- 并发：ThreadPoolExecutor，max_workers=8
- 所有数据读本地库（MarketDataStore），无网络 IO

验收条件：
- [ ] 加载真实 strategy_weights.json，对 10 只标的运行，返回 Signal 列表
- [ ] 550 只标的完整扫描耗时 < 2s
- [ ] `signal_valid_bars=3`：策略 3 天前金叉，今日仍能产生 BUY 信号

测试文件：`tests/test_strategy_matrix_runner.py`（预计 12 个测试）

---

### Sprint 4 — 信号排名器（约 2 天）

> 目标：多策略信号聚合 + 排名 + 输出 Top-2K 候选

#### Task 4.1 SignalRanker（`mytrader/signal/ranker.py`）

```python
class SignalRanker:
    rank(signals: list[Signal]) -> RankingReport
    _aggregate_by_symbol(signals) -> list[Signal]   # 冲突解决（加权投票）
    _score(signal) -> tuple[float, dict]             # 综合得分
```

关键实现点：
- **聚合**：同标的多策略加权投票（`combined = Σ(direction_i × weight_i × confidence_i)`）
- **Top-2K**：输出 `top_k × candidates_multiplier` 个候选（默认 `5×2=10`），供 Risk Manager 递补
- **SELL 不受 Top-K 限制**：持仓平仓优先，SELL 全部透传
- **分组排名**：BUY/SELL 分别排名，SELL 优先处理

验收条件：
- [ ] 同标的 dual_ma BUY + macd SELL → 聚合后按权重决定方向或丢弃
- [ ] 输出候选数 = min(有效信号数, top_k * 2)
- [ ] SELL 信号不被 Top-K 过滤

测试文件：`tests/test_signal_ranker.py`（预计 10 个测试）

---

### Sprint 5 — Risk Manager 递补机制（约 1 天）

> 目标：接收 Top-2K 候选，逐个尝试，递补直到约束用尽

#### Task 5.1 更新 RiskManager（`mytrader/risk/constraints.py`）

在现有 `constraints.py` 中新增递补逻辑：

```python
def select_orders_from_candidates(
    candidates: list[RankedSignal],
    account: AccountState,
    config: RiskConfig,
    max_orders: int = 5,
) -> tuple[list[OrderIntent], list[str]]:   # (approved, rejection_reasons)
    """
    按约束优先级逐个尝试候选信号：
      1. max_total_exposure_pct
      2. max_sector_exposure_pct  → 被拒则递补下一个
      3. max_concurrent_positions
      4. max_single_position_pct  → 截断（取 min），不拒绝
      5. min_order_value
    """
```

验收条件：
- [ ] Top-10 候选中 3 只科技股触发 sector 限制，自动递补第 4/5/6 候选
- [ ] ATR 仓位法结果 35% → 截断为 20%，不拒绝

测试文件：`tests/test_risk_constraints.py`（新增约 8 个测试）

---

### Sprint 6 — 矩阵回测（约 3 天）

> 目标：N策略 × G组 × 参数网格 → strategy_weights.json

#### Task 6.1 MatrixBacktest（`mytrader/backtest/matrix_backtest.py`）

```python
def run_matrix_backtest(
    universe: UniverseManager,
    store: MarketDataStore,
    strategies: list[str],
    param_grids: dict,
    years: int = 5,
) -> dict:   # → strategy_weights.json 内容
```

关键实现点：
- **组合 Sharpe 计算**：等权合并组内日收益率 `pd.concat([r.daily_returns], axis=1).mean(axis=1)` 计算组合 Sharpe（不能取各标的 Sharpe 的算术平均）
- **历史分组**：每次回测月份点调用 `universe.recompute_volatility_tiers_at(date)` 获取 point-in-time 分组（而非静态当前分组）
- **open 参数**：所有 `vbt.Portfolio.from_signals()` 必须传 `open=data[s]["open"]`
- **ensemble 语义**：权重优化在"单点离散值加权投票"语义下进行（与实盘 `run_symbol` 一致）
- **幸存者偏差注释**：回测报告中输出当前成分股快照 + 已知偏差提示

验收条件：
- [ ] 对 NDX 高波动组（10 只 mock 标的）× 2 策略 × 5 参数组合 → 产出 strategy_weights.json
- [ ] 组合 Sharpe 用日收益率序列计算，单只 Sharpe 算术平均会偏离 > 5%（测试验证）
- [ ] open 参数传入后，回测结果与只用 close 的结果有可测量差异

测试文件：`tests/test_matrix_backtest.py`（预计 15 个测试）

#### Task 6.2 更新 BacktestResult（`mytrader/backtest/runner.py`）

```python
@dataclass
class BacktestResult:
    portfolio: vbt.Portfolio
    stats: pd.Series
    daily_returns: pd.Series   # 新增：pf.returns()，供组合 Sharpe 计算
```

---

### Sprint 7 — Walk-Forward 调度集成（约 1 天）

> 目标：每月第一个交易日自动重优化策略权重

#### Task 7.1 更新 TradingScheduler（`mytrader/infra/scheduler.py`）

在现有 `scheduler.py` 中增加月度 job：

```python
# 每月第一个交易日 00:00 ET（需 pandas_market_calendars 判断）
scheduler.add_job(
    run_matrix_backtest_job,
    trigger="cron",
    day_of_week="mon-fri",
    hour=0, minute=0,
    timezone="America/New_York",
    id="monthly_matrix_backtest",
)
```

验收条件：
- [ ] `--reoptimize` CLI 参数手动触发 MatrixBacktest（测试用）
- [ ] MatrixBacktest 完成后自动调用 `matrix_runner.reload_weights()`

---

### Sprint 8 — 端到端集成与测试（约 2 天）

> 目标：全链路联调，干跑验证

#### Task 8.1 更新 main.py

```bash
# 新增参数
python main.py --mode paper --scan-now        # 立即运行一次全量扫描
python main.py --mode paper --reoptimize      # 立即触发 MatrixBacktest
python main.py --mode paper --backfill        # 首次回填 5 年历史
```

#### Task 8.2 干跑验证脚本（`examples/phase5_e2e.py`）

```python
# 端到端测试（paper mode，不真实下单）
store = MarketDataStore(...)
universe = UniverseManager(store)
runner = StrategyMatrixRunner(store, universe)
ranker = SignalRanker(top_k=5)

# 模拟一天的完整流程
scan_result = runner.run(lookback_days=90)
ranking = ranker.rank(scan_result.signals)
# ... 输出 Top-K 及各步骤统计
```

---

## 2. 依赖安装

```bash
/Users/rickouyang/miniforge3/envs/py312trade/bin/pip install duckdb pandas-market-calendars
```

| 包 | 用途 | 是否已安装 |
|----|------|-----------|
| `duckdb` | MatrixBacktest 批量读取、sqlite_scan | ❌ 待安装 |
| `pandas-market-calendars` | 判断交易日、半天交易日 | ❌ 待安装（可选） |

---

## 3. 目录结构变化（Phase 5 新增）

```
mytrader/mytrader/
├── data/
│   └── store/                      # [NEW Sprint 1]
│       ├── __init__.py
│       ├── market_data_store.py    # MarketDataStore
│       ├── sync_service.py         # DataSyncService
│       └── models.py               # SyncReport / BarRow
├── universe/                       # [NEW Sprint 2]
│   ├── __init__.py
│   ├── manager.py                  # UniverseManager
│   ├── constituents.py             # 成分股抓取
│   ├── grouping.py                 # 波动率/行业分组
│   └── models.py                   # SymbolMeta
├── strategy/
│   └── matrix_runner.py            # [NEW Sprint 3] StrategyMatrixRunner
├── signal/
│   └── ranker.py                   # [NEW Sprint 4] SignalRanker
│   └── models.py                   # [MODIFIED] 增加 RankedSignal / RankingReport
├── risk/
│   └── constraints.py              # [MODIFIED Sprint 5] 增加递补逻辑
├── backtest/
│   ├── runner.py                   # [MODIFIED Sprint 6] BacktestResult 增加 daily_returns
│   └── matrix_backtest.py          # [NEW Sprint 6] MatrixBacktest
└── infra/
    ├── scheduler.py                # [MODIFIED Sprint 7] 增加月度 MatrixBacktest job
    └── config.py                   # [MODIFIED Sprint 1] 增加 v2 配置节

config/
├── default.yaml                    # [MODIFIED Sprint 1] 增加 v2 配置节
├── universe.csv                    # [NEW Sprint 2] 成分股缓存
└── strategy_weights.json           # [NEW Sprint 6] MatrixBacktest 产出

tests/
├── test_market_data_store.py       # [NEW Sprint 1] ~15 个
├── test_universe_manager.py        # [NEW Sprint 2] ~10 个
├── test_strategy_matrix_runner.py  # [NEW Sprint 3] ~12 个
├── test_signal_ranker.py           # [NEW Sprint 4] ~10 个
├── test_risk_constraints.py        # [MODIFIED Sprint 5] +8 个
└── test_matrix_backtest.py         # [NEW Sprint 6] ~15 个

examples/
└── phase5_e2e.py                   # [NEW Sprint 8] 端到端干跑
```

---

## 4. 测试策略

### 4.1 单元测试原则

- 所有网络 IO Mock（MarketDataStore、UniverseManager、外部 API）
- 使用 SQLite in-memory（`:memory:`）作为测试数据库
- 策略函数测试继续复用 Phase 1 的 fixture

### 4.2 关键边界测试（必须覆盖）

| 场景 | 测试描述 |
|------|---------|
| 信号有效期 | `signal_valid_bars=3`：信号发出 2 天后仍有效，4 天后失效 |
| 事件型信号 | 双均线只在金叉当天 signal=1，其余为 0，确认有效期机制生效 |
| ensemble 语义 | 回测的加权聚合与实盘 `run_symbol` 的加权逻辑一致性验证 |
| 递补机制 | sector 超限时自动取下一候选，最终持仓数不超过 K |
| 组合 Sharpe | 等权日收益率合并 vs 算术平均 Sharpe，结果差异 > 5% |
| open 参数 | 有/无 open 参数的回测结果不同（确认确实在下一 bar 开盘执行） |
| DuckDB sqlite_scan | get_bars_multi 正确读取本地 SQLite 数据 |
| fallback 策略 | Alpaca 无数据时不写入，data_quality=degraded |

### 4.3 目标测试数

```
当前基线：382 passed
Phase 5 新增：~70 个测试
目标：450+ passed，0 failed
```

---

## 5. 开发顺序与依赖关系

```
Sprint 1（MarketDataStore + DataSyncService）
    ↓ [依赖：本地库]
Sprint 2（UniverseManager）
    ↓ [依赖：分组映射]
Sprint 3（StrategyMatrixRunner）
    ↓ [依赖：矩阵扫描信号]
Sprint 4（SignalRanker）
    ↓ [并行可与 Sprint 3 同步开发]
Sprint 5（Risk Manager 递补）
    ↓ [依赖：Sprint 1+2]
Sprint 6（MatrixBacktest）
    ↓ [依赖：Sprint 1+2，产出 strategy_weights.json]
Sprint 7（Walk-Forward 调度）    ← 依赖 Sprint 6
Sprint 8（端到端集成）           ← 依赖所有 Sprint
```

---

## 6. 关键风险与预案

| 风险 | 概率 | 影响 | 预案 |
|------|------|------|------|
| 首次回填 550 只触发 Alpaca 限速 | 中 | 低（一次性操作） | 分批 50 只，批次间 sleep 1s；限速时 yfinance 补缺（标记 degraded） |
| DuckDB `sqlite_scan` 在当前版本不可用 | 低 | 中 | 降级为 Parquet export + DuckDB 原生读取，或直接 pandas read_sql |
| Wikipedia 成分股抓取失败 | 中 | 低 | 本地 CSV 兜底，手动维护 550 只列表 |
| MatrixBacktest 7 分钟超时 | 低 | 低 | 月度离线运行，7 分钟可接受；若超时可减少参数网格 |
| 回测/实盘 ensemble 语义对齐验证失败 | 中 | 高 | Sprint 6 专项测试验证，不通过不进入 Sprint 7 |
