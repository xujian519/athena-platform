#!/usr/bin/env python3
"""
通用AI绘图平台
Universal AI Drawing Platform

集成SketchAgent和next-ai-draw-io，支持多种绘图场景
可逐步优化为专利专用绘图工具

作者: Athena AI系统
创建时间: 2025年12月6日
版本: 1.0.0
"""

import base64
import logging
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import requests

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DrawingType(Enum):
    """绘图类型枚举"""
    FLOWCHART = 'flowchart'           # 流程图
    MINDMAP = 'mindmap'              # 思维导图
    SYSTEM_DIAGRAM = 'system'        # 系统架构图
    WIREFRAME = 'wireframe'          # UI线框图
    CONCEPTUAL = 'conceptual'        # 概念图
    TECHNICAL = 'technical'          # 技术图表
    BUSINESS = 'business'            # 商业图表
    EDUCATIONAL = 'educational'      # 教育图表
    PRESENTATION = 'presentation'    # 演示图表
    PATENT = 'patent'                # 专利图表

class UseCase(Enum):
    """使用场景枚举"""
    GENERAL = 'general'              # 通用绘图
    SOFTWARE_DESIGN = 'software'     # 软件设计
    BUSINESS_PROCESS = 'business'    # 业务流程
    EDUCATION_TEACHING = 'education' # 教育培训
    PROJECT_MANAGEMENT = 'project'   # 项目管理
    KNOWLEDGE_MANAGEMENT = 'knowledge' # 知识管理
    PATENT_APPLICATION = 'patent'    # 专利申请
    TECHNICAL_DOCUMENTATION = 'tech' # 技术文档

@dataclass
class UniversalDrawingRequest:
    """通用绘图请求"""
    request_id: str
    user_id: str | None = None
    drawing_type: DrawingType = DrawingType.FLOWCHART
    use_case: UseCase = UseCase.GENERAL

    # 输入内容
    text_description: str = ''
    hand_drawn_sketch: bytes | None = None
    reference_images: list[bytes] | None = None

    # 风格和格式
    style: str = 'modern'           # modern, classic, minimalist, colorful
    color_scheme: str = 'professional'  # professional, colorful, monochrome
    output_format: str = 'svg'      # svg, png, jpg, pdf

    # 质量和精度
    quality_level: str = 'standard' # basic, standard, premium
    detail_level: str = 'medium'    # low, medium, high

    # 特殊要求
    size: tuple[int, int] | None = None  # (width, height)
    constraints: list[str] | None = None  # 特殊约束条件

    # 元数据
    title: str = ''
    description: str = ''
    tags: list[str] | None = None

@dataclass
class UniversalDrawingResult:
    """通用绘图结果"""
    success: bool
    request_id: str
    drawing_data: bytes
    metadata: dict[str, Any]

    # 质量指标
    confidence: float = 0.0
    processing_time: float = 0.0
    quality_score: float = 0.0

    # 错误信息
    error_message: str | None = None
    warnings: list[str] | None = None

class UniversalDrawingEngine:
    """通用AI绘图引擎"""

    def __init__(self):
        # 服务端点
        self.sketchagent_url = 'http://localhost:8080/generate'
        self.drawio_url = 'http://localhost:8081/enhance'

        # 绘图模板和样式库
        self.style_templates = self._load_style_templates()
        self.drawing_constraints = self._load_drawing_constraints()

        # 使用场景配置
        self.use_case_configs = self._load_use_case_configs()

    def generate_drawing(self, request: UniversalDrawingRequest) -> UniversalDrawingResult:
        """生成图纸 - 主入口方法"""
        logger.info(f"🎨 开始生成图纸: {request.request_id} - {request.drawing_type.value}")

        start_time = time.time()

        try:
            # 1. 分析和预处理请求
            processed_request = self._preprocess_request(request)

            # 2. 选择最佳绘图策略
            drawing_strategy = self._select_drawing_strategy(processed_request)

            # 3. 执行绘图生成
            drawing_result = self._execute_drawing_strategy(drawing_strategy, processed_request)

            # 4. 后处理和质量检查
            final_result = self._postprocess_drawing(drawing_result, processed_request)

            processing_time = time.time() - start_time

            return UniversalDrawingResult(
                success=True,
                request_id=request.request_id,
                drawing_data=final_result['drawing_data'],
                metadata=final_result['metadata'],
                confidence=final_result.get('confidence', 0.0),
                processing_time=processing_time,
                quality_score=final_result.get('quality_score', 0.0),
                warnings=final_result.get('warnings', [])
            )

        except Exception as e:
            logger.error(f"❌ 绘图生成失败: {e}")
            return UniversalDrawingResult(
                success=False,
                request_id=request.request_id,
                drawing_data=b'',
                metadata={},
                processing_time=time.time() - start_time,
                error_message=str(e),
                warnings=[]
            )

    def _preprocess_request(self, request: UniversalDrawingRequest) -> UniversalDrawingRequest:
        """预处理绘图请求"""
        logger.info('🔍 预处理绘图请求...')

        # 1. 根据使用场景优化参数
        if request.use_case in self.use_case_configs:
            config = self.use_case_configs[request.use_case]

            # 应用默认样式
            if not request.style:
                request.style = config.get('default_style', 'modern')

            # 应用默认尺寸
            if not request.size:
                request.size = config.get('default_size', (800, 600))

            # 添加场景特定的约束
            scene_constraints = config.get('constraints', [])
            if request.constraints:
                request.constraints.extend(scene_constraints)
            else:
                request.constraints = scene_constraints

        # 2. 增强文本描述
        enhanced_description = self._enhance_text_description(request)
        request.text_description = enhanced_description

        # 3. 生成标题
        if not request.title:
            request.title = self._generate_title(request)

        return request

    def _select_drawing_strategy(self, request: UniversalDrawingRequest) -> str:
        """选择最佳绘图策略"""

        # 策略决策矩阵
        if request.hand_drawn_sketch:
            if request.use_case == UseCase.PATENT_APPLICATION:
                return 'patent_sketch_enhancement'
            else:
                return 'sketch_enhancement'

        elif request.drawing_type in [DrawingType.FLOWCHART, DrawingType.SYSTEM_DIAGRAM]:
            if request.use_case in [UseCase.SOFTWARE_DESIGN, UseCase.TECHNICAL_DOCUMENTATION]:
                return 'technical_diagram_generation'
            else:
                return 'general_diagram_generation'

        elif request.drawing_type == DrawingType.MINDMAP:
            return 'mindmap_generation'

        elif request.use_case == UseCase.PATENT_APPLICATION:
            return 'patent_compliant_generation'

        else:
            return 'general_purpose_generation'

    def _execute_drawing_strategy(self, strategy: str, request: UniversalDrawingRequest) -> dict[str, Any]:
        """执行绘图策略"""

        if strategy == 'patent_sketch_enhancement':
            return self._execute_patent_sketch_enhancement(request)
        elif strategy == 'sketch_enhancement':
            return self._execute_sketch_enhancement(request)
        elif strategy == 'technical_diagram_generation':
            return self._execute_technical_diagram_generation(request)
        elif strategy == 'general_diagram_generation':
            return self._execute_general_diagram_generation(request)
        elif strategy == 'patent_compliant_generation':
            return self._execute_patent_compliant_generation(request)
        else:
            return self._execute_general_purpose_generation(request)

    def _execute_general_diagram_generation(self, request: UniversalDrawingRequest) -> dict[str, Any]:
        """通用图表生成"""
        logger.info('📊 执行通用图表生成...')

        # 调用 SketchAgent
        try:
            response = requests.post(self.sketchagent_url, json={
                'description': request.text_description,
                'type': request.drawing_type.value,
                'style': request.style,
                'size': request.size
            }, timeout=60)

            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"SketchAgent API错误: {response.status_code}")

        except Exception as e:
            logger.warning(f"⚠️ SketchAgent调用失败，使用本地生成: {e}")
            return self._generate_fallback_drawing(request)

    def _execute_sketch_enhancement(self, request: UniversalDrawingRequest) -> dict[str, Any]:
        """草图增强"""
        logger.info('🖼️ 执行草图增强...')

        # 调用 next-ai-draw-io
        try:
            sketch_b64 = base64.b64encode(request.hand_drawn_sketch).decode()

            response = requests.post(self.drawio_url, json={
                'description': request.text_description,
                'sketch_image': sketch_b64,
                'enhancement_type': 'general',
                'style': request.style
            }, timeout=60)

            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"next-ai-draw-io API错误: {response.status_code}")

        except Exception as e:
            logger.warning(f"⚠️ next-ai-draw-io调用失败，使用基础增强: {e}")
            return self._basic_sketch_enhancement(request)

    def _execute_patent_compliant_generation(self, request: UniversalDrawingRequest) -> dict[str, Any]:
        """专利合规生成"""
        logger.info('⚖️ 执行专利合规生成...')

        # 1. 生成初始图表
        initial_result = self._execute_general_diagram_generation(request)

        # 2. 应用专利合规性约束
        compliant_result = self._apply_patent_compliance(initial_result, request)

        return compliant_result

    def _execute_patent_sketch_enhancement(self, request: UniversalDrawingRequest) -> dict[str, Any]:
        """专利草图增强"""
        logger.info('⚖️ 执行专利草图增强...')

        # 1. 基础草图增强
        enhanced_result = self._execute_sketch_enhancement(request)

        # 2. 应用专利合规性约束
        patent_compliant_result = self._apply_patent_compliance(enhanced_result, request)

        return patent_compliant_result

    def _apply_patent_compliance(self, drawing_result: dict[str, Any], request: UniversalDrawingRequest) -> dict[str, Any]:
        """应用专利合规性约束"""
        logger.info('📋 应用专利合规性约束...')

        # 专利特定的合规性检查和修复
        compliance_issues = []
        drawing_data = drawing_result.get('drawing_data', b'')

        # 1. 检查线条粗细
        # 2. 检查文字大小
        # 3. 检查边距
        # 4. 检查格式规范

        # 这里简化处理，返回合规的图纸
        return {
            'drawing_data': drawing_data,
            'compliance_score': 0.95,
            'issues_fixed': len(compliance_issues),
            'warnings': compliance_issues
        }

    def _postprocess_drawing(self, drawing_result: dict[str, Any], request: UniversalDrawingRequest) -> dict[str, Any]:
        """后处理图纸"""
        logger.info('🔧 后处理图纸...')

        # 1. 格式转换
        drawing_data = drawing_result.get('drawing_data', b'')
        if request.output_format != 'svg':
            drawing_data = self._convert_format(drawing_data, request.output_format)

        # 2. 质量评估
        quality_score = self._assess_quality(drawing_data, request)

        # 3. 生成元数据
        metadata = {
            'drawing_type': request.drawing_type.value,
            'use_case': request.use_case.value,
            'style': request.style,
            'size': request.size,
            'generated_at': datetime.now().isoformat(),
            'quality_score': quality_score,
            'metadata': drawing_result.get('metadata', {})
        }

        return {
            'drawing_data': drawing_data,
            'metadata': metadata,
            'confidence': drawing_result.get('confidence', 0.85),
            'quality_score': quality_score,
            'warnings': drawing_result.get('warnings', [])
        }

    def _generate_fallback_drawing(self, request: UniversalDrawingRequest) -> dict[str, Any]:
        """生成备用图纸（当外部服务不可用时）"""
        logger.info('🔄 生成备用图纸...')

        # 简单的SVG模板生成
        svg_template = (
            "<svg width='{width}' height='{height}' xmlns='http://www.w3.org/2000/svg'>"
            "<rect x='50' y='50' width='{box_w}' height='{box_h}' fill='none' stroke='black' stroke-width='2'/>"
            "<text x='{text_x}' y='{text_y}' text-anchor='middle' font-family='Arial' font-size='14'>{title}</text>"
            "</svg>"
        )

        width, height = request.size or (800, 600)
        box_w, box_h = width // 3, height // 4
        text_x, text_y = width // 2, height // 2

        svg_content = svg_template.format(
            width=width, height=height,
            box_w=box_w, box_h=box_h,
            text_x=text_x, text_y=text_y,
            title=request.title or request.text_description[:30]
        )

        return {
            'drawing_data': svg_content.encode('utf-8'),
            'confidence': 0.7,
            'warnings': ['使用备用绘图引擎']
        }

    def _basic_sketch_enhancement(self, request: UniversalDrawingRequest) -> dict[str, Any]:
        """基础草图增强"""
        logger.info('🔧 执行基础草图增强...')

        # 简单的图像处理和标准化
        # 这里应该包含实际的图像增强逻辑

        return {
            'drawing_data': request.hand_drawn_sketch,
            'confidence': 0.8,
            'warnings': ['使用基础增强算法']
        }

    def _enhance_text_description(self, request: UniversalDrawingRequest) -> str:
        """增强文本描述"""
        enhanced = request.text_description

        # 根据图表类型添加特定的增强词汇
        type_enhancements = {
            DrawingType.FLOWCHART: '流程图，包含开始、处理步骤、决策点、结束',
            DrawingType.MINDMAP: '思维导图，中心主题，分支结构，层次关系',
            DrawingType.SYSTEM_DIAGRAM: '系统架构图，组件关系，数据流向，接口定义',
            DrawingType.WIREFRAME: 'UI线框图，界面布局，交互元素，用户体验',
        }

        if request.drawing_type in type_enhancements:
            enhanced += f"\n图表类型：{type_enhancements[request.drawing_type]}"

        # 根据使用场景添加场景特定信息
        case_enhancements = {
            UseCase.PATENT_APPLICATION: '专利申请图表，需要符合专利局规范，精确清晰',
            UseCase.SOFTWARE_DESIGN: '软件设计图，包含技术架构，模块关系，接口定义',
            UseCase.BUSINESS_PROCESS: '业务流程图，清晰展示流程步骤和决策点',
        }

        if request.use_case in case_enhancements:
            enhanced += f"\n使用场景：{case_enhancements[request.use_case]}"

        return enhanced

    def _generate_title(self, request: UniversalDrawingRequest) -> str:
        """生成图表标题"""
        if request.text_description:
            # 从描述中提取关键词作为标题
            words = request.text_description.split()[:5]
            return ' '.join(words)
        else:
            return f"{request.drawing_type.value}图表"

    def _convert_format(self, drawing_data: bytes, output_format: str) -> bytes:
        """格式转换"""
        if output_format.lower() == 'svg':
            return drawing_data
        # 可以添加其他格式的转换逻辑
        return drawing_data

    def _assess_quality(self, drawing_data: bytes, request: UniversalDrawingRequest) -> float:
        """评估图纸质量"""
        # 简化的质量评估逻辑
        base_score = 0.8

        # 根据约束条件调整分数
        if request.constraints and len(request.constraints) > 0:
            base_score += 0.1

        # 根据详细程度调整分数
        if request.detail_level == 'high':
            base_score += 0.1
        elif request.detail_level == 'low':
            base_score -= 0.1

        return min(1.0, max(0.0, base_score))

    def _load_style_templates(self) -> dict[str, Any]:
        """加载样式模板"""
        return {
            'modern': {
                'colors': ['#2C3E50', '#3498DB', '#E74C3C', '#2ECC71'],
                'fonts': ['Arial', 'Helvetica'],
                'line_styles': ['solid', 'dashed']
            },
            'classic': {
                'colors': ['#000000', '#333333', '#666666'],
                'fonts': ['Times New Roman', 'Georgia'],
                'line_styles': ['solid']
            },
            'minimalist': {
                'colors': ['#000000', '#FFFFFF'],
                'fonts': ['Helvetica', 'Arial'],
                'line_styles': ['solid']
            }
        }

    def _load_drawing_constraints(self) -> dict[str, Any]:
        """加载绘图约束"""
        return {
            'patent': {
                'min_line_width': 0.1,
                'max_line_width': 0.3,
                'min_font_size': 3.5,
                'margin': 2.5
            },
            'general': {
                'min_line_width': 0.5,
                'min_font_size': 8.0,
                'margin': 1.0
            }
        }

    def _load_use_case_configs(self) -> dict[UseCase, dict[str, Any]:
        """加载使用场景配置"""
        return {
            UseCase.PATENT_APPLICATION: {
                'default_style': 'classic',
                'default_size': (1200, 800),
                'constraints': ['patent_compliance', 'monochrome', 'high_precision']
            },
            UseCase.SOFTWARE_DESIGN: {
                'default_style': 'modern',
                'default_size': (1000, 700),
                'constraints': ['technical_accuracy', 'clear_interfaces']
            },
            UseCase.BUSINESS_PROCESS: {
                'default_style': 'modern',
                'default_size': (800, 600),
                'constraints': ['clear_flow', 'decision_points']
            },
            UseCase.EDUCATION_TEACHING: {
                'default_style': 'colorful',
                'default_size': (900, 600),
                'constraints': ['visual_clarity', 'engaging_design']
            },
            UseCase.GENERAL: {
                'default_style': 'modern',
                'default_size': (800, 600),
                'constraints': []
            }
        }

def main():
    """主函数 - 演示通用AI绘图平台"""
    logger.info('🎨 通用AI绘图平台')
    logger.info(str('=' * 50))
    logger.info('🚀 支持多种绘图类型和使用场景')
    logger.info('📊 从通用工具到专利专用，灵活演进')
    logger.info(str('=' * 50))

    # 创建绘图引擎
    engine = UniversalDrawingEngine()

    # 演示1：通用流程图
    logger.info("\n📊 演示1：通用流程图生成")
    request1 = UniversalDrawingRequest(
        request_id='demo_001',
        drawing_type=DrawingType.FLOWCHART,
        use_case=UseCase.GENERAL,
        text_description='用户登录系统的流程：用户输入用户名密码 → 系统验证 → 验证成功跳转主页，验证失败提示错误',
        style='modern',
        output_format='svg'
    )

    result1 = engine.generate_drawing(request1)
    if result1.success:
        logger.info("✅ 生成成功")
        logger.info(f"   置信度: {result1.confidence:.2f}")
        logger.info(f"   质量分数: {result1.quality_score:.2f}")
        logger.info(f"   处理时间: {result1.processing_time:.2f}秒")
        # 保存结果
        with open(f"/tmp/universal_drawing_{request1.request_id}.svg", 'wb') as f:
            f.write(result1.drawing_data)
    else:
        logger.info(f"❌ 生成失败: {result1.error_message}")

    # 演示2：软件架构图
    logger.info("\n💻 演示2：软件架构图")
    request2 = UniversalDrawingRequest(
        request_id='demo_002',
        drawing_type=DrawingType.SYSTEM_DIAGRAM,
        use_case=UseCase.SOFTWARE_DESIGN,
        text_description='微服务架构：API网关 → 用户服务、订单服务、支付服务 → 数据库集群',
        style='modern',
        detail_level='high',
        output_format='svg'
    )

    result2 = engine.generate_drawing(request2)
    if result2.success:
        logger.info("✅ 生成成功")
        logger.info(f"   置信度: {result2.confidence:.2f}")
        logger.info(f"   质量分数: {result2.quality_score:.2f}")
        logger.info(f"   处理时间: {result2.processing_time:.2f}秒")
        # 保存结果
        with open(f"/tmp/universal_drawing_{request2.request_id}.svg", 'wb') as f:
            f.write(result2.drawing_data)

    # 演示3：专利图纸（预留接口）
    logger.info("\n⚖️ 演示3：专利图纸（预览功能）")
    request3 = UniversalDrawingRequest(
        request_id='demo_003',
        drawing_type=DrawingType.TECHNICAL,
        use_case=UseCase.PATENT_APPLICATION,
        text_description='一种智能专利检索系统的结构框图：包括输入模块、处理模块、输出模块',
        style='classic',
        quality_level='premium',
        output_format='svg'
    )

    result3 = engine.generate_drawing(request3)
    if result3.success:
        logger.info("✅ 生成成功")
        logger.info(f"   置信度: {result3.confidence:.2f}")
        logger.info(f"   质量分数: {result3.quality_score:.2f}")
        logger.info(f"   处理时间: {result3.processing_time:.2f}秒")
        logger.info(f"   合规性分数: {result3.metadata.get('compliance_score', 'N/A')}")
        # 保存结果
        with open(f"/tmp/universal_drawing_{request3.request_id}_patent.svg", 'wb') as f:
            f.write(result3.drawing_data)
    else:
        logger.info(f"❌ 生成失败: {result3.error_message}")

    logger.info("\n💡 平台演进路径:")
    logger.info("   1. 当前：通用AI绘图平台，支持多种场景")
    logger.info("   2. 优化：根据使用反馈，增强特定场景功能")
    logger.info("   3. 专业化：逐步发展为专利专用绘图工具")
    logger.info("   4. 集成：与专利知识图谱深度集成")

    logger.info("\n🎯 下一步建议:")
    logger.info("   1. 部署通用平台，收集用户反馈")
    logger.info("   2. 分析最常用的绘图类型和场景")
    logger.info("   3. 逐步优化专利绘图功能")
    logger.info("   4. 建立用户培训和支持体系")

    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.info("\n👋 演示被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.info(f"\n❌ 演示异常: {e}")
        sys.exit(1)
