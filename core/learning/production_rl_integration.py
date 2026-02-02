#!/usr/bin/env python3
"""
生产环境强化学习集成系统
Production Reinforcement Learning Integration System

功能:
1. 从用户交互中收集反馈
2. 自动计算奖励信号
3. 持续学习和优化
4. 模型持久化和版本管理
5. 性能监控和报告

作者: Athena平台团队
版本: v1.0.0 "生产就绪"
创建: 2025-01-08
"""
import numpy as np

import json
import logging
import pickle
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


from .reinforcement_learning_agent import (
    RLAction,
    RLState,
    RLTransition,
    get_rl_agent,
)

logger = logging.getLogger(__name__)


class RewardType(Enum):
    """奖励类型"""

    # 用户显式反馈
    THUMBS_UP = "thumbs_up"  # 点赞
    THUMBS_DOWN = "thumbs_down"  # 点踩
    RATING_1_5 = "rating_1_5"  # 1-5分评分
    TEXT_FEEDBACK = "text_feedback"  # 文字反馈

    # 隐式反馈
    RESPONSE_TIME = "response_time"  # 响应时间
    COMPLETION_RATE = "completion_rate"  # 完成率
    RE_ENGAGEMENT = "re_engagement"  # 再次使用
    CORRECTION = "correction"  # 用户纠正

    # 任务质量
    TASK_SUCCESS = "task_success"  # 任务成功
    TASK_FAILURE = "task_failure"  # 任务失败
    ERROR_OCCURRED = "error_occurred"  # 发生错误


@dataclass
class UserInteraction:
    """用户交互记录"""

    interaction_id: str
    session_id: str
    timestamp: datetime
    user_input: str
    agent_response: str
    capability_used: str
    context: dict[str, Any] = field(default_factory=dict)

    # 反馈信息
    explicit_feedback: float | None = None  # 显式评分 0-1
    implicit_feedback: dict[str, float] = field(default_factory=dict)

    # 质量指标
    response_time: float = 0.0
    error_occurred: bool = False
    user_corrected: bool = False

    # 元数据
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RLTrainingConfig:
    """强化学习训练配置"""

    # 奖励权重
    thumbs_up_weight: float = 1.0
    thumbs_down_weight: float = -1.0
    rating_weight: float = 0.5
    response_time_weight: float = -0.1
    task_success_weight: float = 1.0
    task_failure_weight: float = -0.5
    error_weight: float = -0.3

    # 训练参数
    learning_rate: float = 0.1
    discount_factor: float = 0.95
    epsilon: float = 0.1
    epsilon_decay: float = 0.995
    epsilon_min: float = 0.01

    # 持久化
    save_interval: int = 100  # 每N次交互保存一次
    backup_count: int = 5  # 保留最近N个备份


class ProductionRLSystem:
    """
    生产环境强化学习系统

    负责收集用户交互,计算奖励,训练RL模型
    """

    def __init__(self, config: RLTrainingConfig | None = None):
        """初始化生产RL系统"""
        self.config = config or RLTrainingConfig()

        # RL智能体
        self.rl_agent = get_rl_agent()
        self.rl_agent.learning_rate = self.config.learning_rate
        self.rl_agent.discount_factor = self.config.discount_factor
        self.rl_agent.epsilon = self.config.epsilon
        self.rl_agent.epsilon_decay = self.config.epsilon_decay
        self.rl_agent.epsilon_min = self.config.epsilon_min

        # 交互历史
        self.interaction_history: list[UserInteraction] = []
        self.total_interactions = 0

        # 持久化路径
        self.data_dir = Path(__file__).parent.parent.parent / "data" / "rl_production"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.model_path = self.data_dir / "rl_model.pkl"
        self.interactions_path = self.data_dir / "interactions.jsonl"
        self.metrics_path = self.data_dir / "metrics.json"

        # 加载已有模型
        self._load_model()

        logger.info("🎮 生产环境强化学习系统初始化完成")

    def _load_model(self) -> Any:
        """加载已有模型"""
        if self.model_path.exists():
            try:
                with open(self.model_path, "rb") as f:
                    data = pickle.load(f)
                    self.rl_agent.q_table = data.get("q_table", {})
                    self.rl_agent.epsilon = data.get("epsilon", self.config.epsilon)
                    self.total_interactions = data.get("total_interactions", 0)

                logger.info(f"✅ 加载已有RL模型: {self.total_interactions} 次交互")
            except Exception as e:
                logger.warning(f"⚠️ 加载模型失败: {e},使用新模型")

    def _save_model(self) -> Any:
        """保存模型"""
        try:
            # 备份旧模型
            if self.model_path.exists():
                backup_path = (
                    self.data_dir
                    / f"rl_model_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
                )
                # 只保留最近N个备份
                backups = sorted(self.data_dir.glob("rl_model_backup_*.pkl"))
                if len(backups) >= self.config.backup_count:
                    for old_backup in backups[: -self.config.backup_count + 1]:
                        old_backup.unlink()

                self.model_path.rename(backup_path)
                logger.debug(f"💾 备份模型到: {backup_path.name}")

            # 保存当前模型
            data = {
                "q_table": dict(self.rl_agent.q_table),
                "epsilon": self.rl_agent.epsilon,
                "total_interactions": self.total_interactions,
                "saved_at": datetime.now().isoformat(),
            }

            with open(self.model_path, "wb") as f:
                pickle.dump(data, f)

            logger.debug(f"💾 模型已保存: {self.total_interactions} 次交互")

        except Exception as e:
            logger.error(f"❌ 保存模型失败: {e}")

    def _save_interaction(self, interaction: UserInteraction) -> Any:
        """保存交互记录"""
        try:
            with open(self.interactions_path, "a") as f:
                record = asdict(interaction)
                record["timestamp"] = interaction.timestamp.isoformat()
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

            # 定期清理旧记录(保留最近10000条)
            if self.total_interactions % 1000 == 0:
                self._cleanup_old_interactions()

        except Exception as e:
            logger.error(f"❌ 保存交互记录失败: {e}")

    def _cleanup_old_interactions(self, keep_count: int = 10000) -> Any:
        """清理旧交互记录"""
        try:
            if not self.interactions_path.exists():
                return

            with open(self.interactions_path) as f:
                lines = f.readlines()

            if len(lines) > keep_count:
                with open(self.interactions_path, "w") as f:
                    f.writelines(lines[-keep_count:])
                logger.debug(f"🧹 清理了 {len(lines) - keep_count} 条旧记录")

        except Exception as e:
            logger.error(f"❌ 清理旧记录失败: {e}")

    def calculate_reward(self, interaction: UserInteraction) -> float:
        """
        计算奖励信号

        综合显式和隐式反馈计算奖励
        """
        reward = 0.0

        # 1. 显式反馈
        if interaction.explicit_feedback is not None:
            # 归一化到 [-1, 1]
            reward += (interaction.explicit_feedback - 0.5) * 2 * self.config.rating_weight

        # 2. 响应时间惩罚(超过5秒开始惩罚)
        if interaction.response_time > 5.0:
            reward += self.config.response_time_weight * (interaction.response_time - 5.0) / 5.0

        # 3. 任务成功/失败
        if interaction.error_occurred:
            reward += self.config.error_weight
            interaction.implicit_feedback["error"] = -1.0

        # 4. 用户纠正(说明回答不准确)
        if interaction.user_corrected:
            reward += self.config.task_failure_weight
            interaction.implicit_feedback["corrected"] = -1.0

        # 5. 完成率奖励
        if not interaction.error_occurred and not interaction.user_corrected:
            reward += self.config.task_success_weight * 0.1
            interaction.implicit_feedback["completed"] = 1.0

        # 限制奖励范围
        reward = max(-2.0, min(2.0, reward))

        return reward

    def create_state_from_interaction(self, interaction: UserInteraction) -> RLState:
        """从交互创建状态"""
        # 使用能力类型和上下文作为状态特征
        state_id = f"{interaction.capability_used}_{interaction.timestamp.hour}"

        features = {
            "capability": interaction.capability_used,
            "hour": interaction.timestamp.hour,
            "day_of_week": interaction.timestamp.weekday(),
            "interaction_count": self.total_interactions,
        }

        return RLState(state_id=state_id, features=features)

    def create_action_from_interaction(self, interaction: UserInteraction) -> RLAction:
        """从交互创建动作"""
        # 动作ID基于使用的能力和响应特征
        action_id = f"{interaction.capability_used}_response"

        return RLAction(
            action_id=action_id,
            action_name=f"使用{interaction.capability_used}响应",
            parameters={
                "response_length": len(interaction.agent_response),
                "has_error": interaction.error_occurred,
            },
        )

    async def record_interaction(
        self,
        user_input: str,
        agent_response: str,
        capability_used: str,
        context: dict[str, Any] | None = None,
        explicit_feedback: float | None = None,
        response_time: float = 0.0,
        error_occurred: bool = False,
        user_corrected: bool = False,
    ) -> dict[str, Any]:
        """
        记录一次用户交互并更新RL模型

        Args:
            user_input: 用户输入
            agent_response: 智能体响应
            capability_used: 使用的能力
            context: 上下文信息
            explicit_feedback: 显式反馈 (0-1)
            response_time: 响应时间(秒)
            error_occurred: 是否发生错误
            user_corrected: 用户是否纠正了答案

        Returns:
            处理结果
        """
        try:
            # 创建交互记录
            interaction = UserInteraction(
                interaction_id=f"interaction_{self.total_interactions}_{int(datetime.now().timestamp())}",
                session_id=context.get("session_id", "default") if context else "default",
                timestamp=datetime.now(),
                user_input=user_input,
                agent_response=agent_response,
                capability_used=capability_used,
                context=context or {},
                explicit_feedback=explicit_feedback,
                response_time=response_time,
                error_occurred=error_occurred,
                user_corrected=user_corrected,
            )

            # 计算奖励
            reward = self.calculate_reward(interaction)
            interaction.implicit_feedback["total_reward"] = reward

            # 创建状态和动作
            state = self.create_state_from_interaction(interaction)
            action = self.create_action_from_interaction(interaction)

            # 创建下一个状态(简化:使用相同状态)
            next_state = state

            # 创建转移
            transition = RLTransition(
                state=state, action=action, reward=reward, next_state=next_state, done=False
            )

            # 学习
            learning_metrics = await self.rl_agent.learn(transition)

            # 保存记录
            self.interaction_history.append(interaction)
            self.total_interactions += 1

            self._save_interaction(interaction)

            # 定期保存模型
            if self.total_interactions % self.config.save_interval == 0:
                self._save_model()
                logger.info(f"💾 已保存RL模型 ({self.total_interactions} 次交互)")

            # 返回结果
            result = {
                "success": True,
                "interaction_id": interaction.interaction_id,
                "reward": reward,
                "learning_metrics": learning_metrics,
                "total_interactions": self.total_interactions,
                "epsilon": self.rl_agent.epsilon,
            }

            logger.debug(
                f"📊 交互已记录: reward={reward:.3f}, "
                f"total={self.total_interactions}, ε={self.rl_agent.epsilon:.3f}"
            )

            return result

        except Exception as e:
            logger.error(f"❌ 记录交互失败: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def add_explicit_feedback(self, interaction_id: str, feedback: float) -> dict[str, Any]:
        """
        为已有交互添加显式反馈

        Args:
            interaction_id: 交互ID
            feedback: 反馈值 (0-1)

        Returns:
            处理结果
        """
        try:
            # 查找交互
            interaction = None
            for inter in reversed(self.interaction_history):
                if inter.interaction_id == interaction_id:
                    interaction = inter
                    break

            if not interaction:
                return {"success": False, "error": f"未找到交互: {interaction_id}"}

            # 更新反馈
            old_feedback = interaction.explicit_feedback
            interaction.explicit_feedback = feedback

            # 重新计算奖励并学习
            reward = self.calculate_reward(interaction)

            state = self.create_state_from_interaction(interaction)
            action = self.create_action_from_interaction(interaction)

            transition = RLTransition(
                state=state, action=action, reward=reward, next_state=state, done=False
            )

            learning_metrics = await self.rl_agent.learn(transition)

            # 保存更新
            self._save_interaction(interaction)

            logger.info(
                f"📝 更新反馈: {interaction_id}, "
                f"{old_feedback} -> {feedback}, reward={reward:.3f}"
            )

            return {
                "success": True,
                "old_feedback": old_feedback,
                "new_feedback": feedback,
                "reward": reward,
                "learning_metrics": learning_metrics,
            }

        except Exception as e:
            logger.error(f"❌ 添加反馈失败: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def get_metrics(self) -> dict[str, Any]:
        """获取RL系统指标"""
        # 最近100次交互的奖励
        recent_interactions = list(self.interaction_history)[-100:]
        recent_rewards = []
        for inter in recent_interactions:
            reward = self.calculate_reward(inter)
            recent_rewards.append(reward)

        # RL智能体报告
        rl_report = await self.rl_agent.get_agent_report()

        return {
            "total_interactions": self.total_interactions,
            "recent_rewards": {
                "count": len(recent_rewards),
                "mean": float(np.mean(recent_rewards)) if recent_rewards else 0,
                "std": float(np.std(recent_rewards)) if recent_rewards else 0,
                "min": float(np.min(recent_rewards)) if recent_rewards else 0,
                "max": float(np.max(recent_rewards)) if recent_rewards else 0,
            },
            "rl_agent": rl_report,
            "learning_progress": {
                "epsilon": self.rl_agent.epsilon,
                "q_table_size": len(self.rl_agent.q_table),
                "exploration_rate": self.rl_agent.epsilon,
            },
            "timestamp": datetime.now().isoformat(),
        }

    async def save_metrics(self):
        """保存指标到文件"""
        try:
            metrics = await self.get_metrics()
            with open(self.metrics_path, "w") as f:
                json.dump(metrics, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"❌ 保存指标失败: {e}")

    def get_learning_summary(self) -> str:
        """获取学习摘要(用于展示)"""
        recent_interactions = list(self.interaction_history)[-50:]

        if not recent_interactions:
            return "🎮 暂无学习数据"

        rewards = [self.calculate_reward(inter) for inter in recent_interactions]
        avg_reward = np.mean(rewards)

        summary = f"""
🎮 强化学习系统摘要

📊 学习统计:
├── 总交互次数: {self.total_interactions}
├── 最近50次平均奖励: {avg_reward:.3f}
├── Q表大小: {len(self.rl_agent.q_table)}
└── 当前探索率: {self.rl_agent.epsilon:.3f}

📈 学习进度:
├── 已从 {self.total_interactions} 次交互中学习
├── 模型持续优化中
└── 定期自动保存

💡 提示:
通过日常使用,系统会自动学习并提升响应质量。
您的反馈(点赞/点踩)会帮助系统更快进步!
        """.strip()

        return summary


# 全局单例
_production_rl_system: ProductionRLSystem | None = None


def get_production_rl_system() -> ProductionRLSystem:
    """获取生产RL系统单例"""
    global _production_rl_system
    if _production_rl_system is None:
        _production_rl_system = ProductionRLSystem()
    return _production_rl_system
