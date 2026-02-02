"""
知识图谱模块 - Knowledge Graph Module

提供知识图谱集成、检索、推理等功能
"""

from core.knowledge_graph.kg_integration import (
    # 数据类
    Entity,
    # 枚举
    EntityType,
    GraphEnhancer,
    GraphPath,
    # 核心类
    KnowledgeGraphClient,
    MockKnowledgeGraphClient,
    Relation,
    RelationType,
    expand_query,
    find_entity_relations,
    get_graph_enhancer,
    # 便捷函数
    get_kg_client,
    search_concepts,
)
from core.knowledge_graph.kg_real_client import (
    # 真实客户端
    RealKnowledgeGraphClient,
    create_knowledge_graph_client,
)

# 法律知识图谱推理增强器
try:
    from core.knowledge_graph.legal_kg_reasoning_enhancer import (
        GraphEnhancedReasoningEngine,
        GraphReasoningContext,
        LegalEntityType,
        LegalKGReasoningEnhancer,
        LegalRelationType,
    )
except ImportError:
    LegalEntityType = None
    LegalRelationType = None
    GraphReasoningContext = None
    LegalKGReasoningEnhancer = None
    GraphEnhancedReasoningEngine = None

__all__ = [
    # 数据类
    "Entity",
    # 枚举
    "EntityType",
    "GraphEnhancedReasoningEngine",
    "GraphEnhancer",
    "GraphPath",
    "GraphReasoningContext",
    # 核心类
    "KnowledgeGraphClient",
    "LegalEntityType",
    "LegalKGReasoningEnhancer",
    "LegalRelationType",
    "MockKnowledgeGraphClient",
    # 真实客户端
    "RealKnowledgeGraphClient",
    "Relation",
    "RelationType",
    "create_knowledge_graph_client",
    "expand_query",
    "find_entity_relations",
    "get_graph_enhancer",
    # 便捷函数
    "get_kg_client",
    "search_concepts",
]
