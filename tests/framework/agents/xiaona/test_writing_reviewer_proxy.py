"""
撰写审查代理（WritingReviewerProxy）单元测试

测试内容：
1. 初始化测试
2. 能力注册测试
3. 系统提示词测试
4. 基本功能测试（使用mock）
"""

import pytest
from typing import Dict, List, Optional, Any

from unittest.mock import patch

from core.framework.agents.xiaona.writing_reviewer_proxy import WritingReviewerProxy
from core.framework.agents.xiaona.base_component import AgentExecutionContext


class TestWritingReviewerInitialization:
    """撰写审查代理初始化测试"""

    def test_writing_reviewer_initialization(self):
        """测试撰写审查代理初始化"""
        reviewer = WritingReviewerProxy()
        assert reviewer.agent_id == "writing_reviewer"
        assert reviewer.status.value == "idle"


class TestWritingReviewerCapabilities:
    """撰写审查代理能力注册测试"""

    def test_writing_reviewer_capabilities(self):
        """测试能力注册"""
        reviewer = WritingReviewerProxy()
        capabilities = reviewer.get_capabilities()
        capability_names = [c.name for c in capabilities]

        assert "legal_terminology_review" in capability_names
        assert "technical_accuracy_review" in capability_names
        assert "writing_style_consistency" in capability_names
        assert "writing_quality_assessment" in capability_names

    def test_writing_reviewer_capability_details(self):
        """测试能力详情"""
        reviewer = WritingReviewerProxy()
        capabilities = reviewer.get_capabilities()

        # 检查legal_terminology_review能力
        legal = next((c for c in capabilities if c.name == "legal_terminology_review"), None)
        assert legal is not None
        assert "法律用语规范性审查" in legal.description

    def test_writing_reviewer_has_capability(self):
        """测试能力检查方法"""
        reviewer = WritingReviewerProxy()
        assert reviewer.has_capability("legal_terminology_review")
        assert reviewer.has_capability("technical_accuracy_review")
        assert not reviewer.has_capability("nonexistent_capability")


class TestWritingReviewerSystemPrompt:
    """撰写审查代理系统提示词测试"""

    def test_get_system_prompt(self):
        """测试获取系统提示词"""
        reviewer = WritingReviewerProxy()
        prompt = reviewer.get_system_prompt()

        assert "专利撰写质量审查专家" in prompt
        assert "法律用语规范性" in prompt
        assert "技术描述准确性" in prompt
        assert "撰写风格一致性" in prompt


class TestWritingReviewerExecute:
    """撰写审查代理基本功能测试"""

    @pytest.mark.asyncio
    async def test_execute_default_task(self):
        """测试默认任务执行（完整审查）"""
        reviewer = WritingReviewerProxy()

        context = AgentExecutionContext(
            session_id="test_session",
            task_id="test_task",
            input_data={
                "application_id": "APP123",
                "claims": "1. 一种测试装置...",
                "specification": "说明书内容..."
            },
            config={},
            metadata={}
        )

        # 使用规则降级
        with patch.object(reviewer, '_call_llm_with_fallback', side_effect=Exception("LLM失败")):
            result = await reviewer.execute(context)

        assert "application_id" in result
        assert "legal_terminology_review" in result
        assert "overall_quality" in result

    @pytest.mark.asyncio
    async def test_review_legal_terminology(self):
        """测试法律用语审查"""
        reviewer = WritingReviewerProxy()

        application = {
            "claims": "1. 一种装置，大约包括特征A。",  # 包含禁用词
            "specification": "说明书内容..."
        }

        result = await reviewer.review_legal_terminology(application)

        assert "status" in result
        assert "score" in result
        assert "terminology_issues" in result

    @pytest.mark.asyncio
    async def test_review_technical_accuracy(self):
        """测试技术准确性审查"""
        reviewer = WritingReviewerProxy()

        application = {
            "technical_field": "测试技术领域",
            "technical_problem": "需要解决的问题",
            "technical_solution": "解决方案包括特征A",
            "beneficial_effects": "达到效果X"
        }

        result = await reviewer.review_technical_accuracy(application)

        assert "status" in result
        assert "score" in result
        assert "accuracy_issues" in result

    @pytest.mark.asyncio
    async def test_check_writing_style_consistency(self):
        """测试撰写风格一致性检查"""
        reviewer = WritingReviewerProxy()

        application = {
            "claims": "1. 一种装置，包括特征A。",
            "specification": "说明书包括该装置...",
            "abstract": "摘要内容..."
        }

        result = await reviewer.check_writing_style_consistency(application)

        assert "overall_consistency" in result
        assert "overall_score" in result
        assert "style_checks" in result

    @pytest.mark.asyncio
    async def test_assess_writing_quality(self):
        """测试撰写质量评估"""
        reviewer = WritingReviewerProxy()

        legal_review = {"score": 0.8}
        technical_review = {"score": 0.75}
        style_review = {"overall_score": 0.85}

        result = await reviewer.assess_writing_quality(
            legal_review, technical_review, style_review
        )

        assert "overall_score" in result
        assert "overall_quality" in result
        assert "dimensions" in result


class TestWritingReviewerHelperMethods:
    """撰写审查代理辅助方法测试"""

    def test_check_terminology_consistency(self):
        """测试检查术语一致性"""
        reviewer = WritingReviewerProxy()

        text = "该传感器用于检测。传感器包括多个类型。感应器也是类似功能。"

        result = reviewer._check_terminology_consistency(text)

        assert "score" in result
        assert "consistent_terms_count" in result

    def test_check_problem_solution_consistency(self):
        """测试检查问题与解决方案一致性"""
        reviewer = WritingReviewerProxy()

        # 一致的情况
        problem = "如何提高效率"
        solution = "本发明通过优化算法提高效率"

        result1 = reviewer._check_problem_solution_consistency(problem, solution)
        assert result1["is_consistent"] is True

        # 不一致的情况
        result2 = reviewer._check_problem_solution_consistency(problem, "本发明降低成本")
        assert result2["is_consistent"] is False

    def test_check_technical_terms_accuracy(self):
        """测试检查技术术语准确性"""
        reviewer = WritingReviewerProxy()

        result = reviewer._check_technical_terms_accuracy("软件", "硬件装置包括软件组件")

        assert "issues" in result
        assert "accuracy_score" in result

    def test_check_effect_rationality(self):
        """测试检查有益效果合理性"""
        reviewer = WritingReviewerProxy()

        # 有因果关系
        result1 = reviewer._check_effect_rationality("方案", "由于采用新结构，因此效率显著提高")
        assert result1["is_rational"] is True

        # 无因果关系
        result2 = reviewer._check_effect_rationality("方案", "效果很好")
        assert result2["is_rational"] is False

    def test_check_tense_consistency(self):
        """测试检查时态一致性"""
        reviewer = WritingReviewerProxy()

        claims = "1. 一种装置包括特征A。"  # 现在时
        result = reviewer._check_tense_consistency(claims, "说明书")

        assert "score" in result
        assert "issues" in result

    def test_check_format_consistency(self):
        """测试检查格式一致性"""
        reviewer = WritingReviewerProxy()

        claims = "1. 一种装置包括特征A。\n2. 还包括特征B。"
        result = reviewer._check_format_consistency(claims, "说明书")

        assert "score" in result

    def test_check_numbering_consistency(self):
        """测试检查编号一致性"""
        reviewer = WritingReviewerProxy()

        claims = "权利要求引用图1"
        specification = "说明书无附图说明"

        result = reviewer._check_numbering_consistency(claims, specification, "", "")

        assert "score" in result
        assert "issues" in result

    def test_extract_keywords(self):
        """测试提取关键词"""
        reviewer = WritingReviewerProxy()

        text = "该装置包括传感器、控制器和执行器，用于实现自动化控制。"

        keywords = reviewer._extract_keywords(text)

        assert isinstance(keywords, list)

    def test_get_quality_level(self):
        """测试获取质量等级"""
        reviewer = WritingReviewerProxy()

        assert reviewer._get_quality_level(0.95) == "优秀"
        assert reviewer._get_quality_level(0.8) == "良好"
        assert reviewer._get_quality_level(0.65) == "合格"
        assert reviewer._get_quality_level(0.4) == "待改进"

    def test_identify_strengths(self):
        """测试识别优势"""
        reviewer = WritingReviewerProxy()

        dimensions = {
            "professionalism": {"score": 0.85, "level": "良好"},
            "accuracy": {"score": 0.9, "level": "优秀"},
            "readability": {"score": 0.7, "level": "合格"}
        }

        strengths = reviewer._identify_strengths(dimensions)

        assert len([s for s in strengths if "优秀" in s or "良好" in s]) > 0

    def test_identify_weaknesses(self):
        """测试识别劣势"""
        reviewer = WritingReviewerProxy()

        dimensions = {
            "professionalism": {"score": 0.5, "level": "待改进"},
            "accuracy": {"score": 0.4, "level": "待改进"},
            "readability": {"score": 0.8, "level": "良好"}
        }

        weaknesses = reviewer._identify_weaknesses(dimensions)

        assert len([w for w in weaknesses if "待改进" in w]) > 0

    def test_determine_improvement_priority(self):
        """测试确定改进优先级"""
        reviewer = WritingReviewerProxy()

        dimensions = {
            "professionalism": {"score": 0.5},
            "accuracy": {"score": 0.4},
            "readability": {"score": 0.8}
        }

        priorities = reviewer._determine_improvement_priority(dimensions)

        assert len(priorities) > 0
        assert all("aspect" in p for p in priorities)

    def test_get_improvement_suggestions(self):
        """测试获取改进建议"""
        reviewer = WritingReviewerProxy()

        suggestions = reviewer._get_improvement_suggestions("professionalism")

        assert isinstance(suggestions, list)

    def test_get_timestamp(self):
        """测试获取时间戳"""
        reviewer = WritingReviewerProxy()
        timestamp = reviewer._get_timestamp()

        assert isinstance(timestamp, str)
        assert len(timestamp) > 0


class TestWritingReviewerInfo:
    """撰写审查代理信息测试"""

    def test_get_info(self):
        """测试获取代理信息"""
        reviewer = WritingReviewerProxy()
        info = reviewer.get_info()

        assert info["agent_id"] == "writing_reviewer"
        assert info["agent_type"] == "WritingReviewerProxy"
        assert "capabilities" in info

    def test_repr(self):
        """测试代理字符串表示"""
        reviewer = WritingReviewerProxy()
        repr_str = repr(reviewer)

        assert "WritingReviewerProxy" in repr_str
