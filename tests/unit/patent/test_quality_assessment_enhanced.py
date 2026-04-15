"""
P2-3: 综合质量评估增强系统 - 单元测试

测试覆盖:
1. 枚举类型测试
2. 数据结构测试
3. 维度评估测试
4. 风险分析测试
5. 改进建议测试
6. 完整评估测试
"""

import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# 导入被测模块
from core.patent.ai_services.quality_assessment_enhanced import (
    AssessmentType,
    BenchmarkComparison,
    # 核心类
    DimensionEvaluator,
    # 数据结构
    DimensionScore,
    EnhancedQualityAssessment,
    EnhancedQualityAssessor,
    ImprovementGenerator,
    ImprovementPriority,
    ImprovementSuggestion,
    # 枚举类型
    QualityDimension,
    QualityGrade,
    QualityRisk,
    RiskAnalyzer,
    RiskLevel,
    # 便捷函数
    assess_patent_quality,
    format_assessment_report,
)

# ============================================================================
# 枚举类型测试
# ============================================================================

class TestEnums:
    """枚举类型测试"""

    def test_quality_dimension_values(self):
        """测试质量维度枚举值"""
        assert QualityDimension.TECHNICAL_VALUE.value == "technical_value"
        assert QualityDimension.LEGAL_STABILITY.value == "legal_stability"
        assert QualityDimension.COMMERCIAL_VALUE.value == "commercial_value"
        assert QualityDimension.SCOPE_CLARITY.value == "scope_clarity"
        assert QualityDimension.DISCLOSURE_QUALITY.value == "disclosure_quality"
        assert QualityDimension.INNOVATION_LEVEL.value == "innovation_level"
        assert QualityDimension.ENFORCEABILITY.value == "enforceability"
        assert QualityDimension.MARKET_RELEVANCE.value == "market_relevance"

    def test_quality_grade_values(self):
        """测试质量等级枚举值"""
        assert QualityGrade.EXCELLENT.value == "A+"
        assert QualityGrade.VERY_GOOD.value == "A"
        assert QualityGrade.GOOD.value == "B+"
        assert QualityGrade.AVERAGE.value == "B"
        assert QualityGrade.BELOW_AVERAGE.value == "C+"
        assert QualityGrade.POOR.value == "C"
        assert QualityGrade.VERY_POOR.value == "D"
        assert QualityGrade.CRITICAL.value == "F"

    def test_risk_level_values(self):
        """测试风险等级枚举值"""
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.CRITICAL.value == "critical"

    def test_improvement_priority_values(self):
        """测试改进优先级枚举值"""
        assert ImprovementPriority.URGENT.value == "urgent"
        assert ImprovementPriority.HIGH.value == "high"
        assert ImprovementPriority.MEDIUM.value == "medium"
        assert ImprovementPriority.LOW.value == "low"
        assert ImprovementPriority.OPTIONAL.value == "optional"

    def test_assessment_type_values(self):
        """测试评估类型枚举值"""
        assert AssessmentType.FULL.value == "full"
        assert AssessmentType.QUICK.value == "quick"
        assert AssessmentType.CLAIMS_ONLY.value == "claims"
        assert AssessmentType.TECHNICAL.value == "technical"
        assert AssessmentType.LEGAL.value == "legal"
        assert AssessmentType.COMMERCIAL.value == "commercial"


# ============================================================================
# 数据结构测试
# ============================================================================

class TestDataStructures:
    """数据结构测试"""

    def test_dimension_score_creation(self):
        """测试维度分数创建"""
        score = DimensionScore(
            dimension=QualityDimension.TECHNICAL_VALUE,
            score=75.0,
            weight=0.2,
            weighted_score=15.0,
            confidence=0.8,
            analysis="技术价值良好",
            key_factors=["创新点明确", "实施例充分"]
        )

        assert score.dimension == QualityDimension.TECHNICAL_VALUE
        assert score.score == 75.0
        assert score.weight == 0.2
        assert len(score.key_factors) == 2

    def test_dimension_score_to_dict(self):
        """测试维度分数转字典"""
        score = DimensionScore(
            dimension=QualityDimension.LEGAL_STABILITY,
            score=80.0,
            weight=0.2,
            weighted_score=16.0,
            confidence=0.85,
            analysis="法律稳定性好",
            key_factors=[]
        )

        result = score.to_dict()
        assert result["dimension"] == "legal_stability"
        assert result["score"] == 80.0
        assert result["weight"] == 0.2

    def test_quality_risk_creation(self):
        """测试质量风险创建"""
        risk = QualityRisk(
            risk_id="risk_001",
            risk_type="low_score",
            dimension=QualityDimension.COMMERCIAL_VALUE,
            severity=RiskLevel.HIGH,
            description="商业价值偏低",
            impact="可能影响专利价值",
            mitigation="加强市场布局",
            likelihood=0.7
        )

        assert risk.risk_id == "risk_001"
        assert risk.severity == RiskLevel.HIGH
        assert risk.likelihood == 0.7

    def test_improvement_suggestion_creation(self):
        """测试改进建议创建"""
        suggestion = ImprovementSuggestion(
            suggestion_id="sug_001",
            dimension=QualityDimension.SCOPE_CLARITY,
            priority=ImprovementPriority.HIGH,
            title="提高权利要求清晰度",
            description="简化权利要求语言",
            current_state="权利要求过长",
            target_state="语言简洁清晰",
            action_items=["简化语言", "定义术语"],
            expected_improvement=15.0,
            effort_level="medium",
            timeline="1-2周"
        )

        assert suggestion.suggestion_id == "sug_001"
        assert suggestion.priority == ImprovementPriority.HIGH
        assert len(suggestion.action_items) == 2

    def test_benchmark_comparison_creation(self):
        """测试基准对比创建"""
        bench = BenchmarkComparison(
            metric="technical_value",
            patent_value=75.0,
            benchmark_avg=65.0,
            benchmark_top=85.0,
            percentile=72.5,
            status="above"
        )

        assert bench.metric == "technical_value"
        assert bench.patent_value == 75.0
        assert bench.status == "above"

    def test_enhanced_quality_assessment_creation(self):
        """测试增强评估结果创建"""
        result = EnhancedQualityAssessment(
            assessment_id="qa_001",
            patent_number="CN1234567A",
            assessment_type=AssessmentType.FULL,
            timestamp=datetime.now(),
            overall_score=75.5,
            overall_grade=QualityGrade.GOOD,
            confidence_level=0.8,
            dimension_scores=[],
            risks=[],
            overall_risk_level=RiskLevel.MEDIUM,
            improvements=[],
            benchmarks=[],
            predicted_validity=0.85,
            predicted_enforceability=0.80,
            predicted_litigation_risk=0.15,
            processing_time=0.5,
            model_used="qwen3.5"
        )

        assert result.assessment_id == "qa_001"
        assert result.overall_score == 75.5
        assert result.overall_grade == QualityGrade.GOOD


# ============================================================================
# 维度评估器测试
# ============================================================================

class TestDimensionEvaluator:
    """维度评估器测试"""

    @pytest.fixture
    def evaluator(self):
        """创建评估器实例"""
        return DimensionEvaluator()

    @pytest.fixture
    def sample_patent_data(self):
        """创建样本专利数据"""
        return {
            "technical_features": ["特征1", "特征2", "特征3", "特征4", "特征5"],
            "technical_field": "人工智能",
            "embodiments": ["实施例1", "实施例2", "实施例3"],
            "claims": [
                {"type": "independent", "text": "一种方法，包括步骤A"},
                {"type": "dependent", "text": "根据权利要求1的方法，还包括步骤B"},
                {"type": "dependent", "text": "根据权利要求1的方法，还包括步骤C"}
            ],
            "description": "这是一段较长的说明书内容" * 100,
            "figures": ["图1", "图2", "图3", "图4", "图5"],
            "citations": ["文献1", "文献2", "文献3"],
            "applications": ["应用1", "应用2", "应用3"],
            "family_members": ["US专利", "EP专利"],
            "keywords": ["新的", "改进", "优化"],
            "technical_problems": ["问题1", "问题2"],
            "filing_date": "2024-01-15"
        }

    def test_dimension_weights(self, evaluator):
        """测试维度权重配置"""
        weights = evaluator.DIMENSION_WEIGHTS

        # 检查所有维度都有权重
        assert len(weights) == 8

        # 检查权重总和为1
        total = sum(weights.values())
        assert abs(total - 1.0) < 0.01

    @pytest.mark.asyncio
    async def test_evaluate_technical_value(self, evaluator, sample_patent_data):
        """测试技术价值评估"""
        score, confidence, analysis, factors = await evaluator._evaluate_technical_value(
            sample_patent_data
        )

        assert 0 <= score <= 100
        assert 0 <= confidence <= 1
        assert isinstance(analysis, str)
        assert isinstance(factors, list)

    @pytest.mark.asyncio
    async def test_evaluate_legal_stability(self, evaluator, sample_patent_data):
        """测试法律稳定性评估"""
        score, confidence, analysis, factors = await evaluator._evaluate_legal_stability(
            sample_patent_data
        )

        assert 0 <= score <= 100
        assert isinstance(factors, list)

    @pytest.mark.asyncio
    async def test_evaluate_dimension(self, evaluator, sample_patent_data):
        """测试维度评估"""
        result = await evaluator.evaluate_dimension(
            QualityDimension.TECHNICAL_VALUE,
            sample_patent_data
        )

        assert isinstance(result, DimensionScore)
        assert result.dimension == QualityDimension.TECHNICAL_VALUE
        assert 0 <= result.score <= 100


# ============================================================================
# 风险分析器测试
# ============================================================================

class TestRiskAnalyzer:
    """风险分析器测试"""

    @pytest.fixture
    def analyzer(self):
        """创建分析器实例"""
        return RiskAnalyzer()

    @pytest.fixture
    def sample_dimension_scores(self):
        """创建样本维度分数"""
        return [
            DimensionScore(
                dimension=QualityDimension.TECHNICAL_VALUE,
                score=75.0,
                weight=0.2,
                weighted_score=15.0,
                confidence=0.8,
                analysis="技术价值良好",
                key_factors=[]
            ),
            DimensionScore(
                dimension=QualityDimension.COMMERCIAL_VALUE,
                score=45.0,  # 低分
                weight=0.15,
                weighted_score=6.75,
                confidence=0.7,
                analysis="商业价值偏低",
                key_factors=[]
            )
        ]

    @pytest.fixture
    def sample_patent_data(self):
        """创建样本专利数据"""
        return {
            "claims": [
                {"type": "independent", "text": "权利要求1"}
            ],
            "description": "短描述"
        }

    @pytest.mark.asyncio
    async def test_analyze_risks(self, analyzer, sample_dimension_scores, sample_patent_data):
        """测试风险分析"""
        risks, overall_level = await analyzer.analyze_risks(
            sample_dimension_scores,
            sample_patent_data
        )

        assert isinstance(risks, list)
        assert isinstance(overall_level, RiskLevel)

    def test_calculate_overall_risk(self, analyzer):
        """测试总体风险计算"""
        # 无风险
        level = analyzer._calculate_overall_risk([])
        assert level == RiskLevel.LOW

        # 高风险
        risks = [
            QualityRisk(
                risk_id="r1",
                risk_type="test",
                dimension=QualityDimension.TECHNICAL_VALUE,
                severity=RiskLevel.HIGH,
                description="高风险",
                impact="影响大",
                mitigation="缓解措施",
                likelihood=0.8
            )
        ]
        level = analyzer._calculate_overall_risk(risks)
        assert level in [RiskLevel.HIGH, RiskLevel.MEDIUM]


# ============================================================================
# 改进建议生成器测试
# ============================================================================

class TestImprovementGenerator:
    """改进建议生成器测试"""

    @pytest.fixture
    def generator(self):
        """创建生成器实例"""
        return ImprovementGenerator()

    @pytest.fixture
    def sample_data(self):
        """创建样本数据"""
        dimension_scores = [
            DimensionScore(
                dimension=QualityDimension.COMMERCIAL_VALUE,
                score=50.0,
                weight=0.15,
                weighted_score=7.5,
                confidence=0.7,
                analysis="商业价值偏低",
                key_factors=[]
            )
        ]

        risks = [
            QualityRisk(
                risk_id="r1",
                risk_type="low_score",
                dimension=QualityDimension.COMMERCIAL_VALUE,
                severity=RiskLevel.HIGH,
                description="商业价值风险",
                impact="影响专利价值",
                mitigation="加强商业布局",
                likelihood=0.7
            )
        ]

        patent_data = {"claims": [{"type": "independent", "text": "权利要求"}]}

        return dimension_scores, risks, patent_data

    @pytest.mark.asyncio
    async def test_generate_suggestions(self, generator, sample_data):
        """测试生成改进建议"""
        dimension_scores, risks, patent_data = sample_data

        suggestions = await generator.generate_suggestions(
            dimension_scores,
            risks,
            patent_data
        )

        assert isinstance(suggestions, list)
        assert len(suggestions) <= 10

        for s in suggestions:
            assert isinstance(s, ImprovementSuggestion)


# ============================================================================
# 增强质量评估系统测试
# ============================================================================

class TestEnhancedQualityAssessor:
    """增强质量评估系统测试"""

    @pytest.fixture
    def assessor(self):
        """创建评估器实例"""
        return EnhancedQualityAssessor()

    @pytest.fixture
    def sample_patent_data(self):
        """创建样本专利数据"""
        return {
            "technical_features": ["特征1", "特征2", "特征3"],
            "technical_field": "人工智能",
            "embodiments": ["实施例1", "实施例2"],
            "claims": [
                {"type": "independent", "text": "一种方法，包括步骤A" * 5},
                {"type": "dependent", "text": "根据权利要求1的方法" * 3},
                {"type": "dependent", "text": "根据权利要求1的方法" * 3}
            ],
            "description": "说明书内容" * 200,
            "figures": ["图1", "图2", "图3"],
            "citations": ["文献1", "文献2"],
            "applications": ["应用1", "应用2"],
            "family_members": ["US专利"],
            "keywords": ["新的", "改进"],
            "technical_problems": ["问题1"],
            "filing_date": "2024-06-01"
        }

    def test_assessor_initialization(self, assessor):
        """测试评估器初始化"""
        assert assessor.dimension_evaluator is not None
        assert assessor.risk_analyzer is not None
        assert assessor.improvement_generator is not None

    def test_get_dimensions_for_type(self, assessor):
        """测试获取评估维度"""
        # 完整评估
        dims = assessor._get_dimensions_for_type(AssessmentType.FULL)
        assert len(dims) == 8

        # 快速评估
        dims = assessor._get_dimensions_for_type(AssessmentType.QUICK)
        assert len(dims) == 3

        # 权利要求评估
        dims = assessor._get_dimensions_for_type(AssessmentType.CLAIMS_ONLY)
        assert len(dims) == 3

    def test_score_to_grade(self, assessor):
        """测试分数转等级"""
        assert assessor._score_to_grade(95) == QualityGrade.EXCELLENT
        assert assessor._score_to_grade(85) == QualityGrade.VERY_GOOD
        assert assessor._score_to_grade(75) == QualityGrade.GOOD
        assert assessor._score_to_grade(65) == QualityGrade.AVERAGE
        assert assessor._score_to_grade(55) == QualityGrade.BELOW_AVERAGE
        assert assessor._score_to_grade(45) == QualityGrade.POOR
        assert assessor._score_to_grade(35) == QualityGrade.VERY_POOR
        assert assessor._score_to_grade(25) == QualityGrade.CRITICAL

    @pytest.mark.asyncio
    async def test_assess_full(self, assessor, sample_patent_data):
        """测试完整评估"""
        result = await assessor.assess(
            patent_number="CN1234567A",
            patent_data=sample_patent_data,
            assessment_type=AssessmentType.FULL
        )

        assert isinstance(result, EnhancedQualityAssessment)
        assert result.patent_number == "CN1234567A"
        assert result.assessment_type == AssessmentType.FULL
        assert 0 <= result.overall_score <= 100
        assert isinstance(result.overall_grade, QualityGrade)
        assert len(result.dimension_scores) == 8

    @pytest.mark.asyncio
    async def test_assess_quick(self, assessor, sample_patent_data):
        """测试快速评估"""
        result = await assessor.assess(
            patent_number="CN1234567A",
            patent_data=sample_patent_data,
            assessment_type=AssessmentType.QUICK
        )

        assert result.assessment_type == AssessmentType.QUICK
        assert len(result.dimension_scores) == 3

    def test_generate_predictions(self, assessor):
        """测试生成预测"""
        dimension_scores = [
            DimensionScore(
                dimension=QualityDimension.LEGAL_STABILITY,
                score=80.0,
                weight=0.2,
                weighted_score=16.0,
                confidence=0.8,
                analysis="法律稳定性好",
                key_factors=[]
            ),
            DimensionScore(
                dimension=QualityDimension.ENFORCEABILITY,
                score=75.0,
                weight=0.05,
                weighted_score=3.75,
                confidence=0.75,
                analysis="可执行性良好",
                key_factors=[]
            )
        ]

        risks = []

        predictions = assessor._generate_predictions(dimension_scores, risks)

        assert "validity" in predictions
        assert "enforceability" in predictions
        assert "litigation_risk" in predictions
        assert 0 <= predictions["validity"] <= 1
        assert 0 <= predictions["enforceability"] <= 1
        assert 0 <= predictions["litigation_risk"] <= 1

    def test_get_stats(self, assessor):
        """测试统计信息"""
        stats = assessor.get_stats()

        assert "cache_size" in stats
        assert "dimensions" in stats
        assert "grade_levels" in stats


# ============================================================================
# 便捷函数测试
# ============================================================================

class TestConvenienceFunctions:
    """便捷函数测试"""

    @pytest.fixture
    def sample_patent_data(self):
        """创建样本专利数据"""
        return {
            "technical_features": ["特征1", "特征2"],
            "technical_field": "电子",
            "claims": [{"type": "independent", "text": "权利要求"}],
            "description": "说明书" * 50,
            "figures": ["图1"]
        }

    @pytest.mark.asyncio
    async def test_assess_patent_quality(self, sample_patent_data):
        """测试评估便捷函数"""
        result = await assess_patent_quality(
            patent_number="CN1234567A",
            patent_data=sample_patent_data,
            assessment_type=AssessmentType.QUICK
        )

        assert isinstance(result, EnhancedQualityAssessment)
        assert result.patent_number == "CN1234567A"

    def test_format_assessment_report(self, sample_patent_data):
        """测试格式化报告"""
        # 创建模拟结果
        result = EnhancedQualityAssessment(
            assessment_id="qa_test",
            patent_number="CN1234567A",
            assessment_type=AssessmentType.FULL,
            timestamp=datetime.now(),
            overall_score=75.0,
            overall_grade=QualityGrade.GOOD,
            confidence_level=0.8,
            dimension_scores=[
                DimensionScore(
                    dimension=QualityDimension.TECHNICAL_VALUE,
                    score=80.0,
                    weight=0.2,
                    weighted_score=16.0,
                    confidence=0.8,
                    analysis="技术价值良好",
                    key_factors=[]
                )
            ],
            risks=[],
            overall_risk_level=RiskLevel.LOW,
            improvements=[],
            benchmarks=[],
            predicted_validity=0.85,
            predicted_enforceability=0.80,
            predicted_litigation_risk=0.15,
            processing_time=0.5,
            model_used="qwen3.5"
        )

        formatted = format_assessment_report(result)

        assert "专利质量评估报告" in formatted
        assert "CN1234567A" in formatted
        assert "75.0" in formatted
        assert "B+" in formatted


# ============================================================================
# 边界条件测试
# ============================================================================

class TestEdgeCases:
    """边界条件测试"""

    @pytest.fixture
    def assessor(self):
        """创建评估器实例"""
        return EnhancedQualityAssessor()

    @pytest.mark.asyncio
    async def test_empty_patent_data(self, assessor):
        """测试空专利数据"""
        result = await assessor.assess(
            patent_number="CN0000000A",
            patent_data={},
            assessment_type=AssessmentType.QUICK
        )

        assert result is not None
        assert result.overall_score >= 0

    @pytest.mark.asyncio
    async def test_minimal_claims(self, assessor):
        """测试最少权利要求"""
        patent_data = {
            "claims": [{"type": "independent", "text": "一个权利要求"}],
            "description": "短描述"
        }

        result = await assessor.assess(
            patent_number="CN1111111A",
            patent_data=patent_data
        )

        assert result is not None
        # 应该有风险提示
        assert len(result.risks) > 0

    def test_score_boundary(self, assessor):
        """测试分数边界"""
        assert assessor._score_to_grade(0) == QualityGrade.CRITICAL
        assert assessor._score_to_grade(100) == QualityGrade.EXCELLENT
        assert assessor._score_to_grade(90) == QualityGrade.EXCELLENT
        assert assessor._score_to_grade(89.9) == QualityGrade.VERY_GOOD


# ============================================================================
# 集成测试
# ============================================================================

class TestIntegration:
    """集成测试"""

    @pytest.fixture
    def assessor(self):
        """创建评估器实例"""
        return EnhancedQualityAssessor()

    @pytest.fixture
    def complete_patent_data(self):
        """创建完整专利数据"""
        return {
            "technical_features": [
                "特征1：使用深度学习",
                "特征2：多模态融合",
                "特征3：注意力机制",
                "特征4：端到端训练",
                "特征5：实时推理"
            ],
            "technical_field": "人工智能深度学习",
            "embodiments": [
                "实施例1：图像识别应用",
                "实施例2：语音识别应用",
                "实施例3：自然语言处理"
            ],
            "claims": [
                {"type": "independent", "text": "一种基于深度学习的多模态识别方法，包括：步骤A，提取图像特征；步骤B，提取语音特征；步骤C，融合多模态特征；步骤D，输出识别结果"},
                {"type": "dependent", "text": "根据权利要求1的方法，其中步骤C使用注意力机制"},
                {"type": "dependent", "text": "根据权利要求1的方法，其中步骤A使用卷积神经网络"},
                {"type": "dependent", "text": "根据权利要求2的方法，注意力权重通过Softmax计算"},
                {"type": "independent", "text": "一种多模态识别系统，包括：图像处理模块，语音处理模块，融合模块"}
            ],
            "description": "详细说明书内容" * 500,
            "figures": ["图1：系统架构图", "图2：流程图", "图3：网络结构图", "图4：实验结果图", "图5：应用场景图"],
            "citations": ["文献1", "文献2", "文献3"],
            "applications": ["人脸识别", "智能安防", "人机交互"],
            "family_members": ["US12345678B2", "EP3456789A1", "JP4567890A"],
            "keywords": ["新的多模态方法", "改进的融合算法", "优化的注意力机制"],
            "technical_problems": ["单模态识别准确率低", "多模态融合效率差"],
            "invention_type": "method",
            "detection_difficulty": "medium",
            "filing_date": "2024-01-15"
        }

    @pytest.mark.asyncio
    async def test_full_assessment_workflow(self, assessor, complete_patent_data):
        """测试完整评估工作流"""
        result = await assessor.assess(
            patent_number="CN12345678A",
            patent_data=complete_patent_data,
            assessment_type=AssessmentType.FULL
        )

        # 验证基本属性
        assert result.patent_number == "CN12345678A"
        assert result.assessment_type == AssessmentType.FULL

        # 验证维度评估
        assert len(result.dimension_scores) == 8
        for ds in result.dimension_scores:
            assert 0 <= ds.score <= 100

        # 验证预测值
        assert 0 <= result.predicted_validity <= 1
        assert 0 <= result.predicted_enforceability <= 1
        assert 0 <= result.predicted_litigation_risk <= 1

        # 验证处理时间
        assert result.processing_time >= 0

    @pytest.mark.asyncio
    async def test_different_assessment_types(self, assessor, complete_patent_data):
        """测试不同评估类型"""
        types = [
            AssessmentType.FULL,
            AssessmentType.QUICK,
            AssessmentType.TECHNICAL,
            AssessmentType.LEGAL,
            AssessmentType.COMMERCIAL
        ]

        for atype in types:
            result = await assessor.assess(
                patent_number="CN12345678A",
                patent_data=complete_patent_data,
                assessment_type=atype
            )

            assert result.assessment_type == atype


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
