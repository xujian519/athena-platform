#!/usr/bin/env python3
"""
统一数据模型 - Vector-Graph Unified Schema
为 NebulaGraph + pgvector 深度融合提供统一的数据抽象

作者: 小诺·双鱼公主
创建时间: 2025-12-28
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


class EntityType(Enum):
    """实体类型枚举"""

    MEMORY = "memory"  # 记忆系统
    LEGAL_DOCUMENT = "legal_document"  # 法律文档
    PATENT_RULE = "patent_rule"  # 专利规则
    PATENT_FULLTEXT = "patent_fulltext"  # 专利全文
    PATENT_JUDGMENT = "patent_judgment"  # 专利判决
    TRADEMARK = "trademark"  # 商标


class SyncDirection(Enum):
    """同步方向"""

    PG_TO_KG = "pg_to_kg"  # pgvector -> NebulaGraph
    KG_TO_PG = "kg_to_pg"  # NebulaGraph -> pgvector
    BIDIRECTIONAL = "bidirectional"  # 双向同步


class SyncStatus(Enum):
    """同步状态"""

    SYNCED = "synced"  # 已同步
    PENDING = "pending"  # 待同步
    PROCESSING = "processing"  # 同步中
    FAILED = "failed"  # 同步失败
    CONFLICT = "conflict"  # 冲突


@dataclass
class UnifiedEntityID:
    """统一实体标识符
    所有实体使用统一的 UUID 作为主键,提供跨数据库的唯一标识
    """

    entity_id: UUID = field(default_factory=uuid4)
    entity_type: EntityType = EntityType.MEMORY
    business_key: str = ""
    version: int = 1

    def to_pgvector_id(self) -> str:
        """转换为 pgvector 内部 ID"""
        return f"{self.entity_type.value}_{self.entity_id.hex}"

    def to_nebula_id(self) -> str:
        """转换为 NebulaGraph 顶点 ID"""
        return f"v{self.entity_type.value}_{self.entity_id.hex[:16]}"

    def to_vector_key(self) -> str:
        """向量缓存键"""
        return f"vec:{self.entity_type.value}:{self.business_key}"

    def to_graph_key(self) -> str:
        """图谱缓存键"""
        return f"graph:{self.entity_type.value}:{self.business_key}"

    def __str__(self) -> str:
        return f"{self.entity_type.value}:{self.business_key}"


@dataclass
class VectorGraphMapping:
    """向量-图谱映射记录
    存储在 vgraph_unified_mapping 表中
    """

    # 统一实体标识
    entity_id: UUID
    entity_type: str
    business_key: str

    # pgvector 映射
    pgvector_table: str
    pgvector_id: UUID
    vector_dimension: int

    # NebulaGraph 映射
    nebula_space: str
    nebula_vertex_id: str
    nebula_tags: list[str]

    # 同步状态
    sync_status: SyncStatus = SyncStatus.SYNCED
    sync_direction: SyncDirection = SyncDirection.BIDIRECTIONAL
    last_sync_time: datetime = field(default_factory=datetime.now)
    sync_version: int = 0

    # 索引优化
    confidence: float = 1.0
    embedding_quality_score: float | None = None
    graph_centrality_score: float | None = None

    # 元数据
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "entity_id": str(self.entity_id),
            "entity_type": self.entity_type,
            "business_key": self.business_key,
            "pgvector_table": self.pgvector_table,
            "pgvector_id": str(self.pgvector_id),
            "vector_dimension": self.vector_dimension,
            "nebula_space": self.nebula_space,
            "nebula_vertex_id": self.nebula_vertex_id,
            "nebula_tags": self.nebula_tags,
            "sync_status": self.sync_status.value,
            "sync_direction": self.sync_direction.value,
            "last_sync_time": self.last_sync_time.isoformat(),
            "sync_version": self.sync_version,
            "confidence": self.confidence,
            "embedding_quality_score": self.embedding_quality_score,
            "graph_centrality_score": self.graph_centrality_score,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class UnifiedEntity:
    """统一实体
    表示一个完整的业务实体,包含向量特征和图特征
    """

    # 基础标识
    unified_id: UnifiedEntityID

    # 内容信息
    title: str = ""
    content: str = ""
    summary: str = ""

    # 向量特征
    vector_embedding: list[float] | None = None
    vector_dimension: int = 1024
    vector_id: str | None = None

    # 图特征
    importance_score: float = 0.0
    centrality_score: float = 0.0
    page_rank: float = 0.0

    # 元数据
    metadata: dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def get_pgvector_payload(self) -> dict[str, Any]:
        """获取 pgvector 存储的 payload"""
        return {
            "entity_id": str(self.unified_id.entity_id),
            "entity_type": self.unified_id.entity_type.value,
            "business_key": self.unified_id.business_key,
            "title": self.title,
            "content": self.content,
            "summary": self.summary,
            "nebula_vertex_id": self.unified_id.to_nebula_id(),
            "metadata": self.metadata,
        }

    def get_nebula_properties(self) -> dict[str, Any]:
        """获取 NebulaGraph 存储的属性"""
        return {
            "entity_id": str(self.unified_id.entity_id),
            "entity_type": self.unified_id.entity_type.value,
            "business_key": self.unified_id.business_key,
            "title": self.title,
            "content": self.content,
            "summary": self.summary,
            "vector_id": self.vector_id,
            "vector_dimension": self.vector_dimension,
            "importance_score": self.importance_score,
            "centrality_score": self.centrality_score,
            "page_rank": self.page_rank,
            "metadata": str(self.metadata),  # NebulaGraph 存储为字符串
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class SemanticRelation:
    """语义关系(基于向量相似度)"""

    source_id: UUID
    target_id: UUID
    similarity_score: float
    vector_distance: float
    calculation_method: str = "cosine"
    confidence: float = 1.0
    calculated_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class BusinessRelation:
    """业务关系"""

    source_id: UUID
    target_id: UUID
    relation_type: str
    weight: float = 1.0
    confidence: float = 1.0
    source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


# 工厂函数
def create_memory_entity(
    business_key: str, title: str, content: str, vector_embedding: list[float] | None = None
) -> UnifiedEntity:
    """创建记忆系统实体"""
    unified_id = UnifiedEntityID(entity_type=EntityType.MEMORY, business_key=business_key)
    return UnifiedEntity(
        unified_id=unified_id,
        title=title,
        content=content,
        summary=content[:200] if len(content) > 200 else content,
        vector_embedding=vector_embedding,
        vector_dimension=768,
    )


def create_patent_entity(
    business_key: str,
    title: str,
    content: str,
    vector_embedding: list[float] | None = None,
    entity_type: EntityType = EntityType.PATENT_RULE,
) -> UnifiedEntity:
    """创建专利实体"""
    unified_id = UnifiedEntityID(entity_type=entity_type, business_key=business_key)
    return UnifiedEntity(
        unified_id=unified_id,
        title=title,
        content=content,
        summary=content[:200] if len(content) > 200 else content,
        vector_embedding=vector_embedding,
        vector_dimension=1024,
    )


# 使用示例
if __name__ == "__main__":
    # 创建统一实体ID
    uid = UnifiedEntityID(entity_type=EntityType.PATENT_RULE, business_key="CN123456")
    print(f"统一ID: {uid}")
    print(f"pgvector ID: {uid.to_pgvector_id()}")
    print(f"Nebula ID: {uid.to_nebula_id()}")

    # 创建完整实体
    entity = create_patent_entity(
        business_key="CN123456", title="专利审查指南", content="这是一份专利审查指南..."
    )
    print(f"\n实体标题: {entity.title}")
    print(f"pgvector payload: {entity.get_pgvector_payload()}")
    print(f"Nebula properties: {entity.get_nebula_properties()}")
