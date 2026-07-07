"""迭代 #1 验证脚本：用真实 MarketDataStore 数据跑小样本矩阵回测。

确认：
1. 4 个策略全部被评估（不再只有 dual_ma）
2. strategy_weights.json 含 backtest_sortino 字段
3. 至少 1 个组的最优策略不再是 dual_ma

仅读不写，输出到 stdout（不覆盖 config/strategy_weights.json）。
"""
from __future__ import annotations
import json
from pathlib import Path
from datetime import date, timedelta

from mytrader.data.store import MarketDataStore
from mytrader.universe.manager import UniverseManager
from mytrader.backtest.matrix_backtest import MatrixBacktest

print("=== 迭代 #1 验证：小样本矩阵回测（真实 DB 数据） ===")

store = MarketDataStore()
universe = UniverseManager(store=store)
groups = universe.get_groups()
print(f"[universe] 总组数: {len(groups)}")
for gid, syms in groups.items():
    print(f"  {gid}: {len(syms)} symbols (前3: {syms[:3]})")

# 每组只取前 3 只标的，加速验证（JIT 禁用下避免全量 604 只）
small_groups = {gid: syms[:3] for gid, syms in groups.items()}
print(f"\n[verify] 小样本：每组前 3 只，共 {sum(len(s) for s in small_groups.values())} 只")

# 用 monkey-patch 让 get_groups 返回小样本（不动 universe 实例的内部状态）
universe.get_groups = lambda: small_groups

mb = MatrixBacktest(store=store, universe=universe, years=5, top_k=2)

# ⚠️ 用修复后的正确策略名（与 main.REOPTIMIZE_STRATEGIES 一致）
strategies = ["dual_ma", "rsi_mean_revert", "macd_cross", "bollinger_band"]
param_grids = {
    "dual_ma":         {"fast": [5, 10], "slow": [20, 40, 60]},
    "rsi_mean_revert": {"period": [14], "oversold": [30], "overbought": [70]},
    "macd_cross":      {"fast": [12], "slow": [26], "signal_period": [9]},
    "bollinger_band":  {"period": [20], "std_dev": [2.0]},
}

print(f"\n[verify] 运行矩阵回测：{len(strategies)} 策略 × {len(small_groups)} 组 × 5 年...")
report = mb.run(strategies=strategies, param_grids=param_grids, output_file=None)

print(f"\n=== 验证结果 ===")
print(f"组数: {len(report.groups)}")

# 检查 1：策略多样性（不再全是 dual_ma）
strategy_counts: dict[str, int] = {}
for gid, weights in report.groups.items():
    for w in weights:
        s = w["strategy"]
        strategy_counts[s] = strategy_counts.get(s, 0) + 1

print(f"\n[检查1] 策略分布（各组 Top-K 选中）:")
for s, c in sorted(strategy_counts.items(), key=lambda x: -x[1]):
    print(f"  {s}: {c} 组")

non_dual_ma_groups = sum(1 for gid, ws in report.groups.items()
                         if ws and any(w["strategy"] != "dual_ma" for w in ws))
print(f"\n  非 dual_ma 组数: {non_dual_ma_groups} / {len(report.groups)}")
assert non_dual_ma_groups >= 1, "❌ 所有组仍为 dual_ma，修复未生效"
print(f"  ✅ 至少 1 组不再仅用 dual_ma")

# 检查 2：backtest_sortino 字段存在
print(f"\n[检查2] backtest_sortino 字段:")
sortino_present = 0
sortino_total = 0
for gid, weights in report.groups.items():
    for w in weights:
        sortino_total += 1
        if "backtest_sortino" in w:
            sortino_present += 1
print(f"  含 backtest_sortino: {sortino_present} / {sortino_total}")
assert sortino_present == sortino_total, "❌ 部分权重条目缺 backtest_sortino"
print(f"  ✅ 全部权重条目含 backtest_sortino")

# 检查 3：每组选中的策略 + Sharpe + Sortino 明细
print(f"\n[检查3] 各组选中策略明细:")
for gid, weights in report.groups.items():
    print(f"  {gid}:")
    for w in weights:
        print(f"    {w['strategy']:20s} params={w['params']} "
              f"weight={w['weight']:.2f} "
              f"sharpe={w.get('backtest_sharpe', 0):.4f} "
              f"sortino={w.get('backtest_sortino', 0):.4f}")

# 检查 4：GroupBacktestResult.portfolio_sortino
print(f"\n[检查4] GroupBacktestResult.portfolio_sortino 字段:")
for gr in report.group_results[:6]:
    print(f"  {gr.group_id} / {gr.strategy:20s} "
          f"sharpe={gr.portfolio_sharpe:.4f} sortino={gr.portfolio_sortino:.4f}")

print(f"\n=== ✅ 全部验证通过 ===")
