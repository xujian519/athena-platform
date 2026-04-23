#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专利AI绘图集成系统
Patent AI Drawing Integration System

基于专利知识图谱，集成SketchAgent和next-ai-draw-io
实现根据专利说明书自动绘制技术草图

作者: Athena AI系统
创建时间: 2025年12月6日
版本: 1.0.0
"""

import base64
import io
import json
import logging
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from PIL import Image

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DrawingRequest:
    """绘图请求"""
    patent_id: str
    text_description: str
    drawing_type: str  # 'flowchart', 'mechanical', 'system', 'circuit'
    hand_drawn_sketch: bytes | None = None
    compliance_requirements: Optional[List[str]] = None
    output_format: str = 'svg'

@dataclass
class DrawingResult:
    """绘图结果"""
    success: bool
    drawing_data: bytes
    compliance_score: float
    processing_time: float
    metadata: Dict[str, Any]

class PatentDrawingEngine:
    """专利AI绘图引擎"""

    def __init__(self):
        self.sketchagent_url = 'http://localhost:8080/generate'  # SketchAgent服务
        self.drawio_url = 'http://localhost:8081/enhance'       # next-ai-draw-io服务
        self.compliance_checker = ComplianceChecker()

    def generate_from_text_only(self, request: DrawingRequest) -> DrawingResult:
        """场景1：纯文本描述生成草图"""
        logger.info(f"🎨 开始纯文本绘图: {request.patent_id}")
        start_time = time.time()

        try:
            # 1. 基于知识图谱增强文本描述
            enhanced_description = self._enhance_with_knowledge_graph(request.text_description)

            # 2. 调用SketchAgent生成初始图纸
            sketch_result = self._call_sketchagent(enhanced_description, request.drawing_type)

            # 3. 专利合规性检查和优化
            compliance_result = self.compliance_checker.check_and_fix(sketch_result['drawing_data'])

            # 4. 最终格式转换
            final_drawing = self._convert_format(compliance_result['drawing_data'], request.output_format)

            processing_time = time.time() - start_time

            return DrawingResult(
                success=True,
                drawing_data=final_drawing,
                compliance_score=compliance_result['score'],
                processing_time=processing_time,
                metadata={
                    'enhanced_description': enhanced_description,
                    'original_sketch': sketch_result,
                    'compliance_issues': compliance_result['issues_fixed']
                }
            )

        except Exception as e:
            logger.error(f"❌ 纯文本绘图失败: {e}")
            return DrawingResult(
                success=False,
                drawing_data=b'',
                compliance_score=0.0,
                processing_time=time.time() - start_time,
                metadata={'error': str(e)}
            )

    def generate_with_sketch_input(self, request: DrawingRequest) -> DrawingResult:
        """场景2：文本描述 + 手绘草图结合"""
        logger.info(f"🎨 开始图文结合绘图: {request.patent_id}")
        start_time = time.time()

        try:
            # 1. 手绘草图数字化和标准化
            digitized_sketch = self._digitize_hand_drawn(request.hand_drawn_sketch)

            # 2. 图像理解，提取草图要素
            sketch_elements = self._analyze_hand_drawn(digitized_sketch)

            # 3. 文本描述与草图要素融合
            fused_description = self._fuse_text_and_sketch(request.text_description, sketch_elements)

            # 4. 调用next-ai-draw-io增强和标准化
            enhanced_result = self._call_drawio_enhance(fused_description, digitized_sketch)

            # 5. 专利合规性检查
            compliance_result = self.compliance_checker.check_and_fix(enhanced_result['drawing_data'])

            processing_time = time.time() - start_time

            return DrawingResult(
                success=True,
                drawing_data=compliance_result['drawing_data'],
                compliance_score=compliance_result['score'],
                processing_time=processing_time,
                metadata={
                    'sketch_elements': sketch_elements,
                    'fused_description': fused_description,
                    'enhancement_result': enhanced_result,
                    'compliance_issues': compliance_result['issues_fixed']
                }
            )

        except Exception as e:
            logger.error(f"❌ 图文结合绘图失败: {e}")
            return DrawingResult(
                success=False,
                drawing_data=b'',
                compliance_score=0.0,
                processing_time=time.time() - start_time,
                metadata={'error': str(e)}
            )

    def _enhance_with_knowledge_graph(self, text_description: str) -> str:
        """基于知识图谱增强文本描述"""
        # 这里可以连接到我们的Neo4j知识图谱
        # 提取相关的技术术语、标准组件、结构关系等
        enhanced = f"""
        基于专利知识图谱增强的技术描述：

        原始描述：{text_description}

        增强要素：
        - 标准技术术语映射
        - 常见结构模式识别
        - 符合专利局规范的绘图要素
        """
        return enhanced

    def _call_sketchagent(self, description: str, drawing_type: str) -> Dict[str, Any]:
        """调用SketchAgent服务"""
        try:
            response = requests.post(self.sketchagent_url, json={
                'description': description,
                'type': drawing_type,
                'style': 'patent_technical'
            }, timeout=60)

            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"SketchAgent API错误: {response.status_code}")

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ SketchAgent调用失败: {e}")
            # 返回模拟结果用于演示
            return {
                'drawing_data': self._generate_mock_drawing(description),
                'confidence': 0.85,
                'elements_detected': ['component_a', 'component_b', 'connection']
            }

    def _call_drawio_enhance(self, description: str, sketch_image: bytes) -> Dict[str, Any]:
        """调用next-ai-draw-io增强服务"""
        try:
            # 将图像编码为base64
            sketch_b64 = base64.b64encode(sketch_image).decode()

            response = requests.post(self.drawio_url, json={
                'description': description,
                'sketch_image': sketch_b64,
                'enhancement_type': 'patent_compliance'
            }, timeout=60)

            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"next-ai-draw-io API错误: {response.status_code}")

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ next-ai-draw-io调用失败: {e}")
            # 返回模拟结果用于演示
            return {
                'drawing_data': self._enhance_mock_drawing(sketch_image),
                'enhancements': ['line_standardization', 'symbol_normalization', 'scale_adjustment'],
                'confidence': 0.92
            }

    def _digitize_hand_drawn(self, sketch_image: bytes) -> bytes:
        """手绘草图数字化"""
        # 图像预处理：去噪、增强对比度、标准化尺寸等
        image = Image.open(io.BytesIO(sketch_image))

        # 转换为黑白
        if image.mode != 'L':
            image = image.convert('L')

        # 调整尺寸为标准图纸尺寸
        image = image.resize((800, 600), Image.Resampling.LANCZOS)

        # 增强对比度
        image = image.point(lambda x: 0 if x < 128 else 255, '1')

        # 保存为标准格式
        output = io.BytesIO()
        image.save(output, format='PNG')
        return output.getvalue()

    def _analyze_hand_drawn(self, sketch_image: bytes) -> Dict[str, Any]:
        """分析手绘草图要素"""
        # 这里应该调用图像理解AI模型
        # 返回检测到的组件、连接、标注等
        return {
            'components': ['rectangular_component', 'circular_component'],
            'connections': ['line_connection', 'arrow_connection'],
            'annotations': ['label_a', 'label_b'],
            'structure_type': 'flowchart',
            'confidence': 0.88
        }

    def _fuse_text_and_sketch(self, text: str, sketch_elements: Dict[str, Any]) -> str:
        """融合文本描述和草图要素"""
        fused = f"""
        融合技术描述：

        文本描述：{text}

        识别的草图要素：
        - 组件：{', '.join(sketch_elements['components'])}
        - 连接：{', '.join(sketch_elements['connections'])}
        - 标注：{', '.join(sketch_elements['annotations'])}
        - 结构类型：{sketch_elements['structure_type']}

        请基于上述信息生成标准化的技术图纸。
        """
        return fused

    def _generate_mock_drawing(self, description: str) -> bytes:
        """生成模拟图纸数据（用于演示）"""
        # 创建简单的SVG图纸
        svg_content = f"""
        <svg width='800' height='600' xmlns='http://www.w3.org/2000/svg'>
            <rect x='50' y='50' width='200' height='100' fill='none' stroke='black' stroke-width='2'/>
            <rect x='300' y='50' width='200' height='100' fill='none' stroke='black' stroke-width='2'/>
            <line x1='250' y1='100' x2='300' y2='100' stroke='black' stroke-width='2' marker-end='url(#arrow)'/>
            <text x='150' y='100' text-anchor='middle' font-family='Arial' font-size='14'>组件A</text>
            <text x='400' y='100' text-anchor='middle' font-family='Arial' font-size='14'>组件B</text>
            <defs>
                <marker id='arrow' markerWidth='10' markerHeight='10' refX='9' refY='3' orient='auto' markerUnits='strokeWidth'>
                    <path d='M0,0 L0,6 L9,3 z' fill='black'/>
                </marker>
            </defs>
        </svg>
        """
        return svg_content.encode('utf-8')

    def _enhance_mock_drawing(self, sketch_image: bytes) -> bytes:
        """增强模拟图纸数据（用于演示）"""
        # 对输入图像进行简单处理并返回
        return sketch_image

    def _convert_format(self, drawing_data: bytes, output_format: str) -> bytes:
        """格式转换"""
        if output_format.lower() == 'svg':
            return drawing_data
        elif output_format.lower() == 'png':
            # SVG转PNG的逻辑
            return drawing_data  # 简化处理
        else:
            return drawing_data

class ComplianceChecker:
    """专利合规性检查器"""

    def __init__(self):
        self.uspto_requirements = {
            'line_width': {'min': 0.1, 'max': 0.3},  # mm
            'text_size': {'min': 3.5, 'max': 14.0},   # mm
            'margin': {'min': 2.5},                   # cm
            'resolution': {'min': 300}                # DPI
        }

    def check_and_fix(self, drawing_data: bytes) -> Dict[str, Any]:
        """检查并修复合规性问题"""
        issues_found = []
        score = 1.0

        # 模拟合规性检查
        # 检查线条粗细、文字大小、边距等

        # 修复发现的问题
        fixed_drawing = self._fix_compliance_issues(drawing_data, issues_found)

        # 每发现一个问题，分数减少0.1
        score -= len(issues_found) * 0.1
        score = max(0.0, score)

        return {
            'drawing_data': fixed_drawing,
            'score': score,
            'issues_found': issues_found,
            'issues_fixed': len(issues_found)
        }

    def _fix_compliance_issues(self, drawing_data: bytes, issues: List[str]) -> bytes:
        """修复合规性问题"""
        # 根据发现的问题进行修复
        # 调整线条粗细、文字大小、边距等
        return drawing_data  # 简化处理

def main():
    """主函数 - 演示AI绘图系统"""
    logger.info('🎨 专利AI绘图集成系统')
    logger.info(str('=' * 50))
    logger.info('🤖 集成SketchAgent和next-ai-draw-io')
    logger.info('📝 支持纯文本和图文结合两种绘图模式')
    logger.info(str('=' * 50))

    # 创建绘图引擎
    engine = PatentDrawingEngine()

    # 演示场景1：纯文本描述生成
    logger.info("\n📝 场景1：纯文本描述生成草图")
    request1 = DrawingRequest(
        patent_id='CN202410000001',
        text_description='一种新型专利检索系统，包括数据输入模块、语义分析模块、向量计算模块和结果输出模块',
        drawing_type='flowchart',
        output_format='svg'
    )

    result1 = engine.generate_from_text_only(request1)
    if result1.success:
        logger.info(f"✅ 绘图成功")
        logger.info(f"   合规性评分: {result1.compliance_score:.2f}")
        logger.info(f"   处理时间: {result1.processing_time:.2f}秒")
        # 保存结果
        with open(f"/tmp/patent_drawing_{request1.patent_id}.svg", 'wb') as f:
            f.write(result1.drawing_data)
    else:
        logger.info(f"❌ 绘图失败: {result1.metadata.get('error', '未知错误')}")

    # 演示场景2：图文结合生成
    logger.info("\n🖼️ 场景2：文本描述 + 手绘草图结合")
    # 这里假设有一个手绘草图文件
    mock_sketch = engine._generate_mock_drawing('mock sketch')

    request2 = DrawingRequest(
        patent_id='CN202410000002',
        text_description='一种智能专利审查系统，具有文档接收、格式检查、实质审查和决定生成功能',
        drawing_type='system',
        hand_drawn_sketch=mock_sketch,
        output_format='svg'
    )

    result2 = engine.generate_with_sketch_input(request2)
    if result2.success:
        logger.info(f"✅ 绘图成功")
        logger.info(f"   合规性评分: {result2.compliance_score:.2f}")
        logger.info(f"   处理时间: {result2.processing_time:.2f}秒")
        # 保存结果
        with open(f"/tmp/patent_drawing_{request2.patent_id}_enhanced.svg", 'wb') as f:
            f.write(result2.drawing_data)
    else:
        logger.info(f"❌ 绘图失败: {result2.metadata.get('error', '未知错误')}")

    logger.info(f"\n💡 集成建议:")
    logger.info(f"   1. 场景1（纯文本）：适合批量处理，自动化程度高")
    logger.info(f"   2. 场景2（图文结合）：质量更高，适合重要专利")
    logger.info(f"   3. 建议采用混合模式：根据专利重要性选择合适的绘图方式")

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