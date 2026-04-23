#!/usr/bin/env python3
from __future__ import annotations
"""
熔断器模块
Circuit Breaker for Athena Intelligent Router

提供熔断器模式实现,防止级联故障

作者: 小诺AI团队
创建时间: 2025-01-09
"""

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """熔断器状态"""

    CLOSED = "closed"  # 正常状态
    OPEN = "open"  # 熔断状态
    HALF_OPEN = "half_open"  # 半开状态


@dataclass
class CircuitBreakerConfig:
    """熔断器配置"""

    failure_threshold: int = 5  # 失败阈值
    recovery_timeout: int = 60  # 恢复超时(秒)
    expected_exception: Exception = Exception  # 预期异常类型
    timeout: int = 30  # 执行超时


class CircuitBreaker:
    """
    熔断器实现

    状态转换:
        CLOSED → OPEN: 失败次数达到阈值
        OPEN → HALF_OPEN: 超时后尝试恢复
        HALF_OPEN → CLOSED: 成功恢复
        HALF_OPEN → OPEN: 恢复失败
    """

    def __init__(self, name: str, config: CircuitBreakerConfig | None = None):
        """
        初始化熔断器

        Args:
            name: 熔断器名称
            config: 熔断器配置
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.opened_at: Optional[float] = None

        logger.info(
            f"✅ 熔断器初始化: {name}, "
            f"failure_threshold={self.config.failure_threshold}, "
            f"recovery_timeout={self.config.recovery_timeout}s"
        )

    def _should_attempt_reset(self) -> bool:
        """检查是否应该尝试重置"""
        if self.opened_at is None:
            return False

        elapsed = time.time() - self.opened_at
        return elapsed >= self.config.recovery_timeout

    def _handle_failure(self) -> Any:
        """处理失败"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN
            self.opened_at = time.time()
            logger.warning(
                f"⚠️ 熔断器打开: {self.name}, "
                f"failure_count={self.failure_count}, "
                f"threshold={self.config.failure_threshold}"
            )

    def _handle_success(self) -> Any:
        """处理成功"""
        self.failure_count = 0
        self.last_failure_time = None

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= 2:  # 连续2次成功才关闭
                self.state = CircuitState.CLOSED
                self.success_count = 0
                self.opened_at = None
                logger.info(f"✅ 熔断器关闭: {self.name}")

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        通过熔断器调用函数

        Args:
            func: 要调用的函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            函数执行结果

        Raises:
            CircuitBreakerOpenError: 熔断器打开时的异常
        """
        # 检查状态
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info(f"🔄 熔断器半开: {self.name}")
            else:
                raise CircuitBreakerOpenError(
                    f"熔断器打开: {self.name}, "
                    f"将在 {int(self.config.recovery_timeout - (time.time() - self.opened_at))} 秒后尝试恢复"
                )

        try:
            # 执行函数
            result = func(*args, **kwargs)
            self._handle_success()
            return result

        except self.config.expected_exception as e:
            self._handle_failure()
            raise e

        except Exception as e:
            # 未预期的异常也计数
            self._handle_failure()
            raise e

    def get_state(self) -> dict:
        """获取熔断器状态"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
            "opened_at": self.opened_at,
            "can_attempt_reset": (
                self._should_attempt_reset() if self.state == CircuitState.OPEN else None
            ),
        }


class CircuitBreakerOpenError(Exception):
    """熔断器打开异常"""

    pass


# 全局熔断器注册表
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str, config: CircuitBreakerConfig | None = None) -> CircuitBreaker:
    """
    获取或创建熔断器

    Args:
        name: 熔断器名称
        config: 熔断器配置

    Returns:
        CircuitBreaker实例
    """
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name, config)
    return _circuit_breakers[name]


def circuit_breaker_decorator(name: str, failure_threshold: int = 5, recovery_timeout: int = 60):
    """
    熔断器装饰器

    Usage:
        @circuit_breaker_decorator("qdrant_search", failure_threshold=5, recovery_timeout=60)
        def search_qdrant(query):
            # 搜索逻辑
            pass
    """

    def decorator(func) -> None:
        def wrapper(*args, **kwargs) -> Any:
            breaker = get_circuit_breaker(
                name,
                CircuitBreakerConfig(
                    failure_threshold=failure_threshold, recovery_timeout=recovery_timeout
                ),
            )
            return breaker.call(func, *args, **kwargs)

        return wrapper

    return decorator


# 导出
__all__ = [
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerOpenError",
    "CircuitState",
    "circuit_breaker_decorator",
    "get_circuit_breaker",
]
