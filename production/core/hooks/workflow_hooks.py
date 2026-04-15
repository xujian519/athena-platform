#!/usr/bin/env python3
"""
Workflow记忆Hooks

集成Hook系统和CrossTaskWorkflowMemory,
在任务关键节点自动提取和存储workflow模式。

Author: Athena平台团队
Created: 2026-01-20
Version: v1.0.0
"""

from __future__ import annotations
import logging
from datetime import datetime
from typing import Any

from core.hooks.base import HookContext, HookRegistry, HookType
from core.memory.cross_task_workflow_memory import CrossTaskWorkflowMemory
from core.memory.failure_learning import FailureKnowledgeBase
from core.memory.tool_call_recorder import ToolCallRecorder, ToolCallTrajectory

logger = logging.getLogger(__name__)


class WorkflowMemoryHooks:
    """
    Workflow记忆Hooks

    在任务执行的关键节点自动触发workflow模式的提取和存储。
    """

    def __init__(
        self,
        memory_system: CrossTaskWorkflowMemory,
        registry: HookRegistry | None = None,
        auto_extract_threshold: float = 0.8,
        enable_tool_recording: bool = True,
        enable_failure_learning: bool = True,
    ):
        """
        初始化Workflow记忆Hooks

        Args:
            memory_system: CrossTaskWorkflowMemory实例
            registry: HookRegistry实例 (可选,默认使用全局)
            auto_extract_threshold: 自动提取的质量阈值
            enable_tool_recording: 是否启用工具调用记录
            enable_failure_learning: 是否启用失败学习
        """
        self.memory = memory_system
        self.registry = registry or HookRegistry()
        self.auto_extract_threshold = auto_extract_threshold

        # 初始化工具调用记录器
        self.tool_recorder: ToolCallRecorder | None = None
        if enable_tool_recording:
            self.tool_recorder = ToolCallRecorder(
                storage_path=str(memory_system.storage_path / "tool_trajectories")
            )

        # 初始化失败学习系统
        self.failure_kb: FailureKnowledgeBase | None = None
        if enable_failure_learning:
            self.failure_kb = FailureKnowledgeBase(
                storage_path=str(memory_system.storage_path / "failure_knowledge")
            )

        # 注册Hooks
        self._register_hooks()

        logger.info(
            f"🔗 WorkflowMemoryHooks初始化完成 "
            f"(自动提取阈值: {auto_extract_threshold}, "
            f"工具记录: {enable_tool_recording}, "
            f"失败学习: {enable_failure_learning})"
        )

    def _register_hooks(self) -> Any:
        """注册所有Hooks"""

        # Hook 1: 任务完成时提取workflow模式
        self.registry.register_function(
            name="extract_workflow_pattern",
            hook_type=HookType.POST_TASK_COMPLETE,
            func=self._on_task_complete,
            priority=100,
        )

        # Hook 2: 工具使用时记录轨迹
        self.registry.register_function(
            name="record_tool_usage",
            hook_type=HookType.POST_TOOL_USE,
            func=self._on_tool_use,
            priority=50,
        )

        # Hook 3: 任务开始时记录上下文
        self.registry.register_function(
            name="record_task_start",
            hook_type=HookType.PRE_TASK_START,
            func=self._on_task_start,
            priority=50,
        )

        # Hook 4: 错误时记录失败信息
        self.registry.register_function(
            name="record_task_error",
            hook_type=HookType.ON_ERROR,
            func=self._on_task_error,
            priority=100,
        )

        logger.info("✅ Workflow记忆Hooks已注册")

    async def _on_task_start(self, context: HookContext):
        """
        任务开始时的Hook

        记录任务初始信息,创建工具调用轨迹。
        """
        task = context.task

        # 获取任务ID
        task_id = getattr(task, "id", f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

        logger.info(f"🎬 任务开始: {task_id}")

        # 在context中设置轨迹记录的初始状态
        context.set("trajectory_started", True)
        context.set("start_time", datetime.now())
        context.set("task_id", task_id)

        # 创建工具调用轨迹
        if self.tool_recorder:
            trajectory = self.tool_recorder.create_trajectory(task_id)
            context.set("tool_call_trajectory", trajectory)
            logger.debug(f"📍 创建工具调用轨迹: {task_id}")

    async def _on_task_complete(self, context: HookContext):
        """
        任务完成时的Hook

        如果任务成功且质量达标,自动提取workflow模式。
        同时保存工具调用轨迹。
        """
        task = context.task
        task_id = context.get("task_id", getattr(task, "id", "unknown"))
        result = context.data.get("result")
        trajectory = context.data.get("trajectory")

        # 保存工具调用轨迹
        tool_call_trajectory: ToolCallTrajectory | None = context.get("tool_call_trajectory")
        if tool_call_trajectory and self.tool_recorder:
            try:
                # 保存轨迹到文件
                self.tool_recorder.save_trajectory(task_id)

                # 获取统计信息
                stats = tool_call_trajectory.get_statistics()
                logger.info(
                    f"💾 工具调用轨迹已保存: {task_id} "
                    f"(总调用: {stats['total_calls']}, "
                    f"成功率: {stats['success_rate']:.1%})"
                )

            except Exception as e:
                logger.error(f"❌ 保存工具调用轨迹失败: {e}")

        # 检查是否应该提取模式(分步检查,避免优先级问题)
        if not result:
            logger.debug("⏭️ 跳过模式提取: 无结果")
            return

        if not trajectory:
            logger.debug("⏭️ 跳过模式提取: 无轨迹数据")
            return

        # 检查成功状态
        success = getattr(result, "success", False)
        if not success:
            logger.debug("⏭️ 跳过模式提取: 任务失败")
            return

        # 检查质量分数
        quality_score = getattr(result, "quality_score", 0.0)
        if quality_score < self.auto_extract_threshold:
            logger.debug(
                f"⏭️ 跳过模式提取: 质量分数 {quality_score:.2f} < {self.auto_extract_threshold}"
            )
            return

        # 所有条件满足,提取模式
        logger.info(f"🎯 任务完成,提取workflow模式: {task_id}")

        try:
            # 提取模式
            pattern = await self.memory.extract_workflow_pattern(
                task=task, trajectory=trajectory, success=True
            )

            # 存储模式
            if pattern:
                await self.memory.store_pattern(pattern)

                logger.info(
                    f"✅ Workflow模式已提取并存储: {pattern.pattern_id} "
                    f"({len(pattern.steps)}步骤)"
                )

        except Exception as e:
            logger.error(f"❌ 提取workflow模式失败: {e}")

    async def _on_tool_use(self, context: HookContext):
        """
        工具使用后的Hook

        记录工具调用轨迹,用于后续构建workflow模式。
        """
        tool_name = context.data.get("tool_name")
        tool_input = context.data.get("tool_input")
        tool_output = context.data.get("tool_output")
        execution_time = context.data.get("execution_time")
        success = context.data.get("success", True)
        error_message = context.data.get("error_message")

        # 获取轨迹对象
        trajectory: ToolCallTrajectory | None = context.get("tool_call_trajectory")

        if trajectory and self.tool_recorder:
            try:
                # 记录工具调用
                # 创建调用记录
                call_id = trajectory.start_call(
                    tool_name=str(tool_name or "unknown"),
                    input_data=tool_input or {},
                    metadata={"timestamp": datetime.now().isoformat()},
                )

                # 结束调用记录
                trajectory.end_call(
                    call_id=call_id,
                    output_data=tool_output,
                    execution_time=float(execution_time or 0.0),
                    success=bool(success),
                    error_message=error_message,
                )

                # 格式化执行时间显示
                time_str = f"{(execution_time*1000):.2f}ms" if execution_time is not None else "N/A"
                logger.debug(f"🔧 工具调用已记录: {tool_name} " f"(耗时: {time_str})")

            except Exception as e:
                logger.error(f"❌ 记录工具调用失败: {e}")
        else:
            # 格式化执行时间显示
            time_str = f"{(execution_time*1000):.2f}ms" if execution_time is not None else "N/A"
            logger.debug(f"🔧 工具调用: {tool_name} " f"(耗时: {time_str})")

    async def _on_task_error(self, context: HookContext):
        """
        任务错误时的Hook

        记录错误信息,用于分析和改进。
        """
        task = context.task
        task_id = context.get("task_id", getattr(task, "id", "unknown"))
        error = context.data.get("error")

        logger.error(f"❌ 任务执行失败: {task_id} " f"错误: {error}")

        # 记录失败案例到学习系统
        if self.failure_kb and error:
            try:
                # 获取堆栈跟踪
                import traceback

                stack_trace = traceback.format_exc()

                # 获取任务描述
                task_description = getattr(task, "description", str(task))
                task_type = getattr(task, "type", getattr(task, "__class__.__name__", "unknown"))

                # 构建上下文信息
                failure_context = {
                    "task_id": task_id,
                    "task_type": task_type,
                    "tool_calls": [],
                    "trajectory_started": context.get("trajectory_started", False),
                }

                # 如果有工具调用轨迹,添加到上下文
                trajectory: ToolCallTrajectory | None = context.get("tool_call_trajectory")
                if trajectory:
                    failure_context["tool_calls"] = [
                        {
                            "tool_name": call.tool_name,
                            "success": call.success,
                            "execution_time": call.execution_time,
                        }
                        for call in trajectory.get_calls()
                    ]

                # 记录失败案例
                failure_case = self.failure_kb.record_failure(
                    task_description=task_description,
                    error_message=str(error),
                    stack_trace=stack_trace,
                    context=failure_context,
                )

                logger.info(
                    f"📚 失败案例已记录: {failure_case.case_id} "
                    f"(类型: {failure_case.failure_type.value}, "
                    f"教训: {len(failure_case.learned_lessons)}条)"
                )

            except Exception as e:
                logger.error(f"❌ 记录失败案例时出错: {e}")


# 便捷函数: 快速创建WorkflowMemoryHooks


def create_workflow_memory_hooks(
    memory_system: CrossTaskWorkflowMemory,
    auto_extract_threshold: float = 0.8,
    enable_tool_recording: bool = True,
    enable_failure_learning: bool = True,
) -> WorkflowMemoryHooks:
    """
    创建Workflow记忆Hooks

    Args:
        memory_system: CrossTaskWorkflowMemory实例
        auto_extract_threshold: 自动提取阈值
        enable_tool_recording: 是否启用工具调用记录
        enable_failure_learning: 是否启用失败学习

    Returns:
        WorkflowMemoryHooks实例
    """
    return WorkflowMemoryHooks(
        memory_system=memory_system,
        auto_extract_threshold=auto_extract_threshold,
        enable_tool_recording=enable_tool_recording,
        enable_failure_learning=enable_failure_learning,
    )


__all__ = ["WorkflowMemoryHooks", "create_workflow_memory_hooks"]
