"""
并发处理优化模块

目标: 将QPS从89.3提升到>100（+12%吞吐量）

优化策略:
1. 协程池优化 - 更高效的异步处理
2. 连接池优化 - 数据库/Redis连接复用
3. 批量处理 - 合并多个小请求
4. 负载均衡 - 智能任务分发

Author: Athena Team
Date: 2026-04-24
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from collections import deque
from datetime import datetime
import threading


@dataclass
class ConcurrencyConfig:
    """并发配置"""
    # 协程池配置
    max_workers: int = 100  # 最大工作协程数
    min_workers: int = 10   # 最小工作协程数
    idle_timeout: int = 60  # 空闲超时（秒）

    # 连接池配置
    db_pool_size: int = 20  # 数据库连接池大小
    redis_pool_size: int = 50  # Redis连接池大小
    max_connections: int = 100  # 总连接数限制

    # 批量处理配置
    batch_size: int = 20  # 批量大小
    batch_timeout: float = 0.1  # 批量超时（秒）

    # 负载均衡配置
    enable_load_balancing: bool = True
    strategy: str = "round_robin"  # round_robin/least_connections/weighted


class WorkerPool:
    """协程工作池"""

    def __init__(self, config: ConcurrencyConfig):
        self.config = config
        self._workers: List[asyncio.Task] = []
        self._task_queue: asyncio.Queue = asyncio.Queue()
        self._results: Dict[str, Any] = {}
        self._is_running = False

    async def start(self):
        """启动工作池"""
        if self._is_running:
            return

        self._is_running = True

        # 创建工作协程
        for i in range(self.config.max_workers):
            task = asyncio.create_task(self._worker(f"worker-{i}"))
            self._workers.append(task)

    async def stop(self):
        """停止工作池"""
        self._is_running = False

        # 取消所有工作协程
        for worker in self._workers:
            worker.cancel()

        # 等待所有协程结束
        await asyncio.gather(*self._workers, return_exceptions=True)

        self._workers.clear()

    async def _worker(self, name: str):
        """工作协程"""
        while self._is_running:
            try:
                # 获取任务（带超时）
                task_data = await asyncio.wait_for(
                    self._task_queue.get(),
                    timeout=self.config.idle_timeout
                )

                # 执行任务
                task_id, func, args, kwargs = task_data
                try:
                    result = await func(*args, **kwargs)
                    self._results[task_id] = {
                        "success": True,
                        "result": result,
                        "worker": name,
                    }
                except Exception as e:
                    self._results[task_id] = {
                        "success": False,
                        "error": str(e),
                        "worker": name,
                    }

            except asyncio.TimeoutError:
                # 空闲超时，退出
                break
            except Exception as e:
                # 其他错误，继续工作
                continue

    async def submit(
        self,
        func: Callable,
        *args,
        task_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """提交任务到工作池"""
        if task_id is None:
            task_id = f"task-{time.time()}"

        await self._task_queue.put((task_id, func, args, kwargs))
        return task_id

    async def get_result(self, task_id: str, timeout: float = 5.0) -> Any:
        """获取任务结果"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            if task_id in self._results:
                return self._results.pop(task_id)
            await asyncio.sleep(0.01)

        raise TimeoutError(f"Task {task_id} timeout")

    def get_stats(self) -> Dict[str, Any]:
        """获取工作池统计"""
        return {
            "workers": len(self._workers),
            "max_workers": self.config.max_workers,
            "queue_size": self._task_queue.qsize(),
            "pending_results": len(self._results),
            "is_running": self._is_running,
        }


class ConnectionPool:
    """连接池管理器"""

    def __init__(self, config: ConcurrencyConfig):
        self.config = config
        self._db_connections: deque = deque()
        self._redis_connections: deque = deque()
        self._db_lock = threading.Lock()
        self._redis_lock = threading.Lock()

    async def get_db_connection(self):
        """获取数据库连接"""
        async with self._db_lock:
            if self._db_connections:
                return self._db_connections.popleft()

            # 创建新连接（模拟）
            await asyncio.sleep(0.01)  # 模拟连接延迟
            return f"db_conn_{time.time()}"

    async def release_db_connection(self, conn):
        """释放数据库连接"""
        async with self._db_lock:
            if len(self._db_connections) < self.config.db_pool_size:
                self._db_connections.append(conn)

    async def get_redis_connection(self):
        """获取Redis连接"""
        async with self._redis_lock:
            if self._redis_connections:
                return self._redis_connections.popleft()

            # 创建新连接（模拟）
            await asyncio.sleep(0.005)  # 模拟连接延迟
            return f"redis_conn_{time.time()}"

    async def release_redis_connection(self, conn):
        """释放Redis连接"""
        async with self._redis_lock:
            if len(self._redis_connections) < self.config.redis_pool_size:
                self._redis_connections.append(conn)

    def get_stats(self) -> Dict[str, Any]:
        """获取连接池统计"""
        return {
            "db_connections": len(self._db_connections),
            "db_pool_size": self.config.db_pool_size,
            "redis_connections": len(self._redis_connections),
            "redis_pool_size": self.config.redis_pool_size,
        }


class BatchProcessor:
    """批量处理器"""

    def __init__(self, config: ConcurrencyConfig):
        self.config = config
        self._batch: List[Any] = []
        self._lock = asyncio.Lock()
        self._last_flush = time.time()

    async def add(self, item: Any, processor: Callable):
        """添加项目到批次"""
        async with self._lock:
            self._batch.append((item, processor))

            # 检查是否应该刷新
            if len(self._batch) >= self.config.batch_size:
                await self._flush()
            elif time.time() - self._last_flush > self.config.batch_timeout:
                await self._flush()

    async def _flush(self):
        """刷新批次"""
        if not self._batch:
            return

        batch = self._batch
        self._batch = []
        self._last_flush = time.time()

        # 并行处理批次中的所有项目
        tasks = [processor(item) for item, processor in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return results

    async def flush(self):
        """手动刷新批次"""
        async with self._lock:
            await self._flush()


class ConcurrencyOptimizer:
    """并发优化器"""

    def __init__(self, config: ConcurrencyConfig):
        self.config = config
        self.worker_pool = WorkerPool(config)
        self.connection_pool = ConnectionPool(config)
        self.batch_processor = BatchProcessor(config)

    async def start(self):
        """启动优化器"""
        await self.worker_pool.start()

    async def stop(self):
        """停止优化器"""
        await self.worker_pool.stop()
        await self.batch_processor.flush()

    async def process_concurrent(
        self,
        tasks: List[Callable],
        *args,
        parallel: bool = True,
        **kwargs
    ) -> List[Any]:
        """并发处理多个任务"""
        if parallel:
            # 并行执行
            results = await asyncio.gather(
                *[task(*args, **kwargs) for task in tasks],
                return_exceptions=True
            )
            return results
        else:
            # 串行执行
            results = []
            for task in tasks:
                result = await task(*args, **kwargs)
                results.append(result)
            return results

    async def process_batch(
        self,
        items: List[Any],
        processor: Callable
    ) -> List[Any]:
        """批量处理"""
        for item in items:
            await self.batch_processor.add(item, processor)

        await self.batch_processor.flush()

    def get_stats(self) -> Dict[str, Any]:
        """获取优化器统计"""
        return {
            "worker_pool": self.worker_pool.get_stats(),
            "connection_pool": self.connection_pool.get_stats(),
            "config": {
                "max_workers": self.config.max_workers,
                "batch_size": self.config.batch_size,
                "db_pool_size": self.config.db_pool_size,
            },
        }


# 使用示例
async def example_concurrent_processing():
    """并发处理示例"""

    config = ConcurrencyConfig(
        max_workers=100,
        batch_size=20,
        db_pool_size=20,
    )

    optimizer = ConcurrencyOptimizer(config)
    await optimizer.start()

    try:
        # 示例任务
        async def sample_task(task_id: int):
            await asyncio.sleep(0.01)  # 模拟10ms处理
            return f"result_{task_id}"

        # 并发处理100个任务
        tasks = [lambda i=i: sample_task(i) for i in range(100)]
        start = time.time()
        results = await optimizer.process_concurrent(tasks, parallel=True)
        duration = (time.time() - start) * 1000

        # 计算QPS
        qps = len(tasks) / (duration / 1000)

        return {
            "tasks_processed": len(tasks),
            "duration_ms": duration,
            "qps": qps,
            "target_qps": 100,
            "achieved": qps >= 100,
            "stats": optimizer.get_stats(),
        }

    finally:
        await optimizer.stop()


if __name__ == "__main__":
    # 测试并发优化
    async def test():
        print("测试并发处理优化...")
        result = await example_concurrent_processing()
        print(f"结果: {result}")

    asyncio.run(test())
