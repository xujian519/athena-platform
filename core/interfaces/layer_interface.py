#!/usr/bin/env python3
from __future__ import annotations
"""
层次接口标准
Layer Interface Standard

定义Athena平台各层次之间的标准通信接口:
- 第4层:决策协调层(总体设计部)
- 第3层:应用服务层(智能体)
- 第2层:业务服务层(服务)
- 第1层:基础设施层(数据库/缓存)

作者: 小诺·双鱼公主
创建时间: 2025-12-27
版本: v1.0.0 "接口标准"
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class LayerType(Enum):
    """层次类型"""

    DECISION = "decision"  # 第4层:决策协调层
    APPLICATION = "application"  # 第3层:应用服务层
    SERVICE = "service"  # 第2层:业务服务层
    INFRASTRUCTURE = "infrastructure"  # 第1层:基础设施层


class RequestStatus(Enum):
    """请求状态"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class LayerRequest:
    """层间请求"""

    request_id: str
    from_layer: LayerType
    to_layer: LayerType
    action: str
    payload: dict[str, Any]
    priority: int = 5  # 1-10, 10最高
    requires_response: bool = True
    metadata: Optional[dict[str, Any]] = None


@dataclass
class LayerResponse:
    """层间响应"""

    request_id: str
    from_layer: LayerType
    status: RequestStatus
    payload: dict[str, Any]
    error: Optional[str] = None
    processing_time_ms: float = 0
    metadata: Optional[dict[str, Any]] = None


@dataclass
class FeedbackData:
    """反馈数据"""

    from_layer: LayerType
    feedback_type: str  # "quality", "performance", "error", "suggestion"
    content: str
    metrics: Optional[dict[str, Any]] = None
    timestamp: str = None


class LayerInterface(ABC):
    """
    层次接口抽象类
    所有层次必须实现此接口
    """

    @abstractmethod
    async def receive_request(self, request: LayerRequest) -> LayerResponse:
        """
        接收来自上层的请求
        """
        pass

    @abstractmethod
    async def send_request(self, request: LayerRequest) -> LayerResponse:
        """
        向下层发送请求
        """
        pass

    @abstractmethod
    async def receive_feedback(self, feedback: FeedbackData):
        """
        接收反馈
        """
        pass

    @abstractmethod
    def get_health_status(self) -> dict[str, Any]:
        """
        获取健康状态
        """
        pass


class LayerInterfaceRegistry:
    """
    层次接口注册中心
    管理所有层次的接口实现
    """

    def __init__(self):
        """初始化注册中心"""
        self.interfaces: dict[LayerType, LayerInterface] = {}
        logger.info("🔗 层次接口注册中心初始化完成")

    def register(self, layer_type: LayerType, interface: LayerInterface) -> Any:
        """注册层次接口"""
        self.interfaces[layer_type] = interface
        logger.info(f"   ✅ 注册层次: {layer_type.value}")

    def get_interface(self, layer_type: LayerType) -> LayerInterface | None:
        """获取层次接口"""
        return self.interfaces.get(layer_type)

    async def send_down(self, request: LayerRequest) -> LayerResponse:
        """
        向下层发送请求
        """
        target_layer = request.to_layer

        interface = self.get_interface(target_layer)
        if not interface:
            return LayerResponse(
                request_id=request.request_id,
                from_layer=target_layer,
                status=RequestStatus.FAILED,
                payload={},
                error=f"目标层次 {target_layer.value} 未注册接口",
            )

        return await interface.receive_request(request)

    async def send_up(self, feedback: FeedbackData):
        """
        向上层发送反馈
        """
        # 简化实现:直接记录日志
        logger.info(f"📤 向上层发送反馈: {feedback.feedback_type}")
        logger.info(f"   来自: {feedback.from_layer.value}")
        logger.info(f"   内容: {feedback.content[:100]}...")


class DecisionLayerInterface(LayerInterface):
    """
    第4层:决策协调层接口

    职责:
    - 接收爸爸的任务请求
    - 做出综合决策
    - 向应用层下达指令
    """

    def __init__(self, registry: LayerInterfaceRegistry):
        self.registry = registry
        self.layer_type = LayerType.DECISION

    async def receive_request(self, request: LayerRequest) -> LayerResponse:
        """接收来自爸爸的请求"""
        logger.info(f"🏛️ 决策层接收请求: {request.action}")

        # 使用综合决策引擎处理

        # 这里简化处理,实际应该调用决策引擎
        return LayerResponse(
            request_id=request.request_id,
            from_layer=self.layer_type,
            status=RequestStatus.COMPLETED,
            payload={"decision": "决策结果"},
            processing_time_ms=100,
        )

    async def send_request(self, request: LayerRequest) -> LayerResponse:
        """决策层不向下层发送请求(只向下发指令)"""
        return await self.registry.send_down(request)

    async def receive_feedback(self, feedback: FeedbackData):
        """接收反馈"""
        logger.info(f"🏛️ 决策层接收反馈: {feedback.feedback_type}")

    def get_health_status(self) -> dict[str, Any]:
        """获取健康状态"""
        return {"layer": "decision", "status": "healthy", "active_decisions": 0}


class ApplicationLayerInterface(LayerInterface):
    """
    第3层:应用服务层接口

    职责:
    - 接收决策层的指令
    - 协调智能体工作
    - 向服务层请求支持
    """

    def __init__(self, registry: LayerInterfaceRegistry):
        self.registry = registry
        self.layer_type = LayerType.APPLICATION

    async def receive_request(self, request: LayerRequest) -> LayerResponse:
        """接收来自决策层的指令"""
        logger.info(f"🤖 应用层接收请求: {request.action}")

        # 协调智能体执行任务
        return LayerResponse(
            request_id=request.request_id,
            from_layer=self.layer_type,
            status=RequestStatus.COMPLETED,
            payload={"result": "执行结果"},
            processing_time_ms=150,
        )

    async def send_request(self, request: LayerRequest) -> LayerResponse:
        """向服务层发送请求"""
        return await self.registry.send_down(request)

    async def receive_feedback(self, feedback: FeedbackData):
        """接收反馈"""
        logger.info(f"🤖 应用层接收反馈: {feedback.feedback_type}")

    def get_health_status(self) -> dict[str, Any]:
        """获取健康状态"""
        return {"layer": "application", "status": "healthy", "active_agents": 4}


class ServiceLayerInterface(LayerInterface):
    """
    第2层:业务服务层接口

    职责:
    - 接收应用层的请求
    - 执行具体业务逻辑
    - 向基础设施层请求数据
    """

    def __init__(self, registry: LayerInterfaceRegistry):
        self.registry = registry
        self.layer_type = LayerType.SERVICE

    async def receive_request(self, request: LayerRequest) -> LayerResponse:
        """接收来自应用层的请求"""
        logger.info(f"⚙️ 服务层接收请求: {request.action}")

        # 执行业务逻辑
        return LayerResponse(
            request_id=request.request_id,
            from_layer=self.layer_type,
            status=RequestStatus.COMPLETED,
            payload={"data": "业务数据"},
            processing_time_ms=200,
        )

    async def send_request(self, request: LayerRequest) -> LayerResponse:
        """向基础设施层发送请求"""
        return await self.registry.send_down(request)

    async def receive_feedback(self, feedback: FeedbackData):
        """接收反馈"""
        logger.info(f"⚙️ 服务层接收反馈: {feedback.feedback_type}")

    def get_health_status(self) -> dict[str, Any]:
        """获取健康状态"""
        return {"layer": "service", "status": "healthy", "active_services": 10}


class InfrastructureLayerInterface(LayerInterface):
    """
    第1层:基础设施层接口

    职责:
    - 接收服务层的数据请求
    - 提供数据库、缓存等服务
    - 不再向下层发送请求
    """

    def __init__(self, registry: LayerInterfaceRegistry):
        self.registry = registry
        self.layer_type = LayerType.INFRASTRUCTURE

    async def receive_request(self, request: LayerRequest) -> LayerResponse:
        """接收来自服务层的请求"""
        logger.info(f"🗄️ 基础设施层接收请求: {request.action}")

        # 提供数据服务
        return LayerResponse(
            request_id=request.request_id,
            from_layer=self.layer_type,
            status=RequestStatus.COMPLETED,
            payload={"data": "存储的数据"},
            processing_time_ms=50,
        )

    async def send_request(self, request: LayerRequest) -> LayerResponse:
        """基础设施层不向下发送请求"""
        return LayerResponse(
            request_id=request.request_id,
            from_layer=self.layer_type,
            status=RequestStatus.FAILED,
            payload={},
            error="基础设施层是最底层,无法向下发送请求",
        )

    async def receive_feedback(self, feedback: FeedbackData):
        """接收反馈"""
        logger.info(f"🗄️ 基础设施层接收反馈: {feedback.feedback_type}")

    def get_health_status(self) -> dict[str, Any]:
        """获取健康状态"""
        return {
            "layer": "infrastructure",
            "status": "healthy",
            "databases": ["PostgreSQL", "Redis", "Qdrant", "Elasticsearch"],
        }


def initialize_layer_system() -> LayerInterfaceRegistry:
    """
    初始化层次系统

    创建所有层次接口并注册到注册中心
    """
    registry = LayerInterfaceRegistry()

    # 创建各层接口
    decision_layer = DecisionLayerInterface(registry)
    application_layer = ApplicationLayerInterface(registry)
    service_layer = ServiceLayerInterface(registry)
    infrastructure_layer = InfrastructureLayerInterface(registry)

    # 注册接口
    registry.register(LayerType.DECISION, decision_layer)
    registry.register(LayerType.APPLICATION, application_layer)
    registry.register(LayerType.SERVICE, service_layer)
    registry.register(LayerType.INFRASTRUCTURE, infrastructure_layer)

    logger.info("✅ 层次系统初始化完成")
    logger.info("   决策层 → 应用层 → 服务层 → 基础设施层")

    return registry


# 全局实例
_registry: LayerInterfaceRegistry = None


def get_layer_registry() -> LayerInterfaceRegistry:
    """获取层次注册中心单例"""
    global _registry
    if _registry is None:
        _registry = initialize_layer_system()
    return _registry


if __name__ == "__main__":
    import asyncio

    async def test():
        """测试层次接口"""
        print("🧪 测试层次接口标准")
        print("=" * 70)

        # 初始化层次系统
        registry = get_layer_registry()

        # 测试1:决策层向应用层发送请求
        print("\n📋 测试1: 决策层 → 应用层")
        request1 = LayerRequest(
            request_id="test_001",
            from_layer=LayerType.DECISION,
            to_layer=LayerType.APPLICATION,
            action="协调智能体",
            payload={"task": "专利分析"},
        )

        response1 = await registry.send_down(request1)
        print(f"响应状态: {response1.status.value}")
        print(f"处理时间: {response1.processing_time_ms}ms")

        # 测试2:应用层向服务层发送请求
        print("\n📋 测试2: 应用层 → 服务层")
        request2 = LayerRequest(
            request_id="test_002",
            from_layer=LayerType.APPLICATION,
            to_layer=LayerType.SERVICE,
            action="查询专利数据",
            payload={"patent_id": "12345"},
        )

        response2 = await registry.send_down(request2)
        print(f"响应状态: {response2.status.value}")
        print(f"处理时间: {response2.processing_time_ms}ms")

        # 测试3:服务层向基础设施层发送请求
        print("\n📋 测试3: 服务层 → 基础设施层")
        request3 = LayerRequest(
            request_id="test_003",
            from_layer=LayerType.SERVICE,
            to_layer=LayerType.INFRASTRUCTURE,
            action="查询数据库",
            payload={"query": "SELECT * FROM patents"},
        )

        response3 = await registry.send_down(request3)
        print(f"响应状态: {response3.status.value}")
        print(f"处理时间: {response3.processing_time_ms}ms")

        # 测试4:查看各层健康状态
        print("\n📊 测试4: 各层健康状态")
        for layer_type in [
            LayerType.DECISION,
            LayerType.APPLICATION,
            LayerType.SERVICE,
            LayerType.INFRASTRUCTURE,
        ]:
            interface = registry.get_interface(layer_type)
            if interface:
                health = interface.get_health_status()
                print(f"   {layer_type.value}: {health}")

    asyncio.run(test())
