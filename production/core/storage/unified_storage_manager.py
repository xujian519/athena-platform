#!/usr/bin/env python3
"""
统一存储管理器
Unified Storage Manager for Qdrant + Neo4j + PostgreSQL

提供统一的接口管理三个存储系统:
- Qdrant: 向量存储
- Neo4j: 图存储
- PostgreSQL: 关系存储 + pgvector向量存储

使用配置系统管理凭据,不硬编码敏感信息

作者: Athena平台团队
创建时间: 2026-01-11
版本: v3.0.0 (统一使用Neo4j作为图数据库,支持pgvector多业务向量表)

技术决策: TD-001 - 统一图数据库选择为Neo4j
"""

from __future__ import annotations
import logging
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any

# PostgreSQL
import psycopg2
import psycopg2.pool

# Neo4j - 统一图数据库 (TD-001)
from neo4j import GraphDatabase
from psycopg2 import sql as psycopg2_sql
from psycopg2.extras import Json, RealDictCursor

# Qdrant
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

# 导入配置管理
from core.config.settings import get_database_config
from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


# ============================================================================
# 历史数据导入相关枚举和常量
# ============================================================================


class HistoricalDataType(Enum):
    """历史数据类型"""

    INVALID_DECISION = "invalid_decision"  # 无效复审决定
    CHINESE_LAW = "chinese_law"  # 中国法律全集
    PATENT_LAW = "patent_law"  # 专利法
    TRADEMARK_DOC = "trademark_doc"  # 商标文档


# 新表映射 (PostgreSQL pgvector表)
PGVECTOR_TABLES = {
    HistoricalDataType.INVALID_DECISION: "patent_rules_vectors",
    HistoricalDataType.CHINESE_LAW: "legal_documents_vectors",
    HistoricalDataType.PATENT_LAW: "legal_documents_vectors",
    HistoricalDataType.TRADEMARK_DOC: "legal_documents_vectors",
}

# 新Qdrant集合映射 (保留Qdrant作为向量存储)
HISTORICAL_QDRANT_COLLECTIONS = {
    HistoricalDataType.INVALID_DECISION: "patent_invalidation_decisions",
    HistoricalDataType.CHINESE_LAW: "legal_docs_chinese_laws",
    HistoricalDataType.PATENT_LAW: "legal_docs_patent_laws",
    HistoricalDataType.TRADEMARK_DOC: "legal_docs_trademark_docs",
}


@dataclass
class StorageConfig:
    """存储配置 - 从配置系统获取"""

    def __init__(self):
        import os

        # 从系统配置获取数据库配置
        # 注意: settings.py 中的 get_database_config() 返回 DatabaseConfig 对象
        db_config = get_database_config()

        # Qdrant配置
        self.qdrant_url: str = db_config.qdrant_url
        self.qdrant_collection: str = db_config.qdrant_collection

        # Neo4j配置 - 统一图数据库 (TD-001)
        # 优先从环境变量读取，否则从配置读取
        self.neo4j_uri: str = os.getenv("NEO4J_URI", db_config.neo4j_uri)
        self.neo4j_username: str = os.getenv("NEO4J_USERNAME", db_config.neo4j_username)
        self.neo4j_password: str = os.getenv("NEO4J_PASSWORD", db_config.neo4j_password)
        self.neo4j_database: str = os.getenv("NEO4J_DATABASE", db_config.neo4j_database)

        # PostgreSQL配置
        self.pg_host: str = db_config.postgres_host
        self.pg_port: int = db_config.postgres_port
        self.pg_database: str = db_config.postgres_db
        self.pg_user: str = db_config.postgres_user
        self.pg_password: str = db_config.postgres_password
        self.pg_min_connections: int = db_config.postgres_min_connections
        self.pg_max_connections: int = db_config.postgres_max_connections


class UnifiedStorageManager:
    """
    统一存储管理器 (v3.0 - Neo4j统一版本)

    提供三个存储系统的统一接口:
    1. Qdrant - 向量存储和检索
    2. Neo4j - 图关系存储和遍历 (TD-001: 统一图数据库)
    3. PostgreSQL - 结构化数据、全文检索和pgvector向量存储
    """

    def __init__(self, config: StorageConfig | None = None):
        """
        初始化统一存储管理器

        Args:
            config: 存储配置,如果不提供则使用默认配置
        """
        self.config = config or StorageConfig()

        # 初始化连接
        self._init_qdrant()
        self._init_neo4j()
        self._init_postgresql()

        logger.info("✅ 统一存储管理器初始化完成 (Neo4j版本 - TD-001)")

    def _init_qdrant(self) -> Any:
        """初始化Qdrant连接"""
        try:
            self.qdrant_client = QdrantClient(url=self.config.qdrant_url)
            # 测试连接
            self.qdrant_client.get_collections()
            logger.info(f"✅ Qdrant连接成功 (URL: {self.config.qdrant_url})")
        except (ConnectionError, OSError) as e:
            logger.error(f"❌ Qdrant网络连接失败: {e}")
            raise RuntimeError(f"无法连接到Qdrant服务器: {e}") from e
        except Exception as e:
            logger.error(f"❌ Qdrant初始化失败: {e}")
            raise

    def _init_neo4j(self) -> Any:
        """初始化Neo4j驱动 (TD-001: 统一图数据库)"""
        try:
            # 创建Neo4j驱动
            self.neo4j_driver = GraphDatabase.driver(
                self.config.neo4j_uri,
                auth=(self.config.neo4j_username, self.config.neo4j_password),
            )

            # 测试连接
            with self.neo4j_driver.session(database=self.config.neo4j_database) as session:
                # 使用Cypher执行测试查询
                result = session.run("RETURN 'OK' as test")
                single_result = result.single()
                if single_result and single_result["test"] == "OK":
                    logger.info(
                        f"✅ Neo4j连接成功 (URI: {self.config.neo4j_uri}, "
                        f"Database: {self.config.neo4j_database})"
                    )

        except (ConnectionError, OSError) as e:
            logger.error(f"❌ Neo4j网络连接失败: {e}")
            raise RuntimeError(f"无法连接到Neo4j服务器: {e}") from e
        except Exception as e:
            logger.error(f"❌ Neo4j初始化失败: {e}")
            raise

    def _init_postgresql(self) -> Any:
        """初始化PostgreSQL连接池(使用配置系统)"""
        try:
            self.pg_pool = psycopg2.pool.ThreadedConnectionPool(
                self.config.pg_min_connections,
                self.config.pg_max_connections,
                host=self.config.pg_host,
                port=self.config.pg_port,
                database=self.config.pg_database,
                user=self.config.pg_user,
                password=self.config.pg_password,
            )
            # 测试连接
            conn = self.pg_pool.getconn()
            conn.close()
            logger.info(
                f"✅ PostgreSQL连接成功 (DB: {self.config.pg_database}, "
                f"连接数: {self.config.pg_min_connections}-{self.config.pg_max_connections})"
            )
        except psycopg2.Error as e:
            logger.error(f"❌ PostgreSQL数据库错误: {e}")
            # 如果数据库不存在,尝试创建
            if "database" in str(e).lower():
                logger.info("📦 数据库不存在,尝试创建...")
                self._create_database()
            else:
                raise
        except (ConnectionError, OSError) as e:
            logger.error(f"❌ PostgreSQL网络连接失败: {e}")
            raise RuntimeError(f"无法连接到PostgreSQL服务器: {e}") from e
        except Exception as e:
            logger.error(f"❌ PostgreSQL初始化失败: {e}")
            raise

    def _create_database(self) -> Any:
        """创建PostgreSQL数据库"""
        try:
            # 验证数据库名称(只允许字母、数字和下划线,且以字母开头)
            import re

            if not re.match(r"^[a-z_A-Z][a-z_A-Z0-9_]*$", self.config.pg_database):
                raise ValueError(f"数据库名称格式无效: {self.config.pg_database}")

            # 先连接到默认postgres数据库 - 使用上下文管理器防止连接泄漏
            conn = None
            try:
                # 连接创建也放在try块内,确保所有异常都被正确处理
                conn = psycopg2.connect(
                    host=self.config.pg_host,
                    port=self.config.pg_port,
                    database="postgres",
                    user=self.config.pg_user,
                    password=self.config.pg_password,
                )
                conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

                # 使用上下文管理器自动关闭cursor
                with conn.cursor() as cursor:
                    # 创建数据库 - 使用psycopg2.sql.Identifier防止SQL注入
                    create_db_query = psycopg2_sql.SQL("CREATE DATABASE {}").format(
                        psycopg2_sql.Identifier(self.config.pg_database)
                    )
                    cursor.execute(create_db_query)

                logger.info(f"✅ 数据库 {self.config.pg_database} 创建成功")

            except Exception as db_error:
                logger.error(f"❌ 数据库创建操作失败: {db_error}")
                raise
            finally:
                # 确保连接总是被关闭
                if conn:
                    conn.close()

            # 重新初始化连接池
            self._init_postgresql()

            # 创建表结构
            self._create_tables()

        except Exception as e:
            logger.error(f"❌ 创建数据库失败: {e}")
            raise

    def _create_tables(self) -> Any:
        """创建PostgreSQL表结构"""
        conn = None
        try:
            conn = self.pg_pool.getconn()

            # 使用上下文管理器自动关闭cursor
            with conn.cursor() as cursor:
                # 创建文档表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS documents (
                        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                        document_number VARCHAR(255) UNIQUE NOT NULL,
                        domain VARCHAR(50) NOT NULL,
                        document_type VARCHAR(50) NOT NULL,
                        title TEXT,
                        content TEXT,
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW()
                    )
                """)

                # 创建索引
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_domain ON documents(domain)")
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_document_type ON documents(document_type)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_document_number ON documents(document_number)"
                )

                # 创建全文检索索引
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_content_fulltext
                    ON documents USING gin(to_tsvector('simple', title || ' ' || content))
                """)

                conn.commit()

            logger.info("✅ PostgreSQL表结构创建成功")

        except Exception as e:
            logger.error(f"❌ 创建表失败: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            # 确保连接总是被归还到连接池
            if conn:
                self.pg_pool.putconn(conn)

    # ========================================================================
    # 统一写入操作
    # ========================================================================

    def write_document(
        self,
        document_number: str,
        domain: str,
        document_type: str,
        title: str,
        content: str,
        vectors: list[float],
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        写入文档到三个存储系统(三写一致性)

        Args:
            document_number: 文档编号
            domain: 领域 (law/patent/trademark)
            document_type: 文档类型 (article/guideline/judgment/decision)
            title: 标题
            content: 内容
            vectors: BGE-M3向量
            metadata: 额外元数据

        Returns:
            文档ID
        """
        doc_id = str(uuid.uuid4())
        metadata = metadata or {}

        logger.info(f"📝 写入文档: {document_number}")

        try:
            # 1. 写入PostgreSQL(主存储)
            self._write_to_postgresql(
                doc_id, document_number, domain, document_type, title, content, metadata
            )

            # 2. 写入Qdrant(向量存储)
            self._write_to_qdrant(
                doc_id,
                vectors,
                {
                    "document_number": document_number,
                    "domain": domain,
                    "document_type": document_type,
                    "title": title,
                    **metadata,
                },
            )

            # 3. 写入Neo4j(图存储) - TD-001: 统一图数据库
            self._write_to_neo4j(doc_id, document_number, domain, document_type, title, metadata)

            logger.info(f"✅ 文档写入成功: {document_number} (ID: {doc_id})")
            return doc_id

        except Exception as e:
            logger.error(f"❌ 文档写入失败: {e}")
            # 回滚PostgreSQL
            try:
                self._delete_from_postgresql(doc_id)
                logger.info(f"✅ 已回滚PostgreSQL中的文档: {doc_id}")
            except Exception as rollback_error:
                # 回滚失败是严重问题,需要记录但不要阻止原始异常的抛出
                logger.error(f"⚠️  回滚PostgreSQL失败: {rollback_error}, 文档ID: {doc_id}")
                # 回滚失败不应该阻止原始错误的抛出
            raise

    def _write_to_postgresql(
        self,
        doc_id: str,
        document_number: str,
        domain: str,
        document_type: str,
        title: str,
        content: str,
        metadata: dict[str, Any],    ) -> str:
        """写入PostgreSQL"""
        conn = None
        try:
            conn = self.pg_pool.getconn()

            # 使用上下文管理器自动关闭cursor
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO documents (id, document_number, domain, document_type, title, content, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """,
                    (
                        doc_id,
                        document_number,
                        domain,
                        document_type,
                        title,
                        content,
                        Json(metadata),
                    ),
                )

                result = cursor.fetchone()
                conn.commit()

            return result[0]

        except Exception:
            if conn:
                conn.rollback()
            raise
        finally:
            # 确保连接总是被归还到连接池
            if conn:
                self.pg_pool.putconn(conn)

    def _write_to_qdrant(self, doc_id: str, vectors: list[dict[str, Any]], payload: dict[str, Any] | None = None):
        """写入Qdrant"""
        # 确保集合存在
        self._ensure_qdrant_collection()

        # 写入向量
        self.qdrant_client.upsert(
            collection_name=self.config.qdrant_collection,
            points=[PointStruct(id=doc_id, vector=vectors, payload=payload or {})],
        )

    def _write_to_neo4j(
        self,
        doc_id: str,
        document_number: str,
        domain: str,
        document_type: str,
        title: str,
        metadata: dict[str, Any],    ):
        """写入Neo4j图数据库 (TD-001: 统一图数据库)"""
        try:
            with self.neo4j_driver.session(database=self.config.neo4j_database) as session:
                # 构建Cypher插入语句
                cypher = """
                    MERGE (d:Document {doc_id: $doc_id})
                    SET d.document_number = $document_number,
                        d.domain = $domain,
                        d.document_type = $document_type,
                        d.title = $title,
                        d.metadata = $metadata,
                        d.created_at = datetime()
                """

                # 执行Cypher
                session.run(
                    cypher,
                    {
                        "doc_id": doc_id,
                        "document_number": document_number,
                        "domain": domain,
                        "document_type": document_type,
                        "title": title,
                        "metadata": metadata,
                    },
                )
                logger.debug(f"Neo4j写入成功: {doc_id}")

        except Exception as e:
            logger.warning(f"⚠️ Neo4j写入失败 (非致命): {e}")
            # Neo4j写入失败不应该阻止整体流程

    def _ensure_qdrant_collection(self) -> Any:
        """确保Qdrant集合存在"""
        try:
            self.qdrant_client.get_collection(self.config.qdrant_collection)
            logger.debug(f"Qdrant集合已存在: {self.config.qdrant_collection}")
        except Exception:
            # 集合不存在或其他错误,尝试创建
            logger.info(f"Qdrant集合不存在或访问失败,尝试创建: {self.config.qdrant_collection}")
            try:
                self.qdrant_client.create_collection(
                    collection_name=self.config.qdrant_collection,
                    vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
                )
                logger.info(f"✅ Qdrant集合已创建: {self.config.qdrant_collection}")
            except Exception as create_error:
                logger.error(f"❌ 创建Qdrant集合失败: {create_error}")
                raise

    # ========================================================================
    # 统一查询操作
    # ========================================================================

    def search(
        self,
        query_text: str,
        query_vector: list[str] = None,
        domain: str | None = None,
        document_type: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        统一搜索接口 - 并行查询三个存储

        Args:
            query_text: 查询文本
            query_vector: 查询向量(可选,如果为空则用query_text生成)
            domain: 领域过滤
            document_type: 文档类型过滤
            limit: 返回数量

        Returns:
            搜索结果列表
        """
        import concurrent.futures

        results = {"vector": [], "graph": [], "fulltext": []}

        # 并行查询
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {}

            # Qdrant向量搜索
            if query_vector:
                futures["vector"] = executor.submit(
                    self._search_qdrant, query_vector, domain, document_type, limit
                )

            # Neo4j图搜索 (TD-001: 统一图数据库)
            futures["graph"] = executor.submit(
                self._search_neo4j, query_text, domain, document_type, limit
            )

            # PostgreSQL全文搜索
            futures["fulltext"] = executor.submit(
                self._search_postgresql, query_text, domain, document_type, limit
            )

            # 收集结果
            for key, future in futures.items():
                try:
                    results[key] = future.result(timeout=5)
                except Exception as e:
                    logger.warning(f"⚠️  {key}搜索失败: {e}")
                    results[key] = []

        # 融合结果
        fused_results = self._fuse_results(results)

        return fused_results

    def _search_qdrant(
        self,
        query_vector: list[float],
        domain: str,
        document_type: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Qdrant向量搜索"""
        # 构建过滤条件
        filter_conditions = {}
        if domain:
            filter_conditions["domain"] = domain
        if document_type:
            filter_conditions["document_type"] = document_type

        # 执行搜索
        search_result = self.qdrant_client.search(  # type: ignore[attr-defined]
            collection_name=self.config.qdrant_collection,
            query_vector=query_vector,
            query_filter=filter_conditions if filter_conditions else None,
            limit=limit,
            with_payload=True,
        )

        # 转换结果
        results = []
        for hit in search_result:
            results.append(
                {"id": hit.id, "score": hit.score, "source": "vector", "payload": hit.payload}
            )

        return results

    def _search_neo4j(
        self, query_text: str, domain: str, document_type: str, limit: int
    ) -> list[dict[str, Any]]:
        """Neo4j图搜索 (TD-001: 统一图数据库)"""
        # 验证limit参数
        try:
            limit = int(limit)
            if limit <= 0 or limit > 1000:
                raise ValueError(f"limit参数超出有效范围: {limit}")
        except (ValueError, TypeError) as e:
            raise ValueError(f"limit参数必须是正整数: {limit}") from e

        try:
            with self.neo4j_driver.session(database=self.config.neo4j_database) as session:
                # 构建Cypher查询
                cypher = """
                    MATCH (d:Document)
                    WHERE d.title CONTAINS $query_text
                """

                params = {"query_text": query_text, "limit": limit}

                if domain:
                    cypher += " AND d.domain = $domain"
                    params["domain"] = domain

                if document_type:
                    cypher += " AND d.document_type = $document_type"
                    params["document_type"] = document_type

                cypher += """
                    RETURN d.doc_id as id, d.document_number as document_number,
                           d.title as title, d.domain as domain, d.document_type as document_type
                    LIMIT $limit
                """

                # 执行Cypher
                result = session.run(cypher, params)

                results = []
                for record in result:
                    results.append(
                        {
                            "id": record["id"],
                            "score": 0.8,  # 图搜索给固定分数
                            "source": "graph",
                            "payload": {
                                "document_number": record["document_number"],
                                "domain": record["domain"],
                                "document_type": record["document_type"],
                                "title": record["title"],
                            },
                        }
                    )

                return results

        except Exception as e:
            logger.warning(f"⚠️ Neo4j搜索失败 (非致命): {e}")
            return []

    def _search_postgresql(
        self, query_text: str, domain: str, document_type: str, limit: int
    ) -> list[dict[str, Any]]:
        """PostgreSQL全文搜索"""
        # 验证limit参数
        try:
            limit = int(limit)
            if limit <= 0 or limit > 1000:
                raise ValueError(f"limit参数超出有效范围: {limit}")
        except (ValueError, TypeError) as e:
            raise ValueError(f"limit参数必须是正整数: {limit}") from e

        conn = None
        try:
            conn = self.pg_pool.getconn()

            # 使用上下文管理器自动关闭cursor
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # 构建SQL查询
                sql = """
                    SELECT
                        id, document_number, domain, document_type, title,
                        ts_rank(to_tsvector('simple', title || ' ' || content), plainto_tsquery('simple', %s)) as rank
                    FROM documents
                    WHERE to_tsvector('simple', title || ' ' || content) @@ plainto_tsquery('simple', %s)
                """

                params = [query_text, query_text]

                if domain:
                    sql += " AND domain = %s"
                    params.append(domain)

                if document_type:
                    sql += " AND document_type = %s"
                    params.append(document_type)

                sql += " ORDER BY rank DESC LIMIT %s"
                params.append(limit)  # type: ignore[list-item]

                cursor.execute(sql, params)

                results = []
                for row in cursor.fetchall():
                    results.append(
                        {
                            "id": str(row["id"]),
                            "score": float(row["rank"]),
                            "source": "fulltext",
                            "payload": {
                                "document_number": row["document_number"],
                                "domain": row["domain"],
                                "document_type": row["document_type"],
                                "title": row["title"],
                            },
                        }
                    )

            return results

        except Exception as e:
            logger.error(f"PostgreSQL搜索失败: {e}")
            raise
        finally:
            if conn:
                self.pg_pool.putconn(conn)

    def _fuse_results(self, results: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
        """融合多源结果"""
        # 简单融合:合并所有结果并按分数排序
        all_results = []

        for _source, source_results in results.items():
            all_results.extend(source_results)

        # 按分数降序排序
        all_results.sort(key=lambda x: x["score"], reverse=True)  # type: ignore[arg-type]

        # 去重(按document_number)
        seen = set()
        unique_results = []
        for result in all_results:
            doc_number = result["payload"].get("document_number")
            if doc_number and doc_number not in seen:
                seen.add(doc_number)
                unique_results.append(result)

        return unique_results[:10]  # 返回Top-10

    # ========================================================================
    # 历史数据导入相关方法
    # ========================================================================

    def write_historical_data(
        self,
        data_type: HistoricalDataType,
        document_number: str,
        title: str,
        content: str,
        vectors: list[float],
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        写入历史数据到专用表和集合

        Args:
            data_type: 历史数据类型
            document_number: 文档编号
            title: 标题
            content: 内容
            vectors: BGE-M3向量
            metadata: 额外元数据

        Returns:
            文档ID
        """
        doc_id = str(uuid.uuid4())
        metadata = metadata or {}

        # 添加数据类型到元数据
        metadata["historical_data_type"] = data_type.value

        logger.info(f"📝 写入历史数据: {data_type.value} - {document_number}")

        try:
            # 1. 写入PostgreSQL pgvector专用表
            self._write_historical_to_pgvector(
                data_type, doc_id, document_number, title, content, vectors, metadata
            )

            # 2. 写入Qdrant专用集合
            collection_name = HISTORICAL_QDRANT_COLLECTIONS[data_type]
            self._write_to_qdrant_collection(
                collection_name,
                doc_id,
                vectors,
                {
                    "document_number": document_number,
                    "data_type": data_type.value,
                    "title": title,
                    **metadata,
                },
            )

            logger.info(f"✅ 历史数据写入成功: {document_number} (ID: {doc_id})")
            return doc_id

        except Exception as e:
            logger.error(f"❌ 历史数据写入失败: {e}")
            # 回滚PostgreSQL
            try:
                self._delete_historical_from_postgresql(data_type, doc_id)
            except Exception as rollback_error:
                logger.error(f"⚠️ 回滚PostgreSQL失败: {rollback_error}")
            raise

    def _write_historical_to_pgvector(
        self,
        data_type: HistoricalDataType,
        doc_id: str,
        document_number: str,
        title: str,
        content: str,
        vectors: list[float],
        metadata: dict[str, Any],    ):
        """写入历史数据到PostgreSQL pgvector专用表"""
        conn = None
        try:
            conn = self.pg_pool.getconn()

            with conn.cursor() as cursor:
                table_name = PGVECTOR_TABLES[data_type]
                table_identifier = psycopg2_sql.Identifier(table_name)

                # 根据不同表类型使用不同字段
                if data_type == HistoricalDataType.INVALID_DECISION:
                    # patent_rules_vectors表
                    insert_sql = psycopg2_sql.SQL("""
                        INSERT INTO {} (rule_id, rule_type, title, content, embedding, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (rule_id) DO NOTHING
                        RETURNING id
                    """).format(table_identifier)
                    cursor.execute(
                        insert_sql,
                        (
                            doc_id,  # rule_id
                            "decision",  # rule_type
                            title,
                            content,
                            vectors,  # embedding
                            Json(metadata),
                        ),
                    )
                else:  # CHINESE_LAW, PATENT_LAW, TRADEMARK_DOC
                    # legal_documents_vectors表
                    insert_sql = psycopg2_sql.SQL("""
                        INSERT INTO {} (document_id, document_type, title, content, embedding, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (document_id) DO NOTHING
                        RETURNING id
                    """).format(table_identifier)
                    cursor.execute(
                        insert_sql,
                        (
                            doc_id,  # document_id
                            data_type.value,  # document_type
                            title,
                            content,
                            vectors,  # embedding
                            Json(metadata),
                        ),
                    )

                result = cursor.fetchone()
                conn.commit()

                if result:
                    logger.debug(f"PostgreSQL pgvector写入成功: {table_name}/{doc_id}")

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"PostgreSQL pgvector写入失败: {e}")
            raise
        finally:
            if conn:
                self.pg_pool.putconn(conn)

    def _write_to_qdrant_collection(
        self, collection_name: str, doc_id: str, vectors: list[float], payload: dict[str, Any]
    ):
        """写入指定Qdrant集合"""
        try:
            self._ensure_qdrant_collection_by_name(collection_name)
            self.qdrant_client.upsert(
                collection_name=collection_name,
                points=[PointStruct(id=doc_id, vector=vectors, payload=payload)],
            )
        except Exception as e:
            logger.error(f"Qdrant写入失败 ({collection_name}): {e}")
            raise

    def _ensure_qdrant_collection_by_name(self, collection_name: str) -> Any:
        """确保指定Qdrant集合存在"""
        try:
            self.qdrant_client.get_collection(collection_name)
            logger.debug(f"Qdrant集合已存在: {collection_name}")
        except Exception as e:
            logger.warning(f"操作失败: {e}")
            logger.info(f"创建Qdrant集合: {collection_name}")
            try:
                self.qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
                )
                logger.info(f"✅ Qdrant集合已创建: {collection_name}")
            except Exception as create_error:
                logger.error(f"❌ 创建Qdrant集合失败: {create_error}")
                raise

    def search_historical_data(
        self,
        data_type: HistoricalDataType,
        query_vector: list[float],
        limit: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        搜索历史数据

        Args:
            data_type: 历史数据类型
            query_vector: 查询向量
            limit: 返回数量
            filters: 过滤条件

        Returns:
            搜索结果列表
        """
        collection_name = HISTORICAL_QDRANT_COLLECTIONS[data_type]

        try:
            search_result = self.qdrant_client.search(  # type: ignore[attr-defined]
                collection_name=collection_name,
                query_vector=query_vector,
                query_filter=filters,
                limit=limit,
                with_payload=True,
            )

            results = []
            for hit in search_result:
                results.append(
                    {
                        "id": hit.id,
                        "score": hit.score,
                        "source": collection_name,
                        "data_type": data_type.value,
                        "payload": hit.payload,
                    }
                )

            logger.info(f"🔍 历史数据搜索: {data_type.value}, 找到 {len(results)} 个结果")
            return results

        except Exception as e:
            logger.error(f"历史数据搜索失败 ({data_type.value}): {e}")
            return []

    def _delete_historical_from_postgresql(self, data_type: HistoricalDataType, doc_id: str):
        """从PostgreSQL历史数据表中删除"""
        conn = None
        try:
            conn = self.pg_pool.getconn()

            with conn.cursor() as cursor:
                table_name = PGVECTOR_TABLES[data_type]
                table_identifier = psycopg2_sql.Identifier(table_name)

                # 根据不同表类型使用不同字段
                if data_type == HistoricalDataType.INVALID_DECISION:
                    delete_sql = psycopg2_sql.SQL("DELETE FROM {} WHERE rule_id = %s").format(
                        table_identifier
                    )
                else:
                    delete_sql = psycopg2_sql.SQL("DELETE FROM {} WHERE document_id = %s").format(
                        table_identifier
                    )

                cursor.execute(delete_sql, (doc_id,))
                conn.commit()

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"从PostgreSQL删除失败: {e}")
            raise
        finally:
            if conn:
                self.pg_pool.putconn(conn)

    def get_historical_stats(self) -> dict[str, Any]:
        """
        获取历史数据统计信息

        Returns:
            统计信息字典
        """
        stats = {"qdrant_collections": {}, "postgresql_tables": {}}

        # 统计Qdrant集合
        for data_type, collection_name in HISTORICAL_QDRANT_COLLECTIONS.items():
            try:
                collection_info = self.qdrant_client.get_collection(collection_name)
                stats["qdrant_collections"][data_type.value] = {
                    "collection": collection_name,
                    "vectors_count": collection_info.points_count,
                    "status": "ok",
                }
            except Exception as e:
                stats["qdrant_collections"][data_type.value] = {
                    "collection": collection_name,
                    "error": str(e),
                    "status": "error",
                }

        # 统计PostgreSQL pgvector表
        for data_type, table_name in PGVECTOR_TABLES.items():
            conn = None
            try:
                conn = self.pg_pool.getconn()

                with conn.cursor() as cursor:
                    table_identifier = psycopg2_sql.Identifier(table_name)
                    count_sql = psycopg2_sql.SQL("SELECT COUNT(*) FROM {}").format(table_identifier)
                    cursor.execute(count_sql)
                    count = cursor.fetchone()[0]

                    stats["postgresql_tables"][data_type.value] = {
                        "table": table_name,
                        "records_count": count,
                        "status": "ok",
                    }

            except Exception as e:
                stats["postgresql_tables"][data_type.value] = {
                    "table": table_name,
                    "error": str(e),
                    "status": "error",
                }
            finally:
                if conn:
                    self.pg_pool.putconn(conn)

        return stats

    # ========================================================================
    # 清理和关闭
    # ========================================================================

    def _delete_from_postgresql(self, doc_id: str) -> Any:
        """从PostgreSQL删除"""
        conn = None
        try:
            conn = self.pg_pool.getconn()

            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM documents WHERE id = %s", (doc_id,))
                conn.commit()

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"从PostgreSQL删除失败: {e}")
            raise
        finally:
            if conn:
                self.pg_pool.putconn(conn)

    def close(self) -> Any:
        """关闭所有连接"""
        # 关闭PostgreSQL连接池
        if hasattr(self, "pg_pool"):
            self.pg_pool.closeall()

        # 关闭Neo4j驱动 (TD-001: 统一图数据库)
        if hasattr(self, "neo4j_driver"):
            self.neo4j_driver.close()

        logger.info("✅ 所有连接已关闭")


# =============================================================================
# 使用示例
# =============================================================================

if __name__ == "__main__":
    # 创建管理器
    manager = UnifiedStorageManager()

    # 测试写入
    try:
        doc_id = manager.write_document(
            document_number="TEST_001",
            domain="law",
            document_type="article",
            title="测试法条",
            content="这是一条测试法条的内容...",
            vectors=[0.1] * 1024,  # 示例向量
            metadata={"test": True},
        )
        print(f"✅ 写入成功,文档ID: {doc_id}")

        # 测试搜索
        results = manager.search(query_text="测试", query_vector=[0.1] * 1024, limit=5)
        print(f"🔍 搜索结果: {len(results)}条")
        for i, result in enumerate(results, 1):
            print(f"  {i}. [{result['score']:.3f}] {result['payload'].get('title')}")

    finally:
        manager.close()
