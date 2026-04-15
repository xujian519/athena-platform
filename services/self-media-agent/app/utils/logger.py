#!/usr/bin/env python3
"""
日志工具
Logger Utility for Xiaochen Agent
"""

import logging
import sys
from typing import Any

from config import settings


def setup_logger() -> Any:
    """设置日志系统"""
    # 创建日志记录器
    logger = logging.getLogger("xiaochen")
    logger.set_level(getattr(logging, settings.LOG_LEVEL))

    # 避免重复添加处理器
    if logger.handlers:
        return logger

    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.set_level(logging.INFO)
    console_handler.set_formatter(formatter)
    logger.add_handler(console_handler)

    # 文件处理器
    if settings.LOG_FILE:
        file_handler = logging.FileHandler(settings.LOG_FILE, encoding='utf-8')
        file_handler.set_level(getattr(logging, settings.LOG_LEVEL))
        file_handler.set_formatter(formatter)
        logger.add_handler(file_handler)

    return logger


# 创建全局logger实例
logger = setup_logger()
