#!/usr/bin/env python3
"""
专利规则构建系统 - 简化版BERT实体关系提取器
Patent Rules Builder - Simplified BERT Entity Relation Extractor

使用本地NLP系统提取专利法律文本中的实体和关系

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

# 使用本地NLP系统
try:
    import sys
    sys.path.append("/Users/xujian/Athena工作平台/production/dev/scripts")
    from nlp_adapter_professional import NLPAdapter
    NLP_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✅ 使用本地NLP系统")
except ImportError:
    NLP_AVAILABLE = False
    logger = logging.getLogger(__name__)
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

    # 司法解释
    JUDICIAL_INTERPRETATION = "司法解释"

    # 概念实体
    CONCEPT = "概念"
    DEFINITION = "定义"
    TERM = "术语"
    CONDITION = "条件"
    REQUIREMENT = "要求"
    PROCEDURE = "程序"
    STANDARD = "标准"

    # 2025修改
    MODIFICATION_2025 = "2025年修改"
    NEW_SECTION = "新增章节"
    AI_SECTION = "AI相关章节"
    BITSTREAM_SECTION = "比特流章节"

    # 特殊实体
    INVENTION = "发明"
    UTILITY_MODEL = "实用新型"
    DESIGN = "外观设计"
    PATENT_RIGHT = "专利权"

class RelationType(Enum):
    """关系类型"""
    # 结构关系
    CONTAINS = "包含"
    REFERENCES = "引用"
    DEFINES = "定义"
    APPLIES_TO = "适用于"
    REQUIRES = "要求"
    PROHIBITS = "禁止"

    # 2025特殊关系
    INTRODUCED_2025 = "2025年引入"
    AMENDED_2025 = "2025年修订"
    AI_RELATED = "AI相关"

    # 其他关系
    RELATED_TO = "相关于"

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

class PatentEntityRelationExtractor:
    """专利领域实体关系提取器"""

    def __init__(self):
        self.nlp_adapter = None

        # 初始化NLP适配器
        self._initialize_nlp_adapter()

        # 专利领域词汇
        self.patent_terms = {
            "legal_terms": [
                "专利法", "实施细则", "审查指南", "司法解释", "条例", "办法"
            ],
            "patent_types": [
                "发明", "实用新型", "外观设计", "专利申请", "专利权"
            ],
            "criteria_terms": [
                "新颖性", "创造性", "实用性", "公开充分", "清楚完整"
            ],
            "ai_terms_2025": [
                "人工智能", "AI", "算法", "模型", "深度学习", "机器学习"
            ]
        }

        # 统计信息
        self.stats = {
            "documents_processed": 0,
            "total_entities": 0,
            "total_relations": 0,
            "processing_time": 0
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
            try:
                nlp_entities = await self.nlp_adapter.extract_entities(text)
                logger.info(f"NLP系统提取到 {len(nlp_entities)} 个实体")

                for nlp_entity in nlp_entities:
                    # 映射实体类型
                    entity_type = self._map_entity_type(nlp_entity.get('type', ''))

                    if entity_type:
                        entity = Entity(
                            entity_id=f"{doc_id}_entity_{len(entities):04d}",
                            entity_type=entity_type,
                            entity_text=nlp_entity.get('text', ''),
                            start_pos=nlp_entity.get('start', 0),
                            end_pos=nlp_entity.get('end', 0),
                            confidence=nlp_entity.get('confidence', 0.8),
                            context=text[max(0, nlp_entity.get('start', 0)-30):
                                     nlp_entity.get('end', 0)+30],
                            extraction_method="nlp_adapter",
                            properties=nlp_entity
                        )
                        entities.append(entity)
            except Exception as e:
                logger.error(f"NLP实体提取失败: {e}")

        # 方法2: 使用规则方法（补充）
        rule_entities = self._extract_with_rules(text, doc_id)
        entities.extend(rule_entities)

        # 去重
        entities = self._deduplicate_entities(entities)

        logger.info(f"总共提取到 {len(entities)} 个实体")
        return entities

    def _map_entity_type(self, nlp_type: str) -> EntityType | None:
        """映射实体类型"""
        # 处理法律条文
        if any(keyword in nlp_type for keyword in ["法条", "条款", "条"]):
            return EntityType.LAW_ARTICLE

        # 处理指南章节
        if any(keyword in nlp_type for keyword in ["章", "节", "部分", "指南"]):
            if "章" in nlp_type:
                return EntityType.GUIDELINE_CHAPTER
            elif "节" in nlp_type:
                return EntityType.GUIDELINE_SECTION
            elif "部分" in nlp_type:
                return EntityType.GUIDELINE_PART

        # 处理概念和定义
        if any(keyword in nlp_type for keyword in ["概念", "定义", "术语"]):
            if "定义" in nlp_type:
                return EntityType.DEFINITION
            elif "术语" in nlp_type:
                return EntityType.TERM
            else:
                return EntityType.CONCEPT

        # 处理条件和要求
        if any(keyword in nlp_type for keyword in ["条件", "要求", "标准"]):
            if "要求" in nlp_type:
                return EntityType.REQUIREMENT
            elif "条件" in nlp_type:
                return EntityType.CONDITION
            else:
                return EntityType.STANDARD

        # 处理2025年修改
        if any(keyword in nlp_type for keyword in ["2025", "AI", "人工智能", "修改"]):
            return EntityType.MODIFICATION_2025

        # 处理专利类型
        if nlp_type == "发明":
            return EntityType.INVENTION
        elif nlp_type == "实用新型":
            return EntityType.UTILITY_MODEL
        elif nlp_type == "外观设计":
            return EntityType.DESIGN
        elif nlp_type == "专利权":
            return EntityType.PATENT_RIGHT

        # 默认返回概念
        return EntityType.CONCEPT

    def _extract_with_rules(self, text: str, doc_id: str) -> list[Entity]:
        """使用规则方法提取实体"""
        entities = []

        # 提取法律条文
        article_pattern = r'(第[一二三四五六七八九十\d]+条[：:\s]*[^。；;]*)'
        for match in re.finditer(article_pattern, text):
            entities.append(Entity(
                entity_id=f"{doc_id}_entity_{len(entities):04d}",
                entity_type=EntityType.LAW_ARTICLE,
                entity_text=match.group(1),
                start_pos=match.start(),
                end_pos=match.end(),
                confidence=0.9,
                context=match.group(1),
                extraction_method="rule_pattern",
                properties={"pattern": article_pattern}
            ))

        # 提取章节
        chapter_pattern = r'(第[一二三四五六七八九十\d]+章[：:\s]*[^。；;]*)'
        for match in re.finditer(chapter_pattern, text):
            entities.append(Entity(
                entity_id=f"{doc_id}_entity_{len(entities):04d}",
                entity_type=EntityType.GUIDELINE_CHAPTER,
                entity_text=match.group(1),
                start_pos=match.start(),
                end_pos=match.end(),
                confidence=0.9,
                context=match.group(1),
                extraction_method="rule_pattern",
                properties={"pattern": chapter_pattern}
            ))

        # 提取2025年修改
        mod_2025_pattern = r'(2025年[^。；;]*[^。；;。]*)'
        for match in re.finditer(mod_2025_pattern, text):
            entities.append(Entity(
                entity_id=f"{doc_id}_entity_{len(entities):04d}",
                entity_type=EntityType.MODIFICATION_2025,
                entity_text=match.group(1),
                start_pos=match.start(),
                end_pos=match.end(),
                confidence=0.95,
                context=match.group(1),
                extraction_method="rule_pattern",
                properties={"pattern": mod_2025_pattern}
            ))

        # 提取AI相关
        ai_keywords = ["人工智能", "AI", "算法", "模型", "深度学习", "机器学习", "神经网络"]
        for keyword in ai_keywords:
            for match in re.finditer(re.escape(keyword), text):
                entities.append(Entity(
                    entity_id=f"{doc_id}_entity_{len(entities):04d}",
                    entity_type=EntityType.AI_SECTION,
                    entity_text=keyword,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=0.85,
                    context=text[max(0, match.start()-20):match.end()+20],
                    extraction_method="rule_keyword",
                    properties={"keyword": keyword}
                ))

        return entities

    def _deduplicate_entities(self, entities: list[Entity]) -> list[Entity]:
        """去重实体"""
        if not entities:
            return entities

        # 按位置排序
        entities.sort(key=lambda e: e.start_pos)

        deduplicated = []
        current = entities[0]

        for next_entity in entities[1:]:
            # 检查是否重叠
            if (next_entity.start_pos < current.end_pos and
                next_entity.entity_type == current.entity_type):
                # 合并实体
                current.end_pos = max(current.end_pos, next_entity.end_pos)
                current.confidence = max(current.confidence, next_entity.confidence)
            else:
                deduplicated.append(current)
                current = next_entity

        deduplicated.append(current)
        return deduplicated

    async def extract_relations(self, text: str, entities: list[Entity]) -> list[Relation]:
        """提取关系"""
        relations = []

        # 使用本地NLP系统
        if self.nlp_adapter:
            try:
                entity_texts = [e.entity_text for e in entities]
                nlp_relations = await self.nlp_adapter.extract_relations(text, entity_texts)
                logger.info(f"NLP系统提取到 {len(nlp_relations)} 个关系")

                for nlp_relation in nlp_relations:
                    # 映射关系类型
                    relation_type = self._map_relation_type(nlp_relation.get('type', ''))

                    if relation_type:
                        source_id = self._find_entity_id(entities, nlp_relation.get('source', ''))
                        target_id = self._find_entity_id(entities, nlp_relation.get('target', ''))

                        if source_id and target_id:
                            relations.append(Relation(
                                relation_id=f"relation_{len(relations):04d}",
                                source_entity_id=source_id,
                                target_entity_id=target_id,
                                relation_type=relation_type,
                                confidence=nlp_relation.get('confidence', 0.7),
                                evidence=nlp_relation.get('evidence', ''),
                                extraction_method="nlp_adapter"
                            ))
            except Exception as e:
                logger.error(f"NLP关系提取失败: {e}")

        # 使用规则方法补充
        rule_relations = self._extract_relations_with_rules(text, entities)
        relations.extend(rule_relations)

        # 去重
        relations = self._deduplicate_relations(relations)

        logger.info(f"总共提取到 {len(relations)} 个关系")
        return relations

    def _map_relation_type(self, nlp_type: str) -> RelationType | None:
        """映射关系类型"""
        if "包含" in nlp_type:
            return RelationType.CONTAINS
        elif "引用" in nlp_type:
            return RelationType.REFERENCES
        elif "定义" in nlp_type:
            return RelationType.DEFINES
        elif "适用于" in nlp_type:
            return RelationType.APPLIES_TO
        elif "要求" in nlp_type:
            return RelationType.REQUIRES
        elif "禁止" in nlp_type:
            return RelationType.PROHIBITS
        elif "2025" in nlp_type:
            return RelationType.INTRODUCED_2025
        elif "AI" in nlp_type:
            return RelationType.AI_RELATED
        else:
            return RelationType.RELATED_TO

    def _find_entity_id(self, entities: list[Entity], text: str) -> str | None:
        """查找实体ID"""
        for entity in entities:
            if text in entity.entity_text or entity.entity_text in text:
                return entity.entity_id
        return None

    def _extract_relations_with_rules(self, text: str, entities: list[Entity]) -> list[Relation]:
        """使用规则提取关系"""
        relations = []

        # 章节包含法条
        for i, entity1 in enumerate(entities):
            for entity2 in entities[i+1:]:
                if (entity1.entity_type == EntityType.GUIDELINE_CHAPTER and
                    entity2.entity_type == EntityType.LAW_ARTICLE):
                    relations.append(Relation(
                        relation_id=f"relation_{len(relations):04d}",
                        source_entity_id=entity1.entity_id,
                        target_entity_id=entity2.entity_id,
                        relation_type=RelationType.CONTAINS,
                        confidence=0.8,
                        evidence=f"{entity1.entity_text} 包含 {entity2.entity_text}",
                        extraction_method="rule_structure"
                    ))

        # 2025年修改引入新内容
        for i, entity1 in enumerate(entities):
            for entity2 in entities[i+1:]:
                if (entity1.entity_type == EntityType.MODIFICATION_2025 and
                    entity2.entity_type in [EntityType.AI_SECTION, EntityType.NEW_SECTION]):
                    relations.append(Relation(
                        relation_id=f"relation_{len(relations):04d}",
                        source_entity_id=entity1.entity_id,
                        target_entity_id=entity2.entity_id,
                        relation_type=RelationType.INTRODUCED_2025,
                        confidence=0.9,
                        evidence=f"2025年修改引入了 {entity2.entity_text}",
                        extraction_method="rule_modification"
                    ))

        return relations

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

    async def extract(self, text: str, doc_id: str = "") -> ExtractionResult:
        """联合提取实体和关系"""
        import time
        start_time = time.time()

        # 提取实体
        entities = await self.extract_entities(text, doc_id)

        # 提取关系
        relations = await self.extract_relations(text, entities)

        processing_time = time.time() - start_time

        # 更新统计
        self.stats["documents_processed"] += 1
        self.stats["total_entities"] += len(entities)
        self.stats["total_relations"] += len(relations)
        self.stats["processing_time"] += processing_time

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
            model_used="local_nlp_system",
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
    extractor = PatentEntityRelationExtractor()

    # 示例文本
    sample_text = """
    中华人民共和国专利法

    第一条 为了保护专利权人的合法权益，鼓励发明创造，制定本法。

    第二条 本法所称的发明创造是指发明、实用新型和外观设计。

    第三章 专利申请的审查
    3.1 发明专利申请应当符合新颖性、创造性和实用性的要求。
    3.2 说明书应当对发明作出清楚、完整的说明。

    2025年修改：新增AI相关发明的审查标准。算法模型需要体现技术创新。
    """

    # 提取实体和关系
    result = await extractor.extract(sample_text, "patent_law_example")

    print(f"提取到 {len(result.entities)} 个实体")
    print(f"提取到 {len(result.relations)} 个关系")
    print(f"处理时间: {result.processing_time:.2f} 秒")

    # 显示实体
    print("\n实体列表:")
    for entity in result.entities:
        print(f"  - {entity.entity_text} [{entity.entity_type.value}] (置信度: {entity.confidence:.2f})")

    # 显示关系
    print("\n关系列表:")
    for relation in result.relations:
        print(f"  - {relation.relation_type.value} (置信度: {relation.confidence:.2f})")

if __name__ == "__main__":
    asyncio.run(main())
