
#!/usr/bin/env python3
"""
小诺·双鱼公主日志系统
Xiaonuo Pisces Princess Logging System

为小诺·双鱼公主提供结构化、标准化的日志记录功能

作者: Athena平台团队
创建时间: 2025-12-18
版本: v1.0.0
"""

import asyncio
import json
import logging
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class LogLevel(Enum):
    """日志级别枚举"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogCategory(Enum):
    """日志分类枚举"""

    SYSTEM = "system"
    AGENT = "agent"
    COORDINATION = "coordination"
    REFLECTION = "reflection"
    FAMILY = "family"
    PERFORMANCE = "performance"
    SECURITY = "security"
    API = "api"
    DATABASE = "infrastructure/infrastructure/database"
    EXTERNAL = "external"


@dataclass
class LogContext:
    """日志上下文"""

    session_id: Optional[str] = None
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    component: Optional[str] = None
    action: Optional[str] = None
    extra: Optional[dict[str, Any]] = None


class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器"""

    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        # 基础日志信息
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.get_message(),
            "module": record.module,
            "function": record.func_name,
            "line": record.lineno,
            "thread": record.thread,
            "thread_name": record.thread_name,
            "process": record.process,
        }

        # 添加异常信息
        if record.exc_info:
            log_data["exception"]] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info),
            }

        # 添加分类和上下文信息
        if hasattr(record, "category"):
            log_data["category"] = record.category
        if hasattr(record, "context"):
            log_data["context"] = record.context

        # 添加额外字段
        if self.include_extra:
            extra_fields = {}
            for key, value in record.__dict__.items():
                if key not in {
                    "name",
                    "msg",
                    "args",
                    "levelname",
                    "levelno",
                    "pathname",
                    "filename",
                    "module",
                    "lineno",
                    "func_name",
                    "created",
                    "msecs",
                    "relative_created",
                    "thread",
                    "thread_name",
                    "process_name",
                    "process",
                    "get_message",
                    "exc_info",
                    "exc_text",
                    "stack_info",
                    "category",
                    "context",
                }:
                    extra_fields[key] = value

            if extra_fields:
                log_data["extra"] = extra_fields

        return json.dumps(log_data, ensure_ascii=False, default=str)


class ColoredConsoleFormatter(logging.Formatter):
    """彩色控制台日志格式化器"""

    # 颜色代码
    COLORS = {
        "DEBUG": "\033[36m",  # 青色
        "INFO": "\033[32m",  # 绿色
        "WARNING": "\033[33m",  # 黄色
        "ERROR": "\033[31m",  # 红色
        "CRITICAL": "\033[35m",  # 紫色
        "RESET": "\033[0m",  # 重置
    }

    # 表情符号
    EMOJIS = {"DEBUG": "🔍", "INFO": "ℹ️", "WARNING": "⚠️", "ERROR": "❌", "CRITICAL": "🔥"}

    def format(self, record: logging.LogRecord) -> str:
        """格式化控制台日志"""
        color = self.COLORS.get(record.levelname, "")
        reset = self.COLORS["RESET"]
        emoji = self.EMOJIS.get(record.levelname, "")

        # 基础格式
        timestamp = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
        logger_name = record.name.split(".")[-1]  # 只显示最后部分

        # 添加分类信息
        category = f"[{record.category}]" if hasattr(record, "category") else ""

        # 格式化消息
        message = record.get_message()

        # 构建最终格式
        formatted = f"{color}{emoji} {timestamp} {logger_name}{category} {record.levelname}: {message}{reset}"

        # 添加异常信息
        if record.exc_info:
            formatted += f"\n{color}{traceback.format_exc()}{reset}"

        return formatted


class XiaonuoLogger:
    """小诺·双鱼公主专用日志器"""

    def __init__(self, name: str = "xiaonuo_princess"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.context = LogContext()
        self._setup_logger()

    def _setup_logger(self) -> Any:
        """设置日志器"""
        # 防止重复设置
        if self.logger.handlers:
            return

        # 从环境变量获取日志配置
        from core.config.environment_manager import get_env_manager

        env_manager = get_env_manager()

        log_level = getattr(logging, env_manager.log_level.upper())
        log_path = env_manager.logs_path
        is_debug = env_manager.debug

        # 设置日志级别
        self.logger.set_level(log_level)

        # 创建日志目录
        log_path.mkdir(parents=True, exist_ok=True)

        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.set_level(log_level)

        if is_debug:
            console_formatter = ColoredConsoleFormatter()
        else:
            console_formatter = StructuredFormatter(include_extra=False)

        console_handler.set_formatter(console_formatter)
        self.logger.add_handler(console_handler)

        # 文件处理器 - JSON格式
        json_handler = logging.FileHandler(log_path / f"{self.name}.json", encoding="utf-8")
        json_handler.set_level(log_level)
        json_formatter = StructuredFormatter(include_extra=True)
        json_handler.set_formatter(json_formatter)
        self.logger.add_handler(json_handler)

        # 错误日志文件
        error_handler = logging.FileHandler(log_path / f"{self.name}_error.json", encoding="utf-8")
        error_handler.set_level(logging.ERROR)
        error_formatter = StructuredFormatter(include_extra=True)
        error_handler.set_formatter(error_formatter)
        self.logger.add_handler(error_handler)

        # 防止日志传播到根日志器
        self.logger.propagate = False

    def set_context(self, **kwargs) -> None:
        """设置日志上下文"""
        for key, value in kwargs.items():
            if hasattr(self.context, key):
                setattr(self.context, key, value)

    def clear_context(self) -> None:
        """清除日志上下文"""
        self.context = LogContext()

    def _log(self, level: LogLevel, message: str, category: LogCategory = None, **kwargs) -> Any:
        """内部日志记录方法"""
        # 添加上下文和分类信息
        extra = {
            "context": asdict(self.context) if any(asdict(self.context).values()) else None,
        }

        if category:
            extra["category"] = category.value

        # 添加额外字段
        extra.update(kwargs)

        # 记录日志
        log_method = getattr(self.logger, level.value.lower())
        log_method(message, extra=extra)

    def debug(self, message: str, category: LogCategory = LogCategory.SYSTEM, **kwargs) -> Any:
        """记录调试日志"""
        self._log(LogLevel.DEBUG, message, category, **kwargs)

    def info(self, message: str, category: LogCategory = LogCategory.SYSTEM, **kwargs) -> Any:
        """记录信息日志"""
        self._log(LogLevel.INFO, message, category, **kwargs)

    def warning(self, message: str, category: LogCategory = LogCategory.SYSTEM, **kwargs) -> Any:
        """记录警告日志"""
        self._log(LogLevel.WARNING, message, category, **kwargs)

    def error(self, message: str, category: LogCategory = LogCategory.SYSTEM, **kwargs) -> Any:
        """记录错误日志"""
        self._log(LogLevel.ERROR, message, category, **kwargs)

    def critical(self, message: str, category: LogCategory = LogCategory.SYSTEM, **kwargs) -> Any:
        """记录关键日志"""
        self._log(LogLevel.CRITICAL, message, category, **kwargs)

    # 专门的分类日志方法
    def log_agent_action(self, action: str, message: str, **kwargs) -> Any:
        """记录智能体动作日志"""
        self.info(message, LogCategory.AGENT, action=action, **kwargs)

    def log_coordination(self, task: str, agents: list, result: Any, **kwargs) -> Any:
        """记录协调日志"""
        self.info(
            f"协调任务完成: {task}",
            LogCategory.COORDINATION,
            task=task,
            agents=agents,
            result_type=type(result).__name__,
            **kwargs,
        )

    def log_reflection(self, experience: str, learning_points: list, **kwargs) -> Any:
        """记录反思日志"""
        self.info(
            f"反思完成: {experience}",
            LogCategory.REFLECTION,
            experience=experience,
            learning_points_count=len(learning_points),
            **kwargs,
        )

    def log_family_interaction(self, emotion: str, message: str, **kwargs) -> Any:
        """记录家庭互动日志"""
        self.info(message, LogCategory.FAMILY, emotion=emotion, **kwargs)

    def log_performance(self, operation: str, duration: float, **kwargs) -> Any:
        """记录性能日志"""
        level = LogLevel.WARNING if duration > 1.0 else LogLevel.INFO
        self._log(
            level,
            f"性能指标: {operation} 耗时 {duration:.3f}s",
            LogCategory.PERFORMANCE,
            operation=operation,
            duration=duration,
            **kwargs,
        )

    def log_security_event(self, event: str, severity: str = "medium", **kwargs) -> Any:
        """记录安全事件日志"""
        level = LogLevel.ERROR if severity == "high" else LogLevel.WARNING
        self._log(
            level,
            f"安全事件: {event}",
            LogCategory.SECURITY,
            event=event,
            severity=severity,
            **kwargs,
        )

    def log_api_request(
        self, method: str, endpoint: str, status_code: int, duration: float, **kwargs
    ) -> Any:
        """记录API请求日志"""
        level = (
            LogLevel.ERROR
            if status_code >= 400
            else LogLevel.WARNING if status_code >= 300 else LogLevel.INFO
        )
        self._log(
            level,
            f"API请求: {method} {endpoint} -> {status_code}",
            LogCategory.API,
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            duration=duration,
            **kwargs,
        )

    def log_database_operation(self, operation: str, table: str, duration: float, **kwargs) -> Any:
        """记录数据库操作日志"""
        level = LogLevel.WARNING if duration > 0.5 else LogLevel.INFO
        self._log(
            level,
            f"数据库操作: {operation} on {table}",
            LogCategory.DATABASE,
            operation=operation,
            table=table,
            duration=duration,
            **kwargs,
        )

    def log_external_service(
        self, service: str, operation: str, success: bool, duration: float, **kwargs
    ) -> Any:
        """记录外部服务调用日志"""
        level = (
            LogLevel.ERROR if not success else LogLevel.WARNING if duration > 2.0 else LogLevel.INFO
        )
        status = "成功" if success else "失败"
        self._log(
            level,
            f"外部服务: {service} {operation} {status}",
            LogCategory.EXTERNAL,
            service=service,
            operation=operation,
            success=success,
            duration=duration,
            **kwargs,
        )

    def log_exception(self, message: str, exception: Exception, **kwargs) -> Any:
        """记录异常日志"""
        self.error(
            f"异常: {message}",
            category=LogCategory.SYSTEM,
            exception_type=type(exception).__name__,
            exception_message=str(exception),
            **kwargs,
        )

    def async_log(
        self, level: LogLevel, message: str, category: LogCategory = None, **kwargs
    ) -> Any:
        """异步日志记录"""
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=1) as executor:
            loop.run_in_executor(executor, self._log, level, message, category, **kwargs)

    def create_child_logger(self, name: str) -> XiaonuoLogger:
        """创建子日志器"""
        child_name = f"{self.name}.{name}"
        child_logger = XiaonuoLogger(child_name)
        child_logger.context = self.context  # 继承上下文
        return child_logger

    def get_log_stats(self) -> dict[str, Any]:
        """获取日志统计信息"""
        from core.config.environment_manager import get_env_manager

        env_manager = get_env_manager()

        log_files = {
            "main": env_manager.logs_path / f"{self.name}.json",
            "error": env_manager.logs_path / f"{self.name}_error.json",
        }

        stats = {}
        for log_type, file_path in log_files.items():
            if file_path.exists():
                stat = file_path.stat()
                stats[log_type]] = {
                    "size_bytes": stat.st_size,
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "exists": True,
                }
            else:
                stats[log_type]] = {"exists": False}

        return {
            "logger_name": self.name,
            "level": logging.get_level_name(self.logger.level),
            "handlers_count": len(self.logger.handlers),
            "log_files": stats,
        }


# 全局日志器实例
_global_logger: Optional[XiaonuoLogger] = None


def get_logger(name: str = "xiaonuo_princess") -> XiaonuoLogger:
    """获取全局日志器实例"""
    global _global_logger
    if _global_logger is None:
        _global_logger = XiaonuoLogger(name)
    return _global_logger


def setup_logging() -> Any:
    """设置全局日志配置"""
    # 确保日志目录存在
    from core.config.environment_manager import get_env_manager

    env_manager = get_env_manager()
    env_manager.logs_path.mkdir(parents=True, exist_ok=True)

    # 设置第三方库的日志级别
    logging.getLogger("urllib3").set_level(logging.WARNING)
    logging.getLogger("requests").set_level(logging.WARNING)
    logging.getLogger("asyncio").set_level(logging.WARNING)

    # 获取全局日志器
    logger = get_logger()
    logger.info("小诺·双鱼公主日志系统初始化完成", LogCategory.SYSTEM)


# 装饰器:自动记录函数执行日志
def log_execution(
    logger: Optional[XiaonuoLogger] = None, category: LogCategory = LogCategory.SYSTEM
) -> Any:
    """装饰器:自动记录函数执行日志"""

    def decorator(func) -> None:
        def sync_wrapper(*args, **kwargs) -> Any:
            log = logger or get_logger()
            func_name = func.__name__
            module_name = func.__module__

            log.set_context(
                function=func_name,
                module=module_name,
            )

            start_time = datetime.now()
            log.info(f"开始执行: {func_name}", category)

            try:
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                log.info(f"执行完成: {func_name}", category, duration=duration, success=True)
                return result

            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                log.log_exception(
                    f"执行失败: {func_name}", e, category=category, duration=duration, success=False
                )
                raise

        async def async_wrapper(*args, **kwargs):
            log = logger or get_logger()
            func_name = func.__name__
            module_name = func.__module__

            log.set_context(
                function=func_name,
                module=module_name,
            )

            start_time = datetime.now()
            log.info(f"开始执行: {func_name}", category)

            try:
                result = await func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                log.info(f"执行完成: {func_name}", category, duration=duration, success=True)
                return result

            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                log.log_exception(
                    f"执行失败: {func_name}", e, category=category, duration=duration, success=False
                )
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


if __name__ == "__main__":
    # 测试日志系统
    setup_logging()
    logger = get_logger()

    print("🧪 测试小诺·双鱼公主日志系统")
    print("=" * 60)

    # 测试各种日志级别
    logger.debug("这是调试信息", LogCategory.SYSTEM)
    logger.info("这是普通信息", LogCategory.SYSTEM)
    logger.warning("这是警告信息", LogCategory.SYSTEM)
    logger.error("这是错误信息", LogCategory.SYSTEM)

    # 测试分类日志
    logger.log_agent_action("初始化", "智能体初始化完成")
    logger.log_coordination("任务调度", ["小娜", "知识图谱"], {"status": "success"})
    logger.log_reflection("学习经验", ["学会了新知识", "提升了能力"])
    logger.log_family_interaction("love", "爸爸,我爱您!")
    logger.log_performance("提示词生成", 0.123)

    # 测试异常日志
    try:
        raise ValueError("这是一个测试异常")
    except Exception as e:
        logger.log_exception("测试异常处理", e)

    # 显示日志统计
    stats = logger.get_log_stats()
    print("\n📊 日志统计:")
    import json

    print(json.dumps(stats, indent=2, ensure_ascii=False))

