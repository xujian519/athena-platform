#!/usr/bin/env python3
from __future__ import annotations
"""
断路器
Circuit Breaker

实现断路器模式,保护系统免受级联故障影响
目标将外部服务故障率控制在5%以下
"""

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """断路状态"""

    CLOSED = "closed"  # 关闭(正常)
    OPEN = "open"  # 打开(熔断)
    HALF_OPEN = "half_open"  # 半开(试探)


@dataclass
class CircuitBreakerConfig:
    """断路器配置"""

    failure_threshold: int = 5  # 失败阈值
    success_threshold: int = 2  # 半开状态成功阈值
    timeout: float = 60.0  # 打开超时(秒)
    rolling_window: float = 60.0  # 滚动窗口(秒)
    half_open_max_calls: int = 3  # 半开状态最大调用数


@dataclass
class CallResult:
    """调用结果"""

    success: bool
    duration: float
    error: Optional[str] = None
    result: Any = None


@dataclass
class CircuitBreakerStats:
    """断路器统计"""

    service_id: str
    state: CircuitState
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    last_failure_time: datetime | None = None
    last_state_change: datetime | None = None
    failure_rate: float = 0.0
    avg_duration: float = 0.0


class CircuitBreaker:
    """
    断路器

    核心功能:
    1. 故障检测
    2. 自动熔断
    3. 半开试探
    4. 自动恢复
    """

    def __init__(self, service_id: str, config: CircuitBreakerConfig | None = None):
        """
        初始化断路器

        Args:
            service_id: 服务ID
            config: 配置
        """
        self.service_id = service_id
        self.config = config or CircuitBreakerConfig()

        # 状态
        self.state = CircuitState.CLOSED
        self.state_changed_at = datetime.now()

        # 调用历史(用于计算失败率)
        self.call_history: list[tuple] = []  # (timestamp, success)

        # 半开状态计数
        self.half_open_calls = 0
        self.half_open_successes = 0

        # 统计
        self.stats = CircuitBreakerStats(service_id=service_id, state=CircuitState.CLOSED)

    async def call(self, func: Callable, *args, **kwargs) -> CallResult:
        """
        通过断路器调用函数

        Args:
            func: 要调用的函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            CallResult: 调用结果
        """
        # 检查断路器状态
        if self.state == CircuitState.OPEN:
            # 检查是否可以进入半开状态
            if self._should_attempt_reset():
                self._transition_to_half_open()
            else:
                # 拒绝调用
                self.stats.rejected_calls += 1
                return CallResult(success=False, duration=0, error=f"断路器打开: {self.service_id}")

        # 执行调用
        start_time = time.time()
        result = CallResult(success=False, duration=0)

        try:
            # 执行函数
            if asyncio.iscoroutinefunction(func):
                response = await func(*args, **kwargs)
            else:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(None, lambda: func(*args, **kwargs))

            result.success = True
            result.result = response
            result.duration = time.time() - start_time

            # 记录成功
            self._record_success(result.duration)

        except Exception as e:
            result.success = False
            result.error = str(e)
            result.duration = time.time() - start_time

            # 记录失败
            self._record_failure()

        return result

    def _should_attempt_reset(self) -> bool:
        """是否应该尝试重置"""
        if self.state != CircuitState.OPEN:
            return False

        time_since_open = (datetime.now() - self.state_changed_at).total_seconds()
        return time_since_open >= self.config.timeout

    def _transition_to_half_open(self) -> Any:
        """转换到半开状态"""
        logger.info(f"断路器进入半开状态: {self.service_id}")
        self.state = CircuitState.HALF_OPEN
        self.state_changed_at = datetime.now()
        self.half_open_calls = 0
        self.half_open_successes = 0
        self.stats.state = CircuitState.HALF_OPEN
        self.stats.last_state_change = datetime.now()

    def _transition_to_open(self) -> Any:
        """转换到打开状态"""
        logger.warning(f"断路器打开: {self.service_id}")
        self.state = CircuitState.OPEN
        self.state_changed_at = datetime.now()
        self.stats.state = CircuitState.OPEN
        self.stats.last_state_change = datetime.now()

    def _transition_to_closed(self) -> Any:
        """转换到关闭状态"""
        logger.info(f"断路器恢复关闭: {self.service_id}")
        self.state = CircuitState.CLOSED
        self.state_changed_at = datetime.now()
        self.call_history.clear()
        self.stats.state = CircuitState.CLOSED
        self.stats.last_state_change = datetime.now()

    def _record_success(self, duration: float) -> Any:
        """记录成功调用"""
        now = datetime.now()
        self.call_history.append((now, True))
        self.stats.successful_calls += 1
        self.stats.total_calls += 1

        # 更新平均耗时
        self.stats.avg_duration = (
            self.stats.avg_duration * (self.stats.total_calls - 1) + duration
        ) / self.stats.total_calls

        # 半开状态处理
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_calls += 1
            self.half_open_successes += 1

            # 达到成功阈值,关闭断路器
            if (
                self.half_open_calls >= self.config.half_open_max_calls
                and self.half_open_successes >= self.config.success_threshold
            ):
                self._transition_to_closed()

        # 清理过期历史
        self._cleanup_history()

    def _record_failure(self) -> Any:
        """记录失败调用"""
        now = datetime.now()
        self.call_history.append((now, False))
        self.stats.failed_calls += 1
        self.stats.total_calls += 1
        self.stats.last_failure_time = now

        # 半开状态处理
        if self.state == CircuitState.HALF_OPEN:
            # 半开状态失败,重新打开
            self._transition_to_open()
        else:
            # 检查是否需要打开断路器
            if self._should_open():
                self._transition_to_open()

        # 清理过期历史
        self._cleanup_history()

    def _should_open(self) -> bool:
        """是否应该打开断路器"""
        # 计算滚动窗口内的失败率
        window_start = datetime.now() - timedelta(seconds=self.config.rolling_window)
        window_calls = [(ts, success) for ts, success in self.call_history if ts >= window_start]

        if len(window_calls) < self.config.failure_threshold:
            return False

        failures = sum(1 for _, success in window_calls if not success)
        failure_rate = failures / len(window_calls)

        return failure_rate >= 0.5 or failures >= self.config.failure_threshold

    def _cleanup_history(self) -> Any:
        """清理过期历史"""
        cutoff = datetime.now() - timedelta(seconds=self.config.rolling_window)
        self.call_history = [(ts, success) for ts, success in self.call_history if ts >= cutoff]

    def get_state(self) -> CircuitState:
        """获取当前状态"""
        return self.state

    def get_stats(self) -> CircuitBreakerStats:
        """获取统计信息"""
        # 计算失败率
        if self.stats.total_calls > 0:
            self.stats.failure_rate = self.stats.failed_calls / self.stats.total_calls
        return self.stats

    def reset(self) -> Any:
        """重置断路器"""
        logger.info(f"重置断路器: {self.service_id}")
        self._transition_to_closed()
        self.call_history.clear()
        self.stats = CircuitBreakerStats(service_id=self.service_id, state=CircuitState.CLOSED)


class CircuitBreakerRegistry:
    """断路器注册表"""

    def __init__(self):
        """初始化注册表"""
        self.breakers: dict[str, CircuitBreaker] = {}

    def get_breaker(
        self, service_id: str, config: CircuitBreakerConfig | None = None
    ) -> CircuitBreaker:
        """
        获取或创建断路器

        Args:
            service_id: 服务ID
            config: 配置

        Returns:
            CircuitBreaker: 断路器实例
        """
        if service_id not in self.breakers:
            self.breakers[service_id] = CircuitBreaker(service_id, config)
            logger.info(f"创建断路器: {service_id}")

        return self.breakers[service_id]

    def remove_breaker(self, service_id: str) -> None:
        """移除断路器"""
        if service_id in self.breakers:
            del self.breakers[service_id]
            logger.info(f"移除断路器: {service_id}")

    def get_all_stats(self) -> dict[str, CircuitBreakerStats]:
        """获取所有断路器统计"""
        return {service_id: breaker.get_stats() for service_id, breaker in self.breakers.items()}


# 单例实例
_registry_instance: CircuitBreakerRegistry | None = None


def get_circuit_breaker_registry() -> CircuitBreakerRegistry:
    """获取断路器注册表单例"""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = CircuitBreakerRegistry()
        logger.info("断路器注册表已初始化")
    return _registry_instance


async def get_circuit_breaker(
    service_id: str = "default", config: CircuitBreakerConfig | None = None
) -> CircuitBreaker:
    """
    获取或创建断路器(异步版本)

    Args:
        service_id: 服务ID(默认为"default")
        config: 断路器配置(可选)

    Returns:
        CircuitBreaker: 断路器实例
    """
    registry = get_circuit_breaker_registry()
    return registry.get_breaker(service_id, config)


def get_circuit_breaker_sync(
    service_id: str = "default", config: CircuitBreakerConfig | None = None
) -> CircuitBreaker:
    """
    获取或创建断路器(同步版本)

    Args:
        service_id: 服务ID(默认为"default")
        config: 断路器配置(可选)

    Returns:
        CircuitBreaker: 断路器实例
    """
    registry = get_circuit_breaker_registry()
    return registry.get_breaker(service_id, config)


def with_circuit_breaker(service_id: Optional[str],
    config: CircuitBreakerConfig | None = None):
    """
    断路器装饰器

    Args:
        service_id: 服务ID
        config: 配置
    """

    def decorator(func: Callable) -> Callable:
        async def async_wrapper(*args, **kwargs):
            registry = get_circuit_breaker_registry()
            breaker = registry.get_breaker(service_id, config)
            result = await breaker.call(func, *args, **kwargs)

            if result.success:
                return result.result
            else:
                raise Exception(result.error or "调用失败")

        def sync_wrapper(*args, **kwargs) -> Any:
            registry = get_circuit_breaker_registry()
            breaker = registry.get_breaker(service_id, config)

            async def async_call():
                result = await breaker.call(func, *args, **kwargs)
                if result.success:
                    return result.result
                else:
                    raise Exception(result.error or "调用失败")

            return asyncio.run(async_call())

        import inspect

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


async def main():
    """测试主函数"""
    registry = get_circuit_breaker_registry()

    print("=== 断路器测试 ===\n")

    # 创建断路器
    breaker = registry.get_breaker(
        "test_service", CircuitBreakerConfig(failure_threshold=3, timeout=5.0)
    )

    # 测试函数
    async def test_service(should_fail: bool = False):
        await asyncio.sleep(0.1)
        if should_fail:
            raise Exception("服务错误")
        return "服务响应"

    # 测试1: 正常调用
    print("测试1: 正常调用")
    result = await breaker.call(test_service, False)
    print(f"  成功: {result.success}")
    print(f"  状态: {breaker.get_state().value}")

    # 测试2: 触发熔断
    print("\n测试2: 触发熔断")
    for i in range(5):
        result = await breaker.call(test_service, True)
        print(f"  调用 {i+1}: 成功={result.success}, 状态={breaker.get_state().value}")

    # 测试3: 熔断后调用
    print("\n测试3: 熔断后调用(应被拒绝)")
    result = await breaker.call(test_service, False)
    print(f"  成功: {result.success}")
    print(f"  错误: {result.error}")

    # 显示统计
    stats = breaker.get_stats()
    print("\n=== 统计信息 ===")
    print(f"总调用: {stats.total_calls}")
    print(f"成功: {stats.successful_calls}")
    print(f"失败: {stats.failed_calls}")
    print(f"拒绝: {stats.rejected_calls}")
    print(f"失败率: {stats.failure_rate:.1%}")


# 入口点: @async_main装饰器已添加到main函数
