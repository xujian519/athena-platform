#!/usr/bin/env python3
"""
学习引擎 (Learning Engine)
基于经验强化和知识迁移的学习系统

核心思想:
1. 经验学习:从情景记忆中提取经验教训
2. 强化学习:基于反馈优化行为策略
3. 知识迁移:将经验转化为长期知识
4. 模式识别:识别成功/失败的行为模式
5. 策略优化:动态调整决策参数

作者: Athena平台团队
创建时间: 2026-01-22
版本: v2.0.0
"""

import asyncio
import hashlib
import json
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class LearningType(Enum):
    """学习类型"""

    REINFORCEMENT = "reinforcement"  # 强化学习
    EXPERIENCE = "experience"  # 经验学习
    PATTERN_RECOGNITION = "pattern_recognition"  # 模式识别
    KNOWLEDGE_TRANSFER = "knowledge_transfer"  # 知识迁移


class FeedbackType(Enum):
    """反馈类型"""

    POSITIVE = "positive"  # 正反馈(奖励)
    NEGATIVE = "negative"  # 负反馈(惩罚)
    NEUTRAL = "neutral"  # 中性反馈


@dataclass
class LearningExperience:
    """学习经验"""

    experience_id: str
    situation: str  # 情境描述
    action: str  # 采取的行动
    result: str  # 结果
    feedback_type: FeedbackType
    reward: float  # 奖励值(-1.0 ~ 1.0)
    learned_at: str = field(default_factory=lambda: datetime.now().isoformat())
    confidence: float = 0.5  # 学习置信度
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "experience_id": self.experience_id,
            "situation": self.situation,
            "action": self.action,
            "result": self.result,
            "feedback_type": self.feedback_type.value,
            "reward": self.reward,
            "learned_at": self.learned_at,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


@dataclass
class BehaviorPattern:
    """行为模式"""

    pattern_id: str
    trigger_conditions: dict[str, Any]  # 触发条件
    recommended_action: str  # 推荐行动
    success_rate: float  # 成功率
    average_reward: float  # 平均奖励
    usage_count: int  # 使用次数
    last_used: str  # 最后使用时间
    confidence: float = 0.5  # 模式置信度

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "pattern_id": self.pattern_id,
            "trigger_conditions": self.trigger_conditions,
            "recommended_action": self.recommended_action,
            "success_rate": self.success_rate,
            "average_reward": self.average_reward,
            "usage_count": self.usage_count,
            "last_used": self.last_used,
            "confidence": self.confidence,
        }


@dataclass
class LearningStrategy:
    """学习策略"""

    strategy_name: str
    parameters: dict[str, Any]  # 策略参数
    performance_metrics: dict[str, float]  # 性能指标
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())


class LearningEngine:
    """
    学习引擎 - 经验强化与知识迁移

    核心功能:
    1. 经验记录:记录行动-结果-反馈三元组
    2. 模式识别:识别成功的行为模式
    3. 策略优化:基于反馈优化决策策略
    4. 知识迁移:将经验转化为长期知识
    5. 性能评估:评估学习效果

    学习机制:
    - 强化学习:基于奖励信号调整行为
    - 经验回放:从历史经验中学习
    - 模式归纳:从多个经验中提取模式
    """

    def __init__(
        self,
        learning_rate: float = 0.1,
        discount_factor: float = 0.9,
        exploration_rate: float = 0.2,
    ):
        """
        初始化学习引擎

        Args:
            learning_rate: 学习率(0~1)
            discount_factor: 折扣因子(未来奖励的权重)
            exploration_rate: 探索率(尝试新行动的概率)
        """
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.exploration_rate = exploration_rate

        # 并发安全锁
        self._lock = asyncio.Lock()

        # 经验库
        self.experiences: list[LearningExperience] = []

        # 行为模式库
        self.patterns: dict[str, BehaviorPattern] = {}

        # Q值表(状态-动作价值)
        self.q_table: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))

        # 学习策略
        self.strategies: dict[str, LearningStrategy] = {}

        # 统计信息
        self.stats = {
            "total_experiences": 0,
            "total_patterns": 0,
            "learning_iterations": 0,
            "average_reward": 0.0,
            "success_rate": 0.0,
        }

    async def learn_from_experience(
        self,
        situation: str,
        action: str,
        result: str,
        feedback_type: FeedbackType,
        reward: float,
        metadata: dict[str, Any] | None = None,
    ) -> LearningExperience:
        """
        从经验中学习

        Args:
            situation: 情境描述
            action: 采取的行动
            result: 结果
            feedback_type: 反馈类型
            reward: 奖励值
            metadata: 元数据

        Returns:
            学习经验
        """
        # 使用锁确保并发安全
        async with self._lock:
            # 创建经验ID
            experience_id = f"exp_{int(time.time() * 1000)}_{hashlib.md5(f'{situation}:{action}'.encode('utf-8'), usedforsecurity=False).hexdigest()[:8]}"

            # 创建学习经验
            experience = LearningExperience(
                experience_id=experience_id,
                situation=situation,
                action=action,
                result=result,
                feedback_type=feedback_type,
                reward=reward,
                metadata=metadata or {},
            )

            # 存储经验
            self.experiences.append(experience)

            # 更新Q值
            state_key = self._get_state_key(situation)
            action_key = action

            # Q-learning更新规则
            current_q = self.q_table[state_key][action_key]
            self.q_table[state_key][action_key] = current_q + self.learning_rate * (
                reward - current_q
            )

            # 更新统计
            self.stats["total_experiences"] += 1
            self._update_average_reward()
            self._update_success_rate()

            logger.info(
                f"📚 学习经验: {situation[:30]}... -> {action[:30]}... "
                f"(奖励={reward:.2f}, 反馈={feedback_type.value})"
            )

            # 定期进行模式识别
            if len(self.experiences) % 10 == 0:
                await self._identify_patterns()

            return experience

    async def get_recommended_action(
        self, situation: str, available_actions: list[str], explore: bool = False
    ) -> tuple[str, float]:
        """
        获取推荐行动

        Args:
            situation: 当前情境
            available_actions: 可用行动列表
            explore: 是否探索(尝试新行动)

        Returns:
            (推荐行动, Q值)
        """
        state_key = self._get_state_key(situation)

        # 探索或利用
        if explore and (hash(state_key) % 100) / 100 < self.exploration_rate:
            # 随机探索
            action = available_actions[hash(state_key) % len(available_actions)]
            q_value = self.q_table[state_key].get(action, 0.0)
            logger.debug(f"🎲 探索: 选择行动 {action}")
            return action, q_value

        # 查找最佳行动
        best_action = None
        best_q_value = float("-inf")

        for action in available_actions:
            q_value = self.q_table[state_key].get(action, 0.0)
            if q_value > best_q_value:
                best_q_value = q_value
                best_action = action

        # 如果没有经验,随机选择
        if best_action is None:
            best_action = available_actions[0]
            best_q_value = 0.0

        logger.debug(f"🎯 利用: 选择行动 {best_action} (Q={best_q_value:.2f})")
        return best_action, best_q_value

    async def _identify_patterns(self):
        """识别行为模式"""
        logger.info("🔍 开始识别行为模式...")

        # 按情境分组经验
        situation_groups = defaultdict(list)
        for exp in self.experiences:
            situation_key = self._get_situation_group_key(exp.situation)
            situation_groups[situation_key].append(exp)

        # 为每个情境识别模式
        for situation_key, experiences in situation_groups.items():
            if len(experiences) < 2:
                continue

            # 按行动分组
            action_groups = defaultdict(list)
            for exp in experiences:
                action_groups[exp.action].append(exp)

            # 找出最佳行动
            best_action = None
            best_avg_reward = float("-inf")
            best_success_rate = 0.0

            for action, action_exps in action_groups.items():
                # 计算平均奖励
                avg_reward = sum(e.reward for e in action_exps) / len(action_exps)

                # 计算成功率
                success_count = sum(1 for e in action_exps if e.reward > 0)
                success_rate = success_count / len(action_exps)

                if avg_reward > best_avg_reward:
                    best_avg_reward = avg_reward
                    best_action = action
                    best_success_rate = success_rate

            # 创建或更新模式
            if best_action and best_success_rate > 0.6:
                pattern_id = f"pattern_{situation_key[:8]}_{hashlib.md5(best_action.encode('utf-8'), usedforsecurity=False).hexdigest()[:8]}"

                if pattern_id in self.patterns:
                    # 更新现有模式
                    pattern = self.patterns[pattern_id]
                    pattern.success_rate = pattern.success_rate * 0.7 + best_success_rate * 0.3
                    pattern.average_reward = pattern.average_reward * 0.7 + best_avg_reward * 0.3
                    pattern.usage_count += len(experiences)
                    pattern.last_used = datetime.now().isoformat()
                    pattern.confidence = min(1.0, pattern.confidence + 0.05)
                else:
                    # 创建新模式
                    self.patterns[pattern_id] = BehaviorPattern(
                        pattern_id=pattern_id,
                        trigger_conditions={"situation_keyword": situation_key},
                        recommended_action=best_action,
                        success_rate=best_success_rate,
                        average_reward=best_avg_reward,
                        usage_count=len(experiences),
                        last_used=datetime.now().isoformat(),
                        confidence=0.5,
                    )

                self.stats["total_patterns"] = len(self.patterns)

        logger.info(f"✅ 识别完成: 发现 {len(self.patterns)} 个行为模式")

    async def reinforce_from_feedback(
        self, experience_id: str, new_reward: float, feedback_type: FeedbackType
    ):
        """
        基于反馈强化学习

        Args:
            experience_id: 经验ID
            new_reward: 新的奖励值
            feedback_type: 反馈类型
        """
        # 查找经验
        experience = next((e for e in self.experiences if e.experience_id == experience_id), None)
        if not experience:
            logger.warning(f"⚠️  经验未找到: {experience_id}")
            return

        # 更新奖励
        old_reward = experience.reward
        experience.reward = new_reward
        experience.feedback_type = feedback_type

        # 重新计算Q值
        state_key = self._get_state_key(experience.situation)
        action_key = experience.action

        current_q = self.q_table[state_key][action_key]
        self.q_table[state_key][action_key] = current_q + self.learning_rate * (
            new_reward - current_q
        )

        logger.info(
            f"🔄 强化学习: {experience_id} " f"(奖励: {old_reward:.2f} -> {new_reward:.2f})"
        )

        # 更新统计
        self._update_average_reward()
        self._update_success_rate()

    async def transfer_to_knowledge(
        self, experience_id: str, memory_system: Any | None = None
    ) -> str | None:
        """
        将经验迁移为知识

        Args:
            experience_id: 经验ID
            memory_system: 记忆系统(可选)

        Returns:
            知识ID(如果迁移成功)
        """
        # 查找经验
        experience = next((e for e in self.experiences if e.experience_id == experience_id), None)
        if not experience:
            logger.warning(f"⚠️  经验未找到: {experience_id}")
            return None

        # 只有高价值的经验才迁移
        if abs(experience.reward) < 0.5 or experience.confidence < 0.7:
            logger.debug(f"⏭️  经验价值不足,跳过迁移: {experience_id}")
            return None

        # 构建知识内容
        knowledge_content = f"""
经验总结:
- 情境:{experience.situation}
- 行动:{experience.action}
- 结果:{experience.result}
- 反馈:{experience.feedback_type.value}
- 奖励:{experience.reward:.2f}

学习结论:
{'此行动在此情境下效果良好,建议重复使用。' if experience.reward > 0 else '此行动在此情境下效果不佳,建议避免使用。'}
"""

        # 如果有记忆系统,存储到语义记忆
        if memory_system:
            try:
                from core.xiaonuo_agent.memory.memory_system import MemoryType

                result = await memory_system.remember(
                    information=knowledge_content,
                    memory_type=MemoryType.SEMANTIC,
                    metadata={
                        "source": "learning_engine",
                        "experience_id": experience_id,
                        "reward": experience.reward,
                    },
                )
                logger.info(f"✅ 知识迁移成功: {experience_id} -> {result}")
                return result.get("semantic")
            except Exception as e:
                logger.error(f"❌ 知识迁移失败: {e}")
                return None

        logger.debug(f"💭 知识内容已生成: {knowledge_content[:100]}...")
        return None

    def _get_state_key(self, situation: str) -> str:
        """生成状态键"""
        # 简化:使用关键词提取(实际应使用NLP)
        keywords = self._extract_keywords(situation)
        return "|".join(sorted(keywords))

    def _get_situation_group_key(self, situation: str) -> str:
        """生成情境分组键"""
        keywords = self._extract_keywords(situation)[:3]  # 取前3个关键词
        return "_".join(sorted(keywords))

    def _extract_keywords(self, text: str) -> list[str]:
        """提取关键词(简化实现)"""
        # 实际应使用TF-IDF或类似算法
        words = text.lower().replace(",", " ").replace(",", " ").split()
        # 过滤常见词
        stopwords = {"的", "了", "是", "在", "我", "你", "他", "她", "它", "们", "这", "那", "和"}
        keywords = [w for w in words if len(w) > 1 and w not in stopwords]
        return keywords[:5]  # 返回前5个关键词

    def _update_average_reward(self):
        """更新平均奖励"""
        if not self.experiences:
            return
        self.stats["average_reward"] = sum(e.reward for e in self.experiences) / len(
            self.experiences
        )

    def _update_success_rate(self):
        """更新成功率"""
        if not self.experiences:
            return
        success_count = sum(1 for e in self.experiences if e.reward > 0)
        self.stats["success_rate"] = success_count / len(self.experiences)

    async def get_patterns(
        self, situation: str | None = None, min_success_rate: float = 0.6
    ) -> list[BehaviorPattern]:
        """
        获取行为模式

        Args:
            situation: 情境描述(可选)
            min_success_rate: 最小成功率

        Returns:
            匹配的模式列表
        """
        if situation:
            # 查找匹配的模式
            situation_key = self._get_situation_group_key(situation)
            matching = []
            for pattern in self.patterns.values():
                if (
                    situation_key in pattern.pattern_id
                    or situation_key in pattern.recommended_action
                ) and pattern.success_rate >= min_success_rate:
                    matching.append(pattern)
            return sorted(matching, key=lambda p: p.success_rate, reverse=True)
        else:
            # 返回所有高质量模式
            return [p for p in self.patterns.values() if p.success_rate >= min_success_rate]

    async def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "total_patterns": len(self.patterns),
            "q_table_size": sum(len(actions) for actions in self.q_table.values()),
            "exploration_rate": self.exploration_rate,
            "learning_rate": self.learning_rate,
        }

    def export_learning_data(self, filepath: str):
        """
        导出学习数据

        Args:
            filepath: 导出文件路径
        """
        data = {
            "experiences": [e.to_dict() for e in self.experiences],
            "patterns": {k: p.to_dict() for k, p in self.patterns.items()},
            "q_table": dict(self.q_table),
            "stats": self.stats,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"📁 学习数据已导出: {filepath}")

    def import_learning_data(self, filepath: str):
        """
        导入学习数据

        Args:
            filepath: 导入文件路径
        """
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        # 恢复经验
        self.experiences = [LearningExperience(**exp) for exp in data.get("experiences", [])]

        # 恢复模式
        self.patterns = {k: BehaviorPattern(**v) for k, v in data.get("patterns", {}).items()}

        # 恢复Q表
        self.q_table = defaultdict(lambda: defaultdict(float))
        for state, actions in data.get("q_table", {}).items():
            for action, value in actions.items():
                self.q_table[state][action] = value

        # 恢复统计
        self.stats.update(data.get("stats", {}))

        logger.info(f"📥 学习数据已导入: {filepath}")


# 便捷函数
async def create_learning_engine(**kwargs) -> LearningEngine:
    """创建学习引擎"""
    return LearningEngine(**kwargs)
