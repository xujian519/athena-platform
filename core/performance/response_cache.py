from __future__ import annotations
"""
响应缓存机制 - 避免重复AI模型调用
用于提升系统响应速度,减少AI模型调用开销
"""

import contextlib
import hashlib
import json
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any


class ResponseCache:
    """智能响应缓存系统"""

    def __init__(
        self, cache_dir: str | None = None, max_memory_items: int = 1000, max_ttl_hours: int = 24
    ):
        """
        初始化缓存系统

        Args:
            cache_dir: 缓存文件目录
            max_memory_items: 内存中最大缓存项数
            max_ttl_hours: 缓存最大存活时间(小时)
        """
        self.cache_dir = (
            Path(cache_dir)
            if cache_dir
            else Path(__file__).parent.parent.parent / "cache" / "responses"
        )
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 内存缓存
        self.memory_cache: dict[str, dict[str, Any]] = {}
        self.max_memory_items = max_memory_items
        self.max_ttl_seconds = max_ttl_hours * 3600

        # 访问统计
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "memory_hits": 0,
            "disk_hits": 0,
            "evictions": 0,
            "total_requests": 0,
        }

        # 线程锁
        self.cache_lock = threading.RLock()

        # 加载现有缓存索引
        self._load_cache_index()

    def _generate_cache_key(self, prompt: str, context: dict | None = None, model: str = "default") -> str:
        """
        生成缓存键

        Args:
            prompt: 用户输入的prompt
            context: 上下文信息
            model: 使用的模型名称

        Returns:
            缓存键字符串
        """
        # 构建缓存内容
        cache_content = {"prompt": prompt, "context": context or {}, "model": model}

        # 生成hash
        content_str = json.dumps(cache_content, sort_keys=True, ensure_ascii=False)
        hash_key = hashlib.sha256(content_str.encode("utf-8")).hexdigest()

        # 简化hash键(取前16位)
        return f"{model}_{hash_key[:16]}"

    def get(self, prompt: str, context: dict | None = None, model: str = "default") -> Any | None:
        """
        获取缓存响应

        Args:
            prompt: 用户输入的prompt
            context: 上下文信息
            model: 使用的模型名称

        Returns:
            缓存的响应内容,如果没有则返回None
        """
        self.cache_stats["total_requests"] += 1
        cache_key = self._generate_cache_key(prompt, context, model)

        with self.cache_lock:
            # 首先检查内存缓存
            if cache_key in self.memory_cache:
                cache_item = self.memory_cache[cache_key]

                # 检查是否过期
                if self._is_cache_valid(cache_item):
                    cache_item["last_access"] = time.time()
                    cache_item["access_count"] += 1
                    self.cache_stats["hits"] += 1
                    self.cache_stats["memory_hits"] += 1
                    return cache_item["response"]
                else:
                    # 过期,移除
                    del self.memory_cache[cache_key]

            # 检查磁盘缓存
            disk_response = self._get_from_disk(cache_key)
            if disk_response is not None:
                self.cache_stats["hits"] += 1
                self.cache_stats["disk_hits"] += 1

                # 加载到内存缓存
                self._add_to_memory(cache_key, disk_response)
                return disk_response

            # 缓存未命中
            self.cache_stats["misses"] += 1
            return None

    def set(
        self,
        prompt: str,
        response: Any,
        context: dict | None = None,
        model: str = "default",
        ttl_hours: int | None = None,
        metadata: dict | None = None,
    ) -> None:
        """
        设置缓存响应

        Args:
            prompt: 用户输入的prompt
            response: 响应内容
            context: 上下文信息
            model: 使用的模型名称
            ttl_hours: 自定义TTL(小时)
            metadata: 额外的元数据
        """
        cache_key = self._generate_cache_key(prompt, context, model)

        with self.cache_lock:
            # 添加到内存缓存
            self._add_to_memory(cache_key, response, ttl_hours, metadata)

            # 异步保存到磁盘
            self._save_to_disk(cache_key, response, ttl_hours, metadata)

    def _add_to_memory(
        self, cache_key: str, response: Any, ttl_hours: int | None = None, metadata: dict | None = None
    ) -> None:
        """添加到内存缓存"""
        # 检查是否需要清理
        if len(self.memory_cache) >= self.max_memory_items:
            self._evict_oldest()

        # 计算过期时间
        ttl = ttl_hours * 3600 if ttl_hours else self.max_ttl_seconds
        expire_time = time.time() + ttl

        # 添加到内存
        cache_item = {
            "response": response,
            "created_at": time.time(),
            "expire_at": expire_time,
            "last_access": time.time(),
            "access_count": 1,
            "metadata": metadata or {},
            "ttl_hours": ttl_hours or (self.max_ttl_seconds // 3600),
        }

        self.memory_cache[cache_key] = cache_item

    def _evict_oldest(self) -> None:
        """清理最旧的缓存项"""
        if not self.memory_cache:
            return

        # 按最后访问时间排序,移除最旧的20%
        sorted_items = sorted(self.memory_cache.items(), key=lambda x: x[1]["last_access"])

        evict_count = max(1, len(sorted_items) // 5)
        for i in range(evict_count):
            cache_key = sorted_items[i][0]
            del self.memory_cache[cache_key]
            self.cache_stats["evictions"] += 1

    def _is_cache_valid(self, cache_item: dict) -> bool:
        """检查缓存是否有效"""
        return time.time() < cache_item["expire_at"]

    def _get_from_disk(self, cache_key: str) -> Any | None:
        """从磁盘获取缓存"""
        cache_file = self.cache_dir / f"{cache_key}.json"

        try:
            if not cache_file.exists():
                return None

            with open(cache_file, encoding="utf-8") as f:
                cache_data = json.load(f)

            # 检查是否过期
            expire_time = cache_data.get("expire_at", 0)
            if time.time() > expire_time:
                # 删除过期文件
                cache_file.unlink(missing_ok=True)
                return None

            return cache_data["response"]

        except Exception as e:
            print(f"从磁盘读取缓存失败 {cache_key}: {e}")
            return None

    def _save_to_disk(
        self, cache_key: str, response: Any, ttl_hours: int | None = None, metadata: dict | None = None
    ) -> None:
        """保存到磁盘"""
        cache_file = self.cache_dir / f"{cache_key}.json"

        try:
            ttl = ttl_hours * 3600 if ttl_hours else self.max_ttl_seconds
            expire_time = time.time() + ttl

            cache_data = {
                "response": response,
                "created_at": time.time(),
                "expire_at": expire_time,
                "metadata": metadata or {},
                "ttl_hours": ttl_hours or (self.max_ttl_seconds // 3600),
                "cache_key": cache_key,
            }

            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"保存缓存到磁盘失败 {cache_key}: {e}")

    def _load_cache_index(self) -> None:
        """加载缓存索引"""
        try:
            index_file = self.cache_dir / "cache_index.json"
            if index_file.exists():
                with open(index_file, encoding="utf-8") as f:
                    index_data = json.load(f)
                    self.cache_stats.update(index_data.get("stats", {}))
        except Exception as e:
            print(f"加载缓存索引失败: {e}")

    def _save_cache_index(self) -> None:
        """保存缓存索引"""
        try:
            index_file = self.cache_dir / "cache_index.json"
            index_data = {
                "stats": self.cache_stats,
                "memory_cache_size": len(self.memory_cache),
                "last_updated": datetime.now().isoformat(),
            }

            with open(index_file, "w", encoding="utf-8") as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存缓存索引失败: {e}")

    def cleanup_expired(self) -> int:
        """清理过期缓存"""
        cleaned_count = 0

        # 清理内存缓存
        with self.cache_lock:
            expired_keys = []
            for key, item in self.memory_cache.items():
                if not self._is_cache_valid(item):
                    expired_keys.append(key)

            for key in expired_keys:
                del self.memory_cache[key]
                cleaned_count += 1

        # 清理磁盘缓存
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                if cache_file.name == "cache_index.json":
                    continue

                with open(cache_file, encoding="utf-8") as f:
                    cache_data = json.load(f)

                expire_time = cache_data.get("expire_at", 0)
                if time.time() > expire_time:
                    cache_file.unlink(missing_ok=True)
                    cleaned_count += 1
        except Exception as e:
            print(f"清理磁盘缓存失败: {e}")

        return cleaned_count

    def get_stats(self) -> dict:
        """获取缓存统计信息"""
        with self.cache_lock:
            hit_rate = 0
            if self.cache_stats["total_requests"] > 0:
                hit_rate = (self.cache_stats["hits"] / self.cache_stats["total_requests"]) * 100

            stats = {
                "cache_stats": self.cache_stats.copy(),
                "hit_rate": f"{hit_rate:.2f}%",
                "memory_cache_size": len(self.memory_cache),
                "max_memory_items": self.max_memory_items,
                "cache_directory": str(self.cache_dir),
                "memory_hit_rate": 0,
                "disk_hit_rate": 0,
            }

            if self.cache_stats["hits"] > 0:
                stats["memory_hit_rate"] = (
                    self.cache_stats["memory_hits"] / self.cache_stats["hits"]
                ) * 100
                stats["disk_hit_rate"] = (
                    self.cache_stats["disk_hits"] / self.cache_stats["hits"]
                ) * 100

            return stats

    def clear(self) -> None:
        """清空所有缓存"""
        with self.cache_lock:
            self.memory_cache.clear()

        # 清空磁盘缓存
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink(missing_ok=True)
        except Exception as e:
            print(f"清空磁盘缓存失败: {e}")

    def __del__(self):
        """析构函数,保存缓存索引"""
        with contextlib.suppress(json.JSONDecodeError, TypeError, ValueError):
            self._save_cache_index()


# 全局缓存实例
_global_cache: ResponseCache | None = None


def get_cache() -> ResponseCache:
    """获取全局缓存实例"""
    global _global_cache
    if _global_cache is None:
        _global_cache = ResponseCache()
    return _global_cache


# 装饰器:自动缓存函数结果
def cached_response(ttl_hours: int = 24, cache_key_func: callable | None = None, use_context: bool = True):
    """
    响应缓存装饰器

    Args:
        ttl_hours: 缓存存活时间(小时)
        cache_key_func: 自定义缓存键生成函数
        use_context: 是否使用上下文信息
    """

    def decorator(func) -> None:
        def wrapper(*args, **kwargs) -> Any:
            cache = get_cache()

            # 提取prompt和context
            prompt = kwargs.get("prompt", "") or (args[0] if args else "")
            context = kwargs.get("context") if use_context else None
            model = kwargs.get("model", "default")

            # 尝试从缓存获取
            cached_result = cache.get(prompt, context, model)
            if cached_result is not None:
                return cached_result

            # 执行原函数
            result = func(*args, **kwargs)

            # 缓存结果
            cache.set(prompt, result, context, model, ttl_hours)

            return result

        wrapper._cached = True
        wrapper._cache_decorator = cached_response
        return wrapper

    return decorator


# 示例使用
if __name__ == "__main__":
    # 创建缓存实例
    cache = ResponseCache()

    # 测试缓存
    prompt = "什么是专利申请?"

    # 第一次调用(缓存未命中)
    result1 = cache.get(prompt)
    print(f"第一次调用结果: {result1}")  # None

    # 设置缓存
    cache.set(prompt, "专利申请是指向专利局提交专利申请的行为...")

    # 第二次调用(缓存命中)
    result2 = cache.get(prompt)
    print(f"第二次调用结果: {result2}")  # 返回缓存的内容

    # 查看统计信息
    stats = cache.get_stats()
    print(f"缓存统计: {stats}")
