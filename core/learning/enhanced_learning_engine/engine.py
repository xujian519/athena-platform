#!/usr/bin/env python3
"""
增强学习引擎 - 主引擎
Enhanced Learning Engine - Main Engine

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0

基于BaseModule的标准化学习引擎,支持统一接口和学习模型
"""

import asyncio
import logging
from collections import defaultdict, deque
from datetime import datetime
from typing import Any

import numpy as np

from core.base_module import BaseModule
from .strategies import LearningStrategies
from .types import (
    AdaptationMode,
    Experience,
    LearningMetrics,
    LearningResult,
    LearningStrategy,
)

logger = logging.getLogger(__name__)


class EnhancedLearningEngine(BaseModule):
    """
    增强学习引擎

    继承BaseModule,提供标准化的学习接口
    """

    def __init__(self, agent_id: str, config: dict | None = None):
        """
        初始化增强学习引擎

        Args:
            agent_id: 智能体ID
            config: 配置参数
        """
        # 提取学习引擎专用配置
        learning_config = config or {}
        learning_strategy = learning_config.get("learning_strategy", LearningStrategy.HYBRID)
        adaptation_mode = learning_config.get("adaptation_mode", AdaptationMode.REACTIVE)
        max_experiences = learning_config.get("max_experiences", 10000)
        learning_rate = learning_config.get("learning_rate", 0.01)
        adaptation_threshold = learning_config.get("adaptation_threshold", 0.8)

        # 初始化基类
        super().__init__(agent_id, config)

        # 学习引擎配置
        self.learning_strategy = LearningStrategy(learning_strategy)
        self.adaptation_mode = AdaptationMode(adaptation_mode)
        self.max_experiences = max_experiences
        self.learning_rate = learning_rate
        self.adaptation_threshold = adaptation_threshold

        # 经验存储
        self._experiences: deque[Experience] = deque(maxlen=max_experiences)
        self._experience_index: defaultdict[str, list[str]] = defaultdict(list)
        self._context_patterns: dict[str, Any] = {}

        # 学习模型
        self._models: dict[str, Any] = {}
        self._strategies: LearningStrategies = LearningStrategies(self)
        self._adaptations: list[dict[str, Any]] = []

        # 统计信息
        self._metrics = LearningMetrics()
        self._performance_history: deque[float] = deque(maxlen=1000)

        # 学习状态
        self._learning_active = False
        self._adaptation_scheduled = False

        # 初始化组件
        self._initialize_components()

    def _initialize_components(self) -> Any:
        """初始化学习组件"""
        # 初始化基础模型
        self._initialize_models()

    def _initialize_models(self) -> Any:
        """初始化学习模型"""
        # 简单的统计模型
        self._models = {
            "reward_tracker": defaultdict(float),
            "action_success": defaultdict(lambda: {"success": 0, "total": 0}),
            "context_patterns": defaultdict(int),
            "performance_tracker": {"recent": deque(maxlen=100), "long_term": deque(maxlen=1000)},
        }

    async def _on_initialize(self) -> bool:
        """初始化逻辑"""
        try:
            # 加载历史数据
            await self._load_historical_data()

            self.logger.info(f"✅ 增强学习引擎初始化成功,策略: {self.learning_strategy.value}")
            return True

        except Exception as e:
            self.logger.error(f"❌ 增强学习引擎初始化失败: {e}")
            return False

    async def _on_start(self) -> bool:
        """启动逻辑"""
        try:
            self.logger.info("🚀 启动增强学习引擎")

            # 启动学习进程
            self._learning_active = True
            asyncio.create_task(self._learning_loop())

            # 启动适应调度器
            if self.adaptation_mode == AdaptationMode.SCHEDULED:
                asyncio.create_task(self._adaptation_scheduler())

            return True

        except Exception as e:
            self.logger.error(f"❌ 增强学习引擎启动失败: {e}")
            return False

    async def _on_stop(self) -> bool:
        """停止逻辑"""
        try:
            self.logger.info("🛑 停止增强学习引擎")

            # 停止学习进程
            self._learning_active = False

            # 保存学习数据
            await self._save_learning_data()

            return True

        except Exception as e:
            self.logger.error(f"❌ 增强学习引擎停止失败: {e}")
            return False

    async def _on_shutdown(self) -> bool:
        """关闭逻辑"""
        try:
            # 清理资源
            self._experiences.clear()
            self._experience_index.clear()
            self._models.clear()
            self._strategies = {}

            self.logger.info("✅ 增强学习引擎已关闭")
            return True

        except Exception as e:
            self.logger.error(f"❌ 增强学习引擎关闭失败: {e}")
            return False

    async def _on_health_check(self) -> bool:
        """健康检查"""
        try:
            # 检查学习状态
            healthy = (
                len(self._experiences) > 0  # 有经验数据
                or self._learning_active  # 学习进程活跃
                or self._metrics.total_experiences > 0  # 或有历史学习记录
            )

            self.logger.debug(
                f"健康检查: 经验数={len(self._experiences)}, 学习活跃={self._learning_active}"
            )

            return healthy

        except Exception as e:
            self.logger.error(f"❌ 健康检查失败: {e}")
            return False

    async def process_experience(
        self, experience_data: dict[str, Any] | Experience
    ) -> LearningResult:
        """
        处理经验数据

        Args:
            experience_data: 经验数据

        Returns:
            LearningResult: 学习结果
        """
        try:
            # 转换经验数据
            if isinstance(experience_data, dict):
                experience = Experience(
                    id=str(len(self._experiences)),
                    task=experience_data.get("task", ""),
                    action=experience_data.get("action", ""),
                    result=experience_data.get("result"),
                    reward=float(experience_data.get("reward", 0.0)),
                    context=experience_data.get("context", {}),
                    metadata=experience_data.get("metadata", {}),
                )
            else:
                experience = experience_data

            # 存储经验
            await self._store_experience(experience)

            # 执行学习
            learning_result = await self.execute_with_metrics(
                "learning_process", self._perform_learning, experience
            )

            # 更新指标
            self._update_metrics(experience, learning_result)

            self.logger.info(f"🧠 处理经验完成: {experience.task} (奖励: {experience.reward:.2f})")

            return learning_result

        except Exception as e:
            self.logger.error(f"❌ 处理经验失败: {e}")
            return LearningResult(
                success=False,
                strategy_used=self.learning_strategy,
                performance_score=0.0,
                adaptation_applied=False,
                insights=[f"学习失败: {e!s}"],
            )

    async def _store_experience(self, experience: Experience) -> None:
        """存储经验"""
        # 添加到经验队列
        self._experiences.append(experience)

        # 更新索引
        context_key = self._generate_context_key(experience.context)
        self._experience_index[context_key].append(experience.id)

        # 更新上下文模式
        self._update_context_patterns(context_key)

        # 限制索引大小
        if len(self._experience_index[context_key]) > 100:
            self._experience_index[context_key] = self._experience_index[context_key][-100:]

    def _generate_context_key(self, context: dict[str, Any]) -> str:
        """生成上下文键"""
        # 提取关键特征
        key_features = []
        for key in sorted(context.keys()):
            if key in ["task_type", "domain", "difficulty", "environment"]:
                key_features.append(f"{key}:{context[key]}")

        return "|".join(key_features) if key_features else "default"

    def _update_context_patterns(self, context_key: str) -> Any:
        """更新上下文模式"""
        self._models["context_patterns"][context_key] += 1

    async def _perform_learning(self, experience: Experience) -> LearningResult:
        """执行学习"""
        # 选择学习策略
        strategy_func = self._strategies.get_strategy(self.learning_strategy)

        # 执行学习
        insights, performance_score = await strategy_func(experience)

        # 检查是否需要适应
        adaptation_applied = False
        if self._should_adapt(performance_score):
            adaptation_applied = await self._apply_adaptation(experience, insights)

        # 生成推荐
        recommendations = self._generate_recommendations(experience, insights, performance_score)

        return LearningResult(
            success=True,
            strategy_used=self.learning_strategy,
            performance_score=performance_score,
            adaptation_applied=adaptation_applied,
            insights=insights,
            recommendations=recommendations,
            metrics=self._get_current_metrics(),
        )

    async def _find_similar_experiences(
        self, context: dict[str, Any], limit: int = 5
    ) -> list[Experience]:
        """查找相似经验"""
        context_key = self._generate_context_key(context)

        if context_key in self._experience_index:
            experience_ids = self._experience_index[context_key]
            experiences = [exp for exp in self._experiences if exp.id in experience_ids]
            return experiences[-limit:]  # 返回最新的几个经验

        return []

    def _should_adapt(self, performance_score: float) -> bool:
        """判断是否需要适应"""
        return (
            performance_score < self.adaptation_threshold
            or self.adaptation_mode == AdaptationMode.PROACTIVE
            or self.adaptation_mode == AdaptationMode.ON_DEMAND
        )

    async def _apply_adaptation(self, experience: Experience, insights: list[str]) -> bool:
        """应用适应"""
        try:
            # 简单的适应策略
            if experience.reward < 0:
                # 降低学习率
                self.learning_rate *= 0.9
                self.logger.info(f"🔧 降低学习率至 {self.learning_rate:.4f}")

            elif experience.reward > 0.8:
                # 提高学习率
                self.learning_rate = min(0.1, self.learning_rate * 1.1)
                self.logger.info(f"🔧 提高学习率至 {self.learning_rate:.4f}")

            # 记录适应
            self._adaptations.append(
                {
                    "timestamp": datetime.now(),
                    "experience_id": experience.id,
                    "reason": "performance_based",
                    "action": "adjust_learning_rate",
                }
            )

            self._metrics.adaptation_count += 1

            return True

        except Exception as e:
            self.logger.error(f"❌ 应用适应失败: {e}")
            return False

    def _generate_recommendations(
        self, experience: Experience, insights: list[str], performance_score: float
    ) -> list[str]:
        """生成推荐"""
        recommendations = []

        if performance_score < 0.3:
            recommendations.append("考虑尝试不同的动作策略")
            recommendations.append("分析失败原因并调整方法")

        elif performance_score > 0.8:
            recommendations.append("当前策略有效,继续保持")
            recommendations.append("考虑将成功经验应用到类似任务")

        # 基于上下文的推荐
        if "difficulty" in experience.context:
            difficulty = experience.context["difficulty"]
            if difficulty == "hard" and performance_score < 0.5:
                recommendations.append("考虑将困难任务分解为更小的子任务")

        return recommendations

    def _get_current_metrics(self) -> dict[str, float]:
        """获取当前指标"""
        return {
            "total_experiences": self._metrics.total_experiences,
            "success_rate": self._metrics.successful_experiences
            / max(self._metrics.total_experiences, 1),
            "average_reward": self._metrics.average_reward,
            "learning_rate": self.learning_rate,
            "adaptation_count": self._metrics.adaptation_count,
        }

    def _update_metrics(self, experience: Experience, learning_result: LearningResult) -> Any:
        """更新学习指标"""
        self._metrics.total_experiences += 1

        if experience.reward > 0:
            self._metrics.successful_experiences += 1

        # 更新平均奖励
        total_reward = (
            self._metrics.average_reward * (self._metrics.total_experiences - 1) + experience.reward
        )
        self._metrics.average_reward = total_reward / self._metrics.total_experiences

        # 更新学习率
        self._metrics.learning_rate = self.learning_rate

        # 记录性能历史
        self._performance_history.append(learning_result.performance_score)

        self._metrics.last_update = datetime.now()

    async def get_strategy(self, task: str) -> dict[str, Any]:
        """
        获取任务策略

        Args:
            task: 任务名称

        Returns:
            dict[str, Any]: 策略信息
        """
        try:
            # 查找相关经验
            relevant_experiences = [
                exp for exp in self._experiences if exp.task == task or task in exp.task
            ]

            if not relevant_experiences:
                return {
                    "task": task,
                    "strategy": "exploration",
                    "confidence": 0.0,
                    "recommended_actions": [],
                    "reason": "没有相关经验,建议探索",
                }

            # 分析最佳动作
            action_performance: defaultdict[str, list[float]] = defaultdict(list)
            for exp in relevant_experiences:
                action_performance[exp.action].append(exp.reward)

            # 选择最佳动作
            best_action = None
            best_avg_reward = float("-inf")

            for action, rewards in action_performance.items():
                avg_reward = np.mean(rewards)
                if avg_reward > best_avg_reward:
                    best_avg_reward = avg_reward
                    best_action = action

            # 计算置信度
            confidence = min(1.0, len(relevant_experiences) / 10.0)

            # 生成推荐动作
            recommended_actions = []
            for action, rewards in action_performance.items():
                avg_reward = np.mean(rewards)
                recommended_actions.append(
                    {
                        "action": action,
                        "average_reward": avg_reward,
                        "success_rate": sum(1 for r in rewards if r > 0) / len(rewards),
                    }
                )

            # 按平均奖励排序
            recommended_actions.sort(key=lambda x: x["average_reward"], reverse=True)

            return {
                "task": task,
                "strategy": "exploitation" if confidence > 0.5 else "exploration",
                "confidence": confidence,
                "best_action": best_action,
                "best_average_reward": best_avg_reward,
                "recommended_actions": recommended_actions[:5],  # 返回前5个推荐
                "total_experiences": len(relevant_experiences),
                "reason": f"基于 {len(relevant_experiences)} 个相关经验的策略",
            }

        except Exception as e:
            self.logger.error(f"❌ 获取策略失败: {e}")
            return {"task": task, "strategy": "error", "confidence": 0.0, "error": str(e)}

    async def get_statistics(self) -> dict[str, Any]:
        """
        获取学习统计信息

        Returns:
            dict[str, Any]: 统计信息
        """
        try:
            # 计算性能趋势
            if len(self._performance_history) >= 10:
                recent = np.mean(list(self._performance_history)[-10:])
                older = (
                    np.mean(list(self._performance_history)[-20:-10])
                    if len(self._performance_history) >= 20
                    else recent
                )
                trend = "improving" if recent > older else "declining"
            else:
                trend = "insufficient_data"

            # 获取最活跃的上下文
            top_contexts = sorted(
                self._models["context_patterns"].items(), key=lambda x: x[1], reverse=True
            )[:5]

            return {
                "agent_id": self.agent_id,
                "learning_strategy": self.learning_strategy.value,
                "adaptation_mode": self.adaptation_mode.value,
                "metrics": {
                    "total_experiences": self._metrics.total_experiences,
                    "successful_experiences": self._metrics.successful_experiences,
                    "success_rate": self._metrics.successful_experiences
                    / max(self._metrics.total_experiences, 1),
                    "average_reward": self._metrics.average_reward,
                    "learning_rate": self._metrics.learning_rate,
                    "adaptation_count": self._metrics.adaptation_count,
                    "pattern_discovered": len(self._models["context_patterns"]),
                },
                "performance_trend": trend,
                "top_contexts": [{"context": ctx, "count": count} for ctx, count in top_contexts],
                "adaptation_history": self._adaptations[-10:],  # 最近10次适应
                "last_update": self._metrics.last_update.isoformat(),
            }

        except Exception as e:
            self.logger.error(f"❌ 获取统计信息失败: {e}")
            return {"error": str(e)}

    async def adapt_strategy(self, current_performance: float, target_performance: float) -> bool:
        """
        适应策略调整

        Args:
            current_performance: 当前性能
            target_performance: 目标性能

        Returns:
            bool: 调整是否成功
        """
        try:
            performance_gap = target_performance - current_performance

            if performance_gap > 0.2:
                # 性能差距大,需要显著调整
                self.learning_rate = min(0.1, self.learning_rate * 1.5)
                self.adaptation_threshold = max(0.5, self.adaptation_threshold - 0.1)
                self.logger.info(
                    f"🔧 大幅调整学习策略: 学习率={self.learning_rate:.4f}, 适应阈值={self.adaptation_threshold:.2f}"
                )

            elif performance_gap > 0.1:
                # 性能差距中等,适度调整
                self.learning_rate = min(0.05, self.learning_rate * 1.2)
                self.logger.info(f"🔧 适度调整学习策略: 学习率={self.learning_rate:.4f}")

            else:
                # 性能差距小,微调
                self.learning_rate *= 1.05
                self.logger.info(f"🔧 微调学习策略: 学习率={self.learning_rate:.4f}")

            # 记录适应
            self._adaptations.append(
                {
                    "timestamp": datetime.now(),
                    "type": "strategy_adaptation",
                    "performance_gap": performance_gap,
                    "new_learning_rate": self.learning_rate,
                    "new_adaptation_threshold": getattr(self, "adaptation_threshold", None),
                }
            )

            return True

        except Exception as e:
            self.logger.error(f"❌ 策略适应失败: {e}")
            return False

    async def _learning_loop(self) -> None:
        """学习循环"""
        while self._learning_active:
            try:
                # 定期进行模式发现和学习
                await self._periodic_learning()

                # 休眠一段时间
                await asyncio.sleep(60)  # 每分钟执行一次

            except Exception as e:
                self.logger.error(f"❌ 学习循环异常: {e}")
                await asyncio.sleep(5)

    async def _adaptation_scheduler(self) -> None:
        """适应调度器"""
        while self._learning_active:
            try:
                # 定期进行适应
                await self._periodic_adaptation()

                # 休眠一段时间
                await asyncio.sleep(300)  # 每5分钟执行一次

            except Exception as e:
                self.logger.error(f"❌ 适应调度器异常: {e}")
                await asyncio.sleep(30)

    async def _periodic_learning(self) -> None:
        """定期学习"""
        try:
            # 如果有足够的经验,进行批量学习
            if len(self._experiences) >= 10:
                # 取最近的10个经验进行学习
                recent_experiences = list(self._experiences)[-10:]

                for exp in recent_experiences:
                    await self._perform_learning(exp)

                self.logger.debug("🧠 完成定期批量学习")

        except Exception as e:
            self.logger.error(f"❌ 定期学习失败: {e}")

    async def _periodic_adaptation(self) -> None:
        """定期适应"""
        try:
            # 检查平均性能
            if len(self._performance_history) >= 10:
                recent_performance = np.mean(list(self._performance_history)[-10:])

                if recent_performance < self.adaptation_threshold:
                    # 应用适应
                    dummy_exp = Experience(
                        id="periodic",
                        task="periodic_adaptation",
                        action="adapt",
                        result=None,
                        reward=float(recent_performance),  # type: ignore
                        context={"type": "periodic"},
                    )
                    await self._apply_adaptation(dummy_exp, ["定期性能检查"])

                    self.logger.debug("🔧 完成定期适应调整")

        except Exception as e:
            self.logger.error(f"❌ 定期适应失败: {e}")

    async def _load_historical_data(self) -> None:
        """加载历史数据"""
        try:
            # 这里可以实现从持久化存储加载数据
            # 目前只是占位符
            pass

        except Exception as e:
            self.logger.error(f"❌ 加载历史数据失败: {e}")

    async def _save_learning_data(self) -> None:
        """保存学习数据"""
        try:
            # 这里可以实现数据持久化
            # 目前只是占位符
            pass

        except Exception as e:
            self.logger.error(f"❌ 保存学习数据失败: {e}")


__all__ = ["EnhancedLearningEngine"]
