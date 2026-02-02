#!/usr/bin/env python3
"""
感知模块统一接口定义
Perception Module Unified Interface Definitions

定义感知引擎和处理器的标准接口,确保所有实现遵循相同的契约。

作者: Athena AI系统
创建时间: 2026-01-24
版本: 1.0.0
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

from .types import (
    InputType,
    PerceptionResult,
    ProcessingMode,
    StreamConfig,
)

# =============================================================================
# 基础处理器接口
# =============================================================================


class IProcessor(ABC):
    """
    基础处理器接口

    定义所有处理器必须实现的核心方法。
    """

    @abstractmethod
    async def initialize(self) -> bool:
        """
        初始化处理器

        Returns:
            初始化是否成功
        """
        pass

    @abstractmethod
    async def process(
        self,
        data: Any,
        input_type: InputType,
        mode: ProcessingMode = ProcessingMode.STANDARD,
        **kwargs: Any,
    ) -> PerceptionResult:
        """
        处理输入数据

        Args:
            data: 输入数据
            input_type: 输入类型
            mode: 处理模式
            **kwargs: 额外参数

        Returns:
            感知结果
        """
        pass

    @abstractmethod
    async def cleanup(self) -> bool:
        """
        清理处理器资源

        Returns:
            清理是否成功
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        健康检查

        Returns:
            处理器是否健康
        """
        pass

    def get_processor_info(self) -> dict[str, Any]:
        """
        获取处理器信息

        Returns:
            处理器信息字典
        """
        return {
            "processor_id": getattr(self, "processor_id", "unknown"),
            "initialized": getattr(self, "initialized", False),
            "supported_types": getattr(self, "supported_types", []),
            "config": getattr(self, "config", {}),
        }


# =============================================================================
# 流式处理器接口
# =============================================================================


class IStreamProcessor(IProcessor):
    """
    流式处理器接口

    扩展基础处理器接口,添加流式处理能力。
    """

    @abstractmethod
    async def stream_process(
        self,
        data_stream: AsyncIterator[Any],
        input_type: InputType,
        config: StreamConfig | None = None,
    ) -> AsyncIterator[PerceptionResult]:
        """
        流式处理数据

        Args:
            data_stream: 异步数据流
            input_type: 输入类型
            config: 流式配置

        Yields:
            感知结果
        """
        pass

    @abstractmethod
    async def process_batch(
        self, data_list: list[Any], input_type: InputType, **kwargs: Any
    ) -> list[PerceptionResult]:
        """
        批量处理数据

        Args:
            data_list: 数据列表
            input_type: 输入类型
            **kwargs: 额外参数

        Returns:
            感知结果列表
        """
        pass


# =============================================================================
# 感知引擎接口
# =============================================================================


class IPerceptionEngine(ABC):
    """
    感知引擎接口

    定义感知引擎的标准接口。
    """

    @abstractmethod
    async def initialize(self) -> bool:
        """
        初始化感知引擎

        Returns:
            初始化是否成功
        """
        pass

    @abstractmethod
    async def perceive(
        self,
        input_data: Any,
        input_type: InputType | None = None,
        mode: ProcessingMode = ProcessingMode.STANDARD,
        **kwargs: Any,
    ) -> PerceptionResult:
        """
        感知处理

        Args:
            input_data: 输入数据
            input_type: 输入类型(可选,自动检测)
            mode: 处理模式
            **kwargs: 额外参数

        Returns:
            感知结果
        """
        pass

    @abstractmethod
    async def stream_perceive(
        self, data_stream: AsyncIterator[Any], input_type: InputType | None = None, **kwargs: Any
    ) -> AsyncIterator[PerceptionResult]:
        """
        流式感知处理

        Args:
            data_stream: 异步数据流
            input_type: 输入类型(可选,自动检测)
            **kwargs: 额外参数

        Yields:
            感知结果
        """
        pass

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """
        健康检查

        Returns:
            健康状态信息
        """
        pass

    @abstractmethod
    async def shutdown(self) -> bool:
        """
        关闭感知引擎

        Returns:
            关闭是否成功
        """
        pass

    @abstractmethod
    def get_metrics(self) -> dict[str, Any]:
        """
        获取性能指标

        Returns:
            性能指标字典
        """
        pass

    @abstractmethod
    def get_status(self) -> dict[str, Any]:
        """
        获取引擎状态

        Returns:
            状态信息字典
        """
        pass


# =============================================================================
# 缓存接口
# =============================================================================


class ICache(ABC):
    """
    缓存接口

    定义缓存组件的标准接口。
    """

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """获取缓存值"""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """设置缓存值"""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        pass

    @abstractmethod
    async def clear(self) -> bool:
        """清空所有缓存"""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        pass

    @abstractmethod
    async def get_stats(self) -> dict[str, Any]:
        """获取缓存统计信息"""
        pass


# =============================================================================
# 监控接口
# =============================================================================


class IMonitor(ABC):
    """
    监控接口

    定义监控组件的标准接口。
    """

    @abstractmethod
    async def start_monitoring(self) -> None:
        """启动监控"""
        pass

    @abstractmethod
    async def stop_monitoring(self) -> None:
        """停止监控"""
        pass

    @abstractmethod
    def record_request(
        self, latency: float, success: bool, metadata: dict[str, Any] | None = None
    ) -> None:
        """记录请求"""
        pass

    @abstractmethod
    def get_metrics(self) -> dict[str, Any]:
        """获取监控指标"""
        pass

    @abstractmethod
    def get_performance_report(self) -> dict[str, Any]:
        """获取性能报告"""
        pass


# =============================================================================
# 工厂接口
# =============================================================================


class IProcessorFactory(ABC):
    """
    处理器工厂接口

    定义处理器创建的标准接口。
    """

    @abstractmethod
    def create_processor(
        self, processor_type: InputType, config: dict[str, Any] | None = None
    ) -> IProcessor:
        """
        创建处理器实例

        Args:
            processor_type: 处理器类型
            config: 配置参数

        Returns:
            处理器实例
        """
        pass

    @abstractmethod
    def register_processor(self, processor_type: InputType, processor_class: type) -> None:
        """注册处理器类"""
        pass

    @abstractmethod
    def get_supported_types(self) -> list[InputType]:
        """获取支持的处理器类型"""
        pass


# =============================================================================
# 导出
# =============================================================================

__all__ = [
    # 组件接口
    "ICache",
    "IMonitor",
    "IPerceptionEngine",
    # 基础接口
    "IProcessor",
    "IProcessorFactory",
    "IStreamProcessor",
]
