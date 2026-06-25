"""MyTrader Streamlit Dashboard — Phase 4 可视化面板。

启动方式：
    cd mytrader
    /Users/rickouyang/miniforge3/envs/py312trade/bin/streamlit run \
        mytrader/monitor/dashboard/app.py

功能模块：
    - 概览（总资产/现金/持仓数/已实现盈亏）
    - 持仓详情（标的/数量/成本/止损/止盈/未实现盈亏）
    - 交易历史（成交记录表格 + 盈亏柱状图）
    - 权益曲线（折线图）
    - 日志查看（最新 100 行）

数据来源：
    - 读取 SQLite 数据库（默认 mytrader/mytrader.db）
    - 可通过侧栏切换数据库路径
    - 每 30 秒自动刷新
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── 确保 mytrader 包可 import ────────────────────────────────────────────────
_ROOT = Path(__file__).parents[4]  # mytrader/ 项目根
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# ---------------------------------------------------------------------------
# 页面配置（必须第一个 st 调用）
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="MyTrader Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------


@st.cache_resource(ttl=30)
def _load_db(db_path: str):
    """加载持久化数据（缓存 30 秒刷新）。"""
    try:
        from mytrader.portfolio.persistence import PortfolioPersistence
        return PortfolioPersistence(f"sqlite:///{db_path}")
    except Exception:
        return None


def _load_trades(db_path: str) -> pd.DataFrame:
    """从 SQLite 读取交易记录，返回 DataFrame。"""
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        df = pd.read_sql(
            "SELECT * FROM trades ORDER BY filled_at DESC",
            conn,
            parse_dates=["filled_at"],
        )
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()


def _load_snapshots(db_path: str) -> pd.DataFrame:
    """从 SQLite 读取权益快照，返回 DataFrame。"""
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        df = pd.read_sql(
            "SELECT * FROM equity_snapshots ORDER BY snapshot_at ASC",
            conn,
            parse_dates=["snapshot_at"],
        )
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()


def _load_logs(log_dir: str, lines: int = 100) -> list[str]:
    """读取最新日志文件末尾 N 行。"""
    try:
        log_path = Path(log_dir)
        log_files = sorted(log_path.glob("mytrader_*.log"), reverse=True)
        if not log_files:
            log_files = sorted(log_path.glob("*.log"), reverse=True)
        if not log_files:
            return ["No log files found"]
        with open(log_files[0], "r", encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()
        return [l.rstrip() for l in all_lines[-lines:]]
    except Exception as exc:
        return [f"Error reading logs: {exc}"]


# ---------------------------------------------------------------------------
# 侧栏配置
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("⚙️ 设置")

    db_path = st.text_input(
        "数据库路径",
        value="mytrader.db",
        help="SQLite 数据库文件路径（相对于 mytrader/ 目录）",
    )
    log_dir = st.text_input(
        "日志目录",
        value="logs",
        help="日志文件目录",
    )
    auto_refresh = st.checkbox("自动刷新（30s）", value=True)
    if auto_refresh:
        import time
        st.caption(f"最后刷新：{datetime.now().strftime('%H:%M:%S')}")
        time.sleep(0)  # 触发重渲染（结合 st.rerun）

    if st.button("🔄 立即刷新"):
        st.cache_resource.clear()
        st.rerun()

    st.divider()
    st.caption("MyTrader Phase 4 Dashboard")

# ---------------------------------------------------------------------------
# 主内容区：Tab 布局
# ---------------------------------------------------------------------------

tab_overview, tab_positions, tab_trades, tab_equity, tab_logs = st.tabs(
    ["📊 概览", "💼 持仓", "📋 交易历史", "📈 权益曲线", "📜 日志"]
)

# ── Tab 1: 概览 ─────────────────────────────────────────────────────────────

with tab_overview:
    st.header("📊 账户概览")

    trades_df = _load_trades(db_path)
    snapshots_df = _load_snapshots(db_path)

    if trades_df.empty and snapshots_df.empty:
        st.info("暂无数据。请确认数据库路径正确，或等待第一次扫描完成。")
    else:
        # 指标卡
        col1, col2, col3, col4 = st.columns(4)

        # 最新权益快照
        if not snapshots_df.empty:
            latest = snapshots_df.iloc[-1]
            total_equity = latest.get("total_equity", 0.0)
            cash = latest.get("cash", 0.0)
            open_pos = int(latest.get("open_positions", 0))
        else:
            total_equity = cash = 0.0
            open_pos = 0

        realized_pnl = float(
            trades_df["realized_pnl"].sum() if "realized_pnl" in trades_df.columns else 0.0
        )
        pnl_color = "normal" if realized_pnl >= 0 else "inverse"

        col1.metric("总资产", f"${total_equity:,.2f}")
        col2.metric("可用现金", f"${cash:,.2f}")
        col3.metric("持仓标的数", open_pos)
        col4.metric(
            "已实现盈亏",
            f"${realized_pnl:,.2f}",
            delta=f"{realized_pnl:+.2f}",
        )

        st.divider()

        # 胜率 & 交易统计
        if not trades_df.empty and "realized_pnl" in trades_df.columns:
            sell_trades = trades_df[trades_df["direction"] == "SELL"]
            if not sell_trades.empty:
                wins = (sell_trades["realized_pnl"] > 0).sum()
                total = len(sell_trades)
                win_rate = wins / total * 100

                c1, c2, c3 = st.columns(3)
                c1.metric("卖出笔数", total)
                c2.metric("盈利笔数", wins)
                c3.metric("胜率", f"{win_rate:.1f}%")


# ── Tab 2: 持仓 ─────────────────────────────────────────────────────────────

with tab_positions:
    st.header("💼 当前持仓")

    try:
        from mytrader.infra.config import load_config
        from mytrader.infra.container import Container

        config = load_config()
        components = Container.build(config, db_url=f"sqlite:///{db_path}")
        open_positions = components.tracker.open_positions

        if not open_positions:
            st.info("当前无持仓")
        else:
            rows = []
            for symbol, pos in open_positions.items():
                rows.append({
                    "标的": symbol,
                    "持仓股数": pos.quantity,
                    "平均成本": f"${pos.avg_cost:.2f}",
                    "止损价": f"${pos.stop_loss_price:.2f}" if pos.stop_loss_price else "—",
                    "止盈价": f"${pos.take_profit_price:.2f}" if pos.take_profit_price else "—",
                    "建仓时间": pos.opened_at.strftime("%Y-%m-%d %H:%M") if pos.opened_at else "—",
                    "市值（成本）": f"${pos.quantity * pos.avg_cost:,.2f}",
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True)
    except Exception as exc:
        st.warning(f"加载持仓失败：{exc}")
        st.caption("请确认 mytrader.db 数据库路径正确")


# ── Tab 3: 交易历史 ──────────────────────────────────────────────────────────

with tab_trades:
    st.header("📋 交易历史")

    trades_df = _load_trades(db_path)
    if trades_df.empty:
        st.info("暂无成交记录")
    else:
        # 展示列
        display_cols = [
            c for c in [
                "filled_at", "symbol", "direction",
                "quantity", "fill_price", "commission",
                "realized_pnl", "stop_loss_price", "take_profit_price",
            ]
            if c in trades_df.columns
        ]
        st.dataframe(trades_df[display_cols], use_container_width=True)

        # 盈亏柱状图
        sell_df = trades_df[trades_df["direction"] == "SELL"].copy() if "direction" in trades_df.columns else pd.DataFrame()
        if not sell_df.empty and "realized_pnl" in sell_df.columns:
            st.subheader("已实现盈亏（卖出记录）")
            sell_df["color"] = sell_df["realized_pnl"].apply(
                lambda x: "盈利" if x >= 0 else "亏损"
            )
            fig = px.bar(
                sell_df.reset_index(),
                x=sell_df.reset_index().index,
                y="realized_pnl",
                color="color",
                color_discrete_map={"盈利": "#26a69a", "亏损": "#ef5350"},
                labels={"x": "交易序号", "realized_pnl": "盈亏 (USD)"},
                title="逐笔已实现盈亏",
            )
            fig.update_layout(showlegend=True, height=350)
            st.plotly_chart(fig, use_container_width=True)


# ── Tab 4: 权益曲线 ──────────────────────────────────────────────────────────

with tab_equity:
    st.header("📈 权益曲线")

    snapshots_df = _load_snapshots(db_path)
    if snapshots_df.empty:
        st.info("暂无权益快照数据")
    else:
        if "snapshot_at" in snapshots_df.columns and "total_equity" in snapshots_df.columns:
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=snapshots_df["snapshot_at"],
                    y=snapshots_df["total_equity"],
                    mode="lines+markers",
                    name="总资产",
                    line=dict(color="#2196F3", width=2),
                )
            )
            if "cash" in snapshots_df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=snapshots_df["snapshot_at"],
                        y=snapshots_df["cash"],
                        mode="lines",
                        name="现金",
                        line=dict(color="#FF9800", width=1, dash="dot"),
                    )
                )
            fig.update_layout(
                title="账户权益曲线",
                xaxis_title="时间",
                yaxis_title="金额 (USD)",
                height=450,
                hovermode="x unified",
            )
            st.plotly_chart(fig, use_container_width=True)

            # 回撤统计
            equity = snapshots_df["total_equity"]
            rolling_max = equity.cummax()
            drawdown = (equity - rolling_max) / rolling_max * 100
            max_dd = drawdown.min()

            c1, c2 = st.columns(2)
            c1.metric("最大回撤", f"{max_dd:.2f}%")
            initial = float(equity.iloc[0])
            final = float(equity.iloc[-1])
            total_return = (final - initial) / initial * 100 if initial > 0 else 0.0
            c2.metric("总回报", f"{total_return:+.2f}%")


# ── Tab 5: 日志 ──────────────────────────────────────────────────────────────

with tab_logs:
    st.header("📜 系统日志")

    log_lines_count = st.slider("显示行数", 20, 200, 100, step=20)
    log_lines = _load_logs(log_dir, lines=log_lines_count)

    log_text = "\n".join(log_lines)
    st.text_area(
        "最新日志",
        value=log_text,
        height=500,
        label_visibility="collapsed",
    )

    # 错误/警告统计
    errors = [l for l in log_lines if "ERROR" in l or "CRITICAL" in l]
    warns = [l for l in log_lines if "WARNING" in l or "WARN" in l]
    if errors:
        st.error(f"发现 {len(errors)} 条错误日志")
        for e in errors[-5:]:
            st.code(e, language="")
    elif warns:
        st.warning(f"发现 {len(warns)} 条警告日志")

# ---------------------------------------------------------------------------
# 自动刷新（每 30 秒）
# ---------------------------------------------------------------------------

if auto_refresh:
    import time
    time.sleep(30)
    st.rerun()
