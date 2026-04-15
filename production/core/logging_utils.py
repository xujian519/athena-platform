"""
日志工具模块
Logging Utilities Module

提供结构化日志和日志增强功能
"""

from __future__ import annotations
import json
import logging
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

# ============================================
# 结构化日志记录器
# ============================================


class StructuredLogger:
    """结构化日志记录器"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.context: dict[str, Any] = {}

    def with_context(self, **kwargs) -> "StructuredLogger":
        """添加上下文信息"""
        new_logger = StructuredLogger(self.logger.name)
        new_logger.context = {**self.context, **kwargs}
        return new_logger

    def _log(self, level: int, message: str, **kwargs) -> Any:
        """内部日志方法"""
        # 合并上下文和额外信息
        extra = {**self.context, **kwargs}

        # 格式化消息
        if extra:
            formatted_message = f"{message} | {json.dumps(extra, ensure_ascii=False)}"
        else:
            formatted_message = message

        self.logger.log(level, formatted_message)

    def debug(self, message: str, **kwargs) -> Any:
        """调试日志"""
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs) -> Any:
        """信息日志"""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs) -> Any:
        """警告日志"""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs) -> Any:
        """错误日志"""
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs) -> Any:
        """严重错误日志"""
        self._log(logging.CRITICAL, message, **kwargs)

    def exception(self, message: str, **kwargs) -> Any:
        """异常日志(包含堆栈跟踪)"""
        self.logger.exception(message, extra={**self.context, **kwargs})


def get_logger(name: str) -> StructuredLogger:
    """获取结构化日志记录器"""
    return StructuredLogger(name)


# ============================================
# 性能日志装饰器
# ============================================

import functools
import time


def log_execution_time(logger: logging.Logger | None = None) -> Any:
    """记录函数执行时间"""

    def decorator(func) -> None:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            log = logger or logging.getLogger(func.__module__)

            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                elapsed = time.perf_counter() - start_time
                log.info(f"{func.__name__} 执行时间: {elapsed:.3f}s")

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            log = logger or logging.getLogger(func.__module__)

            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed = time.perf_counter() - start_time
                log.debug(f"{func.__name__} 执行时间: {elapsed:.3f}s")

        # 根据函数类型返回对应的wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# ============================================
# 日志上下文管理器
# ============================================


@contextmanager
def log_context(logger: logging.Logger, **kwargs) -> Any:
    """日志上下文管理器"""
    # 添加临时上下文
    old_factory = logging.get_log_record_factory()

    def record_factory(*args, **factory_kwargs) -> Any:
        record = old_factory(*args, **factory_kwargs)
        for key, value in kwargs.items():
            setattr(record, key, value)
        return record

    logging.set_log_record_factory(record_factory)

    try:
        yield
    finally:
        logging.set_log_record_factory(old_factory)


# ============================================
# 日志文件管理
# ============================================


class LogFileManager:
    """日志文件管理器"""

    def __init__(self, log_dir: str = "/var/log/athena"):
        self.log_dir = Path(log_dir)
        self.ensure_log_dir()

    def ensure_log_dir(self) -> Any:
        """确保日志目录存在"""
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def get_log_files(self) -> dict[str, Path]:
        """获取所有日志文件路径"""
        return {
            "app": self.log_dir / "app.log",
            "error": self.log_dir / "error.log",
            "security": self.log_dir / "security.log",
            "performance": self.log_dir / "performance.log",
            "access": self.log_dir / "access.log",
        }

    def get_log_size(self) -> dict[str, int]:
        """获取日志文件大小(字节)"""
        sizes = {}
        for name, path in self.get_log_files().items():
            if path.exists():
                sizes[name] = path.stat().st_size
            else:
                sizes[name] = 0
        return sizes

    def rotate_logs(self) -> Any:
        """手动轮转日志"""
        for _name, path in self.get_log_files().items():
            if path.exists():
                # 重命名当前日志文件
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = path.parent / f"{path.stem}.{timestamp}.log"
                path.rename(backup_path)

                # 创建新的日志文件
                path.touch()


# ============================================
# 日志搜索工具
# ============================================


class LogSearcher:
    """日志搜索工具"""

    def __init__(self, log_file: Path):
        self.log_file = log_file

    def search_by_level(self, level: str) -> list:
        """按日志级别搜索"""
        results = []
        if not self.log_file.exists():
            return results

        with open(self.log_file, encoding="utf-8") as f:
            for line in f:
                if f"| {level.upper()} |" in line:
                    results.append(line.strip())

        return results

    def search_by_time_range(self, start_time: str, end_time: str) -> list:
        """按时间范围搜索"""
        results = []
        if not self.log_file.exists():
            return results

        with open(self.log_file, encoding="utf-8") as f:
            for line in f:
                # 提取时间戳
                try:
                    timestamp_str = line.split("|")[0].strip()
                    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

                    start = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
                    end = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")

                    if start <= timestamp <= end:
                        results.append(line.strip())

                except (ValueError, IndexError):
                    continue

        return results

    def search_by_keyword(self, keyword: str) -> list:
        """按关键词搜索"""
        results = []
        if not self.log_file.exists():
            return results

        with open(self.log_file, encoding="utf-8") as f:
            for line in f:
                if keyword in line:
                    results.append(line.strip())

        return results

    def get_recent_logs(self, lines: int = 100) -> list:
        """获取最近的日志"""
        results = []
        if not self.log_file.exists():
            return results

        with open(self.log_file, encoding="utf-8") as f:
            all_lines = f.readlines()
            results = [line.strip() for line in all_lines[-lines:]]

        return results


# ============================================
# 导入asyncio
# ============================================
try:
    import asyncio
except ImportError:
    asyncio = None


# ============================================
# 便捷函数
# ============================================


def setup_logging(config_file: str = "config/logging.yaml") -> Any:
    """设置日志配置"""
    import yaml

    try:
        with open(config_file) as f:
            config = yaml.safe_load(f)
            logging.config.dict_config(config)

        logging.info("日志配置加载成功")
        return True

    except Exception as e:
        # 如果配置文件加载失败,使用基本配置
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        logging.warning(f"日志配置文件加载失败,使用基本配置: {e}")
        return False


def get_log_manager() -> LogFileManager:
    """获取日志文件管理器"""
    return LogFileManager()


def search_logs(log_type: str = "app") -> LogSearcher:
    """获取日志搜索器"""
    manager = get_log_manager()
    log_files = manager.get_log_files()

    if log_type in log_files:
        return LogSearcher(log_files[log_type])
    else:
        raise ValueError(f"未知的日志类型: {log_type}")
