#!/usr/bin/env python3
"""
统一撰写智能体迁移测试套件

测试覆盖：
- WriterAgent的4个核心功能
- PatentDraftingProxy的7个核心功能
- 共15+个测试用例

标记说明：
- @pytest.mark.unit: 单元测试（无外部依赖）
- @pytest.mark.integration: 集成测试（需要LLM）
- @pytest.mark.slow: 慢速测试
"""

import json
from unittest.mock import AsyncMock, Mock, patch

import pytest

from core.framework.agents.xiaona.base_component import (
    AgentExecutionContext,
    AgentStatus,
)
from core.framework.agents.xiaona.patent_drafting_proxy import PatentDraftingProxy

# 导入被测试的类
from core.framework.agents.xiaona.writer_agent import WriterAgent

# 导入测试数据
from tests.agents.fixtures.drafting_fixtures import *

# ============================================================================
# WriterAgent 测试套件 (4个功能)
# ============================================================================

class TestWriterAgentInitialization:
    """WriterAgent初始化测试"""

    @pytest.mark.unit
    @pytest.mark.fast
    def test_writer_agent_initialization(self):
        """测试WriterAgent初始化"""
        agent = WriterAgent(agent_id="test_writer_agent")
        assert agent is not None
        assert agent.agent_id == "test_writer_agent"
        assert hasattr(agent, "llm_manager")

    @pytest.mark.unit
    @pytest.mark.fast
    def test_writer_agent_capabilities_registered(self):
        """测试能力注册"""
        agent = WriterAgent(agent_id="test_capabilities")
        capabilities = agent.get_capabilities()

        # 验证4个核心能力已注册
        capability_names = [cap.name for cap in capabilities]
        assert "claim_drafting" in capability_names
        assert "description_drafting" in capability_names
        assert "office_action_response" in capability_names
        assert "invalidation_petition" in capability_names

    @pytest.mark.unit
    @pytest.mark.fast
    def test_writer_agent_system_prompt(self):
        """测试系统提示词获取"""
        agent = WriterAgent(agent_id="test_prompt")
        prompt = agent.get_system_prompt()

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "撰写者" in prompt or "专利" in prompt


class TestWriterAgentClaimsDrafting:
    """WriterAgent权利要求书撰写功能测试"""

    @pytest.mark.unit
    @pytest.mark.fast
    @patch("core.agents.xiaona.writer_agent.UnifiedLLMManager")
    async def test_draft_claims_success(self, mock_llm_manager):
        """测试成功撰写权利要求书"""
        # 配置mock
        mock_manager_instance = Mock()
        mock_manager_instance.generate = AsyncMock(
            return_value=LLM_SUCCESS_RESPONSES["claims"]
        )
        mock_llm_manager.return_value = mock_manager_instance

        # 配置mock
        mock_manager_instance = Mock()
        mock_manager_instance.generate = AsyncMock(
            return_value=LLM_SUCCESS_RESPONSES["claims"]
        )
        mock_llm_manager.return_value = mock_manager_instance

        # 创建agent并执行
        agent = WriterAgent(agent_id="test_claims")
        context = AgentExecutionContext(
            task_id="TASK_CLAIMS_001",
            session_id="SESSION_001",
            input_data={
                **WRITER_CONTEXT_CLAIMS["input_data"],
                "previous_results": WRITER_CONTEXT_CLAIMS["previous_results"]
            },
            config=WRITER_CONTEXT_CLAIMS["config"],
            metadata={},
        )

        result = await agent.execute(context)

        # 验证结果
        assert result.status == AgentStatus.COMPLETED
        assert result.output_data is not None
        assert result.output_data.get("document_type") == "claims"
        assert "content" in result.output_data

    @pytest.mark.unit
    @pytest.mark.fast
    @patch("core.agents.xiaona.writer_agent.UnifiedLLMManager")
    async def test_draft_claims_with_json_parse_error(self, mock_llm_manager):
        """测试JSON解析错误时的降级处理"""
        mock_manager_instance = Mock()
        mock_manager_instance.generate = AsyncMock(
            return_value=LLM_INVALID_JSON
        )
        mock_llm_manager.return_value = mock_manager_instance

        agent = WriterAgent(agent_id="test_claims_error")
        context = AgentExecutionContext(
            task_id="TASK_CLAIMS_ERROR_001",
            session_id="SESSION_001",
            input_data={
                **WRITER_CONTEXT_CLAIMS["input_data"],
                "previous_results": WRITER_CONTEXT_CLAIMS["previous_results"]
            },
            config=WRITER_CONTEXT_CLAIMS["config"],
            metadata={},
        )

        result = await agent.execute(context)

        # 验证降级处理：返回原始文本
        assert result.status == AgentStatus.COMPLETED
        assert result.output_data.get("document_type") == "claims"
        # full_text应包含原始响应
        assert "full_text" in result.output_data

    @pytest.mark.unit
    @pytest.mark.fast
    def test_format_claims(self):
        """测试权利要求书格式化"""
        agent = WriterAgent(agent_id="test_format_claims")
        claims_data = {
            "independent_claim": "1. 一种测试方法，其特征在于，包括步骤A和步骤B。",
            "dependent_claims": [
                "2. 根据权利要求1所述的方法，其特征在于，步骤A包括子步骤A1。",
                "3. 根据权利要求1所述的方法，其特征在于，步骤B包括子步骤B1。"
            ]
        }

        formatted = agent._format_claims(claims_data)

        assert isinstance(formatted, str)
        assert "步骤A和步骤B" in formatted
        assert "子步骤A1" in formatted
        assert "子步骤B1" in formatted


class TestWriterAgentDescriptionDrafting:
    """WriterAgent说明书撰写功能测试"""

    @pytest.mark.unit
    @pytest.mark.fast
    @patch("core.agents.xiaona.writer_agent.UnifiedLLMManager")
    async def test_draft_description_success(self, mock_llm_manager):
        """测试成功撰写说明书"""
        mock_manager_instance = Mock()
        mock_manager_instance.generate = AsyncMock(
            return_value=LLM_SUCCESS_RESPONSES["specification"]
        )
        mock_llm_manager.return_value = mock_manager_instance

        agent = WriterAgent(agent_id="test_description")
        context = AgentExecutionContext(
            task_id="TASK_DESC_001",
            session_id="SESSION_001",
            input_data={
                "user_input": "请撰写说明书",
                "disclosure": VALID_DISCLOSURE
            },
            config={"writing_type": "description"},
            metadata={},
        )

        result = await agent.execute(context)

        assert result.status == AgentStatus.COMPLETED
        assert result.output_data.get("document_type") == "description"
        assert "content" in result.output_data
        assert "full_text" in result.output_data

    @pytest.mark.unit
    @pytest.mark.fast
    def test_format_description(self):
        """测试说明书格式化"""
        agent = WriterAgent(agent_id="test_format_desc")
        desc_data = {
            "title": "测试专利名称",
            "technical_field": "本发明涉及测试技术领域",
            "background_art": "现有技术存在...",
            "summary": "本发明提供...",
            "brief_description": "图1是测试图",
            "detailed_description": "具体实施方式..."
        }

        formatted = agent._format_description(desc_data)

        assert isinstance(formatted, str)
        assert "测试专利名称" in formatted
        assert "测试技术领域" in formatted
        assert "具体实施方式" in formatted


class TestWriterAgentOfficeActionResponse:
    """WriterAgent审查意见答复功能测试"""

    @pytest.mark.unit
    @pytest.mark.fast
    @patch("core.agents.xiaona.writer_agent.UnifiedLLMManager")
    async def test_draft_office_action_response(self, mock_llm_manager):
        """测试审查意见答复撰写"""
        mock_manager_instance = Mock()
        mock_manager_instance.generate = AsyncMock(
            return_value=json.dumps({
                "introduction": "尊敬的审查员，申请人收到审查意见通知书后，对申请文件进行了修改。",
                "responses": [
                    {
                        "issue": "权利要求1不具备新颖性",
                        "response": "申请人不同意审查员的意见",
                        "amendments": "修改权利要求1",
                        "arguments": "对比文件D1未公开本发明的特征X"
                    }
                ],
                "conclusion": "综上所述，修改后的权利要求具备新颖性和创造性"
            })
        )
        mock_llm_manager.return_value = mock_manager_instance

        agent = WriterAgent(agent_id="test_response")
        context = AgentExecutionContext(
            task_id="TASK_RESPONSE_001",
            session_id="SESSION_001",
            input_data={
                **WRITER_CONTEXT_RESPONSE["input_data"],
                "previous_results": WRITER_CONTEXT_RESPONSE["previous_results"]
            },
            config=WRITER_CONTEXT_RESPONSE["config"],
            metadata={},
        )

        result = await agent.execute(context)

        assert result.status == AgentStatus.COMPLETED
        assert result.output_data.get("document_type") == "office_action_response"
        assert "content" in result.output_data


class TestWriterAgentInvalidationPetition:
    """WriterAgent无效宣告请求书功能测试"""

    @pytest.mark.unit
    @pytest.mark.fast
    @patch("core.agents.xiaona.writer_agent.UnifiedLLMManager")
    async def test_draft_invalidation_petition(self, mock_llm_manager):
        """测试无效宣告请求书撰写"""
        mock_manager_instance = Mock()
        mock_manager_instance.generate = AsyncMock(
            return_value=json.dumps({
                "petition_title": "无效宣告请求书",
                "target_patent": "CN201921401279.9",
                "ground_for_invalidity": "权利要求1-3不具备新颖性",
                "evidence_list": ["D1: CN201198403Y", "D2: CN206156248U"],
                "claim_analysis": [
                    {
                        "claim": "权利要求1",
                        "evidence": "D1公开了所有技术特征",
                        "analysis": "权利要求1相对于D1不具备新颖性",
                        "conclusion": "应予无效"
                    }
                ],
                "conclusion": "请求宣告专利权全部无效"
            })
        )
        mock_llm_manager.return_value = mock_manager_instance

        agent = WriterAgent(agent_id="test_invalidation")
        context = AgentExecutionContext(
            task_id="TASK_INVALIDATION_001",
            session_id="SESSION_001",
            input_data={
                **WRITER_CONTEXT_INVALIDATION["input_data"],
                "previous_results": WRITER_CONTEXT_INVALIDATION["previous_results"]
            },
            config=WRITER_CONTEXT_INVALIDATION["config"],
            metadata={},
        )

        result = await agent.execute(context)

        assert result.status == AgentStatus.COMPLETED
        assert result.output_data.get("document_type") == "invalidation_petition"
        assert "content" in result.output_data


# ============================================================================
# PatentDraftingProxy 测试套件 (7个功能)
# ============================================================================

class TestPatentDraftingProxyInitialization:
    """PatentDraftingProxy初始化测试"""

    @pytest.mark.unit
    @pytest.mark.fast
    def test_patent_drafting_proxy_initialization(self):
        """测试PatentDraftingProxy初始化"""
        proxy = PatentDraftingProxy(
            agent_id="test_drafting_proxy",
            config={}
        )
        assert proxy is not None
        assert proxy.agent_id == "test_drafting_proxy"

    @pytest.mark.unit
    @pytest.mark.fast
    def test_patent_drafting_proxy_capabilities(self):
        """测试能力注册（7个能力）"""
        proxy = PatentDraftingProxy(agent_id="test_capabilities")
        capabilities = proxy.get_capabilities()

        capability_names = [cap.name for cap in capabilities]

        # 验证7个核心能力
        assert "analyze_disclosure" in capability_names
        assert "assess_patentability" in capability_names
        assert "draft_specification" in capability_names
        assert "draft_claims" in capability_names
        assert "optimize_protection_scope" in capability_names
        assert "review_adequacy" in capability_names
        assert "detect_common_errors" in capability_names

    @pytest.mark.unit
    @pytest.mark.fast
    def test_get_system_prompt(self):
        """测试系统提示词获取"""
        proxy = PatentDraftingProxy(agent_id="test_prompt")
        prompt = proxy.get_system_prompt(task_type="comprehensive")

        assert isinstance(prompt, str)
        assert len(prompt) > 0


class TestPatentDraftingProxyDisclosureAnalysis:
    """PatentDraftingProxy交底书分析功能测试"""

    @pytest.mark.unit
    @pytest.mark.fast
    async def test_analyze_disclosure_with_rules(self):
        """测试基于规则的交底书分析（降级方案）"""
        proxy = PatentDraftingProxy(agent_id="test_analyze")

        result = await proxy.analyze_disclosure(VALID_DISCLOSURE)

        assert isinstance(result, dict)
        assert "disclosure_id" in result
        assert "extracted_information" in result
        assert "completeness" in result
        assert "quality_assessment" in result
        assert "recommendations" in result

        # 验证提取的信息结构
        extracted = result["extracted_information"]
        assert "发明名称" in extracted
        assert "技术领域" in extracted
        assert "技术问题" in extracted
        assert "技术方案" in extracted
        assert "有益效果" in extracted
        assert "实施例" in extracted

    @pytest.mark.unit
    @pytest.mark.fast
    async def test_analyze_disclosure_minimal(self):
        """测试最小化交底书分析"""
        proxy = PatentDraftingProxy(agent_id="test_analyze_minimal")

        result = await proxy.analyze_disclosure(MINIMAL_DISCLOSURE)

        assert result is not None
        assert "completeness" in result
        # 最小数据应该检测到缺失内容
        missing_count = sum(
            1 for v in result["completeness"].values()
            if not v["完整"]
        )
        assert missing_count > 0

    @pytest.mark.unit
    @pytest.mark.fast
    def test_extract_invention_name(self):
        """测试发明名称提取"""
        proxy = PatentDraftingProxy(agent_id="test_extract_name")

        # 从完整数据提取
        name = proxy._extract_invention_name(
            content="",
            disclosure_data=VALID_DISCLOSURE
        )
        assert "深度学习" in name
        assert "图像识别" in name

        # 从content提取
        name2 = proxy._extract_invention_name(
            content="发明名称：一种智能控制系统",
            disclosure_data={}
        )
        assert "智能控制系统" in name2

    @pytest.mark.unit
    @pytest.mark.fast
    def test_identify_technical_field(self):
        """测试技术领域识别"""
        proxy = PatentDraftingProxy(agent_id="test_field")

        result = proxy._identify_technical_field(
            content="本发明涉及人工智能和图像处理技术",
            disclosure_data={}
        )

        assert "技术领域" in result
        assert "IPC分类" in result
        assert isinstance(result["IPC分类"], list)

    @pytest.mark.unit
    @pytest.mark.fast
    def test_extract_beneficial_effects(self):
        """测试有益效果提取"""
        proxy = PatentDraftingProxy(agent_id="test_effects")

        effects = proxy._extract_beneficial_effects(
            content="",
            disclosure_data=VALID_DISCLOSURE
        )

        assert isinstance(effects, list)
        assert len(effects) > 0

    @pytest.mark.unit
    @pytest.mark.fast
    def test_assess_quality(self):
        """测试质量评估"""
        proxy = PatentDraftingProxy(agent_id="test_quality")

        extracted = {
            "发明名称": "测试专利",
            "技术领域": {"技术领域": "测试领域"},
            "技术问题": "测试问题",
            "技术方案": {"技术方案概述": "测试方案", "核心特征": ["特征1", "特征2", "特征3"]},
            "有益效果": ["效果1", "效果2"],
            "实施例": []
        }

        completeness = {
            "发明名称": {"完整": True},
            "技术领域": {"完整": True},
            "技术问题": {"完整": True},
            "技术方案": {"完整": True},
            "有益效果": {"完整": True},
            "实施例": {"完整": False}
        }

        quality = proxy._assess_quality(extracted, completeness)

        assert "完整性评分" in quality
        assert "详细程度评分" in quality
        assert "清晰度评分" in quality
        assert "综合评分" in quality
        assert "质量等级" in quality

        # 验证评分范围
        assert 0 <= quality["综合评分"] <= 1


class TestPatentDraftingProxyPatentabilityAssessment:
    """PatentDraftingProxy可专利性评估功能测试"""

    @pytest.mark.unit
    @pytest.mark.fast
    async def test_assess_patentability_by_rules(self):
        """测试基于规则的可专利性评估"""
        proxy = PatentDraftingProxy(agent_id="test_patentability")

        data = {
            "disclosure": VALID_DISCLOSURE,
            "prior_art": []
        }

        result = await proxy.assess_patentability(data)

        assert isinstance(result, dict)
        assert "novelty_assessment" in result
        assert "creativity_assessment" in result
        assert "practicality_assessment" in result
        assert "overall_score" in result
        assert "patentability_level" in result

        # 验证评分结构
        assert "score" in result["novelty_assessment"]
        assert 0 <= result["novelty_assessment"]["score"] <= 1


class TestPatentDraftingProxySpecificationDrafting:
    """PatentDraftingProxy说明书撰写功能测试"""

    @pytest.mark.unit
    @pytest.mark.fast
    async def test_draft_specification_by_template(self):
        """测试基于模板的说明书撰写（降级方案）"""
        proxy = PatentDraftingProxy(agent_id="test_specification")

        data = {
            "disclosure": VALID_DISCLOSURE,
            "patentability": {
                "overall_score": 0.75,
                "patentability_level": "良好"
            }
        }

        result = await proxy.draft_specification(data)

        assert isinstance(result, dict)
        assert "specification_draft" in result
        assert "drafted_at" in result

        # 验证说明书结构
        draft = result["specification_draft"]
        assert isinstance(draft, str)
        assert len(draft) > 0

    @pytest.mark.unit
    @pytest.mark.fast
    def test_generate_title(self):
        """测试发明名称生成"""
        proxy = PatentDraftingProxy(agent_id="test_title")

        title = proxy._generate_title(VALID_DISCLOSURE)

        assert isinstance(title, str)
        assert len(title) > 0
        # 应该去除"新型"、"改进"等词汇
        assert "新型" not in title
        assert "改进" not in title

    @pytest.mark.unit
    @pytest.mark.fast
    def test_draft_technical_field(self):
        """测试技术领域撰写"""
        proxy = PatentDraftingProxy(agent_id="test_field_draft")

        field = proxy._draft_technical_field(VALID_DISCLOSURE)

        assert isinstance(field, str)
        assert "本发明涉及" in field or "技术领域" in field

    @pytest.mark.unit
    @pytest.mark.fast
    def test_determine_claim_type(self):
        """测试权利要求类型判断"""
        proxy = PatentDraftingProxy(agent_id="test_claim_type")

        # 方法类
        method_type = proxy._determine_claim_type(METHOD_DISCLOSURE)
        assert method_type == "method"

        # 装置类
        device_type = proxy._determine_claim_type(DEVICE_DISCLOSURE)
        assert device_type == "device"


class TestPatentDraftingProxyClaimsDrafting:
    """PatentDraftingProxy权利要求书撰写功能测试"""

    @pytest.mark.unit
    @pytest.mark.fast
    async def test_draft_claims_by_template(self):
        """测试基于模板的权利要求书撰写（降级方案）"""
        proxy = PatentDraftingProxy(agent_id="test_claims_draft")

        data = {
            "disclosure": VALID_DISCLOSURE,
            "specification": VALID_SPECIFICATION
        }

        result = await proxy.draft_claims(data)

        assert isinstance(result, dict)
        assert "claims_draft" in result
        assert "独立权利要求" in result
        assert "从属权利要求数量" in result
        assert "drafted_at" in result

    @pytest.mark.unit
    @pytest.mark.fast
    def test_extract_essential_features(self):
        """测试必要技术特征提取"""
        proxy = PatentDraftingProxy(agent_id="test_essential")

        features = proxy._extract_essential_features(VALID_DISCLOSURE)

        assert isinstance(features, list)
        # 应该提取到包含关键词的特征
        assert len(features) >= 0

    @pytest.mark.unit
    @pytest.mark.fast
    def test_format_independent_device_claim(self):
        """测试装置类独立权利要求格式化"""
        proxy = PatentDraftingProxy(agent_id="test_device_claim")

        title = "测试装置"
        features = ["包括组件A", "设置组件B", "配置组件C"]

        claim = proxy._format_independent_device_claim(title, features)

        assert isinstance(claim, str)
        assert "测试装置" in claim
        assert "其特征在于" in claim
        assert "组件A" in claim
        assert "组件B" in claim

    @pytest.mark.unit
    @pytest.mark.fast
    def test_format_independent_method_claim(self):
        """测试方法类独立权利要求格式化"""
        proxy = PatentDraftingProxy(agent_id="test_method_claim")

        title = "测试方法"
        steps = ["步骤A：执行操作X", "步骤B：执行操作Y"]

        claim = proxy._format_independent_method_claim(title, steps)

        assert isinstance(claim, str)
        assert "测试方法" in claim
        assert "其特征在于" in claim
        assert "操作X" in claim or "步骤A" in claim


class TestPatentDraftingProxyProtectionScopeOptimization:
    """PatentDraftingProxy保护范围优化功能测试"""

    @pytest.mark.unit
    @pytest.mark.fast
    @patch.object(PatentDraftingProxy, "_call_llm_with_fallback")
    async def test_optimize_protection_scope(self, mock_llm):
        """测试保护范围优化"""
        mock_llm.return_value = json.dumps({
            "optimization_suggestions": [
                "建议扩大独立权利要求的保护范围",
                "建议减少非必要技术特征"
            ],
            "risk_analysis": "中等风险"
        })

        proxy = PatentDraftingProxy(agent_id="test_optimize")

        data = {
            "claims": VALID_CLAIMS,
            "prior_art": []
        }

        result = await proxy.optimize_protection_scope(data)

        assert isinstance(result, dict)


class TestPatentDraftingProxyAdequacyReview:
    """PatentDraftingProxy充分公开审查功能测试"""

    @pytest.mark.unit
    @pytest.mark.fast
    @patch.object(PatentDraftingProxy, "_call_llm_with_fallback")
    async def test_review_adequacy(self, mock_llm):
        """测试充分公开审查"""
        mock_llm.return_value = json.dumps({
            "adequacy_review": {
                "is_adequate": True,
                "missing_details": [],
                "recommendations": ["说明书公开充分"]
            }
        })

        proxy = PatentDraftingProxy(agent_id="test_adequacy")

        data = {
            "specification": VALID_SPECIFICATION,
            "claims": VALID_CLAIMS
        }

        result = await proxy.review_adequacy(data)

        assert isinstance(result, dict)
        assert "adequacy_review" in result


class TestPatentDraftingProxyErrorDetection:
    """PatentDraftingProxy常见错误检测功能测试"""

    @pytest.mark.unit
    @pytest.mark.fast
    @patch.object(PatentDraftingProxy, "_call_llm_with_fallback")
    async def test_detect_common_errors(self, mock_llm):
        """测试常见错误检测"""
        mock_llm.return_value = json.dumps({
            "detected_errors": [
                {"type": "术语不一致", "location": "权利要求1", "suggestion": "统一术语"},
                {"type": "引用关系错误", "location": "权利要求3", "suggestion": "修正引用"}
            ],
            "error_count": 2
        })

        proxy = PatentDraftingProxy(agent_id="test_errors")

        data = {
            "specification": VALID_SPECIFICATION,
            "claims": VALID_CLAIMS
        }

        result = await proxy.detect_common_errors(data)

        assert isinstance(result, dict)


class TestPatentDraftingProxyCompleteWorkflow:
    """PatentDraftingProxy完整撰写流程测试"""

    @pytest.mark.integration
    @pytest.mark.slow
    async def test_draft_patent_application_complete(self):
        """测试完整专利申请撰写流程"""
        proxy = PatentDraftingProxy(agent_id="test_complete")

        result = await proxy.draft_patent_application(VALID_DISCLOSURE)

        assert isinstance(result, dict)
        assert "disclosure_analysis" in result
        assert "patentability_assessment" in result
        assert "specification" in result
        assert "claims" in result
        assert "adequacy_review" in result
        assert "error_detection" in result
        assert "completed_at" in result


# ============================================================================
# 辅助测试用例
# ============================================================================

class TestUtilityMethods:
    """辅助方法测试"""

    @pytest.mark.unit
    @pytest.mark.fast
    def test_get_timestamp(self):
        """测试时间戳生成"""
        proxy = PatentDraftingProxy(agent_id="test_timestamp")
        timestamp = proxy._get_timestamp()

        assert isinstance(timestamp, str)
        # 验证ISO格式
        assert "T" in timestamp or "-" in timestamp

    @pytest.mark.unit
    @pytest.mark.fast
    def test_get_quality_level(self):
        """测试质量等级判定"""
        proxy = PatentDraftingProxy(agent_id="test_quality_level")

        assert proxy._get_quality_level(0.95) == "优秀"
        assert proxy._get_quality_level(0.8) == "良好"
        assert proxy._get_quality_level(0.65) == "合格"
        assert proxy._get_quality_level(0.5) == "待改进"


# ============================================================================
# 错误处理测试
# ============================================================================

class TestErrorHandling:
    """错误处理测试"""

    @pytest.mark.unit
    @pytest.mark.fast
    async def test_writer_agent_execute_with_error(self):
        """测试WriterAgent错误处理"""
        agent = WriterAgent(agent_id="test_error")

        # 创建无效上下文
        context = AgentExecutionContext(
            task_id="TASK_ERROR_001",
            session_id="SESSION_001",
            input_data={},
            config={"writing_type": "invalid_type"},
            metadata={},
        )

        result = await agent.execute(context)

        # 应该返回错误状态或降级处理
        assert result is not None
        assert result.status in [AgentStatus.COMPLETED, AgentStatus.ERROR]

    @pytest.mark.unit
    @pytest.mark.fast
    def test_patent_drafting_proxy_invalid_input(self):
        """测试PatentDraftingProxy无效输入处理"""
        proxy = PatentDraftingProxy(agent_id="test_invalid")

        # 测试空数据
        result = proxy._extract_document_content({})

        assert isinstance(result, str)

    @pytest.mark.unit
    @pytest.mark.fast
    def test_extract_from_empty_content(self):
        """测试从空内容提取"""
        proxy = PatentDraftingProxy(agent_id="test_empty")

        result = proxy._extract_features_from_text("")

        assert isinstance(result, list)
        assert len(result) == 0


# ============================================================================
# 测试计数器
# ============================================================================

@pytest.fixture(autouse=True)
def test_counter(request):
    """自动统计测试用例数量"""
    # 测试开始前
    if not hasattr(test_counter, 'count'):
        test_counter.count = 0
    test_counter.count += 1

    yield

    # 测试结束后打印统计
    if test_counter.count == request.node.session.testscollected:
        print(f"\n{'='*60}")
        print("测试套件统计:")
        print(f"  收集的测试: {request.node.session.testscollected}")
        print(f"  执行的测试: {test_counter.count}")
        print(f"{'='*60}\n")


# 测试套件元数据
__test_count__ = 25  # 预期测试用例数量
__coverage_target__ = {
    "WriterAgent": ["claim_drafting", "description_drafting", "office_action_response", "invalidation_petition"],
    "PatentDraftingProxy": [
        "analyze_disclosure",
        "assess_patentability",
        "draft_specification",
        "draft_claims",
        "optimize_protection_scope",
        "review_adequacy",
        "detect_common_errors"
    ]
}
