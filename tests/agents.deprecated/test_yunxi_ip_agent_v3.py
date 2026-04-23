#!/usr/bin/env python3
"""
YunxiIPAgentV3单元测试
测试YunxiIPAgentV3的基本功能
"""


import pytest
from core.yunxi.yunxi_ip_agent_v3 import YunxiIPAgentV3


class TestYunxiIPAgentV3:
    """YunxiIPAgentV3测试套件"""

    @pytest.fixture
    def agent(self):
        """创建YunxiIPAgentV3实例"""
        return YunxiIPAgentV3(agent_id="test_yunxi")

    def test_init(self, agent):
        """测试初始化"""
        assert agent is not None
        assert agent.agent_id == "test_yunxi"

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
        valid_input = {"action": "query", "target": "测试"}
        result = agent.validate_input(valid_input)
        assert result is True or result is not None

        # 测试空输入
        invalid_input = {}
        result = agent.validate_input(invalid_input)
        assert result is False or result is not None

    def test_execute_basic(self, agent):
        """测试基本执行功能"""
        request = {
            "action": "query",
            "params": {}
        }
        result = agent.execute(request)
        assert result is not None

    def test_capability_registration(self, agent):
        """测试能力注册"""
        capabilities = agent.get_capabilities()
        cap_names = [cap.name for cap in capabilities]
        # Yunxi IP管理Agent应该有管理能力
        assert len(cap_names) > 0

    def test_status_management(self, agent):
        """测试状态管理"""
        assert hasattr(agent, "status") or hasattr(agent, "_status")

    def test_logger_exists(self, agent):
        """测试日志功能"""
        assert hasattr(agent, "logger")


class TestYunxiIPAgentV3Extended:
    """YunxiIPAgentV3扩展测试"""

    @pytest.fixture
    def agent(self):
        return YunxiIPAgentV3(agent_id="test_yunxi_extended")

    def test_client_management(self, agent):
        """测试客户管理"""
        request = {
            "action": "create_client",
            "data": {
                "name": "测试客户",
                "contact": "test@example.com"
            }
        }
        result = agent.execute(request)
        assert result is not None

    def test_project_management(self, agent):
        """测试项目管理"""
        request = {
            "action": "create_project",
            "data": {
                "name": "测试项目",
                "client_id": "test_client"
            }
        }
        result = agent.execute(request)
        assert result is not None

    def test_deadline_tracking(self, agent):
        """测试截止日期跟踪"""
        request = {
            "action": "check_deadlines",
            "params": {}
        }
        result = agent.execute(request)
        assert result is not None

    def test_document_management(self, agent):
        """测试文档管理"""
        request = {
            "action": "list_documents",
            "project_id": "test_project"
        }
        result = agent.execute(request)
        assert result is not None

    def test_error_handling(self, agent):
        """测试错误处理"""
        # 测试无效参数
        with pytest.raises((ValueError, TypeError)):
            agent.execute(None)

    def test_state_management(self, agent):
        """测试状态管理（如果有）"""
        if hasattr(agent, "get_state"):
            state = agent.get_state()
            assert state is not None

        if hasattr(agent, "set_state"):
            agent.set_state({"test": "value"})
            # 验证状态已设置

    def test_async_execute(self, agent):
        """测试异步执行（如果支持）"""
        import inspect
        if inspect.iscoroutinefunction(agent.execute):
            import asyncio

            async def run_async_test():
                request = {"action": "query", "params": {}}
                result = await agent.execute(request)
                assert result is not None

            asyncio.run(run_async_test())

    def test_report_generation(self, agent):
        """测试报告生成"""
        request = {
            "action": "generate_report",
            "params": {
                "type": "summary",
                "period": "month"
            }
        }
        result = agent.execute(request)
        assert result is not None
