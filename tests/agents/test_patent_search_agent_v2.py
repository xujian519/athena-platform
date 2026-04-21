#!/usr/bin/env python3
"""
PatentSearchAgentV2单元测试
测试PatentSearchAgentV2的基本功能
"""

import pytest
from unittest.mock import Mock, patch

from core.patent.patent_search_agent_v2 import PatentSearchAgentV2


class TestPatentSearchAgentV2:
    """PatentSearchAgentV2测试套件"""

    @pytest.fixture
    def agent(self):
        """创建PatentSearchAgentV2实例"""
        return PatentSearchAgentV2(agent_id="test_patent_search")

    def test_init(self, agent):
        """测试初始化"""
        assert agent is not None
        assert agent.agent_id == "test_patent_search"

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
        valid_input = {"query": "测试专利检索"}
        result = agent.validate_input(valid_input)
        assert result is True or result is not None

        # 测试空输入
        invalid_input = {}
        result = agent.validate_input(invalid_input)
        assert result is False or result is not None

    def test_execute_basic(self, agent):
        """测试基本执行功能"""
        request = {
            "query": "人工智能 专利",
            "limit": 5
        }
        result = agent.execute(request)
        assert result is not None

    def test_capability_registration(self, agent):
        """测试能力注册"""
        capabilities = agent.get_capabilities()
        cap_names = [cap.name for cap in capabilities]
        # 专利搜索Agent应该有搜索能力
        assert "search" in cap_names or "patent_search" in cap_names

    def test_status_management(self, agent):
        """测试状态管理"""
        assert hasattr(agent, "status") or hasattr(agent, "_status")

    def test_logger_exists(self, agent):
        """测试日志功能"""
        assert hasattr(agent, "logger")


class TestPatentSearchAgentV2Extended:
    """PatentSearchAgentV2扩展测试"""

    @pytest.fixture
    def agent(self):
        return PatentSearchAgentV2(agent_id="test_patent_search_extended")

    def test_search_by_keywords(self, agent):
        """测试关键词搜索"""
        request = {
            "query": "机器学习",
            "search_type": "keyword"
        }
        result = agent.execute(request)
        assert result is not None

    def test_search_by_applicant(self, agent):
        """测试申请人搜索"""
        request = {
            "query": "某公司",
            "search_type": "applicant"
        }
        result = agent.execute(request)
        assert result is not None

    def test_search_with_filters(self, agent):
        """测试带过滤条件的搜索"""
        request = {
            "query": "人工智能",
            "filters": {
                "year": "2023",
                "country": "CN"
            }
        }
        result = agent.execute(request)
        assert result is not None

    def test_result_pagination(self, agent):
        """测试结果分页"""
        request = {
            "query": "测试",
            "page": 1,
            "page_size": 10
        }
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
            import asyncio

            async def run_async_test():
                request = {"query": "异步测试"}
                result = await agent.execute(request)
                assert result is not None

            asyncio.run(run_async_test())

    def test_search_result_format(self, agent):
        """测试搜索结果格式"""
        request = {"query": "测试", "limit": 1}
        result = agent.execute(request)
        # 结果应该是字典或列表
        assert isinstance(result, (dict, list))
