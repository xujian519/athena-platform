"""
专利附图智能分析系统 v1.0

基于论文"PatentVision: A multimodal method for drafting patent applications"(2025)

核心功能:
1. 专利附图组件识别
2. 组件连接关系提取
3. 附图标记自动生成
4. 附图说明文字生成

使用模型: qwen3.5 (本地多模态)

作者: Athena平台
版本: v1.0
日期: 2026-03-23
"""

from __future__ import annotations
import base64
import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class DrawingType(Enum):
    """附图类型"""
    STRUCTURE = "structure"           # 结构图
    FLOWCHART = "flowchart"          # 流程图
    CIRCUIT = "circuit"              # 电路图
    BLOCK_DIAGRAM = "block_diagram"  # 方框图
    SCHEMATIC = "schematic"          # 示意图
    EXPLODED_VIEW = "exploded_view"  # 分解图
    CROSS_SECTION = "cross_section"  # 剖视图
    UNKNOWN = "unknown"              # 未知类型


class ComponentType(Enum):
    """组件类型"""
    MECHANICAL = "mechanical"    # 机械部件
    ELECTRICAL = "electrical"    # 电子元件
    SOFTWARE = "software"        # 软件模块
    INTERFACE = "interface"      # 接口
    SENSOR = "sensor"            # 传感器
    ACTUATOR = "actuator"        # 执行器
    CONTROLLER = "controller"    # 控制器
    UNKNOWN = "unknown"          # 未知类型


@dataclass
class DrawingComponent:
    """附图组件"""
    component_id: str              # 组件编号 (如 "1", "2", "10")
    name: str                      # 组件名称
    component_type: ComponentType  # 组件类型
    description: str = ""          # 组件描述
    position: tuple[float, float] | None = None  # 在图中的大致位置 (相对坐标)
    bounding_box: dict[str, float] | None = None  # 边界框 {x, y, width, height}

    def to_dict(self) -> dict:
        return {
            "component_id": self.component_id,
            "name": self.name,
            "component_type": self.component_type.value,
            "description": self.description,
            "position": self.position,
            "bounding_box": self.bounding_box
        }


@dataclass
class ComponentConnection:
    """组件连接关系"""
    source_id: str                 # 源组件编号
    target_id: str                 # 目标组件编号
    connection_type: str           # 连接类型 (electrical, mechanical, data_flow, etc.)
    description: str = ""          # 连接描述

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "connection_type": self.connection_type,
            "description": self.description
        }


@dataclass
class DrawingAnnotation:
    """附图标记"""
    reference_number: str          # 附图标记号
    component_name: str            # 对应组件名称
    position: tuple[float, float]  # 标记位置
    confidence: float = 0.8        # 识别置信度

    def to_dict(self) -> dict:
        return {
            "reference_number": self.reference_number,
            "component_name": self.component_name,
            "position": self.position,
            "confidence": self.confidence
        }


@dataclass
class DrawingAnalysisResult:
    """附图分析结果"""
    image_path: str                           # 图片路径
    drawing_type: DrawingType                 # 附图类型
    drawing_description: str                  # 附图整体描述

    # 识别结果
    components: list[DrawingComponent] = field(default_factory=list)
    connections: list[ComponentConnection] = field(default_factory=list)
    annotations: list[DrawingAnnotation] = field(default_factory=list)

    # 生成的说明
    figure_description: str = ""              # 生成的附图说明

    # 元数据
    confidence_score: float = 0.0             # 整体置信度
    processing_time_ms: float = 0.0          # 处理时间
    model_used: str = ""                      # 使用的模型

    def to_dict(self) -> dict:
        return {
            "image_path": self.image_path,
            "drawing_type": self.drawing_type.value,
            "drawing_description": self.drawing_description,
            "components": [c.to_dict() for c in self.components],
            "connections": [c.to_dict() for c in self.connections],
            "annotations": [a.to_dict() for a in self.annotations],
            "figure_description": self.figure_description,
            "confidence_score": self.confidence_score,
            "processing_time_ms": self.processing_time_ms,
            "model_used": self.model_used
        }


class PatentDrawingAnalyzer:
    """
    专利附图智能分析系统

    基于PatentVision论文，整合视觉语言模型进行专利附图分析。
    使用本地qwen3.5模型实现多模态理解。
    """

    # 模型配置
    MODEL_CONFIG = {
        "model": "qwen3.5",  # 本地多模态模型
        "provider": "mlx",
        "temperature": 0.2,
        "max_tokens": 2000
    }

    def __init__(self, llm_manager=None):
        """
        初始化附图分析器

        Args:
            llm_manager: LLM管理器实例
        """
        self.llm_manager = llm_manager
        self._init_prompts()

    def _init_prompts(self):
        """初始化提示词模板"""
        self.component_identification_prompt = """你是一位专利技术专家，精通阅读和理解专利附图。

请分析这张专利附图，识别图中的所有技术组件。

【分析要求】
1. 识别所有标注了数字编号的组件
2. 推断未标注但明显存在的组件
3. 判断每个组件的类型和功能
4. 描述组件之间的连接关系

【输出格式】(JSON)
```json
{
  "drawing_type": "structure/flowchart/circuit/block_diagram/schematic",
  "overall_description": "附图的整体描述",
  "components": [
    {
      "component_id": "1",
      "name": "组件名称",
      "component_type": "mechanical/electrical/software/interface/sensor/actuator/controller",
      "description": "组件功能描述"
    }
  ],
  "connections": [
    {
      "source_id": "1",
      "target_id": "2",
      "connection_type": "electrical/mechanical/data_flow",
      "description": "连接关系描述"
    }
  ]
}
```

只输出JSON，不要其他内容。
"""

        self.figure_description_prompt = """你是一位专利代理人，需要撰写专利附图说明。

【附图信息】
附图类型: {drawing_type}
附图整体描述: {overall_description}

【识别的组件】
{components_list}

【撰写要求】
1. 使用标准专利附图说明格式
2. 先简要说明附图的整体内容
3. 然后列出各标记对应的组件名称
4. 使用"所述"进行指代
5. 中文输出

【输出格式】
图{figure_number}是本发明实施例提供的{invention_name}的{drawing_type_name}；
图中：
1-{component_1_name}；
2-{component_2_name}；
...

请直接输出附图说明文字，不要其他内容。
"""

    async def analyze_drawing(
        self,
        image_path: str,
        claim_context: str | None = None,
        figure_number: int = 1
    ) -> DrawingAnalysisResult:
        """
        分析专利附图

        Args:
            image_path: 图片路径
            claim_context: 权利要求上下文（可选，用于提高识别准确性）
            figure_number: 附图编号

        Returns:
            DrawingAnalysisResult: 分析结果
        """
        import time
        start_time = time.time()

        logger.info(f"开始分析附图: {image_path}")

        # 1. 读取图片
        image_data = self._read_image(image_path)
        if image_data is None:
            return self._create_error_result(image_path, "无法读取图片")

        # 2. 调用多模态模型进行组件识别
        analysis_result = await self._identify_components(image_data, claim_context)

        if analysis_result is None:
            return self._create_error_result(image_path, "组件识别失败")

        # 3. 提取组件和连接
        components = self._parse_components(analysis_result)
        connections = self._parse_connections(analysis_result)

        # 4. 生成附图标记
        annotations = self._generate_annotations(components)

        # 5. 生成附图说明
        figure_description = await self._generate_figure_description(
            components=components,
            drawing_type=analysis_result.get("drawing_type", "structure"),
            overall_description=analysis_result.get("overall_description", ""),
            figure_number=figure_number
        )

        # 6. 计算处理时间
        processing_time = (time.time() - start_time) * 1000

        return DrawingAnalysisResult(
            image_path=image_path,
            drawing_type=DrawingType(analysis_result.get("drawing_type", "unknown")),
            drawing_description=analysis_result.get("overall_description", ""),
            components=components,
            connections=connections,
            annotations=annotations,
            figure_description=figure_description,
            confidence_score=self._calculate_confidence(components, annotations),
            processing_time_ms=processing_time,
            model_used=self.MODEL_CONFIG["model"]
        )

    async def generate_figure_description(
        self,
        drawing: DrawingAnalysisResult,
        figure_number: int = 1,
        invention_name: str = "装置"
    ) -> str:
        """
        生成标准格式的附图说明

        Args:
            drawing: 附图分析结果
            figure_number: 附图编号
            invention_name: 发明名称

        Returns:
            str: 附图说明文字
        """
        return await self._generate_figure_description(
            components=drawing.components,
            drawing_type=drawing.drawing_type.value,
            overall_description=drawing.drawing_description,
            figure_number=figure_number,
            invention_name=invention_name
        )

    async def batch_analyze_drawings(
        self,
        image_paths: list[str],
        claim_context: str | None = None
    ) -> list[DrawingAnalysisResult]:
        """
        批量分析多张附图

        Args:
            image_paths: 图片路径列表
            claim_context: 权利要求上下文

        Returns:
            List[DrawingAnalysisResult]: 分析结果列表
        """
        results = []
        for i, path in enumerate(image_paths):
            result = await self.analyze_drawing(
                image_path=path,
                claim_context=claim_context,
                figure_number=i + 1
            )
            results.append(result)
        return results

    # ==================== 私有方法 ====================

    def _read_image(self, image_path: str) -> bytes | None:
        """读取图片数据"""
        try:
            path = Path(image_path)
            if not path.exists():
                logger.error(f"图片不存在: {image_path}")
                return None

            with open(path, "rb") as f:
                return f.read()
        except Exception as e:
            logger.error(f"读取图片失败: {e}")
            return None

    async def _identify_components(
        self,
        image_data: bytes,
        claim_context: str | None = None
    ) -> dict | None:
        """调用多模态模型识别组件"""
        if self.llm_manager is None:
            return self._heuristic_component_identification()

        try:
            # 构建带图片的请求
            # 对于支持多模态的LLM，需要将图片编码为base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')

            prompt = self.component_identification_prompt
            if claim_context:
                prompt += f"\n\n【权利要求参考】\n{claim_context[:500]}"

            # 调用多模态LLM
            response = await self.llm_manager.generate(
                message=prompt,
                task_type="multimodal_patent_analysis",
                model_id=self.MODEL_CONFIG["model"],
                temperature=self.MODEL_CONFIG["temperature"],
                images=[{"data": image_base64, "mime_type": "image/png"}]
            )

            response_text = response.content if hasattr(response, 'content') else str(response)

            # 解析JSON
            return self._parse_json_response(response_text)

        except Exception as e:
            logger.warning(f"多模态分析失败: {e}, 使用启发式方法")
            return self._heuristic_component_identification()

    def _heuristic_component_identification(self) -> dict:
        """启发式组件识别（无LLM时的备选方案）"""
        return {
            "drawing_type": "structure",
            "overall_description": "专利技术附图",
            "components": [],
            "connections": []
        }

    def _parse_json_response(self, response_text: str) -> dict | None:
        """解析JSON响应"""
        try:
            # 尝试提取JSON部分
            json_match = response_text
            if "```json" in response_text:
                json_match = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                json_match = response_text.split("```")[1].split("```")[0]

            return json.loads(json_match.strip())
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            return None

    def _parse_components(self, analysis_result: dict) -> list[DrawingComponent]:
        """解析组件列表"""
        components = []
        for comp_data in analysis_result.get("components", []):
            try:
                component_type = ComponentType(
                    comp_data.get("component_type", "unknown")
                )
            except ValueError:
                component_type = ComponentType.UNKNOWN

            components.append(DrawingComponent(
                component_id=comp_data.get("component_id", ""),
                name=comp_data.get("name", ""),
                component_type=component_type,
                description=comp_data.get("description", "")
            ))
        return components

    def _parse_connections(self, analysis_result: dict) -> list[ComponentConnection]:
        """解析连接关系"""
        connections = []
        for conn_data in analysis_result.get("connections", []):
            connections.append(ComponentConnection(
                source_id=conn_data.get("source_id", ""),
                target_id=conn_data.get("target_id", ""),
                connection_type=conn_data.get("connection_type", "unknown"),
                description=conn_data.get("description", "")
            ))
        return connections

    def _generate_annotations(self, components: list[DrawingComponent]) -> list[DrawingAnnotation]:
        """生成附图标记"""
        annotations = []
        for i, comp in enumerate(components):
            annotations.append(DrawingAnnotation(
                reference_number=comp.component_id,
                component_name=comp.name,
                position=(0.5, 0.1 * (i + 1)),  # 简化位置
                confidence=0.8
            ))
        return annotations

    async def _generate_figure_description(
        self,
        components: list[DrawingComponent],
        drawing_type: str,
        overall_description: str,
        figure_number: int,
        invention_name: str = "装置"
    ) -> str:
        """生成附图说明"""
        # 组件列表
        components_list = "\n".join([
            f"- {c.component_id}: {c.name} ({c.description})"
            for c in components
        ]) if components else "暂无组件信息"

        # 附图类型名称映射
        type_names = {
            "structure": "结构示意图",
            "flowchart": "流程图",
            "circuit": "电路图",
            "block_diagram": "方框图",
            "schematic": "原理示意图",
            "exploded_view": "分解示意图",
            "cross_section": "剖视图"
        }
        drawing_type_name = type_names.get(drawing_type, "示意图")

        if self.llm_manager is None or not components:
            # 无LLM或无组件时，生成简化说明
            return self._generate_simple_description(
                figure_number, drawing_type_name, invention_name, components
            )

        try:
            prompt = self.figure_description_prompt.format(
                drawing_type=drawing_type,
                drawing_type_name=drawing_type_name,
                overall_description=overall_description or "专利技术附图",
                components_list=components_list,
                figure_number=figure_number,
                invention_name=invention_name
            )

            response = await self.llm_manager.generate(
                message=prompt,
                task_type="patent_description_generation",
                model_id="qwen3.5",
                temperature=0.3
            )

            return response.content if hasattr(response, 'content') else str(response)

        except Exception as e:
            logger.warning(f"生成附图说明失败: {e}")
            return self._generate_simple_description(
                figure_number, drawing_type_name, invention_name, components
            )

    def _generate_simple_description(
        self,
        figure_number: int,
        drawing_type_name: str,
        invention_name: str,
        components: list[DrawingComponent]
    ) -> str:
        """生成简化的附图说明"""
        lines = [f"图{figure_number}是本发明实施例提供的{invention_name}的{drawing_type_name}；"]

        if components:
            lines.append("图中：")
            for comp in components:
                lines.append(f"{comp.component_id}-{comp.name}；")
        else:
            lines.append("（组件识别结果待补充）")

        return "\n".join(lines)

    def _calculate_confidence(
        self,
        components: list[DrawingComponent],
        annotations: list[DrawingAnnotation]
    ) -> float:
        """计算置信度"""
        if not components:
            return 0.0

        # 基于组件数量和标注一致性的简单置信度计算
        base_confidence = min(0.9, 0.5 + len(components) * 0.1)

        # 检查标注一致性
        annotation_match = sum(1 for a in annotations
                             if any(c.component_id == a.reference_number for c in components))
        if annotations:
            consistency = annotation_match / len(annotations)
            base_confidence *= (0.8 + 0.2 * consistency)

        return round(base_confidence, 2)

    def _create_error_result(self, image_path: str, error_message: str) -> DrawingAnalysisResult:
        """创建错误结果"""
        return DrawingAnalysisResult(
            image_path=image_path,
            drawing_type=DrawingType.UNKNOWN,
            drawing_description=f"分析失败: {error_message}",
            components=[],
            connections=[],
            annotations=[],
            figure_description="",
            confidence_score=0.0,
            model_used="none"
        )


# ==================== 便捷函数 ====================

async def analyze_patent_drawing(
    image_path: str,
    llm_manager=None,
    claim_context: str | None = None
) -> DrawingAnalysisResult:
    """
    便捷函数: 分析专利附图

    Args:
        image_path: 图片路径
        llm_manager: LLM管理器
        claim_context: 权利要求上下文

    Returns:
        DrawingAnalysisResult: 分析结果
    """
    analyzer = PatentDrawingAnalyzer(llm_manager=llm_manager)
    return await analyzer.analyze_drawing(image_path, claim_context)


def format_figure_description(
    result: DrawingAnalysisResult,
    figure_number: int = 1
) -> str:
    """
    格式化附图说明

    Args:
        result: 分析结果
        figure_number: 附图编号

    Returns:
        str: 格式化的附图说明
    """
    if result.figure_description:
        return result.figure_description

    lines = [
        f"图{figure_number}分析结果:",
        f"  类型: {result.drawing_type.value}",
        f"  描述: {result.drawing_description}",
        f"  组件数: {len(result.components)}",
        f"  置信度: {result.confidence_score:.0%}"
    ]

    if result.components:
        lines.append("  组件:")
        for comp in result.components[:5]:  # 最多显示5个
            lines.append(f"    {comp.component_id}: {comp.name}")

    return "\n".join(lines)


def format_full_figure_description(
    results: list[DrawingAnalysisResult],
    invention_name: str = "装置"
) -> str:
    """
    格式化完整的附图说明部分

    Args:
        results: 多个分析结果
        invention_name: 发明名称（用于标题，当前未使用）

    Returns:
        str: 完整的附图说明
    """
    _ = invention_name  # 保留参数以备将来使用
    lines = ["附图说明", "=" * 40, ""]

    for idx, result in enumerate(results, 1):
        _ = idx  # 枚举索引用于未来扩展
        if result.figure_description:
            lines.append(result.figure_description)
            lines.append("")

    return "\n".join(lines)
