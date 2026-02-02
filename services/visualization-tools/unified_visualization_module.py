#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一可视化创建模块
Unified Visualization Creation Module

将SketchAgent、draw.io、ECharts、Excalidraw等工具进行统一管理
提供Athena和小诺智能决策和调用能力

作者: Athena AI系统
创建时间: 2025年12月7日
版本: 1.0.0
"""

import asyncio
import json
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

try:
from intelligent_caller import ScenarioContext, ToolSelection, intelligent_caller
    pass  # 实际导入在下面
except ImportError:
    intelligent_caller = None  # 可选依赖未安装

# 导入LangChain基础
from langchain.tools import BaseTool

# 导入现有可视化工具
from langchain_tools import DrawIOTool, EChartsTool, ExcalidrawTool
from pydantic import BaseModel, Field
from visualization_insights import VisualizationAnalyzer, VisualizationType

logger = logging.getLogger(__name__)

class VisualizationTool(Enum):
    """可视化工具枚举"""
    SKETCHAGENT = 'sketchagent'
    DRAWIO = 'drawio'
    ECHARTS = 'echarts'
    EXCALIDRAW = 'excalidraw'

class VisualizationCategory(Enum):
    """可视化类别枚举"""
    DIAGRAM = 'diagram'           # 图表类（流程图、架构图等）
    CHART = 'chart'              # 数据图表类（柱状图、折线图等）
    SKETCH = 'sketch'            # 草图类（手绘、原型等）
    INTERACTIVE = 'interactive'   # 交互类（可交互仪表板等）

class ComplexityLevel(Enum):
    """复杂度级别"""
    SIMPLE = 'simple'            # 简单：单一工具即可完成
    MEDIUM = 'medium'            # 中等：可能需要工具协作
    COMPLEX = 'complex'          # 复杂：需要多工具组合

@dataclass
class VisualizationRequest:
    """可视化请求"""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # 用户输入
    query: str = ''                           # 用户查询描述
    raw_data: Optional[Dict[str, Any]] = None  # 原始数据（用于图表）
    sketch_image: bytes | None = None      # 手绘草图图像

    # 分类信息
    category: VisualizationCategory | None = None
    complexity: ComplexityLevel = ComplexityLevel.SIMPLE

    # 输出要求
    output_format: str = 'svg'                # svg, png, jpg, json, html
    style: str = 'modern'                     # modern, classic, minimalist, hand_drawn
    size: Tuple[int, int] = (800, 600)       # (width, height)

    # 上下文信息
    use_case: str = 'general'                 # general, patent, presentation, documentation
    audience: str = 'technical'               # technical, business, general
    collaboration_needed: bool = False        # 是否需要协作

    # 元数据
    title: str = ''
    description: str = ''
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class VisualizationResult:
    """可视化结果"""
    success: bool
    request_id: str
    tool_used: str
    category: str

    # 输出内容
    result_data: Union[str, bytes, Dict[str, Any]]
    metadata: Dict[str, Any]

    # 质量指标
    confidence: float = 0.0
    quality_score: float = 0.0
    processing_time: float = 0.0

    # 多工具协作信息
    primary_result: Any | None = None
    secondary_results: List[Any] = field(default_factory=list)

    # 错误信息
    error_message: str | None = None
    warnings: List[str] = field(default_factory=list)

    # 时间戳
    created_at: datetime = field(default_factory=datetime.now)

class BaseVisualizationTool(ABC):
    """可视化工具基类"""

    def __init__(self, name: str, tool_type: VisualizationTool):
        self.name = name
        self.tool_type = tool_type
        self.langchain_tool = None

    @abstractmethod
    async def can_handle(self, request: VisualizationRequest) -> Tuple[bool, float]:
        """判断是否能处理该请求，返回(是否可以处理, 置信度)"""
        pass

    @abstractmethod
    async def process_request(self, request: VisualizationRequest) -> VisualizationResult:
        """处理可视化请求"""
        pass

    @abstractmethod
    def get_supported_categories(self) -> List[VisualizationCategory]:
        """获取支持的类别"""
        pass

    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """获取支持的输出格式"""
        pass

class SketchAgentTool(BaseVisualizationTool):
    """SketchAgent工具包装器"""

    def __init__(self):
        super().__init__('SketchAgent', VisualizationTool.SKETCHAGENT)
        self.api_endpoint = 'http://localhost:8080/generate'

    async def can_handle(self, request: VisualizationRequest) -> Tuple[bool, float]:
        """判断SketchAgent是否能处理该请求"""
        confidence = 0.0

        # 基础能力检查
        if not request.query:
            return False, 0.0

        # 草图增强场景
        if request.sketch_image:
            confidence += 0.4

        # 技术图表场景
        if request.category in [VisualizationCategory.DIAGRAM, VisualizationCategory.SKETCH]:
            confidence += 0.3

        # 专利和文档场景
        if request.use_case in ['patent', 'documentation']:
            confidence += 0.2

        # 简单复杂度更适合
        if request.complexity == ComplexityLevel.SIMPLE:
            confidence += 0.1

        return confidence > 0.3, min(confidence, 1.0)

    async def process_request(self, request: VisualizationRequest) -> VisualizationResult:
        """处理SketchAgent请求"""
        start_time = datetime.now()

        try:
            # 构建请求数据
            payload = {
                'description': request.query,
                'type': 'flowchart',  # 默认流程图
                'style': request.style
            }

            # 如果有草图图像，进行编码
            if request.sketch_image:
                import base64
                sketch_b64 = base64.b64encode(request.sketch_image).decode()
                payload['sketch_image'] = sketch_b64

            # 调用SketchAgent API
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_endpoint, json=payload, timeout=60) as response:
                    if response.status == 200:
                        result_data = await response.json()

                        processing_time = (datetime.now() - start_time).total_seconds()

                        return VisualizationResult(
                            success=True,
                            request_id=request.request_id,
                            tool_used=self.name,
                            category=request.category.value if request.category else 'unknown',
                            result_data=result_data.get('drawing_data', ''),
                            metadata=result_data.get('metadata', {}),
                            confidence=result_data.get('confidence', 0.8),
                            quality_score=0.8,
                            processing_time=processing_time
                        )
                    else:
                        raise Exception(f"SketchAgent API错误: {response.status}")

        except Exception as e:
            logger.error(f"SketchAgent处理失败: {e}")
            return VisualizationResult(
                success=False,
                request_id=request.request_id,
                tool_used=self.name,
                category='error',
                result_data='',
                metadata={},
                processing_time=(datetime.now() - start_time).total_seconds(),
                error_message=str(e)
            )

    def get_supported_categories(self) -> List[VisualizationCategory]:
        return [VisualizationCategory.DIAGRAM, VisualizationCategory.SKETCH]

    def get_supported_formats(self) -> List[str]:
        return ['svg', 'png', 'jpg']

class DrawIOToolAdapter(BaseVisualizationTool):
    """Draw.io工具适配器"""

    def __init__(self):
        super().__init__('Draw.io', VisualizationTool.DRAWIO)
        # 使用现有的LangChain工具
        self.langchain_tool = DrawIOTool()

    async def can_handle(self, request: VisualizationRequest) -> Tuple[bool, float]:
        """判断Draw.io是否能处理该请求"""
        confidence = 0.0

        # 基础能力检查
        if not request.query:
            return False, 0.0

        # 专业图表场景
        if request.category == VisualizationCategory.DIAGRAM:
            confidence += 0.4

        # 技术文档场景
        if request.use_case in ['technical', 'documentation', 'patent']:
            confidence += 0.3

        # 复杂图表更适合
        if request.complexity in [ComplexityLevel.MEDIUM, ComplexityLevel.COMPLEX]:
            confidence += 0.2

        # 专业风格
        if request.style in ['modern', 'classic', 'minimalist']:
            confidence += 0.1

        return confidence > 0.3, min(confidence, 1.0)

    async def process_request(self, request: VisualizationRequest) -> VisualizationResult:
        """处理Draw.io请求"""
        start_time = datetime.now()

        try:
            # 构建参数
            params = {
                'description': request.query,
                'diagram_type': 'flowchart',
                'style': request.style,
                'output_format': request.output_format
            }

            # 调用LangChain工具
            if hasattr(self.langchain_tool, '_arun'):
                result = await self.langchain_tool._arun(json.dumps(params))
            else:
                result = self.langchain_tool._run(json.dumps(params))

            processing_time = (datetime.now() - start_time).total_seconds()

            return VisualizationResult(
                success=True,
                request_id=request.request_id,
                tool_used=self.name,
                category=request.category.value if request.category else 'diagram',
                result_data=result,
                metadata={'tool': 'drawio', 'format': request.output_format},
                confidence=0.9,
                quality_score=0.85,
                processing_time=processing_time
            )

        except Exception as e:
            logger.error(f"Draw.io处理失败: {e}")
            return VisualizationResult(
                success=False,
                request_id=request.request_id,
                tool_used=self.name,
                category='error',
                result_data='',
                metadata={},
                processing_time=(datetime.now() - start_time).total_seconds(),
                error_message=str(e)
            )

    def get_supported_categories(self) -> List[VisualizationCategory]:
        return [VisualizationCategory.DIAGRAM]

    def get_supported_formats(self) -> List[str]:
        return ['svg', 'png', 'jpg', 'xml', 'html']

class EChartsToolAdapter(BaseVisualizationTool):
    """ECharts工具适配器"""

    def __init__(self):
        super().__init__('ECharts', VisualizationTool.ECHARTS)
        self.langchain_tool = EChartsTool()

    async def can_handle(self, request: VisualizationRequest) -> Tuple[bool, float]:
        """判断ECharts是否能处理该请求"""
        confidence = 0.0

        # 基础能力检查
        if not request.query:
            return False, 0.0

        # 数据图表场景
        if request.category == VisualizationCategory.CHART:
            confidence += 0.5

        # 有数据输入
        if request.raw_data:
            confidence += 0.3

        # 交互式需求
        if request.category == VisualizationCategory.INTERACTIVE:
            confidence += 0.2

        return confidence > 0.3, min(confidence, 1.0)

    async def process_request(self, request: VisualizationRequest) -> VisualizationResult:
        """处理ECharts请求"""
        start_time = datetime.now()

        try:
            # 构建参数
            params = {
                'description': request.query,
                'chart_type': 'auto',
                'data': request.raw_data or {},
                'interactive': True,
                'output_format': request.output_format
            }

            # 调用LangChain工具
            if hasattr(self.langchain_tool, '_arun'):
                result = await self.langchain_tool._arun(json.dumps(params))
            else:
                result = self.langchain_tool._run(json.dumps(params))

            processing_time = (datetime.now() - start_time).total_seconds()

            return VisualizationResult(
                success=True,
                request_id=request.request_id,
                tool_used=self.name,
                category=request.category.value if request.category else 'chart',
                result_data=result,
                metadata={'tool': 'echarts', 'interactive': True},
                confidence=0.9,
                quality_score=0.9,
                processing_time=processing_time
            )

        except Exception as e:
            logger.error(f"ECharts处理失败: {e}")
            return VisualizationResult(
                success=False,
                request_id=request.request_id,
                tool_used=self.name,
                category='error',
                result_data='',
                metadata={},
                processing_time=(datetime.now() - start_time).total_seconds(),
                error_message=str(e)
            )

    def get_supported_categories(self) -> List[VisualizationCategory]:
        return [VisualizationCategory.CHART, VisualizationCategory.INTERACTIVE]

    def get_supported_formats(self) -> List[str]:
        return ['html', 'json', 'png', 'jpg']

class ExcalidrawToolAdapter(BaseVisualizationTool):
    """Excalidraw工具适配器"""

    def __init__(self):
        super().__init__('Excalidraw', VisualizationTool.EXCALIDRAW)
        self.langchain_tool = ExcalidrawTool()

    async def can_handle(self, request: VisualizationRequest) -> Tuple[bool, float]:
        """判断Excalidraw是否能处理该请求"""
        confidence = 0.0

        # 基础能力检查
        if not request.query:
            return False, 0.0

        # 草图和手绘场景
        if request.category in [VisualizationCategory.SKETCH, VisualizationCategory.DIAGRAM]:
            confidence += 0.3

        # 协作需求
        if request.collaboration_needed:
            confidence += 0.4

        # 手绘风格
        if request.style == 'hand_drawn':
            confidence += 0.3

        return confidence > 0.3, min(confidence, 1.0)

    async def process_request(self, request: VisualizationRequest) -> VisualizationResult:
        """处理Excalidraw请求"""
        start_time = datetime.now()

        try:
            # 构建参数
            params = {
                'description': request.query,
                'drawing_type': 'whiteboard',
                'style': 'hand_drawn',
                'collaborative': request.collaboration_needed,
                'output_format': request.output_format
            }

            # 调用LangChain工具
            if hasattr(self.langchain_tool, '_arun'):
                result = await self.langchain_tool._arun(json.dumps(params))
            else:
                result = self.langchain_tool._run(json.dumps(params))

            processing_time = (datetime.now() - start_time).total_seconds()

            return VisualizationResult(
                success=True,
                request_id=request.request_id,
                tool_used=self.name,
                category=request.category.value if request.category else 'sketch',
                result_data=result,
                metadata={'tool': 'excalidraw', 'collaborative': request.collaboration_needed},
                confidence=0.85,
                quality_score=0.8,
                processing_time=processing_time
            )

        except Exception as e:
            logger.error(f"Excalidraw处理失败: {e}")
            return VisualizationResult(
                success=False,
                request_id=request.request_id,
                tool_used=self.name,
                category='error',
                result_data='',
                metadata={},
                processing_time=(datetime.now() - start_time).total_seconds(),
                error_message=str(e)
            )

    def get_supported_categories(self) -> List[VisualizationCategory]:
        return [VisualizationCategory.SKETCH, VisualizationCategory.DIAGRAM]

    def get_supported_formats(self) -> List[str]:
        return ['svg', 'png', 'jpg', 'json', 'html']

class UnifiedVisualizationManager:
    """统一可视化管理器"""

    def __init__(self):
        self.tools: List[BaseVisualizationTool] = []
        self.analyzer = VisualizationAnalyzer()
        self.intelligent_caller = intelligent_caller

        # 初始化所有工具
        self._initialize_tools()

    def _initialize_tools(self) -> Any:
        """初始化所有可视化工具"""
        self.tools = [
            SketchAgentTool(),
            DrawIOToolAdapter(),
            EChartsToolAdapter(),
            ExcalidrawToolAdapter()
        ]

        logger.info(f"✅ 已初始化 {len(self.tools)} 个可视化工具")

    async def analyze_request(self, request: VisualizationRequest) -> VisualizationRequest:
        """分析请求，自动分类和确定复杂度"""

        # 使用智能调用器分析请求
        try:
            scenario_context = await self.intelligent_caller.analyze_request(request.query)

            # 基于分析结果设置分类
            if scenario_context.data_type in ['numerical', 'time_series']:
                request.category = VisualizationCategory.CHART
            elif scenario_context.intent in ['system_design', 'documentation']:
                request.category = VisualizationCategory.DIAGRAM
            elif scenario_context.aesthetic_preference == 'hand_drawn':
                request.category = VisualizationCategory.SKETCH
            else:
                request.category = VisualizationCategory.DIAGRAM

            # 设置协作需求
            request.collaboration_needed = scenario_context.collaboration_needed

            # 确定复杂度
            if scenario_context.data_type == 'mixed' or request.collaboration_needed:
                request.complexity = ComplexityLevel.COMPLEX
            elif request.raw_data or request.sketch_image:
                request.complexity = ComplexityLevel.MEDIUM
            else:
                request.complexity = ComplexityLevel.SIMPLE

        except Exception as e:
            logger.warning(f"智能分析失败，使用默认分析: {e}")

            # 降级分析
            request.category = self._basic_category_analysis(request.query)
            request.complexity = self._basic_complexity_analysis(request)

        return request

    def _basic_category_analysis(self, query: str) -> VisualizationCategory:
        """基础分类分析"""
        query_lower = query.lower()

        if any(word in query_lower for word in ['data', '数据', 'chart', '图表', '统计', '趋势']):
            return VisualizationCategory.CHART
        elif any(word in query_lower for word in ['sketch', '草图', 'mockup', '原型', '手绘']):
            return VisualizationCategory.SKETCH
        elif any(word in query_lower for word in ['interactive', '交互', 'dashboard', '仪表板']):
            return VisualizationCategory.INTERACTIVE
        else:
            return VisualizationCategory.DIAGRAM

    def _basic_complexity_analysis(self, request: VisualizationRequest) -> ComplexityLevel:
        """基础复杂度分析"""
        complexity_score = 0

        # 数据输入增加复杂度
        if request.raw_data:
            complexity_score += 1

        # 草图输入增加复杂度
        if request.sketch_image:
            complexity_score += 1

        # 协作需求增加复杂度
        if request.collaboration_needed:
            complexity_score += 1

        if complexity_score >= 2:
            return ComplexityLevel.COMPLEX
        elif complexity_score == 1:
            return ComplexityLevel.MEDIUM
        else:
            return ComplexityLevel.SIMPLE

    async def select_best_tool(self, request: VisualizationRequest) -> Tuple[BaseVisualizationTool, float]:
        """选择最佳工具"""

        best_tool = None
        best_confidence = 0.0

        # 并行评估所有工具
        tool_evaluations = []
        for tool in self.tools:
            can_handle, confidence = await tool.can_handle(request)
            if can_handle:
                tool_evaluations.append((tool, confidence))

                if confidence > best_confidence:
                    best_tool = tool
                    best_confidence = confidence

        if best_tool is None:
            logger.warning('没有工具能处理该请求，使用默认工具')
            best_tool = self.tools[0]  # 默认使用第一个工具
            best_confidence = 0.5

        logger.info(f"🎯 选择工具: {best_tool.name} (置信度: {best_confidence:.2f})")
        return best_tool, best_confidence

    async def create_visualization(self, request: VisualizationRequest) -> VisualizationResult:
        """创建可视化内容 - 主入口方法"""
        logger.info(f"🎨 开始创建可视化: {request.request_id}")

        # 1. 分析请求
        analyzed_request = await self.analyze_request(request)

        # 2. 选择最佳工具
        selected_tool, confidence = await self.select_best_tool(analyzed_request)

        # 3. 处理请求
        if analyzed_request.complexity == ComplexityLevel.COMPLEX:
            # 复杂请求可能需要多工具协作
            result = await self._handle_complex_request(analyzed_request, selected_tool)
        else:
            # 简单和中等请求使用单一工具
            result = await selected_tool.process_request(analyzed_request)

        # 4. 记录和学习
        await self._learn_from_result(analyzed_request, result)

        return result

    async def _handle_complex_request(self, request: VisualizationRequest, primary_tool: BaseVisualizationTool) -> VisualizationResult:
        """处理复杂请求（多工具协作）"""
        logger.info(f"🔄 处理复杂请求，使用多工具协作")

        # 并行调用多个工具
        tasks = []

        # 主工具
        tasks.append(primary_tool.process_request(request))

        # 添加辅助工具
        for tool in self.tools:
            if tool != primary_tool:
                can_handle, _ = await tool.can_handle(request)
                if can_handle and len(tasks) < 3:  # 最多使用3个工具
                    # 创建辅助请求
                    aux_request = VisualizationRequest(
                        request_id=f"{request.request_id}_aux_{tool.name}",
                        query=f"辅助视角: {request.query}",
                        category=request.category,
                        complexity=ComplexityLevel.SIMPLE,
                        output_format=request.output_format
                    )
                    tasks.append(tool.process_request(aux_request))

        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        primary_result = results[0] if not isinstance(results[0], Exception) else None
        secondary_results = []

        for result in results[1:]:
            if isinstance(result, Exception):
                logger.warning(f"辅助工具执行失败: {result}")
            else:
                secondary_results.append(result)

        # 合并结果
        if primary_result:
            primary_result.secondary_results = secondary_results
            if secondary_results:
                primary_result.metadata['collaboration_tools'] = [r.tool_used for r in secondary_results]

        return primary_result or VisualizationResult(
            success=False,
            request_id=request.request_id,
            tool_used='none',
            category='error',
            result_data='',
            metadata={},
            error_message='所有工具执行失败'
        )

    async def _learn_from_result(self, request: VisualizationRequest, result: VisualizationResult):
        """从结果中学习"""
        try:
            # 构建学习数据
            learning_data = {
                'request': {
                    'query': request.query,
                    'category': request.category.value if request.category else None,
                    'complexity': request.complexity.value,
                    'use_case': request.use_case,
                    'collaboration_needed': request.collaboration_needed
                },
                'result': {
                    'success': result.success,
                    'tool_used': result.tool_used,
                    'confidence': result.confidence,
                    'quality_score': result.quality_score,
                    'processing_time': result.processing_time
                }
            }

            # 这里可以实现学习逻辑，比如更新工具选择权重等
            # 暂时只记录日志
            logger.info(f"📚 学习记录: {json.dumps(learning_data, ensure_ascii=False, indent=2)}")

        except Exception as e:
            logger.warning(f"学习记录失败: {e}")

    def get_tool_status(self) -> Dict[str, Any]:
        """获取所有工具状态"""
        return {
            'total_tools': len(self.tools),
            'tools': [
                {
                    'name': tool.name,
                    'type': tool.tool_type.value,
                    'categories': [cat.value for cat in tool.get_supported_categories()],
                    'formats': tool.get_supported_formats()
                }
                for tool in self.tools
            ]
        }

# 全局管理器实例
unified_manager = UnifiedVisualizationManager()

# 便捷函数
async def create_visualization(query: str, **kwargs) -> VisualizationResult:
    """便捷的可视化创建函数"""
    request = VisualizationRequest(query=query, **kwargs)
    return await unified_manager.create_visualization(request)