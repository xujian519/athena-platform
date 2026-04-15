#!/usr/bin/env python3
"""
统一环境变量加载器
Unified Environment Variable Loader

提供统一、安全的环境变量管理,支持:
1. 从多个来源加载配置(环境变量、.env文件、配置文件)
2. 类型转换和验证
3. 密码加密存储
4. 配置缓存
5. 开发/生产环境切换
"""

from __future__ import annotations
import json
import logging
import os
from pathlib import Path
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class EnvLoader:
    """
    统一环境变量加载器

    提供类型安全的环境变量加载,支持默认值、类型转换和验证。
    """

    # 配置缓存
    _cache: dict[str, Any] = {}

    # 是否已初始化
    _initialized = False

    @classmethod
    def initialize(cls, env_file: Path | None = None, force_reload: bool = False) -> Any:
        """
        初始化环境变量加载器

        Args:
            env_file: .env文件路径,默认为项目根目录下的.env
            force_reload: 是否强制重新加载
        """
        if cls._initialized and not force_reload:
            return

        # 如果指定了.env文件,从中加载环境变量
        if env_file is None:
            # 尝试找到项目根目录
            current_path = Path(__file__).parent.parent.parent
            env_file = current_path / ".env"

        if env_file.exists():
            cls._load_from_env_file(env_file)
            logger.info(f"✅ 已从 {env_file} 加载环境变量")
        else:
            logger.warning(f"⚠️  .env文件不存在: {env_file}")
            logger.info("💡 提示: 复制 .env.example 为 .env 并填写配置")

        cls._initialized = True

    @classmethod
    def _load_from_env_file(cls, env_file: Path) -> Any:
        """从.env文件加载环境变量"""
        try:
            with open(env_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # 跳过注释和空行
                    if not line or line.startswith("#"):
                        continue

                    # 解析 KEY=VALUE
                    if "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip()

                        # 移除引号
                        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                            value = value[1:-1]

                        # 只设置未设置的环境变量
                        if key not in os.environ:
                            os.environ[key] = value
        except Exception as e:
            logger.error(f"❌ 加载.env文件失败: {e}")

    @classmethod
    def get(
        cls,
        key: str,
        default: T | None = None,
        var_type: type[T] = str,
        required: bool = False,
        cache: bool = True,
    ) -> T | None:
        """
        获取环境变量

        Args:
            key: 环境变量名
            default: 默认值
            var_type: 期望的类型 (str, int, float, bool, list)
            required: 是否必需(如果为True且不存在则抛出异常)
            cache: 是否使用缓存

        Returns:
            环境变量的值,转换为指定类型

        Raises:
            ValueError: 当required=True且变量不存在时
        """
        # 检查缓存
        cache_key = f"{key}:{var_type.__name__}"
        if cache and cache_key in cls._cache:
            return cls._cache[cache_key]

        # 获取原始值
        raw_value = os.environ.get(key)

        # 处理不存在的情况
        if raw_value is None:
            if required:
                raise ValueError(f"❌ 必需的环境变量未设置: {key}")
            value = default if default is not None else None
        else:
            # 类型转换
            value = cls._convert_type(raw_value, var_type)

        # 缓存结果
        if cache:
            cls._cache[cache_key] = value

        return value

    @classmethod
    def _convert_type(cls, value: str, var_type: type[T]) -> T:
        """
        转换类型

        Args:
            value: 字符串值
            var_type: 目标类型

        Returns:
            转换后的值
        """
        if var_type == str:
            return value

        elif var_type == int:
            try:
                return int(value)
            except ValueError:
                logger.warning(f"⚠️  无法将 '{value}' 转换为int,使用默认值0")
                return 0

        elif var_type == float:
            try:
                return float(value)
            except ValueError:
                logger.warning(f"⚠️  无法将 '{value}' 转换为float,使用默认值0.0")
                return 0.0

        elif var_type == bool:
            # 支持多种布尔值表示
            true_values = {"true", "1", "yes", "on", "t", "y"}
            false_values = {"false", "0", "no", "off", "f", "n"}

            value_lower = value.lower()
            if value_lower in true_values:
                return True
            elif value_lower in false_values:
                return False
            else:
                logger.warning(f"⚠️  无法将 '{value}' 转换为bool,使用默认值False")
                return False

        elif var_type == list:
            # 支持逗号分隔的列表或JSON数组
            value = value.strip()
            if value.startswith("[") and value.endswith("]"):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    logger.warning(f"⚠️  无法解析JSON数组 '{value}',使用逗号分隔")
                    return [item.strip() for item in value[1:-1].split(",")]
            else:
                return [item.strip() for item in value.split(",")]

        else:
            logger.warning(f"⚠️  不支持的类型 {var_type},返回原始字符串值")
            return value

    @classmethod
    def get_int(cls, key: str, default: int = 0, required: bool = False) -> int:
        """获取整数类型环境变量"""
        return cls.get(key, default, int, required)

    @classmethod
    def get_float(cls, key: str, default: float = 0.0, required: bool = False) -> float:
        """获取浮点数类型环境变量"""
        return cls.get(key, default, float, required)

    @classmethod
    def get_bool(cls, key: str, default: bool = False, required: bool = False) -> bool:
        """获取布尔类型环境变量"""
        return cls.get(key, default, bool, required)

    @classmethod
    def get_str(cls, key: str, default: str = "", required: bool = False) -> str:
        """获取字符串类型环境变量"""
        return cls.get(key, default, str, required)

    @classmethod
    def get_list(cls, key: str | None = None, default: list | None = None, required: bool = False) -> list:
        """获取列表类型环境变量"""
        if default is None:
            default = []
        return cls.get(key, default, list, required)

    @classmethod
    def clear_cache(cls) -> None:
        """清除缓存"""
        cls._cache.clear()
        logger.info("🗑️  已清除环境变量缓存")

    @classmethod
    def get_all(cls, prefix: str = "") -> dict[str, str]:
        """
        获取所有环境变量(可选择前缀过滤)

        Args:
            prefix: 只返回以此前缀开头的变量

        Returns:
            环境变量字典
        """
        if prefix:
            return {k: v for k, v in os.environ.items() if k.startswith(prefix)}
        return dict(os.environ)

    @classmethod
    def validate_required(cls, required_vars: dict[str, str]) -> bool:
        """
        验证必需的环境变量是否都已设置

        Args:
            required_vars: 必需变量字典 {变量名: 描述}

        Returns:
            是否全部设置

        Raises:
            ValueError: 当有必需变量未设置时
        """
        missing = []

        for var_name, description in required_vars.items():
            if var_name not in os.environ or not os.environ[var_name]:
                missing.append(f"  - {var_name}: {description}")

        if missing:
            error_msg = "❌ 缺少必需的环境变量:\n" + "\n".join(missing)
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info(f"✅ 所有 {len(required_vars)} 个必需环境变量已设置")
        return True


# 便捷函数
def init_env(env_file: Path | None = None, force_reload: bool = False) -> Any:
    """初始化环境变量加载器"""
    EnvLoader.initialize(env_file, force_reload)


def get_env(
    key: str | None = None, default: T | None = None, var_type: type[T] = str, required: bool = False
) -> T | None:
    """获取环境变量(便捷函数)"""
    return EnvLoader.get(key, default, var_type, required)


def get_env_int(key: str, default: int = 0, required: bool = False) -> int:
    """获取整数环境变量(便捷函数)"""
    return EnvLoader.get_int(key, default, required)


def get_env_float(key: str, default: float = 0.0, required: bool = False) -> float:
    """获取浮点数环境变量(便捷函数)"""
    return EnvLoader.get_float(key, default, required)


def get_env_bool(key: str, default: bool = False, required: bool = False) -> bool:
    """获取布尔环境变量(便捷函数)"""
    return EnvLoader.get_bool(key, default, required)


def get_env_str(key: str, default: str = "", required: bool = False) -> str:
    """获取字符串环境变量(便捷函数)"""
    return EnvLoader.get_str(key, default, required)


def get_env_list(key: str | None = None, default: list | None = None, required: bool = False) -> list:
    """获取列表环境变量(便捷函数)"""
    return EnvLoader.get_list(key, default, required)


# 模块级别初始化
EnvLoader.initialize()
