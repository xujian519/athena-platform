#!/usr/bin/env python3
"""
三级模型缓存系统
L1内存 + L2Redis + L3磁盘
实现<1ms缓存命中延迟

作者: Athena AI
创建时间: 2025-12-29
版本: v1.0.0
"""

from __future__ import annotations
import hashlib
import json
import logging
import pickle
from collections import OrderedDict
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

class L1MemoryCache:
    """L1内存缓存 - 最快速度 (<1ms)

    特性:
    - LRU淘汰策略
    - 容量限制
    - 命中率统计
    """

    def __init__(self, max_size_mb: int = 500):
        """
        初始化L1缓存

        Args:
            max_size_mb: 最大缓存大小(MB)
        """
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.cache: OrderedDict = OrderedDict()
        self.current_size = 0
        self.hits = 0
        self.misses = 0

    def _get_key(self, model_name: str, text: str) -> str:
        """生成缓存键"""
        content = f"{model_name}:{text}"
        return hashlib.sha256(content.encode()).hexdigest()

    def _estimate_size(self, value: Any) -> int:
        """估算值大小(字节)"""
        try:
            import numpy as np
            if isinstance(value, np.ndarray):
                return value.nbytes
        except ImportError:
            pass

        if isinstance(value, (list, tuple)):
            return len(json.dumps(value).encode())
        elif isinstance(value, dict):
            return len(json.dumps(value).encode())
        elif isinstance(value, str):
            return len(value.encode())
        else:
            # pickle大小估算
            return len(pickle.dumps(value))

    def get(self, model_name: str, text: str) -> Any | None:
        """获取缓存值"""
        key = self._get_key(model_name, text)

        if key in self.cache:
            # LRU: 移到末尾
            value = self.cache.pop(key)
            self.cache[key] = value

            self.hits += 1
            logger.debug(f"L1缓存命中: {model_name}")
            return value

        self.misses += 1
        return None

    def set(self, model_name: str, text: str, value: Any):
        """设置缓存值"""
        key = self._get_key(model_name, text)
        size = self._estimate_size(value)

        # 检查是否需要淘汰
        while self.current_size + size > self.max_size_bytes and self.cache:
            # 淘汰最旧的项
            oldest_key, oldest_value = self.cache.popitem(last=False)
            self.current_size -= self._estimate_size(oldest_value)
            logger.debug(f"L1淘汰: {oldest_key[:8]}...")

        # 添加新项
        self.cache[key] = value
        self.current_size += size

    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.current_size = 0
        self.hits = 0
        self.misses = 0
        logger.info("L1缓存已清空")

    def get_stats(self) -> dict:
        """获取统计信息"""
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0

        return {
            "level": "L1",
            "type": "memory",
            "size_mb": round(self.current_size / 1024 / 1024, 2),
            "max_size_mb": self.max_size_bytes / 1024 / 1024,
            "usage_percent": round((self.current_size / self.max_size_bytes) * 100, 1),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(hit_rate, 4),
            "items": len(self.cache)
        }

class ModelCacheManager:
    """模型缓存管理器 - 统一三级缓存接口

    特性:
    - L1内存缓存 (<1ms)
    - L2 Redis缓存 (<10ms) - 可选
    - L3 磁盘缓存 (<100ms) - 可选
    - 自动缓存策略
    - TTL管理
    """

    def __init__(
        self,
        l1_max_size_mb: int = 500,
        enable_l2: bool = False,
        enable_l3: bool = True,
        l3_cache_dir: str = None
    ):
        """
        初始化缓存管理器

        Args:
            l1_max_size_mb: L1缓存最大大小
            enable_l2: 启用L2 Redis缓存
            enable_l3: 启用L3磁盘缓存
            l3_cache_dir: L3缓存目录
        """
        self.l1 = L1MemoryCache(max_size_mb=l1_max_size_mb)
        self.enable_l2 = enable_l2
        self.enable_l3 = enable_l3

        # L2 Redis (可选)
        self.l2_client = None
        if enable_l2:
            try:
                import redis
                self.l2_client = redis.Redis(
                    host='localhost',
                    port=6379,
                    db=0,
                    decode_responses=False
                )
                self.l2_client.ping()
                logger.info("✅ L2 Redis缓存已连接")
            except Exception as e:
                logger.warning(f"L2 Redis连接失败: {e}")
                self.enable_l2 = False

        # L3 磁盘缓存
        self.l3_cache_dir = None
        if enable_l3:
            if l3_cache_dir is None:
                l3_cache_dir = Path("/Users/xujian/Athena工作平台/cache/model_embeddings")
            else:
                l3_cache_dir = Path(l3_cache_dir)

            self.l3_cache_dir = l3_cache_dir
            self.l3_cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ L3磁盘缓存: {self.l3_cache_dir}")

        # 统计
        self.l1_hits = 0
        self.l2_hits = 0
        self.l3_hits = 0
        self.total_misses = 0

    def _get_key(self, model_name: str, text: str) -> str:
        """生成缓存键"""
        content = f"{model_name}:{text}"
        return hashlib.sha256(content.encode()).hexdigest()

    def get(self, model_name: str, text: str) -> Any | None:
        """
        获取缓存值 (三级查找)

        Returns:
            缓存值或None
        """
        key = self._get_key(model_name, text)

        # L1查找
        value = self.l1.get(model_name, text)
        if value is not None:
            self.l1_hits += 1
            return value

        # L2查找
        if self.enable_l2 and self.l2_client:
            try:
                data = self.l2_client.get(f"model:{key}")
                if data:
                    value = pickle.loads(data)
                    # 回填L1
                    self.l1.set(model_name, text, value)
                    self.l2_hits += 1
                    logger.debug(f"L2缓存命中: {model_name}")
                    return value
            except Exception as e:
                logger.warning(f"L2查询失败: {e}")

        # L3查找
        if self.enable_l3 and self.l3_cache_dir:
            cache_file = self.l3_cache_dir / f"{key}.pkl"

            if cache_file.exists():
                try:
                    with open(cache_file, 'rb') as f:
                        value = pickle.load(f)

                    # 回填L1和L2
                    self.l1.set(model_name, text, value)

                    if self.enable_l2 and self.l2_client:
                        try:
                            self.l2_client.setex(
                                f"model:{key}",
                                86400,  # 24小时
                                pickle.dumps(value)
                            )
                        except Exception as e:
                            logger.warning(f'L2回填失败: {e}')

                    self.l3_hits += 1
                    logger.debug(f"L3缓存命中: {model_name}")
                    return value

                except Exception as e:
                    logger.warning(f"L3读取失败: {e}")

        # 未命中
        self.total_misses += 1
        return None

    def set(self, model_name: str, text: str, value: Any):
        """
        设置缓存值 (写入所有启用的层级)
        """
        key = self._get_key(model_name, text)

        # 写入L1
        self.l1.set(model_name, text, value)

        # 写入L2
        if self.enable_l2 and self.l2_client:
            try:
                self.l2_client.setex(
                    f"model:{key}",
                    86400,  # 24小时
                    pickle.dumps(value)
                )
            except Exception as e:
                logger.warning(f"L2写入失败: {e}")

        # 写入L3
        if self.enable_l3 and self.l3_cache_dir:
            cache_file = self.l3_cache_dir / f"{key}.pkl"

            try:
                with open(cache_file, 'wb') as f:
                    pickle.dump(value, f)
            except Exception as e:
                logger.warning(f"L3写入失败: {e}")

    def clear(self, level: str = "all"):
        """
        清空缓存

        Args:
            level: "l1", "l2", "l3", "all"
        """
        if level in ["l1", "all"]:
            self.l1.clear()

        if level in ["l2", "all"] and self.enable_l2 and self.l2_client:
            try:
                # 只删除model相关的键
                for key in self.l2_client.scan_iter("model:*"):
                    self.l2_client.delete(key)
                logger.info("L2缓存已清空")
            except Exception as e:
                logger.warning(f"L2清空失败: {e}")

        if level in ["l3", "all"] and self.enable_l3 and self.l3_cache_dir:
            try:
                for cache_file in self.l3_cache_dir.glob("*.pkl"):
                    cache_file.unlink()
                logger.info("L3缓存已清空")
            except Exception as e:
                logger.warning(f"L3清空失败: {e}")

        # 重置统计
        if level == "all":
            self.l1_hits = 0
            self.l2_hits = 0
            self.l3_hits = 0
            self.total_misses = 0

    def get_stats(self) -> dict:
        """获取缓存统计"""
        total_hits = self.l1_hits + self.l2_hits + self.l3_hits
        total_requests = total_hits + self.total_misses
        overall_hit_rate = total_hits / total_requests if total_requests > 0 else 0

        stats = {
            "overall_hit_rate": round(overall_hit_rate, 4),
            "l1": self.l1.get_stats(),
            "l1_hits": self.l1_hits,
            "total_requests": total_requests
        }

        if self.enable_l2:
            stats["l2_hits"] = self.l2_hits
            stats["l2_enabled"] = True
        else:
            stats["l2_enabled"] = False

        if self.enable_l3:
            stats["l3_hits"] = self.l3_hits
            stats["l3_enabled"] = True
            # L3缓存文件数
            if self.l3_cache_dir and self.l3_cache_dir.exists():
                stats["l3_files"] = len(list(self.l3_cache_dir.glob("*.pkl")))
        else:
            stats["l3_enabled"] = False

        return stats

    def get_detailed_stats(self) -> dict:
        """获取详细统计信息"""
        stats = self.get_stats()

        # 添加层级分布
        total_hits = self.l1_hits + self.l2_hits + self.l3_hits
        if total_hits > 0:
            stats["hit_distribution"] = {
                "l1_percent": round(self.l1_hits / total_hits * 100, 1),
                "l2_percent": round(self.l2_hits / total_hits * 100, 1) if self.enable_l2 else 0,
                "l3_percent": round(self.l3_hits / total_hits * 100, 1) if self.enable_l3 else 0,
            }

        return stats

# 全局缓存管理器
_cache_manager: ModelCacheManager | None = None

def get_cache_manager(**kwargs) -> ModelCacheManager:
    """获取全局缓存管理器实例"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = ModelCacheManager(**kwargs)
    return _cache_manager

def reset_cache_manager():
    """重置全局缓存管理器"""
    global _cache_manager
    _cache_manager = None

# 便捷函数
def cached_embedding(model_name: str):
    """缓存装饰器"""
    cache = get_cache_manager()

    def decorator(func):
        def wrapper(text: str):
            # 尝试从缓存获取
            cached = cache.get(model_name, text)
            if cached is not None:
                return cached

            # 调用原函数
            result = func(text)

            # 写入缓存
            cache.set(model_name, text, result)

            return result

        return wrapper

    return decorator
