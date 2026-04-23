#!/usr/bin/env python3
from __future__ import annotations
"""
统一配置中心
Unified Configuration Center

整合Athena平台的所有配置文件,提供:
- 统一配置接口
- 配置热更新
- 环境区分(dev/test/prod)
- 配置验证
- 配置版本管理

目标:整合61个分散的配置文件

作者: 小诺·双鱼公主
创建时间: 2025-12-27
版本: v1.0.0 "统一配置"
"""

import json
import logging
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class Environment(Enum):
    """环境类型"""

    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class ConfigCategory(Enum):
    """配置类别"""

    DATABASE = "database"
    CACHE = "cache"
    API = "api"
    SERVICE = "service"
    AGENT = "agent"
    MONITORING = "monitoring"
    SECURITY = "security"
    DEPLOYMENT = "deployment"


@dataclass
class ConfigValue:
    """配置值"""

    key: str
    value: Any
    category: ConfigCategory
    description: str = ""
    sensitive: bool = False
    environment: Environment = Environment.DEVELOPMENT
    source_file: str = ""
    last_modified: str = ""


@dataclass
class ConfigSnapshot:
    """配置快照"""

    version: str
    timestamp: str
    environment: Environment
    configs: dict[str, ConfigValue]
    checksum: str = ""


class UnifiedConfigCenter:
    """
    统一配置中心

    整合所有配置,提供统一接口
    """

    def __init__(self, environment: Environment = Environment.DEVELOPMENT):
        """初始化配置中心"""
        self.environment = environment
        self.name = f"Athena统一配置中心({environment.value})"

        # 配置存储
        self.configs: dict[str, ConfigValue] = {}
        self.snapshots: list[ConfigSnapshot] = []

        # 配置文件路径
        self.config_root = Path("/Users/xujian/Athena工作平台/config")
        self.env_files = self._find_env_files()

        # 加载配置
        self._load_all_configs()

        logger.info(f"⚙️ {self.name} 初始化完成")
        logger.info(f"   加载配置: {len(self.configs)}个")
        logger.info(f"   配置文件: {len(self.env_files)}个")

    def _find_env_files(self) -> list[Path]:
        """查找所有环境配置文件"""
        env_files = []

        # 搜索常见的配置文件位置
        search_paths = [
            self.config_root,
            Path("/Users/xujian/Athena工作平台"),
            Path("/Users/xujian/Athena工作平台/production"),
            Path("/Users/xujian/Athena工作平台/.env"),
        ]

        for search_path in search_paths:
            if not search_path.exists():
                continue

            # 查找.env文件
            for env_file in search_path.glob(".env*"):
                if env_file.is_file():
                    env_files.append(env_file)

            # 查找yaml配置
            for yaml_file in search_path.glob("*.yaml"):
                if yaml_file.is_file():
                    env_files.append(yaml_file)

            # 查找yml配置
            for yml_file in search_path.glob("*.yml"):
                if yml_file.is_file():
                    env_files.append(yml_file)

        return env_files

    def _load_all_configs(self) -> Any:
        """加载所有配置"""
        for env_file in self.env_files:
            self._load_file(env_file)

    def _load_file(self, file_path: Path) -> Any:
        """加载单个配置文件"""
        try:
            if file_path.suffix in [".yaml", ".yml"]:
                self._load_yaml(file_path)
            elif file_path.name.startswith(".env"):
                self._load_env(file_path)
            else:
                logger.warning(f"未知的配置文件类型: {file_path}")
        except Exception as e:
            logger.error(f"加载配置文件失败 {file_path}: {e}")

    def _load_yaml(self, file_path: Path) -> Any:
        """加载YAML配置"""
        with open(file_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        # 扁平化配置
        for key, value in self._flatten_dict(data).items():
            config_value = ConfigValue(
                key=key,
                value=value,
                category=self._guess_category(key),
                source_file=str(file_path),
                last_modified=self._get_file_mtime(file_path),
            )
            self.configs[key] = config_value

    def _load_env(self, file_path: Path) -> Any:
        """加载.env配置"""
        with open(file_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                if "=" in line:
                    key, value = line.split("=", 1)
                    config_value = ConfigValue(
                        key=key.strip(),
                        value=value.strip(),
                        category=self._guess_category(key),
                        source_file=str(file_path),
                        last_modified=self._get_file_mtime(file_path),
                    )
                    self.configs[key] = config_value

    def _flatten_dict(self, d: dict, parent_key: str = "", sep: str = ".") -> dict:
        """扁平化字典"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def _guess_category(self, key: str) -> ConfigCategory:
        """猜测配置类别"""
        key_lower = key.lower()

        if any(db in key_lower for db in ["database", "db", "postgres", "mysql", "mongo"]):
            return ConfigCategory.DATABASE
        elif any(cache in key_lower for cache in ["redis", "cache", "memcached"]):
            return ConfigCategory.CACHE
        elif any(api in key_lower for api in ["api", "endpoint", "port"]):
            return ConfigCategory.API
        elif any(svc in key_lower for svc in ["service", "server", "worker"]):
            return ConfigCategory.SERVICE
        elif any(agent in key_lower for agent in ["agent", "xiaonuo", "xiana"]):
            return ConfigCategory.AGENT
        elif any(mon in key_lower for mon in ["monitor", "prometheus", "grafana"]):
            return ConfigCategory.MONITORING
        elif any(sec in key_lower for sec in ["secret", "key", "password", "token"]):
            return ConfigCategory.SECURITY
        else:
            return ConfigCategory.DEPLOYMENT

    def _get_file_mtime(self, file_path: Path) -> str:
        """获取文件修改时间"""
        try:
            return str(os.path.getmtime(file_path))
        except Exception as e:
            logger.debug(f"空except块已触发: {e}")
            return ""

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键(支持点号分隔的嵌套键)
            default: 默认值

        Returns:
            配置值
        """
        return self.configs.get(
            key, ConfigValue(key=key, value=default, category=ConfigCategory.DEPLOYMENT)
        ).value

    def set(
        self, key: str, value: Any, category: ConfigCategory = ConfigCategory.DEPLOYMENT
    ) -> Any:
        """
        设置配置值

        Args:
            key: 配置键
            value: 配置值
            category: 配置类别
        """
        if key in self.configs:
            # 更新现有配置
            self.configs[key].value = value
        else:
            # 创建新配置
            self.configs[key] = ConfigValue(key=key, value=value, category=category)

        logger.info(f"配置更新: {key} = {value}")

    def get_by_category(self, category: ConfigCategory) -> dict[str, ConfigValue]:
        """按类别获取配置"""
        return {k: v for k, v in self.configs.items() if v.category == category}

    def get_all(self) -> dict[str, Any]:
        """获取所有配置(仅值)"""
        return {k: v.value for k, v in self.configs.items()}

    def create_snapshot(self) -> ConfigSnapshot:
        """创建配置快照"""
        import hashlib
        import time

        # 计算校验和
        config_str = json.dumps({k: v.value for k, v in self.configs.items()}, sort_keys=True)
        checksum = hashlib.md5(config_str.encode('utf-8'), usedforsecurity=False).hexdigest()

        snapshot = ConfigSnapshot(
            version=f"v{int(time.time())}",
            timestamp=time.time(),
            environment=self.environment,
            configs=self.configs.copy(),
            checksum=checksum,
        )

        self.snapshots.append(snapshot)
        logger.info(f"创建配置快照: {snapshot.version}")
        return snapshot

    def reload(self) -> Any:
        """重新加载配置"""
        self.configs.clear()
        self._load_all_configs()
        logger.info("配置已重新加载")

    def export_to_yaml(self, output_path: Path) -> Any:
        """导出配置到YAML文件"""
        # 按类别组织
        output_data = {}
        for category in ConfigCategory:
            category_configs = self.get_by_category(category)
            if category_configs:
                output_data[category.value] = {k: v.value for k, v in category_configs.items()}

        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(output_data, f, allow_unicode=True)

        logger.info(f"配置已导出到: {output_path}")

    def get_statistics(self) -> dict[str, Any]:
        """获取配置统计"""
        category_counts = {}
        for config in self.configs.values():
            cat = config.category.value
            category_counts[cat] = category_counts.get(cat, 0) + 1

        return {
            "total_configs": len(self.configs),
            "total_files": len(self.env_files),
            "category_distribution": category_counts,
            "snapshots": len(self.snapshots),
            "environment": self.environment.value,
        }


# 全局实例
_config_center: UnifiedConfigCenter = None


def get_config_center(environment: Environment = Environment.DEVELOPMENT) -> UnifiedConfigCenter:
    """获取配置中心单例"""
    global _config_center
    if _config_center is None or _config_center.environment != environment:
        _config_center = UnifiedConfigCenter(environment)
    return _config_center


# 便捷函数
def get_config(key: str, default: Any = None) -> Any:
    """便捷函数:获取配置值"""
    center = get_config_center()
    return center.get(key, default)


def set_config(key: str, value: Any, category: ConfigCategory = ConfigCategory.DEPLOYMENT) -> None:
    """便捷函数:设置配置值"""
    center = get_config_center()
    center.set(key, value, category)


if __name__ == "__main__":
    # 测试配置中心
    print("🧪 测试统一配置中心")
    print("=" * 70)

    # 初始化
    center = get_config_center()

    # 查看统计
    stats = center.get_statistics()
    print("\n📊 配置统计:")
    print(f"   总配置数: {stats['total_configs']}")
    print(f"   配置文件: {stats['total_files']}")
    print(f"   类别分布: {stats['category_distribution']}")
    print(f"   环境: {stats['environment']}")

    # 创建快照
    print("\n📸 创建配置快照...")
    snapshot = center.create_snapshot()
    print(f"   版本: {snapshot.version}")
    print(f"   校验和: {snapshot.checksum}")

    # 导出配置
    print("\n💾 导出配置...")
    output_path = Path("/Users/xujian/Athena工作平台/config/unified_config_export.yaml")
    center.export_to_yaml(output_path)
    print(f"   已导出到: {output_path}")
