#!/usr/bin/env python3
"""
NebulaGraph知识图谱连接配置
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
            hosts=["127.0.0.1"],  # localhost映射
            port=9669,
            username="root",
            password=get_env_password("NEBULA_PASSWORD"),
            space_name="patent_kg",
            max_connections=20,
            timeout=120000,  # 2分钟
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
        env = os.getenv("ENVIRONMENT", "development").lower()

        if env == "production":
            return cls.get_production_config()
        elif env == "test":
            return cls.get_test_config()
        else:
            return cls.get_development_config()

    def get_connection_string(self) -> str:
        """获取连接字符串"""
        hosts_str = ",".join([f"{host}:{self.port}" for host in self.hosts])
        return f"nebula://{self.username}@{hosts_str}/{self.space_name}"

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        return {
            "hosts": self.hosts,
            "port": self.port,
            "username": self.username,
            "password": self.password,
            "space_name": self.space_name,
            "max_connections": self.max_connections,
            "timeout": self.timeout,
            "partition_num": self.partition_num,
            "replica_factor": self.replica_factor,
            "tags": self.tags,
            "edges": self.edges
        }

    def validate(self) -> list[str]:
        """验证配置有效性"""
        errors = []

        if not self.hosts:
            errors.append("主机地址不能为空")

        if self.port <= 0 or self.port > 65535:
            errors.append("端口号无效")

        if not self.username:
            errors.append("用户名不能为空")

        if not self.space_name:
            errors.append("空间名不能为空")

        if self.max_connections <= 0:
            errors.append("最大连接数必须大于0")

        if self.partition_num <= 0:
            errors.append("分区数必须大于0")

        if self.replica_factor <= 0:
            errors.append("副本因子必须大于0")

        return errors

class NebulaGraphConnectionManager:
    """NebulaGraph连接管理器"""

    def __init__(self, config: NebulaGraphConfig):
        self.config = config
        self.connection_pool = None
        self.session = None

    def get_connection_info(self) -> dict[str, Any]:
        """获取连接信息"""
        return {
            "connection_string": self.config.get_connection_string(),
            "hosts": self.config.hosts,
            "port": self.config.port,
            "space_name": self.config.space_name,
            "max_connections": self.config.max_connections,
            "timeout_ms": self.config.timeout
        }

    def get_schema_info(self) -> dict[str, Any]:
        """获取模式信息"""
        return {
            "tags": self.config.tags,
            "edges": self.config.edges,
            "space_config": {
                "partition_num": self.config.partition_num,
                "replica_factor": self.config.replica_factor
            }
        }

    def export_config_file(self, filepath: str) -> bool:
        """导出配置文件"""
        try:
            import json
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"导出配置文件失败: {e}")
            return False

    def to_dict(self) -> dict[str, Any]:
        """完整配置字典"""
        return {
            "connection": self.get_connection_info(),
            "schema": self.get_schema_info(),
            "environment": os.getenv("ENVIRONMENT", "development")
        }

# 全局配置实例
PRODUCTION_CONFIG = NebulaGraphConfig.get_production_config()
DEVELOPMENT_CONFIG = NebulaGraphConfig.get_development_config()
TEST_CONFIG = NebulaGraphConfig.get_test_config()

# 当前环境配置
CURRENT_CONFIG = NebulaGraphConfig.from_env()

# 连接管理器
PRODUCTION_MANAGER = NebulaGraphConnectionManager(PRODUCTION_CONFIG)
DEVELOPMENT_MANAGER = NebulaGraphConnectionManager(DEVELOPMENT_CONFIG)
TEST_MANAGER = NebulaGraphConnectionManager(TEST_CONFIG)

# 默认管理器
DEFAULT_MANAGER = NebulaGraphConnectionManager(CURRENT_CONFIG)

def get_config_manager(environment: str = None) -> NebulaGraphConnectionManager:
    """根据环境获取配置管理器"""
    if environment == "production":
        return PRODUCTION_MANAGER
    elif environment == "test":
        return TEST_MANAGER
    else:
        return DEFAULT_MANAGER

if __name__ == "__main__":
    # 打印当前配置信息
    config = CURRENT_CONFIG
    manager = DEFAULT_MANAGER

    print("🌐 NebulaGraph连接配置")
    print("=" * 50)
    print(f"环境: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"连接字符串: {config.get_connection_string()}")
    print(f"空间名: {config.space_name}")
    print(f"主机: {config.hosts}")
    print(f"端口: {config.port}")
    print(f"最大连接数: {config.max_connections}")
    print(f"超时时间: {config.timeout}ms")
    print(f"分区数: {config.partition_num}")
    print(f"副本因子: {config.replica_factor}")
    print(f"标签数量: {len(config.tags)}")
    print(f"边类型数量: {len(config.edges)}")

    # 验证配置
    errors = config.validate()
    if errors:
        print("\n❌ 配置错误:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\n✅ 配置验证通过")

    # 导出配置文件
    config_path = "/Users/xujian/Athena工作平台/config/nebula_graph_config.json"
    if manager.export_config_file(config_path):
        print(f"\n📄 配置文件已导出: {config_path}")
    else:
        print(f"\n❌ 配置文件导出失败: {config_path}")
