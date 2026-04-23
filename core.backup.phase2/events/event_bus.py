#!/usr/bin/env python3
"""
事件总线

实现发布/订阅模式的事件总线。

作者: Athena平台团队
创建时间: 2026-04-20
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Type,
)

from .event_types import BaseEvent

logger = logging.getLogger(__name__)


@dataclass
class EventSubscription:
    """事件订阅

    表示一个订阅者对特定事件类型的订阅。
    """

    subscription_id: str
    event_type: Type[BaseEvent]
    subscriber: "EventSubscriber"
    filter_func: Callable[[BaseEvent], bool] | None = None
    created_at: float = field(default_factory=time.time)

    def matches(self, event: BaseEvent) -> bool:
        """检查事件是否匹配此订阅

        Args:
            event: 事件对象

        Returns:
            bool: 是否匹配
        """
        # 类型检查
        if not isinstance(event, self.event_type):
            return False

        # 过滤器检查
        if self.filter_func and not self.filter_func(event):
            return False

        return True


class EventSubscriber:
    """事件订阅者基类

    订阅者需要实现 on_event 方法来处理事件。
    """

    async def on_event(self, event: BaseEvent) -> None:
        """处理事件

        Args:
            event: 事件对象
        """
        raise NotImplementedError("Subclasses must implement on_event")


class CallbackSubscriber(EventSubscriber):
    """回调订阅者

    使用回调函数处理事件。
    """

    def __init__(
        self,
        callback: Callable[[BaseEvent], Any],
        event_type: Type[BaseEvent],
    ):
        """初始化回调订阅者

        Args:
            callback: 回调函数
            event_type: 事件类型
        """
        self._callback = callback
        self._event_type = event_type

    async def on_event(self, event: BaseEvent) -> None:
        """处理事件

        Args:
            event: 事件对象
        """
        if isinstance(event, self._event_type):
            result = self._callback(event)
            if asyncio.iscoroutine(result):
                await result


class QueueSubscriber(EventSubscriber):
    """队列订阅者

    将事件放入队列供后续处理。
    """

    def __init__(self, queue: asyncio.Queue, max_size: int = 1000):
        """初始化队列订阅者

        Args:
            queue: 异步队列
            max_size: 最大队列长度
        """
        self._queue = queue
        self._max_size = max_size

    async def on_event(self, event: BaseEvent) -> None:
        """处理事件

        Args:
            event: 事件对象
        """
        if self._queue.full():
            logger.warning(f"事件队列已满，丢弃事件: {event.event_id}")
            return

        await self._queue.put(event)


class EventBus:
    """事件总线

    实现发布/订阅模式的异步事件总线。
    """

    def __init__(self):
        """初始化事件总线"""
        self._subscriptions: Dict[str, EventSubscription] = {}
        self._event_history: List[BaseEvent] = []
        self._max_history = 1000  # 最多保留 1000 个历史事件
        self._lock = asyncio.Lock()

        logger.info("📡 事件总线已创建")

    async def subscribe(
        self,
        event_type: Type[BaseEvent],
        subscriber: EventSubscriber,
        filter_func: Callable[[BaseEvent], bool] | None = None,
    ) -> str:
        """订阅事件

        Args:
            event_type: 事件类型
            subscriber: 订阅者对象
            filter_func: 可选的过滤函数

        Returns:
            str: 订阅 ID
        """
        subscription_id = f"sub_{uuid.uuid4().hex[:8]}"
        subscription = EventSubscription(
            subscription_id=subscription_id,
            event_type=event_type,
            subscriber=subscriber,
            filter_func=filter_func,
        )

        async with self._lock:
            self._subscriptions[subscription_id] = subscription

        logger.info(
            f"✅ 事件订阅已创建: {subscription_id} - {event_type.__name__}"
        )
        return subscription_id

    async def unsubscribe(self, subscription_id: str) -> bool:
        """取消订阅

        Args:
            subscription_id: 订阅 ID

        Returns:
            bool: 是否成功取消
        """
        async with self._lock:
            if subscription_id in self._subscriptions:
                del self._subscriptions[subscription_id]
                logger.info(f"✅ 事件订阅已取消: {subscription_id}")
                return True
            return False

    async def publish(self, event: BaseEvent) -> None:
        """发布事件（同步）

        Args:
            event: 事件对象
        """
        # 添加到历史记录
        await self._add_to_history(event)

        # 查找匹配的订阅
        subscriptions = []
        async with self._lock:
            for subscription in self._subscriptions.values():
                if subscription.matches(event):
                    subscriptions.append(subscription)

        # 通知订阅者
        for subscription in subscriptions:
            try:
                await subscription.subscriber.on_event(event)
            except Exception as e:
                logger.error(
                    f"❌ 事件处理失败: {subscription.subscription_id} - {e}"
                )

    async def publish_async(self, event: BaseEvent) -> asyncio.Task:
        """发布事件（异步）

        Args:
            event: 事件对象

        Returns:
            asyncio.Task: 异步任务
        """
        return asyncio.create_task(self.publish(event))

    async def _add_to_history(self, event: BaseEvent) -> None:
        """添加事件到历史记录

        Args:
            event: 事件对象
        """
        async with self._lock:
            self._event_history.append(event)
            # 限制历史记录大小
            if len(self._event_history) > self._max_history:
                self._event_history = self._event_history[-self._max_history :]

    def get_history(
        self, event_type: Type[BaseEvent] | None = None, limit: int = 100
    ) -> List[BaseEvent]:
        """获取历史事件

        Args:
            event_type: 事件类型（None 表示所有类型）
            limit: 返回数量限制

        Returns:
            list[BaseEvent]: 事件列表
        """
        if event_type:
            return [
                e
                for e in self._event_history
                if isinstance(e, event_type)
             ][-limit:]
        else:
            return self._event_history[-limit:]

    async def clear_history(self) -> None:
        """清除历史记录"""
        async with self._lock:
            self._event_history.clear()
            logger.info("🗑️ 事件历史已清除")

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息

        Returns:
            dict: 统计信息
        """
        return {
            "total_subscriptions": len(self._subscriptions),
            "history_size": len(self._event_history),
            "subscriptions_by_type": self._get_subscriptions_by_type(),
        }

    def _get_subscriptions_by_type(self) -> Dict[str, int]:
        """按类型统计订阅数量"""
        type_counts = defaultdict(int)
        for subscription in self._subscriptions.values():
            type_name = subscription.event_type.__name__
            type_counts[type_name] += 1
        return dict(type_counts)


# ========================================
# 全局事件总线
# ========================================

_global_event_bus: EventBus | None = None


def get_global_event_bus() -> EventBus:
    """获取全局事件总线

    Returns:
        EventBus: 全局事件总线单例
    """
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus


__all__ = [
    "EventSubscriber",
    "CallbackSubscriber",
    "QueueSubscriber",
    "EventBus",
    "get_global_event_bus",
]
