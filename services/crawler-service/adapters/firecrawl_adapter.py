# -*- coding: utf-8 -*-
"""
FireCrawl适配器
提供FireCrawl API的统一接口封装
"""

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import aiohttp

logger = logging.getLogger(__name__)


class FireCrawlMode(Enum):
    """FireCrawl爬取模式"""
    SCRAPE = 'scrape'           # 单页爬取
    CRAWL = 'crawl'             # 网站爬取
    SEARCH = 'search'           # 搜索爬取
    MAP = 'map'                 # 网站地图


@dataclass
class FireCrawlConfig:
    """FireCrawl配置类"""
    api_key: str = ''           # FireCrawl API密钥
    base_url: str = 'https://api.firecrawl.dev/v1'  # API基础URL
    mode: FireCrawlMode = FireCrawlMode.SCRAPE     # 默认模式
    timeout: int = 30          # 超时时间（秒）
    max_pages: int = 100       # 最大页面数（用于CRAWL模式）
    include_paths: List[str] = None  # 包含路径
    exclude_paths: List[str] = None  # 排除路径
    allow_backlinks: bool = False     # 允许反向链接
    ignore_sitemap: bool = False      # 忽略网站地图
    scrape_options: Dict[str, Any] = None  # 爬取选项

    # 成本控制
    max_cost_per_request: float = 0.01  # 每次请求最大成本
    enable_cost_tracking: bool = True   # 启用成本跟踪

    def __post_init__(self):
        if self.scrape_options is None:
            self.scrape_options = {
                'formats': ['markdown', 'html'],
                'include_tags': [],
                'exclude_tags': [],
                'only_main_content': True,
                'wait_for': 0,
                'screenshot': False,
                'remove_base64_images': True
            }


@dataclass
class FireCrawlResult:
    """FireCrawl爬取结果数据类"""
    url: str
    success: bool
    content: str
    markdown_content: str | None = None
    html_content: str | None = None
    metadata: Dict[str, Any] = None
    processing_time: float = 0.0
    cost: float = 0.0
    error_message: str | None = None

    # 爬取特有字段
    links: List[Dict[str, str]] = None
    images: List[Dict[str, str]] = None
    screenshot: str | None = None
    total_pages: int = 0
    crawl_id: str | None = None


class FireCrawlAdapter:
    """FireCrawl适配器类"""

    def __init__(self, config: FireCrawlConfig | None = None):
        self.config = config or FireCrawlConfig()
        self.session = None
        self.total_cost = 0.0
        self.request_count = 0
        self.session_cost = 0.0

        # 从环境变量获取API密钥（如果未提供）
        if not self.config.api_key:
            self.config.api_key = os.getenv('FIRECRAWL_API_KEY', '')

        if not self.config.api_key:
            logger.warning('未提供FireCrawl API密钥，请设置FIRECRAWL_API_KEY环境变量')

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()

    async def initialize(self):
        """初始化HTTP会话"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    'Authorization': f"Bearer {self.config.api_key}",
                    'Content-Type': 'application/json'
                }
            )
            logger.info('FireCrawl适配器初始化成功')

    async def close(self):
        """关闭HTTP会话"""
        if self.session:
            await self.session.close()
            logger.info(f"FireCrawl适配器已关闭，总成本: ${self.total_cost:.4f}")

    def _estimate_cost(self, response_data: Dict[str, Any]) -> float:
        """估算请求成本"""
        # FireCrawl定价（估算）
        # 基础爬取：$0.001-0.01/页
        # 我们使用中等估算：$0.005/页

        base_cost = 0.005

        # 如果包含截图，额外成本
        if self.config.scrape_options.get('screenshot', False):
            base_cost += 0.002

        # 如果是网站爬取，按页面数计算
        if response_data.get('total_pages', 0) > 1:
            base_cost *= response_data['total_pages']

        return min(base_cost, self.config.max_cost_per_request)

    async def _make_request(self, method: str, endpoint: str, data: Dict | None = None) -> Dict[str, Any]:
        """发起HTTP请求"""
        if not self.session:
            await self.initialize()

        url = f"{self.config.base_url}/{endpoint}"

        try:
            if method.upper() == 'GET':
                async with self.session.get(url, params=data) as response:
                    response.raise_for_status()
                    return await response.json()
            else:
                async with self.session.post(url, json=data) as response:
                    response.raise_for_status()
                    return await response.json()

        except aiohttp.ClientError as e:
            logger.error(f"HTTP请求失败: {e}")
            raise
        except Exception as e:
            logger.error(f"请求处理失败: {e}")
            raise

    async def scrape(self, url: str, **options) -> FireCrawlResult:
        """单页爬取"""
        if not self.config.api_key:
            raise ValueError('需要提供FireCrawl API密钥')

        start_time = time.time()

        # 合并爬取选项
        scrape_options = {**self.config.scrape_options, **options}

        request_data = {
            'url': url,
            **scrape_options
        }

        try:
            result_data = await self._make_request('POST', 'scrape', request_data)
            processing_time = time.time() - start_time

            # 估算成本
            cost = self._estimate_cost(result_data) if self.config.enable_cost_tracking else 0.0
            self.total_cost += cost
            self.session_cost += cost
            self.request_count += 1

            return FireCrawlResult(
                url=url,
                success=True,
                content=result_data.get('markdown', '') or result_data.get('html', ''),
                markdown_content=result_data.get('markdown'),
                html_content=result_data.get('html'),
                metadata=result_data.get('metadata', {}),
                processing_time=processing_time,
                cost=cost,
                links=result_data.get('links', []),
                images=result_data.get('images', []),
                screenshot=result_data.get('screenshot')
            )

        except Exception as e:
            processing_time = time.time() - start_time
            error_message = str(e)
            logger.error(f"FireCrawl爬取失败 {url}: {error_message}")

            return FireCrawlResult(
                url=url,
                success=False,
                content='',
                processing_time=processing_time,
                cost=0.0,
                error_message=error_message
            )

    async def crawl(self, url: str, **options) -> FireCrawlResult:
        """网站爬取"""
        if not self.config.api_key:
            raise ValueError('需要提供FireCrawl API密钥')

        start_time = time.time()

        request_data = {
            'url': url,
            'limit': options.get('limit', self.config.max_pages),
            'include_paths': options.get('include_paths', self.config.include_paths),
            'exclude_paths': options.get('exclude_paths', self.config.exclude_paths),
            'allow_backlinks': options.get('allow_backlinks', self.config.allow_backlinks),
            'ignore_sitemap': options.get('ignore_sitemap', self.config.ignore_sitemap),
            'scrape_options': {**self.config.scrape_options, **options.get('scrape_options', {})}
        }

        try:
            result_data = await self._make_request('POST', 'crawl', request_data)
            processing_time = time.time() - start_time

            # 估算成本
            cost = self._estimate_cost(result_data) if self.config.enable_cost_tracking else 0.0
            self.total_cost += cost
            self.session_cost += cost
            self.request_count += 1

            return FireCrawlResult(
                url=url,
                success=True,
                content=json.dumps(result_data, indent=2),
                metadata=result_data.get('metadata', {}),
                processing_time=processing_time,
                cost=cost,
                total_pages=result_data.get('total_pages', 0),
                crawl_id=result_data.get('id')
            )

        except Exception as e:
            processing_time = time.time() - start_time
            error_message = str(e)
            logger.error(f"FireCrawl网站爬取失败 {url}: {error_message}")

            return FireCrawlResult(
                url=url,
                success=False,
                content='',
                processing_time=processing_time,
                cost=0.0,
                error_message=error_message
            )

    async def search(self, query: str, **options) -> FireCrawlResult:
        """搜索爬取"""
        if not self.config.api_key:
            raise ValueError('需要提供FireCrawl API密钥')

        start_time = time.time()

        request_data = {
            'query': query,
            'limit': options.get('limit', 10),
            'scrape_options': {**self.config.scrape_options, **options.get('scrape_options', {})}
        }

        try:
            result_data = await self._make_request('POST', 'search', request_data)
            processing_time = time.time() - start_time

            # 估算成本
            cost = self._estimate_cost(result_data) if self.config.enable_cost_tracking else 0.0
            self.total_cost += cost
            self.session_cost += cost
            self.request_count += 1

            return FireCrawlResult(
                url=f"search://{query}",
                success=True,
                content=json.dumps(result_data, indent=2),
                metadata={'search_query': query, 'result_count': len(result_data.get('data', []))},
                processing_time=processing_time,
                cost=cost,
                total_pages=len(result_data.get('data', []))
            )

        except Exception as e:
            processing_time = time.time() - start_time
            error_message = str(e)
            logger.error(f"FireCrawl搜索失败 {query}: {error_message}")

            return FireCrawlResult(
                url=f"search://{query}",
                success=False,
                content='',
                processing_time=processing_time,
                cost=0.0,
                error_message=error_message
            )

    async def check_crawl_status(self, crawl_id: str) -> Dict[str, Any]:
        """检查爬取任务状态"""
        if not self.config.api_key:
            raise ValueError('需要提供FireCrawl API密钥')

        try:
            result_data = await self._make_request('GET', f"crawl/{crawl_id}")
            return result_data
        except Exception as e:
            logger.error(f"检查爬取状态失败 {crawl_id}: {e}")
            raise

    async def get_crawl_data(self, crawl_id: str, limit: int = 100) -> FireCrawlResult:
        """获取爬取数据"""
        if not self.config.api_key:
            raise ValueError('需要提供FireCrawl API密钥')

        start_time = time.time()

        try:
            result_data = await self._make_request('GET', f"crawl/{crawl_id}", {'limit': limit})
            processing_time = time.time() - start_time

            return FireCrawlResult(
                url=f"crawl://{crawl_id}",
                success=True,
                content=json.dumps(result_data, indent=2),
                metadata={'crawl_id': crawl_id, 'data_type': 'crawl_results'},
                processing_time=processing_time,
                cost=0.0
            )

        except Exception as e:
            processing_time = time.time() - start_time
            error_message = str(e)
            logger.error(f"获取爬取数据失败 {crawl_id}: {error_message}")

            return FireCrawlResult(
                url=f"crawl://{crawl_id}",
                success=False,
                content='',
                processing_time=processing_time,
                cost=0.0,
                error_message=error_message
            )

    async def batch_scrape(self, urls: List[str], max_concurrent: int = 3) -> List[FireCrawlResult]:
        """批量单页爬取"""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def scrape_with_semaphore(url: str):
            async with semaphore:
                return await self.scrape(url)

        tasks = [scrape_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常结果
        processed_results = []
        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                processed_results.append(FireCrawlResult(
                    url=url,
                    success=False,
                    content='',
                    processing_time=0.0,
                    cost=0.0,
                    error_message=str(result)
                ))
            else:
                processed_results.append(result)

        return processed_results

    def get_usage_stats(self) -> Dict[str, Any]:
        """获取使用统计"""
        return {
            'total_requests': self.request_count,
            'total_cost': self.total_cost,
            'session_cost': self.session_cost,
            'average_cost_per_request': self.total_cost / max(self.request_count, 1),
            'api_configured': bool(self.config.api_key),
            'base_url': self.config.base_url
        }

    def reset_session_stats(self) -> Any:
        """重置会话统计"""
        self.session_cost = 0.0
        logger.info('会话统计已重置')


class FireCrawlAdapterFactory:
    """FireCrawl适配器工厂类"""

    @staticmethod
    def create_basic_adapter(api_key: str = '') -> FireCrawlAdapter:
        """创建基础适配器"""
        config = FireCrawlConfig(
            api_key=api_key,
            mode=FireCrawlMode.SCRAPE,
            enable_cost_tracking=True
        )
        return FireCrawlAdapter(config)

    @staticmethod
    def create_crawler_adapter(api_key: str = '', max_pages: int = 100) -> FireCrawlAdapter:
        """创建网站爬取适配器"""
        config = FireCrawlConfig(
            api_key=api_key,
            mode=FireCrawlMode.CRAWL,
            max_pages=max_pages,
            enable_cost_tracking=True
        )
        return FireCrawlAdapter(config)

    @staticmethod
    def create_search_adapter(api_key: str = '') -> FireCrawlAdapter:
        """创建搜索适配器"""
        config = FireCrawlConfig(
            api_key=api_key,
            mode=FireCrawlMode.SEARCH,
            enable_cost_tracking=True
        )
        return FireCrawlAdapter(config)