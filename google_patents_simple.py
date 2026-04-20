#!/usr/bin/env python3
"""
Google Patents简化检索器
使用requests + BeautifulSoup实现，无需浏览器自动化
"""
import asyncio
import logging
import re
import time
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class GooglePatentResult:
    """Google Patents检索结果"""
    patent_id: str
    title: str
    abstract: str
    assignee: str
    inventors: List[str]
    filing_date: str
    publication_date: str
    url: str
    relevance_score: float = 0.0
    source: str = "google_patents"


class SimpleGooglePatentsRetriever:
    """简化的Google Patents检索器"""

    def __init__(self):
        """初始化检索器"""
        self.base_url = "https://patents.google.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        logger.info("✅ Google Patents检索器初始化成功")

    async def search(
        self,
        query: str,
        max_results: int = 20,
        language: str = "en"
    ) -> List[GooglePatentResult]:
        """
        搜索Google Patents

        Args:
            query: 搜索查询
            max_results: 最大结果数
            language: 语言代码

        Returns:
            检索结果列表
        """
        logger.info(f"🔍 开始Google Patents检索: '{query}'")

        try:
            # 构建搜索URL
            search_url = f"{self.base_url}/"
            params = {
                'q': query,
                'language': language,
                'page': 0
            }

            # 发送请求
            response = self.session.get(
                search_url,
                params=params,
                timeout=30
            )
            response.raise_for_status()

            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # 提取搜索结果
            results = self._parse_search_results(soup, query, max_results)

            logger.info(f"✅ 检索完成，找到 {len(results)} 条结果")
            return results

        except Exception as e:
            logger.error(f"❌ Google Patents检索失败: {e}")
            return []

    def _parse_search_results(
        self,
        soup: BeautifulSoup,
        query: str,
        max_results: int
    ) -> List[GooglePatentResult]:
        """
        解析搜索结果页面

        Args:
            soup: BeautifulSoup对象
            query: 搜索查询
            max_results: 最大结果数

        Returns:
            专利结果列表
        """
        results = []

        try:
            # 查找所有搜索结果项
            # Google Patents使用不同的选择器
            result_selectors = [
                'article[data-test="search-result"]',
                '[data-test="result-item"]',
                '.search-result',
                'article.result-item'
            ]

            result_elements = []
            for selector in result_selectors:
                result_elements = soup.select(selector)
                if result_elements:
                    logger.info(f"✅ 找到 {len(result_elements)} 个结果（选择器: {selector}）")
                    break

            if not result_elements:
                # 尝试通过JavaScript渲染的数据
                logger.warning("⚠️ 未找到搜索结果元素，尝试提取JavaScript数据")
                results = self._extract_from_javascript(soup, query, max_results)
                return results

            # 解析每个结果
            for i, element in enumerate(result_elements[:max_results]):
                try:
                    result = self._parse_result_element(element, query)
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.warning(f"⚠️ 解析结果 {i+1} 失败: {e}")
                    continue

        except Exception as e:
            logger.error(f"❌ 解析搜索结果失败: {e}")

        return results

    def _parse_result_element(
        self,
        element: Any,
        query: str
    ) -> Optional[GooglePatentResult]:
        """
        解析单个结果元素

        Args:
            element: BeautifulSoup元素
            query: 搜索查询

        Returns:
            专利结果或None
        """
        try:
            # 提取专利ID和链接
            link = element.select_one('a[href*="/patent/"]')
            if not link:
                return None

            href = link.get('href', '')
            patent_id = self._extract_patent_id(href)

            # 提取标题
            title_elem = element.select_one('[data-test="result-title"], .title, h5, h3')
            title = title_elem.get_text(strip=True) if title_elem else "N/A"

            # 提取摘要
            abstract_elem = element.select_one('[data-test="result-description"], .description, .abstract')
            abstract = abstract_elem.get_text(strip=True) if abstract_elem else ""

            # 提取申请人
            assignee_elem = element.select_one('[data-test="result-assignee"], .assignee')
            assignee = assignee_elem.get_text(strip=True) if assignee_elem else "Unknown"

            # 提取发明人
            inventors = []
            inventor_elems = element.select('[data-test="result-inventor"], .inventor')
            for elem in inventor_elems[:5]:  # 限制前5个发明人
                inventor = elem.get_text(strip=True)
                if inventor:
                    inventors.append(inventor)

            # 提取日期
            filing_date = ""
            publication_date = ""
            date_elems = element.select('[data-test="result-date"], .date, time')
            if date_elems:
                date_text = date_elems[0].get_text(strip=True)
                # 简单的日期解析
                if re.search(r'\\d{4}-\\d{2}-\\d{2}', date_text):
                    dates = date_text.split('~') if '~' in date_text else [date_text]
                    if len(dates) >= 2:
                        filing_date = dates[0].strip()
                        publication_date = dates[1].strip()
                    elif len(dates) == 1:
                        publication_date = dates[0].strip()

            # 构建完整URL
            url = f"{self.base_url}{href}" if href.startswith('/') else href

            # 计算相关度分数
            relevance_score = self._calculate_relevance(title, abstract, query)

            return GooglePatentResult(
                patent_id=patent_id,
                title=title,
                abstract=abstract,
                assignee=assignee,
                inventors=inventors,
                filing_date=filing_date,
                publication_date=publication_date,
                url=url,
                relevance_score=relevance_score,
                source="google_patents"
            )

        except Exception as e:
            logger.warning(f"⚠️ 解析元素失败: {e}")
            return None

    def _extract_from_javascript(
        self,
        soup: BeautifulSoup,
        query: str,
        max_results: int
    ) -> List[GooglePatentResult]:
        """
        从JavaScript数据中提取结果

        Args:
            soup: BeautifulSoup对象
            query: 搜索查询
            max_results: 最大结果数

        Returns:
            专利结果列表
        """
        results = []

        try:
            # 查找包含数据的script标签
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and ('searchResults' in script.string or 'results' in script.string):
                    # 尝试提取JSON数据
                    import json
                    try:
                        # 简单的JSON提取
                        json_pattern = r'\\{.*"results".*?\\]'
                        matches = re.findall(json_pattern, script.string, re.DOTALL)
                        for match in matches[:max_results]:
                            try:
                                data = json.loads(match)
                                # 解析数据
                                result = self._parse_json_result(data, query)
                                if result:
                                    results.append(result)
                            except:
                                continue
                    except:
                        continue

                if len(results) >= max_results:
                    break

        except Exception as e:
            logger.warning(f"⚠️ 从JavaScript提取数据失败: {e}")

        return results

    def _parse_json_result(
        self,
        data: Dict[str, Any],
        query: str
    ) -> Optional[GooglePatentResult]:
        """解析JSON格式的结果"""
        try:
            patent_id = data.get('patentId', data.get('id', ''))
            title = data.get('title', data.get('headline', ''))
            abstract = data.get('abstract', data.get('description', ''))
            assignee = data.get('assignee', data.get('owner', 'Unknown'))

            # 计算相关度
            relevance_score = self._calculate_relevance(title, abstract, query)

            return GooglePatentResult(
                patent_id=patent_id,
                title=title,
                abstract=abstract,
                assignee=assignee,
                inventors=[],
                filing_date="",
                publication_date=data.get('publicationDate', ''),
                url=f"{self.base_url}/patent/{patent_id}/" if patent_id else "",
                relevance_score=relevance_score,
                source="google_patents"
            )

        except Exception as e:
            logger.warning(f"⚠️ 解析JSON结果失败: {e}")
            return None

    def _extract_patent_id(self, href: str) -> str:
        """从URL中提取专利ID"""
        # 例如: /patent/US12345678/ -> US12345678
        match = re.search(r'/patent/([^/]+)', href)
        if match:
            return match.group(1)
        return "UNKNOWN"

    def _calculate_relevance(self, title: str, abstract: str, query: str) -> float:
        """
        计算相关度分数

        Args:
            title: 标题
            abstract: 摘要
            query: 查询

        Returns:
            相关度分数 (0-1)
        """
        score = 0.0
        query_lower = query.lower()

        # 标题匹配（权重高）
        if title:
            title_lower = title.lower()
            if query_lower in title_lower:
                score += 0.5
                # 完全匹配
                if query_lower == title_lower:
                    score += 0.3

        # 摘要匹配（权重中等）
        if abstract:
            abstract_lower = abstract.lower()
            if query_lower in abstract_lower:
                score += 0.2

        return min(score, 1.0)

    def close(self):
        """关闭会话"""
        if self.session:
            self.session.close()
            logger.info("✅ Google Patents检索器已关闭")


async def main():
    """测试Google Patents检索器"""
    retriever = SimpleGooglePatentsRetriever()

    print("\n" + "="*80)
    print("🔍 Google Patents检索测试")
    print("="*80)

    # 测试查询
    test_queries = [
        "artificial intelligence",
        "machine learning",
        "neural network"
    ]

    for query in test_queries:
        print(f"\n查询: '{query}'")
        print("-" * 80)

        results = await retriever.search(query, max_results=3)

        if results:
            print(f"找到 {len(results)} 条结果:\n")

            for i, result in enumerate(results, 1):
                print(f"{i}. [{result.patent_id}] {result.title}")
                print(f"   申请人: {result.assignee}")
                print(f"   相关度: {result.relevance_score:.2f}")
                if result.abstract:
                    print(f"   摘要: {result.abstract[:100]}...")
                print(f"   URL: {result.url}")
                print()
        else:
            print("未找到结果")

        # 礼貌延迟
        await asyncio.sleep(2)

    retriever.close()
    print("="*80)
    print("✅ 测试完成")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
