#!/usr/bin/env python3
"""
GUI自动化扩展测试
GUI Automation Extensions Test Suite

测试ExtendedGUIExecutor和PerformanceOptimizer功能

作者: 小诺·双鱼公主
创建时间: 2026-01-01
版本: 1.0.0
"""

import asyncio
import logging

# 导入被测试模块
import sys
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.execution.gui_action_extensions import (
    ActionType,
    DragAction,
    ExtendedGUIExecutor,
    HoverAction,
    PerformanceOptimizer,
    RightClickAction,
    ScrollAction,
    SelectAction,
    UploadAction,
)

logging.basicConfig(
    level=logging.WARNING, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


class TestActionType:
    """测试ActionType枚举"""

    def test_all_action_types_defined(self) -> Any:
        """测试所有操作类型已定义"""
        expected_types = {
            "CLICK",
            "TYPE",
            "SCROLL",
            "HOVER",
            "DRAG",
            "RIGHT_CLICK",
            "DOUBLE_CLICK",
            "SELECT",
            "UPLOAD",
            "WAIT",
            "NAVIGATE",
        }

        actual_types = {action.name for action in ActionType}

        assert (
            expected_types == actual_types
        ), f"Missing types: {expected_types - actual_types}, Extra types: {actual_types - expected_types}"

    def test_action_type_creation(self) -> Any:
        """测试ActionType创建"""
        click_action = ActionType.CLICK
        assert click_action.value == "click"

        scroll_action = ActionType.SCROLL
        assert scroll_action.value == "scroll"


class TestDataClasses:
    """测试数据类"""

    def test_scroll_action(self) -> Any:
        """测试ScrollAction"""
        action = ScrollAction(direction="down", amount=500, element="#content")

        assert action.direction == "down"
        assert action.amount == 500
        assert action.element == "#content"

    def test_drag_action(self) -> Any:
        """测试DragAction"""
        action = DragAction(
            start_element="#source",
            end_element="#target",
            start_offset=(10, 10),
            end_offset=(20, 20),
            duration=800,
        )

        assert action.start_element == "#source"
        assert action.end_element == "#target"
        assert action.start_offset == (10, 10)
        assert action.end_offset == (20, 20)
        assert action.duration == 800

    def test_hover_action(self) -> Any:
        """测试HoverAction"""
        action = HoverAction(element="#button", duration=2000)

        assert action.element == "#button"
        assert action.duration == 2000

    def test_select_action(self) -> Any:
        """测试SelectAction"""
        action = SelectAction(element="#dropdown", options=["Option1", "Option2"], multiple=True)

        assert action.element == "#dropdown"
        assert action.options == ["Option1", "Option2"]
        assert action.multiple is True


@pytest.mark.asyncio
class TestExtendedGUIExecutor:
    """测试ExtendedGUIExecutor"""

    async def test_executor_initialization(self):
        """测试执行器初始化"""
        executor = ExtendedGUIExecutor(service_url="http://localhost:8012")

        assert executor.service_url == "http://localhost:8012"
        assert len(executor.action_handlers) == 11  # 11种操作类型

        # 验证所有处理器已注册
        expected_handlers = {
            ActionType.CLICK,
            ActionType.TYPE,
            ActionType.SCROLL,
            ActionType.HOVER,
            ActionType.DRAG,
            ActionType.RIGHT_CLICK,
            ActionType.DOUBLE_CLICK,
            ActionType.SELECT,
            ActionType.UPLOAD,
            ActionType.WAIT,
            ActionType.NAVIGATE,
        }

        actual_handlers = set(executor.action_handlers.keys())
        assert expected_handlers == actual_handlers

    @patch("httpx.AsyncClient")
    async def test_handle_click(self, mock_client_class):
        """测试点击操作"""
        # Mock HTTP响应
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "success", "clicked": True}

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client

        executor = ExtendedGUIExecutor()

        result = await executor.execute_action(ActionType.CLICK, {"selector": "#submit-button"})

        assert result["success"] is True
        assert result["result"]["status"] == "success"

    @patch("httpx.AsyncClient")
    async def test_handle_type(self, mock_client_class):
        """测试输入操作"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "success", "typed": "Hello"}

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client

        executor = ExtendedGUIExecutor()

        result = await executor.execute_action(
            ActionType.TYPE, {"selector": "#input-field", "text": "Hello"}
        )

        assert result["success"] is True

    @patch("httpx.AsyncClient")
    async def test_handle_scroll(self, mock_client_class):
        """测试滚动操作"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "scrolled", "amount": 500}

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client

        executor = ExtendedGUIExecutor()

        result = await executor.execute_action(
            ActionType.SCROLL, {"direction": "down", "amount": 500}
        )

        assert result["success"] is True

    @patch("httpx.AsyncClient")
    async def test_handle_drag(self, mock_client_class):
        """测试拖拽操作"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "dragged"}

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client

        executor = ExtendedGUIExecutor()

        result = await executor.execute_action(
            ActionType.DRAG,
            {
                "start_element": "#source",
                "end_element": "#target",
                "start_offset": [0, 0],
                "end_offset": [0, 0],
                "duration": 500,
            },
        )

        assert result["success"] is True

    @patch("httpx.AsyncClient")
    async def test_handle_right_click(self, mock_client_class):
        """测试右键点击操作"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "right_clicked"}

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client

        executor = ExtendedGUIExecutor()

        result = await executor.execute_action(
            ActionType.RIGHT_CLICK, {"element": "#context-menu-trigger", "menu_item": "#copy"}
        )

        assert result["success"] is True

    @patch("httpx.AsyncClient")
    async def test_handle_select(self, mock_client_class):
        """测试选择操作"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "selected"}

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client

        executor = ExtendedGUIExecutor()

        result = await executor.execute_action(
            ActionType.SELECT, {"element": "#dropdown", "options": ["Option1", "Option2"]}
        )

        assert result["success"] is True

    async def test_handle_wait(self):
        """测试等待操作"""
        executor = ExtendedGUIExecutor()

        import time

        start = time.time()
        result = await executor.execute_action(ActionType.WAIT, {"duration": 100})
        elapsed = time.time() - start

        assert result["success"] is True
        assert result["result"]["duration"] == 100
        assert elapsed >= 0.1  # 至少等待100ms

    async def test_unsupported_action_type(self):
        """测试不支持的操作类型"""
        executor = ExtendedGUIExecutor()

        # 使用无效的ActionType
        result = await executor.execute_action(
            ActionType.CLICK, {}  # 有效类型但无效数据  # 缺少必需参数
        )

        # 应该失败(缺少selector)
        assert result["success"] is False


@pytest.mark.asyncio
class TestPerformanceOptimizer:
    """测试PerformanceOptimizer"""

    def test_optimizer_initialization(self) -> Any:
        """测试优化器初始化"""
        optimizer = PerformanceOptimizer()

        assert optimizer.max_concurrent == 5
        assert len(optimizer.screenshot_cache) == 0
        assert len(optimizer.action_queue) == 0

    @pytest.mark.asyncio
    async def test_batch_execute(self):
        """测试批量执行"""
        optimizer = PerformanceOptimizer()

        # Mock执行器
        executor = MagicMock()
        executor.execute_action = AsyncMock(
            side_effect=[
                {"success": True, "result": {"action": 1}},
                {"success": True, "result": {"action": 2}},
                {"success": True, "result": {"action": 3}},
            ]
        )

        actions = [
            {"type": "click", "selector": "#btn1"},
            {"type": "click", "selector": "#btn2"},
            {"type": "click", "selector": "#btn3"},
        ]

        results = await optimizer.batch_execute(actions, executor)

        assert len(results) == 3
        assert all(r["success"] for r in results)

    def test_optimize_screenshot_low_quality(self) -> Any:
        """测试低质量截图优化"""
        optimizer = PerformanceOptimizer()

        # 创建测试图像 (1920x1080)
        screenshot = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)

        optimized = optimizer.optimize_screenshot(screenshot, quality="low")

        # 低质量应该缩小到50%
        assert optimized.shape[0] == 540  # 1080 * 0.5
        assert optimized.shape[1] == 960  # 1920 * 0.5

    def test_optimize_screenshot_medium_quality(self) -> Any:
        """测试中等质量截图优化"""
        optimizer = PerformanceOptimizer()

        screenshot = np.random.randint(0, 255, (1000, 1000, 3), dtype=np.uint8)

        optimized = optimizer.optimize_screenshot(screenshot, quality="medium")

        # 中等质量缩小到80%
        assert optimized.shape[0] == 800  # 1000 * 0.8
        assert optimized.shape[1] == 800  # 1000 * 0.8

    def test_optimize_screenshot_high_quality(self) -> Any:
        """测试高质量截图优化"""
        optimizer = PerformanceOptimizer()

        screenshot = np.random.randint(0, 255, (800, 600, 3), dtype=np.uint8)

        optimized = optimizer.optimize_screenshot(screenshot, quality="high")

        # 高质量保持原尺寸
        assert optimized.shape == screenshot.shape

    def test_clear_cache(self) -> Any:
        """测试清空缓存"""
        optimizer = PerformanceOptimizer()

        # 添加一些缓存数据
        optimizer.screenshot_cache["key1"] = np.array([1, 2, 3])
        optimizer.screenshot_cache["key2"] = np.array([4, 5, 6])

        assert len(optimizer.screenshot_cache) == 2

        optimizer.clear_cache()

        assert len(optimizer.screenshot_cache) == 0


@pytest.mark.asyncio
class TestIntegration:
    """集成测试"""

    @patch("httpx.AsyncClient")
    async def test_complex_workflow(self, mock_client_class):
        """测试复杂工作流"""
        # Mock HTTP响应
        mock_client = AsyncMock()
        mock_client.post.return_value = MagicMock(json=lambda: {"status": "success"})
        mock_client.get.return_value = MagicMock(json=lambda: {"status": "navigated"})
        mock_client_class.return_value.__aenter__.return_value = mock_client

        executor = ExtendedGUIExecutor()
        PerformanceOptimizer()

        # 复杂工作流:导航 → 点击 → 输入 → 滚动 → 点击
        actions = [
            {"type": "navigate", "url": "https://example.com"},
            {"type": "click", "selector": "#login"},
            {"type": "type", "selector": "#username", "text": "testuser"},
            {"type": "scroll", "direction": "down", "amount": 300},
            {"type": "click", "selector": "#submit"},
        ]

        # 转换为ActionType
        action_types = [
            ActionType.NAVIGATE,
            ActionType.CLICK,
            ActionType.TYPE,
            ActionType.SCROLL,
            ActionType.CLICK,
        ]

        # 执行所有操作
        results = []
        for action, action_type in zip(actions, action_types, strict=False):
            result = await executor.execute_action(action_type, action)
            results.append(result)

        # 验证所有操作成功
        success_count = sum(1 for r in results if r["success"])
        assert success_count == len(actions)


def print_header(title) -> None:
    """打印标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_test_result(name, passed, details="") -> None:
    """打印测试结果"""
    status = "✅ 通过" if passed else "❌ 失败"
    print(f"{status} - {name}")
    if details:
        print(f"     {details}")


async def run_all_tests():
    """运行所有测试"""
    print("\n")
    print("🎮 Athena GUI自动化扩展测试")
    print("   作者: 小诺·双鱼公主")
    print("   日期: 2026-01-01")
    print("\n   测试GUI自动化增强功能")

    all_passed = True

    # 测试1: ActionType枚举
    print_header("测试1: ActionType枚举定义")
    test = TestActionType()
    try:
        test.test_all_action_types_defined()
        test.test_action_type_creation()
        print_test_result("ActionType枚举", True, "11种操作类型全部定义")
    except AssertionError as e:
        print_test_result("ActionType枚举", False, str(e))
        all_passed = False

    # 测试2: 数据类
    print_header("测试2: 数据类定义")
    test = TestDataClasses()
    try:
        test.test_scroll_action()
        test.test_drag_action()
        test.test_hover_action()
        test.test_select_action()
        print_test_result("数据类", True, "所有数据类正常工作")
    except AssertionError as e:
        print_test_result("数据类", False, str(e))
        all_passed = False

    # 测试3: ExtendedGUIExecutor初始化
    print_header("测试3: 执行器初始化")
    test = TestExtendedGUIExecutor()
    try:
        await test.test_executor_initialization()
        print_test_result("执行器初始化", True, "11个处理器已注册")
    except AssertionError as e:
        print_test_result("执行器初始化", False, str(e))
        all_passed = False

    # 测试4: 基础操作处理
    print_header("测试4: 基础操作处理")
    test = TestExtendedGUIExecutor()
    try:
        await test.test_handle_click()
        await test.test_handle_type()
        await test.test_handle_scroll()
        await test.test_handle_drag()
        await test.test_handle_right_click()
        await test.test_handle_select()
        await test.test_handle_wait()
        print_test_result("基础操作处理", True, "所有基础操作正常")
    except Exception as e:
        print_test_result("基础操作处理", False, str(e))
        all_passed = False

    # 测试5: PerformanceOptimizer
    print_header("测试5: 性能优化器")
    test = TestPerformanceOptimizer()
    try:
        test.test_optimizer_initialization()
        await test.test_batch_execute()
        test.test_optimize_screenshot_low_quality()
        test.test_optimize_screenshot_medium_quality()
        test.test_optimize_screenshot_high_quality()
        test.test_clear_cache()
        print_test_result("性能优化器", True, "所有优化功能正常")
    except Exception as e:
        print_test_result("性能优化器", False, str(e))
        all_passed = False

    # 测试6: 集成测试
    print_header("测试6: 集成测试")
    test = TestIntegration()
    try:
        await test.test_complex_workflow()
        print_test_result("集成测试", True, "复杂工作流正常执行")
    except Exception as e:
        print_test_result("集成测试", False, str(e))
        all_passed = False

    # 汇总结果
    print_header("测试结果汇总")
    if all_passed:
        print("\n🎉 所有测试通过!")
        print("\n✅ GUI自动化增强功能全部正常")
        print("   - 11种操作类型支持")
        print("   - 性能优化器工作正常")
        print("   - 批量执行功能正常")
        print("   - 截图优化功能正常")
        return True
    else:
        print("\n⚠️ 部分测试失败")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)
