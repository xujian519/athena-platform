"""
权利要求保护范围测量系统 单元测试

基于论文"A novel approach to measuring the scope of patent claims"(2023)
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import json
from unittest.mock import AsyncMock, Mock

from core.patents.ai_services.claim_scope_analyzer import (
    ClaimScopeAnalyzer,
    ProbabilityEstimate,
    RiskLevel,
    ScopeAnalysisResult,
    ScopeComparison,
    ScopeScore,
    analyze_claim_scope,
    format_scope_report,
)

# ==================== 数据结构测试 ====================

class TestDataStructures:
    """数据结构测试"""

    def test_scope_score_creation(self):
        """测试ScopeScore创建"""
        score = ScopeScore(
            raw_score=65.0,
            normalized_score=63.5,
            confidence=0.85
        )
        assert score.raw_score == 65.0
        assert score.normalized_score == 63.5
        assert score.confidence == 0.85

    def test_scope_score_to_dict(self):
        """测试ScopeScore序列化"""
        score = ScopeScore(raw_score=70.0, normalized_score=68.5, confidence=0.9)
        data = score.to_dict()

        assert data["raw_score"] == 70.0
        assert data["normalized_score"] == 68.5
        assert data["confidence"] == 0.9

    def test_probability_estimate_creation(self):
        """测试ProbabilityEstimate创建"""
        estimate = ProbabilityEstimate(
            probability=0.5,
            log_probability=-0.693,
            self_information=1.0,
            method="test",
            model_used="test_model"
        )
        assert estimate.probability == 0.5
        assert estimate.self_information == 1.0

    def test_probability_estimate_to_dict(self):
        """测试ProbabilityEstimate序列化"""
        estimate = ProbabilityEstimate(
            probability=0.5,
            log_probability=-0.693,
            self_information=1.0,
            method="test",
            model_used="test_model"
        )
        data = estimate.to_dict()

        assert data["probability"] == 0.5
        assert data["method"] == "test"

    def test_scope_analysis_result_creation(self):
        """测试ScopeAnalysisResult创建"""
        result = ScopeAnalysisResult(
            claim_text="测试权利要求",
            claim_number=1,
            scope_score=ScopeScore(raw_score=60.0, normalized_score=60.0, confidence=0.8),
            probability_estimate=ProbabilityEstimate(
                probability=0.5, log_probability=-0.693, self_information=1.0,
                method="test", model_used="test"
            ),
            risk_level=RiskLevel.MEDIUM,
            character_count=10,
            word_count=5,
            technical_term_count=1,
            parameter_count=0
        )

        assert result.claim_number == 1
        assert result.risk_level == RiskLevel.MEDIUM

    def test_scope_analysis_result_to_dict(self):
        """测试ScopeAnalysisResult序列化"""
        result = ScopeAnalysisResult(
            claim_text="测试权利要求",
            claim_number=1,
            scope_score=ScopeScore(raw_score=60.0, normalized_score=60.0, confidence=0.8),
            probability_estimate=ProbabilityEstimate(
                probability=0.5, log_probability=-0.693, self_information=1.0,
                method="test", model_used="test"
            ),
            risk_level=RiskLevel.MEDIUM,
            character_count=10,
            word_count=5,
            technical_term_count=1,
            parameter_count=0
        )

        data = result.to_dict()

        assert data["claim_number"] == 1
        assert data["risk_level"] == "medium"
        assert "scope_score" in data
        assert "probability_estimate" in data


# ==================== 分析器测试 ====================

class TestClaimScopeAnalyzer:
    """分析器基础测试"""

    def test_initialization(self):
        """测试初始化"""
        analyzer = ClaimScopeAnalyzer()
        assert analyzer.llm_manager is None

    def test_initialization_with_llm(self):
        """测试带LLM初始化"""
        mock_llm = Mock()
        analyzer = ClaimScopeAnalyzer(llm_manager=mock_llm)
        assert analyzer.llm_manager == mock_llm

    def test_count_technical_terms(self):
        """测试技术术语计数"""
        analyzer = ClaimScopeAnalyzer()

        text = "该装置包括充电控制器和储能模块"
        count = analyzer._count_technical_terms(text)
        assert count >= 2

    def test_count_parameters(self):
        """测试参数计数"""
        analyzer = ClaimScopeAnalyzer()

        text = "温度为25-30℃，长度为10mm"
        count = analyzer._count_parameters(text)
        assert count >= 2

    def test_identify_narrowing_factors(self):
        """测试缩小因素识别"""
        analyzer = ClaimScopeAnalyzer()

        text = "至少包括三个组件，温度为20-30℃，优选地为25℃"
        factors = analyzer._identify_narrowing_factors(text)
        assert len(factors) > 0

    def test_identify_broadening_factors(self):
        """测试扩大因素识别"""
        analyzer = ClaimScopeAnalyzer()

        text = "包括但不限于以下组件，例如组件A、组件B等"
        factors = analyzer._identify_broadening_factors(text)
        assert len(factors) > 0

    def test_heuristic_probability(self):
        """测试启发式概率估算"""
        analyzer = ClaimScopeAnalyzer()

        # 短文本应该有较高概率
        short_estimate = analyzer._heuristic_probability("一种装置")
        # 长文本应该有较低概率
        long_estimate = analyzer._heuristic_probability("一种装置" * 50)

        assert short_estimate.probability > long_estimate.probability


# ==================== 风险等级测试 ====================

class TestRiskLevelDetermination:
    """风险等级判定测试"""

    def test_low_risk(self):
        """测试低风险等级"""
        analyzer = ClaimScopeAnalyzer()

        level = analyzer._determine_risk_level(75)
        assert level == RiskLevel.LOW

        level = analyzer._determine_risk_level(85)
        assert level == RiskLevel.LOW

    def test_medium_risk(self):
        """测试中风险等级"""
        analyzer = ClaimScopeAnalyzer()

        level = analyzer._determine_risk_level(55)
        assert level == RiskLevel.MEDIUM

        level = analyzer._determine_risk_level(65)
        assert level == RiskLevel.MEDIUM

    def test_high_risk(self):
        """测试高风险等级"""
        analyzer = ClaimScopeAnalyzer()

        level = analyzer._determine_risk_level(35)
        assert level == RiskLevel.HIGH

        level = analyzer._determine_risk_level(45)
        assert level == RiskLevel.HIGH

    def test_very_high_risk(self):
        """测试极高风险等级"""
        analyzer = ClaimScopeAnalyzer()

        level = analyzer._determine_risk_level(15)
        assert level == RiskLevel.VERY_HIGH

        level = analyzer._determine_risk_level(25)
        assert level == RiskLevel.VERY_HIGH


# ==================== 异步测试 ====================

class TestAsyncOperations:
    """异步操作测试"""

    @pytest.mark.asyncio
    async def test_analyze_scope_without_llm(self):
        """测试无LLM时的范围分析"""
        analyzer = ClaimScopeAnalyzer(llm_manager=None)

        result = await analyzer.analyze_scope(
            claim_text="1. 一种装置，其特征在于，包括组件A、组件B和组件C。",
            claim_number=1,
            mode="fast"
        )

        assert isinstance(result, ScopeAnalysisResult)
        assert result.probability_estimate.method == "heuristic_character_count"
        assert result.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.VERY_HIGH]

    @pytest.mark.asyncio
    async def test_analyze_scope_with_mock_llm(self):
        """测试带模拟LLM的范围分析"""
        # 创建模拟LLM管理器
        mock_llm_manager = Mock()

        async def mock_generate(**kwargs):
            return Mock(content=json.dumps({
                "probability": 0.6,
                "reasoning": "测试分析"
            }))

        mock_llm_manager.generate = AsyncMock(side_effect=mock_generate)

        analyzer = ClaimScopeAnalyzer(llm_manager=mock_llm_manager)

        result = await analyzer.analyze_scope(
            claim_text="1. 一种光伏充电系统，包括光伏板和充电控制器。",
            claim_number=1,
            mode="fast"
        )

        assert isinstance(result, ScopeAnalysisResult)
        # 如果LLM成功，方法应该是llm_estimation
        assert result.probability_estimate.method in ["llm_estimation", "heuristic_character_count"]

    @pytest.mark.asyncio
    async def test_compare_claims(self):
        """测试批量比较"""
        analyzer = ClaimScopeAnalyzer(llm_manager=None)

        claims = [
            "1. 一种装置。",
            "2. 根据权利要求1所述的装置，其特征在于包括组件A。",
            "3. 根据权利要求2所述的装置，其特征在于组件A的长度为10mm。"
        ]

        comparisons = await analyzer.compare_claims(claims, mode="fast")

        assert len(comparisons) == 3
        assert all(isinstance(c, ScopeComparison) for c in comparisons)
        # 检查是否有最宽和最窄的标记
        assert any(c.is_broadest for c in comparisons)
        assert any(c.is_narrowest for c in comparisons)


# ==================== 便捷函数测试 ====================

class TestConvenienceFunctions:
    """便捷函数测试"""

    @pytest.mark.asyncio
    async def test_analyze_claim_scope(self):
        """测试便捷分析函数"""
        result = await analyze_claim_scope(
            claim_text="1. 一种装置，包括组件A和组件B。",
            llm_manager=None,
            mode="fast"
        )

        assert isinstance(result, ScopeAnalysisResult)

    def test_format_scope_report(self):
        """测试格式化报告"""
        result = ScopeAnalysisResult(
            claim_text="1. 一种装置，其特征在于...",
            claim_number=1,
            scope_score=ScopeScore(raw_score=65.0, normalized_score=65.0, confidence=0.85),
            probability_estimate=ProbabilityEstimate(
                probability=0.6,
                log_probability=-0.511,
                self_information=0.737,
                method="llm_estimation",
                model_used="deepseek-reasoner"
            ),
            risk_level=RiskLevel.MEDIUM,
            character_count=50,
            word_count=10,
            technical_term_count=3,
            parameter_count=1,
            narrowing_factors=["数量限定"],
            broadening_factors=["开放式表达"],
            recommendations=["建议适度扩大保护范围"]
        )

        report = format_scope_report(result)

        assert "权利要求 1" in report
        assert "65.0/100" in report
        assert "MEDIUM" in report


# ==================== 边界条件测试 ====================

class TestEdgeCases:
    """边界条件测试"""

    @pytest.mark.asyncio
    async def test_empty_claim(self):
        """测试空权利要求"""
        analyzer = ClaimScopeAnalyzer()

        result = await analyzer.analyze_scope("", mode="fast")
        assert result.character_count == 0

    @pytest.mark.asyncio
    async def test_very_long_claim(self):
        """测试超长权利要求"""
        analyzer = ClaimScopeAnalyzer()

        long_text = "一种装置" * 100
        result = await analyzer.analyze_scope(long_text, mode="fast")

        # 长文本应该有较低的范围得分
        assert result.scope_score.normalized_score < 70

    @pytest.mark.asyncio
    async def test_special_characters(self):
        """测试特殊字符"""
        analyzer = ClaimScopeAnalyzer()

        text = "1. 一种装置，包括：组件A（长度10mm）、组件B[温度20-30℃]"
        result = await analyzer.analyze_scope(text, mode="fast")

        assert result is not None


# ==================== 运行测试 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
