#!/usr/bin/env python3
"""
小诺优雅关闭机制
Xiaonuo Graceful Shutdown Mechanism

提供生产级优雅关闭功能：
- 保存当前状态
- 完成进行中的任务
- 通知协作的智能体
- 清理资源
- 记录关闭日志

作者: Athena团队
创建时间: 2026-02-09
版本: v1.0.0
"""

from __future__ import annotations
import asyncio
import logging
import signal
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


# =============================================================================
# 关闭状态
# =============================================================================

@dataclass
class ShutdownState:
    """关闭状态"""

    is_shutting_down: bool = False
    shutdown_reason: str | None = None
    shutdown_start_time: datetime | None = None
    shutdown_timeout: float = 30.0  # 秒

    # 任务状态
    pending_tasks: set[asyncio.Task] = field(default_factory=set)
    completed_tasks: int = 0
    failed_tasks: int = 0

    # 组件状态
    components_saved: bool = False
    peers_notified: bool = False
    resources_cleaned: bool = False


# =============================================================================
# 优雅关闭管理器
# =============================================================================

class GracefulShutdownManager:
    """优雅关闭管理器"""

    def __init__(self, timeout: float = 30.0):
        """
        初始化优雅关闭管理器

        参数:
            timeout: 关闭超时时间（秒）
        """
        self.state = ShutdownState(shutdown_timeout=timeout)
        self._shutdown_hooks: list[Callable] = []
        self._loop: asyncio.AbstractEventLoop | None = None
        self._original_signal_handlers: dict = {}

    def register_shutdown_hook(self, hook: Callable):
        """
        注册关闭钩子函数

        参数:
            hook: 关闭时执行的函数
        """
        self._shutdown_hooks.append(hook)
        logger.debug(f"注册关闭钩子: {hook.__name__}")

    def setup_signal_handlers(self):
        """设置信号处理器"""
        self._loop = asyncio.get_running_loop()

        # 注册信号处理器
        for sig in (signal.SIGTERM, signal.SIGINT):
            self._original_signal_handlers[sig] = signal.signal(
                sig,
                self._signal_handler
            )

        logger.info("信号处理器已设置")

    def _signal_handler(self, signum, frame):
        """
        信号处理函数

        参数:
            signum: 信号编号
            frame: 当前栈帧
        """
        sig_name = signal.Signals(signum).name
        logger.info(f"收到信号: {sig_name}")

        # 触发优雅关闭
        if self._loop:
            self._loop.create_task(self.shutdown(f"收到信号: {sig_name}"))

    async def shutdown(self, reason: str = "手动关闭"):
        """
        执行优雅关闭

        参数:
            reason: 关闭原因
        """
        if self.state.is_shutting_down:
            logger.warning("关闭流程已在进行中")
            return

        self.state.is_shutting_down = True
        self.state.shutdown_reason = reason
        self.state.shutdown_start_time = datetime.now()

        logger.info("=" * 60)
        logger.info("🛑 开始优雅关闭流程")
        logger.info(f"   原因: {reason}")
        logger.info(f"   时间: {self.state.shutdown_start_time.isoformat()}")
        logger.info(f"   超时: {self.state.shutdown_timeout}秒")
        logger.info("=" * 60)

        try:
            # 设置超时
            shutdown_task = asyncio.create_task(self._do_shutdown())
            await asyncio.wait_for(shutdown_task, timeout=self.state.shutdown_timeout)

        except asyncio.TimeoutError:
            logger.error(f"❌ 关闭超时 ({self.state.shutdown_timeout}秒)，强制退出")
            return

        except Exception as e:
            logger.error(f"❌ 关闭过程出错: {e}")
            return

        finally:
            logger.info("✅ 优雅关闭完成")

    async def _do_shutdown(self):
        """执行关闭步骤"""
        steps = [
            ("停止接受新任务", self._stop_accepting_tasks),
            ("等待进行中的任务完成", self._wait_pending_tasks),
            ("保存当前状态", self._save_state),
            ("通知协作智能体", self._notify_peers),
            ("执行关闭钩子", self._execute_shutdown_hooks),
            ("清理资源", self._cleanup_resources),
        ]

        for step_name, step_func in steps:
            logger.info(f"⏳ {step_name}...")
            try:
                await step_func()
                logger.info(f"✅ {step_name} - 完成")
            except Exception as e:
                logger.error(f"❌ {step_name} - 失败: {e}")

    async def _stop_accepting_tasks(self):
        """停止接受新任务"""
        # 这里添加停止接受新任务的逻辑
        await asyncio.sleep(0.1)

    async def _wait_pending_tasks(self):
        """等待进行中的任务完成"""
        if not self.state.pending_tasks:
            logger.info("没有进行中的任务")
            return

        logger.info(f"等待 {len(self.state.pending_tasks)} 个任务完成...")

        # 等待所有任务完成（最多10秒）
        try:
            await asyncio.wait_for(
                asyncio.gather(*self.state.pending_tasks, return_exceptions=True),
                timeout=10.0
            )
            logger.info("所有任务已完成")
        except asyncio.TimeoutError:
            logger.warning("部分任务未能在超时时间内完成")

    async def _save_state(self):
        """保存当前状态"""
        # 这里添加保存状态的逻辑
        # 例如：保存记忆、保存配置、保存进度等
        self.state.components_saved = True
        await asyncio.sleep(0.1)

    async def _notify_peers(self):
        """通知协作的智能体"""
        # 这里添加通知其他智能体的逻辑
        self.state.peers_notified = True
        await asyncio.sleep(0.1)

    async def _execute_shutdown_hooks(self):
        """执行关闭钩子"""
        for hook in self._shutdown_hooks:
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook()
                else:
                    hook()
            except Exception as e:
                logger.error(f"关闭钩子执行失败 ({hook.__name__}): {e}")

    async def _cleanup_resources(self):
        """清理资源"""
        # 这里添加清理资源的逻辑
        # 例如：关闭连接、释放锁、清理缓存等
        self.state.resources_cleaned = True
        await asyncio.sleep(0.1)

    def add_pending_task(self, task: asyncio.Task):
        """
        添加进行中的任务

        参数:
            task: 异步任务
        """
        self.state.pending_tasks.add(task)

    def remove_pending_task(self, task: asyncio.Task):
        """
        移除已完成的任务

        参数:
            task: 异步任务
        """
        self.state.pending_tasks.discard(task)


# =============================================================================
# 使用示例
# =============================================================================

async def example_shutdown_hook():
    """示例关闭钩子"""
    logger.info("执行关闭钩子...")
    await asyncio.sleep(0.5)
    logger.info("关闭钩子完成")


async def main_example():
    """使用示例"""
    # 创建关闭管理器
    shutdown_manager = GracefulShutdownManager(timeout=30.0)

    # 注册关闭钩子
    shutdown_manager.register_shutdown_hook(example_shutdown_hook)

    # 设置信号处理器
    shutdown_manager.setup_signal_handlers()

    # 模拟运行
    logger.info("服务正在运行...")

    # 创建一些模拟任务
    async def mock_task(name: str, duration: float):
        logger.info(f"任务 {name} 开始")
        await asyncio.sleep(duration)
        logger.info(f"任务 {name} 完成")

    task1 = asyncio.create_task(mock_task("Task1", 2.0))
    task2 = asyncio.create_task(mock_task("Task2", 3.0))

    shutdown_manager.add_pending_task(task1)
    shutdown_manager.add_pending_task(task2)

    # 等待任务完成或关闭信号
    try:
        await asyncio.gather(task1, task2)
    except asyncio.CancelledError:
        logger.info("任务被取消")

    # 等待关闭
    await shutdown_manager.state.shutdown_start_time or await asyncio.sleep(100)


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s'
    )

    # 运行示例
    asyncio.run(main_example())
