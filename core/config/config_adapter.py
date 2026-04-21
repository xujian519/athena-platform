"""
配置适配器（兼容旧配置）
Configuration Adapter for Legacy Configuration

提供适配器模式，使旧配置可以无缝迁移到新配置系统
"""
from typing import Dict, Any, Optional
from pathlib import Path
import yaml
from core.config.unified_settings import UnifiedSettings


class ConfigAdapter:
    """配置适配器"""

    @staticmethod
    def adapt_old_database_config(old_config: Dict[str, Any]) -> Dict[str, Any]:
        """适配旧数据库配置到新格式

        Args:
            old_config: 旧配置字典

        Returns:
            新格式配置字典
        """
        new_config = {}

        # 适配DATABASE_URL
        if "DATABASE_URL" in old_config:
            new_config["database_url"] = old_config["DATABASE_URL"]
            # 解析URL提取配置
            # postgresql://user:pass@host:port/db
            import re
            match = re.match(r'postgresql://(\w+):([^@]+)@([^:]+):(\d+)/(\w+)', old_config["DATABASE_URL"])
            if match:
                new_config["database_user"] = match.group(1)
                new_config["database_password"] = match.group(2)
                new_config["database_host"] = match.group(3)
                new_config["database_port"] = int(match.group(4))
                new_config["database_name"] = match.group(5)

        # 适配单独的数据库配置
        if "DB_HOST" in old_config:
            new_config["database_host"] = old_config["DB_HOST"]
        if "DB_PORT" in old_config:
            new_config["database_port"] = old_config["DB_PORT"]
        if "DB_USER" in old_config:
            new_config["database_user"] = old_config["DB_USER"]
        if "DB_PASSWORD" in old_config:
            new_config["database_password"] = old_config["DB_PASSWORD"]
        if "DB_NAME" in old_config:
            new_config["database_name"] = old_config["DB_NAME"]

        return new_config

    @staticmethod
    def adapt_old_redis_config(old_config: Dict[str, Any]) -> Dict[str, Any]:
        """适配旧Redis配置到新格式

        Args:
            old_config: 旧配置字典

        Returns:
            新格式配置字典
        """
        new_config = {}

        # 适配REDIS_URL
        if "REDIS_URL" in old_config:
            new_config["redis_url"] = old_config["REDIS_URL"]
            # 解析URL提取配置
            # redis://[:password]@host:port/db
            import re
            match = re.match(r'redis://(:([^@]+)@)?([^:]+):(\d+)/(\d+)', old_config["REDIS_URL"])
            if match:
                if match.group(2):  # 有密码
                    new_config["redis_password"] = match.group(2)
                new_config["redis_host"] = match.group(3)
                new_config["redis_port"] = int(match.group(4))
                new_config["redis_db"] = int(match.group(5))

        # 适配单独的Redis配置
        if "REDIS_HOST" in old_config:
            new_config["redis_host"] = old_config["REDIS_HOST"]
        if "REDIS_PORT" in old_config:
            new_config["redis_port"] = old_config["REDIS_PORT"]
        if "REDIS_PASSWORD" in old_config:
            new_config["redis_password"] = old_config["REDIS_PASSWORD"]
        if "REDIS_DB" in old_config:
            new_config["redis_db"] = old_config["REDIS_DB"]

        return new_config

    @staticmethod
    def adapt_old_llm_config(old_config: Dict[str, Any]) -> Dict[str, Any]:
        """适配旧LLM配置到新格式

        Args:
            old_config: 旧配置字典

        Returns:
            新格式配置字典
        """
        new_config = {}

        # 适配API密钥
        if "OPENAI_API_KEY" in old_config:
            new_config["llm_default_provider"] = "openai"
            new_config["llm_api_key"] = old_config["OPENAI_API_KEY"]
        elif "ANTHROPIC_API_KEY" in old_config:
            new_config["llm_default_provider"] = "anthropic"
            new_config["llm_api_key"] = old_config["ANTHROPIC_API_KEY"]
        elif "DEEPSEEK_API_KEY" in old_config:
            new_config["llm_default_provider"] = "deepseek"
            new_config["llm_api_key"] = old_config["DEEPSEEK_API_KEY"]

        # 适配模型配置
        if "LLM_MODEL" in old_config:
            new_config["llm_model"] = old_config["LLM_MODEL"]
        if "LLM_TEMPERATURE" in old_config:
            new_config["llm_temperature"] = old_config["LLM_TEMPERATURE"]
        if "LLM_MAX_TOKENS" in old_config:
            new_config["llm_max_tokens"] = old_config["LLM_MAX_TOKENS"]

        return new_config

    @staticmethod
    def load_old_config(config_path: str) -> Dict[str, Any]:
        """加载旧配置文件

        Args:
            config_path: 配置文件路径

        Returns:
            配置字典
        """
        config_file = Path(config_path)
        if not config_file.exists():
            return {}

        # 根据文件扩展名选择加载方式
        if config_file.suffix in [".yml", ".yaml"]:
            with open(config_file) as f:
                return yaml.safe_load(f) or {}
        elif config_file.suffix == ".json":
            import json
            with open(config_file) as f:
                return json.load(f)
        else:
            return {}

    @staticmethod
    def migrate_config(old_config_path: str, config_type: str) -> Dict[str, Any]:
        """迁移旧配置到新格式

        Args:
            old_config_path: 旧配置文件路径
            config_type: 配置类型 (database/redis/llm)

        Returns:
            新格式配置字典
        """
        old_config = ConfigAdapter.load_old_config(old_config_path)

        if config_type == "database":
            return ConfigAdapter.adapt_old_database_config(old_config)
        elif config_type == "redis":
            return ConfigAdapter.adapt_old_redis_config(old_config)
        elif config_type == "llm":
            return ConfigAdapter.adapt_old_llm_config(old_config)
        else:
            return old_config


# 便捷函数
def migrate_database_config(config_path: str) -> Dict[str, Any]:
    """迁移数据库配置"""
    return ConfigAdapter.migrate_config(config_path, "database")


def migrate_redis_config(config_path: str) -> Dict[str, Any]:
    """迁移Redis配置"""
    return ConfigAdapter.migrate_config(config_path, "redis")


def migrate_llm_config(config_path: str) -> Dict[str, Any]:
    """迁移LLM配置"""
    return ConfigAdapter.migrate_config(config_path, "llm")
