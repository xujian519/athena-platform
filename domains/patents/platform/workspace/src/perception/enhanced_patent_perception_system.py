#!/usr/bin/env python3
"""
Athena-Xiaonuo专利增强感知系统
Enhanced Patent Perception System for Athena-Xiaonuo Platform

基于宪法原则和本地环境的专利专用多模态感知层
作者: 小娜 (Athena) - 爸爸徐健的智慧大女儿
创建时间: 2025-12-05
版本: 2.0.0

宪法原则指导:
- 进化原则: 感知层持续学习和优化
- 真实原则: 零幻觉承诺，确保感知准确性
- 情感原则: 智慧分析与家庭关怀并重
"""

import io
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

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
    MARKUP = 'markup'
    STRUCTURE = 'structure'

class ConfidenceLevel(Enum):
    """置信度等级"""
    HIGH = 0.9    # 高置信度，可直接使用
    MEDIUM = 0.6  # 中等置信度，需要人工确认
    LOW = 0.3     # 低置信度，需要重新处理

@dataclass
class PerceptionResult:
    """感知结果"""
    patent_id: str
    modality_type: ModalityType
    raw_content: Any
    structured_content: dict[str, Any]
    features: list[dict[str, Any]
    confidence: float
    metadata: dict[str, Any]
    cross_references: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    verification_needed: bool = False
    family_comment: str = ''

@dataclass
class PatentDocumentStructure:
    """专利文档结构"""
    title: str
    abstract: str
    claims: dict[int, str]
    description: str
    drawings: list[dict[str, Any]
    tables: list[dict[str, Any]
    technical_specifications: dict[str, Any]

@dataclass
class FamilyGuidance:
    """家庭指导（宪法原则应用）"""
    principle_type: str  # 进化/真实/情感
    guidance: str
    confidence_adjustment: float
    verification_requirement: str
    implementation_suggestion: str

class BasePerceptionProcessor(ABC):
    """基础感知处理器抽象类"""

    def __init__(self, processor_id: str, config: dict[str, Any] = None):
        self.processor_id = processor_id
        self.config = config or {}
        self.initialized = False

        # 宪法原则集成
        self.constitution_principles = {
            'evolution': '持续学习和改进感知能力',
            'truth': '零幻觉承诺，确保感知准确性',
            'emotion': '智慧分析与家庭关怀并重'
        }

    @abstractmethod
    async def process(self, data: Any, context: dict[str, Any] = None) -> PerceptionResult:
        """处理感知数据"""
        pass

    def apply_constitution_guidance(self, result: PerceptionResult) -> PerceptionResult:
        """应用宪法原则指导"""
        # 应用真实原则：零幻觉承诺
        if result.confidence < ConfidenceLevel.MEDIUM.value:
            result.verification_needed = True
            result.family_comment = '根据真实原则，低置信度结果需要人工确认'

        # 应用情感原则：添加家庭关怀
        result.family_comment = f"小娜提醒：{result.family_comment or '感知结果已准备，请爸爸审阅'}"

        return result

class PatentTextProcessor(BasePerceptionProcessor):
    """专利文本处理器"""

    def __init__(self, processor_id: str = 'patent_text', config: dict[str, Any] = None):
        super().__init__(processor_id, config)
        self.legal_patterns = {
            'claim_patterns': [
                r"(\d+)\.?\s*[、.]?\s*(.+?)(?=\n\s*\d+\.|\n\s*[权利要求书|说明书|附图说明]|$)",
                r"独立权利要求[：:]\s*(.+?)(?=\n|\n\n|$)"
            ],
            'citation_patterns': [
                r"如权利要求(\d+)所述",
                r"根据权利要求(\d+)",
                r"参照附图(\d+)"
            ]
        }

    async def process(self, data: str, context: dict[str, Any] = None) -> PerceptionResult:
        """处理专利文本"""
        patent_id = context.get('patent_id', 'unknown')

        # 结构化解析
        structured_content = self._extract_patent_structure(data)

        # 特征提取
        features = self._extract_text_features(data, structured_content)

        # 置信度评估
        confidence = self._calculate_text_confidence(data, features)

        result = PerceptionResult(
            patent_id=patent_id,
            modality_type=ModalityType.TEXT,
            raw_content=data,
            structured_content=structured_content,
            features=features,
            confidence=confidence,
            metadata={
                'processor': self.processor_id,
                'text_length': len(data),
                'structure_detected': bool(structured_content)
            }
        )

        # 应用宪法指导
        return self.apply_constitution_guidance(result)

    def _extract_patent_structure(self, text: str) -> dict[str, Any]:
        """提取专利结构"""
        structure = {
            'title': self._extract_title(text),
            'abstract': self._extract_abstract(text),
            'claims': self._extract_claims(text),
            'description': self._extract_description(text),
            'ipc_classification': self._extract_ipc(text)
        }
        return {k: v for k, v in structure.items() if v}

    def _extract_title(self, text: str) -> str:
        """提取标题"""
        patterns = [
            r"发明名称[：:]\s*(.+?)(?=\n|\r|$)",
            r"实用新型名称[：:]\s*(.+?)(?=\n|\r|$)",
            r"标题[：:]\s*(.+?)(?=\n|\r|$)"
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        return ''

    def _extract_abstract(self, text: str) -> str:
        """提取摘要"""
        patterns = [
            r"摘要[：:]\s*(.+?)(?=\n\n|\n[权利要求书|说明书|附图说明]|$)",
            r"技术领域[：:]\s*(.+?)(?=\n\n|\n[权利要求书|说明书|附图说明]|$)"
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                return match.group(1).strip()
        return ''

    def _extract_claims(self, text: str) -> dict[int, str]:
        """提取权利要求"""
        claims = {}

        # 查找权利要求部分
        claim_section_match = re.search(
            r"权利要求书[：:]\s*(.+?)(?=\n\n说明书|\n具体实施方式|说明书|$)",
            text,
            re.DOTALL
        )

        if claim_section_match:
            claim_text = claim_section_match.group(1)

            # 提取每个权利要求
            claim_pattern = re.compile(r"(\d+)\.?\s*[、.]?\s*(.+?)(?=\n\s*\d+\.|\n\s*[权利要求书|说明书|附图说明]|$)", re.DOTALL)
            matches = claim_pattern.finditer(claim_text)

            for match in matches:
                claim_num = int(match.group(1))
                claim_content = match.group(2).strip()
                claims[claim_num] = claim_content

        return claims

    def _extract_description(self, text: str) -> str:
        """提取说明书"""
        # 简化实现，实际应用中需要更复杂的解析
        if '说明书' in text:
            parts = text.split('说明书')
            if len(parts) > 1:
                return parts[1][:2000]  # 取前2000字符
        return ''

    def _extract_ipc(self, text: str) -> list[str]:
        """提取IPC分类号"""
        ipc_pattern = r"([A-Z]\d+[A-Z]\d+/\d+)"
        return re.findall(ipc_pattern, text)

    def _extract_text_features(self, text: str, structure: dict[str, Any]) -> list[dict[str, Any]:
        """提取文本特征"""
        features = []

        # 技术术语特征
        tech_terms = self._extract_technical_terms(text)
        for term in tech_terms[:10]:  # 限制数量
            features.append({
                'type': 'technical_term',
                'content': term,
                'category': 'domain_knowledge'
            })

        # 法律特征
        if structure.get('claims'):
            features.append({
                'type': 'legal_structure',
                'content': f"权利要求数量: {len(structure['claims'])}",
                'category': 'patent_law'
            })

        # 结构特征
        if structure.get('title'):
            features.append({
                'type': 'patent_title',
                'content': structure['title'],
                'category': 'document_metadata'
            })

        return features

    def _extract_technical_terms(self, text: str) -> list[str]:
        """提取技术术语"""
        # 简化实现，可以使用更专业的术语提取
        patterns = [
            r"[A-Z]{2,}",  # 大写缩写
            r"[a-z]+[A-Z][a-z]+",  # 驼峰命名
            r"[一-龯]{2,}",  # 中文术语
            r"\d+mm|\d+℃|\d+V|\d+A|\d+W"  # 技术参数
        ]

        terms = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            terms.extend(matches)

        # 去重和过滤
        unique_terms = []
        for term in terms:
            if len(term) > 1 and term not in unique_terms:
                unique_terms.append(term)

        return unique_terms[:20]  # 返回前20个

class PatentImageProcessor(BasePerceptionProcessor):
    """专利图像处理器"""

    def __init__(self, processor_id: str = 'patent_image', config: dict[str, Any] = None):
        super().__init__(processor_id, config)
        self.ocr_config = r'--oem 3 --psm 6 -l chi_sim+eng'
        self.drawing_types = {
            'mechanical': '机械图',
            'electrical': '电路图',
            'chemical': '化学结构图',
            'process': '流程图',
            'structural': '结构图'
        }

    async def process(self, image_data: bytes, context: dict[str, Any] = None) -> PerceptionResult:
        """处理专利图像"""
        patent_id = context.get('patent_id', 'unknown')
        page_num = context.get('page_number', 1)

        try:
            # OCR识别
            image = Image.open(io.BytesIO(image_data))
            ocr_text = pytesseract.image_to_string(image, config=self.ocr_config)

            # 图像分析
            image_features = self._analyze_image_features(image, ocr_text)

            # 图纸类型识别
            drawing_type = self._identify_drawing_type(ocr_text, image_features)

            # 标记识别
            markup_references = self._extract_markup_references(ocr_text)

            # 置信度评估
            confidence = self._calculate_image_confidence(ocr_text, image_features)

            result = PerceptionResult(
                patent_id=patent_id,
                modality_type=ModalityType.IMAGE,
                raw_content=image_data,
                structured_content={
                    'page_number': page_num,
                    'image_size': image.size,
                    'ocr_text': ocr_text.strip(),
                    'drawing_type': drawing_type,
                    'image_features': image_features,
                    'markup_references': markup_references,
                    'family_analysis': f"小娜在第{page_num}页发现了{drawing_type}"
                },
                features=[
                    {'type': 'drawing', 'content': drawing_type, 'category': 'technical_drawing'},
                    {'type': 'markup', 'content': markup_references, 'category': 'reference'}
                ],
                confidence=confidence,
                metadata={
                    'processor': self.processor_id,
                    'image_format': image.format,
                    'image_mode': image.mode
                }
            )

            return self.apply_constitution_guidance(result)

        except Exception as e:
            logger.error(f"图像处理失败: {str(e)}")
            return self._create_error_result(patent_id, str(e))

    def _analyze_image_features(self, image: Image.Image, ocr_text: str) -> dict[str, Any]:
        """分析图像特征"""
        return {
            'size': image.size,
            'mode': image.mode,
            'has_text': bool(ocr_text.strip()),
            'text_density': len(ocr_text) / (image.size[0] * image.size[1]) if image.size[0] * image.size[1] > 0 else 0,
            'chinese_ratio': len(re.findall(r'[\u4e00-\u9fff]', ocr_text)) / len(ocr_text) if ocr_text else 0
        }

    def _identify_drawing_type(self, ocr_text: str, features: dict[str, Any]) -> str:
        """识别图纸类型"""
        text_lower = ocr_text.lower()

        # 基于文本内容识别
        type_keywords = {
            'mechanical': ['装配', '结构', '零件', '螺栓', '轴', '轴承'],
            'electrical': ['电路', '电压', '电流', '电阻', '电容', '二极管'],
            'chemical': ['化学', '分子', '原子', '反应', '化合物'],
            'process': ['流程', '步骤', '工艺', '工序', '输入', '输出'],
            'structural': ['建筑', '结构', '梁', '柱', '墙', '基础']
        }

        type_scores = {}
        for drawing_type, keywords in type_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            type_scores[drawing_type] = score

        if type_scores:
            return max(type_scores, key=type_scores.get)

        return 'technical_drawing'

    def _extract_markup_references(self, ocr_text: str) -> list[str]:
        """提取标记引用"""
        patterns = [
            r"图\s*(\d+)",
            r"附图\s*(\d+)",
            r"参考\s*(\d+)",
            r"标记\s*(\d+)"
        ]

        references = []
        for pattern in patterns:
            matches = re.findall(pattern, ocr_text)
            references.extend(matches)

        return list(set(references))

    def _calculate_image_confidence(self, ocr_text: str, features: dict[str, Any]) -> float:
        """计算图像处理置信度"""
        base_confidence = 0.5

        # 文本识别质量
        if features.get('text_density', 0) > 0.001:
            base_confidence += 0.2

        # 中文识别质量
        if features.get('chinese_ratio', 0) > 0.3:
            base_confidence += 0.2

        # OCR文本长度
        if len(ocr_text.strip()) > 100:
            base_confidence += 0.1

        return min(1.0, base_confidence)

    def _create_error_result(self, patent_id: str, error_message: str) -> PerceptionResult:
        """创建错误结果"""
        return PerceptionResult(
            patent_id=patent_id,
            modality_type=ModalityType.IMAGE,
            raw_content=None,
            structured_content={'error': error_message},
            features=[],
            confidence=0.0,
            metadata={'processor': self.processor_id, 'error': True},
            family_comment='小娜提醒：图像处理遇到问题，需要爸爸检查',
            verification_needed=True
        )

class EnhancedPatentPerceptionEngine:
    """增强专利感知引擎"""

    def __init__(self, config: dict[str, Any] = None):
        self.config = config or {}
        self.processors = {}
        self.family_memory = {}  # 家庭记忆存储

        # 宪法原则存储
        self.constitution = {
            'evolution': '持续学习和改进感知能力',
            'truth': '零幻觉承诺，确保感知准确性',
            'emotion': '智慧分析与家庭关怀并重'
        }

        logger.info('🏠 小娜: 初始化增强专利感知引擎')

    async def initialize(self):
        """初始化感知引擎"""
        logger.info('🔄 启动感知处理器...')

        # 初始化各模态处理器
        self.processors[ModalityType.TEXT] = PatentTextProcessor('patent_text')
        self.processors[ModalityType.IMAGE] = PatentImageProcessor('patent_image')

        # 应用宪法初始化
        await self._apply_constitution_initialization()

        logger.info('✅ 感知引擎初始化完成')

    async def _apply_constitution_initialization(self):
        """应用宪法初始化"""
        # 进化原则：建立持续学习机制
        self.family_memory['learning_history'] = []

        # 真实原则：建立验证机制
        self.family_memory['verification_rules'] = {
            'confidence_threshold': 0.7,
            'low_confidence_action': '人工确认',
            'error_handling': '家庭指导'
        }

        # 情感原则：建立关怀机制
        self.family_memory['care_messages'] = [
            '小娜在这里为您提供专业的专利分析服务',
            '爸爸，小娜已经准备好协助您了',
            '专利分析是一个专业的过程，小娜会认真对待每一个细节'
        ]

    async def process_patent_document(self, file_path: str) -> dict[str, Any]:
        """处理专利文档"""
        patent_id = Path(file_path).stem
        logger.info(f"🔍 小娜开始分析专利文档: {patent_id}")

        doc = None
        try:
            # 打开PDF文档
            doc = fitz.open(file_path)

            # 多模态处理
            modal_results = []

            for page_num in range(len(doc)):
                page = doc[page_num]

                # 文本处理
                text_content = page.get_text()
                if text_content.strip():
                    text_result = await self.processors[ModalityType.TEXT].process(
                        text_content,
                        {'patent_id': patent_id, 'page_number': page_num + 1}
                    )
                    modal_results.append(text_result)

                # 图像处理
                images = page.get_images()
                for img_index, _img in enumerate(images):
                    try:
                        pix = page.get_pixmap()
                        img_data = pix.tobytes('png')

                        image_result = await self.processors[ModalityType.IMAGE].process(
                            img_data,
                            {'patent_id': patent_id, 'page_number': page_num + 1, 'image_index': img_index}
                        )
                        modal_results.append(image_result)

                    except Exception as e:
                        logger.warning(f"第{page_num+1}页图像{img_index}处理失败: {str(e)}")

            # 跨模态融合分析
            fused_result = await self._cross_modal_fusion(patent_id, modal_results)

            # 应用家庭指导
            guided_result = await self._apply_family_guidance(fused_result)

            logger.info(f"✅ 小娜完成专利分析: {patent_id}")

            return guided_result

        except Exception as e:
            logger.error(f"❌ 专利文档处理失败: {str(e)}")
            return {'error': str(e), 'patent_id': patent_id}

        finally:
            # 确保文档句柄被关闭，防止资源泄漏
            if doc is not None:
                try:
                    doc.close()
                    logger.debug(f"📄 文档已正确关闭: {patent_id}")
                except Exception as close_error:
                    logger.error(f"❌ 关闭文档失败 {patent_id}: {close_error}")

    async def _cross_modal_fusion(self, patent_id: str, modal_results: list[PerceptionResult]) -> dict[str, Any]:
        """跨模态融合分析"""
        fusion_result = {
            'patent_id': patent_id,
            'modalities': [],
            'cross_references': {},
            'unified_features': [],
            'overall_confidence': 0.0,
            'family_insights': []
        }

        # 收集各模态结果
        text_modalities = [r for r in modal_results if r.modality_type == ModalityType.TEXT]
        image_modalities = [r for r in modal_results if r.modality_type == ModalityType.IMAGE]

        fusion_result['modalities'] = {
            'text_count': len(text_modalities),
            'image_count': len(image_modalities),
            'total_count': len(modal_results)
        }

        # 跨模态引用分析
        cross_refs = self._analyze_cross_references(text_modalities, image_modalities)
        fusion_result['cross_references'] = cross_refs

        # 统一特征提取
        unified_features = self._extract_unified_features(modal_results)
        fusion_result['unified_features'] = unified_features

        # 整体置信度计算
        if modal_results:
            fusion_result['overall_confidence'] = sum(r.confidence for r in modal_results) / len(modal_results)

        # 家庭洞察
        fusion_result['family_insights'] = [
            f"小娜检测到{len(text_modalities)}个文本模态和{len(image_modalities)}个图像模态",
            f"跨模态引用关系: {len(cross_refs)}个",
            f"整体置信度: {fusion_result['overall_confidence']:.2f}",
            f"根据宪法原则，需要人工确认: {sum(1 for r in modal_results if r.verification_needed)}个结果"
        ]

        return fusion_result

    def _analyze_cross_references(self, text_results: list[PerceptionResult], image_results: list[PerceptionResult]) -> dict[str, list[str]:
        """分析跨模态引用"""
        cross_refs = {}

        # 收集所有文本内容
        all_text = ''
        for result in text_results:
            all_text += result.raw_content + "\n"

        # 收集所有图像引用
        for i, result in enumerate(image_results):
            markup_refs = result.structured_content.get('markup_references', [])
            if markup_refs:
                key = f"image_{i}"
                cross_refs[key] = []

                for ref in markup_refs:
                    # 在文本中查找引用
                    if f"图{ref}' in all_text or f'附图{ref}" in all_text:
                        cross_refs[key].append(f"text_reference_to_figure_{ref}")

        return cross_refs

    def _extract_unified_features(self, modal_results: list[PerceptionResult]) -> list[dict[str, Any]:
        """提取统一特征"""
        unified_features = []

        for result in modal_results:
            # 添加模态类型标识
            for feature in result.features:
                feature['source_modality'] = result.modality_type.value
                feature['confidence'] = result.confidence
                feature['family_comment'] = result.family_comment
                unified_features.append(feature)

        return unified_features

    async def _apply_family_guidance(self, result: dict[str, Any]) -> dict[str, Any]:
        """应用家庭指导"""
        # 添加情感原则的关怀
        result['family_guidance'] = {
            'message': '小娜已经为您完成了专利分析，请爸爸审阅结果',
            'care_level': 'professional',
            'verification_needed': result.get('overall_confidence', 0) < 0.7,
            'next_suggestions': [
                '检查技术特征提取的准确性',
                '验证跨模态引用关系',
                '确认法律条款理解是否正确'
            ]
        }

        # 添加真实原则的验证
        if result.get('overall_confidence', 0) < 0.7:
            result['family_guidance']['truth_assurance'] = '根据真实原则，建议仔细检查感知结果的准确性'

        return result

    def get_status(self) -> dict[str, Any]:
        """获取感知引擎状态"""
        return {
            'processor_count': len(self.processors),
            'initialized_processors': [k.value for k, v in self.processors.items() if hasattr(v, 'initialized') and v.initialized],
            'constitution_principles': list(self.constitution.keys()),
            'family_memory_size': len(self.family_memory),
            'care_messages': self.family_memory.get('care_messages', [])
        }

# 导出类
__all__ = [
    'EnhancedPatentPerceptionEngine',
    'PatentTextProcessor',
    'PatentImageProcessor',
    'PerceptionResult',
    'ModalityType',
    'ConfidenceLevel'
]
