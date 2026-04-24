"""
适配器实现 - 向后兼容传统Agent

提供适配器类，将传统Agent包装为统一接口。
支持传统架构（core.agents）的BaseAgent适配。

Author: Athena Team
Version: 1.0.0
Date: 2026-04-24
"""

import logging
from typing import Any, Optional

from .base import (
    AgentCapability,
    AgentMetadata,
    AgentRequest,
    AgentResponse,
    AgentStatus,
    HealthStatus,
    MessageConverter,
    ResponseMessage,
    SimpleAgentResponse,
    TaskMessage,
)
from .base_agent import UnifiedBaseAgent
from .config import UnifiedAgentConfig

logger = logging.getLogger(__name__)


# ============ 传统Agent适配器 ============


class LegacyAgentAdapter(UnifiedBaseAgent):
    """
    传统Agent适配器

    将传统BaseAgent（core.agents.base_agent.BaseAgent）包装为统一接口。
    自动处理消息格式转换，保持向后兼容性。

    Usage:
        ```python
        # 创建传统Agent
        legacy_agent = XiaonaLegalAgent()

        # 包装为统一接口
        config = UnifiedAgentConfig.create_minimal("xiaona-legal", "legal-expert")
        adapter = LegacyAgentAdapter(legacy_agent, config)

        # 使用统一接口
        await adapter.initialize()
        response = await adapter.process(AgentRequest(...))
        ```
    """

    def __init__(self, legacy_agent: Any, config: UnifiedAgentConfig):
        """
        初始化适配器

        Args:
            legacy_agent: 传统Agent实例
            config: 统一配置对象
        """
        # 使用适配器名称，但保留对原始Agent的引用
        self._legacy_agent = legacy_agent

        # 如果config名称与legacy_agent不匹配，使用legacy_agent的名称
        if config.name != legacy_agent.name:
            config = config.with_overrides(name=legacy_agent.name)

        super().__init__(config)

        # 适配器性能统计
        self._adapter_overhead = 0.0

    @property
    def name(self) -> str:
        """获取传统Agent名称"""
        return self._legacy_agent.name

    def _load_metadata(self) -> AgentMetadata:
        """加载元数据（从传统Agent）"""
        return AgentMetadata(
            name=self._legacy_agent.name,
            version="1.0.0",
            description=f"{self._legacy_agent.name} (适配器包装)",
            author="Athena Team",
            tags=["adapter", "legacy"]
        )

    def _register_capabilities(self) -> list[AgentCapability]:
        """从传统Agent获取能力"""
        capabilities = []
        if hasattr(self._legacy_agent, 'get_capabilities'):
            for cap in self._legacy_agent.get_capabilities():
                capabilities.append(AgentCapability(
                    name=cap,
                    description=f"能力: {cap}",
                    parameters={},
                    examples=[]
                ))
        return capabilities

    async def initialize(self) -> None:
        """初始化传统Agent"""
        import time
        start_time = time.time()

        try:
            # 调用传统Agent初始化（如果有）
            if hasattr(self._legacy_agent, 'initialize'):
                result = await self._legacy_agent.initialize()
                # 传统initialize可能返回bool或None

            # 尝试连接Gateway
            if self._gateway_enabled:
                await self.connect_gateway()

            # 初始化记忆系统
            if self._memory_enabled and self._config.project_path:
                try:
                    from core.memory.unified_memory_system import get_project_memory
                    self.memory_system = get_project_memory(self._config.project_path)
                    self.logger.info(f"记忆系统已启用 - 项目: {self._config.project_path}")
                except Exception as e:
                    self.logger.warning(f"记忆系统初始化失败: {e}")

            self._status = AgentStatus.READY

            # 记录性能
            init_time = time.time() - start_time
            self._adapter_overhead += init_time

            self.logger.info(f"传统Agent初始化完成: {self.name}")

        except Exception as e:
            self._status = AgentStatus.ERROR
            self.logger.error(f"传统Agent初始化失败: {e}")
            raise

    async def process(self, request: AgentRequest) -> AgentResponse:
        """
        使用新接口处理请求

        将AgentRequest转换为传统格式后调用传统Agent。

        Args:
            request: 新格式请求

        Returns:
            AgentResponse: 新格式响应
        """
        import time
        start_time = time.time()

        try:
            # 转换请求格式
            task_message = MessageConverter.request_to_task(request, self.name)

            # 调用传统Agent（如果支持process_task）
            if hasattr(self._legacy_agent, 'process_task'):
                response_msg = await self._legacy_agent.process_task(task_message)
                response = MessageConverter.task_response_to_response(response_msg)
            else:
                # 传统Agent使用简单的process方法
                result = self._legacy_agent.process(
                    str(request.parameters),
                    **(request.context or {})
                )
                # 包装为AgentResponse
                response = AgentResponse.success_response(
                    request_id=request.request_id,
                    data=result
                )

            # 记录性能
            process_time = time.time() - start_time
            self._adapter_overhead += process_time

            return response

        except Exception as e:
            self.logger.error(f"请求处理失败: {e}")
            return AgentResponse.error_response(
                request_id=request.request_id,
                error=str(e)
            )

    async def shutdown(self) -> None:
        """关闭传统Agent"""
        try:
            # 断开Gateway
            await self.disconnect_gateway()

            # 调用传统Agent关闭（如果有）
            if hasattr(self._legacy_agent, 'shutdown'):
                await self._legacy_agent.shutdown()

            self._status = AgentStatus.SHUTDOWN

            # 输出性能统计
            self.logger.info(f"适配器开销统计: {self._adapter_overhead:.2f}秒")

        except Exception as e:
            self.logger.error(f"关闭失败: {e}")

    async def health_check(self) -> HealthStatus:
        """健康检查"""
        try:
            # 检查传统Agent状态（如果有health_check方法）
            if hasattr(self._legacy_agent, 'health_check'):
                legacy_health = await self._legacy_agent.health_check()
                # 转换为统一格式
                return HealthStatus(
                    status=self._status,
                    message=f"适配器健康 - 传统Agent: {legacy_health}",
                    details={
                        "adapter_overhead": self._adapter_overhead,
                        "legacy_health": str(legacy_health)
                    }
                )

            # 简单健康检查
            is_healthy = self._status in [AgentStatus.READY, AgentStatus.BUSY]
            return HealthStatus(
                status=self._status,
                message="适配器健康" if is_healthy else "Agent未就绪",
                details={
                    "adapter_overhead": self._adapter_overhead,
                    "legacy_agent": str(self._legacy_agent)
                }
            )

        except Exception as e:
            return HealthStatus(
                status=AgentStatus.ERROR,
                message=f"健康检查失败: {e}"
            )


# ============ 简单Agent适配器 ============


class SimpleAgentAdapter(UnifiedBaseAgent):
    """
    简单Agent适配器

    用于包装极简Agent（只有process方法的简单类）。
    适用于快速原型和测试场景。

    Usage:
        ```python
        def simple_handler(input_text: str) -> str:
            return f"处理结果: {input_text}"

        config = UnifiedAgentConfig.create_minimal("simple", "processor")
        adapter = SimpleAgentAdapter(simple_handler, config)
        ```
    """

    def __init__(self, handler: Any, config: UnifiedAgentConfig):
        """
        初始化适配器

        Args:
            handler: 处理函数或对象
            config: 统一配置对象
        """
        self._handler = handler
        super().__init__(config)

    @property
    def name(self) -> str:
        return self._config.name

    async def initialize(self) -> None:
        """初始化（无操作）"""
        self._status = AgentStatus.READY

    async def process(self, request: AgentRequest) -> AgentResponse:
        """调用处理函数"""
        try:
            if callable(self._handler):
                result = self._handler(str(request.parameters))
            else:
                result = str(request.parameters)

            return AgentResponse.success_response(
                request_id=request.request_id,
                data=result
            )

        except Exception as e:
            return AgentResponse.error_response(
                request_id=request.request_id,
                error=str(e)
            )

    async def shutdown(self) -> None:
        """关闭（无操作）"""
        self._status = AgentStatus.SHUTDOWN

    async def health_check(self) -> HealthStatus:
        """健康检查"""
        return HealthStatus(
            status=self._status,
            message="简单适配器健康"
        )


# ============ 适配器工厂 ============


class AdapterFactory:
    """
    适配器工厂

    根据Agent类型自动选择合适的适配器。
    """

    @staticmethod
    def create_adapter(agent: Any, config: Optional[UnifiedAgentConfig] = None) -> UnifiedBaseAgent:
        """
        为Agent创建适配器

        Args:
            agent: 要包装的Agent
            config: 配置对象（可选，自动生成）

        Returns:
            适配后的UnifiedBaseAgent实例

        Raises:
            ValueError: 如果Agent类型不支持
        """
        # 如果已经是统一Agent，直接返回
        if isinstance(agent, UnifiedBaseAgent):
            return agent

        # 生成配置
        if config is None:
            agent_name = getattr(agent, 'name', 'adapted-agent')
            agent_role = getattr(agent, 'role', 'agent')
            config = UnifiedAgentConfig.create_minimal(agent_name, agent_role)

        # 检查是否是传统BaseAgent
        if hasattr(agent, 'process') and hasattr(agent, 'name'):
            # 可能是传统Agent
            if hasattr(agent, 'get_capabilities'):
                return LegacyAgentAdapter(agent, config)
            else:
                return SimpleAgentAdapter(agent, config)

        # 可调用对象
        if callable(agent):
            return SimpleAgentAdapter(agent, config)

        raise ValueError(f"不支持的Agent类型: {type(agent)}")

    @staticmethod
    def is_legacy_agent(agent: Any) -> bool:
        """
        判断是否是传统Agent

        Args:
            agent: 待检查的Agent

        Returns:
            是否是传统Agent
        """
        return (
            hasattr(agent, 'process')
            and hasattr(agent, 'name')
            and not isinstance(agent, UnifiedBaseAgent)
        )

    @staticmethod
    def is_unified_agent(agent: Any) -> bool:
        """
        判断是否是统一Agent

        Args:
            agent: 待检查的Agent

        Returns:
            是否是统一Agent
        """
        return isinstance(agent, UnifiedBaseAgent)


# ============ 导出 ============

__all__ = [
    "LegacyAgentAdapter",
    "SimpleAgentAdapter",
    "AdapterFactory",
]
