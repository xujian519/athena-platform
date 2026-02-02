#!/usr/bin/env python3
"""
优化版通信模块 - 公共接口
Optimized Communication Module - Public Interface

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0

提供消息压缩、批处理、智能路由等优化功能。
"""

from .batch_processor import BatchProcessor
from .compressor import MessageCompressor, LZ4_AVAILABLE, ZSTD_AVAILABLE
from .module import OptimizedCommunicationModule
from .router import MessageRouter
from .types import (
    BatchMessage,
    CommunicationStats,
    CompressionResult,
    CompressionType,
    DeliveryMode,
    Message,
    MessagePriority,
)

# 导出公共接口
__all__ = [
    # 类型
    "CompressionType",
    "MessagePriority",
    "DeliveryMode",
    "Message",
    "BatchMessage",
    "CompressionResult",
    "CommunicationStats",
    # 核心类
    "MessageCompressor",
    "BatchProcessor",
    "MessageRouter",
    "OptimizedCommunicationModule",
    # 常量
    "LZ4_AVAILABLE",
    "ZSTD_AVAILABLE",
]
