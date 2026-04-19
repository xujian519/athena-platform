#!/usr/bin/env python3
from __future__ import annotations
"""
速率限制器
Rate Limiter

防止工具调用被滥用,实现多种速率限制策略。

作者: Athena平台团队
创建时间: 2026-01-25
版本: v1.0.0
"""

import asyncio
import logging
import time
from collections import deque
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RateLimitStrategy(Enum):
    """速率限制策略"""

    # 固定窗口:在固定时间窗口内限制调用次数
    FIXED_WINDOW = "fixed_window"
    # 滑动窗口:使用滑动时间窗口
    SLIDING_WINDOW = "sliding_window"
    # 令牌桶:基于令牌桶算法
    TOKEN_BUCKET = "token_bucket"


@dataclass
class RateLimitConfig:
    """速率限制配置"""

    max_calls: int = 100  # 最大调用次数
    period: float = 60.0  # 时间窗口(秒)
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW


class RateLimiter:
    """
    速率限制器

    防止API或工具被过度调用,保护系统资源。

    支持多种速率限制策略:
    1. 固定窗口:简单但可能在窗口边界有问题
    2. 滑动窗口:更平滑的限流
    3. 令牌桶:允许突发流量
    """

    def __init__(
        self,
        max_calls: int = 100,
        period: float = 60.0,
        strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW,
    ):
        """
        初始化速率限制器

        Args:
            max_calls: 时间窗口内允许的最大调用次数
            period: 时间窗口长度(秒)
            strategy: 限流策略
        """
        self.max_calls = max_calls
        self.period = period
        self.strategy = strategy

        # 滑动窗口:存储调用时间戳
        self._calls: deque = deque()

        # 令牌桶:令牌数量和上次填充时间
        self._tokens: float = float(max_calls)
        self._last_refill: float = time.time()

        # 线程锁
        self._lock = asyncio.Lock()

        logger.info(
            f"🚦 速率限制器初始化完成 (最大{max_calls}次/{period}秒, 策略:{strategy.value})"
        )

    async def acquire(self, timeout: float | None = None) -> bool:
        """
        获取调用许可

        Args:
            timeout: 最大等待时间(秒),None表示不等待直接返回

        Returns:
            是否获取到许可

        Raises:
            asyncio.TimeoutError: 如果在timeout时间内未获取到许可
        """
        async with self._lock:
            if self.strategy == RateLimitStrategy.FIXED_WINDOW:
                return await self._acquire_fixed_window(timeout)
            elif self.strategy == RateLimitStrategy.SLIDING_WINDOW:
                return await self._acquire_sliding_window(timeout)
            elif self.strategy == RateLimitStrategy.TOKEN_BUCKET:
                return await self._acquire_token_bucket(timeout)
            else:
                raise ValueError(f"未知的限流策略: {self.strategy}")

    async def _acquire_fixed_window(self, timeout: float) -> bool:
        """固定窗口策略"""
        now = time.time()

        # 清理过期记录
        window_start = now - self.period
        while self._calls and self._calls[0] < window_start:
            self._calls.popleft()

        # 检查是否超过限制
        if len(self._calls) >= self.max_calls:
            if timeout is None:
                return False

            # 计算需要等待的时间
            sleep_time = self._calls[0] + self.period - now
            if sleep_time > timeout:
                return False

            # 等待
            await asyncio.sleep(sleep_time)

        # 记录调用
        self._calls.append(now)
        return True

    async def _acquire_sliding_window(self, timeout: float,) -> bool:
        """滑动窗口策略"""
        now = time.time()

        # 清理过期记录
        window_start = now - self.period
        while self._calls and self._calls[0] < window_start:
            self._calls.popleft()

        # 检查是否超过限制
        if len(self._calls) >= self.max_calls:
            if timeout is None:
                logger.warning(f"🚫 速率限制:{len(self._calls)}/{self.max_calls}")
                return False

            # 计算需要等待的时间
            sleep_time = self._calls[0] + self.period - now
            if sleep_time > timeout:
                logger.warning(f"🚫 速率限制:需要等待{sleep_time:.2f}秒,超时{timeout}秒")
                return False

            # 等待
            logger.info(f"⏳ 速率限制:等待{sleep_time:.2f}秒...")
            await asyncio.sleep(sleep_time)

            # 重新清理
            window_start = time.time() - self.period
            while self._calls and self._calls[0] < window_start:
                self._calls.popleft()

        # 记录调用
        self._calls.append(now)
        return True

    async def _acquire_token_bucket(self, timeout: float,) -> bool:
        """令牌桶策略"""
        now = time.time()

        # 填充令牌
        time_passed = now - self._last_refill
        tokens_to_add = time_passed * (self.max_calls / self.period)
        self._tokens = min(self.max_calls, self._tokens + tokens_to_add)
        self._last_refill = now

        # 检查是否有足够的令牌
        if self._tokens < 1:
            if timeout is None:
                logger.warning(f"🚫 令牌桶空:{self._tokens:.2f}/{self.max_calls}")
                return False

            # 计算需要等待的时间
            wait_time = (1 - self._tokens) * (self.period / self.max_calls)
            if wait_time > timeout:
                logger.warning(f"🚫 令牌桶空:需要等待{wait_time:.2f}秒,超时{timeout}秒")
                return False

            # 等待
            logger.info(f"⏳ 令牌桶:等待{wait_time:.2f}秒...")
            await asyncio.sleep(wait_time)

            # 重新填充
            now = time.time()
            time_passed = now - self._last_refill
            tokens_to_add = time_passed * (self.max_calls / self.period)
            self._tokens = min(self.max_calls, self._tokens + tokens_to_add)
            self._last_refill = now

        # 消耗一个令牌
        self._tokens -= 1
        return True

    def get_stats(self) -> dict[str, any]:
        """获取速率限制统计"""
        window_start = time.time() - self.period
        recent_calls = sum(1 for t in self._calls if t > window_start)

        return {
            "strategy": self.strategy.value,
            "max_calls": self.max_calls,
            "period": self.period,
            "recent_calls": recent_calls,
            "remaining": max(0, self.max_calls - recent_calls),
            "tokens": self._tokens if self.strategy == RateLimitStrategy.TOKEN_BUCKET else None,
        }

    def reset(self):
        """重置速率限制器"""
        self._calls.clear()
        self._tokens = float(self.max_calls)
        self._last_refill = time.time()
        logger.info("🔄 速率限制器已重置")


class MultiRateLimiter:
    """
    多级速率限制器

    支持为不同的工具或用户设置不同的速率限制。
    """

    def __init__(self):
        """初始化多级速率限制器"""
        self.limiters: dict[str, RateLimiter] = {}
        self._lock = asyncio.Lock()
        logger.info("🚦 多级速率限制器初始化完成")

    async def get_limiter(
        self,
        key: str,
        max_calls: int = 100,
        period: float = 60.0,
        strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW,
    ) -> RateLimiter:
        """
        获取或创建指定key的速率限制器

        Args:
            key: 限制器标识(如工具名、用户ID等)
            max_calls: 最大调用次数
            period: 时间窗口
            strategy: 限流策略

        Returns:
            RateLimiter实例
        """
        async with self._lock:
            if key not in self.limiters:
                self.limiters[key] = RateLimiter(max_calls, period, strategy)
                logger.info(f"✅ 创建速率限制器: {key}")
            return self.limiters[key]

    async def acquire(
        self, key: str, timeout: float | None = None, max_calls: int = 100, period: float = 60.0
    ) -> bool:
        """
        获取调用许可

        Args:
            key: 限制器标识
            timeout: 最大等待时间
            max_calls: 最大调用次数
            period: 时间窗口

        Returns:
            是否获取到许可
        """
        limiter = await self.get_limiter(key, max_calls, period)
        return await limiter.acquire(timeout)

    def get_all_stats(self) -> dict[str, dict[str, any]]:
        """获取所有速率限制器的统计"""
        return {key: limiter.get_stats() for key, limiter in self.limiters.items()}


# 全局速率限制器
_global_rate_limiter: MultiRateLimiter | None = None


def get_global_rate_limiter() -> MultiRateLimiter:
    """获取全局速率限制器"""
    global _global_rate_limiter
    if _global_rate_limiter is None:
        _global_rate_limiter = MultiRateLimiter()
    return _global_rate_limiter


__all__ = [
    "MultiRateLimiter",
    "RateLimitConfig",
    "RateLimitStrategy",
    "RateLimiter",
    "get_global_rate_limiter",
]
