#!/usr/bin/env python3
"""
通用爬虫核心框架
Universal Crawler Core Framework

Athena工作平台公共爬虫工具，支持多种网站的数据抓取
"""

import asyncio
import hashlib
import json
import pickle
import re
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup

from core.logging_config import setup_logging

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

@dataclass
class CrawlerConfig:
    """爬虫配置"""
    name: str
    base_url: str
    headers: dict[str, str] = None
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    rate_limit: float = 1.0  # 每秒请求数
    use_proxy: bool = False
    proxy_list: list[str] = None
    cache_enabled: bool = True
    cache_ttl: int = 3600  # 缓存时间(秒)
    user_agents: list[str] = None

    def __post_init__(self):
        if self.headers is None:
            self.headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        if self.proxy_list is None:
            self.proxy_list = []
        if self.user_agents is None:
            self.user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            ]

@dataclass
class CrawlerRequest:
    """爬虫请求"""
    url: str
    method: str = 'GET'
    params: dict[str, Any] = None
    data: dict[str, Any] = None
    headers: dict[str, str] = None
    cookies: dict[str, str] = None

@dataclass
class CrawlerResponse:
    """爬虫响应"""
    url: str
    status_code: int
    headers: dict[str, str]
    content: str
    encoding: str
    request_time: float
    cached: bool = False

class UniversalCrawler:
    """通用爬虫类"""

    def __init__(self, config: CrawlerConfig):
        """
        初始化爬虫

        Args:
            config: 爬虫配置
        """
        self.config = config
        self.session = None
        self.cache = {}
        self.last_request_time = 0
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0

        # 缓存目录
        self.cache_dir = Path('/Users/xujian/Athena工作平台/data/crawler/cache')
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()

    async def start(self):
        """启动爬虫会话"""
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=20,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )

        timeout = aiohttp.ClientTimeout(total=self.config.timeout)

        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self.config.headers
        )

        logger.info(f"爬虫 '{self.config.name}' 已启动")

    async def close(self):
        """关闭爬虫会话"""
        if self.session:
            await self.session.close()
            logger.info(f"爬虫 '{self.config.name}' 已关闭")

    def _get_cache_key(self, request: CrawlerRequest) -> str:
        """生成缓存键"""
        cache_data = {
            'url': request.url,
            'method': request.method,
            'params': request.params or {},
            'data': request.data or {}
        }
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_str.encode(), usedforsecurity=False).hexdigest()

    def _get_cache_path(self, cache_key: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / f"{cache_key}.cache"

    def _is_cache_valid(self, cache_path: Path) -> bool:
        """检查缓存是否有效"""
        if not cache_path.exists():
            return False

        file_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
        now = datetime.now()
        return (now - file_time).total_seconds() < self.config.cache_ttl

    async def _load_from_cache(self, request: CrawlerRequest) -> CrawlerResponse | None:
        """从缓存加载响应"""
        if not self.config.cache_enabled:
            return None

        cache_key = self._get_cache_key(request)
        cache_path = self._get_cache_path(cache_key)

        if self._is_cache_valid(cache_path):
            try:
                with open(cache_path, 'rb') as f:
                    cached_data = pickle.load(f)
                logger.debug(f"从缓存加载: {request.url}")
                cached_data['cached'] = True
                return CrawlerResponse(**cached_data)
            except Exception as e:
                logger.warning(f"缓存加载失败: {e}")

        return None

    async def _save_to_cache(self, request: CrawlerRequest, response: CrawlerResponse):
        """保存响应到缓存"""
        if not self.config.cache_enabled:
            return

        cache_key = self._get_cache_key(request)
        cache_path = self._get_cache_path(cache_key)

        try:
            response_dict = asdict(response)
            response_dict['cached'] = False  # 标记这不是缓存的响应
            del response_dict['cached']  # 删除临时字段

            with open(cache_path, 'wb') as f:
                pickle.dump(response_dict, f)
            logger.debug(f"保存到缓存: {request.url}")
        except Exception as e:
            logger.warning(f"缓存保存失败: {e}")

    async def _rate_limit(self):
        """速率限制"""
        now = time.time()
        time_since_last = now - self.last_request_time
        min_interval = 1.0 / self.config.rate_limit

        if time_since_last < min_interval:
            await asyncio.sleep(min_interval - time_since_last)

        self.last_request_time = time.time()

    async def fetch(self, request: CrawlerRequest) -> CrawlerResponse:
        """
        获取网页内容

        Args:
            request: 爬虫请求

        Returns:
            爬虫响应
        """
        # 检查缓存
        cached_response = await self._load_from_cache(request)
        if cached_response:
            return cached_response

        # 速率限制
        await self._rate_limit()

        # 准备请求参数
        headers = {**self.config.headers}
        if request.headers:
            headers.update(request.headers)

        # 随机选择User-Agent
        if self.config.user_agents:
            import random
            headers['User-Agent'] = random.choice(self.config.user_agents)

        retry_count = 0
        last_error = None

        while retry_count < self.config.max_retries:
            try:
                start_time = time.time()

                async with self.session.request(
                    method=request.method,
                    url=request.url,
                    params=request.params,
                    data=request.data,
                    headers=headers,
                    cookies=request.cookies,
                    proxy=self._get_proxy() if self.config.use_proxy else None
                ) as response:

                    content = await response.text()
                    request_time = time.time() - start_time

                    crawler_response = CrawlerResponse(
                        url=str(response.url),
                        status_code=response.status,
                        headers=dict(response.headers),
                        content=content,
                        encoding=response.get_encoding(),
                        request_time=request_time
                    )

                    # 保存到缓存
                    await self._save_to_cache(request, crawler_response)

                    # 更新统计
                    self.request_count += 1
                    if response.status == 200:
                        self.success_count += 1
                    else:
                        self.error_count += 1
                        logger.warning(f"请求失败: {request.url}, 状态码: {response.status}")

                    return crawler_response

            except Exception as e:
                last_error = e
                retry_count += 1
                logger.warning(f"请求失败 (尝试 {retry_count}/{self.config.max_retries}): {request.url}, 错误: {e}")

                if retry_count < self.config.max_retries:
                    await asyncio.sleep(self.config.retry_delay * retry_count)

        # 所有重试都失败了
        self.request_count += 1
        self.error_count += 1
        logger.error(f"请求最终失败: {request.url}, 错误: {last_error}")
        raise last_error

    def _get_proxy(self) -> str | None:
        """获取代理"""
        if not self.config.proxy_list:
            return None
        import random
        return random.choice(self.config.proxy_list)

    async def get_page(self, url: str, **kwargs) -> CrawlerResponse:
        """
        获取页面内容的便捷方法

        Args:
            url: 页面URL
            **kwargs: 其他请求参数

        Returns:
            爬虫响应
        """
        request = CrawlerRequest(url=url, **kwargs)
        return await self.fetch(request)

    async def get_json(self, url: str, **kwargs) -> dict[str, Any]:
        """
        获取JSON数据

        Args:
            url: API URL
            **kwargs: 其他请求参数

        Returns:
            JSON数据
        """
        response = await self.get_page(url, **kwargs)

        try:
            return json.loads(response.content)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON解析失败: {e}, 内容: {response.content[:500]}") from e

    def parse_html(self, content: str, parser: str = 'html.parser') -> BeautifulSoup:
        """
        解析HTML内容

        Args:
            content: HTML内容
            parser: 解析器类型

        Returns:
            BeautifulSoup对象
        """
        return BeautifulSoup(content, parser)

    async def extract_links(self, url: str, pattern: str = None) -> list[str]:
        """
        提取页面链接

        Args:
            url: 页面URL
            pattern: 链接匹配模式(正则表达式)

        Returns:
            链接列表
        """
        response = await self.get_page(url)
        soup = self.parse_html(response.content)

        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(url, href)

            if pattern:
                if re.search(pattern, full_url):
                    links.append(full_url)
            else:
                links.append(full_url)

        return list(set(links))  # 去重

    def get_stats(self) -> dict[str, Any]:
        """获取爬虫统计信息"""
        success_rate = (self.success_count / self.request_count * 100) if self.request_count > 0 else 0

        return {
            'name': self.config.name,
            'total_requests': self.request_count,
            'success_count': self.success_count,
            'error_count': self.error_count,
            'success_rate': f"{success_rate:.2f}%",
            'cache_enabled': self.config.cache_enabled,
            'cache_files': len(list(self.cache_dir.glob('*.cache')))
        }

    def clear_cache(self) -> None:
        """清空缓存"""
        for cache_file in self.cache_dir.glob('*.cache'):
            cache_file.unlink()
        logger.info('缓存已清空')

# 便捷函数
async def crawl_urls(urls: list[str], config: CrawlerConfig,
                      processor: Callable[[CrawlerResponse], Any] = None) -> list[Any]:
    """
    批量爬取URL列表

    Args:
        urls: URL列表
        config: 爬虫配置
        processor: 响应处理函数

    Returns:
        处理结果列表
    """
    results = []

    async with UniversalCrawler(config) as crawler:
        tasks = []
        for url in urls:
            task = crawler.get_page(url)
            tasks.append(task)

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                logger.error(f"URL爬取失败: {urls[i]}, 错误: {response}")
                results.append(None)
            else:
                if processor:
                    result = processor(response)
                    results.append(result)
                else:
                    results.append(response)

    return results
