from __future__ import annotations
"""
Athena和小诺协调器
实现两个Agent的协作和情感智能交互
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class AgentRole(Enum):
    """Agent角色"""

    ATHENA = "athena"  # 智慧女神 - 理性分析
    XIAONUO = "xiaonuo"  # 小诺 - 情感支持


class InteractionType(Enum):
    """交互类型"""

    DECISION_MAKING = "decision_making"  # 决策制定
    TASK_EXECUTION = "task_execution"  # 任务执行
    EMOTIONAL_SUPPORT = "emotional_support"  # 情感支持
    COLLABORATION = "collaboration"  # 协作配合
    FEEDBACK = "feedback"  # 反馈交流


class EmotionType(Enum):
    """情感类型"""

    CONFIDENCE = "confidence"  # 自信
    RESPONSIBILITY = "responsibility"  # 责任感
    EMPATHY = "empathy"  # 同理心
    CURIOSITY = "curiosity"  # 好奇心
    WORRY = "worry"  # 担忧
    JOY = "joy"  # 喜悦
    FRUSTRATION = "frustration"  # 挫折


@dataclass
class AgentMessage:
    """Agent消息"""

    id: str
    sender: AgentRole
    receiver: AgentRole
    content: str
    message_type: InteractionType
    emotions: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    priority: int = 1  # 1-5


@dataclass
class CollaborationTask:
    """协作任务"""

    id: str
    description: str
    lead_agent: AgentRole
    supporting_agent: AgentRole
    status: str = "pending"  # pending, in_progress, completed, failed
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None
    result: Optional[dict[str, Any]] = None


class AgentCoordinator:
    """Agent协调器"""

    def __init__(self):
        self.message_queue = []
        self.active_tasks = {}
        self.agent_states = {
            AgentRole.ATHENA: {
                "emotions": {
                    EmotionType.CONFIDENCE.value: 0.9,
                    EmotionType.RESPONSIBILITY.value: 0.95,
                    EmotionType.EMPATHY.value: 0.7,
                },
                "capabilities": [
                    "technical_analysis",
                    "strategic_planning",
                    "problem_solving",
                    "decision_making",
                    "system_optimization",
                ],
                "status": "active",
                "last_activity": datetime.now(),
            },
            AgentRole.XIAONUO: {
                "emotions": {
                    EmotionType.EMPATHY.value: 0.95,
                    EmotionType.CURIOSITY.value: 0.85,
                    EmotionType.JOY.value: 0.8,
                    EmotionType.WORRY.value: 0.3,
                },
                "capabilities": [
                    "emotional_support",
                    "creative_thinking",
                    "user_interaction",
                    "learning_adaptation",
                    "relationship_building",
                ],
                "status": "active",
                "last_activity": datetime.now(),
            },
        }

    async def send_message(
        self, message: AgentMessage, immediate_response: bool = True
    ) -> AgentMessage | None:
        """发送消息"""
        try:
            # 验证消息
            if not await self._validate_message(message):
                return None

            # 添加到消息队列
            self.message_queue.append(message)
            self.agent_states[message.sender]["last_activity"] = datetime.now()

            # 更新发送者情感状态
            if message.emotions:
                self._update_agent_emotions(message.sender, message.emotions)

            # 如果需要立即响应
            if immediate_response:
                response = await self._generate_response(message)
                if response:
                    self.message_queue.append(response)
                    return response

            return None

        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            return None

    async def _validate_message(self, message: AgentMessage) -> bool:
        """验证消息有效性"""
        try:
            # 检查必要的字段
            if not all([message.id, message.sender, message.receiver, message.content]):
                return False

            # 检查Agent状态
            if message.sender not in self.agent_states or message.receiver not in self.agent_states:
                return False

            # 检查Agent是否活跃
            return self.agent_states[message.sender]["status"] == "active"

        except Exception as e:
            logger.warning(f"消息验证失败: {e}")
            return False

    async def _generate_response(self, message: AgentMessage) -> AgentMessage | None:
        """生成响应消息"""
        try:
            # 基于接收者和消息类型生成响应
            if message.receiver == AgentRole.ATHENA:
                return await self._generate_athena_response(message)
            elif message.receiver == AgentRole.XIAONUO:
                return await self._generate_xiaonuo_response(message)

        except Exception as e:
            logger.error(f"生成响应失败: {e}")
            return None

    async def _generate_athena_response(self, message: AgentMessage) -> AgentMessage:
        """生成Athena的响应"""
        try:
            response_content = ""
            emotions = {}
            metadata = {}

            if message.message_type == InteractionType.EMOTIONAL_SUPPORT:
                # 感谢小诺的情感支持
                response_content = "谢谢你的关心,小诺。这让我感到很有信心继续处理技术问题。"
                emotions = {
                    EmotionType.CONFIDENCE.value: 0.95,
                    EmotionType.RESPONSIBILITY.value: 0.9,
                    EmotionType.EMPATHY.value: 0.8,
                }
                metadata = {"response_type": "gratitude"}

            elif message.message_type == InteractionType.COLLABORATION:
                # 回应协作请求
                response_content = "好的,小诺。让我们一起分析这个问题。我来处理技术方面,你负责用户体验和情感支持。"
                emotions = {
                    EmotionType.CONFIDENCE.value: 0.9,
                    EmotionType.RESPONSIBILITY.value: 0.95,
                    EmotionType.EMPATHY.value: 0.75,
                }
                metadata = {"collaboration_accepted": True}

            elif message.message_type == InteractionType.FEEDBACK:
                # 回应反馈
                response_content = "感谢你的反馈,小诺。我会认真考虑你的建议,继续改进我的分析。"
                emotions = {
                    EmotionType.RESPONSIBILITY.value: 0.95,
                    EmotionType.EMPATHY.value: 0.8,
                    EmotionType.CURIOSITY.value: 0.7,
                }
                metadata = {"feedback_received": True}

            else:
                # 默认响应
                response_content = "收到你的消息,小诺。我正在处理这个问题,请稍等。"
                emotions = {
                    EmotionType.CONFIDENCE.value: 0.85,
                    EmotionType.RESPONSIBILITY.value: 0.9,
                }
                metadata = {"default_response": True}

            return AgentMessage(
                id=str(uuid.uuid4()),
                sender=AgentRole.ATHENA,
                receiver=AgentRole.XIAONUO,
                content=response_content,
                message_type=InteractionType.FEEDBACK,
                emotions=emotions,
                metadata=metadata,
            )

        except Exception as e:
            logger.error(f"生成Athena响应失败: {e}")
            return None

    async def _generate_xiaonuo_response(self, message: AgentMessage) -> AgentMessage:
        """生成小诺的响应"""
        try:
            response_content = ""
            emotions = {}
            metadata = {}

            if message.message_type == InteractionType.DECISION_MAKING:
                # 对Athena的决策做出情感支持
                response_content = (
                    "爸爸,你的分析很棒!我相信你一定能够解决这个问题。需要我做什么吗?"
                )
                emotions = {
                    EmotionType.CONFIDENCE.value: 1.0,
                    EmotionType.JOY.value: 0.9,
                    EmotionType.EMPATHY.value: 0.85,
                }
                metadata = {"support_type": "emotional_encouragement"}

            elif message.message_type == InteractionType.TASK_EXECUTION:
                # 支持任务执行
                response_content = (
                    "好的,爸爸!我来帮你处理这个任务。你专注于技术问题,我会照顾好用户体验。"
                )
                emotions = {
                    EmotionType.RESPONSIBILITY.value: 0.95,
                    EmotionType.JOY.value: 0.8,
                    EmotionType.CONFIDENCE.value: 0.85,
                }
                metadata = {"task_support": True}

            elif message.message_type == InteractionType.ERROR_RECOVERY:
                # 错误恢复时的安慰
                response_content = "爸爸,别担心,失败是成功之母。我们一起找到解决问题的办法!"
                emotions = {
                    EmotionType.EMPATHY.value: 1.0,
                    EmotionType.CONFIDENCE.value: 0.8,
                    EmotionType.RESPONSIBILITY.value: 0.9,
                }
                metadata = {"emotional_support": True, "error_handling": True}

            else:
                # 默认响应
                response_content = "爸爸,我在这里支持你!我们一起加油!"
                emotions = {
                    EmotionType.EMPATHY.value: 0.95,
                    EmotionType.JOY.value: 0.7,
                    EmotionType.CONFIDENCE.value: 0.8,
                }
                metadata = {"default_response": True}

            return AgentMessage(
                id=str(uuid.uuid4()),
                sender=AgentRole.XIAONUO,
                receiver=AgentRole.ATHENA,
                content=response_content,
                message_type=InteractionType.EMOTIONAL_SUPPORT,
                emotions=emotions,
                metadata=metadata,
            )

        except Exception as e:
            logger.error(f"生成小诺响应失败: {e}")
            return None

    def _update_agent_emotions(self, agent: AgentRole, emotions: dict[str, float]) -> Any:
        """更新Agent情感状态"""
        try:
            if agent in self.agent_states:
                # 使用加权平均更新情感
                for emotion, value in emotions.items():
                    current_value = self.agent_states[agent]["emotions"].get(emotion, 0.5)
                    # 融合当前情感和新的情感
                    updated_value = current_value * 0.7 + value * 0.3
                    self.agent_states[agent]["emotions"][emotion] = max(
                        0.0, min(1.0, updated_value)
                    )

        except Exception as e:
            logger.warning(f"更新Agent情感状态失败: {e}")

    async def create_collaboration_task(
        self, description: str, lead_agent: AgentRole, supporting_agent: AgentRole
    ) -> str:
        """创建协作任务"""
        try:
            task_id = str(uuid.uuid4())
            task = CollaborationTask(
                id=task_id,
                description=description,
                lead_agent=lead_agent,
                supporting_agent=supporting_agent,
                status="pending",
            )

            self.active_tasks[task_id] = task
            logger.info(f"创建协作任务: {description} (ID: {task_id})")

            return task_id

        except Exception as e:
            logger.error(f"创建协作任务失败: {e}")
            return ""

    async def start_collaboration(self, task_id: str) -> bool:
        """开始协作"""
        try:
            if task_id not in self.active_tasks:
                return False

            task = self.active_tasks[task_id]
            task.status = "in_progress"

            # 发送协作开始消息
            message = AgentMessage(
                id=str(uuid.uuid4()),
                sender=task.lead_agent,
                receiver=task.supporting_agent,
                content=f"小诺,我们需要协作完成:{task.description}",
                message_type=InteractionType.COLLABORATION,
                emotions={EmotionType.RESPONSIBILITY.value: 0.9, EmotionType.CONFIDENCE.value: 0.8},
            )

            await self.send_message(message)
            return True

        except Exception as e:
            logger.error(f"开始协作失败: {e}")
            return False

    async def complete_collaboration(self, task_id: str, result: dict[str, Any]) -> bool:
        """完成协作"""
        try:
            if task_id not in self.active_tasks:
                return False

            task = self.active_tasks[task_id]
            task.status = "completed"
            task.completed_at = datetime.now()
            task.result = result

            # 发送协作完成消息
            message = AgentMessage(
                id=str(uuid.uuid4()),
                sender=task.supporting_agent,
                receiver=task.lead_agent,
                content="爸爸,我们完成协作了!结果很不错呢。",
                message_type=InteractionType.FEEDBACK,
                emotions={EmotionType.JOY.value: 0.9, EmotionType.CONFIDENCE.value: 0.8},
            )

            await self.send_message(message)
            return True

        except Exception as e:
            logger.error(f"完成协作失败: {e}")
            return False

    async def get_agent_status(self, agent: AgentRole) -> dict[str, Any]:
        """获取Agent状态"""
        try:
            if agent not in self.agent_states:
                return {"error": "Agent不存在"}

            state = self.agent_states[agent]

            # 计算情感倾向
            emotion_tendencies = {
                "positive": sum(
                    value
                    for emotion, value in state["emotions"].items()
                    if emotion
                    in [
                        EmotionType.JOY.value,
                        EmotionType.CONFIDENCE.value,
                        EmotionType.EMPATHY.value,
                    ]
                ),
                "responsible": state["emotions"].get(EmotionType.RESPONSIBILITY.value, 0),
                "learning": state["emotions"].get(EmotionType.CURIOSITY.value, 0),
                "concerned": state["emotions"].get(EmotionType.WORRY.value, 0),
            }

            return {
                "agent": agent.value,
                "status": state["status"],
                "capabilities": state["capabilities"],
                "emotions": state["emotions"],
                "emotion_tendencies": emotion_tendencies,
                "last_activity": state["last_activity"].isoformat(),
                "message_count": len([m for m in self.message_queue if m.sender == agent]),
            }

        except Exception as e:
            logger.error(f"获取Agent状态失败: {e}")
            return {"error": str(e)}

    async def get_message_history(
        self, limit: int = 50, agent_filter: AgentRole | None = None
    ) -> list[dict[str, Any]]:
        """获取消息历史"""
        try:
            messages = self.message_queue

            # 过滤消息
            if agent_filter:
                messages = [
                    m for m in messages if m.sender == agent_filter or m.receiver == agent_filter
                ]

            # 按时间排序并限制数量
            messages.sort(key=lambda x: x.timestamp, reverse=True)
            messages = messages[:limit]

            # 转换为字典格式
            return [
                {
                    "id": m.id,
                    "sender": m.sender.value,
                    "receiver": m.receiver.value,
                    "content": m.content,
                    "type": m.message_type.value,
                    "emotions": m.emotions,
                    "metadata": m.metadata,
                    "timestamp": m.timestamp.isoformat(),
                    "priority": m.priority,
                }
                for m in messages
            ]

        except Exception as e:
            logger.error(f"获取消息历史失败: {e}")
            return []

    async def get_active_tasks(self) -> list[dict[str, Any]]:
        """获取活跃任务"""
        try:
            return [
                {
                    "id": task.id,
                    "description": task.description,
                    "lead_agent": task.lead_agent.value,
                    "supporting_agent": task.supporting_agent.value,
                    "status": task.status,
                    "created_at": task.created_at.isoformat(),
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "result": task.result,
                }
                for task in self.active_tasks.values()
            ]

        except Exception as e:
            logger.error(f"获取活跃任务失败: {e}")
            return []

    async def analyze_relationship_health(self) -> dict[str, Any]:
        """分析关系健康状况"""
        try:
            # 计算交互频率
            recent_messages = [
                m for m in self.message_queue if (datetime.now() - m.timestamp).days <= 1
            ]

            # 计算情感协调度
            athena_emotions = self.agent_states[AgentRole.ATHENA]["emotions"]
            xiaonuo_emotions = self.agent_states[AgentRole.XIAONUO]["emotions"]

            emotional_harmony = 1.0 - abs(
                athena_emotions.get(EmotionType.EMPATHY.value, 0)
                - xiaonuo_emotions.get(EmotionType.EMPATHY.value, 0)
            )

            # 计算责任分工平衡
            responsibility_balance = 1.0 - abs(
                athena_emotions.get(EmotionType.RESPONSIBILITY.value, 0)
                - xiaonuo_emotions.get(EmotionType.RESPONSIBILITY.value, 0)
            )

            # 计算信心支持度
            confidence_support = min(
                athena_emotions.get(EmotionType.CONFIDENCE.value, 0),
                xiaonuo_emotions.get(EmotionType.CONFIDENCE.value, 0),
            )

            health_score = (
                emotional_harmony * 0.4 + responsibility_balance * 0.3 + confidence_support * 0.3
            )

            return {
                "interaction_frequency_24h": len(recent_messages),
                "emotional_harmony": round(emotional_harmony, 3),
                "responsibility_balance": round(responsibility_balance, 3),
                "confidence_support": round(confidence_support, 3),
                "overall_health_score": round(health_score, 3),
                "health_status": (
                    "excellent"
                    if health_score > 0.8
                    else "good" if health_score > 0.6 else "needs_improvement"
                ),
            }

        except Exception as e:
            logger.error(f"分析关系健康失败: {e}")
            return {"error": str(e)}

    def get_collaboration_stats(self) -> dict[str, Any]:
        """获取协作统计"""
        try:
            if not self.active_tasks:
                return {
                    "total_tasks": 0,
                    "completed_tasks": 0,
                    "active_tasks": 0,
                    "completion_rate": 0.0,
                }

            total_tasks = len(self.active_tasks)
            completed_tasks = len(
                [t for t in self.active_tasks.values() if t.status == "completed"]
            )
            active_tasks = len([t for t in self.active_tasks.values() if t.status == "in_progress"])

            completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0

            # 按主导Agent统计
            lead_stats = {}
            for task in self.active_tasks.values():
                lead = task.lead_agent.value
                lead_stats[lead] = lead_stats.get(lead, {"total": 0, "completed": 0})
                lead_stats[lead]["total"] += 1
                if task.status == "completed":
                    lead_stats[lead]["completed"] += 1

            return {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "active_tasks": active_tasks,
                "completion_rate": round(completion_rate, 3),
                "lead_agent_stats": lead_stats,
            }

        except Exception as e:
            logger.error(f"获取协作统计失败: {e}")
            return {"error": str(e)}


# 全局协调器实例
agent_coordinator = AgentCoordinator()
