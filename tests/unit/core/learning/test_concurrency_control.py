#!/usr/bin/env python3
"""
并发控制模块单元测试
Concurrency Control Unit Tests

测试ConcurrencyController和相关组件：
1. 速率限制器
2. 异步信号量
3. 并发控制器

作者: Athena平台团队
版本: 1.0.0
创建时间: 2026-01-28
"""

import asyncio
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.learning.concurrency_control import (
    AsyncSemaphore,
    ConcurrencyConfig,
    ConcurrencyController,
    RateLimiter,
)


class TestRateLimiter:
    """速率限制器测试"""

    @pytest.mark.asyncio
    async def test_acquire_token(self):
        """测试获取令牌"""
        limiter = RateLimiter(max_rate=10, window=1.0)

        # 应该能获取令牌
        assert await limiter.acquire() is True

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """测试速率限制"""
        limiter = RateLimiter(max_rate=5, window=1.0)

        # 快速获取5个令牌应该成功
        for _ in range(5):
            assert await limiter.acquire() is True

        # 第6个应该失败（没有令牌了）
        assert await limiter.acquire() is False

    @pytest.mark.asyncio
    async def test_token_replenishment(self):
        """测试令牌补充"""
        limiter = RateLimiter(max_rate=10, window=1.0)

        # 消耗所有令牌
        for _ in range(10):
            await limiter.acquire()

        # 等待令牌补充
        await asyncio.sleep(0.2)

        # 应该能获取到一些令牌
        assert await limiter.acquire() is True

    @pytest.mark.asyncio
    async def test_wait_for_token(self):
        """测试等待令牌"""
        limiter = RateLimiter(max_rate=2, window=1.0)

        # 消耗所有令牌
        for _ in range(2):
            await limiter.acquire()

        # 等待令牌应该会阻塞然后成功
        start = asyncio.get_event_loop().time()
        await limiter.wait_for_token()
        elapsed = asyncio.get_event_loop().time() - start

        # 应该等待大约0.5秒（1秒/2）
        assert elapsed >= 0.3


class TestAsyncSemaphore:
    """异步信号量测试"""

    @pytest.mark.asyncio
    async def test_acquire_release(self):
        """测试获取和释放"""
        sem = AsyncSemaphore(max_concurrent=3)

        # 获取信号量
        assert await sem.acquire() is True
        assert sem.current_count == 1

        # 释放信号量
        sem.release()
        assert sem.current_count == 0

    @pytest.mark.asyncio
    async def test_concurrent_limit(self):
        """测试并发限制"""
        sem = AsyncSemaphore(max_concurrent=2)

        # 获取2个信号量
        assert await sem.acquire() is True
        assert await sem.acquire() is True

        # 获取第3个应该超时
        assert await sem.acquire(timeout=0.1) is False

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """测试上下文管理器"""
        sem = AsyncSemaphore(max_concurrent=1)

        async with sem:
            assert sem.current_count == 1

        assert sem.current_count == 0

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """测试获取统计信息"""
        sem = AsyncSemaphore(max_concurrent=5)

        await sem.acquire()
        await sem.acquire()

        stats = sem.get_stats()
        assert stats["max_concurrent"] == 5
        assert stats["current_count"] == 2
        assert stats["total_acquired"] == 2


class TestConcurrencyController:
    """并发控制器测试"""

    @pytest.fixture
    def controller(self):
        """创建并发控制器"""
        return ConcurrencyController(
            ConcurrencyConfig(
                max_concurrent_tasks=3,
                max_operations_per_second=10,
                max_queue_size=100,
            )
        )

    @pytest.mark.asyncio
    async def test_submit_task(self, controller):
        """测试提交任务"""
        async def sample_task():
            await asyncio.sleep(0.1)
            return "result"

        result = await controller.submit_task(sample_task)
        assert result == "result"

    @pytest.mark.asyncio
    async def test_concurrent_limit(self, controller):
        """测试并发限制"""
        running_count = 0
        max_running = 0

        async def counting_task():
            nonlocal running_count, max_running
            running_count += 1
            max_running = max(max_running, running_count)
            await asyncio.sleep(0.2)
            running_count -= 1
            return "done"

        # 提交10个任务，但max_concurrent=3
        tasks = [
            asyncio.create_task(controller.submit_task(counting_task))
            for _ in range(10)
        ]

        await asyncio.gather(*tasks)

        # 最多只应该有3个任务同时运行
        assert max_running <= 3

    @pytest.mark.asyncio
    async def test_batch_submit(self, controller):
        """测试批量提交"""
        async def sample_task(n):
            await asyncio.sleep(0.01)
            return n * 2

        coros = [lambda n=n: sample_task(n) for n in range(5)]
        results = await controller.submit_batch(coros)

        assert len(results) == 5
        assert results == [0, 2, 4, 6, 8]

    @pytest.mark.asyncio
    async def test_task_timeout(self, controller):
        """测试任务超时"""
        async def slow_task():
            await asyncio.sleep(10)
            return "done"

        with pytest.raises(asyncio.TimeoutError):
            await controller.submit_task(slow_task, timeout=0.1)

    @pytest.mark.asyncio
    async def test_get_statistics(self, controller):
        """测试获取统计信息"""
        async def sample_task():
            return "result"

        await controller.submit_task(sample_task)

        stats = controller.get_statistics()
        assert "config" in stats
        assert "semaphore" in stats
        assert "tasks" in stats
        assert stats["tasks"]["total"] == 1

    @pytest.mark.asyncio
    async def test_shutdown(self, controller):
        """测试关闭"""
        async def sample_task():
            await asyncio.sleep(0.1)
            return "result"

        # 提交任务
        task = asyncio.create_task(controller.submit_task(sample_task))

        # 等待任务完成
        await task

        # 关闭控制器
        await controller.shutdown()

        # 验证没有活动任务
        stats = controller.get_statistics()
        assert stats["tasks"]["active"] == 0


@pytest.mark.asyncio
async def test_full_concurrency_scenario():
    """测试完整的并发控制场景"""
    config = ConcurrencyConfig(
        max_concurrent_tasks=2,
        max_operations_per_second=5,
        task_timeout=1.0,
    )
    controller = ConcurrencyController(config)

    results = []
    errors = []

    async def worker(n):
        try:
            await asyncio.sleep(0.1)
            return f"worker_{n}"
        except Exception as e:
            errors.append(e)
            raise

    # 提交多个任务
    tasks = [
        asyncio.create_task(controller.submit_task(lambda i=i: worker(i), i))
        for i in range(5)
    ]

    results = await asyncio.gather(*tasks)

    assert len(results) == 5
    assert len(errors) == 0

    # 验证统计信息
    stats = controller.get_statistics()
    assert stats["tasks"]["total"] == 5
    assert stats["tasks"]["completed"] >= 5

    await controller.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
