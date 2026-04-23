#!/usr/bin/env python3
"""
WriterAgent单元测试
测试WriterAgent的基本功能
"""


import pytest
from core.xiaona.writer_agent import WriterAgent


class TestWriterAgent:
    """WriterAgent测试套件"""

    @pytest.fixture
    def agent(self):
        """创建WriterAgent实例"""
        return WriterAgent(agent_id="test_writer")

    def test_init(self, agent):
        """测试初始化"""
        assert agent is not None
        assert agent.agent_id == "test_writer"

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
        valid_input = {"content": "测试内容"}
        assert agent.validate_input(valid_input) is True

        # 无效输入
        invalid_input = {}
        assert agent.validate_input(invalid_input) is False

    def test_execute_basic(self, agent):
        """测试基本执行功能"""
        request = {
            "content": "测试写作内容",
            "style": "正式"
        }
        result = agent.execute(request)
        assert result is not None

    def test_execute_with_empty_content(self, agent):
        """测试空内容处理"""
        request = {"content": ""}
        with pytest.raises(ValueError):
            agent.execute(request)

    def test_capability_registration(self, agent):
        """测试能力注册"""
        capabilities = agent.get_capabilities()
        cap_names = [cap.name for cap in capabilities]
        assert "write" in cap_names or "draft" in cap_names

    def test_status_management(self, agent):
        """测试状态管理"""
        assert hasattr(agent, "status") or hasattr(agent, "_status")

    def test_logger_exists(self, agent):
        """测试日志功能"""
        assert hasattr(agent, "logger")


class TestWriterAgentExtended:
    """WriterAgent扩展测试"""

    @pytest.fixture
    def agent(self):
        return WriterAgent(agent_id="test_writer_extended")

    def test_write_with_style(self, agent):
        """测试不同写作风格"""
        styles = ["正式", "非正式", "学术"]
        for style in styles:
            request = {"content": "测试", "style": style}
            result = agent.execute(request)
            assert result is not None

    def test_write_with_format(self, agent):
        """测试不同输出格式"""
        formats = ["markdown", "html", "plain"]
        for fmt in formats:
            request = {"content": "测试", "format": fmt}
            result = agent.execute(request)
            assert result is not None

    def test_error_handling(self, agent):
        """测试错误处理"""
        # 测试无效参数
        with pytest.raises((ValueError, TypeError)):
            agent.execute(None)

    def test_async_execute(self, agent):
        """测试异步执行（如果支持）"""
        import inspect
        if inspect.iscoroutinefunction(agent.execute):
            # Agent支持异步，需要使用异步测试
            import asyncio

            async def run_async_test():
                request = {"content": "异步测试"}
                result = await agent.execute(request)
                assert result is not None

            asyncio.run(run_async_test())
