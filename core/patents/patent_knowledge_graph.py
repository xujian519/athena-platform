from __future__ import annotations
"""
专利技术知识图谱模块
使用NetworkX构建专利技术分析的知识图谱

核心功能:
1. 单文档技术分析:问题-特征-效果三元组构建
2. 特征关系建模:特征之间的依赖、组合、替代关系
3. 跨文档技术比对:新颖性、创造性自动化分析
4. 图谱可视化:技术关系网络展示

作者:Athena平台团队
版本:1.0.0
日期:2026-01-07
"""

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import matplotlib
import matplotlib.pyplot as plt
import networkx as nx

# 设置中文字体支持
matplotlib.rc_params["font.sans-serif"] = ["Arial Unicode MS", "SimHei", "STHeiti"]
matplotlib.rc_params["axes.unicode_minus"] = False


class NodeType(Enum):
    """节点类型枚举"""

    PROBLEM = "problem"  # 技术问题
    FEATURE = "feature"  # 技术特征
    EFFECT = "effect"  # 技术效果
    DOCUMENT = "document"  # 文档(专利/论文)
    CLAIM = "claim"  # 权利要求
    EMBODIMENT = "embodiment"  # 实施例


class RelationType(Enum):
    """关系类型枚举"""

    # 文档内部关系
    SOLVES = "solves"  # 问题-特征:特征解决问题
    ACHIEVES = "achieves"  # 特征-效果:特征实现效果
    DEPENDS_ON = "depends_on"  # 特征依赖:特征A依赖特征B
    COMBINED_WITH = "combined_with"  # 特征组合:特征A与B组合
    ALTERNATIVE_TO = "alternative_to"  # 特征替代:特征A替代B
    INCLUDES = "includes"  # 文档包含:文档包含权利要求

    # 跨文档关系
    SIMILAR_TO = "similar_to"  # 特征相似:特征A与B相似
    IMPROVES_UPON = "improves_upon"  # 改进关系:A改进B
    DIFFERENT_FROM = "different_from"  # 区别关系:A与B不同
    SAME_AS = "same_as"  # 相同关系:A与B相同
    PRIOR_ART = "prior_art"  # 现有技术:A是B的现有技术


@dataclass
class TechnicalTriple:
    """技术三元组:问题-特征-效果"""

    problem: str  # 技术问题
    features: list[str]  # 技术特征列表
    effect: str  # 技术效果
    source_claim: int | None = None  # 来源权利要求号

    def __str__(self) -> str:
        return f"[{self.problem}] + {self.features} → [{self.effect}]"


@dataclass
class FeatureRelation:
    """特征关系"""

    source_feature: str  # 源特征
    target_feature: str  # 目标特征
    relation_type: RelationType  # 关系类型
    strength: float = 1.0  # 关系强度(0-1)
    description: str | None = None  # 关系描述


@dataclass
class DocumentAnalysis:
    """文档技术分析结果"""

    document_id: str  # 文档ID(申请号/公开号)
    document_type: str  # 文档类型(专利/论文)
    document_name: str  # 文档名称
    triples: list[TechnicalTriple] = field(default_factory=list)  # 三元组列表
    feature_relations: list[FeatureRelation] = field(default_factory=list)  # 特征关系
    ipc_classifications: list[str] = field(default_factory=list)  # IPC分类号

    def get_all_features(self) -> set[str]:
        """获取所有技术特征"""
        features = set()
        for triple in self.triples:
            features.update(triple.features)
        return features

    def get_all_problems(self) -> set[str]:
        """获取所有技术问题"""
        return {triple.problem for triple in self.triples}

    def get_all_effects(self) -> set[str]:
        """获取所有技术效果"""
        return {triple.effect for triple in self.triples}


class PatentKnowledgeGraph:
    """
    专利技术知识图谱主类

    核心功能:
    1. 构建单文档技术图谱
    2. 跨文档技术比对
    3. 新颖性/创造性分析
    4. 图谱可视化
    """

    def __init__(self):
        """初始化知识图谱"""
        # 使用有向多重图(支持节点间多种关系)
        self.graph = nx.MultiDiGraph()

        # 文档分析结果缓存
        self.document_analyses: dict[str, DocumentAnalysis] = {}

        # 图统计信息
        self.stats = {
            "total_nodes": 0,
            "total_edges": 0,
            "document_count": 0,
            "problem_count": 0,
            "feature_count": 0,
            "effect_count": 0,
        }

    # ==================== 文档分析功能 ====================

    def analyze_document(
        self,
        document_id: str,
        document_name: str,
        triples: list[TechnicalTriple],
        feature_relations: list[FeatureRelation] | None = None,
        ipc_classifications: list[str] | None = None,
        document_type: str = "专利",
    ) -> DocumentAnalysis:
        """
        分析单个文档,构建技术知识图谱

        Args:
            document_id: 文档ID
            document_name: 文档名称
            triples: 技术三元组列表
            feature_relations: 特征关系列表
            ipc_classifications: IPC分类号
            document_type: 文档类型

        Returns:
            DocumentAnalysis: 文档分析结果
        """
        # 创建文档分析对象
        analysis = DocumentAnalysis(
            document_id=document_id,
            document_name=document_name,
            triples=triples,
            feature_relations=feature_relations or [],
            ipc_classifications=ipc_classifications or [],
            document_type=document_type,
        )

        # 缓存分析结果
        self.document_analyses[document_id] = analysis

        # 添加文档节点
        self._add_document_node(analysis)

        # 添加三元组到图谱
        self._add_triples_to_graph(analysis, document_id)

        # 添加特征关系到图谱
        self._add_feature_relations_to_graph(analysis, document_id)

        # 更新统计信息
        self._update_stats()

        return analysis

    def _add_document_node(self, analysis: DocumentAnalysis) -> Any:
        """添加文档节点"""
        self.graph.add_node(
            analysis.document_id,
            node_type=NodeType.DOCUMENT,
            name=analysis.document_name,
            doc_type=analysis.document_type,
            ipc=analysis.ipc_classifications,
        )
        self.stats["document_count"] += 1

    def _add_triples_to_graph(self, analysis: DocumentAnalysis, document_id: str) -> Any:
        """将三元组添加到图谱"""
        for idx, triple in enumerate(analysis.triples):
            # 创建唯一ID
            problem_id = f"{document_id}_P{idx}"
            effect_id = f"{document_id}_E{idx}"

            # 添加问题节点
            self.graph.add_node(
                problem_id,
                node_type=NodeType.PROBLEM,
                name=triple.problem,
                source_document=document_id,
                source_claim=triple.source_claim,
            )

            # 添加效果节点
            self.graph.add_node(
                effect_id,
                node_type=NodeType.EFFECT,
                name=triple.effect,
                source_document=document_id,
            )

            # 添加特征节点
            feature_ids = []
            for f_idx, feature in enumerate(triple.features):
                feature_id = f"{document_id}_F{idx}_{f_idx}"
                feature_ids.append(feature_id)

                self.graph.add_node(
                    feature_id,
                    node_type=NodeType.FEATURE,
                    name=feature,
                    source_document=document_id,
                    source_claim=triple.source_claim,
                )

                # 添加:特征->问题(解决关系)
                self.graph.add_edge(
                    feature_id,
                    problem_id,
                    relation_type=RelationType.SOLVES,
                    source_document=document_id,
                )

                # 添加:特征->效果(实现关系)
                self.graph.add_edge(
                    feature_id,
                    effect_id,
                    relation_type=RelationType.ACHIEVES,
                    source_document=document_id,
                )

            # 添加:文档->问题(包含关系)
            self.graph.add_edge(document_id, problem_id, relation_type=RelationType.INCLUDES)

            # 添加:文档->效果(包含关系)
            self.graph.add_edge(document_id, effect_id, relation_type=RelationType.INCLUDES)

            self.stats["problem_count"] += 1
            self.stats["feature_count"] += len(triple.features)
            self.stats["effect_count"] += 1

    def _add_feature_relations_to_graph(self, analysis: DocumentAnalysis, document_id: str):
        """添加特征关系到图谱"""
        for relation in analysis.feature_relations:
            # 查找特征节点ID
            source_id = self._find_feature_node(document_id, relation.source_feature)
            target_id = self._find_feature_node(document_id, relation.target_feature)

            if source_id and target_id:
                self.graph.add_edge(
                    source_id,
                    target_id,
                    relation_type=relation.relation_type,
                    strength=relation.strength,
                    description=relation.description,
                    source_document=document_id,
                )

    def _find_feature_node(self, document_id: str, feature_name: str) -> str | None:
        """查找特征节点ID"""
        for node in self.graph.nodes():
            node_data = self.graph.nodes[node]
            if (
                node_data.get("node_type") == NodeType.FEATURE
                and node_data.get("source_document") == document_id
                and node_data.get("name") == feature_name
            ):
                return node
        return None

    def _update_stats(self) -> Any:
        """更新统计信息"""
        self.stats["total_nodes"] = self.graph.number_of_nodes()
        self.stats["total_edges"] = self.graph.number_of_edges()

    # ==================== 跨文档比对功能 ====================

    def compare_documents(
        self, doc1_id: str, doc2_id: str, similarity_threshold: float = 0.7
    ) -> dict[str, Any]:
        """
        对比两个文档的技术差异

        分析维度:
        1. 特征相似度
        2. 问题相似度
        3. 效果相似度
        4. 新颖性分析
        5. 创造性分析

        Args:
            doc1_id: 文档1 ID(目标专利)
            doc2_id: 文档2 ID(对比文献)
            similarity_threshold: 相似度阈值

        Returns:
            对比分析结果字典
        """
        if doc1_id not in self.document_analyses or doc2_id not in self.document_analyses:
            raise ValueError("文档未在图谱中,请先分析文档")

        doc1 = self.document_analyses[doc1_id]
        doc2 = self.document_analyses[doc2_id]

        # 1. 提取特征集合
        features1 = doc1.get_all_features()
        features2 = doc2.get_all_features()

        # 2. 计算特征相似度
        feature_similarity = self._calculate_feature_similarity(features1, features2)

        # 3. 识别相同特征
        common_features = features1 & features2

        # 4. 识别区别特征
        unique_features1 = features1 - features2
        unique_features2 = features2 - features1

        # 5. 问题和效果对比
        problems1 = doc1.get_all_problems()
        problems2 = doc2.get_all_problems()
        effects1 = doc1.get_all_effects()
        effects2 = doc2.get_all_effects()

        common_problems = problems1 & problems2
        unique_problems1 = problems1 - problems2
        unique_effects1 = effects1 - effects2

        # 6. 新颖性分析
        novelty_analysis = self._analyze_novelty(
            doc1_id, doc2_id, common_features, unique_features1
        )

        # 7. 创造性分析
        inventiveness_analysis = self._analyze_inventiveness(
            doc1_id, doc2_id, unique_features1, unique_problems1, unique_effects1
        )

        # 8. 添加跨文档关系到图谱
        self._add_cross_document_relations(doc1_id, doc2_id, common_features, unique_features1)

        return {
            "summary": {
                "doc1_name": doc1.document_name,
                "doc2_name": doc2.document_name,
                "feature_similarity": round(feature_similarity, 3),
                "common_feature_count": len(common_features),
                "unique_feature_doc1": len(unique_features1),
                "unique_feature_doc2": len(unique_features2),
            },
            "feature_comparison": {
                "common_features": list(common_features),
                "unique_features_doc1": list(unique_features1),
                "unique_features_doc2": list(unique_features2),
            },
            "problem_comparison": {
                "common_problems": list(common_problems),
                "unique_problems_doc1": list(unique_problems1),
            },
            "effect_comparison": {
                "common_effects": list(effects1 & effects2),
                "unique_effects_doc1": list(unique_effects1),
            },
            "novelty_analysis": novelty_analysis,
            "inventiveness_analysis": inventiveness_analysis,
        }

    def _calculate_feature_similarity(self, features1: set[str], features2: set[str]) -> float:
        """计算特征相似度(Jaccard系数)"""
        if not features1 or not features2:
            return 0.0

        intersection = len(features1 & features2)
        union = len(features1 | features2)

        return intersection / union if union > 0 else 0.0

    def _analyze_novelty(
        self, doc1_id: str, doc2_id: str, common_features: set[str], unique_features: set[str]
    ) -> dict[str, Any]:
        """
        新颖性分析

        判断标准:
        - 如果存在区别技术特征,则具有新颖性
        - 区别特征数量越多,新颖性越强
        """
        novelty_score = len(unique_features) / max(len(common_features) + len(unique_features), 1)

        novelty_level = "高" if novelty_score > 0.3 else "中" if novelty_score > 0.1 else "低"

        return {
            "novelty_score": round(novelty_score, 3),
            "novelty_level": novelty_level,
            "distinguishing_features": list(unique_features),
            "conclusion": f"相对于{doc2_id},{doc1_id}{'具有' if unique_features else '不具有'}新颖性",
        }

    def _analyze_inventiveness(
        self,
        doc1_id: str,
        doc2_id: str,
        unique_features: set[str],
        unique_problems: set[str],
        unique_effects: set[str],
    ) -> dict[str, Any]:
        """
        创造性分析

        判断标准(三步法):
        1. 确定最接近的现有技术
        2. 确定区别技术特征和实际解决的技术问题
        3. 判断是否显而易见
        """
        # 技术问题判断
        problem_solved = len(unique_problems) > 0

        # 技术效果判断
        effect_improved = len(unique_effects) > 0

        # 特征组合判断
        feature_combination = len(unique_features) > 1

        # 创造性评分
        inventiveness_indicators = 0
        if problem_solved:
            inventiveness_indicators += 1
        if effect_improved:
            inventiveness_indicators += 1
        if feature_combination:
            inventiveness_indicators += 1

        inventiveness_score = inventiveness_indicators / 3.0
        inventiveness_level = (
            "高" if inventiveness_score > 0.6 else "中" if inventiveness_score > 0.3 else "低"
        )

        return {
            "inventiveness_score": round(inventiveness_score, 3),
            "inventiveness_level": inventiveness_level,
            "problem_solved": problem_solved,
            "effect_improved": effect_improved,
            "feature_combination": feature_combination,
            "conclusion": f"相对于{doc2_id},{doc1_id}{'具有' if inventiveness_score > 0.3 else '不具有'}突出的实质性特点和显著的进步",
        }

    def _add_cross_document_relations(
        self, doc1_id: str, doc2_id: str, common_features: set[str], unique_features: set[str]
    ):
        """添加跨文档关系到图谱"""
        # 添加文档间关系
        self.graph.add_edge(
            doc2_id,
            doc1_id,
            relation_type=RelationType.PRIOR_ART,
            description=f"{doc2_id}是{doc1_id}的对比文献",
        )

        # 添加特征相似关系
        for feature in common_features:
            node1 = self._find_feature_node(doc1_id, feature)
            node2 = self._find_feature_node(doc2_id, feature)

            if node1 and node2:
                self.graph.add_edge(
                    node1,
                    node2,
                    relation_type=RelationType.SAME_AS,
                    strength=1.0,
                    description="相同技术特征",
                )

        # 添加特征区别关系
        for feature in unique_features:
            node1 = self._find_feature_node(doc1_id, feature)
            if node1:
                self.graph.add_edge(
                    doc1_id,
                    node1,
                    relation_type=RelationType.DIFFERENT_FROM,
                    description="区别技术特征",
                )

    # ==================== 图谱查询功能 ====================

    def get_document_features(self, document_id: str) -> set[str]:
        """获取文档的所有技术特征"""
        if document_id not in self.document_analyses:
            return set()
        return self.document_analyses[document_id].get_all_features()

    def get_feature_path(self, feature1: str, feature2: str) -> list[str]:
        """获取两个特征之间的最短路径"""
        try:
            return nx.shortest_path(self.graph, feature1, feature2)
        except nx.NetworkXNoPath:
            return []

    def find_similar_documents(self, document_id: str, top_k: int = 5) -> list[tuple[str, float]]:
        """查找与指定文档最相似的其他文档"""
        if document_id not in self.document_analyses:
            return []

        target_features = self.get_document_features(document_id)
        similarities = []

        for doc_id, analysis in self.document_analyses.items():
            if doc_id == document_id:
                continue

            other_features = analysis.get_all_features()
            similarity = self._calculate_feature_similarity(target_features, other_features)
            similarities.append((doc_id, similarity))

        # 按相似度排序
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    # ==================== 图谱可视化功能 ====================

    def visualize_graph(
        self,
        output_path: str | None = None,
        figsize: tuple[int, int] = (16, 12),
        show_labels: bool = True,
        highlight_nodes: list[str] | None = None,
    ):
        """
        可视化知识图谱

        Args:
            output_path: 输出文件路径(None则显示)
            figsize: 图形大小
            show_labels: 是否显示标签
            highlight_nodes: 需要高亮的节点列表
        """
        plt.figure(figsize=figsize)

        # 使用spring layout布局
        pos = nx.spring_layout(self.graph, k=1, iterations=50, seed=42)

        # 按节点类型绘制
        node_colors = []
        node_sizes = []

        for node in self.graph.nodes():
            node_type = self.graph.nodes[node].get("node_type")

            if node_type == NodeType.DOCUMENT:
                node_colors.append("#FF6B6B")  # 红色
                node_sizes.append(1000)
            elif node_type == NodeType.PROBLEM:
                node_colors.append("#4ECDC4")  # 青色
                node_sizes.append(600)
            elif node_type == NodeType.FEATURE:
                node_colors.append("#45B7D1")  # 蓝色
                node_sizes.append(800)
            elif node_type == NodeType.EFFECT:
                node_colors.append("#96CEB4")  # 绿色
                node_sizes.append(600)
            else:
                node_colors.append("#DDDDDD")  # 灰色
                node_sizes.append(400)

        # 绘制节点
        nx.draw_networkx_nodes(
            self.graph, pos, node_color=node_colors, node_size=node_sizes, alpha=0.8
        )

        # 绘制边
        nx.draw_networkx_edges(
            self.graph, pos, edge_color="#AAAAAA", width=1, alpha=0.5, arrows=True, arrowsize=20
        )

        # 绘制标签
        if show_labels:
            labels = {}
            for node in self.graph.nodes():
                node_name = self.graph.nodes[node].get("name", node)
                # 截断过长的标签
                if len(node_name) > 15:
                    node_name = node_name[:12] + "..."
                labels[node] = node_name

            nx.draw_networkx_labels(self.graph, pos, labels, font_size=8, font_family="sans-serif")

        # 高亮指定节点
        if highlight_nodes:
            nx.draw_networkx_nodes(
                self.graph,
                pos,
                nodelist=highlight_nodes,
                node_color="#FFD93D",  # 黄色高亮
                node_size=1000,
                alpha=0.9,
            )

        # 添加图例
        from matplotlib.patches import Patch

        legend_elements = [
            Patch(facecolor="#FF6B6B", label="文档"),
            Patch(facecolor="#4ECDC4", label="技术问题"),
            Patch(facecolor="#45B7D1", label="技术特征"),
            Patch(facecolor="#96CEB4", label="技术效果"),
        ]
        plt.legend(handles=legend_elements, loc="upper left")

        plt.title("专利技术知识图谱", fontsize=16, fontweight="bold")
        plt.axis("off")
        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            print(f"图谱已保存到: {output_path}")
        else:
            plt.show()

        plt.close()

    def visualize_comparison(self, doc1_id: str, doc2_id: str, output_path: str | None = None):
        """
        可视化两个文档的对比图

        Args:
            doc1_id: 文档1 ID
            doc2_id: 文档2 ID
            output_path: 输出文件路径
        """
        # 提取子图
        doc1_nodes = [
            n for n in self.graph.nodes() if self.graph.nodes[n].get("source_document") == doc1_id
        ]
        doc2_nodes = [
            n for n in self.graph.nodes() if self.graph.nodes[n].get("source_document") == doc2_id
        ]

        all_nodes = doc1_nodes + doc2_nodes + [doc1_id, doc2_id]

        if not all_nodes:
            print("未找到相关节点")
            return

        subgraph = self.graph.subgraph(all_nodes)

        plt.figure(figsize=(14, 10))

        # 布局
        pos = nx.spring_layout(subgraph, k=1.5, iterations=50, seed=42)

        # 绘制文档1的节点(蓝色)
        doc1_feature_nodes = [
            n for n in doc1_nodes if self.graph.nodes[n].get("node_type") == NodeType.FEATURE
        ]
        doc1_other_nodes = [n for n in doc1_nodes if n not in doc1_feature_nodes]

        nx.draw_networkx_nodes(
            subgraph,
            pos,
            nodelist=doc1_feature_nodes,
            node_color="#45B7D1",
            node_size=800,
            label=f"{doc1_id} 特征",
            alpha=0.8,
        )

        nx.draw_networkx_nodes(
            subgraph, pos, nodelist=doc1_other_nodes, node_color="#45B7D1", node_size=400, alpha=0.5
        )

        # 绘制文档2的节点(红色)
        doc2_feature_nodes = [
            n for n in doc2_nodes if self.graph.nodes[n].get("node_type") == NodeType.FEATURE
        ]
        doc2_other_nodes = [n for n in doc2_nodes if n not in doc2_feature_nodes]

        nx.draw_networkx_nodes(
            subgraph,
            pos,
            nodelist=doc2_feature_nodes,
            node_color="#FF6B6B",
            node_size=800,
            label=f"{doc2_id} 特征",
            alpha=0.8,
        )

        nx.draw_networkx_nodes(
            subgraph, pos, nodelist=doc2_other_nodes, node_color="#FF6B6B", node_size=400, alpha=0.5
        )

        # 绘制边
        nx.draw_networkx_edges(subgraph, pos, edge_color="#CCCCCC", width=1, alpha=0.5, arrows=True)

        # 绘制标签
        labels = {n: self.graph.nodes[n].get("name", n)[:15] for n in subgraph.nodes()}
        nx.draw_networkx_labels(subgraph, pos, labels, font_size=8)

        plt.legend(fontsize=12)
        plt.title(f"技术对比图谱: {doc1_id} vs {doc2_id}", fontsize=14, fontweight="bold")
        plt.axis("off")
        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            print(f"对比图已保存到: {output_path}")
        else:
            plt.show()

        plt.close()

    # ==================== 导出功能 ====================

    def export_graph_json(self, output_path: str) -> Any:
        """将图谱导出为JSON格式"""
        data = nx.node_link_data(self.graph)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"图谱已导出到: {output_path}")

    def export_graph_gexf(self, output_path: str) -> Any:
        """将图谱导出为GEXF格式(可用Gephi打开)"""
        nx.write_gexf(self.graph, output_path)
        print(f"图谱已导出到: {output_path}")

    def get_statistics(self) -> dict[str, Any]:
        """获取图谱统计信息"""
        return {
            **self.stats,
            "avg_degree": sum(dict(self.graph.degree()).values())
            / max(self.graph.number_of_nodes(), 1),
            "is_connected": nx.is_weakly_connected(self.graph),
            "number_of_weakly_connected_components": nx.number_weakly_connected_components(
                self.graph
            ),
        }

    def print_summary(self) -> Any:
        """打印图谱摘要"""
        stats = self.get_statistics()

        print("=" * 60)
        print("专利技术知识图谱统计摘要")
        print("=" * 60)
        print(f"文档数量: {stats['document_count']}")
        print(f"技术问题数: {stats['problem_count']}")
        print(f"技术特征数: {stats['feature_count']}")
        print(f"技术效果数: {stats['effect_count']}")
        print(f"总节点数: {stats['total_nodes']}")
        print(f"总边数: {stats['total_edges']}")
        print(f"平均度数: {stats['avg_degree']:.2f}")
        print(f"图谱连通性: {'连通' if stats['is_connected'] else '不连通'}")
        print(f"连通分量数: {stats['number_of_weakly_connected_components']}")
        print("=" * 60)


# ==================== 便捷函数 ====================


def create_triple_from_text(
    problem: str | None = None, features_text: str | None = None, effect: str | None = None, source_claim: int | None = None
) -> TechnicalTriple:
    """
    从文本创建技术三元组

    Args:
        problem: 技术问题文本
        features_text: 技术特征文本(可用逗号或分号分隔多个特征)
        effect: 技术效果文本
        source_claim: 来源权利要求号

    Returns:
        TechnicalTriple对象
    """
    # 分割特征文本
    separators = [",", ";", ",", ";", "\n"]
    features = [f.strip() for f in features_text.split(separators[0])]
    for sep in separators[1:]:
        new_features = []
        for f in features:
            new_features.extend([x.strip() for x in f.split(sep)])
        features = new_features

    # 过滤空特征
    features = [f for f in features if f]

    return TechnicalTriple(
        problem=problem, features=features, effect=effect, source_claim=source_claim
    )


if __name__ == "__main__":
    # 示例:使用知识图谱进行专利分析

    # 1. 创建知识图谱
    pkg = PatentKnowledgeGraph()

    # 2. 分析目标专利(CN217373946U)
    target_triples = [
        create_triple_from_text(
            problem="多个打印头共用色带时色带和打印物易被污染",
            features_text="色带盒、隔离件、打印孔、打印通道、色带通道臂远端",
            effect="防止色带和打印物被污染,实现多打印头共用",
            source_claim=1,
        ),
        create_triple_from_text(
            problem="打印通道空间小、打印操作受限",
            features_text="隔离件设置在色带通道臂远端之间、隔离件设置打印孔",
            effect="增大打印通道空间,便于打印操作",
            source_claim=2,
        ),
    ]

    target_relations = [
        FeatureRelation(
            source_feature="隔离件",
            target_feature="打印孔",
            relation_type=RelationType.COMBINED_WITH,
            description="隔离件上设置打印孔实现功能组合",
        )
    ]

    pkg.analyze_document(
        document_id="CN217373946U",
        document_name="一种色带盒及打印机",
        triples=target_triples,
        feature_relations=target_relations,
        ipc_classifications=["B41J 32/00"],
        document_type="实用新型",
    )

    # 3. 分析对比专利(CN97207103.2)
    prior_art_triples = [
        create_triple_from_text(
            problem="储墨盒内的墨水可能泄漏或混合",
            features_text="隔离板、储墨盒盒体、墨水腔",
            effect="分隔储墨盒内部空间,防止墨水泄漏混合",
            source_claim=1,
        )
    ]

    pkg.analyze_document(
        document_id="CN97207103.2",
        document_name="隔离式打印机色带盒",
        triples=prior_art_triples,
        ipc_classifications=["B41J 32/00"],
        document_type="实用新型",
    )

    # 4. 对比分析
    comparison = pkg.compare_documents("CN217373946U", "CN97207103.2")

    print("\n" + "=" * 60)
    print("专利对比分析结果")
    print("=" * 60)
    print(f"\n特征相似度: {comparison['summary']['feature_similarity']}")
    print(f"共同特征数: {comparison['summary']['common_feature_count']}")
    print(f"目标专利区别特征: {comparison['summary']['unique_feature_doc1']}")

    print("\n新颖性分析:")
    print(f"  新颖性评分: {comparison['novelty_analysis']['novelty_score']}")
    print(f"  新颖性等级: {comparison['novelty_analysis']['novelty_level']}")
    print(f"  结论: {comparison['novelty_analysis']['conclusion']}")

    print("\n创造性分析:")
    print(f"  创造性评分: {comparison['inventiveness_analysis']['inventiveness_score']}")
    print(f"  创造性等级: {comparison['inventiveness_analysis']['inventiveness_level']}")
    print(f"  结论: {comparison['inventiveness_analysis']['conclusion']}")

    # 5. 打印图谱统计
    pkg.print_summary()

    # 6. 可视化
    pkg.visualize_comparison(
        "CN217373946U", "CN97207103.2", output_path="/tmp/patent_comparison_graph.png"
    )

    print("\n✅ 知识图谱分析完成!")
