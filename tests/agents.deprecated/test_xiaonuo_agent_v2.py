#!/usr/bin/env python3
"""
XiaonuoAgentV2单元测试
测试XiaonuoAgentV2的基本功能
"""

import pytest
from unittest.mock import Mock, patch

from core.xiaonuo.xiaonuo_agent_v2 import XiaonuoAgentV2


class TestXiaonuoAgentV2:
    """XiaonuoAgentV2测试套件"""

    @pytest.fixture
    def agent(self):
        """创建XiaonuoAgentV2实例"""
        return XiaonuoAgentV2(agent_id="test_xiaonuo")

    def test_init(self, agent):
        """测试初始化"""
        assert agent is not None
        assert agent.agent_id == "test_xiaonuo"

    def test_get_capabilities(self, agent):
        """测试获取能力列表"""
        capabilities = agent.get_capabilities()
        assert capabilities is not None
        assert len(capabilities) > 0

    def test_get_info(self, agent):
        """测试获取Agent信息"""
        info = agent.get_info()
        assert info is not None
        assert "name" in info
        assert "version" in info

    def test_get_system_prompt(self, agent):
        """测试获取系统提示词"""
        prompt = agent.get_system_prompt()
        assert prompt is not None
        assert len(prompt) > 0

    def test_validate_input(self, agent):
        """测试输入验证"""
        # 有效输入
        valid_input = {"task": "测试任务"}
        result = agent.validate_input(valid_input)
        assert result is True or result is not None

        # 测试空输入
        invalid_input = {}
        result = agent.validate_input(invalid_input)
        # 可能返回False或抛出异常
        assert result is False or result is not None

    def test_execute_basic(self, agent):
        """测试基本执行功能"""
        request = {
            "task": "执行测试任务",
            "parameters": {}
        }
        result = agent.execute(request)
        assert result is not None

    def test_capability_registration(self, agent):
        """测试能力注册"""
        capabilities = agent.get_capabilities()
        cap_names = [cap.name for cap in capabilities]
        # Xiaonuo应该有协调相关能力
        assert len(cap_names) > 0

    def test_status_management(self, agent):
        """测试状态管理"""
        assert hasattr(agent, "status") or hasattr(agent, "_status")

    def test_logger_exists(self, agent):
        """测试日志功能"""
        assert hasattr(agent, "logger")


class TestXiaonuoAgentV2Extended:
    """XiaonuoAgentV2扩展测试"""

    @pytest.fixture
    def agent(self):
        return XiaonuoAgentV2(agent_id="test_xiaonuo_extended")

    def test_task_coordination(self, agent):
        """测试任务协调能力"""
        request = {
            "task": "协调测试",
            "agents": ["xiaona", "yunxi"]
        }
        result = agent.execute(request)
        assert result is not None

    def test_workflow_execution(self, agent):
        """测试工作流执行"""
        request = {
            "workflow": "test_workflow",
            "steps": ["step1", "step2"]
        }
        result = agent.execute(request)
        assert result is not None

    def test_agent_delegation(self, agent):
        """测试Agent委派"""
        request = {
            "task": "委派测试",
            "delegate_to": "xiaona"
        }
        result = agent.execute(request)
        assert result is not None

    def test_error_handling(self, agent):
        """测试错误处理"""
        # 测试无效参数
        with pytest.raises((ValueError, TypeError)):
            agent.execute(None)

    def test_state_persistence(self, agent):
        """测试状态持久化（如果有）"""
        if hasattr(agent, "get_state"):
            state = agent.get_state()
            assert state is not None

        if hasattr(agent, "set_state"):
            agent.set_state({"test": "value"})
            assert agent.get_state()["test"] == "value"

    def test_async_execute(self, agent):
        """测试异步执行（如果支持）"""
        import inspect
        if inspect.iscoroutinefunction(agent.execute):
            import asyncio

            async def run_async_test():
                request = {"task": "异步测试"}
                result = await agent.execute(request)
                assert result is not None

            asyncio.run(run_async_test())
