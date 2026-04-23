"""
测试WritingReviewerProxy的LLM集成

测试撰写审查智能体的LLM调用、降级机制和各项检查功能。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from core.agents.xiaona.writing_reviewer_proxy import WritingReviewerProxy


@pytest.fixture
def writing_reviewer():
    """创建WritingReviewerProxy实例"""
    return WritingReviewerProxy(
        agent_id="test_writing_reviewer",
        config={"llm_config": {"model": "claude-3-5-sonnet-20241022"}}
    )


@pytest.fixture
def sample_application():
    """示例申请文件数据"""
    return {
        "application_id": "CN202310000000.0",
        "applicant": "测试申请人",
        "technical_field": "本发明涉及人工智能技术领域，具体涉及一种自动驾驶控制方法。",
        "background_art": "现有技术中，自动驾驶技术存在反应时间长的问题。",
        "technical_problem": "本发明要解决的技术问题是提高自动驾驶系统的反应速度。",
        "technical_solution": "本发明提供一种自动驾驶控制方法，包括：获取传感器数据；通过神经网络处理数据；输出控制指令。",
        "beneficial_effects": "本发明能够显著提高自动驾驶系统的反应速度，提升行车安全性。",
        "claims": """1. 一种自动驾驶控制方法，其特征在于，包括：
获取传感器数据；
通过神经网络处理所述传感器数据；
输出控制指令。

2. 根据权利要求1所述的方法，其特征在于，所述传感器数据包括图像数据和雷达数据。""",
        "specification": """
【技术领域】
本发明涉及人工智能技术领域，具体涉及一种自动驾驶控制方法。

【背景技术】
现有技术中，自动驾驶技术存在反应时间长的问题。

【发明内容】
本发明要解决的技术问题是提高自动驾驶系统的反应速度。
本发明提供一种自动驾驶控制方法，包括：获取传感器数据；通过神经网络处理数据；输出控制指令。

【具体实施方式】
下面结合附图对本发明作进一步说明。
""",
        "abstract": "本发明公开了一种自动驾驶控制方法，包括获取传感器数据、通过神经网络处理数据、输出控制指令。",
        "description": "本发明涉及自动驾驶技术领域。",
    }


class TestLLMIntegration:
    """测试LLM集成功能"""

    @pytest.mark.asyncio
    async def test_review_writing_with_llm_success(self, writing_reviewer, sample_application):
        """测试LLM撰写审查成功调用"""
        # Mock LLM响应
        mock_response = """```json
{
    "legal_terminology_review": {
        "status": "good",
        "score": 0.85,
        "terminology_issues": [],
        "missing_standards": [],
        "consistency_check": {
            "score": 0.9,
            "consistent_terms_count": 25,
            "inconsistent_terms": []
        },
        "total_issues": 0,
        "correction_suggestions": []
    },
    "technical_accuracy_review": {
        "status": "good",
        "score": 0.8,
        "accuracy_issues": [],
        "clarifications_needed": [],
        "consistency_check": {
            "is_consistent": true,
            "description": "技术问题与解决方案一致",
            "suggestion": null
        },
        "term_accuracy": {
            "issues": [],
            "accuracy_score": 0.85
        },
        "total_issues": 0
    },
    "style_consistency": {
        "overall_consistency": "good",
        "overall_score": 0.8,
        "style_checks": {
            "tense_consistency": {
                "score": 0.9,
                "issues": [],
                "description": "时态使用一致"
            },
            "terminology_consistency": {
                "score": 0.8,
                "consistent_terms_count": 25,
                "inconsistent_terms": []
            },
            "format_consistency": {
                "score": 0.85,
                "issues": [],
                "description": "格式一致"
            },
            "numbering_consistency": {
                "score": 0.75,
                "issues": [],
                "description": "编号一致"
            }
        },
        "issues": []
    },
    "quality_assessment": {
        "overall_score": 0.82,
        "overall_quality": "良好",
        "comparable_to": "高于平均水平",
        "dimensions": {
            "professionalism": {"score": 0.85, "level": "良好"},
            "accuracy": {"score": 0.8, "level": "良好"},
            "readability": {"score": 0.8, "level": "良好"}
        },
        "strengths": ["专业性: 良好", "准确性: 良好"],
        "weaknesses": [],
        "improvement_priority": []
    },
    "overall_score": 0.82,
    "overall_quality": "良好",
    "recommendations": ["撰写质量良好，建议保持"]
}
```"""

        with patch.object(writing_reviewer, '_call_llm_with_fallback', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response

            result = await writing_reviewer.review_writing(sample_application)

            # 验证LLM被调用
            mock_llm.assert_called_once()

            # 验证返回结果
            assert result["application_id"] == "CN202310000000.0"
            assert result["overall_quality"] == "良好"
            assert result["overall_score"] == 0.82
            assert "legal_terminology_review" in result
            assert "technical_accuracy_review" in result
            assert "style_consistency" in result
            assert "quality_assessment" in result

    @pytest.mark.asyncio
    async def test_review_writing_fallback_to_rules(self, writing_reviewer, sample_application):
        """测试LLM失败时降级到规则-based审查"""
        # Mock LLM抛出异常
        with patch.object(writing_reviewer, '_call_llm_with_fallback', new_callable=AsyncMock) as mock_llm:
            mock_llm.side_effect = Exception("LLM service unavailable")

            result = await writing_reviewer.review_writing(sample_application)

            # 验证降级到规则-based审查
            assert result["application_id"] == "CN202310000000.0"
            assert "legal_terminology_review" in result
            assert "technical_accuracy_review" in result
            assert "style_consistency" in result

    @pytest.mark.asyncio
    async def test_review_legal_terminology_with_llm(self, writing_reviewer, sample_application):
        """测试法律用语审查LLM调用"""
        mock_response = """```json
{
    "status": "good",
    "score": 0.85,
    "terminology_issues": [],
    "missing_standards": [],
    "consistency_check": {
        "score": 0.9,
        "consistent_terms_count": 25,
        "inconsistent_terms": []
    },
    "total_issues": 0,
    "correction_suggestions": []
}
```"""

        with patch.object(writing_reviewer, '_call_llm_with_fallback', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response

            result = await writing_reviewer.review_legal_terminology(sample_application)

            # 验证返回结果
            assert result["status"] == "good"
            assert result["score"] == 0.85
            assert result["total_issues"] == 0
            assert isinstance(result["terminology_issues"], list)

    @pytest.mark.asyncio
    async def test_review_technical_accuracy_with_llm(self, writing_reviewer, sample_application):
        """测试技术准确性审查LLM调用"""
        mock_response = """```json
{
    "status": "good",
    "score": 0.8,
    "accuracy_issues": [],
    "clarifications_needed": [],
    "consistency_check": {
        "is_consistent": true,
        "description": "技术问题与解决方案一致",
        "suggestion": null
    },
    "term_accuracy": {
        "issues": [],
        "accuracy_score": 0.85
    },
    "total_issues": 0
}
```"""

        with patch.object(writing_reviewer, '_call_llm_with_fallback', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response

            result = await writing_reviewer.review_technical_accuracy(sample_application)

            # 验证返回结果
            assert result["status"] == "good"
            assert result["score"] == 0.8
            assert result["total_issues"] == 0
            assert result["consistency_check"]["is_consistent"] is True

    @pytest.mark.asyncio
    async def test_check_style_consistency_with_llm(self, writing_reviewer, sample_application):
        """测试风格一致性检查LLM调用"""
        mock_response = """```json
{
    "overall_consistency": "good",
    "overall_score": 0.8,
    "style_checks": {
        "tense_consistency": {
            "score": 0.9,
            "issues": [],
            "description": "时态使用一致"
        },
        "terminology_consistency": {
            "score": 0.8,
            "consistent_terms_count": 25,
            "inconsistent_terms": []
        },
        "format_consistency": {
            "score": 0.85,
            "issues": [],
            "description": "格式一致"
        },
        "numbering_consistency": {
            "score": 0.75,
            "issues": [],
            "description": "编号一致"
        }
    },
    "issues": []
}
```"""

        with patch.object(writing_reviewer, '_call_llm_with_fallback', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response

            result = await writing_reviewer.check_writing_style_consistency(sample_application)

            # 验证返回结果
            assert result["overall_consistency"] == "good"
            assert result["overall_score"] == 0.8
            assert "style_checks" in result
            assert isinstance(result["issues"], list)


class TestPromptBuilding:
    """测试提示词构建"""

    def test_build_writing_review_prompt(self, writing_reviewer, sample_application):
        """测试撰写审查提示词构建"""
        prompt = writing_reviewer._build_writing_review_prompt(sample_application, "comprehensive")

        # 验证提示词包含关键信息
        assert "专利申请文件撰写质量审查" in prompt
        assert sample_application["application_id"] in prompt
        assert "法律用语规范性" in prompt
        assert "技术描述准确性" in prompt
        assert "撰写风格一致性" in prompt
        assert "撰写质量评估" in prompt
        assert "comprehensive" in prompt

    def test_build_legal_terminology_prompt(self, writing_reviewer, sample_application):
        """测试法律用语审查提示词构建"""
        prompt = writing_reviewer._build_legal_terminology_prompt(sample_application)

        # 验证提示词包含关键信息
        assert "专利申请文件法律用语规范性审查" in prompt
        assert sample_application["claims"] in prompt
        assert "禁用词汇检查" in prompt
        assert "标准法律用语" in prompt
        assert "专业术语一致性" in prompt

    def test_build_technical_accuracy_prompt(self, writing_reviewer, sample_application):
        """测试技术准确性审查提示词构建"""
        prompt = writing_reviewer._build_technical_accuracy_prompt(sample_application)

        # 验证提示词包含关键信息
        assert "专利申请文件技术描述准确性审查" in prompt
        assert sample_application["technical_problem"] in prompt
        assert sample_application["technical_solution"] in prompt
        assert "问题与解决方案一致性" in prompt
        assert "技术术语准确性" in prompt
        assert "有益效果合理性" in prompt

    def test_build_style_consistency_prompt(self, writing_reviewer, sample_application):
        """测试风格一致性检查提示词构建"""
        prompt = writing_reviewer._build_style_consistency_prompt(sample_application)

        # 验证提示词包含关键信息
        assert "专利申请文件撰写风格一致性检查" in prompt
        assert sample_application["claims"] in prompt
        assert "时态一致性" in prompt
        assert "术语一致性" in prompt
        assert "格式一致性" in prompt
        assert "编号一致性" in prompt


class TestResponseParsing:
    """测试响应解析"""

    def test_parse_writing_review_response_valid_json(self, writing_reviewer):
        """测试解析有效的撰写审查响应"""
        response = """```json
{
    "legal_terminology_review": {
        "status": "good",
        "score": 0.8,
        "total_issues": 0
    },
    "technical_accuracy_review": {
        "status": "good",
        "score": 0.8,
        "total_issues": 0
    },
    "style_consistency": {
        "overall_score": 0.8
    },
    "quality_assessment": {
        "overall_score": 0.8,
        "overall_quality": "良好"
    },
    "overall_score": 0.8,
    "overall_quality": "良好",
    "recommendations": []
}
```"""

        result = writing_reviewer._parse_writing_review_response(response)

        # 验证解析结果
        assert result["overall_score"] == 0.8
        assert result["overall_quality"] == "良好"
        assert "legal_terminology_review" in result
        assert "technical_accuracy_review" in result

    def test_parse_writing_review_response_invalid_json(self, writing_reviewer):
        """测试解析无效的撰写审查响应"""
        response = "Invalid JSON response"

        result = writing_reviewer._parse_writing_review_response(response)

        # 验证返回默认值
        assert result["overall_score"] == 0.0
        assert result["overall_quality"] == "待改进"
        assert any("LLM响应解析失败" in rec for rec in result["recommendations"])

    def test_parse_legal_terminology_response(self, writing_reviewer):
        """测试解析法律用语审查响应"""
        response = """```json
{
    "status": "good",
    "score": 0.85,
    "terminology_issues": [],
    "missing_standards": [],
    "consistency_check": {
        "score": 0.9,
        "consistent_terms_count": 25,
        "inconsistent_terms": []
    },
    "total_issues": 0,
    "correction_suggestions": []
}
```"""

        result = writing_reviewer._parse_legal_terminology_response(response)

        # 验证解析结果
        assert result["status"] == "good"
        assert result["score"] == 0.85
        assert result["total_issues"] == 0

    def test_parse_technical_accuracy_response(self, writing_reviewer):
        """测试解析技术准确性审查响应"""
        response = """```json
{
    "status": "good",
    "score": 0.8,
    "accuracy_issues": [],
    "clarifications_needed": [],
    "consistency_check": {
        "is_consistent": true,
        "description": "技术问题与解决方案一致",
        "suggestion": null
    },
    "term_accuracy": {
        "issues": [],
        "accuracy_score": 0.85
    },
    "total_issues": 0
}
```"""

        result = writing_reviewer._parse_technical_accuracy_response(response)

        # 验证解析结果
        assert result["status"] == "good"
        assert result["score"] == 0.8
        assert result["consistency_check"]["is_consistent"] is True

    def test_parse_style_consistency_response(self, writing_reviewer):
        """测试解析风格一致性检查响应"""
        response = """```json
{
    "overall_consistency": "good",
    "overall_score": 0.8,
    "style_checks": {
        "tense_consistency": {
            "score": 0.9,
            "issues": [],
            "description": "时态使用一致"
        }
    },
    "issues": []
}
```"""

        result = writing_reviewer._parse_style_consistency_response(response)

        # 验证解析结果
        assert result["overall_consistency"] == "good"
        assert result["overall_score"] == 0.8


class TestFallbackMechanism:
    """测试降级机制"""

    @pytest.mark.asyncio
    async def test_legal_terminology_fallback(self, writing_reviewer, sample_application):
        """测试法律用语审查降级机制"""
        # Mock LLM失败
        with patch.object(writing_reviewer, '_call_llm_with_fallback', new_callable=AsyncMock) as mock_llm:
            mock_llm.side_effect = Exception("LLM error")

            result = await writing_reviewer.review_legal_terminology(sample_application)

            # 验证降级到规则-based审查
            assert "status" in result
            assert "score" in result
            assert "total_issues" in result

    @pytest.mark.asyncio
    async def test_technical_accuracy_fallback(self, writing_reviewer, sample_application):
        """测试技术准确性审查降级机制"""
        # Mock LLM失败
        with patch.object(writing_reviewer, '_call_llm_with_fallback', new_callable=AsyncMock) as mock_llm:
            mock_llm.side_effect = Exception("LLM error")

            result = await writing_reviewer.review_technical_accuracy(sample_application)

            # 验证降级到规则-based审查
            assert "status" in result
            assert "score" in result
            assert "total_issues" in result

    @pytest.mark.asyncio
    async def test_style_consistency_fallback(self, writing_reviewer, sample_application):
        """测试风格一致性检查降级机制"""
        # Mock LLM失败
        with patch.object(writing_reviewer, '_call_llm_with_fallback', new_callable=AsyncMock) as mock_llm:
            mock_llm.side_effect = Exception("LLM error")

            result = await writing_reviewer.check_writing_style_consistency(sample_application)

            # 验证降级到规则-based检查
            assert "overall_score" in result
            assert "overall_consistency" in result


class TestEdgeCases:
    """测试边界条件"""

    @pytest.mark.asyncio
    async def test_empty_application_data(self, writing_reviewer):
        """测试空的申请文件数据"""
        empty_application = {
            "application_id": "EMPTY",
            "claims": "",
            "specification": ""
        }

        # Mock LLM返回默认响应
        mock_response = '{"overall_score": 0.0, "overall_quality": "待改进"}'

        with patch.object(writing_reviewer, '_call_llm_with_fallback', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response

            result = await writing_reviewer.review_writing(empty_application)

            # 验证不会崩溃，返回默认值
            assert result["application_id"] == "EMPTY"

    @pytest.mark.asyncio
    async def test_very_long_application_text(self, writing_reviewer, sample_application):
        """测试超长申请文件文本"""
        # 创建超长文本
        long_text = "这是一个很长的技术描述。" * 1000
        sample_application["specification"] = long_text

        # Mock LLM响应
        mock_response = '{"overall_score": 0.7, "overall_quality": "合格"}'

        with patch.object(writing_reviewer, '_call_llm_with_fallback', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response

            result = await writing_reviewer.review_writing(sample_application)

            # 验证能够处理长文本
            assert result["overall_quality"] == "合格"

    def test_build_prompt_with_missing_fields(self, writing_reviewer):
        """测试缺少字段时的提示词构建"""
        incomplete_application = {
            "application_id": "INCOMPLETE",
            "claims": "1. 一种方法。"
        }

        prompt = writing_reviewer._build_writing_review_prompt(incomplete_application, "quick")

        # 验证提示词仍能构建
        assert "专利申请文件撰写质量审查" in prompt
        assert "INCOMPLETE" in prompt


class TestQualityAssessment:
    """测试质量评估功能"""

    @pytest.mark.asyncio
    async def test_assess_writing_quality_excellent(self, writing_reviewer):
        """测试优秀质量评估"""
        legal_review = {"score": 0.95}
        technical_review = {"score": 0.9}
        style_review = {"overall_score": 0.92}

        result = await writing_reviewer.assess_writing_quality(
            legal_review,
            technical_review,
            style_review
        )

        # 验证评估结果
        assert result["overall_score"] >= 0.9
        assert result["overall_quality"] == "优秀"
        assert "comparable_to" in result

    @pytest.mark.asyncio
    async def test_assess_writing_quality_poor(self, writing_reviewer):
        """测试较差质量评估"""
        legal_review = {"score": 0.4}
        technical_review = {"score": 0.5}
        style_review = {"overall_score": 0.45}

        result = await writing_reviewer.assess_writing_quality(
            legal_review,
            technical_review,
            style_review
        )

        # 验证评估结果
        assert result["overall_score"] < 0.6
        assert result["overall_quality"] == "待改进"
        assert "improvement_priority" in result
