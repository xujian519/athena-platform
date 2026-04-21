#!/usr/bin/env python3
"""
Knowledge Graph Models
知识图谱模型模块

统一的知识图谱模型接口
"""

from .patent import (
    # 核心模型
    UnifiedPatentKnowledgeGraph,
    # 兼容层
    PatentKnowledgeGraph,
    EnhancedPatentKnowledgeGraph,
    # 枚举类型
    NodeType,
    RelationType,
    QueryType,
    # 数据类
    TechnicalTriple,
    FeatureRelation,
    DocumentAnalysis,
    KnowledgeNode,
    KnowledgeRelation,
    SearchResult,
    HybridSearchConfig,
    # 后端
    GraphBackend as PatentGraphBackend,
    PersistentGraphBackend,
    MemoryGraphBackend,
    # 便捷函数
    get_patent_kg,
)

from .unified import (
    # 核心模型
    UnifiedKnowledgeGraph,
    LegalKnowledgeGraphBuilder,
    # 枚举类型
    GraphBackend,
    # 配置
    Neo4jConfig,
    GraphStatistics,
    # 数据类
    PatentLaw,
    CasePrecedent,
    InferenceRule,
    LegalEntity,
    LegalRelation,
    # 便捷函数
    get_unified_knowledge_graph,
)

__all__ = [
    # 专利模型
    "UnifiedPatentKnowledgeGraph",
    "PatentKnowledgeGraph",
    "EnhancedPatentKnowledgeGraph",
    "NodeType",
    "RelationType",
    "QueryType",
    "TechnicalTriple",
    "FeatureRelation",
    "DocumentAnalysis",
    "KnowledgeNode",
    "KnowledgeRelation",
    "SearchResult",
    "HybridSearchConfig",
    "PatentGraphBackend",
    "PersistentGraphBackend",
    "MemoryGraphBackend",
    "get_patent_kg",
    # 统一模型
    "UnifiedKnowledgeGraph",
    "LegalKnowledgeGraphBuilder",
    "GraphBackend",
    "Neo4jConfig",
    "GraphStatistics",
    "PatentLaw",
    "CasePrecedent",
    "InferenceRule",
    "LegalEntity",
    "LegalRelation",
    "get_unified_knowledge_graph",
]
