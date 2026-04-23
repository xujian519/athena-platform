"""
Testagent测试套件
==================

测试Testagent的各项功能
"""


import pytest
from core.framework.agents.testagent import Testagent

from core.framework.agents.xiaona.base_component import (
    AgentExecutionContext,
    AgentStatus,
)


class TestTestagent:
    """Testagent测试"""

    @pytest.fixture
    def agent(self):
        """创建Agent实例"""
        return Testagent(agent_id="test_testagent")

    @pytest.fixture
    def basic_context(self):
        """创建基本执行上下文"""
        return AgentExecutionContext(
            session_id="SESSION_001",
            task_id="TASK_001",
            input_data={"input": "test"},
            config={},
            metadata={},
        )

    def test_agent_initialization(self, agent):
        """测试Agent初始化"""
        assert agent.agent_id == "test_testagent"
        assert len(agent.get_capabilities()) > 0

    def test_capabilities(self, agent):
        """测试能力注册"""
        capabilities = agent.get_capabilities()
        assert len(capabilities) >= 1
        capability_names = [c.name for c in capabilities]
        assert "testagent" in capability_names

    @pytest.mark.asyncio
    async def test_execute_success(self, agent, basic_context):
        """测试正常执行"""
        result = await agent.execute(basic_context)
        assert result.status == AgentStatus.COMPLETED
        assert result.output_data is not None

    def test_validate_input_valid(self, agent, basic_context):
        """测试有效输入验证"""
        is_valid = agent.validate_input(basic_context)
        assert is_valid is True

    def test_validate_input_invalid(self, agent):
        """测试无效输入验证"""
        context = AgentExecutionContext(
            session_id="",  # 空session_id
            task_id="TASK_001",
            input_data={},
            config={},
            metadata={},
        )
        is_valid = agent.validate_input(context)
        assert is_valid is False

    def test_get_system_prompt(self, agent):
        """测试系统提示词"""
        prompt = agent.get_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_get_info(self, agent):
        """测试get_info方法"""
        info = agent.get_info()
        assert "agent_id" in info
        assert "agent_type" in info
        assert "capabilities" in info
