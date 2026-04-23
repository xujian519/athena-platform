"""
配置适配器

> 版本: v1.0
> 更新: 2026-04-21
> 说明: 适配旧配置格式到新的统一配置系统

用途:
- 兼容旧的配置访问方式
- 逐步迁移到新的配置系统
- 无缝过渡，不破坏现有代码
"""

from typing import Dict, Any, Optional
from pathlib import Path
import json
import os


class ConfigAdapter:
    """
    配置适配器
    
    将旧的配置格式适配到新的统一配置系统
    """

    @staticmethod
    def adapt_env_file(env_path: str = ".env") -> Dict[str, Any]:
        """
        适配.env文件到新配置格式
        
        参数:
            env_path: .env文件路径
            
        返回:
            配置字典
        """
        config = {}
        
        if not Path(env_path).exists():
            return config
        
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                
                # 跳过注释和空行
                if not line or line.startswith("#"):
                    continue
                
                # 解析KEY=VALUE
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # 适配到新的配置键名
                    new_key = ConfigAdapter._map_old_key_to_new(key)
                    config[new_key] = value
        
        return config

    @staticmethod
    def _map_old_key_to_new(old_key: str) -> str:
        """
        映射旧的配置键到新的配置键
        
        参数:
            old_key: 旧的配置键名
            
        返回:
            新的配置键名
        """
        # 数据库配置映射
        mapping = {
            "DB_HOST": "database_host",
            "DB_PORT": "database_port",
            "DB_USER": "database_user",
            "DB_NAME": "database_name",
            "DB_PASSWORD": "database_password",
            
            # Redis配置
            "REDIS_HOST": "redis_host",
            "REDIS_PORT": "redis_port",
            "REDIS_PASSWORD": "redis_password",
            
            # LLM配置
            "OPENAI_API_KEY": "llm_api_key",
            "ANTHROPIC_API_KEY": "llm_api_key",
            
            # JWT配置
            "JWT_SECRET": "jwt_secret",
            "JWT_SECRET_KEY": "jwt_secret",
            
            # Neo4j配置
            "NEO4J_PASSWORD": "neo4j_password",
        }
        
        return mapping.get(old_key, old_key.lower())

    @staticmethod
    def adapt_service_discovery(
        config_path: str = "config/service_discovery.json"
    ) -> Dict[str, Any]:
        """
        适配服务发现配置
        
        参数:
            config_path: 配置文件路径
            
        返回:
            配置字典
        """
        if not Path(config_path).exists():
            return {}
        
        with open(config_path) as f:
            data = json.load(f)
        
        # 提取API配置
        api_config = data.get("api", {})
        
        return {
            "gateway_host": api_config.get("host", "0.0.0.0"),
            "gateway_port": api_config.get("port", 8005),
            "gateway_cors_enabled": api_config.get("cors_enabled", True),
            "gateway_rate_limiting": api_config.get("rate_limiting", {}),
        }

    @staticmethod
    def adapt_llm_model_registry(
        config_path: str = "config/llm_model_registry.json"
    ) -> Dict[str, Any]:
        """
        适配LLM模型注册表
        
        参数:
            config_path: 配置文件路径
            
        返回:
            配置字典
        """
        if not Path(config_path).exists():
            return {}
        
        with open(config_path) as f:
            data = json.load(f)
        
        # 提取模型信息
        registry = data.get("models", [])
        
        # 按provider分组
        providers = {}
        for model in registry:
            provider = model.get("provider", "unknown")
            if provider not in providers:
                providers[provider] = []
            providers[provider].append(model)
        
        return {
            "llm_providers": list(providers.keys()),
            "llm_models": {model["model_id"]: model for model in registry},
        }

    @staticmethod
    def get_legacy_config(key: str, default: Any = None) -> Any:
        """
        获取旧配置的值（向后兼容）
        
        参数:
            key: 配置键名
            default: 默认值
            
        返回:
            配置值
        """
        # 1. 尝试从环境变量读取
        env_value = os.getenv(key, default)
        if env_value != default:
            return env_value
        
        # 2. 尝试从.env文件读取
        env_path = Path(".env")
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("#") or not line:
                        continue
                    
                    if "=" in line:
                        k, v = line.split("=", 1)
                        if k.strip() == key:
                            return v.strip()
        
        return default

    @staticmethod
    def migrate_to_new_config(
        old_config_paths: list = None,
        output_path: str = "config/environments/development.yml"
    ) -> None:
        """
        迁移旧配置到新配置格式
        
        参数:
            old_config_paths: 旧配置文件路径列表
            output_path: 输出配置文件路径
        """
        if old_config_paths is None:
            old_config_paths = [
                ".env",
                "config/service_discovery.json",
                "config/llm_model_registry.json",
            ]
        
        # 收集所有配置
        new_config = {}
        
        # 适配.env文件
        env_config = ConfigAdapter.adapt_env_file(old_config_paths[0])
        new_config.update(env_config)
        
        # 适配服务发现配置
        if len(old_config_paths) > 1:
            service_config = ConfigAdapter.adapt_service_discovery(old_config_paths[1])
            new_config.update(service_config)
        
        # 适配LLM模型注册表
        if len(old_config_paths) > 2:
            llm_config = ConfigAdapter.adapt_llm_model_registry(old_config_paths[2])
            new_config.update(llm_config)
        
        # 输出到新配置文件
        import yaml
        with open(output_path, "w") as f:
            yaml.dump(new_config, f, default_flow_style=False)
        
        print(f"✅ 配置已迁移到: {output_path}")


# 向后兼容的便捷函数
def get_config(key: str, default: Any = None) -> Any:
    """
    获取配置值（向后兼容）
    
    优先级:
    1. 新的统一配置系统
    2. 旧的环境变量
    3. .env文件
    4. 默认值
    
    参数:
        key: 配置键名
        default: 默认值
        
    返回:
        配置值
    """
    try:
        from core.config.unified_settings import settings
        # 尝试从新配置获取
        if hasattr(settings, key):
            return getattr(settings, key)
    except Exception:
        pass
    
    # 回退到旧配置
    return ConfigAdapter.get_legacy_config(key, default)


__all__ = [
    "ConfigAdapter",
    "get_config",
]
