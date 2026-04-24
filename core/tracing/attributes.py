"""
OpenTelemetry标准化属性定义

定义Athena平台使用的标准化追踪属性，遵循OpenTelemetry语义约定。
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from enum import Enum


class SpanKind(Enum):
    """Span类型枚举"""
    SERVER = "SERVER"       # 服务端处理请求
    CLIENT = "CLIENT"       # 客户端发送请求
    PRODUCER = "PRODUCER"   # 生产者发送消息
    CONSUMER = "CONSUMER"   # 消费者处理消息
    INTERNAL = "INTERNAL"   # 内部操作


# ========== 通用属性 ==========

class CommonAttributes:
    """通用属性"""

    SERVICE_NAME = "service.name"
    SERVICE_VERSION = "service.version"
    DEPLOYMENT_ENVIRONMENT = "deployment.environment"
    HOST_NAME = "host.name"
    PROCESS_ID = "process.id"
    THREAD_ID = "thread.id"


# ========== Agent相关属性 ==========

@dataclass
class AgentAttributes:
    """
    Agent处理Span属性

    遵循OpenTelemetry AI Agent工作组的语义约定草案。
    """

    AGENT_NAME = "agent.name"
    AGENT_ROLE = "agent.role"
    AGENT_TYPE = "agent.type"
    AGENT_TASK_TYPE = "agent.task_type"
    AGENT_REQUEST_ID = "agent.request_id"
    AGENT_SESSION_ID = "agent.session_id"
    AGENT_USER_ID = "agent.user_id"
    AGENT_TOOL_COUNT = "agent.tool_count"
    AGENT_STEP_COUNT = "agent.step_count"

    @staticmethod
    def create(
        agent_name: str,
        task_type: str,
        agent_role: Optional[str] = None,
        agent_type: str = "unified",
        request_id: Optional[str] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        创建Agent属性字典

        Args:
            agent_name: Agent名称（如xiaona, xiaonuo, yunxi）
            task_type: 任务类型（如patent_analysis, patent_search）
            agent_role: Agent角色（如legal_expert, coordinator）
            agent_type: Agent类型（unified, specialized, legacy）
            request_id: 请求ID
            session_id: 会话ID
            user_id: 用户ID

        Returns:
            标准化的属性字典
        """
        attributes = {
            AgentAttributes.AGENT_NAME: agent_name,
            AgentAttributes.AGENT_TASK_TYPE: task_type,
            AgentAttributes.AGENT_TYPE: agent_type,
        }

        if agent_role:
            attributes[AgentAttributes.AGENT_ROLE] = agent_role
        if request_id:
            attributes[AgentAttributes.AGENT_REQUEST_ID] = request_id
        if session_id:
            attributes[AgentAttributes.AGENT_SESSION_ID] = session_id
        if user_id:
            attributes[AgentAttributes.AGENT_USER_ID] = user_id

        # 添加额外属性
        attributes.update(kwargs)

        return attributes


# ========== LLM相关属性 ==========

@dataclass
class LLMAttributes:
    """
    LLM调用Span属性

    遵循OpenTelemetry AI LLM工作组的语义约定草案。
    """

    LLM_PROVIDER = "llm.provider"
    LLM_MODEL_NAME = "llm.model.name"
    LLM_REQUEST_TYPE = "llm.request.type"
    LLM_RESPONSE_TYPE = "llm.response.type"
    LLM_TOKEN_COUNT_TOTAL = "llm.token.count.total"
    LLM_TOKEN_COUNT_PROMPT = "llm.token.count.prompt"
    LLM_TOKEN_COUNT_COMPLETION = "llm.token.count.completion"
    LLM_FINISH_REASON = "llm.finish_reason"
    LLM_TEMPERATURE = "llm.temperature"
    LLM_MAX_TOKENS = "llm.max_tokens"

    @staticmethod
    def create(
        provider: str,
        model: str,
        request_type: str = "chat",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        创建LLM属性字典

        Args:
            provider: 提供商（如claude, gpt4, deepseek, glm）
            model: 模型名称（如claude-3-opus, gpt-4）
            request_type: 请求类型（chat, completion, embedding）
            temperature: 温度参数
            max_tokens: 最大token数

        Returns:
            标准化的属性字典
        """
        attributes = {
            LLMAttributes.LLM_PROVIDER: provider,
            LLMAttributes.LLM_MODEL_NAME: model,
            LLMAttributes.LLM_REQUEST_TYPE: request_type,
        }

        if temperature is not None:
            attributes[LLMAttributes.LLM_TEMPERATURE] = temperature
        if max_tokens is not None:
            attributes[LLMAttributes.LLM_MAX_TOKENS] = max_tokens

        attributes.update(kwargs)

        return attributes

    @staticmethod
    def add_response(
        attributes: Dict[str, Any],
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        finish_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """添加LLM响应属性"""
        result = attributes.copy()
        result[LLMAttributes.LLM_TOKEN_COUNT_PROMPT] = prompt_tokens
        result[LLMAttributes.LLM_TOKEN_COUNT_COMPLETION] = completion_tokens
        result[LLMAttributes.LLM_TOKEN_COUNT_TOTAL] = total_tokens
        if finish_reason:
            result[LLMAttributes.LLM_FINISH_REASON] = finish_reason
        return result


# ========== 数据库相关属性 ==========

@dataclass
class DatabaseAttributes:
    """数据库操作属性"""

    DB_SYSTEM = "db.system"
    DB_NAME = "db.name"
    DB_STATEMENT = "db.statement"
    DB_OPERATION = "db.operation"
    DB_TABLE = "db.sql.table"

    @staticmethod
    def create(
        db_system: str,
        db_name: str,
        operation: str,
        table: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """创建数据库属性字典"""
        attributes = {
            DatabaseAttributes.DB_SYSTEM: db_system,
            DatabaseAttributes.DB_NAME: db_name,
            DatabaseAttributes.DB_OPERATION: operation,
        }

        if table:
            attributes[DatabaseAttributes.DB_TABLE] = table

        attributes.update(kwargs)
        return attributes


# ========== HTTP相关属性 ==========

@dataclass
class HTTPAttributes:
    """HTTP请求属性"""

    HTTP_METHOD = "http.method"
    HTTP_URL = "http.url"
    HTTP_STATUS_CODE = "http.status_code"
    HTTP_ROUTE = "http.route"

    @staticmethod
    def create(
        method: str,
        url: str,
        status_code: Optional[int] = None,
        route: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """创建HTTP属性字典"""
        attributes = {
            HTTPAttributes.HTTP_METHOD: method,
            HTTPAttributes.HTTP_URL: url,
        }

        if status_code:
            attributes[HTTPAttributes.HTTP_STATUS_CODE] = status_code
        if route:
            attributes[HTTPAttributes.HTTP_ROUTE] = route

        attributes.update(kwargs)
        return attributes


# ========== 工具调用相关属性 ==========

@dataclass
class ToolAttributes:
    """工具调用属性"""

    TOOL_NAME = "tool.name"
    TOOL_CATEGORY = "tool.category"
    TOOL_STATUS = "tool.status"
    TOOL_DURATION_MS = "tool.duration_ms"
    TOOL_ERROR_MESSAGE = "tool.error.message"

    @staticmethod
    def create(
        tool_name: str,
        category: str,
        status: str = "success",
        duration_ms: Optional[int] = None,
        error_message: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """创建工具调用属性字典"""
        attributes = {
            ToolAttributes.TOOL_NAME: tool_name,
            ToolAttributes.TOOL_CATEGORY: category,
            ToolAttributes.TOOL_STATUS: status,
        }

        if duration_ms:
            attributes[ToolAttributes.TOOL_DURATION_MS] = duration_ms
        if error_message:
            attributes[ToolAttributes.TOOL_ERROR_MESSAGE] = error_message

        attributes.update(kwargs)
        return attributes


# ========== 错误相关属性 ==========

@dataclass
class ErrorAttributes:
    """错误属性"""

    ERROR_TYPE = "error.type"
    ERROR_MESSAGE = "error.message"
    ERROR_STACKTRACE = "error.stacktrace"

    @staticmethod
    def create(
        error_type: str,
        message: str,
        stacktrace: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """创建错误属性字典"""
        attributes = {
            ErrorAttributes.ERROR_TYPE: error_type,
            ErrorAttributes.ERROR_MESSAGE: message,
        }

        if stacktrace:
            attributes[ErrorAttributes.ERROR_STACKTRACE] = stacktrace

        attributes.update(kwargs)
        return attributes
