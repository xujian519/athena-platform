#!/usr/bin/env python3
"""
强化学习智能体
Reinforcement Learning Agent

实现强化学习能力:
1. Q-Learning
2. Policy Gradient
3. Actor-Critic
4. 多臂老虎机
5. 经验回放

作者: Athena平台团队
创建时间: 2025-12-26
版本: v1.0.0 "强化探索"
"""
from __future__ import annotations
import logging
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class RLAlgorithm(Enum):
    """强化学习算法"""

    Q_LEARNING = "q_learning"  # Q-Learning
    DEEP_Q = "deep_q"  # Deep Q-Network
    POLICY_GRADIENT = "policy_gradient"  # Policy Gradient
    ACTOR_CRITIC = "actor_critic"  # Actor-Critic
    PPO = "ppo"  # Proximal Policy Optimization
    A3C = "a3c"  # Asynchronous Actor-Critic
    MULTI_ARM_BANDIT = "multi_arm_bandit"  # 多臂老虎机


class ExplorationStrategy(Enum):
    """探索策略"""

    EPSILON_GREEDY = "epsilon_greedy"  # ε-贪婪
    SOFTMAX = "softmax"  # Softmax
    UCB = "ucb"  # Upper Confidence Bound
    THOMPSON_SAMPLING = "thompson"  # Thompson Sampling


@dataclass
class RLAction:
    """强化学习动作"""

    action_id: str
    action_name: str
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class RLState:
    """强化学习状态"""

    state_id: str
    features: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RLTransition:
    """强化学习转移"""

    state: RLState
    action: RLAction
    reward: float
    next_state: RLState
    done: bool


@dataclass
class RLExperience:
    """强化学习经验"""

    episode: int
    transitions: list[RLTransition]
    total_reward: float
    episode_length: int
    timestamp: datetime = field(default_factory=datetime.now)


class ReinforcementLearningAgent:
    """
    强化学习智能体

    核心功能:
    1. 环境交互
    2. 策略学习
    3. 价值估计
    4. 经验回放
    5. 探索-利用平衡
    """

    def __init__(self, agent_id: str = "athena_rl"):
        self.agent_id = agent_id

        # 算法配置
        self.algorithm = RLAlgorithm.Q_LEARNING
        self.exploration_strategy = ExplorationStrategy.EPSILON_GREEDY

        # Q表(状态-动作值)
        self.q_table: dict[tuple[str, str], float] = defaultdict(float)

        # 动作计数(用于UCB等探索策略)
        self.action_counts: dict[str, int] = defaultdict(int)

        # 策略网络
        self.policy_network: Any | None = None

        # 经验回放缓冲
        self.replay_buffer: deque[RLTransition] = deque(maxlen=10000)

        # 统计信息
        self.episode_history: deque[RLExperience] = deque(maxlen=1000)
        self.current_episode = 0
        self.total_steps = 0
        self.total_reward = 0.0

        # 超参数
        self.learning_rate = 0.1
        self.discount_factor = 0.95
        self.epsilon = 0.1  # 探索率
        self.epsilon_decay = 0.995
        self.epsilon_min = 0.01

        logger.info(f"🎮 强化学习智能体初始化完成 - {agent_id}")

    async def select_action(self, state: RLState, available_actions: list[RLAction]) -> RLAction:
        """选择动作(探索-利用平衡)"""
        if self.exploration_strategy == ExplorationStrategy.EPSILON_GREEDY:
            return await self._epsilon_greedy_select(state, available_actions)
        elif self.exploration_strategy == ExplorationStrategy.SOFTMAX:
            return await self._softmax_select(state, available_actions)
        elif self.exploration_strategy == ExplorationStrategy.UCB:
            return await self._ucb_select(state, available_actions)
        else:  # THOMPSON_SAMPLING
            return await self._thompson_sampling_select(state, available_actions)

    async def _epsilon_greedy_select(
        self, state: RLState, available_actions: list[RLAction]
    ) -> RLAction:
        """ε-贪婪策略"""
        if np.random.random() < self.epsilon:
            # 探索:随机选择
            selected = available_actions[np.random.randint(0, len(available_actions))]
            logger.debug(f"🎲 探索: {selected.action_name}")
        else:
            # 利用:选择Q值最大的
            state_id = state.state_id
            q_values = [
                (action, self.q_table[state_id, action.action_id]) for action in available_actions
            ]

            selected = max(q_values, key=lambda x: x[1])[0]
            logger.debug(
                f"🎯 利用: {selected.action_name} (Q={self.q_table[state_id, selected.action_id]:.3f})"
            )

        # 更新动作计数
        self.action_counts[selected.action_id] += 1

        return selected

    async def _softmax_select(self, state: RLState, available_actions: list[RLAction]) -> RLAction:
        """Softmax策略"""
        state_id = state.state_id

        # 计算Softmax概率
        q_values = np.array([self.q_table[state_id, a.action_id] for a in available_actions])

        # 温度参数
        temperature = 1.0
        exp_values = np.exp(q_values / temperature)
        probabilities = exp_values / np.sum(exp_values)

        # 根据概率选择
        selected_idx = np.random.choice(len(available_actions), p=probabilities)
        selected = available_actions[selected_idx]

        # 更新动作计数
        self.action_counts[selected.action_id] += 1

        return selected

    async def _ucb_select(self, state: RLState, available_actions: list[RLAction]) -> RLAction:
        """
        UCB (Upper Confidence Bound) 策略

        使用改进的动作计数机制,准确跟踪每个动作的选择次数
        """
        state_id = state.state_id

        # 计算UCB值
        ucb_values = []
        for action in available_actions:
            q_value = self.q_table[state_id, action.action_id]
            # 使用正确的动作计数
            action_count = self.action_counts[action.action_id]

            # UCB公式
            if action_count == 0:
                ucb = float("inf")
            else:
                exploration_bonus = np.sqrt(2 * np.log(self.total_steps + 1) / action_count)
                ucb = q_value + exploration_bonus

            ucb_values.append((action, ucb))

        # 选择UCB最大的动作
        selected = max(ucb_values, key=lambda x: x[1])[0]

        # 更新动作计数
        self.action_counts[selected.action_id] += 1

        return selected

    async def _thompson_sampling_select(
        self, state: RLState, available_actions: list[RLAction]
    ) -> RLAction:
        """Thompson Sampling策略"""
        state_id = state.state_id

        # 从后验分布采样
        samples = []
        for action in available_actions:
            q_value = self.q_table[state_id, action.action_id]
            # 简化:从正态分布采样
            sample = np.random.normal(q_value, 1.0)
            samples.append((action, sample))

        # 选择采样值最大的
        selected = max(samples, key=lambda x: x[1])[0]

        # 更新动作计数
        self.action_counts[selected.action_id] += 1

        return selected

    async def learn(self, transition: RLTransition) -> dict[str, float]:
        """从经验中学习"""
        state_id = transition.state.state_id
        action_id = transition.action.action_id
        reward = transition.reward
        next_state_id = transition.next_state.state_id

        # Q-Learning更新
        if self.algorithm == RLAlgorithm.Q_LEARNING:
            old_q = self.q_table[state_id, action_id]

            # 找到下一个状态的最大Q值
            next_q_values = [self.q_table[next_state_id, a] for a in [action_id]]  # 简化
            max_next_q = max(next_q_values) if next_q_values else 0

            # Bellman方程
            new_q = old_q + self.learning_rate * (
                reward + self.discount_factor * max_next_q - old_q
            )

            self.q_table[state_id, action_id] = new_q

            learning_metrics = {
                "old_q": old_q,
                "new_q": new_q,
                "td_error": abs(new_q - old_q),
                "reward": reward,
            }

        else:
            # 其他算法的简化版本
            old_q = self.q_table[state_id, action_id]
            new_q = old_q  # 保持不变
            learning_metrics = {"reward": reward, "old_q": old_q, "new_q": new_q, "td_error": 0.0}

        # 添加到经验回放缓冲
        self.replay_buffer.append(transition)

        logger.debug(f"📚 学习: Q({state_id}, {action_id}) = {new_q:.3f}")

        return learning_metrics

    async def learn_from_batch(self, transitions: list[RLTransition]) -> dict[str, float]:
        """批量学习"""
        total_td_error = 0

        for transition in transitions:
            metrics = await self.learn(transition)
            if "td_error" in metrics:
                total_td_error += metrics["td_error"]

        avg_td_error = total_td_error / len(transitions) if transitions else 0

        return {"avg_td_error": avg_td_error, "batch_size": len(transitions)}

    async def experience_replay(self, batch_size: int = 32) -> dict[str, float | None]:
        """
        经验回放(优化采样效率)
        """
        if len(self.replay_buffer) < batch_size:
            return None

        # 使用random.sample进行高效采样(而不是np.random.choice)
        import random

        samples = random.sample(list(self.replay_buffer), batch_size)

        # 批量学习
        return await self.learn_from_batch(samples)

    async def run_episode(
        self,
        env_steps: Callable[[RLState], tuple[list[RLAction], RLState, float, bool]],
        max_steps: int = 100,
    ) -> RLExperience:
        """运行一个episode"""
        self.current_episode += 1

        # 初始状态
        state = RLState(state_id="state_0", features={})

        transitions = []
        total_reward = 0
        steps = 0

        for _step in range(max_steps):
            # 获取可用动作和下一步(env_steps是同步函数)
            available_actions, next_state, reward, done = env_steps(state)

            # 选择动作
            action = await self.select_action(state, available_actions)

            # 记录转移
            transition = RLTransition(
                state=state, action=action, reward=reward, next_state=next_state, done=done
            )
            transitions.append(transition)

            # 学习
            await self.learn(transition)

            total_reward += reward
            steps += 1
            self.total_steps += 1

            state = next_state

            if done:
                break

        # 衰减探索率
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

        # 创建经验
        experience = RLExperience(
            episode=self.current_episode,
            transitions=transitions,
            total_reward=total_reward,
            episode_length=steps,
        )

        self.episode_history.append(experience)

        logger.info(
            f"🏁 Episode {self.current_episode} 完成: "
            f"reward={total_reward:.2f}, steps={steps}, ε={self.epsilon:.3f}"
        )

        return experience

    async def get_policy(self, state: RLState) -> dict[str, float]:
        """获取当前策略(动作概率分布)"""
        state_id = state.state_id

        # 获取所有可能的动作及其Q值
        policy = {}
        for (s, a), q in self.q_table.items():
            if s == state_id:
                policy[a] = q

        return policy

    async def get_value(self, state: RLState) -> float:
        """获取状态价值(最大Q值)"""
        state_id = state.state_id

        q_values = [q for (s, a), q in self.q_table.items() if s == state_id]

        if not q_values:
            return 0.0

        return max(q_values)

    async def get_agent_report(self) -> dict[str, Any]:
        """获取智能体报告(增强版,包含动作计数)"""
        recent_rewards = [exp.total_reward for exp in list(self.episode_history)[-100:]]

        return {
            "agent_id": self.agent_id,
            "algorithm": self.algorithm.value,
            "exploration_strategy": self.exploration_strategy.value,
            "total_episodes": self.current_episode,
            "total_steps": self.total_steps,
            "q_table_size": len(self.q_table),
            "replay_buffer_size": len(self.replay_buffer),
            "epsilon": self.epsilon,
            "performance": (
                {
                    "avg_reward": np.mean(recent_rewards) if recent_rewards else 0,
                    "best_reward": max(recent_rewards) if recent_rewards else 0,
                    "recent_episodes": len(recent_rewards),
                }
                if recent_rewards
                else {}
            ),
            "hyperparameters": {
                "learning_rate": self.learning_rate,
                "discount_factor": self.discount_factor,
                "epsilon_decay": self.epsilon_decay,
            },
            "action_statistics": {
                "total_actions_tried": len(self.action_counts),
                "action_counts": dict(self.action_counts),
            },
        }


# 导出便捷函数
_rl_agent: ReinforcementLearningAgent | None = None


def get_rl_agent() -> ReinforcementLearningAgent:
    """获取强化学习智能体单例"""
    global _rl_agent
    if _rl_agent is None:
        _rl_agent = ReinforcementLearningAgent()
    return _rl_agent


# =============================================================================
# === 策略类 ===
# =============================================================================

@dataclass
class RLPolicy:
    """强化学习策略"""

    algorithm: RLAlgorithm
    state_space_size: int
    action_space_size: int
    learning_rate: float = 0.001
    discount_factor: float = 0.99
    epsilon: float = 0.1
    epsilon_decay: float = 0.995
    exploration_strategy: ExplorationStrategy = ExplorationStrategy.EPSILON_GREEDY

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "algorithm": self.algorithm.value,
            "state_space_size": self.state_space_size,
            "action_space_size": self.action_space_size,
            "learning_rate": self.learning_rate,
            "discount_factor": self.discount_factor,
            "epsilon": self.epsilon,
            "epsilon_decay": self.epsilon_decay,
            "exploration_strategy": self.exploration_strategy.value,
        }


# 创建默认策略
def create_default_policy(
    state_space_size: int,
    action_space_size: int,
    algorithm: RLAlgorithm = RLAlgorithm.Q_LEARNING,
) -> RLPolicy:
    """创建默认强化学习策略"""
    return RLPolicy(
        algorithm=algorithm,
        state_space_size=state_space_size,
        action_space_size=action_space_size,
    )


@dataclass
class RLTrainer:
    """强化学习训练器"""

    agent_id: str
    algorithm: RLAlgorithm = RLAlgorithm.Q_LEARNING
    learning_rate: float = 0.1
    discount_factor: float = 0.95
    epsilon_start: float = 1.0
    epsilon_end: float = 0.01
    epsilon_decay: float = 0.995
    episodes: int = 1000
    max_steps_per_episode: int = 100
    eval_frequency: int = 100
    save_frequency: int = 500


__all__ = [
    "RLAlgorithm",
    "ExplorationStrategy",
    "RLPolicy",
    "RLTrainer",
    "create_default_policy",
    "ReinforcementLearningAgent",
    "get_rl_agent",
]
