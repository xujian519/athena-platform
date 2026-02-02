#!/usr/bin/env python3
"""
增强的多模态专利感知层
Enhanced Multimodal Patent Perception Layer

专门为专利业务设计的多模态感知系统，
集成了文本、图像、表格、公式等多种模态的协同分析。

作者: Athena AI系统
创建时间: 2025-12-05
版本: 1.0.0
"""

import asyncio
import io
import json
import logging
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import fitz  # PyMuPDF
import pytesseract
from PIL import Image

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModalityType(Enum):
    """模态类型"""
    TEXT = 'text'
    IMAGE = 'image'
    TABLE = 'table'
    FORMULA = 'formula'
    DRAWING = 'drawing'
    DIAGRAM = 'diagram'
    MARKUP = 'markup'

@dataclass
class ModalityContent:
    """模态内容"""
    modality_type: ModalityType
    content: Any
    location: Dict[str, Any]  # 页码、坐标等信息
    confidence: float
    metadata: Dict[str, Any]
    cross_references: List[str]  # 跨模态引用

@dataclass
class PatentModalityAnalysis:
    """专利多模态分析结果"""
    patent_id: str
    modalities: List[ModalityContent]
    cross_modal_relations: Dict[str, List[str]]
    unified_features: List[Dict[str, Any]]
    claim_drawing_mappings: Dict[int, List[str]]  # 权利要求到图纸的映射
    technical_diagrams: List[Dict[str, Any]]
    confidence_scores: Dict[ModalityType, float]

class PatentImageAnalyzer:
    """专利图像分析器"""

    def __init__(self):
        self.ocr_config = r'--oem 3 --psm 6 -l chi_sim+eng'
        self.diagram_patterns = [
            r'图\s*\d+',  # 图1, 图2
            r'Fig\.\s*\d+',  # Fig.1, Fig.2
            r'附图\s*\d+',  # 附图1, 附图2
        ]

    def analyze_patent_image(self, image_data: bytes, page_num: int = 1) -> Dict[str, Any]:
        """
        分析专利图像内容

        Args:
            image_data: 图像二进制数据
            page_num: 页码

        Returns:
            图像分析结果
        """
        try:
            # OCR识别
            image = Image.open(io.BytesIO(image_data))
            ocr_text = pytesseract.image_to_string(image, config=self.ocr_config)

            # 检测图纸类型
            diagram_type = self._detect_diagram_type(ocr_text)

            # 提取技术元素
            technical_elements = self._extract_technical_elements(ocr_text)

            # 识别标记和引用
            markup_references = self._extract_markup_references(ocr_text)

            return {
                'page_number': page_num,
                'image_size': image.size,
                'ocr_text': ocr_text.strip(),
                'diagram_type': diagram_type,
                'technical_elements': technical_elements,
                'markup_references': markup_references,
                'confidence': self._calculate_ocr_confidence(ocr_text),
                'modality': 'technical_drawing'
            }

        except Exception as e:
            logger.error(f"图像分析失败: {str(e)}")
            return {'error': str(e), 'confidence': 0.0}

    def _detect_diagram_type(self, text: str) -> str:
        """检测图纸类型"""
        text_lower = text.lower()

        if any(keyword in text_lower for keyword in ['结构图', '爆炸图', '装配图']):
            return 'structural_diagram'
        elif any(keyword in text_lower for keyword in ['流程图', '工艺图', '步骤']):
            return 'process_diagram'
        elif any(keyword in text_lower for keyword in ['电路图', '原理图', '接线图']):
            return 'circuit_diagram'
        elif any(keyword in text_lower for keyword in '曲线图图表数据图'):
            return 'chart_diagram'
        else:
            return 'technical_drawing'

    def _extract_technical_elements(self, text: str) -> List[Dict[str, Any]]:
        """提取技术元素"""
        elements = []

        # 提取数字标记
        number_patterns = re.findall(r'(\d+)[：:]\s*([^\n]+)', text)
        for num, desc in number_patterns:
            elements.append({
                'type': 'numbered_reference',
                'number': num,
                'description': desc.strip(),
                'confidence': 0.8
            })

        # 提取技术术语
        technical_terms = re.findall(r'([A-Z]{2,}|[a-z]+[A-Z][a-z]+)', text)
        for term in set(technical_terms):
            if len(term) > 2:
                elements.append({
                    'type': 'technical_term',
                    'term': term,
                    'confidence': 0.6
                })

        return elements

    def _extract_markup_references(self, text: str) -> List[str]:
        """提取标记引用"""
        references = []

        # 查找图纸引用
        for pattern in self.diagram_patterns:
            matches = re.findall(pattern, text)
            references.extend(matches)

        return list(set(references))

    def _calculate_ocr_confidence(self, text: str) -> float:
        """计算OCR置信度"""
        if not text.strip():
            return 0.0

        # 基于文本长度和字符质量估算
        text_length = len(text.strip())

        # 检查中文字符比例
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        chinese_ratio = chinese_chars / text_length if text_length > 0 else 0

        # 基础置信度
        base_confidence = min(0.9, text_length / 1000)

        # 中文识别加成
        chinese_bonus = 0.1 if chinese_ratio > 0.3 else 0

        return min(1.0, base_confidence + chinese_bonus)

class PatentMultimodalProcessor:
    """专利多模态处理器"""

    def __init__(self):
        self.image_analyzer = PatentImageAnalyzer()
        self.cross_modal_patterns = {
            'claim_drawing': r"权利要求.*?图\s*(\d+)",
            'description_drawing': r"说明书.*?附图\s*(\d+)",
            'drawing_description': r"图\s*(\d+).*?为.*?([^。；；]+)",
        }

    def analyze_patent_document(self, file_path: str) -> PatentModalityAnalysis:
        """
        分析专利文档的多模态内容

        Args:
            file_path: PDF文件路径

        Returns:
            多模态分析结果
        """
        logger.info(f"开始多模态分析: {file_path}")

        patent_id = Path(file_path).stem
        modalities = []
        cross_modal_relations = {}

        try:
            # 打开PDF文档
            doc = fitz.open(file_path)

            # 逐页分析
            for page_num in range(len(doc)):
                page = doc[page_num]

                # 获取文本内容
                text_content = page.get_text()
                if text_content.strip():
                    modalities.append(ModalityContent(
                        modality_type=ModalityType.TEXT,
                        content=text_content,
                        location={'page': page_num + 1},
                        confidence=1.0,
                        metadata={'length': len(text_content)},
                        cross_references=[]
                    ))

                # 获取图像内容
                images = page.get_images()
                for img_index, img in enumerate(images):
                    try:
                        # 提取图像
                        pix = page.get_pixmap()
                        img_data = pix.tobytes('png')

                        # 分析图像
                        image_analysis = self.image_analyzer.analyze_patent_image(
                            img_data, page_num + 1
                        )

                        if 'error' not in image_analysis:
                            modalities.append(ModalityContent(
                                modality_type=ModalityType.IMAGE,
                                content=image_analysis,
                                location={
                                    'page': page_num + 1,
                                    'image_index': img_index
                                },
                                confidence=image_analysis.get('confidence', 0.0),
                                metadata=image_analysis,
                                cross_references=image_analysis.get('markup_references', [])
                            ))

                    except Exception as e:
                        logger.warning(f"第{page_num+1}页图像{img_index}处理失败: {str(e)}")

            doc.close()

            # 建立跨模态关系
            cross_modal_relations = self._build_cross_modal_relations(modalities)

            # 提取统一特征
            unified_features = self._extract_unified_features(modalities)

            # 建立权利要求到图纸的映射
            claim_drawing_mappings = self._build_claim_drawing_mappings(modalities)

            # 收集技术图纸
            technical_diagrams = self._collect_technical_diagrams(modalities)

            # 计算各模态置信度
            confidence_scores = self._calculate_modality_confidence(modalities)

            return PatentModalityAnalysis(
                patent_id=patent_id,
                modalities=modalities,
                cross_modal_relations=cross_modal_relations,
                unified_features=unified_features,
                claim_drawing_mappings=claim_drawing_mappings,
                technical_diagrams=technical_diagrams,
                confidence_scores=confidence_scores
            )

        except Exception as e:
            logger.error(f"多模态分析失败: {str(e)}")
            return PatentModalityAnalysis(
                patent_id=patent_id,
                modalities=[],
                cross_modal_relations={},
                unified_features=[],
                claim_drawing_mappings={},
                technical_diagrams=[],
                confidence_scores={}
            )

    def _build_cross_modal_relations(self, modalities: List[ModalityContent]) -> Dict[str, List[str]]:
        """建立跨模态关系"""
        relations = {}

        # 收集所有引用
        all_references = {}
        for i, modality in enumerate(modalities):
            if modality.cross_references:
                all_references[f"modality_{i}"] = modality.cross_references

        # 查找交叉引用
        for ref_key, references in all_references.items():
            matching_modalities = []
            for j, modality in enumerate(modalities):
                if f"modality_{j}" != ref_key:  # 不自引用
                    # 检查是否匹配
                    if any(ref in str(modality.content) for ref in references):
                        matching_modalities.append(f"modality_{j}")

            if matching_modalities:
                relations[ref_key] = matching_modalities

        return relations

    def _extract_unified_features(self, modalities: List[ModalityContent]) -> List[Dict[str, Any]]:
        """提取统一特征"""
        unified_features = []

        # 从文本模态提取特征
        text_modalities = [m for m in modalities if m.modality_type == ModalityType.TEXT]
        for modality in text_modalities:
            # 提取技术特征
            features = self._extract_text_features(modality.content)
            unified_features.extend(features)

        # 从图像模态提取特征
        image_modalities = [m for m in modalities if m.modality_type == ModalityType.IMAGE]
        for modality in image_modalities:
            # 提取视觉特征
            features = self._extract_image_features(modality.content)
            unified_features.extend(features)

        return unified_features

    def _extract_text_features(self, text: str) -> List[Dict[str, Any]]:
        """从文本提取特征"""
        features = []

        # 提取权利要求特征
        claim_matches = re.findall(r'(\d+)\.?\s*([^.\n]+)', text)
        for claim_num, claim_text in claim_matches:
            features.append({
                'type': 'claim',
                'claim_number': int(claim_num),
                'text': claim_text.strip(),
                'modality': 'text'
            })

        # 提取技术术语
        tech_terms = re.findall(r'([A-Z]{2,}|[a-z]+[A-Z][a-z]+|[一-龯]{2,})', text)
        for term in set(tech_terms):
            if len(term) > 2:
                features.append({
                    'type': 'technical_term',
                    'term': term,
                    'modality': 'text'
                })

        return features

    def _extract_image_features(self, image_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从图像分析结果提取特征"""
        features = []

        if 'technical_elements' in image_analysis:
            for element in image_analysis['technical_elements']:
                features.append({
                    'type': element['type'],
                    'content': element,
                    'modality': 'image',
                    'page': image_analysis.get('page_number')
                })

        return features

    def _build_claim_drawing_mappings(self, modalities: List[ModalityContent]) -> Dict[int, List[str]]:
        """建立权利要求到图纸的映射"""
        mappings = {}

        # 收集文本内容
        text_content = ''
        for modality in modalities:
            if modality.modality_type == ModalityType.TEXT:
                text_content += modality.content + "\n"

        # 收集图纸引用
        drawing_references = {}
        for modality in modalities:
            if modality.modality_type == ModalityType.IMAGE:
                drawing_refs = modality.metadata.get('markup_references', [])
                for ref in drawing_refs:
                    drawing_refs[ref] = modality.location.get('page', 0)

        # 查找权利要求对图纸的引用
        claim_pattern = r'权利要求\s*(\d+).*?(图\s*\d+|附图\s*\d+)'
        matches = re.findall(claim_pattern, text_content)

        for claim_num, drawing_ref in matches:
            if claim_num not in mappings:
                mappings[int(claim_num)] = []

            if drawing_ref in drawing_references:
                mappings[int(claim_num)].append(f"page_{drawing_references[drawing_ref]}")

        return mappings

    def _collect_technical_diagrams(self, modalities: List[ModalityContent]) -> List[Dict[str, Any]]:
        """收集技术图纸"""
        diagrams = []

        for modality in modalities:
            if modality.modality_type == ModalityType.IMAGE:
                diagram_info = modality.metadata
                diagrams.append({
                    'page': diagram_info.get('page_number'),
                    'type': diagram_info.get('diagram_type'),
                    'elements': diagram_info.get('technical_elements', []),
                    'confidence': modality.confidence,
                    'location': modality.location
                })

        return diagrams

    def _calculate_modality_confidence(self, modalities: List[ModalityContent]) -> Dict[ModalityType, float]:
        """计算各模态置信度"""
        confidence_scores = {}

        for modality_type in ModalityType:
            type_modalities = [m for m in modalities if m.modality_type == modality_type]
            if type_modalities:
                # 计算平均置信度
                avg_confidence = sum(m.confidence for m in type_modalities) / len(type_modalities)
                confidence_scores[modality_type] = avg_confidence
            else:
                confidence_scores[modality_type] = 0.0

        return confidence_scores

# 测试代码
if __name__ == '__main__':
    processor = PatentMultimodalProcessor()

    # 测试文件
    test_pdf = '/Users/xujian/Athena工作平台/patent-platform/workspace/data/raw/disclosures/CN201815134U.pdf'

    if Path(test_pdf).exists():
        logger.info('🔍 开始多模态专利分析...')
        result = processor.analyze_patent_document(test_pdf)

        logger.info(f"\n📊 分析结果:")
        logger.info(f"专利ID: {result.patent_id}")
        logger.info(f"模态数量: {len(result.modalities)}")
        logger.info(f"跨模态关系: {len(result.cross_modal_relations)}")
        logger.info(f"统一特征: {len(result.unified_features)}")
        logger.info(f"技术图纸: {len(result.technical_diagrams)}")

        logger.info(f"\n📋 各模态置信度:")
        for modality, confidence in result.confidence_scores.items():
            logger.info(f"  {modality.value}: {confidence:.2f}")

        logger.info(f"\n🔗 权利要求-图纸映射:")
        for claim, drawings in result.claim_drawing_mappings.items():
            logger.info(f"  权利要求{claim}: {drawings}")
    else:
        logger.info(f"❌ 测试文件不存在: {test_pdf}")