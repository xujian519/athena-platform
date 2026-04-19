#!/usr/bin/env python3
from __future__ import annotations
"""
Athena智能体工具调用管理器
Agent Tool Call Manager

统一管理18个工具的调用、执行、监控和验证

核心功能:
1. 统一工具调用接口
2. 调用日志记录
3. 错误处理机制
4. 结果验证
5. 性能监控

作者: Athena平台团队
创建时间: 2025-12-29
版本: v1.0.0
"""

import asyncio
import json
import time
import traceback
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from core.logging_config import setup_logging

# 导入统一的工具定义
from .base import ToolCategory, ToolDefinition
from .hooks import HookContext, HookEvent, HookRegistry, register_default_hooks
from .feature_gates import feature  # P2-2: 导入功能门控

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


class CallStatus(Enum):
    """调用状态"""

    PENDING = "pending"  # 等待执行
    RUNNING = "running"  # 执行中
    SUCCESS = "success"  # 成功
    FAILED = "failed"  # 失败
    TIMEOUT = "timeout"  # 超时
    CANCELLED = "cancelled"  # 已取消


@dataclass
class ToolCallRequest:
    """工具调用请求"""

    request_id: str
    tool_name: str
    parameters: dict[str, Any]
    context: dict[str, Any] | None = None
    priority: int = 2  # 1=high, 2=medium, 3=low
    timeout: float = 30.0  # 秒
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ToolCallResult:
    """工具调用结果"""

    request_id: str
    tool_name: str
    status: CallStatus
    result: Any | None = None
    error: str | None = None
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


class ToolCallManager:
    """
    工具调用管理器(增强版)

    核心功能:
    1. 工具注册和发现
    2. 统一调用接口
    3. 调用日志记录
    4. 错误处理和重试
    5. 结果验证
    6. 性能监控
    7. 速率限制(新增)
    8. 内存管理优化(新增)
    """

    def __init__(
        self,
        log_dir: str = "logs/tool_calls",
        max_history: int = 1000,
        enable_rate_limit: bool = True,
        max_calls_per_minute: int = 100,
        enable_hooks: bool = True,
    ):
        """
        初始化工具调用管理器

        Args:
            log_dir: 日志目录
            max_history: 最大历史记录数(防止内存泄漏)
            enable_rate_limit: 是否启用速率限制
            max_calls_per_minute: 每分钟最大调用次数
            enable_hooks: 是否启用Hook系统
        """
        self.tools: dict[str, ToolDefinition] = {}
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 🔧 内存优化:使用deque限制历史记录大小
        self.call_history: deque = deque(maxlen=max_history)
        self.max_history = max_history

        # 🚦 速率限制
        self.enable_rate_limit = enable_rate_limit
        if enable_rate_limit:
            try:
                from .rate_limiter import RateLimiter

                self.rate_limiter = RateLimiter(max_calls=max_calls_per_minute, period=60.0)
                logger.info(f"✅ 速率限制已启用: {max_calls_per_minute}次/分钟")
            except ImportError:
                logger.warning("⚠️ 无法导入rate_limiter,速率限制未启用")
                self.enable_rate_limit = False
                self.rate_limiter = None
        else:
            self.rate_limiter = None

        # 🎣 Hook系统
        self.enable_hooks = enable_hooks
        self.hook_registry: HookRegistry | None = None
        if enable_hooks:
            self.hook_registry = HookRegistry()
            # 注册默认Hook
            register_default_hooks(self.hook_registry)
            logger.info("✅ Hook系统已启用")

        # 统计信息
        self.stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "timeout_calls": 0,
            "avg_execution_time": 0.0,
            "rate_limited_calls": 0,  # 被速率限制的调用次数
            "hook_blocked_calls": 0,  # 被Hook阻止的调用次数
        }

        # 工具性能统计
        self.tool_stats: dict[str, dict[str, Any]] = {}

        logger.info("🔧 工具调用管理器初始化完成(增强版+Hook系统)")

    def register_tool(self, tool: ToolDefinition) -> Any:
        """注册工具"""
        self.tools[tool.tool_id] = tool
        self.tool_stats[tool.tool_id] = {"calls": 0, "successes": 0, "failures": 0, "avg_time": 0.0}
        logger.info(f"✅ 工具已注册: {tool.name} ({tool.category.value})")

    def get_tool(self, tool_name: str) -> ToolDefinition | None:
        """获取工具定义"""
        return self.tools.get(tool_name)

    def list_tools(self, category: ToolCategory | None = None) -> list[str]:
        """列出可用工具"""
        if category:
            return [name for name, tool in self.tools.items() if tool.category == category]
        return list(self.tools.keys())

    async def call_tool(
        self,
        tool_name: str,
        parameters: dict[str, Any],        context: dict[str, Any] | None = None,
        priority: int = 2,
        timeout: float | None = None,
    ) -> ToolCallResult:
        """
        调用工具(统一接口,带速率限制)

        Args:
            tool_name: 工具名称
            parameters: 参数字典
            context: 上下文信息
            priority: 优先级 (1=high, 2=medium, 3=low)
            timeout: 超时时间(秒)

        Returns:
            ToolCallResult: 调用结果
        """
        request_id = str(uuid.uuid4())
        request = ToolCallRequest(
            request_id=request_id,
            tool_name=tool_name,
            parameters=parameters,
            context=context,
            priority=priority,
        )

        # 🚦 速率限制检查
        if self.enable_rate_limit and self.rate_limiter:
            allowed = await self.rate_limiter.acquire(timeout=0)
            if not allowed:
                logger.warning(f"🚫 速率限制:工具调用被拒绝 {tool_name}")
                result = ToolCallResult(
                    request_id=request_id,
                    tool_name=tool_name,
                    status=CallStatus.FAILED,
                    error="速率限制:调用过于频繁,请稍后重试",
                    execution_time=0.0,
                )
                self.stats["rate_limited_calls"] += 1
                self._record_result(result)
                return result

        # 检查工具是否存在
        tool = self.get_tool(tool_name)
        if not tool:
            result = ToolCallResult(
                request_id=request_id,
                tool_name=tool_name,
                status=CallStatus.FAILED,
                error=f"工具不存在: {tool_name}",
            )
            self._record_result(result)
            return result

        # 验证必需参数
        missing_params = [p for p in tool.required_params if p not in parameters]
        if missing_params:
            result = ToolCallResult(
                request_id=request_id,
                tool_name=tool_name,
                status=CallStatus.FAILED,
                error=f"缺少必需参数: {missing_params}",
            )
            self._record_result(result)
            return result

        # 设置超时
        effective_timeout = timeout or tool.timeout

        # 🎣 执行Pre-tool-use Hooks
        if self.enable_hooks and self.hook_registry:
            hook_context = HookContext(
                tool_name=tool_name,
                parameters=parameters,
                context=context,
                request_id=request_id,
            )

            try:
                hook_result = await self.hook_registry.execute_hooks(
                    HookEvent.PRE_TOOL_USE, hook_context
                )

                # Hook阻止调用
                if not hook_result.should_proceed:
                    logger.warning(
                        f"🚫 工具调用被Hook阻止: {tool_name} - {hook_result.error_message}"
                    )
                    result = ToolCallResult(
                        request_id=request_id,
                        tool_name=tool_name,
                        status=CallStatus.FAILED,
                        error=hook_result.error_message or "Hook阻止调用",
                        execution_time=0.0,
                        metadata=hook_result.metadata,
                    )
                    self.stats["hook_blocked_calls"] += 1
                    self._record_result(result)
                    return result

                # 应用修改后的参数
                if hook_result.modified_parameters:
                    parameters = hook_result.modified_parameters
                    logger.info(f"🔧 Hook修改参数: {tool_name}")

            except Exception as e:
                logger.error(f"❌ Pre-tool-use Hook执行失败: {e}")
                # Hook错误不应阻止主流程

        # 执行调用
        start_time = time.time()
        try:
            logger.info(f"🔧 调用工具: {tool_name} (request_id={request_id})")

            # 异步执行
            result = await self._execute_tool(tool, request, effective_timeout)

        except asyncio.TimeoutError:
            logger.error(f"⏰ 工具调用超时: {tool_name}")
            result = ToolCallResult(
                request_id=request_id,
                tool_name=tool_name,
                status=CallStatus.TIMEOUT,
                error=f"工具调用超时 ({effective_timeout}秒)",
                execution_time=time.time() - start_time,
            )

        except Exception as e:
            logger.error(f"❌ 工具调用失败: {tool_name} - {e}")
            result = ToolCallResult(
                request_id=request_id,
                tool_name=tool_name,
                status=CallStatus.FAILED,
                error=str(e),
                execution_time=time.time() - start_time,
                metadata={"traceback": traceback.format_exc()},
            )

        # 记录结果
        self._record_result(result)

        # 🎣 执行Post-tool-use或Tool-failure Hooks
        if self.enable_hooks and self.hook_registry:
            hook_context = HookContext(
                tool_name=tool_name,
                parameters=parameters,
                context=context,
                request_id=request_id,
                metadata=result.metadata,
            )

            try:
                if result.status == CallStatus.SUCCESS:
                    await self.hook_registry.execute_hooks(
                        HookEvent.POST_TOOL_USE, hook_context
                    )
                else:
                    await self.hook_registry.execute_hooks(
                        HookEvent.TOOL_FAILURE, hook_context
                    )
            except Exception as e:
                logger.error(f"❌ Post-tool-use Hook执行失败: {e}")

        # 记录日志
        self._write_log(request, result)

        return result

    async def _execute_tool(
        self, tool: ToolDefinition, request: ToolCallRequest, timeout: float
    ) -> ToolCallResult:
        """执行工具调用"""
        start_time = time.time()

        # 创建结果对象
        result = ToolCallResult(
            request_id=request.request_id, tool_name=request.tool_name, status=CallStatus.RUNNING
        )

        # 执行工具处理器
        try:
            # 带超时的异步执行
            tool_result = await asyncio.wait_for(
                tool.handler(request.parameters, request.context), timeout=timeout
            )

            # 成功
            result.status = CallStatus.SUCCESS
            result.result = tool_result
            result.execution_time = time.time() - start_time

            logger.info(f"✅ 工具调用成功: {request.tool_name} ({result.execution_time:.2f}秒)")

        except asyncio.TimeoutError:
            result.status = CallStatus.TIMEOUT
            result.error = f"执行超时 ({timeout}秒)"
            result.execution_time = time.time() - start_time
            raise

        except Exception as e:
            result.status = CallStatus.FAILED
            result.error = str(e)
            result.execution_time = time.time() - start_time
            raise

        return result

    def _record_result(self, result: ToolCallResult) -> Any:
        """记录调用结果"""
        # 添加到历史
        self.call_history.append(result)

        # 更新统计
        self.stats["total_calls"] += 1
        if result.status == CallStatus.SUCCESS:
            self.stats["successful_calls"] += 1
        elif result.status == CallStatus.TIMEOUT:
            self.stats["timeout_calls"] += 1
        else:
            self.stats["failed_calls"] += 1

        # 更新平均执行时间
        if result.execution_time > 0:
            current_total = self.stats["avg_execution_time"] * (self.stats["total_calls"] - 1)
            self.stats["avg_execution_time"] = (current_total + result.execution_time) / self.stats[
                "total_calls"
            ]

        # 更新工具统计
        tool_name = result.tool_name
        if tool_name in self.tool_stats:
            self.tool_stats[tool_name]["calls"] += 1
            if result.status == CallStatus.SUCCESS:
                self.tool_stats[tool_name]["successes"] += 1
            else:
                self.tool_stats[tool_name]["failures"] += 1

            current_avg = self.tool_stats[tool_name]["avg_time"]
            call_count = self.tool_stats[tool_name]["calls"]
            self.tool_stats[tool_name]["avg_time"] = (
                current_avg * (call_count - 1) + result.execution_time
            ) / call_count

    def _write_log(self, request: ToolCallRequest, result: ToolCallResult) -> Any:
        """写入调用日志"""
        log_entry = {
            "timestamp": result.timestamp.isoformat(),
            "request_id": request.request_id,
            "tool_name": request.tool_name,
            "parameters": request.parameters,
            "context": request.context,
            "priority": request.priority,
            "status": result.status.value,
            "error": result.error,
            "execution_time": result.execution_time,
            "result_summary": str(result.result)[:200] if result.result else None,
        }

        # 写入日志文件
        log_file = self.log_dir / f"tool_calls_{datetime.now().strftime('%Y%m%d')}.jsonl"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        success_rate = (
            self.stats["successful_calls"] / max(self.stats["total_calls"], 1)
            if self.stats["total_calls"] > 0
            else 0
        )

        stats_dict = {
            **self.stats,
            "success_rate": success_rate,
            "tool_count": len(self.tools),
            "tool_stats": self.tool_stats,
        }

        # 添加Hook统计
        if self.enable_hooks and self.hook_registry:
            stats_dict["hook_stats"] = self.hook_registry.get_stats()

        return stats_dict

    def get_tool_performance(self, tool_name: str) -> dict[str, Any] | None:
        """获取工具性能统计"""
        return self.tool_stats.get(tool_name)

    def get_recent_calls(self, limit: int = 10) -> list[ToolCallResult]:
        """获取最近的调用记录"""
        return self.call_history[-limit:]

    # ========================================
    # P2-2: 并行工具执行
    # ========================================

    async def call_tools_parallel(
        self,
        tool_calls: list[dict[str, Any]],
        max_concurrency: int = 10,
        context: dict[str, Any] | None = None,
    ) -> list[ToolCallResult]:
        """
        并行调用多个工具 (P2-2)

        支持依赖分析和错误隔离，无依赖的工具并行执行，有依赖的串行执行。

        Args:
            tool_calls: 工具调用列表，每个元素为 {"tool_name": str, "parameters": dict, "depends_on": list[str]}
            max_concurrency: 最大并发数
            context: 上下文信息

        Returns:
            list[ToolCallResult]: 调用结果列表

        Example:
            >>> results = await manager.call_tools_parallel([
            ...     {"tool_name": "tool1", "parameters": {"arg1": "value1"}},
            ...     {"tool_name": "tool2", "parameters": {"arg2": "value2"}, "depends_on": ["tool1"]},
            ... ])
        """
        # 🚦 检查功能门控
        if not feature("parallel_tool_execution"):
            logger.warning("⚠️ 并行工具执行功能未启用，回退到串行执行")
            return await self._call_tools_serial(tool_calls, context)

        logger.info(f"🚀 开始并行执行 {len(tool_calls)} 个工具调用")

        # 构建依赖图
        dependency_graph = self._build_dependency_graph(tool_calls)

        # 分析执行批次（无依赖的可以并行）
        execution_batches = self._analyze_execution_batches(dependency_graph)

        logger.info(f"📊 分为 {len(execution_batches)} 个执行批次")

        # 按批次执行
        all_results: list[ToolCallResult] = []

        for batch_idx, batch in enumerate(execution_batches):
            logger.info(f"⚡ 执行批次 {batch_idx + 1}/{len(execution_batches)} ({len(batch)} 个工具)")

            # 并行执行当前批次
            batch_results = await self._execute_batch(
                batch,
                tool_calls,
                max_concurrency,
                context,
            )

            all_results.extend(batch_results)

            # 检查批次是否全部成功
            batch_failures = [r for r in batch_results if r.status != CallStatus.SUCCESS]
            if batch_failures:
                logger.warning(
                    f"⚠️ 批次 {batch_idx + 1} 有 {len(batch_failures)} 个失败，继续执行后续批次"
                )

        logger.info(f"✅ 并行执行完成: {len(all_results)} 个结果")
        return all_results

    def _build_dependency_graph(self, tool_calls: list[dict[str, Any]]) -> dict[str, set[str]]:
        """
        构建依赖图

        Args:
            tool_calls: 工具调用列表

        Returns:
            dict: 依赖图 {tool_name: set[dependent_tool_names]}
        """
        graph: dict[str, set[str]] = {}

        for call in tool_calls:
            tool_name = call.get("tool_name", "")
            depends_on = call.get("depends_on", [])

            if tool_name not in graph:
                graph[tool_name] = set()

            for dep in depends_on:
                if dep not in graph:
                    graph[dep] = set()
                graph[dep].add(tool_name)

        return graph

    def _analyze_execution_batches(
        self, dependency_graph: dict[str, set[str]]
    ) -> list[list[str]]:
        """
        分析执行批次（拓扑排序）

        Args:
            dependency_graph: 依赖图

        Returns:
            list[list[str]]: 批次列表，每个批次包含可并行执行的工具名称
        """
        # 计算入度
        in_degree: dict[str, int] = {node: 0 for node in dependency_graph}
        for node in dependency_graph:
            for dependent in dependency_graph[node]:
                in_degree[dependent] += 1

        # 拓扑排序
        batches: list[list[str]] = []
        remaining = set(dependency_graph.keys())

        while remaining:
            # 找出所有入度为0的节点
            current_batch = [node for node in remaining if in_degree[node] == 0]

            if not current_batch:
                # 循环依赖，打破
                logger.warning("⚠️ 检测到循环依赖，打破循环")
                current_batch = [list(remaining)[0]]

            batches.append(current_batch)

            # 移除当前批次
            for node in current_batch:
                remaining.remove(node)
                for dependent in dependency_graph[node]:
                    in_degree[dependent] -= 1

        return batches

    async def _execute_batch(
        self,
        batch: list[str],
        tool_calls: list[dict[str, Any]],
        max_concurrency: int,
        context: dict[str, Any] | None,
    ) -> list[ToolCallResult]:
        """
        执行一个批次（并行）

        Args:
            batch: 批次工具名称列表
            tool_calls: 原始工具调用列表
            max_concurrency: 最大并发数
            context: 上下文

        Returns:
            list[ToolCallResult]: 批次执行结果
        """
        # 创建任务列表
        tasks = []
        for tool_name in batch:
            # 查找对应的工具调用
            call = next((c for c in tool_calls if c.get("tool_name") == tool_name), None)
            if call:
                task = self._execute_single_tool_safe(call, context)
                tasks.append(task)

        # 并发控制：使用信号量
        semaphore = asyncio.Semaphore(max_concurrency)

        async def execute_with_semaphore(task: asyncio.Task) -> ToolCallResult:
            async with semaphore:
                return await task

        # 并行执行
        try:
            results = await asyncio.gather(
                *[execute_with_semaphore(asyncio.create_task(task)) for task in tasks],
                return_exceptions=True,  # 不因单个失败中断全部
            )
        except Exception as e:
            logger.error(f"❌ 批次执行异常: {e}")
            results = []

        # 处理结果（异常转换为失败结果）
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                tool_name = batch[i] if i < len(batch) else "unknown"
                final_results.append(
                    ToolCallResult(
                        request_id=str(uuid.uuid4()),
                        tool_name=tool_name,
                        status=CallStatus.FAILED,
                        error=str(result),
                        execution_time=0.0,
                    )
                )
            else:
                final_results.append(result)

        return final_results

    async def _execute_single_tool_safe(
        self, call: dict[str, Any], context: dict[str, Any] | None
    ) -> ToolCallResult:
        """
        安全执行单个工具（带异常捕获）

        Args:
            call: 工具调用
            context: 上下文

        Returns:
            ToolCallResult: 执行结果
        """
        try:
            return await self.call_tool(
                tool_name=call.get("tool_name", ""),
                parameters=call.get("parameters", {}),
                context=context,
            )
        except Exception as e:
            logger.error(f"❌ 工具执行异常: {call.get('tool_name')} - {e}")
            return ToolCallResult(
                request_id=str(uuid.uuid4()),
                tool_name=call.get("tool_name", ""),
                status=CallStatus.FAILED,
                error=str(e),
                execution_time=0.0,
            )

    async def _call_tools_serial(
        self, tool_calls: list[dict[str, Any]], context: dict[str, Any] | None
    ) -> list[ToolCallResult]:
        """
        串行执行工具（回退方案）

        Args:
            tool_calls: 工具调用列表
            context: 上下文

        Returns:
            list[ToolCallResult]: 执行结果
        """
        results = []
        for call in tool_calls:
            result = await self._execute_single_tool_safe(call, context)
            results.append(result)
        return results


# 全局单例
_tool_manager: ToolCallManager | None = None


def get_tool_manager() -> ToolCallManager:
    """获取工具调用管理器单例"""
    global _tool_manager
    if _tool_manager is None:
        _tool_manager = ToolCallManager()

        # 注册真实工具
        _register_real_tools(_tool_manager)

    return _tool_manager


def _register_real_tools(manager: ToolCallManager) -> Any:
    """注册真实工具(使用真实实现)"""
    import asyncio

    from .real_tool_implementations import register_real_tools

    # 注册所有真实工具
    asyncio.run(register_real_tools(manager))

    logger.info(f"✅ 已注册 {len(manager.tools)} 个真实工具")


# 便捷函数
async def call_tool(
    tool_name: str, parameters: dict[str, Any], context: dict[str, Any] | None = None
) -> ToolCallResult:
    """便捷的工具调用函数"""
    manager = get_tool_manager()
    return await manager.call_tool(tool_name, parameters, context)


# 测试
async def main():
    """测试工具调用管理器"""
    print("🧪 测试工具调用管理器")
    print("=" * 60)

    # 获取管理器
    manager = get_tool_manager()

    # 显示工具列表
    print(f"\n🔧 可用工具 ({len(manager.tools)}个):")
    for tool_name in manager.list_tools():
        tool = manager.get_tool(tool_name)
        print(f"  - {tool_name}: {tool.description}")

    # 测试工具调用
    print("\n📞 测试工具调用:")

    # 1. 代码分析
    result = await call_tool(
        "code_analyzer", {"code": "def hello(): print('Hello')", "language": "python"}
    )
    print(f"\n1. 代码分析: {result.status.value}")
    if result.result:
        print(f"   结果: {result.result}")

    # 2. 聊天伴侣
    result = await call_tool("chat_companion", {"message": "你好!", "style": "friendly"})
    print(f"\n2. 聊天伴侣: {result.status.value}")
    if result.result:
        print(f"   结果: {result.result}")

    # 3. 知识图谱
    result = await call_tool("knowledge_graph", {"query": "Python编程", "domain": "技术"})
    print(f"\n3. 知识图谱: {result.status.value}")
    if result.result:
        print(f"   结果: {result.result}")

    # 4. 系统监控
    result = await call_tool("system_monitor", {"target": "system", "metrics": ["cpu", "memory"]})
    print(f"\n4. 系统监控: {result.status.value}")
    if result.result:
        print(f"   结果: {result.result}")

    # 5. 网络搜索
    result = await call_tool("web_search", {"query": "AI技术发展", "limit": 5})
    print(f"\n5. 网络搜索: {result.status.value}")
    if result.result:
        print(f"   结果: {result.result}")

    # 显示统计
    print("\n📊 调用统计:")
    stats = manager.get_stats()
    print(f"  总调用数: {stats['total_calls']}")
    print(f"  成功数: {stats['successful_calls']}")
    print(f"  失败数: {stats['failed_calls']}")
    print(f"  成功率: {stats['success_rate']:.2%}")
    print(f"  平均执行时间: {stats['avg_execution_time']:.3f}秒")

    print("\n✅ 测试完成!")


# 入口点: @async_main装饰器已添加到main函数
