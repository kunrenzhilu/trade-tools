"""OHLCV 数据质量校验。

校验结果作为 DataQualityReport 返回，不直接抛异常，
由调用方决定是否继续使用该数据。
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd
from loguru import logger


@dataclass
class DataQualityReport:
    symbol: str
    timeframe: str
    total_rows: int
    missing_rows: int = 0          # 相比预期交易日少了多少行
    suspect_bars: int = 0          # 价格异常 bar 数量
    low_liquidity_bars: int = 0    # 成交量为 0 的 bar 数
    issues: list[str] = field(default_factory=list)

    @property
    def is_ok(self) -> bool:
        """True 表示数据质量可接受。"""
        return len(self.issues) == 0

    def summary(self) -> str:
        status = "OK" if self.is_ok else "WARN"
        return (
            f"[{status}] {self.symbol}/{self.timeframe}: "
            f"{self.total_rows} rows, "
            f"suspect={self.suspect_bars}, "
            f"low_liquidity={self.low_liquidity_bars}"
            + (f", issues={self.issues}" if self.issues else "")
        )


def validate_ohlcv(
    df: pd.DataFrame,
    symbol: str = "",
    timeframe: str = "1d",
    min_rows: int = 10,
) -> DataQualityReport:
    """对清洗后的 OHLCV DataFrame 做质量验证。

    Args:
        df:        清洗后的 DataFrame
        symbol:    股票代码
        timeframe: K 线周期
        min_rows:  最少行数要求

    Returns:
        DataQualityReport
    """
    report = DataQualityReport(
        symbol=symbol,
        timeframe=timeframe,
        total_rows=len(df) if df is not None else 0,
    )

    if df is None or df.empty:
        report.issues.append("empty_dataframe")
        logger.warning(f"[{symbol}] Validation: empty DataFrame")
        return report

    # 最少行数
    if len(df) < min_rows:
        issue = f"too_few_rows({len(df)}<{min_rows})"
        report.issues.append(issue)
        logger.warning(f"[{symbol}] {issue}")

    # 价格异常 bar
    if "is_suspect" in df.columns:
        report.suspect_bars = int(df["is_suspect"].sum())
        suspect_pct = report.suspect_bars / len(df)
        if suspect_pct > 0.01:  # 超过 1% 的 bar 异常
            report.issues.append(f"high_suspect_rate({suspect_pct:.1%})")

    # 低流动性 bar
    if "is_low_liquidity" in df.columns:
        report.low_liquidity_bars = int(df["is_low_liquidity"].sum())

    # 价格逻辑校验：high >= close >= low，high >= open >= low
    price_ok = (
        (df["high"] >= df["close"]).all()
        and (df["close"] >= df["low"]).all()
        and (df["high"] >= df["open"]).all()
        and (df["open"] >= df["low"]).all()
    )
    if not price_ok:
        report.issues.append("price_ohlc_violation")
        logger.error(f"[{symbol}] OHLC price logic violation detected")

    # 负价格
    if (df[["open", "high", "low", "close"]] <= 0).any().any():
        report.issues.append("non_positive_price")

    logger.debug(report.summary())
    return report
