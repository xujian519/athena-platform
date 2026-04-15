#!/usr/bin/env python3
"""
浏览器自动化集成测试
Browser Automation Integration Test

测试GUI自动化增强功能与执行引擎的集成

作者: 小诺·双鱼公主
创建时间: 2026-01-01
版本: 1.0.0
"""

from __future__ import annotations
import asyncio
import logging
import sys
from pathlib import Path
from typing import Any

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.execution.execution_engine import ActionType, ExecutionEngine, Task, TaskPriority

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("BrowserIntegrationTest")


class BrowserAutomationIntegrationTest:
    """浏览器自动化集成测试"""

    def __init__(self):
        self.engine = None
        self.test_results = []

    async def setup(self):
        """设置测试环境"""
        logger.info("🔧 设置测试环境...")

        # 创建执行引擎
        self.engine = ExecutionEngine(agent_id="browser_test", config={"max_concurrent": 5})

        await self.engine.initialize()
        logger.info("✅ 执行引擎已初始化")

    async def test_browser_action_type(self):
        """测试浏览器动作类型"""
        logger.info("\n" + "=" * 70)
        logger.info("🧪 测试1: 浏览器动作类型")
        logger.info("=" * 70)

        # 创建浏览器任务
        task = Task(
            id="test_browser_001",
            name="测试百度搜索",
            action_type=ActionType.BROWSER_ACTION,
            action_data={
                "task": '打开百度首页,搜索框输入"人工智能"',
                "url": "https://www.baidu.com",
                "verification": {"expected_text": "人工智能"},
                "max_steps": 10,
                "enable_screenshots": True,
            },
            priority=TaskPriority.NORMAL,
        )

        logger.info(f"📋 创建任务: {task.name}")
        logger.info(f"   动作类型: {task.action_type.value}")

        # 验证ActionType包含BROWSER_ACTION
        assert hasattr(ActionType, "BROWSER_ACTION"), "BROWSER_ACTION类型不存在"
        assert ActionType.BROWSER_ACTION.value == "browser_action"

        logger.info("✅ 浏览器动作类型验证通过")

        return {"test": "browser_action_type", "success": True}

    async def test_task_execution(self):
        """测试任务执行(需要browser-automation-service运行)"""
        logger.info("\n" + "=" * 70)
        logger.info("🧪 测试2: 任务执行")
        logger.info("=" * 70)

        logger.info("⚠️ 此测试需要browser-automation-service在端口8012运行")
        logger.info("   启动命令: cd services/browser-automation-service && python api_server.py")

        # 创建任务
        task = Task(
            id="test_browser_002",
            name="执行浏览器自动化任务",
            action_type=ActionType.BROWSER_ACTION,
            action_data={"task": "访问百度首页", "url": "https://www.baidu.com", "max_steps": 5},
            priority=TaskPriority.NORMAL,
        )

        try:
            # 执行任务
            task_id = await self.engine.execute_task(task)
            logger.info(f"✅ 任务已调度: {task_id}")

            # 等待一段时间让任务执行
            await asyncio.sleep(5)

            # 获取任务结果
            result = await self.engine.get_task_result(task_id)

            if result:
                logger.info(f"📊 任务状态: {result.status.value}")
                logger.info(
                    f"   执行时间: {result.duration:.2f}秒"
                    if result.duration
                    else "   执行时间: N/A"
                )

            return {"test": "task_execution", "success": True, "task_id": task_id}

        except Exception as e:
            logger.warning(f"⚠️ 任务执行测试跳过: {e}")
            logger.info("   这通常是因为browser-automation-service未运行")

            return {"test": "task_execution", "success": False, "skip": True, "reason": str(e)}

    async def test_workflow_integration(self):
        """测试工作流集成"""
        logger.info("\n" + "=" * 70)
        logger.info("🧪 测试3: 工作流集成")
        logger.info("=" * 70)

        # 创建包含浏览器动作的工作流
        workflow_id = await self.engine.create_workflow(
            name="浏览器自动化测试工作流",
            tasks_data=[
                {
                    "name": "步骤1: 打开百度",
                    "type": "browser_action",
                    "data": {
                        "task": "打开百度首页",
                        "url": "https://www.baidu.com",
                        "max_steps": 5,
                    },
                },
                {
                    "name": "步骤2: 搜索(模拟)",
                    "type": "function",
                    "data": {"function": "print_message", "args": ["搜索步骤(模拟)"]},
                },
            ],
            parallel=False,
        )

        logger.info(f"✅ 工作流已创建: {workflow_id}")

        # 获取工作流状态
        status = self.engine.workflow_engine.get_workflow_status(workflow_id)
        logger.info(f"📊 工作流状态: {status}")

        return {"test": "workflow_integration", "success": True, "workflow_id": workflow_id}

    async def test_action_executor_registry(self):
        """测试动作执行器注册"""
        logger.info("\n" + "=" * 70)
        logger.info("🧪 测试4: 动作执行器注册")
        logger.info("=" * 70)

        action_executor = self.engine.action_executor

        # 检查BROWSER_ACTION是否注册
        assert (
            ActionType.BROWSER_ACTION in action_executor.executors
        ), "BROWSER_ACTION未注册到执行器"

        # 检查执行器方法
        assert hasattr(
            action_executor, "_execute_browser_action"
        ), "_execute_browser_action方法不存在"

        # 验证执行器映射
        executor_method = action_executor.executors[ActionType.BROWSER_ACTION]
        assert executor_method == action_executor._execute_browser_action

        logger.info("✅ 动作执行器注册验证通过")
        logger.info(f"   已注册执行器: {len(action_executor.executors)} 个")
        logger.info(
            f"   执行器列表: {', '.join([t.value for t in action_executor.executors])}"
        )

        return {
            "test": "action_executor_registry",
            "success": True,
            "registered_executors": len(action_executor.executors),
        }

    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("\n" + "🌸" * 35)
        logger.info("   浏览器自动化集成测试")
        logger.info("   小诺·双鱼公主为您服务 💖")
        logger.info("🌸" * 35)

        try:
            # 设置
            await self.setup()

            # 测试列表
            tests = [
                ("浏览器动作类型", self.test_browser_action_type),
                ("任务执行", self.test_task_execution),
                ("工作流集成", self.test_workflow_integration),
                ("执行器注册", self.test_action_executor_registry),
            ]

            results = []

            # 执行测试
            for test_name, test_func in tests:
                try:
                    result = await test_func()
                    results.append(result)
                except Exception as e:
                    logger.error(f"❌ 测试失败: {test_name} - {e}")
                    results.append({"test": test_name, "success": False, "error": str(e)})

            # 汇总结果
            self.print_summary(results)

            # 清理
            await self.engine.shutdown()

        except Exception as e:
            logger.error(f"❌ 测试套件失败: {e}")
            raise

    def print_summary(self, results) -> None:
        """打印测试总结"""
        logger.info("\n" + "=" * 70)
        logger.info("📊 测试总结")
        logger.info("=" * 70)

        total = len(results)
        passed = sum(1 for r in results if r.get("success") and not r.get("skip"))
        skipped = sum(1 for r in results if r.get("skip"))
        failed = total - passed - skipped

        logger.info(f"总计: {total} 个测试")
        logger.info(f"通过: {passed} 个 ✅")
        logger.info(f"跳过: {skipped} 个 ⏭️")
        logger.info(f"失败: {failed} 个 ❌")

        if passed == total:
            logger.info("\n🎉 所有测试通过!")
        else:
            logger.info("\n⚠️ 部分测试未通过,请检查详情")

        # 详细结果
        for result in results:
            status = (
                "✅"
                if result.get("success") and not result.get("skip")
                else "⏭️" if result.get("skip") else "❌"
            )
            logger.info(f"   {status} {result.get('test', 'unknown')}")


# ==================== 辅助函数 ====================


def print_message(msg: str) -> Any:
    """用于测试的打印函数"""
    print(f"[TEST] {msg}")


async def main():
    """主函数"""
    tester = BrowserAutomationIntegrationTest()
    await tester.run_all_tests()


if __name__ == "__main__":
    # 将辅助函数添加到全局,供function调用测试使用
    globals()["print_message"] = print_message

    asyncio.run(main())
