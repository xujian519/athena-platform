"""
缓存中间件

提供基于 Redis 的 HTTP 响应缓存功能。
"""

import hashlib
import json
import re
import time
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Request, Response
from starlette.responses import JSONResponse

from .base import Middleware, MiddlewareContext


class CacheMiddleware(Middleware):
    """缓存中间件

    对 GET 和 HEAD 请求的响应进行缓存，提升性能。

    配置选项：
    - redis_url: Redis 连接 URL
    - default_ttl: 默认缓存时间（秒），默认 60
    - cacheable_methods: 可缓存的 HTTP 方法，默认 ["GET", "HEAD"]
    - cacheable_status_codes: 可缓存的状态码，默认 [200, 301, 302]
    - cache_key_prefix: 缓存键前缀，默认 "athena_cache:"
    - cache_rules: 缓存规则列表，按路径模式匹配
    - skip_headers: 跳过缓存的响应头，默认 ["Authorization"]
    - max_body_size: 最大缓存响应体大小（字节），默认 1MB

    缓存规则格式：
    [
        {
            "path_pattern": "^/api/v1/patents",  # 路径正则
            "ttl": 300,                          # 缓存时间（秒）
            "methods": ["GET"],                  # 允许的方法
            "vary_headers": ["Authorization"]     # 变化头
        }
    ]
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/1",
        default_ttl: int = 60,
        cacheable_methods: list[str] | None = None,
        cacheable_status_codes: list[int] | None = None,
        cache_key_prefix: str = "athena_cache:",
        cache_rules: list[dict] | None = None,
        skip_headers: list[str] | None = None,
        max_body_size: int = 1024 * 1024,  # 1MB
        **kwargs
    ):
        super().__init__(**kwargs)
        self._redis_url = redis_url
        self._default_ttl = default_ttl
        self._cacheable_methods = set(cacheable_methods or ["GET", "HEAD"])
        self._cacheable_status_codes = set(cacheable_status_codes or [200, 301, 302])
        self._cache_key_prefix = cache_key_prefix
        self._skip_headers = set(skip_headers or ["Authorization", "Cookie", "Set-Cookie"])
        self._max_body_size = max_body_size

        # 编译缓存规则
        self._cache_rules = []
        if cache_rules:
            for rule in cache_rules:
                self._cache_rules.append({
                    "pattern": re.compile(rule.get("path_pattern", ".*")),
                    "ttl": rule.get("ttl", default_ttl),
                    "methods": set(rule.get("methods", ["GET"])),
                    "vary_headers": set(rule.get("vary_headers", [])),
                })

        # Redis 客户端（延迟初始化）
        self._redis: Any | None = None
        self._use_memory = False

        # 统计信息
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
        }

    async def _get_redis(self):
        """获取 Redis 连接"""
        if self._redis is None:
            try:
                import redis.asyncio as aioredis
                self._redis = await aioredis.from_url(
                    self._redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
            except ImportError:
                # 使用内存缓存
                self._redis = InMemoryCache()
                self._use_memory = True
        return self._redis

    async def process(
        self,
        ctx: MiddlewareContext,
        call_next: Callable[[MiddlewareContext], Awaitable[Response]]
    ) -> Response:
        """处理请求"""

        request = ctx.request

        # 检查是否可缓存
        if request.method not in self._cacheable_methods:
            return await call_next(ctx)

        # 检查是否有跳过缓存的头
        if request.headers.get("Cache-Control") == "no-cache":
            return await call_next(ctx)

        # 生成缓存键
        cache_key = self._generate_cache_key(request)

        # 尝试从缓存获取
        cached_data = await self._get_cached(cache_key)
        if cached_data is not None:
            self._stats["hits"] += 1
            return self._create_cached_response(cached_data)

        # 缓存未命中，执行请求
        self._stats["misses"] += 1
        response = await call_next(ctx)

        # 检查是否应该缓存响应
        if self._should_cache_response(request, response):
            await self._set_cached(cache_key, response)

        return response

    def _generate_cache_key(self, request: Request) -> str:
        """生成缓存键

        基于请求方法、路径、查询参数和指定头部生成唯一键。
        """
        # 基础键
        key_parts = [
            request.method,
            request.url.path,
        ]

        # 添加查询参数
        if request.url.query:
            key_parts.append(request.url.query)

        # 添加变化头（根据缓存规则）
        vary_headers = self._get_vary_headers(request)
        if vary_headers:
            for header in sorted(vary_headers):
                value = request.headers.get(header, "")
                key_parts.append(f"{header}:{value}")

        # 生成哈希
        key_string = "|".join(key_parts)
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:16]

        return f"{self._cache_key_prefix}{key_hash}"

    def _get_vary_headers(self, request: Request) -> set:
        """获取变化头"""
        # 检查缓存规则
        for rule in self._cache_rules:
            if rule["pattern"].match(request.url.path):
                return rule["vary_headers"]
        return set()

    def _get_ttl(self, request: Request) -> int:
        """获取缓存 TTL"""
        # 检查缓存规则
        for rule in self._cache_rules:
            if rule["pattern"].match(request.url.path):
                if request.method in rule["methods"]:
                    return rule["ttl"]

        # 返回默认 TTL
        return self._default_ttl

    async def _get_cached(self, cache_key: str) -> dict | None:
        """从缓存获取数据"""
        try:
            redis = await self._get_redis()
            data = await redis.get(cache_key)
            if data:
                return json.loads(data)
        except Exception:
            # 缓存失败不影响主流程
            pass
        return None

    async def _set_cached(self, cache_key: str, response: Response) -> None:
        """设置缓存"""
        try:
            # 检查响应体大小
            body = getattr(response, "body", b"")
            if isinstance(body, str):
                body = body.encode()
            if len(body) > self._max_body_size:
                return

            # 序列化响应
            cached_data = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": body.decode() if isinstance(body, bytes) else body,
                "cached_at": time.time(),
            }

            redis = await self._get_redis()
            ttl = self._get_ttl_for_response(response)
            await redis.setex(cache_key, ttl, json.dumps(cached_data))

            self._stats["sets"] += 1

        except Exception:
            # 缓存失败不影响主流程
            pass

    def _get_ttl_for_response(self, response: Response) -> int:
        """从响应获取 TTL"""
        # 检查 Cache-Control 头
        cache_control = response.headers.get("Cache-Control", "")
        if "max-age=" in cache_control:
            try:
                max_age = int(cache_control.split("max-age=")[1].split(",")[0])
                return max_age
            except (ValueError, IndexError):
                pass

        # 返回默认 TTL
        return self._default_ttl

    def _should_cache_response(self, request: Request, response: Response) -> bool:
        """判断是否应该缓存响应"""
        # 检查状态码
        if response.status_code not in self._cacheable_status_codes:
            return False

        # 检查响应头
        cache_control = response.headers.get("Cache-Control", "")
        if "no-store" in cache_control or "private" in cache_control:
            return False

        # 检查缓存规则
        for rule in self._cache_rules:
            if rule["pattern"].match(request.url.path):
                if request.method in rule["methods"]:
                    return True

        # 默认不缓存（需要明确配置）
        return False

    def _create_cached_response(self, cached_data: dict) -> Response:
        """从缓存数据创建响应"""
        # 添加缓存指示头
        headers = cached_data.get("headers", {})
        headers["X-Cache"] = "HIT"
        headers["Age"] = str(int(time.time() - cached_data.get("cached_at", 0)))

        return JSONResponse(
            status_code=cached_data["status_code"],
            content=json.loads(cached_data["body"]) if self._is_json(cached_data["body"]) else cached_data["body"],
            headers=headers,
        )

    def _is_json(self, body: str) -> bool:
        """检查是否是 JSON"""
        try:
            json.loads(body)
            return True
        except (json.JSONDecodeError, TypeError):
            return False

    async def invalidate(self, pattern: str) -> int:
        """使缓存失效

        Args:
            pattern: 缓存键模式（支持通配符）

        Returns:
            int: 失效的缓存数量
        """
        try:
            redis = await self._get_redis()
            keys = []
            async for key in redis.scan_iter(match=f"{self._cache_key_prefix}{pattern}*"):
                keys.append(key)

            if keys:
                await redis.delete(*keys)
                self._stats["deletes"] += len(keys)

            return len(keys)
        except Exception:
            return 0

    def get_stats(self) -> dict:
        """获取缓存统计"""
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total if total > 0 else 0

        return {
            **self._stats,
            "hit_rate": round(hit_rate, 4),
            "total_requests": total,
        }

    def reset_stats(self) -> None:
        """重置统计"""
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
        }


class InMemoryCache:
    """内存缓存（用于没有 Redis 的情况）"""

    def __init__(self):
        self._cache: dict[str, tuple[str, float]] = {}  # key -> (value, expiry)

    async def get(self, key: str) -> str | None:
        if key in self._cache:
            value, expiry = self._cache[key]
            if time.time() < expiry:
                return value
            else:
                del self._cache[key]
        return None

    async def setex(self, key: str, seconds: int, value: str):
        self._cache[key] = (value, time.time() + seconds)

    async def delete(self, *keys: str):
        for key in keys:
            self._cache.pop(key, None)

    async def scan_iter(self, match: str):
        for key in self._cache.keys():
            if match.replace("*", "") in key:
                yield key
