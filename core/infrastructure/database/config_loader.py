
"""
数据库配置加载器
统一管理所有数据库配置
"""

import os
from dataclasses import dataclass
from typing import Any, Optional

import yaml


@dataclass
class DatabaseConfig:
    """数据库配置数据类"""

    type: str
    host: str
    port: int
    user: Optional[str] = None
    password: Optional[str] = None
    database: Optional[str] = None
    readonly: bool = False
    pool: Optional[dict[str, Any]] = None
    options: Optional[dict[str, Any]] = None


class DatabaseConfigLoader:
    """数据库配置加载器"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._find_config_file()
        self.config = self._load_config()
        self._resolve_env_variables()

    def _find_config_file(self) -> str:
        """查找配置文件"""
        possible_paths = [
            os.path.join(os.getcwd(), "config", "database_unified.yaml"),
            os.path.join(os.path.dirname(__file__), "../../../config/database_unified.yaml"),
            "/Users/xujian/Athena工作平台/config/database_unified.yaml",
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        raise FileNotFoundError("无法找到数据库配置文件")

    def _load_config(self) -> dict[str, Any]:
        """加载配置文件"""
        with open(self.config_path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _resolve_env_variables(self) -> Any:
        """解析环境变量"""
        env_vars = self.config.get("environment_variables", {})

        for _key, value in env_vars.items():
            # 解析 ${VAR:default} 格式
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                # 提取变量名和默认值
                var_expr = value[2:-1]
                if ":" in var_expr:
                    var_name, default_value = var_expr.split(":", 1)
                else:
                    var_name = var_expr
                    default_value = ""

                # 获取环境变量值或使用默认值
                env_value = os.getenv(var_name, default_value)
                os.environ[var_name] = env_value  # 设置环境变量

    def get_config(self, database_name: str) -> DatabaseConfig:
        """获取指定数据库的配置"""
        db_configs = self.config.get("databases", {})
        db_config = db_configs.get(database_name)

        if not db_config:
            raise ValueError(f"未找到数据库配置: {database_name}")

        # 解析环境变量
        config_dict = {}
        for key, value in db_config.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                var_expr = value[2:-1]
                if ":" in var_expr:
                    var_name, _ = var_expr.split(":", 1)
                else:
                    var_name = var_expr
                config_dict[key] = os.getenv(var_name, value)
            else:
                config_dict[key] = value

        return DatabaseConfig(**config_dict)

    def get_connection_string(self, database_name: str) -> str:
        """获取数据库连接字符串"""
        config = self.get_config(database_name)

        if config.type == "postgresql":
            return (
                f"postgresql://{config.user}:{config.password}@"
                f"{config.host}:{config.port}/{config.database}"
            )
        elif config.type == "redis":
            auth = f":{config.password}@' if config.password else '"
            return f"redis://{auth}{config.host}:{config.port}/{config.database}"
        elif config.type == "vector_db":
            return f"http://{config.host}:{config.port}"
        elif config.type == "graph_db":
            return config.uri
        else:
            raise ValueError(f"不支持的数据库类型: {config.type}")

    def get_all_configs(self) -> dict[str, DatabaseConfig]:
        """获取所有数据库配置"""
        configs = {}
        db_configs = self.config.get("databases", {})

        for name, _ in db_configs.items():
            configs[name] = self.get_config(name)

        return configs

    def get_pool_config(self, database_name: str) -> dict[str, Any]:
        """获取连接池配置"""
        config = self.get_config(database_name)
        return config.pool or {}

    def is_readonly(self, database_name: str) -> bool:
        """检查数据库是否为只读"""
        config = self.get_config(database_name)
        return config.readonly or False


# 全局配置加载器实例
_config_loader = None


def get_database_config_loader(config_path: Optional[str] = None) -> DatabaseConfigLoader:
    """获取数据库配置加载器实例"""
    global _config_loader
    if _config_loader is None:
        _config_loader = DatabaseConfigLoader(config_path)
    return _config_loader


# 便捷函数
def get_database_config(database_name: str) -> DatabaseConfig:
    """获取数据库配置"""
    loader = get_database_config_loader()
    return loader.get_config(database_name)


def get_connection_string(database_name: str) -> str:
    """获取数据库连接字符串"""
    loader = get_database_config_loader()
    return loader.get_connection_string(database_name)

