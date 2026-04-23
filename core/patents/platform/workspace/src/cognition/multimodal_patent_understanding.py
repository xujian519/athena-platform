#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多模态专利理解系统
Multimodal Patent Understanding System

功能:
1. 图表理解 - 专利附图、流程图、结构图的智能分析
2. 公式识别 - 数学公式、化学式的解析和理解
3. 表格提取 - 专利表格数据的结构化提取
4. 技术图纸分析 - 工程图纸、示意图的专业解读
5. 跨模态关联 - 文本与图像内容的关联分析
"""

import asyncio
import base64
import hashlib
import json
import logging
import os
import re
import sys
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

# 图像处理相关
import cv2
import fitz  # PyMuPDF
import latex2mathml.converter
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np

# OCR和文档处理
import pytesseract

# 科学公式处理
import sympy

# AI模型相关
import torch
import torch.nn.functional as F
from pdf2image import convert_from_path
from PIL import Image, ImageDraw, ImageFont
from sympy.parsing.latex import parse_latex
from transformers import (
    AutoImageProcessor,
    AutoModel,
    AutoTokenizer,
    DonutProcessor,
    LayoutLMv3ForTokenClassification,
    LayoutLMv3Processor,
    VisionEncoderDecoderModel,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置
MODEL_CACHE_DIR = '/Users/xujian/Athena工作平台/models/multimodal_cache'
os.makedirs(MODEL_CACHE_DIR, exist_ok=True)


class ContentType(Enum):
    """内容类型枚举"""
    TEXT = 'text'                    # 纯文本
    IMAGE = 'image'                  # 图像
    TABLE = 'table'                  # 表格
    FORMULA = 'formula'              # 数学公式
    CHEMICAL = 'chemical'            # 化学式
    DIAGRAM = 'diagram'              # 示意图
    FLOWCHART = 'flowchart'          # 流程图
    DRAWING = 'drawing'              # 工程图纸


class ImageType(Enum):
    """图像类型枚举"""
    PATENT_DRAWING = 'patent_drawing'        # 专利附图
    FLOW_DIAGRAM = 'flow_diagram'           # 流程图
    STRUCTURE_DIAGRAM = 'structure_diagram' # 结构图
    DATA_CHART = 'data_chart'               # 数据图表
    SCHEMATIC = 'schematic'                 # 原理图
    PHOTOGRAPH = 'photograph'               # 照片
    SCREENSHOT = 'screenshot'               # 截图


@dataclass
class MultimodalContent:
    """多模态内容结构"""
    content_id: str
    content_type: ContentType
    image_type: ImageType | None = None
    raw_data: Union[str, bytes, np.ndarray] = None
    text_content: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    bounding_boxes: Optional[List[Dict[str, Any]]] = None
    confidence: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class MultimodalAnalysisResult:
    """多模态分析结果"""
    content_id: str
    analysis_type: str
    extracted_content: List[MultimodalContent]
    relationships: List[Dict[str, Any]]
    summary: str
    confidence: float
    processing_time: float
    metadata: Optional[Dict[str, Any]] = None


class ImageProcessor:
    """图像处理器"""

    def __init__(self):
        self.ocr_config = {
            'rnn': True,
            'oem': 3,
            'psm': 6,
            'lang': 'chi_sim+eng'
        }
        self.layout_processor = None
        self._load_models()

    def _load_models(self):
        """加载模型"""
        try:
            # 加载布局分析模型
            self.layout_processor = LayoutLMv3Processor.from_pretrained(
                'microsoft/layoutlmv3-base',
                cache_dir=MODEL_CACHE_DIR
            )
            logger.info('多模态模型加载成功')
        except Exception as e:
            logger.warning(f"模型加载失败: {str(e)}")

    def extract_text_from_image(self, image: Union[str, np.ndarray]) -> Dict[str, Any]:
        """从图像中提取文本"""
        try:
            if isinstance(image, str):
                # 文件路径
                img = cv2.imread(image)
            else:
                img = image

            # 使用pytesseract进行OCR
            text = pytesseract.image_to_string(img, config='--oem 3 --psm 6 -l chi_sim+eng')

            # 获取详细的OCR结果（包括置信度和位置）
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, config='--oem 3 --psm 6 -l chi_sim+eng')

            # 构建文本块
            text_blocks = []
            current_block = ''
            current_conf = 0
            block_count = 0

            for i in range(len(data['text'])):
                if int(data['conf'][i]) > 0:
                    if data['text'][i].strip():
                        # 非空文本
                        if not current_block:
                            block_count += 1
                            current_conf = int(data['conf'][i])
                        current_block += data['text'][i] + ' '
                    else:
                        # 空文本，表示一个块的结束
                        if current_block.strip():
                            text_blocks.append({
                                'block_id': block_count,
                                'text': current_block.strip(),
                                'confidence': current_conf,
                                'position': {
                                    'x': data['left'][i-1],
                                    'y': data['top'][i-1],
                                    'width': data['width'][i-1],
                                    'height': data['height'][i-1]
                                }
                            })
                        current_block = ''

            # 处理最后一个块
            if current_block.strip():
                text_blocks.append({
                    'block_id': block_count + 1,
                    'text': current_block.strip(),
                    'confidence': current_conf,
                    'position': {
                        'x': data['left'][-1],
                        'y': data['top'][-1],
                        'width': data['width'][-1],
                        'height': data['height'][-1]
                    }
                })

            return {
                'full_text': text,
                'text_blocks': text_blocks,
                'total_blocks': len(text_blocks)
            }

        except Exception as e:
            logger.error(f"图像文本提取失败: {str(e)}")
            return {
                'full_text': '',
                'text_blocks': [],
                'total_blocks': 0,
                'error': str(e)
            }

    def detect_layout_elements(self, image: Union[str, np.ndarray]) -> List[Dict[str, Any]]:
        """检测图像中的布局元素"""
        try:
            if isinstance(image, str):
                img = cv2.imread(image)
            else:
                img = image

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # 检测表格线条
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))

            horizontal_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, horizontal_kernel)
            vertical_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, vertical_kernel)

            # 组合线条
            table_mask = cv2.addWeighted(horizontal_lines, 0.5, vertical_lines, 0.5, 0.0)

            # 查找轮廓
            contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            layout_elements = []

            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 1000:  # 过滤小的噪点
                    x, y, w, h = cv2.boundingRect(contour)

                    # 判断元素类型
                    aspect_ratio = w / h

                    if aspect_ratio > 3:
                        element_type = 'horizontal_line'
                    elif aspect_ratio < 0.3:
                        element_type = 'vertical_line'
                    elif 0.8 < aspect_ratio < 1.2:
                        element_type = 'cell'
                    else:
                        element_type = 'table_region'

                    layout_elements.append({
                        'type': element_type,
                        'bounding_box': {
                            'x': x,
                            'y': y,
                            'width': w,
                            'height': h
                        },
                        'area': area,
                        'aspect_ratio': aspect_ratio
                    })

            return layout_elements

        except Exception as e:
            logger.error(f"布局检测失败: {str(e)}")
            return []

    def analyze_diagram_structure(self, image: Union[str, np.ndarray]) -> Dict[str, Any]:
        """分析图表结构"""
        try:
            if isinstance(image, str):
                img = cv2.imread(image)
            else:
                img = image

            # 转换为灰度图
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # 边缘检测
            edges = cv2.Canny(gray, 50, 150)

            # 查找轮廓
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # 分析形状
            shapes = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 500:  # 过滤小的形状
                    # 计算轮廓近似
                    epsilon = 0.02 * cv2.arcLength(contour, True)
                    approx = cv2.approxPolyDP(contour, epsilon, True)

                    # 获取边界框
                    x, y, w, h = cv2.boundingRect(contour)

                    # 判断形状类型
                    if len(approx) == 3:
                        shape_type = 'triangle'
                    elif len(approx) == 4:
                        aspect_ratio = w / float(h)
                        if 0.95 <= aspect_ratio <= 1.05:
                            shape_type = 'square'
                        else:
                            shape_type = 'rectangle'
                    elif len(approx) > 8:
                        shape_type = 'circle'
                    else:
                        shape_type = 'polygon'

                    shapes.append({
                        'type': shape_type,
                        'bounding_box': {
                            'x': x,
                            'y': y,
                            'width': w,
                            'height': h
                        },
                        'area': area,
                        'vertices': len(approx)
                    })

            # 分析连接线
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, minLineLength=50, maxLineGap=10)

            connections = []
            if lines is not None:
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    connections.append({
                        'start': {'x': x1, 'y': y1},
                        'end': {'x': x2, 'y': y2},
                        'length': np.sqrt((x2-x1)**2 + (y2-y1)**2)
                    })

            return {
                'shapes': shapes,
                'connections': connections,
                'total_shapes': len(shapes),
                'total_connections': len(connections)
            }

        except Exception as e:
            logger.error(f"图表结构分析失败: {str(e)}")
            return {
                'shapes': [],
                'connections': [],
                'error': str(e)
            }


class FormulaExtractor:
    """公式提取器"""

    def __init__(self):
        self.formula_patterns = self._init_formula_patterns()

    def _init_formula_patterns(self) -> Dict[str, str]:
        """初始化公式模式"""
        return {
            'mathematical': r'[\d\+\-\*\/\=\(\)\[\]\{\}\^\_\∑\∏\∫\√\π\α\β\γ\δ\θ\λ\μ\σ\φ\ω]',
            'chemical': r'[A-Z][a-z]?\d*(?:\([^)]*\)\d*)?[\+\-\=\→\←]',
            'physical': r'[F=ma]|[E=mc²]|[PV=nRT]|[v=d/t]',
            'fraction': r'\d+\/\d+',
            'subscript': r'[A-Za-z]\d+',
            'superscript': r'[A-Za-z]\^[A-Za-z\d]+'
        }

    def extract_formulas_from_text(self, text: str) -> List[Dict[str, Any]]:
        """从文本中提取公式"""
        formulas = []

        # 提取数学公式
        math_matches = re.finditer(self.formula_patterns['mathematical'], text)
        for match in math_matches:
            formula_text = match.group()
            if self._is_likely_formula(formula_text):
                formulas.append({
                    'type': 'mathematical',
                    'text': formula_text,
                    'position': match.span(),
                    'confidence': 0.8
                })

        # 提取化学式
        chemical_matches = re.finditer(self.formula_patterns['chemical'], text)
        for match in chemical_matches:
            formula_text = match.group()
            if self._is_likely_chemical(formula_text):
                formulas.append({
                    'type': 'chemical',
                    'text': formula_text,
                    'position': match.span(),
                    'confidence': 0.7
                })

        # 提取分数
        fraction_matches = re.finditer(self.formula_patterns['fraction'], text)
        for match in fraction_matches:
            formula_text = match.group()
            numerator, denominator = formula_text.split('/')
            formulas.append({
                'type': 'fraction',
                'text': formula_text,
                'structured': {
                    'numerator': numerator,
                    'denominator': denominator
                },
                'position': match.span(),
                'confidence': 0.9
            })

        return formulas

    def _is_likely_formula(self, text: str) -> bool:
        """判断是否为可能的公式"""
        # 简单的启发式规则
        formula_indicators = ['=', '+', '-', '*', '/', '^', '_', '∑', '∏', '∫']
        return any(indicator in text for indicator in formula_indicators)

    def _is_likely_chemical(self, text: str) -> bool:
        """判断是否为化学式"""
        # 检查是否包含化学元素符号
        element_pattern = r'[A-Z][a-z]?'
        elements = re.findall(element_pattern, text)
        return len(elements) >= 2  # 至少包含两个元素

    def parse_latex_formula(self, latex_formula: str) -> Dict[str, Any]:
        """解析LaTeX公式"""
        try:
            # 使用sympy解析LaTeX
            expr = parse_latex(latex_formula)

            return {
                'type': 'latex_mathematical',
                'original': latex_formula,
                'sympy_expr': str(expr),
                'variables': list(expr.free_symbols),
                'is_equation': '=' in latex_formula,
                'success': True
            }
        except Exception as e:
            return {
                'type': 'latex_mathematical',
                'original': latex_formula,
                'error': str(e),
                'success': False
            }


class TableExtractor:
    """表格提取器"""

    def __init__(self):
        pass

    def extract_table_from_image(self, image: Union[str, np.ndarray]) -> Dict[str, Any]:
        """从图像中提取表格"""
        try:
            if isinstance(image, str):
                img = cv2.imread(image)
            else:
                img = image

            # 转换为灰度图
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # 二值化
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

            # 检测水平线和垂直线
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))

            horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel)
            vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel)

            # 组合线条
            table_structure = cv2.addWeighted(horizontal_lines, 0.5, vertical_lines, 0.5, 0.0)

            # 查找单元格
            contours, _ = cv2.findContours(table_structure, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            cells = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 500:  # 过滤小的噪点
                    x, y, w, h = cv2.boundingRect(contour)
                    cells.append({
                        'bounding_box': {'x': x, 'y': y, 'width': w, 'height': h},
                        'area': area,
                        'cell_image': img[y:y+h, x:x+w]
                    })

            # 对单元格进行排序（从左到右，从上到下）
            cells.sort(key=lambda c: (c['bounding_box']['y'], c['bounding_box']['x']))

            # 估算表格结构
            if cells:
                # 确定行列数
                x_positions = sorted(set(c['bounding_box']['x'] for c in cells))
                y_positions = sorted(set(c['bounding_box']['y'] for c in cells))

                rows = len(y_positions)
                cols = len(x_positions)

                # 重构表格
                table_data = []
                for row in range(rows):
                    row_data = []
                    for col in range(cols):
                        # 查找对应的单元格
                        target_x = x_positions[col]
                        target_y = y_positions[row]

                        cell = next((c for c in cells
                                   if abs(c['bounding_box']['x'] - target_x) < 10 and
                                      abs(c['bounding_box']['y'] - target_y) < 10), None)

                        if cell:
                            # 对单元格进行OCR
                            cell_text = pytesseract.image_to_string(
                                cell['cell_image'],
                                config='--oem 3 --psm 7 -l chi_sim+eng'
                            ).strip()
                            row_data.append(cell_text)
                        else:
                            row_data.append('')
                    table_data.append(row_data)

                return {
                    'success': True,
                    'rows': rows,
                    'cols': cols,
                    'table_data': table_data,
                    'cells': cells
                }
            else:
                return {
                    'success': False,
                    'error': '未检测到表格结构',
                    'cells': []
                }

        except Exception as e:
            logger.error(f"表格提取失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'cells': []
            }

    def structure_table_data(self, raw_table: List[List[str]]) -> Dict[str, Any]:
        """结构化表格数据"""
        if not raw_table or len(raw_table) < 2:
            return {'structured': False, 'error': '表格数据不足'}

        try:
            # 假设第一行为标题
            headers = raw_table[0]
            data_rows = raw_table[1:]

            # 转换为字典列表
            structured_data = []
            for row in data_rows:
                if len(row) == len(headers):
                    row_dict = {}
                    for i, header in enumerate(headers):
                        row_dict[header.strip()] = row[i].strip()
                    structured_data.append(row_dict)

            # 尝试数值转换
            numeric_columns = []
            for col in range(len(headers)):
                numeric_values = []
                for row in data_rows:
                    if col < len(row):
                        try:
                            val = float(row[col])
                            numeric_values.append(val)
                        except ValueError:
                            break

                # 如果超过80%的值是数值，则认为是数值列
                if len(numeric_values) > len(data_rows) * 0.8:
                    numeric_columns.append(col)

            return {
                'structured': True,
                'headers': headers,
                'data_rows': data_rows,
                'structured_data': structured_data,
                'numeric_columns': numeric_columns,
                'total_rows': len(structured_data)
            }

        except Exception as e:
            return {
                'structured': False,
                'error': str(e)
            }


class MultimodalPatentUnderstanding:
    """多模态专利理解主系统"""

    def __init__(self):
        self.image_processor = ImageProcessor()
        self.formula_extractor = FormulaExtractor()
        self.table_extractor = TableExtractor()
        self.processing_stats = {
            'total_processed': 0,
            'text_extractions': 0,
            'formula_extractions': 0,
            'table_extractions': 0,
            'diagram_analyses': 0
        }

    async def process_patent_document(self, patent_file: str) -> MultimodalAnalysisResult:
        """处理专利文档"""
        start_time = time.time()

        try:
            content_id = str(uuid.uuid4())
            extracted_content = []
            relationships = []

            # 判断文件类型
            file_extension = patent_file.lower().split('.')[-1]

            if file_extension == 'pdf':
                contents = await self._process_pdf(patent_file)
            elif file_extension in ['jpg', 'jpeg', 'png', 'bmp', 'tiff']:
                contents = await self._process_image(patent_file)
            else:
                raise ValueError(f"不支持的文件格式: {file_extension}")

            # 分析内容
            for content in contents:
                if content.content_type == ContentType.TEXT:
                    # 提取公式
                    formulas = self.formula_extractor.extract_formulas_from_text(content.text_content or '')
                    for formula in formulas:
                        formula_content = MultimodalContent(
                            content_id=str(uuid.uuid4()),
                            content_type=ContentType.FORMULA,
                            text_content=formula['text'],
                            structured_data=formula,
                            confidence=formula['confidence']
                        )
                        extracted_content.append(formula_content)

                        # 添加关系
                        relationships.append({
                            'source': content.content_id,
                            'target': formula_content.content_id,
                            'type': 'contains',
                            'confidence': 0.9
                        })

                elif content.content_type == ContentType.IMAGE:
                    if content.image_type == ImageType.DATA_CHART:
                        # 分析表格
                        table_result = self.table_extractor.extract_table_from_image(content.raw_data)
                        if table_result['success']:
                            table_content = MultimodalContent(
                                content_id=str(uuid.uuid4()),
                                content_type=ContentType.TABLE,
                                structured_data=table_result,
                                confidence=0.8
                            )
                            extracted_content.append(table_content)

                            relationships.append({
                                'source': content.content_id,
                                'target': table_content.content_id,
                                'type': 'contains',
                                'confidence': 0.85
                            })

                    elif content.image_type in [ImageType.FLOW_DIAGRAM, ImageType.STRUCTURE_DIAGRAM]:
                        # 分析图表结构
                        diagram_result = self.image_processor.analyze_diagram_structure(content.raw_data)
                        content.structured_data = diagram_result
                        self.processing_stats['diagram_analyses'] += 1

            # 生成摘要
            summary = self._generate_summary(extracted_content)

            processing_time = time.time() - start_time
            self.processing_stats['total_processed'] += 1

            return MultimodalAnalysisResult(
                content_id=content_id,
                analysis_type='patent_document',
                extracted_content=extracted_content,
                relationships=relationships,
                summary=summary,
                confidence=0.85,
                processing_time=processing_time,
                metadata={
                    'file_path': patent_file,
                    'file_type': file_extension,
                    'total_contents': len(contents),
                    'extracted_elements': len(extracted_content)
                }
            )

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"专利文档处理失败: {str(e)}")

            return MultimodalAnalysisResult(
                content_id=str(uuid.uuid4()),
                analysis_type='patent_document',
                extracted_content=[],
                relationships=[],
                summary=f"处理失败: {str(e)}",
                confidence=0.0,
                processing_time=processing_time,
                metadata={'error': str(e)}
            )

    async def _process_pdf(self, pdf_path: str) -> List[MultimodalContent]:
        """处理PDF文件"""
        contents = []

        try:
            # 使用PyMuPDF处理PDF
            pdf_document = fitz.open(pdf_path)

            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]

                # 提取文本
                text = page.get_text()
                if text.strip():
                    text_content = MultimodalContent(
                        content_id=str(uuid.uuid4()),
                        content_type=ContentType.TEXT,
                        text_content=text,
                        confidence=0.95
                    )
                    contents.append(text_content)
                    self.processing_stats['text_extractions'] += 1

                # 提取图像
                image_list = page.get_images()
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = pdf_document.extract_image(xref)
                    image_bytes = base_image['image']
                    image_ext = base_image['ext']

                    # 保存临时图像
                    temp_image_path = f"temp_image_{page_num}_{img_index}.{image_ext}"
                    with open(temp_image_path, 'wb') as f:
                        f.write(image_bytes)

                    # 处理图像
                    image_content = await self._process_image(temp_image_path)
                    contents.extend(image_content)

                    # 清理临时文件
                    os.remove(temp_image_path)

            pdf_document.close()

        except Exception as e:
            logger.error(f"PDF处理失败: {str(e)}")

        return contents

    async def _process_image(self, image_path: str) -> List[MultimodalContent]:
        """处理图像文件"""
        contents = []

        try:
            # 读取图像
            img = cv2.imread(image_path)

            # 提取文本
            ocr_result = self.image_processor.extract_text_from_image(img)
            if ocr_result['full_text'].strip():
                text_content = MultimodalContent(
                    content_id=str(uuid.uuid4()),
                    content_type=ContentType.TEXT,
                    text_content=ocr_result['full_text'],
                    structured_data=ocr_result,
                    confidence=0.9
                )
                contents.append(text_content)
                self.processing_stats['text_extractions'] += 1

            # 检测布局元素
            layout_elements = self.image_processor.detect_layout_elements(img)
            if layout_elements:
                image_type = self._classify_image_type(layout_elements, img.shape)

                image_content = MultimodalContent(
                    content_id=str(uuid.uuid4()),
                    content_type=ContentType.IMAGE,
                    image_type=image_type,
                    raw_data=img,
                    structured_data={'layout_elements': layout_elements},
                    bounding_boxes=ocr_result.get('text_blocks', []),
                    confidence=0.85
                )
                contents.append(image_content)

        except Exception as e:
            logger.error(f"图像处理失败: {str(e)}")

        return contents

    def _classify_image_type(self, layout_elements: List[Dict[str, Any]], image_shape: Tuple[int, ...]) -> ImageType:
        """分类图像类型"""
        table_regions = [e for e in layout_elements if e['type'] == 'table_region']
        lines = [e for e in layout_elements if e['type'] in ['horizontal_line', 'vertical_line']]

        if len(table_regions) > 0:
            return ImageType.DATA_CHART
        elif len(lines) > 5:
            return ImageType.FLOW_DIAGRAM
        else:
            return ImageType.PATENT_DRAWING

    def _generate_summary(self, extracted_content: List[MultimodalContent]) -> str:
        """生成分析摘要"""
        content_types = {}
        for content in extracted_content:
            content_type = content.content_type.value
            content_types[content_type] = content_types.get(content_type, 0) + 1

        summary_parts = []
        if content_types.get('text', 0) > 0:
            summary_parts.append(f"提取了 {content_types['text']} 个文本片段")
        if content_types.get('formula', 0) > 0:
            summary_parts.append(f"识别了 {content_types['formula']} 个公式")
        if content_types.get('table', 0) > 0:
            summary_parts.append(f"提取了 {content_types['table']} 个表格")
        if content_types.get('image', 0) > 0:
            summary_parts.append(f"分析了 {content_types['image']} 个图像")

        return '; '.join(summary_parts) if summary_parts else '未提取到有效内容'

    def get_processing_stats(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        return self.processing_stats.copy()

    def export_results(self, result: MultimodalAnalysisResult, output_format: str = 'json') -> str:
        """导出分析结果"""
        if output_format == 'json':
            # 准备导出数据
            export_data = {
                'content_id': result.content_id,
                'analysis_type': result.analysis_type,
                'summary': result.summary,
                'confidence': result.confidence,
                'processing_time': result.processing_time,
                'metadata': result.metadata,
                'extracted_content': [
                    {
                        'content_id': content.content_id,
                        'content_type': content.content_type.value,
                        'image_type': content.image_type.value if content.image_type else None,
                        'text_content': content.text_content,
                        'structured_data': content.structured_data,
                        'confidence': content.confidence
                    }
                    for content in result.extracted_content
                ],
                'relationships': result.relationships
            }

            return json.dumps(export_data, ensure_ascii=False, indent=2)

        elif output_format == 'markdown':
            # 生成Markdown报告
            lines = [
                f"# 多模态专利分析报告",
                f"**分析ID**: {result.content_id}",
                f"**分析类型**: {result.analysis_type}",
                f"**处理时间**: {result.processing_time:.2f}秒",
                f"**置信度**: {result.confidence:.2f}",
                '',
                '## 分析摘要',
                result.summary,
                '',
                '## 提取的内容'
            ]

            for i, content in enumerate(result.extracted_content, 1):
                lines.extend([
                    f"",
                    f"### {i}. {content.content_type.value}",
                    f"**置信度**: {content.confidence:.2f}",
                ])

                if content.text_content:
                    lines.extend([
                        '**文本内容**:',
                        '```',
                        content.text_content[:500] + '...' if len(content.text_content) > 500 else content.text_content,
                        '```'
                    ])

                if content.structured_data:
                    lines.extend([
                        '**结构化数据**:',
                        '```json',
                        json.dumps(content.structured_data, ensure_ascii=False, indent=2)[:1000] + '...' if len(json.dumps(content.structured_data, ensure_ascii=False)) > 1000 else json.dumps(content.structured_data, ensure_ascii=False, indent=2),
                        '```'
                    ])

            return "\n".join(lines)

        else:
            raise ValueError(f"不支持的导出格式: {output_format}")


# 创建全局实例
multimodal_understanding = MultimodalPatentUnderstanding()


# 使用示例
async def test_multimodal_understanding():
    """测试多模态专利理解"""
    logger.info('🖼️ 测试多模态专利理解系统')

    # 测试公式提取
    test_text = """
    本发明涉及一种新型计算方法，其中关键技术参数满足以下关系：
    E = mc²
    化学反应式：2H₂ + O₂ → 2H₂O
    效率计算公式：η = (输出功率/输入功率) × 100%
    """

    logger.info("\n🧮 测试公式提取...")
    formulas = multimodal_understanding.formula_extractor.extract_formulas_from_text(test_text)
    for formula in formulas:
        logger.info(f"发现公式: {formula['text']} (类型: {formula['type']}, 置信度: {formula['confidence']})")

    # 测试LaTeX解析
    latex_formula = r"\int_{0}^{\infty} e^{-x^2} dx = \frac{\sqrt{\pi}}{2}"
    logger.info(f"\n📐 测试LaTeX解析: {latex_formula}")
    parsed = multimodal_understanding.formula_extractor.parse_latex_formula(latex_formula)
    print('解析结果:', parsed)

    # 显示统计信息
    logger.info("\n📊 处理统计:")
    stats = multimodal_understanding.get_processing_stats()
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    import time
    asyncio.run(test_multimodal_understanding())