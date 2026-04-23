#!/usr/bin/env python3
from __future__ import annotations
"""
安全配置加载器
Secure Configuration Loader

从环境变量安全加载配置,避免硬编码敏感信息

作者: Athena平台团队
创建时间: 2026-01-16
更新时间: 2026-01-26 (TD-001: 迁移到Neo4j)
版本: v2.0.0
"""

import logging
import os
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

try:
    from dotenv import load_dotenv

    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

logger = setup_logging()


class SecureConfig:
    """
    安全配置管理器

    从环境变量加载配置,避免硬编码敏感信息
    """

    def __init__(self, env_file: str | None = None):
        """
        初始化配置管理器

        Args:
            env_file: .env文件路径,默认为项目根目录的.env
        """
        self._config: dict[str, Any] = {}
        self._load_env_file(env_file)

    def _load_env_file(self, env_file: str | None = None) -> Any:
        """
        加载.env文件

        Args:
            env_file: .env文件路径
        """
        if env_file is None:
            # 尝试找到项目根目录的.env文件
            current_path = Path(__file__).resolve()
            for parent in [
                current_path,
                current_path.parent.parent,
                current_path.parent.parent.parent,
            ]:
                env_path = parent / ".env"
                if env_path.exists():
                    env_file = str(env_path)
                    break

        if env_file and DOTENV_AVAILABLE:
            try:
                load_dotenv(env_file)
                logger.info(f"✅ 已加载环境变量文件: {env_file}")
            except Exception as e:
                logger.warning(f"⚠️ 加载.env文件失败: {e}")
        elif not DOTENV_AVAILABLE:
            logger.warning("⚠️ python-dotenv未安装,无法加载.env文件")

    def get(self, key: str, default: str | None = None, required: bool = False) -> str | None:
        """
        获取配置值

        Args:
            key: 配置键名
            default: 默认值
            required: 是否必需(必需时如果未找到会抛出异常)

        Returns:
            配置值

        Raises:
            ValueError: 当required=True且配置不存在时
        """
        value = os.getenv(key, default)

        if required and value is None:
            raise ValueError(
                f"❌ 缺少必需的环境变量: {key}\n"
                f"请在.env文件中设置此变量,或参考.env.example模板"
            )

        return value

    def get_int(self, key: str, default: int = 0, required: bool = False) -> int:
        """获取整数配置"""
        value = self.get(key, str(default) if default is not None else None, required)
        if value is None:
            return 0
        try:
            return int(value)
        except ValueError:
            logger.error(f"❌ 配置 {key} 的值 '{value}' 不是有效的整数")
            return default or 0

    def get_bool(self, key: str, default: bool = False) -> bool:
        """获取布尔配置"""
        value = self.get(key, str(default))
        if value is None:
            return default
        return value.lower() in ("true", "1", "yes", "on")

    def get_postgres_config(self) -> dict[str, Any]:
        """获取PostgreSQL配置"""
        return {
            "host": self.get("POSTGRES_HOST", "localhost"),
            "port": self.get_int("POSTGRES_PORT", 5432),
            "user": self.get("POSTGRES_USER", "postgres"),
            "password": self.get("POSTGRES_PASSWORD", required=True),
            "dbname": self.get("POSTGRES_DBNAME", "athena"),
        }

    def get_nebula_config(self) -> dict[str, Any]:
        """
        获取NebulaGraph配置

        ⚠️ TD-001: 已废弃,请使用get_neo4j_config()
        NebulaGraph已迁移到Neo4j
        """
        import warnings

        warnings.warn(
            "get_nebula_config()已废弃,请使用get_neo4j_config() (TD-001)",
            DeprecationWarning,
            stacklevel=2
        )

        return {
            "address": self.get("NEBULA_ADDRESS", "127.0.0.1:9669"),
            "user": self.get("NEBULA_USER", "root"),
            "password": self.get("NEBULA_PASSWORD", required=True),
            "space": self.get("NEBULA_SPACE", "patent_kg"),
        }

    def get_neo4j_config(self) -> dict[str, Any]:
        """获取Neo4j配置"""
        return {
            "uri": self.get("NEO4J_URI", "bolt://localhost:7687"),
            "username": self.get("NEO4J_USERNAME", "neo4j"),
            "password": self.get("NEO4J_PASSWORD", required=True),
            "database": self.get("NEO4J_DATABASE", "patent_guidelines"),
        }

    def get_redis_config(self) -> dict[str, Any]:
        """获取Redis配置"""
        return {
            "host": self.get("REDIS_HOST", "localhost"),
            "port": self.get_int("REDIS_PORT", 6379),
            "password": self.get("REDIS_PASSWORD", ""),
            "db": self.get_int("REDIS_DB", 0),
        }


# 全局配置实例
_global_config: SecureConfig | None = None


def get_config(env_file: str | None = None) -> SecureConfig:
    """
    获取全局配置实例

    Args:
        env_file: .env文件路径

    Returns:
        SecureConfig实例
    """
    global _global_config
    if _global_config is None:
        _global_config = SecureConfig(env_file)
    return _global_config


def get_password(service_name: str) -> str:
    """
    获取服务密码(便捷函数)

    Args:
        service_name: 服务名称(postgres, nebula, neo4j等)

    Returns:
        密码字符串

    Raises:
        ValueError: 当密码未配置时
    """
    config = get_config()
    password_key = f"{service_name.upper()}_PASSWORD"
    password = config.get(password_key, required=True)
    if password is None:
        raise ValueError(f"密码配置 {password_key} 未设置")
    return password


# 导出
__all__ = [
    "SecureConfig",
    "get_config",
    "get_password",
]


if __name__ == "__main__":
    # 测试配置加载
    import sys

    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("🔐 安全配置加载器测试")
    print("=" * 60)

    try:
        config = get_config()

        # 测试PostgreSQL配置
        print("\n📊 PostgreSQL配置:")
        pg_config = config.get_postgres_config()
        for key, value in pg_config.items():
            if key == "password":
                print(f"  {key}: {'*' * len(value)}")
            else:
                print(f"  {key}: {value}")

        # 测试NebulaGraph配置
        print("\n📊 NebulaGraph配置:")
        nebula_config = config.get_nebula_config()
        for key, value in nebula_config.items():
            if key == "password":
                print(f"  {key}: {'*' * len(value)}")
            else:
                print(f"  {key}: {value}")

        print("\n✅ 配置加载测试完成")

    except ValueError as e:
        print(f"\n❌ 配置错误: {e}")
        print("\n💡 提示: 请确保已创建.env文件并填入必要的配置")
        print("   可以参考.env.example模板")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
