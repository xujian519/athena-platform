#!/usr/bin/env python3
from __future__ import annotations
"""
浏览器自动化适配器
Browser Automation Adapter

将browser-automation-service集成到Athena执行引擎中:
1. 统一ActionType接口
2. 任务路由和调度
3. 与GUI执行增强器集成

作者: 小诺·双鱼公主
创建时间: 2026-01-01
版本: 1.0.0
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class BrowserActionInput:
    """
    浏览器动作输入

    用于执行引擎的标准化接口
    """

    task: str  # 任务描述
    url: Optional[str] = None  # 起始URL
    verification: dict | None = None  # 验证规则
    max_steps: int = 50  # 最大执行步数
    enable_screenshots: bool = True  # 是否截图
    enable_verification: bool = True  # 是否验证

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "task": self.task,
            "url": self.url,
            "verification": self.verification or {},
            "max_steps": self.max_steps,
            "capture_screenshots": self.enable_screenshots,
            "screenshot_each_step": False,
        }


@dataclass
class ActionResult:
    """
    动作执行结果

    统一的执行结果格式
    """

    success: bool
    action_type: str
    result: Any = None
    error: Optional[str] = None
    metadata: dict | None = None  # 使用 Optional

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BrowserAutomationAdapter:
    """
    浏览器自动化适配器

    职责:
    1. 将browser-automation-service集成到执行引擎
    2. 提供标准化的ActionType处理接口
    3. 任务路由和调度
    """

    def __init__(self, config: dict | None = None):
        """
        初始化适配器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.enhancer = None
        self.BrowserAction = None  # 初始化 BrowserAction 字段

        logger.info("🔌 浏览器自动化适配器初始化")

    async def initialize(self):
        """初始化组件"""
        try:
            from core.execution.gui_execution_enhancer import BrowserAction, GUIExecutionEnhancer

            self.enhancer = GUIExecutionEnhancer(self.config)
            await self.enhancer.initialize()

            self.BrowserAction = BrowserAction

            logger.info("✅ 浏览器自动化适配器就绪")

        except Exception as e:
            logger.error(f"❌ 初始化失败: {e}")
            raise

    async def execute(self, action_input: BrowserActionInput) -> ActionResult:
        """
        执行浏览器自动化动作

        Args:
            action_input: 浏览器动作输入

        Returns:
            ActionResult: 执行结果
        """
        if not self.enhancer:
            return ActionResult(success=False, action_type="browser_action", error="增强器未初始化")

        try:
            # 检查 BrowserAction 是否已初始化
            if self.BrowserAction is None:
                return ActionResult(
                    success=False,
                    action_type="browser",
                    error="BrowserAction 未初始化",
                    metadata={},
                )

            # 转换为BrowserAction
            browser_action = self.BrowserAction(
                task=action_input.task,
                url=action_input.url,
                verification=action_input.verification,
                max_steps=action_input.max_steps,
                capture_screenshots=action_input.enable_screenshots,
            )

            # 执行
            result = await self.enhancer.execute_with_verification(browser_action)

            # 转换为ActionResult
            return ActionResult(
                success=result.success and result.verified,
                action_type="browser_action",
                result={
                    "status": result.status.value,
                    "message": result.message,
                    "steps_taken": result.steps_taken,
                    "retry_count": result.retry_count,
                    "execution_time": result.execution_time,
                    "verified": result.verified,
                    "before_screenshot": result.before_screenshot,
                    "after_screenshot": result.after_screenshot,
                },
                error=result.error,
                metadata={
                    "task_id": f"task_{result.started_at.strftime('%Y%m%d_%H%M%S') if result.started_at else 'unknown'}",
                    "verification_details": result.verification_details,
                    "started_at": result.started_at.isoformat() if result.started_at else None,
                    "completed_at": (
                        result.completed_at.isoformat() if result.completed_at else None
                    ),
                },
            )

        except Exception as e:
            logger.error(f"❌ 执行失败: {e}")
            return ActionResult(success=False, action_type="browser_action", error=str(e))

    async def batch_execute(
        self, actions: list[BrowserActionInput], max_concurrent: int = 3
    ) -> list[ActionResult]:
        """
        批量执行

        Args:
            actions: 动作列表
            max_concurrent: 最大并发数

        Returns:
            list[ActionResult]: 结果列表
        """
        if not self.enhancer:
            return [
                ActionResult(success=False, action_type="browser_action", error="增强器未初始化")
                for _ in actions
            ]

        try:
            # 检查 BrowserAction 是否已初始化
            if self.BrowserAction is None:
                return [
                    ActionResult(
                        success=False,
                        action_type="browser",
                        error="BrowserAction 未初始化",
                        metadata={},
                    )
                    for _ in actions
                ]

            # 转换为BrowserAction列表
            browser_actions = [
                self.BrowserAction(
                    task=action.task,
                    url=action.url,
                    verification=action.verification,
                    max_steps=action.max_steps,
                    capture_screenshots=action.enable_screenshots,
                )
                for action in actions
            ]

            # 批量执行
            results = await self.enhancer.batch_execute(browser_actions, max_concurrent)

            # 转换为ActionResult列表
            return [
                ActionResult(
                    success=result.success and result.verified,
                    action_type="browser_action",
                    result={
                        "status": result.status.value,
                        "message": result.message,
                        "steps_taken": result.steps_taken,
                        "retry_count": result.retry_count,
                        "execution_time": result.execution_time,
                        "verified": result.verified,
                    },
                    error=result.error,
                    metadata={
                        "task": result.task,
                        "verification_details": result.verification_details,
                    },
                )
                for result in results
            ]

        except Exception as e:
            logger.error(f"❌ 批量执行失败: {e}")
            return [
                ActionResult(success=False, action_type="browser_action", error=str(e))
                for _ in actions
            ]

    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            bool: 服务是否健康
        """
        if not self.enhancer:
            return False

        return await self.enhancer.health_check()

    async def shutdown(self):
        """关闭资源"""
        if self.enhancer:
            await self.enhancer.shutdown()
        logger.info("🛑 浏览器自动化适配器已关闭")


# ==================== 执行引擎集成 ====================


class BrowserActionExecutor:
    """
    浏览器动作执行器

    供ActionExecutor调用的标准接口
    """

    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self.adapter: BrowserAutomationAdapter | None = None

    async def initialize(self):
        """初始化"""
        self.adapter = BrowserAutomationAdapter(self.config)
        await self.adapter.initialize()
        logger.info("✅ 浏览器动作执行器就绪")

    async def execute(self, action_data: dict[str, Any]) -> ActionResult:
        """
        执行浏览器动作

        Args:
            action_data: 动作数据
                - task: str (必需)
                - url: str (可选)
                - verification: dict (可选)
                - max_steps: int (可选)
                - enable_screenshots: bool (可选)

        Returns:
            ActionResult
        """
        if not self.adapter:
            await self.initialize()

        # 再次检查 adapter 是否初始化成功
        if not self.adapter:
            return ActionResult(
                success=False, action_type="browser", error="浏览器适配器初始化失败", metadata={}
            )

        # 构造输入
        action_input = BrowserActionInput(
            task=action_data.get("task", ""),
            url=action_data.get("url"),
            verification=action_data.get("verification"),
            max_steps=action_data.get("max_steps", 50),
            enable_screenshots=action_data.get("enable_screenshots", True),
        )

        return await self.adapter.execute(action_input)

    async def shutdown(self):
        """关闭"""
        if self.adapter:
            await self.adapter.shutdown()


# 导出
__all__ = [
    "ActionResult",
    "BrowserActionExecutor",
    "BrowserActionInput",
    "BrowserAutomationAdapter",
]


# ==================== 使用示例 ====================

if __name__ == "__main__":

    async def main():
        """测试浏览器自动化适配器"""
        # 创建适配器
        adapter = BrowserAutomationAdapter()
        await adapter.initialize()

        # 健康检查
        healthy = await adapter.health_check()
        print(f"服务健康: {healthy}")

        # 执行任务
        action = BrowserActionInput(
            task="打开百度首页,搜索'人工智能'",
            url="https://www.baidu.com",
            verification={"expected_text": "人工智能"},
        )

        result = await adapter.execute(action)

        print(f"成功: {result.success}")
        print(f"状态: {result.result.get('status') if result.result else 'N/A'}")
        print(f"消息: {result.result.get('message') if result.result else 'N/A'}")

        await adapter.shutdown()

    asyncio.run(main())
