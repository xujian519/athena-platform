#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专利知识抽取系统
Patent Knowledge Extraction System

从专利法律文档中抽取实体和关系，构建知识图谱
Extract entities and relationships from patent legal documents to build knowledge graph

作者: Athena AI系统
创建时间: 2025年12月6日
版本: 1.0.0
"""

import hashlib
import json
import logging
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# NLP相关库
try:
    import jieba
    import jieba.posseg as pseg
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False
    logger.info('警告: jieba未安装，将使用基础文本处理')

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logger.info('警告: spacy未安装，高级NLP功能不可用')

# 文档处理库
try:
    from docx import Document
    PYTHON_DOCX_AVAILABLE = True
except ImportError:
    PYTHON_DOCX_AVAILABLE = False
    logger.info('警告: python-docx未安装，无法处理.docx文件')

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False
    logger.info('警告: PyPDF2未安装，无法处理PDF文件')

# 本地模块
from patent_knowledge_graph_schema import (
    CaseEntity,
    EntityType,
    KnowledgeEntity,
    KnowledgeRelation,
    LawEntity,
    LegalArticleEntity,
    PatentKnowledgeGraphSchema,
    RelationType,
    TechnicalConceptEntity,
    generate_entity_id,
    generate_relation_id,
)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ExtractionResult:
    """抽取结果"""
    entities: List[KnowledgeEntity]
    relations: List[KnowledgeRelation]
    source_file: str
    extraction_time: datetime
    processing_stats: Dict[str, Any]

class DocumentProcessor(ABC):
    """文档处理器抽象基类"""

    @abstractmethod
    def can_process(self, file_path: str) -> bool:
        """检查是否能处理该文件"""
        pass

    @abstractmethod
    def extract_text(self, file_path: str) -> str:
        """从文件中提取文本"""
        pass

class WordDocumentProcessor(DocumentProcessor):
    """Word文档处理器"""

    def can_process(self, file_path: str) -> bool:
        return file_path.lower().endswith(('.doc', '.docx'))

    def extract_text(self, file_path: str) -> str:
        if not PYTHON_DOCX_AVAILABLE:
            raise ImportError('python-docx库未安装，无法处理Word文档')

        try:
            if file_path.lower().endswith('.docx'):
                doc = Document(file_path)
                text_parts = []
                for paragraph in doc.paragraphs:
                    if paragraph.text.strip():
                        text_parts.append(paragraph.text.strip())
                return '\n'.join(text_parts)
            else:
                # .doc文件需要使用其他库，这里简化处理
                raise ValueError('暂不支持.doc文件格式，请转换为.docx格式')
        except Exception as e:
            logger.error(f"处理Word文件失败 {file_path}: {str(e)}")
            return ''

class PDFDocumentProcessor(DocumentProcessor):
    """PDF文档处理器"""

    def can_process(self, file_path: str) -> bool:
        return file_path.lower().endswith('.pdf')

    def extract_text(self, file_path: str) -> str:
        if not PYPDF2_AVAILABLE:
            raise ImportError('PyPDF2库未安装，无法处理PDF文档')

        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text_parts = []
                for page in reader.pages:
                    text_parts.append(page.extract_text())
                return '\n'.join(text_parts)
        except Exception as e:
            logger.error(f"处理PDF文件失败 {file_path}: {str(e)}")
            return ''

class TextDocumentProcessor(DocumentProcessor):
    """文本文档处理器"""

    def can_process(self, file_path: str) -> bool:
        return file_path.lower().endswith(('.txt', '.md'))

    def extract_text(self, file_path: str) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            for encoding in ['gbk', 'gb2312', 'latin1']:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        return file.read()
                except UnicodeDecodeError:
                    continue
            raise ValueError('无法解码文件，尝试了多种编码格式')
        except Exception as e:
            logger.error(f"处理文本文件失败 {file_path}: {str(e)}")
            return ''

class PatentKnowledgeExtractor:
    """专利知识抽取器"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化知识抽取器

        Args:
            config: 配置字典，包含各种抽取参数
        """
        self.config = config or {}
        self.schema = PatentKnowledgeGraphSchema()

        # 初始化文档处理器
        self.document_processors = [
            WordDocumentProcessor(),
            PDFDocumentProcessor(),
            TextDocumentProcessor()
        ]

        # 初始化NLP工具
        self._init_nlp_tools()

        # 加载法律术语词典
        self._load_legal_terminology()

        # 抽取统计
        self.extraction_stats = {
            'processed_files': 0,
            'total_entities': 0,
            'total_relations': 0,
            'errors': 0
        }

        logger.info('专利知识抽取器初始化完成')

    def _init_nlp_tools(self):
        """初始化NLP工具"""
        # 添加法律术语到jieba词典
        if JIEBA_AVAILABLE:
            legal_terms = [
                '专利法', '实施细则', '审查指南', '无效宣告', '复审',
                '权利要求', '说明书', '发明', '实用新型', '外观设计',
                '新颖性', '创造性', '实用性', '现有技术', '公开充分',
                '侵权', '等同侵权', '全部技术特征', '覆盖原则'
            ]
            for term in legal_terms:
                jieba.add_word(term, freq=1000, tag='nw')

        # 初始化spaCy（如果可用）
        self.nlp = None
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load('zh_core_web_sm')
                logger.info('spaCy中文模型加载成功')
            except OSError:
                logger.warning('spaCy中文模型未找到，使用基础NLP功能')
                self.nlp = None

    def _load_legal_terminology(self):
        """加载法律术语词典"""
        self.legal_entities = {
            '法律法规': ['专利法', '著作权法', '商标法', '反不正当竞争法'],
            '司法机关': ['最高人民法院', '知识产权法院', '专利复审委员会'],
            '法律程序': ['无效宣告', '复审', '行政诉讼', '民事诉讼'],
            '专利类型': ['发明专利', '实用新型', '外观设计'],
            '授权条件': ['新颖性', '创造性', '实用性']
        }

        self.legal_concepts = {
            '权利要求解释': ['清楚', '简要', '得到说明书支持', '保护范围'],
            '侵权判定': ['全面覆盖原则', '等同原则', '禁止反悔原则'],
            '无效理由': ['缺乏新颖性', '缺乏创造性', '公开不充分', '修改超范围']
        }

    def _get_document_processor(self, file_path: str) -> DocumentProcessor | None:
        """获取合适的文档处理器"""
        for processor in self.document_processors:
            if processor.can_process(file_path):
                return processor
        return None

    def _preprocess_text(self, text: str) -> str:
        """预处理文本"""
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)

        # 移除特殊字符（保留中文、英文、数字、基本标点）
        text = re.sub(r'[^\u4e00-\u9fff\w\s.,;:!?()（）【】''''''''、。，；：！？]', '', text)

        # 标准化标点符号
        text = text.replace('（', '(').replace('）', ')')
        text = text.replace('【', '[').replace('】', ']')
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")

        return text.strip()

    def _extract_legal_entities(self, text: str, source_file: str) -> List[KnowledgeEntity]:
        """抽取法律实体"""
        entities = []

        # 抽取法条引用
        article_pattern = r'第([一二三四五六七八九十百千万\d]+)条[，。]?(?:第([一二三四五六七八九十百千万\d]+)款[，。]?)?'
        article_matches = re.finditer(article_pattern, text)

        for match in article_matches:
            article_num = match.group(1)
            article_name = f"第{article_num}条"
            if match.group(2):
                article_name += f"第{match.group(2)}款"

            # 获取上下文
            start, end = match.span()
            context_start = max(0, start - 100)
            context_end = min(len(text), end + 100)
            context = text[context_start:context_end].strip()

            entity = LegalArticleEntity(
                id=generate_entity_id(EntityType.LEGAL_ARTICLE, article_name, source_file),
                type=EntityType.LEGAL_ARTICLE,
                name=article_name,
                description=context,
                properties={
                    'article_number': article_num,
                    'sub_article': match.group(2),
                    'context': context
                },
                source=source_file,
                confidence=0.9
            )
            entities.append(entity)

        # 抽取案例引用
        case_pattern = r'([（\(][^）\)]*[）\)]\d{4}[）\)]?[年]?\s*[\u4e00-\u9fff\d]+[号]|案号[:：]\s*[\w\d]+)'
        case_matches = re.finditer(case_pattern, text)

        for match in case_matches:
            case_ref = match.group()
            entity = KnowledgeEntity(
                id=generate_entity_id(EntityType.COURT_CASE, case_ref, source_file),
                type=EntityType.COURT_CASE,
                name=case_ref,
                description=f"案例引用: {case_ref}",
                properties={'reference_text': case_ref},
                source=source_file,
                confidence=0.7
            )
            entities.append(entity)

        # 抽取技术概念
        tech_patterns = [
            r'技术特征[:：]\s*([^。；\n]+)',
            r'技术方案[:：]\s*([^。；\n]+)',
            r'发明内容[:：]\s*([^。；\n]+)'
        ]

        for pattern in tech_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                concept = match.group(1).strip()
                if len(concept) > 5:  # 过滤过短的匹配
                    entity = TechnicalConceptEntity(
                        id=generate_entity_id(EntityType.TECHNICAL_CONCEPT, concept[:20], source_file),
                        type=EntityType.TECHNICAL_CONCEPT,
                        name=concept,
                        properties={
                            'extraction_pattern': pattern,
                            'context': match.group(0)
                        },
                        source=source_file,
                        confidence=0.6
                    )
                    entities.append(entity)

        return entities

    def _extract_relations(self, text: str, entities: List[KnowledgeEntity], source_file: str) -> List[KnowledgeRelation]:
        """抽取实体间关系"""
        relations = []

        # 构建实体位置映射
        entity_positions = {}
        for entity in entities:
            if entity.name in text:
                for match in re.finditer(re.escape(entity.name), text):
                    entity_positions[entity.id] = match.span()

        # 抽取引用关系
        citation_patterns = [
            r'([^。；\n]*)根据([^\s]+)条([^\s]*)的规定',
            r'([^。；\n]*)依据([^\s]+)条([^\s]*)',
            r'([^。；\n]*)按照([^\s]+)条([^\s]*)'
        ]

        for pattern in citation_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                # 查找对应的法条实体
                for entity in entities:
                    if entity.type == EntityType.LEGAL_ARTICLE and entity.name in match.group(2):
                        # 创建案例->法条的引用关系
                        case_entities = [e for e in entities if e.type in
                                       [EntityType.INVALIDATION_DECISION, EntityType.REEXAMINATION_DECISION]]
                        for case_entity in case_entities:
                            relation = KnowledgeRelation(
                                id=generate_relation_id(case_entity.id, entity.id, RelationType.CITES),
                                source=case_entity.id,
                                target=entity.id,
                                type=RelationType.CITES,
                                properties={
                                    'citation_context': match.group(0),
                                    'citation_type': 'statutory'
                                },
                                evidence=match.group(0),
                                source_document=source_file,
                                confidence=0.8
                            )
                            relations.append(relation)

        # 抽取解释关系
        interpretation_patterns = [
            r'([^。；\n]*)对([^\s]+)条([^\s]*)的解释',
            r'([^。；\n*)]([^\s]+)条([^\s]*)的含义',
            r'([^。；\n*)明确([^\s]+)条([^\s]*)的范围'
        ]

        for pattern in interpretation_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                for entity in entities:
                    if entity.type == EntityType.LEGAL_ARTICLE and entity.name in match.group(2):
                        # 创建解释关系
                        interpretation_entities = [e for e in entities if e.type in
                                                 [EntityType.COURT_CASE, EntityType.INVALIDATION_DECISION]]
                        for interp_entity in interpretation_entities:
                            relation = KnowledgeRelation(
                                id=generate_relation_id(interp_entity.id, entity.id, RelationType.INTERPRETS),
                                source=interp_entity.id,
                                target=entity.id,
                                type=RelationType.INTERPRETS,
                                properties={
                                    'interpretation_context': match.group(0),
                                    'interpretation_method': 'judicial'
                                },
                                evidence=match.group(0),
                                source_document=source_file,
                                confidence=0.75
                            )
                            relations.append(relation)

        return relations

    def _process_document(self, file_path: str) -> ExtractionResult:
        """处理单个文档"""
        start_time = datetime.now()

        # 选择文档处理器
        processor = self._get_document_processor(file_path)
        if not processor:
            logger.warning(f"没有找到合适的处理器: {file_path}")
            return ExtractionResult(
                entities=[], relations=[],
                source_file=file_path,
                extraction_time=datetime.now(),
                processing_stats={'error': 'Unsupported file format'}
            )

        try:
            # 提取文本
            logger.info(f"正在处理文件: {file_path}")
            raw_text = processor.extract_text(file_path)

            if not raw_text:
                logger.warning(f"文件内容为空: {file_path}")
                return ExtractionResult(
                    entities=[], relations=[],
                    source_file=file_path,
                    extraction_time=datetime.now(),
                    processing_stats={'error': 'Empty file content'}
                )

            # 预处理文本
            text = self._preprocess_text(raw_text)

            # 判断文档类型
            file_name = os.path.basename(file_path)
            doc_type = self._classify_document_type(text, file_name)

            # 根据文档类型进行专门处理
            entities, relations = self._extract_by_document_type(text, file_path, doc_type)

            # 通用实体和关系抽取
            if doc_type != 'legal_regulation':  # 法律法规已有专门处理
                general_entities = self._extract_legal_entities(text, file_path)
                general_relations = self._extract_relations(text, general_entities, file_path)
                entities.extend(general_entities)
                relations.extend(general_relations)

            # 去重
            entities = self._deduplicate_entities(entities)
            relations = self._deduplicate_relations(relations)

            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()

            stats = {
                'doc_type': doc_type,
                'text_length': len(text),
                'processing_time': processing_time,
                'entities_count': len(entities),
                'relations_count': len(relations)
            }

            self.extraction_stats['processed_files'] += 1
            self.extraction_stats['total_entities'] += len(entities)
            self.extraction_stats['total_relations'] += len(relations)

            logger.info(f"处理完成: {file_path}, 实体: {len(entities)}, 关系: {len(relations)}, 耗时: {processing_time:.2f}s")

            return ExtractionResult(
                entities=entities,
                relations=relations,
                source_file=file_path,
                extraction_time=end_time,
                processing_stats=stats
            )

        except Exception as e:
            logger.error(f"处理文档失败 {file_path}: {str(e)}")
            self.extraction_stats['errors'] += 1
            return ExtractionResult(
                entities=[], relations=[],
                source_file=file_path,
                extraction_time=datetime.now(),
                processing_stats={'error': str(e)}
            )

    def _classify_document_type(self, text: str, file_name: str) -> str:
        """分类文档类型"""
        text_lower = text.lower()
        file_name_lower = file_name.lower()

        # 基于文件名判断
        if '无效' in file_name_lower:
            return 'invalidation_decision'
        elif '复审' in file_name_lower:
            return 'reexamination_decision'
        elif '指南' in file_name_lower:
            return 'examination_guideline'
        elif '法' in file_name_lower or '条例' in file_name_lower:
            return 'legal_regulation'

        # 基于内容判断
        if '专利法' in text or '实施细则' in text:
            return 'legal_regulation'
        elif '审查指南' in text:
            return 'examination_guideline'
        elif '无效宣告' in text or '请求人' in text and '专利权' in text:
            return 'invalidation_decision'
        elif '复审' in text and '请求' in text:
            return 'reexamination_decision'

        return 'unknown'

    def _extract_by_document_type(self, text: str, file_path: str, doc_type: str) -> Tuple[List[KnowledgeEntity], List[KnowledgeRelation]]:
        """根据文档类型进行专门抽取"""
        entities = []
        relations = []
        file_name = os.path.basename(file_path)

        if doc_type == 'legal_regulation':
            # 法律法规文档处理
            entities.extend(self._extract_legal_regulation_entities(text, file_path))
            relations.extend(self._extract_legal_regulation_relations(text, entities, file_path))

        elif doc_type == 'invalidation_decision':
            # 无效宣告决定处理
            entities.extend(self._extract_invalidation_case_entities(text, file_name, file_path))
            relations.extend(self._extract_case_relations(text, entities, file_path))

        elif doc_type == 'reexamination_decision':
            # 复审决定处理
            entities.extend(self._extract_reexamination_case_entities(text, file_name, file_path))
            relations.extend(self._extract_case_relations(text, entities, file_path))

        elif doc_type == 'examination_guideline':
            # 审查指南处理
            entities.extend(self._extract_guideline_entities(text, file_path))
            relations.extend(self._extract_guideline_relations(text, entities, file_path))

        return entities, relations

    def _extract_legal_regulation_entities(self, text: str, file_path: str) -> List[KnowledgeEntity]:
        """抽取法律法规实体"""
        entities = []

        # 抽取法律/法规基本信息
        title_match = re.search(r'([^。\n]*(?:法|条例|规定|办法|细则|指南)[^。\n]*)', text)
        if title_match:
            title = title_match.group(1).strip()

            # 判断是法律还是法规
            if '专利法' in title:
                entity_type = EntityType.LAW
            elif '细则' in title or '条例' in title:
                entity_type = EntityType.REGULATION
            elif '指南' in title:
                entity_type = EntityType.EXAMINATION_GUIDELINE
            else:
                entity_type = EntityType.LAW

            if entity_type == EntityType.LAW:
                entity = LawEntity(
                    id=generate_entity_id(entity_type, title, file_path),
                    type=entity_type,
                    name=title,
                    properties={
                        'issuing_authority': self._extract_issuing_authority(text),
                        'effective_date': self._extract_effective_date(text)
                    },
                    source=file_path,
                    confidence=0.95
                )
            else:
                entity = KnowledgeEntity(
                    id=generate_entity_id(entity_type, title, file_path),
                    type=entity_type,
                    name=title,
                    properties={
                        'issuing_authority': self._extract_issuing_authority(text),
                        'effective_date': self._extract_effective_date(text)
                    },
                    source=file_path,
                    confidence=0.95
                )
            entities.append(entity)

        # 抽取章节结构
        chapter_pattern = r'第[一二三四五六七八九十百千万\d]+章[^\n]*'
        chapter_matches = re.finditer(chapter_pattern, text)

        for match in chapter_matches:
            chapter_title = match.group().strip()
            entity = KnowledgeEntity(
                id=generate_entity_id(EntityType.LEGAL_ARTICLE, chapter_title, file_path),
                type=EntityType.LEGAL_ARTICLE,
                name=chapter_title,
                properties={
                    'structure_type': 'chapter',
                    'chapter_number': self._extract_chapter_number(chapter_title)
                },
                source=file_path,
                confidence=0.9
            )
            entities.append(entity)

        return entities

    def _extract_invalidation_case_entities(self, text: str, file_name: str, file_path: str) -> List[KnowledgeEntity]:
        """抽取无效宣告案例实体"""
        entities = []

        # 从文件名提取案件信息
        case_number = self._extract_case_number_from_filename(file_name)

        if case_number:
            entity = CaseEntity(
                id=generate_entity_id(EntityType.INVALIDATION_DECISION, case_number, file_path),
                type=EntityType.INVALIDATION_DECISION,
                name=case_number,
                properties={
                    'case_number': case_number,
                    'decision_type': '无效宣告'
                },
                source=file_path,
                confidence=1.0
            )
            entities.append(entity)

        # 抽取当事人信息
        applicant_pattern = r'请求人[:：]\s*([^。\n]+)'
        applicant_matches = re.finditer(applicant_pattern, text)

        for match in applicant_matches:
            applicant_name = match.group(1).strip()
            entity = KnowledgeEntity(
                id=generate_entity_id(EntityType.APPLICANT, applicant_name, file_path),
                type=EntityType.APPLICANT,
                name=applicant_name,
                properties={'role': '请求人'},
                source=file_path,
                confidence=0.8
            )
            entities.append(entity)

        patent_holder_pattern = r'专利权人[:：]\s*([^。\n]+)'
        holder_matches = re.finditer(patent_holder_pattern, text)

        for match in holder_matches:
            holder_name = match.group(1).strip()
            entity = KnowledgeEntity(
                id=generate_entity_id(EntityType.PATENT_HOLDER, holder_name, file_path),
                type=EntityType.PATENT_HOLDER,
                name=holder_name,
                properties={'role': '专利权人'},
                source=file_path,
                confidence=0.8
            )
            entities.append(entity)

        # 抽取专利号
        patent_pattern = r'专利号[:：]?\s*(ZL[\d.]+|\d+\.\d+)'
        patent_matches = re.finditer(patent_pattern, text)

        for match in patent_matches:
            patent_number = match.group(1)
            entity = KnowledgeEntity(
                id=generate_entity_id(EntityType.PATENT, patent_number, file_path),
                type=EntityType.PATENT,
                name=patent_number,
                properties={'patent_type': '涉案专利'},
                source=file_path,
                confidence=0.9
            )
            entities.append(entity)

        return entities

    def _extract_reexamination_case_entities(self, text: str, file_name: str, file_path: str) -> List[KnowledgeEntity]:
        """抽取复审案例实体"""
        entities = []

        # 类似于无效宣告案例的处理
        case_number = self._extract_case_number_from_filename(file_name)

        if case_number:
            entity = CaseEntity(
                id=generate_entity_id(EntityType.REEXAMINATION_DECISION, case_number, file_path),
                type=EntityType.REEXAMINATION_DECISION,
                name=case_number,
                properties={
                    'case_number': case_number,
                    'decision_type': '复审决定'
                },
                source=file_path,
                confidence=1.0
            )
            entities.append(entity)

        # 其他实体抽取逻辑类似无效宣告案例
        # 这里可以根据复审决定的特点进行专门处理

        return entities

    def _extract_guideline_entities(self, text: str, file_path: str) -> List[KnowledgeEntity]:
        """抽取审查指南实体"""
        entities = []

        # 抽取指南章节
        section_patterns = [
            r'第[一二三四五六七八九十百千万\d]+部分[^\n]*',
            r'第[一二三四五六七八九十百千万\d]+章[^\n]*',
            r'第[一二三四五六七八九十百千万\d]+节[^\n]*'
        ]

        for pattern in section_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                section_title = match.group().strip()
                entity = KnowledgeEntity(
                    id=generate_entity_id(EntityType.GUIDELINE_SECTION, section_title, file_path),
                    type=EntityType.GUIDELINE_SECTION,
                    name=section_title,
                    properties={
                        'section_type': self._determine_section_type(section_title),
                        'section_content': self._extract_section_content(text, match.start())
                    },
                    source=file_path,
                    confidence=0.9
                )
                entities.append(entity)

        return entities

    def _extract_legal_regulation_relations(self, text: str, entities: List[KnowledgeEntity], file_path: str) -> List[KnowledgeRelation]:
        """抽取法律法规关系"""
        relations = []

        # 找到法律实体
        law_entities = [e for e in entities if e.type == EntityType.LAW]
        article_entities = [e for e in entities if e.type == EntityType.LEGAL_ARTICLE]

        for law_entity in law_entities:
            for article_entity in article_entities:
                # 如果章节属于该法律，创建包含关系
                if self._is_article_belong_to_law(article_entity, law_entity, text):
                    relation = KnowledgeRelation(
                        id=generate_relation_id(law_entity.id, article_entity.id, RelationType.CONTAINS),
                        source=law_entity.id,
                        target=article_entity.id,
                        type=RelationType.CONTAINS,
                        properties={'relation_type': 'legal_hierarchy'},
                        source_document=file_path,
                        confidence=0.85
                    )
                    relations.append(relation)

        return relations

    def _extract_case_relations(self, text: str, entities: List[KnowledgeEntity], file_path: str) -> List[KnowledgeRelation]:
        """抽取案例关系"""
        relations = []

        case_entities = [e for e in entities if e.type in [EntityType.INVALIDATION_DECISION, EntityType.REEXAMINATION_DECISION]]
        article_entities = [e for e in entities if e.type == EntityType.LEGAL_ARTICLE]
        applicant_entities = [e for e in entities if e.type == EntityType.APPLICANT]
        patent_entities = [e for e in entities if e.type == EntityType.PATENT]

        for case_entity in case_entities:
            # 案例与当事人的关系
            for applicant_entity in applicant_entities:
                relation = KnowledgeRelation(
                    id=generate_relation_id(case_entity.id, applicant_entity.id, RelationType.FILES),
                    source=applicant_entity.id,
                    target=case_entity.id,
                    type=RelationType.FILES,
                    properties={'relation_type': 'case_applicant'},
                    source_document=file_path,
                    confidence=0.8
                )
                relations.append(relation)

            # 案例与专利的关系
            for patent_entity in patent_entities:
                relation = KnowledgeRelation(
                    id=generate_relation_id(case_entity.id, patent_entity.id, RelationType.GOVERNS),
                    source=case_entity.id,
                    target=patent_entity.id,
                    type=RelationType.GOVERNS,
                    properties={'relation_type': 'case_patent'},
                    source_document=file_path,
                    confidence=0.9
                )
                relations.append(relation)

        return relations

    def _extract_guideline_relations(self, text: str, entities: List[KnowledgeEntity], file_path: str) -> List[KnowledgeRelation]:
        """抽取审查指南关系"""
        relations = []

        # 审查指南内部的层次关系
        section_entities = [e for e in entities if e.type == EntityType.GUIDELINE_SECTION]

        for i, entity1 in enumerate(section_entities):
            for entity2 in section_entities[i+1:]:
                # 基于文本位置判断层次关系
                if self._is_section_contains_section(entity1, entity2, text):
                    relation = KnowledgeRelation(
                        id=generate_relation_id(entity1.id, entity2.id, RelationType.CONTAINS),
                        source=entity1.id,
                        target=entity2.id,
                        type=RelationType.CONTAINS,
                        properties={'relation_type': 'guideline_hierarchy'},
                        source_document=file_path,
                        confidence=0.7
                    )
                    relations.append(relation)

        return relations

    def _deduplicate_entities(self, entities: List[KnowledgeEntity]) -> List[KnowledgeEntity]:
        """去重实体"""
        seen = set()
        deduplicated = []

        for entity in entities:
            entity_key = (entity.type, entity.name.lower())
            if entity_key not in seen:
                seen.add(entity_key)
                deduplicated.append(entity)

        return deduplicated

    def _deduplicate_relations(self, relations: List[KnowledgeRelation]) -> List[KnowledgeRelation]:
        """去重关系"""
        seen = set()
        deduplicated = []

        for relation in relations:
            relation_key = (relation.source, relation.target, relation.type)
            if relation_key not in seen:
                seen.add(relation_key)
                deduplicated.append(relation)

        return deduplicated

    def _extract_issuing_authority(self, text: str) -> str | None:
        """提取发布机关"""
        authority_patterns = [
            r'([^。\n]*委员会[^。\n]*)发布',
            r'([^。\n]*人民政府[^。\n]*)发布',
            r'([^。\n]*人民法院[^。\n]*)发布'
        ]

        for pattern in authority_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()

        return None

    def _extract_effective_date(self, text: str) -> str | None:
        """提取生效日期"""
        date_patterns = [
            r'自(\d{4}年\d{1,2}月\d{1,2}日)起施行',
            r'(\d{4}年\d{1,2}月\d{1,2}日)起施行',
            r'生效日期[:：]\s*(\d{4}年\d{1,2}月\d{1,2}日)'
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()

        return None

    def _extract_chapter_number(self, chapter_title: str) -> str | None:
        """提取章节编号"""
        match = re.search(r'第([一二三四五六七八九十百千万\d]+)章', chapter_title)
        if match:
            return match.group(1)
        return None

    def _extract_case_number_from_filename(self, filename: str) -> str | None:
        """从文件名提取案件编号"""
        # 常见的案件编号模式
        patterns = [
            r'(\d+W\d+)',  # 如 5W12345
            r'WX\d+',      # 如 WX12345
            r'\d{8,}',     # 纯数字
            r'CN\d+\.\d+', # 如 CN123456789.0
        ]

        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                return match.group(1)

        return filename.split('.')[0]  # 如果没有匹配，使用文件名

    def _determine_section_type(self, section_title: str) -> str:
        """确定章节类型"""
        if '部分' in section_title:
            return 'part'
        elif '章' in section_title:
            return 'chapter'
        elif '节' in section_title:
            return 'section'
        else:
            return 'unknown'

    def _extract_section_content(self, text: str, start_pos: int) -> str:
        """提取章节内容"""
        # 找到下一个章节的位置
        next_section_pattern = r'第[一二三四五六七八九十百千万\d]+(?:部分|章|节)'
        next_match = re.search(next_section_pattern, text[start_pos+100:])  # 从当前位置后100字符开始搜索

        if next_match:
            end_pos = start_pos + 100 + next_match.start()
        else:
            end_pos = min(start_pos + 1000, len(text))  # 限制长度

        return text[start_pos:end_pos].strip()[:200]  # 返回前200字符

    def _is_article_belong_to_law(self, article_entity: KnowledgeEntity, law_entity: KnowledgeEntity, text: str) -> bool:
        """判断法条是否属于法律"""
        # 简单实现：如果法条在文本中出现在法律名称之后，认为属于该法律
        law_pos = text.find(law_entity.name)
        article_pos = text.find(article_entity.name)

        return law_pos != -1 and article_pos != -1 and article_pos > law_pos

    def _is_section_contains_section(self, section1: KnowledgeEntity, section2: KnowledgeEntity, text: str) -> bool:
        """判断章节1是否包含章节2"""
        # 简单实现：基于文本位置判断
        section1_pos = text.find(section1.name)
        section2_pos = text.find(section2.name)

        return section1_pos != -1 and section2_pos != -1 and section2_pos > section1_pos

    def process_directory(self, directory_path: str, recursive: bool = True, max_files: int = None) -> List[ExtractionResult]:
        """处理目录中的所有文档"""
        logger.info(f"开始处理目录: {directory_path}")

        # 获取所有文件
        if recursive:
            file_paths = []
            for root, dirs, files in os.walk(directory_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if any(file_path.lower().endswith(ext) for ext in ['.doc', '.docx', '.pdf', '.txt', '.md']):
                        file_paths.append(file_path)
        else:
            file_paths = [os.path.join(directory_path, f) for f in os.listdir(directory_path)
                         if os.path.isfile(os.path.join(directory_path, f)) and
                         any(f.lower().endswith(ext) for ext in ['.doc', '.docx', '.pdf', '.txt', '.md'])]

        if max_files:
            file_paths = file_paths[:max_files]

        logger.info(f"找到 {len(file_paths)} 个文件待处理")

        results = []
        for i, file_path in enumerate(file_paths, 1):
            logger.info(f"处理进度: {i}/{len(file_paths)}")
            result = self._process_document(file_path)
            results.append(result)

        logger.info(f"目录处理完成，共处理 {len(results)} 个文件")
        self._log_extraction_stats()

        return results

    def _log_extraction_stats(self):
        """记录抽取统计信息"""
        stats = self.extraction_stats
        logger.info('=' * 50)
        logger.info('抽取统计信息:')
        logger.info(f"  处理文件数: {stats['processed_files']}")
        logger.info(f"  总实体数: {stats['total_entities']}")
        logger.info(f"  总关系数: {stats['total_relations']}")
        logger.info(f"  错误数: {stats['errors']}")
        if stats['processed_files'] > 0:
            logger.info(f"  平均每文件实体数: {stats['total_entities'] / stats['processed_files']:.1f}")
            logger.info(f"  平均每文件关系数: {stats['total_relations'] / stats['processed_files']:.1f}")
        logger.info('=' * 50)

    def export_results(self, results: List[ExtractionResult], output_dir: str):
        """导出抽取结果"""
        os.makedirs(output_dir, exist_ok=True)

        # 收集所有实体和关系
        all_entities = []
        all_relations = []

        for result in results:
            all_entities.extend(result.entities)
            all_relations.extend(result.relations)

        # 导出实体
        entities_file = os.path.join(output_dir, 'entities.json')
        entities_data = []
        for entity in all_entities:
            entity_dict = {
                'id': entity.id,
                'type': entity.type.value,
                'name': entity.name,
                'description': entity.description,
                'properties': entity.properties,
                'source': entity.source,
                'confidence': entity.confidence,
                'created_at': entity.created_at.isoformat() if entity.created_at else None
            }
            entities_data.append(entity_dict)

        with open(entities_file, 'w', encoding='utf-8') as f:
            json.dump(entities_data, f, ensure_ascii=False, indent=2, default=str)

        # 导出关系
        relations_file = os.path.join(output_dir, 'relations.json')
        relations_data = []
        for relation in all_relations:
            relation_dict = {
                'id': relation.id,
                'source': relation.source,
                'target': relation.target,
                'type': relation.type.value,
                'properties': relation.properties,
                'confidence': relation.confidence,
                'evidence': relation.evidence,
                'source_document': relation.source_document,
                'created_at': relation.created_at.isoformat() if relation.created_at else None
            }
            relations_data.append(relation_dict)

        with open(relations_file, 'w', encoding='utf-8') as f:
            json.dump(relations_data, f, ensure_ascii=False, indent=2, default=str)

        # 导出统计信息
        stats_file = os.path.join(output_dir, 'extraction_stats.json')
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.extraction_stats, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"结果已导出到: {output_dir}")
        logger.info(f"  实体文件: {entities_file}")
        logger.info(f"  关系文件: {relations_file}")
        logger.info(f"  统计文件: {stats_file}")

# ============================================================================
# 使用示例
# ============================================================================

if __name__ == '__main__':
    # 创建抽取器
    extractor = PatentKnowledgeExtractor()

    # 处理单个文件示例
    # result = extractor._process_document("/path/to/document.docx")

    # 处理目录示例
    # results = extractor.process_directory("/Users/xujian/学习资料/专利", max_files=5)

    # 导出结果示例
    # extractor.export_results(results, "/tmp/patent_extraction_results")

    logger.info('专利知识抽取系统已就绪')
    logger.info('支持处理的文件格式: .doc, .docx, .pdf, .txt, .md')
    logger.info('主要功能:')
    logger.info('  1. 法律法规实体抽取')
    logger.info('  2. 案例文书实体抽取')
    logger.info('  3. 技术概念抽取')
    logger.info('  4. 法律关系抽取')
    logger.info('  5. 批量文档处理')
    logger.info('  6. 结果导出为JSON格式')