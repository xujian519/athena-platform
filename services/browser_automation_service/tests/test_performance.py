#!/usr/bin/env python3
"""
性能测试
Performance Tests for Browser Automation Service

测试响应时间、吞吐量、内存使用等性能指标

作者: 小诺·双鱼公主
版本: 1.0.0
"""

import asyncio
import gc
import time

import pytest
from core.session_manager import SessionManager

from core.concurrency import ConcurrencyManager, RateLimiter, SemaphoreManager


class TestPerformanceBenchmarks:
    """测试性能基准"""

    @pytest.mark.asyncio
    async def test_semaphore_performance(self):
        """测试信号量性能"""
        sem = SemaphoreManager(max_concurrent=10, name="perf_test")

        start = time.monotonic()

        # 执行100次获取和释放
        for _ in range(100):
            async with sem.acquire():
                pass

        elapsed = time.monotonic() - start

        # 应该很快完成（< 1秒）
        assert elapsed < 1.0

        stats = sem.get_stats()
        assert stats["total_requests"] == 100

    @pytest.mark.asyncio
    async def test_rate_limiter_performance(self):
        """测试速率限制器性能"""
        limiter = RateLimiter(rate=1000, per=1)

        start = time.monotonic()

        # 尝试获取1000次
        count = 0
        for _ in range(1000):
            if await limiter.acquire():
                count += 1

        elapsed = time.monotonic() - start

        # 应该快速完成
        assert elapsed < 0.1
        assert count == 1000

    @pytest.mark.asyncio
    async def test_session_manager_performance(self):
        """测试会话管理器性能"""
        manager = SessionManager()

        # 模拟创建和删除会话
        async def session_lifecycle():
            from unittest.mock import AsyncMock, MagicMock

            mock_page = MagicMock()
            mock_page.close = AsyncMock()

            mock_context = MagicMock()

            session = await manager.create_session(
                mock_page,
                mock_context,
                "test_context",
                {"test": "data"},
            )

            await manager.delete_session(session.session_id)

        start = time.monotonic()

        # 执行100次会话生命周期
        for _ in range(100):
            await session_lifecycle()

        elapsed = time.monotonic() - start

        # 应该快速完成
        assert elapsed < 0.5

        # 验证统计
        assert manager.total_count == 100

    @pytest.mark.asyncio
    async def test_concurrent_performance(self):
        """测试并发性能"""
        manager = ConcurrencyManager()

        async def worker(worker_id: int):
            async with manager.navigate_semaphore.acquire():
                await asyncio.sleep(0.01)
                return worker_id

        start = time.monotonic()

        # 并发执行50个worker
        tasks = [worker(i) for i in range(50)]
        results = await asyncio.gather(*tasks)

        elapsed = time.monotonic() - start

        # 所有任务都应该完成
        assert len(results) == 50

        # 应该在合理时间内完成
        # 50个任务 / 5并发 ≈ 10批次 * 0.01秒 ≈ 0.1秒
        assert elapsed < 0.5


class TestMemoryUsage:
    """测试内存使用"""

    @pytest.mark.asyncio
    async def test_session_memory_leak(self):
        """测试会话内存泄漏"""
        import tracemalloc

        tracemalloc.start()

        manager = SessionManager()

        # 获取初始内存
        snapshot1 = tracemalloc.take_snapshot()

        # 创建大量会话
        from unittest.mock import AsyncMock, MagicMock

        for i in range(100):
            mock_page = MagicMock()
            mock_page.close = AsyncMock()

            mock_context = MagicMock()

            await manager.create_session(
                mock_page,
                mock_context,
                f"context_{i}",
            )

        # 删除所有会话
        for session_id in list(manager.sessions.keys()):
            await manager.delete_session(session_id)

        # 强制垃圾回收
        gc.collect()

        # 获取最终内存
        snapshot2 = tracemalloc.take_snapshot()

        # 计算内存差异
        top_stats = snapshot2.compare_to(snapshot1, "lineno")

        # 检查内存泄漏（前10个分配位置）
        total_allocated = sum(stat.size_diff for stat in top_stats[:10])

        # 应该不会分配太多内存（< 1MB）
        assert total_allocated < 1024 * 1024

        tracemalloc.stop()

    @pytest.mark.asyncio
    async def test_semaphore_memory_stability(self):
        """测试信号量内存稳定性"""
        import tracemalloc

        tracemalloc.start()

        sem = SemaphoreManager(max_concurrent=5, name="mem_test")

        snapshot1 = tracemalloc.take_snapshot()

        # 执行大量操作
        for _ in range(1000):
            async with sem.acquire():
                pass

        gc.collect()

        snapshot2 = tracemalloc.take_snapshot()

        # 内存增长应该很小
        top_stats = snapshot2.compare_to(snapshot1, "lineno")
        total_allocated = sum(stat.size_diff for stat in top_stats[:10])

        # 应该 < 100KB
        assert total_allocated < 100 * 1024

        tracemalloc.stop()


class TestThroughput:
    """测试吞吐量"""

    @pytest.mark.asyncio
    async def test_semaphore_throughput(self):
        """测试信号量吞吐量"""
        sem = SemaphoreManager(max_concurrent=10, name="throughput")

        async def worker():
            async with sem.acquire():
                await asyncio.sleep(0.01)  # 模拟工作

        start = time.monotonic()

        # 执行100个任务
        tasks = [worker() for _ in range(100)]
        await asyncio.gather(*tasks)

        elapsed = time.monotonic() - start

        # 计算吞吐量（任务/秒）
        throughput = 100 / elapsed

        # 应该达到至少 500 任务/秒
        assert throughput > 500

    @pytest.mark.asyncio
    async def test_session_throughput(self):
        """测试会话吞吐量"""
        manager = SessionManager()

        async def create_delete_session():
            from unittest.mock import AsyncMock, MagicMock

            mock_page = MagicMock()
            mock_page.close = AsyncMock()

            mock_context = MagicMock()

            session = await manager.create_session(
                mock_page,
                mock_context,
                "test_ctx",
            )
            await manager.delete_session(session.session_id)

        start = time.monotonic()

        # 执行100次创建/删除
        for _ in range(100):
            await create_delete_session()

        elapsed = time.monotonic() - start

        # 计算吞吐量
        throughput = 100 / elapsed

        # 应该至少 200 会话操作/秒
        assert throughput > 200


class TestLatency:
    """测试延迟"""

    @pytest.mark.asyncio
    async def test_semaphore_acquire_latency(self):
        """测试信号量获取延迟"""
        sem = SemaphoreManager(max_concurrent=5, name="latency_test")

        latencies = []

        for _ in range(50):
            start = time.perf_counter()
            async with sem.acquire():
                pass
            latencies.append(time.perf_counter() - start)

        # 计算统计数据
        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        min(latencies)

        # 平均延迟应该 < 1ms
        assert avg_latency < 0.001

        # 最大延迟应该 < 10ms
        assert max_latency < 0.01

    @pytest.mark.asyncio
    async def test_rate_limiter_latency(self):
        """测试速率限制器延迟"""
        limiter = RateLimiter(rate=100, per=1)

        latencies = []

        for _ in range(50):
            start = time.perf_counter()
            await limiter.acquire()
            latencies.append(time.perf_counter() - start)

        avg_latency = sum(latencies) / len(latencies)

        # 平均延迟应该很小
        assert avg_latency < 0.001


class TestScalability:
    """测试可扩展性"""

    @pytest.mark.asyncio
    async def test_concurrent_scaling(self):
        """测试并发扩展"""
        results = {}

        for concurrency in [1, 5, 10, 20]:
            sem = SemaphoreManager(max_concurrent=concurrency, name=f"scale_{concurrency}")

            async def worker():
                async with sem.acquire():
                    await asyncio.sleep(0.01)

            start = time.monotonic()

            tasks = [worker() for _ in range(50)]
            await asyncio.gather(*tasks)

            elapsed = time.monotonic() - start
            results[concurrency] = elapsed

        # 更高的并发应该更快完成
        assert results[20] < results[10] < results[5] < results[1]

    @pytest.mark.asyncio
    async def test_session_limit_scaling(self):
        """测试会话限制扩展"""
        from config.settings import settings

        original_limit = settings.MAX_CONCURRENT_SESSIONS

        try:
            # 测试不同限制下的表现
            for limit in [10, 50, 100]:
                settings.MAX_CONCURRENT_SESSIONS = limit

                manager = SessionManager()

                # 尝试创建限制数量的会话
                from unittest.mock import AsyncMock, MagicMock

                for i in range(limit):
                    mock_page = MagicMock()
                    mock_page.close = AsyncMock()
                    mock_context = MagicMock()

                    session = await manager.create_session(
                        mock_page,
                        mock_context,
                        f"ctx_{i}",
                    )

                    assert session.session_id is not None

                # 验证数量
                assert manager.active_count == limit

                # 清理
                await manager.shutdown()

        finally:
            settings.MAX_CONCURRENT_SESSIONS = original_limit


class TestResourceCleanup:
    """测试资源清理"""

    @pytest.mark.asyncio
    async def test_semaphore_cleanup(self):
        """测试信号量清理"""
        sem = SemaphoreManager(max_concurrent=5, name="cleanup_test")

        # 获取所有许可
        async def holder():
            async with sem.acquire():
                await asyncio.sleep(0.1)

        tasks = [asyncio.create_task(holder()) for _ in range(5)]

        # 等待所有获取
        await asyncio.sleep(0.01)

        assert sem.available == 0

        # 等待所有完成
        await asyncio.gather(*tasks)

        # 所有许可应该被释放
        assert sem.available == 5
        assert sem.active_count == 0

    @pytest.mark.asyncio
    async def test_session_cleanup(self):
        """测试会话清理"""
        manager = SessionManager()

        from unittest.mock import AsyncMock, MagicMock

        # 创建多个会话
        sessions = []
        for i in range(10):
            mock_page = MagicMock()
            mock_page.close = AsyncMock()
            mock_context = MagicMock()

            session = await manager.create_session(
                mock_page,
                mock_context,
                f"ctx_{i}",
            )
            sessions.append(session)

        assert manager.active_count == 10

        # 清理所有会话
        await manager.shutdown()

        assert manager.active_count == 0
        assert len(manager.sessions) == 0


class TestPerformanceUnderLoad:
    """测试负载下的性能"""

    @pytest.mark.asyncio
    async def test_high_concurrency_load(self):
        """测试高并发负载"""
        manager = ConcurrencyManager()

        results = []
        errors = []

        async def heavy_worker(worker_id: int):
            try:
                async with manager.navigate_semaphore.acquire(timeout=1):
                    # 模拟一些工作
                    await asyncio.sleep(0.05)
                    results.append(worker_id)
            except Exception as e:
                errors.append((worker_id, e))

        start = time.monotonic()

        # 启动大量worker（超过并发限制）
        tasks = [heavy_worker(i) for i in range(50)]
        await asyncio.gather(*tasks)

        elapsed = time.monotonic() - start

        # 所有任务应该完成
        assert len(results) == 50
        assert len(errors) == 0

        # 应该在合理时间内完成
        assert elapsed < 2.0

    @pytest.mark.asyncio
    async def test_burst_traffic(self):
        """测试突发流量"""
        limiter = RateLimiter(rate=10, per=1)

        # 突发20个请求
        success = 0
        failed = 0

        for _ in range(20):
            if await limiter.acquire():
                success += 1
            else:
                failed += 1

        # 前10个应该成功，其余失败
        assert success == 10
        assert failed == 10


# 性能基准数据
PERFORMANCE_BENCHMARKS = {
    "semaphore_acquire_avg": "< 1ms",
    "semaphore_throughput": "> 500 ops/sec",
    "session_throughput": "> 200 ops/sec",
    "rate_limiter_latency": "< 1ms",
    "concurrent_scaling": "linear",
    "memory_leak": "< 1MB for 100 sessions",
}


@pytest.mark.skip(reason="性能基准测试，默认跳过")
class TestPerformanceBenchmarksDetailed:
    """详细的性能基准测试（默认跳过）"""

    @pytest.mark.asyncio
    async def test_full_performance_report(self):
        """生成完整性能报告"""
        results = {}

        # 信号量性能
        sem = SemaphoreManager(max_concurrent=10, name="benchmark")
        start = time.monotonic()
        for _ in range(1000):
            async with sem.acquire():
                pass
        results["semaphore_1000_ops"] = time.monotonic() - start

        # 会话管理器性能
        manager = SessionManager()
        start = time.monotonic()

        from unittest.mock import AsyncMock, MagicMock

        for i in range(100):
            mock_page = MagicMock()
            mock_page.close = AsyncMock()
            mock_context = MagicMock()

            session = await manager.create_session(
                mock_page,
                mock_context,
                f"ctx_{i}",
            )
            await manager.delete_session(session.session_id)

        results["session_100_ops"] = time.monotonic() - start

        # 打印报告
        print("\n" + "=" * 60)
        print("性能基准测试报告")
        print("=" * 60)
        for name, value in results.items():
            print(f"{name}: {value:.4f}s")
        print("=" * 60)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
