#!/usr/bin/env python3
from __future__ import annotations
"""
三库联动规则查询系统 - 实际数据库接入版本
Three-Database Rule Query System - Real Database Integration

将向量数据库、知识图谱、规则数据库的实际查询接入系统

作者: Athena平台团队
创建时间: 2026-01-20
版本: v2.0.0 "Real Integration"
"""

import asyncio
import hashlib
import logging
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


# ============================================================================
# 配置管理
# ============================================================================

def _load_domain_strategies() -> dict[str, dict[str, float]]:
    """加载领域查询策略配置"""
    config_file = Path("config/query_strategies.yaml")

    if config_file.exists():
        try:
            with open(config_file, encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config.get("domain_strategies", {})
        except Exception as e:
            logger.warning(f"⚠️ 加载配置文件失败,使用默认配置: {e}")

    # 默认配置
    return {
        "patent": {
            "vector_weight": 0.2,
            "kg_weight": 0.3,
            "rule_weight": 0.5
        },
        "legal": {
            "vector_weight": 0.3,
            "kg_weight": 0.2,
            "rule_weight": 0.5
        },
        "trademark": {
            "vector_weight": 0.4,
            "kg_weight": 0.2,
            "rule_weight": 0.4
        },
        "general": {
            "vector_weight": 0.5,
            "kg_weight": 0.3,
            "rule_weight": 0.2
        }
    }


# 加载配置(全局变量)
_DOMAIN_STRATEGIES = _load_domain_strategies()


# ============================================================================
# 数据类定义
# ============================================================================

class QuerySource(Enum):
    """查询来源"""
    VECTOR_DB = "vector_db"           # 向量数据库(语义搜索)
    KNOWLEDGE_GRAPH = "knowledge_graph"  # 知识图谱(关系推理)
    RULE_DATABASE = "rule_database"    # 规则数据库(显式规则)
    HYBRID = "hybrid"                 # 混合查询


@dataclass
class RuleResult:
    """规则查询结果"""
    source: QuerySource
    rule_id: str
    content: str
    confidence: float
    metadata: dict[str, Any] | None = None
    references: list[str] | None = None


@dataclass
class QueryResult:
    """综合查询结果"""
    query: str
    results: list[RuleResult]
    synthesis: str                    # 综合分析
    confidence: float                 # 综合置信度
    sources_used: list[QuerySource]
    query_time_ms: float              # 查询耗时(毫秒)
    cache_hit: bool = False           # 是否命中缓存


# ============================================================================
# 查询缓存系统
# ============================================================================

class QueryCache:
    """查询缓存 - 提升重复查询性能(线程安全)"""

    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        """
        初始化查询缓存

        Args:
            max_size: 最大缓存条目数
            ttl: 缓存过期时间(秒)
        """
        self.max_size = max_size
        self.ttl = ttl
        self._cache: dict[str, tuple[Any, float]] = {}
        self._access_times: dict[str, float] = {}
        self._lock = asyncio.Lock()  # 添加异步锁保护并发访问

        logger.info(f"💾 查询缓存初始化 (max_size={max_size}, ttl={ttl}s)")

    def _generate_key(self, query: str, source: QuerySource, **kwargs) -> str:
        """生成缓存键"""
        key_data = f"{source.value}:{query}"
        for k, v in sorted(kwargs.items()):
            key_data += f":{k}={v}"
        return hashlib.md5(key_data.encode('utf-8'), usedforsecurity=False).hexdigest()

    async def get(self, query: str, source: QuerySource, **kwargs) -> Any | None:
        """获取缓存(线程安全)"""
        async with self._lock:
            key = self._generate_key(query, source, **kwargs)

            if key not in self._cache:
                return None

            result, timestamp = self._cache[key]

            # 检查是否过期
            if time.time() - timestamp > self.ttl:
                del self._cache[key]
                if key in self._access_times:
                    del self._access_times[key]
                return None

            # 更新访问时间
            self._access_times[key] = time.time()

            return result

    async def set(self, query: str, source: QuerySource, result: Any, **kwargs) -> None:
        """设置缓存(线程安全)"""
        async with self._lock:
            key = self._generate_key(query, source, **kwargs)

            # 如果缓存已满,删除最久未访问的条目
            if len(self._cache) >= self.max_size and self._access_times:
                oldest_key = min(self._access_times.items(), key=lambda x: x[1])[0]
                del self._cache[oldest_key]
                del self._access_times[oldest_key]

            self._cache[key] = (result, time.time())
            self._access_times[key] = time.time()

    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()
        self._access_times.clear()
        logger.info("🗑️ 缓存已清空")

    def stats(self) -> dict[str, Any]:
        """获取缓存统计"""
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "ttl": self.ttl
        }


# 全局缓存实例
_query_cache = QueryCache()


# ============================================================================
# 向量数据库查询器 - 真实实现
# ============================================================================

class RealVectorDBQuerier:
    """向量数据库查询器 - 真实实现(PostgreSQL pgvector + Qdrant)"""

    def __init__(self, storage_manager=None):
        """
        初始化向量数据库查询器

        Args:
            storage_manager: UnifiedStorageManager实例
        """
        self.storage_manager = storage_manager
        self.cache = _query_cache

        # 延迟导入embedding模型
        self._embedding_model = None

        logger.info("🔍 向量数据库查询器初始化 (真实实现)")

    def _get_embedding_model(self) -> Any:
        """获取embedding模型(延迟加载) - 使用平台MPS优化的BGE-M3"""
        if self._embedding_model is None:
            try:
                # 使用平台MPS优化的BGE-M3模型

                # 异步加载模型（在同步上下文中创建新事件循环）
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # 如果已有运行中的事件循环，使用create_task
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as pool:
                            self._embedding_model = pool.submit(
                                asyncio.run,
                                self._load_mps_model()
                            ).result()
                    else:
                        self._embedding_model = asyncio.run(self._load_mps_model())

                    logger.info("✅ MPS优化的BGE-M3模型加载成功")
                except RuntimeError:
                    # 在同步上下文中使用线程池加载
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        self._embedding_model = pool.submit(
                            asyncio.run,
                            self._load_mps_model()
                        ).result()
                    logger.info("✅ MPS优化的BGE-M3模型加载成功（通过线程池）")

            except Exception as e:
                logger.warning(f"⚠️ MPS模型加载失败，使用模拟embedding: {e}")
                self._embedding_model = "mock"
        return self._embedding_model

    async def _load_mps_model(self):
        """加载MPS优化的BGE-M3模型"""
        from core.models.mps_embedding_models import get_mps_embedding_manager

        manager = get_mps_embedding_manager()

        # 确保模型已加载
        if "bge-m3-zh" not in manager.get_loaded_models():
            success = await manager.load_model(
                model_id="bge-m3-zh",
                model_name="BAAI/bge-m3",
                model_type="bge-m3",
            )
            if not success:
                raise RuntimeError("MPS模型加载失败")

        return manager

    def _encode_text(self, text: str) -> list[float]:
        """将文本编码为向量 - 使用平台MPS优化的BGE-M3"""
        model = self._embedding_model

        if model == "mock":
            # 模拟embedding(简单哈希)
            hash_val = int(hashlib.md5(text.encode('utf-8'), usedforsecurity=False).hexdigest(), 16)
            import numpy as np
            np.random.seed(hash_val % (2**32))
            return np.random.rand(1024).tolist()

        # 使用MPS优化的真实模型
        try:
            import asyncio
            import concurrent.futures

            # 在线程池中异步编码
            def sync_encode():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(model.encode("bge-m3-zh", text))
                finally:
                    loop.close()

            with concurrent.futures.ThreadPoolExecutor() as pool:
                result = pool.submit(sync_encode).result()

            return result.embeddings[0] if result.embeddings else []

        except Exception as e:
            logger.warning(f"⚠️ MPS编码失败，使用模拟embedding: {e}")
            # 降级到模拟embedding
            hash_val = int(hashlib.md5(text.encode('utf-8'), usedforsecurity=False).hexdigest(), 16)
            import numpy as np
            np.random.seed(hash_val % (2**32))
            return np.random.rand(1024).tolist()

    async def query(
        self,
        text: str,
        top_k: int = 5,
        threshold: float = 0.7,
        use_cache: bool = True
    ) -> list[RuleResult]:
        """
        语义搜索查询

        Args:
            text: 查询文本
            top_k: 返回结果数量
            threshold: 相似度阈值
            use_cache: 是否使用缓存

        Returns:
            list[RuleResult]: 查询结果
        """
        start_time = time.time()

        # 检查缓存
        if use_cache:
            cached = await self.cache.get(text, QuerySource.VECTOR_DB, top_k=top_k)
            if cached is not None:
                logger.debug(f"✅ 向量查询缓存命中: {text[:30]}...")
                return cached

        logger.info(f"🔍 向量数据库查询: {text[:50]}...")

        if not self.storage_manager:
            logger.warning("⚠️ 存储管理器未初始化,返回模拟结果")
            return self._mock_results(text, top_k)

        try:
            # 1. 将查询文本编码为向量
            query_vector = self._encode_text(text)

            # 2. 在PostgreSQL pgvector中搜索
            pg_results = await self._query_pgvector(query_vector, top_k, threshold)

            # 3. 如果需要,在Qdrant中搜索
            qdrant_results = []
            if len(pg_results) < top_k:
                qdrant_results = await self._query_qdrant(query_vector, top_k - len(pg_results), threshold)

            # 4. 合并结果
            all_results = pg_results + qdrant_results

            # 5. 缓存结果
            if use_cache and all_results:
                await self.cache.set(text, QuerySource.VECTOR_DB, all_results, top_k=top_k)

            query_time = (time.time() - start_time) * 1000
            logger.info(f"✅ 向量查询完成: {len(all_results)}条结果, 耗时{query_time:.1f}ms")

            return all_results

        except ImportError as e:
            logger.error(f"❌ 模块导入失败: {e}")
            return self._mock_results(text, top_k)
        except (AttributeError, TypeError) as e:
            logger.error(f"❌ 向量操作错误: {e}")
            return self._mock_results(text, top_k)
        except Exception as e:
            logger.error(f"❌ 向量查询失败: {e}")
            return self._mock_results(text, top_k)

    async def _query_pgvector(
        self,
        vector: list[float],
        top_k: int,
        threshold: float
    ) -> list[RuleResult]:
        """在PostgreSQL pgvector中查询"""
        conn = None
        try:
            conn = self.storage_manager.pg_pool.getconn()
            try:
                with conn.cursor() as cursor:
                    # 使用pgvector进行相似度搜索
                    cursor.execute("""
                        SELECT
                            id,
                            document_number,
                            title,
                            content,
                            metadata,
                            1 - (embedding <=> %s::vector) as similarity
                        FROM patent_rules_vectors
                        WHERE embedding <=> %s::vector < %s
                        ORDER BY embedding <=> %s::vector
                        LIMIT %s
                    """, (vector, vector, 1 - threshold, vector, top_k))

                    results = []
                    for row in cursor.fetchall():
                        similarity = row[5]
                        if similarity >= threshold:
                            results.append(RuleResult(
                                source=QuerySource.VECTOR_DB,
                                rule_id=row[1],
                                content=f"{row[2]}: {row[3][:200]}...",
                                confidence=similarity,
                                metadata={"db": "pgvector", "similarity": similarity}
                            ))

                    return results

            finally:
                # 确保连接总是被释放
                if conn is not None:
                    self.storage_manager.pg_pool.putconn(conn)

        except ImportError as e:
            logger.error(f"❌ PostgreSQL模块未安装: {e}")
            if conn is not None:
                try:
                    self.storage_manager.pg_pool.putconn(conn)
                except Exception as e:
                    # 记录异常但不中断流程
                    logger.debug(f"[real_database_query] Exception: {e}")
            return []
        except (AttributeError, ValueError) as e:
            logger.error(f"❌ pgvector操作错误: {e}")
            if conn is not None:
                try:
                    self.storage_manager.pg_pool.putconn(conn)
                except Exception as e:
                    # 记录异常但不中断流程
                    logger.debug(f"[real_database_query] Exception: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ pgvector查询失败: {e}")
            # 确保异常时也释放连接
            if conn is not None:
                try:
                    self.storage_manager.pg_pool.putconn(conn)
                except Exception as e:
                    # 记录异常但不中断流程
                    logger.debug(f"[real_database_query] Exception: {e}")
            return []

    async def _query_qdrant(
        self,
        vector: list[float],
        top_k: int,
        threshold: float
    ) -> list[RuleResult]:
        """在Qdrant中查询"""
        try:

            # 执行搜索
            search_results = self.storage_manager.qdrant_client.search(
                collection_name="patent_rules",
                query_vector=vector,
                limit=top_k,
                score_threshold=threshold
            )

            results = []
            for hit in search_results:
                results.append(RuleResult(
                    source=QuerySource.VECTOR_DB,
                    rule_id=str(hit.id),
                    content=hit.payload.get("content", "")[:200],
                    confidence=hit.score,
                    metadata={"db": "qdrant", "similarity": hit.score}
                ))

            return results

        except Exception as e:
            logger.error(f"❌ Qdrant查询失败: {e}")
            return []

    def _mock_results(self, text: str, top_k: int) -> list[RuleResult]:
        """返回模拟结果"""
        return [
            RuleResult(
                source=QuerySource.VECTOR_DB,
                rule_id=f"vec_mock_{i}",
                content=f"向量搜索结果 {i}: 与'{text}'语义相关的规则 (模拟)",
                confidence=0.85 - i * 0.1,
                metadata={"db": "mock", "similarity": 0.85 - i * 0.1}
            )
            for i in range(min(top_k, 3))
        ]


# ============================================================================
# 知识图谱查询器 - 真实实现
# ============================================================================

class RealKnowledgeGraphQuerier:
    """知识图谱查询器 - 真实实现(Neo4j)"""

    def __init__(self, storage_manager=None):
        """
        初始化知识图谱查询器

        Args:
            storage_manager: UnifiedStorageManager实例
        """
        self.storage_manager = storage_manager
        self.cache = _query_cache
        self._neo4j_driver = None

        logger.info("🕸️ 知识图谱查询器初始化 (Neo4j)")

    def _get_neo4j_driver(self):
        """获取Neo4j驱动(延迟加载)"""
        if self._neo4j_driver is None:
            try:
                from neo4j import GraphDatabase
                self._neo4j_driver = GraphDatabase.driver(
                    "bolt://localhost:7687",
                    auth=("neo4j", "athena_neo4j_2024")
                )
                logger.info("✅ Neo4j驱动初始化成功")
            except ImportError:
                logger.error("❌ neo4j模块未安装")
                raise
            except Exception as e:
                logger.error(f"❌ Neo4j连接失败: {e}")
                raise
        return self._neo4j_driver

    async def query(
        self,
        text: str,
        depth: int = 2,
        use_cache: bool = True
    ) -> list[RuleResult]:
        """
        知识图谱关系查询

        Args:
            text: 查询文本
            depth: 推理深度
            use_cache: 是否使用缓存

        Returns:
            list[RuleResult]: 查询结果
        """
        start_time = time.time()

        # 检查缓存
        if use_cache:
            cached = await self.cache.get(text, QuerySource.KNOWLEDGE_GRAPH, depth=depth)
            if cached is not None:
                logger.debug(f"✅ 知识图谱查询缓存命中: {text[:30]}...")
                return cached

        logger.info(f"🕸️ 知识图谱查询: {text[:50]}...")

        try:
            # 1. 提取实体
            entities = await self._extract_entities(text)

            # 2. 在Neo4j中进行图遍历
            results = await self._query_neo4j(entities, depth)

            # 3. 缓存结果
            if use_cache and results:
                await self.cache.set(text, QuerySource.KNOWLEDGE_GRAPH, results, depth=depth)

            query_time = (time.time() - start_time) * 1000
            logger.info(f"✅ 知识图谱查询完成: {len(results)}条结果, 耗时{query_time:.1f}ms")

            return results

        except Exception as e:
            logger.error(f"❌ 知识图谱查询失败: {e}")
            return self._mock_results(text, depth)

    async def _extract_entities(self, text: str) -> list[str]:
        """提取实体"""
        # 简单实现:提取关键词
        # TODO: 使用NLP工具进行实体识别
        import re
        words = re.findall(r'[\w]+', text)
        # 过滤停用词
        stopwords = {'的', '是', '在', '和', '与', '或', '了', '要'}
        entities = [w for w in words if len(w) > 1 and w not in stopwords]
        return entities[:5]  # 返回前5个实体

    async def _query_neo4j(
        self,
        entities: list[str],
        depth: int
    ) -> list[RuleResult]:
        """在Neo4j中查询"""
        try:
            driver = self._get_neo4j_driver()
            results = []

            with driver.session() as session:
                # 对每个实体进行图遍历
                for entity in entities:
                    # 使用Cypher查询相关节点和关系
                    query = f"""
                        MATCH (n)
                        WHERE n.title CONTAINS $entity OR n.name CONTAINS $entity
                           OR n.judgment_id CONTAINS $entity OR n.patent_number CONTAINS $entity
                        OPTIONAL MATCH (n)-[r*1..{depth}]-(related)
                        RETURN DISTINCT n, related
                        LIMIT 10
                    """

                    result = session.run(query, entity=entity)

                    for record in result:
                        node = record["n"]
                        if node:
                            # 提取节点信息
                            labels = list(node.labels)
                            node_id = node.get("judgment_id") or node.get("patent_number") or node.get("title") or entity

                            results.append(RuleResult(
                                source=QuerySource.KNOWLEDGE_GRAPH,
                                rule_id=f"kg_{node_id}",
                                content=f"知识图谱发现: {entity} -> {node_id} ({', '.join(labels)})",
                                confidence=0.75,
                                metadata={"entity": entity, "path_length": depth, "labels": labels}
                            ))

            return results

        except Exception as e:
            logger.error(f"❌ Neo4j查询失败: {e}")
            return []

    def _mock_results(self, text: str, depth: int) -> list[RuleResult]:
        """返回模拟结果"""
        return [
            RuleResult(
                source=QuerySource.KNOWLEDGE_GRAPH,
                rule_id=f"kg_mock_{i}",
                content=f"知识图谱推理结果 {i}: 基于关系网络的规则推断 (模拟)",
                confidence=0.75 - i * 0.08,
                metadata={"entity": text[:10], "path_length": depth}
            )
            for i in range(min(depth + 1, 3))
        ]

    def close(self):
        """关闭Neo4j连接"""
        if self._neo4j_driver:
            self._neo4j_driver.close()
            self._neo4j_driver = None
            logger.info("🕸️ Neo4j连接已关闭")


# ============================================================================
# 规则数据库查询器 - 真实实现
# ============================================================================

class RealRuleDatabaseQuerier:
    """规则数据库查询器 - 真实实现(PostgreSQL规则库)"""

    def __init__(self, storage_manager=None):
        """
        初始化规则数据库查询器

        Args:
            storage_manager: UnifiedStorageManager实例
        """
        self.storage_manager = storage_manager
        self.cache = _query_cache

        logger.info("📖 规则数据库查询器初始化 (真实实现)")

    async def query(
        self,
        text: str,
        exact_match: bool = False,
        use_cache: bool = True,
        domain: str | None = None
    ) -> list[RuleResult]:
        """
        规则数据库查询

        Args:
            text: 查询文本
            exact_match: 是否精确匹配
            use_cache: 是否使用缓存
            domain: 限制查询的领域

        Returns:
            list[RuleResult]: 查询结果
        """
        start_time = time.time()

        # 检查缓存
        if use_cache:
            cached = await self.cache.get(text, QuerySource.RULE_DATABASE, exact_match=exact_match, domain=domain)
            if cached is not None:
                logger.debug(f"✅ 规则数据库查询缓存命中: {text[:30]}...")
                return cached

        logger.info(f"📖 规则数据库查询: {text[:50]}...")

        if not self.storage_manager:
            logger.warning("⚠️ 存储管理器未初始化,返回模拟结果")
            return self._mock_results(text)

        conn = None
        try:
            conn = self.storage_manager.pg_pool.getconn()

            try:
                with conn.cursor() as cursor:
                    if exact_match:
                        # 精确匹配
                        cursor.execute("""
                            SELECT
                                id,
                                document_number,
                                domain,
                                document_type,
                                title,
                                content,
                                metadata
                            FROM documents
                            WHERE domain = COALESCE(%s, domain)
                              AND (
                                    title %s %s OR
                                    content %s %s OR
                                    document_number = %s
                                  )
                            ORDER BY
                                CASE
                                    WHEN document_number = %s THEN 1
                                    WHEN title %s %s THEN 2
                                    ELSE 3
                                END
                            LIMIT 20
                        """, (domain, text, text, text, text, text, text, text, text))
                    else:
                        # 全文搜索
                        cursor.execute("""
                            SELECT
                                id,
                                document_number,
                                domain,
                                document_type,
                                title,
                                content,
                                metadata,
                                ts_rank(to_tsvector('simple', title || ' ' || content), plainto_tsquery('simple', %s)) as rank
                            FROM documents
                            WHERE domain = COALESCE(%s, domain)
                              AND to_tsvector('simple', title || ' ' || content) @@ plainto_tsquery('simple', %s)
                            ORDER BY rank DESC
                            LIMIT 20
                        """, (text, domain, text))

                    results = []
                    for row in cursor.fetchall():
                        confidence = 0.95 if exact_match else 0.80
                        results.append(RuleResult(
                            source=QuerySource.RULE_DATABASE,
                            rule_id=row[1],
                            content=f"{row[4]}: {row[5][:200]}...",
                            confidence=confidence,
                            metadata={
                                "db": "rule_db",
                                "domain": row[2],
                                "type": row[3],
                                "exact_match": exact_match
                            }
                        ))

                    # 缓存结果
                    if use_cache and results:
                        await self.cache.set(text, QuerySource.RULE_DATABASE, results, exact_match=exact_match, domain=domain)

                    query_time = (time.time() - start_time) * 1000
                    logger.info(f"✅ 规则数据库查询完成: {len(results)}条结果, 耗时{query_time:.1f}ms")

                    return results

            finally:
                # 确保连接总是被释放
                if conn is not None:
                    self.storage_manager.pg_pool.putconn(conn)

        except ImportError as e:
            logger.error(f"❌ 数据库驱动未安装: {e}")
            if conn is not None:
                try:
                    self.storage_manager.pg_pool.putconn(conn)
                except Exception as e:
                    # 记录异常但不中断流程
                    logger.debug(f"[real_database_query] Exception: {e}")
            return self._mock_results(text)
        except (AttributeError, ValueError) as e:
            logger.error(f"❌ 数据库操作错误: {e}")
            if conn is not None:
                try:
                    self.storage_manager.pg_pool.putconn(conn)
                except Exception as e:
                    # 记录异常但不中断流程
                    logger.debug(f"[real_database_query] Exception: {e}")
            return self._mock_results(text)
        except Exception as e:
            logger.error(f"❌ 规则数据库查询失败: {e}")
            # 确保异常时也释放连接
            if conn is not None:
                try:
                    self.storage_manager.pg_pool.putconn(conn)
                except Exception as e:
                    # 记录异常但不中断流程
                    logger.debug(f"[real_database_query] Exception: {e}")
            return self._mock_results(text)

    def _mock_results(self, text: str) -> list[RuleResult]:
        """返回模拟结果"""
        return [
            RuleResult(
                source=QuerySource.RULE_DATABASE,
                rule_id=f"rule_mock_{i}",
                content=f"规则数据库结果 {i}: 精确匹配的规则条文 (模拟)",
                confidence=0.95 - i * 0.05,
                metadata={"db": "mock", "exact_match": True}
            )
            for i in range(2)
        ]


# ============================================================================
# 三库联动查询系统 - 真实实现
# ============================================================================

class RealThreeDatabaseQuery:
    """三库联动查询系统 - 真实实现"""

    def __init__(self, storage_manager=None, enable_l2_cache: bool = True):
        """
        初始化三库联动查询系统

        Args:
            storage_manager: UnifiedStorageManager实例
            enable_l2_cache: 是否启用L2 Redis缓存
        """
        self.storage_manager = storage_manager
        self.vector_db = RealVectorDBQuerier(storage_manager)
        self.knowledge_graph = RealKnowledgeGraphQuerier(storage_manager)
        self.rule_database = RealRuleDatabaseQuerier(storage_manager)

        # 初始化L1缓存(内存缓存)
        self.cache = _query_cache

        # 初始化L2缓存(Redis缓存)
        self.l2_cache = None
        if enable_l2_cache:
            try:
                from core.cache.redis_cache import MultiLevelCache, RedisL2Cache

                # 获取Redis客户端
                redis_client = None
                if storage_manager and hasattr(storage_manager, 'redis_client'):
                    redis_client = storage_manager.redis_client

                # 创建L2缓存
                self.l2_cache = RedisL2Cache(
                    redis_client=redis_client,
                    key_prefix="athena:query:l2:",
                    default_ttl=7200  # 2小时
                )

                # 创建多级缓存
                self.multi_cache = MultiLevelCache(
                    l1_cache=self.cache,
                    l2_cache=self.l2_cache
                )

                logger.info("🔗 多级缓存已启用 (L1: 内存 + L2: Redis)")
            except ImportError:
                logger.warning("⚠️ Redis缓存模块未找到,仅使用L1缓存")
                self.multi_cache = None
        else:
            self.multi_cache = None

        logger.info("🔗 三库联动查询系统初始化完成 (真实实现)")

    async def query(
        self,
        text: str,
        use_vector: bool = True,
        use_kg: bool = True,
        use_rules: bool = True,
        vector_weight: float = 0.3,
        kg_weight: float = 0.2,
        rule_weight: float = 0.5,
        use_cache: bool = True
    ) -> QueryResult:
        """
        综合查询(三库联动)

        Args:
            text: 查询文本
            use_vector: 是否使用向量数据库
            use_kg: 是否使用知识图谱
            use_rules: 是否使用规则数据库
            vector_weight: 向量数据库权重
            kg_weight: 知识图谱权重
            rule_weight: 规则数据库权重
            use_cache: 是否使用缓存

        Returns:
            QueryResult: 综合查询结果
        """
        start_time = time.time()

        logger.info(f"🔗 开始三库联动查询: {text[:50]}...")

        results = []
        sources_used = []
        cache_hit = False

        # 并行查询三个数据库
        tasks = []

        if use_vector:
            tasks.append(("vector", self.vector_db.query(text, use_cache=use_cache)))

        if use_kg:
            tasks.append(("kg", self.knowledge_graph.query(text, use_cache=use_cache)))

        if use_rules:
            tasks.append(("rules", self.rule_database.query(text, use_cache=use_cache)))

        # 等待所有查询完成
        if tasks:
            query_responses = await asyncio.gather(*[task for _, task in tasks])

            for (source_name, _), query_results in zip(tasks, query_responses, strict=False):
                results.extend(query_results)

                if source_name == "vector":
                    sources_used.append(QuerySource.VECTOR_DB)
                elif source_name == "kg":
                    sources_used.append(QuerySource.KNOWLEDGE_GRAPH)
                elif source_name == "rules":
                    sources_used.append(QuerySource.RULE_DATABASE)

        # 计算综合置信度
        total_weight = sum([
            vector_weight if use_vector else 0,
            kg_weight if use_kg else 0,
            rule_weight if use_rules else 0
        ])

        if total_weight == 0:
            total_weight = 1.0

        # 按来源加权平均置信度
        weighted_confidence = 0.0

        for result in results:
            if result.source == QuerySource.VECTOR_DB:
                weighted_confidence += result.confidence * vector_weight
            elif result.source == QuerySource.KNOWLEDGE_GRAPH:
                weighted_confidence += result.confidence * kg_weight
            elif result.source == QuerySource.RULE_DATABASE:
                weighted_confidence += result.confidence * rule_weight

        overall_confidence = weighted_confidence / total_weight

        # 生成综合分析
        synthesis = self._synthesize_results(text, results)

        query_time = (time.time() - start_time) * 1000

        return QueryResult(
            query=text,
            results=results,
            synthesis=synthesis,
            confidence=overall_confidence,
            sources_used=sources_used,
            query_time_ms=query_time,
            cache_hit=cache_hit
        )

    def _synthesize_results(self, query: str, results: list[RuleResult]) -> str:
        """综合分析结果"""
        if not results:
            return f"未找到与查询'{query}'相关的规则。"

        # 按来源分组
        by_source = {
            QuerySource.VECTOR_DB: [],
            QuerySource.KNOWLEDGE_GRAPH: [],
            QuerySource.RULE_DATABASE: []
        }

        for result in results:
            by_source[result.source].append(result)

        synthesis_parts = []

        # 向量数据库结果
        if by_source[QuerySource.VECTOR_DB]:
            vec_count = len(by_source[QuerySource.VECTOR_DB])
            synthesis_parts.append(f"🔍 语义搜索找到 {vec_count} 条相关规则")

        # 知识图谱结果
        if by_source[QuerySource.KNOWLEDGE_GRAPH]:
            kg_count = len(by_source[QuerySource.KNOWLEDGE_GRAPH])
            synthesis_parts.append(f"🕸️ 关系推理发现 {kg_count} 条相关规则")

        # 规则数据库结果
        if by_source[QuerySource.RULE_DATABASE]:
            rule_count = len(by_source[QuerySource.RULE_DATABASE])
            synthesis_parts.append(f"📖 规则库匹配 {rule_count} 条精确规则")

        return " | ".join(synthesis_parts)

    async def query_by_domain(
        self,
        text: str,
        domain: str,
        use_cache: bool = True
    ) -> QueryResult:
        """
        按领域查询(自动优化权重)

        从配置文件 (config/query_strategies.yaml) 加载领域策略

        Args:
            text: 查询文本
            domain: 领域(patent, legal, trademark, copyright, general)
            use_cache: 是否使用缓存

        Returns:
            QueryResult: 查询结果
        """
        # 从全局配置获取领域策略
        strategy = _DOMAIN_STRATEGIES.get(domain, _DOMAIN_STRATEGIES["general"])

        logger.info(f"🎯 使用领域策略: {domain}")

        return await self.query(
            text,
            vector_weight=strategy["vector_weight"],
            kg_weight=strategy["kg_weight"],
            rule_weight=strategy["rule_weight"],
            use_cache=use_cache
        )


# 便捷函数
async def query_rules_real(
    text: str,
    domain: str = "general",
    storage_manager=None
) -> QueryResult:
    """
    便捷的规则查询函数(真实实现)

    Args:
        text: 查询文本
        domain: 领域
        storage_manager: 存储管理器

    Returns:
        QueryResult: 查询结果
    """
    query_system = RealThreeDatabaseQuery(storage_manager)
    return await query_system.query_by_domain(text, domain)


# 导出缓存控制函数
def clear_query_cache() -> None:
    """清空查询缓存"""
    _query_cache.clear()


def get_cache_stats() -> dict[str, Any]:
    """获取缓存统计"""
    return _query_cache.stats()


__all__ = [
    'QueryCache',
    'QueryResult',
    'QuerySource',
    'RealKnowledgeGraphQuerier',
    'RealRuleDatabaseQuerier',
    'RealThreeDatabaseQuery',
    'RealVectorDBQuerier',
    'RuleResult',
    'clear_query_cache',
    'get_cache_stats',
    'query_rules_real'
]
