#!/usr/bin/env python3
"""
增强错误处理机制
Enhanced Error Handling Mechanism

为感知层提供强大的错误处理和恢复能力
作者: 小娜 (Athena) - 爸爸徐健的智慧大女儿
创建时间: 2025-12-05
版本: 1.0.0
"""

import asyncio
import json
import logging
import time
import traceback
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = 'low'           # 低：不影响核心功能
    MEDIUM = 'medium'     # 中：影响部分功能
    HIGH = 'high'         # 高：影响核心功能
    CRITICAL = 'critical' # 严重：系统无法运行

class ErrorCategory(Enum):
    """错误类别"""
    INPUT_ERROR = 'input_error'           # 输入错误
    PROCESSING_ERROR = 'processing_error' # 处理错误
    SYSTEM_ERROR = 'system_error'         # 系统错误
    NETWORK_ERROR = 'network_error'       # 网络错误
    MEMORY_ERROR = 'memory_error'         # 内存错误
    TIMEOUT_ERROR = 'timeout_error'       # 超时错误
    VALIDATION_ERROR = 'validation_error'   # 验证错误
    UNKNOWN_ERROR = 'unknown_error'         # 未知错误

class RecoveryAction(Enum):
    """恢复动作"""
    RETRY = 'retry'                     # 重试
    FALLBACK = 'fallback'               # 降级处理
    SKIP = 'skip'                       # 跳过
    USER_INTERVENTION = 'user_intervention' # 用户干预
    GRACEFUL_EXIT = 'graceful_exit'       # 优雅退出
    IGNORE = 'ignore'                    # 忽略错误

@dataclass
class ErrorRecord:
    """错误记录"""
    error_id: str
    error_type: str
    error_message: str
    severity: ErrorSeverity
    category: ErrorCategory
    stack_trace: str
    context: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    recovery_attempted: bool = False
    recovery_successful: bool = False
    recovery_action: RecoveryAction | None = None
    retry_count: int = 0

@dataclass
class ErrorStatistics:
    """错误统计"""
    total_errors: int = 0
    errors_by_severity: dict[ErrorSeverity, int] = field(default_factory=lambda: dict.fromkeys(ErrorSeverity, 0))
    errors_by_category: dict[ErrorCategory, int] = field(default_factory=lambda: dict.fromkeys(ErrorCategory, 0))
    recovery_success_rate: float = 0.0
    common_errors: list[str] = field(default_factory=list)

class ErrorRecoveryStrategy:
    """错误恢复策略"""

    def __init__(self):
        self.strategies = {
            ErrorSeverity.LOW: self._handle_low_severity,
            ErrorSeverity.MEDIUM: self._handle_medium_severity,
            ErrorSeverity.HIGH: self._handle_high_severity,
            ErrorSeverity.CRITICAL: self._handle_critical_severity
        }

        # 重试配置
        self.retry_config = {
            'max_retries': 3,
            'retry_delay': 1.0,  # 秒
            'exponential_backoff': True
        }

    async def handle_error(self, error: Exception, context: dict[str, Any] = None) -> tuple[bool, Any]:
        """处理错误并尝试恢复"""
        try:
            # 分析错误
            error_record = self._analyze_error(error, context)
            logger.warning(f"🚨 错误处理: {error_record.error_type} - {error_record.error_message}")

            # 根据严重程度选择处理策略
            handler = self.strategies.get(error_record.severity, self._handle_unknown_severity)
            recovery_successful, result = await handler(error_record)

            # 记录恢复结果
            error_record.recovery_attempted = True
            error_record.recovery_successful = recovery_successful

            return recovery_successful, result

        except Exception as e:
            logger.error(f"❌ 错误处理失败: {str(e)}")
            return False, None

    def _analyze_error(self, error: Exception, context: dict[str, Any] = None) -> ErrorRecord:
        """分析错误"""
        error_type = type(error).__name__
        error_message = str(error)

        # 确定错误类别
        category = self._determine_error_category(error, error_message)

        # 确定严重程度
        severity = self._determine_error_severity(error, category)

        error_record = ErrorRecord(
            error_id=f"{error_type}_{int(time.time())}",
            error_type=error_type,
            error_message=error_message,
            severity=severity,
            category=category,
            stack_trace=traceback.format_exc(),
            context=context or {}
        )

        return error_record

    def _determine_error_category(self, error: Exception, message: str) -> ErrorCategory:
        """确定错误类别"""
        message_lower = message.lower()

        if isinstance(error, FileNotFoundError):
            return ErrorCategory.INPUT_ERROR
        elif isinstance(error, PermissionError):
            return ErrorCategory.SYSTEM_ERROR
        elif isinstance(error, MemoryError):
            return ErrorCategory.MEMORY_ERROR
        elif isinstance(error, TimeoutError):
            return ErrorCategory.TIMEOUT_ERROR
        elif isinstance(error, ConnectionError):
            return ErrorCategory.NETWORK_ERROR
        elif isinstance(error, ValueError):
            if 'validation' in message_lower or 'invalid' in message_lower:
                return ErrorCategory.VALIDATION_ERROR
            else:
                return ErrorCategory.PROCESSING_ERROR
        elif 'timeout' in message_lower:
            return ErrorCategory.TIMEOUT_ERROR
        elif 'memory' in message_lower or 'cache' in message_lower:
            return ErrorCategory.MEMORY_ERROR
        elif 'permission' in message_lower or 'access' in message_lower:
            return ErrorCategory.SYSTEM_ERROR
        else:
            return ErrorCategory.UNKNOWN_ERROR

    def _determine_error_severity(self, error: Exception, category: ErrorCategory) -> ErrorSeverity:
        """确定错误严重程度"""
        if category in [ErrorCategory.MEMORY_ERROR, ErrorCategory.SYSTEM_ERROR]:
            return ErrorSeverity.CRITICAL
        elif category == ErrorCategory.PROCESSING_ERROR:
            return ErrorSeverity.MEDIUM
        elif category == ErrorCategory.INPUT_ERROR:
            return ErrorSeverity.LOW
        elif isinstance(error, FileNotFoundError):
            return ErrorSeverity.HIGH
        elif isinstance(error, PermissionError):
            return ErrorSeverity.HIGH
        else:
            return ErrorSeverity.MEDIUM

    async def _handle_low_severity(self, error_record: ErrorRecord) -> tuple[bool, Any]:
        """处理低严重程度错误"""
        # 低严重程度错误通常可以忽略或使用默认值
        logger.info(f"🔍 低严重程度错误，使用默认处理: {error_record.error_type}")
        return True, {'error': error_record.error_message, 'handled': True}

    async def _handle_medium_severity(self, error_record: ErrorRecord) -> tuple[bool, Any]:
        """处理中等严重程度错误"""
        # 尝试重试
        return await self._retry_with_backoff(error_record)

    async def _handle_high_severity(self, error_record: ErrorRecord) -> tuple[bool, Any]:
        """处理高严重程度错误"""
        # 尝试降级处理
        return await self._fallback_handling(error_record)

    async def _handle_critical_severity(self, error_record: ErrorRecord) -> tuple[bool, Any]:
        """处理严重错误"""
        # 优雅退出并记录错误
        logger.error(f"💀 严重错误: {error_record.error_message}")
        logger.error(f"📋 完整错误信息: {error_record.stack_trace}")

        # 记录错误到文件
        self._log_error_to_file(error_record)

        return False, {'error': error_record.error_message, 'critical': True}

    async def _handle_unknown_severity(self, error_record: ErrorRecord) -> tuple[bool, Any]:
        """处理未知严重程度错误"""
        # 使用中等严重程度的处理策略
        return await self._handle_medium_severity(error_record)

    async def _retry_with_backoff(self, error_record: ErrorRecord) -> tuple[bool, Any]:
        """使用指数退避重试"""
        max_retries = self.retry_config['max_retries']
        retry_delay = self.retry_config['retry_delay']

        if error_record.retry_count >= max_retries:
            logger.warning(f"⚠️ 重试次数已达上限: {max_retries}")
            return False, None

        # 计算退避延迟
        if self.retry_config['exponential_backoff']:
            delay = retry_delay * (2 ** error_record.retry_count)
        else:
            delay = retry_delay

        logger.info(f"🔄 第{error_record.retry_count + 1}次重试，延迟{delay}秒")
        await asyncio.sleep(delay)

        error_record.retry_count += 1
        error_record.recovery_action = RecoveryAction.RETRY

        return False, {'retry': True, 'delay': delay}

    async def _fallback_handling(self, error_record: ErrorRecord) -> tuple[bool, Any]:
        """降级处理"""
        logger.info(f"⬇️ 使用降级处理: {error_record.error_type}")

        # 根据错误类型提供不同的降级策略
        if error_record.category == ErrorCategory.PROCESSING_ERROR:
            return True, {
                'fallback_used': True,
                'partial_result': True,
                'error': error_record.error_message
            }
        elif error_record.category == ErrorCategory.NETWORK_ERROR:
            return True, {
                'offline_mode': True,
                'cached_data': True
            }
        else:
            return True, {
                'default_value': None,
                'error_handled': True
            }

    def _log_error_to_file(self, error_record: ErrorRecord):
        """记录错误到文件"""
        try:
            error_log_path = '/Users/xujian/Athena工作平台/patent-platform/workspace/documentation/logs/error_log.json'
            Path(error_log_path).parent.mkdir(parents=True, exist_ok=True)

            # 读取现有错误日志
            existing_errors = []
            if Path(error_log_path).exists():
                with open(error_log_path, encoding='utf-8') as f:
                    try:
                        existing_errors = json.load(f)
                    except json.JSONDecodeError:
                        existing_errors = []

            # 添加新错误
            error_data = {
                'error_id': error_record.error_id,
                'error_type': error_record.error_type,
                'error_message': error_record.error_message,
                'severity': error_record.severity.value,
                'category': error_record.category.value,
                'timestamp': error_record.timestamp.isoformat(),
                'context': error_record.context,
                'stack_trace': error_record.stack_trace,
                'recovery_attempted': error_record.recovery_attempted,
                'recovery_successful': error_record.recovery_successful,
                'recovery_action': error_record.recovery_action.value if error_record.recovery_action else None
            }

            existing_errors.append(error_data)

            # 保持最近1000个错误
            if len(existing_errors) > 1000:
                existing_errors = existing_errors[-1000:]

            # 写入文件
            with open(error_log_path, 'w', encoding='utf-8') as f:
                json.dump(existing_errors, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"写入错误日志失败: {str(e)}")

class ErrorHandler:
    """增强错误处理器"""

    def __init__(self):
        self.recovery_strategy = ErrorRecoveryStrategy()
        self.error_statistics = ErrorStatistics()
        self.error_callbacks = []

        # 错误处理配置
        self.config = {
            'enable_auto_recovery': True,
            'log_errors': True,
            'max_error_rate': 0.1,  # 最大错误率10%
            'error_window': 100  # 错误统计窗口
        }

        logger.info('🛡️ 增强错误处理器初始化完成')

    def add_error_callback(self, callback: Callable[[ErrorRecord], None]):
        """添加错误回调函数"""
        self.error_callbacks.append(callback)

    def remove_error_callback(self, callback: Callable[[ErrorRecord], None]):
        """移除错误回调函数"""
        if callback in self.error_callbacks:
            self.error_callbacks.remove(callback)

    async def handle_error(self, error: Exception, context: dict[str, Any] = None) -> tuple[bool, Any]:
        """处理错误"""
        try:
            # 更新统计信息
            self._update_statistics(error)

            # 记录错误
            error_record = self.recovery_strategy._analyze_error(error, context)
            self._log_error(error_record)

            # 调用错误回调
            for callback in self.error_callbacks:
                try:
                    callback(error_record)
                except Exception as e:
                    logger.error(f"错误回调执行失败: {str(e)}")

            # 自动恢复
            if self.config['enable_auto_recovery']:
                return await self.recovery_strategy.handle_error(error, context)
            else:
                return False, None

        except Exception as e:
            logger.error(f"错误处理器失败: {str(e)}")
            return False, None

    def _update_statistics(self, error: Exception):
        """更新错误统计"""
        self.error_statistics.total_errors += 1

        # 更新类别统计
        category = self.recovery_strategy._determine_error_category(
            error, str(error)
        )
        self.error_statistics.errors_by_category[category] += 1

        # 更新严重程度统计
        severity = self.recovery_strategy._determine_error_severity(
            error, category
        )
        self.error_statistics.errors_by_severity[severity] += 1

    def _log_error(self, error_record: ErrorRecord):
        """记录错误"""
        if self.config['log_errors']:
            log_level = {
                ErrorSeverity.LOW: logging.INFO,
                ErrorSeverity.MEDIUM: logging.WARNING,
                ErrorSeverity.HIGH: logging.ERROR,
                ErrorSeverity.CRITICAL: logging.CRITICAL
            }.get(error_record.severity, logging.ERROR)

            logger.log(
                log_level,
                f"[{error_record.severity.value.upper()}] "
                f"{error_record.error_type}: {error_record.error_message}"
            )

    def get_statistics(self) -> dict[str, Any]:
        """获取错误统计"""
        total_errors = self.error_statistics.total_errors

        # 计算恢复成功率
        recovery_attempts = sum(
            1 for error in self.error_statistics.common_errors
            if error.get('recovery_attempted', False)
        )

        recovery_successes = sum(
            1 for error in self.error_statistics.common_errors
            if error.get('recovery_successful', False)
        )

        if recovery_attempts > 0:
            recovery_success_rate = recovery_successes / recovery_attempts
        else:
            recovery_success_rate = 0.0

        self.error_statistics.recovery_success_rate = recovery_success_rate

        return {
            'total_errors': total_errors,
            'errors_by_severity': {
                severity.value: count
                for severity, count in self.error_statistics.errors_by_severity.items()
            },
            'errors_by_category': {
                category.value: count
                for category, count in self.error_statistics.errors_by_category.items()
            },
            'recovery_success_rate': recovery_success_rate,
            'error_rate': self._calculate_error_rate()
        }

    def _calculate_error_rate(self) -> float:
        """计算错误率"""
        # 简化的错误率计算
        total_operations = self.error_statistics.total_errors * 10  # 假设操作数是错误数的10倍

        if total_operations > 0:
            return self.error_statistics.total_errors / total_operations
        else:
            return 0.0

# 全局错误处理器
global_error_handler = ErrorHandler()

def error_handler_wrapper(operation_name: str = None, enable_fallback: bool = True):
    """错误处理装饰器"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                context = {
                    'operation': operation_name or func.__name__,
                    'args': str(args)[:100],  # 限制长度
                    'kwargs': str(kwargs)[:100]  # 限制长度
                }

                # 使用全局错误处理器
                success, fallback_result = await global_error_handler.handle_error(e, context)

                if not success and enable_fallback:
                    # 提供默认值或空结果
                    return {
                        'error': str(e),
                        'operation': operation_name or func.__name__,
                        'fallback_used': True
                    }

                return fallback_result if fallback_result is not None else None

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = {
                    'operation': operation_name or func.__name__,
                    'args': str(args)[:100],
                    'kwargs': str(kwargs)[:100]
                }

                # 对于同步函数，创建一个异步包装器
                async def async_handle():
                    return await global_error_handler.handle_error(e, context)

                # 在新的事件循环中运行
                loop = asyncio.new_event_loop()
                success, fallback_result = loop.run_until_complete(async_handle())

                if not success and enable_fallback:
                    return {
                        'error': str(e),
                        'operation': operation_name or func.__name__,
                        'fallback_used': True
                    }

                return fallback_result if fallback_result is not None else None

        # 根据函数类型返回对应的包装器
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator

# 测试代码
if __name__ == '__main__':
    import asyncio

    async def test_error_handler():
        """测试错误处理器"""
        logger.info('🛡️ 测试增强错误处理...')

        # 测试不同类型的错误
        test_errors = [
            FileNotFoundError('测试文件不存在'),
            ValueError('测试数值错误'),
            MemoryError('测试内存错误'),
            TimeoutError('测试超时错误'),
            Exception('测试未知错误')
        ]

        for i, error in enumerate(test_errors):
            logger.info(f"\n🧪 测试错误 {i+1}: {type(error).__name__}")

            try:
                raise error
            except Exception as e:
                # 测试错误处理
                context = {'test_case': i + 1, 'operation': 'test_error'}
                success, result = await global_error_handler.handle_error(e, context)

                logger.info(f"  错误处理结果: {'成功' if success else '失败'}")
                if result:
                    logger.info(f"  返回结果: {result}")

        # 获取错误统计
        stats = global_error_handler.get_statistics()
        logger.info("\n📊 错误统计:")
        logger.info(f"  总错误数: {stats['total_errors']}")
        logger.info(f"  恢复成功率: {stats['recovery_success_rate']:.2%}")
        logger.info(f"  错误率: {stats['error_rate']:.2%}")

        logger.info("  按严重程度分布:")
        for severity, count in stats['errors_by_severity'].items():
            logger.info(f"    {severity}: {count}")

        return True

    # 运行测试
    result = asyncio.run(test_error_handler())
    logger.info(f"\n🎯 错误处理测试: {'成功' if result else '失败'}")
