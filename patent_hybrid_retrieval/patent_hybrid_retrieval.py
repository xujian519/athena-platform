#!/usr/bin/env python3
"""
专利混合检索系统 - 基于Athena现有技术栈
Patent Hybrid Retrieval System - Based on Athena Existing Tech Stack

集成PostgreSQL全文搜索、Qdrant向量检索、Neo4j知识图谱的专利检索系统
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Any

# PostgreSQL连接
import psycopg2

sys.path.append(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "workspace",
        "src",
    )
)
import os

# Athena现有组件
import sys

from knowledge_graph.neo4j_manager import Neo4jManager
from psycopg2.extras import RealDictCursor

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.vector.qdrant_adapter import QdrantVectorAdapter

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """检索结果数据结构"""

    patent_id: str
    title: str
    abstract: str
    score: float
    source: str  # 'fulltext', 'vector', 'kg'
    evidence: str  # 匹配的文本片段或路径
    metadata: dict[str, Any]


class PatentHybridRetrieval:
    """专利混合检索系统 - 基于Athena技术栈"""

    def __init__(self):
        """初始化检索系统组件"""
        logger.info("初始化专利混合检索系统...")

        # 初始化数据库连接
        self._init_postgresql()

        # 初始化向量检索（Qdrant）
        self.vector_adapter = QdrantVectorAdapter()

        # 初始化知识图谱（Neo4j）
        self.kg_manager = Neo4jManager()

        # 检索权重配置
        self.weights = {
            "fulltext": 0.4,  # PostgreSQL全文搜索
            "vector": 0.5,  # Qdrant向量检索
            "kg": 0.1,  # Neo4j知识图谱
        }

        logger.info("混合检索系统初始化完成")

    def _init_postgresql(self):
        """初始化PostgreSQL连接"""
        try:
            # 使用环境变量配置
            from config.database import get_patent_connection_params, get_patent_db_config

            db_config = get_patent_db_config().get_config()
            conn_params = get_patent_connection_params()

            # 设置游标工厂
            from psycopg2.extras import RealDictCursor

            conn_params["cursor_factory"] = RealDictCursor

            self.pg_conn = psycopg2.connect(**conn_params)
            self.pg_conn.autocommit = False
            logger.info(
                f"PostgreSQL连接成功: {db_config.host}:{db_config.port}/{db_config.database}"
            )
        except Exception as e:
            logger.error(f"PostgreSQL连接失败: {e}")
            self.pg_conn = None

    async def search(self, query: str, top_k: int = 20) -> list[RetrievalResult]:
        """
        混合检索主函数

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            检索结果列表
        """
        logger.info(f"开始混合检索，查询: {query}")

        # 并行执行三种检索
        tasks = [
            self._fulltext_search(query, top_k * 2),
            self._vector_search(query, top_k * 2),
            self._kg_search(query, top_k),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        ft_results = results[0] if not isinstance(results[0], Exception) else []
        vector_results = results[1] if not isinstance(results[1], Exception) else []
        kg_results = results[2] if not isinstance(results[2], Exception) else []

        # 融合排序
        final_results = self._merge_and_rerank(ft_results, vector_results, kg_results, top_k)

        logger.info(f"检索完成，返回 {len(final_results)} 条结果")

        return final_results

    async def _fulltext_search(self, query: str, top_k: int) -> list[RetrievalResult]:
        """PostgreSQL全文搜索"""
        if not self.pg_conn:
            logger.warning("PostgreSQL未连接，跳过全文搜索")
            return []

        results = []
        try:
            with self.pg_conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 使用PostgreSQL的全文搜索功能
                sql = """
                SELECT
                    p.patent_id,
                    p.title,
                    p.abstract,
                    ts_rank_cd(
                        setweight(to_tsvector('chinese', p.title), 'A') ||
                        setweight(to_tsvector('chinese', p.abstract), 'B') ||
                        setweight(to_tsvector('chinese', p.claims), 'C'),
                        plainto_tsquery('chinese', %s)
                    ) as rank,
                    ts_headline('chinese', p.title, plainto_tsquery('chinese', %s)) as title_highlight,
                    ts_headline('chinese', p.abstract, plainto_tsquery('chinese', %s)) as abstract_highlight
                FROM patents p
                WHERE
                    to_tsvector('chinese', p.title || ' ' || p.abstract || ' ' || p.claims) @@ plainto_tsquery('chinese', %s)
                ORDER BY rank DESC
                LIMIT %s
                """

                cur.execute(sql, (query, query, query, query, top_k))
                rows = cur.fetchall()

                for row in rows:
                    results.append(
                        RetrievalResult(
                            patent_id=row["patent_id"],
                            title=row["title"],
                            abstract=row["abstract"],
                            score=float(row["rank"]),
                            source="fulltext",
                            evidence=f"标题: {row['title_highlight']}<br>摘要: {row['abstract_highlight']}",
                            metadata={
                                "highlight": {
                                    "title": row["title_highlight"],
                                    "abstract": row["abstract_highlight"],
                                }
                            },
                        )
                    )

        except Exception as e:
            logger.error(f"全文搜索出错: {e}")

        return results

    async def _vector_search(self, query: str, top_k: int) -> list[RetrievalResult]:
        """Qdrant向量检索"""
        # 这里需要查询向量，简化处理
        # 实际应用中需要先将query转换为向量
        try:
            # 假设已有query向量（实际需要调用embedding模型）
            query_vector = [0.1] * 1024  # 示例向量

            # 搜索专利向量
            results = await self.vector_adapter.search_vectors(
                collection_type="patents", query_vector=query_vector, limit=top_k, threshold=0.3
            )

            retrieval_results = []
            for item in results:
                # 获取专利详细信息（需要从PostgreSQL查询）
                patent_info = await self._get_patent_info(item["id"])
                if patent_info:
                    retrieval_results.append(
                        RetrievalResult(
                            patent_id=item["id"],
                            title=patent_info.get("title", ""),
                            abstract=patent_info.get("abstract", ""),
                            score=float(item["score"]),
                            source="vector",
                            evidence=f"向量相似度: {item['score']:.3f}",
                            metadata={"vector_id": item["id"], "vector_score": item["score"]},
                        )
                    )

            return retrieval_results

        except Exception as e:
            logger.error(f"向量搜索出错: {e}")
            return []

    async def _kg_search(self, query: str, top_k: int) -> list[RetrievalResult]:
        """Neo4j知识图谱检索"""
        try:
            # 提取查询中的关键技术术语（简化处理）
            keywords = self._extract_keywords(query)

            # 构建Cypher查询
            cypher = """
            MATCH (p:Patent)-[:HAS_TECHNOLOGY]->(t:Technology)
            WHERE any(keyword in $keywords WHERE toLower(t.name) CONTAINS toLower(keyword))
            WITH p, count(*) as tech_count
            OPTIONAL MATCH (p)-[:CITES]->(cited:Patent)
            OPTIONAL MATCH (citing:Patent)-[:CITES]->(p)
            RETURN
                p.patent_id as patent_id,
                p.title as title,
                p.abstract as abstract,
                tech_count,
                count(DISTINCT cited) + count(DISTINCT citing) as citation_count,
                [t in [(p)-[:HAS_TECHNOLOGY]->(t:Technology) | t.name]
                 WHERE any(keyword in $keywords WHERE toLower(t) CONTAINS toLower(keyword))][..3] as matched_tech
            ORDER BY tech_count DESC, citation_count DESC
            LIMIT $limit
            """

            # 执行查询
            records = await self.kg_manager.execute_cypher(
                cypher, parameters={"keywords": keywords, "limit": top_k}
            )

            results = []
            for record in records:
                # 计算综合分数
                score = record["tech_count"] * 0.7 + record["citation_count"] * 0.3

                results.append(
                    RetrievalResult(
                        patent_id=record["patent_id"],
                        title=record.get("title", ""),
                        abstract=record.get("abstract", ""),
                        score=score,
                        source="kg",
                        evidence=f"匹配技术: {', '.join(record['matched_tech'])}",
                        metadata={
                            "tech_count": record["tech_count"],
                            "citation_count": record["citation_count"],
                            "matched_tech": record["matched_tech"],
                        },
                    )
                )

            return results

        except Exception as e:
            logger.error(f"知识图谱搜索出错: {e}")
            return []

    def _extract_keywords(self, text: str) -> list[str]:
        """提取关键词（简化版）"""
        # 实际应用中应使用NLP工具
        # 这里简单切分
        import re

        words = re.findall(r"\b\w+\b", text)
        # 过滤停用词和短词
        stop_words = {"的", "是", "在", "和", "与", "或", "等", "及", "基于", "包括"}
        keywords = [w for w in words if len(w) > 1 and w not in stop_words]
        return keywords[:5]  # 返回前5个关键词

    async def _get_patent_info(self, patent_id: str) -> dict[str, Any | None]:
        """从PostgreSQL获取专利详细信息"""
        if not self.pg_conn:
            return None

        try:
            with self.pg_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT patent_id, title, abstract, claims FROM patents WHERE patent_id = %s",
                    (patent_id,),
                )
                return dict(cur.fetchone()) if cur.rowcount > 0 else None
        except Exception:
            return None

    def _merge_and_rerank(
        self,
        ft_results: list[RetrievalResult],
        vector_results: list[RetrievalResult],
        kg_results: list[RetrievalResult],
        top_k: int,
    ) -> list[RetrievalResult]:
        """融合和重排序检索结果"""
        # 收集所有结果
        all_patents = {}

        # 合并全文搜索结果
        for result in ft_results:
            patent_id = result.patent_id
            if patent_id not in all_patents:
                all_patents[patent_id] = {
                    "patent": result,
                    "scores": {"fulltext": 0, "vector": 0, "kg": 0},
                    "sources": [],
                }
            all_patents[patent_id]["scores"]["fulltext"] = result.score
            all_patents[patent_id]["sources"].append(f"FT:{result.score:.3f}")

        # 合并向量搜索结果
        for result in vector_results:
            patent_id = result.patent_id
            if patent_id not in all_patents:
                all_patents[patent_id] = {
                    "patent": result,
                    "scores": {"fulltext": 0, "vector": 0, "kg": 0},
                    "sources": [],
                }
            all_patents[patent_id]["scores"]["vector"] = result.score
            all_patents[patent_id]["sources"].append(f"VEC:{result.score:.3f}")

        # 合并知识图谱结果
        for result in kg_results:
            patent_id = result.patent_id
            if patent_id not in all_patents:
                all_patents[patent_id] = {
                    "patent": result,
                    "scores": {"fulltext": 0, "vector": 0, "kg": 0},
                    "sources": [],
                }
            all_patents[patent_id]["scores"]["kg"] = result.score
            all_patents[patent_id]["sources"].append(f"KG:{result.score:.3f}")

        # 计算加权总分
        final_results = []
        for patent_id, data in all_patents.items():
            scores = data["scores"]
            total_score = (
                scores["fulltext"] * self.weights["fulltext"]
                + scores["vector"] * self.weights["vector"]
                + scores["kg"] * self.weights["kg"]
            )

            patent = data["patent"]
            patent.score = total_score
            patent.metadata["sources"] = data["sources"]
            patent.metadata["score_breakdown"] = {
                "fulltext": scores["fulltext"],
                "vector": scores["vector"],
                "kg": scores["kg"],
                "weights": self.weights,
            }

            final_results.append(patent)

        # 排序并返回Top-K
        final_results.sort(key=lambda x: x.score, reverse=True)
        return final_results[:top_k]

    async def get_patent_details(self, patent_id: str) -> dict[str, Any | None]:
        """获取专利详细信息"""
        patent_info = await self._get_patent_info(patent_id)
        if not patent_info:
            return None

        # 获取知识图谱信息
        kg_info = await self._get_patent_kg_info(patent_id)

        # 合并信息
        details = {
            "basic_info": patent_info,
            "knowledge_graph": kg_info,
            "retrieval_stats": {"last_accessed": datetime.now().isoformat()},
        }

        return details

    async def _get_patent_kg_info(self, patent_id: str) -> dict[str, Any]:
        """获取专利在知识图谱中的信息"""
        try:
            cypher = """
            MATCH (p:Patent {patent_id: $patent_id})
            OPTIONAL MATCH (p)-[:HAS_TECHNOLOGY]->(t:Technology)
            OPTIONAL MATCH (p)-[:CITES]->(cited:Patent)
            OPTIONAL MATCH (citing:Patent)-[:CITES]->(p)
            OPTIONAL MATCH (p)-[:BELONGS_TO]->(ipc:IPC)
            RETURN
                collect(DISTINCT t.name) as technologies,
                count(DISTINCT cited) as citations_made,
                count(DISTINCT citing) as citations_received,
                collect(DISTINCT ipc.code) as ipc_codes
            """

            result = await self.kg_manager.execute_cypher(
                cypher, parameters={"patent_id": patent_id}
            )

            return result[0] if result else {}

        except Exception as e:
            logger.error(f"获取专利知识图谱信息出错: {e}")
            return {}

    def get_system_stats(self) -> dict[str, Any]:
        """获取系统统计信息"""
        stats = {
            "components": {
                "postgresql": self.pg_conn is not None,
                "qdrant": True,  # 已初始化
                "neo4j": True,  # 已初始化
            },
            "weights": self.weights,
            "last_updated": datetime.now().isoformat(),
        }

        # 获取各组件的详细统计
        try:
            if self.pg_conn:
                with self.pg_conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM patents")
                    stats["patent_count"] = cur.fetchone()[0]
        except Exception:
            stats["patent_count"] = "Unknown"

        return stats


# 测试函数
async def test_patent_retrieval():
    """测试专利混合检索系统"""
    logger.info(str("\n" + "=" * 80))
    logger.info("🔍 专利混合检索系统测试 (基于Athena技术栈)")
    logger.info(str("=" * 80))

    # 初始化系统
    retrieval_system = PatentHybridRetrieval()

    # 显示系统状态
    logger.info("\n📊 系统状态:")
    stats = retrieval_system.get_system_stats()
    for key, value in stats.items():
        logger.info(f"  {key}: {value}")

    # 测试查询
    test_queries = ["深度学习图像识别", "基于区块链的数据存储", "自然语言处理技术"]

    for query in test_queries:
        logger.info(f"\n🔎 查询: {query}")
        logger.info(str("-" * 60))

        try:
            results = await retrieval_system.search(query, top_k=5)

            if results:
                for i, result in enumerate(results, 1):
                    logger.info(f"\n{i}. 专利ID: {result.patent_id}")
                    logger.info(f"   标题: {result.title}")
                    logger.info(f"   综合评分: {result.score:.4f}")
                    logger.info(f"   数据来源: {result.metadata['sources']}")
                    logger.info(f"   证据: {result.evidence[:100]}...")
            else:
                logger.info("  暂无相关结果")

        except Exception as e:
            logger.info(f"  检索出错: {e}")

    logger.info("\n✅ 测试完成！")


if __name__ == "__main__":
    asyncio.run(test_patent_retrieval())
