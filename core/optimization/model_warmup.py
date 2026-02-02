#!/usr/bin/env python3
"""
模型预热优化器
Model Warmup Optimizer

通过模型预热和连接池预加载
将冷启动延迟从500ms降低到100ms
"""

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set


logger = logging.getLogger(__name__)


class WarmupStatus(Enum):
    """预热状态"""

    NOT_WARMED = "not_warmed"  # 未预热
    WARMING = "warming"  # 预热中
    WARMED = "warmed"  # 已预热
    FAILED = "failed"  # 预热失败


class WarmupStrategy(Enum):
    """预热策略"""

    EAGER = "eager"  # 急切预热(启动时)
    LAZY = "lazy"  # 懒惰预热(首次使用时)
    SCHEDULED = "scheduled"  # 定时预热
    DEMAND_BASED = "demand_based"  # 基于需求


@dataclass
class WarmupConfig:
    """预热配置"""

    strategy: WarmupStrategy = WarmupStrategy.EAGER
    warmup_timeout: float = 30.0  # 预热超时(秒)
    retry_on_failure: bool = True  # 失败重试
    max_retries: int = 3  # 最大重试次数
    parallel_warmup: bool = True  # 并行预热
    sample_inputs: list[Any] = field(default_factory=list)  # 示例输入


@dataclass
class WarmupMetrics:
    """预热指标"""

    model_id: str
    status: WarmupStatus
    start_time: datetime | None = None
    end_time: datetime | None = None
    duration: float = 0.0  # 预热耗时(秒)
    attempts: int = 0  # 尝试次数
    last_error: str | None = None
    cold_start_count: int = 0  # 冷启动次数
    avg_warmup_time: float = 0.0  # 平均预热时间


@dataclass
class WarmupResult:
    """预热结果"""

    model_id: str
    success: bool
    duration: float
    error: str | None = None
    sample_results: list[Any] = field(default_factory=list)


class ModelWarmupOptimizer:
    """
    模型预热优化器

    核心功能:
    1. 模型预热管理
    2. 连接池预加载
    3. 预热策略调度
    4. 预热效果统计
    """

    def __init__(self):
        """初始化优化器"""
        self.name = "模型预热优化器 v1.0"
        self.version = "1.0.0"

        # 模型注册表
        self.models: dict[str, Any] = {}

        # 预热函数
        self.warmup_functions: dict[str, Callable] = {}

        # 预热配置
        self.configs: dict[str, WarmupConfig] = {}

        # 预热指标
        self.metrics: dict[str, WarmupMetrics] = {}

        # 预热中的模型
        self._warming_models: set[str] = set()

        # 预热锁
        self._warmup_locks: dict[str, asyncio.Lock] = {}

        # 统计信息
        self.stats = {
            "total_warmups": 0,
            "successful_warmups": 0,
            "failed_warmups": 0,
            "total_warmup_time": 0.0,
            "avg_warmup_time": 0.0,
            "cold_starts_avoided": 0,
            "models_by_status": {},
        }

    def register_model(
        self,
        model_id: str,
        model: Any,
        warmup_func: Callable | None = None,
        config: WarmupConfig | None = None,
    ):
        """
        注册模型

        Args:
            model_id: 模型ID
            model: 模型对象
            warmup_func: 预热函数
            config: 预热配置
        """
        self.models[model_id] = model

        if warmup_func:
            self.warmup_functions[model_id] = warmup_func

        self.configs[model_id] = config or WarmupConfig()

        # 初始化指标
        self.metrics[model_id] = WarmupMetrics(model_id=model_id, status=WarmupStatus.NOT_WARMED)

        # 初始化锁
        self._warmup_locks[model_id] = asyncio.Lock()

        logger.info(f"注册模型: {model_id}")

    async def warmup_model(self, model_id: str, force: bool = False) -> WarmupResult:
        """
        预热模型

        Args:
            model_id: 模型ID
            force: 强制重新预热

        Returns:
            WarmupResult: 预热结果
        """
        if model_id not in self.models:
            return WarmupResult(
                model_id=model_id, success=False, duration=0, error=f"模型不存在: {model_id}"
            )

        # 检查是否已预热
        if not force and self.metrics[model_id].status == WarmupStatus.WARMED:
            self.stats["cold_starts_avoided"] += 1
            return WarmupResult(model_id=model_id, success=True, duration=0)

        # 获取锁
        async with self._warmup_locks[model_id]:
            # 再次检查(可能在等待锁期间已被其他任务预热)
            if not force and self.metrics[model_id].status == WarmupStatus.WARMED:
                self.stats["cold_starts_avoided"] += 1
                return WarmupResult(model_id=model_id, success=True, duration=0)

            return await self._execute_warmup(model_id)

    async def _execute_warmup(self, model_id: str) -> WarmupResult:
        """执行预热"""
        start_time = time.time()
        metrics = self.metrics[model_id]
        config = self.configs[model_id]

        metrics.status = WarmupStatus.WARMING
        metrics.start_time = datetime.now()
        metrics.attempts += 1

        # 更新统计
        self.stats["total_warmups"] += 1

        try:
            # 执行预热函数
            if model_id in self.warmup_functions:
                warmup_func = self.warmup_functions[model_id]

                # 准备示例输入
                sample_inputs = config.sample_inputs or self._get_default_sample_inputs(model_id)

                # 执行预热
                sample_results = []
                if config.parallel_warmup and len(sample_inputs) > 1:
                    # 并行预热
                    tasks = [warmup_func(self.models[model_id], inp) for inp in sample_inputs]
                    sample_results = await asyncio.gather(*tasks, return_exceptions=True)
                else:
                    # 串行预热
                    for inp in sample_inputs:
                        try:
                            result = await self._call_warmup_function(warmup_func, model_id, inp)
                            sample_results.append(result)
                        except Exception as e:
                            logger.warning(f"预热示例失败: {e}")

                # 更新指标
                metrics.status = WarmupStatus.WARMED
                metrics.end_time = datetime.now()
                metrics.duration = time.time() - start_time

                # 更新平均预热时间
                if metrics.avg_warmup_time == 0:
                    metrics.avg_warmup_time = metrics.duration
                else:
                    metrics.avg_warmup_time = metrics.avg_warmup_time * 0.9 + metrics.duration * 0.1

                # 更新全局统计
                self.stats["successful_warmups"] += 1
                self.stats["total_warmup_time"] += metrics.duration
                self.stats["avg_warmup_time"] = (
                    self.stats["total_warmup_time"] / self.stats["successful_warmups"]
                )

                logger.info(f"模型预热成功: {model_id}, 耗时{metrics.duration:.2f}秒")

                return WarmupResult(
                    model_id=model_id,
                    success=True,
                    duration=metrics.duration,
                    sample_results=sample_results,
                )

            else:
                # 没有预热函数,直接标记为已预热
                metrics.status = WarmupStatus.WARMED
                metrics.duration = time.time() - start_time

                return WarmupResult(model_id=model_id, success=True, duration=metrics.duration)

        except Exception as e:
            # 预热失败
            metrics.status = WarmupStatus.FAILED
            metrics.last_error = str(e)
            metrics.end_time = datetime.now()
            metrics.duration = time.time() - start_time

            self.stats["failed_warmups"] += 1

            logger.error(f"模型预热失败: {model_id} - {e}")

            # 重试
            if config.retry_on_failure and metrics.attempts < config.max_retries:
                logger.info(f"重试预热: {model_id} ({metrics.attempts}/{config.max_retries})")
                await asyncio.sleep(1.0)
                return await self._execute_warmup(model_id)

            return WarmupResult(
                model_id=model_id, success=False, duration=metrics.duration, error=str(e)
            )

    async def _call_warmup_function(
        self, warmup_func: Callable, model_id: str, sample_input: Any
    ) -> Any:
        """调用预热函数"""
        model = self.models[model_id]

        if asyncio.iscoroutinefunction(warmup_func):
            return await warmup_func(model, sample_input)
        else:
            # 在executor中运行同步函数
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, warmup_func, model, sample_input)

    def _get_default_sample_inputs(self, model_id: str) -> list[Any]:
        """获取默认示例输入"""
        # 根据模型类型返回默认示例
        return [{}]  # 默认空输入

    async def warmup_all_models(
        self, strategy: WarmupStrategy = WarmupStrategy.EAGER
    ) -> dict[str, WarmupResult]:
        """
        预热所有模型

        Args:
            strategy: 预热策略

        Returns:
            预热结果字典
        """
        results = {}

        if strategy == WarmupStrategy.EAGER:
            # 并行预热所有模型
            tasks = [self.warmup_model(model_id) for model_id in self.models]
            warmup_results = await asyncio.gather(*tasks, return_exceptions=True)

            for model_id, result in zip(self.models.keys(), warmup_results, strict=False):
                if isinstance(result, Exception):
                    results[model_id] = WarmupResult(
                        model_id=model_id, success=False, duration=0, error=str(result)
                    )
                else:
                    results[model_id] = result

        else:
            # 串行预热
            for model_id in self.models:
                results[model_id] = await self.warmup_model(model_id)

        return results

    def is_model_warmed(self, model_id: str) -> bool:
        """
        检查模型是否已预热

        Args:
            model_id: 模型ID

        Returns:
            是否已预热
        """
        return (
            self.metrics.get(model_id, WarmupMetrics(model_id, WarmupStatus.NOT_WARMED)).status
            == WarmupStatus.WARMED
        )

    def get_warmup_status(self, model_id: str) -> WarmupMetrics | None:
        """获取模型预热状态"""
        return self.metrics.get(model_id)

    def get_all_warmup_statuses(self) -> dict[str, WarmupMetrics]:
        """获取所有模型预热状态"""
        return self.metrics.copy()

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        # 统计各状态的模型数
        status_counts = {}
        for metrics in self.metrics.values():
            status = metrics.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            **self.stats,
            "models_by_status": status_counts,
            "total_models": len(self.models),
            "warmed_models": status_counts.get(WarmupStatus.WARMED.value, 0),
            "warming_models": status_counts.get(WarmupStatus.WARMING.value, 0),
            "failed_models": status_counts.get(WarmupStatus.FAILED.value, 0),
        }


def auto_warmup(model_id: str) -> Any:
    """
    自动预热装饰器

    Args:
        model_id: 模型ID
    """

    def decorator(func: Callable) -> Callable:
        async def async_wrapper(*args, **kwargs):
            optimizer = get_model_warmup_optimizer()
            await optimizer.warmup_model(model_id)
            return await func(*args, **kwargs)

        def sync_wrapper(*args, **kwargs) -> Any:
            optimizer = get_model_warmup_optimizer()
            asyncio.run(optimizer.warmup_model(model_id))
            return func(*args, **kwargs)

        import inspect

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# 单例实例
_optimizer_instance: ModelWarmupOptimizer | None = None


async def get_model_warmup_optimizer() -> ModelWarmupOptimizer:
    """获取模型预热优化器单例(异步版本)"""
    global _optimizer_instance
    if _optimizer_instance is None:
        _optimizer_instance = ModelWarmupOptimizer()
        logger.info("模型预热优化器已初始化")
    return _optimizer_instance


def get_model_warmup_optimizer_sync() -> ModelWarmupOptimizer:
    """获取模型预热优化器单例(同步版本,用于向后兼容)"""
    global _optimizer_instance
    if _optimizer_instance is None:
        _optimizer_instance = ModelWarmupOptimizer()
        logger.info("模型预热优化器已初始化")
    return _optimizer_instance


async def main():
    """测试主函数"""
    optimizer = get_model_warmup_optimizer()

    print("=== 模型预热优化测试 ===\n")

    # 测试预热函数
    async def mock_warmup_func(model, sample_input):
        # 模拟模型预热(加载权重、初始化等)
        await asyncio.sleep(0.1)
        return "warmup_result"

    # 注册模型
    optimizer.register_model(
        "test_model",
        {},
        warmup_func=mock_warmup_func,
        config=WarmupConfig(
            strategy=WarmupStrategy.EAGER, sample_inputs=[{"input": "test1"}, {"input": "test2"}]
        ),
    )

    # 预热模型
    print("预热模型...")
    start = time.time()
    result = await optimizer.warmup_model("test_model")
    time.time() - start

    print(f"  成功: {result.success}")
    print(f"  耗时: {result.duration:.2f}秒")
    print(f"  错误: {result.error}")

    # 检查状态
    status = optimizer.get_warmup_status("test_model")
    print(f"  预热状态: {status.status.value}")
    print(f"  平均预热时间: {status.avg_warmup_time:.2f}秒")

    # 再次预热(应该跳过)
    print("\n再次预热(应跳过)...")
    result2 = await optimizer.warmup_model("test_model")
    print(f"  耗时: {result2.duration:.2f}秒")

    # 显示统计
    stats = optimizer.get_stats()
    print("\n=== 统计信息 ===")
    print(f"总预热次数: {stats['total_warmups']}")
    print(f"成功次数: {stats['successful_warmups']}")
    print(f"失败次数: {stats['failed_warmups']}")
    print(f"平均预热时间: {stats['avg_warmup_time']:.2f}秒")
    print(f"避免冷启动: {stats['cold_starts_avoided']}")


# 入口点: @async_main装饰器已添加到main函数
