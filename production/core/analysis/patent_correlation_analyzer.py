#!/usr/bin/env python3
"""
专利智能关联分析系统
Patent Intelligent Correlation Analysis System

分析法律法规与决定书案例之间的关联关系,构建智能关联网络
"""

from __future__ import annotations
import json
import re
import sys
import time
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np

from core.logging_config import setup_logging

# 添加Athena平台路径
sys.path.append("/Users/xujian/Athena工作平台")

# 导入组件
from qdrant_client import QdrantClient
from qdrant_client.models import Filter

from core.nlp.bge_embedding_service import get_bge_service
from core.rag.hybrid_patent_rag_service import HybridPatentRAGService, PatentRAGQuery, QueryIntent

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


@dataclass
class LegalReference:
    """法律条文引用"""

    law_name: str
    article: str
    reference_count: int = 0
    decision_types: list[str] = field(default_factory=list)
    confidence_score: float = 0.0


@dataclass
class CaseCorrelation:
    """案例关联"""

    case_id: str
    case_type: str
    legal_references: list[str]
    similarity_score: float
    correlation_type: str  # direct_ref, similar_case, precedent
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CorrelationNetwork:
    """关联网络"""

    nodes: dict[str, dict[str, Any]] = field(default_factory=dict)
    edges: list[dict[str, Any]] = field(default_factory=list)
    clusters: dict[str, list[str]] = field(default_factory=dict)
    statistics: dict[str, Any] = field(default_factory=dict)


class PatentCorrelationAnalyzer:
    """专利关联分析器"""

    def __init__(self, config: dict[str, Any] | None = None):
        """初始化关联分析器"""
        self.name = "专利智能关联分析器"
        self.version = "1.0.0"

        # 配置
        self.config = config or {
            "similarity_threshold": 0.7,  # 相似度阈值
            "correlation_types": ["legal_ref", "case_similarity", "precedent"],
            "max_references_per_analysis": 100,
            "network_analysis_enabled": True,
            "output_directory": "/Users/xujian/Athena工作平台/correlation_reports",
        }

        # 初始化服务
        self.bge_service = None
        self.qdrant_client = QdrantClient(host="localhost", port=6333)
        self.hybrid_rag_service = HybridPatentRAGService()

        # 法律条文正则模式
        self.legal_ref_patterns = [
            r"《([^》]{2,50})》第([一二三四五六七八九十百千万0-9]+)条",
            r"《([^》]{2,50})》第([一二三四五六七八九十百千万0-9]+)条第([一二三四五六七八九十百千万0-9]+)款",
            r"《([^》]{2,50})》([0-9]+)条",
            r"([^《]*法)[^第]*第([一二三四五六七八九十百千万0-9]+)条",
        ]

        # 关联类型权重
        self.correlation_weights = {
            "legal_ref": 1.0,  # 直接法律条文引用
            "case_similarity": 0.8,  # 案例相似性
            "precedent": 0.9,  # 先例关系
            "semantic_similarity": 0.6,  # 语义相似性
        }

        logger.info(f"✅ {self.name} 初始化完成")

    async def _ensure_bge_service(self):
        """确保BGE服务已初始化"""
        if self.bge_service is None:
            self.bge_service = await get_bge_service()

    async def analyze_legal_references(self, limit: int = 1000) -> dict[str, Any]:
        """分析决定书中的法律条文引用"""
        logger.info(f"🔍 分析法律条文引用,样本限制: {limit}")

        await self._ensure_bge_service()

        # 从决定书集合中提取法律引用
        legal_refs = defaultdict(
            lambda: {"reference_count": 0, "decision_types": [], "cases": [], "contexts": []}
        )

        collections = ["patent_decisions_review", "patent_decisions_invalid"]

        for collection_name in collections:
            try:
                # 获取所有文档(实际中应该分批处理)
                scroll_result = self.qdrant_client.scroll(
                    collection_name=collection_name, limit=limit, with_payload=True
                )

                for point in scroll_result[0]:
                    content = point.payload.get("content", "")
                    metadata = point.payload.get("metadata", {})

                    # 提取法律引用
                    refs = self._extract_legal_references(content)

                    for ref in refs:
                        law_key = f"{ref['law_name']}第{ref['article']}条"
                        legal_refs[law_key]["reference_count"] += 1

                        if (
                            metadata.get("decision_type")
                            not in legal_refs[law_key]["decision_types"]
                        ):
                            legal_refs[law_key]["decision_types"].append(
                                metadata.get("decision_type")
                            )

                        legal_refs[law_key]["cases"].append(
                            {
                                "case_id": point.id,
                                "decision_type": metadata.get("decision_type"),
                                "patent_number": metadata.get("patent_number"),
                            }
                        )

                        # 保存上下文
                        context = self._extract_reference_context(content, ref)
                        if context:
                            legal_refs[law_key]["contexts"].append(context)

            except Exception as e:
                logger.error(f"❌ 分析集合 {collection_name} 失败: {e}")

        # 统计分析
        ref_statistics = self._analyze_reference_statistics(legal_refs)

        return {
            "legal_references": dict(legal_refs),
            "statistics": ref_statistics,
            "analysis_timestamp": datetime.now().isoformat(),
        }

    def _extract_legal_references(self, content: str) -> list[dict[str, str]]:
        """提取法律条文引用"""
        references = []

        for pattern in self.legal_ref_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if len(match) >= 2:
                    law_name = match[0].strip()
                    article = match[1].strip()

                    # 清理和标准化
                    law_name = self._normalize_law_name(law_name)
                    article = self._normalize_article_number(article)

                    if law_name and article:
                        references.append(
                            {
                                "law_name": law_name,
                                "article": article,
                                "raw_reference": f"《{law_name}》第{article}条",
                            }
                        )

        return references

    def _normalize_law_name(self, law_name: str) -> str:
        """标准化法律名称"""
        # 移除多余空格和标点
        law_name = re.sub(r"\s+", "", law_name)

        # 标准化常见法律名称
        law_mapping = {
            "中华人民共和国专利法": "专利法",
            "中华人民共和国专利法实施细则": "专利法实施细则",
            "专利法": "专利法",
            "专利法实施细则": "专利法实施细则",
        }

        return law_mapping.get(law_name, law_name)

    def _normalize_article_number(self, article: str) -> str:
        """标准化条款号"""
        # 转换中文数字
        chinese_numbers = {
            "一": "1",
            "二": "2",
            "三": "3",
            "四": "4",
            "五": "5",
            "六": "6",
            "七": "7",
            "八": "8",
            "九": "9",
            "十": "10",
        }

        for cn, num in chinese_numbers.items():
            article = article.replace(cn, num)

        return article

    def _extract_reference_context(self, content: str, ref: dict[str, str]) -> str:
        """提取引用上下文"""
        ref_text = ref["raw_reference"]
        ref_index = content.find(ref_text)

        if ref_index == -1:
            return ""

        # 提取前后各50个字符作为上下文
        max(0, ref_index - 50)
        end = min(len(content), ref_index + len(ref_text) + 50)

        return content[end]

    def _analyze_reference_statistics(
        self, legal_refs: dict[str, dict[str, Any]]) -> dict[str, Any]:
        """分析引用统计"""
        total_refs = len(legal_refs)
        ref_counts = [info["reference_count"] for info in legal_refs.values()]

        # 最常引用的法条
        top_refs = sorted(legal_refs.items(), key=lambda x: x[1]["reference_count"], reverse=True)[
            :20
        ]

        # 按法律类型分类
        law_types = defaultdict(list)
        for ref_key, info in legal_refs.items():
            law_name = ref_key.split("第")[0]
            law_types[law_name].append(info["reference_count"])

        return {
            "total_unique_references": total_refs,
            "total_reference_instances": sum(ref_counts),
            "avg_references_per_law": np.mean(ref_counts) if ref_counts else 0,
            "most_referenced_laws": [
                (ref_key, info["reference_count"]) for ref_key, info in top_refs
            ],
            "reference_distribution": {
                law_name: {
                    "count": len(refs),
                    "total_instances": sum(refs),
                    "avg_instances": np.mean(refs) if refs else 0,
                }
                for law_name, refs in law_types.items()
            },
        }

    async def find_similar_cases(self, query_case_id: str, limit: int = 10) -> dict[str, Any]:
        """查找相似案例"""
        logger.info(f"🔍 查找与案例 {query_case_id} 相似的案例")

        # 获取查询案例的内容
        query_case = await self._get_case_by_id(query_case_id)
        if not query_case:
            return {"error": f"未找到案例: {query_case_id}"}

        query_content = query_case["content"]
        query_metadata = query_case["metadata"]

        # 构建查询
        search_query = PatentRAGQuery(
            query=f"相似案例: {query_content[:200]}...",  # 使用前200字符作为查询
            document_types=[],  # 搜索所有类型
            intent=QueryIntent.CASE_REFERENCE,
            top_k=limit,
            filters={"case_id": {"ne": query_case_id}},  # 排除自己
        )

        # 执行搜索
        search_response = await self.hybrid_rag_service.search(search_query)

        # 分析相似性
        similar_cases = []
        for result in search_response.combined_results:
            similarity_score = await self._calculate_case_similarity(query_content, result.content)

            similar_case = {
                "case_id": result.id,
                "content_preview": result.content[:200],
                "metadata": result.metadata,
                "similarity_score": similarity_score,
                "correlation_type": self._determine_correlation_type(
                    similarity_score, query_metadata, result.metadata
                ),
            }
            similar_cases.append(similar_case)

        # 按相似度排序
        similar_cases.sort(key=lambda x: x["similarity_score"], reverse=True)

        return {
            "query_case_id": query_case_id,
            "query_case_metadata": query_metadata,
            "similar_cases": similar_cases[:limit],
            "analysis_timestamp": datetime.now().isoformat(),
        }

    async def _get_case_by_id(self, case_id: str) -> dict[str, Any] | None:
        """根据ID获取案例"""
        # 在各个集合中搜索
        collections = ["patent_decisions_review", "patent_decisions_invalid"]

        for collection_name in collections:
            try:
                search_result = self.qdrant_client.search(
                    collection_name=collection_name,
                    query_filter=Filter(must=["chunk_id"]),
                    limit=1,
                    with_payload=True,
                )

                if search_result:
                    point = search_result[0]
                    return {
                        "content": point.payload.get("content", ""),
                        "metadata": point.payload.get("metadata", {}),
                    }

            except Exception as e:
                logger.error(f"❌ 搜索案例失败 {collection_name}: {e}")

        return None

    async def _calculate_case_similarity(self, content1: str, content2: str) -> float:
        """计算案例相似度"""
        try:
            # 获取向量
            embedding_result = await self.bge_service.encode([content1, content2])

            if (
                isinstance(embedding_result.embeddings, list)
                and len(embedding_result.embeddings) >= 2
            ):
                vec1 = embedding_result.embeddings[0]
                vec2 = embedding_result.embeddings[1]

                if not isinstance(vec1, list):
                    vec1 = vec1.tolist()
                if not isinstance(vec2, list):
                    vec2 = vec2.tolist()

                # 计算余弦相似度
                vec1_np = np.array(vec1)
                vec2_np = np.array(vec2)

                if np.all(vec1_np == 0) or np.all(vec2_np == 0):
                    return 0.0

                dot_product = np.dot(vec1_np, vec2_np)
                norm1 = np.linalg.norm(vec1_np)
                norm2 = np.linalg.norm(vec2_np)

                if norm1 == 0 or norm2 == 0:
                    return 0.0

                return dot_product / (norm1 * norm2)

        except Exception as e:
            logger.error(f"❌ 计算相似度失败: {e}")

        return 0.0

    def _determine_correlation_type(
        self, similarity_score: float, metadata1: dict[str, Any], metadata2: dict[str, Any]
    ) -> str:
        """确定关联类型"""
        # 检查是否有相同专利号
        patent1 = metadata1.get("patent_number")
        patent2 = metadata2.get("patent_number")
        if patent1 and patent1 == patent2:
            return "same_patent"

        # 检查是否有相同法律引用
        refs1 = set(metadata1.get("legal_references", []))
        refs2 = set(metadata2.get("legal_references", []))
        if refs1 & refs2:
            return "common_legal_reference"

        # 基于相似度
        if similarity_score > 0.9:
            return "high_similarity"
        elif similarity_score > 0.8:
            return "medium_similarity"
        elif similarity_score > 0.7:
            return "low_similarity"
        else:
            return "weak_similarity"

    async def build_correlation_network(
        self, focus_legal_refs: list[str] = None, max_cases: int = 500
    ) -> CorrelationNetwork:
        """构建关联网络"""
        logger.info(f"🕸️ 构建关联网络,最大案例数: {max_cases}")

        if focus_legal_refs is None:
            # 获取最常引用的法条
            ref_analysis = await self.analyze_legal_references(1000)
            focus_legal_refs = [
                ref[0] for ref in ref_analysis["statistics"]["most_referenced_laws"][:10]
            ]

        network = CorrelationNetwork()

        # 添加法条节点
        for ref in focus_legal_refs:
            law_name, article = ref.split("第", 1)
            article = article.replace("条", "")

            network.nodes[ref] = {
                "type": "legal_reference",
                "law_name": law_name,
                "article": article,
                "label": ref,
                "weight": 0,
            }

        # 获取相关案例
        for ref in focus_legal_refs:
            related_cases = await self._find_cases_by_legal_reference(
                ref, max_cases // len(focus_legal_refs)
            )

            for case in related_cases:
                case_id = case["id"]

                # 添加案例节点
                if case_id not in network.nodes:
                    network.nodes[case_id] = {
                        "type": "case",
                        "label": f"案例 {case_id}",
                        "metadata": case["metadata"],
                        "weight": 0,
                    }

                # 添加关联边
                correlation = CaseCorrelation(
                    case_id=case_id,
                    case_type=case["metadata"].get("decision_type", "unknown"),
                    legal_references=[ref],
                    similarity_score=case.get("score", 0.5),
                    correlation_type="legal_ref",
                )

                edge = {
                    "source": ref,
                    "target": case_id,
                    "weight": self.correlation_weights["legal_ref"],
                    "correlation_type": "legal_ref",
                    "metadata": asdict(correlation),
                }
                network.edges.append(edge)

                # 更新节点权重
                network.nodes[ref]["weight"] += 1
                network.nodes[case_id]["weight"] += 1

        # 计算网络统计
        network.statistics = self._calculate_network_statistics(network)

        return network

    async def _find_cases_by_legal_reference(
        self, legal_ref: str, limit: int
    ) -> list[dict[str, Any]]:
        """根据法律引用查找案例"""
        # 构建查询
        query = PatentRAGQuery(
            query=legal_ref, document_types=[], intent=QueryIntent.CASE_REFERENCE, top_k=limit
        )

        # 执行搜索
        response = await self.hybrid_rag_service.search(query)

        cases = []
        for result in response.combined_results:
            if legal_ref in result.content:
                cases.append(
                    {
                        "id": result.id,
                        "content": result.content,
                        "metadata": result.metadata,
                        "score": result.score,
                    }
                )

        return cases

    def _calculate_network_statistics(self, network: CorrelationNetwork) -> dict[str, Any]:
        """计算网络统计"""
        if not self.config["network_analysis_enabled"]:
            return {"network_analysis_disabled": True}

        try:
            # 构建NetworkX图
            G = nx.Graph()

            # 添加节点
            for node_id, node_data in network.nodes.items():
                G.add_node(node_id, **node_data)

            # 添加边
            for edge in network.edges:
                G.add_edge(edge["source"], edge["target"], weight=edge["weight"])

            # 计算统计指标
            statistics = {
                "network_analysis_enabled": True,
                "total_nodes": G.number_of_nodes(),
                "total_edges": G.number_of_edges(),
                "density": nx.density(G),
                "is_connected": nx.is_connected(G),
                "average_clustering": nx.average_clustering(G),
                "degree_centrality": dict(nx.degree_centrality(G)),
                "betweenness_centrality": dict(nx.betweenness_centrality(G)),
                "eigenvector_centrality": dict(nx.eigenvector_centrality(G, max_iter=1000)),
            }

            # 社区检测
            try:
                communities = nx.community_louvain_communities(G)
                statistics["communities"] = [list(community) for community in communities]
                statistics["num_communities"] = len(communities)
            except Exception:
                statistics["communities"] = []
                statistics["num_communities"] = 0

            # 中心性最高的节点
            if statistics["degree_centrality"]:
                statistics["most_central_nodes"] = sorted(
                    statistics["degree_centrality"].items(), key=lambda x: x[1], reverse=True
                )[:10]

        except Exception as e:
            logger.error(f"❌ 网络分析失败: {e}")
            statistics = {"network_analysis_enabled": False, "error": str(e)}

        return statistics

    async def generate_correlation_report(self, output_file: str | None = None) -> dict[str, Any]:
        """生成关联分析报告"""
        logger.info("📊 生成关联分析报告")

        # 分析法律引用
        legal_ref_analysis = await self.analyze_legal_references(1000)

        # 构建关联网络
        correlation_network = await self.build_correlation_network()

        # 生成综合报告
        report = {
            "report_metadata": {
                "analyzer": self.name,
                "version": self.version,
                "generation_time": datetime.now().isoformat(),
            },
            "legal_reference_analysis": legal_ref_analysis,
            "correlation_network": {
                "nodes": correlation_network.nodes,
                "edges": correlation_network.edges,
                "statistics": correlation_network.statistics,
            },
            "recommendations": self._generate_recommendations(
                legal_ref_analysis, correlation_network
            ),
        }

        # 保存报告
        if output_file is None:
            timestamp = int(time.time())
            output_file = f"patent_correlation_analysis_report_{timestamp}.json"

        output_path = Path(self.config["output_directory"]) / output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ 关联分析报告已保存: {output_path}")
        return report

    def _generate_recommendations(
        self, legal_ref_analysis: dict[str, Any], network: CorrelationNetwork
    ) -> list[str]:
        """生成分析建议"""
        recommendations = []

        # 基于法律引用分析的建议
        if legal_ref_analysis["statistics"]["total_unique_references"] > 100:
            recommendations.append("📚 法律引用覆盖面广,建议构建专题知识库")

        top_law = (
            legal_ref_analysis["statistics"]["most_referenced_laws"][0]
            if legal_ref_analysis["statistics"]["most_referenced_laws"]
            else None
        )
        if top_law:
            recommendations.append(
                f"⚖️ 最常引用的法条是 '{top_law[0]}'(引用{top_law[1]}次),建议重点优化相关内容"
            )

        # 基于网络分析的建议
        if network.statistics.get("num_communities", 0) > 3:
            recommendations.append("🕸️ 案例形成多个关联社区,建议按社区分类展示")

        if network.statistics.get("is_connected", False):
            recommendations.append("🔗 案例关联网络连通性好,可以构建完整的知识图谱")
        else:
            recommendations.append("⚠️ 案例关联网络存在孤立节点,需要补充关联关系")

        # 处理建议
        total_refs = legal_ref_analysis["statistics"]["total_reference_instances"]
        if total_refs > 10000:
            recommendations.append("📈 引用数据量大,建议采用分布式处理和索引优化")
        else:
            recommendations.append("💾 可以采用全量分析策略")

        return recommendations


async def main():
    """主函数"""
    print("🚀 专利智能关联分析系统")
    print("=" * 60)

    analyzer = PatentCorrelationAnalyzer()

    try:
        # 生成综合关联分析报告
        report = await analyzer.generate_correlation_report()

        print("\n📊 关联分析报告:")
        print(
            f"   - 唯一法律引用: {report['legal_reference_analysis']['statistics']['total_unique_references']:,}"
        )
        print(
            f"   - 总引用实例: {report['legal_reference_analysis']['statistics']['total_reference_instances']:,}"
        )
        print(
            f"   - 网络节点数: {report['correlation_network']['statistics'].get('total_nodes', 0):,}"
        )
        print(
            f"   - 网络边数: {report['correlation_network']['statistics'].get('total_edges', 0):,}"
        )

        print("\n💡 分析建议:")
        for rec in report["recommendations"]:
            print(f"   • {rec}")

        # 演示相似案例查找
        print("\n🔍 相似案例查找演示:")

        # 这里需要一个实际的案例ID进行演示
        print("   (需要实际案例ID进行演示)")

    except Exception as e:
        logger.error(f"❌ 关联分析失败: {e}")
        print(f"❌ 分析失败: {e}")


# 入口点: @async_main装饰器已添加到main函数
