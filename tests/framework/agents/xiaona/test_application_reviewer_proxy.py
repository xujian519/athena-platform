"""
申请文件审查代理（ApplicationReviewerProxy）单元测试

测试内容：
1. 初始化测试
2. 能力注册测试
3. 系统提示词测试
4. 基本功能测试（使用mock）
"""

import pytest
from typing import Dict, List, Optional, Any


from core.framework.agents.xiaona.application_reviewer_proxy import ApplicationDocumentReviewerProxy
from core.framework.agents.xiaona.base_component import AgentExecutionContext


class TestApplicationReviewerInitialization:
    """申请文件审查代理初始化测试"""

    def test_application_reviewer_initialization(self):
        """测试申请文件审查代理初始化"""
        reviewer = ApplicationDocumentReviewerProxy()
        assert reviewer.agent_id == "application_reviewer"
        assert reviewer.status.value == "idle"


class TestApplicationReviewerCapabilities:
    """申请文件审查代理能力注册测试"""

    def test_application_reviewer_capabilities(self):
        """测试能力注册"""
        reviewer = ApplicationDocumentReviewerProxy()
        capabilities = reviewer.get_capabilities()
        capability_names = [c.name for c in capabilities]

        assert "format_review" in capability_names
        assert "disclosure_review" in capability_names
        assert "claims_review" in capability_names
        assert "specification_review" in capability_names

    def test_application_reviewer_capability_details(self):
        """测试能力详情"""
        reviewer = ApplicationDocumentReviewerProxy()
        capabilities = reviewer.get_capabilities()

        # 检查format_review能力
        format_review = next((c for c in capabilities if c.name == "format_review"), None)
        assert format_review is not None
        assert "格式规范审查" in format_review.description

    def test_application_reviewer_has_capability(self):
        """测试能力检查方法"""
        reviewer = ApplicationDocumentReviewerProxy()
        assert reviewer.has_capability("format_review")
        assert reviewer.has_capability("disclosure_review")
        assert not reviewer.has_capability("nonexistent_capability")


class TestApplicationReviewerSystemPrompt:
    """申请文件审查代理系统提示词测试"""

    def test_get_system_prompt(self):
        """测试获取系统提示词"""
        reviewer = ApplicationDocumentReviewerProxy()
        prompt = reviewer.get_system_prompt()

        assert "专利申请文件审查专家" in prompt
        assert "格式规范性" in prompt
        assert "技术披露" in prompt
        assert "权利要求书" in prompt
        assert "说明书" in prompt


class TestApplicationReviewerExecute:
    """申请文件审查代理基本功能测试"""

    @pytest.mark.asyncio
    async def test_execute_default_task(self):
        """测试默认任务执行（完整审查）"""
        reviewer = ApplicationDocumentReviewerProxy()

        context = AgentExecutionContext(
            session_id="test_session",
            task_id="test_task",
            input_data={
                "application_id": "APP123",
                "applicant": "测试申请人",
                "claims": "1. 一种测试装置...",
                "specification": "技术领域：本发明涉及..."
            },
            config={},
            metadata={}
        )

        result = await reviewer.execute(context)

        assert "application_id" in result
        assert "overall_score" in result
        assert "overall_quality" in result

    @pytest.mark.asyncio
    async def test_review_format(self):
        """测试格式审查"""
        reviewer = ApplicationDocumentReviewerProxy()

        application = {
            "documents": ["请求书", "说明书", "权利要求书"],
            "applicant_data": {
                "name": "测试申请人",
                "address": "测试地址",
                "nationality": "中国"
            }
        }

        result = await reviewer.review_format(application)

        assert "format_check" in result
        assert "required_documents" in result

    @pytest.mark.asyncio
    async def test_review_disclosure(self):
        """测试技术披露审查"""
        reviewer = ApplicationDocumentReviewerProxy()

        application = {
            "technical_field": "本发明涉及测试技术领域",
            "background_art": "现有技术存在...",
            "technical_problem": "现有技术存在问题...",
            "technical_solution": "本发明提供...",
            "beneficial_effects": "本发明具有..."
        }

        result = await reviewer.review_disclosure(application)

        assert "disclosure_adequacy" in result
        assert "disclosures" in result

    @pytest.mark.asyncio
    async def test_review_claims(self):
        """测试权利要求书审查"""
        reviewer = ApplicationDocumentReviewerProxy()

        application = {
            "claims": "1. 一种测试装置，包括特征A、特征B和特征C。\n2. 根据权利要求1所述的装置，其特征在于还包括特征D。",
            "specification": "说明书内容..."
        }

        result = await reviewer.review_claims(application)

        assert "claims_review" in result
        assert "total_claims" in result

    @pytest.mark.asyncio
    async def test_review_specification(self):
        """测试说明书审查"""
        reviewer = ApplicationDocumentReviewerProxy()

        application = {
            "specification": "技术领域：本发明涉及...\n\n背景技术：...\n\n发明内容：...",
            "embodiments": [
                {"description": "实施例1..."},
                {"description": "实施例2..."}
            ],
            "drawings": ["图1", "图2"]
        }

        result = await reviewer.review_specification(application)

        assert "specification_review" in result
        assert "total_embodiments" in result


class TestApplicationReviewerHelperMethods:
    """申请文件审查代理辅助方法测试"""

    def test_parse_claims(self):
        """测试解析权利要求"""
        reviewer = ApplicationDocumentReviewerProxy()

        claims_text = """1. 一种测试装置，包括特征A。
2. 根据权利要求1所述的装置，还包括特征B。
3. 根据权利要求2所述的装置，还包括特征C。"""

        claims = reviewer._parse_claims(claims_text)

        assert len(claims) == 3
        assert claims[0]["type"] == "independent"
        assert claims[1]["type"] == "dependent"

    def test_assess_disclosure_completeness(self):
        """测试评估披露充分性"""
        reviewer = ApplicationDocumentReviewerProxy()

        # 充分披露
        result1 = reviewer._assess_disclosure_completeness("技术领域", "这是一个详细的技术领域描述，超过100字的内容可以充分说明技术背景和范围。")
        assert result1["status"] == "sufficient"

        # 不充分披露
        result2 = reviewer._assess_disclosure_completeness("技术领域", "短")
        assert result2["status"] == "insufficient"

    def test_assess_claims_clarity(self):
        """测试评估权利要求清晰度"""
        reviewer = ApplicationDocumentReviewerProxy()

        claims_list = [
            {"text": "一种装置，包括特征A和特征B。"},  # 适中长度
            {"text": "一种装置，包括特征A。"}           # 太短
        ]

        result = reviewer._assess_claims_clarity(claims_list)

        assert "score" in result
        assert 0 <= result["score"] <= 1

    def test_assess_claims_support(self):
        """测试评估权利要求支持"""
        reviewer = ApplicationDocumentReviewerProxy()

        claims_list = [
            {"text": "一种装置，包括传感器和控制器。"}
        ]

        application = {
            "specification": "该装置包括传感器用于检测，控制器用于控制。"
        }

        result = reviewer._assess_claims_support(claims_list, application)

        assert "score" in result
        assert 0 <= result["score"] <= 1

    def test_assess_claims_breadth(self):
        """测试评估权利要求保护范围"""
        reviewer = ApplicationDocumentReviewerProxy()

        # 单个独立权利要求
        single_independent = [
            {"type": "independent", "text": "一种装置，包括特征A。"}
        ]

        result = reviewer._assess_claims_breadth(single_independent)

        assert "score" in result

    def test_assess_specification_completeness(self):
        """测试评估说明书完整性"""
        reviewer = ApplicationDocumentReviewerProxy()

        application = {
            "specification": "技术领域：...\n背景技术：...\n发明内容：...\n附图说明：...\n具体实施方式：..."
        }

        result = reviewer._assess_specification_completeness(application)

        assert "score" in result
        assert 0 <= result["score"] <= 1

    def test_assess_specification_clarity(self):
        """测试评估说明书清晰度"""
        reviewer = ApplicationDocumentReviewerProxy()

        # 结构化文本
        structured = "段落1\n\n段落2\n\n段落3\n\n段落4"
        result = reviewer._assess_specification_clarity(structured)

        assert result["score"] > 0.5

    def test_assess_enablement(self):
        """测试评估充分公开"""
        reviewer = ApplicationDocumentReviewerProxy()

        # 有实施方式
        embodiments = [{"description": "详细实施方式描述" * 50}]

        result = reviewer._assess_enablement("说明内容", embodiments)

        assert "score" in result

    def test_extract_keywords(self):
        """测试提取关键词"""
        reviewer = ApplicationDocumentReviewerProxy()

        text = "该装置包括传感器和控制器，用于实现自动化控制功能。"

        keywords = reviewer._extract_keywords(text)

        assert isinstance(keywords, list)

    def test_calculate_overall_score(self):
        """测试计算综合评分"""
        reviewer = ApplicationDocumentReviewerProxy()

        format_result = {"format_check": "passed", "completeness_ratio": 1.0}
        disclosure_result = {"completeness_score": 0.8}
        claims_result = {"claims_review": {"clarity": {"score": 0.75}}}
        specification_result = {"specification_review": {"completeness": {"score": 0.8}}}

        score = reviewer._calculate_overall_score(
            format_result, disclosure_result, claims_result, specification_result
        )

        assert 0 <= score <= 1

    def test_get_quality_level(self):
        """测试获取质量等级"""
        reviewer = ApplicationDocumentReviewerProxy()

        assert reviewer._get_quality_level(0.95) == "优秀"
        assert reviewer._get_quality_level(0.8) == "良好"
        assert reviewer._get_quality_level(0.65) == "合格"
        assert reviewer._get_quality_level(0.4) == "待改进"


class TestApplicationReviewerInfo:
    """申请文件审查代理信息测试"""

    def test_get_info(self):
        """测试获取代理信息"""
        reviewer = ApplicationDocumentReviewerProxy()
        info = reviewer.get_info()

        assert info["agent_id"] == "application_reviewer"
        assert info["agent_type"] == "ApplicationDocumentReviewerProxy"
        assert "capabilities" in info

    def test_repr(self):
        """测试代理字符串表示"""
        reviewer = ApplicationDocumentReviewerProxy()
        repr_str = repr(reviewer)

        assert "ApplicationDocumentReviewerProxy" in repr_str
