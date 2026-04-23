"""
环境配置加载器
Environment Configuration Loader

支持从YAML文件加载配置，支持继承和覆盖
"""
from typing import Dict, Any, Optional
from pathlib import Path
import yaml
from core.config.settings import Settings


def load_yaml_config(yaml_path: str) -> Dict[str, Any]:
    """加载YAML配置文件

    Args:
        yaml_path: YAML文件路径

    Returns:
        配置字典
    """
    yaml_file = Path(yaml_path)
    if not yaml_file.exists():
        return {}

    with open(yaml_file) as f:
        return yaml.safe_load(f) or {}


def load_base_config() -> Dict[str, Any]:
    """加载基础配置

    Returns:
        基础配置字典
    """
    config = {}
    base_dir = Path("config/base")

    if not base_dir.exists():
        return config

    # 加载所有基础配置文件
    for yaml_file in base_dir.glob("*.yml"):
        file_config = load_yaml_config(str(yaml_file))
        config.update(file_config)

    return config


def load_environment_config(env: str = "development") -> Dict[str, Any]:
    """加载环境特定配置

    Args:
        env: 环境名称 (development/test/production)

    Returns:
        环境配置字典
    """
    env_file = Path(f"config/environments/{env}.yml")
    return load_yaml_config(str(env_file))


def load_service_config(service: str) -> Dict[str, Any]:
    """加载服务特定配置

    Args:
        service: 服务名称 (gateway/xiaona/xiaonuo等)

    Returns:
        服务配置字典
    """
    service_file = Path(f"config/services/{service}.yml")
    return load_yaml_config(str(service_file))


def load_full_config(
    env: str = "development",
    service: Optional[str] = None
) -> Dict[str, Any]:
    """加载完整配置（支持继承）

    配置加载顺序:
    1. base/ (基础配置)
    2. environments/{env}.yml (环境配置)
    3. services/{service}.yml (服务配置，可选)

    Args:
        env: 环境名称
        service: 服务名称（可选）

    Returns:
        完整配置字典
    """
    # 1. 加载基础配置
    config = load_base_config()

    # 2. 加载环境配置（覆盖基础配置）
    env_config = load_environment_config(env)
    config.update(env_config)

    # 3. 加载服务配置（覆盖环境配置）
    if service:
        service_config = load_service_config(service)
        config.update(service_config)

    return config


def create_settings_from_config(
    env: str = "development",
    service: Optional[str] = None
) -> Settings:
    """从YAML配置创建Settings实例

    Args:
        env: 环境名称
        service: 服务名称（可选）

    Returns:
        Settings实例
    """
    config = load_full_config(env, service)
    return Settings.from_yaml_dict(config)


def print_config_info(config: Dict[str, Any]) -> None:
    """打印配置信息（用于调试）

    Args:
        config: 配置字典
    """
    print("=== 配置信息 ===")
    for key, value in config.items():
        if isinstance(value, dict):
            print(f"{key}:")
            for sub_key, sub_value in value.items():
                print(f"  {sub_key}: {sub_value}")
        else:
            print(f"{key}: {value}")


# 便捷函数
def get_settings(
    env: str = "development",
    service: Optional[str] = None
) -> Settings:
    """获取配置实例

    Args:
        env: 环境名称
        service: 服务名称（可选）

    Returns:
        Settings实例
    """
    return create_settings_from_config(env, service)
