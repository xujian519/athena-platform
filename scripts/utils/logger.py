#!/usr/bin/env python3
"""
日志工具
提供统一的日志记录功能
"""

import logging
import sys
from pathlib import Path


class ScriptLogger:
    """脚本日志记录器"""

    def __init__(self, name: str, log_file: str | None = None):
        self.name = name
        self.logger = logging.getLogger(name)

        # 避免重复添加handler
        if not self.logger.handlers:
            self._setup_logger(log_file)

    def _setup_logger(self, log_file: str | None = None) -> Any:
        """设置日志记录器"""
        # 设置日志级别
        self.logger.setLevel(logging.INFO)

        # 创建formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # 控制台handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # 文件handler（如果指定了文件）
        if log_file:
            # 确保日志目录存在
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def debug(self, message: str) -> Any:
        """记录调试信息"""
        self.logger.debug(message)

    def info(self, message: str) -> Any:
        """记录信息"""
        self.logger.info(message)

    def warning(self, message: str) -> Any:
        """记录警告"""
        self.logger.warning(message)

    def error(self, message: str) -> Any:
        """记录错误"""
        self.logger.error(message)

    def critical(self, message: str) -> Any:
        """记录严重错误"""
        self.logger.critical(message)


def setup_script_logging(level: str = "INFO", log_file: str | None = None) -> Any:
    """设置脚本全局日志"""
    log_level = getattr(logging, level.upper(), logging.INFO)

    # 配置根日志记录器
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[]
    )

    # 如果指定了日志文件，添加文件handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)

        logging.getLogger().addHandler(file_handler)


def get_logger(name: str) -> ScriptLogger:
    """获取日志记录器"""
    return ScriptLogger(name)
