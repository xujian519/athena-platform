#!/usr/bin/env python3
from __future__ import annotations
"""
浏览器自动化工具 - 小诺集成
Browser Automation Tool for Xiaonuo

为小诺提供浏览器自动化能力的工具集成

作者: 小诺·双鱼公主
版本: v1.0.0
"""

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)

# 浏览器自动化服务配置
BROWSER_SERVICE_URL = "http://localhost:8030"


class BrowserAutomationTool:
    """
    浏览器自动化工具

    为小诺提供浏览器自动化能力,包括:
    - 页面导航
    - 元素交互
    - 表单填写
    - 截图
    - 内容提取
    - JavaScript执行
    """

    def __init__(self, service_url: str = BROWSER_SERVICE_URL):
        """
        初始化浏览器自动化工具

        Args:
            service_url: 浏览器自动化服务地址
        """
        self.service_url = service_url.rstrip("/")
        self.session = requests.Session()

    def _make_request(
        self, method: str, endpoint: str, data: dict | None = None
    ) -> dict[str, Any]:
        """
        发送HTTP请求

        Args:
            method: HTTP方法
            endpoint: API端点
            data: 请求数据

        Returns:
            响应数据
        """
        url = f"{self.service_url}{endpoint}"

        try:
            if method.upper() == "GET":
                response = self.session.get(url, timeout=30)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, timeout=30)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 请求失败: {e}")
            return {"success": False, "error": str(e), "message": "浏览器自动化服务请求失败"}

    def health_check(self) -> dict[str, Any]:
        """
        健康检查

        Returns:
            服务状态信息
        """
        return self._make_request("GET", "/health")

    def navigate(self, url: str, wait_until: str = "load") -> dict[str, Any]:
        """
        导航到指定URL

        Args:
            url: 目标URL
            wait_until: 等待条件 (load, domcontentloaded, networkidle)

        Returns:
            导航结果
        """
        logger.info(f"🌐 导航到: {url}")
        return self._make_request(
            "POST", "/api/v1/navigate", {"url": url, "wait_until": wait_until}
        )

    def click(self, selector: str, timeout: int | None = None) -> dict[str, Any]:
        """
        点击元素

        Args:
            selector: CSS选择器
            timeout: 超时时间(毫秒)

        Returns:
            点击结果
        """
        logger.info(f"🖱️  点击元素: {selector}")
        return self._make_request(
            "POST", "/api/v1/click", {"selector": selector, "timeout": timeout}
        )

    def fill(self, selector: str, value: str, timeout: int | None = None) -> dict[str, Any]:
        """
        填写表单

        Args:
            selector: CSS选择器
            value: 填写的值
            timeout: 超时时间(毫秒)

        Returns:
            填写结果
        """
        logger.info(f"✍️  填写表单: {selector} = {value}")
        return self._make_request(
            "POST", "/api/v1/fill", {"selector": selector, "value": value, "timeout": timeout}
        )

    def screenshot(self, full_page: bool = False) -> dict[str, Any]:
        """
        截取当前页面

        Args:
            full_page: 是否截取整个页面

        Returns:
            截图结果(包含base64图片)
        """
        logger.info(f"📸 截图 (full_page={full_page})")
        return self._make_request("POST", "/api/v1/screenshot", {"full_page": full_page})

    def get_content(self) -> dict[str, Any]:
        """
        获取当前页面内容

        Returns:
            页面内容(HTML、文本等)
        """
        logger.info("📄 获取页面内容")
        return self._make_request("GET", "/api/v1/content")

    def evaluate(self, script: str) -> dict[str, Any]:
        """
        执行JavaScript代码

        Args:
            script: JavaScript代码

        Returns:
            执行结果
        """
        logger.info(f"🔨 执行JavaScript: {script[:50]}...")
        return self._make_request("POST", "/api/v1/evaluate", {"script": script})

    def execute_task(self, task: str) -> dict[str, Any]:
        """
        执行自动化任务

        Args:
            task: 任务描述,如"打开百度并搜索Athena"

        Returns:
            任务执行结果
        """
        logger.info(f"🎯 执行任务: {task}")
        return self._make_request("POST", "/api/v1/task", {"task": task})

    def get_status(self) -> dict[str, Any]:
        """
        获取浏览器代理状态

        Returns:
            代理状态信息
        """
        return self._make_request("GET", "/api/v1/status")

    def get_config(self) -> dict[str, Any]:
        """
        获取当前配置

        Returns:
            配置信息
        """
        return self._make_request("GET", "/api/v1/config")


# =============================================================================
# 工具信息注册
# =============================================================================

TOOL_INFO = {
    "name": "browser_automation",
    "description": "浏览器自动化工具 - 提供页面导航、元素交互、表单填写、截图等功能",
    "version": "1.0.0",
    "author": "小诺·双鱼公主",
    "capabilities": [
        "navigate - 导航到指定URL",
        "click - 点击页面元素",
        "fill - 填写表单",
        "screenshot - 截取页面",
        "get_content - 获取页面内容",
        "evaluate - 执行JavaScript",
        "execute_task - 执行自动化任务",
        "health_check - 健康检查",
    ],
    "parameters": {
        "navigate": {
            "url": {"type": "string", "required": True, "description": "目标URL"},
            "wait_until": {
                "type": "string",
                "required": False,
                "default": "load",
                "description": "等待条件",
            },
        },
        "click": {
            "selector": {"type": "string", "required": True, "description": "CSS选择器"},
            "timeout": {"type": "integer", "required": False, "description": "超时时间(毫秒)"},
        },
        "fill": {
            "selector": {"type": "string", "required": True, "description": "CSS选择器"},
            "value": {"type": "string", "required": True, "description": "填写的值"},
            "timeout": {"type": "integer", "required": False, "description": "超时时间(毫秒)"},
        },
        "screenshot": {
            "full_page": {
                "type": "boolean",
                "required": False,
                "default": False,
                "description": "是否截取整个页面",
            }
        },
        "evaluate": {
            "script": {"type": "string", "required": True, "description": "JavaScript代码"}
        },
        "execute_task": {"task": {"type": "string", "required": True, "description": "任务描述"}},
    },
    "examples": [
        {
            "description": "导航到百度首页",
            "action": "navigate",
            "params": {"url": "https://www.baidu.com"},
        },
        {
            "description": "搜索关键词",
            "action": "execute_task",
            "params": {"task": "打开百度并搜索小诺双鱼公主"},
        },
        {"description": "截取当前页面", "action": "screenshot", "params": {"full_page": True}},
        {"description": "获取页面内容", "action": "get_content", "params": {}},
    ],
    "service_endpoint": BROWSER_SERVICE_URL,
    "service_port": 8030,
    "documentation": "http://localhost:8030/docs",
}

# =============================================================================
# 工厂函数
# =============================================================================


def create_browser_tool(service_url: str = BROWSER_SERVICE_URL) -> BrowserAutomationTool:
    """
    创建浏览器自动化工具实例

    Args:
        service_url: 浏览器自动化服务地址

    Returns:
        BrowserAutomationTool实例
    """
    return BrowserAutomationTool(service_url)


# 默认工具实例
default_tool = None


def get_browser_tool() -> BrowserAutomationTool:
    """
    获取默认浏览器自动化工具实例

    Returns:
        BrowserAutomationTool实例
    """
    global default_tool
    if default_tool is None:
        default_tool = create_browser_tool()
    return default_tool


# =============================================================================
# 测试
# =============================================================================

if __name__ == "__main__":
    # 测试浏览器工具
    print("🧪 测试浏览器自动化工具...")

    tool = create_browser_tool()

    # 健康检查
    print("\n1️⃣ 健康检查:")
    health = tool.health_check()
    print(f"   状态: {health.get('status', 'unknown')}")

    # 导航到百度
    print("\n2️⃣ 导航到百度:")
    result = tool.navigate("https://www.baidu.com")
    print(f"   结果: {result.get('success', False)}")

    # 执行任务
    print("\n3️⃣ 执行搜索任务:")
    result = tool.execute_task("打开百度并搜索小诺双鱼公主")
    print(f"   结果: {result.get('success', False)}")

    print("\n✅ 测试完成!")
