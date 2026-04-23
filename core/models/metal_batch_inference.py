#!/usr/bin/env python3
"""
Metal批量推理优化器
Metal Batch Inference Optimizer for llama-cpp-python

优化多个并发请求的处理性能,充分利用Metal GPU加速
"""

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class BatchStrategy(Enum):
    """批处理策略"""

    # 动态批处理:等待一定时间或达到批次大小后处理
    DYNAMIC = "dynamic"
    # 静态批处理:固定批次大小,满批即处理
    STATIC = "static"
    # 流式批处理:单个请求流式处理
    STREAMING = "streaming"


@dataclass
class InferenceRequest:
    """推理请求数据结构"""

    request_id: str
    prompt: str
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    stop: list[str] = field(default_factory=list)
    echo: bool = False
    priority: int = 0  # 优先级,数字越大优先级越高
    metadata: dict[str, Any] = field(default_factory=dict)

    creation_time: float = field(default_factory=time.time)
    start_time: Optional[float] = None
    completion_time: Optional[float] = None

    @property
    def waiting_time(self) -> float:
        """等待时间"""
        if self.start_time is None:
            return time.time() - self.creation_time
        return self.start_time - self.creation_time

    @property
    def processing_time(self) -> float:
        """处理时间"""
        if self.completion_time is None or self.start_time is None:
            return 0.0
        return self.completion_time - self.start_time

    @property
    def total_time(self) -> float:
        """总时间"""
        if self.completion_time is None:
            return time.time() - self.creation_time
        return self.completion_time - self.creation_time


@dataclass
class InferenceResult:
    """推理结果数据结构"""

    request_id: str
    text: str
    tokens_generated: int
    input_tokens: int
    processing_time: float
    waiting_time: float
    total_time: float
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def tokens_per_second(self) -> float:
        """生成速度(tokens/秒)"""
        if self.processing_time > 0:
            return self.tokens_generated / self.processing_time
        return 0.0


class MetalBatchProcessor:
    """
    Metal批量推理处理器

    核心功能:
    1. 请求队列管理:按优先级排序的请求队列
    2. 动态批处理:智能合并多个请求
    3. 并发执行:使用线程池并行处理
    4. 性能监控:实时统计和性能指标
    """

    def __init__(
        self,
        model,
        strategy: BatchStrategy = BatchStrategy.DYNAMIC,
        max_batch_size: int = 8,
        max_wait_time: float = 0.1,  # 最大等待时间(秒)
        max_concurrent: int = 4,  # 最大并发数
        n_threads: int = 8,
    ):
        """
        初始化批量处理器

        Args:
            model: llama_cpp.Llama模型实例
            strategy: 批处理策略
            max_batch_size: 最大批次大小
            max_wait_time: 最大等待时间(动态批处理)
            max_concurrent: 最大并发数
            n_threads: CPU线程数
        """
        self.model = model
        self.strategy = strategy
        self.max_batch_size = max_batch_size
        self.max_wait_time = max_wait_time
        self.n_threads = n_threads

        # 请求队列
        self.request_queue: list[InferenceRequest] = []
        self.queue_lock = Lock()

        # 并发执行器
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent)

        # 性能统计
        self.stats = {
            "total_requests": 0,
            "total_tokens": 0,
            "total_processing_time": 0.0,
            "total_waiting_time": 0.0,
            "batch_count": 0,
            "average_batch_size": 0.0,
            "average_tokens_per_second": 0.0,
        }

        logger.info(
            f"MetalBatchProcessor初始化完成: strategy={strategy.value}, "
            f"max_batch={max_batch_size}, max_concurrent={max_concurrent}"
        )

    async def submit_request(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stop: Optional[list[str]] = None,
        priority: int = 0,
        request_id: Optional[str] = None,
    ) -> InferenceResult:
        """
        提交推理请求

        Args:
            prompt: 输入提示
            max_tokens: 最大生成token数
            temperature: 温度参数
            top_p: top_p采样参数
            stop: 停止词列表
            priority: 优先级
            request_id: 请求ID(可选,自动生成)

        Returns:
            InferenceResult: 推理结果
        """
        if request_id is None:
            request_id = f"req_{int(time.time() * 1000000)}"

        request = InferenceRequest(
            request_id=request_id,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop=stop or [],
            priority=priority,
        )

        # 根据策略处理请求
        if self.strategy == BatchStrategy.STREAMING:
            # 流式处理:立即执行
            result = await self._execute_single(request)
        elif self.strategy == BatchStrategy.STATIC:
            # 静态批处理:等待批次满
            result = await self._execute_static_batch(request)
        else:  # DYNAMIC
            # 动态批处理:等待或超时后执行
            result = await self._execute_dynamic_batch(request)

        # 更新统计信息
        self._update_stats(result)

        return result

    async def submit_batch(self, requests: list[InferenceRequest]) -> list[InferenceResult]:
        """
        批量提交请求

        Args:
            requests: 请求列表

        Returns:
            list[InferenceResult]: 结果列表
        """
        # 按优先级排序
        sorted_requests = sorted(requests, key=lambda r: r.priority, reverse=True)

        # 分批处理
        batches = [
            sorted_requests[i : i + self.max_batch_size]
            for i in range(0, len(sorted_requests), self.max_batch_size)
        ]

        # 并发执行批次
        tasks = [self._execute_batch(batch) for batch in batches]
        results = await asyncio.gather(*tasks)

        # 展平结果
        flat_results = []
        for batch_result in results:
            flat_results.extend(batch_result)

        return flat_results

    async def _execute_single(self, request: InferenceRequest) -> InferenceResult:
        """执行单个请求"""
        request.start_time = time.time()

        loop = asyncio.get_event_loop()
        output = await loop.run_in_executor(self.executor, self._sync_generate, request)

        request.completion_time = time.time()

        return InferenceResult(
            request_id=request.request_id,
            text=output["choices"][0]["text"],
            tokens_generated=output["usage"]["completion_tokens"],
            input_tokens=output["usage"]["prompt_tokens"],
            processing_time=request.processing_time,
            waiting_time=request.waiting_time,
            total_time=request.total_time,
            metadata=request.metadata,
        )

    async def _execute_static_batch(self, request: InferenceRequest) -> InferenceResult:
        """静态批处理:等待批次满后执行"""
        with self.queue_lock:
            self.request_queue.append(request)
            self.request_queue.sort(key=lambda r: r.priority, reverse=True)

        # 等待批次满
        while True:
            with self.queue_lock:
                queue_size = len(self.request_queue)

            if queue_size >= self.max_batch_size:
                break

            await asyncio.sleep(0.01)

        # 取出一批请求
        with self.queue_lock:
            batch = self.request_queue[: self.max_batch_size]
            self.request_queue = self.request_queue[self.max_batch_size :]

        # 执行批次
        results = await self._execute_batch(batch)

        # 返回当前请求的结果
        for result in results:
            if result.request_id == request.request_id:
                return result

        raise ValueError(f"未找到请求结果: {request.request_id}")

    async def _execute_dynamic_batch(self, request: InferenceRequest) -> InferenceResult:
        """动态批处理:等待超时或批次满后执行"""
        with self.queue_lock:
            self.request_queue.append(request)
            self.request_queue.sort(key=lambda r: r.priority, reverse=True)

        # 等待超时或批次满
        start_wait = time.time()
        while True:
            with self.queue_lock:
                queue_size = len(self.request_queue)
                elapsed = time.time() - start_wait

            if queue_size >= self.max_batch_size or elapsed >= self.max_wait_time:
                break

            await asyncio.sleep(0.005)

        # 取出一批请求
        with self.queue_lock:
            batch_size = min(len(self.request_queue), self.max_batch_size)
            batch = self.request_queue[:batch_size]
            self.request_queue = self.request_queue[batch_size:]

        # 执行批次
        results = await self._execute_batch(batch)

        # 返回当前请求的结果
        for result in results:
            if result.request_id == request.request_id:
                return result

        raise ValueError(f"未找到请求结果: {request.request_id}")

    async def _execute_batch(self, batch: list[InferenceRequest]) -> list[InferenceResult]:
        """执行一批请求(并发)"""
        tasks = [self._execute_single(req) for req in batch]
        results = await asyncio.gather(*tasks)
        return results

    def _sync_generate(self, request: InferenceRequest) -> dict[str, Any]:
        """同步生成(在线程池中执行)"""
        output = self.model(
            request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            stop=request.stop if request.stop else None,
            echo=request.echo,
        )
        return output

    def _update_stats(self, result: InferenceResult) -> Any:
        """更新性能统计"""
        self.stats["total_requests"] += 1
        self.stats["total_tokens"] += result.tokens_generated
        self.stats["total_processing_time"] += result.processing_time
        self.stats["total_waiting_time"] += result.waiting_time

        if self.stats["total_requests"] > 0:
            avg_time = (
                self.stats["total_processing_time"] + self.stats["total_waiting_time"]
            ) / self.stats["total_requests"]
            avg_tokens = self.stats["total_tokens"] / self.stats["total_requests"]
            self.stats["average_tokens_per_second"] = avg_tokens / avg_time if avg_time > 0 else 0

    def get_stats(self) -> dict[str, Any]:
        """获取性能统计"""
        return self.stats.copy()

    def reset_stats(self) -> Any:
        """重置统计信息"""
        self.stats = {
            "total_requests": 0,
            "total_tokens": 0,
            "total_processing_time": 0.0,
            "total_waiting_time": 0.0,
            "batch_count": 0,
            "average_batch_size": 0.0,
            "average_tokens_per_second": 0.0,
        }

    def shutdown(self) -> Any:
        """关闭处理器"""
        self.executor.shutdown(wait=True)
        logger.info("MetalBatchProcessor已关闭")


class MetalBatchInferenceManager:
    """
    Metal批量推理管理器

    提供高级API接口,简化批量推理的使用
    """

    def __init__(
        self,
        model,
        strategy: BatchStrategy = BatchStrategy.DYNAMIC,
        max_batch_size: int = 8,
        max_wait_time: float = 0.1,
        max_concurrent: int = 4,
    ):
        self.processor = MetalBatchProcessor(
            model=model,
            strategy=strategy,
            max_batch_size=max_batch_size,
            max_wait_time=max_wait_time,
            max_concurrent=max_concurrent,
        )

    async def generate(
        self, prompt: str, max_tokens: int = 512, temperature: float = 0.7, **kwargs
    ) -> str:
        """
        生成文本(简化API)

        Args:
            prompt: 输入提示
            max_tokens: 最大生成token数
            temperature: 温度参数
            **kwargs: 其他参数

        Returns:
            str: 生成的文本
        """
        result = await self.processor.submit_request(
            prompt=prompt, max_tokens=max_tokens, temperature=temperature, **kwargs
        )
        return result.text

    async def generate_batch(
        self, prompts: list[str], max_tokens: int = 512, temperature: float = 0.7, **kwargs
    ) -> list[str]:
        """
        批量生成文本

        Args:
            prompts: 输入提示列表
            max_tokens: 最大生成token数
            temperature: 温度参数
            **kwargs: 其他参数

        Returns:
            list[str]: 生成的文本列表
        """
        requests = [
            InferenceRequest(
                request_id=f"req_{i}",
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs,
            )
            for i, prompt in enumerate(prompts)
        ]

        results = await self.processor.submit_batch(requests)
        return [result.text for result in results]

    def get_performance_stats(self) -> dict[str, Any]:
        """获取性能统计"""
        return self.processor.get_stats()

    def shutdown(self) -> Any:
        """关闭管理器"""
        self.processor.shutdown()


# 便捷函数
async def create_batch_inference_manager(
    model,
    strategy: str = "dynamic",
    max_batch_size: int = 8,
    max_wait_time: float = 0.1,
    max_concurrent: int = 4,
) -> MetalBatchInferenceManager:
    """
    创建批量推理管理器

    Args:
        model: llama_cpp.Llama模型实例
        strategy: 批处理策略 ("dynamic", "static", "streaming")
        max_batch_size: 最大批次大小
        max_wait_time: 最大等待时间
        max_concurrent: 最大并发数

    Returns:
        MetalBatchInferenceManager: 批量推理管理器
    """
    strategy_enum = BatchStrategy(strategy)
    return MetalBatchInferenceManager(
        model=model,
        strategy=strategy_enum,
        max_batch_size=max_batch_size,
        max_wait_time=max_wait_time,
        max_concurrent=max_concurrent,
    )
