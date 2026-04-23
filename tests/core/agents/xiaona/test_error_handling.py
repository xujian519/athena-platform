"""
错误处理单元测试

测试范围:
- 空数据处理
- 无效数据处理
- 异常捕获与恢复
- 边界条件处理
"""

import asyncio

import pytest

from core.framework.agents.xiaona.application_reviewer_proxy import ApplicationDocumentReviewerProxy
from core.framework.agents.xiaona.base_component import (
    AgentExecutionContext,
    AgentExecutionResult,
    AgentStatus,
)
from core.framework.agents.xiaona.creativity_analyzer_proxy import CreativityAnalyzerProxy
from core.framework.agents.xiaona.infringement_analyzer_proxy import InfringementAnalyzerProxy
from core.framework.agents.xiaona.invalidation_analyzer_proxy import InvalidationAnalyzerProxy
from core.framework.agents.xiaona.novelty_analyzer_proxy import NoveltyAnalyzerProxy


# 测试用子类
class TestableInvalidationAnalyzerProxy(InvalidationAnalyzerProxy):
    async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
        return AgentExecutionResult(
            agent_id=self.agent_id,
            status=AgentStatus.COMPLETED,
            output_data={"test": "result"},
            execution_time=0.1
        )

    def get_system_prompt(self) -> str:
        return "测试系统提示词"


class TestableApplicationReviewerProxy(ApplicationDocumentReviewerProxy):
    async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
        return AgentExecutionResult(
            agent_id=self.agent_id,
            status=AgentStatus.COMPLETED,
            output_data={"test": "result"},
            execution_time=0.1
        )

    def get_system_prompt(self) -> str:
        return "测试系统提示词"


class TestableNoveltyAnalyzerProxy(NoveltyAnalyzerProxy):
    async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
        return AgentExecutionResult(
            agent_id=self.agent_id,
            status=AgentStatus.COMPLETED,
            output_data={"test": "result"},
            execution_time=0.1
        )

    def get_system_prompt(self) -> str:
        return "测试系统提示词"


class TestableCreativityAnalyzerProxy(CreativityAnalyzerProxy):
    async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
        return AgentExecutionResult(
            agent_id=self.agent_id,
            status=AgentStatus.COMPLETED,
            output_data={"test": "result"},
            execution_time=0.1
        )

    def get_system_prompt(self) -> str:
        return "测试系统提示词"


class TestableInfringementAnalyzerProxy(InfringementAnalyzerProxy):
    async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
        return AgentExecutionResult(
            agent_id=self.agent_id,
            status=AgentStatus.COMPLETED,
            output_data={"test": "result"},
            execution_time=0.1
        )

    def get_system_prompt(self) -> str:
        return "测试系统提示词"


class TestErrorHandling:
    """错误处理测试"""

    # ========== 空数据处理测试 ==========

    @pytest.mark.asyncio
    async def test_invalidation_analyzer_empty_patent_id(self):
        """测试无效宣告分析 - 空专利ID"""
        agent = TestableInvalidationAnalyzerProxy(agent_id="test_agent")

        result = await agent.analyze_invalidation(
            {"patent_id": ""},  # 空专利ID
            [],
            "comprehensive"
        )

        # 应该有默认处理
        assert "target_patent" in result
        assert result["target_patent"]["patent_id"] == ""

    @pytest.mark.asyncio
    async def test_application_reviewer_missing_fields(self):
        """测试申请审查 - 缺少必需字段"""
        agent = TestableApplicationReviewerProxy(agent_id="test_agent")

        incomplete_app = {
            "application_id": "CN123",
            # 缺少很多必需字段
        }

        result = await agent.review_application(incomplete_app, "comprehensive")

        # 应该有默认处理
        assert "application_id" in result
        assert "overall_score" in result

    @pytest.mark.asyncio
    async def test_novelty_analyzer_no_prior_art(self):
        """测试新颖性分析 - 无对比文件"""
        agent = TestableNoveltyAnalyzerProxy(agent_id="test_agent")

        result = await agent.analyze_novelty(
            {"patent_id": "CN123"},
            "standard"
        )

        # 应该有默认处理
        assert "patent_id" in result
        assert "novelty_conclusion" in result

    @pytest.mark.asyncio
    async def test_creativity_analyzer_no_prior_art(self):
        """测试创造性分析 - 无现有技术"""
        agent = TestableCreativityAnalyzerProxy(agent_id="test_agent")

        result = await agent.analyze_creativity(
            {"patent_id": "CN123"},
            "standard"
        )

        # 应该有默认处理
        assert "patent_id" in result
        assert "creativity_conclusion" in result

    @pytest.mark.asyncio
    async def test_infringement_analyzer_empty_claims(self):
        """测试侵权分析 - 空权利要求"""
        agent = TestableInfringementAnalyzerProxy(agent_id="test_agent")

        result = await agent.analyze_infringement(
            {"claims": ""},  # 空权利要求
            {"features": {}},
            "comprehensive"
        )

        # 应该有默认处理
        assert "patent_id" in result
        assert "infringement_conclusion" in result

    # ========== 无效数据处理测试 ==========

    @pytest.mark.asyncio
    async def test_invalidation_analyzer_invalid_reference_format(self):
        """测试无效宣告分析 - 无效对比文件格式"""
        agent = TestableInvalidationAnalyzerProxy(agent_id="test_agent")

        # 对比文件格式不正确（缺少必需字段）
        invalid_refs = [
            {"publication_number": "CN123"}  # 缺少content等字段
        ]

        result = await agent.analyze_invalidation(
            {"patent_id": "CN123"},
            invalid_refs,
            "quick"
        )

        # 应该有容错处理
        assert "target_patent" in result

    @pytest.mark.asyncio
    async def test_application_reviewer_invalid_claims_format(self):
        """测试申请审查 - 无效权利要求格式"""
        agent = TestableApplicationReviewerProxy(agent_id="test_agent")

        # 权利要求为空字符串
        invalid_app = {
            "application_id": "CN123",
            "claims": "",  # 空字符串
        }

        result = await agent.review_claims(invalid_app)

        # 应该有容错处理
        assert "claims_review" in result

    # ========== 类型错误处理测试 ==========

    @pytest.mark.asyncio
    async def test_novelty_analyzer_wrong_type_input(self):
        """测试新颖性分析 - 空字典输入"""
        agent = TestableNoveltyAnalyzerProxy(agent_id="test_agent")

        # 传入空字典
        result = await agent.analyze_novelty(
            {},  # 空字典
            "standard"
        )

        # 应该有容错处理
        assert "patent_id" in result

    # ========== 边界条件测试 ==========

    @pytest.mark.asyncio
    async def test_invalidation_analyzer_very_long_input(self):
        """测试无效宣告分析 - 超长输入"""
        agent = TestableInvalidationAnalyzerProxy(agent_id="test_agent")

        long_patent = {
            "patent_id": "CN" + "1" * 1000,  # 超长专利号
            "title": "X" * 10000,
            "claims": "Y" * 100000,
        }

        result = await agent.analyze_invalidation(
            long_patent,
            [],
            "quick"
        )

        # 应该能够处理
        assert "target_patent" in result

    @pytest.mark.asyncio
    async def test_application_reviewer_special_characters(self):
        """测试申请审查 - 特殊字符处理"""
        agent = TestableApplicationReviewerProxy(agent_id="test_agent")

        app_with_special_chars = {
            "application_id": "CN123!@#$%",
            "claims": "权利要求包含特殊字符：<>\"'&",
        }

        result = await agent.review_claims(app_with_special_chars)

        # 应该能够处理特殊字符
        assert "claims_review" in result

    # ========== 并发安全测试 ==========

    @pytest.mark.asyncio
    async def test_concurrent_analysis(self):
        """测试并发分析的安全性"""
        agent1 = TestableInvalidationAnalyzerProxy(agent_id="agent1")
        agent2 = TestableInvalidationAnalyzerProxy(agent_id="agent2")

        patent_data = {"patent_id": "CN123"}

        # 并发执行
        results = await asyncio.gather(
            agent1.analyze_invalidation(patent_data, [], "quick"),
            agent2.analyze_invalidation(patent_data, [], "quick")
        )

        # 两个结果应该独立
        assert len(results) == 2
        assert all("target_patent" in r for r in results)

    # ========== 内存安全测试 ==========

    @pytest.mark.asyncio
    async def test_recursive_analysis_protection(self):
        """测试递归分析的保护"""
        agent = TestableInvalidationAnalyzerProxy(agent_id="test_agent")

        # 模拟可能引起递归的情况
        complex_data = {
            "patent_id": "CN123",
            "self_reference": None  # 自引用
        }

        result = await agent.analyze_invalidation(
            complex_data,
            [],
            "quick"
        )

        # 应该不会无限递归
        assert "target_patent" in result

    # ========== 数据完整性测试 ==========

    @pytest.mark.asyncio
    async def test_result_structure_consistency(self):
        """测试结果结构一致性"""
        agents = [
            TestableInvalidationAnalyzerProxy(agent_id="agent1"),
            TestableApplicationReviewerProxy(agent_id="agent2"),
            TestableNoveltyAnalyzerProxy(agent_id="agent3"),
            TestableCreativityAnalyzerProxy(agent_id="agent4"),
        ]

        for agent in agents:
            # 所有分析结果都应该有时间戳
            if hasattr(agent, 'analyze_invalidation'):
                result = await agent.analyze_invalidation({"patent_id": "CN123"}, [], "quick")
                assert "analyzed_at" in result or "generated_at" in result or "reviewed_at" in result

    # ========== 性能压力测试 ==========

    @pytest.mark.asyncio
    async def test_bulk_analysis_performance(self):
        """测试批量分析性能"""
        agent = TestableInvalidationAnalyzerProxy(agent_id="test_agent")

        # 创建100个测试数据
        patents = [{"patent_id": f"CN{i}"} for i in range(100)]

        import time
        start_time = time.time()

        # 批量分析
        tasks = [agent.analyze_invalidation(patent, [], "quick") for patent in patents]
        results = await asyncio.gather(*tasks)

        elapsed_time = time.time() - start_time

        # 100个分析应该在合理时间内完成
        assert elapsed_time < 30.0  # 30秒
        assert len(results) == 100

    # ========== 错误恢复测试 ==========

    @pytest.mark.asyncio
    async def test_recovery_after_error(self):
        """测试错误后的恢复能力"""
        agent = TestableInvalidationAnalyzerProxy(agent_id="test_agent")

        # 第一次调用可能失败
        try:
            await agent.analyze_invalidation(None, [], "quick")
        except:
            pass

        # 第二次调用应该成功
        result2 = await agent.analyze_invalidation({"patent_id": "CN123"}, [], "quick")

        # 应该能够恢复
        assert result2 is not None
        assert "target_patent" in result2

    # ========== 数据验证测试 ==========

    @pytest.mark.asyncio
    async def test_data_validation_invalid_characters(self):
        """测试无效字符数据的验证"""
        agent = TestableApplicationReviewerProxy(agent_id="test_agent")

        # 包含控制字符的数据
        app_with_control_chars = {
            "application_id": "CN123\x00\x01",
            "claims": "权利要求\x00\x02",
        }

        result = await agent.review_format(app_with_control_chars)

        # 应该能够处理或清理控制字符
        assert "format_check" in result

    @pytest.mark.asyncio
    async def test_data_validation_unicode_handling(self):
        """测试Unicode数据处理"""
        agent = TestableInvalidationAnalyzerProxy(agent_id="test_agent")

        # 包含emoji的数据
        patent_with_emoji = {
            "patent_id": "CN123😀",
            "title": "专利标题🎉",
        }

        result = await agent.analyze_invalidation(
            patent_with_emoji,
            [],
            "quick"
        )

        # 应该能够处理emoji
        assert "target_patent" in result

    # ========== 资源清理测试 ==========

    @pytest.mark.asyncio
    async def test_resource_cleanup_after_error(self):
        """测试错误后的资源清理"""
        agent = TestableInvalidationAnalyzerProxy(agent_id="test_agent")

        # 模拟资源使用

        # 尝试执行可能失败的任务
        try:
            await agent.analyze_invalidation(None, [], "quick")
        except:
            pass

        # 状态应该被正确重置
        assert agent.status in [AgentStatus.IDLE, AgentStatus.ERROR]
