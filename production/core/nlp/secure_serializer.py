from __future__ import annotations
"""
安全序列化工具

使用JSON或MessagePack替代不安全的pickle,防止反序列化漏洞
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Any

try:
    import msgpack

    HAS_MSGPACK = True
except ImportError:
    HAS_MSGPACK = False

logger = logging.getLogger(__name__)


class SecureSerializer:
    """安全序列化器 - 使用JSON或MessagePack替代pickle"""

    def __init__(self, use_msgpack: bool = True):
        """
        初始化安全序列化器

        Args:
            use_msgpack: 是否使用MessagePack(更快更紧凑),如果不可用则回退到JSON
        """
        self.use_msgpack = use_msgpack and HAS_MSGPACK
        if use_msgpack and not HAS_MSGPACK:
            logger.warning("msgpack不可用,使用JSON作为替代")

    def dump(self, data: Any, filepath: str) -> bool:
        """
        安全地序列化数据到文件

        Args:
            data: 要序列化的数据(必须是JSON可序列化的类型)
            filepath: 目标文件路径

        Returns:
            是否成功
        """
        try:
            filepath_obj = Path(filepath)
            filepath_obj.parent.mkdir(parents=True, exist_ok=True)

            if self.use_msgpack:
                with open(filepath, "wb") as f:
                    # 使用MessagePack进行二进制序列化
                    packed = msgpack.packb(data, use_bin_type=True)
                    f.write(packed)
            else:
                # 使用JSON作为后备
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

            logger.debug(f"✅ 数据已安全序列化到: {filepath}")
            return True

        except (TypeError, ValueError) as e:
            logger.error(f"❌ 数据序列化失败,包含不支持的类型: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ 序列化到文件失败 [{filepath}]: {e}")
            return False

    def load(self, filepath: str) -> Any | None:
        """
        安全地从文件反序列化数据

        Args:
            filepath: 源文件路径

        Returns:
            反序列化的数据,失败返回None
        """
        try:
            if not Path(filepath).exists():
                logger.warning(f"⚠️ 文件不存在: {filepath}")
                return None

            if self.use_msgpack:
                with open(filepath, "rb") as f:
                    data = msgpack.unpackb(f.read(), raw=False)
            else:
                with open(filepath, encoding="utf-8") as f:
                    data = json.load(f)

            logger.debug(f"✅ 数据已安全地从 {filepath} 反序列化")
            return data

        except msgpack.exceptions.ExtraData as e:
            logger.error(f"❌ MessagePack数据损坏: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON数据损坏: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ 从文件反序列化失败 [{filepath}]: {e}")
            return None

    def validate_and_dump(self, data: Any, filepath: str, schema: dict) -> bool:
        """
        验证数据结构并序列化

        Args:
            data: 要序列化的数据
            filepath: 目标文件路径
            schema: 数据结构schema(用于验证)

        Returns:
            是否成功
        """
        # 验证数据结构
        if not self._validate_schema(data, schema):
            logger.error("❌ 数据验证失败,不符合schema要求")
            return False

        # 添加校验和
        data_with_checksum = {
            "data": data,
            "checksum": self._compute_checksum(data),
            "version": "1.0",
        }

        return self.dump(data_with_checksum, filepath)

    def validate_and_load(self, filepath: str, schema: dict) -> Any | None:
        """
        反序列化并验证数据

        Args:
            filepath: 源文件路径
            schema: 数据结构schema(用于验证)

        Returns:
            验证后的数据,失败返回None
        """
        loaded_data = self.load(filepath)
        if loaded_data is None:
            return None

        # 检查版本和校验和
        if isinstance(loaded_data, dict) and "data" in loaded_data:
            # 验证校验和
            if "checksum" in loaded_data:
                expected_checksum = self._compute_checksum(loaded_data["data"])
                if loaded_data["checksum"] != expected_checksum:
                    logger.error("❌ 数据校验失败,可能被篡改")
                    return None

            # 验证数据结构
            if not self._validate_schema(loaded_data["data"], schema):
                logger.error("❌ 数据验证失败,不符合schema要求")
                return None

            return loaded_data["data"]

        # 兼容旧格式(无校验和)
        if self._validate_schema(loaded_data, schema):
            return loaded_data

        logger.error("❌ 数据验证失败")
        return None

    def _compute_checksum(self, data: Any) -> str:
        """计算数据的校验和"""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def _validate_schema(self, data: Any, schema: dict) -> bool:
        """
        验证数据结构

        Args:
            data: 要验证的数据
            schema: schema定义

        Returns:
            是否符合schema
        """
        if not isinstance(data, dict):
            return False

        for key, expected_type in schema.items():
            if key not in data:
                logger.error(f"❌ 缺少必需字段: {key}")
                return False

            if not isinstance(data[key], expected_type):
                logger.error(
                    f"❌ 字段 {key} 类型错误,期望 {expected_type},实际 {type(data[key])}"
                )
                return False

        return True


# 全局默认序列化器实例
_default_serializer = None


def get_serializer(use_msgpack: bool = True) -> SecureSerializer:
    """获取默认的安全序列化器"""
    global _default_serializer
    if _default_serializer is None:
        _default_serializer = SecureSerializer(use_msgpack=use_msgpack)
    return _default_serializer


# 便捷函数
def secure_dump(data: Any, filepath: str, use_msgpack: bool = True) -> bool:
    """安全地序列化数据(便捷函数)"""
    return get_serializer(use_msgpack).dump(data, filepath)


def secure_load(filepath: str, use_msgpack: bool = True) -> Any | None:
    """安全地反序列化数据(便捷函数)"""
    return get_serializer(use_msgpack).load(filepath)
