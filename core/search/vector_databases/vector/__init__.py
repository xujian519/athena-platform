#!/usr/bin/env python3

"""
Athena平台向量管理模块
Vector Management Module for Athena Platform

本模块提供统一的向量存储、检索和语义路由功能

主要组件:
- UnifiedVectorManager: 统一向量管理器(推荐使用)
- IntelligentVectorManager: 兼容性别名
- SemanticRouter: 兼容性别名
- QdrantVectorAdapter: 兼容性别名
"""

# 导入统一向量管理器
from .unified_vector_manager import (
    UnifiedVectorManager,
    VectorDomain,
    get_vector_manager,
)

# 向后兼容的别名
IntelligentVectorManager = UnifiedVectorManager
SemanticRouter = UnifiedVectorManager
QdrantVectorAdapter = UnifiedVectorManager

__all__ = [
    # 向后兼容别名
    "IntelligentVectorManager",
    "QdrantVectorAdapter",
    "SemanticRouter",
    # 主要导出
    "UnifiedVectorManager",
    "VectorDomain",
    "get_vector_manager",
]

