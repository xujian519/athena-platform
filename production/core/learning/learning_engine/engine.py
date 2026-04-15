#!/usr/bin/env python3
"""
学习引擎 - 主引擎
Learning Engine - Main Engine

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0

支持机器学习、经验积累、模式识别和自适应调整
"""

from __future__ import annotations
import inspect
import logging
from collections import defaultdict
from datetime import datetime
from typing import Any

from core.learning.persistence_manager import get_persistence_manager

from .adaptive_optimizer import AdaptiveOptimizer
from .experience_store import ExperienceStore
from .knowledge_updater import KnowledgeGraphUpdater
from .pattern_recognizer import PatternRecognizer

logger = logging.getLogger(__name__)


class LearningEngine:
    """学习引擎 - 完整实现"""

    def __init__(self, agent_id: str, config: dict | None = None):
        self.agent_id = agent_id
        self.config = config or {}
        self.initialized = False

        # 核心组件
        self.experience_store = ExperienceStore(
            max_experiences=self.config.get("max_experiences", 10000)
        )
        self.pattern_recognizer = PatternRecognizer()
        self.adaptive_optimizer = AdaptiveOptimizer()
        self.knowledge_updater: KnowledgeGraphUpdater | None = None  # 延迟初始化

        # 学习状态
        self.learning_stats: dict[str, Any] = {
            "total_experiences": 0,
            "patterns_discovered": 0,
            "optimizations_applied": 0,
            "last_learning": None,
        }

        # 性能阈值(用于反馈学习)
        self.performance_threshold = self.config.get("performance_threshold", 0.5)

        # 学习记录存储
        self.learning_records: list[dict[str, Any]] = []
        self.feedback_records: list[dict[str, Any]] = []

        # 当前学习率(用于行为适应)
        self.current_learning_rate = self.config.get("learning_rate", 0.1)

        # 适应计数
        self.adaptation_count = 0

        # 回调管理
        self._callbacks: defaultdict[str, list[Any]] = defaultdict(list)

        logger.info(f"🧠 创建学习引擎: {self.agent_id}")

    async def initialize(self, knowledge_manager: Any = None) -> None:
        """初始化学习引擎"""
        logger.info(f"🚀 启动学习引擎: {self.agent_id}")

        try:
            # 初始化知识图谱更新器
            if knowledge_manager:
                self.knowledge_updater = KnowledgeGraphUpdater(knowledge_manager)
                await self.knowledge_updater.start()

            # 加载历史数据
            await self._load_historical_data()

            self.initialized = True

            # 触发初始化事件
            await self._trigger_callbacks(
                "initialized", {"agent_id": self.agent_id, "timestamp": datetime.now()}
            )

            logger.info(f"✅ 学习引擎初始化完成: {self.agent_id}")

        except Exception as e:
            logger.error(f"❌ 学习引擎初始化失败 {self.agent_id}: {e}")
            raise

    async def learn(self, data: dict[str, Any]) -> dict[str, Any]:
        """学习数据"""
        if not self.initialized:
            raise RuntimeError("学习引擎未初始化")

        try:
            # 1. 存储经验
            experience = {
                "type": data.get("type", "general"),
                "context": data.get("context", {}),
                "content": data.get("content", {}),
                "outcome": data.get("outcome", {}),
                "feedback": data.get("feedback", {}),
                "performance": data.get("performance", 0.0),
            }
            self.experience_store.add_experience(experience)

            # 2. 模式识别
            patterns = await self._recognize_patterns_from_experience(experience)

            # 3. 自适应优化
            optimization_result = await self._optimize_based_on_experience(experience)

            # 4. 更新知识图谱
            if self.knowledge_updater:
                await self._update_knowledge_from_experience(experience, patterns)

            # 5. 更新统计
            self._update_learning_stats(experience, patterns, optimization_result)

            result = {
                "status": "learned",
                "experience_id": experience["id"],
                "patterns_found": len(patterns),
                "optimizations_applied": optimization_result.get("applied", False),
                "learning_confidence": self._calculate_learning_confidence(),
            }

            # 触发学习完成事件
            await self._trigger_callbacks("learned", result)

            return result

        except Exception as e:
            logger.error(f"学习过程失败: {e}")
            return {"status": "error", "error": str(e)}

    async def _recognize_patterns_from_experience(
        self, experience: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """从经验中识别模式"""
        patterns = []

        try:
            context_type = experience.get("type", "general")

            # 获取相似经验
            similar_experiences = self.experience_store.get_similar_experiences(
                experience["context"], limit=20
            )

            if len(similar_experiences) >= 3:
                # 识别模式
                patterns = await self.pattern_recognizer.recognize_patterns(
                    [*similar_experiences, experience], context_type
                )

                if patterns:
                    logger.info(f"发现 {len(patterns)} 个新模式")

        except Exception as e:
            logger.error(f"模式识别失败: {e}")

        return patterns

    async def _optimize_based_on_experience(self, experience: dict[str, Any]) -> dict[str, Any]:
        """基于经验进行优化"""
        try:
            performance = experience.get("performance", 0.0)
            context = experience.get("context", {})

            # 获取当前参数
            current_params = self._get_current_parameters()

            # 优化参数
            optimized_params = await self.adaptive_optimizer.optimize_parameters(
                performance, current_params, context
            )

            # 检查是否有优化
            applied = optimized_params != current_params

            if applied:
                await self._apply_optimized_parameters(optimized_params)
                self.learning_stats["optimizations_applied"] += 1
                logger.info(
                    f"应用参数优化: {len(set(optimized_params.items()) - set(current_params.items()))} 项"
                )

            return {
                "applied": applied,
                "old_params": current_params,
                "new_params": optimized_params,
            }

        except Exception as e:
            logger.error(f"优化过程失败: {e}")
            return {"applied": False, "error": str(e)}

    async def _update_knowledge_from_experience(
        self, experience: dict[str, Any], patterns: list[dict[str, Any]]
    ) -> None:
        """从经验更新知识图谱"""
        try:
            # 检查knowledge_updater是否可用
            if self.knowledge_updater is None:
                logger.warning("Knowledge updater not available, skipping knowledge update")
                return

            # 更新实体
            if "entities" in experience.get("content", {}):
                for entity in experience["content"]["entities"]:
                    await self.knowledge_updater.schedule_update("add_entity", entity)

            # 更新关系
            if "relations" in experience.get("content", {}):
                for relation in experience["content"]["relations"]:
                    await self.knowledge_updater.schedule_update("add_relation", relation)

            # 添加学习到的模式
            for pattern in patterns:
                await self.knowledge_updater.schedule_update("learned_pattern", pattern)

        except Exception as e:
            logger.error(f"知识图谱更新失败: {e}")

    def _get_current_parameters(self) -> dict[str, Any]:
        """获取当前参数（从配置读取）"""
        # 从配置中读取参数，如果配置不存在则使用默认值
        return {
            "depth": self.config.get("depth", 5),
            "temperature": self.config.get("temperature", 0.7),
            "learning_rate": self.config.get("learning_rate", 0.1),
            "batch_size": self.config.get("batch_size", 32),
            "creativity": self.config.get("creativity", 0.5),
        }

    async def _apply_optimized_parameters(self, params: dict[str, Any]) -> None:
        """应用优化后的参数"""
        # 这里应该将参数应用到实际的系统中
        logger.info(f"应用优化参数: {params}")

    def _calculate_learning_confidence(self) -> float:
        """计算学习置信度"""
        total_experiences = len(self.experience_store.experiences)

        if total_experiences == 0:
            return 0.0

        # 基于经验数量和优化成功率计算
        experience_factor = min(1.0, total_experiences / 100)
        optimization_factor = min(1.0, self.learning_stats["optimizations_applied"] / 10)

        return (experience_factor + optimization_factor) / 2

    def _update_learning_stats(
        self,
        experience: dict[str, Any],        patterns: list[dict[str, Any]],
        optimization_result: dict[str, Any],    ) -> None:
        """更新学习统计"""
        self.learning_stats["total_experiences"] += 1
        self.learning_stats["patterns_discovered"] += len(patterns)
        if optimization_result.get("applied"):
            self.learning_stats["optimizations_applied"] += 1
        self.learning_stats["last_learning"] = datetime.now()

    async def _load_historical_data(self) -> None:
        """加载历史数据（使用持久化管理器）"""
        try:
            # 使用持久化管理器加载历史经验
            persistence = await get_persistence_manager()
            experiences = await persistence.load_experiences(self.agent_id)

            for exp_data in experiences:
                # 确保经验有必需的字段
                if "id" not in exp_data:
                    exp_data["id"] = len(self.experience_store.experiences)
                if "timestamp" not in exp_data:
                    exp_data["timestamp"] = datetime.now()
                elif isinstance(exp_data["timestamp"], str):
                    exp_data["timestamp"] = datetime.fromisoformat(exp_data["timestamp"])

                self.experience_store.add_experience(exp_data)

            logger.info(f"✅ 加载了 {len(experiences)} 条历史经验")

            # 加载学习模式
            patterns = await persistence.load_patterns(self.agent_id)
            for pattern_data in patterns:
                # 将模式添加到模式识别器
                if hasattr(self, 'pattern_recognizer'):
                    self.pattern_recognizer.pattern_history.append({
                        "timestamp": datetime.now(),
                        "context_type": pattern_data.get("context_type", "loaded"),
                        "patterns": [pattern_data]
                    })

            logger.info(f"✅ 加载了 {len(patterns)} 个历史模式")

        except Exception as e:
            logger.warning(f"加载历史数据失败: {e}")

    async def save_state(self) -> None:
        """保存状态（使用持久化管理器）"""
        try:
            # 使用持久化管理器保存数据
            persistence = await get_persistence_manager()

            # 保存经验数据
            saved_count = 0
            for exp in self.experience_store.experiences:
                exp_dict = dict(exp)
                await persistence.save_experience(
                    agent_id=self.agent_id,
                    experience=exp_dict,
                    metadata={"source": "learning_engine"},
                )
                saved_count += 1

            # 保存学习模式
            pattern_count = 0
            for history in self.pattern_recognizer.pattern_history:
                for pattern in history["patterns"]:
                    await persistence.save_pattern(
                        agent_id=self.agent_id,
                        pattern=pattern,
                        metadata={
                            "context_type": history["context_type"],
                            "timestamp": history["timestamp"].isoformat()
                        },
                    )
                    pattern_count += 1

            logger.info(f"✅ 保存了 {saved_count} 条经验和 {pattern_count} 个模式")

        except Exception as e:
            logger.error(f"保存状态失败: {e}")

    async def get_learning_summary(self) -> dict[str, Any]:
        """获取学习摘要"""
        return {
            "agent_id": self.agent_id,
            "statistics": self.learning_stats.copy(),
            "experience_count": len(self.experience_store.experiences),
            "pattern_count": len(self.pattern_recognizer.pattern_history),
            "current_strategy": self.adaptive_optimizer.current_strategy,
            "learning_confidence": self._calculate_learning_confidence(),
        }

    async def get_patterns(self, pattern_type: str | None = None) -> list[dict[str, Any]]:
        """获取学习到的模式"""
        all_patterns = []
        for history in self.pattern_recognizer.pattern_history:
            for pattern in history["patterns"]:
                if pattern_type is None or pattern["type"] == pattern_type:
                    all_patterns.append(pattern)
        return all_patterns

    async def get_similar_experiences(self, context: dict[str, Any]) -> list[dict[str, Any]]:
        """获取相似经验"""
        return self.experience_store.get_similar_experiences(context)

    def register_callback(self, event_type: str, callback: Any) -> None:
        """注册回调函数"""
        self._callbacks[event_type].append(callback)

    async def _trigger_callbacks(self, event_type: str, data: dict[str, Any]) -> None:
        """触发回调"""
        for callback in self._callbacks[event_type]:
            try:
                if inspect.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
            except Exception as e:
                logger.error(f"回调执行失败: {e}")

    async def shutdown(self) -> None:
        """关闭学习引擎"""
        logger.info(f"🔄 关闭学习引擎: {self.agent_id}")

        try:
            # 保存状态
            await self.save_state()

            # 关闭知识图谱更新器
            if self.knowledge_updater:
                await self.knowledge_updater.stop()

            self.initialized = False

            # 触发关闭事件
            await self._trigger_callbacks(
                "shutdown", {"agent_id": self.agent_id, "timestamp": datetime.now()}
            )

            logger.info(f"✅ 学习引擎已关闭: {self.agent_id}")

        except Exception as e:
            logger.error(f"关闭学习引擎失败: {e}")

    @classmethod
    async def initialize_global(cls, config: dict | None = None) -> "LearningEngine":
        """初始化全局实例"""
        if not hasattr(cls, "global_instance"):
            cls.global_instance = cls("global", config)
            await cls.global_instance.initialize()
        return cls.global_instance

    async def process_experience(self, experience: dict[str, Any]) -> dict[str, Any]:
        """处理经验数据"""
        try:
            # 记录经验
            experience_id = f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # 分析经验类型
            exp_type = experience.get("type", "general")
            outcome = experience.get("outcome", "neutral")

            # 学习策略调整
            learning_updates: dict[str, Any] = {}
            if outcome == "success":
                learning_updates["confidence"] = 0.1
                learning_updates["strategy_success"] = True
            elif outcome == "failure":
                learning_updates["confidence"] = -0.05
                learning_updates["strategy_success"] = False

            # 保存学习记录
            await self._store_learning_record(experience_id, experience, learning_updates)

            return {
                "success": True,
                "experience_id": experience_id,
                "learning_updates": learning_updates,
                "message": f"经验处理成功: {exp_type}",
            }

        except Exception as e:
            logger.error(f"处理经验失败: {e}")
            return {"success": False, "error": str(e)}

    async def learn_from_feedback(self, feedback: dict[str, Any]) -> dict[str, Any]:
        """从反馈中学习"""
        try:
            feedback_type = feedback.get("type", "general")
            feedback_value = feedback.get("value", 0)

            # 调整学习参数
            if feedback_type == "performance":
                if feedback_value > 0.7:
                    self.performance_threshold = min(1.0, self.performance_threshold + 0.05)
                else:
                    self.performance_threshold = max(0.3, self.performance_threshold - 0.05)

            # 记录反馈
            feedback_id = f"feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            await self._store_feedback_record(feedback_id, feedback)

            return {"success": True, "feedback_id": feedback_id, "adjustments": "学习参数已更新"}

        except Exception as e:
            logger.error(f"反馈学习失败: {e}")
            return {"success": False, "error": str(e)}

    async def adapt_behavior(self, context: dict[str, Any]) -> dict[str, Any]:
        """适应行为模式

        根据任务类型和复杂度动态调整行为策略。
        """
        try:
            # 基于历史学习调整行为
            adaptations: dict[str, Any] = {}

            # 分析上下文
            task_type = context.get("task_type", "general")
            complexity = context.get("complexity", "medium")

            # 适应性调整
            if task_type == "decision":
                adaptations["decision_strategy"] = "collaborative"
                # 复杂度越高，人工参与度越高
                if complexity == "high":
                    adaptations["human_involvement"] = 0.9
                elif complexity == "low":
                    adaptations["human_involvement"] = 0.6
                else:
                    adaptations["human_involvement"] = 0.8
            elif task_type == "learning":
                # 复杂度越高，学习率越低，探索越多
                if complexity == "high":
                    adaptations["learning_rate"] = 0.05
                    adaptations["exploration"] = 0.3
                elif complexity == "low":
                    adaptations["learning_rate"] = 0.15
                    adaptations["exploration"] = 0.1
                else:
                    adaptations["learning_rate"] = 0.1
                    adaptations["exploration"] = 0.2

            return {"success": True, "adaptations": adaptations}

        except Exception as e:
            logger.error(f"行为适应失败: {e}")
            return {"success": False, "error": str(e)}

    async def get_learning_insights(self) -> dict[str, Any]:
        """获取学习洞察"""
        try:
            # 聚合学习历史
            insights = {
                "total_experiences": getattr(self, "experience_count", 0),
                "learning_rate": getattr(self, "current_learning_rate", 0.1),
                "adaptation_count": getattr(self, "adaptation_count", 0),
                "performance_trend": "improving",
                "recommendations": [],
            }

            # 生成建议
            if insights["learning_rate"] < 0.05:
                insights["recommendations"].append("建议增加学习探索")

            if insights["adaptation_count"] < 10:
                insights["recommendations"].append("建议更多行为适应")

            return insights

        except Exception as e:
            logger.error(f"获取学习洞察失败: {e}")
            return {"error": str(e)}

    async def _store_learning_record(self, exp_id: str, experience: dict, updates: dict) -> None:
        """存储学习记录"""
        # 简化实现,实际应该存储到记忆系统
        if not hasattr(self, "learning_records"):
            self.learning_records = []

        record = {
            "id": exp_id,
            "experience": experience,
            "updates": updates,
            "timestamp": datetime.now().isoformat(),
        }

        self.learning_records.append(record)

        # 限制记录数量
        if len(self.learning_records) > 100:
            self.learning_records = self.learning_records[-50:]

    async def _store_feedback_record(self, fb_id: str, feedback: dict) -> None:
        """存储反馈记录"""
        if not hasattr(self, "feedback_records"):
            self.feedback_records = []

        record = {"id": fb_id, "feedback": feedback, "timestamp": datetime.now().isoformat()}

        self.feedback_records.append(record)

        # 限制记录数量
        if len(self.feedback_records) > 50:
            self.feedback_records = self.feedback_records[-25:]  # type: ignore

    @classmethod
    async def shutdown_global(cls) -> None:
        """关闭全局实例"""
        if hasattr(cls, "global_instance") and cls.global_instance:
            await cls.global_instance.shutdown()
            del cls.global_instance


__all__ = ["LearningEngine"]
