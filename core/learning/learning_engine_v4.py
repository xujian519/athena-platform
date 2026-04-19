#!/usr/bin/env python3
from __future__ import annotations
"""
学习引擎 v4.0 - 维特根斯坦版
Learning Engine v4.0 - Wittgenstein Edition

基于维特根斯坦《逻辑哲学论》的学习原则:
- 诚实:学习的每个进步都有证据支持
- 精确:学习是逻辑结构的调整,不是模糊的改进
- 敬畏:无法学习的诚实承认,不强求
- 证据:所有学习都基于证据权重,而非盲目调整

v4.0核心特性:
1. 证据权重学习 - 每个学习都有证据支持
2. 置信度追踪 - 学习过程中追踪置信度变化
3. 逻辑结构学习 - 学习事实的逻辑关系
4. 边界学习 - 学习什么可以学,什么不可以学

作者: 小诺·双鱼公主 v4.0
创建时间: 2025-12-25
版本: v4.0.0 "逻辑之光"
"""

import json
import logging
import sys
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

sys.path.append(str(Path(__file__).parent.parent))

# 导入v4.0模块
from v4.uncertainty_quantifier import Confidence, UncertaintyQuantifier

logger = logging.getLogger(__name__)


class LearningType(Enum):
    """学习类型"""

    SUPERVISED = "supised"  # 监督学习
    REINFORCEMENT = "reinforcement"  # 强化学习
    UNSUPERVISED = "unsupervised"  # 无监督学习
    TRANSFER = "transfer"  # 迁移学习
    EVIDENCE_BASED = "evidence_based"  # v4.0新增:基于证据的学习


class EvidenceQuality(Enum):
    """v4.0证据质量等级"""

    HIGH = "high"  # 高质量:直接证据,可重复验证
    MEDIUM = "medium"  # 中等质量:间接证据,部分验证
    LOW = "low"  # 低质量:推测性证据,难以验证
    UNKNOWN = "unknown"  # 未知质量:无法评估


@dataclass
class LearningExperienceV4:
    """
    v4.0学习经验 - 包含证据和置信度

    基于维特根斯坦原则:每个学习都必须有证据支持
    """

    id: str
    type: LearningType
    context: dict[str, Any]
    action: Any
    result: Any
    reward: float = 0.0

    # v4.0新增字段
    confidence: Confidence | None = None  # 学习的置信度
    evidence: list[str] = field(default_factory=list)  # 支持证据
    evidence_quality: EvidenceQuality = EvidenceQuality.MEDIUM
    logical_structure: str | None = None  # 学习的逻辑结构
    learning_boundary: bool = True  # 是否在学习边界内
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class LearningProgressV4:
    """
    v4.0学习进度 - 包含置信度追踪
    """

    total_experiences: int = 0
    successful_learnings: int = 0
    failed_learnings: int = 0
    average_confidence_improvement: float = 0.0  # v4.0:平均置信度改进
    evidence_distribution: dict[str, int] = field(default_factory=dict)  # v4.0:证据分布
    logical_patterns_learned: int = 0  # v4.0:学习的逻辑模式数


class ExperienceStoreV4:
    """v4.0经验存储器 - 包含证据权重"""

    def __init__(self, max_experiences: int = 10000):
        self.max_experiences = max_experiences
        self.experiences = deque(maxlen=max_experiences)
        self.experience_index = {}  # 经验索引
        self.evidence_weights = defaultdict(float)  # v4.0:证据权重

    def add_experience(self, experience: LearningExperienceV4) -> None:
        """添加经验 - v4.0版本"""
        experience.id = f"exp_{datetime.now().timestamp()}"

        self.experiences.append(experience)

        # 更新索引
        context_key = self._generate_context_key(experience.context)
        if context_key not in self.experience_index:
            self.experience_index[context_key] = []
        self.experience_index[context_key].append(experience.id)

        # v4.0:更新证据权重
        for evidence in experience.evidence:
            weight = self._calculate_evidence_weight(evidence, experience.evidence_quality)
            self.evidence_weights[evidence] += weight

        conf_value = experience.confidence.value if experience.confidence else 0.0
        logger.info(f"添加经验 #{experience.id}: {experience.type.value}, 置信度: {conf_value:.1%}")

    def _calculate_evidence_weight(self, evidence: str, quality: EvidenceQuality) -> float:
        """v4.0新增:计算证据权重"""
        base_weights = {
            EvidenceQuality.HIGH: 1.0,
            EvidenceQuality.MEDIUM: 0.5,
            EvidenceQuality.LOW: 0.1,
            EvidenceQuality.UNKNOWN: 0.0,
        }
        return base_weights.get(quality, 0.5)

    def get_similar_experiences(
        self,
        context: dict[str, Any],        limit: int = 10,
        min_confidence: float = 0.0,  # v4.0新增:最小置信度过滤
    ) -> list[LearningExperienceV4]:
        """获取相似经验 - v4.0版本"""
        context_key = self._generate_context_key(context)
        if context_key not in self.experience_index:
            return []

        experience_ids = self.experience_index[context_key]
        experiences = [
            self.experiences[int(eid.split("_")[1])]
            for eid in experience_ids
            if eid in [exp.id for exp in self.experiences]
        ]

        # v4.0:按置信度和时间排序
        experiences = [
            exp for exp in experiences if exp.confidence and exp.confidence.value >= min_confidence
        ]
        experiences.sort(
            key=lambda x: (x.confidence.value if x.confidence else 0, x.timestamp), reverse=True
        )

        return experiences[:limit]

    def _generate_context_key(self, context: dict[str, Any]) -> str:
        """生成上下文键"""
        return json.dumps(context, sort_keys=True)


class LearningEngineV4:
    """
    学习引擎 v4.0 - 基于维特根斯坦原则

    核心改变:
    1. 从"盲目学习"到"基于证据的学习"
    2. 从"单次奖励"到"置信度追踪"
    3. 从"无限优化"到"边界识别"
    4. 从"黑盒学习"到"逻辑结构学习"
    """

    def __init__(self):
        self.experience_store = ExperienceStoreV4()
        self.learning_progress = LearningProgressV4()
        self.learning_rate = 0.1

        # v4.0核心组件
        self.uncertainty_quantifier = UncertaintyQuantifier()

        # v4.0:学习边界
        self.learning_boundaries = {
            "unsayable_domains": ["情感体验", "价值判断", "道德决策", "美学品味", "存在感受"],
            "low_evidence_threshold": 0.3,
            "min_confidence_for_learning": 0.5,
        }

        # 逻辑结构学习器
        self.logical_patterns = {}

    async def learn_from_experience(
        self,
        context: dict[str, Any],        action: Any,
        result: Any,
        reward: float,
        evidence: list[str] | None = None,
        evidence_quality: EvidenceQuality = EvidenceQuality.MEDIUM,
    ) -> LearningExperienceV4:
        """
        v4.0从经验中学习

        Returns:
            v4.0格式的学习经验,包含证据和置信度
        """
        # v4.0:检查是否在学习边界内
        is_in_boundary, boundary_reason = self._check_learning_boundary(context)
        if not is_in_boundary:
            logger.warning(f"超出学习边界: {boundary_reason}")
            return LearningExperienceV4(
                id="boundary_rejected",
                type=LearningType.EVIDENCE_BASED,
                context=context,
                action=action,
                result=result,
                reward=0.0,
                confidence=self.uncertainty_quantifier.quantify(
                    claim="超出学习边界", evidence=[boundary_reason], information_completeness=0.8
                ),
                evidence=[boundary_reason],
                evidence_quality=EvidenceQuality.UNKNOWN,
                learning_boundary=False,
            )

        # v4.0:评估证据质量
        if not evidence:
            evidence = [f"奖励: {reward:.2f}"]

        # v4.0:量化学习置信度
        claim = f"在上下文 {context} 中,动作 {action} 产生结果 {result}"
        confidence = self.uncertainty_quantifier.quantify(
            claim=claim,
            evidence=evidence,
            information_completeness=self._assess_evidence_completeness(evidence, context),
        )

        # 调整置信度基于奖励
        confidence.value = max(0.0, min(1.0, confidence.value * (0.5 + reward)))

        # 提取逻辑结构
        logical_structure = self._extract_logical_structure(context, action, result)

        # 创建学习经验
        experience = LearningExperienceV4(
            id="",  # 将在add_experience中设置
            type=LearningType.EVIDENCE_BASED,
            context=context,
            action=action,
            result=result,
            reward=reward,
            confidence=confidence,
            evidence=evidence,
            evidence_quality=evidence_quality,
            logical_structure=logical_structure,
            learning_boundary=True,
        )

        # 添加到存储
        self.experience_store.add_experience(experience)

        # 更新学习进度
        self._update_learning_progress(experience)

        # v4.0:如果置信度足够高,学习逻辑模式
        if confidence.value >= self.learning_boundaries["min_confidence_for_learning"]:
            await self._learn_logical_pattern(experience)

        return experience

    def _check_learning_boundary(self, context: dict[str, Any]) -> tuple[bool, str]:
        """
        v4.0新增:检查学习边界

        维特根斯坦:有些内容是不可学的(不可说领域)
        """
        context_str = json.dumps(context, ensure_ascii=False).lower()

        for unsayable_domain in self.learning_boundaries["unsayable_domains"]:
            if unsayable_domain in context_str:
                return False, f"涉及不可说领域:{unsayable_domain}"

        return True, "在学习边界内"

    def _assess_evidence_completeness(self, evidence: list[str], context: dict[str, Any]) -> float:
        """
        v4.0新增:评估证据完整性
        """
        if not evidence:
            return 0.0

        completeness = 0.5  # 基础分数

        # 证据数量
        if len(evidence) >= 3:
            completeness += 0.2
        elif len(evidence) >= 1:
            completeness += 0.1

        # 上下文覆盖
        json.dumps(context, ensure_ascii=False)
        evidence_str = " ".join(evidence)
        context_coverage = sum(1 for key in context if str(key) in evidence_str)
        completeness += min(context_coverage * 0.1, 0.3)

        return min(completeness, 1.0)

    def _extract_logical_structure(
        self, context: dict[str, Any], action: Any, result: Any
    ) -> str | None:
        """
        v4.0新增:提取逻辑结构

        维特根斯坦:理解事实的逻辑结构
        """
        # 简化的逻辑结构提取
        if isinstance(result, bool):
            return "boolean_logic"
        elif isinstance(result, (int, float)):
            return "quantitative"
        elif isinstance(result, str):
            return "symbolic"
        elif isinstance(result, (list, dict)):
            return "structural"
        else:
            return "unknown"

    async def _learn_logical_pattern(self, experience: LearningExperienceV4):
        """
        v4.0新增:学习逻辑模式

        从经验中提取和存储逻辑模式
        """
        structure = experience.logical_structure
        if structure and structure != "unknown":
            if structure not in self.logical_patterns:
                self.logical_patterns[structure] = []

            self.logical_patterns[structure].append(
                {
                    "experience_id": experience.id,
                    "context": experience.context,
                    "confidence": experience.confidence.value if experience.confidence else 0.0,
                    "timestamp": experience.timestamp.isoformat(),
                }
            )

            self.learning_progress.logical_patterns_learned = len(self.logical_patterns)
            logger.info(f"学习逻辑模式: {structure}, 总模式数: {len(self.logical_patterns)}")

    def _update_learning_progress(self, experience: LearningExperienceV4) -> Any:
        """更新学习进度 - v4.0版本"""
        self.learning_progress.total_experiences += 1

        if experience.reward > 0:
            self.learning_progress.successful_learnings += 1
        else:
            self.learning_progress.failed_learnings += 1

        # v4.0:更新证据分布
        if experience.evidence_quality:
            quality_str = experience.evidence_quality.value
            self.learning_progress.evidence_distribution[quality_str] = (
                self.learning_progress.evidence_distribution.get(quality_str, 0) + 1
            )

    async def get_action(
        self, context: dict[str, Any], possible_actions: list[Any], min_confidence: float = 0.5
    ) -> tuple[Any, Confidence]:
        """
        v4.0获取建议动作 - 基于证据和置信度

        Returns:
            (动作, 置信度)
        """
        # 获取相似经验
        similar_experiences = self.experience_store.get_similar_experiences(
            context, limit=10, min_confidence=min_confidence
        )

        if not similar_experiences:
            # 没有足够经验,返回低置信度
            confidence = self.uncertainty_quantifier.quantify(
                claim=f"在上下文 {context} 中,没有足够经验",
                evidence=["缺乏相似经验"],
                information_completeness=0.3,
            )

            # 随机选择动作
            import random

            action = random.choice(possible_actions) if possible_actions else None

            return action, confidence

        # v4.0:基于证据权重选择动作
        action_scores = defaultdict(float)
        action_confidences = defaultdict(list)

        for exp in similar_experiences:
            action_key = str(exp.action)
            if exp.reward > 0:
                # 基于奖励、置信度和证据权重计算分数
                evidence_weight = sum(
                    self.experience_store.evidence_weights.get(ev, 0.5) for ev in exp.evidence
                ) / max(len(exp.evidence), 1)

                conf_value = exp.confidence.value if exp.confidence else 0.5
                score = exp.reward * conf_value * evidence_weight
                action_scores[action_key] += score
                action_confidences[action_key].append(conf_value)

        # 选择最佳动作
        if action_scores:
            best_action_key = max(action_scores, key=action_scores.get)  # type: ignore
            best_score = action_scores[best_action_key]

            # 找到对应的动作
            best_action = None
            for action in possible_actions:
                if str(action) == best_action_key:
                    best_action = action
                    break

            if best_action is None:
                best_action = possible_actions[0]

            # v4.0:计算置信度
            avg_confidence = sum(action_confidences[best_action_key]) / len(
                action_confidences[best_action_key]
            )

            confidence = self.uncertainty_quantifier.quantify(
                claim=f"在上下文 {context} 中,选择动作 {best_action}",
                evidence=[
                    f"基于 {len(action_confidences[best_action_key])} 个相似经验",
                    f"平均分数: {best_score:.2f}",
                    f"历史成功率: {avg_confidence:.1%}",
                ],
                information_completeness=avg_confidence,
            )
            confidence.value = avg_confidence

            return best_action, confidence

        # 默认返回第一个动作
        default_confidence = self.uncertainty_quantifier.quantify(
            claim="使用默认动作", evidence=["缺乏有效经验"], information_completeness=0.4
        )

        return possible_actions[0] if possible_actions else None, default_confidence

    def get_learning_statistics(self) -> dict[str, Any]:
        """获取学习统计 - v4.0版本"""
        base_stats = {
            "total_experiences": self.learning_progress.total_experiences,
            "successful_learnings": self.learning_progress.successful_learnings,
            "failed_learnings": self.learning_progress.failed_learnings,
            "success_rate": (
                self.learning_progress.successful_learnings
                / self.learning_progress.total_experiences
                if self.learning_progress.total_experiences > 0
                else 0
            ),
            "logical_patterns_learned": self.learning_progress.logical_patterns_learned,
            "evidence_distribution": self.learning_progress.evidence_distribution,
        }

        # v4.0新增:证据质量分析
        total_evidence = sum(self.learning_progress.evidence_distribution.values())
        if total_evidence > 0:
            evidence_quality_analysis = {
                quality: count / total_evidence
                for quality, count in self.learning_progress.evidence_distribution.items()
            }
            base_stats["evidence_quality_analysis"] = evidence_quality_analysis

        # v4.0新增:逻辑模式分析
        if self.logical_patterns:
            base_stats["logical_pattern_breakdown"] = {
                structure: len(patterns) for structure, patterns in self.logical_patterns.items()
            }

        return base_stats

    def explain_learning(self, experience_id: str) -> str:
        """
        v4.0新增:解释学习过程

        这是v4.0的核心特性:透明化学习过程
        """
        for exp in self.experience_store.experiences:
            if exp.id == experience_id:
                explanation = "📊 学习经验解析 (v4.0)\n\n"
                explanation += f"🆔 经验ID: {exp.id}\n"
                explanation += f"📚 学习类型: {exp.type.value}\n"
                explanation += f"🎖️ 奖励: {exp.reward:.2f}\n\n"

                if exp.confidence:
                    explanation += f"📈 学习置信度: {exp.confidence.value:.1%} ({exp.confidence.level.value})\n"
                    explanation += "📋 支持证据:\n"
                    for i, evidence in enumerate(exp.evidence[:5], 1):
                        explanation += f"  {i}. {evidence}\n"

                    if exp.confidence.limitations:
                        explanation += "\n⚠️ 局限性:\n"
                        for lim in exp.confidence.limitations:
                            explanation += f"  • {lim}\n"

                explanation += f"\n🔬 证据质量: {exp.evidence_quality.value}\n"
                explanation += f"🧠 逻辑结构: {exp.logical_structure or '未知'}\n"
                explanation += f"🔒 学习边界内: {'是' if exp.learning_boundary else '否'}\n"

                return explanation

        return f"❌ 未找到经验: {experience_id}"

    def export_learning_report(self) -> str:
        """导出学习报告 - v4.0版本"""
        stats = self.get_learning_statistics()

        report = "=" * 80 + "\n"
        report += "📊 v4.0学习引擎报告\n"
        report += "基于维特根斯坦《逻辑哲学论》\n"
        report += "=" * 80 + "\n\n"

        report += "📈 学习统计:\n"
        report += f"  • 总经验数: {stats['total_experiences']}\n"
        report += f"  • 成功学习: {stats['successful_learnings']}\n"
        report += f"  • 失败学习: {stats['failed_learnings']}\n"
        report += f"  • 成功率: {stats['success_rate']:.1%}\n\n"

        report += "🧠 逻辑模式:\n"
        report += f"  • 学习的模式数: {stats['logical_patterns_learned']}\n"

        if "logical_pattern_breakdown" in stats:
            for structure, count in stats["logical_pattern_breakdown"].items():
                report += f"    - {structure}: {count}\n"
        report += "\n"

        report += "📋 证据分布:\n"
        for quality, count in stats.get("evidence_distribution", {}).items():
            report += f"  • {quality}: {count}\n"

        if "evidence_quality_analysis" in stats:
            report += "\n📊 证据质量分析:\n"
            for quality, ratio in stats["evidence_quality_analysis"].items():
                report += f"  • {quality}: {ratio:.1%}\n"

        report += "\n" + "=" * 80 + "\n"
        report += f"报告生成时间: {datetime.now().isoformat()}\n"

        return report


# 便捷函数
def get_learning_engine_v4() -> LearningEngineV4:
    """获取v4.0学习引擎实例"""
    return LearningEngineV4()


# 使用示例
async def main():
    """使用示例"""
    print("🧠 测试v4.0学习引擎(维特根斯坦版)...")

    learner = LearningEngineV4()

    # 示例1:可学习的技术内容
    print("\n" + "=" * 80)
    print("测试1:技术学习(可学习)")
    print("=" * 80)

    experience1 = await learner.learn_from_experience(
        context={"task": "code_review", "language": "python"},
        action="建议使用类型注解",
        result="代码可读性提升",
        reward=0.8,
        evidence=["类型注解提升代码可读性", "团队反馈积极"],
        evidence_quality=EvidenceQuality.HIGH,
    )

    print(f"✅ 学习成功: {experience1.id}")
    conf_value1 = experience1.confidence.value if experience1.confidence else 0.0
    print(f"   置信度: {conf_value1:.1%}")
    print(f"   逻辑结构: {experience1.logical_structure}")

    # 示例2:不可学习的领域
    print("\n" + "=" * 80)
    print("测试2:情感体验学习(不可学习)")
    print("=" * 80)

    experience2 = await learner.learn_from_experience(
        context={"task": "情感理解", "type": "subjective"},
        action="分析用户情感",
        result="情感分析完成",
        reward=0.5,
        evidence=["用户反馈"],
    )

    print(f"⚠️ 学习边界: {experience2.learning_boundary}")
    conf_value2 = experience2.confidence.value if experience2.confidence else 0.0
    print(f"   置信度: {conf_value2:.1%}")

    # 示例3:获取学习统计
    print("\n" + "=" * 80)
    print("学习统计报告")
    print("=" * 80)

    print(learner.export_learning_report())


# 入口点: @async_main装饰器已添加到main函数
