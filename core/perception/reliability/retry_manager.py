#!/usr/bin/env python3
"""
Athena 感知模块 - 企业级重试管理器
支持指数退避、智能重试、重试限制
最后更新: 2026-01-26
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Optional, Callable, Any, List, Type, Dict
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """重试策略"""
    FIXED = "fixed"           # 固定间隔
    LINEAR = "linear"         # 线性增长
    EXPONENTIAL = "exponential"  # 指数退避
    CUSTOM = "custom"         # 自定义


@dataclass
class RetryConfig:
    """重试配置"""
    max_attempts: int = 3              # 最大重试次数
    base_delay: float = 1.0            # 基础延迟（秒）
    max_delay: float = 60.0            # 最大延迟（秒）
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    backoff_multiplier: float = 2.0    # 退避倍数
    jitter: bool = True                # 添加随机抖动
    jitter_range: float = 0.1          # 抖动范围（0-1）
    retry_on: List[Type[Exception]] = field(default_factory=list)
    stop_on: List[Type[Exception]] = field(default_factory=list)


@dataclass
class RetryResult:
    """重试结果"""
    success: bool
    attempts: int
    total_duration: float
    result: Any = None
    error: Exception | None = None
    retry_history: List[Dict[str, Any]] = field(default_factory=list)


class RetryManager:
    """
    企业级重试管理器

    功能：
    - 指数退避重试
    - 智能重试判断
    - 重试限制
    - 重试统计
    - 可重试异常检测
    """

    def __init__(self):
        """初始化重试管理器"""
        # 重试统计
        self.stats = {
            "total_attempts": 0,
            "total_successes": 0,
            "total_failures": 0,
            "total_retries": 0
        }

        logger.info("✓ 重试管理器已初始化")

    async def execute_with_retry(
        self,
        func: Callable,
        config: RetryConfig | None = None,
        *args,
        **kwargs
    ) -> RetryResult:
        """
        执行带重试的函数

        Args:
            func: 要执行的函数
            config: 重试配置
            *args: 函数参数
            **kwargs: 函数关键字参数

        Returns:
            重试结果
        """
        config = config or RetryConfig()

        attempts = 0
        start_time = datetime.now()
        history = []
        last_error = None
        result = None

        while attempts < config.max_attempts:
            attempts += 1
            attempt_start = datetime.now()

            try:
                # 执行函数
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                # 成功
                duration = (datetime.now() - attempt_start).total_seconds()

                history.append({
                    "attempt": attempts,
                    "success": True,
                    "duration": duration,
                    "timestamp": attempt_start.isoformat()
                })

                self.stats["total_attempts"] += attempts
                self.stats["total_successes"] += 1

                logger.info(f"✓ 重试成功: 第{attempts}次尝试, 耗时{duration:.2f}秒")

                return RetryResult(
                    success=True,
                    attempts=attempts,
                    total_duration=(datetime.now() - start_time).total_seconds(),
                    result=result,
                    retry_history=history
                )

            except Exception as e:
                last_error = e
                duration = (datetime.now() - attempt_start).total_seconds()

                # 检查是否应该停止重试
                if type(e) in config.stop_on:
                    logger.warning(f"⚠️ 遇到不可重试错误，停止重试: {type(e).__name__}")
                    break

                # 检查是否是最后一次尝试
                if attempts >= config.max_attempts:
                    logger.warning(f"⚠️ 达到最大重试次数({config.max_attempts})")
                    break

                # 计算延迟
                delay = self._calculate_delay(config, attempts)

                history.append({
                    "attempt": attempts,
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "duration": duration,
                    "retry_after": delay,
                    "timestamp": attempt_start.isoformat()
                })

                logger.warning(
                    f"⚠️ 尝试{attempts}失败: {type(e).__name__} - {e} | "
                    f"{delay:.2f}秒后重试..."
                )

                # 等待后重试
                await asyncio.sleep(delay)

        # 所有尝试都失败
        total_duration = (datetime.now() - start_time).total_seconds()

        self.stats["total_attempts"] += attempts
        self.stats["total_failures"] += 1
        self.stats["total_retries"] += attempts - 1

        logger.error(f"❌ 重试失败: {attempts}次尝试后仍然失败")

        return RetryResult(
            success=False,
            attempts=attempts,
            total_duration=total_duration,
            error=last_error,
            retry_history=history
        )

    def _calculate_delay(self, config: RetryConfig, attempt: int) -> float:
        """
        计算重试延迟

        Args:
            config: 重试配置
            attempt: 当前尝试次数

        Returns:
            延迟时间（秒）
        """
        # 计算基础延迟
        if config.strategy == RetryStrategy.FIXED:
            delay = config.base_delay
        elif config.strategy == RetryStrategy.LINEAR:
            delay = config.base_delay * attempt
        elif config.strategy == RetryStrategy.EXPONENTIAL:
            delay = config.base_delay * (config.backoff_multiplier ** (attempt - 1))
        else:
            delay = config.base_delay

        # 限制最大延迟
        delay = min(delay, config.max_delay)

        # 添加抖动
        if config.jitter:
            jitter_amount = delay * config.jitter_range
            jitter = random.uniform(-jitter_amount, jitter_amount)
            delay = max(0, delay + jitter)

        return delay

    async def execute_batch_with_retry(
        self,
        func: Callable,
        items: List[Any],
        config: RetryConfig | None = None,
        *args,
        **kwargs
    ) -> List[RetryResult]:
        """
        批量执行带重试的函数

        Args:
            func: 要执行的函数
            items: 要处理的项目列表
            config: 重试配置
            *args: 函数参数
            **kwargs: 函数关键字参数

        Returns:
            重试结果列表
        """
        results = []

        for item in items:
            try:
                result = await self.execute_with_retry(
                    func,
                    config,
                    item,
                    *args,
                    **kwargs
                )
                results.append(result)
            except Exception as e:
                logger.error(f"批量处理项失败: {e}")
                results.append(RetryResult(
                    success=False,
                    attempts=0,
                    total_duration=0,
                    error=e
                ))

        return results

    def get_stats(self) -> Dict[str, Any]:
        """
        获取重试统计

        Returns:
            统计信息字典
        """
        success_rate = 0
        if self.stats["total_attempts"] > 0:
            success_rate = self.stats["total_successes"] / self.stats["total_attempts"]

        avg_attempts = 0
        if self.stats["total_successes"] > 0:
            avg_attempts = self.stats["total_attempts"] / self.stats["total_successes"]

        return {
            "total_attempts": self.stats["total_attempts"],
            "total_successes": self.stats["total_successes"],
            "total_failures": self.stats["total_failures"],
            "total_retries": self.stats["total_retries"],
            "success_rate": success_rate,
            "avg_attempts_per_success": avg_attempts
        }

    def reset_stats(self):
        """重置统计"""
        self.stats = {
            "total_attempts": 0,
            "total_successes": 0,
            "total_failures": 0,
            "total_retries": 0
        }
        logger.info("✓ 重试统计已重置")


def retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    backoff_multiplier: float = 2.0,
    retry_on: Optional[List[Type[Exception]]] | None = None
):
    """
    重试装饰器

    Args:
        max_attempts: 最大尝试次数
        base_delay: 基础延迟
        strategy: 重试策略
        backoff_multiplier: 退避倍数
        retry_on: 可重试的异常类型列表
    """
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            config = RetryConfig(
                max_attempts=max_attempts,
                base_delay=base_delay,
                strategy=strategy,
                backoff_multiplier=backoff_multiplier,
                retry_on=retry_on or []
            )

            # 获取重试管理器（从参数或创建新的）
            retry_mgr = kwargs.pop('retry_manager', None) or RetryManager()

            result = await retry_mgr.execute_with_retry(
                func,
                config,
                *args,
                **kwargs
            )

            if result.success:
                return result.result
            else:
                raise result.error

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 同步函数暂不支持重试
            return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# 使用示例
if __name__ == "__main__":
    import asyncio
    import functools

    async def test_retry_manager():
        manager = RetryManager()

        # 测试1: 成功的重试
        print("\n=== 测试1: 成功的重试 ===")
        attempts = [0]

        async def flaky_function():
            attempts[0] += 1
            if attempts[0] < 3:
                raise ConnectionError("连接失败")
            return "成功!"

        result = await manager.execute_with_retry(
            flaky_function,
            RetryConfig(max_attempts=5, base_delay=0.1)
        )
        print(f"结果: {result}")
        print(f"尝试次数: {result.attempts}")

        # 测试2: 失败的重试
        print("\n=== 测试2: 失败的重试 ===")
        attempts2 = [0]

        async def always_fail_function():
            attempts2[0] += 1
            raise ValueError("总是失败")

        result = await manager.execute_with_retry(
            always_fail_function,
            RetryConfig(max_attempts=3, base_delay=0.1)
        )
        print(f"成功: {result.success}")
        print(f"尝试次数: {result.attempts}")
        print(f"历史记录: {len(result.retry_history)}条")

        # 测试3: 使用装饰器
        print("\n=== 测试3: 使用装饰器 ===")
        attempts3 = [0]

        @retry(max_attempts=3, base_delay=0.1)
        async def decorated_function():
            attempts3[0] += 1
            if attempts3[0] < 2:
                raise ConnectionError("连接失败")
            return "装饰器成功!"

        try:
            result = await decorated_function()
            print(f"结果: {result}")
        except Exception as e:
            print(f"失败: {e}")

        # 显示统计
        print("\n=== 重试统计 ===")
        stats = manager.get_stats()
        for key, value in stats.items():
            print(f"{key}: {value}")

    asyncio.run(test_retry_manager())
