#!/usr/bin/env python3
"""
浏览器管理器
Browser Manager for Browser Automation Service

作者: 小诺·双鱼公主
版本: 1.0.0
"""

import base64
import uuid
from typing import Any

from config.browser_config import BrowserConfig, get_browser_config
from config.settings import logger

from core.playwright_engine import PlaywrightEngine, get_engine
from core.session_manager import Session, get_session_manager


class BrowserManager:
    """
    浏览器管理器

    提供高层浏览器操作API，包括导航、点击、填充、截图等功能
    """

    def __init__(self, config: BrowserConfig | None = None):
        """
        初始化浏览器管理器

        Args:
            config: 浏览器配置
        """
        self.config = config or get_browser_config()
        self.engine: PlaywrightEngine | None = None
        self.session_manager = get_session_manager()
        self._current_context_id: str | None = None

    async def initialize(self) -> None:
        """初始化浏览器管理器"""
        logger.info("🔧 初始化浏览器管理器...")
        self.engine = await get_engine()
        logger.info("✅ 浏览器管理器就绪")

    async def _get_or_create_session(self, session_id: str | None = None) -> Session:
        """
        获取或创建会话

        Args:
            session_id: 会话ID（可选）

        Returns:
            Session: 会话对象
        """
        # 确保引擎已初始化
        if not self.engine or not self.engine.is_initialized:
            await self.initialize()

        # 生成或使用提供的上下文ID
        context_id = session_id or self._current_context_id or str(uuid.uuid4())

        # 获取或创建上下文
        if context_id not in self.engine.contexts:
            await self.engine.create_context(context_id)

        context = self.engine.contexts[context_id]

        # 获取或创建页面
        page = await self.engine.get_page(context_id)

        # 获取或创建会话
        session = await self.session_manager.get_or_create_default_session(
            page, context, context_id
        )

        # 更新当前上下文ID
        self._current_context_id = context_id

        return session

    async def navigate(
        self, url: str, wait_until: str = "load", session_id: str | None = None
    ) -> dict[str, Any]:
        """
        导航到指定URL

        Args:
            url: 目标URL
            wait_until: 等待条件 (load, domcontentloaded, networkidle)
            session_id: 会话ID

        Returns:
            dict: 导航结果
        """
        session = await self._get_or_create_session(session_id)
        page = session.page

        try:
            logger.info(f"🌐 导航到: {url}")

            response = await page.goto(
                url, wait_until=wait_until, timeout=30000
            )

            title = await page.title()

            return {
                "success": True,
                "url": page.url,
                "title": title,
                "status_code": response.status if response else None,
            }

        except Exception as e:
            logger.error(f"❌ 导航失败: {e}")
            return {"success": False, "error": str(e), "message": f"导航失败: {e}"}

    async def click(
        self, selector: str, timeout: int = 5000, session_id: str | None = None
    ) -> dict[str, Any]:
        """
        点击元素

        Args:
            selector: CSS选择器
            timeout: 超时时间(毫秒)
            session_id: 会话ID

        Returns:
            dict: 点击结果
        """
        session = await self._get_or_create_session(session_id)
        page = session.page

        try:
            logger.info(f"🖱️  点击元素: {selector}")

            await page.click(selector, timeout=timeout)

            return {
                "success": True,
                "selector": selector,
                "message": f"成功点击元素: {selector}",
            }

        except Exception as e:
            logger.error(f"❌ 点击失败: {e}")
            return {"success": False, "error": str(e), "message": f"点击失败: {e}"}

    async def fill(
        self, selector: str, value: str, timeout: int = 5000, session_id: str | None = None
    ) -> dict[str, Any]:
        """
        填写表单

        Args:
            selector: CSS选择器
            value: 填写的值
            timeout: 超时时间(毫秒)
            session_id: 会话ID

        Returns:
            dict: 填写结果
        """
        session = await self._get_or_create_session(session_id)
        page = session.page

        try:
            logger.info(f"✍️  填写表单: {selector} = {value}")

            await page.fill(selector, value, timeout=timeout)

            return {
                "success": True,
                "selector": selector,
                "value": value,
                "message": f"成功填写表单: {selector}",
            }

        except Exception as e:
            logger.error(f"❌ 填写失败: {e}")
            return {"success": False, "error": str(e), "message": f"填写失败: {e}"}

    async def screenshot(
        self, full_page: bool = False, session_id: str | None = None
    ) -> dict[str, Any]:
        """
        截取页面

        Args:
            full_page: 是否截取整个页面
            session_id: 会话ID

        Returns:
            dict: 截图结果
        """
        session = await self._get_or_create_session(session_id)
        page = session.page

        try:
            logger.info(f"📸 截图 (full_page={full_page})")

            screenshot_bytes = await page.screenshot(full_page=full_page)
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode("utf-8")

            viewport_size = page.viewport_size
            width = viewport_size["width"] if viewport_size else 1920
            height = viewport_size["height"] if viewport_size else 1080

            return {
                "success": True,
                "screenshot": screenshot_base64,
                "width": width,
                "height": height,
                "full_page": full_page,
            }

        except Exception as e:
            logger.error(f"❌ 截图失败: {e}")
            return {"success": False, "error": str(e), "message": f"截图失败: {e}"}

    async def get_content(self, session_id: str | None = None) -> dict[str, Any]:
        """
        获取页面内容

        Args:
            session_id: 会话ID

        Returns:
            dict: 页面内容
        """
        session = await self._get_or_create_session(session_id)
        page = session.page

        try:
            logger.info("📄 获取页面内容")

            url = page.url
            title = await page.title()
            text = await page.inner_text("body")

            # 获取链接
            links = await page.eval_on_selector_all(
                "a", "elements => elements.map(e => e.href)"
            )
            links = links or []

            return {
                "success": True,
                "url": url,
                "title": title,
                "text": text,
                "links": links,
            }

        except Exception as e:
            logger.error(f"❌ 获取内容失败: {e}")
            return {"success": False, "error": str(e), "message": f"获取内容失败: {e}"}

    async def evaluate(
        self, script: str, session_id: str | None = None
    ) -> dict[str, Any]:
        """
        执行JavaScript

        Args:
            script: JavaScript代码
            session_id: 会话ID

        Returns:
            dict: 执行结果
        """
        session = await self._get_or_create_session(session_id)
        page = session.page

        try:
            logger.info(f"🔨 执行JavaScript: {script[:50]}...")

            result = await page.evaluate(script)

            return {"success": True, "result": result, "script": script}

        except Exception as e:
            logger.error(f"❌ 执行JavaScript失败: {e}")
            return {"success": False, "error": str(e), "message": f"执行失败: {e}"}

    async def get_status(self) -> dict[str, Any]:
        """
        获取浏览器状态

        Returns:
            dict: 状态信息
        """
        active_sessions = self.session_manager.active_count
        total_sessions = self.session_manager.total_count

        sessions_list = await self.session_manager.list_sessions()

        return {
            "success": True,
            "active_sessions": active_sessions,
            "total_sessions": total_sessions,
            "sessions": sessions_list,
            "engine_initialized": self.engine.is_initialized if self.engine else False,
            "active_contexts": self.engine.active_contexts_count if self.engine else 0,
        }

    async def shutdown(self) -> None:
        """关闭浏览器管理器"""
        logger.info("🛑 关闭浏览器管理器...")
        await self.session_manager.shutdown()
        logger.info("✅ 浏览器管理器已关闭")


# 全局浏览器管理器实例
_browser_manager: BrowserManager | None = None


async def get_browser_manager() -> BrowserManager:
    """获取全局浏览器管理器实例"""
    global _browser_manager
    if _browser_manager is None:
        _browser_manager = BrowserManager()
        await _browser_manager.initialize()
    return _browser_manager


# 导出
__all__ = [
    "BrowserManager",
    "get_browser_manager",
]
