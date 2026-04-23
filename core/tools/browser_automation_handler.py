#!/usr/bin/env python3
from __future__ import annotations
"""
浏览器自动化工具Handler
Browser Automation Tool Handler for Unified Tool Registry

提供浏览器自动化能力的工具处理器，基于Playwright引擎。

Author: Athena平台团队
Created: 2026-04-19
Version: 1.0.0
"""

import logging
import tempfile
from pathlib import Path
from typing import Any

import requests

logger = logging.getLogger(__name__)

# 浏览器自动化服务配置
BROWSER_SERVICE_URL = "http://localhost:8030"
SERVICE_TIMEOUT = 300  # 5分钟超时


class BrowserAutomationClient:
    """
    浏览器自动化客户端

    提供完整的浏览器自动化能力，包括：
    - 页面导航
    - 元素交互（点击、填充表单）
    - 截图
    - 内容提取
    - JavaScript执行
    - 智能任务执行
    """

    def __init__(self, service_url: str = BROWSER_SERVICE_URL):
        """
        初始化客户端

        Args:
            service_url: 浏览器自动化服务地址
        """
        self.service_url = service_url.rstrip("/")
        self.session = requests.Session()
        logger.info(f"🌐 浏览器自动化客户端初始化: {self.service_url}")

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict[str, Any]] = None,
        timeout: int = 30
    ) -> dict[str, Any]:
        """
        发送HTTP请求到浏览器自动化服务

        Args:
            method: HTTP方法
            endpoint: API端点
            data: 请求数据
            timeout: 超时时间(秒)

        Returns:
            响应数据
        """
        url = f"{self.service_url}{endpoint}"

        try:
            if method.upper() == "GET":
                response = self.session.get(url, timeout=timeout)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, timeout=timeout)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.ConnectionError:
            error_msg = (
                f"❌ 无法连接到浏览器自动化服务 ({self.service_url})\n"
                f"   请确认服务已启动: cd services/browser_automation_service && python main.py"
            )
            logger.error(error_msg)
            return {
                "success": False,
                "error": "connection_error",
                "message": error_msg
            }

        except requests.exceptions.Timeout:
            logger.error(f"❌ 请求超时: {url}")
            return {
                "success": False,
                "error": "timeout",
                "message": f"请求超时({timeout}秒)"
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 请求失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "浏览器自动化服务请求失败"
            }

    def health_check(self) -> dict[str, Any]:
        """健康检查"""
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
        return self._make_request(
            "POST",
            "/api/v1/navigate",
            {"url": url, "wait_until": wait_until}
        )

    def click(self, selector: str, timeout: Optional[int] = None) -> dict[str, Any]:
        """
        点击元素

        Args:
            selector: CSS选择器
            timeout: 超时时间(毫秒)

        Returns:
            点击结果
        """
        return self._make_request(
            "POST",
            "/api/v1/click",
            {"selector": selector, "timeout": timeout}
        )

    def fill(self, selector: str, value: str, timeout: Optional[int] = None) -> dict[str, Any]:
        """
        填写表单

        Args:
            selector: CSS选择器
            value: 填写的值
            timeout: 超时时间(毫秒)

        Returns:
            填写结果
        """
        return self._make_request(
            "POST",
            "/api/v1/fill",
            {"selector": selector, "value": value, "timeout": timeout}
        )

    def screenshot(self, full_page: bool = False, save_path: Optional[str] = None) -> dict[str, Any]:
        """
        截取当前页面

        Args:
            full_page: 是否截取整个页面
            save_path: 保存路径（可选）

        Returns:
            截图结果
        """
        result = self._make_request(
            "POST",
            "/api/v1/screenshot",
            {"full_page": full_page}
        )

        # 如果指定了保存路径，保存base64图片
        if save_path and result.get("success") and "data" in result:
            try:
                import base64

                # 解码base64图片数据
                image_data = base64.b64decode(result["data"])

                # 保存到文件
                save_path_obj = Path(save_path)
                save_path_obj.parent.mkdir(parents=True, exist_ok=True)
                save_path_obj.write_bytes(image_data)

                result["saved_path"] = str(save_path_obj)

            except Exception as e:
                logger.warning(f"截图保存失败: {e}")

        return result

    def get_content(self) -> dict[str, Any]:
        """
        获取当前页面内容

        Returns:
            页面内容
        """
        return self._make_request("GET", "/api/v1/content")

    def evaluate(self, script: str) -> dict[str, Any]:
        """
        执行JavaScript代码

        Args:
            script: JavaScript代码

        Returns:
            执行结果
        """
        return self._make_request(
            "POST",
            "/api/v1/evaluate",
            {"script": script}
        )

    def execute_task(self, task: str) -> dict[str, Any]:
        """
        执行自动化任务

        Args:
            task: 任务描述

        Returns:
            任务执行结果
        """
        return self._make_request(
            "POST",
            "/api/v1/task",
            {"task": task},
            timeout=SERVICE_TIMEOUT  # 任务执行可能需要较长时间
        )


# =============================================================================
# 全局客户端实例
# =============================================================================

_global_client: BrowserAutomationClient | None = None


def get_browser_client(service_url: str = BROWSER_SERVICE_URL) -> BrowserAutomationClient:
    """
    获取浏览器自动化客户端实例（单例模式）

    Args:
        service_url: 服务URL

    Returns:
        浏览器自动化客户端
    """
    global _global_client
    if _global_client is None:
        _global_client = BrowserAutomationClient(service_url)
    return _global_client


# =============================================================================
# Handler函数（统一工具注册表接口）
# =============================================================================

async def browser_automation_handler(
    params: dict[str, Any],
    context: dict[str, Any]
) -> dict[str, Any]:
    """
    浏览器自动化工具Handler

    功能:
    1. 页面导航
    2. 元素交互（点击、填充表单）
    3. 页面截图
    4. 内容提取
    5. JavaScript执行
    6. 智能任务执行

    Args:
        params: {
            "action": str,              # 操作类型: health_check, navigate, click, fill, screenshot, get_content, evaluate, execute_task
            "url": str,                 # 目标URL（navigate时必需）
            "selector": str,            # CSS选择器（click/fill时必需）
            "value": str,               # 填充值（fill时必需）
            "script": str,              # JavaScript代码（evaluate时必需）
            "task": str,                # 任务描述（execute_task时必需）
            "wait_until": str,          # 等待条件（可选，默认"load"）
            "timeout": int,             # 超时时间（可选）
            "full_page": bool,          # 是否全页截图（可选）
            "save_path": str,           # 截图保存路径（可选）
            "service_url": str,         # 服务URL（可选）
        }
        context: 上下文信息

    Returns:
        执行结果
    """
    # 获取参数
    action = params.get("action", "navigate")
    service_url = params.get("service_url", BROWSER_SERVICE_URL)

    # 获取客户端
    client = get_browser_client(service_url)

    # 根据action类型执行不同操作
    try:
        if action == "health_check":
            result = client.health_check()

        elif action == "navigate":
            url = params.get("url")
            if not url:
                return {
                    "success": False,
                    "error": "缺少必需参数: url",
                    "required_params": ["url"]
                }
            wait_until = params.get("wait_until", "load")
            result = client.navigate(url, wait_until)

        elif action == "click":
            selector = params.get("selector")
            if not selector:
                return {
                    "success": False,
                    "error": "缺少必需参数: selector",
                    "required_params": ["selector"]
                }
            timeout = params.get("timeout")
            result = client.click(selector, timeout)

        elif action == "fill":
            selector = params.get("selector")
            value = params.get("value")
            if not selector or value is None:
                return {
                    "success": False,
                    "error": "缺少必需参数: selector, value",
                    "required_params": ["selector", "value"]
                }
            timeout = params.get("timeout")
            result = client.fill(selector, value, timeout)

        elif action == "screenshot":
            full_page = params.get("full_page", False)
            save_path = params.get("save_path")
            result = client.screenshot(full_page, save_path)

        elif action == "get_content":
            result = client.get_content()

        elif action == "evaluate":
            script = params.get("script")
            if not script:
                return {
                    "success": False,
                    "error": "缺少必需参数: script",
                    "required_params": ["script"]
                }
            result = client.evaluate(script)

        elif action == "execute_task":
            task = params.get("task")
            if not task:
                return {
                    "success": False,
                    "error": "缺少必需参数: task",
                    "required_params": ["task"]
                }
            result = client.execute_task(task)

        else:
            return {
                "success": False,
                "error": f"不支持的操作: {action}",
                "supported_actions": [
                    "health_check", "navigate", "click", "fill",
                    "screenshot", "get_content", "evaluate", "execute_task"
                ]
            }

        # 添加成功标识
        if "success" not in result:
            result["success"] = True

        return result

    except Exception as e:
        logger.error(f"浏览器自动化操作失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "action": action
        }


# =============================================================================
# 便捷函数
# =============================================================================

async def navigate_to_url(url: str, wait_until: str = "load") -> dict[str, Any]:
    """
    便捷函数：导航到URL

    Args:
        url: 目标URL
        wait_until: 等待条件

    Returns:
        导航结果
    """
    return await browser_automation_handler({
        "action": "navigate",
        "url": url,
        "wait_until": wait_until
    }, {})


async def take_screenshot(full_page: bool = False, save_path: Optional[str] = None) -> dict[str, Any]:
    """
    便捷函数：截图

    Args:
        full_page: 是否全页截图
        save_path: 保存路径

    Returns:
        截图结果
    """
    return await browser_automation_handler({
        "action": "screenshot",
        "full_page": full_page,
        "save_path": save_path
    }, {})


async def execute_browser_task(task: str) -> dict[str, Any]:
    """
    便捷函数：执行智能任务

    Args:
        task: 任务描述

    Returns:
        执行结果
    """
    return await browser_automation_handler({
        "action": "execute_task",
        "task": task
    }, {})


# =============================================================================
# 导出
# =============================================================================

__all__ = [
    "BrowserAutomationClient",
    "browser_automation_handler",
    "get_browser_client",
    "navigate_to_url",
    "take_screenshot",
    "execute_browser_task",
]
