#!/usr/bin/env python3
from __future__ import annotations
"""
MPS并行推理引擎 - 阶段3优化
实现GPU异步并行推理,大幅提升吞吐量

作者: 小诺·双鱼公主 🌊✨
创建时间: 2025-12-27
版本: v1.0.0
"""

import asyncio
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any

import numpy as np
import torch

from core.logging_config import setup_logging

logger = setup_logging()


@dataclass
class InferenceRequest:
    """推理请求"""

    request_id: str
    model_name: str
    inputs: Any
    priority: int = 0  # 优先级,数字越大优先级越高
    callback: Callable | None = None


@dataclass
class InferenceResult:
    """推理结果"""

    request_id: str
    model_name: str
    outputs: Any
    inference_time_ms: float
    success: bool
    error: Optional[str] = None


@dataclass
class ParallelInferenceConfig:
    """并行推理配置"""

    max_concurrent_requests: int = 500  # 最大并发请求数(从100提升)
    max_batch_size: int = 256  # 最大批处理大小
    request_timeout_seconds: float = 30.0
    enable_priority_queue: bool = True
    enable_result_cache: bool = True
    cache_size: int = 1000
    max_workers: int = 8  # 工作线程数


class MPSParallelInferenceEngine:
    """MPS并行推理引擎"""

    def __init__(self, config: ParallelInferenceConfig = None):
        self.config = config or ParallelInferenceConfig()
        self.device = self._select_device()

        # 模型注册表
        self.models: dict[str, torch.nn.Module] = {}
        self.model_locks: dict[str, threading.Lock] = {}

        # 请求队列
        self.request_queue: asyncio.Queue = asyncio.Queue()
        self.priority_queues: dict[int, asyncio.Queue] = {}

        # 结果缓存
        self.result_cache: dict[str, InferenceResult] = {}
        self.cache_lock = threading.Lock()

        # 统计信息
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_inference_time_ms": 0.0,
            "cache_hits": 0,
            "cache_misses": 0,
        }
        self.stats_lock = threading.Lock()

        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_workers)

        logger.info("🚀 MPS并行推理引擎初始化完成")
        logger.info(f"📊 最大并发: {self.config.max_concurrent_requests}")
        logger.info(f"📦 最大批次: {self.config.max_batch_size}")
        logger.info(f"🔧 工作线程: {self.config.max_workers}")

    def _select_device(self) -> torch.device:
        """选择最优设备"""
        if torch.backends.mps.is_available():
            logger.info("✅ 使用MPS GPU加速")
            return torch.device("mps")
        elif torch.cuda.is_available():
            logger.info("✅ 使用CUDA GPU加速")
            return torch.device("cuda")
        else:
            logger.info("⚠️ 使用CPU模式")
            return torch.device("cpu")

    def register_model(self, name: str, model: torch.nn.Module) -> Any:
        """注册模型到推理引擎"""
        self.models[name] = model.to(self.device)
        self.model_locks[name] = threading.Lock()

        # 优化模型
        model.eval()
        for param in model.parameters():
            param.requires_grad = False

        logger.info(f"📝 模型已注册: {name}")

    async def infer(self, request: InferenceRequest) -> InferenceResult:
        """
        异步推理接口

        Args:
            request: 推理请求

        Returns:
            推理结果
        """
        start_time = time.time()

        # 检查缓存
        if self.config.enable_result_cache:
            cached_result = self._get_cached_result(request)
            if cached_result is not None:
                with self.stats_lock:
                    self.stats["cache_hits"] += 1
                return cached_result
            else:
                with self.stats_lock:
                    self.stats["cache_misses"] += 1

        # 检查模型是否存在
        if request.model_name not in self.models:
            error_msg = f"模型未注册: {request.model_name}"
            logger.error(error_msg)
            return InferenceResult(
                request_id=request.request_id,
                model_name=request.model_name,
                outputs=None,
                inference_time_ms=0.0,
                success=False,
                error=error_msg,
            )

        # 执行推理
        try:
            # 使用线程池执行推理(避免GIL)
            loop = asyncio.get_event_loop()
            outputs = await loop.run_in_executor(
                self.executor, self._execute_inference, request.model_name, request.inputs
            )

            inference_time_ms = (time.time() - start_time) * 1000

            # 创建结果
            result = InferenceResult(
                request_id=request.request_id,
                model_name=request.model_name,
                outputs=outputs,
                inference_time_ms=inference_time_ms,
                success=True,
            )

            # 缓存结果
            if self.config.enable_result_cache:
                self._cache_result(request, result)

            # 更新统计
            with self.stats_lock:
                self.stats["total_requests"] += 1
                self.stats["successful_requests"] += 1
                self.stats["total_inference_time_ms"] += inference_time_ms

            # 回调
            if request.callback:
                await request.callback(result)

            return result

        except Exception as e:
            logger.error(f"推理失败: {e}")
            inference_time_ms = (time.time() - start_time) * 1000

            with self.stats_lock:
                self.stats["total_requests"] += 1
                self.stats["failed_requests"] += 1

            return InferenceResult(
                request_id=request.request_id,
                model_name=request.model_name,
                outputs=None,
                inference_time_ms=inference_time_ms,
                success=False,
                error=str(e),
            )

    def _execute_inference(self, model_name: str, inputs: Any) -> Any:
        """执行推理(线程池中运行)"""
        model = self.models[model_name]

        # 获取模型锁
        with self.model_locks[model_name]:
            # 准备输入
            prepared_inputs = self._prepare_inputs(inputs)

            # 根据输入类型调用模型
            try:
                if isinstance(prepared_inputs, dict):
                    # 字典类型,用**解包
                    outputs = model(**prepared_inputs)
                else:
                    # 张量或其他类型,直接传递
                    outputs = model(prepared_inputs)
            except TypeError as e:
                # 如果关键字参数调用失败,尝试位置参数
                if isinstance(prepared_inputs, dict) and "inputs" in prepared_inputs:
                    outputs = model(prepared_inputs["inputs"])
                else:
                    raise e

            # 同步GPU
            if self.device.type == "mps":
                torch.mps.synchronize()
            elif self.device.type == "cuda":
                torch.cuda.synchronize()

            return outputs

    def _prepare_inputs(self, inputs: Any) -> Any:
        """准备模型输入"""
        if isinstance(inputs, dict):
            prepared = {}
            for key, value in inputs.items():
                if isinstance(value, (list, np.ndarray)):
                    tensor = (
                        torch.tensor(value)
                        if isinstance(value, np.ndarray)
                        else torch.tensor(value)
                    )
                    prepared[key] = tensor.to(self.device, non_blocking=True)
                elif isinstance(value, torch.Tensor):
                    prepared[key] = value.to(self.device, non_blocking=True)
                else:
                    prepared[key] = value
            return prepared
        elif isinstance(inputs, torch.Tensor):
            return inputs.to(self.device, non_blocking=True)
        elif isinstance(inputs, (list, np.ndarray)):
            return torch.tensor(inputs).to(self.device, non_blocking=True)
        else:
            # 其他类型,直接传递给模型
            return inputs

    def _prepare_batch_inputs(self, inputs_list: list[Any]) -> dict[str, torch.Tensor]:
        """准备批处理输入"""
        if isinstance(inputs_list[0], dict):
            # 字典列表,按key批处理
            batched = {}
            for key in inputs_list[0]:
                values = [item[key] for item in inputs_list]
                tensors = []
                for value in values:
                    if isinstance(value, np.ndarray):
                        tensors.append(torch.tensor(value))
                    elif isinstance(value, torch.Tensor):
                        tensors.append(value)
                    else:
                        tensors.append(torch.tensor(value))
                batched[key] = torch.stack(tensors).to(self.device, non_blocking=True)
            return batched
        else:
            # 简单列表
            tensors = []
            for item in inputs_list:
                if isinstance(item, np.ndarray):
                    tensors.append(torch.tensor(item))
                elif isinstance(item, torch.Tensor):
                    tensors.append(item)
                else:
                    tensors.append(torch.tensor(item))
            return {"inputs": torch.stack(tensors).to(self.device, non_blocking=True)}

    async def batch_infer(self, requests: list[InferenceRequest]) -> list[InferenceResult]:
        """
        批量异步推理

        Args:
            requests: 推理请求列表

        Returns:
            推理结果列表
        """
        logger.info(f"🔄 批量推理: {len(requests)}个请求")

        # 按模型分组
        model_groups: dict[str, list[InferenceRequest]] = {}
        for request in requests:
            if request.model_name not in model_groups:
                model_groups[request.model_name] = []
            model_groups[request.model_name].append(request)

        # 并行处理每个模型组
        tasks = []
        for model_name, model_requests in model_groups.items():
            task = self._process_model_batch(model_name, model_requests)
            tasks.append(task)

        model_results = await asyncio.gather(*tasks, return_exceptions=True)

        # 合并结果
        all_results = []
        for results in model_results:
            if isinstance(results, Exception):
                logger.error(f"批处理错误: {results}")
                continue
            all_results.extend(results)

        # 按原始顺序排序
        result_map = {r.request_id: r for r in all_results}
        ordered_results = [result_map[r.request_id] for r in requests if r.request_id in result_map]

        return ordered_results

    async def _process_model_batch(
        self, model_name: str, requests: list[InferenceRequest]
    ) -> list[InferenceResult]:
        """处理单个模型的批次"""
        results = []

        # 分批处理
        batch_size = min(len(requests), self.config.max_batch_size)
        for i in range(0, len(requests), batch_size):
            batch = requests[i : i + batch_size]

            # 并行推理
            tasks = [self.infer(req) for req in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    logger.error(f"推理错误: {result}")
                    results.append(
                        InferenceResult(
                            request_id=batch[j].request_id,
                            model_name=model_name,
                            outputs=None,
                            inference_time_ms=0.0,
                            success=False,
                            error=str(result),
                        )
                    )
                else:
                    results.append(result)

        return results

    def _get_cached_result(self, request: InferenceRequest) -> InferenceResult | None:
        """获取缓存结果"""
        cache_key = self._generate_cache_key(request)
        with self.cache_lock:
            return self.result_cache.get(cache_key)

    def _cache_result(self, request: InferenceRequest, result: InferenceResult) -> Any:
        """缓存结果"""
        if len(self.result_cache) >= self.config.cache_size:
            # 简单的LRU:删除最旧的10%
            items_to_remove = len(self.result_cache) // 10
            keys_to_remove = list(self.result_cache.keys())[:items_to_remove]
            for key in keys_to_remove:
                del self.result_cache[key]

        cache_key = self._generate_cache_key(request)
        with self.cache_lock:
            self.result_cache[cache_key] = result

    def _generate_cache_key(self, request: InferenceRequest) -> str:
        """生成缓存键"""
        import hashlib
        import json

        # 序列化输入
        if isinstance(request.inputs, dict):
            inputs_str = json.dumps(request.inputs, sort_keys=True, default=str)
        elif isinstance(request.inputs, (list, tuple)):
            inputs_str = str(request.inputs)
        else:
            inputs_str = str(request.inputs)

        # 生成哈希(用于缓存key,非安全场景)
        hash_obj = hashlib.md5(f"{request.model_name}:{inputs_str}".encode(), usedforsecurity=False)
        return hash_obj.hexdigest()

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        with self.stats_lock:
            total_requests = self.stats["total_requests"]
            success_rate = (
                (self.stats["successful_requests"] / total_requests * 100)
                if total_requests > 0
                else 0
            )
            avg_inference_time = (
                (self.stats["total_inference_time_ms"] / self.stats["successful_requests"])
                if self.stats["successful_requests"] > 0
                else 0
            )

            return {
                "total_requests": total_requests,
                "successful_requests": self.stats["successful_requests"],
                "failed_requests": self.stats["failed_requests"],
                "success_rate": f"{success_rate:.2f}%",
                "avg_inference_time_ms": avg_inference_time,
                "cache_hits": self.stats["cache_hits"],
                "cache_misses": self.stats["cache_misses"],
                "cache_hit_rate": (
                    f"{(self.stats['cache_hits'] / (self.stats['cache_hits'] + self.stats['cache_misses']) * 100):.2f}%"
                    if (self.stats["cache_hits"] + self.stats["cache_misses"]) > 0
                    else "0%"
                ),
                "registered_models": list(self.models.keys()),
                "device": str(self.device),
            }

    def clear_cache(self) -> None:
        """清空结果缓存"""
        with self.cache_lock:
            self.result_cache.clear()
        logger.info("🗑️ 结果缓存已清空")

    async def shutdown(self):
        """关闭引擎"""
        logger.info("🛑 正在关闭MPS并行推理引擎...")

        # 关闭线程池
        self.executor.shutdown(wait=True)

        # 清空缓存
        self.clear_cache()

        # 卸载模型
        for name in self.models:
            del self.models[name]

        logger.info("✅ MPS并行推理引擎已关闭")


# 全局单例
_parallel_engine: MPSParallelInferenceEngine | None = None
_engine_lock = threading.Lock()


def get_parallel_inference_engine() -> MPSParallelInferenceEngine:
    """获取全局并行推理引擎实例"""
    global _parallel_engine
    if _parallel_engine is None:
        with _engine_lock:
            if _parallel_engine is None:
                _parallel_engine = MPSParallelInferenceEngine()
    return _parallel_engine


async def main():
    """测试并行推理引擎"""
    # setup_logging()  # 日志配置已移至模块导入

    engine = MPSParallelInferenceEngine()

    # 创建模拟模型
    class DummyModel(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.linear = torch.nn.Linear(768, 128)

        def forward(self, inputs) -> None:
            return self.linear(inputs)

    model = DummyModel()
    engine.register_model("dummy", model)

    # 测试单个推理
    print("\n📊 测试单个推理...")
    request = InferenceRequest(
        request_id="test_001", model_name="dummy", inputs=torch.randn(1, 768)
    )

    result = await engine.infer(request)
    print(f"结果: {result}")
    print(f"推理耗时: {result.inference_time_ms:.2f}ms")

    # 测试批量推理
    print("\n📊 测试批量推理...")
    requests = [
        InferenceRequest(
            request_id=f"batch_{i:03d}", model_name="dummy", inputs=torch.randn(1, 768)
        )
        for i in range(100)
    ]

    start_time = time.time()
    results = await engine.batch_infer(requests)
    total_time = (time.time() - start_time) * 1000

    print(f"总请求数: {len(results)}")
    print(f"总耗时: {total_time:.2f}ms")
    print(f"平均耗时: {total_time / len(results):.2f}ms")
    print(f"吞吐量: {len(results) / (total_time / 1000):.2f} 请求/秒")

    # 显示统计
    print("\n📊 引擎统计:")
    stats = engine.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    await engine.shutdown()


# 入口点: @async_main装饰器已添加到main函数
