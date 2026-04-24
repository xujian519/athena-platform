"""
API响应优化模块

目标: 将API P95延迟从170.5ms降至<100ms（-41%改进）

优化策略:
1. 响应缓存 - 缓存高频API响应
2. 序列化优化 - 使用更快的序列化器
3. 数据库查询优化 - 减少查询次数
4. 异步处理 - 并行处理独立任务

Author: Athena Team
Date: 2026-04-24
"""

import asyncio
import json
import hashlib
import time
from typing import Any, Dict, List, Optional, Callable
from functools import wraps
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta


@dataclass
class CacheConfig:
    """缓存配置"""
    enabled: bool = True
    ttl_seconds: int = 300  # 5分钟
    max_size: int = 1000
    key_prefix: str = "api_cache"


class APICache:
    """API响应缓存"""

    def __init__(self, config: CacheConfig):
        self.config = config
        self._cache: Dict[str, tuple[Any, float]] = {}  # key -> (value, expiry)
        self._access_times: Dict[str, float] = {}  # key -> last_access

    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """生成缓存键"""
        # 序列化参数
        key_data = {
            "func": func_name,
            "args": str(args),
            "kwargs": str(sorted(kwargs.items())),
        }
        key_str = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        return f"{self.config.key_prefix}:{func_name}:{key_hash}"

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if not self.config.enabled:
            return None

        if key not in self._cache:
            return None

        value, expiry = self._cache[key]

        # 检查是否过期
        if time.time() > expiry:
            del self._cache[key]
            if key in self._access_times:
                del self._access_times[key]
            return None

        # 更新访问时间
        self._access_times[key] = time.time()
        return value

    def set(self, key: str, value: Any):
        """设置缓存值"""
        if not self.config.enabled:
            return

        # 检查缓存大小
        if len(self._cache) >= self.config.max_size:
            self._evict_lru()

        expiry = time.time() + self.config.ttl_seconds
        self._cache[key] = (value, expiry)
        self._access_times[key] = time.time()

    def _evict_lru(self):
        """淘汰最久未使用的项"""
        if not self._access_times:
            return

        # 找到最久未使用的键
        lru_key = min(self._access_times.items(), key=lambda x: x[1])[0]
        del self._cache[lru_key]
        del self._access_times[lru_key]

    def clear(self):
        """清空缓存"""
        self._cache.clear()
        self._access_times.clear()

    def stats(self) -> Dict[str, int]:
        """获取缓存统计"""
        return {
            "size": len(self._cache),
            "max_size": self.config.max_size,
            "hit_rate": 0.0,  # 需要额外跟踪hit/miss
        }


# 全局缓存实例
_global_cache: Optional[APICache] = None


def get_api_cache() -> APICache:
    """获取全局API缓存"""
    global _global_cache
    if _global_cache is None:
        _global_cache = APICache(CacheConfig())
    return _global_cache


def cached_api(ttl: int = 300):
    """
    API缓存装饰器

    Args:
        ttl: 缓存生存时间（秒），默认5分钟

    Usage:
        @cached_api(ttl=600)
        async def get_patent_data(patent_id: str):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_api_cache()
            key = cache._generate_key(func.__name__, args, kwargs)

            # 尝试从缓存获取
            cached_value = cache.get(key)
            if cached_value is not None:
                return cached_value

            # 执行函数
            result = await func(*args, **kwargs)

            # 缓存结果
            cache.set(key, result)

            return result

        return wrapper
    return decorator


class FastJSONEncoder(json.JSONEncoder):
    """优化的JSON编码器"""

    def default(self, obj: Any) -> Any:
        # 处理datetime
        if isinstance(obj, datetime):
            return obj.isoformat()
        # 处理dataclass
        if hasattr(obj, "__dataclass_fields__"):
            return asdict(obj)
        return super().default(obj)


def fast_json_dumps(obj: Any) -> str:
    """快速JSON序列化"""
    return json.dumps(obj, cls=FastJSONEncoder, separators=(",", ":"))


def fast_json_loads(s: str) -> Any:
    """快速JSON反序列化"""
    return json.loads(s)


class ResponseOptimizer:
    """API响应优化器"""

    def __init__(self):
        self.cache = get_api_cache()
        self.optimizations_enabled = True

    async def optimize_api_call(
        self,
        func: Callable,
        *args,
        use_cache: bool = True,
        parallel: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        优化的API调用

        Args:
            func: 要调用的函数
            use_cache: 是否使用缓存
            parallel: 是否并行处理（如果有多个独立任务）

        Returns:
            优化后的响应
        """
        start_time = time.time()

        try:
            # 尝试缓存
            if use_cache:
                cache_key = self.cache._generate_key(func.__name__, args, kwargs)
                cached_result = self.cache.get(cache_key)
                if cached_result is not None:
                    return {
                        "success": True,
                        "data": cached_result,
                        "cached": True,
                        "duration_ms": (time.time() - start_time) * 1000,
                    }

            # 执行函数
            result = await func(*args, **kwargs)

            # 缓存结果
            if use_cache:
                self.cache.set(cache_key, result)

            return {
                "success": True,
                "data": result,
                "cached": False,
                "duration_ms": (time.time() - start_time) * 1000,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000,
            }


# 使用示例
async def example_optimized_api():
    """优化后的API示例"""

    optimizer = ResponseOptimizer()

    # 示例1: 缓存的API调用
    @cached_api(ttl=600)
    async def get_patent_info(patent_id: str) -> Dict[str, Any]:
        # 模拟数据库查询
        await asyncio.sleep(0.1)  # 100ms
        return {
            "patent_id": patent_id,
            "title": "示例专利",
            "status": "active",
        }

    # 第一次调用 - 未缓存
    result1 = await optimizer.optimize_api_call(
        get_patent_info,
        "CN123456",
        use_cache=True
    )

    # 第二次调用 - 从缓存获取
    result2 = await optimizer.optimize_api_call(
        get_patent_info,
        "CN123456",
        use_cache=True
    )

    return {
        "first_call": result1,
        "second_call": result2,
        "cache_stats": optimizer.cache.stats(),
    }


if __name__ == "__main__":
    # 测试优化效果
    async def test():
        print("测试API响应优化...")
        result = await example_optimized_api()
        print(f"结果: {json.dumps(result, indent=2, ensure_ascii=False)}")

    asyncio.run(test())
