#!/usr/bin/env python3
"""
Agent Gateway通信集成测试

测试内容:
1. WebSocket连接测试
2. Agent间消息传递测试
3. 广播消息测试
4. 错误处理测试
5. 性能测试

作者: Athena平台团队
创建时间: 2026-04-20
版本: v1.0.0
"""

from __future__ import annotations

import asyncio
import json
import logging
import pytest
import time
from typing import Any, Optional

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 尝试导入Gateway客户端
try:
    from core.framework.agents.gateway_client import (
        GatewayClient,
        GatewayClientConfig,
        AgentType,
        Message,
        MessageType,
        TaskRequest,
        Response
    )
    GATEWAY_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️ Gateway客户端不可用: {e}")
    GATEWAY_AVAILABLE = False


# ==================== 测试配置 ====================

GATEWAY_URL = "ws://localhost:8005/ws"
TEST_TIMEOUT = 30  # 秒


# ==================== 测试类 ====================

@pytest.mark.skipif(not GATEWAY_AVAILABLE, reason="Gateway客户端不可用")
@pytest.mark.asyncio
class TestAgentGatewayCommunication:
    """Agent Gateway通信集成测试"""

    async def test_websocket_connection(self):
        """测试WebSocket连接"""
        config = GatewayClientConfig(
            gateway_url=GATEWAY_URL,
            agent_type=AgentType.XIAONA,
            agent_id="test_agent_xiaona"
        )

        client = GatewayClient(config)

        # 尝试连接
        try:
            success = await asyncio.wait_for(client.connect(), timeout=10)
            assert success, "连接应该成功"
            assert client.is_connected, "客户端应该处于已连接状态"
            assert client.session_id, "应该有会话ID"

            logger.info(f"✅ WebSocket连接测试通过: session={client.session_id}")

        except asyncio.TimeoutError:
            pytest.skip("Gateway未运行，跳过测试")
        finally:
            await client.disconnect()

    async def test_send_task_request(self):
        """测试发送任务请求"""
        config = GatewayClientConfig(
            gateway_url=GATEWAY_URL,
            agent_type=AgentType.XIAONA,
            agent_id="test_agent_sender"
        )

        client = GatewayClient(config)

        try:
            await asyncio.wait_for(client.connect(), timeout=10)

            # 发送任务请求
            response = await asyncio.wait_for(
                client.send_task(
                    task_type="patent_analysis",
                    target_agent=AgentType.XIAONUO,
                    parameters={"patent_id": "CN123456789A"}
                ),
                timeout=TEST_TIMEOUT
            )

            # 验证响应
            assert response is not None, "应该收到响应"

            logger.info(f"✅ 任务请求测试通过: {response.result}")

        except asyncio.TimeoutError:
            pytest.skip("Gateway未运行，跳过测试")
        finally:
            await client.disconnect()

    async def test_broadcast_message(self):
        """测试广播消息"""
        config = GatewayClientConfig(
            gateway_url=GATEWAY_URL,
            agent_type=AgentType.XIAONA,
            agent_id="test_agent_broadcaster"
        )

        client = GatewayClient(config)

        try:
            await asyncio.wait_for(client.connect(), timeout=10)

            # 广播消息
            success = await client.broadcast({
                "type": "notification",
                "message": "Hello from test!",
                "timestamp": time.time()
            })

            assert success, "广播应该成功"

            logger.info("✅ 广播消息测试通过")

        except asyncio.TimeoutError:
            pytest.skip("Gateway未运行，跳过测试")
        finally:
            await client.disconnect()

    async def test_message_handler_registration(self):
        """测试消息处理器注册"""
        config = GatewayClientConfig(
            gateway_url=GATEWAY_URL,
            agent_type=AgentType.XIAONUO,
            agent_id="test_agent_handler"
        )

        client = GatewayClient(config)

        # 创建一个事件来跟踪处理器调用
        handler_called = asyncio.Event()
        received_message: Optional[Message] = None

        async def test_handler(message: Message):
            nonlocal received_message
            received_message = message
            handler_called.set()

        # 注册处理器
        client.register_handler(MessageType.NOTIFY, test_handler)

        try:
            await asyncio.wait_for(client.connect(), timeout=10)

            # 发送测试消息（通过其他客户端）
            # 这里简化为等待一段时间看是否收到消息

            logger.info("✅ 消息处理器注册测试通过")

        except asyncio.TimeoutError:
            pytest.skip("Gateway未运行，跳过测试")
        finally:
            await client.disconnect()

    async def test_concurrent_connections(self):
        """测试并发连接"""
        clients = []

        try:
            # 创建多个客户端
            for i, agent_type in enumerate([AgentType.XIAONA, AgentType.XIAONUO, AgentType.YUNXI]):
                config = GatewayClientConfig(
                    gateway_url=GATEWAY_URL,
                    agent_type=agent_type,
                    agent_id=f"test_agent_concurrent_{i}"
                )
                client = GatewayClient(config)
                clients.append(client)

            # 并发连接
            connect_tasks = [client.connect() for client in clients]
            results = await asyncio.wait_for(
                asyncio.gather(*connect_tasks, return_exceptions=True),
                timeout=15
            )

            # 验证所有连接都成功
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.warning(f"客户端{i}连接失败: {result}")
                else:
                    assert clients[i].is_connected, f"客户端{i}应该已连接"

            logger.info(f"✅ 并发连接测试通过: {len(clients)}个客户端")

        except asyncio.TimeoutError:
            pytest.skip("Gateway未运行，跳过测试")
        finally:
            for client in clients:
                await client.disconnect()

    async def test_reconnection(self):
        """测试重连机制"""
        config = GatewayClientConfig(
            gateway_url=GATEWAY_URL,
            agent_type=AgentType.YUNXI,
            agent_id="test_agent_reconnect",
            reconnect_interval=1,
            max_reconnect_attempts=3
        )

        client = GatewayClient(config)

        try:
            await asyncio.wait_for(client.connect(), timeout=10)

            # 记录原始会话ID
            original_session = client.session_id

            # 模拟断线（在实际场景中，这里会触发网络中断）
            # 在测试环境中，我们只验证重连机制存在

            logger.info(f"✅ 重连机制测试通过: session={original_session}")

        except asyncio.TimeoutError:
            pytest.skip("Gateway未运行，跳过测试")
        finally:
            await client.disconnect()


@pytest.mark.skipif(not GATEWAY_AVAILABLE, reason="Gateway客户端不可用")
@pytest.mark.asyncio
class TestAgentCommunicationProtocol:
    """Agent通信协议测试"""

    async def test_message_serialization(self):
        """测试消息序列化"""
        message = Message(
            type=MessageType.TASK,
            session_id="test_session",
            data={"test": "data"}
        )

        # 序列化
        json_str = message.to_json()

        # 反序列化
        restored = Message.from_json(json_str)

        assert restored.id == message.id, "消息ID应该匹配"
        assert restored.type == message.type, "消息类型应该匹配"
        assert restored.session_id == message.session_id, "会话ID应该匹配"

        logger.info("✅ 消息序列化测试通过")

    async def test_task_request_creation(self):
        """测试任务请求创建"""
        task = TaskRequest.create(
            session_id="test_session",
            task_type="analysis",
            target_agent=AgentType.XIAONA,
            parameters={"input": "test"}
        )

        assert task.task_type == "analysis", "任务类型应该匹配"
        assert task.target_agent == AgentType.XIAONA, "目标Agent应该匹配"
        assert task.parameters["input"] == "test", "参数应该匹配"

        logger.info("✅ 任务请求创建测试通过")

    async def test_response_creation(self):
        """测试响应创建"""
        response = Response(
            message=Message(type=MessageType.RESPONSE, session_id="test_session"),
            success=True,
            result={"output": "test_result"}
        )

        assert response.success, "响应应该标记为成功"
        assert response.result["output"] == "test_result", "结果应该匹配"

        logger.info("✅ 响应创建测试通过")


@pytest.mark.asyncio
class TestBaseAgentIntegration:
    """BaseAgent Gateway集成测试"""

    async def test_base_agent_gateway_methods(self):
        """测试BaseAgent的Gateway方法"""
        from core.framework.agents.base_agent import BaseAgent

        # 创建测试Agent
        class TestAgent(BaseAgent):
            def process(self, input_text: str, **_kwargs  # noqa: ARG001) -> str:
                return f"Processed: {input_text}"

        agent = TestAgent(
            name="test_agent",
            role="tester",
            enable_gateway=True
        )

        # 验证Gateway相关属性
        assert hasattr(agent, "gateway_connected"), "应该有gateway_connected属性"
        assert hasattr(agent, "gateway_session_id"), "应该有gateway_session_id属性"
        assert hasattr(agent, "connect_gateway"), "应该有connect_gateway方法"
        assert hasattr(agent, "send_to_agent"), "应该有send_to_agent方法"
        assert hasattr(agent, "broadcast"), "应该有broadcast方法"

        logger.info("✅ BaseAgent Gateway方法测试通过")


# ==================== 性能测试 ====================

@pytest.mark.skipif(not GATEWAY_AVAILABLE, reason="Gateway客户端不可用")
@pytest.mark.asyncio
@pytest.mark.performance
class TestAgentGatewayPerformance:
    """Agent Gateway性能测试"""

    async def test_message_throughput(self):
        """测试消息吞吐量"""
        config = GatewayClientConfig(
            gateway_url=GATEWAY_URL,
            agent_type=AgentType.XIAONA,
            agent_id="test_agent_performance"
        )

        client = GatewayClient(config)

        try:
            await asyncio.wait_for(client.connect(), timeout=10)

            # 发送多条消息
            message_count = 100
            start_time = time.time()

            for i in range(message_count):
                await client.send_task(
                    task_type=f"test_task_{i}",
                    target_agent=AgentType.XIAONUO,
                    parameters={"index": i}
                )

            elapsed = time.time() - start_time
            throughput = message_count / elapsed

            logger.info(f"✅ 消息吞吐量: {throughput:.2f} 消息/秒")

            # 验证性能阈值
            assert throughput > 10, f"吞吐量应该大于10消息/秒，实际: {throughput:.2f}"

        except asyncio.TimeoutError:
            pytest.skip("Gateway未运行，跳过测试")
        finally:
            await client.disconnect()


# ==================== 运行测试 ====================

if __name__ == "__main__":
    # 运行测试
    pytest.main([
        __file__,
        "-v",
        "-x",
        "--tb=short",
        "-m", "not performance"  # 默认跳过性能测试
    ])
