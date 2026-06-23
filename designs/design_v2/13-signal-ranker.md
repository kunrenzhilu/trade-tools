# Module 13 — Signal Ranker（信号排名与选股）

> 上级文档：[00-overview.md](./00-overview.md)  
> Phase 5 新增模块

---

## 1. 职责

- 接收 Strategy Matrix Runner 输出的 **M×N 条 Signal**
- 解决同一标的的**多策略信号冲突**（聚合为单一判断）
- 按综合得分对所有候选标的**排名**
- 输出 **Top-K 标的**（默认 K=5），供下游 Signal Filter → Risk Manager → 执行

> v1 没有此模块——信号直接进风控下单。
> v2 的核心增量：扫 550 只 → **只交易最强的 Top-K**，从"全下单"变"精选下单"。

---

## 2. 在数据流中的位置

```
Strategy Matrix Runner  → M×N 条 Signal（含 strategy_name, confidence, group_id）
        ↓
Signal Ranker
   1. 按 symbol 聚合多策略信号（冲突解决）
   2. 计算每个候选的综合得分
   3. 排名，取 Top-K
        ↓ K 条 RankedSignal
Signal Filter → Risk Manager → Execution
```

---

## 3. 第一步：同标的多策略聚合（冲突解决）

一只标的可能收到多条信号（dual_ma BUY + macd SELL）。聚合规则：

```
方案 A（加权投票，推荐）：
  combined_score = Σ(direction_i × weight_i × confidence_i)
  combined > +threshold  → 聚合为 BUY
  combined < -threshold  → 聚合为 SELL
  否则                   → 丢弃（分歧太大，不交易）

方案 B（一致性要求）：
  要求组内多数策略同向（如 ≥2/3 同向）才保留
  → 更保守，信号更少但质量更高
```

> 复用 Phase 1 的 `ensemble_signal()` 思想。聚合后每个 symbol 至多 1 条信号。
> **分歧标的直接丢弃**——策略打架说明该标的当前不明朗，不交易是最优解。

---

## 4. 第二步：综合得分排名

聚合后的每个候选标的，计算综合得分：

```
score(symbol) = w1 × strategy_weight       # 组内策略权重（回测产出）
              + w2 × signal_confidence      # 信号强度
              + w3 × backtest_win_rate       # 该策略组的历史胜率
              + w4 × backtest_sharpe_norm     # 历史 Sharpe（归一化）
              - w5 × recent_correlation       # 与已选标的的相关性惩罚（可选）
```

| 因子 | 含义 | 权重建议 |
|------|------|---------|
| `strategy_weight` | 组合中该策略的权重 | 高 |
| `signal_confidence` | 当前信号置信度 | 中 |
| `backtest_win_rate` | 历史胜率 | 中 |
| `backtest_sharpe` | 历史风险调整收益 | 高 |
| `correlation_penalty` | 避免选出高度相关的标的（如全是科技股） | 低（可选） |

> **相关性惩罚**是分散度的补救：Top-5 若全是科技股，等于把鸡蛋放一个篮子。
> 加入惩罚项，鼓励选出跨板块、低相关的 Top-K。

---

## 5. 第三步：Top-K 选取

```
# Ranker 输出 Top-2K 候选（而非直接输出 Top-K）
ranked = sorted(candidates, by=score, desc=True)
top_candidates = ranked[:2*K]   # 输出 2×K 候选，交由 Risk Manager 递补筛选
```

**为什么是 Top-2K 而非 Top-K：**

```
Top-K 候选在 Risk Manager 阶段可能因以下约束被拒：
  - max_sector_exposure_pct=40%（科技股占比超限）
  - max_concurrent_positions=5（已有持仓占位）
  - ATR 仓位法计算结果超过 max_single_position_pct=20%（被截断后资金利用率极低）

如果 Ranker 只输出精确 K 个，被拒后没有替代品 → 实际持仓 < K → 资金利用率低
输出 2K 候选，Risk Manager 逐个尝试，被拒则递补下一个，直到约束用尽或候选耗尽
```

**K=5 的影响**（设计访谈确认）：

```
分散度：等权下每仓 20%，高度集中，单只暴雷砸 20% 净值
        → 这是"少而精高信念"风格，靠 risk_per_trade=1% + 止损控风险
统计量：5/天 × 250 日 = 1250 笔/年，足够验证策略 edge
机会成本：扫 550 只只取 0.9%，精度高但可能漏掉次优信号
资金效率：$100k/5 = $20k 每仓，对零佣金 Alpaca 无压力
```

> K 是配置项 `signal_ranker.top_k`，未来想降波动可调至 10-15。
> 注意：实际下单数还受 Risk Manager 的 `max_concurrent_positions` 约束（递补至约束用尽）。

---

## 6. 模块接口设计

```python
@dataclass
class RankedSignal:
    signal: Signal              # 聚合后的信号
    score: float                # 综合得分
    rank: int                   # 排名（1 = 最强）
    score_breakdown: dict       # 各因子贡献，便于复盘


@dataclass
class RankingReport:
    total_candidates: int       # 聚合前信号数
    after_aggregation: int      # 聚合后候选数
    top_k: list[RankedSignal]   # 最终选出的 Top-K
    dropped_conflicts: int      # 因策略分歧丢弃的标的数


class SignalRanker:
    def __init__(self, top_k: int = 5,
                 score_weights: dict | None = None,
                 conflict_threshold: float = 0.3) -> None: ...

    def rank(self, signals: list[Signal]) -> RankingReport:
        """聚合 → 评分 → 排名 → 取 Top-K。"""

    def _aggregate_by_symbol(self, signals: list[Signal]) -> list[Signal]:
        """同标的多策略聚合（冲突解决）。"""

    def _score(self, signal: Signal) -> tuple[float, dict]:
        """计算综合得分 + 各因子明细。"""
```

---

## 7. 完整流程示例

```python
def rank(signals):
    # 1. 同标的聚合
    aggregated = self._aggregate_by_symbol(signals)
    # → 50 条原始 → 18 条聚合（10 条因分歧丢弃）

    # 2. 评分
    scored = []
    for sig in aggregated:
        score, breakdown = self._score(sig)
        scored.append((sig, score, breakdown))

    # 3. 排名 + Top-K
    scored.sort(key=lambda x: x[1], reverse=True)
    top_k = [
        RankedSignal(signal=s, score=sc, rank=i+1, score_breakdown=bd)
        for i, (s, sc, bd) in enumerate(scored[:self.top_k])
    ]

    return RankingReport(
        total_candidates=len(signals),
        after_aggregation=len(aggregated),
        top_k=top_k,
        dropped_conflicts=len(signals_dropped),
    )
```

---

## 8. 注意点

### 8.1 BUY 和 SELL 候选分开排名
- BUY 信号（开新仓）和 SELL 信号（平已有仓）逻辑不同
- SELL 应优先处理（风控：先平仓再开仓）
- 建议：SELL 信号不受 Top-K 限制（持仓该平就平），只对 BUY 信号取 Top-2K 候选
- **资金结算注意**：Alpaca 中，当日卖出所得资金当日即可通过 `account.buying_power` 字段
  体现（而非 `account.cash`）。实现时查询 `buying_power` 可避免 T+1/T+2 结算时序问题，
  确保 SELL 后资金可立即用于当日 BUY。

### 8.2 已持仓标的的处理
- 若某标的已在持仓中，又收到 BUY 信号 → 不重复开仓（交给 Risk Manager 判断加仓）
- Ranker 应感知当前持仓，避免把已持仓标的算进 Top-K 名额

### 8.3 评分权重本身的过拟合
- `score_weights`（w1~w5）也是参数，过度调优会过拟合
- 建议固定一组合理权重，或纳入 MatrixBacktest 一起验证

### 8.4 相关性惩罚的计算成本
- 计算 Top-K 候选间的两两相关性需额外读取历史 → 有成本
- Phase 5 初期可先不加相关性惩罚，观察 Top-K 是否过度集中再决定

---

## 9. 风险点

| 风险 | 级别 | 缓解措施 |
|------|------|---------|
| Top-K 过度集中（全科技股） | 中 | 相关性惩罚 / 行业上限约束 |
| 评分权重过拟合 | 中 | 固定权重或纳入回测验证 |
| SELL 信号被 Top-K 挤掉 | 中 | SELL 不受 Top-K 限制 |
| 已持仓标的重复计入 | 低 | Ranker 感知持仓状态 |

---

## 10. 目录结构（Phase 5 待实现）

```
mytrader/
└── signal/
    ├── ranker.py               # SignalRanker（Phase 5 新增）
    ├── models.py               # ✅ 扩展：RankedSignal / RankingReport
    ├── pipeline.py             # ✅ 复用：Top-K 后接 Signal Filter
    └── filters/                # ✅ 复用
```

---

## 参考来源

- *Advances in Financial Machine Learning*, Ch.6 — Ensemble Methods (de Prado)
- *Active Portfolio Management* — Grinold & Kahn（信号合成与 IC）
- *Algorithmic Trading*, Ch.2 — Portfolio Construction (Ernest Chan)
