#!/usr/bin/env python3
from __future__ import annotations
"""
WebSocket连接管理器
WebSocket Connection Manager

管理所有WebSocket连接的生命周期，包括：
- 连接注册和移除
- 订阅管理
- 活跃度监控
- 连接统计

作者: Athena平台团队
版本: 1.0.0
创建时间: 2026-01-28
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

from websockets.asyncio.server import ServerConnection

# 类型别名，保持向后兼容
WebSocketServerProtocol = ServerConnection

from core.communication.websocket_auth import WebSocketAuthResult

logger = logging.getLogger(__name__)


class ConnectionInfo:
    """连接信息"""

    def __init__(
        self,
        connection_id: str,
        websocket: WebSocketServerProtocol,
        auth_result: WebSocketAuthResult,
    ):
        self.connection_id = connection_id
        self.websocket = websocket
        self.auth_result = auth_result
        self.connected_at = datetime.now()
        self.last_activity = datetime.now()
        self.subscriptions: set[str] = set()
        self.metadata: dict[str, Any] = {}

    @property
    def is_expired(self) -> bool:
        """检查连接是否过期"""
        # 默认30分钟无活动视为过期
        timeout = 30 * 60
        return (datetime.now() - self.last_activity).total_seconds() > timeout


class ConnectionManager:
    """
    连接管理器

    管理所有WebSocket连接。
    """

    def __init__(self, max_connections: int = 1000):
        """
        初始化连接管理器

        Args:
            max_connections: 最大连接数
        """
        self.max_connections = max_connections
        self._connections: dict[str, ConnectionInfo] = {}
        self._channels: dict[str, set[str]] = {}  # channel -> set of connection_ids
        self._lock = asyncio.Lock()
        self._cleanup_task: asyncio.Task | None = None

    async def add_connection(
        self,
        connection_id: str,
        websocket: WebSocketServerProtocol,
        auth_result: WebSocketAuthResult,
    ) -> bool:
        """
        添加新连接

        Args:
            connection_id: 连接ID
            websocket: WebSocket连接
            auth_result: 认证结果

        Returns:
            是否添加成功
        """
        async with self._lock:
            if len(self._connections) >= self.max_connections:
                logger.warning("已达到最大连接数限制")
                return False

            if connection_id in self._connections:
                logger.warning(f"连接ID已存在: {connection_id}")
                return False

            self._connections[connection_id] = ConnectionInfo(
                connection_id, websocket, auth_result
            )

            logger.info(
                f"✅ 连接已注册: {connection_id} "
                f"(用户: {auth_result.username}, 总连接数: {len(self._connections)})"
            )

            return True

    async def remove_connection(self, connection_id: str) -> bool:
        """
        移除连接

        Args:
            connection_id: 连接ID

        Returns:
            是否移除成功
        """
        async with self._lock:
            if connection_id not in self._connections:
                return False

            # 从所有频道取消订阅
            connection_info = self._connections[connection_id]
            for channel in connection_info.subscriptions:
                self._channels[channel].discard(connection_id)
                if not self._channels[channel]:
                    del self._channels[channel]

            del self._connections[connection_id]

            logger.info(
                f"📤 连接已移除: {connection_id} "
                f"(剩余连接数: {len(self._connections)})"
            )

            return True

    async def get_connection(
        self, connection_id: str
    ) -> WebSocketServerProtocol | None:
        """
        获取WebSocket连接

        Args:
            connection_id: 连接ID

        Returns:
            WebSocket连接，如果不存在返回None
        """
        connection_info = self._connections.get(connection_id)
        if connection_info:
            return connection_info.websocket
        return None

    async def get_connection_info(
        self, connection_id: str
    ) -> ConnectionInfo | None:
        """
        获取连接信息

        Args:
            connection_id: 连接ID

        Returns:
            连接信息，如果不存在返回None
        """
        return self._connections.get(connection_id)

    async def update_last_activity(self, connection_id: str) -> None:
        """
       更新连接最后活跃时间

        Args:
            connection_id: 连接ID
        """
        connection_info = self._connections.get(connection_id)
        if connection_info:
            connection_info.last_activity = datetime.now()

    async def subscribe(self, connection_id: str, channel: str) -> bool:
        """
        订阅频道

        Args:
            connection_id: 连接ID
            channel: 频道名称

        Returns:
            是否订阅成功
        """
        async with self._lock:
            connection_info = self._connections.get(connection_id)
            if not connection_info:
                return False

            # 添加到连接的订阅列表
            connection_info.subscriptions.add(channel)

            # 添加到频道的订阅者列表
            self._channels.setdefault(channel, set()).add(connection_id)

            logger.debug(
                f"🔔 订阅成功: {connection_id} -> {channel} "
                f"(频道订阅数: {len(self._channels[channel])})"
            )

            return True

    async def unsubscribe(self, connection_id: str, channel: str) -> bool:
        """
        取消订阅频道

        Args:
            connection_id: 连接ID
            channel: 频道名称

        Returns:
            是否取消订阅成功
        """
        async with self._lock:
            connection_info = self._connections.get(connection_id)
            if not connection_info:
                return False

            # 从连接的订阅列表移除
            connection_info.subscriptions.discard(channel)

            # 从频道的订阅者列表移除
            if channel in self._channels:
                self._channels[channel].discard(connection_id)
                if not self._channels[channel]:
                    del self._channels[channel]

            logger.debug(f"🔕 取消订阅: {connection_id} -> {channel}")

            return True

    async def get_channel_subscribers(self, channel: str) -> set[str]:
        """
        获取频道的所有订阅者

        Args:
            channel: 频道名称

        Returns:
            订阅者连接ID集合
        """
        return self._channels.get(channel, set()).copy()

    async def broadcast(
        self, message: str, exclude: set[str] | None = None
    ) -> int:
        """
        广播消息到所有连接

        Args:
            message: 消息内容
            exclude: 要排除的连接ID集合

        Returns:
            发送成功的连接数
        """
        exclude = exclude or set()
        count = 0

        for connection_id, connection_info in self._connections.items():
            if connection_id in exclude:
                continue

            try:
                await connection_info.websocket.send(message)
                count += 1
            except Exception as e:
                logger.warning(
                    f"⚠️ 广播失败: {connection_id}, 错误: {e}"
                )

        return count

    async def disconnect_all(self) -> int:
        """
        断开所有连接

        Returns:
            断开的连接数
        """
        count = 0

        for connection_id in list(self._connections.keys()):
            try:
                connection_info = self._connections[connection_id]
                await connection_info.websocket.close()
                count += 1
            except Exception:
                pass

        self._connections.clear()
        self._channels.clear()

        return count

    async def get_connection_count(self) -> int:
        """
        获取当前连接数

        Returns:
            连接数
        """
        return len(self._connections)

    async def get_stats(self) -> dict[str, Any]:
        """
        获取连接统计信息

        Returns:
            统计信息字典
        """
        async with self._lock:
            # 按角色统计
            role_counts: dict[str, int] = {}
            for connection_info in self._connections.values():
                role = connection_info.auth_result.role.value if connection_info.auth_result.role else "unknown"
                role_counts[role] = role_counts.get(role, 0) + 1

            # 按频道统计
            channel_counts = {
                channel: len(subscribers)
                for channel, subscribers in self._channels.items()
            }

            return {
                "total_connections": len(self._connections),
                "max_connections": self.max_connections,
                "role_distribution": role_counts,
                "channel_counts": channel_counts,
                "total_channels": len(self._channels),
            }

    async def start_cleanup_task(self, interval: float = 60.0) -> None:
        """
        启动清理任务，定期清理过期连接

        Args:
            interval: 清理间隔（秒）
        """

        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(interval)
                    await self._cleanup_expired_connections()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"清理任务错误: {e}")

        self._cleanup_task = asyncio.create_task(cleanup_loop())
        logger.info(f"🧹 清理任务已启动 (间隔: {interval}秒)")

    async def stop_cleanup_task(self) -> None:
        """停止清理任务"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("🛑 清理任务已停止")

    async def _cleanup_expired_connections(self) -> int:
        """
        清理过期连接

        Returns:
            清理的连接数
        """
        expired = []

        for connection_id, connection_info in self._connections.items():
            if connection_info.is_expired:
                expired.append(connection_id)

        count = 0
        for connection_id in expired:
            try:
                connection_info = self._connections[connection_id]
                await connection_info.websocket.close(1000, "连接超时")
                await self.remove_connection(connection_id)
                count += 1
                logger.info(f"🧹 清理过期连接: {connection_id}")
            except Exception as e:
                logger.error(f"❌ 清理连接失败: {connection_id}, 错误: {e}")

        return count


# =============================================================================
# === 便捷函数 ===
# =============================================================================

# 全局连接管理器实例
_global_connection_manager: ConnectionManager | None = None


def get_connection_manager(
    max_connections: int = 1000,
    connection_timeout: float = 3600.0,
    cleanup_interval: float = 300.0,
) -> ConnectionManager:
    """
    获取或创建连接管理器实例

    Args:
        max_connections: 最大连接数
        connection_timeout: 连接超时时间（秒）
        cleanup_interval: 清理间隔时间（秒）

    Returns:
        ConnectionManager 实例
    """
    global _global_connection_manager

    if _global_connection_manager is None:
        _global_connection_manager = ConnectionManager(
            max_connections=max_connections,
            connection_timeout=connection_timeout,
            cleanup_interval=cleanup_interval,
        )

    return _global_connection_manager


__all__ = [
    "ConnectionManager",
    "ConnectionInfo",
    "get_connection_manager",
]
