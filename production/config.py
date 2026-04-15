#!/usr/bin/env python3
"""
生产环境安全配置加载器
Production Environment Secure Configuration Loader

从环境变量加载配置,避免硬编码敏感信息

作者: 徐健
日期: 2025-12-29
"""

from __future__ import annotations
import os
from pathlib import Path

from dotenv import load_dotenv


class ProductionConfig:
    """生产环境配置类"""

    def __init__(self, env_file: str | None = None):
        """
        初始化配置

        Args:
            env_file: .env文件路径,如果为None则使用默认路径
        """
        # 加载环境变量
        if env_file:
            load_dotenv(env_file)
        else:
            # 尝试从多个位置加载.env文件
            possible_locations = [
                # 当前脚本目录
                Path(__file__).parent / '.env',
                # 项目根目录
                Path(__file__).parent.parent / '.env',
                # 当前工作目录
                Path.cwd() / '.env',
                # 脚本所在目录的上级
                Path(__file__).parent.parent.parent / '.env',
                # 系统配置
                Path('/etc/athena/.env'),
            ]
            loaded = False
            for location in possible_locations:
                if location.exists():
                    load_dotenv(location)
                    print(f"✅ 从 {location} 加载配置")
                    loaded = True
                    break

            if not loaded:
                print("⚠️  警告: 未找到.env文件,使用默认配置")
                print("   提示: 请复制.env.example到.env并配置密码")

    # ===========================
    # 数据库配置
    # ===========================

    @property
    def postgres_host(self) -> str:
        return os.getenv('POSTGRES_HOST', 'localhost')

    @property
    def postgres_port(self) -> int:
        return int(os.getenv('POSTGRES_PORT', 5432))

    @property
    def postgres_user(self) -> str:
        return os.getenv('POSTGRES_USER', 'athena')

    @property
    def postgres_password(self) -> str:
        """从环境变量获取PostgreSQL密码"""
        password = os.getenv('POSTGRES_PASSWORD')
        if not password:
            raise ValueError(
                "POSTGRES_PASSWORD环境变量未设置! "
                "请在.env文件中配置POSTGRES_PASSWORD"
            )
        return password

    @property
    def postgres_db(self) -> str:
        return os.getenv('POSTGRES_DB', 'athena_production')

    @property
    def postgres_url(self) -> str:
        """生成PostgreSQL连接URL"""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # ===========================
    # NebulaGraph配置 (已废弃)
    # ===========================
    # ⚠️  DEPRECATED: NebulaGraph已废弃，系统已迁移到PostgreSQL + Qdrant架构
    # 以下配置仅为向后兼容保留，新代码不应使用

    @property
    def nebula_host(self) -> str:
        """⚠️  DEPRECATED: NebulaGraph已废弃"""
        import warnings
        warnings.warn(
            "NebulaGraph已废弃，请使用PostgreSQL + Qdrant架构",
            DeprecationWarning,
            stacklevel=2
        )
        return os.getenv('NEBULA_HOST', 'localhost')

    @property
    def nebula_port(self) -> int:
        """⚠️  DEPRECATED: NebulaGraph已废弃"""
        return int(os.getenv('NEBULA_PORT', 9669))

    @property
    def nebula_user(self) -> str:
        """⚠️  DEPRECATED: NebulaGraph已废弃"""
        return os.getenv('NEBULA_USER', 'root')

    @property
    def nebula_password(self) -> str:
        """⚠️  DEPRECATED: NebulaGraph已废弃"""
        password = os.getenv('NEBULA_PASSWORD')
        if not password:
            # 不再抛出异常，返回默认值
            return 'nebula'
        return password

    @property
    def nebula_space(self) -> str:
        """⚠️  DEPRECATED: NebulaGraph已废弃"""
        return os.getenv('NEBULA_SPACE', 'athena_graph')

    @property
    def redis_host(self) -> str:
        return os.getenv('REDIS_HOST', 'localhost')

    @property
    def redis_port(self) -> int:
        return int(os.getenv('REDIS_PORT', 6379))

    @property
    def redis_password(self) -> str | None:
        return os.getenv('REDIS_PASSWORD')

    @property
    def redis_db(self) -> int:
        return int(os.getenv('REDIS_DB', 0))

    # ===========================
    # 服务端口
    # ===========================

    @property
    def api_port(self) -> int:
        return int(os.getenv('API_PORT', 8080))

    @property
    def api_host(self) -> str:
        return os.getenv('API_HOST', '0.0.0.0')

    @property
    def nlp_service_port(self) -> int:
        return int(os.getenv('NLP_SERVICE_PORT', 8000))

    @property
    def nlp_service_host(self) -> str:
        return os.getenv('NLP_SERVICE_HOST', 'localhost')

    # ===========================
    # 外部服务
    # ===========================

    @property
    def elasticsearch_host(self) -> str:
        return os.getenv('ELASTICSEARCH_HOST', 'localhost')

    @property
    def elasticsearch_port(self) -> int:
        return int(os.getenv('ELASTICSEARCH_PORT', 9200))

    @property
    def qdrant_host(self) -> str:
        return os.getenv('QDRANT_HOST', 'localhost')

    @property
    def qdrant_port(self) -> int:
        return int(os.getenv('QDRANT_PORT', 6333))

    # ===========================
    # 安全配置
    # ===========================

    @property
    def jwt_secret_key(self) -> str:
        key = os.getenv('JWT_SECRET_KEY')
        if not key or key == 'your_jwt_secret_key_change_in_production':
            raise ValueError(
                "JWT_SECRET_KEY未设置或使用默认值! "
                "请在.env文件中设置安全的JWT_SECRET_KEY"
            )
        return key

    @property
    def encryption_key(self) -> str:
        key = os.getenv('ENCRYPTION_KEY')
        if not key or key == 'your_encryption_key_change_in_production':
            raise ValueError(
                "ENCRYPTION_KEY未设置或使用默认值! "
                "请在.env文件中设置安全的ENCRYPTION_KEY"
            )
        return key

    @property
    def api_key(self) -> str | None:
        key = os.getenv('API_KEY')
        if key == 'your_api_key_if_needed':
            return None
        return key

    # ===========================
    # 日志配置
    # ===========================

    @property
    def log_level(self) -> str:
        return os.getenv('LOG_LEVEL', 'INFO')

    @property
    def log_file_path(self) -> str:
        return os.getenv('LOG_FILE_PATH', '/var/log/athena/production.log')

    # ===========================
    # 其他配置
    # ===========================

    @property
    def environment(self) -> str:
        return os.getenv('ENVIRONMENT', 'production')

    @property
    def timezone(self) -> str:
        return os.getenv('TIMEZONE', 'Asia/Shanghai')

    @property
    def max_workers(self) -> int:
        return int(os.getenv('MAX_WORKERS', 4))

    @property
    def request_timeout(self) -> int:
        return int(os.getenv('REQUEST_TIMEOUT', 30))


# 全局配置实例
_config: ProductionConfig | None = None


def get_config(env_file: str | None = None) -> ProductionConfig:
    """
    获取全局配置实例

    Args:
        env_file: .env文件路径

    Returns:
        ProductionConfig实例
    """
    global _config
    if _config is None:
        _config = ProductionConfig(env_file)
    return _config


def reload_config(env_file: str | None = None) -> ProductionConfig:
    """
    重新加载配置

    Args:
        env_file: .env文件路径

    Returns:
        新的ProductionConfig实例
    """
    global _config
    _config = ProductionConfig(env_file)
    return _config


# 便捷函数
def get_postgres_config() -> dict:
    """获取PostgreSQL配置字典"""
    config = get_config()
    return {
        'host': config.postgres_host,
        'port': config.postgres_port,
        'user': config.postgres_user,
        'password': config.postgres_password,
        'database': config.postgres_db,
    }


def get_nebula_config() -> dict:
    """
    ⚠️  DEPRECATED: 获取Nebula配置字典

    警告: NebulaGraph已废弃，此函数仅为向后兼容保留
    新代码应使用PostgreSQL + Qdrant架构
    """
    import warnings
    warnings.warn(
        "get_nebula_config()已废弃，请使用get_postgres_config()",
        DeprecationWarning,
        stacklevel=2
    )
    config = get_config()
    return {
        'host': config.nebula_host,
        'port': config.nebula_port,
        'user': config.nebula_user,
        'password': config.nebula_password,
        'space': config.nebula_space,
    }


def get_redis_config() -> dict:
    """获取Redis配置字典"""
    config = get_config()
    return {
        'host': config.redis_host,
        'port': config.redis_port,
        'password': config.redis_password,
        'db': config.redis_db,
    }


if __name__ == '__main__':
    # 测试配置加载
    print("🔧 测试生产环境配置加载")
    print("=" * 60)

    try:
        config = get_config()
        print("✅ 配置加载成功")
        print(f"   环境: {config.environment}")
        print(f"   PostgreSQL: {config.postgres_host}:{config.postgres_port}")
        print(f"   Qdrant: {config.qdrant_host}:{config.qdrant_port}")
        print(f"   Redis: {config.redis_host}:{config.redis_port}")
        print(f"   日志级别: {config.log_level}")
        print("   注意: NebulaGraph已废弃，使用PostgreSQL + Qdrant架构")
    except ValueError as e:
        print(f"❌ 配置加载失败: {e}")
        print("   请确保.env文件存在且包含必要的配置")
