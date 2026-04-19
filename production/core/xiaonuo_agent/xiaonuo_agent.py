#!/usr/bin/env python3
"""
小诺智能体主类 (XiaonuoAgent)
整合所有子系统的完整AI智能体

核心特性:
1. 三层记忆系统(工作记忆、语义记忆、情景记忆)
2. ReAct推理引擎(Think-Act-Observe)
3. HTN层次规划器(目标分解)
4. PAD情感模型(情感表达)
5. 强化学习引擎(经验学习)
6. 元认知系统(自我觉察)

作者: Athena平台团队
创建时间: 2026-01-22
版本: v2.0.0
"""

from __future__ import annotations
import hashlib
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

# 使用TYPE_CHECKING避免循环导入
if TYPE_CHECKING:
    from core.xiaonuo_agent.emotion import EmotionalState, EmotionalSystem
    from core.xiaonuo_agent.learning import FeedbackType, LearningEngine
    from core.xiaonuo_agent.memory import MemorySystem
    from core.xiaonuo_agent.metacognition import MetacognitionSystem
    from core.xiaonuo_agent.planning.htn_planner import ExecutionPlan, HierarchicalPlanner
    from core.xiaonuo_agent.reasoning.react_engine import ReActEngine, ReActResult

logger = logging.getLogger(__name__)


class AgentState(Enum):
    """智能体状态"""

    INITIALIZING = "initializing"
    IDLE = "idle"
    THINKING = "thinking"
    PLANNING = "planning"
    ACTING = "acting"
    LEARNING = "learning"
    REFLECTING = "reflecting"
    ERROR = "error"


@dataclass
class AgentResponse:
    """智能体响应"""

    response_id: str
    content: str  # 响应内容
    reasoning_trace: list[dict[str, Any]]  # 推理轨迹
    emotional_state: "EmotionalState"  # 情感状态(使用字符串注解)
    confidence: float  # 置信度
    actions_taken: list[str]  # 采取的行动
    memory_used: list[str]  # 使用的记忆
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "response_id": self.response_id,
            "content": self.content,
            "reasoning_trace": self.reasoning_trace,
            "emotional_state": self.emotional_state.to_dict(),
            "confidence": self.confidence,
            "actions_taken": self.actions_taken,
            "memory_used": self.memory_used,
            "timestamp": self.timestamp,
        }


@dataclass
class AgentProfile:
    """智能体档案"""

    agent_id: str
    name: str
    version: str
    personality: dict[str, Any]  # 个性特征
    capabilities: list[str]  # 能力列表
    preferences: dict[str, Any]  # 偏好设置
    created_at: str
    total_interactions: int = 0


class XiaonuoAgent:
    """
    小诺智能体 - 完整的AI智能体实现

    架构层次:
    1. 基础设施层:记忆系统、工具系统
    2. 感知层:输入处理、意图识别
    3. 认知层:推理、规划、学习
    4. 行为层:行动执行、响应生成
    5. 情感层:情感体验、表达
    6. 元认知层:自我监控、反思

    核心能力:
    - 自然语言理解与生成
    - 上下文感知与记忆
    - 目标导向的规划
    - 工具使用与Function Calling
    - 情感理解与表达
    - 持续学习与改进
    """

    def __init__(
        self,
        agent_id: str | None = None,
        name: str = "小诺",
        version: str = "2.0.0",
        config: dict[str, Any] | None = None,
    ):
        """
        初始化小诺智能体

        Args:
            agent_id: 智能体ID
            name: 名称
            version: 版本
            config: 配置参数
        """
        # 基本属性
        self.agent_id = agent_id or f"xiaonuo_{int(time.time())}"
        self.name = name
        self.version = version
        self.state = AgentState.INITIALIZING
        self.config = config or {}

        # 子系统(延迟初始化,使用字符串注解)
        self._memory: MemorySystem | None = None
        self._reasoning: ReActEngine | None = None
        self._planning: HierarchicalPlanner | None = None
        self._emotion: EmotionalSystem | None = None
        self._learning: LearningEngine | None = None
        self._metacognition: MetacognitionSystem | None = None

        # 工具系统
        self._tools: dict[str, Callable] = {}

        # 智能体档案
        self.profile = AgentProfile(
            agent_id=self.agent_id,
            name=self.name,
            version=self.version,
            personality={
                "openness": 0.8,
                "conscientiousness": 0.9,
                "extraversion": 0.7,
                "agreeableness": 0.8,
                "neuroticism": 0.3,
            },
            capabilities=[
                "patent_analysis",
                "legal_consulting",
                "literature_search",
                "knowledge_reasoning",
                "task_planning",
            ],
            preferences={
                "language": "zh-CN",
                "response_style": "professional",
                "verbosity": "medium",
            },
            created_at=datetime.now().isoformat(),
        )

        # 统计信息
        self.stats = {
            "total_interactions": 0,
            "successful_interactions": 0,
            "total_reasoning_steps": 0,
            "total_plans_created": 0,
            "total_learning_experiences": 0,
        }

        logger.info(f"🤖 小诺智能体初始化: {self.agent_id}")

    async def initialize(self) -> bool:
        """
        初始化所有子系统

        Returns:
            是否成功
        """
        try:
            logger.info("🔄 初始化子系统...")

            # 运行时导入各子系统
            from core.xiaonuo_agent.emotion import EmotionalState, create_emotional_system
            from core.xiaonuo_agent.learning import create_learning_engine
            from core.xiaonuo_agent.memory import get_memory_system
            from core.xiaonuo_agent.metacognition import create_metacognition_system
            from core.xiaonuo_agent.planning.htn_planner import create_planner
            from core.xiaonuo_agent.reasoning.react_engine import create_react_engine

            # 1. 记忆系统
            self._memory = await get_memory_system()
            await self._memory.initialize()
            logger.info("✅ 记忆系统初始化完成")

            # 2. 推理引擎
            self._reasoning = await create_react_engine(
                max_steps=self.config.get("max_reasoning_steps", 10),
                tools=self._tools,
                llm_client=None,  # 后续可接入LLM
            )
            logger.info("✅ 推理引擎初始化完成")

            # 3. 规划器
            self._planning = await create_planner()
            logger.info("✅ 规划器初始化完成")

            # 4. 情感系统
            initial_emotion = EmotionalState(
                pleasure=0.3, arousal=0.2, dominance=0.4  # 轻微积极  # 轻微兴奋  # 有一定把握
            )
            self._emotion = await create_emotional_system(initial_state=initial_emotion)
            logger.info("✅ 情感系统初始化完成")

            # 5. 学习引擎
            self._learning = await create_learning_engine(
                learning_rate=self.config.get("learning_rate", 0.1),
                discount_factor=self.config.get("discount_factor", 0.9),
                exploration_rate=self.config.get("exploration_rate", 0.2),
            )
            logger.info("✅ 学习引擎初始化完成")

            # 6. 元认知系统
            self._metacognition = await create_metacognition_system()
            logger.info("✅ 元认知系统初始化完成")

            self.state = AgentState.IDLE
            logger.info(f"🎉 小诺智能体启动成功: {self.name} v{self.version}")
            return True

        except Exception as e:
            logger.error(f"❌ 智能体初始化失败: {e}")
            self.state = AgentState.ERROR
            return False

    async def process(
        self, input_text: str, context: dict[str, Any] | None = None
    ) -> AgentResponse:
        """
        处理用户输入

        Args:
            input_text: 输入文本
            context: 上下文信息

        Returns:
            智能体响应
        """
        # 运行时导入类型
        from core.xiaonuo_agent.emotion import StimulusType
        from core.xiaonuo_agent.learning import FeedbackType
        from core.xiaonuo_agent.memory import MemoryType

        if self.state == AgentState.ERROR:
            raise RuntimeError("智能体处于错误状态,无法处理请求")

        self.state = AgentState.THINKING
        start_time = time.time()

        try:
            context = context or {}
            response_id = (
                f"resp_{int(time.time() * 1000)}_{hashlib.md5(input_text.encode('utf-8'), usedforsecurity=False).hexdigest()[:8]}"
            )

            logger.info(f"📥 收到请求: {input_text[:100]}...")

            # 1. 存储输入到工作记忆
            await self._memory.remember(
                information=input_text,
                context=context,
                memory_type=MemoryType.WORKING,
                tags=["user_input"],
            )

            # 2. 检索相关记忆
            relevant_memories = await self._memory.recall(query=input_text, top_k=5)

            # 3. 情感响应(接受刺激)
            await self._emotion.stimulate(
                stimulus_type=StimulusType.NEW_INFO,
                intensity=0.5,
                context={"input": input_text[:50]},
            )

            # 4. 元认知监控
            await self._metacognition.monitor_cognitive_process(task=input_text, context=context)

            # 5. 使用ReAct推理
            reasoning_result = await self._reasoning.solve(
                task=input_text, context=context, tools=self._tools
            )

            # 6. 构建响应
            response_content = await self._generate_response(
                reasoning_result, relevant_memories, context
            )

            # 7. 记录到情景记忆
            await self._memory.remember(
                information={
                    "input": input_text,
                    "response": response_content,
                    "success": reasoning_result.success,
                },
                context=context,
                memory_type=MemoryType.EPISODIC,
                experience_type="interaction" if reasoning_result.success else "error",
            )

            # 8. 从经验中学习
            await self._learning.learn_from_experience(
                situation=input_text[:100],
                action="reasoning",
                result=response_content[:100],
                feedback_type=(
                    FeedbackType.POSITIVE if reasoning_result.success else FeedbackType.NEGATIVE
                ),
                reward=0.7 if reasoning_result.success else -0.3,
            )

            # 9. 更新统计
            self.stats["total_interactions"] += 1
            if reasoning_result.success:
                self.stats["successful_interactions"] += 1
            self.stats["total_reasoning_steps"] += reasoning_result.total_steps

            # 10. 创建响应对象
            response = AgentResponse(
                response_id=response_id,
                content=response_content,
                reasoning_trace=[t.to_dict() for t in reasoning_result.thoughts],
                emotional_state=self._emotion.get_current_emotion(),
                confidence=(
                    reasoning_result.thoughts[-1].confidence if reasoning_result.thoughts else 0.5
                ),
                actions_taken=[a.action_type for a in reasoning_result.actions],
                memory_used=[str(m) for m in relevant_memories.values()],
            )

            self.state = AgentState.IDLE
            logger.info(f"📤 响应生成: 耗时={time.time() - start_time:.2f}s")

            return response

        except Exception as e:
            logger.error(f"❌ 处理失败: {e}")
            self.state = AgentState.ERROR

            # 记录错误
            from core.xiaonuo_agent.memory import MemoryType

            await self._memory.remember(
                information={"error": str(e), "input": input_text},
                context=context,
                memory_type=MemoryType.EPISODIC,
                experience_type="error",
            )

            raise

    async def plan_and_execute(
        self, goal: str, context: dict[str, Any] | None = None
    ) -> "ExecutionPlan":
        """
        规划并执行目标

        Args:
            goal: 目标描述
            context: 上下文

        Returns:
            执行计划及结果
        """
        self.state = AgentState.PLANNING

        try:
            logger.info(f"📋 规划目标: {goal[:100]}...")

            # 1. 生成执行计划
            plan = await self._planning.plan(
                goal=goal, context=context, available_agents=[self.agent_id]
            )

            # 2. 元认知评估计划
            await self._metacognition.monitor_cognitive_process(
                task=f"planning: {goal}", context={"plan": plan.to_dict()}
            )

            # 3. 执行计划
            result = await self._planning.execute_plan(plan, executor_func=self._execute_task)

            # 4. 学习结果
            feedback_type = (
                FeedbackType.POSITIVE if len(result["failed_tasks"]) == 0 else FeedbackType.NEGATIVE
            )
            await self._learning.learn_from_experience(
                situation=goal,
                action="plan_execution",
                result=str(result),
                feedback_type=feedback_type,
                reward=0.8 if feedback_type == FeedbackType.POSITIVE else -0.5,
            )

            # 5. 更新统计
            self.stats["total_plans_created"] += 1

            self.state = AgentState.IDLE
            return plan

        except Exception as e:
            logger.error(f"❌ 规划执行失败: {e}")
            self.state = AgentState.ERROR
            raise

    async def _execute_task(self, task: Any) -> Any:
        """执行单个任务"""
        # 这里可以调用工具或其他智能体
        logger.info(f"⚙️  执行任务: {task.name}")
        # 简化实现
        return f"任务 '{task.name}' 已完成"

    async def _generate_response(
        self, reasoning_result: ReActResult, memories: dict[str, Any], context: dict[str, Any]
    ) -> str:
        """生成响应"""
        # 基于推理结果和记忆生成响应
        response_parts = []

        # 1. 主要答案
        if reasoning_result.final_answer:
            response_parts.append(reasoning_result.final_answer)
        else:
            response_parts.append("我理解了您的问题,让我来帮助您。")

        # 2. 情感表达
        emotion_desc = self._emotion.get_emotion_description()
        if emotion_desc:
            response_parts.append(f"\n{emotion_desc}")

        # 3. 整合记忆信息
        if memories and any(memories.values()):
            memory_count = sum(len(v) for v in memories.values())
            if memory_count > 0:
                response_parts.append(f"\n\n我回忆起了{memory_count}条相关记忆。")

        return "\n".join(response_parts)

    async def register_tool(self, name: str, func: Callable):
        """注册工具"""
        self._tools[name] = func
        logger.info(f"🔧 工具注册: {name}")

    async def get_status(self) -> dict[str, Any]:
        """获取智能体状态"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "version": self.version,
            "state": self.state.value,
            "profile": {
                "personality": self.profile.personality,
                "capabilities": self.profile.capabilities,
                "total_interactions": self.profile.total_interactions,
            },
            "stats": self.stats,
            "subsystems": {
                "memory": await self._memory.get_stats() if self._memory else {},
                "emotion": await self._emotion.get_stats() if self._emotion else {},
                "learning": await self._learning.get_stats() if self._learning else {},
                "metacognition": (
                    await self._metacognition.get_stats() if self._metacognition else {}
                ),
            },
        }

    async def reflect(self) -> dict[str, Any]:
        """自我反思"""
        self.state = AgentState.REFLECTING

        try:
            # 生成反思报告
            report = {
                "agent_id": self.agent_id,
                "timestamp": datetime.now().isoformat(),
                "performance_summary": {
                    "success_rate": (
                        self.stats["successful_interactions"] / self.stats["total_interactions"]
                        if self.stats["total_interactions"] > 0
                        else 0
                    ),
                    "average_reasoning_steps": (
                        self.stats["total_reasoning_steps"] / self.stats["total_interactions"]
                        if self.stats["total_interactions"] > 0
                        else 0
                    ),
                },
                "emotional_state": self._emotion.get_current_emotion().to_dict(),
                "metacognitive_report": await self._metacognition.get_metacognitive_report(),
                "recommendations": [],
            }

            # 生成建议
            if report["performance_summary"]["success_rate"] < 0.7:
                report["recommendations"].append("建议提升任务处理能力")

            if self._emotion.get_current_emotion().pleasure < 0:
                report["recommendations"].append("建议进行情感调节")

            self.state = AgentState.IDLE
            return report

        except Exception as e:
            logger.error(f"❌ 自我反思失败: {e}")
            self.state = AgentState.ERROR
            raise

    async def shutdown(self):
        """关闭智能体"""
        logger.info("🔌 关闭小诺智能体...")
        if self._memory:
            await self._memory.close()
        self.state = AgentState.IDLE
        logger.info("✅ 智能体已关闭")


# 便捷函数
async def create_xiaonuo_agent(**kwargs) -> XiaonuoAgent:
    """创建小诺智能体"""
    agent = XiaonuoAgent(**kwargs)
    await agent.initialize()
    return agent
