#!/usr/bin/env python3
"""
配置迁移脚本
Configuration Migration Script

将旧配置迁移到新的统一配置系统
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config.config_adapter import ConfigAdapter


def migrate_all_configs():
    """迁移所有配置"""
    print("=== 开始配置迁移 ===\n")

    # 1. 迁移数据库配置
    print("1. 迁移数据库配置:")
    db_configs = [
        "config/database_config.yaml",
        "config/database_unified.yaml",
        "config/database.yaml",
    ]

    for config_path in db_configs:
        if Path(config_path).exists():
            try:
                ConfigAdapter.migrate_database_config(config_path)
                print(f"   ✓ {config_path}")
            except Exception as e:
                print(f"   ✗ {config_path}: {e}")

    # 2. 迁移Redis配置
    print("\n2. 迁移Redis配置:")
    redis_configs = [
        "config/redis.yaml",
    ]

    for config_path in redis_configs:
        if Path(config_path).exists():
            try:
                ConfigAdapter.migrate_redis_config(config_path)
                print(f"   ✓ {config_path}")
            except Exception as e:
                print(f"   ✗ {config_path}: {e}")

    # 3. 迁移LLM配置
    print("\n3. 迁移LLM配置:")
    llm_configs = [
        "config/llm_models_env_template.env",
        "config/domestic_llm_config.json",
    ]

    for config_path in llm_configs:
        if Path(config_path).exists():
            try:
                ConfigAdapter.migrate_llm_config(config_path)
                print(f"   ✓ {config_path}")
            except Exception as e:
                print(f"   ✗ {config_path}: {e}")

    print("\n=== 配置迁移完成 ===")
    print("\n提示: 迁移后的配置需要手动验证和调整")


if __name__ == "__main__":
    migrate_all_configs()
