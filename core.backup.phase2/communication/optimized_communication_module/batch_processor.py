#!/usr/bin/env python3
from __future__ import annotations
"""
优化版通信模块 - 批处理器
Optimized Communication Module - Batch Processor

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0
"""

import logging
import queue
import threading
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Any

from .types import BatchMessage, CompressionType, Message

logger = logging.getLogger(__name__)


class BatchProcessor:
    """批处理器

    负责将消息批量处理以提高效率。
    """

    def __init__(self, config: dict[str, Any]):
        """初始化批处理器

        Args:
            config: 配置字典
        """
        self.config = config
        self.batch_size = config.get("batch_size", 100)
        self.batch_timeout = config.get("batch_timeout", 1.0)
        self.max_batch_size = config.get("max_batch_size", 1000)
        self.adaptive_batching = config.get("adaptive_batching", True)

        # 批处理队列
        self.batch_queues: defaultdict[str, queue.Queue] = defaultdict(queue.Queue)
        self.batch_timers: dict[str, threading.Timer] = {}
        self.batch_locks: defaultdict[str, threading.Lock] = defaultdict(threading.Lock)

        # 统计信息
        self.stats: dict[str, Any] = {
            "total_batches_processed": 0,
            "total_messages_batched": 0,
            "average_batch_size": 0.0,
            "batch_efficiency": 0.0,
        }

        logger.info("📦 批处理器初始化完成")

    def add_message_to_batch(self, message: Message) -> str | None:
        """添加消息到批处理队列

        Args:
            message: 消息对象

        Returns:
            接收者ID
        """
        try:
            receiver_id = message.receiver_id

            with self.batch_locks[receiver_id]:
                q = self.batch_queues[receiver_id]
                q.put(message)

                # 设置批处理定时器
                if receiver_id not in self.batch_timers:
                    self._schedule_batch_processing(receiver_id)

                # 检查是否需要立即处理
                if q.qsize() >= self.batch_size:
                    self._process_batch_immediately(receiver_id)

                return receiver_id

        except Exception as e:
            logger.error(f"添加消息到批处理失败: {e}")
            return None

    def _schedule_batch_processing(self, receiver_id: str):
        """调度批处理

        Args:
            receiver_id: 接收者ID
        """

        def process_batch():
            with self.batch_locks[receiver_id]:
                self._process_batch_immediately(receiver_id)
                self.batch_timers.pop(receiver_id, None)

        timer = threading.Timer(self.batch_timeout, process_batch)
        timer.daemon = True
        timer.start()
        self.batch_timers[receiver_id] = timer

    def _process_batch_immediately(self, receiver_id: str) -> Any:
        """立即处理批次

        Args:
            receiver_id: 接收者ID
        """
        try:
            with self.batch_locks[receiver_id]:
                q = self.batch_queues[receiver_id]
                if q.empty():
                    return

                # 收集批次消息
                messages: list[Message] = []
                while not q.empty() and len(messages) < self.max_batch_size:
                    try:
                        messages.append(q.get_nowait())
                    except queue.Empty:
                        break

                if not messages:
                    return

                # 创建批量消息
                batch_id = str(uuid.uuid4())
                batch_message = BatchMessage(
                    batch_id=batch_id,
                    messages=messages,
                    batch_size=len(messages),
                    compression_type=CompressionType.GZIP,
                    metadata={
                        "receiver_id": receiver_id,
                        "created_at": datetime.now().isoformat(),
                    },
                )

                # 更新统计
                self.stats["total_batches_processed"] += 1
                self.stats["total_messages_batched"] += len(messages)

                total_batches = self.stats["total_batches_processed"]
                current_avg = self.stats["average_batch_size"]
                new_avg = (current_avg * (total_batches - 1) + len(messages)) / total_batches
                self.stats["average_batch_size"] = new_avg

                logger.debug(f"处理批次: {batch_id}, 消息数: {len(messages)}")

                # 这里应该调用实际的批处理逻辑
                # 简化实现,返回批量消息
                return batch_message

        except Exception as e:
            logger.error(f"批处理失败: {e}")
            return None

    def get_batch_stats(self) -> dict[str, Any]:
        """获取批处理统计

        Returns:
            统计信息字典
        """
        return self.stats.copy()


__all__ = ["BatchProcessor"]
