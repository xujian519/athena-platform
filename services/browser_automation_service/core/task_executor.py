#!/usr/bin/env python3
"""
智能任务执行器
Task Executor for Browser Automation Service

作者: 小诺·双鱼公主
版本: 1.0.0
"""

import re
import uuid
from typing import Any

from config.settings import logger

from core.browser_manager import BrowserManager

# 预编译正则表达式以提高性能
URL_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?[\w\-]+\.[\w\-]+(?:\.[\w\-]+)*/?[^\s]*"
)
SEARCH_PATTERN = re.compile(
    r'搜索[：:"]*([^"\']+)|search\s+for\s+(\w+)'
)
CLICK_PATTERN = re.compile(
    r'点击[：:"]*([^"\']+)|click\s+(?:on\s+)?(?:the\s+)?["\']?([^"\']+)["\']?'
)


class TaskExecutor:
    """
    智能任务执行器

    将自然语言任务转换为浏览器操作序列
    """

    def __init__(self, browser_manager: BrowserManager | None = None):
        """
        初始化任务执行器

        Args:
            browser_manager: 浏览器管理器
        """
        self.browser_manager = browser_manager

    async def _get_manager(self) -> BrowserManager:
        """获取浏览器管理器"""
        if self.browser_manager is None:
            from core.browser_manager import get_browser_manager

            self.browser_manager = await get_browser_manager()
        return self.browser_manager

    async def execute(self, task: str, url: str | None = None, **kwargs) -> dict[str, Any]:
        """
        执行自然语言任务

        Args:
            task: 任务描述
            url: 起始URL
            **kwargs: 其他参数

        Returns:
            dict: 执行结果
        """
        task_id = str(uuid.uuid4())
        manager = await self._get_manager()

        logger.info(f"🎯 执行任务 [{task_id[:8]}]: {task}")

        try:
            # 解析任务
            actions = await self._parse_task(task, url)

            # 执行操作序列
            results = []
            screenshots = []

            for i, action in enumerate(actions):
                logger.info(f"  📍 步骤 {i + 1}/{len(actions)}: {action['description']}")

                result = await self._execute_action(action, manager)
                results.append(result)

                # 如果失败，停止执行
                if not result.get("success"):
                    logger.error(f"❌ 任务执行失败于步骤 {i + 1}")
                    return {
                        "success": False,
                        "task_id": task_id,
                        "task": task,
                        "status": "failed",
                        "steps_taken": i + 1,
                        "message": f"任务执行失败: {result.get('message', '未知错误')}",
                        "error": result.get("error"),
                        "screenshots": screenshots,
                    }

                # 收集截图（如果是截图操作）
                if action.get("type") == "screenshot" and result.get("success"):
                    screenshots.append(result.get("screenshot", ""))

            return {
                "success": True,
                "task_id": task_id,
                "task": task,
                "status": "completed",
                "steps_taken": len(results),
                "message": "任务执行成功",
                "screenshots": screenshots,
            }

        except Exception as e:
            logger.error(f"❌ 任务执行异常: {e}")
            return {
                "success": False,
                "task_id": task_id,
                "task": task,
                "status": "failed",
                "message": f"任务执行异常: {e}",
                "error": str(e),
            }

    async def _parse_task(self, task: str, url: str | None = None) -> list[dict[str, Any]]:
        """
        解析自然语言任务

        Args:
            task: 任务描述
            url: 起始URL

        Returns:
            list: 操作序列
        """
        actions = []
        task_lower = task.lower()

        # 1. 导航操作
        # 提取URL（使用预编译正则表达式）
        urls = URL_PATTERN.findall(task)

        if urls:
            target_url = urls[0]
            if not target_url.startswith("http"):
                target_url = "https://" + target_url
            actions.append(
                {"type": "navigate", "url": target_url, "description": f"导航到 {target_url}"}
            )
        elif url:
            actions.append(
                {"type": "navigate", "url": url, "description": f"导航到 {url}"}
            )

        # 2. 搜索操作
        if "搜索" in task or "search" in task_lower:
            # 提取搜索关键词（使用预编译正则表达式）
            search_match = SEARCH_PATTERN.search(task)
            if search_match:
                keyword = search_match.group(1) or search_match.group(2)

                # 百度搜索
                if "百度" in task or "baidu" in task_lower:
                    actions.append(
                        {"type": "navigate", "url": "https://www.baidu.com", "description": "打开百度"}
                    )
                    actions.append(
                        {"type": "fill", "selector": "#kw", "value": keyword, "description": f"输入搜索词: {keyword}"}
                    )
                    actions.append(
                        {"type": "click", "selector": "#su", "description": "点击搜索按钮"}
                    )

                # Google搜索
                elif "google" in task_lower or "谷歌" in task:
                    actions.append(
                        {"type": "navigate", "url": "https://www.google.com", "description": "打开Google"}
                    )
                    actions.append(
                        {"type": "fill", "selector": "textarea[name='q']", "value": keyword, "description": f"输入搜索词: {keyword}"}
                    )

        # 3. 点击操作
        if "点击" in task or "click" in task_lower:
            # 提取按钮/元素描述（使用预编译正则表达式）
            click_match = CLICK_PATTERN.search(task)
            if click_match:
                element = click_match.group(1) or click_match.group(2)
                # 简单的选择器映射
                selector = self._map_element_to_selector(element)
                if selector:
                    actions.append(
                        {"type": "click", "selector": selector, "description": f"点击 {element}"}
                    )

        # 4. 截图操作
        if "截图" in task or "screenshot" in task_lower:
            actions.append({"type": "screenshot", "full_page": False, "description": "截取页面"})

        # 如果没有识别到任何操作，添加默认操作
        if not actions and urls:
            # 只有一个URL，执行导航
            pass

        return actions

    def _map_element_to_selector(self, element: str) -> str | None:
        """
        将元素描述映射到CSS选择器

        Args:
            element: 元素描述

        Returns:
            str | None: CSS选择器
        """
        element_lower = element.lower()

        # 常见元素映射
        mappings = {
            "搜索按钮": "#su",
            "search button": "button[type='submit']",
            "登录按钮": ".login-btn, #login-btn, button:has-text('登录')",
            "login button": ".login-btn, #login-btn, button:has-text('Login')",
            "提交按钮": "button[type='submit'], .submit-btn",
            "submit button": "button[type='submit'], .submit-btn",
            "确定": "button:has-text('确定'), .confirm-btn",
            "confirm": "button:has-text('Confirm'), .confirm-btn",
        }

        return mappings.get(element_lower.strip())

    async def _execute_action(
        self, action: dict[str, Any], manager: BrowserManager
    ) -> dict[str, Any]:
        """
        执行单个操作

        Args:
            action: 操作定义
            manager: 浏览器管理器

        Returns:
            dict: 执行结果
        """
        action_type = action.get("type")

        if action_type == "navigate":
            return await manager.navigate(action.get("url", ""))

        elif action_type == "click":
            return await manager.click(
                action.get("selector", ""),
                timeout=action.get("timeout", 5000),
            )

        elif action_type == "fill":
            return await manager.fill(
                action.get("selector", ""),
                action.get("value", ""),
                timeout=action.get("timeout", 5000),
            )

        elif action_type == "screenshot":
            return await manager.screenshot(full_page=action.get("full_page", False))

        else:
            return {"success": False, "error": f"未知操作类型: {action_type}"}


# 导出
__all__ = ["TaskExecutor"]
