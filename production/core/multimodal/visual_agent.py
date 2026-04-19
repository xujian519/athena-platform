#!/usr/bin/env python3
"""
视觉Agent增强模块
Visual Agent Enhancement Module

提供专利附图分析、技术图纸理解等视觉能力。

主要功能:
1. 专利附图分析:理解专利附图中的技术特征
2. 技术图纸理解:解析工程图纸、流程图等
3. 视觉模型集成:支持GPT-4V/Claude 3.5 Sonnet等

作者: Athena平台团队
创建时间: 2026-01-20
版本: v1.0.0 "Phase 3"
"""

from __future__ import annotations
import asyncio
import base64
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from io import BytesIO
from pathlib import Path
from typing import Any, BinaryIO

logger = logging.getLogger(__name__)


# ============================================================================
# 数据模型
# ============================================================================


class VisionTaskType(str, Enum):
    """视觉任务类型"""

    PATENT_DRAWING = "patent_drawing"  # 专利附图分析
    TECHNICAL_DIAGRAM = "technical_diagram"  # 技术图纸理解
    SCHEMATIC = "schematic"  # 原理图分析
    FLOWCHART = "flowchart"  # 流程图分析
    DOCUMENT_SCAN = "document_scan"  # 文档扫描识别
    CHART_ANALYSIS = "chart_analysis"  # 图表分析


class ImageSource(str, Enum):
    """图片来源类型"""

    FILE_PATH = "file_path"  # 文件路径
    URL = "url"  # 网络URL
    BASE64 = "base64"  # Base64编码
    BYTES = "bytes"  # 字节流


@dataclass
class ImageInput:
    """图像输入"""

    source_type: ImageSource
    data: str | bytes | BinaryIO
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_base64(self) -> str:
        """转换为Base64编码"""
        if self.source_type == ImageSource.BASE64:
            if isinstance(self.data, str):
                return self.data
            elif isinstance(self.data, bytes):
                return base64.b64encode(self.data).decode("utf-8")
            elif isinstance(self.data, (BinaryIO, BytesIO)):
                self.data.seek(0)  # type: ignore
                content = self.data.read()  # type: ignore
                return base64.b64encode(content).decode("utf-8")
            else:
                raise ValueError(f"不支持的BASE64数据类型: {type(self.data)}")
        elif self.source_type == ImageSource.FILE_PATH:
            if isinstance(self.data, (str, Path)):
                with open(str(self.data), "rb") as f:
                    return base64.b64encode(f.read()).decode("utf-8")
            else:
                raise ValueError(f"FILE_PATH类型必须是str或Path,得到: {type(self.data)}")
        elif self.source_type == ImageSource.BYTES:
            if isinstance(self.data, bytes):
                return base64.b64encode(self.data).decode("utf-8")
            elif isinstance(self.data, (BinaryIO, BytesIO)):
                self.data.seek(0)  # type: ignore
                content = self.data.read()  # type: ignore
                return base64.b64encode(content).decode("utf-8")
            else:
                raise ValueError(f"不支持的BYTES数据类型: {type(self.data)}")
        else:
            raise ValueError(f"无法从 {self.source_type} 转换为Base64")


@dataclass
class VisionAnalysisResult:
    """视觉分析结果"""

    task_id: str
    task_type: VisionTaskType
    success: bool
    analysis: str
    key_elements: list[str] = field(default_factory=list)
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type.value,
            "success": self.success,
            "analysis": self.analysis,
            "key_elements": self.key_elements,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }


# ============================================================================
# 视觉模型客户端
# ============================================================================


class VisionModelClient:
    """视觉模型客户端基类"""

    def __init__(self, model_name: str, api_key: str | None = None):
        """
        初始化视觉模型客户端

        Args:
            model_name: 模型名称
            api_key: API密钥
        """
        self.model_name = model_name
        self.api_key = api_key
        logger.info(f"🔍 视觉模型客户端初始化: {model_name}")

    async def analyze_image(
        self, image: ImageInput, prompt: str, task_type: VisionTaskType
    ) -> VisionAnalysisResult:
        """
        分析图像

        Args:
            image: 图像输入
            prompt: 分析提示词
            task_type: 任务类型

        Returns:
            VisionAnalysisResult: 分析结果
        """
        raise NotImplementedError("子类必须实现此方法")


class MockVisionModelClient(VisionModelClient):
    """模拟视觉模型客户端(用于测试)"""

    def __init__(self):
        super().__init__("mock_vision_model")

    async def analyze_image(
        self, image: ImageInput, prompt: str, task_type: VisionTaskType
    ) -> VisionAnalysisResult:
        """模拟图像分析"""
        # 模拟处理延迟
        await asyncio.sleep(0.1)

        # 根据任务类型返回模拟结果
        if task_type == VisionTaskType.PATENT_DRAWING:
            analysis = "这是专利附图的模拟分析结果。附图展示了一个技术装置的示意图,包含主要组件A、B和连接关系。"
            key_elements = ["组件A", "组件B", "连接关系"]
            confidence = 0.85
        elif task_type == VisionTaskType.TECHNICAL_DIAGRAM:
            analysis = "这是技术图纸的模拟分析结果。图纸展示了一个系统的架构,包括输入模块、处理模块和输出模块。"
            key_elements = ["输入模块", "处理模块", "输出模块"]
            confidence = 0.88
        else:
            analysis = f"这是{task_type.value}的模拟分析结果。"
            key_elements = []
            confidence = 0.80

        return VisionAnalysisResult(
            task_id=f"mock_{datetime.now().timestamp()}",
            task_type=task_type,
            success=True,
            analysis=analysis,
            key_elements=key_elements,
            confidence=confidence,
        )


# ============================================================================
# 视觉Agent
# ============================================================================


class VisualAgent:
    """
    视觉Agent

    提供专利附图分析、技术图纸理解等视觉能力。
    """

    def __init__(self, vision_client: VisionModelClient | None = None):
        """
        初始化视觉Agent

        Args:
            vision_client: 视觉模型客户端(默认使用Mock客户端)
        """
        self.vision_client = vision_client or MockVisionModelClient()
        self.analysis_history: list[VisionAnalysisResult] = []

        logger.info("👁️ 视觉Agent初始化完成")

    async def analyze_patent_drawing(
        self, image: ImageInput, context: str | None = None
    ) -> VisionAnalysisResult:
        """
        分析专利附图

        Args:
            image: 附图图像
            context: 上下文信息(如专利标题、摘要等)

        Returns:
            VisionAnalysisResult: 分析结果
        """
        logger.info("📊 开始分析专利附图...")

        # 构建提示词
        prompt_parts = [
            "请分析这张专利附图,",
            "识别并描述:",
            "1. 附图展示的技术特征和组件",
            "2. 组件之间的连接关系",
            "3. 附图在说明专利技术方案中的作用",
        ]

        if context:
            prompt_parts.append(f"\n上下文信息:{context}")

        prompt = "\n".join(prompt_parts)

        # 调用视觉模型
        result = await self.vision_client.analyze_image(
            image=image, prompt=prompt, task_type=VisionTaskType.PATENT_DRAWING
        )

        # 添加到历史记录
        self.analysis_history.append(result)

        logger.info(
            f"✅ 专利附图分析完成 | "
            f"置信度: {result.confidence:.2%} | "
            f"关键元素: {len(result.key_elements)}个"
        )

        return result

    async def analyze_technical_diagram(
        self, image: ImageInput, diagram_type: str | None = None
    ) -> VisionAnalysisResult:
        """
        分析技术图纸

        Args:
            image: 纸张图像
            diagram_type: 图纸类型(如流程图、原理图、结构图等)

        Returns:
            VisionAnalysisResult: 分析结果
        """
        logger.info(f"📋 开始分析技术图纸{f'({diagram_type})' if diagram_type else ''}...")

        # 构建提示词
        prompt_parts = [
            "请分析这张技术图纸,",
            "识别并描述:",
            "1. 纸张的类型和用途",
            "2. 主要组成部分和模块",
            "3. 各部分之间的关系和数据流向",
            "4. 关键的技术特征和参数",
        ]

        if diagram_type:
            prompt_parts.append(f"\n图纸类型:{diagram_type}")

        prompt = "\n".join(prompt_parts)

        # 调用视觉模型
        result = await self.vision_client.analyze_image(
            image=image, prompt=prompt, task_type=VisionTaskType.TECHNICAL_DIAGRAM
        )

        # 添加到历史记录
        self.analysis_history.append(result)

        logger.info(
            f"✅ 技术图纸分析完成 | "
            f"置信度: {result.confidence:.2%} | "
            f"关键元素: {len(result.key_elements)}个"
        )

        return result

    async def analyze_schematic(
        self, image: ImageInput, system_description: str | None = None
    ) -> VisionAnalysisResult:
        """
        分析原理图

        Args:
            image: 原理图图像
            system_description: 系统描述

        Returns:
            VisionAnalysisResult: 分析结果
        """
        logger.info("⚡ 开始分析原理图...")

        prompt_parts = [
            "请分析这张原理图,",
            "识别并描述:",
            "1. 系统的总体架构",
            "2. 主要功能模块和组件",
            "3. 信号或数据流向",
            "4. 控制逻辑和时序关系",
        ]

        if system_description:
            prompt_parts.append(f"\n系统描述:{system_description}")

        prompt = "\n".join(prompt_parts)

        result = await self.vision_client.analyze_image(
            image=image, prompt=prompt, task_type=VisionTaskType.SCHEMATIC
        )

        self.analysis_history.append(result)

        logger.info(f"✅ 原理图分析完成 | " f"置信度: {result.confidence:.2%}")

        return result

    async def analyze_flowchart(
        self, image: ImageInput, process_context: str | None = None
    ) -> VisionAnalysisResult:
        """
        分析流程图

        Args:
            image: 流程图图像
            process_context: 流程上下文

        Returns:
            VisionAnalysisResult: 分析结果
        """
        logger.info("🔄 开始分析流程图...")

        prompt_parts = [
            "请分析这张流程图,",
            "识别并描述:",
            "1. 流程的起点和终点",
            "2. 主要的步骤和决策点",
            "3. 各步骤之间的逻辑关系",
            "4. 流程的关键路径和分支",
        ]

        if process_context:
            prompt_parts.append(f"\n流程上下文:{process_context}")

        prompt = "\n".join(prompt_parts)

        result = await self.vision_client.analyze_image(
            image=image, prompt=prompt, task_type=VisionTaskType.FLOWCHART
        )

        self.analysis_history.append(result)

        logger.info(f"✅ 流程图分析完成 | " f"置信度: {result.confidence:.2%}")

        return result

    async def batch_analyze(
        self, images: list[ImageInput], task_type: VisionTaskType, context: str | None = None
    ) -> list[VisionAnalysisResult]:
        """
        批量分析图像

        Args:
            images: 图像列表
            task_type: 任务类型
            context: 上下文信息

        Returns:
            list[VisionAnalysisResult]: 分析结果列表
        """
        logger.info(f"📦 开始批量分析 {len(images)} 张图像...")

        results = []

        for i, image in enumerate(images):
            logger.info(f"处理第 {i+1}/{len(images)} 张图像...")

            if task_type == VisionTaskType.PATENT_DRAWING:
                result = await self.analyze_patent_drawing(image, context)
            elif task_type == VisionTaskType.TECHNICAL_DIAGRAM:
                result = await self.analyze_technical_diagram(image)
            elif task_type == VisionTaskType.SCHEMATIC:
                result = await self.analyze_schematic(image, context)
            elif task_type == VisionTaskType.FLOWCHART:
                result = await self.analyze_flowchart(image, context)
            else:
                # 通用分析
                result = await self.vision_client.analyze_image(
                    image=image, prompt="请分析这张图片", task_type=task_type
                )

            results.append(result)

        logger.info(f"✅ 批量分析完成 | 总数: {len(results)}")

        return results

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        if not self.analysis_history:
            return {"total_analyses": 0, "success_rate": 0.0, "avg_confidence": 0.0}

        total = len(self.analysis_history)
        successful = sum(1 for r in self.analysis_history if r.success)
        avg_confidence = sum(r.confidence for r in self.analysis_history) / total

        # 按任务类型统计
        task_type_counts = {}
        for result in self.analysis_history:
            task_type = result.task_type.value
            task_type_counts[task_type] = task_type_counts.get(task_type, 0) + 1

        return {
            "total_analyses": total,
            "successful_analyses": successful,
            "success_rate": successful / total if total > 0 else 0.0,
            "avg_confidence": avg_confidence,
            "task_type_distribution": task_type_counts,
        }


# ============================================================================
# 视觉工具集成
# ============================================================================


class VisualToolIntegration:
    """
    视觉工具集成

    将视觉Agent集成到现有工具体系中。
    """

    def __init__(self, visual_agent: VisualAgent | None = None):
        """
        初始化视觉工具集成

        Args:
            visual_agent: 视觉Agent实例
        """
        self.visual_agent = visual_agent or VisualAgent()

        logger.info("🔧 视觉工具集成初始化完成")

    async def process_patent_with_drawings(
        self, patent_data: dict[str, Any], drawing_paths: list[str]
    ) -> dict[str, Any]:
        """
        处理带附图的专利

        Args:
            patent_data: 专利数据
            drawing_paths: 附图路径列表

        Returns:
            Dict: 处理结果,包含专利信息和附图分析
        """
        logger.info(f"📄 开始处理专利附图,共 {len(drawing_paths)} 张")

        # 准备图像输入
        images = [
            ImageInput(source_type=ImageSource.FILE_PATH, data=path) for path in drawing_paths
        ]

        # 批量分析附图
        context = f"专利标题:{patent_data.get('title', '')}"
        drawing_analyses = await self.visual_agent.batch_analyze(
            images=images, task_type=VisionTaskType.PATENT_DRAWING, context=context
        )

        # 整合结果
        result = {
            "patent_id": patent_data.get("patent_id", ""),
            "title": patent_data.get("title", ""),
            "abstract": patent_data.get("abstract", ""),
            "drawings": [
                {"path": drawing_paths[i], "analysis": analysis.to_dict()}
                for i, analysis in enumerate(drawing_analyses)
            ],
            "total_drawings": len(drawing_paths),
            "processing_time": datetime.now().isoformat(),
        }

        logger.info(f"✅ 专利附图处理完成 | 附图数: {len(drawing_paths)}")

        return result

    async def extract_technical_features(
        self, diagram_path: str, diagram_type: str | None = None
    ) -> dict[str, Any]:
        """
        从技术图纸中提取特征

        Args:
            diagram_path: 图纸路径
            diagram_type: 图纸类型

        Returns:
            Dict: 提取的技术特征
        """
        logger.info(f"🔧 开始从图纸提取特征: {diagram_path}")

        image = ImageInput(source_type=ImageSource.FILE_PATH, data=diagram_path)

        # 分析图纸
        result = await self.visual_agent.analyze_technical_diagram(
            image=image, diagram_type=diagram_type
        )

        # 提取关键特征
        features = {
            "diagram_path": diagram_path,
            "diagram_type": diagram_type,
            "key_elements": result.key_elements,
            "analysis": result.analysis,
            "confidence": result.confidence,
            "extracted_at": result.timestamp,
        }

        logger.info(
            f"✅ 特征提取完成 | "
            f"关键特征数: {len(result.key_elements)} | "
            f"置信度: {result.confidence:.2%}"
        )

        return features

    async def compare_diagrams(self, diagram_paths: list[str]) -> dict[str, Any]:
        """
        比较多个图纸

        Args:
            diagram_paths: 图纸路径列表

        Returns:
            Dict: 比较结果
        """
        logger.info(f"🔄 开始比较 {len(diagram_paths)} 张图纸")

        # 分析所有图纸
        images = [
            ImageInput(source_type=ImageSource.FILE_PATH, data=path) for path in diagram_paths
        ]

        analyses = await self.visual_agent.batch_analyze(
            images=images, task_type=VisionTaskType.TECHNICAL_DIAGRAM
        )

        # 提取共同点和差异
        all_elements = set()
        for analysis in analyses:
            all_elements.update(analysis.key_elements)

        common_elements = []
        for element in all_elements:
            if all(element in analysis.key_elements for analysis in analyses):
                common_elements.append(element)

        comparison = {
            "total_diagrams": len(diagram_paths),
            "diagrams": [
                {"path": diagram_paths[i], "analysis": analysis.to_dict()}
                for i, analysis in enumerate(analyses)
            ],
            "common_elements": common_elements,
            "unique_elements_per_diagram": [
                [elem for elem in analysis.key_elements if elem not in common_elements]
                for analysis in analyses
            ],
            "comparison_time": datetime.now().isoformat(),
        }

        logger.info(f"✅ 图纸比较完成 | " f"共同特征: {len(common_elements)}个")

        return comparison


# ============================================================================
# 便捷函数
# ============================================================================

# 全局单例
_visual_agent: VisualAgent | None = None
_visual_tool_integration: VisualToolIntegration | None = None


def get_visual_agent() -> VisualAgent:
    """获取全局视觉Agent单例"""
    global _visual_agent
    if _visual_agent is None:
        _visual_agent = VisualAgent()
    return _visual_agent


def get_visual_tool_integration() -> VisualToolIntegration:
    """获取全局视觉工具集成单例"""
    global _visual_tool_integration
    if _visual_tool_integration is None:
        _visual_tool_integration = VisualToolIntegration()
    return _visual_tool_integration


async def analyze_patent_drawing(
    image_path: str | None = None, context: str | None = None
) -> VisionAnalysisResult:
    """
    便捷的专利附图分析函数

    Args:
        image_path: 附图路径
        context: 上下文信息

    Returns:
        VisionAnalysisResult: 分析结果

    Example:
        >>> result = await analyze_patent_drawing(
        ...     "/path/to/patent_drawing.png",
        ...     context="专利标题:一种新型装置"
        ... )
        >>> print(result.analysis)
    """
    agent = get_visual_agent()

    image = ImageInput(source_type=ImageSource.FILE_PATH, data=image_path)

    return await agent.analyze_patent_drawing(image, context)


async def analyze_technical_diagram(
    image_path: str | None = None, diagram_type: str | None = None
) -> VisionAnalysisResult:
    """
    便捷的技术图纸分析函数

    Args:
        image_path: 图纸路径
        diagram_type: 图纸类型

    Returns:
        VisionAnalysisResult: 分析结果
    """
    agent = get_visual_agent()

    image = ImageInput(source_type=ImageSource.FILE_PATH, data=image_path)

    return await agent.analyze_technical_diagram(image, diagram_type)


__all__ = [
    # 数据模型
    "ImageInput",
    "ImageSource",
    "MockVisionModelClient",
    "VisionAnalysisResult",
    # 视觉模型
    "VisionModelClient",
    # 枚举
    "VisionTaskType",
    # 视觉Agent
    "VisualAgent",
    # 工具集成
    "VisualToolIntegration",
    "analyze_patent_drawing",
    "analyze_technical_diagram",
    # 便捷函数
    "get_visual_agent",
    "get_visual_tool_integration",
]
