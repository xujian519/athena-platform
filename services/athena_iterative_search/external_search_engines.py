#!/usr/bin/env python3
"""
外部搜索引擎API实现
支持百度、Bing、搜狗等搜索引擎的API调用
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any

import aiohttp

from .types import (
    ExternalSearchResult,
    PatentMetadata,
    PatentSearchResult,
    SearchEngineType,
)

logger = logging.getLogger(__name__)

class BaseSearchEngine:
    """搜索引擎基类"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.api_key = config.get('api_key')
        self.api_secret = config.get('api_secret')
        self.base_url = config.get('base_url', '')
        self.rate_limit = config.get('rate_limit', 10)  # 每秒请求数
        self.last_request_time = 0

    async def _rate_limit(self):
        """速率限制"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        min_interval = 1.0 / self.rate_limit

        if time_since_last < min_interval:
            await asyncio.sleep(min_interval - time_since_last)

        self.last_request_time = time.time()

    def _convert_to_patent_result(self, external_result: ExternalSearchResult) -> PatentSearchResult:
        """将外部搜索结果转换为专利搜索结果"""
        patent_result = PatentSearchResult(
            title=external_result.title,
            content=external_result.snippet or external_result.content,
            url=external_result.url,
            score=external_result.score,
            engine_type=SearchEngineType.EXTERNAL_SEARCH
        )

        # 尝试从内容中提取专利信息
        patent_metadata = self._extract_patent_metadata(external_result)
        if patent_metadata:
            patent_result.patent_metadata = patent_metadata

        return patent_result

    def _extract_patent_metadata(self, result: ExternalSearchResult) -> PatentMetadata | None:
        """从搜索结果中提取专利元数据"""
        content = f"{result.title} {result.snippet or ''}"

        # 简单的专利号识别模式
        patent_patterns = [
            r'CN(\d{9}[A-Z])',  # 中国专利号
            r'US(\d{7,8}[A-Z]?)',  # 美国专利号
            r'EP(\d{7,8}[A-Z]?)',  # 欧洲专利号
            r'WO(\d{8})',  # PCT专利号
        ]

        import re
        patent_number = None

        for pattern in patent_patterns:
            match = re.search(pattern, content)
            if match:
                patent_number = match.group(0)
                break

        if patent_number:
            return PatentMetadata(
                patent_id=patent_number,
                patent_name=result.title,
                source_file=result.source_engine
            )

        return None

class BaiduSearchEngine(BaseSearchEngine):
    """百度搜索引擎API实现"""

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.base_url = 'https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/plugin'
        self.access_token = None
        self.token_expires_at = 0

    async def get_access_token(self) -> str:
        """获取百度API访问令牌"""
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token

        url = 'https://aip.baidubce.com/oauth/2.0/token'
        params = {
            'grant_type': 'client_credentials',
            'client_id': self.api_key,
            'client_secret': self.api_secret
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    self.access_token = data['access_token']
                    self.token_expires_at = time.time() + data['expires_in'] - 300  # 提前5分钟刷新
                    return self.access_token
                else:
                    raise Exception(f"百度API认证失败: {response.status}")

    async def search(self, query: str, max_results: int = 10) -> list[PatentSearchResult]:
        """执行百度搜索"""
        await self._rate_limit()

        try:
            access_token = await self.get_access_token()

            # 使用百度文心搜索插件
            url = f"{self.base_url}/web_search"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f"Bearer {access_token}"
            }

            payload = {
                'query': f"{query} 专利 技术",
                'top_num': max_results
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_baidu_response(data)
                    else:
                        logger.error(f"百度搜索API错误: {response.status}")
                        return []

        except Exception as e:
            logger.error(f"百度搜索失败: {e}")
            return []

    def _parse_baidu_response(self, data: dict) -> list[PatentSearchResult]:
        """解析百度搜索响应"""
        results = []

        if 'result' in data and 'web_search' in data['result']:
            for item in data['result']['web_search'].get('results', []):
                external_result = ExternalSearchResult(
                    title=item.get('title', ''),
                    snippet=item.get('body', ''),
                    url=item.get('url', ''),
                    source_engine='baidu',
                    display_url=item.get('url', ''),
                    last_updated=datetime.now()
                )

                patent_result = self._convert_to_patent_result(external_result)
                results.append(patent_result)

        return results

class BingSearchEngine(BaseSearchEngine):
    """Bing搜索引擎API实现"""

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.base_url = 'https://api.bing.microsoft.com/v7.0/search'

    async def search(self, query: str, max_results: int = 10) -> list[PatentSearchResult]:
        """执行Bing搜索"""
        await self._rate_limit()

        try:
            headers = {
                'Ocp-Apim-Subscription-Key': self.api_key,
                'User-Agent': 'Athena-Patent-Search/1.0'
            }

            params = {
                'q': f"{query} patent technology",
                'count': max_results,
                'freshness': 'Month',
                'mkt': 'zh-CN',
                'safe_search': 'Moderate'
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_bing_response(data)
                    else:
                        logger.error(f"Bing搜索API错误: {response.status}")
                        return []

        except Exception as e:
            logger.error(f"Bing搜索失败: {e}")
            return []

    def _parse_bing_response(self, data: dict) -> list[PatentSearchResult]:
        """解析Bing搜索响应"""
        results = []

        if 'web_pages' in data and 'value' in data['web_pages']:
            for item in data['web_pages']['value']:
                external_result = ExternalSearchResult(
                    title=item.get('name', ''),
                    snippet=item.get('snippet', ''),
                    url=item.get('url', ''),
                    source_engine='bing',
                    display_url=item.get('display_url', ''),
                    last_updated=datetime.fromisoformat(item.get('date_last_crawled', '').replace('Z', '+00:00')) if item.get('date_last_crawled') else datetime.now()
                )

                patent_result = self._convert_to_patent_result(external_result)
                results.append(patent_result)

        return results

class SogouSearchEngine(BaseSearchEngine):
    """搜狗搜索引擎API实现"""

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.base_url = 'https://api.sogou.com/sss'

    async def search(self, query: str, max_results: int = 10) -> list[PatentSearchResult]:
        """执行搜狗搜索"""
        await self._rate_limit()

        try:
            params = {
                'query': f"{query} 专利 技术",
                'num': max_results,
                'format': 'json',
                'key': self.api_key
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_sogou_response(data)
                    else:
                        logger.error(f"搜狗搜索API错误: {response.status}")
                        return []

        except Exception as e:
            logger.error(f"搜狗搜索失败: {e}")
            return []

    def _parse_sogou_response(self, data: dict) -> list[PatentSearchResult]:
        """解析搜狗搜索响应"""
        results = []

        if 'data' in data and isinstance(data['data'], list):
            for item in data['data']:
                external_result = ExternalSearchResult(
                    title=item.get('title', ''),
                    snippet=item.get('content', ''),
                    url=item.get('url', ''),
                    source_engine='sogou',
                    display_url=item.get('url', ''),
                    last_updated=datetime.now()
                )

                patent_result = self._convert_to_patent_result(external_result)
                results.append(patent_result)

        return results

class GooglePatentSearchEngine(BaseSearchEngine):
    """Google专利搜索引擎"""

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.base_url = 'https://patents.google.com'

    async def search(self, query: str, max_results: int = 10) -> list[PatentSearchResult]:
        """执行Google专利搜索"""
        await self._rate_limit()

        try:
            # Google专利搜索使用公开接口，无需API密钥
            params = {
                'q': query,
                'num': max_results,
                'language': 'zh-CN',
                'country': 'CN'
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        html = await response.text()
                        return self._parse_google_patents_html(html)
                    else:
                        logger.error(f"Google专利搜索错误: {response.status}")
                        return []

        except Exception as e:
            logger.error(f"Google专利搜索失败: {e}")
            return []

    def _parse_google_patents_html(self, html: str) -> list[PatentSearchResult]:
        """解析Google专利搜索HTML响应"""
        results = []

        # 使用简单的HTML解析提取专利信息
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')

            # 查找专利结果项
            patent_items = soup.find_all('div', class_='search-result-item')

            for item in patent_items:
                try:
                    title_elem = item.find('h3')
                    title = title_elem.get_text(strip=True) if title_elem else ''

                    link_elem = item.find('a')
                    url = link_elem.get('href') if link_elem else ''

                    # 提取专利号
                    patent_id = self._extract_patent_id_from_url(url) if url else None

                    # 提取摘要
                    snippet_elem = item.find('p', class_='snippet')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''

                    external_result = ExternalSearchResult(
                        title=title,
                        snippet=snippet,
                        url=self.base_url + url if url else '',
                        source_engine='google_patents',
                        display_url=self.base_url + url if url else '',
                        last_updated=datetime.now()
                    )

                    patent_result = self._convert_to_patent_result(external_result)
                    if patent_id:
                        patent_result.patent_id = patent_id

                    results.append(patent_result)

                except Exception as e:
                    logger.warning(f"解析单个专利结果失败: {e}")
                    continue

        except ImportError:
            logger.warning('BeautifulSoup未安装，无法解析Google专利搜索结果')
        except Exception as e:
            logger.error(f"解析Google专利搜索结果失败: {e}")

        return results

    def _extract_patent_id_from_url(self, url: str) -> str | None:
        """从URL中提取专利号"""
        import re

        # 匹配专利号模式
        patterns = [
            r'/patent/([A-Z]{2}\d+[A-Z]?)',  # 标准专利号格式
            r'/patent/(\d+)',  # 纯数字专利号
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

class ExternalSearchEngineManager:
    """外部搜索引擎管理器"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.engines = {}
        self._init_engines()

    def _init_engines(self) -> Any:
        """初始化搜索引擎"""
        engine_configs = self.config.get('external_engines', {})

        # 初始化百度搜索
        if 'baidu' in engine_configs and engine_configs['baidu'].get('enabled', False):
            self.engines['baidu'] = BaiduSearchEngine(engine_configs['baidu'])

        # 初始化Bing搜索
        if 'bing' in engine_configs and engine_configs['bing'].get('enabled', False):
            self.engines['bing'] = BingSearchEngine(engine_configs['bing'])

        # 初始化搜狗搜索
        if 'sogou' in engine_configs and engine_configs['sogou'].get('enabled', False):
            self.engines['sogou'] = SogouSearchEngine(engine_configs['sogou'])

        # 初始化Google专利搜索（默认启用）
        self.engines['google_patents'] = GooglePatentSearchEngine(engine_configs.get('google_patents', {}))

    async def search_all(self, query: str, max_results: int = 10) -> list[PatentSearchResult]:
        """并行搜索所有启用的搜索引擎"""
        if not self.engines:
            logger.warning('没有可用的外部搜索引擎')
            return []

        # 并行执行搜索
        tasks = []
        for engine_name, engine in self.engines.items():
            task = self._search_single_engine(engine_name, engine, query, max_results)
            tasks.append(task)

        results = []
        if tasks:
            search_results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(search_results):
                if isinstance(result, Exception):
                    engine_name = list(self.engines.keys())[i]
                    logger.error(f"搜索引擎 {engine_name} 搜索失败: {result}")
                elif isinstance(result, list):
                    results.extend(result)

        # 去重并按相关性排序
        results = self._deduplicate_and_rank(results)

        return results[:max_results]

    async def _search_single_engine(self, engine_name: str, engine: BaseSearchEngine, query: str, max_results: int) -> list[PatentSearchResult]:
        """单个搜索引擎搜索"""
        try:
            logger.info(f"使用 {engine_name} 搜索: {query}")
            results = await engine.search(query, max_results)
            logger.info(f"{engine_name} 搜索完成，返回 {len(results)} 条结果")
            return results
        except Exception as e:
            logger.error(f"搜索引擎 {engine_name} 搜索失败: {e}")
            return []

    def _deduplicate_and_rank(self, results: list[PatentSearchResult]) -> list[PatentSearchResult]:
        """去重并排序"""
        if not results:
            return results

        # 按URL去重
        seen_urls = set()
        deduplicated = []

        for result in results:
            url_key = result.url or result.title
            if url_key not in seen_urls:
                seen_urls.add(url_key)
                deduplicated.append(result)

        # 按分数排序
        deduplicated.sort(key=lambda x: x.score, reverse=True)

        return deduplicated

    def get_available_engines(self) -> list[str]:
        """获取可用的搜索引擎列表"""
        return list(self.engines.keys())
