#!/usr/bin/env python3

"""
自适应限流器
Adaptive Rate Limiter

基于系统负载自适应调整限流策略,保护系统免受过载影响。

功能特性:
1. 动态限流阈值
2. 系统负载感知
3. 优先级感知
4. 令牌桶算法
5. 滑动窗口统计

限流策略:
- 固定速率:恒定的请求速率
- 令牌桶:允许突发流量
- 漏桶:平滑流量
- 自适应:根据负载动态调整

作者: Athena AI系统
创建时间: 2026-01-25
版本: 1.0.0
"""

import asyncio
import contextlib
import logging
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class RateLimitStrategy(Enum):
    """限流策略"""

    FIXED = "fixed"  # 固定速率
    TOKEN_BUCKET = "token_bucket"  # 令牌桶
    LEAKY_BUCKET = "leaky_bucket"  # 漏桶
    ADAPTIVE = "adaptive"  # 自适应


class LoadLevel(Enum):
    """负载级别"""

    LOW = 0  # 低负载 (< 50%)
    MEDIUM = 1  # 中负载 (50% - 75%)
    HIGH = 2  # 高负载 (75% - 90%)
    CRITICAL = 3  # 临界负载 (> 90%)


@dataclass
class RateLimitConfig:
    """限流配置"""

    strategy: RateLimitStrategy = RateLimitStrategy.ADAPTIVE
    base_rate: float = 100.0  # 基础速率(请求/秒)
    max_rate: float = 1000.0  # 最大速率
    min_rate: float = 10.0  # 最小速率
    burst_size: int = 10  # 突发大小
    window_size: float = 1.0  # 统计窗口大小(秒)

    # 自适应参数
    cpu_threshold_high: float = 0.75  # CPU高负载阈值
    cpu_threshold_low: float = 0.50  # CPU低负载阈值
    memory_threshold_high: float = 0.80  # 内存高负载阈值
    adjustment_factor: float = 1.2  # 调整因子


@dataclass
class RateLimitResult:
    """限流结果"""

    allowed: bool  # 是否允许
    wait_time: float = 0.0  # 建议等待时间(秒)
    current_rate: float = 0.0  # 当前速率
    reason: str = ""  # 原因


@dataclass
class SystemMetrics:
    """系统指标"""

    cpu_usage: float = 0.0  # CPU使用率
    memory_usage: float = 0.0  # 内存使用率
    request_rate: float = 0.0  # 请求速率
    error_rate: float = 0.0  # 错误率
    avg_response_time: float = 0.0  # 平均响应时间
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def load_level(self) -> LoadLevel:
        """负载级别"""
        max_usage = max(self.cpu_usage, self.memory_usage)
        if max_usage < 0.5:
            return LoadLevel.LOW
        elif max_usage < 0.75:
            return LoadLevel.MEDIUM
        elif max_usage < 0.9:
            return LoadLevel.HIGH
        else:
            return LoadLevel.CRITICAL


@dataclass
class RateLimiterMetrics:
    """限流器指标"""

    total_requests: int = 0
    allowed_requests: int = 0
    rejected_requests: int = 0
    current_rate: float = 0.0
    avg_wait_time: float = 0.0
    peak_rate: float = 0.0

    # 调整历史
    rate_adjustments: int = 0
    last_adjustment_time: Optional[datetime] = None

    @property
    def rejection_rate(self) -> float:
        """拒绝率"""
        if self.total_requests == 0:
            return 0.0
        return self.rejected_requests / self.total_requests


class AdaptiveRateLimiter:
    """自适应限流器

    基于系统负载动态调整限流策略。

    使用示例:
        >>> limiter = AdaptiveRateLimiter(config=RateLimitConfig(base_rate=100))
        >>> await limiter.initialize()
        >>>
        >>> # 限流检查
        >>> result = await limiter.acquire()
        >>> if result.allowed:
        >>>     # 处理请求
        >>>     await process_request()
        >>>     await limiter.release()
        >>>
        >>> # 或使用上下文管理器
        >>> async with limiter:
        >>>     await process_request()
    """

    def __init__(self, config: Optional[RateLimitConfig] = None):
        """初始化限流器

        Args:
            config: 限流配置
        """
        self.config = config or RateLimitConfig()
        self._current_rate = self.config.base_rate

        # 令牌桶
        self._tokens = self.config.burst_size
        self._last_refill = time.time()

        # 请求时间戳(滑动窗口)
        self._request_times: deque[float] = deque()

        # 系统指标
        self._metrics = SystemMetrics()

        # 限流器指标
        self._limiter_metrics = RateLimiterMetrics()

        # 锁
        self._lock = asyncio.Lock()

        # 后台任务
        self._monitor_task: asyncio.Optional[Task] = None
        self._running = False

        logger.info(
            f"🚦 初始化自适应限流器 "
            f"(策略={self.config.strategy.value}, 基础速率={self.config.base_rate})"
        )

    async def initialize(self) -> None:
        """初始化限流器"""
        if self._running:
            return

        self._running = True

        # 启动监控任务
        if self.config.strategy == RateLimitStrategy.ADAPTIVE:
            self._monitor_task = asyncio.create_task(self._monitor_loop())

        logger.info("✅ 自适应限流器启动完成")

    async def shutdown(self) -> None:
        """关闭限流器"""
        logger.info("🛑 关闭自适应限流器...")

        self._running = False

        if self._monitor_task:
            self._monitor_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._monitor_task

        logger.info("✅ 自适应限流器已关闭")

    async def acquire(self, priority: int = 0) -> RateLimitResult:
        """获取许可

        Args:
            priority: 优先级(数字越小优先级越高)

        Returns:
            限流结果
        """
        self._limiter_metrics.total_requests += 1

        async with self._lock:
            # 更新令牌桶
            self._refill_tokens()

            # 根据策略检查
            if self.config.strategy == RateLimitStrategy.TOKEN_BUCKET:
                result = self._check_token_bucket()
            elif self.config.strategy == RateLimitStrategy.LEAKY_BUCKET:
                result = self._check_leaky_bucket()
            elif self.config.strategy == RateLimitStrategy.FIXED:
                result = self._check_fixed_rate()
            else:  # ADAPTIVE
                result = self._check_adaptive()

            if result.allowed:
                self._limiter_metrics.allowed_requests += 1
                self._request_times.append(time.time())
            else:
                self._limiter_metrics.rejected_requests += 1

            logger.debug(
                f"🚦 限流检查: {'允许' if result.allowed else '拒绝'} "
                f"(当前速率={self._current_rate:.1f}, 原因={result.reason})"
            )

            return result

    async def release(self) -> None:
        """释放许可"""
        # 对于某些策略可能需要特殊处理
        pass

    async def __aenter__(self):
        """异步上下文管理器入口"""
        result = await self.acquire()
        if not result.allowed:
            raise RuntimeError(f"限流拒绝: {result.reason}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.release()

    def _refill_tokens(self) -> None:
        """填充令牌桶"""
        now = time.time()
        elapsed = now - self._last_refill

        # 计算应添加的令牌数
        tokens_to_add = elapsed * self._current_rate
        self._tokens = min(
            self._tokens + tokens_to_add,
            self.config.burst_size,
        )
        self._last_refill = now

    def _check_token_bucket(self) -> RateLimitResult:
        """检查令牌桶"""
        if self._tokens >= 1:
            self._tokens -= 1
            return RateLimitResult(
                allowed=True,
                current_rate=self._current_rate,
            )
        else:
            # 计算等待时间
            wait_time = (1 - self._tokens) / self._current_rate
            return RateLimitResult(
                allowed=False,
                wait_time=wait_time,
                current_rate=self._current_rate,
                reason="令牌不足",
            )

    def _check_leaky_bucket(self) -> RateLimitResult:
        """检查漏桶"""
        now = time.time()

        # 清理旧的时间戳
        cutoff = now - self.config.window_size
        while self._request_times and self._request_times[0] < cutoff:
            self._request_times.popleft()

        # 检查是否超过速率
        if len(self._request_times) < self._current_rate * self.config.window_size:
            return RateLimitResult(
                allowed=True,
                current_rate=self._current_rate,
            )
        else:
            # 计算最旧请求的剩余时间
            oldest_time = self._request_times[0]
            wait_time = cutoff - oldest_time
            return RateLimitResult(
                allowed=False,
                wait_time=max(0, wait_time),
                current_rate=self._current_rate,
                reason="漏桶已满",
            )

    def _check_fixed_rate(self) -> RateLimitResult:
        """检查固定速率"""
        return self._check_leaky_bucket()

    def _check_adaptive(self) -> RateLimitResult:
        """检查自适应限流"""
        # 基于当前负载级别调整策略
        load_level = self._metrics.load_level

        if load_level == LoadLevel.LOW:
            # 低负载:使用令牌桶,允许突发
            return self._check_token_bucket()
        elif load_level == LoadLevel.MEDIUM:
            # 中负载:使用漏桶,平滑流量
            return self._check_leaky_bucket()
        elif load_level == LoadLevel.HIGH:
            # 高负载:降低速率
            target_rate = self._current_rate * 0.8
            self._update_rate(target_rate)
            return self._check_leaky_bucket()
        else:  # CRITICAL
            # 临界负载:严格限制
            target_rate = self._current_rate * 0.5
            self._update_rate(target_rate)
            result = self._check_leaky_bucket()
            result.reason = "系统负载过高"
            return result

    def _update_rate(self, new_rate: float) -> None:
        """更新速率

        Args:
            new_rate: 新速率
        """
        # 限制速率范围
        new_rate = max(
            self.config.min_rate,
            min(self.config.max_rate, new_rate),
        )

        if new_rate != self._current_rate:
            old_rate = self._current_rate
            self._current_rate = new_rate

            self._limiter_metrics.rate_adjustments += 1
            self._limiter_metrics.last_adjustment_time = datetime.now()
            self._limiter_metrics.peak_rate = max(self._limiter_metrics.peak_rate, new_rate)

            logger.info(
                f"📊 速率调整: {old_rate:.1f} -> {new_rate:.1f} 请求/秒 "
                f"(负载={self._metrics.load_level.name})"
            )

    async def _monitor_loop(self) -> None:
        """监控循环"""
        while self._running:
            try:
                await asyncio.sleep(1.0)

                # 收集系统指标
                await self._collect_metrics()

                # 自适应调整
                await self._adaptive_adjust()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ 监控循环异常: {e}")
                await asyncio.sleep(1)

    async def _collect_metrics(self) -> None:
        """收集系统指标"""
        # 这里可以集成实际的系统监控
        # 示例:使用psutil获取CPU和内存使用率

        try:
            import psutil

            self._metrics.cpu_usage = psutil.cpu_percent(interval=None) / 100
            self._metrics.memory_usage = psutil.virtual_memory().percent / 100

        except ImportError:
            # 如果没有psutil,使用估算值
            pass

        # 计算请求速率
        now = time.time()
        cutoff = now - self.config.window_size
        recent_requests = sum(1 for t in self._request_times if t >= cutoff)
        self._metrics.request_rate = recent_requests / self.config.window_size

        # 更新当前速率
        self._limiter_metrics.current_rate = self._metrics.request_rate

    async def _adaptive_adjust(self) -> None:
        """自适应调整"""
        load_level = self._metrics.load_level

        if load_level == LoadLevel.LOW:
            # 低负载:增加速率
            if self._current_rate < self.config.max_rate:
                new_rate = self._current_rate * self.config.adjustment_factor
                self._update_rate(new_rate)

        elif load_level == LoadLevel.CRITICAL:
            # 临界负载:大幅降低速率
            new_rate = self._current_rate / self.config.adjustment_factor
            self._update_rate(new_rate)

    def get_metrics(self) -> RateLimiterMetrics:
        """获取限流器指标"""
        return self._limiter_metrics

    def get_system_metrics(self) -> SystemMetrics:
        """获取系统指标"""
        return self._metrics

    async def reset(self) -> None:
        """重置限流器"""
        async with self._lock:
            self._tokens = self.config.burst_size
            self._request_times.clear()
            self._current_rate = self.config.base_rate
            logger.info("🔄 限流器已重置")


# 便捷函数
def create_rate_limiter(
    strategy: RateLimitStrategy = RateLimitStrategy.ADAPTIVE,
    base_rate: float = 100.0,
) -> AdaptiveRateLimiter:
    """创建限流器"""
    config = RateLimitConfig(strategy=strategy, base_rate=base_rate)
    return AdaptiveRateLimiter(config)


# 全局限流器实例
_global_limiter: Optional[AdaptiveRateLimiter] = None


def get_global_limiter() -> AdaptiveRateLimiter:
    """获取全局限流器实例"""
    global _global_limiter
    if _global_limiter is None:
        _global_limiter = create_rate_limiter()
    return _global_limiter


async def initialize_global_limiter(config: Optional[RateLimitConfig] = None) -> AdaptiveRateLimiter:
    """初始化全局限流器"""
    global _global_limiter
    if _global_limiter is None:
        _global_limiter = AdaptiveRateLimiter(config)
    await _global_limiter.initialize()
    return _global_limiter


# 装饰器
def rate_limit(
    limiter: Optional[AdaptiveRateLimiter] = None,
    priority: int = 0,
):
    """限流装饰器

    Args:
        limiter: 限流器实例(如果为None,使用全局实例)
        priority: 优先级

    Returns:
        装饰器函数
    """

    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            l = limiter or _global_limiter

            # 获取许可
            result = await l.acquire(priority)
            if not result.allowed:
                raise RuntimeError(f"限流拒绝: {result.reason}")

            try:
                return await func(*args, **kwargs)
            finally:
                await l.release()

        return wrapper

    return decorator


__all__ = [
    "AdaptiveRateLimiter",
    "LoadLevel",
    "RateLimitConfig",
    "RateLimitResult",
    "RateLimitStrategy",
    "RateLimiterMetrics",
    "SystemMetrics",
    "create_rate_limiter",
    "get_global_limiter",
    "initialize_global_limiter",
    "rate_limit",
]

