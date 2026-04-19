#!/usr/bin/env python3
"""
统一日志配置模块
Unified Logging Configuration

提供标准化的日志配置,替代各模块中重复的logging.basicConfig调用

作者: Athena平台团队
版本: v1.0.0
"""

from __future__ import annotations
import logging
import sys
from pathlib import Path


class LogLevel:
    """日志级别"""

    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


def setup_logging(
    level: int = logging.INFO,
    format_string: str | None = None,
    log_file: str | Path | None = None,
    name: str | None = None,
) -> logging.Logger:
    """
    设置日志配置

    Args:
        level: 日志级别,默认INFO
        format_string: 日志格式字符串,默认为标准格式
        log_file: 日志文件路径(可选)
        name: logger名称,默认为调用模块名

    Returns:
        配置好的logger实例

    Examples:
        >>> # 基础使用
        >>> logger = setup_logging()
        >>>
        >>> # 自定义级别
        >>> logger = setup_logging(level=logging.DEBUG)
        >>>
        >>> # 输出到文件
        >>> logger = setup_logging(log_file='app.log')
        >>>
        >>> # 获取命名logger
        >>> logger = setup_logging(name='my_module')
    """
    # 默认格式
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # 配置根logger(只配置一次)
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)

        formatter = logging.Formatter(format_string)
        console_handler.setFormatter(formatter)

        root_logger.addHandler(console_handler)
        root_logger.setLevel(level)

    # 获取或创建logger
    if name is None:
        # 获取调用者的模块名
        import inspect

        frame = inspect.currentframe().f_back
        name = frame.f_globals.get("__name__", "__main__")

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 添加文件处理器(如果指定)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(format_string))

        logger.addHandler(file_handler)

    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """
    获取logger实例(快捷方法)

    Args:
        name: logger名称,默认为调用模块名

    Returns:
        logger实例

    Examples:
        >>> logger = get_logger()
        >>> logger.info("Hello")
    """
    return setup_logging(name=name)


# 预配置的logger实例
def get_default_logger() -> logging.Logger:
    """获取默认配置的logger"""
    return setup_logging()


# 为了向后兼容,提供常见的配置变体
def setup_simple_logging(level: int = logging.INFO) -> logging.Logger:
    """简单日志配置(不含name)"""
    return setup_logging(level=level, format_string="%(asctime)s - %(levelname)s - %(message)s")


def setup_verbose_logging(level: int = logging.DEBUG) -> logging.Logger:
    """详细日志配置(DEBUG级别)"""
    return setup_logging(
        level=level,
        format_string="%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
    )


def setup_file_logging(
    log_file: str | Path, level: int = logging.INFO, also_console: bool = True
) -> logging.Logger:
    """
    文件日志配置

    Args:
        log_file: 日志文件路径
        level: 日志级别
        also_console: 是否同时输出到控制台
    """
    logger = setup_logging(level=level, log_file=log_file)
    return logger


# 便捷的上下文管理器,用于临时更改日志级别
class LogLevelContext:
    """临时日志级别上下文管理器"""

    def __init__(self, logger: logging.Logger, level: int):
        self.logger = logger
        self.level = level
        self.old_level = None

    def __enter__(self):
        self.old_level = self.logger.level
        self.logger.setLevel(self.level)
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.setLevel(self.old_level)
        return False


# 全局默认logger(用于快速迁移)
_default_logger = None


def logger() -> logging.Logger:
    """
    获取全局默认logger(最快方式)

    注意:这个函数会自动初始化logging,如果还未初始化的话
    """
    global _default_logger
    if _default_logger is None:
        _default_logger = get_default_logger()
    return _default_logger


# 模块导出
__all__ = [
    "LogLevel",
    "LogLevelContext",
    "get_default_logger",
    "get_logger",
    "logger",
    "setup_file_logging",
    "setup_logging",
    "setup_simple_logging",
    "setup_verbose_logging",
]
