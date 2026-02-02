"""
消息序列化器
提供高性能的消息序列化和压缩功能
"""
import pandas as pd

import gzip
import json
import logging
from core.logging_config import setup_logging
import lzma
import pickle
import time
import zlib
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import msgpack
import numpy as np
import orjson

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

class SerializationFormat(Enum):
    """序列化格式"""
    JSON = 'json'
    PICKLE = 'pickle'
    MSGPACK = 'msgpack'
    ORJSON = 'orjson'

class CompressionType(Enum):
    """压缩类型"""
    NONE = 'none'
    GZIP = 'gzip'
    ZLIB = 'zlib'
    LZMA = 'lzma'

@dataclass
class SerializationConfig:
    """序列化配置"""
    format: SerializationFormat = SerializationFormat.ORJSON
    compression: CompressionType = CompressionType.GZIP
    compression_threshold: int = 1024  # 大于1KB的消息才压缩
    enable_compression: bool = True
    enable_validation: bool = True
    max_message_size: int = 10 * 1024 * 1024  # 10MB

class MessageSerializer:
    """消息序列化器"""

    def __init__(self, config: SerializationConfig | None = None):
        self.config = config or SerializationConfig()
        self.stats = {
            'serializations': 0,
            'deserializations': 0,
            'compression_count': 0,
            'total_size_original': 0,
            'total_size_compressed': 0,
            'avg_serialization_time': 0.0,
            'avg_deserialization_time': 0.0
        }

    def serialize(self, data: Any) -> bytes:
        """序列化数据"""
        start_time = time.time()

        try:
            # 1. 基础序列化
            if self.config.format == SerializationFormat.JSON:
                serialized = json.dumps(data, ensure_ascii=False).encode('utf-8')
            elif self.config.format == SerializationFormat.PICKLE:
                serialized = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
            elif self.config.format == SerializationFormat.MSGPACK:
                serialized = msgpack.packb(data, use_bin_type=True)
            elif self.config.format == SerializationFormat.ORJSON:
                serialized = orjson.dumps(data)
            else:
                raise ValueError(f"不支持的序列化格式: {self.config.format}")

            # 2. 验证大小
            if len(serialized) > self.config.max_message_size:
                raise ValueError(f"消息大小超过限制: {len(serialized)} > {self.config.max_message_size}")

            # 3. 压缩
            if (self.config.enable_compression and
                len(serialized) > self.config.compression_threshold):
                compressed = self._compress(serialized)
                if len(compressed) < len(serialized) * 0.9:  # 压缩后大小至少减少10%
                    serialized = compressed
                    self.stats['compression_count'] += 1

            # 4. 添加元数据
            final_data = self._add_metadata(serialized)

            # 5. 更新统计
            serialization_time = time.time() - start_time
            self._update_stats('serialize', len(data) if hasattr(data, '__len__') else 0,
                             len(serialized), serialization_time)

            return final_data

        except Exception as e:
            logger.error(f"序列化失败: {e}")
            raise

    def deserialize(self, data: bytes) -> Any:
        """反序列化数据"""
        start_time = time.time()

        try:
            # 1. 解析元数据
            serialized_data, metadata = self._parse_metadata(data)

            # 2. 解压缩
            if metadata.get('compressed', False):
                serialized_data = self._decompress(serialized_data, metadata['compression_type'])

            # 3. 基础反序列化
            if metadata['format'] == SerializationFormat.JSON.value:
                result = json.loads(serialized_data.decode('utf-8'))
            elif metadata['format'] == SerializationFormat.PICKLE.value:
                result = pickle.loads(serialized_data)
            elif metadata['format'] == SerializationFormat.MSGPACK.value:
                result = msgpack.unpackb(serialized_data, raw=False)
            elif metadata['format'] == SerializationFormat.ORJSON.value:
                result = orjson.loads(serialized_data)
            else:
                raise ValueError(f"不支持的序列化格式: {metadata['format']}")

            # 4. 更新统计
            deserialization_time = time.time() - start_time
            self._update_stats('deserialize', len(serialized_data),
                             len(data), deserialization_time)

            return result

        except Exception as e:
            logger.error(f"反序列化失败: {e}")
            raise

    def _compress(self, data: bytes) -> bytes:
        """压缩数据"""
        if self.config.compression == CompressionType.GZIP:
            return gzip.compress(data, compresslevel=6)
        elif self.config.compression == CompressionType.ZLIB:
            return zlib.compress(data, level=6)
        elif self.config.compression == CompressionType.LZMA:
            return lzma.compress(data, preset=6)
        else:
            return data

    def _decompress(self, data: bytes, compression_type: str) -> bytes:
        """解压缩数据"""
        if compression_type == CompressionType.GZIP.value:
            return gzip.decompress(data)
        elif compression_type == CompressionType.ZLIB.value:
            return zlib.decompress(data)
        elif compression_type == CompressionType.LZMA.value:
            return lzma.decompress(data)
        else:
            return data

    def _add_metadata(self, data: bytes) -> bytes:
        """添加元数据"""
        metadata = {
            'format': self.config.format.value,
            'compressed': self.config.compression != CompressionType.NONE,
            'compression_type': self.config.compression.value,
            'timestamp': datetime.now().isoformat(),
            'version': '1.0'
        }

        # 将元数据添加到数据前部
        metadata_bytes = json.dumps(metadata).encode('utf-8')
        metadata_length = len(metadata_bytes).to_bytes(4, byteorder='big')

        return metadata_length + metadata_bytes + data

    def _parse_metadata(self, data: bytes) -> tuple[bytes, dict[str, Any]:
        """解析元数据"""
        # 读取元数据长度
        metadata_length = int.from_bytes(data[:4], byteorder='big')

        # 读取元数据
        metadata_bytes = data[4:4+metadata_length]
        metadata = json.loads(metadata_bytes.decode('utf-8'))

        # 返回实际数据和元数据
        actual_data = data[4+metadata_length:]
        return actual_data, metadata

    def _update_stats(self, operation: str, original_size: int, final_size: int, duration: float) -> Any:
        """更新统计信息"""
        if operation == 'serialize':
            self.stats['serializations'] += 1
            self.stats['total_size_original'] += original_size
            self.stats['total_size_compressed'] += final_size
            # 更新平均序列化时间
            alpha = 0.1
            self.stats['avg_serialization_time'] = (
                alpha * duration +
                (1 - alpha) * self.stats['avg_serialization_time']
            )
        else:
            self.stats['deserializations'] += 1
            # 更新平均反序列化时间
            alpha = 0.1
            self.stats['avg_deserialization_time'] = (
                alpha * duration +
                (1 - alpha) * self.stats['avg_deserialization_time']
            )

    def get_stats(self) -> dict[str, Any]:
        """获取序列化统计信息"""
        compression_ratio = 1.0
        if self.stats['total_size_original'] > 0:
            compression_ratio = (
                self.stats['total_size_compressed'] /
                self.stats['total_size_original']
            )

        return {
            'operations': {
                'serializations': self.stats['serializations'],
                'deserializations': self.stats['deserializations'],
                'compression_count': self.stats['compression_count']
            },
            'performance': {
                'avg_serialization_time': self.stats['avg_serialization_time'],
                'avg_deserialization_time': self.stats['avg_deserialization_time'],
                'compression_ratio': compression_ratio,
                'total_size_saved': (
                    self.stats['total_size_original'] -
                    self.stats['total_size_compressed']
                )
            },
            'config': {
                'format': self.config.format.value,
                'compression': self.config.compression.value,
                'compression_threshold': self.config.compression_threshold
            }
        }

class HighPerformanceSerializer:
    """高性能序列化器(针对特定场景优化)"""

    @staticmethod
    def serialize_numpy_array(arr: np.ndarray) -> bytes:
        """序列化NumPy数组"""
        # 使用numpy的内部序列化,更高效
        return pickle.dumps(arr, protocol=pickle.HIGHEST_PROTOCOL)

    @staticmethod
    def deserialize_numpy_array(data: bytes) -> np.ndarray:
        """反序列化NumPy数组"""
        return pickle.loads(data)

    @staticmethod
    def serialize_dataframe(df) -> bytes:
        """序列化DataFrame(pandas)"""
        try:
            # 尝试使用parquet格式(更高效)
            import io

            import pyarrow.parquet as pq
            buffer = io.BytesIO()
            df.to_parquet(buffer, index=False)
            return buffer.getvalue()
        except ImportError:
            # 回退到pickle
            return pickle.dumps(df, protocol=pickle.HIGHEST_PROTOCOL)

    @staticmethod
    def deserialize_dataframe(data: bytes) -> 'pd.DataFrame':
        """反序列化DataFrame"""
        try:
            import io

            import pandas as pd
            buffer = io.BytesIO(data)
            return pd.read_parquet(buffer)
        except Exception as e:  # TODO
            return pickle.loads(data)

class MessageBatchSerializer:
    """批量消息序列化器"""

    def __init__(self, serializer: MessageSerializer):
        self.serializer = serializer
        self.batch_size = 100

    def serialize_batch(self, messages: list[Any]) -> bytes:
        """批量序列化消息"""
        batch_data = {
            'messages': messages,
            'batch_size': len(messages),
            'timestamp': datetime.now().isoformat()
        }
        return self.serializer.serialize(batch_data)

    def deserialize_batch(self, data: bytes) -> list[Any]:
        """批量反序列化消息"""
        batch_data = self.serializer.deserialize(data)
        return batch_data['messages']

# 全局序列化器实例
default_serializer = MessageSerializer()
high_perf_serializer = HighPerformanceSerializer()
batch_serializer = MessageBatchSerializer(default_serializer)

# 便捷函数
def serialize_message(data: Any) -> bytes:
    """序列化消息"""
    return default_serializer.serialize(data)

def deserialize_message(data: bytes) -> Any:
    """反序列化消息"""
    return default_serializer.deserialize(data)

def get_serialization_stats() -> dict[str, Any]:
    """获取序列化统计信息"""
    return default_serializer.get_stats()

# 性能测试函数
async def benchmark_serialization(data: Any, iterations: int = 1000) -> dict[str, float]:
    """序列化性能测试"""
    import time

    # 测试序列化
    start_time = time.time()
    for _ in range(iterations):
        serialized = serialize_message(data)
    serialization_time = time.time() - start_time

    # 测试反序列化
    start_time = time.time()
    for _ in range(iterations):
        deserialize_message(serialized)
    deserialization_time = time.time() - start_time

    return {
        'serialization_time': serialization_time / iterations,
        'deserialization_time': deserialization_time / iterations,
        'throughput_serialization': iterations / serialization_time,
        'throughput_deserialization': iterations / deserialization_time
    }