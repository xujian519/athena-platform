#!/usr/bin/env python3
from __future__ import annotations
"""
增强学习引擎 - 学习策略
Enhanced Learning Engine - Learning Strategies

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0
"""

import logging

import numpy as np

from .types import Experience, LearningStrategy

logger = logging.getLogger(__name__)


class LearningStrategies:
    """学习策略集合"""

    def __init__(self, engine):
        """初始化学习策略

        Args:
            engine: 增强学习引擎实例
        """
        self.engine = engine
        self._strategies = {
            LearningStrategy.SUPERVISED: self._supervised_learning,
            LearningStrategy.REINFORCEMENT: self._reinforcement_learning,
            LearningStrategy.UNSUPERVISED: self._unsupervised_learning,
            LearningStrategy.TRANSFER: self._transfer_learning,
            LearningStrategy.HYBRID: self._hybrid_learning,
        }

    def get_strategy(self, strategy: LearningStrategy):
        """获取指定的学习策略"""
        return self._strategies.get(strategy, self._hybrid_learning)

    async def _supervised_learning(self, experience: Experience) -> tuple[list[str], float]:
        """监督学习"""
        insights = []
        performance_score = 0.0

        try:
            # 更新动作成功率
            action_key = f"{experience.task}:{experience.action}"
            self.engine._models["action_success"][action_key]["total"] += 1
            if experience.reward > 0:
                self.engine._models["action_success"][action_key]["success"] += 1

            # 计算成功率
            success_rate = (
                self.engine._models["action_success"][action_key]["success"]
                / self.engine._models["action_success"][action_key]["total"]
            )

            # 生成洞察
            if success_rate > 0.8:
                insights.append(
                    f"动作 '{experience.action}' 在任务 '{experience.task}' 中表现良好 (成功率: {success_rate:.2f})"
                )
            elif success_rate < 0.3:
                insights.append(
                    f"动作 '{experience.action}' 在任务 '{experience.task}' 中表现不佳 (成功率: {success_rate:.2f})"
                )

            performance_score = success_rate

        except Exception as e:
            self.engine.logger.error(f"❌ 监督学习失败: {e}")
            insights.append(f"监督学习失败: {e!s}")

        return insights, performance_score

    async def _reinforcement_learning(self, experience: Experience) -> tuple[list[str], float]:
        """强化学习"""
        insights = []
        performance_score = 0.0

        try:
            # 更新奖励跟踪
            action_key = f"{experience.task}:{experience.action}"
            current_reward = self.engine._models["reward_tracker"][action_key]
            new_reward = (
                current_reward * (1 - self.engine.learning_rate) + experience.reward * self.engine.learning_rate
            )
            self.engine._models["reward_tracker"][action_key] = new_reward

            # 生成洞察
            if new_reward > current_reward:
                insights.append(
                    f"动作 '{experience.action}' 在任务 '{experience.task}' 中的奖励提升 ({current_reward:.2f} → {new_reward:.2f})"
                )
            else:
                insights.append(
                    f"动作 '{experience.action}' 在任务 '{experience.task}' 中的奖励下降 ({current_reward:.2f} → {new_reward:.2f})"
                )

            performance_score = max(0.0, new_reward)

        except Exception as e:
            self.engine.logger.error(f"❌ 强化学习失败: {e}")
            insights.append(f"强化学习失败: {e!s}")

        return insights, performance_score

    async def _unsupervised_learning(self, experience: Experience) -> tuple[list[str], float]:
        """无监督学习"""
        insights = []
        performance_score = 0.0

        try:
            # 简单的模式检测
            context_key = self.engine._generate_context_key(experience.context)
            pattern_count = self.engine._models["context_patterns"][context_key]

            # 生成洞察
            if pattern_count % 10 == 0:  # 每10次经验生成一次洞察
                insights.append(f"上下文模式 '{context_key}' 出现了 {pattern_count} 次")

            # 计算新颖性分数
            novelty_score = 1.0 / (1.0 + pattern_count)
            performance_score = novelty_score

            if novelty_score > 0.8:
                insights.append(f"发现了新的上下文模式: {context_key}")

        except Exception as e:
            self.engine.logger.error(f"❌ 无监督学习失败: {e}")
            insights.append(f"无监督学习失败: {e!s}")

        return insights, performance_score

    async def _transfer_learning(self, experience: Experience) -> tuple[list[str], float]:
        """迁移学习"""
        insights = []
        performance_score = 0.0

        try:
            # 查找相似经验
            similar_experiences = await self.engine._find_similar_experiences(experience.context)

            if similar_experiences:
                # 计算平均奖励
                avg_reward = sum(exp.reward for exp in similar_experiences) / len(
                    similar_experiences
                )

                # 比较当前奖励与相似经验
                if experience.reward > avg_reward:
                    insights.append(
                        f"当前表现优于相似历史经验 ({experience.reward:.2f} > {avg_reward:.2f})"
                    )
                else:
                    insights.append(
                        f"当前表现不如相似历史经验 ({experience.reward:.2f} < {avg_reward:.2f})"
                    )

                performance_score = min(1.0, experience.reward / max(avg_reward, 0.1))
            else:
                insights.append("未找到相似历史经验,这是新的学习领域")
                performance_score = 0.5

        except Exception as e:
            self.engine.logger.error(f"❌ 迁移学习失败: {e}")
            insights.append(f"迁移学习失败: {e!s}")

        return insights, performance_score

    async def _hybrid_learning(self, experience: Experience) -> tuple[list[str], float]:
        """混合学习"""
        insights = []
        performance_scores = []

        # 执行多种学习策略
        strategies = [
            (self._supervised_learning, "监督学习"),
            (self._reinforcement_learning, "强化学习"),
            (self._unsupervised_learning, "无监督学习"),
            (self._transfer_learning, "迁移学习"),
        ]

        for strategy_func, strategy_name in strategies:
            try:
                strategy_insights, strategy_score = await strategy_func(experience)
                insights.extend([f"[{strategy_name}] {insight}" for insight in strategy_insights])
                performance_scores.append(strategy_score)
            except Exception as e:
                insights.append(f"[{strategy_name}] 学习失败: {e!s}")
                performance_scores.append(0.0)

        # 综合性能分数
        performance_score = np.mean(performance_scores) if performance_scores else 0.0

        # 添加混合学习洞察
        insights.append(f"混合学习综合性能分数: {performance_score:.2f}")

        return insights, float(performance_score)  # type: ignore


__all__ = ["LearningStrategies"]
