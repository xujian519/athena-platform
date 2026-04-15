"""
安全序列化工具模块

提供安全的序列化和反序列化方法,替代不安全的pickle。
支持: JSON, MessagePack, Joblib等安全格式。

作者: 徐健
日期: 2025-12-29
"""

from __future__ import annotations
import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any

try:
    import msgpack

    MSGPACK_AVAILABLE = True
except ImportError:
    MSGPACK_AVAILABLE = False
    logging.warning("msgpack未安装,将使用JSON作为序列化格式")

try:
    import joblib

    JOBLIB_AVAILABLE = True
except ImportError:
    JOBLIB_AVAILABLE = False
    logging.warning("joblib未安装,模型序列化将使用JSON(部分功能受限)")

logger = logging.getLogger(__name__)


class SerializationError(Exception):
    """序列化错误"""

    pass


class DeserializationError(Exception):
    """反序列化错误"""

    pass


class SecureSerializer:
    """
    安全序列化器

    提供多种安全的序列化格式,替代不安全的pickle。
    """

    def __init__(self, format: str = "json"):
        """
        初始化序列化器

        Args:
            format: 序列化格式 ('json', 'msgpack', 'joblib')
        """
        self.format = format.lower()

        # 验证格式支持
        if self.format == "msgpack" and not MSGPACK_AVAILABLE:
            logger.warning("msgpack不可用,降级到JSON")
            self.format = "json"
        elif self.format == "joblib" and not JOBLIB_AVAILABLE:
            logger.warning("joblib不可用,降级到JSON")
            self.format = "json"

    def serialize(self, obj: Any) -> bytes:
        """
        序列化对象

        Args:
            obj: 要序列化的对象

        Returns:
            序列化后的字节数据

        Raises:
            SerializationError: 序列化失败
        """
        try:
            if self.format == "json":
                return self._serialize_json(obj)
            elif self.format == "msgpack":
                return self._serialize_msgpack(obj)
            elif self.format == "joblib":
                return self._serialize_joblib(obj)
            else:
                raise SerializationError(f"不支持的序列化格式: {self.format}")
        except Exception as e:
            logger.error(f"序列化失败: {e}")
            raise SerializationError(f"序列化失败: {e}") from e

    def deserialize(self, data: bytes) -> Any:
        """
        反序列化数据

        Args:
            data: 要反序列化的字节数据

        Returns:
            反序列化后的对象

        Raises:
            DeserializationError: 反序列化失败
        """
        try:
            if self.format == "json":
                return self._deserialize_json(data)
            elif self.format == "msgpack":
                return self._deserialize_msgpack(data)
            elif self.format == "joblib":
                return self._deserialize_joblib(data)
            else:
                raise DeserializationError(f"不支持的序列化格式: {self.format}")
        except Exception as e:
            logger.error(f"反序列化失败: {e}")
            raise DeserializationError(f"反序列化失败: {e}") from e

    def _serialize_json(self, obj: Any) -> bytes:
        """使用JSON序列化"""
        # 使用自定义编码器处理特殊类型
        json_str = json.dumps(obj, default=self._json_default, ensure_ascii=False)
        return json_str.encode("utf-8")

    def _deserialize_json(self, data: bytes) -> Any:
        """使用JSON反序列化"""
        json_str = data.decode("utf-8")
        return json.loads(json_str)

    def _serialize_msgpack(self, obj: Any) -> bytes:
        """使用MessagePack序列化"""
        if not MSGPACK_AVAILABLE:
            raise SerializationError("msgpack未安装")
        return msgpack.packb(obj, use_bin_type=True, default=self._msgpack_default)

    def _deserialize_msgpack(self, data: bytes) -> Any:
        """使用MessagePack反序列化"""
        if not MSGPACK_AVAILABLE:
            raise DeserializationError("msgpack未安装")
        return msgpack.unpackb(data, raw=False)

    def _serialize_joblib(self, obj: Any) -> bytes:
        """使用joblib序列化"""
        if not JOBLIB_AVAILABLE:
            raise SerializationError("joblib未安装")
        import io

        buffer = io.BytesIO()
        joblib.dump(obj, buffer)
        return buffer.getvalue()

    def _deserialize_joblib(self, data: bytes) -> Any:
        """使用joblib反序列化"""
        if not JOBLIB_AVAILABLE:
            raise DeserializationError("joblib未安装")
        import io

        buffer = io.BytesIO(data)
        return joblib.load(buffer)

    @staticmethod
    def _json_default(obj: Any) -> Any:
        """JSON序列化默认处理器"""
        if isinstance(obj, datetime):
            return {"__datetime__": obj.isoformat()}
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, set):
            return list(obj)
        elif hasattr(obj, "__dict__"):
            return obj.__dict__
        else:
            raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

    @staticmethod
    def _msgpack_default(obj: Any) -> Any:
        """MessagePack序列化默认处理器"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, set):
            return list(obj)
        else:
            raise TypeError(f"Object of type {type(obj).__name__} is not MessagePack serializable")


class SecureJSONSerializer(SecureSerializer):
    """JSON序列化器 (默认,兼容性最好)"""

    def __init__(self):
        super().__init__(format="json")


class SecureMsgpackSerializer(SecureSerializer):
    """MessagePack序列化器 (二进制,高性能)"""

    def __init__(self):
        super().__init__(format="msgpack")


class SecureJoblibSerializer(SecureSerializer):
    """Joblib序列化器 (适合numpy/机器学习模型)"""

    def __init__(self):
        super().__init__(format="joblib")


# 便捷函数
def dumps(obj: Any, format: str = "json") -> bytes:
    """
    序列化对象 (便捷函数)

    Args:
        obj: 要序列化的对象
        format: 序列化格式 ('json', 'msgpack', 'joblib')

    Returns:
        序列化后的字节数据
    """
    serializer = SecureSerializer(format=format)
    return serializer.serialize(obj)


def loads(data: bytes, format: str = "json") -> Any:
    """
    反序列化数据 (便捷函数)

    Args:
        data: 要反序列化的字节数据
        format: 序列化格式 ('json', 'msgpack', 'joblib')

    Returns:
        反序列化后的对象
    """
    serializer = SecureSerializer(format=format)
    return serializer.deserialize(data)


# 模型序列化专用函数 (使用joblib)
def dump_model(model: Any, filepath: str) -> None:
    """
    保存模型到文件 (使用joblib)

    Args:
        model: 模型对象
        filepath: 文件路径
    """
    if not JOBLIB_AVAILABLE:
        raise ImportError("joblib未安装,请运行: pip install joblib")

    try:
        joblib.dump(model, filepath)
        logger.info(f"模型已保存到: {filepath}")
    except Exception as e:
        logger.error(f"模型保存失败: {e}")
        raise


def load_model(filepath: str) -> Any:
    """
    从文件加载模型 (使用joblib)

    Args:
        filepath: 文件路径

    Returns:
        加载的模型对象
    """
    if not JOBLIB_AVAILABLE:
        raise ImportError("joblib未安装,请运行: pip install joblib")

    try:
        model = joblib.load(filepath)
        logger.info(f"模型已从 {filepath} 加载")
        return model
    except Exception as e:
        logger.error(f"模型加载失败: {e}")
        raise


# 缓存序列化专用函数
def serialize_for_cache(obj: Any) -> bytes:
    """
    序列化对象用于缓存 (推荐使用msgpack或json)

    Args:
        obj: 要序列化的对象

    Returns:
        序列化后的字节数据
    """
    # 优先使用msgpack (更高效),降级到json
    format = "msgpack" if MSGPACK_AVAILABLE else "json"
    return dumps(obj, format=format)


def deserialize_from_cache(data: bytes) -> Any:
    """
    从缓存反序列化数据

    Args:
        data: 缓存的字节数据

    Returns:
        反序列化后的对象
    """
    # 尝试msgpack,失败则尝试json
    try:
        if MSGPACK_AVAILABLE:
            return loads(data, format="msgpack")
        else:
            return loads(data, format="json")
    except Exception:
        return loads(data, format="json")


__all__ = [
    "DeserializationError",
    "SecureJSONSerializer",
    "SecureJoblibSerializer",
    "SecureMsgpackSerializer",
    "SecureSerializer",
    "SerializationError",
    "deserialize_from_cache",
    "dump_model",
    "dumps",
    "load_model",
    "loads",
    "serialize_for_cache",
]
