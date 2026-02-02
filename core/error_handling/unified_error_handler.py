#!/usr/bin/env python3
"""
统一错误处理框架
Unified Error Handling Framework

为整个平台提供统一的错误处理能力:
1. 错误分类体系
2. 错误恢复策略
3. 优雅降级机制
4. 错误监控和告警
5. 自动重试策略
6. 错误日志追踪

作者: Athena平台团队
创建时间: 2025-12-26
版本: v1.0.0 "统一错误处理"
"""

import asyncio
import logging
import traceback
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """错误严重程度"""

    INFO = "info"  # 信息
    WARNING = "warning"  # 警告
    ERROR = "error"  # 错误
    CRITICAL = "critical"  # 严重
    FATAL = "fatal"  # 致命


class ErrorCategory(Enum):
    """错误类别"""

    VALIDATION = "validation"  # 验证错误
    EXECUTION = "execution"  # 执行错误
    TIMEOUT = "timeout"  # 超时错误
    RESOURCE = "resource"  # 资源错误
    DEPENDENCY = "dependency"  # 依赖错误
    PERMISSION = "permission"  # 权限错误
    NETWORK = "network"  # 网络错误
    SYSTEM = "system"  # 系统错误
    UNKNOWN = "unknown"  # 未知错误


class RecoveryStrategy(Enum):
    """恢复策略"""

    RETRY = "retry"  # 重试
    FALLBACK = "fallback"  # 降级
    IGNORE = "ignore"  # 忽略
    ESCALATE = "escalate"  # 升级
    TERMINATE = "terminate"  # 终止


@dataclass
class ErrorRecord:
    """错误记录"""

    error_id: str
    error_type: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    stack_trace: str | None = None
    context: dict[str, Any] = field(default_factory=dict)
    recovery_strategy: RecoveryStrategy | None = None
    recovery_attempted: bool = False
    recovery_successful: bool = False
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RecoveryAction:
    """恢复动作"""

    name: str
    strategy: RecoveryStrategy
    max_attempts: int = 3
    delay: float = 1.0
    action: Callable | None = None


class UnifiedErrorHandler:
    """
    统一错误处理器

    核心功能:
    1. 错误捕获和分类
    2. 自动恢复
    3. 优雅降级
    4. 错误追踪
    5. 监控告警
    6. 统计分析
    """

    def __init__(self):
        # 错误历史
        self.error_history: deque[ErrorRecord] = deque(maxlen=10000)

        # 错误统计
        self.error_stats: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

        # 恢复策略映射
        self.recovery_strategies: dict[ErrorCategory, list[RecoveryAction]] = {}

        # 降级处理器
        self.fallback_handlers: dict[str, Callable] = {}

        # 告警规则
        self.alert_rules: list[Callable] = []

        # 初始化默认恢复策略
        self._initialize_default_strategies()

        logger.info("🛡️ 统一错误处理框架初始化完成")

    def _initialize_default_strategies(self) -> Any:
        """初始化默认恢复策略"""
        # 超时错误:重试
        self.recovery_strategies[ErrorCategory.TIMEOUT] = [
            RecoveryAction(
                name="retry_with_backoff",
                strategy=RecoveryStrategy.RETRY,
                max_attempts=3,
                delay=2.0,
            )
        ]

        # 网络错误:重试 + 降级
        self.recovery_strategies[ErrorCategory.NETWORK] = [
            RecoveryAction(
                name="retry_network", strategy=RecoveryStrategy.RETRY, max_attempts=5, delay=1.0
            ),
            RecoveryAction(name="use_cache", strategy=RecoveryStrategy.FALLBACK),
        ]

        # 依赖错误:降级
        self.recovery_strategies[ErrorCategory.DEPENDENCY] = [
            RecoveryAction(name="use_alternative", strategy=RecoveryStrategy.FALLBACK)
        ]

        # 验证错误:忽略(由调用方处理)
        self.recovery_strategies[ErrorCategory.VALIDATION] = [
            RecoveryAction(name="skip_validation", strategy=RecoveryStrategy.IGNORE)
        ]

    async def handle_error(
        self, error: Exception, context: dict[str, Any] | None = None
    ) -> ErrorRecord:
        """
        处理错误

        Args:
            error: 异常对象
            context: 错误上下文

        Returns:
            ErrorRecord: 错误记录
        """
        # 1. 分类错误
        category = await self._classify_error(error)

        # 2. 确定严重程度
        severity = await self._determine_severity(error, category)

        # 3. 创建错误记录
        error_record = ErrorRecord(
            error_id=self._generate_error_id(),
            error_type=type(error).__name__,
            category=category,
            severity=severity,
            message=str(error),
            stack_trace=traceback.format_exc(),
            context=context or {},
        )

        # 4. 记录错误
        self.error_history.append(error_record)
        self.error_stats[category.value][severity.value] += 1

        # 5. 尝试恢复
        recovery_actions = self.recovery_strategies.get(category, [])
        if recovery_actions:
            for action in recovery_actions:
                success = await self._attempt_recovery(error_record, action)
                if success:
                    error_record.recovery_successful = True
                    break

        # 6. 检查告警
        await self._check_alerts(error_record)

        # 7. 记录日志
        self._log_error(error_record)

        return error_record

    async def _classify_error(self, error: Exception) -> ErrorCategory:
        """分类错误"""
        error_type = type(error).__name__

        # 超时错误
        if "timeout" in error_type.lower() or isinstance(error, asyncio.TimeoutError):
            return ErrorCategory.TIMEOUT

        # 网络错误
        network_errors = ["ConnectionError", "HTTPError", "RequestException"]
        if any(ne in error_type for ne in network_errors):
            return ErrorCategory.NETWORK

        # 验证错误
        validation_errors = ["ValidationError", "ValueError", "TypeError"]
        if any(ve in error_type for ve in validation_errors):
            return ErrorCategory.VALIDATION

        # 权限错误
        permission_errors = ["PermissionError", "AccessDenied", "Unauthorized"]
        if any(pe in error_type for pe in permission_errors):
            return ErrorCategory.PERMISSION

        # 资源错误
        resource_errors = ["ResourceNotFound", "FileNotFound", "OutOfMemory"]
        if any(re in error_type for re in resource_errors):
            return ErrorCategory.RESOURCE

        # 依赖错误
        if "dependency" in str(error).lower():
            return ErrorCategory.DEPENDENCY

        # 系统错误
        system_errors = ["SystemError", "RuntimeError", "InternalError"]
        if any(se in error_type for se in system_errors):
            return ErrorCategory.SYSTEM

        return ErrorCategory.UNKNOWN

    async def _determine_severity(self, error: Exception, category: ErrorCategory) -> ErrorSeverity:
        """确定严重程度"""
        # 致命错误
        if isinstance(error, (SystemExit, KeyboardInterrupt)):
            return ErrorSeverity.FATAL

        # 严重错误
        if category in [ErrorCategory.SYSTEM, ErrorCategory.RESOURCE]:
            return ErrorSeverity.CRITICAL

        # 错误
        if category in [ErrorCategory.EXECUTION, ErrorCategory.DEPENDENCY]:
            return ErrorSeverity.ERROR

        # 警告
        if category in [ErrorCategory.VALIDATION, ErrorCategory.TIMEOUT]:
            return ErrorSeverity.WARNING

        return ErrorSeverity.INFO

    async def _attempt_recovery(self, error_record: ErrorRecord, action: RecoveryAction) -> bool:
        """尝试恢复"""
        error_record.recovery_strategy = action.strategy
        error_record.recovery_attempted = True

        if action.strategy == RecoveryStrategy.RETRY:
            # 重试逻辑(由调用方实现)
            logger.info(f"🔄 尝试重试: {action.name}")
            return False  # 需要调用方配合

        elif action.strategy == RecoveryStrategy.FALLBACK:
            # 降级逻辑
            logger.info(f"⬇️ 尝试降级: {action.name}")

            # 查找降级处理器
            fallback_key = error_record.context.get("operation", "")
            if fallback_key in self.fallback_handlers:
                try:
                    result = await self.fallback_handlers[fallback_key](error_record)
                    return result is not None
                except Exception as e:
                    logger.warning(f"⚠️ 降级失败: {e}")
                    return False

        elif action.strategy == RecoveryStrategy.IGNORE:
            # 忽略错误
            logger.info(f"⏭️ 忽略错误: {action.name}")
            return True

        elif action.strategy == RecoveryStrategy.ESCALATE:
            # 升级处理
            logger.warning(f"⬆️ 升级错误: {action.name}")
            return False

        elif action.strategy == RecoveryStrategy.TERMINATE:
            # 终止操作
            logger.critical(f"🛑 终止操作: {action.name}")
            return False

        return False

    def register_fallback(self, key: str, handler: Callable) -> Any:
        """注册降级处理器"""
        self.fallback_handlers[key] = handler
        logger.info(f"📝 降级处理器已注册: {key}")

    async def execute_with_fallback(
        self, primary_func: Callable, fallback_func: Callable, *args, **kwargs
    ) -> Any:
        """
        带降级的执行

        Args:
            primary_func: 主函数
            fallback_func: 降级函数
            *args, **kwargs: 参数

        Returns:
            Any: 执行结果
        """
        try:
            if asyncio.iscoroutinefunction(primary_func):
                return await primary_func(*args, **kwargs)
            else:
                return primary_func(*args, **kwargs)

        except Exception as e:
            logger.warning(f"⚠️ 主函数失败,使用降级: {e}")

            await self.handle_error(
                e, context={"operation": "execute_with_fallback"}
            )

            try:
                if asyncio.iscoroutinefunction(fallback_func):
                    return await fallback_func(*args, **kwargs)
                else:
                    return fallback_func(*args, **kwargs)

            except Exception as fallback_error:
                logger.error(f"❌ 降级函数也失败: {fallback_error}")
                await self.handle_error(fallback_error, context={"operation": "fallback"})
                raise

    async def _check_alerts(self, error_record: ErrorRecord):
        """检查告警"""
        for rule in self.alert_rules:
            try:
                should_alert = await rule(error_record)
                if should_alert:
                    await self._send_alert(error_record)
            except Exception as e:
                logger.error(f"❌ 告警规则执行失败: {e}")

    async def _send_alert(self, error_record: ErrorRecord):
        """发送告警"""
        # 简化实现:记录日志
        logger.critical(
            f"🚨 错误告警: [{error_record.severity.value.upper()}] "
            f"{error_record.error_type}: {error_record.message}"
        )

    def _log_error(self, error_record: ErrorRecord) -> Any:
        """记录错误日志"""
        log_func = {
            ErrorSeverity.INFO: logger.info,
            ErrorSeverity.WARNING: logger.warning,
            ErrorSeverity.ERROR: logger.error,
            ErrorSeverity.CRITICAL: logger.critical,
            ErrorSeverity.FATAL: logger.critical,
        }.get(error_record.severity, logger.error)

        log_func(
            f"[{error_record.category.value.upper()}] "
            f"{error_record.error_type}: {error_record.message}"
        )

    def _generate_error_id(self) -> str:
        """生成错误ID"""
        import uuid

        return f"ERR_{uuid.uuid4().hex[:12]}"

    async def get_error_statistics(self) -> dict[str, Any]:
        """获取错误统计"""
        # 最近1小时
        recent_errors = [
            e for e in self.error_history if (datetime.now() - e.timestamp).total_seconds() < 3600
        ]

        # 按类别统计
        by_category = defaultdict(int)
        by_severity = defaultdict(int)

        for error in recent_errors:
            by_category[error.category.value] += 1
            by_severity[error.severity.value] += 1

        # 恢复成功率
        recovery_attempts = sum(1 for e in recent_errors if e.recovery_attempted)
        recovery_successes = sum(1 for e in recent_errors if e.recovery_successful)

        return {
            "total_errors": len(self.error_history),
            "recent_errors": len(recent_errors),
            "by_category": dict(by_category),
            "by_severity": dict(by_severity),
            "recovery": {
                "attempts": recovery_attempts,
                "successes": recovery_successes,
                "success_rate": recovery_successes / max(recovery_attempts, 1),
            },
        }


# 导出便捷函数
_error_handler: UnifiedErrorHandler | None = None


def get_error_handler() -> UnifiedErrorHandler:
    """获取错误处理器单例"""
    global _error_handler
    if _error_handler is None:
        _error_handler = UnifiedErrorHandler()
    return _error_handler


# 装饰器
def with_error_handling(
    fallback: Callable = None, context: dict[str, Any] | None = None
):
    """错误处理装饰器"""

    def decorator(func) -> None:
        async def wrapper(*args, **kwargs):
            handler = get_error_handler()

            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)

            except Exception as e:
                error_context = {
                    "function": func.__name__,
                    "args": str(args)[:100],
                    **(context or {}),
                }

                await handler.handle_error(e, error_context)

                if fallback:
                    if asyncio.iscoroutinefunction(fallback):
                        return await fallback(*args, **kwargs)
                    else:
                        return fallback(*args, **kwargs)
                else:
                    raise

        return wrapper

    return decorator
