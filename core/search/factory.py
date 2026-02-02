"""
搜索引擎工厂
使用工厂模式创建和管理搜索引擎实例
"""

import importlib
import logging
from typing import Any

from .base import BaseSearchEngine

logger = logging.getLogger(__name__)


class SearchEngineFactory:
    """搜索引擎工厂类"""

    _engines: dict[str, type[BaseSearchEngine]] = {}
    _instances: dict[str, BaseSearchEngine] = {}

    @classmethod
    def register_engine(cls, name: str, engine_class: type[BaseSearchEngine]) -> Any:
        """
        注册搜索引擎类

        Args:
            name: 引擎名称
            engine_class: 引擎类
        """
        cls._engines[name] = engine_class

    @classmethod
    def register_from_module(cls, name: str, module_path: str, class_name: str) -> Any:
        """
        从模块动态注册搜索引擎

        Args:
            name: 引擎名称
            module_path: 模块路径
            class_name: 类名
        """
        try:
            module = importlib.import_module(module_path)
            engine_class = getattr(module, class_name)
            cls.register_engine(name, engine_class)
        except Exception as e:
            logger.info(f"Failed to register engine {name}: {e}")

    @classmethod
    def create_engine(
        cls, name: str | None = None, config: dict | None = None, singleton: bool = True
    ) -> BaseSearchEngine:
        """
        创建搜索引擎实例

        Args:
            name: 引擎名称
            config: 配置参数
            singleton: 是否使用单例模式

        Returns:
            搜索引擎实例
        """
        if name not in cls._engines:
            raise ValueError(f"Unknown search engine: {name}")

        # 单例模式
        if singleton:
            if name not in cls._instances:
                engine_class = cls._engines[name]
                cls._instances[name] = engine_class(name, config)
            return cls._instances[name]

        # 每次创建新实例
        engine_class = cls._engines[name]
        return engine_class(name, config)

    @classmethod
    def get_available_engines(cls) -> list:
        """获取所有已注册的引擎名称"""
        return list(cls._engines.keys())

    @classmethod
    def get_engine_info(cls, name: str) -> dict:
        """获取引擎信息"""
        if name not in cls._engines:
            raise ValueError(f"Unknown search engine: {name}")

        engine_class = cls._engines[name]
        return {
            "name": name,
            "class": engine_class.__name__,
            "module": engine_class.__module__,
            "doc": engine_class.__doc__,
        }

    @classmethod
    def clear_instances(cls) -> None:
        """清除所有缓存的实例"""
        cls._instances.clear()


# 自动注册函数
def auto_register_engines() -> Any:
    """自动注册所有搜索引擎"""

    # 注册Web搜索引擎
    try:
        SearchEngineFactory.register_from_module(
            "web", "core.search.external.web_search_engines", "WebSearchEngine"
        )
    except ImportError:
        logger.info("Web search engine module not found")

    # 注册深度搜索引擎
    try:
        SearchEngineFactory.register_from_module(
            "deepsearch", "core.search.deepsearch.deepsearch_integration", "DeepSearchIntegration"
        )
    except ImportError:
        logger.info("Deep search engine module not found")

    # 注册专利搜索引擎
    try:
        SearchEngineFactory.register_from_module(
            "patent", "core.search.patent.patent_search", "PatentSearchEngine"
        )
    except ImportError:
        logger.info("Patent search engine module not found")


# 初始化时自动注册
auto_register_engines()
