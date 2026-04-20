#!/usr/bin/env python3
"""
Gateway WebSocket 集成测试

测试 WebSocket 端点、流式转发、会话管理和认证授权。

作者: Athena平台团队
创建时间: 2026-04-20
"""
from __future__ import annotations

import asyncio
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_websocket_connection_manager():
    """测试 WebSocket 连接管理器"""
    from core.gateway.websocket_handler import (
        WebSocketConnection,
        WebSocketConnectionManager,
        get_global_connection_manager,
    )

    print("\n=== 测试 WebSocket 连接管理器 ===")

    # 创建连接管理器
    manager = WebSocketConnectionManager()

    # 模拟 WebSocket 对象
    class MockWebSocket:
        def __init__(self):
            self.messages = []
            self.closed = False

        async def send(self, message: str):
            self.messages.append(message)

        async def close(self, code: int = 1000, reason: str = ""):
            self.closed = True

    # 测试连接
    ws1 = MockWebSocket()
    ws2 = MockWebSocket()

    conn1 = await manager.connect(ws1, session_id="session1", user_id="user1")
    conn2 = await manager.connect(ws2, session_id="session1", user_id="user1")

    print(f"✅ 连接1: {conn1.connection_id}")
    print(f"✅ 连接2: {conn2.connection_id}")

    # 测试发送消息
    await manager.send_to_connection(conn1.connection_id, {"type": "test"})
    await manager.send_to_session("session1", {"type": "broadcast"})

    print(f"✅ 连接1收到消息: {len(ws1.messages)}条")
    print(f"✅ 连接2收到消息: {len(ws2.messages)}条")

    # 测试统计
    stats = manager.get_stats()
    print(f"✅ 统计信息: {stats}")

    # 清理
    await manager.disconnect(conn1.connection_id)
    await manager.disconnect(conn2.connection_id)

    print("✅ WebSocket 连接管理器测试完成")


async def test_session_manager():
    """测试会话管理器"""
    from core.gateway.session_manager import (
        SessionManager,
        get_global_session_manager,
    )

    print("\n=== 测试会话管理器 ===")

    # 创建会话管理器
    session_manager = SessionManager(session_timeout=3600.0)

    # 创建会话
    session1 = await session_manager.create_session(
        user_id="user1",
        agent_name="xiaona",
        agent_type="legal",
    )

    session2 = await session_manager.create_session(
        user_id="user2",
        agent_name="xiaonuo",
        agent_type="coordinator",
    )

    print(f"✅ 会话1: {session1.session_id}")
    print(f"✅ 会话2: {session2.session_id}")

    # 获取会话
    retrieved_session = await session_manager.get_session(session1.session_id)
    assert retrieved_session.session_id == session1.session_id
    print(f"✅ 会话获取成功: {retrieved_session.session_id}")

    # 更新会话
    updated_session = await session_manager.update_session(
        session1.session_id,
        state={"test": "data"},
    )
    assert updated_session is not None
    assert "test" in updated_session.state
    print(f"✅ 会话更新成功: {updated_session.state}")

    # 获取用户会话
    user_sessions = await session_manager.get_user_sessions("user1")
    assert len(user_sessions) == 1
    print(f"✅ 用户会话: {len(user_sessions)}个")

    # 测试统计
    stats = session_manager.get_stats()
    print(f"✅ 统计信息: {stats}")

    # 清理
    await session_manager.delete_session(session1.session_id)
    await session_manager.delete_session(session2.session_id)

    print("✅ 会话管理器测试完成")


async def test_auth_manager():
    """测试认证管理器"""
    from core.gateway.auth import (
        AuthManager,
        get_global_auth_manager,
    )

    print("\n=== 测试认证管理器 ===")

    # 创建认证管理器
    auth_manager = AuthManager(secret_key="test_secret")

    # 生成令牌
    token1 = auth_manager.generate_token(user_id="user1", metadata={"role": "admin"})
    token2 = auth_manager.generate_token(user_id="user2", metadata={"role": "user"})

    print(f"✅ 令牌1: {token1.token[:20]}...")
    print(f"✅ 令牌2: {token2.token[:20]}...")

    # 验证令牌
    verified_token1 = auth_manager.verify_token(token1.token)
    assert verified_token1 is not None
    assert verified_token1.user_id == "user1"
    print(f"✅ 令牌1验证成功: {verified_token1.user_id}")

    # 撤销令牌
    revoked = auth_manager.revoke_token(token2.token)
    assert revoked is True
    print(f"✅ 令牌2已撤销")

    # 验证已撤销的令牌
    verified_token2 = auth_manager.verify_token(token2.token)
    assert verified_token2 is None
    print(f"✅ 已撤销令牌验证失败（符合预期）")

    # 测试统计
    stats = auth_manager.get_stats()
    print(f"✅ 统计信息: {stats}")

    print("✅ 认证管理器测试完成")


async def test_permission_checker():
    """测试权限检查器"""
    from core.gateway.auth import (
        PermissionChecker,
        get_global_permission_checker,
    )

    print("\n=== 测试权限检查器 ===")

    # 创建权限检查器
    checker = PermissionChecker()

    # 测试权限检查
    admin_permission = checker.check_permission("user1", "admin", "any:action")
    assert admin_permission is True
    print(f"✅ 管理员权限: {admin_permission}")

    user_permission = checker.check_permission("user2", "user", "agent:run")
    assert user_permission is True
    print(f"✅ 用户权限: {user_permission}")

    guest_permission = checker.check_permission("user3", "guest", "session:read")
    assert guest_permission is False
    print(f"✅ 访客权限: {guest_permission}")

    # 添加角色权限
    checker.add_role_permissions("guest", ["session:read"])
    guest_permission_after = checker.check_permission("user3", "guest", "session:read")
    assert guest_permission_after is True
    print(f"✅ 更新后访客权限: {guest_permission_after}")

    print("✅ 权限检查器测试完成")


async def test_connection_limiter():
    """测试连接限制器"""
    from core.gateway.auth import (
        ConnectionLimiter,
        get_global_connection_limiter,
    )

    print("\n=== 测试连接限制器 ===")

    # 创建连接限制器
    limiter = ConnectionLimiter(
        max_connections=3,
        max_connections_per_user=2,
    )

    # 测试连接获取
    allowed1 = await limiter.acquire_connection("user1")
    allowed2 = await limiter.acquire_connection("user1")
    allowed3 = await limiter.acquire_connection("user2")

    assert allowed1 is True
    assert allowed2 is True
    assert allowed3 is True
    print(f"✅ 连接1-3已允许")

    # 测试用户连接限制
    allowed4 = await limiter.acquire_connection("user1")
    assert allowed4 is False
    print(f"✅ 用户连接限制生效")

    # 测试全局连接限制
    allowed5 = await limiter.acquire_connection("user3")
    assert allowed5 is False
    print(f"✅ 全局连接限制生效")

    # 测试连接释放
    await limiter.release_connection("user1")
    stats = limiter.get_stats()
    print(f"✅ 连接已释放: {stats['current_connections']}/{stats['max_connections']}")

    print("✅ 连接限制器测试完成")


async def test_websocket_streaming():
    """测试 WebSocket 流式转发"""
    from core.gateway.websocket_streaming import (
        AgentWebSocketStreamer,
        WebSocketStreamingHandler,
        get_global_streamer,
    )
    from core.agents.stream_events import AssistantTextDelta, StatusEvent

    print("\n=== 测试 WebSocket 流式转发 ===")

    # 创建流式转发器
    streamer = AgentWebSocketStreamer()

    # 创建模拟的连接管理器
    from core.gateway.websocket_handler import get_global_connection_manager

    connection_manager = get_global_connection_manager()

    # 模拟 WebSocket 对象
    class MockWebSocket:
        def __init__(self):
            self.messages = []

        async def send(self, message: str):
            self.messages.append(message)

    ws = MockWebSocket()
    conn = await connection_manager.connect(ws, session_id="test_session")

    # 创建流式处理器
    handler = await streamer.create_streamer(conn.connection_id, "test_session")

    # 发送测试事件
    await handler.emit(AssistantTextDelta(text="Hello, "))
    await handler.emit(AssistantTextDelta(text="world!"))
    await handler.emit(StatusEvent(message="测试完成", level="info"))

    # 等待处理
    await asyncio.sleep(0.2)

    # 验证消息
    print(f"✅ 收到消息: {len(ws.messages)}条")
    for i, msg in enumerate(ws.messages[:3]):
        print(f"   [{i+1}] {msg[:50]}...")

    # 清理
    await streamer.remove_streamer(conn.connection_id)
    await connection_manager.disconnect(conn.connection_id)

    print("✅ WebSocket 流式转发测试完成")


async def main():
    """主函数"""
    print("🧪 开始 Gateway WebSocket 集成测试...")
    print("=" * 60)

    try:
        await test_websocket_connection_manager()
        await test_session_manager()
        await test_auth_manager()
        await test_permission_checker()
        await test_connection_limiter()
        await test_websocket_streaming()

        print("\n" + "=" * 60)
        print("🎉 所有测试完成！")

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
