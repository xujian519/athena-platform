#!/usr/bin/env python3
"""
专利规则构建系统 - BERT实体关系提取器
Patent Rules Builder - BERT Entity Relation Extractor

使用BERT模型提取专利法律文本中的实体和关系，支持2025年修改内容

作者: Athena平台团队
创建时间: 2025-12-20
版本: v2.0.0
"""

from __future__ import annotations
import asyncio
import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 使用本地NLP系统
try:
    import sys
    sys.path.append("/Users/xujian/Athena工作平台/production/dev/scripts")
    from nlp_adapter_professional import NLPAdapter
    NLP_AVAILABLE = True
    logger.info("✅ 使用本地NLP系统")
except ImportError:
    NLP_AVAILABLE = False
    logger.warning("本地NLP系统不可用")

# 中文分词
try:
    import jieba
    import jieba.posseg as pseg
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EntityType(Enum):
    """实体类型"""
    # 法律条文
    LAW_ARTICLE = "法律条文"
    LAW_SECTION = "法条条款"

    # 审查指南
    GUIDELINE_PART = "指南部分"
    GUIDELINE_CHAPTER = "指南章节"
    GUIDELINE_SECTION = "指南节"
    GUIDELINE_SUBSECTION = "指南小节"
    GUIDELINE_EXAMPLE = "指南案例"
    GUIDELINE_NOTE = "指南注释"

    # 司法解释
    JUDICIAL_INTERPRETATION = "司法解释"
    INTERPRETATION_RULE = "解释规则"
    CASE_REFERENCE = "案例引用"

    # 2025修改
    MODIFICATION_2025 = "2025年修改"
    NEW_SECTION = "新增章节"
    DELETED_SECTION = "删除章节"
    AI_SECTION = "AI相关章节"
    BITSTREAM_SECTION = "比特流章节"

    # 概念实体
    CONCEPT = "概念"
    DEFINITION = "定义"
    TERM = "术语"
    CONDITION = "条件"
    EXCEPTION = "例外"
    REQUIREMENT = "要求"
    PROCEDURE = "程序"
    STANDARD = "标准"
    CRITERION = "标准"
    EXAMPLE_CASE = "案例示例"
    PRIOR_ART = "现有技术"
    TECH_FEATURE = "技术特征"
    APPLICATION_FIELD = "应用领域"

    # 特殊实体
    INVENTION = "发明"
    UTILITY_MODEL = "实用新型"
    DESIGN = "外观设计"
    PATENT_RIGHT = "专利权"
    INFRINGEMENT = "侵权"
    LICENSING = "许可"
    ASSIGNMENT = "转让"

class RelationType(Enum):
    """关系类型"""
    # 结构关系
    HAS_PART = "包含部分"
    HAS_CHAPTER = "包含章"
    HAS_SECTION = "包含节"
    HAS_SUBSECTION = "包含小节"
    CONTAINS = "包含"

    # 引用关系
    REFERENCES = "引用"
    CITES = "引用"
    ACCORDING_TO = "根据"
    BASED_ON = "基于"
    IN_ACCORDANCE_WITH = "依据"

    # 解释关系
    INTERPRETS = "解释"
    CLARIFIES = "澄清"
    ILLUSTRATES = "说明"
    EXAMPLES = "举例"

    # 逻辑关系
    DEFINES = "定义"
    IS_DEFINED_AS = "被定义为"
    APPLIES_TO = "适用于"
    DOES_NOT_APPLY_TO = "不适用于"
    CONDITION_FOR = "是...的条件"
    EXCEPTION_TO = "是...的例外"
    REQUIRES = "要求"
    PROHIBITS = "禁止"
    PERMITS = "允许"

    # 比较关系
    RELATED_TO = "相关于"
    SIMILAR_TO = "类似于"
    DIFFERENT_FROM = "区别于"
    OPPOSITE_OF = "相反于"
    SUPERIOR_TO = "优于"
    INFERIOR_TO = "劣于"

    # 时间关系
    MODIFIED_BY = "被修改为"
    REPLACES = "替代"
    SUPERSEDES = "废止"
    PRECEDES = "先于"
    SUCCEEDS = "后于"

    # 2025特殊关系
    INTRODUCED_2025 = "2025年引入"
    AMENDED_2025 = "2025年修订"
    DELETED_2025 = "2025年删除"
    AI_RELATED = "AI相关"
    BITSTREAM_RELATED = "比特流相关"

@dataclass
class Entity:
    """实体数据结构"""
    entity_id: str
    entity_type: EntityType
    entity_text: str
    start_pos: int
    end_pos: int
    confidence: float
    context: str
    extraction_method: str
    properties: dict = None

@dataclass
class Relation:
    """关系数据结构"""
    relation_id: str
    source_entity_id: str
    target_entity_id: str
    relation_type: RelationType
    confidence: float
    evidence: str
    extraction_method: str

@dataclass
class ExtractionResult:
    """提取结果"""
    doc_id: str
    entities: list[Entity]
    relations: list[Relation]
    processing_time: float
    model_used: str
    statistics: dict

class BERTEntityExtractor:
    """基于本地NLP系统的实体提取器"""

    def __init__(self, model_name: str = "patent_bert"):
        self.model_name = model_name
        self.nlp_adapter = None

        # 专利领域特定词汇
        self.patent_terms = self._load_patent_terms()

        # 初始化NLP适配器
        self._initialize_nlp_adapter()

    def _load_patent_terms(self) -> dict:
        """加载专利领域术语"""
        return {
            "invention_terms": [
                "发明", "实用新型", "外观设计", "专利申请", "专利权",
                "权利要求", "说明书", "摘要", "附图", "优先权"
            ],
            "legal_terms": [
                "专利法", "实施细则", "审查指南", "司法解释", "条例",
                "办法", "规定", "决定", "公告", "通知"
            ],
            "procedure_terms": [
                "申请", "审查", "授权", "公告", "无效", "复审",
                "异议", "诉讼", "执行", "许可", "转让"
            ],
            "criteria_terms": [
                "新颖性", "创造性", "实用性", "公开充分", "清楚完整",
                "支持", "单一性", "修改超范围"
            ],
            "ai_terms_2025": [
                "人工智能", "AI", "算法", "模型", "数据", "训练",
                "深度学习", "机器学习", "神经网络", "比特流"
            ],
            "biotech_terms_2025": [
                "基因", "基因编辑", "CRISPR", "生物序列", "蛋白质",
                "细胞", "组织", "器官", "医疗方法"
            ]
        }

    def _initialize_nlp_adapter(self) -> Any:
        """初始化NLP适配器"""
        if not NLP_AVAILABLE:
            logger.warning("NLP系统不可用，将使用规则方法")
            return

        try:
            logger.info("初始化本地NLP适配器...")
            self.nlp_adapter = NLPAdapter()
            logger.info("✅ NLP适配器初始化成功")
        except Exception as e:
            logger.error(f"❌ NLP适配器初始化失败: {e}")
            self.nlp_adapter = None

    async def extract_entities(self, text: str, doc_id: str = "") -> list[Entity]:
        """提取实体"""
        entities = []

        # 方法1: 使用本地NLP系统
        if self.nlp_adapter:
            nlp_entities = await self._extract_with_nlp(text, doc_id)
            entities.extend(nlp_entities)

        # 方法2: 使用规则方法（补充）
        rule_entities = self._extract_with_rules(text, doc_id)
        entities.extend(rule_entities)

        # 去重和合并
        entities = self._merge_entities(entities)

        # 分配ID
        for i, entity in enumerate(entities):
            entity.entity_id = f"{doc_id}_entity_{i:04d}"

        return entities

    async def _extract_with_nlp(self, text: str, doc_id: str) -> list[Entity]:
        """使用本地NLP系统提取实体"""
        entities = []

        try:
            # 使用NLP适配器提取实体
            nlp_entities = await self.nlp_adapter.extract_entities(text)

            for nlp_entity in nlp_entities:
                # 映射到我们的实体类型
                entity_type = self._map_nlp_entity_type(nlp_entity.get('type', ''))

                if entity_type:
                    entity_text = nlp_entity.get('text', '')
                    start_pos = nlp_entity.get('start', 0)
                    end_pos = nlp_entity.get('end', len(entity_text))
                    confidence = nlp_entity.get('confidence', 0.8)

                    # 获取上下文
                    context_start = max(0, start_pos - 50)
                    context_end = min(len(text), end_pos + 50)
                    context = text[context_start:context_end]

                    entity = Entity(
                        entity_id="",  # 稍后分配
                        entity_type=entity_type,
                        entity_text=entity_text,
                        start_pos=start_pos,
                        end_pos=end_pos,
                        confidence=confidence,
                        context=context,
                        extraction_method="nlp_adapter",
                        properties=nlp_entity
                    )
                    entities.append(entity)

        except Exception as e:
            logger.error(f"NLP实体提取失败: {e}")

        return entities

    def _map_nlp_entity_type(self, nlp_type: str) -> EntityType | None:
        """将NLP系统实体类型映射到我们的类型"""
        type_mapping = {
            '法律条文': EntityType.LAW_ARTICLE,
            '法条条款': EntityType.LAW_SECTION,
            '指南章节': EntityType.GUIDELINE_CHAPTER,
            '指南节': EntityType.GUIDELINE_SECTION,
            '指南小节': EntityType.GUIDELINE_SUBSECTION,
            '司法解释': EntityType.JUDICIAL_INTERPRETATION,
            '概念': EntityType.CONCEPT,
            '定义': EntityType.DEFINITION,
            '术语': EntityType.TERM,
            '条件': EntityType.CONDITION,
            '要求': EntityType.REQUIREMENT,
            '标准': EntityType.STANDARD,
            '发明': EntityType.INVENTION,
            '实用新型': EntityType.UTILITY_MODEL,
            '外观设计': EntityType.DESIGN,
            '专利权': EntityType.PATENT_RIGHT,
        }

        # 处理2025年修改相关
        if '2025' in nlp_type or 'AI' in nlp_type:
            return EntityType.MODIFICATION_2025

        return type_mapping.get(nlp_type, None)

    def _extract_with_rules(self, text: str, doc_id: str) -> list[Entity]:
        """使用规则方法提取实体"""
        entities = []

        # 提取各种类型的实体
        entities.extend(self._extract_law_articles(text, doc_id))
        entities.extend(self._extract_patent_terms(text, doc_id))
        entities.extend(self._extract_2025_modifications(text, doc_id))
        entities.extend(self._extract_conditions_and_standards(text, doc_id))

        return entities

    def _extract_law_articles(self, text: str, doc_id: str) -> list[Entity]:
        """提取法律条文"""
        entities = []

        # 法律条文模式
        patterns = [
            r'(第[一二三四五六七八九十\d]+条)',
            r'(第[一二三四五六七八九十\d]+章)',
            r'(第[一二三四五六七八九十\d]+节)',
            r'(第[一二三四五六七八九十\d]+部分)',
            r'(\d+\.\d+)',
            r'(\d+\.\d+\.\d+)'
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, text):
                entity_text = match.group(1)
                start_pos = match.start()
                end_pos = match.end()

                # 判断条文类型
                if "章" in entity_text:
                    entity_type = EntityType.GUIDELINE_CHAPTER
                elif "节" in entity_text:
                    entity_type = EntityType.GUIDELINE_SECTION
                elif "部分" in entity_text:
                    entity_type = EntityType.GUIDELINE_PART
                elif "条" in entity_text:
                    entity_type = EntityType.LAW_ARTICLE
                elif re.match(r'\d+\.\d+\.\d+', entity_text):
                    entity_type = EntityType.GUIDELINE_SUBSECTION
                else:
                    entity_type = EntityType.GUIDELINE_SECTION

                context = text[max(0, start_pos-30):start_pos] + entity_text + \
                         text[end_pos:min(len(text), end_pos+30)]

                entity = Entity(
                    entity_id="",
                    entity_type=entity_type,
                    entity_text=entity_text,
                    start_pos=start_pos,
                    end_pos=end_pos,
                    confidence=0.9,  # 规则方法置信度高
                    context=context,
                    extraction_method="rule_pattern",
                    properties={"pattern": pattern}
                )
                entities.append(entity)

        return entities

    def _extract_patent_terms(self, text: str, doc_id: str) -> list[Entity]:
        """提取专利术语"""
        entities = []

        # 遍历专利术语词典
        for category, terms in self.patent_terms.items():
            for term in terms:
                # 查找术语的所有出现位置
                for match in re.finditer(re.escape(term), text):
                    start_pos = match.start()
                    end_pos = match.end()

                    # 避免重复提取
                    if any(e.start_pos <= start_pos and e.end_pos >= end_pos
                          for e in entities):
                        continue

                    # 确定实体类型
                    if category == "ai_terms_2025":
                        entity_type = EntityType.AI_SECTION
                    elif category == "biotech_terms_2025":
                        entity_type = EntityType.BITSTREAM_SECTION
                    elif category == "legal_terms":
                        entity_type = EntityType.TERM
                    else:
                        entity_type = EntityType.CONCEPT

                    context = text[max(0, start_pos-20):start_pos] + term + \
                             text[end_pos:min(len(text), end_pos+20)]

                    entity = Entity(
                        entity_id="",
                        entity_type=entity_type,
                        entity_text=term,
                        start_pos=start_pos,
                        end_pos=end_pos,
                        confidence=0.85,
                        context=context,
                        extraction_method="rule_dictionary",
                        properties={"category": category}
                    )
                    entities.append(entity)

        return entities

    def _extract_2025_modifications(self, text: str, doc_id: str) -> list[Entity]:
        """提取2025年修改相关实体"""
        entities = []

        # 2025年修改关键词
        modification_keywords = [
            "2025年修改", "二零二五年", "新增", "删除", "修订", "调整",
            "AI相关", "人工智能", "大数据", "比特流", "基因编辑"
        ]

        for keyword in modification_keywords:
            for match in re.finditer(re.escape(keyword), text):
                start_pos = match.start()
                end_pos = match.end()

                context = text[max(0, start_pos-30):start_pos] + keyword + \
                         text[end_pos:min(len(text), end_pos+30)]

                entity_type = EntityType.MODIFICATION_2025
                if "AI" in keyword or "人工智能" in keyword:
                    entity_type = EntityType.AI_SECTION
                elif "比特流" in keyword:
                    entity_type = EntityType.BITSTREAM_SECTION
                elif "新增" in keyword:
                    entity_type = EntityType.NEW_SECTION
                elif "删除" in keyword:
                    entity_type = EntityType.DELETED_SECTION

                entity = Entity(
                    entity_id="",
                    entity_type=entity_type,
                    entity_text=keyword,
                    start_pos=start_pos,
                    end_pos=end_pos,
                    confidence=0.8,
                    context=context,
                    extraction_method="rule_2025_modification"
                )
                entities.append(entity)

        return entities

    def _extract_conditions_and_standards(self, text: str, doc_id: str) -> list[Entity]:
        """提取条件和标准"""
        entities = []

        # 条件模式
        condition_patterns = [
            r'(应当[：:\s]*[^。；;]*)',
            r'(必须[：:\s]*[^。；;]*)',
            r'(可以[：:\s]*[^。；;]*)',
            r'(不得[：:\s]*[^。；;]*)',
            r'(需要[：:\s]*[^。；;]*)'
        ]

        for pattern in condition_patterns:
            for match in re.finditer(pattern, text):
                entity_text = match.group(1)
                if len(entity_text) > 100:  # 避免过长的匹配
                    continue

                start_pos = match.start()
                end_pos = match.end()

                if "应当" in entity_text or "必须" in entity_text:
                    entity_type = EntityType.REQUIREMENT
                elif "不得" in entity_text:
                    entity_type = EntityType.PROHIBITS
                else:
                    entity_type = EntityType.CONDITION

                entity = Entity(
                    entity_id="",
                    entity_type=entity_type,
                    entity_text=entity_text,
                    start_pos=start_pos,
                    end_pos=end_pos,
                    confidence=0.75,
                    context=entity_text,
                    extraction_method="rule_condition"
                )
                entities.append(entity)

        return entities

    def _merge_entities(self, entities: list[Entity]) -> list[Entity]:
        """合并和去重实体"""
        if not entities:
            return entities

        # 按位置排序
        entities.sort(key=lambda e: e.start_pos)

        merged = []
        current = entities[0]

        for next_entity in entities[1:]:
            # 检查是否重叠
            if (next_entity.start_pos < current.end_pos and
                next_entity.entity_type == current.entity_type):
                # 合并实体
                current.end_pos = max(current.end_pos, next_entity.end_pos)
                current.entity_text = text = current.context  # 使用原始文本
                current.confidence = max(current.confidence, next_entity.confidence)
            else:
                merged.append(current)
                current = next_entity

        merged.append(current)
        return merged

class BERTRelationExtractor:
    """基于本地NLP系统的关系提取器"""

    def __init__(self, model_name: str = "patent_bert"):
        self.model_name = model_name
        self.nlp_adapter = None

        # 关系关键词模式
        self.relation_patterns = self._load_relation_patterns()

        # 初始化NLP适配器
        self._initialize_nlp_adapter()

    def _load_relation_patterns(self) -> dict:
        """加载关系模式"""
        return {
            RelationType.REFERENCES: [
                r'根据([^.。]*?)[,.，。]',
                r'依据([^.。]*?)[,.，。]',
                r'按照([^.。]*?)[,.，。]'
            ],
            RelationType.DEFINES: [
                r'([^.。]*?)是指([^.。]*?)[,.，。]',
                r'([^.。]*?)指的是([^.。]*?)[,.，。]',
                r'定义为([^.。]*?)[,.，。]'
            ],
            RelationType.APPLIES_TO: [
                r'适用于([^.。]*?)[,.，。]',
                r'应用于([^.。]*?)[,.，。]',
                r'针对([^.。]*?)[,.，。]'
            ],
            RelationType.EXCEPTION_TO: [
                r'除了([^.。]*?)以外',
                r'([^.。]*?)除外',
                r'不适用于([^.。]*?)[,.，。]'
            ],
            RelationType.REQUIRES: [
                r'应当([^.。]*?)[,.，。]',
                r'必须([^.。]*?)[,.，。]',
                r'需要([^.。]*?)[,.，。]'
            ],
            RelationType.PROHIBITS: [
                r'不得([^.。]*?)[,.，。]',
                r'禁止([^.。]*?)[,.，。]',
                r'不允许([^.。]*?)[,.，。]'
            ],
            RelationType.INTRODUCED_2025: [
                r'2025年新增([^.。]*?)[,.，。]',
                r'新增加([^.。]*?)[,.，。]'
            ],
            RelationType.MODIFIED_BY: [
                r'2025年修订([^.。]*?)[,.，。]',
                r'修改为([^.。]*?)[,.，。]'
            ]
        }

    def _initialize_nlp_adapter(self) -> Any:
        """初始化NLP适配器"""
        if not NLP_AVAILABLE:
            logger.warning("NLP系统不可用，将使用规则方法")
            return

        try:
            logger.info("初始化本地NLP适配器...")
            self.nlp_adapter = NLPAdapter()
            logger.info("✅ NLP适配器初始化成功")
        except Exception as e:
            logger.error(f"❌ NLP适配器初始化失败: {e}")
            self.nlp_adapter = None

    async def extract_relations(self, text: str, entities: list[Entity]) -> list[Relation]:
        """提取关系"""
        relations = []

        # 方法1: 使用本地NLP系统
        if self.nlp_adapter:
            nlp_relations = await self._extract_with_nlp(text, entities)
            relations.extend(nlp_relations)

        # 方法2: 使用规则方法
        rule_relations = self._extract_with_rules(text, entities)
        relations.extend(rule_relations)

        # 方法3: 使用共现关系
        cooccurrence_relations = self._extract_cooccurrence_relations(text, entities)
        relations.extend(cooccurrence_relations)

        # 去重
        relations = self._deduplicate_relations(relations)

        # 分配ID
        for i, relation in enumerate(relations):
            relation.relation_id = f"relation_{i:04d}"

        return relations

    def _extract_with_rules(self, text: str, entities: list[Entity]) -> list[Relation]:
        """使用规则提取关系"""
        relations = []

        # 遍历所有关系模式
        for relation_type, patterns in self.relation_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text)

                for match in matches:
                    # 找到关系涉及的两个实体
                    relation_text = match.group(0)

                    # 查找最近的实体
                    source_entity = self._find_nearest_entity(
                        entities, match.start(), direction="before"
                    )
                    target_entity = self._find_nearest_entity(
                        entities, match.end(), direction="after"
                    )

                    if source_entity and target_entity:
                        relation = Relation(
                            relation_id="",
                            source_entity_id=source_entity.entity_id,
                            target_entity_id=target_entity.entity_id,
                            relation_type=relation_type,
                            confidence=0.8,
                            evidence=relation_text,
                            extraction_method="rule_pattern"
                        )
                        relations.append(relation)

        return relations

    def _extract_cooccurrence_relations(self, text: str, entities: list[Entity]) -> list[Relation]:
        """提取共现关系"""
        relations = []

        # 在同一句话中的实体可能存在关系
        sentences = re.split(r'[。；;!]', text)

        for sentence in sentences:
            sentence_entities = []
            sentence_start = text.find(sentence)

            # 找出句子中的实体
            for entity in entities:
                if (entity.start_pos >= sentence_start and
                    entity.end_pos <= sentence_start + len(sentence)):
                    sentence_entities.append(entity)

            # 创建实体对的关系
            for i, entity1 in enumerate(sentence_entities):
                for entity2 in sentence_entities[i+1:]:
                    # 判断关系类型
                    relation_type = self._infer_relation_type(entity1, entity2, sentence)

                    if relation_type:
                        relation = Relation(
                            relation_id="",
                            source_entity_id=entity1.entity_id,
                            target_entity_id=entity2.entity_id,
                            relation_type=relation_type,
                            confidence=0.6,  # 共现关系置信度较低
                            evidence=sentence,
                            extraction_method="cooccurrence"
                        )
                        relations.append(relation)

        return relations

    def _find_nearest_entity(self, entities: list[Entity], position: int,
                           direction: str = "after") -> Entity | None:
        """查找最近的实体"""
        nearest = None
        min_distance = float('inf')

        for entity in entities:
            if direction == "before":
                distance = position - entity.end_pos
                if distance > 0 and distance < min_distance:
                    min_distance = distance
                    nearest = entity
            else:  # after
                distance = entity.start_pos - position
                if distance > 0 and distance < min_distance:
                    min_distance = distance
                    nearest = entity

        return nearest

    def _infer_relation_type(self, entity1: Entity, entity2: Entity,
                           context: str) -> RelationType | None:
        """推断关系类型"""
        # 章节关系
        if (entity1.entity_type == EntityType.GUIDELINE_CHAPTER and
            entity2.entity_type in [EntityType.GUIDELINE_SECTION, EntityType.LAW_ARTICLE]):
            return RelationType.HAS_SECTION

        # 法条与概念
        if entity1.entity_type == EntityType.LAW_ARTICLE:
            if entity2.entity_type == EntityType.DEFINITION:
                return RelationType.DEFINES
            elif entity2.entity_type in [EntityType.REQUIREMENT, EntityType.CONDITION]:
                return RelationType.REQUIRES

        # 2025修改
        if entity1.entity_type == EntityType.MODIFICATION_2025:
            if entity2.entity_type in [EntityType.NEW_SECTION, EntityType.AI_SECTION]:
                return RelationType.INTRODUCED_2025

        # 默认返回相关关系
        return RelationType.RELATED_TO

    def _deduplicate_relations(self, relations: list[Relation]) -> list[Relation]:
        """去重关系"""
        seen = set()
        deduplicated = []

        for relation in relations:
            key = (
                relation.source_entity_id,
                relation.target_entity_id,
                relation.relation_type
            )

            if key not in seen:
                seen.add(key)
                deduplicated.append(relation)

        return deduplicated

class BERTEntityRelationExtractor:
    """BERT实体关系联合提取器"""

    def __init__(self, model_name: str = "bert-base-chinese"):
        self.entity_extractor = BERTEntityExtractor(model_name)
        self.relation_extractor = BERTRelationExtractor(model_name)

        # 统计信息
        self.stats = {
            "documents_processed": 0,
            "total_entities": 0,
            "total_relations": 0,
            "entity_types": {},
            "relation_types": {},
            "processing_time": 0
        }

    async def extract(self, text: str, doc_id: str = "") -> ExtractionResult:
        """联合提取实体和关系"""
        import time
        start_time = time.time()

        # 提取实体
        entities = self.entity_extractor.extract_entities(text, doc_id)

        # 提取关系
        relations = self.relation_extractor.extract_relations(text, entities)

        processing_time = time.time() - start_time

        # 更新统计
        self.stats["documents_processed"] += 1
        self.stats["total_entities"] += len(entities)
        self.stats["total_relations"] += len(relations)
        self.stats["processing_time"] += processing_time

        # 统计类型分布
        for entity in entities:
            entity_type = entity.entity_type.value
            self.stats["entity_types"][entity_type] = \
                self.stats["entity_types"].get(entity_type, 0) + 1

        for relation in relations:
            relation_type = relation.relation_type.value
            self.stats["relation_types"][relation_type] = \
                self.stats["relation_types"].get(relation_type, 0) + 1

        # 生成统计信息
        statistics = {
            "entity_count": len(entities),
            "relation_count": len(relations),
            "entity_type_distribution": self._count_entity_types(entities),
            "relation_type_distribution": self._count_relation_types(relations),
            "avg_entity_confidence": np.mean([e.confidence for e in entities]) if entities else 0,
            "avg_relation_confidence": np.mean([r.confidence for r in relations]) if relations else 0
        }

        result = ExtractionResult(
            doc_id=doc_id,
            entities=entities,
            relations=relations,
            processing_time=processing_time,
            model_used=self.entity_extractor.model_name,
            statistics=statistics
        )

        return result

    def _count_entity_types(self, entities: list[Entity]) -> dict:
        """统计实体类型分布"""
        type_counts = {}
        for entity in entities:
            type_name = entity.entity_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        return type_counts

    def _count_relation_types(self, relations: list[Relation]) -> dict:
        """统计关系类型分布"""
        type_counts = {}
        for relation in relations:
            type_name = relation.relation_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        return type_counts

    def get_statistics(self) -> dict:
        """获取统计信息"""
        if self.stats["documents_processed"] > 0:
            return {
                **self.stats,
                "avg_entities_per_doc": self.stats["total_entities"] / self.stats["documents_processed"],
                "avg_relations_per_doc": self.stats["total_relations"] / self.stats["documents_processed"],
                "avg_processing_time": self.stats["processing_time"] / self.stats["documents_processed"]
            }
        return self.stats

# 使用示例
async def main():
    """主函数示例"""
    extractor = BERTEntityRelationExtractor()

    # 示例文本
    sample_text = """
    中华人民共和国专利法

    第一条 为了保护专利权人的合法权益，鼓励发明创造，推动发明创造的应用，
    提高创新能力，促进科学技术进步和经济社会发展，制定本法。

    第二条 本法所称的发明创造是指发明、实用新型和外观设计。

    第三条 国务院专利行政部门负责管理全国的专利工作；
    统一受理和审查专利申请，依法授予专利权。

    2025年修改：新增AI相关发明的审查标准，特别是算法模型的创造性判断。
    """

    # 提取实体和关系
    result = await extractor.extract(sample_text, "patent_law_example")

    print(f"提取到 {len(result.entities)} 个实体")
    print(f"提取到 {len(result.relations)} 个关系")
    print(f"处理时间: {result.processing_time:.2f} 秒")

    # 显示实体
    for entity in result.entities[:5]:
        print(f"\n实体: {entity.entity_text}")
        print(f"  类型: {entity.entity_type.value}")
        print(f"  置信度: {entity.confidence:.2f}")

    # 显示关系
    for relation in result.relations[:5]:
        print(f"\n关系: {relation.relation_type.value}")
        print(f"  置信度: {relation.confidence:.2f}")
        print(f"  证据: {relation.evidence[:50]}...")

if __name__ == "__main__":
    asyncio.run(main())
