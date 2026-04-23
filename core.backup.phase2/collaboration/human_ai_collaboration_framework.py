#!/usr/bin/env python3
from __future__ import annotations
"""
人机协作框架
Human-AI Collaboration Framework

为小娜设计的人机协作和人类在环决策系统
实现智能体与人类专家的高效协作

作者: 徐健 (xujian519@gmail.com)
创建时间: 2025-12-17
版本: v1.0.0
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class CollaborationMode(Enum):
    """协作模式"""

    AUTOMATIC = "automatic"  # 自动模式
    SEMI_AUTOMATIC = "semi_automatic"  # 半自动模式
    HUMAN_IN_LOOP = "human_in_loop"  # 人类在环
    HUMAN_SUPERVISED = "human_supervised"  # 人类监督
    COLLABORATIVE = "collaborative"  # 协作模式


class DecisionLevel(Enum):
    """决策级别"""

    LOW = 1  # 低级别 - AI可自动决策
    MEDIUM = 2  # 中级别 - 需要人类确认
    HIGH = 3  # 高级别 - 需要人类决策
    CRITICAL = 4  # 关键级别 - 必须专家决策


class TaskType(Enum):
    """任务类型"""

    PATENT_ANALYSIS = "patent_analysis"  # 专利分析
    LEGAL_RESEARCH = "legal_research"  # 法律研究
    DOCUMENT_DRAFTING = "document_drafting"  # 文件起草
    STRATEGY_PLANNING = "strategy_planning"  # 策略规划
    RISK_ASSESSMENT = "risk_assessment"  # 风险评估
    CLIENT_ADVICE = "client_advice"  # 客户建议


@dataclass
class HumanExpert:
    """人类专家信息"""

    expert_id: str
    name: str
    title: str
    expertise: list[str]
    availability: dict[str, Any]
    contact_info: dict[str, str]
    preference: dict[str, Any] = field(default_factory=dict)


@dataclass
class CollaborationTask:
    """协作任务"""

    task_id: str
    task_type: TaskType
    title: str
    description: str
    context: dict[str, Any]
    ai_output: str | None = None
    human_review: str | None = None
    final_decision: str | None = None
    decision_level: DecisionLevel = DecisionLevel.MEDIUM
    collaboration_mode: CollaborationMode = CollaborationMode.SEMI_AUTOMATIC
    assigned_expert: HumanExpert | None = None
    status: str = "pending"  # pending, in_progress, completed, rejected
    priority: int = 3  # 1-5, 5为最高
    created_at: datetime = field(default_factory=datetime.now)
    deadline: datetime | None = None


@dataclass
class CollaborationSession:
    """协作会话"""

    session_id: str
    task: CollaborationTask
    messages: list[dict[str, Any]] = field(default_factory=list)
    ai_confidence: float = 0.0
    human_confidence: float = 0.0
    consensus_reached: bool = False
    final_output: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None


class HumanInTheLoopEngine:
    """人类在环决策引擎"""

    def __init__(self, llm_client=None, notification_service=None):
        self.llm_client = llm_client
        self.notification_service = notification_service
        self.experts_database: dict[str, HumanExpert] = {}
        self.active_sessions: dict[str, CollaborationSession] = {}
        self.completed_tasks: list[CollaborationTask] = []

        # 决策级别阈值配置
        self.decision_thresholds = {
            DecisionLevel.LOW: 0.95,  # AI置信度>95%可自动决策
            DecisionLevel.MEDIUM: 0.80,  # AI置信度>80%需人类确认
            DecisionLevel.HIGH: 0.60,  # AI置信度>60%需人类决策
            DecisionLevel.CRITICAL: 0.0,  # 关键决策必须由人类主导
        }

        # 任务类型对应的默认决策级别
        self.task_decision_levels = {
            TaskType.PATENT_ANALYSIS: DecisionLevel.MEDIUM,
            TaskType.LEGAL_RESEARCH: DecisionLevel.HIGH,
            TaskType.DOCUMENT_DRAFTING: DecisionLevel.MEDIUM,
            TaskType.STRATEGY_PLANNING: DecisionLevel.HIGH,
            TaskType.RISK_ASSESSMENT: DecisionLevel.CRITICAL,
            TaskType.CLIENT_ADVICE: DecisionLevel.CRITICAL,
        }

    def register_expert(self, expert: HumanExpert) -> bool:
        """注册专家"""
        try:
            self.experts_database[expert.expert_id] = expert
            logger.info(f"专家注册成功: {expert.name} ({expert.title})")
            return True
        except Exception as e:
            logger.error(f"专家注册失败: {e}")
            return False

    def determine_decision_level(
        self, task_type: TaskType, ai_confidence: float, context: dict[str, Any]
    ) -> DecisionLevel:
        """确定决策级别"""

        # 基础决策级别
        self.task_decision_levels.get(task_type, DecisionLevel.MEDIUM)

        # 根据AI置信度调整
        if ai_confidence >= self.decision_thresholds[DecisionLevel.LOW]:
            return DecisionLevel.LOW
        elif ai_confidence >= self.decision_thresholds[DecisionLevel.MEDIUM]:
            return DecisionLevel.MEDIUM
        elif ai_confidence >= self.decision_thresholds[DecisionLevel.HIGH]:
            return DecisionLevel.HIGH
        else:
            return DecisionLevel.CRITICAL

    def select_best_expert(
        self, task_type: TaskType, context: dict[str, Any], availability_required: bool = True
    ) -> HumanExpert | None:
        """选择最适合的专家"""

        # 根据任务类型筛选专家
        relevant_experts = []
        task_type_str = task_type.value

        for expert in self.experts_database.values():
            # 检查专业匹配度
            if any(
                task_type_str in expertise.lower()
                or any(keyword in expertise.lower() for keyword in task_type_str.split("_"))
                for expertise in expert.expertise
            ):

                # 检查可用性
                if availability_required:
                    current_time = datetime.now()
                    expert_available = True

                    # 检查工作时间
                    if "working_hours" in expert.availability:
                        working_hours = expert.availability["working_hours"]
                        current_hour = current_time.hour
                        if not (working_hours["start"] <= current_hour <= working_hours["end"]):
                            expert_available = False

                    # 检查日期可用性
                    if "available_days" in expert.availability:
                        available_days = expert.availability["available_days"]
                        current_weekday = current_time.weekday()
                        if current_weekday not in available_days:
                            expert_available = False

                    if expert_available:
                        relevant_experts.append(expert)
                else:
                    relevant_experts.append(expert)

        # 选择最佳专家(简单实现:选择第一个匹配的专家)
        if relevant_experts:
            return relevant_experts[0]

        return None

    async def create_collaboration_task(
        self,
        task_type: TaskType,
        title: str,
        description: str,
        context: dict[str, Any],        ai_output: str,
        ai_confidence: float,
        priority: int = 3,
        deadline: datetime | None = None,
    ) -> CollaborationTask:
        """创建协作任务"""

        task_id = f"task_{int(datetime.now().timestamp())}"
        decision_level = self.determine_decision_level(task_type, ai_confidence, context)

        # 确定协作模式
        if decision_level == DecisionLevel.LOW:
            collaboration_mode = CollaborationMode.AUTOMATIC
        elif decision_level == DecisionLevel.MEDIUM:
            collaboration_mode = CollaborationMode.SEMI_AUTOMATIC
        elif decision_level == DecisionLevel.HIGH:
            collaboration_mode = CollaborationMode.HUMAN_IN_LOOP
        else:
            collaboration_mode = CollaborationMode.HUMAN_SUPERVISED

        task = CollaborationTask(
            task_id=task_id,
            task_type=task_type,
            title=title,
            description=description,
            context=context,
            ai_output=ai_output,
            decision_level=decision_level,
            collaboration_mode=collaboration_mode,
            priority=priority,
            deadline=deadline,
        )

        # 如果需要人类参与,选择专家
        if decision_level.value >= DecisionLevel.MEDIUM.value:
            task.assigned_expert = self.select_best_expert(task_type, context)

            # 发送通知
            if task.assigned_expert and self.notification_service:
                await self._notify_expert(task)

        logger.info(f"创建协作任务: {task.title} (级别: {decision_level.value})")
        return task

    async def start_collaboration_session(self, task: CollaborationTask) -> CollaborationSession:
        """启动协作会话"""

        session_id = f"session_{int(datetime.now().timestamp())}"

        session = CollaborationSession(
            session_id=session_id,
            task=task,
            ai_confidence=self._calculate_ai_confidence(task.ai_output, task.context),
        )

        self.active_sessions[session_id] = session

        # 添加AI初始消息
        session.messages.append(
            {
                "sender": "ai",
                "content": task.ai_output,
                "confidence": session.ai_confidence,
                "timestamp": datetime.now().isoformat(),
            }
        )

        logger.info(f"启动协作会话: {session_id}")
        return session

    async def process_human_input(
        self, session_id: str, human_input: str, confidence: float | None = None
    ) -> dict[str, Any]:
        """处理人类输入"""

        if session_id not in self.active_sessions:
            raise ValueError(f"协作会话不存在: {session_id}")

        session = self.active_sessions[session_id]

        # 记录人类输入
        session.messages.append(
            {
                "sender": "human",
                "content": human_input,
                "confidence": confidence or 1.0,
                "timestamp": datetime.now().isoformat(),
            }
        )

        session.human_confidence = confidence or 1.0

        # 分析共识情况
        consensus = await self._analyze_consensus(session)
        session.consensus_reached = consensus["reached"]

        if consensus["reached"]:
            session.final_output = consensus["final_output"]
            session.completed_at = datetime.now()
            session.task.status = "completed"
            session.task.final_decision = session.final_output

            # 移动到已完成任务
            self.completed_tasks.append(session.task)
            del self.active_sessions[session_id]

        return {
            "session_id": session_id,
            "consensus_reached": session.consensus_reached,
            "final_output": session.final_output,
            "suggestions": consensus.get("suggestions", []),
        }

    async def _analyze_consensus(self, session: CollaborationSession) -> dict[str, Any]:
        """分析人机共识"""

        ai_messages = [msg for msg in session.messages if msg["sender"] == "ai"]
        human_messages = [msg for msg in session.messages if msg["sender"] == "human"]

        if not human_messages:
            return {"reached": False, "reason": "no_human_input"}

        # 简单的共识判断逻辑
        last_ai_msg = ai_messages[-1] if ai_messages else ""
        last_human_msg = human_messages[-1] if human_messages else ""

        # 如果人类明确同意
        if "同意" in last_human_msg or "确认" in last_human_msg or "通过" in last_human_msg:
            return {
                "reached": True,
                "final_output": last_ai_msg,
                "confidence": min(session.ai_confidence, session.human_confidence),
            }

        # 如果人类提供修改意见
        if "修改" in last_human_msg or "调整" in last_human_msg or "优化" in last_human_msg:
            # 需要AI根据人类意见修改
            refined_output = await self._refine_ai_output(
                session.task.ai_output, last_human_msg, session.task.context
            )

            # 添加AI修改后的消息
            session.messages.append(
                {
                    "sender": "ai",
                    "content": refined_output,
                    "confidence": 0.9,  # 修改后的置信度
                    "timestamp": datetime.now().isoformat(),
                    "refined": True,
                }
            )

            return {"reached": False, "reason": "ai_refined"}

        # 如果人类明确拒绝
        if "拒绝" in last_human_msg or "不同意" in last_human_msg or "重做" in last_human_msg:
            return {
                "reached": False,
                "reason": "human_rejected",
                "suggestions": ["需要重新分析", "考虑其他方案"],
            }

        # 默认情况:需要进一步讨论
        return {"reached": False, "reason": "need_discussion"}

    async def _refine_ai_output(
        self, original_output: str, human_feedback: str, context: dict[str, Any]
    ) -> str:
        """根据人类反馈优化AI输出"""

        # 简单实现:在原输出后添加修改说明
        refined = f"{original_output}\n\n[根据专家反馈优化]\n{human_feedback}"

        # 在实际应用中,这里应该调用LLM重新生成
        if self.llm_client:
            try:
                pass

                # response = await self.llm_client.generate(prompt)
                # refined = response.text
            except Exception as e:
                logger.error(f"AI优化失败: {e}")

        return refined

    def _calculate_ai_confidence(self, output: str, context: dict[str, Any]) -> float:
        """计算AI置信度"""

        # 简单实现:基于输出长度和内容完整性
        base_confidence = 0.8

        # 输出长度加分
        length_score = min(len(output) / 1000, 1.0) * 0.1

        # 内容完整性加分
        completeness_keywords = ["分析", "结论", "建议", "风险"]
        completeness_score = (
            sum(1 for keyword in completeness_keywords if keyword in output)
            / len(completeness_keywords)
            * 0.1
        )

        confidence = base_confidence + length_score + completeness_score
        return min(confidence, 1.0)

    async def _notify_expert(self, task: CollaborationTask):
        """通知专家"""

        if not task.assigned_expert or not self.notification_service:
            return

        notification = {
            "expert_id": task.assigned_expert.expert_id,
            "expert_name": task.assigned_expert.name,
            "task_id": task.task_id,
            "task_title": task.title,
            "task_description": task.description,
            "decision_level": task.decision_level.value,
            "priority": task.priority,
            "deadline": task.deadline.isoformat() if task.deadline else None,
            "notification_time": datetime.now().isoformat(),
        }

        try:
            await self.notification_service.send_notification(notification)
            logger.info(f"专家通知已发送: {task.assigned_expert.name}")
        except Exception as e:
            logger.error(f"专家通知发送失败: {e}")

    def get_collaboration_statistics(self) -> dict[str, Any]:
        """获取协作统计信息"""

        total_sessions = len(self.active_sessions) + len(self.completed_tasks)
        completed_count = len(self.completed_tasks)

        if completed_count > 0:
            # 平均协作时间
            collaboration_times = []
            for task in self.completed_tasks:
                # 这里应该记录实际的协作时间,简化计算
                collaboration_times.append(30)  # 假设平均30分钟

            avg_collaboration_time = sum(collaboration_times) / len(collaboration_times)

            # 专家参与度
            expert_participation = {}
            for task in self.completed_tasks:
                if task.assigned_expert:
                    expert_id = task.assigned_expert.expert_id
                    expert_participation[expert_id] = expert_participation.get(expert_id, 0) + 1
        else:
            avg_collaboration_time = 0
            expert_participation = {}

        return {
            "total_sessions": total_sessions,
            "active_sessions": len(self.active_sessions),
            "completed_sessions": completed_count,
            "completion_rate": completed_count / total_sessions if total_sessions > 0 else 0,
            "average_collaboration_time": avg_collaboration_time,
            "expert_participation": expert_participation,
            "registered_experts": len(self.experts_database),
        }


# 示例使用
async def demo_human_ai_collaboration():
    """演示人机协作流程"""

    # 创建人类在环引擎
    collaboration_engine = HumanInTheLoopEngine()

    # 注册专家
    patent_expert = HumanExpert(
        expert_id="dr_zhang",
        name="张博士",
        title="专利分析专家",
        expertise=["patent_analysis", "patent_law", "technical_analysis"],
        availability={
            "working_hours": {"start": 9, "end": 18},
            "available_days": [0, 1, 2, 3, 4],  # 周一到周五
        },
        contact_info={"email": "zhang@expert.com", "phone": "+86-138-xxxx-xxxx"},
    )

    collaboration_engine.register_expert(patent_expert)

    # 创建协作任务
    task = await collaboration_engine.create_collaboration_task(
        task_type=TaskType.PATENT_ANALYSIS,
        title="专利CN123456789A新颖性分析",
        description="请分析该专利的新颖性,识别相关现有技术",
        context={
            "patent_number": "CN123456789A",
            "patent_title": "一种智能优化算法",
            "technical_field": "人工智能",
            "client_requirements": ["快速分析", "准确判断"],
        },
        ai_output="基于初步检索,该专利具有创新性,未发现完全相同的现有技术。建议继续深入检索以确认。",
        ai_confidence=0.75,
        priority=4,
    )

    # 启动协作会话
    session = await collaboration_engine.start_collaboration_session(task)

    print(f"协作会话已启动: {session.session_id}")
    print(f"决策级别: {task.decision_level.value}")
    print(f"协作模式: {task.collaboration_mode.value}")
    if task.assigned_expert:
        print(f"指定专家: {task.assigned_expert.name}")

    # 模拟专家输入
    human_input = "分析基本合理,但需要补充以下几个方面的检索:1. 国外专利数据库;2. 学术论文库;3. 行业标准。"
    result = await collaboration_engine.process_human_input(
        session.session_id, human_input, confidence=0.9
    )

    print(f"协作结果: {result}")

    # 获取统计信息
    stats = collaboration_engine.get_collaboration_statistics()
    print(f"协作统计: {stats}")


if __name__ == "__main__":
    asyncio.run(demo_human_ai_collaboration())
