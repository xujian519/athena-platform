#!/usr/bin/env python3
"""
GUI操作类型扩展
GUI Action Type Extensions

扩展支持的GUI操作类型:
1. 拖拽操作
2. 滚动操作
3. 悬停操作
4. 多选操作
5. 文件上传
6. 右键菜单

作者: 小诺·双鱼公主
创建时间: 2026-01-01
版本: 1.0.0
"""

from __future__ import annotations
import asyncio
import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any

import cv2
import httpx
import numpy as np

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """操作类型"""

    CLICK = "click"  # 点击
    TYPE = "type"  # 输入文字
    SCROLL = "scroll"  # 滚动
    HOVER = "hover"  # 悬停
    DRAG = "drag"  # 拖拽
    RIGHT_CLICK = "right_click"  # 右键点击
    DOUBLE_CLICK = "double_click"  # 双击
    SELECT = "select"  # 选择
    UPLOAD = "upload"  # 上传文件
    WAIT = "wait"  # 等待
    NAVIGATE = "navigate"  # 导航到URL


@dataclass
class ScrollAction:
    """滚动操作"""

    direction: str = "down"  # up, down, left, right
    amount: int = 500  # 滚动像素
    element: str | None = None  # 目标元素


@dataclass
class DragAction:
    """拖拽操作"""

    start_element: str  # 起始元素
    end_element: str  # 结束元素
    start_offset: tuple[int, int] = (0, 0)  # 起始偏移
    end_offset: tuple[int, int] = (0, 0)  # 结束偏移
    duration: int = 500  # 持续时间(毫秒)


@dataclass
class HoverAction:
    """悬停操作"""

    element: str  # 目标元素
    duration: int = 1000  # 悬停时长(毫秒)


@dataclass
class RightClickAction:
    """右键操作"""

    element: str  # 目标元素
    menu_item: str | None = None  # 点击的菜单项


@dataclass
class SelectAction:
    """选择操作"""

    element: str  # 目标元素
    options: list[str]  # 要选择的选项
    multiple: bool = False  # 是否多选


@dataclass
class UploadAction:
    """上传操作"""

    element: str  # 上传按钮元素
    file_paths: list[str]  # 文件路径列表


class ExtendedGUIExecutor:
    """
    扩展GUI执行器

    支持更多操作类型的GUI自动化
    """

    def __init__(self, service_url: str = "http://localhost:8012"):
        """
        初始化扩展执行器

        Args:
            service_url: browser-automation-service URL
        """
        self.service_url = service_url

        # 操作处理器
        self.action_handlers = {
            ActionType.CLICK: self._handle_click,
            ActionType.TYPE: self._handle_type,
            ActionType.SCROLL: self._handle_scroll,
            ActionType.HOVER: self._handle_hover,
            ActionType.DRAG: self._handle_drag,
            ActionType.RIGHT_CLICK: self._handle_right_click,
            ActionType.DOUBLE_CLICK: self._handle_double_click,
            ActionType.SELECT: self._handle_select,
            ActionType.UPLOAD: self._handle_upload,
            ActionType.WAIT: self._handle_wait,
            ActionType.NAVIGATE: self._handle_navigate,
        }

        logger.info(f"🎮 扩展GUI执行器初始化: {service_url}")

    async def execute_action(
        self, action_type: ActionType, action_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        执行GUI操作

        Args:
            action_type: 操作类型
            action_data: 操作数据

        Returns:
            result: 执行结果
        """
        handler = self.action_handlers.get(action_type)

        if handler is None:
            return {"success": False, "error": f"不支持的操作类型: {action_type}"}

        try:
            result = await handler(action_data)
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"❌ 操作执行失败: {e}")
            return {"success": False, "error": str(e)}

    async def _handle_click(self, data: dict[str, Any]) -> dict[str, Any]:
        """处理点击操作"""
        selector = data.get("selector")
        if not selector:
            raise ValueError("缺少selector参数")

        # 调用browser-automation-service
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.service_url}/api/action/click", json={"selector": selector}
            )
            return response.json()

    async def _handle_type(self, data: dict[str, Any]) -> dict[str, Any]:
        """处理输入操作"""
        selector = data.get("selector")
        text = data.get("text")

        if not selector or text is None:
            raise ValueError("缺少selector或text参数")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.service_url}/api/action/type", json={"selector": selector, "text": text}
            )
            return response.json()

    async def _handle_scroll(self, data: dict[str, Any]) -> dict[str, Any]:
        """处理滚动操作"""
        direction = data.get("direction", "down")
        amount = data.get("amount", 500)
        element = data.get("element")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.service_url}/api/action/scroll",
                json={"direction": direction, "amount": amount, "element": element},
            )
            return response.json()

    async def _handle_hover(self, data: dict[str, Any]) -> dict[str, Any]:
        """处理悬停操作"""
        element = data.get("element")
        duration = data.get("duration", 1000)

        if not element:
            raise ValueError("缺少element参数")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.service_url}/api/action/hover",
                json={"selector": element, "duration": duration},
            )
            return response.json()

    async def _handle_drag(self, data: dict[str, Any]) -> dict[str, Any]:
        """处理拖拽操作"""
        start_element = data.get("start_element")
        end_element = data.get("end_element")

        if not start_element or not end_element:
            raise ValueError("缺少start_element或end_element参数")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.service_url}/api/action/drag",
                json={
                    "start_selector": start_element,
                    "end_selector": end_element,
                    "start_offset": data.get("start_offset", [0, 0]),
                    "end_offset": data.get("end_offset", [0, 0]),
                    "duration": data.get("duration", 500),
                },
            )
            return response.json()

    async def _handle_right_click(self, data: dict[str, Any]) -> dict[str, Any]:
        """处理右键操作"""
        element = data.get("element")
        menu_item = data.get("menu_item")

        if not element:
            raise ValueError("缺少element参数")

        async with httpx.AsyncClient() as client:
            # 先右键点击
            await client.post(
                f"{self.service_url}/api/action/right_click", json={"selector": element}
            )

            # 如果有菜单项,点击菜单
            if menu_item:
                response = await client.post(
                    f"{self.service_url}/api/action/click", json={"selector": menu_item}
                )
                return response.json()

            return {"status": "success"}

    async def _handle_double_click(self, data: dict[str, Any]) -> dict[str, Any]:
        """处理双击操作"""
        element = data.get("element")

        if not element:
            raise ValueError("缺少element参数")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.service_url}/api/action/double_click", json={"selector": element}
            )
            return response.json()

    async def _handle_select(self, data: dict[str, Any]) -> dict[str, Any]:
        """处理选择操作"""
        element = data.get("element")
        options = data.get("options", [])

        if not element or not options:
            raise ValueError("缺少element或options参数")

        async with httpx.AsyncClient() as client:
            results = []
            for option in options:
                response = await client.post(
                    f"{self.service_url}/api/action/select",
                    json={"selector": element, "option": option},
                )
                results.append(response.json())

            return {"results": results}

    async def _handle_upload(self, data: dict[str, Any]) -> dict[str, Any]:
        """处理上传操作"""
        element = data.get("element")
        file_paths = data.get("file_paths", [])

        if not element or not file_paths:
            raise ValueError("缺少element或file_paths参数")

        # 验证文件存在
        for file_path in file_paths:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")

        async with httpx.AsyncClient() as client:
            # 使用multipart上传
            files = [("files", open(fp, "rb")) for fp in file_paths]

            data = {"selector": element}

            response = await client.post(
                f"{self.service_url}/api/action/upload", data=data, files=files
            )

            return response.json()

    async def _handle_wait(self, data: dict[str, Any]) -> dict[str, Any]:
        """处理等待操作"""
        duration = data.get("duration", 1000)
        data.get("condition")

        # 简单等待
        await asyncio.sleep(duration / 1000)

        # TODO: 实现条件等待
        return {"status": "waited", "duration": duration}

    async def _handle_navigate(self, data: dict[str, Any]) -> dict[str, Any]:
        """处理导航操作"""
        url = data.get("url")

        if not url:
            raise ValueError("缺少url参数")

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.service_url}/api/navigate", params={"url": url})
            return response.json()


class PerformanceOptimizer:
    """
    性能优化器

    优化GUI自动化性能
    """

    def __init__(self):
        # 截图缓存
        self.screenshot_cache: dict[str, np.ndarray] = {}

        # 批处理队列
        self.action_queue: list[dict[str, Any]] = []

        # 并发控制
        self.max_concurrent = 5
        self.semaphore = asyncio.Semaphore(self.max_concurrent)

        logger.info("⚡ 性能优化器初始化完成")

    async def batch_execute(
        self, actions: list[dict[str, Any]], executor: ExtendedGUIExecutor
    ) -> list[dict[str, Any]]:
        """
        批量执行操作

        Args:
            actions: 操作列表
            executor: 执行器

        Returns:
            results: 结果列表
        """
        results = []

        # 并发执行
        tasks = [self._execute_with_semaphore(action, executor) for action in actions]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        return results

    async def _execute_with_semaphore(
        self, action: dict[str, Any], executor: ExtendedGUIExecutor
    ) -> dict[str, Any]:
        """使用信号量控制并发"""
        async with self.semaphore:
            action_type = ActionType(action["type"])
            return await executor.execute_action(action_type, action)

    def optimize_screenshot(self, screenshot: np.ndarray, quality: str = "medium") -> np.ndarray:
        """
        优化截图

        Args:
            screenshot: 截图数组
            quality: 质量级别 (low, medium, high)

        Returns:
            optimized: 优化后的截图
        """
        if quality == "low":
            # 降低分辨率
            scale = 0.5
            dimensions = (int(screenshot.shape[1] * scale), int(screenshot.shape[0] * scale))
            optimized = cv2.resize(screenshot, dimensions)
        elif quality == "medium":
            # 轻微压缩
            optimized = cv2.resize(screenshot, None, fx=0.8, fy=0.8)
        else:
            # 保持原质量
            optimized = screenshot

        return optimized

    def clear_cache(self) -> None:
        """清空缓存"""
        self.screenshot_cache.clear()
        logger.info("🗑️ 缓存已清空")


# 导出
__all__ = [
    "ActionType",
    "DragAction",
    "ExtendedGUIExecutor",
    "HoverAction",
    "PerformanceOptimizer",
    "RightClickAction",
    "ScrollAction",
    "SelectAction",
    "UploadAction",
]
