# Design Changelog

> 记录设计文档的版本变更及变更理由，便于追溯决策来源。

---

## v2.1 — 2026-06-23（Claude 审查后修正）

### 背景

基于 glm_review.md 和 claude_review.md 的独立审查，修正设计文档中影响回测/实盘一致性的缺陷。

### 修改清单

| 优先级 | 问题 | 涉及文件 | 变更内容 |
|--------|------|----------|---------|
| P0 | #1 回测/实盘 ensemble 语义不等价 | `12-strategy-matrix.md` | §4 明确 ensemble 权重优化须在"单点离散值聚合"语义下进行，与实盘 iloc[-1] 加权等价 |
| P0 | #2 事件型信号 iloc[-1] 漏单 | `12-strategy-matrix.md`, `09-infrastructure.md` | §6 改为检查最近 N bar 内信号有效期（`signal_valid_bars=3`，可配置） |
| P0 | #16 矩阵回测缺 open 参数 | `07-backtest-module.md` | §3.1、§4、§9 全部补充 `open=open_series`，注明必须传入 |
| P1 | #9 平均 Sharpe 计算错误 | `07-backtest-module.md` | §10.3 改为等权合并日收益率序列计算组合 Sharpe；`BacktestResult` 增加 `daily_returns` 字段 |
| P1 | #3 fallback 复权混用 | `10-market-data-store.md` | §6 强制约束：fallback 时不写入（标记 degraded），等主源恢复；§8.2 升级为强制约束 |
| P1 | #5 波动率分组静态 vs 动态 | `07-backtest-module.md`, `11-universe-manager.md` | §10.4 增加历史分组对齐设计点；`11` 补充 `recompute_volatility_tiers_at(date)` 接口 |
| P1 | #6 Top-K 与风控约束未协调 | `13-signal-ranker.md`, `04-risk-manager.md` | §5 改为输出 Top-2K 候选供 Risk Manager 递补；§6 增加约束优先级说明 |
| P2 | #4 幸存者偏差量化 | `11-universe-manager.md` | §8.2 补充偏差规模估算（5年~100只变动）和分组影响差异 |
| P2 | #10 Walk-Forward 重叠讨论 | `07-backtest-module.md` | §10.5 补充窗口重叠率分析和改进方向（时间衰减权重等） |
| P2 | #11 df 传参不一致 | `12-strategy-matrix.md` | §6 改为传完整 df（部分策略需要 high/low/volume） |
| P2 | #14 隔夜跳空防护缺失 | `04-risk-manager.md` | 新增 §7.5 隔夜跳空风险管理（财报平仓/VIX 阈值/可配置开关） |
| P2 | #18 时区混乱 | `09-infrastructure.md` | §2.1 区分 `timezone`（日志显示）和 `trading_timezone`（调度逻辑），明确时区策略 |
| P3 | #7 DuckDB 性能声明不实 | `10-market-data-store.md` | 删除"快 10-100×"的不实数字，改为客观说明（42MB 下差别有限，可选 Parquet 优化） |
| P3 | #8 5 年窗口描述错误 | `07-backtest-module.md` | §10.2 修正时间范围（2021-2026，不含 2020 崩盘），说明需 6 年才能覆盖 |
| P3 | #12 Config 未更新到 v2 | `09-infrastructure.md` | §2.1 补充 v2 新增配置节（universe/strategy_matrix/signal_ranker/market_data_store） |
| P3 | #13 SELL 资金结算 | `13-signal-ranker.md` | §8.1 补充使用 `buying_power` 字段避免结算时序问题 |
| P3 | #17 半天交易日延迟 | `10-market-data-store.md` | §6 补充半天交易日说明（影响可忽略，可选 pandas_market_calendars 精确处理） |

### 不变项
- glm_review #15（fees 保守估计）：维持 `fees=0.001`，此为有益的保守假设；仅补充 slippage 注释
- glm_review 对 #3 的 P0 评级：降为 P1（需 fallback 才触发，低频事件）

---

## v2.0 — 2026-06-23（Phase 5 设计访谈后重构）

### 背景

Phase 1-4 完成后，在规划 Phase 5 时发现：v1 设计把系统定位为
**"单策略 × 固定几只股票 → 直接下单"的线性执行流水线**，缺少
**"从大规模标的中筛选该交易标的"** 的核心环节。

经过 5 轮设计访谈澄清需求后，将系统重构为
**「离线回测层 + 在线交易层」双层架构**。本次变更不影响 Phase 1-4 已交付代码，
仅更新设计文档（design_v2），作为 Phase 5 实现依据。

### 访谈结论（决策来源）

| # | 问题 | 结论 |
|---|------|------|
| Q1 | 系统定位 | **全自动交易系统**；策略开发由外部系统负责，本系统只做"回测验证 + 选股 + 执行" |
| Q2 | 标的范围 | **S&P 500 + Nasdaq 100**（去重 ~550 只）；两组策略适配差异显著（均值回归 vs 动量） |
| Q3 | 多策略聚合 | 组合本身即策略，权重需被回测验证；策略↔标的 mapping 数据驱动 |
| Q4 | 参数粒度 | **按标的分组**优化参数（波动率/行业/市值），绝不对单只优化（防过拟合） |
| Q5 | 回测→实盘 | 回测产出"策略×组"表现排名，实盘只执行排名 **Top-K** 的组合 |

### 新增模块文档

| 文件 | 模块 | 说明 |
|------|------|------|
| `10-market-data-store.md` | Market Data Store | 本地时序库（SQLite 实盘 / DuckDB 回测）+ DataSyncService 增量同步 |
| `11-universe-manager.md` | Universe Manager | S&P 500 + Nasdaq 100 成分股维护、去重、按特征分组 |
| `12-strategy-matrix.md` | Strategy Matrix Runner | M 策略 × N 标的批量运行，按组分配策略 |
| `13-signal-ranker.md` | Signal Ranker | 多信号聚合、排名、Top-K 选股 |

### 修改的既有文档

| 文件 | 变更 | 理由 |
|------|------|------|
| `00-overview.md` | 重写：双层架构、模块清单扩展、v2 数据流、Phase 5 路线、关键参数表 | 系统定位从半自动→全自动；引入大规模选股 |
| `01-data-layer.md` | 数据存储从"按请求 Parquet 缓存"改为"本地时序库 + 增量同步" | v1 缓存 key 含 start/end，滑动窗口导致全量重拉、触发限速 |
| `02-strategy-engine.md` | 新增多策略调度、分组参数、数据驱动 mapping；ensemble 权重改为回测产出 | 支持多策略并行 + 防过拟合 |
| `07-backtest-module.md` | 新增矩阵回测（第 10 节）：N策略×G组×参数网格、5年窗口、Walk-Forward 月度 | 产出实盘选股的 strategy_weights.json |

### 关键技术决策及理由

#### 1. 数据存储：本地时序库 + 增量同步（替代请求缓存）

```
变更：v1 按请求 Parquet 缓存 → v2 本地库（SQLite + DuckDB）+ 增量同步
理由：
  - v1 缓存 key=(symbol,start,end)，日期窗口滑动即全量重拉 → 触发 API 限速
  - v2 增量只拉 delta（每天每只 ~1 根新 bar），盘中读本地库无网络
  - 数据量仅 ~42MB（550只×5年），无需 MySQL，嵌入式 DB 足矣
  - DuckDB 列式读取专为回测"批量读5年"场景优化，比 SQLite 快 10-100×
```

#### 2. 数据源：Alpaca 主 + yfinance 备

```
变更：v1 扫描直接调 yfinance → v2 DataSyncService 调 Alpaca（主）+ yfinance（备）
理由：
  - Alpaca 官方 API，限速可预测（200 req/min），支持多标的批量请求
  - Alpaca v2/delayed_sip 免费全量 SIP（15min 延迟），数据质量优于 yfinance
  - yfinance 是非官方爬虫，限速不透明，作 fallback / 回填补缺
  - 增量架构下数据源延迟不再是实盘瓶颈（同步是收盘后离线批处理）
```

#### 3. 回测窗口：5 年（替代单标的 3 年）

```
变更：v1 单标的 3 年 → v2 全标的 5 年
理由：
  - 90 天/3 年覆盖行情不全，回测统计意义弱
  - 5 年覆盖完整牛熊周期（2020崩盘+2021牛+2022熊+2023-24复苏）
  - 不取 15 年：太老数据市场结构已变，相关性下降
  - 区分两个 lookback：实盘扫描 90 天（够算指标）vs 回测 5 年（验证）
```

#### 4. 参数粒度：按组，不按单只

```
变更：v1 全局固定参数 → v2 按标的分组参数
理由：
  - 对 550 只各自优化 = 550 次独立优化 = 必然过拟合（多重比较）
  - 按特征分组（波动率/行业/市值），组内共用参数，自由度可控
  - 参数差异来自标的统计特征，不是标的本身
```

#### 5. 策略权重更新：每月 Walk-Forward

```
变更：v1 无更新机制 → v2 每月重优化
理由：
  - 更新太频繁（每天）→ 拟合噪音，权重翻转，策略左右打脸
  - 更新太慢（每年）→ 行情切换反应迟钝
  - 每月 ≈ 21 交易日，足够样本外验证，换手率可控
```

#### 6. Top-K = 5

```
变更：v1 无选股概念（全下单）→ v2 扫 550 只取 Top-5
理由及代价：
  - 集中高信念押注，靠 risk_per_trade=1% + 止损控风险（非分散）
  - 代价：等权下每仓 20%，单只暴雷砸 20% 净值（主动选择的风格）
  - 统计量足够：5/天 × 250 日 = 1250 笔/年，可验证策略 edge
  - 未来想降波动可调 K 至 10-15
```

### 不变项（沿用 v1）

- 策略纯函数设计 + 回测/实盘一致性原则
- 前视偏差防护（强制 shift(1)）
- Signal Filter / Risk Manager / Execution / Portfolio / Monitor 模块设计
- 失败安全、可观测性、持仓真相来源等设计原则

### 影响范围

- ✅ 不影响 Phase 1-4 已交付代码（仅设计文档变更）
- 🔲 Phase 5 按 design_v2 实现新增 4 模块 + 矩阵回测 + Walk-Forward 调度

---

## v1.0 — 2026-06-13（Phase 1 完成后）

- 初始设计：9 个模块的线性执行流水线
- 定位：轻量级日间交易系统，半自动执行
- 详见 `../design_v1/`
