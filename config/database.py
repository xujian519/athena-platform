#!/usr/bin/env python3
"""
数据库配置管理 - 支持PostgreSQL专利数据库
Database Configuration Manager - Support PostgreSQL Patent Database
"""

import logging
import os
from dataclasses import dataclass
from typing import Any

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """数据库配置类"""

    host: str = "localhost"
    port: int = 5432
    database: str = "patent_db"
    username: str = "postgres"
    password: str = ""
    schema: str = "public"
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600

    def get_connection_string(self) -> str:
        """获取数据库连接字符串"""
        if self.password:
            return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        else:
            return f"postgresql://{self.username}@{self.host}:{self.port}/{self.database}"

    def get_connection_params(self) -> dict[str, Any]:
        """获取数据库连接参数"""
        params = {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "user": self.username,
            "cursor_factory": None,  # 将在使用时设置
        }

        if self.password:
            params["password"] = self.password

        return params


class PatentDatabaseConfig:
    """专利数据库专用配置"""

    def __init__(self):
        self.config = self._load_config()
        self._validate_config()

    def _load_config(self) -> DatabaseConfig:
        """从环境变量加载配置"""
        config = DatabaseConfig()

        # 从环境变量读取配置
        config.host = os.getenv("PATENT_DB_HOST", "localhost")
        config.port = int(os.getenv("PATENT_DB_PORT", "5432"))
        config.database = os.getenv("PATENT_DB_NAME", "patent_db")
        config.username = os.getenv("PATENT_DB_USER", "postgres")
        config.password = os.getenv("PATENT_DB_PASSWORD", "")
        config.schema = os.getenv("PATENT_DB_SCHEMA", "public")

        # 连接池配置
        config.pool_size = int(os.getenv("PATENT_DB_POOL_SIZE", "10"))
        config.max_overflow = int(os.getenv("PATENT_DB_MAX_OVERFLOW", "20"))
        config.pool_timeout = int(os.getenv("PATENT_DB_POOL_TIMEOUT", "30"))
        config.pool_recycle = int(os.getenv("PATENT_DB_POOL_RECYCLE", "3600"))

        logger.info(f"✅ 专利数据库配置加载完成: {config.host}:{config.port}/{config.database}")

        return config

    def _validate_config(self):
        """验证配置有效性"""
        if not self.config.host:
            raise ValueError("数据库主机不能为空")

        if not self.config.database:
            raise ValueError("数据库名不能为空")

        if not self.config.username:
            raise ValueError("数据库用户名不能为空")

        if self.config.port < 1 or self.config.port > 65535:
            raise ValueError("数据库端口无效")

    def get_config(self) -> DatabaseConfig:
        """获取数据库配置"""
        return self.config

    def get_connection_string(self) -> str:
        """获取连接字符串"""
        return self.config.get_connection_string()

    def get_connection_params(self) -> dict[str, Any]:
        """获取连接参数"""
        return self.config.get_connection_params()

    def get_patent_table_config(self) -> dict[str, str]:
        """获取专利表配置"""
        return {
            "patents_table": os.getenv("PATENTS_TABLE", "patents"),
            "patents_fulltext_index": os.getenv("PATENTS_FULLTEXT_INDEX", "patents_ft_idx"),
            "patents_vector_table": os.getenv("PATENTS_VECTOR_TABLE", "patent_vectors"),
            "patents_citations_table": os.getenv("PATENTS_CITATIONS_TABLE", "patent_citations"),
            "patents_ipc_table": os.getenv("PATENTS_IPC_TABLE", "patent_ipc"),
        }

    def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor

            logger.info(
                f"🔄 测试专利数据库连接: {self.config.host}:{self.config.port}/{self.config.database}"
            )

            conn = psycopg2.connect(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.username,
                password=self.config.password,
                cursor_factory=RealDictCursor,
                connect_timeout=10,
            )

            # 测试查询
            with conn.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()
                logger.info(f"✅ 数据库连接成功: {version[0] if version else 'Unknown'}")

                # 检查专利表是否存在
                table_config = self.get_patent_table_config()
                cursor.execute(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = '{self.config.schema}'
                        AND table_name = '{table_config["patents_table"]}'
                    );
                """)
                table_exists = cursor.fetchone()[0]

                if table_exists:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_config['patents_table']}")
                    patent_count = cursor.fetchone()[0]
                    logger.info(f"📊 专利表存在，包含 {patent_count:,} 条记录")
                else:
                    logger.warning(f"⚠️ 专利表 {table_config['patents_table']} 不存在")

            conn.close()
            return True

        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            return False

    def get_search_config(self) -> dict[str, Any]:
        """获取搜索相关配置"""
        return {
            "default_limit": int(os.getenv("PATENT_SEARCH_LIMIT", "20")),
            "max_limit": int(os.getenv("PATENT_SEARCH_MAX_LIMIT", "100")),
            "highlight_enabled": os.getenv("PATENT_SEARCH_HIGHLIGHT", "true").lower() == "true",
            "ranking_weights": {
                "title": float(os.getenv("PATENT_RANK_TITLE_WEIGHT", "2.0")),
                "abstract": float(os.getenv("PATENT_RANK_ABSTRACT_WEIGHT", "1.5")),
                "claims": float(os.getenv("PATENT_RANK_CLAIMS_WEIGHT", "1.0")),
                "description": float(os.getenv("PATENT_RANK_DESCRIPTION_WEIGHT", "0.8")),
            },
            "search_languages": os.getenv("PATENT_SEARCH_LANGUAGES", "chinese,english").split(","),
            "min_query_length": int(os.getenv("PATENT_SEARCH_MIN_QUERY_LENGTH", "2")),
        }


# 创建全局配置实例
patent_db_config = PatentDatabaseConfig()


# 便捷函数
def get_patent_db_config() -> PatentDatabaseConfig:
    """获取专利数据库配置实例"""
    return patent_db_config


def get_patent_connection_string() -> str:
    """获取专利数据库连接字符串"""
    return patent_db_config.get_connection_string()


def get_patent_connection_params() -> dict[str, Any]:
    """获取专利数据库连接参数"""
    return patent_db_config.get_connection_params()


def test_patent_database() -> bool:
    """测试专利数据库连接"""
    return patent_db_config.test_connection()


if __name__ == "__main__":
    # 测试配置
    print("🔧 专利数据库配置信息")
    print("=" * 50)

    config = get_patent_db_config().get_config()
    print(f"主机: {config.host}")
    print(f"端口: {config.port}")
    print(f"数据库: {config.database}")
    print(f"用户名: {config.username}")
    print(f"模式: {config.schema}")
    print(f"连接池大小: {config.pool_size}")

    # 测试连接
    print("\n🔄 测试数据库连接...")
    if test_patent_database():
        print("✅ 数据库配置正常")
    else:
        print("❌ 数据库配置有问题")
