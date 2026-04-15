#!/usr/bin/env python3
"""
爬虫性能优化器 - Phase 1
Crawler Performance Optimizer

实现高性能并发爬虫系统，大幅提升爬取效率

作者: Athena AI系统
创建时间: 2025年12月6日
版本: 1.0.0
"""

import asyncio
import hashlib
import logging
import pickle
import random
import socket
import ssl
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

import aiohttp
import redis

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"crawler_optimization_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class CrawlerConfig:
    """爬虫配置"""
    # 并发配置
    max_concurrent: int = 100  # 最大并发数
    batch_size: int = 50     # 批处理大小
    connection_pool_size: int = 50  # 连接池大小

    # 延迟配置
    min_delay: float = 0.1      # 最小延迟(秒)
    max_delay: float = 0.5      # 最大延迟(秒)
    smart_delay: bool = True    # 智能延迟调整

    # 代理配置
    proxy_rotation: bool = True  # 代理轮换
    proxy_health_check: bool = True  # 代理健康检查

    # 缓存配置
    cache_enabled: bool = True
    cache_ttl: int = 3600  # 缓存过期时间(秒)
    cache_size_limit: int = 10000  # 缓存大小限制

    # Redis配置
    redis_enabled: bool = True
    redis_host: str = 'localhost'
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str | None = None

    # 智能延迟配置
    adaptive_delay: bool = True
    domain_specific_delays: dict[str, dict[str, float]] = field(default_factory=dict)
    machine_learning_enabled: bool = False  # 预留ML优化接口

    # 重试配置
    max_retries: int = 3
    retry_delay: float = 1.0

    # 超时配置
    request_timeout: int = 30
    connect_timeout: int = 10

    # SSL配置
    ssl_verify: bool = False  # 专利网站可能需要关闭SSL验证

class RedisCacheManager:
    """Redis缓存管理器"""

    def __init__(self, config: CrawlerConfig):
        self.config = config
        self.redis_client = None
        self.cache_prefix = 'crawler_cache:'
        self.stats_cache = 'crawler_stats'

        if config.redis_enabled:
            self._connect_redis()

    def _connect_redis(self) -> bool:
        """连接到Redis"""
        try:
            self.redis_client = redis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                db=self.config.redis_db,
                password=self.config.redis_password,
                decode_responses=False,  # 使用二进制存储
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # 测试连接
            self.redis_client.ping()
            logger.info('✅ 成功连接到Redis缓存')
            return True
        except Exception as e:
            logger.warning(f"⚠️ Redis连接失败: {e}，将使用内存缓存")
            self.redis_client = None
            return False

    def get(self, cache_key: str) -> Any | None:
        """获取缓存数据"""
        if not self.redis_client:
            return None

        try:
            data = self.redis_client.get(self.cache_prefix + cache_key)
            if data:
                # 反序列化
                cache_entry = pickle.loads(data)
                if time.time() - cache_entry['timestamp'] < self.config.cache_ttl:
                    return cache_entry['data']
                else:
                    # 过期删除
                    self.delete(cache_key)
            return None
        except Exception as e:
            logger.warning(f"Redis获取缓存失败: {e}")
            return None

    def set(self, cache_key: str, data: Any) -> bool:
        """设置缓存数据"""
        if not self.redis_client:
            return False

        try:
            cache_entry = {
                'data': data,
                'timestamp': time.time()
            }
            serialized_data = pickle.dumps(cache_entry)

            # 设置带过期时间的缓存
            self.redis_client.setex(
                self.cache_prefix + cache_key,
                self.config.cache_ttl,
                serialized_data
            )
            return True
        except Exception as e:
            logger.warning(f"Redis设置缓存失败: {e}")
            return False

    def delete(self, cache_key: str) -> bool:
        """删除缓存"""
        if not self.redis_client:
            return False

        try:
            self.redis_client.delete(self.cache_prefix + cache_key)
            return True
        except Exception as e:
            logger.warning(f"Redis删除缓存失败: {e}")
            return False

    def get_cache_stats(self) -> dict[str, Any]:
        """获取缓存统计信息"""
        if not self.redis_client:
            return {'status': 'disabled'}

        try:
            info = self.redis_client.info()
            return {
                'status': 'connected',
                'used_memory': info.get('used_memory_human', 'N/A'),
                'connected_clients': info.get('connected_clients', 0),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0)
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def clear_cache(self) -> bool:
        """清空所有缓存"""
        if not self.redis_client:
            return False

        try:
            # 删除所有带前缀的键
            pattern = self.cache_prefix + '*'
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"✅ 清除了 {len(keys)} 个缓存项")
            return True
        except Exception as e:
            logger.warning(f"清除缓存失败: {e}")
            return False

class SmartDelayManager:
    """智能延迟管理器"""

    def __init__(self, config: CrawlerConfig):
        self.config = config
        self.domain_stats = {}  # 域名统计信息
        self.delay_history = {}  # 延迟历史记录

        # 域名特定延迟配置
        self.domain_configs = {
            'google.com': {'base_delay': 2.0, 'max_delay': 5.0, 'weight': 2.0},
            'patents.google.com': {'base_delay': 1.5, 'max_delay': 3.0, 'weight': 1.8},
            'uspto.gov': {'base_delay': 1.0, 'max_delay': 2.5, 'weight': 1.5},
            'worldwide.espacenet.com': {'base_delay': 0.8, 'max_delay': 2.0, 'weight': 1.3},
            'patentscope.justia.com': {'base_delay': 0.5, 'max_delay': 1.5, 'weight': 1.0},
        }

    def update_domain_stats(self, domain: str, response_time: float, success: bool):
        """更新域名统计信息"""
        if domain not in self.domain_stats:
            self.domain_stats[domain] = {
                'success_count': 0,
                'error_count': 0,
                'total_response_time': 0,
                'request_count': 0,
                'avg_response_time': 0,
                'error_rate': 0,
                'last_request_time': 0
            }

        stats = self.domain_stats[domain]
        current_time = time.time()

        # 更新统计
        if success:
            stats['success_count'] += 1
            stats['total_response_time'] += response_time
        else:
            stats['error_count'] += 1

        stats['request_count'] += 1
        stats['last_request_time'] = current_time

        # 计算平均值
        if stats['request_count'] > 0:
            stats['avg_response_time'] = stats['total_response_time'] / stats['success_count'] if stats['success_count'] > 0 else 0
            stats['error_rate'] = stats['error_count'] / stats['request_count']

    def calculate_delay(self, domain: str, response_time: float | None = None) -> float:
        """计算智能延迟"""
        # 获取域名配置
        domain_config = self.domain_configs.get(domain, {
            'base_delay': self.config.min_delay,
            'max_delay': self.config.max_delay,
            'weight': 1.0
        })

        if not self.config.adaptive_delay:
            # 固定延迟
            return random.uniform(self.config.min_delay, self.config.max_delay)

        # 智能延迟计算
        base_delay = domain_config['base_delay']
        max_delay = domain_config['max_delay']
        weight = domain_config['weight']

        # 基于响应时间调整
        if response_time is not None:
            if response_time < 0.5:  # 快速响应，可以增加延迟避免过度请求
                delay_factor = 1.5
            elif response_time > 5.0:  # 慢速响应，可以减少延迟
                delay_factor = 0.8
            else:
                delay_factor = 1.0
        else:
            delay_factor = 1.0

        # 基于错误率调整
        if domain in self.domain_stats:
            stats = self.domain_stats[domain]
            error_rate = stats['error_rate']

            if error_rate > 0.3:  # 错误率高于30%，大幅增加延迟
                error_factor = 3.0
            elif error_rate > 0.1:  # 错误率高于10%，适度增加延迟
                error_factor = 1.5
            else:
                error_factor = 1.0
        else:
            error_factor = 1.0

        # 基于请求频率调整（避免过于频繁的请求）
        time_since_last = time.time() - self.domain_stats.get(domain, {}).get('last_request_time', 0)
        frequency_factor = max(0.5, min(2.0, time_since_last / 2.0))  # 0.5-2.0范围

        # 计算最终延迟
        calculated_delay = base_delay * delay_factor * error_factor * frequency_factor * weight

        # 添加随机性
        random_factor = random.uniform(0.8, 1.2)
        final_delay = calculated_delay * random_factor

        # 限制在合理范围内
        return max(self.config.min_delay, min(max_delay, final_delay))

    def get_domain_stats(self) -> dict[str, Any]:
        """获取域名统计信息"""
        return self.domain_stats.copy()

class OptimizedAsyncCrawler:
    """优化后的异步爬虫"""

    def __init__(self, config: CrawlerConfig = None):
        self.config = config or CrawlerConfig()
        self.session = None
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'avg_response_time': 0,
            'total_time': 0,
            'start_time': time.time()
        }

        # 缓存系统
        self.cache = {} if not config.cache_enabled else None
        self.redis_cache = RedisCacheManager(self.config) if self.config.redis_enabled else None

        # 智能延迟管理器
        self.delay_manager = SmartDelayManager(self.config)

        # SSL上下文
        self.ssl_context = ssl.create_default_context() if not self.config.ssl_verify else None

    async def initialize_session(self):
        """初始化HTTP会话"""
        timeout = aiohttp.ClientTimeout(
            total=self.config.request_timeout,
            connect=self.config.connect_timeout
        )

        # 连接器配置
        connector = aiohttp.TCPConnector(
            limit=self.config.connection_pool_size,
            limit_per_host=20,
            ttl_dns_cache=300,
            use_dns_cache=True,
            family=socket.AF_INET,
            ssl=self.ssl_context
        )

        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self._get_default_headers()
        )

        logger.info('✅ 异步HTTP会话初始化完成')
        logger.info(f"   最大并发: {self.config.max_concurrent}")
        logger.info(f"   连接池大小: {self.config.connection_pool_size}")

    def _get_default_headers(self) -> dict[str, str]:
        """获取默认请求头"""
        return {
            'User-Agent': self._get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'DNT': '1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }

    def _get_random_user_agent(self) -> str:
        """获取随机User-Agent"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/605.1.15',
        ]
        return random.choice(user_agents)

    def _get_cache_key(self, url: str, method: str = 'GET') -> str:
        """生成缓存键"""
        content = f"{method}:{url}"
        return hashlib.md5(content.encode('utf-8'), usedforsecurity=False).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Any | None:
        """从缓存获取数据（支持Redis + 内存缓存）"""
        # 首先尝试Redis缓存
        if self.redis_cache:
            cached_data = self.redis_cache.get(cache_key)
            if cached_data:
                self.stats['cache_hits'] += 1
                return cached_data

        # 回退到内存缓存
        if self.cache and cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if time.time() - cache_entry['timestamp'] < self.config.cache_ttl:
                self.stats['cache_hits'] += 1
                return cache_entry['data']
            else:
                del self.cache[cache_key]

        self.stats['cache_misses'] += 1
        return None

    def _set_cache(self, cache_key: str, data: Any) -> None:
        """设置缓存数据（支持Redis + 内存缓存）"""
        # 尝试设置Redis缓存
        redis_success = False
        if self.redis_cache:
            redis_success = self.redis_cache.set(cache_key, data)

        # 如果Redis失败或未启用，使用内存缓存
        if not redis_success and self.cache:
            # 缓存大小限制
            if len(self.cache) >= self.config.cache_size_limit:
                # 删除最旧的缓存项
                oldest_key = min(self.cache.keys(),
                               key=lambda k: self.cache[k]['timestamp'])
                del self.cache[oldest_key]

            self.cache[cache_key] = {
                'data': data,
                'timestamp': time.time()
            }

    async def _smart_delay(self, response_time: float, base_url: str, success: bool = True) -> float:
        """智能延迟计算"""
        domain = urlparse(base_url).netloc

        # 更新域名统计信息
        self.delay_manager.update_domain_stats(domain, response_time, success)

        # 计算智能延迟
        delay = self.delay_manager.calculate_delay(domain, response_time)

        return delay

    async def fetch_url(self, url: str, method: str = 'GET',
                     data: dict = None, headers: dict = None) -> dict[str, Any]:
        """获取单个URL"""
        start_time = time.time()

        # 检查缓存
        cache_key = self._get_cache_key(url, method)
        if cached_data := self._get_from_cache(cache_key):
            return {
                'success': True,
                'data': cached_data,
                'from_cache': True,
                'response_time': 0.001,
                'url': url
            }

        # 合并请求头
        request_headers = self._get_default_headers()
        if headers:
            request_headers.update(headers)

        try:
            async with self.session.request(method, url, json=data,
                                        headers=request_headers) as response:
                response_time = time.time() - start_time

                if response.status == 200:
                    content = await response.text()

                    # 保存到缓存
                    self._set_cache(cache_key, content)

                    # 智能延迟
                    delay = await self._smart_delay(response_time, url, success=True)

                    self.stats['successful_requests'] += 1
                    self.stats['total_time'] += response_time + delay

                    return {
                        'success': True,
                        'data': content,
                        'url': url,
                        'response_time': response_time,
                        'delay': delay,
                        'status_code': response.status,
                        'headers': dict(response.headers)
                    }
                else:
                    self.stats['failed_requests'] += 1
                    return {
                        'success': False,
                        'error': f"HTTP {response.status}",
                        'url': url,
                        'response_time': response_time
                    }

        except asyncio.TimeoutError:
            self.stats['failed_requests'] += 1
            return {
                'success': False,
                'error': 'Request timeout',
                'url': url,
                'response_time': self.config.request_timeout
            }
        except Exception as e:
            self.stats['failed_requests'] += 1
            return {
                'success': False,
                'error': str(e),
                'url': url,
                'response_time': time.time() - start_time
            }

        finally:
            self.stats['total_requests'] += 1

    async def batch_fetch(self, urls: list[str], batch_size: int = None) -> list[dict[str, Any]]:
        """批量获取URLs"""
        batch_size = batch_size or self.config.batch_size
        results = []

        # 创建信号量控制并发
        semaphore = asyncio.Semaphore(self.config.max_concurrent)

        async def fetch_with_semaphore(url: str) -> dict[str, Any]:
            async with semaphore:
                return await self.fetch_url(url)

        logger.info(f"🚀 开始批量获取 {len(urls)} 个URL")
        logger.info(f"   批大小: {batch_size}")
        logger.info(f"   最大并发: {self.config.max_concurrent}")

        start_time = time.time()

        # 分批处理
        for i in range(0, len(urls), batch_size):
            batch = urls[i:i + batch_size]

            logger.info(f"   处理批次 {i//batch_size + 1}/{(len(urls)+batch_size-1)//batch_size}")

            # 并发获取当前批次
            batch_tasks = [fetch_with_semaphore(url) for url in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            # 处理异常
            for result in batch_results:
                if isinstance(result, Exception):
                    results.append({
                        'success': False,
                        'error': str(result),
                        'url': 'unknown'
                    })
                else:
                    results.append(result)

        total_time = time.time() - start_time
        successful_count = sum(1 for r in results if r.get('success', False))

        logger.info("✅ 批量获取完成")
        logger.info(f"   成功: {successful_count}/{len(urls)}")
        logger.info(f"   总耗时: {total_time:.2f}秒")
        logger.info(f"   平均速度: {len(urls)/total_time:.1f} URLs/秒")

        return results

    def get_stats(self) -> dict[str, Any]:
        """获取增强的爬虫统计信息"""
        current_time = time.time()

        # 基础统计
        if self.stats['total_requests'] > 0:
            self.stats['avg_response_time'] = self.stats['total_time'] / self.stats['total_requests']
            self.stats['success_rate'] = (self.stats['successful_requests'] / self.stats['total_requests']) * 100
            # 请求速率
            self.stats['requests_per_second'] = self.stats['total_requests'] / (current_time - self.stats['start_time'])
        else:
            self.stats['avg_response_time'] = 0
            self.stats['success_rate'] = 0
            self.stats['requests_per_second'] = 0

        if self.stats['cache_hits'] + self.stats['cache_misses'] > 0:
            self.stats['cache_hit_rate'] = (self.stats['cache_hits'] / (self.stats['cache_hits'] + self.stats['cache_misses'])) * 100
        else:
            self.stats['cache_hit_rate'] = 0

        self.stats['uptime'] = current_time - self.stats['start_time']

        # 添加缓存统计
        if self.redis_cache:
            redis_stats = self.redis_cache.get_cache_stats()
            self.stats['redis_cache'] = redis_stats
        else:
            self.stats['redis_cache'] = {'status': 'disabled'}

        # 添加域名统计
        self.stats['domain_stats'] = self.delay_manager.get_domain_stats()

        # 计算性能提升估算
        cache_effectiveness = self.stats.get('cache_hit_rate', 0) / 100
        concurrency_effectiveness = min(self.config.max_concurrent / 10, 10)  # 相比串行爬虫的倍数
        estimated_speedup = 1 + (cache_effectiveness * 2) + (concurrency_effectiveness - 1)

        self.stats['performance_metrics'] = {
            'estimated_speedup': round(estimated_speedup, 1),
            'cache_effectiveness': round(cache_effectiveness * 100, 1),
            'concurrency_factor': round(concurrency_effectiveness, 1),
            'smart_delay_enabled': self.config.adaptive_delay,
            'redis_enabled': self.config.redis_enabled
        }

        return self.stats

    async def close(self):
        """关闭爬虫"""
        if self.session:
            await self.session.close()
            logger.info('🔌 HTTP会话已关闭')

async def demo_optimized_crawler():
    """演示优化后的爬虫"""
    logger.info('🚀 爬虫性能优化演示')
    logger.info(str('=' * 50))

    # 配置
    config = CrawlerConfig(
        max_concurrent=50,
        batch_size=25,
        min_delay=0.1,
        max_delay=0.3,
        cache_enabled=True,
        smart_delay=True
    )

    # 创建爬虫
    crawler = OptimizedAsyncCrawler(config)
    await crawler.initialize_session()

    # 测试URLs
    test_urls = [
        'https://patents.google.com',
        'https://www.uspto.gov',
        'https://worldwide.espacenet.com',
        'https://patentscope.justia.com'
    ]

    # 重复URLs测试缓存
    test_urls.extend(test_urls[:2])

    # 批量获取
    await crawler.batch_fetch(test_urls)

    # 显示统计
    stats = crawler.get_stats()
    logger.info("\n📊 性能统计")
    logger.info(str('-' * 30))
    logger.info(f"总请求数: {stats['total_requests']}")
    logger.info(f"成功请求数: {stats['successful_requests']}")
    logger.info(f"失败请求数: {stats['failed_requests']}")
    logger.info(f"成功率: {stats['success_rate']:.1f}%")
    logger.info(f"缓存命中率: {stats.get('cache_hit_rate', 0):.1f}%")
    logger.info(f"平均响应时间: {stats['avg_response_time']:.3f}秒")
    logger.info(f"总运行时间: {stats['uptime']:.2f}秒")

    # 缓存效果
    logger.info("\n💾 缓存效果")
    logger.info(str('-' * 30))
    logger.info(f"缓存命中: {stats['cache_hits']}")
    logger.info(f"缓存未命中: {stats['cache_misses']}")

    await crawler.close()

if __name__ == '__main__':
    asyncio.run(demo_optimized_crawler())
