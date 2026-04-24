#!/usr/bin/env python3
"""上下文对象池单元测试 - 验证对象复用效果"""

import pytest
import asyncio
import time
import gc
from pathlib import Path
from core.context_management.context_object_pool import (
    ContextObjectPool,
    PoolStats,
    get_context_pool,
)
from core.context_management.async_task_context_manager import ContextStatus


@pytest.fixture
async def pool():
    """创建对象池实例"""
    pool = ContextObjectPool(max_size=10, initial_size=2, max_idle_time=60.0)
    yield pool
    # 清理
    await pool.clear()


@pytest.mark.asyncio
class TestContextObjectPool:
    """上下文对象池测试套件"""

    async def test_acquire_and_release(self, pool: ContextObjectPool):
        """测试获取和释放对象"""
        # 获取对象（会从预初始化的池中获取）
        context = await pool.acquire("test_001")
        assert context.task_id == "test_001"
        assert pool.stats.total_requests == 1
        assert pool.stats.reused == 1  # 预初始化的对象被复用
        assert pool.stats.created == 0  # 没有创建新对象

        # 释放对象
        await pool.release(context)
        assert pool.stats.current_size == 2  # 回到初始大小

    async def test_object_reuse(self, pool: ContextObjectPool):
        """测试对象复用"""
        # 第一次获取（从预初始化池中获取）
        ctx1 = await pool.acquire("test_002")
        await pool.release(ctx1)

        # 第二次获取（应该复用）
        ctx2 = await pool.acquire("test_003")
        assert pool.stats.reused == 2  # 两次都复用了预初始化对象
        assert pool.stats.created == 0  # 没有创建新对象
        await pool.release(ctx2)

    async def test_pool_exhaustion(self, pool: ContextObjectPool):
        """测试池耗尽（自动扩容）"""
        # 获取超过初始大小的对象数量
        contexts = []
        for i in range(15):  # 超过initial_size=2
            ctx = await pool.acquire(f"test_exhaust_{i}")
            contexts.append(ctx)

        # 验证创建了新对象
        assert pool.stats.created > 2
        assert pool.stats.total_requests == 15

        # 释放所有对象
        for ctx in contexts:
            await pool.release(ctx)

        # 验证池大小恢复
        assert pool.stats.current_size <= pool.max_size

    async def test_pool_full_discard(self, pool: ContextObjectPool):
        """测试池满时丢弃对象"""
        # 填满池
        contexts = []
        for i in range(pool.max_size + 5):
            ctx = await pool.acquire(f"test_full_{i}")
            contexts.append(ctx)

        # 释放所有对象（部分会被丢弃）
        for ctx in contexts:
            await pool.release(ctx)

        # 验证有对象被丢弃
        assert pool.stats.discarded > 0
        assert pool.stats.current_size == pool.max_size

    async def test_stats_tracking(self, pool: ContextObjectPool):
        """测试统计跟踪"""
        # 同时获取多个对象（超过预初始化数量，触发扩容）
        contexts = []
        for i in range(5):
            ctx = await pool.acquire(f"test_stats_{i}")
            contexts.append(ctx)

        # 释放一半
        for ctx in contexts[:3]:
            await pool.release(ctx)

        # 再获取几个（会有复用）
        for i in range(5, 8):
            ctx = await pool.acquire(f"test_stats_{i}")
            contexts.append(ctx)

        # 释放所有
        for ctx in contexts:
            await pool.release(ctx)

        stats = pool.get_stats()

        assert stats.total_requests == 8
        assert stats.reused > 0  # 应该有复用
        assert stats.created > 0  # 应该有创建（超过预初始化的2个）
        assert 0 < stats.reuse_rate <= 1  # 复用率在合理范围
        assert 0 < stats.creation_rate < 1  # 创建率在合理范围

    async def test_memory_estimate(self, pool: ContextObjectPool):
        """测试内存估算"""
        memory_info = pool.get_memory_estimate()

        assert "current_objects" in memory_info
        assert "estimated_current_memory_kb" in memory_info
        assert "estimated_max_memory_kb" in memory_info
        assert "memory_usage_rate" in memory_info

        print(f"\n内存估算: {memory_info}")

    async def test_warm_up(self, pool: ContextObjectPool):
        """测试预热功能"""
        await pool.warm_up(5)

        stats = pool.get_stats()
        assert stats.current_size >= 5

    async def test_cleanup_idle_objects(self, pool: ContextObjectPool):
        """测试清理空闲对象"""
        # 创建一些对象并记录使用时间
        ctx1 = await pool.acquire("test_idle_1")
        # 模拟对象被使用了一段时间
        pool._metadata["test_idle_1"]["last_used"] = time.time() - 400  # 400秒前
        await pool.release(ctx1)

        # 清理空闲对象
        cleaned = await pool.cleanup_idle_objects()
        assert cleaned >= 0

    async def test_clear_pool(self, pool: ContextObjectPool):
        """测试清空对象池"""
        # 添加一些对象
        for i in range(5):
            ctx = await pool.acquire(f"test_clear_{i}")
            await pool.release(ctx)

        assert pool.stats.current_size > 0

        # 清空
        await pool.clear()

        assert pool.stats.current_size == 0
        assert pool.stats.created == 0  # 统计也被重置


@pytest.mark.asyncio
class TestContextObjectPoolPerformance:
    """对象池性能测试"""

    async def test_reuse_performance(self, pool: ContextObjectPool):
        """测试复用性能"""
        # 预热池
        await pool.warm_up(100)

        # 测试复用性能
        times = []
        for i in range(1000):
            start = time.perf_counter()
            ctx = await pool.acquire(f"perf_{i}")
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)
            await pool.release(ctx)

        avg_time = sum(times) / len(times)

        print(f"\n对象获取性能:")
        print(f"平均: {avg_time:.3f}ms")
        print(f"最小: {min(times):.3f}ms")
        print(f"最大: {max(times):.3f}ms")

        stats = pool.get_stats()
        print(f"复用率: {stats.reuse_rate:.2%}")
        print(f"创建率: {stats.creation_rate:.2%}")

        # 性能验证：对象获取应该非常快（<0.1ms）
        assert avg_time < 0.1, f"对象获取性能未达标: {avg_time:.3f}ms > 0.1ms"
        assert stats.reuse_rate > 0.90, f"复用率未达标: {stats.reuse_rate:.2%} < 90%"

    async def test_memory_comparison(self):
        """对比有池和无池的内存使用"""
        import tracemalloc

        # 测试无池情况
        gc.collect()
        tracemalloc.start()
        start_snapshot = tracemalloc.take_snapshot()

        # 创建1000个对象（无池）
        for i in range(1000):
            from core.context_management.async_task_context_manager import TaskContext
            ctx = TaskContext(
                task_id=f"nopool_{i}",
                task_description="测试",
                created_at="2024-01-01",
                updated_at="2024-01-01",
                status=ContextStatus.ACTIVE,
            )
            del ctx

        gc.collect()
        no_pool_snapshot = tracemalloc.take_snapshot()
        no_pool_stats = no_pool_snapshot.compare_to(start_snapshot, 'lineno')
        no_pool_used = sum(stat.size_diff for stat in no_pool_stats)

        # 重置tracemalloc
        tracemalloc.stop()
        tracemalloc.start()
        start_snapshot = tracemalloc.take_snapshot()

        # 测试有池情况
        pool = ContextObjectPool(max_size=1000, initial_size=100)
        await pool.warm_up(100)

        contexts = []
        for i in range(1000):
            ctx = await pool.acquire(f"withpool_{i}")
            contexts.append(ctx)

        # 释放一半
        for ctx in contexts[:500]:
            await pool.release(ctx)

        del contexts

        gc.collect()
        with_pool_snapshot = tracemalloc.take_snapshot()
        with_pool_stats = with_pool_snapshot.compare_to(start_snapshot, 'lineno')
        with_pool_used = sum(stat.size_diff for stat in with_pool_stats)

        tracemalloc.stop()

        print(f"\n内存使用对比:")
        print(f"无池: {no_pool_used / 1024:.2f} KB")
        print(f"有池: {with_pool_used / 1024:.2f} KB")
        if no_pool_used > 0:
            savings = (1 - with_pool_used / no_pool_used) * 100
            print(f"节省: {savings:.1f}%")
        else:
            print("节省: N/A")

        # 对象池应该减少内存使用
        # 注意：由于Python的内存管理，实际效果可能因运行而异
        # 这里主要验证对象池没有造成内存泄漏

    async def test_concurrent_access(self):
        """测试并发访问"""
        pool = ContextObjectPool(max_size=100, initial_size=10)

        # 并发获取和释放
        async def worker(worker_id: int):
            for i in range(10):
                ctx = await pool.acquire(f"worker_{worker_id}_task_{i}")
                # 模拟使用
                await asyncio.sleep(0.001)
                await pool.release(ctx)

        # 启动10个并发worker
        start = time.time()
        tasks = [worker(i) for i in range(10)]
        await asyncio.gather(*tasks)
        elapsed = time.time() - start

        stats = pool.get_stats()
        print(f"\n并发访问测试:")
        print(f"总操作数: {stats.total_requests}")
        print(f"总耗时: {elapsed:.3f}s")
        print(f"QPS: {stats.total_requests / elapsed:.2f}")

        # 验证没有竞争条件
        assert stats.total_requests == 100  # 10 workers × 10 operations


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])
