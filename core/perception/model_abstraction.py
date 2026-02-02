#!/usr/bin/env python3
"""
AI模型抽象层
AI Model Abstraction Layer

提供统一的AI模型接口,支持多个模型的灵活切换和组合。

支持的模型类型:
1. 文本嵌入模型 (Embedding Models)
2. 文本生成模型 (Generation Models)
3. 图像理解模型 (Vision Models)
4. 多模态模型 (Multimodal Models)
5. 专利专用模型 (Patent-Specific Models)

设计原则:
1. 统一接口 - 所有模型实现相同的接口
2. 可插拔 - 支持运行时模型切换
3. 可组合 - 支持模型pipeline
4. 可扩展 - 易于添加新模型
5. 可观测 - 内置追踪和监控

作者: Athena AI系统
创建时间: 2026-01-25
版本: 1.0.0
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Generic, TypeVar

logger = logging.getLogger(__name__)

# 类型变量
T = TypeVar("T")


class ModelType(Enum):
    """模型类型"""

    EMBEDDING = "embedding"  # 嵌入模型
    GENERATION = "generation"  # 生成模型
    VISION = "vision"  # 视觉模型
    MULTIMODAL = "multimodal"  # 多模态模型
    PATENT_ANALYSIS = "patent_analysis"  # 专利分析模型
    SENTIMENT = "sentiment"  # 情感分析
    NER = "ner"  # 命名实体识别


class ModelProvider(Enum):
    """模型提供商"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    HUGGINGFACE = "huggingface"
    LOCAL = "local"
    CUSTOM = "custom"


@dataclass
class ModelConfig:
    """模型配置"""

    model_type: ModelType
    provider: ModelProvider
    model_name: str
    api_key: str | None = None
    api_base: str | None = None
    max_tokens: int = 2048
    temperature: float = 0.7
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0

    # 模型特定配置
    device: str = "cpu"  # cpu, cuda, mps
    batch_size: int = 32
    cache_embeddings: bool = True

    # 成本控制
    cost_per_1k_tokens: float = 0.0
    max_daily_cost: float = 100.0

    def validate(self) -> bool:
        """验证配置"""
        if self.temperature < 0 or self.temperature > 2:
            raise ValueError(f"temperature必须在[0,2]范围内,当前值: {self.temperature}")
        if self.max_tokens <= 0:
            raise ValueError(f"max_tokens必须大于0,当前值: {self.max_tokens}")
        return True


@dataclass
class ModelInput:
    """模型输入"""

    data: str | list[str] | Any  # 输入数据
    parameters: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ModelOutput:
    """模型输出"""

    result: Any  # 输出结果
    model_used: str  # 使用的模型
    confidence: float = 1.0  # 置信度
    tokens_used: int = 0  # 使用的token数
    cost: float = 0.0  # 成本(美元)
    latency: float = 0.0  # 延迟(秒)
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ModelMetrics:
    """模型指标"""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    total_latency: float = 0.0
    avg_latency: float = 0.0
    p95_latency: float = 0.0
    p99_latency: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0

    @property
    def success_rate(self) -> float:
        """成功率"""
        return self.successful_requests / max(self.total_requests, 1)

    @property
    def cache_hit_rate(self) -> float:
        """缓存命中率"""
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / max(total, 1)

    @property
    def avg_cost_per_request(self) -> float:
        """平均每次请求成本"""
        return self.total_cost / max(self.total_requests, 1)


class AIModel(ABC):
    """AI模型抽象基类"""

    def __init__(self, config: ModelConfig):
        """初始化模型

        Args:
            config: 模型配置
        """
        self.config = config
        self.config.validate()
        self.metrics = ModelMetrics()
        self._initialized = False

    @abstractmethod
    async def initialize(self) -> None:
        """初始化模型"""
        pass

    @abstractmethod
    async def process(self, input_data: ModelInput) -> ModelOutput:
        """处理输入

        Args:
            input_data: 模型输入

        Returns:
            模型输出
        """
        pass

    @abstractmethod
    async def batch_process(self, inputs: list[ModelInput]) -> list[ModelOutput]:
        """批量处理

        Args:
            inputs: 输入列表

        Returns:
            输出列表
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """健康检查"""
        pass

    async def cleanup(self) -> None:
        """清理资源"""
        self._initialized = False

    def get_metrics(self) -> ModelMetrics:
        """获取模型指标"""
        return self.metrics

    def estimate_cost(self, num_tokens: int) -> float:
        """估算成本

        Args:
            num_tokens: token数量

        Returns:
            成本(美元)
        """
        cost_per_1k = self.config.cost_per_1k_tokens
        return (num_tokens / 1000) * cost_per_1k


class BaseModel(AIModel):
    """基础模型实现(模板模式)"""

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self._model = None
        self._tokenizer = None

    async def initialize(self) -> None:
        """初始化模型"""
        if self._initialized:
            return

        logger.info(f"🔧 初始化模型: {self.config.model_name}")

        try:
            await self._load_model()
            await self._load_tokenizer()
            self._initialized = True
            logger.info(f"✅ 模型初始化完成: {self.config.model_name}")
        except Exception as e:
            logger.error(f"❌ 模型初始化失败 {self.config.model_name}: {e}")
            raise

    async def _load_model(self) -> None:
        """加载模型(子类实现)"""
        # 默认实现:无操作
        pass

    async def _load_tokenizer(self) -> None:
        """加载分词器(子类实现)"""
        # 默认实现:无操作
        pass

    async def process(self, input_data: ModelInput) -> ModelOutput:
        """处理输入"""
        if not self._initialized:
            raise RuntimeError("模型未初始化")

        start_time = asyncio.get_event_loop().time()

        try:
            # 检查缓存
            cached_result = await self._get_from_cache(input_data)
            if cached_result is not None:
                self.metrics.cache_hits += 1
                return cached_result

            self.metrics.cache_misses += 1

            # 实际处理
            result = await self._process_impl(input_data)

            # 记录指标
            latency = asyncio.get_event_loop().time() - start_time
            self._update_metrics(result, latency)

            # 缓存结果
            if self.config.cache_embeddings:
                await self._save_to_cache(input_data, result)

            return result

        except Exception as e:
            self.metrics.failed_requests += 1
            logger.error(f"❌ 处理失败 {self.config.model_name}: {e}")
            raise

    @abstractmethod
    async def _process_impl(self, input_data: ModelInput) -> ModelOutput:
        """实际处理实现(子类实现)"""
        pass

    async def _get_from_cache(self, input_data: ModelInput) -> ModelOutput | None:
        """从缓存获取(子类可覆盖)"""
        return None

    async def _save_to_cache(self, input_data: ModelInput, output: ModelOutput) -> None:
        """保存到缓存(子类可覆盖)"""
        pass

    async def batch_process(self, inputs: list[ModelInput]) -> list[ModelOutput]:
        """批量处理"""
        results = []
        for inp in inputs:
            result = await self.process(inp)
            results.append(result)
        return results

    def health_check(self) -> bool:
        """健康检查"""
        return self._initialized

    def _update_metrics(self, output: ModelOutput, latency: float) -> None:
        """更新指标"""
        self.metrics.total_requests += 1
        self.metrics.successful_requests += 1
        self.metrics.total_tokens += output.tokens_used
        self.metrics.total_cost += output.cost
        self.metrics.total_latency += latency

        # 更新平均延迟
        if self.metrics.total_requests > 0:
            self.metrics.avg_latency = self.metrics.total_latency / self.metrics.total_requests


class ModelRegistry:
    """模型注册表

    管理所有可用的AI模型,支持动态注册和获取。
    """

    def __init__(self):
        """初始化注册表"""
        self._models: dict[str, type[AIModel]] = {}
        self._instances: dict[str, AIModel] = {}
        self._aliases: dict[str, str] = {}  # 别名 -> 实际名称
        logger.info("📋 模型注册表初始化完成")

    def register(
        self,
        name: str,
        model_class: type[AIModel],
        aliases: list[str] | None = None,
    ) -> None:
        """注册模型

        Args:
            name: 模型名称
            model_class: 模型类
            aliases: 别名列表
        """
        self._models[name] = model_class

        # 注册别名
        if aliases:
            for alias in aliases:
                self._aliases[alias] = name

        logger.info(f"📦 注册模型: {name} (别名: {aliases})")

    async def get_model(self, name_or_alias: str, config: ModelConfig) -> AIModel:
        """获取模型实例

        Args:
            name_or_alias: 模型名称或别名
            config: 模型配置

        Returns:
            模型实例
        """
        # 解析别名
        name = self._aliases.get(name_or_alias, name_or_alias)

        # 检查是否已存在实例
        instance_key = f"{name}:{id(config)}"
        if instance_key in self._instances:
            return self._instances[instance_key]

        # 创建新实例
        if name not in self._models:
            available = ", ".join(self._models.keys())
            raise ValueError(f"未找到模型: {name_or_alias}。可用模型: {available}")

        model_class = self._models[name]
        instance = model_class(config)
        await instance.initialize()

        # 缓存实例
        self._instances[instance_key] = instance

        logger.info(f"✅ 创建模型实例: {name}")
        return instance

    def list_models(self) -> list[str]:
        """列出所有已注册的模型"""
        return list(self._models.keys())

    def get_model_info(self, name: str) -> dict[str, Any]:
        """获取模型信息

        Args:
            name: 模型名称

        Returns:
            模型信息字典
        """
        if name not in self._models:
            return {}

        model_class = self._models[name]
        return {
            "name": name,
            "class": model_class.__name__,
            "module": model_class.__module__,
            "doc": model_class.__doc__,
        }


class ModelPipeline:
    """模型管道

    支持多个模型的串联和并联组合。
    """

    def __init__(self, registry: ModelRegistry):
        """初始化管道

        Args:
            registry: 模型注册表
        """
        self.registry = registry
        self._stages: list[tuple[str, ModelConfig]] = []
        self._parallel_groups: list[list[tuple[str, ModelConfig]]] = []
        logger.info("🔗 模型管道初始化完成")

    def add_stage(self, model_name: str, config: ModelConfig) -> "ModelPipeline":
        """添加串联阶段

        Args:
            model_name: 模型名称
            config: 模型配置

        Returns:
            管道实例(支持链式调用)
        """
        self._stages.append((model_name, config))
        return self

    def add_parallel_group(self, models: list[tuple[str, ModelConfig]]) -> "ModelPipeline":
        """添加并联组

        Args:
            models: 模型列表 [(name, config), ...]

        Returns:
            管道实例(支持链式调用)
        """
        self._parallel_groups.append(models)
        return self

    async def process(self, input_data: ModelInput) -> ModelOutput:
        """处理输入(管道模式)

        Args:
            input_data: 输入数据

        Returns:
            最终输出
        """
        current_input = input_data

        # 执行串联阶段
        for model_name, config in self._stages:
            model = await self.registry.get_model(model_name, config)
            output = await model.process(current_input)

            # 更新输入为上一步的输出
            current_input = ModelInput(
                data=output.result,
                metadata={"stage_model": model_name},
            )

        # 执行并联组
        for group in self._parallel_groups:
            tasks = []
            for model_name, config in group:
                model = await self.registry.get_model(model_name, config)
                tasks.append(model.process(current_input))

            # 并行执行
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 处理结果
            successful_results = [r for r in results if isinstance(r, ModelOutput)]
            if successful_results:
                # 合并结果
                current_input = ModelInput(
                    data=[r.result for r in successful_results],
                    metadata={"parallel_models": len(group)},
                )

        return current_input

    async def batch_process(self, inputs: list[ModelInput]) -> list[ModelOutput]:
        """批量处理

        Args:
            inputs: 输入列表

        Returns:
            输出列表
        """
        results = []
        for inp in inputs:
            result = await self.process(inp)
            results.append(result)
        return results


# 全局模型注册表
_global_registry: ModelRegistry | None = None


def get_model_registry() -> ModelRegistry:
    """获取全局模型注册表"""
    global _global_registry
    if _global_registry is None:
        _global_registry = ModelRegistry()
    return _global_registry


__all__ = [
    "AIModel",
    "BaseModel",
    "ModelConfig",
    "ModelInput",
    "ModelMetrics",
    "ModelOutput",
    "ModelPipeline",
    "ModelProvider",
    "ModelRegistry",
    "ModelType",
    "get_model_registry",
]
