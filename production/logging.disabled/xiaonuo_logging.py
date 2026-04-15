#!/usr/bin/env python3
"""
小诺日志配置模块
Xiaonuo Logging Configuration

提供统一的日志记录配置：
- 标准化日志格式
- 多级别日志输出
- 文件和控制台双输出
- 按日期滚动日志文件

作者: Athena团队
创建时间: 2026-02-09
版本: v1.0.0
"""

from __future__ import annotations
import logging
import sys
from pathlib import Path

# =============================================================================
# 日志格式
# =============================================================================

# 控制台日志格式（简洁）
CONSOLE_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
CONSOLE_DATE_FORMAT = "%H:%M:%S"

# 文件日志格式（详细）
FILE_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s"
FILE_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


# =============================================================================
# 日志配置
# =============================================================================

def setup_logging(
    name: str,
    level: int = logging.INFO,
    log_file: Path | None = None,
    console: bool = True
) -> logging.Logger:
    """
    设置并返回配置好的日志记录器

    参数:
        name: 日志记录器名称
        level: 日志级别 (默认: INFO)
        log_file: 日志文件路径 (可选)
        console: 是否输出到控制台 (默认: True)

    返回:
        logging.Logger: 配置好的日志记录器
    """
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 避免重复添加处理器
    if logger.handlers:
        return logger

    # 创建格式化器
    console_formatter = logging.Formatter(
        CONSOLE_FORMAT,
        datefmt=CONSOLE_DATE_FORMAT
    )
    file_formatter = logging.Formatter(
        FILE_FORMAT,
        datefmt=FILE_DATE_FORMAT
    )

    # 控制台处理器
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    # 文件处理器
    if log_file:
        # 确保日志目录存在
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(
            log_file,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    获取已配置的日志记录器

    参数:
        name: 日志记录器名称

    返回:
        logging.Logger: 日志记录器实例
    """
    return logging.getLogger(name)


# =============================================================================
# 预配置的日志记录器
# =============================================================================

# 监控服务日志记录器
_monitor_logger: logging.Logger | None = None


def get_monitor_logger() -> logging.Logger:
    """获取监控服务的日志记录器"""
    global _monitor_logger

    if _monitor_logger is None:
        log_file = Path("logs/monitoring.log")
        _monitor_logger = setup_logging(
            "xiaonuo.monitoring",
            level=logging.INFO,
            log_file=log_file,
            console=True
        )

    return _monitor_logger


# 健康检查服务日志记录器
_health_logger: logging.Logger | None = None


def get_health_logger() -> logging.Logger:
    """获取健康检查服务的日志记录器"""
    global _health_logger

    if _health_logger is None:
        log_file = Path("logs/health_check.log")
        _health_logger = setup_logging(
            "xiaonuo.health",
            level=logging.INFO,
            log_file=log_file,
            console=True
        )

    return _health_logger


# =============================================================================
# 使用示例
# =============================================================================

if __name__ == "__main__":
    # 创建测试日志记录器
    logger = setup_logging(
        "test",
        level=logging.DEBUG,
        log_file=Path("logs/test.log")
    )

    # 测试不同级别的日志
    logger.debug("这是DEBUG级别的日志")
    logger.info("这是INFO级别的日志")
    logger.warning("这是WARNING级别的日志")
    logger.error("这是ERROR级别的日志")
    logger.critical("这是CRITICAL级别的日志")

    # 测试预配置的日志记录器
    monitor_logger = get_monitor_logger()
    monitor_logger.info("监控服务日志测试")

    health_logger = get_health_logger()
    health_logger.info("健康检查服务日志测试")
