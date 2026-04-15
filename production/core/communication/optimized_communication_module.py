#!/usr/bin/env python3
"""
优化版通信模块 - 向后兼容重定向
Optimized Communication Module - Backward Compatibility Redirect

⚠️ DEPRECATED: 此文件已重构为模块化目录 core.communication.optimized_communication_module/
原文件已备份为 optimized_communication_module.py.bak

请使用新导入:
    from core.communication.optimized_communication_module import OptimizedCommunicationModule

此文件仅用于向后兼容,将在未来版本中移除。
"""

from __future__ import annotations
import warnings

from .optimized_communication_module import (
    LZ4_AVAILABLE,
    ZSTD_AVAILABLE,
    BatchMessage,
    BatchProcessor,
    CommunicationStats,
    CompressionResult,
    CompressionType,
    DeliveryMode,
    Message,
    MessageCompressor,
    MessagePriority,
    MessageRouter,
    OptimizedCommunicationModule,
)

# 触发弃用警告
warnings.warn(
    "optimized_communication_module.py 已重构为模块化目录 core.communication.optimized_communication_module/。\n"
    "请使用新导入: from core.communication.optimized_communication_module import OptimizedCommunicationModule\n"
    "原文件已备份为 optimized_communication_module.py.bak",
    DeprecationWarning,
    stacklevel=2,
)

# 导出所有公共接口以保持向后兼容
__all__ = [
    "CompressionType",
    "MessagePriority",
    "DeliveryMode",
    "Message",
    "BatchMessage",
    "CompressionResult",
    "CommunicationStats",
    "MessageCompressor",
    "BatchProcessor",
    "MessageRouter",
    "OptimizedCommunicationModule",
    "LZ4_AVAILABLE",
    "ZSTD_AVAILABLE",
]
