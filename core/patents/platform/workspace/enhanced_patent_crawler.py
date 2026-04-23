#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版专利爬虫 - 集成优化技术的专利数据获取系统
Enhanced Patent Crawler - Patent Data Acquisition System with Integrated Optimization

集成代理轮换、智能重试、分布式架构的专利爬虫系统

作者: Athena AI系统
创建时间: 2025年12月6日
版本: 1.0.0
"""

import asyncio
import hashlib
import json
import logging
import re

# 导入优化爬虫模块
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urljoin, urlparse

sys.path.append('/Users/xujian/Athena工作平台/tools/optimization')
sys.path.append('/Users/xujian/Athena工作平台/tools/advanced')

from crawler_performance_optimizer import CrawlerConfig, OptimizedAsyncCrawler
from distributed_crawler import CrawlTask, DistributedCrawlerMaster
from proxy_manager import ProxyConfig, ProxyRotationManager
from resilient_crawler import CircuitBreakerConfig, ResilientAsyncCrawler, RetryConfig

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [EnhancedPatentCrawler] %(message)s',
    handlers=[
        logging.FileHandler(f'enhanced_patent_crawler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedPatentCrawler:
    """增强版专利爬虫"""

    def __init__(self, use_distributed: bool = False):
        self.use_distributed = use_distributed
        self.crawler = None
        self.master = None
        self.stats = {
            'patents_found': 0,
            'patents_processed': 0,
            'patents_failed': 0,
            'start_time': time.time()
        }

        # 专利数据源配置
        self.patent_sources = {
            'google_patents': {
                'base_url': 'https://patents.google.com',
                'search_url': 'https://patents.google.com/search',
                'priority': 1,
                'rate_limit': 0.5  # 秒
            },
            'uspto': {
                'base_url': 'https://www.uspto.gov',
                'search_url': 'https://patft.uspto.gov/netacgi/nph-Parser',
                'priority': 2,
                'rate_limit': 1.0
            },
            'espacenet': {
                'base_url': 'https://worldwide.espacenet.com',
                'search_url': 'https://worldwide.espacenet.com/searchResults',
                'priority': 3,
                'rate_limit': 0.8
            }
        }

    async def initialize(self):
        """初始化爬虫系统"""
        if self.use_distributed:
            # 分布式模式
            self.master = DistributedCrawlerMaster()
            await self.master.start()
            logger.info('🌐 分布式专利爬虫已启动')
        else:
            # 单机模式 - 使用弹性爬虫
            retry_config = RetryConfig(
                max_retries=3,
                base_delay=1.0,
                max_delay=30.0,
                retry_strategy='exponential_backoff',
                retry_on_status=[429, 500, 502, 503, 504]
            )

            circuit_config = CircuitBreakerConfig(
                failure_threshold=5,
                recovery_timeout=60.0
            )

            self.crawler = ResilientAsyncCrawler(
                retry_config=retry_config,
                circuit_breaker_config=circuit_config
            )
            await self.crawler.initialize_session()
            logger.info('🛡️ 弹性专利爬虫已启动')

    async def search_patents(self, query: str, source: str = 'google_patents',
                            limit: int = 100, **kwargs) -> List[Dict[str, Any]]:
        """搜索专利"""
        if source not in self.patent_sources:
            raise ValueError(f"不支持的数据源: {source}")

        source_config = self.patent_sources[source]
        search_urls = self._build_search_urls(query, source_config, limit, **kwargs)

        logger.info(f"🔍 开始搜索专利: '{query}' (来源: {source}, 限制: {limit})")

        if self.use_distributed:
            # 分布式处理
            task_ids = self.master.add_urls(search_urls, priority=source_config['priority'])

            # 等待任务完成
            await self._wait_for_tasks(task_ids)

            # 获取结果
            results = self.master.get_task_results(task_ids)
            patents = self._process_search_results(results, source)
        else:
            # 单机处理
            results = await self.crawler.batch_fetch(search_urls, max_concurrent=5)
            patents = self._process_crawl_results(results, source)

        self.stats['patents_found'] += len(patents)
        logger.info(f"✅ 搜索完成，找到 {len(patents)} 个专利")

        return patents

    async def get_patent_details(self, patent_url: str, source: str = 'google_patents') -> Dict[str, Any] | None]:
        """获取专利详情"""
        logger.info(f"📄 获取专利详情: {patent_url}")

        if self.use_distributed:
            # 分布式处理
            task_ids = self.master.add_urls([patent_url], priority=5)
            await self._wait_for_tasks(task_ids)
            results = self.master.get_task_results(task_ids)

            for task_id, result in results.items():
                if result['status'] == 'completed':
                    patent_data = self._parse_patent_details(result['result']['data'], source)
                    if patent_data:
                        self.stats['patents_processed'] += 1
                        return patent_data
        else:
            # 单机处理
            results = await self.crawler.batch_fetch([patent_url])
            for result in results:
                if result.get('success'):
                    patent_data = self._parse_patent_details(result['data'], source)
                    if patent_data:
                        self.stats['patents_processed'] += 1
                        return patent_data

        self.stats['patents_failed'] += 1
        logger.warning(f"⚠️ 无法获取专利详情: {patent_url}")
        return None

    def _build_search_urls(self, query: str, source_config: Dict, limit: int, **kwargs) -> List[str]:
        """构建搜索URL"""
        if source_config['base_url'] == 'https://patents.google.com':
            # Google Patents URL构建
            urls = []
            for page in range(0, limit, 10):  # 每页10个结果
                params = {
                    'q': query,
                    'oq': query,
                    'p': page,
                    'num': min(10, limit - page)
                }
                search_url = self._build_url_with_params(source_config['search_url'], params)
                urls.append(search_url)
            return urls

        elif source_config['base_url'] == 'https://patft.uspto.gov':
            # USPTO URL构建
            params = {
                'patentnumber': query,
                'Submit': 'Search'
            }
            return [self._build_url_with_params(source_config['search_url'], params)]

        else:
            # 默认搜索URL
            params = {
                'q': query,
                'limit': limit
            }
            return [self._build_url_with_params(source_config['search_url'], params)]

    def _build_url_with_params(self, base_url: str, params: Dict) -> str:
        """构建带参数的URL"""
        from urllib.parse import urlencode
        param_string = urlencode(params)
        return f"{base_url}?{param_string}"

    async def _wait_for_tasks(self, task_ids: List[str], timeout: int = 300):
        """等待任务完成"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            results = self.master.get_task_results(task_ids)

            # 检查是否所有任务都完成
            completed = all(
                result['status'] in ['completed', 'failed']
                for result in results.values()
            )

            if completed:
                break

            await asyncio.sleep(2)

    def _process_search_results(self, results: Dict[str, Any], source: str) -> List[Dict[str, Any]]:
        """处理分布式搜索结果"""
        patents = []
        for task_id, result in results.items():
            if result['status'] == 'completed' and result['result']:
                patent_links = self._extract_patent_links(result['result']['data'], source)
                patents.extend(patent_links)
        return patents

    def _process_crawl_results(self, results: List[Dict[str, Any]], source: str) -> List[Dict[str, Any]]:
        """处理爬取结果"""
        patents = []
        for result in results:
            if result.get('success'):
                patent_links = self._extract_patent_links(result['data'], source)
                patents.extend(patent_links)
        return patents

    def _extract_patent_links(self, html_content: str, source: str) -> List[Dict[str, Any]]:
        """提取专利链接"""
        patents = []

        if source == 'google_patents':
            # Google Patents链接提取
            pattern = r'<a[^>]+href='(/patent/[^']+)"[^>]*>([^<]+)</a>'
            matches = re.findall(pattern, html_content)

            for patent_url, title in matches:
                full_url = f"https://patents.google.com{patent_url}"
                patents.append({
                    'patent_url': full_url,
                    'title': title.strip(),
                    'source': source
                })

        elif source == 'uspto':
            # USPTO链接提取
            pattern = r'<a[^>]+href='([^']*patent[^']*)'[^>]*>([^<]+)</a>'
            matches = re.findall(pattern, html_content)

            for patent_url, title in matches:
                if 'uspto.gov' in patent_url:
                    patents.append({
                        'patent_url': patent_url,
                        'title': title.strip(),
                        'source': source
                    })

        return patents

    def _parse_patent_details(self, html_content: str, source: str) -> Dict[str, Any] | None]:
        """解析专利详情"""
        try:
            patent_data = {
                'source': source,
                'crawled_at': datetime.now().isoformat(),
                'raw_content': html_content[:5000]  # 保存前5000字符
            }

            if source == 'google_patents':
                # Google Patents详情解析
                title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_content)
                if title_match:
                    patent_data['title'] = title_match.group(1).strip()

                # 提取专利号
                patent_num_match = re.search(r'Patent number: ([^<\n]+)', html_content)
                if patent_num_match:
                    patent_data['patent_number'] = patent_num_match.group(1).strip()

                # 提取摘要
                abstract_match = re.search(r'<h2[^>]*>Abstract</h2>\s*<div[^>]*>(.*?)</div>', html_content, re.DOTALL)
                if abstract_match:
                    patent_data['abstract'] = abstract_match.group(1).strip()

                # 提取发明人
                inventor_match = re.search(r'Inventors?:\s*([^<\n]+)', html_content)
                if inventor_match:
                    patent_data['inventors'] = [name.strip() for name in inventor_match.group(1).split(',')]

                # 提取申请日期
                filing_date_match = re.search(r'Filing date:\s*([^<\n]+)', html_content)
                if filing_date_match:
                    patent_data['filing_date'] = filing_date_match.group(1).strip()

            elif source == 'uspto':
                # USPTO详情解析
                title_match = re.search(r'<font size="\+1"><b>([^<]+)</b></font>', html_content)
                if title_match:
                    patent_data['title'] = title_match.group(1).strip()

                # 提取专利号
                patent_num_match = re.search(r'United States Patent[^:]*:\s*([0-9,]+)', html_content)
                if patent_num_match:
                    patent_data['patent_number'] = patent_num_match.group(1).strip()

                # 提取摘要
                abstract_start = html_content.find('Abstract:')
                if abstract_start != -1:
                    abstract_end = html_content.find('\n\n', abstract_start)
                    if abstract_end != -1:
                        abstract_text = html_content[abstract_start:abstract_end].replace('Abstract:', '').strip()
                        patent_data['abstract'] = abstract_text

            # 生成专利ID
            if 'patent_number' in patent_data:
                patent_data['patent_id'] = hashlib.md5(patent_data['patent_number'].encode('utf-8'), usedforsecurity=False).hexdigest()
            else:
                patent_data['patent_id'] = hashlib.md5(html_content.encode('utf-8'), usedforsecurity=False).hexdigest()

            return patent_data

        except Exception as e:
            logger.error(f"解析专利详情时出错: {e}")
            return None

    async def batch_process_patents(self, patent_urls: List[str], source: str = 'google_patents',
                                   batch_size: int = 20) -> List[Dict[str, Any]]:
        """批量处理专利"""
        logger.info(f"📦 开始批量处理 {len(patent_urls)} 个专利")

        patents = []
        for i in range(0, len(patent_urls), batch_size):
            batch = patent_urls[i:i + batch_size]
            logger.info(f"   处理批次 {i//batch_size + 1}/{(len(patent_urls) + batch_size - 1)//batch_size}")

            if self.use_distributed:
                # 分布式处理
                task_ids = self.master.add_urls(batch, priority=3)
                await self._wait_for_tasks(task_ids, timeout=600)
                results = self.master.get_task_results(task_ids)

                for task_id, result in results.items():
                    if result['status'] == 'completed':
                        patent_data = self._parse_patent_details(result['result']['data'], source)
                        if patent_data:
                            patents.append(patent_data)
            else:
                # 单机处理
                results = await self.crawler.batch_fetch(batch, max_concurrent=5)
                for result in results:
                    if result.get('success'):
                        patent_data = self._parse_patent_details(result['data'], source)
                        if patent_data:
                            patents.append(patent_data)

        logger.info(f"✅ 批量处理完成，成功处理 {len(patents)} 个专利")
        return patents

    def get_stats(self) -> Dict[str, Any]:
        """获取爬虫统计"""
        uptime = time.time() - self.stats['start_time']

        base_stats = {
            'uptime': uptime,
            'patents_found': self.stats['patents_found'],
            'patents_processed': self.stats['patents_processed'],
            'patents_failed': self.stats['patents_failed'],
            'processing_rate': self.stats['patents_processed'] / uptime if uptime > 0 else 0
        }

        if self.use_distributed and self.master:
            base_stats['distributed_stats'] = self.master.get_master_stats()
        elif self.crawler:
            base_stats['crawler_stats'] = self.crawler.get_stats()

        return base_stats

    async def save_results(self, patents: List[Dict[str, Any]], output_file: str = None):
        """保存结果到文件"""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"patent_data_{timestamp}.json"

        output_data = {
            'export_time': datetime.now().isoformat(),
            'total_patents': len(patents),
            'stats': self.get_stats(),
            'patents': patents
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        logger.info(f"💾 专利数据已保存到: {output_file}")
        return output_file

    async def close(self):
        """关闭爬虫"""
        if self.use_distributed and self.master:
            self.master.stop()
        elif self.crawler:
            await self.crawler.close()
        logger.info('🔌 增强版专利爬虫已关闭')

async def demo_enhanced_patent_crawler():
    """演示增强版专利爬虫"""
    logger.info('🚀 增强版专利爬虫演示')
    logger.info(str('=' * 50))

    # 创建爬虫（单机模式进行演示）
    crawler = EnhancedPatentCrawler(use_distributed=False)
    await crawler.initialize()

    # 搜索示例
    search_queries = [
        'machine learning',
        'artificial intelligence',
        'blockchain'
    ]

    all_patents = []

    for query in search_queries:
        logger.info(f"\n🔍 搜索专利: {query}")
        patents = await crawler.search_patents(query, limit=20)
        logger.info(f"   找到 {len(patents)} 个专利")

        # 获取前5个专利的详情
        if patents:
            patent_urls = [p['patent_url'] for p in patents[:5]]
            details = await crawler.batch_process_patents(patent_urls)
            all_patents.extend(details)
            logger.info(f"   成功处理 {len(details)} 个专利详情")

    # 保存结果
    if all_patents:
        output_file = await crawler.save_results(all_patents)
        logger.info(f"\n💾 结果已保存到: {output_file}")

    # 显示统计
    stats = crawler.get_stats()
    logger.info(f"\n📊 爬虫统计:")
    logger.info(f"   运行时间: {stats['uptime']:.1f}秒")
    logger.info(f"   发现专利: {stats['patents_found']}")
    logger.info(f"   处理专利: {stats['patents_processed']}")
    logger.info(f"   失败专利: {stats['patents_failed']}")
    logger.info(f"   处理速率: {stats['processing_rate']:.2f} 专利/秒")

    await crawler.close()

if __name__ == '__main__':
    asyncio.run(demo_enhanced_patent_crawler())