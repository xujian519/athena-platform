#!/usr/bin/env python3
"""
Metal混合推理系统
Metal Hybrid Inference System for llama-cpp-python

实现智能的CPU/GPU混合推理,优化性能和资源利用率
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .layer_offload_manager import LayerOffloadManager, OffloadConfig, OffloadStrategy

logger = logging.getLogger(__name__)


class WorkloadType(Enum):
    """工作负载类型"""

    # 交互式:低延迟优先
    INTERACTIVE = "interactive"
    # 批处理:高吞吐量优先
    BATCH = "batch"
    # 长文本:内存优化
    LONG_CONTEXT = "long_context"
    # 实时流:快速响应
    STREAMING = "streaming"


class ExecutionMode(Enum):
    """执行模式"""

    # 自动模式:根据负载自动调整
    AUTO = "auto"
    # 性能模式:最大化GPU使用
    PERFORMANCE = "performance"
    # 均衡模式:平衡性能和内存
    BALANCED = "balanced"
    # 节能模式:最小化GPU使用
    POWER_SAVE = "power_save"


@dataclass
class HybridConfig:
    """混合推理配置"""

    # 执行模式
    mode: ExecutionMode = ExecutionMode.BALANCED

    # GPU层分配策略
    gpu_layer_ratio: float = 0.5  # 默认50%层到GPU
    dynamic_adjustment: bool = True  # 动态调整GPU层数

    # 性能参数
    n_threads: int = 8
    n_batch: int = 512
    n_ctx: int = 32768

    # 内存管理
    use_mmap: bool = True
    use_mlock: bool = False
    memory_threshold: float = 0.85  # 内存使用阈值

    # 批处理
    enable_batching: bool = True
    max_batch_size: int = 8
    batch_wait_time: float = 0.1

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "mode": self.mode.value,
            "n_gpu_layers": -1 if self.gpu_layer_ratio >= 1.0 else int(32 * self.gpu_layer_ratio),
            "n_ctx": self.n_ctx,
            "n_batch": self.n_batch,
            "n_threads": self.n_threads,
            "use_mmap": self.use_mmap,
            "use_mlock": self.use_mlock,
        }


@dataclass
class InferenceMetrics:
    """推理指标"""

    total_requests: int = 0
    total_tokens: int = 0
    total_time: float = 0.0
    gpu_time: float = 0.0
    cpu_time: float = 0.0

    avg_latency: float = 0.0
    p50_latency: float = 0.0
    p95_latency: float = 0.0
    p99_latency: float = 0.0

    tokens_per_second: float = 0.0
    gpu_utilization: float = 0.0
    memory_usage_gb: float = 0.0

    latency_samples: list[float] = field(default_factory=list)

    def update_latency(self, latency: float) -> None:
        """更新延迟样本"""
        self.latency_samples.append(latency)
        # 保留最近1000个样本
        if len(self.latency_samples) > 1000:
            self.latency_samples = self.latency_samples[-1000:]

        # 计算百分位数
        sorted_samples = sorted(self.latency_samples)
        self.avg_latency = sum(sorted_samples) / len(sorted_samples)
        self.p50_latency = sorted_samples[int(len(sorted_samples) * 0.5)]
        self.p95_latency = sorted_samples[int(len(sorted_samples) * 0.95)]
        self.p99_latency = sorted_samples[int(len(sorted_samples) * 0.99)]


class AdaptiveLayerScheduler:
    """
    自适应层调度器

    根据工作负载和系统状态动态调整CPU/GPU层分配
    """

    def __init__(
        self,
        total_layers: int,
        initial_gpu_ratio: float = 0.5,
        adjustment_interval: float = 10.0,
        min_gpu_ratio: float = 0.1,
        max_gpu_ratio: float = 1.0,
    ):
        """
        初始化调度器

        Args:
            total_layers: 总层数
            initial_gpu_ratio: 初始GPU层比例
            adjustment_interval: 调整间隔(秒)
            min_gpu_ratio: 最小GPU层比例
            max_gpu_ratio: 最大GPU层比例
        """
        self.total_layers = total_layers
        self.current_gpu_ratio = initial_gpu_ratio
        self.adjustment_interval = adjustment_interval
        self.min_gpu_ratio = min_gpu_ratio
        self.max_gpu_ratio = max_gpu_ratio

        self.last_adjustment_time = time.time()
        self.adjustment_history: list[dict[str, Any]] = []

        # 性能跟踪
        self.performance_window: list[float] = []
        self.window_size = 100

    def should_adjust(self) -> bool:
        """检查是否需要调整"""
        return time.time() - self.last_adjustment_time >= self.adjustment_interval

    def calculate_new_ratio(
        self, current_performance: float, target_latency: float, memory_pressure: float
    ) -> float:
        """
        计算新的GPU层比例

        Args:
            current_performance: 当前性能(tokens/秒)
            target_latency: 目标延迟(秒)
            memory_pressure: 内存压力(0-1)

        Returns:
            float: 新的GPU层比例
        """
        # 记录性能
        self.performance_window.append(current_performance)
        if len(self.performance_window) > self.window_size:
            self.performance_window.pop(0)

        # 计算性能趋势
        if len(self.performance_window) >= 10:
            recent_avg = sum(self.performance_window[-10:]) / 10
            overall_avg = sum(self.performance_window) / len(self.performance_window)
            trend = recent_avg / overall_avg if overall_avg > 0 else 1.0
        else:
            trend = 1.0

        # 调整策略
        new_ratio = self.current_gpu_ratio

        # 内存压力大:减少GPU层
        if memory_pressure > 0.9:
            new_ratio = max(self.min_gpu_ratio, new_ratio - 0.2)
            logger.info(f"内存压力高,减少GPU层: {new_ratio:.2f}")

        # 性能下降:增加GPU层
        elif trend < 0.9 and new_ratio < self.max_gpu_ratio:
            new_ratio = min(self.max_gpu_ratio, new_ratio + 0.1)
            logger.info(f"性能下降,增加GPU层: {new_ratio:.2f}")

        # 性能稳定且内存充足:尝试增加GPU层
        elif trend > 1.05 and memory_pressure < 0.8 and new_ratio < self.max_gpu_ratio:
            new_ratio = min(self.max_gpu_ratio, new_ratio + 0.05)
            logger.info(f"性能良好,增加GPU层: {new_ratio:.2f}")

        # 平滑调整
        new_ratio = self.current_gpu_ratio * 0.7 + new_ratio * 0.3
        new_ratio = max(self.min_gpu_ratio, min(self.max_gpu_ratio, new_ratio))

        # 记录调整历史
        self.adjustment_history.append(
            {
                "timestamp": time.time(),
                "old_ratio": self.current_gpu_ratio,
                "new_ratio": new_ratio,
                "performance": current_performance,
                "trend": trend,
                "memory_pressure": memory_pressure,
            }
        )

        self.current_gpu_ratio = new_ratio
        self.last_adjustment_time = time.time()

        return new_ratio

    def get_current_gpu_layers(self) -> int:
        """获取当前GPU层数"""
        return int(self.total_layers * self.current_gpu_ratio)

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "current_gpu_ratio": self.current_gpu_ratio,
            "current_gpu_layers": self.get_current_gpu_layers(),
            "total_adjustments": len(self.adjustment_history),
            "performance_trend": (
                sum(self.performance_window[-10:]) / len(self.performance_window[-10:])
                if len(self.performance_window) >= 10
                else 1.0
            ),
        }


class MetalHybridInferenceEngine:
    """
    Metal混合推理引擎

    核心功能:
    1. 智能执行模式选择
    2. 自适应层调度
    3. 性能监控和优化
    4. 资源管理
    """

    def __init__(
        self,
        model_path: str,
        model_name: str,
        quantization: str = "q4_k_m",
        config: HybridConfig | None = None,
    ):
        """
        初始化混合推理引擎

        Args:
            model_path: 模型路径
            model_name: 模型名称
            quantization: 量化方式
            config: 混合推理配置
        """
        self.model_path = model_path
        self.model_name = model_name
        self.quantization = quantization
        self.config = config or HybridConfig()

        # 初始化层管理器
        self.layer_manager = LayerOffloadManager(model_name, quantization)

        # 模型实例
        self.model = None
        self.total_layers = self.layer_manager._estimate_total_layers()

        # 自适应调度器
        self.scheduler = AdaptiveLayerScheduler(
            total_layers=self.total_layers, initial_gpu_ratio=self.config.gpu_layer_ratio
        )

        # 性能指标
        self.metrics = InferenceMetrics()

        # 工作负载检测
        self.request_history: list[dict[str, Any]] = []
        self.workload_type = WorkloadType.INTERACTIVE

        logger.info(
            f"MetalHybridInferenceEngine初始化: model={model_name}, "
            f"layers={self.total_layers}, mode={self.config.mode.value}"
        )

    async def initialize(self):
        """初始化引擎"""
        logger.info("正在加载模型...")
        start_time = time.time()

        # 根据配置加载模型
        await self._load_model()

        load_time = time.time() - start_time
        logger.info(f"模型加载完成: {load_time:.2f}秒")

    async def _load_model(self):
        """加载模型"""
        try:
            from llama_cpp import Llama
        except ImportError:
            raise ImportError("llama-cpp-python未安装。请运行: pip install llama-cpp-python")

        # 获取配置
        config_dict = self.config.to_dict()

        logger.info(
            f"加载模型配置: n_gpu_layers={config_dict['n_gpu_layers']}, "
            f"n_ctx={config_dict['n_ctx']}"
        )

        self.model = Llama(model_path=self.model_path, **config_dict, verbose=False)

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        workload_type: WorkloadType | None = None,
    ) -> str:
        """
        生成文本

        Args:
            prompt: 输入提示
            max_tokens: 最大生成token数
            temperature: 温度参数
            workload_type: 工作负载类型

        Returns:
            str: 生成的文本
        """
        # 检测工作负载类型
        if workload_type:
            self.workload_type = workload_type
        else:
            self.workload_type = self._detect_workload_type(prompt, max_tokens)

        # 调整执行模式
        await self._adjust_execution_mode()

        # 执行推理
        start_time = time.time()

        loop = asyncio.get_event_loop()
        output = await loop.run_in_executor(
            None,
            lambda: self.model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=0.9,
                stop=["\n\n\n"],  # 防止过长输出
            ),
        )

        elapsed = time.time() - start_time

        # 更新指标
        self._update_metrics(output, elapsed)

        # 记录请求历史
        self.request_history.append(
            {
                "timestamp": time.time(),
                "prompt_length": len(prompt),
                "max_tokens": max_tokens,
                "actual_tokens": output["usage"]["completion_tokens"],
                "latency": elapsed,
                "workload_type": self.workload_type.value,
            }
        )

        return output["choices"][0]["text"]

    def _detect_workload_type(self, prompt: str, max_tokens: int) -> WorkloadType:
        """检测工作负载类型"""
        # 短提示 + 少量输出 = 交互式
        if len(prompt) < 500 and max_tokens < 256:
            return WorkloadType.INTERACTIVE

        # 长提示 + 长上下文 = 长文本
        if len(prompt) > 4000:
            return WorkloadType.LONG_CONTEXT

        # 短提示 + 大量输出 = 批处理
        if max_tokens > 1000:
            return WorkloadType.BATCH

        # 默认交互式
        return WorkloadType.INTERACTIVE

    async def _adjust_execution_mode(self):
        """调整执行模式"""
        # 检查是否需要调整
        if not self.scheduler.should_adjust():
            return

        # 获取当前性能
        current_performance = self.metrics.tokens_per_second

        # 计算内存压力
        import psutil

        memory = psutil.virtual_memory()
        memory_pressure = memory.percent / 100.0

        # 根据工作负载类型调整目标延迟
        target_latencies = {
            WorkloadType.INTERACTIVE: 0.5,  # 500ms
            WorkloadType.BATCH: 5.0,  # 5秒
            WorkloadType.LONG_CONTEXT: 10.0,  # 10秒
            WorkloadType.STREAMING: 0.2,  # 200ms
        }
        target_latency = target_latencies.get(self.workload_type, 1.0)

        # 计算新的GPU层比例
        new_ratio = self.scheduler.calculate_new_ratio(
            current_performance=current_performance,
            target_latency=target_latency,
            memory_pressure=memory_pressure,
        )

        # 如果需要重新加载模型
        if abs(new_ratio - self.config.gpu_layer_ratio) > 0.1:
            logger.info(
                f"重新配置模型: GPU层比例 {self.config.gpu_layer_ratio:.2f} -> {new_ratio:.2f}"
            )
            self.config.gpu_layer_ratio = new_ratio
            # 注意:实际应用中可能需要重新加载模型
            # 这里简化处理,仅更新配置

    def _update_metrics(self, output: dict[str, Any], latency: float) -> Any:
        """更新性能指标"""
        self.metrics.total_requests += 1
        self.metrics.total_tokens += output["usage"]["completion_tokens"]
        self.metrics.total_time += latency

        # 更新延迟指标
        self.metrics.update_latency(latency)

        # 计算吞吐量
        if self.metrics.total_time > 0:
            self.metrics.tokens_per_second = self.metrics.total_tokens / self.metrics.total_time

    async def generate_batch(
        self, prompts: list[str], max_tokens: int = 512, temperature: float = 0.7
    ) -> list[str]:
        """
        批量生成

        Args:
            prompts: 提示列表
            max_tokens: 最大生成token数
            temperature: 温度参数

        Returns:
            list[str]: 生成文本列表
        """
        tasks = [
            self.generate(prompt, max_tokens, temperature, WorkloadType.BATCH) for prompt in prompts
        ]
        return await asyncio.gather(*tasks)

    def get_metrics(self) -> InferenceMetrics:
        """获取性能指标"""
        return self.metrics

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "config": {
                "mode": self.config.mode.value,
                "gpu_layer_ratio": self.config.gpu_layer_ratio,
                "n_threads": self.config.n_threads,
                "n_ctx": self.config.n_ctx,
            },
            "scheduler": self.scheduler.get_stats(),
            "metrics": {
                "total_requests": self.metrics.total_requests,
                "total_tokens": self.metrics.total_tokens,
                "avg_latency": self.metrics.avg_latency,
                "p95_latency": self.metrics.p95_latency,
                "p99_latency": self.metrics.p99_latency,
                "tokens_per_second": self.metrics.tokens_per_second,
            },
            "workload": {
                "current_type": self.workload_type.value,
                "request_history_size": len(self.request_history),
            },
        }

    def print_performance_report(self) -> Any:
        """打印性能报告"""
        stats = self.get_stats()

        print("\n" + "=" * 80)
        print("📊 Metal混合推理性能报告")
        print("=" * 80)
        print()
        print("⚙️  配置:")
        print(f"   执行模式: {stats['config']['mode']}")
        print(f"   GPU层比例: {stats['config']['gpu_layer_ratio']:.1%}")
        print(f"   CPU线程: {stats['config']['n_threads']}")
        print(f"   上下文长度: {stats['config']['n_ctx']}")
        print()
        print("📈 性能指标:")
        print(f"   总请求数: {stats['metrics']['total_requests']}")
        print(f"   总tokens: {stats['metrics']['total_tokens']}")
        print(f"   平均延迟: {stats['metrics']['avg_latency']:.3f}秒")
        print(f"   P95延迟: {stats['metrics']['p95_latency']:.3f}秒")
        print(f"   P99延迟: {stats['metrics']['p99_latency']:.3f}秒")
        print(f"   吞吐量: {stats['metrics']['tokens_per_second']:.2f} tokens/秒")
        print()
        print("🔄 调度器:")
        print(f"   当前GPU层数: {stats['scheduler']['current_gpu_layers']}")
        print(f"   调整次数: {stats['scheduler']['total_adjustments']}")
        print(f"   性能趋势: {stats['scheduler']['performance_trend']:.2%}")
        print()
        print("💼 工作负载:")
        print(f"   当前类型: {stats['workload']['current_type']}")
        print(f"   历史记录: {stats['workload']['request_history_size']} 条")
        print()
        print("=" * 80)


# 便捷函数
async def create_hybrid_engine(
    model_path: str,
    model_name: str,
    quantization: str = "q4_k_m",
    mode: str = "balanced",
    gpu_layer_ratio: float = 0.5,
) -> MetalHybridInferenceEngine:
    """
    创建混合推理引擎

    Args:
        model_path: 模型路径
        model_name: 模型名称
        quantization: 量化方式
        mode: 执行模式 ("auto", "performance", "balanced", "power_save")
        gpu_layer_ratio: GPU层比例

    Returns:
        MetalHybridInferenceEngine: 混合推理引擎
    """
    config = HybridConfig(mode=ExecutionMode(mode), gpu_layer_ratio=gpu_layer_ratio)

    engine = MetalHybridInferenceEngine(
        model_path=model_path, model_name=model_name, quantization=quantization, config=config
    )

    await engine.initialize()
    return engine
