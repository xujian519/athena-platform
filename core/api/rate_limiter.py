#!/usr/bin/env python3
from __future__ import annotations
"""
API限流控制模块
Rate Limiter for API Calls

提供请求重试、并发控制、速率限制等功能
"""

import asyncio
import logging
import os
import random
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from threading import Lock
from typing import Any

logger = logging.getLogger(__name__)


class RateLimitError(Exception):
    """限流错误"""

    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class BackoffStrategy(Enum):
    """退避策略"""

    FIXED = "fixed"  # 固定延迟
    LINEAR = "linear"  # 线性增长
    EXPONENTIAL = "exponential"  # 指数退避
    RANDOMIZED = "randomized"  # 随机退避


@dataclass
class RetryConfig:
    """重试配置"""

    max_retries: int = 3  # 最大重试次数
    base_delay: float = 1.0  # 基础延迟(秒)
    max_delay: float = 60.0  # 最大延迟(秒)
    backoff_strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL
    jitter: bool = True  # 添加随机抖动
    jitter_range: float = 0.5  # 抖动范围(±0.5秒)

    # 可重试的HTTP状态码
    retryable_status_codes: list[int] = field(default_factory=lambda: [429, 502, 503, 504])

    # 可重试的错误代码
    retryable_error_codes: list[str] = field(default_factory=lambda: ["1302", "1301"])


@dataclass
class RateLimitConfig:
    """速率限制配置"""

    max_concurrent: int = 3  # 最大并发数
    requests_per_second: float = 2.0  # 每秒请求数
    requests_per_minute: int = 100  # 每分钟请求数


class TokenBucket:
    """令牌桶算法实现"""

    def __init__(self, rate: float, capacity: int):
        """
        Args:
            rate: 令牌生成速率(令牌/秒)
            capacity: 桶容量(最大令牌数)
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self._lock = Lock()

    def acquire(self, tokens: int = 1, timeout: float | None = None) -> bool:
        """
        获取令牌

        Args:
            tokens: 需要的令牌数量
            timeout: 超时时间(秒),None表示不等待

        Returns:
            是否成功获取令牌
        """
        with self._lock:
            now = time.time()
            # 补充令牌
            elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now

            # 检查是否有足够令牌
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True

            return False

    def wait_for_token(self, tokens: int = 1, max_wait: float = 60.0) -> bool:
        """等待直到有足够令牌"""
        start_time = time.time()
        while time.time() - start_time < max_wait:
            if self.acquire(tokens):
                return True
            time.sleep(0.1)
        return False


class SlidingWindowRateLimiter:
    """滑动窗口速率限制器"""

    def __init__(self, max_requests: int, window_seconds: int):
        """
        Args:
            max_requests: 时间窗口内最大请求数
            window_seconds: 时间窗口(秒)
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: deque = deque()
        self._lock = Lock()

    def acquire(self) -> bool:
        """尝试获取请求许可"""
        with self._lock:
            now = time.time()

            # 移除时间窗口外的请求
            while self.requests and self.requests[0] <= now - self.window_seconds:
                self.requests.popleft()

            # 检查是否超过限制
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True

            return False

    def get_wait_time(self) -> float:
        """获取需要等待的时间"""
        with self._lock:
            if not self.requests or len(self.requests) < self.max_requests:
                return 0.0

            oldest_request = self.requests[0]
            wait_time = self.window_seconds - (time.time() - oldest_request)
            return max(0.0, wait_time)


class APIRateLimiter:
    """API限流控制器"""

    def __init__(
        self,
        retry_config: RetryConfig | None = None,
        rate_limit_config: RateLimitConfig | None = None,
    ):
        """
        Args:
            retry_config: 重试配置
            rate_limit_config: 速率限制配置
        """
        self.retry_config = retry_config or RetryConfig()
        self.rate_limit_config = rate_limit_config or RateLimitConfig()

        # 创建限流器
        self._token_bucket = TokenBucket(
            rate=self.rate_limit_config.requests_per_second,
            capacity=int(self.rate_limit_config.requests_per_second * 2),
        )

        self._minute_limiter = SlidingWindowRateLimiter(
            max_requests=self.rate_limit_config.requests_per_minute, window_seconds=60
        )

        # 并发控制
        self._semaphore = asyncio.Semaphore(self.rate_limit_config.max_concurrent)
        self._active_requests = 0
        self._request_lock = Lock()

        # 统计信息
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "rate_limited": 0,
            "retried_requests": 0,
        }

    def calculate_delay(self, attempt: int) -> float:
        """计算重试延迟"""
        config = self.retry_config

        if config.backoff_strategy == BackoffStrategy.FIXED:
            delay = config.base_delay
        elif config.backoff_strategy == BackoffStrategy.LINEAR:
            delay = config.base_delay * (attempt + 1)
        elif config.backoff_strategy == BackoffStrategy.EXPONENTIAL:
            delay = config.base_delay * (2**attempt)
        else:  # RANDOMIZED
            delay = config.base_delay * random.uniform(1, attempt + 2)

        # 添加随机抖动
        if config.jitter:
            jitter = random.uniform(-config.jitter_range, config.jitter_range)
            delay += jitter

        return min(delay, config.max_delay)

    def should_retry(self, exception: Exception) -> bool:
        """判断是否应该重试"""
        error_str = str(exception)

        # 检查错误代码
        for code in self.retry_config.retryable_error_codes:
            if code in error_str:
                return True

        # 检查HTTP状态码
        return any(str(status) in error_str for status in self.retry_config.retryable_status_codes)

    def wait_for_rate_limit(self) -> None:
        """等待速率限制"""
        # 等待令牌桶
        while not self._token_bucket.acquire():
            time.sleep(0.1)

        # 等待滑动窗口
        while not self._minute_limiter.acquire():
            wait_time = self._minute_limiter.get_wait_time()
            if wait_time > 0:
                logger.debug(f"速率限制中,等待 {wait_time:.2f} 秒...")
                time.sleep(min(wait_time, 1.0))

    def sync_call_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """同步调用(带重试)"""
        for attempt in range(self.retry_config.max_retries + 1):
            try:
                # 等待速率限制
                if attempt > 0:
                    delay = self.calculate_delay(attempt - 1)
                    logger.info(f"重试第 {attempt} 次,等待 {delay:.2f} 秒...")
                    time.sleep(delay)
                else:
                    self.wait_for_rate_limit()

                # 更新统计
                self.stats["total_requests"] += 1
                with self._request_lock:
                    self._active_requests += 1

                # 执行调用
                result = func(*args, **kwargs)

                # 成功
                self.stats["successful_requests"] += 1
                return result

            except Exception as e:
                self.stats["failed_requests"] += 1

                # 检查是否应该重试
                if attempt < self.retry_config.max_retries and self.should_retry(e):
                    self.stats["retried_requests"] += 1
                    logger.warning(f"请求失败(可重试): {e}")
                    continue
                else:
                    # 不重试,抛出异常
                    raise

            finally:
                with self._request_lock:
                    self._active_requests -= 1

    async def async_call_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """异步调用(带重试和并发控制)"""
        async with self._semaphore:
            for attempt in range(self.retry_config.max_retries + 1):
                try:
                    # 等待速率限制
                    if attempt > 0:
                        delay = self.calculate_delay(attempt - 1)
                        logger.info(f"重试第 {attempt} 次,等待 {delay:.2f} 秒...")
                        await asyncio.sleep(delay)
                    else:
                        # 在异步中等待令牌
                        await asyncio.get_event_loop().run_in_executor(
                            None, self.wait_for_rate_limit
                        )

                    # 更新统计
                    self.stats["total_requests"] += 1

                    # 执行调用
                    if asyncio.iscoroutinefunction(func):
                        result = await func(*args, **kwargs)
                    else:
                        result = func(*args, **kwargs)

                    # 成功
                    self.stats["successful_requests"] += 1
                    return result

                except Exception as e:
                    self.stats["failed_requests"] += 1

                    # 检查是否应该重试
                    if attempt < self.retry_config.max_retries and self.should_retry(e):
                        self.stats["retried_requests"] += 1
                        logger.warning(f"请求失败(可重试): {e}")
                        continue
                    else:
                        # 不重试,抛出异常
                        raise

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        success_rate = (
            self.stats["successful_requests"] / self.stats["total_requests"] * 100
            if self.stats["total_requests"] > 0
            else 0
        )

        return {
            **self.stats,
            "active_requests": self._active_requests,
            "success_rate": f"{success_rate:.2f}%",
        }

    def reset_stats(self) -> None:
        """重置统计信息"""
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "rate_limited": 0,
            "retried_requests": 0,
        }


# 便捷装饰器
def rate_limited(max_retries: int = 3, max_concurrent: int = 3, requests_per_second: float = 2.0):
    """
    限流装饰器

    Usage:
        @rate_limited(max_retries=3, max_concurrent=2)
        def call_api(prompt):
            return api_call(prompt)
    """
    limiter = APIRateLimiter(
        retry_config=RetryConfig(max_retries=max_retries),
        rate_limit_config=RateLimitConfig(
            max_concurrent=max_concurrent, requests_per_second=requests_per_second
        ),
    )

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            return limiter.sync_call_with_retry(func, *args, **kwargs)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await limiter.async_call_with_retry(func, *args, **kwargs)

        # 根据函数类型返回对应的包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# 全局限流器实例(默认配置)
_default_limiter: APIRateLimiter | None = None


def get_default_limiter() -> APIRateLimiter:
    """获取默认限流器"""
    global _default_limiter
    if _default_limiter is None:
        _default_limiter = APIRateLimiter()
    return _default_limiter


# 便捷函数
def call_with_retry(func: Callable, *args, **kwargs) -> Any:
    """使用默认限流器调用函数"""
    return get_default_limiter().sync_call_with_retry(func, *args, **kwargs)


async def async_call_with_retry(func: Callable, *args, **kwargs) -> Any:
    """使用默认限流器异步调用函数"""
    return await get_default_limiter().async_call_with_retry(func, *args, **kwargs)


if __name__ == "__main__":
    # 测试代码
    import zhipuai

    # 创建智谱AI客户端(带限流)
    @rate_limited(max_retries=3, max_concurrent=2)
    def call_zhipu_api(prompt: str) -> Any:
        client = zhipuai.ZhipuAI(api_key=os.getenv("ZHIPU_API_KEY"))
        response = client.chat.completions.create(
            model="glm-4", messages=[{"role": "user", "content": prompt}]
        )
        return response

    # 测试调用
    result = call_zhipu_api("你好")
    print(result)
