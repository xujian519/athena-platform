#!/usr/bin/env python3
from __future__ import annotations
"""
综合集成决策引擎
Integrated Decision Engine

基于钱学森"从定性到定量的综合集成法",
实现多轮迭代、多方意见综合的决策引擎。

核心思想:
1. 定性判断方向 - 确定分析思路
2. 定量分析评估 - 基于方向选择方法
3. 综合集成迭代 - 多轮讨论达成共识
4. 形成定量结论 - 输出明确决策

作者: 小诺·双鱼公主
创建时间: 2025-12-27
版本: v1.0.0 "综合集成"
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class DirectionType(Enum):
    """定性方向类型"""

    TECHNICAL = "技术分析"  # 技术方案评估
    LEGAL = "法律分析"  # 法律风险分析
    BUSINESS = "商业分析"  # 商业价值分析
    SYSTEM = "系统分析"  # 系统整体分析
    INTEGRATED = "综合分析"  # 多维度综合


class ConsensusLevel(Enum):
    """共识等级"""

    CONSENSUS = "共识"  # 完全一致
    COMPATIBLE = "兼容"  # 可以兼容
    CONFLICT = "冲突"  # 存在冲突
    DIVERGENCE = "分歧"  # 根本分歧


@dataclass
class QualitativeDirection:
    """定性判断方向"""

    direction: DirectionType
    reasoning: str
    confidence: float
    suggested_agents: list[str]
    analysis_framework: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AgentOpinion:
    """智能体意见"""

    agent_name: str
    opinion: str
    confidence: float
    evidence: list[str]
    reasoning: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ConflictAnalysis:
    """冲突分析"""

    has_conflict: bool
    conflict_type: ConsensusLevel
    conflicting_parties: list[str]
    conflict_points: list[str]
    resolution_strategy: str


@dataclass
class IntegrationResult:
    """综合集成结果"""

    iteration: int
    consensus_level: ConsensusLevel
    integrated_conclusion: str
    confidence: float
    supporting_reasons: list[str]
    remaining_divergences: list[str]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Decision:
    """最终决策"""

    task_id: str
    task_description: str

    # 定性判断
    qualitative_direction: QualitativeDirection

    # 智能体意见
    agent_opinions: list[AgentOpinion]

    # 综合集成过程
    integration_iterations: list[IntegrationResult]

    # 最终结论
    final_conclusion: str
    final_confidence: float
    decision_basis: str

    # 决策元数据
    decision_made_at: str = field(default_factory=lambda: datetime.now().isoformat())
    decision_methodology: str = "从定性到定量的综合集成法"


class IntegratedDecisionEngine:
    """
    综合集成决策引擎

    实现钱学森"从定性到定量的综合集成法"
    """

    def __init__(self):
        """初始化决策引擎"""
        self.name = "综合集成决策引擎"
        self.version = "v1.0.0"

        # 决策历史(用于学习和优化)
        self.decision_history: list[Decision] = []

        # 决策规则库
        self.decision_rules = self._init_decision_rules()

        logger.info(f"🧠 {self.name} ({self.version}) 初始化完成")
        logger.info("   ✅ 综合集成法:就绪")
        logger.info("   ✅ 多轮迭代:就绪")
        logger.info("   ✅ 冲突仲裁:就绪")

    def _init_decision_rules(self) -> dict[str, Any]:
        """初始化决策规则库"""
        return {
            "consensus_threshold": 0.75,  # 共识阈值
            "max_iterations": 3,  # 最大迭代次数
            "confidence_weight": {"high": 0.9, "medium": 0.7, "low": 0.5},  # 高置信度权重
            "direction_mappings": {
                "技术": DirectionType.TECHNICAL,
                "技术方案": DirectionType.TECHNICAL,
                "架构": DirectionType.TECHNICAL,
                "法律": DirectionType.LEGAL,
                "专利": DirectionType.LEGAL,
                "风险": DirectionType.LEGAL,
                "商业": DirectionType.BUSINESS,
                "成本": DirectionType.BUSINESS,
                "系统": DirectionType.SYSTEM,
                "整体": DirectionType.SYSTEM,
            },
        }

    async def make_decision(
        self,
        task_id: str,
        task_description: str,
        agent_opinions: list[AgentOpinion],
        context: dict[str, Any] | None = None,
    ) -> Decision:
        """
        做出综合集成决策

        Args:
            task_id: 任务ID
            task_description: 任务描述
            agent_opinions: 各智能体的意见
            context: 上下文信息

        Returns:
            Decision: 最终决策
        """
        logger.info(f"🎯 开始综合集成决策: {task_id}")
        logger.info(f"   任务描述: {task_description}")
        logger.info(f"   参与智能体: {[op.agent_name for op in agent_opinions]}")

        # 第1步:定性判断方向
        logger.info("\n[第1步]定性判断方向...")
        qualitative_direction = await self._qualitative_assess_direction(
            task_description, agent_opinions, context
        )
        logger.info(f"   方向: {qualitative_direction.direction.value}")
        logger.info(f"   理由: {qualitative_direction.reasoning}")

        # 第2步:分析智能体意见
        logger.info("\n[第2步]分析智能体意见...")
        for opinion in agent_opinions:
            logger.info(f"   {opinion.agent_name}: {opinion.opinion}")
            logger.info(f"     置信度: {opinion.confidence}, 证据: {len(opinion.evidence)}条")

        # 第3步:检测冲突
        logger.info("\n[第3步]检测意见冲突...")
        conflict_analysis = await self._detect_conflicts(agent_opinions)
        logger.info(f"   冲突状态: {conflict_analysis.conflict_type.value}")

        # 第4步:综合集成迭代
        logger.info("\n[第4步]综合集成迭代...")
        integration_iterations = []

        for iteration in range(1, self.decision_rules["max_iterations"] + 1):
            logger.info(f"\n   第{iteration}轮迭代...")

            iteration_result = await self._integrate_iteration(
                iteration,
                qualitative_direction,
                agent_opinions,
                conflict_analysis,
                integration_iterations,
            )

            integration_iterations.append(iteration_result)
            logger.info(f"   共识等级: {iteration_result.consensus_level.value}")
            logger.info(f"   当前提论: {iteration_result.integrated_conclusion.get('')[:100]}...")

            # 检查是否达成足够共识
            if iteration_result.consensus_level in [
                ConsensusLevel.CONSENSUS,
                ConsensusLevel.COMPATIBLE,
            ]:
                logger.info(f"\n   ✅ 第{iteration}轮达成共识,停止迭代")
                break

            # 如果有冲突,进行冲突解决
            if conflict_analysis.has_conflict:
                logger.info("\n   ⚠️ 检测到冲突,启动冲突解决...")
                agent_opinions = await self._resolve_conflicts(agent_opinions, conflict_analysis)
                # 重新分析冲突
                conflict_analysis = await self._detect_conflicts(agent_opinions)

        # 第5步:形成最终决策
        logger.info("\n[第5步]形成最终决策...")
        final_decision = await self._form_final_decision(
            task_id, task_description, qualitative_direction, agent_opinions, integration_iterations
        )

        # 记录决策历史
        self.decision_history.append(final_decision)

        logger.info("\n✅ 综合集成决策完成")
        logger.info(f"   最终结论: {final_decision.final_conclusion}")
        logger.info(f"   置信度: {final_decision.final_confidence}%")
        logger.info("=" * 70)

        return final_decision

    async def _qualitative_assess_direction(
        self, task_description: str, agent_opinions: list[AgentOpinion], context: dict[str, Any]
    ) -> QualitativeDirection:
        """
        第1步:定性判断方向

        基于任务描述和智能体意见,判断问题的性质和方向
        """
        # 分析任务关键词,确定方向
        direction = self._determine_direction(task_description)

        # 确定需要的智能体
        suggested_agents = [op.agent_name for op in agent_opinions]

        # 选择分析框架
        analysis_framework = self._select_analysis_framework(direction)

        # 形成定性判断理由
        reasoning = f"""根据任务描述"{task_description[:50]}...",
这个问题属于{direction.value}范畴。
建议采用{analysis_framework}进行分析。
"""

        return QualitativeDirection(
            direction=direction,
            reasoning=reasoning,
            confidence=0.8,
            suggested_agents=suggested_agents,
            analysis_framework=analysis_framework,
        )

    def _determine_direction(self, task_description: str) -> DirectionType:
        """根据任务描述确定方向"""
        desc_lower = task_description.lower()

        # 关键词匹配
        for keyword, direction in self.decision_rules["direction_mappings"].items():
            if keyword in desc_lower:
                return direction

        # 默认使用综合分析
        return DirectionType.INTEGRATED

    def _select_analysis_framework(self, direction: DirectionType) -> str:
        """选择分析框架"""
        frameworks = {
            DirectionType.TECHNICAL: "技术可行性分析框架",
            DirectionType.LEGAL: "法律合规性分析框架",
            DirectionType.BUSINESS: "商业价值分析框架",
            DirectionType.SYSTEM: "系统工程分析框架",
            DirectionType.INTEGRATED: "多维度综合分析框架",
        }
        return frameworks.get(direction, "通用分析框架")

    async def _detect_conflicts(self, agent_opinions: list[AgentOpinion]) -> ConflictAnalysis:
        """
        检测智能体意见的冲突
        """
        if len(agent_opinions) < 2:
            return ConflictAnalysis(
                has_conflict=False,
                conflict_type=ConsensusLevel.CONSENSUS,
                conflicting_parties=[],
                conflict_points=[],
                resolution_strategy="无需解决",
            )

        # 简化的冲突检测:基于置信度差异和内容关键词
        confidences = [op.confidence for op in agent_opinions]
        max_conf = max(confidences)
        min_conf = min(confidences)

        # 如果置信度差异太大,可能存在冲突
        if max_conf - min_conf > 0.3:
            return ConflictAnalysis(
                has_conflict=True,
                conflict_type=ConsensusLevel.CONFLICT,
                conflicting_parties=[
                    op.agent_name
                    for op in agent_opinions
                    if op.confidence == min_conf or op.confidence == max_conf
                ],
                conflict_points=["置信度差异较大"],
                resolution_strategy="启动辩论机制,要求双方补充证据",
            )

        # 检查意见内容是否有矛盾关键词
        opinion_texts = [op.opinion.lower() for op in agent_opinions]
        conflict_keywords = ["但是", "然而", "相反", "不同意", "风险", "问题"]

        has_contradiction = any(
            any(kw in text for kw in conflict_keywords) for text in opinion_texts
        )

        if has_contradiction:
            return ConflictAnalysis(
                has_conflict=True,
                conflict_type=ConsensusLevel.CONFLICT,
                conflicting_parties=[op.agent_name for op in agent_opinions],
                conflict_points=["意见表述存在潜在冲突"],
                resolution_strategy="深入分析,识别真实分歧点",
            )

        # 默认认为兼容
        return ConflictAnalysis(
            has_conflict=False,
            conflict_type=ConsensusLevel.COMPATIBLE,
            conflicting_parties=[],
            conflict_points=[],
            resolution_strategy="无需特殊处理",
        )

    async def _integrate_iteration(
        self,
        iteration_num: int,
        direction: QualitativeDirection,
        opinions: list[AgentOpinion],
        conflict: ConflictAnalysis,
        previous_iterations: list[IntegrationResult],
    ) -> IntegrationResult:
        """
        综合集成迭代
        """
        # 计算平均置信度
        avg_confidence = sum(op.confidence for op in opinions) / len(opinions)

        # 收集所有理由
        all_reasons = []
        for op in opinions:
            all_reasons.append(f"{op.agent_name}: {op.reasoning}")

        # 形成综合结论
        if conflict.has_conflict:
            # 有冲突时,综合结论需要平衡各方
            integrated_conclusion = f"""综合各智能体意见,考虑{conflict.conflicting_parties}等不同观点,
本问题需要平衡多方面因素。
{direction.direction.value}分析显示,平均置信度为{avg_confidence:.1%}。
建议采取折中方案,综合考虑各方关切。"""
            consensus_level = conflict.conflict_type
            remaining_divergences = conflict.conflict_points
        else:
            # 无冲突时,可以形成更强的结论
            integrated_conclusion = f"""各智能体意见基本一致,{direction.direction.value}分析结论明确。
综合置信度达到{avg_confidence:.1%}。
可以基于{direction.analysis_framework}形成决策。"""
            consensus_level = ConsensusLevel.CONSENSUS
            remaining_divergences = []

        return IntegrationResult(
            iteration=iteration_num,
            consensus_level=consensus_level,
            integrated_conclusion=integrated_conclusion,
            confidence=avg_confidence,
            supporting_reasons=all_reasons,
            remaining_divergences=remaining_divergences,
        )

    async def _resolve_conflicts(
        self, opinions: list[AgentOpinion], conflict: ConflictAnalysis
    ) -> list[AgentOpinion]:
        """
        解决冲突
        """
        # 简化的冲突解决:要求置信度低的智能体补充证据
        resolved_opinions = []

        for op in opinions:
            if op.agent_name in conflict.conflicting_parties and op.confidence < 0.7:
                # 模拟要求补充证据(实际应该调用智能体补充)
                resolved_op = AgentOpinion(
                    agent_name=op.agent_name,
                    opinion=op.opinion + " [经补充证据后]",
                    confidence=min(op.confidence + 0.1, 1.0),
                    evidence=[*op.evidence, "补充的新证据"],
                    reasoning=op.reasoning + " 考虑到其他观点后,我调整了判断。",
                )
                resolved_opinions.append(resolved_op)
            else:
                resolved_opinions.append(op)

        return resolved_opinions

    async def _form_final_decision(
        self,
        task_id: str,
        task_description: str,
        direction: QualitativeDirection,
        opinions: list[AgentOpinion],
        iterations: list[IntegrationResult],
    ) -> Decision:
        """
        形成最终决策
        """
        # 取最后一次迭代的结果
        final_iteration = iterations[-1] if iterations else None

        if final_iteration:
            final_conclusion = final_iteration.integrated_conclusion
            final_confidence = final_iteration.confidence
            decision_basis = (
                f"经过{len(iterations)}轮迭代,{final_iteration.consensus_level.value}等级"
            )
        else:
            final_conclusion = "未能形成有效综合结论"
            final_confidence = 0.0
            decision_basis = "综合集成失败"

        return Decision(
            task_id=task_id,
            task_description=task_description,
            qualitative_direction=direction,
            agent_opinions=opinions,
            integration_iterations=iterations,
            final_conclusion=final_conclusion,
            final_confidence=final_confidence,
            decision_basis=decision_basis,
        )

    def get_decision_statistics(self) -> dict[str, Any]:
        """获取决策统计信息"""
        if not self.decision_history:
            return {"total_decisions": 0}

        total = len(self.decision_history)
        avg_confidence = sum(d.final_confidence for d in self.decision_history) / total

        consensus_distribution = {}
        for decision in self.decision_history:
            if decision.integration_iterations:
                level = decision.integration_iterations[-1].consensus_level.value
                consensus_distribution[level] = consensus_distribution.get(level, 0) + 1

        return {
            "total_decisions": total,
            "average_confidence": avg_confidence,
            "consensus_distribution": consensus_distribution,
            "latest_decision": (
                self.decision_history[-1].decision_made_at if self.decision_history else None
            ),
        }


# 全局实例
_engine: IntegratedDecisionEngine | None = None


def get_decision_engine() -> IntegratedDecisionEngine:
    """获取决策引擎单例"""
    global _engine
    if _engine is None:
        _engine = IntegratedDecisionEngine()
    return _engine


# 便捷函数
async def make_integrated_decision(
    task_id: str,
    task_description: str,
    agent_opinions: list[AgentOpinion],
    context: dict[str, Any] | None = None,
) -> Decision:
    """便捷函数:做出综合集成决策"""
    engine = get_decision_engine()
    return await engine.make_decision(task_id, task_description, agent_opinions, context)


if __name__ == "__main__":

    async def test():
        """测试综合集成决策引擎"""
        print("🧪 测试综合集成决策引擎")
        print("=" * 70)

        # 模拟场景:技术选型决策
        task_id = "task_001"
        task_description = "选择专利检索系统的向量数据库方案"

        # 模拟两个智能体的意见
        opinions = [
            AgentOpinion(
                agent_name="小娜",
                opinion="建议使用Qdrant,因为它在专利检索场景下性能更好",
                confidence=0.85,
                evidence=["Qdrant在相似度搜索上表现优秀", "社区活跃"],
                reasoning="基于专利检索的专业需求,Qdrant更适合",
            ),
            AgentOpinion(
                agent_name="Athena",
                opinion="建议使用PostgreSQL+pgvector,因为技术栈统一",
                confidence=0.75,
                evidence=["减少技术栈复杂度", "维护成本更低"],
                reasoning="考虑到运维成本,统一技术栈更明智",
            ),
        ]

        # 做出决策
        decision = await make_integrated_decision(task_id, task_description, opinions)

        # 输出结果
        print("\n" + "=" * 70)
        print("📊 决策结果")
        print("=" * 70)
        print(f"任务: {decision.task_description}")
        print(f"\n定性方向: {decision.qualitative_direction.direction.value}")
        print("\n各智能体意见:")
        for op in decision.agent_opinions:
            print(f"  - {op.agent_name}: {op.opinion}")
            print(f"    置信度: {op.confidence}")
        print("\n综合集成过程:")
        for iteration in decision.integration_iterations:
            print(f"  第{iteration.iteration}轮:")
            print(f"    共识等级: {iteration.consensus_level.value}")
            print(f"    置信度: {iteration.confidence:.2%}")
        print(f"\n最终决策: {decision.final_conclusion}")
        print(f"置信度: {decision.final_confidence:.2%}")
        print(f"决策依据: {decision.decision_basis}")
        print("=" * 70)

        # 统计信息
        stats = get_decision_engine().get_decision_statistics()
        print(f"\n📈 决策统计: {stats}")

    asyncio.run(test())
