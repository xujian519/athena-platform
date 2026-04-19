"""
速率限制中间件

基于 Redis 实现分布式速率限制。
"""

import time
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Request
from starlette.responses import Response

from .base import (
    Middleware,
    MiddlewareContext,
    RateLimitExceededException,
)


class RateLimitMiddleware(Middleware):
    """速率限制中间件

    支持多种限流策略：
    1. 固定窗口（Fixed Window）
    2. 滑动窗口（Sliding Window）
    3. 令牌桶（Token Bucket）

    配置选项：
    - strategy: 限流策略，fixed_window / sliding_window / token_bucket
    - requests_per_window: 每个时间窗口的请求数，默认 100
    - window_size: 时间窗口大小（秒），默认 60
    - burst_size: 突发容量（仅令牌桶），默认 10
    - redis_url: Redis 连接 URL，默认 redis://localhost:6379/0
    - skip_paths: 跳过限流的路径列表
    """

    def __init__(
        self,
        strategy: str = "fixed_window",
        requests_per_window: int = 100,
        window_size: int = 60,
        burst_size: int = 10,
        redis_url: str = "redis://localhost:6379/0",
        skip_paths: list[str] | None = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self._strategy = strategy
        self._requests_per_window = requests_per_window
        self._window_size = window_size
        self._burst_size = burst_size
        self._redis_url = redis_url
        self._skip_paths = set(skip_paths or [])

        # 添加默认跳过路径
        self._skip_paths.update([
            "/health",
            "/metrics",
        ])

        # Redis 连接池（延迟初始化）
        self._redis: Any | None = None

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
                # 如果没有安装 redis，使用内存实现
                self._redis = InMemoryStore()
        return self._redis

    async def process(
        self,
        ctx: MiddlewareContext,
        call_next: Callable[[MiddlewareContext], Awaitable[Response]]
    ) -> Response:
        """处理速率限制"""

        # 检查是否跳过限流
        if self._should_skip_rate_limit(ctx.request.url.path):
            return await call_next(ctx)

        # 获取客户端标识
        client_id = self._get_client_id(ctx.request, ctx)

        # 检查是否超过限制
        allowed, retry_after = await self._check_rate_limit(client_id)

        if not allowed:
            raise RateLimitExceededException(
                f"Rate limit exceeded. Try again in {retry_after} seconds.",
                retry_after=retry_after
            )

        return await call_next(ctx)

    def _should_skip_rate_limit(self, path: str) -> bool:
        """检查是否跳过限流"""
        for skip_path in self._skip_paths:
            if path.startswith(skip_path):
                return True
        return False

    def _get_client_id(self, request: Request, ctx: MiddlewareContext) -> str:
        """获取客户端标识"""
        # 优先使用用户ID
        if ctx.user_id:
            return f"user:{ctx.user_id}"

        # 使用客户端IP
        client_ip = self._get_client_ip(request)
        return f"ip:{client_ip}"

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        if request.client:
            return request.client.host
        return "unknown"

    async def _check_rate_limit(self, client_id: str) -> tuple[bool, int]:
        """检查速率限制

        Returns:
            tuple[bool, int]: (是否允许, 重试时间秒数)
        """
        redis = await self._get_redis()

        if self._strategy == "fixed_window":
            return await self._check_fixed_window(redis, client_id)
        elif self._strategy == "sliding_window":
            return await self._check_sliding_window(redis, client_id)
        elif self._strategy == "token_bucket":
            return await self._check_token_bucket(redis, client_id)
        else:
            # 默认使用固定窗口
            return await self._check_fixed_window(redis, client_id)

    async def _check_fixed_window(
        self, redis: Any, client_id: str
    ) -> tuple[bool, int]:
        """固定窗口算法"""
        key = f"ratelimit:{client_id}:fixed"
        current_time = int(time.time())
        window_start = current_time // self._window_size * self._window_size

        # 使用 Redis 管道减少往返
        pipe = redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start - 1)
        pipe.zcard(key)
        pipe.pexpire(key, (self._window_size + 1) * 1000)
        results = await pipe.execute()

        count = results[1]

        if count >= self._requests_per_window:
            ttl = await redis.pttl(key)
            retry_after = (ttl + 999) // 1000  # 转换为秒
            return False, retry_after

        # 添加当前请求
        await redis.zadd(key, {str(current_time): current_time})
        return True, 0

    async def _check_sliding_window(
        self, redis: Any, client_id: str
    ) -> tuple[bool, int]:
        """滑动窗口算法"""
        key = f"ratelimit:{client_id}:sliding"
        current_time = time.time()
        window_start = current_time - self._window_size

        # 移除窗口外的记录
        await redis.zremrangebyscore(key, 0, window_start)

        # 获取当前计数
        count = await redis.zcard(key)

        if count >= self._requests_per_window:
            # 计算最旧记录的过期时间
            oldest = await redis.zrange(key, 0, 0, withscores=True)
            if oldest:
                retry_after = int(oldest[0][1] + self._window_size - current_time) + 1
                return False, max(retry_after, 1)
            return False, self._window_size

        # 添加当前请求
        await redis.zadd(key, {str(current_time): current_time})
        await redis.pexpire(key, int(self._window_size * 1000))
        return True, 0

    async def _check_token_bucket(
        self, redis: Any, client_id: str
    ) -> tuple[bool, int]:
        """令牌桶算法"""
        key = f"ratelimit:{client_id}:tokens"
        current_time = time.time()

        # 获取当前桶状态
        data = await redis.hgetall(key)

        if not data:
            # 初始化令牌桶
            tokens = self._burst_size
            last_refill = current_time
        else:
            tokens = float(data.get("tokens", self._burst_size))
            last_refill = float(data.get("last_refill", current_time))

        # 计算应该添加的令牌数
        elapsed = current_time - last_refill
        refill_rate = self._requests_per_window / self._window_size
        new_tokens = min(
            self._burst_size,
            tokens + elapsed * refill_rate
        )

        if new_tokens < 1:
            # 没有足够的令牌
            retry_after = int((1 - new_tokens) / refill_rate) + 1
            return False, retry_after

        # 消耗一个令牌
        await redis.hset(key, mapping={
            "tokens": new_tokens - 1,
            "last_refill": current_time
        })
        await redis.pexpire(key, int(self._window_size * 2 * 1000))

        return True, 0


class InMemoryStore:
    """内存存储（用于没有 Redis 的情况）"""

    def __init__(self):
        self._store: dict[str, list] = {}
        self._hashes: dict[str, dict] = {}

    async def zremrangebyscore(self, key: str, min_score: float, max_score: float):
        if key in self._store:
            self._store[key] = [
                (k, v) for k, v in self._store[key]
                if not (min_score <= v <= max_score)
            ]

    async def zcard(self, key: str) -> int:
        return len(self._store.get(key, []))

    async def zadd(self, key: str, mapping: dict):
        if key not in self._store:
            self._store[key] = []
        for member, score in mapping.items():
            self._store[key].append((member, float(score)))

    async def zrange(self, key: str, start: int, end: int, withscores: bool = False):
        items = sorted(self._store.get(key, []), key=lambda x: x[1])
        items = items[start:end + 1]
        if withscores:
            return items
        return [k for k, v in items]

    async def pexpire(self, key: str, milliseconds: int):
        pass  # 内存实现不需要过期

    async def pttl(self, key: str) -> int:
        return 60000  # 默认返回 60 秒

    async def hgetall(self, key: str) -> dict:
        return self._hashes.get(key, {})

    async def hset(self, key: str, mapping: dict):
        if key not in self._hashes:
            self._hashes[key] = {}
        self._hashes[key].update(mapping)

    def pipeline(self):
        return _Pipeline(self)


class _Pipeline:
    """简单的管道实现"""

    def __init__(self, store: InMemoryStore):
        self._store = store
        self._commands: list[Callable] = []

    def zremrangebyscore(self, key: str, min_score: float, max_score: float):
        self._commands.append(lambda: self._store.zremrangebyscore(key, min_score, max_score))
        return self

    def zcard(self, key: str):
        self._commands.append(lambda: self._store.zcard(key))
        return self

    def pexpire(self, key: str, milliseconds: int):
        self._commands.append(lambda: self._store.pexpire(key, milliseconds))
        return self

    async def execute(self):
        results = []
        for cmd in self._commands:
            results.append(await cmd())
        return results
