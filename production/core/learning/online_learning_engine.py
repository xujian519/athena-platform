#!/usr/bin/env python3
"""
在线学习引擎
Online Learning Engine

基于《Agentic Design Patterns》第9章:Learning and Adaptation

实现智能体的在线学习和自适应能力:
1. 从执行结果中学习
2. 用户反馈适应
3. 经验提取和策略优化
4. 元学习和快速适应

作者: 小诺·双鱼座
版本: v1.0.0 "持续进化"
创建时间: 2025-01-05
"""

from __future__ import annotations
import logging
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class LearningType(Enum):
    """学习类型"""

    FROM_EXECUTION = "from_execution"  # 从执行结果学习
    FROM_FEEDBACK = "from_feedback"  # 从用户反馈学习
    FROM_FAILURE = "from_failure"  # 从失败中学习
    META_LEARNING = "meta_learning"  # 元学习


@dataclass
class LearningExperience:
    """学习经验"""

    experience_id: str
    learning_type: LearningType
    task_context: dict[str, Any]
    action_taken: dict[str, Any]
    result: dict[str, Any]
    success: bool
    reward: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    lessons_learned: list[str] = field(default_factory=list)
    strategy_updates: dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyProfile:
    """策略配置文件"""

    strategy_id: str
    name: str
    parameters: dict[str, Any] = field(default_factory=dict)
    performance_metrics: dict[str, float] = field(default_factory=dict)
    usage_count: int = 0
    success_rate: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)


class OnlineLearningEngine:
    """在线学习引擎"""

    def __init__(self):
        """初始化学习引擎"""
        self.name = "在线学习引擎"
        self.version = "1.0.0"

        # 日志配置
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(self.name)

        # 经验库
        self.experiences: list[LearningExperience] = []

        # 策略库
        self.strategies: dict[str, StrategyProfile] = {}

        # 学习统计
        self.stats = {
            "total_learning_episodes": 0,
            "successful_learnings": 0,
            "failed_learnings": 0,
            "strategy_updates": 0,
            "feedback_processed": 0,
        }

        # 学习配置
        self.config = {
            "learning_rate": 0.01,  # 学习率
            "experience_decay": 0.95,  # 经验衰减
            "min_experiences_for_learning": 5,  # 最小学习经验数
            "auto_adapt": True,  # 自动适应
            "meta_learning_enabled": True,  # 元学习开关
        }

        # 用户偏好模型
        self.user_preferences: dict[str, dict[str, Any]] = {}

        print(f"🧠 {self.name} v{self.version} 初始化完成")

    async def learn_from_execution(
        self,
        task_context: dict[str, Any],        actions: list[dict[str, Any]],        results: list[dict[str, Any]],    ) -> list[str]:
        """
        从执行结果中学习

        Args:
            task_context: 任务上下文
            actions: 执行的动作列表
            results: 执行结果列表

        Returns:
            list[str]: 学到的经验教训
        """
        self.logger.info("🧠 从执行结果中学习...")

        lessons = []

        try:
            # 1. 分析成功案例
            successful_actions = [
                (action, result)
                for action, result in zip(actions, results, strict=False)
                if result.get("success", False)
            ]

            # 2. 分析失败案例
            failed_actions = [
                (action, result)
                for action, result in zip(actions, results, strict=False)
                if not result.get("success", False)
            ]

            # 3. 提取成功模式
            if successful_actions:
                success_patterns = await self._extract_success_patterns(
                    task_context, successful_actions
                )
                lessons.extend(success_patterns)

            # 4. 分析失败原因
            if failed_actions:
                failure_lessons = await self._analyze_failures(task_context, failed_actions)
                lessons.extend(failure_lessons)

            # 5. 更新策略
            if lessons:
                await self._update_strategies_from_lessons(lessons)

            # 6. 创建学习经验
            experience = LearningExperience(
                experience_id=f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                learning_type=LearningType.FROM_EXECUTION,
                task_context=task_context,
                action_taken=actions[0] if actions else {},
                result=results[0] if results else {},
                success=len(successful_actions) > len(failed_actions),
                reward=len(successful_actions) - len(failed_actions),
                lessons_learned=lessons,
            )

            self.experiences.append(experience)
            self.stats["total_learning_episodes"] += 1
            self.stats["successful_learnings"] += len(successful_actions)
            self.stats["failed_learnings"] += len(failed_actions)

            self.logger.info(f"✅ 学习完成,获得 {len(lessons)} 条经验")
            return lessons

        except Exception as e:
            self.logger.error(f"❌ 执行学习失败: {e}")
            return []

    async def adapt_to_user_feedback(
        self, user_id: str, feedback: dict[str, Any], context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        适应用户反馈

        Args:
            user_id: 用户ID
            feedback: 用户反馈
            context: 上下文信息

        Returns:
            dict[str, Any]: 适应结果
        """
        self.logger.info(f"🔄 适应用户反馈: {user_id}")

        try:
            # 1. 分析反馈类型
            feedback.get("type", "rating")
            feedback_value = feedback.get("value", 0)
            feedback_text = feedback.get("text", "")

            # 2. 更新用户偏好
            await self._update_user_preferences(user_id, feedback, context)

            # 3. 调整推理策略
            strategy_adjustments = await self._adjust_inference_strategy(user_id, feedback)

            # 4. 个性化优化
            personalization = await self._personalize_response(user_id, feedback)

            # 5. 创建学习经验
            experience = LearningExperience(
                experience_id=f"feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                learning_type=LearningType.FROM_FEEDBACK,
                task_context=context or {},
                action_taken={"type": "response_generation"},
                result={"feedback": feedback},
                success=feedback_value > 0.5,
                reward=feedback_value,
                lessons_learned=[f"用户偏好: {feedback_text}", f"调整策略: {strategy_adjustments}"],
            )

            self.experiences.append(experience)
            self.stats["feedback_processed"] += 1

            result = {
                "user_id": user_id,
                "adaptation_successful": True,
                "strategy_adjustments": strategy_adjustments,
                "personalization": personalization,
                "updated_preferences": self.user_preferences.get(user_id, {}),
            }

            self.logger.info("✅ 用户反馈适应完成")
            return result

        except Exception as e:
            self.logger.error(f"❌ 反馈适应失败: {e}")
            return {"adaptation_successful": False, "error": str(e)}

    async def meta_learning(
        self, task_history: list[dict[str, Any]], num_tasks: int = 10
    ) -> dict[str, Any]:
        """
        元学习 - 学习如何学习

        Args:
            task_history: 任务历史
            num_tasks: 分析的任务数量

        Returns:
            dict[str, Any]: 元学习结果
        """
        self.logger.info(f"🎓 执行元学习,分析 {min(num_tasks, len(task_history))} 个任务")

        try:
            # 1. 跨任务模式识别
            patterns = await self._identify_cross_task_patterns(task_history[-num_tasks:])

            # 2. 学习任务相似性
            task_similarity = await self._learn_task_similarity(task_history)

            # 3. 识别迁移学习机会
            transfer_opportunities = await self._identify_transfer_opportunities(
                task_history, patterns
            )

            # 4. 生成元学习策略
            meta_strategies = await self._generate_meta_strategies(patterns)

            # 5. 更新学习策略
            await self._update_learning_strategies(meta_strategies)

            result = {
                "patterns_identified": len(patterns),
                "task_similarity": task_similarity,
                "transfer_opportunities": transfer_opportunities,
                "meta_strategies": meta_strategies,
                "learning_capability": "improved",
            }

            self.logger.info(f"✅ 元学习完成: 识别 {len(patterns)} 个模式")
            return result

        except Exception as e:
            self.logger.error(f"❌ 元学习失败: {e}")
            return {"learning_capability": "unchanged", "error": str(e)}

    async def extract_and_optimize_strategy(
        self, domain: str, experience_window: int = 50
    ) -> dict[str, Any]:
        """
        提取并优化策略

        Args:
            domain: 领域
            experience_window: 经验窗口大小

        Returns:
            dict[str, Any]: 优化结果
        """
        self.logger.info(f"⚙️ 提取并优化策略: {domain}")

        try:
            # 1. 获取相关经验
            relevant_experiences = [
                exp
                for exp in self.experiences[-experience_window:]
                if exp.task_context.get("domain") == domain
            ]

            if len(relevant_experiences) < self.config["min_experiences_for_learning"]:
                self.logger.warning(
                    f"经验不足 ({len(relevant_experiences)}/{self.config['min_experiences_for_learning']})"
                )
                return {"optimization_status": "insufficient_data"}

            # 2. 分析策略模式
            strategy_patterns = await self._analyze_strategy_patterns(relevant_experiences)

            # 3. 识别最优策略
            best_strategies = await self._identify_best_strategies(relevant_experiences)

            # 4. 生成策略建议
            strategy_recommendations = await self._generate_strategy_recommendations(
                best_strategies
            )

            # 5. 更新策略库
            for rec in strategy_recommendations:
                await self._add_or_update_strategy(rec)

            result = {
                "domain": domain,
                "optimization_status": "success",
                "experiences_analyzed": len(relevant_experiences),
                "patterns_found": len(strategy_patterns),
                "strategies_recommended": len(strategy_recommendations),
                "recommendations": strategy_recommendations,
            }

            self.stats["strategy_updates"] += len(strategy_recommendations)

            self.logger.info(f"✅ 策略优化完成: 生成 {len(strategy_recommendations)} 个建议")
            return result

        except Exception as e:
            self.logger.error(f"❌ 策略优化失败: {e}")
            return {"optimization_status": "failed", "error": str(e)}

    async def _analyze_common_features(
        self, successful_actions: list[tuple[dict, dict]]
    ) -> dict[str, int]:
        """分析共同特征"""
        features = defaultdict(int)

        for action, _result in successful_actions:
            action_name = action.get("name", "unknown")
            features[action_name] += 1

            # 分析参数特征
            params = action.get("params", {})
            if isinstance(params, dict):
                for key in params:
                    features[f"param_{key}"] += 1

        return dict(features)

    async def _extract_success_patterns(
        self, context: dict[str, Any], successful_actions: list[tuple[dict, dict]]
    ) -> list[str]:
        """提取成功模式"""
        patterns = []

        if not successful_actions:
            return patterns

        # 分析共同特征
        common_features = await self._analyze_common_features(successful_actions)
        for feature, count in common_features.items():
            if count >= len(successful_actions) * 0.5:
                patterns.append(f"成功特征: {feature} (出现{count}次)")

        return patterns

    async def _analyze_failures(
        self, context: dict[str, Any], failed_actions: list[tuple[dict, dict]]
    ) -> list[str]:
        """分析失败原因"""
        lessons = []

        for action, result in failed_actions:
            error = result.get("error", "未知错误")
            lessons.append(f"避免: {action.get('name', '未知动作')} - {error}")

        return lessons

    async def _update_strategies_from_lessons(self, lessons: list[str]) -> None:
        """从经验中更新策略"""
        # 提取策略更新
        for lesson in lessons:
            if "成功特征" in lesson:
                # 正向强化
                await self._reinforce_positive_pattern(lesson)
            elif "避免" in lesson:
                # 负向规避
                await self._add_negative_pattern(lesson)

    async def _reinforce_positive_pattern(self, pattern: str) -> None:
        """强化正向模式"""
        # 实现正向强化逻辑
        pass

    async def _add_negative_pattern(self, pattern: str) -> None:
        """添加负向模式"""
        # 实现负向规避逻辑
        pass

    async def _update_user_preferences(
        self, user_id: str, feedback: dict[str, Any], context: dict[str, Any]
    ) -> None:
        """更新用户偏好"""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {
                "preferred_response_style": "balanced",
                "preferred_detail_level": "medium",
                "preferred_examples": False,
                "feedback_history": [],
            }

        # 分析反馈模式
        feedback_history = self.user_preferences[user_id]["feedback_history"]
        feedback_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "value": feedback.get("value", 0),
                "type": feedback.get("type", "unknown"),
            }
        )

        # 更新偏好
        if len(feedback_history) > 5:
            recent_scores = [f["value"] for f in feedback_history[-5:]]
            avg_score = sum(recent_scores) / len(recent_scores)

            if avg_score > 0.8:
                self.user_preferences[user_id]["preferred_response_style"] = "detailed"
            elif avg_score < 0.4:
                self.user_preferences[user_id]["preferred_response_style"] = "concise"

    async def _adjust_inference_strategy(
        self, user_id: str, feedback: dict[str, Any]
    ) -> dict[str, Any]:
        """调整推理策略"""
        adjustments = {}

        preferences = self.user_preferences.get(user_id, {})
        style = preferences.get("preferred_response_style", "balanced")

        if style == "detailed":
            adjustments["max_tokens"] = 2000
            adjustments["temperature"] = 0.7
        elif style == "concise":
            adjustments["max_tokens"] = 500
            adjustments["temperature"] = 0.5
        else:
            adjustments["max_tokens"] = 1000
            adjustments["temperature"] = 0.6

        return adjustments

    async def _personalize_response(self, user_id: str, feedback: dict[str, Any]) -> dict[str, Any]:
        """个性化响应"""
        preferences = self.user_preferences.get(user_id, {})

        return {
            "greeting": "customized" if user_id in self.user_preferences else "default",
            "detail_level": preferences.get("preferred_detail_level", "medium"),
            "include_examples": preferences.get("preferred_examples", False),
        }

    async def _identify_cross_task_patterns(
        self, task_history: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """识别跨任务模式"""
        patterns = []

        # 分析成功任务的共同特征
        successful_tasks = [t for t in task_history if t.get("success", False)]

        if len(successful_tasks) < 2:
            return patterns

        # 特征提取
        common_features = ["使用GLM-4.7规划", "并行任务识别", "用户确认步骤", "动态调整"]

        for feature in common_features:
            count = sum(1 for t in successful_tasks if feature in str(t))
            if count >= len(successful_tasks) * 0.6:
                patterns.append(
                    {
                        "pattern": feature,
                        "frequency": count / len(successful_tasks),
                        "confidence": min(count / len(successful_tasks), 1.0),
                    }
                )

        return patterns

    async def _learn_task_similarity(self, task_history: list[dict[str, Any]]) -> dict[str, float]:
        """学习任务相似性"""
        # 简化实现
        return {"domain_similarity": 0.7, "complexity_similarity": 0.6, "strategy_similarity": 0.8}

    async def _identify_transfer_opportunities(
        self, task_history: list[dict[str, Any]], patterns: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """识别迁移学习机会"""
        opportunities = []

        for pattern in patterns:
            if pattern["frequency"] > 0.7:
                opportunities.append(
                    {
                        "source_pattern": pattern["pattern"],
                        "transfer_confidence": pattern["confidence"],
                        "potential_benefit": "high",
                    }
                )

        return opportunities

    async def _generate_meta_strategies(
        self, patterns: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """生成元策略"""
        strategies = []

        # 基于模式生成策略
        for pattern in patterns:
            strategies.append(
                {
                    "name": f"基于{pattern['pattern']}的策略",
                    "description": f"利用{pattern['pattern']}提高成功率",
                    "confidence": pattern["confidence"],
                    "applicability": pattern["frequency"],
                }
            )

        return strategies

    async def _update_learning_strategies(self, meta_strategies: list[dict[str, Any]]) -> None:
        """更新学习策略"""
        # 更新学习配置
        for strategy in meta_strategies:
            if strategy["confidence"] > 0.8:
                # 高置信度策略,直接应用
                pass
            elif strategy["applicability"] > 0.6:
                # 中等适用性,谨慎应用
                pass

    async def _analyze_strategy_patterns(
        self, experiences: list[LearningExperience]
    ) -> list[dict[str, Any]]:
        """分析策略模式"""
        # 统计成功策略
        strategy_success = defaultdict(lambda: {"success": 0, "total": 0})

        for exp in experiences:
            action_name = exp.action_taken.get("name", "unknown")
            strategy_success[action_name]["total"] += 1
            if exp.success:
                strategy_success[action_name]["success"] += 1

        # 生成模式
        patterns = []
        for action, stats in strategy_success.items():
            if stats["total"] >= 3:
                success_rate = stats["success"] / stats["total"]
                patterns.append(
                    {
                        "action": action,
                        "usage_count": stats["total"],
                        "success_rate": success_rate,
                        "reliability": "high" if success_rate > 0.8 else "medium",
                    }
                )

        return sorted(patterns, key=lambda x: x["success_rate"], reverse=True)

    async def _identify_best_strategies(
        self, experiences: list[LearningExperience]
    ) -> list[dict[str, Any]]:
        """识别最优策略"""
        # 计算每个策略的平均奖励
        strategy_rewards = defaultdict(list)

        for exp in experiences:
            action_name = exp.action_taken.get("name", "unknown")
            strategy_rewards[action_name].append(exp.reward)

        # 找出最优策略
        best_strategies = []
        for action, rewards in strategy_rewards.items():
            if len(rewards) >= 3:
                avg_reward = sum(rewards) / len(rewards)
                best_strategies.append(
                    {"action": action, "avg_reward": avg_reward, "sample_size": len(rewards)}
                )

        return sorted(best_strategies, key=lambda x: x["avg_reward"], reverse=True)

    async def _generate_strategy_recommendations(
        self, best_strategies: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """生成策略建议"""
        recommendations = []

        for strategy in best_strategies[:5]:  # 取前5个
            recommendations.append(
                {
                    "strategy_id": f"str_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{strategy['action']}",
                    "name": strategy["action"],
                    "expected_reward": strategy["avg_reward"],
                    "confidence": min(len(strategy["sample_size"]) / 10, 1.0),
                    "parameters": {"preferred": True, "weight": strategy["avg_reward"]},
                }
            )

        return recommendations

    async def _add_or_update_strategy(self, recommendation: dict[str, Any]) -> None:
        """添加或更新策略"""
        strategy_id = recommendation["strategy_id"]

        if strategy_id in self.strategies:
            # 更新现有策略
            strategy = self.strategies[strategy_id]
            strategy.usage_count += 1
            strategy.last_updated = datetime.now()
        else:
            # 添加新策略
            self.strategies[strategy_id] = StrategyProfile(
                strategy_id=strategy_id,
                name=recommendation["name"],
                parameters=recommendation.get("parameters", {}),
                performance_metrics={"expected_reward": recommendation.get("expected_reward", 0)},
                success_rate=recommendation.get("confidence", 0.5),
                usage_count=1,
            )

    def get_learning_stats(self) -> dict[str, Any]:
        """获取学习统计"""
        return {
            **self.stats,
            "total_experiences": len(self.experiences),
            "total_strategies": len(self.strategies),
            "user_count": len(self.user_preferences),
        }

    def get_top_strategies(self, limit: int = 10) -> list[StrategyProfile]:
        """获取顶级策略"""
        strategies = list(self.strategies.values())
        strategies.sort(key=lambda s: s.success_rate, reverse=True)
        return strategies[:limit]


# ==================== 全局实例 ====================

_online_learning_engine: OnlineLearningEngine | None = None


def get_online_learning_engine() -> OnlineLearningEngine:
    """获取在线学习引擎单例"""
    global _online_learning_engine
    if _online_learning_engine is None:
        _online_learning_engine = OnlineLearningEngine()
    return _online_learning_engine


# ==================== 导出 ====================

__all__ = [
    "LearningExperience",
    "LearningType",
    "OnlineLearningEngine",
    "StrategyProfile",
    "get_online_learning_engine",
]
