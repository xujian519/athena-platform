#!/usr/bin/env python3
"""
异步批处理器单元测试
Unit Tests for Async Batch Processor

作者: Athena AI系统
创建时间: 2026-01-25
版本: 1.0.0
"""

import asyncio
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.communication.engine.async_batch_processor import AsyncBatchProcessor
from core.communication.optimized_communication_module import Message, MessagePriority


@pytest.mark.asyncio
@pytest.mark.unit
class TestAsyncBatchProcessor:
    """异步批处理器测试"""

    @pytest.fixture
    async def batch_processor(self):
        """创建批处理器实例"""
        processor = AsyncBatchProcessor(
            batch_size=10,
            batch_timeout=1.0,
            max_batch_size=100
        )
        await processor.start()
        yield processor
        await processor.stop()

    @pytest.fixture
    def sample_message(self):
        """创建示例消息"""
        return Message(
            message_id="test-msg-1",
            sender_id="test_sender",
            receiver_id="test_receiver",
            message_type="text",
            payload="Test message content",
            priority=MessagePriority.NORMAL
        )

    async def test_add_message(self, batch_processor, sample_message):
        """测试添加消息"""
        result = await batch_processor.add_message(sample_message)
        assert result is True
        assert batch_processor.get_queue_size("test_receiver") == 1

    async def test_batch_processing(self, batch_processor):
        """测试批处理"""
        # 添加多条消息
        messages = []
        for i in range(15):
            message = Message(
                message_id=f"test-msg-{i}",
                sender_id="test_sender",
                receiver_id="test_receiver",
                message_type="text",
                payload=f"Message {i}",
                priority=MessagePriority.NORMAL
            )
            messages.append(message)
            await batch_processor.add_message(message)

        # 等待批处理
        await asyncio.sleep(2)

        # 检查统计
        stats = batch_processor.get_stats()
        assert stats['total_messages_batched'] > 0
        assert stats['total_batches_processed'] > 0

    async def test_flush(self, batch_processor):
        """测试刷新队列"""
        # 添加消息
        for i in range(5):
            message = Message(
                message_id=f"test-msg-{i}",
                sender_id="test_sender",
                receiver_id="test_receiver",
                message_type="text",
                payload=f"Message {i}",
                priority=MessagePriority.NORMAL
            )
            await batch_processor.add_message(message)

        # 刷新队列
        result = await batch_processor.flush("test_receiver")

        # 验证结果
        assert result is not None
        assert result.batch_size == 5
        assert batch_processor.get_queue_size("test_receiver") == 0

    async def test_multiple_receivers(self, batch_processor):
        """测试多接收者批处理"""
        receivers = ["receiver_1", "receiver_2", "receiver_3"]

        # 为每个接收者添加消息
        for receiver_id in receivers:
            for i in range(5):
                message = Message(
                    message_id=f"msg-{receiver_id}-{i}",
                    sender_id="test_sender",
                    receiver_id=receiver_id,
                    message_type="text",
                    payload=f"Message {i} for {receiver_id}",
                    priority=MessagePriority.NORMAL
                )
                await batch_processor.add_message(message)

        # 等待处理
        await asyncio.sleep(2)

        # 刷新所有队列
        results = await batch_processor.flush_all()

        # 验证结果
        assert len(results) == 3
        for receiver_id, batch in results.items():
            if batch:
                assert batch.batch_size == 5

    async def test_stats(self, batch_processor):
        """测试统计信息"""
        # 添加消息
        for i in range(20):
            message = Message(
                message_id=f"test-msg-{i}",
                sender_id="test_sender",
                receiver_id="test_receiver",
                message_type="text",
                payload=f"Message {i}",
                priority=MessagePriority.NORMAL
            )
            await batch_processor.add_message(message)

        # 等待批处理
        await asyncio.sleep(2)

        # 获取统计
        stats = batch_processor.get_stats()

        # 验证统计信息
        assert 'total_batches_processed' in stats
        assert 'total_messages_batched' in stats
        assert 'average_batch_size' in stats
        assert 'queue_sizes' in stats

        # 验证数值合理性
        assert stats['total_messages_batched'] <= 20
        assert stats['average_batch_size'] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
