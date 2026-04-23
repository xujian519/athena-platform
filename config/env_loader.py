#!/usr/bin/env python3
"""
环境配置加载器
支持配置继承和环境变量覆盖
"""
from pathlib import Path


def load_env(env_name: str = "development") -> dict[str, str]:
    """
    加载环境配置，支持继承

    Args:
        env_name: 环境名称 (development/test/production)

    Returns:
        环境配置字典

    加载顺序:
        1. 加载.env基础配置
        2. 加载.env.{env_name}环境特定配置
        3. 环境特定配置覆盖基础配置
    """
    base_env = {}
    current_env = {}

    # 1. 加载基础配置
    base_env_file = Path(".env")
    if base_env_file.exists():
        with open(base_env_file) as f:
            for line in f:
                line = line.strip()
                # 跳过注释和空行
                if not line or line.startswith("#"):
                    continue
                # 解析键值对
                if "=" in line:
                    key, value = line.split("=", 1)
                    base_env[key.strip()] = value.strip()

    # 2. 加载环境特定配置
    env_file = Path(f".env.{env_name}")
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                # 跳过注释和空行
                if not line or line.startswith("#"):
                    continue
                # 解析键值对
                if "=" in line:
                    key, value = line.split("=", 1)
                    current_env[key.strip()] = value.strip()

    # 3. 合并配置（环境特定配置覆盖基础配置）
    return {**base_env, **current_env}


def get_env(env_name: str = "development") -> dict[str, str]:
    """
    获取环境配置（便捷函数）

    Args:
        env_name: 环境名称

    Returns:
        环境配置字典
    """
    return load_env(env_name)


def print_env_info(env_name: str = "development") -> None:
    """
    打印环境配置信息

    Args:
        env_name: 环境名称
    """
    config = load_env(env_name)
    print(f"=== 环境配置: {env_name} ===")
    print(f"配置项数量: {len(config)}")
    print("\n主要配置:")
    for key in sorted(config.keys())[:10]:  # 只显示前10个
        # 隐藏密码
        value = config[key]
        if any(keyword in key.upper() for keyword in ["PASSWORD", "SECRET", "KEY"]):
            value = "***HIDDEN***"
        print(f"  {key}={value}")
    if len(config) > 10:
        print(f"  ... 还有 {len(config) - 10} 个配置项")


if __name__ == "__main__":
    import sys

    env = sys.argv[1] if len(sys.argv) > 1 else "development"
    print_env_info(env)
