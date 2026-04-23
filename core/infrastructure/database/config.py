
"""
数据库配置管理模块
提供统一的数据库配置,从环境变量读取
"""

import os
from typing import Any

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class DatabaseConfig:
    """数据库配置类,从环境变量读取配置"""

    @staticmethod
    def get_postgresql_config() -> dict[str, Any]:
        """
        获取PostgreSQL配置

        Returns:
            包含PostgreSQL连接配置的字典
        """
        return {
            "host": os.getenv("PG_HOST", "localhost"),
            "port": int(os.getenv("PG_PORT", "5432")),
            "database": os.getenv("PG_DATABASE", "athena"),
            "user": os.getenv("PG_USER", "postgres"),
            "password": os.getenv("PG_PASSWORD", ""),
        }

    @staticmethod
    def get_neo4j_config() -> dict[str, Any]:
        """
        获取Neo4j配置

        Returns:
            包含Neo4j连接配置的字典
        """
        return {
            "uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            "user": os.getenv("NEO4J_USER", "neo4j"),
            "password": os.getenv("NEO4J_PASSWORD", ""),
        }

    @staticmethod
    def get_qdrant_config() -> dict[str, Any]:
        """
        获取Qdrant配置

        Returns:
            包含Qdrant连接配置的字典
        """
        return {
            "url": os.getenv("QDRANT_URL", "http://localhost:6333"),
        }

    @classmethod
    def validate_config(cls) -> bool:
        """
        验证必需的配置项是否存在

        Returns:
            验证通过返回True,否则返回False

        Raises:
            ValueError: 当必需的配置项缺失时
        """
        pg_config = cls.get_postgresql_config()
        neo4j_config = cls.get_neo4j_config()

        missing_configs = []

        if not pg_config["password"]:
            missing_configs.append("PG_PASSWORD")

        if not neo4j_config["password"]:
            missing_configs.append("NEO4J_PASSWORD")

        if missing_configs:
            raise ValueError(
                f"缺少必需的环境变量: {', '.join(missing_configs)}\n" f"请在.env文件中配置这些变量"
            )

        return True

