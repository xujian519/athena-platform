#!/usr/bin/env python3
from __future__ import annotations
"""
异步批处理器
Async Batch Processor

使用asyncio实现的消息批处理器,用于优化通信模块性能

作者: Athena AI系统
创建时间: 2026-01-25
版本: 1.0.0
"""

import asyncio
import logging
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from core.communication.optimized_communication_module import BatchMessage, CompressionType, Message

logger = logging.getLogger(__name__)


@dataclass
class BatchStats:
    """批处理统计信息"""

    total_batches_processed: int = 0
    total_messages_batched: int = 0
    total_batch_time: float = 0.0
    average_batch_size: float = 0.0
    batches_per_second: float = 0.0
    last_batch_time: datetime | None = None


class AsyncBatchProcessor:
    """
    异步批处理器

    使用asyncio实现的高性能消息批处理器
    支持动态批处理、超时处理和优先级队列
    """

    def __init__(
        self, batch_size: int = 100, batch_timeout: float = 1.0, max_batch_size: int = 1000
    ):
        """
        初始化异步批处理器

        Args:
            batch_size: 默认批次大小
            batch_timeout: 批处理超时时间(秒)
            max_batch_size: 最大批次大小
        """
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.max_batch_size = max_batch_size

        # 异步队列和锁
        self.queues: dict[str, asyncio.Queue] = defaultdict(asyncio.Queue)
        self.locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self.timers: dict[str, asyncio.Task] = {}

        # 统计信息
        self.stats = BatchStats()

        # 处理任务
        self._processor_tasks: list[asyncio.Task] = []
        self._running = False

        logger.info("📦 异步批处理器初始化完成")

    async def start(self) -> None:
        """启动批处理器"""
        if self._running:
            logger.warning("批处理器已在运行")
            return

        self._running = True
        logger.info("🚀 启动异步批处理器")

    async def stop(self) -> None:
        """停止批处理器"""
        if not self._running:
            return

        self._running = False

        # 取消所有定时器
        for task in self.timers.values():
            if not task.done():
                task.cancel()

        # 等待所有处理任务完成
        await asyncio.gather(*self._processor_tasks, return_exceptions=True)

        self._processor_tasks.clear()
        self.timers.clear()

        logger.info("⏹️ 异步批处理器已停止")

    async def add_message(self, message: Message) -> bool:
        """
        添加消息到批处理队列

        Args:
            message: 要批处理的消息

        Returns:
            bool: 是否成功添加
        """
        try:
            receiver_id = message.receiver_id

            async with self.locks[receiver_id]:
                queue = self.queues[receiver_id]

                # 检查队列大小
                if queue.qsize() >= self.max_batch_size:
                    logger.warning(
                        f"接收者 {receiver_id} 的队列已满 "
                        f"({queue.qsize()}/{self.max_batch_size})"
                    )
                    return False

                # 添加消息到队列
                await queue.put(message)

                # 如果是第一条消息,启动批处理任务
                if receiver_id not in self.timers:
                    self.timers[receiver_id] = asyncio.create_task(
                        self._batch_processing_loop(receiver_id)
                    )

                # 如果达到批次大小,触发立即处理
                if queue.qsize() >= self.batch_size:
                    # 通知处理循环
                    pass

                return True

        except Exception as e:
            logger.error(f"添加消息到批处理失败: {e}")
            return False

    async def _batch_processing_loop(self, receiver_id: str) -> None:
        """
        批处理循环

        Args:
            receiver_id: 接收者ID
        """
        try:
            while self._running:
                queue = self.queues.get(receiver_id)
                if not queue:
                    break

                # 等待消息或超时
                try:
                    # 等待第一批消息或超时
                    await asyncio.wait_for(queue.get(), timeout=self.batch_timeout)

                    # 收集更多消息(直到超时或达到批次大小)
                    messages = [queue.get_nowait()]
                    deadline = asyncio.get_event_loop().time() + self.batch_timeout

                    while (
                        len(messages) < self.batch_size
                        and asyncio.get_event_loop().time() < deadline
                    ):
                        try:
                            message = await asyncio.wait_for(
                                queue.get(), timeout=deadline - asyncio.get_event_loop().time()
                            )
                            messages.append(message)
                        except asyncio.TimeoutError:
                            break

                    # 处理批次
                    if messages:
                        await self._process_batch(receiver_id, messages)

                except asyncio.TimeoutError:
                    # 超时,检查队列是否有消息
                    try:
                        message = queue.get_nowait()
                        if message:
                            messages = [message]
                            # 尝试获取更多消息
                            while len(messages) < self.batch_size:
                                try:
                                    messages.append(queue.get_nowait())
                                except asyncio.QueueEmpty:
                                    break

                            if messages:
                                await self._process_batch(receiver_id, messages)
                    except asyncio.QueueEmpty:
                        continue

                # 短暂休眠避免CPU占用
                await asyncio.sleep(0.01)

        except asyncio.CancelledError:
            logger.debug(f"批处理循环已取消: {receiver_id}")
        except Exception as e:
            logger.error(f"批处理循环异常 {receiver_id}: {e}")
        finally:
            # 清理定时器
            self.timers.pop(receiver_id, None)

    async def _process_batch(
        self, receiver_id: str, messages: list[Message]
    ) -> BatchMessage | None:
        """
        处理一批消息

        Args:
            receiver_id: 接收者ID
            messages: 消息列表

        Returns:
            Optional[BatchMessage]: 批量消息对象
        """
        start_time = time.time()

        try:
            if not messages:
                return None

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
                    "message_count": len(messages),
                },
            )

            # 更新统计
            self.stats.total_batches_processed += 1
            self.stats.total_messages_batched += len(messages)

            # 计算平均批次大小
            total_batches = self.stats.total_batches_processed
            current_avg = self.stats.average_batch_size
            new_avg = (current_avg * (total_batches - 1) + len(messages)) / total_batches
            self.stats.average_batch_size = new_avg

            # 计算吞吐量
            elapsed = time.time() - start_time
            self.stats.total_batch_time += elapsed
            if self.stats.total_batch_time > 0:
                self.stats.batches_per_second = (
                    self.stats.total_batches_processed / self.stats.total_batch_time
                )

            self.stats.last_batch_time = datetime.now()

            logger.debug(
                f"✅ 处理批次 {batch_id}: "
                f"{len(messages)}条消息 -> {receiver_id} "
                f"({elapsed*1000:.2f}ms)"
            )

            # 这里应该调用实际的批处理逻辑(发送、存储等)
            # 例如:await self._send_batch(batch_message)

            return batch_message

        except Exception as e:
            logger.error(f"批处理失败 {receiver_id}: {e}")
            return None

    async def flush(self, receiver_id: str) -> BatchMessage | None:
        """
        刷新指定接收者的队列

        Args:
            receiver_id: 接收者ID

        Returns:
            Optional[BatchMessage]: 处理的批量消息
        """
        queue = self.queues.get(receiver_id)
        if not queue:
            return None

        async with self.locks[receiver_id]:
            messages = []
            while not queue.empty():
                try:
                    messages.append(queue.get_nowait())
                except asyncio.QueueEmpty:
                    break

            if messages:
                return await self._process_batch(receiver_id, messages)

        return None

    async def flush_all(self) -> Optional[dict[str, BatchMessage]]:
        """
        刷新所有队列

        Returns:
            dict[str, Optional[BatchMessage]]: 每个接收者的处理结果
        """
        results = {}

        for receiver_id in list(self.queues.keys()):
            results[receiver_id] = await self.flush(receiver_id)

        return results

    def get_queue_size(self, receiver_id: str) -> int:
        """
        获取队列大小

        Args:
            receiver_id: 接收者ID

        Returns:
            int: 队列大小
        """
        queue = self.queues.get(receiver_id)
        return queue.qsize() if queue else 0

    def get_stats(self) -> dict[str, Any]:
        """
        获取统计信息

        Returns:
            dict[str, Any]: 统计信息字典
        """
        return {
            "total_batches_processed": self.stats.total_batches_processed,
            "total_messages_batched": self.stats.total_messages_batched,
            "average_batch_size": self.stats.average_batch_size,
            "batches_per_second": self.stats.batches_per_second,
            "last_batch_time": (
                self.stats.last_batch_time.isoformat() if self.stats.last_batch_time else None
            ),
            "active_receivers": len(self.queues),
            "queue_sizes": {
                receiver_id: self.get_queue_size(receiver_id) for receiver_id in self.queues
            },
        }

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.stop()


# 导出
__all__ = ["AsyncBatchProcessor", "BatchStats"]
