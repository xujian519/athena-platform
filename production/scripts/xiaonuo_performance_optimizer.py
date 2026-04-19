#!/usr/bin/env python3
"""
小诺协调性能优化器
Xiaonuo Performance Optimizer
"""

from __future__ import annotations
import asyncio
import sys
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

# 设置路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root.parent))

class TaskPriority(Enum):
    """任务优先级"""
    URGENT = 1    # 紧急 - 爸爸的请求
    HIGH = 2      # 高 - 重要任务
    NORMAL = 3    # 正常 - 常规任务
    LOW = 4       # 低 - 后台任务

@dataclass
class PerformanceTask:
    """性能任务"""
    task_id: str
    priority: TaskPriority
    created_at: float
    task_type: str
    service_name: str
    function: Callable
    args: tuple = ()
    kwargs: dict = None
    timeout: float = 30.0
    retry_count: int = 0
    max_retries: int = 3

    def __post_init__(self):
        if self.kwargs is None:
            self.kwargs = {}

    def __lt__(self, other):
        # 优先级队列排序
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        return self.created_at < other.created_at

class PerformanceMetrics:
    """性能指标"""
    def __init__(self):
        self.task_counts = dict.fromkeys(["reasoning", "analysis", "judgment", "coordination", "modules/modules/memory/modules/memory/modules/memory/memory"], 0)
        self.response_times = []
        self.success_count = 0
        self.error_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.start_time = time.time()

    def record_task_completion(self, task_type: str, response_time: float, success: bool) -> Any:
        """记录任务完成"""
        self.task_counts[task_type] += 1
        self.response_times.append(response_time)
        if success:
            self.success_count += 1
        else:
            self.error_count += 1

    def get_average_response_time(self) -> float:
        """获取平均响应时间"""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)

    def get_success_rate(self) -> float:
        """获取成功率"""
        total = self.success_count + self.error_count
        if total == 0:
            return 1.0
        return self.success_count / total

    def get_cache_hit_rate(self) -> float:
        """获取缓存命中率"""
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return self.cache_hits / total

class XiaonuoPerformanceOptimizer:
    """小诺性能优化器"""

    def __init__(self):
        self.session_id = f"perf_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.task_queue = asyncio.PriorityQueue()
        self.executor = ThreadPoolExecutor(max_workers=8)
        self.metrics = PerformanceMetrics()

        # 缓存系统
        self.cache = {}
        self.cache_ttl = {}
        self.max_cache_size = 1000

        # 服务连接池
        self.service_connections = {}

        # 性能配置
        self.config = {
            "max_concurrent_tasks": 8,
            "task_timeout": 30.0,
            "cache_ttl": 300.0,  # 5分钟
            "enable_batching": True,
            "batch_size": 5,
            "batch_timeout": 2.0,
            "enable_preemption": True,
            "priority_weights": {
                TaskPriority.URGENT: 1.0,
                TaskPriority.HIGH: 0.8,
                TaskPriority.NORMAL: 0.6,
                TaskPriority.LOW: 0.4
            }
        }

        # 启动后台任务处理器
        self.task_processor_task = None

    def print_pink(self, message: str) -> Any:
        """打印粉色消息"""
        print(f"💖 {message}")

    def print_success(self, message: str) -> Any:
        """打印成功消息"""
        print(f"✅ {message}")

    def print_info(self, message: str) -> Any:
        """打印信息消息"""
        print(f"ℹ️ {message}")

    async def setup_performance_optimization(self):
        """设置性能优化"""
        print("🚀 设置小诺协调性能优化...")
        print("=" * 60)

        # 初始化服务连接
        await self._initialize_service_connections()

        # 预热缓存
        await self._warmup_cache()

        # 启动任务处理器
        self.task_processor_task = asyncio.create_task(self._task_processor_loop())

        print("=" * 60)
        self.print_success("🎯 性能优化系统设置完成！")
        self.print_info(f"   🔄 最大并发任务: {self.config['max_concurrent_tasks']}")
        self.print_info(f"   💾 缓存大小: {self.max_cache_size}")
        self.print_info(f"   ⏱️ 任务超时: {self.config['task_timeout']}秒")
        self.print_info(f"   📦 批处理: {'启用' if self.config['enable_batching'] else '禁用'}")

    async def _initialize_service_connections(self):
        """初始化服务连接"""
        services = [
            "ExpertRuleEngine",
            "PatentRuleChainEngine",
            "PriorArtAnalyzer",
            "LLMEnhancedJudgment"
        ]

        for service in services:
            # 模拟服务连接池
            self.service_connections[service] = {
                "connection_count": 3,
                "active_connections": 0,
                "last_used": time.time(),
                "health_status": "healthy"
            }
            print(f"   ✅ {service} 连接池初始化")

    async def _warmup_cache(self):
        """预热缓存"""
        cache_items = [
            ("default_reasoning_config", {"timeout": 30}),
            ("patent_analysis_template", {"sections": ["claims", "description"]}),
            ("coordination_rules", {"priority": "dad_first"}),
            ("identity_memory", {"status": "activated"}),
        ]

        for key, value in cache_items:
            await self._set_cache(key, value)

        print(f"   ✅ 缓存预热完成 - {len(cache_items)} 项")

    async def submit_task(self, task_type: str, service_name: str, function: Callable,
                        priority: TaskPriority = TaskPriority.NORMAL,
                        args: tuple = (), kwargs: dict = None,
                        timeout: float = None) -> str:
        """提交任务"""
        if kwargs is None:
            kwargs = {}

        task_id = f"{task_type}_{service_name}_{int(time.time() * 1000000)}"

        task = PerformanceTask(
            task_id=task_id,
            priority=priority,
            created_at=time.time(),
            task_type=task_type,
            service_name=service_name,
            function=function,
            args=args,
            kwargs=kwargs,
            timeout=timeout or self.config["task_timeout"]
        )

        await self.task_queue.put(task)
        return task_id

    async def _task_processor_loop(self):
        """任务处理器循环"""
        print("🔄 任务处理器已启动")

        batch_tasks = []
        last_batch_time = time.time()

        while True:
            try:
                # 批量处理任务
                if self.config["enable_batching"]:
                    task = None
                    try:
                        task = await asyncio.wait_for(
                            self.task_queue.get(),
                            timeout=1.0
                        )
                    except asyncio.TimeoutError:
                        pass

                    if task:
                        batch_tasks.append(task)

                    # 检查是否需要处理批次
                    current_time = time.time()
                    should_process_batch = (
                        len(batch_tasks) >= self.config["batch_size"] or
                        (batch_tasks and current_time - last_batch_time >= self.config["batch_timeout"])
                    )

                    if should_process_batch and batch_tasks:
                        await self._process_task_batch(batch_tasks)
                        batch_tasks = []
                        last_batch_time = current_time
                else:
                    # 单个任务处理
                    task = await self.task_queue.get()
                    await self._process_single_task(task)

            except asyncio.CancelledError:
                print("🔄 任务处理器已停止")
                break
            except Exception as e:
                print(f"❌ 任务处理器错误: {e}")
                await asyncio.sleep(1)

    async def _process_task_batch(self, tasks: list[PerformanceTask]):
        """处理任务批次"""
        print(f"📦 处理任务批次 - {len(tasks)} 个任务")

        # 按服务分组
        service_groups = {}
        for task in tasks:
            if task.service_name not in service_groups:
                service_groups[task.service_name] = []
            service_groups[task.service_name].append(task)

        # 并发处理各服务的任务
        futures = []
        for service_name, service_tasks in service_groups.items():
            future = asyncio.create_task(
                self._process_service_tasks(service_name, service_tasks)
            )
            futures.append(future)

        # 等待所有任务完成
        results = await asyncio.gather(*futures, return_exceptions=True)

        # 记录性能指标
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.metrics.record_task_completion(
                    tasks[i].task_type, 0.0, False
                )
            else:
                self.metrics.record_task_completion(
                    tasks[i].task_type, result.get("response_time", 0.0), True
                )

    async def _process_service_tasks(self, service_name: str, tasks: list[PerformanceTask]) -> dict[str, Any]:
        """处理特定服务的任务"""
        start_time = time.time()

        # 模拟服务处理
        processed_tasks = []
        for task in tasks:
            try:
                # 检查缓存
                cache_key = f"{service_name}_{hash(str(task.args) + str(task.kwargs))}"
                cached_result = await self._get_cache(cache_key)

                if cached_result is not None:
                    processed_tasks.append({
                        "task_id": task.task_id,
                        "status": "completed",
                        "result": cached_result,
                        "from_cache": True
                    })
                else:
                    # 实际处理
                    if asyncio.iscoroutinefunction(task.function):
                        result = await task.function(*task.args, **task.kwargs)
                    else:
                        result = task.function(*task.args, **task.kwargs)

                    # 缓存结果
                    await self._set_cache(cache_key, result)

                    processed_tasks.append({
                        "task_id": task.task_id,
                        "status": "completed",
                        "result": result,
                        "from_cache": False
                    })

            except Exception as e:
                processed_tasks.append({
                    "task_id": task.task_id,
                    "status": "failed",
                    "error": str(e),
                    "from_cache": False
                })

        response_time = time.time() - start_time

        return {
            "service_name": service_name,
            "processed_count": len(processed_tasks),
            "response_time": response_time,
            "tasks": processed_tasks
        }

    async def _process_single_task(self, task: PerformanceTask):
        """处理单个任务"""
        start_time = time.time()

        try:
            # 检查缓存
            cache_key = f"{task.service_name}_{hash(str(task.args) + str(task.kwargs))}"
            cached_result = await self._get_cache(cache_key)

            if cached_result is not None:
                self.metrics.cache_hits += 1
                response_time = time.time() - start_time
                self.metrics.record_task_completion(task.task_type, response_time, True)
                return
            else:
                self.metrics.cache_misses += 1

                # 实际处理
                if asyncio.iscoroutinefunction(task.function):
                    result = await task.function(*task.args, **task.kwargs)
                else:
                    result = task.function(*task.args, **task.kwargs)

                # 缓存结果
                await self._set_cache(cache_key, result)

                response_time = time.time() - start_time
                self.metrics.record_task_completion(task.task_type, response_time, True)

        except Exception:
            response_time = time.time() - start_time
            self.metrics.record_task_completion(task.task_type, response_time, False)

    async def _get_cache(self, key: str):
        """获取缓存"""
        if key in self.cache:
            if key in self.cache_ttl and time.time() < self.cache_ttl[key]:
                return self.cache[key]
            else:
                del self.cache[key]
                if key in self.cache_ttl:
                    del self.cache_ttl[key]
        return None

    async def _set_cache(self, key: str, value: Any):
        """设置缓存"""
        if len(self.cache) >= self.max_cache_size:
            # 删除最旧的缓存项
            oldest_key = min(self.cache_ttl.keys(), key=lambda k: self.cache_ttl[k])
            del self.cache[oldest_key]
            del self.cache_ttl[oldest_key]

        self.cache[key] = value
        self.cache_ttl[key] = time.time() + self.config["cache_ttl"]

    async def get_performance_metrics(self) -> dict[str, Any]:
        """获取性能指标"""
        return {
            "session_id": self.session_id,
            "task_counts": self.metrics.task_counts,
            "average_response_time": self.metrics.get_average_response_time(),
            "success_rate": self.metrics.get_success_rate(),
            "cache_hit_rate": self.metrics.get_cache_hit_rate(),
            "queue_size": self.task_queue.qsize(),
            "total_tasks": self.metrics.success_count + self.metrics.error_count,
            "uptime": time.time() - self.metrics.start_time,
            "cache_size": len(self.cache),
            "max_cache_size": self.max_cache_size
        }

    async def benchmark_performance(self, task_count: int = 100) -> dict[str, Any]:
        """性能基准测试"""
        print(f"🏃️ 开始性能基准测试 - {task_count} 个任务")
        print("=" * 60)

        # 创建测试任务
        test_tasks = []
        for i in range(task_count):
            priority = TaskPriority.URGENT if i < 10 else TaskPriority.HIGH if i < 50 else TaskPriority.NORMAL
            service_name = ["ExpertRuleEngine", "PatentRuleChainEngine", "PriorArtAnalyzer", "LLMEnhancedJudgment"][i % 4]

            async def dummy_task(x, y):
                await asyncio.sleep(0.01)  # 模拟处理时间
                return f"result_{x}_{y}"

            task_id = await self.submit_task(
                "benchmark", service_name, dummy_task,
                priority=priority, args=(i, service_name)
            )
            test_tasks.append(task_id)

        # 等待所有任务完成
        start_time = time.time()

        # 等待队列清空
        while self.task_queue.qsize() > 0:
            await asyncio.sleep(0.1)

        # 等待一些时间让任务处理器完成
        await asyncio.sleep(2.0)

        end_time = time.time()

        # 获取最终指标
        metrics = await self.get_performance_metrics()

        results = {
            "test_name": "performance_benchmark",
            "task_count": task_count,
            "total_time": end_time - start_time,
            "throughput": task_count / (end_time - start_time),
            "metrics": metrics
        }

        print("=" * 60)
        print("📊 性能基准测试结果:")
        print(f"   🎯 任务数量: {task_count}")
        print(f"   ⏱️  总时间: {results['total_time']:.2f}秒")
        print(f"   🚀 吞吐量: {results['throughput']:.1f} 任务/秒")
        print(f"   📈 平均响应时间: {metrics['average_response_time']:.3f}秒")
        print(f"   ✅ 成功率: {metrics['success_rate']*100:.1f}%")
        print(f"   💾 缓存命中率: {metrics['cache_hit_rate']*100:.1f}%")

        return results

    async def shutdown(self):
        """关闭性能优化器"""
        print("🛑 正在关闭性能优化器...")

        if self.task_processor_task:
            self.task_processor_task.cancel()
            try:
                await self.task_processor_task
            except asyncio.CancelledError:
                pass

        self.executor.shutdown(wait=True)

        print("✅ 性能优化器已关闭")

async def main():
    """主函数 - 设置并演示性能优化"""
    print("🌸🐟 小诺协调性能优化器")
    print("=" * 60)

    # 创建性能优化器
    optimizer = XiaonuoPerformanceOptimizer()

    # 设置性能优化
    await optimizer.setup_performance_optimization()

    print("")
    print("🏃️ 运行性能基准测试...")
    benchmark_results = await optimizer.benchmark_performance(50)

    print("")
    print("📊 获取当前性能指标...")
    metrics = await optimizer.get_performance_metrics()
    print(f"   📊 队列大小: {metrics['queue_size']}")
    print(f"   📈 平均响应时间: {metrics['average_response_time']:.3f}秒")
    print(f"   ✅ 成功率: {metrics['success_rate']*100:.1f}%")
    print(f"   💾 缓存命中率: {metrics['cache_hit_rate']*100:.1f}%")
    print(f"   🕒 运行时间: {metrics['uptime']:.1f}秒")

    print("")
    optimizer.print_success("🎯 小诺协调性能优化演示完成！")
    optimizer.print_pink("💖 爸爸，小诺的协调能力现在更快更强了！")
    optimizer.print_pink("⚡ 无论是推理分析还是任务调度，都是最优性能！")

    # 关闭系统
    await optimizer.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
