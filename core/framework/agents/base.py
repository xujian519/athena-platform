
"""
Athena智能体统一接口基类

所有智能体必须继承此基类并实现其抽象方法。
提供统一的初始化、处理、健康检查和关闭接口。

Author: Athena Team
Version: 1.0.0
Date: 2025-02-21
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

# 类型检查时导入,避免循环导入
if TYPE_CHECKING:
    from core.governance.unified_tool_registry import UnifiedToolRegistry

# ============ 数据模型 ============


class AgentStatus(Enum):
    """智能体状态枚举"""
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    SHUTDOWN = "shutdown"


@dataclass
class AgentCapability:
    """智能体能力描述"""
    name: str
    description: str
    parameters: Optional[dict[str, Any]] = field(default_factory=dict)
    examples: Optional[list[dict[str, Any]]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "examples": self.examples
        }


@dataclass
class AgentMetadata:
    """智能体元数据"""
    name: str
    version: str
    description: str
    author: str
    created_at: datetime = field(default_factory=datetime.now)
    tags: Optional[list[str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "created_at": self.created_at.isoformat(),
            "tags": self.tags
        }


@dataclass
class AgentRequest:
    """智能体请求模型"""
    request_id: str
    action: str
    parameters: Optional[dict[str, Any]] = field(default_factory=dict)
    context: Optional[dict[str, Any]] = field(default_factory=dict)
    metadata: Optional[dict[str, Any]] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "request_id": self.request_id,
            "action": self.action,
            "parameters": self.parameters,
            "context": self.context,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class AgentResponse:
    """智能体响应模型"""
    request_id: str
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Optional[dict[str, Any]] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    processing_time_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "request_id": self.request_id,
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "processing_time_ms": self.processing_time_ms
        }

    @classmethod
    def error_response(cls, request_id: str, error: str, **_kwargs) -> "AgentResponse":  # noqa: ARG001
        """创建错误响应"""
        return cls(
            request_id=request_id,
            success=False,
            error=error,
            **_kwargs  # noqa: ARG001
        )

    @classmethod
    def success_response(cls, request_id: str, data: Any = None, **_kwargs) -> "AgentResponse":  # noqa: ARG001
        """创建成功响应"""
        return cls(
            request_id=request_id,
            success=True,
            data=data,
            **_kwargs  # noqa: ARG001
        )


@dataclass
class HealthStatus:
    """健康状态"""
    status: AgentStatus
    message: str = ""
    details: Optional[dict[str, Any]] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def is_healthy(self) -> str:
        """是否健康"""
        return self.status in [AgentStatus.READY, AgentStatus.BUSY]

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "healthy": self.is_healthy()
        }


# ============ 智能体基类 ============


class BaseAgent(ABC):
    """
    智能体统一接口基类

    所有智能体必须继承此类并实现所有抽象方法。
    提供统一的初始化、处理、健康检查和关闭接口。

    Usage:
        ```python
        class MyAgent(BaseAgent):
            @property
            def name(self) -> str:
                return "my-agent"

            async def initialize(self) -> str:
                # 初始化逻辑
                self._status = AgentStatus.READY

            async def process(self, request: AgentRequest) -> str:
                # 处理逻辑
                return AgentResponse.success_response(
                    request_id=request.request_id,
                    data={"result": "ok"}
                )

            async def shutdown(self) -> str:
                # 清理逻辑
                self._status = AgentStatus.SHUTDOWN

            async def health_check(self) -> str:
                # 健康检查逻辑
                return HealthStatus(status=self._status)
        ```
    """

    # 类级别的注册表
    _registry: Optional[dict[str, type]] = {}

    def __init__(self, config: Optional[dict[str, Any]] = None):
        """
        初始化智能体

        Args:
            config: 智能体配置字典
        """
        self._config = config or {}
        self._status = AgentStatus.INITIALIZING
        self._metadata = self._load_metadata()
        self._capabilities = self._register_capabilities()
        self._context: Optional[dict[str, Any]] = {}

        # 性能统计
        self._stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_processing_time_ms": 0
        }

        # 工具管理器(延迟初始化)
        self._tool_registry: Optional["UnifiedToolRegistry"] = None
        self._tools_enabled: bool = config.get("tools_enabled", True) if config else True

        # 初始化日志
        self._setup_logging()

        self.logger.info(f"初始化智能体: {self.name} v{self._metadata.version}")

    # ========== 必须实现的抽象属性和方法 ==========

    @property
    @abstractmethod
    def name(self) -> str:
        """
        智能体名称 (唯一标识符)

        Returns:
            智能体名称，如 "xiaona-legal"

        Note:
            此名称将用于智能体的注册和发现，必须全局唯一
        """
        pass

    @abstractmethod
    async def initialize(self) -> str:
        """
        初始化智能体资源

        在此方法中加载模型、建立连接等耗时操作。
        初始化完成后应将状态设置为 READY。

        Raises:
            Exception: 初始化失败时抛出异常，状态将自动设置为ERROR

        Note:
            此方法会在智能体创建后由AgentFactory或框架自动调用
        """
        pass

    @abstractmethod
    async def process(self, request: AgentRequest) -> str:
        """
        处理智能体请求的核心方法

        Args:
            request: 智能体请求对象

        Returns:
            AgentResponse: 响应对象

        Raises:
            Exception: 处理失败时抛出异常，由safe_process捕获

        Note:
            此方法由safe_process包装，自动处理状态转换和异常捕获
        """
        pass

    @abstractmethod
    async def shutdown(self) -> str:
        """
        关闭智能体，释放资源

        在此方法中关闭连接、释放内存、保存状态等。
        关闭完成后应将状态设置为 SHUTDOWN。

        Note:
            此方法会在智能体销毁前由框架自动调用
        """
        pass

    @abstractmethod
    async def health_check(self) -> str:
        """
        健康检查

        Returns:
            HealthStatus: 健康状态对象

        Note:
            用于监控和负载均衡系统判断智能体可用性
        """
        pass

    # ========== 可选重写的方法 ==========

    def _load_metadata(self) -> str:
        """
        加载智能体元数据 (可选重写)

        Returns:
            AgentMetadata: 元数据对象
        """
        return AgentMetadata(
            name=self.name,
            version="1.0.0",
            description=f"{self.name}智能体",
            author="Athena Team",
            tags=[]
        )

    def _register_capabilities(self) -> list[AgentCapability]:
        """
        注册智能体能力 (可选重写)

        Returns:
            能力列表

        Note:
            每个能力应包含name、description和参数说明
        """
        return []

    async def validate_request(self, request: AgentRequest) -> str:
        """
        验证请求有效性 (可选重写)

        Args:
            request: 待验证的请求

        Returns:
            bool: 是否有效

        Note:
            返回False将直接返回错误响应，不会调用process方法
        """
        if not request.action:
            self.logger.warning("请求缺少action字段")
            return False
        return True

    async def before_process(self, request: AgentRequest) -> str:
        """
        处理前钩子 (可选重写)

        Args:
            request: 即将处理的请求

        Note:
            可用于请求预处理、日志记录、权限检查等
        """
        pass

    async def after_process(self, request: AgentRequest, response: AgentResponse) -> str:
        """
        处理后钩子 (可选重写)

        Args:
            request: 已处理的请求
            response: 生成的响应

        Note:
            可用于响应后处理、日志记录、指标收集等
        """
        pass

    # ========== 公共属性和方法 ==========

    @property
    def status(self) -> str:
        """获取当前状态"""
        return self._status

    @property
    def is_ready(self) -> str:
        """是否就绪"""
        return self._status == AgentStatus.READY

    @property
    def config(self) -> dict[str, Any]:
        """获取配置"""
        return self._config.copy()

    def get_capabilities(self) -> list[AgentCapability]:
        """获取能力列表"""
        return self._capabilities.copy()

    def get_metadata(self) -> str:
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

    def set_context(self, key: str, value: Any) -> str:
        """设置上下文"""
        self._context[key] = value

    def get_context(self, key: str, default: Any = None) -> str:
        """获取上下文"""
        return self._context.get(key, default)

    # ========== 工具支持方法 ==========

    async def _get_tool_registry(self) -> Optional["UnifiedToolRegistry"]:
        """
        获取工具注册中心(延迟初始化)

        Returns:
            UnifiedToolRegistry实例,如果工具未启用则返回None
        """
        if not self._tools_enabled:
            return None

        if self._tool_registry is None:
            try:
                from core.governance.unified_tool_registry import get_unified_registry

                self._tool_registry = get_unified_registry()

                # 如果注册中心未初始化,则初始化
                if not self._tool_registry.tools:
                    await self._tool_registry.initialize()

                self.logger.debug(f"工具注册中心已连接,可用工具: {len(self._tool_registry.tools)}")
            except ImportError as e:
                self.logger.warning(f"无法导入工具注册中心: {e}")
                self._tools_enabled = False
                return None
            except Exception as e:
                self.logger.error(f"初始化工具注册中心失败: {e}")
                self._tools_enabled = False
                return None

        return self._tool_registry

    async def call_tool(
        self,
        tool_id: str,
        parameters: Optional[dict[str, Any]],
        context: Optional[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        调用工具

        Args:
            tool_id: 工具ID (如 "builtin.file_read", "mcp.server.tool", "search.patent_search")
            parameters: 工具参数
            context: 执行上下文

        Returns:
            工具执行结果

        Raises:
            RuntimeError: 如果工具调用失败

        Example:
            >>> result = await agent.call_tool(
            ...     "builtin.file_read",
            ...     {"path": "/path/to/file.txt"}
            ... )
            >>> if result["success"]:
            ...     content = result["result"]["content"]
        """
        registry = await self._get_tool_registry()

        if not registry:
            return {
                "success": False,
                "error": "工具系统未启用或不可用",
                "tool_id": tool_id
            }

        try:
            execution_result = await registry.execute_tool(tool_id, parameters, context)

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

    async def discover_tools(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 5,
        use_vector: bool = False
    ) -> list[str, Any]:
        """
        智能发现工具

        Args:
            query: 查询描述 (如 "搜索专利", "读取文件", "翻译文档")
            category: 工具类别过滤 (builtin, mcp, search, service, agent等)
            limit: 返回数量限制
            use_vector: 是否使用向量搜索(更精确但需要模型)

        Returns:
            匹配的工具列表,按相关性排序

        Example:
            >>> tools = await agent.discover_tools("搜索专利")
            >>> for tool in tools:
            ...     print(f"{tool['name']}: {tool['description']}")
        """
        registry = await self._get_tool_registry()

        if not registry:
            return []

        try:
            from core.governance.unified_tool_registry import ToolCategory

            category_enum = ToolCategory(category) if category else None

            results = await registry.discover_tools(
                query=query,
                category=category_enum,
                limit=limit,
                use_vector=use_vector
            )

            return results

        except Exception as e:
            self.logger.error(f"工具发现失败: {e}")
            return []

    async def list_tools(
        self,
        category: Optional[str] = None,
        status: Optional[str] = None
    ) -> list[str, Any]:
        """
        列出可用工具

        Args:
            category: 按类别过滤 (builtin, mcp, search, service, agent等)
            status: 按状态过滤 (available, busy, error等)

        Returns:
            工具信息列表

        Example:
            >>> # 列出所有可用工具
            >>> tools = await agent.list_tools()
            >>> # 只列出内置工具
            >>> builtin = await agent.list_tools(category="builtin")
        """
        registry = await self._get_tool_registry()

        if not registry:
            return []

        try:
            from core.governance.unified_tool_registry import ToolCategory, ToolStatus

            category_enum = ToolCategory(category) if category else None
            status_enum = ToolStatus(status) if status else None

            return registry.list_tools(category=category_enum, status=status_enum)

        except Exception as e:
            self.logger.error(f"列出工具失败: {e}")
            return []

    async def get_tool_info(self, tool_id: str) -> Optional[dict[str, Any]]:
        """
        获取工具详细信息

        Args:
            tool_id: 工具ID

        Returns:
            工具详细信息,如果工具不存在返回None

        Example:
            >>> info = await agent.get_tool_info("builtin.file_read")
            >>> print(info["description"])
            >>> print(info["capabilities"])
        """
        registry = await self._get_tool_registry()

        if not registry:
            return None

        try:
            return registry.get_tool_info(tool_id)
        except Exception as e:
            self.logger.error(f"获取工具信息失败 {tool_id}: {e}")
            return None

    @property
    def tools_enabled(self) -> str:
        """工具系统是否启用"""
        return self._tools_enabled

    # ========== 核心处理方法 ==========

    async def safe_process(self, request: AgentRequest) -> str:
        """
        安全处理请求 (包含异常处理和钩子)

        Args:
            request: 请求对象

        Returns:
            AgentResponse: 响应对象

        Note:
            这是外部调用的主要入口，自动处理：
            - 请求验证
            - 状态检查
            - 前置/后置钩子
            - 异常捕获
            - 性能统计
        """
        start_time = datetime.now()
        self._stats["total_requests"] += 1

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
                    error=f"智能体未就绪: {self._status.value}"
                )

            # 更新状态
            self._status = AgentStatus.BUSY

            # 前置钩子
            await self.before_process(request)

            # 核心处理
            response = await self.process(request)

            # 后置钩子
            await self.after_process(request, response)

            # 统计
            self._stats["successful_requests"] += 1

            return response

        except Exception as e:
            self.logger.error(f"处理请求失败: {e}", exc_info=True)
            self._status = AgentStatus.ERROR
            self._stats["failed_requests"] += 1

            return AgentResponse.error_response(
                request_id=request.request_id,
                error=str(e)
            )

        finally:
            # 计算处理时间
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            self._stats["total_processing_time_ms"] += processing_time

            # 恢复状态
            if self._status == AgentStatus.BUSY:
                self._status = AgentStatus.READY

    # ========== 工具方法 ==========

    def _setup_logging(self) -> str:
        """设置日志"""
        self.logger = logging.getLogger(f"agent.{self.name}")

        # 如果logger还没有handler，添加默认配置
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '[%(asctime)s] %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    async def ping(self) -> str:
        """
        快速健康检查 (简化版)

        Returns:
            bool: 是否健康
        """
        try:
            status = await self.health_check()
            return status.is_healthy()
        except Exception:
            return False

    def reset_stats(self) -> str:
        """重置统计信息"""
        self._stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_processing_time_ms": 0
        }

    def to_dict(self) -> dict[str, Any]:
        """
        转换为字典表示

        Returns:
            包含智能体基本信息的字典
        """
        return {
            "name": self.name,
            "status": self._status.value,
            "metadata": self._metadata.to_dict(),
            "capabilities": [cap.to_dict() for cap in self._capabilities],
            "stats": self.get_stats()
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name} status={self._status.value}>"


# ============ 智能体注册中心 ==========


class _AgentRegistryInstance:
    """AgentRegistry的单例实例类"""
    def __init__(self):
        self._agents: Optional[dict[str, BaseAgent]] = {}
        self._logger = logging.getLogger("agent.registry")


# 模块级别的单例实例
_registry_instance = _AgentRegistryInstance()


class AgentRegistry:
    """
    智能体注册中心

    管理所有智能体的注册、发现和生命周期。
    使用模块级单例模式，全局唯一实例。

    Usage:
        ```python
        # 注册智能体
        AgentRegistry.register(agent)

        # 获取智能体
        agent = AgentRegistry.get("xiaona-legal")

        # 根据能力查找
        agents = AgentRegistry.get_by_capability("patent-search")
        ```
    """

    @classmethod
    def _get_instance(cls) -> str:
        """获取单例实例"""
        return _registry_instance

    @classmethod
    def register(cls, agent: BaseAgent) -> str:
        """
        注册智能体

        Args:
            agent: 智能体实例

        Raises:
            ValueError: 如果智能体名称已存在

        Note:
            智能体名称必须全局唯一
        """
        instance = cls._get_instance()
        name = agent.name
        if name in instance._agents:
            raise ValueError(f"智能体 {name} 已存在")
        instance._agents[name] = agent
        instance._logger.info(f"注册智能体: {name}")

    @classmethod
    def unregister(cls, name: str) -> str:
        """
        注销智能体

        Args:
            name: 智能体名称

        Note:
            这不会关闭智能体，仅从注册表中移除
        """
        instance = cls._get_instance()
        if name in instance._agents:
            del instance._agents[name]
            instance._logger.info(f"注销智能体: {name}")

    @classmethod
    def get(cls, name: str) -> Optional["BaseAgent"]:
        """
        获取智能体

        Args:
            name: 智能体名称

        Returns:
            智能体实例，如果不存在返回None
        """
        instance = cls._get_instance()
        return instance._agents.get(name)

    @classmethod
    def list_agents(cls) -> list[str]:
        """
        列出所有智能体名称

        Returns:
            智能体名称列表
        """
        instance = cls._get_instance()
        return list(instance._agents.keys())

    @classmethod
    def get_all(cls) -> dict[str, BaseAgent]:
        """
        获取所有智能体

        Returns:
            智能体字典 {name: agent}
        """
        instance = cls._get_instance()
        return instance._agents.copy()

    @classmethod
    def get_by_capability(cls, capability: str) -> list[BaseAgent]:
        """
        根据能力查找智能体

        Args:
            capability: 能力名称

        Returns:
            具有该能力的智能体列表
        """
        result = []
        for agent in cls._get_instance()._agents.values():
            for cap in agent.get_capabilities():
                if cap.name == capability:
                    result.append(agent)
                    break
        return result

    @classmethod
    def get_ready_agents(cls) -> list[BaseAgent]:
        """
        获取所有就绪的智能体

        Returns:
            就绪状态的智能体列表
        """
        return [agent for agent in cls._get_instance()._agents.values() if agent.is_ready]

    @classmethod
    async def initialize_all(cls) -> str:
        """
        初始化所有智能体

        Note:
            按注册顺序依次初始化
        """
        for agent in cls._get_instance()._agents.values():
            if agent.status == AgentStatus.INITIALIZING:
                try:
                    await agent.initialize()
                except Exception as e:
                    cls._get_instance()._logger.error(f"初始化智能体 {agent.name} 失败: {e}")

    @classmethod
    async def shutdown_all(cls) -> str:
        """
        关闭所有智能体

        Note:
            按注册倒序依次关闭
        """
        agents = list(cls._get_instance()._agents.values())
        for agent in reversed(agents):
            try:
                await agent.shutdown()
            except Exception as e:
                cls._get_instance()._logger.error(f"关闭智能体 {agent.name} 失败: {e}")

    @classmethod
    async def health_check_all(cls) -> dict[str, HealthStatus]:
        """
        检查所有智能体健康状态

        Returns:
            {name: HealthStatus} 字典
        """
        results = {}
        for name, agent in cls._get_instance()._agents.items():
            try:
                results[name] = await agent.health_check()
            except Exception as e:
                results[name] = HealthStatus(
                    status=AgentStatus.ERROR,
                    message=str(e)
                )
        return results

    @classmethod
    def clear(cls) -> str:
        """
        清空注册表

        Note:
        主要用于测试环境
        """
        cls._get_instance()._agents.clear()


# 导出
__all__ = [
    "AgentStatus",
    "AgentCapability",
    "AgentMetadata",
    "AgentRequest",
    "AgentResponse",
    "HealthStatus",
    "BaseAgent",
    "AgentRegistry"
]

