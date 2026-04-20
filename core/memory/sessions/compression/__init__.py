#!/usr/bin/env python3
"""
上下文压缩系统

提供智能的对话历史压缩功能，用于管理长对话的上下文。

作者: Athena平台团队
创建时间: 2026-04-21
"""
from .types import (
    CompressionLevel,
    MessageImportance,
    CompressionStrategy,
    ImportanceScore,
    CompressionResult,
    TokenBudget,
    CompressionConfig,
    MessageMetadata,
)
from .scorer import MessageScorer
from .compressor import ContextCompressor

__all__ = [
    # 类型
    "CompressionLevel",
    "MessageImportance",
    "CompressionStrategy",
    "ImportanceScore",
    "CompressionResult",
    "TokenBudget",
    "CompressionConfig",
    "MessageMetadata",
    # 核心类
    "MessageScorer",
    "ContextCompressor",
]
