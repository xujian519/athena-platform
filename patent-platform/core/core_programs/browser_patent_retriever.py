#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于浏览器自动化的专利检索器
Browser-based Patent Retriever

使用Playwright实现稳定的专利数据获取
绕过反爬虫限制，确保获取真实专利数据

作者: 小诺 (Athena AI助手)
创建时间: 2025-12-08
版本: 1.0.0
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from playwright.async_api import Browser, Page, async_playwright

logger = logging.getLogger(__name__)

@dataclass
class PatentResult:
    """专利搜索结果"""
    title: str
    application_number: str = ''
    publication_number: str = ''
    abstract: str = ''
    url: str = ''
    assignee: str = ''
    filing_date: str = ''
    publication_date: str = ''
    priority_date: str = ''
    inventors: Optional[List[str] = None
    ipc_codes: Optional[List[str] = None
    source: str = 'browser_retrieval'
    extracted_at: str = ''

    def __post_init__(self):
        if self.inventors is None:
            self.inventors = []
        if self.ipc_codes is None:
            self.ipc_codes = []
        if not self.extracted_at:
            self.extracted_at = time.strftime('%Y-%m-%d %H:%M:%S')

class BrowserPatentRetriever:
    """基于浏览器的专利检索器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化检索器"""
        self.config = config or self._get_default_config()
        self.browser = None
        self.page = None
        self.is_initialized = False

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'headless': True,
            'browser_type': 'chromium',  # chromium, firefox, webkit
            'viewport': {'width': 1920, 'height': 1080},
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'timeout': {
                'page_load': 30000,
                'element_wait': 10000,
                'search': 15000
            },
            'delays': {
                'between_searches': 3.0,
                'after_page_load': 2.0,
                'after_element_interaction': 1.0
            },
            'base_url': 'https://patents.google.com'
        }

    async def initialize(self):
        """初始化浏览器"""
        if self.is_initialized:
            return

        logger.info('初始化浏览器自动化...')
        self.playwright = await async_playwright().start()

        # 启动浏览器
        if self.config['browser_type'] == 'chromium':
            self.browser = await self.playwright.chromium.launch(
                headless=self.config['headless'],
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
        elif self.config['browser_type'] == 'firefox':
            self.browser = await self.playwright.firefox.launch(
                headless=self.config['headless']
            )
        else:
            self.browser = await self.playwright.webkit.launch(
                headless=self.config['headless']
            )

        # 创建页面
        self.page = await self.browser.new_page()

        # 设置用户代理
        await self.page.set_extra_http_headers({
            'User-Agent': self.config['user_agent']
        })

        # 设置视口
        await self.page.set_viewport_size(self.config['viewport'])

        self.is_initialized = True
        logger.info('浏览器初始化完成')

    async def search_patents(self, query: str, max_results: int = 20) -> List[PatentResult]:
        """
        搜索专利

        Args:
            query: 搜索关键词
            max_results: 最大返回结果数

        Returns:
            专利结果列表
        """
        if not self.is_initialized:
            await self.initialize()

        logger.info(f"开始搜索专利: {query}")

        try:
            # 构建搜索URL
            encoded_query = quote(query)
            search_url = f"{self.config['base_url']}/?q={encoded_query}&oq={encoded_query}"

            # 访问搜索页面
            await self.page.goto(search_url, timeout=self.config['timeout']['page_load'])

            # 等待页面加载
            await self.page.wait_for_timeout(self.config['delays']['after_page_load'])

            # 等待搜索结果加载
            await self._wait_for_search_results()

            # 提取搜索结果
            results = await self._extract_search_results(max_results)

            logger.info(f"找到 {len(results)} 个专利结果")
            return results

        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []

    async def _wait_for_search_results(self):
        """等待搜索结果加载"""
        try:
            # 等待搜索结果容器出现
            await self.page.wait_for_selector(
                '.search-results, .result-list, .search-result-item',
                timeout=self.config['timeout']['search']
            )
        except Exception as e:
            logger.debug(f"等待搜索结果超时，尝试继续解析: {e}")

    async def _extract_search_results(self, max_results: int) -> List[PatentResult]:
        """提取搜索结果"""
        results = []

        try:
            # 查找搜索结果项 - 使用多种可能的选择器
            result_selectors = [
                'div.search-result-item',
                "a[href*='/patent/']",
                '.result-item',
                '.search-result',
                '[data-result-id]'
            ]

            result_elements = []
            for selector in result_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        result_elements = elements
                        logger.debug(f"使用选择器 '{selector}' 找到 {len(elements)} 个结果")
                        break
                except:
                    continue

            # 如果还是找不到，尝试查找包含专利链接的元素
            if not result_elements:
                result_elements = await self.page.query_selector_all("a[href*='/patent/']")

            logger.info(f"找到 {len(result_elements)} 个结果元素")

            # 提取每个结果的信息
            for i, element in enumerate(result_elements[:max_results]):
                try:
                    patent = await self._extract_patent_data(element)
                    if patent:
                        results.append(patent)
                        logger.debug(f"成功提取第 {i+1} 个专利: {patent.title[:50]}...")
                except Exception as e:
                    logger.debug(f"提取第 {i+1} 个专利失败: {e}")
                    continue

        except Exception as e:
            logger.error(f"提取搜索结果失败: {e}")

        return results

    async def _extract_patent_data(self, element) -> PatentResult | None:
        """从元素中提取专利数据"""
        try:
            patent = PatentResult(title='')

            # 提取标题
            title_selectors = [
                'h3',
                'h2',
                '.title',
                '.search-result-title',
                'a'
            ]

            for selector in title_selectors:
                title_elem = await element.query_selector(selector)
                if title_elem:
                    title_text = await title_elem.inner_text()
                    if title_text and len(title_text.strip()) > 0:
                        patent.title = title_text.strip()
                        break

            # 如果通过当前元素找不到标题，尝试点击获取详情
            if not patent.title:
                return None

            # 提取链接
            link_elem = await element.query_selector("a[href*='/patent/']")
            if link_elem:
                href = await link_elem.get_attribute('href')
                if href:
                    if href.startswith('/'):
                        patent.url = self.config['base_url'] + href
                    else:
                        patent.url = href

            # 尝试获取详细信息（如果有链接的话）
            if patent.url and False:  # 暂时禁用详情抓取以提高速度
                patent = await self._extract_detailed_patent_info(patent)

            return patent if patent.title else None

        except Exception as e:
            logger.debug(f"提取专利数据失败: {e}")
            return None

    async def _extract_detailed_patent_info(self, patent: PatentResult) -> PatentResult:
        """提取详细专利信息"""
        try:
            # 在新标签页中打开专利详情
            new_page = await self.browser.new_page()
            await new_page.goto(patent.url, timeout=15000)

            # 等待页面加载
            await new_page.wait_for_timeout(2000)

            # 提取详细信息
            # 申请号
            app_number_elem = await new_page.query_selector('[data-app-number], .application-number')
            if app_number_elem:
                patent.application_number = await app_number_elem.inner_text()

            # 公开号
            pub_number_elem = await new_page.query_selector('[data-publication-number], .publication-number')
            if pub_number_elem:
                patent.publication_number = await pub_number_elem.inner_text()

            # 摘要
            abstract_elem = await new_page.query_selector('.abstract, .description-abstract')
            if abstract_elem:
                patent.abstract = await abstract_elem.inner_text()

            # 申请人和发明人
            assignee_elem = await new_page.query_selector('.assignee, .applicant')
            if assignee_elem:
                patent.assignee = await assignee_elem.inner_text()

            # 日期信息
            date_elems = await new_page.query_selector_all('[data-date], .date')
            for elem in date_elems:
                date_text = await elem.inner_text()
                if 'filing' in date_text.lower():
                    patent.filing_date = date_text
                elif 'publication' in date_text.lower():
                    patent.publication_date = date_text

            # 关闭新标签页
            await new_page.close()

        except Exception as e:
            logger.debug(f"提取详细专利信息失败: {e}")

        return patent

    async def get_patent_details(self, patent_url: str) -> PatentResult | None:
        """获取专利详细信息"""
        if not self.is_initialized:
            await self.initialize()

        try:
            logger.info(f"获取专利详情: {patent_url}")

            # 在新标签页中打开
            detail_page = await self.browser.new_page()
            await detail_page.goto(patent_url, timeout=20000)

            # 等待页面加载
            await detail_page.wait_for_timeout(3000)

            # 创建专利对象
            patent = PatentResult(url=patent_url)

            # 提取详细信息
            patent.title = await self._safe_extract_text(detail_page, 'h1, .title')
            patent.abstract = await self._safe_extract_text(detail_page, '.abstract')
            patent.application_number = await self._safe_extract_text(detail_page, '[data-app-number]')
            patent.publication_number = await self._safe_extract_text(detail_page, '[data-publication-number]')
            patent.assignee = await self._safe_extract_text(detail_page, '.assignee')

            # 关闭页面
            await detail_page.close()

            return patent

        except Exception as e:
            logger.error(f"获取专利详情失败: {e}")
            return None

    async def _safe_extract_text(self, page, selector: str) -> str:
        """安全地提取文本"""
        try:
            element = await page.query_selector(selector)
            if element:
                return await element.inner_text()
except Exception:  # TODO: 根据上下文指定具体异常类型
        return ''

    async def close(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
            self.is_initialized = False
            logger.info('浏览器已关闭')

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()

# 使用示例
async def main():
    """主函数示例"""
    retriever = BrowserPatentRetriever()

    try:
        async with retriever:
            # 搜索专利
            results = await retriever.search_patents('artificial intelligence', max_results=5)

            logger.info(f"找到 {len(results)} 个专利:")
            for i, patent in enumerate(results, 1):
                logger.info(f"\n{i}. {patent.title}")
                logger.info(f"   申请号: {patent.application_number}")
                logger.info(f"   链接: {patent.url}")
                if patent.abstract:
                    logger.info(f"   摘要: {patent.abstract[:150]}...")

    except Exception as e:
        logger.info(f"搜索失败: {e}")

if __name__ == '__main__':
    asyncio.run(main())