#!/usr/bin/env python3
# ruff: noqa: E402 - Module level imports placed after class definitions to avoid circular dependencies
"""
感知模块
Perception Module

负责多模态输入的感知和处理,包括文本、图像、音频、视频等。
支持流式处理和实时感知。

作者: Athena AI系统
创建时间: 2025-12-04
版本: 3.0.0
"""

from __future__ import annotations
import inspect
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable, Coroutine
from typing import Any

# 从types.py导入统一的类型定义
from .types import InputType, PerceptionResult

logger = logging.getLogger(__name__)

# 类型别名
CallbackFunc = Callable[[Any], Any | Coroutine[Any, Any, Any]]


class BaseProcessor(ABC):
    """基础处理器"""

    def __init__(self, processor_id: str, config: dict[str, Any] | None = None):
        self.processor_id = processor_id
        self.config = config or {}
        self.initialized = False
        self.callbacks: dict[str, list[CallbackFunc]] = {}

    @abstractmethod
    async def initialize(self):
        """初始化处理器"""
        pass

    @abstractmethod
    async def process(self, data: Any, input_type: str) -> PerceptionResult:
        """处理输入数据"""
        pass

    @abstractmethod
    async def cleanup(self):
        """清理处理器"""
        pass

    def health_check(self) -> bool:
        """健康检查

        检查处理器是否健康运行。默认实现基于初始化状态。
        子类可以覆盖此方法以实现更复杂的健康检查逻辑。

        Returns:
            bool: 处理器是否健康
        """
        return self.initialized

    def register_callback(self, event: str, callback: CallbackFunc) -> None:
        """注册回调函数"""
        if event not in self.callbacks:
            self.callbacks[event] = []
        self.callbacks[event].append(callback)

    async def trigger_callbacks(self, event: str, data: Any) -> None:
        """触发回调函数"""
        if event in self.callbacks:
            for callback in self.callbacks[event]:
                try:
                    if inspect.iscoroutinefunction(callback):
                        result = callback(data)
                        if inspect.isawaitable(result):
                            await result
                    else:
                        _ = callback(data)
                except Exception as e:
                    logger.error(f"回调执行失败 {event}: {e}")


class PerceptionEngine:
    """感知引擎"""

    def __init__(self, agent_id: str, config: dict[str, Any] | None = None):
        self.agent_id = agent_id
        self.config = config or {}
        self.initialized = False

        # 处理器注册表
        self.processors: dict[InputType, BaseProcessor] = {}

        # 回调函数注册表
        self._callbacks: dict[str, list[CallbackFunc]] = {}

        # 优化和监控组件
        self.optimizer = None
        self.monitor = None

        # 全局实例
        self.global_instance: PerceptionEngine | None = None

        logger.info(f"👁️ 创建感知引擎: {agent_id}")

    async def initialize(self):
        """初始化感知引擎"""
        if self.initialized:
            return

        logger.info(f"🚀 启动感知引擎: {self.agent_id}")

        try:
            # 初始化处理器
            await self._initialize_processors()

            self.initialized = True
            logger.info(f"✅ 感知引擎启动完成: {self.agent_id}")

        except Exception as e:
            logger.error(f"❌ 感知引擎启动失败 {self.agent_id}: {e}")
            raise

    async def _initialize_processors(self):
        """初始化处理器"""
        from .processors.audio_processor import AudioProcessor
        from .processors.enhanced_multimodal_processor import (
            EnhancedMultiModalProcessor,
        )
        from .processors.image_processor import ImageProcessor
        from .processors.multimodal_processor import MultiModalProcessor
        from .processors.text_processor import TextProcessor
        from .processors.video_processor import VideoProcessor

        # 创建处理器
        text_processor = TextProcessor("text_processor", self.config.get("text", {}))
        image_processor = ImageProcessor("image_processor", self.config.get("image", {}))
        audio_processor = AudioProcessor("audio_processor", self.config.get("audio", {}))
        video_processor = VideoProcessor("video_processor", self.config.get("video", {}))

        # 根据配置选择多模态处理器
        use_enhanced = self.config.get("use_enhanced_multimodal", True)
        if use_enhanced:
            multimodal_processor = EnhancedMultiModalProcessor(
                "enhanced_multimodal_processor", self.config.get("multimodal", {})
            )
            logger.info("🚀 使用增强多模态处理器")
        else:
            multimodal_processor = MultiModalProcessor(
                "multimodal_processor", self.config.get("multimodal", {})
            )
            logger.info("📦 使用标准多模态处理器")

        # 初始化处理器
        await text_processor.initialize()
        await image_processor.initialize()
        await audio_processor.initialize()
        await video_processor.initialize()
        await multimodal_processor.initialize()

        # 检查是否启用优化和监控
        enable_optimization = self.config.get("performance", {}).get("enable_cache", False)
        enable_monitoring = self.config.get("monitoring", {}).get("enabled", False)

        # 应用优化和监控(条件性启用)
        if enable_optimization or enable_monitoring:
            try:
                from .monitoring_metrics import get_global_monitor
                from .performance_optimizer import get_global_optimizer

                optimizer = await get_global_optimizer(self.config.get("performance", {}))
                monitor = await get_global_monitor(self.config.get("monitoring", {}))

                # 优化处理器
                if enable_optimization:
                    for processor in [
                        text_processor,
                        image_processor,
                        audio_processor,
                        video_processor,
                        multimodal_processor,
                    ]:
                        await optimizer.optimize_processor(processor)

                # 启动监控
                if enable_monitoring:
                    all_processors = [
                        text_processor,
                        image_processor,
                        audio_processor,
                        video_processor,
                        multimodal_processor,
                    ]
                    await monitor.start_monitoring(all_processors)

                # 保存优化器和监控器引用
                self.optimizer = optimizer
                self.monitor = monitor

                logger.info("✅ 感知处理器初始化完成(含优化和监控)")
            except Exception as e:
                logger.warning(f"⚠️ 优化和监控启用失败,使用基础版本: {e}")
                enable_optimization = False
                enable_monitoring = False

        # 注册处理器
        self.processors[InputType.TEXT] = text_processor
        self.processors[InputType.IMAGE] = image_processor
        self.processors[InputType.AUDIO] = audio_processor
        self.processors[InputType.VIDEO] = video_processor
        self.processors[InputType.MULTIMODAL] = multimodal_processor

        if not (enable_optimization or enable_monitoring):
            # 保存空的引用
            self.optimizer = None
            self.monitor = None
            logger.info("✅ 感知处理器初始化完成(基础版本)")

    async def process(self, data: Any, input_type: str) -> PerceptionResult:
        """处理输入数据"""
        if not self.initialized:
            raise RuntimeError("感知引擎未初始化")

        try:
            # 检测输入类型
            detected_type = self._detect_input_type(data, input_type)

            # 获取对应处理器
            if detected_type == InputType.UNKNOWN:
                raise ValueError(f"无法处理输入类型: {input_type}")

            processor = self.processors.get(detected_type)
            if not processor:
                raise ValueError(f"未找到处理器: {detected_type}")

            # 处理数据
            result = await processor.process(data, detected_type.value)

            # 记录处理结果
            await self._record_perception_result(result)

            logger.debug(f"👁️ 感知处理完成: {detected_type.value}")

            return result

        except Exception as e:
            logger.error(f"❌ 感知处理失败 {self.agent_id}: {e}")
            raise

    def _detect_input_type(self, data: Any, input_type: str) -> InputType:
        """检测输入类型"""
        if input_type:
            try:
                return InputType(input_type.lower())
            except ValueError:
                # 指定的类型无效,记录并继续自动检测
                logger.debug(f"指定的输入类型 '{input_type}' 无效,使用自动检测")

        # 基于数据内容自动检测
        if isinstance(data, str):
            return InputType.TEXT
        elif hasattr(data, "shape") and hasattr(data, "dtype"):  # numpy array
            if len(data.shape) == 3:  # 可能是图像
                return InputType.IMAGE
            elif len(data.shape) == 1:  # 可能是音频
                return InputType.AUDIO
        elif isinstance(data, dict) and "modality" in data:
            return InputType.MULTIMODAL

        return InputType.UNKNOWN

    async def _record_perception_result(self, result: PerceptionResult):
        """记录感知结果"""
        try:
            # 构建感知记录(用于未来的记忆系统集成)
            _perception_record = {
                "type": "perception_result",
                "input_type": result.input_type.value,
                "content_summary": str(result.raw_content)[:200],
                "features": result.features,
                "confidence": result.confidence,
                "timestamp": result.timestamp.isoformat(),
                "agent_id": self.agent_id,
            }

            # TODO: 与记忆系统集成
            # await self.memory_system.store_memory(_perception_record)

            logger.debug("📝 感知结果已记录")

        except Exception as e:
            logger.error(f"记录感知结果失败: {e}")

    async def stream_process(self, data_stream: Any, input_type: str) -> Any:
        """流式处理"""
        if not self.initialized:
            raise RuntimeError("感知引擎未初始化")

        try:
            # 检测输入类型
            detected_type = self._detect_input_type(data_stream, input_type)

            # 获取处理器
            processor = self.processors.get(detected_type)
            if not processor or not hasattr(processor, "stream_process"):
                # 降级到普通处理
                logger.warning(f"处理器不支持流式处理,降级到普通处理: {detected_type}")
                result = await self.process(data_stream, input_type)
                yield result
                return

            # 流式处理
            async for chunk in processor.stream_process(data_stream):
                yield chunk

        except Exception as e:
            logger.error(f"❌ 流式处理失败 {self.agent_id}: {e}")
            raise

    async def get_status(self) -> dict[str, Any]:
        """获取感知引擎状态"""
        processor_status = {}
        for input_type, processor in self.processors.items():
            processor_status[input_type.value] = {
                "processor_id": processor.processor_id,
                "initialized": processor.initialized,
                "config_keys": list(processor.config.keys()) if processor.config else [],
            }

        return {
            "agent_id": self.agent_id,
            "initialized": self.initialized,
            "processor_count": len(self.processors),
            "available_processors": list(self.processors.keys()),
            "processor_status": processor_status,
        }

    async def get_performance_dashboard(self) -> dict[str, Any]:
        """获取性能监控仪表板"""
        dashboard = {
            "engine_status": await self.get_status(),
            "optimization_status": {},
            "monitoring_dashboard": {},
        }

        # 获取优化器状态
        if self.optimizer:
            dashboard["optimization_status"] = self.optimizer.get_performance_metrics()

        # 获取监控仪表板
        if self.monitor:
            dashboard["monitoring_dashboard"] = self.monitor.get_monitoring_dashboard()

        return dashboard

    async def get_performance_report(self, time_range: int = 3600) -> dict[str, Any]:
        """获取性能报告"""
        report = {
            "engine_id": self.agent_id,
            "time_range_seconds": time_range,
            "processor_performance": {},
        }

        # 获取监控器报告
        if self.monitor:
            report.update(self.monitor.get_performance_report(time_range))

        # 获取各处理器统计
        for input_type, processor in self.processors.items():
            if hasattr(processor, "get_processing_stats"):
                report["processor_performance"][
                    input_type.value
                ] = await processor.get_processing_stats()

        return report

    def register_callback(self, event_type: str, callback: CallbackFunc) -> None:
        """注册回调函数"""
        if event_type not in self._callbacks:
            self._callbacks[event_type] = []
        self._callbacks[event_type].append(callback)

    async def shutdown(self):
        """关闭感知引擎"""
        logger.info(f"🔄 关闭感知引擎: {self.agent_id}")

        try:
            # 停止监控
            if self.monitor:
                await self.monitor.stop_monitoring()

            # 清理优化器
            if self.optimizer:
                await self.optimizer.cleanup()

            # 关闭所有处理器
            for processor in self.processors.values():
                await processor.cleanup()

            self.processors.clear()
            self.initialized = False

            logger.info(f"✅ 感知引擎已关闭: {self.agent_id}")

        except Exception as e:
            logger.error(f"❌ 感知引擎关闭失败 {self.agent_id}: {e}")

    @classmethod
    async def initialize_global(cls):
        """初始化全局实例"""
        if cls.global_instance is None:
            cls.global_instance = cls("global", {})
            await cls.global_instance.initialize()
        return cls.global_instance

    @classmethod
    async def shutdown_global(cls):
        """关闭全局实例"""
        if cls.global_instance:
            await cls.global_instance.shutdown()
            cls.global_instance = None


# 导出统一接口
# 导出自适应限流器
# 可选导入 - adaptive_rate_limiter模块可能不存在
try:
    from .adaptive_rate_limiter import (
    AdaptiveRateLimiter,
    LoadLevel,
    RateLimitConfig,
    RateLimiterMetrics,
    RateLimitResult,
    RateLimitStrategy,
    SystemMetrics,
    create_rate_limiter,
    get_global_limiter,
    initialize_global_limiter,
    rate_limit,
)
except ImportError:
    # adaptive_rate_limiter模块未安装或不可用
    pass


# 导出BM25检索
# 可选导入 - bm25_retriever模块可能不存在
try:
    from .bm25_retriever import (
    BM25Config,
    BM25Retriever,
    Document,
    HybridRetriever,
    SearchResult,
    create_bm25_retriever,
    create_hybrid_retriever,
)
except ImportError:
    # bm25_retriever模块未安装或不可用
    pass


# 导出缓存预热
# 可选导入 - cache_warmer模块可能不存在
try:
    from .cache_warmer import (
    CacheWarmer,
    CacheWarmerManager,
    WarmupConfig,
    WarmupItem,
    WarmupResult,
    WarmupStrategy,
    create_cache_warmer,
    get_warmer_manager,
)
except ImportError:
    # cache_warmer模块未安装或不可用
    pass


# 导出统一配置
# 可选导入 - config_manager模块可能不存在
try:
    from .config_manager import (
    CacheConfig,
    PerceptionConfigManager,
    get_config_manager,
)
except ImportError:
    # config_manager模块未安装或不可用
    pass


# 导出动态负载均衡器
# 可选导入 - dynamic_load_balancer模块可能不存在
try:
    from .dynamic_load_balancer import (
    DynamicLoadBalancer,
    HealthStatus,
    LoadBalancerMetrics,
    LoadBalancingStrategy,
    ProcessorNode,
    RoutingResult,
    create_load_balancer,
)
except ImportError:
    # dynamic_load_balancer模块未安装或不可用
    pass


# 导出智能缓存淘汰
# 可选导入 - intelligent_cache_eviction模块可能不存在
try:
    from .intelligent_cache_eviction import (
    CacheEntry,
    CacheStats,
    EvictionPolicy,
    EvictionResult,
    IntelligentCacheEvictor,
    create_cache_evictor,
)
except ImportError:
    # intelligent_cache_eviction模块未安装或不可用
    pass

from .interfaces import (
    ICache,
    IMonitor,
    IPerceptionEngine,
    IProcessor,
    IProcessorFactory,
    IStreamProcessor,
)

# 导出AI模型抽象层
# 可选导入 - model_abstraction模块可能不存在
try:
    from .model_abstraction import (
    AIModel,
    BaseModel,
    ModelConfig,
    ModelInput,
    ModelMetrics,
    ModelOutput,
    ModelPipeline,
    ModelProvider,
    ModelRegistry,
    ModelType,
    get_model_registry,
)
except ImportError:
    # model_abstraction模块未安装或不可用
    pass


# 导出OpenTelemetry追踪
# 可选导入 - opentelemetry_tracing模块可能不存在
try:
    from .opentelemetry_tracing import (
    PerceptionTracer,
    TracerBackend,
    TracingConfig,
    get_tracer,
    initialize_tracing,
    trace,
)
except ImportError:
    # opentelemetry_tracing模块未安装或不可用
    pass


# 导出智能优先级队列
# 可选导入 - priority_queue模块可能不存在
try:
    from .priority_queue import (
    Priority,
    PriorityTask,
    QueueMetrics,
    SchedulingPolicy,
    SmartPriorityQueue,
    create_priority_queue,
)
except ImportError:
    # priority_queue模块未安装或不可用
    pass

from .processors.audio_processor import AudioProcessor
from .processors.enhanced_multimodal_processor import EnhancedMultiModalProcessor
from .processors.image_processor import ImageProcessor
from .processors.multimodal_processor import MultiModalProcessor

# 导出类
from .processors.text_processor import TextProcessor
from .processors.video_processor import VideoProcessor

# 导出请求合并器
# 可选导入 - request_merger模块可能不存在
try:
    from .request_merger import (
    MergeKey,
    MergeResult,
    MergerMetrics,
    MergeStrategy,
    PendingRequest,
    RequestMerger,
    create_request_merger,
    get_global_merger,
    initialize_global_merger,
    merge_requests,
)
except ImportError:
    # request_merger模块未安装或不可用
    pass

# 可选导入 - resilience模块可能不存在
try:
    from .resilience import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerMetrics,
    CircuitState,
    ResilientExecutor,
    RetryConfig,
    RetryExecutor,
    RetryResult,
    create_circuit_breaker,
    create_retry_executor,
)
except ImportError:
    # resilience模块未安装或不可用
    pass


# 导出重试和熔断
# 可选导入 - resilience模块可能不存在
try:
    from .resilience import (
    RetryStrategy as ResilienceRetryStrategy,
)
except ImportError:
    # resilience模块未安装或不可用
    pass

# 可选导入 - resilience模块可能不存在
try:
    from .resilience import (
    circuit_breaker as circuit_breaker_decorator,
)
except ImportError:
    # resilience模块未安装或不可用
    pass

# 可选导入 - resilience模块可能不存在
try:
    from .resilience import (
    retry as retry_decorator,
)
except ImportError:
    # resilience模块未安装或不可用
    pass


# 导出流式处理器
# 可选导入 - stream_processor模块可能不存在
try:
    from .stream_processor import (
    ChunkSize,
    StreamChunk,
    StreamConfig,
    StreamProcessor,
    StreamProgress,
    StreamResult,
    chunk_stream,
    process_data_stream,
    process_file_stream,
)
except ImportError:
    # stream_processor模块未安装或不可用
    pass


# 导出统一优化处理器
# 可选导入 - unified_optimized_processor模块可能不存在
try:
    from .unified_optimized_processor import (
    ProcessingStats,
    ProcessingStrategy,
    UnifiedOptimizedProcessor,
    create_unified_optimized_processor,
)
except ImportError:
    # unified_optimized_processor模块未安装或不可用
    pass


__all__ = [
    "AIModel",
    "AdaptiveRateLimiter",
    "AudioProcessor",
    # BM25检索
    "BM25Config",
    "BM25Retriever",
    "BaseModel",
    "BaseProcessor",
    # 统一配置
    "CacheConfig",
    "CacheEntry",
    "CacheStats",
    # 缓存预热
    "CacheWarmer",
    "CacheWarmerManager",
    # 流式处理器
    "ChunkSize",
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerMetrics",
    "CircuitState",
    "Document",
    "DynamicLoadBalancer",
    "EnhancedMultiModalProcessor",
    # 智能缓存淘汰
    "EvictionPolicy",
    "EvictionResult",
    "HealthStatus",
    "HybridRetriever",
    "ICache",
    "IMonitor",
    "IPerceptionEngine",
    # 统一接口
    "IProcessor",
    "IProcessorFactory",
    "IStreamProcessor",
    "ImageProcessor",
    "InputType",
    "IntelligentCacheEvictor",
    "LoadBalancerMetrics",
    # 动态负载均衡器
    "LoadBalancingStrategy",
    "LoadLevel",
    "MergeKey",
    "MergeResult",
    # 请求合并器
    "MergeStrategy",
    "MergerMetrics",
    "ModelConfig",
    "ModelInput",
    "ModelMetrics",
    "ModelOutput",
    "ModelPipeline",
    "ModelProvider",
    "ModelRegistry",
    # AI模型抽象层
    "ModelType",
    "MultiModalProcessor",
    "PendingRequest",
    # 配置管理
    "PerceptionConfigManager",
    "PerceptionEngine",
    "PerceptionResult",
    "PerceptionSystem",  # 添加别名以保持兼容性
    # OpenTelemetry追踪
    "PerceptionTracer",
    # 智能优先级队列
    "Priority",
    "PriorityTask",
    "ProcessingStats",
    "ProcessingStrategy",
    "ProcessorNode",
    "QueueMetrics",
    "RateLimitConfig",
    "RateLimitResult",
    # 自适应限流器
    "RateLimitStrategy",
    "RateLimiterMetrics",
    "RequestMerger",
    # 重试和熔断
    "ResilienceRetryStrategy",
    "ResilientExecutor",
    "RetryConfig",
    "RetryExecutor",
    "RetryResult",
    "RoutingResult",
    "SchedulingPolicy",
    "SearchResult",
    "SmartPriorityQueue",
    "StreamChunk",
    "StreamConfig",
    "StreamProcessor",
    "StreamProgress",
    "StreamResult",
    "SystemMetrics",
    "TextProcessor",
    "TracerBackend",
    "TracingConfig",
    # 统一优化处理器
    "UnifiedOptimizedProcessor",
    "VideoProcessor",
    "WarmupConfig",
    "WarmupItem",
    "WarmupResult",
    "WarmupStrategy",
    "chunk_stream",
    "circuit_breaker_decorator",
    "create_bm25_retriever",
    "create_cache_evictor",
    "create_cache_warmer",
    "create_circuit_breaker",
    "create_hybrid_retriever",
    "create_load_balancer",
    "create_priority_queue",
    "create_rate_limiter",
    "create_request_merger",
    "create_retry_executor",
    "create_unified_optimized_processor",
    "get_config_manager",
    "get_global_limiter",
    "get_global_merger",
    "get_model_registry",
    "get_tracer",
    "get_warmer_manager",
    "initialize_global_limiter",
    "initialize_global_merger",
    "initialize_tracing",
    "merge_requests",
    "process_data_stream",
    "process_file_stream",
    "rate_limit",
    "retry_decorator",
    "trace",
]

# 添加别名以保持向后兼容性
PerceptionSystem = PerceptionEngine
