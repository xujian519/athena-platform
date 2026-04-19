#!/usr/bin/env python3
from __future__ import annotations
"""
RL智能体实现
RL Tool Routing Agent

基于强化学习的工具路由智能体
通过训练优化工具选择策略,目标将工具选择准确率从96%提升到97%
"""

import logging
import random
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

import numpy as np

logger = logging.getLogger(__name__)


class AgentState(Enum):
    """智能体状态"""

    TRAINING = "training"  # 训练中
    EVALUATION = "evaluation"  # 评估中
    DEPLOYED = "deployed"  # 已部署


class ExplorationStrategy(Enum):
    """探索策略"""

    EPSILON_GREEDY = "epsilon_greedy"  # ε-贪婪
    BOLTZMANN = "boltzmann"  # 玻尔兹曼
    UCB = "ucb"  # 上置信界


@dataclass
class TrainingConfig:
    """训练配置"""

    learning_rate: float = 0.001  # 学习率
    gamma: float = 0.99  # 折扣因子
    epsilon_start: float = 1.0  # 初始探索率
    epsilon_end: float = 0.01  # 最终探索率
    epsilon_decay: float = 0.995  # 探索率衰减
    batch_size: int = 32  # 批大小
    memory_size: int = 10000  # 经验回放大小
    target_update_freq: int = 100  # 目标网络更新频率
    exploration_strategy: ExplorationStrategy = ExplorationStrategy.EPSILON_GREEDY


@dataclass
class TrainingMetrics:
    """训练指标"""

    episode: int = 0
    total_episodes: int = 0
    total_rewards: float = 0.0
    avg_reward: float = 0.0
    loss: float = 0.0
    epsilon: float = 1.0
    success_rate: float = 0.0
    tool_selection_accuracy: float = 0.0
    training_time: float = 0.0


@dataclass
class Transition:
    """经验元组"""

    state: np.ndarray
    action: int
    reward: float
    next_state: np.ndarray
    done: bool


class QNetwork:
    """Q网络(简化版DQN)"""

    def __init__(self, state_size: int, action_size: int, hidden_size: int = 128):
        """
        初始化Q网络

        Args:
            state_size: 状态空间大小
            action_size: 动作空间大小
            hidden_size: 隐藏层大小
        """
        self.state_size = state_size
        self.action_size = action_size
        self.hidden_size = hidden_size

        # 简化的神经网络参数(实际应使用torch/keras)
        self.weights1 = np.random.randn(state_size, hidden_size) * 0.01
        self.bias1 = np.zeros(hidden_size)
        self.weights2 = np.random.randn(hidden_size, action_size) * 0.01
        self.bias2 = np.zeros(action_size)

    def forward(self, state: np.ndarray) -> np.ndarray:
        """前向传播"""
        # 隐藏层
        hidden = np.maximum(0, np.dot(state, self.weights1) + self.bias1)
        # 输出层
        q_values = np.dot(hidden, self.weights2) + self.bias2
        return q_values

    def get_action(self, state: np.ndarray, epsilon: float = 0.0) -> int:
        """
        获取动作(ε-贪婪)

        Args:
            state: 状态
            epsilon: 探索率

        Returns:
            动作索引
        """
        if random.random() < epsilon:
            return random.randint(0, self.action_size - 1)

        q_values = self.forward(state)
        return int(np.argmax(q_values))

    def update(self, state: np.ndarray, target_q: np.ndarray, learning_rate: float):
        """
        更新网络参数

        Args:
            state: 状态
            target_q: 目标Q值
            learning_rate: 学习率
        """
        # 前向传播
        hidden = np.maximum(0, np.dot(state, self.weights1) + self.bias1)
        q_values = np.dot(hidden, self.weights2) + self.bias2

        # 计算梯度
        output_error = q_values - target_q
        hidden_error = np.dot(output_error, self.weights2.T)
        hidden_error[hidden <= 0] = 0  # ReLU梯度

        # 更新权重
        self.weights2 -= learning_rate * np.outer(hidden, output_error)
        self.bias2 -= learning_rate * output_error
        self.weights1 -= learning_rate * np.outer(state, hidden_error)
        self.bias1 -= learning_rate * hidden_error


class ToolRoutingAgent:
    """
    工具路由RL智能体

    核心功能:
    1. DQN算法实现
    2. 经验回放
    3. 目标网络更新
    4. 探索-利用平衡
    """

    def __init__(self, state_size: int, action_size: int, config: TrainingConfig | None = None):
        """
        初始化智能体

        Args:
            state_size: 状态空间大小
            action_size: 动作空间大小
            config: 训练配置
        """
        self.name = "工具路由RL智能体 v1.0"
        self.version = "1.0.0"
        self.state_size = state_size
        self.action_size = action_size
        self.config = config or TrainingConfig()

        # Q网络
        self.q_network = QNetwork(state_size, action_size)
        self.target_network = QNetwork(state_size, action_size)

        # 初始化目标网络
        self._update_target_network()

        # 经验回放缓冲区
        self.memory = deque(maxlen=self.config.memory_size)

        # 训练状态
        self.state = AgentState.TRAINING
        self.epsilon = self.config.epsilon_start
        self.training_step = 0

        # 指标
        self.metrics = TrainingMetrics()

    def select_action(self, state: np.ndarray, explore: bool = True) -> int:
        """
        选择动作

        Args:
            state: 当前状态
            explore: 是否探索

        Returns:
            动作索引
        """
        epsilon = self.epsilon if explore else 0.0
        return self.q_network.get_action(state, epsilon)

    def remember(self, transition: Transition):
        """
        存储经验

        Args:
            transition: 经验元组
        """
        self.memory.append(transition)

    async def train_step(self) -> float:
        """
        执行一步训练

        Returns:
            损失值
        """
        if len(self.memory) < self.config.batch_size:
            return 0.0

        # 采样批次
        transitions = random.sample(list(self.memory), self.config.batch_size)
        states = np.array([t.state for t in transitions])
        actions = np.array([t.action for t in transitions])
        rewards = np.array([t.reward for t in transitions])
        next_states = np.array([t.next_state for t in transitions])
        dones = np.array([t.done for t in transitions])

        # 计算目标Q值
        next_q_values = self.target_network.forward(next_states)
        max_next_q = np.max(next_q_values, axis=1)
        target_q = rewards + (1 - dones.astype(float)) * self.config.gamma * max_next_q

        # 计算当前Q值
        current_q = self.q_network.forward(states)

        # 创建目标(只更新执行的动作)
        target_q_full = current_q.copy()
        for i in range(self.config.batch_size):
            target_q_full[i, actions[i]] = target_q[i]

        # 更新网络
        for i in range(self.config.batch_size):
            self.q_network.update(states[i], target_q_full[i], self.config.learning_rate)

        # 更新目标网络
        self.training_step += 1
        if self.training_step % self.config.target_update_freq == 0:
            self._update_target_network()

        # 衰减探索率
        if self.epsilon > self.config.epsilon_end:
            self.epsilon *= self.config.epsilon_decay

        # 计算损失
        loss = np.mean((current_q - target_q_full) ** 2)
        return loss

    def _update_target_network(self):
        """更新目标网络(软更新)"""
        self.target_network.weights1 = self.q_network.weights1.copy()
        self.target_network.bias1 = self.q_network.bias1.copy()
        self.target_network.weights2 = self.q_network.weights2.copy()
        self.target_network.bias2 = self.q_network.bias2.copy()

    async def train(self, env, num_episodes: int = 1000) -> TrainingMetrics:
        """
        训练智能体

        Args:
            env: 环境
            num_episodes: 训练回合数

        Returns:
            训练指标
        """
        start_time = datetime.now()
        episode_rewards = []
        episode_successes = []
        episode_accuracies = []

        logger.info(f"开始训练: {num_episodes}回合")

        for episode in range(num_episodes):
            state = env.reset()
            episode_reward = 0.0
            done = False
            steps = 0
            correct_actions = 0

            while not done and steps < 100:
                # 选择动作
                action = self.select_action(state, explore=True)

                # 执行动作
                next_state, reward, done, info = await env.step(action)

                # 存储经验
                transition = Transition(
                    state=state, action=action, reward=reward, next_state=next_state, done=done
                )
                self.remember(transition)

                # 训练
                loss = await self.train_step()

                state = next_state
                episode_reward += reward
                steps += 1

                # 统计准确性
                if info.get("correct", False):
                    correct_actions += 1

            # 记录回合指标
            episode_rewards.append(episode_reward)
            episode_successes.append(episode_reward > 0)
            if steps > 0:
                episode_accuracies.append(correct_actions / steps)

            # 更新指标
            self.metrics.episode = episode
            self.metrics.total_episodes = episode + 1
            self.metrics.total_rewards = sum(episode_rewards)
            self.metrics.avg_reward = sum(episode_rewards[-100:]) / min(100, len(episode_rewards))
            self.metrics.loss = loss
            self.metrics.epsilon = self.epsilon
            self.metrics.success_rate = sum(episode_successes[-100:]) / min(
                100, len(episode_successes)
            )
            self.metrics.tool_selection_accuracy = sum(episode_accuracies[-100:]) / min(
                100, len(episode_accuracies)
            )

            # 打印进度
            if (episode + 1) % 100 == 0:
                logger.info(
                    f"回合 {episode + 1}/{num_episodes}, "
                    f"平均奖励: {self.metrics.avg_reward:.2f}, "
                    f"准确率: {self.metrics.tool_selection_accuracy:.2%}, "
                    f"ε: {self.epsilon:.3f}"
                )

        self.metrics.training_time = (datetime.now() - start_time).total_seconds()

        logger.info(f"训练完成! 最终准确率: {self.metrics.tool_selection_accuracy:.2%}")

        return self.metrics

    async def evaluate(self, env, num_episodes: int = 100) -> dict[str, float]:
        """
        评估智能体

        Args:
            env: 环境
            num_episodes: 评估回合数

        Returns:
            评估指标
        """
        self.state = AgentState.EVALUATION

        episode_rewards = []
        episode_successes = []
        all_actions = []
        correct_actions = 0
        total_actions = 0

        for _episode in range(num_episodes):
            state = env.reset()
            episode_reward = 0.0
            done = False

            while not done:
                # 选择动作(不探索)
                action = self.select_action(state, explore=False)
                all_actions.append(action)
                total_actions += 1

                # 执行动作
                next_state, reward, done, info = await env.step(action)

                state = state + next_state
                episode_reward += reward

                if info.get("correct", False):
                    correct_actions += 1

            episode_rewards.append(episode_reward)
            episode_successes.append(episode_reward > 0)

        metrics = {
            "avg_reward": sum(episode_rewards) / len(episode_rewards),
            "success_rate": sum(episode_successes) / len(episode_successes),
            "tool_selection_accuracy": correct_actions / total_actions if total_actions > 0 else 0,
        }

        logger.info(f"评估完成 - 准确率: {metrics['tool_selection_accuracy']:.2%}")

        return metrics

    def get_action_probabilities(self, state: np.ndarray) -> np.ndarray:
        """
        获取动作概率分布

        Args:
            state: 状态

        Returns:
            动作概率
        """
        q_values = self.q_network.forward(state)
        # Softmax
        exp_q = np.exp(q_values - np.max(q_values))
        return exp_q / np.sum(exp_q)

    def save_model(self, filepath: str):
        """保存模型"""
        import pickle

        model_data = {
            "q_network": {
                "weights1": self.q_network.weights1,
                "bias1": self.q_network.bias1,
                "weights2": self.q_network.weights2,
                "bias2": self.q_network.bias2,
            },
            "target_network": {
                "weights1": self.target_network.weights1,
                "bias1": self.target_network.bias1,
                "weights2": self.target_network.weights2,
                "bias2": self.target_network.bias2,
            },
            "metrics": self.metrics,
            "epsilon": self.epsilon,
        }
        with open(filepath, "wb") as f:
            pickle.dump(model_data, f)
        logger.info(f"模型已保存: {filepath}")

    def load_model(self, filepath: str):
        """加载模型"""
        import pickle

        with open(filepath, "rb") as f:
            model_data = pickle.load(f)

        self.q_network.weights1 = model_data["q_network"]["weights1"]
        self.q_network.bias1 = model_data["q_network"]["bias1"]
        self.q_network.weights2 = model_data["q_network"]["weights2"]
        self.q_network.bias2 = model_data["q_network"]["bias2"]

        self.target_network.weights1 = model_data["target_network"]["weights1"]
        self.target_network.bias1 = model_data["target_network"]["bias1"]
        self.target_network.weights2 = model_data["target_network"]["weights2"]
        self.target_network.bias2 = model_data["target_network"]["bias2"]

        self.metrics = model_data["metrics"]
        self.epsilon = model_data["epsilon"]

        logger.info(f"模型已加载: {filepath}")


# 单例实例
_agent_instance: ToolRoutingAgent | None = None


def get_tool_routing_agent(state_size: int = 10, action_size: int = 5) -> ToolRoutingAgent:
    """获取工具路由RL智能体单例"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = ToolRoutingAgent(state_size, action_size)
        logger.info("工具路由RL智能体已初始化")
    return _agent_instance


async def main():
    """测试主函数"""

    # 创建简单的测试环境
    class SimpleEnv:
        def __init__(self):
            self.state_size = 4
            self.action_size = 3
            self.correct_action = 0

        def reset(self):
            self.correct_action = random.randint(0, 2)
            return np.random.randn(self.state_size)

        async def step(self, action):
            reward = 1.0 if action == self.correct_action else -0.1
            done = random.random() < 0.1
            info = {"correct": action == self.correct_action}
            return np.random.randn(self.state_size), reward, done, info

    env = SimpleEnv()
    agent = get_tool_routing_agent(env.state_size, env.action_size)

    print("=== RL智能体训练测试 ===\n")

    # 训练
    print("开始训练...")
    metrics = await agent.train(env, num_episodes=200)

    print("\n=== 训练完成 ===")
    print(f"训练回合: {metrics.total_episodes}")
    print(f"平均奖励: {metrics.avg_reward:.2f}")
    print(f"工具选择准确率: {metrics.tool_selection_accuracy:.2%}")
    print(f"成功率: {metrics.success_rate:.2%}")
    print(f"训练时间: {metrics.training_time:.1f}秒")

    # 评估
    print("\n开始评估...")
    eval_metrics = await agent.evaluate(env, num_episodes=50)
    print(f"评估准确率: {eval_metrics['tool_selection_accuracy']:.2%}")


# 入口点: @async_main装饰器已添加到main函数
