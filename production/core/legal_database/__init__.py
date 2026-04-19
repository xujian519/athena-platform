#!/usr/bin/env python3
"""
Athena 高质量法律数据库系统
Athena High-Quality Legal Database System

版本: v3.0.0
技术决策: TD-001 - 统一图数据库选择为Neo4j

基于 ChatGLM 专家建议构建的"同一源"法律数据库
- PostgreSQL: 权威的结构化信息和版本控制(质量基准)
- Qdrant: 文本块的语义检索能力
- Neo4j: 实体关系和推理路径 (TD-001: 从NebulaGraph迁移)

作者: Athena AI Team
创建: 2026-01-15
更新: 2026-01-25 (TD-001: 迁移到Neo4j)
"""

# Neo4j核心导出 (TD-001)
# 其他模块导出
from __future__ import annotations
from core.legal_database.importer import LegalDatabaseImporter
from core.legal_database.models import (
    ArticleClause,
    ChangeType,
    LegalHierarchy,
    LegalNorm,
    LegalStatus,
    NormChange,
    VectorizedClause,
)
from core.legal_database.neo4j_graph_builder import (
    Neo4jLegalKnowledgeGraphBuilder,
    build_legal_knowledge_graph,
)
from core.legal_database.neo4j_schema import (
    EntityType,
    Neo4jQueryBuilder,
    Neo4jSchema,
    RelationType,
)
from core.legal_database.parser import LegalTextParser, ParsedArticle, ParsedNorm

# 兼容层: 旧名称映射
LegalKnowledgeGraphBuilder = Neo4jLegalKnowledgeGraphBuilder  # 向后兼容
NebulaSchema = Neo4jSchema  # 向后兼容
NebulaQueryBuilder = Neo4jQueryBuilder  # 向后兼容

__version__ = "3.0.0 (TD-001: Neo4j)"

__all__ = [
    # Neo4j核心 (新)
    "Neo4jLegalKnowledgeGraphBuilder",
    "Neo4jSchema",
    "Neo4jQueryBuilder",
    "EntityType",
    "RelationType",
    "build_legal_knowledge_graph",
    # 其他模块
    "LegalDatabaseImporter",
    "LegalTextParser",
    "ParsedNorm",
    "ParsedArticle",
    "ArticleClause",
    "LegalNorm",
    "NormChange",
    "LegalStatus",
    "ChangeType",
    "LegalHierarchy",
    "VectorizedClause",
    # 兼容层
    "LegalKnowledgeGraphBuilder",
    "NebulaSchema",
    "NebulaQueryBuilder",
]
