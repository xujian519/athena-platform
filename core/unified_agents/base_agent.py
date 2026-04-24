"""
统一Agent基类实现

整合两套架构的最佳实践，提供统一的Agent接口。
支持双接口模式（process + process_task）实现向后兼容。

核心特性:
1. 双接口模式 - 兼容传统和新一代接口
2. 统一生命周期 - initialize, process, shutdown
3. 可选集成 - Gateway和记忆系统（可选依赖）
4. 性能统计 - 自动收集处理指标
5. 健康检查 - 标准化的健康状态接口

Author: Athena Team
Version: 1.0.0
Date: 2026-04-24
"""

import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
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
    TaskMessage,
)
from .config import UnifiedAgentConfig

logger = logging.getLogger(__name__)

# ============ 可选依赖导入 ============

# Gateway客户端（可选）
try:
    from core.agents.gateway_client import (
        AgentType as GatewayAgentType,
        GatewayClient,
        GatewayClientConfig,
        Message,
        MessageType,
    )
    GATEWAY_AVAILABLE = True
except ImportError:
    GATEWAY_AVAILABLE = False
    GatewayClient = None  # type: ignore
    GatewayClientConfig = None  # type: ignore
    GatewayAgentType = None  # type: ignore
    Message = None  # type: ignore
    MessageType = None  # type: ignore

# 统一记忆系统（可选）
try:
    from core.memory.unified_memory_system import (
        MemoryCategory,
        MemoryType,
        UnifiedMemorySystem,
        get_project_memory,
    )
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    UnifiedMemorySystem = None  # type: ignore
    get_project_memory = None  # type: ignore
    MemoryType = None  # type: ignore
    MemoryCategory = None  # type: ignore

# 工具注册中心（可选）
try:
    from core.governance.unified_tool_registry import UnifiedToolRegistry, get_unified_registry
    TOOLS_AVAILABLE = True
except ImportError:
    TOOLS_AVAILABLE = False
    UnifiedToolRegistry = None  # type: ignore
    get_unified_registry = None  # type: ignore

# OpenTelemetry追踪（可选）
try:
    from core.tracing import (
        AthenaTracer,
        TracingConfig,
        get_config,
        setup_tracing,
        is_initialized
    )
    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False
    AthenaTracer = None  # type: ignore
    TracingConfig = None  # type: ignore
    get_config = None  # type: ignore
    setup_tracing = None  # type: ignore
    is_initialized = lambda: False


# ============ 统一Agent基类 ============


class UnifiedBaseAgent(ABC):
    """
    统一Agent基类 - 整合两套架构的最佳实践

    特性:
    1. 双接口模式 - 兼容传统process_task和新一代process接口
    2. 统一生命周期 - initialize, process, shutdown
    3. 可选依赖 - Gateway和记忆系统（可选）
    4. 性能统计 - 自动收集处理指标
    5. 健康检查 - 标准化的健康状态接口

    Usage:
        ```python
        class MyAgent(UnifiedBaseAgent):
            @property
            def name(self) -> str:
                return "my-agent"

            async def initialize(self) -> None:
                # 初始化逻辑
                self._status = AgentStatus.READY

            async def process(self, request: AgentRequest) -> AgentResponse:
                # 处理逻辑
                return AgentResponse.success_response(
                    request_id=request.request_id,
                    data={"result": "ok"}
                )

            async def shutdown(self) -> None:
                # 清理逻辑
                self._status = AgentStatus.SHUTDOWN

            async def health_check(self) -> HealthStatus:
                return HealthStatus(status=self._status)
        ```
    """

    def __init__(self, config: UnifiedAgentConfig):
        """
        初始化Agent

        Args:
            config: Agent配置对象
        """
        # 验证配置
        is_valid, errors = config.validate()
        if not is_valid:
            raise ValueError(f"配置无效: {', '.join(errors)}")

        self._config = config
        self._status = AgentStatus.INITIALIZING
        self._metadata = self._load_metadata()
        self._capabilities = self._register_capabilities()

        # 性能统计
        self._stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_processing_time_ms": 0,
        }

        # Gateway通信（可选）
        self._gateway_client: Optional[GatewayClient] = None
        self._gateway_enabled = config.enable_gateway and GATEWAY_AVAILABLE
        self._agent_type = self._determine_agent_type()

        # 统一记忆系统（可选）
        self.memory_system: Optional[UnifiedMemorySystem] = None
        self._memory_enabled = config.enable_memory and MEMORY_AVAILABLE and config.project_path

        # 工具注册中心（可选）
        self._tool_registry: Optional[UnifiedToolRegistry] = None
        self._tools_enabled = config.enable_tools and TOOLS_AVAILABLE

        # OpenTelemetry追踪（可选）
        self._tracer: Optional[AthenaTracer] = None
        self._tracing_enabled = config.enable_tracing and TRACING_AVAILABLE
        if self._tracing_enabled:
            try:
                # 确保追踪系统已初始化
                if not is_initialized():
                    setup_tracing(service_name=f"agent.{config.name}")

                # 创建Agent专用追踪器
                self._tracer = AthenaTracer(f"agent.{config.name}")
                self.logger.debug(f"追踪器已初始化: agent.{config.name}")
            except Exception as e:
                self.logger.warning(f"追踪器初始化失败: {e}")
                self._tracing_enabled = False

        # 日志
        self.logger = logging.getLogger(f"agent.{config.name}")
        self.logger.info(f"初始化Agent: {config.name} v{config.version}")

    # ==================== 必须实现的抽象方法 ====================

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Agent名称（唯一标识符）

        Returns:
            Agent名称，如 "xiaona-legal"
        """
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """
        初始化Agent资源

        在此方法中加载模型、建立连接等耗时操作。
        初始化完成后应将状态设置为 READY。

        Raises:
            Exception: 初始化失败时抛出异常
        """
        pass

    @abstractmethod
    async def process(self, request: AgentRequest) -> AgentResponse:
        """
        处理Agent请求的核心方法（新一代接口）

        Args:
            request: Agent请求对象

        Returns:
            AgentResponse: 响应对象
        """
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """
        关闭Agent，释放资源

        在此方法中关闭连接、释放内存、保存状态等。
        关闭完成后应将状态设置为 SHUTDOWN。
        """
        pass

    @abstractmethod
    async def health_check(self) -> HealthStatus:
        """
        健康检查

        Returns:
            HealthStatus: 健康状态对象
        """
        pass

    # ==================== 可选重写的方法 ====================

    def _load_metadata(self) -> AgentMetadata:
        """
        加载Agent元数据（可选重写）

        Returns:
            AgentMetadata: 元数据对象
        """
        return AgentMetadata(
            name=self.name,
            version=self._config.version,
            description=f"{self.name}智能体",
            author="Athena Team",
            tags=[]
        )

    def _register_capabilities(self) -> list[AgentCapability]:
        """
        注册Agent能力（可选重写）

        Returns:
            能力列表
        """
        return []

    async def validate_request(self, request: AgentRequest) -> bool:
        """
        验证请求有效性（可选重写）

        Args:
            request: 待验证的请求

        Returns:
            是否有效
        """
        if not request.action:
            self.logger.warning("请求缺少action字段")
            return False
        return True

    # ==================== 传统接口支持（向后兼容） ====================

    async def process_task(self, task_message: TaskMessage) -> ResponseMessage:
        """
        传统任务处理接口（向后兼容）

        将传统TaskMessage转换为AgentRequest后调用process方法，
        然后将AgentResponse转换回ResponseMessage。

        Args:
            task_message: 传统任务消息

        Returns:
            ResponseMessage: 传统响应消息
        """
        # 转换消息格式
        request = MessageConverter.task_to_request(task_message)

        # 调用统一处理
        response = await self.safe_process(request)

        # 转换回传统格式
        return MessageConverter.response_to_task_response(response)

    # ==================== 安全处理包装 ====================

    async def safe_process(self, request: AgentRequest) -> AgentResponse:
        """
        安全处理请求（包含异常处理和统计）

        支持跨服务追踪：从请求中提取trace_headers并恢复追踪上下文。

        Args:
            request: 请求对象

        Returns:
            AgentResponse: 响应对象
        """
        start_time = datetime.now()
        self._stats["total_requests"] += 1

        # 提取TraceContext（跨服务追踪）
        trace_context_extracted = False
        if self._tracing_enabled and TRACING_AVAILABLE and request.trace_headers:
            try:
                from core.tracing import TraceContext
                context = TraceContext.extract_from_headers(request.trace_headers)
                if context:
                    # 使用提取的上下文作为父Span
                    # 注意：OpenTelemetry会自动使用当前上下文
                    trace_context_extracted = True
                    self.logger.debug(f"提取TraceContext: {request.trace_headers.get('traceparent', 'N/A')[:50]}...")
            except Exception as e:
                self.logger.debug(f"提取TraceContext失败: {e}")

        # 追踪支持
        span_context = None
        if self._tracing_enabled and self._tracer:
            span_context = self._tracer.start_agent_span(
                agent_name=self.name,
                task_type=request.action or "unknown",
                request_id=request.request_id
            )
            span_context.__enter__()

        try:
            # 验证请求
            if not await self.validate_request(request):
                self._stats["failed_requests"] += 1
                return AgentResponse.error_response(
                    request_id=request.request_id,
                    error="请求验证失败"
                )

            # 检查状态
            if self._status != AgentStatus.READY:
                self._stats["failed_requests"] += 1
                return AgentResponse.error_response(
                    request_id=request.request_id,
                    error=f"Agent未就绪: {self._status.value}"
                )

            # 更新状态
            self._status = AgentStatus.BUSY

            # 核心处理
            response = await self.process(request)

            # 统计
            self._stats["successful_requests"] += 1

            return response

        except Exception as e:
            self.logger.error(f"处理请求失败: {e}", exc_info=True)
            self._status = AgentStatus.ERROR
            self._stats["failed_requests"] += 1

            # 记录异常到追踪
            if self._tracing_enabled and self._tracer:
                try:
                    self._tracer.record_exception(e)
                except Exception:
                    pass  # 追踪失败不影响主流程

            return AgentResponse.error_response(
                request_id=request.request_id,
                error=str(e)
            )

        finally:
            # 结束追踪Span
            if span_context:
                try:
                    span_context.__exit__(None, None, None)
                except Exception:
                    pass  # 追踪失败不影响主流程

            # 计算处理时间
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            self._stats["total_processing_time_ms"] += processing_time

            # 恢复状态
            if self._status == AgentStatus.BUSY:
                self._status = AgentStatus.READY

    # ==================== Gateway通信 ====================

    async def connect_gateway(self) -> bool:
        """
        连接到Gateway

        Returns:
            是否连接成功
        """
        if not self._gateway_enabled:
            self.logger.debug("Gateway通信已禁用")
            return False

        if self._gateway_client is None:
            config = GatewayClientConfig(
                gateway_url=self._config.gateway_url,
                agent_type=self._agent_type or GatewayAgentType.UNKNOWN,
                agent_id=self.name
            )
            self._gateway_client = GatewayClient(config)

            # 注册消息处理器
            self._gateway_client.register_handler(MessageType.TASK, self._handle_gateway_task)
            self._gateway_client.register_handler(MessageType.QUERY, self._handle_gateway_query)
            self._gateway_client.register_handler(MessageType.NOTIFY, self._handle_gateway_notify)

        return await self._gateway_client.connect()

    async def disconnect_gateway(self) -> None:
        """断开Gateway连接"""
        if self._gateway_client:
            await self._gateway_client.disconnect()

    async def send_to_agent(
        self,
        target_agent: str,
        task_type: str,
        parameters: Optional[dict[str, Any]] = None,
        priority: int = 5,
        trace_headers: Optional[dict[str, str]] = None
    ) -> Optional[Any]:
        """
        发送消息到其他Agent（支持跨服务追踪）

        自动注入当前TraceContext到消息headers，实现完整的调用链追踪。

        Args:
            target_agent: 目标Agent名称
            task_type: 任务类型
            parameters: 任务参数
            priority: 优先级（0-10）
            trace_headers: 可选的追踪headers（如果不提供则自动注入）

        Returns:
            响应结果

        Example:
            >>> # 自动注入trace
            >>> result = await self.send_to_agent("xiaona", "analyze")
            >>>
            >>> # 手动指定trace headers
            >>> result = await self.send_to_agent(
            ...     "xiaona", "analyze",
            ...     trace_headers=TraceContext.inject_to_headers()
            ... )
        """
        if not self._gateway_client or not self._gateway_client.is_connected:
            self.logger.warning("未连接到Gateway")
            return None

        # 确定目标Agent类型
        agent_type_map = {
            "xiaona": GatewayAgentType.XIAONA,
            "小娜": GatewayAgentType.XIAONA,
            "xiaonuo": GatewayAgentType.XIAONUO,
            "小诺": GatewayAgentType.XIAONUO,
            "yunxi": GatewayAgentType.YUNXI,
            "云熙": GatewayAgentType.YUNXI,
        }

        target_type = agent_type_map.get(target_agent.lower(), GatewayAgentType.UNKNOWN)

        # 自动注入TraceContext（如果未提供且追踪已启用）
        headers = trace_headers
        if headers is None and self._tracing_enabled and TRACING_AVAILABLE:
            try:
                from core.tracing import TraceContext
                headers = TraceContext.inject_to_headers()
                self.logger.debug(f"注入TraceContext: {headers.get('traceparent', 'N/A')[:50]}...")
            except Exception as e:
                self.logger.debug(f"注入TraceContext失败: {e}")

        response = await self._gateway_client.send_task(
            task_type=task_type,
            target_agent=target_type,
            parameters=parameters,
            priority=priority,
            trace_headers=headers  # 传递trace headers
        )

        return response.result if response and response.success else None

    async def broadcast(self, data: Optional[dict[str, Any]]) -> bool:
        """
        广播消息到所有Agent

        Args:
            data: 广播数据

        Returns:
            是否成功
        """
        if not self._gateway_client or not self._gateway_client.is_connected:
            self.logger.warning("未连接到Gateway")
            return False

        return await self._gateway_client.broadcast(data)

    def _handle_gateway_task(self, message: Message) -> None:
        """处理Gateway任务消息"""
        self.logger.info(f"收到任务: {message.data}")

    def _handle_gateway_query(self, message: Message) -> None:
        """处理Gateway查询消息"""
        self.logger.info(f"收到查询: {message.data}")

    def _handle_gateway_notify(self, message: Message) -> None:
        """处理Gateway通知消息"""
        self.logger.info(f"收到通知: {message.data}")

    @property
    def gateway_connected(self) -> bool:
        """是否已连接到Gateway"""
        return self._gateway_client is not None and self._gateway_client.is_connected

    # ==================== 记忆系统 ====================

    def load_memory(
        self,
        type: MemoryType,
        category: MemoryCategory,
        key: str
    ) -> Optional[str]:
        """
        加载记忆

        Args:
            type: 记忆类型
            category: 记忆分类
            key: 唯一键

        Returns:
            记忆内容，如果不存在则返回None
        """
        if not self._memory_enabled or not self.memory_system:
            return None

        try:
            return self.memory_system.read(type, category, key)
        except Exception as e:
            self.logger.error(f"记忆加载失败: {e}")
            return None

    def save_memory(
        self,
        type: MemoryType,
        category: MemoryCategory,
        key: str,
        content: str,
        metadata: Optional[dict[str, Any]] = None
    ) -> bool:
        """
        保存记忆

        Args:
            type: 记忆类型
            category: 记忆分类
            key: 唯一键
            content: Markdown内容
            metadata: 元数据

        Returns:
            是否成功
        """
        if not self._memory_enabled or not self.memory_system:
            self.logger.debug("记忆系统未启用，跳过保存")
            return False

        try:
            self.memory_system.write(type, category, key, content, metadata)
            return True
        except Exception as e:
            self.logger.error(f"记忆保存失败: {e}")
            return False

    def search_memory(
        self,
        query: str,
        type: Optional[MemoryType] = None,
        category: Optional[MemoryCategory] = None,
        limit: int = 10
    ) -> list:
        """
        搜索记忆

        Args:
            query: 搜索查询
            type: 记忆类型过滤（可选）
            category: 记忆分类过滤（可选）
            limit: 返回数量限制

        Returns:
            匹配的记忆条目列表
        """
        if not self._memory_enabled or not self.memory_system:
            return []

        try:
            return self.memory_system.search(query, type, category, limit)
        except Exception as e:
            self.logger.error(f"记忆搜索失败: {e}")
            return []

    # ==================== 工具系统 ====================

    async def _get_tool_registry(self) -> Optional[UnifiedToolRegistry]:
        """
        获取工具注册中心（延迟初始化）

        Returns:
            UnifiedToolRegistry实例，如果工具未启用则返回None
        """
        if not self._tools_enabled:
            return None

        if self._tool_registry is None:
            try:
                self._tool_registry = get_unified_registry()

                # 如果注册中心未初始化，则初始化
                if not self._tool_registry.tools:
                    await self._tool_registry.initialize()

                self.logger.debug(f"工具注册中心已连接，可用工具: {len(self._tool_registry.tools)}")
            except Exception as e:
                self.logger.warning(f"初始化工具注册中心失败: {e}")
                self._tools_enabled = False
                return None

        return self._tool_registry

    async def call_tool(
        self,
        tool_id: str,
        parameters: Optional[dict[str, Any]] = None,
        context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        调用工具

        Args:
            tool_id: 工具ID
            parameters: 工具参数
            context: 执行上下文

        Returns:
            工具执行结果
        """
        registry = await self._get_tool_registry()

        if not registry:
            return {
                "success": False,
                "error": "工具系统未启用或不可用",
                "tool_id": tool_id
            }

        try:
            execution_result = await registry.execute_tool(tool_id, parameters or {}, context or {})

            return {
                "success": execution_result.success,
                "result": execution_result.result,
                "error": execution_result.error,
                "tool_id": tool_id,
                "execution_time": execution_result.execution_time,
                "timestamp": execution_result.timestamp.isoformat()
            }

        except Exception as e:
            self.logger.error(f"工具调用失败 {tool_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "tool_id": tool_id
            }

    # ==================== 公共属性和方法 ====================

    @property
    def status(self) -> AgentStatus:
        """获取当前状态"""
        return self._status

    @property
    def is_ready(self) -> bool:
        """是否就绪"""
        return self._status == AgentStatus.READY

    def get_capabilities(self) -> list[AgentCapability]:
        """获取能力列表"""
        return self._capabilities.copy()

    def get_metadata(self) -> AgentMetadata:
        """获取元数据"""
        return self._metadata

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        stats = self._stats.copy()
        if stats["total_requests"] > 0:
            stats["avg_processing_time_ms"] = (
                stats["total_processing_time_ms"] / stats["total_requests"]
            )
            stats["success_rate"] = (
                stats["successful_requests"] / stats["total_requests"]
            )
        return stats

    def to_dict(self) -> dict[str, Any]:
        """转换为字典表示"""
        return {
            "name": self.name,
            "status": self._status.value,
            "metadata": self._metadata.to_dict(),
            "capabilities": [cap.to_dict() for cap in self._capabilities],
            "stats": self.get_stats()
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name} status={self._status.value}>"

    # ==================== 私有方法 ====================

    def _determine_agent_type(self) -> Optional[GatewayAgentType]:
        """根据名称确定Agent类型"""
        if not GATEWAY_AVAILABLE:
            return None

        name_lower = self.name.lower()
        if "xiaona" in name_lower or "小娜" in name_lower:
            return GatewayAgentType.XIAONA
        elif "xiaonuo" in name_lower or "小诺" in name_lower:
            return GatewayAgentType.XIAONUO
        elif "yunxi" in name_lower or "云熙" in name_lower:
            return GatewayAgentType.YUNXI
        else:
            return GatewayAgentType.UNKNOWN


# ============ 导出 ============

__all__ = [
    "UnifiedBaseAgent",
]
