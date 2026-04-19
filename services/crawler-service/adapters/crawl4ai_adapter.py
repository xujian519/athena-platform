"""
Crawl4AI适配器
提供Crawl4AI的统一接口封装
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

# Crawl4AI导入
try:
    from crawl4ai import AsyncWebCrawler
    from crawl4ai.chunking_strategy import RegexChunking
    from crawl4ai.extraction_strategy import CosineStrategy, LLMExtractionStrategy
except ImportError as e:
    logging.warning(f"Crawl4AI导入失败: {e}")
    AsyncWebCrawler = None

logger = logging.getLogger(__name__)


class ExtractionMode(Enum):
    """提取模式枚举"""
    BASIC = 'basic'                    # 基础HTML提取
    AI_ENHANCED = 'ai_enhanced'        # AI增强提取
    LLM_POWERED = 'llm_powered'        # LLM驱动提取
    SEMANTIC_CHUNKING = 'semantic'     # 语义分块


@dataclass
class Crawl4AIConfig:
    """Crawl4AI配置类"""
    extraction_mode: ExtractionMode = ExtractionMode.BASIC
    use_browser: bool = False           # 是否使用浏览器渲染
    headless: bool = True              # 无头模式
    verbose: bool = False              # 详细日志
    delay_before_return_html: float = 0.5    # 返回HTML前延迟
    js_code: str | None = None      # 要执行的JS代码
    wait_for: str | None = None     # 等待的CSS选择器
    css_selector: str | None = None # CSS选择器提取
    llm_extraction_prompt: str | None = None  # LLM提取提示
    similarity_threshold: float = 0.7  # 相似度阈值
    chunk_size: int = 1000            # 分块大小
    overlap: int = 100                # 重叠大小

    # 成本控制
    max_cost_per_request: float = 0.01  # 每次请求最大成本
    enable_cost_tracking: bool = True   # 启用成本跟踪


@dataclass
class CrawlResult:
    """爬取结果数据类"""
    url: str
    success: bool
    content: str
    metadata: dict[str, Any]
    extraction_mode: str
    processing_time: float
    cost: float = 0.0
    error_message: str | None = None

    # AI增强结果
    extracted_data: dict[str, Any] | None = None
    chunks: list[dict[str, Any]] | None = None
    markdown_content: str | None = None
    links: list[dict[str, str]] | None = None
    images: list[dict[str, str]] | None = None


class Crawl4AIAdapter:
    """Crawl4AI适配器类"""

    def __init__(self, config: Crawl4AIConfig | None = None):
        self.config = config or Crawl4AIConfig()
        self.crawler = None
        self.total_cost = 0.0
        self.request_count = 0
        self.session_cost = 0.0

        if AsyncWebCrawler is None:
            raise ImportError('Crawl4AI未正确安装，请先安装: pip install crawl4ai')

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()

    async def initialize(self):
        """初始化Crawl4AI爬虫"""
        try:
            self.crawler = AsyncWebCrawler(
                headless=self.config.headless,
                verbose=self.config.verbose,
                browser_type='chromium' if self.config.use_browser else None
            )
            await self.crawler.start()
            logger.info('Crawl4AI适配器初始化成功')
        except Exception as e:
            logger.error(f"Crawl4AI适配器初始化失败: {e}")
            raise

    async def close(self):
        """关闭爬虫"""
        if self.crawler:
            await self.crawler.close()
            logger.info(f"Crawl4AI适配器已关闭，总成本: ${self.total_cost:.4f}")

    def _estimate_cost(self, result) -> float:
        """估算请求成本"""
        # 基础成本（假设每次请求基础费用）
        base_cost = 0.002

        # AI增强额外成本
        if hasattr(result, 'extracted_content') and result.extracted_content:
            base_cost += 0.003

        # LLM提取额外成本
        if hasattr(result, 'extracted_data') and result.extracted_data:
            base_cost += 0.005

        # 浏览器渲染成本
        if self.config.use_browser:
            base_cost += 0.002

        return min(base_cost, self.config.max_cost_per_request)

    def _create_extraction_strategy(self) -> Any:
        """创建提取策略"""
        if self.config.extraction_mode == ExtractionMode.LLM_POWERED:
            if not self.config.llm_extraction_prompt:
                self.config.llm_extraction_prompt = """
                从以下网页内容中提取结构化信息，包括：
                1. 标题和主要内容
                2. 关键数据和统计信息
                3. 链接和联系信息
                4. 产品或服务信息
                以JSON格式返回结果。
                """

            return LLMExtractionStrategy(
                provider='openai',
                api_token='your-token-here',  # 实际使用时需要配置
                instruction=self.config.llm_extraction_prompt,
                schema={
                    'type': 'object',
                    'properties': {
                        'title': {'type': 'string'},
                        'main_content': {'type': 'string'},
                        'key_data': {'type': 'array'},
                        'links': {'type': 'array'},
                        'contact_info': {'type': 'object'}
                    }
                }
            )

        elif self.config.extraction_mode == ExtractionMode.SEMANTIC_CHUNKING:
            return CosineStrategy(
                similarity_threshold=self.config.similarity_threshold,
                semantic_filter='principal topics, main theme'
            )

        return None

    async def crawl(self, url: str, **kwargs) -> CrawlResult:
        """执行爬取任务"""
        if not self.crawler:
            await self.initialize()

        start_time = time.time()

        # 更新配置（如果有临时参数）
        temp_config = self.config
        for key, value in kwargs.items():
            if hasattr(temp_config, key):
                setattr(temp_config, key, value)

        try:
            # 准备爬取参数
            crawl_kwargs = {
                'delay_before_return_html': temp_config.delay_before_return_html,
                'js_code': temp_config.js_code,
                'wait_for': temp_config.wait_for,
                'css_selector': temp_config.css_selector,
                'word_count_threshold': 10,
                'extraction_strategy': self._create_extraction_strategy(),
                'chunking_strategy': RegexChunking() if temp_config.extraction_mode == ExtractionMode.SEMANTIC_CHUNKING else None,
                'bypass_cache': False
            }

            # 执行爬取
            result = await self.crawler.arun(url, **crawl_kwargs)

            processing_time = time.time() - start_time

            # 估算成本
            cost = self._estimate_cost(result) if temp_config.enable_cost_tracking else 0.0
            self.total_cost += cost
            self.session_cost += cost
            self.request_count += 1

            # 构建返回结果
            crawl_result = CrawlResult(
                url=url,
                success=True,
                content=result.html if result.html else '',
                metadata={
                    'status_code': result.status_code if hasattr(result, 'status_code') else 200,
                    'response_headers': dict(result.response_headers) if hasattr(result, 'response_headers') else {},
                    'js_execution_time': result.js_execution_time if hasattr(result, 'js_execution_time') else 0,
                    'download_time': result.download_time if hasattr(result, 'download_time') else 0
                },
                extraction_mode=temp_config.extraction_mode.value,
                processing_time=processing_time,
                cost=cost,
                extracted_data=result.extracted_data if hasattr(result, 'extracted_data') else None,
                markdown_content=result.markdown if hasattr(result, 'markdown') else None,
                links=[{'url': link.get('href', ''), 'text': link.get('text', '')} for link in result.links] if hasattr(result, 'links') and result.links else None,
                images=[{'src': img.get('src', ''), 'alt': img.get('alt', '')} for img in result.images] if hasattr(result, 'images') and result.images else None
            )

            logger.info(f"成功爬取 {url}，耗时 {processing_time:.2f}s，成本 ${cost:.4f}")
            return crawl_result

        except Exception as e:
            processing_time = time.time() - start_time
            error_message = str(e)

            logger.error(f"爬取失败 {url}: {error_message}")

            return CrawlResult(
                url=url,
                success=False,
                content='',
                metadata={},
                extraction_mode=temp_config.extraction_mode.value,
                processing_time=processing_time,
                cost=0.0,
                error_message=error_message
            )

    async def batch_crawl(self, urls: list[str], max_concurrent: int = 3) -> list[CrawlResult]:
        """批量爬取"""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def crawl_with_semaphore(url: str):
            async with semaphore:
                return await self.crawl(url)

        tasks = [crawl_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常结果
        processed_results = []
        for url, result in zip(urls, results, strict=False):
            if isinstance(result, Exception):
                processed_results.append(CrawlResult(
                    url=url,
                    success=False,
                    content='',
                    metadata={},
                    extraction_mode=self.config.extraction_mode.value,
                    processing_time=0.0,
                    cost=0.0,
                    error_message=str(result)
                ))
            else:
                processed_results.append(result)

        return processed_results

    def get_usage_stats(self) -> dict[str, Any]:
        """获取使用统计"""
        return {
            'total_requests': self.request_count,
            'total_cost': self.total_cost,
            'session_cost': self.session_cost,
            'average_cost_per_request': self.total_cost / max(self.request_count, 1),
            'extraction_mode': self.config.extraction_mode.value,
            'browser_enabled': self.config.use_browser
        }

    def reset_session_stats(self) -> Any:
        """重置会话统计"""
        self.session_cost = 0.0
        logger.info('会话统计已重置')


class Crawl4AIAdapterFactory:
    """Crawl4AI适配器工厂类"""

    @staticmethod
    def create_basic_adapter() -> Crawl4AIAdapter:
        """创建基础适配器"""
        config = Crawl4AIConfig(
            extraction_mode=ExtractionMode.BASIC,
            use_browser=False,
            enable_cost_tracking=True
        )
        return Crawl4AIAdapter(config)

    @staticmethod
    def create_ai_enhanced_adapter() -> Crawl4AIAdapter:
        """创建AI增强适配器"""
        config = Crawl4AIConfig(
            extraction_mode=ExtractionMode.AI_ENHANCED,
            use_browser=True,
            delay_before_return_html=1.0,
            enable_cost_tracking=True
        )
        return Crawl4AIAdapter(config)

    @staticmethod
    def create_llm_powered_adapter(llm_prompt: str | None = None) -> Crawl4AIAdapter:
        """创建LLM驱动适配器"""
        config = Crawl4AIConfig(
            extraction_mode=ExtractionMode.LLM_POWERED,
            use_browser=True,
            delay_before_return_html=2.0,
            llm_extraction_prompt=llm_prompt,
            enable_cost_tracking=True
        )
        return Crawl4AIAdapter(config)

    @staticmethod
    def create_semantic_adapter() -> Crawl4AIAdapter:
        """创建语义分块适配器"""
        config = Crawl4AIConfig(
            extraction_mode=ExtractionMode.SEMANTIC_CHUNKING,
            use_browser=True,
            similarity_threshold=0.7,
            chunk_size=1000,
            overlap=100,
            enable_cost_tracking=True
        )
        return Crawl4AIAdapter(config)
