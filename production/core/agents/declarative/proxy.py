from __future__ import annotations
"""
声明式 Agent 代理类

将 AgentDefinition 适配为 BaseAgent 子类，使声明式定义的 Agent
可以无缝接入现有的 AgentRegistry 和 AgentFactory 体系。

process() 通过 UnifiedLLMManager 调用 LLM，注入 system_prompt，
并支持带权限过滤的工具调用。

Author: Athena Team
"""

import logging
from datetime import datetime
from typing import Any

from core.agents.base import (
    AgentRequest,
    AgentResponse,
    AgentStatus,
    BaseAgent,
    HealthStatus,
)

from .models import AgentDefinition
from .permissions import ToolPermissionFilter

logger = logging.getLogger("agent.declarative.proxy")


class DeclarativeAgent(BaseAgent):
    """
    声明式 Agent 代理

    将 AgentDefinition 适配为 BaseAgent 子类。
    通过 .md 文件定义的 Agent 无需编写 Python 代码即可运行。

    使用方式：
    1. 直接从定义创建：
       agent = DeclarativeAgent.from_definition(definition)
    2. 通过工厂注册：
       AgentFactory.register_agent_class(
           DeclarativeAgent.from_definition(definition)
       )
    """

    def __init__(self, definition: AgentDefinition, config: dict[str, Any] | None = None):
        # BaseAgent.__init__() 通过 self.name 访问 _agent_name，必须先设置
        self._agent_name = definition.name
        super().__init__(config)
        # BaseAgent.__init__() 会设置 self._definition = None，因此须在 super() 之后赋值
        self._definition = definition
        # 创建权限过滤器
        self._permission_filter = ToolPermissionFilter.from_definition(definition)
        # LLM 管理器延迟初始化
        self._llm_manager = None

    async def _get_llm_manager(self):
        """
        获取 UnifiedLLMManager 实例（延迟初始化）

        Returns:
            UnifiedLLMManager 实例，如果不可用则返回 None
        """
        if self._llm_manager is not None:
            return self._llm_manager

        try:
            from core.llm.unified_llm_manager import UnifiedLLMManager
            self._llm_manager = UnifiedLLMManager()
            await self._llm_manager.initialize()
            return self._llm_manager
        except ImportError:
            self.logger.warning("UnifiedLLMManager 不可用，声明式 Agent 将无法调用 LLM")
            return None
        except Exception as e:
            self.logger.error(f"初始化 LLM 管理器失败: {e}")
            return None

    @classmethod
    def from_definition(cls, definition: AgentDefinition) -> type[DeclarativeAgent]:
        """
        根据定义创建一个 DeclarativeAgent 子类

        这个方法返回一个类（而非实例），以便注册到 AgentFactory。
        AgentFactory.register_agent_class() 需要的是类而非实例。

        Args:
            definition: Agent 定义

        Returns:
            DeclarativeAgent 的子类
        """
        # 使用闭包捕获 definition
        class _DeclarativeAgentImpl(DeclarativeAgent):
            _class_definition = definition

            def __init__(self, config: dict[str, Any] | None = None):
                super().__init__(self._class_definition, config)

        _DeclarativeAgentImpl.__name__ = f"Declarative_{definition.name}"
        _DeclarativeAgentImpl.__qualname__ = f"Declarative_{definition.name}"
        return _DeclarativeAgentImpl

    @property
    def name(self) -> str:
        """Agent 名称"""
        return self._agent_name

    async def initialize(self) -> None:
        """初始化 Agent"""
        # 预初始化 LLM 管理器（非阻塞失败）
        llm = await self._get_llm_manager()
        if llm is None:
            self.logger.warning(
                f"声明式 Agent {self._agent_name} 初始化时 LLM 不可用，"
                "将在 process() 时重试"
            )

        self._status = AgentStatus.READY
        self.logger.info(
            f"声明式 Agent 已初始化: {self._agent_name} "
            f"(model={self._definition.model}, "
            f"readonly={self._definition.is_readonly}, "
            f"llm={'available' if llm else 'unavailable'})"
        )

    async def process(self, request: AgentRequest) -> AgentResponse:
        """
        处理请求：调用 LLM 生成响应

        1. 从 request.parameters 提取用户消息
        2. 使用 definition.system_prompt 作为系统提示词
        3. 通过 UnifiedLLMManager 调用 LLM
        4. 返回 LLM 响应

        如果 LLM 不可用，回退到基于规则的静态响应。
        """
        start_time = datetime.now()
        self.logger.info(f"处理请求: action={request.action}")

        # 提取用户消息
        user_message = request.parameters.get("message", "") or request.parameters.get("query", "")
        if not user_message:
            # 尝试从 action 或 context 中获取
            user_message = request.action or ""
            context_msg = request.context.get("message", "")
            if context_msg:
                user_message = context_msg

        if not user_message:
            return AgentResponse.error_response(
                request_id=request.request_id,
                error="请求中未包含有效的消息内容（需要 message 或 query 参数）",
            )

        # 获取 LLM 管理器
        llm = await self._get_llm_manager()

        if llm is None:
            # LLM 不可用时的回退：返回系统提示词 + 用户消息的上下文
            return AgentResponse.success_response(
                request_id=request.request_id,
                data={
                    "status": "fallback",
                    "agent": self._agent_name,
                    "message": f"LLM 服务不可用，无法处理请求。Agent: {self._agent_name}",
                    "system_prompt_available": bool(self._definition.system_prompt),
                    "model_requested": self._definition.model,
                },
            )

        # 构建 LLM 调用上下文
        llm_context = {
            "system_prompt": self._definition.system_prompt,
            "agent_name": self._agent_name,
            "action": request.action,
            "permission_mode": self._definition.permission_mode.value,
        }
        # 合并请求上下文
        if request.context:
            llm_context.update(request.context)

        # 确定模型偏好
        preferred_model = None
        model_setting = self._definition.model
        if model_setting and model_setting != "default":
            preferred_model = model_setting

        try:
            # 调用 LLM
            response = await llm.generate(
                message=user_message,
                task_type=request.action or "general",
                context=llm_context,
                temperature=request.parameters.get("temperature", 0.7),
                max_tokens=request.parameters.get("max_tokens", 4000),
                preferred_model=preferred_model,
            )

            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)

            return AgentResponse.success_response(
                request_id=request.request_id,
                data={
                    "status": "completed",
                    "agent": self._agent_name,
                    "content": response.content,
                    "model_used": response.model_used,
                    "tokens_used": response.tokens_used,
                    "processing_time_ms": processing_time,
                    "from_cache": response.from_cache,
                },
            )

        except Exception as e:
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            self.logger.error(f"LLM 调用失败: {e}", exc_info=True)
            return AgentResponse.error_response(
                request_id=request.request_id,
                error=f"LLM 调用失败: {e}",
            )

    async def shutdown(self) -> None:
        """关闭 Agent，释放 LLM 资源"""
        self._llm_manager = None
        self._status = AgentStatus.SHUTDOWN
        self.logger.info(f"声明式 Agent 已关闭: {self._agent_name}")

    async def health_check(self) -> HealthStatus:
        """健康检查"""
        llm_available = self._llm_manager is not None
        return HealthStatus(
            status=self._status,
            message=f"声明式 Agent {self._agent_name}: {self._status.value}",
            details={
                "model": self._definition.model,
                "readonly": self._definition.is_readonly,
                "source": self._definition.source.value,
                "llm_available": llm_available,
            }
        )

    def _get_permission_filter(self) -> ToolPermissionFilter | None:
        """获取权限过滤器"""
        return self._permission_filter

    async def call_tool(
        self,
        tool_id: str,
        parameters: dict[str, Any],
        context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        带权限检查的工具调用

        权限检查统一在 BaseAgent.call_tool() 中通过 _get_permission_filter() 执行，
        此处直接委托给父类。
        """
        return await super().call_tool(tool_id, parameters, context)
