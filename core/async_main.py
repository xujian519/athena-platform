#!/usr/bin/env python3
"""
异步入口统一模块
Async Main Entry Point Module

提供装饰器和工具函数,简化async main的编写

作者: Athena平台团队
版本: v1.0.0
"""

import asyncio
import functools
import logging
import signal
import sys
from collections.abc import Callable, Coroutine
from typing import Any, Optional

logger = logging.getLogger(__name__)


def async_main(
    coroutine_func: Callable | None = None,
    *,
    debug: bool = False,
    loop_factory: Callable | None = None,
):
    """
    异步main装饰器

    替代常见的:
        # 入口点: @async_main装饰器已添加到main函数

    Args:
        coroutine_func: 异步主函数
        debug: 是否启用debug模式
        loop_factory: 自定义事件循环工厂

    Examples:
        >>> @async_main
        ... async def main():
        ...     print("Hello!")
        >>>
        >>> # 或者带参数
        >>> @async_main(debug=True)
        ... async def main():
        ...     print("Debug mode!")
    """

    def decorator(func: Callable[..., Coroutine]) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                if loop_factory:
                    asyncio.run(func(*args, **kwargs), debug=debug, loop_factory=loop_factory)
                else:
                    asyncio.run(func(*args, **kwargs), debug=debug)
            except KeyboardInterrupt:
                logger.info("程序被用户中断")
                sys.exit(0)
            except Exception as e:
                logger.error(f"程序异常退出: {e}", exc_info=True)
                sys.exit(1)

        return wrapper

    if coroutine_func is None:
        # @async_main() 形式
        return decorator
    else:
        # @async_main 形式
        return decorator(coroutine_func)


def run_async(coroutine: Coroutine, *, debug: bool = False, handle_signals: bool = True) -> Any:
    """
    运行异步协程(函数式API)

    Args:
        coroutine: 要运行的协程
        debug: 是否启用debug模式
        handle_signals: 是否处理信号

    Examples:
        >>> async def main():
        ...     return "Hello"
        >>>
        >>> result = run_async(main())
    """
    try:
        return asyncio.run(coroutine, debug=debug)
    except KeyboardInterrupt:
        if handle_signals:
            logger.info("程序被用户中断")
            sys.exit(0)
        raise
    except Exception as e:
        logger.error(f"程序异常退出: {e}", exc_info=True)
        sys.exit(1)


class AsyncMainContext:
    """
    Async Main上下文管理器

    提供更精细的控制和清理
    """

    def __init__(self, debug: bool = False, shutdown_timeout: float = 5.0):
        self.debug = debug
        self.shutdown_timeout = shutdown_timeout
        self.loop = None
        self._tasks = set()

    async def __aenter__(self):
        self.loop = asyncio.get_running_loop()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # 取消所有未完成的任务
        if self._tasks:
            logger.info(f"取消 {len(self._tasks)} 个未完成任务")
            for task in self._tasks:
                task.cancel()

            # 等待任务取消
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self._tasks, return_exceptions=True),
                    timeout=self.shutdown_timeout,
                )
            except asyncio.TimeoutError:
                logger.warning("任务取消超时")

        return False

    def create_task(self, coro: Coroutine) -> asyncio.Task:
        """创建任务并跟踪"""
        task = self.loop.create_task(coro)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task


def setup_signal_handlers(loop: asyncio.AbstractEventLoop):
    """
    设置信号处理器

    Args:
        loop: 事件循环
    """

    def handle_signal():
        logger.info("收到终止信号,正在清理...")
        loop.stop()

    try:
        loop.add_signal_handler(signal.SIGTERM, handle_signal)
        loop.add_signal_handler(signal.SIGINT, handle_signal)
    except NotImplementedError:
        # Windows不支持add_signal_handler
        pass


# 便捷的main函数模板
async def async_main_template(main_func: Callable, args: list | None = None, kwargs: dict | None = None):
    """
    通用async main模板

    Args:
        main_func: 主函数
        args: 位置参数
        kwargs: 关键字参数

    Examples:
        >>> @async_main
        ... async def main():
        ...     await async_main_template(my_task, args=[1, 2])
    """
    args = args or []
    kwargs = kwargs or {}

    try:
        return await main_func(*args, **kwargs)
    finally:
        # 清理资源
        await cleanup_resources()


async def cleanup_resources():
    """清理资源(可被子类重写)"""
    # 等待所有任务完成(除了当前任务)
    current = asyncio.current_task()
    tasks = [t for t in asyncio.all_tasks() if t != current]

    if tasks:
        logger.debug(f"等待 {len(tasks)} 个任务完成")
        await asyncio.gather(*tasks, return_exceptions=True)


# 便捷的批处理运行器
async def run_batch(coroutines: list[Coroutine], max_concurrency: int = 10):
    """
    批量运行协程

    Args:
        coroutines: 协程列表
        max_concurrency: 最大并发数

    Examples:
        >>> tasks = [process_item(i) for i in range(100)]
        >>> results = await run_batch(tasks, max_concurrency=10)
    """
    semaphore = asyncio.Semaphore(max_concurrency)

    async def run_with_semaphore(coro):
        async with semaphore:
            return await coro

    results = await asyncio.gather(
        *[run_with_semaphore(c) for c in coroutines], return_exceptions=True
    )

    return results


# 模块导出
__all__ = [
    "AsyncMainContext",
    "async_main",
    "async_main_template",
    "cleanup_resources",
    "run_async",
    "run_batch",
    "setup_signal_handlers",
]
