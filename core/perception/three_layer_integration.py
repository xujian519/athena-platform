#!/usr/bin/env python3
from __future__ import annotations
"""
感知模块三层架构集成配置
Perception Module Three-Layer Architecture Integration Configuration

提供感知模块与法律世界模型三层架构的集成接口
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()
load_dotenv(Path(__file__).parent / "perception_three_tier.env")


@dataclass
class ThreeLayerConfig:
    """三层架构配置"""

    # PostgreSQL配置
    pg_host: str
    pg_port: int
    pg_database: str
    pg_user: str

    # Neo4j配置
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    neo4j_database: str

    # Qdrant配置
    qdrant_url: str
    qdrant_collection: str

    # Redis配置
    redis_url: str
    redis_cache_ttl: int

    @classmethod
    def from_env(cls) -> "ThreeLayerConfig":
        """从环境变量加载配置"""
        return cls(
            pg_host=os.getenv("PERCEPTION_PG_HOST", "localhost"),
            pg_port=int(os.getenv("PERCEPTION_PG_PORT", "5432")),
            pg_database=os.getenv("PERCEPTION_PG_DATABASE", "athena"),
            pg_user=os.getenv("PERCEPTION_PG_USER", "xujian"),
            neo4j_uri=os.getenv("PERCEPTION_NEO4J_URI", "bolt://localhost:7687"),
            neo4j_user=os.getenv("PERCEPTION_NEO4J_USER", "neo4j"),
            neo4j_password=os.getenv("PERCEPTION_NEO4J_PASSWORD", "athena123"),
            neo4j_database=os.getenv("PERCEPTION_NEO4J_DATABASE", "athena"),
            qdrant_url=os.getenv("PERCEPTION_QDRANT_URL", "http://localhost:6333"),
            qdrant_collection=os.getenv("PERCEPTION_QDRANT_COLLECTION", "perception_vectors"),
            redis_url=os.getenv("PERCEPTION_REDIS_URL", "redis://localhost:6379/1"),
            redis_cache_ttl=int(os.getenv("PERCEPTION_REDIS_CACHE_TTL", "3600")),
        )

    def get_postgres_url(self) -> str:
        """获取PostgreSQL连接URL"""
        return f"postgresql://{self.pg_user}@{self.pg_host}:{self.pg_port}/{self.pg_database}"

    def get_neo4j_config(self) -> dict[str, str]:
        """获取Neo4j连接配置"""
        return {
            "uri": self.neo4j_uri,
            "user": self.neo4j_user,
            "password": self.neo4j_password,
        }


@dataclass
class LayerMapping:
    """三层架构节点类型映射"""

    # Layer 1: 法律法规层
    layer1_labels = [
        "LawDocument",  # 法律文档
        "LawArticle",  # 法律条文
        "LegalConcept",  # 法律概念
        "PerceptionConcept",  # 感知概念(扩展)
    ]

    # Layer 2: 专利专业层
    layer2_labels = [
        "PatentLawDocument",  # 专利法律文档
        "PatentGuideChapter",  # 专利审查指南章节
        "PatentReviewDecision",  # 专利复审决定
    ]

    # Layer 3: 判决文书层
    layer3_labels = [
        "JudgmentDocument",  # 判决文书
        "JudgmentCitation",  # 法律引用
        "PerceptionApplication",  # 感知应用(扩展)
    ]

    # 感知输入类型映射到三层架构
    input_mapping = {
        "patent_drawing": "PatentLawDocument",  # 专利图纸 -> Layer 2
        "claim_text": "PatentLawDocument",  # 权利要求 -> Layer 2
        "legal_text": "LawDocument",  # 法律文本 -> Layer 1
        "judgment": "JudgmentDocument",  # 判决文书 -> Layer 3
        "multimodal_patent": "PatentLawDocument",  # 多模态专利 -> Layer 2
    }

    # 感知关系类型
    perception_relations = [
        "EXTRACTS_FROM",  # 提取特征
        "ANALYZES",  # 分析内容
        "PROCESS",  # 处理数据
        "INTERPRETS",  # 解释法律
        "ENABLES",  # 使能应用
        "PERCEPTION_RELATION",  # 通用感知关系
    ]


@dataclass
class PerceptionQueries:
    """感知模块三层架构查询"""

    @staticmethod
    def query_layer1_laws(limit: int = 10) -> str:
        """查询Layer 1法律文档"""
        return f"""
        MATCH (l:LawDocument)
        RETURN l.node_id, l.title, l.document_type, l.law_id, l.importance
        ORDER BY l.importance DESC
        LIMIT {limit}
        """

    @staticmethod
    def query_layer2_patents(document_type: str | None = None, limit: int = 10) -> str:
        """查询Layer 2专利文档"""
        if document_type:
            return f"""
            MATCH (p:PatentLawDocument {{document_type: '{document_type}'}})
            RETURN p.node_id, p.title, p.document_type, p.section_id, p.full_path
            ORDER BY p.level
            LIMIT {limit}
            """
        return f"""
        MATCH (p:PatentLawDocument)
        RETURN p.node_id, p.title, p.document_type, p.section_id, p.full_path
        ORDER BY p.level
        LIMIT {limit}
        """

    @staticmethod
    def query_layer3_judgments(case_type: str | None = None, limit: int = 10) -> str:
        """查询Layer 3判决文书"""
        if case_type:
            return f"""
            MATCH (j:JudgmentDocument {{case_type: '{case_type}'}})
            RETURN j.judgment_id, j.title, j.year, j.case_type, j.plaintiff, j.defendant
            ORDER BY j.year DESC
            LIMIT {limit}
            """
        return f"""
        MATCH (j:JudgmentDocument)
        RETURN j.judgment_id, j.title, j.year, j.case_type, j.plaintiff, j.defendant
        ORDER BY j.year DESC
        LIMIT {limit}
        """

    @staticmethod
    def query_cross_layer_law_to_patent(law_id: str) -> str:
        """跨层查询:法律到专利文档"""
        return f"""
        MATCH (l:LawDocument {{law_id: '{law_id}'}})-[:LEGAL_BASIS_FOR]->(p:PatentLawDocument)
        RETURN l.title as law_title, p.title as patent_title, p.document_type
        ORDER BY p.level
        """

    @staticmethod
    def query_cross_layer_patent_to_judgment(section_id: str) -> str:
        """跨层查询:专利文档到判决"""
        return f"""
        MATCH (p:PatentLawDocument {{section_id: '{section_id}'}})
        MATCH (j:JudgmentDocument)
        WHERE p.title CONTAINS j.title OR j.title CONTAINS p.title
        RETURN p.title as patent_title, j.title as judgment_title, j.case_type
        LIMIT 10
        """

    @staticmethod
    def query_perception_concepts() -> str:
        """查询感知概念(Layer 1扩展)"""
        return """
        MATCH (c:PerceptionConcept)
        RETURN c.concept_id, c.concept_name, c.concept_type, c.definition, c.category
        ORDER BY c.category, c.concept_name
        """

    @staticmethod
    def query_perception_applications() -> str:
        """查询感知应用(Layer 3扩展)"""
        return """
        MATCH (a:PerceptionApplication)
        RETURN a.app_id, a.app_name, a.app_type, a.description, a.status
        ORDER BY a.app_type, a.app_name
        """

    @staticmethod
    def query_full_perception_chain(concept_name: str) -> str:
        """查询完整感知链:感知概念 -> 法律文档 -> 专利文档 -> 判决应用"""
        return f"""
        MATCH path = (c:PerceptionConcept {{concept_name: '{concept_name}'}})-[*0..2]-(j:JudgmentDocument)
        RETURN [node in nodes(path) | labels(node)[0] + ':' + coalesce(node.title, node.concept_name, node.app_name)] as perception_chain
        LIMIT 10
        """


class ThreeLayerIntegrator:
    """三层架构集成器"""

    def __init__(self, config: ThreeLayerConfig | None = None):
        """初始化集成器"""
        self.config = config or ThreeLayerConfig.from_env()
        self.layer_mapping = LayerMapping()
        self.queries = PerceptionQueries()

    def get_connection_info(self) -> dict[str, Any]:
        """获取连接信息"""
        return {
            "postgres": {
                "url": self.config.get_postgres_url(),
                "host": self.config.pg_host,
                "port": self.config.pg_port,
                "database": self.config.pg_database,
                "user": self.config.pg_user,
            },
            "neo4j": self.config.get_neo4j_config(),
            "qdrant": {
                "url": self.config.qdrant_url,
                "collection": self.config.qdrant_collection,
            },
            "redis": {
                "url": self.config.redis_url,
                "cache_ttl": self.config.redis_cache_ttl,
            },
        }

    def get_layer_statistics(self) -> dict[str, dict[str, int]]:
        """获取各层统计信息(从PostgreSQL查询)"""
        import psycopg2

        stats = {}

        try:
            conn = psycopg2.connect(
                host=self.config.pg_host,
                port=self.config.pg_port,
                database=self.config.pg_database,
                user=self.config.pg_user,
            )
            cursor = conn.cursor()

            # Layer 1统计
            cursor.execute("SELECT COUNT(*) FROM law_documents")
            layer1_count = cursor.fetchone()[0]

            # Layer 2统计
            cursor.execute("SELECT COUNT(*) FROM patent_law_documents")
            layer2_count = cursor.fetchone()[0]

            # Layer 3统计
            cursor.execute("SELECT COUNT(*) FROM patent_judgments")
            layer3_count = cursor.fetchone()[0]

            stats = {
                "Layer 1 (法律法规)": {
                    "total": layer1_count,
                    "node_types": ["LawDocument", "PerceptionConcept"],
                },
                "Layer 2 (专利专业)": {
                    "total": layer2_count,
                    "node_types": [
                        "PatentLawDocument",
                        "PatentGuideChapter",
                        "PatentReviewDecision",
                    ],
                },
                "Layer 3 (判决文书)": {
                    "total": layer3_count,
                    "node_types": ["JudgmentDocument", "PerceptionApplication"],
                },
            }

            cursor.close()
            conn.close()

        except Exception as e:
            print(f"获取统计信息失败: {e}")

        return stats


# 全局集成器实例
_integrator: ThreeLayerIntegrator | None = None


def get_three_layer_integrator() -> ThreeLayerIntegrator:
    """获取三层架构集成器单例"""
    global _integrator
    if _integrator is None:
        _integrator = ThreeLayerIntegrator()
    return _integrator


__all__ = [
    "LayerMapping",
    "PerceptionQueries",
    "ThreeLayerConfig",
    "ThreeLayerIntegrator",
    "get_three_layer_integrator",
]
