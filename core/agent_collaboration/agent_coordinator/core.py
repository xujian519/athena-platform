#!/usr/bin/env python3
from __future__ import annotations
"""
Agent协调器 - 核心类
Agent Coordinator - Core Class

作者: Athena AI系统
创建时间: 2025-12-04
重构时间: 2026-01-26
版本: 2.0.0
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

from ..agent_registry import AgentType
from ..agents import AnalysisAgent, CreativeAgent, SearchAgent  # type: ignore[attr-defined]
from ..base_agent import BaseAgent
from ..communication import ResponseMessage, TaskMessage
from .strategies import CoordinationStrategies
from .templates import initialize_workflow_templates
from .types import TaskDefinition, TaskExecution, TaskStatus, WorkflowType

logger = logging.getLogger(__name__)


class AgentCoordinator(BaseAgent):
    """Agent协调器 - 智能任务协调专家"""

    def __init__(
        self, agent_id: str = "agent_coordinator_001", config: Optional[dict[str, Any]] = None
    ):
        super().__init__(
            agent_id=agent_id,
            name="智能任务协调器",
            agent_type=AgentType.COORDINATOR,
            description="专业的多Agent任务协调专家,负责智能任务分发、工作流优化和协作管理",
            config=config or {},
        )

        # 任务管理
        self.task_queue: asyncio.Queue[Any] = asyncio.Queue()
        self.active_tasks: dict[str, TaskExecution] = {}
        self.completed_tasks: dict[str, TaskExecution] = {}

        # 工作流模板
        self.workflow_templates = initialize_workflow_templates()

        # 性能统计
        self.tasks_coordinated = 0
        self.successful_tasks = 0
        self.failed_tasks = 0
        self.avg_task_duration = 0.0

        # 协调策略配置 - 优化版本
        self.coordination_strategies = {
            "load_balancing": True,
            "specialization_matching": True,
            "performance_optimization": True,
            "deadline_aware": True,
            "intelligent_routing": True,  # 新增:智能路由
            "adaptive_scheduling": True,  # 新增:自适应调度
            "resource_monitoring": True,  # 新增:资源监控
            "failure_recovery": True,  # 新增:故障恢复
        }

        # 性能优化配置
        self.max_concurrent_tasks = (config or {}).get("max_concurrent_tasks", 10)
        self.task_timeout = (config or {}).get("task_timeout", 300)  # 5分钟超时
        self.retry_attempts = (config or {}).get("retry_attempts", 3)

        # 智能调度参数
        self.agent_performance_scores = {}  # Agent性能评分
        self.task_complexity_cache = {}  # 任务复杂度缓存

        # 协调策略实例
        self._strategies = CoordinationStrategies(self)

        # 内存泄露修复: 保存后台任务引用以便取消
        self._task_processing_task: asyncio.Task | None = None
        self._performance_monitoring_task: asyncio.Task | None = None

    def get_capabilities(self) -> list[str]:
        """获取协调器能力列表"""
        return [
            "task_coordination",
            "workflow_management",
            "load_balancing",
            "agent_selection",
            "task_prioritization",
            "deadline_management",
            "performance_optimization",
            "conflict_resolution",
            "resource_allocation",
            "collaboration_orchestration",
        ]

    async def initialize(self):
        """初始化协调器"""
        await super().initialize()

        # 创建专业化Agent实例
        await self._create_specialized_agents()

        # 启动任务处理循环 - 保存任务引用以便后续取消
        self._task_processing_task = asyncio.create_task(self._task_processing_loop())

        # 启动性能监控 - 保存任务引用以便后续取消
        self._performance_monitoring_task = asyncio.create_task(self._performance_monitoring_loop())

        logger.info("✅ Agent协调器初始化完成")

    async def _create_specialized_agents(self):
        """创建专业化Agent实例"""
        try:
            # 创建搜索Agent
            self.search_agent = SearchAgent()
            await self.search_agent.initialize()

            # 创建分析Agent
            self.analysis_agent = AnalysisAgent()
            await self.analysis_agent.initialize()

            # 创建创意Agent
            self.creative_agent = CreativeAgent()
            await self.creative_agent.initialize()

            logger.info("✅ 专业化Agent创建完成")

        except Exception as e:
            logger.error(f"❌ 专业化Agent创建失败: {e}")
            raise

    async def process_task(self, task_message: TaskMessage) -> ResponseMessage:
        """处理协调任务"""
        try:
            task_type = task_message.task_type
            content = task_message.content

            # 根据任务类型执行协调策略 - 优化版本
            if task_type == "coordinate_workflow":
                result = await self._coordinate_workflow(content)
            elif task_type == "create_workflow":
                result = await self._create_workflow(content)
            elif task_type == "agent_status_check":
                result = await self._check_agent_status(content)
            elif task_type == "task_status_query":
                result = await self._query_task_status(content)
            elif task_type == "performance_report":
                result = await self._generate_performance_report(content)
            elif task_type == "intelligent_task_assignment":
                result = await self._strategies.intelligent_task_assignment(content)
            elif task_type == "load_balancing":
                result = await self._strategies.load_balancing_assignment(content)
            elif task_type == "failure_recovery":
                result = await self._strategies.handle_task_failure(content)
            else:
                result = await self._general_coordination(content)

            return ResponseMessage(
                task_id=task_message.task_id,
                sender_id=self.agent_id,
                recipient_id=task_message.sender_id,
                success=True,
                content=result,
                metadata={
                    "task_type": task_type,
                    "coordination_time": datetime.now().isoformat(),
                    "coordinator_status": self.get_status(),
                },
            )

        except Exception as e:
            logger.error(f"❌ 协调器任务处理失败: {e}")
            return ResponseMessage(
                task_id=task_message.task_id,
                sender_id=self.agent_id,
                recipient_id=task_message.sender_id,
                success=False,
                error_message=str(e),
            )

    async def _coordinate_workflow(self, content: dict[str, Any]) -> dict[str, Any]:
        """协调工作流执行"""
        workflow_type = WorkflowType(content.get("workflow_type", "sequential"))
        tasks = content.get("tasks", [])
        user_request = content.get("user_request", "")

        logger.info(f"🔄 协调工作流: {workflow_type.value}, 任务数: {len(tasks)}")

        # 创建工作流执行计划
        execution_plan = await self._create_execution_plan(workflow_type, tasks, user_request)

        # 执行工作流
        workflow_result = await self._execute_workflow(execution_plan)

        return {
            "workflow_type": workflow_type.value,
            "execution_plan": execution_plan,
            "workflow_result": workflow_result,
            "coordination_summary": {
                "total_tasks": len(tasks),
                "successful_tasks": len(
                    [t for t in workflow_result.get("task_results", []) if t.get("success", False)]
                ),
                "execution_time": workflow_result.get("total_execution_time", 0),
                "agents_involved": workflow_result.get("agents_used", []),
            },
        }

    async def _create_execution_plan(
        self, workflow_type: WorkflowType, tasks: list[dict[str, Any]], user_request: str
    ) -> dict[str, Any]:
        """创建执行计划"""
        plan: dict[str, Any] = {
            "workflow_type": workflow_type.value,
            "user_request": user_request,
            "tasks": [],
            "agent_assignments": {},
            "dependencies": {},
            "estimated_duration": 0,
        }

        # 分析任务并分配Agent
        for i, task in enumerate(tasks):
            task_type = task.get("type", "")
            task_content = task.get("content", {})

            # 智能Agent选择
            selected_agent = await self._select_best_agent(task_type, task_content)

            task_plan = {
                "task_id": f"task_{i+1:03d}",
                "task_type": task_type,
                "content": task_content,
                "assigned_agent": selected_agent,
                "priority": task.get("priority", 2),
                "estimated_duration": self._estimate_task_duration(task_type),
            }

            plan["tasks"].append(task_plan)
            plan["agent_assignments"][task_plan["task_id"]] = selected_agent

            # 设置依赖关系(对于串行工作流)
            if workflow_type == WorkflowType.SEQUENTIAL and i > 0:
                plan["dependencies"][task_plan["task_id"]] = [f"task_{i:03d}"]

            # 累计估计时间
            if workflow_type == WorkflowType.SEQUENTIAL:
                plan["estimated_duration"] += task_plan["estimated_duration"]
            else:
                plan["estimated_duration"] = max(
                    plan["estimated_duration"], task_plan["estimated_duration"]
                )

        return plan

    async def _select_best_agent(self, task_type: str, task_content: dict[str, Any]) -> str:
        """智能选择最适合的Agent"""
        # 任务类型到Agent的映射
        task_agent_mapping = {
            "patent_search": self.search_agent.agent_id,
            "semantic_search": self.search_agent.agent_id,
            "patent_analysis": self.analysis_agent.agent_id,
            "technology_trend_analysis": self.analysis_agent.agent_id,
            "innovation_generation": self.creative_agent.agent_id,
            "creative_solutions": self.creative_agent.agent_id,
        }

        # 直接映射
        if task_type in task_agent_mapping:
            return task_agent_mapping[task_type]

        # 基于内容特征选择
        content_lower = str(task_content).lower()

        if any(keyword in content_lower for keyword in ["搜索", "search", "检索", "query"]):
            return self.search_agent.agent_id
        elif any(
            keyword in content_lower for keyword in ["分析", "analysis", "评估", "assessment"]
        ):
            return self.analysis_agent.agent_id
        elif any(
            keyword in content_lower for keyword in ["创新", "innovation", "创意", "creative"]
        ):
            return self.creative_agent.agent_id

        # 默认返回搜索Agent
        return self.search_agent.agent_id

    def _estimate_task_duration(self, task_type: str) -> float:
        """估算任务执行时间(秒)"""
        duration_mapping = {
            "patent_search": 2.0,
            "semantic_search": 1.5,
            "patent_analysis": 5.0,
            "technology_trend_analysis": 3.0,
            "innovation_generation": 4.0,
            "creative_solutions": 3.5,
        }
        return duration_mapping.get(task_type, 2.0)

    async def _execute_workflow(self, execution_plan: dict[str, Any]) -> dict[str, Any]:
        """执行工作流"""
        workflow_type = execution_plan["workflow_type"]
        tasks = execution_plan["tasks"]
        dependencies = execution_plan.get("dependencies", {})

        start_time = datetime.now()
        task_results = []
        agents_used = set()

        try:
            if workflow_type == "sequential":
                # 串行执行
                for task in tasks:
                    result = await self._execute_single_task(task)
                    task_results.append(result)
                    agents_used.add(result.get("agent_used", "unknown"))

                    # 检查任务是否成功
                    if not result.get("success", False):
                        logger.warning(f"⚠️ 任务 {task['task_id']} 执行失败,终止工作流")
                        break

            elif workflow_type == "parallel":
                # 并行执行
                task_coroutines = [self._execute_single_task(task) for task in tasks]
                task_results = await asyncio.gather(*task_coroutines, return_exceptions=True)
                agents_used.update(
                    result.get("agent_used", "unknown")
                    for result in task_results
                    if isinstance(result, dict)
                )

            elif workflow_type == "pipeline":
                # 流水线执行
                for task in tasks:
                    # 检查依赖
                    task_id = task["task_id"]
                    if task_id in dependencies:
                        dependency_tasks = dependencies[task_id]
                        for dep_task_id in dependency_tasks:
                            # 确保依赖任务完成
                            dep_result = next(
                                (r for r in task_results if r.get("task_id") == dep_task_id), None
                            )
                            if not dep_result or not dep_result.get("success", False):
                                logger.error(f"❌ 依赖任务 {dep_task_id} 失败,跳过任务 {task_id}")
                                continue

                    result = await self._execute_single_task(task)
                    task_results.append(result)
                    agents_used.add(result.get("agent_used", "unknown"))

            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            return {
                "workflow_status": "completed",
                "task_results": task_results,
                "agents_used": list(agents_used),
                "total_execution_time": execution_time,
                "success_rate": sum(
                    1 for r in task_results if isinstance(r, dict) and r.get("success", False)
                )
                / len(task_results),
            }

        except Exception as e:
            logger.error(f"❌ 工作流执行失败: {e}")
            return {
                "workflow_status": "failed",
                "error_message": str(e),
                "task_results": task_results,
                "agents_used": list(agents_used),
                "total_execution_time": (datetime.now() - start_time).total_seconds(),
            }

    async def _execute_single_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """执行单个任务"""
        task_id = task["task_id"]
        task_type = task["task_type"]
        task_content = task["content"]
        agent_id = task["assigned_agent"]

        try:
            logger.info(f"🔧 执行任务 {task_id}: {task_type} -> {agent_id}")

            # 发送任务给指定Agent
            from ..communication import TaskPriority

            task_priority_value = task.get("priority", 2)
            if isinstance(task_priority_value, int):
                task_priority = TaskPriority(task_priority_value)
            else:
                task_priority = TaskPriority.MEDIUM

            TaskMessage(
                task_id=task_id,
                sender_id=self.agent_id,
                recipient_id=agent_id,
                task_type=task_type,
                content=task_content,
                priority=task_priority,
            )

            # 等待响应
            response = await self._wait_for_agent_response(task_id, timeout=30.0)

            if response and response.success:
                return {
                    "task_id": task_id,
                    "success": True,
                    "content": response.content,
                    "agent_used": agent_id,
                    "execution_time": response.execution_time,
                    "metadata": response.metadata,
                }
            else:
                return {
                    "task_id": task_id,
                    "success": False,
                    "error_message": response.error_message if response else "Task timeout",
                    "agent_used": agent_id,
                }

        except Exception as e:
            logger.error(f"❌ 任务 {task_id} 执行异常: {e}")
            return {
                "task_id": task_id,
                "success": False,
                "error_message": str(e),
                "agent_used": agent_id,
            }

    async def _wait_for_agent_response(
        self, task_id: str, timeout: float = 30.0
    ) -> ResponseMessage | None:
        """等待Agent响应"""
        start_time = datetime.now()

        while (datetime.now() - start_time).total_seconds() < timeout:
            # 检查消息总线中是否有响应
            if self.message_bus and hasattr(self.message_bus, "message_history"):
                recent_messages = self.message_bus.message_history[-10:]
                for message in recent_messages:
                    if (
                        isinstance(message, dict)
                        and message.get("task_id") == task_id
                        and message.get("recipient_id") == self.agent_id
                        and message.get("message_type") == "response"
                    ):
                        # 从字典构造 ResponseMessage
                        return ResponseMessage(
                            task_id=message.get("task_id", ""),
                            sender_id=message.get("sender_id", ""),
                            recipient_id=message.get("recipient_id", ""),
                            success=message.get("success", False),
                            content=message.get("content", {}),
                            error_message=message.get("error_message"),
                            execution_time=message.get("execution_time", 0.0) or 0.0,
                            metadata=message.get("metadata") or {},
                        )

            await asyncio.sleep(0.5)  # 短暂等待

        logger.warning(f"⚠️ 任务 {task_id} 响应超时")
        return None

    async def _create_workflow(self, content: dict[str, Any]) -> dict[str, Any]:
        """创建工作流"""
        workflow_name = content.get("workflow_name", "")
        workflow_type = content.get("workflow_type", "sequential")
        user_request = content.get("user_request", "")

        # 智能工作流设计
        workflow_design = await self._design_workflow(user_request, workflow_type)

        return {
            "workflow_name": workflow_name,
            "workflow_design": workflow_design,
            "creation_time": datetime.now().isoformat(),
            "estimated_duration": workflow_design.get("estimated_duration", 0),
            "required_agents": workflow_design.get("required_agents", []),
        }

    async def _design_workflow(self, user_request: str, workflow_type: str) -> dict[str, Any]:
        """智能设计工作流"""
        request_lower = user_request.lower()

        # 基于用户请求设计工作流
        if "专利" in request_lower and "搜索" in request_lower:
            return {
                "workflow_type": "pipeline",
                "steps": [
                    {"type": "patent_search", "description": "专利检索"},
                    {"type": "patent_analysis", "description": "专利分析"},
                ],
                "required_agents": [self.search_agent.agent_id, self.analysis_agent.agent_id],
                "estimated_duration": 7.0,
            }
        elif "创新" in request_lower or "创意" in request_lower:
            return {
                "workflow_type": "collaborative",
                "steps": [
                    {"type": "patent_search", "description": "技术背景搜索"},
                    {"type": "innovation_generation", "description": "创新想法生成"},
                ],
                "required_agents": [self.search_agent.agent_id, self.creative_agent.agent_id],
                "estimated_duration": 6.0,
            }
        else:
            return {
                "workflow_type": "sequential",
                "steps": [{"type": "patent_search", "description": "信息收集"}],
                "required_agents": [self.search_agent.agent_id],
                "estimated_duration": 2.0,
            }

    async def _check_agent_status(self, content: dict[str, Any]) -> dict[str, Any]:
        """检查Agent状态"""
        agent_ids = content.get("agent_ids", [])

        if not agent_ids:
            # 检查所有Agent状态
            agents_to_check = [self.search_agent, self.analysis_agent, self.creative_agent]
        else:
            # 检查指定Agent
            agents_to_check = []
            all_agents = [self.search_agent, self.analysis_agent, self.creative_agent]
            for agent in all_agents:
                if agent.agent_id in agent_ids:
                    agents_to_check.append(agent)

        status_report = {}
        for agent in agents_to_check:
            status_report[agent.agent_id] = agent.get_status()

        return {
            "agent_status_report": status_report,
            "check_time": datetime.now().isoformat(),
            "total_agents": len(status_report),
            "available_agents": len(
                [s for s in status_report.values() if s.get("status") == "idle"]
            ),
        }

    async def _query_task_status(self, content: dict[str, Any]) -> dict[str, Any]:
        """查询任务状态"""
        task_ids = content.get("task_ids", [])

        if not task_ids:
            # 返回所有任务状态
            task_status = {
                task_id: execution.__dict__ for task_id, execution in self.active_tasks.items()
            }
        else:
            # 返回指定任务状态
            task_status = {}
            for task_id in task_ids:
                if task_id in self.active_tasks:
                    task_status[task_id] = self.active_tasks[task_id].__dict__
                elif task_id in self.completed_tasks:
                    task_status[task_id] = self.completed_tasks[task_id].__dict__

        return {
            "task_status": task_status,
            "query_time": datetime.now().isoformat(),
            "active_tasks_count": len(self.active_tasks),
            "completed_tasks_count": len(self.completed_tasks),
        }

    async def _generate_performance_report(self, content: dict[str, Any]) -> dict[str, Any]:
        """生成性能报告"""
        time_range = content.get("time_range", "24h")

        # 收集性能数据
        coordinator_stats = self.get_status()

        # 收集Agent性能数据
        agent_stats = {}
        all_agents = [self.search_agent, self.analysis_agent, self.creative_agent]
        for agent in all_agents:
            agent_stats[agent.agent_id] = agent.get_status()

        # 计算总体性能指标
        total_tasks = sum(stats.get("task_count", 0) for stats in agent_stats.values())
        total_success = sum(stats.get("success_count", 0) for stats in agent_stats.values())
        overall_success_rate = total_success / total_tasks if total_tasks > 0 else 0

        return {
            "performance_report": {
                "coordinator_stats": coordinator_stats,
                "agent_stats": agent_stats,
                "overall_metrics": {
                    "total_tasks_processed": total_tasks,
                    "overall_success_rate": overall_success_rate,
                    "avg_execution_time": sum(
                        stats.get("avg_execution_time", 0) for stats in agent_stats.values()
                    )
                    / len(agent_stats),
                    "active_agents": len(
                        [s for s in agent_stats.values() if s.get("status") == "idle"]
                    ),
                },
            },
            "report_time": datetime.now().isoformat(),
            "time_range": time_range,
        }

    async def _general_coordination(self, content: dict[str, Any]) -> dict[str, Any]:
        """通用协调功能"""
        return {
            "coordination_type": "general",
            "content": content,
            "coordination_result": "General coordination completed",
            "available_agents": [
                self.search_agent.agent_id,
                self.analysis_agent.agent_id,
                self.creative_agent.agent_id,
            ],
        }

    async def _task_processing_loop(self):
        """任务处理循环 - 支持取消"""
        try:
            while True:
                try:
                    # 从队列获取任务
                    task_definition = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)

                    # 处理任务
                    await self._process_task_definition(task_definition)

                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"❌ 任务处理循环异常: {e}")
        except asyncio.CancelledError:
            # 内存泄露修复: 正确处理取消信号
            logger.info("📋 任务处理循环已收到取消信号，正在退出...")
            raise  # 重新抛出以让调用者知道

    async def _process_task_definition(self, task_definition: TaskDefinition):
        """处理任务定义"""
        task_id = task_definition.task_id

        try:
            # 创建任务执行记录
            execution = TaskExecution(
                task_definition=task_definition,
                status=TaskStatus.ASSIGNED,
                assigned_agents=task_definition.required_agents,
                start_time=datetime.now().isoformat(),
            )

            self.active_tasks[task_id] = execution

            # 执行任务协调逻辑
            # 这里可以根据工作流类型执行不同的协调策略
            result = await self._coordinate_task_execution(task_definition)

            # 更新执行状态
            execution.status = (
                TaskStatus.COMPLETED if result.get("success", True) else TaskStatus.FAILED
            )
            execution.results = result
            execution.end_time = datetime.now().isoformat()

            # 移动到完成任务列表
            self.completed_tasks[task_id] = execution
            del self.active_tasks[task_id]

            # 更新性能统计
            self.tasks_coordinated += 1
            if execution.status == TaskStatus.COMPLETED:
                self.successful_tasks += 1

        except Exception as e:
            logger.error(f"❌ 任务处理失败 {task_id}: {e}")
            if task_id in self.active_tasks:
                self.active_tasks[task_id].status = TaskStatus.FAILED
                self.active_tasks[task_id].error_message = str(e)
                self.failed_tasks += 1

    async def _coordinate_task_execution(self, task_definition: TaskDefinition) -> dict[str, Any]:
        """协调任务执行"""
        # 简化的任务执行协调
        return {
            "success": True,
            "task_id": task_definition.task_id,
            "execution_result": "Task execution completed successfully",
            "execution_time": 1.0,
        }

    async def _performance_monitoring_loop(self):
        """性能监控循环 - 支持取消"""
        try:
            while True:
                try:
                    # 更新平均任务持续时间
                    if self.successful_tasks > 0:
                        total_time = sum(
                            (
                                datetime.fromisoformat(exec.end_time)
                                - datetime.fromisoformat(exec.start_time)
                            ).total_seconds()
                            for exec in self.completed_tasks.values()
                            if exec.start_time and exec.end_time
                        )
                        self.avg_task_duration = total_time / self.successful_tasks

                    # 内存泄露修复: 改进清理策略 - 基于时间和数量
                    await self._cleanup_old_tasks()

                    await asyncio.sleep(60)  # 每分钟监控一次

                except Exception as e:
                    logger.error(f"❌ 性能监控异常: {e}")
                    await asyncio.sleep(5)
        except asyncio.CancelledError:
            # 内存泄露修复: 正确处理取消信号
            logger.info("📊 性能监控循环已收到取消信号，正在退出...")
            raise  # 重新抛出以让调用者知道

    async def _cleanup_old_tasks(self):
        """清理旧任务 - 改进版本，基于时间和数量"""
        try:
            now = datetime.now()

            # 策略1: 清理超过1小时的任务
            cutoff_time = now - timedelta(hours=1)
            tasks_to_remove = [
                task_id
                for task_id, execution in self.completed_tasks.items()
                if execution.start_time
                and datetime.fromisoformat(execution.start_time) < cutoff_time
            ]

            # 策略2: 如果数量超过500，清理最旧的
            if len(self.completed_tasks) > 500:
                sorted_tasks = sorted(
                    self.completed_tasks.items(),
                    key=lambda x: x[1].start_time or "",
                )
                extra_count = len(self.completed_tasks) - 500
                for task_id, _ in sorted_tasks[:extra_count]:
                    if task_id not in tasks_to_remove:
                        tasks_to_remove.append(task_id)

            # 执行清理
            for task_id in tasks_to_remove:
                del self.completed_tasks[task_id]

            if tasks_to_remove:
                logger.debug(f"🧹 清理了 {len(tasks_to_remove)} 个旧任务")

        except Exception as e:
            logger.error(f"❌ 清理旧任务失败: {e}")

    async def shutdown(self):
        """内存泄露修复: 优雅关闭协调器，取消所有后台任务"""
        logger.info("🛑 开始关闭Agent协调器...")

        # 取消任务处理循环
        if self._task_processing_task and not self._task_processing_task.done():
            self._task_processing_task.cancel()
            try:
                await self._task_processing_task
            except asyncio.CancelledError:
                logger.debug("任务处理循环已取消")
                raise  # 重新抛出CancelledError

        # 取消性能监控循环
        if self._performance_monitoring_task and not self._performance_monitoring_task.done():
            self._performance_monitoring_task.cancel()
            try:
                await self._performance_monitoring_task
            except asyncio.CancelledError:
                logger.debug("性能监控循环已取消")
                raise  # 重新抛出CancelledError

        # 清空任务队列
        while not self.task_queue.empty():
            try:
                self.task_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

        logger.info("✅ Agent协调器已关闭")

    def __del__(self):
        """析构函数 - 确保资源被清理"""
        try:
            if hasattr(self, "_task_processing_task"):
                if self._task_processing_task and not self._task_processing_task.done():
                    self._task_processing_task.cancel()
            if hasattr(self, "_performance_monitoring_task"):
                if self._performance_monitoring_task and not self._performance_monitoring_task.done():
                    self._performance_monitoring_task.cancel()
        except Exception as e:
            # 析构函数中不抛出异常，但记录日志
            logger.debug(f"资源清理时出现异常（析构函数）: {e}")

    def get_coordination_stats(self) -> dict[str, Any]:
        """获取协调统计信息"""
        return {
            "coordinator_id": self.agent_id,
            "tasks_coordinated": self.tasks_coordinated,
            "successful_tasks": self.successful_tasks,
            "failed_tasks": self.failed_tasks,
            "success_rate": (
                self.successful_tasks / self.tasks_coordinated if self.tasks_coordinated > 0 else 0
            ),
            "avg_task_duration": self.avg_task_duration,
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "available_agents": 3,  # search, analysis, creative
            "coordination_strategies": self.coordination_strategies,
            "intelligent_routing_enabled": self.coordination_strategies.get(
                "intelligent_routing", False
            ),
            "load_balancing_enabled": self.coordination_strategies.get("load_balancing", False),
            "failure_recovery_enabled": self.coordination_strategies.get("failure_recovery", False),
        }


# 全局Agent协调器实例
_agent_coordinator = None


def get_agent_coordinator(config: Optional[dict[str, Any]] = None) -> AgentCoordinator:
    """获取全局Agent协调器实例"""
    global _agent_coordinator
    if _agent_coordinator is None:
        _agent_coordinator = AgentCoordinator(config=config)
    return _agent_coordinator
