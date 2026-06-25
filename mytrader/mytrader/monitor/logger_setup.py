"""logger_setup — loguru 结构化日志配置。

功能：
- 按日轮转，保留 30 天
- JSON 序列化，方便后续解析
- 支持动态配置日志级别
"""

from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger


def setup_logger(
    log_dir: str | Path = "logs",
    level: str = "INFO",
    rotation: str = "1 day",
    retention: str = "30 days",
    serialize: bool = True,
) -> None:
    """初始化 loguru 日志配置。

    Args:
        log_dir:   日志目录（相对或绝对路径）
        level:     日志级别（DEBUG/INFO/WARN/ERROR）
        rotation:  轮转策略（"1 day"/"100 MB" 等）
        retention: 保留时长（"30 days"/"7 days" 等）
        serialize: 是否 JSON 序列化（生产建议 True；开发建议 False）
    """
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    # 移除默认 handler，重新配置
    logger.remove()

    # 控制台输出（人类可读，不序列化）
    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level:<8}</level> | "
               "<cyan>{module}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | {message}",
        colorize=True,
    )

    # 文件输出（JSON，方便解析）
    logger.add(
        str(log_dir / "mytrader_{time:YYYY-MM-DD}.log"),
        level=level,
        rotation=rotation,
        retention=retention,
        serialize=serialize,
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} | {message}",
    )

    # 专用告警日志（仅 WARN 及以上，保留 90 天）
    logger.add(
        str(log_dir / "alerts_{time:YYYY-MM-DD}.log"),
        level="WARNING",
        rotation="1 day",
        retention="90 days",
        serialize=True,
        encoding="utf-8",
    )

    logger.info(f"Logger initialized: level={level}, log_dir={log_dir}, serialize={serialize}")
