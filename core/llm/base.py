from __future__ import annotations
"""
统一LLM层 - 基础抽象类
定义所有模型适配器必须遵循的接口规范

作者: Claude Code
日期: 2026-01-23
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ModelType(Enum):
    """模型类型分类"""

    REASONING = "reasoning"  # 推理模型 - 用于复杂分析和逻辑推理
    CHAT = "chat"  # 对话模型 - 用于日常对话和简单问答
    MULTIMODAL = "multimodal"  # 多模态模型 - 支持图像、音频等多模态处理
    SPECIALIZED = "specialized"  # 专用模型 - 数学、代码、专利分析等
    LOCAL = "local"  # 本地模型 - 本地部署的开源模型
    RERANK = "rerank"  # 重排序模型 - 用于结果重排序和优化


class DeploymentType(Enum):
    """部署类型"""

    CLOUD = "cloud"  # 云端API
    LOCAL = "local"  # 本地部署
    HYBRID = "hybrid"  # 混合部署


class SelectionStrategy(Enum):
    """模型选择策略"""

    COST_OPTIMIZED = "cost_optimized"  # 成本优化 - 优先使用低成本模型
    PERFORMANCE_OPTIMIZED = "performance_optimized"  # 性能优化 - 优先使用低延迟模型
    QUALITY_OPTIMIZED = "quality_optimized"  # 质量优化 - 优先使用高质量模型
    BALANCED = "balanced"  # 平衡策略 - 综合考虑成本、性能、质量
    LOCAL_FIRST = "local_first"  # 本地优先 - 优先使用本地模型


@dataclass
class ModelCapability:
    """
    模型能力定义

    描述一个模型的所有能力和特性,用于模型选择和匹配
    """

    model_id: str  # 模型唯一标识符
    model_type: ModelType  # 模型类型
    deployment: DeploymentType  # 部署类型

    # 能力特征
    max_context: int  # 最大上下文长度(tokens)
    supports_streaming: bool = False  # 是否支持流式输出
    supports_function_call: bool = False  # 是否支持函数调用
    supports_vision: bool = False  # 是否支持视觉
    supports_thinking: bool = False  # 是否支持深度思考模式

    # 性能指标
    avg_latency_ms: float = 1000.0  # 平均延迟(毫秒)
    throughput_tps: float = 50.0  # 吞吐量(tokens/秒)

    # 成本指标
    cost_per_1k_tokens: float = 0.01  # 每1K tokens成本(元)

    # 质量指标
    quality_score: float = 0.8  # 质量评分(0-1)

    # 适用场景
    suitable_tasks: list[str] = field(default_factory=list)  # 适用的任务类型
    unsuitable_tasks: list[str] = field(default_factory=list)  # 不适用的任务类型

    def is_suitable_for(self, task_type: str) -> bool:
        """检查模型是否适合指定任务类型"""
        if task_type in self.unsuitable_tasks:
            return False
        if not self.suitable_tasks:
            return True  # 没有限制则认为适合
        return task_type in self.suitable_tasks

    def estimate_cost(self, tokens: int) -> float:
        """估算成本"""
        return (tokens / 1000) * self.cost_per_1k_tokens

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "model_id": self.model_id,
            "model_type": self.model_type.value,
            "deployment": self.deployment.value,
            "max_context": self.max_context,
            "supports_streaming": self.supports_streaming,
            "supports_function_call": self.supports_function_call,
            "supports_vision": self.supports_vision,
            "supports_thinking": self.supports_thinking,
            "avg_latency_ms": self.avg_latency_ms,
            "throughput_tps": self.throughput_tps,
            "cost_per_1k_tokens": self.cost_per_1k_tokens,
            "quality_score": self.quality_score,
            "suitable_tasks": self.suitable_tasks,
            "unsuitable_tasks": self.unsuitable_tasks,
        }


@dataclass
class LLMRequest:
    """
    统一LLM请求

    所有模型适配器接收的统一请求格式
    """

    message: str  # 用户消息
    task_type: str  # 任务类型
    context: dict[str, Any] = field(default_factory=dict)  # 上下文信息
    user_id: str = "default"  # 用户ID

    # 可选参数
    temperature: float = 0.7  # 温度参数(0-1,越高越随机)
    max_tokens: int = 2000  # 最大生成tokens数
    stream: bool = False  # 是否使用流式输出
    enable_thinking: bool = False  # 是否启用深度思考模式

    # 约束条件
    preferred_model: Optional[str] = None  # 偏好的模型
    max_cost: Optional[float] = None  # 最大成本
    max_latency: Optional[float] = None  # 最大延迟(秒)
    require_quality: Optional[float] = None  # 要求的最小质量分数
    prefer_local: bool = False  # 是否偏好本地模型

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "message": self.message,
            "task_type": self.task_type,
            "context": self.context,
            "user_id": self.user_id,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": self.stream,
            "enable_thinking": self.enable_thinking,
            "preferred_model": self.preferred_model,
            "max_cost": self.max_cost,
            "max_latency": self.max_latency,
            "require_quality": self.require_quality,
            "prefer_local": self.prefer_local,
        }


@dataclass
class LLMResponse:
    """
    统一LLM响应

    所有模型适配器返回的统一响应格式
    """

    content: str  # 生成的内容
    model_used: str  # 实际使用的模型
    reasoning_content: str = ""  # 推理过程(深度思考模式)
    thinking_content: str = ""  # 思考过程

    # 元数据
    tokens_used: int = 0  # 使用的tokens数
    processing_time: float = 0.0  # 处理时间(秒)
    cost: float = 0.0  # 成本(元)

    # 质量指标
    quality_score: float = 0.0  # 质量评分(0-1)
    confidence: float = 0.0  # 置信度(0-1)

    # 缓存标记
    from_cache: bool = False  # 是否来自缓存

    # 原始响应
    raw_response: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "content": self.content,
            "model_used": self.model_used,
            "reasoning_content": self.reasoning_content,
            "thinking_content": self.thinking_content,
            "tokens_used": self.tokens_used,
            "processing_time": self.processing_time,
            "cost": self.cost,
            "quality_score": self.quality_score,
            "confidence": self.confidence,
            "from_cache": self.from_cache,
            "raw_response": self.raw_response,
        }


class BaseLLMAdapter(ABC):
    """
    LLM适配器基类

    所有模型适配器必须继承此类并实现抽象方法
    """

    def __init__(self, model_id: str, capability: ModelCapability):
        """
        初始化适配器

        Args:
            model_id: 模型唯一标识符
            capability: 模型能力定义
        """
        self.model_id = model_id
        self.capability = capability
        self._initialized = False

    @abstractmethod
    async def initialize(self) -> bool:
        """
        初始化模型

        Returns:
            bool: 初始化是否成功
        """
        pass

    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        生成响应

        Args:
            request: LLM请求

        Returns:
            LLMResponse: LLM响应
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            bool: 模型是否健康可用
        """
        pass

    @abstractmethod
    async def get_stats(self) -> dict[str, Any]:
        """
        获取统计信息

        Returns:
            Dict: 统计信息字典
        """
        pass

    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        return self._initialized

    async def validate_request(self, request: LLMRequest) -> bool:
        """
        验证请求是否有效

        Args:
            request: LLM请求

        Returns:
            bool: 请求是否有效
        """
        # 检查上下文长度
        if len(request.message) > self.capability.max_context:
            return False

        # 检查是否支持流式输出
        if request.stream and not self.capability.supports_streaming:
            return False

        # 检查是否支持思考模式
        return not (request.enable_thinking and not self.capability.supports_thinking)
