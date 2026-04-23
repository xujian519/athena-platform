#!/usr/bin/env python3
from __future__ import annotations
"""
服务自动释放配置管理器
Service Auto-Release Configuration Manager

支持从YAML文件、环境变量和预设加载配置

作者: Athena平台团队
版本: 1.0.0
创建时间: 2026-02-09
"""

import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class AutoReleaseConfig:
    """
    自动释放配置管理器

    支持多层级配置：
    1. 环境变量（最高优先级）
    2. YAML配置文件
    3. 预设配置
    4. 默认值
    """

    # 默认配置
    DEFAULTS = {
        'enabled': True,
        'idle_timeout': 3600,      # 60分钟
        'cleanup_interval': 300,   # 5分钟
    }

    # 环境变量名称
    ENV_VARS = {
        'enabled': 'ATHENA_AUTO_RELEASE_ENABLED',
        'idle_timeout': 'ATHENA_IDLE_TIMEOUT',
        'cleanup_interval': 'ATHENA_CLEANUP_INTERVAL',
        'preset': 'ATHENA_AUTO_RELEASE_PRESET',
    }

    # 预设配置
    PRESETS = {
        'development': {
            'idle_timeout': 600,
            'cleanup_interval': 60,
        },
        'testing': {
            'idle_timeout': 300,
            'cleanup_interval': 30,
        },
        'production': {
            'idle_timeout': 3600,
            'cleanup_interval': 300,
        },
        'long_running': {
            'idle_timeout': 7200,
            'cleanup_interval': 600,
        },
    }

    def __init__(
        self,
        config_file: str | Path | None = None,
        preset: Optional[str] = None
    ):
        """
        初始化配置管理器

        Args:
            config_file: YAML配置文件路径
            preset: 预设配置名称（development/testing/production/long_running）
        """
        self._config: dict[str, Any] = {}
        self._service_configs: dict[str, dict[str, Any]] = {}

        # 加载配置
        self._load_config(config_file, preset)

    def _load_config(
        self,
        config_file: str | Path | None,
        preset: Optional[str]
    ):
        """加载配置"""
        # 1. 从默认值开始
        self._config = self.DEFAULTS.copy()

        # 2. 应用预设配置
        if preset:
            preset_config = self.PRESETS.get(preset)
            if preset_config:
                self._config.update(preset_config)
                logger.info(f"✅ 应用预设配置: {preset}")

        # 3. 从YAML文件加载
        if config_file:
            yaml_config = self._load_yaml_config(config_file)
            if yaml_config:
                self._config.update(yaml_config.get('global', {}))
                self._service_configs = yaml_config.get('services', {})
                logger.info(f"✅ 加载配置文件: {config_file}")

        # 4. 从环境变量加载（最高优先级）
        self._load_env_config()

    def _load_yaml_config(
        self,
        config_file: str | Path
    ) -> Optional[dict[str, Any]]:
        """从YAML文件加载配置"""
        try:
            import yaml
        except ImportError:
            logger.warning("⚠️ PyYAML未安装，无法加载YAML配置文件")
            return None

        config_path = Path(config_file)
        if not config_path.is_absolute():
            # 如果是相对路径，从项目根目录查找
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / config_file

        if not config_path.exists():
            logger.warning(f"⚠️ 配置文件不存在: {config_path}")
            return None

        try:
            with open(config_path, encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"❌ 加载配置文件失败: {e}")
            return None

    def _load_env_config(self):
        """从环境变量加载配置"""
        # 检查预设
        preset_env = os.getenv(self.ENV_VARS['preset'])
        if preset_env and preset_env in self.PRESETS:
            preset_config = self.PRESETS[preset_env]
            self._config.update(preset_config)
            logger.info(f"✅ 应用环境变量预设: {preset_env}")

        # 启用状态
        enabled_env = os.getenv(self.ENV_VARS['enabled'])
        if enabled_env is not None:
            self._config['enabled'] = enabled_env.lower() in ('true', '1', 'yes', 'on')

        # 超时时间
        timeout_env = os.getenv(self.ENV_VARS['idle_timeout'])
        if timeout_env is not None:
            try:
                self._config['idle_timeout'] = int(timeout_env)
            except ValueError:
                logger.warning(f"⚠️ 无效的超时时间: {timeout_env}")

        # 清理间隔
        interval_env = os.getenv(self.ENV_VARS['cleanup_interval'])
        if interval_env is not None:
            try:
                self._config['cleanup_interval'] = int(interval_env)
            except ValueError:
                logger.warning(f"⚠️ 无效的清理间隔: {interval_env}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值
        """
        return self._config.get(key, default)

    def get_service_config(
        self,
        service_name: str,
        key: str,
        default: Any = None
    ) -> Any:
        """
        获取服务特定配置

        Args:
            service_name: 服务名称
            key: 配置键
            default: 默认值

        Returns:
            配置值
        """
        service_config = self._service_configs.get(service_name, {})
        value = service_config.get(key)

        # 如果服务配置中没有该值，使用全局配置
        if value is None:
            return self.get(key, default)

        return value if value is not None else default

    def is_enabled(self) -> bool:
        """检查是否启用自动释放"""
        return self._config.get('enabled', True)

    def get_idle_timeout(self, service_name: Optional[str] = None) -> int:
        """
        获取空闲超时时间

        Args:
            service_name: 服务名称（可选）

        Returns:
            超时时间（秒）
        """
        if service_name:
            service_timeout = self.get_service_config(service_name, 'idle_timeout')
            if service_timeout is not None:
                return service_timeout

        return self._config.get('idle_timeout', self.DEFAULTS['idle_timeout'])

    def get_cleanup_interval(self) -> int:
        """获取清理检查间隔"""
        return self._config.get('cleanup_interval', self.DEFAULTS['cleanup_interval'])

    def should_auto_stop(self, service_name: str) -> bool:
        """
        检查服务是否应该自动停止

        Args:
            service_name: 服务名称

        Returns:
            是否自动停止
        """
        auto_stop = self.get_service_config(service_name, 'auto_stop')
        if auto_stop is not None:
            return auto_stop

        # 默认行为
        return True

    def to_dict(self) -> dict[str, Any]:
        """返回配置字典"""
        return {
            'global': self._config.copy(),
            'services': self._service_configs.copy(),
        }


# =============================================================================
# === 全局实例 ===
# =============================================================================

_global_config: AutoReleaseConfig | None = None


def get_auto_release_config(
    config_file: str | Path | None = None,
    preset: Optional[str] = None,
    reload: bool = False
) -> AutoReleaseConfig:
    """
    获取全局配置实例

    Args:
        config_file: YAML配置文件路径
        preset: 预设配置名称
        reload: 是否重新加载配置

    Returns:
        AutoReleaseConfig 实例
    """
    global _global_config

    if _global_config is None or reload:
        _global_config = AutoReleaseConfig(config_file, preset)

    return _global_config


def load_config_from_env() -> dict[str, Any]:
    """
    从环境变量加载配置（便捷函数）

    环境变量：
    - ATHENA_AUTO_RELEASE_ENABLED: 是否启用（true/false）
    - ATHENA_IDLE_TIMEOUT: 超时时间（秒）
    - ATHENA_CLEANUP_INTERVAL: 清理间隔（秒）
    - ATHENA_AUTO_RELEASE_PRESET: 预设名称

    Returns:
        配置字典
    """
    config = AutoReleaseConfig()
    return {
        'enabled': config.is_enabled(),
        'idle_timeout': config.get_idle_timeout(),
        'cleanup_interval': config.get_cleanup_interval(),
    }


__all__ = [
    "AutoReleaseConfig",
    "get_auto_release_config",
    "load_config_from_env",
]
