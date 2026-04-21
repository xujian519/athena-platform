"""
工作流构建器

根据场景构建智能体工作流，支持串行、并行和迭代执行模式。
"""

from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field
import logging
from datetime import datetime

from core.orchestration.agent_registry import AgentRegistry
from core.orchestration.scenario_detector import Scenario, ScenarioDetector
from core.agents.xiaona.base_component import (
    BaseXiaonaComponent,
    AgentExecutionContext,
    AgentExecutionResult,
    AgentStatus,
)

logger = logging.getLogger(__name__)


class ExecutionMode(Enum):
    """执行模式"""
    SEQUENTIAL = "sequential"  # 串行执行
    PARALLEL = "parallel"      # 并行执行
    ITERATIVE = "iterative"    # 迭代执行
    HYBRID = "hybrid"          # 混合模式


@dataclass
class WorkflowStep:
    """工作流步骤"""
    step_id: str                              # 步骤ID
    agent_id: str                             # 智能体ID
    context: AgentExecutionContext            # 执行上下文
    dependencies: List[str] = field(default_factory=list)  # 依赖的步骤ID
    retry_count: int = 0                      # 重试次数
    max_retries: int = 3                      # 最大重试次数
    timeout: float = 300.0                    # 超时时间（秒）


@dataclass
class WorkflowResult:
    """工作流执行结果"""
    workflow_id: str                          # 工作流ID
    scenario: Scenario                        # 场景类型
    status: AgentStatus                       # 执行状态
    steps: Dict[str, AgentExecutionResult]   # 各步骤执行结果
    final_output: Optional[Dict[str, Any]]   # 最终输出
    total_time: float = 0.0                  # 总执行时间
    error_message: Optional[str] = None      # 错误信息
    metadata: Dict[str, Any] = field(default_factory=dict)


class WorkflowBuilder:
    """
    工作流构建器

    根据场景和智能体组合构建工作流。
    """

    def __init__(
        self,
        agent_registry: AgentRegistry,
        scenario_detector: ScenarioDetector
    ):
        """
        初始化工作流构建器

        Args:
            agent_registry: 智能体注册表
            scenario_detector: 场景识别器
        """
        self.agent_registry = agent_registry
        self.scenario_detector = scenario_detector
        self.logger = logging.getLogger(__name__)

    def build_workflow(
        self,
        scenario: Scenario,
        user_input: str,
        session_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> List[WorkflowStep]:
        """
        构建工作流

        Args:
            scenario: 场景类型
            user_input: 用户输入
            session_id: 会话ID
            config: 额外配置

        Returns:
            工作流步骤列表

        Raises:
            ValueError: 如果需要的智能体未注册
        """
        config = config or {}
        required_agents = self.scenario_detector.get_required_agents(scenario)
        execution_mode = self.scenario_detector.get_execution_mode(scenario)

        self.logger.info(
            f"构建工作流: 场景={scenario.value}, "
            f"智能体={required_agents}, 模式={execution_mode}"
        )

        # 验证智能体是否已注册
        for agent_id in required_agents:
            agent = self.agent_registry.get_agent(agent_id)
            if agent is None:
                raise ValueError(f"智能体 {agent_id} 未注册")

        # 根据执行模式构建工作流
        if execution_mode == "sequential":
            return self._build_sequential_workflow(
                required_agents, user_input, session_id, config
            )
        elif execution_mode == "parallel":
            return self._build_parallel_workflow(
                required_agents, user_input, session_id, config
            )
        elif execution_mode == "hybrid":
            return self._build_hybrid_workflow(
                required_agents, user_input, session_id, config
            )
        else:
            # 默认串行
            return self._build_sequential_workflow(
                required_agents, user_input, session_id, config
            )

    def _build_sequential_workflow(
        self,
        agent_ids: List[str],
        user_input: str,
        session_id: str,
        config: Dict[str, Any]
    ) -> List[WorkflowStep]:
        """
        构建串行工作流

        Args:
            agent_ids: 智能体ID列表
            user_input: 用户输入
            session_id: 会话ID
            config: 配置

        Returns:
            工作流步骤列表
        """
        steps = []
        task_id = f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        for i, agent_id in enumerate(agent_ids):
            step_id = f"step_{i+1}_{agent_id}"

            # 构建执行上下文
            context = AgentExecutionContext(
                session_id=session_id,
                task_id=f"{task_id}_{agent_id}",
                input_data={
                    "user_input": user_input,
                    "previous_results": {},  # 串行执行时，可以获取前面步骤的结果
                },
                config=config,
                metadata={"step_index": i},
            )

            # 添加依赖（串行：每个步骤依赖前一个步骤）
            dependencies = []
            if i > 0:
                dependencies.append(f"step_{i}_{agent_ids[i-1]}")

            step = WorkflowStep(
                step_id=step_id,
                agent_id=agent_id,
                context=context,
                dependencies=dependencies,
            )

            steps.append(step)

        return steps

    def _build_parallel_workflow(
        self,
        agent_ids: List[str],
        user_input: str,
        session_id: str,
        config: Dict[str, Any]
    ) -> List[WorkflowStep]:
        """
        构建并行工作流

        Args:
            agent_ids: 智能体ID列表
            user_input: 用户输入
            session_id: 会话ID
            config: 配置

        Returns:
            工作流步骤列表
        """
        steps = []
        task_id = f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        for i, agent_id in enumerate(agent_ids):
            step_id = f"step_{i+1}_{agent_id}"

            context = AgentExecutionContext(
                session_id=session_id,
                task_id=f"{task_id}_{agent_id}",
                input_data={"user_input": user_input},
                config=config,
                metadata={"step_index": i},
            )

            # 并行执行：无依赖
            step = WorkflowStep(
                step_id=step_id,
                agent_id=agent_id,
                context=context,
                dependencies=[],
            )

            steps.append(step)

        return steps

    def _build_hybrid_workflow(
        self,
        agent_ids: List[str],
        user_input: str,
        session_id: str,
        config: Dict[str, Any]
    ) -> List[WorkflowStep]:
        """
        构建混合工作流（并行+串行）

        Args:
            agent_ids: 智能体ID列表
            user_input: 用户输入
            session_id: 会话ID
            config: 配置

        Returns:
            工作流步骤列表
        """
        # 示例：planner和retriever并行，后续串行
        steps = []
        task_id = f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # 第一阶段：并行执行（planner + retriever）
        parallel_agents = ["xiaona_planner", "xiaona_retriever"]
        for i, agent_id in enumerate(parallel_agents):
            if agent_id in agent_ids:
                step_id = f"step_1_{agent_id}"
                context = AgentExecutionContext(
                    session_id=session_id,
                    task_id=f"{task_id}_{agent_id}",
                    input_data={"user_input": user_input},
                    config=config,
                )
                steps.append(WorkflowStep(
                    step_id=step_id,
                    agent_id=agent_id,
                    context=context,
                    dependencies=[],
                ))

        # 第二阶段：串行执行（剩余智能体）
        remaining_agents = [aid for aid in agent_ids if aid not in parallel_agents]
        for i, agent_id in enumerate(remaining_agents):
            step_id = f"step_2_{agent_id}"
            context = AgentExecutionContext(
                session_id=session_id,
                task_id=f"{task_id}_{agent_id}",
                input_data={"user_input": user_input},
                config=config,
            )

            # 依赖第一阶段的所有步骤
            dependencies = [f"step_1_{aid}" for aid in parallel_agents if aid in agent_ids]

            steps.append(WorkflowStep(
                step_id=step_id,
                agent_id=agent_id,
                context=context,
                dependencies=dependencies,
            ))

        return steps
