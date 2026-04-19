#!/usr/bin/env python3
from __future__ import annotations
"""
宝宸知识库同步模块
Bao Chen Knowledge Base Sync Module for Athena Platform

将宝宸知识库 Wiki/ 目录下的专利法律知识同步到 Athena 的 Qdrant 向量库中。

核心组件:
- chunk_processor: Markdown 分块 + wiki-link 提取
- qdrant_writer: Qdrant 批量写入
- sync_manager: 同步编排（全量/增量）
- baochen_retriever: 带分类过滤的检索器
"""

from .chunk_processor import ChunkProcessor, BaoChenChunk
from .qdrant_writer import QdrantWriter
from .sync_manager import BaoChenSyncManager
from .baochen_retriever import BaoChenKnowledgeRetriever

__all__ = [
    "BaoChenChunk",
    "BaoChenKnowledgeRetriever",
    "BaoChenSyncManager",
    "ChunkProcessor",
    "QdrantWriter",
]
