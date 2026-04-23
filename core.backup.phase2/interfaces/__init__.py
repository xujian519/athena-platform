"""
核心接口定义层 - 依赖倒置核心

此模块定义了所有核心接口，用于消除core对services/domains的反向依赖。

遵循依赖倒置原则（Dependency Inversion Principle）：
- 高层模块（core）不应依赖低层模块（services/domains）
- 两者都应依赖抽象（接口）
- 接口由core定义，实现由services/domains提供
"""

from .vector_store import VectorStoreProvider, VectorSearchResult
from .knowledge_base import KnowledgeBaseService, KnowledgeQueryResult
from .patent_service import PatentRetrievalService, PatentDetail, PatentSearchResult

__all__ = [
    "VectorStoreProvider",
    "VectorSearchResult",
    "KnowledgeBaseService",
    "KnowledgeQueryResult",
    "PatentRetrievalService",
    "PatentDetail",
    "PatentSearchResult",
]
