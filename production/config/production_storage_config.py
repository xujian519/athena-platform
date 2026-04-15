#!/usr/bin/env python3
"""
Athena生产环境存储配置
Production Storage Configuration for Athena Platform

整合三大向量库+知识图谱系统：
1. 法律向量库 + legal_kg知识图谱
2. 专利规则向量库 + patent_rules知识图谱
3. 专利决定书向量库 + patent_decisions知识图谱

作者: Athena AI Team
创建时间: 2025-12-28
版本: v2.0.0
"""

from __future__ import annotations
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


def get_env_password(key: str, default: str | None = None) -> str:
    """从环境变量获取密码，如果不存在则使用默认值或抛出异常"""
    value = os.environ.get(key, default)
    if not value:
        raise ValueError(f"密码环境变量 {key} 未设置，请检查 .env 文件")
    return value


# ==================== 环境定义 ====================

class Environment(str, Enum):
    """环境类型"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class StorageType(str, Enum):
    """存储类型"""
    VECTOR = "vector"      # 向量数据库
    GRAPH = "graph"        # 图数据库
    HYBRID = "hybrid"      # 混合存储


# ==================== Qdrant配置 ====================

@dataclass
class QdrantCollectionConfig:
    """Qdrant集合配置"""
    # 集合标识
    key: str                          # 内部唯一标识
    name: str                         # Qdrant中的集合名称

    # 集合描述
    display_name: str                 # 显示名称（中文）
    description: str                  # 详细描述
    category: str                     # 分类 (legal/patent/decision)

    # 向量配置
    dimension: int                    # 向量维度
    distance: str = "Cosine"          # 距离度量
    vector_model: str = "BGE-large-zh"  # 向量模型

    # 关联的知识图谱
    linked_graph_space: str | None = None  # 关联的NebulaGraph图空间

    # 状态
    is_primary: bool = False          # 是否为主要集合
    is_active: bool = True            # 是否启用

    # 统计信息（运行时更新）
    vector_count: int = 0             # 向量数量
    indexed_count: int = 0            # 已索引数量

    # 元数据
    created_at: str = "2025-12-28"
    version: str = "2.0.0"


# ==================== NebulaGraph配置 ====================

@dataclass
class NebulaSpaceConfig:
    """NebulaGraph图空间配置"""
    # 空间标识
    key: str                          # 内部唯一标识
    name: str                         # NebulaGraph中的空间名称

    # 空间描述
    display_name: str                 # 显示名称（中文）
    description: str                  # 详细描述
    category: str                     # 分类 (legal/patent/decision)

    # 关联的向量库
    linked_vector_collection: str | None = None  # 关联的Qdrant集合

    # 空间配置
    partition_num: int = 10
    replica_factor: int = 1
    vid_type: str = "FIXED_STRING(32)"

    # Schema定义
    tags: dict[str, list[str]] = field(default_factory=dict)
    edges: dict[str, list[str]] = field(default_factory=dict)

    # 统计信息（运行时更新）
    vertex_count: int = 0
    edge_count: int = 0

    # 状态
    is_primary: bool = False
    is_active: bool = True

    # 元数据
    created_at: str = "2025-12-28"
    version: str = "2.0.0"


@dataclass
class NebulaConnectionConfig:
    """NebulaGraph连接配置"""
    hosts: list[str]                  # 主机列表
    port: int                         # 端口
    username: str                     # 用户名
    password: str                     # 密码

    # 连接池配置
    max_connections: int = 10
    timeout: int = 60000              # 超时（毫秒）

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "hosts": self.hosts,
            "port": self.port,
            "username": self.username,
            "password": self.password,
            "max_connections": self.max_connections,
            "timeout": self.timeout
        }


# ==================== 生产环境配置 ====================

@dataclass
class ProductionStorageConfig:
    """生产环境存储配置"""

    # 环境信息
    environment: Environment = Environment.PRODUCTION

    # Qdrant配置
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None

    # NebulaGraph连接配置
    nebula_connection: NebulaConnectionConfig = field(default_factory=lambda: NebulaConnectionConfig(
        hosts=["127.0.0.1"],
        port=9669,
        username="root",
        password=get_env_password("NEBULA_PASSWORD"),
        max_connections=20,
        timeout=120000
    ))

    # 向量库集合配置
    qdrant_collections: dict[str, QdrantCollectionConfig] = field(default_factory=dict)

    # 知识图谱空间配置
    nebula_spaces: dict[str, NebulaSpaceConfig] = field(default_factory=dict)

    def __post_init__(self):
        """初始化后配置三大系统"""
        self._init_legal_system()
        self._init_patent_rules_system()
        self._init_patent_decisions_system()

    def _init_legal_system(self) -> Any:
        """初始化法律向量库+知识图谱系统"""
        # Qdrant集合
        self.qdrant_collections["laws_articles"] = QdrantCollectionConfig(
            key="laws_articles",
            name="laws_articles",
            display_name="法律条款库",
            description="Laws-1.0.0法律条款向量库，包含宪法、民法典、刑法、行政法、经济法、社会法、诉讼法、司法解释等（53,903条）",
            category="legal",
            dimension=1024,
            distance="Cosine",
            vector_model="BGE-large-zh-v1.5",
            linked_graph_space="legal_kg",
            is_primary=True,
            vector_count=53903,
            version="2.0.0"
        )

        # NebulaGraph空间
        self.nebula_spaces["legal_kg"] = NebulaSpaceConfig(
            key="legal_kg",
            name="legal_kg",
            display_name="法律知识图谱",
            description="法律领域知识图谱，包含法律、条款、章节等节点及其关系（144,633节点）",
            category="legal",
            linked_vector_collection="laws_articles",
            partition_num=20,
            replica_factor=1,
            tags={
                "Law": ["name", "full_name", "category", "level"],
                "Article": ["law_name", "article_num", "content", "full_ref"],
                "Chapter": ["law_name", "chapter_num", "title"],
                "Section": ["law_name", "section_num", "title"],
                "LegalConcept": ["name", "definition", "category"]
            },
            edges={
                "HAS_ARTICLE": ["effective_date"],
                "BELONGS_TO_CHAPTER": [],
                "BELONGS_TO_SECTION": [],
                "RELATED_TO": ["relation_type", "confidence"],
                "CITES": ["context", "frequency"],
                "MODIFIES": ["modification_date", "description"],
                "REVOKES": ["revocation_date", "reason"]
            },
            vertex_count=144633,
            edge_count=12093,
            is_primary=True,
            version="2.0.0"
        )

    def _init_patent_rules_system(self) -> Any:
        """初始化专利规则向量库+知识图谱系统"""
        # Qdrant集合
        self.qdrant_collections["patent_rules_complete"] = QdrantCollectionConfig(
            key="patent_rules_complete",
            name="patent_rules_complete",
            display_name="专利规则库",
            description="完整的专利规则向量库，包含专利法、实施细则、审查指南、司法解释等（2,721条）",
            category="patent",
            dimension=1024,
            distance="Cosine",
            vector_model="BGE-large-zh-v1.5",
            linked_graph_space="patent_rules",
            is_primary=True,
            vector_count=2721,
            version="2.0.0"
        )

        # NebulaGraph空间
        self.nebula_spaces["patent_rules"] = NebulaSpaceConfig(
            key="patent_rules",
            name="patent_rules",
            display_name="专利规则知识图谱",
            description="专利规则知识图谱，包含专利概念、审查指南章节、法律引用等（53节点，83关系）",
            category="patent",
            linked_vector_collection="patent_rules_complete",
            partition_num=10,
            replica_factor=1,
            tags={
                "PatentConcept": ["name", "doc_count"],
                "GuidelineSection": ["name"],
                "LawCitation": ["law_name", "article", "full_ref"],
                "PatentDocument": ["doc_id", "title"],
                "DecisionDocument": ["doc_id", "decision_number", "decision_date", "decision_type"],
                "DecisionBlock": ["section", "block_type", "char_count"]
            },
            edges={
                "DISCUSSES_CONCEPT": [],
                "BELONGS_TO_SECTION": [],
                "CITES_LAW": [],
                "HAS_BLOCK": [],
                "REFERS_TO_DECISION": []
            },
            vertex_count=53,
            edge_count=83,
            is_primary=True,
            version="2.0.0"
        )

    def _init_patent_decisions_system(self) -> Any:
        """初始化专利决定书向量库+知识图谱系统"""
        # Qdrant集合
        self.qdrant_collections["patent_decisions"] = QdrantCollectionConfig(
            key="patent_decisions",
            name="patent_decisions",
            display_name="专利决定书库",
            description="专利无效宣告和专利复审决定书向量库（308,888条）",
            category="decision",
            dimension=1024,
            distance="Cosine",
            vector_model="BGE-large-zh-v1.5",
            linked_graph_space="patent_rules",  # 共用patent_rules空间
            is_primary=True,
            vector_count=308888,
            version="2.0.0"
        )

        # 决定书节点和关系已添加到patent_rules空间中
        # DecisionDocument: 6,500个
        # DecisionBlock: 15,230个
        # LawCitation: 358个
        # HAS_BLOCK: 4,855条
        # CITES_LAW: 5,130条


# ==================== 配置工厂 ====================

class StorageConfigFactory:
    """存储配置工厂"""

    @staticmethod
    def get_production_config() -> ProductionStorageConfig:
        """获取生产环境配置"""
        return ProductionStorageConfig(
            environment=Environment.PRODUCTION,
            qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333"),
            qdrant_api_key=os.getenv("QDRANT_API_KEY"),
            nebula_connection=NebulaConnectionConfig(
                hosts=os.getenv("NEBULA_HOSTS", "127.0.0.1").split(","),
                port=int(os.getenv("NEBULA_PORT", "9669")),
                username=os.getenv("NEBULA_USER", "root"),
                password=get_env_password("NEBULA_PASSWORD"),
                max_connections=int(os.getenv("NEBULA_MAX_CONNECTIONS", "20")),
                timeout=int(os.getenv("NEBULA_TIMEOUT", "120000"))
            )
        )

    @staticmethod
    def get_development_config() -> ProductionStorageConfig:
        """获取开发环境配置"""
        return ProductionStorageConfig(
            environment=Environment.DEVELOPMENT,
            qdrant_url="http://localhost:6333",
            nebula_connection=NebulaConnectionConfig(
                hosts=["127.0.0.1"],
                port=9669,
                username="root",
                password=get_env_password("NEBULA_PASSWORD"),
                max_connections=5,
                timeout=30000
            )
        )

    @staticmethod
    def get_config_from_env() -> ProductionStorageConfig:
        """从环境变量获取配置"""
        env = os.getenv("ENVIRONMENT", "development").lower()

        if env == "production":
            return StorageConfigFactory.get_production_config()
        else:
            return StorageConfigFactory.get_development_config()


# ==================== 工具函数 ====================

def get_collection_by_category(config: ProductionStorageConfig, category: str) -> list[QdrantCollectionConfig]:
    """按分类获取向量库集合"""
    return [
        coll for coll in config.qdrant_collections.values()
        if coll.category == category and coll.is_active
    ]


def get_space_by_category(config: ProductionStorageConfig, category: str) -> list[NebulaSpaceConfig]:
    """按分类获取知识图谱空间"""
    return [
        space for space in config.nebula_spaces.values()
        if space.category == category and space.is_active
    ]


def get_primary_collection(config: ProductionStorageConfig, category: str) -> QdrantCollectionConfig | None:
    """获取主要向量库集合"""
    for coll in config.qdrant_collections.values():
        if coll.category == category and coll.is_primary:
            return coll
    return None


def get_primary_space(config: ProductionStorageConfig, category: str) -> NebulaSpaceConfig | None:
    """获取主要知识图谱空间"""
    for space in config.nebula_spaces.values():
        if space.category == category and space.is_primary:
            return space
    return None


def validate_config(config: ProductionStorageConfig) -> list[str]:
    """验证配置完整性"""
    errors = []

    # 检查Qdrant连接
    if not config.qdrant_url:
        errors.append("Qdrant URL未配置")

    # 检查NebulaGraph连接
    if not config.nebula_connection.hosts:
        errors.append("NebulaGraph主机未配置")
    if config.nebula_connection.port <= 0:
        errors.append("NebulaGraph端口无效")

    # 检查向量库和图谱的链接
    for _coll_key, collection in config.qdrant_collections.items():
        if collection.linked_graph_space:
            if collection.linked_graph_space not in config.nebula_spaces:
                errors.append(f"集合 {collection.name} 链接的图谱空间 {collection.linked_graph_space} 不存在")

    # 检查图谱到向量库的链接
    for _space_key, space in config.nebula_spaces.items():
        if space.linked_vector_collection:
            if space.linked_vector_collection not in config.qdrant_collections:
                errors.append(f"空间 {space.name} 链接的向量库 {space.linked_vector_collection} 不存在")

    return errors


def print_config_summary(config: ProductionStorageConfig) -> Any:
    """打印配置摘要"""
    print("=" * 80)
    print(f"🔧 Athena存储配置摘要 [{config.environment.value.upper()}]")
    print("=" * 80)

    # Qdrant配置
    print("\n📊 Qdrant向量数据库:")
    print(f"   URL: {config.qdrant_url}")
    print(f"   集合数量: {len(config.qdrant_collections)}")

    for category in ["legal", "patent", "decision"]:
        collections = get_collection_by_category(config, category)
        if collections:
            print(f"\n   {category.upper()}向量库:")
            for coll in collections:
                total_vectors = coll.vector_count
                graph_link = f"→ {coll.linked_graph_space}" if coll.linked_graph_space else "无链接"
                print(f"      • {coll.display_name}: {total_vectors:,}条向量 {graph_link}")

    # NebulaGraph配置
    print("\n🕸️  NebulaGraph知识图谱:")
    print(f"   连接: {config.nebula_connection.hosts[0]}:{config.nebula_connection.port}")
    print(f"   空间数量: {len(config.nebula_spaces)}")

    for category in ["legal", "patent", "decision"]:
        spaces = get_space_by_category(config, category)
        if spaces:
            print(f"\n   {category.upper()}知识图谱:")
            for space in spaces:
                total_vertices = space.vertex_count
                total_edges = space.edge_count
                vector_link = f"← {space.linked_vector_collection}" if space.linked_vector_collection else "无链接"
                print(f"      • {space.display_name}: {total_vertices:,}节点, {total_edges:,}边 {vector_link}")

    # 验证配置
    print("\n🔍 配置验证:")
    errors = validate_config(config)
    if errors:
        print("   ❌ 发现问题:")
        for error in errors:
            print(f"      • {error}")
    else:
        print("   ✅ 配置验证通过")

    print("\n" + "=" * 80)


def export_config_json(config: ProductionStorageConfig, filepath: str) -> Any:
    """导出配置为JSON文件"""
    import json

    config_dict = {
        "environment": config.environment.value,
        "qdrant": {
            "url": config.qdrant_url,
            "collections": {
                key: {
                    "name": coll.name,
                    "display_name": coll.display_name,
                    "description": coll.description,
                    "category": coll.category,
                    "dimension": coll.dimension,
                    "vector_count": coll.vector_count,
                    "linked_graph_space": coll.linked_graph_space
                }
                for key, coll in config.qdrant_collections.items()
            }
        },
        "nebula_graph": {
            "connection": config.nebula_connection.to_dict(),
            "spaces": {
                key: {
                    "name": space.name,
                    "display_name": space.display_name,
                    "description": space.description,
                    "category": space.category,
                    "partition_num": space.partition_num,
                    "replica_factor": space.replica_factor,
                    "vertex_count": space.vertex_count,
                    "edge_count": space.edge_count,
                    "linked_vector_collection": space.linked_vector_collection,
                    "tags": space.tags,
                    "edges": space.edges
                }
                for key, space in config.nebula_spaces.items()
            }
        }
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(config_dict, f, ensure_ascii=False, indent=2)

    print(f"✅ 配置已导出到: {filepath}")


# ==================== 主程序 ====================

if __name__ == "__main__":
    # 获取配置
    config = StorageConfigFactory.get_config_from_env()

    # 打印摘要
    print_config_summary(config)

    # 导出配置
    export_config_json(
        config,
        "/Users/xujian/Athena工作平台/config/production_storage_config.json"
    )

    print("\n📝 使用示例:")
    print("""
    from config.production_storage_config import StorageConfigFactory

    # 获取生产环境配置
    config = StorageConfigFactory.get_production_config()

    # 访问法律向量库
    legal_collection = config.qdrant_collections["laws_articles"]
    print(f"法律向量库: {legal_collection.vector_count}条")

    # 访问法律知识图谱
    legal_space = config.nebula_spaces["legal_kg"]
    print(f"法律知识图谱: {legal_space.vertex_count}节点")

    # 获取专利规则主要配置
    patent_coll = get_primary_collection(config, "patent")
    patent_space = get_primary_space(config, "patent")
    """)
