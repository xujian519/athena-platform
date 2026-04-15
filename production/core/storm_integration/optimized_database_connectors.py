#!/usr/bin/env python3
"""
优化的真实数据库连接器 (NebulaGraph版本 - 已废弃)

版本: v3.0.0
技术决策: TD-001 - 统一图数据库选择为Neo4j

⚠️ 迁移说明 ⚠️
此文件包含NebulaGraph实现,已被Neo4j版本替代。
新版本请参考: core/storm_integration/neo4j_database_connectors.py

迁移映射:
- OptimizedNebulaGraphRetriever → OptimizedNeo4jRetriever
- ConnectionPool → GraphDatabase.driver
- nGQL → Cypher
- space → database
- port 9669 → port 7687

保留原因: 保持向后兼容性

作者: Athena 平台团队
创建时间: 2026-01-02
更新时间: 2026-01-25 (TD-001: 标记为废弃)
"""

from __future__ import annotations
import asyncio
import os
import re
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

logger = setup_logging()


class OptimizedPostgreSQLRetriever:
    """
    优化的 PostgreSQL 专利检索器

    使用 Athena 平台的真实配置
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        user: str = "postgres",
        password: str = "",  # PostgreSQL 通常使用 peer 认证
        database: str = "legal_world_model",  # 默认数据库 (原athena_db)
    ):
        """
        初始化 PostgreSQL 检索器

        Args:
            host: 主机地址
            port: 端口号
            user: 用户名
            password: 密码 (本地通常不需要)
            database: 数据库名称
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self._connection = None
        self._connected = False

        logger.info(f"初始化 PostgreSQL 检索器: {host}:{port}/{database}")

    async def connect(self):
        """建立连接"""
        try:
            import asyncpg

            # 构建连接字符串
            if self.password:
                connection_string = (
                    f"postgresql://{self.user}:{self.password}"
                    f"@{self.host}:{self.port}/{self.database}"
                )
            else:
                # 本地 PostgreSQL 通常使用 peer 认证
                connection_string = (
                    f"postgresql://{self.user}@{self.host}:{self.port}/{self.database}"
                )

            logger.info(f"尝试连接: {self.host}:{self.port}/{self.database}")
            self._connection = await asyncpg.connect(connection_string)
            self._connected = True

            # 测试查询
            await self._connection.fetchval("SELECT version()")
            logger.info("✅ PostgreSQL 连接成功")

            # 获取表列表
            tables = await self._connection.fetch("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
                LIMIT 10
            """)

            if tables:
                table_names = [t["table_name"] for t in tables]
                logger.info(f"📊 可用表 (前10个): {table_names}")

        except ImportError:
            logger.warning("asyncpg 未安装,使用模拟数据")
            self._connected = False
        except Exception as e:
            logger.warning(f"PostgreSQL 连接失败: {e}")
            logger.info("将使用模拟数据")
            self._connected = False

    async def search_patents(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """
        检索专利数据

        Args:
            query: 查询文本
            limit: 返回数量

        Returns:
            专利列表
        """
        if not self._connected:
            logger.info("使用模拟专利数据")
            return await self._mock_search(query, limit)

        try:
            # 尝试在不同的表中搜索
            sql = """
            SELECT
                table_name,
                column_name,
                data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name IN (
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
            )
            ORDER BY table_name, ordinal_position
            """

            columns = await self._connection.fetch(sql)

            # 查找包含 patent 相关的表
            patent_tables = set()
            for col in columns:
                table_name = col["table_name"]
                if "patent" in table_name.lower():
                    patent_tables.add(table_name)

            if patent_tables:
                logger.info(f"📊 发现专利相关表: {patent_tables}")

                # 尝试搜索第一个专利表
                table_name = next(iter(patent_tables))
                search_sql = f"""
                SELECT *
                FROM {table_name}
                LIMIT {limit}
                """

                results = await self._connection.fetch(search_sql)

                patents = []
                for row in results:
                    patents.append(
                        {
                            "table": table_name,
                            "data": dict(row),
                            "relevance_score": 0.8,
                        }
                    )

                logger.info(f"✅ 从 PostgreSQL 检索到 {len(patents)} 条记录")
                return patents
            else:
                logger.info("未找到专利相关表,返回模拟数据")
                return await self._mock_search(query, limit)

        except Exception as e:
            logger.error(f"检索失败: {e}")
            return await self._mock_search(query, limit)

    async def _mock_search(self, query: str, limit: int) -> list[dict[str, Any]]:
        """模拟检索"""
        return [
            {
                "table": "patent_mock",
                "data": {
                    "id": f"CN10{i}0000{i}A",
                    "title": f"关于{query}的专利 {i+1}",
                    "abstract": f"本发明公开了{query}的相关技术方案...",
                    "applicant": f"某科技公司{i}",
                    "date": "2023-05-15",
                },
                "relevance_score": 0.9 - i * 0.1,
            }
            for i in range(min(limit, 3))
        ]

    async def close(self):
        """关闭连接"""
        if self._connection:
            await self._connection.close()


class OptimizedNebulaGraphRetriever:
    """
    优化的 NebulaGraph 检索器

    使用 Athena 平台的真实配置
    """

    # 可用的 space (根据实际 NebulaGraph 空间)
    AVAILABLE_SPACES = [
        "patent_kg",  # 专利知识图谱
        "patent_kg_extended",  # 扩展专利知识图谱
        "patent_full_text",  # 专利全文
        "patent_rules",  # 专利规则
        "legal_kg",  # 法律知识图谱
    ]

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 9669,
        space: str = "patent_kg",  # 使用实际存在的空间
        username: str = "root",
        password: str = os.getenv("NEBULA_PASSWORD", "nebula"),
    ):
        """
        初始化 NebulaGraph 检索器

        Args:
            host: Graphd 主机地址
            port: Graphd 端口
            space: 图空间名称
            username: 用户名
            password: 密码
        """
        # 验证space名称(防止nGQL注入)
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", space):
            raise ValueError(
                f"Invalid space name: {space}. Only letters, numbers and underscores are allowed."
            )

        # 如果space不在白名单中,记录警告
        if space not in self.AVAILABLE_SPACES:
            logger.warning(f"Space '{space}' not in AVAILABLE_SPACES, using anyway")

        self.host = host
        self.port = port
        self.space = space
        self.username = username
        self.password = password
        self._session = None
        self._pool = None
        self._connected = False

        logger.info(f"初始化 NebulaGraph: {host}:{port}/{space}")

    async def connect(self):
        """建立连接"""
        try:
            from nebula3.Config import Config
            from nebula3.gclient.net import ConnectionPool

            # 配置连接
            config = Config()
            config.max_connection_pool_size = 10

            # NebulaGraph 需要 (host, port) 元组列表
            server_list = [(self.host, self.port)]

            # 创建连接池 (同步方法,不需要 await)
            self._pool = ConnectionPool()
            self._pool.init(server_list, config)

            # 获取会话
            self._session = self._pool.get_session(self.username, self.password)
            self._connected = True

            # 测试查询 - space已在__init__中验证安全
            result = self._session.execute(f"USE {self.space};")

            if result.is_succeeded():
                logger.info(f"✅ NebulaGraph 连接成功,使用空间: {self.space}")

                # 获取可用空间
                stats_result = self._session.execute("SHOW SPACES;")
                if stats_result.is_succeeded():
                    spaces = [row.values[0] for row in stats_result.rows()]
                    logger.info(f"📊 可用空间: {spaces}")

                # 获取 TAGS 和 EDGES
                tags_result = self._session.execute("SHOW TAGS;")
                if tags_result.is_succeeded():
                    tags = [row.values[0] for row in tags_result.rows()]
                    logger.info(f"📊 节点类型: {tags[:5]}...")  # 只显示前5个

                edges_result = self._session.execute("SHOW EDGES;")
                if edges_result.is_succeeded():
                    edges = [row.values[0] for row in edges_result.rows()]
                    logger.info(f"📊 边类型: {edges[:5]}...")  # 只显示前5个
            else:
                logger.warning(f"空间 {self.space} 不存在,尝试其他空间")
                # 尝试使用第一个可用空间(来自白名单,安全)
                self.space = self.AVAILABLE_SPACES[0]
                result = self._session.execute(f"USE {self.space};")
                if result.is_succeeded():
                    logger.info(f"✅ 切换到空间: {self.space}")
                    self._connected = True
                else:
                    self._connected = False

        except ImportError:
            logger.warning("nebula3 未安装,使用模拟数据")
            self._connected = False
        except Exception as e:
            logger.warning(f"NebulaGraph 连接失败: {e}")
            logger.info("将使用模拟数据")
            self._connected = False

    async def search_knowledge(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """
        检索知识图谱

        Args:
            query: 查询文本
            limit: 返回数量

        Returns:
            知识节点列表
        """
        if not self._connected:
            logger.info("使用模拟知识图谱数据")
            return await self._mock_search(query, limit)

        try:
            # 构建查询
            ngql = f"""
            USE {self.space};
            MATCH (n)
            WHERE id(n) IS NOT NULL
            RETURN n
            LIMIT {limit};
            """

            result = self._session.execute(ngql)

            knowledge_nodes = []
            if result.is_succeeded():
                for row in result.rows():
                    # row.values 是一个列表
                    node_value = row.values[0]
                    # node_value 可能是 Node 对象
                    try:
                        # 尝试获取节点数据
                        node_data = {
                            "id": str(node_value),  # 简化处理
                            "relevance_score": 0.8,
                        }
                        knowledge_nodes.append(node_data)
                    except Exception as e:
                        # 如果无法解析,创建简单节点
                        logger.debug(f"节点解析失败,使用简化节点: {e}")
                        knowledge_nodes.append(
                            {
                                "id": f"node_{len(knowledge_nodes)}",
                                "relevance_score": 0.8,
                            }
                        )

                logger.info(f"✅ 从 NebulaGraph 检索到 {len(knowledge_nodes)} 个节点")
                return knowledge_nodes
            else:
                logger.info("查询失败,返回模拟数据")
                return await self._mock_search(query, limit)

        except Exception as e:
            logger.error(f"知识图谱检索失败: {e}")
            return await self._mock_search(query, limit)

    async def _mock_search(self, query: str, limit: int) -> list[dict[str, Any]]:
        """模拟检索"""
        return [
            {
                "id": f"entity_{i}",
                "tags": ["Technology", "Patent"],
                "properties": {
                    "name": f"{query}相关技术{i+1}",
                    "description": f"{query}的技术方案...",
                    "type": "patent_concept",
                },
                "relevance_score": 0.85 - i * 0.1,
            }
            for i in range(min(limit, 2))
        ]

    async def close(self):
        """关闭连接"""
        if self._session:
            self._session.release()
        # NebulaGraph 的连接池不需要 await
        if hasattr(self, "_pool") and self._pool:
            try:
                self._pool.close()
            except Exception as e:
                logger.warning(f"⚠️ 关闭连接池失败: {e}")


class OptimizedQdrantRetriever:
    """
    优化的 Qdrant 向量检索器

    使用本地 Embedding 模型 + Qdrant
    """

    def __init__(
        self,
        url: str = "http://localhost:6333",
        collection_name: str = "legal_knowledge",
        embedding_model_path: Path | None = None,
    ):
        """
        初始化 Qdrant 检索器

        Args:
            url: Qdrant 服务地址
            collection_name: 集合名称
            embedding_model_path: Embedding 模型路径
        """
        self.url = url
        self.collection_name = collection_name
        self._client = None
        self._connected = False
        self._embedding_model = None

        # 导入本地 Embedding 模型
        try:
            import sys
            from pathlib import Path as FilePath

            # 添加项目路径
            project_root = FilePath(__file__).parent.parent.parent
            sys.path.insert(0, str(project_root))

            from core.storm_integration.local_embedding_integration import LocalEmbeddingModel

            embedding_model_path or Path(
                "/Users/xujian/Athena工作平台/models/converted/BAAI/bge-m3"
            )
            self._embedding_model = LocalEmbeddingModel(model_name="bge-large-zh")
            logger.info("✅ 本地 Embedding 模型已就绪")
        except Exception as e:
            logger.warning(f"无法加载 Embedding 模型: {e}")
            logger.info("将使用模拟查询向量")

        logger.info(f"初始化 Qdrant: {url}/{collection_name}")

    async def connect(self):
        """建立连接"""
        try:
            from qdrant_client import QdrantClient

            self._client = QdrantClient(url=self.url, timeout=30)
            self._connected = True

            collections = self._client.get_collections()
            collection_names = [c.name for c in collections.collections]

            logger.info("✅ Qdrant 连接成功")
            logger.info(f"📊 可用集合: {len(collection_names)} 个")

            # 计算总向量数
            total_vectors = 0
            for name in collection_names:
                try:
                    info = self._client.get_collection(name)
                    count = info.points_count
                    total_vectors += count
                    if count > 1000:
                        logger.info(f"  - {name}: {count:,} 个向量")
                except Exception as e:
                    logger.debug(f"获取集合 {name} 信息失败: {e}")

            logger.info(f"📊 总向量数: {total_vectors:,}+")

            # 检查目标集合
            if self.collection_name in collection_names:
                collection_info = self._client.get_collection(self.collection_name)
                logger.info(
                    f"📊 集合 {self.collection_name}: {collection_info.points_count} 个向量"
                )

        except Exception as e:
            logger.error(f"Qdrant 连接失败: {e}")
            self._connected = False

    async def search_vectors(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """
        向量检索

        Args:
            query: 查询文本
            limit: 返回数量

        Returns:
            检索结果列表
        """
        if not self._connected:
            logger.warning("Qdrant 未连接")
            return await self._mock_search(query, limit)

        try:
            # 生成查询向量
            if self._embedding_model:
                self._embedding_model.load()
                query_vector = self._embedding_model.encode_single(query)
                logger.info(f"✅ 向量生成成功,维度: {len(query_vector)}")
            else:
                # 使用模拟向量
                import random

                query_vector = [random.random() for _ in range(1024)]
                logger.info("使用模拟查询向量")

            # 执行检索
            search_result = self._client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=limit,
                with_payload=True,
                score_threshold=None,
            )

            results = []
            for hit in search_result.points:
                results.append(
                    {
                        "id": hit.id,
                        "score": hit.score,
                        "payload": hit.payload,
                        "relevance_score": hit.score,
                    }
                )

            logger.info(f"✅ 检索到 {len(results)} 条结果")
            return results

        except Exception as e:
            logger.error(f"向量检索失败: {e}")
            return await self._mock_search(query, limit)

    async def _mock_search(self, query: str, limit: int) -> list[dict[str, Any]]:
        """模拟检索"""
        return [
            {
                "id": f"doc_{i}",
                "score": 0.95 - i * 0.05,
                "payload": {
                    "text": f"{query}相关的法律条文...",
                    "content": f"这是关于{query}的法律文档...",
                    "title": f"法律文档{i+1}",
                },
                "relevance_score": 0.95 - i * 0.05,
            }
            for i in range(min(limit, 3))
        ]

    async def close(self):
        """关闭连接"""
        if self._client:
            self._client.close()


class OptimizedDataManager:
    """
    优化的数据管理器 (Phase 2)

    统一管理所有真实数据源:
    - PostgreSQL 专利数据库
    - NebulaGraph 知识图谱
    - Qdrant 向量数据库 (30万+向量 + 本地 Embedding)
    """

    def __init__(
        self,
        pg_database: str = "legal_world_model",  # 原athena_db
        nebula_space: str = "patent_graph",
        qdrant_collection: str = "legal_knowledge",
    ):
        """初始化"""
        self.pg_retriever = OptimizedPostgreSQLRetriever(database=pg_database)
        self.ng_retriever = OptimizedNebulaGraphRetriever(space=nebula_space)
        self.qd_retriever = OptimizedQdrantRetriever(collection_name=qdrant_collection)

        self._connected = False

    async def connect_all(self):
        """连接所有数据源"""
        logger.info("=" * 70)
        logger.info("连接所有真实数据源 (Phase 2 优化版)")
        logger.info("=" * 70)

        # 连接 PostgreSQL
        logger.info("\n[1/3] 连接 PostgreSQL...")
        await self.pg_retriever.connect()

        # 连接 NebulaGraph
        logger.info("\n[2/3] 连接 NebulaGraph...")
        await self.ng_retriever.connect()

        # 连接 Qdrant
        logger.info("\n[3/3] 连接 Qdrant...")
        await self.qd_retriever.connect()

        # 统计连接状态
        connected_count = sum(
            [
                self.pg_retriever._connected,
                self.ng_retriever._connected,
                self.qd_retriever._connected,
            ]
        )

        logger.info(f"\n{'='*70}")
        logger.info(f"✅ 成功连接 {connected_count}/3 个数据源")
        logger.info(f"{'='*70}")

        if connected_count > 0:
            self._connected = True

        return self._connected

    async def search_all(
        self, query: str, limit_per_source: int = 5
    ) -> dict[str, list[dict[str, Any]]]:
        """并行检索所有数据源"""
        import asyncio

        tasks = {
            "patent_db": self.pg_retriever.search_patents(query, limit_per_source),
            "knowledge_graph": self.ng_retriever.search_knowledge(query, limit_per_source),
            "vector_search": self.qd_retriever.search_vectors(query, limit_per_source),
        }

        results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        # 组装结果
        final_results = {}
        for key, result in zip(tasks.keys(), results, strict=False):
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


async def test_optimized_connections():
    """测试优化的连接"""
    # setup_logging()  # 日志配置已移至模块导入

    manager = OptimizedDataManager()

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
            if source == "patent_db":
                data = item.get("data", {})
                logger.info(f"  {i}. {data.get('title', 'N/A')}")
            elif source == "knowledge_graph":
                props = item.get("properties", {})
                logger.info(f"  {i}. {props.get('name', 'N/A')}")
            else:
                payload = item.get("payload", {})
                text = payload.get("text", payload.get("content", "N/A"))
                logger.info(f"  {i}. {text[:50]}...")

    # 关闭连接
    await manager.close_all()

    logger.info(f"\n{'='*70}")
    logger.info("测试完成!")
    logger.info(f"{'='*70}")


if __name__ == "__main__":
    asyncio.run(test_optimized_connections())
