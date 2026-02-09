#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Athena工作平台 - 统一配置管理器
Unified Configuration Manager for Athena Work Platform

功能:
- 统一加载和管理所有配置文件
- 支持环境特定配置覆盖
- 配置验证和类型检查
- 热重载支持
- 配置变更监控
"""

import argparse
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml

logger = logging.getLogger(__name__)


@dataclass
class ConfigSource:
    """配置源定义"""
    name: str
    path: Path
    format: str = 'yaml'  # yaml, json
    required: bool = True
    watch: bool = False


@dataclass
class ConfigManagerConfig:
    """配置管理器配置"""
    config_root: Path = Path('config_new')
    environment: str = 'development'
    auto_reload: bool = False
    validation: bool = True
    backup_config: bool = True


class ConfigManager:
    """统一配置管理器"""

    def __init__(self, config: ConfigManagerConfig | None = None):
        self.config = config or ConfigManagerConfig()
        self.config_root = self.config.config_root
        self.environment = self.config.environment

        # 配置缓存
        self._config_cache: Dict[str, Any] = {}
        self._config_sources: Dict[str, ConfigSource] = {}
        self._last_modified: Dict[str, datetime] = {}

        # 注册配置源
        self._register_config_sources()

        # 加载配置
        self.load_all_configs()

    def _register_config_sources(self) -> Any:
        """注册所有配置源"""
        config_dir = self.config_root

        # 基础配置源
        self._config_sources = {
            # 基础设施配置
            'cache': ConfigSource(
                name='cache',
                path=config_dir / 'infrastructure' / 'cache' / 'redis.yaml'
            ),
            'postgresql': ConfigSource(
                name='postgresql',
                path=config_dir / 'infrastructure' / 'databases' / 'postgresql.yaml'
            ),
            'elasticsearch': ConfigSource(
                name='elasticsearch',
                path=config_dir / 'infrastructure' / 'databases' / 'elasticsearch.yaml'
            ),

            # 服务配置
            'ai_inference': ConfigSource(
                name='ai_inference',
                path=config_dir / 'services' / 'ai' / 'inference_service.yaml'
            ),

            # 环境配置
            'environment': ConfigSource(
                name='environment',
                path=config_dir / 'environments' / self.environment / 'config.yaml',
                required=True
            ),
        }

    def _load_config_file(self, source: ConfigSource) -> Dict[str, Any]:
        """加载单个配置文件"""
        if not source.path.exists():
            if source.required:
                raise FileNotFoundError(f"Required config file not found: {source.path}")
            logger.warning(f"Optional config file not found: {source.path}")
            return {}

        try:
            with open(source.path, 'r', encoding='utf-8') as f:
                if source.format == 'yaml':
                    config = yaml.safe_load(f) or {}
                elif source.format == 'json':
                    config = json.load(f) or {}
                else:
                    raise ValueError(f"Unsupported config format: {source.format}")

            # 记录修改时间
            self._last_modified[source.name] = datetime.fromtimestamp(
                source.path.stat().st_mtime
            )

            logger.info(f"Loaded config from {source.path}")
            return config

        except Exception as e:
            logger.error(f"Failed to load config from {source.path}: {e}")
            if source.required:
                raise
            return {}

    def load_all_configs(self) -> Any | None:
        """加载所有配置文件"""
        logger.info(f"Loading all configs for environment: {self.environment}")

        # 清空缓存
        self._config_cache.clear()

        # 加载所有配置源
        for name, source in self._config_sources.items():
            try:
                self._config_cache[name] = self._load_config_file(source)
            except Exception as e:
                logger.error(f"Failed to load config {name}: {e}")
                if source.required:
                    raise

        # 合并配置
        self._merged_config = self._merge_configs()

        # 验证配置
        if self.config.validation:
            self._validate_config()

        logger.info('All configs loaded successfully')

    def _merge_configs(self) -> Dict[str, Any]:
        """合并所有配置"""
        merged = {}

        # 按优先级合并配置
        # 1. 基础配置
        # 2. 环境特定配置
        # 3. 服务特定配置

        # 加载基础配置
        for name, config in self._config_cache.items():
            if name != 'environment':
                merged[name] = config

        # 环境配置覆盖基础配置
        if 'environment' in self._config_cache:
            env_config = self._config_cache['environment']
            for key, value in env_config.items():
                if isinstance(value, dict) and key in merged:
                    merged[key].update(value)
                else:
                    merged[key] = value

        return merged

    def _validate_config(self) -> Any:
        """验证配置"""
        required_keys = [
            'app.name',
            'app.version',
            'database.host',
            'database.name',
            'redis.host'
        ]

        for key in required_keys:
            if not self.get_value(key):
                raise ValueError(f"Required config key missing: {key}")

        logger.info('Config validation passed')

    def get_value(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点号分隔的嵌套键"""
        keys = key.split('.')
        value = self._merged_config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            # 尝试环境变量
            env_key = '_'.join(keys).upper()
            env_value = os.getenv(env_key)
            if env_value is not None:
                # 尝试转换类型
                if isinstance(default, bool):
                    return env_value.lower() in ('true', '1', 'yes', 'on')
                elif isinstance(default, int):
                    return int(env_value)
                elif isinstance(default, float):
                    return float(env_value)
                return env_value
            return default

    def get_section(self, section: str) -> Dict[str, Any]:
        """获取配置段"""
        return self._merged_config.get(section, {})

    def reload_config(self, source_name: str | None = None) -> Any:
        """重新加载配置"""
        if source_name:
            if source_name in self._config_sources:
                source = self._config_sources[source_name]
                self._config_cache[source_name] = self._load_config_file(source)
                logger.info(f"Reloaded config: {source_name}")
            else:
                logger.error(f"Unknown config source: {source_name}")
        else:
            self.load_all_configs()

    def check_changes(self) -> Dict[str, bool]:
        """检查配置文件变更"""
        changes = {}

        for name, source in self._config_sources.items():
            if source.path.exists():
                current_mtime = datetime.fromtimestamp(source.path.stat().st_mtime)
                last_mtime = self._last_modified.get(name)

                if last_mtime and current_mtime > last_mtime:
                    changes[name] = True
                else:
                    changes[name] = False
            else:
                changes[name] = False

        return changes

    def list_configs(self) -> Dict[str, Dict[str, Any]]:
        """列出所有配置及其状态"""
        configs = {}

        for name, source in self._config_sources.items():
            configs[name] = {
                'path': str(source.path),
                'exists': source.path.exists(),
                'required': source.required,
                'loaded': name in self._config_cache,
                'last_modified': self._last_modified.get(name)
            }

        return configs

    def save_config(self, section: str, config: Dict[str, Any]) -> None:
        """保存配置段"""
        # 暂时不实现配置保存功能
        # 配置应该是只读的，通过版本控制管理
        logger.warning('Config saving is not implemented yet')

    def export_config(self, output_path: Path, format: str = 'yaml') -> Any:
        """导出完整配置"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            if format == 'yaml':
                yaml.dump(self._merged_config, f, default_flow_style=False,
                         allow_unicode=True, indent=2)
            elif format == 'json':
                json.dump(self._merged_config, f, ensure_ascii=False, indent=2)
            else:
                raise ValueError(f"Unsupported format: {format}")

        logger.info(f"Config exported to {output_path}")


def main() -> None:
    """命令行接口"""
    parser = argparse.ArgumentParser(description='Athena配置管理器')
    parser.add_argument('--env', default='development', help='环境名称')
    parser.add_argument('--config-root', default='config_new', help='配置根目录')
    parser.add_argument('--list', action='store_true', help='列出所有配置')
    parser.add_argument('--get', help='获取配置值')
    parser.add_argument('--section', help='获取配置段')
    parser.add_argument('--reload', help='重新加载指定配置')
    parser.add_argument('--check', action='store_true', help='检查配置变更')
    parser.add_argument('--export', help='导出配置到文件')
    parser.add_argument('--format', default='yaml', choices=['yaml', 'json'],
                       help='导出格式')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')

    args = parser.parse_args()

    # 配置日志
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 创建配置管理器
    config_manager = ConfigManager(
        ConfigManagerConfig(
            config_root=Path(args.config_root),
            environment=args.env
        )
    )

    try:
        if args.list:
            configs = config_manager.list_configs()
            logger.info("\n配置文件列表:")
            logger.info(str('-' * 60))
            for name, info in configs.items():
                status = '✓' if info['loaded'] else '✗'
                logger.info(f"{status} {name:20} {info['path']}")

        elif args.get:
            value = config_manager.get_value(args.get)
            logger.info(f"{args.get} = {value}")

        elif args.section:
            section = config_manager.get_section(args.section)
            logger.info(f"\n配置段: {args.section}")
            logger.info(str('-' * 40))
            print(yaml.dump(section, default_flow_style=False, allow_unicode=True))

        elif args.reload:
            config_manager.reload_config(args.reload)
            logger.info(f"已重新加载配置: {args.reload}")

        elif args.check:
            changes = config_manager.check_changes()
            has_changes = any(changes.values())
            if has_changes:
                logger.info("\n检测到配置文件变更:")
                logger.info(str('-' * 40))
                for name, changed in changes.items():
                    if changed:
                        logger.info(f"✓ {name} 已修改")
            else:
                logger.info("\n没有检测到配置文件变更")

        elif args.export:
            config_manager.export_config(Path(args.export), args.format)
            logger.info(f"配置已导出到: {args.export}")

        else:
            parser.print_help()

    except Exception as e:
        logger.error(f"Error: {e}")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())