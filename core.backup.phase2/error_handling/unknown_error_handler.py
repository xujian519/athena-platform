#!/usr/bin/env python3
from __future__ import annotations
"""
未知错误处理器
Unknown Error Handler

智能识别和处理未知类型的错误
通过错误模式分析和自动恢复策略提高系统韧性
"""

import asyncio
import hashlib
import inspect
import logging
import re
import traceback
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """错误类别枚举"""

    NETWORK = "network"  # 网络错误
    DATABASE = "database"  # 数据库错误
    EXTERNAL_API = "external_api"  # 外部API错误
    VALIDATION = "validation"  # 验证错误
    RESOURCE = "resource"  # 资源错误
    LOGIC = "logic"  # 逻辑错误
    UNKNOWN = "unknown"  # 未知错误


class ErrorSeverity(Enum):
    """错误严重程度"""

    LOW = "low"  # 低
    MEDIUM = "medium"  # 中
    HIGH = "high"  # 高
    CRITICAL = "critical"  # 严重


class RecoveryActionType(Enum):
    """恢复动作类型"""

    RETRY = "retry"  # 重试
    SKIP = "skip"  # 跳过
    FALLBACK = "fallback"  # 降级
    LOG_ONLY = "log_only"  # 仅记录
    ESCALATE = "escalate"  # 升级


@dataclass
class ErrorPattern:
    """错误模式"""

    pattern_id: str
    name: str
    category: ErrorCategory
    severity: ErrorSeverity
    patterns: list[str]  # 匹配模式(正则或字符串)
    recovery_actions: list[RecoveryActionType]
    occurrences: int = 0  # 出现次数
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    recovery_success_rate: float = 0.0


@dataclass
class ErrorInstance:
    """错误实例"""

    error_id: str
    pattern_id: str  # 关联的模式ID
    category: ErrorCategory
    severity: ErrorSeverity
    error_type: str  # 错误类型
    error_message: str  # 错误消息
    stack_trace: str  # 堆栈跟踪
    context: dict[str, Any]  # 上下文信息
    timestamp: datetime
    recovered: bool = False  # 是否已恢复
    recovery_action: RecoveryActionType | None = None
    recovery_duration: float = 0.0  # 恢复耗时(秒)


@dataclass
class RecoveryResult:
    """恢复结果"""

    success: bool
    action_taken: RecoveryActionType
    message: str
    duration: float = 0.0
    fallback_value: Any = None


class UnknownErrorHandler:
    """
    未知错误处理器

    核心功能:
    1. 错误模式学习和识别
    2. 自动分类和严重程度评估
    3. 智能恢复策略选择
    4. 错误统计和分析
    """

    def __init__(self):
        """初始化错误处理器"""
        self.name = "未知错误处理器 v1.0"
        self.version = "1.0.0"

        # 错误模式库
        self.error_patterns: dict[str, ErrorPattern] = {}

        # 错误实例历史
        self.error_history: list[ErrorInstance] = []
        self.max_history_size = 10000

        # 统计信息
        self.stats = {
            "total_errors": 0,
            "categorized_errors": 0,
            "unknown_errors": 0,
            "recovered_errors": 0,
            "recovery_success_rate": 0.0,
            "errors_by_category": {},
            "errors_by_severity": {},
        }

        # 恢复处理器
        self.recovery_handlers: dict[RecoveryActionType, Callable] = {
            RecoveryActionType.RETRY: self._retry_recovery,
            RecoveryActionType.SKIP: self._skip_recovery,
            RecoveryActionType.FALLBACK: self._fallback_recovery,
            RecoveryActionType.LOG_ONLY: self._log_only_recovery,
            RecoveryActionType.ESCALATE: self._escalate_recovery,
        }

        # 初始化默认错误模式
        self._initialize_default_patterns()

    def _initialize_default_patterns(self) -> Any:
        """初始化默认错误模式"""
        # 网络错误模式
        self.register_pattern(
            ErrorPattern(
                pattern_id="network_timeout",
                name="网络超时",
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                patterns=[r"timeout", r"timed out", r"连接超时", r"Connection timed out"],
                recovery_actions=[RecoveryActionType.RETRY, RecoveryActionType.FALLBACK],
            )
        )

        self.register_pattern(
            ErrorPattern(
                pattern_id="network_refused",
                name="连接被拒绝",
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.HIGH,
                patterns=[r"connection refused", r"连接被拒绝", r"Connection refused"],
                recovery_actions=[RecoveryActionType.RETRY, RecoveryActionType.ESCALATE],
            )
        )

        # 数据库错误模式
        self.register_pattern(
            ErrorPattern(
                pattern_id="db_connection",
                name="数据库连接错误",
                category=ErrorCategory.DATABASE,
                severity=ErrorSeverity.HIGH,
                patterns=[
                    r"database.*error",
                    r"数据库.*错误",
                    r"SQL error",
                    r"ORA-",
                    r"MySQL error",
                ],
                recovery_actions=[RecoveryActionType.RETRY, RecoveryActionType.FALLBACK],
            )
        )

        self.register_pattern(
            ErrorPattern(
                pattern_id="db_constraint",
                name="数据库约束错误",
                category=ErrorCategory.DATABASE,
                severity=ErrorSeverity.MEDIUM,
                patterns=[r"constraint.*violat", r"unique.*constraint", r"foreign.*key"],
                recovery_actions=[RecoveryActionType.LOG_ONLY],
            )
        )

        # 外部API错误
        self.register_pattern(
            ErrorPattern(
                pattern_id="api_unavailable",
                name="外部API不可用",
                category=ErrorCategory.EXTERNAL_API,
                severity=ErrorSeverity.HIGH,
                patterns=[r"service unavailable", r"503", r"502", r"API.*error"],
                recovery_actions=[RecoveryActionType.RETRY, RecoveryActionType.FALLBACK],
            )
        )

        # 验证错误
        self.register_pattern(
            ErrorPattern(
                pattern_id="validation_error",
                name="验证错误",
                category=ErrorCategory.VALIDATION,
                severity=ErrorSeverity.LOW,
                patterns=[r"validation.*error", r"invalid.*value", r"验证.*失败", r"ValueError"],
                recovery_actions=[RecoveryActionType.LOG_ONLY],
            )
        )

        # 资源错误
        self.register_pattern(
            ErrorPattern(
                pattern_id="resource_exhausted",
                name="资源耗尽",
                category=ErrorCategory.RESOURCE,
                severity=ErrorSeverity.CRITICAL,
                patterns=[r"out of memory", r"memory.*error", r"disk.*full", r"resource.*exhaust"],
                recovery_actions=[RecoveryActionType.ESCALATE, RecoveryActionType.FALLBACK],
            )
        )

    def register_pattern(self, pattern: ErrorPattern) -> Any:
        """
        注册错误模式

        Args:
            pattern: 错误模式
        """
        self.error_patterns[pattern.pattern_id] = pattern
        logger.debug(f"注册错误模式: {pattern.pattern_id} - {pattern.name}")

    def handle_error(
        self, error: Exception, context: dict[str, Any] | None = None
    ) -> RecoveryResult:
        """
        处理错误

        Args:
            error: 异常对象
            context: 上下文信息

        Returns:
            RecoveryResult: 恢复结果
        """
        context = context or {}
        start_time = datetime.now()

        # 提取错误信息
        error_type = type(error).__name__
        error_message = str(error)
        stack_trace = traceback.format_exc()

        # 识别错误模式
        pattern_id = self._identify_pattern(error_type, error_message, stack_trace)

        # 确定错误类别和严重程度
        category, severity = self._categorize_error(error, pattern_id)

        # 创建错误实例
        error_id = self._generate_error_id(error_type, error_message)
        error_instance = ErrorInstance(
            error_id=error_id,
            pattern_id=pattern_id,
            category=category,
            severity=severity,
            error_type=error_type,
            error_message=error_message,
            stack_trace=stack_trace,
            context=context,
            timestamp=datetime.now(),
        )

        # 更新模式统计
        if pattern_id and pattern_id in self.error_patterns:
            pattern = self.error_patterns[pattern_id]
            pattern.occurrences += 1
            if pattern.first_seen is None:
                pattern.first_seen = datetime.now()
            pattern.last_seen = datetime.now()

        # 添加到历史
        self._add_to_history(error_instance)

        # 更新统计
        self.stats["total_errors"] += 1
        self.stats["errors_by_category"][category.value] = (
            self.stats["errors_by_category"].get(category.value, 0) + 1
        )
        self.stats["errors_by_severity"][severity.value] = (
            self.stats["errors_by_severity"].get(severity.value, 0) + 1
        )

        if pattern_id:
            self.stats["categorized_errors"] += 1
        else:
            self.stats["unknown_errors"] += 1

        # 选择恢复动作
        recovery_action = self._select_recovery_action(error_instance, pattern_id)

        # 执行恢复
        recovery_result = self._execute_recovery(error_instance, recovery_action)

        # 更新错误实例
        error_instance.recovered = recovery_result.success
        error_instance.recovery_action = recovery_result.action_taken
        error_instance.recovery_duration = (datetime.now() - start_time).total_seconds()

        if recovery_result.success:
            self.stats["recovered_errors"] += 1

        # 更新恢复成功率
        self._update_recovery_stats()

        # 记录错误
        self._log_error(error_instance, recovery_result)

        return recovery_result

    def _identify_pattern(
        self, error_type: str, error_message: str, stack_trace: str
    ) -> str | None:
        """识别错误模式"""
        # 组合所有文本
        combined_text = f"{error_type} {error_message} {stack_trace}".lower()

        # 尝试匹配所有模式
        for pattern_id, pattern in self.error_patterns.items():
            for pattern_str in pattern.patterns:
                if pattern_str.lower() in combined_text:
                    return pattern_id

                # 尝试正则匹配
                try:
                    if re.search(pattern_str, combined_text, re.IGNORECASE):
                        return pattern_id
                except re.error:
                    pass

        return None

    def _categorize_error(
        self, error: Exception, pattern_id: str,
    ) -> tuple[ErrorCategory, ErrorSeverity]:
        """对错误进行分类和评估严重程度"""
        # 如果有匹配的模式,使用模式的分类
        if pattern_id and pattern_id in self.error_patterns:
            pattern = self.error_patterns[pattern_id]
            return pattern.category, pattern.severity

        # 根据错误类型推断
        error_type = type(error).__name__

        # 网络相关错误
        if error_type in ["ConnectionError", "TimeoutError", "ConnectTimeout"]:
            return ErrorCategory.NETWORK, ErrorSeverity.MEDIUM

        # 数据库相关错误
        if "database" in error_type.lower() or "sql" in error_type.lower():
            return ErrorCategory.DATABASE, ErrorSeverity.HIGH

        # 验证错误
        if error_type in ["ValueError", "TypeError", "ValidationError"]:
            return ErrorCategory.VALIDATION, ErrorSeverity.LOW

        # 资源错误
        if error_type in ["MemoryError", "ResourceExhausted"]:
            return ErrorCategory.RESOURCE, ErrorSeverity.CRITICAL

        # 默认未知错误
        return ErrorCategory.UNKNOWN, ErrorSeverity.MEDIUM

    def _select_recovery_action(
        self, error_instance: ErrorInstance, pattern_id: str,
    ) -> RecoveryActionType:
        """选择恢复动作"""
        # 如果有模式匹配,使用模式推荐的恢复动作
        if pattern_id and pattern_id in self.error_patterns:
            pattern = self.error_patterns[pattern_id]
            if pattern.recovery_actions:
                # 选择成功率最高的恢复动作
                return pattern.recovery_actions[0]

        # 根据严重程度选择
        if error_instance.severity == ErrorSeverity.CRITICAL:
            return RecoveryActionType.ESCALATE
        elif error_instance.severity == ErrorSeverity.HIGH:
            return RecoveryActionType.RETRY
        else:
            return RecoveryActionType.LOG_ONLY

    def _execute_recovery(
        self, error_instance: ErrorInstance, action: RecoveryActionType
    ) -> RecoveryResult:
        """执行恢复动作"""
        if action in self.recovery_handlers:
            try:
                return self.recovery_handlers[action](error_instance)
            except Exception as e:
                logger.error(f"恢复动作执行失败: {e}")
                return RecoveryResult(
                    success=False, action_taken=action, message=f"恢复执行异常: {e}"
                )

        return RecoveryResult(success=False, action_taken=None, message="没有可用的恢复处理器")

    def _retry_recovery(self, error_instance: ErrorInstance) -> RecoveryResult:
        """重试恢复"""
        return RecoveryResult(
            success=False,
            action_taken=RecoveryActionType.RETRY,
            message="建议重试操作",
        )

    def _skip_recovery(self, error_instance: ErrorInstance) -> RecoveryResult:
        """跳过恢复"""
        return RecoveryResult(
            success=True, action_taken=RecoveryActionType.SKIP, message="已跳过错误操作"
        )

    def _fallback_recovery(self, error_instance: ErrorInstance) -> RecoveryResult:
        """降级恢复"""
        return RecoveryResult(
            success=True,
            action_taken=RecoveryActionType.FALLBACK,
            message="已使用降级方案",
            fallback_value=None,
        )

    def _log_only_recovery(self, error_instance: ErrorInstance) -> RecoveryResult:
        """仅记录"""
        return RecoveryResult(
            success=True, action_taken=RecoveryActionType.LOG_ONLY, message="错误已记录"
        )

    def _escalate_recovery(self, error_instance: ErrorInstance) -> RecoveryResult:
        """升级处理"""
        return RecoveryResult(
            success=False,
            action_taken=RecoveryActionType.ESCALATE,
            message="错误已升级,需要人工处理",
        )

    def _generate_error_id(self, error_type: str, error_message: str) -> str:
        """生成错误ID"""
        content = f"{error_type}:{error_message}:{datetime.now().isoformat()}"
        return hashlib.md5(content.encode('utf-8'), usedforsecurity=False).hexdigest()[:16]

    def _add_to_history(self, error_instance: ErrorInstance) -> Any:
        """添加到历史记录"""
        self.error_history.append(error_instance)

        # 限制历史大小
        if len(self.error_history) > self.max_history_size:
            self.error_history = self.error_history[-self.max_history_size :]

    def _update_recovery_stats(self) -> Any:
        """更新恢复统计"""
        total = self.stats["total_errors"]
        recovered = self.stats["recovered_errors"]
        self.stats["recovery_success_rate"] = recovered / total if total > 0 else 0

    def _log_error(self, error_instance: ErrorInstance, result: RecoveryResult) -> Any:
        """记录错误"""
        log_level = logging.ERROR

        if error_instance.severity == ErrorSeverity.CRITICAL:
            log_level = logging.CRITICAL
        elif error_instance.severity == ErrorSeverity.LOW:
            log_level = logging.WARNING

        logger.log(
            log_level,
            f"[{error_instance.error_id}] {error_instance.category.value} - "
            f"{error_instance.error_type}: {error_instance.error_message}",
            extra={
                "error_id": error_instance.error_id,
                "category": error_instance.category.value,
                "severity": error_instance.severity.value,
                "recovered": error_instance.recovered,
                "recovery_action": result.action_taken.value if result.action_taken else None,
            },
        )

    def get_error_stats(self) -> dict[str, Any]:
        """获取错误统计"""
        return self.stats.copy()

    def get_error_patterns(self) -> dict[str, ErrorPattern]:
        """获取所有错误模式"""
        return self.error_patterns.copy()

    def get_recent_errors(
        self, category: ErrorCategory | None = None, limit: int = 100
    ) -> list[ErrorInstance]:
        """
        获取最近的错误

        Args:
            category: 错误类别(可选)
            limit: 返回数量限制

        Returns:
            错误实例列表
        """
        errors = self.error_history

        if category:
            errors = [e for e in errors if e.category == category]

        return errors[-limit:]

    def learn_from_error(self, error_instance: ErrorInstance) -> Any:
        """
        从错误中学习

        Args:
            error_instance: 错误实例
        """
        # 如果是未知错误且出现多次,创建新模式
        if error_instance.pattern_id is None and error_instance.category == ErrorCategory.UNKNOWN:

            # 统计相同错误类型的出现次数
            similar_errors = [
                e for e in self.error_history if e.error_type == error_instance.error_type
            ]

            if len(similar_errors) >= 3:
                # 创建新的错误模式
                pattern_id = f"auto_{error_instance.error_type.lower()}_{len(similar_errors)}"

                self.register_pattern(
                    ErrorPattern(
                        pattern_id=pattern_id,
                        name=f"自动学习: {error_instance.error_type}",
                        category=error_instance.category,
                        severity=error_instance.severity,
                        patterns=[error_instance.error_type],
                        recovery_actions=[RecoveryActionType.LOG_ONLY],
                    )
                )

                logger.info(f"从错误中学习新模式: {pattern_id}")


def error_handler(fallback_value: Any = None, escalate: bool = False):
    """
    错误处理装饰器

    Args:
        fallback_value: 降级返回值
        escalate: 是否升级严重错误
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                handler = get_unknown_error_handler()
                result = handler.handle_error(
                    e, context={"function": func.__name__, "args": str(args)[:200]}
                )

                if result.success and result.fallback_value is not None:
                    return result.fallback_value
                elif not result.success and escalate:
                    raise
                elif fallback_value is not None:
                    return fallback_value
                else:
                    raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handler = get_unknown_error_handler()
                result = handler.handle_error(
                    e, context={"function": func.__name__, "args": str(args)[:200]}
                )

                if result.success and result.fallback_value is not None:
                    return result.fallback_value
                elif not result.success and escalate:
                    raise
                elif fallback_value is not None:
                    return fallback_value
                else:
                    raise

        # 根据函数类型返回对应的wrapper
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# 单例实例
_handler_instance: UnknownErrorHandler | None = None


def get_unknown_error_handler() -> UnknownErrorHandler:
    """获取未知错误处理器单例"""
    global _handler_instance
    if _handler_instance is None:
        _handler_instance = UnknownErrorHandler()
        logger.info("未知错误处理器已初始化")
    return _handler_instance


async def main():
    """测试主函数"""
    handler = get_unknown_error_handler()

    print("=== 未知错误处理测试 ===\n")

    # 测试1: 网络超时错误
    print("测试1: 网络超时错误")
    try:
        raise asyncio.TimeoutError("Connection timed out after 30 seconds")
    except Exception as e:
        result = handler.handle_error(e, {"test": "network_timeout"})
        print(f"  识别模式: {result.message}")
        print(f"  恢复成功: {result.success}")

    # 测试2: 验证错误
    print("\n测试2: 验证错误")
    try:
        raise ValueError("Invalid parameter value")
    except Exception as e:
        result = handler.handle_error(e, {"test": "validation"})
        print(f"  识别模式: {result.message}")
        print(f"  恢复动作: {result.action_taken}")

    # 测试3: 未知错误
    print("\n测试3: 未知错误")
    try:
        raise RuntimeError("Unexpected error occurred")
    except Exception as e:
        result = handler.handle_error(e, {"test": "unknown"})
        print(f"  识别模式: {result.message}")
        print(f"  恢复成功: {result.success}")

    # 显示统计
    stats = handler.get_error_stats()
    print("\n=== 统计信息 ===")
    print(f"总错误数: {stats['total_errors']}")
    print(f"已分类错误: {stats['categorized_errors']}")
    print(f"未知错误: {stats['unknown_errors']}")
    print(f"恢复成功率: {stats['recovery_success_rate']:.1%}")


# 入口点: @async_main装饰器已添加到main函数
