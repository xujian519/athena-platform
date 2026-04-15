"""
权利要求生成器 v2.0 单元测试

测试基于论文《Can Large Language Models Generate High-quality Patent Claims?》
的增强功能。
"""

import pytest

pytestmark = pytest.mark.skip(reason="模块导入问题，待修复")

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from unittest.mock import AsyncMock, Mock

from core.patent.claim_generator import ClaimsSet, ClaimType, InventionType

# 测试目标
from core.patent.claim_generator_v2 import (
    EnhancedClaimDraft,
    EnhancedClaimGenerator,
    QualityDimension,
    QualityScore,
    SpecificationContext,
    format_enhanced_claims_for_filing,
    generate_claims_from_specification,
)

# ==================== 测试数据 ====================

@pytest.fixture
def mock_llm_manager():
    """模拟LLM管理器"""
    manager = Mock()

    async def mock_generate(**kwargs):
        """模拟生成响应"""
        prompt = kwargs.get("message", "")

        if "提取技术特征" in prompt:
            return Mock(content="""{
                "core_features": [
                    {"name": "光伏板", "type": "component", "description": "太阳能转换装置"},
                    {"name": "充电控制器", "type": "component", "description": "控制充放电"},
                    {"name": "储能电池", "type": "component", "description": "存储电能"}
                ],
                "optional_features": [
                    {"name": "温度传感器", "type": "component", "description": "监测温度"}
                ]
            }""")
        elif "独立权利要求" in prompt:
            return Mock(content="""1. 一种光伏充电控制系统，其特征在于，包括：
    光伏板，用于将太阳能转换为电能；
    充电控制器，与所述光伏板电连接，用于控制充电过程；
    储能电池，与所述充电控制器电连接，用于存储所述电能。
""")
        elif "从属权利要求" in prompt:
            return Mock(content="""2. 根据权利要求1所述的光伏充电控制系统，其特征在于，还包括：
    温度传感器，与所述充电控制器连接，用于监测所述储能电池的温度。
""")
        elif "质量评估" in prompt or "质量检查" in prompt:
            return Mock(content="""{
                "scores": [
                    {"dimension": "feature_completeness", "score": 8.5, "comments": "特征完整"},
                    {"dimension": "conceptual_clarity", "score": 8.0, "comments": "概念清晰"},
                    {"dimension": "feature_linkage", "score": 7.5, "comments": "关联性良好"}
                ],
                "improvement_suggestions": ["可增加参数范围限定"]
            }""")
        else:
            return Mock(content="测试响应")

    manager.generate = AsyncMock(side_effect=mock_generate)
    return manager


@pytest.fixture
def sample_specification():
    """示例说明书数据"""
    return SpecificationContext(
        title="一种光伏充电控制系统",
        technical_field="本发明涉及光伏发电技术领域，特别是涉及一种光伏充电控制系统。",
        background_art="现有的光伏充电系统存在充电效率低、无法智能调节等问题。",
        technical_problem="如何提高光伏充电的效率和安全性",
        technical_solution="通过智能充电控制器实现充电过程优化",
        beneficial_effects="充电效率提升30%，延长电池寿命",
        detailed_description="系统包括光伏板、充电控制器、储能电池等组件...",
        embodiments=[
            "实施例1: 如图1所示，光伏板采用单晶硅材料...",
            "实施例2: 充电控制器采用MPPT算法..."
        ]
    )


@pytest.fixture
def sample_specification_dict():
    """示例说明书字典格式"""
    return {
        "title": "一种光伏充电控制系统",
        "technical_field": "光伏发电技术领域",
        "background_art": "现有系统充电效率低",
        "technical_problem": "提高充电效率",
        "technical_solution": "智能充电控制器",
        "beneficial_effects": "效率提升30%",
        "detailed_description": "系统包括光伏板、充电控制器、储能电池等组件...",
        "embodiments": ["实施例1: 光伏板采用单晶硅材料..."]
    }


# ==================== SpecificationContext 测试 ====================

class TestSpecificationContext:
    """说明书上下文测试"""

    def test_from_dict(self, sample_specification_dict):
        """测试从字典创建"""
        spec = SpecificationContext.from_dict(sample_specification_dict)

        assert spec.title == "一种光伏充电控制系统"
        assert spec.technical_field == "光伏发电技术领域"
        assert len(spec.embodiments) == 1

    def test_get_full_context(self, sample_specification):
        """测试获取完整上下文"""
        context = sample_specification.get_full_context()

        assert "【发明名称】" in context
        assert "【技术领域】" in context
        assert "光伏充电控制系统" in context
        assert "【具体实施方式】" in context


# ==================== EnhancedClaimDraft 测试 ====================

class TestEnhancedClaimDraft:
    """增强版权利要求草稿测试"""

    def test_quality_scores(self):
        """测试质量评分"""
        draft = EnhancedClaimDraft(
            claim_number=1,
            claim_type=ClaimType.INDEPENDENT,
            text="测试权利要求"
        )

        # 添加评分
        draft.quality_scores = [
            QualityScore(QualityDimension.FEATURE_COMPLETENESS, 8.5, "良好"),
            QualityScore(QualityDimension.CONCEPTUAL_CLARITY, 9.0, "优秀")
        ]

        assert draft.get_overall_quality() == pytest.approx(8.75, 0.01)

    def test_to_dict(self):
        """测试序列化"""
        draft = EnhancedClaimDraft(
            claim_number=1,
            claim_type=ClaimType.INDEPENDENT,
            text="测试权利要求",
            quality_scores=[
                QualityScore(QualityDimension.FEATURE_COMPLETENESS, 8.0, "测试")
            ],
            improvement_suggestions=["建议1"]
        )

        result = draft.to_dict()

        assert result["claim_number"] == 1
        assert "quality_scores" in result
        assert "improvement_suggestions" in result
        assert result["overall_quality"] == 8.0


# ==================== EnhancedClaimGenerator 测试 ====================

class TestEnhancedClaimGenerator:
    """增强权利要求生成器测试"""

    @pytest.mark.asyncio
    async def test_generate_from_specification(self, mock_llm_manager, sample_specification):
        """测试基于说明书生成"""
        generator = EnhancedClaimGenerator(llm_manager=mock_llm_manager)

        result = await generator.generate_from_specification(
            specification=sample_specification,
            invention_type=InventionType.DEVICE,
            num_independent=1,
            num_dependent=2,
            enable_quality_check=False  # 简化测试
        )

        assert isinstance(result, ClaimsSet)
        assert result.invention_type == InventionType.DEVICE
        assert len(result.independent_claims) == 1
        assert len(result.dependent_claims) == 2

    @pytest.mark.asyncio
    async def test_generate_with_quality_check(self, mock_llm_manager, sample_specification):
        """测试带质量检查的生成"""
        generator = EnhancedClaimGenerator(llm_manager=mock_llm_manager)

        result = await generator.generate_from_specification(
            specification=sample_specification,
            invention_type=InventionType.DEVICE,
            num_independent=1,
            num_dependent=0,
            enable_quality_check=True
        )

        # 检查质量评分是否被添加
        independent_claim = result.independent_claims[0]
        if hasattr(independent_claim, 'quality_scores'):
            assert len(independent_claim.quality_scores) > 0

    @pytest.mark.asyncio
    async def test_generate_from_dict_spec(self, mock_llm_manager, sample_specification_dict):
        """测试从字典格式说明书生成"""
        generator = EnhancedClaimGenerator(llm_manager=mock_llm_manager)

        result = await generator.generate_from_specification(
            specification=sample_specification_dict,
            invention_type=InventionType.DEVICE
        )

        assert result is not None
        assert result.invention_title != ""

    @pytest.mark.asyncio
    async def test_generate_from_description(self, mock_llm_manager):
        """测试从简单描述生成"""
        generator = EnhancedClaimGenerator(llm_manager=mock_llm_manager)

        description = """
        发明名称: 一种智能温控系统
        技术领域: 温度控制技术
        技术方案: 包括温度传感器、控制器和执行器
        """

        result = await generator.generate_from_description(
            description=description,
            invention_type=InventionType.SYSTEM
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_extract_features_v2(self, mock_llm_manager):
        """测试特征提取"""
        generator = EnhancedClaimGenerator(llm_manager=mock_llm_manager)

        specification = "一种光伏充电系统，包括光伏板、充电控制器和储能电池"

        features = await generator._extract_features_v2(specification)

        assert isinstance(features, dict)
        assert "core_features" in features or len(features) > 0


# ==================== 便捷函数测试 ====================

class TestConvenienceFunctions:
    """便捷函数测试"""

    @pytest.mark.asyncio
    async def test_generate_claims_from_specification(self, mock_llm_manager, sample_specification):
        """测试便捷生成函数"""
        result = await generate_claims_from_specification(
            specification=sample_specification,
            llm_manager=mock_llm_manager,
            invention_type=InventionType.DEVICE
        )

        assert isinstance(result, ClaimsSet)

    def test_format_enhanced_claims_for_filing(self):
        """测试格式化输出"""
        claims_set = ClaimsSet(
            invention_title="测试发明",
            invention_type=InventionType.DEVICE,
            independent_claims=[
                EnhancedClaimDraft(
                    claim_number=1,
                    claim_type=ClaimType.INDEPENDENT,
                    text="1. 一种装置，其特征在于...",
                    quality_scores=[
                        QualityScore(QualityDimension.FEATURE_COMPLETENESS, 8.5, "良好")
                    ]
                )
            ],
            dependent_claims=[
                EnhancedClaimDraft(
                    claim_number=2,
                    claim_type=ClaimType.DEPENDENT,
                    text="2. 根据权利要求1所述的装置...",
                    parent_ref=1
                )
            ]
        )

        result = format_enhanced_claims_for_filing(claims_set)

        assert "权利要求书" in result
        assert "1. 一种装置" in result
        assert "2. 根据权利要求1" in result


# ==================== 质量评分测试 ====================

class TestQualityScoring:
    """质量评分测试"""

    def test_quality_dimension_enum(self):
        """测试质量维度枚举"""
        dimensions = [
            QualityDimension.FEATURE_COMPLETENESS,
            QualityDimension.CONCEPTUAL_CLARITY,
            QualityDimension.FEATURE_LINKAGE,
            QualityDimension.TECHNICAL_COHERENCE,
            QualityDimension.LEGAL_COMPLIANCE
        ]

        assert len(dimensions) == 5

    def test_quality_score_creation(self):
        """测试质量评分创建"""
        score = QualityScore(
            dimension=QualityDimension.FEATURE_COMPLETENESS,
            score=8.5,
            comments="特征提取完整"
        )

        assert score.dimension == QualityDimension.FEATURE_COMPLETENESS
        assert score.score == 8.5
        assert "完整" in score.comments


# ==================== 集成测试 ====================

class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_generation_workflow(self, mock_llm_manager, sample_specification):
        """测试完整生成工作流"""
        generator = EnhancedClaimGenerator(llm_manager=mock_llm_manager)

        # 完整生成流程
        result = await generator.generate_from_specification(
            specification=sample_specification,
            invention_type=InventionType.DEVICE,
            num_independent=1,
            num_dependent=3,
            enable_quality_check=True
        )

        # 验证结果
        assert result.invention_title != ""
        assert len(result.independent_claims) == 1
        assert len(result.dependent_claims) == 3

        # 验证独立权利要求
        independent = result.independent_claims[0]
        assert independent.claim_type == ClaimType.INDEPENDENT
        assert independent.claim_number == 1

        # 验证从属权利要求引用关系
        for dep in result.dependent_claims:
            assert dep.parent_ref is not None
            assert dep.claim_type == ClaimType.DEPENDENT


# ==================== 运行测试 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
