#!/usr/bin/env python3
"""
通信引擎核心模块单元测试
Unit Tests for Communication Engine

作者: Athena AI系统
创建时间: 2026-01-25
版本: 1.0.0
"""

import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


from core.communication.communication_engine import (
    Channel,
    ChannelType,
    CommunicationEngine,
    Message,
    MessageStatus,
    MessageType,
    ProtocolType,
)


@pytest.mark.unit
class TestMessage:
    """消息类测试"""

    def test_create_message_minimal(self):
        """测试创建最小消息"""
        message = Message(
            id="msg_001",
            sender_id="agent_001",
            receiver_id="agent_002",
            channel_id="channel_001",
            message_type=MessageType.TEXT,
            content="Hello"
        )

        assert message.id == "msg_001"
        assert message.sender_id == "agent_001"
        assert message.receiver_id == "agent_002"
        assert message.content == "Hello"
        assert message.status == MessageStatus.PENDING
        assert message.priority == 0

    def test_create_message_full(self):
        """测试创建完整消息"""
        metadata = {"source": "test"}
        message = Message(
            id="msg_002",
            sender_id="agent_001",
            receiver_id="agent_002",
            channel_id="channel_001",
            message_type=MessageType.TEXT,
            content="Hello",
            status=MessageStatus.SENT,
            metadata=metadata,
            protocol=ProtocolType.JSON,
            priority=5,
            ttl=3600,
            retry_count=1,
            max_retries=3
        )

        assert message.status == MessageStatus.SENT
        assert message.metadata == metadata
        assert message.priority == 5
        assert message.ttl == 3600

    def test_message_timestamp_default(self):
        """测试消息时间戳默认值"""
        before = datetime.now()
        message = Message(
            id="msg_001",
            sender_id="agent_001",
            receiver_id="agent_002",
            channel_id="channel_001",
            message_type=MessageType.TEXT,
            content="Hello"
        )
        after = datetime.now()

        assert before <= message.timestamp <= after

    def test_message_to_dict(self):
        """测试消息转换为字典"""
        message = Message(
            id="msg_001",
            sender_id="agent_001",
            receiver_id="agent_002",
            channel_id="channel_001",
            message_type=MessageType.TEXT,
            content="Hello"
        )

        from dataclasses import asdict
        msg_dict = asdict(message)

        assert msg_dict["id"] == "msg_001"
        assert msg_dict["sender_id"] == "agent_001"


@pytest.mark.unit
class TestChannel:
    """通道类测试"""

    def test_create_channel_minimal(self):
        """测试创建最小通道"""
        channel = Channel(
            id="channel_001",
            name="Test Channel",
            channel_type=ChannelType.DIRECT
        )

        assert channel.id == "channel_001"
        assert channel.name == "Test Channel"
        assert channel.channel_type == ChannelType.DIRECT
        assert channel.is_active is True
        assert len(channel.participants) == 0

    def test_create_channel_full(self):
        """测试创建完整通道"""
        participants = ["agent_001", "agent_002"]
        channel = Channel(
            id="channel_002",
            name="Group Channel",
            channel_type=ChannelType.GROUP,
            participants=participants,
            is_active=True
        )

        assert channel.channel_type == ChannelType.GROUP
        assert len(channel.participants) == 2
        assert "agent_001" in channel.participants

    def test_channel_timestamps(self):
        """测试通道时间戳"""
        before = datetime.now()
        channel = Channel(
            id="channel_001",
            name="Test",
            channel_type=ChannelType.DIRECT
        )
        after = datetime.now()

        assert before <= channel.created_at <= after
        assert before <= channel.last_activity <= after


@pytest.mark.asyncio
@pytest.mark.unit
class TestCommunicationEngine:
    """通信引擎测试"""

    @pytest.fixture
    async def engine(self):
        """创建通信引擎实例"""
        eng = CommunicationEngine()
        await eng.initialize()
        yield eng
        await eng.shutdown()

    @pytest.mark.asyncio
    async def test_engine_initialization(self, engine):
        """测试引擎初始化"""
        assert engine is not None
        assert engine.is_initialized()

    @pytest.mark.asyncio
    async def test_create_channel(self, engine):
        """测试创建通道"""
        channel = await engine.create_channel(
            channel_id="test_channel",
            name="Test Channel",
            channel_type=ChannelType.DIRECT
        )

        assert channel is not None
        assert channel.id == "test_channel"
        assert channel.name == "Test Channel"

    @pytest.mark.asyncio
    async def test_create_duplicate_channel(self, engine):
        """测试创建重复通道"""
        await engine.create_channel(
            channel_id="test_channel",
            name="Test Channel",
            channel_type=ChannelType.DIRECT
        )

        # 尝试创建重复通道
        with pytest.raises(Exception):  # 可能抛出不同的异常
            await engine.create_channel(
                channel_id="test_channel",
                name="Another Channel",
                channel_type=ChannelType.DIRECT
            )

    @pytest.mark.asyncio
    async def test_send_message(self, engine):
        """测试发送消息"""
        # 创建通道
        await engine.create_channel(
            channel_id="test_channel",
            name="Test",
            channel_type=ChannelType.DIRECT
        )

        # 发送消息
        message = await engine.send_message(
            sender_id="agent_001",
            receiver_id="agent_002",
            channel_id="test_channel",
            message_type=MessageType.TEXT,
            content="Hello"
        )

        assert message is not None
        assert message.sender_id == "agent_001"
        assert message.receiver_id == "agent_002"
        assert message.content == "Hello"

    @pytest.mark.asyncio
    async def test_broadcast_message(self, engine):
        """测试广播消息"""
        # 创建群组通道
        await engine.create_channel(
            channel_id="group_channel",
            name="Group",
            channel_type=ChannelType.GROUP
        )

        # 添加参与者
        await engine.add_participant("group_channel", "agent_001")
        await engine.add_participant("group_channel", "agent_002")

        # 广播消息
        message = await engine.broadcast_message(
            sender_id="agent_001",
            channel_id="group_channel",
            message_type=MessageType.TEXT,
            content="Broadcast"
        )

        assert message is not None
        assert message.message_type == MessageType.TEXT

    @pytest.mark.asyncio
    async def test_get_channel(self, engine):
        """测试获取通道"""
        # 创建通道
        await engine.create_channel(
            channel_id="test_channel",
            name="Test",
            channel_type=ChannelType.DIRECT
        )

        # 获取通道
        channel = await engine.get_channel("test_channel")
        assert channel is not None
        assert channel.id == "test_channel"

    @pytest.mark.asyncio
    async def test_get_nonexistent_channel(self, engine):
        """测试获取不存在的通道"""
        channel = await engine.get_channel("nonexistent")
        assert channel is None

    @pytest.mark.asyncio
    async def test_add_participant(self, engine):
        """测试添加参与者"""
        await engine.create_channel(
            channel_id="test_channel",
            name="Test",
            channel_type=ChannelType.GROUP
        )

        await engine.add_participant("test_channel", "agent_001")

        channel = await engine.get_channel("test_channel")
        assert "agent_001" in channel.participants

    @pytest.mark.asyncio
    async def test_remove_participant(self, engine):
        """测试移除参与者"""
        await engine.create_channel(
            channel_id="test_channel",
            name="Test",
            channel_type=ChannelType.GROUP
        )

        await engine.add_participant("test_channel", "agent_001")
        await engine.remove_participant("test_channel", "agent_001")

        channel = await engine.get_channel("test_channel")
        assert "agent_001" not in channel.participants

    @pytest.mark.asyncio
    async def test_message_history(self, engine):
        """测试消息历史"""
        await engine.create_channel(
            channel_id="test_channel",
            name="Test",
            channel_type=ChannelType.DIRECT
        )

        # 发送多条消息
        await engine.send_message(
            sender_id="agent_001",
            receiver_id="agent_002",
            channel_id="test_channel",
            message_type=MessageType.TEXT,
            content="Message 1"
        )
        await engine.send_message(
            sender_id="agent_002",
            receiver_id="agent_001",
            channel_id="test_channel",
            message_type=MessageType.TEXT,
            content="Message 2"
        )

        # 获取历史
        history = await engine.get_message_history("test_channel")
        assert len(history) >= 2

    @pytest.mark.asyncio
    async def test_get_statistics(self, engine):
        """测试获取统计信息"""
        stats = await engine.get_statistics()
        assert isinstance(stats, dict)
        assert "channels" in stats or "total_channels" in stats


@pytest.mark.unit
class TestEnums:
    """枚举类测试"""

    def test_message_type_values(self):
        """测试消息类型枚举值"""
        assert MessageType.TEXT.value == 'text'
        assert MessageType.IMAGE.value == 'image'
        assert MessageType.AUDIO.value == 'audio'
        assert MessageType.VIDEO.value == 'video'

    def test_channel_type_values(self):
        """测试通道类型枚举值"""
        assert ChannelType.DIRECT.value == 'direct'
        assert ChannelType.GROUP.value == 'group'
        assert ChannelType.BROADCAST.value == 'broadcast'

    def test_message_status_values(self):
        """测试消息状态枚举值"""
        assert MessageStatus.PENDING.value == 'pending'
        assert MessageStatus.SENT.value == 'sent'
        assert MessageStatus.DELIVERED.value == 'delivered'

    def test_protocol_type_values(self):
        """测试协议类型枚举值"""
        assert ProtocolType.JSON.value == 'json'
        assert ProtocolType.XML.value == 'xml'
        assert ProtocolType.PROTOBUF.value == 'protobuf'


@pytest.mark.unit
class TestMessagePriority:
    """消息优先级测试"""

    def test_priority_range(self):
        """测试优先级范围"""
        message = Message(
            id="msg_001",
            sender_id="agent_001",
            receiver_id="agent_002",
            channel_id="channel_001",
            message_type=MessageType.TEXT,
            content="Test",
            priority=0
        )
        assert message.priority == 0

        message.priority = 9
        assert message.priority == 9


@pytest.mark.unit
class TestMessageTTL:
    """消息TTL测试"""

    def test_ttl_none(self):
        """测试无TTL"""
        message = Message(
            id="msg_001",
            sender_id="agent_001",
            receiver_id="agent_002",
            channel_id="channel_001",
            message_type=MessageType.TEXT,
            content="Test",
            ttl=None
        )
        assert message.ttl is None

    def test_ttl_set(self):
        """测试设置TTL"""
        message = Message(
            id="msg_001",
            sender_id="agent_001",
            receiver_id="agent_002",
            channel_id="channel_001",
            message_type=MessageType.TEXT,
            content="Test",
            ttl=3600
        )
        assert message.ttl == 3600


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
