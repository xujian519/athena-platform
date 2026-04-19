#!/usr/bin/env python3
"""
Chrome MCP集成工具
基于Playwright的智能浏览器自动化和MCP集成
作者: 小娜 & 小诺
创建时间: 2025-12-04
"""

import asyncio
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Playwright相关
from playwright.async_api import async_playwright

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChromeMCPIntegration:
    """Chrome MCP集成系统"""

    def __init__(self, headless: bool = False, timeout: int = 30000):
        """
        初始化Chrome MCP集成系统

        Args:
            headless: 是否无头模式运行
            timeout: 超时时间（毫秒）
        """
        self.headless = headless
        self.timeout = timeout
        self.browser = None
        self.context = None
        self.page = None
        self.is_initialized = False

        logger.info('🌐 Chrome MCP集成系统初始化')

    async def initialize(self):
        """初始化浏览器"""
        if self.is_initialized:
            return

        try:
            logger.info('🚀 启动Playwright浏览器...')

            self.playwright = await async_playwright().start()

            # 启动Chromium浏览器
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas-usage',
                    '--no-first-run',
                    '--no-zygote',
                    '--single-process',
                    '--disable-gpu'
                ]
            )

            # 创建浏览器上下文
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                ignore_https_errors=True
            )

            # 创建页面
            self.page = await self.context.new_page()

            # 设置页面超时
            self.page.set_default_timeout(self.timeout)

            self.is_initialized = True
            logger.info('✅ Chrome MCP集成系统初始化完成')

        except Exception as e:
            logger.error(f"❌ Chrome MCP初始化失败: {e}")
            raise

    async def close(self):
        """关闭浏览器"""
        if self.page:
            await self.page.close()
            self.page = None

        if self.context:
            await self.context.close()
            self.context = None

        if self.browser:
            await self.browser.close()
            self.browser = None

        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

        self.is_initialized = False
        logger.info('🔄 Chrome MCP集成系统已关闭')

    async def navigate_to(self, url: str) -> dict[str, Any]:
        """
        导航到指定URL

        Args:
            url: 目标URL

        Returns:
            导航结果
        """
        if not self.is_initialized:
            await self.initialize()

        try:
            start_time = time.time()
            logger.info(f"🧭 导航到: {url}")

            await self.page.goto(url)

            # 等待页面加载完成
            await self.page.wait_for_load_state('networkidle', timeout=10000)

            # 获取页面信息
            title = await self.page.title()
            current_url = self.page.url

            load_time = time.time() - start_time

            result = {
                'success': True,
                'url': current_url,
                'title': title,
                'load_time': load_time,
                'timestamp': datetime.now().isoformat()
            }

            logger.info(f"✅ 页面加载完成: {title} ({load_time:.2f}s)")
            return result

        except Exception as e:
            logger.error(f"❌ 导航失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'url': url,
                'timestamp': datetime.now().isoformat()
            }

    async def extract_content(self, selectors: dict[str, str] = None) -> dict[str, Any]:
        """
        提取页面内容

        Args:
            selectors: CSS选择器映射

        Returns:
            提取的内容
        """
        if not self.page:
            return {'success': False, 'error': '浏览器未初始化'}

        try:
            content = {}

            # 默认选择器
            default_selectors = {
                'title': 'title',
                'h1': 'h1',
                'h2': 'h2',
                'main_content': 'main, article, .content, .main',
                'paragraphs': 'p',
                'links': 'a[href]'
            }

            # 合并选择器
            all_selectors = {**default_selectors, **(selectors or {})}

            for name, selector in all_selectors.items():
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        if name == 'links':
                            # 特殊处理链接
                            links = []
                            for element in elements:
                                href = await element.get_attribute('href')
                                text = await element.text_content()
                                if href and text:
                                    links.append({
                                        'url': href,
                                        'text': text.strip()
                                    })
                            content[name] = links
                        else:
                            # 普通文本内容
                            texts = []
                            for element in elements:
                                text = await element.text_content()
                                if text:
                                    texts.append(text.strip())
                            content[name] = texts
                except Exception as e:
                    logger.warning(f"⚠️ 提取选择器 {selector} 失败: {e}")
                    content[name] = []

            # 获取页面URL和标题
            content['page_url'] = self.page.url
            content['page_title'] = await self.page.title()

            return {
                'success': True,
                'content': content,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ 内容提取失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def take_screenshot(self, filename: str = None, full_page: bool = True) -> dict[str, Any]:
        """
        截取页面截图

        Args:
            filename: 截图文件名
            full_page: 是否截取整个页面

        Returns:
            截图结果
        """
        if not self.page:
            return {'success': False, 'error': '浏览器未初始化'}

        try:
            if not filename:
                filename = f"screenshot_{int(time.time())}.png"

            # 确保目录存在
            screenshot_dir = Path('screenshots')
            screenshot_dir.mkdir(exist_ok=True)

            screenshot_path = screenshot_dir / filename

            await self.page.screenshot(
                path=str(screenshot_path),
                full_page=full_page
            )

            return {
                'success': True,
                'filename': filename,
                'path': str(screenshot_path),
                'full_page': full_page,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ 截图失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def execute_script(self, script: str) -> dict[str, Any]:
        """
        执行JavaScript脚本

        Args:
            script: JavaScript代码

        Returns:
            执行结果
        """
        if not self.page:
            return {'success': False, 'error': '浏览器未初始化'}

        try:
            result = await self.page.evaluate(script)

            return {
                'success': True,
                'result': result,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ 脚本执行失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def search_patents(self, query: str, source: str = 'google_patents') -> dict[str, Any]:
        """
        搜索专利

        Args:
            query: 搜索查询
            source: 数据源

        Returns:
            搜索结果
        """
        search_urls = {
            'google_patents': f"https://patents.google.com/?q={query}",
            'uspto': f"https://patft.uspto.gov/netacgi/nph-Parser?patentnumber={query}",
            'epo': f"https://worldwide.espacenet.com/searchResults?query={query}"
        }

        url = search_urls.get(source, search_urls['google_patents'])

        # 导航到搜索页面
        nav_result = await self.navigate_to(url)
        if not nav_result['success']:
            return nav_result

        # 等待搜索结果加载
        try:
            await self.page.wait_for_selector('.search-result, .result-item, .patent-result', timeout=10000)
        except Exception:
            logger.warning('⚠️ 搜索结果选择器未找到，尝试提取内容')

        # 提取搜索结果
        selectors = {
            'patent_results': '.search-result, .result-item, .patent-result',
            'patent_titles': '.patent-title, .title, h3',
            'patent_numbers': '.patent-number, .publication-number',
            'patent_abstracts': '.patent-summary, .abstract, .summary'
        }

        content_result = await self.extract_content(selectors)

        return {
            'success': True,
            'query': query,
            'source': source,
            'url': url,
            'results': content_result.get('content', {}),
            'timestamp': datetime.now().isoformat()
        }

    async def wait_and_click(self, selector: str, timeout: int = 5000) -> dict[str, Any]:
        """
        等待并点击元素

        Args:
            selector: CSS选择器
            timeout: 超时时间

        Returns:
            点击结果
        """
        if not self.page:
            return {'success': False, 'error': '浏览器未初始化'}

        try:
            # 等待元素出现
            element = await self.page.wait_for_selector(selector, timeout=timeout)

            # 滚动到元素
            await element.scroll_into_view_if_needed()

            # 点击元素
            await element.click()

            return {
                'success': True,
                'selector': selector,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ 点击失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'selector': selector,
                'timestamp': datetime.now().isoformat()
            }

    async def fill_form(self, form_data: dict[str, str]) -> dict[str, Any]:
        """
        填充表单

        Args:
            form_data: 表单数据 {selector: value}

        Returns:
            填充结果
        """
        if not self.page:
            return {'success': False, 'error': '浏览器未初始化'}

        try:
            results = {}

            for selector, value in form_data.items():
                try:
                    # 等待输入框
                    element = await self.page.wait_for_selector(selector, timeout=5000)

                    # 清空并填充
                    await element.clear()
                    await element.fill(value)

                    results[selector] = 'success'

                except Exception as e:
                    results[selector] = f"failed: {e}"
                    logger.warning(f"⚠️ 填充失败 {selector}: {e}")

            return {
                'success': True,
                'results': results,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ 表单填充失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


# 全局实例管理
_chrome_mcp = None

def get_chrome_mcp() -> ChromeMCPIntegration:
    """获取Chrome MCP实例"""
    global _chrome_mcp
    if _chrome_mcp is None:
        _chrome_mcp = ChromeMCPIntegration()
    return _chrome_mcp


# 便捷函数
async def quick_navigate(url: str) -> dict[str, Any]:
    """快速导航"""
    chrome = get_chrome_mcp()
    return await chrome.navigate_to(url)


async def quick_extract(selectors: dict[str, str] = None) -> dict[str, Any]:
    """快速提取内容"""
    chrome = get_chrome_mcp()
    return await chrome.extract_content(selectors)


async def quick_screenshot(filename: str = None) -> dict[str, Any]:
    """快速截图"""
    chrome = get_chrome_mcp()
    return await chrome.take_screenshot(filename)


# 测试函数
async def test_chrome_mcp():
    """测试Chrome MCP功能"""
    logger.info('🧪 测试Chrome MCP集成功能...')

    chrome = get_chrome_mcp()

    try:
        # 初始化
        await chrome.initialize()
        logger.info('✅ Chrome初始化成功')

        # 测试导航
        logger.info("\n1️⃣ 测试导航功能...")
        nav_result = await chrome.navigate_to('https://www.example.com')
        if nav_result['success']:
            logger.info(f"   ✅ 导航成功: {nav_result['title']}")
        else:
            logger.info(f"   ❌ 导航失败: {nav_result.get('error')}")

        # 测试内容提取
        logger.info("\n2️⃣ 测试内容提取...")
        extract_result = await chrome.extract_content()
        if extract_result['success']:
            content = extract_result['content']
            logger.info(f"   ✅ 提取成功: 标题='{content.get('page_title', '')}'")
            logger.info(f"   H1标题数量: {len(content.get('h1', []))}")
        else:
            logger.info(f"   ❌ 提取失败: {extract_result.get('error')}")

        # 测试截图
        logger.info("\n3️⃣ 测试截图功能...")
        screenshot_result = await chrome.take_screenshot('test_screenshot.png')
        if screenshot_result['success']:
            logger.info(f"   ✅ 截图成功: {screenshot_result['path']}")
        else:
            logger.info(f"   ❌ 截图失败: {screenshot_result.get('error')}")

        # 测试脚本执行
        logger.info("\n4️⃣ 测试脚本执行...")
        script_result = await chrome.execute_script('document.title')
        if script_result['success']:
            logger.info(f"   ✅ 脚本执行成功: {script_result['result']}")
        else:
            logger.info(f"   ❌ 脚本执行失败: {script_result.get('error')}")

        logger.info("\n🎉 Chrome MCP集成功能测试完成！")

    except Exception as e:
        logger.info(f"❌ 测试过程异常: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 关闭浏览器
        await chrome.close()


if __name__ == '__main__':
    asyncio.run(test_chrome_mcp())
