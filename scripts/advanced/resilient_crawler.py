#!/usr/bin/env python3
"""
弹性爬虫 - 增强的错误重试和故障恢复机制
Resilient Crawler - Enhanced Error Retry and Failure Recovery

实现智能重试策略、故障恢复、熔断机制和自适应配置

作者: Athena AI系统
创建时间: 2025年12月6日
版本: 1.0.0
"""

import asyncio
import logging
import random
import socket
import ssl
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from urllib.parse import urlparse

import aiohttp

# 导入相关模块
from proxy_manager import ProxyConfig, ProxyRotationManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [ResilientCrawler] %(message)s',
    handlers=[
        logging.FileHandler(f"resilient_crawler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RetryStrategy(Enum):
    """重试策略枚举"""
    EXPONENTIAL_BACKOFF = 'exponential_backoff'
    LINEAR_BACKOFF = 'linear_backoff'
    FIXED_INTERVAL = 'fixed_interval'
    ADAPTIVE = 'adaptive'

class CircuitBreakerState(Enum):
    """熔断器状态"""
    CLOSED = 'closed'      # 正常状态
    OPEN = 'open'         # 熔断状态
    HALF_OPEN = 'half_open'  # 半开状态

@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    jitter: bool = True
    jitter_factor: float = 0.1
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    retry_on_status: list[int] = field(default_factory=lambda: [429, 500, 502, 503, 504])
    retry_on_exceptions: list[str] = field(default_factory=lambda: [
        'TimeoutError', 'ConnectionError', 'SSLError', 'HTTPError'
    ])

@dataclass
class CircuitBreakerConfig:
    """熔断器配置"""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    expected_exception: list[str] = field(default_factory=lambda: [
        'ConnectionError', 'TimeoutError'
    ])
    success_threshold: int = 3  # 半开状态下的成功次数阈值

class CircuitBreaker:
    """熔断器"""

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.success_count = 0

    async def call(self, func: Callable, *args, **kwargs):
        """通过熔断器调用函数"""
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                logger.info('🔄 熔断器进入半开状态')
            else:
                raise Exception('熔断器开启，拒绝调用')

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure(e)
            raise e

    def _should_attempt_reset(self) -> bool:
        """是否应该尝试重置熔断器"""
        return (self.last_failure_time and
                time.time() - self.last_failure_time >= self.config.recovery_timeout)

    def _on_success(self):
        """成功时的处理"""
        self.failure_count = 0
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.success_count = 0
                logger.info('✅ 熔断器已重置为关闭状态')

    def _on_failure(self, exception: Exception):
        """失败时的处理"""
        exception_name = type(exception).__name__
        if exception_name in self.config.expected_exception:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.config.failure_threshold:
                self.state = CircuitBreakerState.OPEN
                logger.warning(f"🚫 熔断器开启，失败次数: {self.failure_count}")

class AdaptiveRetryManager:
    """自适应重试管理器"""

    def __init__(self, config: RetryConfig):
        self.config = config
        self.domain_stats = {}
        self.global_stats = {
            'total_retries': 0,
            'successful_retries': 0,
            'failed_retries': 0
        }

    def calculate_delay(self, attempt: int, domain: str = None) -> float:
        """计算重试延迟"""
        base_delay = self.config.base_delay

        if self.config.retry_strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = base_delay * (self.config.backoff_factor ** (attempt - 1))
        elif self.config.retry_strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = base_delay * attempt
        elif self.config.retry_strategy == RetryStrategy.FIXED_INTERVAL:
            delay = base_delay
        elif self.config.retry_strategy == RetryStrategy.ADAPTIVE:
            delay = self._adaptive_delay(domain, attempt)
        else:
            delay = base_delay

        # 限制最大延迟
        delay = min(delay, self.config.max_delay)

        # 添加抖动
        if self.config.jitter:
            jitter_amount = delay * self.config.jitter_factor
            delay += random.uniform(-jitter_amount, jitter_amount)

        return max(0, delay)

    def _adaptive_delay(self, domain: str, attempt: int) -> float:
        """自适应延迟计算"""
        base_delay = self.config.base_delay

        # 基于域名统计调整
        if domain and domain in self.domain_stats:
            stats = self.domain_stats[domain]
            success_rate = stats['successes'] / (stats['successes'] + stats['failures'])

            if success_rate < 0.5:  # 成功率低，增加延迟
                factor = 2.0
            elif success_rate > 0.8:  # 成功率高，减少延迟
                factor = 0.5
            else:
                factor = 1.0
        else:
            factor = 1.0

        # 基于尝试次数调整
        return base_delay * (factor ** attempt)

    def update_stats(self, domain: str, success: bool):
        """更新统计信息"""
        if domain not in self.domain_stats:
            self.domain_stats[domain] = {'successes': 0, 'failures': 0}

        if success:
            self.domain_stats[domain]['successes'] += 1
            self.global_stats['successful_retries'] += 1
        else:
            self.domain_stats[domain]['failures'] += 1
            self.global_stats['failed_retries'] += 1

        self.global_stats['total_retries'] += 1

    def get_stats(self) -> dict[str, Any]:
        """获取重试统计"""
        return {
            'global_stats': self.global_stats.copy(),
            'domain_stats': self.domain_stats.copy(),
            'retry_success_rate': (
                self.global_stats['successful_retries'] / self.global_stats['total_retries'] * 100
                if self.global_stats['total_retries'] > 0 else 0
            )
        }

class ResilientAsyncCrawler:
    """弹性异步爬虫"""

    def __init__(self,
                 retry_config: RetryConfig = None,
                 circuit_breaker_config: CircuitBreakerConfig = None,
                 proxy_manager: ProxyRotationManager = None):
        self.retry_config = retry_config or RetryConfig()
        self.circuit_breaker_config = circuit_breaker_config or CircuitBreakerConfig()
        self.proxy_manager = proxy_manager

        # 初始化组件
        self.retry_manager = AdaptiveRetryManager(self.retry_config)
        self.circuit_breakers = {}
        self.session = None

        # 统计信息
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'retries_attempted': 0,
            'circuit_breaker_activations': 0,
            'proxy_switches': 0,
            'start_time': time.time()
        }

    async def initialize_session(self):
        """初始化HTTP会话"""
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=20,
            ttl_dns_cache=300,
            use_dns_cache=True,
            family=socket.AF_INET,
            ssl=ssl.create_default_context()
        )

        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self._get_default_headers()
        )

        logger.info('✅ 弹性HTTP会话初始化完成')

    def _get_default_headers(self) -> dict[str, str]:
        """获取默认请求头"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]

        return {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

    def _get_circuit_breaker(self, domain: str) -> CircuitBreaker:
        """获取或创建域名熔断器"""
        if domain not in self.circuit_breakers:
            self.circuit_breakers[domain] = CircuitBreaker(self.circuit_breaker_config)
        return self.circuit_breakers[domain]

    async def fetch_with_retry(self, url: str, method: str = 'GET',
                              data: dict = None, headers: dict = None) -> dict[str, Any]:
        """带重试机制的请求"""
        domain = urlparse(url).netloc
        circuit_breaker = self._get_circuit_breaker(domain)

        attempt = 0
        last_exception = None
        proxy_used = None

        while attempt < self.retry_config.max_retries + 1:
            attempt += 1
            self.stats['total_requests'] += 1

            # 选择代理
            current_proxy = None
            if self.proxy_manager and attempt > 1:  # 重试时使用代理
                current_proxy = self.proxy_manager.get_best_proxy()
                if current_proxy != proxy_used:
                    proxy_used = current_proxy
                    self.stats['proxy_switches'] += 1
                    logger.info(f"🔄 切换到代理: {current_proxy.host}:{current_proxy.port}")

            try:
                # 通过熔断器执行请求
                result = await circuit_breaker.call(
                    self._execute_request, url, method, data, headers, current_proxy
                )

                # 成功时更新统计
                if self.proxy_manager and current_proxy:
                    self.proxy_manager.release_proxy(current_proxy, True, result.get('response_time', 0))

                self.retry_manager.update_stats(domain, True)
                self.stats['successful_requests'] += 1

                return result

            except Exception as e:
                last_exception = e
                exception_name = type(e).__name__

                # 失败时处理
                if self.proxy_manager and current_proxy:
                    self.proxy_manager.release_proxy(current_proxy, False)

                # 检查是否需要重试
                if attempt <= self.retry_config.max_retries:
                    # 检查状态码是否需要重试
                    should_retry = False
                    if hasattr(e, 'status') and e.status in self.retry_config.retry_on_status:
                        should_retry = True
                    elif exception_name in self.retry_config.retry_on_exceptions:
                        should_retry = True

                    if should_retry:
                        # 计算重试延迟
                        delay = self.retry_manager.calculate_delay(attempt, domain)
                        logger.warning(f"⚠️ 请求失败 (尝试 {attempt}/{self.retry_config.max_retries + 1}): {exception_name}")
                        logger.info(f"⏱️ 等待 {delay:.2f} 秒后重试...")
                        await asyncio.sleep(delay)
                        self.stats['retries_attempted'] += 1
                        continue

                # 记录熔断器激活
                if circuit_breaker.state == CircuitBreakerState.OPEN:
                    self.stats['circuit_breaker_activations'] += 1
                    logger.warning(f"🚫 域名 {domain} 熔断器已激活")

                break

        # 所有重试都失败
        self.retry_manager.update_stats(domain, False)
        self.stats['failed_requests'] += 1

        logger.error(f"❌ 请求最终失败: {url} (尝试了 {attempt} 次)")
        return {
            'success': False,
            'error': str(last_exception),
            'url': url,
            'attempts': attempt,
            'final_exception': type(last_exception).__name__
        }

    async def _execute_request(self, url: str, method: str = 'GET',
                             data: dict = None, headers: dict = None,
                             proxy_config: ProxyConfig = None) -> dict[str, Any]:
        """执行HTTP请求"""
        start_time = time.time()

        # 准备代理
        proxy = None
        if proxy_config:
            if proxy_config.username and proxy_config.password:
                proxy = f"{proxy_config.proxy_type}://{proxy_config.username}:{proxy_config.password}@{proxy_config.host}:{proxy_config.port}"
            else:
                proxy = f"{proxy_config.proxy_type}://{proxy_config.host}:{proxy_config.port}"

        # 合并请求头
        request_headers = self._get_default_headers()
        if headers:
            request_headers.update(headers)

        async with self.session.request(
            method, url, json=data, headers=request_headers, proxy=proxy
        ) as response:
            response_time = time.time() - start_time

            if response.status == 200:
                content = await response.text()
                return {
                    'success': True,
                    'data': content,
                    'response_time': response_time,
                    'status_code': response.status,
                    'headers': dict(response.headers),
                    'proxy_used': f"{proxy_config.host}:{proxy_config.port}" if proxy_config else None
                }
            else:
                # 创建自定义异常
                error_msg = f"HTTP {response.status}"
                error = aiohttp.ClientResponseError(
                    request_info=response.request_info,
                    history=response.history,
                    status=response.status,
                    message=error_msg
                )
                raise error

    async def batch_fetch(self, urls: list[str], max_concurrent: int = 10) -> list[dict[str, Any]:
        """批量获取URLs"""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def fetch_with_semaphore(url: str) -> dict[str, Any]:
            async with semaphore:
                return await self.fetch_with_retry(url)

        logger.info(f"🚀 开始弹性批量获取 {len(urls)} 个URL")
        logger.info(f"   最大并发: {max_concurrent}")

        start_time = time.time()

        # 并发获取
        tasks = [fetch_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'success': False,
                    'error': str(result),
                    'url': urls[i] if i < len(urls) else 'unknown',
                    'attempts': 0
                })
            else:
                processed_results.append(result)

        total_time = time.time() - start_time
        successful_count = sum(1 for r in processed_results if r.get('success', False))

        logger.info("✅ 弹性批量获取完成")
        logger.info(f"   成功: {successful_count}/{len(urls)}")
        logger.info(f"   总耗时: {total_time:.2f}秒")
        logger.info(f"   平均速度: {len(urls)/total_time:.1f} URLs/秒")

        return processed_results

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        current_time = time.time()
        uptime = current_time - self.stats['start_time']

        # 基础统计
        if self.stats['total_requests'] > 0:
            success_rate = (self.stats['successful_requests'] / self.stats['total_requests']) * 100
            retry_rate = (self.stats['retries_attempted'] / self.stats['total_requests']) * 100
        else:
            success_rate = 0
            retry_rate = 0

        # 熔断器统计
        circuit_breaker_stats = {}
        for domain, breaker in self.circuit_breakers.items():
            circuit_breaker_stats[domain] = {
                'state': breaker.state.value,
                'failure_count': breaker.failure_count,
                'success_count': breaker.success_count
            }

        # 代理统计
        proxy_stats = None
        if self.proxy_manager:
            proxy_stats = self.proxy_manager.get_proxy_stats()

        return {
            'basic_stats': {
                'total_requests': self.stats['total_requests'],
                'successful_requests': self.stats['successful_requests'],
                'failed_requests': self.stats['failed_requests'],
                'success_rate': round(success_rate, 1),
                'uptime': round(uptime, 1)
            },
            'resilience_stats': {
                'retries_attempted': self.stats['retries_attempted'],
                'retry_rate': round(retry_rate, 1),
                'circuit_breaker_activations': self.stats['circuit_breaker_activations'],
                'proxy_switches': self.stats['proxy_switches']
            },
            'retry_stats': self.retry_manager.get_stats(),
            'circuit_breaker_stats': circuit_breaker_stats,
            'proxy_stats': proxy_stats
        }

    async def close(self):
        """关闭爬虫"""
        if self.session:
            await self.session.close()
            logger.info('🔌 弹性HTTP会话已关闭')

async def demo_resilient_crawler():
    """演示弹性爬虫"""
    logger.info('🛡️ 弹性爬虫演示')
    logger.info(str('=' * 50))

    # 创建配置
    retry_config = RetryConfig(
        max_retries=3,
        base_delay=1.0,
        max_delay=10.0,
        retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        jitter=True
    )

    circuit_config = CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=30.0
    )

    # 创建弹性爬虫
    crawler = ResilientAsyncCrawler(retry_config, circuit_config)
    await crawler.initialize_session()

    # 测试URLs（包含一些可能失败的URL）
    test_urls = [
        'https://httpbin.org/status/200',  # 成功
        'https://httpbin.org/status/429',  # 限流 - 会重试
        'https://httpbin.org/status/500',  # 服务器错误 - 会重试
        'https://httpbin.org/delay/5',     # 超时 - 会重试
        'https://httpbin.org/status/200',  # 成功
    ]

    logger.info(f"\n🚀 开始弹性批量获取 {len(test_urls)} 个URL")

    # 批量获取
    results = await crawler.batch_fetch(test_urls, max_concurrent=3)

    # 显示结果
    logger.info("\n📊 结果统计:")
    for i, result in enumerate(results):
        status = '✅ 成功' if result.get('success') else '❌ 失败'
        attempts = result.get('attempts', 0)
        proxy_used = result.get('proxy_used', '无')
        logger.info(f"   {i+1}. {status} (尝试{attempts}次, 代理:{proxy_used})")

    # 显示详细统计
    stats = crawler.get_stats()
    logger.info("\n📈 弹性爬虫统计:")
    logger.info(f"   总请求数: {stats['basic_stats']['total_requests']}")
    logger.info(f"   成功率: {stats['basic_stats']['success_rate']}%")
    logger.info(f"   重试率: {stats['resilience_stats']['retry_rate']}%")
    logger.info(f"   熔断器激活: {stats['resilience_stats']['circuit_breaker_activations']}次")
    logger.info(f"   代理切换: {stats['resilience_stats']['proxy_switches']}次")

    if stats['proxy_stats']:
        logger.info("\n🌐 代理统计:")
        proxy_stats = stats['proxy_stats']
        logger.info(f"   总代理数: {proxy_stats['total_proxies']}")
        logger.info(f"   健康代理: {proxy_stats['healthy_proxies']}")
        logger.info(f"   健康率: {proxy_stats['health_rate']:.1f}%")

    await crawler.close()

if __name__ == '__main__':
    asyncio.run(demo_resilient_crawler())
