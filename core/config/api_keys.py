#!/usr/bin/env python3
"""
API密钥管理模块
API Keys Management Module

安全地管理所有外部API密钥,从环境变量加载

作者: Athena AI系统
创建时间: 2025-12-19
版本: 1.0.0
"""

import logging
import os
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


class APIKeyConfig(BaseModel):
    """单个API密钥配置"""

    api_key: str
    enabled: bool = True
    rate_limit: dict[str, int] | None = None
    endpoint: str = ""
    description: str = ""

    @validator("api_key")
    def validate_api_key(self, v) -> None:
        """验证API密钥不为空"""
        if not v or v.strip() == "":
            raise ValueError("API密钥不能为空")
        return v


class SearchAPIKeys(BaseModel):
    """搜索引擎API密钥配置"""

    # Tavily AI搜索引擎
    tavily: list[str] = Field(default_factory=list)

    # Bocha AI搜索引擎
    bocha: list[str] = Field(default_factory=list)

    # Metaso AI搜索引擎
    metaso: list[str] = Field(default_factory=list)

    # Serper搜索引擎
    serper: list[str] = Field(default_factory=list)

    # Bing搜索引擎
    bing_search: list[str] = Field(default_factory=list)

    # DuckDuckGo搜索引擎(通常不需要API密钥)
    duckduckgo: list[str] = Field(default_factory=list)

    # Brave搜索引擎
    brave: list[str] = Field(default_factory=list)

    # Perplexity搜索引擎
    perplexity: list[str] = Field(default_factory=list)

    def get_enabled_engines(self) -> dict[str, list[str]]:
        """获取所有启用的搜索引擎密钥"""
        return {engine: keys for engine, keys in self.dict().items() if keys and len(keys) > 0}

    def get_engine_keys(self, engine: str) -> list[str]:
        """获取指定引擎的API密钥列表"""
        return self.dict().get(engine, [])


class APIKeyManager:
    """API密钥管理器"""

    def __init__(self):
        """初始化API密钥管理器"""
        self._keys: SearchAPIKeys | None = None
        self._load_keys()

    def _load_keys(self) -> Any:
        """从环境变量加载API密钥"""
        try:
            # 从环境变量加载密钥
            self._keys = SearchAPIKeys(
                tavily=self._parse_key_list(os.getenv("TAVILY_API_KEYS", "")),
                bocha=self._parse_key_list(os.getenv("BOCHA_API_KEYS", "")),
                metaso=self._parse_key_list(os.getenv("METASO_API_KEYS", "")),
                serper=self._parse_key_list(os.getenv("SERPER_API_KEYS", "")),
                bing_search=self._parse_key_list(os.getenv("BING_SEARCH_API_KEYS", "")),
                duckduckgo=self._parse_key_list(os.getenv("DUCKDUCKGO_API_KEYS", "")),
                brave=self._parse_key_list(os.getenv("BRAVE_API_KEYS", "")),
                perplexity=self._parse_key_list(os.getenv("PERPLEXITY_API_KEYS", "")),
            )

            # 记录已配置的引擎
            enabled_engines = self._keys.get_enabled_engines()
            if enabled_engines:
                logger.info(f"✅ 已配置的搜索引擎: {list(enabled_engines.keys())}")
                for engine, keys in enabled_engines.items():
                    logger.info(f"   • {engine}: {len(keys)} 个密钥")
            else:
                logger.warning("⚠️ 未配置任何搜索引擎API密钥")

        except Exception as e:
            logger.error(f"❌ 加载API密钥失败: {e}")
            self._keys = SearchAPIKeys()

    def _parse_key_list(self, keys_string: str) -> list[str]:
        """
        解析密钥字符串为列表
        支持逗号、分号或空格分隔的多个密钥
        """
        if not keys_string or keys_string.strip() == "":
            return []

        # 移除空白字符并按分隔符拆分
        keys = []
        for separator in [",", ";", " ", "\n", "\t"]:
            if separator in keys_string:
                keys = [k.strip() for k in keys_string.split(separator) if k.strip()]
                break

        # 如果没有找到分隔符,将整个字符串作为单个密钥
        if not keys and keys_string.strip():
            keys = [keys_string.strip()]

        return keys

    @property
    def keys(self) -> SearchAPIKeys:
        """获取API密钥配置"""
        if self._keys is None:
            self._load_keys()
        return self._keys if self._keys is not None else SearchAPIKeys()

    def get_api_keys_dict(self) -> dict[str, list[str]]:
        """获取API密钥字典(用于兼容旧代码)"""
        return self._keys.get_enabled_engines()

    def reload(self) -> Any:
        """重新加载API密钥(用于配置热重载)"""
        logger.info("🔄 重新加载API密钥...")
        self._load_keys()

    def get_engine_key(self, engine: str, index: int = 0) -> str | None:
        """
        获取指定引擎的特定索引的密钥

        Args:
            engine: 搜索引擎名称
            index: 密钥索引(用于轮换)

        Returns:
            API密钥或None
        """
        keys = self._keys.get_engine_keys(engine)
        if keys and 0 <= index < len(keys):
            return keys[index]
        return None


# 全局单例实例
_api_key_manager: APIKeyManager | None = None


def get_api_key_manager() -> APIKeyManager:
    """获取全局API密钥管理器实例"""
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = APIKeyManager()
    return _api_key_manager


def get_search_api_keys() -> dict[str, list[str]]:
    """便捷函数:获取所有搜索引擎API密钥"""
    return get_api_key_manager().get_api_keys_dict()


# 导出
__all__ = [
    "APIKeyConfig",
    "APIKeyManager",
    "SearchAPIKeys",
    "get_api_key_manager",
    "get_search_api_keys",
]
