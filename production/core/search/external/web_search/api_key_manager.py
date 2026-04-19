#!/usr/bin/env python3
"""
联网搜索引擎 - API密钥管理器
Web Search Engines - API Key Manager

管理多个搜索引擎的API密钥轮换和负载均衡

作者: 小娜 & 小诺
创建时间: 2025-12-04
重构时间: 2026-01-26
版本: 2.1.0
"""

from __future__ import annotations
from datetime import datetime
from typing import Any

from core.logging_config import setup_logging
from core.search.external.web_search.types import SearchEngineType

logger = setup_logging()


class APIKeyManager:
    """API密钥管理器 - 实现密钥轮换和负载均衡"""

    def __init__(self, api_keys: dict[str, list[str]]):
        """
        初始化API密钥管理器

        Args:
            api_keys: {engine_type: [api_key1, api_key2, ...]}
        """
        self.api_keys = api_keys
        self.key_indices = dict.fromkeys(api_keys, 0)
        self.key_usage_stats: dict[str, dict[str, int]] = {
            engine: {} for engine in api_keys
        }
        self.key_last_used: dict[str, dict[str, datetime]] = {
            engine: {} for engine in api_keys
        }
        self.key_failure_counts: dict[str, dict[str, int]] = {
            engine: {} for engine in api_keys
        }

    def get_next_key(self, engine_type: SearchEngineType) -> str | None:
        """
        获取下一个可用的API密钥

        Args:
            engine_type: 搜索引擎类型

        Returns:
            API密钥或None
        """
        engine_name = engine_type.value
        if engine_name not in self.api_keys:
            logger.error(f"❌ 未找到搜索引擎 {engine_name} 的API密钥")
            return None

        keys = self.api_keys[engine_name]
        if not keys:
            logger.error(f"❌ 搜索引擎 {engine_name} 没有配置API密钥")
            return None

        # 策略1:选择最少使用的密钥
        best_key = self._select_best_key(engine_name)
        if best_key:
            return best_key

        # 策略2:如果所有密钥都达到限制,返回最近使用的
        return keys[self.key_indices[engine_name]] if keys else None

    def _select_best_key(self, engine_name: str) -> str | None:
        """选择最佳密钥"""
        current_time = datetime.now()
        best_key = None
        min_score = float("inf")

        for i, key in enumerate(self.api_keys[engine_name]):
            # 计算密钥评分(使用次数、失败次数、最后使用时间)
            usage_count = self.key_usage_stats[engine_name].get(key, 0)
            failure_count = self.key_failure_counts[engine_name].get(key, 0)
            last_used = self.key_last_used[engine_name].get(key, datetime.min)

            # 计算时间权重(24小时内的使用次数权重递减)
            hours_since_use = (current_time - last_used).total_seconds() / 3600
            time_weighted_usage = usage_count * max(0.1, 1 - hours_since_use / 24)

            # 综合评分(失败次数有高惩罚)
            score = time_weighted_usage + failure_count * 10

            if score < min_score:
                min_score = score
                best_key = key
                self.key_indices[engine_name] = i

        return best_key

    def record_usage(
        self, engine_type: SearchEngineType, api_key: str, success: bool = True
    ) -> Any:
        """记录API密钥使用情况"""
        engine_name = engine_type.value

        if success:
            self.key_usage_stats[engine_name][api_key] = (
                self.key_usage_stats[engine_name].get(api_key, 0) + 1
            )
            self.key_failure_counts[engine_name][api_key] = max(
                0, self.key_failure_counts[engine_name].get(api_key, 0) - 1
            )
        else:
            self.key_failure_counts[engine_name][api_key] = (
                self.key_failure_counts[engine_name].get(api_key, 0) + 1
            )

        self.key_last_used[engine_name][api_key] = datetime.now()

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        stats: dict[str, Any] = {}
        for engine_name, keys in self.api_keys.items():
            engine_stats = {
                "total_keys": len(keys),
                "usage_stats": self.key_usage_stats.get(engine_name, {}),
                "failure_stats": self.key_failure_counts.get(engine_name, {}),
                "last_used": self.key_last_used.get(engine_name, {}),
            }
            stats[engine_name] = engine_stats
        return stats
