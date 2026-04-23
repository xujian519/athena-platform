#!/usr/bin/env python3

"""
Athena 感知模块 - 降级管理和熔断器
支持服务降级、功能降级、熔断器模式
最后更新: 2026-01-26
"""

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class DegradationLevel(Enum):
    """降级级别"""
    NONE = "none"               # 无降级
    PARTIAL = "partial"         # 部分降级
    FULL = "full"               # 完全降级


class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = "closed"           # 关闭（正常）
    OPEN = "open"               # 开启（熔断）
    HALF_OPEN = "half_open"     # 半开（试探）


@dataclass
class CircuitBreakerConfig:
    """熔断器配置"""
    failure_threshold: int = 5           # 失败阈值
    success_threshold: int = 2           # 成功阈值（半开状态）
    timeout: float = 60.0               # 熔断超时（秒）
    rolling_window: float = 60.0        # 滚动窗口（秒）


@dataclass
class CircuitBreakerState:
    """熔断器状态数据"""
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    last_state_change: float = field(default_factory=time.time)
    rolling_failures: list[float] = field(default_factory=list)


class CircuitBreaker:
    """
    熔断器实现

    功能：
    - 失败检测
    - 自动熔断
    - 半开试探
    - 自动恢复
    """

    def __init__(self, config: CircuitBreakerConfig):
        """
        初始化熔断器

        Args:
            config: 熔断器配置
        """
        self.config = config
        self.state_data = CircuitBreakerState()
        self._lock = asyncio.Lock()

        logger.info(
            f"✓ 熔断器已初始化 "
            f"(失败阈值: {config.failure_threshold}, "
            f"超时: {config.timeout}s)"
        )

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        通过熔断器调用函数

        Args:
            func: 要调用的函数
            *args: 函数参数
            **kwargs: 函数关键字参数

        Returns:
            函数返回值

        Raises:
            Exception: 熔断器开启或函数执行失败
        """
        async with self._lock:
            # 检查熔断器状态
            if self.state_data.state == CircuitState.OPEN:
                # 检查是否应该进入半开状态
                if self._should_attempt_reset():
                    logger.info("熔断器进入半开状态")
                    self.state_data.state = CircuitState.HALF_OPEN
                    self.state_data.last_state_change = time.time()
                else:
                    raise Exception("熔断器已开启，拒绝请求")

            # 检查滚动窗口中的失败次数
            self._clean_rolling_failures()

            if len(self.state_data.rolling_failures) >= self.config.failure_threshold:
                self._trip_breaker()
                raise Exception("达到失败阈值，熔断器已开启")

        try:
            # 执行函数
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # 记录成功
            await self._record_success()

            return result

        except Exception as e:
            # 记录失败
            await self._record_failure()
            raise e

    async def _record_success(self):
        """记录成功"""
        async with self._lock:
            self.state_data.success_count += 1

            # 如果在半开状态，达到成功阈值则关闭熔断器
            if (self.state_data.state == CircuitState.HALF_OPEN and
                self.state_data.success_count >= self.config.success_threshold):
                logger.info("熔断器已关闭（恢复）")
                self.state_data.state = CircuitState.CLOSED
                self.state_data.failure_count = 0
                self.state_data.success_count = 0
                self.state_data.last_state_change = time.time()

    async def _record_failure(self):
        """记录失败"""
        async with self._lock:
            self.state_data.failure_count += 1
            self.state_data.last_failure_time = time.time()

            # 添加到滚动窗口
            self.state_data.rolling_failures.append(time.time())

            # 检查是否需要熔断
            if len(self.state_data.rolling_failures) >= self.config.failure_threshold:
                self._trip_breaker()

    def _trip_breaker(self):
        """触发熔断"""
        if self.state_data.state != CircuitState.OPEN:
            logger.warning(f"熔断器已开启！失败次数: {self.state_data.failure_count}")
            self.state_data.state = CircuitState.OPEN
            self.state_data.last_state_change = time.time()

    def _should_attempt_reset(self) -> bool:
        """检查是否应该尝试重置熔断器"""
        return (time.time() - self.state_data.last_state_change) >= self.config.timeout

    def _clean_rolling_failures(self):
        """清理滚动窗口中的过期失败记录"""
        cutoff_time = time.time() - self.config.rolling_window
        self.state_data.rolling_failures = [
            t for t in self.state_data.rolling_failures
            if t > cutoff_time
        ]

    def get_state(self) -> dict[str, Any]:
        """
        获取熔断器状态

        Returns:
            状态信息字典
        """
        self._clean_rolling_failures()

        return {
            "state": self.state_data.state.value,
            "failure_count": self.state_data.failure_count,
            "success_count": self.state_data.success_count,
            "rolling_failures": len(self.state_data.rolling_failures),
            "last_failure_time": self.state_data.last_failure_time,
            "last_state_change": self.state_data.last_state_change
        }

    def reset(self):
        """重置熔断器"""
        self.state_data = CircuitBreakerState()
        logger.info("✓ 熔断器已重置")


class DegradationManager:
    """
    降级管理器

    功能：
    - 服务降级
    - 功能降级
    - 自动降级
    - 自动恢复
    """

    def __init__(self):
        """初始化降级管理器"""
        self.current_level = DegradationLevel.NONE
        self.degraded_services: dict[str, DegradationLevel] = {}
        self.fallbacks: dict[str, Callable] = {}
        self.circuit_breakers: dict[str, CircuitBreaker] = {}

        logger.info("✓ 降级管理器已初始化")

    def register_circuit_breaker(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None
    ):
        """
        注册熔断器

        Args:
            name: 熔断器名称
            config: 熔断器配置
        """
        config = config or CircuitBreakerConfig()
        self.circuit_breakers[name] = CircuitBreaker(config)
        logger.info(f"✓ 已注册熔断器: {name}")

    def register_fallback(self, name: str, fallback: Callable):
        """
        注册降级函数

        Args:
            name: 降级名称
            fallback: 降级函数
        """
        self.fallbacks[name] = fallback
        logger.info(f"✓ 已注册降级函数: {name}")

    async def call_with_protection(
        self,
        service_name: str,
        func: Callable,
        fallback_name: Optional[str] = None,
        *args,
        **kwargs
    ) -> Any:
        """
        带保护的调用服务

        Args:
            service_name: 服务名称
            func: 要调用的函数
            fallback_name: 降级函数名称
            *args: 函数参数
            **kwargs: 函数关键字参数

        Returns:
            函数返回值或降级结果
        """
        # 检查是否降级
        if self.is_degraded(service_name):
            logger.warning(f"服务已降级: {service_name}")
            if fallback_name and fallback_name in self.fallbacks:
                return await self._execute_fallback(fallback_name, *args, **kwargs)
            raise Exception(f"服务已降级且无降级函数: {service_name}")

        # 通过熔断器调用
        if service_name in self.circuit_breakers:
            breaker = self.circuit_breakers[service_name]
            try:
                return await breaker.call(func, *args, **kwargs)
            except Exception as e:
                # 尝试降级
                if fallback_name and fallback_name in self.fallbacks:
                    logger.warning(f"服务调用失败，使用降级函数: {service_name}")
                    return await self._execute_fallback(fallback_name, *args, **kwargs)
                raise e
        else:
            # 无熔断器，直接调用
            return await func(*args, **kwargs)

    async def _execute_fallback(self, name: str, *args, **kwargs) -> Any:
        """
        执行降级函数

        Args:
            name: 降级函数名称
            *args: 函数参数
            **kwargs: 函数关键字参数

        Returns:
            降级函数返回值
        """
        fallback = self.fallbacks.get(name)
        if fallback:
            if asyncio.iscoroutinefunction(fallback):
                return await fallback(*args, **kwargs)
            else:
                return fallback(*args, **kwargs)
        raise Exception(f"降级函数不存在: {name}")

    def degrade_service(self, service_name: str, level: DegradationLevel):
        """
        降级服务

        Args:
            service_name: 服务名称
            level: 降级级别
        """
        old_level = self.degraded_services.get(service_name)
        self.degraded_services[service_name] = level

        logger.warning(
            f"服务降级: {service_name} "
            f"({old_level.value if old_level else 'none'} → {level.value})"
        )

    def recover_service(self, service_name: str):
        """
        恢复服务

        Args:
            service_name: 服务名称
        """
        if service_name in self.degraded_services:
            del self.degraded_services[service_name]
            logger.info(f"服务已恢复: {service_name}")

    def is_degraded(self, service_name: Optional[str] = None) -> bool:
        """
        检查是否降级

        Args:
            service_name: 服务名称，None表示检查全局降级

        Returns:
            是否降级
        """
        if service_name:
            return service_name in self.degraded_services
        return len(self.degraded_services) > 0

    def get_degradation_status(self) -> dict[str, Any]:
        """
        获取降级状态

        Returns:
            降级状态字典
        """
        return {
            "global_level": self.current_level.value,
            "degraded_services": {
                name: level.value
                for name, level in self.degraded_services.items()
            },
            "circuit_breakers": {
                name: breaker.get_state()
                for name, breaker in self.circuit_breakers.items()
            }
        }


# 使用示例
if __name__ == "__main__":
    import asyncio

    async def test_circuit_breaker_and_degradation():
        # 创建降级管理器
        manager = DegradationManager()

        # 注册熔断器
        manager.register_circuit_breaker(
            "ocr_service",
            CircuitBreakerConfig(failure_threshold=3, timeout=10)
        )

        # 注册降级函数
        async def ocr_fallback(image_path: str):
            return f"[降级] 缓存结果: {image_path}"

        manager.register_fallback("ocr", ocr_fallback)

        # 测试熔断器
        print("\n=== 测试熔断器 ===")
        call_count = [0]

        async def flaky_ocr(image_path: str):
            call_count[0] += 1
            if call_count[0] <= 3:
                raise ConnectionError("OCR服务不可用")
            return f"OCR结果: {image_path}"

        # 尝试调用（前3次失败）
        for i in range(5):
            try:
                result = await manager.call_with_protection(
                    "ocr_service",
                    flaky_ocr,
                    "ocr",
                    "/tmp/test.png"
                )
                print(f"第{i+1}次调用成功: {result}")
            except Exception as e:
                print(f"第{i+1}次调用失败: {e}")

            # 显示熔断器状态
            state = manager.circuit_breakers["ocr_service"].get_state()
            print(f"熔断器状态: {state['state']}")

            await asyncio.sleep(0.5)

        # 显示降级状态
        print("\n=== 降级状态 ===")
        status = manager.get_degradation_status()
        print(f"降级服务: {status['degraded_services']}")
        print(f"熔断器状态: {status['circuit_breakers']}")

    asyncio.run(test_circuit_breaker_and_degradation())

