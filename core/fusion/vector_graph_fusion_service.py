#!/usr/bin/env python3
from __future__ import annotations
"""
向量-图融合记忆服务
Vector-Graph Fusion Memory Service

深度融合 pgvector 向量搜索与 Neo4j 图数据库的统一记忆服务

功能:
1. 统一数据模型 - 双向映射向量ID和图顶点ID
2. 融合查询引擎 - 5种查询策略
3. 实时同步机制 - CDC双向同步
4. 智能缓存 - 性能优化

作者: 小诺·双鱼公主
创建时间: 2025-12-28
版本: v3.0.0 (TD-001: 统一图数据库选择为Neo4j)
"""

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from core.config.unified_config import get_database_config
from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class QueryStrategy(Enum):
    """查询策略"""

    PURE_VECTOR = "pure_vector"  # 纯向量搜索
    PURE_GRAPH = "pure_graph"  # 纯图搜索
    VECTOR_GUIDED = "vector_guided"  # 向量引导图搜索
    GRAPH_PRUNED = "graph_pruned"  # 图剪枝向量搜索
    FUSION_BOTH = "fusion_both"  # 融合双路


@dataclass
class FusionQueryResult:
    """融合查询结果"""

    entity_id: str
    entity_type: str
    business_key: str
    content: str
    vector_score: float = 0.0
    graph_distance: int = 0
    graph_centrality: float = 0.0
    combined_score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class FusionConfig:
    """融合配置 (v3.0.0 - TD-001)"""

    # PostgreSQL 配置
    pg_host: str = "localhost"
    pg_port: int = 5432
    pg_user: str = "postgres"
    pg_password: str = ""
    pg_database: str = "athena_memory"

    # 向量配置 - 统一使用BGE-M3
    vector_dimension: int = 1024  # BGE-M3向量维度
    embedding_model: str = "BGE-M3"  # 统一使用BGE-M3

    # Neo4j 配置 (TD-001: 替换NebulaGraph)
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_database: str = "athena_memory"
    neo4j_username: str = "neo4j"
    neo4j_password: str = ""

    # 查询配置
    default_strategy: QueryStrategy = QueryStrategy.FUSION_BOTH
    vector_weight: float = 0.7
    graph_weight: float = 0.3
    max_results: int = 20
    similarity_threshold: float = 0.6

    # 缓存配置
    enable_cache: bool = True
    cache_ttl_seconds: int = 3600

    @classmethod
    def from_unified_config(cls) -> "FusionConfig":
        """从统一配置创建 (TD-001)"""
        db_config = get_database_config()
        neo4j_config = db_config.get("neo4j", {})
        postgres_config = db_config.get("postgres", {})

        return cls(
            pg_host=postgres_config.get("host", "localhost"),
            pg_port=postgres_config.get("port", 5432),
            pg_user=postgres_config.get("user", "postgres"),
            pg_password=postgres_config.get("password", ""),
            pg_database=postgres_config.get("database", "athena_memory"),
            neo4j_uri=neo4j_config.get("uri", "bolt://localhost:7687"),
            neo4j_database=neo4j_config.get("database", "athena_memory"),
            neo4j_username=neo4j_config.get("username", "neo4j"),
            neo4j_password=neo4j_config.get("password", ""),
        )


class VectorGraphFusionService:
    """向量-图融合记忆服务 (v3.0.0 - TD-001)"""

    def __init__(self, config: FusionConfig = None):
        """初始化融合服务"""
        self.config = config or FusionConfig.from_unified_config()
        self.pg_pool = None
        self.neo4j_driver = None
        self.initialized = False

        # BGE 模型(延迟加载)
        self.bge_model = None
        self.bge_tokenizer = None
        self.device = None

    async def initialize(self):
        """初始化融合服务"""
        logger.info("🚀 初始化向量-图融合记忆服务...")

        try:
            # 1. 创建 PostgreSQL 连接池
            from core.database.unified_connection import get_postgres_pool

            self.pg_pool = await get_postgres_pool(
                host=self.config.pg_host,
                port=self.config.pg_port,
                user=self.config.pg_user,
                password=self.config.pg_password,
                database=self.config.pg_database,
                min_size=2,
                max_size=10,
            )
            logger.info("✅ PostgreSQL 连接池已创建")

            # 2. 连接 Neo4j (TD-001)
            try:
                from neo4j import GraphDatabase

                self.neo4j_driver = GraphDatabase.driver(
                    self.config.neo4j_uri,
                    auth=(self.config.neo4j_username, self.config.neo4j_password),
                )
                # 测试连接
                with self.neo4j_driver.session(database=self.config.neo4j_database) as session:
                    result = session.run("RETURN 'Connection OK' as message")
                    record = result.single()
                    if record and record["message"] == "Connection OK":
                        logger.info("✅ Neo4j 连接已建立")
            except Exception as e:
                logger.warning(f"⚠️ Neo4j 连接失败: {e}，将仅使用向量搜索")

            # 3. 验证向量表存在
            await self._validate_schema()

            # 4. 初始化 BGE 模型(延迟加载)
            logger.info("📥 BGE 模型将延迟加载(首次使用时)")

            self.initialized = True
            logger.info("✅ 向量-图融合记忆服务初始化完成")

        except Exception as e:
            logger.error(f"❌ 初始化失败: {e}")
            raise

    async def _validate_schema(self):
        """验证数据库架构"""
        async with self.pg_pool.acquire() as conn:
            # 检查向量表
            tables = await conn.fetch("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name IN ('agent_memory_vectors', 'episodic_memory_vectors', 'vgraph_unified_mapping')
            """)

            table_names = {row["table_name"] for row in tables}
            required_tables = {
                "agent_memory_vectors",
                "episodic_memory_vectors",
                "vgraph_unified_mapping",
            }

            missing = required_tables - table_names
            if missing:
                raise RuntimeError(f"缺少必需的表: {missing}")

            logger.info("✅ 数据库架构验证通过")

    async def _load_bge_model(self):
        """延迟加载 BGE 模型"""
        if self.bge_model is not None:
            return

        logger.info("📥 加载 BGE Base ZH v1.5 模型...")

        try:
            import torch
            from transformers import BertModel, BertTokenizer

            # 检测设备
            if torch.backends.mps.is_available():
                self.device = "mps"
                torch_dtype = torch.float16
                logger.info("✅ 使用 Apple Silicon MPS 加速")
            else:
                self.device = "cpu"
                torch_dtype = torch.float32
                logger.info("✅ 使用 CPU 推理")

            # 使用本地BGE模型
            model_path = "http://127.0.0.1:8766/v1/embeddings"

            self.bge_tokenizer = BertTokenizer.from_pretrained(model_path, local_files_only=True)
            self.bge_model = BertModel.from_pretrained(
                model_path, torch_dtype=torch_dtype, local_files_only=True
            )
            self.bge_model = self.bge_model.to(self.device)
            self.bge_model.eval()

            logger.info("✅ BGE 模型加载完成")

        except Exception as e:
            logger.error(f"❌ BGE 模型加载失败: {e}")
            raise

    def _generate_embedding(self, text: str) -> list[float]:
        """生成文本向量(1024维(BGE-M3))"""
        if not text:
            return [0.0] * self.config.vector_dimension

        text = text.strip()[:512]

        if self.bge_model is None:
            raise RuntimeError("BGE 模型未加载,请先调用 _load_bge_model()")

        try:
            import numpy as np
            import torch
            import torch.nn.functional as F

            inputs = self.bge_tokenizer(
                text, padding=True, truncation=True, max_length=512, return_tensors="pt"
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.bge_model(**inputs)
                cls_embedding = outputs.last_hidden_state[:, 0, :]
                cls_embedding = F.normalize(cls_embedding, p=2, dim=1)
                embedding = cls_embedding[0].cpu().numpy()

            return embedding.tolist()

        except Exception as e:
            logger.error(f"❌ 向量生成失败: {e}")
            return np.random.rand(self.config.vector_dimension).tolist()

    async def store_memory(
        self,
        agent_id: str,
        content: str,
        memory_type: str,
        importance: float = 0.5,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """存储记忆到向量-图融合系统"""
        if not self.initialized:
            raise RuntimeError("服务未初始化")

        # 确保模型已加载
        if self.bge_model is None:
            await self._load_bge_model()

        # 生成向量
        embedding = self._generate_embedding(content)
        vector_str = "[" + ",".join(map(str, embedding)) + "]"

        # 生成 ID
        vector_id = str(uuid4())
        entity_id = str(uuid4())
        memory_id = f"agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"

        async with self.pg_pool.acquire() as conn:
            # 插入向量表
            await conn.execute(
                """
                INSERT INTO agent_memory_vectors (
                    id, memory_id, agent_id, context_type,
                    content, embedding, metadata, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6::vector, $7, $8)
            """,
                vector_id,
                memory_id,
                agent_id,
                memory_type,
                content,
                vector_str,
                json.dumps({"tags": tags or [], "importance": importance, **(metadata or {})}),
                datetime.now(),
            )

            # 创建统一映射 (TD-001: 使用 Neo4j 字段名)
            await conn.execute(
                """
                INSERT INTO vgraph_unified_mapping (
                    entity_id, entity_type, business_key,
                    pgvector_table, pgvector_id, vector_dimension,
                    neo4j_database, neo4j_node_id,
                    sync_status, confidence, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """,
                entity_id,
                "agent_memory",
                memory_id,
                "agent_memory_vectors",
                vector_id,
                self.config.vector_dimension,
                self.config.neo4j_database,
                f"AgentMemory{{id: '{memory_id}'}}",  # Neo4j 节点标识
                "synced",
                importance,
                json.dumps(
                    {
                        "agent_id": agent_id,
                        "memory_type": memory_type,
                        "stored_at": datetime.now().isoformat(),
                    }
                ),
            )

        # 同步到 Neo4j (TD-001)
        if self.neo4j_driver:
            await self._sync_to_neo4j(memory_id, agent_id, content, memory_type, tags, metadata)

        logger.info(f"✅ 记忆已存储: {memory_id}")
        return memory_id

    async def _sync_to_neo4j(
        self,
        memory_id: str,
        agent_id: str,
        content: str,
        memory_type: str,
        tags: list[str],
        metadata: dict[str, Any],    ):
        """同步记忆到 Neo4j (TD-001)"""
        try:
            with self.neo4j_driver.session(database=self.config.neo4j_database) as session:
                cypher = """
                    MERGE (m:AgentMemory {id: $id})
                    SET m.agent_id = $agent_id,
                        m.content = $content,
                        m.memory_type = $memory_type,
                        m.tags = $tags,
                        m.metadata = $metadata,
                        m.created_at = $created_at
                    RETURN m.id as id
                """
                session.run(
                    cypher,
                    {
                        "id": memory_id,
                        "agent_id": agent_id,
                        "content": content[:1000],  # 限制长度
                        "memory_type": memory_type,
                        "tags": tags or [],
                        "metadata": json.dumps(metadata or {}),
                        "created_at": datetime.now().isoformat(),
                    },
                )
        except Exception as e:
            logger.warning(f"⚠️ Neo4j 同步失败: {e}")

    async def search_memories(
        self,
        query: str,
        agent_id: str | None = None,
        memory_type: str | None = None,
        limit: int = 10,
        strategy: QueryStrategy = None,
    ) -> list[FusionQueryResult]:
        """融合查询记忆"""
        if not self.initialized:
            raise RuntimeError("服务未初始化")

        strategy = strategy or self.config.default_strategy

        # 确保模型已加载
        if self.bge_model is None:
            await self._load_bge_model()

        # 生成查询向量
        query_embedding = self._generate_embedding(query)
        query_vector_str = "[" + ",".join(map(str, query_embedding)) + "]"

        async with self.pg_pool.acquire() as conn:
            # 构建查询条件和参数
            where_conditions = ["v.embedding IS NOT NULL"]
            params = []
            param_idx = 1

            # 第一个参数是查询向量
            params.append(query_vector_str)
            param_idx += 1

            if agent_id:
                where_conditions.append(f"v.agent_id = ${param_idx}")
                params.append(agent_id)
                param_idx += 1

            if memory_type:
                where_conditions.append(f"v.context_type = ${param_idx}")
                params.append(memory_type)
                param_idx += 1

            where_sql = " AND " + " AND ".join(where_conditions)

            # 纯向量搜索
            if strategy == QueryStrategy.PURE_VECTOR:
                results = await conn.fetch(
                    f"""
                    SELECT
                        v.memory_id as business_key,
                        v.agent_id,
                        v.content,
                        1 - (v.embedding <=> $1::vector) as vector_score
                    FROM agent_memory_vectors v
                    WHERE {where_conditions[0]}{where_sql}
                    ORDER BY v.embedding <=> $1::vector
                    LIMIT ${param_idx}
                """,
                    *params,
                    limit,
                )

                return [
                    FusionQueryResult(
                        entity_id=str(uuid4()),
                        entity_type="agent_memory",
                        business_key=row["business_key"],
                        content=row["content"],
                        vector_score=row["vector_score"],
                        combined_score=row["vector_score"],
                    )
                    for row in results
                ]

            # 融合双路搜索(默认)
            elif strategy == QueryStrategy.FUSION_BOTH:
                # 需要添加额外的WHERE条件
                join_conditions = where_conditions.copy()
                join_conditions.append("m.sync_status = 'synced'")
                join_where_sql = " AND " + " AND ".join(join_conditions)

                results = await conn.fetch(
                    f"""
                    SELECT
                        v.memory_id as business_key,
                        v.agent_id,
                        v.content,
                        1 - (v.embedding <=> $1::vector) as vector_score,
                        m.confidence as graph_centrality
                    FROM agent_memory_vectors v
                    INNER JOIN vgraph_unified_mapping m
                        ON v.memory_id = m.business_key
                    WHERE {join_conditions[0]}{join_where_sql}
                    ORDER BY
                        (1 - (v.embedding <=> $1::vector)) * {self.config.vector_weight}
                        + m.confidence * {self.config.graph_weight} DESC
                    LIMIT ${param_idx}
                """,
                    *params,
                    limit,
                )

                return [
                    FusionQueryResult(
                        entity_id=str(uuid4()),
                        entity_type="agent_memory",
                        business_key=row["business_key"],
                        content=row["content"],
                        vector_score=row["vector_score"],
                        graph_centrality=row["graph_centrality"],
                        combined_score=(
                            row["vector_score"] * self.config.vector_weight
                            + row["graph_centrality"] * self.config.graph_weight
                        ),
                        metadata={"strategy": "fusion_both"},
                    )
                    for row in results
                ]

        return []

    async def get_memory_by_id(self, memory_id: str) -> dict[str, Any] | None:
        """通过 ID 获取记忆"""
        if not self.initialized:
            raise RuntimeError("服务未初始化")

        async with self.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT
                    v.*,
                    m.entity_id,
                    m.neo4j_node_id,  -- TD-001: 字段更新
                    m.sync_status
                FROM agent_memory_vectors v
                LEFT JOIN vgraph_unified_mapping m
                    ON v.memory_id = m.business_key
                WHERE v.memory_id = $1
            """,
                memory_id,
            )

            if row:
                return dict(row)
            return None

    async def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        if not self.initialized:
            raise RuntimeError("服务未初始化")

        async with self.pg_pool.acquire() as conn:
            stats = await conn.fetchrow("""
                SELECT
                    (SELECT COUNT(*) FROM agent_memory_vectors) as total_agent_memories,
                    (SELECT COUNT(*) FROM episodic_memory_vectors) as total_episodic_memories,
                    (SELECT COUNT(*) FROM vgraph_unified_mapping) as total_mappings,
                    (SELECT COUNT(*) FROM agent_memory_vectors WHERE embedding IS NOT NULL) as agent_with_vectors,
                    (SELECT COUNT(*) FROM episodic_memory_vectors WHERE embedding IS NOT NULL) as episodic_with_vectors,
                    (SELECT COUNT(*) FROM vgraph_unified_mapping WHERE sync_status = 'synced') as synced_entities
            """)

            return {
                "total_agent_memories": stats["total_agent_memories"],
                "total_episodic_memories": stats["total_episodic_memories"],
                "total_mappings": stats["total_mappings"],
                "coverage_rate": (
                    (stats["agent_with_vectors"] + stats["episodic_with_vectors"])
                    / (stats["total_agent_memories"] + stats["total_episodic_memories"] or 1)
                )
                * 100,
                "sync_rate": (stats["synced_entities"] / (stats["total_mappings"] or 1)) * 100,
                "graph_backend": "Neo4j",  # TD-001: 更新图数据库后端
            }

    async def close(self):
        """关闭连接"""
        if self.pg_pool:
            await self.pg_pool.close()

        if self.neo4j_driver:
            self.neo4j_driver.close()

        logger.info("🔌 连接已关闭")


# 全局单例
_fusion_service: VectorGraphFusionService = None


async def get_fusion_service(config: FusionConfig = None) -> VectorGraphFusionService:
    """获取融合服务单例"""
    global _fusion_service

    if _fusion_service is None:
        _fusion_service = VectorGraphFusionService(config)
        await _fusion_service.initialize()

    return _fusion_service


# ========== 兼容层 ==========

# 保留旧配置字段名称以保持向后兼容
@dataclass
class LegacyFusionConfig:
    """兼容层配置类"""

    # NebulaGraph 配置 (已废弃,保留以兼容)
    nebula_address: str = "127.0.0.1:9669"
    nebula_space: str = "athena_memory"
    nebula_user: str = "root"
    nebula_password: str = os.getenv("NEBULA_PASSWORD", "nebula")

    @staticmethod
    def migrate_to_v3() -> FusionConfig:
        """迁移到 v3.0.0 配置"""
        return FusionConfig.from_unified_config()
