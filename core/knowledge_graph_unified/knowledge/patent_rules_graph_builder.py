#!/usr/bin/env python3

"""
专利规则知识图谱构建器
Patent Rules Knowledge Graph Builder

构建和更新专利规则相关的知识图谱

作者: Athena AI系统
创建时间: 2025-12-05
版本: 1.0.0
"""

import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class NodeType(Enum):
    """节点类型"""

    LEGAL_DOCUMENT = "legal_document"
    ARTICLE = "article"
    CHAPTER = "chapter"
    SECTION = "section"
    CLAUSE = "clause"
    CONCEPT = "concept"
    PROCEDURE = "procedure"
    CRITERION = "criterion"
    DEADLINE = "deadline"
    AUTHORITY = "authority"


class RelationType(Enum):
    """关系类型"""

    BELONGS_TO = "belongs_to"
    CONTAINS = "contains"
    DEFINES = "defines"
    REFERENCES = "references"
    SUPERSEDES = "supersedes"
    PREREQUISITE = "prerequisite"
    CONSEQUENCE = "consequence"
    EXAMPLES = "dev/examples"
    EXCEPTION = "exception"


@dataclass
class KnowledgeNode:
    """知识图谱节点"""

    id: str
    type: NodeType
    name: str
    properties: dict[str, Any]
    text: Optional[str] = None


@dataclass
class KnowledgeRelation:
    """知识图谱关系"""

    source: str
    target: str
    type: RelationType
    properties: dict[str, Any]
class PatentRulesGraphBuilder:
    """专利规则知识图谱构建器"""

    def __init__(self):
        self.nodes: dict[str, KnowledgeNode] = {}
        self.relations: list[KnowledgeRelation] = []
        self.existing_nodes: set[str] = set()
        self.existing_relations: set[str] = set()

        # 专利相关概念词典
        self.patent_concepts = {
            "专利",
            "发明",
            "实用新型",
            "外观设计",
            "申请",
            "审查",
            "授权",
            "权利要求",
            "说明书",
            "摘要",
            "附图",
            "优先权",
            "新颖性",
            "创造性",
            "实用性",
            "公开",
            "公告",
            "异议",
            "无效",
            "撤销",
            "终止",
            "期限",
            "费用",
            "代理",
            "专利权",
            "侵权",
            "许可",
            "转让",
            "评估",
            "诉讼",
        }

        # 法律概念词典
        self.legal_concepts = {
            "当事人",
            "权利",
            "义务",
            "责任",
            "赔偿",
            "诉讼",
            "仲裁",
            "调解",
            "执行",
            "保全",
            "证据",
            "举证",
            "管辖",
            "时效",
            "法律适用",
            "司法解释",
            "行政法规",
            "部门规章",
            "地方性法规",
        }

    def build_graph_from_rules(self, rules: list[dict[str, Any]) -> dict[str, Any]]:
        """从规则列表构建知识图谱"""
        logger.info(f"🏗️ 开始构建知识图谱,规则数量: {len(rules)}")

        # 处理每条规则
        for rule in rules:
            self._process_rule(rule)

        # 构建概念关系
        self._build_concept_relations()

        # 构建层级关系
        self._build_hierarchy_relations()

        # 统计信息
        stats = {
            "nodes_count": len(self.nodes),
            "relations_count": len(self.relations),
            "node_types": self._get_node_type_stats(),
            "relation_types": self._get_relation_type_stats(),
        }

        logger.info(
            f"✅ 知识图谱构建完成: {stats['nodes_count']} 节点, {stats['relations_count']} 关系"
        )

        return {
            "nodes": [self._node_to_dict(node) for node in self.nodes.values()],
            "relations": [self._relation_to_dict(rel) for rel in self.relations],
            "statistics": stats,
            "build_time": datetime.now().isoformat(),
        }

    def _process_rule(self, rule: dict[str, Any]):
        """处理单条规则"""
        text = rule.get("text", "")
        source_file = rule.get("source_file", "")
        metadata = rule.get("metadata", {})

        # 创建文档节点
        doc_node = self._get_or_create_document_node(source_file)

        # 根据规则类型创建相应节点
        chunk_type = metadata.get("chunk_type", "paragraph")

        if chunk_type == "article":
            rule_node = self._create_article_node(rule)
            self._add_relation(doc_node.id, rule_node.id, RelationType.CONTAINS)

        elif chunk_type == "chapter":
            rule_node = self._create_chapter_node(rule)
            self._add_relation(doc_node.id, rule_node.id, RelationType.CONTAINS)

        elif chunk_type == "section":
            rule_node = self._create_section_node(rule)
            self._add_relation(doc_node.id, rule_node.id, RelationType.CONTAINS)

        else:
            # 创建通用规则节点
            rule_node = self._create_generic_rule_node(rule)
            self._add_relation(doc_node.id, rule_node.id, RelationType.CONTAINS)

        # 提取概念节点
        concept_nodes = self._extract_concepts(text)
        for concept_node in concept_nodes:
            self._add_relation(rule_node.id, concept_node.id, RelationType.DEFINES)

        # 提取程序和时间节点
        procedure_nodes = self._extract_procedures(text)
        for proc_node in procedure_nodes:
            self._add_relation(rule_node.id, proc_node.id, RelationType.CONTAINS)

        deadline_nodes = self._extract_deadlines(text)
        for deadline_node in deadline_nodes:
            self._add_relation(rule_node.id, deadline_node.id, RelationType.DEFINES)

    def _get_or_create_document_node(self, source_file: str) -> KnowledgeNode:
        """获取或创建文档节点"""
        doc_id = f"doc_{self._generate_id(source_file)}"

        if doc_id not in self.nodes:
            doc_type = self._classify_document_type(source_file)

            node = KnowledgeNode(
                id=doc_id,
                type=NodeType.LEGAL_DOCUMENT,
                name=source_file,
                properties={
                    "file_name": source_file,
                    "document_type": doc_type,
                    "create_time": datetime.now().isoformat(),
                },
            )

            self.nodes[doc_id] = node

        return self.nodes[doc_id]

    def _classify_document_type(self, file_name: str) -> str:
        """分类文档类型"""
        if "专利法" in file_name:
            return "专利法"
        elif "实施细则" in file_name:
            return "专利法实施细则"
        elif "审查指南" in file_name:
            return "专利审查指南"
        elif "民法典" in file_name:
            return "民法典"
        elif "司法解释" in file_name or "最高人民法院" in file_name:
            return "司法解释"
        else:
            return "其他法律文件"

    def _create_article_node(self, rule: dict[str, Any]) -> KnowledgeNode:
        """创建条款节点"""
        metadata = rule.get("metadata", {})
        article_num = metadata.get("article_num", "")

        node_id = f"article_{self._generate_id(rule['text_hash'])}"

        if node_id not in self.nodes:
            node = KnowledgeNode(
                id=node_id,
                type=NodeType.ARTICLE,
                name=f"条款 {article_num}",
                properties={
                    "article_num": article_num,
                    "source_file": rule.get("source_file"),
                    "chunk_type": "article",
                    "text_hash": rule.get("text_hash"),
                },
                text=rule.get("text"),
            )

            self.nodes[node_id] = node

        return self.nodes[node_id]

    def _create_chapter_node(self, rule: dict[str, Any]) -> KnowledgeNode:
        """创建章节节点"""
        metadata = rule.get("metadata", {})
        chapter_num = metadata.get("chapter_num", "")

        node_id = f"chapter_{self._generate_id(rule['text_hash'])}"

        if node_id not in self.nodes:
            node = KnowledgeNode(
                id=node_id,
                type=NodeType.CHAPTER,
                name=f"章节 {chapter_num}",
                properties={
                    "chapter_num": chapter_num,
                    "source_file": rule.get("source_file"),
                    "chunk_type": "chapter",
                    "text_hash": rule.get("text_hash"),
                },
                text=rule.get("text"),
            )

            self.nodes[node_id] = node

        return self.nodes[node_id]

    def _create_section_node(self, rule: dict[str, Any]) -> KnowledgeNode:
        """创建小节节点"""
        metadata = rule.get("metadata", {})
        section_num = metadata.get("section_num", "")

        node_id = f"section_{self._generate_id(rule['text_hash'])}"

        if node_id not in self.nodes:
            node = KnowledgeNode(
                id=node_id,
                type=NodeType.SECTION,
                name=f"小节 {section_num}",
                properties={
                    "section_num": section_num,
                    "source_file": rule.get("source_file"),
                    "chunk_type": "section",
                    "text_hash": rule.get("text_hash"),
                },
                text=rule.get("text"),
            )

            self.nodes[node_id] = node

        return self.nodes[node_id]

    def _create_generic_rule_node(self, rule: dict[str, Any]) -> KnowledgeNode:
        """创建通用规则节点"""
        node_id = f"rule_{self._generate_id(rule['text_hash'])}"

        if node_id not in self.nodes:
            metadata = rule.get("metadata", {})
            chunk_type = metadata.get("chunk_type", "paragraph")

            node = KnowledgeNode(
                id=node_id,
                type=NodeType.CLAUSE,
                name=f"规则 {chunk_type}",
                properties={
                    "source_file": rule.get("source_file"),
                    "chunk_type": chunk_type,
                    "text_hash": rule.get("text_hash"),
                    "relevance": metadata.get("relevance_to_patent", "中"),
                },
                text=rule.get("text"),
            )

            self.nodes[node_id] = node

        return self.nodes[node_id]

    def _extract_concepts(self, text: str) -> list[KnowledgeNode]:
        """提取概念节点"""
        concept_nodes = []

        # 提取专利概念
        for concept in self.patent_concepts:
            if concept in text:
                node_id = f"concept_patent_{concept}"

                if node_id not in self.nodes:
                    node = KnowledgeNode(
                        id=node_id,
                        type=NodeType.CONCEPT,
                        name=concept,
                        properties={
                            "concept_type": "专利概念",
                            "category": "patent",
                            "definition": self._get_concept_definition(concept),
                        },
                    )

                    self.nodes[node_id] = node
                    concept_nodes.append(node)

        # 提取法律概念
        for concept in self.legal_concepts:
            if concept in text:
                node_id = f"concept_legal_{concept}"

                if node_id not in self.nodes:
                    node = KnowledgeNode(
                        id=node_id,
                        type=NodeType.CONCEPT,
                        name=concept,
                        properties={
                            "concept_type": "法律概念",
                            "category": "legal",
                            "definition": self._get_concept_definition(concept),
                        },
                    )

                    self.nodes[node_id] = node
                    concept_nodes.append(node)

        return concept_nodes

    def _extract_procedures(self, text: str) -> list[KnowledgeNode]:
        """提取程序节点"""
        procedure_nodes = []

        # 程序性关键词
        procedure_keywords = [
            "申请",
            "审查",
            "公告",
            "授权",
            "异议",
            "无效",
            "撤销",
            "诉讼",
            "仲裁",
        ]

        for keyword in procedure_keywords:
            if keyword in text:
                node_id = f"procedure_{self._generate_id(keyword + text[:50])}"

                if node_id not in self.nodes:
                    node = KnowledgeNode(
                        id=node_id,
                        type=NodeType.PROCEDURE,
                        name=f"{keyword}程序",
                        properties={
                            "procedure_type": keyword,
                            "description": f"与{keyword}相关的程序性规定",
                        },
                    )

                    self.nodes[node_id] = node
                    procedure_nodes.append(node)

        return procedure_nodes

    def _extract_deadlines(self, text: str) -> list[KnowledgeNode]:
        """提取时间期限节点"""
        deadline_nodes = []

        # 匹配时间期限
        deadline_patterns = [
            r"(\d+)[日天月年]内",
            r"(\d+)[个]*[工作日]内",
            r"自.*之日起(\d+)[日天月年]",
            r"不超过(\d+)[日天月年]",
            r"至少(\d+)[日天月年]",
        ]

        for pattern in deadline_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                deadline_text = match.group() if hasattr(match, "group") else f"{match}日内"
                node_id = f"deadline_{self._generate_id(deadline_text)}"

                if node_id not in self.nodes:
                    node = KnowledgeNode(
                        id=node_id,
                        type=NodeType.DEADLINE,
                        name=f"期限 {deadline_text}",
                        properties={
                            "deadline_type": "时间期限",
                            "duration": deadline_text,
                            "time_unit": self._extract_time_unit(deadline_text),
                        },
                    )

                    self.nodes[node_id] = node
                    deadline_nodes.append(node)

        return deadline_nodes

    def _get_concept_definition(self, concept: str) -> str:
        """获取概念定义"""
        definitions = {
            "专利": "国家授予发明创造者在一定期限内的独占权",
            "发明": "对产品、方法或者其改进所提出的新的技术方案",
            "实用新型": "对产品的形状、构造或者其结合所提出的适于实用的新的技术方案",
            "外观设计": "对产品的形状、图案或者其结合以及色彩与形状、图案的结合所作出的富有美感并适于工业应用的新设计",
            "新颖性": "不属于现有技术",
            "创造性": "与现有技术相比,具有突出的实质性特点和显著的进步",
            "实用性": "能够制造或者使用,并且能够产生积极效果",
            "权利要求": "专利申请人要求专利保护的范围",
            "说明书": "清楚、完整地描述发明创造的技术内容",
        }

        return definitions.get(concept, f"{concept}相关的专业概念")

    def _extract_time_unit(self, deadline_text: str) -> str:
        """提取时间单位"""
        if "日" in deadline_text:
            return "日"
        elif "月" in deadline_text:
            return "月"
        elif "年" in deadline_text:
            return "年"
        elif "工作日" in deadline_text:
            return "工作日"
        else:
            return "未知"

    def _build_concept_relations(self):
        """构建概念之间的关系"""
        # 概念层级关系
        concept_hierarchy = {
            "专利": ["发明", "实用新型", "外观设计"],
            "申请": ["提交申请", "形式审查", "实质审查"],
            "授权": ["公告", "颁发证书"],
        }

        for parent, children in concept_hierarchy.items():
            parent_id = f"concept_patent_{parent}"
            if parent_id in self.nodes:
                for child in children:
                    child_id = f"concept_patent_{child}"
                    if child_id in self.nodes:
                        self._add_relation(parent_id, child_id, RelationType.CONTAINS)

    def _build_hierarchy_relations(self):
        """构建层级关系"""
        # 构建文档、章节、条款的层级关系
        for node in self.nodes.values():
            if node.type == NodeType.ARTICLE:
                # 查找所属章节
                chapter_num = node.properties.get("chapter_num")
                if chapter_num:
                    for other_node in self.nodes.values():
                        if (
                            other_node.type == NodeType.CHAPTER
                            and other_node.properties.get("chapter_num") == chapter_num
                        ):
                            self._add_relation(other_node.id, node.id, RelationType.CONTAINS)
                            break

    def _add_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: RelationType,
        properties: Optional[dict[str, Any]] = None,
    ):
        """添加关系"""
        relation = KnowledgeRelation(
            source=source_id, target=target_id, type=relation_type, properties=properties or {}
        )

        self.relations.append(relation)

    def _generate_id(self, text: str) -> str:
        """生成ID"""
        import hashlib

        return hashlib.md5(text.encode("utf-8"), usedforsecurity=False).hexdigest()

    def _node_to_dict(self, node: KnowledgeNode) -> dict[str, Any]:
        """节点转字典"""
        return {
            "id": node.id,
            "type": node.type.value,
            "name": node.name,
            "properties": node.properties,
            "text": node.text,
        }

    def _relation_to_dict(self, relation: KnowledgeRelation) -> dict[str, Any]:
        """关系转字典"""
        return {
            "source": relation.source,
            "target": relation.target,
            "type": relation.type.value,
            "properties": relation.properties,
        }

    def _get_node_type_stats(self) -> dict[str, int]:
        """获取节点类型统计"""
        stats = {}
        for node in self.nodes.values():
            node_type = node.type.value
            stats[node_type] = stats.get(node_type, 0) + 1
        return stats

    def _get_relation_type_stats(self) -> dict[str, int]:
        """获取关系类型统计"""
        stats = {}
        for relation in self.relations:
            rel_type = relation.type.value
            stats[rel_type] = stats.get(rel_type, 0) + 1
        return stats

    def save_graph_to_file(self, graph_data: dict[str, Any], file_path: str):
        """保存知识图谱到文件"""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(graph_data, f, ensure_ascii=False, indent=2)

        logger.info(f"💾 知识图谱已保存到: {file_path}")


# 导出主要类
__all__ = [
    "KnowledgeNode",
    "KnowledgeRelation",
    "NodeType",
    "PatentRulesGraphBuilder",
    "RelationType",
]

