#!/usr/bin/env python3
"""
Google Patents检索器 v2 - 使用直接URL和Playwright
"""
import asyncio
import logging
import re
from dataclasses import dataclass
from typing import List, Optional

from playwright.async_api import async_playwright

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
    publication_date: str
    url: str
    relevance_score: float = 0.0
    source: str = "google_patents"


class GooglePatentsRetrieverV2:
    """Google Patents检索器 v2"""

    def __init__(self, headless: bool = True):
        """初始化检索器"""
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.page = None
        logger.info("✅ Google Patents检索器v2初始化成功")

    async def initialize(self):
        """初始化浏览器"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        self.page = await self.browser.new_page()
        logger.info("✅ 浏览器初始化成功")

    async def search(
        self,
        query: str,
        max_results: int = 20
    ) -> List[GooglePatentResult]:
        """
        搜索Google Patents

        Args:
            query: 搜索查询
            max_results: 最大结果数

        Returns:
            检索结果列表
        """
        if not self.page:
            await self.initialize()

        logger.info(f"🔍 开始Google Patents检索: '{query}'")

        try:
            # 构建搜索URL
            search_url = f"https://patents.google.com/?q={query}&oq={query}"

            # 访问搜索页面
            await self.page.goto(search_url, wait_until='domcontentloaded', timeout=30000)

            # 等待结果加载
            await asyncio.sleep(3)

            # 尝试多个等待策略
            try:
                await self.page.wait_for_selector('[data-test="search-result"], article, .search-result', timeout=10000)
            except:
                logger.warning("⚠️ 等待搜索结果超时，继续执行...")

            # 提取结果
            results = await self._extract_results(query, max_results)

            logger.info(f"✅ 检索完成，找到 {len(results)} 条结果")
            return results

        except Exception as e:
            logger.error(f"❌ Google Patents检索失败: {e}")
            return []

    async def _extract_results(
        self,
        query: str,
        max_results: int
    ) -> List[GooglePatentResult]:
        """提取搜索结果"""
        results = []

        try:
            # 获取页面内容
            content = await self.page.content()

            # 尝试提取JavaScript渲染的数据
            js_results = await self._extract_from_js(query, max_results)
            if js_results:
                return js_results

            # 使用选择器提取结果
            selectors = [
                'article',
                '[data-test="search-result"]',
                '.search-result'
            ]

            for selector in selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        logger.info(f"✅ 找到 {len(elements)} 个结果元素（选择器: {selector}）")

                        for i, element in enumerate(elements[:max_results]):
                            result = await self._parse_element(element, query)
                            if result:
                                results.append(result)

                        if results:
                            break
                except:
                    continue

        except Exception as e:
            logger.error(f"❌ 提取结果失败: {e}")

        return results

    async def _extract_from_js(
        self,
        query: str,
        max_results: int
    ) -> List[GooglePatentResult]:
        """从JavaScript数据中提取结果"""
        results = []

        try:
            # 执行JavaScript获取数据
            data = await self.page.evaluate('''() => {
                // 尝试从window对象获取数据
                if (window.__INITIAL_STATE__) {
                    return window.__INITIAL_STATE__;
                }
                if (window.__DATA__) {
                    return window.__DATA__;
                }
                // 尝试获取所有script标签内容
                const scripts = Array.from(document.querySelectorAll('script'));
                const dataScripts = scripts
                    .map(s => s.textContent)
                    .filter(text => text.includes('searchResults') || text.includes('results'));
                return dataScripts.join('\\n');
            }''')

            if data and isinstance(data, str):
                # 解析JSON数据
                import json
                try:
                    # 尝试提取JSON对象
                    json_matches = re.findall(r'\\{[^{}]*"[^"]*results"[^{}]*\\}', data)
                    for match in json_matches[:max_results]:
                        try:
                            obj = json.loads(match)
                            # 解析结果...
                        except:
                            continue
                except:
                    pass

        except Exception as e:
            logger.debug(f"从JavaScript提取数据失败: {e}")

        return results

    async def _parse_element(
        self,
        element,
        query: str
    ) -> Optional[GooglePatentResult]:
        """解析结果元素 - 改进版"""
        try:
            # 获取元素的HTML文本
            text_content = await element.inner_text()

            # 提取专利ID - 从文本中查找
            patent_id = "UNKNOWN"
            id_patterns = [
                r'([A-Z]{2}\d+[A-Z]?)',  # US12345678B2
                r'(CN\d+[A-Z])',         # CN123456789A
                r'(EP\d+[A-Z]?)',        # EP1234567
                r'(WO\d{4}\/\d+)',       # WO2021/123456
                r'(JP\d{4,8}[A-Z]?)'     # JP12345678
            ]

            for pattern in id_patterns:
                match = re.search(pattern, text_content)
                if match:
                    patent_id = match.group(1)
                    break

            # 提取标题 - 通常是第一个文本节点
            title = "N/A"
            try:
                # 尝试多个选择器
                title_selectors = [
                    'h5',
                    'h3',
                    '[data-test="result-title"]',
                    '.title',
                    'strong'
                ]

                for selector in title_selectors:
                    title_elem = await element.query_selector(selector)
                    if title_elem:
                        title_text = await title_elem.inner_text()
                        # 清理标题，去除日期等干扰信息
                        title = title_text.split('Priority')[0].split('Filed')[0].split('•')[0].strip()
                        if len(title) > 10:  # 有效标题通常较长
                            break
            except:
                title = text_content.split('\n')[0].strip()[:100]

            # 提取摘要 - 通常是较长的文本
            abstract = ""
            try:
                # 获取所有文本并过滤
                all_text = await element.inner_text()
                lines = [line.strip() for line in all_text.split('\n') if line.strip()]

                # 找到较长的行作为摘要
                for line in lines:
                    if len(line) > 50 and not line.startswith('Priority') and not line.startswith('Filed'):
                        abstract = line
                        break
            except:
                abstract = ""

            # 提取申请人
            assignee = "Unknown"
            try:
                # 从文本中提取申请人信息
                assignee_pattern = r'([^•\n]+?)(?:Priority|Filed|Granted|Published|$)'
                matches = re.findall(assignee_pattern, text_content)
                for match in matches:
                    match = match.strip()
                    # 过滤掉日期和专利号
                    if not re.match(r'^\d{4}-\d{2}-\d{2}', match) and not re.match(r'^[A-Z]{2}\d+', match):
                        if len(match) > 2 and len(match) < 100:
                            assignee = match
                            break
            except:
                pass

            # 提取发明人
            inventors = []
            try:
                # 查找发明人模式
                inventor_pattern = r'([A-Z][a-z]+ [A-Z][a-z]+)'
                matches = re.findall(inventor_pattern, text_content)
                # 去重并限制数量
                inventors = list(set(matches))[:5]
            except:
                pass

            # 提取公开日
            publication_date = ""
            try:
                # 查找日期模式
                date_pattern = r'(\d{4}-\d{2}-\d{2})'
                dates = re.findall(date_pattern, text_content)
                if dates:
                    # 取第一个日期作为公开日
                    publication_date = dates[0]
            except:
                pass

            # 构建URL - 使用专利ID
            url = f"https://patents.google.com/patent/{patent_id}/" if patent_id != "UNKNOWN" else ""

            # 计算相关度
            relevance_score = self._calculate_relevance(title, abstract, query)

            return GooglePatentResult(
                patent_id=patent_id,
                title=title,
                abstract=abstract[:300] if abstract else "",  # 限制摘要长度
                assignee=assignee,
                inventors=inventors,
                publication_date=publication_date,
                url=url,
                relevance_score=relevance_score,
                source="google_patents"
            )

        except Exception as e:
            logger.warning(f"⚠️ 解析元素失败: {e}")
            return None

    def _extract_patent_id(self, href: str) -> str:
        """从URL提取专利ID"""
        match = re.search(r'/patent/([^/]+)', href)
        return match.group(1) if match else "UNKNOWN"

    def _calculate_relevance(self, title: str, abstract: str, query: str) -> float:
        """计算相关度分数"""
        score = 0.0
        query_lower = query.lower()

        if title:
            title_lower = title.lower()
            if query_lower in title_lower:
                score += 0.5
            if query_lower == title_lower:
                score += 0.3

        if abstract and query_lower in abstract.lower():
            score += 0.2

        return min(score, 1.0)

    async def close(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("✅ Google Patents检索器已关闭")


async def test_retriever():
    """测试检索器"""
    retriever = GooglePatentsRetrieverV2(headless=True)

    print("\n" + "="*80)
    print("🔍 Google Patents检索测试")
    print("="*80)

    try:
        results = await retriever.search("deep learning", max_results=5)

        if results:
            print(f"\n找到 {len(results)} 条结果:\n")

            for i, result in enumerate(results, 1):
                print(f"{i}. [{result.patent_id}] {result.title}")
                print(f"   申请人: {result.assignee}")
                print(f"   相关度: {result.relevance_score:.2f}")
                if result.abstract:
                    print(f"   摘要: {result.abstract[:100]}...")
                print()
        else:
            print("未找到结果（可能需要网络连接或Playwright未安装）")

    finally:
        await retriever.close()

    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_retriever())
