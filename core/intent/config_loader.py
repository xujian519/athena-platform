"""
意图识别服务 - 配置加载器

负责加载、验证和管理意图识别服务的配置。

Author: Xiaonuo
Created: 2025-01-17
Version: 1.0.0
"""

import os
import re
from pathlib import Path
from typing import Any

import yaml

from core.intent.exceptions import ConfigurationError


class IntentConfig:
    """
    意图识别配置管理器

    提供配置加载、环境变量替换、路径解析等功能。
    """

    def __init__(self, config_path: str | None = None):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径,默认为 config/intent_config.yaml
        """
        if config_path is None:
            # 默认配置文件路径
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "intent_config.yaml"

        self.config_path = Path(config_path)
        self._config: dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """加载配置文件"""
        if not self.config_path.exists():
            raise ConfigurationError(config_key=str(self.config_path), reason="配置文件不存在")

        try:
            with open(self.config_path, encoding="utf-8") as f:
                raw_config = yaml.safe_load(f)

            # 处理空配置文件的情况
            if raw_config is None:
                raw_config = {}

            # 处理环境变量替换
            self._config = self._resolve_env_variables(raw_config)

            # 确保配置是字典类型
            if not isinstance(self._config, dict):
                self._config = {}

        except yaml.YAMLError as e:
            raise ConfigurationError(config_key=str(self.config_path), reason=f"YAML解析失败: {e}")
        except Exception as e:
            raise ConfigurationError(config_key=str(self.config_path), reason=f"加载失败: {e}")

    def _resolve_env_variables(self, config: Any) -> Any:
        """
        递归解析配置中的环境变量

        支持格式: ${VAR_NAME} 或 ${VAR_NAME:-default_value}

        Args:
            config: 配置对象(可能是dict、list或基本类型)

        Returns:
            解析后的配置对象
        """
        if isinstance(config, dict):
            return {key: self._resolve_env_variables(value) for key, value in config.items()}
        elif isinstance(config, list):
            return [self._resolve_env_variables(item) for item in config]
        elif isinstance(config, str):
            return self._substitute_env_var(config)
        else:
            return config

    def _substitute_env_var(self, value: str) -> Any:
        """
        替换字符串中的环境变量引用

        Args:
            value: 包含环境变量引用的字符串

        Returns:
            替换后的值(如果替换结果是数字,返回数字类型)
        """
        # 匹配 ${VAR_NAME} 或 ${VAR_NAME:-default_value}
        pattern = r"\$\{([^}:]+)(?::-([^}]*))?\}"

        def replace_var(match) -> None:
            var_name = match.group(1)
            default_value = match.group(2) if match.group(2) is not None else ""
            return os.environ.get(var_name, default_value)

        result = re.sub(pattern, replace_var, value)

        # 尝试转换为数字类型
        if result.isdigit():
            return int(result)
        try:
            return float(result)
        except ValueError:
            # 尝试转换为布尔值
            if result.lower() == "true":
                return True
            elif result.lower() == "false":
                return False
            # 保持字符串类型
            return result

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置项

        支持点号分隔的路径,如 "models.bge_m3.device"

        Args:
            key_path: 配置键路径(点号分隔)
            default: 默认值

        Returns:
            配置值

        Raises:
            ConfigurationError: 当配置项不存在且没有默认值时
        """
        keys = key_path.split(".")
        value = self._config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                if default is not None:
                    return default
                raise ConfigurationError(config_key=key_path, reason="配置项不存在")

        return value

    def get_model_path(self, model_name: str) -> Path:
        """
        获取模型路径

        Args:
            model_name: 模型名称(如 bge_m3, bert)

        Returns:
            模型路径对象

        Raises:
            ConfigurationError: 当模型配置不存在时
        """
        path_str = self.get(f"models.{model_name}.model_path")
        if not path_str:
            raise ConfigurationError(
                config_key=f"models.{model_name}.model_path", reason="模型路径未配置"
            )

        # 支持相对路径和绝对路径
        path = Path(path_str)
        if not path.is_absolute():
            project_root = Path(self.get("global.project_root"))
            path = project_root / path

        return path

    def get_device(self, model_name: str = "bge_m3") -> str:
        """
        获取模型设备配置

        Args:
            model_name: 模型名称

        Returns:
            设备类型 (cuda, mps, cpu, auto)
        """
        return self.get(f"models.{model_name}.device", "auto")

    def get_cache_dir(self, model_name: str = "bge_m3") -> Path:
        """
        获取模型缓存目录

        Args:
            model_name: 模型名称

        Returns:
            缓存目录路径
        """
        cache_str = self.get(f"models.{model_name}.cache_dir")
        if cache_str:
            path = Path(cache_str)
            if not path.is_absolute():
                project_root = Path(self.get("global.project_root"))
                path = project_root / path
            return path

        # 默认缓存目录
        return Path.home() / ".cache" / "transformers"

    def is_cache_enabled(self) -> bool:
        """检查是否启用缓存"""
        return self.get("global.enable_cache", True)

    def get_log_level(self) -> str:
        """获取日志级别"""
        return self.get("global.log_level", "INFO")

    def get_timeout(self, timeout_type: str = "single_inference") -> float:
        """
        获取超时配置

        Args:
            timeout_type: 超时类型 (single_inference, batch_inference, model_load, total_request)

        Returns:
            超时时间(秒)
        """
        return self.get(f"performance.timeouts.{timeout_type}", 10.0)

    def is_debug_mode(self) -> bool:
        """检查是否启用调试模式"""
        return self.get("development.debug", False)

    def is_testing_mode(self) -> bool:
        """检查是否为测试模式"""
        return self.get("testing.mock_mode", False)

    def to_dict(self) -> dict[str, Any]:
        """返回完整的配置字典"""
        return self._config.copy()

    def reload(self) -> None:
        """重新加载配置文件"""
        self._load_config()


# 全局配置实例(单例)
_config_instance: IntentConfig | None = None


def get_intent_config() -> IntentConfig:
    """
    获取全局配置实例(单例模式)

    Returns:
        IntentConfig实例
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = IntentConfig()
    return _config_instance


def reload_config() -> None:
    """重新加载配置"""
    global _config_instance
    if _config_instance is not None:
        _config_instance.reload()
