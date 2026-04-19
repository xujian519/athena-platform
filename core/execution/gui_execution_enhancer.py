#!/usr/bin/env python3
from __future__ import annotations
"""
GUI执行增强器
GUI Execution Enhancer

为browser-automation-service提供增强功能:
1. 自动截图管理
2. 视觉验证集成
3. 智能重试机制
4. 执行日志记录

作者: 小诺·双鱼公主
创建时间: 2026-01-01
版本: 1.0.0
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """执行状态"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    VERIFICATION_FAILED = "verification_failed"


@dataclass
class BrowserAction:
    """浏览器动作定义"""

    task: str  # 任务描述
    url: str | None = None  # 起始URL
    verification: dict = field(default_factory=dict)
    max_steps: int = 50  # 最大执行步数
    timeout: int = 30  # 超时时间(秒)
    capture_screenshots: bool = True  # 是否截图
    screenshot_each_step: bool = False  # 每步都截图


@dataclass
class GUIExecutionResult:
    """GUI执行结果"""

    status: ExecutionStatus
    task: str
    success: bool
    message: str

    # 截图
    before_screenshot: str | None = None
    after_screenshot: str | None = None
    step_screenshots: list[str] = field(default_factory=list)

    # 验证结果
    verified: bool = False
    verification_details: dict | None = None

    # 执行信息
    steps_taken: int = 0
    retry_count: int = 0
    execution_time: float = 0.0

    # 时间戳
    started_at: datetime | None = None
    completed_at: datetime | None = None

    # 错误信息
    error: str | None = None


class GUIExecutionEnhancer:
    """
    GUI执行增强器

    核心功能:
    1. 与browser-automation-service集成
    2. 自动截图管理
    3. 视觉验证触发
    4. 失败重试机制
    5. 执行日志记录
    """

    def __init__(self, config: dict | None = None):
        """
        初始化GUI执行增强器

        Args:
            config: 配置字典
                - browser_service_url: browser-automation-service URL
                - enable_verification: 是否启用视觉验证
                - default_max_retries: 默认最大重试次数
        """
        self.config = config or {}

        # browser-automation-service配置
        self.browser_service_url = self.config.get("browser_service_url", "http://localhost:8012")

        # 视觉验证引擎
        self.visual_engine = None
        self.enable_verification = self.config.get("enable_verification", True)

        # 重试配置
        self.default_max_retries = self.config.get("default_max_retries", 3)

        # 截图目录
        self.screenshot_dir = Path(
            self.config.get("screenshot_dir", "/Users/xujian/Athena工作平台/data/screenshots")
        )
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

        # HTTP客户端
        self.http_client = httpx.AsyncClient(timeout=300.0)

        logger.info("🚀 GUI执行增强器初始化完成")
        logger.info(f"   Browser Service: {self.browser_service_url}")
        logger.info(f"   视觉验证: {'启用' if self.enable_verification else '禁用'}")

    async def initialize(self):
        """初始化组件"""
        if self.enable_verification:
            try:
                from core.perception.visual_verification_engine import VisualVerificationEngine

                self.visual_engine = VisualVerificationEngine()
                await self.visual_engine.initialize()
                logger.info("✅ 视觉验证引擎已集成")
            except Exception as e:
                logger.warning(f"⚠️ 视觉验证引擎初始化失败: {e}")
                self.visual_engine = None

    async def execute_with_verification(self, action: BrowserAction) -> GUIExecutionResult:
        """
        带视觉验证的GUI执行

        Args:
            action: 浏览器动作

        Returns:
            GUIExecutionResult: 执行结果
        """
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        logger.info(f"🎯 开始执行任务: {action.task}")
        logger.info(f"   任务ID: {task_id}")

        # 初始化结果
        result = GUIExecutionResult(
            status=ExecutionStatus.PENDING,
            task=action.task,
            success=False,
            message="任务开始",
            started_at=datetime.now(),
        )

        try:
            # 1. 执行前截图(如果指定了URL)
            if action.url and action.capture_screenshots:
                result.before_screenshot = await self._capture_initial_page(action.url, task_id)

            # 2. 执行任务(带重试)
            await self._execute_with_retry(action, task_id, result)

            # 3. 执行后截图
            if action.capture_screenshots:
                result.after_screenshot = await self._capture_final_page(task_id)

            # 4. 视觉验证
            if self.visual_engine and action.verification:
                verification_result = await self._verify_execution(
                    action, result.before_screenshot, result.after_screenshot
                )
                result.verified = verification_result.status.value == "success"
                result.verification_details = verification_result.details

                if not result.verified:
                    result.status = ExecutionStatus.VERIFICATION_FAILED
                    result.message = f"验证失败: {verification_result.message}"
                    logger.warning(f"⚠️ {result.message}")
                else:
                    result.status = ExecutionStatus.SUCCESS
                    result.message = f"执行成功并验证通过: {verification_result.message}"
            else:
                result.status = ExecutionStatus.SUCCESS
                result.message = "执行成功(未验证)"

        except Exception as e:
            logger.error(f"❌ 执行失败: {e}")
            result.status = ExecutionStatus.FAILED
            result.error = str(e)
            result.message = f"执行异常: {e!s}"

        finally:
            result.completed_at = datetime.now()
            result.execution_time = (
                (result.completed_at - result.started_at).total_seconds()
                if result.started_at
                else 0.0
            )

        logger.info(f"✅ 任务完成: {result.status.value}")
        logger.info(f"   耗时: {result.execution_time:.2f}秒")
        logger.info(f"   重试: {result.retry_count}次")

        return result

    async def _execute_with_retry(
        self, action: BrowserAction, task_id: str, result: GUIExecutionResult
    ) -> dict[str, Any]:
        """
        带重试的执行

        Args:
            action: 浏览器动作
            task_id: 任务ID
            result: 结果对象(用于更新)

        Returns:
            Dict: 执行结果
        """
        max_retries = action.verification.get("max_retries", self.default_max_retries)
        retry_delay = 2  # 秒

        for attempt in range(max_retries + 1):
            if attempt > 0:
                result.retry_count = attempt
                result.status = ExecutionStatus.RETRYING
                logger.info(f"🔄 第 {attempt} 次重试...")

            try:
                # 调用browser-automation-service
                response = await self._call_browser_service(action)

                if response.get("success"):
                    result.steps_taken = response.get("steps", 0)
                    logger.info(f"✅ 执行成功,步数: {result.steps_taken}")
                    return response
                else:
                    error = response.get("error", "Unknown error")
                    logger.warning(f"⚠️ 执行失败: {error}")

                    if attempt < max_retries:
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # 指数退避
                    else:
                        result.error = error
                        raise Exception(f"执行失败,已达最大重试次数: {error}")

            except Exception as e:
                if attempt < max_retries:
                    logger.warning(f"⚠️ 执行异常: {e}")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise

    async def _call_browser_service(self, action: BrowserAction) -> dict[str, Any]:
        """
        调用browser-automation-service API

        Args:
            action: 浏览器动作

        Returns:
            Dict: API响应
        """
        url = f"{self.browser_service_url}/api/v1/task"

        payload = {"task": action.task, "max_steps": action.max_steps}

        if action.url:
            payload["url"] = action.url

        logger.info(f"📡 调用浏览器服务: {url}")

        try:
            response = await self.http_client.post(url, json=payload)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"❌ HTTP请求失败: {e}")
            return {"success": False, "error": str(e)}

    async def _verify_execution(
        self,
        action: BrowserAction,
        before_screenshot: str,
        after_screenshot: str,
    ):
        """
        验证执行结果

        Args:
            action: 浏览器动作
            before_screenshot: 执行前截图
            after_screenshot: 执行后截图

        Returns:
            VerificationResult
        """
        if not self.visual_engine or not after_screenshot:
            return None

        from core.perception.visual_verification_engine import GUIAction

        gui_action = GUIAction(action_type="browser_task", description=action.task)

        verification_rules = action.verification or {}

        return await self.visual_engine.verify_execution(
            action=gui_action,
            before_screenshot=before_screenshot or "",
            after_screenshot=after_screenshot,
            expected_elements=verification_rules.get("expected_elements"),
            expected_text=verification_rules.get("expected_text"),
            verify_change=True,
        )

    async def _capture_initial_page(self, url: str, task_id: str) -> str | None:
        """
        捕获初始页面截图

        Args:
            url: 页面URL
            task_id: 任务ID

        Returns:
            str: 截图路径
        """
        # 通过browser-automation-service获取截图
        # 这里简化处理
        logger.info(f"📸 捕获初始页面: {url}")
        return None  # 实际应该调用API获取截图

    async def _capture_final_page(self, task_id: str) -> str | None:
        """
        捕获最终页面截图

        Args:
            task_id: 任务ID

        Returns:
            str: 截图路径
        """
        # 通过browser-automation-service获取截图
        # 这里简化处理
        logger.info("📸 捕获最终页面")
        return None  # 实际应该调用API获取截图

    async def batch_execute(
        self, actions: list[BrowserAction], max_concurrent: int = 3
    ) -> list[GUIExecutionResult]:
        """
        批量执行任务

        Args:
            actions: 任务列表
            max_concurrent: 最大并发数

        Returns:
            list[GUIExecutionResult]: 结果列表
        """
        logger.info(f"🚀 批量执行 {len(actions)} 个任务,并发数: {max_concurrent}")

        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_one(action: BrowserAction) -> GUIExecutionResult:
            async with semaphore:
                return await self.execute_with_verification(action)

        tasks = [execute_one(action) for action in actions]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常结果
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(
                    GUIExecutionResult(
                        status=ExecutionStatus.FAILED,
                        task=actions[i].task,
                        success=False,
                        message=f"执行异常: {result!s}",
                        error=str(result),
                    )
                )
            else:
                final_results.append(result)

        # 统计
        success_count = sum(1 for r in final_results if r.success)
        logger.info(f"✅ 批量执行完成: {success_count}/{len(actions)} 成功")

        return final_results

    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            bool: 服务是否健康
        """
        try:
            url = f"{self.browser_service_url}/health"
            response = await self.http_client.get(url)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"⚠️ 健康检查失败: {e}")
            return False

    async def shutdown(self):
        """关闭资源"""
        await self.http_client.aclose()
        logger.info("🛑 GUI执行增强器已关闭")


# 导出
__all__ = ["BrowserAction", "ExecutionStatus", "GUIExecutionEnhancer", "GUIExecutionResult"]


# ==================== 使用示例 ====================

if __name__ == "__main__":

    async def main():
        """测试GUI执行增强器"""
        enhancer = GUIExecutionEnhancer()
        await enhancer.initialize()

        # 执行简单任务
        action = BrowserAction(
            task="打开百度首页,搜索'人工智能'",
            url="https://www.baidu.com",
            verification={"expected_text": "人工智能", "max_retries": 3},
        )

        result = await enhancer.execute_with_verification(action)

        print(f"状态: {result.status.value}")
        print(f"成功: {result.success}")
        print(f"消息: {result.message}")
        print(f"验证: {result.verified}")
        print(f"耗时: {result.execution_time:.2f}秒")

        await enhancer.shutdown()

    asyncio.run(main())
