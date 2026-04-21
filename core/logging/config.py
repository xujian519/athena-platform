"""
日志配置管理器
Logging Configuration Manager

支持从YAML文件加载日志配置
"""
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from .unified_logger import UnifiedLogger, LogLevel
from .handlers import AsyncLogHandler, RotatingFileHandler, RemoteHandler
from .filters import SensitiveDataFilter


class LoggingConfigLoader:
    """日志配置加载器

    从YAML文件加载日志配置并创建UnifiedLogger实例
    """

    @staticmethod
    def load_from_yaml(config_path: str) -> Dict[str, Any]:
        """从YAML文件加载配置

        Args:
            config_path: 配置文件路径

        Returns:
            配置字典
        """
        config_file = Path(config_path)

        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        return config

    @classmethod
    def create_logger(
        cls,
        service_name: str,
        config_path: Optional[str] = None,
        config_dict: Optional[Dict[str, Any]] = None
    ) -> UnifiedLogger:
        """创建日志记录器

        Args:
            service_name: 服务名称
            config_path: 配置文件路径
            config_dict: 配置字典（优先级高于config_path）

        Returns:
            UnifiedLogger实例
        """
        # 加载配置
        if config_dict:
            config = config_dict
        elif config_path:
            config = cls.load_from_yaml(config_path)
        else:
            # 使用默认配置
            config = cls._get_default_config()

        # 合并服务特定配置
        service_config = config.get("services", {}).get(service_name, {})
        merged_config = cls._merge_config(config.get("default", {}), service_config)

        # 创建logger
        logger = cls._create_logger_from_config(service_name, merged_config)

        return logger

    @staticmethod
    def _merge_config(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """合并配置"""
        merged = base.copy()

        for key, value in override.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = LoggingConfigLoader._merge_config(merged[key], value)
            else:
                merged[key] = value

        return merged

    @staticmethod
    def _create_logger_from_config(service_name: str, config: Dict[str, Any]) -> UnifiedLogger:
        """从配置创建logger

        Args:
            service_name: 服务名称
            config: 配置字典

        Returns:
            UnifiedLogger实例
        """
        # 获取日志级别
        level_str = config.get("level", "INFO")
        level = LogLevel[level_str.upper()]

        # 创建logger
        logger = UnifiedLogger(service_name, level=level)

        # 添加handlers
        handlers_config = config.get("handlers", [])
        for handler_config in handlers_config:
            handler = LoggingConfigLoader._create_handler(handler_config)
            if handler:
                logger.add_handler(handler)

        # 添加filters
        filters_config = config.get("filters", [])
        for filter_config in filters_config:
            filter_obj = LoggingConfigLoader._create_filter(filter_config)
            if filter_obj:
                logger.add_filter(filter_obj)

        return logger

    @staticmethod
    def _create_handler(config: Dict[str, Any]) -> Optional[logging.Handler]:
        """创建handler

        Args:
            config: handler配置

        Returns:
            Handler实例
        """
        handler_type = config.get("type")

        if handler_type == "console":
            # 控制台输出
            formatter = config.get("formatter", "text")
            return logging.StreamHandler()

        elif handler_type == "file":
            # 文件输出
            filename = config.get("filename", "app.log")
            max_bytes = config.get("max_bytes", 10 * 1024 * 1024)
            backup_count = config.get("backup_count", 5)
            compress = config.get("compress", True)

            return RotatingFileHandler(
                filename=filename,
                maxBytes=max_bytes,
                backupCount=backup_count,
                compress=compress
            )

        elif handler_type == "async":
            # 异步handler
            wrapped_handler_config = config.get("handler", {})
            wrapped_handler = LoggingConfigLoader._create_handler(wrapped_handler_config)

            if wrapped_handler:
                capacity = config.get("capacity", 1000)
                return AsyncLogHandler(wrapped_handler, capacity=capacity)

        elif handler_type == "remote":
            # 远程收集
            url = config.get("url")
            if not url:
                return None

            return RemoteHandler(
                url=url,
                batch_size=config.get("batch_size", 10),
                batch_timeout=config.get("batch_timeout", 5.0)
            )

        return None

    @staticmethod
    def _create_filter(config: Dict[str, Any]) -> Optional[logging.Filter]:
        """创建filter

        Args:
            config: filter配置

        Returns:
            Filter实例
        """
        filter_type = config.get("type")

        if filter_type == "sensitive":
            # 敏感信息过滤
            return SensitiveDataFilter(
                mask_char=config.get("mask_char", "*"),
                mask_ratio=config.get("mask_ratio", 0.5)
            )

        return None

    @staticmethod
    def _get_default_config() -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "default": {
                "level": "INFO",
                "handlers": [
                    {
                        "type": "console",
                        "formatter": "text"
                    }
                ],
                "filters": [
                    {
                        "type": "sensitive"
                    }
                ]
            },
            "services": {}
        }
