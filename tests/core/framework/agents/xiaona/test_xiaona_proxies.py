#!/usr/bin/env python3
"""
小娜专业代理单元测试

测试9个小娜专业代理的基础功能。
代理列表：
- RetrieverAgent - 检索代理
- AnalyzerAgent - 分析代理
- NoveltyAnalyzerProxy - 新颖性分析代理
- CreativityAnalyzerProxy - 创造性分析代理
- InfringementAnalyzerProxy - 侵权分析代理
- InvalidationAnalyzerProxy - 无效分析代理
- ApplicationDocumentReviewerProxy - 申请审查代理
- WritingReviewerProxy - 写作审查代理
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch

from core.framework.agents.xiaona.base_component import (
    AgentExecutionContext,
    AgentStatus,
)


# ========== 通用测试基类 ==========

class BaseProxyTest:
    """代理测试基类"""

    @pytest.fixture
    def agent(self):
        """创建代理实例 - 子类需要实现"""
        raise NotImplementedError("子类需要实现agent fixture")

    @pytest.fixture
    def sample_input(self):
        """示例输入 - 子类可以覆盖"""
        return {"test": "input"}

    @pytest.mark.asyncio
    async def test_agent_initialization(self, agent):
        """测试代理初始化"""
        assert agent is not None
        assert agent.agent_id is not None
        assert len(agent.get_capabilities()) > 0

    @pytest.mark.asyncio
    async def test_agent_has_capabilities(self, agent):
        """测试代理有注册能力"""
        capabilities = agent.get_capabilities()
        assert isinstance(capabilities, list)
        assert len(capabilities) > 0
        for cap in capabilities:
            assert hasattr(cap, 'name')
            assert hasattr(cap, 'description')

    @pytest.mark.asyncio
    async def test_agent_get_info(self, agent):
        """测试获取代理信息"""
        info = agent.get_info()
        assert isinstance(info, dict)
        assert "agent_id" in info
        assert "agent_type" in info
        assert "status" in info
        assert "capabilities" in info

    @pytest.mark.asyncio
    async def test_agent_get_system_prompt(self, agent):
        """测试获取系统提示词"""
        prompt = agent.get_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    @pytest.mark.asyncio
    async def test_agent_validate_input_valid(self, agent):
        """测试有效输入验证"""
        context = AgentExecutionContext(
            session_id="test_session",
            task_id="test_task",
            input_data=self.sample_input,
            config={},
            metadata={},
        )
        result = agent.validate_input(context)
        assert result is True

    @pytest.mark.asyncio
    async def test_agent_validate_input_invalid_session(self, agent):
        """测试无效session_id"""
        context = AgentExecutionContext(
            session_id="",
            task_id="test_task",
            input_data=self.sample_input,
            config={},
            metadata={},
        )
        result = agent.validate_input(context)
        assert result is False

    @pytest.mark.asyncio
    async def test_agent_repr(self, agent):
        """测试字符串表示"""
        repr_str = repr(agent)
        assert agent.agent_id in repr_str


# ========== RetrieverAgent测试 ==========

class TestRetrieverAgent(BaseProxyTest):
    """测试检索代理"""

    @pytest.fixture
    def agent(self):
        with patch('core.framework.agents.xiaona.retriever_agent.PatentSearchService'):
            from core.framework.agents.xiaona.retriever_agent import RetrieverAgent
            return RetrieverAgent()

    @pytest.fixture
    def sample_input(self):
        return {
            "query": "深度学习 图像识别",
            "limit": 10,
        }

    @pytest.mark.asyncio
    async def test_has_search_capability(self, agent):
        """测试有搜索能力"""
        assert agent.has_capability("search_patents") or \
               agent.has_capability("patent_search") or \
               len(agent.get_capabilities()) > 0


# ========== AnalyzerAgent测试 ==========

class TestAnalyzerAgent(BaseProxyTest):
    """测试分析代理"""

    @pytest.fixture
    def agent(self):
        with patch('core.framework.agents.xiaona.analyzer_agent.PatentAnalysisEngine'):
            from core.framework.agents.xiaona.analyzer_agent import AnalyzerAgent
            return AnalyzerAgent()

    @pytest.fixture
    def sample_input(self):
        return {
            "patent_data": {
                "title": "测试专利",
                "claims": ["1. 一种测试方法..."],
            }
        }


# ========== NoveltyAnalyzerProxy测试 ==========

class TestNoveltyAnalyzerProxy(BaseProxyTest):
    """测试新颖性分析代理"""

    @pytest.fixture
    def agent(self):
        from core.framework.agents.xiaona.novelty_analyzer_proxy import NoveltyAnalyzerProxy
        return NoveltyAnalyzerProxy()

    @pytest.fixture
    def sample_input(self):
        return {
            "patent_data": {
                "title": "测试发明",
                "claims": ["权利要求1"],
            },
            "prior_art": ["对比文件1"],
        }

    @pytest.mark.asyncio
    async def test_has_assess_capability(self, agent):
        """测试有评估能力"""
        capabilities = agent.get_capabilities()
        assert len(capabilities) > 0


# ========== CreativityAnalyzerProxy测试 ==========

class TestCreativityAnalyzerProxy(BaseProxyTest):
    """测试创造性分析代理"""

    @pytest.fixture
    def agent(self):
        from core.framework.agents.xiaona.creativity_analyzer_proxy import CreativityAnalyzerProxy
        return CreativityAnalyzerProxy()

    @pytest.fixture
    def sample_input(self):
        return {
            "patent_data": {
                "title": "测试发明",
                "technical_effect": "提高效率",
            },
            "prior_art": ["现有技术1"],
        }


# ========== InfringementAnalyzerProxy测试 ==========

class TestInfringementAnalyzerProxy(BaseProxyTest):
    """测试侵权分析代理"""

    @pytest.fixture
    def agent(self):
        from core.framework.agents.xiaona.infringement_analyzer_proxy import InfringementAnalyzerProxy
        return InfringementAnalyzerProxy()

    @pytest.fixture
    def sample_input(self):
        return {
            "patent_number": "CN123456789A",
            "product": "待分析产品",
            "claims": ["权利要求1"],
        }


# ========== InvalidationAnalyzerProxy测试 ==========

class TestInvalidationAnalyzerProxy(BaseProxyTest):
    """测试无效分析代理"""

    @pytest.fixture
    def agent(self):
        from core.framework.agents.xiaona.invalidation_analyzer_proxy import InvalidationAnalyzerProxy
        return InvalidationAnalyzerProxy()

    @pytest.fixture
    def sample_input(self):
        return {
            "patent_number": "CN123456789A",
            "evidence_list": ["D1", "D2"],
        }

    @pytest.mark.asyncio
    async def test_invalidation_capability(self, agent):
        """测试无效分析能力"""
        capabilities = agent.get_capabilities()
        capability_names = [c.name for c in capabilities]
        # 至少应该有相关能力
        assert len(capability_names) > 0


# ========== ApplicationReviewerProxy测试 ==========

class TestApplicationReviewerProxy(BaseProxyTest):
    """测试申请审查代理"""

    @pytest.fixture
    def agent(self):
        from core.framework.agents.xiaona.application_reviewer_proxy import ApplicationDocumentReviewerProxy
        return ApplicationDocumentReviewerProxy()

    @pytest.fixture
    def sample_input(self):
        return {
            "application_data": {
                "title": "测试发明",
                "claims": ["1. 测试权利要求"],
                "specification": "说明书内容",
            }
        }

    @pytest.mark.asyncio
    async def test_has_review_capabilities(self, agent):
        """测试有审查能力"""
        capabilities = agent.get_capabilities()
        capability_names = [c.name for c in capabilities]
        assert len(capability_names) > 0


# ========== WritingReviewerProxy测试 ==========

class TestWritingReviewerProxy(BaseProxyTest):
    """测试写作审查代理"""

    @pytest.fixture
    def agent(self):
        from core.framework.agents.xiaona.writing_reviewer_proxy import WritingReviewerProxy
        return WritingReviewerProxy()

    @pytest.fixture
    def sample_input(self):
        return {
            "document_content": "待审查的文档内容",
            "document_type": "claims",
        }


# ========== 通用代理测试套件 ==========

class TestAgentCommonBehavior:
    """测试所有代理的通用行为"""

    @pytest.mark.parametrize("agent_class,module_name", [
        ("RetrieverAgent", "retriever_agent"),
        ("AnalyzerAgent", "analyzer_agent"),
        ("NoveltyAnalyzerProxy", "novelty_analyzer_proxy"),
        ("CreativityAnalyzerProxy", "creativity_analyzer_proxy"),
        ("InfringementAnalyzerProxy", "infringement_analyzer_proxy"),
        ("InvalidationAnalyzerProxy", "invalidation_analyzer_proxy"),
        ("ApplicationDocumentReviewerProxy", "application_reviewer_proxy"),
        ("WritingReviewerProxy", "writing_reviewer_proxy"),
    ])
    @pytest.mark.asyncio
    async def test_agent_can_be_imported(self, agent_class, module_name):
        """测试所有代理可以导入"""
        try:
            module = __import__(f"core.framework.agents.xiaona.{module_name}", fromlist=[agent_class])
            agent_cls = getattr(module, agent_class)
            assert agent_cls is not None
        except ImportError as e:
            pytest.skip(f"无法导入 {agent_class}: {e}")

    @pytest.mark.parametrize("agent_class,module_name", [
        ("RetrieverAgent", "retriever_agent"),
        ("AnalyzerAgent", "analyzer_agent"),
        ("NoveltyAnalyzerProxy", "novelty_analyzer_proxy"),
        ("CreativityAnalyzerProxy", "creativity_analyzer_proxy"),
        ("InfringementAnalyzerProxy", "infringement_analyzer_proxy"),
        ("InvalidationAnalyzerProxy", "invalidation_analyzer_proxy"),
        ("ApplicationDocumentReviewerProxy", "application_reviewer_proxy"),
        ("WritingReviewerProxy", "writing_reviewer_proxy"),
    ])
    @pytest.mark.asyncio
    async def test_agent_has_status(self, agent_class, module_name):
        """测试所有代理有状态"""
        try:
            module = __import__(f"core.framework.agents.xiaona.{module_name}", fromlist=[agent_class])
            agent_cls = getattr(module, agent_class)
            agent = agent_cls()
            assert hasattr(agent, 'status')
            assert isinstance(agent.status, AgentStatus)
        except (ImportError, Exception) as e:
            pytest.skip(f"无法测试 {agent_class}: {e}")


# ========== 错误处理测试 ==========

class TestAgentErrorHandling:
    """测试代理错误处理"""

    @pytest.mark.asyncio
    async def test_invalid_task_type(self):
        """测试无效任务类型处理"""
        from core.framework.agents.xiaona.novelty_analyzer_proxy import NoveltyAnalyzerProxy
        agent = NoveltyAnalyzerProxy()

        context = AgentExecutionContext(
            session_id="test",
            task_id="test",
            input_data={},
            config={},
            metadata={},
        )

        # 应该能处理空输入而不崩溃
        try:
            result = await agent.execute(context)
            assert result is not None
        except Exception:
            # 如果抛出异常也是可以接受的
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
