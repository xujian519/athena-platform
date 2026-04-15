#!/usr/bin/env python3
"""
Playwright引擎封装
Playwright Engine Wrapper for Browser Automation Service

作者: 小诺·双鱼公主
版本: 1.0.0
"""

from typing import Any

from config.browser_config import BrowserConfig
from config.settings import logger
from playwright.async_api import (
    Browser,
    BrowserContext,
    BrowserType,
    Page,
    async_playwright,
)


class PlaywrightEngine:
    """
    Playwright引擎封装类

    提供浏览器启动、页面创建等基础功能
    """

    def __init__(self, config: BrowserConfig | None = None):
        """
        初始化Playwright引擎

        Args:
            config: 浏览器配置
        """
        self.config = config or BrowserConfig()
        self.playwright = None
        self.browser: Browser | None = None
        self.contexts: dict[str, BrowserContext] = {}
        self._pages: dict[str, dict[str, Page]] = {}  # {context_id: {page_id: Page}}
        self._page_counter = 0  # 用于生成唯一页面ID
        self._initialized = False

    async def initialize(self) -> None:
        """初始化Playwright引擎"""
        if self._initialized:
            return

        try:
            logger.info("🚀 初始化Playwright引擎...")
            self.playwright = await async_playwright().start()

            # 启动浏览器
            browser_type = self._get_browser_type()
            launch_options = self.config.get_launch_options()

            self.browser = await browser_type.launch(**launch_options)

            self._initialized = True
            logger.info(f"✅ Playwright引擎初始化成功 (浏览器: {self.config.browser_type})")

        except Exception as e:
            logger.error(f"❌ Playwright引擎初始化失败: {e}")
            raise

    def _get_browser_type(self) -> BrowserType:
        """获取浏览器类型"""
        browser_types = {
            "chromium": self.playwright.chromium,
            "firefox": self.playwright.firefox,
            "webkit": self.playwright.webkit,
        }
        browser_type = browser_types.get(self.config.browser_type)
        if not browser_type:
            raise ValueError(f"不支持的浏览器类型: {self.config.browser_type}")
        return browser_type

    async def create_context(
        self,
        context_id: str,
        user_agent: str | None = None,
        viewport: dict[str, int] | None = None,
    ) -> BrowserContext:
        """
        创建浏览器上下文

        Args:
            context_id: 上下文ID
            user_agent: 自定义用户代理
            viewport: 视口大小

        Returns:
            BrowserContext: 浏览器上下文
        """
        if not self._initialized:
            await self.initialize()

        if context_id in self.contexts:
            logger.warning(f"⚠️ 上下文 {context_id} 已存在，返回现有上下文")
            return self.contexts[context_id]

        try:
            # 创建上下文选项
            context_options: dict[str, Any] = {
                "viewport": viewport or self.config.viewport,
                "java_script_enabled": True,
            }

            # 设置用户代理
            if user_agent or self.config.user_agent:
                context_options["user_agent"] = user_agent or self.config.user_agent

            # 创建上下文
            context = await self.browser.new_context(**context_options)
            self.contexts[context_id] = context

            # 设置默认超时
            context.set_default_timeout(self.config.default_timeout)
            context.set_default_navigation_timeout(self.config.navigation_timeout)

            logger.info(f"✅ 创建浏览器上下文: {context_id}")
            return context

        except Exception as e:
            logger.error(f"❌ 创建浏览器上下文失败: {e}")
            raise

    async def get_page(self, context_id: str, page_id: str | None = None) -> Page:
        """
        获取或创建页面

        Args:
            context_id: 上下文ID
            page_id: 页面ID（可选）

        Returns:
            Page: 页面对象
        """
        context = self.contexts.get(context_id)
        if not context:
            raise ValueError(f"上下文不存在: {context_id}")

        # 如果没有指定页面ID，创建新页面
        if not page_id:
            page = await context.new_page()
            # 生成唯一页面ID并存储映射
            self._page_counter += 1
            generated_page_id = f"{context_id}_page_{self._page_counter}"
            if context_id not in self._pages:
                self._pages[context_id] = {}
            self._pages[context_id][generated_page_id] = page
            logger.info(f"✅ 创建新页面: {generated_page_id} in {context_id}")
            return page

        # 如果指定了页面ID，查找现有页面
        if context_id in self._pages and page_id in self._pages[context_id]:
            page = self._pages[context_id][page_id]
            # 检查页面是否已关闭
            try:
                _ = page.url
                return page
            except Exception:
                # 页面已关闭，从映射中移除
                del self._pages[context_id][page_id]

        # 页面不存在或已关闭，创建新页面
        page = await context.new_page()
        if context_id not in self._pages:
            self._pages[context_id] = {}
        self._pages[context_id][page_id] = page
        logger.info(f"✅ 创建新页面: {page_id} in {context_id}")
        return page

    async def close_context(self, context_id: str) -> None:
        """
        关闭浏览器上下文

        Args:
            context_id: 上下文ID
        """
        context = self.contexts.get(context_id)
        if context:
            # 清理该上下文的所有页面映射
            if context_id in self._pages:
                del self._pages[context_id]
            await context.close()
            del self.contexts[context_id]
            logger.info(f"🗑️  关闭浏览器上下文: {context_id}")

    async def close_all_contexts(self) -> None:
        """关闭所有浏览器上下文"""
        for context_id in list(self.contexts.keys()):
            await self.close_context(context_id)
        logger.info("🗑️  关闭所有浏览器上下文")

    async def shutdown(self) -> None:
        """关闭Playwright引擎"""
        try:
            # 关闭所有上下文
            await self.close_all_contexts()

            # 关闭浏览器
            if self.browser:
                await self.browser.close()
                self.browser = None

            # 停止Playwright
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None

            self._initialized = False
            logger.info("🛑 Playwright引擎已关闭")

        except Exception as e:
            logger.error(f"❌ 关闭Playwright引擎时出错: {e}")

    @property
    def is_initialized(self) -> bool:
        """检查引擎是否已初始化"""
        return self._initialized

    @property
    def active_contexts_count(self) -> int:
        """获取活跃上下文数量"""
        return len(self.contexts)


# 全局引擎实例
_engine: PlaywrightEngine | None = None


async def get_engine() -> PlaywrightEngine:
    """获取全局引擎实例"""
    global _engine
    if _engine is None:
        _engine = PlaywrightEngine()
        await _engine.initialize()
    return _engine


async def close_engine() -> None:
    """关闭全局引擎"""
    global _engine
    if _engine:
        await _engine.shutdown()
        _engine = None


# 导出
__all__ = [
    "PlaywrightEngine",
    "get_engine",
    "close_engine",
]
