"""SQLAlchemy 持久化层 — 成交记录 + 持仓快照（SQLite）。

使用 SQLAlchemy 2.x Core API（非 ORM），轻量无 Session 依赖。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    insert,
    select,
)
from sqlalchemy.engine import Engine

from mytrader.portfolio.models import Portfolio, Position, TradeRecord
from mytrader.strategy.base import SignalDirection


# ---------------------------------------------------------------------------
# 表定义
# ---------------------------------------------------------------------------

metadata = MetaData()

trades_table = Table(
    "trades",
    metadata,
    Column("trade_id", String(64), primary_key=True),
    Column("symbol", String(16), nullable=False),
    Column("direction", String(8), nullable=False),
    Column("quantity", Integer, nullable=False),
    Column("fill_price", Float, nullable=False),
    Column("commission", Float, nullable=False),
    Column("filled_at", DateTime, nullable=False),
    Column("realized_pnl", Float, default=0.0),
    Column("stop_loss_price", Float, default=0.0),
    Column("take_profit_price", Float, nullable=True),
    Column("meta_json", Text, default="{}"),
)

snapshots_table = Table(
    "portfolio_snapshots",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("snapshot_at", DateTime, nullable=False),
    Column("cash", Float, nullable=False),
    Column("total_equity", Float, nullable=False),
    Column("realized_pnl", Float, nullable=False),
    Column("open_positions", Integer, nullable=False),
    Column("positions_json", Text, default="{}"),
)


# ---------------------------------------------------------------------------
# 持久化类
# ---------------------------------------------------------------------------

class PortfolioPersistence:
    """Portfolio 持久化，操作 SQLite via SQLAlchemy Core。

    Args:
        db_url: SQLAlchemy 连接字符串，默认内存 SQLite。
                生产环境用 "sqlite:///~/.mytrader/portfolio.db"
    """

    def __init__(self, db_url: str = "sqlite:///:memory:") -> None:
        self._engine: Engine = create_engine(db_url)
        metadata.create_all(self._engine)

    @classmethod
    def from_path(cls, db_path: str | Path) -> "PortfolioPersistence":
        """从文件路径创建（自动展开 ~）。"""
        path = Path(db_path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        return cls(f"sqlite:///{path}")

    def save_trade(self, trade: TradeRecord) -> None:
        """插入成交记录（ignore 已存在的 trade_id）。"""
        with self._engine.connect() as conn:
            stmt = insert(trades_table).prefix_with("OR IGNORE").values(
                trade_id=trade.trade_id,
                symbol=trade.symbol,
                direction=trade.direction.value,
                quantity=trade.quantity,
                fill_price=trade.fill_price,
                commission=trade.commission,
                filled_at=trade.filled_at,
                realized_pnl=trade.realized_pnl,
                stop_loss_price=trade.stop_loss_price,
                take_profit_price=trade.take_profit_price,
                meta_json=json.dumps(trade.meta),
            )
            conn.execute(stmt)
            conn.commit()

    def save_snapshot(
        self,
        portfolio: Portfolio,
        total_equity: float,
        snapshot_at: datetime | None = None,
    ) -> None:
        """保存持仓快照。"""
        if snapshot_at is None:
            snapshot_at = datetime.utcnow()

        positions_data = {
            s: {
                "quantity": p.quantity,
                "avg_cost": p.avg_cost,
                "stop_loss_price": p.stop_loss_price,
            }
            for s, p in portfolio.open_positions.items()
        }

        with self._engine.connect() as conn:
            conn.execute(
                insert(snapshots_table).values(
                    snapshot_at=snapshot_at,
                    cash=portfolio.cash,
                    total_equity=total_equity,
                    realized_pnl=portfolio.realized_pnl,
                    open_positions=len(portfolio.open_positions),
                    positions_json=json.dumps(positions_data),
                )
            )
            conn.commit()

    def load_trades(self, symbol: str | None = None) -> list[dict]:
        """读取历史成交记录。"""
        with self._engine.connect() as conn:
            stmt = select(trades_table)
            if symbol:
                stmt = stmt.where(trades_table.c.symbol == symbol)
            rows = conn.execute(stmt).fetchall()
            return [dict(r._mapping) for r in rows]

    def load_latest_snapshot(self) -> dict | None:
        """读取最新持仓快照。"""
        with self._engine.connect() as conn:
            stmt = (
                select(snapshots_table)
                .order_by(snapshots_table.c.snapshot_at.desc())
                .limit(1)
            )
            row = conn.execute(stmt).fetchone()
            return dict(row._mapping) if row else None
