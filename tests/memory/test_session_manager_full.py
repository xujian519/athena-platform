#!/usr/bin/env python3
"""
会话记忆系统单元测试 - SessionManager完整测试

测试SessionManager的完整功能。

作者: Athena平台团队
创建时间: 2026-04-21
"""

import tempfile

import pytest

from core.framework.memory.sessions.manager import SessionManager
from core.framework.memory.sessions.storage import FileSessionStorage
from core.framework.memory.sessions.types import (
    MessageRole,
    SessionStatus,
)


def test_create_and_get_session():
    """测试创建和获取会话"""
    # Arrange
    manager = SessionManager()

    # Act
    memory = manager.create_session(
        session_id="test_session",
        user_id="user123",
        agent_id="xiaona",
    )

    # Assert
    assert memory is not None
    assert memory.context.session_id == "test_session"

    retrieved = manager.get_session("test_session")
    assert retrieved is not None
    assert retrieved.context.user_id == "user123"


def test_add_message_to_session():
    """测试添加消息到会话"""
    # Arrange
    manager = SessionManager()
    manager.create_session(
        session_id="test_session",
        user_id="user123",
        agent_id="xiaona",
    )

    # Act
    message = manager.add_message(
        session_id="test_session",
        role=MessageRole.USER,
        content="Hello, how are you?",
        token_count=10,
    )

    # Assert
    assert message is not None
    assert message.content == "Hello, how are you?"

    session = manager.get_session("test_session")
    assert len(session.messages) == 1
    assert session.context.total_tokens == 10


def test_close_session():
    """测试关闭会话"""
    # Arrange
    manager = SessionManager()
    manager.create_session(
        session_id="test_session",
        user_id="user123",
        agent_id="xiaona",
    )

    # Act
    result = manager.close_session("test_session")

    # Assert
    assert result is True
    session = manager.get_session("test_session")
    assert session.context.status == SessionStatus.CLOSED


def test_delete_session():
    """测试删除会话"""
    # Arrange
    manager = SessionManager()
    manager.create_session(
        session_id="test_session",
        user_id="user123",
        agent_id="xiaona",
    )

    # Act
    result = manager.delete_session("test_session")

    # Assert
    assert result is True
    session = manager.get_session("test_session")
    assert session is None


def test_get_session_messages():
    """测试获取会话消息"""
    # Arrange
    manager = SessionManager()
    manager.create_session(
        session_id="test_session",
        user_id="user123",
        agent_id="xiaona",
    )

    manager.add_message("test_session", MessageRole.USER, "Hello", 5)
    manager.add_message("test_session", MessageRole.ASSISTANT, "Hi", 3)
    manager.add_message("test_session", MessageRole.USER, "How are you?", 7)

    # Act
    messages = manager.get_session_messages("test_session")

    # Assert
    assert len(messages) == 3
    assert messages[0].content == "Hello"
    assert messages[1].content == "Hi"
    assert messages[2].content == "How are you?"


def test_get_session_messages_with_limit():
    """测试限制消息数量"""
    # Arrange
    manager = SessionManager()
    manager.create_session(
        session_id="test_session",
        user_id="user123",
        agent_id="xiaona",
    )

    for i in range(10):
        manager.add_message("test_session", MessageRole.USER, f"Message {i}", 1)

    # Act - 只获取最近5条
    messages = manager.get_session_messages("test_session", count=5)

    # Assert
    assert len(messages) == 5


def test_get_session_messages_by_role():
    """测试按角色获取消息"""
    # Arrange
    manager = SessionManager()
    manager.create_session(
        session_id="test_session",
        user_id="user123",
        agent_id="xiaona",
    )

    manager.add_message("test_session", MessageRole.USER, "U1", 1)
    manager.add_message("test_session", MessageRole.ASSISTANT, "A1", 1)
    manager.add_message("test_session", MessageRole.USER, "U2", 1)
    manager.add_message("test_session", MessageRole.ASSISTANT, "A2", 1)

    # Act - 只获取用户消息
    user_messages = manager.get_session_messages(
        "test_session",
        role=MessageRole.USER
    )

    # Assert
    assert len(user_messages) == 2
    assert all(m.role == MessageRole.USER for m in user_messages)


def test_get_active_sessions():
    """测试获取活跃会话"""
    # Arrange
    manager = SessionManager()

    manager.create_session("session1", "user1", "xiaona")
    manager.create_session("session2", "user1", "xiaona")
    manager.create_session("session3", "user2", "xiaona")

    # 关闭一个会话
    manager.close_session("session2")

    # Act
    active_sessions = manager.get_active_sessions()

    # Assert
    assert len(active_sessions) == 2


def test_get_active_sessions_by_user():
    """测试按用户获取活跃会话"""
    # Arrange
    manager = SessionManager()

    manager.create_session("session1", "user1", "xiaona")
    manager.create_session("session2", "user2", "xiaona")
    manager.create_session("session3", "user1", "xiaona")

    # Act
    user1_sessions = manager.get_active_sessions(user_id="user1")

    # Assert
    assert len(user1_sessions) == 2
    assert all(s.context.user_id == "user1" for s in user1_sessions)


def test_cleanup_expired_sessions():
    """测试清理过期会话"""
    # Arrange
    manager = SessionManager(session_timeout=1)  # 1秒超时

    manager.create_session("session1", "user1", "xiaona")
    manager.create_session("session2", "user2", "xiaona")

    # 让session1过期
    import time
    time.sleep(1.1)
    manager.get_session("session1").context.update_activity()

    # Act
    cleaned_count = manager.cleanup_expired_sessions()

    # Assert
    # session2应该被清理（没有活动更新）
    assert cleaned_count >= 1


def test_get_session_stats():
    """测试获取会话统计信息"""
    # Arrange
    manager = SessionManager()

    manager.create_session("session1", "user1", "xiaona")
    manager.add_message("session1", MessageRole.USER, "Hello", 10)
    manager.add_message("session1", MessageRole.ASSISTANT, "Hi", 5)

    manager.create_session("session2", "user2", "xiaona")
    manager.add_message("session2", MessageRole.USER, "Hello", 8)

    # Act
    stats = manager.get_session_stats()

    # Assert
    assert stats["total_sessions"] == 2
    assert stats["active_sessions"] == 2
    assert stats["total_messages"] == 3
    assert stats["total_tokens"] == 23


def test_generate_session_summary():
    """测试生成会话摘要"""
    # Arrange
    manager = SessionManager()
    manager.create_session(
        session_id="test_session",
        user_id="user123",
        agent_id="xiaona",
    )

    # 添加一些消息
    manager.add_message("test_session", MessageRole.USER, "Hello", 5)
    manager.add_message("test_session", MessageRole.ASSISTANT, "Hi", 3)

    # Act
    summary = manager.generate_session_summary(
        session_id="test_session",
        title="测试会话",
        summary="这是一个测试会话",
        key_points=["要点1", "要点2"],
        tags=["测试"],
    )

    # Assert
    assert summary is not None
    assert summary.title == "测试会话"
    assert summary.summary == "这是一个测试会话"
    assert len(summary.key_points) == 2
    assert summary.message_count == 2


def test_file_storage_integration():
    """测试文件存储集成"""
    # Arrange
    with tempfile.TemporaryDirectory() as temp_dir:
        storage = FileSessionStorage(storage_dir=temp_dir)
        manager = SessionManager(storage=storage)

        # 创建会话
        manager.create_session(
            session_id="test_session",
            user_id="user123",
            agent_id="xiaona",
        )
        manager.add_message("test_session", MessageRole.USER, "Hello", 5)

        # 关闭会话（触发保存）
        manager.close_session("test_session")

        # Act - 创建新的管理器，从存储加载
        SessionManager(storage=storage)
        loaded = storage.load("test_session")

        # Assert
        assert loaded is not None
        assert loaded.context.session_id == "test_session"
        assert len(loaded.messages) == 1
        assert loaded.messages[0].content == "Hello"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

