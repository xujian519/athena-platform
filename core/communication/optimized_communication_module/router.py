#!/usr/bin/env python3
from __future__ import annotations
"""
优化版通信模块 - 消息路由器
Optimized Communication Module - Message Router

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0
"""

import logging
import time
from collections import defaultdict
from collections.abc import Callable
from typing import Any

from .types import Message

logger = logging.getLogger(__name__)


class MessageRouter:
    """消息路由器

    负责消息的路由和订阅管理。
    """

    def __init__(self, config: dict[str, Any]):
        """初始化消息路由器

        Args:
            config: 配置字典
        """
        self.config = config
        self.routing_table: dict[str, Any] = {}
        self.subscriptions: defaultdict[str, set[str]] = defaultdict(set)
        self.message_handlers: dict[str, Callable] = {}
        self.routing_cache: dict[str, tuple[list[str], float]] = {}
        self.cache_ttl = config.get("routing_cache_ttl", 300)  # 5分钟缓存

    def register_handler(self, message_type: str, handler: Callable):
        """注册消息处理器

        Args:
            message_type: 消息类型
            handler: 处理器函数
        """
        self.message_handlers[message_type] = handler
        logger.debug(f"注册消息处理器: {message_type}")

    def subscribe(self, subscriber_id: str, message_type: str):
        """订阅消息类型

        Args:
            subscriber_id: 订阅者ID
            message_type: 消息类型
        """
        self.subscriptions[subscriber_id].add(message_type)
        logger.debug(f"订阅者 {subscriber_id} 订阅 {message_type}")

    def unsubscribe(self, subscriber_id: str, message_type: Optional[str] = None):
        """取消订阅

        Args:
            subscriber_id: 订阅者ID
            message_type: 消息类型(可选,为None则取消所有订阅)
        """
        if message_type:
            self.subscriptions[subscriber_id].discard(message_type)
        else:
            self.subscriptions[subscriber_id].clear()

    def route_message(self, message: Message) -> list[str]:
        """路由消息到接收者

        Args:
            message: 消息对象

        Returns:
            接收者ID列表
        """
        cache_key = f"{message.sender_id}:{message.message_type}"

        # 检查缓存
        if cache_key in self.routing_cache:
            cached_result, timestamp = self.routing_cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return cached_result

        # 查找订阅者
        receivers = []
        for subscriber_id, subscribed_types in self.subscriptions.items():
            if message.message_type in subscribed_types:
                receivers.append(subscriber_id)

        # 如果没有指定接收者,发送给所有订阅者
        if not message.receiver_id and receivers:
            message.receiver_id = ",".join(receivers)

        # 缓存结果
        self.routing_cache[cache_key] = (receivers, time.time())

        return receivers

    def get_routing_stats(self) -> dict[str, Any]:
        """获取路由统计

        Returns:
            统计信息字典
        """
        return {
            "total_handlers": len(self.message_handlers),
            "total_subscribers": len(self.subscriptions),
            "cache_entries": len(self.routing_cache),
            "subscription_details": {
                subscriber: list(types) for subscriber, types in self.subscriptions.items()
            },
        }


__all__ = ["MessageRouter"]
