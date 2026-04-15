#!/usr/bin/env python3
"""
动态知识图谱系统
Dynamic Knowledge Graph System

专利领域的动态知识图谱构建、更新和质量评估系统

作者: Athena + 小诺
创建时间: 2025-12-05
版本: 3.0.0
"""

import asyncio
import json
import logging
import pickle
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import networkx as nx
import numpy as np

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NodeType(Enum):
    """节点类型"""
    PATENT = 'patent'
    TECHNOLOGY = 'technology'
    COMPANY = 'company'
    INVENTOR = 'inventor'
    LEGAL_CASE = 'legal_case'
    STANDARD = 'standard'
    PRODUCT = 'product'
    INDUSTRY = 'industry'
    KEYWORD = 'keyword'
    CONCEPT = 'concept'

class RelationType(Enum):
    """关系类型"""
    CITES = 'cites'                  # 引用
    CITED_BY = 'cited_by'            # 被引用
    SIMILAR_TO = 'similar_to'         # 相似
    PART_OF = 'part_of'              # 属于
    CONTAINS = 'contains'            # 包含
    APPLIES_TO = 'applies_to'         # 应用于
    DEVELOPED_BY = 'developed_by'     # 开发者
    USED_IN = 'used_in'              # 使用于
    CONFLICTS_WITH = 'conflicts_with' # 冲突
    SUPPORTS = 'supports'            # 支持
    RELATED_TO = 'related_to'        # 相关
    INSTANCE_OF = 'instance_of'      # 实例
    CATEGORY_OF = 'category_of'      # 分类
    USES = 'uses'                    # 使用
    IS_USED_BY = 'is_used_by'        # 被使用

class QualityLevel(Enum):
    """质量等级"""
    EXCELLENT = 5    # 优秀
    GOOD = 4         # 良好
    AVERAGE = 3      # 平均
    POOR = 2         # 差
    INVALID = 1      # 无效

class UpdateStrategy(Enum):
    """更新策略"""
    IMMEDIATE = 'immediate'          # 立即更新
    BATCH = 'batch'                  # 批量更新
    SCHEDULED = 'scheduled'          # 定时更新
    MANUAL = 'manual'                # 手动更新
    ADAPTIVE = 'adaptive'            # 自适应更新

@dataclass
class KnowledgeNode:
    """知识图谱节点"""
    node_id: str
    node_type: NodeType
    properties: dict[str, Any]
    embedding: np.ndarray | None = None
    quality_score: float = 1.0
    confidence: float = 1.0
    source: str = ''
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: int = 1
    access_count: int = 0
    last_accessed: datetime | None = None

@dataclass
class KnowledgeRelation:
    """知识图谱关系"""
    relation_id: str
    source_id: str
    target_id: str
    relation_type: RelationType
    properties: dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0
    confidence: float = 1.0
    quality_score: float = 1.0
    source: str = ''
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: int = 1
    verification_count: int = 0

@dataclass
class QualityMetrics:
    """质量指标"""
    completeness: float      # 完整性
    accuracy: float         # 准确性
    consistency: float      # 一致性
    timeliness: float       # 及时性
    relevance: float        # 相关性
    coverage: float         # 覆盖度
    freshness: float        # 新鲜度
    overall_score: float    # 综合得分

class QualityAssessor:
    """质量评估器"""

    def __init__(self):
        self.quality_weights = {
            'completeness': 0.2,
            'accuracy': 0.25,
            'consistency': 0.15,
            'timeliness': 0.1,
            'relevance': 0.15,
            'freshness': 0.15
        }

    def assess_node_quality(self, node: KnowledgeNode, graph: nx.Graph) -> QualityMetrics:
        """评估节点质量"""
        metrics = {
            'completeness': self._assess_completeness(node),
            'accuracy': self._assess_accuracy(node, graph),
            'consistency': self._assess_consistency(node, graph),
            'timeliness': self._assess_timeliness(node),
            'relevance': self._assess_relevance(node, graph),
            'coverage': self._assess_coverage(node, graph),
            'freshness': self._assess_freshness(node)
        }

        # 计算综合得分
        overall_score = sum(
            metrics[key] * weight
            for key, weight in self.quality_weights.items()
        )

        return QualityMetrics(overall_score=overall_score, **metrics)

    def _assess_completeness(self, node: KnowledgeNode) -> float:
        """评估完整性"""
        required_props = self._get_required_properties(node.node_type)
        missing_props = len(required_props - set(node.properties.keys()))

        if not required_props:
            return 1.0

        completeness = 1.0 - (missing_props / len(required_props))
        return max(0.0, completeness)

    def _assess_accuracy(self, node: KnowledgeNode, graph: nx.Graph) -> float:
        """评估准确性"""
        # 基于验证次数和置信度
        if node.node_type == NodeType.PATENT:
            return node.confidence
        else:
            # 非专利节点基于邻居节点的准确度
            neighbors = list(graph.neighbors(node.node_id))
            if not neighbors:
                return 0.5

            neighbor_accuracy = []
            for neighbor_id in neighbors:
                neighbor_node = graph.nodes[neighbor_id].get('data')
                if neighbor_node and hasattr(neighbor_node, 'confidence'):
                    neighbor_accuracy.append(neighbor_node.confidence)

            return np.mean(neighbor_accuracy) if neighbor_accuracy else 0.5

    def _assess_consistency(self, node: KnowledgeNode, graph: nx.Graph) -> float:
        """评估一致性"""
        # 检查节点属性的一致性
        consistency_score = 1.0

        # 检查数值属性的合理性
        for _key, value in node.properties.items():
            if isinstance(value, (int, float)) and value < 0:
                consistency_score *= 0.8

        # 检查文本属性的格式
        for _key, value in node.properties.items():
            if isinstance(value, str) and len(value.strip()) == 0:
                consistency_score *= 0.9

        return consistency_score

    def _assess_timeliness(self, node: KnowledgeNode) -> float:
        """评估及时性"""
        days_old = (datetime.now() - node.updated_at).days

        # 根据节点类型设置不同的时效性要求
        if node.node_type == NodeType.PATENT:
            # 专利信息相对稳定
            if days_old < 30:
                return 1.0
            elif days_old < 365:
                return 0.9
            else:
                return 0.7
        else:
            # 其他信息更新要求较高
            if days_old < 7:
                return 1.0
            elif days_old < 30:
                return 0.8
            else:
                return 0.5

    def _assess_relevance(self, node: KnowledgeNode, graph: nx.Graph) -> float:
        """评估相关性"""
        # 基于访问次数和连接度
        degree = graph.degree(node.node_id)

        if node.access_count == 0:
            access_score = 0.5
        else:
            # 归一化访问分数
            access_score = min(node.access_count / 100.0, 1.0)

        # 连接度分数
        degree_score = min(degree / 20.0, 1.0)

        return (access_score + degree_score) / 2

    def _assess_coverage(self, node: KnowledgeNode, graph: nx.Graph) -> float:
        """评估覆盖度"""
        # 检查关系的多样性
        relations = set()
        for _, _, data in graph.edges(node.node_id, data=True):
            relation = data.get('data')
            if relation and hasattr(relation, 'relation_type'):
                relations.add(relation.relation_type)

        expected_relations = self._get_expected_relations(node.node_type)
        if not expected_relations:
            return 1.0

        coverage = len(relations & expected_relations) / len(expected_relations)
        return coverage

    def _assess_freshness(self, node: KnowledgeNode) -> float:
        """评估新鲜度"""
        # 基于最后访问时间
        if not node.last_accessed:
            return 0.5

        days_since_access = (datetime.now() - node.last_accessed).days
        return max(0.0, 1.0 - days_since_access / 90.0)

    def _get_required_properties(self, node_type: NodeType) -> set[str]:
        """获取必需属性"""
        required_props = {
            NodeType.PATENT: {'title', 'abstract', 'patent_number'},
            NodeType.COMPANY: {'name', 'country'},
            NodeType.INVENTOR: {'name'},
            NodeType.TECHNOLOGY: {'name', 'category'},
            NodeType.LEGAL_CASE: {'title', 'decision'},
            NodeType.STANDARD: {'title', 'standard_number'},
            NodeType.PRODUCT: {'name', 'category'},
            NodeType.INDUSTRY: {'name'},
            NodeType.KEYWORD: {'term'},
            NodeType.CONCEPT: {'name', 'definition'}
        }
        return required_props.get(node_type, set())

    def _get_expected_relations(self, node_type: NodeType) -> set[RelationType]:
        """获取预期关系类型"""
        expected_relations = {
            NodeType.PATENT: {
                RelationType.CITES, RelationType.CITED_BY, RelationType.SIMILAR_TO,
                RelationType.DEVELOPED_BY, RelationType.APPLIES_TO
            },
            NodeType.TECHNOLOGY: {
                RelationType.USED_IN, RelationType.APPLIES_TO, RelationType.RELATED_TO
            },
            NodeType.COMPANY: {
                RelationType.DEVELOPED_BY, RelationType.USED_IN, RelationType.PART_OF
            },
            NodeType.INVENTOR: {
                RelationType.DEVELOPED_BY
            }
        }
        return expected_relations.get(node_type, set())

class KnowledgeGraphManager:
    """知识图谱管理器"""

    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.quality_assessor = QualityAssessor()
        self.node_index = {}  # node_id -> node_data
        self.relation_index = {}  # relation_id -> relation_data

        # 更新策略配置
        self.update_strategies = {
            NodeType.PATENT: UpdateStrategy.IMMEDIATE,
            NodeType.COMPANY: UpdateStrategy.BATCH,
            NodeType.INVENTOR: UpdateStrategy.SCHEDULED,
            NodeType.TECHNOLOGY: UpdateStrategy.ADAPTIVE
        }

        # 质量阈值
        self.quality_thresholds = {
            'min_quality': 0.6,
            'min_confidence': 0.7,
            'max_age_days': 365
        }

        # 更新队列
        self.update_queue = []
        self.batch_size = 100

        # 统计信息
        self.stats = {
            'total_nodes': 0,
            'total_relations': 0,
            'last_update': None,
            'quality_distribution': defaultdict(int)
        }

    def add_node(self, node: KnowledgeNode) -> bool:
        """添加节点"""
        try:
            # 检查节点是否已存在
            if node.node_id in self.graph:
                return self._update_node(node)

            # 质量评估
            initial_graph = self.graph.copy()
            initial_graph.add_node(node.node_id, data=node)
            quality = self.quality_assessor.assess_node_quality(node, initial_graph)

            # 质量过滤
            if quality.overall_score < self.quality_thresholds['min_quality']:
                logger.warning(f"节点 {node.node_id} 质量过低，拒绝添加: {quality.overall_score:.2f}")
                return False

            # 添加到图
            self.graph.add_node(node.node_id, data=node)
            self.node_index[node.node_id] = node

            # 更新统计
            self._update_node_stats(node, quality)

            logger.info(f"✅ 节点 {node.node_id} 添加成功，质量分数: {quality.overall_score:.2f}")
            return True

        except Exception as e:
            logger.error(f"❌ 添加节点 {node.node_id} 失败: {e}")
            return False

    def add_relation(self, relation: KnowledgeRelation) -> bool:
        """添加关系"""
        try:
            # 检查源节点和目标节点是否存在
            if relation.source_id not in self.graph or relation.target_id not in self.graph:
                logger.warning(f"关系 {relation.relation_id} 的节点不存在")
                return False

            # 检查关系是否已存在
            if self.graph.has_edge(relation.source_id, relation.target_id, key=relation.relation_id):
                return self._update_relation(relation)

            # 质量检查
            if relation.confidence < self.quality_thresholds['min_confidence']:
                logger.warning(f"关系 {relation.relation_id} 置信度过低，拒绝添加: {relation.confidence:.2f}")
                return False

            # 添加到图
            self.graph.add_edge(
                relation.source_id,
                relation.target_id,
                key=relation.relation_id,
                data=relation
            )
            self.relation_index[relation.relation_id] = relation

            # 更新节点访问次数
            self._increment_access_count(relation.source_id)
            self._increment_access_count(relation.target_id)

            # 更新统计
            self.stats['total_relations'] += 1

            logger.info(f"✅ 关系 {relation.relation_id} 添加成功")
            return True

        except Exception as e:
            logger.error(f"❌ 添加关系 {relation.relation_id} 失败: {e}")
            return False

    def update_node(self, node_id: str, new_properties: dict[str, Any]) -> bool:
        """更新节点"""
        if node_id not in self.graph:
            return False

        node_data = self.graph.nodes[node_id]['data']
        if not node_data:
            return False

        # 更新属性
        node_data.properties.update(new_properties)
        node_data.updated_at = datetime.now()
        node_data.version += 1

        # 重新评估质量
        quality = self.quality_assessor.assess_node_quality(node_data, self.graph)
        node_data.quality_score = quality.overall_score

        # 更新索引
        self.node_index[node_id] = node_data

        logger.info(f"✅ 节点 {node_id} 更新成功，新质量分数: {quality.overall_score:.2f}")
        return True

    def _update_node(self, new_node: KnowledgeNode) -> bool:
        """内部节点更新"""
        old_node = self.graph.nodes[new_node.node_id]['data']
        if not old_node:
            return False

        # 保留访问统计
        new_node.access_count = old_node.access_count
        new_node.last_accessed = old_node.last_accessed
        new_node.version = old_node.version + 1

        # 更新属性
        self.graph.nodes[new_node.node_id]['data'] = new_node
        self.node_index[new_node.node_id] = new_node

        return True

    def _update_relation(self, new_relation: KnowledgeRelation) -> bool:
        """内部关系更新"""
        edge_data = self.graph[new_relation.source_id][new_relation.target_id][new_relation.relation_id]['data']
        if not edge_data:
            return False

        # 更新属性
        edge_data.properties.update(new_relation.properties)
        edge_data.updated_at = datetime.now()
        edge_data.version += 1
        edge_data.verification_count += 1

        self.relation_index[new_relation.relation_id] = edge_data
        return True

    def _increment_access_count(self, node_id: str):
        """增加节点访问次数"""
        if node_id in self.graph:
            node_data = self.graph.nodes[node_id]['data']
            if node_data:
                node_data.access_count += 1
                node_data.last_accessed = datetime.now()

    def _update_node_stats(self, node: KnowledgeNode, quality: QualityMetrics):
        """更新节点统计"""
        self.stats['total_nodes'] += 1

        # 更新质量分布
        quality_level = int(quality.overall_score * 5)
        quality_level = max(1, min(5, quality_level))
        self.stats['quality_distribution'][quality_level] += 1

    def search_nodes(self,
                    node_type: NodeType | None = None,
                    properties: dict[str, Any] | None = None,
                    keywords: list[str] | None = None,
                    limit: int = 100) -> list[KnowledgeNode]:
        """搜索节点"""
        results = []

        for _node_id, node_data in self.graph.nodes(data=True):
            node = node_data['data']

            # 节点类型过滤
            if node_type and node.node_type != node_type:
                continue

            # 属性过滤
            if properties:
                match = True
                for key, value in properties.items():
                    if key not in node.properties or node.properties[key] != value:
                        match = False
                        break
                if not match:
                    continue

            # 关键词搜索
            if keywords:
                text_content = str(node.properties).lower()
                if not all(keyword.lower() in text_content for keyword in keywords):
                    continue

            results.append(node)

            if len(results) >= limit:
                break

        # 按质量分数排序
        results.sort(key=lambda x: x.quality_score, reverse=True)
        return results

    def find_similar_nodes(self, node_id: str, similarity_threshold: float = 0.8, limit: int = 10) -> list[tuple[str, float]]:
        """查找相似节点"""
        if node_id not in self.graph:
            return []

        source_node = self.graph.nodes[node_id]['data']
        if not source_node or not source_node.embedding:
            return []

        similarities = []
        source_embedding = source_node.embedding

        for other_id, other_data in self.graph.nodes(data=True):
            if other_id == node_id:
                continue

            other_node = other_data['data']
            if not other_node or not other_node.embedding:
                continue

            # 计算余弦相似度
            similarity = np.dot(source_embedding, other_node.embedding) / (
                np.linalg.norm(source_embedding) * np.linalg.norm(other_node.embedding)
            )

            if similarity >= similarity_threshold:
                similarities.append((other_id, similarity))

        # 按相似度排序并限制数量
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:limit]

    def get_node_neighbors(self, node_id: str, relation_types: list[RelationType] | None = None) -> list[tuple[str, RelationType, float]]:
        """获取节点的邻居"""
        if node_id not in self.graph:
            return []

        neighbors = []

        for target_id, edge_data in self.graph[node_id].items():
            for _relation_id, relation in edge_data.items():
                rel_data = relation['data']
                if not rel_data:
                    continue

                if relation_types and rel_data.relation_type not in relation_types:
                    continue

                neighbors.append((target_id, rel_data.relation_type, rel_data.weight))

        return neighbors

    def dynamic_update(self, update_source: dict[str, Any], update_strategy: UpdateStrategy | None = None):
        """动态更新知识图谱"""
        logger.info(f"🔄 开始动态更新，来源: {update_source.get('source', 'unknown')}")

        try:
            # 解析更新数据
            nodes_data = update_source.get('nodes', [])
            relations_data = update_source.get('relations', [])

            # 确定更新策略
            if not update_strategy:
                update_strategy = UpdateStrategy.IMMEDIATE

            # 执行更新
            if update_strategy == UpdateStrategy.IMMEDIATE:
                self._process_immediate_update(nodes_data, relations_data)
            elif update_strategy == UpdateStrategy.BATCH:
                self._process_batch_update(nodes_data, relations_data)
            elif update_strategy == UpdateStrategy.ADAPTIVE:
                self._process_adaptive_update(nodes_data, relations_data)

            # 清理低质量数据
            self._cleanup_low_quality_data()

            # 重新计算质量分数
            self._recalculate_quality_scores()

            # 更新统计信息
            self._update_global_stats()

            self.stats['last_update'] = datetime.now()
            logger.info('✅ 动态更新完成')

        except Exception as e:
            logger.error(f"❌ 动态更新失败: {e}")

    def _process_immediate_update(self, nodes_data: list[dict], relations_data: list[dict]):
        """处理立即更新"""
        # 添加节点
        for node_data in nodes_data:
            node = KnowledgeNode(
                node_id=node_data['id'],
                node_type=NodeType(node_data['type']),
                properties=node_data.get('properties', {}),
                confidence=node_data.get('confidence', 1.0),
                source=node_data.get('source', '')
            )
            self.add_node(node)

        # 添加关系
        for relation_data in relations_data:
            relation = KnowledgeRelation(
                relation_id=relation_data['id'],
                source_id=relation_data['source'],
                target_id=relation_data['target'],
                relation_type=RelationType(relation_data['type']),
                weight=relation_data.get('weight', 1.0),
                confidence=relation_data.get('confidence', 1.0),
                source=relation_data.get('source', '')
            )
            self.add_relation(relation)

    def _process_batch_update(self, nodes_data: list[dict], relations_data: list[dict]):
        """处理批量更新"""
        # 添加到更新队列
        self.update_queue.extend(nodes_data + relations_data)

        # 达到批量大小时处理
        if len(self.update_queue) >= self.batch_size:
            self._flush_update_queue()

    def _process_adaptive_update(self, nodes_data: list[dict], relations_data: list[dict]):
        """处理自适应更新"""
        for node_data in nodes_data:
            node_type = NodeType(node_data['type'])
            strategy = self.update_strategies.get(node_type, UpdateStrategy.BATCH)

            if strategy == UpdateStrategy.IMMEDIATE:
                node = KnowledgeNode(
                    node_id=node_data['id'],
                    node_type=node_type,
                    properties=node_data.get('properties', {}),
                    confidence=node_data.get('confidence', 1.0),
                    source=node_data.get('source', '')
                )
                self.add_node(node)
            else:
                self.update_queue.append(node_data)

        for relation_data in relations_data:
            # 关系通常立即处理
            relation = KnowledgeRelation(
                relation_id=relation_data['id'],
                source_id=relation_data['source'],
                target_id=relation_data['target'],
                relation_type=RelationType(relation_data['type']),
                weight=relation_data.get('weight', 1.0),
                confidence=relation_data.get('confidence', 1.0),
                source=relation_data.get('source', '')
            )
            self.add_relation(relation)

    def _flush_update_queue(self):
        """清空更新队列"""
        if not self.update_queue:
            return

        # 处理队列中的数据
        for item in self.update_queue:
            if 'type' in item:  # 节点数据
                node = KnowledgeNode(
                    node_id=item['id'],
                    node_type=NodeType(item['type']),
                    properties=item.get('properties', {}),
                    confidence=item.get('confidence', 1.0),
                    source=item.get('source', '')
                )
                self.add_node(node)
            else:  # 关系数据
                relation = KnowledgeRelation(
                    relation_id=item['id'],
                    source_id=item['source'],
                    target_id=item['target'],
                    relation_type=RelationType(item['type']),
                    weight=item.get('weight', 1.0),
                    confidence=item.get('confidence', 1.0),
                    source=item.get('source', '')
                )
                self.add_relation(relation)

        self.update_queue.clear()
        logger.info(f"🔄 批量更新完成，处理了 {len(self.update_queue)} 项数据")

    def _cleanup_low_quality_data(self):
        """清理低质量数据"""
        nodes_to_remove = []

        # 检查节点质量
        for node_id, node_data in self.graph.nodes(data=True):
            node = node_data['data']
            if not node:
                continue

            # 检查质量分数
            if node.quality_score < self.quality_thresholds['min_quality']:
                nodes_to_remove.append(node_id)
                continue

            # 检查时间戳
            age_days = (datetime.now() - node.updated_at).days
            if age_days > self.quality_thresholds['max_age_days']:
                # 低质量的旧数据
                if node.quality_score < 0.8:
                    nodes_to_remove.append(node_id)
                    continue

        # 删除低质量节点
        for node_id in nodes_to_remove:
            self.graph.remove_node(node_id)
            if node_id in self.node_index:
                del self.node_index[node_id]

        if nodes_to_remove:
            logger.info(f"🧹 清理了 {len(nodes_to_remove)} 个低质量节点")

    def _recalculate_quality_scores(self):
        """重新计算质量分数"""
        for node_id in list(self.graph.nodes()):
            node_data = self.graph.nodes[node_id]['data']
            if not node_data:
                continue

            quality = self.quality_assessor.assess_node_quality(node_data, self.graph)
            node_data.quality_score = quality.overall_score

    def _update_global_stats(self):
        """更新全局统计"""
        self.stats['total_nodes'] = self.graph.number_of_nodes()
        self.stats['total_relations'] = self.graph.number_of_edges()

        # 重新计算质量分布
        self.stats['quality_distribution'] = defaultdict(int)
        for _node_id, node_data in self.graph.nodes(data=True):
            node = node_data['data']
            if node:
                quality_level = int(node.quality_score * 5)
                quality_level = max(1, min(5, quality_level))
                self.stats['quality_distribution'][quality_level] += 1

    def export_graph(self, output_path: str, format: str = 'json'):
        """导出知识图谱"""
        export_data = {
            'nodes': [],
            'relations': [],
            'metadata': {
                'export_time': datetime.now().isoformat(),
                'total_nodes': self.graph.number_of_nodes(),
                'total_relations': self.graph.number_of_edges(),
                'stats': self.stats
            }
        }

        # 导出节点
        for _node_id, node_data in self.graph.nodes(data=True):
            node = node_data['data']
            if node:
                export_data['nodes'].append({
                    'id': node.node_id,
                    'type': node.node_type.value,
                    'properties': node.properties,
                    'quality_score': node.quality_score,
                    'confidence': node.confidence,
                    'source': node.source,
                    'created_at': node.created_at.isoformat(),
                    'updated_at': node.updated_at.isoformat(),
                    'version': node.version,
                    'access_count': node.access_count
                })

        # 导出关系
        for source, target, edge_data in self.graph.edges(data=True):
            for _relation_id, relation in edge_data.items():
                if hasattr(relation, 'data'):
                    rel_data = relation.data
                else:
                    rel_data = relation

                if rel_data:
                    export_data['relations'].append({
                        'id': rel_data.relation_id,
                        'source': source,
                        'target': target,
                        'type': rel_data.relation_type.value,
                        'properties': rel_data.properties,
                        'weight': rel_data.weight,
                        'confidence': rel_data.confidence,
                        'quality_score': rel_data.quality_score,
                        'source': rel_data.source,
                        'created_at': rel_data.created_at.isoformat(),
                        'updated_at': rel_data.updated_at.isoformat(),
                        'version': rel_data.version,
                        'verification_count': rel_data.verification_count
                    })

        # 保存文件
        if format == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
        elif format == 'pickle':
            with open(output_path, 'wb') as f:
                pickle.dump(export_data, f)

        logger.info(f"📄 知识图谱已导出到: {output_path}")

    def get_quality_report(self) -> dict[str, Any]:
        """获取质量报告"""
        total_nodes = self.stats['total_nodes']
        if total_nodes == 0:
            return {}

        quality_distribution = self.stats['quality_distribution']

        # 计算平均质量分数
        total_quality_score = sum(level * count for level, count in quality_distribution.items())
        average_quality = total_quality_score / total_nodes / 5  # 归一化到0-1

        # 计算质量等级分布百分比
        quality_percentages = {}
        for level, count in quality_distribution.items():
            quality_percentages[f'level_{level}'] = (count / total_nodes) * 100

        return {
            'total_nodes': total_nodes,
            'total_relations': self.stats['total_relations'],
            'average_quality_score': average_quality,
            'quality_distribution': quality_distribution,
            'quality_percentages': quality_percentages,
            'last_update': self.stats['last_update'],
            'quality_thresholds': self.quality_thresholds
        }

async def main():
    """主函数"""
    logger.info('🗺️ 动态知识图谱系统测试')
    logger.info('Athena + 小诺 为您服务~ 💖')
    logger.info(str('='*50))

    # 初始化知识图谱管理器
    kg_manager = KnowledgeGraphManager()

    # 创建测试节点
    test_patents = [
        KnowledgeNode(
            node_id='patent_001',
            node_type=NodeType.PATENT,
            properties={
                'title': '基于人工智能的专利审查系统',
                'abstract': '本发明提供一种基于深度学习的智能专利审查方法',
                'patent_number': 'CN202512050001',
                'inventors': ['张三', '李四'],
                'company': 'AI科技公司',
                'filing_date': '2025-12-05',
                'technology_field': '人工智能'
            },
            confidence=0.95,
            source='test_data'
        ),
        KnowledgeNode(
            node_id='patent_002',
            node_type=NodeType.PATENT,
            properties={
                'title': '新型机械传动装置',
                'abstract': '本发明涉及一种改进的机械传动结构',
                'patent_number': 'CN202512050002',
                'inventors': ['王五'],
                'company': '机械制造公司',
                'filing_date': '2025-12-04',
                'technology_field': '机械工程'
            },
            confidence=0.88,
            source='test_data'
        ),
        KnowledgeNode(
            node_id='tech_001',
            node_type=NodeType.TECHNOLOGY,
            properties={
                'name': '深度学习',
                'category': '人工智能',
                'description': '基于神经网络的学习方法',
                'applications': ['图像识别', '自然语言处理', '专利审查']
            },
            confidence=0.92,
            source='test_data'
        ),
        KnowledgeNode(
            node_id='company_001',
            node_type=NodeType.COMPANY,
            properties={
                'name': 'AI科技公司',
                'country': '中国',
                'industry': '软件开发',
                'founded': '2018',
                'employees': 500
            },
            confidence=0.90,
            source='test_data'
        )
    ]

    # 创建测试关系
    test_relations = [
        KnowledgeRelation(
            relation_id='rel_001',
            source_id='patent_001',
            target_id='tech_001',
            relation_type=RelationType.USES,
            weight=0.9,
            confidence=0.85,
            source='test_data'
        ),
        KnowledgeRelation(
            relation_id='rel_002',
            source_id='patent_001',
            target_id='patent_002',
            relation_type=RelationType.CITES,
            weight=0.7,
            confidence=0.80,
            source='test_data'
        ),
        KnowledgeRelation(
            relation_id='rel_003',
            source_id='patent_001',
            target_id='company_001',
            relation_type=RelationType.DEVELOPED_BY,
            weight=1.0,
            confidence=0.95,
            source='test_data'
        )
    ]

    # 添加节点和关系
    logger.info("\n📝 添加测试节点...")
    for i, node in enumerate(test_patents, 1):
        success = kg_manager.add_node(node)
        logger.info(f"  {i}. 节点 {node.node_id}: {'✅' if success else '❌'}")

    logger.info("\n🔗 添加测试关系...")
    for i, relation in enumerate(test_relations, 1):
        success = kg_manager.add_relation(relation)
        logger.info(f"  {i}. 关系 {relation.relation_id}: {'✅' if success else '❌'}")

    # 搜索测试
    logger.info("\n🔍 搜索测试:")
    ai_patents = kg_manager.search_nodes(
        node_type=NodeType.PATENT,
        keywords=['人工智能', 'AI'],
        limit=5
    )
    logger.info(f"找到 {len(ai_patents)} 个AI相关专利:")
    for patent in ai_patents:
        logger.info(f"  - {patent.node_id}: {patent.properties.get('title', '')}")

    # 邻居节点测试
    logger.info("\n👥 邻居节点测试:")
    neighbors = kg_manager.get_node_neighbors('patent_001')
    logger.info(f"patent_001 的邻居节点 ({len(neighbors)} 个):")
    for neighbor_id, relation_type, weight in neighbors:
        logger.info(f"  - {neighbor_id}: {relation_type.value} (权重: {weight:.2f})")

    # 动态更新测试
    logger.info("\n🔄 动态更新测试:")
    update_data = {
        'source': 'test_update',
        'nodes': [
            {
                'id': 'patent_003',
                'type': 'patent',
                'properties': {
                    'title': '区块链专利管理系统',
                    'abstract': '基于区块链技术的专利管理解决方案',
                    'patent_number': 'CN202512050003'
                },
                'confidence': 0.87
            }
        ],
        'relations': [
            {
                'id': 'rel_004',
                'source': 'patent_003',
                'target': 'tech_001',
                'type': 'uses',
                'weight': 0.8,
                'confidence': 0.82
            }
        ]
    }

    kg_manager.dynamic_update(update_data)

    # 质量报告
    logger.info("\n📊 质量报告:")
    quality_report = kg_manager.get_quality_report()
    logger.info(f"总节点数: {quality_report.get('total_nodes', 0)}")
    logger.info(f"总关系数: {quality_report.get('total_relations', 0)}")
    logger.info(f"平均质量分数: {quality_report.get('average_quality_score', 0):.2f}")
    logger.info('质量分布:')
    for level, percentage in quality_report.get('quality_percentages', {}).items():
        logger.info(f"  等级 {level}: {percentage:.1f}%")

    # 导出知识图谱
    kg_manager.export_graph('test_knowledge_graph.json')
    logger.info("\n✅ 测试完成！知识图谱已导出到 test_knowledge_graph.json")

if __name__ == '__main__':
    asyncio.run(main())
