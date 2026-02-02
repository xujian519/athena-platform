#!/usr/bin/env python3
"""
技术图纸智能分析器
Technical Drawing Intelligent Analyzer

集成GLM-4V进行技术图纸理解,支持专利附图、工程图纸、技术图表的专业分析

作者: Athena AI系统
创建时间: 2025-12-24
版本: 1.0.0
"""

import base64
import io
import json
import logging
import os
import re

# 导入上下文压缩器
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import cv2
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from performance.context_compressor import ContextCompressor


class DrawingType(Enum):
    """图纸类型"""

    PATENT_DRAWING = "patent_drawing"  # 专利附图
    MECHANICAL_DRAWING = "mechanical_drawing"  # 机械图纸
    CIRCUIT_DIAGRAM = "circuit_diagram"  # 电路图
    FLOWCHART = "flowchart"  # 流程图
    STRUCTURE_DIAGRAM = "structure_diagram"  # 结构图
    SCHEMATIC = "schematic"  # 原理图
    TECHNICAL_ILLUSTRATION = "technical_illustration"  # 技术插图


class AnalysisLevel(Enum):
    """分析深度"""

    BASIC = "basic"  # 基础识别(这是什么图?)
    INTERMEDIATE = "intermediate"  # 中级分析(有哪些组件?)
    ADVANCED = "advanced"  # 高级分析(如何工作?与说明书关联?)


@dataclass
class DrawingAnalysisResult:
    """图纸分析结果"""

    drawing_type: DrawingType
    file_path: str

    # 基础识别
    title: str = ""  # 图纸标题
    description: str = ""  # 整体描述
    confidence: float = 0.0  # 置信度

    # 组件分析
    components: list[dict[str, Any]] = field(default_factory=list)  # 识别的组件
    labels: list[str] = field(default_factory=list)  # 图纸标注
    annotations: dict[str, str] = field(default_factory=dict)  # 标注说明

    # 技术分析
    technical_features: list[str] = field(default_factory=list)  # 技术特征
    working_principle: str = ""  # 工作原理
    structure_info: dict = field(default_factory=dict)  # 结构信息

    # 关联分析
    related_claims: list[str] = field(default_factory=list)  # 关联的权利要求
    specification_reference: str = ""  # 参考的说明书段落

    # 元数据
    analysis_level: AnalysisLevel = AnalysisLevel.BASIC
    processing_time: float = 0.0
    model_used: str = ""
    tokens_used: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    error: str | None = None


@dataclass
class ImageChunk:
    """图像分块"""

    chunk_id: int
    image_data: bytes  # base64编码
    position: dict[str, int]  # {x, y, width, height}
    description: str = ""


class TechnicalDrawingAnalyzer:
    """技术图纸智能分析器"""

    def __init__(
        self,
        glm_client=None,
        max_image_size: int = 2048,
        chunk_size: int = 1024,
        enable_chunking: bool = True,
    ):
        """
        初始化分析器

        Args:
            glm_client: GLM统一客户端
            max_image_size: 最大图像尺寸(像素)
            chunk_size: 分块大小(像素)
            enable_chunking: 是否启用分块处理
        """
        self.glm_client = glm_client
        self.max_image_size = max_image_size
        self.chunk_size = chunk_size
        self.enable_chunking = enable_chunking

        # 上下文压缩器
        self.context_compressor = ContextCompressor(
            max_history_length=3,  # 只保留最近3轮对话
            max_tokens=6000,  # 为图像留出空间
            compression_strategy="importance",  # 使用重要性压缩
        )

        self.logger = self._setup_logger()

        # 统计信息
        self.stats = {
            "total_analyses": 0,
            "successful_analyses": 0,
            "total_chunks_processed": 0,
            "average_processing_time": 0.0,
            "drawing_type_distribution": {},
        }

    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger("TechnicalDrawingAnalyzer")
        logger.set_level(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.set_formatter(formatter)
            logger.add_handler(handler)

        return logger

    async def analyze(
        self,
        image_path: str,
        analysis_level: AnalysisLevel = AnalysisLevel.INTERMEDIATE,
        specification_text: str | None = None,
        related_claims: list[str] | None = None,
    ) -> DrawingAnalysisResult:
        """
        分析技术图纸

        Args:
            image_path: 图像文件路径
            analysis_level: 分析深度
            specification_text: 说明书文本(用于关联分析)
            related_claims: 相关权利要求

        Returns:
            DrawingAnalysisResult: 分析结果
        """
        start_time = datetime.now()
        self.stats["total_analyses"] += 1

        try:
            # 1. 读取和预处理图像
            image_data = await self._load_and_preprocess_image(image_path)
            base64_image = base64.b64encode(image_data).decode("utf-8")

            # 2. 判断是否需要分块
            image = Image.open(io.BytesIO(image_data))
            width, height = image.size

            if self.enable_chunking and (width > self.chunk_size or height > self.chunk_size):
                # 分块处理
                return await self._analyze_with_chunking(
                    image_path,
                    image_data,
                    base64_image,
                    analysis_level,
                    specification_text,
                    related_claims,
                )
            else:
                # 整体处理
                return await self._analyze_whole(
                    image_path, base64_image, analysis_level, specification_text, related_claims
                )

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"图纸分析失败: {e!s}")

            return DrawingAnalysisResult(
                drawing_type=DrawingType.PATENT_DRAWING,
                file_path=image_path,
                confidence=0.0,
                processing_time=processing_time,
                error=str(e),
            )

    async def _analyze_whole(
        self,
        image_path: str,
        base64_image: str,
        analysis_level: AnalysisLevel,
        specification_text: str,
        related_claims: list[str],
    ) -> DrawingAnalysisResult:
        """整体分析图纸"""

        # 构建提示词
        prompt = self._build_analysis_prompt(analysis_level, specification_text, related_claims)

        # 调用GLM-4V
        _messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ]

        # 压缩上下文(如果有对话历史)
        compressed_messages = self.context_compressor.compress_context(
            [{"role": "user", "content": prompt}]
        ).compressed_messages

        start_time = datetime.now()

        # 调用GLM API
        if self.glm_client:
            from services.ai_models.glm_full_suite.glm_unified_client import (
                GLMModel,
                GLMRequest,
                ModalityType,
            )

            request = GLMRequest(
                model=GLMModel.GLM_4V_PLUS,
                messages=compressed_messages,
                modality=ModalityType.MULTIMODAL,
                max_tokens=3000,
                temperature=0.3,
            )
            response = await self.glm_client.chat(request)

            if response.success:
                # 解析响应
                result = self._parse_analysis_response(response.content, image_path, analysis_level)
                result.processing_time = (datetime.now() - start_time).total_seconds()
                result.model_used = GLMModel.GLM_4V_PLUS.value
                result.tokens_used = response.usage.get("total_tokens", 0)

                # 更新统计
                self.stats["successful_analyses"] += 1
                self.stats["drawing_type_distribution"][result.drawing_type.value] = (
                    self.stats["drawing_type_distribution"].get(result.drawing_type.value, 0) + 1
                )

                return result
            else:
                raise Exception(f"GLM API调用失败: {response.error}")
        else:
            raise Exception("GLM客户端未初始化")

    async def _analyze_with_chunking(
        self,
        image_path: str,
        image_data: bytes,
        base64_image: str,
        analysis_level: AnalysisLevel,
        specification_text: str,
        related_claims: list[str],
    ) -> DrawingAnalysisResult:
        """分块分析大图纸"""
        self.logger.info(f"使用分块处理策略: {image_path}")

        # 1. 分块
        chunks = await self._chunk_image(image_data)

        self.stats["total_chunks_processed"] += len(chunks)
        self.logger.info(f"图像已分为 {len(chunks)} 块")

        # 2. 逐块分析
        chunk_results = []
        for i, chunk in enumerate(chunks):
            self.logger.info(f"分析第 {i+1}/{len(chunks)} 块...")

            prompt = self._build_chunk_analysis_prompt(chunk, i, len(chunks))

            if self.glm_client:
                from services.ai_models.glm_full_suite.glm_unified_client import (
                    GLMModel,
                    GLMRequest,
                    ModalityType,
                )

                request = GLMRequest(
                    model=GLMModel.GLM_4V_PLUS,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{chunk.image_data}"
                                    },
                                },
                                {"type": "text", "text": prompt},
                            ],
                        }
                    ],
                    modality=ModalityType.MULTIMODAL,
                    max_tokens=1500,  # 每块使用较少token
                    temperature=0.3,
                )

                response = await self.glm_client.chat(request)
                if response.success:
                    chunk_results.append(response.content)
                else:
                    self.logger.warning(f"第 {i+1} 块分析失败: {response.error}")

        # 3. 合并结果
        merged_result = await self._merge_chunk_results(chunk_results, image_path, analysis_level)

        # 4. 整体理解(可选)
        if len(chunks) > 1 and specification_text:
            # 基于说明书进行整体理解
            overall_prompt = f"""
基于以下分块分析结果和说明书文本,提供整体理解:

分块分析摘要:
{chr(10).join([f'{i+1}. {r[:200]}...' for i, r in enumerate(chunk_results)])}

说明书文本:
{specification_text[:1000]}

请提供:
1. 图纸整体类型和标题
2. 主要组件列表(合并所有分块的结果)
3. 整体工作原理
4. 与说明书的关联
"""

            # 使用GLM-4.6进行文本理解和合并
            from services.ai_models.glm_full_suite.glm_unified_client import (
                GLMModel,
                GLMRequest,
                ModalityType,
            )

            request = GLMRequest(
                model=GLMModel.GLM_4_6,
                messages=[{"role": "user", "content": overall_prompt}],
                modality=ModalityType.TEXT,
                max_tokens=2000,
                temperature=0.3,
            )

            response = await self.glm_client.chat(request)
            if response.success:
                # 更新合并结果
                merged_result = self._update_result_with_overall_understanding(
                    merged_result, response.content
                )

        return merged_result

    async def _load_and_preprocess_image(self, image_path: str) -> bytes:
        """加载和预处理图像"""
        # 读取图像
        img = cv2.imread(image_path)

        if img is None:
            raise ValueError(f"无法读取图像: {image_path}")

        # 调整大小(如果太大)
        height, width = img.shape[:2]
        if max(width, height) > self.max_image_size:
            scale = self.max_image_size / max(width, height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
            self.logger.info(f"图像已调整大小: {width}x{height} -> {new_width}x{new_height}")

        # 转换为JPEG格式
        _, buffer = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 85])
        return buffer.tobytes()

    async def _chunk_image(self, image_data: bytes) -> list[ImageChunk]:
        """将图像分块"""
        img = Image.open(io.BytesIO(image_data))
        width, height = img.size

        chunks = []
        chunk_id = 0

        # 计算分块数量
        cols = (width + self.chunk_size - 1) // self.chunk_size
        rows = (height + self.chunk_size - 1) // self.chunk_size

        for row in range(rows):
            for col in range(cols):
                x1 = col * self.chunk_size
                y1 = row * self.chunk_size
                x2 = min(x1 + self.chunk_size, width)
                y2 = min(y1 + self.chunk_size, height)

                # 裁剪图像
                chunk_img = img.crop((x1, y1, x2, y2))

                # 转换为base64
                buffer = io.BytesIO()
                chunk_img.save(buffer, format="JPEG", quality=85)
                chunk_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

                chunks.append(
                    ImageChunk(
                        chunk_id=chunk_id,
                        image_data=chunk_base64,
                        position={"x": x1, "y": y1, "width": x2 - x1, "height": y2 - y1},
                        description=f"分块{chunk_id+1} (位置: {x1},{y1})",
                    )
                )

                chunk_id += 1

        return chunks

    def _build_analysis_prompt(
        self, level: AnalysisLevel, specification_text: str, related_claims: list[str]
    ) -> str:
        """构建分析提示词"""

        base_prompt = "你是一位专业的技术图纸分析专家。请仔细分析这张技术图纸。"

        if level == AnalysisLevel.BASIC:
            prompt = f"""{base_prompt}

请提供:
1. 图纸类型(专利附图/机械图纸/电路图/流程图等)
2. 图纸标题和简要描述
3. 主要可见组件(列出5-10个)

请以JSON格式回复:
{{
    "drawing_type": "图纸类型",
    "title": "标题",
    "description": "描述",
    "components": ["组件1", "组件2", ...]
}}
"""

        elif level == AnalysisLevel.INTERMEDIATE:
            prompt = f"""{base_prompt}

请提供详细分析:
1. 图纸类型和标题
2. 整体描述
3. 所有识别的组件(包括编号和说明)
4. 技术特征(3-5点)
5. 图中的标注和说明文字

请以JSON格式回复:
{{
    "drawing_type": "图纸类型",
    "title": "标题",
    "description": "整体描述",
    "components": [{{"id": "编号", "name": "名称", "description": "说明"}}],
    "technical_features": ["特征1", "特征2", ...],
    "annotations": {{"标注": "说明"}}
}}
"""

        else:  # ADVANCED
            ref_text = ""
            if specification_text:
                ref_text = f"\n参考说明书:\n{specification_text[:1500]}"

            claims_text = ""
            if related_claims:
                claims_text = "\n相关权利要求:\n" + "\n".join(related_claims[:3])

            prompt = f"""{base_prompt}

请进行深度技术分析:{ref_text}{claims_text}

请提供:
1. 图纸类型和标题
2. 整体描述
3. 详细的组件分析(编号、名称、功能、位置关系)
4. 技术特征和工作原理
5. 与说明文的关联(对应说明书哪部分内容)
6. 支撑的权利要求

请以JSON格式回复:
{{
    "drawing_type": "图纸类型",
    "title": "标题",
    "description": "描述",
    "components": [{{"id": "编号", "name": "名称", "function": "功能", "position": "位置"}}],
    "technical_features": ["特征1", ...],
    "working_principle": "工作原理",
    "specification_reference": "参考段落",
    "related_claims": ["权利要求1", ...]
}}
"""

        return prompt

    def _build_chunk_analysis_prompt(
        self, chunk: ImageChunk, chunk_index: int, total_chunks: int
    ) -> str:
        """构建分块分析提示词"""
        return f"""你是技术图纸分析专家。这是图纸的第 {chunk_index + 1}/{total_chunks} 块。
{chunk.description}

请分析这一部分:
1. 可见的组件和编号
2. 文字标注和说明
3. 技术特征

请以简洁的JSON格式回复:
{{
    "components": [{{"id": "编号", "name": "名称", "description": "说明"}}],
    "annotations": {{"标注": "说明"}},
    "features": ["特征1", "特征2"]
}}
"""

    def _parse_analysis_response(
        self, response_content: str, image_path: str, analysis_level: AnalysisLevel
    ) -> DrawingAnalysisResult:
        """解析GLM响应"""
        try:
            # 尝试提取JSON
            json_match = re.search(r"\{[\s\S]*\}", response_content)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)

                # 映射图纸类型
                drawing_type = self._map_drawing_type(data.get("drawing_type", ""))

                result = DrawingAnalysisResult(
                    drawing_type=drawing_type,
                    file_path=image_path,
                    title=data.get("title", ""),
                    description=data.get("description", ""),
                    confidence=0.85,
                    analysis_level=analysis_level,
                )

                # 解析组件
                if "components" in data:
                    result.components = data["components"]

                # 解析标注
                if "annotations" in data:
                    result.annotations = data["annotations"]

                # 解析技术特征
                if "technical_features" in data:
                    result.technical_features = data["technical_features"]

                # 解析工作原理(高级分析)
                if "working_principle" in data:
                    result.working_principle = data["working_principle"]

                # 解析关联信息(高级分析)
                if "specification_reference" in data:
                    result.specification_reference = data["specification_reference"]
                if "related_claims" in data:
                    result.related_claims = data["related_claims"]

                return result
            else:
                # JSON解析失败,使用文本解析
                return self._parse_text_response(response_content, image_path, analysis_level)

        except Exception as e:
            self.logger.warning(f"JSON解析失败: {e!s}, 使用文本解析")
            return self._parse_text_response(response_content, image_path, analysis_level)

    def _parse_text_response(
        self, text: str, image_path: str, analysis_level: AnalysisLevel
    ) -> DrawingAnalysisResult:
        """解析文本响应"""
        return DrawingAnalysisResult(
            drawing_type=DrawingType.PATENT_DRAWING,
            file_path=image_path,
            description=text[:500],
            confidence=0.6,
            analysis_level=analysis_level,
        )

    def _map_drawing_type(self, type_str: str) -> DrawingType:
        """映射图纸类型"""
        type_mapping = {
            "专利附图": DrawingType.PATENT_DRAWING,
            "机械图纸": DrawingType.MECHANICAL_DRAWING,
            "电路图": DrawingType.CIRCUIT_DIAGRAM,
            "流程图": DrawingType.FLOWCHART,
            "结构图": DrawingType.STRUCTURE_DIAGRAM,
            "原理图": DrawingType.SCHEMATIC,
        }
        return type_mapping.get(type_str, DrawingType.PATENT_DRAWING)

    async def _merge_chunk_results(
        self, chunk_results: list[str], image_path: str, analysis_level: AnalysisLevel
    ) -> DrawingAnalysisResult:
        """合并分块分析结果"""
        # 简化实现:返回第一个结果的结构
        # 实际应该智能合并所有分块的结果
        return DrawingAnalysisResult(
            drawing_type=DrawingType.PATENT_DRAWING,
            file_path=image_path,
            description=f"分块分析结果(共{len(chunk_results)}块)",
            confidence=0.75,
            analysis_level=analysis_level,
        )

    def _update_result_with_overall_understanding(
        self, result: DrawingAnalysisResult, overall_content: str
    ) -> DrawingAnalysisResult:
        """使用整体理解更新结果"""
        result.description += f"\n\n整体理解:\n{overall_content[:500]}"
        return result

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()

    def reset_statistics(self) -> Any:
        """重置统计信息"""
        self.stats = {
            "total_analyses": 0,
            "successful_analyses": 0,
            "total_chunks_processed": 0,
            "average_processing_time": 0.0,
            "drawing_type_distribution": {},
        }


# 导出
__all__ = ["AnalysisLevel", "DrawingAnalysisResult", "DrawingType", "TechnicalDrawingAnalyzer"]
