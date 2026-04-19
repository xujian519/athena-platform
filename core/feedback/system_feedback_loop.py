#!/usr/bin/env python3
from __future__ import annotations
"""
系统反馈闭环
System Feedback Loop

实现钱学森"实践-认识-再实践"的思想,
建立系统的反馈闭环机制:
- 效果评估
- 问题诊断
- 改进应用
- 知识积累

作者: 小诺·双鱼公主
创建时间: 2025-12-27
版本: v1.0.0 "反馈闭环"
"""

import asyncio
import logging

# 添加项目路径
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.decision.integrated_decision_engine import Decision

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class EffectivenessLevel(Enum):
    """效果等级"""

    EXCELLENT = "优秀"
    GOOD = "良好"
    SATISFACTORY = "满意"
    NEEDS_IMPROVEMENT = "需改进"
    POOR = "差"


class ImprovementType(Enum):
    """改进类型"""

    RULE_ADJUSTMENT = "规则调整"
    METHOD_REFINEMENT = "方法优化"
    MODEL_RETRAINING = "模型重训练"
    KNOWLEDGE_UPDATE = "知识更新"
    CONFIG_CHANGE = "配置变更"


@dataclass
class ExecutionResult:
    """执行结果"""

    decision_id: str
    executed_at: str
    execution_time_seconds: float
    success: bool
    user_satisfaction: float | None = None  # 0.0-1.0
    actual_outcome: str | None = None
    resource_usage: dict[str, Any] = field(default_factory=dict)


@dataclass
class EffectivenessAssessment:
    """效果评估"""

    decision_id: str
    effectiveness_level: EffectivenessLevel
    score: float  # 0.0-1.0
    strengths: list[str]
    weaknesses: list[str]
    assessment_time: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ProblemDiagnosis:
    """问题诊断"""

    decision_id: str
    problems_identified: list[str]
    root_causes: list[str]
    suggested_improvements: list[ImprovementType]
    urgency: str  # low, medium, high
    diagnosis_time: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ImprovementAction:
    """改进行动"""

    action_id: str
    improvement_type: ImprovementType
    description: str
    target_component: str
    applied: bool = False
    applied_at: str | None = None
    result: str | None = None


@dataclass
class LearningRecord:
    """学习记录"""

    record_id: str
    decision_id: str
    lesson_learned: str
    best_practice: str | None = None
    avoidance_pattern: str | None = None
    knowledge_category: str = "general"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class SystemFeedbackLoop:
    """
    系统反馈闭环

    实现"实践-认识-再实践"的持续优化循环
    """

    def __init__(self):
        """初始化反馈闭环"""
        self.name = "系统反馈闭环"
        self.version = "v1.0.0"

        # 存储
        self.execution_history: list[ExecutionResult] = []
        self.effectiveness_records: list[EffectivenessAssessment] = []
        self.problem_diagnoses: list[ProblemDiagnosis] = []
        self.improvement_actions: list[ImprovementAction] = []
        self.learning_records: list[LearningRecord] = []

        # 评估标准
        self.evaluation_criteria = self._init_evaluation_criteria()

        logger.info(f"🔄 {self.name} ({self.version}) 初始化完成")
        logger.info("   ✅ 效果评估: 就绪")
        logger.info("   ✅ 问题诊断: 就绪")
        logger.info("   ✅ 改进应用: 就绪")
        logger.info("   ✅ 知识积累: 就绪")

    def _init_evaluation_criteria(self) -> dict[str, Any]:
        """初始化评估标准"""
        return {
            "satisfaction_weight": 0.4,
            "success_weight": 0.3,
            "efficiency_weight": 0.2,
            "resource_weight": 0.1,
            "thresholds": {
                "excellent": 0.9,
                "good": 0.75,
                "satisfactory": 0.6,
                "needs_improvement": 0.4,
            },
        }

    async def record_execution(
        self,
        decision: Decision,
        execution_time: float,
        success: bool,
        user_satisfaction: float | None = None,
        actual_outcome: str | None = None,
        resource_usage: dict[str, Any] | None = None,
    ) -> ExecutionResult:
        """
        记录决策执行结果

        Args:
            decision: 执行的决策
            execution_time: 执行耗时(秒)
            success: 是否成功
            user_satisfaction: 用户满意度(0-1)
            actual_outcome: 实际结果
            resource_usage: 资源使用情况

        Returns:
            ExecutionResult: 执行结果记录
        """
        execution_result = ExecutionResult(
            decision_id=decision.task_id,
            executed_at=datetime.now().isoformat(),
            execution_time_seconds=execution_time,
            success=success,
            user_satisfaction=user_satisfaction,
            actual_outcome=actual_outcome,
            resource_usage=resource_usage or {},
        )

        self.execution_history.append(execution_result)

        logger.info(f"📝 记录执行结果: {decision.task_id}")
        logger.info(f"   成功: {success}, 满意度: {user_satisfaction}")

        # 触发效果评估
        await self.assess_effectiveness(execution_result, decision)

        return execution_result

    async def assess_effectiveness(
        self, execution: ExecutionResult, decision: Decision
    ) -> EffectivenessAssessment:
        """
        评估决策效果

        Args:
            execution: 执行结果
            decision: 原决策

        Returns:
            EffectivenessAssessment: 效果评估
        """
        logger.info(f"📊 评估效果: {execution.decision_id}")

        # 计算综合得分
        criteria = self.evaluation_criteria

        # 成功得分
        success_score = 1.0 if execution.success else 0.3

        # 满意度得分
        satisfaction_score = execution.user_satisfaction or 0.7

        # 效率得分(假设30秒为基准)
        efficiency_score = max(0, 1 - execution.execution_time_seconds / 60)

        # 资源使用得分
        resource_score = 0.8  # 简化处理

        # 加权综合得分
        overall_score = (
            success_score * criteria["success_weight"]
            + satisfaction_score * criteria["satisfaction_weight"]
            + efficiency_score * criteria["efficiency_weight"]
            + resource_score * criteria["resource_weight"]
        )

        # 确定效果等级
        thresholds = criteria["thresholds"]
        if overall_score >= thresholds["excellent"]:
            level = EffectivenessLevel.EXCELLENT
        elif overall_score >= thresholds["good"]:
            level = EffectivenessLevel.GOOD
        elif overall_score >= thresholds["satisfactory"]:
            level = EffectivenessLevel.SATISFACTORY
        elif overall_score >= thresholds["needs_improvement"]:
            level = EffectivenessLevel.NEEDS_IMPROVEMENT
        else:
            level = EffectivenessLevel.POOR

        # 分析优缺点
        strengths = []
        weaknesses = []

        if execution.success:
            strengths.append("决策执行成功")
        else:
            weaknesses.append("决策执行失败")

        if execution.user_satisfaction and execution.user_satisfaction >= 0.8:
            strengths.append("用户满意度高")
        elif execution.user_satisfaction and execution.user_satisfaction < 0.6:
            weaknesses.append("用户满意度低")

        if decision.final_confidence >= 0.8:
            strengths.append("决策置信度高")
        else:
            weaknesses.append("决策置信度较低,可能需要更多支持")

        assessment = EffectivenessAssessment(
            decision_id=execution.decision_id,
            effectiveness_level=level,
            score=overall_score,
            strengths=strengths,
            weaknesses=weaknesses,
        )

        self.effectiveness_records.append(assessment)

        logger.info(f"   效果等级: {level.value}")
        logger.info(f"   综合得分: {overall_score:.2%}")
        logger.info(f"   优势: {len(strengths)}项, 劣势: {len(weaknesses)}项")

        # 如果效果不佳,触发问题诊断
        if level in [EffectivenessLevel.NEEDS_IMPROVEMENT, EffectivenessLevel.POOR]:
            await self.diagnose_problems(assessment, decision)

        return assessment

    async def diagnose_problems(
        self, assessment: EffectivenessAssessment, decision: Decision
    ) -> ProblemDiagnosis:
        """
        诊断问题

        Args:
            assessment: 效果评估
            decision: 原决策

        Returns:
            ProblemDiagnosis: 问题诊断
        """
        logger.info(f"🔍 诊断问题: {assessment.decision_id}")

        problems = []
        root_causes = []
        improvements = []

        # 基于劣势分析问题
        for weakness in assessment.weaknesses:
            if "失败" in weakness:
                problems.append("决策执行失败")
                root_causes.append("可能存在执行障碍或资源不足")
                improvements.append(ImprovementType.METHOD_REFINEMENT)

            if "满意度低" in weakness:
                problems.append("用户不满意")
                root_causes.append("决策方向可能与用户期望不符")
                improvements.append(ImprovementType.RULE_ADJUSTMENT)

            if "置信度低" in weakness:
                problems.append("决策置信度不足")
                root_causes.append("信息不完整或分析方法不当")
                improvements.append(ImprovementType.KNOWLEDGE_UPDATE)

        # 分析决策过程
        if decision.final_confidence < 0.6:
            problems.append("决策质量偏低")
            root_causes.append("综合集成过程可能需要优化")
            improvements.append(ImprovementType.METHOD_REFINEMENT)

        # 确定紧急程度
        if assessment.score < 0.4:
            urgency = "high"
        elif assessment.score < 0.6:
            urgency = "medium"
        else:
            urgency = "low"

        diagnosis = ProblemDiagnosis(
            decision_id=assessment.decision_id,
            problems_identified=problems,
            root_causes=root_causes,
            suggested_improvements=improvements,
            urgency=urgency,
        )

        self.problem_diagnoses.append(diagnosis)

        logger.info(f"   识别问题: {len(problems)}个")
        logger.info(f"   紧急程度: {urgency}")

        # 触发改进应用
        for improvement_type in improvements:
            await self.apply_improvement(diagnosis, improvement_type)

        return diagnosis

    async def apply_improvement(
        self, diagnosis: ProblemDiagnosis, improvement_type: ImprovementType
    ) -> ImprovementAction:
        """
        应用改进

        Args:
            diagnosis: 问题诊断
            improvement_type: 改进类型

        Returns:
            ImprovementAction: 改进行动
        """
        action_id = f"improvement_{int(datetime.now().timestamp())}"

        # 根据改进类型生成具体行动
        if improvement_type == ImprovementType.RULE_ADJUSTMENT:
            description = "调整决策规则以提升效果"
            target_component = "decision_engine"

        elif improvement_type == ImprovementType.METHOD_REFINEMENT:
            description = "优化综合集成方法"
            target_component = "integration_method"

        elif improvement_type == ImprovementType.KNOWLEDGE_UPDATE:
            description = "更新知识库和规则"
            target_component = "knowledge_base"

        else:
            description = f"应用{improvement_type}改进"
            target_component = "general"

        action = ImprovementAction(
            action_id=action_id,
            improvement_type=improvement_type,
            description=description,
            target_component=target_component,
            applied=True,
            applied_at=datetime.now().isoformat(),
            result="改进已应用,等待验证",
        )

        self.improvement_actions.append(action)

        logger.info(f"🔧 应用改进: {description}")
        logger.info(f"   类型: {improvement_type.value}")

        # 记录学习
        await self.record_learning(diagnosis, action)

        return action

    async def record_learning(
        self, diagnosis: ProblemDiagnosis, action: ImprovementAction
    ) -> LearningRecord:
        """
        记录学习

        将经验教训转化为系统知识
        """
        record_id = f"learning_{int(datetime.now().timestamp())}"

        # 提取经验教训
        lesson = f"""问题: {', '.join(diagnosis.problems_identified)}
原因: {', '.join(diagnosis.root_causes)}
改进: {action.description}
"""

        # 识别最佳实践(如果是优秀案例)
        best_practice = None
        if diagnosis.urgency == "low":
            best_practice = f"成功的决策模式: {action.description}"

        # 识别应避免的模式
        avoidance_pattern = None
        if diagnosis.urgency in ["high", "medium"]:
            avoidance_pattern = f"应避免: {', '.join(diagnosis.root_causes)}"

        # 确定知识类别
        if "规则" in action.description:
            category = "decision_rule"
        elif "方法" in action.description:
            category = "methodology"
        elif "知识" in action.description:
            category = "knowledge"
        else:
            category = "general"

        learning = LearningRecord(
            record_id=record_id,
            decision_id=diagnosis.decision_id,
            lesson_learned=lesson,
            best_practice=best_practice,
            avoidance_pattern=avoidance_pattern,
            knowledge_category=category,
        )

        self.learning_records.append(learning)

        logger.info(f"💡 记录学习: {record_id}")
        logger.info(f"   类别: {category}")

        return learning

    def get_feedback_statistics(self) -> dict[str, Any]:
        """获取反馈闭环统计"""
        total_executions = len(self.execution_history)
        if total_executions == 0:
            return {"status": "no_data"}

        avg_score = sum(e.score for e in self.effectiveness_records) / len(
            self.effectiveness_records
        )

        effectiveness_dist = {}
        for record in self.effectiveness_records:
            level = record.effectiveness_level.value
            effectiveness_dist[level] = effectiveness_dist.get(level, 0) + 1

        return {
            "total_executions": total_executions,
            "average_effectiveness_score": avg_score,
            "effectiveness_distribution": effectiveness_dist,
            "total_improvements": len(self.improvement_actions),
            "total_learnings": len(self.learning_records),
        }

    def get_recent_learnings(
        self, category: str | None = None, limit: int = 5
    ) -> list[LearningRecord]:
        """获取最近的学习记录"""
        learnings = self.learning_records

        if category:
            learnings = [l for l in learnings if l.knowledge_category == category]

        return learnings[-limit:]


# 全局实例
_feedback_loop: SystemFeedbackLoop | None = None


def get_feedback_loop() -> SystemFeedbackLoop:
    """获取反馈闭环单例"""
    global _feedback_loop
    if _feedback_loop is None:
        _feedback_loop = SystemFeedbackLoop()
    return _feedback_loop


# 便捷函数
async def record_and_learn(
    decision: Decision,
    execution_time: float,
    success: bool,
    user_satisfaction: float | None = None,
) -> EffectivenessAssessment:
    """便捷函数:记录执行并触发学习闭环"""
    loop = get_feedback_loop()
    await loop.record_execution(decision, execution_time, success, user_satisfaction)
    # 评估已经在record_execution中触发
    assessment = next(
        (e for e in loop.effectiveness_records if e.decision_id == decision.task_id), None
    )
    return assessment


if __name__ == "__main__":

    async def test():
        """测试系统反馈闭环"""
        print("🧪 测试系统反馈闭环")
        print("=" * 70)

        # 创建测试决策
        from core.decision.integrated_decision_engine import (
            ConsensusLevel,
            Decision,
            DirectionType,
            IntegrationResult,
            QualitativeDirection,
        )

        test_decision = Decision(
            task_id="test_001",
            task_description="测试决策",
            qualitative_direction=QualitativeDirection(
                direction=DirectionType.TECHNICAL,
                reasoning="测试",
                confidence=0.8,
                suggested_agents=[],
                analysis_framework="测试",
            ),
            agent_opinions=[],
            integration_iterations=[
                IntegrationResult(
                    iteration=1,
                    consensus_level=ConsensusLevel.CONSENSUS,
                    integrated_conclusion="测试结论",
                    confidence=0.85,
                    supporting_reasons=[],
                    remaining_divergences=[],
                )
            ],
            final_conclusion="这是一个测试决策",
            final_confidence=0.85,
            decision_basis="测试",
        )

        # 测试1:记录执行并评估
        print("\n📝 测试1: 记录执行并评估效果")
        loop = get_feedback_loop()

        # 模拟一个成功的执行
        assessment1 = await record_and_learn(
            decision=test_decision, execution_time=15.5, success=True, user_satisfaction=0.9
        )
        print(f"   效果等级: {assessment1.effectiveness_level.value}")
        print(f"   得分: {assessment1.score:.2%}")

        # 测试2:模拟一个不理想的执行
        print("\n📝 测试2: 记录不理想的执行")
        assessment2 = await record_and_learn(
            decision=test_decision, execution_time=45.0, success=False, user_satisfaction=0.5
        )
        print(f"   效果等级: {assessment2.effectiveness_level.value}")
        print(f"   得分: {assessment2.score:.2%}")

        # 测试3:查看统计
        print("\n📊 测试3: 反馈闭环统计")
        stats = loop.get_feedback_statistics()
        print(f"   总执行次数: {stats['total_executions']}")
        print(f"   平均得分: {stats['average_effectiveness_score']:.2%}")
        print(f"   效果分布: {stats['effectiveness_distribution']}")
        print(f"   改进次数: {stats['total_improvements']}")
        print(f"   学习记录: {stats['total_learnings']}")

        # 测试4:查看学习记录
        print("\n💡 测试4: 学习记录")
        learnings = loop.get_recent_learnings(limit=3)
        for i, learning in enumerate(learnings, 1):
            print(f"\n学习{i}:")
            print(f"  经验教训: {learning.lesson_learned[:100]}...")
            if learning.best_practice:
                print(f"  最佳实践: {learning.best_practice}")
            if learning.avoidance_pattern:
                print(f"  避免模式: {learning.avoidance_pattern}")

    asyncio.run(test())
