#!/usr/bin/env python3
from __future__ import annotations
"""
MCP服务集成模块

实现MCP服务发现、工具注册、性能监控和错误处理。

Author: Athena平台团队
Created: 2026-01-20
Version: v1.0.0
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from core.tools.base import ToolCapability, ToolCategory, ToolDefinition, ToolPriority, ToolRegistry

logger = logging.getLogger(__name__)


class MCPServiceStatus(Enum):
    """MCP服务状态"""

    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class MCPServiceInfo:
    """
    MCP服务信息

    描述一个MCP服务的基本信息。
    """

    service_id: str  # 服务唯一标识
    name: str  # 服务名称
    description: str  # 服务描述
    server_type: str  # 服务器类型 (patent-search, academic-search等)
    host: str = "localhost"  # 主机地址
    port: int = 8000  # 端口号
    protocol: str = "http"  # 协议 (http, https, stdio)

    # 状态信息
    status: MCPServiceStatus = MCPServiceStatus.STOPPED
    last_check: datetime | None = None
    last_error: Optional[str] = None

    # 工具列表
    available_tools: list[str] = field(default_factory=list)

    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class MCPCallMetrics:
    """
    MCP调用指标

    跟踪MCP服务的调用性能。
    """

    service_id: str  # 服务ID
    tool_name: str  # 工具名称

    total_calls: int = 0  # 总调用次数
    successful_calls: int = 0  # 成功次数
    failed_calls: int = 0  # 失败次数

    total_execution_time: float = 0.0  # 总执行时间
    avg_execution_time: float = 0.0  # 平均执行时间
    min_execution_time: float = float("inf")
    max_execution_time: float = 0.0

    last_called: datetime | None = None
    last_error: Optional[str] = None
    last_success: datetime | None = None

    # 错误分类
    error_counts: dict[str, int] = field(default_factory=dict)

    def update(self, execution_time: float, success: bool, error: Optional[str] = None) -> Any:
        """
        更新调用指标

        Args:
            execution_time: 执行时间(秒)
            success: 是否成功
            error: 错误信息(如果失败)
        """
        self.total_calls += 1

        if success:
            self.successful_calls += 1
            self.last_success = datetime.now()
        else:
            self.failed_calls += 1
            self.last_error = error or "Unknown error"

            # 错误分类统计
            if error:
                error_type = error.split(":")[0] if ":" in error else error
                self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1

        # 更新执行时间统计
        self.total_execution_time += execution_time
        self.avg_execution_time = self.total_execution_time / self.total_calls

        if execution_time < self.min_execution_time:
            self.min_execution_time = execution_time

        if execution_time > self.max_execution_time:
            self.max_execution_time = execution_time

        self.last_called = datetime.now()

    def get_success_rate(self) -> float:
        """获取成功率"""
        return self.successful_calls / self.total_calls if self.total_calls > 0 else 0.0

    def get_error_summary(self) -> dict[str, int]:
        """获取错误摘要"""
        return dict(sorted(self.error_counts.items(), key=lambda x: -x[1]))


@dataclass
class MCPRetryPolicy:
    """
    MCP重试策略

    定义MCP调用的重试规则。
    """

    max_retries: int = 3  # 最大重试次数
    base_delay: float = 1.0  # 基础延迟(秒)
    max_delay: float = 30.0  # 最大延迟(秒)
    exponential_backoff: bool = True  # 指数退避

    # 可重试的错误类型
    retryable_errors: list[str] = field(
        default_factory=lambda: ["timeout", "connection", "network", "temporary"]
    )

    def should_retry(self, error: str, retry_count: int) -> bool:
        """
        判断是否应该重试

        Args:
            error: 错误信息
            retry_count: 当前重试次数

        Returns:
            是否应该重试
        """
        if retry_count >= self.max_retries:
            return False

        if not error:
            return False

        error_lower = error.lower()

        # 检查是否是可重试的错误
        return any(retryable.lower() in error_lower for retryable in self.retryable_errors)

    def get_delay(self, retry_count: int) -> float:
        """
        获取重试延迟

        Args:
            retry_count: 重试次数

        Returns:
            延迟时间(秒)
        """
        delay = self.base_delay * 2 ** retry_count if self.exponential_backoff else self.base_delay

        return min(delay, self.max_delay)


class MCPServiceRegistry:
    """
    MCP服务注册中心

    管理所有MCP服务的注册、发现和状态跟踪。
    """

    # 预定义的MCP服务配置
    PREDEFINED_SERVICES = {
        "patent-search-mcp": {
            "name": "专利搜索MCP服务",
            "description": "提供中国专利搜索功能",
            "server_type": "patent_search",
            "port": 8001,
            "tools": ["search_cn_patents", "get_patent_by_id", "analyze_patent_landscape"],
        },
        "academic-search-mcp": {
            "name": "学术搜索MCP服务",
            "description": "提供学术论文搜索功能",
            "server_type": "academic_search",
            "port": 8002,
            "tools": ["search_papers", "get_paper_metadata", "get_citations"],
        },
        "patent-downloader-mcp": {
            "name": "专利下载MCP服务",
            "description": "提供专利文档下载功能",
            "server_type": "patent_download",
            "port": 8003,
            "tools": ["download_patent_pdf", "get_patent_fulltext"],
        },
        "gaode-mcp": {
            "name": "高德地图MCP服务",
            "description": "提供高德地图API集成",
            "server_type": "map_service",
            "port": 8004,
            "tools": ["geocoding", "path_planning", "poi_search"],
        },
        "jina-ai-mcp": {
            "name": "Jina AI MCP服务",
            "description": "提供Jina AI集成功能",
            "server_type": "ai_service",
            "port": 8005,
            "tools": ["embedding", "rerank", "web_search"],
        },
        "chrome-mcp": {
            "name": "Chrome浏览器MCP服务",
            "description": "提供Chrome浏览器控制",
            "server_type": "browser_automation",
            "port": 8006,
            "tools": ["navigate", "screenshot", "execute_js"],
        },
        "github-mcp": {
            "name": "GitHub MCP服务",
            "description": "提供GitHub API集成",
            "server_type": "version_control",
            "port": 8007,
            "tools": ["list_issues", "create_pr", "get_file_content"],
        },
    }

    def __init__(self, tool_registry: ToolRegistry):
        """
        初始化MCP服务注册中心

        Args:
            tool_registry: 工具注册中心
        """
        self.tool_registry = tool_registry
        self._services: dict[str, MCPServiceInfo] = {}
        self._metrics: dict[str, MCPCallMetrics] = {}

        # 重试策略
        self.retry_policy = MCPRetryPolicy()

        logger.info("🔌 MCPServiceRegistry初始化完成")

    def register_service(self, service: MCPServiceInfo) -> None:
        """
        注册MCP服务

        Args:
            service: MCPServiceInfo对象
        """
        self._services[service.service_id] = service
        service.updated_at = datetime.now()

        logger.info(
            f"✅ MCP服务已注册: {service.name} " f"({service.server_type}, 端口: {service.port})"
        )

    def register_predefined_services(self) -> None:
        """注册所有预定义的MCP服务"""
        for service_id, config in self.PREDEFINED_SERVICES.items():
            service = MCPServiceInfo(
                service_id=service_id,
                name=config["name"],
                description=config["description"],
                server_type=config["server_type"],
                port=config["port"],
                available_tools=config["tools"],
            )
            self.register_service(service)

            # 自动注册工具到工具注册中心
            self._auto_register_tools(service)

        logger.info(f"✅ 已注册{len(self.PREDEFINED_SERVICES)}个预定义MCP服务")

    def _auto_register_tools(self, service: MCPServiceInfo) -> None:
        """
        自动注册MCP服务的工具到工具注册中心

        Args:
            service: MCP服务信息
        """
        # 映射MCP服务器类型到工具分类
        category_mapping = {
            "patent_search": ToolCategory.PATENT_SEARCH,
            "academic_search": ToolCategory.ACADEMIC_SEARCH,
            "patent_download": ToolCategory.DATA_EXTRACTION,
            "map_service": ToolCategory.API_INTEGRATION,
            "ai_service": ToolCategory.MCP_SERVICE,
            "browser_automation": ToolCategory.WEB_AUTOMATION,
            "version_control": ToolCategory.API_INTEGRATION,
        }

        # 映射MCP服务器类型到领域
        domain_mapping = {
            "patent_search": ["patent", "legal"],
            "academic_search": ["academic", "research"],
            "patent_download": ["patent", "document"],
            "map_service": ["location", "geography"],
            "ai_service": ["ai", "nlp"],
            "browser_automation": ["web", "automation"],
            "version_control": ["development", "git"],
        }

        category = category_mapping.get(service.server_type, ToolCategory.MCP_SERVICE)
        domains = domain_mapping.get(service.server_type, ["all"])

        for tool_name in service.available_tools:
            tool_id = f"{service.service_id}.{tool_name}"

            # 创建工具定义
            tool = ToolDefinition(
                tool_id=tool_id,
                name=f"{service.name} - {tool_name}",
                description=f"MCP工具: {tool_name}",
                category=category,
                priority=ToolPriority.MEDIUM,
                capability=ToolCapability(
                    input_types=["json"],
                    output_types=["json"],
                    domains=domains,
                    task_types=["mcp_call"],
                ),
                implementation_type="mcp",
                implementation_ref=f"{service.service_id}:{tool_name}",
                config={
                    "service_id": service.service_id,
                    "host": service.host,
                    "port": service.port,
                    "protocol": service.protocol,
                },
                dependencies=[service.service_id],
                tags={"mcp", service.server_type, tool_name},
            )

            self.tool_registry.register(tool)

            logger.debug(f"   🔧 工具已自动注册: {tool_id}")

    def get_service(self, service_id: str) -> MCPServiceInfo | None:
        """
        获取MCP服务信息

        Args:
            service_id: 服务ID

        Returns:
            MCPServiceInfo对象,如果不存在返回None
        """
        return self._services.get(service_id)

    def list_services(
        self, status_filter: MCPServiceStatus | None = None
    ) -> list[MCPServiceInfo]:
        """
        列出所有MCP服务

        Args:
            status_filter: 状态过滤器 (可选)

        Returns:
            MCP服务列表
        """
        services = list(self._services.values())

        if status_filter:
            services = [s for s in services if s.status == status_filter]

        return services

    def get_metrics(self, service_id: str, tool_name: str) -> MCPCallMetrics | None:
        """
        获取MCP调用指标

        Args:
            service_id: 服务ID
            tool_name: 工具名称

        Returns:
            MCPCallMetrics对象,如果不存在返回None
        """
        key = f"{service_id}.{tool_name}"
        return self._metrics.get(key)

    def update_metrics(
        self,
        service_id: str,
        tool_name: str,
        execution_time: float,
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        """
        更新MCP调用指标

        Args:
            service_id: 服务ID
            tool_name: 工具名称
            execution_time: 执行时间(秒)
            success: 是否成功
            error: 错误信息 (可选)
        """
        key = f"{service_id}.{tool_name}"

        if key not in self._metrics:
            self._metrics[key] = MCPCallMetrics(service_id=service_id, tool_name=tool_name)

        self._metrics[key].update(execution_time, success, error)

    async def call_mcp_tool(
        self, service_id: str, tool_name: str, parameters: dict[str, Any], retry_count: int = 0
    ) -> dict[str, Any]:
        """
        调用MCP工具(带重试)

        Args:
            service_id: 服务ID
            tool_name: 工具名称
            parameters: 调用参数
            retry_count: 当前重试次数

        Returns:
            调用结果
        """
        service = self.get_service(service_id)

        if not service:
            raise ValueError(f"MCP服务不存在: {service_id}")

        start_time = datetime.now()
        result = {"success": False, "data": None, "error": None}

        try:
            # 这里应该调用实际的MCP服务
            # 暂时使用模拟实现
            result = await self._execute_mcp_call(service, tool_name, parameters)

            # 记录成功指标
            execution_time = (datetime.now() - start_time).total_seconds()
            self.update_metrics(service_id, tool_name, execution_time, True)

            # 同步更新工具注册中心的性能指标
            tool_id = f"{service_id}.{tool_name}"
            self.tool_registry.update_tool_performance(tool_id, execution_time, True)

            return result

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)

            # 记录失败指标
            self.update_metrics(service_id, tool_name, execution_time, False, error_msg)

            # 同步更新工具注册中心的性能指标
            tool_id = f"{service_id}.{tool_name}"
            self.tool_registry.update_tool_performance(tool_id, execution_time, False)

            # 检查是否应该重试
            if self.retry_policy.should_retry(error_msg, retry_count):
                delay = self.retry_policy.get_delay(retry_count)

                logger.warning(
                    f"⚠️ MCP调用失败,{delay}秒后重试 ({retry_count + 1}/{self.retry_policy.max_retries}): "
                    f"{service_id}.{tool_name} - {error_msg}"
                )

                await asyncio.sleep(delay)
                return await self.call_mcp_tool(service_id, tool_name, parameters, retry_count + 1)
            else:
                logger.error(f"❌ MCP调用最终失败: {service_id}.{tool_name} - {error_msg}")
                return {"success": False, "data": None, "error": error_msg, "retries": retry_count}

    async def _execute_mcp_call(
        self, service: MCPServiceInfo, tool_name: str, parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """
        执行MCP调用(实际实现)

        Args:
            service: MCP服务信息
            tool_name: 工具名称
            parameters: 调用参数

        Returns:
            调用结果
        """
        # TODO: 实现实际的MCP调用逻辑
        # 这里需要根据service的协议类型选择不同的调用方式
        # - stdio: 通过子进程调用
        # - http: 通过HTTP API调用

        # 暂时返回模拟结果
        logger.debug(f"🔧 模拟MCP调用: {service.service_id}.{tool_name}")

        await asyncio.sleep(0.1)  # 模拟网络延迟

        return {
            "success": True,
            "data": {"result": f"Mock result from {tool_name}", "parameters": parameters},
            "error": None,
        }

    def get_service_statistics(self) -> dict[str, Any]:
        """
        获取服务统计信息

        Returns:
            统计信息字典
        """
        total_services = len(self._services)
        running_services = sum(
            1 for s in self._services.values() if s.status == MCPServiceStatus.RUNNING
        )

        total_calls = sum(m.total_calls for m in self._metrics.values())
        total_success = sum(m.successful_calls for m in self._metrics.values())
        overall_success_rate = total_success / total_calls if total_calls > 0 else 0.0

        return {
            "total_services": total_services,
            "running_services": running_services,
            "stopped_services": total_services - running_services,
            "total_calls": total_calls,
            "total_success": total_success,
            "total_failures": total_calls - total_success,
            "overall_success_rate": overall_success_rate,
        }


__all__ = [
    "MCPCallMetrics",
    "MCPRetryPolicy",
    "MCPServiceInfo",
    "MCPServiceRegistry",
    "MCPServiceStatus",
]
