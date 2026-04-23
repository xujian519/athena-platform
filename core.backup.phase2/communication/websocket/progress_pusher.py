#!/usr/bin/env python3
from __future__ import annotations
"""
WebSocket 实时进度推送模块
WebSocket Real-time Progress Push Module

通过 WebSocket 实时推送任务执行进度到前端。

特性:
1. 双向通信
2. 房间隔离
3. 进度广播
4. 心跳检测
5. 自动重连

Author: Athena Team
Version: 1.0.0
Date: 2026-02-25
"""

import asyncio
import json
import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ========== 消息类型 ==========


class MessageType(Enum):
    """消息类型"""
    # 客户端 -> 服务端
    SUBSCRIBE = "subscribe"  # 订阅任务更新
    UNSUBSCRIBE = "unsubscribe"  # 取消订阅
    PING = "ping"  # 心跳
    # 服务端 -> 客户端
    PROGRESS_UPDATE = "progress_update"  # 进度更新
    STEP_COMPLETED = "step_completed"  # 步骤完成
    STEP_FAILED = "step_failed"  # 步骤失败
    TASK_COMPLETED = "task_completed"  # 任务完成
    TASK_FAILED = "task_failed"  # 任务失败
    ERROR = "error"  # 错误消息
    PONG = "pong"  # 心跳响应


# ========== 消息数据结构 ==========


@dataclass
class WebSocketMessage:
    """WebSocket 消息"""
    msg_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    msg_type: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_json(self) -> str:
        return json.dumps({
            "msg_id": self.msg_id,
            "msg_type": self.msg_type,
            "data": self.data,
            "timestamp": self.timestamp,
        })

    @classmethod
    def from_json(cls, json_str: str) -> "WebSocketMessage":
        data = json.loads(json_str)
        return cls(
            msg_id=data.get("msg_id", str(uuid.uuid4())),
            msg_type=data.get("msg_type", ""),
            data=data.get("data", {}),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
        )


@dataclass
class ProgressUpdate:
    """进度更新数据"""
    task_id: str
    step_id: str
    step_name: str
    status: str
    progress_percent: int
    current_step: int
    total_steps: int
    message: str = ""
    result: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ========== WebSocket 连接管理 ==========


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        # 活跃连接: {connection_id: websocket}
        self.active_connections: dict[str, Any] = {}

        # 任务订阅: {task_id: set[connection_id]}
        self.task_subscribers: dict[str, set[str]] = {}

        # 连接到任务: {connection_id: set[task_id]}
        self.connection_tasks: dict[str, set[str]] = {}

        # 心跳检测
        self._heartbeat_task: asyncio.Task | None = None
        self._heartbeat_interval = 30  # 心跳间隔(秒)

        logger.info("🔌 WebSocket 连接管理器初始化")

    async def connect(self, websocket: Any, connection_id: str | None = None) -> str:
        """接受新连接"""
        if connection_id is None:
            connection_id = str(uuid.uuid4())

        self.active_connections[connection_id] = websocket
        self.connection_tasks[connection_id] = set()

        logger.info(f"📱 新连接: {connection_id}")

        # 启动心跳检测
        if self._heartbeat_task is None:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        return connection_id

    async def disconnect(self, connection_id: str) -> None:
        """断开连接"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]

        # 取消所有订阅
        if connection_id in self.connection_tasks:
            for task_id in self.connection_tasks[connection_id]:
                self.task_subscribers[task_id].discard(connection_id)
            del self.connection_tasks[connection_id]

        logger.info(f"📱 连接断开: {connection_id}")

    async def subscribe(self, connection_id: str, task_id: str) -> bool:
        """订阅任务更新"""
        if connection_id not in self.active_connections:
            return False

        if task_id not in self.task_subscribers:
            self.task_subscribers[task_id] = set()

        self.task_subscribers[task_id].add(connection_id)
        self.connection_tasks[connection_id].add(task_id)

        logger.info(f"📬 {connection_id} 订阅任务: {task_id}")

        # 发送当前状态
        await self._send_current_status(connection_id, task_id)

        return True

    async def unsubscribe(self, connection_id: str, task_id: str) -> bool:
        """取消订阅任务"""
        if connection_id in self.connection_tasks:
            self.connection_tasks[connection_id].discard(task_id)

        if task_id in self.task_subscribers:
            self.task_subscribers[task_id].discard(connection_id)

        logger.info(f"📬 {connection_id} 取消订阅: {task_id}")

        return True

    async def broadcast_progress(
        self,
        task_id: str,
        update: ProgressUpdate,
    ) -> int:
        """广播进度更新到所有订阅者"""
        if task_id not in self.task_subscribers:
            return 0

        message = WebSocketMessage(
            msg_type=MessageType.PROGRESS_UPDATE.value,
            data=update.to_dict(),
        )

        count = 0
        failed_connections = set()

        for connection_id in self.task_subscribers[task_id]:
            websocket = self.active_connections.get(connection_id)

            if websocket is None:
                failed_connections.add(connection_id)
                continue

            try:
                await websocket.send_text(message.to_json())
                count += 1
            except Exception as e:
                logger.warning(f"⚠️ 发送消息失败 {connection_id}: {e}")
                failed_connections.add(connection_id)

        # 清理失败的连接
        for connection_id in failed_connections:
            await self.disconnect(connection_id)

        return count

    async def _send_current_status(
        self,
        connection_id: str,
        task_id: str,
    ) -> None:
        """发送当前任务状态"""
        # 这里可以从缓存/数据库加载当前状态
        # 简化实现：发送订阅确认
        message = WebSocketMessage(
            msg_type="subscription_confirmed",
            data={
                "task_id": task_id,
                "message": f"已订阅任务 {task_id} 的更新",
            },
        )

        websocket = self.active_connections.get(connection_id)
        if websocket:
            try:
                await websocket.send_text(message.to_json())
            except Exception as e:
                logger.warning(f"⚠️ 发送确认失败: {e}")

    async def _heartbeat_loop(self) -> None:
        """心跳检测循环"""
        while True:
            try:
                await asyncio.sleep(self._heartbeat_interval)

                # 检查所有连接
                failed_connections = set()

                for connection_id, websocket in self.active_connections.items():
                    try:
                        # 发送心跳
                        pong = WebSocketMessage(
                            msg_type=MessageType.PONG.value,
                            data={"timestamp": datetime.now().isoformat()},
                        )
                        await websocket.send_text(pong.to_json())

                    except Exception as e:
                        logger.debug(f"心跳失败 {connection_id}: {e}")
                        failed_connections.add(connection_id)

                # 清理失败的连接
                for connection_id in failed_connections:
                    await self.disconnect(connection_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"心跳循环错误: {e}")

    def get_connection_count(self) -> int:
        """获取活跃连接数"""
        return len(self.active_connections)

    def get_subscriber_count(self, task_id: str) -> int:
        """获取任务订阅者数量"""
        return len(self.task_subscribers.get(task_id, set()))


# ========== 全局连接管理器 ==========


# 全局连接管理器实例
_connection_manager: ConnectionManager | None = None


def get_connection_manager() -> ConnectionManager:
    """获取全局连接管理器"""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager


# ========== 进度推送器 ==========


class ProgressPusher:
    """进度推送器 - 集成到执行引擎"""

    def __init__(self, connection_manager: ConnectionManager | None = None):
        self.connection_manager = connection_manager or get_connection_manager()
        logger.info("📡 进度推送器初始化")

    async def push_step_start(
        self,
        task_id: str,
        step_id: str,
        step_name: str,
        total_steps: int,
    ) -> None:
        """推送步骤开始"""
        update = ProgressUpdate(
            task_id=task_id,
            step_id=step_id,
            step_name=step_name,
            status="in_progress",
            progress_percent=0,
            current_step=0,
            total_steps=total_steps,
            message=f"开始执行: {step_name}",
        )

        await self.connection_manager.broadcast_progress(task_id, update)

    async def push_step_progress(
        self,
        task_id: str,
        step_id: str,
        step_name: str,
        progress: int,
        message: str,
    ) -> None:
        """推送步骤进度"""
        update = ProgressUpdate(
            task_id=task_id,
            step_id=step_id,
            step_name=step_name,
            status="in_progress",
            progress_percent=progress,
            current_step=0,
            total_steps=0,
            message=message,
        )

        await self.connection_manager.broadcast_progress(task_id, update)

    async def push_step_completed(
        self,
        task_id: str,
        step_id: str,
        step_name: str,
        result: str,
        total_steps: int,
        completed_steps: int,
    ) -> None:
        """推送步骤完成"""
        progress = int(completed_steps / total_steps * 100) if total_steps > 0 else 0

        update = ProgressUpdate(
            task_id=task_id,
            step_id=step_id,
            step_name=step_name,
            status="completed",
            progress_percent=progress,
            current_step=completed_steps,
            total_steps=total_steps,
            message=f"完成: {step_name}",
            result=result[:500] if result else None,  # 截断长结果
        )

        await self.connection_manager.broadcast_progress(task_id, update)

    async def push_step_failed(
        self,
        task_id: str,
        step_id: str,
        step_name: str,
        error: str,
        total_steps: int,
        completed_steps: int,
    ) -> None:
        """推送步骤失败"""
        progress = int(completed_steps / total_steps * 100) if total_steps > 0 else 0

        update = ProgressUpdate(
            task_id=task_id,
            step_id=step_id,
            step_name=step_name,
            status="failed",
            progress_percent=progress,
            current_step=completed_steps,
            total_steps=total_steps,
            message=f"失败: {step_name}",
            error=error,
        )

        await self.connection_manager.broadcast_progress(task_id, update)

    async def push_task_completed(
        self,
        task_id: str,
        total_steps: int,
    ) -> None:
        """推送任务完成"""
        update = ProgressUpdate(
            task_id=task_id,
            step_id="",
            step_name="",
            status="completed",
            progress_percent=100,
            current_step=total_steps,
            total_steps=total_steps,
            message="任务全部完成",
        )

        await self.connection_manager.broadcast_progress(task_id, update)

    async def push_task_failed(
        self,
        task_id: str,
        error: str,
    ) -> None:
        """推送任务失败"""
        update = ProgressUpdate(
            task_id=task_id,
            step_id="",
            step_name="",
            status="failed",
            progress_percent=0,
            current_step=0,
            total_steps=0,
            message=f"任务失败: {error}",
            error=error,
        )

        await self.connection_manager.broadcast_progress(task_id, update)


# ========== 导出 ==========


__all__ = [
    "MessageType",
    "WebSocketMessage",
    "ProgressUpdate",
    "ConnectionManager",
    "get_connection_manager",
    "ProgressPusher",
]
