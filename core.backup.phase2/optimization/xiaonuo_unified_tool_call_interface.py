#!/usr/bin/env python3
from __future__ import annotations
"""
小诺·双鱼公主统一工具调用接口
Xiaonuo·Pisces Princess Unified Tool Call Interface (UTCI)

标准化、智能化的工具调用系统,提供统一的函数调用体验

作者: 小诺·双鱼公主
创建时间: 2025-12-18
版本: v1.0.0 "智能调用"
"""

import asyncio
import logging
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from core.logging_config import setup_logging

# 导入现有组件
from .intelligent_tool_router import ToolPriority, ToolRecommendation

if TYPE_CHECKING:
    from collections.abc import Callable

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class ToolCallStatus(Enum):
    """工具调用状态"""

    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class CallStrategy(Enum):
    """调用策略"""

    SEQUENTIAL = "sequential"  # 顺序执行
    PARALLEL = "parallel"  # 并行执行
    PIPELINE = "pipeline"  # 流水线执行
    ADAPTIVE = "adaptive"  # 自适应执行


@dataclass
class ToolCall:
    """工具调用定义"""

    tool_name: str
    function: Callable
    parameters: dict[str, Any]
    priority: ToolPriority = ToolPriority.NORMAL
    timeout: float = 30.0
    retry_count: int = 3
    dependencies: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolCallResult:
    """工具调用结果"""

    call_id: str
    tool_name: str
    status: ToolCallStatus
    result: Any = None
    error: str | None = None
    execution_time: float = 0.0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionContext:
    """执行上下文"""

    user_id: str
    session_id: str
    intent: str
    context: dict[str, Any]
    capabilities: list[str] = field(default_factory=list)
    constraints: dict[str, Any] = field(default_factory=dict)


class XiaonuoUnifiedToolCallInterface:
    """小诺统一工具调用接口"""

    def __init__(self):
        self.name = "小诺·双鱼公主统一工具调用接口"
        self.version = "v1.0.0"

        # 工具注册表
        self.tool_registry: dict[str, ToolCall] = {}

        # 执行历史
        self.execution_history: list[ToolCallResult] = []

        # 性能统计
        self.performance_metrics: dict[str, Any] = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "average_execution_time": 0.0,
            "tool_usage_stats": {},
        }

        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=10)

        # 初始化路由器
        self._init_router()

        logger.info(f"🔧 {self.name} v{self.version} 初始化完成")

    def _init_router(self) -> Any:
        """初始化智能路由器"""
        try:
            from ..smart_routing.intelligent_tool_router import IntelligentToolRouter

            self.router = IntelligentToolRouter()
            logger.info("✅ 智能路由器初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ 智能路由器初始化失败: {e}")
            self.router = None

    def register_tool(
        self,
        tool_name: str,
        function: Callable,
        description: str = "",
        parameters_schema: dict | None = None,
        priority: ToolPriority = ToolPriority.NORMAL,
    ) -> bool:
        """注册工具"""
        try:
            tool_call = ToolCall(
                tool_name=tool_name,
                function=function,
                parameters={},
                priority=priority,
                metadata={
                    "description": description,
                    "parameters_schema": parameters_schema or {},
                    "registration_time": datetime.now().isoformat(),
                },
            )

            self.tool_registry[tool_name] = tool_call
            logger.info(f"✅ 工具注册成功: {tool_name}")
            return True

        except Exception as e:
            logger.error(f"❌ 工具注册失败 {tool_name}: {e}")
            return False

    async def smart_function_call(
        self,
        intent: str,
        context: dict[str, Any],        tools: list[str] = None,
        strategy: CallStrategy = CallStrategy.ADAPTIVE,
    ) -> list[ToolCallResult]:
        """
        智能函数调用 - 小诺的核心能力

        Args:
            intent: 用户意图
            context: 执行上下文
            tools: 指定工具列表(可选)
            strategy: 执行策略

        Returns:
            执行结果列表
        """
        logger.info(f"🎯 开始智能函数调用: {intent}")

        start_time = time.time()

        try:
            # 1. 意图分析和工具选择
            selected_tools = await self._analyze_intent_and_select_tools(intent, context, tools)

            # 2. 优化调用顺序
            optimized_tools = await self._optimize_call_sequence(selected_tools, strategy)

            # 3. 执行工具调用
            results = await self._execute_tool_calls(optimized_tools, context, strategy)

            # 4. 更新性能指标
            execution_time = time.time() - start_time
            self._update_performance_metrics(results, execution_time)

            logger.info(f"✅ 智能函数调用完成,耗时: {execution_time:.2f}秒")
            return results

        except Exception as e:
            logger.error(f"❌ 智能函数调用失败: {e}")
            return [
                ToolCallResult(
                    call_id=str(uuid.uuid4()),
                    tool_name="smart_function_call",
                    status=ToolCallStatus.FAILED,
                    error=str(e),
                )
            ]

    async def _analyze_intent_and_select_tools(
        self, intent: str, context: dict[str, Any], preferred_tools: list[str] = None
    ) -> list[ToolCall]:
        """分析意图并选择工具"""
        selected_tools = []

        # 如果指定了偏好工具,优先使用
        if preferred_tools:
            for tool_name in preferred_tools:
                if tool_name in self.tool_registry:
                    tool_call = self.tool_registry[tool_name]
                    # 根据意图调整参数
                    optimized_params = await self._optimize_parameters(tool_name, intent, context)
                    tool_call.parameters = optimized_params
                    selected_tools.append(tool_call)

        # 如果没有指定工具或工具不足,使用智能路由
        if not selected_tools and self.router:
            try:
                recommendations = await self._get_tool_recommendations(intent, context)
                for rec in recommendations:
                    if rec.tool_name in self.tool_registry:
                        tool_call = self.tool_registry[rec.tool_name]
                        tool_call.priority = ToolPriority(rec.priority.value)
                        selected_tools.append(tool_call)
            except Exception as e:
                logger.warning(f"⚠️ 智能路由失败,使用默认工具: {e}")

        # 如果还是没有工具,选择所有可用工具
        if not selected_tools:
            selected_tools = list(self.tool_registry.values())

        logger.info(f"🎯 选择了 {len(selected_tools)} 个工具")
        return selected_tools

    async def _optimize_parameters(
        self, tool_name: str, intent: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """优化工具参数"""
        base_params = {}

        # 从上下文中提取相关参数
        if "parameters" in context:
            base_params.update(context["parameters"])

        # 根据意图和工具名称优化参数
        if "search" in intent.lower() and "search" in tool_name.lower():
            base_params.update(
                {
                    "query": context.get("query", intent),
                    "limit": context.get("limit", 10),
                    "language": "zh-CN",
                }
            )

        if "crawl" in intent.lower() or "crawler" in tool_name.lower():
            base_params.update(
                {
                    "url": context.get("url", ""),
                    "depth": context.get("depth", 1),
                    "output_format": context.get("output_format", "json"),
                }
            )

        return base_params

    async def _get_tool_recommendations(
        self, intent: str, context: dict[str, Any]
    ) -> list[ToolRecommendation]:
        """获取工具推荐"""
        # 这里应该调用现有的智能路由器
        recommendations = []

        # 基于意图的简单推荐逻辑
        if "search" in intent.lower():
            recommendations.append(
                ToolRecommendation(
                    tool_name="bing_search",
                    priority=ToolPriority.IMPORTANT,
                    confidence=0.9,
                    reason="搜索相关任务",
                    estimated_time=2.0,
                )
            )

        if "crawl" in intent.lower() or "爬虫" in intent:
            recommendations.append(
                ToolRecommendation(
                    tool_name="universal_crawler",
                    priority=ToolPriority.CRITICAL,
                    confidence=0.95,
                    reason="爬虫任务",
                    estimated_time=5.0,
                )
            )

        return recommendations

    async def _optimize_call_sequence(
        self, tools: list[ToolCall], strategy: CallStrategy
    ) -> list[ToolCall]:
        """优化调用序列"""
        if strategy == CallStrategy.SEQUENTIAL:
            # 按优先级排序
            tools.sort(key=lambda t: self._priority_to_weight(t.priority))

        elif strategy == CallStrategy.PARALLEL:
            # 并行执行不需要特殊排序
            pass

        elif strategy == CallStrategy.PIPELINE:
            # 流水线执行:按依赖关系排序
            tools = self._topological_sort(tools)

        elif strategy == CallStrategy.ADAPTIVE:
            # 自适应:根据工具特性选择最佳策略
            strategy = await self._determine_optimal_strategy(tools)
            return await self._optimize_call_sequence(tools, strategy)

        return tools

    def _priority_to_weight(self, priority: ToolPriority) -> int:
        """优先级转权重"""
        weights = {
            ToolPriority.CRITICAL: 1,
            ToolPriority.IMPORTANT: 2,
            ToolPriority.NORMAL: 3,
            ToolPriority.OPTIONAL: 4,
        }
        return weights.get(priority, 3)

    def _topological_sort(self, tools: list[ToolCall]) -> list[ToolCall]:
        """拓扑排序(处理依赖关系)"""
        # 简化实现:无依赖工具在前
        no_deps = [t for t in tools if not t.dependencies]
        with_deps = [t for t in tools if t.dependencies]
        return no_deps + with_deps

    async def _determine_optimal_strategy(self, tools: list[ToolCall]) -> CallStrategy:
        """确定最优执行策略"""
        if len(tools) == 1:
            return CallStrategy.SEQUENTIAL

        # 如果有依赖关系,使用流水线
        if any(t.dependencies for t in tools):
            return CallStrategy.PIPELINE

        # 如果都是短时间任务,使用并行
        if all(t.metadata.get("estimated_time", 1.0) < 3.0 for t in tools):
            return CallStrategy.PARALLEL

        # 否则使用顺序执行
        return CallStrategy.SEQUENTIAL

    async def _execute_tool_calls(
        self, tools: list[ToolCall], context: dict[str, Any], strategy: CallStrategy
    ) -> list[ToolCallResult]:
        """执行工具调用"""
        results = []

        if strategy == CallStrategy.PARALLEL:
            # 并行执行
            tasks = [self._execute_single_tool(tool, context) for tool in tools]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # 顺序或流水线执行
            for tool in tools:
                result = await self._execute_single_tool(tool, context)
                results.append(result)

                # 如果失败且不是可选工具,停止执行
                if result.status == ToolCallStatus.FAILED and tool.priority in [
                    ToolPriority.CRITICAL,
                    ToolPriority.IMPORTANT,
                ]:
                    logger.warning(f"⚠️ 关键工具 {tool.tool_name} 执行失败,停止后续执行")
                    break

        return results

    async def _execute_single_tool(self, tool: ToolCall, context: dict[str, Any]) -> ToolCallResult:
        """执行单个工具"""
        call_id = str(uuid.uuid4())
        start_time = datetime.now()

        try:
            logger.info(f"🔧 执行工具: {tool.tool_name}")

            # 准备执行参数
            execution_params = {**tool.parameters, **context}

            # 执行工具函数
            if asyncio.iscoroutinefunction(tool.function):
                result = await asyncio.wait_for(
                    tool.function(**execution_params), timeout=tool.timeout
                )
            else:
                # 在线程池中执行同步函数
                result = await asyncio.get_event_loop().run_in_executor(
                    self.executor, lambda: tool.function(**execution_params)
                )

            execution_time = (datetime.now() - start_time).total_seconds()

            return ToolCallResult(
                call_id=call_id,
                tool_name=tool.tool_name,
                status=ToolCallStatus.COMPLETED,
                result=result,
                execution_time=execution_time,
                start_time=start_time,
                end_time=datetime.now(),
            )

        except TimeoutError:
            logger.error(f"⏰ 工具执行超时: {tool.tool_name}")
            return ToolCallResult(
                call_id=call_id,
                tool_name=tool.tool_name,
                status=ToolCallStatus.TIMEOUT,
                error="执行超时",
                execution_time=(datetime.now() - start_time).total_seconds(),
                start_time=start_time,
                end_time=datetime.now(),
            )

        except Exception as e:
            logger.error(f"❌ 工具执行失败 {tool.tool_name}: {e}")
            return ToolCallResult(
                call_id=call_id,
                tool_name=tool.tool_name,
                status=ToolCallStatus.FAILED,
                error=str(e),
                execution_time=(datetime.now() - start_time).total_seconds(),
                start_time=start_time,
                end_time=datetime.now(),
            )

    def _update_performance_metrics(self, results: list[ToolCallResult], total_time: float) -> Any:
        """更新性能指标"""
        self.performance_metrics["total_calls"] += len(results)

        successful_calls = sum(1 for r in results if r.status == ToolCallStatus.COMPLETED)
        failed_calls = len(results) - successful_calls

        self.performance_metrics["successful_calls"] += successful_calls
        self.performance_metrics["failed_calls"] += failed_calls

        # 更新平均执行时间
        total_time_so_far = self.performance_metrics.get("total_execution_time", 0) + total_time
        total_calls = self.performance_metrics["total_calls"]
        self.performance_metrics["average_execution_time"] = total_time_so_far / total_calls
        self.performance_metrics["total_execution_time"] = total_time_so_far

        # 更新工具使用统计
        for result in results:
            tool_name = result.tool_name
            if tool_name not in self.performance_metrics["tool_usage_stats"]:
                self.performance_metrics["tool_usage_stats"][tool_name] = {
                    "calls": 0,
                    "successes": 0,
                    "failures": 0,
                    "total_time": 0,
                }

            stats = self.performance_metrics["tool_usage_stats"][tool_name]
            stats["calls"] += 1
            stats["total_time"] += result.execution_time

            if result.status == ToolCallStatus.COMPLETED:
                stats["successes"] += 1
            else:
                stats["failures"] += 1

        # 保存执行历史
        self.execution_history.extend(results)

        # 限制历史记录大小
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-1000:]

    def get_performance_report(self) -> dict[str, Any]:
        """获取性能报告"""
        return {
            "interface_version": self.version,
            "registered_tools": len(self.tool_registry),
            "performance_metrics": self.performance_metrics.copy(),
            "recent_executions": self.execution_history[-10:],
            "generated_at": datetime.now().isoformat(),
        }

    def get_tool_list(self) -> dict[str, dict[str, Any]]:
        """获取工具列表"""
        return {
            name: {
                "description": tool.metadata.get("description", ""),
                "priority": tool.priority.value,
                "timeout": tool.timeout,
                "dependencies": tool.dependencies,
                "metadata": tool.metadata,
            }
            for name, tool in self.tool_registry.items()
        }


# 全局实例
xiaonuo_utci = XiaonuoUnifiedToolCallInterface()


# 便捷函数
async def smart_call(
    intent: str, context: dict[str, Any], tools: list[str] | None = None
) -> list[ToolCallResult]:
    """便捷的智能调用函数"""
    return await xiaonuo_utci.smart_function_call(intent, context, tools)


def register_tool(name: str, function: Callable, description: str = "", **kwargs) -> bool:
    """便捷的工具注册函数"""
    return xiaonuo_utci.register_tool(name, function, description, **kwargs)
