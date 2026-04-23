"""
Python WebSocket Agent适配器测试

测试Agent与Gateway的WebSocket通信功能。
"""

import asyncio
import os
import sys

import pytest

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from core.framework.agents.websocket_adapter import (
    AgentType,
    WebSocketClient,
    XiaonaAgentAdapter,
    XiaonuoAgentAdapter,
    YunxiAgentAdapter,
    create_xiaona_agent,
)

# 测试配置
GATEWAY_URL = "ws://localhost:8005/ws"
AUTH_TOKEN = "demo_token"


class TestWebSocketClient:
    """WebSocket客户端测试"""

    @pytest.mark.asyncio
    async def test_client_connection(self):
        """测试客户端连接"""
        client = WebSocketClient(
            gateway_url=GATEWAY_URL,
            auth_token=AUTH_TOKEN
        )

        # 连接到Gateway
        assert await client.connect()
        assert client.is_connected
        assert client.session_id is not None

        # 断开连接
        await client.disconnect()
        assert not client.is_connected

    @pytest.mark.asyncio
    async def test_send_task(self):
        """测试发送任务"""
        client = WebSocketClient(
            gateway_url=GATEWAY_URL,
            auth_token=AUTH_TOKEN
        )

        await client.connect()

        # 发送任务
        task_id = await client.send_task(
            task_type="patent_analysis",
            target_agent=AgentType.XIAONA,
            parameters={
                "patent_id": "CN123456789A",
                "analysis_type": "creativity"
            }
        )

        assert task_id is not None
        assert task_id.startswith("msg_")

        await client.disconnect()

    @pytest.mark.asyncio
    async def test_send_query(self):
        """测试发送查询"""
        client = WebSocketClient(
            gateway_url=GATEWAY_URL,
            auth_token=AUTH_TOKEN
        )

        await client.connect()

        # 发送查询
        query_id = await client.send_query(
            query_type="agent_status",
            parameters={}
        )

        assert query_id is not None

        await client.disconnect()


class TestXiaonaAgent:
    """小娜Agent测试"""

    @pytest.mark.asyncio
    async def test_agent_startup(self):
        """测试Agent启动"""
        agent = XiaonaAgentAdapter(
            gateway_url=GATEWAY_URL,
            auth_token=AUTH_TOKEN
        )

        # 启动Agent
        await agent.start()
        assert agent.is_running
        assert agent.is_connected

        # 停止Agent
        await agent.stop()
        assert not agent.is_running

    @pytest.mark.asyncio
    async def test_patent_search_task(self):
        """测试专利检索任务"""
        agent = XiaonaAgentAdapter(
            gateway_url=GATEWAY_URL,
            auth_token=AUTH_TOKEN
        )

        await agent.start()

        # 模拟任务处理
        async def mock_progress(progress, status, current_step="", total_steps=0):
            print(f"进度: {progress}% - {status}")

        result = await agent.handle_task(
            task_type="patent_search",
            parameters={
                "query": "人工智能",
                "field": "G06N",
                "limit": 5
            },
            progress_callback=mock_progress
        )

        assert result is not None
        assert "results" in result
        assert len(result["results"]) <= 5

        await agent.stop()

    @pytest.mark.asyncio
    async def test_patent_analysis_task(self):
        """测试专利分析任务"""
        agent = XiaonaAgentAdapter(
            gateway_url=GATEWAY_URL,
            auth_token=AUTH_TOKEN
        )

        await agent.start()

        # 模拟任务处理
        async def mock_progress(progress, status, current_step="", total_steps=0):
            print(f"进度: {progress}% - {status}")

        result = await agent.handle_task(
            task_type="patent_analysis",
            parameters={
                "patent_id": "CN123456789A",
                "analysis_type": "comprehensive"
            },
            progress_callback=mock_progress
        )

        assert result is not None
        assert "creativity" in result

        await agent.stop()


class TestXiaonuoAgent:
    """小诺Agent测试"""

    @pytest.mark.asyncio
    async def test_agent_startup(self):
        """测试Agent启动"""
        agent = XiaonuoAgentAdapter(
            gateway_url=GATEWAY_URL,
            auth_token=AUTH_TOKEN
        )

        await agent.start()
        assert agent.is_running

        await agent.stop()
        assert not agent.is_running


class TestYunxiAgent:
    """云希Agent测试"""

    @pytest.mark.asyncio
    async def test_agent_startup(self):
        """测试Agent启动"""
        agent = YunxiAgentAdapter(
            gateway_url=GATEWAY_URL,
            auth_token=AUTH_TOKEN
        )

        await agent.start()
        assert agent.is_running

        await agent.stop()
        assert not agent.is_running


@pytest.mark.integration
class TestEndToEnd:
    """端到端集成测试"""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """测试完整工作流"""
        # 1. 启动小娜Agent
        xiaona = await create_xiaona_agent(
            gateway_url=GATEWAY_URL,
            auth_token=AUTH_TOKEN
        )

        # 2. 等待连接建立
        await asyncio.sleep(2)

        # 3. 验证Agent状态
        assert xiaona.is_running
        assert xiaona.is_connected

        # 4. 停止Agent
        await xiaona.stop()

        # 5. 验证已停止
        assert not xiaona.is_running


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])
