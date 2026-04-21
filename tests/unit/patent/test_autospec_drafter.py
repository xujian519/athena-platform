"""
AutoSpec专利说明书撰写框架单元测试
Unit tests for AutoSpec Drafter

基于论文 "AutoSpec: Multi-Agent Patent Specification Drafting" (2025)
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from unittest.mock import MagicMock

from patents.core.ai_services.autospec_drafter import (
    AutoSpecDrafter,
    DraftPhase,
    InventionType,
    InventionUnderstanding,
    QualityReport,
    SectionContent,
    SectionType,
    SpecificationDraft,
    TechnicalFeature,
    draft_patent_specification,
    format_specification,
)

# ==================== 枚举测试 ====================

class TestEnums:
    """枚举类型测试"""

    def test_draft_phase_values(self):
        """测试撰写阶段枚举（9阶段流程）"""
        assert DraftPhase.INVENTION_UNDERSTANDING.value == "invention_understanding"
        assert DraftPhase.PRIOR_ART_SEARCH.value == "prior_art_search"
        assert DraftPhase.COMPARISON_ANALYSIS.value == "comparison_analysis"
        assert DraftPhase.INVENTIVE_POINT.value == "inventive_point"
        assert DraftPhase.SPECIFICATION_DRAFTING.value == "specification_drafting"
        assert DraftPhase.CLAIMS_DRAFTING.value == "claims_drafting"
        assert DraftPhase.EXAMINER_SIMULATION.value == "examiner_simulation"
        assert DraftPhase.MODIFICATION.value == "modification"
        assert DraftPhase.FINAL_CONFIRMATION.value == "final_confirmation"

    def test_section_type_values(self):
        """测试章节类型枚举"""
        assert SectionType.TECHNICAL_FIELD.value == "technical_field"
        assert SectionType.BACKGROUND.value == "background"
        assert SectionType.INVENTION_CONTENT.value == "invention_content"
        assert SectionType.EMBODIMENTS.value == "embodiments"
        assert SectionType.DRAWING_DESCRIPTION.value == "drawing_description"

    def test_invention_type_values(self):
        """测试发明类型枚举"""
        assert InventionType.PRODUCT.value == "product"
        assert InventionType.METHOD.value == "method"
        assert InventionType.DEVICE.value == "device"
        assert InventionType.SYSTEM.value == "system"
        assert InventionType.COMPOSITION.value == "composition"


# ==================== 数据结构测试 ====================

class TestTechnicalFeature:
    """TechnicalFeature 数据结构测试"""

    def test_feature_creation(self):
        """测试技术特征创建"""
        feature = TechnicalFeature(
            feature_id="F1",
            name="光伏板",
            description="将光能转换为电能",
            is_essential=True,
            technical_effect="提供电能来源"
        )
        assert feature.feature_id == "F1"
        assert feature.name == "光伏板"
        assert feature.is_essential is True
        assert feature.technical_effect == "提供电能来源"

    def test_feature_dependencies(self):
        """测试特征依赖"""
        feature = TechnicalFeature(
            feature_id="F2",
            name="控制器",
            description="控制充电过程",
            dependencies=["F1"]
        )
        assert len(feature.dependencies) == 1
        assert "F1" in feature.dependencies


class TestInventionUnderstanding:
    """InventionUnderstanding 数据结构测试"""

    def test_understanding_creation(self):
        """测试发明理解创建"""
        understanding = InventionUnderstanding(
            invention_title="光伏充电系统",
            invention_type=InventionType.SYSTEM,
            technical_field="新能源技术",
            core_innovation="智能充电控制",
            technical_problem="充电效率低",
            technical_solution="采用智能控制算法",
            technical_effects=["提高充电效率", "延长电池寿命"],
            essential_features=[
                TechnicalFeature("F1", "智能控制器", "控制充电过程", True, "提高效率")
            ],
            optional_features=[
                TechnicalFeature("F2", "显示模块", "显示充电状态", False, "用户体验")
            ],
            prior_art_issues=["现有充电方式效率低下", "缺乏智能控制"],
            differentiation=["采用AI算法", "自适应充电策略"]
        )
        assert understanding.invention_title == "光伏充电系统"
        assert understanding.invention_type == InventionType.SYSTEM
        assert len(understanding.technical_effects) == 2
        assert len(understanding.essential_features) == 1
        assert len(understanding.optional_features) == 1

    def test_understanding_to_dict(self):
        """测试发明理解序列化"""
        understanding = InventionUnderstanding(
            invention_title="测试发明",
            invention_type=InventionType.DEVICE,
            technical_field="测试领域",
            core_innovation="测试创新",
            technical_problem="测试问题",
            technical_solution="测试方案",
            technical_effects=["效果1"],
            essential_features=[
                TechnicalFeature("F1", "特征1", "描述1", True, "效果1")
            ],
            optional_features=[],
            prior_art_issues=[],
            differentiation=[]
        )
        result = understanding.to_dict()
        assert result["invention_title"] == "测试发明"
        assert result["invention_type"] == "device"
        assert len(result["essential_features"]) == 1


class TestSectionContent:
    """SectionContent 数据结构测试"""

    def test_section_creation(self):
        """测试章节内容创建"""
        section = SectionContent(
            section_type=SectionType.TECHNICAL_FIELD,
            title="技术领域",
            content="本发明涉及新能源技术领域。",
            word_count=100,
            quality_score=0.9
        )
        assert section.section_type == SectionType.TECHNICAL_FIELD
        assert section.quality_score == 0.9

    def test_section_to_dict(self):
        """测试章节序列化"""
        section = SectionContent(
            section_type=SectionType.BACKGROUND,
            title="背景技术",
            content="背景技术内容",
            issues=["问题1"]
        )
        result = section.to_dict()
        assert result["section_type"] == "background"
        assert "问题1" in result["issues"]


class TestSpecificationDraft:
    """SpecificationDraft 数据结构测试"""

    def test_draft_creation(self):
        """测试说明书草稿创建"""
        draft = SpecificationDraft(
            draft_id="test_001",
            version=1,
            invention_title="测试发明"
        )
        assert draft.draft_id == "test_001"
        assert draft.version == 1
        assert len(draft.sections) == 0

    def test_draft_with_sections(self):
        """测试带章节的草稿"""
        draft = SpecificationDraft(
            draft_id="test_002",
            invention_title="测试发明",
            sections={
                SectionType.TECHNICAL_FIELD: SectionContent(
                    section_type=SectionType.TECHNICAL_FIELD,
                    title="技术领域",
                    content="测试内容"
                )
            },
            claims=["1. 一种装置。"]
        )
        assert len(draft.sections) == 1
        assert len(draft.claims) == 1

    def test_get_full_specification(self):
        """测试获取完整说明书"""
        draft = SpecificationDraft(
            draft_id="test_003",
            invention_title="测试发明",
            sections={
                SectionType.TECHNICAL_FIELD: SectionContent(
                    section_type=SectionType.TECHNICAL_FIELD,
                    title="技术领域",
                    content="本发明涉及测试技术领域。"
                ),
                SectionType.BACKGROUND: SectionContent(
                    section_type=SectionType.BACKGROUND,
                    title="背景技术",
                    content="背景技术内容。"
                )
            },
            claims=["1. 一种测试装置。", "2. 根据权利要求1所述的装置。"]
        )
        full_spec = draft.get_full_specification()
        assert "测试发明" in full_spec
        assert "技术领域" in full_spec
        assert "权利要求书" in full_spec

    def test_draft_to_dict(self):
        """测试草稿序列化"""
        draft = SpecificationDraft(
            draft_id="test_004",
            invention_title="测试发明",
            overall_quality_score=8.5
        )
        result = draft.to_dict()
        assert result["draft_id"] == "test_004"
        assert result["overall_quality_score"] == 8.5


class TestQualityReport:
    """QualityReport 数据结构测试"""

    def test_report_creation(self):
        """测试质量报告创建"""
        report = QualityReport(
            overall_score=8.5,
            dimensions={"completeness": 9.0, "clarity": 8.0},
            critical_issues=[],
            warnings=["警告1"],
            suggestions=["建议1"],
            is_acceptable=True
        )
        assert report.overall_score == 8.5
        assert report.is_acceptable is True

    def test_report_to_dict(self):
        """测试质量报告序列化"""
        report = QualityReport(
            overall_score=7.5,
            dimensions={"completeness": 8.0},
            critical_issues=["问题1"],
            warnings=[],
            suggestions=["建议1"]
        )
        result = report.to_dict()
        assert result["overall_score"] == 7.5
        assert "问题1" in result["critical_issues"]


# ==================== AutoSpecDrafter 测试 ====================

class TestAutoSpecDrafter:
    """AutoSpecDrafter 核心测试"""

    def test_drafter_initialization(self):
        """测试撰写框架初始化"""
        drafter = AutoSpecDrafter()
        assert drafter.llm_manager is None
        assert "understanding" in drafter.MODEL_CONFIG
        assert "planning" in drafter.MODEL_CONFIG

    def test_drafter_with_llm_manager(self):
        """测试带LLM管理器的初始化"""
        mock_llm = MagicMock()
        drafter = AutoSpecDrafter(llm_manager=mock_llm)
        assert drafter.llm_manager == mock_llm

    def test_init_prompts(self):
        """测试提示词初始化"""
        drafter = AutoSpecDrafter()
        assert hasattr(drafter, 'understanding_prompt')
        assert hasattr(drafter, 'quality_check_prompt')
        assert hasattr(drafter, 'generation_prompts')

    def test_heuristic_understanding(self):
        """测试启发式发明理解"""
        drafter = AutoSpecDrafter()
        understanding = drafter._heuristic_understanding(
            "光伏充电系统\n包括光伏板和控制器"
        )
        assert understanding.invention_type == InventionType.DEVICE
        assert understanding.confidence_score == 0.5

    def test_build_understanding(self):
        """测试构建发明理解"""
        drafter = AutoSpecDrafter()
        result = {
            "invention_title": "测试发明",
            "invention_type": "method",
            "technical_field": "测试领域",
            "core_innovation": "测试创新",
            "technical_problem": "测试问题",
            "technical_solution": "测试方案",
            "technical_effects": ["效果1"],
            "essential_features": [
                {"id": "F1", "name": "特征1", "description": "描述1", "effect": "效果1"}
            ],
            "optional_features": []
        }
        understanding = drafter._build_understanding(result, 0.5)
        assert understanding.invention_title == "测试发明"
        assert understanding.invention_type == InventionType.METHOD
        assert len(understanding.essential_features) == 1

    def test_generate_simple_claims(self):
        """测试简单权利要求生成"""
        drafter = AutoSpecDrafter()
        understanding = InventionUnderstanding(
            invention_title="测试装置",
            invention_type=InventionType.DEVICE,
            technical_field="测试领域",
            core_innovation="测试创新",
            technical_problem="测试问题",
            technical_solution="测试方案",
            technical_effects=["效果1"],
            essential_features=[
                TechnicalFeature("F1", "组件A", "描述A", True, "效果A"),
                TechnicalFeature("F2", "组件B", "描述B", True, "效果B")
            ],
            optional_features=[],
            prior_art_issues=[],
            differentiation=[]
        )
        claims = drafter._generate_simple_claims(understanding)
        assert len(claims) >= 1
        assert "测试装置" in claims[0]

    def test_generate_heuristic_section(self):
        """测试启发式章节生成"""
        drafter = AutoSpecDrafter()
        understanding = InventionUnderstanding(
            invention_title="测试发明",
            invention_type=InventionType.DEVICE,
            technical_field="测试领域",
            core_innovation="测试创新",
            technical_problem="测试问题",
            technical_solution="测试方案",
            technical_effects=["效果1"],
            essential_features=[],
            optional_features=[],
            prior_art_issues=["现有问题1"],
            differentiation=["差异化特点"]
        )

        section = drafter._generate_heuristic_section(
            SectionType.TECHNICAL_FIELD, understanding
        )
        assert section.section_type == SectionType.TECHNICAL_FIELD
        assert "测试领域" in section.content

    def test_heuristic_quality_check(self):
        """测试启发式质量检查"""
        drafter = AutoSpecDrafter()

        # 完整草稿
        draft = SpecificationDraft(
            draft_id="test_001",
            invention_title="测试发明",
            sections={
                SectionType.TECHNICAL_FIELD: SectionContent(
                    section_type=SectionType.TECHNICAL_FIELD,
                    title="技术领域",
                    content="技术领域内容，字数超过五十个字",
                    word_count=100
                ),
                SectionType.BACKGROUND: SectionContent(
                    section_type=SectionType.BACKGROUND,
                    title="背景技术",
                    content="背景技术内容，字数超过五十个字",
                    word_count=100
                ),
                SectionType.INVENTION_CONTENT: SectionContent(
                    section_type=SectionType.INVENTION_CONTENT,
                    title="发明内容",
                    content="发明内容，字数超过五十个字",
                    word_count=100
                ),
                SectionType.EMBODIMENTS: SectionContent(
                    section_type=SectionType.EMBODIMENTS,
                    title="具体实施方式",
                    content="具体实施方式内容，字数超过五十个字",
                    word_count=100
                )
            },
            claims=["1. 一种装置。", "2. 根据权利要求1所述的装置。"]
        )

        report = drafter._heuristic_quality_check(draft)
        assert report.overall_score >= 5.0
        assert len(report.dimensions) == 7

    def test_heuristic_quality_check_missing_sections(self):
        """测试缺少章节的质量检查"""
        drafter = AutoSpecDrafter()
        draft = SpecificationDraft(
            draft_id="test_002",
            invention_title="测试发明",
            sections={},  # 无章节
            claims=[]
        )
        report = drafter._heuristic_quality_check(draft)
        assert len(report.critical_issues) > 0
        assert report.is_acceptable is False

    def test_parse_json_response(self):
        """测试JSON响应解析"""
        drafter = AutoSpecDrafter()

        # 带代码块的JSON
        response = '```json\n{"key": "value"}\n```'
        result = drafter._parse_json_response(response)
        assert result is not None
        assert result["key"] == "value"

        # 纯JSON
        response = '{"key": "value"}'
        result = drafter._parse_json_response(response)
        assert result["key"] == "value"

    def test_parse_json_response_invalid(self):
        """测试无效JSON响应"""
        drafter = AutoSpecDrafter()
        result = drafter._parse_json_response("not valid json")
        assert result is None


# ==================== 异步方法测试 ====================

@pytest.mark.asyncio
class TestAsyncMethods:
    """异步方法测试"""

    async def test_quick_draft(self):
        """测试快速撰写"""
        drafter = AutoSpecDrafter()
        draft = await drafter.quick_draft(
            disclosure="光伏充电系统\n包括光伏板和充电控制器",
            skip_quality_check=True
        )
        assert draft.draft_id is not None
        assert draft.invention_title != ""
        assert len(draft.sections) > 0

    async def test_draft_specification_no_llm(self):
        """测试无LLM时的说明书撰写"""
        drafter = AutoSpecDrafter()
        draft = await drafter.draft_specification(
            disclosure="智能充电装置\n包括主控模块和充电接口",
            enable_quality_check=False
        )
        assert draft is not None
        assert len(draft.claims) > 0

    async def test_understand_invention_no_llm(self):
        """测试无LLM时的发明理解"""
        drafter = AutoSpecDrafter()
        understanding = await drafter._understand_invention(
            "光伏充电系统\n包括光伏板和控制器"
        )
        assert understanding is not None
        assert understanding.invention_type == InventionType.DEVICE


# ==================== 便捷函数测试 ====================

class TestConvenienceFunctions:
    """便捷函数测试"""

    @pytest.mark.asyncio
    async def test_draft_patent_specification(self):
        """测试便捷撰写函数"""
        draft = await draft_patent_specification(
            disclosure="测试发明\n包括组件A和组件B",
            llm_manager=None,
            drawing_paths=None
        )
        assert isinstance(draft, SpecificationDraft)

    def test_format_specification(self):
        """测试格式化说明书"""
        draft = SpecificationDraft(
            draft_id="test_001",
            invention_title="测试发明",
            sections={
                SectionType.TECHNICAL_FIELD: SectionContent(
                    section_type=SectionType.TECHNICAL_FIELD,
                    title="技术领域",
                    content="测试领域"
                )
            },
            claims=["1. 一种装置。"]
        )
        formatted = format_specification(draft)
        assert "测试发明" in formatted
        assert "技术领域" in formatted


# ==================== 集成测试标记 ====================

@pytest.mark.integration
class TestAutoSpecIntegration:
    """集成测试（需要实际模型）"""

    @pytest.mark.asyncio
    async def test_full_drafting_pipeline(self):
        """完整撰写流程测试"""
        # 这个测试需要实际的LLM连接
        pytest.skip("需要实际LLM连接")

    @pytest.mark.asyncio
    async def test_quality_iteration(self):
        """质量迭代测试"""
        # 需要完整的系统
        pytest.skip("需要完整系统集成")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
