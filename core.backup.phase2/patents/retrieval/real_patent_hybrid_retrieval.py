#!/usr/bin/env python3
"""
真实专利数据库适配器
Real Patent Database Adapter
用于适配本地PostgreSQL中的200多G专利数据
"""

import asyncio
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional, List, Dict
from pathlib import Path

# 配置日志（必须在最前面）
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 数据库连接
import psycopg2
from psycopg2.extras import RealDictCursor

# 添加patent-platform路径
project_root = Path(__file__).parent.parent.parent
workspace_src = project_root / "patent-platform" / "workspace" / "src"
if str(workspace_src) not in sys.path:
    sys.path.insert(0, str(workspace_src))

try:
    from core.knowledge_graph.neo4j_manager import Neo4jManager
except ImportError:
    # 如果导入失败，设置为None（知识图谱功能可选）
    Neo4jManager = None
    logger.warning("⚠️ Neo4jManager不可用，知识图谱功能将被禁用")

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.database import get_patent_db_config, test_patent_database
from core.vector.qdrant_adapter import QdrantVectorAdapter

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PatentDocument:
    """专利文档数据结构 - 真实数据版本"""

    patent_id: str
    title: str
    abstract: str
    claims: str
    description: str
    ipc_codes: List[str]
    publication_date: str
    applicant: str
    inventors: List[str]
    citations: List[str]
    family_id: Optional[str] = None
    priority_date: Optional[str] = None
    legal_status: Optional[str] = None


@dataclass
class RetrievalResult:
    """检索结果数据结构"""

    patent_id: str
    title: str
    abstract: str
    score: float
    source: str  # 'fulltext', 'vector', 'kg'
    evidence: str  # 匹配的文本片段或路径
    metadata: Dict[str, Any]


class RealPatentHybridRetrieval:
    """真实专利混合检索系统"""

    def __init__(self):
        """初始化检索系统组件"""
        logger.info("🚀 初始化真实专利混合检索系统...")

        # 初始化数据库连接
        self._init_postgresql()

        # 初始化向量检索（Qdrant）
        self.vector_adapter = QdrantVectorAdapter()

        # 初始化知识图谱（Neo4j）
        if Neo4jManager is not None:
            self.kg_manager = Neo4jManager()
        else:
            self.kg_manager = None
            logger.warning("⚠️ 知识图谱管理器未初始化，仅使用PostgreSQL+Qdrant检索")

        # 获取专利数据库配置
        self.db_config = get_patent_db_config()
        self.table_config = self.db_config.get_patent_table_config()
        self.search_config = self.db_config.get_search_config()

        # 检索权重配置
        self.weights = {
            "fulltext": 0.4,  # PostgreSQL全文搜索
            "vector": 0.5,  # Qdrant向量检索
            "kg": 0.1,  # Neo4j知识图谱
        }

        logger.info("✅ 真实专利混合检索系统初始化完成")

    def _init_postgresql(self):
        """初始化PostgreSQL连接"""
        try:
            # 测试数据库连接
            if not test_patent_database():
                raise Exception("无法连接到专利数据库")

            # 获取连接参数
            from config.database import get_patent_connection_params

            conn_params = get_patent_connection_params()
            conn_params["cursor_factory"] = RealDictCursor

            self.pg_conn = psycopg2.connect(**conn_params)
            self.pg_conn.autocommit = False

            logger.info("✅ PostgreSQL专利数据库连接成功")
        except Exception as e:
            logger.error(f"❌ PostgreSQL连接失败: {e}")
            self.pg_conn = None

    async def search(self, query: str, top_k: int = 20) -> List[RetrievalResult]:
        """
        混合检索主函数

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            检索结果列表
        """
        logger.info(f"🔍 开始真实专利混合检索，查询: {query}")

        # 查询长度检查
        if len(query) < self.search_config["min_query_length"]:
            logger.warning(f"查询长度过短: {len(query)} < {self.search_config['min_query_length']}")
            return []

        # 限制最大返回数量
        top_k = min(top_k, self.search_config["max_limit"])

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

        logger.info(f"✅ 检索完成，返回 {len(final_results)} 条结果")
        return final_results

    async def _fulltext_search(self, query: str, top_k: int) -> List[RetrievalResult]:
        """PostgreSQL全文搜索 - 真实数据版本"""
        if not self.pg_conn:
            logger.warning("PostgreSQL未连接，跳过全文搜索")
            return []

        results = []
        try:
            with self.pg_conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 使用配置的表名和权重
                patents_table = self.table_config["patents_table"]
                weights = self.search_config["ranking_weights"]

                # 构建动态全文搜索SQL
                sql = f"""
                SELECT
                    p.patent_id,
                    p.title,
                    p.abstract,
                    ts_rank_cd(
                        setweight(to_tsvector('simple', p.title), 'A') ||
                        setweight(to_tsvector('simple', p.abstract), 'B') ||
                        setweight(to_tsvector('simple', p.claims), 'C') ||
                        setweight(to_tsvector('simple', p.description), 'D'),
                        plainto_tsquery('simple', %s),
                        {weights["title"]}  -- title权重
                    ) as title_rank,
                    ts_rank_cd(
                        setweight(to_tsvector('simple', p.title), 'A') ||
                        setweight(to_tsvector('simple', p.abstract), 'B') ||
                        setweight(to_tsvector('simple', p.claims), 'C') ||
                        setweight(to_tsvector('simple', p.description), 'D'),
                        plainto_tsquery('simple', %s),
                        {weights["abstract"]}  -- abstract权重
                    ) as abstract_rank,
                    ts_headline('simple', p.title, plainto_tsquery('simple', %s)) as title_highlight,
                    ts_headline('simple', p.abstract, plainto_tsquery('simple', %s)) as abstract_highlight
                FROM {patents_table} p
                WHERE
                    to_tsvector('simple', p.title || ' ' || p.abstract || ' ' || p.claims || ' ' || p.description) @@ plainto_tsquery('simple', %s)
                ORDER BY (title_rank + abstract_rank) DESC
                LIMIT %s
                """

                cur.execute(sql, (query, query, query, query, query, top_k))
                rows = cur.fetchall()

                for row in rows:
                    # 计算综合分数
                    combined_score = float(row["title_rank"] + row["abstract_rank"])

                    evidence_parts = []
                    if row["title_highlight"] and row["title_highlight"] != row["title"]:
                        evidence_parts.append(f"标题: {row['title_highlight']}")
                    if row["abstract_highlight"] and row["abstract_highlight"] != row["abstract"]:
                        evidence_parts.append(f"摘要: {row['abstract_highlight']}")

                    evidence = (
                        "<br>".join(evidence_parts)
                        if evidence_parts
                        else row["abstract"][:200] + "..."
                    )

                    results.append(
                        RetrievalResult(
                            patent_id=row["patent_id"],
                            title=row["title"],
                            abstract=row["abstract"],
                            score=combined_score,
                            source="fulltext",
                            evidence=evidence,
                            metadata={
                                "highlight": {
                                    "title": row["title_highlight"],
                                    "abstract": row["abstract_highlight"],
                                },
                                "rank_breakdown": {
                                    "title_rank": float(row["title_rank"]),
                                    "abstract_rank": float(row["abstract_rank"]),
                                },
                            },
                        )
                    )

        except Exception as e:
            logger.error(f"❌ 全文搜索出错: {e}")

        return results

    async def _vector_search(self, query: str, top_k: int) -> List[RetrievalResult]:
        """Qdrant向量检索 - 真实数据版本"""
        try:
            # 生成查询向量（这里需要调用实际的embedding模型）
            query_vector = await self._generate_query_vector(query)

            if query_vector is None:
                logger.warning("无法生成查询向量，跳过向量检索")
                return []

            # 搜索专利向量
            results = await self.vector_adapter.search_vectors(
                collection_type="patents", query_vector=query_vector, limit=top_k, threshold=0.3
            )

            retrieval_results = []
            for item in results:
                # 获取专利详细信息（从PostgreSQL查询）
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
                            metadata={
                                "vector_id": item["id"],
                                "vector_score": item["score"],
                                "similarity_details": {
                                    "threshold": 0.3,
                                    "vector_dimension": len(query_vector) if query_vector else 0,
                                },
                            },
                        )
                    )

            return retrieval_results

        except Exception as e:
            logger.error(f"❌ 向量搜索出错: {e}")
            return []

    async def _kg_search(self, query: str, top_k: int) -> List[RetrievalResult]:
        """Neo4j知识图谱检索 - 真实数据版本"""
        try:
            # 提取查询中的关键技术术语
            keywords = self._extract_keywords(query)

            if not keywords:
                logger.warning("无法提取关键词，跳过知识图谱搜索")
                return []

            # 构建Cypher查询
            cypher = """
            MATCH (p:Patent)-[:HAS_TECHNOLOGY]->(t:Technology)
            WHERE any(keyword in $keywords WHERE toLower(t.name) CONTAINS toLower(keyword))
            WITH p, count(*) as tech_count
            OPTIONAL MATCH (p)-[:CITES]->(cited:Patent)
            OPTIONAL MATCH (citing:Patent)-[:CITES]->(p)
            OPTIONAL MATCH (p)-[:BELONGS_TO]->(ipc:IPC)
            RETURN
                p.patent_id as patent_id,
                p.title as title,
                p.abstract as abstract,
                tech_count,
                count(DISTINCT cited) as citations_made,
                count(DISTINCT citing) as citations_received,
                collect(DISTINCT t.name)[..3] as matched_tech,
                collect(DISTINCT ipc.code)[..3] as matched_ipc
            ORDER BY tech_count DESC, citations_received DESC
            LIMIT $limit
            """

            # 执行查询
            records = await self.kg_manager.execute_cypher(
                cypher, parameters={"keywords": keywords, "limit": top_k}
            )

            results = []
            for record in records:
                # 计算综合分数
                tech_count = record.get("tech_count", 0)
                citations = record.get("citations_received", 0)
                score = tech_count * 0.7 + citations * 0.3

                # 构建证据
                evidence_parts = []
                matched_tech = record.get("matched_tech", [])
                matched_ipc = record.get("matched_ipc", [])

                if matched_tech:
                    evidence_parts.append(f"匹配技术: {', '.join(matched_tech)}")
                if matched_ipc:
                    evidence_parts.append(f"匹配IPC: {', '.join(matched_ipc)}")
                if citations > 0:
                    evidence_parts.append(f"被引用次数: {citations}")

                evidence = "; ".join(evidence_parts) if evidence_parts else "知识图谱关联"

                results.append(
                    RetrievalResult(
                        patent_id=record["patent_id"],
                        title=record.get("title", ""),
                        abstract=record.get("abstract", ""),
                        score=score,
                        source="kg",
                        evidence=evidence,
                        metadata={
                            "tech_count": tech_count,
                            "citation_count": citations,
                            "matched_tech": matched_tech,
                            "matched_ipc": matched_ipc,
                            "kg_score_details": {"tech_weight": 0.7, "citation_weight": 0.3},
                        },
                    )
                )

            return results

        except Exception as e:
            logger.error(f"❌ 知识图谱搜索出错: {e}")
            return []

    async def _generate_query_vector(self, query: str) -> Optional[List[float]]:
        """生成查询向量"""
        try:
            # 这里应该调用实际的embedding模型
            # 暂时使用模拟向量
            import numpy as np

            return np.random.rand(768).tolist()  # 假设768维向量
        except Exception as e:
            logger.error(f"生成查询向量失败: {e}")
            return None

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        try:
            import re

            import jieba

            # 使用jieba分词
            words = jieba.cut(text)

            # 过滤处理
            stop_words = {
                "的",
                "是",
                "在",
                "和",
                "与",
                "或",
                "等",
                "及",
                "基于",
                "包括",
                "一种",
                "方法",
                "系统",
            }
            keywords = []

            for word in words:
                word = word.strip()
                if (
                    len(word) > 1
                    and word not in stop_words
                    and not word.isdigit()
                    and re.match(r"^[\u4e00-\u9fa5a-zA-Z0-9]+$", word)
                ):
                    keywords.append(word)

            return keywords[:8]  # 返回前8个关键词
        except ImportError:
            # 如果没有jieba，使用简单分词
            import re

            words = re.findall(r"\b\w+\b", text)
            stop_words = {"的", "是", "在", "和", "与", "或", "等", "及", "基于", "包括"}
            keywords = [w for w in words if len(w) > 1 and w not in stop_words]
            return keywords[:5]
        except Exception as e:
            logger.error(f"关键词提取失败: {e}")
            return []

    async def _get_patent_info(self, patent_id: str) -> Optional[Dict[str, Any]]:
        """从PostgreSQL获取专利详细信息"""
        if not self.pg_conn:
            return None

        try:
            patents_table = self.table_config["patents_table"]

            with self.pg_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    f"SELECT patent_id, title, abstract, claims, description FROM {patents_table} WHERE patent_id = %s",
                    (patent_id,),
                )
                result = cur.fetchone()
                return dict(result) if result else None
        except Exception as e:
            logger.error(f"获取专利信息失败: {e}")
            return None

    def _merge_and_rerank(
        self,
        ft_results: List[RetrievalResult],
        vector_results: List[RetrievalResult],
        kg_results: List[RetrievalResult],
        top_k: int,
    ) -> List[RetrievalResult]:
        """融合和重排序检索结果"""
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
                "total_score": total_score,
            }

            final_results.append(patent)

        # 排序并返回Top-K
        final_results.sort(key=lambda x: x.score, reverse=True)
        return final_results[:top_k]

    async def get_patent_details(self, patent_id: str) -> Optional[Dict[str, Any]]:
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
            "retrieval_stats": {
                "last_accessed": datetime.now().isoformat(),
                "data_source": "real_patent_database",
            },
        }

        return details

    async def _get_patent_kg_info(self, patent_id: str) -> Dict[str, Any]:
        """获取专利在知识图谱中的信息"""
        try:
            cypher = """
            MATCH (p:Patent {patent_id: $patent_id})
            OPTIONAL MATCH (p)-[:HAS_TECHNOLOGY]->(t:Technology)
            OPTIONAL MATCH (p)-[:CITES]->(cited:Patent)
            OPTIONAL MATCH (citing:Patent)-[:CITES]->(p)
            OPTIONAL MATCH (p)-[:BELONGS_TO]->(ipc:IPC)
            OPTIONAL MATCH (p)-[:BELONGS_TO_FAMILY]->(family:PatentFamily)
            RETURN
                collect(DISTINCT t.name) as technologies,
                count(DISTINCT cited) as citations_made,
                count(DISTINCT citing) as citations_received,
                collect(DISTINCT ipc.code) as ipc_codes,
                collect(DISTINCT family.family_id) as family_ids
            """

            result = await self.kg_manager.execute_cypher(
                cypher, parameters={"patent_id": patent_id}
            )

            return result[0] if result else {}

        except Exception as e:
            logger.error(f"获取专利知识图谱信息出错: {e}")
            return {}

    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        stats = {
            "components": {
                "postgresql": self.pg_conn is not None,
                "qdrant": True,  # 已初始化
                "neo4j": True,  # 已初始化
            },
            "config": {
                "database": self.db_config.get_config().__dict__,
                "tables": self.table_config,
                "search": self.search_config,
                "weights": self.weights,
            },
            "last_updated": datetime.now().isoformat(),
        }

        # 获取专利数据统计
        try:
            if self.pg_conn:
                patents_table = self.table_config["patents_table"]
                with self.pg_conn.cursor() as cur:
                    cur.execute(f"SELECT COUNT(*) FROM {patents_table}")
                    stats["patent_count"] = cur.fetchone()[0]

                    # 获取更多统计信息
                    cur.execute(f"""
                        SELECT
                            COUNT(DISTINCT applicant) as unique_applicants,
                            COUNT(DISTINCT publication_date::date) as unique_dates,
                            MIN(publication_date) as earliest_date,
                            MAX(publication_date) as latest_date
                        FROM {patents_table}
                        WHERE publication_date IS NOT NULL
                    """)
                    row = cur.fetchone()
                    stats["patent_stats"] = {
                        "unique_applicants": row[0],
                        "unique_dates": row[1],
                        "earliest_date": str(row[2]) if row[2] else None,
                        "latest_date": str(row[3]) if row[3] else None,
                    }
        except Exception as e:
            logger.error(f"获取专利统计信息失败: {e}")
            stats["patent_count"] = "Unknown"

        return stats


# 测试函数
async def test_real_patent_retrieval():
    """测试真实专利混合检索系统"""
    logger.info("\n" + "=" * 80)
    logger.info("🔍 真实专利混合检索系统测试")
    logger.info("=" * 80)

    # 初始化系统
    retrieval_system = RealPatentHybridRetrieval()

    # 显示系统状态
    logger.info("\n📊 系统状态:")
    stats = retrieval_system.get_system_stats()
    for key, value in stats.items():
        if key != "config":  # 配置信息太详细，单独显示
            logger.info(f"  {key}: {value}")

    # 测试查询
    test_queries = ["深度学习图像识别", "区块链数据存储", "自然语言处理", "人工智能专利"]

    for query in test_queries:
        logger.info(f"\n🔎 查询: {query}")
        logger.info("-" * 60)

        try:
            results = await retrieval_system.search(query, top_k=5)

            if results:
                for i, result in enumerate(results, 1):
                    logger.info(f"\n{i}. 专利ID: {result.patent_id}")
                    logger.info(
                        f"   标题: {result.title[:100]}{'...' if len(result.title) > 100 else ''}"
                    )
                    logger.info(f"   综合评分: {result.score:.4f}")
                    logger.info(f"   数据来源: {result.metadata['sources']}")
                    logger.info(
                        f"   证据: {result.evidence[:150]}{'...' if len(result.evidence) > 150 else ''}"
                    )
            else:
                logger.info("  暂无相关结果")

        except Exception as e:
            logger.error(f"  检索出错: {e}")

    logger.info("\n✅ 测试完成！")


if __name__ == "__main__":
    asyncio.run(test_real_patent_retrieval())
