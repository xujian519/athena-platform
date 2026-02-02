#!/usr/bin/env python3
"""
感知模块工厂类
Perception Module Factory

提供统一的处理器和引擎创建接口,支持依赖注入和配置管理。

作者: Athena AI系统
创建时间: 2026-01-24
版本: 1.0.0
"""

import logging
from typing import Any, Optional

from .types import (
    InputType,
    OptimizedPerceptionConfig,
    PerceptionConfig,
    StreamConfig,
    StreamType,
)

logger = logging.getLogger(__name__)


class ProcessorFactory:
    """
    处理器工厂类

    负责创建各种处理器实例,支持单例模式和自定义配置。
    """

    # 处理器注册表
    _processors: dict[InputType, type] = {}
    _instances: dict[str, Any] = {}

    @classmethod
    def register_processor(cls, input_type: InputType, processor_class: type) -> None:
        """
        注册处理器类

        Args:
            input_type: 输入类型
            processor_class: 处理器类
        """
        cls._processors[input_type] = processor_class
        logger.debug(f"注册处理器: {input_type.value} -> {processor_class.__name__}")

    @classmethod
    def unregister_processor(cls, input_type: InputType) -> None:
        """
        注销处理器类

        Args:
            input_type: 输入类型
        """
        if input_type in cls._processors:
            del cls._processors[input_type]
            logger.debug(f"注销处理器: {input_type.value}")

    @classmethod
    def create_processor(
        cls, input_type: InputType, config: dict[str, Any] | None = None, singleton: bool = False
    ) -> Any:
        """
        创建处理器实例

        Args:
            input_type: 输入类型
            config: 配置参数
            singleton: 是否使用单例模式

        Returns:
            处理器实例

        Raises:
            ValueError: 不支持的输入类型
        """
        processor_class = cls._processors.get(input_type)
        if not processor_class:
            raise ValueError(f"不支持的输入类型: {input_type}")

        # 单例模式
        if singleton:
            instance_key = f"{input_type.value}_singleton"
            if instance_key not in cls._instances:
                cls._instances[instance_key] = processor_class(input_type.value, config or {})
                logger.debug(f"创建单例处理器: {instance_key}")
            return cls._instances[instance_key]

        # 普通模式
        instance = processor_class(input_type.value, config or {})
        logger.debug(f"创建处理器实例: {input_type.value}")
        return instance

    @classmethod
    def get_registered_processors(cls) -> list:
        """获取已注册的处理器类型列表"""
        return list(cls._processors.keys())


class PerceptionEngineFactory:
    """
    感知引擎工厂类

    负责创建不同类型的感知引擎实例。
    """

    # 引擎注册表
    _engines: dict[str, type] = {}
    _instances: dict[str, Any] = {}

    @classmethod
    def register_engine(cls, engine_type: str, engine_class: type) -> None:
        """
        注册引擎类

        Args:
            engine_type: 引擎类型标识
            engine_class: 引擎类
        """
        cls._engines[engine_type] = engine_class
        logger.debug(f"注册引擎: {engine_type} -> {engine_class.__name__}")

    @classmethod
    def create_engine(
        cls,
        agent_id: str,
        engine_type: str = "standard",
        config: PerceptionConfig | Optional[dict[str, Any] = None,
        singleton: bool = False,
    ) -> Any:
        """
        创建感知引擎实例

        Args:
            agent_id: 智能体ID
            engine_type: 引擎类型 ('standard', 'enhanced', 'optimized', 'patent')
            config: 配置对象或字典
            singleton: 是否使用单例模式

        Returns:
            感知引擎实例

        Raises:
            ValueError: 不支持的引擎类型
        """
        engine_class = cls._engines.get(engine_type)
        if not engine_class:
            raise ValueError(f"不支持的引擎类型: {engine_type}")

        # 转换配置为PerceptionConfig
        if config is None:
            config = PerceptionConfig()
        elif isinstance(config, dict):
            if engine_type == "optimized":
                config = OptimizedPerceptionConfig(**config)
            else:
                config = PerceptionConfig(**config)

        # 单例模式
        if singleton:
            instance_key = f"{engine_type}_{agent_id}"
            if instance_key not in cls._instances:
                cls._instances[instance_key] = engine_class(agent_id, config.__dict__)
                logger.info(f"创建单例引擎: {instance_key}")
            return cls._instances[instance_key]

        # 普通模式
        instance = engine_class(agent_id, config.__dict__)
        logger.info(f"创建引擎实例: {engine_type} for {agent_id}")
        return instance

    @classmethod
    def get_engine_types(cls) -> list:
        """获取已注册的引擎类型列表"""
        return list(cls._engines.keys())


class StreamProcessorFactory:
    """
    流处理器工厂类

    负责创建各种流处理器实例。
    """

    _processors: dict[StreamType, type] = {}

    @classmethod
    def register_processor(cls, stream_type: StreamType, processor_class: type) -> None:
        """注册流处理器类"""
        cls._processors[stream_type] = processor_class
        logger.debug(f"注册流处理器: {stream_type.value}")

    @classmethod
    def create_processor(cls, stream_type: StreamType, config: StreamConfig | None = None) -> Any:
        """
        创建流处理器实例

        Args:
            stream_type: 流类型
            config: 流配置

        Returns:
            流处理器实例
        """
        processor_class = cls._processors.get(stream_type)
        if not processor_class:
            raise ValueError(f"不支持的流类型: {stream_type}")

        config = config or StreamConfig()
        instance = processor_class(config)
        logger.debug(f"创建流处理器: {stream_type.value}")
        return instance


class PerceptionBuilder:
    """
    感知模块构建器

    提供流畅的API来构建复杂的感知处理管道。
    """

    def __init__(self, agent_id: str):
        """
        初始化构建器

        Args:
            agent_id: 智能体ID
        """
        self.agent_id = agent_id
        self.config = PerceptionConfig()
        self._processors = []
        self._middleware = []
        self._extensions = []

    def with_config(self, config: PerceptionConfig | dict[str, Any]) -> PerceptionBuilder:
        """
        设置配置

        Args:
            config: 配置对象或字典

        Returns:
            自身实例,支持链式调用
        """
        if isinstance(config, dict):
            self.config = PerceptionConfig(**config)
        else:
            self.config = config
        return self

    def with_processor(
        self, input_type: InputType, processor_config: dict | None = None
    ) -> PerceptionBuilder:
        """
        添加处理器

        Args:
            input_type: 输入类型
            processor_config: 处理器配置

        Returns:
            自身实例,支持链式调用
        """
        self._processors.append((input_type, processor_config or {}))
        return self

    def with_middleware(self, middleware: Any) -> PerceptionBuilder:
        """
        添加中间件

        Args:
            middleware: 中间件实例

        Returns:
            自身实例,支持链式调用
        """
        self._middleware.append(middleware)
        return self

    def with_extension(self, extension: Any) -> PerceptionBuilder:
        """
        添加扩展

        Args:
            extension: 扩展实例

        Returns:
            自身实例,支持链式调用
        """
        self._extensions.append(extension)
        return self

    async def build(self, engine_type: str = "standard") -> Any:
        """
        构建感知引擎

        Args:
            engine_type: 引擎类型

        Returns:
            配置好的感知引擎实例
        """
        # 创建引擎
        engine = PerceptionEngineFactory.create_engine(self.agent_id, engine_type, self.config)

        # 初始化引擎
        await engine.initialize()

        # 添加处理器
        for input_type, config in self._processors:
            processor = ProcessorFactory.create_processor(input_type, config)
            await processor.initialize()
            # 注册到引擎(需要引擎支持)

        # 应用中间件和扩展
        for middleware in self._middleware:
            if hasattr(middleware, "apply_to"):
                middleware.apply_to(engine)

        for extension in self._extensions:
            if hasattr(extension, "extend"):
                extension.extend(engine)

        logger.info(f"构建完成: {engine_type} 引擎 for {self.agent_id}")
        return engine


# =============================================================================
# 便捷函数
# =============================================================================


async def create_perception_engine(
    agent_id: str,
    engine_type: str = "standard",
    config: PerceptionConfig | Optional[dict[str, Any] = None,
) -> Any:
    """
    创建并初始化感知引擎(便捷函数)

    Args:
        agent_id: 智能体ID
        engine_type: 引擎类型
        config: 配置对象或字典

    Returns:
        初始化完成的感知引擎实例
    """
    engine = PerceptionEngineFactory.create_engine(agent_id, engine_type, config)
    await engine.initialize()
    return engine


def create_text_processor(config: dict | None = None) -> Any:
    """创建文本处理器(便捷函数)"""
    return ProcessorFactory.create_processor(InputType.TEXT, config)


def create_image_processor(config: dict | None = None) -> Any:
    """创建图像处理器(便捷函数)"""
    return ProcessorFactory.create_processor(InputType.IMAGE, config)


def create_audio_processor(config: dict | None = None) -> Any:
    """创建音频处理器(便捷函数)"""
    return ProcessorFactory.create_processor(InputType.AUDIO, config)


def create_video_processor(config: dict | None = None) -> Any:
    """创建视频处理器(便捷函数)"""
    return ProcessorFactory.create_processor(InputType.VIDEO, config)


def create_multimodal_processor(config: dict | None = None) -> Any:
    """创建多模态处理器(便捷函数)"""
    return ProcessorFactory.create_processor(InputType.MULTIMODAL, config)


# =============================================================================
# 导出
# =============================================================================

__all__ = [
    "PerceptionBuilder",
    "PerceptionEngineFactory",
    "ProcessorFactory",
    "StreamProcessorFactory",
    "create_audio_processor",
    "create_image_processor",
    "create_multimodal_processor",
    "create_perception_engine",
    "create_text_processor",
    "create_video_processor",
]
