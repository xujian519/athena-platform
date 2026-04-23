"""
环境配置加载器（第2阶段重构版本）
Environment Configuration Loader (Phase 2 Refactored Version)

支持从YAML文件加载配置，支持继承和覆盖
"""
from typing import Dict, Any, Optional
from pathlib import Path
import yaml
from core.config.unified_settings import UnifiedSettings


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
        service_file = Path(f"config/services/{service}.yml")
        service_config = load_yaml_config(str(service_file))
        config.update(service_config)

    return config


def create_unified_settings(
    env: str = "development",
    service: Optional[str] = None
) -> UnifiedSettings:
    """从YAML配置创建UnifiedSettings实例

    Args:
        env: 环境名称
        service: 服务名称（可选）

    Returns:
        UnifiedSettings实例
    """
    config = load_full_config(env, service)
    return UnifiedSettings.from_yaml_dict(config)


# 便捷函数
def get_unified_settings(
    env: str = "development",
    service: Optional[str] = None
) -> UnifiedSettings:
    """获取配置实例

    Args:
        env: 环境名称
        service: 服务名称（可选）

    Returns:
        UnifiedSettings实例
    """
    return create_unified_settings(env, service)
