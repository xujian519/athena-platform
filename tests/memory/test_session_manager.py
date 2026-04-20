#!/usr/bin/env python3
"""
会话记忆系统单元测试 - SessionManager

测试SessionManager的核心功能。

作者: Athena平台团队
创建时间: 2026-04-21
"""
from __future__ import annotations

import pytest
from datetime import datetime, timedelta

from core.memory.sessions.types import (
    SessionMessage,
    SessionContext,
    SessionStatus,
    MessageRole,
    SessionMemory,
    SessionSummary,
)


def test_create_session_context():
    """测试创建会话上下文"""
    # Arrange & Act
    context = SessionContext(
        session_id="test_session",
        user_id="user123",
        agent_id="xiaona",
    )

    # Assert
    assert context.session_id == "test_session"
    assert context.user_id == "user123"
    assert context.agent_id == "xiaona"
    assert context.status == SessionStatus.ACTIVE
    assert context.message_count == 0
    assert context.total_tokens == 0


def test_session_context_update_activity():
    """测试更新会话活动时间"""
    # Arrange
    context = SessionContext(
        session_id="test_session",
        user_id="user123",
        agent_id="xiaona",
    )
    old_activity = context.last_activity

    # Act - 等待一小段时间后更新
    import time
    time.sleep(0.01)
    context.update_activity()

    # Assert
    assert context.last_activity > old_activity


def test_session_context_is_expired():
    """测试会话过期检查"""
    # Arrange
    context = SessionContext(
        session_id="test_session",
        user_id="user123",
        agent_id="xiaona",
    )
    # 设置过去的时间
    context.last_activity = datetime.now() - timedelta(seconds=3700)

    # Act
    is_expired = context.is_expired(timeout_seconds=3600)

    # Assert
    assert is_expired is True


def test_create_session_message():
    """测试创建会话消息"""
    # Arrange & Act
    message = SessionMessage(
        role=MessageRole.USER,
        content="Hello, how are you?",
        token_count=10,
    )

    # Assert
    assert message.role == MessageRole.USER
    assert message.content == "Hello, how are you?"
    assert message.token_count == 10
    assert message.message_id.startswith("msg_")


def test_session_memory_add_message():
    """测试会话记忆添加消息"""
    # Arrange
    context = SessionContext(
        session_id="test_session",
        user_id="user123",
        agent_id="xiaona",
    )
    memory = SessionMemory(context=context)

    message1 = SessionMessage(
        role=MessageRole.USER,
        content="Hello",
        token_count=5,
    )
    message2 = SessionMessage(
        role=MessageRole.ASSISTANT,
        content="Hi there!",
        token_count=5,
    )

    # Act
    memory.add_message(message1)
    memory.add_message(message2)

    # Assert
    assert len(memory.messages) == 2
    assert memory.context.message_count == 2
    assert memory.context.total_tokens == 10


def test_session_memory_get_recent_messages():
    """测试获取最近消息"""
    # Arrange
    context = SessionContext(
        session_id="test_session",
        user_id="user123",
        agent_id="xiaona",
    )
    memory = SessionMemory(context=context)

    # 添加5条消息
    for i in range(5):
        message = SessionMessage(
            role=MessageRole.USER,
            content=f"Message {i}",
            token_count=1,
        )
        memory.add_message(message)

    # Act - 获取最近3条
    recent = memory.get_recent_messages(count=3)

    # Assert
    assert len(recent) == 3
    assert recent[0].content == "Message 2"
    assert recent[1].content == "Message 3"
    assert recent[2].content == "Message 4"


def test_session_memory_get_recent_messages_by_role():
    """测试按角色获取最近消息"""
    # Arrange
    context = SessionContext(
        session_id="test_session",
        user_id="user123",
        agent_id="xiaona",
    )
    memory = SessionMemory(context=context)

    # 添加混合消息
    memory.add_message(SessionMessage(role=MessageRole.USER, content="U1", token_count=1))
    memory.add_message(SessionMessage(role=MessageRole.ASSISTANT, content="A1", token_count=1))
    memory.add_message(SessionMessage(role=MessageRole.USER, content="U2", token_count=1))
    memory.add_message(SessionMessage(role=MessageRole.ASSISTANT, content="A2", token_count=1))

    # Act - 只获取用户消息
    user_messages = memory.get_recent_messages(count=10, role=MessageRole.USER)

    # Assert
    assert len(user_messages) == 2
    assert all(m.role == MessageRole.USER for m in user_messages)


def test_session_memory_calculate_tokens():
    """测试计算总token数"""
    # Arrange
    context = SessionContext(
        session_id="test_session",
        user_id="user123",
        agent_id="xiaona",
    )
    memory = SessionMemory(context=context)

    # 添加消息
    memory.add_message(SessionMessage(role=MessageRole.USER, content="Hello", token_count=5))
    memory.add_message(SessionMessage(role=MessageRole.ASSISTANT, content="Hi", token_count=3))

    # Act
    total_tokens = memory.calculate_tokens()

    # Assert
    assert total_tokens == 8


def test_create_session_summary():
    """测试创建会话摘要"""
    # Arrange & Act
    summary = SessionSummary(
        session_id="test_session",
        title="专利分析讨论",
        summary="用户咨询了专利分析方法",
        key_points=["专利检索", "创造性分析"],
        tags=["专利", "分析"],
    )

    # Assert
    assert summary.session_id == "test_session"
    assert summary.title == "专利分析讨论"
    assert len(summary.key_points) == 2
    assert len(summary.tags) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
