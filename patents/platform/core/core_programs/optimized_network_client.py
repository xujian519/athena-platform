#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化的专利检索网络客户端
Optimized Patent Retrieval Network Client

解决Google Patents等专利数据库的访问限制问题
实现反反爬虫机制和智能重试策略

作者: 小诺 (Athena AI助手)
创建时间: 2025-12-08
版本: 1.0.0
"""

import json
import logging
import random
import time
from typing import Any, Dict, List, Optional, Union
from urllib.parse import quote, urlencode

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class OptimizedNetworkClient:
    """优化的网络访问客户端"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化网络客户端"""
        self.config = config or self._get_default_config()
        self.session = self._create_session()
        self.request_count = 0
        self.last_request_time = 0
        self.success_rate = 0.0

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'base_urls': {
                'google_patents': 'https://patents.google.com',
                'google_patents_api': 'https://patents.google.com/xhr/query'
            },
            'request_delay': {
                'min': 2.0,  # 最小延迟2秒
                'max': 5.0,  # 最大延迟5秒
                'base': 3.0   # 基础延迟3秒
            },
            'retry': {
                'max_attempts': 3,
                'backoff_factor': 2,
                'retry_on_status': [400, 429, 500, 502, 503, 504]
            },
            'timeout': {
                'connect': 10,
                'read': 15,
                'total': 30
            },
            'user_agents': [
                # Chrome on macOS
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                # Chrome on Windows
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                # Firefox on macOS
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0',
                # Safari on macOS
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15'
            ]
        }

    def _create_session(self) -> requests.Session:
        """创建优化的requests会话"""
        session = requests.Session()

        # 设置连接池
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=3
        )
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        # 设置默认超时
        session.timeout = (
            self.config['timeout']['connect'],
            self.config['timeout']['read']
        )

        return session

    def _get_random_headers(self) -> Dict[str, str]:
        """生成随机请求头"""
        user_agent = random.choice(self.config['user_agents'])

        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }

        # 添加一些浏览器特有的头
        if 'Chrome' in user_agent:
            headers.update({
                'sec-ch-ua': ''Not_A Brand';v='8', 'Chromium';v='120', 'Google Chrome';v='120'',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': ''macOS''
            })

        return headers

    def _rate_limit(self):
        """实施速率限制"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        # 计算需要的延迟时间
        base_delay = self.config['request_delay']['base']
        random_variation = random.uniform(
            self.config['request_delay']['min'],
            self.config['request_delay']['max']
        )
        required_delay = max(base_delay, random_variation)

        # 如果距离上次请求时间太短，就等待
        if time_since_last_request < required_delay:
            sleep_time = required_delay - time_since_last_request
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)

        self.last_request_time = time.time()
        self.request_count += 1

    def _make_request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> requests.Response:
        """带有重试机制的请求"""
        max_attempts = self.config['retry']['max_attempts']
        retry_on_status = self.config['retry']['retry_on_status']
        backoff_factor = self.config['retry']['backoff_factor']

        last_exception = None

        for attempt in range(max_attempts):
            try:
                # 应用速率限制
                self._rate_limit()

                # 设置随机headers
                if 'headers' not in kwargs:
                    kwargs['headers'] = {}
                kwargs['headers'].update(self._get_random_headers())

                # 发送请求
                response = self.session.request(method, url, **kwargs)

                # 检查响应状态
                if response.status_code not in retry_on_status:
                    # 更新成功率
                    if self.request_count > 0:
                        self.success_rate = (self.success_rate * (self.request_count - 1) + 1) / self.request_count
                    return response

                # 如果是需要重试的状态码
                if attempt < max_attempts - 1:
                    wait_time = backoff_factor ** attempt
                    logger.warning(
                        f"Request failed with status {response.status_code}, "
                        f"retrying in {wait_time} seconds (attempt {attempt + 1}/{max_attempts})"
                    )
                    time.sleep(wait_time)
                    continue

                # 最后一次尝试，直接返回
                return response

            except Exception as e:
                last_exception = e
                if attempt < max_attempts - 1:
                    wait_time = backoff_factor ** attempt
                    logger.warning(
                        f"Request failed with exception: {e}, "
                        f"retrying in {wait_time} seconds (attempt {attempt + 1}/{max_attempts})"
                    )
                    time.sleep(wait_time)
                    continue
                raise

        # 如果所有重试都失败了
        raise last_exception

    def search_google_patents(
        self,
        query: str,
        num_results: int = 10,
        page: int = 1
    ) -> List[Dict[str, Any]]:
        """
        优化的Google Patents搜索

        Args:
            query: 搜索关键词
            num_results: 返回结果数量
            page: 页码

        Returns:
            专利结果列表
        """
        logger.info(f"Searching Google Patents for: {query}")

        # 构建搜索URL
        encoded_query = quote(query)
        start_index = (page - 1) * num_results

        search_url = (
            f"{self.config['base_urls']['google_patents']}/"
            f"?q={encoded_query}&oq={encoded_query}"
            f"&num={num_results}&start={start_index}"
        )

        try:
            # 发送请求
            response = self._make_request_with_retry('GET', search_url)
            response.raise_for_status()

            # 解析HTML响应
            return self._parse_search_results(response.text, query)

        except Exception as e:
            logger.error(f"Failed to search Google Patents: {e}")
            return []

    def search_google_patents_api(
        self,
        query: str,
        num_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        尝试使用Google Patents API

        Args:
            query: 搜索关键词
            num_results: 返回结果数量

        Returns:
            专利结果列表
        """
        logger.info(f"Searching Google Patents API for: {query}")

        # 构建API请求
        api_url = self.config['base_urls']['google_patents_api']

        params = {
            'text': query,
            'num': num_results,
            'type': 'PATENT'
        }

        headers = {
            'Referer': self.config['base_urls']['google_patents'],
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json, text/plain, */*'
        }

        try:
            response = self._make_request_with_retry(
                'GET',
                api_url,
                params=params,
                headers=headers
            )

            # 检查响应类型
            content_type = response.headers.get('content-type', '').lower()

            if 'application/json' in content_type:
                # JSON响应
                data = response.json()
                return self._parse_api_response(data)
            else:
                # HTML响应（可能是错误页面）
                logger.warning('API returned HTML instead of JSON, falling back to web scraping')
                return self.search_google_patents(query, num_results)

        except Exception as e:
            logger.error(f"API search failed: {e}")
            # 降级到网页抓取
            return self.search_google_patents(query, num_results)

    def _parse_search_results(self, html_content: str, query: str) -> List[Dict[str, Any]]:
        """解析搜索结果页面"""
        patents = []

        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # 查找搜索结果项
            result_items = soup.find_all('div', class_='search-result-item')

            if not result_items:
                # 尝试其他可能的选择器
                result_items = soup.find_all('a', href=lambda x: x and '/patent/' in x)

            for item in result_items[:10]:  # 限制处理数量
                try:
                    patent_data = self._extract_patent_data(item)
                    if patent_data:
                        patents.append(patent_data)
                except Exception as e:
                    logger.debug(f"Failed to extract patent data: {e}")
                    continue

            logger.info(f"Found {len(patents)} patents for query: {query}")

        except Exception as e:
            logger.error(f"Failed to parse search results: {e}")

        return patents

    def _extract_patent_data(self, item) -> Dict[str, Any | None]:
        """从HTML元素中提取专利数据"""
        patent_data = {}

        try:
            # 提取标题
            title_elem = item.find('h3') or item.find('h2') or item.find('a')
            if title_elem:
                patent_data['title'] = title_elem.get_text(strip=True)

            # 提取链接
            link_elem = item.find('a', href=True)
            if link_elem:
                href = link_elem.get('href')
                if href.startswith('/'):
                    href = self.config['base_urls']['google_patents'] + href
                patent_data['url'] = href

            # 提取申请号
            number_elem = item.find(string=lambda text: text and any(
                keyword in text.lower() for keyword in ['us', 'cn', 'ep', 'wo', 'jp']
            ))
            if number_elem:
                patent_data['application_number'] = number_elem.strip()

            # 提取摘要
            abstract_elem = item.find('div', class_='abstract') or item.find('p')
            if abstract_elem:
                patent_data['abstract'] = abstract_elem.get_text(strip=True)[:200]

            # 提取日期
            date_elem = item.find(string=lambda text: text and any(
                keyword in text.lower() for keyword in ['priority', 'publication', 'filing']
            ))
            if date_elem:
                patent_data['date'] = date_elem.strip()

            # 添加来源信息
            patent_data['source'] = 'google_patents'
            patent_data['extracted_at'] = time.time()

            return patent_data if patent_data.get('title') else None

        except Exception as e:
            logger.debug(f"Failed to extract patent data from item: {e}")
            return None

    def _parse_api_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """解析API响应数据"""
        patents = []

        try:
            # 根据实际API响应格式解析
            if 'results' in data:
                results = data['results']
            elif 'patents' in data:
                results = data['patents']
            else:
                results = data

            if isinstance(results, list):
                for result in results:
                    patent_data = {
                        'title': result.get('title', ''),
                        'application_number': result.get('publication_number', ''),
                        'abstract': result.get('abstract', ''),
                        'url': result.get('url', ''),
                        'source': 'google_patents_api',
                        'extracted_at': time.time()
                    }
                    patents.append(patent_data)

        except Exception as e:
            logger.error(f"Failed to parse API response: {e}")

        return patents

    def get_statistics(self) -> Dict[str, Any]:
        """获取客户端统计信息"""
        return {
            'total_requests': self.request_count,
            'success_rate': self.success_rate,
            'last_request_time': self.last_request_time,
            'configured_delay': {
                'min': self.config['request_delay']['min'],
                'max': self.config['request_delay']['max'],
                'base': self.config['request_delay']['base']
            }
        }

# 使用示例
if __name__ == '__main__':
    # 配置日志
    logging.basicConfig(level=logging.INFO)

    # 创建客户端
    client = OptimizedNetworkClient()

    # 执行搜索
    results = client.search_google_patents('artificial intelligence', num_results=5)

    logger.info(f"找到 {len(results)} 个专利:")
    for i, patent in enumerate(results, 1):
        logger.info(f"\n{i}. {patent.get('title', 'N/A')}")
        logger.info(f"   申请号: {patent.get('application_number', 'N/A')}")
        logger.info(f"   链接: {patent.get('url', 'N/A')}")
        if 'abstract' in patent:
            logger.info(f"   摘要: {patent['abstract'][:100]}...")

    # 显示统计信息
    stats = client.get_statistics()
    logger.info(f"\n📊 统计信息: {stats}")