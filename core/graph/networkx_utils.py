#!/usr/bin/env python3
from __future__ import annotations
"""
NetworkX图分析工具模块
NetworkX Graph Analysis Utilities

提供统一的图操作接口,支持推理引擎、知识图谱、专利分析等场景
"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

try:

    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    nx = None

logger = logging.getLogger(__name__)


class GraphType(Enum):
    """图类型"""

    UNDIRECTED = "undirected"  # 无向图
    DIRECTED = "directed"  # 有向图
    MULTI = "multi"  # 多重图
    MULTI_DIRECTED = "multi_directed"  # 多重有向图


class CentralityMetric(Enum):
    """中心性指标类型"""

    DEGREE = "degree"  # 度中心性
    BETWEENNESS = "betweenness"  # 中介中心性
    CLOSENESS = "closeness"  # 接近中心性
    PAGERANK = "pagerank"  # PageRank
    EIGENVECTOR = "eigenvector"  # 特征向量中心性


@dataclass
class GraphStats:
    """图统计信息"""

    num_nodes: int = 0
    num_edges: int = 0
    is_connected: bool = False
    avg_degree: float = 0.0
    density: float = 0.0
    diameter: int = 0
    avg_clustering: float = 0.0
    num_communities: int = 0


@dataclass
class NodeInfo:
    """节点信息"""

    node_id: str
    attributes: dict[str, Any] = field(default_factory=dict)
    centrality_scores: dict[str, float] = field(default_factory=dict)
    community_id: Optional[int] = None


@dataclass
class EdgeInfo:
    """边信息"""

    source: str
    target: str
    weight: float = 1.0
    attributes: dict[str, Any] = field(default_factory=dict)


class NetworkXGraphManager:
    """NetworkX图管理器"""

    def __init__(self, graph_type: GraphType = GraphType.DIRECTED):
        """初始化图管理器

        Args:
            graph_type: 图类型
        """
        if not NETWORKX_AVAILABLE:
            raise RuntimeError("NetworkX未安装,请先安装: pip install networkx")

        self.graph_type = graph_type
        self.graph = self._create_graph(graph_type)
        self.logger = logging.getLogger(self.__class__.__name__)

    def _create_graph(self, graph_type: GraphType) -> Any:
        """创建图"""
        if graph_type == GraphType.UNDIRECTED:
            return nx.Graph()
        elif graph_type == GraphType.DIRECTED:
            return nx.DiGraph()
        elif graph_type == GraphType.MULTI:
            return nx.MultiGraph()
        elif graph_type == GraphType.MULTI_DIRECTED:
            return nx.MultiDiGraph()
        else:
            raise ValueError(f"不支持的图类型: {graph_type}")

    def add_node(self, node_id: str, **attributes) -> None:
        """添加节点

        Args:
            node_id: 节点ID
            **attributes: 节点属性
        """
        self.graph.add_node(node_id, **attributes)
        self.logger.debug(f"添加节点: {node_id}")

    def add_edge(self, source: str, target: str, weight: float = 1.0, **attributes) -> None:
        """添加边

        Args:
            source: 源节点
            target: 目标节点
            weight: 边权重
            **attributes: 边属性
        """
        self.graph.add_edge(source, target, weight=weight, **attributes)
        self.logger.debug(f"添加边: {source} -> {target} (权重: {weight})")

    def add_nodes_from(self, nodes: list[tuple[str, dict[str, Any]]) -> None]:
        """批量添加节点

        Args:
            nodes: 节点列表 [(node_id, attributes), ...]
        """
        self.graph.add_nodes_from(nodes)
        self.logger.debug(f"批量添加 {len(nodes)} 个节点")

    def add_edges_from(self, edges: list[tuple[str, str, float, dict[str, Any]]) -> None]:
        """批量添加边

        Args:
            edges: 边列表 [(source, target, weight, attributes), ...]
        """
        for edge in edges:
            if len(edge) == 4:
                source, target, weight, attrs = edge
                self.graph.add_edge(source, target, weight=weight, **attrs)
            elif len(edge) == 3:
                source, target, weight = edge
                self.graph.add_edge(source, target, weight=weight)
            elif len(edge) == 2:
                source, target = edge
                self.graph.add_edge(source, target)

        self.logger.debug(f"批量添加 {len(edges)} 条边")

    def get_node(self, node_id: str) -> NodeInfo | None:
        """获取节点信息

        Args:
            node_id: 节点ID

        Returns:
            节点信息,如果不存在返回None
        """
        if node_id not in self.graph:
            return None

        return NodeInfo(node_id=node_id, attributes=dict(self.graph.nodes[node_id]))

    def get_neighbors(self, node_id: str) -> list[str]:
        """获取节点的邻居

        Args:
            node_id: 节点ID

        Returns:
            邻居节点列表
        """
        if node_id not in self.graph:
            return []

        return list(self.graph.neighbors(node_id))

    def get_shortest_path(
        self, source: str, target: str, weight: str = "weight"
    ) -> Optional[list[str]]:
        """获取最短路径

        Args:
            source: 源节点
            target: 目标节点
            weight: 权重属性名

        Returns:
            最短路径节点列表,如果不存在路径返回None
        """
        try:
            if nx.is_directed(self.graph):
                path = nx.shortest_path(self.graph, source, target, weight=weight)
            else:
                path = nx.shortest_path(self.graph, source, target)
            return path
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def get_all_shortest_paths(
        self, source: str, cutoff: Optional[int] = None
    ) -> dict[str, list[str]]:
        """获取到所有节点的最短路径

        Args:
            source: 源节点
            cutoff: 最大路径长度

        Returns:
            目标节点到路径的映射
        """
        try:
            paths = nx.single_source_shortest_path(self.graph, source, cutoff=cutoff)
            return paths
        except nx.NodeNotFound:
            return {}

    def calculate_centrality(
        self, metric: CentralityMetric = CentralityMetric.PAGERANK, **kwargs
    ) -> dict[str, float]:
        """计算中心性指标

        Args:
            metric: 中心性指标类型
            **kwargs: 额外参数

        Returns:
            节点到中心性分数的映射
        """
        if metric == CentralityMetric.DEGREE:
            centrality = nx.degree_centrality(self.graph)
        elif metric == CentralityMetric.BETWEENNESS:
            centrality = nx.betweenness_centrality(self.graph, **kwargs)
        elif metric == CentralityMetric.CLOSENESS:
            centrality = nx.closeness_centrality(self.graph, **kwargs)
        elif metric == CentralityMetric.PAGERANK:
            centrality = nx.pagerank(self.graph, **kwargs)
        elif metric == CentralityMetric.EIGENVECTOR:
            centrality = nx.eigenvector_centrality(self.graph, **kwargs)
        else:
            raise ValueError(f"不支持的中心性指标: {metric}")

        return centrality

    def detect_communities(self, method: str = "greedy") -> list[set[str]]:
        """检测社区

        Args:
            method: 检测方法 ("greedy", "label_propagation")

        Returns:
            社区列表,每个社区是节点集合
        """
        if method == "greedy":
            communities = nx.community.greedy_modularity_communities(self.graph)
        elif method == "label_propagation":
            communities = nx.community.label_propagation_communities(self.graph)
        else:
            raise ValueError(f"不支持的社区检测方法: {method}")

        return [set(c) for c in communities]

    def get_graph_stats(self) -> GraphStats:
        """获取图统计信息

        Returns:
            图统计信息
        """
        stats = GraphStats(
            num_nodes=self.graph.number_of_nodes(), num_edges=self.graph.number_of_edges()
        )

        if stats.num_nodes > 0:
            # 连通性
            if nx.is_directed(self.graph):
                stats.is_connected = nx.is_weakly_connected(self.graph)
            else:
                stats.is_connected = nx.is_connected(self.graph)

            # 平均度
            degrees = [d for n, d in self.graph.degree()]
            stats.avg_degree = sum(degrees) / len(degrees) if degrees else 0.0

            # 密度
            stats.density = nx.density(self.graph)

            # 聚类系数
            if nx.is_directed(self.graph):
                # 对于有向图,使用无向版本计算聚类
                undirected = self.graph.to_undirected()
                stats.avg_clustering = nx.average_clustering(undirected)
            else:
                stats.avg_clustering = nx.average_clustering(self.graph)

            # 直径(只对连通图)
            if stats.is_connected and stats.num_nodes > 1:
                if nx.is_directed(self.graph):
                    stats.diameter = nx.diameter(self.graph.to_undirected())
                else:
                    stats.diameter = nx.diameter(self.graph)

            # 社区数量
            communities = self.detect_communities()
            stats.num_communities = len(communities)

        return stats

    def find_cycles(self, length: Optional[int] = None) -> list[list[str]]:
        """查找图中的环

        Args:
            length: 环的长度,None表示所有长度

        Returns:
            环列表,每个环是节点列表
        """
        if not nx.is_directed(self.graph):
            # 无向图
            cycles = list(nx.simple_cycles(self.graph.to_directed()))
        else:
            # 有向图
            cycles = list(nx.simple_cycles(self.graph))

        # 过滤长度
        if length is not None:
            cycles = [c for c in cycles if len(c) == length]

        return cycles

    def topological_sort(self) -> list[str]:
        """拓扑排序(仅适用于有向无环图)

        Returns:
            拓扑排序的节点列表
        """
        if not nx.is_directed(self.graph):
            raise ValueError("拓扑排序仅适用于有向图")

        return list(nx.topological_sort(self.graph))

    def export_to_dict(self) -> dict[str, Any]:
        """导出为字典格式

        Returns:
            图的字典表示
        """
        return {
            "graph_type": self.graph_type.value,
            "num_nodes": self.graph.number_of_nodes(),
            "num_edges": self.graph.number_of_edges(),
            "nodes": [
                {"id": node, "attributes": dict(self.graph.nodes[node])}
                for node in self.graph.nodes()
            ],
            "edges": [
                {
                    "source": source,
                    "target": target,
                    "weight": data.get("weight", 1.0),
                    "attributes": {k: v for k, v in data.items() if k != "weight"},
                }
                for source, target, data in self.graph.edges(data=True)
            ],
        }

    def export_to_json(self, filepath: str) -> Any:
        """导出为JSON文件

        Args:
            filepath: 文件路径
        """
        graph_dict = self.export_to_dict()

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(graph_dict, f, ensure_ascii=False, indent=2)

        self.logger.info(f"图已导出到: {filepath}")

    @staticmethod
    def import_from_dict(graph_dict: dict[str, Any]) -> "NetworkXGraphManager":
        """从字典导入图

        Args:
            graph_dict: 图的字典表示

        Returns:
            图管理器实例
        """
        graph_type = GraphType(graph_dict["graph_type"])
        manager = NetworkXGraphManager(graph_type)

        # 添加节点
        for node_data in graph_dict["nodes"]:
            manager.add_node(node_data["id"], **node_data["attributes"])

        # 添加边
        for edge_data in graph_dict["edges"]:
            manager.add_edge(
                edge_data["source"],
                edge_data["target"],
                weight=edge_data["weight"],
                **edge_data["attributes"],
            )

        return manager

    @staticmethod
    def import_from_json(filepath: str) -> "NetworkXGraphManager":
        """从JSON文件导入图

        Args:
            filepath: 文件路径

        Returns:
            图管理器实例
        """
        with open(filepath, encoding="utf-8") as f:
            graph_dict = json.load(f)

        return NetworkXGraphManager.import_from_dict(graph_dict)


def create_reasoning_rule_graph() -> NetworkXGraphManager:
    """创建推理规则图(用于专家规则引擎)

    Returns:
        图管理器实例
    """
    return NetworkXGraphManager(GraphType.DIRECTED)


def create_knowledge_graph() -> NetworkXGraphManager:
    """创建知识图谱(用于知识推理)

    Returns:
        图管理器实例
    """
    return NetworkXGraphManager(GraphType.DIRECTED)


def create_patent_citation_graph() -> NetworkXGraphManager:
    """创建专利引用图(用于专利分析)

    Returns:
        图管理器实例
    """
    return NetworkXGraphManager(GraphType.DIRECTED)


def create_reasoning_dependency_graph() -> NetworkXGraphManager:
    """创建推理依赖图(用于推理链分析)

    Returns:
        图管理器实例
    """
    return NetworkXGraphManager(GraphType.DIRECTED)


# 便捷函数
def get_networkx_version() -> str:
    """获取NetworkX版本

    Returns:
        版本字符串,如果未安装返回"未安装"
    """
    if NETWORKX_AVAILABLE:
        return nx.__version__
    return "未安装"


def is_networkx_available() -> bool:
    """检查NetworkX是否可用

    Returns:
        True如果可用,否则False
    """
    return NETWORKX_AVAILABLE


if __name__ == "__main__":
    # 测试代码
    if NETWORKX_AVAILABLE:
        print(f"✅ NetworkX 版本: {get_networkx_version()}")
        print()

        # 创建测试图
        graph = create_reasoning_rule_graph()

        # 添加节点
        graph.add_node("规则A", type="novelty", priority=1)
        graph.add_node("规则B", type="inventive", priority=2)
        graph.add_node("规则C", type="utility", priority=3)

        # 添加边
        graph.add_edge("规则A", "规则B", weight=0.8)
        graph.add_edge("规则B", "规则C", weight=0.9)

        # 获取统计信息
        stats = graph.get_graph_stats()
        print("📊 图统计信息:")
        print(f"  节点数: {stats.num_nodes}")
        print(f"  边数: {stats.num_edges}")
        print(f"  密度: {stats.density:.3f}")
        print(f"  连通: {stats.is_connected}")

        # 最短路径
        path = graph.get_shortest_path("规则A", "规则C")
        print(f"\n🔍 最短路径: {path}")

        # 中心性
        centrality = graph.calculate_centrality(CentralityMetric.PAGERANK)
        print("\n⭐ PageRank中心性:")
        for node, score in sorted(centrality.items(), key=lambda x: -x[1]):
            print(f"  {node}: {score:.3f}")

        print("\n✅ NetworkX工具模块测试通过")
    else:
        print("❌ NetworkX未安装")
