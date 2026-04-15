#!/usr/bin/env python3
"""
可靠性增强组件
Reliability Enhancement Components

功能特性：
- 重试机制（指数退避）
- 熔断器（自动降级）
- 死信队列（失败任务处理）
- 可靠性监控

Created by Athena AI系统
Date: 2025-12-14
Version: 1.0.0
"""

import asyncio
import functools
import logging
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')


# =============================================================================
# 重试机制
# =============================================================================

@dataclass
class RetryConfig:
    """重试配置"""
    max_attempts: int = 3           # 最大重试次数
    base_delay: float = 1.0         # 基础延迟（秒）
    max_delay: float = 60.0         # 最大延迟（秒）
    exponential_base: float = 2.0   # 指数退避基数
    jitter: bool = True             # 是否添加随机抖动
    retriable_exceptions: tuple = (Exception,)  # 可重试的异常类型


class RetryStats:
    """重试统计"""
    def __init__(self):
        self.total_attempts = 0
        self.successful_attempts = 0
        self.failed_attempts = 0
        self.retry_count = 0
        self.exceptions: dict[str, int] = {}


class RetryManager:
    """重试管理器"""

    def __init__(self, config: RetryConfig | None = None):
        """
        初始化重试管理器

        Args:
            config: 重试配置
        """
        self.config = config or RetryConfig()
        self.stats = RetryStats()
        self.logger = logging.getLogger(f"{__name__}.RetryManager")

    async def execute(self,
                     func: Callable,
                     *args,
                     context: dict[str, Any] | None = None,
                     **kwargs) -> Any:
        """
        执行带重试的函数

        Args:
            func: 要执行的函数
            *args: 函数参数
            context: 上下文信息
            **kwargs: 函数关键字参数

        Returns:
            函数执行结果
        """
        context = context or {}
        last_exception = None

        for attempt in range(1, self.config.max_attempts + 1):
            try:
                self.stats.total_attempts += 1

                # 执行函数
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                # 成功执行
                self.stats.successful_attempts += 1
                if attempt > 1:
                    self.logger.info(
                        f"✅ 重试成功 (第{attempt}次尝试) "
                        f"[{context.get('operation_name', 'unknown')}]"
                    )
                return result

            except Exception as e:
                last_exception = e
                exc_type = type(e).__name__
                self.stats.exceptions[exc_type] = self.stats.exceptions.get(exc_type, 0) + 1

                # 检查是否可重试
                if not isinstance(e, self.config.retriable_exceptions):
                    self.logger.error(f"❌ 不可重试的异常: {exc_type}: {e}")
                    self.stats.failed_attempts += 1
                    raise

                # 检查是否还有重试机会
                if attempt >= self.config.max_attempts:
                    self.logger.error(
                        f"❌ 重试失败 (已达到最大重试次数: {self.config.max_attempts}) "
                        f"[{context.get('operation_name', 'unknown')}]"
                    )
                    self.stats.failed_attempts += 1
                    self.stats.retry_count += attempt - 1
                    raise

                # 计算延迟时间
                delay = self._calculate_delay(attempt)
                self.stats.retry_count += 1

                self.logger.warning(
                    f"⚠️ 执行失败 (第{attempt}次尝试)，"
                    f"{delay:.2f}秒后重试... "
                    f"[{context.get('operation_name', 'unknown')}]"
                    f"错误: {exc_type}: {str(e)[:100]}"
                )

                # 等待后重试
                await asyncio.sleep(delay)

        # 理论上不会到达这里
        if last_exception:
            raise last_exception

    def _calculate_delay(self, attempt: int) -> float:
        """
        计算重试延迟（指数退避 + 抖动）

        Args:
            attempt: 当前尝试次数

        Returns:
            延迟时间（秒）
        """
        # 指数退避
        delay = min(
            self.config.base_delay * (self.config.exponential_base ** (attempt - 1)),
            self.config.max_delay
        )

        # 添加随机抖动（避免雷群效应）
        if self.config.jitter:
            import random
            delay = delay * (0.5 + random.random() * 0.5)

        return delay

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            'total_attempts': self.stats.total_attempts,
            'successful_attempts': self.stats.successful_attempts,
            'failed_attempts': self.stats.failed_attempts,
            'retry_count': self.stats.retry_count,
            'exceptions': self.stats.exceptions.copy(),
            'success_rate': (
                self.stats.successful_attempts / self.stats.total_attempts
                if self.stats.total_attempts > 0 else 0
            )
        }


def with_retry(config: RetryConfig | None = None):
    """
    重试装饰器

    Args:
        config: 重试配置

    Returns:
        装饰器函数
    """
    retry_manager = RetryManager(config)

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            context = kwargs.pop('retry_context', None)
            return await retry_manager.execute(
                func, *args, context=context, **kwargs
            )

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 同步函数的重试支持
            import asyncio
            context = kwargs.pop('retry_context', None)
            return asyncio.run(retry_manager.execute(
                func, *args, context=context, **kwargs
            ))

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# =============================================================================
# 熔断器
# =============================================================================

class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = "closed"       # 关闭（正常）
    OPEN = "open"           # 打开（熔断）
    HALF_OPEN = "half_open" # 半开（试探）


@dataclass
class CircuitBreakerConfig:
    """熔断器配置"""
    failure_threshold: int = 5      # 失败阈值
    success_threshold: int = 2      # 成功阈值（半开状态）
    timeout: float = 60.0           # 熔断超时（秒）
    window_size: int = 100          # 滑动窗口大小
    min_calls: int = 10             # 最小调用数


class CircuitBreaker:
    """熔断器"""

    def __init__(self,
                 name: str,
                 config: CircuitBreakerConfig | None = None):
        """
        初始化熔断器

        Args:
            name: 熔断器名称
            config: 熔断器配置
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.logger = logging.getLogger(f"{__name__}.CircuitBreaker.{name}")

        # 状态
        self._state = CircuitState.CLOSED
        self._state_changed_at = time.time()

        # 统计
        self._failure_count = 0
        self._success_count = 0
        self._call_history: deque = deque(maxlen=self.config.window_size)

        # 同步锁
        self._lock = asyncio.Lock()

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        通过熔断器调用函数

        Args:
            func: 要调用的函数
            *args: 函数参数
            **kwargs: 函数关键字参数

        Returns:
            函数执行结果

        Raises:
            CircuitBreakerOpenError: 熔断器打开时
        """
        async with self._lock:
            # 检查是否应该尝试恢复
            if self._state == CircuitState.OPEN:
                if time.time() - self._state_changed_at >= self.config.timeout:
                    self._transition_to_half_open()
                    self.logger.info(f"🔄 熔断器进入半开状态: {self.name}")
                else:
                    raise CircuitBreakerOpenError(
                        f"熔断器已打开: {self.name}，"
                        f"剩余冷却时间: {self._get_remaining_cooldown():.1f}秒"
                    )

        try:
            # 执行函数
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # 记录成功
            await self._record_success()

            return result

        except Exception:
            # 记录失败
            await self._record_failure()
            raise

    async def _record_success(self):
        """记录成功调用"""
        async with self._lock:
            self._success_count += 1
            self._call_history.append(True)

            # 半开状态下的成功处理
            if self._state == CircuitState.HALF_OPEN:
                if self._success_count >= self.config.success_threshold:
                    self._transition_to_closed()
                    self.logger.info(f"✅ 熔断器已恢复: {self.name}")

    async def _record_failure(self):
        """记录失败调用"""
        async with self._lock:
            self._failure_count += 1
            self._call_history.append(False)

            # 检查是否应该打开熔断器
            if len(self._call_history) >= self.config.min_calls:
                recent_failures = sum(1 for x in self._call_history if not x)
                failure_rate = recent_failures / len(self._call_history)

                if failure_rate >= 0.5 or recent_failures >= self.config.failure_threshold:
                    if self._state != CircuitState.OPEN:
                        self._transition_to_open()
                        self.logger.error(
                            f"⚠️ 熔断器已打开: {self.name} "
                            f"(失败率: {failure_rate:.1%}, 失败数: {recent_failures})"
                        )

    def _transition_to_open(self):
        """转换到打开状态"""
        self._state = CircuitState.OPEN
        self._state_changed_at = time.time()
        self._failure_count = 0
        self._success_count = 0

    def _transition_to_half_open(self):
        """转换到半开状态"""
        self._state = CircuitState.HALF_OPEN
        self._state_changed_at = time.time()
        self._failure_count = 0
        self._success_count = 0

    def _transition_to_closed(self):
        """转换到关闭状态"""
        self._state = CircuitState.CLOSED
        self._state_changed_at = time.time()
        self._failure_count = 0
        self._success_count = 0
        self._call_history.clear()

    def _get_remaining_cooldown(self) -> float:
        """获取剩余冷却时间"""
        elapsed = time.time() - self._state_changed_at
        return max(0, self.config.timeout - elapsed)

    def get_state(self) -> CircuitState:
        """获取当前状态"""
        return self._state

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            'name': self.name,
            'state': self._state.value,
            'failure_count': self._failure_count,
            'success_count': self._success_count,
            'call_history_size': len(self._call_history),
            'recent_failures': sum(1 for x in self._call_history if not x),
            'remaining_cooldown': (
                self._get_remaining_cooldown()
                if self._state == CircuitState.OPEN else 0
            )
        }


class CircuitBreakerOpenError(Exception):
    """熔断器打开异常"""
    pass


# =============================================================================
# 死信队列
# =============================================================================

@dataclass
class FailedTask:
    """失败任务"""
    task_id: str
    task_type: str
    parameters: dict[str, Any]
    exception: str
    attempts: int = 0
    max_attempts: int = 3
    created_at: float = field(default_factory=time.time)
    last_attempt: float = field(default_factory=time.time)


class DeadLetterQueue:
    """死信队列"""

    def __init__(self, max_size: int = 1000):
        """
        初始化死信队列

        Args:
            max_size: 队列最大大小
        """
        self.max_size = max_size
        self._queue: deque = deque()
        self._lock = asyncio.Lock()
        self.logger = logging.getLogger(f"{__name__}.DeadLetterQueue")

    async def add(self,
                  task_id: str,
                  task_type: str,
                  parameters: dict[str, Any],
                  exception: Exception,
                  max_attempts: int = 3):
        """
        添加失败任务到队列

        Args:
            task_id: 任务ID
            task_type: 任务类型
            parameters: 任务参数
            exception: 异常对象
            max_attempts: 最大重试次数
        """
        async with self._lock:
            if len(self._queue) >= self.max_size:
                self.logger.warning(f"⚠️ 死信队列已满，丢弃任务: {task_id}")
                return False

            failed_task = FailedTask(
                task_id=task_id,
                task_type=task_type,
                parameters=parameters,
                exception=str(exception),
                max_attempts=max_attempts
            )

            self._queue.append(failed_task)
            self.logger.info(f"📬 任务已加入死信队列: {task_id} (队列大小: {len(self._queue)})")
            return True

    async def get(self) -> FailedTask | None:
        """
        从队列获取任务

        Returns:
            失败任务，队列为空时返回None
        """
        async with self._lock:
            if not self._queue:
                return None
            return self._queue.popleft()

    async def size(self) -> int:
        """获取队列大小"""
        async with self._lock:
            return len(self._queue)

    async def clear(self):
        """清空队列"""
        async with self._lock:
            self._queue.clear()
            self.logger.info("🗑️ 死信队列已清空")


# =============================================================================
# 可靠性管理器
# =============================================================================

class ReliabilityManager:
    """可靠性管理器（整合所有组件）"""

    def __init__(self):
        """初始化可靠性管理器"""
        self.logger = logging.getLogger(f"{__name__}.ReliabilityManager")

        # 重试管理器
        self.retry_manager = RetryManager()

        # 熔断器集合
        self.circuit_breakers: dict[str, CircuitBreaker] = {}

        # 死信队列
        self.dead_letter_queue = DeadLetterQueue()

        # 统计
        self.stats = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'retried_calls': 0,
            'circuit_breaker_trips': 0
        }

    def get_circuit_breaker(self,
                           name: str,
                           config: CircuitBreakerConfig | None = None) -> CircuitBreaker:
        """
        获取或创建熔断器

        Args:
            name: 熔断器名称
            config: 熔断器配置

        Returns:
            熔断器实例
        """
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(name, config)
            self.logger.info(f"✅ 创建熔断器: {name}")
        return self.circuit_breakers[name]

    async def execute_with_reliability(self,
                                     operation_name: str,
                                     func: Callable,
                                     *args,
                                     use_retry: bool = True,
                                     use_circuit_breaker: bool = True,
                                     **kwargs) -> Any:
        """
        执行带可靠性保障的操作

        Args:
            operation_name: 操作名称
            func: 要执行的函数
            *args: 函数参数
            use_retry: 是否使用重试
            use_circuit_breaker: 是否使用熔断器
            **kwargs: 函数关键字参数

        Returns:
            函数执行结果
        """
        self.stats['total_calls'] += 1

        # 熔断器保护
        if use_circuit_breaker:
            cb = self.get_circuit_breaker(operation_name)
        else:
            cb = None

        # 定义要执行的函数（包含重试逻辑）
        async def execute_with_retry():
            if use_retry:
                return await self.retry_manager.execute(
                    func,
                    *args,
                    context={'operation_name': operation_name},
                    **kwargs
                )
            else:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)

        # 通过熔断器执行
        try:
            if cb:
                result = await cb.call(execute_with_retry)
            else:
                result = await execute_with_retry()

            self.stats['successful_calls'] += 1
            return result

        except Exception:
            self.stats['failed_calls'] += 1

            # 检查是否需要加入死信队列
            if use_circuit_breaker and cb and cb.get_state() == CircuitState.OPEN:
                self.stats['circuit_breaker_trips'] += 1

            raise

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            'total_calls': self.stats['total_calls'],
            'successful_calls': self.stats['successful_calls'],
            'failed_calls': self.stats['failed_calls'],
            'success_rate': (
                self.stats['successful_calls'] / self.stats['total_calls']
                if self.stats['total_calls'] > 0 else 0
            ),
            'retry_stats': self.retry_manager.get_stats(),
            'circuit_breakers': {
                name: cb.get_stats()
                for name, cb in self.circuit_breakers.items()
            },
            'dead_letter_queue_size': asyncio.create_task(
                self.dead_letter_queue.size() if asyncio.iscoroutinefunction(self.dead_letter_queue.size)
                else self.dead_letter_queue.size()
            )
        }


# =============================================================================
# 全局可靠性管理器
# =============================================================================

_global_reliability_manager: ReliabilityManager | None = None


def get_reliability_manager() -> ReliabilityManager:
    """获取全局可靠性管理器（单例）"""
    global _global_reliability_manager
    if _global_reliability_manager is None:
        _global_reliability_manager = ReliabilityManager()
    return _global_reliability_manager


# =============================================================================
# 测试代码
# =============================================================================

async def test_reliability_components():
    """测试可靠性组件"""
    logger.info("="*60)
    logger.info("🧪 测试可靠性组件")
    logger.info("="*60)

    manager = get_reliability_manager()

    # 测试1: 重试机制
    logger.info("\n📝 测试1: 重试机制")
    attempt_count = 0

    async def failing_function():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise ValueError("模拟失败")
        return "成功"

    result = await manager.execute_with_reliability(
        "test_operation",
        failing_function
    )
    logger.info(f"✅ 重试测试完成: {result}, 尝试次数: {attempt_count}")

    # 测试2: 熔断器
    logger.info("\n📝 测试2: 熔断器")
    failure_count = 0

    async def circuit_breaker_test():
        nonlocal failure_count
        failure_count += 1
        raise RuntimeError("熔断器测试失败")

    # 触发熔断器打开
    for _i in range(10):
        try:
            await manager.execute_with_reliability(
                "circuit_test",
                circuit_breaker_test,
                use_retry=False
            )
        except Exception:
            pass

    cb = manager.circuit_breakers.get('circuit_test')
    if cb:
        logger.info(f"   熔断器状态: {cb.get_state().value}")
        logger.info(f"   熔断器统计: {cb.get_stats()}")

    # 测试3: 死信队列
    logger.info("\n📝 测试3: 死信队列")
    await manager.dead_letter_queue.add(
        'task_001',
        'test_task',
        {'param': 'value'},
        Exception("测试异常")
    )

    queue_size = await manager.dead_letter_queue.size()
    logger.info(f"✅ 死信队列大小: {queue_size}")

    # 测试4: 总体统计
    logger.info("\n📝 测试4: 总体统计")
    stats = manager.get_stats()
    logger.info(f"   统计信息: {stats}")

    logger.info("\n" + "="*60)
    logger.info("🎉 测试完成！")
    logger.info("="*60)


if __name__ == '__main__':
    asyncio.run(test_reliability_components())
