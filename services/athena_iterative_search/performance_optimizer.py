#!/usr/bin/env python3
"""
性能优化器
提供缓存管理、连接池优化、异步处理等性能优化功能
"""

import asyncio
import concurrent.futures
import hashlib
import json
import logging
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import lru_cache, wraps
from typing import Any, Callable, Dict, List, Optional, Union

import aiohttp
import aioredis
import psutil
import redis
from aioredis import ConnectionPool

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """性能指标"""
    request_count: int = 0
    total_response_time: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    error_count: int = 0
    concurrent_requests: int = 0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0

    @property
    def average_response_time(self) -> float:
        """平均响应时间"""
        if self.request_count == 0:
            return 0.0
        return self.total_response_time / self.request_count

    @property
    def cache_hit_rate(self) -> float:
        """缓存命中率"""
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return self.cache_hits / total

    def to_dict(self) -> Dict[str, float]:
        """转换为字典"""
        return {
            'request_count': self.request_count,
            'average_response_time': self.average_response_time,
            'cache_hit_rate': self.cache_hit_rate,
            'error_rate': self.error_count / max(self.request_count, 1),
            'concurrent_requests': self.concurrent_requests,
            'memory_usage_mb': self.memory_usage,
            'cpu_usage_percent': self.cpu_usage
        }

class AdvancedCacheManager:
    """高级缓存管理器"""

    def __init__(
        self,
        redis_client: redis.Redis | None = None,
        default_ttl: int = 3600,
        max_size: int = 10000
    ):
        self.redis_client = redis_client
        self.default_ttl = default_ttl
        self.max_size = max_size

        # 内存缓存
        self.memory_cache = {}
        self.cache_timestamps = {}
        self.cache_access_count = defaultdict(int)
        self.cache_lock = threading.RLock()

        # 缓存统计
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }

    def _generate_cache_key(self, prefix: str, data: Any) -> str:
        """生成缓存键"""
        if isinstance(data, str):
            content = data
        elif isinstance(data, dict):
            content = json.dumps(data, sort_keys=True)
        else:
            content = str(data)

        hash_value = hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()
        return f"{prefix}:{hash_value}"

    async def get(self, prefix: str, key_data: Any) -> Any | None:
        """获取缓存值"""
        cache_key = self._generate_cache_key(prefix, key_data)

        # 先检查内存缓存
        with self.cache_lock:
            if cache_key in self.memory_cache:
                timestamp = self.cache_timestamps.get(cache_key, 0)
                if time.time() - timestamp < self.default_ttl:
                    self.cache_access_count[cache_key] += 1
                    self.stats['hits'] += 1
                    return self.memory_cache[cache_key]
                else:
                    # 过期，删除
                    del self.memory_cache[cache_key]
                    del self.cache_timestamps[cache_key]

        # 检查Redis缓存
        if self.redis_client:
            try:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    # 反序列化
                    if cached_data.startswith(b'json:'):
                        data = json.loads(cached_data[5:])
                    else:
                        data = cached_data

                    # 更新内存缓存
                    with self.cache_lock:
                        self._set_memory_cache(cache_key, data)
                        self.stats['hits'] += 1
                    return data
            except Exception as e:
                logger.warning(f"Redis缓存获取失败: {e}")

        self.stats['misses'] += 1
        return None

    async def set(
        self,
        prefix: str,
        key_data: Any,
        value: Any,
        ttl: int | None = None
    ) -> bool:
        """设置缓存值"""
        cache_key = self._generate_cache_key(prefix, key_data)
        ttl = ttl or self.default_ttl

        # 设置内存缓存
        with self.cache_lock:
            self._set_memory_cache(cache_key, value)

        # 设置Redis缓存
        if self.redis_client:
            try:
                # 序列化
                if isinstance(value, (dict, list)):
                    serialized = f"json:{json.dumps(value, ensure_ascii=False)}"
                else:
                    serialized = str(value)

                self.redis_client.setex(cache_key, ttl, serialized)
                return True
            except Exception as e:
                logger.warning(f"Redis缓存设置失败: {e}")
                return False

        return True

    def _set_memory_cache(self, cache_key: str, value: Any) -> Any:
        """设置内存缓存"""
        # 检查缓存大小限制
        if len(self.memory_cache) >= self.max_size:
            self._evict_lru()

        self.memory_cache[cache_key] = value
        self.cache_timestamps[cache_key] = time.time()
        self.cache_access_count[cache_key] = 1

    def _evict_lru(self) -> Any:
        """淘汰最少使用的缓存项"""
        if not self.cache_access_count:
            return

        # 找到最少使用的项
        lru_key = min(self.cache_access_count.items(), key=lambda x: x[1])[0]

        # 删除
        del self.memory_cache[lru_key]
        del self.cache_timestamps[lru_key]
        del self.cache_access_count[lru_key]
        self.stats['evictions'] += 1

    def clear(self, prefix: str | None = None) -> Any:
        """清理缓存"""
        with self.cache_lock:
            if prefix:
                # 清理指定前缀的缓存
                keys_to_remove = [k for k in self.memory_cache.keys() if k.startswith(prefix)]
                for key in keys_to_remove:
                    del self.memory_cache[key]
                    del self.cache_timestamps[key]
                    del self.cache_access_count[key]
            else:
                # 清理所有缓存
                self.memory_cache.clear()
                self.cache_timestamps.clear()
                self.cache_access_count.clear()

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total = self.stats['hits'] + self.stats['misses']
        return {
            **self.stats,
            'hit_rate': self.stats['hits'] / max(total, 1),
            'memory_cache_size': len(self.memory_cache),
            'memory_cache_bytes': sum(
                len(str(v)) for v in self.memory_cache.values()
            )
        }

class ConnectionPoolManager:
    """连接池管理器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.http_pools = {}
        self.redis_pool = None

    async def get_http_pool(self, name: str = 'default') -> aiohttp.ClientSession:
        """获取HTTP连接池"""
        if name not in self.http_pools:
            connector = aiohttp.TCPConnector(
                limit=self.config.get('http_connections', 20),
                limit_per_host=self.config.get('connections_per_host', 10),
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )

            timeout = aiohttp.ClientTimeout(
                total=self.config.get('http_timeout', 30),
                connect=self.config.get('connect_timeout', 10),
                sock_read=self.config.get('read_timeout', 30)
            )

            self.http_pools[name] = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            )

        return self.http_pools[name]

    async def get_redis_pool(self) -> aioredis.Redis:
        """获取Redis连接池"""
        if not self.redis_pool:
            self.redis_pool = aioredis.Redis(
                host=self.config.get('redis_host', 'localhost'),
                port=self.config.get('redis_port', 6379),
                db=self.config.get('redis_db', 0),
                max_connections=self.config.get('redis_connections', 10)
            )
        return self.redis_pool

    async def close_all(self):
        """关闭所有连接"""
        for pool in self.http_pools.values():
            await pool.close()

        if self.redis_pool:
            await self.redis_pool.close()

class AsyncTaskQueue:
    """异步任务队列"""

    def __init__(self, max_workers: int = 5, queue_size: int = 100):
        self.max_workers = max_workers
        self.queue_size = queue_size
        self.queue = asyncio.Queue(maxsize=queue_size)
        self.workers = []
        self.running = False

    async def start(self):
        """启动工作线程"""
        self.running = True
        self.workers = [
            asyncio.create_task(self._worker(f"worker-{i}"))
            for i in range(self.max_workers)
        ]
        logger.info(f"异步任务队列已启动，{self.max_workers}个工作线程")

    async def stop(self):
        """停止工作线程"""
        self.running = False
        # 等待所有任务完成
        await self.queue.join()
        # 取消工作线程
        for worker in self.workers:
            worker.cancel()
        await asyncio.gather(*self.workers, return_exceptions=True)
        logger.info('异步任务队列已停止')

    async def _worker(self, name: str):
        """工作线程"""
        while self.running:
            try:
                task_func, args, kwargs = await asyncio.wait_for(
                    self.queue.get(),
                    timeout=1.0
                )
                try:
                    await task_func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"任务执行失败 [{name}]: {e}")
                finally:
                    self.queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"工作线程错误 [{name}]: {e}")

    async def submit(self, func: Callable, *args, **kwargs):
        """提交任务"""
        await self.queue.put((func, args, kwargs))

    def is_full(self) -> bool:
        """检查队列是否已满"""
        return self.queue.qsize() >= self.queue_size

    def size(self) -> int:
        """获取队列大小"""
        return self.queue.qsize()

class PerformanceOptimizer:
    """性能优化器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.metrics = PerformanceMetrics()
        self.cache_manager = AdvancedCacheManager(
            default_ttl=config.get('cache_ttl', 3600),
            max_size=config.get('cache_size', 10000)
        )
        self.connection_pool = ConnectionPoolManager(config)
        self.task_queue = AsyncTaskQueue(
            max_workers=config.get('max_workers', 5),
            queue_size=config.get('queue_size', 100)
        )
        self._lock = asyncio.Lock()

        # 系统资源监控
        self.monitoring = config.get('enable_monitoring', True)
        self.monitor_interval = config.get('monitor_interval', 60)

    async def start(self):
        """启动性能优化器"""
        await self.task_queue.start()

        if self.monitoring:
            asyncio.create_task(self._monitor_system_resources())

        logger.info('性能优化器已启动')

    async def stop(self):
        """停止性能优化器"""
        await self.task_queue.stop()
        await self.connection_pool.close_all()
        logger.info('性能优化器已停止')

    def cache_result(self, prefix: str, ttl: int | None = None) -> Any:
        """缓存装饰器"""
        def decorator(func) -> None:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # 生成缓存键
                cache_data = {
                    'args': args,
                    'kwargs': kwargs
                }

                # 尝试从缓存获取
                cached_result = await self.cache_manager.get(prefix, cache_data)
                if cached_result is not None:
                    return cached_result

                # 执行函数
                result = await func(*args, **kwargs)

                # 缓存结果
                await self.cache_manager.set(prefix, cache_data, result, ttl)

                return result
            return wrapper
        return decorator

    def async_execute(self, submit_to_queue: bool = False) -> Any:
        """异步执行装饰器"""
        def decorator(func) -> None:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()

                async with self._lock:
                    self.metrics.concurrent_requests += 1

                try:
                    if submit_to_queue and not self.task_queue.is_full():
                        # 提交到任务队列
                        future = asyncio.Future()
                        await self.task_queue.submit(
                            self._execute_with_future, func, args, kwargs, future
                        )
                        result = await future
                    else:
                        # 直接执行
                        result = await func(*args, **kwargs)

                    # 更新指标
                    response_time = time.time() - start_time
                    self.metrics.request_count += 1
                    self.metrics.total_response_time += response_time

                    return result

                except Exception as e:
                    self.metrics.error_count += 1
                    logger.error(f"执行失败 {func.__name__}: {e}")
                    raise
                finally:
                    async with self._lock:
                        self.metrics.concurrent_requests -= 1

            return wrapper
        return decorator

    async def _execute_with_future(self, func, args, kwargs, future):
        """在任务队列中执行函数"""
        try:
            result = await func(*args, **kwargs)
            future.set_result(result)
        except Exception as e:
            future.set_exception(e)

    async def batch_process(
        self,
        items: List[Any],
        process_func: Callable,
        batch_size: int = 10,
        max_concurrent: int = 5
    ) -> List[Any]:
        """批量处理"""
        if not items:
            return []

        results = []
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_batch(batch):
            async with semaphore:
                tasks = [process_func(item) for item in batch]
                return await asyncio.gather(*tasks, return_exceptions=True)

        # 分批处理
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = await process_batch(batch)
            results.extend(batch_results)

        return results

    async def _monitor_system_resources(self):
        """监控系统资源"""
        while True:
            try:
                # 获取系统资源使用情况
                memory = psutil.virtual_memory()
                cpu = psutil.cpu_percent(interval=1)

                self.metrics.memory_usage = memory.used / 1024 / 1024  # MB
                self.metrics.cpu_usage = cpu

                # 记录警告
                if memory.percent > 90:
                    logger.warning(f"内存使用率过高: {memory.percent:.1f}%")

                if cpu > 80:
                    logger.warning(f"CPU使用率过高: {cpu:.1f}%")

                await asyncio.sleep(self.monitor_interval)

            except Exception as e:
                logger.error(f"系统资源监控失败: {e}")
                await asyncio.sleep(self.monitor_interval)

    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return {
            'performance': self.metrics.to_dict(),
            'cache': self.cache_manager.get_stats(),
            'queue': {
                'size': self.task_queue.size(),
                'max_size': self.task_queue.queue_size,
                'workers': len(self.task_queue.workers)
            }
        }

    def reset_metrics(self) -> Any:
        """重置指标"""
        self.metrics = PerformanceMetrics()

class RateLimiter:
    """速率限制器"""

    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []

    async def acquire(self) -> bool:
        """获取请求许可"""
        now = time.time()

        # 清理过期请求
        self.requests = [req_time for req_time in self.requests
                        if now - req_time < self.time_window]

        # 检查是否超过限制
        if len(self.requests) >= self.max_requests:
            return False

        # 记录请求
        self.requests.append(now)
        return True

    async def wait_for_slot(self):
        """等待可用槽位"""
        while not await self.acquire():
            await asyncio.sleep(0.1)

# 全局性能优化器实例
_global_optimizer: PerformanceOptimizer | None = None

def get_global_optimizer() -> PerformanceOptimizer | None:
    """获取全局性能优化器"""
    return _global_optimizer

async def initialize_global_optimizer(config: Dict[str, Any]):
    """初始化全局性能优化器"""
    global _global_optimizer
    _global_optimizer = PerformanceOptimizer(config)
    await _global_optimizer.start()

async def shutdown_global_optimizer():
    """关闭全局性能优化器"""
    global _global_optimizer
    if _global_optimizer:
        await _global_optimizer.stop()
        _global_optimizer = None