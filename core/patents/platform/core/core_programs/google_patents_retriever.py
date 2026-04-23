#!/usr/bin/env python3
"""
Google Patents智能检索系统
Google Patents Intelligent Retrieval System

集成到Athena工作平台的完整Google Patents检索解决方案
支持智能搜索、批量处理、数据分析和导出功能

作者: Athena (智慧女神)
创建时间: 2025-12-07
版本: 1.0.0
"""

import asyncio
import csv
import json
import logging
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import aiofiles
import pandas as pd

# 配置日志（必须在导入模块之前配置）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 浏览器自动化
try:
    from browser_use import Agent, Browser
    BROWSER_USE_AVAILABLE = True
    logger.info('✅ browser-use框架可用')
except ImportError:
    BROWSER_USE_AVAILABLE = False
    logger.info('⚠️ browser-use框架未安装')

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
    logger.info('✅ Playwright框架可用')
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.info('⚠️ Playwright框架未安装')
    async_playwright = None

import hashlib

# 数据处理
from bs4 import BeautifulSoup

class SearchStatus(Enum):
    """搜索状态枚举"""
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'

class PatentPriority(Enum):
    """专利优先级"""
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'

@dataclass
class PatentData:
    """专利数据模型"""
    patent_id: str
    title: str
    abstract: str
    inventors: List[str]
    assignee: str
    filing_date: str
    publication_date: str
    priority_date: Optional[str]
    classification: str
    family_id: Optional[str]
    legal_status: str
    claims: List[str]
    citations: List[str]
    family_members: List[str]
    url: str
    relevance_score: float = 0.0
    search_query: str = ''
    extracted_at: str = ''

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['inventors'] = ', '.join(self.inventors)
        data['claims'] = '\n'.join(self.claims)
        data['citations'] = ', '.join(self.citations)
        data['family_members'] = ', '.join(self.family_members)
        return data

class GooglePatentsRetriever:
    """Google Patents智能检索器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化检索器

        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.browser = None
        self.agent = None
        self.playwright = None
        self.context = None
        self.page = None

        # 配置参数
        self.base_url = 'https://patents.google.com'
        self.headless = self.config.get('headless', False)
        # 暂时禁用browser-use，只使用Playwright，确保基本功能可用
        self.use_browser_use = False  # self.config.get('use_browser_use', True) and BROWSER_USE_AVAILABLE
        self.use_playwright = self.config.get('use_playwright', True) and PLAYWRIGHT_AVAILABLE
        self.max_concurrent = self.config.get('max_concurrent', 3)
        self.request_delay = self.config.get('request_delay', 2)

        # 统计信息
        self.stats = {
            'total_searches': 0,
            'successful_searches': 0,
            'failed_searches': 0,
            'total_patents_found': 0,
            'start_time': datetime.now()
        }

        # 缓存系统
        self.cache_enabled = self.config.get('cache_enabled', True)
        self.cache_ttl = self.config.get('cache_ttl', 3600)  # 1小时缓存
        self.search_cache = {}  # 内存缓存
        self.cache_hits = 0
        self.cache_misses = 0

    async def initialize(self):
        """初始化检索器"""
        try:
            if self.use_browser_use:
                await self._init_browser_use()
            elif self.use_playwright:
                await self._init_playwright()
            else:
                raise ValueError('无可用的浏览器自动化框架')

            logger.info('✅ Google Patents检索器初始化成功')
            return True

        except Exception as e:
            logger.error(f"❌ 初始化失败: {e}")
            return False

    async def _init_browser_use(self):
        """初始化browser-use"""
        self.browser = Browser(
            headless=self.headless,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--window-size=1920,1080'
            ]
        )
        logger.info('✅ browser-use初始化成功')

    async def _init_playwright(self):
        """初始化Playwright"""
        try:
            if not async_playwright:
                raise ImportError('async_playwright not available')

            # 正确的方式：调用async_playwright()函数
            playwright_instance = async_playwright()
            self.playwright = await playwright_instance.start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--window-size=1920,1080'
                ]
            )
            self.context = await self.browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )
            self.page = await self.context.new_page()
            logger.info('✅ Playwright初始化成功')
        except Exception as e:
            logger.error(f"❌ Playwright初始化失败: {e}")
            raise

    async def search_patents(
        self,
        query: str,
        max_results: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        priority: PatentPriority = PatentPriority.MEDIUM
    ) -> Dict[str, Any]:
        """
        搜索专利

        Args:
            query: 搜索查询
            max_results: 最大结果数
            filters: 搜索筛选器
            priority: 搜索优先级

        Returns:
            搜索结果
        """
        search_id = f"search_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(query) % 10000}"

        logger.info(f"🔍 开始搜索专利: {query}")
        logger.info(f"📊 搜索ID: {search_id}")

        # 生成缓存键
        cache_key = self._generate_cache_key(query, max_results, filters, priority)

        # 检查缓存
        if self.cache_enabled:
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                self.cache_hits += 1
                logger.info(f"🎯 缓存命中! 返回缓存结果")
                cached_result['search_id'] = search_id  # 更新搜索ID
                cached_result['from_cache'] = True
                return cached_result
            else:
                self.cache_misses += 1

        self.stats['total_searches'] += 1

        try:
            if self.use_browser_use:
                patents = await self._search_with_browser_use(query, max_results, filters)
            elif self.use_playwright:
                patents = await self._search_with_playwright(query, max_results, filters)
            else:
                raise ValueError('无可用的搜索方法')

            self.stats['successful_searches'] += 1
            self.stats['total_patents_found'] += len(patents)

            # 计算相关性评分
            patents = await self._calculate_relevance_scores(patents, query)

            # 根据优先级排序
            patents = await self._sort_by_priority(patents, priority)

            result = {
                'success': True,
                'search_id': search_id,
                'query': query,
                'total_found': len(patents),
                'patents': patents,
                'filters': filters,
                'search_time': datetime.now().isoformat(),
                'source': 'Google Patents',
                'method': 'browser_use' if self.use_browser_use else 'playwright',
                'from_cache': False
            }

            # 保存到缓存
            if self.cache_enabled:
                self._save_to_cache(cache_key, result)

            # 保存搜索历史
            await self._save_search_history(search_id, result)

            return result

        except Exception as e:
            self.stats['failed_searches'] += 1
            logger.error(f"❌ 搜索失败: {e}")

            return {
                'success': False,
                'search_id': search_id,
                'query': query,
                'error': str(e),
                'search_time': datetime.now().isoformat()
            }

    async def _search_with_browser_use(
        self,
        query: str,
        max_results: int,
        filters: Optional[Dict[str, Any]]
    ) -> List[PatentData]:
        """使用browser-use搜索"""
        logger.info('🤖 使用browser-use进行智能搜索')

        # 构建搜索任务
        task = f"""
        请在Google Patents网站上搜索关于'{query}'的专利。

        搜索要求：
        1. 访问 https://patents.google.com
        2. 在搜索框中输入查询词: {query}
        3. 执行搜索并等待结果加载
        4. 提取前{max_results}个专利的详细信息

        需要提取的专利信息：
        - 专利号 (patent number)
        - 专利标题 (title)
        - 发明人 (inventors)
        - 申请人/受让人 (assignee)
        - 申请日期 (filing date)
        - 公开日期 (publication date)
        - 优先权日期 (priority date)
        - 分类号 (classification)
        - 摘要 (abstract)
        - 权利要求 (claims)
        - 引用文献 (citations)
        - 法律状态 (legal status)
        - 专利家族信息 (family)

        请将结果格式化为JSON数组返回。
        """

        self.agent = Agent(
            task=task,
            llm=self._get_llm_instance(),
            browser=self.browser
        )

        # 执行搜索
        result = await self.agent.run()

        # 解析结果
        patents = await self._parse_browser_use_result(result, query)

        return patents

    async def _search_with_playwright(
        self,
        query: str,
        max_results: int,
        filters: Optional[Dict[str, Any]]
    ) -> List[PatentData]:
        """使用Playwright搜索 - 增强版"""
        logger.info('🎭 使用Playwright进行智能搜索')

        patents = []

        try:
            # 检查page对象是否存在
            if not self.page:
                raise ValueError('Page对象未初始化')

            # 1. 智能访问Google Patents - 添加反爬虫对策
            logger.info('🌐 访问Google Patents首页...')
            await self.page.goto(self.base_url, wait_until='domcontentloaded')

            # 随机延迟，模拟人类行为
            await asyncio.sleep(1 + (hash(query) % 3))

            # 等待页面完全加载
            try:
                await self.page.wait_for_load_state('networkidle', timeout=10000)
            except:
                logger.warning('⚠️ 网络空闲等待超时，继续执行...')

            # 2. 多种搜索框选择器策略
            search_selectors = [
                'input[placeholder*="Search"]',
                'input[placeholder*="search"]',
                'input[name="q"]',
                '#searchInput',
                '.search-input input',
                'input[type="search"]',
                '[aria-label*="Search"]'
            ]

            search_input = None
            for selector in search_selectors:
                try:
                    search_input = await self.page.wait_for_selector(selector, timeout=3000)
                    if search_input:
                        logger.info(f"✅ 找到搜索框: {selector}")
                        break
                except:
                    continue

            if not search_input:
                # 尝试通过JavaScript找到搜索框
                search_input = await self.page.evaluate('''() => {
                    const inputs = document.querySelectorAll('input');
                    for (let input of inputs) {
                        if (input.placeholder && input.placeholder.toLowerCase().includes('search')) {
                            return input;
                        }
                        if (input.name === 'q' || input.type === 'search') {
                            return input;
                        }
                    }
                    return null;
                }''')

                if search_input:
                    logger.info('✅ 通过JavaScript找到搜索框')

            if not search_input:
                raise ValueError('无法找到搜索框')

            # 3. 智能输入搜索查询
            logger.info(f"📝 输入搜索查询: {query}")

            # 清空并输入查询
            await self.page.evaluate('''(input) => {
                input.value = '';
                input.focus();
            }''', search_input)

            # 模拟人类输入 - 逐字符输入
            for i, char in enumerate(query):
                await search_input.type(char)
                if i % 3 == 0:  # 每3个字符停顿一下
                    await asyncio.sleep(0.1 + (hash(char) % 2) * 0.1)

            await asyncio.sleep(0.5)

            # 4. 提交搜索 - 多种方式
            submit_success = False

            # 方法1: 按Enter键
            try:
                await search_input.press('Enter')
                submit_success = True
                logger.info('✅ 通过Enter键提交搜索')
            except Exception as e:
                # 记录异常但不中断流程
                logger.debug(f"[google_patents_retriever] Exception: {e}")

            # 方法2: 点击搜索按钮
            if not submit_success:
                submit_selectors = [
                    'button[type="submit"]',
                    '[data-test="search-button"]',
                    '.search-button',
                    '#searchButton',
                    'button[aria-label*="Search"]'
                ]

                for selector in submit_selectors:
                    try:
                        search_button = await self.page.wait_for_selector(selector, timeout=2000)
                        if search_button:
                            await search_button.click()
                            submit_success = True
                            logger.info(f"✅ 通过搜索按钮提交: {selector}")
                            break
                    except:
                        continue

            if not submit_success:
                # 方法3: 使用JavaScript表单提交
                await self.page.evaluate('''() => {
                    const forms = document.querySelectorAll('form');
                    for (let form of forms) {
                        if (form.querySelector('input[name="q"]') ||
                            form.querySelector('input[type="search"]') ||
                            form.querySelector('input[placeholder*='search' i]')) {
                            form.submit();
                            return true;
                        }
                    }
                    return false;
                }''')
                logger.info('✅ 通过JavaScript表单提交')

            # 5. 等待搜索结果加载 - 增强等待策略
            logger.info('⏳ 等待搜索结果加载...')

            result_loaded = False
            result_selectors = [
                '[data-test="search-result"]',
                '.search-result',
                '.result-item',
                '[data-test="result-item"]',
                'article[data-test="result"]',
                '.patent-result',
                '#results .result'
            ]

            for selector in result_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=8000)
                    result_loaded = True
                    logger.info(f"✅ 找到搜索结果: {selector}")
                    break
                except:
                    continue

            # 如果没有找到结果选择器，等待URL变化或页面内容更新
            if not result_loaded:
                try:
                    # 等待URL包含搜索参数
                    await self.page.wait_for_url('**/*?*', timeout=10000)
                    logger.info('✅ 检测到搜索URL变化')
                    result_loaded = True
                except Exception as e:
                    # 记录异常但不中断流程
                    logger.debug(f"[google_patents_retriever] URL等待异常: {e}")

            # 最后的等待策略 - 等待页面稳定
            if not result_loaded:
                await asyncio.sleep(3)
                logger.info('⏳ 使用固定延迟等待页面稳定')

            # 6. 提取搜索结果 - 增强提取策略
            patents = await self._extract_search_results_playwright_enhanced(max_results, query)

        except Exception as e:
            logger.error(f"❌ Playwright搜索失败: {e}")
            # 记录当前页面状态用于调试
            try:
                current_url = self.page.url
                page_title = await self.page.title()
                logger.info(f"🔍 当前页面: {current_url} - {page_title}")
            except Exception as e:
                # 记录异常但不中断流程
                logger.debug(f"[google_patents_retriever] 页面状态获取异常: {e}")

        return patents

    async def _extract_search_results_playwright(self, max_results: int, query: str) -> List[PatentData]:
        """使用Playwright提取搜索结果"""
        patents = []

        try:
            # 获取搜索结果元素
            results = await self.page.query_selector_all('[data-test="search-result"]')
            if not results:
                results = await self.page.query_selector_all('.search-result')

            logger.info(f"📊 找到 {len(results)} 个搜索结果")

            # 限制结果数量
            results = results[:max_results]

            for i, result in enumerate(results):
                try:
                    patent = await self._extract_patent_info_playwright(result, i + 1, query)
                    if patent:
                        patents.append(patent)

                    # 添加延迟避免过快请求
                    await asyncio.sleep(0.5)

                except Exception as e:
                    logger.warning(f"⚠️ 提取第 {i+1} 个专利信息失败: {e}")

        except Exception as e:
            logger.error(f"❌ 提取搜索结果失败: {e}")

        return patents

    async def _extract_search_results_playwright_enhanced(self, max_results: int, query: str) -> List[PatentData]:
        """使用Playwright提取搜索结果 - 增强版"""
        patents = []

        try:
            logger.info('🔍 开始提取搜索结果...')

            # 多种结果选择器策略
            result_selectors = [
                '[data-test="search-result"]',
                '.search-result',
                '.result-item',
                '[data-test="result-item"]',
                'article[data-test="result"]',
                '.patent-result',
                '#results .result',
                'li.result',
                'div[class*="result"]',
                'a[href*="patent"]'
            ]

            all_results = []
            for selector in result_selectors:
                try:
                    results = await self.page.query_selector_all(selector)
                    if results:
                        logger.info(f"✅ 使用选择器找到 {len(results)} 个结果: {selector}")
                        all_results.extend(results)
                        if len(all_results) >= max_results * 2:
                            break
                except Exception as e:
                    logger.debug(f"选择器 {selector} 未找到结果: {e}")
                    continue

            # 如果没有找到任何结果，尝试JavaScript提取
            if not all_results:
                logger.info('🔄 尝试JavaScript提取专利链接...')
                try:
                    js_results = await self.page.evaluate('''() => {
                        const results = [];
                        const links = document.querySelectorAll('a[href*="patent"]');
                        links.forEach(link => {
                            const href = link.href;
                            if (href.includes('patents.google.com/patent/')) {
                                results.push({
                                    element: link,
                                    href: href,
                                    text: link.innerText || link.textContent
                                });
                            }
                        });
                        return results.slice(0, 20);
                    }''')

                    if js_results:
                        logger.info(f"✅ JavaScript找到 {len(js_results)} 个专利链接")
                        for js_result in js_results:
                            try:
                                patent = await self._extract_patent_from_js_result(js_result, query)
                                if patent:
                                    patents.append(patent)
                                    if len(patents) >= max_results:
                                        break
                            except Exception as e:
                                logger.warning(f"⚠️ 处理JS结果失败: {e}")

                except Exception as e:
                    logger.warning(f"⚠️ JavaScript提取失败: {e}")

            # 处理常规DOM结果
            if all_results and len(patents) < max_results:
                # 去重
                unique_results = []
                seen_positions = set()

                for result in all_results:
                    try:
                        bbox = await result.bounding_box()
                        if bbox:
                            pos_key = f"{int(bbox.x/10)}_{int(bbox.y/10)}"
                            if pos_key not in seen_positions:
                                seen_positions.add(pos_key)
                                unique_results.append(result)
                    except:
                        unique_results.append(result)

                logger.info(f"📊 去重后找到 {len(unique_results)} 个唯一结果")
                unique_results = unique_results[:max_results]

                for i, result in enumerate(unique_results):
                    try:
                        patent = await self._extract_patent_info_playwright_enhanced(result, i + 1, query)
                        if patent:
                            patents.append(patent)

                        await asyncio.sleep(0.3 + (hash(str(i)) % 3) * 0.2)

                        if len(patents) >= max_results:
                            break

                    except Exception as e:
                        logger.warning(f"⚠️ 提取第 {i+1} 个专利信息失败: {e}")

            logger.info(f"✅ 成功提取 {len(patents)} 个专利信息")

        except Exception as e:
            logger.error(f"❌ 增强版结果提取失败: {e}")

        return patents

    async def _extract_patent_info_playwright_enhanced(self, result_element, index: int, query: str) -> Optional[PatentData]:
        """使用Playwright提取单个专利信息 - 增强版"""
        try:
            # 通用提取策略
            title = ''
            patent_id = ''
            abstract = ''
            assignee = ''
            date_info = ''
            classification = ''
            url = ''

            # 提取标题和链接
            title_selectors = [
                'a[data-test="result-title"]',
                '.result-title a',
                'h3 a',
                'h2 a',
                'a[href*="patent"]',
                '[class*="title"] a',
                'span[class*="title"]'
            ]

            title_element = None
            for selector in title_selectors:
                try:
                    title_element = await result_element.query_selector(selector)
                    if title_element:
                        title = await title_element.text_content()
                        url = await title_element.get_attribute('href')
                        if title and url:
                            break
                except:
                    continue

            if not title:
                try:
                    title = await result_element.text_content()
                    title = title.strip().split('\n')[0][:100]
                except Exception as e:
                    # 记录异常但不中断流程
                    logger.debug(f"[google_patents_retriever] 标题提取异常: {e}")

            # 提取专利号
            patent_selectors = [
                '[data-test="result-number"]',
                '.patent-number',
                '.result-number',
                '[class*="patent-number"]',
                '[class*="publication-number"]',
                'span[class*="number"]'
            ]

            for selector in patent_selectors:
                try:
                    patent_element = await result_element.query_selector(selector)
                    if patent_element:
                        patent_id = await patent_element.text_content()
                        if patent_id:
                            break
                except:
                    continue

            if not patent_id and url:
                import re
                patent_match = re.search(r'patent/([^?/]+)', url)
                if patent_match:
                    patent_id = patent_match.group(1)

            # 提取其他字段...（简化版本）
            abstract = '摘要信息待提取'
            assignee = '申请人待提取'
            date_info = ''
            classification = ''

            # 清理数据
            title = title.strip() if title else f"专利 {index}"
            patent_id = patent_id.strip() if patent_id else f"UNKNOWN_{index}"
            url = url.strip() if url else f"https://patents.google.com/patent/{patent_id}"

            # 解析日期
            filing_date, publication_date = self._parse_dates(date_info)

            patent = PatentData(
                patent_id=patent_id,
                title=title,
                abstract=abstract,
                inventors=[],
                assignee=assignee,
                filing_date=filing_date,
                publication_date=publication_date,
                priority_date='',
                classification=classification,
                family_id='',
                legal_status='',
                claims=[],
                citations=[],
                family_members=[],
                url=url,
                search_query=query,
                extracted_at=datetime.now().isoformat()
            )

            return patent

        except Exception as e:
            logger.error(f"❌ 增强版专利信息提取失败: {e}")
            return None

    async def _extract_patent_from_js_result(self, js_result: Dict[str, Any], query: str) -> Optional[PatentData]:
        """从JavaScript提取的结果创建专利对象"""
        try:
            href = js_result.get('href', '')
            text = js_result.get('text', '')

            import re
            patent_match = re.search(r'patent/([^?/]+)', href)
            patent_id = patent_match.group(1) if patent_match else f"JS_PATENT_{hash(href) % 10000}"

            title = text.strip().split('\n')[0][:100] if text else f"专利 {patent_id}"

            patent = PatentData(
                patent_id=patent_id,
                title=title,
                abstract='从JavaScript提取的专利信息',
                inventors=[],
                assignee='待提取',
                filing_date='',
                publication_date='',
                priority_date='',
                classification='',
                family_id='',
                legal_status='',
                claims=[],
                citations=[],
                family_members=[],
                url=href,
                search_query=query,
                extracted_at=datetime.now().isoformat()
            )

            return patent

        except Exception as e:
            logger.warning(f"⚠️ JS结果转换失败: {e}")
            return None

    async def _extract_patent_info_playwright(self, result_element, index: int, query: str) -> Optional[PatentData]:
        """使用Playwright提取单个专利信息"""
        try:
            # 专利标题
            title_element = await result_element.query_selector('a[data-test="result-title"]')
            title = await title_element.text_content() if title_element else ''

            # 专利号
            number_element = await result_element.query_selector('[data-test="result-number"]')
            patent_id = await number_element.text_content() if number_element else ''

            # 摘要
            abstract_element = await result_element.query_selector('[data-test="result-abstract"]')
            abstract = await abstract_element.text_content() if abstract_element else ''

            # 申请人
            assignee_element = await result_element.query_selector('[data-test="result-assignee"]')
            assignee = await assignee_element.text_content() if assignee_element else ''

            # 日期信息
            date_element = await result_element.query_selector('[data-test="result-date"]')
            date_info = await date_element.text_content() if date_element else ''

            # 分类号
            classification_element = await result_element.query_selector('[data-test="result-classification"]')
            classification = await classification_element.text_content() if classification_element else ''

            # URL
            link_element = await result_element.query_selector('a[data-test="result-title"]')
            url = await link_element.get_attribute('href') if link_element else ''
            if url and not url.startswith('http'):
                url = self.base_url + url

            # 解析日期
            filing_date, publication_date = self._parse_dates(date_info)

            patent = PatentData(
                patent_id=patent_id.strip(),
                title=title.strip(),
                abstract=abstract.strip(),
                inventors=[],  # 需要详情页获取
                assignee=assignee.strip(),
                filing_date=filing_date,
                publication_date=publication_date,
                priority_date='',
                classification=classification.strip(),
                family_id='',
                legal_status='',
                claims=[],
                citations=[],
                family_members=[],
                url=url,
                search_query=query,
                extracted_at=datetime.now().isoformat()
            )

            return patent

        except Exception as e:
            logger.error(f"❌ 提取专利信息失败: {e}")
            return None

    async def get_patent_details(self, patent_id: str) -> Dict[str, Any]:
        """获取专利详细信息"""
        logger.info(f"📄 获取专利详情: {patent_id}")

        try:
            if self.use_browser_use:
                return await self._get_details_browser_use(patent_id)
            elif self.use_playwright:
                return await self._get_details_playwright(patent_id)
            else:
                raise ValueError('无可用的详情获取方法')

        except Exception as e:
            logger.error(f"❌ 获取专利详情失败: {e}")
            return {
                'success': False,
                'patent_id': patent_id,
                'error': str(e)
            }

    async def _get_details_playwright(self, patent_id: str) -> Dict[str, Any]:
        """使用Playwright获取专利详情"""
        try:
            # 访问专利详情页
            detail_url = f"{self.base_url}/patent/{patent_id}"
            await self.page.goto(detail_url)
            await self.page.wait_for_load_state('networkidle')

            # 提取详细信息
            details = {}

            # 等待主要内容加载
            await self.page.wait_for_timeout(2000)

            # 发明人
            inventors_element = await self.page.query_selector('[data-test="inventors"]')
            if inventors_element:
                inventors_text = await inventors_element.text_content()
                details['inventors'] = [inv.strip() for inv in inventors_text.split(',')]

            # 权利要求
            claims_element = await self.page.query_selector('[data-test="claims"]')
            if claims_element:
                claims_text = await claims_element.text_content()
                details['claims'] = [claim.strip() for claim in claims_text.split('\n') if claim.strip()]

            # 引用文献
            citations_element = await self.page.query_selector('[data-test="citations"]')
            if citations_element:
                citations_text = await citations_element.text_content()
                details['citations'] = [citation.strip() for citation in citations_text.split(',') if citation.strip()]

            # 法律状态
            legal_status_element = await self.page.query_selector('[data-test="legal-status"]')
            if legal_status_element:
                details['legal_status'] = await legal_status_element.text_content()

            # 专利家族
            family_element = await self.page.query_selector('[data-test="family"]')
            if family_element:
                family_text = await family_element.text_content()
                details['family_members'] = [member.strip() for member in family_text.split(',') if member.strip()]

            # 优先权日期
            priority_element = await self.page.query_selector('[data-test="priority-date"]')
            if priority_element:
                details['priority_date'] = await priority_element.text_content()

            # 家族ID
            family_id_element = await self.page.query_selector('[data-test="family-id"]')
            if family_id_element:
                details['family_id'] = await family_id_element.text_content()

            return {
                'success': True,
                'patent_id': patent_id,
                'details': details,
                'extracted_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ 获取详情失败: {e}")
            return {
                'success': False,
                'patent_id': patent_id,
                'error': str(e)
            }

    async def batch_search(
        self,
        queries: List[str],
        max_results_per_query: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        save_results: bool = True
    ) -> Dict[str, Any]:
        """批量搜索专利"""
        logger.info(f"🔄 开始批量搜索: {len(queries)} 个查询")

        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 使用信号量控制并发
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def search_with_semaphore(query: str) -> Dict[str, Any]:
            async with semaphore:
                result = await self.search_patents(query, max_results_per_query, filters)
                await asyncio.sleep(self.request_delay)
                return result

        # 执行批量搜索
        tasks = [search_with_semaphore(query) for query in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        successful_searches = []
        failed_searches = []
        all_patents = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_searches.append({
                    'query': queries[i],
                    'error': str(result)
                })
                logger.error(f"查询 {queries[i]} 失败: {result}")
            else:
                if result['success']:
                    successful_searches.append(result)
                    all_patents.extend(result['patents'])
                else:
                    failed_searches.append(result)

        # 去重
        unique_patents = await self._deduplicate_patents(all_patents)

        batch_result = {
            'batch_id': batch_id,
            'total_queries': len(queries),
            'successful_searches': len(successful_searches),
            'failed_searches': len(failed_searches),
            'total_patents_found': len(unique_patents),
            'queries': queries,
            'results': successful_searches,
            'failed_queries': failed_searches,
            'all_patents': unique_patents,
            'batch_time': datetime.now().isoformat()
        }

        # 保存批量搜索结果
        if save_results:
            await self._save_batch_results(batch_id, batch_result)

        return batch_result

    async def analyze_patents(self, patents: List[PatentData]) -> Dict[str, Any]:
        """分析专利数据"""
        logger.info(f"📊 开始分析 {len(patents)} 个专利")

        analysis = {
            'total_patents': len(patents),
            'analysis_time': datetime.now().isoformat(),
            'statistics': {},
            'trends': {},
            'top_assignees': {},
            'top_classifications': {},
            'timeline_analysis': {},
            'keyword_analysis': {}
        }

        # 基本统计
        analysis['statistics'] = {
            'total_patents': len(patents),
            'patents_with_abstract': len([p for p in patents if p.abstract]),
            'patents_with_claims': len([p for p in patents if p.claims]),
            'unique_assignees': len(set(p.assignee for p in patents if p.assignee)),
            'unique_classifications': len(set(p.classification for p in patents if p.classification))
        }

        # 顶级申请人
        assignee_counts = {}
        for patent in patents:
            if patent.assignee:
                assignee_counts[patent.assignee] = assignee_counts.get(patent.assignee, 0) + 1

        analysis['top_assignees'] = dict(
            sorted(assignee_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        )

        # 顶级分类号
        classification_counts = {}
        for patent in patents:
            if patent.classification:
                # 提取主分类号
                main_class = patent.classification.split()[0] if patent.classification.split() else patent.classification
                classification_counts[main_class] = classification_counts.get(main_class, 0) + 1

        analysis['top_classifications'] = dict(
            sorted(classification_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        )

        # 时间线分析
        year_counts = {}
        for patent in patents:
            if patent.publication_date:
                year = patent.publication_date.split('-')[0]
                if year.isdigit():
                    year_counts[year] = year_counts.get(year, 0) + 1

        analysis['timeline_analysis'] = dict(
            sorted(year_counts.items(), key=lambda x: x[0])
        )

        # 关键词分析
        all_text = ' '.join([
            f"{p.title} {p.abstract}"
            for p in patents
            if p.title or p.abstract
        ]).lower()

        # 提取常见关键词
        common_words = ['patent', 'method', 'system', 'device', 'apparatus', 'based', 'used', 'data', 'process']
        word_counts = {}

        for word in all_text.split():
            if len(word) > 3 and word not in common_words:
                word_counts[word] = word_counts.get(word, 0) + 1

        analysis['keyword_analysis'] = dict(
            sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:20]
        )

        return analysis

    async def export_patents(
        self,
        patents: List[PatentData],
        format: str = 'json',
        filename: Optional[str] = None,
        include_analysis: bool = False
    ) -> str:
        """导出专利数据"""
        logger.info(f"📤 导出 {len(patents)} 个专利为 {format} 格式")

        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"patents_export_{timestamp}.{format}"

        export_data = {
            'export_info': {
                'total_patents': len(patents),
                'export_format': format,
                'export_time': datetime.now().isoformat(),
                'source': 'Google Patents'
            },
            'patents': [patent.to_dict() for patent in patents]
        }

        if include_analysis:
            export_data['analysis'] = await self.analyze_patents(patents)

        try:
            if format.lower() == 'json':
                await self._export_json(export_data, filename)
            elif format.lower() == 'csv':
                await self._export_csv(patents, filename)
            elif format.lower() == 'excel':
                await self._export_excel(patents, filename, include_analysis)
            else:
                raise ValueError(f"不支持的导出格式: {format}")

            logger.info(f"✅ 导出成功: {filename}")
            return filename

        except Exception as e:
            logger.error(f"❌ 导出失败: {e}")
            raise

    async def _export_json(self, data: Dict[str, Any], filename: str):
        """导出为JSON格式"""
        async with aiofiles.open(filename, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(data, ensure_ascii=False, indent=2))

    async def _export_csv(self, patents: List[PatentData], filename: str):
        """导出为CSV格式"""
        df = pd.DataFrame([patent.to_dict() for patent in patents])
        df.to_csv(filename, index=False, encoding='utf-8-sig')

    async def _export_excel(self, patents: List[PatentData], filename: str, include_analysis: bool):
        """导出为Excel格式"""
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # 专利数据表
            df_patents = pd.DataFrame([patent.to_dict() for patent in patents])
            df_patents.to_excel(writer, sheet_name='Patents', index=False)

            if include_analysis:
                # 分析结果表
                analysis = await self.analyze_patents(patents)

                # 统计信息
                stats_data = []
                for key, value in analysis['statistics'].items():
                    stats_data.append({'指标': key, '值': value})
                df_stats = pd.DataFrame(stats_data)
                df_stats.to_excel(writer, sheet_name='Statistics', index=False)

                # 顶级申请人
                assignee_data = [{'申请人': k, '专利数量': v} for k, v in analysis['top_assignees'].items()]
                df_assignees = pd.DataFrame(assignee_data)
                df_assignees.to_excel(writer, sheet_name='Top Assignees', index=False)

                # 分类统计
                class_data = [{'分类号': k, '专利数量': v} for k, v in analysis['top_classifications'].items()]
                df_class = pd.DataFrame(class_data)
                df_class.to_excel(writer, sheet_name='Classifications', index=False)

    async def _calculate_relevance_scores(self, patents: List[PatentData], query: str) -> List[PatentData]:
        """计算相关性评分"""
        query_terms = query.lower().split()

        for patent in patents:
            score = 0.0
            title_text = patent.title.lower()
            abstract_text = patent.abstract.lower()

            # 标题匹配
            for term in query_terms:
                if term in title_text:
                    score += 0.3

            # 摘要匹配
            for term in query_terms:
                if term in abstract_text:
                    score += 0.2

            patent.relevance_score = min(1.0, score)

        return patents

    async def _sort_by_priority(self, patents: List[PatentData], priority: PatentPriority) -> List[PatentData]:
        """根据优先级排序"""
        if priority == PatentPriority.HIGH:
            # 按相关性排序
            patents.sort(key=lambda x: x.relevance_score, reverse=True)
        elif priority == PatentPriority.LOW:
            # 按申请日期排序
            patents.sort(key=lambda x: x.filing_date or '', reverse=True)
        else:
            # 默认按公开日期排序
            patents.sort(key=lambda x: x.publication_date or '', reverse=True)

        return patents

    def _parse_dates(self, date_info: str) -> tuple:
        """解析日期信息"""
        filing_date = ''
        publication_date = ''

        try:
            # 简单的日期解析逻辑
            if 'Filed:' in date_info:
                filing_part = date_info.split('Filed:')[1].split(';')[0].strip()
                filing_date = filing_part
            if 'Publication:' in date_info:
                pub_part = date_info.split('Publication:')[1].split(';')[0].strip()
                publication_date = pub_part
        except Exception as e:
            logger.warning(f"⚠️ 日期解析失败: {e}")

        return filing_date, publication_date

    def _get_llm_instance(self):
        """获取LLM实例"""
        try:
            # 使用Ollama本地LLM
            from langchain_ollama import OllamaLLM
            llm = OllamaLLM(model='qwen:7b', temperature=0.1)
            # 修复browser-use兼容性问题：添加provider属性
            if not hasattr(llm, 'provider'):
                llm.provider = 'ollama'
            return llm
        except ImportError:
            logger.warning('使用默认LLM配置')
            return None

    async def _parse_browser_use_result(self, result: Any, query: str) -> List[PatentData]:
        """解析browser-use结果"""
        patents = []

        try:
            # 这里需要根据实际返回的格式进行解析
            # 由于browser-use的输出格式可能不固定，提供基础解析
            if isinstance(result, str):
                # 尝试解析JSON
                try:
                    data = json.loads(result)
                    if isinstance(data, list):
                        for item in data:
                            patent = await self._create_patent_from_dict(item, query)
                            if patent:
                                patents.append(patent)
                except json.JSONDecodeError:
                    logger.warning('无法解析JSON结果，使用文本提取')
                    patents = await self._extract_patents_from_text(result, query)
            else:
                logger.warning('未知的返回格式类型')

        except Exception as e:
            logger.error(f"解析结果失败: {e}")

        return patents

    async def _create_patent_from_dict(self, data: Dict[str, Any], query: str) -> Optional[PatentData]:
        """从字典创建专利对象"""
        try:
            patent = PatentData(
                patent_id=data.get('patent_number', data.get('patent_id', '')),
                title=data.get('title', ''),
                abstract=data.get('abstract', ''),
                inventors=data.get('inventors', []),
                assignee=data.get('assignee', ''),
                filing_date=data.get('filing_date', ''),
                publication_date=data.get('publication_date', ''),
                priority_date=data.get('priority_date', ''),
                classification=data.get('classification', ''),
                family_id=data.get('family_id', ''),
                legal_status=data.get('legal_status', ''),
                claims=data.get('claims', []),
                citations=data.get('citations', []),
                family_members=data.get('family_members', []),
                url=data.get('url', ''),
                search_query=query,
                extracted_at=datetime.now().isoformat()
            )
            return patent
        except Exception as e:
            logger.error(f"创建专利对象失败: {e}")
            return None

    async def _extract_patents_from_text(self, text: str, query: str) -> List[PatentData]:
        """从文本中提取专利信息"""
        # 简化的文本提取逻辑
        patents = []

        # 这里可以根据实际文本格式进行更复杂的解析
        # 目前返回空列表，需要根据实际情况调整

        return patents

    async def _deduplicate_patents(self, patents: List[PatentData]) -> List[PatentData]:
        """去重专利"""
        seen_ids = set()
        unique_patents = []

        for patent in patents:
            if patent.patent_id and patent.patent_id not in seen_ids:
                seen_ids.add(patent.patent_id)
                unique_patents.append(patent)

        return unique_patents

    async def _save_search_history(self, search_id: str, result: Dict[str, Any]):
        """保存搜索历史"""
        try:
            history_file = Path('data/patents/search_history.json')
            history_file.parent.mkdir(parents=True, exist_ok=True)

            # 读取现有历史
            history = []
            if history_file.exists():
                async with aiofiles.open(history_file, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    if content:
                        history = json.loads(content)

            # 添加新搜索
            history.append(result)

            # 保存历史
            async with aiofiles.open(history_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(history, ensure_ascii=False, indent=2))

        except Exception as e:
            logger.error(f"保存搜索历史失败: {e}")

    async def _save_batch_results(self, batch_id: str, result: Dict[str, Any]):
        """保存批量搜索结果"""
        try:
            results_dir = Path('data/patents/batch_results')
            results_dir.mkdir(parents=True, exist_ok=True)

            filename = results_dir / f"{batch_id}.json"

            async with aiofiles.open(filename, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(result, ensure_ascii=False, indent=2))

        except Exception as e:
            logger.error(f"保存批量结果失败: {e}")

    async def get_statistics(self) -> Dict[str, Any]:
        """获取检索统计信息"""
        end_time = datetime.now()
        duration = end_time - self.stats['start_time']

        stats = {
            'current_session': {
                'start_time': self.stats['start_time'].isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration.total_seconds(),
                'total_searches': self.stats['total_searches'],
                'successful_searches': self.stats['successful_searches'],
                'failed_searches': self.stats['failed_searches'],
                'success_rate': self.stats['successful_searches'] / max(1, self.stats['total_searches']),
                'total_patents_found': self.stats['total_patents_found']
            },
            'system_info': {
                'browser_use_available': BROWSER_USE_AVAILABLE,
                'playwright_available': PLAYWRIGHT_AVAILABLE,
                'current_method': 'browser_use' if self.use_browser_use else 'playwright',
                'headless_mode': self.headless,
                'max_concurrent': self.max_concurrent
            }
        }

        return stats

    async def close(self):
        """关闭检索器"""
        try:
            if self.use_playwright and self.page:
                await self.page.close()
            if self.use_playwright and self.context:
                await self.context.close()
            if self.use_playwright and self.browser:
                await self.browser.close()
            if self.use_playwright and self.playwright:
                await self.playwright.stop()

            logger.info('🔒 Google Patents检索器已关闭')

        except Exception as e:
            logger.error(f"❌ 关闭检索器失败: {e}")

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    # 缓存相关方法
    def _generate_cache_key(self, query: str, max_results: int, filters: Optional[Dict[str, Any]], priority: PatentPriority) -> str:
        """生成缓存键"""
        cache_data = {
            'query': query,
            'max_results': max_results,
            'filters': filters or {},
            'priority': priority.value
        }
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_str.encode('utf-8'), usedforsecurity=False).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Dict[str, Any] | None:
        """从缓存获取结果"""
        try:
            if cache_key in self.search_cache:
                cached_item = self.search_cache[cache_key]
                # 检查是否过期
                current_time = datetime.now()
                cached_time = datetime.fromisoformat(cached_item['timestamp'])

                if (current_time - cached_time).seconds < self.cache_ttl:
                    # 清理过期的缓存项
                    if 'expired_items' not in self.search_cache:
                        self.search_cache['expired_items'] = []

                    return cached_item['result']
                else:
                    # 移除过期项
                    del self.search_cache[cache_key]
        except Exception as e:
            logger.warning(f"⚠️ 缓存读取失败: {e}")

        return None

    def _save_to_cache(self, cache_key: str, result: Dict[str, Any]):
        """保存结果到缓存"""
        try:
            self.search_cache[cache_key] = {
                'result': result,
                'timestamp': datetime.now().isoformat()
            }

            # 限制缓存大小 - 移除最旧的项
            max_cache_size = 1000
            if len(self.search_cache) > max_cache_size:
                # 按时间排序并移除最旧的项
                sorted_items = sorted(
                    self.search_cache.items(),
                    key=lambda x: x[1]['timestamp']
                )
                # 保留最新的max_cache_size-1个项
                self.search_cache = dict(sorted_items[-(max_cache_size-1):])

        except Exception as e:
            logger.warning(f"⚠️ 缓存保存失败: {e}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return {
            'cache_enabled': self.cache_enabled,
            'cache_ttl': self.cache_ttl,
            'cache_size': len(self.search_cache),
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'cache_hit_rate': self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0
        }

    def clear_cache(self):
        """清空缓存"""
        self.search_cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0
        logger.info('🧹 缓存已清空')