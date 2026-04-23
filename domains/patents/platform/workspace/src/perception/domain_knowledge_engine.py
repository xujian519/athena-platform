#!/usr/bin/env python3
"""
领域知识引擎 - 动态知识注入与检索增强
Domain Knowledge Engine - Dynamic Knowledge Injection and RAG

基于设计文档要求的领域知识库集成和动态知识注入系统
作者: 小娜 (Athena) - 爸爸徐健的智慧大女儿
创建时间: 2025-12-05
版本: 1.0.0
"""

import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

# 数据处理导入
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

logger = logging.getLogger(__name__)

class KnowledgeType(Enum):
    """知识类型"""
    PATENT_LAW = 'patent_law'           # 专利法律
    TECHNICAL_STANDARD = 'technical_standard'  # 技术标准
    DOMAIN_EXPERTISE = 'domain_expertise'      # 领域专业知识
    PRIOR_ART = 'prior_art'             # 现有技术
    TECHNICAL_TERM = 'technical_term'   # 技术术语
    CLASSIFICATION = 'classification'    # 分类知识

class KnowledgeSource(Enum):
    """知识来源"""
    PATENT_DATABASE = 'patent_database'     # 专利数据库
    TECHNICAL_LITERATURE = 'technical_literature'  # 技术文献
    EXPERT_INPUT = 'expert_input'           # 专家输入
    WEB_CRAWLING = 'web_crawling'           # 网络爬取
    USER_FEEDBACK = 'user_feedback'         # 用户反馈
    SYSTEM_GENERATED = 'system_generated'   # 系统生成

@dataclass
class KnowledgeEntity:
    """知识实体"""
    entity_id: str
    name: str
    type: KnowledgeType
    definition: str
    aliases: list[str] = field(default_factory=list)
    attributes: dict[str, Any] = field(default_factory=dict)
    relationships: dict[str, list[str] = field(default_factory=dict)
    confidence: float = 1.0
    source: KnowledgeSource = KnowledgeSource.SYSTEM_GENERATED
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    last_accessed: datetime | None = None

@dataclass
class KnowledgeTriple:
    """知识三元组"""
    triple_id: str
    subject: str          # 主语
    predicate: str        # 谓语
    object: str           # 宾语
    confidence: float
    source: KnowledgeSource
    evidence: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class RetrievalResult:
    """检索结果"""
    query: str
    retrieved_entities: list[KnowledgeEntity]
    retrieved_triples: list[KnowledgeTriple]
    relevance_scores: list[float]
    retrieval_method: str
    total_results: int
    query_time: float

class PatentKnowledgeBase:
    """专利知识库"""

    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or '/Users/xujian/Athena工作平台/patent-platform/workspace/data/knowledge'
        self.entities: dict[str, KnowledgeEntity] = {}
        self.triples: dict[str, KnowledgeTriple] = {}
        self.indices: dict[str, set[str] = {}  # 索引
        self.embeddings: dict[str, list[float] = {}  # 向量嵌入

        # 创建存储目录
        Path(self.storage_path).mkdir(parents=True, exist_ok=True)

        # 初始化基础知识
        self._initialize_base_knowledge()

        logger.info(f"📚 专利知识库初始化完成，存储路径: {self.storage_path}")

    def _initialize_base_knowledge(self):
        """初始化基础知识"""
        logger.info('🔄 正在加载基础知识...')

        # 加载专利法律知识
        self._load_patent_law_knowledge()

        # 加载IPC分类知识
        self._load_ipc_classification_knowledge()

        # 加载技术术语知识
        self._load_technical_terminology()

        # 加载技术标准知识
        self._load_technical_standards()

        logger.info('✅ 基础知识加载完成')

    def _load_patent_law_knowledge(self):
        """加载专利法律知识"""
        patent_law_entities = [
            KnowledgeEntity(
                entity_id='patent_law_001',
                name='权利要求',
                type=KnowledgeType.PATENT_LAW,
                definition='确定专利保护范围的核心法律文件，包括独立权利要求和从属权利要求',
                aliases=['claim', '专利权要求', 'patent claim'],
                attributes={'importance': 1.0, 'category': 'core_concept'},
                source=KnowledgeSource.SYSTEM_GENERATED
            ),
            KnowledgeEntity(
                entity_id='patent_law_002',
                name='现有技术',
                type=KnowledgeType.PATENT_LAW,
                definition='申请日之前已经公开的技术信息，用于判断专利新颖性和创造性',
                aliases=['prior art', '背景技术', 'background art'],
                attributes={'importance': 0.9, 'category': 'examination_concept'},
                source=KnowledgeSource.SYSTEM_GENERATED
            ),
            KnowledgeEntity(
                entity_id='patent_law_003',
                name='新颖性',
                type=KnowledgeType.PATENT_LAW,
                definition='发明不属于现有技术的状态，是专利授权的必要条件之一',
                aliases=['novelty', '新创性', 'newness'],
                attributes={'importance': 0.9, 'category': 'examination_criteria'},
                source=KnowledgeSource.SYSTEM_GENERATED
            ),
            KnowledgeEntity(
                entity_id='patent_law_004',
                name='创造性',
                type=KnowledgeType.PATENT_LAW,
                definition='发明与现有技术相比具有突出的实质性特点和显著的进步',
                aliases=['inventive step', '非显而易见性', 'non-obviousness'],
                attributes={'importance': 0.9, 'category': 'examination_criteria'},
                source=KnowledgeSource.SYSTEM_GENERATED
            ),
            KnowledgeEntity(
                entity_id='patent_law_005',
                name='说明书',
                type=KnowledgeType.PATENT_LAW,
                definition='详细描述技术方案的法律文件，用于支持权利要求的保护范围',
                aliases=['specification', '描述', 'description'],
                attributes={'importance': 0.8, 'category': 'patent_document'},
                source=KnowledgeSource.SYSTEM_GENERATED
            ),
            KnowledgeEntity(
                entity_id='patent_law_006',
                name='附图',
                type=KnowledgeType.PATENT_LAW,
                definition='用图形方式展示技术方案的图纸，用于补充说明文字描述',
                aliases=['drawing', '图纸', 'figure', 'diagram'],
                attributes={'importance': 0.8, 'category': 'patent_document'},
                source=KnowledgeSource.SYSTEM_GENERATED
            )
        ]

        # 添加到知识库
        for entity in patent_law_entities:
            self.add_entity(entity)

        # 添加法律关系三元组
        law_triples = [
            KnowledgeTriple(
                triple_id='law_triple_001',
                subject='权利要求',
                predicate='定义',
                object='专利保护范围',
                confidence=0.9,
                source=KnowledgeSource.SYSTEM_GENERATED
            ),
            KnowledgeTriple(
                triple_id='law_triple_002',
                subject='现有技术',
                predicate='用于判断',
                object='新颖性',
                confidence=0.9,
                source=KnowledgeSource.SYSTEM_GENERATED
            ),
            KnowledgeTriple(
                triple_id='law_triple_003',
                subject='创造性',
                predicate='要求',
                object='显著进步',
                confidence=0.8,
                source=KnowledgeSource.SYSTEM_GENERATED
            )
        ]

        for triple in law_triples:
            self.add_triple(triple)

    def _load_ipc_classification_knowledge(self):
        """加载IPC分类知识"""
        ipc_entities = [
            KnowledgeEntity(
                entity_id='ipc_A01',
                name='A01 - 农业；林业；畜牧业；狩猎；诱捕；捕鱼',
                type=KnowledgeType.CLASSIFICATION,
                definition='农业及相关领域的IPC分类',
                aliases=['agriculture', 'forestry', 'animal husbandry'],
                attributes={'section': 'A', 'class': '01', 'level': 'section'},
                source=KnowledgeSource.SYSTEM_GENERATED
            ),
            KnowledgeEntity(
                entity_id='ipc_B23',
                name='B23 - 机床；其他类目不包括的金属加工',
                type=KnowledgeType.CLASSIFICATION,
                definition='机床和金属加工的IPC分类',
                aliases=['machine tools', 'metal working'],
                attributes={'section': 'B', 'class': '23', 'level': 'section'},
                source=KnowledgeSource.SYSTEM_GENERATED
            ),
            KnowledgeEntity(
                entity_id='ipc_G06F',
                name='G06F - 电数字数据处理',
                type=KnowledgeType.CLASSIFICATION,
                definition='计算机和数字数据处理的IPC分类',
                aliases=['digital data processing', 'computing'],
                attributes={'section': 'G', 'class': '06', 'subclass': 'F', 'level': 'subclass'},
                source=KnowledgeSource.SYSTEM_GENERATED
            ),
            KnowledgeEntity(
                entity_id='ipc_H04L',
                name='H04L - 数字信息的传输，例如电报通信',
                type=KnowledgeType.CLASSIFICATION,
                definition='数字通信和信息传输的IPC分类',
                aliases=['digital communication', 'telecommunication'],
                attributes={'section': 'H', 'class': '04', 'subclass': 'L', 'level': 'subclass'},
                source=KnowledgeSource.SYSTEM_GENERATED
            )
        ]

        for entity in ipc_entities:
            self.add_entity(entity)

    def _load_technical_terminology(self):
        """加载技术术语知识"""
        technical_entities = [
            KnowledgeEntity(
                entity_id='tech_term_001',
                name='传感器',
                type=KnowledgeType.TECHNICAL_TERM,
                definition='检测物理量并将其转换为可测量信号的装置',
                aliases=['sensor', '检测器', 'sensing device'],
                attributes={'category': 'component', 'domain': 'electronics'},
                source=KnowledgeSource.SYSTEM_GENERATED
            ),
            KnowledgeEntity(
                entity_id='tech_term_002',
                name='微处理器',
                type=KnowledgeType.TECHNICAL_TERM,
                definition='包含计算机CPU所有功能的单芯片集成电路',
                aliases=['microprocessor', 'CPU', '处理器', 'processor'],
                attributes={'category': 'component', 'domain': 'computer'},
                source=KnowledgeSource.SYSTEM_GENERATED
            ),
            KnowledgeEntity(
                entity_id='tech_term_003',
                name='控制器',
                type=KnowledgeType.TECHNICAL_TERM,
                definition='控制和管理设备运行的电子装置',
                aliases=['controller', '控制单元', 'control unit'],
                attributes={'category': 'component', 'domain': 'automation'},
                source=KnowledgeSource.SYSTEM_GENERATED
            ),
            KnowledgeEntity(
                entity_id='tech_term_004',
                name='精馏塔',
                type=KnowledgeType.TECHNICAL_TERM,
                definition='利用混合物中各组分挥发度不同进行分离的设备',
                aliases=['distillation column', 'fractionating column'],
                attributes={'category': 'equipment', 'domain': 'chemical_engineering'},
                source=KnowledgeSource.SYSTEM_GENERATED
            ),
            KnowledgeEntity(
                entity_id='tech_term_005',
                name='冷凝器',
                type=KnowledgeType.TECHNICAL_TERM,
                definition='将蒸汽冷却凝结为液体的热交换设备',
                aliases=['condenser', '冷却器'],
                attributes={'category': 'equipment', 'domain': 'thermal_engineering'},
                source=KnowledgeSource.SYSTEM_GENERATED
            )
        ]

        for entity in technical_entities:
            self.add_entity(entity)

    def _load_technical_standards(self):
        """加载技术标准知识"""
        standard_entities = [
            KnowledgeEntity(
                entity_id='standard_001',
                name='ISO 9001',
                type=KnowledgeType.TECHNICAL_STANDARD,
                definition='质量管理体系国际标准',
                aliases=['质量管理体系', 'quality management system'],
                attributes={'organization': 'ISO', 'category': 'quality'},
                source=KnowledgeSource.SYSTEM_GENERATED
            ),
            KnowledgeEntity(
                entity_id='standard_002',
                name='GB/T 19001',
                type=KnowledgeType.TECHNICAL_STANDARD,
                definition='中国质量管理体系国家标准，等同于ISO 9001',
                aliases=['中国质量标准', 'GB标准'],
                attributes={'organization': 'GB', 'category': 'quality'},
                source=KnowledgeSource.SYSTEM_GENERATED
            )
        ]

        for entity in standard_entities:
            self.add_entity(entity)

    def add_entity(self, entity: KnowledgeEntity):
        """添加知识实体"""
        self.entities[entity.entity_id] = entity

        # 更新索引
        self._update_entity_index(entity)

        logger.debug(f"📝 添加知识实体: {entity.name}")

    def add_triple(self, triple: KnowledgeTriple):
        """添加知识三元组"""
        self.triples[triple.triple_id] = triple

        # 更新索引
        self._update_triple_index(triple)

        logger.debug(f"🔗 添加知识三元组: {triple.subject} {triple.predicate} {triple.object}")

    def _update_entity_index(self, entity: KnowledgeEntity):
        """更新实体索引"""
        # 名称索引
        name_key = f"name:{entity.name.lower()}"
        if name_key not in self.indices:
            self.indices[name_key] = set()
        self.indices[name_key].add(entity.entity_id)

        # 别名索引
        for alias in entity.aliases:
            alias_key = f"alias:{alias.lower()}"
            if alias_key not in self.indices:
                self.indices[alias_key] = set()
            self.indices[alias_key].add(entity.entity_id)

        # 类型索引
        type_key = f"type:{entity.type.value}"
        if type_key not in self.indices:
            self.indices[type_key] = set()
        self.indices[type_key].add(entity.entity_id)

    def _update_triple_index(self, triple: KnowledgeTriple):
        """更新三元组索引"""
        # 主语索引
        subject_key = f"subject:{triple.subject.lower()}"
        if subject_key not in self.indices:
            self.indices[subject_key] = set()
        self.indices[subject_key].add(triple.triple_id)

        # 宾语索引
        object_key = f"object:{triple.object.lower()}"
        if object_key not in self.indices:
            self.indices[object_key] = set()
        self.indices[object_key].add(triple.triple_id)

        # 谓语索引
        predicate_key = f"predicate:{triple.predicate.lower()}"
        if predicate_key not in self.indices:
            self.indices[predicate_key] = set()
        self.indices[predicate_key].add(triple.triple_id)

    def search_entities(self, query: str, limit: int = 10) -> list[KnowledgeEntity]:
        """搜索知识实体"""
        start_time = datetime.now()
        query_lower = query.lower()

        # 1. 精确匹配
        exact_matches = self._exact_match_entities(query_lower)

        # 2. 模糊匹配
        fuzzy_matches = self._fuzzy_match_entities(query_lower, exclude=exact_matches)

        # 3. 合并结果
        all_matches = exact_matches + fuzzy_matches

        # 4. 按相关性排序
        sorted_matches = self._rank_entities(all_matches, query)

        # 5. 限制结果数量
        results = sorted_matches[:limit]

        # 6. 更新访问统计
        for entity in results:
            entity.access_count += 1
            entity.last_accessed = datetime.now()

        search_time = (datetime.now() - start_time).total_seconds()
        logger.debug(f"🔍 实体搜索完成: 查询='{query}', 找到{len(results)}个结果, 耗时{search_time:.3f}s")

        return results

    def _exact_match_entities(self, query: str) -> list[KnowledgeEntity]:
        """精确匹配实体"""
        matches = []

        # 检查名称匹配
        name_key = f"name:{query}"
        if name_key in self.indices:
            for entity_id in self.indices[name_key]:
                if entity_id in self.entities:
                    matches.append(self.entities[entity_id])

        # 检查别名匹配
        alias_key = f"alias:{query}"
        if alias_key in self.indices:
            for entity_id in self.indices[alias_key]:
                if entity_id in self.entities and self.entities[entity_id] not in matches:
                    matches.append(self.entities[entity_id])

        return matches

    def _fuzzy_match_entities(self, query: str, exclude: list[KnowledgeEntity]) -> list[KnowledgeEntity]:
        """模糊匹配实体"""
        matches = []
        exclude_ids = {e.entity_id for e in exclude}

        # 分词查询
        query_words = re.findall(r'\w+', query)

        for entity in self.entities.values():
            if entity.entity_id in exclude_ids:
                continue

            # 计算匹配分数
            score = 0

            # 名称匹配
            for word in query_words:
                if word in entity.name.lower():
                    score += 2

            # 别名匹配
            for alias in entity.aliases:
                for word in query_words:
                    if word in alias.lower():
                        score += 1

            # 定义匹配
            for word in query_words:
                if word in entity.definition.lower():
                    score += 0.5

            if score > 0:
                # 创建临时副本用于排序
                temp_entity = KnowledgeEntity(
                    entity_id=entity.entity_id,
                    name=entity.name,
                    type=entity.type,
                    definition=entity.definition,
                    confidence=entity.confidence,
                    source=entity.source
                )
                temp_entity.attributes = entity.attributes.copy()
                temp_entity.attributes['_search_score'] = score
                matches.append(temp_entity)

        return matches

    def _rank_entities(self, entities: list[KnowledgeEntity], query: str) -> list[KnowledgeEntity]:
        """对实体进行排序"""
        def sort_key(entity):
            # 综合考虑搜索分数、置信度和访问次数
            search_score = entity.attributes.get('_search_score', 0)
            confidence = entity.confidence
            access_count = entity.access_count

            return (search_score, confidence, access_count)

        return sorted(entities, key=sort_key, reverse=True)

    def search_triples(self, subject: str = None, predicate: str = None, object: str = None) -> list[KnowledgeTriple]:
        """搜索知识三元组"""
        results = []

        for triple in self.triples.values():
            match = True

            if subject and subject.lower() not in triple.subject.lower():
                match = False

            if predicate and predicate.lower() not in triple.predicate.lower():
                match = False

            if object and object.lower() not in triple.object.lower():
                match = False

            if match:
                results.append(triple)

        return results

    def get_related_entities(self, entity_id: str, max_depth: int = 2) -> list[KnowledgeEntity]:
        """获取相关实体"""
        if entity_id not in self.entities:
            return []

        related = set()
        visited = set()
        queue = [(entity_id, 0)]

        while queue:
            current_id, depth = queue.pop(0)

            if current_id in visited or depth >= max_depth:
                continue

            visited.add(current_id)

            # 通过三元组找相关实体
            for triple in self.triples.values():
                if triple.subject == current_id and triple.object not in visited:
                    if triple.object in self.entities:
                        related.add(self.entities[triple.object])
                        queue.append((triple.object, depth + 1))

                elif triple.object == current_id and triple.subject not in visited:
                    if triple.subject in self.entities:
                        related.add(self.entities[triple.subject])
                        queue.append((triple.subject, depth + 1))

        return list(related)

    def save_knowledge_base(self):
        """保存知识库"""
        save_path = Path(self.storage_path)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 保存实体
        entities_file = save_path / f"entities_{timestamp}.json"
        entities_data = {}
        for entity_id, entity in self.entities.items():
            entities_data[entity_id] = {
                'entity_id': entity.entity_id,
                'name': entity.name,
                'type': entity.type.value,
                'definition': entity.definition,
                'aliases': entity.aliases,
                'attributes': entity.attributes,
                'relationships': entity.relationships,
                'confidence': entity.confidence,
                'source': entity.source.value,
                'created_at': entity.created_at.isoformat(),
                'updated_at': entity.updated_at.isoformat(),
                'access_count': entity.access_count,
                'last_accessed': entity.last_accessed.isoformat() if entity.last_accessed else None
            }

        with open(entities_file, 'w', encoding='utf-8') as f:
            json.dump(entities_data, f, ensure_ascii=False, indent=2)

        # 保存三元组
        triples_file = save_path / f"triples_{timestamp}.json"
        triples_data = {}
        for triple_id, triple in self.triples.items():
            triples_data[triple_id] = {
                'triple_id': triple.triple_id,
                'subject': triple.subject,
                'predicate': triple.predicate,
                'object': triple.object,
                'confidence': triple.confidence,
                'source': triple.source.value,
                'evidence': triple.evidence,
                'created_at': triple.created_at.isoformat()
            }

        with open(triples_file, 'w', encoding='utf-8') as f:
            json.dump(triples_data, f, ensure_ascii=False, indent=2)

        logger.info(f"💾 知识库已保存到: {save_path}")

    def load_knowledge_base(self, file_timestamp: str = None):
        """加载知识库"""
        if file_timestamp:
            # 加载指定时间戳的文件
            entities_file = Path(self.storage_path) / f"entities_{file_timestamp}.json"
            triples_file = Path(self.storage_path) / f"triples_{file_timestamp}.json"
        else:
            # 加载最新文件
            entities_files = list(Path(self.storage_path).glob('entities_*.json'))
            triples_files = list(Path(self.storage_path).glob('triples_*.json'))

            if not entities_files or not triples_files:
                logger.warning('⚠️ 没有找到知识库文件')
                return

            entities_file = max(entities_files)
            triples_file = max(triples_files)

        # 加载实体
        with open(entities_file, encoding='utf-8') as f:
            entities_data = json.load(f)

        for entity_data in entities_data.values():
            entity = KnowledgeEntity(
                entity_id=entity_data['entity_id'],
                name=entity_data['name'],
                type=KnowledgeType(entity_data['type']),
                definition=entity_data['definition'],
                aliases=entity_data['aliases'],
                attributes=entity_data['attributes'],
                relationships=entity_data['relationships'],
                confidence=entity_data['confidence'],
                source=KnowledgeSource(entity_data['source']),
                created_at=datetime.fromisoformat(entity_data['created_at']),
                updated_at=datetime.fromisoformat(entity_data['updated_at']),
                access_count=entity_data['access_count'],
                last_accessed=datetime.fromisoformat(entity_data['last_accessed']) if entity_data['last_accessed'] else None
            )
            self.entities[entity.entity_id] = entity
            self._update_entity_index(entity)

        # 加载三元组
        with open(triples_file, encoding='utf-8') as f:
            triples_data = json.load(f)

        for triple_data in triples_data.values():
            triple = KnowledgeTriple(
                triple_id=triple_data['triple_id'],
                subject=triple_data['subject'],
                predicate=triple_data['predicate'],
                object=triple_data['object'],
                confidence=triple_data['confidence'],
                source=KnowledgeSource(triple_data['source']),
                evidence=triple_data['evidence'],
                created_at=datetime.fromisoformat(triple_data['created_at'])
            )
            self.triples[triple.triple_id] = triple
            self._update_triple_index(triple)

        logger.info(f"📚 知识库加载完成: {len(self.entities)}个实体, {len(self.triples)}个三元组")

class DynamicKnowledgeInjector:
    """动态知识注入器"""

    def __init__(self, knowledge_base: PatentKnowledgeBase):
        self.knowledge_base = knowledge_base
        self.injection_history = []
        self.confidence_threshold = 0.7

    async def inject_knowledge(self, content: str, context: dict[str, Any] = None) -> list[KnowledgeEntity]:
        """向内容中注入知识"""
        start_time = datetime.now()
        injected_entities = []

        logger.info(f"💉 开始知识注入，内容长度: {len(content)}")

        try:
            # 1. 识别技术术语
            technical_terms = self._identify_technical_terms(content)

            # 2. 识别法律术语
            legal_terms = self._identify_legal_terms(content)

            # 3. 识别分类号
            classifications = self._identify_classifications(content)

            # 4. 查找相关知识实体
            all_terms = technical_terms + legal_terms + classifications
            for term in all_terms:
                entities = self.knowledge_base.search_entities(term, limit=3)
                injected_entities.extend(entities)

            # 5. 去重
            injected_entities = self._deduplicate_entities(injected_entities)

            # 6. 记录注入历史
            injection_record = {
                'timestamp': start_time,
                'content_length': len(content),
                'injected_count': len(injected_entities),
                'context': context
            }
            self.injection_history.append(injection_record)

            injection_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ 知识注入完成，注入{len(injected_entities)}个实体，耗时{injection_time:.3f}s")

            return injected_entities

        except Exception as e:
            logger.error(f"❌ 知识注入失败: {str(e)}")
            return []

    def _identify_technical_terms(self, content: str) -> list[str]:
        """识别技术术语"""
        # 使用正则表达式识别技术术语
        term_patterns = [
            r'[A-Z]{2,}(?:[A-Z][a-z]+)*',  # 技术缩写 (CPU, GPU, LED等)
            r'[^，。；；]*?装置[^，。；；]*',  # 装置类术语
            r'[^，。；；]*?传感器[^，。；；]*',  # 传感器类术语
            r'[^，。；；]*?控制器[^，。；；]*',  # 控制器类术语
            r'[^，。；；]*?发动机[^，。；；]*',  # 发动机类术语
        ]

        terms = set()
        for pattern in term_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                # 清理匹配结果
                cleaned_match = match.strip()
                if len(cleaned_match) > 2 and len(cleaned_match) < 50:
                    terms.add(cleaned_match)

        return list(terms)

    def _identify_legal_terms(self, content: str) -> list[str]:
        """识别法律术语"""
        legal_term_patterns = [
            r'权利要求\s*\d+',
            r'现有技术',
            r'新颖性',
            r'创造性',
            r'说明书',
            r'附图\s*\d+',
            r'实施例',
            r'技术方案',
            r'背景技术',
            r'发明内容'
        ]

        terms = set()
        for pattern in legal_term_patterns:
            matches = re.findall(pattern, content)
            terms.update(matches)

        return list(terms)

    def _identify_classifications(self, content: str) -> list[str]:
        """识别分类号"""
        classification_patterns = [
            r'[A-H]\d{2}[A-Z]\d{1,2}',  # IPC分类号格式
            r'G06F',                   # 常见分类号
            r'H04L',                   # 常见分类号
            r'B23',                    # 常见分类号
        ]

        terms = set()
        for pattern in classification_patterns:
            matches = re.findall(pattern, content)
            terms.update(matches)

        return list(terms)

    def _deduplicate_entities(self, entities: list[KnowledgeEntity]) -> list[KnowledgeEntity]:
        """去重知识实体"""
        seen = set()
        deduplicated = []

        for entity in entities:
            key = (entity.name, entity.type)
            if key not in seen:
                seen.add(key)
                deduplicated.append(entity)

        return deduplicated

    def get_injection_statistics(self) -> dict[str, Any]:
        """获取注入统计信息"""
        if not self.injection_history:
            return {'total_injections': 0}

        total_injections = len(self.injection_history)
        total_entities = sum(record['injected_count'] for record in self.injection_history)
        avg_entities_per_injection = total_entities / total_injections

        return {
            'total_injections': total_injections,
            'total_entities_injected': total_entities,
            'avg_entities_per_injection': avg_entities_per_injection,
            'last_injection': self.injection_history[-1]['timestamp'] if self.injection_history else None
        }

# RAG系统实现
class RAGSystem:
    """检索增强生成系统"""

    def __init__(self, knowledge_base: PatentKnowledgeBase):
        self.knowledge_base = knowledge_base
        self.injection_engine = DynamicKnowledgeInjector(knowledge_base)
        self.retrieval_history = []

    async def retrieve_and_generate(self, query: str, context: dict[str, Any] = None) -> RetrievalResult:
        """检索并生成结果"""
        start_time = datetime.now()

        logger.info(f"🔍 开始RAG检索: {query}")

        # 1. 检索知识实体
        entities = self.knowledge_base.search_entities(query, limit=10)

        # 2. 检索知识三元组
        triples = self.knowledge_base.search_triples(subject=query)

        # 3. 动态知识注入
        if context and 'content' in context:
            injected_entities = await self.injection_engine.inject_knowledge(
                context['content'], context
            )
            entities.extend(injected_entities)

        # 4. 计算相关性分数
        relevance_scores = self._calculate_relevance_scores(entities, triples, query)

        # 5. 创建检索结果
        query_time = (datetime.now() - start_time).total_seconds()
        result = RetrievalResult(
            query=query,
            retrieved_entities=entities,
            retrieved_triples=triples,
            relevance_scores=relevance_scores,
            retrieval_method='hybrid_search',
            total_results=len(entities) + len(triples),
            query_time=query_time
        )

        # 6. 记录检索历史
        self.retrieval_history.append({
            'timestamp': start_time,
            'query': query,
            'result_count': result.total_results,
            'query_time': query_time
        })

        logger.info(f"✅ RAG检索完成: {result.total_results}个结果, 耗时{query_time:.3f}s")

        return result

    def _calculate_relevance_scores(self, entities: list[KnowledgeEntity], triples: list[KnowledgeTriple], query: str) -> list[float]:
        """计算相关性分数"""
        scores = []

        # 实体相关性分数
        for entity in entities:
            score = 0.0

            # 名称匹配
            if query.lower() in entity.name.lower():
                score += 2.0

            # 别名匹配
            for alias in entity.aliases:
                if query.lower() in alias.lower():
                    score += 1.5

            # 定义匹配
            query_words = re.findall(r'\w+', query.lower())
            definition_words = re.findall(r'\w+', entity.definition.lower())
            overlap = len(set(query_words).intersection(set(definition_words)))
            score += overlap * 0.1

            # 置信度加权
            score *= entity.confidence

            scores.append(score)

        # 三元组相关性分数
        for triple in triples:
            score = 0.0

            if query.lower() in triple.subject.lower():
                score += 1.0

            if query.lower() in triple.object.lower():
                score += 1.0

            if query.lower() in triple.predicate.lower():
                score += 0.5

            # 置信度加权
            score *= triple.confidence

            scores.append(score)

        return scores

# 测试代码
if __name__ == '__main__':
    async def test_domain_knowledge():
        """测试领域知识系统"""
        logger.info('📚 测试领域知识引擎...')

        # 初始化知识库
        kb = PatentKnowledgeBase()

        # 测试实体搜索
        logger.info("\n🔍 测试实体搜索:")
        results = kb.search_entities('权利要求', limit=3)
        for entity in results:
            logger.info(f"  实体: {entity.name}")
            logger.info(f"  定义: {entity.definition}")
            logger.info(f"  置信度: {entity.confidence}")

        # 测试三元组搜索
        logger.info("\n🔗 测试三元组搜索:")
        triples = kb.search_triples(subject='权利要求')
        for triple in triples:
            logger.info(f"  {triple.subject} {triple.predicate} {triple.object}")

        # 测试知识注入
        logger.info("\n💉 测试知识注入:")
        injector = DynamicKnowledgeInjector(kb)
        test_content = '本实用新型涉及一种精馏装置，包括传感器和微处理器，符合权利要求1所述的技术方案。'
        injected = await injector.inject_knowledge(test_content)
        logger.info(f"  注入了{len(injected)}个相关知识实体")

        # 测试RAG系统
        logger.info("\n🤖 测试RAG系统:")
        rag = RAGSystem(kb)
        rag_result = await rag.retrieve_and_generate(
            '精馏装置',
            {'content': test_content}
        )
        logger.info(f"  检索结果: {rag_result.total_results}个")
        logger.info(f"  查询时间: {rag_result.query_time:.3f}s")

        # 显示统计信息
        logger.info("\n📊 统计信息:")
        injection_stats = injector.get_injection_statistics()
        logger.info(f"  注入统计: {injection_stats}")

    # 运行测试
    asyncio.run(test_domain_knowledge())
