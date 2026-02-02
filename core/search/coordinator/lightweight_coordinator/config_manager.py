#!/usr/bin/env python3
"""
轻量协调器 - 配置管理模块
Lightweight Coordinator - Configuration Management

作者: Athena AI系统
创建时间: 2025-12-05
重构时间: 2026-01-27
版本: 2.0.0
"""

import asyncio
import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any

from .types import ConfigItem, ConfigType

logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理器"""

    def __init__(self):
        """初始化配置管理器"""
        self.configs: dict[str, ConfigItem] = {}
        self.config_subscribers: dict[str, list[Callable[..., Any]]] = {}
        self.stats: dict[str, Any] = {"total_configs": 0, "last_sync_time": None}

    async def set_config(
        self,
        key: str,
        value: Any,
        config_type: ConfigType,
        description: str = "",
        scope: str = "global",
        tool_name: str | None = None,
        sync_callback: Callable[[str, ConfigItem, Any]] | None = None,
    ) -> bool:
        """设置配置

        Args:
            key: 配置键
            value: 配置值
            config_type: 配置类型
            description: 配置描述
            scope: 配置范围
            tool_name: 工具名称
            sync_callback: 同步回调函数

        Returns:
            是否设置成功
        """
        try:
            full_key = f"{scope}:{key}" if scope != "global" else key

            # 创建或更新配置
            config_item = ConfigItem(
                key=key,
                value=value,
                type=config_type,
                description=description,
                scope=scope,
                updated_at=datetime.now(),
            )

            self.configs[full_key] = config_item

            # 通知订阅者
            await self._notify_config_subscribers(full_key, config_item)

            # 同步到工具
            if scope != "global" and tool_name and sync_callback:
                await sync_callback(tool_name, config_item)

            self.stats["total_configs"] = len(self.configs)
            logger.info(f"✅ 配置已设置: {full_key}")

            return True

        except Exception as e:
            logger.error(f"❌ 设置配置失败: {e}")
            return False

    def get_config(self, key: str, scope: str = "global", default: Any = None) -> Any:
        """获取配置

        Args:
            key: 配置键
            scope: 配置范围
            default: 默认值

        Returns:
            配置值
        """
        full_key = f"{scope}:{key}" if scope != "global" else key
        config_item = self.configs.get(full_key)

        if config_item:
            return config_item.value
        return default

    def subscribe_config(
        self, key: str, callback: Callable[..., Any], scope: str = "global"
    ):
        """订阅配置变更

        Args:
            key: 配置键
            callback: 回调函数
            scope: 配置范围
        """
        full_key = f"{scope}:{key}" if scope != "global" else key
        if full_key not in self.config_subscribers:
            self.config_subscribers[full_key] = []
        self.config_subscribers[full_key].append(callback)

    async def sync_all_configs(
        self, sync_callback: Callable[[str, ConfigItem], Any]
    ):
        """同步所有配置到对应工具

        Args:
            sync_callback: 同步回调函数
        """
        try:
            for _full_key, config_item in self.configs.items():
                if config_item.scope != "global":
                    tool_name = config_item.scope
                    await sync_callback(tool_name, config_item)

            self.stats["last_sync_time"] = datetime.now()
            logger.info("✅ 所有配置已同步到工具")

        except Exception as e:
            logger.error(f"❌ 配置同步失败: {e}")

    async def _notify_config_subscribers(self, key: str, config_item: ConfigItem):
        """通知配置订阅者

        Args:
            key: 配置键
            config_item: 配置项
        """
        if key in self.config_subscribers:
            for callback in self.config_subscribers[key]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(config_item)
                    else:
                        callback(config_item)
                except Exception as e:
                    logger.error(f"❌ 通知订阅者失败: {e}")

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息

        Returns:
            统计信息字典
        """
        return self.stats.copy()


__all__ = ["ConfigManager"]
