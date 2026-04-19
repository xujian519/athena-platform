#!/usr/bin/env python3
"""
意图识别学习引擎集成编排器
Intent Recognition Learning Engines Orchestrator

统一管理P0-P3所有学习引擎与意图识别系统的集成:
- P0: 自主学习 - 性能监控和优化
- P1: 在线学习 - 模型持续优化
- P2: 强化学习 - 对话策略优化
- P3: 元学习 - 快速适应新领域

作者: Athena AI Team
版本: 1.0.0
创建: 2026-01-29
"""

from __future__ import annotations
import asyncio
import json
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

# 导入学习引擎
from production.core.learning.autonomous_learning_system import AutonomousLearningSystem
from production.core.learning.online_learning import ExperienceReplayBuffer
from production.core.learning.reinforcement_learning_agent import (
    ExplorationStrategy,
    ReinforcementLearningAgent,
    RLAction,
    RLAlgorithm,
    RLState,
)

logger = logging.getLogger(__name__)


class LearningPriority(Enum):
    """学习优先级"""
    P0 = "autonomous"  # 自主学习 - 系统级优化
    P1 = "online"      # 在线学习 - 模型优化
    P2 = "reinforcement"  # 强化学习 - 策略优化
    P3 = "meta"        # 元学习 - 快速适应


@dataclass
class IntentRecognitionExperience:
    """意图识别经验"""
    experience_id: str
    timestamp: datetime
    query: str
    predicted_intent: str
    true_intent: str | None  # 用户反馈的真实意图
    confidence: float
    correct: bool
    response_time_ms: float
    user_satisfaction: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LearningMetrics:
    """学习指标"""
    total_predictions: int = 0
    correct_predictions: int = 0
    accuracy: float = 0.0
    avg_response_time: float = 0.0
    avg_confidence: float = 0.0
    learning_cycles: int = 0
    last_update: datetime = field(default_factory=datetime.now)


class IntentLearningOrchestrator:
    """
    意图识别学习引擎编排器

    统一管理所有学习引擎，实现:
    1. P0: 自主学习 - 性能监控和系统优化
    2. P1: 在线学习 - 模型持续优化
    3. P2: 强化学习 - 对话策略优化
    4. P3: 元学习 - 快速适应新领域
    """

    def __init__(
        self,
        agent_id: str = "intent_learning_agent",
        enable_p0_autonomous: bool = True,
        enable_p1_online: bool = True,
        enable_p2_reinforcement: bool = True,
        enable_p3_meta: bool = True,
    ):
        """
        初始化学习引擎编排器

        Args:
            agent_id: 智能体ID
            enable_p0_autonomous: 启用P0自主学习
            enable_p1_online: 启用P1在线学习
            enable_p2_reinforcement: 启用P2强化学习
            enable_p3_meta: 启用P3元学习
        """
        self.agent_id = agent_id

        # 配置
        self.enable_p0 = enable_p0_autonomous
        self.enable_p1 = enable_p1_online
        self.enable_p2 = enable_p2_reinforcement
        self.enable_p3 = enable_p3_meta

        # 经验存储
        self.experiences: deque[IntentRecognitionExperience] = deque(maxlen=10000)
        self.metrics = LearningMetrics()

        # 学习引擎
        self.learning_engines: dict[str, Any] = {}

        # 初始化学习引擎
        self._initialize_engines()

        logger.info("🧠 意图识别学习引擎编排器初始化完成")
        logger.info(f"   Agent ID: {agent_id}")
        logger.info(f"   P0 (自主学习): {'✅ 启用' if self.enable_p0 else '❌ 禁用'}")
        logger.info(f"   P1 (在线学习): {'✅ 启用' if self.enable_p1 else '❌ 禁用'}")
        logger.info(f"   P2 (强化学习): {'✅ 启用' if self.enable_p2 else '❌ 禁用'}")
        logger.info(f"   P3 (元学习): {'✅ 启用' if self.enable_p3 else '❌ 禁用'}")

    def _initialize_engines(self):
        """初始化所有学习引擎"""

        # P0: 自主学习引擎 (始终启用，用于系统监控)
        if self.enable_p0:
            try:
                self.learning_engines["p0_autonomous"] = AutonomousLearningSystem(
                    agent_id=f"{self.agent_id}_autonomous"
                )
                logger.info("✅ P0 自主学习引擎初始化成功")
            except Exception as e:
                logger.warning(f"⚠️ P0 自主学习引擎初始化失败: {e}")

        # P1: 在线学习引擎
        if self.enable_p1:
            try:
                from production.core.learning.online_learning import ReplayStrategy

                # 创建经验回放缓冲区
                replay_buffer = ExperienceReplayBuffer(
                    capacity=5000,
                    strategy=ReplayStrategy.PRIORITIZED  # 使用优先级回放
                )

                # 注意: OnlineLearningEngine 需要模型，这里先创建缓冲区
                # 实际模型会在集成时提供
                self.learning_engines["p1_replay_buffer"] = replay_buffer
                logger.info("✅ P1 在线学习引擎初始化成功 (回放缓冲区)")
            except Exception as e:
                logger.warning(f"⚠️ P1 在线学习引擎初始化失败: {e}")

        # P2: 强化学习引擎
        if self.enable_p2:
            try:
                rl_agent = ReinforcementLearningAgent(
                    agent_id=f"{self.agent_id}_rl"
                )
                # 设置为Q-Learning算法
                rl_agent.algorithm = RLAlgorithm.Q_LEARNING
                rl_agent.exploration_strategy = ExplorationStrategy.EPSILON_GREEDY
                self.learning_engines["p2_reinforcement"] = rl_agent
                logger.info("✅ P2 强化学习引擎初始化成功")
            except Exception as e:
                logger.warning(f"⚠️ P2 强化学习引擎初始化失败: {e}")

        # P3: 元学习引擎 (需要模型，延迟初始化)
        if self.enable_p3:
            self.learning_engines["p3_meta"] = None  # 占位，实际使用时初始化
            logger.info("⏳ P3 元学习引擎 (延迟初始化，需要模型)")

    # =============================================================================
    # 核心接口: 记录意图识别经验
    # =============================================================================

    async def record_experience(
        self,
        query: str,
        predicted_intent: str,
        confidence: float,
        response_time_ms: float,
        true_intent: str | None = None,
        user_satisfaction: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> IntentRecognitionExperience:
        """
        记录意图识别经验

        Args:
            query: 用户查询
            predicted_intent: 预测意图
            confidence: 置信度
            response_time_ms: 响应时间
            true_intent: 真实意图 (用户反馈)
            user_satisfaction: 用户满意度 (0-1)
            metadata: 额外元数据

        Returns:
            IntentRecognitionExperience: 记录的经验
        """
        # 判断是否正确
        correct = (true_intent is None) or (predicted_intent == true_intent)

        # 创建经验对象
        experience = IntentRecognitionExperience(
            experience_id=f"{int(time.time() * 1000)}",
            timestamp=datetime.now(),
            query=query,
            predicted_intent=predicted_intent,
            true_intent=true_intent,
            confidence=confidence,
            correct=correct,
            response_time_ms=response_time_ms,
            user_satisfaction=user_satisfaction,
            metadata=metadata or {},
        )

        # 存储经验
        self.experiences.append(experience)

        # 更新指标
        self.metrics.total_predictions += 1
        if correct:
            self.metrics.correct_predictions += 1

        self.metrics.accuracy = (
            self.metrics.correct_predictions / self.metrics.total_predictions
            if self.metrics.total_predictions > 0
            else 0.0
        )

        # 更新平均响应时间
        n = self.metrics.total_predictions
        self.metrics.avg_response_time = (
            (self.metrics.avg_response_time * (n - 1) + response_time_ms) / n
        )

        # 更新平均置信度
        self.metrics.avg_confidence = (
            (self.metrics.avg_confidence * (n - 1) + confidence) / n
        )

        self.metrics.last_update = datetime.now()

        # 触发学习引擎
        await self._trigger_learning_engines(experience)

        logger.debug(
            f"📊 记录经验: {predicted_intent} "
            f"(准确率: {self.metrics.accuracy:.2%}, "
            f"置信度: {confidence:.2%})"
        )

        return experience

    async def _trigger_learning_engines(self, experience: IntentRecognitionExperience):
        """触发相应的学习引擎"""

        # P0: 自主学习 - 所有经验都学习
        if self.enable_p0 and "p0_autonomous" in self.learning_engines:
            asyncio.create_task(
                self._p0_autonomous_learning(experience)
            )

        # P1: 在线学习 - 错误样本优先学习
        if self.enable_p1 and not experience.correct:
            asyncio.create_task(
                self._p1_online_learning(experience)
            )

        # P2: 强化学习 - 需要用户反馈
        if self.enable_p2 and experience.true_intent is not None:
            asyncio.create_task(
                self._p2_reinforcement_learning(experience)
            )

        # P3: 元学习 - 检测到新领域时触发
        if self.enable_p3 and self._detect_new_domain(experience):
            asyncio.create_task(
                self._p3_meta_learning(experience)
            )

    # =============================================================================
    # P0: 自主学习 - 性能监控和系统优化
    # =============================================================================

    async def _p0_autonomous_learning(self, experience: IntentRecognitionExperience):
        """
        P0: 自主学习

        功能:
        1. 性能监控 (准确率、响应时间、置信度)
        2. 异常检测 (性能下降)
        3. 优化提案生成
        """
        try:
            p0_engine = self.learning_engines.get("p0_autonomous")
            if not p0_engine:
                return

            # 构建上下文
            context = {
                "query": experience.query,
                "predicted_intent": experience.predicted_intent,
                "confidence": experience.confidence,
                "response_time_ms": experience.response_time_ms,
                "current_accuracy": self.metrics.accuracy,
                "avg_response_time": self.metrics.avg_response_time,
            }

            # 构建动作
            action = "intent_recognition"

            # 构建结果
            result = {
                "success": experience.correct,
                "confidence": experience.confidence,
                "response_time_ms": experience.response_time_ms,
            }

            # 计算奖励
            reward = 1.0 if experience.correct else -1.0
            if experience.user_satisfaction is not None:
                reward = experience.user_satisfaction if experience.correct else -experience.user_satisfaction

            # 从经验中学习
            await p0_engine.learn_from_experience(
                context=context,
                action=action,
                result=result,
                reward=reward,
            )

            logger.debug(f"🧠 P0 自主学习: 奖励={reward:.2f}")

        except Exception as e:
            logger.error(f"❌ P0 自主学习失败: {e}")

    # =============================================================================
    # P1: 在线学习 - 模型持续优化
    # =============================================================================

    async def _p1_online_learning(self, experience: IntentRecognitionExperience):
        """
        P1: 在线学习

        功能:
        1. 存储错误样本到经验回放缓冲区
        2. 定期增量训练模型
        3. 防止灾难遗忘
        """
        try:
            replay_buffer = self.learning_engines.get("p1_replay_buffer")
            if not replay_buffer:
                return

            # 创建学习经验 (适配在线学习格式)
            from production.core.learning.online_learning import Experience

            learning_experience = Experience(
                task_id="intent_classification",
                input_data=experience.query,
                target=experience.true_intent or experience.predicted_intent,
                reward=1.0 if experience.correct else -1.0,
                importance=1.0 - experience.confidence,  # 低置信度样本更重要
                metadata={
                    "predicted_intent": experience.predicted_intent,
                    "confidence": experience.confidence,
                },
            )

            # 添加到回放缓冲区
            replay_buffer.add(learning_experience)

            logger.debug(
                f"📚 P1 在线学习: 存储样本 "
                f"(重要性: {learning_experience.importance:.2f})"
            )

            # TODO: 定期触发模型增量训练
            # 这需要实际的模型实例和训练逻辑

        except Exception as e:
            logger.error(f"❌ P1 在线学习失败: {e}")

    # =============================================================================
    # P2: 强化学习 - 对话策略优化
    # =============================================================================

    async def _p2_reinforcement_learning(self, experience: IntentRecognitionExperience):
        """
        P2: 强化学习

        功能:
        1. 学习最优的意图确认策略
        2. 优化多轮对话决策
        3. 平衡探索与利用
        """
        try:
            rl_agent = self.learning_engines.get("p2_reinforcement")
            if not rl_agent:
                return

            # 构建状态
            state = RLState(
                state_id=f"intent_{experience.predicted_intent}",
                features={
                    "confidence": experience.confidence,
                    "response_time_ms": experience.response_time_ms,
                    "predicted_intent": experience.predicted_intent,
                }
            )

            # 定义可用动作 (意图确认策略)
            available_actions = [
                RLAction(action_id="accept", action_name="直接接受预测", parameters={}),
                RLAction(action_id="verify", action_name="询问用户确认", parameters={}),
                RLAction(action_id="fallback", action_name="使用默认策略", parameters={}),
            ]

            # 构建下一个状态 (简化)
            next_state = RLState(
                state_id="next",
                features={"correct": experience.correct}
            )

            # 计算奖励
            reward = 1.0 if experience.correct else -1.0
            if experience.user_satisfaction is not None:
                reward = experience.user_satisfaction if experience.correct else -experience.user_satisfaction

            # Q-Learning更新
            rl_agent.q_table[state.state_id, "accept"] += (
                rl_agent.learning_rate *
                (reward + rl_agent.discount_factor * 0 - rl_agent.q_table[state.state_id, "accept"])
            )

            logger.debug(
                f"🎮 P2 强化学习: Q值更新 "
                f"(奖励={reward:.2f}, 动作=accept)"
            )

        except Exception as e:
            logger.error(f"❌ P2 强化学习失败: {e}")

    # =============================================================================
    # P3: 元学习 - 快速适应新领域
    # =============================================================================

    def _detect_new_domain(self, experience: IntentRecognitionExperience) -> bool:
        """
        检测是否出现新领域

        基于以下信号:
        1. 低置信度但正确 (新表达方式)
        2. 置信度高但错误 (领域混淆)
        3. 响应时间异常
        """
        # 低置信度但可能正确
        if experience.confidence < 0.6 and experience.true_intent is None:
            return True

        # 置信度高但错误 (可能是新领域)
        if experience.confidence > 0.8 and not experience.correct:
            return True

        return False

    async def _p3_meta_learning(self, experience: IntentRecognitionExperience):
        """
        P3: 元学习

        功能:
        1. 快速适应新领域
        2. 少样本学习
        3. 迁移学习
        """
        try:
            logger.info(
                f"🧠 P3 元学习: 检测到新领域样本 "
                f"(查询: {experience.query[:50]}...)"
            )

            # TODO: 实现实际的元学习逻辑
            # 1. 收集少量样本
            # 2. 使用MAML快速适应
            # 3. 更新模型参数

            logger.debug("🧠 P3 元学习: 标记为需要快速适应")

        except Exception as e:
            logger.error(f"❌ P3 元学习失败: {e}")

    # =============================================================================
    # 公共接口
    # =============================================================================

    def get_metrics(self) -> LearningMetrics:
        """获取学习指标"""
        return self.metrics

    def get_learning_status(self) -> dict[str, Any]:
        """获取学习引擎状态"""
        return {
            "agent_id": self.agent_id,
            "total_experiences": len(self.experiences),
            "metrics": {
                "accuracy": self.metrics.accuracy,
                "avg_response_time_ms": self.metrics.avg_response_time,
                "avg_confidence": self.metrics.avg_confidence,
                "total_predictions": self.metrics.total_predictions,
                "learning_cycles": self.metrics.learning_cycles,
            },
            "engines": {
                "p0_autonomous": "p0_autonomous" in self.learning_engines,
                "p1_online": "p1_replay_buffer" in self.learning_engines,
                "p2_reinforcement": "p2_reinforcement" in self.learning_engines,
                "p3_meta": "p3_meta" in self.learning_engines,
            },
            "last_update": self.metrics.last_update.isoformat(),
        }

    async def optimize_system(self) -> dict[str, Any]:
        """
        触发系统优化 (P0自主学习)

        Returns:
            优化结果
        """
        if not self.enable_p0 or "p0_autonomous" not in self.learning_engines:
            return {"status": "skipped", "reason": "P0自主学习未启用"}

        try:
            p0_engine = self.learning_engines["p0_autonomous"]

            # 分析性能趋势
            recent_experiences = list(self.experiences)[-100:]
            if len(recent_experiences) < 10:
                return {"status": "skipped", "reason": "样本不足"}

            # 计算最近准确率
            recent_accuracy = sum(
                1 for e in recent_experiences if e.correct
            ) / len(recent_experiences)

            # 检查是否需要优化
            if recent_accuracy < 0.7:  # 阈值可配置
                logger.info(f"🔧 P0 自主学习: 触发系统优化 (当前准确率: {recent_accuracy:.2%})")

                # 生成优化提案
                optimization_proposal = await p0_engine.optimize_parameters()

                return {
                    "status": "optimized",
                    "recent_accuracy": recent_accuracy,
                    "proposal": optimization_proposal,
                }
            else:
                return {
                    "status": "good",
                    "recent_accuracy": recent_accuracy,
                    "message": "系统性能良好，无需优化"
                }

        except Exception as e:
            logger.error(f"❌ 系统优化失败: {e}")
            return {"status": "error", "error": str(e)}

    def export_experiences(self, filepath: str | None = None) -> str:
        """
        导出学习经验

        Args:
            filepath: 导出文件路径

        Returns:
            导出文件的完整路径
        """
        if filepath is None:
            filepath = f"data/intent_experiences_{int(time.time())}.json"

        # 确保目录存在
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        # 转换为可序列化格式
        experiences_data = [
            {
                "experience_id": e.experience_id,
                "timestamp": e.timestamp.isoformat(),
                "query": e.query,
                "predicted_intent": e.predicted_intent,
                "true_intent": e.true_intent,
                "confidence": e.confidence,
                "correct": e.correct,
                "response_time_ms": e.response_time_ms,
                "user_satisfaction": e.user_satisfaction,
                "metadata": e.metadata,
            }
            for e in self.experiences
        ]

        # 写入文件
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({
                "export_time": datetime.now().isoformat(),
                "total_experiences": len(experiences_data),
                "metrics": {
                    "accuracy": self.metrics.accuracy,
                    "avg_response_time_ms": self.metrics.avg_response_time,
                    "avg_confidence": self.metrics.avg_confidence,
                    "total_predictions": self.metrics.total_predictions,
                },
                "experiences": experiences_data,
            }, f, indent=2, ensure_ascii=False)

        logger.info(f"📤 导出学习经验: {filepath} ({len(experiences_data)} 条)")
        return filepath


# =============================================================================
# 全局单例
# =============================================================================
_orchestrator: IntentLearningOrchestrator | None = None


def get_intent_learning_orchestrator(
    agent_id: str = "intent_learning_agent",
    enable_all: bool = True,
) -> IntentLearningOrchestrator:
    """
    获取意图识别学习引擎编排器单例

    Args:
        agent_id: 智能体ID
        enable_all: 是否启用所有学习引擎

    Returns:
        IntentLearningOrchestrator: 编排器实例
    """
    global _orchestrator

    if _orchestrator is None:
        _orchestrator = IntentLearningOrchestrator(
            agent_id=agent_id,
            enable_p0_autonomous=enable_all,
            enable_p1_online=enable_all,
            enable_p2_reinforcement=enable_all,
            enable_p3_meta=enable_all,
        )

    return _orchestrator
