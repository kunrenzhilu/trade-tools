一、可能导致策略失效的核心问题（严重）
1. 回测 ensemble 与实盘 ensemble 逻辑不一致 ⚠️
矛盾所在：

回测阶段（07-backtest-module.md 10.3）：ensemble_signal() 对整个时间序列做加权投票（每日信号对齐后加权）
实盘阶段（12-strategy-matrix.md 6 节 + 13-signal-ranker.md 3 节）：只取 sig_series.iloc[-1]（最后一根 bar 的离散值 1/-1/0），再在 Signal Ranker 中做加权投票
12-strategy-matrix.mdL249-L254

        latest = int(sig_series.iloc[-1])
        if latest == 0:
            continue   # HOLD
为什么会导致策略失效：回测验证的是"时间序列上的加权组合"，实盘执行的是"单点离散值的加权组合"。两者数学上不等价。一个在回测中表现好的 ensemble 权重，在实盘的单点聚合下可能完全失效，因为丢失了信号的时间维度信息。

建议：实盘的 Signal Ranker 聚合逻辑必须与回测的 ensemble_signal() 严格对齐，或者在 MatrixBacktest 阶段就产出 ensemble 后的单一 signal series，实盘只取最后一根 bar。

2. "只看最后一根 bar" 漏掉趋势中段信号 ⚠️
问题：12-strategy-matrix.md 第 6 节只取 sig_series.iloc[-1]。但策略输出的是事件型信号（交叉瞬间=1，其余=0）。如果双均线在 3 天前金叉，今天 signal=0（HOLD），系统不会入场，但趋势可能还在继续。

影响：趋势策略（dual_ma、MACD）的入场点会被大量漏掉——交叉只在一天发生，如果当天不是扫描日就彻底错过。

建议：改为状态型判断（如 signal != 0 的最后一次出现距今 N bar 内仍有效），或改用持仓状态信号（1=持有多头，-1=持有空头，0=空仓）而非事件信号。

3. 复权数据源混用导致价格跳变 ⚠️
10-market-data-store.mdL231-L234

- Alpaca `adjustment="all"` 与 yfinance `auto_adjust=True` 都做后复权
- 但两源复权算法可能有细微差异 → `source` 字段记录来源，避免混用导致价格跳变
- 建议：同一标的尽量固定用同一数据源
问题："尽量固定"不是强制约束。当 Alpaca 某天限速/宕机、fallback 到 yfinance 时，同一标的的后复权基准不同 → 历史价格出现跳变 → 均线/MACD/布林带计算全部出错 → 产生假信号。

建议：要么强制单源（fallback 时记录但不写入，等待主源恢复），要么存储原始未复权价格 + 调整因子，在读取时统一计算复权，而非存储复权后的价格。

4. 幸存者偏差被低估
11-universe-manager.mdL170-L173

- 回测时若只用**当前**成分股，会引入幸存者偏差（剔除了被踢出指数的标的）
- 严格做法：回测用历史时点的成分股快照
- Phase 5 初期可接受当前成分股（简化），但需在文档标注此偏差
问题：文档标注为"中风险"，但对均值回归策略（RSI、布林带，分配给 S&P 500 低波动组）影响极大。被踢出 S&P 500 的股票通常经历了暴跌，不纳入会系统性高估策略收益。5 年回测窗口内（2021-2026），S&P 500 成分变动约 20-30 只，足以显著扭曲回测结论。

建议：至少在回测报告中输出"成分股变动列表"和影响评估，或使用 point-in-time 成分股数据（如从 Alpaca 或第三方获取历史成分股快照）。

5. 波动率分组动态变化导致回测/实盘不一致
问题：11-universe-manager.md 6 节说波动率分层是动态的（每周/每月重算）。但回测时（07-backtest-module.md 10.3），一只标的被固定分到当前所属组，用该组参数回测 5 年。

例如 TSLA 当前是"高波动组"，用高波动参数（slow=60）回测 5 年。但 5 年中 TSLA 可能经历过"中波动"时期，当时 slow=60 的参数并不适合。

影响：回测结果不反映真实场景（分组会随时间变化），系统性高估或低估策略表现。

建议：回测时用 point-in-time 分组（每月按当时波动率分组），或至少标注此假设的影响。

二、设计不周全的问题（中高）
6. Top-K=5 与风控约束的交互未协调
存在多处约束冲突：

约束	值	来源
Top-K 选股	5	13-signal-ranker.md
max_concurrent_positions	5	04-risk-manager.md
max_single_position_pct	20%	04-risk-manager.md
max_sector_exposure_pct	40%	04-risk-manager.md
risk_per_trade	1%	04-risk-manager.md
冲突场景：

Top-5 里有 3 只科技股（Nasdaq 占 57%，很可能），sector 限制 40% → 只能开 2 只 → 第 3 只被拒 → 但没有递补机制（13-signal-ranker.md 8.2 提到"已持仓不占名额"但没有递补设计）→ 实际持仓 < 5 → 资金利用率低
ATR 仓位法算出低波动股仓位可能远超 20%（risk_per_trade=1% / ATR×2=2% → 50% 仓位），需要取 min，但没有文档说明优先级
按等权 20% × 5 = 100%，但 max_total_exposure=80%，矛盾
建议：Signal Ranker 应输出候选名单（如 Top-10），Risk Manager 逐个尝试下单，被拒则递补下一个，直到资金/仓位约束用尽。

7. DuckDB 读 SQLite 的性能承诺可能无法兑现
10-market-data-store.mdL74-L75

> DuckDB 原生支持 `sqlite_scan()` 直接查询 SQLite 文件，**可避免数据双写**——
> 实盘只写 SQLite，回测时 DuckDB 直接读 SQLite 表做列式分析。这是首选方案。
问题：sqlite_scan() 是通过 SQLite 的行式引擎读取再转 DuckDB 格式的。数据仍在 SQLite 的行式 B-tree 中，DuckDB 无法获得真正的列式存储优势（如列压缩、列式向量化扫描）。对于 42MB 的数据量可能差别不大，但"快 10-100×"的承诺不成立。

建议：如果要真正的列式加速，应该用 DuckDB 原生表或 Parquet 文件存储回测数据，而非依赖 sqlite_scan() 代理。或者直接用 Parquet（47MB 的 Parquet 读取也很快）。

8. 回测 5 年窗口的时间范围矛盾
07-backtest-module.md 10.2 说：

code

5 年 → 覆盖完整牛熊周期：
        2020 崩盘 + 2021 牛市 + 2022 熊市 + 2023-24 复苏
但当前日期是 2026-06-23，5 年窗口是 2021-06 ~ 2026-06。2020 崩盘（2020-03）不在窗口内。CHANGELOG 也说"5 年覆盖 2020 崩盘"但实际覆盖不到。

建议：修正描述为"覆盖 2022 熊市 + 2023-24 复苏 + 2025-26 行情"，或扩大窗口到 6-7 年（但需权衡市场结构变化）。

9. 矩阵回测取"组内平均 Sharpe"方法有误
07-backtest-module.mdL346-L348

                sharpes = [backtest_one(data[s], strategy, params).sharpe for s in symbols]
                avg_sharpe = mean(sharpes)
                candidates.append((strategy, params, avg_sharpe))
问题：Sharpe 是比率（收益/波动），直接平均无统计意义。两只标的：A 的 Sharpe=2.0（高收益高波动），B 的 Sharpe=0.5（低收益低波动），平均=1.25，但实际组合 Sharpe 可能完全不同。

正确做法：将组内所有标的的日收益率合并为一个组合（等权或按市值加权），计算组合的 Sharpe。或者在组内做 portfolio backtest 而非独立单标的 backtest。

10. Walk-Forward 窗口重叠率过高
07-backtest-module.md 10.5：

code

训练窗口 5 年 → 优化权重 → 应用 1 个月 → 滚动前移
相邻两次优化窗口重叠 59/60 = 98.3%。这意味着：

权重变化极缓慢，月度更新的意义不大（惯性太大）
但如果市场突变（如 2020-03 式崩盘），5 年窗口的旧数据拖累，权重无法快速适应
建议：考虑用更短训练窗口（如 2-3 年）+ 更频繁更新，或用 EMA 衰减权重让近期数据权重更高，而非简单滑动窗口。

三、其他值得注意的问题
11. 策略函数签名限制策略类型
02-strategy-engine.md 说策略签名是 (close: pd.Series, **params) -> pd.Series，12-strategy-matrix.md 调用时只传 df["close"]。但部分策略需要 high/low/volume（如 ATR 计算、成交量确认）。虽然 02 说"额外传入 df"，但 Matrix Runner 没有传 df 的逻辑，限制只能用 close 型策略。

12. Config 仍是 v1 格式未更新
09-infrastructure.md 的 default.yaml 还是 v1 的单策略格式（strategy: name: dual_ma），与 v2 的多策略分组 + strategy_weights.json 完全脱节。DI Container（build_app）也没有装配新模块（MarketDataStore、UniverseManager、StrategyMatrixRunner、SignalRanker）。

13. SELL 信号与资金结算时序
13-signal-ranker.md 8.1 说"SELL 优先处理，先平仓再开仓"。但 Alpaca 的资金结算有 T+1 延迟（当日卖出所得资金当日可用来买新股，但需看券商规则）。如果 SELL 未结算就提交 BUY，可能因资金不足被拒。需要确认 Alpaca 的 unsettled funds 政策。

14. 隔夜跳空风险对短线策略致命
策略定位"持仓 1-5 天"（00-overview.md），意味着必须持仓过夜。美股隔夜跳空（盘后/盘前大波动）是短线策略的主要风险来源，但 04-risk-manager.md 的缓解措施仅"了解券商止损单类型"，没有设计：

隔夜仓位上限限制
财报前强制平仓（03-signal-filter.md 2.5 提到财报但只是"标记"）
VIX 阈值降低隔夜仓位
15. 回测成本假设与实盘不符
07-backtest-module.md 用 fees=0.001（0.1%），但 Alpaca 零佣金，实际 fees≈0。同时 slippage=0.001（0.1%）对 Top-K 选出的标的（可能是流动性中等的高信念标的）可能偏低。高估费用、低估滑点，方向性错误。

16. 矩阵回测伪代码缺少 open 参数
07-backtest-module.md 第 9 节明确说"实盘一般在下一根 bar 的开盘价执行，需传 open=open_series"，但 10.3 的 backtest_one() 伪代码没有体现 open 参数。如果矩阵回测用 close 执行而实盘用 open 执行，回测/实盘不一致。

17. 半天交易日同步延迟
10-market-data-store.md 说"16:30 ET 收盘后同步"。但美股半天交易日（如感恩节次日、圣诞前夜）13:00 收盘，16:30 才同步意味着 3.5 小时延迟。虽不影响交易（已收盘），但影响盘后分析和 Walk-Forward 重优化的及时性。

18. 进程时区与交易时区分离的混乱
09-infrastructure.md 系统时区 Asia/Shanghai，Job 时区 America/New_York。日志时间用 Shanghai 还是 ET？告警消息中的时间用哪个？容易导致复盘时时间错位（如"09:35 盘前扫描"在日志里显示 21:35）。

四、建议优先修复的问题排序
优先级	问题	影响
P0	#1 回测/实盘 ensemble 逻辑不一致	策略验证完全失效
P0	#2 只看最后一根 bar 漏信号	趋势策略大量漏单
P0	#3 复权数据源混用	价格跳变产生假信号
P1	#6 Top-K 与风控约束未协调	资金利用率低 / 约束冲突
P1	#5 波动率分组动态 vs 回测静态	回测结果不反映实际
P1	#9 组内平均 Sharpe 计算错误	策略排名不可靠
P1	#16 矩阵回测缺 open 参数	回测/实盘不一致
P2	#4 幸存者偏差	回测系统性偏高
P2	#10 Walk-Forward 窗口重叠过高	适应性差
P2	#14 隔夜跳空风控缺失	短线策略主要风险
P3	#7 DuckDB 性能承诺	影响不大（42MB）
P3	#12 Config 未更新到 v2	实现时会暴露
最严重的是 #1 和 #2——它们直接破坏了"回测/实盘一致性"这个核心设计原则，导致回测验证的结果在实盘中无法复现。建议在 Phase 5 编码前先修正这两个设计缺陷。