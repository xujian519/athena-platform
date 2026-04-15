#!/usr/bin/env python3
"""
性能和内存测试
Performance and Memory Tests

测试覆盖：
- 并发压力测试
- 内存泄漏检测
- 连接池性能测试
- 对象池性能测试
- 资源使用监控

Created by Athena AI系统
Date: 2025-12-14
Version: 1.0.0
"""

import asyncio
import gc
import logging
import time
import tracemalloc
from dataclasses import dataclass
from typing import Any

import pytest

# 导入被测试模块
from connection_pool_manager import (
    LLMConnectionPool,
    close_all_pools,
    get_llm_pool,
)
from object_pool_manager import (
    DictPool,
    ObjectPoolConfig,
    get_memory_optimizer,
    pooled_dict,
)

logger = logging.getLogger(__name__)


# =============================================================================
# 性能测试
# =============================================================================

class TestConnectionPoolPerformance:
    """连接池性能测试"""

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_acquisitions(self):
        """测试并发获取连接"""
        pool = get_llm_pool()
        await pool.initialize()

        # 并发获取和释放连接
        async def acquire_and_release():
            async with pool.connection():
                await asyncio.sleep(0.01)  # 模拟工作
                return True

        start = time.time()
        num_tasks = 100
        tasks = [acquire_and_release() for _ in range(num_tasks)]
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start

        throughput = num_tasks / elapsed
        assert all(results)
        assert throughput > 50  # 至少50 ops/sec

        logger.info(f"✅ 并发获取性能: {throughput:.2f} ops/sec")

        await close_all_pools()

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_pool_efficiency(self):
        """测试连接池效率"""
        pool = get_llm_pool()
        await pool.initialize()

        # 测试连接复用
        connections_used = set()

        async def track_connection(pool, tracker_set):
            async with pool.connection() as conn:
                # 追踪连接ID
                conn_id = id(conn)
                tracker_set.add(conn_id)
                await asyncio.sleep(0.01)

        start = time.time()
        tasks = [track_connection(pool, connections_used) for _ in range(50)]
        await asyncio.gather(*tasks)
        time.time() - start

        # 验证连接复用
        pool_stats = pool.get_stats()
        connection_reuse = len(connections_used) < 50

        logger.info(f"✅ 连接复用: {connection_reuse}")
        logger.info(f"   使用连接数: {len(connections_used)}/50")
        logger.info(f"   池统计: {pool_stats}")

        assert connection_reuse, "应该复用连接"

        await close_all_pools()

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_pool_scaling(self):
        """测试连接池扩展"""
        config = type('Config', (), {'min_size': 2, 'max_size': 10})()
        pool = LLMConnectionPool(config)
        await pool.initialize()

        # 初始大小
        initial_size = pool.stats.current_size
        assert initial_size == 2

        # 并发获取超过初始大小的连接
        async def use_connection():
            async with pool.connection():
                await asyncio.sleep(0.1)

        tasks = [use_connection() for _ in range(8)]
        await asyncio.gather(*tasks)

        # 验证池已扩展
        final_size = pool.stats.current_size
        assert final_size > initial_size

        logger.info(f"✅ 连接池扩展: {initial_size} -> {final_size}")

        await pool.close()


class TestObjectPoolPerformance:
    """对象池性能测试"""

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_dict_pool_performance(self):
        """测试字典对象池性能"""
        optimizer = get_memory_optimizer()
        await optimizer.initialize_all()

        # 使用对象池
        start = time.time()
        num_iterations = 1000

        for _ in range(num_iterations):
            async with pooled_dict() as d:
                for i in range(10):
                    d[f'key_{i}'] = f'value_{i}'

        elapsed_with_pool = time.time() - start

        # 不使用对象池
        start = time.time()
        for _ in range(num_iterations):
            d = {}
            for i in range(10):
                d[f'key_{i}'] = f'value_{i}'

        elapsed_without_pool = time.time() - start

        speedup = elapsed_without_pool / elapsed_with_pool

        logger.info("✅ 字典池性能:")
        logger.info(f"   使用池: {elapsed_with_pool:.3f}秒")
        logger.info(f"   不使用池: {elapsed_without_pool:.3f}秒")
        logger.info(f"   加速: {speedup:.2f}x")

        await optimizer.close_all()

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_object_reuse(self):
        """测试对象复用"""
        pool = DictPool()
        await pool.initialize()

        # 多次获取和释放
        for _ in range(50):
            obj = await pool.acquire()
            await pool.release(obj)

        stats = pool.get_stats()

        # 验证对象被复用
        reuse_rate = 1 - (stats['total_created'] / stats['total_acquired'])
        logger.info(f"✅ 对象复用率: {reuse_rate:.1%}")
        logger.info(f"   创建: {stats['total_created']}, 获取: {stats['total_acquired']}")

        assert reuse_rate > 0.5, "对象复用率应该大于50%"

        await pool.close()


# =============================================================================
# 内存测试
# =============================================================================

class TestMemoryLeaks:
    """内存泄漏测试"""

    @pytest.mark.asyncio
    @pytest.mark.memory
    async def test_connection_pool_no_leaks(self):
        """测试连接池无内存泄漏"""
        tracemalloc.start()

        # 获取基线内存
        gc.collect()
        baseline = tracemalloc.get_traced_memory()[0]

        # 使用连接池
        pool = get_llm_pool()
        await pool.initialize()

        # 执行多次操作
        for _ in range(100):
            async with pool.connection():
                await asyncio.sleep(0.001)

        # 清理
        await pool.close()
        gc.collect()

        # 检查内存增长
        final = tracemalloc.get_traced_memory()[0]
        memory_growth = final - baseline
        growth_kb = memory_growth / 1024

        logger.info(f"✅ 内存增长: {growth_kb:.2f} KB")

        # 内存增长应该小于1MB
        assert memory_growth < 1024 * 1024, f"内存泄漏检测: {growth_kb:.2f} KB"

        tracemalloc.stop()

    @pytest.mark.asyncio
    @pytest.mark.memory
    async def test_object_pool_no_leaks(self):
        """测试对象池无内存泄漏"""
        tracemalloc.start()

        # 获取基线
        gc.collect()
        baseline = tracemalloc.get_traced_memory()[0]

        # 使用对象池
        optimizer = get_memory_optimizer()
        await optimizer.initialize_all()

        # 执行多次操作
        for _ in range(1000):
            async with pooled_dict() as d:
                for i in range(10):
                    d[f'key_{i}'] = f'value_{i}'

        # 清理
        await optimizer.close_all()
        gc.collect()

        # 检查内存
        final = tracemalloc.get_traced_memory()[0]
        memory_growth = final - baseline
        growth_kb = memory_growth / 1024

        logger.info(f"✅ 内存增长: {growth_kb:.2f} KB")

        # 内存增长应该小于500KB
        assert memory_growth < 500 * 1024, f"内存泄漏检测: {growth_kb:.2f} KB"

        tracemalloc.stop()

    @pytest.mark.asyncio
    @pytest.mark.memory
    async def test_cleanup_effectiveness(self):
        """测试清理功能有效性"""
        pool = DictPool(ObjectPoolConfig(initial_size=20, max_size=100))
        await pool.initialize()

        initial_size = pool.stats.current_size
        logger.info(f"初始对象数: {initial_size}")

        # 获取并释放大量对象
        for _ in range(50):
            obj = await pool.acquire()
            await pool.release(obj)

        # 手动清理
        await pool._cleanup_idle_objects()

        final_size = pool.stats.current_size
        logger.info(f"清理后对象数: {final_size}")

        # 对象数应该接近初始大小
        assert final_size <= initial_size + 5, "清理功能应该移除多余对象"

        await pool.close()


# =============================================================================
# 压力测试
# =============================================================================

class TestStressTests:
    """压力测试"""

    @pytest.mark.asyncio
    @pytest.mark.stress
    async def test_high_concurrency(self):
        """高并发测试"""
        pool = get_llm_pool()
        await pool.initialize()

        num_concurrent = 200
        start = time.time()

        async def heavy_operation():
            async with pool.connection():
                # 模拟耗时操作
                await asyncio.sleep(0.1)

        tasks = [heavy_operation() for _ in range(num_concurrent)]
        await asyncio.gather(*tasks)

        elapsed = time.time() - start
        throughput = num_concurrent / elapsed

        logger.info("✅ 高并发测试:")
        logger.info(f"   并发数: {num_concurrent}")
        logger.info(f"   吞吐量: {throughput:.2f} ops/sec")
        logger.info(f"   平均延迟: {elapsed/num_concurrent*1000:.2f} ms")

        # 验证没有错误
        stats = pool.get_stats()
        assert stats['total_errors'] == 0, "应该没有错误"

        await close_all_pools()

    @pytest.mark.asyncio
    @pytest.mark.stress
    async def test_rapid_acquisition_release(self):
        """快速获取和释放测试"""
        pool = get_llm_pool()
        await pool.initialize()

        num_operations = 1000
        start = time.time()

        for _ in range(num_operations):
            async with pool.connection():
                pass  # 空操作

        elapsed = time.time() - start
        ops_per_sec = num_operations / elapsed

        logger.info("✅ 快速操作测试:")
        logger.info(f"   操作数: {num_operations}")
        logger.info(f"   吞吐量: {ops_per_sec:.2f} ops/sec")
        logger.info(f"   平均延迟: {elapsed/num_operations*1000:.2f} ms")

        # 应该能处理至少500 ops/sec
        assert ops_per_sec > 500, f"吞吐量太低: {ops_per_sec:.2f} ops/sec"

        await close_all_pools()

    @pytest.mark.asyncio
    @pytest.mark.stress
    async def test_memory_pressure(self):
        """内存压力测试"""
        optimizer = get_memory_optimizer()
        await optimizer.initialize_all()

        # 大量创建和销毁对象
        num_iterations = 5000

        start = time.time()
        for _ in range(num_iterations):
            async with pooled_dict() as d:
                # 填充数据
                for i in range(20):
                    d[f'key_{i}'] = f'value_{i}' * 10

        elapsed = time.time() - start
        ops_per_sec = num_iterations / elapsed

        logger.info("✅ 内存压力测试:")
        logger.info(f"   迭代次数: {num_iterations}")
        logger.info(f"   吞吐量: {ops_per_sec:.2f} ops/sec")

        # 检查内存使用
        memory_usage = optimizer.get_memory_usage_estimate()
        logger.info(f"   内存使用: {memory_usage}")

        # 内存效率应该大于70%
        assert memory_usage['memory_efficiency'] > 0.7, "内存效率太低"

        await optimizer.close_all()


# =============================================================================
# 资源监控
# =============================================================================

@dataclass
class ResourceSnapshot:
    """资源快照"""
    timestamp: float
    connection_stats: dict[str, Any]
    object_pool_stats: dict[str, Any]
    memory_usage: dict[str, Any]


class ResourceMonitor:
    """资源监控器"""

    def __init__(self):
        self.snapshots: list[ResourceSnapshot] = []
        self.logger = logging.getLogger(f"{__name__}.ResourceMonitor")

    async def take_snapshot(self) -> ResourceSnapshot:
        """获取资源快照"""
        # 连接池统计
        llm_pool = get_llm_pool()
        connection_stats = llm_pool.get_stats()

        # 对象池统计
        optimizer = get_memory_optimizer()
        object_pool_stats = optimizer.get_stats()

        # 内存使用
        memory_usage = optimizer.get_memory_usage_estimate()

        snapshot = ResourceSnapshot(
            timestamp=time.time(),
            connection_stats=connection_stats,
            object_pool_stats=object_pool_stats,
            memory_usage=memory_usage
        )

        self.snapshots.append(snapshot)
        return snapshot

    def analyze_trends(self) -> dict[str, Any]:
        """分析资源趋势"""
        if len(self.snapshots) < 2:
            return {}

        first = self.snapshots[0]
        last = self.snapshots[-1]

        return {
            'duration_seconds': last.timestamp - first.timestamp,
            'connection_growth': last.connection_stats['current_size'] - first.connection_stats['current_size'],
            'object_pool_growth': last.memory_usage['total_objects'] - first.memory_usage['total_objects'],
            'memory_efficiency_change': last.memory_usage['memory_efficiency'] - first.memory_usage['memory_efficiency']
        }


# =============================================================================
# 综合性能测试
# =============================================================================

async def comprehensive_performance_test():
    """综合性能测试"""
    logger.info("="*70)
    logger.info("🔬 综合性能测试")
    logger.info("="*70)

    # 初始化
    llm_pool = get_llm_pool()
    optimizer = get_memory_optimizer()

    await llm_pool.initialize()
    await optimizer.initialize_all()

    monitor = ResourceMonitor()

    # 测试1: 连接池性能
    logger.info("\n📝 测试1: 连接池并发性能")
    await monitor.take_snapshot()

    async def use_llm_connection():
        async with llm_pool.connection():
            await asyncio.sleep(0.05)

    start = time.time()
    tasks = [use_llm_connection() for _ in range(50)]
    await asyncio.gather(*tasks)
    elapsed = time.time() - start

    logger.info(f"   完成: 50个任务, 耗时: {elapsed:.2f}秒")
    logger.info(f"   吞吐量: {50/elapsed:.2f} ops/sec")

    # 测试2: 对象池性能
    logger.info("\n📝 测试2: 对象池性能")
    await monitor.take_snapshot()

    start = time.time()
    for _ in range(1000):
        async with pooled_dict() as d:
            for i in range(5):
                d[f'key_{i}'] = f'value_{i}'

    elapsed = time.time() - start
    logger.info(f"   完成: 1000次操作, 耗时: {elapsed:.2f}秒")
    logger.info(f"   吞吐量: {1000/elapsed:.2f} ops/sec")

    # 测试3: 资源趋势分析
    logger.info("\n📝 测试3: 资源趋势分析")
    trends = monitor.analyze_trends()
    logger.info(f"   趋势: {trends}")

    # 测试4: 最终统计
    logger.info("\n📝 测试4: 最终统计")
    logger.info(f"   连接池: {llm_pool.get_stats()}")
    logger.info(f"   内存使用: {optimizer.get_memory_usage_estimate()}")
    logger.info(f"   对象池: {optimizer.get_stats()}")

    # 清理
    await llm_pool.close()
    await optimizer.close_all()

    logger.info("\n" + "="*70)
    logger.info("🎉 综合性能测试完成！")
    logger.info("="*70)


# =============================================================================
# 运行测试
# =============================================================================

def run_tests():
    """运行所有测试"""
    pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '-m', 'performance or memory or stress'
    ])


if __name__ == '__main__':
    # 运行综合测试
    asyncio.run(comprehensive_performance_test())

    # 或运行pytest测试
    # run_tests()
