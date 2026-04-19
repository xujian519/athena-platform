#!/usr/bin/env python3
"""
语义记忆 (Semantic Memory)
基于Neo4j + Qdrant的长期语义知识记忆

特点:
- Neo4j存储知识图谱(实体关系)
- Qdrant存储向量嵌入(语义搜索)
- 永久存储(不会过期)
- 支持复杂推理(图遍历)

作者: Athena平台团队
创建时间: 2026-01-22
版本: v2.0.0
"""

from __future__ import annotations
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from core.config.xiaona_config import get_config
from core.neo4j.neo4j_graph_client import Neo4jClient

logger = logging.getLogger(__name__)


class KnowledgeType(Enum):
    """知识类型"""

    FACT = "fact"  # 事实
    CONCEPT = "concept"  # 概念
    RULE = "rule"  # 规则
    PROCEDURE = "procedure"  # 程序
    RELATIONSHIP = "relationship"  # 关系


@dataclass
class SemanticMemoryItem:
    """语义记忆项"""

    knowledge_id: str
    knowledge_type: KnowledgeType
    content: str
    embedding: list[float] | None = None
    entities: list[str] | None = None
    relations: dict[str, list[str]] | None = None  # {"related_to": ["id1", "id2"]}
    metadata: dict[str, Any] | None = None
    confidence: float = 1.0
    created_at: str = None
    last_accessed: str = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.last_accessed is None:
            self.last_accessed = self.created_at
        if self.entities is None:
            self.entities = []
        if self.relations is None:
            self.relations = {}
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data["knowledge_type"] = self.knowledge_type.value
        return data


class SemanticMemory:
    """
    语义记忆 - 长期知识记忆系统

    基于 Neo4j + Qdrant:
    1. Neo4j: 存储结构化知识图谱
    2. Qdrant: 存储向量嵌入用于语义搜索

    特点:
    - 永久存储
    - 语义搜索
    - 知识推理
    - 关系网络
    """

    def __init__(
        self,
        collection_name: str = "semantic_memory",
        embedding_dim: int = 768,
        neo4j_client: Neo4jClient = None,
        qdrant_client: QdrantClient = None,
    ):
        """
        初始化语义记忆

        Args:
            collection_name: Qdrant集合名称
            embedding_dim: 向量维度
            neo4j_client: Neo4j客户端
            qdrant_client: Qdrant客户端
        """
        self.collection_name = collection_name
        self.embedding_dim = embedding_dim
        self._neo4j = neo4j_client
        self._qdrant = qdrant_client

        # 性能统计
        self.stats = {
            "total_stores": 0,
            "total_searches": 0,
            "neo4j_queries": 0,
            "qdrant_searches": 0,
        }

    async def _get_neo4j(self) -> Neo4jClient:
        """获取Neo4j客户端"""
        if self._neo4j is None:
            self._neo4j = Neo4jClient()
            await self._neo4j.connect()
        return self._neo4j

    async def _get_qdrant(self) -> QdrantClient:
        """获取Qdrant客户端"""
        if self._qdrant is None:
            config = await get_config()
            self._qdrant = QdrantClient(
                url=config.qdrant.url, api_key=config.qdrant.api_key or None
            )
            # 确保集合存在
            await self._ensure_collection()
        return self._qdrant

    async def _ensure_collection(self):
        """确保Qdrant集合存在"""
        qdrant = await self._get_qdrant()
        collections = qdrant.get_collections()  # 移除await
        collection_names = [c.name for c in collections.collections]

        if self.collection_name not in collection_names:
            qdrant.create_collection(  # 移除await
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self.embedding_dim, distance=Distance.COSINE),
            )
            logger.info(f"✅ 创建Qdrant集合: {self.collection_name}")

    async def _generate_embedding(self, text: str) -> list[float]:
        """生成文本嵌入向量"""
        # 这里应该调用实际的嵌入模型
        # 暂时使用随机向量(需要替换为真实模型)
        import hashlib


        # 使用文本哈希生成伪随机向量(仅为演示)
        hash_obj = hashlib.md5(text.encode('utf-8'), usedforsecurity=False)
        np.random.seed(int(hash_obj.hexdigest()[:8], 16))
        embedding = np.random.randn(self.embedding_dim).tolist()

        # 归一化
        norm = sum(x**2 for x in embedding) ** 0.5
        embedding = [x / norm for x in embedding]

        return embedding

    async def store(
        self,
        content: str,
        knowledge_type: KnowledgeType,
        entities: list[str] | None = None,
        relations: dict[str, list[str]] | None = None,
        metadata: dict[str, Any] | None = None,
        confidence: float = 1.0,
    ) -> str:
        """
        存储语义记忆

        Args:
            content: 知识内容
            knowledge_type: 知识类型
            entities: 涉及的实体列表
            relations: 与其他知识的关系
            metadata: 元数据
            confidence: 置信度

        Returns:
            知识ID
        """
        # 生成知识ID(使用UUID格式,Qdrant要求)
        import hashlib
        import time
        import uuid

        knowledge_id = str(uuid.uuid4())
        # 同时生成可读的字符串ID用于显示
        readable_id = (
            f"sm_{int(time.time() * 1000)}_{hashlib.md5(content.encode('utf-8'), usedforsecurity=False).hexdigest()[:8]}"
        )

        # 生成嵌入向量
        embedding = await self._generate_embedding(content)

        # 创建记忆项
        memory_item = SemanticMemoryItem(
            knowledge_id=readable_id,  # 使用可读ID
            knowledge_type=knowledge_type,
            content=content,
            embedding=embedding,
            entities=entities or [],
            relations=relations or {},
            metadata=metadata or {},
            confidence=confidence,
        )

        # 存储到Qdrant(向量搜索)
        qdrant = await self._get_qdrant()
        qdrant.upsert(  # 移除await,Qdrant客户端是同步的
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=knowledge_id,  # Qdrant使用UUID
                    vector=embedding,
                    payload={
                        "content": content,
                        "knowledge_type": knowledge_type.value,
                        "entities": entities or [],
                        "confidence": confidence,
                        "created_at": memory_item.created_at,
                        "readable_id": readable_id,  # 存储可读ID
                    },
                )
            ],
        )

        # 存储到Neo4j(知识图谱)
        neo4j = await self._get_neo4j()
        await self._store_to_neo4j(neo4j, memory_item)

        self.stats["total_stores"] += 1
        logger.info(f"✅ 语义记忆存储: {readable_id} ({knowledge_type.value})")

        return readable_id

    async def _store_to_neo4j(self, neo4j: Neo4jClient, memory: SemanticMemoryItem):
        """存储到Neo4j知识图谱"""
        # 创建知识节点
        cypher = """
        MERGE (k:Knowledge {id: $knowledge_id})
        SET k.content = $content,
            k.type = $knowledge_type,
            k.confidence = $confidence,
            k.created_at = $created_at
        """

        await neo4j.execute(
            cypher,
            parameters={
                "knowledge_id": memory.knowledge_id,
                "content": memory.content,
                "knowledge_type": memory.knowledge_type.value,
                "confidence": memory.confidence,
                "created_at": memory.created_at,
            },
        )

        # 创建实体关系
        for entity in memory.entities:
            entity_cypher = """
            MERGE (e:Entity {name: $entity_name})
            WITH e, k
            MATCH (k:Knowledge {id: $knowledge_id})
            MERGE (k)-[:MENTIONS]->(e)
            """
            await neo4j.execute(
                entity_cypher,
                parameters={"entity_name": entity, "knowledge_id": memory.knowledge_id},
            )

        # 创建知识间关系
        for relation_type, related_ids in memory.relations.items():
            for related_id in related_ids:
                relation_cypher = """
                MATCH (k1:Knowledge {id: $knowledge_id})
                MATCH (k2:Knowledge {id: $related_id})
                MERGE (k1)-[r:RELATED {type: $relation_type}]->(k2)
                """
                await neo4j.execute(
                    relation_cypher,
                    parameters={
                        "knowledge_id": memory.knowledge_id,
                        "related_id": related_id,
                        "relation_type": relation_type,
                    },
                )

    async def search(
        self,
        query: str,
        top_k: int = 10,
        knowledge_type: KnowledgeType | None = None,
        min_confidence: float = 0.0,
    ) -> list[SemanticMemoryItem]:
        """
        语义搜索记忆

        Args:
            query: 查询文本
            top_k: 返回结果数量
            knowledge_type: 知识类型过滤
            min_confidence: 最小置信度

        Returns:
            匹配的记忆列表
        """
        self.stats["total_searches"] += 1

        # 生成查询向量
        query_embedding = await self._generate_embedding(query)

        # Qdrant向量搜索
        qdrant = await self._get_qdrant()
        search_results = qdrant.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=top_k,
            query_filter=None,  # 可以添加过滤条件
        )

        # 解析结果
        memories = []
        for result in search_results:
            if result.score < min_confidence:
                continue

            payload = result.payload
            if knowledge_type and payload["knowledge_type"] != knowledge_type.value:
                continue

            memory = SemanticMemoryItem(
                knowledge_id=result.id,
                knowledge_type=KnowledgeType(payload["knowledge_type"]),
                content=payload["content"],
                confidence=payload.get("confidence", 1.0),
                entities=payload.get("entities", []),
                created_at=payload.get("created_at"),
            )
            memories.append(memory)

        self.stats["qdrant_searches"] += 1
        return memories

    async def get_related(
        self, knowledge_id: str, relation_type: str | None = None, max_depth: int = 2
    ) -> list[SemanticMemoryItem]:
        """
        获取相关知识(通过Neo4j图遍历)

        Args:
            knowledge_id: 起始知识ID
            relation_type: 关系类型过滤(可选)
            max_depth: 最大遍历深度

        Returns:
            相关知识列表
        """
        neo4j = await self._get_neo4j()
        self.stats["neo4j_queries"] += 1

        if relation_type:
            cypher = """
            MATCH (k:Knowledge {id: $knowledge_id})-[:RELATED {type: $relation_type}*1..{max_depth}]->(related:Knowledge)
            RETURN DISTINCT related
            LIMIT 50
            """
        else:
            cypher = """
            MATCH (k:Knowledge {id: $knowledge_id})-[:RELATED*1..{max_depth}]->(related:Knowledge)
            RETURN DISTINCT related
            LIMIT 50
            """

        results = await neo4j.execute_and_fetch(
            cypher,
            parameters={
                "knowledge_id": knowledge_id,
                "relation_type": relation_type,
                "max_depth": max_depth,
            },
        )

        memories = []
        for record in results:
            related = record.get("related")
            if related:
                memories.append(
                    SemanticMemoryItem(
                        knowledge_id=related.get("id"),
                        knowledge_type=KnowledgeType(related.get("type")),
                        content=related.get("content"),
                        confidence=related.get("confidence", 1.0),
                        created_at=related.get("created_at"),
                    )
                )

        return memories

    async def get_entity_knowledge(self, entity_name: str) -> list[SemanticMemoryItem]:
        """
        获取涉及特定实体的所有知识

        Args:
            entity_name: 实体名称

        Returns:
            相关知识列表
        """
        neo4j = await self._get_neo4j()

        cypher = """
        MATCH (e:Entity {name: $entity_name})<-[:MENTIONS]-(k:Knowledge)
        RETURN k
        ORDER BY k.confidence DESC
        LIMIT 100
        """

        results = await neo4j.execute_and_fetch(cypher, parameters={"entity_name": entity_name})

        memories = []
        for record in results:
            k = record.get("k")
            if k:
                memories.append(
                    SemanticMemoryItem(
                        knowledge_id=k.get("id"),
                        knowledge_type=KnowledgeType(k.get("type")),
                        content=k.get("content"),
                        confidence=k.get("confidence", 1.0),
                        created_at=k.get("created_at"),
                    )
                )

        return memories

    async def update(self, knowledge_id: str, updates: dict[str, Any]) -> bool:
        """
        更新知识

        Args:
            knowledge_id: 知识ID
            updates: 更新字段

        Returns:
            是否成功
        """
        # 更新Neo4j
        neo4j = await self._get_neo4j()

        set_clauses = []
        parameters = {"knowledge_id": knowledge_id}

        for key, value in updates.items():
            if key == "content":
                set_clauses.append("k.content = $content")
                parameters["content"] = value
            elif key == "confidence":
                set_clauses.append("k.confidence = $confidence")
                parameters["confidence"] = value
            elif key == "metadata":
                set_clauses.append("k.metadata = $metadata")
                parameters["metadata"] = json.dumps(value)

        if set_clauses:
            cypher = f"""
            MATCH (k:Knowledge {{id: $knowledge_id}})
            SET {', '.join(set_clauses)}
            """
            await neo4j.execute(cypher, parameters=parameters)

        # TODO: 更新Qdrant(需要重新生成嵌入)
        logger.info(f"✅ 知识更新: {knowledge_id}")
        return True

    async def delete(self, knowledge_id: str) -> bool:
        """
        删除知识

        Args:
            knowledge_id: 知识ID

        Returns:
            是否成功
        """
        # 从Qdrant删除
        qdrant = await self._get_qdrant()
        qdrant.delete(collection_name=self.collection_name, points_selector=[knowledge_id])

        # 从Neo4j删除
        neo4j = await self._get_neo4j()
        cypher = """
        MATCH (k:Knowledge {id: $knowledge_id})
        DETACH DELETE k
        """
        await neo4j.execute(cypher, parameters={"knowledge_id": knowledge_id})

        logger.info(f"🗑️  知识删除: {knowledge_id}")
        return True

    async def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        qdrant = await self._get_qdrant()
        collection_info = qdrant.get_collection(self.collection_name)

        return {
            **self.stats,
            "total_knowledge": collection_info.points_count,
            "collection_name": self.collection_name,
        }

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 检查Qdrant
            qdrant = await self._get_qdrant()
            qdrant.get_collections()

            # 检查Neo4j
            neo4j = await self._get_neo4j()
            neo4j.get_database_info()  # 移除await,同步方法

            return True
        except Exception as e:
            logger.error(f"❌ 语义记忆健康检查失败: {e}")
            return False


# 全局语义记忆实例
_semantic_memory = None


async def get_semantic_memory() -> SemanticMemory:
    """获取全局语义记忆实例"""
    global _semantic_memory
    if _semantic_memory is None:
        _semantic_memory = SemanticMemory()
    return _semantic_memory
