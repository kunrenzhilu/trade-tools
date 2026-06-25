"""成分股数据获取 — Wikipedia S&P 500 + Nasdaq 100 官方列表。

提供：
    fetch_sp500()     → list[dict] — 含 symbol, sector
    fetch_nasdaq100() → list[dict] — 含 symbol
    load_from_csv(path) → list[dict] — 本地 CSV 兜底

降级策略：网络失败时自动读取本地 universe.csv 兜底。
"""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Any

import pandas as pd
from loguru import logger

# Wikipedia 需要浏览器级的 User-Agent，否则返回 403
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    )
}


def _fetch_tables(url: str) -> list[pd.DataFrame]:
    """用 requests 带 User-Agent 下载 HTML 后交给 pd.read_html 解析。

    注意：pd.read_html 默认用 urllib，不带 UA 会被 Wikipedia 403。
    """
    import requests
    resp = requests.get(url, headers=_HEADERS, timeout=15)
    resp.raise_for_status()
    return pd.read_html(io.StringIO(resp.text), header=0)


def fetch_sp500() -> list[dict[str, str]]:
    """从 Wikipedia 抓取 S&P 500 成分股。"""
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    try:
        tables = _fetch_tables(url)
        df = tables[0]
        sym_col = next(
            (c for c in df.columns if "ticker" in c.lower() or "symbol" in c.lower()),
            df.columns[0],
        )
        sec_col = next(
            (c for c in df.columns if "sector" in c.lower() or "industry" in c.lower()),
            None,
        )
        result = []
        for _, row in df.iterrows():
            sym = str(row[sym_col]).strip().upper().replace(".", "-")
            if not sym or sym in ("NAN", "NONE"):
                continue
            sector = str(row[sec_col]).strip() if sec_col else "Unknown"
            result.append({"symbol": sym, "sector": sector, "index": "SP500"})
        logger.info(f"[constituents] S&P 500: {len(result)} symbols from Wikipedia")
        return result
    except Exception as e:
        logger.warning(f"[constituents] fetch_sp500 failed ({type(e).__name__}): {e}")
        return []


def fetch_nasdaq100() -> list[dict[str, str]]:
    """从 Wikipedia 抓取 Nasdaq 100 成分股。"""
    url = "https://en.wikipedia.org/wiki/Nasdaq-100"
    try:
        tables = _fetch_tables(url)
        df = None
        for t in tables:
            cols_lower = [c.lower() for c in t.columns]
            if any("ticker" in c or "symbol" in c for c in cols_lower):
                df = t
                break
        if df is None:
            raise ValueError("Cannot find Nasdaq 100 table in Wikipedia page")

        sym_col = next(
            (c for c in df.columns if "ticker" in c.lower() or "symbol" in c.lower()),
            df.columns[0],
        )
        sec_col = next(
            (c for c in df.columns if "sector" in c.lower() or "industry" in c.lower()),
            None,
        )
        result = []
        for _, row in df.iterrows():
            sym = str(row[sym_col]).strip().upper().replace(".", "-")
            if not sym or sym == "NAN":
                continue
            sector = str(row[sec_col]).strip() if sec_col else "Unknown"
            result.append({"symbol": sym, "sector": sector, "index": "NASDAQ100"})
        logger.info(f"[constituents] Nasdaq 100: {len(result)} symbols from Wikipedia")
        return result
    except Exception as e:
        logger.warning(f"[constituents] fetch_nasdaq100 failed: {e}")
        return []


def load_from_csv(path: str | Path) -> list[dict[str, str]]:
    """从本地 CSV 加载成分股（兜底方案）。

    CSV 格式：symbol,sector,index（header 必须包含 symbol 列）
    """
    path = Path(path)
    if not path.exists():
        return []
    result = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sym = row.get("symbol", "").strip().upper()
            if sym:
                result.append(
                    {
                        "symbol": sym,
                        "sector": row.get("sector", "Unknown").strip(),
                        "index": row.get("index", "SP500").strip(),
                    }
                )
    logger.info(f"[constituents] loaded {len(result)} symbols from {path}")
    return result


def save_to_csv(
    records: list[dict[str, str]],
    path: str | Path,
) -> None:
    """将成分股列表保存为 CSV（缓存 + 兜底更新）。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["symbol", "sector", "index"])
        writer.writeheader()
        writer.writerows(records)
    logger.info(f"[constituents] saved {len(records)} symbols to {path}")
