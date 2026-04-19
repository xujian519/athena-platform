#!/usr/bin/env python3
from __future__ import annotations
"""
Athena缓存管理器
提供统一的Redis缓存接口
"""

import json
import logging
import pickle
from typing import Any

import redis


class AthenaCacheManager:
    """Athena平台统一缓存管理器"""

    def __init__(self, host="127.0.0.1", port=6379, db=0, password=None):
        """初始化Redis连接"""
        self.redis_client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=False,  # 保持二进制模式,支持pickle
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
        )
        self.default_ttl = 3600  # 默认1小时过期

        # 测试连接
        try:
            self.redis_client.ping()
            logging.info("✅ Redis缓存连接成功")
        except Exception as e:
            logging.error(f"❌ Redis连接失败: {e}")

    def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """
        设置缓存
        Args:
            key: 缓存键
            value: 缓存值(任意Python对象)
            ttl: 过期时间(秒),默认使用default_ttl
        Returns:
            bool: 是否成功
        """
        try:
            # 序列化数据
            serialized_data = pickle.dumps(value)
            expire_time = ttl or self.default_ttl

            result = self.redis_client.setex(name=key, time=expire_time, value=serialized_data)
            return bool(result)
        except Exception as e:
            logging.error(f"缓存设置失败 {key}: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取缓存
        Args:
            key: 缓存键
            default: 默认值
        Returns:
            Any: 缓存值或默认值
        """
        try:
            data = self.redis_client.get(key)
            if data is None:
                return default

            # 反序列化数据
            return pickle.loads(data)
        except Exception as e:
            logging.error(f"缓存获取失败 {key}: {e}")
            return default

    def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logging.error(f"缓存删除失败 {key}: {e}")
            return False

    def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logging.error(f"缓存检查失败 {key}: {e}")
            return False

    def clear(self, pattern: str = "*") -> int:
        """清理缓存"""
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logging.error(f"缓存清理失败 {pattern}: {e}")
            return 0

    def get_stats(self) -> dict:
        """获取Redis统计信息"""
        try:
            info = self.redis_client.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "0B"),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(info),
            }
        except Exception as e:
            logging.error(f"获取Redis统计失败: {e}")
            return {}

    def _calculate_hit_rate(self, info: dict) -> float:
        """计算缓存命中率"""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        return (hits / total * 100) if total > 0 else 0.0

    def set_service_cache(self, service_name: str, data: dict, ttl: int = 300) -> bool:
        """
        设置服务缓存
        Args:
            service_name: 服务名称
            data: 服务数据
            ttl: 过期时间(默认5分钟)
        """
        key = f"service:{service_name}"
        return self.set(key, data, ttl)

    def get_service_cache(self, service_name: str, default: dict | None = None) -> dict:
        """获取服务缓存"""
        key = f"service:{service_name}"
        return self.get(key, default or {})

    def set_api_cache(self, endpoint: str, params: dict, response: dict, ttl: int = 600) -> bool:
        """
        设置API响应缓存
        Args:
            endpoint: API端点
            params: 请求参数
            response: 响应数据
            ttl: 过期时间(默认10分钟)
        """
        # 创建缓存键
        import hashlib

        params_str = json.dumps(params, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode(), usedforsecurity=False).hexdigest()
        key = f"api:{endpoint}:{params_hash}"

        return self.set(key, response, ttl)

    def get_api_cache(self, endpoint: str, params: dict, default: dict | None = None) -> dict:
        """获取API响应缓存"""
        import hashlib

        params_str = json.dumps(params, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode(), usedforsecurity=False).hexdigest()
        key = f"api:{endpoint}:{params_hash}"

        return self.get(key, default or {})


# 全局缓存实例
cache_manager = AthenaCacheManager()


# 装饰器:缓存函数结果
def cache_result(key_prefix: str, ttl: int = 300) -> Any:
    """
    缓存函数结果的装饰器
    Args:
        key_prefix: 缓存键前缀
        ttl: 过期时间(秒)
    """

    def decorator(func) -> None:
        def wrapper(*args, **kwargs) -> Any:
            # 生成缓存键
            import hashlib

            args_str = str(args) + str(sorted(kwargs.items()))
            args_hash = hashlib.md5(args_str.encode(), usedforsecurity=False).hexdigest()
            cache_key = f"{key_prefix}:{args_hash}"

            # 尝试从缓存获取
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result

            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            return result

        return wrapper

    return decorator
