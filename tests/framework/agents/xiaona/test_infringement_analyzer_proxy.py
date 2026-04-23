"""
侵权分析代理（InfringementAnalyzerProxy）单元测试

测试内容：
1. 初始化测试
2. 能力注册测试
3. 系统提示词测试
4. 基本功能测试（使用mock）
"""

import pytest
from typing import Dict, List, Optional, Any

from unittest.mock import patch

from core.framework.agents.xiaona.infringement_analyzer_proxy import InfringementAnalyzerProxy
from core.framework.agents.xiaona.base_component import AgentExecutionContext


class TestInfringementAnalyzerInitialization:
    """侵权分析代理初始化测试"""

    def test_infringement_analyzer_initialization(self):
        """测试侵权分析代理初始化"""
        analyzer = InfringementAnalyzerProxy()
        assert analyzer.agent_id == "infringement_analyzer"
        assert analyzer.status.value == "idle"


class TestInfringementAnalyzerCapabilities:
    """侵权分析代理能力注册测试"""

    def test_infringement_analyzer_capabilities(self):
        """测试能力注册"""
        analyzer = InfringementAnalyzerProxy()
        capabilities = analyzer.get_capabilities()
        capability_names = [c.name for c in capabilities]

        assert "claim_interpretation" in capability_names
        assert "feature_comparison" in capability_names
        assert "infringement_determination" in capability_names
        assert "risk_assessment" in capability_names

    def test_infringement_analyzer_capability_details(self):
        """测试能力详情"""
        analyzer = InfringementAnalyzerProxy()
        capabilities = analyzer.get_capabilities()

        # 检查claim_interpretation能力
        interpretation = next((c for c in capabilities if c.name == "claim_interpretation"), None)
        assert interpretation is not None
        assert "权利要求解释" in interpretation.description

    def test_infringement_analyzer_has_capability(self):
        """测试能力检查方法"""
        analyzer = InfringementAnalyzerProxy()
        assert analyzer.has_capability("claim_interpretation")
        assert analyzer.has_capability("feature_comparison")
        assert not analyzer.has_capability("nonexistent_capability")


class TestInfringementAnalyzerSystemPrompt:
    """侵权分析代理系统提示词测试"""

    def test_get_system_prompt(self):
        """测试获取系统提示词"""
        analyzer = InfringementAnalyzerProxy()
        prompt = analyzer.get_system_prompt()

        assert "专利侵权分析专家" in prompt
        assert "权利要求解释" in prompt
        assert "全面原则" in prompt
        assert "等同原则" in prompt


class TestInfringementAnalyzerExecute:
    """侵权分析代理基本功能测试"""

    @pytest.mark.asyncio
    async def test_execute_default_task(self):
        """测试默认任务执行（完整侵权分析）"""
        analyzer = InfringementAnalyzerProxy()

        context = AgentExecutionContext(
            session_id="test_session",
            task_id="test_task",
            input_data={
                "patent_data": {
                    "patent_id": "CN123456",
                    "claims": "1. 一种测试装置...",
                    "estimated_value": 1000000
                },
                "product_data": {
                    "product_name": "被控产品",
                    "features": {"特征A": "valueA"}
                }
            },
            config={},
            metadata={}
        )

        # Mock各阶段方法
        with patch.object(analyzer, 'interpret_claims', return_value={"claims": []}):
            with patch.object(analyzer, 'compare_features', return_value={"comparisons": []}):
                with patch.object(analyzer, 'determine_infringement', return_value={}):
                    with patch.object(analyzer, 'assess_risk', return_value={}):
                        result = await analyzer.execute(context)

        assert "patent_id" in result
        assert "product" in result

    @pytest.mark.asyncio
    async def test_interpret_claims(self):
        """测试权利要求解释"""
        analyzer = InfringementAnalyzerProxy()

        patent_data = {
            "patent_id": "CN123456",
            "claims": "1. 一种测试装置，包括特征A、特征B和特征C。"
        }

        # 使用规则降级
        result = await analyzer.interpret_claims(patent_data)

        assert result["patent_id"] == "CN123456"
        assert "claims" in result

    @pytest.mark.asyncio
    async def test_compare_features(self):
        """测试特征比对"""
        analyzer = InfringementAnalyzerProxy()

        claims = [
            {
                "claim_number": 1,
                "essential_features": ["特征A", "特征B", "特征C"]
            }
        ]

        product_description = {
            "product_name": "测试产品",
            "features": {
                "特征A": "实现方式A",
                "特征B": "实现方式B",
                "特征C": "实现方式C"
            }
        }

        result = await analyzer.compare_features(claims, product_description)

        assert "product" in result
        assert "comparisons" in result

    @pytest.mark.asyncio
    async def test_determine_infringement(self):
        """测试侵权判定"""
        analyzer = InfringementAnalyzerProxy()

        comparisons = [
            {
                "claim_number": 1,
                "covered_features": ["特征A", "特征B"],
                "missing_features": [],
                "infringement_type": "literal_infringement"
            }
        ]

        result = await analyzer.determine_infringement(comparisons)

        assert "infringement_conclusion" in result
        assert "confidence" in result

    @pytest.mark.asyncio
    async def test_assess_risk(self):
        """测试风险评估"""
        analyzer = InfringementAnalyzerProxy()

        infringement_result = {
            "infringement_conclusion": "构成字面侵权",
            "confidence": 0.9,
            "infringed_claims": {"literal": [1, 2], "equivalent": [], "total": 2}
        }

        result = await analyzer.assess_risk(infringement_result, 1000000)

        assert "risk_level" in result
        assert "estimated_damages" in result


class TestInfringementAnalyzerHelperMethods:
    """侵权分析代理辅助方法测试"""

    def test_parse_claims(self):
        """测试解析权利要求"""
        analyzer = InfringementAnalyzerProxy()

        claims_text = """1. 一种测试装置，包括特征A。
2. 根据权利要求1所述的装置，还包括特征B。
3. 根据权利要求2所述的装置，还包括特征C。"""

        claims = analyzer._parse_claims(claims_text)

        assert len(claims) == 3
        assert claims[0]["type"] == "independent"
        assert claims[1]["type"] == "dependent"

    def test_extract_essential_features(self):
        """测试提取必要技术特征"""
        analyzer = InfringementAnalyzerProxy()

        claim_text = "一种测试装置，包括特征A、特征B和特征C。"

        features = analyzer._extract_essential_features(claim_text)

        assert isinstance(features, list)

    def test_determine_protection_scope(self):
        """测试确定保护范围"""
        analyzer = InfringementAnalyzerProxy()

        narrow_claim = "1. 一种装置，包括特征A。"
        wide_claim = "1. 一种装置，包括特征A、特征B、特征C、特征D、特征E和特征F，其中所述特征A..."

        scope1 = analyzer._determine_protection_scope(narrow_claim)
        scope2 = analyzer._determine_protection_scope(wide_claim)

        assert scope1 in ["较窄", "中等", "较宽"]
        assert scope2 in ["较窄", "中等", "较宽"]

    def test_feature_covered(self):
        """测试特征覆盖判断"""
        analyzer = InfringementAnalyzerProxy()

        product_features = {
            "特征A": "实现方式A",
            "特征B": "实现方式B"
        }

        result1 = analyzer._feature_covered("特征A", product_features)
        result2 = analyzer._feature_covered("特征C", product_features)

        assert result1 is True
        assert result2 is False

    def test_is_equivalent(self):
        """测试等同特征判断"""
        analyzer = InfringementAnalyzerProxy()

        result1 = analyzer._is_equivalent("包括特征A", "包含特征A")
        result2 = analyzer._is_equivalent("包括特征A", "完全不同的特征")

        assert result1 is True
        assert result2 is False

    def test_generate_comparison_summary(self):
        """测试生成比对摘要"""
        analyzer = InfringementAnalyzerProxy()

        comparisons = [
            {"infringement_type": "literal_infringement", "coverage_ratio": 1.0},
            {"infringement_type": "no_infringement", "coverage_ratio": 0.5}
        ]

        summary = analyzer._generate_comparison_summary(comparisons)

        assert "total_claims_compared" in summary
        assert summary["total_claims_compared"] == 2

    def test_get_legal_basis(self):
        """测试获取法律依据"""
        analyzer = InfringementAnalyzerProxy()

        basis1 = analyzer._get_legal_basis([1], [])
        basis2 = analyzer._get_legal_basis([], [1])
        basis3 = analyzer._get_legal_basis([1], [1])

        assert "全面原则" in basis1
        assert "等同原则" in basis2

    def test_generate_action_recommendations(self):
        """测试生成行动建议"""
        analyzer = InfringementAnalyzerProxy()

        high_actions = analyzer._generate_action_recommendations("high")
        medium_actions = analyzer._generate_action_recommendations("medium")
        low_actions = analyzer._generate_action_recommendations("low")

        assert len(high_actions) > 0
        assert len(medium_actions) > 0
        assert len(low_actions) > 0
        assert "停止" in high_actions[0] or "许可" in high_actions[0]


class TestInfringementAnalyzerInfo:
    """侵权分析代理信息测试"""

    def test_get_info(self):
        """测试获取代理信息"""
        analyzer = InfringementAnalyzerProxy()
        info = analyzer.get_info()

        assert info["agent_id"] == "infringement_analyzer"
        assert info["agent_type"] == "InfringementAnalyzerProxy"
        assert "capabilities" in info

    def test_repr(self):
        """测试代理字符串表示"""
        analyzer = InfringementAnalyzerProxy()
        repr_str = repr(analyzer)

        assert "InfringementAnalyzerProxy" in repr_str
