"""诊断脚本：DASH/HON 为什么被 SignalFilter 拦截？

直接复现 scan_orchestrator 的 pipeline 构建和数据加载流程，
对 DASH/HON 跑一次过滤器，打印每个过滤器的拒绝原因。

运行（在服务器上）：
    cd /root/trade-tools/mytrader
    /root/miniforge3/envs/py312trade/bin/python diag_filter.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# 确保能 import mytrader
sys.path.insert(0, str(Path(__file__).parent))

from datetime import date, timedelta

from mytrader.data.store.market_data_store import MarketDataStore
from mytrader.infra.config import load_config
from mytrader.signal.pipeline import SignalPipeline
from mytrader.strategy.base import Signal, SignalDirection


SYMBOLS = ["DASH", "HON"]


def make_signal(symbol: str, df) -> Signal:
    """用 df 最后一根 bar 作为信号时间戳，构造 BUY 信号。"""
    ts = df.index[-1]
    return Signal(
        symbol=symbol,
        direction=SignalDirection.BUY,
        timestamp=ts,
        confidence=1.0,
        strategy_name="diag",
        price_hint=float(df["close"].iloc[-1]),
    )


def main() -> None:
    cfg = load_config()
    print(f"signal_filter config:")
    fcfg = cfg.signal_filter
    print(f"  volume_filter_enabled={fcfg.volume_filter_enabled} threshold={fcfg.volume_filter_threshold} window={fcfg.volume_filter_window}")
    print(f"  atr_filter_enabled={fcfg.atr_filter_enabled} period={fcfg.atr_filter_period} max_atr_pct={fcfg.atr_filter_max_atr_pct}")
    print(f"  sentiment_filter_enabled={fcfg.sentiment_filter_enabled}")
    print(f"  time_window_filter_enabled={fcfg.time_window_filter_enabled}")
    print(f"  cooldown_filter_enabled={fcfg.cooldown_filter_enabled} min_bars={fcfg.cooldown_filter_min_bars}")
    print()

    pipeline = SignalPipeline.from_config(fcfg)
    print(f"pipeline filters (in order): {[f.name for f in pipeline._filters]}")
    print()

    # 与 container.py:228 一致的构造方式
    store_db_url = cfg.market_data_store.db_url
    if store_db_url.startswith("sqlite:///"):
        store_db = store_db_url[len("sqlite:///"):]
    else:
        store_db = store_db_url
    db_path = store_db if store_db and store_db != "default" else None
    store = MarketDataStore(db_path=db_path)

    for sym in SYMBOLS:
        print(f"===== {sym} =====")
        end = date.today()
        start = end - timedelta(days=60)
        df = store.get_bars(sym, start=start, end=end, timeframe="1d")
        if df is None or df.empty:
            print(f"  NO DATA for {sym}")
            continue

        print(f"  bars: {len(df)}")
        print(f"  latest 5 bars:")
        print(df.tail(5).to_string().replace("\n", "\n  "))
        print()

        # 构造一个 BUY 信号
        sig = make_signal(sym, df)
        print(f"  signal: {sig.direction.value} @ {sig.timestamp} close={df['close'].iloc[-1]:.2f}")
        print()

        # 逐个跑过滤器，看每一步的结果
        current = sig
        for f in pipeline._filters:
            fs = f.apply(current, df)
            if fs.passed:
                print(f"  [{f.name}] PASS")
            else:
                print(f"  [{f.name}] REJECTED — rejected_by={fs.rejected_by}, reason={fs.rejection_reason}")
                break

        # 再跑第二次，模拟 CooldownFilter 的跨扫描状态
        print()
        print(f"  --- 2nd call (simulating next scan) ---")
        fs2 = f.apply(current, df)  # type: ignore[name-defined]
        if fs2.passed:
            print(f"  [{f.name}] PASS")
        else:
            print(f"  [{f.name}] REJECTED — {fs2.rejection_reason}")
        print()

        # 关键诊断：如果是 CooldownFilter，打印它的状态
        for f in pipeline._filters:
            if hasattr(f, "_last_pass"):
                print(f"  CooldownFilter state: {dict(f._last_pass)}")
        print()


if __name__ == "__main__":
    main()
