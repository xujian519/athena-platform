#!/usr/bin/env python3
"""
Qdrant集合名称统一配置
Unified Qdrant Collection Names Configuration

本文件统一管理所有Qdrant集合的名称、用途和配置
确保整个平台使用一致的集合命名规范

作者: 小诺·双鱼公主
创建时间: 2025-12-24
版本: v1.0.0
"""

from __future__ import annotations
from dataclasses import dataclass


# 集合维度标准
class VectorDimension(int):
    """向量维度标准"""
    STANDARD_768 = 768   # 标准BGE-base-zh维度
    STANDARD_1024 = 1024  # 大模型BGE-large-zh维度


class CollectionCategory(str):
    """集合分类"""
    PATENT = "patent"          # 专利相关
    LEGAL = "legal"            # 法律相关
    TECHNICAL = "technical"     # 技术术语
    MEMORY = "modules/modules/memory/modules/memory/modules/memory/memory"          # 记忆存储
    MULTIMODAL = "multimodal"  # 多模态
    KNOWLEDGE = "modules/modules/knowledge/knowledge/modules/knowledge/knowledge/modules/knowledge/knowledge/knowledge"    # 知识图谱


@dataclass
class QdrantCollectionConfig:
    """Qdrant集合配置"""
    # 集合标识
    key: str                          # 内部使用的唯一标识
    name: str                         # Qdrant中的实际集合名称

    # 集合描述
    display_name: str                 # 显示名称（中文）
    description: str                  # 详细描述
    category: str                     # 分类

    # 向量配置
    dimension: int                    # 向量维度
    distance: str = "Cosine"          # 距离度量

    # 状态
    is_primary: bool = False          # 是否为主要集合
    is_active: bool = True            # 是否启用

    # 元数据
    created_at: str = "2025-12-24"    # 创建日期
    version: str = "1.0.0"            # 版本号


# ==================== 统一的集合配置 ====================

# Qdrant集合配置注册表
QDRANT_COLLECTIONS: dict[str, QdrantCollectionConfig] = {

    # ========== 专利规则相关 ==========
    "patent_rules_complete": QdrantCollectionConfig(
        key="patent_rules_complete",
        name="patent_rules_bge_m3_v2",
        display_name="专利规则库 (BGE-M3 v2)",
        description="专利规则向量库，使用BGE-M3模型重建，包含专利法、实施细则、审查指南、司法解释等（208条）",
        category=CollectionCategory.PATENT,
        dimension=VectorDimension.STANDARD_1024,
        is_primary=True,
        version="2.0.0"
    ),

    "patent_guidelines": QdrantCollectionConfig(
        key="patent_guidelines",
        name="patent_guidelines",
        display_name="专利审查指南",
        description="专利审查指南向量库（376条）",
        category=CollectionCategory.PATENT,
        dimension=VectorDimension.STANDARD_1024,
        is_primary=False,
        version="1.0.0"
    ),

    "patent_decisions": QdrantCollectionConfig(
        key="patent_decisions",
        name="patent_decisions",
        display_name="专利审查决定书",
        description="专利审查决定书向量库（复审决定和无效宣告决定，1,054条样本）",
        category=CollectionCategory.PATENT,
        dimension=VectorDimension.STANDARD_1024,
        is_primary=False,
        version="1.0.0"
    ),

    # ========== 法律相关 ==========
    "laws_articles": QdrantCollectionConfig(
        key="laws_articles",
        name="laws_articles_bge_m3_v3",  # 更新到BGE-M3 v3版本 (2026-01-10)
        display_name="法律条款库 (BGE-M3)",
        description="Laws-1.0.0法律条款向量库，使用BGE-M3模型重建，包含宪法、民法典、刑法、行政法、经济法、社会法、诉讼法、司法解释等（53,903条）",
        category=CollectionCategory.LEGAL,
        dimension=VectorDimension.STANDARD_1024,
        is_primary=True,
        version="3.0.0"  # BGE-M3版本
    ),

    "legal_vectors": QdrantCollectionConfig(
        key="legal_vectors",
        name="legal_vectors",
        display_name="法律实体向量",
        description="法律实体向量库（50条测试数据）",
        category=CollectionCategory.LEGAL,
        dimension=VectorDimension.STANDARD_768,
        is_primary=False,
        version="1.0.0"
    ),

    # ========== 记忆存储 ==========
    "ai_family_shared_memory": QdrantCollectionConfig(
        key="ai_family_shared_memory",
        name="ai_family_shared_memory",
        display_name="AI家族共享记忆",
        description="AI家族（小诺、小娜等）的共享记忆向量库（21条）",
        category=CollectionCategory.MEMORY,
        dimension=VectorDimension.STANDARD_1024,
        is_primary=True,
        version="1.0.0"
    ),

    # ========== 多模态文件 ==========
    "multimodal_vectors": QdrantCollectionConfig(
        key="multimodal_vectors",
        name="multimodal_vectors",
        display_name="多模态文件向量",
        description="多模态文件处理系统的向量库，支持图像、文档、音频、视频等（3条测试数据）",
        category=CollectionCategory.MULTIMODAL,
        dimension=VectorDimension.STANDARD_768,
        is_primary=True,
        version="1.0.0"
    ),

    # ========== 通用/备用 ==========
    "patent_vectors": QdrantCollectionConfig(
        key="patent_vectors",
        name="patent_vectors",
        display_name="专利向量库（备用）",
        description="专利向量库，当前为空，预留用于扩展",
        category=CollectionCategory.PATENT,
        dimension=VectorDimension.STANDARD_768,
        is_primary=False,
        is_active=False,
        version="1.0.0"
    ),

    "test_storage_verification": QdrantCollectionConfig(
        key="test_storage_verification",
        name="test_storage_verification",
        display_name="存储验证测试",
        description="用于验证Qdrant存储功能的测试集合",
        category=CollectionCategory.KNOWLEDGE,
        dimension=VectorDimension.STANDARD_768,
        is_primary=False,
        is_active=False,
        version="1.0.0"
    ),
}


# ==================== 集合名称映射 ====================

# 旧名称到新名称的映射（用于兼容性）
COLLECTION_NAME_MIGRATION = {
    # 昨天报告中的旧名称 -> 当前实际名称
    "patent_rules_hq": "patent_rules_complete",
    "patent_rules_vectors": "patent_guidelines",
    "backup_legal_documents": "laws_articles",
    "patent_rules_complete": "patent_rules_complete",
    "patent_rules_unified_1024": "patent_rules_complete",
    "legal_vector_db": "legal_vectors",
    "general_memory_db": "ai_family_shared_memory",
}


# ==================== 集合分组 ====================

# 按分类分组
COLLECTIONS_BY_CATEGORY: dict[str, list[str]] = {
    CollectionCategory.PATENT: [
        "patent_rules_complete",
        "patent_guidelines",
        "patent_decisions",
        "patent_vectors"
    ],
    CollectionCategory.LEGAL: [
        "laws_articles",
        "legal_vectors"
    ],
    CollectionCategory.MEMORY: [
        "ai_family_shared_memory"
    ],
    CollectionCategory.MULTIMODAL: [
        "multimodal_vectors"
    ],
}


# 主要集合（每个分类一个）
PRIMARY_COLLECTIONS: dict[str, str] = {
    CollectionCategory.PATENT: "patent_rules_complete",
    CollectionCategory.LEGAL: "laws_articles_bge_m3_v3",  # 更新到BGE-M3 v3版本 (2026-01-10)
    CollectionCategory.MEMORY: "ai_family_shared_memory",
    CollectionCategory.MULTIMODAL: "multimodal_vectors",
}


# ==================== 工具函数 ====================

def get_collection_config(key: str) -> QdrantCollectionConfig | None:
    """获取集合配置"""
    return QDRANT_COLLECTIONS.get(key)


def get_collection_name(key: str) -> str | None:
    """获取集合的实际名称"""
    config = get_collection_config(key)
    return config.name if config else None


def get_collection_by_actual_name(actual_name: str) -> QdrantCollectionConfig | None:
    """根据实际名称反向查找配置"""
    for config in QDRANT_COLLECTIONS.values():
        if config.name == actual_name:
            return config
    return None


def get_primary_collection(category: str) -> str | None:
    """获取指定分类的主要集合名称"""
    return PRIMARY_COLLECTIONS.get(category)


def get_all_active_collections() -> list[QdrantCollectionConfig]:
    """获取所有启用的集合配置"""
    return [cfg for cfg in QDRANT_COLLECTIONS.values() if cfg.is_active]


def get_collections_by_category(category: str) -> list[QdrantCollectionConfig]:
    """获取指定分类的所有集合"""
    keys = COLLECTIONS_BY_CATEGORY.get(category, [])
    return [QDRANT_COLLECTIONS.get(k) for k in keys if k in QDRANT_COLLECTIONS]


def migrate_collection_name(old_name: str) -> str:
    """
    迁移旧集合名称到新名称

    Args:
        old_name: 旧的集合名称

    Returns:
        新的集合名称，如果没有映射则返回原名称
    """
    return COLLECTION_NAME_MIGRATION.get(old_name, old_name)


def validate_collection_config(collection_name: str, dimension: int) -> bool:
    """
    验证集合配置是否正确

    Args:
        collection_name: 集合名称
        dimension: 向量维度

    Returns:
        是否配置正确
    """
    config = get_collection_by_actual_name(collection_name)
    if not config:
        return False

    return config.dimension == dimension


# ==================== 配置摘要 ====================

def get_config_summary() -> dict[str, any]:
    """获取配置摘要信息"""
    active_collections = get_all_active_collections()

    total_vectors = 0
    category_stats = {}

    for cfg in active_collections:
        if cfg.category not in category_stats:
            category_stats[cfg.category] = {"count": 0, "collections": []}

        category_stats[cfg.category]["count"] += 1
        category_stats[cfg.category]["collections"].append(cfg.display_name)

    return {
        "total_collections": len(active_collections),
        "categories": len(category_stats),
        "category_stats": category_stats,
        "dimension_standard": {
            "768": VectorDimension.STANDARD_768,
            "1024": VectorDimension.STANDARD_1024
        }
    }


# ==================== 初始化/测试 ====================

if __name__ == "__main__":
    print("=" * 80)
    print("Qdrant集合名称统一配置")
    print("=" * 80)

    # 显示所有集合配置
    print("\n📚 集合配置列表:")
    print("-" * 80)

    for _key, config in QDRANT_COLLECTIONS.items():
        status = "✅" if config.is_active else "❌"
        primary = "🌟" if config.is_primary else "  "
        print(f"{status} {primary} {config.display_name}")
        print(f"   Key: {config.key}")
        print(f"   Collection: {config.name}")
        print(f"   Category: {config.category} | Dimension: {config.dimension} | Vectors: 待统计")
        print()

    # 显示主要集合
    print("\n🌟 主要集合（每个分类）:")
    print("-" * 80)
    for category, collection_key in PRIMARY_COLLECTIONS.items():
        config = QDRANT_COLLECTIONS.get(collection_key)
        if config:
            print(f"{category}: {config.name} ({config.display_name})")

    # 显示分类统计
    print("\n📊 分类统计:")
    print("-" * 80)
    summary = get_config_summary()
    for category, stats in summary["category_stats"].items():
        print(f"{category}: {stats['count']} 个集合")
        for coll in stats["collections"]:
            print(f"  - {coll}")

    print("\n" + "=" * 80)
    print(f"总计: {summary['total_collections']} 个集合，{summary['categories']} 个分类")
    print("=" * 80)
