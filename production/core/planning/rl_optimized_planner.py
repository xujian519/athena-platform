#!/usr/bin/env python3
"""
强化学习优化的规划器
RL-Optimized Planner

使用Q-learning算法优化策略选择和参数配置。

核心组件:
1. QNetwork: 神经网络Q函数近似器
2. ExperienceReplay: 经验回放缓冲区
3. RLOptimizedPlanner: 强化学习优化规划器
4. QLearningAgent: Q学习智能体

作者: Athena平台团队
创建时间: 2026-01-20
版本: v1.0.0 "Phase 2"
"""

from __future__ import annotations
import json
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import ComplexityAnalysis, ComplexityLevel, ExecutionPlan, StrategyType, Task

logger = logging.getLogger(__name__)


# ============================================================================
# Q网络 - 简化版本 (不依赖torch)
# ============================================================================


class QNetwork:
    """
    Q网络 - 使用表格型Q-learning

    对于小规模状态空间,使用表格比神经网络更高效。
    状态表示为: (complexity, task_type_hash)
    动作表示为: 策略类型
    """

    def __init__(self, learning_rate: float = 0.1, discount_factor: float = 0.95):
        """
        初始化Q网络

        Args:
            learning_rate: 学习率 (α)
            discount_factor: 折扣因子 (γ)
        """
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor

        # Q表: (state_key, action) -> q_value
        self.q_table: dict[str, dict[str, float]] = {}

        # 默认Q值
        self.default_q_value = 0.0

        logger.info(f"🧠 Q网络初始化完成 (α={learning_rate}, γ={discount_factor})")

    def _get_state_key(self, complexity: str, task_type: str) -> str:
        """生成状态键"""
        return f"{complexity}:{task_type}"

    def get_q_value(self, complexity: str, task_type: str, action: str) -> float:
        """获取Q值"""
        state_key = self._get_state_key(complexity, task_type)

        if state_key not in self.q_table:
            self.q_table[state_key] = {
                StrategyType.REACT.value: self.default_q_value,
                StrategyType.PLANNING.value: self.default_q_value,
                StrategyType.WORKFLOW_REUSE.value: self.default_q_value,
                StrategyType.ADAPTIVE.value: self.default_q_value,
            }

        return self.q_table[state_key].get(action, self.default_q_value)

    def set_q_value(self, complexity: str, task_type: str, action: str, value: float) -> None:
        """设置Q值"""
        state_key = self._get_state_key(complexity, task_type)

        if state_key not in self.q_table:
            self.q_table[state_key] = {
                StrategyType.REACT.value: self.default_q_value,
                StrategyType.PLANNING.value: self.default_q_value,
                StrategyType.WORKFLOW_REUSE.value: self.default_q_value,
                StrategyType.ADAPTIVE.value: self.default_q_value,
            }

        self.q_table[state_key][action] = value

    def update(
        self,
        complexity: str,
        task_type: str,
        action: str,
        reward: float,
        next_complexity: str | None = None,
        next_task_type: str | None = None,
    ) -> float:
        """
        Q-learning更新规则

        Q(s,a) ← Q(s,a) + α[r + γ max_a' Q(s',a') - Q(s,a)]

        Args:
            complexity: 当前复杂度
            task_type: 当前任务类型
            action: 执行的动作
            reward: 获得的奖励
            next_complexity: 下一个状态的复杂度
            next_task_type: 下一个状态的任务类型

        Returns:
            更新后的Q值
        """
        # 当前Q值
        current_q = self.get_q_value(complexity, task_type, action)

        # 计算最大未来Q值
        if next_complexity and next_task_type:
            max_next_q = self._get_max_q_value(next_complexity, next_task_type)
        else:
            max_next_q = 0.0  # 终止状态

        # Q-learning更新
        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * max_next_q - current_q
        )

        # 保存更新后的Q值
        self.set_q_value(complexity, task_type, action, new_q)

        logger.debug(
            f"Q更新: {complexity}/{task_type}/{action} "
            f"{current_q:.3f} → {new_q:.3f} "
            f"(奖励: {reward:.3f})"
        )

        return new_q

    def _get_max_q_value(self, complexity: str, task_type: str) -> float:
        """获取状态的最大Q值"""
        state_key = self._get_state_key(complexity, task_type)

        if state_key not in self.q_table:
            return self.default_q_value

        q_values = self.q_table[state_key].values()
        return max(q_values) if q_values else self.default_q_value

    def get_best_action(self, complexity: str, task_type: str) -> str:
        """获取最佳动作"""
        state_key = self._get_state_key(complexity, task_type)

        if state_key not in self.q_table:
            # 随机选择
            return random.choice(
                [
                    StrategyType.REACT.value,
                    StrategyType.PLANNING.value,
                    StrategyType.WORKFLOW_REUSE.value,
                    StrategyType.ADAPTIVE.value,
                ]
            )

        q_values = self.q_table[state_key]
        max_q = max(q_values.values())

        # 获取所有最大Q值的动作
        best_actions = [action for action, q in q_values.items() if q == max_q]

        # 如果有多个,随机选择一个
        return random.choice(best_actions)

    def save(self, path: str) -> None:
        """保存Q表"""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.q_table, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 Q表已保存到: {path}")

    def load(self, path: str) -> None:
        """加载Q表"""
        if Path(path).exists():
            with open(path, encoding="utf-8") as f:
                self.q_table = json.load(f)
            logger.info(f"📂 Q表已从 {path} 加载")
        else:
            logger.warning(f"⚠️ Q表文件不存在: {path}")


# ============================================================================
# 经验回放缓冲区
# ============================================================================


@dataclass
class Experience:
    """经验样本"""

    complexity: str
    task_type: str
    action: str
    reward: float
    next_complexity: str
    next_task_type: str
    done: bool
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())


class ExperienceReplay:
    """经验回放缓冲区"""

    def __init__(self, capacity: int = 10000):
        """
        初始化经验回放缓冲区

        Args:
            capacity: 缓冲区容量
        """
        self.capacity = capacity
        self.buffer: list[Experience] = []
        self.position = 0

        logger.info(f"📦 经验回放缓冲区初始化完成 (容量: {capacity})")

    def push(
        self,
        complexity: str,
        task_type: str,
        action: str,
        reward: float,
        next_complexity: str | None = None,
        next_task_type: str | None = None,
        done: bool = False,
    ) -> None:
        """添加经验"""
        experience = Experience(
            complexity=complexity,
            task_type=task_type,
            action=action,
            reward=reward,
            next_complexity=next_complexity,
            next_task_type=next_task_type,
            done=done,
        )

        if len(self.buffer) < self.capacity:
            self.buffer.append(experience)
        else:
            self.buffer[self.position] = experience

        self.position = (self.position + 1) % self.capacity

    def sample(self, batch_size: int) -> list[Experience]:
        """随机采样经验"""
        if len(self.buffer) < batch_size:
            return self.buffer.copy()

        return random.sample(self.buffer, batch_size)

    def __len__(self) -> int:
        return len(self.buffer)

    def clear(self) -> None:
        """清空缓冲区"""
        self.buffer.clear()
        self.position = 0


# ============================================================================
# 奖励函数
# ============================================================================


class RewardFunction:
    """奖励函数"""

    def __init__(self):
        # 奖励权重
        self.success_weight = 10.0
        self.time_penalty_weight = -0.1
        self.quality_bonus_weight = 5.0

    def calculate(
        self, success: bool, execution_time: float, quality_score: float, expected_time: float
    ) -> float:
        """
        计算奖励

        奖励组成:
        1. 成功奖励: +10 (成功), -5 (失败)
        2. 时间惩罚: -0.1 * (actual_time / expected_time - 1)  # TODO: 确保除数不为零
        3. 质量奖励: +5 * (quality_score - 0.5)

        Args:
            success: 是否成功
            execution_time: 实际执行时间
            quality_score: 质量分数 (0-1)
            expected_time: 预期执行时间

        Returns:
            奖励值
        """
        # 成功奖励
        success_reward = self.success_weight if success else -5.0

        # 时间惩罚 (相对于预期时间)
        time_ratio = execution_time / expected_time if expected_time > 0 else 1.0
        time_penalty = self.time_penalty_weight * (time_ratio - 1.0)

        # 质量奖励
        quality_bonus = self.quality_bonus_weight * (quality_score - 0.5)

        total_reward = success_reward + time_penalty + quality_bonus

        logger.debug(
            f"🎯 奖励计算: 成功={success}({success_reward:+.1f}), "
            f"时间比={time_ratio:.2f}({time_penalty:+.2f}), "
            f"质量={quality_score:.2f}({quality_bonus:+.2f}) "
            f"→ 总奖励={total_reward:+.2f}"
        )

        return total_reward


# ============================================================================
# Q学习智能体
# ============================================================================


class QLearningAgent:
    """Q学习智能体"""

    def __init__(
        self,
        learning_rate: float = 0.1,
        discount_factor: float = 0.95,
        epsilon: float = 0.1,
        epsilon_decay: float = 0.995,
        epsilon_min: float = 0.01,
    ):
        """
        初始化Q学习智能体

        Args:
            learning_rate: 学习率
            discount_factor: 折扣因子
            epsilon: 探索率
            epsilon_decay: 探索率衰减
            epsilon_min: 最小探索率
        """
        self.q_network = QNetwork(learning_rate, discount_factor)
        self.reward_function = RewardFunction()

        # Epsilon-greedy参数
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min

        # 统计信息
        self.total_episodes = 0
        self.total_steps = 0

        logger.info(
            f"🤖 Q学习智能体初始化完成 "
            f"(ε={epsilon}, 衰减={epsilon_decay}, 最小值={epsilon_min})"
        )

    def select_action(
        self, complexity: str, task_type: str, available_actions: list[str] | None = None
    ) -> str:
        """
        选择动作 (epsilon-greedy策略)

        Args:
            complexity: 任务复杂度
            task_type: 任务类型
            available_actions: 可用动作列表

        Returns:
            选择的动作
        """
        # 默认可用动作
        if available_actions is None:
            available_actions = [
                StrategyType.REACT.value,
                StrategyType.PLANNING.value,
                StrategyType.WORKFLOW_REUSE.value,
                StrategyType.ADAPTIVE.value,
            ]

        # Epsilon-greedy
        if random.random() < self.epsilon:
            # 探索: 随机选择
            action = random.choice(available_actions)
            logger.debug(f"🎲 探索: 随机选择 {action}")
        else:
            # 利用: 选择Q值最大的动作
            action = self.q_network.get_best_action(complexity, task_type)
            logger.debug(f"🎯 利用: 选择最佳动作 {action}")

            # 如果最佳动作不在可用列表中,随机选择
            if action not in available_actions:
                action = random.choice(available_actions)

        return action

    def update(
        self,
        complexity: str,
        task_type: str,
        action: str,
        success: bool,
        execution_time: float,
        quality_score: float,
        expected_time: float,
        next_complexity: str | None = None,
        next_task_type: str | None = None,
    ) -> float:
        """
        更新Q值

        Args:
            complexity: 当前复杂度
            task_type: 当前任务类型
            action: 执行的动作
            success: 是否成功
            execution_time: 执行时间
            quality_score: 质量分数
            expected_time: 预期时间
            next_complexity: 下一个复杂度
            next_task_type: 下一个任务类型

        Returns:
            计算的奖励
        """
        # 计算奖励
        reward = self.reward_function.calculate(
            success=success,
            execution_time=execution_time,
            quality_score=quality_score,
            expected_time=expected_time,
        )

        # 更新Q值
        self.q_network.update(
            complexity=complexity,
            task_type=task_type,
            action=action,
            reward=reward,
            next_complexity=next_complexity,
            next_task_type=next_task_type,
        )

        # 衰减探索率
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

        self.total_steps += 1

        return reward

    def decay_epsilon(self) -> None:
        """手动衰减探索率"""
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        logger.debug(f"📉 探索率衰减至: {self.epsilon:.4f}")

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "total_episodes": self.total_episodes,
            "total_steps": self.total_steps,
            "current_epsilon": self.epsilon,
            "q_table_size": len(self.q_network.q_table),
        }


# ============================================================================
# RL优化规划器
# ============================================================================


class RLOptimizedPlanner:
    """
    强化学习优化的规划器

    使用Q-learning算法优化策略选择,
    结合TaskComplexityAnalyzer进行复杂度分析。

    工作流程:
    1. 分析任务复杂度
    2. 使用Q-learning智能体选择策略
    3. 生成执行计划
    4. 记录经验并更新Q值
    """

    def __init__(
        self,
        learning_rate: float = 0.1,
        discount_factor: float = 0.95,
        epsilon: float = 0.1,
        q_table_path: str | None = None,
    ):
        """
        初始化RL优化规划器

        Args:
            learning_rate: 学习率
            discount_factor: 折扣因子
            epsilon: 初始探索率
            q_table_path: Q表保存路径
        """
        from .task_complexity_analyzer import TaskComplexityAnalyzer

        self.complexity_analyzer = TaskComplexityAnalyzer()
        self.agent = QLearningAgent(
            learning_rate=learning_rate, discount_factor=discount_factor, epsilon=epsilon
        )
        self.replay_buffer = ExperienceReplay(capacity=10000)

        # Q表路径
        self.q_table_path = q_table_path or "data/q_table.json"

        # 尝试加载已保存的Q表
        self._load_q_table()

        # 规划器实例 (懒加载)
        self._planners: dict[StrategyType, Any] = {}

        logger.info("🎮 RL优化规划器初始化完成")

    def _load_q_table(self) -> None:
        """加载Q表"""
        try:
            self.agent.q_network.load(self.q_table_path)
        except Exception as e:
            logger.warning(f"加载Q表失败: {e}")

    def _save_q_table(self) -> None:
        """保存Q表"""
        try:
            import os

            os.makedirs(os.path.dirname(self.q_table_path), exist_ok=True)
            self.agent.q_network.save(self.q_table_path)
        except Exception as e:
            logger.warning(f"保存Q表失败: {e}")

    async def plan(self, task: Task) -> ExecutionPlan:
        """
        为任务生成RL优化的执行计划

        Args:
            task: 任务对象

        Returns:
            ExecutionPlan: 执行计划
        """
        logger.info(f"🎮 开始RL规划: {task.task_id}")

        # 步骤1: 分析任务复杂度
        complexity_analysis = await self.complexity_analyzer.analyze(task)

        logger.info(
            f"📊 复杂度分析: {complexity_analysis.complexity.value} "
            f"(分数: {complexity_analysis.score:.1f})"
        )

        # 步骤2: 使用RL智能体选择策略
        action = self.agent.select_action(
            complexity=complexity_analysis.complexity.value, task_type=task.task_type
        )

        selected_strategy = StrategyType(action)

        logger.info(f"🤖 RL选择策略: {selected_strategy.value} (ε={self.agent.epsilon:.4f})")

        # 步骤3: 生成执行计划
        plan = await self._generate_plan(task, selected_strategy, complexity_analysis)

        # 步骤4: 添加RL元数据
        plan.metadata["rl_optimized"] = True
        plan.metadata["epsilon"] = self.agent.epsilon
        plan.metadata["q_values"] = self._get_q_values(
            complexity_analysis.complexity.value, task.task_type
        )

        # 保存复杂度分析
        plan.metadata["complexity_analysis"] = complexity_analysis.to_dict()

        # 预估执行时间
        plan.estimated_duration = self._estimate_duration(complexity_analysis, selected_strategy)

        logger.info(
            f"✅ RL规划完成: {plan.plan_id} | "
            f"策略: {plan.strategy.value} | "
            f"置信度: {plan.confidence:.2%} | "
            f"预估耗时: {plan.estimated_duration}s"
        )

        return plan

    async def _generate_plan(
        self, task: Task, strategy: StrategyType, complexity_analysis: ComplexityAnalysis
    ) -> ExecutionPlan:
        """生成执行计划"""
        plan = ExecutionPlan(
            task_id=task.task_id, strategy=strategy, confidence=complexity_analysis.confidence
        )

        # 根据策略类型设置元数据
        if strategy == StrategyType.REACT:
            plan.metadata["approach"] = "reactive"
            plan.metadata["max_iterations"] = 10
        elif strategy == StrategyType.PLANNING:
            plan.metadata["approach"] = "explicit_planning"
            estimated_steps = min(complexity_analysis.factors.estimated_steps, 10)
            for i in range(estimated_steps):
                step = {
                    "step_number": i + 1,
                    "name": f"步骤{i + 1}",
                    "description": f"执行第{i + 1}个操作",
                    "status": "pending",
                }
                plan.steps.append(step)
        elif strategy == StrategyType.WORKFLOW_REUSE:
            plan.metadata["approach"] = "workflow_reuse"
        else:  # ADAPTIVE
            plan.metadata["approach"] = "adaptive"
            plan.metadata["adjustment_interval"] = 3

        return plan

    def _get_q_values(self, complexity: str, task_type: str) -> dict[str, float]:
        """获取当前状态的Q值"""
        q_values = {}
        for strategy in StrategyType:
            q_values[strategy.value] = self.agent.q_network.get_q_value(
                complexity, task_type, strategy.value
            )
        return q_values

    def _estimate_duration(self, complexity: ComplexityAnalysis, strategy: StrategyType) -> int:
        """预估执行时间(秒)"""
        base_duration = 30

        # 复杂度倍数
        if complexity.complexity == ComplexityLevel.SIMPLE:
            complexity_multiplier = 1.0
        elif complexity.complexity == ComplexityLevel.MEDIUM:
            complexity_multiplier = 2.0
        else:
            complexity_multiplier = 4.0

        # 策略倍数
        if strategy == StrategyType.REACT:
            strategy_multiplier = 1.0
        elif strategy == StrategyType.PLANNING:
            strategy_multiplier = 0.8
        elif strategy == StrategyType.WORKFLOW_REUSE:
            strategy_multiplier = 0.5
        else:  # ADAPTIVE
            strategy_multiplier = 1.2

        estimated = base_duration * complexity_multiplier * strategy_multiplier

        return int(estimated)

    async def record_performance(
        self,
        task: Task,
        plan: ExecutionPlan,
        success: bool,
        execution_time: float,
        quality_score: float,
    ) -> None:
        """
        记录执行性能并更新Q值

        Args:
            task: 任务对象
            plan: 执行计划
            success: 是否成功
            execution_time: 执行时间
            quality_score: 质量分数
        """
        # 获取复杂度分析
        complexity_analysis = plan.metadata.get("complexity_analysis", {})
        complexity = complexity_analysis.get("complexity", "medium")

        # 计算奖励并更新Q值
        expected_time = float(plan.estimated_duration) if plan.estimated_duration else 30.0

        reward = self.agent.update(
            complexity=complexity,
            task_type=task.task_type,
            action=plan.strategy.value,
            success=success,
            execution_time=execution_time,
            quality_score=quality_score,
            expected_time=expected_time,
        )

        # 添加到经验回放
        self.replay_buffer.push(
            complexity=complexity,
            task_type=task.task_type,
            action=plan.strategy.value,
            reward=reward,
            done=True,
        )

        logger.info(
            f"📊 RL性能记录: {plan.strategy.value} | "
            f"{'✅' if success else '❌'} | "
            f"耗时: {execution_time:.2f}s | "
            f"质量: {quality_score:.2f} | "
            f"奖励: {reward:+.2f} | "
            f"ε: {self.agent.epsilon:.4f}"
        )

        # 定期保存Q表
        if self.agent.total_steps % 10 == 0:
            self._save_q_table()

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        agent_stats = self.agent.get_statistics()

        return {
            **agent_stats,
            "replay_buffer_size": len(self.replay_buffer),
            "q_table_path": self.q_table_path,
        }

    async def train(self, num_episodes: int = 100, batch_size: int = 32) -> dict[str, Any]:
        """
        训练RL模型

        Args:
            num_episodes: 训练回合数
            batch_size: 批次大小

        Returns:
            训练统计信息
        """
        logger.info(f"🏋️ 开始RL训练 ({num_episodes}回合)")

        total_rewards = []

        for episode in range(num_episodes):
            episode_reward = 0.0

            # 模拟一个episode (使用经验回放)
            if len(self.replay_buffer) >= batch_size:
                experiences = self.replay_buffer.sample(batch_size)

                for exp in experiences:
                    # 更新Q值
                    self.agent.q_network.update(
                        complexity=exp.complexity,
                        task_type=exp.task_type,
                        action=exp.action,
                        reward=exp.reward,
                        next_complexity=exp.next_complexity,
                        next_task_type=exp.next_task_type,
                    )

                    episode_reward += exp.reward

            total_rewards.append(episode_reward)

            if (episode + 1) % 10 == 0:
                avg_reward = sum(total_rewards[-10:]) / min(10, len(total_rewards))
                logger.info(
                    f"Episode {episode + 1}/{num_episodes} | "
                    f"平均奖励: {avg_reward:.2f} | "
                    f"ε: {self.agent.epsilon:.4f}"
                )

        # 保存训练后的Q表
        self._save_q_table()

        return {
            "total_episodes": num_episodes,
            "final_epsilon": self.agent.epsilon,
            "average_reward": sum(total_rewards) / len(total_rewards) if total_rewards else 0.0,
        }


# ============================================================================
# 便捷函数
# ============================================================================

# 全局单例
_rl_planner: RLOptimizedPlanner | None = None


def get_rl_optimized_planner() -> RLOptimizedPlanner:
    """获取全局RL优化规划器单例"""
    global _rl_planner
    if _rl_planner is None:
        _rl_planner = RLOptimizedPlanner()
    return _rl_planner


async def plan_with_rl(task: Task) -> ExecutionPlan:
    """
    便捷的RL规划函数

    Args:
        task: 任务对象

    Returns:
        ExecutionPlan: 执行计划

    Example:
        >>> from core.planning.models import Task
        >>> result = await plan_with_rl(
        ...     Task(description="分析专利的新颖性")
        ... )
        >>> print(result.strategy)
        StrategyType.PLANNING
    """
    planner = get_rl_optimized_planner()
    return await planner.plan(task)


__all__ = [
    "ExperienceReplay",
    "QLearningAgent",
    "QNetwork",
    "RLOptimizedPlanner",
    "RewardFunction",
    "get_rl_optimized_planner",
    "plan_with_rl",
]
