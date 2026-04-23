"""
ApplicationReviewerProxy LLM集成测试

测试申请文件审查智能体的LLM调用功能。
"""

from unittest.mock import AsyncMock

import pytest

from core.framework.agents.xiaona.application_reviewer_proxy import ApplicationDocumentReviewerProxy


@pytest.fixture
def reviewer():
    """创建审查智能体实例"""
    return ApplicationDocumentReviewerProxy(
        agent_id="test_application_reviewer",
        config={"llm_config": {"model": "claude-3-5-sonnet-20241022"}}
    )


@pytest.fixture
def sample_application():
    """示例申请文件数据"""
    return {
        "application_id": "CN202310000000.0",
        "applicant": "测试申请人",
        "documents": ["请求书", "说明书", "权利要求书", "摘要"],
        "applicant_data": {
            "name": "张三",
            "address": "北京市海淀区",
            "nationality": "中国"
        },
        "technical_field": "本发明涉及人工智能技术领域，具体涉及一种自动驾驶方法。",
        "background_art": "现有技术中，自动驾驶方法存在安全性不足的问题。",
        "technical_problem": "本发明要解决的技术问题是提高自动驾驶的安全性。",
        "technical_solution": "本发明提供一种自动驾驶方法，包括以下步骤：获取环境数据；分析环境数据；做出驾驶决策。",
        "beneficial_effects": "本发明能够显著提高自动驾驶的安全性。",
        "claims": "1. 一种自动驾驶方法，其特征在于，包括：获取环境数据；分析所述环境数据；做出驾驶决策。\n2. 根据权利要求1所述的方法，其特征在于，所述环境数据包括图像数据。",
        "specification": "技术领域\n本发明涉及人工智能技术领域。\n\n背景技术\n现有技术存在不足。\n\n发明内容\n本发明提供一种自动驾驶方法。\n\n具体实施方式\n下面结合附图对本发明作进一步说明。",
        "embodiments": [
            "实施例1：系统包括摄像头、处理器和控制器。",
            "实施例2：系统还包括激光雷达。"
        ],
        "drawings": ["图1", "图2"]
    }


class TestFormatReviewWithLLM:
    """测试格式审查（LLM版本）"""

    @pytest.mark.asyncio
    async def test_format_review_with_llm_success(self, reviewer, sample_application):
        """测试LLM格式审查成功"""
        # Mock LLM响应
        mock_response = """```json
{
    "format_check": "passed",
    "required_documents": ["请求书", "说明书", "权利要求书", "摘要"],
    "provided_documents": ["请求书", "说明书", "权利要求书", "摘要"],
    "missing_documents": [],
    "applicant_data": {
        "status": "complete",
        "info": {
            "name": "张三",
            "address": "北京市海淀区",
            "nationality": "中国"
        }
    },
    "format_issues": [],
    "completeness_ratio": 1.0
}
```"""

        # Mock LLM调用
        reviewer._call_llm_with_fallback = AsyncMock(return_value=mock_response)

        # 执行审查
        result = await reviewer.review_format(sample_application)

        # 验证结果
        assert result["format_check"] == "passed"
        assert result["completeness_ratio"] == 1.0
        assert len(result["missing_documents"]) == 0
        assert result["applicant_data"]["status"] == "complete"

    @pytest.mark.asyncio
    async def test_format_review_fallback_to_rules(self, reviewer, sample_application):
        """测试LLM失败时降级到规则审查"""
        # Mock LLM调用失败
        reviewer._call_llm_with_fallback = AsyncMock(side_effect=Exception("LLM error"))

        # 执行审查（应该降级到规则）
        result = await reviewer.review_format(sample_application)

        # 验证降级方案结果
        assert "format_check" in result
        assert "completeness_ratio" in result
        assert "required_documents" in result


class TestDisclosureReviewWithLLM:
    """测试披露审查（LLM版本）"""

    @pytest.mark.asyncio
    async def test_disclosure_review_with_llm_success(self, reviewer, sample_application):
        """测试LLM披露审查成功"""
        # Mock LLM响应
        mock_response = """```json
{
    "disclosure_adequacy": "sufficient",
    "disclosures": {
        "technical_field": {"status": "sufficient", "score": 0.9, "description": "技术领域披露充分"},
        "background_art": {"status": "sufficient", "score": 0.8, "description": "背景技术披露充分"},
        "technical_problem": {"status": "sufficient", "score": 0.9, "description": "技术问题披露充分"},
        "technical_solution": {"status": "sufficient", "score": 0.85, "description": "技术方案披露充分"},
        "beneficial_effects": {"status": "sufficient", "score": 0.8, "description": "有益效果披露充分"}
    },
    "missing_disclosures": [],
    "completeness_score": 0.85
}
```"""

        # Mock LLM调用
        reviewer._call_llm_with_fallback = AsyncMock(return_value=mock_response)

        # 执行审查
        result = await reviewer.review_disclosure(sample_application)

        # 验证结果
        assert result["disclosure_adequacy"] == "sufficient"
        assert result["completeness_score"] == 0.85
        assert len(result["missing_disclosures"]) == 0
        assert "technical_field" in result["disclosures"]


class TestClaimsReviewWithLLM:
    """测试权利要求审查（LLM版本）"""

    @pytest.mark.asyncio
    async def test_claims_review_with_llm_success(self, reviewer, sample_application):
        """测试LLM权利要求审查成功"""
        # Mock LLM响应
        mock_response = """```json
{
    "claims_review": {
        "clarity": {"score": 0.85, "description": "权利要求表述清晰"},
        "support": {"score": 0.8, "description": "权利要求得到说明书支持"},
        "breadth": {"score": 0.75, "description": "保护范围合理"},
        "dependency": {"score": 0.9, "description": "依赖关系正确"}
    },
    "total_claims": 2,
    "independent_claims": 1,
    "dependent_claims": 1,
    "issues": [],
    "suggestions": ["权利要求质量良好"]
}
```"""

        # Mock LLM调用
        reviewer._call_llm_with_fallback = AsyncMock(return_value=mock_response)

        # 执行审查
        result = await reviewer.review_claims(sample_application)

        # 验证结果
        assert result["total_claims"] == 2
        assert result["independent_claims"] == 1
        assert result["dependent_claims"] == 1
        assert "claims_review" in result
        assert result["claims_review"]["clarity"]["score"] == 0.85


class TestSpecificationReviewWithLLM:
    """测试说明书审查（LLM版本）"""

    @pytest.mark.asyncio
    async def test_specification_review_with_llm_success(self, reviewer, sample_application):
        """测试LLM说明书审查成功"""
        # Mock LLM响应
        mock_response = """```json
{
    "specification_review": {
        "completeness": {"score": 0.8, "description": "说明书包含主要部分"},
        "clarity": {"score": 0.75, "description": "说明书表述清晰"},
        "enablement": {"score": 0.85, "description": "充分公开充分"},
        "best_mode": {"score": 0.7, "description": "最佳实施方式已披露"},
        "drawings_support": {"score": 0.8, "description": "附图支持充分"}
    },
    "total_embodiments": 2,
    "total_drawings": 2,
    "issues": [],
    "suggestions": ["说明书质量良好"]
}
```"""

        # Mock LLM调用
        reviewer._call_llm_with_fallback = AsyncMock(return_value=mock_response)

        # 执行审查
        result = await reviewer.review_specification(sample_application)

        # 验证结果
        assert result["total_embodiments"] == 2
        assert result["total_drawings"] == 2
        assert "specification_review" in result
        assert result["specification_review"]["completeness"]["score"] == 0.8


class TestComprehensiveReview:
    """测试完整审查流程"""

    @pytest.mark.asyncio
    async def test_comprehensive_review_with_llm(self, reviewer, sample_application):
        """测试完整审查流程（LLM版本）"""
        # Mock所有LLM调用
        format_response = """```json
{
    "format_check": "passed",
    "required_documents": ["请求书", "说明书", "权利要求书", "摘要"],
    "provided_documents": ["请求书", "说明书", "权利要求书", "摘要"],
    "missing_documents": [],
    "applicant_data": {"status": "complete", "info": {"name": "张三", "address": "北京市海淀区", "nationality": "中国"}},
    "format_issues": [],
    "completeness_ratio": 1.0
}
```"""

        disclosure_response = """```json
{
    "disclosure_adequacy": "sufficient",
    "disclosures": {},
    "missing_disclosures": [],
    "completeness_score": 0.85
}
```"""

        claims_response = """```json
{
    "claims_review": {},
    "total_claims": 2,
    "independent_claims": 1,
    "dependent_claims": 1,
    "issues": [],
    "suggestions": []
}
```"""

        specification_response = """```json
{
    "specification_review": {},
    "total_embodiments": 2,
    "total_drawings": 2,
    "issues": [],
    "suggestions": []
}
```"""

        # Mock LLM调用
        reviewer._call_llm_with_fallback = AsyncMock(
            side_effect=[
                format_response,
                disclosure_response,
                claims_response,
                specification_response
            ]
        )

        # 执行完整审查
        result = await reviewer.review_application(sample_application)

        # 验证结果
        assert "format_review" in result
        assert "disclosure_review" in result
        assert "claims_review" in result
        assert "specification_review" in result
        assert "overall_score" in result
        assert "overall_quality" in result
        assert "recommendations" in result


class TestPromptBuilding:
    """测试提示词构建"""

    def test_build_format_review_prompt(self, reviewer, sample_application):
        """测试格式审查提示词构建"""
        prompt = reviewer._build_format_review_prompt(sample_application)

        assert "# 任务：专利申请文件格式审查" in prompt
        assert "CN202310000000.0" in prompt
        assert "张三" in prompt
        assert "```json" in prompt

    def test_build_disclosure_review_prompt(self, reviewer, sample_application):
        """测试披露审查提示词构建"""
        prompt = reviewer._build_disclosure_review_prompt(sample_application)

        assert "# 任务：专利申请文件技术披露充分性审查" in prompt
        assert "技术领域" in prompt
        assert "背景技术" in prompt
        assert "技术方案" in prompt

    def test_build_claims_review_prompt(self, reviewer, sample_application):
        """测试权利要求审查提示词构建"""
        prompt = reviewer._build_claims_review_prompt(sample_application)

        assert "# 任务：专利权利要求书审查" in prompt
        assert "自动驾驶方法" in prompt
        assert "环境数据" in prompt

    def test_build_specification_review_prompt(self, reviewer, sample_application):
        """测试说明书审查提示词构建"""
        prompt = reviewer._build_specification_review_prompt(sample_application)

        assert "# 任务：专利说明书审查" in prompt
        assert "技术领域" in prompt
        assert "具体实施方式" in prompt


class TestResponseParsing:
    """测试响应解析"""

    def test_parse_format_review_response_success(self, reviewer):
        """测试成功解析格式审查响应"""
        response = """```json
{
    "format_check": "passed",
    "completeness_ratio": 1.0
}
```"""

        result = reviewer._parse_format_review_response(response)

        assert result["format_check"] == "passed"
        assert result["completeness_ratio"] == 1.0

    def test_parse_format_review_response_invalid_json(self, reviewer):
        """测试解析无效JSON"""
        response = "This is not a valid JSON"

        result = reviewer._parse_format_review_response(response)

        # 应该返回默认值
        assert result["format_check"] == "failed"
        assert "LLM响应解析失败" in result["format_issues"]

    def test_parse_disclosure_review_response_success(self, reviewer):
        """测试成功解析披露审查响应"""
        response = """```json
{
    "disclosure_adequacy": "sufficient",
    "completeness_score": 0.85
}
```"""

        result = reviewer._parse_disclosure_review_response(response)

        assert result["disclosure_adequacy"] == "sufficient"
        assert result["completeness_score"] == 0.85


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
