#!/usr/bin/env python3
"""
外部搜索与爬虫集成系统
当外部搜索引擎或MCP失败时，自动启动爬虫进行补充搜索
作者: 小娜 & 小诺
创建时间: 2025-12-04
"""

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from crawler_auto_trigger import get_crawler_trigger

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """搜索结果"""
    success: bool
    content_type: str
    query: str
    result_count: int = 0
    items: list[dict] | None = None
    error_type: str = ''
    response_time: float = 0.0
    source: str = ''
    timestamp: str = ''

    def __post_init__(self):
        if self.items is None:
            self.items = []
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

@dataclass
class SearchConfig:
    """搜索配置"""
    enable_auto_crawler: bool = True
    crawler_timeout: int = 300
    max_crawler_retries: int = 2
    crawler_priority_threshold: float = 0.7
    search_sources: list[str] | None = None

    def __post_init__(self):
        if self.search_sources is None:
            self.search_sources = ['google_search', 'mcp_search', 'bing_search']

class SearchCrawlerIntegration:
    """搜索与爬虫集成系统"""

    def __init__(self, config: SearchConfig = None):
        """
        初始化集成系统

        Args:
            config: 搜索配置
        """
        self.config = config or SearchConfig()
        self.crawler_trigger = get_crawler_trigger()
        self.search_history = []
        self.fallback_stats = {
            'total_searches': 0,
            'successful_searches': 0,
            'crawler_triggers': 0,
            'crawler_successes': 0
        }

        logger.info('🔍 搜索与爬虫集成系统初始化完成')

    async def search_with_fallback(self, query: str, content_type: str = 'general',
                                 search_func: Callable = None, **kwargs) -> SearchResult:
        """
        带有爬虫回退的搜索功能

        Args:
            query: 搜索查询
            content_type: 内容类型 (patent, paper, general, etc.)
            search_func: 搜索函数
            **kwargs: 其他搜索参数

        Returns:
            搜索结果
        """
        start_time = time.time()
        self.fallback_stats['total_searches'] += 1

        logger.info(f"🔍 开始搜索: {query} (类型: {content_type})")

        try:
            # 尝试主要搜索方法
            if search_func:
                search_result = await self._execute_primary_search(search_func, query, **kwargs)
            else:
                search_result = await self._execute_default_search(query, content_type, **kwargs)

            search_result.response_time = time.time() - start_time

            # 检查是否需要触发爬虫
            if self._should_trigger_crawler(search_result):
                logger.info(f"🕷️ 搜索失败，触发爬虫回退: {query}")
                crawler_result = await self._trigger_crawler_fallback(query, content_type, search_result)

                # 合并结果
                if crawler_result.get('success'):
                    search_result.items.extend(crawler_result.get('items', []))
                    search_result.result_count = len(search_result.items)
                    search_result.success = True

            # 记录搜索结果
            self._record_search_result(search_result)

            if search_result.success:
                self.fallback_stats['successful_searches'] += 1
                logger.info(f"✅ 搜索成功: {len(search_result.items)} 个结果")
            else:
                logger.warning(f"⚠️ 搜索失败: {search_result.error_type}")

            return search_result

        except Exception as e:
            logger.error(f"❌ 搜索过程异常: {e}")
            return SearchResult(
                success=False,
                content_type=content_type,
                query=query,
                error_type='search_exception',
                response_time=time.time() - start_time,
                source='search_crawler_integration'
            )

    async def _execute_primary_search(self, search_func: Callable, query: str, **kwargs) -> SearchResult:
        """执行主要搜索"""
        try:
            # 执行搜索函数
            result = await search_func(query, **kwargs)

            # 转换为标准格式
            if isinstance(result, dict):
                return SearchResult(
                    success=result.get('success', True),
                    content_type=result.get('content_type', 'general'),
                    query=query,
                    result_count=result.get('result_count', len(result.get('items', []))),
                    items=result.get('items', []),
                    error_type=result.get('error_type', ''),
                    source='primary_search'
                )
            else:
                # 假设返回的是项目列表
                return SearchResult(
                    success=True,
                    content_type='general',
                    query=query,
                    result_count=len(result) if result else 0,
                    items=result if result else [],
                    source='primary_search'
                )

        except Exception as e:
            logger.error(f"❌ 主要搜索失败: {e}")
            return SearchResult(
                success=False,
                content_type='general',
                query=query,
                error_type='search_error',
                source='primary_search'
            )

    async def _execute_default_search(self, query: str, content_type: str, **kwargs) -> SearchResult:
        """执行默认搜索（模拟）"""
        # 模拟搜索延迟
        await asyncio.sleep(1)

        # 模拟搜索结果
        mock_success = kwargs.get('mock_success', True)

        if mock_success:
            mock_items = [
                {
                    'title': f"默认搜索结果 1 - {query}",
                    'url': f"https://example.com/search1?q={query}",
                    'source': 'default_search',
                    'timestamp': datetime.now().isoformat()
                }
            ]
            return SearchResult(
                success=True,
                content_type=content_type,
                query=query,
                result_count=len(mock_items),
                items=mock_items,
                source='default_search'
            )
        else:
            return SearchResult(
                success=False,
                content_type=content_type,
                query=query,
                error_type='no_results',
                source='default_search'
            )

    def _should_trigger_crawler(self, search_result: SearchResult) -> bool:
        """判断是否应该触发爬虫"""
        if not self.config.enable_auto_crawler:
            return False

        # 搜索失败
        if not search_result.success:
            return True

        # 结果为空
        if search_result.result_count == 0:
            return True

        # 响应时间过长
        if search_result.response_time > 10:
            return True

        return False

    async def _trigger_crawler_fallback(self, query: str, content_type: str,
                                       original_result: SearchResult) -> dict[str, Any]:
        """触发爬虫回退"""
        self.fallback_stats['crawler_triggers'] += 1

        # 构建触发信息
        trigger_info = {
            'content_type': content_type,
            'status': 'failed' if not original_result.success else 'no_results',
            'error_type': original_result.error_type,
            'query': query,
            'result_count': original_result.result_count,
            'response_time': original_result.response_time,
            'original_source': original_result.source
        }

        # 触发爬虫
        task = await self.crawler_trigger.check_and_trigger(trigger_info)

        if task:
            # 执行爬虫任务
            crawler_result = await self.crawler_trigger.execute_crawler_task(task['task_id'])

            if crawler_result['success']:
                self.fallback_stats['crawler_successes'] += 1
                return {
                    'success': True,
                    'items': crawler_result['result']['items'],
                    'source': 'crawler_fallback'
                }
            else:
                logger.error(f"❌ 爬虫回退失败: {crawler_result['error']}")
                return {'success': False, 'error': crawler_result['error']}
        else:
            logger.warning('⚠️ 未能创建爬虫任务')
            return {'success': False, 'error': 'no_crawler_task'}

    def _record_search_result(self, result: SearchResult):
        """记录搜索结果"""
        record = {
            'query': result.query,
            'content_type': result.content_type,
            'success': result.success,
            'result_count': result.result_count,
            'source': result.source,
            'response_time': result.response_time,
            'timestamp': result.timestamp
        }
        self.search_history.append(record)

        # 限制历史记录数量
        if len(self.search_history) > 1000:
            self.search_history = self.search_history[-500:]

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        total_searches = self.fallback_stats['total_searches']
        success_rate = self.fallback_stats['successful_searches'] / total_searches if total_searches > 0 else 0
        crawler_success_rate = self.fallback_stats['crawler_successes'] / self.fallback_stats['crawler_triggers'] if self.fallback_stats['crawler_triggers'] > 0 else 0

        return {
            'search_stats': {
                'total_searches': total_searches,
                'successful_searches': self.fallback_stats['successful_searches'],
                'success_rate': f"{success_rate:.2%}"
            },
            'crawler_stats': {
                'triggers': self.fallback_stats['crawler_triggers'],
                'successes': self.fallback_stats['crawler_successes'],
                'success_rate': f"{crawler_success_rate:.2%}"
            },
            'config': {
                'auto_crawler_enabled': self.config.enable_auto_crawler,
                'crawler_timeout': self.config.crawler_timeout,
                'max_retries': self.config.max_crawler_retries
            },
            'last_updated': datetime.now().isoformat()
        }

    def get_recent_searches(self, limit: int = 10) -> list[dict[str, Any]:
        """获取最近的搜索记录"""
        return self.search_history[-limit:]


# 便捷函数
async def enhanced_search(query: str, content_type: str = 'general',
                         search_func: Callable = None, **kwargs) -> SearchResult:
    """
    增强搜索的便捷函数

    Args:
        query: 搜索查询
        content_type: 内容类型
        search_func: 搜索函数
        **kwargs: 其他参数

    Returns:
        搜索结果
    """
    integration = SearchCrawlerIntegration()
    return await integration.search_with_fallback(query, content_type, search_func, **kwargs)


# 测试函数
async def test_integration():
    """测试搜索集成功能"""
    logger.info('🧪 测试搜索与爬虫集成功能...')

    # 模拟搜索失败的函数
    async def mock_failed_search(query: str, **kwargs):
        await asyncio.sleep(0.5)
        return {
            'success': False,
            'error_type': 'search_error',
            'items': []
        }

    # 测试1: 搜索失败，触发爬虫
    logger.info("\n1️⃣ 测试搜索失败触发爬虫...")
    result1 = await enhanced_search(
        query='artificial intelligence patent',
        content_type='patent',
        search_func=mock_failed_search
    )

    logger.info(f"   搜索成功: {result1.success}")
    logger.info(f"   结果数量: {result1.result_count}")
    logger.info(f"   结果来源: {[item.get('source', 'unknown') for item in result1.items[:3]}")

    # 测试2: 搜索成功，无需爬虫
    logger.info("\n2️⃣ 测试搜索成功无需爬虫...")

    async def mock_successful_search(query: str, **kwargs):
        await asyncio.sleep(0.3)
        return {
            'success': True,
            'items': [
                {'title': f"搜索结果 - {query}', 'url': 'https://example.com', 'source': 'search"}
            ]
        }

    result2 = await enhanced_search(
        query='machine learning',
        content_type='paper',
        search_func=mock_successful_search
    )

    logger.info(f"   搜索成功: {result2.success}")
    logger.info(f"   结果数量: {result2.result_count}")

    # 测试3: 无搜索函数，使用默认搜索
    logger.info("\n3️⃣ 测试默认搜索...")
    result3 = await enhanced_search(
        query='blockchain technology',
        content_type='general',
        mock_success=False
    )

    logger.info(f"   搜索成功: {result3.success}")
    logger.info(f"   错误类型: {result3.error_type}")

    # 显示统计信息
    integration = SearchCrawlerIntegration()
    stats = integration.get_statistics()
    logger.info("\n📊 统计信息:")
    logger.info(f"   总搜索次数: {stats['search_stats']['total_searches']}")
    logger.info(f"   搜索成功率: {stats['search_stats']['success_rate']}")
    logger.info(f"   爬虫触发次数: {stats['crawler_stats']['triggers']}")
    logger.info(f"   爬虫成功率: {stats['crawler_stats']['success_rate']}")


if __name__ == '__main__':
    asyncio.run(test_integration())
