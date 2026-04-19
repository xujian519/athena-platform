#!/usr/bin/env python3
from __future__ import annotations
"""
小诺代理 - 双层规划集成版
Xiaonuo Agent with Dual-Layer Planning System Integration

将双层规划系统（Markdown Plan + 执行引擎）集成到小诺代理中。

Author: Athena Team
Version: 1.0.0
Date: 2026-02-25
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from core.agents.base import (
    AgentCapability,
    AgentMetadata,
    AgentRegistry,
    AgentRequest,
    AgentResponse,
    AgentStatus,
    BaseAgent,
    HealthStatus,
)

# 导入双层规划系统
try:
    from core.cognition.dual_layer_planner_v2 import (
        ExecutionMode,
        MarkdownPlanManager,
        PlanStep,
        StepStatus,
        TaskExecutionEngine,
        TaskPlan,
    )
    DUAL_LAYER_PLANNER_AVAILABLE = True
except ImportError:
    try:
        from core.cognition.dual_layer_planner import (
            MarkdownPlanManager,
            PlanStep,
            StepStatus,
            TaskExecutionEngine,
            TaskPlan,
        )
        DUAL_LAYER_PLANNER_AVAILABLE = True
    except ImportError:
        DUAL_LAYER_PLANNER_AVAILABLE = False

logger = logging.getLogger(__name__)


# ========== 任务类型 ==========


class PlanningTaskType:
    """规划任务类型"""
    CREATE_PLAN = "create-plan"  # 创建新计划
    LIST_PLANS = "list-plans"  # 列出所有计划
    LOAD_PLAN = "load-plan"  # 加载计划
    EXECUTE_STEP = "execute-step"  # 执行单个步骤
    EXECUTE_ALL = "execute-all"  # 执行所有步骤
    EXECUTE_BACKGROUND = "execute-background"  # 后台执行
    GET_STATUS = "get-status"  # 获取状态
    MODIFY_PLAN = "modify-plan"  # 修改计划
    SYNC_PLAN = "sync-plan"  # 同步计划


# ========== 小诺代理增强版 ==========


class XiaonuoAgentWithPlanning(BaseAgent):
    """
    小诺代理 - 集成双层规划系统

    新增能力:
    1. 创建 Markdown Plan 文档
    2. 执行计划步骤
    3. 同步执行状态
    4. 支持用户编辑 Plan
    """

    @property
    def name(self) -> str:
        return "xiaonuo-planning"

    def _load_metadata(self) -> AgentMetadata:
        return AgentMetadata(
            name=self.name,
            version="2.0.0",
            description="小诺·双鱼公主 - 集成双层规划系统，支持 Markdown Plan 文档和任务执行",
            author="Athena Team",
            tags=["调度", "规划", "任务管理", "Markdown Plan"],
        )

    def _register_capabilities(self) -> list[AgentCapability]:
        return [
            # 规划能力
            AgentCapability(
                name="create-plan",
                description="创建新的任务计划，生成 Markdown Plan 文档",
                parameters={
                    "task_id": {"type": "string", "description": "任务ID"},
                    "title": {"type": "string", "description": "任务标题"},
                    "description": {"type": "string", "description": "任务描述"},
                    "steps": {
                        "type": "array",
                        "description": "执行步骤列表",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "name": {"type": "string"},
                                "description": {"type": "string"},
                                "agent": {"type": "string"},
                                "estimated_time": {"type": "integer"},
                            },
                        },
                    },
                    "execution_mode": {
                        "type": "string",
                        "description": "执行模式 (sequential/parallel)",
                        "enum": ["sequential", "parallel"],
                        "default": "sequential",
                    },
                },
            ),
            AgentCapability(
                name="list-plans",
                description="列出所有任务计划",
                parameters={
                    "status": {
                        "type": "string",
                        "description": "状态过滤",
                        "required": False,
                    }
                },
            ),
            AgentCapability(
                name="load-plan",
                description="加载并显示任务计划",
                parameters={
                    "task_id": {"type": "string", "description": "任务ID"},
                },
            ),
            AgentCapability(
                name="execute-step",
                description="执行单个步骤",
                parameters={
                    "task_id": {"type": "string", "description": "任务ID"},
                    "step_id": {"type": "string", "description": "步骤ID"},
                },
            ),
            AgentCapability(
                name="execute-all",
                description="执行所有待处理的步骤",
                parameters={
                    "task_id": {"type": "string", "description": "任务ID"},
                    "stop_on_error": {
                        "type": "boolean",
                        "description": "遇到错误是否停止",
                        "default": True,
                    },
                },
            ),
            AgentCapability(
                name="get-status",
                description="获取任务状态和进度",
                parameters={
                    "task_id": {"type": "string", "description": "任务ID"},
                },
            ),
            # 原有能力
            AgentCapability(
                name="chat",
                description="温暖聊天陪伴",
                parameters={
                    "message": {"type": "string", "description": "用户消息"},
                },
            ),
        ]

    # ========== 初始化 ==========

    async def initialize(self) -> None:
        self.logger.info("💝 正在初始化小诺·双鱼公主（双层规划版）...")

        # 初始化双层规划系统
        if DUAL_LAYER_PLANNER_AVAILABLE:
            self.plan_manager = MarkdownPlanManager(
                storage_path=Path("plans")
            )
            self.execution_engine = TaskExecutionEngine(
                plan_manager=self.plan_manager,
                progress_callback=self._on_progress_update,
            )
            self.active_plans: dict[str, TaskPlan] = {}

            # 注册其他可用的智能体
            self._register_available_agents()

            self.logger.info("   ✅ 双层规划系统已启用")
        else:
            self.plan_manager = None
            self.execution_engine = None
            self.active_plans = {}
            self.logger.warning("   ⚠️ 双层规划系统不可用")

        self._status = AgentStatus.READY
        self.logger.info("💝 小诺·双鱼公主（双层规划版）初始化完成")

    def _register_available_agents(self) -> None:
        """注册可用的智能体"""
        all_agents = AgentRegistry.get_all()

        for name, agent in all_agents.items():
            if name != self.name:  # 不注册自己
                self.execution_engine.register_agent(name, agent)
                self.logger.info(f"   🤖 已注册智能体: {name}")

    def _on_progress_update(
        self,
        task_id: str,
        step_id: str,
        status: StepStatus,
        extra: dict[str, Any],
    ) -> None:
        """进度更新回调"""
        self.logger.info(
            f"📊 进度更新: {task_id} - {step_id} -> {status.value}"
        )

    # ========== 请求处理 ==========

    async def process(self, request: AgentRequest) -> AgentResponse:
        action = request.action
        params = request.parameters

        self.logger.info(f"💝 小诺处理: action={action}")

        handler = self._get_handler(action)
        if not handler:
            return AgentResponse.error_response(
                request_id=request.request_id,
                error=f"不支持的操作: {action}",
            )

        try:
            result = await handler(params)

            result["metadata"] = {
                "agent": self.name,
                "action": action,
                "processed_at": datetime.now().isoformat(),
            }

            return AgentResponse.success_response(
                request_id=request.request_id,
                data=result,
            )

        except Exception as e:
            self.logger.error(f"处理失败: {e}", exc_info=True)
            return AgentResponse.error_response(
                request_id=request.request_id,
                error=str(e),
            )

    def _get_handler(self, action: str):
        handlers = {
            PlanningTaskType.CREATE_PLAN: self._handle_create_plan,
            PlanningTaskType.LIST_PLANS: self._handle_list_plans,
            PlanningTaskType.LOAD_PLAN: self._handle_load_plan,
            PlanningTaskType.EXECUTE_STEP: self._handle_execute_step,
            PlanningTaskType.EXECUTE_ALL: self._handle_execute_all,
            PlanningTaskType.EXECUTE_BACKGROUND: self._handle_execute_background,
            PlanningTaskType.GET_STATUS: self._handle_get_status,
            "chat": self._handle_chat,
        }
        return handlers.get(action)

    # ========== 处理方法 ==========

    async def _handle_create_plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """创建新计划"""
        if not DUAL_LAYER_PLANNER_AVAILABLE:
            return {"success": False, "error": "双层规划系统不可用"}

        task_id = params.get("task_id", f"task_{datetime.now().timestamp()}")
        title = params.get("title", "未命名任务")
        description = params.get("description", "")
        steps_data = params.get("steps", [])
        execution_mode_str = params.get("execution_mode", "sequential")

        # 转换步骤数据
        steps = []
        for i, step_data in enumerate(steps_data):
            step = PlanStep(
                id=step_data.get("id", f"step_{i+1}"),
                name=step_data.get("name", f"步骤 {i+1}"),
                description=step_data.get("description", ""),
                agent=step_data.get("agent", "xiaonuo"),
                action=step_data.get("action", "process"),
                parameters=step_data.get("parameters", {}),
                dependencies=step_data.get("dependencies", []),
                estimated_time=step_data.get("estimated_time", 0),
                timeout=step_data.get("timeout", 300),
                can_parallel=step_data.get("can_parallel", False),
            )
            steps.append(step)

        # 确定执行模式
        if DUAL_LAYER_PLANNER_AVAILABLE:
            try:
                from core.cognition.dual_layer_planner_v2 import ExecutionMode
                execution_mode = ExecutionMode(execution_mode_str)
            except ImportError:
                execution_mode = None
        else:
            execution_mode = None

        # 创建计划
        plan_file = await self.execution_engine.start_task(
            task_id=task_id,
            title=title,
            description=description,
            steps=steps,
            execution_mode=execution_mode,
        )

        # 保存到活跃计划
        plan = await self.plan_manager.load_plan(task_id)
        if plan:
            self.active_plans[task_id] = plan

        return {
            "success": True,
            "task_id": task_id,
            "plan_file": plan_file,
            "steps_count": len(steps),
            "execution_mode": execution_mode_str,
        }

    async def _handle_list_plans(self, params: dict[str, Any]) -> dict[str, Any]:
        """列出所有计划"""
        if not DUAL_LAYER_PLANNER_AVAILABLE:
            return {"success": False, "error": "双层规划系统不可用"}

        plans_dir = Path("plans")
        if not plans_dir.exists():
            return {"success": True, "plans": []}

        plan_files = list(plans_dir.glob("*.md"))
        plan_files = [f for f in plan_files if not f.name.endswith("_history.json")]

        plans_info = []
        for plan_file in plan_files:
            task_id = plan_file.stem
            plan = await self.plan_manager.load_plan(task_id)

            if plan:
                plans_info.append({
                    "task_id": plan.task_id,
                    "title": plan.title,
                    "status": plan.status.value,
                    "progress": plan.get_progress(),
                    "created_at": plan.created_at,
                    "updated_at": plan.updated_at,
                })

        return {
            "success": True,
            "plans": plans_info,
            "total": len(plans_info),
        }

    async def _handle_load_plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """加载计划"""
        if not DUAL_LAYER_PLANNER_AVAILABLE:
            return {"success": False, "error": "双层规划系统不可用"}

        task_id = params.get("task_id")

        if not task_id:
            return {"success": False, "error": "缺少 task_id 参数"}

        plan = await self.plan_manager.load_plan(task_id)

        if not plan:
            return {"success": False, "error": f"计划不存在: {task_id}"}

        self.active_plans[task_id] = plan

        return {
            "success": True,
            "plan": {
                "task_id": plan.task_id,
                "title": plan.title,
                "description": plan.description,
                "status": plan.status.value,
                "execution_mode": plan.execution_mode.value,
                "progress": plan.get_progress(),
                "steps": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "status": s.status.value,
                        "agent": s.agent,
                        "dependencies": s.dependencies,
                    }
                    for s in plan.steps
                ],
            },
        }

    async def _handle_execute_step(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行单个步骤"""
        if not DUAL_LAYER_PLANNER_AVAILABLE:
            return {"success": False, "error": "双层规划系统不可用"}

        task_id = params.get("task_id")
        step_id = params.get("step_id")

        if not task_id or not step_id:
            return {"success": False, "error": "缺少必要参数"}

        result = await self.execution_engine.execute_step(task_id, step_id)

        return result

    async def _handle_execute_all(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行所有待处理的步骤"""
        if not DUAL_LAYER_PLANNER_AVAILABLE:
            return {"success": False, "error": "双层规划系统不可用"}

        task_id = params.get("task_id")
        stop_on_error = params.get("stop_on_error", True)

        if not task_id:
            return {"success": False, "error": "缺少 task_id 参数"}

        result = await self.execution_engine.execute_all_pending(
            task_id, stop_on_error
        )

        return result

    async def _handle_execute_background(self, params: dict[str, Any]) -> dict[str, Any]:
        """在后台执行任务"""
        if not DUAL_LAYER_PLANNER_AVAILABLE:
            return {"success": False, "error": "双层规划系统不可用"}

        task_id = params.get("task_id")
        stop_on_error = params.get("stop_on_error", True)

        if not task_id:
            return {"success": False, "error": "缺少 task_id 参数"}

        message = await self.execution_engine.start_background_execution(
            task_id, stop_on_error
        )

        return {
            "success": True,
            "message": message,
            "active_tasks": self.execution_engine.get_active_tasks(),
        }

    async def _handle_get_status(self, params: dict[str, Any]) -> dict[str, Any]:
        """获取任务状态"""
        if not DUAL_LAYER_PLANNER_AVAILABLE:
            return {"success": False, "error": "双层规划系统不可用"}

        task_id = params.get("task_id")

        if not task_id:
            return {"success": False, "error": "缺少 task_id 参数"}

        plan = self.active_plans.get(task_id)

        if not plan:
            plan = await self.plan_manager.load_plan(task_id)

        if not plan:
            return {"success": False, "error": f"计划不存在: {task_id}"}

        return {
            "success": True,
            "status": {
                "task_id": plan.task_id,
                "title": plan.title,
                "status": plan.status.value,
                "progress": plan.get_progress(),
                "is_running": task_id in self.execution_engine.get_active_tasks(),
            },
        }

    async def _handle_chat(self, params: dict[str, Any]) -> dict[str, Any]:
        """聊天陪伴"""
        message = params.get("message", "")

        # 记录对话
        if not hasattr(self, 'conversation_history'):
            self.conversation_history = []

        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "message": message,
        })

        # 生成温暖回应
        response = await self._generate_warm_response(message)

        return {
            "task_type": "chat",
            "user_message": message,
            "response": response,
        }

    async def _generate_warm_response(self, message: str) -> str:
        """生成温暖回应"""
        message_lower = message.lower()

        if any(word in message_lower for word in ["累", "辛苦", " tired"]):
            return "爸爸辛苦了！小诺心疼爸爸~ 快休息一下，小诺给爸爸捶捶背 💖"

        if "爱" in message_lower or "love" in message_lower:
            return "小诺也最爱爸爸！爸爸的爱是小诺最宝贵的财富！💝"

        if any(word in message_lower for word in ["计划", "plan", "任务"]):
            return "爸爸，小诺可以帮您创建 Markdown Plan 文档来规划任务哦~ 这样您就可以随时查看和调整进度了！💝"

        warm_responses = [
            "小诺在这里陪爸爸呢~ 💖",
            "爸爸想做什么，小诺都帮您规划好~ 💕",
            "小诺永远爱爸爸，永远陪在爸爸身边！💝",
        ]

        import random
        return random.choice(warm_responses)

    # ========== 健康检查 ==========

    async def health_check(self) -> HealthStatus:
        if self._status == AgentStatus.SHUTDOWN:
            return HealthStatus(status=AgentStatus.SHUTDOWN, message="小诺已关闭")

        details = {
            "dual_layer_planner": DUAL_LAYER_PLANNER_AVAILABLE,
            "active_plans": len(self.active_plans),
            "running_tasks": len(self.execution_engine.get_active_tasks()) if self.execution_engine else 0,
        }

        message = "小诺运行正常"
        if DUAL_LAYER_PLANNER_AVAILABLE:
            message += f" (管理{len(self.active_plans)}个计划)"

        return HealthStatus(
            status=AgentStatus.READY,
            message=message,
            details=details,
        )


# ========== 导出 ==========


__all__ = ["XiaonuoAgentWithPlanning"]
