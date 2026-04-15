#!/usr/bin/env python3
"""
Athena平台知识图谱集成系统
提供知识图谱构建、查询、分析和推理功能
"""

import asyncio
import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import networkx as nx

from core.logging_config import setup_logging

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

class RelationType(Enum):
    """关系类型枚举"""
    IS_A = 'is_a'                    # 是一个
    PART_OF = 'part_of'             # 是...的一部分
    RELATED_TO = 'related_to'       # 与...相关
    CAUSES = 'causes'               # 导致
    CAUSED_BY = 'caused_by'         # 由...导致
    SIMILAR_TO = 'similar_to'       # 与...相似
    DIFFERENT_FROM = 'different_from' # 与...不同
    INSTANCE_OF = 'instance_of'     # 是...的实例
    SUBCLASS_OF = 'subclass_of'     # 是...的子类
    HAS_PROPERTY = 'has_property'   # 具有属性
    ENABLES = 'enables'             # 使能
    REQUIRES = 'requires'           # 需要
    LOCATED_IN = 'located_in'       # 位于
    APPLIES_TO = 'applies_to'       # 应用于
    USED_FOR = 'used_for'           # 用于

class EntityType(Enum):
    """实体类型枚举"""
    PERSON = 'person'
    ORGANIZATION = 'organization'
    LOCATION = 'location'
    PRODUCT = 'product'
    TECHNOLOGY = 'technology'
    CONCEPT = 'concept'
    EVENT = 'event'
    DOCUMENT = 'document'
    PATENT = 'patent'
    CLAIM = 'claim'
    INVENTION = 'invention'
    METHOD = 'method'
    SYSTEM = 'system'
    COMPONENT = 'component'
    MATERIAL = 'material'
    PROCESS = 'process'
    UNKNOWN = 'unknown'

@dataclass
class Entity:
    """知识图谱实体"""
    entity_id: str
    name: str
    entity_type: EntityType
    properties: dict[str, Any] = field(default_factory=dict)
    aliases: list[str] = field(default_factory=list)
    confidence: float = 1.0
    source: str = ''
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Relation:
    """知识图谱关系"""
    relation_id: str
    subject: str  # 主实体ID
    predicate: RelationType
    object: str   # 客体实体ID
    properties: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    source: str = ''
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class KnowledgeTriple:
    """知识三元组"""
    subject: Entity
    predicate: RelationType
    object: Entity
    confidence: float = 1.0
    context: str = ''

class EntityExtractor:
    """实体提取器"""

    def __init__(self):
        """初始化实体提取器"""
        self.entity_patterns = self._initialize_patterns()
        self.type_keywords = self._initialize_type_keywords()

    def _initialize_patterns(self) -> dict[str, list[str]]:
        """初始化实体识别模式"""
        return {
            'patent': [
                r'专利\s*(?:号\s*)?([A-Z]{2}\d{8,})',
                r'Patent\s+(?:No\.?\s*)?([A-Z]{2}\d{8,})',
                r'申请号\s*[:：]\s*(\d{10,})'
            ],
            'person': [
                r'([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # 英文人名
                r'([\u4e00-\u9fff]{2,4})',  # 中文人名
            ],
            'organization': [
                r'([A-Z][a-z_a-Z\s&]+(?:Inc\.|Corp\.|Ltd\.|LLC|Company|Corporation))',
                r'([\u4e00-\u9fff]+(?:公司|集团|企业|研究院|大学|学院|实验室))'
            ],
            'technology': [
                r'(?:人工智能|AI|机器学习|深度学习|神经网络|算法|模型)',
                r'(?:云计算|大数据|区块链|物联网|5G|6G)',
                r'(?:量子计算|生物技术|新材料|新能源)'
            ],
            'date': [
                r'(\d{4}年\d{1,2}月\d{1,2}日)',
                r'(\d{4}-\d{2}-\d{2})',
                r'(\d{1,2}/\d{1,2}/\d{4})'
            ]
        }

    def _initialize_type_keywords(self) -> dict[EntityType, list[str]]:
        """初始化类型关键词"""
        return {
            EntityType.PERSON: ['人', '发明人', '申请人', '作者', '研究员', '工程师'],
            EntityType.ORGANIZATION: ['公司', '企业', '机构', '大学', '研究院', '实验室', '集团'],
            EntityType.LOCATION: ['国家', '城市', '地区', '省', '市', '县', '区'],
            EntityType.PRODUCT: ['产品', '设备', '系统', '装置', '器件', '工具'],
            EntityType.TECHNOLOGY: ['技术', '方法', '算法', '模型', '方案', '工艺'],
            EntityType.CONCEPT: ['概念', '理论', '原理', '思想', '理念', '观点'],
            EntityType.EVENT: ['事件', '会议', '展览', '发布', '发布', '合作'],
            EntityType.DOCUMENT: ['文档', '论文', '报告', '说明书', '文件', '资料'],
            EntityType.PATENT: ['专利', '发明', '创造', '创新', '技术方案'],
            EntityType.CLAIM: ['权利要求', '保护范围', '权利要求书', '权要'],
            EntityType.INVENTION: ['发明创造', '技术创新', '技术突破', '创新成果']
        }

    def extract_entities(self, text: str, context: str = '') -> list[Entity]:
        """从文本中提取实体"""
        entities = []

        # 基于模式的提取
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    entity_text = match.group(1).strip()

                    # 确定实体类型
                    actual_type = self._map_pattern_to_type(entity_type)

                    # 生成实体ID
                    entity_id = self._generate_entity_id(entity_text, actual_type)

                    # 检查是否已存在
                    existing = next((e for e in entities if e.entity_id == entity_id), None)
                    if existing:
                        continue

                    entity = Entity(
                        entity_id=entity_id,
                        name=entity_text,
                        entity_type=actual_type,
                        properties={'source_pattern': pattern},
                        confidence=0.8,
                        source=context
                    )
                    entities.append(entity)

        # 基于关键词的类型推断
        entities = self._infer_entity_types(text, entities)

        return entities

    def _map_pattern_to_type(self, pattern_type: str) -> EntityType:
        """将模式类型映射到实体类型"""
        mapping = {
            'patent': EntityType.PATENT,
            'person': EntityType.PERSON,
            'organization': EntityType.ORGANIZATION,
            'technology': EntityType.TECHNOLOGY,
            'date': EntityType.CONCEPT  # 日期暂时归类为概念
        }
        return mapping.get(pattern_type, EntityType.UNKNOWN)

    def _infer_entity_types(self, text: str, entities: list[Entity]) -> list[Entity]:
        """基于关键词推断实体类型"""
        words = re.findall(r'[\u4e00-\u9fff]+|[a-z_a-Z]+', text.lower())

        for entity in entities:
            if entity.entity_type != EntityType.UNKNOWN:
                continue

            entity_name = entity.name.lower()

            for entity_type, keywords in self.type_keywords.items():
                for keyword in keywords:
                    if keyword.lower() in entity_name:
                        entity.entity_type = entity_type
                        break
                    elif keyword.lower() in words and entity_name in text:
                        # 实体名称附近有关键词
                        entity.entity_type = entity_type
                        entity.confidence *= 0.9  # 降低置信度
                        break

        return entities

    def _generate_entity_id(self, name: str, entity_type: EntityType) -> str:
        """生成实体ID"""
        name_hash = hashlib.md5(name.encode('utf-8'), usedforsecurity=False).hexdigest()
        return f"{entity_type.value}_{name_hash}"

class RelationExtractor:
    """关系提取器"""

    def __init__(self):
        """初始化关系提取器"""
        self.relation_patterns = self._initialize_relation_patterns()

    def _initialize_relation_patterns(self) -> list[dict]:
        """初始化关系提取模式"""
        return [
            {
                'type': RelationType.IS_A,
                'patterns': [
                    r'(.+?)是(.+?)的(.+)',
                    r'(.+?)是(.+)',
                    r'(.+?)为(.+?)的(.+)',
                    r'(.+?)属于(.+?)',
                    r'(.+?)是一种(.+)'
                ]
            },
            {
                'type': RelationType.PART_OF,
                'patterns': [
                    r'(.+?)是(.+?)的(.+?)部分',
                    r'(.+?)包含(.+?)',
                    r'(.+?)由(.+?)组成',
                    r'(.+?)是(.+?)的组件'
                ]
            },
            {
                'type': RelationType.CAUSES,
                'patterns': [
                    r'(.+?)导致(.+?)',
                    r'(.+?)引起(.+?)',
                    r'(.+?)产生(.+?)',
                    r'(.+?)是(.+?)的原因'
                ]
            },
            {
                'type': RelationType.USED_FOR,
                'patterns': [
                    r'(.+?)用于(.+?)',
                    r'(.+?)适用于(.+?)',
                    r'(.+?)应用于(.+?)',
                    r'(.+?)可用于(.+?)'
                ]
            },
            {
                'type': RelationType.REQUIRES,
                'patterns': [
                    r'(.+?)需要(.+?)',
                    r'(.+?)依赖(.+?)',
                    r'(.+?)要求(.+?)',
                    r'(.+?)基于(.+?)'
                ]
            },
            {
                'type': RelationType.LOCATED_IN,
                'patterns': [
                    r'(.+?)位于(.+?)',
                    r'(.+?)在(.+?)',
                    r'(.+?)坐落于(.+?)',
                    r'(.+?)地处(.+?)'
                ]
            }
        ]

    def extract_relations(self, text: str, entities: list[Entity]) -> list[Relation]:
        """从文本中提取关系"""
        relations = []
        entity_map = {e.name.lower(): e for e in entities}
        entity_map.update({alias.lower(): e for e in entities for alias in e.aliases})

        for pattern_info in self.relation_patterns:
            relation_type = pattern_info['type']

            for pattern in pattern_info['patterns']:
                matches = re.finditer(pattern, text, re.IGNORECASE)

                for match in matches:
                    groups = match.groups()
                    if len(groups) < 2:
                        continue

                    subject_text = groups[0].strip()
                    object_text = groups[1].strip()

                    # 查找对应的实体
                    subject_entity = self._find_entity(subject_text, entity_map)
                    object_entity = self._find_entity(object_text, entity_map)

                    if subject_entity and object_entity:
                        relation_id = self._generate_relation_id(
                            subject_entity.entity_id,
                            relation_type.value,
                            object_entity.entity_id
                        )

                        relation = Relation(
                            relation_id=relation_id,
                            subject=subject_entity.entity_id,
                            predicate=relation_type,
                            object=object_entity.entity_id,
                            confidence=0.7,
                            source='pattern_extraction'
                        )
                        relations.append(relation)

        return relations

    def _find_entity(self, text: str, entity_map: dict[str, Entity]) -> Entity | None:
        """查找实体"""
        text_lower = text.lower()

        # 精确匹配
        if text_lower in entity_map:
            return entity_map[text_lower]

        # 模糊匹配
        for entity_name, entity in entity_map.items():
            if text_lower in entity_name or entity_name in text_lower:
                return entity

        return None

    def _generate_relation_id(self, subject: str, predicate: str, object: str) -> str:
        """生成关系ID"""
        content = f"{subject}_{predicate}_{object}"
        return hashlib.md5(content.encode('utf-8'), usedforsecurity=False).hexdigest()[:12]

class KnowledgeGraphBuilder:
    """知识图谱构建器"""

    def __init__(self):
        """初始化知识图谱构建器"""
        self.entity_extractor = EntityExtractor()
        self.relation_extractor = RelationExtractor()
        self.entities = {}
        self.relations = {}
        self.graph = nx.DiGraph()

    def build_from_text(self, text: str, context: str = '') -> dict[str, Any]:
        """从文本构建知识图谱"""
        logger.info(f"从文本构建知识图谱，文本长度: {len(text)}")

        # 提取实体
        entities = self.entity_extractor.extract_entities(text, context)

        # 提取关系
        relations = self.relation_extractor.extract_relations(text, entities)

        # 合并到知识图谱
        self._merge_entities(entities)
        self._merge_relations(relations)

        # 更新图结构
        self._update_graph()

        return {
            'entities_added': len(entities),
            'relations_added': len(relations),
            'total_entities': len(self.entities),
            'total_relations': len(self.relations),
            'graph_nodes': self.graph.number_of_nodes(),
            'graph_edges': self.graph.number_of_edges()
        }

    def _merge_entities(self, new_entities: list[Entity]) -> Any:
        """合并实体"""
        for entity in new_entities:
            if entity.entity_id in self.entities:
                # 更新现有实体
                existing = self.entities[entity.entity_id]

                # 合并属性
                existing.properties.update(entity.properties)

                # 合并别名
                for alias in entity.aliases:
                    if alias not in existing.aliases:
                        existing.aliases.append(alias)

                # 更新置信度（取平均值）
                existing.confidence = (existing.confidence + entity.confidence) / 2

            else:
                # 添加新实体
                self.entities[entity.entity_id] = entity

    def _merge_relations(self, new_relations: list[Relation]) -> Any:
        """合并关系"""
        for relation in new_relations:
            if relation.relation_id in self.relations:
                # 更新现有关系
                existing = self.relations[relation.relation_id]
                existing.confidence = (existing.confidence + relation.confidence) / 2
                existing.properties.update(relation.properties)
            else:
                # 添加新关系
                self.relations[relation.relation_id] = relation

    def _update_graph(self) -> Any:
        """更新图结构"""
        self.graph.clear()

        # 添加节点
        for entity_id, entity in self.entities.items():
            self.graph.add_node(
                entity_id,
                name=entity.name,
                type=entity.entity_type.value,
                properties=entity.properties,
                confidence=entity.confidence
            )

        # 添加边
        for _relation_id, relation in self.relations.items():
            if relation.subject in self.graph and relation.object in self.graph:
                self.graph.add_edge(
                    relation.subject,
                    relation.object,
                    relation=relation.predicate.value,
                    confidence=relation.confidence,
                    properties=relation.properties
                )

    def query_entity(self, entity_name: str, fuzzy: bool = True) -> list[Entity]:
        """查询实体"""
        results = []

        for entity in self.entities.values():
            if fuzzy:
                # 模糊匹配
                if (entity_name.lower() in entity.name.lower() or
                    entity.name.lower() in entity_name.lower()):
                    results.append(entity)

                # 检查别名
                for alias in entity.aliases:
                    if (entity_name.lower() in alias.lower() or
                        alias.lower() in entity_name.lower()):
                        results.append(entity)
                        break
            else:
                # 精确匹配
                if entity_name.lower() == entity.name.lower():
                    results.append(entity)

        return results

    def query_relations(self, entity_id: str, relation_type: RelationType | None = None) -> list[Relation]:
        """查询关系"""
        results = []

        for relation in self.relations.values():
            if relation.subject == entity_id or relation.object == entity_id:
                if relation_type is None or relation.predicate == relation_type:
                    results.append(relation)

        return results

    def find_path(self, source: str, target: str, max_depth: int = 5) -> list[list[str]]:
        """查找实体间路径"""
        try:
            paths = list(nx.all_simple_paths(self.graph, source, target, cutoff=max_depth))
            return paths
        except nx.NetworkXNoPath:
            return []

    def get_neighbors(self, entity_id: str, depth: int = 1) -> set[str]:
        """获取邻居实体"""
        neighbors = set()

        if entity_id not in self.graph:
            return neighbors

        current_level = {entity_id}

        for _ in range(depth):
            next_level = set()
            for node in current_level:
                next_level.update(self.graph.neighbors(node))
                # 对于有向图，还要考虑入边
                next_level.update(self.graph.predecessors(node))

            neighbors.update(next_level)
            current_level = next_level - neighbors

        neighbors.discard(entity_id)  # 移除自身
        return neighbors

    def calculate_similarity(self, entity1_id: str, entity2_id: str) -> float:
        """计算实体相似度"""
        if entity1_id not in self.graph or entity2_id not in self.graph:
            return 0.0

        # 获取邻居
        neighbors1 = self.get_neighbors(entity1_id, depth=2)
        neighbors2 = self.get_neighbors(entity2_id, depth=2)

        # Jaccard相似度
        intersection = len(neighbors1 & neighbors2)
        union = len(neighbors1 | neighbors2)

        if union == 0:
            return 0.0

        jaccard_sim = intersection / union

        # 考虑实体类型相似度
        entity1 = self.entities.get(entity1_id)
        entity2 = self.entities.get(entity2_id)

        type_sim = 1.0 if entity1 and entity2 and entity1.entity_type == entity2.entity_type else 0.5

        # 综合相似度
        return jaccard_sim * 0.7 + type_sim * 0.3

    def get_statistics(self) -> dict[str, Any]:
        """获取知识图谱统计信息"""
        entity_type_counts = Counter()
        relation_type_counts = Counter()

        for entity in self.entities.values():
            entity_type_counts[entity.entity_type.value] += 1

        for relation in self.relations.values():
            relation_type_counts[relation.predicate.value] += 1

        return {
            'total_entities': len(self.entities),
            'total_relations': len(self.relations),
            'entity_types': dict(entity_type_counts),
            'relation_types': dict(relation_type_counts),
            'graph_density': nx.density(self.graph) if self.graph.number_of_nodes() > 1 else 0,
            'connected_components': nx.number_connected_components(self.graph.to_undirected()),
            'average_clustering': nx.average_clustering(self.graph.to_undirected()) if self.graph.number_of_nodes() > 2 else 0
        }

    def export_graph(self, format: str = 'json') -> str:
        """导出知识图谱"""
        if format == 'json':
            return self._export_json()
        elif format == 'graphml':
            return self._export_graphml()
        else:
            raise ValueError(f"不支持的导出格式: {format}")

    def _export_json(self) -> str:
        """导出为JSON格式"""
        data = {
            'entities': [],
            'relations': []
        }

        for entity in self.entities.values():
            entity_data = {
                'id': entity.entity_id,
                'name': entity.name,
                'type': entity.entity_type.value,
                'properties': entity.properties,
                'aliases': entity.aliases,
                'confidence': entity.confidence,
                'source': entity.source,
                'created_at': entity.created_at.isoformat()
            }
            data['entities'].append(entity_data)

        for relation in self.relations.values():
            relation_data = {
                'id': relation.relation_id,
                'subject': relation.subject,
                'predicate': relation.predicate.value,
                'object': relation.object,
                'properties': relation.properties,
                'confidence': relation.confidence,
                'source': relation.source,
                'created_at': relation.created_at.isoformat()
            }
            data['relations'].append(relation_data)

        return json.dumps(data, ensure_ascii=False, indent=2)

    def _export_graphml(self) -> str:
        """导出为GraphML格式"""
        import io

        output = io.StringIO()
        nx.write_graphml(self.graph, output)
        return output.getvalue()

class KnowledgeGraphReasoner:
    """知识图谱推理器"""

    def __init__(self, graph_builder: KnowledgeGraphBuilder):
        """初始化推理器"""
        self.graph_builder = graph_builder
        self.inference_rules = self._initialize_inference_rules()

    def _initialize_inference_rules(self) -> list[dict]:
        """初始化推理规则"""
        return [
            {
                'name': 'transitivity_is_a',
                'premise': [
                    ('?A', RelationType.IS_A, '?B'),
                    ('?B', RelationType.IS_A, '?C')
                ],
                'conclusion': ('?A', RelationType.IS_A, '?C'),
                'confidence': 0.8
            },
            {
                'name': 'transitivity_part_of',
                'premise': [
                    ('?A', RelationType.PART_OF, '?B'),
                    ('?B', RelationType.PART_OF, '?C')
                ],
                'conclusion': ('?A', RelationType.PART_OF, '?C'),
                'confidence': 0.9
            },
            {
                'name': 'symmetry_similar_to',
                'premise': [
                    ('?A', RelationType.SIMILAR_TO, '?B')
                ],
                'conclusion': ('?B', RelationType.SIMILAR_TO, '?A'),
                'confidence': 0.9
            },
            {
                'name': 'causation_chain',
                'premise': [
                    ('?A', RelationType.CAUSES, '?B'),
                    ('?B', RelationType.CAUSES, '?C')
                ],
                'conclusion': ('?A', RelationType.CAUSES, '?C'),
                'confidence': 0.7
            },
            {
                'name': 'induced_requirements',
                'premise': [
                    ('?A', RelationType.REQUIRES, '?B'),
                    ('?B', RelationType.REQUIRES, '?C')
                ],
                'conclusion': ('?A', RelationType.REQUIRES, '?C'),
                'confidence': 0.6
            }
        ]

    def infer_new_relations(self, max_inferences: int = 100) -> list[Relation]:
        """推理新关系"""
        new_relations = []
        inference_count = 0

        for rule in self.inference_rules:
            if inference_count >= max_inferences:
                break

            # 查找满足前提的关系组合
            premises = rule['premise']
            if len(premises) == 1:
                # 单前提推理
                inferred = self._apply_single_premise_rule(rule)
            elif len(premises) == 2:
                # 双前提推理
                inferred = self._apply_double_premise_rule(rule)
            else:
                continue

            new_relations.extend(inferred)
            inference_count += len(inferred)

        # 过滤已存在的关系
        new_relations = [rel for rel in new_relations if rel.relation_id not in self.graph_builder.relations]

        logger.info(f"推理出 {len(new_relations)} 个新关系")
        return new_relations

    def _apply_single_premise_rule(self, rule: dict) -> list[Relation]:
        """应用单前提规则"""
        inferred_relations = []

        predicate_type = rule['premise'][0][1]
        conclusion = rule['conclusion']

        for relation in self.graph_builder.relations.values():
            if relation.predicate == predicate_type:
                # 应用推理规则
                new_relation = Relation(
                    relation_id=self._generate_inference_id(rule, relation),
                    subject=relation.object if conclusion[0] == '?B' else relation.subject,
                    predicate=conclusion[1],
                    object=relation.subject if conclusion[2] == '?A' else relation.object,
                    confidence=relation.confidence * rule['confidence'],
                    properties={'inferred_by': rule['name'], 'source_relation': relation.relation_id},
                    source='inference'
                )
                inferred_relations.append(new_relation)

        return inferred_relations

    def _apply_double_premise_rule(self, rule: dict) -> list[Relation]:
        """应用双前提规则"""
        inferred_relations = []

        premise1 = rule['premise'][0]
        premise2 = rule['premise'][1]
        conclusion = rule['conclusion']

        # 查找匹配第一个前提的关系
        relations1 = [r for r in self.graph_builder.relations.values() if r.predicate == premise1[1]]

        # 查找匹配第二个前提的关系
        relations2 = [r for r in self.graph_builder.relations.values() if r.predicate == premise2[1]]

        # 寻找匹配的组合
        for rel1 in relations1:
            for rel2 in relations2:
                # 检查变量绑定
                if premise1[2] == premise2[0]:  # ?B = ?A
                    if rel1.object == rel2.subject:
                        new_relation = Relation(
                            relation_id=self._generate_inference_id(rule, rel1, rel2),
                            subject=rel1.subject,
                            predicate=conclusion[1],
                            object=rel2.object,
                            confidence=min(rel1.confidence, rel2.confidence) * rule['confidence'],
                            properties={
                                'inferred_by': rule['name'],
                                'source_relations': [rel1.relation_id, rel2.relation_id]
                            },
                            source='inference'
                        )
                        inferred_relations.append(new_relation)

        return inferred_relations

    def _generate_inference_id(self, rule: dict, *relations) -> str:
        """生成推理关系ID"""
        content = f"{rule['name']}_{'_'.join([rel.relation_id for rel in relations])}"
        return f"inferred_{hashlib.md5(content.encode('utf-8'), usedforsecurity=False).hexdigest()}"

    def apply_inferences(self, max_inferences: int = 100) -> Any:
        """应用推理结果"""
        new_relations = self.infer_new_relations(max_inferences)

        # 将推理关系添加到知识图谱
        for relation in new_relations:
            self.graph_builder.relations[relation.relation_id] = relation

        # 更新图结构
        self.graph_builder._update_graph()

        return len(new_relations)

    def explain_entity(self, entity_id: str, max_depth: int = 3) -> dict[str, Any]:
        """解释实体（获取实体的相关信息）"""
        if entity_id not in self.graph_builder.entities:
            return {'error': '实体不存在'}

        entity = self.graph_builder.entities[entity_id]

        # 获取直接关系
        direct_relations = self.graph_builder.query_relations(entity_id)

        # 获取邻居实体
        neighbors = self.graph_builder.get_neighbors(entity_id, max_depth)

        # 分析实体在知识图谱中的角色
        roles = self._analyze_entity_roles(entity_id)

        # 找到相似实体
        similar_entities = []
        for neighbor_id in neighbors:
            similarity = self.graph_builder.calculate_similarity(entity_id, neighbor_id)
            if similarity > 0.5:
                similar_entities.append({
                    'entity_id': neighbor_id,
                    'entity_name': self.graph_builder.entities.get(neighbor_id, {}).get('name', neighbor_id),
                    'similarity': similarity
                })

        # 排序并限制数量
        similar_entities.sort(key=lambda x: x['similarity'], reverse=True)
        similar_entities = similar_entities[:10]

        return {
            'entity': {
                'id': entity.entity_id,
                'name': entity.name,
                'type': entity.entity_type.value,
                'properties': entity.properties,
                'confidence': entity.confidence
            },
            'direct_relations': [
                {
                    'predicate': rel.predicate.value,
                    'target': rel.object if rel.subject == entity_id else rel.subject,
                    'confidence': rel.confidence
                }
                for rel in direct_relations
            ],
            'neighbors_count': len(neighbors),
            'roles': roles,
            'similar_entities': similar_entities
        }

    def _analyze_entity_roles(self, entity_id: str) -> list[str]:
        """分析实体的角色"""
        roles = []

        # 获取入度和出度
        in_degree = self.graph_builder.graph.in_degree(entity_id)
        out_degree = self.graph_builder.graph.out_degree(entity_id)

        # 基于度数推断角色
        if in_degree > out_degree * 2:
            roles.append('核心概念')
        elif out_degree > in_degree * 2:
            roles.append('连接器')
        elif in_degree + out_degree > 10:
            roles.append('枢纽节点')

        # 基于实体类型推断角色
        entity = self.graph_builder.entities.get(entity_id)
        if entity:
            if entity.entity_type == EntityType.TECHNOLOGY:
                roles.append('技术节点')
            elif entity.entity_type == EntityType.ORGANIZATION:
                roles.append('组织节点')
            elif entity.entity_type == EntityType.PERSON:
                roles.append('人员节点')

        return roles

# 全局知识图谱实例
_knowledge_graph = None

def get_knowledge_graph() -> KnowledgeGraphBuilder:
    """获取知识图谱实例"""
    global _knowledge_graph
    if _knowledge_graph is None:
        _knowledge_graph = KnowledgeGraphBuilder()
    return _knowledge_graph

# 工具函数
async def build_knowledge_graph_from_documents(documents: list[dict[str, str]]) -> dict[str, Any]:
    """从文档构建知识图谱"""
    kg = get_knowledge_graph()
    reasoner = KnowledgeGraphReasoner(kg)

    total_stats = {
        'entities_added': 0,
        'relations_added': 0,
        'inferences_applied': 0
    }

    for doc in documents:
        text = doc.get('text', '')
        context = doc.get('context', '')

        if text:
            stats = kg.build_from_text(text, context)
            total_stats['entities_added'] += stats['entities_added']
            total_stats['relations_added'] += stats['relations_added']

    # 应用推理
    inferences = reasoner.apply_inferences(max_inferences=50)
    total_stats['inferences_applied'] = inferences

    # 获取最终统计
    final_stats = kg.get_statistics()
    total_stats.update(final_stats)

    return total_stats

if __name__ == '__main__':
    async def test_knowledge_graph():
        """测试知识图谱系统"""
        kg = get_knowledge_graph()
        reasoner = KnowledgeGraphReasoner(kg)

        # 测试文本
        test_texts = [
            {
                'text': '人工智能技术包括机器学习和深度学习。深度学习是机器学习的一个分支。',
                'context': '技术文档'
            },
            {
                'text': '张三是谷歌公司的人工智能研究员，他发明了一种新的神经网络算法。',
                'context': '人员信息'
            },
            {
                'text': '谷歌公司位于美国加州，是世界知名的科技公司。',
                'context': '公司信息'
            }
        ]

        # 构建知识图谱
        for text_info in test_texts:
            stats = kg.build_from_text(text_info['text'], text_info['context'])
            logger.info(f"处理结果: {stats}")

        # 应用推理
        inferences = reasoner.apply_inferences()
        logger.info(f"推理出 {inferences} 个新关系")

        # 查询测试
        google_entities = kg.query_entity('谷歌')
        logger.info(f"找到谷歌相关实体: {[e.name for e in google_entities]}")

        if google_entities:
            google_id = google_entities[0].entity_id
            explanation = reasoner.explain_entity(google_id)
            logger.info(f"谷歌实体解释: {json.dumps(explanation, ensure_ascii=False, indent=2)}")

        # 统计信息
        stats = kg.get_statistics()
        logger.info(f"知识图谱统计: {json.dumps(stats, ensure_ascii=False, indent=2)}")

    asyncio.run(test_knowledge_graph())
