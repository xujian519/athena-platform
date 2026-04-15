"""
统一LLM层 - 语义响应缓存系统
使用语义相似度匹配缓存查询,减少重复API调用

作者: Claude Code
日期: 2026-01-23
"""

from __future__ import annotations
import hashlib
import logging
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class CacheStrategy(Enum):
    """缓存策略"""

    EXACT = "exact"  # 精确匹配
    SEMANTIC = "semantic"  # 语义相似度匹配
    HYBRID = "hybrid"  # 混合策略


@dataclass
class CacheEntry:
    """缓存条目"""

    key: str  # 缓存键
    message: str  # 原始消息
    task_type: str  # 任务类型
    response_content: str  # 响应内容
    model_used: str  # 使用的模型
    tokens_used: int  # 使用tokens
    cost: float  # 成本
    timestamp: float  # 创建时间戳
    ttl: int  # 生存时间(秒)
    hit_count: int = 0  # 命中次数
    similarity_threshold: float = 0.85  # 相似度阈值

    def is_expired(self) -> bool:
        """检查是否过期"""
        return time.time() - self.timestamp > self.ttl

    def get_similarity(self, other_message: str) -> float:
        """
        计算与另一个消息的相似度

        Args:
            other_message: 另一个消息

        Returns:
            float: 相似度分数 (0-1)
        """
        # 简单的基于关键词的相似度计算
        # 生产环境可以使用嵌入向量进行语义相似度计算
        words1 = set(self.message.lower().split())
        words2 = set(other_message.lower().split())

        if not words1 or not words2:
            return 0.0

        # Jaccard相似度
        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0


class ResponseCache:
    """
    响应缓存系统

    功能:
    1. 存储LLM响应
    2. 语义相似度匹配
    3. TTL过期管理
    4. 缓存统计
    """

    def __init__(
        self,
        max_entries: int = 1000,
        default_ttl: int = 3600,
        strategy: CacheStrategy = CacheStrategy.SEMANTIC,
        similarity_threshold: float = 0.85,
    ):
        """
        初始化缓存系统

        Args:
            max_entries: 最大缓存条目数
            default_ttl: 默认TTL(秒)
            strategy: 缓存策略
            similarity_threshold: 语义相似度阈值
        """
        self.max_entries = max_entries
        self.default_ttl = default_ttl
        self.strategy = strategy
        self.similarity_threshold = similarity_threshold

        # 缓存存储
        self.cache: dict[str, CacheEntry] = {}

        # 统计信息
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_saved_tokens": 0,
            "total_saved_cost": 0.0,
            "hit_rate": 0.0,
        }

        # 任务类型配置(哪些任务类型可以缓存)
        self.cacheable_tasks = {"simple_qa", "general_chat", "patent_search", "simple_chat"}

        # 锁保护:保护所有缓存操作
        self._lock = threading.RLock()  # 使用可重入锁,允许同一线程多次获取

        logger.info(
            f"✅ 响应缓存初始化完成 "
            f"(策略: {strategy.value}, "
            f"TTL: {default_ttl}s, "
            f"最大条目: {max_entries}, "
            f"线程安全: 已启用)"
        )

    def _generate_key(self, message: str, task_type: str) -> str:
        """
        生成缓存键

        Args:
            message: 消息内容
            task_type: 任务类型

        Returns:
            str: 缓存键
        """
        # 使用MD5哈希生成唯一键
        content = f"{task_type}:{message}"
        return hashlib.md5(content.encode('utf-8'), usedforsecurity=False).hexdigest()

    def get(
        self, message: str, task_type: str, model_id: str | None = None
    ) -> CacheEntry | None:
        """
        获取缓存的响应(线程安全)

        Args:
            message: 消息内容
            task_type: 任务类型
            model_id: 模型ID(可选)

        Returns:
            Optional[CacheEntry]: 缓存条目,如果未找到返回None
        """
        with self._lock:
            self.stats["total_requests"] += 1

            # 检查任务类型是否可缓存
            if task_type not in self.cacheable_tasks:
                self.stats["cache_misses"] += 1
                return None

            # 清理过期条目
            self._cleanup_expired()

            # 根据策略查找缓存
            if self.strategy == CacheStrategy.EXACT:
                entry = self._get_exact(message, task_type)
            elif self.strategy == CacheStrategy.SEMANTIC:
                entry = self._get_semantic(message, task_type)
            else:  # HYBRID
                entry = self._get_exact(message, task_type)
                if entry is None:
                    entry = self._get_semantic(message, task_type)

            if entry:
                self.stats["cache_hits"] += 1
                entry.hit_count += 1
                self._update_stats()
                logger.debug(
                    f"💾 缓存命中: {task_type} (相似度: {entry.get_similarity(message):.2f})"
                )
            else:
                self.stats["cache_misses"] += 1
                logger.debug(f"💔 缓存未命中: {task_type}")

            return entry

    def _get_exact(self, message: str, task_type: str) -> CacheEntry | None:
        """精确匹配"""
        key = self._generate_key(message, task_type)
        entry = self.cache.get(key)
        if entry and not entry.is_expired():
            return entry
        return None

    def _get_semantic(self, message: str, task_type: str) -> CacheEntry | None:
        """语义相似度匹配"""
        best_entry = None
        best_similarity = 0.0

        for entry in self.cache.values():
            # 跳过不同任务类型的条目
            if entry.task_type != task_type:
                continue

            # 跳过过期条目
            if entry.is_expired():
                continue

            # 计算相似度
            similarity = entry.get_similarity(message)

            if similarity >= self.similarity_threshold and similarity > best_similarity:
                best_entry = entry
                best_similarity = similarity

        return best_entry

    def set(
        self,
        message: str,
        task_type: str,
        response_content: str,
        model_used: str,
        tokens_used: int,
        cost: float,
        ttl: int | None = None,
    ) -> None:
        """
        设置缓存(线程安全)

        Args:
            message: 消息内容
            task_type: 任务类型
            response_content: 响应内容
            model_used: 使用的模型
            tokens_used: 使用tokens
            cost: 成本
            ttl: 生存时间(可选)
        """
        with self._lock:
            # 检查任务类型是否可缓存
            if task_type not in self.cacheable_tasks:
                return

            # 生成缓存键
            key = self._generate_key(message, task_type)

            # 检查缓存大小
            if len(self.cache) >= self.max_entries:
                self._evict_lru()

            # 创建缓存条目
            entry = CacheEntry(
                key=key,
                message=message,
                task_type=task_type,
                response_content=response_content,
                model_used=model_used,
                tokens_used=tokens_used,
                cost=cost,
                timestamp=time.time(),
                ttl=ttl or self.default_ttl,
                similarity_threshold=self.similarity_threshold,
            )

            self.cache[key] = entry
            logger.debug(f"💾 缓存已添加: {task_type} (TTL: {entry.ttl}s)")

    def _cleanup_expired(self) -> None:
        """清理过期条目"""
        expired_keys = [key for key, entry in self.cache.items() if entry.is_expired()]
        for key in expired_keys:
            del self.cache[key]

        if expired_keys:
            logger.debug(f"🧹 清理了 {len(expired_keys)} 个过期缓存条目")

    def _evict_lru(self) -> None:
        """驱逐最少使用的条目(LRU)"""
        if not self.cache:
            return

        # 找到最少使用的条目
        lru_key = min(
            self.cache.keys(), key=lambda k: (self.cache[k].hit_count, self.cache[k].timestamp)
        )

        del self.cache[lru_key]
        logger.debug(f"🗑️ 驱逐LRU缓存条目: {lru_key}")

    def _update_stats(self) -> None:
        """更新统计信息"""
        total = self.stats["total_requests"]
        if total > 0:
            self.stats["hit_rate"] = self.stats["cache_hits"] / total

    def get_stats(self) -> dict[str, Any]:
        """
        获取统计信息

        Returns:
            Dict: 统计信息
        """
        # 计算节省的成本和tokens
        saved_tokens = sum(entry.tokens_used * entry.hit_count for entry in self.cache.values())
        saved_cost = sum(entry.cost * entry.hit_count for entry in self.cache.values())

        self.stats["total_saved_tokens"] = saved_tokens
        self.stats["total_saved_cost"] = saved_cost

        return {
            **self.stats,
            "cache_size": len(self.cache),
            "max_entries": self.max_entries,
            "strategy": self.strategy.value,
            "similarity_threshold": self.similarity_threshold,
        }

    def get_report(self) -> str:
        """
        生成缓存报告

        Returns:
            str: 格式化的缓存报告
        """
        stats = self.get_stats()

        lines = [
            "=" * 80,
            "响应缓存报告",
            "=" * 80,
            "",
            "[概览]",
            f"  总请求数: {stats['total_requests']}",
            f"  缓存命中: {stats['cache_hits']}",
            f"  缓存未命中: {stats['cache_misses']}",
            f"  命中率: {stats['hit_rate']*100:.1f}%",
            "",
            "[缓存状态]",
            f"  当前大小: {stats['cache_size']}/{stats['max_entries']}",
            f"  策略: {stats['strategy']}",
            f"  相似度阈值: {stats['similarity_threshold']}",
            "",
            "[节省统计]",
            f"  节省Tokens: {stats['total_saved_tokens']:,}",
            f"  节省成本: ¥{stats['total_saved_cost']:.4f}",
            "",
            "[任务类型分布]",
        ]

        # 按任务类型统计
        task_counts: dict[str, int] = {}
        for entry in self.cache.values():
            task_counts[entry.task_type] = task_counts.get(entry.task_type, 0) + 1

        for task_type, count in sorted(task_counts.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  {task_type}: {count}条目")

        lines.extend(["", "=" * 80])

        return "\n".join(lines)

    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()
        logger.info("🧹 缓存已清空")

    def configure_task_type(
        self, task_type: str, cacheable: bool, ttl: int | None = None
    ) -> None:
        """
        配置任务类型的缓存设置

        Args:
            task_type: 任务类型
            cacheable: 是否可缓存
            ttl: TTL(可选)
        """
        if cacheable:
            self.cacheable_tasks.add(task_type)
            logger.info(f"✅ 任务类型 {task_type} 已启用缓存")
        else:
            self.cacheable_tasks.discard(task_type)
            logger.info(f"❌ 任务类型 {task_type} 已禁用缓存")


# 单例
_response_cache: ResponseCache | None = None
_response_cache_lock = threading.Lock()


def get_response_cache() -> ResponseCache:
    """
    获取响应缓存单例(线程安全)

    Returns:
        ResponseCache: 响应缓存实例
    """
    global _response_cache
    if _response_cache is None:
        with _response_cache_lock:
            # 双重检查锁定
            if _response_cache is None:
                _response_cache = ResponseCache()
    return _response_cache


def reset_response_cache():
    """重置单例(用于测试,线程安全)"""
    global _response_cache
    with _response_cache_lock:
        _response_cache = None
