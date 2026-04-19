#!/usr/bin/env python3
from __future__ import annotations
"""
提示词模板缓存管理器
Prompt Template Cache Manager

版本: 1.0.0
功能:
- 缓存生成的提示词模板
- 支持变量替换结果的缓存
- LRU缓存策略
- 缓存统计和监控
"""

import hashlib
import json
import logging
import threading
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CachedPrompt:
    """缓存的提示词"""

    system_prompt: str
    user_prompt: str
    scenario_rule_id: str
    created_at: datetime = field(default_factory=datetime.now)
    hit_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)

    def is_expired(self, ttl_seconds: int) -> bool:
        """检查缓存是否过期"""
        age = (datetime.now() - self.created_at).total_seconds()
        return age > ttl_seconds

    def touch(self):
        """更新访问时间和计数"""
        self.hit_count += 1
        self.last_accessed = datetime.now()


class PromptTemplateCache:
    """
    提示词模板缓存管理器

    特性:
    1. 基于内容hash的缓存键生成
    2. LRU缓存淘汰策略
    3. 线程安全
    4. 缓存统计
    """

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600, enable_stats: bool = True):
        """
        初始化缓存管理器

        Args:
            max_size: 最大缓存条目数
            ttl_seconds: 缓存生存时间(秒)
            enable_stats: 是否启用统计
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.enable_stats = enable_stats

        # 线程安全的缓存存储
        self._cache: OrderedDict[str, CachedPrompt] = OrderedDict()
        self._lock = threading.RLock()

        # 统计信息
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "evictions": 0,
            "expirations": 0,
        }

        logger.info(f"✅ 提示词模板缓存初始化完成 (max_size={max_size}, ttl={ttl_seconds}s)")

    def _generate_cache_key(
        self, domain: str, task_type: str, phase: str, variables: dict[str, Any]
    ) -> str:
        """
        生成缓存键

        使用内容hash确保变量值相同时产生相同的key
        """
        # 规范化变量:排序并序列化
        normalized_vars = json.dumps(variables, sort_keys=True, ensure_ascii=False)

        # 组合所有参数
        key_parts = [domain, task_type, phase or "any", normalized_vars]
        key_string = "|".join(key_parts)

        # 生成hash(使用更短的key)
        return hashlib.sha256(key_string.encode("utf-8")).hexdigest()[:32]

    def get(
        self, domain: str, task_type: str, phase: str, variables: dict[str, Any]
    ) -> tuple[str, str | None]:
        """
        从缓存获取提示词

        Args:
            domain: 领域
            task_type: 任务类型
            phase: 阶段
            variables: 变量字典

        Returns:
            (system_prompt, user_prompt) 或 None
        """
        if self.enable_stats:
            self.stats["total_requests"] += 1

        cache_key = self._generate_cache_key(domain, task_type, phase, variables)

        with self._lock:
            if cache_key in self._cache:
                cached = self._cache[cache_key]

                # 检查是否过期
                if cached.is_expired(self.ttl_seconds):
                    del self._cache[cache_key]
                    if self.enable_stats:
                        self.stats["expirations"] += 1
                        self.stats["cache_misses"] += 1
                    logger.debug(f"⚠️ 缓存过期: {cache_key[:16]}...")
                    return None

                # 更新访问信息
                cached.touch()
                # LRU: 移到末尾
                self._cache.move_to_end(cache_key)

                if self.enable_stats:
                    self.stats["cache_hits"] += 1

                logger.debug(f"✅ 缓存命中: {cache_key[:16]}... (hit#{cached.hit_count})")
                return cached.system_prompt, cached.user_prompt

        if self.enable_stats:
            self.stats["cache_misses"] += 1

        logger.debug(f"❌ 缓存未命中: {cache_key[:16]}...")
        return None

    def set(
        self,
        domain: str,
        task_type: str,
        phase: str,
        variables: dict[str, Any],        system_prompt: str,
        user_prompt: str,
        scenario_rule_id: str,
    ):
        """
        设置缓存

        Args:
            domain: 领域
            task_type: 任务类型
            phase: 阶段
            variables: 变量字典
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            scenario_rule_id: 场景规则ID
        """
        cache_key = self._generate_cache_key(domain, task_type, phase, variables)

        with self._lock:
            # 检查缓存大小,执行LRU淘汰
            if len(self._cache) >= self.max_size and cache_key not in self._cache:
                # 移除最旧的条目
                oldest_key, oldest = self._cache.popitem(last=False)
                if self.enable_stats:
                    self.stats["evictions"] += 1
                logger.debug(f"🗑️ LRU淘汰: {oldest_key[:16]}... (hit#{oldest.hit_count})")

            # 创建缓存条目
            cached = CachedPrompt(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                scenario_rule_id=scenario_rule_id,
            )

            self._cache[cache_key] = cached
            # 新条目放到末尾
            self._cache.move_to_end(cache_key)

            logger.debug(f"💾 缓存已保存: {cache_key[:16]}...")

    def invalidate(self, domain: str | None = None, task_type: str | None = None):
        """
        使缓存失效

        Args:
            domain: 领域(None表示清除所有)
            task_type: 任务类型(None表示清除指定领域的所有)
        """
        with self._lock:
            if domain is None:
                # 清除所有
                count = len(self._cache)
                self._cache.clear()
                logger.info(f"🗑️ 清除所有缓存: {count}条")
            else:
                # 选择性清除
                keys_to_remove = []
                for key in self._cache:
                    # 由于key是hash,无法直接匹配,需要重新构建
                    # 这里简化处理:清除所有,实际应用可以改进key结构
                    keys_to_remove.append(key)

                for key in keys_to_remove:
                    del self._cache[key]

                logger.info(
                    f"🗑️ 清除指定缓存: {domain}/{task_type or '*'}: {len(keys_to_remove)}条"
                )

    def cleanup_expired(self) -> int:
        """
        清理过期缓存

        Returns:
            清理的条目数
        """
        with self._lock:
            expired_keys = [
                key for key, cached in self._cache.items() if cached.is_expired(self.ttl_seconds)
            ]

            for key in expired_keys:
                del self._cache[key]
                if self.enable_stats:
                    self.stats["expirations"] += 1

            if expired_keys:
                logger.info(f"🧹 清理过期缓存: {len(expired_keys)}条")

            return len(expired_keys)

    def get_stats(self) -> dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            统计信息字典
        """
        with self._lock:
            if not self.enable_stats:
                return {"stats_enabled": False}

            total_requests = self.stats["total_requests"]
            hit_rate = self.stats["cache_hits"] / total_requests * 100 if total_requests > 0 else 0

            return {
                "stats_enabled": True,
                "total_requests": total_requests,
                "cache_hits": self.stats["cache_hits"],
                "cache_misses": self.stats["cache_misses"],
                "hit_rate": round(hit_rate, 2),
                "evictions": self.stats["evictions"],
                "expirations": self.stats["expirations"],
                "current_size": len(self._cache),
                "max_size": self.max_size,
                "utilization": round(len(self._cache) / self.max_size * 100, 2),
            }

    def clear(self):
        """清空缓存"""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"🗑️ 缓存已清空: {count}条")


# 全局单例
_global_prompt_cache: PromptTemplateCache | None = None
_cache_lock = threading.Lock()


def get_prompt_cache(max_size: int = 1000, ttl_seconds: int = 3600) -> PromptTemplateCache:
    """
    获取全局提示词缓存实例

    Args:
        max_size: 最大缓存大小
        ttl_seconds: 缓存TTL

    Returns:
        PromptTemplateCache实例
    """
    global _global_prompt_cache

    with _cache_lock:
        if _global_prompt_cache is None:
            _global_prompt_cache = PromptTemplateCache(max_size=max_size, ttl_seconds=ttl_seconds)

        return _global_prompt_cache


def reset_prompt_cache():
    """重置全局缓存(用于测试)"""
    global _global_prompt_cache

    with _cache_lock:
        if _global_prompt_cache:
            _global_prompt_cache.clear()
        _global_prompt_cache = None
