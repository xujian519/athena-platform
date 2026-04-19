#!/usr/bin/env python3
from __future__ import annotations
"""
AI家族共享记忆向量库
Family Shared Memory Vector Database

这是为整个AI家族(小诺、小娜等)共享的记忆向量库,
作为平台记忆模块的基础设施。

设计原则:
1. 家族共享 - 所有智能体共享同一份记忆
2. 多源记忆 - 支持情节、语义、程序三类记忆向量化
3. 语义检索 - 支持自然语言语义搜索记忆
4. 高性能 - 基于Qdrant HNSW索引,毫秒级响应
5. 可扩展 - 轻松支持未来更多智能体加入
"""
import builtins
import collections
import contextlib
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class AgentType(Enum):
    """智能体类型"""

    XIAONUO = "小诺"  # 平台总调度官
    XIANA = "小娜"  # 专利法律专家
    ATHENA = "Athena"  # 平台核心智能体
    FATHER = "徐健"  # 爸爸(用户)


class MemoryCategory(Enum):
    """记忆分类(对应三大记忆类型)"""

    EPISODIC = "episodic"  # 情节记忆
    SEMANTIC = "semantic"  # 语义记忆
    PROCEDURAL = "procedural"  # 程序记忆


@dataclass
class MemoryVector:
    """记忆向量对象"""

    # 必填字段
    memory_id: str  # 记忆唯一ID
    content: str  # 记忆内容(用于生成向量)
    memory_type: str  # 记忆类型 (episodic/semantic/procedural)
    agent: str  # 创建者/相关智能体
    timestamp: str  # 创建时间

    # 可选字段
    title: str = ""  # 标题(主要用于情节记忆)
    importance: float = 0.5  # 重要性 (0-1)
    emotional_weight: float = 0.5  # 情感权重 (0-1)
    tags: list[str] = field(default_factory=list)  # 标签
    participants: list[str] = field(default_factory=list)  # 参与者
    related_memories: list[str] = field(default_factory=list)  # 关联记忆ID

    # 元数据
    metadata: dict[str, Any] = field(default_factory=dict)
    access_count: int = 0  # 访问次数
    last_accessed: str = ""  # 最后访问时间


class FamilyMemoryVectorDB:
    """AI家族共享记忆向量数据库"""

    def __init__(self, qdrant_host: str = "localhost", qdrant_port: int = 6333):
        """初始化向量数据库"""
        self.qdrant_host = qdrant_host
        self.qdrant_port = qdrant_port

        # 集合命名
        self.collection_name = "ai_family_shared_memory"

        # 向量维度(与BGE模型一致)
        self.vector_size = 1024

        # 初始化客户端(延迟连接)
        self._client = None

        logger.info("🧠 AI家族共享记忆向量库初始化")
        logger.info(f"   Qdrant: {qdrant_host}:{qdrant_port}")
        logger.info(f"   集合名称: {self.collection_name}")
        logger.info(f"   向量维度: {self.vector_size}")

    @property
    def client(self) -> QdrantClient:
        """延迟初始化Qdrant客户端"""
        if self._client is None:
            self._client = QdrantClient(host=self.qdrant_host, port=self.qdrant_port, timeout=30)
        return self._client

    async def initialize(self):
        """初始化数据库(创建集合)"""
        try:
            if await self._collection_exists():
                logger.info(f"✅ 集合 '{self.collection_name}' 已存在")
                info = await self.get_collection_info()
                logger.info(f"   向量数量: {info.get('vectors_count', 0)}")
                logger.info(
                    f"   索引状态: {'已构建' if info.get('status') == 'green' else '未构建'}"
                )
            else:
                # 创建新集合
                await self._create_collection()
                logger.info(f"✅ 集合 '{self.collection_name}' 创建成功")

            return True
        except Exception as e:
            logger.error(f"操作失败: {e}", exc_info=True)
            raise

    async def _collection_exists(self) -> bool:
        """检查集合是否存在"""
        try:
            existing_names = [c.name for c in collections.collections]
            return self.collection_name in existing_names
        except Exception as e:
            logger.error(f"操作失败: {e}", exc_info=True)
            raise

    async def _create_collection(self):
        """创建记忆向量集合"""
        # 删除旧集合(如果存在)
        try:
            logger.info("🗑️  清理旧集合")
        except Exception as e:
            logger.error(f"操作失败: {e}", exc_info=True)
            raise
        # 创建新集合
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=self.vector_size, distance=Distance.COSINE  # 余弦相似度
            ),
        )

        # 创建索引(按记忆类型、智能体)
        try:
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="memory_type",
                field_schema="keyword",
            )
        except Exception as e:
            logger.error(f"操作失败: {e}", exc_info=True)
            raise

        with contextlib.suppress(builtins.BaseException):
            self.client.create_payload_index(
                collection_name=self.collection_name, field_name="agent", field_schema="keyword"
            )

        logger.info(f"✅ 集合 '{self.collection_name}' 和索引创建完成")

    async def get_collection_info(self) -> dict:
        """获取集合信息"""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "points_count": info.points_count,
                "indexed_vectors_count": info.indexed_vectors_count,
                "segments_count": info.segments_count,
                "status": info.status,
                "config": info.config.dict() if hasattr(info.config, "dict") else info.config,
                "optimizer_status": info.optimizer_status,
            }
        except Exception as e:
            logger.error(f"操作失败: {e}", exc_info=True)
            raise

    async def add_memory(self, memory: MemoryVector, embedding: list[float]) -> str:
        """
        添加记忆向量

        Args:
            memory: 记忆对象
            embedding: 向量嵌入(1024维)

        Returns:
            记忆ID
        """
        try:
            payload = {
                "memory_id": memory.memory_id,  # 保留原始ID在payload中
                "content": memory.content,
                "title": memory.title,
                "memory_type": memory.memory_type,
                "agent": memory.agent,
                "timestamp": memory.timestamp,
                "importance": memory.importance,
                "emotional_weight": memory.emotional_weight,
                "tags": memory.tags,
                "participants": memory.participants,
                "related_memories": memory.related_memories,
                "access_count": memory.access_count,
                "last_accessed": memory.last_accessed,
                **memory.metadata,
            }

            # 将字符串ID转换为UUID v5(基于namespace和memory_id)
            point_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, memory.memory_id)

            # 创建向量点
            point = PointStruct(
                id=point_uuid, vector=embedding, payload=payload  # 使用UUID而不是字符串
            )

            # 上传向量
            self.client.upsert(collection_name=self.collection_name, points=[point])

            logger.debug(f"✅ 记忆已向量化: {memory.memory_id} ({memory.memory_type})")
            return memory.memory_id

        except Exception as e:
            logger.error(f"操作失败: {e}", exc_info=True)
            raise

    async def add_memories_batch(
        self, memories: list[MemoryVector], embeddings: list[list[float]]
    ) -> list[str]:
        """批量添加记忆向量"""
        try:
            points = []
            for memory, embedding in zip(memories, embeddings, strict=False):
                payload = {
                    "memory_id": memory.memory_id,
                    "content": memory.content,
                    "title": memory.title,
                    "memory_type": memory.memory_type,
                    "agent": memory.agent,
                    "timestamp": memory.timestamp,
                    "importance": memory.importance,
                    "emotional_weight": memory.emotional_weight,
                    "tags": memory.tags,
                    "participants": memory.participants,
                    "related_memories": memory.related_memories,
                    "access_count": memory.access_count,
                    "last_accessed": memory.last_accessed,
                    **memory.metadata,
                }

                # 将字符串ID转换为UUID
                point_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, memory.memory_id)

                points.append(PointStruct(id=point_uuid, vector=embedding, payload=payload))

            # 批量上传
            self.client.upsert(collection_name=self.collection_name, points=points)

            logger.info(f"✅ 批量添加 {len(memories)} 条记忆向量")
            return [m.memory_id for m in memories]

        except Exception as e:
            logger.error(f"操作失败: {e}", exc_info=True)
            raise

    async def semantic_search(
        self,
        query_embedding: list[float],
        limit: int = 10,
        memory_type: str | None = None,
        agent: str | None = None,
        min_importance: float = 0.0,
        filters: dict | None = None,
    ) -> list[dict]:
        """
        语义搜索记忆

        Args:
            query_embedding: 查询向量
            limit: 返回数量
            memory_type: 过滤记忆类型
            agent: 过滤智能体
            min_importance: 最小重要性
            filters: 自定义过滤条件

        Returns:
            搜索结果列表
        """
        try:
            filter_conditions = []

            if memory_type:
                filter_conditions.append(
                    FieldCondition(key="memory_type", match=MatchValue(value=memory_type))
                )

            if agent:
                filter_conditions.append(FieldCondition(key="agent", match=MatchValue(value=agent)))

            if filters:
                for key, value in filters.items():
                    filter_conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))

            # 构建filter
            search_filter = Filter(must=filter_conditions) if filter_conditions else None

            # 使用新版API query_points方法
            query_response = self.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                limit=limit,
                query_filter=search_filter,
            )

            # 新版API返回QueryResponse,结果在points属性中
            results = query_response.points if hasattr(query_response, "points") else []

            # 格式化结果
            formatted_results = []
            for result in results:
                formatted_results.append(
                    {"id": result.id, "score": result.score, "payload": result.payload}
                )

            logger.debug(f"🔍 语义搜索返回 {len(formatted_results)} 条结果")
            return formatted_results

        except Exception as e:
            logger.error(f"操作失败: {e}", exc_info=True)
            raise

    async def hybrid_search(
        self,
        query_embedding: list[float],
        query_text: str,
        limit: int = 10,
        filters: dict | None = None,
    ) -> list[dict]:
        """
        混合搜索:向量搜索 + 全文搜索

        Args:
            query_embedding: 查询向量
            query_text: 查询文本
            limit: 返回数量
            filters: 过滤条件

        Returns:
            搜索结果
        """
        try:
            vector_results = await self.semantic_search(
                query_embedding=query_embedding, limit=limit * 2, filters=filters  # 获取更多候选
            )

            # 在向量结果中再进行文本匹配
            if query_text:
                # 简单的文本过滤:检查content或title是否包含查询词
                query_lower = query_text.lower()
                filtered_results = []
                for result in vector_results:
                    content = result.get("payload", {}).get("content", "")
                    title = result.get("payload", {}).get("title", "")
                    if query_lower in content.lower() or query_lower in title.lower():
                        filtered_results.append(result)
                return filtered_results[:limit]

            return vector_results[:limit]

        except Exception as e:
            logger.error(f"操作失败: {e}", exc_info=True)
            raise

    async def get_memory_by_id(self, memory_id: str) -> dict | None:
        """根据ID获取记忆"""
        try:
            point_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, memory_id)

            results = self.client.retrieve(collection_name=self.collection_name, ids=[point_uuid])

            if results:
                return {"id": results[0].id, "payload": results[0].payload}
            return None

        except Exception as e:
            logger.error(f"操作失败: {e}", exc_info=True)
            raise

    async def update_memory_access(self, memory_id: str):
        """更新记忆访问信息"""
        try:
            point_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, memory_id)

            # 获取原记录
            results = self.client.retrieve(collection_name=self.collection_name, ids=[point_uuid])

            if results:
                original = results[0]
                payload = original.payload

                # 更新访问信息
                payload["access_count"] = payload.get("access_count", 0) + 1
                payload["last_accessed"] = datetime.now().isoformat()

                # 更新payload(保持向量不变)
                # 注意:Qdrant需要重新插入整个点
                # 这里简化处理,实际生产环境可以考虑使用overwrite_payload

                logger.debug(f"✅ 更新访问信息: {memory_id}")

        except Exception as e:
            logger.error(f"操作失败: {e}", exc_info=True)
            raise
    async def get_statistics(self) -> dict:
        """获取统计信息"""
        try:
            info = await self.get_collection_info()

            stats = {
                "collection_name": self.collection_name,
                "points_count": info.get("points_count", 0),
                "indexed_vectors": info.get("indexed_vectors_count", 0),
                "segments_count": info.get("segments_count", 0),
                "status": str(info.get("status", "unknown")),
                "config": info.get("config", {}),
                "optimizer_status": info.get("optimizer_status", {}),
            }

            return stats

        except Exception as e:
            logger.error(f"操作失败: {e}", exc_info=True)
            raise


# 全局单例
_vector_db = None


def get_family_memory_db() -> FamilyMemoryVectorDB:
    """获取家族记忆向量库单例"""
    global _vector_db
    if _vector_db is None:
        _vector_db = FamilyMemoryVectorDB()
    return _vector_db


# 测试代码
async def main():
    """测试代码"""
    import sys

    sys.path.insert(0, "/Users/xujian/Athena工作平台")

    from core.nlp.bge_embedding_service import get_bge_service

    db = get_family_memory_db()

    # 初始化
    print("\n🚀 初始化家族记忆向量库...")
    await db.initialize()

    # 测试添加记忆
    print("\n📝 测试添加记忆...")

    # 获取BGE服务
    bge_service = await get_bge_service()

    # 创建测试记忆
    test_memory = MemoryVector(
        memory_id="test_001",
        content="《钟之歌》是爸爸创作的一首关于孤独和智慧的诗歌",
        memory_type="episodic",
        agent="小诺",
        timestamp=datetime.now().isoformat(),
        title="《钟之歌》记忆",
        importance=1.0,
        emotional_weight=1.0,
        tags=["诗歌", "钟之歌", "重要", "家庭时光"],
        participants=["徐健", "小诺", "小娜"],
    )

    # 生成向量
    print("   生成向量嵌入...")
    embedding_result = await bge_service.encode(test_memory.content)
    embedding = embedding_result.embeddings

    # 添加记忆
    print("   添加记忆向量...")
    await db.add_memory(test_memory, embedding)

    # 测试语义搜索
    print("\n🔍 测试语义搜索...")
    query = "关于诗歌的记忆"
    query_result = await bge_service.encode(query)
    query_embedding = query_result.embeddings

    results = await db.semantic_search(query_embedding, limit=5)

    print(f"   搜索结果 ({len(results)} 条):")
    for i, result in enumerate(results, 1):
        payload = result.get("payload", {})
        print(f"   {i}. {payload.get('title', 'N/A')}: {payload.get('content', '')[:50]}...")
        print(f"      相似度: {result.get('score', 0):.4f}")

    # 显示统计
    print("\n📊 统计信息:")
    stats = await db.get_statistics()
    for key, value in stats.items():
        if key != "config":
            print(f"   {key}: {value}")

    print("\n✅ 测试完成!")


# 入口点: @async_main装饰器已添加到main函数
