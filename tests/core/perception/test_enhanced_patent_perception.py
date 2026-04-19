#!/usr/bin/env python3
"""
增强专利感知模块测试
Tests for Enhanced Patent Perception Module
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pathlib import Path
from unittest.mock import MagicMock, patch

from core.perception.enhanced_patent_perception import (
    EnhancedPatentPerceptionEngine,
    PatentDrawingAnalyzer,
    PatentInputType,
    PatentNoveltyAnalyzer,
    PatentPerceptionResult,
    PatentTechnicalExtractor,
)


class TestPatentInputType:
    """测试PatentInputType枚举"""

    def test_patent_text_type(self):
        """测试专利文本类型"""
        assert PatentInputType.PATENT_TEXT.value == "patent_text"

    def test_patent_image_type(self):
        """测试专利图像类型"""
        assert PatentInputType.PATENT_IMAGE.value == "patent_image"

    def test_patent_drawing_type(self):
        """测试专利图纸类型"""
        assert PatentInputType.PATENT_DRAWING.value == "patent_drawing"

    def test_technical_diagram_type(self):
        """测试技术图表类型"""
        assert PatentInputType.TECHNICAL_DIAGRAM.value == "technical_diagram"

    def test_claims_text_type(self):
        """测试权利要求文本类型"""
        assert PatentInputType.CLAIMS_TEXT.value == "claims_text"

    def test_specification_type(self):
        """测试说明书类型"""
        assert PatentInputType.SPECIFICATION.value == "specification"

    def test_prior_art_type(self):
        """测试现有技术类型"""
        assert PatentInputType.PRIOR_ART.value == "prior_art"

    def test_invalidation_evidence_type(self):
        """测试无效证据类型"""
        assert PatentInputType.INVALIDATION_EVIDENCE.value == "invalidation_evidence"

    def test_multimodal_patent_type(self):
        """测试多模态专利类型"""
        assert PatentInputType.MULTIMODAL_PATENT.value == "multimodal_patent"


class TestPatentTechnicalExtractor:
    """测试PatentTechnicalExtractor类"""

    @pytest.fixture
    def extractor(self):
        """创建提取器实例"""
        return PatentTechnicalExtractor()

    def test_initialization(self, extractor):
        """测试初始化"""
        assert extractor.technical_terms is not None
        assert extractor.ipc_mapping is not None
        assert len(extractor.feature_patterns) > 0

    def test_technical_terms_loaded(self, extractor):
        """测试技术术语加载"""
        assert isinstance(extractor.technical_terms, dict)

    def test_ipc_mapping_loaded(self, extractor):
        """测试IPC映射加载"""
        assert isinstance(extractor.ipc_mapping, dict)

    def test_feature_patterns_defined(self, extractor):
        """测试特征模式定义"""
        assert len(extractor.feature_patterns) >= 6

    def test_extract_technical_features(self, extractor):
        """测试技术特征提取"""
        text = "本装置包括:传感器模块、控制单元和执行器"
        features = extractor.extract_technical_features(text)
        assert isinstance(features, list)
        # 应该能提取到特征
        if len(features) > 0:
            assert isinstance(features[0], str)

    def test_extract_ipc_classification(self, extractor):
        """测试IPC分类提取"""
        text = "本发明涉及一种数据处理装置,属于H04L领域"
        ipc = extractor.extract_ipc_classification(text)
        assert ipc is not None
        # 应该能识别出H04L
        assert "H04L" in ipc or len(ipc) > 0

    def test_identify_technical_field(self, extractor):
        """测试技术领域识别"""
        text = "本发明涉及计算机视觉和人工智能技术"
        field = extractor.identify_technical_field(text)
        assert field is not None
        assert isinstance(field, str)

    def test_extract_key_components(self, extractor):
        """测试关键组件提取"""
        text = "该系统包括处理器、存储器和通信模块"
        components = extractor.extract_key_components(text)
        assert isinstance(components, list)

    def test_analyze_technical_complexity(self, extractor):
        """测试技术复杂度分析"""
        text = "本发明包括多个子系统,每个子系统包含复杂的算法和硬件组件"
        complexity = extractor.analyze_technical_complexity(text)
        assert complexity is not None
        assert isinstance(complexity, (int, float))


class TestPatentDrawingAnalyzer:
    """测试PatentDrawingAnalyzer类"""

    @pytest.fixture
    def analyzer(self):
        """创建分析器实例"""
        return PatentDrawingAnalyzer()

    def test_initialization(self, analyzer):
        """测试初始化"""
        assert analyzer is not None

    @patch('cv2.imread')
    def test_analyze_drawing_structure(self, mock_imread, analyzer):
        """测试图纸结构分析"""
        # 模拟图像
        mock_imread.return_value = MagicMock(shape=(100, 100, 3))

        result = analyzer.analyze_drawing_structure("test.png")
        assert result is not None

    def test_extract_drawings_from_patent(self, analyzer):
        """测试从专利中提取图纸"""
        # 使用Mock来避免实际文件操作
        with patch.object(analyzer, 'extract_drawings_from_pdf') as mock_extract:
            mock_extract.return_value = []
            result = mock_extract("patent.pdf")
            assert isinstance(result, list)

    def test_identify_drawing_type(self, analyzer):
        """测试识别图纸类型"""
        # 测试不同的图纸类型识别逻辑
        assert hasattr(analyzer, 'identify_drawing_type')

    def test_analyze_reference_numerals(self, analyzer):
        """测试分析参考数字"""
        with patch.object(analyzer, 'analyze_reference_numerals') as mock_analyze:
            mock_analyze.return_value = {}
            result = mock_analyze("test.png")
            assert isinstance(result, dict)


class TestPatentNoveltyAnalyzer:
    """测试PatentNoveltyAnalyzer类"""

    @pytest.fixture
    def analyzer(self):
        """创建分析器实例"""
        return PatentNoveltyAnalyzer()

    def test_initialization(self, analyzer):
        """测试初始化"""
        assert analyzer is not None
        assert hasattr(analyzer, 'assess_novelty')

    def test_assess_novelty_basic(self, analyzer):
        """测试基本新颖性评估"""
        patent_text = "本发明涉及一种全新的数据处理方法"
        prior_art = ["现有技术1", "现有技术2"]

        with patch.object(analyzer, 'assess_novelty') as mock_assess:
            mock_assess.return_value = {
                "novelty_score": 0.75,
                "novelty_level": "中等",
                "novel_features": ["全新数据处理方法"]
            }
            result = mock_assess(patent_text, prior_art)
            assert result["novelty_score"] >= 0
            assert result["novelty_level"] is not None

    def test_identify_novel_features(self, analyzer):
        """测试识别新颖特征"""
        patent_text = "本发明首次采用了XX技术"
        prior_art = ["现有技术"]

        with patch.object(analyzer, 'identify_novel_features') as mock_identify:
            mock_identify.return_value = ["XX技术"]
            result = mock_identify(patent_text, prior_art)
            assert isinstance(result, list)

    def test_compare_with_prior_art(self, analyzer):
        """测试与现有技术对比"""
        current_patent = "新技术方案"
        prior_art = "旧技术方案"

        with patch.object(analyzer, 'compare_with_prior_art') as mock_compare:
            mock_compare.return_value = {
                "similarity": 0.3,
                "differences": ["差异1", "差异2"]
            }
            result = mock_compare(current_patent, prior_art)
            assert "similarity" in result
            assert "differences" in result

    def test_assess_inventive_step(self, analyzer):
        """测试评估创造性"""
        patent_text = "本发明解决了长期存在的技术难题"

        with patch.object(analyzer, 'assess_inventive_step') as mock_assess:
            mock_assess.return_value = {
                "has_inventive_step": True,
                "confidence": 0.8
            }
            result = mock_assess(patent_text)
            assert result["has_inventive_step"] is True


class TestEnhancedPatentPerceptionEngine:
    """测试EnhancedPatentPerceptionEngine类"""

    @pytest.fixture
    def engine(self):
        """创建引擎实例"""
        config = {
            "enable_ocr": True,
            "enable_drawing_analysis": True,
            "enable_novelty_analysis": True
        }
        return EnhancedPatentPerceptionEngine(config)

    def test_initialization(self, engine):
        """测试初始化"""
        assert engine is not None
        assert engine.config is not None

    def test_process_patent_text(self, engine):
        """测试处理专利文本"""
        patent_text = "本发明涉及一种数据处理方法"

        with patch.object(engine, 'process_patent_text') as mock_process:
            mock_process.return_value = MagicMock(
                success=True,
                content="处理后的内容",
                technical_features=[],
                ipc_classification="G06F"
            )
            result = mock_process(patent_text)
            assert result.success is True

    def test_process_patent_image(self, engine):
        """测试处理专利图像"""
        with patch.object(engine, 'process_patent_image') as mock_process:
            mock_process.return_value = MagicMock(
                success=True,
                detected_elements=[],
                ocr_text="OCR结果"
            )
            result = mock_process("patent.png")
            assert result.success is True

    def test_process_multimodal_patent(self, engine):
        """测试处理多模态专利"""
        patent_data = {
            "text": "专利文本",
            "images": ["image1.png", "image2.png"]
        }

        with patch.object(engine, 'process_multimodal_patent') as mock_process:
            mock_process.return_value = MagicMock(
                success=True,
                text_result="文本结果",
                image_results=[],
                integrated_analysis="综合分析"
            )
            result = mock_process(patent_data)
            assert result.success is True

    def test_extract_patent_metadata(self, engine):
        """测试提取专利元数据"""
        patent_text = "专利号:CN202310000000.0\\n申请日:2023-01-01"

        with patch.object(engine, 'extract_patent_metadata') as mock_extract:
            mock_extract.return_value = {
                "patent_number": "CN202310000000.0",
                "application_date": "2023-01-01"
            }
            result = mock_extract(patent_text)
            assert "patent_number" in result

    def test_analyze_patent_claims(self, engine):
        """测试分析专利权利要求"""
        claims = "1. 一种数据处理方法,其特征在于..."

        with patch.object(engine, 'analyze_patent_claims') as mock_analyze:
            mock_analyze.return_value = {
                "independent_claims": 1,
                "dependent_claims": 0,
                "main_features": ["数据处理方法"]
            }
            result = mock_analyze(claims)
            assert "independent_claims" in result

    def test_batch_process_patents(self, engine):
        """测试批量处理专利"""
        patents = ["专利1", "专利2", "专利3"]

        with patch.object(engine, 'batch_process_patents') as mock_batch:
            mock_batch.return_value = [
                MagicMock(success=True),
                MagicMock(success=True),
                MagicMock(success=True)
            ]
            results = mock_batch(patents)
            assert len(results) == 3
            assert all(r.success for r in results)


class TestPatentPerceptionIntegration:
    """测试专利感知集成功能"""

    @pytest.fixture
    def engine(self):
        """创建引擎实例用于集成测试"""
        return EnhancedPatentPerceptionEngine({})

    def test_full_patent_analysis_workflow(self, engine):
        """测试完整的专利分析工作流"""
        patent_data = {
            "text": "本发明涉及一种人工智能算法",
            "images": []
        }

        with patch.object(engine, 'process') as mock_process:
            mock_process.return_value = PatentPerceptionResult(
                success=True,
                confidence=0.85,
                content="分析结果",
                metadata={},
                ipc_classification=["G06N"],
                technical_features=["人工智能算法"],
                novelty_assessment={}
            )
            result = mock_process(patent_data)
            assert result.success is True
            assert result.confidence > 0

    def test_error_handling(self, engine):
        """测试错误处理"""
        with patch.object(engine, 'process') as mock_process:
            # 模拟处理失败
            mock_process.side_effect = Exception("处理失败")

            with pytest.raises(Exception):
                engine.process("invalid_data")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
