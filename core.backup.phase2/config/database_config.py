"""
Athena平台数据库配置管理

> 版本: v1.0
> 更新: 2026-04-21
> 说明: 统一管理Athena、Patent和Legal World Model三个数据库

数据库资产：
1. Athena主库（PostgreSQL）- 系统数据
2. Patent专利库（PostgreSQL）- 专利数据
3. Legal World Model（Neo4j）- 法律知识图谱
"""

from pydantic import Field, field_validator
from typing import Optional
from .unified_settings import Settings


class DatabaseConfig:
    """数据库配置基类"""
    
    host: str
    port: int
    name: str
    user: str
    password: str
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600


class AthenaDatabaseConfig(DatabaseConfig):
    """Athena主库配置"""
    
    def __init__(self, settings: Settings):
        self.host = settings.database_host
        self.port = settings.database_port
        self.name = settings.database_name
        self.user = settings.database_user
        self.password = settings.database_password
        self.pool_size = settings.database_pool_size
        self.max_overflow = settings.database_max_overflow
        self.pool_timeout = settings.database_pool_timeout
        self.pool_recycle = settings.database_pool_recycle
    
    @property
    def url(self) -> str:
        """生成数据库连接URL"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class PatentDatabaseConfig(DatabaseConfig):
    """Patent专利库配置"""
    
    def __init__(self, settings: Settings):
        # 从环境变量读取
        import os
        self.host = os.getenv("PATENT_DB_HOST", "localhost")
        self.port = int(os.getenv("PATENT_DB_PORT", 5432))
        self.name = os.getenv("PATENT_DB_NAME", "patent_db")
        self.user = os.getenv("PATENT_DB_USER", "athena")
        self.password = os.getenv("PATENT_DB_PASSWORD", "")
        self.pool_size = int(os.getenv("PATENT_DB_POOL_SIZE", 10))
        self.max_overflow = int(os.getenv("PATENT_DB_MAX_OVERFLOW", 20))
        self.pool_timeout = int(os.getenv("PATENT_DB_POOL_TIMEOUT", 30))
        self.pool_recycle = int(os.getenv("PATENT_DB_POOL_RECYCLE", 3600))
    
    @property
    def url(self) -> str:
        """生成数据库连接URL"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class Neo4jDatabaseConfig:
    """Neo4j法律世界模型配置"""
    
    def __init__(self, settings: Settings):
        import os
        self.host = os.getenv("NEO4J_HOST", "localhost")
        self.port = 7687
        self.name = "neo4j"
        self.user = "neo4j"
        self.password = os.getenv("NEO4J_PASSWORD", "")
        self.database = os.getenv("NEO4J_DATABASE", "neo4j")
    
    @property
    def bolt_url(self) -> str:
        """生成Bolt协议URL"""
        return f"bolt://{self.user}:{self.password}@{self.host}:{self.port}"
    
    @property
    def http_url(self) -> str:
        """生成HTTP协议URL"""
        return f"http://{self.host}:{7474}"


class DatabaseManager:
    """数据库管理器 - 统一管理所有数据库"""
    
    def __init__(self, settings: Settings = None):
        """初始化数据库管理器"""
        self.settings = settings or Settings.load()
        self.athena = AthenaDatabaseConfig(self.settings)
        self.patent = PatentDatabaseConfig(self.settings)
        self.neo4j = Neo4jDatabaseConfig(self.settings)
    
    def get_athena_config(self) -> AthenaDatabaseConfig:
        """获取Athena主库配置"""
        return self.athena
    
    def get_patent_config(self) -> PatentDatabaseConfig:
        """获取Patent专利库配置"""
        return self.patent
    
    def get_neo4j_config(self) -> Neo4jDatabaseConfig:
        """获取Neo4j配置"""
        return self.neo4j
    
    def get_all_configs(self) -> dict:
        """获取所有数据库配置"""
        return {
            "athena": {
                "url": self.athena.url,
                "name": self.athena.name,
                "host": self.athena.host,
                "port": self.athena.port
            },
            "patent": {
                "url": self.patent.url,
                "name": self.patent.name,
                "host": self.patent.host,
                "port": self.patent.port
            },
            "neo4j": {
                "bolt_url": self.neo4j.bolt_url,
                "http_url": self.neo4j.http_url,
                "name": self.neo4j.database,
                "host": self.neo4j.host
            }
        }


# 全局数据库管理器实例
_db_manager: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """
    获取全局数据库管理器实例
    
    返回:
        数据库管理器实例（单例）
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


__all__ = [
    "AthenaDatabaseConfig",
    "PatentDatabaseConfig",
    "Neo4jDatabaseConfig",
    "DatabaseManager",
    "get_database_manager",
]
