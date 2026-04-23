#!/usr/bin/env python3

"""
强化学习调度优化器
Reinforcement Learning Scheduling Optimizer

通过历史数据训练策略模型,优化任务调度决策

作者: 小诺·双鱼座
创建时间: 2025-12-14
"""
import pickle
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import numpy as np


class SchedulingAction(Enum):
    """调度动作"""

    ASSIGN_TO_BEST_AGENT = "assign_best"  # 分配给最佳智能体
    ASSIGN_TO_FASTEST = "assign_fastest"  # 分配给最快智能体
    ASSIGN_TO_LEAST_LOADED = "assign_least_loaded"  # 分配给负载最低的智能体
    PARALLEL_EXECUTION = "parallel"  # 并行执行
    QUEUE_HIGH_PRIORITY = "queue_high"  # 高优先级队列
    DEFER_EXECUTION = "defer"  # 延迟执行


@dataclass
class TaskState:
    """任务状态(用于RL)"""

    task_type: str
    priority: int
    estimated_duration: float
    resource_requirements: dict[str, float]
    dependencies_count: int
    deadline_hours: float
    value_score: float
    is_rush: bool


@dataclass
class SystemState:
    """系统状态(用于RL)"""

    agent_loads: list[float]
    agent_success_rates: list[float]
    agent_specializations: list[list[str]
    queue_lengths: list[int]
    avg_waiting_time: float
    system_utilization: float
    recent_failure_rate: float
    time_of_day: int


class RLExperience:
    """强化学习经验"""

    def __init__(self, state, action, reward, next_state, done):
        self.state = state
        self.action = action
        self.reward = reward
        self.next_state = next_state
        self.done = done


class RLSchedulingOptimizer:
    """强化学习调度优化器"""

    def __init__(self):
        self.name = "小诺强化学习调度优化器"
        self.version = "1.0.0"

        # 超参数
        self.learning_rate = 0.001
        self.gamma = 0.95  # 折扣因子
        self.epsilon = 0.1  # 探索率
        self.memory_size = 10000
        self.batch_size = 32
        self.target_update_freq = 100

        # 经验回放池
        self.experience_buffer = deque(maxlen=self.memory_size)

        # Q网络(简化版本,实际应用中应使用深度神经网络)
        self.q_table = defaultdict(lambda: defaultdict(float))
        self.target_q_table = defaultdict(lambda: defaultdict(float))

        # 状态编码器
        self.state_encoder = StateEncoder()

        # 奖励函数配置
        self.reward_weights = {
            "completion_time": 0.3,
            "success_rate": 0.3,
            "resource_efficiency": 0.2,
            "deadline_met": 0.15,
            "load_balance": 0.05,
        }

        # 训练统计
        self.training_stats = {
            "episodes": 0,
            "total_rewards": 0,
            "avg_reward": 0,
            "epsilon_decay": 0.995,
            "min_epsilon": 0.01,
        }

        # 性能历史
        self.performance_history = deque(maxlen=1000)

        print(f"🧠 {self.name} 初始化完成")

    def optimize_task_priority(
        self, tasks: list[dict[str, Any], current_system_state: SystemState
    ) -> list[int]:
        """优化任务队列优先级"""
        priorities = []

        for task in tasks:
            # 编码任务状态
            task_state = self._encode_task(task)
            state_vector = self.state_encoder.encode(task_state, current_system_state)

            # 获取Q值
            action_values = self._get_q_values(state_vector)

            # 根据最佳动作计算优先级分数
            best_action = max(action_values.items(), key=lambda x: x[1])[0]
            priority_score = self._calculate_priority_score(
                task, best_action, action_values[best_action]
            )

            priorities.append(priority_score)

        # 返回排序后的索引
        return sorted(range(len(priorities)), key=lambda i: priorities[i], reverse=True)

    def select_scheduling_action(
        self,
        task: dict[str, Any],        available_agents: list[dict[str, Any],        system_state: SystemState,
    ) -> tuple[str, str]:
        """选择调度动作(动作, 目标智能体)"""
        # ε-贪婪策略
        if np.random.random() < self.epsilon:
            # 探索:随机选择
            action = np.random.choice([a.value for a in SchedulingAction])
        else:
            # 利用:选择最佳动作
            task_state = self._encode_task(task)
            state_vector = self.state_encoder.encode(task_state, system_state)
            action_values = self._get_q_values(state_vector)
            action = max(action_values.items(), key=lambda x: x[1])[0]

        # 根据动作选择具体智能体
        agent_id = self._select_agent_for_action(action, task, available_agents, system_state)

        return action, agent_id

    def store_experience(
        self, state: np.ndarray, action: str, reward: float, next_state: np.ndarray, done: bool
    ):
        """存储经验"""
        experience = RLExperience(state, action, reward, next_state, done)
        self.experience_buffer.append(experience)

    def train(self) -> Any:
        """训练模型"""
        if len(self.experience_buffer) < self.batch_size:
            return

        # 随机采样批次
        batch = np.random.choice(list(self.experience_buffer), self.batch_size, replace=False)

        total_loss = 0

        for exp in batch:
            # 当前Q值
            current_q = self.q_table[self._state_to_key(exp.state)][exp.action]

            # 计算目标Q值
            if exp.done:
                target_q = exp.reward
            else:
                next_state_key = self._state_to_key(exp.next_state)
                next_q_values = self.target_q_table[next_state_key]
                max_next_q = max(next_q_values.values()) if next_q_values else 0
                target_q = exp.reward + self.gamma * max_next_q

            # 更新Q值
            td_error = target_q - current_q
            self.q_table[self._state_to_key(exp.state)][exp.action] += self.learning_rate * td_error
            total_loss += abs(td_error)

        # 定期更新目标网络
        self.training_stats["episodes"] += 1
        if self.training_stats["episodes"] % self.target_update_freq == 0:
            self.target_q_table = self.q_table.copy()

        # 衰减探索率
        self.epsilon = max(
            self.training_stats["min_epsilon"], self.epsilon * self.training_stats["epsilon_decay"]
        )

        return total_loss / self.batch_size

    def calculate_reward(
        self,
        task: dict[str, Any],        action: str,
        result: dict[str, Any],        start_time: float,
        end_time: float,
    ) -> float:
        """计算奖励"""
        reward = 0

        # 1. 完成时间奖励
        actual_duration = end_time - start_time
        estimated_duration = task.get("estimated_duration", 300)
        time_efficiency = min(1.0, estimated_duration / actual_duration)
        reward += self.reward_weights["completion_time"] * time_efficiency

        # 2. 成功率奖励
        success = result.get("success", False)
        if success:
            reward += self.reward_weights["success_rate"]
        else:
            reward -= self.reward_weights["success_rate"] * 2  # 失败惩罚

        # 3. 资源效率奖励
        resource_usage = result.get("resource_usage", {})
        efficiency_score = self._calculate_resource_efficiency(resource_usage)
        reward += self.reward_weights["resource_efficiency"] * efficiency_score

        # 4. 截止时间奖励
        if "deadline" in task:
            deadline_met = end_time <= task["deadline"]
            if deadline_met:
                reward += self.reward_weights["deadline_met"]
            else:
                reward -= self.reward_weights["deadline_met"] * (end_time - task["deadline"]) / 3600

        # 5. 负载均衡奖励
        if "load_balance_score" in result:
            reward += self.reward_weights["load_balance"] * result["load_balance_score"]

        # 记录性能
        self.performance_history.append(
            {
                "timestamp": datetime.now(),
                "reward": reward,
                "duration": actual_duration,
                "success": success,
            }
        )

        return reward

    def _encode_task(self, task: dict[str, Any]) -> TaskState:
        """编码任务状态"""
        return TaskState(
            task_type=task.get("type", "unknown"),
            priority=task.get("priority", 1),
            estimated_duration=task.get("estimated_duration", 300),
            resource_requirements=task.get("resource_requirements", {}),
            dependencies_count=len(task.get("dependencies", [])),
            deadline_hours=task.get("deadline_hours", 24),
            value_score=task.get("value_score", 1.0),
            is_rush=task.get("priority", 1) >= 3,
        )

    def _get_q_values(self, state_vector: np.ndarray) -> dict[str, float]:
        """获取状态-动作值"""
        state_key = self._state_to_key(state_vector)
        return dict(self.q_table[state_key])

    def _state_to_key(self, state: np.ndarray) -> str:
        """将状态向量转换为键"""
        # 简化:将连续状态离散化
        discretized = tuple(np.round(state * 10).astype(int))
        return str(discretized)

    def _calculate_priority_score(self, task: dict[str, Any], action: str, q_value: float) -> float:
        """计算优先级分数"""
        base_priority = task.get("priority", 1) * 10
        value_score = task.get("value_score", 1.0) * 20

        # 根据动作调整
        if action == SchedulingAction.QUEUE_HIGH_PRIORITY.value:
            action_bonus = 30
        elif action == SchedulingAction.ASSIGN_TO_FASTEST.value:
            action_bonus = 20
        else:
            action_bonus = 10

        # 紧急任务加分
        urgency_bonus = 25 if task.get("priority", 1) >= 3 else 0

        return base_priority + value_score + action_bonus + urgency_bonus + q_value

    def _select_agent_for_action(
        self,
        action: str,
        task: dict[str, Any],        agents: list[dict[str, Any],        system_state: SystemState,
    ) -> str:
        """根据动作选择智能体"""
        if not agents:
            return None

        if action == SchedulingAction.ASSIGN_TO_BEST_AGENT.value:
            # 选择成功率最高且能力匹配的智能体
            capable_agents = [a for a in agents if self._can_agent_handle_task(a, task)]
            if capable_agents:
                return max(capable_agents, key=lambda x: x["success_rate"])["id"]

        elif action == SchedulingAction.ASSIGN_TO_FASTEST.value:
            # 选择速度最快的智能体
            capable_agents = [a for a in agents if self._can_agent_handle_task(a, task)]
            if capable_agents:
                return min(capable_agents, key=lambda x: x.get("avg_duration", 999))["id"]

        elif action == SchedulingAction.ASSIGN_TO_LEAST_LOADED.value:
            # 选择负载最低的智能体
            return min(agents, key=lambda x: x["current_load"])["id"]

        # 默认:选择第一个可用的智能体
        return agents[0]["id"]

    def _can_agent_handle_task(self, agent: dict[str, Any], task: dict[str, Any]) -> bool:
        """检查智能体是否能处理任务"""
        task_requirements = task.get("required_capabilities", [])
        agent_capabilities = agent.get("capabilities", [])
        return all(req in agent_capabilities for req in task_requirements)

    def _calculate_resource_efficiency(self, resource_usage: dict[str, float]) -> float:
        """计算资源效率分数"""
        if not resource_usage:
            return 0.5

        # 计算资源利用率(理想值在0.7-0.9之间)
        cpu_usage = resource_usage.get("cpu", 0)
        memory_usage = resource_usage.get("memory", 0)

        cpu_score = 1.0 - abs(cpu_usage - 0.8) if cpu_usage <= 0.8 else cpu_usage
        memory_score = 1.0 - abs(memory_usage - 0.8) if memory_usage <= 0.8 else memory_usage

        return (cpu_score + memory_score) / 2

    def get_performance_stats(self) -> dict[str, Any]:
        """获取性能统计"""
        if not self.performance_history:
            return {}

        recent_rewards = [p["reward"] for p in list(self.performance_history)[-100:]
        recent_durations = [p["duration"] for p in list(self.performance_history)[-100:]
        recent_success_rate = (
            sum(1 for p in list(self.performance_history)[-100:] if p["success"]) / 100
        )

        return {
            "avg_reward": np.mean(recent_rewards),
            "reward_std": np.std(recent_rewards),
            "avg_duration": np.mean(recent_durations),
            "duration_std": np.std(recent_durations),
            "recent_success_rate": recent_success_rate,
            "epsilon": self.epsilon,
            "training_episodes": self.training_stats["episodes"],
            "experience_buffer_size": len(self.experience_buffer),
        }

    def save_model(self, filepath: str) -> None:
        """保存模型"""
        model_data = {
            "q_table": dict(self.q_table),
            "target_q_table": dict(self.target_q_table),
            "training_stats": self.training_stats,
            "epsilon": self.epsilon,
        }

        with open(filepath, "wb") as f:
            pickle.dump(model_data, f)
        print(f"✅ 模型已保存到: {filepath}")

    def load_model(self, filepath: str) -> Optional[Any]:
        """加载模型"""
        try:
            with open(filepath, "rb") as f:
                model_data = pickle.load(f)

            self.q_table = defaultdict(lambda: defaultdict(float), model_data["q_table"])
            self.target_q_table = defaultdict(
                lambda: defaultdict(float), model_data["target_q_table"]
            )
            self.training_stats = model_data["training_stats"]
            self.epsilon = model_data.get("epsilon", 0.1)

            print(f"✅ 模型已从 {filepath} 加载")
        except FileNotFoundError:
            print(f"⚠️ 模型文件 {filepath} 不存在,使用默认初始化")


class StateEncoder:
    """状态编码器"""

    def __init__(self):
        self.task_types = {
            "patent_application": 0,
            "media_operation": 1,
            "data_analysis": 2,
            "content_creation": 3,
            "legal_review": 4,
            "technical_development": 5,
        }

    def encode(self, task_state: TaskState, system_state: SystemState) -> np.ndarray:
        """编码状态为向量"""
        # 任务特征 (10维)
        task_features = [
            self.task_types.get(task_state.task_type, -1) / 6.0,
            task_state.priority / 3.0,
            task_state.estimated_duration / 3600.0,  # 标准化为小时
            task_state.resource_requirements.get("cpu", 1.0) / 8.0,
            task_state.resource_requirements.get("memory", 2.0) / 16.0,
            task_state.resource_requirements.get("gpu", 0) / 2.0,
            task_state.dependencies_count / 10.0,
            task_state.deadline_hours / 168.0,  # 标准化为周
            task_state.value_score,
            1.0 if task_state.is_rush else 0.0,
        ]

        # 系统特征 (10维)
        system_features = [
            np.mean(system_state.agent_loads) if system_state.agent_loads else 0,
            np.std(system_state.agent_loads) if system_state.agent_loads else 0,
            np.mean(system_state.agent_success_rates) if system_state.agent_success_rates else 0,
            system_state.system_utilization,
            system_state.recent_failure_rate,
            system_state.avg_waiting_time / 3600.0,
            system_state.time_of_day / 24.0,
            sum(system_state.queue_lengths) / 100.0,
            max(system_state.queue_lengths) / 50.0 if system_state.queue_lengths else 0,
            len(system_state.agent_specializations) / 10.0,
        ]

        # 组合为20维向量
        return np.array(task_features + system_features)


# 导出主类
__all__ = [
    "RLExperience",
    "RLSchedulingOptimizer",
    "SchedulingAction",
    "StateEncoder",
    "SystemState",
    "TaskState",
]

