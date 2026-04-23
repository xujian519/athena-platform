#!/usr/bin/env python3
from __future__ import annotations
"""
优化版通信模块 - 消息压缩器
Optimized Communication Module - Message Compressor

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0
"""

import base64
import gzip
import logging
import lzma
import pickle
import time
from typing import Any

# 尝试导入高级压缩库
try:
    import lz4.frame

    LZ4_AVAILABLE = True
except ImportError:
    LZ4_AVAILABLE = False

try:
    import zstd

    ZSTD_AVAILABLE = True
except ImportError:
    ZSTD_AVAILABLE = False

from .types import CompressionResult, CompressionType, Message, MessagePriority

logger = logging.getLogger(__name__)


class MessageCompressor:
    """消息压缩器

    支持多种压缩算法和自适应压缩策略。
    """

    def __init__(self, config: dict[str, Any]):
        """初始化消息压缩器

        Args:
            config: 配置字典
        """
        self.config = config
        self.default_compression = config.get("default_compression", CompressionType.AUTO)
        self.compression_threshold = config.get("compression_threshold", 1024)
        self.adaptive_compression = config.get("adaptive_compression", True)

        # 压缩性能基准
        self.compression_benchmarks: dict[str, dict[str, float]] = {}
        self._benchmark_compression_algorithms()

    def _benchmark_compression_algorithms(self):
        """基准测试压缩算法性能"""
        test_data = b"x" * 10000  # 10KB测试数据
        algorithms = [CompressionType.GZIP, CompressionType.LZMA]

        if LZ4_AVAILABLE:
            algorithms.append(CompressionType.LZ4)
        if ZSTD_AVAILABLE:
            algorithms.append(CompressionType.ZSTD)

        for algorithm in algorithms:
            try:
                start_time = time.time()
                compressed_data = self._compress_data(test_data, algorithm)
                compression_time = time.time() - start_time

                self.compression_benchmarks[algorithm.value] = {
                    "compression_ratio": len(compressed_data) / len(test_data),
                    "compression_time": compression_time,
                    "speed": len(test_data) / compression_time / 1024 / 1024,  # MB/s
                }

                logger.debug(
                    f"{algorithm.value} 压缩基准: {self.compression_benchmarks[algorithm.value]}"
                )

            except Exception as e:
                logger.warning(f"压缩算法 {algorithm.value} 基准测试失败: {e}")

    def compress_message(
        self, message: Message
    ) -> Optional[tuple[Message, CompressionResult]]:
        """压缩消息

        Args:
            message: 消息对象

        Returns:
            (压缩后的消息, 压缩结果)
        """
        try:
            # 序列化消息payload
            if isinstance(message.payload, (str, bytes)):
                original_data = (
                    message.payload.encode()
                    if isinstance(message.payload, str)
                    else message.payload
                )
            else:
                original_data = pickle.dumps(message.payload)

            original_size = len(original_data)

            # 小消息不压缩
            if original_size < self.compression_threshold:
                return message, None

            # 选择压缩算法
            compression_type = self._select_compression_algorithm(message, original_size)
            if compression_type == CompressionType.NONE:
                return message, None

            # 执行压缩
            start_time = time.time()
            compressed_data = self._compress_data(original_data, compression_type)
            compression_time = time.time() - start_time

            # 创建压缩结果
            compression_ratio = len(compressed_data) / original_size
            compression_result = CompressionResult(
                original_size=original_size,
                compressed_size=len(compressed_data),
                compression_ratio=compression_ratio,
                compression_time=compression_time,
                algorithm=compression_type.value,
            )

            # 更新消息
            message.payload = base64.b64encode(compressed_data).decode("utf-8")
            message.compression = compression_type
            message.metadata["compressed"] = True
            message.metadata["original_size"] = original_size
            message.metadata["compressed_size"] = len(compressed_data)

            return message, compression_result

        except Exception as e:
            logger.error(f"消息压缩失败: {e}")
            return message, None

    def decompress_message(self, message: Message) -> Message:
        """解压缩消息

        Args:
            message: 消息对象

        Returns:
            解压缩后的消息
        """
        try:
            if not message.metadata.get("compressed", False):
                return message

            # 获取压缩数据
            compressed_data = base64.b64decode(message.payload)

            # 解压缩
            decompressed_data = self._decompress_data(
                compressed_data, message.compression
            )

            # 还原原始数据
            if message.metadata.get("original_type") == "str":
                message.payload = decompressed_data.decode("utf-8")
            else:
                try:
                    # 尝试作为字符串
                    message.payload = decompressed_data.decode("utf-8")
                except UnicodeDecodeError:
                    # 作为pickle对象
                    message.payload = pickle.loads(decompressed_data)

            # 清理压缩标记
            message.metadata.pop("compressed", None)
            message.metadata.pop("original_size", None)
            message.metadata.pop("compressed_size", None)

            return message

        except Exception as e:
            logger.error(f"消息解压缩失败: {e}")
            return message

    def _select_compression_algorithm(
        self, message: Message, data_size: int
    ) -> CompressionType:
        """选择压缩算法

        Args:
            message: 消息对象
            data_size: 数据大小

        Returns:
            压缩算法类型
        """
        if message.compression != CompressionType.AUTO:
            return message.compression

        if not self.adaptive_compression:
            return self.default_compression

        # 基于消息类型和大小自适应选择
        if message.priority == MessagePriority.CRITICAL:
            # 关键消息优先速度
            return CompressionType.LZ4 if LZ4_AVAILABLE else CompressionType.GZIP
        elif message.priority == MessagePriority.BULK:
            # 批量消息优先压缩率
            return CompressionType.LZMA
        elif data_size < 10240:  # 小于10KB
            return CompressionType.GZIP
        else:
            # 大消息选择最高效的算法
            best_algorithm = self.default_compression
            best_ratio = 1.0

            for algorithm, benchmark in self.compression_benchmarks.items():
                if benchmark["compression_ratio"] < best_ratio:
                    best_ratio = benchmark["compression_ratio"]
                    best_algorithm = CompressionType(algorithm)

            return best_algorithm

    def _compress_data(self, data: bytes, compression_type: CompressionType) -> bytes:
        """压缩数据

        Args:
            data: 原始数据
            compression_type: 压缩算法类型

        Returns:
            压缩后的数据
        """
        if compression_type == CompressionType.GZIP:
            return gzip.compress(data)
        elif compression_type == CompressionType.LZ4 and LZ4_AVAILABLE:
            return lz4.frame.compress(data)
        elif compression_type == CompressionType.LZMA:
            return lzma.compress(data)
        elif compression_type == CompressionType.ZSTD and ZSTD_AVAILABLE:
            compressor = zstd.ZstdCompressor()
            return compressor.compress(data)
        else:
            raise ValueError(f"不支持的压缩算法: {compression_type}")

    def _decompress_data(self, data: bytes, compression_type: CompressionType) -> bytes:
        """解压缩数据

        Args:
            data: 压缩数据
            compression_type: 压缩算法类型

        Returns:
            解压缩后的数据
        """
        if compression_type == CompressionType.GZIP:
            return gzip.decompress(data)
        elif compression_type == CompressionType.LZ4 and LZ4_AVAILABLE:
            return lz4.frame.decompress(data)
        elif compression_type == CompressionType.LZMA:
            return lzma.decompress(data)
        elif compression_type == CompressionType.ZSTD and ZSTD_AVAILABLE:
            decompressor = zstd.ZstdDecompressor()
            return decompressor.decompress(data)
        else:
            raise ValueError(f"不支持的压缩算法: {compression_type}")


__all__ = ["MessageCompressor", "LZ4_AVAILABLE", "ZSTD_AVAILABLE"]
