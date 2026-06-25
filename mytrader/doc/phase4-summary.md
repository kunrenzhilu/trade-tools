# Phase 4 开发总结

> 日期：2026-06-21  
> Python 环境：`/Users/rickouyang/miniforge3/envs/py312trade`（Python 3.12.13）  
> 测试结果：**382 passed（Mock: 382），0 failed**

---

## 1. Phase 4 已完成

### 1.1 新增目录结构

```
mytrader/mytrader/
├── data/
│   └── providers/
│       └── alpaca_provider.py       # [NEW] AlpacaDataProvider：Alpaca v2 Market Data API
│
├── scan_orchestrator.py             # [NEW] ScanOrchestrator：扫描编排器，连接全链路
│
└── monitor/
    └── dashboard/
        ├── __init__.py              # [NEW]
        └── app.py                   # [NEW] Streamlit Dashboard（5 Tab 可视化面板）

mytrader/
├── main.py                          # [MODIFIED] 接入 ScanOrchestrator 真实回调 + --scan-now 参数
├── config/default.yaml              # [MODIFIED] 新增 watchlist 配置节
└── .env.example                     # [MODIFIED] 新增 Phase 4 数据源 & 标的配置

mytrader/mytrader/infra/
└── config.py                        # [MODIFIED] 新增 WatchlistConfig

mytrader/tests/
├── test_alpaca_provider.py          # [NEW] 14 个测试
└── test_scan_orchestrator.py        # [NEW] 24 个测试
```

---

## 2. 关键设计决策

| 决策 | 选择 | 原因 |
|------|------|------|
| **数据源抽象** | AlpacaDataProvider 实现同一 DataProvider Protocol | YFinance/Alpaca 可按配置无缝切换，strategy/risk 层无感知 |
| **Alpaca 数据 feed** | `sip`（默认），支持切换 `iex` | SIP=免费全量 15min 延迟，适合日线扫描；IEX=实时但覆盖有限 |
| **复权** | `adjustment="all"`（split+dividend） | 与 yfinance auto_adjust=True 保持一致 |
| **扫描编排器位置** | `mytrader/scan_orchestrator.py`（顶层包） | 跨越多个子模块，放在 mytrader 包根更合理，不属于单一子模块 |
| **_generate_signals Mock 策略** | 测试中直接替换 `orch._generate_signals`（MagicMock） | 绕开策略注册表的全局副作用，测试真正关注的是扫描流程 |
| **EOD check 止损/止盈** | 读 `Position.stop_loss_price / take_profit_price`，与 latest close 比较 | 简单可靠；真实盘应在 Broker 层设置 bracket order |
| **Streamlit 自动刷新** | `st.rerun()` + 30s `time.sleep` | 简单实现；生产环境可改为 `streamlit_autorefresh` 组件 |
| **watchlist 配置** | `WatchlistConfig`（`symbols` + `lookback_days` + `max_concurrent_symbols`） | 集中管理标的列表，支持 .env 覆盖 |

---

## 3. 数据流链路（Phase 4 完成后）

```
config.watchlist.symbols
        ↓
ScanOrchestrator._run_scan(symbol)
        ↓
DataProvider.get_ohlcv(symbol, lookback_days)    ← YFinanceProvider / AlpacaDataProvider
        ↓
_generate_signals(df) → STRATEGY_REGISTRY[name](close, **params)
        ↓
SignalPipeline.run(signals, df)                   ← volume/atr/cooldown 等过滤器
        ↓
RiskManager.evaluate(filtered_signal, df)         ← 仓位计算 + 约束 + 熔断
        ↓
Broker.submit(intent, df)                          ← PaperBroker / AlpacaBroker
        ↓
PortfolioTracker.process_order(result)
        ↓
NotificationService.notify_order(result)           ← Telegram / 企业微信

TradingScheduler → morning_scan / intraday_scan / eod_check / reconciliation
Streamlit Dashboard ← SQLite DB（持仓/交易/权益曲线）
```

---

## 4. 测试覆盖（Phase 4 新增 38 个 Mock 测试）

### 4.1 AlpacaDataProvider（14 个）

| 测试类 | 测试数 | 主要覆盖点 |
|--------|--------|-----------|
| `TestGetOHLCV` | 7 | 正常返回 OHLCV / UTC 索引 / 缓存命中跳过 client / 不支持 timeframe 抛错 / 空响应返回空 DF / client 异常返回空 DF / 全 timeframe 接受 |
| `TestGetLatestBar` | 2 | 正常返回 Series / 空数据抛 RuntimeError |
| `TestBarsToDataframe` | 5 | None 输入 / DataFrame 直传 / MultiIndex 展开 / UTC 强制 / 非 UTC 转换 |

### 4.2 ScanOrchestrator（24 个）

| 测试类 | 测试数 | 主要覆盖点 |
|--------|--------|-----------|
| `TestScanModels` | 3 | SymbolScanResult 默认值 / error 标记 / ScanSummary 统计 |
| `TestMorningScan` | 12 | BUY/SELL 提交订单 / HOLD 无订单 / 过滤器拦截 / 风控拒绝 / 数据失败记 error / 空数据跳过 / 多标的 / 单标的异常继续 / PENDING 不更新 tracker / FILLED 调用 tracker / 通知被调用 / 通知失败不崩溃 |
| `TestIntradayScan` | 1 | scan_type="intraday" 正确设置 |
| `TestEODCheck` | 4 | 止损触发 / 止盈触发 / 未触碰无订单 / 无持仓空 summary |
| `TestSyncRiskState` | 1 | 正确同步 capital/exposure/positions 到 RiskManager |
| `TestBuildOrchestrator` | 2 | yfinance 模式构建 / alpaca 模式使用 AlpacaDataProvider |

**总计：382 passed（344 Phase1-3 Mock + 38 Phase4），0 failed**

---

## 5. 新增配置项

### config/default.yaml

```yaml
watchlist:
  symbols: ["AAPL", "MSFT", "TSLA", "NVDA", "SPY", "QQQ"]
  lookback_days: 90
  max_concurrent_symbols: 5
```

### .env 覆盖格式

```bash
DATA__PROVIDER=alpaca                              # 切换为 Alpaca 数据源
WATCHLIST__SYMBOLS='["AAPL","MSFT","TSLA"]'       # 覆盖标的列表
WATCHLIST__LOOKBACK_DAYS=120
```

---

## 6. 启动方式

```bash
cd /Users/rickouyang/Github/trade-tools/mytrader

# paper 模式，正常调度启动
/Users/rickouyang/miniforge3/envs/py312trade/bin/python main.py

# 立即执行一次盘前扫描（调试）
/Users/rickouyang/miniforge3/envs/py312trade/bin/python main.py --scan-now morning

# semi_auto 模式
/Users/rickouyang/miniforge3/envs/py312trade/bin/python main.py --mode semi_auto

# dry-run（只检查配置）
/Users/rickouyang/miniforge3/envs/py312trade/bin/python main.py --dry-run

# 启动 Dashboard
/Users/rickouyang/miniforge3/envs/py312trade/bin/streamlit run mytrader/monitor/dashboard/app.py
```

---

## 7. Phase 4 遗留（TODO → Phase 5）

| 模块 | 说明 | 优先级 |
|------|------|--------|
| `reconciliation` 真实集成 | 接入真实 Alpaca/IBKR `get_positions`，盘后自动对账 | P1 |
| Dashboard 实时行情 | 接入 Alpaca WebSocket 实时显示最新价 | P2 |
| 全自动模式端到端验证 | Paper 账户跑完整一个交易日 auto 模式，确认无误后开放 | P2 |
| 开盘跳空分批执行 | 极端跳空日 VWAP/时间分批替代一次性市价单 | P3 |
| 策略多选 + Ensemble | 多策略投票后再过 RiskManager，提高信号质量 | P3 |
| 港股支持 | `IBKRDataProvider` 接入 TWS 历史 API，扩展 watchlist 至港股 | P3 |
