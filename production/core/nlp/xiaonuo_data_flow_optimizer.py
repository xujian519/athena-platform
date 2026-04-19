#!/usr/bin/env python3
"""
小诺数据流优化器
Xiaonuo Data Flow Optimizer

实现模块间数据流的高效传递和优化,包括:
1. 数据流管道设计
2. 智能缓存机制
3. 批处理优化
4. 异步处理支持
5. 内存管理优化

作者: 小诺AI团队
日期: 2025-12-18
"""

from __future__ import annotations
import asyncio
import gc
import json
import os
import queue
import threading
import time
from collections import deque
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

from core.logging_config import setup_logging

if TYPE_CHECKING:
    from collections.abc import Callable

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


@dataclass
class DataFlowConfig:
    """数据流配置"""

    # 缓存配置
    cache_size: int = 1000
    enable_smart_cache: bool = True

    # 批处理配置
    batch_size: int = 32
    batch_timeout: float = 0.1  # 100ms

    # 异步配置
    max_workers: int = 4
    enable_async: bool = True

    # 内存管理
    memory_limit_mb: int = 1024  # 1GB
    gc_threshold: float = 0.8

    # 性能监控
    enable_profiling: bool = True
    stats_window: int = 1000


@dataclass
class FlowMetrics:
    """流处理指标"""

    total_requests: int = 0
    processed_requests: int = 0
    error_count: int = 0
    avg_latency: float = 0.0
    max_latency: float = 0.0
    min_latency: float = float("inf")
    cache_hits: int = 0
    cache_misses: int = 0
    memory_usage_mb: float = 0.0
    throughput: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class DataPacket:
    """数据包"""

    id: str
    data: Any
    metadata: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    ttl: float = 300.0  # 5分钟过期


class SmartCache:
    """智能缓存系统"""

    def __init__(self, max_size: int = 1000, ttl: float = 300.0):
        self.max_size = max_size
        self.ttl = ttl
        self.cache: dict[str, tuple[Any, datetime, int]] = (
            {}
        )  # key -> (value, timestamp, access_count)
        self.access_order = deque()
        self.lock = threading.RLock()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Any | None:
        """获取缓存值"""
        with self.lock:
            if key not in self.cache:
                self.misses += 1
                return None

            value, timestamp, count = self.cache[key]

            # 检查过期
            if (datetime.now() - timestamp).total_seconds() > self.ttl:
                del self.cache[key]
                self.access_order.remove(key)
                self.misses += 1
                return None

            # 更新访问信息
            self.cache[key] = (value, timestamp, count + 1)
            self.access_order.remove(key)
            self.access_order.append(key)
            self.hits += 1

            return value

    def put(self, key: str, value: Any) -> None:
        """存储缓存值"""
        with self.lock:
            current_time = datetime.now()

            # 如果键已存在,更新
            if key in self.cache:
                self.cache[key] = (value, current_time, self.cache[key][2] + 1)
                self.access_order.remove(key)
                self.access_order.append(key)
                return

            # 如果缓存已满,删除最少使用的项
            if len(self.cache) >= self.max_size:
                oldest_key = self.access_order.popleft()
                del self.cache[oldest_key]

            # 添加新项
            self.cache[key] = (value, current_time, 1)
            self.access_order.append(key)

    def get_stats(self) -> dict[str, Any]:
        """获取缓存统计"""
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = self.hits / total_requests if total_requests > 0 else 0

            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": hit_rate,
            }


class DataFlowOptimizer:
    """数据流优化器"""

    def __init__(self, config: DataFlowConfig = None):
        self.config = config or DataFlowConfig()

        # 核心组件
        self.cache = SmartCache(max_size=self.config.cache_size, ttl=600.0)  # 固定10分钟TTL

        # 批处理队列
        self.batch_queue = queue.Queue()
        self.batch_processor = None

        # 异步处理
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_workers)
        self.active_futures: dict[str, Future] = {}

        # 数据流管道
        self.pipelines: dict[str, list[Callable]] = {}
        self.flow_state: dict[str, Any] = {}

        # 性能监控
        self.metrics = FlowMetrics()
        self.metrics_history: deque = deque(maxlen=self.config.stats_window)
        self.lock = threading.RLock()

        # 内存管理
        self.memory_usage = 0.0
        self.gc_counter = 0

        logger.info("🚀 小诺数据流优化器初始化完成")
        logger.info(
            f"📊 缓存大小: {self.config.cache_size}, 智能缓存: {self.config.enable_smart_cache}"
        )
        logger.info(f"⚡ 最大工作线程: {self.config.max_workers}")
        logger.info(f"💾 内存限制: {self.config.memory_limit_mb}MB")

    def create_pipeline(self, name: str, processors: list[Callable]) -> None:
        """创建数据处理管道"""
        if name in self.pipelines:
            logger.warning(f"⚠️ 管道 {name} 已存在,将被覆盖")

        self.pipelines[name] = processors
        self.flow_state[name] = {"total_processed": 0, "total_time": 0.0, "errors": 0}

        logger.info(f"📋 创建数据流管道: {name}, 处理器数量: {len(processors)}")

    async def process_pipeline_async(self, name: str, data: Any) -> Any:
        """异步处理数据流管道"""
        if name not in self.pipelines:
            raise ValueError(f"管道 {name} 不存在")

        start_time = time.time()
        current_data = data

        try:
            for i, processor in enumerate(self.pipelines[name]):
                # 尝试从缓存获取
                cache_key = f"{name}_step_{i}_{hash(str(current_data))}"
                if self.config.enable_smart_cache:
                    cached_result = self.cache.get(cache_key)
                    if cached_result is not None:
                        current_data = cached_result
                        continue

                # 执行处理步骤
                if asyncio.iscoroutinefunction(processor):
                    current_data = await processor(current_data)
                else:
                    current_data = await asyncio.get_event_loop().run_in_executor(
                        self.executor, processor, current_data
                    )

                # 缓存结果
                if self.config.enable_smart_cache:
                    self.cache.put(cache_key, current_data)

            # 更新指标
            processing_time = time.time() - start_time
            self._update_metrics(processing_time, success=True)

            # 更新管道状态
            with self.lock:
                self.flow_state[name]["total_processed"] += 1
                self.flow_state[name]["total_time"] += processing_time

            return current_data

        except Exception as e:
            processing_time = time.time() - start_time
            self._update_metrics(processing_time, success=False)

            with self.lock:
                self.flow_state[name]["errors"] += 1

            logger.error(f"❌ 管道 {name} 处理失败: {e}")
            raise

    def process_pipeline_sync(self, name: str, data: Any) -> Any:
        """同步处理数据流管道"""
        if name not in self.pipelines:
            raise ValueError(f"管道 {name} 不存在")

        start_time = time.time()
        current_data = data

        try:
            for i, processor in enumerate(self.pipelines[name]):
                # 尝试从缓存获取
                cache_key = f"{name}_step_{i}_{hash(str(current_data))}"
                if self.config.enable_smart_cache:
                    cached_result = self.cache.get(cache_key)
                    if cached_result is not None:
                        current_data = cached_result
                        continue

                # 执行处理步骤
                current_data = processor(current_data)

                # 缓存结果
                if self.config.enable_smart_cache:
                    self.cache.put(cache_key, current_data)

            # 更新指标
            processing_time = time.time() - start_time
            self._update_metrics(processing_time, success=True)

            # 更新管道状态
            with self.lock:
                self.flow_state[name]["total_processed"] += 1
                self.flow_state[name]["total_time"] += processing_time

            return current_data

        except Exception as e:
            processing_time = time.time() - start_time
            self._update_metrics(processing_time, success=False)

            with self.lock:
                self.flow_state[name]["errors"] += 1

            logger.error(f"❌ 管道 {name} 处理失败: {e}")
            raise

    def batch_process(self, name: str, batch_data: list[Any]) -> list[Any]:
        """批量处理数据"""
        if not batch_data:
            return []

        # 如果批量大小大于配置,分批处理
        if len(batch_data) > self.config.batch_size:
            results = []
            for i in range(0, len(batch_data), self.config.batch_size):
                batch = batch_data[i : i + self.config.batch_size]
                batch_results = self._process_single_batch(name, batch)
                results.extend(batch_results)
            return results
        else:
            return self._process_single_batch(name, batch_data)

    def _process_single_batch(self, name: str, batch_data: list[Any]) -> list[Any]:
        """处理单个批次"""
        if not self.config.enable_async:
            # 同步批处理
            return [self.process_pipeline_sync(name, data) for data in batch_data]

        # 异步批处理
        async def async_batch_process():
            tasks = [self.process_pipeline_async(name, data) for data in batch_data]
            return await asyncio.gather(*tasks, return_exceptions=True)

        # 运行异步批处理
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(async_batch_process())
            return results
        finally:
            loop.close()

    def optimize_data_transfer(
        self, source_data: dict[str, Any], target_keys: list[str] | None = None
    ) -> dict[str, Any]:
        """优化数据传输,只传输必要的数据"""
        if target_keys is None:
            # 自动推断必要的键
            target_keys = list(source_data.keys())

        optimized_data = {}
        for key in target_keys:
            if key in source_data:
                value = source_data[key]

                # 数据压缩逻辑
                if isinstance(value, (list, tuple)) and len(value) > 100:
                    # 大列表进行压缩标记
                    optimized_data[key] = {
                        "_compressed": True,
                        "_length": len(value),
                        "_preview": (
                            value[:5] if hasattr(value, "__getitem__") else str(value)[:100]
                        ),
                    }
                else:
                    optimized_data[key] = value

        return optimized_data

    def smart_memory_cleanup(self) -> None:
        """智能内存清理"""
        self.gc_counter += 1

        # 检查内存使用情况
        current_memory = self._get_memory_usage()
        self.memory_usage = current_memory

        if current_memory > self.config.memory_limit_mb * self.config.gc_threshold:
            logger.info(f"🧹 内存使用过高 ({current_memory:.1f}MB),执行清理...")

            # 清理缓存
            cache_size_before = len(self.cache.cache)
            self.cache.cache.clear()
            self.cache.access_order.clear()

            # 强制垃圾回收
            collected = gc.collect()

            new_memory = self._get_memory_usage()
            memory_freed = current_memory - new_memory

            logger.info(
                f"✅ 内存清理完成: 缓存清理 {cache_size_before} 项, "
                f"垃圾回收 {collected} 对象, 释放内存 {memory_freed:.1f}MB"
            )

    def _update_metrics(self, latency: float, success: bool) -> None:
        """更新性能指标"""
        with self.lock:
            self.metrics.total_requests += 1

            if success:
                self.metrics.processed_requests += 1
                self.metrics.avg_latency = (
                    self.metrics.avg_latency * (self.metrics.processed_requests - 1) + latency
                ) / self.metrics.processed_requests
                self.metrics.max_latency = max(self.metrics.max_latency, latency)
                self.metrics.min_latency = min(self.metrics.min_latency, latency)
            else:
                self.metrics.error_count += 1

            # 更新缓存统计
            cache_stats = self.cache.get_stats()
            self.metrics.cache_hits = cache_stats["hits"]
            self.metrics.cache_misses = cache_stats["misses"]

            # 计算吞吐量
            if self.metrics.total_requests > 0:
                time_span = (datetime.now() - self.metrics.timestamp).total_seconds()
                if time_span > 0:
                    self.metrics.throughput = self.metrics.total_requests / time_span

            # 定期保存历史指标
            if self.metrics.total_requests % 100 == 0:
                self.metrics_history.append(asdict(self.metrics))
                self.metrics.timestamp = datetime.now()

    def _get_memory_usage(self) -> float:
        """获取当前内存使用量(MB)"""
        try:
            import psutil

            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            logger.warning("⚠️ psutil未安装,无法获取精确内存使用量")
            return 0.0

    def get_performance_report(self) -> dict[str, Any]:
        """获取性能报告"""
        with self.lock:
            cache_stats = self.cache.get_stats()

            # 计算各管道性能
            pipeline_stats = {}
            for name, state in self.flow_state.items():
                if state["total_processed"] > 0:
                    avg_time = state["total_time"] / state["total_processed"]
                    pipeline_stats[name] = {
                        "processed": state["total_processed"],
                        "avg_time": avg_time,
                        "total_time": state["total_time"],
                        "errors": state["errors"],
                        "error_rate": state["errors"] / state["total_processed"],
                    }

            return {
                "metrics": asdict(self.metrics),
                "cache": cache_stats,
                "pipelines": pipeline_stats,
                "memory_usage_mb": self.memory_usage,
                "gc_count": self.gc_counter,
                "config": asdict(self.config),
            }

    def save_performance_data(self, filepath: str) -> None:
        """保存性能数据到文件"""
        try:
            report = self.get_performance_report()

            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"💾 性能数据已保存: {filepath}")
        except Exception as e:
            logger.error(f"❌ 保存性能数据失败: {e}")

    def cleanup(self) -> None:
        """清理资源"""
        logger.info("🧹 正在清理数据流优化器资源...")

        # 关闭线程池
        self.executor.shutdown(wait=True)

        # 清理缓存
        self.cache.cache.clear()

        # 清理管道
        self.pipelines.clear()
        self.flow_state.clear()

        logger.info("✅ 数据流优化器资源清理完成")


# 预定义的数据流处理器
class CommonProcessors:
    """常用数据流处理器"""

    @staticmethod
    def data_validator(data: Any) -> Any:
        """数据验证处理器"""
        if data is None:
            raise ValueError("数据不能为空")
        return data

    @staticmethod
    def data_normalizer(data: dict[str, Any]) -> dict[str, Any]:
        """数据标准化处理器"""
        if isinstance(data, dict):
            # 移除None值
            return {k: v for k, v in data.items() if v is not None}
        return data

    @staticmethod
    def json_serializer(data: Any) -> str:
        """JSON序列化处理器"""
        return json.dumps(data, ensure_ascii=False, default=str)

    @staticmethod
    def json_deserializer(data: str) -> Any:
        """JSON反序列化处理器"""
        return json.loads(data)

    @staticmethod
    def batch_aggregator(batch_data: list[Any]) -> dict[str, Any]:
        """批量数据聚合处理器"""
        if not isinstance(batch_data, list):
            return {"items": [batch_data], "count": 1}

        return {
            "items": batch_data,
            "count": len(batch_data),
            "batch_id": f"batch_{int(time.time() * 1000)}",
        }


def create_xiaonuo_data_flow() -> DataFlowOptimizer:
    """创建小诺数据流优化器实例"""

    # 创建配置
    config = DataFlowConfig(
        cache_size=2000,  # 更大的缓存
        batch_size=64,  # 更大的批处理
        max_workers=8,  # 更多工作线程
        memory_limit_mb=2048,  # 2GB内存限制
        gc_threshold=0.8,
        enable_async=True,
        enable_smart_cache=True,
    )

    # 创建优化器
    optimizer = DataFlowOptimizer(config)

    # 创建标准处理管道
    optimizer.create_pipeline(
        "nlp_processing",
        [
            CommonProcessors.data_validator,
            CommonProcessors.data_normalizer,
        ],
    )

    optimizer.create_pipeline(
        "batch_processing",
        [
            CommonProcessors.batch_aggregator,
            CommonProcessors.json_serializer,
        ],
    )

    optimizer.create_pipeline(
        "response_serialization",
        [
            CommonProcessors.json_serializer,
        ],
    )

    return optimizer


# 测试代码
async def test_data_flow_optimizer():
    """测试数据流优化器"""
    print("🧪 开始测试数据流优化器...")

    # 创建优化器
    optimizer = create_xiaonuo_data_flow()

    # 创建测试管道
    def uppercase_processor(data: str) -> str:
        time.sleep(0.01)  # 模拟处理时间
        return data.upper()

    def add_timestamp_processor(data: str) -> dict[str, str]:
        return {"text": data, "timestamp": datetime.now().isoformat()}

    optimizer.create_pipeline("test_pipeline", [uppercase_processor, add_timestamp_processor])

    # 测试单次处理
    print("\n📝 测试1: 单次处理")
    result = optimizer.process_pipeline_sync("test_pipeline", "hello world")
    print(f"结果: {result}")

    # 测试异步处理
    print("\n📝 测试2: 异步处理")
    result = await optimizer.process_pipeline_async("test_pipeline", "async test")
    print(f"结果: {result}")

    # 测试批处理
    print("\n📝 测试3: 批处理")
    batch_data = [f"item_{i}" for i in range(10)]
    batch_results = optimizer.batch_process("test_pipeline", batch_data)
    print(f"批处理结果数量: {len(batch_results)}")

    # 测试缓存
    print("\n📝 测试4: 缓存效果")
    start_time = time.time()
    optimizer.process_pipeline_sync("test_pipeline", "cached data")
    cache_time = time.time() - start_time

    start_time = time.time()
    optimizer.process_pipeline_sync("test_pipeline", "cached data")
    cache_hit_time = time.time() - start_time

    print(f"首次处理时间: {cache_time:.4f}s")
    print(f"缓存命中时间: {cache_hit_time:.4f}s")
    print(f"加速比: {cache_time/cache_hit_time:.2f}x")

    # 性能报告
    print("\n📊 性能报告:")
    report = optimizer.get_performance_report()
    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))

    # 清理
    optimizer.cleanup()
    print("\n✅ 数据流优化器测试完成!")


if __name__ == "__main__":
    asyncio.run(test_data_flow_optimizer())
