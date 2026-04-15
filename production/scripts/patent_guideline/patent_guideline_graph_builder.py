#!/usr/bin/env python3
"""
专利指南知识图谱构建器
Patent Guideline Knowledge Graph Builder

构建专利审查指南的知识图谱

作者: Athena平台团队
创建时间: 2025-12-20
"""

from __future__ import annotations
import asyncio
import json
import logging
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

# 使用安全哈希函数替代不安全的MD5/SHA1
from production.utils.security_helpers import short_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class GuidelineEntity:
    """指南实体"""
    entity_id: str
    entity_type: str
    entity_name: str
    entity_value: str
    attributes: dict
    section_id: str
    confidence: float
    source_text: str

@dataclass
class GuidelineRelation:
    """指南关系"""
    relation_id: str
    subject_id: str
    object_id: str
    relation_type: str
    attributes: dict
    confidence: float
    source_text: str
    reference_type: str = "explicit"

class PatentGuidelineGraphBuilder:
    """专利指南知识图谱构建器"""

    def __init__(self):
        # 导入NLP适配器
        import os
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        self.nlp_adapter = None  # 延迟初始化

        # 实体类型定义
        self.entity_types = {
            # 文档结构
            "DOCUMENT": "文档",
            "PART": "部分",
            "CHAPTER": "章",
            "SECTION": "节",
            "SUBSECTION": "小节",
            "PARAGRAPH": "段落",

            # 法律相关
            "LAW_ARTICLE": "法律条款",
            "RULE": "审查规则",
            "PRINCIPLE": "审查原则",
            "CRITERION": "审查标准",
            "PROCEDURE": "审查程序",
            "EVIDENCE": "证据",
            "EXAMPLE": "案例",
            "NOTE": "注释",

            # 技术相关
            "TECH_FIELD": "技术领域",
            "TECH_FEATURE": "技术特征",
            "INVENTION": "发明",
            "UTILITY_MODEL": "实用新型",
            "DESIGN": "外观设计",

            # 概念相关
            "CONCEPT": "概念",
            "DEFINITION": "定义",
            "TERM": "术语",
            "CONDITION": "条件",
            "EXCEPTION": "例外",
            "REQUIREMENT": "要求"
        }

        # 关系类型定义
        self.relation_types = {
            # 层级关系
            "HAS_PART": "包含部分",
            "HAS_CHAPTER": "包含章",
            "HAS_SECTION": "包含节",
            "HAS_SUBSECTION": "包含小节",
            "CONTAINS": "包含",
            "BELONGS_TO": "属于",

            # 引用关系
            "REFERS_TO": "引用",
            "REFERENCED_BY": "被引用",
            "CITES": "引用",
            "CITED_BY": "被引用",
            "ACCORDING_TO": "根据",
            "BASED_ON": "基于",
            "IN_ACCORDANCE_WITH": "依据",

            # 逻辑关系
            "DEFINES": "定义",
            "IS_DEFINED_AS": "被定义为",
            "EXEMPLIFIES": "举例说明",
            "ILLUSTRATES": "说明",
            "APPLIES_TO": "适用于",
            "DOES_NOT_APPLY_TO": "不适用于",
            "CONDITION_FOR": "是...的条件",
            "EXCEPTION_TO": "是...的例外",
            "REQUIREMENT_FOR": "是...的要求",

            # 概念关系
            "RELATED_TO": "相关于",
            "SIMILAR_TO": "类似于",
            "DIFFERENT_FROM": "区别于",
            "OPPOSITE_OF": "相反于",
            "CLASSIFIES": "分类",
            "INSTANCE_OF": "是...的实例",

            # 法律关系
            "REGULATES": "规范",
            "MANDATES": "规定",
            "PROHIBITS": "禁止",
            "PERMITS": "允许",
            "REQUIRES": "要求"
        }

        # 正则表达式模式
        self.patterns = {
            # 法律条款引用
            "law_reference": r"专利法第([一二三四五六七八九十百千万0-9]+)条",
            "law_detail": r"专利法实施细则第([一二三四五六七八九十百千万0-9]+)条",
            "guide_reference": r"审查指南第([一二三四五六七八九十百千万0-9]+部分|章|节)",

            # 内部引用
            "internal_ref": r"(参见|根据|依据|按照)(本部分|本指南|本章|本节|上述)?(第?[一二三四五六七八九十\d]+部分|第[一二三四五六七八九十\d]+章|[\d.]+节)",
            "see_also": r"参见第([\d.]+)节",
            "see_chapter": r"参见第([一二三四五六七八九十\d]+)章",

            # 定义
            "definition": r"(是指|定义为|指的是|即|也就是)",
            "example": r"【例(\d+)】",
            "note": r"注(\d*)：",
            "emphasis": r"注意：",

            # 条件和例外
            "condition": r"(在|当|如果|凡是)的情况下",
            "exception": r"(但是|除...外|...除外)",
            "requirement": r"(应当|必须|需要|要求)",
            "prohibition": r"(不得|不能|禁止|不允许)"
        }

    async def build_graph(self, document_data: dict, output_dir: Path) -> dict:
        """构建知识图谱"""
        logger.info("开始构建专利指南知识图谱")

        # 初始化NLP适配器
        if not self.nlp_adapter:
            from scripts.nlp_adapter_professional import ProfessionalNLPAdapter
            self.nlp_adapter = ProfessionalNLPAdapter()
            await self.nlp_adapter.__aenter__()

        try:
            # 1. 提取文档结构实体
            structure_entities = await self._extract_structure_entities(document_data)

            # 2. 提取内容实体
            content_entities = await self._extract_content_entities(document_data, structure_entities)

            # 3. 提取引用关系
            reference_relations = await self._extract_reference_relations(document_data)

            # 4. 提取语义关系
            semantic_relations = await self._extract_semantic_relations(
                document_data,
                structure_entities + content_entities
            )

            # 5. 合并所有实体和关系
            all_entities = structure_entities + content_entities
            all_relations = reference_relations + semantic_relations

            # 6. 去重和优化
            all_entities, all_relations = self._deduplicate_and_optimize(
                all_entities, all_relations
            )

            # 7. 保存结果
            self._save_graph_data(all_entities, all_relations, output_dir, document_data)

            # 8. 生成NebulaGraph导入脚本
            self._generate_nebula_scripts(all_entities, all_relations, output_dir)

            stats = {
                "total_entities": len(all_entities),
                "total_relations": len(all_relations),
                "entity_types": Counter(e.entity_type for e in all_entities),
                "relation_types": Counter(r.relation_type for r in all_relations),
                "processing_time": datetime.now().isoformat()
            }

            logger.info(f"✅ 知识图谱构建完成: {stats['total_entities']}个实体, {stats['total_relations']}个关系")
            return stats

        finally:
            if self.nlp_adapter:
                await self.nlp_adapter.__aexit__(None, None, None)

    async def _extract_structure_entities(self, document_data: dict) -> list[GuidelineEntity]:
        """提取文档结构实体"""
        entities = []
        metadata = document_data.get('metadata', {})

        # 文档实体
        doc_entity = GuidelineEntity(
            entity_id=f"DOC_{short_hash(metadata.get('title', '').encode())[:8]}",
            entity_type="DOCUMENT",
            entity_name=metadata.get('title', ''),
            entity_value=json.dumps(metadata, ensure_ascii=False),
            attributes={
                "version": metadata.get('version'),
                "author": metadata.get('author'),
                "created_date": metadata.get('created_date'),
                "page_count": metadata.get('page_count')
            },
            section_id="ROOT",
            confidence=1.0,
            source_text=metadata.get('title', '')
        )
        entities.append(doc_entity)

        # 章节实体
        sections = document_data.get('sections', [])
        for section in sections:
            entity = GuidelineEntity(
                entity_id=section.get('section_id', ''),
                entity_type=self._map_section_type(section.get('level', 0)),
                entity_name=section.get('title', ''),
                entity_value=section.get('content', '')[:500],
                attributes={
                    "level": section.get('level'),
                    "parent_id": section.get('parent_id'),
                    "full_path": section.get('full_path'),
                    "page_range": section.get('page_range')
                },
                section_id=section.get('section_id', ''),
                confidence=1.0,
                source_text=section.get('title', '')
            )
            entities.append(entity)

        return entities

    async def _extract_content_entities(self, document_data: dict,
                                       structure_entities: list[GuidelineEntity]) -> list[GuidelineEntity]:
        """提取内容实体"""
        entities = []
        sections = document_data.get('sections', [])

        for section in sections:
            content = section.get('content', '')
            if not content:
                continue

            # 使用NLP提取实体
            nlp_entities = await self.nlp_adapter.extract_entities(
                content, "patent_guideline"
            )

            # 转换为GuidelineEntity
            for nlp_entity in nlp_entities:
                entity_type = self._classify_entity_type(
                    nlp_entity.get('text', ''),
                    nlp_entity.get('type', 'UNKNOWN')
                )

                entity = GuidelineEntity(
                    entity_id=self._generate_entity_id(
                        nlp_entity.get('text', ''),
                        section.get('section_id', ''),
                        entity_type
                    ),
                    entity_type=entity_type,
                    entity_name=nlp_entity.get('text', ''),
                    entity_value=self._extract_entity_value(
                        content, nlp_entity.get('text', ''), nlp_entity.get('position', 0)
                    ),
                    attributes={
                        "position": nlp_entity.get('position', 0),
                        "context_length": len(content),
                        "section_level": section.get('level', 0),
                        "nlp_confidence": nlp_entity.get('nlp_confidence', 0.8)
                    },
                    section_id=section.get('section_id', ''),
                    confidence=nlp_entity.get('confidence', 0.8),
                    source_text=content
                )
                entities.append(entity)

            # 使用规则提取额外实体
            rule_entities = self._extract_entities_with_rules(content, section)
            entities.extend(rule_entities)

        return entities

    async def _extract_reference_relations(self, document_data: dict) -> list[GuidelineRelation]:
        """提取引用关系"""
        relations = []
        sections = document_data.get('sections', [])

        for section in sections:
            content = section.get('content', '')
            if not content:
                continue

            # 查找法律条款引用
            law_refs = re.finditer(self.patterns['law_reference'], content)
            for match in law_refs:
                law_id = f"LAW_ARTICLE_{match.group(1)}"
                relations.append(GuidelineRelation(
                    relation_id=self._generate_relation_id(
                        section.get('section_id', ''),
                        law_id,
                        "REFERS_TO"
                    ),
                    subject_id=section.get('section_id', ''),
                    object_id=law_id,
                    relation_type="REFERS_TO",
                    attributes={
                        "reference_type": "law",
                        "article_number": match.group(1),
                        "reference_text": match.group()
                    },
                    confidence=0.95,
                    source_text=match.group(),
                    reference_type="explicit"
                ))

            # 查找内部引用
            internal_refs = re.finditer(self.patterns['internal_ref'], content)
            for match in internal_refs:
                ref_text = match.group()
                # 提取引用的目标部分
                target_section = self._parse_reference_target(ref_text)
                if target_section:
                    relations.append(GuidelineRelation(
                        relation_id=self._generate_relation_id(
                            section.get('section_id', ''),
                            target_section,
                            "REFERS_TO"
                        ),
                        subject_id=section.get('section_id', ''),
                        object_id=target_section,
                        relation_type="REFERS_TO",
                        attributes={
                            "reference_type": "internal",
                            "reference_text": ref_text
                        },
                        confidence=0.9,
                        source_text=ref_text,
                        reference_type="explicit"
                    ))

        return relations

    async def _extract_semantic_relations(self, document_data: dict,
                                         entities: list[GuidelineEntity]) -> list[GuidelineRelation]:
        """提取语义关系"""
        relations = []

        # 按章节分组实体
        entities_by_section = defaultdict(list)
        for entity in entities:
            entities_by_section[entity.section_id].append(entity)

        # 在同一章节内查找关系
        for section_id, section_entities in entities_by_section.items():
            relations.extend(
                await self._find_relations_in_section(
                    document_data, section_id, section_entities
                )
            )

        # 查找跨章节关系
        relations.extend(
            await self._find_cross_section_relations(document_data, entities_by_section)
        )

        return relations

    async def _find_relations_in_section(self, document_data: dict,
                                        section_id: str,
                                        entities: list[GuidelineEntity]) -> list[GuidelineRelation]:
        """在章节内查找关系"""
        relations = []
        content = ""

        # 获取章节内容
        for section in document_data.get('sections', []):
            if section.get('section_id') == section_id:
                content = section.get('content', '')
                break

        # 使用NLP提取关系
        nlp_relations = await self.nlp_adapter.extract_relations(
            content, entities, "patent_guideline"
        )

        # 转换为GuidelineRelation
        for nlp_rel in nlp_relations:
            # 查找对应的实体ID
            subject_id = self._find_entity_id(
                nlp_rel.get('subject', ''), entities
            )
            object_id = self._find_entity_id(
                nlp_rel.get('object', ''), entities
            )

            if subject_id and object_id:
                relation = GuidelineRelation(
                    relation_id=self._generate_relation_id(
                        subject_id, object_id, nlp_rel.get('type', 'RELATED_TO')
                    ),
                    subject_id=subject_id,
                    object_id=object_id,
                    relation_type=nlp_rel.get('type', 'RELATED_TO'),
                    attributes={
                        "nlp_confidence": nlp_rel.get('confidence', 0.7),
                        "context": nlp_rel.get('context', '')
                    },
                    confidence=nlp_rel.get('confidence', 0.7),
                    source_text=content
                )
                relations.append(relation)

        # 使用规则查找定义关系
        relations.extend(self._find_definition_relations(content, entities))

        return relations

    async def _find_cross_section_relations(self, document_data: dict,
                                          entities_by_section: dict) -> list[GuidelineRelation]:
        """查找跨章节关系"""
        relations = []

        # 查找相似概念
        all_entities = []
        for section_entities in entities_by_section.values():
            all_entities.extend(section_entities)

        # 按类型分组
        entities_by_type = defaultdict(list)
        for entity in all_entities:
            entities_by_type[entity.entity_type].append(entity)

        # 为相同类型的实体创建相似关系
        for entity_type, type_entities in entities_by_type.items():
            for i, e1 in enumerate(type_entities):
                for e2 in type_entities[i+1:]:
                    if e1.section_id != e2.section_id:  # 跨章节
                        similarity = self._calculate_entity_similarity(e1, e2)
                        if similarity > 0.7:  # 高相似度
                            relations.append(GuidelineRelation(
                                relation_id=self._generate_relation_id(
                                    e1.entity_id, e2.entity_id, "SIMILAR_TO"
                                ),
                                subject_id=e1.entity_id,
                                object_id=e2.entity_id,
                                relation_type="SIMILAR_TO",
                                attributes={
                                    "similarity": similarity,
                                    "type": entity_type
                                },
                                confidence=similarity,
                                source_text=""
                            ))

        return relations

    def _extract_entities_with_rules(self, content: str, section: dict) -> list[GuidelineEntity]:
        """使用规则提取实体"""
        entities = []

        # 提取案例
        example_matches = re.finditer(self.patterns['example'], content)
        for match in example_matches:
            example_id = match.group(1)
            # 提取案例内容
            start = match.start()
            end = self._find_section_end(content, start)
            example_content = content[start:end].strip()

            entity = GuidelineEntity(
                entity_id=f"EX_{section.get('section_id')}_{example_id}",
                entity_type="EXAMPLE",
                entity_name=f"例{example_id}",
                entity_value=example_content,
                attributes={
                    "example_number": example_id,
                    "section_id": section.get('section_id'),
                    "content_length": len(example_content)
                },
                section_id=section.get('section_id', ''),
                confidence=0.9,
                source_text=example_content
            )
            entities.append(entity)

        # 提取注释
        note_matches = re.finditer(self.patterns['note'], content)
        for match in note_matches:
            note_id = match.group(1) or "1"
            start = match.start()
            end = self._find_section_end(content, start)
            note_content = content[start:end].strip()

            entity = GuidelineEntity(
                entity_id=f"NOTE_{section.get('section_id')}_{note_id}",
                entity_type="NOTE",
                entity_name=f"注{note_id}",
                entity_value=note_content,
                attributes={
                    "note_number": note_id,
                    "section_id": section.get('section_id')
                },
                section_id=section.get('section_id', ''),
                confidence=0.9,
                source_text=note_content
            )
            entities.append(entity)

        # 提取条件句
        condition_matches = re.finditer(self.patterns['condition'], content)
        for match in condition_matches:
            entity = GuidelineEntity(
                entity_id=self._generate_entity_id(
                    match.group(), section.get('section_id'), "CONDITION"
                ),
                entity_type="CONDITION",
                entity_name="条件",
                entity_value=match.group(),
                attributes={
                    "position": match.start(),
                    "condition_type": "conditional"
                },
                section_id=section.get('section_id', ''),
                confidence=0.8,
                source_text=match.group()
            )
            entities.append(entity)

        return entities

    def _find_definition_relations(self, content: str, entities: list[GuidelineEntity]) -> list[GuidelineRelation]:
        """查找定义关系"""
        relations = []

        for entity in entities:
            if entity.entity_type in ["CONCEPT", "TERM"]:
                # 查找定义模式
                def_patterns = [
                    f"{entity.entity_name}{pattern}"
                    for pattern in ["是指", "定义为", "指的是", "即", "也就是"]
                ]

                for pattern in def_patterns:
                    if pattern in content:
                        # 查找定义内容
                        start = content.find(pattern)
                        start = start + len(entity.entity_name) + 2  # 跳过术语和"是"
                        end = self._find_sentence_end(content, start)
                        definition = content[start:end].strip()

                        # 创建定义实体
                        def_entity = GuidelineEntity(
                            entity_id=self._generate_entity_id(
                                f"DEF_{entity.entity_name}", entity.section_id, "DEFINITION"
                            ),
                            entity_type="DEFINITION",
                            entity_name=f"{entity.entity_name}的定义",
                            entity_value=definition,
                            attributes={
                                "defined_term": entity.entity_name
                            },
                            section_id=entity.section_id,
                            confidence=0.9,
                            source_text=definition
                        )
                        entities.append(def_entity)

                        # 创建关系
                        relations.append(GuidelineRelation(
                            relation_id=self._generate_relation_id(
                                def_entity.entity_id, entity.entity_id, "DEFINES"
                            ),
                            subject_id=def_entity.entity_id,
                            object_id=entity.entity_id,
                            relation_type="DEFINES",
                            attributes={
                                "definition_type": "explicit"
                            },
                            confidence=0.9,
                            source_text=pattern
                        ))

        return relations

    def _deduplicate_and_optimize(self, entities: list[GuidelineEntity],
                                 relations: list[GuidelineRelation]) -> tuple[list[GuidelineEntity], list[GuidelineRelation]]:
        """去重和优化"""
        # 实体去重
        unique_entities = {}
        for entity in entities:
            # 基于实体名称和类型去重
            key = (entity.entity_name, entity.entity_type)
            if key not in unique_entities:
                unique_entities[key] = entity
            else:
                # 保留置信度更高的
                if entity.confidence > unique_entities[key].confidence:
                    unique_entities[key] = entity

        # 关系去重
        unique_relations = {}
        for relation in relations:
            key = (relation.subject_id, relation.object_id, relation.relation_type)
            if key not in unique_relations:
                unique_relations[key] = relation
            else:
                # 保留置信度更高的
                if relation.confidence > unique_relations[key].confidence:
                    unique_relations[key] = relation

        return list(unique_entities.values()), list(unique_relations.values())

    def _save_graph_data(self, entities: list[GuidelineEntity],
                        relations: list[GuidelineRelation],
                        output_dir: Path,
                        document_data: dict):
        """保存图谱数据"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 创建输出目录
        graph_dir = output_dir / "patent_guideline_knowledge_graph"
        graph_dir.mkdir(parents=True, exist_ok=True)

        # 保存实体
        entities_file = graph_dir / f"guideline_entities_{timestamp}.json"
        entities_data = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "description": "专利指南知识图谱实体",
                "total_entities": len(entities),
                "entity_types": dict(Counter(e.entity_type for e in entities)),
                "source_document": document_data.get('metadata', {}).get('title', '')
            },
            "entities": [asdict(e) for e in entities]
        }
        with open(entities_file, 'w', encoding='utf-8') as f:
            json.dump(entities_data, f, ensure_ascii=False, indent=2)

        # 保存关系
        relations_file = graph_dir / f"guideline_relations_{timestamp}.json"
        relations_data = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "description": "专利指南知识图谱关系",
                "total_relations": len(relations),
                "relation_types": dict(Counter(r.relation_type for r in relations))
            },
            "relations": [asdict(r) for r in relations]
        }
        with open(relations_file, 'w', encoding='utf-8') as f:
            json.dump(relations_data, f, ensure_ascii=False, indent=2)

        logger.info("  💾 知识图谱数据已保存:")
        logger.info(f"     实体文件: {entities_file}")
        logger.info(f"     关系文件: {relations_file}")

    def _generate_nebula_scripts(self, entities: list[GuidelineEntity],
                                 relations: list[GuidelineRelation],
                                 output_dir: Path):
        """生成NebulaGraph导入脚本"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        graph_dir = output_dir / "patent_guideline_knowledge_graph"

        # 创建tags脚本
        tags_dir = graph_dir / "nebula_tags"
        tags_dir.mkdir(exist_ok=True)

        # 为每种实体类型创建tag
        for entity_type in {e.entity_type for e in entities}:
            type_entities = [e for e in entities if e.entity_type == entity_type]
            if type_entities:
                tag_file = tags_dir / f"{entity_type.lower()}.ngql"
                with open(tag_file, 'w', encoding='utf-8') as f:
                    # 创建tag定义
                    f.write(f"CREATE TAG IF NOT EXISTS {entity_type} (\n")
                    f.write("  entity_id string,\n")
                    f.write("  entity_name string,\n")
                    f.write("  entity_value string,\n")
                    f.write("  section_id string,\n")
                    f.write("  confidence double,\n")
                    f.write("  created_at timestamp\n")
                    f.write(");\n\n")

                    # 插入数据
                    f.write(f"INSERT VERTEX {entity_type} (\n")
                    f.write("  entity_id, entity_name, entity_value, ")
                    f.write("  section_id, confidence, created_at\n")
                    f.write(") VALUES\n")

                    for i, entity in enumerate(type_entities):
                        f.write(f"  '{entity.entity_id}': (")
                        f.write(f"'{entity.entity_id}', '{entity.entity_name}', ")
                        f.write(f"'{entity.entity_value[:200]}', ")
                        f.write(f"'{entity.section_id}', {entity.confidence}, ")
                        f.write(f"datetime('{datetime.now().isoformat()}')")
                        f.write(")\n")
                        if i < len(type_entities) - 1:
                            f.write(",")

        # 创建edges脚本
        edges_dir = graph_dir / "nebula_edges"
        edges_dir.mkdir(exist_ok=True)

        # 为每种关系类型创建edge
        for relation_type in {r.relation_type for r in relations}:
            type_relations = [r for r in relations if r.relation_type == relation_type]
            if type_relations:
                edge_file = edges_dir / f"{relation_type.lower()}.ngql"
                with open(edge_file, 'w', encoding='utf-8') as f:
                    # 创建edge定义
                    f.write(f"CREATE EDGE IF NOT EXISTS {relation_type} (\n")
                    f.write("  relation_id string,\n")
                    f.write("  confidence double,\n")
                    f.write("  attributes string,\n")
                    f.write("  created_at timestamp\n")
                    f.write(");\n\n")

                    # 插入数据
                    f.write(f"INSERT EDGE {relation_type} (\n")
                    f.write("  relation_id, confidence, attributes, created_at\n")
                    f.write(") VALUES\n")

                    for i, relation in enumerate(type_relations):
                        f.write(f"  '{relation.subject_id}' -> '{relation.object_id}': (")
                        f.write(f"'{relation.relation_id}', {relation.confidence}, ")
                        f.write(f"'{json.dumps(relation.attributes, ensure_ascii=False)}', ")
                        f.write(f"datetime('{datetime.now().isoformat()}')")
                        f.write(")\n")
                        if i < len(type_relations) - 1:
                            f.write(",")

        logger.info(f"  📦 NebulaGraph脚本已生成: {graph_dir}/nebula_*/")

    # 辅助方法
    def _map_section_type(self, level: int) -> str:
        """映射章节类型"""
        mapping = {
            1: "PART",
            2: "CHAPTER",
            3: "SECTION",
            4: "SUBSECTION",
            5: "PARAGRAPH"
        }
        return mapping.get(level, "SECTION")

    def _classify_entity_type(self, text: str, nlp_type: str) -> str:
        """分类实体类型"""
        # 优先使用NLP类型
        if nlp_type in self.entity_types:
            return nlp_type

        # 使用规则分类
        text_lower = text.lower()

        if "专利法" in text_lower:
            return "LAW_ARTICLE"
        elif "审查指南" in text_lower:
            return "RULE"
        elif text_lower.startswith(("例", "【例")):
            return "EXAMPLE"
        elif text_lower.startswith(("注", "note")):
            return "NOTE"
        elif text_lower.startswith(("第", "章", "节")):
            return "SECTION"
        elif any(word in text_lower for word in ["是指", "定义"]):
            return "DEFINITION"
        elif any(word in text_lower for word in ["技术", "发明", "实用新型", "外观设计"]):
            return "CONCEPT"
        else:
            return "TERM"

    def _extract_entity_value(self, content: str, entity_text: str, position: int) -> str:
        """提取实体值"""
        # 查找实体周围的上下文
        start = max(0, position - 50)
        end = min(len(content), position + len(entity_text) + 100)
        return content[start:end]

    def _generate_entity_id(self, text: str, section_id: str, entity_type: str) -> str:
        """生成实体ID"""
        content = f"{text}_{section_id}_{entity_type}"
        return short_hash(content.encode())[:16]

    def _generate_relation_id(self, subject_id: str, object_id: str, relation_type: str) -> str:
        """生成关系ID"""
        content = f"{subject_id}_{object_id}_{relation_type}"
        return short_hash(content.encode())[:16]

    def _parse_reference_target(self, ref_text: str) -> str | None:
        """解析引用目标"""
        # 提取章号
        chapter_match = re.search(r'第([一二三四五六七八九十\d]+)章', ref_text)
        if chapter_match:
            return f"C{chapter_match.group(1)}"

        # 提取节号
        section_match = re.search(r'([\d.]+)节', ref_text)
        if section_match:
            return f"S{section_match.group(1).replace('.', '-')}"

        return None

    def _find_entity_id(self, entity_name: str, entities: list[GuidelineEntity]) -> str | None:
        """查找实体ID"""
        for entity in entities:
            if entity.entity_name == entity_name:
                return entity.entity_id
        return None

    def _calculate_entity_similarity(self, e1: GuidelineEntity, e2: GuidelineEntity) -> float:
        """计算实体相似度"""
        if e1.entity_type != e2.entity_type:
            return 0.0

        # 简单的文本相似度
        name1 = set(e1.entity_name.lower().split())
        name2 = set(e2.entity_name.lower().split())

        if not name1 or not name2:
            return 0.0

        intersection = name1 & name2
        union = name1 | name2

        return len(intersection) / len(union)

    def _find_section_end(self, content: str, start: int) -> int:
        """查找章节结束位置"""
        # 查找下一个章节标题或特殊标记
        patterns = [
            r'\n【例\d+】',
            r'\n注\d*：',
            r'\n第[一二三四五六七八九十\d]+[部分章]',
            r'\n\d+\.\d+',
            r'\n\d+\.\d+\.\d+'
        ]

        min_end = len(content)
        for pattern in patterns:
            match = re.search(pattern, content[start:])
            if match:
                min_end = min(min_end, start + match.start())

        return min_end

    def _find_sentence_end(self, content: str, start: int) -> int:
        """查找句子结束位置"""
        end_chars = ['。', '！', '？', '\n\n']
        min_end = len(content)

        for char in end_chars:
            pos = content.find(char, start)
            if pos > start:
                min_end = min(min_end, pos)

        return min_end

# 使用示例
async def main():
    """主函数示例"""
    builder = PatentGuidelineGraphBuilder()

    # 模拟文档数据
    sample_doc = {
        "metadata": {
            "title": "专利审查指南",
            "version": "2023版",
            "page_count": 500
        },
        "sections": [
            {
                "section_id": "C4",
                "level": 2,
                "title": "第四章 创造性",
                "content": "创造性是指与现有技术相比，该发明具有突出的实质性特点和显著的进步。【例1】...",
                "parent_id": "P2"
            }
        ]
    }

    # 构建知识图谱
    output_dir = Path("/Users/xujian/Athena工作平台/production/data")
    stats = await builder.build_graph(sample_doc, output_dir)

    print("\n知识图谱构建统计:")
    print(f"  实体数: {stats['total_entities']}")
    print(f"  关系数: {stats['total_relations']}")
    print(json.dumps(stats['entity_types'], ensure_ascii=False, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
