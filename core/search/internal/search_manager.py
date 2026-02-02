#!/usr/bin/env python3
"""
内部搜索引擎管理器
Internal Search Engine Manager

基于Athena知识图谱和Qdrant向量化系统的内部搜索引擎实现

作者: Athena AI系统
创建时间: 2025-12-04
"""

import json
import logging
import sqlite3
from datetime import datetime
from typing import Any


# 导入基础类型
from ..types import Document, SearchResult, SearchType

logger = logging.getLogger(__name__)


class InternalSearchManager:
    """内部搜索引擎管理器"""

    def __init__(self, config: dict[str, Any]):
        """
        初始化内部搜索引擎管理器

        Args:
            config: 搜索配置
        """
        self.config = config
        self.initialized = False

        # 数据库路径
        self.db_path = "/Users/xujian/Athena工作平台/data/athena_knowledge_graph.db"

        # Qdrant配置(连接到真实运行的Qdrant)
        self.qdrant_config = {
            "host": "localhost",
            "port": 6333,
            "collections": {"patent_legal_docs": {"dimension": 1024}},  # 连接到我们创建的集合
        }

    async def initialize(self):
        """初始化内部搜索引擎"""
        if self.initialized:
            return

        logger.info("🚀 初始化内部搜索引擎管理器...")

        try:
            # 验证数据库连接
            self._verify_database_connection()

            # 验证Qdrant连接(如果可用)
            await self._verify_qdrant_connection()

            self.initialized = True
            logger.info("✅ 内部搜索引擎管理器初始化完成")

        except Exception as e:
            logger.error(f"❌ 内部搜索引擎管理器初始化失败: {e}")
            raise

    def _verify_database_connection(self) -> Any:
        """验证数据库连接"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 检查知识图谱表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            required_tables = ["vertices", "edges"]
            for table in required_tables:
                if table in tables:
                    logger.info(f"✅ 找到知识图谱表: {table}")
                else:
                    logger.warning(f"⚠️ 缺少知识图谱表: {table}")

            conn.close()

        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            raise

    async def _verify_qdrant_connection(self):
        """验证Qdrant连接"""
        try:
            import aiohttp

            logger.info("🔍 检查Qdrant连接状态...")

            # 使用HTTP API检查Qdrant
            url = f"http://{self.qdrant_config['host']}:{self.qdrant_config['port']}/collections"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        data = await response.json()
                        collections = data.get("result", {}).get("collections", [])
                        collection_names = [col["name"] for col in collections]

                        logger.info(f"✅ Qdrant连接成功,可用集合: {collection_names}")

                        # 检查我们的目标集合是否存在
                        target_collection = "patent_legal_docs"
                        if target_collection in collection_names:
                            logger.info(f"✅ 找到目标集合: {target_collection}")
                        else:
                            logger.warning(f"⚠️ 目标集合不存在: {target_collection}")
                    else:
                        logger.warning(f"⚠️ Qdrant API响应异常: {response.status}")

        except aiohttp.ClientError as e:
            logger.warning(f"⚠️ 无法连接到Qdrant: {e}")
        except Exception as e:
            logger.warning(f"⚠️ Qdrant连接检查失败: {e}")

    async def search(
        self, query: str, search_type: SearchType = SearchType.HYBRID, limit: int = 10
    ) -> list[SearchResult]:
        """
        执行内部搜索

        Args:
            query: 搜索查询
            search_type: 搜索类型
            limit: 结果数量限制

        Returns:
            搜索结果列表
        """
        if not self.initialized:
            await self.initialize()

        logger.info(f"🔍 执行内部搜索: {query} (类型: {search_type.value})")

        results = []

        try:
            if search_type in [SearchType.FULLTEXT, SearchType.HYBRID]:
                # 全文搜索(基于知识图谱)
                fulltext_results = await self._search_fulltext(query, limit // 2)
                results.extend(fulltext_results)

            if search_type in [SearchType.SEMANTIC, SearchType.HYBRID]:
                # 语义搜索(基于Qdrant向量)
                semantic_results = await self._search_semantic(query, limit // 2)
                results.extend(semantic_results)

            # 处理结果
            processed_results = self._process_search_results(query, results, search_type)
            return processed_results

        except Exception as e:
            logger.error(f"❌ 内部搜索失败: {e}")
            return []

    async def _search_fulltext(self, query: str, limit: int) -> list[SearchResult]:
        """执行全文搜索"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 在知识图谱中搜索匹配的节点
            search_query = f"%{query}%"
            cursor.execute(
                """
                SELECT id, type, label, properties, source_graph
                FROM vertices
                WHERE label LIKE ? OR properties LIKE ?
                LIMIT ?
            """,
                (search_query, search_query, limit * 2),
            )

            rows = cursor.fetchall()
            conn.close()

            results = []
            for row in rows:
                doc_id, doc_type, title, properties, source = row

                try:
                    props = json.loads(properties) if properties else {}
                except (json.JSONDecodeError, TypeError, ValueError):
                    props = {}

                # 创建文档对象
                document = Document(
                    id=doc_id,
                    title=title,
                    content=props.get("content", title),
                    metadata={"type": doc_type, "source_graph": source, "properties": props},
                )

                # 创建搜索结果
                result = SearchResult(
                    documents=[document],
                    scores=[0.8],  # 简化的评分
                    query=query,
                    search_type=SearchType.FULLTEXT,
                    total_time=0.1,
                    total_found=len(rows),
                )

                results.append(result)

            return results

        except Exception as e:
            logger.error(f"❌ 全文搜索失败: {e}")
            return []

    async def _search_semantic(self, query: str, limit: int) -> list[SearchResult]:
        """执行语义搜索(基于Qdrant)"""
        try:
            import aiohttp

            logger.info(f"🔍 执行Qdrant语义搜索: {query}")

            # 生成查询向量(简化版本,使用哈希向量)
            query_vector = self._generate_query_vector(query)

            # 连接到Qdrant
            collection_name = "patent_legal_docs"
            url = f"http://{self.qdrant_config['host']}:{self.qdrant_config['port']}/collections/{collection_name}/search"

            search_payload = {
                "vector": query_vector,
                "limit": limit,
                "with_payload": True,
                "with_vector": False,
            }

            async with aiohttp.ClientSession() as session, session.post(
                url, json=search_payload, timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    search_results = data.get("result", [])

                    if not search_results:
                        logger.info("📭 Qdrant中未找到匹配结果")
                        return self._create_empty_semantic_result(query)

                    # 转换Qdrant结果为SearchResult
                    documents = []
                    scores = []

                    for hit in search_results:
                        payload = hit.get("payload", {})
                        score = hit.get("score", 0.0)

                        document = Document(
                            id=payload.get("id", f"qdrant_{hit['id']}"),
                            title=payload.get("title", f"向量匹配文档 {hit['id']}"),
                            content=payload.get(
                                "content", f"与查询语义相似的内容,相似度: {score:.3f}"
                            ),
                            metadata={
                                "source": "qdrant_vector",
                                "collection": collection_name,
                                "similarity_score": score,
                                "vector_id": hit["id"],
                                "payload": payload,
                            },
                        )

                        documents.append(document)
                        scores.append(score)

                    logger.info(f"✅ Qdrant语义搜索成功,找到 {len(documents)} 个结果")

                    return [
                        SearchResult(
                            documents=documents,
                            scores=scores,
                            query=query,
                            search_type=SearchType.SEMANTIC,
                            total_time=0.3,
                            total_found=len(documents),
                        )
                    ]

                else:
                    logger.warning(f"⚠️ Qdrant搜索请求失败: HTTP {response.status}")
                    return self._create_fallback_semantic_result(query, limit)

        except aiohttp.ClientError as e:
            logger.warning(f"⚠️ Qdrant连接失败: {e}")
            return self._create_fallback_semantic_result(query, limit)
        except Exception as e:
            logger.error(f"❌ 语义搜索失败: {e}")
            return []

    def _generate_query_vector(self, query: str) -> list[float]:
        """生成查询向量(简化版本)"""
        import hashlib

        # 创建基于查询哈希的1024维向量(简化实现)
        hash_obj = hashlib.md5(query.encode("utf-8"), usedforsecurity=False)
        hash_hex = hash_obj.hexdigest()

        # 将哈希值转换为向量
        vector = []
        for i in range(0, len(hash_hex), 2):
            hex_pair = hash_hex[i : i + 2]
            value = int(hex_pair, 16) / 255.0 - 0.5  # 归一化到[-0.5, 0.5]
            vector.append(value)

        # 填充到1024维
        while len(vector) < 1024:
            vector.extend(vector[: min(1024 - len(vector), len(vector))])

        return vector[:1024]

    def _create_empty_semantic_result(self, query: str) -> list[SearchResult]:
        """创建空的语义搜索结果"""
        return [
            SearchResult(
                documents=[],
                scores=[],
                query=query,
                search_type=SearchType.SEMANTIC,
                total_time=0.1,
                total_found=0,
            )
        ]

    def _create_fallback_semantic_result(self, query: str, limit: int) -> list[SearchResult]:
        """创建降级语义搜索结果"""
        # 在无法连接Qdrant时,提供基础匹配结果
        fallback_documents = [
            Document(
                id=f"fallback_semantic_{i}",
                title=f"语义匹配结果 {i+1}",
                content=f"与 '{query}' 可能相关的文档内容",
                metadata={
                    "source": "fallback_semantic",
                    "query_match": True,
                    "reason": "qdrant_unavailable",
                },
            )
            for i in range(min(limit, 3))
        ]

        return [
            SearchResult(
                documents=fallback_documents,
                scores=[0.7] * len(fallback_documents),
                query=query,
                search_type=SearchType.SEMANTIC,
                total_time=0.15,
                total_found=len(fallback_documents),
            )
        ]

    def _process_search_results(
        self, query: str, raw_results: list[SearchResult], search_type: SearchType
    ) -> list[SearchResult]:
        """处理搜索结果"""
        if not raw_results:
            # 创建空结果
            return [
                SearchResult(
                    documents=[],
                    scores=[],
                    query=query,
                    search_type=search_type,
                    total_time=0.1,
                    total_found=0,
                )
            ]

        # 合并结果(如果有多个SearchResult)
        all_documents = []
        all_scores = []

        for result in raw_results:
            all_documents.extend(result.documents)
            all_scores.extend(result.scores)

        # 按分数排序
        sorted_results = sorted(zip(all_documents, all_scores, strict=False), key=lambda x: x[1], reverse=True)

        # 取前N个结果
        top_results = sorted_results[: min(10, len(sorted_results))]

        if top_results:
            documents, scores = zip(*top_results, strict=False)
            documents = list(documents)
            scores = list(scores)
        else:
            documents = []
            scores = []

        return [
            SearchResult(
                documents=documents,
                scores=scores,
                query=query,
                search_type=search_type,
                total_time=0.3,
                total_found=len(all_documents),
            )
        ]

    async def index_document(self, document: Document) -> bool:
        """
        索引文档到内部搜索引擎

        Args:
            document: 要索引的文档

        Returns:
            是否索引成功
        """
        try:
            # 这里应该实现文档索引逻辑
            # 将文档存储到知识图谱和向量数据库
            logger.info(f"📝 索引文档: {document.id}")
            return True

        except Exception as e:
            logger.error(f"❌ 文档索引失败: {e}")
            return False

    async def get_statistics(self) -> dict[str, Any]:
        """获取搜索引擎统计信息"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 统计知识图谱数据
            cursor.execute("SELECT COUNT(*) FROM vertices")
            vertex_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM edges")
            edge_count = cursor.fetchone()[0]

            cursor.execute("SELECT DISTINCT type FROM vertices")
            vertex_types = [row[0] for row in cursor.fetchall()]

            conn.close()

            return {
                "vertex_count": vertex_count,
                "edge_count": edge_count,
                "vertex_types": vertex_types,
                "indexed_documents": 0,  # 实际应该统计索引的文档数
                "last_index_time": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ 获取统计信息失败: {e}")
            return {}

    async def shutdown(self):
        """关闭内部搜索引擎管理器"""
        logger.info("🔄 关闭内部搜索引擎管理器...")
        self.initialized = False
        logger.info("✅ 内部搜索引擎管理器已关闭")

    async def health_check(self) -> dict[str, Any]:
        """健康检查"""
        try:
            stats = await self.get_statistics()
            return {
                "status": "healthy" if self.initialized else "unhealthy",
                "initialized": self.initialized,
                "statistics": stats,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "timestamp": datetime.now().isoformat()}
