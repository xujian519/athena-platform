#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实数据源和 Embedding 模型集成 (NebulaGraph版本 - 已废弃)

版本: v3.0.0
技术决策: TD-001 - 统一图数据库选择为Neo4j

⚠️ 迁移说明 ⚠️
此文件包含NebulaGraph实现,已被Neo4j版本替代。
新版本请参考: core/storm_integration/neo4j_database_connectors.py

完整集成:
1. PostgreSQL 真实连接
2. Neo4j 真实连接 (TD-001: 从NebulaGraph迁移)
3. Qdrant 向量检索 (带真实 embedding)
4. Embedding 模型集成 (BGE/Sentence-Transformers)

作者: Athena 平台团队
创建时间: 2026-01-02
更新时间: 2026-01-25 (TD-001: 标记为废弃)
"""

import asyncio
from core.async_main import async_main
import logging
from core.logging_config import setup_logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = setup_logging()


class EmbeddingModel:
    """
    Embedding 模型基类

    支持多种 embedding 模型:
    - BGE (BAAI General Embedding)
    - Sentence-Transformers
    - OpenAI Embeddings
    """

    def __init__(
        self,
        model_name: str = "BAAI/BAAI/bge-m3",
        model_type: str = "bge",  # bge, sentence-transformers, openai
        device: str = "cpu"
    ):
        """
        初始化 Embedding 模型

        Args:
            model_name: 模型名称
            model_type: 模型类型
            device: 运行设备 (cpu/cuda)
        """
        self.model_name = model_name
        self.model_type = model_type
        self.device = device
        self._model = None
        self._loaded = False

        logger.info(f"初始化 Embedding 模型: {model_name} ({model_type})")

    def load(self):
        """加载模型"""
        if self._loaded:
            return

        try:
            if self.model_type == "bge":
                self._load_bge_model()
            elif self.model_type == "sentence-transformers":
                self._load_sentence_transformers()
            elif self.model_type == "openai":
                self._load_openai_embeddings()
            else:
                logger.warning(f"未知的模型类型: {self.model_type}")

            if self._model is not None:
                self._loaded = True
                logger.info(f"✅ Embedding 模型加载成功: {self.model_name}")

        except Exception as e:
            logger.error(f"Embedding 模型加载失败: {e}")
            self._loaded = False

    def _load_bge_model(self):
        """加载 BGE 模型"""
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(
                self.model_name,
                device=self.device
            )
            logger.info(f"✅ BGE 模型加载成功: {self.model_name}")

        except ImportError:
            logger.warning("sentence-transformers 未安装")
        except Exception as e:
            logger.error(f"BGE 模型加载失败: {e}")

    def _load_sentence_transformers(self):
        """加载 Sentence-Transformers 模型"""
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(
                self.model_name,
                device=self.device
            )

        except Exception as e:
            logger.error(f"Sentence-Transformers 模型加载失败: {e}")

    def _load_openai_embeddings(self):
        """加载 OpenAI Embeddings (API)"""
        try:
            from openai import OpenAI

            self._client = OpenAI()
            self._model = "openai"

            logger.info("✅ OpenAI Embeddings 初始化成功")

        except Exception as e:
            logger.error(f"OpenAI Embeddings 初始化失败: {e}")

    def encode(self, texts: list[str]) -> list[list[float]]:
        """
        生成文本向量

        Args:
            texts: 文本列表

        Returns:
            向量列表
        """
        if not self._loaded:
            logger.warning("模型未加载,返回零向量")
            dim = 1024  # BGE-M3向量维度(已更新) if "bge" in self.model_name else 1536
            return [[0.0] * dim for _ in texts]

        try:
            if self.model_type in ["bge", "sentence-transformers"]:
                # 本地模型
                embeddings = self._model.encode(
                    texts,
                    normalize_embeddings=True,
                    show_progress_bar=False
                )
                return embeddings.tolist()

            elif self.model_type == "openai":
                # OpenAI API
                embeddings = []
                for text in texts:
                    response = self._client.embeddings.create(
                        model="text-embedding-3-small",
                        input=text
                    )
                    embeddings.append(response.data[0].embedding)
                return embeddings

        except Exception as e:
            logger.error(f"生成向量失败: {e}")
            # 返回零向量作为后备
            dim = 1024  # BGE-M3向量维度(已更新) if "bge" in self.model_name else 1536
            return [[0.0] * dim for _ in texts]

    def encode_single(self, text: str) -> list[float]:
        """生成单个文本的向量"""
        return self.encode([text])[0]


class RealPostgreSQLRetriever:
    """
    真实的 PostgreSQL 专利检索器

    使用 Athena 平台的真实配置连接
    """

    def __init__(self):
        """初始化"""
        # 导入 Athena 的配置
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))

        try:
            from config.config_loader import get_database_config
            self.db_config = get_database_config()
            logger.info(f"✅ 加载数据库配置: {self.db_config.host}:{self.db_config.port}/{self.db_config.database}")
        except Exception as e:
            logger.warning(f"无法加载数据库配置: {e}")
            # 使用默认配置(本地PostgreSQL端口5432)
            self.db_config = type('Config', (), {
                'host': 'localhost',
                'port': 5432,  # 本地PostgreSQL端口(替代Docker的15432)
                'user': 'postgres',
                'password': 'YsUM&f_va2g_iu7ueyp_osw',
                'database': 'patent_db'
            })()

        self._connection = None
        self._connected = False

    async def connect(self):
        """建立连接"""
        try:
            import asyncpg

            connection_string = (
                f"postgresql://{self.db_config.user}:{self.db_config.password}"
                f"@{self.db_config.host}:{self.db_config.port}/{self.db_config.database}"
            )

            self._connection = await asyncpg.connect(connection_string)
            self._connected = True

            # 测试查询
            version = await self._connection.fetchval('SELECT version()')
            logger.info(f"✅ PostgreSQL 连接成功")

            # 获取专利数量
            tables = await self._connection.fetch("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name LIKE '%patent%'
                LIMIT 5
            """)

            if tables:
                logger.info(f"📊 发现专利相关表: {[t['table_name'] for t in tables]}")

        except ImportError:
            logger.warning("asyncpg 未安装,使用模拟数据")
            self._connected = False
        except Exception as e:
            logger.warning(f"PostgreSQL 连接失败: {e}")
            logger.info("将使用模拟数据")
            self._connected = False

    async def search_patents(
        self,
        query: str,
        limit: int = 10
    ) -> list[dict[str, Any]]:
        """检索专利"""
        if not self._connected:
            return await self._mock_search(query, limit)

        try:
            # 尝试在 patent_basic 表中搜索
            sql = """
            SELECT
                patent_id,
                application_number,
                title,
                abstract,
                applicant,
                application_date,
                ipc_classification
            FROM patent_basic
            WHERE title ILIKE $1 OR abstract ILIKE $1
            ORDER BY application_date DESC
            LIMIT $2
            """

            results = await self._connection.fetch(sql, f"%{query}%", limit)

            patents = []
            for row in results:
                patents.append({
                    'patent_id': row['patent_id'],
                    'application_number': row['application_number'],
                    'title': row['title'],
                    'abstract': row['abstract'] or '',
                    'applicant': row['applicant'] or '',
                    'application_date': str(row['application_date']) if row['application_date'] else '',
                    'ipc_classification': row['ipc_classification'] or '',
                    'relevance_score': 0.8,  # 简化处理
                })

            logger.info(f"✅ 从 PostgreSQL 检索到 {len(patents)} 条专利")
            return patents

        except Exception as e:
            logger.error(f"检索失败: {e}")
            return await self._mock_search(query, limit)

    async def _mock_search(self, query: str, limit: int) -> list[dict[str, Any]]:
        """模拟检索"""
        return [
            {
                'patent_id': f'CN10{i}0000{i}A',
                'application_number': f'CN202310{i}000.{i}',
                'title': f'关于{query}的专利 {i+1}',
                'abstract': f'本发明公开了{query}的相关技术方案...',
                'applicant': f'某科技公司{i}',
                'application_date': '2023-05-15',
                'ipc_classification': 'G06N3/00',
                'relevance_score': 0.9 - i * 0.1,
            }
            for i in range(min(limit, 3))
        ]

    async def close(self):
        """关闭连接"""
        if self._connection:
            await self._connection.close()


class RealNebulaGraphRetriever:
    """
    真实的 NebulaGraph 检索器

    使用 Athena 平台的真实配置连接
    """

    def __init__(self):
        """初始化"""
        # 使用 NebulaGraph 的默认配置
        self.hosts = "127.0.0.1:9669,127.0.0.1:19669"  # patent 相关图
        self.space = "patent_kg"

        # 验证space名称(防止nGQL注入)
        import re
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', self.space):
            raise ValueError(f"Invalid space name: {self.space}")

        self._session = None
        self._connected = False

        logger.info(f"初始化 NebulaGraph: {self.hosts}/{self.space}")

    async def connect(self):
        """建立连接"""
        try:
            from nebula3.gclient.net import ConnectionPool

            self._pool = ConnectionPool()
            await self._pool.init([self.hosts.split(',')])

            self._session = self._pool.get_session('root', 'nebula')
            self._connected = True

            # 测试查询
            result = self._session.execute(f"USE {self.space};")
            logger.info(f"✅ NebulaGraph 连接成功,使用空间: {self.space}")

        except Exception as e:
            logger.warning(f"NebulaGraph 连接失败: {e}")
            logger.info("将使用模拟数据")
            self._connected = False

    async def search_knowledge(
        self,
        query: str,
        limit: int = 10
    ) -> list[dict[str, Any]]:
        """检索知识图谱

        ⚠️ 安全说明:query参数经过转义处理,防止nGQL注入
        space名称已在初始化时通过正则验证
        """
        if not self._connected:
            return await self._mock_search(query, limit)

        try:
            # 转义query,防止nGQL注入
            escaped_query = query.replace("\\", "\\\\").replace("\"", "\\\"")

            ngql = f"""
            USE {self.space};
            MATCH (n)
            WHERE n.name CONTAINS \"{escaped_query}\"
            RETURN n
            LIMIT {limit};
            """

            result = self._session.execute(ngql)

            knowledge_nodes = []
            if result.is_succeeded():
                for row in result:
                    node = row[0]
                    knowledge_nodes.append({
                        'id': node.get_id(),
                        'labels': list(node.tags()),
                        'properties': dict(node.properties()),
                        'relevance_score': 0.8,
                    })

            logger.info(f"✅ 从 NebulaGraph 检索到 {len(knowledge_nodes)} 个节点")
            return knowledge_nodes

        except Exception as e:
            logger.error(f"知识图谱检索失败: {e}")
            return await self._mock_search(query, limit)

    async def _mock_search(self, query: str, limit: int) -> list[dict[str, Any]]:
        """模拟检索"""
        return [
            {
                'id': f'entity_{i}',
                'labels': ['Technology', 'Patent'],
                'properties': {
                    'name': f'{query}相关技术{i+1}',
                    'description': f'{query}的技术方案...',
                },
                'relevance_score': 0.85 - i * 0.1,
            }
            for i in range(min(limit, 2))
        ]

    async def close(self):
        """关闭连接"""
        if self._session:
            self._session.release()
        if hasattr(self, '_pool') and self._pool:
            await self._pool.close()


class RealQdrantRetriever:
    """
    真实的 Qdrant 向量检索器 (带 Embedding)
    """

    def __init__(
        self,
        collection_name: str = "legal_knowledge",
        embedding_model: EmbeddingModel | None = None
    ):
        """初始化"""
        self.collection_name = collection_name
        self.embedding_model = embedding_model or EmbeddingModel()
        self._client = None
        self._connected = False

        logger.info(f"初始化 Qdrant: {collection_name}")

    async def connect(self):
        """建立连接"""
        try:
            from qdrant_client import QdrantClient

            self._client = QdrantClient(url="http://localhost:6333", timeout=30)
            self._connected = True

            collections = self._client.get_collections()
            collection_names = [c.name for c in collections.collections]

            logger.info(f"✅ Qdrant 连接成功")
            logger.info(f"📊 可用集合: {collection_names}")

            # 检查目标集合
            if self.collection_name in collection_names:
                collection_info = self._client.get_collection(self.collection_name)
                logger.info(f"📊 集合 {self.collection_name}: {collection_info.points_count} 个向量")

        except Exception as e:
            logger.error(f"Qdrant 连接失败: {e}")
            self._connected = False

    async def search_vectors(
        self,
        query: str,
        limit: int = 10
    ) -> list[dict[str, Any]]:
        """向量检索 (带真实 Embedding)"""
        if not self._connected:
            return await self._mock_search(query, limit)

        try:
            # 生成查询向量
            self.embedding_model.load()
            query_vector = self.embedding_model.encode_single(query)

            # 执行检索
            from qdrant_client.models import PointStruct

            # 尝试搜索
            try:
                search_result = self._client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    limit=limit,
                )
            except Exception as e:
                logger.warning(f'search方法失败，尝试query_points: {e}')
                # 如果 search 失败,使用 query_points
                search_result = self._client.query_points(
                    collection_name=self.collection_name,
                    limit=limit,
                )

            results = []
            for hit in search_result.points if hasattr(search_result, 'points') else search_result:
                results.append({
                    'id': hit.id,
                    'score': getattr(hit, 'score', 0.8),
                    'payload': hit.payload,
                    'relevance_score': getattr(hit, 'score', 0.8),
                })

            logger.info(f"✅ 向量检索到 {len(results)} 条结果")
            return results
        except Exception as e:
            logger.error(f"向量检索失败: {e}")
            return await self._mock_search(query, limit)

    async def _mock_search(self, query: str, limit: int) -> list[dict[str, Any]]:
        """模拟检索"""
        return [
            {
                'id': f'doc_{i}',
                'score': 0.95 - i * 0.05,
                'payload': {
                    'text': f'{query}相关的法律条文...',
                    'content': f'这是关于{query}的法律文档...',
                    'title': f'法律文档{i+1}',
                },
                'relevance_score': 0.95 - i * 0.05,
            }
            for i in range(min(limit, 3))
        ]


class RealDataManager:
    """
    真实数据管理器 (完整版)

    统一管理所有真实数据源:
    - PostgreSQL 专利数据库
    - NebulaGraph 知识图谱
    - Qdrant 向量数据库 (带 Embedding)
    """

    def __init__(self):
        """初始化"""
        self.pg_retriever = RealPostgreSQLRetriever()
        self.ng_retriever = RealNebulaGraphRetriever()
        self.qd_retriever = RealQdrantRetriever()

        self._connected = False

    async def connect_all(self):
        """连接所有数据源"""
        logger.info("="*70)
        logger.info("连接所有真实数据源")
        logger.info("="*70)

        # 加载 Embedding 模型
        logger.info("\n[1/3] 加载 Embedding 模型...")
        self.qd_retriever.embedding_model.load()

        # 连接 PostgreSQL
        logger.info("\n[2/3] 连接 PostgreSQL...")
        await self.pg_retriever.connect()

        # 连接 NebulaGraph
        logger.info("\n[3/3] 连接 NebulaGraph...")
        await self.ng_retriever.connect()

        # 连接 Qdrant
        logger.info("\n[4/3] 连接 Qdrant...")
        await self.qd_retriever.connect()

        # 统计连接状态
        connected_count = sum([
            self.pg_retriever._connected,
            self.ng_retriever._connected,
            self.qd_retriever._connected,
        ])

        logger.info(f"\n{'='*70}")
        logger.info(f"✅ 成功连接 {connected_count}/3 个数据源")
        logger.info(f"{'='*70}")

        if connected_count > 0:
            self._connected = True

        return self._connected

    async def search_all(
        self,
        query: str,
        limit_per_source: int = 5
    ) -> dict[str, list[dict[str, Any]]:
        """并行检索所有数据源"""
        import asyncio

        # 生成查询向量
        self.qd_retriever.embedding_model.load()

        tasks = {
            'patent_db': self.pg_retriever.search_patents(query, limit_per_source),
            'knowledge_graph': self.ng_retriever.search_knowledge(query, limit_per_source),
            'vector_search': self.qd_retriever.search_vectors(query, limit_per_source),
        }

        results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        # 组装结果
        final_results = {}
        for key, result in zip(tasks.keys(), results):
            if isinstance(result, Exception):
                logger.error(f"{key} 检索失败: {result}")
                final_results[key] = []
            else:
                final_results[key] = result

        return final_results

    async def close_all(self):
        """关闭所有连接"""
        await self.pg_retriever.close()
        await self.ng_retriever.close()
        if self.qd_retriever._client:
            self.qd_retriever._client.close()


async def test_all_real_sources():
    """测试所有真实数据源"""
    # setup_logging()  # 日志配置已移至模块导入

    manager = RealDataManager()

    # 连接所有数据源
    await manager.connect_all()

    # 测试检索
    query = "专利创造性判断标准"
    logger.info(f"\n{'='*70}")
    logger.info(f"测试查询: {query}")
    logger.info(f"{'='*70}\n")

    results = await manager.search_all(query, limit_per_source=3)

    # 打印结果
    for source, items in results.items():
        logger.info(f"\n[{source}]: {len(items)} 条结果")
        for i, item in enumerate(items[:2], 1):
            if source == 'patent_db':
                logger.info(f"  {i}. {item.get('title', 'N/A')}")
                logger.info(f"     申请人: {item.get('applicant', 'N/A')}")
            elif source == 'knowledge_graph':
                props = item.get('properties', {})
                logger.info(f"  {i}. {props.get('name', 'N/A')}")
            else:
                payload = item.get('payload', {})
                logger.info(f"  {i}. {payload.get('title', payload.get('text', 'N/A')[:50])}")

    # 关闭连接
    await manager.close_all()

    logger.info(f"\n{'='*70}")
    logger.info("测试完成!")
    logger.info(f"{'='*70}")


if __name__ == "__main__":
    asyncio.run(test_all_real_sources())
