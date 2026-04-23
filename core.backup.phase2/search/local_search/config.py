from __future__ import annotations
"""
本地搜索引擎配置管理
从 config/local_search_engine.json 加载配置
"""

from typing import Optional
import json
import logging
from pathlib import Path
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_DEFAULT_CONFIG_PATH = _PROJECT_ROOT / "config" / "local_search_engine.json"


@dataclass
class LocalSearchConfig:
    """本地搜索引擎配置"""

    # 连接配置
    base_url: str = "http://lse-gateway:3001"  # Docker内网地址
    external_url: str = "http://localhost:3003"  # 宿主机地址
    use_docker_network: bool = False  # 是否使用Docker内网

    # 超时和重试
    timeout: float = 30.0
    connect_timeout: float = 5.0
    max_retries: int = 2

    # 默认搜索参数
    default_max_results: int = 5
    default_language: str = "zh-CN"
    default_categories: str = "general"
    scrape_format: str = "markdown"

    # 健康检查
    health_check_enabled: bool = True
    health_check_interval: int = 30
    health_check_timeout: float = 5.0

    # 功能开关
    enabled: bool = True
    set_as_default_web_engine: bool = True

    def get_connection_url(self) -> str:
        """根据运行环境返回连接地址"""
        return self.base_url if self.use_docker_network else self.external_url

    @classmethod
    def from_file(cls, path: Path | Optional[str] = None) -> "LocalSearchConfig":
        """从JSON配置文件加载"""
        config_path = Path(path) if path else _DEFAULT_CONFIG_PATH

        if not config_path.exists():
            logger.info(f"配置文件不存在，使用默认配置: {config_path}")
            return cls()

        try:
            with open(config_path, encoding="utf-8") as f:
                data = json.load(f)

            connection = data.get("connection", {})
            defaults = data.get("defaults", {})
            health = data.get("health_check", {})
            integration = data.get("integration", {})

            return cls(
                base_url=connection.get("base_url", cls.base_url),
                external_url=connection.get("external_url", cls.external_url),
                use_docker_network=connection.get("use_docker_network", False),
                timeout=connection.get("timeout", cls.timeout),
                connect_timeout=connection.get("connect_timeout", cls.connect_timeout),
                max_retries=connection.get("max_retries", cls.max_retries),
                default_max_results=defaults.get("max_results", cls.default_max_results),
                default_language=defaults.get("language", cls.default_language),
                default_categories=defaults.get("categories", cls.default_categories),
                scrape_format=defaults.get("scrape_format", cls.scrape_format),
                health_check_enabled=health.get("enabled", True),
                health_check_interval=health.get("interval", cls.health_check_interval),
                health_check_timeout=health.get("timeout", cls.health_check_timeout),
                enabled=integration.get("enabled", True),
                set_as_default_web_engine=integration.get(
                    "set_as_default_web_engine", True
                ),
            )
        except Exception as e:
            logger.warning(f"加载配置文件失败，使用默认配置: {e}")
            return cls()
