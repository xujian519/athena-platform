#!/usr/bin/env python3
from __future__ import annotations
"""
优化版通信模块 - 公共接口
Optimized Communication Module - Public Interface

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0

提供消息压缩、批处理、智能路由等优化功能。
"""

from typing import Any

from .batch_processor import BatchProcessor
from .compressor import LZ4_AVAILABLE, ZSTD_AVAILABLE, MessageCompressor
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

# =============================================================================
# === 便捷函数 ===
# =============================================================================

# 全局模块实例
_global_optimized_module: OptimizedCommunicationModule | None = None


def get_optimized_module(
    config: dict[str, Any] | None = None,
) -> OptimizedCommunicationModule:
    """
    获取或创建优化通信模块实例

    Args:
        config: 配置参数

    Returns:
        OptimizedCommunicationModule 实例
    """
    global _global_optimized_module

    if _global_optimized_module is None:
        _global_optimized_module = OptimizedCommunicationModule(config or {})

    return _global_optimized_module


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
    # 便捷函数
    "get_optimized_module",
    # 常量
    "LZ4_AVAILABLE",
    "ZSTD_AVAILABLE",
]
