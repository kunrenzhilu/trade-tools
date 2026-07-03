"""PaperDailyMetrics — paper trading 每日结构化 metrics 归档。

迭代 #5 新增（P0-D）。

目的：
    Paper 期间需要每日记录 account/signals/orders/positions/risk/data freshness，
    否则一个月后无法计算 paper Sortino/DD，也无法区分策略问题与系统问题。

设计原则：
    - 缺 broker account API 时不要崩溃，填 0/None 并记录 warning
    - 写文件前创建目录
    - UTF-8、indent=2、ensure_ascii=False
    - 不写入敏感字段（api_key / secret / token / password）
    - 函数式接口：调用方传 broker/tracker/scan_summary，模块不持有状态

JSON 结构（稳定，便于后续分析脚本读取）：
    {
      "date": "YYYY-MM-DD",
      "account": {"equity": 0.0, "cash": 0.0, "buying_power": 0.0},
      "signals": {"raw": 0, "buy_candidates": 0, "sell": 0, "approved": 0},
      "orders": {"submitted": 0, "filled": 0, "pending": 0, "rejected": 0},
      "positions": {"local_count": 0, "broker_count": 0, "diff_count": 0},
      "risk": {"daily_return": 0.0, "rolling_dd": 0.0},
      "data": {"symbols": 0, "latest_bar": "YYYY-MM-DD"}
    }
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from loguru import logger


# ---------------------------------------------------------------------------
# 敏感字段黑名单（永不写入 metrics JSON）
# ---------------------------------------------------------------------------

_SENSITIVE_KEYS = frozenset({
    "api_key", "apikey", "api_secret", "secret", "secret_key",
    "token", "access_token", "refresh_token", "password", "passwd",
    "bearer", "authorization", "auth",
})


def _is_sensitive(key: str) -> bool:
    k = (key or "").lower()
    return k in _SENSITIVE_KEYS or "key" in k and "ticker" not in k and "sortino" not in k and "sharpe" not in k


def _sanitize(obj: Any) -> Any:
    """递归剔除敏感字段（含 api_key/secret/token 等）。"""
    if isinstance(obj, dict):
        clean: dict[str, Any] = {}
        for k, v in obj.items():
            if _is_sensitive(str(k)):
                continue
            clean[k] = _sanitize(v)
        return clean
    if isinstance(obj, (list, tuple)):
        return [_sanitize(v) for v in obj]
    return obj


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------

@dataclass
class PaperDailyMetrics:
    """Paper 每日 metrics（迭代 #5）。

    结构稳定，可序列化为 JSON 归档，便于后续计算 paper Sortino/DD。
    """

    date: str
    account: dict[str, Any] = field(default_factory=dict)
    signals: dict[str, int] = field(default_factory=dict)
    orders: dict[str, int] = field(default_factory=dict)
    positions: dict[str, int] = field(default_factory=dict)
    risk: dict[str, float] = field(default_factory=dict)
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _sanitize(asdict(self))


# ---------------------------------------------------------------------------
# 默认输出目录
# ---------------------------------------------------------------------------

DEFAULT_OUTPUT_DIR: Path = Path("reports/paper/daily")


# ---------------------------------------------------------------------------
# 公共接口
# ---------------------------------------------------------------------------

def collect_paper_daily_metrics(
    *,
    broker: Any,
    tracker: Any,
    scan_summary: Any | None = None,
    data_status: dict[str, Any] | None = None,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    today: date | None = None,
) -> Path:
    """采集并写出 paper daily metrics JSON，返回文件路径。

    Args:
        broker:        AlpacaBroker / PaperBroker 等（缺 API 时填 0/None，不崩溃）
        tracker:       PortfolioTracker
        scan_summary:  ScanSummary（可选；None 时 signals 字段填 0）
        data_status:   数据新鲜度 dict（可选；含 symbols / latest_bar）
        output_dir:    输出目录（默认 reports/paper/daily）
        today:         指定日期（默认 UTC today）

    Returns:
        写出的 JSON 文件路径
    """
    if today is None:
        today = datetime.now(timezone.utc).date()

    metrics = PaperDailyMetrics(date=today.isoformat())

    # ── account ──
    metrics.account = _collect_account(broker, tracker)

    # ── signals ──
    metrics.signals = _collect_signals(scan_summary)

    # ── orders ──
    metrics.orders = _collect_orders(broker)

    # ── positions ──
    metrics.positions = _collect_positions(broker, tracker)

    # ── risk ──
    metrics.risk = _collect_risk(tracker)

    # ── data ──
    metrics.data = _collect_data_status(data_status)

    # ── 写文件 ──
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{today.isoformat()}.json"

    payload = metrics.to_dict()
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, default=str)

    logger.info(
        f"[PaperMetrics] wrote daily metrics: {out_path} "
        f"(orders={metrics.orders}, positions={metrics.positions})"
    )
    return out_path


# ---------------------------------------------------------------------------
# 内部采集器
# ---------------------------------------------------------------------------

def _collect_account(broker: Any, tracker: Any = None) -> dict[str, Any]:
    """读取 broker account 信息。缺 API 时返回零值。

    优先用 broker.health_check()（AlpacaBroker 已实现），
    其次尝试 broker.get_account()，
    最后用 tracker.portfolio.cash 兜底。
    """
    account: dict[str, Any] = {
        "equity": 0.0,
        "cash": 0.0,
        "buying_power": 0.0,
    }
    try:
        if hasattr(broker, "health_check"):
            hc = broker.health_check()
            if isinstance(hc, dict) and hc.get("status") == "connected":
                # health_check 返回 cash/buying_power；equity 字段不存在时用 cash 兜底
                cash = _safe_float(hc.get("cash", 0.0))
                account["cash"] = cash
                account["equity"] = _safe_float(hc.get("equity", cash))
                account["buying_power"] = _safe_float(hc.get("buying_power", 0.0))
                return account
        if hasattr(broker, "get_account"):
            acct = broker.get_account()
            account["equity"] = _safe_float(getattr(acct, "equity", 0.0))
            account["cash"] = _safe_float(getattr(acct, "cash", 0.0))
            account["buying_power"] = _safe_float(getattr(acct, "buying_power", 0.0))
            return account
    except Exception as exc:
        logger.debug(f"[PaperMetrics] account collection failed: {exc}")
    # 兜底：使用 tracker.portfolio.cash
    if tracker is not None:
        try:
            portfolio = getattr(tracker, "portfolio", None)
            if portfolio is not None:
                cash = _safe_float(getattr(portfolio, "cash", 0.0))
                account["cash"] = cash
                if account["equity"] == 0.0:
                    account["equity"] = cash
        except Exception as exc:
            logger.debug(f"[PaperMetrics] tracker fallback failed: {exc}")
    return account


def _collect_signals(scan_summary: Any | None) -> dict[str, int]:
    """从 ScanSummary 提取信号统计。"""
    result = {"raw": 0, "buy_candidates": 0, "sell": 0, "approved": 0}
    if scan_summary is None:
        return result
    try:
        # ScanSummary 提供 buy_count / sell_count / order_count / error_count
        result["raw"] = len(getattr(scan_summary, "results", []) or [])
        result["buy_candidates"] = int(getattr(scan_summary, "buy_count", 0))
        result["sell"] = int(getattr(scan_summary, "sell_count", 0))
        result["approved"] = int(getattr(scan_summary, "order_count", 0))
    except Exception as exc:
        logger.debug(f"[PaperMetrics] signals collection failed: {exc}")
    return result


def _collect_orders(broker: Any) -> dict[str, int]:
    """从 broker.order_history 统计订单状态。"""
    result = {"submitted": 0, "filled": 0, "pending": 0, "rejected": 0}
    try:
        history = getattr(broker, "order_history", []) or []
    except Exception as exc:
        logger.debug(f"[PaperMetrics] orders collection failed: {exc}")
        return result

    # 延迟导入避免循环依赖
    try:
        from mytrader.execution.models import OrderStatus as _OS
    except Exception:  # pragma: no cover - 仅在 import 失败时降级
        _OS = None  # type: ignore[assignment]

    result["submitted"] = len(history)
    for o in history:
        status = getattr(o, "status", None)
        if _OS is not None and status == _OS.FILLED:
            result["filled"] += 1
        elif _OS is not None and status == _OS.PENDING:
            result["pending"] += 1
        elif _OS is not None and status == _OS.REJECTED:
            result["rejected"] += 1
        else:
            # 字符串兜底
            s = str(status or "").upper()
            if s == "FILLED":
                result["filled"] += 1
            elif s == "PENDING":
                result["pending"] += 1
            elif s == "REJECTED":
                result["rejected"] += 1
    return result


def _collect_positions(broker: Any, tracker: Any) -> dict[str, int]:
    """统计本地 vs broker 持仓数量与 diff。"""
    result = {"local_count": 0, "broker_count": 0, "diff_count": 0}

    # local
    try:
        open_positions = getattr(tracker, "open_positions", {}) or {}
        result["local_count"] = len(open_positions)
    except Exception as exc:
        logger.debug(f"[PaperMetrics] local positions failed: {exc}")

    # broker
    try:
        if hasattr(broker, "get_positions"):
            broker_positions = broker.get_positions() or []
            result["broker_count"] = len(broker_positions)
            # 简单 diff：取本地与 broker symbol 集合的对称差大小
            local_set = set((getattr(tracker, "open_positions", {}) or {}).keys())
            broker_set = {p.get("symbol") for p in broker_positions if p.get("symbol")}
            result["diff_count"] = len(local_set ^ broker_set)
    except Exception as exc:
        logger.debug(f"[PaperMetrics] broker positions failed: {exc}")

    return result


def _collect_risk(tracker: Any) -> dict[str, float]:
    """从 tracker 提取 risk 指标（daily_return / rolling_dd）。

    PortfolioTracker 当前可能不直接维护这两个指标；本次 best-effort 填 0.0，
    后续可由 tracker 扩展提供。
    """
    result = {"daily_return": 0.0, "rolling_dd": 0.0}
    try:
        portfolio = getattr(tracker, "portfolio", None)
        if portfolio is not None:
            # 若 portfolio 暴露 daily_pnl_pct / max_drawdown，使用之
            result["daily_return"] = _safe_float(
                getattr(portfolio, "daily_pnl_pct", 0.0)
            )
            result["rolling_dd"] = _safe_float(
                getattr(portfolio, "max_drawdown", 0.0)
            )
    except Exception as exc:
        logger.debug(f"[PaperMetrics] risk collection failed: {exc}")
    return result


def _collect_data_status(data_status: dict[str, Any] | None) -> dict[str, Any]:
    """数据新鲜度。"""
    if not data_status:
        return {"symbols": 0, "latest_bar": None}
    return {
        "symbols": int(data_status.get("symbols", 0) or 0),
        "latest_bar": data_status.get("latest_bar"),
    }


def _safe_float(value: Any, default: float = 0.0) -> float:
    """安全转 float：None / NaN / Inf / 非数值 → default。"""
    if value is None:
        return default
    try:
        f = float(value)
    except (ValueError, TypeError):
        return default
    if f != f:  # NaN
        return default
    if f in (float("inf"), float("-inf")):
        return default
    return f
