#!/usr/bin/env python3
"""
法律数据库系统 (BGE-M3 + Reranker)
Legal Database System with BGE-M3 and Reranker

统一使用平台优化的BGE-M3向量化模型和BGE-Reranker重排序模型

作者: Athena AI系统
创建时间: 2025-01-15
版本: 1.0.0

主要功能:
- BGE-M3向量化 (MPS加速)
- BGE-Reranker重排序
- 法律数据搜索
"""

from __future__ import annotations
__version__ = "1.0.0"
__author__ = "Athena AI系统"

from .legal_search_engine import LegalSearchEngine
from .vectorize_legal_data import LegalVectorizePipeline

__all__ = [
    "LegalSearchEngine",
    "LegalVectorizePipeline"
]
