#!/usr/bin/env python3
from __future__ import annotations
"""
智能响应缓存系统
Intelligent Response Cache System

避免重复的AI模型调用,提升响应速度
"""

import hashlib
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any


class IntelligentCache:
    """智能响应缓存系统"""

    def __init__(self, cache_dir: str | None = None, max_ttl_hours: int = 24, max_items: int = 1000):
        self.cache_dir = (
            Path(cache_dir) if cache_dir else Path(__file__).parent.parent / "cache" / "responses"
        )
        self.max_ttl_hours = max_ttl_hours
        self.max_items = max_items

        # 内存缓存
        self.memory_cache: dict[str, dict[str, Any]] = {}

        # 统计信息
        self.stats = {"hits": 0, "misses": 0, "total_requests": 0, "cache_size": 0}

        self._init_cache()

    def _init_cache(self) -> Any:
        """初始化缓存目录"""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 加载现有缓存索引
        index_file = self.cache_dir / "cache_index.json"
        if index_file.exists():
            try:
                with open(index_file, encoding="utf-8") as f:
                    self.memory_cache = json.load(f)
                self._cleanup_expired()
                print(f"📦 加载了 {len(self.memory_cache)} 个缓存条目")
            except Exception as e:
                print(f"⚠️ 缓存加载失败: {e}")
                self.memory_cache = {}
        else:
            self.memory_cache = {}

    def _generate_key(self, query: str, context: str = "") -> str:
        """生成缓存键"""
        # 简化上下文,只取前500字符
        simplified_context = context[:500] if len(context) > 500 else context

        content = f"{query}|{simplified_context}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _cleanup_expired(self) -> Any:
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = []

        for key, data in self.memory_cache.items():
            if current_time - data.get("timestamp", 0) > self.max_ttl_hours * 3600:
                expired_keys.append(key)

        for key in expired_keys:
            del self.memory_cache[key]

            # 删除磁盘文件
            cache_file = self.cache_dir / f"{key}.json"
            if cache_file.exists():
                cache_file.unlink()

        if expired_keys:
            self._save_index()
            print(f"🗑️ 清理了 {len(expired_keys)} 个过期缓存条目")

    def get(self, query: str, context: str = "") -> str | None:
        """获取缓存的响应"""
        self.stats["total_requests"] += 1

        key = self._generate_key(query, context)

        if key in self.memory_cache:
            data = self.memory_cache[key]

            # 检查是否过期
            if time.time() - data.get("timestamp", 0) <= self.max_ttl_hours * 3600:
                self.stats["hits"] += 1
                print(f"🎯 缓存命中!命中率: {self.get_hit_rate():.1%}")
                return data["response"]
            else:
                # 删除过期条目
                del self.memory_cache[key]
                cache_file = self.cache_dir / f"{key}.json"
                if cache_file.exists():
                    cache_file.unlink()

        self.stats["misses"] += 1
        return None

    def set(self, query: str, response: str, context: str = "") -> Any:
        """设置缓存响应"""
        key = self._generate_key(query, context)

        # 如果缓存已满,删除最旧的条目
        if len(self.memory_cache) >= self.max_items:
            oldest_key = min(
                self.memory_cache.keys(), key=lambda k: self.memory_cache[k].get("timestamp", 0)
            )
            del self.memory_cache[oldest_key]

            # 删除磁盘文件
            cache_file = self.cache_dir / f"{oldest_key}.json"
            if cache_file.exists():
                cache_file.unlink()

        # 保存到内存缓存
        self.memory_cache[key] = {
            "query": query,
            "response": response,
            "context_preview": context[:100] if context else "",
            "timestamp": time.time(),
            "created_at": datetime.now().isoformat(),
        }

        # 保存到磁盘
        cache_file = self.cache_dir / f"{key}.json"
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(self.memory_cache[key], f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 缓存保存失败: {e}")

        # 定期保存索引
        if len(self.memory_cache) % 10 == 0:
            self._save_index()

        self.stats["cache_size"] = len(self.memory_cache)

    def _save_index(self) -> Any:
        """保存缓存索引"""
        index_file = self.cache_dir / "cache_index.json"
        try:
            # 只保存索引信息,不保存完整响应
            index_data = {}
            for key, data in self.memory_cache.items():
                index_data[key] = {
                    "query": data["query"],
                    "context_preview": data.get("context_preview", ""),
                    "timestamp": data["timestamp"],
                    "created_at": data["created_at"],
                }

            with open(index_file, "w", encoding="utf-8") as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 索引保存失败: {e}")

    def get_hit_rate(self) -> float:
        """获取缓存命中率"""
        if self.stats["total_requests"] == 0:
            return 0.0
        return self.stats["hits"] / self.stats["total_requests"]

    def get_stats(self) -> dict[str, Any]:
        """获取缓存统计信息"""
        return {
            **self.stats,
            "hit_rate": self.get_hit_rate(),
            "cache_size_mb": self._get_cache_size_mb(),
        }

    def _get_cache_size_mb(self) -> float:
        """获取缓存大小(MB)"""
        total_size = 0
        for cache_file in self.cache_dir.glob("*.json"):
            total_size += cache_file.stat().st_size
        return total_size / (1024 * 1024)

    def clear_cache(self) -> None:
        """清空缓存"""
        # 清空内存缓存
        self.memory_cache.clear()

        # 删除磁盘文件
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()

        # 重置统计
        self.stats = {"hits": 0, "misses": 0, "total_requests": 0, "cache_size": 0}

        print("🗑️ 缓存已清空")

    def optimize_cache(self) -> Any:
        """优化缓存"""
        print("🔧 开始优化缓存...")

        # 清理过期条目
        self._cleanup_expired()

        # 如果缓存仍然过大,删除最旧的条目
        while len(self.memory_cache) > self.max_items * 0.8:
            oldest_key = min(
                self.memory_cache.keys(), key=lambda k: self.memory_cache[k].get("timestamp", 0)
            )
            del self.memory_cache[oldest_key]

            cache_file = self.cache_dir / f"{oldest_key}.json"
            if cache_file.exists():
                cache_file.unlink()

        self._save_index()
        print(f"✅ 缓存优化完成,当前条目: {len(self.memory_cache)}")


# 全局缓存实例
_intelligent_cache = None


def get_intelligent_cache() -> IntelligentCache:
    """获取全局智能缓存实例"""
    global _intelligent_cache
    if _intelligent_cache is None:
        _intelligent_cache = IntelligentCache()
    return _intelligent_cache


# 使用示例和测试
if __name__ == "__main__":
    # 创建缓存实例
    cache = IntelligentCache()

    # 测试缓存
    test_query = "如何优化AI模型的性能?"
    test_response = "可以通过以下方式优化:1. 使用缓存 2. 优化算法 3. 增加硬件资源"

    # 设置缓存
    cache.set(test_query, test_response, "这是一个关于AI优化的查询")

    # 获取缓存
    cached_response = cache.get(test_query, "这是一个关于AI优化的查询")
    print(f"缓存响应: {cached_response}")

    # 显示统计信息
    stats = cache.get_stats()
    print(f"缓存统计: {json.dumps(stats, ensure_ascii=False, indent=2)}")
