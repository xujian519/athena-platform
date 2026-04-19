#!/usr/bin/env python3
from __future__ import annotations
"""
图和网络分析模块
Graph and Network Analysis Module

提供NetworkX图操作工具,支持推理引擎、知识图谱、专利分析等场景
"""

from .networkx_utils import (
    CentralityMetric,
    EdgeInfo,
    # 数据类
    GraphStats,
    # 枚举类型
    GraphType,
    # 主要类
    NetworkXGraphManager,
    NodeInfo,
    create_knowledge_graph,
    create_patent_citation_graph,
    create_reasoning_dependency_graph,
    # 便捷函数
    create_reasoning_rule_graph,
    get_networkx_version,
    is_networkx_available,
)

__all__ = [
    "CentralityMetric",
    "EdgeInfo",
    # 数据类
    "GraphStats",
    # 枚举类型
    "GraphType",
    # 主要类
    "NetworkXGraphManager",
    "NodeInfo",
    "create_knowledge_graph",
    "create_patent_citation_graph",
    "create_reasoning_dependency_graph",
    # 便捷函数
    "create_reasoning_rule_graph",
    "get_networkx_version",
    "is_networkx_available",
]

__version__ = "1.0.0"
__author__ = "Athena Platform Team"
