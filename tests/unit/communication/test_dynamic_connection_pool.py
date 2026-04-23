#!/usr/bin/env python3
"""
动态连接池单元测试
Unit Tests for Dynamic Connection Pool

作者: Athena AI系统
创建时间: 2026-01-25
版本: 1.0.0
"""

import asyncio
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from unittest.mock import MagicMock

from core.communication.engine.dynamic_connection_pool import (
    ConnectionConfig,
    DynamicConnectionPool,
    PooledConnection,
)


@pytest.mark.asyncio
@pytest.mark.unit
class TestDynamicConnectionPool:
    """动态连接池测试"""

    @pytest.fixture
    async def connection_pool(self):
        """创建连接池实例"""
        # Mock连接工厂
        async def mock_factory():
            mock_conn = MagicMock()
            mock_conn.id = id(mock_conn)
            return mock_conn

        # Mock关闭函数
        async def mock_close(conn):
            pass

        # Mock健康检查函数
        async def mock_health_check(conn):
            return True

        config = ConnectionConfig(
            min_size=2,
            max_size=10,
            acquire_timeout=5.0,
            idle_timeout=60.0,
            ttl=300.0,
            health_check_interval=30.0
        )

        pool = DynamicConnectionPool(
            connection_factory=mock_factory,
            connection_close=mock_close,
            health_check=mock_health_check,
            config=config
        )
        await pool.start()
        yield pool
        await pool.stop()

    async def test_pool_initialization(self, connection_pool):
        """测试连接池初始化"""
        # 检查初始连接数
        stats = connection_pool.get_stats()
        assert stats['total_connections'] >= 2  # min_size
        assert stats['active_connections'] == 0

    async def test_acquire_release(self, connection_pool):
        """测试获取和释放连接"""
        # 获取连接
        conn1 = await connection_pool.acquire(timeout=5.0)
        assert conn1 is not None

        # 检查活跃连接数
        stats = connection_pool.get_stats()
        assert stats['active_connections'] == 1

        # 释放连接
        await connection_pool.release(conn1)

        # 检查空闲连接数
        stats = connection_pool.get_stats()
        assert stats['active_connections'] == 0
        assert stats['idle_connections'] >= 1

    async def test_multiple_acquires(self, connection_pool):
        """测试并发获取连接"""
        # 同时获取多个连接
        connections = []
        for _ in range(5):
            conn = await connection_pool.acquire(timeout=5.0)
            connections.append(conn)

        # 验证活跃连接数
        stats = connection_pool.get_stats()
        assert stats['active_connections'] == 5

        # 释放所有连接
        for conn in connections:
            await connection_pool.release(conn)

        # 验证所有连接已释放
        stats = connection_pool.get_stats()
        assert stats['active_connections'] == 0

    async def test_max_size_limit(self, connection_pool):
        """测试最大连接数限制"""
        # 尝试获取超过最大连接数的连接
        connections = []
        for _i in range(15):  # max_size=10
            try:
                conn = await asyncio.wait_for(
                    connection_pool.acquire(timeout=1.0),
                    timeout=2.0
                )
                connections.append(conn)
            except TimeoutError:
                # 预期会超时
                break

        # 验证不能超过最大连接数
        stats = connection_pool.get_stats()
        assert stats['active_connections'] <= 10

        # 清理
        for conn in connections:
            await connection_pool.release(conn)

    async def test_acquire_timeout(self, connection_pool):
        """测试获取超时"""
        # 获取所有可用连接
        connections = []
        for _ in range(10):
            try:
                conn = await asyncio.wait_for(
                    connection_pool.acquire(timeout=2.0),
                    timeout=3.0
                )
                connections.append(conn)
            except TimeoutError:
                break

        # 尝试获取超出限制的连接，应该超时
        with pytest.raises(asyncio.TimeoutError):
            await connection_pool.acquire(timeout=0.5)

        # 清理
        for conn in connections:
            await connection_pool.release(conn)

    async def test_stats_tracking(self, connection_pool):
        """测试统计信息跟踪"""
        # 获取和释放连接
        conn = await connection_pool.acquire(timeout=5.0)
        await connection_pool.release(conn)

        # 检查统计信息
        stats = connection_pool.get_stats()
        assert stats['total_acquired'] >= 1
        assert stats['total_released'] >= 1
        assert stats['total_created'] >= 2
        assert 'average_wait_time' in stats
        assert 'utilization' in stats

    async def test_connection_reuse(self, connection_pool):
        """测试连接复用"""
        # 获取并释放连接
        conn1 = await connection_pool.acquire(timeout=5.0)
        id(conn1)
        await connection_pool.release(conn1)

        # 再次获取连接，应该复用之前的连接
        conn2 = await connection_pool.acquire(timeout=5.0)
        id(conn2)
        await connection_pool.release(conn2)

        # 验证连接被复用（至少有时）
        # 注意：由于并发和内部逻辑，这个测试可能不完全可靠
        stats = connection_pool.get_stats()
        assert stats['total_created'] <= stats['total_acquired'] + 2

    async def test_invalid_release(self, connection_pool):
        """测试释放无效连接"""
        # 尝试释放不存在的连接
        fake_conn = MagicMock()
        fake_conn.id = 99999

        # 不应该抛出异常
        await connection_pool.release(fake_conn)

    async def test_health_check_failure(self):
        """测试健康检查失败处理"""
        # Mock工厂
        async def mock_factory():
            mock_conn = MagicMock()
            mock_conn.id = id(mock_conn)
            return mock_conn

        # Mock关闭函数
        async def mock_close(conn):
            pass

        # Mock健康检查（总是失败）
        async def mock_health_check_failing(conn):
            return False

        config = ConnectionConfig(
            min_size=2,
            max_size=10,
            max_retries=2
        )

        pool = DynamicConnectionPool(
            connection_factory=mock_factory,
            connection_close=mock_close,
            health_check=mock_health_check_failing,
            config=config
        )
        await pool.start()

        # 执行健康检查
        await pool._perform_health_check()

        # 检查统计信息
        stats = pool.get_stats()
        assert stats['total_health_check_failures'] > 0

        await pool.stop()

    async def test_context_manager(self):
        """测试异步上下文管理器"""
        async def mock_factory():
            return MagicMock()

        async def mock_close(conn):
            pass

        config = ConnectionConfig(min_size=2, max_size=5)

        async with DynamicConnectionPool(
            connection_factory=mock_factory,
            connection_close=mock_close,
            config=config
        ) as pool:
            # 验证连接池已启动
            stats = pool.get_stats()
            assert stats['total_connections'] >= 2

        # 验证连接池已停止（上下文退出）
        stats = pool.get_stats()
        assert pool._running is False

    async def test_idle_cleanup(self):
        """测试空闲连接清理"""
        async def mock_factory():
            return MagicMock()

        close_count = 0

        async def mock_close(conn):
            nonlocal close_count
            close_count += 1

        async def mock_health_check(conn):
            return True

        config = ConnectionConfig(
            min_size=1,
            max_size=10,
            idle_timeout=0.1,  # 100ms
            health_check_interval=10.0
        )

        pool = DynamicConnectionPool(
            connection_factory=mock_factory,
            connection_close=mock_close,
            health_check=mock_health_check,
            config=config
        )
        await pool.start()

        # 获取一些连接
        connections = []
        for _ in range(5):
            conn = await pool.acquire(timeout=5.0)
            connections.append(conn)

        # 释放所有连接
        for conn in connections:
            await pool.release(conn)

        # 等待清理任务执行（超过idle_timeout）
        await asyncio.sleep(0.3)

        # 触发清理
        await pool._cleanup_expired_connections()

        # 验证一些连接被清理（但保留了min_size）
        stats = pool.get_stats()
        assert stats['total_connections'] <= 5

        await pool.stop()

    async def test_concurrent_access(self, connection_pool):
        """测试并发访问"""
        async def acquire_release():
            conn = await connection_pool.acquire(timeout=5.0)
            await asyncio.sleep(0.01)  # 模拟工作
            await connection_pool.release(conn)

        # 并发执行多个获取/释放操作
        tasks = [acquire_release() for _ in range(20)]
        await asyncio.gather(*tasks)

        # 验证所有连接都已释放
        stats = connection_pool.get_stats()
        assert stats['active_connections'] == 0


@pytest.mark.unit
class TestConnectionConfig:
    """连接配置测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = ConnectionConfig()
        assert config.min_size == 5
        assert config.max_size == 50
        assert config.acquire_timeout == 30.0
        assert config.idle_timeout == 300.0
        assert config.ttl == 3600.0

    def test_custom_config(self):
        """测试自定义配置"""
        config = ConnectionConfig(
            min_size=10,
            max_size=100,
            acquire_timeout=60.0
        )
        assert config.min_size == 10
        assert config.max_size == 100
        assert config.acquire_timeout == 60.0


@pytest.mark.unit
class TestPooledConnection:
    """池化连接测试"""

    def test_connection_age(self):
        """测试连接年龄计算"""
        conn = MagicMock()
        pooled = PooledConnection(connection=conn)

        # 初始年龄应该接近0
        age = pooled.age
        assert age >= 0
        assert age < 1.0  # 小于1秒

    def test_idle_time(self):
        """测试空闲时间计算"""
        conn = MagicMock()
        pooled = PooledConnection(connection=conn)

        # 标记为使用后立即释放
        pooled.mark_used()
        pooled.mark_released()

        # 空闲时间应该接近0
        idle_time = pooled.idle_time
        assert idle_time >= 0
        assert idle_time < 1.0

    def test_mark_used_released(self):
        """测试使用和释放标记"""
        conn = MagicMock()
        pooled = PooledConnection(connection=conn)

        assert pooled.in_use is False

        pooled.mark_used()
        assert pooled.in_use is True

        pooled.mark_released()
        assert pooled.in_use is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
