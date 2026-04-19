#!/usr/bin/env python3
from __future__ import annotations
"""
异步NLP处理器
Asynchronous NLP Processor

使用asyncio实现高性能的异步NLP处理,替代线程池方案

性能优势:
- 更低的内存占用(协程 vs 线程)
- 更高的并发度(1000+ vs 线程池的4-32)
- 更高效的I/O处理

作者: Athena平台团队
创建时间: 2026-01-25
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Any

logger = logging.getLogger(__name__)


class AsyncNLPProcessor:
    """异步NLP处理器"""

    def __init__(
        self, max_concurrent_tasks: int = 100, cpu_workers: int = 4, queue_size: int = 1000
    ):
        """
        初始化异步NLP处理器

        Args:
            max_concurrent_tasks: 最大并发任务数
            cpu_workers: CPU密集型任务的线程池大小
            queue_size: 任务队列大小
        """
        self.max_concurrent_tasks = max_concurrent_tasks
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self.cpu_executor = ThreadPoolExecutor(max_workers=cpu_workers)
        self.task_queue: asyncio.Queue[Any] = asyncio.Queue(maxsize=queue_size)

        # 统计信息
        self.stats: dict[str, Any] = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "avg_latency_ms": 0.0,
        }

        logger.info(
            f"✅ 异步NLP处理器初始化完成"
            f" - 并发任务: {max_concurrent_tasks}, "
            f"CPU线程: {cpu_workers}"
        )

    async def process_single(
        self, text: str, processor: Callable[[str], Awaitable[dict[str, Any]]], **kwargs: Any
    ) -> dict[str, Any]:
        """
        异步处理单个文本

        Args:
            text: 输入文本
            processor: 异步处理函数
            **kwargs: 额外参数

        Returns:
            处理结果
        """
        async with self.semaphore:
            start_time = asyncio.get_event_loop().time()

            try:
                result = await processor(text, **kwargs)
                self.stats["completed_tasks"] += 1

                # 更新延迟统计
                latency_ms = (asyncio.get_event_loop().time() - start_time) * 1000
                self._update_latency_stats(latency_ms)

                return result

            except Exception as e:
                self.stats["failed_tasks"] += 1
                logger.error(f"❌ 处理失败: {e}")
                raise

    async def process_batch(
        self,
        texts: list[str],
        processor: Callable[[str], Awaitable[dict[str, Any]]],
        show_progress: bool = False,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """
        异步批量处理文本

        Args:
            texts: 文本列表
            processor: 异步处理函数
            show_progress: 是否显示进度
            **kwargs: 额外参数

        Returns:
            处理结果列表
        """
        self.stats["total_tasks"] = len(texts)

        # 创建所有任务
        tasks = [self.process_single(text, processor, **kwargs) for text in texts]

        # 使用asyncio.gather并发执行
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ 任务{i}失败: {result}")
                processed_results.append({"success": False, "error": str(result), "index": i})
            else:
                processed_results.append(result)

        if show_progress:
            logger.info(f"✅ 批量处理完成: {len(processed_results)}/{len(texts)}")

        return processed_results

    async def process_batch_with_rate_limit(
        self,
        texts: list[str],
        processor: Callable[[str], Awaitable[dict[str, Any]]],
        rate_limit: float = 100.0,  # 每秒请求数
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """
        带速率限制的批量处理

        Args:
            texts: 文本列表
            processor: 异步处理函数
            rate_limit: 每秒最大请求数
            **kwargs: 额外参数

        Returns:
            处理结果列表
        """
        self.stats["total_tasks"] = len(texts)
        results = []
        min_interval = 1.0 / rate_limit

        for i, text in enumerate(texts):
            # 控制速率
            if i > 0:
                await asyncio.sleep(min_interval)

            try:
                result = await self.process_single(text, processor, **kwargs)
                results.append(result)

                if (i + 1) % 100 == 0:
                    logger.info(f"进度: {i + 1}/{len(texts)}")

            except Exception as e:
                logger.error(f"❌ 处理失败({i}): {e}")
                results.append({"success": False, "error": str(e), "index": i})

        return results

    async def process_streaming(
        self,
        texts: list[str],
        processor: Callable[[str], Awaitable[dict[str, Any]]],
        batch_size: int = 32,
        **kwargs: Any,
    ) -> Any:
        """
        流式批量处理(生成器)

        Args:
            texts: 文本列表
            processor: 异步处理函数
            batch_size: 每批处理数量
            **kwargs: 额外参数

        Yields:
            处理结果
        """
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch_results = await self.process_batch(batch, processor, **kwargs)

            for result in batch_results:
                yield result

    def run_cpu_bound(self, func: Callable[..., Any], *args, **kwargs) -> Awaitable[Any]:
        """
        在线程池中运行CPU密集型任务

        Args:
            func: CPU密集型函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            异步结果
        """
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(self.cpu_executor, partial(func, *args, **kwargs))

    async def shutdown(self) -> None:
        """关闭处理器"""
        self.cpu_executor.shutdown(wait=True)
        logger.info("✅ 异步NLP处理器已关闭")

    def _update_latency_stats(self, latency_ms: float) -> None:
        """更新延迟统计"""
        n = self.stats["completed_tasks"]
        if n == 1:
            self.stats["avg_latency_ms"] = latency_ms
        else:
            # 指数移动平均
            alpha = 0.1
            self.stats["avg_latency_ms"] = (
                alpha * latency_ms + (1 - alpha) * self.stats["avg_latency_ms"]
            )

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "success_rate": (
                self.stats["completed_tasks"] / self.stats["total_tasks"] * 100
                if self.stats["total_tasks"] > 0
                else 0
            ),
            "concurrent_capacity": self.max_concurrent_tasks,
            "available_permits": self.semaphore._value,
        }


# 全局异步处理器实例
_async_processor: AsyncNLPProcessor | None = None


def get_async_processor() -> AsyncNLPProcessor:
    """获取全局异步NLP处理器"""
    global _async_processor
    if _async_processor is None:
        _async_processor = AsyncNLPProcessor()
    return _async_processor


# 便捷装饰器:将同步函数转换为异步
def asyncify(max_workers: int = 4) -> Callable[[Callable[..., Any]], Callable[..., Awaitable[Any]]]:
    """
    将同步函数转换为异步的装饰器

    Args:
        max_workers: 线程池大小
    """
    executor = ThreadPoolExecutor(max_workers=max_workers)

    def decorator(func: Callable[..., Any]) -> Callable[..., Awaitable[Any]]:
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(executor, partial(func, *args, **kwargs))

        return wrapper

    return decorator


if __name__ == "__main__":
    # 测试异步处理器
    async def mock_processor(text: str) -> dict[str, Any]:
        """模拟处理函数"""
        await asyncio.sleep(0.1)  # 模拟I/O延迟
        return {"text": text, "processed": True}

    async def main():
        processor = AsyncNLPProcessor(max_concurrent_tasks=10)

        # 测试单个处理
        result = await processor.process_single("测试文本", mock_processor)
        print(f"单个处理结果: {result}")

        # 测试批量处理
        texts = [f"文本{i}" for i in range(20)]
        results = await processor.process_batch(texts, mock_processor, show_progress=True)
        print(f"批量处理完成: {len(results)}个结果")

        # 显示统计
        stats = processor.get_stats()
        print("\n📊 统计信息:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

        await processor.shutdown()

    asyncio.run(main())
