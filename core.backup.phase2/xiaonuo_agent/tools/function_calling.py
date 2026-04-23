#!/usr/bin/env python3
from __future__ import annotations
"""
Function Calling工具调用系统
支持工具定义、注册、调用和结果处理

核心功能:
1. 工具定义:定义工具接口和参数schema
2. 工具注册:动态注册可用工具
3. 工具调用:执行工具并返回结果
4. 参数验证:验证输入参数
5. 结果处理:处理和格式化结果

作者: Athena平台团队
创建时间: 2026-01-22
版本: v2.0.0
"""

import asyncio
import hashlib
import inspect
import json
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Union, get_type_hints

logger = logging.getLogger(__name__)


class ToolStatus(Enum):
    """工具状态"""

    AVAILABLE = "available"
    BUSY = "busy"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class ToolParameter:
    """工具参数定义"""

    name: str
    type: str  # 参数类型
    description: str
    required: bool = True
    default: Any = None
    enum: list[Any] | None = None  # 枚举值
    format: str | None = None  # 格式要求

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        param_dict = {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "required": self.required,
        }
        if self.default is not None:
            param_dict["default"] = self.default
        if self.enum:
            param_dict["enum"] = self.enum
        if self.format:
            param_dict["format"] = self.format
        return param_dict


@dataclass
class ToolDefinition:
    """工具定义"""

    name: str  # 工具名称
    description: str  # 工具描述
    parameters: list[ToolParameter]  # 参数列表
    function: Callable  # 实际函数
    category: str = "general"  # 工具分类
    status: ToolStatus = ToolStatus.AVAILABLE
    timeout: float = 30.0  # 超时时间(秒)
    rate_limit: int | None = None  # 速率限制(每分钟调用次数)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "parameters": [p.to_dict() for p in self.parameters],
            "status": self.status.value,
            "timeout": self.timeout,
            "metadata": self.metadata,
        }


@dataclass
class ToolCallResult:
    """工具调用结果"""

    call_id: str
    tool_name: str
    success: bool
    result: Any
    error_message: str | None = None
    execution_time: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "call_id": self.call_id,
            "tool_name": self.tool_name,
            "success": self.success,
            "result": str(self.result)[:500] if self.result else None,
            "error": self.error_message,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp,
        }


@dataclass
class ToolCallRecord:
    """工具调用记录"""

    call_id: str
    tool_name: str
    parameters: dict[str, Any]
    result: ToolCallResult
    caller: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class FunctionCallingSystem:
    """
    Function Calling工具调用系统

    核心功能:
    1. 工具注册:动态注册可用工具
    2. 工具发现:查找匹配的工具
    3. 工具调用:执行工具并处理结果
    4. 参数验证:验证输入参数
    5. 调用历史:记录所有工具调用

    特点:
    - 支持同步和异步工具
    - 自动参数验证
    - 超时和错误处理
    - 调用历史和统计
    """

    def __init__(self):
        """初始化Function Calling系统"""
        # 工具注册表
        self._tools: dict[str, ToolDefinition] = {}

        # 调用历史
        self._call_history: list[ToolCallRecord] = []

        # 调用统计
        self._call_stats: dict[str, dict[str, int]] = {}

        # 速率限制跟踪
        self._rate_limit_tracker: dict[str, list[float]] = {}

        logger.info("🔧 Function Calling系统初始化")

    def register_tool(
        self,
        name: str,
        description: str,
        function: Callable,
        parameters: list[ToolParameter] | None = None,
        category: str = "general",
        timeout: float = 30.0,
        rate_limit: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ToolDefinition:
        """
        注册工具

        Args:
            name: 工具名称
            description: 工具描述
            function: 工具函数
            parameters: 参数定义(自动推断)
            category: 工具分类
            timeout: 超时时间
            rate_limit: 速率限制
            metadata: 元数据

        Returns:
            工具定义
        """
        # 如果没有提供参数定义,自动从函数推断
        if parameters is None:
            parameters = self._infer_parameters(function)

        tool = ToolDefinition(
            name=name,
            description=description,
            parameters=parameters,
            function=function,
            category=category,
            timeout=timeout,
            rate_limit=rate_limit,
            metadata=metadata or {},
        )

        self._tools[name] = tool
        self._call_stats[name] = {"total_calls": 0, "successful_calls": 0, "failed_calls": 0}

        logger.info(f"✅ 工具注册: {name} ({category})")

        return tool

    def register_tool_from_function(
        self, func: Callable, category: str = "general", **kwargs
    ) -> ToolDefinition:
        """
        从函数直接注册工具

        Args:
            func: 函数对象
            category: 工具分类
            **kwargs: 其他参数

        Returns:
            工具定义
        """
        name = kwargs.get("name", func.__name__)
        description = kwargs.get("description", func.__doc__ or f"Tool: {name}")

        return self.register_tool(
            name=name, description=description, function=func, category=category, **kwargs
        )

    async def call_tool(
        self,
        tool_name: str,
        parameters: dict[str, Any],        timeout: float | None = None,
        caller: str | None = None,
    ) -> ToolCallResult:
        """
        调用工具

        Args:
            tool_name: 工具名称
            parameters: 参数字典
            timeout: 超时时间(覆盖默认值)
            caller: 调用者标识

        Returns:
            调用结果
        """
        call_id = (
            f"call_{int(time.time() * 1000)}_{hashlib.md5(tool_name.encode('utf-8'), usedforsecurity=False).hexdigest()[:8]}"
        )
        start_time = time.time()

        # 检查工具是否存在
        if tool_name not in self._tools:
            result = ToolCallResult(
                call_id=call_id,
                tool_name=tool_name,
                success=False,
                result=None,
                error_message=f"工具 '{tool_name}' 不存在",
            )
            self._record_call(call_id, tool_name, parameters, result, caller)
            return result

        tool = self._tools[tool_name]

        # 检查工具状态
        if tool.status != ToolStatus.AVAILABLE:
            result = ToolCallResult(
                call_id=call_id,
                tool_name=tool_name,
                success=False,
                result=None,
                error_message=f"工具 '{tool_name}' 状态为 {tool.status.value}",
            )
            self._record_call(call_id, tool_name, parameters, result, caller)
            return result

        # 检查速率限制
        if not self._check_rate_limit(tool_name):
            result = ToolCallResult(
                call_id=call_id,
                tool_name=tool_name,
                success=False,
                result=None,
                error_message=f"工具 '{tool_name}' 达到速率限制",
            )
            self._record_call(call_id, tool_name, parameters, result, caller)
            return result

        # 验证参数
        validation_error = self._validate_parameters(tool, parameters)
        if validation_error:
            result = ToolCallResult(
                call_id=call_id,
                tool_name=tool_name,
                success=False,
                result=None,
                error_message=f"参数验证失败: {validation_error}",
            )
            self._record_call(call_id, tool_name, parameters, result, caller)
            return result

        # 执行工具
        # 在try块之前初始化exec_timeout,确保在异常处理中可用
        exec_timeout = timeout or tool.timeout

        try:
            # 异步执行
            if asyncio.iscoroutinefunction(tool.function):
                result_value = await asyncio.wait_for(
                    tool.function(**parameters), timeout=exec_timeout
                )
            else:
                # 同步函数,在线程池中执行
                loop = asyncio.get_event_loop()
                result_value = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: tool.function(**parameters)),
                    timeout=exec_timeout,
                )

            execution_time = time.time() - start_time

            # 创建成功结果
            call_result = ToolCallResult(
                call_id=call_id,
                tool_name=tool_name,
                success=True,
                result=result_value,
                execution_time=execution_time,
            )

            # 更新统计
            self._call_stats[tool_name]["total_calls"] += 1
            self._call_stats[tool_name]["successful_calls"] += 1

            logger.info(f"✅ 工具调用成功: {tool_name} (耗时={execution_time:.2f}s)")

        except asyncio.TimeoutError:
            call_result = ToolCallResult(
                call_id=call_id,
                tool_name=tool_name,
                success=False,
                result=None,
                error_message=f"工具调用超时 (>{exec_timeout}s)",
                execution_time=time.time() - start_time,
            )
            self._call_stats[tool_name]["total_calls"] += 1
            self._call_stats[tool_name]["failed_calls"] += 1
            logger.error(f"⏱️  工具调用超时: {tool_name}")

        except Exception as e:
            call_result = ToolCallResult(
                call_id=call_id,
                tool_name=tool_name,
                success=False,
                result=None,
                error_message=str(e),
                execution_time=time.time() - start_time,
            )
            self._call_stats[tool_name]["total_calls"] += 1
            self._call_stats[tool_name]["failed_calls"] += 1
            logger.error(f"❌ 工具调用失败: {tool_name} - {e}")

        # 记录调用
        self._record_call(call_id, tool_name, parameters, call_result, caller)

        return call_result

    async def call_tool_batch(
        self, calls: list[dict[str, Any]], caller: str | None = None
    ) -> list[ToolCallResult]:
        """
        批量调用工具

        Args:
            calls: 调用列表 [{"tool_name": str, "parameters": dict}, ...]
            caller: 调用者标识

        Returns:
            调用结果列表
        """
        tasks = []
        for call in calls:
            task = self.call_tool(
                tool_name=call["tool_name"], parameters=call.get("parameters", {}), caller=caller
            )
            tasks.append(task)

        return await asyncio.gather(*tasks)

    def get_tool(self, tool_name: str) -> ToolDefinition | None:
        """获取工具定义"""
        return self._tools.get(tool_name)

    def list_tools(
        self, category: str | None = None, status: ToolStatus | None = None
    ) -> list[ToolDefinition]:
        """
        列出工具

        Args:
            category: 工具分类过滤
            status: 工具状态过滤

        Returns:
            工具列表
        """
        tools = list(self._tools.values())

        if category:
            tools = [t for t in tools if t.category == category]

        if status:
            tools = [t for t in tools if t.status == status]

        return tools

    def search_tools(self, query: str) -> list[ToolDefinition]:
        """
        搜索工具

        Args:
            query: 搜索关键词

        Returns:
            匹配的工具列表
        """
        query_lower = query.lower()
        matching_tools = []

        for tool in self._tools.values():
            # 搜索名称和描述
            if query_lower in tool.name.lower() or query_lower in tool.description.lower():
                matching_tools.append(tool)

        return matching_tools

    def _infer_parameters(self, func: Callable) -> list[ToolParameter]:
        """从函数推断参数定义"""
        parameters = []

        try:
            # 获取函数签名
            sig = inspect.signature(func)
            type_hints = get_type_hints(func)

            for param_name, param in sig.parameters.items():
                # 跳过self参数
                if param_name == "self":
                    continue

                # 获取类型
                param_type = type_hints.get(param_name, str)
                type_str = self._type_to_string(param_type)

                # 创建参数定义
                tool_param = ToolParameter(
                    name=param_name,
                    type=type_str,
                    description=f"Parameter: {param_name}",
                    required=param.default == param.empty,
                    default=param.default if param.default != param.empty else None,
                )

                parameters.append(tool_param)

        except Exception as e:
            logger.warning(f"⚠️  参数推断失败: {e}")

        return parameters

    def _type_to_string(self, type_hint: Any) -> str:
        """将类型提示转换为字符串"""
        type_map = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object",
            type(None): "null",
        }

        if type_hint in type_map:
            return type_map[type_hint]

        # 处理Optional类型
        if hasattr(type_hint, "__origin__"):
            origin = type_hint.__origin__
            if origin == Union:
                # Optional[T] = Union[T, None]
                args = type_hint.__args__
                if len(args) == 2 and type(None) in args:
                    return self._type_to_string(args[0])

        return "string"  # 默认

    def _validate_parameters(
        self, tool: ToolDefinition, parameters: dict[str, Any]
    ) -> str | None:
        """验证参数"""
        # 检查必需参数
        for param in tool.parameters:
            if param.required and param.name not in parameters:
                return f"缺少必需参数: {param.name}"

            # 检查枚举值
            if param.name in parameters and param.enum:
                if parameters[param.name] not in param.enum:
                    return f"参数 {param.name} 必须是以下值之一: {param.enum}"

        return None

    def _check_rate_limit(self, tool_name: str) -> bool:
        """检查速率限制"""
        tool = self._tools.get(tool_name)
        if not tool or not tool.rate_limit:
            return True

        current_time = time.time()

        # 初始化跟踪记录
        if tool_name not in self._rate_limit_tracker:
            self._rate_limit_tracker[tool_name] = []

        # 清理1分钟前的记录
        self._rate_limit_tracker[tool_name] = [
            t for t in self._rate_limit_tracker[tool_name] if current_time - t < 60
        ]

        # 检查限制
        if len(self._rate_limit_tracker[tool_name]) >= tool.rate_limit:
            return False

        # 记录此次调用
        self._rate_limit_tracker[tool_name].append(current_time)
        return True

    def _record_call(
        self,
        call_id: str,
        tool_name: str,
        parameters: dict[str, Any],        result: ToolCallResult,
        caller: str,
    ):
        """记录调用"""
        record = ToolCallRecord(
            call_id=call_id,
            tool_name=tool_name,
            parameters=parameters,
            result=result,
            caller=caller,
        )

        self._call_history.append(record)

        # 限制历史记录大小
        if len(self._call_history) > 1000:
            self._call_history = self._call_history[-1000:]

    def get_call_history(
        self, tool_name: str | None = None, limit: int = 50
    ) -> list[ToolCallRecord]:
        """获取调用历史"""
        history = self._call_history

        if tool_name:
            history = [r for r in history if r.tool_name == tool_name]

        return history[-limit:]

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        total_calls = sum(s["total_calls"] for s in self._call_stats.values())
        successful_calls = sum(s["successful_calls"] for s in self._call_stats.values())

        return {
            "total_tools": len(self._tools),
            "total_calls": total_calls,
            "successful_calls": successful_calls,
            "failed_calls": total_calls - successful_calls,
            "success_rate": successful_calls / total_calls if total_calls > 0 else 0,
            "tool_stats": self._call_stats,
        }

    def export_tools_schema(self, filepath: str):
        """导出工具Schema(用于LLM)"""
        schema = {
            "tools": [tool.to_dict() for tool in self._tools.values()],
            "exported_at": datetime.now().isoformat(),
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(schema, f, ensure_ascii=False, indent=2)

        logger.info(f"📁 工具Schema已导出: {filepath}")


# 全局Function Calling系统实例
_function_calling_system: FunctionCallingSystem | None = None


async def get_function_calling_system() -> FunctionCallingSystem:
    """获取全局Function Calling系统实例"""
    global _function_calling_system
    if _function_calling_system is None:
        _function_calling_system = FunctionCallingSystem()
    return _function_calling_system


# 便捷装饰器
def tool(
    name: str | None = None,
    description: str | None = None,
    category: str = "general",
    timeout: float = 30.0,
    rate_limit: int | None = None,
):
    """
    工具装饰器

    用法:
    @tool(name="my_tool", description="My tool description")
    async def my_function(param1: str, param2: int) -> str:
        return "result"
    """

    def decorator(func: Callable) -> Callable:
        # 保存原始函数
        original_func = func

        # 生成工具名称
        tool_name = name or func.__name__
        tool_description = description or func.__doc__ or f"Tool: {tool_name}"

        # 注册为工具(延迟到系统初始化后)
        async def register_wrapper():
            system = await get_function_calling_system()
            system.register_tool(
                name=tool_name,
                description=tool_description,
                function=original_func,
                category=category,
                timeout=timeout,
                rate_limit=rate_limit,
            )

        # 标记函数需要注册
        func._tool_register = register_wrapper

        return func

    return decorator
