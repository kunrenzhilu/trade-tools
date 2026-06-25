# Phase 2 测试文档

> 版本：v1.0  
> 日期：2026-06-14  
> 对应开发阶段：Phase 2 — 信号过滤 → 风险管理 → 执行 → 持仓追踪（已完成）  
> 已有测试：94 个（全部通过）

---

## 1. 测试策略总览

### 1.1 测试目标

Phase 2 引入了信号过滤、风险管理、执行引擎、持仓追踪和基础设施五大模块，构成了从策略信号到模拟成交的完整半自动交易链路。测试目标是确保**每个模块独立可靠、模块间接口契约正确、边界条件充分防御**，为 Phase 3 向真实券商接入奠定基础。

### 1.2 测试分层

| 层级 | 说明 | 已有测试 | 待补充 |
|------|------|---------|--------|
| **单元测试** | 纯函数级别：单个函数/过滤器/计算器输入→输出验证 | 94 个 | 56 个 |
| **集成测试** | 模块间协作：Signal→Risk→Execution→Portfolio 全链路 | 0 个 | 6 个 |
| **端到端测试** | 完整实盘模拟：数据拉取→策略信号→过滤→风控→成交→持仓 | 0 个 | 1 个 |

### 1.3 测试优先级定义

| 级别 | 含义 | 示例 |
|------|------|------|
| **P0（阻塞）** | 一旦出错将导致亏损或系统不可用，必须通过 | 熔断器触发后拒绝下单、FIFO 盈亏计算错误、幂等性失效 |
| **P1（高）** | 核心功能边界条件，未覆盖有隐蔽风险 | 仓位计算零参数、冷却期边界、持久化读写失败 |
| **P2（中）** | 鲁棒性增强，正常路径之外的分支 | 异常输入降级、日志输出验证、配置校验失败 |
| **P3（低）** | 锦上添花，不影响核心功能正确性 | 代码风格检查、Protocol 类型兼容性 |

---

## 2. 现有测试覆盖矩阵

### 2.1 Infra 基础设施（12 个测试）

| 模块 | 文件 | 函数/类 | 已测试 | 测试文件 |
|------|------|---------|--------|---------|
| config | `config.py` | `AppConfig` / `load_config()` | 7 个 | `test_infra.py` |
| config | `config.py` | `SystemConfig` / `DataConfig` / `StrategyConfig` 等子类 | **0 个**（仅隐式覆盖）❌ | — |
| config | `config.py` | `_find_default_yaml()` | **0 个** ❌ | — |
| config | `config.py` | `field_validator`（`_parse_risk` / `_parse_monitor`） | **1 个**（仅 `_parse_risk` 隐式）❌ | — |
| event_bus | `event_bus.py` | `EventBus` / `Events` | 5 个 | `test_infra.py` |

**config 已覆盖**：默认值加载、YAML 文件系统/风险/嵌套/信号过滤器配置、环境变量覆盖（`RISK__RISK_PER_TRADE`）、缺失文件降级

**event_bus 已覆盖**：订阅/发布、多 handler 分发、异常隔离（单 handler 异常不影响其他）、取消订阅、无订阅者发布、clear 清空

**config 未覆盖**：各子配置类的独立字段默认值、Pydantic 范围约束验证、`_find_default_yaml` 向上查找逻辑、`_parse_monitor` validator、各字段 `ge=`/`le=` 越界

**event_bus 未覆盖**：重复订阅同一 handler 行为、handler 无 `__name__` 属性（lambda）异常、publish 后 handler 列表不可变

### 2.2 Signal Filter 信号过滤器（25 个测试）

| 模块 | 文件 | 函数/类 | 已测试 | 测试文件 |
|------|------|---------|--------|---------|
| models | `models.py` | `FilteredSignal` / `FilterResult` | 3 个（间接）| `test_signal_filter.py` |
| pipeline | `pipeline.py` | `SignalPipeline` | 3 个 | `test_signal_filter.py` |
| filters | `filters/volume_filter.py` | `VolumeFilter` | 4 个 | `test_signal_filter.py` |
| filters | `filters/atr_filter.py` | `ATRFilter` | 3 个 | `test_signal_filter.py` |
| filters | `filters/sentiment_filter.py` | `SentimentFilter` | 3 个 | `test_signal_filter.py` |
| filters | `filters/time_window_filter.py` | `TimeWindowFilter` | 3 个 | `test_signal_filter.py` |
| filters | `filters/cooldown_filter.py` | `CooldownFilter` | 4 个 | `test_signal_filter.py` |
| filters | `filters/__init__.py` | `BaseFilter` Protocol | **0 个** ❌ | — |

**VolumeFilter 已覆盖**：成交量充足通过、成交量低拒绝、无 volume 列放行、数据不足放行

**ATRFilter 已覆盖**：低波动通过、高波动拒绝、缺 atr 列放行

**SentimentFilter 已覆盖**：无 benchmark 放行、熊市拒绝 BUY、熊市允许 SELL

**TimeWindowFilter 已覆盖**：日线放行、开盘缓冲期内拒绝、缓冲期后放行

**CooldownFilter 已覆盖**：首次通过、冷却期内拒绝、冷却期后通过、BUY/SELL 方向独立

**SignalPipeline 已覆盖**：空流水线全部通过、`from_config` 构建、`FilterResult` 统计

**过滤器未覆盖**：ATRFilter 信号时间戳早于所有数据、`close_val == 0` 路径；VolumeFilter 精确边界值（等于均值的 1.5 倍）；SentimentFilter 牛市场景（允许 BUY/拒绝 SELL）；TimeWindowFilter 收盘缓冲期、跨日边界；CooldownFilter 冷却期内 BUY→SELL 转向触发；`BaseFilter` Protocol 类型检查

### 2.3 Risk Manager 风险管理器（22 个测试）

| 模块 | 文件 | 函数/类 | 已测试 | 测试文件 |
|------|------|---------|--------|---------|
| models | `models.py` | `OrderIntent` / `CircuitBreakerState` | 2 个 | `test_risk_manager.py` |
| position_sizer | `position_sizer.py` | `fixed_amount_size` / `atr_position_size` / `fixed_fraction_size` | 4 个 | `test_risk_manager.py` |
| stop_loss | `stop_loss.py` | `fixed_stop` / `fixed_take_profit` / `atr_stop` / `time_stop_bars` | 3 个 | `test_risk_manager.py` |
| circuit_breaker | `circuit_breaker.py` | `CircuitBreaker`（三层熔断：日/周/月） | 5 个 | `test_risk_manager.py` |
| constraints | `constraints.py` | 约束检查（4 种） | 4 个 | `test_risk_manager.py` |
| manager | `manager.py` | `RiskManager`（门面） | **0 个** ❌ | — |

**position_sizer 已覆盖**：`fixed_amount_size`（基本/零止损距离）、`atr_position_size`（正值）、`fixed_fraction_size`（基本/零价）

**stop_loss 已覆盖**：`fixed_stop`（多/空）、`atr_stop`、`fixed_take_profit`

**circuit_breaker 已覆盖**：NORMAL / DAILY / WEEKLY / RESET 状态转换

**constraints 已覆盖**：单标的上限、总持仓上限、最小订单金额、最大持仓数

**RiskManager 未覆盖**：整合流程（position_sizer + stop_loss + circuit_breaker + constraints 串联）、`reject_reason` 汇总、检查顺序验证、熔断触发后恢复

**position_sizer 未覆盖**：`atr_value <= 0` 异常输入、`account_equity <= 0`、`risk_per_trade` 越界

**stop_loss 未覆盖**：`time_stop_bars` 到期触发、`atr_stop` 零 ATR 输入

**circuit_breaker 未覆盖**：跨日/跨周/跨月重置边界（同一天内的时间边界）、月亏损阈值触发后次月自动恢复、同时触发多个级别时的优先级

### 2.4 Execution 执行引擎（12 个测试）

| 模块 | 文件 | 函数/类 | 已测试 | 测试文件 |
|------|------|---------|--------|---------|
| models | `models.py` | `OrderResult` / `OrderStatus` | 3 个（间接）| `test_execution.py` |
| slippage | `slippage.py` | `SlippageModel` | 4 个 | `test_execution.py` |
| paper_broker | `paper_broker.py` | `PaperBroker` | 5 个 | `test_execution.py` |
| base | `base.py` | `BrokerProtocol` | **0 个** ❌ | — |

**SlippageModel 已覆盖**：BUY 加价、SELL 减价、手续费计算、零滑点

**PaperBroker 已覆盖**：BUY 成交、SELL 成交、末行拒绝（insufficient data）、幂等性（重复client_order_id）、手续费、历史记录查询、gross_value 计算

**执行层未覆盖**：`BrokerProtocol` 类型检查；佣金和滑点组合计算精度（浮点累加）；同时多个 OrderIntent 批量提交；订单在数据边界（最后一行）时的拒绝行为细节；零数量订单

### 2.5 Portfolio 持仓追踪器（23 个测试）

| 模块 | 文件 | 函数/类 | 已测试 | 测试文件 |
|------|------|---------|--------|---------|
| models | `models.py` | `Position` / `Portfolio` / `TradeRecord` | 3 个（间接）| `test_portfolio.py` |
| pnl_calculator | `pnl_calculator.py` | `apply_buy` / `apply_sell`（FIFO） | 9 个 | `test_portfolio.py` |
| tracker | `tracker.py` | `PortfolioTracker` | 8 个 | `test_portfolio.py` |
| metrics | `metrics.py` | `Sharpe` / `MaxDD` / `Calmar` / `胜率` / `盈亏比` | 5 个 | `test_portfolio.py` |
| persistence | `persistence.py` | SQLAlchemy Core（`trades` + `portfolio_snapshots`） | 4 个 | `test_portfolio.py` |

**pnl_calculator 已覆盖**：单次买入/多次加权均价；FIFO 盈利/亏损/多批卖出/超数报错/清仓

**tracker 已覆盖**：初始状态、现金扣减、建仓、卖出盈亏、拒绝逻辑、现金不足、快照持久化、交易计数

**metrics 已覆盖**：Sharpe / MaxDD / Calmar / 胜率 / 盈亏比 / summary 字段

**persistence 已覆盖**：存取交易记录、幂等性（重复插入）、快照、symbol 过滤

**portfolio 未覆盖**：开仓成本为 0 的边界（除零保护）；FIFO 多次部分卖出后剩余 lot 正确性；Tracker 消费多个连续 OrderResult 后的累积状态校验；持久化数据库连接失败降级；无交易历史时 metrics 返回值

---

## 3. 覆盖缺口分析（按设计文档风险点）

### 3.1 关键设计约束对照

根据 `design/` 设计文档和 `phase2-summary.md`，以下是 Phase 2 的设计约束及对应测试覆盖情况：

| 设计约束 | 来源 | 风险级别 | 测试覆盖 |
|----------|------|---------|---------|
| 所有过滤器使用 `.rolling(n).mean().shift(1)` 防前视偏差 | `03-signal-filter` | **极高** | ✅ VolumeFilter/ATRFilter 隐式验证 |
| `RiskManager` 门面整合全部组件 | `04-risk-manager` | **极高** | ❌ 未覆盖（仅有各组件独立测试） |
| PaperBroker 下一 bar 开盘价成交 (`next_bar_open * (1±slippage)`) | `05-execution-engine` §4 | 高 | ✅ 已覆盖 |
| 幂等性：`uuid4().hex[:16]` 防止重复成交 | `05-execution-engine` §5 | 高 | ✅ 已覆盖 |
| FIFO 盈亏队列计算 | `06-portfolio-tracker` §3 | 高 | ⚠️ 基本覆盖，多次部分卖出后剩余 lot 未测 |
| 熔断后拒绝所有新订单 | `04-risk-manager` §4 | 高 | ⚠️ 单测已覆盖，集成链路未测 |
| `atr_stop` 的 2:1 风险收益比自动设置止盈 | `04-risk-manager` §3 | 中 | ⚠️ `fixed_take_profit` 已测，ATR 止盈未独立测 |
| EventBus 同步字典分派 | `09-infrastructure` §3 | 中 | ✅ 已覆盖 |
| 执行层不自动提交券商 | `05-execution-engine` §1 | 中 | ✅ 仅 PaperBroker，架构保证 |
| SQLAlchemy Core（非 ORM） | `06-portfolio-tracker` §5 | 中 | ✅ `with engine.connect()` 已测试 |

### 3.2 源码分支覆盖缺失点

#### risk/manager.py — `RiskManager.process()`

```python
# 分支 1: 熔断触发 → 拒绝，不调用后续组件
if self.circuit_breaker.state != CircuitBreakerState.NORMAL:
    return reject("circuit_breaker_active")  # ← 集成场景未测

# 分支 2: 仓位计算 → stop_loss → constraints 顺序依赖
# position_sizer 输出影响 stop_loss，但仅独立测试

# 分支 3: 全局约束（总持仓/最大持仓数）与单笔约束同时违反
# 只返回第一个 reject_reason 还是全部？

# 分支 4: stop_loss 距离为 0 时的 take_profit 自动计算
```

#### execution/paper_broker.py — `PaperBroker.execute()`

```python
# 分支 1: df 最后一行不满足 next_bar 条件 → reject
# 只测了 "末行拒绝"，未测 df 为空数据集时

# 分支 2: 滑点导致 execute_price <= 0
# 未测试（理论上可能但不应产生负价格）

# 分支 3: 同时提交 BUY + SELL（对冲场景）
# 仅单独测试了 BUY 和 SELL，未测两个 OderIntent 同时提交
```

#### risk/circuit_breaker.py — `CircuitBreaker.update_pnl()`

```python
# 分支 1: 日亏损恰好等于 daily_limit
# 当前测试使用 "超过" 阈值，边界 "等于" 未覆盖

# 分支 2: reset() 后的状态恢复
# 测试了 RESET 枚举，但未测实际调用 reset() 后的行为

# 分支 3: 跨月边界（如 1 月 31 日 → 2 月 1 日）
# daily/weekly/monthly 重置在日期边界的行为
```

#### signal/filters/atr_filter.py — `ATRFilter.apply()`

```python
# 分支 1: 信号时间戳早于 ATR 序列所有数据
atr_val = atr_series.loc[atr_series.index <= signal.ts].iloc[-1]
# ← 如果所有 index > signal.ts，iloc[-1] 取的是最后一项而非对应时间

# 分支 2: close_val == 0（除零风险）
vol = atr_val / close_val  # ← close_val=0 时产生 inf
```

#### signal/filters/cooldown_filter.py — `CooldownFilter.apply()`

```python
# 分支 1: 冷却期内方向反转（BUY → SELL）
# 当前 "不同方向独立" 测试仅验证了冷却期后，未测冷却期内转向
```

---

## 4. 补充测试用例设计

### 4.1 Infra 补充测试（P0-P2）

**测试文件**：`tests/test_infra.py`（追加到现有文件）

| # | 测试用例 | 优先级 | 测试目的 | 输入 | 预期结果 |
|---|---------|--------|---------|------|---------|
| IC1 | `test_system_config_defaults` | P1 | SystemConfig 独立默认值 | `SystemConfig()` | `data_dir` 等字段有正确默认值 |
| IC2 | `test_data_config_defaults` | P1 | DataConfig cache_dir / ttl 默认值 | `DataConfig()` | 与 YAML 默认值一致 |
| IC3 | `test_config_field_range_validation` | P0 | `risk_per_trade` 越界抛 ValidationError | `risk_per_trade=0.001`（=ge 边界） | 不抛异常 |
| IC4 | `test_config_field_above_max_raises` | P0 | `risk_per_trade=1.0`（超过 le=0.05） | 超出范围值 | `ValidationError` |
| IC5 | `test_config_field_below_min_raises` | P1 | `slippage_pct=-0.01`（小于 ge=0） | 负数值 | `ValidationError` |
| IC6 | `test_backtest_config_use_next_open` | P1 | BacktestConfig use_next_open 默认 True | `BacktestConfig()` | `use_next_open=True` |
| IC7 | `test_circuit_breaker_config_limits` | P1 | 熔断器默认阈值 | `CircuitBreakerConfig()` | `daily=-0.02`, `weekly=-0.05`, `monthly=-0.10` |
| IC8 | `test_find_default_yaml` | P1 | `_find_default_yaml()` 向上查找 | 当前目录无 config 但上级有 | 找到上级 config/default.yaml |
| IC9 | `test_eventbus_duplicate_subscribe` | P2 | 同一 handler 重复订阅 | subscribe 两次后 publish | handler 被调用次数明确（1 次或 2 次取决于设计意图）|
| IC10 | `test_eventbus_handler_without_name` | P3 | lambda handler 异常隔离 | 订阅 lambda，publish | 异常被隔离，不阻断其他 handler |

### 4.2 Signal Filter 补充测试（P0-P2）

**测试文件**：`tests/test_signal_filter.py`（追加到现有文件）

| # | 测试用例 | 优先级 | 测试目的 | 输入 | 预期结果 |
|---|---------|--------|---------|------|---------|
| SF1 | `test_volume_boundary_exact_mean` | P1 | 成交量恰好等于 20 日均值 | vol=均值 | 行为明确（通过或拒绝，取决于 `<=` vs `<`） |
| SF2 | `test_volume_boundary_mean_times_1_5` | P1 | 成交量恰好 = 1.5 倍均值 | vol=1.5*mean | 行为明确 |
| SF3 | `test_atr_signal_before_data` | P1 | 信号时间戳早于所有 ATR 数据 | 信号 ts 比数据最早时间早 1 天 | 放行或降级处理，不崩溃 |
| SF4 | `test_atr_close_val_zero` | P0 | close_val == 0 除零风险 | ATR>0, close=0 | 不抛除零异常，行为合理 |
| SF5 | `test_sentiment_bullish_allow_buy` | P1 | 牛市允许 BUY 信号 | benchmark > 200MA, signal=BUY | 通过 |
| SF6 | `test_sentiment_bullish_reject_sell` | P1 | 牛市拒绝 SELL 信号 | benchmark > 200MA, signal=SELL | 拒绝 |
| SF7 | `test_time_window_close_buffer` | P1 | 收盘缓冲期内拒绝 | 14:50（收盘前 10 分钟） | 拒绝 |
| SF8 | `test_time_window_across_day` | P2 | 跨日边界（23:59 → 00:01） | 两个连续时间戳跨日 | 过滤器正确处理 |
| SF9 | `test_cooldown_reverse_direction_during_cooldown` | P1 | 冷却期内反向信号 | BUY→冷却中→SELL | 拒绝（因 BUY 冷却中，方向独立） |
| SF10 | `test_pipeline_filter_order` | P1 | from_config 构建顺序与 config 一致 | YAML 配置 3 个 filter | 流水线按 config 顺序执行 |
| SF11 | `test_pipeline_all_rejected` | P2 | 所有过滤器均拒绝 | 刻意构造触发所有过滤器的数据 | FilterResult 全部 rejected |
| SF12 | `test_filter_result_reject_reasons_preserved` | P1 | reject_reason 保存在 FilterResult | 多个信号被不同原因拒绝 | reasons 包含所有拒绝原因 |

### 4.3 Risk Manager 补充测试（P0-P2）

**测试文件**：`tests/test_risk_manager.py`（追加到现有文件）

| # | 测试用例 | 优先级 | 测试目的 | 输入 | 预期结果 |
|---|---------|--------|---------|------|---------|
| RM1 | `test_risk_manager_full_pipeline_approve` | P0 | RiskManager 全链路通过 | 正常 OrderIntent | 返回 approve，含仓位+止损+止盈 |
| RM2 | `test_risk_manager_circuit_breaker_reject` | P0 | 熔断激活时拒绝订单 | circuit_breaker=DAILY → process | 返回 reject，reason="circuit_breaker_active" |
| RM3 | `test_risk_manager_constraint_reject` | P0 | 超总持仓上限时拒绝 | 已有 5 个持仓 → 新订单 | 返回 reject |
| RM4 | `test_risk_manager_multiple_violations` | P1 | 同时违反约束和熔断 | 熔断+超限 | 返回第一个 reject_reason（或全部） |
| RM5 | `test_risk_manager_stop_loss_integration` | P1 | RiskManager 中 stop_loss 自动计算 | approve 的 OrderIntent | `stop_loss` 和 `take_profit` 正确附加 |
| RM6 | `test_atr_position_size_zero_atr` | P0 | atr_value=0 时的安全降级 | ATR 序列全为 0 | 不抛除零异常，回退到 fixed_amount_size |
| RM7 | `test_atr_position_size_negative_equity` | P1 | account_equity <= 0 | equity=-10000 | 不崩溃，返回 0 或合理值 |
| RM8 | `test_time_stop_bars_triggered` | P1 | 持仓超过 N bars 触发止损 | 持仓 bars > time_stop_bars | stop_reason="time_stop" |
| RM9 | `test_circuit_breaker_boundary_exact` | P1 | 日亏损恰好等于阈值（-2%） | daily_pnl == -0.02 | 行为明确（触发/不触发） |
| RM10 | `test_circuit_breaker_reset_after_new_day` | P0 | 跨日后日熔断自动恢复 | DAILY → next_day → process | 状态恢复 NORMAL |
| RM11 | `test_circuit_breaker_monthly_persists` | P1 | 月熔断不随跨日恢复 | MONTHLY → next_day | 状态保持 MONTHLY |
| RM12 | `test_circuit_breaker_multi_level_priority` | P1 | 日+周同时触发时取最高级别 | daily+weekly 都超过阈值 | state=WEEKLY（比 DAILY 更严重） |

### 4.4 Execution 补充测试（P0-P2）

**测试文件**：`tests/test_execution.py`（追加到现有文件）

| # | 测试用例 | 优先级 | 测试目的 | 输入 | 预期结果 |
|---|---------|--------|---------|------|---------|
| EX1 | `test_paper_broker_empty_dataframe` | P0 | 空 DataFrame 提交订单 | df 为空 | reject，不清算 |
| EX2 | `test_paper_broker_zero_quantity` | P0 | 零数量订单 | qty=0 | reject 或安全降级 |
| EX3 | `test_paper_broker_negative_slippage_price` | P1 | 滑点导致负执行价 | slippage_pct > 1.0 | 拒绝或 clamp 到 min_price |
| EX4 | `test_paper_broker_batch_orders` | P1 | 同时提交多个 OrderIntent | 3 个不同 symbol 订单 | 全部成交，不相互干扰 |
| EX5 | `test_paper_broker_order_history_persistence` | P1 | 历史记录正确累积 | 连续 5 笔交易 | `get_history()` 返回 5 条 |
| EX6 | `test_slippage_pct_boundary` | P2 | 零滑点 + 零手续费边界 | slippage=0, commission=0 | execute_price == next_open |

### 4.5 Portfolio 补充测试（P0-P2）

**测试文件**：`tests/test_portfolio.py`（追加到现有文件）

| # | 测试用例 | 优先级 | 测试目的 | 输入 | 预期结果 |
|---|---------|--------|---------|------|---------|
| PF1 | `test_fifo_multi_partial_sell_lots` | P0 | 多次部分卖出后仓库正确 | BUY 200 → SELL 50 → SELL 100 → SELL 50 | 最终 qty=0, lots 为空, 各笔盈亏正确 |
| PF2 | `test_fifo_large_buy_many_sells` | P1 | 大批买入后多次小额卖出 | BUY 1000 → 10×SELL 100 | FIFO 队列耗尽，总盈亏与单笔买入一致 |
| PF3 | `test_tracker_consecutive_orders` | P1 | 连续 3 个 OrderResult 累积状态 | 建仓→加仓→平仓 | 累计 P&L = 各笔 P&L 之和 |
| PF4 | `test_metrics_no_trades` | P0 | 无交易时 metrics 返回值 | 空交易列表 | 不抛异常，返回 0 或 NaN 的合理值 |
| PF5 | `test_metrics_extreme_values` | P1 | 极端盈亏（+500% / -80%）| 包含极端值的交易历史 | Sharpe 等指标合理（不因单笔极端值崩溃） |
| PF6 | `test_persistence_connection_failure` | P1 | 数据库连接失败降级 | SQLite 文件权限只读 | 不崩溃，日志记录错误 |
| PF7 | `test_persistence_snapshot_roundtrip` | P1 | 快照写入后读回一致性 | 写入 snapshot → 读取 | 各字段值与写入一致 |
| PF8 | `test_pnl_zero_cost_division` | P0 | 开仓成本为 0 | 成本=0 的 buy，正常 sell | 不除零，处理合理 |

---

## 5. 测试优先级汇总

### 5.1 P0（阻塞级）— 共计 17 项

这些测试对应**一旦出错将导致资金亏损或系统不可用**的核心功能：

| # | 模块 | 测试 | 风险后果 |
|---|------|------|---------|
| 1 | config | IC3/IC4 `test_config_field_range_validation` | 非法参数被接受，导致仓位/风控参数异常 |
| 2 | signal | SF4 `test_atr_close_val_zero` | 除零异常崩溃 |
| 3 | risk | RM1 `test_risk_manager_full_pipeline_approve` | RiskManager 门面不可用 |
| 4 | risk | RM2 `test_risk_manager_circuit_breaker_reject` | 熔断失效，巨额亏损 |
| 5 | risk | RM3 `test_risk_manager_constraint_reject` | 超限持仓未被阻止 |
| 6 | risk | RM6 `test_atr_position_size_zero_atr` | ATR=0 除零崩溃 |
| 7 | risk | RM10 `test_circuit_breaker_reset_after_new_day` | 熔断器不恢复，永久锁死 |
| 8 | execution | EX1 `test_paper_broker_empty_dataframe` | 空数据崩溃 |
| 9 | execution | EX2 `test_paper_broker_zero_quantity` | 零数量订单未防御 |
| 10 | portfolio | PF1 `test_fifo_multi_partial_sell_lots` | FIFO 多次部分卖出后 lot 残留 |
| 11 | portfolio | PF4 `test_metrics_no_trades` | 无交易时指标计算崩溃 |
| 12 | portfolio | PF8 `test_pnl_zero_cost_division` | 除零异常崩溃 |

### 5.2 P1（高优先级）— 共计 25 项

覆盖**核心功能的边界条件和关键路径**：

infra：IC1, IC2, IC5, IC6, IC7, IC8（6 项）  
signal：SF1, SF2, SF3, SF5, SF6, SF7, SF9, SF10, SF12（9 项）  
risk：RM4, RM5, RM7, RM8, RM9, RM11, RM12（7 项）  
execution：EX3, EX4, EX5（3 项）  
portfolio：PF2, PF3, PF5, PF6, PF7（5 项）

### 5.3 P2（中优先级）— 共计 10 项

鲁棒性增强和边界条件覆盖。

infra：IC9  
signal：SF8, SF11  
risk：（无）  
execution：EX6  
portfolio：（无）

### 5.4 P3（低优先级）— 共计 1 项

IC10 lambda handler 无 `__name__` 异常隔离。

---

## 6. Phase 2 集成测试设计（新建文件）

**测试文件**：`tests/test_integration_phase2.py`（新文件）

| # | 测试用例 | 优先级 | 测试目的 | 输入 | 预期结果 |
|---|---------|--------|---------|------|---------|
| IT2-1 | `test_signal_to_risk_pipeline` | P0 | 策略信号 → 信号过滤 → 风险管理 | 合成 OHLCV + dual_ma 信号 | RiskManager 输出 OrderIntent |
| IT2-2 | `test_signal_to_execution_pipeline` | P0 | 信号 → 过滤 → 风控 → 成交 | 合成数据全链路 | PaperBroker 返回 OrderResult |
| IT2-3 | `test_signal_to_portfolio_pipeline` | P0 | 信号 → 过滤 → 风控 → 成交 → 持仓 | 合成数据 + 连续 5 个信号 | PortfolioTracker 持仓正确更新 |
| IT2-4 | `test_circuit_breaker_integration` | P0 | 熔断触发后整个链路拒绝 | 先触发熔断 → 再提交信号 | 所有环节拒绝 |
| IT2-5 | `test_filter_pipeline_rejects_all` | P1 | 所有过滤器拒绝时链路中止 | 构造触发所有过滤器的数据 | 不进入 RiskManager |
| IT2-6 | `test_eventbus_end_to_end` | P1 | EventBus 连接所有模块 | 发布 signal_event → 各模块消费 | 每个模块的 handler 被正确调用 |

---

## 7. 测试执行指南

### 7.1 环境要求

```bash
# Python 环境
/Users/rickouyang/miniforge3/envs/py312trade  # Python 3.12.13

# 额外依赖（Phase 2 新增）
/Users/rickouyang/miniforge3/envs/py312trade/bin/pip install sqlalchemy pydantic-settings
```

### 7.2 运行现有测试

```bash
# 运行全部已有测试
/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest mytrader/tests/ -v

# 仅某模块
/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest mytrader/tests/test_infra.py -v
/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest mytrader/tests/test_signal_filter.py -v
/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest mytrader/tests/test_risk_manager.py -v
/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest mytrader/tests/test_execution.py -v
/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest mytrader/tests/test_portfolio.py -v

# 带覆盖率
/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest mytrader/tests/ \
  --cov=mytrader --cov-report=term-missing

# 聚焦特定模块
/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest mytrader/tests/ \
  -k "circuit_breaker" -v
/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest mytrader/tests/ \
  -k "fifo" -v
```

### 7.3 运行补充测试（规划中）

```bash
# Infra 补充
pytest mytrader/tests/test_infra.py -v -k "config_ or eventbus_"

# Signal Filter 补充
pytest mytrader/tests/test_signal_filter.py -v -k "boundary or reverse or order"

# Risk Manager 补充
pytest mytrader/tests/test_risk_manager.py -v -k "pipeline or circuit_breaker_reset or zero_atr"

# Execution 补充
pytest mytrader/tests/test_execution.py -v -k "zero or batch or empty"

# Portfolio 补充
pytest mytrader/tests/test_portfolio.py -v -k "multi_partial or no_trades or zero_cost"

# 集成测试
pytest mytrader/tests/test_integration_phase2.py -v

# 全量
pytest mytrader/tests/ -v --cov=mytrader --cov-report=term-missing
```

### 7.4 测试数据要求

| 测试类型 | 数据来源 | 说明 |
|---------|---------|------|
| config | `tmp_path` + 临时 YAML 文件 | 不依赖真实 config 文件 |
| event_bus | 内存对象 | 无外部依赖 |
| signal filters | `make_ohlcv()` 合成 OHLCV + 手动构造信号 | 与 Phase 1 一致 |
| position_sizer | 传参计算 | 纯函数，无外部依赖 |
| circuit_breaker | 内存状态 | 不依赖数据库 |
| paper_broker | 合成 OHLCV DataFrame | 无网络 |
| pnl_calculator | 传参计算 | 纯函数 |
| persistence | `sqlite:///:memory:` | 内存数据库，隔离 |
| metrics | 构造交易列表 | 纯函数 |
| integration | 合成数据全链路 | 不依赖网络 |

### 7.5 当前通过率

```
Phase 1: 108 passed ✅
Phase 2: 94 passed ✅
合计：202 passed, 0 failed ✅
```

### 7.6 预期补充后测试数量

| 文件 | 现有 | 补充后 | 新增 |
|------|------|--------|------|
| `test_infra.py` | 12 | 22 | +10 |
| `test_signal_filter.py` | 25 | 37 | +12 |
| `test_risk_manager.py` | 22 | 34 | +12 |
| `test_execution.py` | 12 | 18 | +6 |
| `test_portfolio.py` | 23 | 31 | +8 |
| `test_integration_phase2.py` | 0 | 6 | +6（新建） |
| **Phase 2 新增合计** | — | — | **+54** |
| **全项目合计** | **202** | **~256** | — |

---

## 8. 关键设计约束与风险点覆盖评估

### 8.1 过滤器防前视偏差 — 极高风险 ⚠️

| 约束 | 覆盖 |
|------|------|
| VolumeFilter `rolling(20).mean().shift(1)` | ✅ 现有测试覆盖 |
| ATRFilter 使用历史 ATR 值 | ⚠️ 隐式验证，无专项破坏性测试 |
| 所有过滤器不访问 future 数据 | ⚠️ 无专项检查（可参照 Phase 1 前视偏差破坏性测试模式） |
| CooldownFilter 仅依赖历史同向信号时间戳 | ✅ 方向独立测试已验证 |

### 8.2 风险管理器整合 — 极高风险 ❌

| 约束 | 覆盖 |
|------|------|
| `RiskManager` 门面串联全部组件 | ❌ RM1 待补充 |
| 熔断触发 → 拒绝所有订单 | ❌ 仅 circuit_breaker 单测，未验证 RiskManager 中链路 |
| 仓位 + 止损 + 约束同时作用 | ❌ 各组件独立测试，未验证整合后的相互影响 |
| OrderIntent 幂等 ID 贯穿全部组件 | ⚠️ 部分覆盖（仅 risk/models 中有 ID 测试） |

### 8.3 熔断器安全 — 高风险 ⚠️

| 约束 | 覆盖 |
|------|------|
| 日/周/月三层级联 | ✅ 状态枚举和转换已覆盖 |
| 跨日重置 | ❌ RM10 待补充 |
| 月熔断跨日保持 | ❌ RM11 待补充 |
| 多级同时触发优先级 | ❌ RM12 待补充 |
| 熔断后恢复到 NORMAL | ❌ reset() 实际调用未测 |

### 8.4 执行引擎正确性 — 中风险 ⚠️

| 约束 | 覆盖 |
|------|------|
| `next_bar_open * (1+slippage)` BUY 成交价 | ✅ 已覆盖 |
| `next_bar_open * (1-slippage)` SELL 成交价 | ✅ 已覆盖 |
| 幂等性（重复 client_order_id） | ✅ 已覆盖 |
| 末行拒绝 | ✅ 已覆盖 |
| 佣金计算 | ✅ 已覆盖 |
| 空数据/零数量防御 | ❌ EX1/EX2 待补充 |
| 批量订单不相互干扰 | ❌ EX4 待补充 |

### 8.5 FIFO 盈亏计算 — 高风险 ⚠️

| 约束 | 覆盖 |
|------|------|
| 单次买入/卖出 | ✅ 已覆盖 |
| 多批买入加权均价 | ✅ 已覆盖 |
| FIFO 盈利/亏损 | ✅ 已覆盖 |
| 多批部分卖出 | ⚠️ 2 次卖出已测，多次剩余 lot 未测 |
| 超量卖出报错 | ✅ 已覆盖 |
| 成本为 0 除零 | ❌ PF8 待补充 |

### 8.6 持久化可靠性 — 中风险 ⚠️

| 约束 | 覆盖 |
|------|------|
| SQLAlchemy Core `with engine.connect()` | ✅ 已覆盖 |
| 交易记录存取 | ✅ 已覆盖 |
| 快照存取 | ✅ 已覆盖 |
| 幂等性（重复插入） | ✅ 已覆盖 |
| 连接失败降级 | ❌ PF6 待补充 |

---

## 附录 A：Phase 2 测试文件结构（规划）

```
mytrader/tests/
├── __init__.py
├── conftest.py                      # 共享 fixtures（已有，需追加 Phase 2 fixtures）
├── test_data_layer.py               # Phase 1（已有）
├── test_cache.py                    # Phase 1（已有）
├── test_provider.py                 # Phase 1（已有）
├── test_strategy.py                 # Phase 1（已有）
├── test_backtest.py                 # Phase 1（已有）
├── test_integration.py              # Phase 1（已有）
├── test_infra.py                    # Phase 2（已有 12 个，追加 10 个）
├── test_signal_filter.py            # Phase 2（已有 25 个，追加 12 个）
├── test_risk_manager.py             # Phase 2（已有 22 个，追加 12 个）
├── test_execution.py                # Phase 2（已有 12 个，追加 6 个）
├── test_portfolio.py                # Phase 2（已有 23 个，追加 8 个）
└── test_integration_phase2.py       # Phase 2 集成测试（新建，6 个）
```

## 附录 B：Phase 2 共享 Fixtures 建议（追加到 conftest.py）

```python
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta

@pytest.fixture
def sample_ohlcv_with_index():
    """50 行合成 OHLCV，带 DatetimeIndex（UTC）和 open/high/low/close/volume 列。"""
    idx = pd.date_range("2023-01-03 09:30", periods=50, freq="1h", tz="UTC")
    rng = np.random.RandomState(42)
    close = 100 + rng.randn(50).cumsum()
    return pd.DataFrame({
        "open": close + rng.uniform(-0.5, 0.5, 50),
        "high": close + rng.uniform(0, 1.0, 50),
        "low": close - rng.uniform(0, 1.0, 50),
        "close": close,
        "volume": rng.randint(1_000_000, 10_000_000, 50).astype(float),
    }, index=idx)

@pytest.fixture
def sample_signal_buy():
    """标准 BUY 信号 FilteredSignal。"""
    from mytrader.signal.models import FilteredSignal
    return FilteredSignal(
        ts=pd.Timestamp("2023-01-04 10:00", tz="UTC"),
        symbol="AAPL",
        direction=1,  # BUY
        signal_value=1,
        price_hint=150.0,
    )

@pytest.fixture
def sample_signal_sell():
    """标准 SELL 信号 FilteredSignal。"""
    from mytrader.signal.models import FilteredSignal
    return FilteredSignal(
        ts=pd.Timestamp("2023-01-04 14:00", tz="UTC"),
        symbol="AAPL",
        direction=-1,  # SELL
        signal_value=-1,
        price_hint=148.0,
    )

@pytest.fixture
def sample_order_intent():
    """标准 OrderIntent。"""
    from mytrader.risk.models import OrderIntent
    return OrderIntent(
        symbol="AAPL",
        direction=1,
        quantity=100,
        order_type="limit",
        price=150.0,
        stop_loss=145.0,
        take_profit=160.0,
    )

@pytest.fixture
def tmp_db_path(tmp_path):
    """临时 SQLite 数据库路径。"""
    db_path = tmp_path / "test_portfolio.db"
    yield f"sqlite:///{db_path}"
```

## 附录 C：Phase 2 风险登记表

| 风险编号 | 风险描述 | 严重程度 | 影响 | 缓解措施 | 对应测试 |
|---------|---------|---------|------|---------|---------|
| R01 | 熔断器不恢复导致永久锁死 | 极高 | 系统无法交易 | 跨日/跨周/跨月自动重置测试 | ❌ RM10-RM12 待补充 |
| R02 | RiskManager 门面未串联测试 | 极高 | 组件间接口不匹配 | 全链路集成测试 | ❌ RM1 待补充 |
| R03 | ATR 除零导致崩溃 | 高 | 波动率过滤/仓位计算异常 | 零值防御测试 | ❌ SF4, RM6 待补充 |
| R04 | FIFO 多次部分卖出 lot 残留 | 高 | 盈亏计算错误 | 多次部分卖出测试 | ❌ PF1 待补充 |
| R05 | 过滤器防前视偏差不完整 | 高 | 虚高信号通过率 | 破坏性前视偏差专项测试 | ⚠️ 部分覆盖 |
| R06 | 配置字段越界未被拦截 | 高 | 异常参数导致风险敞口过大 | Pydantic 约束验证测试 | ❌ IC3-IC5 待补充 |
| R07 | 持久化连接失败未降级 | 中 | 交易记录丢失 | 连接失败降级测试 | ❌ PF6 待补充 |
| R08 | 零数量/空数据提交未防御 | 中 | 执行引擎崩溃 | 零数量和空数据防御测试 | ❌ EX1-EX2 待补充 |
