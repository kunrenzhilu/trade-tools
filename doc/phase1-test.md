# Phase 1 测试文档

> 版本：v1.0  
> 日期：2026-06-14  
> 对应开发阶段：Phase 1 — 策略验证（已完成）  
> 已有测试：29 个（全部通过）

---

## 1. 测试策略总览

### 1.1 测试目标

Phase 1 的测试目标是确保三大核心模块（Data Layer、Strategy Engine、Backtest Module）在投入 Phase 2 半自动执行之前，**数据质量可靠、信号逻辑正确、回测结果可信**。

### 1.2 测试分层

| 层级 | 说明 | 已有测试 | 待补充 |
|------|------|---------|--------|
| **单元测试** | 纯函数级别：单个函数输入→输出验证 | 29 个 | 52 个 |
| **集成测试** | 模块间协作：Data→Strategy→Backtest 全链路 | 0 个 | 5 个 |
| **端到端测试** | 完整回测流程：数据拉取→信号生成→报告输出 | `examples/phase1_backtest.py` 脚本 | 1 个 |

### 1.3 测试优先级定义

| 级别 | 含义 | 示例 |
|------|------|------|
| **P0（阻塞）** | 一旦出错将导致无法使用的功能，必须通过 | 前视偏差、数据清洗、信号值域 |
| **P1（高）** | 核心功能边界条件，未覆盖有隐蔽风险 | 缓存 TTL、指标边界值、参数传播 |
| **P2（中）** | 鲁棒性增强，正常路径之外的分支 | 异常输入处理、报告文件完整性 |
| **P3（低）** | 锦上添花，不影响核心功能正确性 | 日志输出格式、Protocol 类型检查 |

---

## 2. 现有测试覆盖矩阵

### 2.1 Data Layer（12 个测试）

| 模块 | 文件 | 函数/类 | 已测试 | 测试文件 |
|------|------|---------|--------|---------|
| cleaner | `cleaner.py` | `clean_ohlcv()` | 8 个 | `test_data_layer.py` |
| validator | `validator.py` | `validate_ohlcv()` / `DataQualityReport` | 4 个 | `test_data_layer.py` |
| cache | `cache.py` | `DataCache` | **0 个** ❌ | — |
| provider | `yfinance_provider.py` | `YFinanceProvider` | **0 个** ❌ | — |
| base | `base.py` | `DataProvider` Protocol | **0 个** ❌ | — |

**cleaner 已覆盖**：列名小写、UTC 时区、索引排序、去重、NaN 前向填充、异常标记、低流动性标记、空输入

**validator 已覆盖**：合法数据、空 DataFrame、行数不足、负价格检测

### 2.2 Strategy Engine（17 个测试）

| 模块 | 文件 | 函数/类 | 已测试 | 测试文件 |
|------|------|---------|--------|---------|
| indicators | `indicators.py` | `sma` / `ema` / `rsi` / `bb` / `macd` / `atr` / `crossed_*` | 6 个 | `test_strategy.py` |
| strategies | `strategies/*.py` | 4 个策略函数 | 2 个（值域 + 前视偏差） | `test_strategy.py` |
| ensemble | `ensemble.py` | `ensemble_signal()` | 3 个 | `test_strategy.py` |
| registry | `registry.py` | `register_strategy()` / `STRATEGY_REGISTRY` | 2 个 | `test_strategy.py` |
| base | `base.py` | `Signal` / `SignalDirection` | **0 个** ❌ | — |

**indicators 已覆盖**：SMA 长度, SMA 首有效值, RSI 范围, BB 上下轨, MACD 维度, ATR 非负

**indicators 未覆盖**：`ema`、`crossed_above`、`crossed_below`、极短序列、全 NaN 输入、参数边界

**strategies 已覆盖**：4 个策略的前视偏差参数化测试、dual_ma 和 rsi 的值域检查

**strategies 未覆盖**：自定义参数组合、信号持续性、索引对齐、常量价格输入

**ensemble 已覆盖**：等权投票、冲突信号、权重归一化

**ensemble 未覆盖**：空列表、权重长度不匹配、阈值边界、不同长度信号、单信号

### 2.3 Backtest Module（0 个测试）

| 模块 | 文件 | 函数/类 | 已测试 | 测试文件 |
|------|------|---------|--------|---------|
| runner | `runner.py` | `BacktestConfig` / `BacktestResult` / `BacktestRunner` | **0 个** ❌ | — |
| report | `report.py` | `BacktestReport` | **0 个** ❌ | — |

**runner 未覆盖**：BacktestConfig 默认值/验证、run() 正常/异常路径、run_optimize() 功能、BacktestResult 统计字段

**report 未覆盖**：generate() 输出文件完整性、CSV 内容正确性、HTML 文件生成、空交易处理

---

## 3. 覆盖缺口分析（按设计文档风险点）

### 3.1 关键设计约束对照

根据 `design/` 设计文档和 `phase1-summary.md`，以下是 Phase 1 的设计约束及对应测试覆盖情况：

| 设计约束 | 来源 | 风险级别 | 测试覆盖 |
|----------|------|---------|---------|
| 策略函数强制 `shift(1)` 避免前视偏差 | `02-strategy-engine` §7.1, `01-data-layer` §7.3 | **极高** | ✅ 4 个前视偏差专项测试 |
| 回测/实盘共用同一套策略函数 | `02-strategy-engine` §2, `00-overview` §7 | 高 | ⚠️ 仅间接验证（回测调用策略函数），无专门一致性测试 |
| `size_type="Percent"` VectorBT 1.0.0 适配 | `07-backtest-module` §9 | 高 | ❌ 未覆盖 |
| `open=open_series` 下一 bar 开盘价执行 | `07-backtest-module` §4 | 高 | ❌ 未覆盖 |
| 数据缓存 TTL 策略（日线 18:00/历史永不过期） | `01-data-layer` §5 | 高 | ❌ 未覆盖 |
| 数据清洗后统一 UTC 时区 | `01-data-layer` §6 | 中 | ✅ UTC 测试 + 时区转换（非 UTC → UTC 未覆盖） |
| 数据质量校验（价格逻辑/负价） | `01-data-layer` §6 | 中 | ⚠️ 负价已覆盖，OHLC 价格逻辑未覆盖 |
| `pf.stats()` 不含 `Annualized Return` | `07-backtest-module` §5 | 中 | ❌ 未覆盖 |

### 3.2 源码分支覆盖缺失点

#### cleaner.py — `clean_ohlcv()`

源码流程中未覆盖的分支：

```python
# 分支 1: df=None → 直接返回（当前测试仅覆盖 df=empty DataFrame，未测 None）
if df is None or df.empty:  # ← None 分支未覆盖
    return df

# 分支 2: 缺少必需列 → raise ValueError
required = {"open", "high", "low", "close", "volume"}
missing = required - set(df.columns)
if missing:
    raise ValueError(...)  # ← 未覆盖

# 分支 3: 非 DatetimeIndex → 转换
if not isinstance(df.index, pd.DatetimeIndex):
    df.index = pd.to_datetime(df.index)  # ← 未覆盖

# 分支 4: tz-aware 非 UTC → 转换
else:
    df.index = df.index.tz_convert("UTC")  # ← 未覆盖

# 分支 5: ffill 作用于多列（只有 close 列 NaN 测试，未测多列）
nan_before = df[["close"]].isna().sum().sum()  # ← 只统计 close，多列场景未覆盖
```

#### validator.py — `validate_ohlcv()`

```python
# 分支 1: is_suspect 列不存在时不统计（当前测试均先经过 cleaner）
if "is_suspect" in df.columns:  # ← 列缺失分支未覆盖

# 分支 2: 高嫌疑率 >1%
if suspect_pct > 0.01:  # ← 未覆盖

# 分支 3: OHLC 价格逻辑违反
# high >= close, close >= low, high >= open, open >= low
if not price_ok:  # ← 未覆盖

# 分支 4: low_liquidity 统计
if "is_low_liquidity" in df.columns:  # ← 列缺失分支未覆盖
```

---

## 4. 补充测试用例设计

### 4.1 Data Layer 补充测试（P0-P2）

#### 4.1.1 cleaner.py 补充测试

**测试文件**：`tests/test_data_layer.py`（追加到现有文件）

| # | 测试用例 | 优先级 | 测试目的 | 输入 | 预期结果 |
|---|---------|--------|---------|------|---------|
| C1 | `test_none_input_returns_none` | P1 | 验证 `df=None` 返回原值 | `clean_ohlcv(None)` | 返回 `None` |
| C2 | `test_missing_columns_raises` | P0 | 缺少 OHLCV 列时抛出 ValueError | DataFrame 只有 `close, volume` 列 | `ValueError` 包含 `Missing columns` |
| C3 | `test_non_datetime_index_converted` | P1 | 非 DatetimeIndex 应被转换 | DataFrame 用 int 索引 | 索引变为 DatetimeIndex, tz=UTC |
| C4 | `test_non_utc_tz_converted` | P1 | 非 UTC 时区应转换为 UTC | DataFrame 索引 tz="Asia/Shanghai" | 索引 tz="UTC" |
| C5 | `test_suspect_flag_first_row` | P2 | 第一行 pct_change 为 NaN 时 is_suspect 行为 | 正常 20 行数据 | 第一行 `is_suspect` 为 False/NaN，非 True |
| C6 | `test_multiple_suspect_bars` | P2 | 连续多行 >50% 涨跌均被标记 | 连续 3 行价格翻倍 | 3 个 `is_suspect=True` |
| C7 | `test_nan_in_multiple_columns_ffilled` | P2 | 多列同时 NaN 时 ffill 处理 | open/close/volume 均 NaN | 所有 NaN 被 ffill |

#### 4.1.2 validator.py 补充测试

**测试文件**：`tests/test_data_layer.py`（追加）

| # | 测试用例 | 优先级 | 测试目的 | 输入 | 预期结果 |
|---|---------|--------|---------|------|---------|
| V1 | `test_high_suspect_rate` | P1 | 嫌疑 bar 比例 >1% 时触发警告 | 50 行数据，2 个 is_suspect=True | `is_ok=False`，issues 含 `high_suspect_rate` |
| V2 | `test_price_ohlc_violation` | P0 | OHLC 价格逻辑违反检测 | high < close 或 close < low | `is_ok=False`，issues 含 `price_ohlc_violation` |
| V3 | `test_price_ohlc_edge_equal` | P2 | high==close==low 等极端相等情况 | 所有价格相等 | `is_ok=True`（≥关系允许相等） |
| V4 | `test_validator_without_suspect_column` | P1 | 未清洗数据（无 is_suspect 列） | 不含 is_suspect 列的干净数据 | `is_ok=True`，suspect_bars=0，无异常 |
| V5 | `test_none_input` | P1 | df=None 时的行为 | `validate_ohlcv(None)` | `is_ok=False`，issues 含 `empty_dataframe` |
| V6 | `test_min_rows_boundary` | P2 | 恰好等于 min_rows 时通过 | 数据行数 = min_rows | `is_ok=True` |
| V7 | `test_multiple_issues` | P2 | 同时存在多个问题时全部记录 | 行数不足 + 价格违反 | issues 包含两条记录 |

#### 4.1.3 cache.py 补充测试（新建文件）

**测试文件**：`tests/test_cache.py`（新文件）

| # | 测试用例 | 优先级 | 测试目的 | 输入 | 预期结果 |
|---|---------|--------|---------|------|---------|
| CK1 | `test_write_and_read` | P0 | 缓存写入后再读取一致性 | 写入 DataFrame → 读取 | 读回 DataFrame 与写入内容一致 |
| CK2 | `test_cache_miss_returns_none` | P0 | 未缓存的 key 返回 None | 读取不存在的 key | 返回 `None` |
| CK3 | `test_historical_data_never_expires` | P0 | end 距今 >365 天的缓存永不过期 | end=2020-01-01 的文件 | `get()` 返回数据，不标记为过期 |
| CK4 | `test_daily_data_expires_after_18utc` | P1 | 日线在当天 18:00 UTC 后过期 | 文件 mtime=当天 10:00，now=当天 19:00 | `get()` 返回 `None`（过期） |
| CK5 | `test_intraday_data_expires_after_30min` | P1 | 分钟数据在 30 分钟后过期 | 文件 mtime=30 分钟前 | `get()` 返回 `None` |
| CK6 | `test_invalidate_removes_cache` | P1 | invalidate 后读取返回 None | 写入 → invalidate → 读取 | 返回 `None` |
| CK7 | `test_path_generation` | P1 | 缓存路径格式正确 | provider="yf", symbol="AAPL", timeframe="1d" | 路径为 `~/.mytrader/cache/yf/AAPL/1d/{start}_{end}.parquet` |
| CK8 | `test_symbol_with_dots` | P2 | 含 `.` 的股票代码路径安全 | symbol="BRK.B" | 路径中 `.` 被替换，不会创建子目录 |
| CK9 | `test_overwrite_cache` | P2 | 重复 set 会覆盖旧数据 | set(A) → set(B) → get | 返回 B |
| CK10 | `test_corrupt_parquet_returns_none` | P2 | 损坏的 parquet 文件不会被误返回 | 手动写入非法 parquet | `get()` 返回 `None` |
| CK11 | `test_cache_directory_created` | P2 | set 自动创建父目录 | set 到不存在目录的路径 | 目录被创建，文件写入成功 |

#### 4.1.4 yfinance_provider.py 补充测试（新建文件）

**测试文件**：`tests/test_provider.py`（新文件）

> **注意**：这些测试使用 `unittest.mock` mock `yfinance.Ticker`，不发起真实网络请求。

| # | 测试用例 | 优先级 | 测试目的 | 输入 | 预期结果 |
|---|---------|--------|---------|------|---------|
| P1 | `test_conforms_to_protocol` | P1 | YFinanceProvider 符合 DataProvider Protocol | — | `isinstance(provider, DataProvider)` → True |
| P2 | `test_unsupported_timeframe_raises` | P1 | 不支持的时间周期抛出 ValueError | `get_ohlcv("AAPL", ..., timeframe="3m")` | `ValueError` |
| P3 | `test_cache_hit_returns_cached` | P1 | 缓存命中时跳过网络请求 | 预填充 DataCache | 返回缓存数据，不调用 yfinance |
| P4 | `test_cache_miss_fetches_and_caches` | P1 | 缓存未命中时拉取并写入缓存 | 空 DataCache + mock yfinance | yfinance 被调用，数据被写入缓存 |
| P5 | `test_empty_response_returns_empty_df` | P1 | yfinance 返回空数据时的降级行为 | mock 返回空 DataFrame | 返回含 OHLCV 列的空 DataFrame |
| P6 | `test_retry_on_failure` | P1 | 网络异常后自动重试 | mock 前 2 次抛异常，第 3 次成功 | 成功返回数据，yfinance 被调用 3 次 |
| P7 | `test_data_cleaned_after_fetch` | P2 | 拉取的数据经过 clean_ohlcv 处理 | mock 原始数据含大写列名 | 返回数据列名为小写 |
| P8 | `test_quality_report_logged` | P2 | 数据质量校验结果被记录 | mock 数据含异常值 | 日志包含 quality 相关信息 |

### 4.2 Strategy Engine 补充测试（P0-P2）

#### 4.2.1 indicators.py 补充测试

**测试文件**：`tests/test_strategy.py`（追加）

| # | 测试用例 | 优先级 | 测试目的 | 输入 | 预期结果 |
|---|---------|--------|---------|------|---------|
| I1 | `test_ema_length` | P1 | EMA 输出长度与输入一致 | 50 行 close | 输出长度 50 |
| I2 | `test_crossed_above_detection` | P1 | 上穿检测正确 | A=[1,2], B=[1.5,1.5] | 第 2 行为 True |
| I3 | `test_crossed_above_no_cross` | P1 | 无交叉时全 False | A 始终 > B | 全部 False |
| I4 | `test_crossed_below_detection` | P1 | 下穿检测正确 | A=[2,1], B=[1.5,1.5] | 第 2 行为 True |
| I5 | `test_crossed_below_no_cross` | P1 | 无交叉时全 False | A 始终 < B | 全部 False |
| I6 | `test_sma_period_larger_than_data` | P1 | period > 数据行数时 | 5 行数据，period=10 | 全 NaN |
| I7 | `test_rsi_on_constant_prices` | P2 | 所有价格相同时 RSI | 所有 close=100 | 不抛异常，数值有意义或 NaN |
| I8 | `test_bollinger_on_short_data` | P2 | 数据行数 < period | 5 行数据，period=20 | 适当处理 NaN |
| I9 | `test_macd_histogram_formula` | P2 | histogram = macd_line - signal_line | 100 行 close | `hist == macd_line - signal_line` |
| I10 | `test_atr_basic_iteration` | P2 | ATR 首有效值位置 | 60 行 OHLCV，period=14 | 前 13 行 NaN，之后全正 |

#### 4.2.2 strategies/ 补充测试

**测试文件**：`tests/test_strategy.py`（追加）

| # | 测试用例 | 优先级 | 测试目的 | 输入 | 预期结果 |
|---|---------|--------|---------|------|---------|
| S1 | `test_all_strategies_return_int_dtype` | P0 | 所有策略返回值类型为 int | 100 行 close | 返回值 `dtype` 为 int |
| S2 | `test_all_strategies_index_alignment` | P0 | 所有策略返回 index 与 close 一致 | 100 行 close | `signal.index.equals(close.index)` → True |
| S3 | `test_dual_ma_custom_params` | P1 | 双均线使用非默认参数 | fast=5, slow=60 | 返回合法信号序列，值域 {-1,0,1} |
| S4 | `test_dual_ma_fast_greater_than_slow` | P2 | fast > slow 时的行为（异常参数） | fast=30, slow=10 | 不应崩溃，可为全 0 |
| S5 | `test_rsi_custom_thresholds` | P1 | RSI 使用非默认阈值 | oversold=20, overbought=80 | 合法信号序列 |
| S6 | `test_bollinger_custom_std` | P1 | 布林带使用非默认 std | std_dev=3.0 | 合法信号序列 |
| S7 | `test_macd_custom_params` | P1 | MACD 使用非默认参数 | fast=5, slow=35, signal_period=5 | 合法信号序列 |
| S8 | `test_constant_price_input` | P2 | 所有价格为常数的输入 | close 全部 = 100 | 所有策略不抛异常，返回值稳定 |
| S9 | `test_signal_dtype_not_float` | P2 | 信号值不含浮点 | 100 行 close | 信号 unique 全为整数 -1/0/1 |
| S10 | `test_short_series` | P2 | 极短序列（少于指标最小周期） | 10 行 close | 不抛异常，安全降级 |

#### 4.2.3 ensemble.py 补充测试

**测试文件**：`tests/test_strategy.py`（追加）

| # | 测试用例 | 优先级 | 测试目的 | 输入 | 预期结果 |
|---|---------|--------|---------|------|---------|
| E1 | `test_empty_signals_raises` | P0 | 空信号列表抛出 ValueError | `ensemble_signal([])` | `ValueError` |
| E2 | `test_weights_length_mismatch` | P0 | 权重和信号数量不一致 | 2 信号, 3 权重 | `ValueError` |
| E3 | `test_single_signal_above_threshold` | P1 | 单信号超过阈值时通过 | 信号=1, threshold=0.5 | 结果为 1 |
| E4 | `test_single_signal_below_threshold` | P1 | 单信号未超过阈值 | 信号=1, threshold=1.5 | 结果为 0 |
| E5 | `test_threshold_zero` | P1 | threshold=0 时所有非零都通过 | threshold=0 | 任何非零 combined 都映射为对应信号 |
| E6 | `test_all_hold_signals` | P2 | 所有策略输出 HOLD | 全部信号=0 | 结果为全 0 |
| E7 | `test_different_length_signals` | P2 | 信号索引长度不一致 | 两个不同索引的信号 | 索引对齐后正确处理 |
| E8 | `test_negative_weight_edge` | P3 | 负权重未被拒绝 | weights=[-1, 2] | 归一化后仍正常运行 |

#### 4.2.4 base.py / registry.py 补充测试

**测试文件**：`tests/test_strategy.py`（追加）

| # | 测试用例 | 优先级 | 测试目的 | 输入 | 预期结果 |
|---|---------|--------|---------|------|---------|
| BR1 | `test_signal_is_actionable_buy` | P1 | BUY 信号 is_actionable=True | 创建 direction=BUY 的 Signal | `is_actionable()` → True |
| BR2 | `test_signal_is_actionable_sell` | P1 | SELL 信号 is_actionable=True | 创建 direction=SELL 的 Signal | `is_actionable()` → True |
| BR3 | `test_signal_is_actionable_hold` | P1 | HOLD 信号 is_actionable=False | 创建 direction=HOLD 的 Signal | `is_actionable()` → False |
| BR4 | `test_signal_default_indicators` | P2 | indicators 默认为空 dict | `Signal(...)` 不传 indicators | `signal.indicators == {}` |
| BR5 | `test_signal_default_price_hint` | P2 | price_hint 默认为 None | `Signal(...)` 不传 price_hint | `signal.price_hint is None` |
| BR6 | `test_register_duplicate_name_raises` | P1 | 重复注册同名策略抛出 ValueError | 两次 `@register_strategy("same_name")` | `ValueError` |
| BR7 | `test_strategy_returns_int_dtype` | P1 | 所有已注册策略返回 int dtype | 100 行 close | 结果 dtype 为 int |

### 4.3 Backtest Module 补充测试（新建文件）

#### 4.3.1 BacktestRunner 补充测试

**测试文件**：`tests/test_backtest.py`（新文件）

> **注意**：使用合成数据（无需访问网络），但需 VectorBT 依赖。

| # | 测试用例 | 优先级 | 测试目的 | 输入 | 预期结果 |
|---|---------|--------|---------|------|---------|
| BT1 | `test_config_defaults` | P1 | BacktestConfig 默认值符合预期 | 最小必填参数构造 | `init_cash=100000`, `fees=0.001`, `slippage=0.001`, `use_next_open=True`, `size=0.95` |
| BT2 | `test_config_custom_values` | P1 | 所有自定义参数正确保存 | 自定义 fees=0.005 等 | config.fees == 0.005 |
| BT3 | `test_runner_with_synthetic_data` | P0 | BacktestRunner.run() 端到端测试 | 合成 200 行 OHLCV + dual_ma | 返回 BacktestResult，stats 含 Sharpe |
| BT4 | `test_runner_invalid_strategy_name` | P0 | 不存在的策略名抛出 ValueError | strategy_name="nonexistent" | `ValueError`，提示可用策略 |
| BT5 | `test_runner_empty_data_raises` | P0 | 空数据回测抛出 ValueError | mock 返回空 DataFrame | `ValueError` |
| BT6 | `test_runner_next_open_vs_close` | P0 | use_next_open=False 与 True 结果有差异 | 同一数据两种模式 | 两种模式 stats 不完全相同 |
| BT7 | `test_runner_custom_provider` | P1 | 注入自定义 DataProvider | mock DataProvider 注入 BacktestRunner | 使用 mock 数据而非真实 yfinance |
| BT8 | `test_optimize_grid_search` | P0 | run_optimize 返回正确结构的 DataFrame | 小网格 `{"fast":[5,10],"slow":[20,30]}` | DataFrame 含参数列 + 指标列，按 Sharpe 降序 |
| BT9 | `test_optimize_single_combination` | P1 | 单个参数组合的网格搜索 | 每参数只有一个值 | 返回 1 行 DataFrame |
| BT10 | `test_optimize_failing_combinations` | P2 | 部分参数组合失败时继续执行 | 一个组合参数非法 + 其他正常 | 非法组合被跳过，合法组合正常返回 |
| BT11 | `test_result_stats_keys` | P1 | BacktestResult.stats 包含关键字段 | 正常回测 | stats 包含 `Total Return [%]`, `Sharpe Ratio`, `Max Drawdown [%]`, `Calmar Ratio`, `Win Rate [%]`, `Profit Factor`, `Total Trades` |
| BT12 | `test_result_print_stats` | P2 | print_stats() 不抛异常 | 正常回测结果 | 无异常抛出 |

#### 4.3.2 BacktestReport 补充测试

**测试文件**：`tests/test_backtest.py`（追加）

| # | 测试用例 | 优先级 | 测试目的 | 输入 | 预期结果 |
|---|---------|--------|---------|------|---------|
| BR1 | `test_generate_creates_directory` | P1 | generate 创建输出目录 | 正常 BacktestResult | 输出目录存在 |
| BR2 | `test_generate_creates_stats_csv` | P0 | stats.csv 存在且内容正确 | 正常结果 | 文件存在，非空 |
| BR3 | `test_generate_creates_trades_csv` | P1 | trades.csv 存在且内容正确 | 有交易的正常结果 | 文件存在，非空，列含 trade 信息 |
| BR4 | `test_generate_creates_html_files` | P1 | HTML 报告文件存在 | 正常结果 | `equity_curve.html` 和 `drawdowns.html` 存在且非空 |
| BR5 | `test_generate_with_custom_name` | P2 | 自定义目录名 | name="my_test_run" | 输出到 `reports/my_test_run/` |
| BR6 | `test_generate_returns_correct_path` | P2 | generate 返回正确的 Path | 正常结果 | 返回 Path 对象指向输出目录 |
| BR7 | `test_generate_no_trades_portfolio` | P2 | 无交易时 trades 处理 | 策略全程 HOLD | 不抛异常，可能无 trades.csv |
| BR8 | `test_generate_tempdir_isolation` | P2 | 使用 tmp_path 隔离测试 | pytest tmp_path 作为 output_dir | 不影响真实 reports/ 目录 |

### 4.4 集成测试（新建文件）

**测试文件**：`tests/test_integration.py`（新文件）

| # | 测试用例 | 优先级 | 测试目的 | 输入 | 预期结果 |
|---|---------|--------|---------|------|---------|
| IT1 | `test_data_to_signal_pipeline` | P0 | Data Layer → Strategy Engine 完整链路 | 合成 OHLCV → 4 个策略分别生成信号 | 每个策略返回合法信号 |
| IT2 | `test_data_to_signal_to_backtest` | P0 | 全链路：Data→Strategy→Backtest | 合成 200 行 OHLCV | BacktestResult 生成成功 |
| IT3 | `test_all_strategies_work_with_synthetic` | P0 | 4 个策略与合成数据的回测 | 合成趋势/震荡数据 | 所有策略不抛异常，stats 合理 |
| IT4 | `test_strategy_determinism` | P1 | 相同数据多次回测结果一致 | 同一数据回测两次 | Sharpe 等关键指标相同 |
| IT5 | `test_ensemble_in_backtest` | P1 | Ensemble 信号用于回测 | 2 个策略 → ensemble → BacktestRunner | 回测结果正常生成 |

---

## 5. 测试优先级汇总

### 5.1 P0（阻塞级）— 共计 13 项

这些测试对应**一旦出错将导致系统不可用或产生错误交易信号**的核心功能：

| # | 模块 | 测试 | 风险后果 |
|---|------|------|---------|
| 1 | cleaner | C2 `test_missing_columns_raises` | 非 OHLCV 数据被误用 |
| 2 | validator | V2 `test_price_ohlc_violation` | 价格逻辑错误的数据被接受 |
| 3 | cache | CK1 `test_write_and_read` | 缓存功能不可用，数据源频繁重复请求 |
| 4 | cache | CK2 `test_cache_miss_returns_none` | 缓存逻辑错误导致错误数据 |
| 5 | cache | CK3 `test_historical_data_never_expires` | 历史数据被重复拉取 |
| 6 | ensemble | E1 `test_empty_signals_raises` | 空信号列表传入未防御 |
| 7 | ensemble | E2 `test_weights_length_mismatch` | 权重与信号不匹配未检测 |
| 8 | strategy | S1 `test_all_strategies_return_int_dtype` | 信号类型不是 int |
| 9 | strategy | S2 `test_all_strategies_index_alignment` | 信号索引与数据不一致 |
| 10 | runner | BT3 `test_runner_with_synthetic_data` | 回测核心流程不可用 |
| 11 | runner | BT4 `test_runner_invalid_strategy_name` | 配置错误未检测 |
| 12 | runner | BT5 `test_runner_empty_data_raises` | 空数据情况未处理 |
| 13 | runner | BT6 `test_runner_next_open_vs_close` | 执行价格模式不一致 |
| 14 | runner | BT8 `test_optimize_grid_search` | 参数优化功能不可用 |

### 5.2 P1（高优先级）— 共计 22 项

这些测试覆盖**核心功能的边界条件和缓存/参数传播等关键路径**：

data layer：C1, C3, C4, V1, V4, V5, CK4, CK5, CK6, CK7, P1, P2, P3, P4, P5, P6  
strategy engine：I1-I6（6项）, S3, S5, S6, S7, E3, E4, E5, BR1-BR3, BR6, BR7  
backtest：BT1, BT2, BT7, BT9, BT11, BR1, BR2, BR3, BR4

### 5.3 P2（中优先级）— 共计 24 项

鲁棒性增强和边界条件覆盖。

### 5.4 P3（低优先级）— 共计 1 项

E8 负权重边界。

---

## 6. 测试执行指南

### 6.1 环境要求

```bash
# Python 环境（phase1-summary.md 指定）
/Users/rickouyang/miniforge3/envs/py312trade  # Python 3.12.13

# 激活环境
conda activate py312trade

# 确认依赖
cd mytrader
pip install -e ".[dev]"
```

### 6.2 运行现有测试

```bash
# 运行全部已有测试
pytest tests/ -v

# 仅某模块
pytest tests/test_data_layer.py -v
pytest tests/test_strategy.py -v

# 带覆盖率
pytest tests/ --cov=mytrader --cov-report=term-missing

# 聚焦前视偏差
pytest tests/test_strategy.py -k "lookahead" -v
```

### 6.3 运行补充测试（规划中）

```bash
# Data Layer 补充
pytest tests/test_data_layer.py -v           # 已有文件追加 C1-C7, V1-V7
pytest tests/test_cache.py -v                # 新文件 CK1-CK11
pytest tests/test_provider.py -v             # 新文件 P1-P8

# Strategy Engine 补充
pytest tests/test_strategy.py -v -k "indicators or ensemble or base or registry"

# Backtest 补充
pytest tests/test_backtest.py -v             # 新文件 BT1-BT12, BR1-BR8

# 集成测试
pytest tests/test_integration.py -v          # 新文件 IT1-IT5

# 全量（建议添加后执行）
pytest tests/ -v --cov=mytrader --cov-report=term-missing
```

### 6.4 测试数据要求

| 测试类型 | 数据来源 | 说明 |
|---------|---------|------|
| cleaner/validator | `make_ohlcv()` 辅助函数生成合成数据 | 不依赖网络 |
| cache | tmp_path 隔离目录 + 合成 DataFrame | 不污染真实缓存 |
| provider | `unittest.mock` patch `yfinance.Ticker` | 不发起真实网络请求 |
| strategies | `make_trending_close()` / `make_oscillating_close()` 合成 | 已有辅助函数 |
| backtest | 合成 200 行 OHLCV 数据 | 不依赖网络 |
| integration | 合成数据全链路 | 不依赖网络 |

### 6.5 当前通过率

```
现有 29 个测试 — 全部通过 ✅
```

### 6.6 预期补充后测试数量

| 文件 | 现有 | 补充后 |
|------|------|--------|
| `test_data_layer.py` | 12 | 19 (+7 cleaner, +7 validator) |
| `test_cache.py` | 0 | 11 (新建) |
| `test_provider.py` | 0 | 8 (新建) |
| `test_strategy.py` | 17 | 37 (+10 indicators, +10 strategies, +5 ensemble, +7 base/registry) |
| `test_backtest.py` | 0 | 20 (+12 runner, +8 report) |
| `test_integration.py` | 0 | 5 (新建) |
| **合计** | **29** | **~100** |

---

## 7. 关键设计约束与风险点覆盖评估

### 7.1 前视偏差（Look-ahead Bias）— 极高风险 ✅

| 约束 | 覆盖 |
|------|------|
| 所有策略 `shift(1)` | ✅ 4 个参数化破坏性测试 |
| 篡改最后 bar 不影响信号 | ✅ 已覆盖 |
| `use_next_open=True` 回测用开盘价执行 | ⚠️ 已有配置，BT6 将补充对比测试 |
| 策略函数不访问当日 close 做决策 | ✅ shift(1) 实现已验证 |

### 7.2 数据质量 — 高风险 ⚠️

| 风险点 | 覆盖 |
|------|------|
| 缺失列 → ValueError | ❌ C2 待补充 |
| OHLC 价格逻辑违反 | ❌ V2 待补充 |
| 高嫌疑率 | ❌ V1 待补充 |
| 缓存过期策略 | ❌ CK3-CK5 待补充 |
| 时区转换（非UTC → UTC） | ❌ C4 待补充 |

### 7.3 回测/实盘一致性 — 高风险 ⚠️

| 约束 | 覆盖 |
|------|------|
| 策略函数纯函数，无外部状态 | ✅ 间接验证（前视偏差测试可证明） |
| 确定性（相同输入相同输出） | ❌ IT4 待补充 |
| 回测和实盘用同一套函数 | ⚠️ 通过架构设计保证，IT2 将集成验证 |

### 7.4 VectorBT 1.0.0 适配 — 中风险 ⚠️

| 约束 | 覆盖 |
|------|------|
| `size_type="Percent"` | ❌ BT3 将覆盖 |
| `pf.stats()` 无 `Annualized Return` | ❌ BT11 将验证 stats 字段 |
| `use_next_open` + `open=` 参数 | ❌ BT6 将覆盖 |

---

## 附录 A：测试文件结构（规划）

```
mytrader/
└── tests/
    ├── __init__.py
    ├── conftest.py                 # 共享 fixtures（tmp_cache_dir, mock_provider 等）
    ├── test_data_layer.py          # cleaner + validator（已有 12 个，追加 14 个）
    ├── test_cache.py               # DataCache（新建，11 个）
    ├── test_provider.py            # YFinanceProvider（新建，8 个）
    ├── test_strategy.py            # indicators + ensemble + registry + base（已有 17 个，追加 27 个）
    ├── test_backtest.py            # BacktestRunner + BacktestReport（新建，20 个）
    └── test_integration.py         # 集成测试（新建，5 个）
```

## 附录 B：共享 Fixtures 建议（conftest.py）

```python
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import date, datetime, timezone

@pytest.fixture
def sample_close():
    """100 行上升趋势收盘价。"""
    idx = pd.date_range("2023-01-01", periods=100, freq="B")
    prices = 100.0 * np.exp(np.cumsum(0.002 + 0.01 * np.random.RandomState(42).randn(100)))
    return pd.Series(prices, index=idx, name="close")

@pytest.fixture
def sample_ohlcv():
    """50 行合成 OHLCV 数据。"""
    idx = pd.date_range("2023-01-01", periods=50, freq="B", tz="UTC")
    rng = np.random.RandomState(42)
    close = pd.Series(100 + rng.randn(50).cumsum(), index=idx)
    return pd.DataFrame({
        "open": close * (1 + rng.uniform(-0.005, 0.005, 50)),
        "high": close * (1 + rng.uniform(0, 0.02, 50)),
        "low": close * (1 - rng.uniform(0, 0.02, 50)),
        "close": close,
        "volume": rng.randint(1_000_000, 10_000_000, 50).astype(float),
    }, index=idx)

@pytest.fixture
def tmp_cache_dir(tmp_path):
    """临时缓存目录。"""
    return tmp_path / "cache"
```

## 附录 C：风险登记表

| 风险编号 | 风险描述 | 严重程度 | 影响 | 缓解措施 | 对应测试 |
|---------|---------|---------|------|---------|---------|
| R01 | 策略存在前视偏差 | 极高 | 回测结果虚高，实盘亏损 | 所有策略 shift(1) + 破坏性测试 | ✅ 已覆盖 |
| R02 | 数据质量校验不完整 | 高 | 错误价格数据产生错误信号 | 补充 OHLC 逻辑、高嫌疑率测试 | ⚠️ V1-V2 待补充 |
| R03 | 缓存策略失效 | 高 | 数据源请求超限 or 使用过期数据 | 补充 TTL 测试 | ❌ CK3-CK5 待补充 |
| R04 | 回测/实盘执行价格不一致 | 高 | 回测与实盘收益差异巨大 | use_next_open 对比测试 | ❌ BT6 待补充 |
| R05 | 策略参数传播错误 | 中 | 非默认参数产生的信号不正确 | 所有策略自定义 param 测试 | ❌ S3-S7 待补充 |
| R06 | VectorBT API 适配错误 | 中 | 回测无法运行或结果异常 | 端到端回测测试 | ❌ BT3 待补充 |
| R07 | Ensemble 边界未处理 | 中 | 空信号/权重不匹配导致崩溃 | 空列表和长度检查测试 | ❌ E1-E2 待补充 |
