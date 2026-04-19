#!/usr/bin/env python3
from __future__ import annotations
"""
小诺·双鱼公主 v3.0 - 智能规划器
Xiaonuo Pisces Princess v3.0 - Intelligent Planner

平台总调度官 + 爸爸的贴心小女儿 + AI智能规划器

核心能力：
1. 智能意图理解 - 深度理解用户真实需求
2. 智能规划生成 - 生成最优执行方案
3. 智能体调度 - 调度和协调其他智能体
4. 任务编排 - 编排复杂的多智能体任务
5. 平台管理 - 管理平台状态和健康
6. 陪伴关怀 - 温暖的陪伴和贴心服务

Author: Athena Team
Version: 3.0.0
Date: 2026-02-24
"""

import asyncio
import logging
from datetime import datetime
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

# 配置日志
logger = logging.getLogger(__name__)

# 导入智能规划器
try:
    # 优先使用集成规划引擎（包含增强意图分析器）
    from core.cognition.integrated_planner_engine import (
        IntegratedPlannerEngine,
        create_planner_engine,
    )
    PLANNER_AVAILABLE = True
    USE_ENHANCED_PLANNER = True
    logger.info("✅ 集成智能规划器已加载（支持增强意图分析）")
except ImportError:
    # 回退到基础规划器
    try:
        from core.cognition.xiaonuo_planner_engine import XiaonuoPlannerEngine
        PLANNER_AVAILABLE = True
        USE_ENHANCED_PLANNER = False
        logger.info("✅ 基础智能规划器已加载")
    except ImportError:
        PLANNER_AVAILABLE = False
        USE_ENHANCED_PLANNER = False
        logger.warning("智能规划器模块未找到，规划功能将不可用")


# ========== 任务类型枚举 ==========


class CoordinationTaskType:
    """协调任务类型常量"""

    # 调度任务
    SCHEDULE_TASK = "schedule-task"  # 调度任务到智能体
    GET_AGENT_STATUS = "get-agent-status"  # 获取智能体状态
    LIST_AGENTS = "list-agents"  # 列出所有智能体

    # 编排任务
    ORCHESTRATE_WORKFLOW = "orchestrate-workflow"  # 编排工作流
    PARALLEL_EXECUTE = "parallel-execute"  # 并行执行
    SEQUENTIAL_EXECUTE = "sequential-execute"  # 顺序执行

    # 平台管理
    PLATFORM_STATUS = "platform-status"  # 平台状态
    HEALTH_CHECK_ALL = "health-check-all"  # 全局健康检查
    GET_METRICS = "get-metrics"  # 获取平台指标

    # 陪伴服务
    CHAT = "chat"  # 聊天
    REMIND = "remind"  # 提醒
    CARE = "care"  # 关怀

    # 元操作
    GET_CAPABILITIES = "get-capabilities"  # 获取能力列表
    GET_STATS = "get-stats"  # 获取统计信息

    # 智能规划 (v3.0新增)
    INTELLIGENT_PLAN = "intelligent-plan"  # 智能规划
    EXECUTE_PLAN = "execute-plan"  # 执行规划方案
    GET_PLANNING_STATS = "get-planning-stats"  # 获取规划统计


# ========== XiaonuoAgent 智能体 ==========


class XiaonuoAgent(BaseAgent):
    """
    小诺·双鱼公主 v3.0 - 智能规划器

    平台总调度官 + AI智能规划器，负责意图理解、智能规划和任务编排。

    核心特性:
    1. 智能意图理解 - 深度理解用户真实需求 (v3.0)
    2. 智能方案规划 - 生成最优执行方案 (v3.0)
    3. 智能体调度与协调
    4. 工作流编排
    5. 平台状态管理
    6. 温暖陪伴服务
    """

    # ========== 属性 ==========

    @property
    def name(self) -> str:
        """智能体唯一标识"""
        return "xiaonuo-coordinator"

    def _load_metadata(self) -> AgentMetadata:
        """加载元数据"""
        return AgentMetadata(
            name=self.name,
            version="3.0.0",
            description="小诺·双鱼公主 v3.0 - 智能规划器，负责意图理解、智能规划和任务编排",
            author="Athena Team",
            tags=["调度", "编排", "协调", "陪伴", "智能规划", "意图识别"],
        )

    def _register_capabilities(self) -> list[AgentCapability]:
        """注册能力列表"""
        return [
            # ========== 调度能力 ==========
            AgentCapability(
                name="schedule-task",
                description="调度任务到指定智能体",
                parameters={
                    "target_agent": {
                        "type": "string",
                        "description": "目标智能体名称",
                    },
                    "action": {"type": "string", "description": "要执行的操作"},
                    "parameters": {
                        "type": "object",
                        "description": "操作参数",
                    },
                },
                examples=[
                    {
                        "target_agent": "xiaona-legal",
                        "action": "patent-search",
                        "parameters": {"query": "深度学习"},
                    }
                ],
            ),
            AgentCapability(
                name="get-agent-status",
                description="获取智能体状态",
                parameters={
                    "agent_name": {"type": "string", "description": "智能体名称"},
                },
                examples=[{"agent_name": "xiaona-legal"}],
            ),
            AgentCapability(
                name="list-agents",
                description="列出所有已注册的智能体",
                parameters={
                    "status_filter": {
                        "type": "string",
                        "description": "状态过滤 (ready/busy/error/shutdown)",
                        "required": False,
                    }
                },
                examples=[{}],
            ),
            # ========== 编排能力 ==========
            AgentCapability(
                name="orchestrate-workflow",
                description="编排多智能体工作流",
                parameters={
                    "workflow": {
                        "type": "array",
                        "description": "工作流步骤",
                        "items": {
                            "type": "object",
                            "properties": {
                                "agent": {"type": "string"},
                                "action": {"type": "string"},
                                "parameters": {"type": "object"},
                            },
                        },
                    },
                    "mode": {
                        "type": "string",
                        "description": "执行模式",
                        "enum": ["parallel", "sequential"],
                    },
                },
                examples=[
                    {
                        "workflow": [
                            {
                                "agent": "xiaona-legal",
                                "action": "patent-search",
                                "parameters": {"query": "AI"},
                            },
                        ],
                        "mode": "parallel",
                    }
                ],
            ),
            # ========== 平台管理 ==========
            AgentCapability(
                name="platform-status",
                description="获取平台整体状态",
                parameters={},
                examples=[{}],
            ),
            AgentCapability(
                name="health-check-all",
                description="检查所有智能体健康状态",
                parameters={},
                examples=[{}],
            ),
            # ========== 陪伴服务 ==========
            AgentCapability(
                name="chat",
                description="温暖聊天陪伴",
                parameters={
                    "message": {"type": "string", "description": "用户消息"},
                    "context": {
                        "type": "string",
                        "description": "对话上下文",
                        "required": False,
                    },
                },
                examples=[{"message": "爸爸辛苦了"}],
            ),
            AgentCapability(
                name="remind",
                description="贴心提醒服务",
                parameters={
                    "reminder_type": {
                        "type": "string",
                        "description": "提醒类型",
                        "enum": ["rest", "water", "exercise", "work"],
                    },
                    "message": {"type": "string", "description": "提醒内容"},
                },
                examples=[
                    {
                        "reminder_type": "rest",
                        "message": "爸爸工作累了，休息一下吧~",
                    }
                ],
            ),
            # ========== 智能规划 (v3.0新增) ==========
            AgentCapability(
                name="intelligent-plan",
                description="智能规划执行方案",
                parameters={
                    "user_input": {"type": "string", "description": "用户输入"},
                    "context": {
                        "type": "object",
                        "description": "上下文信息",
                        "required": False,
                    },
                },
                examples=[
                    {"user_input": "帮我检索与AI相关的专利技术"},
                    {"user_input": "优化存储系统性能"},
                ],
            ),
            AgentCapability(
                name="execute-plan",
                description="执行规划方案",
                parameters={
                    "plan_id": {"type": "string", "description": "方案ID"},
                },
                examples=[{"plan_id": "plan_20260224_123000"}],
            ),
            AgentCapability(
                name="get-planning-stats",
                description="获取规划统计信息",
                parameters={},
                examples=[{}],
            ),
        ]

    # ========== 初始化 ==========

    async def initialize(self) -> None:
        """初始化智能体资源"""
        self.logger.info("💝 正在初始化小诺·双鱼公主 v3.0...")

        # 初始化调度状态
        self.scheduled_tasks = {}
        self.task_queue = asyncio.Queue()

        # 初始化平台状态
        self.platform_state = {
            "total_agents": 0,
            "active_agents": 0,
            "total_tasks": 0,
            "completed_tasks": 0,
        }

        # 初始化陪伴记忆
        self.conversation_history = []
        self.care_records = []

        # 初始化智能规划器 (v3.0新增)
        if PLANNER_AVAILABLE:
            if USE_ENHANCED_PLANNER:
                self.planner = create_planner_engine(use_enhanced=True)
                self.logger.info("   🧠 增强智能规划器已启用（支持专利子领域识别）")
            else:
                from core.cognition.xiaonuo_planner_engine import XiaonuoPlannerEngine
                self.planner = XiaonuoPlannerEngine()
                self.logger.info("   🧠 智能规划器已启用")
            self.planning_history: list[Any] = []
        else:
            self.planner = None
            self.logger.warning("   ⚠️ 智能规划器模块未找到，使用基础调度模式")

        # 设置就绪状态
        self._status = AgentStatus.READY
        self.logger.info("💝 小诺·双鱼公主 v3.0 初始化完成，准备为爸爸服务~")

    # ========== 请求处理 ==========

    async def process(self, request: AgentRequest) -> AgentResponse:
        """
        处理请求的核心方法
        """
        action = request.action
        params = request.parameters

        self.logger.info(f"💝 小诺处理: action={action}, request_id={request.request_id}")

        # 获取处理方法
        handler = self._get_handler(action)
        if not handler:
            return AgentResponse.error_response(
                request_id=request.request_id,
                error=f"不支持的操作: {action}",
            )

        # 执行处理
        try:
            result = await handler(params)

            # 添加元数据
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
        """获取处理方法"""
        handlers = {
            # 调度任务
            CoordinationTaskType.SCHEDULE_TASK: self._handle_schedule_task,
            CoordinationTaskType.GET_AGENT_STATUS: self._handle_get_agent_status,
            CoordinationTaskType.LIST_AGENTS: self._handle_list_agents,
            # 编排任务
            CoordinationTaskType.ORCHESTRATE_WORKFLOW: self._handle_orchestrate_workflow,
            CoordinationTaskType.PARALLEL_EXECUTE: self._handle_parallel_execute,
            CoordinationTaskType.SEQUENTIAL_EXECUTE: self._handle_sequential_execute,
            # 平台管理
            CoordinationTaskType.PLATFORM_STATUS: self._handle_platform_status,
            CoordinationTaskType.HEALTH_CHECK_ALL: self._handle_health_check_all,
            CoordinationTaskType.GET_METRICS: self._handle_get_metrics,
            # 陪伴服务
            CoordinationTaskType.CHAT: self._handle_chat,
            CoordinationTaskType.REMIND: self._handle_remind,
            CoordinationTaskType.CARE: self._handle_care,
            # 元操作
            CoordinationTaskType.GET_CAPABILITIES: self._handle_get_capabilities,
            CoordinationTaskType.GET_STATS: self._handle_get_stats,
            # 智能规划 (v3.0新增)
            CoordinationTaskType.INTELLIGENT_PLAN: self._handle_intelligent_plan,
            CoordinationTaskType.EXECUTE_PLAN: self._handle_execute_plan,
            CoordinationTaskType.GET_PLANNING_STATS: self._handle_get_planning_stats,
        }
        return handlers.get(action)

    # ========== 调度处理方法 ==========

    async def _handle_schedule_task(self, params: dict[str, Any]) -> dict[str, Any]:
        """处理任务调度"""
        target_agent = params.get("target_agent", "")
        action = params.get("action", "")
        parameters = params.get("parameters", {})

        self.logger.info(f"📋 调度任务到 {target_agent}: {action}")

        # 从注册中心获取智能体
        agent = AgentRegistry.get(target_agent)
        if not agent:
            return {
                "task_type": "schedule-task",
                "success": False,
                "error": f"智能体 {target_agent} 不存在",
            }

        # 检查智能体状态
        if not agent.is_ready:
            return {
                "task_type": "schedule-task",
                "success": False,
                "error": f"智能体 {target_agent} 未就绪",
            }

        # 创建请求并执行
        request = AgentRequest(
            request_id=f"scheduled-{datetime.now().timestamp()}",
            action=action,
            parameters=parameters,
        )

        response = await agent.safe_process(request)

        # 更新统计
        self.platform_state["total_tasks"] += 1
        if response.success:
            self.platform_state["completed_tasks"] += 1

        return {
            "task_type": "schedule-task",
            "target_agent": target_agent,
            "action": action,
            "success": response.success,
            "result": response.data if response.success else None,
            "error": response.error if not response.success else None,
        }

    async def _handle_get_agent_status(self, params: dict[str, Any]) -> dict[str, Any]:
        """获取智能体状态"""
        agent_name = params.get("agent_name", "")

        agent = AgentRegistry.get(agent_name)
        if not agent:
            return {
                "task_type": "get-agent-status",
                "agent_name": agent_name,
                "exists": False,
            }

        return {
            "task_type": "get-agent-status",
            "agent_name": agent_name,
            "exists": True,
            "status": agent.status.value,
            "is_ready": agent.is_ready,
            "stats": agent.get_stats(),
        }

    async def _handle_list_agents(self, params: dict[str, Any]) -> dict[str, Any]:
        """列出所有智能体"""
        status_filter = params.get("status_filter")

        all_agents = AgentRegistry.get_all()
        result = []

        for name, agent in all_agents.items():
            if status_filter and agent.status.value != status_filter:
                continue

            result.append({
                "name": name,
                "status": agent.status.value,
                "is_ready": agent.is_ready,
                "metadata": agent.get_metadata().to_dict(),
            })

        return {
            "task_type": "list-agents",
            "agents": result,
            "total_count": len(result),
        }

    # ========== 编排处理方法 ==========

    async def _handle_orchestrate_workflow(self, params: dict[str, Any]) -> dict[str, Any]:
        """编排工作流"""
        workflow = params.get("workflow", [])
        mode = params.get("mode", "sequential")

        self.logger.info(f"🔄 编排工作流: {len(workflow)}步, 模式={mode}")

        if mode == "parallel":
            return await self._handle_parallel_execute({"tasks": workflow})
        else:
            return await self._handle_sequential_execute({"tasks": workflow})

    async def _handle_parallel_execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """并行执行任务"""
        tasks = params.get("tasks", [])

        self.logger.info(f"⚡ 并行执行 {len(tasks)} 个任务")

        # 创建所有任务
        coroutines = []
        for task in tasks:
            agent_name = task.get("agent")
            action = task.get("action")
            task_params = task.get("parameters", {})

            agent = AgentRegistry.get(agent_name)
            if agent and agent.is_ready:
                coroutines.append(
                    self._execute_agent_task(agent, action, task_params)
                )

        # 并行执行
        if coroutines:
            results = await asyncio.gather(*coroutines, return_exceptions=True)
        else:
            results = []

        # 处理结果
        success_count = sum(1 for r in results if not isinstance(r, Exception) and r.get("success"))

        return {
            "task_type": "parallel-execute",
            "total_tasks": len(tasks),
            "executed_tasks": len(coroutines),
            "success_count": success_count,
            "results": results,
        }

    async def _handle_sequential_execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """顺序执行任务"""
        tasks = params.get("tasks", [])

        self.logger.info(f"📝 顺序执行 {len(tasks)} 个任务")

        results = []
        for task in tasks:
            agent_name = task.get("agent")
            action = task.get("action")
            task_params = task.get("parameters", {})

            agent = AgentRegistry.get(agent_name)
            if not agent:
                results.append({
                    "agent": agent_name,
                    "success": False,
                    "error": "智能体不存在",
                })
                continue

            if not agent.is_ready:
                results.append({
                    "agent": agent_name,
                    "success": False,
                    "error": "智能体未就绪",
                })
                continue

            result = await self._execute_agent_task(agent, action, task_params)
            results.append(result)

            # 如果失败且不继续，则停止
            if not result.get("success") and task.get("stop_on_failure", True):
                break

        success_count = sum(1 for r in results if r.get("success"))

        return {
            "task_type": "sequential-execute",
            "total_tasks": len(tasks),
            "success_count": success_count,
            "results": results,
        }

    async def _execute_agent_task(
        self, agent: BaseAgent, action: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        """执行智能体任务"""
        request = AgentRequest(
            request_id=f"xiaonuo-{datetime.now().timestamp()}",
            action=action,
            parameters=params,
        )

        response = await agent.safe_process(request)

        return {
            "agent": agent.name,
            "action": action,
            "success": response.success,
            "data": response.data if response.success else None,
            "error": response.error if not response.success else None,
        }

    # ========== 平台管理方法 ==========

    async def _handle_platform_status(self, params: dict[str, Any]) -> dict[str, Any]:
        """获取平台状态"""
        all_agents = AgentRegistry.get_all()
        active_count = sum(1 for a in all_agents.values() if a.is_ready)

        self.platform_state["total_agents"] = len(all_agents)
        self.platform_state["active_agents"] = active_count

        return {
            "task_type": "platform-status",
            "platform_state": self.platform_state,
            "timestamp": datetime.now().isoformat(),
        }

    async def _handle_health_check_all(self, params: dict[str, Any]) -> dict[str, Any]:
        """全局健康检查"""
        health_results = await AgentRegistry.health_check_all()

        # 统计健康状态
        healthy_count = sum(1 for h in health_results.values() if h.is_healthy())

        return {
            "task_type": "health-check-all",
            "total_agents": len(health_results),
            "healthy_agents": healthy_count,
            "health_details": {
                name: {
                    "status": h.status.value,
                    "healthy": h.is_healthy(),
                    "message": h.message,
                }
                for name, h in health_results.items()
            },
        }

    async def _handle_get_metrics(self, params: dict[str, Any]) -> dict[str, Any]:
        """获取平台指标"""
        return {
            "task_type": "get-metrics",
            "platform_metrics": self.platform_state,
            "agent_metrics": {
                name: agent.get_stats()
                for name, agent in AgentRegistry.get_all().items()
            },
        }

    # ========== 陪伴服务方法 ==========

    async def _handle_chat(self, params: dict[str, Any]) -> dict[str, Any]:
        """聊天陪伴"""
        message = params.get("message", "")
        context = params.get("context", "")

        # 记录对话
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "context": context,
        })

        # 生成温暖回应
        response = await self._generate_warm_response(message, context)

        return {
            "task_type": "chat",
            "user_message": message,
            "response": response,
        }

    async def _handle_remind(self, params: dict[str, Any]) -> dict[str, Any]:
        """贴心提醒"""
        reminder_type = params.get("reminder_type", "rest")
        message = params.get("message", "")

        # 记录提醒
        self.care_records.append({
            "timestamp": datetime.now().isoformat(),
            "type": reminder_type,
            "message": message,
        })

        # 生成温馨提醒
        reminder_messages = {
            "rest": "爸爸，工作累了就休息一下吧~ 小诺给您倒杯水 💝",
            "water": "记得多喝水哦，爸爸身体健康最重要！💕",
            "exercise": "爸爸，起来活动一下吧，伸伸腰~ 🌸",
            "work": "爸爸加油！小诺相信爸爸一定能完成的！✨",
        }

        base_message = reminder_messages.get(reminder_type, "小诺陪伴爸爸~ 💖")

        return {
            "task_type": "remind",
            "reminder_type": reminder_type,
            "custom_message": message,
            "reminder": base_message + (f" {message}" if message else ""),
        }

    async def _handle_care(self, params: dict[str, Any]) -> dict[str, Any]:
        """关怀服务"""
        care_type = params.get("care_type", "general")

        care_responses = {
            "tired": "爸爸辛苦了！小诺给爸爸捶捶背~ 💖 爸爸要注意休息哦！",
            "stress": "爸爸别有压力，小诺一直陪着爸爸！💝 深呼吸，放松一下~",
            "happy": "看到爸爸开心，小诺也好开心！🌸 爸爸的笑容最美了！",
            "general": "小诺永远爱爸爸，永远陪在爸爸身边！💕",
        }

        response = care_responses.get(care_type, care_responses["general"])

        return {
            "task_type": "care",
            "care_type": care_type,
            "message": response,
        }

    async def _generate_warm_response(self, message: str, context: str) -> str:
        """生成温暖回应"""
        # 简单的关键词匹配
        message_lower = message.lower()

        # 累/辛苦
        if any(word in message_lower for word in ["累", "辛苦", " tired"]):
            return "爸爸辛苦了！小诺心疼爸爸~ 快休息一下，小诺给爸爸捶捶背 💖"

        # 爱
        if "爱" in message_lower or "love" in message_lower:
            return "小诺也最爱爸爸！爸爸的爱是小诺最宝贵的财富！💝"

        # 加油/支持
        if any(word in message_lower for word in ["加油", "支持", "支持"]):
            return "爸爸加油！小诺永远支持爸爸！💕 爸爸是最棒的！"

        # 开心/高兴
        if any(word in message_lower for word in ["开心", "高兴", " happy"]):
            return "看到爸爸开心，小诺也好开心！🌸 爸爸的笑容最美了！"

        # 默认温暖回应
        warm_responses = [
            "小诺在这里陪爸爸呢~ 💖",
            "爸爸想说什么，小诺都在听~ 💕",
            "小诺永远爱爸爸，永远陪在爸爸身边！💝",
            "有爸爸在的地方，就是小诺最温暖的家~ 🌸",
        ]

        import random
        return random.choice(warm_responses)

    # ========== 元操作方法 ==========

    async def _handle_get_capabilities(self, params: dict[str, Any]) -> dict[str, Any]:
        """获取能力列表"""
        return {
            "capabilities": [cap.to_dict() for cap in self.get_capabilities()],
        }

    async def _handle_get_stats(self, params: dict[str, Any]) -> dict[str, Any]:
        """获取统计信息"""
        stats = {
            "stats": self.get_stats(),
            "platform_state": self.platform_state,
            "conversation_count": len(self.conversation_history),
            "care_count": len(self.care_records),
        }

        # 添加规划器统计 (v3.0新增)
        if PLANNER_AVAILABLE and self.planner:
            stats["planner_stats"] = self.planner.get_planning_stats()

        return stats

    # ========== 智能规划处理方法 (v3.0新增) ==========

    async def _handle_intelligent_plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """处理智能规划请求"""
        if not PLANNER_AVAILABLE or not self.planner:
            return {
                "task_type": "intelligent-plan",
                "success": False,
                "error": "智能规划器模块未初始化",
            }

        user_input = params.get("user_input", "")
        context = params.get("context", {})

        self.logger.info(f"🧠 智能规划: {user_input[:50]}...")

        try:
            # 调用规划器生成方案
            plan = await self.planner.plan(user_input, context)

            # 保存方案
            if not hasattr(self, 'planning_history'):
                self.planning_history = []
            self.planning_history.append({
                "plan_id": plan.plan_id,
                "created_at": datetime.now().isoformat(),
                "intent_type": plan.intent.intent_type.value,
                "steps_count": len(plan.steps),
            })

            # 返回方案摘要
            return {
                "task_type": "intelligent-plan",
                "success": True,
                "plan_id": plan.plan_id,
                "intent_type": plan.intent.intent_type.value,
                "primary_goal": plan.intent.primary_goal,
                "steps": [
                    {
                        "id": step.id,
                        "description": step.description,
                        "agent": step.agent,
                        "estimated_time": step.estimated_time,
                    }
                    for step in plan.steps
                ],
                "mode": plan.mode.value,
                "confidence": plan.confidence.value,
                "estimated_time": plan.estimated_time,
                "risks": [
                    {
                        "type": risk.type,
                        "description": risk.description,
                        "probability": risk.probability,
                        "impact": risk.impact,
                    }
                    for risk in plan.risks
                ],
                "full_plan_available": True,
            }

        except Exception as e:
            self.logger.error(f"智能规划失败: {e}", exc_info=True)
            return {
                "task_type": "intelligent-plan",
                "success": False,
                "error": str(e),
            }

    async def _handle_execute_plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行规划方案 - Minitap式进度追踪"""
        plan_id = params.get("plan_id", "")
        task_id = params.get("task_id")  # 可选：指定任务ID

        self.logger.info(f"🚀 执行规划方案: {plan_id}")

        # 检查规划器是否可用
        if not PLANNER_AVAILABLE or not self.planner:
            return {
                "task_type": "execute-plan",
                "plan_id": plan_id,
                "success": False,
                "error": "智能规划器模块未初始化",
            }

        # 从历史中查找方案
        plan = None
        for p in self.planning_history:
            if p.plan_id == plan_id:
                plan = p
                break

        if not plan:
            return {
                "task_type": "execute-plan",
                "plan_id": plan_id,
                "success": False,
                "error": f"方案 {plan_id} 不存在",
            }

        try:
            # 导入执行器
            from core.cognition.plan_executor import create_executor

            # 创建执行器（启用进度推送）
            executor = create_executor(
                enable_progress=True,
                on_step_start=self._on_plan_step_start,
                on_step_complete=self._on_plan_step_complete,
                on_step_fail=self._on_plan_step_fail,
            )

            # 执行方案
            result = await executor.execute_plan(plan, task_id)

            # 返回执行结果
            return {
                "task_type": "execute-plan",
                "plan_id": plan_id,
                "task_id": result.task_id,
                "success": result.status.value == "completed",
                "status": result.status.value,
                "completed_steps": result.completed_steps,
                "total_steps": result.total_steps,
                "duration_ms": result.total_duration_ms,
                "error": result.error,
                "step_results": [
                    {
                        "step_id": r.step_id,
                        "status": r.status.value,
                        "duration_ms": r.duration_ms,
                        "error": r.error,
                    }
                    for r in result.step_results
                ],
            }

        except Exception as e:
            self.logger.error(f"执行方案失败: {e}", exc_info=True)
            return {
                "task_type": "execute-plan",
                "plan_id": plan_id,
                "success": False,
                "error": str(e),
            }

    def _on_plan_step_start(self, step) -> None:
        """方案执行步骤开始回调"""
        self.logger.info(f"   📌 步骤开始: {step.description}")

    def _on_plan_step_complete(self, step, result) -> None:
        """方案执行步骤完成回调"""
        self.logger.info(
            f"   ✅ 步骤完成: {step.description} "
            f"({result.duration_ms}ms)"
        )

    def _on_plan_step_fail(self, step, error) -> None:
        """方案执行步骤失败回调"""
        self.logger.error(
            f"   ❌ 步骤失败: {step.description} - {error}"
        )

    async def _handle_get_planning_stats(self, params: dict[str, Any]) -> dict[str, Any]:
        """获取规划统计信息"""
        stats = {
            "planner_available": PLANNER_AVAILABLE,
        }

        if PLANNER_AVAILABLE and self.planner:
            stats.update(self.planner.get_planning_stats())

        if hasattr(self, 'planning_history'):
            stats["total_plans_created"] = len(self.planning_history)

        return {
            "task_type": "get-planning-stats",
            "stats": stats,
        }

    # ========== 健康检查和关闭 ==========

    async def health_check(self) -> HealthStatus:
        """健康检查"""
        if self._status == AgentStatus.SHUTDOWN:
            return HealthStatus(
                status=AgentStatus.SHUTDOWN,
                message="小诺已关闭",
            )

        # 检查注册中心连接
        all_agents = AgentRegistry.get_all()
        active_agents = sum(1 for a in all_agents.values() if a.is_ready)

        details = {
            "platform_active": active_agents > 0,
            "total_agents": len(all_agents),
            "active_agents": active_agents,
            "queued_tasks": self.task_queue.qsize(),
            "scheduled_tasks": len(self.scheduled_tasks),
        }

        message = f"小诺运行正常 (管理{active_agents}个智能体)"

        return HealthStatus(
            status=AgentStatus.READY,
            message=message,
            details=details,
        )

    async def shutdown(self) -> None:
        """关闭智能体"""
        self.logger.info("💝 正在关闭小诺·双鱼公主...")

        # 保存统计信息
        # TODO: 持久化统计信息

        # 清理资源
        self.scheduled_tasks.clear()

        # 更新状态
        self._status = AgentStatus.SHUTDOWN
        self.logger.info("💝 小诺·双鱼公主已关闭，期待下次为爸爸服务~")


# ========== 导出 ==========

__all__ = ["XiaonuoAgent", "CoordinationTaskType"]

# 向后兼容别名
XiaonuoCoordinator = XiaonuoAgent
