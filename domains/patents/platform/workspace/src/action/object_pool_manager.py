#!/usr/bin/env python3
"""
对象池管理器
Object Pool Manager

功能特性：
- 通用对象池
- 减少对象创建开销
- 内存复用优化
- 对象池监控

Created by Athena AI系统
Date: 2025-12-14
Version: 1.0.0
"""

import asyncio
import logging
import time
import weakref
from collections import deque
from collections.abc import Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class ObjectPoolConfig:
    """对象池配置"""
    initial_size: int = 5         # 初始对象数
    max_size: int = 50            # 最大对象数
    max_idle_time: int = 300      # 最大空闲时间（秒）
    cleanup_interval: int = 60    # 清理间隔（秒）


@dataclass
class PoolItem:
    """池项包装"""
    obj: Any
    created_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)
    use_count: int = 0


class ObjectPool:
    """通用对象池"""

    def __init__(self,
                 name: str,
                 factory: Callable[[], T],
                 reset: Callable[[T], None] | None = None,
                 config: ObjectPoolConfig | None = None):
        """
        初始化对象池

        Args:
            name: 对象池名称
            factory: 对象工厂函数
            reset: 对象重置函数（可选）
            config: 对象池配置
        """
        self.name = name
        self.factory = factory
        self.reset = reset
        self.config = config or ObjectPoolConfig()

        self.logger = logging.getLogger(f"{__name__}.{name}")

        # 对象池
        self._pool: deque = deque()
        self._active_objects: weakref.WeakSet = weakref.WeakSet()

        # 统计信息
        self.stats = {
            'total_created': 0,
            'total_acquired': 0,
            'total_released': 0,
            'total_reset': 0,
            'current_size': 0,
            'active_count': 0,
            'idle_count': 0
        }

        # 清理任务
        self._cleanup_task = None

        self.logger.info(f"✅ {name} 对象池初始化完成")

    async def initialize(self):
        """初始化对象池（创建初始对象）"""
        for _ in range(self.config.initial_size):
            obj = self._create_object()
            self._pool.append(obj)

        self.stats['current_size'] = len(self._pool)
        self.stats['idle_count'] = len(self._pool)

        # 启动清理任务
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

        self.logger.info(f"✅ {self.name} 对象池初始化完成，创建了 {len(self._pool)} 个对象")

    async def acquire(self) -> T:
        """
        获取对象

        Returns:
            对象实例
        """
        # 尝试从池中获取
        if self._pool:
            item = self._pool.popleft()
            item.last_used = time.time()
            item.use_count += 1
            self._active_objects.add(item.obj)

            self.stats['total_acquired'] += 1
            self.stats['idle_count'] = len(self._pool)
            self.stats['active_count'] = len(self._active_objects)

            return item.obj

        # 池中无对象，创建新对象
        if self.stats['current_size'] < self.config.max_size:
            obj = self._create_object()
            self._active_objects.add(obj)

            self.stats['total_acquired'] += 1
            self.stats['active_count'] = len(self._active_objects)

            return obj

        # 已达最大对象数，等待或创建临时对象
        self.logger.warning(f"⚠️ {self.name} 对象池已耗尽，创建临时对象")
        return self.factory()

    async def release(self, obj: T):
        """
        释放对象

        Args:
            obj: 对象实例
        """
        if obj in self._active_objects:
            self._active_objects.remove(obj)

            # 重置对象状态
            if self.reset:
                try:
                    self.reset(obj)
                    self.stats['total_reset'] += 1
                except Exception as e:
                    self.logger.warning(f"⚠️ 重置对象失败: {e}")
                    # 重置失败，丢弃对象
                    self.stats['current_size'] -= 1
                    return

            # 放回池中
            item = PoolItem(obj=obj)
            self._pool.append(item)

            self.stats['total_released'] += 1
            self.stats['idle_count'] = len(self._pool)

    @asynccontextmanager
    async def object(self):
        """对象上下文管理器"""
        obj = await self.acquire()
        try:
            yield obj
        finally:
            await self.release(obj)

    def _create_object(self) -> T:
        """创建新对象"""
        obj = self.factory()
        self.stats['total_created'] += 1
        self.stats['current_size'] += 1
        return obj

    async def _cleanup_loop(self):
        """定期清理空闲对象"""
        while True:
            try:
                await asyncio.sleep(self.config.cleanup_interval)
                await self._cleanup_idle_objects()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"❌ 清理任务失败: {e}")

    async def _cleanup_idle_objects(self):
        """清理空闲对象"""
        current_time = time.time()
        removed_count = 0

        # 保留最小数量的对象
        min_keep = self.config.initial_size
        while len(self._pool) > min_keep:
            item = self._pool[0]  # 查看最老的对象
            idle_time = current_time - item.last_used

            if idle_time > self.config.max_idle_time:
                self._pool.popleft()
                self.stats['current_size'] -= 1
                removed_count += 1
            else:
                break

        if removed_count > 0:
            self.stats['idle_count'] = len(self._pool)
            self.logger.info(f"🧹 清理了 {removed_count} 个空闲对象")

    async def close(self):
        """关闭对象池"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # 清空对象池
        self._pool.clear()
        self._active_objects.clear()

        self.stats['current_size'] = 0
        self.stats['idle_count'] = 0
        self.stats['active_count'] = 0

        self.logger.info(f"🔌 {self.name} 对象池已关闭")

    def get_stats(self) -> dict[str, Any]:
        """获取对象池统计"""
        return {
            'name': self.name,
            'total_created': self.stats['total_created'],
            'total_acquired': self.stats['total_acquired'],
            'total_released': self.stats['total_released'],
            'total_reset': self.stats['total_reset'],
            'current_size': self.stats['current_size'],
            'active_count': self.stats['active_count'],
            'idle_count': self.stats['idle_count'],
            'utilization': self.stats['active_count'] / self.config.max_size if self.config.max_size > 0 else 0
        }


# =============================================================================
# 专用对象池
# =============================================================================

class StringBuilderPool(ObjectPool):
    """字符串构建器对象池"""

    @staticmethod
    def factory() -> list:
        return []

    @staticmethod
    def reset(obj: list):
        obj.clear()

    def __init__(self, config: ObjectPoolConfig | None = None):
        super().__init__(
            "StringBuilderPool",
            self.factory,
            self.reset,
            config or ObjectPoolConfig(initial_size=10, max_size=100)
        )


class DictPool(ObjectPool):
    """字典对象池"""

    @staticmethod
    def factory() -> dict:
        return {}

    @staticmethod
    def reset(obj: dict):
        obj.clear()

    def __init__(self, config: ObjectPoolConfig | None = None):
        super().__init__(
            "DictPool",
            self.factory,
            self.reset,
            config or ObjectPoolConfig(initial_size=10, max_size=100)
        )


class ListPool(ObjectPool):
    """列表对象池"""

    @staticmethod
    def factory() -> list:
        return []

    @staticmethod
    def reset(obj: list):
        obj.clear()

    def __init__(self, config: ObjectPoolConfig | None = None):
        super().__init__(
            "ListPool",
            self.factory,
            self.reset,
            config or ObjectPoolConfig(initial_size=20, max_size=200)
        )


class ByteArrayPool(ObjectPool):
    """字节数组对象池"""

    @staticmethod
    def factory() -> bytearray:
        return bytearray(4096)  # 4KB缓冲区

    @staticmethod
    def reset(obj: bytearray):
        obj.clear()

    def __init__(self, buffer_size: int = 4096, config: ObjectPoolConfig | None = None):
        self.buffer_size = buffer_size
        super().__init__(
            "ByteArrayPool",
            self.factory,
            self.reset,
            config or ObjectPoolConfig(initial_size=5, max_size=50)
        )


# =============================================================================
# 内存优化工具
# =============================================================================

class MemoryOptimizer:
    """内存优化工具"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.MemoryOptimizer")
        self.pools: dict[str, ObjectPool] = {}

    def register_pool(self, name: str, pool: ObjectPool):
        """注册对象池"""
        self.pools[name] = pool
        self.logger.info(f"✅ 注册对象池: {name}")

    async def initialize_all(self):
        """初始化所有对象池"""
        for pool in self.pools.values():
            await pool.initialize()
        self.logger.info("✅ 所有对象池已初始化")

    async def close_all(self):
        """关闭所有对象池"""
        for pool in self.pools.values():
            await pool.close()
        self.pools.clear()
        self.logger.info("🔌 所有对象池已关闭")

    def get_stats(self) -> dict[str, dict[str, Any]:
        """获取所有对象池统计"""
        return {
            name: pool.get_stats()
            for name, pool in self.pools.items()
        }

    async def cleanup_all(self):
        """清理所有对象池的空闲对象"""
        for pool in self.pools.values():
            await pool._cleanup_idle_objects()
        self.logger.info("🧹 所有对象池已清理")

    def get_memory_usage_estimate(self) -> dict[str, Any]:
        """估算内存使用"""
        total_objects = sum(pool.stats['current_size'] for pool in self.pools.values())
        active_objects = sum(pool.stats['active_count'] for pool in self.pools.values())
        idle_objects = sum(pool.stats['idle_count'] for pool in self.pools.values())

        return {
            'total_objects': total_objects,
            'active_objects': active_objects,
            'idle_objects': idle_objects,
            'pool_count': len(self.pools),
            'memory_efficiency': idle_objects / total_objects if total_objects > 0 else 0
        }


# =============================================================================
# 全局对象池管理器
# =============================================================================

_global_optimizer: MemoryOptimizer | None = None


def get_memory_optimizer() -> MemoryOptimizer:
    """获取内存优化器（单例）"""
    global _global_optimizer
    if _global_optimizer is None:
        _global_optimizer = MemoryOptimizer()

        # 注册常用对象池
        _global_optimizer.register_pool('string_builder', StringBuilderPool())
        _global_optimizer.register_pool('dict', DictPool())
        _global_optimizer.register_pool('list', ListPool())
        _global_optimizer.register_pool('byte_array', ByteArrayPool())

    return _global_optimizer


# =============================================================================
# 便利函数
# =============================================================================

async def get_dict() -> dict:
    """从对象池获取字典"""
    optimizer = get_memory_optimizer()
    pool = optimizer.pools.get('dict')
    if pool:
        return await pool.acquire()
    return {}


async def release_dict(obj: dict):
    """释放字典到对象池"""
    optimizer = get_memory_optimizer()
    pool = optimizer.pools.get('dict')
    if pool:
        await pool.release(obj)


async def get_list() -> list:
    """从对象池获取列表"""
    optimizer = get_memory_optimizer()
    pool = optimizer.pools.get('list')
    if pool:
        return await pool.acquire()
    return []


async def release_list(obj: list):
    """释放列表到对象池"""
    optimizer = get_memory_optimizer()
    pool = optimizer.pools.get('list')
    if pool:
        await pool.release(obj)


# =============================================================================
# 上下文管理器
# =============================================================================

@asynccontextmanager
async def pooled_dict():
    """字典对象池上下文管理器"""
    obj = await get_dict()
    try:
        yield obj
    finally:
        await release_dict(obj)


@asynccontextmanager
async def pooled_list():
    """列表对象池上下文管理器"""
    obj = await get_list()
    try:
        yield obj
    finally:
        await release_list(obj)


# =============================================================================
# 测试代码
# =============================================================================

async def test_object_pools():
    """测试对象池"""
    logger.info("="*60)
    logger.info("🧪 测试对象池")
    logger.info("="*60)

    # 获取内存优化器
    optimizer = get_memory_optimizer()
    await optimizer.initialize_all()

    # 测试1: 字典对象池
    logger.info("\n📝 测试1: 字典对象池")
    async with pooled_dict() as d:
        d['key1'] = 'value1'
        d['key2'] = 'value2'
        logger.info(f"✅ 使用池化字典: {d}")

    stats = optimizer.pools['dict'].get_stats()
    logger.info(f"   字典池统计: {stats}")

    # 测试2: 列表对象池
    logger.info("\n📝 测试2: 列表对象池")
    async with pooled_list() as lst:
        lst.extend([1, 2, 3, 4, 5])
        logger.info(f"✅ 使用池化列表: {lst}")

    stats = optimizer.pools['list'].get_stats()
    logger.info(f"   列表池统计: {stats}")

    # 测试3: 并发使用对象池
    logger.info("\n📝 测试3: 并发使用对象池")
    async def use_pooled_objects():
        async with pooled_dict() as d:
            for i in range(10):
                d[f'key_{i}'] = f'value_{i}'
            await asyncio.sleep(0.01)

    start = time.time()
    tasks = [use_pooled_objects() for _ in range(20)]
    await asyncio.gather(*tasks)
    elapsed = time.time() - start

    logger.info(f"✅ 并发测试完成: {len(tasks)} 个任务, 耗时: {elapsed:.2f}秒")

    # 测试4: 内存使用估算
    logger.info("\n📝 测试4: 内存使用估算")
    memory_usage = optimizer.get_memory_usage_estimate()
    logger.info(f"   内存使用: {memory_usage}")

    # 测试5: 所有对象池统计
    logger.info("\n📝 测试5: 所有对象池统计")
    all_stats = optimizer.get_stats()
    for name, stats in all_stats.items():
        logger.info(f"   {name}: {stats}")

    # 清理
    await optimizer.close_all()

    logger.info("\n" + "="*60)
    logger.info("🎉 测试完成！")
    logger.info("="*60)


if __name__ == '__main__':
    asyncio.run(test_object_pools())
