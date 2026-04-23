from __future__ import annotations
"""
Redis缓存实现
使用Redis作为分布式缓存存储
"""

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

# 使用统一的Redis配置
try:
    from core.cache.redis_config import get_redis_config
    REDIS_CONFIG_AVAILABLE = True
except ImportError:
    REDIS_CONFIG_AVAILABLE = False


class RedisCache:
    """Redis缓存类"""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        db: Optional[int] = None,
        password: Optional[str] = None,
        default_ttl: int = 300,
        use_config: bool = True,
        **kwargs,
    ):
        """
        初始化Redis缓存

        Args:
            host: Redis主机（如果为None且use_config=True，从配置读取）
            port: Redis端口（如果为None且use_config=True，从配置读取）
            db: Redis数据库编号（如果为None且use_config=True，从配置读取）
            password: Redis密码（如果为None且use_config=True，从配置读取）
            default_ttl: 默认生存时间（秒）
            use_config: 是否使用统一配置（默认True）
            **kwargs: 其他Redis连接参数
        """
        if not REDIS_AVAILABLE:
            raise ImportError("redis包未安装，请运行: pip install redis")

        # 获取配置
        if use_config and REDIS_CONFIG_AVAILABLE:
            config = get_redis_config()
            redis_host = host or config.get("host")
            redis_port = port or config.get("port")
            redis_db = db or config.get("db")
            redis_password = password or config.get("password")
        else:
            redis_host = host or "localhost"
            redis_port = port or 6379
            redis_db = db or 0
            redis_password = password

        self._default_ttl = default_ttl
        self._client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password,
            decode_responses=True,
            **kwargs
        )

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 生存时间（秒），None表示使用默认值

        Returns:
            是否设置成功
        """
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            ttl = ttl if ttl is not None else self._default_ttl
            return self._client.setex(key, ttl, value)
        except Exception:
            return False

    def get(self, key: str) -> Any | None:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值，如果不存在则返回None
        """
        try:
            value = self._client.get(key)
            if value is None:
                return None
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception:
            return None

    def delete(self, key: str) -> bool:
        """
        删除缓存值

        Args:
            key: 缓存键

        Returns:
            是否删除成功
        """
        try:
            return bool(self._client.delete(key))
        except Exception:
            return False

    def exists(self, key: str) -> bool:
        """
        检查缓存键是否存在

        Args:
            key: 缓存键

        Returns:
            是否存在
        """
        try:
            return bool(self._client.exists(key))
        except Exception:
            return False

    def clear(self) -> bool:
        """
        清空当前数据库的所有缓存

        Returns:
            是否清空成功
        """
        try:
            return self._client.flushdb() is not None
        except Exception:
            return False

    def get_many(self, keys: list[str]) -> dict[str, Any]:
        """
        批量获取缓存值

        Args:
            keys: 缓存键列表

        Returns:
            键值对字典
        """
        try:
            values = self._client.mget(keys)
            result = {}
            for key, value in zip(keys, values, strict=False):
                if value is not None:
                    try:
                        result[key] = json.loads(value)
                    except json.JSONDecodeError:
                        result[key] = value
            return result
        except Exception:
            return {}

    def set_many(self, mapping: dict[str, Any]) -> bool:
        """
        批量设置缓存值

        Args:
            mapping: 键值对字典

        Returns:
            是否设置成功
        """
        try:
            pipe = self._client.pipeline()
            for key, value in mapping.items():
                if isinstance(value, (dict, list)):
                    value = json.dumps(value)
                pipe.setex(key, self._default_ttl, value)
            pipe.execute()
            return True
        except Exception:
            return False

    def delete_many(self, keys: list[str]) -> bool:
        """
        批量删除缓存值

        Args:
            keys: 缓存键列表

        Returns:
            是否删除成功
        """
        try:
            if keys:
                return self._client.delete(*keys) > 0
            return True
        except Exception:
            return False

    def expire(self, key: str, ttl: int) -> bool:
        """
        设置键的生存时间

        Args:
            key: 缓存键
            ttl: 生存时间（秒）

        Returns:
            是否设置成功
        """
        try:
            return bool(self._client.expire(key, ttl))
        except Exception:
            return False

    def ttl(self, key: str) -> int:
        """
        获取键的剩余生存时间

        Args:
            key: 缓存键

        Returns:
            剩余生存时间（秒），-1表示永久存在，-2表示不存在
        """
        try:
            return self._client.ttl(key)
        except Exception:
            return -2

    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        原子递增

        Args:
            key: 缓存键
            amount: 递增量

        Returns:
            递增后的值，失败返回None
        """
        try:
            return self._client.incrby(key, amount)
        except Exception:
            return None

    def decrement(self, key: str, amount: int = 1) -> Optional[int]:
        """
        原子递减

        Args:
            key: 缓存键
            amount: 递减量

        Returns:
            递减后的值，失败返回None
        """
        try:
            return self._client.decrby(key, amount)
        except Exception:
            return None

    def keys(self, pattern: str = "*") -> list[str]:
        """
        获取匹配模式的所有键

        Args:
            pattern: 键模式

        Returns:
            键列表
        """
        try:
            return self._client.keys(pattern)
        except Exception:
            return []

    def size(self) -> int:
        """
        获取当前数据库的键数量

        Returns:
            键数量
        """
        try:
            return self._client.dbsize()
        except Exception:
            return 0

    def ping(self) -> bool:
        """
        检查Redis连接

        Returns:
            是否连接正常
        """
        try:
            return bool(self._client.ping())
        except Exception:
            return False

    def close(self) -> None:
        """关闭Redis连接"""
        try:
            self._client.close()
        except Exception as e:
            print(f"捕获Exception异常: {e}")

    def __del__(self):
        """析构函数，确保连接关闭"""
        self.close()
