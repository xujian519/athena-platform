#!/usr/bin/env python3
"""
Athena平台工具系统 v2.0
基于Claude Code架构设计的增强工具接口

核心特性:
1. 完整的工具生命周期管理
2. 输入/输出模式验证（使用Pydantic）
3. 权限和安全检查
4. 进度回调支持
5. 工具元数据和分类
6. 并发安全性和只读属性
7. MCP集成支持

Author: Athena平台团队
Date: 2026-04-20
Version: v2.0.0
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
)
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# 类型变量
Input = TypeVar("Input")
Output = TypeVar("Output")
Progress = TypeVar("Progress")


class PermissionMode(Enum):
    """权限模式"""
    DEFAULT = "default"  # 默认模式，未匹配规则时需要用户确认
    AUTO = "auto"  # 自动模式，未匹配规则时自动拒绝
    BYPASS = "bypass"  # 绕过模式，允许所有调用（谨慎使用）


class InterruptBehavior(Enum):
    """中断行为"""
    CANCEL = "cancel"  # 取消操作
    BLOCK = "block"  # 阻塞操作


class ToolValidationResult(BaseModel):
    """工具验证结果"""
    is_valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ToolResult(BaseModel, Generic[Output]):
    """工具执行结果"""
    success: bool
    output: Output | None = None
    error: str | None = None
    execution_time: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True


@dataclass
class ToolContext:
    """
    工具执行上下文

    类似Claude Code的ToolUseContext，提供执行环境信息。
    """

    # 会话信息
    session_id: str
    agent_id: str | None = None
    agent_type: str | None = None

    # 系统配置
    model: str = "claude-sonnet-4-6"
    debug_mode: bool = False
    timeout: float = 30.0

    # 资源限制
    max_result_size_chars: int = 100_000
    file_reading_limits: dict[str, int] = field(default_factory=dict)
    glob_limits: dict[str, int] = field(default_factory=dict)

    # MCP集成
    mcp_clients: dict[str, Any] = field(default_factory=dict)
    mcp_resources: dict[str, Any] = field(default_factory=dict)

    # 权限和安全
    permission_mode: PermissionMode = PermissionMode.DEFAULT
    working_directory: str = ""

    # 取消控制
    abort_controller: Any | None = None

    # 消息上下文
    messages: list[dict[str, Any]] = field(default_factory=list)

    # 父消息（用于子代理）
    parent_message: dict[str, Any] | None = None

    def is_aborted(self) -> bool:
        """检查是否已取消"""
        if self.abort_controller:
            # 假设abort_controller有cancelled属性
            return getattr(self.abort_controller, 'cancelled', False)
        return False


@dataclass
class ToolMetadata:
    """
    工具元数据

    类似Claude Code的工具定义，包含工具的描述性信息。
    """

    # 基本信息
    name: str
    description: str
    category: str
    priority: str = "medium"

    # 别名和搜索
    aliases: list[str] = field(default_factory=list)
    search_hint: str | None = None

    # 模式定义（使用Pydantic模型）
    input_schema: type[BaseModel] | None = None
    output_schema: type[BaseModel] | None = None

    # JSON模式（用于MCP）
    input_json_schema: dict[str, Any] | None = None

    # 限制和约束
    max_result_size_chars: int = 100_000
    timeout: float = 30.0

    # 安全属性
    is_read_only: bool = False
    is_concurrency_safe: bool = True
    is_destructive: bool = False
    is_search_or_read_command: bool = False

    # 行为特性
    interrupt_behavior: InterruptBehavior | None = None
    is_open_world: bool = False
    requires_user_interaction: bool = False

    # 加载策略
    should_defer: bool = False  # 需要工具搜索
    always_load: bool = False  # 跳过延迟加载
    strict: bool = False  # 严格模式

    # MCP信息
    is_mcp: bool = False
    is_lsp: bool = False
    mcp_info: dict[str, str] | None = None


class BaseTool(ABC, Generic[Input, Output, Progress]):
    """
    基础工具接口

    基于Claude Code的Tool接口设计的Python版本。

    所有工具都应继承此类并实现所需方法。
    """

    def __init__(self, metadata: ToolMetadata):
        """
        初始化工具

        Args:
            metadata: 工具元数据
        """
        self.metadata = metadata
        self._logger = logging.getLogger(f"tools.{metadata.name}")

    @abstractmethod
    async def call(
        self,
        args: Input,
        context: ToolContext,
        can_use_tool: Callable[[str], bool],
        on_progress: Callable[[Progress], None] | None = None,
    ) -> ToolResult[Output]:
        """
        执行工具

        Args:
            args: 输入参数
            context: 执行上下文
            can_use_tool: 检查是否可以使用其他工具的函数
            on_progress: 进度回调

        Returns:
            工具执行结果
        """
        pass

    async def description(self, input: Input, context: ToolContext) -> str:
        """
        生成工具描述

        Args:
            input: 输入参数
            context: 执行上下文

        Returns:
            工具描述文本
        """
        return self.metadata.description

    def is_enabled(self) -> bool:
        """检查工具是否启用"""
        return True

    def is_read_only(self, input: Input) -> bool:
        """检查工具是否只读"""
        return self.metadata.is_read_only

    def is_concurrency_safe(self, input: Input) -> bool:
        """检查工具是否并发安全"""
        return self.metadata.is_concurrency_safe

    def is_destructive(self, input: Input) -> bool:
        """检查工具是否具有破坏性"""
        return self.metadata.is_destructive

    def interrupt_behavior(self) -> InterruptBehavior | None:
        """返回中断行为"""
        return self.metadata.interrupt_behavior

    def is_search_or_read_command(
        self, input: Input
    ) -> dict[str, bool] | None:
        """
        检查是否为搜索或读命令

        Returns:
            包含is_search, is_read, is_list的字典，或None
        """
        if self.metadata.is_search_or_read_command:
            return {
                "is_search": True,
                "is_read": True,
                "is_list": False,
            }
        return None

    def is_open_world(self, input: Input) -> bool:
        """检查是否为开放世界工具"""
        return self.metadata.is_open_world

    def requires_user_interaction(self) -> bool:
        """检查是否需要用户交互"""
        return self.metadata.requires_user_interaction

    async def validate_input(
        self, input: Input, context: ToolContext
    ) -> ToolValidationResult:
        """
        验证输入参数

        Args:
            input: 输入参数
            context: 执行上下文

        Returns:
            验证结果
        """
        errors = []
        warnings = []

        # 使用Pydantic模式验证
        if self.metadata.input_schema:
            try:
                if isinstance(input, dict):
                    self.metadata.input_schema(**input)
                elif not isinstance(input, self.metadata.input_schema):
                    errors.append(
                        f"输入类型不匹配，期望 {self.metadata.input_schema.__name__}"
                    )
            except Exception as e:
                errors.append(f"输入验证失败: {str(e)}")

        return ToolValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def inputs_equivalent(self, a: Input, b: Input) -> bool:
        """
        比较两个输入是否等效

        Args:
            a: 输入A
            b: 输入B

        Returns:
            是否等效
        """
        return a == b


class ToolRegistry:
    """
    工具注册表

    管理所有工具的注册、查找和调用。
    """

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}
        self._aliases: dict[str, str] = {}  # alias -> tool_name
        self._lock = asyncio.Lock()
        self._logger = logging.getLogger(f"{__name__}.ToolRegistry")

    async def register(self, tool: BaseTool) -> None:
        """
        注册工具

        Args:
            tool: 工具实例
        """
        async with self._lock:
            name = tool.metadata.name
            self._tools[name] = tool

            # 注册别名
            for alias in tool.metadata.aliases:
                self._aliases[alias] = name

            self._logger.info(f"✅ 工具已注册: {name}")

    def get(self, name: str) -> BaseTool | None:
        """
        获取工具

        Args:
            name: 工具名称或别名

        Returns:
            工具实例，如果不存在返回None
        """
        # 检查别名
        tool_name = self._aliases.get(name, name)
        return self._tools.get(tool_name)

    def list_tools(self) -> list[str]:
        """列出所有工具名称"""
        return list(self._tools.keys())

    async def call_tool(
        self,
        name: str,
        args: Any,
        context: ToolContext,
        can_use_tool: Callable[[str], bool] | None = None,
        on_progress: Callable[[Any], None] | None = None,
    ) -> ToolResult:
        """
        调用工具

        Args:
            name: 工具名称
            args: 输入参数
            context: 执行上下文
            can_use_tool: 检查是否可以使用其他工具
            on_progress: 进度回调

        Returns:
            工具执行结果
        """
        tool = self.get(name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"工具不存在: {name}",
            )

        if not tool.is_enabled():
            return ToolResult(
                success=False,
                error=f"工具未启用: {name}",
            )

        # 验证输入
        validation = await tool.validate_input(args, context)
        if not validation.is_valid:
            return ToolResult(
                success=False,
                error=f"输入验证失败: {', '.join(validation.errors)}",
            )

        # 调用工具
        try:
            result = await tool.call(args, context, can_use_tool or (lambda _: True), on_progress)
            return result
        except Exception as e:
            self._logger.error(f"工具执行失败 {name}: {e}")
            return ToolResult(
                success=False,
                error=str(e),
            )


# 导出
__all__ = [
    "BaseTool",
    "ToolContext",
    "ToolMetadata",
    "ToolResult",
    "ToolValidationResult",
    "ToolRegistry",
    "PermissionMode",
    "InterruptBehavior",
]
