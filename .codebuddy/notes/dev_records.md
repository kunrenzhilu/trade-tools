# MyTrader 开发记录

> 记录每个开发阶段的详细实现内容、关键决策和新增文件。  
> 由 CODEBUDDY.md §5 引用，开发时优先查阅本文件。

---

## Phase 1（2026-06-13）✅

**主题**：Data Layer + Strategy Engine + VectorBT 回测

### 新增模块
| 模块 | 文件 |
|------|------|
| Data Layer | `data/providers/yfinance_provider.py`、`data/cleaner.py`、`data/validator.py`、`data/cache.py` |
| Strategy Engine | `strategy/strategies/dual_ma.py`、`rsi_mean_reversion.py`、`macd_crossover.py`、`bollinger_bands.py` |
| 指标库 | `strategy/indicators.py`（pandas-ta 封装）|
| Backtest | `backtest/runner.py`（BacktestRunner + BacktestConfig + BacktestResult）、`backtest/report.py` |

### 关键设计决策
| 决策 | 说明 |
|------|------|
| 策略函数签名 | `(close: pd.Series, **params) -> pd.Series`，纯函数，不依赖外部状态 |
| 前视偏差防护 | 所有策略强制 `shift(1)`，4 个专项破坏性测试验证 |
| 回测/实盘一致 | 策略函数同时被 `BacktestRunner` 和未来实盘引擎调用 |
| 指标库 | `indicators.py` 封装 pandas-ta，对外接口不变，策略层无感知 |
| 数据缓存 | Parquet，路径 `~/.mytrader/cache/yfinance/{symbol}/{timeframe}/` |
| 执行价格 | 回测用 `open=open_series`，信号在下一 bar 开盘价执行 |
| Signal 值 | 1=BUY，-1=SELL，0=HOLD（int 类型） |

### VectorBT 1.0.0 破坏性变更
```python
# ❌ 旧版（不可用）
size_type="valuepercent"
pf.stats()["Annualized Return"]

# ✅ 1.0.0 正确写法
size_type="Percent"
pf.stats()["Benchmark Return [%]"]  # Annualized Return 字段已移除
```

### 回测验证结果（AAPL 2022–2025）
| 策略 | 总回报 | Sharpe | MaxDD |
|------|--------|--------|-------|
| 布林带均值回归 | +44.5% | 0.96 | 20.5% |
| MACD 交叉 | +36.9% | 0.87 | 20.0% |
| RSI 均值回归 | +19.3% | 0.47 | 26.0% |
| 双均线 | +15.9% | 0.46 | 20.7% |
| 买入持有基准 | +39.8% | — | — |

双均线最优参数：`fast=5, slow=60`，Sharpe 1.06，Calmar 1.17。

**测试数：108 passed**

---

## Phase 2（2026-06-14）✅

**主题**：Signal Filter + Risk Manager + Paper Broker + Portfolio Tracker

### 新增模块
| 模块 | 文件 |
|------|------|
| Signal Filter | `signal/filters/`（volume/atr/sentiment/time_window/cooldown）、`signal/pipeline.py` |
| Risk Manager | `risk/position_sizer.py`、`risk/stop_loss.py`、`risk/circuit_breaker.py`、`risk/constraints.py` |
| Paper Broker | `execution/paper_broker.py` |
| Portfolio Tracker | `portfolio/tracker.py`、`portfolio/models.py` |

### 关键设计决策
- Signal Filter：过滤管道可插拔，通过配置开关（volume/ATR/cooldown/time_window）
- Risk Manager：ATR 仓位法为主，固定金额/固定比例为辅；三层熔断（日/周/月）
- PaperBroker：下一 bar 开盘价模拟成交，与 BacktestRunner 语义一致

**测试数：94 passed（累计 202）**

---

## Phase 3（2026-06-21）✅

**主题**：AlpacaBroker + IBKRBroker + 通知推送 + 调度器 + Monitor Layer + 对账

### 新增模块
| 模块 | 文件 | 说明 |
|------|------|------|
| 依赖注入容器 | `infra/container.py` | `Container.build(config)` 工厂，根据 mode 装配 Broker |
| 定时调度器 | `infra/scheduler.py` | APScheduler 4 个定时 job（盘前/盘中/盘后/对账） |
| Alpaca 经纪商 | `execution/alpaca_broker.py` | 美股，semi_auto/auto 双模式，零佣金 |
| IBKR 经纪商 | `execution/ibkr_broker.py` | 港美股，ib_insync，readonly 保护 |
| 通知服务 | `execution/notification.py` | Telegram + 企业微信，冷却期去重 |
| 健康检查 | `monitor/health_checker.py` | 4 项检查，返回 HealthReport |
| 日志配置 | `monitor/logger_setup.py` | loguru 按日轮转，JSON 序列化 |
| 对账服务 | `portfolio/reconciliation.py` | 本地 vs 券商持仓核对，差异告警 |

### 执行模式
| 模式 | Broker | 说明 |
|------|--------|------|
| `paper` | PaperBroker | 下一 bar 开盘价模拟成交（默认） |
| `semi_auto` | AlpacaBroker | 返回 PENDING + 推送通知，人工确认 |
| `auto` | AlpacaBroker/IBKRBroker | 直接调用 API 下单 |

### .env 变量格式（Pydantic nested 风格）
```bash
ALPACA__API_KEY=xxx
ALPACA__SECRET_KEY=xxx
NOTIFICATION__TELEGRAM_ENABLED=true
NOTIFICATION__TELEGRAM_BOT_TOKEN=xxx
EXECUTION__MODE=semi_auto
```

**测试数：142 passed（累计 344）**

---

## Phase 4（2026-06-21）✅

**主题**：AlpacaDataProvider + ScanOrchestrator + Streamlit Dashboard + watchlist 配置

### 新增模块
| 模块 | 文件 | 说明 |
|------|------|------|
| Alpaca 数据源 | `data/providers/alpaca_provider.py` | 对接 `v2/delayed_sip`（15min 延迟，免费全量 SIP） |
| 扫描编排器 | `scan_orchestrator.py` | 连接全链路，`morning_scan` / `intraday_scan` / `eod_check` |
| Streamlit 面板 | `monitor/dashboard/app.py` | 可视化持仓、信号、健康状态 |

### main.py 新增参数
```bash
python main.py --scan-now morning   # 立即执行一次盘前扫描（调试用）
```

### WatchlistConfig（新增配置项）
```yaml
watchlist:
  symbols: ["AAPL", "MSFT", "TSLA", "NVDA", "SPY"]
  lookback_days: 90
  max_concurrent_symbols: 5
```

**测试数：38 passed（累计 382）**

---

## Phase 5（2026-06-23）✅

**主题**：大规模选股基础设施 — MarketDataStore + UniverseManager + 矩阵扫描 + 矩阵回测 + Walk-Forward 调度

### 背景

Phase 1-4 采用"固定几只标的 × 单策略 → 直接下单"线性流水线。  
Phase 5 升级为 v2 双层架构：**离线回测层**（每月 Walk-Forward）+ **在线交易层**（每日 16 次扫描）。  
设计依据：`designs/design_v2/`（v2.1 版本，含 claude_review.md 修订）。

### 新增文件
```
mytrader/mytrader/
├── data/store/
│   ├── market_data_store.py    # SQLite 写 + DuckDB sqlite_scan 读
│   ├── sync_service.py         # 增量同步（fallback 不写混源数据）
│   └── models.py               # SyncReport
├── universe/
│   ├── manager.py              # UniverseManager（含历史分组接口）
│   ├── constituents.py         # Wikipedia 抓取 + CSV 兜底
│   ├── grouping.py             # 波动率分层（ATR% 分位）+ group_id 构建
│   └── models.py               # SymbolMeta
├── strategy/
│   └── matrix_runner.py        # StrategyMatrixRunner（信号有效期 3bar）
├── signal/
│   └── ranker.py               # SignalRanker（冲突聚合 + Top-2K 候选）
├── risk/
│   └── candidate_selector.py   # 5 级约束递补选股
└── backtest/
    └── matrix_backtest.py      # MatrixBacktest（组合 Sharpe + open 参数）

tests/
├── test_market_data_store.py   # 20 个测试
├── test_universe_manager.py    # 18 个测试
├── test_strategy_matrix_ranker.py  # 19 个测试
└── test_matrix_backtest.py     # 17 个测试

examples/
└── phase5_e2e.py               # 端到端干跑脚本
doc/
└── phase5-summary.md           # 详细开发总结
```

### 修改文件
| 文件 | 修改内容 |
|------|---------|
| `backtest/runner.py` | `BacktestResult` 增加 `daily_returns: pd.Series` 字段 |
| `infra/scheduler.py` | 增加 `on_monthly_reoptimize` 回调 + 每月第一个交易日 00:00 ET job |
| `main.py` | 增加 `--reoptimize`（立即触发矩阵回测）、`--backfill`（首次回填 5 年数据）参数 |
| `designs/design_v2/` | 7 个文档按 claude_review.md 修订（v2.1），CHANGELOG 记录所有变更 |

### 核心设计点

**1. 信号有效期（解决事件型信号漏单）**
```python
# 检查最近 N bar 内是否有非零信号（默认 N=3）
recent = sig_series.iloc[-signal_valid_bars:]
nonzero = recent[recent != 0]
if nonzero.empty:
    continue   # 无信号，跳过
latest = int(nonzero.iloc[-1])  # 取最近一次有效信号方向
```

**2. Top-2K 递补机制**
- SignalRanker 输出 `top_k × 2 = 10` 个 BUY 候选
- CandidateSelector 按 5 级约束逐个尝试，sector 超限时跳过递补下一候选
- SELL 信号不受 Top-K 限制

**3. 组合 Sharpe（修复组内平均 Sharpe 计算错误）**
```python
# ❌ 错误（Sharpe 是比率，不能直接平均）
avg_sharpe = mean([r.sharpe for r in results])

# ✅ 正确（等权合并日收益率序列，计算组合 Sharpe）
returns_df = pd.concat([r.daily_returns for r in results], axis=1)
portfolio_sharpe = compute_sharpe(returns_df.mean(axis=1))
```

**4. Fallback 不写入混源数据**
- 主源（Alpaca）无数据时标记 `data_quality=degraded`，**不写入 yfinance 数据**
- 防止不同来源的复权基准混用导致价格跳变

### 首次启动顺序
```bash
python main.py --backfill       # 回填 5 年历史数据（约 5-10 分钟）
python main.py --reoptimize     # 产出 config/strategy_weights.json
python examples/phase5_e2e.py   # 端到端干跑验证
python main.py --mode paper     # 启动全自动调度
```

### 遗留待完成（Phase 6 方向）
| 项目 | 说明 |
|------|------|
| AlpacaDataProvider 替换 yfinance | `--backfill` 目前用 yfinance，切换需 Alpaca API Key |
| Walk-Forward 历史分组 | `recompute_volatility_tiers_at()` 已实现但未接入矩阵回测 |
| Ensemble 权重网格搜索 | 目前用 Sharpe 归一化简化；严格版需在离散投票序列上搜索 |
| 幸存者偏差修复 | 需历史成分股快照数据源（Polygon.io 等） |
| AlpacaBroker auto 模式端到端验证 | 需真实 Alpaca Paper 账户 |
| 对账真实集成 | Alpaca/IBKR `get_positions` 接入 |

**测试数：85 passed（累计 467）**  
**详细总结：`doc/phase5-summary.md`**

---

*本文件记录开发详情，每完成一个 Phase 在此追加记录。*
