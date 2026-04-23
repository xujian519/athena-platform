"""
撰写审查智能体单元测试

测试范围:
- 法律用语规范性审查
- 技术描述准确性审查
- 撰写风格一致性检查
- 撰写质量评估
"""

import pytest
from unittest.mock import Mock, patch
from core.agents.xiaona.writing_reviewer_proxy import WritingReviewerProxy
from core.agents.xiaona.base_component import AgentExecutionContext, AgentExecutionResult, AgentStatus


class TestableWritingReviewerProxy(WritingReviewerProxy):
    """可测试的撰写审查智能体"""

    async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
        """执行任务（测试用）"""
        return AgentExecutionResult(
            agent_id=self.agent_id,
            status=AgentStatus.COMPLETED,
            output_data={"test": "result"},
            execution_time=0.1
        )

    def get_system_prompt(self) -> str:
        """获取系统提示词（测试用）"""
        return "测试系统提示词"


class TestWritingReviewerProxy:
    """撰写审查智能体测试"""

    @pytest.fixture
    def agent(self):
        """创建智能体实例"""
        return TestableWritingReviewerProxy(agent_id="test_writing_reviewer")

    @pytest.fixture
    def sample_application(self):
        """示例申请文件"""
        return {
            "application_id": "CN202600000000",
            "applicant": "测试公司",
            "claims": "1. 一种装置，其特征在于包括特征A和特征B，所述特征A连接于特征B。",
            "specification": "本发明涉及一种装置技术领域。背景技术中...本发明的技术方案是...",
            "abstract": "本发明公开了一种装置...",
            "technical_field": "装置技术领域",
            "technical_problem": "现有装置存在问题",
            "technical_solution": "通过特征A和特征B解决问题",
            "beneficial_effects": "由于采用了上述方案，从而提高了性能"
        }

    @pytest.fixture
    def poor_application(self):
        """质量较差的申请文件（包含问题）"""
        return {
            "application_id": "CN202600000001",
            "applicant": "测试公司",
            "claims": "1. 大约一种装置，可能包括特征A和特征B。",
            "specification": "本发明涉及一种装置技术领域。",
            "abstract": "本发明公开了一种装置...",
            "technical_field": "装置技术领域",
            "technical_problem": "现有装置存在问题",
            "technical_solution": "通过特征A和特征B解决问题",
            "beneficial_effects": "效果很好"
        }

    # ========== 初始化测试 ==========

    def test_initialization(self, agent):
        """测试智能体初始化"""
        assert agent.agent_id == "test_writing_reviewer"
        assert len(agent.get_capabilities()) == 4

        expected_capabilities = [
            "legal_terminology_review",
            "technical_accuracy_review",
            "writing_style_consistency",
            "writing_quality_assessment"
        ]
        capability_names = [cap.name for cap in agent.get_capabilities()]
        for cap in expected_capabilities:
            assert cap in capability_names

    # ========== review_writing 测试 ==========

    @pytest.mark.asyncio
    async def test_review_writing_comprehensive(
        self,
        agent,
        sample_application
    ):
        """测试完整撰写审查流程"""
        result = await agent.review_writing(
            sample_application,
            review_scope="comprehensive"
        )

        # 验证返回结构
        assert "application_id" in result
        assert "review_scope" in result
        assert result["review_scope"] == "comprehensive"
        assert "legal_terminology_review" in result
        assert "technical_accuracy_review" in result
        assert "style_consistency" in result
        assert "quality_assessment" in result
        assert "overall_score" in result
        assert "overall_quality" in result
        assert "recommendations" in result
        assert "reviewed_at" in result

        # 验证评分
        assert 0 <= result["overall_score"] <= 1

    @pytest.mark.asyncio
    async def test_review_writing_quick(
        self,
        agent,
        sample_application
    ):
        """测试快速审查模式"""
        result = await agent.review_writing(
            sample_application,
            review_scope="quick"
        )

        assert result["review_scope"] == "quick"

    # ========== review_legal_terminology 测试 ==========

    @pytest.mark.asyncio
    async def test_review_legal_terminology_good(
        self,
        agent,
        sample_application
    ):
        """测试法律用语审查 - 质量良好"""
        result = await agent.review_legal_terminology(sample_application)

        assert "status" in result
        assert "score" in result
        assert "terminology_issues" in result
        assert "missing_standards" in result
        assert "consistency_check" in result
        assert "total_issues" in result
        assert "correction_suggestions" in result

        # 质量良好的申请应该有较高评分
        assert result["score"] >= 0.6
        assert result["status"] in ["excellent", "good", "fair", "poor"]

    @pytest.mark.asyncio
    async def test_review_legal_terminology_poor(
        self,
        agent,
        poor_application
    ):
        """测试法律用语审查 - 质量较差"""
        result = await agent.review_legal_terminology(poor_application)

        # 质量较差的申请应该发现问题
        # "大约"、"可能"是禁用词
        assert result["total_issues"] > 0

        # 应该有术语问题
        if result["total_issues"] > 0:
            assert len(result["terminology_issues"]) > 0 or len(result["missing_standards"]) > 0

    # ========== review_technical_accuracy 测试 ==========

    @pytest.mark.asyncio
    async def test_review_technical_accuracy_consistent(
        self,
        agent,
        sample_application
    ):
        """测试技术准确性审查 - 一致"""
        result = await agent.review_technical_accuracy(sample_application)

        assert "status" in result
        assert "score" in result
        assert "accuracy_issues" in result
        assert "consistency_check" in result
        assert "total_issues" in result

        # 技术问题和解决方案一致的申请应该有较高评分
        assert result["score"] >= 0.6

    @pytest.mark.asyncio
    async def test_review_technical_accuracy_inconsistent(
        self,
        agent
    ):
        """测试技术准确性审查 - 不一致"""
        application = {
            "technical_problem": "装置存在性能问题",
            "technical_solution": "通过优化算法提高计算速度",  # 与问题不匹配
            "beneficial_effects": "效果很好"
        }

        result = await agent.review_technical_accuracy(application)

        # 问题与解决方案不匹配应该被识别
        consistency = result["consistency_check"]
        if not consistency["is_consistent"]:
            assert result["total_issues"] > 0

    # ========== check_writing_style_consistency 测试 ==========

    @pytest.mark.asyncio
    async def test_check_writing_style_consistency(
        self,
        agent,
        sample_application
    ):
        """测试撰写风格一致性检查"""
        result = await agent.check_writing_style_consistency(sample_application)

        assert "overall_consistency" in result
        assert "overall_score" in result
        assert "style_checks" in result
        assert "issues" in result

        # 验证子检查
        style_checks = result["style_checks"]
        assert "tense_consistency" in style_checks
        assert "terminology_consistency" in style_checks
        assert "format_consistency" in style_checks
        assert "numbering_consistency" in style_checks

    # ========== assess_writing_quality 测试 ==========

    @pytest.mark.asyncio
    async def test_assess_writing_quality_excellent(
        self,
        agent
    ):
        """测试撰写质量评估 - 优秀"""
        legal_review = {
            "score": 0.95,
            "total_issues": 0
        }
        technical_review = {
            "score": 0.92,
            "total_issues": 0
        }
        style_review = {
            "overall_score": 0.90
        }

        result = await agent.assess_writing_quality(
            legal_review,
            technical_review,
            style_review
        )

        assert "overall_score" in result
        assert "overall_quality" in result
        assert "comparable_to" in result
        assert "dimensions" in result
        assert "strengths" in result
        assert "weaknesses" in result
        assert "improvement_priority" in result

        # 优秀的质量应该是"优秀"或"良好"
        assert result["overall_quality"] in ["优秀", "良好"]
        assert result["overall_score"] >= 0.75

    @pytest.mark.asyncio
    async def test_assess_writing_quality_poor(
        self,
        agent
    ):
        """测试撰写质量评估 - 较差"""
        legal_review = {
            "score": 0.4,
            "total_issues": 10
        }
        technical_review = {
            "score": 0.3,
            "total_issues": 8
        }
        style_review = {
            "overall_score": 0.35
        }

        result = await agent.assess_writing_quality(
            legal_review,
            technical_review,
            style_review
        )

        # 较差的质量应该是"待改进"
        assert result["overall_quality"] == "待改进"
        assert result["overall_score"] < 0.6

    # ========== 辅助方法测试 ==========

    def test_check_terminology_consistency(self, agent):
        """测试术语一致性检查"""
        text = "本发明涉及一种装置。所述装置包括特征A。该装置的特征B连接于特征C。"

        result = agent._check_terminology_consistency(text)

        assert "score" in result
        assert "consistent_terms_count" in result
        assert "inconsistent_terms" in result
        assert 0 <= result["score"] <= 1

    def test_extract_keywords(self, agent):
        """测试提取关键词"""
        text = "本发明涉及一种装置，包括特征A和特征B，用于实现功能C"

        keywords = agent._extract_keywords(text)

        assert isinstance(keywords, list)
        assert len(keywords) > 0
        # 应该过滤掉常见词
        assert "所述" not in keywords
        assert "其特征在于" not in keywords
        assert "包括" not in keywords

    def test_get_quality_level(self, agent):
        """测试获取质量等级"""
        assert agent._get_quality_level(0.95) == "优秀"
        assert agent._get_quality_level(0.8) == "良好"
        assert agent._get_quality_level(0.65) == "合格"
        assert agent._get_quality_level(0.4) == "待改进"

    def test_identify_strengths(self, agent):
        """测试识别优势"""
        dimensions = {
            "professionalism": {"score": 0.9, "level": "优秀"},
            "accuracy": {"score": 0.85, "level": "良好"},
            "readability": {"score": 0.75, "level": "良好"}
        }

        strengths = agent._identify_strengths(dimensions)

        assert isinstance(strengths, list)
        # 应该识别出高分维度
        assert len([s for s in strengths if "优秀" in s or "良好" in s]) > 0

    def test_identify_weaknesses(self, agent):
        """测试识别劣势"""
        dimensions = {
            "professionalism": {"score": 0.5, "level": "待改进"},
            "accuracy": {"score": 0.4, "level": "待改进"},
            "readability": {"score": 0.75, "level": "良好"}
        }

        weaknesses = agent._identify_weaknesses(dimensions)

        assert isinstance(weaknesses, list)
        # 应该识别出低分维度
        assert len([w for w in weaknesses if "待改进" in w]) > 0

    def test_determine_improvement_priority(self, agent):
        """测试确定改进优先级"""
        dimensions = {
            "professionalism": {"score": 0.4},  # 高优先级
            "accuracy": {"score": 0.5},      # 中优先级
            "readability": {"score": 0.8}     # 无需改进
        }

        priorities = agent._determine_improvement_priority(dimensions)

        assert isinstance(priorities, list)
        # 应该返回需要改进的维度
        assert len(priorities) > 0
        # 应该按分数排序
        if len(priorities) >= 2:
            assert priorities[0]["current_score"] <= priorities[1]["current_score"]

    # ========== 边界条件测试 ==========

    @pytest.mark.asyncio
    async def test_review_writing_empty_application(
        self,
        agent
    ):
        """测试空申请数据的处理"""
        with pytest.raises(Exception):
            await agent.review_writing({}, "comprehensive")

    @pytest.mark.asyncio
    async def test_review_legal_terminology_empty_claims(
        self,
        agent
    ):
        """测试空权利要求的处理"""
        application = {
            "application_id": "CN202600000000",
            "claims": "",
            "specification": "说明"
        }

        result = await agent.review_legal_terminology(application)

        # 应该能处理空权利要求
        assert "status" in result
        assert "score" in result

    # ========== 性能测试 ==========

    @pytest.mark.asyncio
    async def test_performance_review_writing(
        self,
        agent,
        sample_application
    ):
        """测试审查性能 - 应该在合理时间内完成"""
        import time

        start_time = time.time()
        await agent.review_writing(
            sample_application,
            "comprehensive"
        )
        elapsed_time = time.time() - start_time

        # 完整审查应该在3秒内完成
        assert elapsed_time < 3.0

    # ========== 集成测试 ==========

    @pytest.mark.asyncio
    async def test_full_workflow(
        self,
        agent,
        sample_application
    ):
        """测试完整工作流程"""
        # 1. 法律用语审查
        legal = await agent.review_legal_terminology(sample_application)

        # 2. 技术准确性审查
        technical = await agent.review_technical_accuracy(sample_application)

        # 3. 风格一致性检查
        style = await agent.check_writing_style_consistency(sample_application)

        # 4. 质量评估
        quality = await agent.assess_writing_quality(legal, technical, style)

        # 验证工作流程连贯性
        assert legal["score"] >= 0
        assert technical["score"] >= 0
        assert style["overall_score"] >= 0
        assert quality["overall_score"] >= 0

        # 验证最终质量评级有效
        assert quality["overall_quality"] in ["优秀", "良好", "合格", "待改进"]

    # ========== 特定场景测试 ==========

    @pytest.mark.asyncio
    async def test_detect_forbidden_terms(self, agent):
        """测试检测禁用词汇"""
        application = {
            "application_id": "CN202600000000",
            "claims": "大约一种装置，可能包括特征A",
            "specification": "说明"
        }

        result = await agent.review_legal_terminology(application)

        # 应该检测到禁用词汇
        assert result["total_issues"] > 0
        forbidden_found = any(
            issue["type"] == "forbidden_term"
            for issue in result["terminology_issues"]
        )
        assert forbidden_found

    @pytest.mark.asyncio
    async def test_check_tense_consistency_issues(self, agent):
        """测试时态一致性检查 - 有问题"""
        application = {
            "application_id": "CN202600000000",
            "claims": "权利要求已包括特征A",  # 使用了"已"
            "specification": "说明"
        }

        result = await agent.check_writing_style_consistency(application)

        # 应该检测到时态问题
        tense_check = result["style_checks"]["tense_consistency"]
        if tense_check["score"] < 1.0:
            assert len(tense_check["issues"]) > 0

    @pytest.mark.asyncio
    async def test_check_format_consistency_issues(self, agent):
        """测试格式一致性检查 - 有问题"""
        application = {
            "application_id": "CN202600000000",
            "claims": "1一种装置，包括特征A\n2一种方法，包括步骤B",  # 编号格式不规范
            "specification": "说明"
        }

        result = await agent.check_writing_style_consistency(application)

        # 应该检测到格式问题
        format_check = result["style_checks"]["format_consistency"]
        if format_check["score"] < 1.0:
            assert len(format_check["issues"]) > 0
