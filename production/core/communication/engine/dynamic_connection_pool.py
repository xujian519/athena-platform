#!/usr/bin/env python3
"""
动态连接池
Dynamic Connection Pool

提供高性能的异步连接池管理,支持健康检查、TTL和动态扩缩容

作者: Athena AI系统
创建时间: 2026-01-25
版本: 1.0.0
"""

from __future__ import annotations
import asyncio
import contextlib
import logging
import time
from collections import deque
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ConnectionStats:
    """连接统计信息"""

    total_created: int = 0
    total_acquired: int = 0
    total_released: int = 0
    total_failed: int = 0
    total_health_checks: int = 0
    total_health_check_failures: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    last_health_check: datetime | None = None
    average_wait_time: float = 0.0


@dataclass
class ConnectionConfig:
    """连接池配置"""

    min_size: int = 5  # 最小连接数
    max_size: int = 50  # 最大连接数
    acquire_timeout: float = 30.0  # 获取连接超时(秒)
    idle_timeout: float = 300.0  # 空闲超时(秒)
    ttl: float = 3600.0  # 连接TTL(秒)
    health_check_interval: float = 60.0  # 健康检查间隔(秒)
    health_check_timeout: float = 5.0  # 健康检查超时(秒)
    max_retries: int = 3  # 最大重试次数
    retry_delay: float = 1.0  # 重试延迟(秒)


@dataclass
class PooledConnection:
    """池化连接"""

    connection: Any
    created_at: datetime = field(default_factory=datetime.now)
    last_used: datetime = field(default_factory=datetime.now)
    last_health_check: datetime | None = None
    health_check_failures: int = 0
    is_healthy: bool = True
    in_use: bool = False

    @property
    def age(self) -> float:
        """连接年龄(秒)"""
        return (datetime.now() - self.created_at).total_seconds()

    @property
    def idle_time(self) -> float:
        """空闲时间(秒)"""
        return (datetime.now() - self.last_used).total_seconds()

    def mark_used(self) -> None:
        """标记为已使用"""
        self.last_used = datetime.now()
        self.in_use = True

    def mark_released(self) -> None:
        """标记为已释放"""
        self.last_used = datetime.now()
        self.in_use = False


class DynamicConnectionPool:
    """
    动态连接池

    特性:
    - 异步连接获取和释放
    - 动态扩缩容
    - 健康检查和自动恢复
    - TTL和空闲超时管理
    - 连接统计和监控
    """

    def __init__(
        self,
        connection_factory: Callable[[], Awaitable[Any]],
        connection_close: Callable[[Any], Awaitable[None]],
        health_check: Callable[[Any, Awaitable[bool]]] | None = None,
        config: ConnectionConfig | None = None,
    ):
        """
        初始化连接池

        Args:
            connection_factory: 创建连接的异步函数
            connection_close: 关闭连接的异步函数
            health_check: 健康检查的异步函数(可选)
            config: 连接池配置(可选)
        """
        self.connection_factory = connection_factory
        self.connection_close = connection_close
        self.health_check = health_check
        self.config = config or ConnectionConfig()

        # 连接池
        self._idle_connections: deque[PooledConnection] = deque()
        self._active_connections: set[PooledConnection] = set()
        self._all_connections: set[PooledConnection] = set()

        # 同步原语
        self._lock = asyncio.Lock()
        self._available = asyncio.Condition(self._lock)
        self._running = False

        # 统计信息
        self.stats = ConnectionStats()
        self._wait_times: deque[float] = deque(maxlen=1000)

        # 后台任务
        self._health_check_task: asyncio.Task[None] | None | None = None
        self._cleanup_task: asyncio.Task[None] | None | None = None

        logger.info(f"🔗 连接池初始化: min={self.config.min_size}, " f"max={self.config.max_size}")

    async def start(self) -> None:
        """启动连接池"""
        if self._running:
            logger.warning("连接池已在运行")
            return

        self._running = True

        # 初始化最小连接数
        await self._initialize_pool()

        # 启动健康检查任务
        if self.health_check:
            self._health_check_task = asyncio.create_task(self._health_check_loop())

        # 启动清理任务
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

        logger.info("🚀 连接池已启动")

    async def stop(self) -> None:
        """停止连接池"""
        if not self._running:
            return

        self._running = False

        # 取消后台任务
        if self._health_check_task:
            self._health_check_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()

        # 等待任务完成
        tasks = [t for t in [self._health_check_task, self._cleanup_task] if t]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        # 关闭所有连接
        await self._close_all_connections()

        logger.info("⏹️ 连接池已停止")

    async def _initialize_pool(self) -> None:
        """初始化连接池到最小大小"""
        async with self._lock:
            while len(self._all_connections) < self.config.min_size:
                try:
                    conn = await self._create_connection()
                    self._idle_connections.append(conn)
                except Exception as e:
                    logger.error(f"初始化连接失败: {e}")
                    break

        logger.info(f"✅ 连接池初始化完成: {len(self._all_connections)}个连接")

    async def acquire(self, timeout: float | None = None) -> Any:
        """
        获取连接

        Args:
            timeout: 获取超时时间(秒),None表示使用配置的默认值

        Returns:
            Any: 连接对象

        Raises:
            asyncio.TimeoutError: 获取超时
            Exception: 创建连接失败
        """
        timeout = timeout or self.config.acquire_timeout
        start_time = time.time()

        try:
            async with self._available:
                # 等待可用连接
                deadline = asyncio.get_event_loop().time() + timeout

                while True:
                    # 尝试获取空闲连接
                    if self._idle_connections:
                        pooled = self._idle_connections.popleft()

                        # 检查连接是否健康
                        if pooled.is_healthy:
                            pooled.mark_used()
                            self._active_connections.add(pooled)
                            self.stats.total_acquired += 1

                            wait_time = time.time() - start_time
                            self._wait_times.append(wait_time)
                            self.stats.average_wait_time = sum(self._wait_times) / len(
                                self._wait_times
                            )

                            return pooled.connection
                        else:
                            # 移除不健康的连接
                            await self._close_connection(pooled)

                    # 检查是否可以创建新连接
                    if len(self._all_connections) < self.config.max_size:
                        try:
                            pooled = await self._create_connection()
                            pooled.mark_used()
                            self._active_connections.add(pooled)
                            self.stats.total_acquired += 1

                            wait_time = time.time() - start_time
                            self._wait_times.append(wait_time)
                            self.stats.average_wait_time = sum(self._wait_times) / len(
                                self._wait_times
                            )

                            return pooled.connection
                        except Exception as e:
                            logger.error(f"创建连接失败: {e}")
                            self.stats.total_failed += 1

                    # 等待连接可用
                    remaining = deadline - asyncio.get_event_loop().time()
                    if remaining <= 0:
                        raise asyncio.TimeoutError(f"获取连接超时({timeout}秒)")

                    await asyncio.wait_for(self._available.wait(), timeout=remaining)

        except asyncio.TimeoutError:
            self.stats.total_failed += 1
            raise
        except Exception as e:
            self.stats.total_failed += 1
            logger.error(f"获取连接失败: {e}")
            raise

    async def release(self, connection: Any) -> None:
        """
        释放连接

        Args:
            connection: 要释放的连接对象
        """
        async with self._lock:
            # 查找对应的PooledConnection
            pooled = None
            for p in self._active_connections:
                if p.connection == connection:
                    pooled = p
                    break

            if not pooled:
                logger.warning("尝试释放不存在的连接")
                return

            # 从活跃连接中移除
            self._active_connections.discard(pooled)

            # 检查连接是否健康
            if not pooled.is_healthy:
                await self._close_connection(pooled)
                self.stats.total_released += 1
                return

            # 标记为空闲
            pooled.mark_released()
            self._idle_connections.append(pooled)
            self.stats.total_released += 1

            # 通知等待的获取者
            self._available.notify()

    async def _create_connection(self) -> PooledConnection:
        """创建新连接"""
        connection = await self.connection_factory()
        pooled = PooledConnection(connection=connection)

        self._all_connections.add(pooled)
        self.stats.total_created += 1
        self.stats.active_connections = len(self._active_connections)
        self.stats.idle_connections = len(self._idle_connections)

        logger.debug(f"创建新连接,当前总数: {len(self._all_connections)}")

        return pooled

    async def _close_connection(self, pooled: PooledConnection) -> None:
        """关闭连接"""
        try:
            await self.connection_close(pooled.connection)
        except Exception as e:
            logger.error(f"关闭连接失败: {e}")

        self._all_connections.discard(pooled)
        self._active_connections.discard(pooled)

        # 从空闲队列中移除
        with contextlib.suppress(ValueError):
            self._idle_connections.remove(pooled)

        self.stats.active_connections = len(self._active_connections)
        self.stats.idle_connections = len(self._idle_connections)

    async def _close_all_connections(self) -> None:
        """关闭所有连接"""
        tasks = []

        for pooled in list(self._all_connections):
            tasks.append(self._close_connection(pooled))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        logger.info(f"已关闭所有连接,共{len(tasks)}个")

    async def _health_check_loop(self) -> None:
        """健康检查循环"""
        while self._running:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                await self._perform_health_check()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"健康检查异常: {e}")

    async def _perform_health_check(self) -> None:
        """执行健康检查"""
        if not self.health_check:
            return

        self.stats.total_health_checks += 1
        self.stats.last_health_check = datetime.now()

        async with self._lock:
            # 检查所有连接
            for pooled in list(self._all_connections):
                try:
                    # 执行健康检查
                    is_healthy = await asyncio.wait_for(
                        self.health_check(pooled.connection),
                        timeout=self.config.health_check_timeout,
                    )

                    if is_healthy:
                        pooled.is_healthy = True
                        pooled.health_check_failures = 0
                        pooled.last_health_check = datetime.now()
                    else:
                        pooled.health_check_failures += 1
                        self.stats.total_health_check_failures += 1

                        # 连续失败多次则标记为不健康
                        if pooled.health_check_failures >= self.config.max_retries:
                            pooled.is_healthy = False
                            logger.warning(
                                f"连接健康检查连续失败{pooled.health_check_failures}次,"
                                f"标记为不健康"
                            )

                except asyncio.TimeoutError:
                    pooled.health_check_failures += 1
                    self.stats.total_health_check_failures += 1
                    logger.warning("健康检查超时")

                except Exception as e:
                    pooled.health_check_failures += 1
                    self.stats.total_health_check_failures += 1
                    logger.error(f"健康检查异常: {e}")

    async def _cleanup_loop(self) -> None:
        """清理循环"""
        while self._running:
            try:
                await asyncio.sleep(30)  # 每30秒清理一次
                await self._cleanup_expired_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"清理异常: {e}")

    async def _cleanup_expired_connections(self) -> None:
        """清理过期连接"""
        async with self._lock:
            datetime.now()
            to_close = []

            # 检查空闲连接
            for pooled in list(self._idle_connections):
                # TTL超时
                if pooled.age > self.config.ttl:
                    to_close.append(pooled)
                    continue

                # 空闲超时(但保持最小连接数)
                if (
                    pooled.idle_time > self.config.idle_timeout
                    and len(self._all_connections) > self.config.min_size
                ):
                    to_close.append(pooled)
                    continue

            # 关闭过期连接
            for pooled in to_close:
                await self._close_connection(pooled)

            if to_close:
                logger.info(f"清理了{len(to_close)}个过期连接")

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "total_created": self.stats.total_created,
            "total_acquired": self.stats.total_acquired,
            "total_released": self.stats.total_released,
            "total_failed": self.stats.total_failed,
            "total_health_checks": self.stats.total_health_checks,
            "total_health_check_failures": self.stats.total_health_check_failures,
            "active_connections": len(self._active_connections),
            "idle_connections": len(self._idle_connections),
            "total_connections": len(self._all_connections),
            "last_health_check": (
                self.stats.last_health_check.isoformat() if self.stats.last_health_check else None
            ),
            "average_wait_time": self.stats.average_wait_time,
            "utilization": (
                len(self._active_connections) / self.config.max_size
                if self.config.max_size > 0
                else 0
            ),
        }

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.stop()


# 导出
__all__ = ["ConnectionConfig", "ConnectionStats", "DynamicConnectionPool", "PooledConnection"]
