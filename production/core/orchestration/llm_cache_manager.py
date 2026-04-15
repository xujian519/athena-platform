#!/usr/bin/env python3
"""
LLM调用缓存管理器
LLM Call Cache Manager for Athena Platform

智能缓存LLM响应,减少重复调用,提升性能

作者: 小诺·双鱼座
创建时间: 2025-12-16
"""

from __future__ import annotations
import asyncio
import hashlib
import json
import logging
import pickle
import threading
import time
from collections import OrderedDict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import redis


class CacheStrategy(Enum):
    """缓存策略"""

    EXACT_MATCH = "exact_match"  # 精确匹配
    SEMANTIC_SIMILARITY = "semantic"  # 语义相似
    PATTERN_MATCH = "pattern"  # 模式匹配
    ADAPTIVE = "adaptive"  # 自适应策略


@dataclass
class CacheConfig:
    """缓存配置"""

    # 基础配置
    enabled: bool = True
    strategy: CacheStrategy = CacheStrategy.ADAPTIVE
    max_size: int = 10000  # 最大缓存条目数
    ttl: int = 3600  # 默认过期时间(秒)

    # Redis配置
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_prefix: str = "athena_llm_cache:"

    # 智能缓存配置
    similarity_threshold: float = 0.85  # 语义相似度阈值
    min_response_length: int = 50  # 最小响应长度才缓存
    max_response_length: int = 10000  # 最大响应长度

    # 性能优化配置
    batch_size: int = 100  # 批量处理大小
    cleanup_interval: int = 300  # 清理间隔(秒)
    preload_hot_cache: bool = True  # 预加载热点数据


@dataclass
class CacheEntry:
    """缓存条目"""

    key: str  # 缓存键
    value: str  # LLM响应
    task_type: str  # 任务类型
    model_name: str  # 模型名称
    timestamp: datetime  # 缓存时间
    ttl: int  # 生存时间
    hit_count: int = 0  # 命中次数
    last_hit: datetime = None  # 最后命中时间
    similarity_score: float = 1.0  # 相似度分数
    embedding: list[float] | None = None  # 内容向量(用于语义匹配)
    metadata: dict[str, Any] | None = None  # 元数据


class LLMCacheManager:
    """LLM缓存管理器"""

    def __init__(self, config: CacheConfig | None = None):
        self.name = "LLM缓存管理器"
        self.version = "1.0.0"
        self.logger = logging.getLogger(self.name)

        # 配置
        self.config = config or CacheConfig()

        # 内存缓存
        self.memory_cache = OrderedDict()
        self.cache_lock = threading.RLock()

        # Redis连接
        self.redis_client = None
        if self.config.enabled:
            self._init_redis()

        # 统计信息
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "semantic_matches": 0,
            "cache_size": 0,
            "memory_usage": 0,
            "avg_response_time": 0.0,
        }

        # 热点缓存
        self.hot_patterns = {}

        # 启动后台任务
        if self.config.enabled:
            self._start_background_tasks()

        print(f"🚀 {self.name} 初始化完成 - 策略: {self.config.strategy.value}")

    def _init_redis(self) -> Any:
        """初始化Redis连接"""
        try:
            self.redis_client = redis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                db=self.config.redis_db,
                decode_responses=False,  # 使用bytes以支持pickle
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # 测试连接
            self.redis_client.ping()
            self.logger.info("Redis连接成功")
        except Exception as e:
            self.logger.warning(f"Redis连接失败,使用纯内存缓存: {e}")
            self.redis_client = None

    def _start_background_tasks(self) -> Any:
        """启动后台任务"""
        # 定期清理过期缓存
        asyncio.create_task(self._cleanup_expired_cache())

        # 预加载热点缓存
        if self.config.preload_hot_cache:
            asyncio.create_task(self._preload_hot_cache())

    def generate_cache_key(
        self,
        prompt: str,
        model_name: str,
        task_type: str = "general",
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """生成缓存键"""
        # 标准化prompt
        normalized_prompt = self._normalize_prompt(prompt)

        # 组合关键参数
        key_data = {
            "prompt": normalized_prompt,
            "model": model_name,
            "task_type": task_type,
            "temperature": round(temperature, 2),
            "max_tokens": max_tokens,
        }

        # 生成哈希
        key_str = json.dumps(key_data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(key_str.encode("utf-8")).hexdigest()[:32]

    def _normalize_prompt(self, prompt: str) -> str:
        """标准化prompt"""
        # 移除多余空白
        prompt = " ".join(prompt.split())

        # 转换为小写(对于模式匹配)
        if self.config.strategy == CacheStrategy.PATTERN_MATCH:
            prompt = prompt.lower()

        return prompt

    async def get(
        self,
        prompt: str,
        model_name: str,
        task_type: str = "general",
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str | None:
        """获取缓存响应"""
        if not self.config.enabled:
            return None

        start_time = time.time()
        self.stats["total_requests"] += 1

        try:
            # 1. 精确匹配
            cache_key = self.generate_cache_key(
                prompt, model_name, task_type, temperature, max_tokens
            )
            cached_response = await self._get_exact_match(cache_key)
            if cached_response:
                self.stats["cache_hits"] += 1
                self._update_hit_stats(cache_key)
                return cached_response

            # 2. 语义相似匹配
            if self.config.strategy in [CacheStrategy.SEMANTIC_SIMILARITY, CacheStrategy.ADAPTIVE]:
                similar_response = await self._get_semantic_match(prompt, model_name, task_type)
                if similar_response:
                    self.stats["cache_hits"] += 1
                    self.stats["semantic_matches"] += 1
                    return similar_response

            # 3. 模式匹配
            if self.config.strategy == CacheStrategy.PATTERN_MATCH:
                pattern_response = await self._get_pattern_match(prompt, model_name)
                if pattern_response:
                    self.stats["cache_hits"] += 1
                    return pattern_response

            self.stats["cache_misses"] += 1
            return None

        except Exception as e:
            self.logger.error(f"缓存获取失败: {e}")
            self.stats["cache_misses"] += 1
            return None

        finally:
            # 更新平均响应时间
            response_time = time.time() - start_time
            self.stats["avg_response_time"] = (
                self.stats["avg_response_time"] * (self.stats["total_requests"] - 1) + response_time
            ) / self.stats["total_requests"]

    async def _get_exact_match(self, cache_key: str) -> str | None:
        """精确匹配缓存"""
        # 先查内存缓存
        with self.cache_lock:
            if cache_key in self.memory_cache:
                entry = self.memory_cache[cache_key]
                if not self._is_expired(entry):
                    # 移动到末尾(LRU)
                    self.memory_cache.move_to_end(cache_key)
                    return entry.value
                else:
                    # 删除过期条目
                    del self.memory_cache[cache_key]

        # 查Redis缓存
        if self.redis_client:
            try:
                cached_data = self.redis_client.get(f"{self.config.redis_prefix}{cache_key}")
                if cached_data:
                    entry = pickle.loads(cached_data)
                    if not self._is_expired(entry):
                        # 写入内存缓存
                        with self.cache_lock:
                            self.memory_cache[cache_key] = entry
                        return entry.value
            except Exception as e:
                self.logger.warning(f"Redis读取失败: {e}")

        return None

    async def _get_semantic_match(
        self, prompt: str, model_name: str, task_type: str
    ) -> str | None:
        """语义相似匹配"""
        # 这里可以集成embedding模型进行相似度计算
        # 简化实现:使用文本相似度

        with self.cache_lock:
            for entry in self.memory_cache.values():
                if (
                    entry.model_name == model_name
                    and entry.task_type == task_type
                    and entry.embedding
                ):

                    # 计算相似度(简化版)
                    similarity = self._calculate_text_similarity(prompt, entry.value)
                    if similarity >= self.config.similarity_threshold:
                        return entry.value

        return None

    async def _get_pattern_match(self, prompt: str, model_name: str) -> str | None:
        """模式匹配"""
        prompt_lower = prompt.lower()

        with self.cache_lock:
            for entry in self.memory_cache.values():
                if entry.model_name == model_name:
                    # 检查关键词匹配
                    if self._pattern_match(prompt_lower, entry.key):
                        return entry.value

        return None

    async def set(
        self,
        prompt: str,
        response: str,
        model_name: str,
        task_type: str = "general",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        ttl: int | None = None,
    ) -> bool:
        """设置缓存"""
        if not self.config.enabled:
            return False

        # 检查响应长度
        if len(response) < self.config.min_response_length:
            return False

        if len(response) > self.config.max_response_length:
            return False

        try:
            cache_key = self.generate_cache_key(
                prompt, model_name, task_type, temperature, max_tokens
            )

            # 创建缓存条目
            entry = CacheEntry(
                key=cache_key,
                value=response,
                task_type=task_type,
                model_name=model_name,
                timestamp=datetime.now(),
                ttl=ttl or self.config.ttl,
                embedding=(
                    await self._get_embedding(prompt)
                    if self.config.strategy == CacheStrategy.SEMANTIC_SIMILARITY
                    else None
                ),
                metadata={
                    "prompt_length": len(prompt),
                    "response_length": len(response),
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )

            # 写入内存缓存
            with self.cache_lock:
                # 检查缓存大小
                if len(self.memory_cache) >= self.config.max_size:
                    # 删除最旧的条目
                    self.memory_cache.popitem(last=False)

                self.memory_cache[cache_key] = entry

            # 写入Redis缓存
            if self.redis_client:
                try:
                    self.redis_client.setex(
                        f"{self.config.redis_prefix}{cache_key}", entry.ttl, pickle.dumps(entry)
                    )
                except Exception as e:
                    self.logger.warning(f"Redis写入失败: {e}")

            # 更新统计
            self.stats["cache_size"] = len(self.memory_cache)
            self._update_memory_usage()

            return True

        except Exception as e:
            self.logger.error(f"缓存设置失败: {e}")
            return False

    def _is_expired(self, entry: CacheEntry) -> bool:
        """检查缓存是否过期"""
        return datetime.now() - entry.timestamp > timedelta(seconds=entry.ttl)

    def _update_hit_stats(self, cache_key: str) -> Any:
        """更新命中统计"""
        with self.cache_lock:
            if cache_key in self.memory_cache:
                entry = self.memory_cache[cache_key]
                entry.hit_count += 1
                entry.last_hit = datetime.now()

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度(简化版)"""
        # 实际应用中应使用更精确的算法
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        if not union:
            return 0.0

        return len(intersection) / len(union)

    def _pattern_match(self, prompt: str, pattern: str) -> bool:
        """模式匹配"""
        # 简化的模式匹配
        prompt_words = set(prompt.split())
        pattern_words = set(pattern.split())

        # 至少50%的关键词匹配
        overlap = len(prompt_words.intersection(pattern_words))
        return overlap / len(pattern_words) >= 0.5

    async def _get_embedding(self, text: str) -> list[float]:
        """获取文本向量"""
        # 这里应集成实际的embedding模型
        # 简化实现:返回固定长度的伪向量
        import hashlib

        hash_obj = hashlib.md5(text.encode("utf-8"), usedforsecurity=False)
        return [
            float(int(hash_obj.hexdigest()[i : i + 2], 16)) / 255.0
            for i in range(0, min(64, len(hash_obj.hexdigest())), 2)
        ]

    def _update_memory_usage(self) -> Any:
        """更新内存使用统计"""
        total_size = 0
        with self.cache_lock:
            for entry in self.memory_cache.values():
                total_size += len(pickle.dumps(entry))

        self.stats["memory_usage"] = total_size

    async def _cleanup_expired_cache(self):
        """定期清理过期缓存"""
        while True:
            try:
                await asyncio.sleep(self.config.cleanup_interval)

                expired_keys = []
                with self.cache_lock:
                    for key, entry in self.memory_cache.items():
                        if self._is_expired(entry):
                            expired_keys.append(key)

                    for key in expired_keys:
                        del self.memory_cache[key]

                if expired_keys:
                    self.logger.info(f"清理了 {len(expired_keys)} 个过期缓存")
                    self._update_memory_usage()

            except Exception as e:
                self.logger.error(f"缓存清理失败: {e}")

    async def _preload_hot_cache(self):
        """预加载热点缓存"""
        # 预加载常见的prompt模式
        hot_prompts = [
            ("你好", "greeting"),
            ("请介绍一下", "introduction"),
            ("如何", "how_to"),
            ("什么是", "what_is"),
            ("为什么", "why"),
            ("分析", "analysis"),
            ("总结", "summary"),
        ]

        for _prompt, _task_type in hot_prompts:
            # 可以从历史数据中预加载热点响应
            pass

    def get_cache_statistics(self) -> dict[str, Any]:
        """获取缓存统计信息"""
        total_requests = self.stats["total_requests"]
        hit_rate = (self.stats["cache_hits"] / total_requests * 100) if total_requests > 0 else 0

        return {
            "enabled": self.config.enabled,
            "strategy": self.config.strategy.value,
            "total_requests": total_requests,
            "cache_hits": self.stats["cache_hits"],
            "cache_misses": self.stats["cache_misses"],
            "hit_rate": f"{hit_rate:.2f}%",
            "semantic_matches": self.stats["semantic_matches"],
            "cache_size": self.stats["cache_size"],
            "memory_usage_mb": f"{self.stats['memory_usage'] / 1024 / 1024:.2f}",
            "avg_response_time_ms": f"{self.stats['avg_response_time'] * 1000:.2f}",
        }

    def clear_cache(self, pattern: str | None = None) -> None:
        """清理缓存"""
        if pattern:
            # 清理匹配模式的缓存
            with self.cache_lock:
                keys_to_remove = [k for k in self.memory_cache if pattern in k]
                for key in keys_to_remove:
                    del self.memory_cache[key]
        else:
            # 清理所有缓存
            with self.cache_lock:
                self.memory_cache.clear()

        if self.redis_client:
            try:
                if pattern:
                    keys = self.redis_client.keys(f"{self.config.redis_prefix}*{pattern}*")
                else:
                    keys = self.redis_client.keys(f"{self.config.redis_prefix}*")

                if keys:
                    self.redis_client.delete(*keys)
            except Exception as e:
                self.logger.warning(f"Redis清理失败: {e}")

        self.logger.info(f"缓存已清理: {pattern or '全部'}")

    def export_cache(self, filepath: str) -> Any:
        """导出缓存"""
        try:
            cache_data = {}
            with self.cache_lock:
                for key, entry in self.memory_cache.items():
                    cache_data[key] = asdict(entry)

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2, default=str)

            self.logger.info(f"缓存已导出到: {filepath}")

        except Exception as e:
            self.logger.error(f"缓存导出失败: {e}")

    def import_cache(self, filepath: str) -> Any:
        """导入缓存"""
        try:
            with open(filepath, encoding="utf-8") as f:
                cache_data = json.load(f)

            with self.cache_lock:
                for key, data in cache_data.items():
                    # 重建CacheEntry对象
                    data["timestamp"] = datetime.fromisoformat(data["timestamp"])
                    if data["last_hit"]:
                        data["last_hit"] = datetime.fromisoformat(data["last_hit"])

                    entry = CacheEntry(**data)
                    self.memory_cache[key] = entry

            self.logger.info(f"缓存已从 {filepath} 导入,共 {len(cache_data)} 条")

        except Exception as e:
            self.logger.error(f"缓存导入失败: {e}")


# 导出主类
__all__ = ["CacheConfig", "CacheEntry", "CacheStrategy", "LLMCacheManager"]
