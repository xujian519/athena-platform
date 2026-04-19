from __future__ import annotations
"""
Athena自主控制系统主控制器
整合平台管理、决策引擎和Agent协调
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from core.logging_config import setup_logging

from .agent_coordinator import AgentCoordinator, AgentRole
from .decision_engine import DecisionContext, DecisionEngine, DecisionType, Priority

# 导入自定义模块
from .platform_manager import PlatformManager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class ControlMode(Enum):
    """控制模式"""

    MANUAL = "manual"  # 手动控制
    SEMI_AUTONOMOUS = "semi_autonomous"  # 半自主
    FULLY_AUTONOMOUS = "fully_autonomous"  # 全自主


@dataclass
class AutonomousTask:
    """自主任务"""

    id: str
    name: str
    description: str
    agent: AgentRole
    priority: Priority
    created_at: datetime
    deadline: datetime | None = None
    status: str = "pending"  # pending, in_progress, completed, failed
    progress: float = 0.0
    result: dict[str, Any] | None = None


class AutonomousController:
    """Athena自主控制系统主控制器"""

    def __init__(self):
        self.platform_manager = PlatformManager()
        self.decision_engine = DecisionEngine()
        self.agent_coordinator = AgentCoordinator()

        self.control_mode = ControlMode.SEMI_AUTONOMOUS
        self.autonomous_tasks = {}
        self.system_goals = self._load_system_goals()

        # 监控和回调
        self.monitoring_callbacks = {}
        self.error_handlers = []

        # 控制历史
        self.control_history = []

        # 运行状态
        self.is_running = False
        self.start_time = None

    def _load_system_goals(self) -> dict[str, Any]:
        """加载系统目标"""
        return {
            "platform_health": {
                "target_uptime": 0.99,
                "target_response_time": 2.0,
                "target_error_rate": 0.01,
            },
            "performance": {
                "target_throughput": 1000,
                "target_cpu_usage": 0.7,
                "target_memory_usage": 0.8,
            },
            "security": {
                "target_vulnerability_scan": True,
                "target_access_control": 0.95,
                "target_threat_detection": True,
            },
            "cost_efficiency": {"target_resource_usage": 0.8, "target_operational_cost": 1.0},
            "agent_coordination": {
                "target_interaction_frequency": 10,
                "target_emotional_harmony": 0.8,
                "target_collaboration_success": 0.9,
            },
        }

    async def start_autonomous_control(
        self, mode: ControlMode = ControlMode.SEMI_AUTONOMOUS
    ) -> dict[str, Any]:
        """启动自主控制"""
        try:
            if self.is_running:
                return {"success": False, "error": "自主控制已在运行中"}

            self.control_mode = mode
            self.is_running = True
            self.start_time = datetime.now()

            # 记录启动事件
            self._record_control_event(
                "autonomous_control_started",
                {"mode": mode.value, "timestamp": self.start_time.isoformat()},
            )

            # 启动监控任务
            if mode in [ControlMode.SEMI_AUTONOMOUS, ControlMode.FULLY_AUTONOMOUS]:
                asyncio.create_task(self._run_autonomous_monitoring())
                asyncio.create_task(self._run_autonomous_tasks())

            logger.info(f"自主控制系统已启动 (模式: {mode.value})")
            return {"success": True, "mode": mode.value}

        except Exception as e:
            logger.error(f"启动自主控制失败: {e}")
            return {"success": False, "error": str(e)}

    async def stop_autonomous_control(self) -> dict[str, Any]:
        """停止自主控制"""
        try:
            if not self.is_running:
                return {"success": False, "error": "自主控制未在运行"}

            self.is_running = False

            # 记录停止事件
            self._record_control_event(
                "autonomous_control_stopped",
                {
                    "running_duration": (datetime.now() - self.start_time).total_seconds(),
                    "timestamp": datetime.now().isoformat(),
                },
            )

            # 停止所有自主任务
            for task_id, task in self.autonomous_tasks.items():
                if task.status == "in_progress":
                    await self.cancel_task(task_id)

            logger.info("自主控制系统已停止")
            return {"success": True}

        except Exception as e:
            logger.error(f"停止自主控制失败: {e}")
            return {"success": False, "error": str(e)}

    async def _run_autonomous_monitoring(self):
        """运行自主监控"""
        try:
            while self.is_running:
                # 监控平台状态
                platform_status = await self.platform_manager.get_platform_status()

                # 分析并处理问题
                await self._analyze_and_handle_issues(platform_status)

                # 更新系统目标进度
                await self._update_goal_progress(platform_status)

                # 等待下一次监控
                await asyncio.sleep(30)  # 30秒监控间隔

        except Exception as e:
            logger.error(f"自主监控出错: {e}")
            await self._handle_error("monitoring_error", e)

    async def _run_autonomous_tasks(self):
        """运行自主任务"""
        try:
            while self.is_running:
                # 检查待执行任务
                pending_tasks = [
                    t
                    for t in self.autonomous_tasks.values()
                    if t.status == "pending" and t.agent == AgentRole.ATHENA
                ]

                # 按优先级执行任务
                pending_tasks.sort(key=lambda x: x.priority.value, reverse=True)

                for task in pending_tasks:
                    if not self.is_running:
                        break

                    await self._execute_autonomous_task(task)
                    await asyncio.sleep(1)  # 任务间隔

                # 检查已完成的任务
                completed_tasks = [
                    t
                    for t in self.autonomous_tasks.values()
                    if t.status == "completed" and t.agent == AgentRole.XIAONUO
                ]

                for task in completed_tasks:
                    await self._handle_task_completion(task)
                    await asyncio.sleep(1)

                await asyncio.sleep(5)  # 任务检查间隔

        except Exception as e:
            logger.error(f"自主任务执行出错: {e}")
            await self._handle_error("task_execution_error", e)

    async def create_autonomous_task(
        self,
        name: str,
        description: str,
        agent: AgentRole,
        priority: Priority,
        deadline: datetime | None = None,
    ) -> str:
        """创建自主任务"""
        try:
            task_id = str(len(self.autonomous_tasks) + 1)
            task = AutonomousTask(
                id=task_id,
                name=name,
                description=description,
                agent=agent,
                priority=priority,
                created_at=datetime.now(),
                deadline=deadline,
            )

            self.autonomous_tasks[task_id] = task

            # 如果是Athena任务,立即评估并可能开始执行
            if agent == AgentRole.ATHENA and self.control_mode != ControlMode.MANUAL:
                await self._evaluate_and_schedule_task(task)

            logger.info(f"创建自主任务: {name} (ID: {task_id}, Agent: {agent.value})")
            return task_id

        except Exception as e:
            logger.error(f"创建自主任务失败: {e}")
            return ""

    async def _evaluate_and_schedule_task(self, task: AutonomousTask):
        """评估并调度任务"""
        try:
            # 获取当前上下文
            await self._get_current_context()

            # 使用决策引擎评估任务
            decision_context = DecisionContext(
                platform_status=await self.platform_manager.get_platform_status(),
                system_metrics=await self._get_system_metrics(),
                user_intent=task.description,
            )

            # 决定是否执行任务
            should_execute = await self._should_execute_task(task, decision_context)

            if should_execute:
                task.status = "in_progress"
                logger.info(f"开始执行任务: {task.name}")

        except Exception as e:
            logger.error(f"评估任务失败: {e}")

    async def _should_execute_task(self, task: AutonomousTask, context: DecisionContext) -> bool:
        """判断是否应该执行任务"""
        try:
            # 检查优先级
            if task.priority.value >= Priority.HIGH.value:
                return True

            # 检查平台状态
            platform_status = context.platform_status
            if isinstance(platform_status, dict):
                # 如果平台有问题,高优先级任务应该执行
                if platform_status.get("platform_status") in ["degraded", "critical"]:
                    return task.priority.value >= Priority.HIGH.value

            # 检查Agent状态
            agent_status = await self.agent_coordinator.get_agent_status(task.agent)
            if agent_status.get("status") == "active":
                # 检查Agent的情感状态
                emotions = agent_status.get("emotions", {})
                if task.agent == AgentRole.ATHENA:
                    # Athena需要有足够的责任感和信心
                    if (
                        emotions.get("responsibility", 0) < 0.6
                        or emotions.get("confidence", 0) < 0.5
                    ):
                        return False
                elif task.agent == AgentRole.XIAONUO:
                    # 小诺需要有同理心
                    if emotions.get("empathy", 0) < 0.5:
                        return False

            return task.priority.value >= Priority.MEDIUM.value

        except Exception as e:
            logger.warning(f"判断任务执行条件失败: {e}")
            return False

    async def _execute_autonomous_task(self, task: AutonomousTask):
        """执行自主任务"""
        try:
            task.status = "in_progress"
            task.progress = 0.1

            # 记录任务开始
            self._record_control_event(
                "task_started",
                {
                    "task_id": task.id,
                    "task_name": task.name,
                    "agent": task.agent.value,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            # 根据Agent类型执行任务
            if task.agent == AgentRole.ATHENA:
                result = await self._execute_athena_task(task)
            elif task.agent == AgentRole.XIAONUO:
                result = await self._execute_xiaonuo_task(task)

            # 更新任务状态
            task.status = "completed"
            task.progress = 1.0
            task.result = result

            # 记录任务完成
            self._record_control_event(
                "task_completed",
                {
                    "task_id": task.id,
                    "task_name": task.name,
                    "agent": task.agent.value,
                    "success": True,
                    "timestamp": datetime.now().isoformat(),
                },
            )

        except Exception as e:
            task.status = "failed"
            task.progress = 0.0
            logger.error(f"执行任务失败: {task.name}, 错误: {e}")

            # 记录任务失败
            self._record_control_event(
                "task_failed",
                {
                    "task_id": task.id,
                    "task_name": task.name,
                    "agent": task.agent.value,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                },
            )

    async def _execute_athena_task(self, task: AutonomousTask) -> dict[str, Any]:
        """执行Athena任务"""
        try:
            # 获取平台状态
            platform_status = await self.platform_manager.get_platform_status()

            # 创建决策上下文
            decision_context = DecisionContext(
                platform_status=platform_status,
                system_metrics=await self._get_system_metrics(),
                user_intent=task.description,
                agent_emotions=self.agent_coordinator.agent_states[AgentRole.ATHENA]["emotions"],
            )

            # 基于任务类型进行决策
            if "监控" in task.description or "检查" in task.description:
                decision_type = DecisionType.OPTIMIZATION
            elif "错误" in task.description or "故障" in task.description:
                decision_type = DecisionType.ERROR_RECOVERY
            elif "启动" in task.description or "停止" in task.description:
                decision_type = DecisionType.PLATFORM_CONTROL
            else:
                decision_type = DecisionType.SERVICE_MANAGEMENT

            # 使用决策引擎
            decision, _confidence = await self.decision_engine.make_decision(
                decision_context, decision_type
            )

            # 执行决策
            if decision.action == "restart_service":
                # 解析服务名
                service_name = self._extract_service_name_from_description(task.description)
                if service_name:
                    result = await self.platform_manager.restart_service(service_name)
            elif decision.action == "start_service":
                service_name = self._extract_service_name_from_description(task.description)
                if service_name:
                    result = await self.platform_manager.start_service(service_name)
            elif decision.action == "stop_service":
                service_name = self._extract_service_name_from_description(task.description)
                if service_name:
                    result = await self.platform_manager.stop_service(service_name)
            elif decision.action == "restart_platform":
                result = await self.platform_manager.restart_platform()
            else:
                result = {"action": decision.action, "message": "决策已记录,等待执行"}

            # 更新决策引擎的成功状态
            self.decision_engine.update_decision_success(
                decision.action, result.get("success", False), result
            )

            return result

        except Exception as e:
            logger.error(f"执行Athena任务失败: {e}")
            return {"error": str(e)}

    async def _execute_xiaonuo_task(self, task: AutonomousTask) -> dict[str, Any]:
        """执行小诺任务"""
        try:
            # 小诺主要提供情感支持和用户体验优化
            result = {
                "action": "emotional_support",
                "message": "小诺已完成情感支持任务",
                "user_experience_improvement": True,
                "emotional_wellness": 0.95,
            }

            # 更新小诺的情感状态
            self.agent_coordinator.agent_states[AgentRole.XIAONUO]["emotions"].update(
                {"joy": 0.9, "confidence": 0.85, "empathy": 0.95}
            )

            return result

        except Exception as e:
            logger.error(f"执行小诺任务失败: {e}")
            return {"error": str(e)}

    def _extract_service_name_from_description(self, description: str) -> str | None:
        """从描述中提取服务名"""
        service_keywords = {
            "api": "api-gateway",
            "网关": "api-gateway",
            "认知": "ai-cognitive",
            "感知": "ai-perception",
            "记忆": "memory-services",
            "数据库": "postgres",
            "缓存": "redis",
            "向量": "qdrant",
            "监控": "prometheus",
            "仪表板": "grafana",
            "浏览器": "browser-automation",
        }

        for keyword, service in service_keywords.items():
            if keyword in description:
                return service

        return None

    async def _handle_task_completion(self, task: AutonomousTask):
        """处理任务完成"""
        try:
            # 任务完成后,从活动任务列表中移除
            if task.id in self.autonomous_tasks:
                del self.autonomous_tasks[task.id]

            # 如果有截止时间,清理过期任务
            await self._cleanup_expired_tasks()

        except Exception as e:
            logger.warning(f"处理任务完成失败: {e}")

    async def _cleanup_expired_tasks(self):
        """清理过期任务"""
        try:
            now = datetime.now()
            expired_tasks = [
                task_id
                for task_id, task in self.autonomous_tasks.items()
                if task.deadline and task.deadline < now and task.status != "in_progress"
            ]

            for task_id in expired_tasks:
                del self.autonomous_tasks[task_id]
                logger.info(f"清理过期任务: {task_id}")

        except Exception as e:
            logger.warning(f"清理过期任务失败: {e}")

    async def cancel_task(self, task_id: str) -> dict[str, Any]:
        """取消任务"""
        try:
            if task_id not in self.autonomous_tasks:
                return {"success": False, "error": "任务不存在"}

            task = self.autonomous_tasks[task_id]
            task.status = "cancelled"

            del self.autonomous_tasks[task_id]

            logger.info(f"任务已取消: {task.name} (ID: {task_id})")
            return {"success": True}

        except Exception as e:
            logger.error(f"取消任务失败: {e}")
            return {"success": False, "error": str(e)}

    async def _analyze_and_handle_issues(self, platform_status: dict[str, Any]):
        """分析并处理问题"""
        try:
            if not isinstance(platform_status, dict):
                return

            issues = []

            # 检查服务状态
            service_status_counts = platform_status.get("service_status_counts", {})
            error_count = service_status_counts.get("error", 0)
            total_services = platform_status.get("total_services", 1)

            if error_count > 0:
                issues.append(
                    {
                        "type": "service_failure",
                        "severity": "high" if error_count > total_services * 0.3 else "medium",
                        "description": f"有 {error_count} 个服务异常",
                        "data": {"error_count": error_count, "total_services": total_services},
                    }
                )

            # 检查系统资源
            if "system_info" in platform_status:
                system_info = platform_status["system_info"]
                if system_info.get("cpu_percent", 0) > 90:
                    issues.append(
                        {
                            "type": "resource_overload",
                            "severity": "high",
                            "description": f"CPU使用率过高: {system_info['cpu_percent']}%",
                            "data": {"cpu_percent": system_info["cpu_percent"]},
                        }
                    )

                if system_info.get("memory_percent", 0) > 90:
                    issues.append(
                        {
                            "type": "resource_overload",
                            "severity": "high",
                            "description": f"内存使用率过高: {system_info['memory_percent']}%",
                            "data": {"memory_percent": system_info["memory_percent"]},
                        }
                    )

            # 处理发现的问题
            for issue in issues:
                await self._handle_issue(issue)

        except Exception as e:
            logger.warning(f"分析问题失败: {e}")

    async def _handle_issue(self, issue: dict[str, Any]):
        """处理发现的问题"""
        try:
            issue_type = issue.get("type")
            severity = issue.get("severity", "medium")

            # 创建自主任务来处理问题
            if issue_type == "service_failure" and severity == "high":
                await self.create_autonomous_task(
                    name="紧急服务恢复",
                    description=f"处理异常服务: {issue['description']}",
                    agent=AgentRole.ATHENA,
                    priority=Priority.CRITICAL,
                    deadline=datetime.now() + timedelta(minutes=5),
                )

            elif issue_type == "resource_overload":
                await self.create_autonomous_task(
                    name="资源优化",
                    description=f"优化系统资源使用: {issue['description']}",
                    agent=AgentRole.ATHENA,
                    priority=Priority.HIGH,
                    deadline=datetime.now() + timedelta(minutes=10),
                )

        except Exception as e:
            logger.warning(f"处理问题失败: {e}")

    async def _get_current_context(self) -> DecisionContext:
        """获取当前决策上下文"""
        try:
            return DecisionContext(
                platform_status=await self.platform_manager.get_platform_status(),
                system_metrics=await self._get_system_metrics(),
                history=self.decision_engine.decision_history[-10:],
                agent_emotions={
                    "athena": self.agent_coordinator.agent_states[AgentRole.ATHENA]["emotions"],
                    "xiaonuo": self.agent_coordinator.agent_states[AgentRole.XIAONUO]["emotions"],
                },
            )

        except Exception as e:
            logger.warning(f"获取上下文失败: {e}")
            return DecisionContext()

    async def _get_system_metrics(self) -> dict[str, float]:
        """获取系统指标"""
        try:
            platform_status = await self.platform_manager.get_platform_status()
            if "system_info" in platform_status:
                return platform_status["system_info"]
            return {}

        except Exception as e:
            logger.warning(f"获取系统指标失败: {e}")
            return {}

    async def _update_goal_progress(self, platform_status: dict[str, Any]):
        """更新目标进度"""
        try:
            if not isinstance(platform_status, dict):
                return

            # 更新平台健康目标进度
            if "service_status_counts" in platform_status:
                error_count = platform_status["service_status_counts"].get("error", 0)
                total_services = platform_status.get("total_services", 1)
                uptime_rate = (total_services - error_count) / total_services
                self.system_goals["platform_health"]["current_uptime"] = uptime_rate

            # 更新系统指标进度
            if "system_info" in platform_status:
                cpu_usage = platform_status["system_info"].get("cpu_percent", 0) / 100
                memory_usage = platform_status["system_info"].get("memory_percent", 0) / 100
                self.system_goals["performance"]["current_cpu_usage"] = cpu_usage
                self.system_goals["performance"]["current_memory_usage"] = memory_usage

        except Exception as e:
            logger.warning(f"更新目标进度失败: {e}")

    def _record_control_event(self, event_type: str, event_data: dict[str, Any]) -> Any:
        """记录控制事件"""
        try:
            event = {
                "timestamp": datetime.now().isoformat(),
                "type": event_type,
                "data": event_data,
            }

            self.control_history.append(event)

            # 保持历史记录在合理范围内
            if len(self.control_history) > 1000:
                self.control_history = self.control_history[-500:]

        except Exception as e:
            logger.warning(f"记录控制事件失败: {e}")

    async def _handle_error(self, error_type: str, error: Exception):
        """处理错误"""
        try:
            for handler in self.error_handlers:
                await handler(error_type, error)

        except Exception as e:
            logger.error(f"错误处理器执行失败: {e}")

    def add_error_handler(self, handler: Callable) -> None:
        """添加错误处理器"""
        self.error_handlers.append(handler)

    def add_monitoring_callback(self, callback: Callable) -> None:
        """添加监控回调"""
        self.monitoring_callbacks[callback.__name__] = callback

    async def get_system_status(self) -> dict[str, Any]:
        """获取系统整体状态"""
        try:
            # 获取平台状态
            platform_status = await self.platform_manager.get_platform_status()

            # 获取Agent状态
            athena_status = await self.agent_coordinator.get_agent_status(AgentRole.ATHENA)
            xiaonuo_status = await self.agent_coordinator.get_agent_status(AgentRole.XIAONUO)

            # 获取决策统计
            decision_stats = self.decision_engine.get_decision_stats()

            # 获取协作统计
            collaboration_stats = self.agent_coordinator.get_collaboration_stats()

            # 获取关系健康状态
            relationship_health = await self.agent_coordinator.analyze_relationship_health()

            # 获取任务统计
            task_stats = {
                "total_tasks": len(self.autonomous_tasks),
                "pending_tasks": len(
                    [t for t in self.autonomous_tasks.values() if t.status == "pending"]
                ),
                "in_progress_tasks": len(
                    [t for t in self.autonomous_tasks.values() if t.status == "in_progress"]
                ),
                "completed_tasks": len(
                    [t for t in self.autonomous_tasks.values() if t.status == "completed"]
                ),
                "failed_tasks": len(
                    [t for t in self.autonomous_tasks.values() if t.status == "failed"]
                ),
            }

            return {
                "autonomous_control": {
                    "is_running": self.is_running,
                    "control_mode": self.control_mode.value,
                    "start_time": self.start_time.isoformat() if self.start_time else None,
                    "running_duration": (
                        (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
                    ),
                },
                "platform": platform_status,
                "agents": {"athena": athena_status, "xiaonuo": xiaonuo_status},
                "decision_engine": decision_stats,
                "collaboration": collaboration_stats,
                "relationship_health": relationship_health,
                "tasks": task_stats,
                "goals": self.system_goals,
                "control_events": len(self.control_history),
            }

        except Exception as e:
            logger.error(f"获取系统状态失败: {e}")
            return {"error": str(e)}

    async def set_control_mode(self, mode: ControlMode) -> dict[str, Any]:
        """设置控制模式"""
        try:
            old_mode = self.control_mode
            self.control_mode = mode

            # 如果从手动切换到自主模式,启动自主控制
            if old_mode == ControlMode.MANUAL and mode in [
                ControlMode.SEMI_AUTONOMOUS,
                ControlMode.FULLY_AUTONOMOUS,
            ]:
                await self.start_autonomous_control(mode)
            # 如果从自主切换到手动,停止自主控制
            elif (
                old_mode in [ControlMode.SEMI_AUTONOMOUS, ControlMode.FULLY_AUTONOMOUS]
                and mode == ControlMode.MANUAL
            ):
                await self.stop_autonomous_control()

            return {"success": True, "mode": mode.value}

        except Exception as e:
            logger.error(f"设置控制模式失败: {e}")
            return {"success": False, "error": str(e)}


# 全局自主控制器实例
autonomous_controller = AutonomousController()
