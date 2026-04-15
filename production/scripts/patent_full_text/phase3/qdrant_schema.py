#!/usr/bin/env python3
"""
Qdrant向量数据库Schema定义
Patent Full Text Vector Database Schema

定义专利全文向量化存储的集合配置、向量类型和Payload结构

作者: Athena平台团队
创建时间: 2025-12-25
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class VectorType(Enum):
    """向量类型枚举"""
    # Layer 1: 全局检索层
    TITLE = "title"
    ABSTRACT = "abstract"
    IPC_CLASSIFICATION = "ipc_classification"

    # Layer 2: 核心内容层
    INDEPENDENT_CLAIM = "independent_claim"
    DEPENDENT_CLAIM = "dependent_claim"

    # Layer 3: 发明内容层
    TECHNICAL_PROBLEM = "technical_problem"
    TECHNICAL_SOLUTION = "technical_solution"
    BENEFICIAL_EFFECT = "beneficial_effect"
    EMBODIMENT = "embodiment"


class ClaimType(Enum):
    """权利要求类型"""
    INDEPENDENT = "independent"
    DEPENDENT = "dependent"


class ContentSection(Enum):
    """发明内容分段类型"""
    TECHNICAL_PROBLEM = "技术问题"
    TECHNICAL_SOLUTION = "技术方案"
    BENEFICIAL_EFFECT = "有益效果"
    EMBODIMENT = "具体实施方式"


@dataclass
class QdrantCollectionConfig:
    """Qdrant集合配置"""

    # 集合基本信息
    collection_name: str = "patent_full_text_v2"
    vector_size: int = 768  # BGE-base-zh-v1.5维度
    distance_metric: str = "Cosine"

    # 分片配置
    shard_number: int = 4  # 分片数
    replication_factor: int = 1  # 副本数

    # 优化配置
    optimizers_config: dict[str, Any] = field(default_factory=lambda: {
        "indexing_threshold": 20000  # 索引阈值
    })

    # 稀疏向量配置（可选）
    enable_sparse_vectors: bool = False
    sparse_index_type: str = "bm25"  # bm25 or tf-idf

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式（用于Qdrant API）"""
        config = {
            "vectors": {
                "size": self.vector_size,
                "distance": self.distance_metric
            },
            "shard_number": self.shard_number,
            "replication_factor": self.replication_factor,
            "optimizers_config": self.optimizers_config
        }

        if self.enable_sparse_vectors:
            config["sparse_vectors"] = {
                "bm25": {
                    "index": {
                        "type": self.sparse_index_type
                    }
                }
            }

        return config


@dataclass
class VectorPayload:
    """
    向量Payload数据结构

    每个向量携带的元数据信息
    """

    # ========== 必需字段（无默认值）===========
    # 基础信息
    patent_number: str
    publication_date: int  # YYYYMMDD格式
    application_date: int

    # IPC分类
    ipc_main_class: str
    ipc_subclass: str
    ipc_full_path: str

    # 专利类型
    patent_type: str  # invention/utility_model/design

    # 向量类型标识
    vector_type: str  # VectorType枚举值
    section: str  # 所属部分描述

    # ========== 可选字段（有默认值）===========
    # 内容标识
    text: str = ""  # 实际文本内容（前500字符）
    text_hash: str = ""  # MD5哈希值
    token_count: int = 0  # Token数量
    language: str = "zh"

    # 法律状态
    legal_status: str = "active"

    # 权利要求专用字段
    claim_number: int | None = None  # 权利要求编号
    claim_type: str | None = None  # independent/dependent

    # 发明内容专用字段
    content_section: str | None = None  # ContentSection枚举值
    chunk_index: int | None = 0  # 分块索引
    total_chunks: int | None = 1  # 总分块数

    def to_dict(self) -> dict[str, Any]:
        """转换为字典（用于Qdrant插入）"""
        payload = {
            "patent_number": self.patent_number,
            "publication_date": self.publication_date,
            "application_date": self.application_date,
            "ipc_main_class": self.ipc_main_class,
            "ipc_subclass": self.ipc_subclass,
            "ipc_full_path": self.ipc_full_path,
            "patent_type": self.patent_type,
            "legal_status": self.legal_status,
            "vector_type": self.vector_type,
            "section": self.section,
            "text": self.text,
            "text_hash": self.text_hash,
            "token_count": self.token_count,
            "language": self.language
        }

        # 添加可选字段
        if self.claim_number is not None:
            payload["claim_number"] = self.claim_number
        if self.claim_type is not None:
            payload["claim_type"] = self.claim_type
        if self.content_section is not None:
            payload["content_section"] = self.content_section
        if self.chunk_index is not None:
            payload["chunk_index"] = self.chunk_index
        if self.total_chunks is not None:
            payload["total_chunks"] = self.total_chunks

        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VectorPayload":
        """从字典创建实例"""
        return cls(**{
            k: v for k, v in data.items()
            if k in cls.__dataclass_fields__
        })


@dataclass
class VectorInfo:
    """
    向量信息

    用于返回向量化结果
    """
    vector_id: str
    vector_type: str
    patent_number: str
    payload: VectorPayload
    success: bool = True
    error_message: str | None = None


@dataclass
class VectorizationResultV2:
    """
    向量化结果V2

    包含三个层的向量化结果
    """
    patent_number: str
    success: bool

    # 各层向量结果
    layer1_vectors: list[VectorInfo] = field(default_factory=list)  # 全局检索层
    layer2_vectors: list[VectorInfo] = field(default_factory=list)  # 核心内容层
    layer3_vectors: list[VectorInfo] = field(default_factory=list)  # 发明内容层

    # 统计信息
    total_vector_count: int = 0
    processing_time: float = 0.0
    error_message: str | None = None

    @property
    def all_vectors(self) -> list[VectorInfo]:
        """获取所有向量"""
        return self.layer1_vectors + self.layer2_vectors + self.layer3_vectors

    def get_vectors_by_type(self, vector_type: VectorType) -> list[VectorInfo]:
        """按类型获取向量"""
        return [
            v for v in self.all_vectors
            if v.vector_type == vector_type.value
        ]

    def get_summary(self) -> dict[str, Any]:
        """获取结果摘要"""
        return {
            "patent_number": self.patent_number,
            "success": self.success,
            "total_vectors": self.total_vector_count,
            "layer1_count": len(self.layer1_vectors),
            "layer2_count": len(self.layer2_vectors),
            "layer3_count": len(self.layer3_vectors),
            "processing_time": self.processing_time,
            "vector_types": {
                vt.value: len(self.get_vectors_by_type(vt))
                for vt in VectorType
            }
        }


class QdrantSchemaManager:
    """Qdrant Schema管理器"""

    def __init__(self, config: QdrantCollectionConfig):
        self.config = config
        self.payload_index_config = self._get_payload_index_config()

    def _get_payload_index_config(self) -> dict[str, str]:
        """
        获取Payload索引配置

        为常用检索字段创建索引
        """
        return {
            # 基础信息索引
            "patent_number": "keyword",
            "publication_date": "integer",
            "application_date": "integer",

            # IPC分类索引
            "ipc_main_class": "keyword",
            "ipc_subclass": "keyword",

            # 专利类型索引
            "patent_type": "keyword",
            "legal_status": "keyword",

            # 向量类型索引
            "vector_type": "keyword",
            "claim_type": "keyword",
            "content_section": "keyword",

            # 权利要求索引
            "claim_number": "integer",

            # 分块索引
            "chunk_index": "integer",
            "total_chunks": "integer",

            # Token数量索引（用于过滤）
            "token_count": "integer"
        }

    def get_collection_config(self) -> dict[str, Any]:
        """获取完整集合配置"""
        return {
            **self.config.to_dict(),
            "payload_schema": self.payload_index_config
        }

    def get_create_collection_payload(self) -> dict[str, Any]:
        """
        获取创建集合的完整Payload

        Returns:
            可直接用于Qdrant create_collection API的字典
        """
        return {
            "collection_name": self.config.collection_name,
            **self.get_collection_config()
        }


# ========== 便捷函数 ==========

def get_default_config() -> QdrantCollectionConfig:
    """获取默认配置"""
    return QdrantCollectionConfig()


def get_schema_manager() -> QdrantSchemaManager:
    """获取Schema管理器"""
    return QdrantSchemaManager(get_default_config())


def create_payload_from_patent(
    patent_number: str,
    patent_data: dict[str, Any],
    vector_type: VectorType,
    **kwargs
) -> VectorPayload:
    """
    从专利数据创建Payload

    Args:
        patent_number: 专利号
        patent_data: 专利数据字典
        vector_type: 向量类型
        **kwargs: 额外字段

    Returns:
        VectorPayload实例
    """
    return VectorPayload(
        patent_number=patent_number,
        publication_date=int(patent_data.get("publication_date", "0").replace("-", "")),
        application_date=int(patent_data.get("application_date", "0").replace("-", "")),
        ipc_main_class=patent_data.get("ipc_main_class", ""),
        ipc_subclass=patent_data.get("ipc_subclass", ""),
        ipc_full_path=patent_data.get("ipc_full_path", ""),
        patent_type=patent_data.get("patent_type", "invention"),
        legal_status=patent_data.get("legal_status", "active"),
        vector_type=vector_type.value,
        section=vector_type.value,
        **kwargs
    )


# ========== 示例使用 ==========

def main() -> None:
    """示例使用"""
    print("=" * 70)
    print("Qdrant Schema定义")
    print("=" * 70)

    # 1. 获取默认配置
    config = get_default_config()
    print("\n📋 集合配置:")
    print(f"  名称: {config.collection_name}")
    print(f"  向量维度: {config.vector_size}")
    print(f"  距离度量: {config.distance_metric}")

    # 2. 获取Schema管理器
    manager = get_schema_manager()

    # 3. 获取完整配置
    full_config = manager.get_create_collection_payload()
    print("\n📦 完整配置:")
    import json
    print(json.dumps(full_config, indent=2, ensure_ascii=False))

    # 4. 创建示例Payload
    payload = create_payload_from_patent(
        patent_number="CN112233445A",
        patent_data={
            "publication_date": "2021-08-15",
            "application_date": "2020-12-01",
            "ipc_main_class": "G06F",
            "ipc_subclass": "G06F40/00",
            "ipc_full_path": "G→G06→G06F→G06F40",
            "patent_type": "invention"
        },
        vector_type=VectorType.ABSTRACT,
        text="一种基于人工智能的图像识别方法...",
        token_count=156
    )

    print("\n📝 Payload示例:")
    print(f"  专利号: {payload.patent_number}")
    print(f"  向量类型: {payload.vector_type}")
    print(f"  IPC分类: {payload.ipc_subclass}")
    print(f"  Token数: {payload.token_count}")

    # 5. 向量化结果示例
    result = VectorizationResultV2(
        patent_number="CN112233445A",
        success=True,
        layer1_vectors=[
            VectorInfo(
                vector_id="vec_001",
                vector_type=VectorType.TITLE.value,
                patent_number="CN112233445A",
                payload=payload
            )
        ],
        total_vector_count=1,
        processing_time=2.5
    )

    print("\n📊 向量化结果摘要:")
    summary = result.get_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
