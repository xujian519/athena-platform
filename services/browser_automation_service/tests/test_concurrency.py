#!/usr/bin/env python3
"""
并发控制测试
Concurrency Control Tests for Browser Automation Service

测试信号量、速率限制、熔断器等并发控制功能

作者: 小诺·双鱼公主
版本: 1.0.0
"""

import asyncio
import time

import pytest

from core.concurrency import (
    CircuitBreaker,
    ConcurrencyManager,
    RateLimiter,
    SemaphoreManager,
)
from core.exceptions import ConcurrentLimitExceededError


class TestRateLimiter:
    """测试速率限制器"""

    @pytest.mark.asyncio
    async def test_rate_limiter_acquire(self):
        """测试速率限制获取"""
        limiter = RateLimiter(rate=10, per=1)  # 10请求/秒

        # 应该能快速获取10个许可
        for _ in range(10):
            assert await limiter.acquire() is True

        # 第11个应该失败
        assert await limiter.acquire() is False

    @pytest.mark.asyncio
    async def test_rate_limiter_refill(self):
        """测试速率限制恢复"""
        limiter = RateLimiter(rate=5, per=1)  # 5请求/秒

        # 使用所有许可
        for _ in range(5):
            await limiter.acquire()

        # 应该被限制
        assert await limiter.acquire() is False

        # 等待恢复
        await asyncio.sleep(1.1)

        # 应该能再次获取
        assert await limiter.acquire() is True

    @pytest.mark.asyncio
    async def test_rate_limiter_wait(self):
        """测试速率限制等待"""
        limiter = RateLimiter(rate=2, per=1)  # 2请求/秒

        start = time.monotonic()

        # 获取3个许可（第3个需要等待）
        for _ in range(3):
            await limiter.wait()

        elapsed = time.monotonic() - start

        # 应该等待约0.5秒
        assert elapsed >= 0.4
        assert elapsed < 1.0


class TestSemaphoreManager:
    """测试信号量管理器"""

    @pytest.mark.asyncio
    async def test_semaphore_acquire(self):
        """测试信号量获取"""
        sem = SemaphoreManager(max_concurrent=3, name="test")

        assert sem.available == 3
        assert sem.active_count == 0

        async with sem.acquire():
            assert sem.available == 2
            assert sem.active_count == 1

        assert sem.available == 3
        assert sem.active_count == 0

    @pytest.mark.asyncio
    async def test_semaphore_concurrent(self):
        """测试信号量并发"""
        sem = SemaphoreManager(max_concurrent=2, name="test")
        results = []

        async def worker(worker_id: int):
            try:
                async with sem.acquire(timeout=0.5):
                    results.append(f"worker-{worker_id}-start")
                    await asyncio.sleep(0.2)
                    results.append(f"worker-{worker_id}-end")
            except ConcurrentLimitExceededError:
                results.append(f"worker-{worker_id}-timeout")

        # 启动4个worker（超过限制）
        tasks = [worker(i) for i in range(4)]
        await asyncio.gather(*tasks)

        # 应该有2个成功，2个超时
        successful = [r for r in results if "timeout" not in r]
        timeouts = [r for r in results if "timeout" in r]

        assert len(successful) == 4  # 4个开始
        assert len(timeouts) == 2  # 2个超时

    @pytest.mark.asyncio
    async def test_semaphore_timeout(self):
        """测试信号量超时"""
        sem = SemaphoreManager(max_concurrent=1, name="test")

        async def holder():
            async with sem.acquire():
                await asyncio.sleep(0.5)

        # 启动第一个holder
        task = asyncio.create_task(holder())

        # 等待它获取信号量
        await asyncio.sleep(0.1)

        # 尝试获取（应该超时）
        with pytest.raises(ConcurrentLimitExceededError) as exc_info:
            async with sem.acquire(timeout=0.1):
                pass

        assert "超时" in str(exc_info.value)

        await task

    @pytest.mark.asyncio
    async def test_semaphore_stats(self):
        """测试信号量统计"""
        sem = SemaphoreManager(max_concurrent=5, name="test")

        async def worker():
            async with sem.acquire():
                await asyncio.sleep(0.1)

        # 启动多个worker
        tasks = [worker() for _ in range(10)]
        await asyncio.gather(*tasks)

        stats = sem.get_stats()

        assert stats["name"] == "test"
        assert stats["max_concurrent"] == 5
        assert stats["active_count"] == 0
        assert stats["available"] == 5
        assert stats["total_requests"] == 10


class TestCircuitBreaker:
    """测试熔断器"""

    @pytest.mark.asyncio
    async def test_circuit_breaker_closed_state(self):
        """测试熔断器关闭状态"""
        cb = CircuitBreaker(failure_threshold=3, timeout=1.0)

        # 初始状态应该是关闭的
        assert cb.state == CircuitBreaker.CLOSED

        # 成功调用
        result = await cb.call(lambda: "success")
        assert result == "success"
        assert cb.state == CircuitBreaker.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_breaker_open_on_failures(self):
        """测试熔断器在失败时打开"""
        cb = CircuitBreaker(failure_threshold=2, timeout=1.0)

        # 第一次失败
        with pytest.raises(Exception):
            await cb.call(lambda: (_ for _ in ()).throw(ValueError("error")))

        assert cb.state == CircuitBreaker.CLOSED
        assert cb.failure_count == 1

        # 第二次失败 - 应该打开熔断器
        with pytest.raises(Exception):
            await cb.call(lambda: (_ for _ in ()).throw(ValueError("error")))

        assert cb.state == CircuitBreaker.OPEN
        assert cb.failure_count == 2

    @pytest.mark.asyncio
    async def test_circuit_breaker_rejects_when_open(self):
        """测试熔断器打开时拒绝请求"""
        cb = CircuitBreaker(failure_threshold=2, timeout=1.0)

        # 触发熔断器
        for _ in range(2):
            try:
                await cb.call(lambda: (_ for _ in ()).throw(ValueError("error")))
            except Exception:
                pass

        assert cb.state == CircuitBreaker.OPEN

        # 应该拒绝请求
        with pytest.raises(Exception, match="熔断器打开"):
            await cb.call(lambda: "should not execute")

    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_state(self):
        """测试熔断器半开状态"""
        cb = CircuitBreaker(failure_threshold=2, timeout=0.2, half_open_attempts=2)

        # 触发熔断器
        for _ in range(2):
            try:
                await cb.call(lambda: (_ for _ in ()).throw(ValueError("error")))
            except Exception:
                pass

        assert cb.state == CircuitBreaker.OPEN

        # 等待超时
        await asyncio.sleep(0.3)

        # 下一次调用应该进入半开状态
        result = await cb.call(lambda: "success")
        assert result == "success"
        assert cb.state == CircuitBreaker.HALF_OPEN

        # 成功调用达到阈值，应该恢复
        result = await cb.call(lambda: "success")
        assert result == "success"
        assert cb.state == CircuitBreaker.CLOSED
        assert cb.failure_count == 0

    @pytest.mark.asyncio
    async def test_circuit_breaker_stats(self):
        """测试熔断器统计"""
        cb = CircuitBreaker(failure_threshold=3, timeout=1.0)

        stats = cb.get_stats()

        assert stats["name"] == "circuit_breaker"
        assert stats["state"] == CircuitBreaker.CLOSED
        assert stats["failure_count"] == 0
        assert stats["failure_threshold"] == 3

    @pytest.mark.asyncio
    async def test_circuit_breaker_with_async_function(self):
        """测试熔断器与异步函数"""
        cb = CircuitBreaker(failure_threshold=2, timeout=1.0)

        async def async_func():
            await asyncio.sleep(0.01)
            return "async_result"

        result = await cb.call(async_func)
        assert result == "async_result"


class TestConcurrencyManager:
    """测试并发控制管理器"""

    @pytest.mark.asyncio
    async def test_concurrency_manager_initialization(self):
        """测试并发管理器初始化"""
        manager = ConcurrencyManager()

        assert manager.navigate_semaphore is not None
        assert manager.click_semaphore is not None
        assert manager.fill_semaphore is not None
        assert manager.screenshot_semaphore is not None
        assert manager.js_semaphore is not None
        assert manager.task_semaphore is not None
        assert manager.rate_limiter is not None

    @pytest.mark.asyncio
    async def test_concurrency_manager_rate_limit(self):
        """测试并发管理器速率限制"""
        manager = ConcurrencyManager()

        # 应该能获取一些许可
        success_count = 0
        for _ in range(10):
            if await manager.check_rate_limit():
                success_count += 1

        assert success_count > 0
        assert success_count <= 10

    @pytest.mark.asyncio
    async def test_concurrency_manager_stats(self):
        """测试并发管理器统计"""
        manager = ConcurrencyManager()

        async def test_worker():
            async with manager.navigate_semaphore.acquire():
                await asyncio.sleep(0.05)

        # 启动一些worker
        tasks = [test_worker() for _ in range(3)]
        await asyncio.gather(*tasks)

        stats = manager.get_all_stats()

        assert "semaphores" in stats
        assert "rate_limit" in stats
        assert "navigate" in stats["semaphores"]
        assert stats["semaphores"]["navigate"]["total_requests"] == 3


class TestConcurrentScenarios:
    """测试并发场景"""

    @pytest.mark.asyncio
    async def test_multiple_concurrent_operations(self):
        """测试多个并发操作"""
        manager = ConcurrencyManager()
        results = []

        async def navigate_task(i: int):
            async with manager.navigate_semaphore.acquire():
                results.append(f"nav-{i}-start")
                await asyncio.sleep(0.05)
                results.append(f"nav-{i}-end")

        async def click_task(i: int):
            async with manager.click_semaphore.acquire():
                results.append(f"click-{i}-start")
                await asyncio.sleep(0.03)
                results.append(f"click-{i}-end")

        # 启动混合任务
        tasks = []
        for i in range(3):
            tasks.append(navigate_task(i))
            tasks.append(click_task(i))

        await asyncio.gather(*tasks)

        # 所有任务都应该完成
        assert len([r for r in results if "end" in r]) == 6

    @pytest.mark.asyncio
    async def test_semaphore_reuse(self):
        """测试信号量重用"""
        sem = SemaphoreManager(max_concurrent=2, name="reuse")

        # 多次使用同一个信号量
        for _ in range(5):
            async with sem.acquire():
                await asyncio.sleep(0.01)

        stats = sem.get_stats()
        assert stats["total_requests"] == 5
        assert stats["active_count"] == 0

    @pytest.mark.asyncio
    async def test_rate_limit_under_load(self):
        """测试负载下的速率限制"""
        limiter = RateLimiter(rate=10, per=1)
        success = 0
        failed = 0

        # 尝试快速获取20个许可
        for _ in range(20):
            if await limiter.acquire():
                success += 1
            else:
                failed += 1

        assert success == 10  # 只有10个应该成功
        assert failed == 10  # 剩余10个失败


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
