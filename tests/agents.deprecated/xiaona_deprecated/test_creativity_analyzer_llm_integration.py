"""
CreativityAnalyzerProxy LLM集成测试

测试创造性分析智能体的LLM调用功能。
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from core.agents.xiaona.creativity_analyzer_proxy import CreativityAnalyzerProxy


@pytest.fixture
def analyzer():
    """创建创造性分析智能体实例"""
    return CreativityAnalyzerProxy(
        agent_id="test_creativity_analyzer",
        config={"llm_config": {"model": "claude-3-5-sonnet-20241022"}}
    )


@pytest.fixture
def sample_patent():
    """示例专利数据"""
    return {
        "patent_id": "CN123456789A",
        "title": "一种基于深度学习的自动驾驶方法",
        "technical_field": "人工智能",
        "invention_content": "本发明采用多模态融合深度学习模型，结合视觉、激光雷达和毫米波雷达数据进行环境感知，通过自适应权重调整机制优化感知效果，采用端到端学习框架实现从感知到决策的一体化处理。",
        "technical_problem": "现有自动驾驶技术在复杂环境下感知准确率低，鲁棒性不足",
        "beneficial_effects": "本发明能够显著提高感知准确率30%，降低误报率50%，在恶劣天气条件下仍能保持高可靠性，解决了长期未解决的技术难题。",
        "prior_art": [
            {
                "publication_number": "CN101234567A",
                "title": "一种车载视觉感知方法",
                "content": "采用单目摄像头进行环境感知，准确率75%"
            },
            {
                "publication_number": "US9876543B2",
                "title": "激光雷达点云处理方法",
                "content": "使用激光雷达进行3D目标检测"
            }
        ],
        "differences": [
            "多模态融合架构：结合视觉、激光雷达和毫米波雷达",
            "自适应权重调整机制：根据环境条件动态调整各模态权重",
            "端到端学习框架：从原始数据到决策的端到端学习"
        ]
    }


@pytest.fixture
def sample_patent_low_creativity():
    """示例低创造性专利数据"""
    return {
        "patent_id": "CN987654321A",
        "title": "一种水杯",
        "technical_field": "日常用品",
        "invention_content": "水杯包括杯体和杯盖，杯盖上设有出水口，杯体采用红色塑料制成。",
        "technical_problem": "无",
        "beneficial_effects": "方便用户饮水",
        "prior_art": [
            {
                "publication_number": "CN201234567U",
                "title": "水杯",
                "content": "一种普通水杯，包括杯体和杯盖"
            }
        ],
        "differences": [
            "杯盖颜色不同"
        ]
    }


class TestObviousnessAssessmentWithLLM:
    """测试显而易见性评估（LLM版本）"""

    @pytest.mark.asyncio
    async def test_obviousness_assessment_with_llm_success(self, analyzer, sample_patent):
        """测试LLM显而易见性评估成功"""
        # Mock LLM响应
        mock_response = """```json
{
    "is_obvious": false,
    "confidence": 0.85,
    "reasoning": "本发明采用多模态融合架构，结合视觉、激光雷达和毫米波雷达数据，这种组合方式在现有技术中未被明确教导。自适应权重调整机制和端到端学习框架带来了预料不到的技术效果（感知准确率提高30%，误报率降低50%）。",
    "key_factors": [
        "现有技术未明确教导多模态融合",
        "带来预料不到的技术效果",
        "技术方案非显而易见的组合"
    ],
    "closest_prior_art": "CN101234567A",
    "distinguishing_features": ["多模态融合架构", "自适应权重调整机制", "端到端学习框架"],
    "technical_problem": "复杂环境下感知准确率低",
    "obviousness_conclusion": "非显而易见"
}
```"""

        # Mock LLM调用
        analyzer._call_llm_with_fallback = AsyncMock(return_value=mock_response)

        # 执行评估
        result = await analyzer.assess_obviousness(sample_patent)

        # 验证结果
        assert result["is_obvious"] == False
        assert result["confidence"] == 0.85
        assert "reasoning" in result
        assert "key_factors" in result
        assert len(result["distinguishing_features"]) == 3

    @pytest.mark.asyncio
    async def test_obviousness_assessment_fallback_to_rules(self, analyzer, sample_patent):
        """测试LLM失败时降级到规则评估"""
        # Mock LLM调用失败
        analyzer._call_llm_with_fallback = AsyncMock(side_effect=Exception("LLM error"))

        # 执行评估（应该降级到规则）
        result = await analyzer.assess_obviousness(sample_patent)

        # 验证降级方案结果
        assert "is_obvious" in result
        assert "confidence" in result
        assert "reasoning" in result


class TestInventiveStepEvaluationWithLLM:
    """测试创造性步骤评估（LLM版本）"""

    @pytest.mark.asyncio
    async def test_inventive_step_evaluation_with_llm_success(self, analyzer, sample_patent):
        """测试LLM创造性步骤评估成功"""
        # Mock LLM响应
        mock_response = """```json
{
    "has_inventive_step": true,
    "step_magnitude": "significant",
    "confidence": 0.9,
    "reasoning": "本发明在自动驾驶感知领域提出了创新的多模态融合架构和自适应权重调整机制，技术方案具有重大创新，非显而易见。",
    "evidence": [
        "多模态融合架构在自动驾驶领域的创新应用",
        "自适应权重调整机制解决了长期未解决的技术难题",
        "端到端学习框架突破了传统分步处理的局限"
    ],
    "technical_difficulty": "high",
    "innovation_level": "breakthrough",
    "contribution_to_field": "对自动驾驶感知技术领域做出了重大贡献，显著提高了感知准确率和鲁棒性"
}
```"""

        # Mock LLM调用
        analyzer._call_llm_with_fallback = AsyncMock(return_value=mock_response)

        # 执行评估
        result = await analyzer.evaluate_inventive_step(sample_patent)

        # 验证结果
        assert result["has_inventive_step"] == True
        assert result["step_magnitude"] == "significant"
        assert result["confidence"] == 0.9
        assert len(result["evidence"]) == 3
        assert result["technical_difficulty"] == "high"
        assert result["innovation_level"] == "breakthrough"

    @pytest.mark.asyncio
    async def test_inventive_step_evaluation_low_creativity(self, analyzer, sample_patent_low_creativity):
        """测试低创造性专利的创造性步骤评估"""
        # Mock LLM响应
        mock_response = """```json
{
    "has_inventive_step": false,
    "step_magnitude": "none",
    "confidence": 0.8,
    "reasoning": "该专利仅改变了杯盖的颜色，属于常规设计变更，技术方案显而易见，无实质性创新。",
    "evidence": [
        "颜色改变是常规设计手段",
        "未解决任何技术问题",
        "无技术效果提升"
    ],
    "technical_difficulty": "low",
    "innovation_level": "routine",
    "contribution_to_field": "对技术领域无贡献"
}
```"""

        # Mock LLM调用
        analyzer._call_llm_with_fallback = AsyncMock(return_value=mock_response)

        # 执行评估
        result = await analyzer.evaluate_inventive_step(sample_patent_low_creativity)

        # 验证结果
        assert result["has_inventive_step"] == False
        assert result["step_magnitude"] == "none"
        assert result["technical_difficulty"] == "low"
        assert result["innovation_level"] == "routine"


class TestTechnicalAdvancementAnalysisWithLLM:
    """测试技术进步分析（LLM版本）"""

    @pytest.mark.asyncio
    async def test_technical_advancement_analysis_with_llm_success(self, analyzer, sample_patent):
        """测试LLM技术进步分析成功"""
        # Mock LLM响应
        mock_response = """```json
{
    "has_advancement": true,
    "advancement_type": "performance",
    "improvement_degree": "significant",
    "confidence": 0.9,
    "reasoning": "本发明显著提高了自动驾驶感知系统的性能，感知准确率提高30%，误报率降低50%，解决了长期未解决的技术难题。",
    "evidence": [
        "感知准确率提高30%",
        "误报率降低50%",
        "恶劣天气条件下保持高可靠性",
        "解决了长期未解决的技术难题"
    ],
    "quantitative_metrics": {
        "performance_improvement": "30%",
        "error_rate_reduction": "50%",
        "reliability_improvement": "显著"
    },
    "commercial_value": "high",
    "technical_significance": "重大技术进步，对自动驾驶产业化具有重要推动作用"
}
```"""

        # Mock LLM调用
        analyzer._call_llm_with_fallback = AsyncMock(return_value=mock_response)

        # 执行分析
        result = await analyzer.analyze_technical_advancement(sample_patent)

        # 验证结果
        assert result["has_advancement"] == True
        assert result["advancement_type"] == "performance"
        assert result["improvement_degree"] == "significant"
        assert result["confidence"] == 0.9
        assert len(result["evidence"]) == 4
        assert result["commercial_value"] == "high"

    @pytest.mark.asyncio
    async def test_technical_advancement_analysis_fallback_to_rules(self, analyzer, sample_patent):
        """测试LLM失败时降级到规则分析"""
        # Mock LLM调用失败
        analyzer._call_llm_with_fallback = AsyncMock(side_effect=Exception("LLM error"))

        # 执行分析（应该降级到规则）
        result = await analyzer.analyze_technical_advancement(sample_patent)

        # 验证降级方案结果
        assert "has_advancement" in result
        assert "advancement_type" in result
        assert "improvement_degree" in result


class TestComprehensiveCreativityAnalysis:
    """测试完整创造性分析流程"""

    @pytest.mark.asyncio
    async def test_comprehensive_creativity_analysis_with_llm(self, analyzer, sample_patent):
        """测试完整创造性分析流程（LLM版本）"""
        # Mock LLM响应
        mock_response = """```json
{
    "obviousness_assessment": {
        "is_obvious": false,
        "confidence": 0.85,
        "reasoning": "非显而易见"
    },
    "inventive_step_evaluation": {
        "has_inventive_step": true,
        "step_magnitude": "significant",
        "confidence": 0.9,
        "evidence": ["证据1", "证据2"]
    },
    "technical_advancement": {
        "has_advancement": true,
        "advancement_type": "performance",
        "improvement_degree": "significant",
        "evidence": ["证据1", "证据2"]
    },
    "unexpected_effects": {
        "has_unexpected_effects": true,
        "effects": ["感知准确率提高30%", "误报率降低50%"],
        "evidence": ["预料不到的技术效果"]
    },
    "creativity_conclusion": "具备创造性",
    "creativity_level": "high",
    "overall_confidence": 0.88,
    "key_reasoning": [
        "非显而易见的技术方案",
        "显著的技术进步",
        "预料不到的技术效果"
    ],
    "recommendations": ["建议授权"]
}
```"""

        # Mock LLM调用
        analyzer._call_llm_with_fallback = AsyncMock(return_value=mock_response)

        # 执行完整分析
        result = await analyzer.analyze_creativity(sample_patent)

        # 验证结果
        assert "obviousness_assessment" in result
        assert "inventive_step_evaluation" in result
        assert "technical_advancement" in result
        assert "unexpected_effects" in result
        assert "creativity_conclusion" in result
        assert "creativity_level" in result
        assert result["creativity_level"] == "high"
        assert result["patent_id"] == "CN123456789A"


class TestPromptBuilding:
    """测试提示词构建"""

    def test_build_obviousness_assessment_prompt(self, analyzer, sample_patent):
        """测试显而易见性评估提示词构建"""
        prompt = analyzer._build_obviousness_assessment_prompt(sample_patent)

        assert "# 任务：专利显而易见性评估" in prompt
        assert "CN123456789A" in prompt
        assert "自动驾驶" in prompt
        assert "```json" in prompt
        assert "is_obvious" in prompt

    def test_build_inventive_step_prompt(self, analyzer, sample_patent):
        """测试创造性步骤评估提示词构建"""
        prompt = analyzer._build_inventive_step_prompt(sample_patent)

        assert "# 任务：专利创造性步骤评估" in prompt
        assert "多模态融合架构" in prompt
        assert "has_inventive_step" in prompt
        assert "step_magnitude" in prompt

    def test_build_technical_advancement_prompt(self, analyzer, sample_patent):
        """测试技术进步分析提示词构建"""
        prompt = analyzer._build_technical_advancement_prompt(sample_patent)

        assert "# 任务：专利技术进步分析" in prompt
        assert "人工智能" in prompt
        assert "has_advancement" in prompt
        assert "improvement_degree" in prompt

    def test_build_comprehensive_creativity_prompt(self, analyzer, sample_patent):
        """测试完整创造性分析提示词构建"""
        prompt = analyzer._build_comprehensive_creativity_prompt(sample_patent)

        assert "# 任务：专利创造性综合分析" in prompt
        assert "CN123456789A" in prompt
        assert "creativity_conclusion" in prompt
        assert "creativity_level" in prompt


class TestResponseParsing:
    """测试响应解析"""

    def test_parse_obviousness_response_success(self, analyzer):
        """测试成功解析显而易见性评估响应"""
        response = """```json
{
    "is_obvious": false,
    "confidence": 0.85,
    "reasoning": "非显而易见"
}
```"""

        result = analyzer._parse_obviousness_response(response)

        assert result["is_obvious"] == False
        assert result["confidence"] == 0.85
        assert result["reasoning"] == "非显而易见"

    def test_parse_obviousness_response_invalid_json(self, analyzer):
        """测试解析无效JSON"""
        response = "This is not a valid JSON"

        result = analyzer._parse_obviousness_response(response)

        # 应该返回默认值
        assert result["is_obvious"] == True
        assert result["confidence"] == 0.5
        assert "LLM响应解析失败" in result["reasoning"]

    def test_parse_inventive_step_response_success(self, analyzer):
        """测试成功解析创造性步骤评估响应"""
        response = """```json
{
    "has_inventive_step": true,
    "step_magnitude": "significant",
    "confidence": 0.9
}
```"""

        result = analyzer._parse_inventive_step_response(response)

        assert result["has_inventive_step"] == True
        assert result["step_magnitude"] == "significant"
        assert result["confidence"] == 0.9

    def test_parse_technical_advancement_response_success(self, analyzer):
        """测试成功解析技术进步分析响应"""
        response = """```json
{
    "has_advancement": true,
    "advancement_type": "performance",
    "improvement_degree": "significant",
    "confidence": 0.9
}
```"""

        result = analyzer._parse_technical_advancement_response(response)

        assert result["has_advancement"] == True
        assert result["advancement_type"] == "performance"
        assert result["improvement_degree"] == "significant"
        assert result["confidence"] == 0.9

    def test_parse_comprehensive_creativity_response_success(self, analyzer, sample_patent):
        """测试成功解析完整创造性分析响应"""
        response = """```json
{
    "obviousness_assessment": {"is_obvious": false},
    "inventive_step_evaluation": {"has_inventive_step": true},
    "technical_advancement": {"has_advancement": true},
    "unexpected_effects": {"has_unexpected_effects": true},
    "creativity_conclusion": "具备创造性",
    "creativity_level": "high"
}
```"""

        result = analyzer._parse_comprehensive_creativity_response(response, sample_patent)

        assert result["obviousness_assessment"]["is_obvious"] == False
        assert result["inventive_step_evaluation"]["has_inventive_step"] == True
        assert result["creativity_conclusion"] == "具备创造性"
        assert result["creativity_level"] == "high"
        assert result["patent_id"] == "CN123456789A"


class TestRulesBasedFallback:
    """测试规则-based降级方案"""

    @pytest.mark.asyncio
    async def test_obviousness_assessment_by_rules(self, analyzer, sample_patent):
        """测试基于规则的显而易见性评估"""
        result = await analyzer._assess_obviousness_by_rules(sample_patent)

        assert "is_obvious" in result
        assert "confidence" in result
        assert "reasoning" in result
        assert "key_factors" in result

    @pytest.mark.asyncio
    async def test_inventive_step_evaluation_by_rules(self, analyzer, sample_patent):
        """测试基于规则的创造性步骤评估"""
        result = await analyzer._evaluate_inventive_step_by_rules(sample_patent)

        assert "has_inventive_step" in result
        assert "step_magnitude" in result
        assert "technical_difficulty" in result
        assert "innovation_level" in result

    @pytest.mark.asyncio
    async def test_technical_advancement_analysis_by_rules(self, analyzer, sample_patent):
        """测试基于规则的技术进步分析"""
        result = await analyzer._analyze_technical_advancement_by_rules(sample_patent)

        assert "has_advancement" in result
        assert "advancement_type" in result
        assert "improvement_degree" in result
        assert "commercial_value" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
