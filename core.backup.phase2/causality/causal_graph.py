#!/usr/bin/env python3
from __future__ import annotations
"""
因果图 (Causal Graph)
构建和管理因果关系图

作者: 小诺·双鱼公主
版本: v1.0.0
"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class CausalRelationType(str, Enum):
    """因果关型类型"""

    DIRECT = "direct"  # 直接因果
    INDIRECT = "indirect"  # 间接因果
    CONFOUNDING = "confounding"  # 混淆因子
    MEDIATING = "mediating"  # 中介变量
    COLLIDER = "collider"  # 碰撞节点


@dataclass
class CausalNode:
    """因果图节点"""

    node_id: str
    name: str
    node_type: str  # variable, outcome, treatment, confounder
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CausalEdge:
    """因果图边"""

    edge_id: str
    source: str  # 源节点ID
    target: str  # 目标节点ID
    relation_type: CausalRelationType
    strength: float = 1.0  # 因果强度 0-1
    confidence: float = 1.0  # 置信度 0-1
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CausalPath:
    """因果路径"""

    path_id: str
    nodes: list[str]  # 节点ID序列
    edges: list[str]  # 边ID序列
    total_strength: float = 0  # 路径总强度
    length: int = 0  # 路径长度


class CausalGraph:
    """
    因果图

    功能:
    1. 构建因果关系图
    2. 识别变量关系
    3. 验证因果关系
    4. 发现因果路径
    """

    def __init__(self, graph_id: str = "default"):
        self.graph_id = graph_id
        self.name = "因果图"
        self.version = "1.0.0"

        # 图结构
        self.nodes: dict[str, CausalNode] = {}
        self.edges: dict[str, CausalEdge] = {}
        self.adjacency: dict[str, set[str]] = {}  # 邻接表
        self.reverse_adjacency: dict[str, set[str]] = {}  # 反向邻接表

        # 统计信息
        self.stats = {
            "total_nodes": 0,
            "total_edges": 0,
            "direct_relations": 0,
            "indirect_relations": 0,
            "paths_discovered": 0,
        }

        logger.info(f"✅ {self.name} 初始化完成 (ID: {graph_id})")

    def add_node(
        self,
        node_id: str,
        name: str,
        node_type: str = "variable",
        metadata: dict[str, Any] | None = None,
    ) -> CausalNode:
        """
        添加节点

        Args:
            node_id: 节点ID
            name: 节点名称
            node_type: 节点类型
            metadata: 元数据

        Returns:
            创建的节点
        """
        node = CausalNode(node_id=node_id, name=name, node_type=node_type, metadata=metadata or {})

        self.nodes[node_id] = node
        self.adjacency[node_id] = set()
        self.reverse_adjacency[node_id] = set()
        self.stats["total_nodes"] += 1

        logger.debug(f"📍 添加节点: {name} ({node_id})")
        return node

    def add_edge(
        self,
        edge_id: str,
        source: str,
        target: str,
        relation_type: CausalRelationType = CausalRelationType.DIRECT,
        strength: float = 1.0,
        confidence: float = 1.0,
        metadata: dict[str, Any] | None = None,
    ) -> CausalEdge:
        """
        添加边(因果关系)

        Args:
            edge_id: 边ID
            source: 源节点ID
            target: 目标节点ID
            relation_type: 关系类型
            strength: 因果强度
            confidence: 置信度
            metadata: 元数据

        Returns:
            创建的边
        """
        # 确保节点存在
        if source not in self.nodes:
            self.add_node(source, source)
        if target not in self.nodes:
            self.add_node(target, target)

        edge = CausalEdge(
            edge_id=edge_id,
            source=source,
            target=target,
            relation_type=relation_type,
            strength=strength,
            confidence=confidence,
            metadata=metadata or {},
        )

        self.edges[edge_id] = edge
        self.adjacency[source].add(target)
        self.reverse_adjacency[target].add(source)
        self.stats["total_edges"] += 1

        if relation_type == CausalRelationType.DIRECT:
            self.stats["direct_relations"] += 1
        else:
            self.stats["indirect_relations"] += 1

        logger.debug(f"🔗 添加边: {source} -> {target} ({relation_type.value})")
        return edge

    def find_causal_paths(self, source: str, target: str, max_length: int = 5) -> list[CausalPath]:
        """
        查找因果路径

        Args:
            source: 源节点
            target: 目标节点
            max_length: 最大路径长度

        Returns:
            因果路径列表
        """
        if source not in self.nodes or target not in self.nodes:
            return []

        # BFS搜索路径
        paths = []
        queue = [(source, [source], [])]  # (当前节点, 节点路径, 边路径)
        visited = set()

        while queue:
            current, node_path, edge_path = queue.pop(0)

            if len(node_path) > max_length + 1:
                continue

            if current == target and len(node_path) > 1:
                # 计算路径强度
                total_strength = 1.0
                for edge_id in edge_path:
                    edge = self.edges[edge_id]
                    total_strength *= edge.strength

                path = CausalPath(
                    path_id=f"path_{source}_{target}_{len(paths)}",
                    nodes=node_path,
                    edges=edge_path,
                    total_strength=total_strength,
                    length=len(node_path) - 1,
                )
                paths.append(path)
                self.stats["paths_discovered"] += 1
                continue

            if current in visited:
                continue
            visited.add(current)

            # 探索邻接节点
            for neighbor in self.adjacency.get(current, set()):
                # 找到对应的边
                edge_id = self._find_edge(current, neighbor)
                if edge_id:
                    queue.append((neighbor, [*node_path, neighbor], [*edge_path, edge_id]))

        # 按强度排序
        paths.sort(key=lambda p: p.total_strength, reverse=True)
        return paths

    def _find_edge(self, source: str, target: str) -> str | None:
        """查找从source到target的边"""
        for edge_id, edge in self.edges.items():
            if edge.source == source and edge.target == target:
                return edge_id
        return None

    def get_causes(self, node_id: str) -> list[str]:
        """
        获取节点的直接原因

        Args:
            node_id: 节点ID

        Returns:
            原因节点ID列表
        """
        return list(self.reverse_adjacency.get(node_id, set()))

    def get_effects(self, node_id: str) -> list[str]:
        """
        获取节点的直接结果

        Args:
            node_id: 节点ID

        Returns:
            结果节点ID列表
        """
        return list(self.adjacency.get(node_id, set()))

    def identify_confounders(self, treatment: str, outcome: str) -> list[str]:
        """
        识别混淆因子

        混淆因子:同时影响处理和结果的变量

        Args:
            treatment: 处理变量
            outcome: 结果变量

        Returns:
            混淆因子列表
        """
        confounders = []

        # 获取处理的原因
        treatment_causes = set(self.get_causes(treatment))

        # 获取结果的原因
        outcome_causes = set(self.get_causes(outcome))

        # 找到共同的原因
        common = treatment_causes & outcome_causes

        for node_id in common:
            # 检查是否是混淆因子
            edges_to_treatment = self._find_edges_to(node_id, treatment)
            edges_to_outcome = self._find_edges_to(node_id, outcome)

            if edges_to_treatment and edges_to_outcome:
                confounders.append(node_id)

        return confounders

    def _find_edges_to(self, source: str, target: str) -> list[str]:
        """查找从source到target的所有边"""
        return [
            edge_id
            for edge_id, edge in self.edges.items()
            if edge.source == source and edge.target == target
        ]

    def identify_mediators(self, treatment: str, outcome: str) -> list[str]:
        """
        识别中介变量

        中介变量:位于处理和结果之间的变量

        Args:
            treatment: 处理变量
            outcome: 结果变量

        Returns:
            中介变量列表
        """
        mediators = []

        # 查找从treatment到outcome的路径
        paths = self.find_causal_paths(treatment, outcome, max_length=3)

        for path in paths:
            # 路径长度为2的中间节点是中介变量
            if path.length == 2 and len(path.nodes) == 3:
                mediators.append(path.nodes[1])

        return list(set(mediators))

    def identify_colliders(self, node_id: str) -> list[str]:
        """
        识别碰撞节点

        碰撞节点:两个边指向的同一个节点

        Args:
            node_id: 节点ID

        Returns:
            碰撞节点列表
        """
        colliders = []

        # 获取所有指向当前节点的边
        causes = self.get_causes(node_id)

        # 检查原因之间是否有边
        for i, cause1 in enumerate(causes):
            for cause2 in causes[i + 1 :]:
                # 如果cause1和cause2之间没有边,则node_id是碰撞节点
                if not self._has_edge(cause1, cause2) and not self._has_edge(cause2, cause1):
                    colliders.append(node_id)
                    break

        return list(set(colliders))

    def _has_edge(self, source: str, target: str) -> bool:
        """检查是否存在从source到target的边"""
        return target in self.adjacency.get(source, set())

    def validate_causal_relation(
        self, cause: str, effect: str, data: list[dict[str, Any]] | None = None
    ) -> dict[str, Any]:
        """
        验证因果关系

        Args:
            cause: 原因变量
            effect: 结果变量
            data: 观测数据

        Returns:
            验证结果
        """
        result = {
            "has_path": False,
            "path_count": 0,
            "paths": [],
            "strength": 0,
            "confidence": "low",
        }

        # 查找因果路径
        paths = self.find_causal_paths(cause, effect)

        if paths:
            result["has_path"] = True
            result["path_count"] = len(paths)
            result["paths"] = [
                {"nodes": path.nodes, "length": path.length, "strength": path.total_strength}
                for path in paths[:5]  # 返回前5条路径
            ]
            result["strength"] = paths[0].total_strength  # 使用最强路径的强度

            # 根据路径数量和强度评估置信度
            if result["path_count"] >= 3 and result["strength"] > 0.7:
                result["confidence"] = "high"
            elif result["path_count"] >= 1 and result["strength"] > 0.4:
                result["confidence"] = "medium"

        # 如果有数据,可以进行更详细的验证
        # 这里省略了统计检验的实现

        return result

    def get_graph_summary(self) -> dict[str, Any]:
        """获取图摘要"""
        return {
            "graph_id": self.graph_id,
            "name": self.name,
            "version": self.version,
            "stats": self.stats,
            "node_types": {
                node_type: sum(1 for n in self.nodes.values() if n.node_type == node_type)
                for node_type in ["variable", "outcome", "treatment", "confounder"]
            },
            "edge_types": {
                relation_type.value: sum(
                    1 for e in self.edges.values() if e.relation_type == relation_type
                )
                for relation_type in CausalRelationType
            },
            "highly_connected_nodes": self._get_highly_connected_nodes(top_n=5),
        }

    def _get_highly_connected_nodes(self, top_n: int = 5) -> list[dict[str, Any]]:
        """获取高度连接的节点"""
        node_connections = [
            {
                "node_id": node_id,
                "name": self.nodes[node_id].name,
                "out_degree": len(self.adjacency.get(node_id, set())),
                "in_degree": len(self.reverse_adjacency.get(node_id, set())),
                "total_degree": (
                    len(self.adjacency.get(node_id, set()))
                    + len(self.reverse_adjacency.get(node_id, set()))
                ),
            }
            for node_id in self.nodes
        ]

        # 按总连接数排序
        node_connections.sort(key=lambda x: x["total_degree"], reverse=True)
        return node_connections[:top_n]

    def export_json(self) -> str:
        """导出为JSON格式"""
        data = {
            "graph_id": self.graph_id,
            "nodes": [
                {
                    "id": node.node_id,
                    "name": node.name,
                    "type": node.node_type,
                    "metadata": node.metadata,
                }
                for node in self.nodes.values()
            ],
            "edges": [
                {
                    "id": edge.edge_id,
                    "source": edge.source,
                    "target": edge.target,
                    "type": edge.relation_type.value,
                    "strength": edge.strength,
                    "confidence": edge.confidence,
                    "metadata": edge.metadata,
                }
                for edge in self.edges.values()
            ],
        }
        return json.dumps(data, ensure_ascii=False, indent=2)


# 全局单例
_graph_instances: dict[str, CausalGraph] = {}


def get_causal_graph(graph_id: str = "default") -> CausalGraph:
    """获取因果图实例"""
    if graph_id not in _graph_instances:
        _graph_instances[graph_id] = CausalGraph(graph_id)
    return _graph_instances[graph_id]
