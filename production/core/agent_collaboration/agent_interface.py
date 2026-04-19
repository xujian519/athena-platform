#!/usr/bin/env python3
"""
智能体标准化接口协议
Agent Standard Interface Protocol

定义所有智能体的标准化通信接口,实现松耦合架构

作者: Athena平台团队
版本: v1.0.0
创建: 2025-01-12
"""

from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """智能体状态"""

    OFFLINE = "offline"  # 离线
    STARTING = "starting"  # 启动中
    ONLINE = "online"  # 在线
    BUSY = "busy"  # 忙碌
    ERROR = "error"  # 错误
    MAINTENANCE = "maintenance"  # 维护中


class MessageType(Enum):
    """消息类型"""

    CHAT = "chat"  # 聊天
    TASK = "task"  # 任务执行
    QUERY = "query"  # 查询
    NOTIFICATION = "notification"  # 通知
    HEALTH_CHECK = "health_check"  # 健康检查


@dataclass
class AgentMessage:
    """标准化消息格式"""

    message_id: str
    message_type: MessageType
    sender: str  # 发送者ID
    receiver: str  # 接收者ID
    content: str  # 消息内容
    context: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    reply_to: str | None = None  # 回复的消息ID


@dataclass
class AgentResponse:
    """标准化响应格式"""

    message_id: str  # 原消息ID
    success: bool  # 是否成功
    content: str  # 响应内容
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None  # 错误信息
    agent_status: AgentStatus = AgentStatus.ONLINE
    processing_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AgentInfo:
    """智能体信息"""

    agent_id: str  # 智能体ID
    name: str  # 智能体名称
    full_name: str  # 全名
    role: str  # 角色
    description: str  # 描述
    version: str  # 版本号
    capabilities: list[str]  # 能力列表
    endpoint: str | None = None  # API端点
    port: int | None = None  # 端口号
    protocol: str = "http"  # 协议类型
    status: AgentStatus = AgentStatus.OFFLINE
    last_health_check: datetime | None = None


class IAgent(ABC):
    """智能体标准化接口

    所有智能体都必须实现此接口以确保互操作性
    """

    @abstractmethod
    async def process_message(self, message: AgentMessage) -> AgentResponse:
        """处理消息

        Args:
            message: 标准化消息

        Returns:
            标准化响应
        """
        pass

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """健康检查

        Returns:
            健康状态信息
        """
        pass

    @abstractmethod
    async def get_capabilities(self) -> list[str]:
        """获取能力列表

        Returns:
            能力列表
        """
        pass

    @abstractmethod
    async def get_agent_info(self) -> AgentInfo:
        """获取智能体信息

        Returns:
            智能体信息
        """
        pass


class AgentClient:
    """智能体客户端 - 用于调用其他智能体"""

    def __init__(self, agent_info: AgentInfo):
        """初始化客户端

        Args:
            agent_info: 智能体信息
        """
        self.agent_info = agent_info
        self.timeout = 30.0  # 默认超时

    async def send_message(
        self, content: str, context: dict[str, Any] | None = None
    ) -> AgentResponse:
        """发送消息到智能体

        Args:
            content: 消息内容
            context: 上下文信息

        Returns:
            响应
        """
        import httpx

        # 构建标准化消息
        message = AgentMessage(
            message_id=f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            message_type=MessageType.CHAT,
            sender="xiaonuo",
            receiver=self.agent_info.agent_id,
            content=content,
            context=context or {},
        )

        try:
            # 使用HTTP API调用
            endpoint = f"{self.agent_info.protocol}://localhost:{self.agent_info.port}/chat"

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    endpoint, json={"message": content, "context": context or {}}
                )
                response.raise_for_status()
                data = response.json()

                # 转换为标准化响应
                return AgentResponse(
                    message_id=message.message_id,
                    success=data.get("success", True),
                    content=data.get("response", ""),
                    data=data.get("data", {}),
                    processing_time=data.get("processing_time", 0.0),
                )

        except Exception as e:
            logger.error(f"❌ 调用智能体 {self.agent_info.agent_id} 失败: {e}")
            return AgentResponse(
                message_id=message.message_id,
                success=False,
                content=f"调用失败: {e!s}",
                error=str(e),
                agent_status=AgentStatus.ERROR,
            )

    async def check_health(self) -> bool:
        """检查智能体健康状态

        Returns:
            是否健康
        """
        import httpx

        try:
            endpoint = f"{self.agent_info.protocol}://localhost:{self.agent_info.port}/health"

            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(endpoint)
                response.raise_for_status()
                data = response.json()
                return data.get("status") == "healthy"

        except Exception as e:
            logger.warning(f"⚠️ 智能体 {self.agent_info.agent_id} 健康检查失败: {e}")
            return False


class AgentRegistry:
    """智能体注册中心"""

    def __init__(self):
        """初始化注册中心"""
        self.agents: dict[str, AgentInfo] = {}
        self.clients: dict[str, AgentClient] = {}

    def register(self, agent_info: AgentInfo) -> Any:
        """注册智能体

        Args:
            agent_info: 智能体信息
        """
        self.agents[agent_info.agent_id] = agent_info
        self.clients[agent_info.agent_id] = AgentClient(agent_info)
        logger.info(f"✅ 注册智能体: {agent_info.name} ({agent_info.agent_id})")

    def unregister(self, agent_id: str) -> Any:
        """注销智能体

        Args:
            agent_id: 智能体ID
        """
        if agent_id in self.agents:
            del self.agents[agent_id]
            if agent_id in self.clients:
                del self.clients[agent_id]
            logger.info(f"❌ 注销智能体: {agent_id}")

    def get_agent(self, agent_id: str) -> AgentInfo | None:
        """获取智能体信息

        Args:
            agent_id: 智能体ID

        Returns:
            智能体信息,如果不存在返回None
        """
        return self.agents.get(agent_id)

    def get_client(self, agent_id: str) -> AgentClient | None:
        """获取智能体客户端

        Args:
            agent_id: 智能体ID

        Returns:
            智能体客户端,如果不存在返回None
        """
        return self.clients.get(agent_id)

    def list_agents(self) -> list[AgentInfo]:
        """列出所有智能体

        Returns:
            智能体信息列表
        """
        return list(self.agents.values())

    def get_agents_by_capability(self, capability: str) -> list[AgentInfo]:
        """根据能力获取智能体

        Args:
            capability: 能力名称

        Returns:
            具有该能力的智能体列表
        """
        return [agent for agent in self.agents.values() if capability in agent.capabilities]


# 全局注册中心
_agent_registry: AgentRegistry | None = None


def get_agent_registry() -> AgentRegistry:
    """获取全局智能体注册中心

    Returns:
        智能体注册中心
    """
    global _agent_registry
    if _agent_registry is None:
        _agent_registry = AgentRegistry()
    return _agent_registry
