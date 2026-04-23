"""
执行监控器

监控工作流的执行状态，支持断点续传和错误恢复。
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional

from core.orchestration.workflow_builder import ExecutionMode, WorkflowResult, WorkflowStep

from core.framework.agents.xiaona.base_component import AgentExecutionResult, AgentStatus

logger = logging.getLogger(__name__)


@dataclass
class ExecutionState:
    """执行状态"""
    workflow_id: str                          # 工作流ID
    current_step: int = 0                     # 当前步骤
    completed_steps: list[str] = field(default_factory=list)  # 已完成步骤
    failed_steps: list[str] = field(default_factory=list)     # 失败步骤
    step_results: dict[str, AgentExecutionResult] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class ExecutionMonitor:
    """
    执行监控器

    监控工作流执行，支持状态查询、错误恢复和断点续传。
    """

    def __init__(self):
        # 存储工作流的执行状态
        self._states: dict[str, ExecutionState] = {}
        self.logger = logging.getLogger(__name__)

    def create_workflow_state(self, workflow_id: str) -> ExecutionState:
        """
        创建工作流执行状态

        Args:
            workflow_id: 工作流ID

        Returns:
            执行状态对象
        """
        state = ExecutionState(
            workflow_id=workflow_id,
            start_time=datetime.now(),
        )
        self._states[workflow_id] = state
        self.logger.info(f"创建工作流状态: {workflow_id}")
        return state

    def update_step_result(
        self,
        workflow_id: str,
        step_id: str,
        result: AgentExecutionResult
    ) -> None:
        """
        更新步骤执行结果

        Args:
            workflow_id: 工作流ID
            step_id: 步骤ID
            result: 执行结果
        """
        state = self._states.get(workflow_id)
        if not state:
            self.logger.warning(f"工作流 {workflow_id} 状态不存在")
            return

        # 记录结果
        state.step_results[step_id] = result

        # 更新完成或失败列表
        if result.status == AgentStatus.COMPLETED:
            state.completed_steps.append(step_id)
            self.logger.info(f"步骤完成: {step_id}")
        elif result.status == AgentStatus.ERROR:
            state.failed_steps.append(step_id)
            self.logger.error(f"步骤失败: {step_id}, 错误: {result.error_message}")

    def get_workflow_state(self, workflow_id: str) -> Optional[ExecutionState]:
        """
        获取工作流执行状态

        Args:
            workflow_id: 工作流ID

        Returns:
            执行状态，如果不存在返回None
        """
        return self._states.get(workflow_id)

    def get_progress(self, workflow_id: str, total_steps: int) -> dict[str, Any]:
        """
        获取工作流进度

        Args:
            workflow_id: 工作流ID
            total_steps: 总步骤数

        Returns:
            进度信息字典
        """
        state = self._states.get(workflow_id)
        if not state:
            return {
                "workflow_id": workflow_id,
                "progress": 0,
                "completed": 0,
                "failed": 0,
                "remaining": total_steps,
            }

        completed = len(state.completed_steps)
        failed = len(state.failed_steps)
        progress = (completed / total_steps * 100) if total_steps > 0 else 0

        return {
            "workflow_id": workflow_id,
            "progress": round(progress, 2),
            "completed": completed,
            "failed": failed,
            "remaining": total_steps - completed - failed,
            "start_time": state.start_time.isoformat() if state.start_time else None,
            "elapsed_seconds": (
                (datetime.now() - state.start_time).total_seconds()
                if state.start_time else 0
            ),
        }

    def can_resume(self, workflow_id: str) -> bool:
        """
        检查工作流是否可以恢复

        Args:
            workflow_id: 工作流ID

        Returns:
            是否可以恢复
        """
        state = self._states.get(workflow_id)
        return state is not None and len(state.failed_steps) > 0

    def cleanup(self, workflow_id: str) -> None:
        """
        清理工作流状态

        Args:
            workflow_id: 工作流ID
        """
        if workflow_id in self._states:
            del self._states[workflow_id]
            self.logger.info(f"清理工作流状态: {workflow_id}")

    def cleanup_old_states(self, max_age_hours: int = 24) -> int:
        """
        清理旧的工作流状态

        Args:
            max_age_hours: 最大保留时间（小时）

        Returns:
            清理的数量
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        to_remove = []

        for workflow_id, state in self._states.items():
            if state.start_time and state.start_time < cutoff_time:
                to_remove.append(workflow_id)

        for workflow_id in to_remove:
            self.cleanup(workflow_id)

        self.logger.info(f"清理 {len(to_remove)} 个过期工作流状态")
        return len(to_remove)


async def execute_workflow(
    workflow_id: str,
    steps: list[WorkflowStep],
    agent_getter: callable,
    monitor: ExecutionMonitor,
    execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL
) -> WorkflowResult:
    """
    执行工作流

    Args:
        workflow_id: 工作流ID
        steps: 工作流步骤列表
        agent_getter: 智能体获取函数
        monitor: 执行监控器
        execution_mode: 执行模式

    Returns:
        工作流执行结果
    """
    logger = logging.getLogger(__name__)
    start_time = datetime.now()

    # 创建执行状态
    monitor.create_workflow_state(workflow_id)

    try:
        if execution_mode == ExecutionMode.SEQUENTIAL:
            results = await _execute_sequential(steps, agent_getter, monitor, workflow_id)
        elif execution_mode == ExecutionMode.PARALLEL:
            results = await _execute_parallel(steps, agent_getter, monitor, workflow_id)
        else:
            results = await _execute_sequential(steps, agent_getter, monitor, workflow_id)

        # 检查是否有失败步骤
        failed_steps = [sid for sid, res in results.items() if res.status == AgentStatus.ERROR]

        status = AgentStatus.COMPLETED if not failed_steps else AgentStatus.ERROR

        # 计算总执行时间
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()

        # 构建最终结果
        final_output = {}
        for _step_id, result in results.items():
            if result.output_data:
                final_output.update(result.output_data)

        return WorkflowResult(
            workflow_id=workflow_id,
            scenario=Scenario.UNKNOWN,  # 从上下文中获取
            status=status,
            steps=results,
            final_output=final_output,
            total_time=total_time,
            error_message=", ".join(failed_steps) if failed_steps else None,
        )

    except Exception as e:
        logger.exception(f"工作流执行异常: {workflow_id}")
        end_time = datetime.now()

        return WorkflowResult(
            workflow_id=workflow_id,
            scenario=Scenario.UNKNOWN,
            status=AgentStatus.ERROR,
            steps={},
            final_output=None,
            total_time=(end_time - start_time).total_seconds(),
            error_message=str(e),
        )


async def _execute_sequential(
    steps: list[WorkflowStep],
    agent_getter: callable,
    monitor: ExecutionMonitor,
    workflow_id: str
) -> dict[str, AgentExecutionResult]:
    """
    串行执行工作流

    Args:
        steps: 工作流步骤列表
        agent_getter: 智能体获取函数
        monitor: 执行监控器
        workflow_id: 工作流ID

    Returns:
        步骤执行结果字典
    """
    results = {}
    previous_results = {}

    for step in steps:
        # 获取智能体
        agent = agent_getter(step.agent_id)
        if not agent:
            results[step.step_id] = AgentExecutionResult(
                agent_id=step.agent_id,
                status=AgentStatus.ERROR,
                output_data=None,
                error_message=f"智能体 {step.agent_id} 未找到",
            )
            monitor.update_step_result(workflow_id, step.step_id, results[step.step_id])
            continue

        # 更新上下文（传入前面步骤的结果）
        step.context.input_data["previous_results"] = previous_results

        # 执行
        result = await agent._execute_with_monitoring(step.context)
        results[step.step_id] = result
        monitor.update_step_result(workflow_id, step.step_id, result)

        # 累积结果
        if result.status == AgentStatus.COMPLETED:
            previous_results[step.step_id] = result.output_data
        else:
            # 失败时停止执行
            break

    return results


async def _execute_parallel(
    steps: list[WorkflowStep],
    agent_getter: callable,
    monitor: ExecutionMonitor,
    workflow_id: str
) -> dict[str, AgentExecutionResult]:
    """
    并行执行工作流

    Args:
        steps: 工作流步骤列表
        agent_getter: 智能体获取函数
        monitor: 执行监控器
        workflow_id: 工作流ID

    Returns:
        步骤执行结果字典
    """
    async def execute_single_step(step: WorkflowStep) -> tuple:
        agent = agent_getter(step.agent_id)
        if not agent:
            result = AgentExecutionResult(
                agent_id=step.agent_id,
                status=AgentStatus.ERROR,
                output_data=None,
                error_message=f"智能体 {step.agent_id} 未找到",
            )
        else:
            result = await agent._execute_with_monitoring(step.context)

        monitor.update_step_result(workflow_id, step.step_id, result)
        return step.step_id, result

    # 并发执行所有步骤
    tasks = [execute_single_step(step) for step in steps]
    results_list = await asyncio.gather(*tasks, return_exceptions=True)

    # 处理结果
    results = {}
    for item in results_list:
        if isinstance(item, Exception):
            logger.exception(f"并行执行异常: {item}")
        else:
            step_id, result = item
            results[step_id] = result

    return results
