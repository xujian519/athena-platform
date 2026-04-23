#!/usr/bin/env python3
from __future__ import annotations
"""
执行方案执行器 - Minitap式进度追踪集成
Execution Plan Executor - Minitap-Style Progress Tracking Integration

将小诺的ExecutionPlan与WebSocket进度推送系统集成，实现：
1. 实时进度推送
2. 步骤状态追踪
3. 失败处理
4. 结果聚合

Author: Athena Team
Version: 1.0.0
Date: 2026-02-26
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

# 初始化 logger - 必须在所有可能使用它的代码之前
logger = logging.getLogger(__name__)

from core.agents.base import AgentRegistry, AgentRequest
from core.cognition.xiaonuo_planner_engine import (
    ExecutionMode,
    ExecutionPlan,
    ExecutionStep,
)

# 导入验证器
try:
    from core.cognition.verification import (
        VerificationResult,
        VerificationStatus,
        VerifierFactory,
    )
    VERIFICATION_AVAILABLE = True
except ImportError:
    VERIFICATION_AVAILABLE = False
    logger.warning("⚠️ 验证器模块未加载，验证功能将被禁用")

# 可选导入进度推送器
try:
    from core.communication.websocket.progress_pusher import (
        ProgressPusher,
        ProgressUpdate,
        get_connection_manager,
    )
    PROGRESS_AVAILABLE = True
except ImportError:
    PROGRESS_AVAILABLE = False
    logger.warning("⚠️ 进度推送器模块未加载，进度推送功能将被禁用")

# 可选导入失败恢复
try:
    from core.cognition.checkpoint import CheckpointManager, StepCheckpoint, get_checkpoint_manager
    from core.cognition.failure_recovery import (
        FailureAnalyzer,
        FailureRecoveryHandler,
        FailureStrategy,
    )
    RECOVERY_AVAILABLE = True
except ImportError:
    RECOVERY_AVAILABLE = False
    CheckpointManager = None  # type: ignore
    StepCheckpoint = None  # type: ignore
    FailureRecoveryHandler = None  # type: ignore

# 可选导入原子任务系统
try:
    from core.cognition.atomic_task import (
        AtomicTask,
        AtomicTaskDecomposer,
        AtomicTaskExecutor,
        AtomicTaskStatus,
    )
    ATOMIC_AVAILABLE = True
except ImportError:
    ATOMIC_AVAILABLE = False
    AtomicTask = None  # type: ignore
    AtomicTaskDecomposer = None  # type: ignore
    AtomicTaskExecutor = None  # type: ignore


# ========== 空进度推送器（后备） ==========


class NullProgressPusher:
    """空进度推送器 - 当进度推送不可用时使用"""

    async def push_step_start(self, *args, **kwargs):
        """空实现"""
        pass

    async def push_step_progress(self, *args, **kwargs):
        """空实现"""
        pass

    async def push_step_completed(self, *args, **kwargs):
        """空实现"""
        pass

    async def push_step_failed(self, *args, **kwargs):
        """空实现"""
        pass

    async def push_task_completed(self, *args, **kwargs):
        """空实现"""
        pass

    async def push_task_failed(self, *args, **kwargs):
        """空实现"""
        pass


# 获取进度推送器
def get_progress_pusher():
    """获取进度推送器（返回实际推送器或空推送器）"""
    if PROGRESS_AVAILABLE:
        return ProgressPusher()
    return NullProgressPusher()


# ========== 执行状态 ==========


class StepStatus(Enum):
    """步骤执行状态"""
    PENDING = "pending"  # 等待执行
    IN_PROGRESS = "in_progress"  # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    SKIPPED = "skipped"  # 跳过


class TaskStatus(Enum):
    """任务整体状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ========== 执行结果 ==========


@dataclass
class StepResult:
    """步骤执行结果"""
    step_id: str
    status: StepStatus
    output: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: int = 0


@dataclass
class ExecutionResult:
    """执行结果"""
    task_id: str
    plan_id: str
    status: TaskStatus
    step_results: list[StepResult] = field(default_factory=list)
    final_output: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    total_duration_ms: int = 0
    completed_steps: int = 0
    total_steps: int = 0


# ========== 执行器 ==========


class PlanExecutor:
    """
    执行方案执行器 - Minitap式进度追踪

    核心功能:
    1. 执行ExecutionPlan
    2. 实时推送进度到WebSocket
    3. 处理步骤失败
    4. 聚合执行结果
    """

    def __init__(
        self,
        progress_pusher: Any | None = None,
        on_step_start: Callable[[ExecutionStep], None] | None = None,
        on_step_complete: Callable[[ExecutionStep, StepResult], None] | None = None,
        on_step_fail: Callable[[ExecutionStep, Exception], None] | None = None,
        enable_checkpoint: bool = True,
        enable_recovery: bool = True,
        enable_atomic: bool = True,
    ):
        """
        初始化执行器

        Args:
            progress_pusher: 进度推送器
            on_step_start: 步骤开始回调
            on_step_complete: 步骤完成回调
            on_step_fail: 步骤失败回调
            enable_checkpoint: 是否启用检查点
            enable_recovery: 是否启用失败恢复
            enable_atomic: 是否启用原子任务分解
        """
        self.progress_pusher = progress_pusher or get_progress_pusher()
        self.on_step_start = on_step_start
        self.on_step_complete = on_step_complete
        self.on_step_fail = on_step_fail

        # 执行中状态
        self._current_task_id: Optional[str] = None
        self._current_plan: ExecutionPlan | None = None
        self._is_cancelled = False

        # 失败恢复组件
        self.enable_checkpoint = enable_checkpoint and RECOVERY_AVAILABLE
        self.enable_recovery = enable_recovery and RECOVERY_AVAILABLE

        if self.enable_checkpoint:
            self.checkpoint_manager = get_checkpoint_manager()
        else:
            self.checkpoint_manager = None

        if self.enable_recovery:
            self.failure_handler = FailureRecoveryHandler(
                checkpoint_manager=self.checkpoint_manager,
            )
            self._retry_counts: dict[str, int] = {}
        else:
            self.failure_handler = None
            self._retry_counts = {}

        # 步骤状态跟踪（用于检查点）
        self._step_states: dict[str, StepCheckpoint] = {} if RECOVERY_AVAILABLE else {}

        # 原子任务组件
        self.enable_atomic = enable_atomic and ATOMIC_AVAILABLE
        if self.enable_atomic:
            self.atomic_decomposer = AtomicTaskDecomposer()
            self.atomic_executor = AtomicTaskExecutor()

        logger.info("🚀 执行方案执行器初始化")
        if self.enable_checkpoint:
            logger.info("   📂 检查点已启用")
        if self.enable_recovery:
            logger.info("   🔄 失败恢复已启用")
        if self.enable_atomic:
            logger.info("   ⚛️ 原子任务分解已启用")

    async def execute_plan(
        self,
        plan: ExecutionPlan,
        task_id: Optional[str] = None,
    ) -> ExecutionResult:
        """
        执行完整的方案

        Args:
            plan: 执行方案
            task_id: 任务ID（用于进度追踪）

        Returns:
            ExecutionResult: 执行结果
        """
        # 生成任务ID
        if task_id is None:
            task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        self._current_task_id = task_id
        self._current_plan = plan
        self._is_cancelled = False

        # 初始化结果
        result = ExecutionResult(
            task_id=task_id,
            plan_id=plan.plan_id,
            status=TaskStatus.RUNNING,
            started_at=datetime.now(),
            total_steps=len(plan.steps),
        )

        logger.info(f"🎯 开始执行方案: {plan.plan_id}")
        logger.info(f"   任务ID: {task_id}")
        logger.info(f"   步骤数: {len(plan.steps)}")
        logger.info(f"   执行模式: {plan.mode.value}")

        try:
            # 根据执行模式执行
            if plan.mode == ExecutionMode.PARALLEL:
                await self._execute_parallel(plan, result)
            elif plan.mode == ExecutionMode.SEQUENTIAL:
                await self._execute_sequential(plan, result)
            else:  # HYBRID
                await self._execute_hybrid(plan, result)

            # 全部完成
            if not self._is_cancelled:
                result.status = TaskStatus.COMPLETED
                await self.progress_pusher.push_task_completed(
                    task_id,
                    len(plan.steps),
                )

        except asyncio.CancelledError:
            result.status = TaskStatus.CANCELLED
            logger.info(f"⚠️ 任务已取消: {task_id}")

        except Exception as e:
            result.status = TaskStatus.FAILED
            result.error = str(e)
            logger.error(f"❌ 执行失败: {e}", exc_info=True)

            await self.progress_pusher.push_task_failed(task_id, str(e))

        finally:
            result.completed_at = datetime.now()
            if result.started_at:
                result.total_duration_ms = int(
                    (result.completed_at - result.started_at).total_seconds() * 1000
                )

        logger.info(
            f"   ✅ 执行完成: {result.status.value} "
            f"({result.completed_steps}/{result.total_steps} 步骤, "
            f"{result.total_duration_ms}ms)"
        )

        return result

    async def _execute_sequential(
        self,
        plan: ExecutionPlan,
        result: ExecutionResult,
    ) -> None:
        """顺序执行模式"""
        completed_step_ids = []

        for i, step in enumerate(plan.steps):
            if self._is_cancelled:
                break

            # 检查依赖
            if not self._check_dependencies(step, result.step_results):
                logger.warning(f"⚠️ 步骤 {step.id} 依赖未满足，跳过")
                continue

            # 更新步骤状态为进行中
            if self.enable_checkpoint:
                self._step_states[step.id] = StepCheckpoint(
                    step_id=step.id,
                    status="in_progress",
                    started_at=datetime.now().isoformat(),
                )

            # 执行步骤（带重试和恢复）
            step_result = await self._execute_step_with_recovery(
                step,
                current_step=i + 1,
                total_steps=len(plan.steps),
                completed_steps=completed_step_ids,
            )

            result.step_results.append(step_result)

            # 更新步骤状态
            if self.enable_checkpoint:
                self._step_states[step.id].status = step_result.status.value
                self._step_states[step.id].completed_at = datetime.now().isoformat()
                if step_result.status == StepStatus.COMPLETED:
                    self._step_states[step.id].output = step_result.output
                elif step_result.status == StepStatus.FAILED:
                    self._step_states[step.id].error = step_result.error

                # 创建检查点
                try:
                    self.checkpoint_manager.create_checkpoint(
                        task_id=self._current_task_id,
                        plan_id=plan.plan_id,
                        completed_steps=completed_step_ids + [step.id] if step_result.status == StepStatus.COMPLETED else completed_step_ids,
                        current_step=step.id,
                        step_states=self._step_states,
                    )
                except Exception as e:
                    logger.warning(f"检查点创建失败: {e}")

            if step_result.status == StepStatus.COMPLETED:
                completed_step_ids.append(step.id)
                result.completed_steps += 1
            elif step_result.status == StepStatus.SKIPPED:
                logger.info(f"⏭️ 步骤 {step.id} 已跳过")
            elif step_result.status == StepStatus.FAILED:
                # 顺序模式下，失败则停止（除非恢复策略决定继续）
                if not step.fallback_strategy:
                    raise Exception(f"步骤 {step.id} 失败: {step_result.error}")

    async def _execute_parallel(
        self,
        plan: ExecutionPlan,
        result: ExecutionResult,
    ) -> None:
        """并行执行模式"""
        # 创建所有任务
        tasks = []
        for i, step in enumerate(plan.steps):
            tasks.append(
                self._execute_step(
                    step,
                    current_step=i + 1,
                    total_steps=len(plan.steps),
                )
            )

        # 并行执行
        step_results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        for step_result in step_results:
            if isinstance(step_result, Exception):
                logger.error(f"并行执行异常: {step_result}")
                # 创建失败结果
                result.step_results.append(
                    StepResult(
                        step_id="unknown",
                        status=StepStatus.FAILED,
                        error=str(step_result),
                    )
                )
            else:
                result.step_results.append(step_result)
                if step_result.status == StepStatus.COMPLETED:
                    result.completed_steps += 1

    async def _execute_hybrid(
        self,
        plan: ExecutionPlan,
        result: ExecutionResult,
    ) -> None:
        """混合执行模式 - 根据依赖关系智能调度"""
        # 构建依赖图
        dependency_graph = self._build_dependency_graph(plan.steps)

        # 找出可以并行执行的任务组
        execution_groups = self._resolve_execution_groups(
            plan.steps,
            dependency_graph,
        )

        # 按组执行
        for group in execution_groups:
            if self._is_cancelled:
                break

            if len(group) == 1:
                # 单个步骤顺序执行
                step = plan.steps[group[0]]
                step_result = await self._execute_step(
                    step,
                    current_step=result.completed_steps + 1,
                    total_steps=len(plan.steps),
                )
                result.step_results.append(step_result)
                if step_result.status == StepStatus.COMPLETED:
                    result.completed_steps += 1
            else:
                # 多个步骤并行执行
                tasks = []
                for idx in group:
                    step = plan.steps[idx]
                    tasks.append(
                        self._execute_step(
                            step,
                            current_step=result.completed_steps + 1,
                            total_steps=len(plan.steps),
                        )
                    )

                step_results = await asyncio.gather(*tasks, return_exceptions=True)

                for step_result in step_results:
                    if isinstance(step_result, Exception):
                        result.step_results.append(
                            StepResult(
                                step_id="unknown",
                                status=StepStatus.FAILED,
                                error=str(step_result),
                            )
                        )
                    else:
                        result.step_results.append(step_result)
                        if step_result.status == StepStatus.COMPLETED:
                            result.completed_steps += 1

    async def _execute_step(
        self,
        step: ExecutionStep,
        current_step: int,
        total_steps: int,
    ) -> StepResult:
        """
        执行单个步骤 - Minitap式进度推送

        流程:
        1. 推送步骤开始
        2. 调用回调
        3. 执行Agent
        4. 验证结果（如果启用）
        5. 推送步骤完成/失败
        6. 调用回调
        """
        started_at = datetime.now()

        # 推送步骤开始
        await self.progress_pusher.push_step_start(
            self._current_task_id,
            step.id,
            step.description,
            total_steps,
        )

        logger.info(f"   ⚙️ [{current_step}/{total_steps}] {step.description}")

        # 步骤开始回调
        if self.on_step_start:
            try:
                self.on_step_start(step)
            except Exception as e:
                logger.warning(f"步骤开始回调异常: {e}")

        try:
            # 获取Agent
            agent = AgentRegistry.get(step.agent)
            if not agent:
                raise ValueError(f"智能体 {step.agent} 不存在")

            # 创建请求
            request = AgentRequest(
                request_id=f"{self._current_task_id}_{step.id}",
                action=step.action,
                parameters=step.parameters,
            )

            # 执行请求
            response = await agent.safe_process(request)

            # 验证结果（如果启用）
            verification_result = None
            if VERIFICATION_AVAILABLE and hasattr(step, "verification"):
                verification_result = await self._verify_step_result(step, response.data)

            completed_at = datetime.now()
            duration_ms = int(
                (completed_at - started_at).total_seconds() * 1000
            )

            if response.success:
                # 检查验证结果
                if verification_result and not verification_result.passed:
                    # 验证失败
                    if hasattr(step, "verification") and step.verification.required:
                        result = StepResult(
                            step_id=step.id,
                            status=StepStatus.FAILED,
                            error=f"验证失败: {verification_result.issues[0].message if verification_result.issues else 'Unknown'}",
                            started_at=started_at,
                            completed_at=completed_at,
                            duration_ms=duration_ms,
                        )

                        # 推送步骤失败
                        await self.progress_pusher.push_step_failed(
                            self._current_task_id,
                            step.id,
                            step.description,
                            result.error,
                            total_steps,
                            current_step - 1,
                        )

                        logger.error(
                            f"   ❌ [{current_step}/{total_steps}] {step.description}: 验证失败"
                        )
                    else:
                        # 警告但继续
                        result = StepResult(
                            step_id=step.id,
                            status=StepStatus.COMPLETED,
                            output=response.data,
                            started_at=started_at,
                            completed_at=completed_at,
                            duration_ms=duration_ms,
                        )

                        await self.progress_pusher.push_step_completed(
                            self._current_task_id,
                            step.id,
                            step.description,
                            f"完成(有警告): {response.data[:200] if response.data else ''}",
                            total_steps,
                            current_step,
                        )

                        logger.warning(
                            f"   ⚠️ [{current_step}/{total_steps}] {step.description}: 有警告但继续"
                        )
                else:
                    # 成功
                    result = StepResult(
                        step_id=step.id,
                        status=StepStatus.COMPLETED,
                        output=response.data,
                        started_at=started_at,
                        completed_at=completed_at,
                        duration_ms=duration_ms,
                    )

                    # 推送步骤完成
                    await self.progress_pusher.push_step_completed(
                        self._current_task_id,
                        step.id,
                        step.description,
                        str(response.data)[:200] if response.data else "成功",
                        total_steps,
                        current_step,
                    )

                    # 步骤完成回调
                    if self.on_step_complete:
                        try:
                            self.on_step_complete(step, result)
                        except Exception as e:
                            logger.warning(f"步骤完成回调异常: {e}")

                    logger.info(
                        f"   ✅ [{current_step}/{total_steps}] {step.description} "
                        f"({duration_ms}ms)"
                    )

            else:
                # 失败
                result = StepResult(
                    step_id=step.id,
                    status=StepStatus.FAILED,
                    error=response.error,
                    started_at=started_at,
                    completed_at=completed_at,
                    duration_ms=duration_ms,
                )

                # 推送步骤失败
                await self.progress_pusher.push_step_failed(
                    self._current_task_id,
                    step.id,
                    step.description,
                    response.error or "未知错误",
                    total_steps,
                    current_step - 1,
                )

                # 步骤失败回调
                if self.on_step_fail:
                    try:
                        self.on_step_fail(step, Exception(response.error))
                    except Exception as e:
                        logger.warning(f"步骤失败回调异常: {e}")

                logger.error(
                    f"   ❌ [{current_step}/{total_steps}] {step.description}: "
                    f"{response.error}"
                )

        except Exception as e:
            completed_at = datetime.now()
            duration_ms = int(
                (completed_at - started_at).total_seconds() * 1000
            )

            result = StepResult(
                step_id=step.id,
                status=StepStatus.FAILED,
                error=str(e),
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=duration_ms,
            )

            # 推送步骤失败
            await self.progress_pusher.push_step_failed(
                self._current_task_id,
                step.id,
                step.description,
                str(e),
                total_steps,
                current_step - 1,
            )

            # 步骤失败回调
            if self.on_step_fail:
                try:
                    self.on_step_fail(step, e)
                except Exception as cb_e:
                    logger.warning(f"步骤失败回调异常: {cb_e}")

            logger.error(
                f"   ❌ [{current_step}/{total_steps}] {step.description}: {e}",
                exc_info=True,
            )

        return result

    async def _execute_step_with_recovery(
        self,
        step: ExecutionStep,
        current_step: int,
        total_steps: int,
        completed_steps: list[str],
    ) -> StepResult:
        """
        执行步骤（带失败恢复）

        如果启用失败恢复，会在步骤失败时尝试智能处理
        """
        retry_count = self._retry_counts.get(step.id, 0)

        try:
            # 执行步骤
            result = await self._execute_step(
                step,
                current_step=current_step,
                total_steps=total_steps,
            )

            # 成功则清除重试计数
            if result.status == StepStatus.COMPLETED:
                self._retry_counts.pop(step.id, None)

            return result

        except Exception as e:
            # 失败处理
            logger.error(f"步骤执行异常: {step.id} - {e}")

            if not self.enable_recovery or not self._current_plan:
                # 未启用恢复，直接返回失败结果
                return StepResult(
                    step_id=step.id,
                    status=StepStatus.FAILED,
                    error=str(e),
                )

            # 调用失败恢复处理器
            recovery_result = await self.failure_handler.handle_failure(
                step=step,
                error=e,
                execution_plan=self._current_plan,
                task_id=self._current_task_id,
                completed_steps=completed_steps,
                retry_count=retry_count,
            )

            action = recovery_result.get("action")

            if action == "retry":
                # 重试
                new_retry_count = recovery_result.get("retry_count", retry_count + 1)
                self._retry_counts[step.id] = new_retry_count

                logger.info(f"🔄 重试步骤 {step.id} (第 {new_retry_count} 次)")
                return await self._execute_step_with_recovery(
                    step,
                    current_step,
                    total_steps,
                    completed_steps,
                )

            elif action == "skip":
                # 跳过
                logger.info(f"⏭️ 跳过步骤 {step.id}")
                return StepResult(
                    step_id=step.id,
                    status=StepStatus.SKIPPED,
                    output={"skipped": True, "reason": recovery_result.get("message")},
                )

            elif action == "rollback":
                # 回退
                checkpoint = recovery_result.get("checkpoint")
                if checkpoint:
                    logger.info(f"⏪ 回退到检查点 {checkpoint.checkpoint_id}")
                    # TODO: 实现从检查点恢复的逻辑
                    return StepResult(
                        step_id=step.id,
                        status=StepStatus.FAILED,
                        error=f"回退到检查点 {checkpoint.checkpoint_id}",
                    )
                else:
                    # 没有检查点，失败
                    return StepResult(
                        step_id=step.id,
                        status=StepStatus.FAILED,
                        error="无法回退：没有可用检查点",
                    )

            elif action == "replan":
                # 重新规划
                logger.info(f"📋 重新规划: {recovery_result.get('message')}")
                # TODO: 实现重新规划的逻辑
                return StepResult(
                    step_id=step.id,
                    status=StepStatus.FAILED,
                    error="重新规划功能待实现",
                )

            else:  # abort
                # 中止
                return StepResult(
                    step_id=step.id,
                    status=StepStatus.FAILED,
                    error=recovery_result.get("reason", "执行中止"),
                )

    def _check_dependencies(
        self,
        step: ExecutionStep,
        completed_results: list[StepResult],
    ) -> bool:
        """检查步骤依赖是否满足"""
        if not step.dependencies:
            return True

        completed_ids = {r.step_id for r in completed_results if r.status == StepStatus.COMPLETED}

        for dep_id in step.dependencies:
            if dep_id not in completed_ids:
                return False

        return True

    def _build_dependency_graph(self, steps: list[ExecutionStep]) -> dict[str, list[str]]:
        """构建依赖图"""
        graph = {}
        for step in steps:
            graph[step.id] = step.dependencies.copy()
        return graph

    def _resolve_execution_groups(
        self,
        steps: list[ExecutionStep],
        dependency_graph: dict[str, list[str]],
    ) -> list[list[int]]:
        """
        解析可并行执行的步骤组

        使用拓扑排序和层次分组
        """
        groups = []
        remaining = set(range(len(steps)))
        completed = set()

        while remaining:
            # 找出所有依赖已满足的步骤
            ready = []
            for idx in remaining:
                step = steps[idx]
                # 检查是否所有依赖都已完成
                if all(dep in completed for dep in step.dependencies):
                    ready.append(idx)

            if not ready:
                # 循环依赖，强制执行第一个
                ready = [min(remaining)]

            # 将这组加入结果
            groups.append(ready)

            # 标记为已完成
            for idx in ready:
                completed.add(steps[idx].id)
                remaining.remove(idx)

        return groups

    def cancel(self) -> None:
        """取消当前执行"""
        self._is_cancelled = True
        logger.info("⚠️ 请求取消执行")

    async def _verify_step_result(
        self,
        step: ExecutionStep,
        result_data: dict[str, Any],
    ) -> Any | None:
        """
        验证步骤执行结果

        Args:
            step: 执行步骤
            result_data: Agent返回的数据

        Returns:
            VerificationResult: 验证结果，如果未启用验证则返回None
        """
        if not VERIFICATION_AVAILABLE:
            return None

        # 检查是否启用验证
        if not hasattr(step, "verification") or not step.verification.enabled:
            return None

        try:
            # 创建验证器
            verifier = VerifierFactory.create_verifier(
                step.action,
                criteria=step.verification.custom_criteria,
            )

            if verifier is None:
                # 没有合适的验证器，跳过
                return None

            # 执行验证
            logger.info(f"   🔍 验证步骤: {step.id}")
            verification_result = await verifier.verify(result_data)

            # 记录验证结果
            logger.info(
                f"   📊 验证结果: {verification_result.status.value} "
                f"(分数: {verification_result.score:.1f})"
            )

            if verification_result.issues:
                for issue in verification_result.issues:
                    logger.info(
                        f"      - {issue.severity}: {issue.message} "
                        f"({issue.code})"
                    )

            return verification_result

        except Exception as e:
            logger.error(f"验证异常: {e}", exc_info=True)
            # 验证失败不阻塞执行，返回警告
            from core.cognition.verification import VerificationResult, VerificationStatus

            return VerificationResult(
                status=VerificationStatus.WARNING,
                issues=[],
                score=0,
                details={"error": str(e)},
            )

    def get_progress(self) -> dict[str, Any]:
        """获取当前执行进度"""
        if not self._current_task_id:
            return {"status": "idle"}

        return {
            "task_id": self._current_task_id,
            "plan_id": self._current_plan.plan_id if self._current_plan else None,
            "status": "running" if not self._is_cancelled else "cancelled",
        }


# ========== 辅助函数 ==========


def create_executor(
    enable_progress: bool = True,
    on_step_start: Callable[[ExecutionStep], None] | None = None,
    on_step_complete: Callable[[ExecutionStep, StepResult], None] | None = None,
    on_step_fail: Callable[[ExecutionStep, Exception], None] | None = None,
    enable_checkpoint: bool = True,
    enable_recovery: bool = True,
    enable_atomic: bool = True,
) -> PlanExecutor:
    """
    创建执行器

    Args:
        enable_progress: 是否启用进度推送
        on_step_start: 步骤开始回调
        on_step_complete: 步骤完成回调
        on_step_fail: 步骤失败回调
        enable_checkpoint: 是否启用检查点
        enable_recovery: 是否启用失败恢复
        enable_atomic: 是否启用原子任务分解

    Returns:
        PlanExecutor: 执行器实例
    """
    progress_pusher = get_progress_pusher() if enable_progress else None

    return PlanExecutor(
        progress_pusher=progress_pusher,
        on_step_start=on_step_start,
        on_step_complete=on_step_complete,
        on_step_fail=on_step_fail,
        enable_checkpoint=enable_checkpoint,
        enable_recovery=enable_recovery,
        enable_atomic=enable_atomic,
    )


# ========== 导出 ==========


__all__ = [
    "StepStatus",
    "TaskStatus",
    "StepResult",
    "ExecutionResult",
    "PlanExecutor",
    "create_executor",
]
