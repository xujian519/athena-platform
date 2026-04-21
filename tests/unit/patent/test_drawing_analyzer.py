"""
专利附图智能分析系统单元测试
Unit tests for Patent Drawing Analyzer

基于论文 "PatentVision: A multimodal method for drafting patent applications" (2025)
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from core.patents.ai_services.drawing_analyzer import (
    ComponentConnection,
    ComponentType,
    DrawingAnalysisResult,
    DrawingAnnotation,
    DrawingComponent,
    DrawingType,
    PatentDrawingAnalyzer,
    analyze_patent_drawing,
    format_figure_description,
    format_full_figure_description,
)

# ==================== 数据结构测试 ====================

class TestDrawingComponent:
    """DrawingComponent 数据结构测试"""

    def test_component_creation(self):
        """测试组件创建"""
        component = DrawingComponent(
            component_id="1",
            name="光伏板",
            component_type=ComponentType.MECHANICAL,
            description="用于将光能转换为电能"
        )
        assert component.component_id == "1"
        assert component.name == "光伏板"
        assert component.component_type == ComponentType.MECHANICAL
        assert component.position is None

    def test_component_with_position(self):
        """测试带位置的组件"""
        component = DrawingComponent(
            component_id="2",
            name="控制器",
            component_type=ComponentType.CONTROLLER,
            description="控制充电过程",
            position=(0.5, 0.3),
            bounding_box={"x": 100, "y": 200, "width": 50, "height": 30}
        )
        assert component.position == (0.5, 0.3)
        assert component.bounding_box["width"] == 50

    def test_component_to_dict(self):
        """测试组件序列化"""
        component = DrawingComponent(
            component_id="3",
            name="传感器",
            component_type=ComponentType.SENSOR,
            description="检测电流"
        )
        result = component.to_dict()
        assert result["component_id"] == "3"
        assert result["component_type"] == "sensor"


class TestComponentConnection:
    """ComponentConnection 数据结构测试"""

    def test_connection_creation(self):
        """测试连接关系创建"""
        connection = ComponentConnection(
            source_id="1",
            target_id="2",
            connection_type="electrical",
            description="电连接"
        )
        assert connection.source_id == "1"
        assert connection.target_id == "2"
        assert connection.connection_type == "electrical"

    def test_connection_to_dict(self):
        """测试连接关系序列化"""
        connection = ComponentConnection(
            source_id="2",
            target_id="3",
            connection_type="data_flow",
            description="数据传输"
        )
        result = connection.to_dict()
        assert result["source_id"] == "2"
        assert result["connection_type"] == "data_flow"


class TestDrawingAnnotation:
    """DrawingAnnotation 数据结构测试"""

    def test_annotation_creation(self):
        """测试附图标记创建"""
        annotation = DrawingAnnotation(
            reference_number="10",
            component_name="储能电池",
            position=(0.3, 0.7),
            confidence=0.95
        )
        assert annotation.reference_number == "10"
        assert annotation.confidence == 0.95

    def test_annotation_to_dict(self):
        """测试附图标记序列化"""
        annotation = DrawingAnnotation(
            reference_number="11",
            component_name="逆变器",
            position=(0.5, 0.5)
        )
        result = annotation.to_dict()
        assert result["reference_number"] == "11"
        assert result["confidence"] == 0.8  # 默认值


class TestDrawingAnalysisResult:
    """DrawingAnalysisResult 数据结构测试"""

    def test_result_creation(self):
        """测试分析结果创建"""
        result = DrawingAnalysisResult(
            image_path="/path/to/image.png",
            drawing_type=DrawingType.STRUCTURE,
            drawing_description="光伏充电系统结构图"
        )
        assert result.image_path == "/path/to/image.png"
        assert result.drawing_type == DrawingType.STRUCTURE
        assert len(result.components) == 0

    def test_result_with_components(self):
        """测试带组件的分析结果"""
        components = [
            DrawingComponent("1", "组件A", ComponentType.MECHANICAL, "描述A"),
            DrawingComponent("2", "组件B", ComponentType.ELECTRICAL, "描述B")
        ]
        result = DrawingAnalysisResult(
            image_path="/path/to/image.png",
            drawing_type=DrawingType.BLOCK_DIAGRAM,
            drawing_description="系统方框图",
            components=components,
            confidence_score=0.85
        )
        assert len(result.components) == 2
        assert result.confidence_score == 0.85

    def test_result_to_dict(self):
        """测试分析结果序列化"""
        result = DrawingAnalysisResult(
            image_path="/test/image.png",
            drawing_type=DrawingType.FLOWCHART,
            drawing_description="处理流程图",
            components=[DrawingComponent("1", "步骤1", ComponentType.SOFTWARE)],
            confidence_score=0.9,
            processing_time_ms=1500.0,
            model_used="qwen3.5"
        )
        data = result.to_dict()
        assert data["drawing_type"] == "flowchart"
        assert len(data["components"]) == 1
        assert data["processing_time_ms"] == 1500.0


# ==================== 枚举测试 ====================

class TestEnums:
    """枚举类型测试"""

    def test_drawing_type_values(self):
        """测试附图类型枚举"""
        assert DrawingType.STRUCTURE.value == "structure"
        assert DrawingType.FLOWCHART.value == "flowchart"
        assert DrawingType.CIRCUIT.value == "circuit"
        assert DrawingType.BLOCK_DIAGRAM.value == "block_diagram"

    def test_component_type_values(self):
        """测试组件类型枚举"""
        assert ComponentType.MECHANICAL.value == "mechanical"
        assert ComponentType.ELECTRICAL.value == "electrical"
        assert ComponentType.SOFTWARE.value == "software"
        assert ComponentType.SENSOR.value == "sensor"
        assert ComponentType.CONTROLLER.value == "controller"


# ==================== 分析器测试 ====================

class TestPatentDrawingAnalyzer:
    """PatentDrawingAnalyzer 核心测试"""

    def test_analyzer_initialization(self):
        """测试分析器初始化"""
        analyzer = PatentDrawingAnalyzer()
        assert analyzer.llm_manager is None
        assert analyzer.MODEL_CONFIG["model"] == "qwen3.5"

    def test_analyzer_with_llm_manager(self):
        """测试带LLM管理器的初始化"""
        mock_llm = MagicMock()
        analyzer = PatentDrawingAnalyzer(llm_manager=mock_llm)
        assert analyzer.llm_manager == mock_llm

    def test_init_prompts(self):
        """测试提示词初始化"""
        analyzer = PatentDrawingAnalyzer()
        assert hasattr(analyzer, 'component_identification_prompt')
        assert hasattr(analyzer, 'figure_description_prompt')
        assert "JSON" in analyzer.component_identification_prompt

    def test_read_image_nonexistent(self):
        """测试读取不存在的图片"""
        analyzer = PatentDrawingAnalyzer()
        result = analyzer._read_image("/nonexistent/path.png")
        assert result is None

    def test_read_image_existing(self):
        """测试读取存在的图片"""
        # 创建临时图片文件
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)  # 简化的PNG头
            temp_path = f.name

        try:
            analyzer = PatentDrawingAnalyzer()
            result = analyzer._read_image(temp_path)
            assert result is not None
            assert len(result) > 0
        finally:
            os.unlink(temp_path)

    def test_parse_json_response(self):
        """测试JSON响应解析"""
        analyzer = PatentDrawingAnalyzer()

        # 带代码块的JSON
        response = '```json\n{"drawing_type": "structure", "components": []}\n```'
        result = analyzer._parse_json_response(response)
        assert result is not None
        assert result["drawing_type"] == "structure"

        # 纯JSON
        response = '{"drawing_type": "flowchart"}'
        result = analyzer._parse_json_response(response)
        assert result["drawing_type"] == "flowchart"

    def test_parse_json_response_invalid(self):
        """测试无效JSON响应"""
        analyzer = PatentDrawingAnalyzer()
        result = analyzer._parse_json_response("not valid json")
        assert result is None

    def test_parse_components(self):
        """测试组件解析"""
        analyzer = PatentDrawingAnalyzer()
        analysis_result = {
            "components": [
                {"component_id": "1", "name": "电机", "component_type": "mechanical"},
                {"component_id": "2", "name": "控制器", "component_type": "controller"}
            ]
        }
        components = analyzer._parse_components(analysis_result)
        assert len(components) == 2
        assert components[0].name == "电机"
        assert components[1].component_type == ComponentType.CONTROLLER

    def test_parse_connections(self):
        """测试连接关系解析"""
        analyzer = PatentDrawingAnalyzer()
        analysis_result = {
            "connections": [
                {"source_id": "1", "target_id": "2", "connection_type": "electrical"},
                {"source_id": "2", "target_id": "3", "connection_type": "data_flow"}
            ]
        }
        connections = analyzer._parse_connections(analysis_result)
        assert len(connections) == 2
        assert connections[0].source_id == "1"
        assert connections[1].connection_type == "data_flow"

    def test_generate_annotations(self):
        """测试附图标记生成"""
        analyzer = PatentDrawingAnalyzer()
        components = [
            DrawingComponent("1", "组件A", ComponentType.MECHANICAL),
            DrawingComponent("2", "组件B", ComponentType.ELECTRICAL),
            DrawingComponent("3", "组件C", ComponentType.SENSOR)
        ]
        annotations = analyzer._generate_annotations(components)
        assert len(annotations) == 3
        assert annotations[0].reference_number == "1"
        assert annotations[1].component_name == "组件B"

    def test_calculate_confidence_no_components(self):
        """测试无组件时的置信度计算"""
        analyzer = PatentDrawingAnalyzer()
        confidence = analyzer._calculate_confidence([], [])
        assert confidence == 0.0

    def test_calculate_confidence_with_components(self):
        """测试有组件时的置信度计算"""
        analyzer = PatentDrawingAnalyzer()
        components = [
            DrawingComponent("1", "A", ComponentType.MECHANICAL),
            DrawingComponent("2", "B", ComponentType.ELECTRICAL)
        ]
        annotations = [
            DrawingAnnotation("1", "A", (0.5, 0.5)),
            DrawingAnnotation("2", "B", (0.3, 0.3))
        ]
        confidence = analyzer._calculate_confidence(components, annotations)
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.5  # 有组件时应该有较高置信度

    def test_create_error_result(self):
        """测试错误结果创建"""
        analyzer = PatentDrawingAnalyzer()
        result = analyzer._create_error_result("/test/path.png", "测试错误")
        assert result.image_path == "/test/path.png"
        assert result.drawing_type == DrawingType.UNKNOWN
        assert "测试错误" in result.drawing_description
        assert result.confidence_score == 0.0

    def test_generate_simple_description(self):
        """测试简化说明生成"""
        analyzer = PatentDrawingAnalyzer()
        components = [
            DrawingComponent("1", "光伏板", ComponentType.MECHANICAL),
            DrawingComponent("2", "充电器", ComponentType.ELECTRICAL)
        ]
        description = analyzer._generate_simple_description(
            figure_number=1,
            drawing_type_name="结构示意图",
            invention_name="光伏充电装置",
            components=components
        )
        assert "图1" in description
        assert "光伏充电装置" in description
        assert "光伏板" in description


# ==================== 异步方法测试 ====================

@pytest.mark.asyncio
class TestAsyncMethods:
    """异步方法测试"""

    async def test_analyze_drawing_no_image(self):
        """测试分析不存在的图片"""
        analyzer = PatentDrawingAnalyzer()
        result = await analyzer.analyze_drawing("/nonexistent/image.png")
        assert result.drawing_type == DrawingType.UNKNOWN
        assert len(result.components) == 0

    async def test_analyze_drawing_with_image(self):
        """测试分析存在的图片（无LLM）"""
        # 创建临时图片
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
            temp_path = f.name

        try:
            analyzer = PatentDrawingAnalyzer()  # 无LLM
            result = await analyzer.analyze_drawing(temp_path)
            # 无LLM时使用启发式方法
            assert result.image_path == temp_path
            assert result.drawing_type == DrawingType.STRUCTURE
        finally:
            os.unlink(temp_path)

    async def test_generate_figure_description(self):
        """测试附图说明生成"""
        analyzer = PatentDrawingAnalyzer()
        drawing = DrawingAnalysisResult(
            image_path="/test.png",
            drawing_type=DrawingType.STRUCTURE,
            drawing_description="测试附图",
            components=[
                DrawingComponent("1", "组件A", ComponentType.MECHANICAL),
                DrawingComponent("2", "组件B", ComponentType.ELECTRICAL)
            ]
        )
        description = await analyzer.generate_figure_description(drawing, figure_number=1)
        assert "图1" in description

    async def test_batch_analyze_drawings(self):
        """测试批量分析"""
        # 创建多个临时图片
        temp_files = []
        for _ in range(3):
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
                f.write(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
                temp_files.append(f.name)

        try:
            analyzer = PatentDrawingAnalyzer()
            results = await analyzer.batch_analyze_drawings(temp_files)
            assert len(results) == 3
        finally:
            for path in temp_files:
                os.unlink(path)


# ==================== 便捷函数测试 ====================

class TestConvenienceFunctions:
    """便捷函数测试"""

    @pytest.mark.asyncio
    async def test_analyze_patent_drawing(self):
        """测试便捷分析函数"""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
            temp_path = f.name

        try:
            result = await analyze_patent_drawing(temp_path)
            assert isinstance(result, DrawingAnalysisResult)
        finally:
            os.unlink(temp_path)

    def test_format_figure_description(self):
        """测试格式化附图说明"""
        result = DrawingAnalysisResult(
            image_path="/test.png",
            drawing_type=DrawingType.STRUCTURE,
            drawing_description="测试描述",
            components=[
                DrawingComponent("1", "组件A", ComponentType.MECHANICAL),
                DrawingComponent("2", "组件B", ComponentType.ELECTRICAL)
            ],
            confidence_score=0.85
        )
        formatted = format_figure_description(result, figure_number=1)
        assert "图1" in formatted
        assert "structure" in formatted

    def test_format_figure_description_with_content(self):
        """测试有内容的格式化"""
        result = DrawingAnalysisResult(
            image_path="/test.png",
            drawing_type=DrawingType.BLOCK_DIAGRAM,
            drawing_description="系统方框图",
            figure_description="图1是本发明的方框图；\n图中：1-主控模块；2-通信模块；",
            confidence_score=0.9
        )
        formatted = format_figure_description(result, figure_number=1)
        # 有预生成的说明时直接返回
        assert "主控模块" in formatted

    def test_format_full_figure_description(self):
        """测试完整附图说明格式化"""
        results = [
            DrawingAnalysisResult(
                image_path="/1.png",
                drawing_type=DrawingType.STRUCTURE,
                drawing_description="结构图",
                figure_description="图1是本发明的结构示意图；"
            ),
            DrawingAnalysisResult(
                image_path="/2.png",
                drawing_type=DrawingType.FLOWCHART,
                drawing_description="流程图",
                figure_description="图2是本发明的工作流程图；"
            )
        ]
        full_description = format_full_figure_description(results, "智能装置")
        assert "附图说明" in full_description
        assert "图1" in full_description
        assert "图2" in full_description


# ==================== 边界条件测试 ====================

class TestEdgeCases:
    """边界条件测试"""

    def test_empty_components_list(self):
        """测试空组件列表"""
        analyzer = PatentDrawingAnalyzer()
        annotations = analyzer._generate_annotations([])
        assert len(annotations) == 0

    def test_unknown_component_type(self):
        """测试未知组件类型"""
        analyzer = PatentDrawingAnalyzer()
        analysis_result = {
            "components": [
                {"component_id": "1", "name": "组件", "component_type": "unknown_type"}
            ]
        }
        components = analyzer._parse_components(analysis_result)
        assert len(components) == 1
        assert components[0].component_type == ComponentType.UNKNOWN

    def test_missing_optional_fields(self):
        """测试缺失可选字段"""
        component = DrawingComponent(
            component_id="1",
            name="测试组件",
            component_type=ComponentType.MECHANICAL
        )
        # 可选字段应为None或默认值
        assert component.description == ""
        assert component.position is None
        assert component.bounding_box is None


# ==================== 集成测试标记 ====================

@pytest.mark.integration
class TestDrawingAnalyzerIntegration:
    """集成测试（需要实际模型）"""

    @pytest.mark.asyncio
    async def test_full_analysis_pipeline(self):
        """完整分析流程测试"""
        # 这个测试需要实际的LLM连接
        # 在CI环境中跳过
        pytest.skip("需要实际LLM连接")

    @pytest.mark.asyncio
    async def test_multimodal_analysis(self):
        """多模态分析测试"""
        # 需要支持多模态的模型
        pytest.skip("需要多模态模型支持")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
