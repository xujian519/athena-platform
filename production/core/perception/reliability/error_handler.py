#!/usr/bin/env python3
from __future__ import annotations
"""
Athena 感知模块 - 企业级错误处理框架
支持错误分类、日志记录、恢复策略
最后更新: 2026-01-26
"""

import asyncio
import functools
import logging
import traceback
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """错误类别"""
    VALIDATION = "validation"       # 输入验证错误
    PROCESSING = "processing"       # 处理错误
    EXTERNAL = "external"           # 外部服务错误
    TIMEOUT = "timeout"             # 超时错误
    RESOURCE = "resource"           # 资源不足错误
    SYSTEM = "system"               # 系统错误
    UNKNOWN = "unknown"             # 未知错误


class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"                     # 低：可忽略
    MEDIUM = "medium"               # 中：需要注意
    HIGH = "high"                   # 高：需要立即处理
    CRITICAL = "critical"           # 严重：系统可能崩溃


@dataclass
class ErrorInfo:
    """错误信息"""
    error_type: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    traceback_str: str | None = None
    context: dict[str, Any] = field(default_factory=dict)
    recovery_suggestion: str | None = None
    retry_able: bool = False


class ErrorHandler:
    """
    企业级错误处理器

    功能：
    - 错误分类和记录
    - 错误恢复策略
    - 错误告警
    - 错误统计
    - 自动恢复
    """

    def __init__(self):
        """初始化错误处理器"""
        # 错误统计
        self.error_counts: dict[str, int] = {}
        self.error_history: list[ErrorInfo] = []
        self.max_history = 1000

        # 错误处理器映射
        self.error_handlers: dict[ErrorCategory, list[Callable]] = {
            category: [] for category in ErrorCategory
        }

        # 告警回调
        self.alert_callbacks: list[Callable] = []

        logger.info("✓ 错误处理框架已初始化")

    def classify_error(self, error: Exception) -> ErrorInfo:
        """
        分类错误

        Args:
            error: 异常对象

        Returns:
            错误信息对象
        """
        error_type = type(error).__name__
        error_message = str(error)

        # 根据异常类型分类
        category = self._determine_category(error)
        severity = self._determine_severity(category, error)

        # 生成恢复建议
        recovery_suggestion = self._generate_recovery_suggestion(category, error)

        # 获取traceback
        traceback_str = ''.join(traceback.format_tb(error.__traceback__))

        error_info = ErrorInfo(
            error_type=error_type,
            category=category,
            severity=severity,
            message=error_message,
            traceback_str=traceback_str,
            recovery_suggestion=recovery_suggestion,
            retry_able=self._is_retry_able(category)
        )

        return error_info

    def _determine_category(self, error: Exception) -> ErrorCategory:
        """确定错误类别"""
        type(error).__name__
        error_message = str(error).lower()

        # 根据异常类型判断
        if isinstance(error, (ValueError, TypeError, AttributeError)):
            return ErrorCategory.VALIDATION
        elif isinstance(error, (TimeoutError, asyncio.TimeoutError)):
            return ErrorCategory.TIMEOUT
        elif isinstance(error, (MemoryError, ConnectionError)):
            return ErrorCategory.RESOURCE
        elif "connection" in error_message or "network" in error_message:
            return ErrorCategory.EXTERNAL
        elif "ocr" in error_message or "tesseract" in error_message:
            return ErrorCategory.PROCESSING
        elif "file" in error_message or "not found" in error_message:
            return ErrorCategory.RESOURCE
        else:
            return ErrorCategory.UNKNOWN

    def _determine_severity(self, category: ErrorCategory, error: Exception) -> ErrorSeverity:
        """确定错误严重程度"""
        if category == ErrorCategory.RESOURCE:
            return ErrorSeverity.HIGH
        elif category == ErrorCategory.SYSTEM:
            return ErrorSeverity.CRITICAL
        elif category == ErrorCategory.TIMEOUT:
            return ErrorSeverity.MEDIUM
        elif category == ErrorCategory.PROCESSING:
            return ErrorSeverity.MEDIUM
        elif category == ErrorCategory.VALIDATION:
            return ErrorSeverity.LOW
        else:
            return ErrorSeverity.MEDIUM

    def _generate_recovery_suggestion(self, category: ErrorCategory, error: Exception) -> str:
        """生成恢复建议"""
        suggestions = {
            ErrorCategory.VALIDATION: "请检查输入参数格式和内容",
            ErrorCategory.PROCESSING: "建议重试或使用备用处理方案",
            ErrorCategory.EXTERNAL: "检查外部服务连接状态",
            ErrorCategory.TIMEOUT: "增加超时时间或优化处理逻辑",
            ErrorCategory.RESOURCE: "释放系统资源或增加配置",
            ErrorCategory.SYSTEM: "检查系统配置和依赖服务",
            ErrorCategory.UNKNOWN: "查看日志了解详细错误信息"
        }
        return suggestions.get(category, "请查看错误详情")

    def _is_retry_able(self, category: ErrorCategory) -> bool:
        """判断错误是否可重试"""
        return category in [
            ErrorCategory.TIMEOUT,
            ErrorCategory.EXTERNAL,
            ErrorCategory.PROCESSING
        ]

    async def handle_error(
        self,
        error: Exception,
        context: dict[str, Any] | None | None = None
    ) -> ErrorInfo:
        """
        处理错误

        Args:
            error: 异常对象
            context: 错误上下文

        Returns:
            错误信息对象
        """
        # 分类错误
        error_info = self.classify_error(error)

        # 添加上下文
        if context:
            error_info.context.update(context)

        # 记录错误
        self._record_error(error_info)

        # 记录日志
        self._log_error(error_info)

        # 触发告警
        await self._trigger_alert(error_info)

        # 执行错误处理器
        await self._execute_handlers(error_info)

        return error_info

    def _record_error(self, error_info: ErrorInfo):
        """记录错误"""
        error_key = f"{error_info.category.value}:{error_info.error_type}"

        # 更新计数
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1

        # 添加到历史记录
        self.error_history.append(error_info)

        # 限制历史记录大小
        if len(self.error_history) > self.max_history:
            self.error_history.pop(0)

    def _log_error(self, error_info: ErrorInfo):
        """记录错误日志"""
        log_level_map = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }

        log_level = log_level_map.get(error_info.severity, logging.ERROR)

        log_message = (
            f"[{error_info.category.value.upper()}] "
            f"{error_info.error_type}: {error_info.message}"
        )

        if error_info.context:
            log_message += f" | Context: {error_info.context}"

        if error_info.recovery_suggestion:
            log_message += f" | 建议: {error_info.recovery_suggestion}"

        logger.log(log_level, log_message)

        if error_info.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            logger.error(f"Traceback:\n{error_info.traceback_str}")

    async def _trigger_alert(self, error_info: ErrorInfo):
        """触发告警"""
        # 只对严重错误触发告警
        if error_info.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            for callback in self.alert_callbacks:
                try:
                    await callback(error_info)
                except Exception as e:
                    logger.error(f"告警回调执行失败: {e}")

    async def _execute_handlers(self, error_info: ErrorInfo):
        """执行错误处理器"""
        handlers = self.error_handlers.get(error_info.category, [])

        for handler in handlers:
            try:
                await handler(error_info)
            except Exception as e:
                logger.error(f"错误处理器执行失败: {e}")

    def register_handler(
        self,
        category: ErrorCategory,
        handler: Callable
    ):
        """
        注册错误处理器

        Args:
            category: 错误类别
            handler: 处理函数
        """
        self.error_handlers[category].append(handler)
        logger.info(f"✓ 已注册错误处理器: {category.value}")

    def register_alert_callback(self, callback: Callable):
        """
        注册告警回调

        Args:
            callback: 回调函数
        """
        self.alert_callbacks.append(callback)
        logger.info("✓ 已注册告警回调")

    def get_error_stats(self) -> dict[str, Any]:
        """
        获取错误统计

        Returns:
            统计信息字典
        """
        total_errors = sum(self.error_counts.values())

        # 按类别统计
        category_counts = {}
        for error_key, count in self.error_counts.items():
            category = error_key.split(":")[0]
            category_counts[category] = category_counts.get(category, 0) + count

        # 最近错误
        recent_errors = [
            {
                "type": e.error_type,
                "category": e.category.value,
                "severity": e.severity.value,
                "message": e.message,
                "timestamp": e.timestamp.isoformat()
            }
            for e in self.error_history[-10:]
        ]

        return {
            "total_errors": total_errors,
            "error_counts": self.error_counts,
            "category_counts": category_counts,
            "recent_errors": recent_errors,
            "history_size": len(self.error_history)
        }

    def clear_history(self):
        """清空错误历史"""
        self.error_history.clear()
        self.error_counts.clear()
        logger.info("✓ 错误历史已清空")


def handle_errors(
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    reraise: bool = False,
    default_return: Any = None
):
    """
    错误处理装饰器

    Args:
        category: 错误类别
        reraise: 是否重新抛出异常
        default_return: 默认返回值
    """
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # 获取错误处理器（假设在类中）
                error_handler = getattr(args[0], 'error_handler', None) if args else None

                if error_handler:
                    await error_handler.handle_error(e, context={
                        "function": func.__name__,
                        "args": str(args)[:100],
                        "kwargs": str(kwargs)[:100]
                    })

                if reraise:
                    raise
                return default_return

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 对于同步函数，记录日志但不处理
                logger.error(f"错误在 {func.__name__}: {e}")
                if reraise:
                    raise
                return default_return

        # 根据函数类型返回包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# 全局错误处理器实例
global_error_handler = ErrorHandler()


# 使用示例
if __name__ == "__main__":
    import asyncio

    async def test_error_handler():
        handler = ErrorHandler()

        # 注册告警回调
        async def alert_callback(error_info: ErrorInfo):
            print(f"🚨 告警: {error_info.severity.value} - {error_info.message}")

        handler.register_alert_callback(alert_callback)

        # 测试不同类型的错误
        print("\n=== 测试1: 验证错误 ===")
        try:
            int("invalid")
        except Exception as e:
            error_info = await handler.handle_error(e, context={"test": "validation"})
            print(f"可重试: {error_info.retry_able}")
            print(f"建议: {error_info.recovery_suggestion}")

        print("\n=== 测试2: 超时错误 ===")
        try:
            raise asyncio.TimeoutError("操作超时")
        except Exception as e:
            error_info = await handler.handle_error(e, context={"test": "timeout"})
            print(f"可重试: {error_info.retry_able}")

        print("\n=== 测试3: 资源错误 ===")
        try:
            raise MemoryError("内存不足")
        except Exception as e:
            error_info = await handler.handle_error(e, context={"test": "resource"})

        # 显示统计
        print("\n=== 错误统计 ===")
        stats = handler.get_error_stats()
        print(f"总错误数: {stats['total_errors']}")
        print(f"类别统计: {stats['category_counts']}")

    asyncio.run(test_error_handler())
