# Module 01 — Data Layer（数据层）

> 上级文档：[00-overview.md](./00-overview.md)

---

## 1. 职责

- 从外部数据源（券商 API、免费行情 API）拉取行情数据
- 对数据做清洗、格式归一化
- 提供本地缓存，减少重复请求
- 向上游（Strategy Engine）提供统一的数据接口

Data Layer 是整个系统的**基石**，数据质量直接决定信号质量和回测有效性。

---

## 2. 数据类型

| 类型 | 描述 | 用途 |
|------|------|------|
| **OHLCV** | 开高低收量，分钟/日频 | 指标计算、回测 |
| **Tick** | 逐笔成交 | 高精度实盘（可选） |
| **财务数据** | EPS、市值、PE 等 | 基本面过滤 |
| **宏观数据** | 利率、指数、VIX | 市场情绪判断 |
| **新闻/情感** | 舆情分数 | 可选，作为辅助信号 |

**当前阶段只需实现 OHLCV。**

---

## 3. 数据源选型

| 数据源 | 覆盖范围 | 频率 | 延迟 | 成本 | 推荐场景 |
|--------|---------|------|------|------|---------|
| `yfinance` | 美股、港股、ETF | 1m–1d | 15min 延迟 | 免费 | 回测、日线实盘 |
| `akshare` | A股、港股 | 日线为主 | 实时 | 免费 | A股数据获取 |
| **Alpaca `v2/delayed_sip`** | **美股全量 SIP** | **1m–1d** | **15 分钟** | **免费，不限量** | **美股实盘 + 分钟级回测** |
| Alpaca SIP Real-time | 美股全量 SIP | tick/分钟 | 实时 | $99/月 | 高频实盘 |
| IBKR Market Data | 全市场 | 实时 | 实时 | 需订阅 | 生产级实盘 |
| Polygon.io | 美股 | tick/分钟 | 实时（付费） | 免费有限额 | 高质量历史数据 |

---

## 4. 模块接口设计

```python
# 统一的数据接口协议（Protocol/ABC）
class DataProvider(Protocol):
    def get_ohlcv(
        self,
        symbol: str,
        start: date,
        end: date,
        timeframe: str = "1d",   # "1m", "5m", "1h", "1d"
    ) -> pd.DataFrame:
        """
        返回 DataFrame，列：open, high, low, close, volume
        索引：DatetimeIndex，时区统一为 UTC
        """
        ...

    def get_latest_bar(self, symbol: str, timeframe: str = "1m") -> pd.Series:
        """实盘用：获取最新一根 K 线"""
        ...
```

所有数据源都实现该 Protocol，Strategy Engine 只依赖 Protocol，不依赖具体实现。

---

## 5. 缓存策略

```
请求数据
    │
    ▼
检查本地缓存（Parquet 文件）
    │
    ├── 命中且新鲜 ──▶ 直接返回
    │
    └── 未命中 / 过期 ──▶ 拉取远程 ──▶ 写入缓存 ──▶ 返回
```

- **存储格式**：Parquet（`pyarrow`，列式存储，pandas 读写极快）
- **缓存目录**：`~/.mytrader/cache/{source}/{symbol}/{timeframe}/{start}_{end}.parquet`
- **过期策略**：
  - 日线数据：当天 18:00 UTC 后刷新
  - 分钟数据：过去 30 分钟后刷新
  - 历史数据（end 距今 > 365 天）：永不过期

---

## 6. 数据清洗规则

| 问题 | 处理方式 |
|------|---------|
| 缺失 K 线（节假日正常，交易日异常） | 前向填充（`ffill`），标记为异常并记日志 |
| 价格异常值（单 bar 涨跌 > 50%） | 标记 `is_suspect=True`，保留但不参与信号计算 |
| 成交量为 0 | 标记为流动性不足，跳过该交易日 |
| 复权问题 | 统一使用**后复权**价格（`auto_adjust=True`） |
| 时区问题 | 所有时间统一转为 UTC 存储，展示时转为本地时区 |

---

## 7. 注意点

### 7.1 yfinance 的已知问题
- 日内数据（1m/5m）只能拉取最近 7–60 天，超出范围会静默返回空 DataFrame，需做空值检查
- 港股 symbol 格式为 `0700.HK`（需加 `.HK` 后缀）
- `yfinance` 偶尔返回数据与真实成交量/价格有细微差异（非主流券商数据），**不建议用于高频策略**

### 7.2 数据对齐问题
- 多个 symbol 的时间戳可能不完全对齐（不同市场、ETF vs 股票）
- 在做多标的组合回测时，必须做时间轴 `reindex` 对齐，避免引入未来数据

### 7.3 前视偏差（Look-ahead Bias）⚠️ 高风险
- 这是回测失效的头号原因
- **绝对不能**在 T 日信号计算中使用 T 日的收盘价（当天 close）
- 策略应基于 **T-1 日收盘价**或 **T 日开盘价**做决策
- VectorBT 中通过 `shift(1)` 实现滞后

### 7.4 股票拆分/合并
- `yfinance` 的 `auto_adjust=True` 会自动处理拆分复权
- 但如果用原始价格缓存后再手动计算，需注意历史价格需要重新拉取

---

## 8. 风险点

| 风险 | 级别 | 缓解措施 |
|------|------|---------|
| 数据源宕机 | 高 | 配置多个备用数据源，自动降级 |
| 前视偏差 | 高 | 数据访问层统一做滞后处理，单元测试覆盖 |
| 时区混乱 | 中 | 所有时间统一 UTC，仅在输出层转换 |
| 数据质量差（毛刺、错误） | 中 | 引入数据质量检查器，异常数据标记而非删除 |
| API 频率限制 | 低 | 本地缓存 + 请求限速（`time.sleep`） |

---

## 9. 目录结构（Phase 1 已实现）

```
mytrader/
└── data/
    ├── __init__.py
    ├── base.py               # DataProvider Protocol 定义 + OHLCVFrame 类型别名
    ├── providers/
    │   ├── __init__.py
    │   └── yfinance_provider.py   # ✅ 已实现：含缓存集成、重试、后复权
    │   # alpaca_provider.py       # Phase 2 实现
    │   # akshare_provider.py      # 按需实现（A股）
    ├── cache.py              # ✅ 本地 Parquet 缓存管理（TTL 策略）
    ├── cleaner.py            # ✅ 数据清洗规则（列名/时区/去重/异常标记）
    └── validator.py          # ✅ 数据质量校验（DataQualityReport）
```

---

## 参考来源

- [yfinance GitHub](https://github.com/ranaroussi/yfinance)
- [AKShare 文档](https://akshare.akfamily.xyz/)
- [Alpaca Market Data API](https://docs.alpaca.markets/reference/stockbars)
- *Advances in Financial Machine Learning*, Ch.2 — Bars (de Prado)
- [Look-ahead bias explained — QuantStart](https://www.quantstart.com/articles/lookforward-bias-in-your-backtesting-system/)
