#!/usr/bin/env python3
"""
Agent适配器单元测试

测试AgentAdapter和ProxyAgentAdapter的功能。
"""

import pytest
from core.xiaonuo_agent.adapters.agent_adapter import AgentAdapter
from core.xiaonuo_agent.adapters.proxy_adapter import ProxyAgentAdapter
from core.xiaonuo_agent.adapters.registry import AgentToolRegistry, get_agent_registry

from core.framework.agents.declarative.models import AgentDefinition, AgentSource


@pytest.fixture
def sample_agent_definition():
    """创建示例Agent定义"""
    return AgentDefinition(
        name="test_agent",
        description="测试Agent",
        system_prompt="你是一个测试助手。",
        model="default",
        source=AgentSource.BUILTIN,
        filename="test_agent.md"
    )


@pytest.fixture
def agent_adapter(sample_agent_definition):
    """创建Agent适配器"""
    return AgentAdapter(sample_agent_definition)


class TestAgentAdapter:
    """测试AgentAdapter"""

    def test_init(self, agent_adapter):
        """测试初始化"""
        assert agent_adapter.agent_name == "test_agent"
        assert agent_adapter.description == "测试Agent"
        assert agent_adapter.model == "default"

    def test_prepare_input_basic(self, agent_adapter):
        """测试输入准备（基础）"""
        input_text = agent_adapter._prepare_input(
            task="测试任务",
            context={},
            kwargs={}
        )

        assert "## 任务" in input_text
        assert "测试任务" in input_text

    def test_prepare_input_with_context(self, agent_adapter):
        """测试输入准备（带上下文）"""
        input_text = agent_adapter._prepare_input(
            task="测试任务",
            context={"key": "value"},
            kwargs={}
        )

        assert "## 上下文" in input_text
        assert '"key": "value"' in input_text

    def test_prepare_input_with_kwargs(self, agent_adapter):
        """测试输入准备（带额外参数）"""
        input_text = agent_adapter._prepare_input(
            task="测试任务",
            context={},
            kwargs={"extra": "data"}
        )

        assert "## 额外信息" in input_text
        assert '"extra": "data"' in input_text

    def test_parse_response_json(self, agent_adapter):
        """测试响应解析（JSON）"""
        response = '{"result": "success", "data": {"key": "value"}}'

        result = agent_adapter._parse_response(response)

        assert result["success"] is True
        assert result["result"] == "success"
        assert result["data"]["key"] == "value"

    def test_parse_response_json_code_block(self, agent_adapter):
        """测试响应解析（JSON代码块）"""
        response = '```json\n{"result": "success"}\n```'

        result = agent_adapter._parse_response(response)

        assert result["success"] is True
        assert result["result"] == "success"

    def test_parse_response_text(self, agent_adapter):
        """测试响应解析（纯文本）"""
        response = "这是一段普通的文本响应"

        result = agent_adapter._parse_response(response)

        assert result["success"] is True
        assert result["type"] == "text"
        assert result["content"] == response

    def test_to_tool_definition(self, agent_adapter):
        """测试转换为工具定义"""
        tool_def = agent_adapter.to_tool_definition()

        assert tool_def["name"] == "test_agent"
        assert tool_def["description"] == "测试Agent"
        assert tool_def["category"] == "agent"
        assert tool_def["metadata"]["type"] == "declarative"


class TestProxyAgentAdapter:
    """测试ProxyAgentAdapter"""

    def test_init_basic(self):
        """测试初始化（基础）"""
        adapter = ProxyAgentAdapter("application_reviewer")

        assert adapter.agent_name == "application_reviewer"
        assert adapter.method_name == "review_format"  # 默认方法（METHOD_MAPPING中的第一个方法）

    def test_init_with_method(self):
        """测试初始化（指定方法）"""
        adapter = ProxyAgentAdapter("application_reviewer", "review_format")

        assert adapter.agent_name == "application_reviewer"
        assert adapter.method_name == "review_format"

    def test_init_invalid_agent(self):
        """测试初始化（无效代理）"""
        with pytest.raises(ValueError, match="未知的代理"):
            ProxyAgentAdapter("invalid_agent")

    def test_init_invalid_method(self):
        """测试初始化（无效方法）"""
        with pytest.raises(ValueError, match="没有方法"):
            ProxyAgentAdapter("application_reviewer", "invalid_method")

    def test_parse_class_path(self):
        """测试类路径解析"""
        adapter = ProxyAgentAdapter("application_reviewer")

        module_path, class_name = adapter._parse_class_path(
            "core.agents.xiaona.ApplicationReviewerProxy"
        )

        assert module_path == "core.agents.xiaona"
        assert class_name == "ApplicationReviewerProxy"

    def test_list_all_proxies(self):
        """测试列出所有代理"""
        proxies = ProxyAgentAdapter.list_all_proxies()

        assert "application_reviewer" in proxies
        assert "writing_reviewer" in proxies
        assert "novelty_analyzer" in proxies
        assert "creativity_analyzer" in proxies
        assert "infringement_analyzer" in proxies
        assert "invalidation_analyzer" in proxies

    def test_get_proxy_methods(self):
        """测试获取代理方法"""
        methods = ProxyAgentAdapter.get_proxy_methods("application_reviewer")

        assert "review_format" in methods
        assert "review_disclosure" in methods
        assert "review_claims" in methods
        assert "review_specification" in methods
        assert "review_application" in methods

    def test_get_proxy_methods_invalid(self):
        """测试获取代理方法（无效代理）"""
        methods = ProxyAgentAdapter.get_proxy_methods("invalid_agent")

        assert methods == []

    def test_to_tool_definition(self):
        """测试转换为工具定义"""
        adapter = ProxyAgentAdapter("application_reviewer", "review_format")

        tool_def = adapter.to_tool_definition()

        assert tool_def["name"] == "application_reviewer.review_format"
        assert tool_def["category"] == "agent"
        assert tool_def["metadata"]["type"] == "proxy"
        assert tool_def["metadata"]["agent_name"] == "application_reviewer"
        assert tool_def["metadata"]["method_name"] == "review_format"


class TestAgentToolRegistry:
    """测试AgentToolRegistry"""

    @pytest.mark.asyncio
    async def test_singleton(self):
        """测试单例模式"""
        registry1 = await get_agent_registry()
        registry2 = await get_agent_registry()

        assert registry1 is registry2

    @pytest.mark.asyncio
    async def test_init(self):
        """测试初始化"""
        registry = AgentToolRegistry()

        assert registry._fc_system is None
        assert registry._registered_agents == {}

    @pytest.mark.asyncio
    async def test_register_declarative_agents(self):
        """测试注册声明式Agent"""
        registry = AgentToolRegistry()

        # 模拟FunctionCallingSystem
        from unittest.mock import Mock
        registry._fc_system = Mock()
        registry._fc_system.register_tool = Mock()

        # 注册
        count = await registry._register_declarative_agents()

        # 验证
        assert count > 0
        assert len(registry._registered_agents) > 0

    @pytest.mark.asyncio
    async def test_list_agents(self):
        """测试列出Agent"""
        registry = AgentToolRegistry()

        # 模拟注册
        registry._registered_agents = {
            "agent1": {"type": "declarative"},
            "agent2": {"type": "proxy"},
        }

        # 列出所有
        all_agents = registry.list_agents()
        assert set(all_agents) == {"agent1", "agent2"}

        # 过滤类型
        declarative_agents = registry.list_agents("declarative")
        assert declarative_agents == ["agent1"]

        proxy_agents = registry.list_agents("proxy")
        assert proxy_agents == ["agent2"]

    @pytest.mark.asyncio
    async def test_get_agent_info(self):
        """测试获取Agent信息"""
        registry = AgentToolRegistry()

        # 模拟注册
        info = {"type": "declarative", "data": "test"}
        registry._registered_agents["agent1"] = info

        # 获取信息
        agent_info = registry.get_agent_info("agent1")
        assert agent_info == info

        # 获取不存在的信息
        assert registry.get_agent_info("invalid") is None

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """测试获取统计信息"""
        registry = AgentToolRegistry()

        # 模拟注册
        registry._registered_agents = {
            "agent1": {"type": "declarative"},
            "agent2": {"type": "declarative"},
            "agent3": {"type": "proxy"},
        }

        stats = registry.get_stats()

        assert stats["total"] == 3
        assert stats["declarative_agents"] == 2
        assert stats["proxy_agents"] == 1
        assert set(stats["agents"]) == {"agent1", "agent2", "agent3"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
