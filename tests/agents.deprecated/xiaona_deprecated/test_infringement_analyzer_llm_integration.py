"""
InfringementAnalyzerProxy LLM集成测试

测试侵权分析智能体的LLM调用功能。
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from core.agents.xiaona.infringement_analyzer_proxy import InfringementAnalyzerProxy


@pytest.fixture
def analyzer():
    """创建侵权分析智能体实例"""
    return InfringementAnalyzerProxy(
        agent_id="test_infringement_analyzer",
        config={"llm_config": {"model": "claude-3-5-sonnet-20241022"}}
    )


@pytest.fixture
def sample_patent():
    """示例专利数据"""
    return {
        "patent_id": "CN123456789A",
        "title": "一种自动驾驶控制方法",
        "claims": """1. 一种自动驾驶控制方法，其特征在于，包括：
获取车辆周围环境数据；
根据所述环境数据生成控制指令；
根据所述控制指令控制车辆行驶。

2. 根据权利要求1所述的方法，其特征在于，所述环境数据包括图像数据和激光雷达数据。

3. 根据权利要求1所述的方法，其特征在于，所述控制指令包括加速指令、减速指令和转向指令。""",
        "specification": """技术领域
本发明涉及自动驾驶技术领域，具体涉及一种自动驾驶控制方法。

背景技术
随着人工智能技术的发展，自动驾驶技术越来越受到关注。

发明内容
本发明提供一种自动驾驶控制方法，能够提高行驶安全性。

具体实施方式
下面结合附图对本发明作进一步说明。"""
    }


@pytest.fixture
def sample_product_literal_infringement():
    """示例产品数据（字面侵权）"""
    return {
        "product_name": "某品牌自动驾驶系统",
        "features": {
            "环境数据获取": "通过摄像头和激光雷达获取车辆周围环境数据",
            "控制指令生成": "根据环境数据生成加速、减速、转向等控制指令",
            "车辆控制": "根据控制指令控制车辆的油门、刹车和转向系统"
        }
    }


@pytest.fixture
def sample_product_equivalent_infringement():
    """示例产品数据（等同侵权）"""
    return {
        "product_name": "某品牌辅助驾驶系统",
        "features": {
            "环境感知": "通过多传感器融合获取周围环境信息",
            "决策控制": "基于环境信息生成驾驶策略",
            "执行控制": "将驾驶策略转换为车辆控制信号"
        }
    }


@pytest.fixture
def sample_product_no_infringement():
    """示例产品数据（不侵权）"""
    return {
        "product_name": "普通定速巡航系统",
        "features": {
            "速度设定": "驾驶员设定巡航速度",
            "速度保持": "系统自动保持设定速度",
            "速度调节": "通过按钮调节巡航速度"
        }
    }


class TestClaimInterpretationWithLLM:
    """测试权利要求解释（LLM版本）"""

    @pytest.mark.asyncio
    async def test_interpret_claims_with_llm_success(self, analyzer, sample_patent):
        """测试LLM权利要求解释成功"""
        # Mock LLM响应
        mock_response = """```json
{
    "patent_id": "CN123456789A",
    "total_claims": 3,
    "independent_claims": 1,
    "dependent_claims": 2,
    "claims": [
        {
            "claim_number": 1,
            "type": "independent",
            "text": "一种自动驾驶控制方法，其特征在于，包括：获取车辆周围环境数据；根据所述环境数据生成控制指令；根据所述控制指令控制车辆行驶。",
            "essential_features": [
                "获取车辆周围环境数据",
                "根据环境数据生成控制指令",
                "根据控制指令控制车辆行驶"
            ],
            "protection_scope": "中等",
            "interpretation_notes": "权利要求1保护一种自动驾驶控制方法，包含三个核心步骤",
            "functional_features": ["生成控制指令", "控制车辆行驶"],
            "broad_concepts": ["环境数据", "控制指令"]
        },
        {
            "claim_number": 2,
            "type": "dependent",
            "text": "根据权利要求1所述的方法，其特征在于，所述环境数据包括图像数据和激光雷达数据。",
            "essential_features": [
                "环境数据包括图像数据和激光雷达数据"
            ],
            "protection_scope": "较窄",
            "interpretation_notes": "权利要求2进一步限定了环境数据的类型",
            "functional_features": [],
            "broad_concepts": []
        },
        {
            "claim_number": 3,
            "type": "dependent",
            "text": "根据权利要求1所述的方法，其特征在于，所述控制指令包括加速指令、减速指令和转向指令。",
            "essential_features": [
                "控制指令包括加速指令、减速指令和转向指令"
            ],
            "protection_scope": "较窄",
            "interpretation_notes": "权利要求3进一步限定了控制指令的类型",
            "functional_features": [],
            "broad_concepts": []
        }
    ]
}
```"""

        # Mock LLM调用
        analyzer._call_llm_with_fallback = AsyncMock(return_value=mock_response)

        # 执行解释
        result = await analyzer.interpret_claims(sample_patent)

        # 验证结果
        assert result["patent_id"] == "CN123456789A"
        assert result["total_claims"] == 3
        assert result["independent_claims"] == 1
        assert result["dependent_claims"] == 2
        assert len(result["claims"]) == 3

        # 验证权利要求1
        claim1 = result["claims"][0]
        assert claim1["claim_number"] == 1
        assert claim1["type"] == "independent"
        assert len(claim1["essential_features"]) == 3

    @pytest.mark.asyncio
    async def test_interpret_claims_fallback_to_rules(self, analyzer, sample_patent):
        """测试LLM失败时降级到规则解释"""
        # Mock LLM调用失败
        analyzer._call_llm_with_fallback = AsyncMock(side_effect=Exception("LLM error"))

        # 执行解释（应该降级到规则）
        result = await analyzer.interpret_claims(sample_patent)

        # 验证降级方案结果
        assert "patent_id" in result
        assert "total_claims" in result
        assert "claims" in result
        assert result["patent_id"] == "CN123456789A"


class TestFeatureComparisonWithLLM:
    """测试特征比对（LLM版本）"""

    @pytest.mark.asyncio
    async def test_compare_features_literal_infringement(self, analyzer, sample_patent, sample_product_literal_infringement):
        """测试字面侵权场景的特征比对"""
        # 先获取权利要求解释
        claims_result = await analyzer.interpret_claims(sample_patent)
        claims = claims_result["claims"]

        # Mock LLM响应（字面侵权）
        mock_response = """```json
{
    "product": "某品牌自动驾驶系统",
    "comparisons": [
        {
            "claim_number": 1,
            "covered_features": [
                "获取车辆周围环境数据",
                "根据环境数据生成控制指令",
                "根据控制指令控制车辆行驶"
            ],
            "missing_features": [],
            "equivalent_features": [],
            "infringement_type": "literal_infringement",
            "coverage_ratio": 1.0,
            "analysis": "被诉产品包含了权利要求1的全部必要技术特征，构成字面侵权"
        }
    ],
    "summary": {
        "total_claims_compared": 1,
        "literal_infringement": 1,
        "equivalent_infringement": 0,
        "no_infringement": 0,
        "average_coverage_ratio": 1.0
    }
}
```"""

        # Mock LLM调用
        analyzer._call_llm_with_fallback = AsyncMock(return_value=mock_response)

        # 执行特征比对
        result = await analyzer.compare_features(claims, sample_product_literal_infringement)

        # 验证结果
        assert result["product"] == "某品牌自动驾驶系统"
        assert len(result["comparisons"]) == 1
        assert result["comparisons"][0]["infringement_type"] == "literal_infringement"
        assert result["comparisons"][0]["coverage_ratio"] == 1.0

    @pytest.mark.asyncio
    async def test_compare_features_equivalent_infringement(self, analyzer, sample_patent, sample_product_equivalent_infringement):
        """测试等同侵权场景的特征比对"""
        # 先获取权利要求解释
        claims_result = await analyzer.interpret_claims(sample_patent)
        claims = claims_result["claims"]

        # Mock LLM响应（等同侵权）
        mock_response = """```json
{
    "product": "某品牌辅助驾驶系统",
    "comparisons": [
        {
            "claim_number": 1,
            "covered_features": [
                "获取车辆周围环境数据"
            ],
            "missing_features": [
                "根据环境数据生成控制指令",
                "根据控制指令控制车辆行驶"
            ],
            "equivalent_features": [
                "环境感知 ≈ 获取车辆周围环境数据",
                "决策控制 ≈ 根据环境数据生成控制指令",
                "执行控制 ≈ 根据控制指令控制车辆行驶"
            ],
            "infringement_type": "equivalent_infringement",
            "coverage_ratio": 0.33,
            "analysis": "被诉产品的特征与权利要求1的特征构成等同，可能构成等同侵权"
        }
    ],
    "summary": {
        "total_claims_compared": 1,
        "literal_infringement": 0,
        "equivalent_infringement": 1,
        "no_infringement": 0,
        "average_coverage_ratio": 0.33
    }
}
```"""

        # Mock LLM调用
        analyzer._call_llm_with_fallback = AsyncMock(return_value=mock_response)

        # 执行特征比对
        result = await analyzer.compare_features(claims, sample_product_equivalent_infringement)

        # 验证结果
        assert result["product"] == "某品牌辅助驾驶系统"
        assert result["comparisons"][0]["infringement_type"] == "equivalent_infringement"
        assert len(result["comparisons"][0]["equivalent_features"]) > 0

    @pytest.mark.asyncio
    async def test_compare_features_no_infringement(self, analyzer, sample_patent, sample_product_no_infringement):
        """测试不侵权场景的特征比对"""
        # 先获取权利要求解释
        claims_result = await analyzer.interpret_claims(sample_patent)
        claims = claims_result["claims"]

        # Mock LLM响应（不侵权）
        mock_response = """```json
{
    "product": "普通定速巡航系统",
    "comparisons": [
        {
            "claim_number": 1,
            "covered_features": [],
            "missing_features": [
                "获取车辆周围环境数据",
                "根据环境数据生成控制指令",
                "根据控制指令控制车辆行驶"
            ],
            "equivalent_features": [],
            "infringement_type": "no_infringement",
            "coverage_ratio": 0.0,
            "analysis": "被诉产品仅具备定速巡航功能，不涉及自动驾驶控制，不构成侵权"
        }
    ],
    "summary": {
        "total_claims_compared": 1,
        "literal_infringement": 0,
        "equivalent_infringement": 0,
        "no_infringement": 1,
        "average_coverage_ratio": 0.0
    }
}
```"""

        # Mock LLM调用
        analyzer._call_llm_with_fallback = AsyncMock(return_value=mock_response)

        # 执行特征比对
        result = await analyzer.compare_features(claims, sample_product_no_infringement)

        # 验证结果
        assert result["product"] == "普通定速巡航系统"
        assert result["comparisons"][0]["infringement_type"] == "no_infringement"
        assert result["comparisons"][0]["coverage_ratio"] == 0.0

    @pytest.mark.asyncio
    async def test_compare_features_fallback_to_rules(self, analyzer, sample_patent, sample_product_literal_infringement):
        """测试LLM失败时降级到规则比对"""
        # 先获取权利要求解释
        claims_result = await analyzer.interpret_claims(sample_patent)
        claims = claims_result["claims"]

        # Mock LLM调用失败
        analyzer._call_llm_with_fallback = AsyncMock(side_effect=Exception("LLM error"))

        # 执行比对（应该降级到规则）
        result = await analyzer.compare_features(claims, sample_product_literal_infringement)

        # 验证降级方案结果
        assert "product" in result
        assert "comparisons" in result
        assert "summary" in result


class TestInfringementDeterminationWithLLM:
    """测试侵权判定（LLM版本）"""

    @pytest.mark.asyncio
    async def test_determine_infringement_literal(self, analyzer):
        """测试字面侵权判定"""
        comparisons = [
            {
                "claim_number": 1,
                "infringement_type": "literal_infringement",
                "covered_features": ["特征1", "特征2", "特征3"],
                "missing_features": [],
                "coverage_ratio": 1.0
            }
        ]

        # Mock LLM响应
        mock_response = """```json
{
    "infringement_conclusion": "构成字面侵权",
    "infringed_claims": {
        "literal": [1],
        "equivalent": [],
        "total": 1
    },
    "non_infringed_claims": [],
    "legal_basis": "专利法第11条（全面原则）",
    "confidence": 0.9,
    "reasoning": "被诉产品包含了权利要求1的全部必要技术特征，根据全面原则，构成字面侵权。"
}
```"""

        # Mock LLM调用
        analyzer._call_llm_with_fallback = AsyncMock(return_value=mock_response)

        # 执行判定
        result = await analyzer.determine_infringement(comparisons)

        # 验证结果
        assert result["infringement_conclusion"] == "构成字面侵权"
        assert result["confidence"] == 0.9
        assert len(result["infringed_claims"]["literal"]) == 1

    @pytest.mark.asyncio
    async def test_determine_infringement_equivalent(self, analyzer):
        """测试等同侵权判定"""
        comparisons = [
            {
                "claim_number": 1,
                "infringement_type": "equivalent_infringement",
                "covered_features": ["特征1"],
                "missing_features": ["特征2", "特征3"],
                "equivalent_features": ["特征2 ≈ 特征2'", "特征3 ≈ 特征3'"],
                "coverage_ratio": 0.33
            }
        ]

        # Mock LLM响应
        mock_response = """```json
{
    "infringement_conclusion": "构成等同侵权",
    "infringed_claims": {
        "literal": [],
        "equivalent": [1],
        "total": 1
    },
    "non_infringed_claims": [],
    "legal_basis": "专利法第11条（等同原则）",
    "confidence": 0.75,
    "reasoning": "被诉产品的特征与权利要求1的特征手段、功能、效果基本相同，构成等同侵权。"
}
```"""

        # Mock LLM调用
        analyzer._call_llm_with_fallback = AsyncMock(return_value=mock_response)

        # 执行判定
        result = await analyzer.determine_infringement(comparisons)

        # 验证结果
        assert result["infringement_conclusion"] == "构成等同侵权"
        assert result["confidence"] == 0.75
        assert len(result["infringed_claims"]["equivalent"]) == 1

    @pytest.mark.asyncio
    async def test_determine_infringement_no_infringement(self, analyzer):
        """测试不侵权判定"""
        comparisons = [
            {
                "claim_number": 1,
                "infringement_type": "no_infringement",
                "covered_features": [],
                "missing_features": ["特征1", "特征2", "特征3"],
                "equivalent_features": [],
                "coverage_ratio": 0.0
            }
        ]

        # Mock LLM响应
        mock_response = """```json
{
    "infringement_conclusion": "不构成侵权",
    "infringed_claims": {
        "literal": [],
        "equivalent": [],
        "total": 0
    },
    "non_infringed_claims": [1],
    "legal_basis": "不适用",
    "confidence": 0.92,
    "reasoning": "被诉产品缺少权利要求1的多个必要技术特征，且不构成等同，不构成侵权。"
}
```"""

        # Mock LLM调用
        analyzer._call_llm_with_fallback = AsyncMock(return_value=mock_response)

        # 执行判定
        result = await analyzer.determine_infringement(comparisons)

        # 验证结果
        assert result["infringement_conclusion"] == "不构成侵权"
        assert result["confidence"] == 0.92
        assert result["infringed_claims"]["total"] == 0

    @pytest.mark.asyncio
    async def test_determine_infringement_fallback_to_rules(self, analyzer):
        """测试LLM失败时降级到规则判定"""
        comparisons = [
            {
                "claim_number": 1,
                "infringement_type": "literal_infringement",
                "covered_features": ["特征1"],
                "coverage_ratio": 1.0
            }
        ]

        # Mock LLM调用失败
        analyzer._call_llm_with_fallback = AsyncMock(side_effect=Exception("LLM error"))

        # 执行判定（应该降级到规则）
        result = await analyzer.determine_infringement(comparisons)

        # 验证降级方案结果
        assert "infringement_conclusion" in result
        assert "infringed_claims" in result
        assert "confidence" in result


class TestRiskAssessmentWithLLM:
    """测试风险评估（LLM版本）"""

    @pytest.mark.asyncio
    async def test_assess_risk_high(self, analyzer):
        """测试高风险评估"""
        infringement_result = {
            "infringement_conclusion": "构成字面侵权",
            "confidence": 0.9,
            "infringed_claims": {"total": 3}
        }
        claim_value = 1000000

        # Mock LLM响应
        mock_response = """```json
{
    "risk_level": "high",
    "estimated_damages": 500000,
    "injunctive_relief_risk": 0.9,
    "litigation_risk": "high",
    "design_around_suggestions": [
        "修改被控侵权产品的技术特征，使其不完全落入权利要求保护范围",
        "通过技术改进，实现与专利不同的技术方案",
        "寻求专利无效宣告或专利权评价",
        "评估许可谈判的可行性"
    ],
    "recommended_actions": [
        "立即停止涉嫌侵权行为",
        "寻求专业律师意见",
        "考虑与专利权人协商许可",
        "评估无效宣告的可能性"
    ],
    "risk_analysis": "构成字面侵权且置信度高，侵权风险高，建议立即采取应对措施。"
}
```"""

        # Mock LLM调用
        analyzer._call_llm_with_fallback = AsyncMock(return_value=mock_response)

        # 执行评估
        result = await analyzer.assess_risk(infringement_result, claim_value)

        # 验证结果
        assert result["risk_level"] == "high"
        assert result["estimated_damages"] == 500000
        assert result["injunctive_relief_risk"] == 0.9
        assert len(result["recommended_actions"]) > 0

    @pytest.mark.asyncio
    async def test_assess_risk_medium(self, analyzer):
        """测试中风险评估"""
        infringement_result = {
            "infringement_conclusion": "构成等同侵权",
            "confidence": 0.75,
            "infringed_claims": {"total": 1}
        }
        claim_value = 1000000

        # Mock LLM响应
        mock_response = """```json
{
    "risk_level": "medium",
    "estimated_damages": 300000,
    "injunctive_relief_risk": 0.6,
    "litigation_risk": "medium",
    "design_around_suggestions": [
        "修改被控侵权产品的技术特征",
        "寻求专利无效宣告"
    ],
    "recommended_actions": [
        "继续监控市场动态",
        "准备规避设计方案",
        "收集不侵权证据",
        "评估许可谈判的可行性"
    ],
    "risk_analysis": "构成等同侵权，风险中等，建议准备应对方案。"
}
```"""

        # Mock LLM调用
        analyzer._call_llm_with_fallback = AsyncMock(return_value=mock_response)

        # 执行评估
        result = await analyzer.assess_risk(infringement_result, claim_value)

        # 验证结果
        assert result["risk_level"] == "medium"
        assert result["estimated_damages"] == 300000
        assert result["injunctive_relief_risk"] == 0.6

    @pytest.mark.asyncio
    async def test_assess_risk_low(self, analyzer):
        """测试低风险评估"""
        infringement_result = {
            "infringement_conclusion": "不构成侵权",
            "confidence": 0.92,
            "infringed_claims": {"total": 0}
        }
        claim_value = 1000000

        # Mock LLM响应
        mock_response = """```json
{
    "risk_level": "low",
    "estimated_damages": 0,
    "injunctive_relief_risk": 0.1,
    "litigation_risk": "low",
    "design_around_suggestions": [],
    "recommended_actions": [
        "继续现有业务",
        "定期更新技术方案",
        "关注专利法律动态"
    ],
    "risk_analysis": "不构成侵权，风险低，可继续现有业务。"
}
```"""

        # Mock LLM调用
        analyzer._call_llm_with_fallback = AsyncMock(return_value=mock_response)

        # 执行评估
        result = await analyzer.assess_risk(infringement_result, claim_value)

        # 验证结果
        assert result["risk_level"] == "low"
        assert result["estimated_damages"] == 0
        assert result["injunctive_relief_risk"] == 0.1

    @pytest.mark.asyncio
    async def test_assess_risk_fallback_to_rules(self, analyzer):
        """测试LLM失败时降级到规则评估"""
        infringement_result = {
            "infringement_conclusion": "构成字面侵权",
            "confidence": 0.85,
            "infringed_claims": {"total": 2}
        }
        claim_value = 1000000

        # Mock LLM调用失败
        analyzer._call_llm_with_fallback = AsyncMock(side_effect=Exception("LLM error"))

        # 执行评估（应该降级到规则）
        result = await analyzer.assess_risk(infringement_result, claim_value)

        # 验证降级方案结果
        assert "risk_level" in result
        assert "estimated_damages" in result
        assert "recommended_actions" in result


class TestCompleteAnalysisWorkflow:
    """测试完整侵权分析流程"""

    @pytest.mark.asyncio
    async def test_complete_analysis_with_llm(self, analyzer, sample_patent, sample_product_literal_infringement):
        """测试完整侵权分析流程（使用LLM）"""
        # Mock各个阶段的LLM响应
        responses = [
            # interpret_claims响应
            """```json
{
    "patent_id": "CN123456789A",
    "total_claims": 3,
    "independent_claims": 1,
    "dependent_claims": 2,
    "claims": [
        {
            "claim_number": 1,
            "type": "independent",
            "text": "一种自动驾驶控制方法",
            "essential_features": ["特征1", "特征2", "特征3"],
            "protection_scope": "中等"
        }
    ]
}
```""",
            # compare_features响应
            """```json
{
    "product": "某品牌自动驾驶系统",
    "comparisons": [{
        "claim_number": 1,
        "infringement_type": "literal_infringement",
        "coverage_ratio": 1.0
    }],
    "summary": {}
}
```""",
            # determine_infringement响应
            """```json
{
    "infringement_conclusion": "构成字面侵权",
    "infringed_claims": {"literal": [1], "equivalent": [], "total": 1},
    "non_infringed_claims": [],
    "legal_basis": "专利法第11条",
    "confidence": 0.9,
    "reasoning": "字面侵权"
}
```""",
            # assess_risk响应
            """```json
{
    "risk_level": "high",
    "estimated_damages": 500000,
    "injunctive_relief_risk": 0.9,
    "litigation_risk": "high",
    "design_around_suggestions": [],
    "recommended_actions": ["立即停止侵权"]
}
```"""
        ]

        # Mock LLM调用
        call_count = 0
        async def mock_call(*args, **kwargs):
            nonlocal call_count
            response = responses[call_count % len(responses)]
            call_count += 1
            return response

        analyzer._call_llm_with_fallback = AsyncMock(side_effect=mock_call)

        # 执行完整分析
        result = await analyzer.analyze_infringement(sample_patent, sample_product_literal_infringement)

        # 验证完整结果
        assert result["patent_id"] == "CN123456789A"
        assert "claims_analysis" in result
        assert "feature_comparison" in result
        assert "infringement_conclusion" in result
        assert "risk_assessment" in result
        assert result["infringement_conclusion"]["infringement_conclusion"] == "构成字面侵权"
        assert result["risk_assessment"]["risk_level"] == "high"


class TestEdgeCases:
    """测试边界条件"""

    @pytest.mark.asyncio
    async def test_empty_claims(self, analyzer):
        """测试空权利要求"""
        patent_data = {"patent_id": "TEST", "claims": ""}
        result = await analyzer.interpret_claims(patent_data)
        assert result["total_claims"] >= 0

    @pytest.mark.asyncio
    async def test_malformed_llm_response(self, analyzer, sample_patent):
        """测试格式错误的LLM响应"""
        # Mock返回错误格式的响应
        analyzer._call_llm_with_fallback = AsyncMock(return_value="This is not JSON")

        # 应该降级到规则
        result = await analyzer.interpret_claims(sample_patent)
        assert "patent_id" in result

    @pytest.mark.asyncio
    async def test_zero_claim_value(self, analyzer):
        """测试零索赔金额"""
        infringement_result = {
            "infringement_conclusion": "构成字面侵权",
            "confidence": 0.9,
            "infringed_claims": {"total": 1}
        }
        result = await analyzer.assess_risk(infringement_result, 0)
        assert "estimated_damages" in result
