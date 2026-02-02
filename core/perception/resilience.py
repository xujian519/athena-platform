#!/usr/bin/env python3
"""
请求重试和熔断机制
Request Retry and Circuit Breaker Mechanism

提供健壮的请求重试和熔断功能,保护系统免受级联故障影响。

功能特性:
1. 多种重试策略
2. 熔断器模式
3. 超时控制
4. 降级策略
5. 健康检查

重试策略:
- 固定间隔
- 指数退避
- 线性退避
- 随机抖动
- 自适应

熔断器状态:
- 关闭 (CLOSED) - 正常工作
- 打开 (OPEN) - 熔断激活
- 半开 (HALF_OPEN) - 测试恢复

作者: Athena AI系统
创建时间: 2026-01-25
版本: 1.0.0
"""

import asyncio
import inspect
import logging
import random
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryStrategy(Enum):
    """重试策略"""

    FIXED = "fixed"  # 固定间隔
    EXPONENTIAL = "exponential"  # 指数退避
    LINEAR = "linear"  # 线性退避
    RANDOM = "random"  # 随机抖动
    ADAPTIVE = "adaptive"  # 自适应


class CircuitState(Enum):
    """熔断器状态"""

    CLOSED = "closed"  # 关闭(正常)
    OPEN = "open"  # 打开(熔断)
    HALF_OPEN = "half_open"  # 半开(测试恢复)


@dataclass
class RetryConfig:
    """重试配置"""

    max_attempts: int = 3  # 最大重试次数
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    base_delay: float = 1.0  # 基础延迟(秒)
    max_delay: float = 60.0  # 最大延迟(秒)
    exponential_base: float = 2.0  # 指数基数
    jitter: bool = True  # 是否添加随机抖动
    jitter_factor: float = 0.1  # 抖动因子

    # 超时配置
    timeout: float | None = None  # 单次请求超时
    total_timeout: float | None = None  # 总超时时间

    # 重试条件
    retry_on: list[type[Exception]] | None = None  # 需要重试的异常类型
    no_retry_on: list[type[Exception]] | None = None  # 不需要重试的异常类型

    def validate(self) -> None:
        """验证配置"""
        if self.max_attempts < 1:
            raise ValueError("max_attempts必须大于等于1")
        if self.base_delay < 0:
            raise ValueError("base_delay必须大于等于0")
        if self.max_delay < self.base_delay:
            raise ValueError("max_delay必须大于等于base_delay")


@dataclass
class CircuitBreakerConfig:
    """熔断器配置"""

    failure_threshold: int = 5  # 失败阈值
    success_threshold: int = 2  # 成功阈值(半开状态)
    timeout: float = 60.0  # 熔断超时(秒)
    half_open_max_calls: int = 3  # 半开状态最大调用数
    sliding_window_size: int = 100  # 滑动窗口大小
    min_throughput: int = 10  # 最小吞吐量


@dataclass
class RetryResult:
    """重试结果"""

    success: bool
    result: Any = None
    error: Exception | None = None
    attempts: int = 0  # 尝试次数
    total_time: float = 0.0  # 总耗时
    retry_delays: list[float] = field(default_factory=list)  # 各次重试延迟


@dataclass
class CircuitBreakerMetrics:
    """熔断器指标"""

    state: CircuitState = CircuitState.CLOSED
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rejected_requests: int = 0
    last_failure_time: datetime | None = None
    last_state_change: datetime = field(default_factory=datetime.now)

    # 滑动窗口
    sliding_window: list[bool] = field(default_factory=list)  # True=成功, False=失败

    @property
    def failure_rate(self) -> float:
        """失败率"""
        if self.total_requests == 0:
            return 0.0
        return self.failed_requests / self.total_requests

    @property
    def success_rate(self) -> float:
        """成功率"""
        return 1.0 - self.failure_rate


class RetryExecutor:
    """重试执行器

    提供灵活的重试机制。

    使用示例:
        >>> executor = RetryExecutor(config=RetryConfig(max_attempts=3))
        >>>
        >>> async def risky_operation():
        >>>     # 可能失败的操作
        >>>     pass
        >>>
        >>> result = await executor.execute(risky_operation)
    """

    def __init__(self, config: RetryConfig | None = None):
        """初始化重试执行器

        Args:
            config: 重试配置
        """
        self.config = config or RetryConfig()
        self.config.validate()

        logger.info(
            f"🔄 初始化重试执行器 "
            f"(最大尝试={self.config.max_attempts}, 策略={self.config.strategy.value})"
        )

    async def execute(
        self,
        func: Callable[..., T],
        *args: Any,
        **kwargs: Any,
    ) -> RetryResult:
        """执行函数(带重试)

        Args:
            func: 要执行的函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            重试结果
        """
        start_time = time.time()
        last_error = None
        attempts = 0
        retry_delays = []

        for attempt in range(self.config.max_attempts):
            attempts = attempt + 1

            try:
                # 执行函数
                if self.config.timeout is not None:
                    result = await asyncio.wait_for(
                        self._call_func(func, *args, **kwargs),
                        timeout=self.config.timeout,
                    )
                else:
                    result = await self._call_func(func, *args, **kwargs)

                # 成功
                total_time = time.time() - start_time
                logger.debug(f"✅ 重试成功: 第{attempts}次尝试 " f"(耗时={total_time:.3f}s)")

                return RetryResult(
                    success=True,
                    result=result,
                    attempts=attempts,
                    total_time=total_time,
                    retry_delays=retry_delays,
                )

            except Exception as e:
                last_error = e

                # 检查是否应该重试
                if not self._should_retry(e, attempt):
                    break

                # 计算重试延迟
                if attempt < self.config.max_attempts - 1:
                    delay = self._calculate_delay(attempt)
                    retry_delays.append(delay)

                    logger.debug(f"⚠️ 第{attempts}次尝试失败: {e}, " f"{delay:.2f}秒后重试...")

                    await asyncio.sleep(delay)

        # 所有尝试都失败
        total_time = time.time() - start_time
        logger.error(
            f"❌ 重试失败: 共{attempts}次尝试, " f"总耗时={total_time:.3f}s, 最后错误={last_error}"
        )

        return RetryResult(
            success=False,
            error=last_error,
            attempts=attempts,
            total_time=total_time,
            retry_delays=retry_delays,
        )

    async def _call_func(
        self,
        func: Callable[..., T],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """调用函数"""
        if inspect.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)

    def _should_retry(self, error: Exception, attempt: int) -> bool:
        """判断是否应该重试"""
        # 检查是否达到最大尝试次数
        if attempt >= self.config.max_attempts - 1:
            return False

        # 检查总超时
        if self.config.total_timeout is not None:
            # 这里简化处理,实际应该跟踪累计时间
            pass

        # 检查异常类型
        if self.config.no_retry_on:
            if any(isinstance(error, t) for t in self.config.no_retry_on):
                return False

        if self.config.retry_on:
            return any(isinstance(error, t) for t in self.config.retry_on)

        # 默认重试所有异常
        return True

    def _calculate_delay(self, attempt: int) -> float:
        """计算重试延迟"""
        if self.config.strategy == RetryStrategy.FIXED:
            delay = self.config.base_delay

        elif self.config.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.config.base_delay * (self.config.exponential_base**attempt)

        elif self.config.strategy == RetryStrategy.LINEAR:
            delay = self.config.base_delay * (attempt + 1)

        elif self.config.strategy == RetryStrategy.RANDOM:
            delay = random.uniform(0, self.config.max_delay)

        else:  # ADAPTIVE
            # 自适应策略:根据失败次数调整
            delay = min(
                self.config.base_delay * (1.5**attempt),
                self.config.max_delay,
            )

        # 限制最大延迟
        delay = min(delay, self.config.max_delay)

        # 添加随机抖动
        if self.config.jitter:
            jitter_amount = delay * self.config.jitter_factor
            delay += random.uniform(-jitter_amount, jitter_amount)
            delay = max(0, delay)

        return delay


class CircuitBreaker:
    """熔断器

    实现熔断器模式,保护系统免受级联故障影响。

    使用示例:
        >>> breaker = CircuitBreaker(config=CircuitBreakerConfig())
        >>> await breaker.initialize()
        >>>
        >>> async def protected_operation():
        >>>     # 受保护的操作
        >>>     pass
        >>>
        >>> # 使用熔断器
        >>> result = await breaker.call(protected_operation)
    """

    def __init__(self, config: CircuitBreakerConfig | None = None):
        """初始化熔断器

        Args:
            config: 熔断器配置
        """
        self.config = config or CircuitBreakerConfig()
        self._metrics = CircuitBreakerMetrics()

        # 半开状态计数器
        self._half_open_calls = 0

        # 锁
        self._lock = asyncio.Lock()

        logger.info(
            f"⚡ 初始化熔断器 "
            f"(失败阈值={self.config.failure_threshold}, "
            f"超时={self.config.timeout}s)"
        )

    async def initialize(self) -> None:
        """初始化熔断器"""
        logger.info("✅ 熔断器初始化完成")

    async def call(
        self,
        func: Callable[..., T],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """调用受保护的函数

        Args:
            func: 要调用的函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            函数结果

        Raises:
            RuntimeError: 如果熔断器打开
        """
        # 检查熔断器状态
        async with self._lock:
            if self._metrics.state == CircuitState.OPEN:
                # 检查是否应该转换为半开状态
                if self._should_attempt_reset():
                    self._transition_to_half_open()
                else:
                    self._metrics.rejected_requests += 1
                    raise RuntimeError("熔断器打开,拒绝请求")

            elif self._metrics.state == CircuitState.HALF_OPEN:
                # 半开状态限制调用次数
                if self._half_open_calls >= self.config.half_open_max_calls:
                    self._metrics.rejected_requests += 1
                    raise RuntimeError("熔断器半开,已达最大调用次数")

        # 执行函数
        try:
            if inspect.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # 成功
            await self._on_success()
            return result

        except Exception:
            # 失败
            await self._on_failure()
            raise

    async def _on_success(self) -> None:
        """处理成功"""
        async with self._lock:
            self._metrics.total_requests += 1
            self._metrics.successful_requests += 1
            self._sliding_window_append(True)

            if self._metrics.state == CircuitState.HALF_OPEN:
                self._half_open_calls += 1

                # 检查是否应该转换为关闭状态
                if self._half_open_calls >= self.config.success_threshold:
                    self._transition_to_closed()

    async def _on_failure(self) -> None:
        """处理失败"""
        async with self._lock:
            self._metrics.total_requests += 1
            self._metrics.failed_requests += 1
            self._metrics.last_failure_time = datetime.now()
            self._sliding_window_append(False)

            # 检查是否应该打开熔断器
            if self._should_trip():
                self._transition_to_open()

    def _sliding_window_append(self, success: bool) -> None:
        """添加到滑动窗口"""
        self._metrics.sliding_window.append(success)

        # 保持窗口大小
        if len(self._metrics.sliding_window) > self.config.sliding_window_size:
            self._metrics.sliding_window.pop(0)

    def _should_trip(self) -> bool:
        """判断是否应该打开熔断器"""
        # 检查失败次数
        if self._metrics.failed_requests >= self.config.failure_threshold:
            # 检查最小吞吐量
            if self._metrics.total_requests >= self.config.min_throughput:
                return True

        # 检查滑动窗口失败率
        if len(self._metrics.sliding_window) >= self.config.min_throughput:
            failure_rate = 1 - sum(self._metrics.sliding_window) / len(self._metrics.sliding_window)
            if failure_rate > 0.5:  # 50%失败率
                return True

        return False

    def _should_attempt_reset(self) -> bool:
        """判断是否应该尝试重置"""
        if self._metrics.last_failure_time is None:
            return True

        elapsed = (datetime.now() - self._metrics.last_failure_time).total_seconds()
        return elapsed >= self.config.timeout

    def _transition_to_open(self) -> None:
        """转换到打开状态"""
        logger.warning(
            f"⚡ 熔断器打开: "
            f"失败数={self._metrics.failed_requests}, "
            f"失败率={self._metrics.failure_rate:.2%}"
        )
        self._metrics.state = CircuitState.OPEN
        self._metrics.last_state_change = datetime.now()

    def _transition_to_half_open(self) -> None:
        """转换到半开状态"""
        logger.info("🔓 熔断器半开: 测试恢复")
        self._metrics.state = CircuitState.HALF_OPEN
        self._metrics.last_state_change = datetime.now()
        self._half_open_calls = 0

    def _transition_to_closed(self) -> None:
        """转换到关闭状态"""
        logger.info(
            f"✅ 熔断器关闭: "
            f"成功数={self._metrics.successful_requests}, "
            f"成功率={self._metrics.success_rate:.2%}"
        )
        self._metrics.state = CircuitState.CLOSED
        self._metrics.last_state_change = datetime.now()
        self._half_open_calls = 0

    def get_state(self) -> CircuitState:
        """获取熔断器状态"""
        return self._metrics.state

    def get_metrics(self) -> CircuitBreakerMetrics:
        """获取指标"""
        return self._metrics

    def reset(self) -> None:
        """重置熔断器"""
        logger.info("🔄 重置熔断器")
        self._metrics = CircuitBreakerMetrics()
        self._half_open_calls = 0


class ResilientExecutor:
    """弹性执行器

    结合重试和熔断功能,提供完整的弹性机制。

    使用示例:
        >>> executor = ResilientExecutor(
        >>>     retry_config=RetryConfig(max_attempts=3),
        >>>     circuit_config=CircuitBreakerConfig()
        >>> )
        >>> await executor.initialize()
        >>>
        >>> result = await executor.execute(risky_operation)
    """

    def __init__(
        self,
        retry_config: RetryConfig | None = None,
        circuit_config: CircuitBreakerConfig | None = None,
        enable_retry: bool = True,
        enable_circuit: bool = True,
    ):
        """初始化弹性执行器

        Args:
            retry_config: 重试配置
            circuit_config: 熔断器配置
            enable_retry: 是否启用重试
            enable_circuit: 是否启用熔断
        """
        self.enable_retry = enable_retry
        self.enable_circuit = enable_circuit

        self.retry_executor = RetryExecutor(retry_config) if enable_retry else None
        self.circuit_breaker = CircuitBreaker(circuit_config) if enable_circuit else None

        logger.info(f"🛡️ 初始化弹性执行器 " f"(重试={enable_retry}, 熔断={enable_circuit})")

    async def initialize(self) -> None:
        """初始化执行器"""
        if self.circuit_breaker:
            await self.circuit_breaker.initialize()
        logger.info("✅ 弹性执行器初始化完成")

    async def execute(
        self,
        func: Callable[..., T],
        *args: Any,
        **kwargs: Any,
    ) -> RetryResult:
        """执行函数(带弹性机制)

        Args:
            func: 要执行的函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            执行结果
        """
        # 使用熔断器
        if self.circuit_breaker:
            start_time = time.time()
            # 包装函数以支持重试
            async def protected_func(*a, **kw):
                if self.retry_executor:
                    return await self.retry_executor.execute(func, *a, **kw)
                else:
                    if inspect.iscoroutinefunction(func):
                        return await func(*a, **kw)
                    else:
                        return func(*a, **kw)

            # 通过熔断器调用
            try:
                result = await self.circuit_breaker.call(protected_func, *args, **kwargs)
                # 如果没有使用重试执行器,需要包装成RetryResult
                if not self.retry_executor:
                    return RetryResult(
                        success=True,
                        result=result,
                        attempts=1,
                        total_time=time.time() - start_time,
                    )
                return result
            except Exception as e:
                return RetryResult(
                    success=False,
                    error=e,
                    attempts=0,
                    total_time=0.0,
                )

        # 仅使用重试
        elif self.retry_executor:
            return await self.retry_executor.execute(func, *args, **kwargs)

        # 直接执行
        else:
            start_time = time.time()
            try:
                if inspect.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                return RetryResult(
                    success=True,
                    result=result,
                    attempts=1,
                    total_time=time.time() - start_time,
                )
            except Exception as e:
                return RetryResult(
                    success=False,
                    error=e,
                    attempts=1,
                    total_time=time.time() - start_time,
                )

    def get_metrics(self) -> dict[str, Any]:
        """获取指标"""
        metrics = {}

        if self.retry_executor:
            metrics["retry"] = {
                "enabled": self.enable_retry,
                "config": self.retry_executor.config,
            }

        if self.circuit_breaker:
            metrics["circuit"] = {
                "enabled": self.enable_circuit,
                "state": self.circuit_breaker.get_state().value,
                "metrics": self.circuit_breaker.get_metrics(),
            }

        return metrics


# 便捷函数
def create_retry_executor(
    max_attempts: int = 3,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
) -> RetryExecutor:
    """创建重试执行器"""
    config = RetryConfig(max_attempts=max_attempts, strategy=strategy)
    return RetryExecutor(config)


def create_circuit_breaker(
    failure_threshold: int = 5,
    timeout: float = 60.0,
) -> CircuitBreaker:
    """创建熔断器"""
    config = CircuitBreakerConfig(
        failure_threshold=failure_threshold,
        timeout=timeout,
    )
    return CircuitBreaker(config)


# 装饰器
def retry(
    max_attempts: int = 3,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
):
    """重试装饰器"""

    def decorator(func: Callable) -> Callable:
        executor = RetryExecutor(config=RetryConfig(max_attempts=max_attempts, strategy=strategy))

        async def wrapper(*args, **kwargs):
            result = await executor.execute(func, *args, **kwargs)
            if result.success:
                return result.result
            else:
                raise result.error

        return wrapper

    return decorator


def circuit_breaker(
    failure_threshold: int = 5,
    timeout: float = 60.0,
):
    """熔断装饰器"""

    def decorator(func: Callable) -> Callable:
        breaker = CircuitBreaker(
            config=CircuitBreakerConfig(
                failure_threshold=failure_threshold,
                timeout=timeout,
            )
        )

        async def wrapper(*args, **kwargs):
            return await breaker.call(func, *args, **kwargs)

        return wrapper

    return decorator


__all__ = [
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerMetrics",
    "CircuitState",
    "ResilientExecutor",
    "RetryConfig",
    "RetryExecutor",
    "RetryResult",
    "RetryStrategy",
    "circuit_breaker",
    "create_circuit_breaker",
    "create_retry_executor",
    "retry",
]
