#!/usr/bin/env python3

"""
Dolphin + NetworkX 深度技术分析集成
Dolphin Document Parsing + NetworkX Graph Analysis Integration

这个模块展示了如何将Dolphin的高精度文档解析与NetworkX的图分析能力结合,
创建强大的专利技术深度分析系统。
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import networkx as nx

from core.ai.perception.dolphin_client import DolphinDocumentParser
from core.graph.networkx_utils import NetworkXGraphManager

logger = logging.getLogger(__name__)


@dataclass
class TechnicalEntity:
    """技术实体"""

    entity_id: str
    entity_type: str  # component, method, formula, table, reference
    text: str
    position: tuple[int, int, int, Optional[int]] = None  # (x1, y1, x2, y2)
    confidence: float = 1.0
    metadata: Optional[dict] = None


@dataclass
class TechnicalRelation:
    """技术关系"""

    source: str
    target: str
    relation_type: str  # depends_on, improves, implements, references, contains
    weight: float = 1.0
    metadata: Optional[dict] = None


class DolphinNetworkXAnalyzer:
    """
    Dolphin + NetworkX 深度技术分析器

    核心能力:
    1. 文档解析与技术实体提取
    2. 技术关系图构建
    3. 技术深度分析
    4. 技术演化路径识别
    5. 核心创新点发现
    """

    def __init__(
        self,
        dolphin_client: Optional[DolphinDocumentParser] = None,
        graph_manager: Optional[NetworkXGraphManager] = None,
    ):
        """
        初始化分析器

        Args:
            dolphin_client: Dolphin文档解析客户端
            graph_manager: NetworkX图管理器
        """
        self.dolphin_client = dolphin_client or DolphinDocumentParser()
        self.graph_manager = graph_manager or NetworkXGraphManager()
        self.technical_graph = nx.DiGraph()

    async def analyze_patent_technical_depth(
        self,
        document_path: str,
        build_knowledge_graph: bool = True,
    ) -> dict[str, Any]:
        """
        对专利文档进行技术深度分析

        分析流程:
        1. 使用Dolphin解析文档(高精度识别技术元素)
        2. 提取技术实体(组件、方法、公式、表格等)
        3. 识别技术关系(依赖、改进、实现等)
        4. 构建技术知识图谱
        5. 计算技术重要性指标
        6. 识别核心创新点

        Args:
            document_path: 专利文档路径
            build_knowledge_graph: 是否构建知识图谱

        Returns:
            技术深度分析结果
        """
        logger.info(f"🔬 开始技术深度分析: {document_path}")

        # 步骤1: 使用Dolphin高精度解析文档
        logger.info("📄 步骤1: Dolphin文档解析...")
        parse_result = await self.dolphin_client.parse_document(
            file_path=document_path,
            output_format="both",
        )

        # 步骤2: 提取技术实体
        logger.info("🧩 步骤2: 提取技术实体...")
        entities = await self._extract_technical_entities(parse_result)

        # 步骤3: 识别技术关系
        logger.info("🔗 步骤3: 识别技术关系...")
        relations = await self._identify_technical_relations(entities, parse_result)

        # 步骤4: 构建技术图谱
        logger.info("🕸️  步骤4: 构建技术知识图谱...")
        self.technical_graph.clear()
        for entity in entities:
            self.technical_graph.add_node(
                entity.entity_id,
                **{
                    "type": entity.entity_type,
                    "text": entity.text,
                    "position": entity.position,
                    "confidence": entity.confidence,
                    "metadata": entity.metadata or {},
                },
            )

        for relation in relations:
            self.technical_graph.add_edge(
                relation.source,
                relation.target,
                **{
                    "type": relation.relation_type,
                    "weight": relation.weight,
                    "metadata": relation.metadata or {},
                },
            )

        # 步骤5: 计算技术重要性指标
        logger.info("📊 步骤5: 计算技术重要性指标...")
        metrics = self._calculate_technical_metrics()

        # 步骤6: 识别核心创新点
        logger.info("💡 步骤6: 识别核心创新点...")
        innovations = self._identify_key_innovations(metrics)

        # 步骤7: 技术演化分析
        logger.info("📈 步骤7: 技术演化分析...")
        evolution = self._analyze_technical_evolution()

        result = {
            "document_path": document_path,
            "parse_result": parse_result,
            "entities_count": len(entities),
            "relations_count": len(relations),
            "metrics": metrics,
            "innovations": innovations,
            "evolution": evolution,
            "graph_stats": self._get_graph_statistics(),
        }

        logger.info(f"✅ 技术深度分析完成: {len(entities)}个实体, {len(relations)}个关系")

        return result

    async def _extract_technical_entities(
        self,
        parse_result: dict,
    ) -> list[TechnicalEntity]:
        """
        从Dolphin解析结果中提取技术实体

        提取类型:
        1. 组件/模块 (Component)
        2. 方法/算法 (Method)
        3. 公式/方程 (Formula)
        4. 表格数据 (Table)
        5. 参考文献引用 (Reference)
        """
        entities = []
        results = parse_result.get("results", [])

        for page_result in results:
            layouts = page_result.get("layouts", [])

            for layout in layouts:
                layout_type = layout.get("type", "")
                text = layout.get("text", "")
                bbox = layout.get("bbox", [])

                # 根据Dolphin识别的元素类型分类
                entity_type = self._classify_technical_entity(layout_type, text)

                if entity_type:
                    entity = TechnicalEntity(
                        entity_id=f"{entity_type}_{len(entities)}",
                        entity_type=entity_type,
                        text=text,
                        position=tuple(bbox) if bbox else None,
                        confidence=layout.get("confidence", 1.0),
                        metadata={"raw_type": layout_type, "page": page_result.get("page")},
                    )
                    entities.append(entity)

        return entities

    def _classify_technical_entity(self, layout_type: str, text: str) -> Optional[str]:
        """
        根据Dolphin布局类型和文本内容分类技术实体

        Dolphin支持的21种文档元素类型:
        - title, text, header, footer
        - table, formula, figure, list
        - reference, appendix, etc.
        """
        # 表格类实体
        if layout_type == "table":
            return "table"

        # 公式类实体
        if layout_type == "formula":
            return "formula"

        # 参考文献引用
        if layout_type == "reference" or self._is_reference_text(text):
            return "reference"

        # 组件/模块(从文本识别)
        if self._is_component_text(text):
            return "component"

        # 方法/算法(从文本识别)
        if self._is_method_text(text):
            return "method"

        # 技术描述
        if layout_type in ["text", "paragraph"]:
            return "description"

        return None

    def _is_reference_text(self, text: str) -> bool:
        """检测是否为参考文献引用"""
        patterns = [
            r"\[\d+\]",  # [1], [2], etc.
            r"\([^)]+\d{4}\)",  # (Author, 2024)
            r"et al\.",
            r"IEEE",
            r"ACM",
        ]
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)

    def _is_component_text(self, text: str) -> bool:
        """检测是否为组件/模块描述"""
        component_keywords = [
            "module",
            "component",
            "unit",
            "block",
            "circuit",
            "模块",
            "组件",
            "单元",
            "电路",
            "装置",
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in component_keywords)

    def _is_method_text(self, text: str) -> bool:
        """检测是否为方法/算法描述"""
        method_keywords = [
            "method",
            "algorithm",
            "approach",
            "technique",
            "方法",
            "算法",
            "方法",
            "技术",
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in method_keywords)

    async def _identify_technical_relations(
        self,
        entities: list[TechnicalEntity],
        parse_result: dict,
    ) -> list[TechnicalRelation]:
        """
        识别技术实体之间的关系

        关系类型:
        1. depends_on: 依赖关系
        2. improves: 改进关系
        3. implements: 实现关系
        4. references: 引用关系
        5. contains: 包含关系
        """
        relations = []
        _entity_map = {e.entity_id: e for e in entities}

        # 分析实体文本,识别关系线索
        for i, entity in enumerate(entities):
            for other_entity in entities[i + 1 :]:
                relation = self._detect_relation(entity, other_entity, parse_result)
                if relation:
                    relations.append(relation)

        return relations

    def _detect_relation(
        self,
        entity1: TechnicalEntity,
        entity2: TechnicalEntity,
        parse_result: dict,
    ) -> Optional[TechnicalRelation]:
        """检测两个实体之间的关系"""
        text1 = entity1.text.lower()
        _text2 = entity2.text.lower()

        # 引用关系
        if entity1.entity_type == "reference" or entity2.entity_type == "reference":
            return TechnicalRelation(
                source=entity1.entity_id,
                target=entity2.entity_id,
                relation_type="references",
                weight=0.5,
            )

        # 依赖关系线索
        dependency_patterns = ["based on", "using", "utilizing", "基于", "使用", "利用"]
        for pattern in dependency_patterns:
            if pattern in text1 and entity2.entity_type in ["component", "method"]:
                return TechnicalRelation(
                    source=entity1.entity_id,
                    target=entity2.entity_id,
                    relation_type="depends_on",
                    weight=0.8,
                )

        # 改进关系线索
        improvement_patterns = ["improves", "enhances", "optimizes", "改进", "增强", "优化"]
        for pattern in improvement_patterns:
            if pattern in text1:
                return TechnicalRelation(
                    source=entity1.entity_id,
                    target=entity2.entity_id,
                    relation_type="improves",
                    weight=0.9,
                )

        # 实现关系线索
        implementation_patterns = ["implements", "realizes", "实现", "实现"]
        for pattern in implementation_patterns:
            if pattern in text1:
                return TechnicalRelation(
                    source=entity1.entity_id,
                    target=entity2.entity_id,
                    relation_type="implements",
                    weight=0.7,
                )

        return None

    def _calculate_technical_metrics(self) -> dict[str, Any]:
        """
        计算技术重要性指标

        使用NetworkX图算法:
        1. PageRank: 核心技术识别
        2. Betweenness: 技术桥梁识别
        3. Closeness: 技术中心性
        4. HITS: 技术权威性
        5. Community Detection: 技术聚类
        """
        metrics = {}

        if len(self.technical_graph) == 0:
            return metrics

        # PageRank - 识别核心技术
        try:
            pagerank = nx.pagerank(self.technical_graph, weight="weight")
            metrics["pagerank"] = pagerank
        except Exception as e:
            logger.warning(f"PageRank计算失败: {e}")
            metrics["pagerank"]] = {}

        # Betweenness Centrality - 识别技术桥梁
        try:
            betweenness = nx.betweenness_centrality(self.technical_graph, weight="weight")
            metrics["betweenness"] = betweenness
        except Exception as e:
            logger.warning(f"Betweenness计算失败: {e}")
            metrics["betweenness"]] = {}

        # Closeness Centrality - 技术中心性
        try:
            closeness = nx.closeness_centrality(self.technical_graph)
            metrics["closeness"] = closeness
        except Exception as e:
            logger.warning(f"Closeness计算失败: {e}")
            metrics["closeness"]] = {}

        # HITS - 技术权威性和枢纽性
        try:
            hubs, authorities = nx.hits(self.technical_graph)
            metrics["hubs"] = hubs
            metrics["authorities"] = authorities
        except Exception as e:
            logger.warning(f"HITS计算失败: {e}")
            metrics["hubs"]] = {}
            metrics["authorities"]] = {}

        # Community Detection - 技术聚类
        try:
            communities = list(
                nx.community.greedy_modularity_communities(self.technical_graph.to_undirected())
            )
            metrics["communities"]] = [list(community) for community in communities]
        except Exception as e:
            logger.warning(f"Community Detection失败: {e}")
            metrics["communities"]] = []

        return metrics

    def _identify_key_innovations(self, metrics: dict) -> list[dict]:
        """
        识别核心创新点

        创新点特征:
        1. 高PageRank分数(核心技术)
        2. 高Betweenness分数(技术桥梁)
        3. 高Authority分数(权威技术)
        4. 独特技术社区
        """
        innovations = []

        pagerank = metrics.get("pagerank", {})
        authorities = metrics.get("authorities", {})
        betweenness = metrics.get("betweenness", {})

        # 找出高分节点
        for node_id in self.technical_graph.nodes():
            node_data = self.technical_graph.nodes[node_id]

            scores = {
                "pagerank": pagerank.get(node_id, 0),
                "authority": authorities.get(node_id, 0),
                "betweenness": betweenness.get(node_id, 0),
            }

            # 综合评分
            innovation_score = (
                scores["pagerank"] * 0.4 + scores["authority"] * 0.4 + scores["betweenness"] * 0.2
            )

            if innovation_score > 0.1:  # 阈值可调整
                innovations.append(
                    {
                        "entity_id": node_id,
                        "entity_type": node_data.get("type"),
                        "text": node_data.get("text"),
                        "innovation_score": innovation_score,
                        "scores": scores,
                    }
                )

        # 按创新分数排序
        innovations.sort(key=lambda x: x["innovation_score"], reverse=True)

        return innovations[:10]  # 返回Top 10创新点

    def _analyze_technical_evolution(self) -> dict:
        """
        分析技术演化路径

        识别:
        1. 技术依赖链
        2. 技术演化路径
        3. 关键技术节点
        """
        evolution = {}

        if len(self.technical_graph) == 0:
            return evolution

        # 最长路径(技术演化链)
        try:
            longest_path = nx.dag_longest_path(self.technical_graph)
            evolution["longest_path"] = longest_path
            evolution["evolution_chain_length"] = len(longest_path)
        except Exception as e:
            logger.warning(f"技术演化路径分析失败: {e}")
            evolution["longest_path"]] = []
            evolution["evolution_chain_length"] = 0

        # 强连通分量(技术循环依赖)
        try:
            sccs = list(nx.strongly_connected_components(self.technical_graph))
            evolution["strongly_connected_components"] = len(sccs)
        except Exception as e:
            logger.warning(f"强连通分量分析失败: {e}")
            evolution["strongly_connected_components"] = 0

        return evolution

    def _get_graph_statistics(self) -> dict:
        """获取图谱统计信息"""
        return {
            "nodes": len(self.technical_graph.nodes),
            "edges": len(self.technical_graph.edges),
            "density": nx.density(self.technical_graph),
            "is_directed": self.technical_graph.is_directed(),
            "is_connected": nx.is_weakly_connected(self.technical_graph),
        }

    async def compare_technical_depth(
        self,
        doc1_path: str,
        doc2_path: str,
    ) -> dict[str, Any]:
        """
        比较两个专利文档的技术深度

        Args:
            doc1_path: 文档1路径
            doc2_path: 文档2路径

        Returns:
            技术深度比较结果
        """
        logger.info(f"🔍 比较技术深度: {doc1_path} vs {doc2_path}")

        # 分析两个文档
        analysis1 = await self.analyze_patent_technical_depth(doc1_path)
        analysis2 = await self.analyze_patent_technical_depth(doc2_path)

        # 比较指标
        comparison = {
            "doc1": {
                "path": doc1_path,
                "entities": analysis1["entities_count"],
                "relations": analysis1["relations_count"],
                "innovations": len(analysis1["innovations"]),
                "top_innovation": analysis1["innovations"][0] if analysis1["innovations"] else None,
            },
            "doc2": {
                "path": doc2_path,
                "entities": analysis2["entities_count"],
                "relations": analysis2["relations_count"],
                "innovations": len(analysis2["innovations"]),
                "top_innovation": analysis2["innovations"][0] if analysis2["innovations"] else None,
            },
            "comparison": {
                "complexity_diff": analysis1["entities_count"] - analysis2["entities_count"],
                "innovation_diff": len(analysis1["innovations"]) - len(analysis2["innovations"]),
            },
        }

        return comparison

    def export_technical_graph(
        self,
        output_path: str,
        format: str = "gexf",
    ) -> None:
        """
        导出技术图谱

        Args:
            output_path: 输出路径
            format: 导出格式 (gexf, graphml, json)
        """
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        if format == "gexf":
            nx.write_gexf(self.technical_graph, output_path)
        elif format == "graphml":
            nx.write_graphml(self.technical_graph, output_path)
        elif format == "json":
            from networkx.readwrite import json_graph

            data = json_graph.node_link_data(self.technical_graph)
            import json

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ 技术图谱已导出: {output_path}")


# 便捷函数
async def analyze_patent_technical_depth(document_path: str) -> dict:
    """
    便捷函数:分析专利技术深度

    Args:
        document_path: 专利文档路径

    Returns:
        技术深度分析结果
    """
    analyzer = DolphinNetworkXAnalyzer()
    return await analyzer.analyze_patent_technical_depth(document_path)

