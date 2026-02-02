# -*- coding: utf-8 -*-
"""
混合爬虫管理器
智能路由选择和统一管理内部爬虫、Crawl4AI、FireCrawl
"""

import asyncio
import json
import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urljoin, urlparse

from adapters.crawl4ai_adapter import (
    Crawl4AIAdapter,
    Crawl4AIAdapterFactory,
    ExtractionMode,
)
from adapters.firecrawl_adapter import FireCrawlAdapter, FireCrawlAdapterFactory

# 导入内部爬虫
from .universal_crawler import CrawlerConfig, UniversalCrawler

logger = logging.getLogger(__name__)


class CrawlerType(Enum):
    """爬虫类型枚举"""
    INTERNAL = 'internal'           # 内部爬虫
    CRAWL4AI = 'crawl4ai'           # Crawl4AI
    FIRECRAWL = 'firecrawl'         # FireCrawl


@dataclass
class RoutingDecision:
    """路由决策结果"""
    crawler_type: CrawlerType
    reason: str
    confidence: float  # 决策置信度 0-1
    estimated_cost: float
    estimated_time: float
    config_overrides: Dict[str, Any] = None


@dataclass
class HybridCrawlResult:
    """混合爬取结果"""
    url: str
    success: bool
    content: str
    metadata: Dict[str, Any]
    crawler_used: CrawlerType
    routing_decision: RoutingDecision
    processing_time: float
    cost: float
    error_message: str | None = None

    # 增强结果
    extracted_data: Optional[Dict[str, Any]] = None
    markdown_content: str | None = None
    links: Optional[List[Dict[str, str]]] = None
    images: Optional[List[Dict[str, str]]] = None


class CostLimiter:
    """成本限制器"""

    def __init__(self, monthly_limit: float = 100.0, daily_limit: float = 10.0):
        self.monthly_limit = monthly_limit
        self.daily_limit = daily_limit
        self.monthly_spent = 0.0
        self.daily_spent = 0.0
        self.usage_history = []

    def can_use_external(self, estimated_cost: float = 0.01) -> bool:
        """检查是否可以使用外部工具"""
        return (self.monthly_spent + estimated_cost <= self.monthly_limit and
                self.daily_spent + estimated_cost <= self.daily_limit)

    def record_cost(self, cost: float, crawler_type: CrawlerType) -> Any:
        """记录成本"""
        if crawler_type != CrawlerType.INTERNAL:
            self.monthly_spent += cost
            self.daily_spent += cost
            self.usage_history.append({
                'cost': cost,
                'crawler_type': crawler_type.value,
                'timestamp': asyncio.get_event_loop().time()
            })

    def get_usage_stats(self) -> Dict[str, Any]:
        """获取使用统计"""
        return {
            'monthly_spent': self.monthly_spent,
            'monthly_limit': self.monthly_limit,
            'monthly_remaining': max(0, self.monthly_limit - self.monthly_spent),
            'daily_spent': self.daily_spent,
            'daily_limit': self.daily_limit,
            'daily_remaining': max(0, self.daily_limit - self.daily_spent),
            'usage_history_count': len(self.usage_history)
        }


class HybridCrawlerManager:
    """混合爬虫管理器"""

    def __init__(self,
                 internal_config: CrawlerConfig | None = None,
                 crawl4ai_config: Dict | None = None,
                 firecrawl_config: Dict | None = None,
                 cost_limits: Dict | None = None):

        # 初始化爬虫配置
        self.internal_config = internal_config or CrawlerConfig(
            name='混合爬虫-内部',
            base_url='https://example.com'
        )

        # 初始化成本限制器
        cost_config = cost_limits or {}
        self.cost_limiter = CostLimiter(
            monthly_limit=cost_config.get('monthly_limit', 100.0),
            daily_limit=cost_config.get('daily_limit', 10.0)
        )

        # 爬虫实例（延迟初始化）
        self.internal_crawler = None
        self.crawl4ai_adapter = None
        self.firecrawl_adapter = None

        # 外部爬虫配置
        self.crawl4ai_config = crawl4ai_config or {}
        self.firecrawl_config = firecrawl_config or {}

        # 路由规则配置
        self.routing_rules = self._init_routing_rules()

        # 统计信息
        self.stats = {
            'total_requests': 0,
            'internal_usage': 0,
            'crawl4ai_usage': 0,
            'firecrawl_usage': 0,
            'routing_decisions': []
        }

    def _init_routing_rules(self) -> Dict[str, Any]:
        """初始化路由规则"""
        return {
            # JavaScript网站特征
            'js_indicators': [
                r'react\.js|vue\.js|angular\.js',
                r'\.jsx?\.|\.vue$|\.ts$',
                r'spa|single[-_]?page[-_]?application',
                r'__webpack|webpack\.json',
                r'\/api\/|\/graphql',
                r'data-react|data-vue|ng-app'
            ],

            # 需要AI提取的特征
            'ai_extraction_indicators': [
                r'product|catalog|inventory',
                r'news|article|blog',
                r'report|analysis|research',
                r'data|statistics|metrics',
                r'documentation|docs'
            ],

            # 大规模爬取特征
            'large_scale_indicators': [
                r'sitemap\.xml',
                r'robots\.txt',
                r'pagination|page=|p=\d+',
                r'category|section'
            ],

            # 简单静态网站特征
            'static_indicators': [
                r'\.html?$|\.htm$',
                r'css|bootstrap|tailwind',
                r'jquery|vanilla[-_]?js'
            ],

            # 域名规则
            'domain_rules': {
                'always_external': [
                    'linkedin.com',
                    'twitter.com',
                    'facebook.com',
                    'instagram.com'
                ],
                'prefer_internal': [
                    'github.com',
                    'stackoverflow.com',
                    'wikipedia.org'
                ]
            }
        }

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()

    async def initialize(self):
        """初始化所有爬虫实例"""
        try:
            # 初始化内部爬虫
            self.internal_crawler = UniversalCrawler(self.internal_config)

            logger.info('混合爬虫管理器初始化成功')
        except Exception as e:
            logger.error(f"混合爬虫管理器初始化失败: {e}")
            raise

    async def close(self):
        """关闭所有爬虫实例"""
        if self.internal_crawler:
            await self.internal_crawler.__aexit__(None, None, None)

        if self.crawl4ai_adapter:
            await self.crawl4ai_adapter.__aexit__(None, None, None)

        if self.firecrawl_adapter:
            await self.firecrawl_adapter.__aexit__(None, None, None)

        logger.info('混合爬虫管理器已关闭')

    def _analyze_url(self, url: str) -> Dict[str, bool]:
        """分析URL特征"""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        path = parsed.path.lower()

        analysis = {
            'is_js_heavy': False,
            'needs_ai_extraction': False,
            'is_large_scale': False,
            'is_static': False,
            'is_restricted_domain': False
        }

        # 检查JavaScript特征
        js_patterns = self.routing_rules['js_indicators']
        analysis['is_js_heavy'] = any(re.search(pattern, path, re.IGNORECASE) for pattern in js_patterns)

        # 检查AI提取需求
        ai_patterns = self.routing_rules['ai_extraction_indicators']
        analysis['needs_ai_extraction'] = any(re.search(pattern, path, re.IGNORECASE) for pattern in ai_patterns)

        # 检查大规模爬取特征
        large_patterns = self.routing_rules['large_scale_indicators']
        analysis['is_large_scale'] = any(re.search(pattern, path, re.IGNORECASE) for pattern in large_patterns)

        # 检查静态网站特征
        static_patterns = self.routing_rules['static_indicators']
        analysis['is_static'] = any(re.search(pattern, path, re.IGNORECASE) for pattern in static_patterns)

        # 检查受限域名
        domain_rules = self.routing_rules['domain_rules']
        analysis['is_restricted_domain'] = any(
            restricted in domain for restricted in domain_rules['always_external']
        )

        return analysis

    def make_routing_decision(self, url: str, strategy: str = 'auto') -> RoutingDecision:
        """制定路由决策"""
        analysis = self._analyze_url(url)

        # 策略路由
        if strategy == 'internal':
            return RoutingDecision(
                crawler_type=CrawlerType.INTERNAL,
                reason='用户指定内部爬虫',
                confidence=1.0,
                estimated_cost=0.0,
                estimated_time=2.0
            )

        elif strategy == 'crawl4ai':
            return RoutingDecision(
                crawler_type=CrawlerType.CRAWL4AI,
                reason='用户指定Crawl4AI',
                confidence=1.0,
                estimated_cost=0.008,
                estimated_time=5.0
            )

        elif strategy == 'firecrawl':
            return RoutingDecision(
                crawler_type=CrawlerType.FIRECRAWL,
                reason='用户指定FireCrawl',
                confidence=1.0,
                estimated_cost=0.005,
                estimated_time=3.0
            )

        # 自动路由决策
        if strategy == 'auto':
            # 成本检查
            if not self.cost_limiter.can_use_external():
                return RoutingDecision(
                    crawler_type=CrawlerType.INTERNAL,
                    reason='成本限制，使用内部爬虫',
                    confidence=1.0,
                    estimated_cost=0.0,
                    estimated_time=2.0
                )

            # 受限域名直接使用外部工具
            if analysis['is_restricted_domain']:
                return RoutingDecision(
                    crawler_type=CrawlerType.FIRECRAWL,
                    reason='受限域名，使用FireCrawl绕过限制',
                    confidence=0.9,
                    estimated_cost=0.005,
                    estimated_time=3.0
                )

            # JavaScript重度网站优先FireCrawl
            if analysis['is_js_heavy']:
                if analysis['needs_ai_extraction']:
                    return RoutingDecision(
                        crawler_type=CrawlerType.CRAWL4AI,
                        reason='JavaScript网站需要AI增强提取',
                        confidence=0.85,
                        estimated_cost=0.008,
                        estimated_time=5.0
                    )
                else:
                    return RoutingDecision(
                        crawler_type=CrawlerType.FIRECRAWL,
                        reason='JavaScript网站使用FireCrawl处理',
                        confidence=0.8,
                        estimated_cost=0.005,
                        estimated_time=3.0
                    )

            # 需要AI提取的网站使用Crawl4AI
            if analysis['needs_ai_extraction']:
                return RoutingDecision(
                    crawler_type=CrawlerType.CRAWL4AI,
                    reason='需要AI智能提取',
                    confidence=0.8,
                    estimated_cost=0.008,
                    estimated_time=5.0
                )

            # 大规模爬取使用FireCrawl
            if analysis['is_large_scale']:
                return RoutingDecision(
                    crawler_type=CrawlerType.FIRECRAWL,
                    reason='大规模爬取任务',
                    confidence=0.75,
                    estimated_cost=0.005,
                    estimated_time=3.0
                )

            # 默认使用内部爬虫
            return RoutingDecision(
                crawler_type=CrawlerType.INTERNAL,
                reason='标准静态网站，使用内部爬虫',
                confidence=0.7,
                estimated_cost=0.0,
                estimated_time=2.0
            )

        # 默认决策
        return RoutingDecision(
            crawler_type=CrawlerType.INTERNAL,
            reason='默认使用内部爬虫',
            confidence=0.5,
            estimated_cost=0.0,
            estimated_time=2.0
        )

    async def _get_crawler_instance(self, crawler_type: CrawlerType):
        """获取爬虫实例（延迟初始化）"""
        if crawler_type == CrawlerType.INTERNAL:
            return self.internal_crawler

        elif crawler_type == CrawlerType.CRAWL4AI:
            if not self.crawl4ai_adapter:
                factory = Crawl4AIAdapterFactory
                if self.crawl4ai_config.get('mode') == 'ai_enhanced':
                    self.crawl4ai_adapter = factory.create_ai_enhanced_adapter()
                elif self.crawl4ai_config.get('mode') == 'llm_powered':
                    prompt = self.crawl4ai_config.get('llm_prompt')
                    self.crawl4ai_adapter = factory.create_llm_powered_adapter(prompt)
                else:
                    self.crawl4ai_adapter = factory.create_basic_adapter()
                await self.crawl4ai_adapter.initialize()
            return self.crawl4ai_adapter

        elif crawler_type == CrawlerType.FIRECRAWL:
            if not self.firecrawl_adapter:
                factory = FireCrawlAdapterFactory
                api_key = self.firecrawl_config.get('api_key', '')
                mode = self.firecrawl_config.get('mode', 'scrape')

                if mode == 'search':
                    self.firecrawl_adapter = factory.create_search_adapter(api_key)
                elif mode == 'crawl':
                    max_pages = self.firecrawl_config.get('max_pages', 100)
                    self.firecrawl_adapter = factory.create_crawler_adapter(api_key, max_pages)
                else:
                    self.firecrawl_adapter = factory.create_basic_adapter(api_key)
                await self.firecrawl_adapter.initialize()
            return self.firecrawl_adapter

        else:
            raise ValueError(f"不支持的爬虫类型: {crawler_type}")

    async def crawl(self, url: str, strategy: str = 'auto', **kwargs) -> HybridCrawlResult:
        """执行智能路由爬取"""
        # 路由决策
        routing_decision = self.make_routing_decision(url, strategy)

        # 更新统计
        self.stats['total_requests'] += 1
        self.stats['routing_decisions'].append({
            'url': url,
            'decision': routing_decision.crawler_type.value,
            'reason': routing_decision.reason,
            'confidence': routing_decision.confidence
        })

        try:
            # 获取爬虫实例
            crawler = await self._get_crawler_instance(routing_decision.crawler_type)

            # 执行爬取
            if routing_decision.crawler_type == CrawlerType.INTERNAL:
                result = await crawler.get_page(url)
                content = result.content
                metadata = result.metadata
                self.stats['internal_usage'] += 1

                return HybridCrawlResult(
                    url=url,
                    success=True,
                    content=content,
                    metadata=metadata,
                    crawler_used=routing_decision.crawler_type,
                    routing_decision=routing_decision,
                    processing_time=result.metadata.get('fetch_time', 0),
                    cost=0.0
                )

            elif routing_decision.crawler_type == CrawlerType.CRAWL4AI:
                # 应用配置覆盖
                config_overrides = routing_decision.config_overrides or {}
                result = await crawler.crawl(url, **{**config_overrides, **kwargs})

                self.stats['crawl4ai_usage'] += 1
                self.cost_limiter.record_cost(result.cost, routing_decision.crawler_type)

                return HybridCrawlResult(
                    url=url,
                    success=result.success,
                    content=result.content,
                    metadata=result.metadata,
                    crawler_used=routing_decision.crawler_type,
                    routing_decision=routing_decision,
                    processing_time=result.processing_time,
                    cost=result.cost,
                    error_message=result.error_message,
                    extracted_data=result.extracted_data,
                    markdown_content=result.markdown_content,
                    links=result.links,
                    images=result.images
                )

            elif routing_decision.crawler_type == CrawlerType.FIRECRAWL:
                # 应用配置覆盖
                config_overrides = routing_decision.config_overrides or {}
                result = await crawler.scrape(url, **{**config_overrides, **kwargs})

                self.stats['firecrawl_usage'] += 1
                self.cost_limiter.record_cost(result.cost, routing_decision.crawler_type)

                return HybridCrawlResult(
                    url=url,
                    success=result.success,
                    content=result.content,
                    metadata=result.metadata,
                    crawler_used=routing_decision.crawler_type,
                    routing_decision=routing_decision,
                    processing_time=result.processing_time,
                    cost=result.cost,
                    error_message=result.error_message,
                    markdown_content=result.markdown_content,
                    links=result.links,
                    images=result.images
                )

        except Exception as e:
            error_message = str(e)
            logger.error(f"爬取失败 {url}: {error_message}")

            return HybridCrawlResult(
                url=url,
                success=False,
                content='',
                metadata={},
                crawler_used=routing_decision.crawler_type,
                routing_decision=routing_decision,
                processing_time=0.0,
                cost=0.0,
                error_message=error_message
            )

    async def batch_crawl(self, urls: List[str], strategy: str = 'auto', max_concurrent: int = 5) -> List[HybridCrawlResult]:
        """批量智能路由爬取"""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def crawl_with_semaphore(url: str):
            async with semaphore:
                return await self.crawl(url, strategy)

        tasks = [crawl_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常结果
        processed_results = []
        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                processed_results.append(HybridCrawlResult(
                    url=url,
                    success=False,
                    content='',
                    metadata={},
                    crawler_used=CrawlerType.INTERNAL,
                    routing_decision=RoutingDecision(
                        crawler_type=CrawlerType.INTERNAL,
                        reason='异常处理',
                        confidence=1.0,
                        estimated_cost=0.0,
                        estimated_time=0.0
                    ),
                    processing_time=0.0,
                    cost=0.0,
                    error_message=str(result)
                ))
            else:
                processed_results.append(result)

        return processed_results

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'routing_stats': self.stats.copy(),
            'cost_stats': self.cost_limiter.get_usage_stats(),
            'crawler_stats': {}
        }

    def reset_stats(self) -> Any:
        """重置统计信息"""
        self.stats = {
            'total_requests': 0,
            'internal_usage': 0,
            'crawl4ai_usage': 0,
            'firecrawl_usage': 0,
            'routing_decisions': []
        }
        self.cost_limiter = CostLimiter(
            monthly_limit=self.cost_limiter.monthly_limit,
            daily_limit=self.cost_limiter.daily_limit
        )
        logger.info('统计信息已重置')