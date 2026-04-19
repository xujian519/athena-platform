#!/usr/bin/env python3
"""
NebulaGraph知识图谱连接配置（修复版）
提供生产环境和开发环境的连接参数
"""

from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Any


def get_env_password(key: str) -> str:
    """从环境变量获取密码"""
    value = os.environ.get(key)
    if not value:
        raise ValueError(f"密码环境变量 {key} 未设置，请检查 .env 文件")
    return value


@dataclass
class NebulaGraphConfig:
    """NebulaGraph连接配置"""

    # 基础连接信息
    hosts: list[str]
    port: int
    username: str
    password: str
    space_name: str

    # 连接池配置
    max_connections: int = 10
    timeout: int = 60000  # 毫秒

    # 空间配置
    partition_num: int = 10
    replica_factor: int = 1

    # 标签和边类型定义
    tags: dict[str, list[str]]
    edges: dict[str, list[str]]

    @classmethod
    def get_production_config(cls) -> NebulaGraphConfig:
        """获取生产环境配置"""
        return cls(
            hosts=["127.0.0.1"],
            port=9669,
            username="root",
            password=get_env_password("NEBULA_PASSWORD"),
            space_name="patent_kg",
            max_connections=20,
            timeout=120000,
            partition_num=20,
            replica_factor=1,
            tags={
                "patent_entity": ["name", "type", "description", "category", "weight"],
                "patent_type": ["name", "description"],
                "applicant": ["name", "category", "country"],
                "inventor": ["name", "affiliation"],
                "ipc_code": ["code", "description", "section"],
                "legal_status": ["status", "date", "authority"]
            },
            edges={
                "patent_relation": ["relation_type", "confidence", "source", "date"],
                "has_patent_type": ["classification_date", "authority"],
                "invented_by": ["invention_date", "contribution"],
                "belongs_to_ipc": ["classification_date", "depth"],
                "has_legal_status": ["status_change_date", "authority"],
                "cites": ["citation_date", "citation_type", "context"]
            }
        )

    @classmethod
    def get_development_config(cls) -> NebulaGraphConfig:
        """获取开发环境配置"""
        return cls(
            hosts=["127.0.0.1"],
            port=9669,
            username="root",
            password=get_env_password("NEBULA_PASSWORD"),
            space_name="patent_kg_dev",
            max_connections=5,
            timeout=30000,
            partition_num=5,
            replica_factor=1,
            tags=cls.get_production_config().tags,
            edges=cls.get_production_config().edges
        )

    @classmethod
    def get_test_config(cls) -> NebulaGraphConfig:
        """获取测试环境配置"""
        return cls(
            hosts=["127.0.0.1"],
            port=9669,
            username="root",
            password=get_env_password("NEBULA_PASSWORD"),
            space_name="patent_kg_test",
            max_connections=3,
            timeout=15000,
            partition_num=3,
            replica_factor=1,
            tags=cls.get_production_config().tags,
            edges=cls.get_production_config().edges
        )

    @classmethod
    def from_env(cls) -> NebulaGraphConfig:
        """从环境变量加载配置"""
        return cls(
            hosts=os.getenv("NEBULA_HOSTS", "127.0.0.1").split(","),
            port=int(os.getenv("NEBULA_PORT", "9669")),
            username=os.getenv("NEBULA_USERNAME", "root"),
            password=os.getenv("NEBULA_PASSWORD", "nebula"),
            space_name=os.getenv("NEBULA_SPACE", "patent_kg"),
            max_connections=int(os.getenv("NEBULA_MAX_CONNECTIONS", "10")),
            timeout=int(os.getenv("NEBULA_TIMEOUT", "60000"))
        )


def get_config_class() -> Any | None:
    """获取正确的Config类"""
    try:
        from nebula3.Config import Config
        return Config
    except ImportError:
        # 旧版本兼容
        from nebula3.gclient.net import ConnectionPool as Config
        return Config


# 便捷函数
def get_nebula_config(env: str = "production") -> NebulaGraphConfig:
    """获取NebulaGraph配置的便捷函数

    Args:
        env: 环境类型 ("production", "development", "test")

    Returns:
        NebulaGraph配置对象
    """
    if env == "production":
        return NebulaGraphConfig.get_production_config()
    elif env == "development":
        return NebulaGraphConfig.get_development_config()
    elif env == "test":
        return NebulaGraphConfig.get_test_config()
    else:
        return NebulaGraphConfig.get_development_config()


if __name__ == "__main__":
    # 测试配置
    config = get_nebula_config("production")
    print("NebulaGraph配置:")
    print(f"  主机: {config.hosts}")
    print(f"  端口: {config.port}")
    print(f"  空间: {config.space_name}")
    print(f"  用户: {config.username}")
