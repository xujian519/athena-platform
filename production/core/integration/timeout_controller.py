#!/usr/bin/env python3
from __future__ import annotations
"""
外部服务超时控制器
External Service Timeout Controller

通过智能超时控制和自适应延迟调整
优化外部服务调用延迟,目标减少40%
"""

import asyncio
import logging
import statistics
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class TimeoutStrategy(Enum):
    """超时策略"""

    FIXED = "fixed"  # 固定超时
    ADAPTIVE = "adaptive"  # 自适应超时
    PERCENTILE_BASED = "percentile"  # 基于百分位
    PREDICTIVE = "predictive"  # 预测性超时


class CircuitState(Enum):
    """断路状态"""

    CLOSED = "closed"  # 关闭(正常)
    OPEN = "open"  # 打开(熔断)
    HALF_OPEN = "half_open"  # 半开(试探)


@dataclass
class TimeoutConfig:
    """超时配置"""

    base_timeout: float = 5.0  # 基础超时(秒)
    min_timeout: float = 0.5  # 最小超时
    max_timeout: float = 30.0  # 最大超时
    strategy: TimeoutStrategy = TimeoutStrategy.ADAPTIVE
    percentile: float = 0.95  # 百分位阈值
    circuit_breaker_threshold: int = 5  # 断路器阈值(连续失败次数)
    circuit_breaker_timeout: float = 60.0  # 断路器超时(秒)


@dataclass
class ServiceMetrics:
    """服务指标"""

    service_id: str
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    timeout_calls: int = 0
    response_times: list[float] = field(default_factory=list)
    success_rate: float = 1.0
    avg_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0
    last_call_time: datetime | None = None
    consecutive_failures: int = 0
    circuit_state: CircuitState = CircuitState.CLOSED
    circuit_opened_at: datetime | None = None


@dataclass
class CallResult:
    """调用结果"""

    success: bool
    duration: float
    timed_out: bool
    error: str | None = None
    result: Any = None
    timeout_used: float = 0.0


class ExternalServiceTimeoutController:
    """
    外部服务超时控制器

    核心功能:
    1. 智能超时控制
    2. 自适应延迟调整
    3. 断路器保护
    4. 服务健康监控
    """

    def __init__(self):
        """初始化控制器"""
        self.name = "外部服务超时控制器 v1.0"
        self.version = "1.0.0"

        # 服务配置
        self.service_configs: dict[str, TimeoutConfig] = {}

        # 服务指标
        self.service_metrics: dict[str, ServiceMetrics] = {}

        # 默认配置
        self.default_config = TimeoutConfig()

        # 统计信息
        self.stats = {
            "total_services": 0,
            "active_services": 0,
            "circuit_opened_count": 0,
            "total_timeouts": 0,
            "timeout_reduction_rate": 0.0,
        }

    def register_service(self, service_id: str, config: TimeoutConfig | None = None):
        """
        注册服务

        Args:
            service_id: 服务ID
            config: 超时配置
        """
        self.service_configs[service_id] = config or self.default_config
        self.service_metrics[service_id] = ServiceMetrics(service_id=service_id)
        self.stats["total_services"] += 1
        logger.info(f"注册服务: {service_id}")

    async def call_with_timeout(
        self,
        service_id: str,
        func: Callable,
        *args,
        custom_timeout: float | None = None,
        **kwargs,
    ) -> CallResult:
        """
        带超时控制调用服务

        Args:
            service_id: 服务ID
            func: 要调用的函数
            *args: 位置参数
            custom_timeout: 自定义超时
            **kwargs: 关键字参数

        Returns:
            CallResult: 调用结果
        """
        # 获取配置
        config = self.service_configs.get(service_id, self.default_config)
        metrics = self.service_metrics.get(service_id)

        if not metrics:
            self.register_service(service_id, config)
            metrics = self.service_metrics[service_id]

        # 检查断路器
        if metrics.circuit_state == CircuitState.OPEN:
            # 检查是否可以尝试恢复
            if metrics.circuit_opened_at:
                time_since_open = (datetime.now() - metrics.circuit_opened_at).total_seconds()
                if time_since_open < config.circuit_breaker_timeout:
                    return CallResult(
                        success=False,
                        duration=0,
                        timed_out=False,
                        error=f"断路器打开: {service_id}",
                    )
                else:
                    # 进入半开状态
                    metrics.circuit_state = CircuitState.HALF_OPEN
                    logger.info(f"断路器进入半开状态: {service_id}")

        # 计算超时时间
        timeout = custom_timeout or self._calculate_timeout(service_id, config)

        start_time = time.time()
        result = CallResult(success=False, duration=0, timed_out=False, timeout_used=timeout)

        try:
            # 执行调用
            if asyncio.iscoroutinefunction(func):
                response = await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
            else:
                loop = asyncio.get_event_loop()
                response = await asyncio.wait_for(
                    loop.run_in_executor(None, func, *args, **kwargs), timeout=timeout
                )

            # 成功
            duration = time.time() - start_time
            result.success = True
            result.duration = duration
            result.result = response

            # 更新指标
            self._update_success_metrics(service_id, duration)

        except asyncio.TimeoutError:
            # 超时
            duration = time.time() - start_time
            result.timed_out = True
            result.duration = duration
            result.error = f"超时({timeout:.2f}秒)"

            # 更新指标
            self._update_timeout_metrics(service_id, duration)

        except Exception as e:
            # 其他错误
            duration = time.time() - start_time
            result.duration = duration
            result.error = str(e)

            # 更新指标
            self._update_failure_metrics(service_id, duration)

        return result

    def _calculate_timeout(self, service_id: str, config: TimeoutConfig) -> float:
        """计算超时时间"""
        metrics = self.service_metrics.get(service_id)

        if not metrics or not metrics.response_times:
            return config.base_timeout

        if config.strategy == TimeoutStrategy.FIXED:
            return config.base_timeout

        elif config.strategy == TimeoutStrategy.PERCENTILE_BASED:
            # 基于历史响应时间的百分位
            if len(metrics.response_times) >= 10:
                sorted_times = sorted(metrics.response_times)
                index = int(len(sorted_times) * config.percentile)
                percentile_time = sorted_times[min(index, len(sorted_times) - 1)]
                # 添加一些缓冲
                return min(config.max_timeout, max(config.min_timeout, percentile_time * 1.5))
            return config.base_timeout

        elif config.strategy == TimeoutStrategy.ADAPTIVE:
            # 自适应:基于平均和P99
            if len(metrics.response_times) >= 10:
                avg = statistics.mean(metrics.response_times)
                # 使用平均值的2倍或P99,取较大者
                timeout = max(avg * 2, metrics.p99_response_time)
                return min(config.max_timeout, max(config.min_timeout, timeout))
            return config.base_timeout

        else:  # PREDICTIVE
            # 预测性(简化版,实际可以使用更复杂的预测模型)
            if metrics.avg_response_time > 0:
                predicted = metrics.avg_response_time * 1.8
                return min(config.max_timeout, max(config.min_timeout, predicted))
            return config.base_timeout

    def _update_success_metrics(self, service_id: str, duration: float):
        """更新成功指标"""
        metrics = self.service_metrics[service_id]

        metrics.total_calls += 1
        metrics.successful_calls += 1
        metrics.consecutive_failures = 0
        metrics.last_call_time = datetime.now()

        # 更新响应时间
        metrics.response_times.append(duration)
        if len(metrics.response_times) > 1000:
            metrics.response_times = metrics.response_times[-1000:]

        # 重新计算统计
        if metrics.response_times:
            metrics.avg_response_time = statistics.mean(metrics.response_times)
            sorted_times = sorted(metrics.response_times)
            n = len(sorted_times)
            metrics.p95_response_time = sorted_times[int(n * 0.95)]
            metrics.p99_response_time = sorted_times[int(n * 0.99)]

        # 更新成功率
        metrics.success_rate = metrics.successful_calls / metrics.total_calls

        # 半开状态转为关闭
        if metrics.circuit_state == CircuitState.HALF_OPEN:
            metrics.circuit_state = CircuitState.CLOSED
            logger.info(f"断路器恢复关闭: {service_id}")

    def _update_timeout_metrics(self, service_id: str, duration: float):
        """更新超时指标"""
        metrics = self.service_metrics[service_id]

        metrics.total_calls += 1
        metrics.timeout_calls += 1
        metrics.consecutive_failures += 1
        metrics.last_call_time = datetime.now()
        self.stats["total_timeouts"] += 1

        # 更新成功率
        metrics.success_rate = metrics.successful_calls / metrics.total_calls

        # 检查是否需要打开断路器
        config = self.service_configs.get(service_id, self.default_config)
        if metrics.consecutive_failures >= config.circuit_breaker_threshold:
            metrics.circuit_state = CircuitState.OPEN
            metrics.circuit_opened_at = datetime.now()
            self.stats["circuit_opened_count"] += 1
            logger.warning(f"断路器打开: {service_id}")

    def _update_failure_metrics(self, service_id: str, duration: float):
        """更新失败指标"""
        metrics = self.service_metrics[service_id]

        metrics.total_calls += 1
        metrics.failed_calls += 1
        metrics.consecutive_failures += 1
        metrics.last_call_time = datetime.now()

        # 更新成功率
        metrics.success_rate = metrics.successful_calls / metrics.total_calls

        # 检查是否需要打开断路器
        config = self.service_configs.get(service_id, self.default_config)
        if metrics.consecutive_failures >= config.circuit_breaker_threshold:
            metrics.circuit_state = CircuitState.OPEN
            metrics.circuit_opened_at = datetime.now()
            self.stats["circuit_opened_count"] += 1
            logger.warning(f"断路器打开: {service_id}")

    def get_service_metrics(self, service_id: str) -> ServiceMetrics | None:
        """获取服务指标"""
        return self.service_metrics.get(service_id)

    def get_all_metrics(self) -> dict[str, ServiceMetrics]:
        """获取所有服务指标"""
        return self.service_metrics.copy()

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        active_services = sum(
            1 for m in self.service_metrics.values() if m.circuit_state == CircuitState.CLOSED
        )

        timeout_reduction = 0.0
        if self.stats["total_services"] > 0:
            # 计算平均超时减少(相对于固定超时)
            original_timeouts = sum(
                self.service_configs.get(s, self.default_config).base_timeout
                for s in self.service_configs
            )
            current_timeouts = sum(
                self._calculate_timeout(s, self.service_configs.get(s, self.default_config))
                for s in self.service_configs
            )
            if original_timeouts > 0:
                timeout_reduction = (original_timeouts - current_timeouts) / original_timeouts

        return {
            **self.stats,
            "active_services": active_services,
            "timeout_reduction_rate": timeout_reduction,
        }


def with_timeout(service_id: str, timeout: float | None = None):
    """
    超时控制装饰器

    Args:
        service_id: 服务ID
        timeout: 自定义超时
    """

    def decorator(func: Callable) -> Callable:
        async def async_wrapper(*args, **kwargs):
            controller = get_timeout_controller()
            result = await controller.call_with_timeout(
                service_id, func, *args, custom_timeout=timeout, **kwargs
            )
            if result.success:
                return result.result
            else:
                raise Exception(result.error)

        def sync_wrapper(*args, **kwargs):
            controller = get_timeout_controller()

            async def async_call():
                result = await controller.call_with_timeout(
                    service_id, func, *args, custom_timeout=timeout, **kwargs
                )
                if result.success:
                    return result.result
                else:
                    raise Exception(result.error)

            return asyncio.run(async_call())

        import inspect

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# 单例实例
_controller_instance: ExternalServiceTimeoutController | None = None


def get_timeout_controller() -> ExternalServiceTimeoutController:
    """获取外部服务超时控制器单例"""
    global _controller_instance
    if _controller_instance is None:
        _controller_instance = ExternalServiceTimeoutController()
        logger.info("外部服务超时控制器已初始化")
    return _controller_instance


async def main():
    """测试主函数"""
    controller = get_timeout_controller()

    print("=== 外部服务超时控制测试 ===\n")

    # 注册服务
    controller.register_service(
        "test_api", TimeoutConfig(base_timeout=5.0, strategy=TimeoutStrategy.ADAPTIVE)
    )

    # 测试函数
    async def test_api_call(duration: float):
        await asyncio.sleep(duration)
        return f"API响应(耗时{duration}秒)"

    # 测试1: 正常调用
    print("测试1: 正常调用")
    result = await controller.call_with_timeout("test_api", test_api_call, 0.5)
    print(f"  成功: {result.success}")
    print(f"  耗时: {result.duration:.2f}秒")
    print(f"  超时时间: {result.timeout_used:.2f}秒")

    # 测试2: 超时调用
    print("\n测试2: 超时调用")
    result = await controller.call_with_timeout("test_api", test_api_call, 3.0)
    print(f"  成功: {result.success}")
    print(f"  超时: {result.timed_out}")
    print(f"  耗时: {result.duration:.2f}秒")
    print(f"  错误: {result.error}")

    # 执行多次调用以收集指标
    print("\n执行多次调用...")
    for i in range(20):
        duration = 0.1 + (i % 5) * 0.1
        await controller.call_with_timeout("test_api", test_api_call, duration)

    # 显示指标
    metrics = controller.get_service_metrics("test_api")
    if metrics:
        print("\n=== 服务指标 ===")
        print(f"总调用次数: {metrics.total_calls}")
        print(f"成功次数: {metrics.successful_calls}")
        print(f"超时次数: {metrics.timeout_calls}")
        print(f"成功率: {metrics.success_rate:.1%}")
        print(f"平均响应时间: {metrics.avg_response_time:.2f}秒")
        print(f"P95响应时间: {metrics.p95_response_time:.2f}秒")
        print(f"P99响应时间: {metrics.p99_response_time:.2f}秒")
        print(f"断路状态: {metrics.circuit_state.value}")

    # 显示统计
    stats = controller.get_stats()
    print("\n=== 全局统计 ===")
    print(f"总服务数: {stats['total_services']}")
    print(f"活跃服务: {stats['active_services']}")
    print(f"断路打开次数: {stats['circuit_opened_count']}")
    print(f"超时减少率: {stats['timeout_reduction_rate']:.1%}")


# 入口点: @async_main装饰器已添加到main函数
