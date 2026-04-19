#!/usr/bin/env python3
from __future__ import annotations
"""
风险预测模块
Risk Predictor

功能:
1. 预测方案执行风险
2. 识别潜在失败点
3. 提供风险缓解建议
4. 计算综合风险评分

Author: Athena Team
Version: 1.0.0
Date: 2026-02-24
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .xiaonuo_planner_engine import ExecutionPlan, ExecutionStep, Risk

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"  # 低风险 (0-0.3)
    MEDIUM = "medium"  # 中风险 (0.3-0.6)
    HIGH = "high"  # 高风险 (0.6-0.8)
    CRITICAL = "critical"  # 严重风险 (0.8-1.0)


@dataclass
class RiskAssessment:
    """风险评估结果"""
    plan_id: str
    overall_risk: RiskLevel
    overall_score: float  # 0-1
    risks: list[Risk]
    mitigation_suggestions: list[str]
    risk_breakdown: dict[str, float] = field(default_factory=dict)


class RiskPredictor:
    """
    风险预测器

    核心功能:
    1. 多维度风险识别
    2. 风险等级评估
    3. 缓解措施生成
    """

    # 风险类别权重
    TIME_RISK_WEIGHT = 0.3
    RESOURCE_RISK_WEIGHT = 0.3
    DEPENDENCY_RISK_WEIGHT = 0.2
    COMPLEXITY_RISK_WEIGHT = 0.2

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.assessment_history: list[RiskAssessment] = []

    def predict(
        self,
        plan: ExecutionPlan,
        context: dict[str, Any] | None = None
    ) -> RiskAssessment:
        """
        预测方案风险

        Args:
            plan: 执行方案
            context: 上下文信息

        Returns:
            RiskAssessment: 风险评估结果
        """
        self.logger.info(f"⚠️ 预测风险: {plan.plan_id}")

        # 1. 识别各类风险
        risks = []

        # 时间风险
        time_risks = self._assess_time_risks(plan)
        risks.extend(time_risks)

        # 资源风险
        resource_risks = self._assess_resource_risks(plan)
        risks.extend(resource_risks)

        # 依赖风险
        dependency_risks = self._assess_dependency_risks(plan)
        risks.extend(dependency_risks)

        # 复杂度风险
        complexity_risks = self._assess_complexity_risks(plan)
        risks.extend(complexity_risks)

        # 2. 计算综合风险评分
        overall_score = self._calculate_overall_risk(risks, plan)

        # 3. 确定风险等级
        overall_risk = self._determine_risk_level(overall_score)

        # 4. 生成缓解建议
        mitigation_suggestions = self._generate_mitigation_suggestions(risks, overall_risk)

        # 5. 创建评估结果
        assessment = RiskAssessment(
            plan_id=plan.plan_id,
            overall_risk=overall_risk,
            overall_score=overall_score,
            risks=risks,
            mitigation_suggestions=mitigation_suggestions,
            risk_breakdown={
                "time_risk": sum(r.probability for r in time_risks) if time_risks else 0,
                "resource_risk": sum(r.probability for r in resource_risks) if resource_risks else 0,
                "dependency_risk": sum(r.probability for r in dependency_risks) if dependency_risks else 0,
                "complexity_risk": sum(r.probability for r in complexity_risks) if complexity_risks else 0,
            },
        )

        # 6. 记录历史
        self.assessment_history.append(assessment)

        self.logger.info(f"   ✅ 风险预测完成: 等级={overall_risk.value}, 评分={overall_score:.2f}")

        return assessment

    def _assess_time_risks(self, plan: ExecutionPlan) -> list[Risk]:
        """评估时间风险"""
        risks = []

        # 执行时间过长
        if plan.estimated_time > 600:  # 超过10分钟
            risks.append(Risk(
                type="time",
                description=f"预计执行时间{plan.estimated_time}秒可能超出用户耐心阈值",
                probability=0.7,
                impact="high",
                mitigation="考虑分批返回结果或提供进度反馈",
            ))

        # 某个步骤时间过长
        for step in plan.steps:
            if step.estimated_time > 300:  # 单个步骤超过5分钟
                risks.append(Risk(
                    type="time",
                    description=f"步骤 '{step.description}' 预计耗时{step.estimated_time}秒",
                    probability=0.5,
                    impact="medium",
                    mitigation="将步骤分解为多个小步骤或异步执行",
                ))

        return risks

    def _assess_resource_risks(self, plan: ExecutionPlan) -> list[Risk]:
        """评估资源风险"""
        risks = []

        # 智能体过载风险
        agent_usage = {}
        for step in plan.steps:
            agent_usage[step.agent] = agent_usage.get(step.agent, 0) + 1

        max_concurrent = {
            "xiaona": 2,
            "xiaonuo": 3,
        }

        for agent, count in agent_usage.items():
            max_conc = max_concurrent.get(agent, 2)
            if count > max_conc:
                risks.append(Risk(
                    type="resource",
                    description=f"{agent} 智能体负载过高 ({count}/{max_conc})",
                    probability=0.6 + (count - max_conc) * 0.1,
                    impact="high",
                    mitigation=f"限制{agent}并发数或增加任务队列",
                ))

        # 资源冲突风险
        if len(plan.resource_requirements.databases) > 2:
            risks.append(Risk(
                type="resource",
                description="多个数据库访问可能导致锁竞争",
                probability=0.4,
                impact="medium",
                mitigation="合理安排数据库访问顺序",
            ))

        return risks

    def _assess_dependency_risks(self, plan: ExecutionPlan) -> list[Risk]:
        """评估依赖风险"""
        risks = []

        # 依赖链过长
        max_chain_length = 0
        for step in plan.steps:
            chain_length = self._calculate_dependency_chain_length(step, plan.steps)
            max_chain_length = max(max_chain_length, chain_length)

        if max_chain_length > 4:
            risks.append(Risk(
                type="dependency",
                description=f"依赖链过长(最长{max_chain_length}步)，单点失败影响大",
                probability=0.5 + max_chain_length * 0.1,
                impact="high",
                mitigation="增加并行执行或引入检查点机制",
            ))

        # 循环依赖风险（简化检测）
        step_ids = {step.id for step in plan.steps}
        for step in plan.steps:
            for dep in step.dependencies:
                if dep not in step_ids:
                    risks.append(Risk(
                        type="dependency",
                        description=f"步骤 {step.id} 依赖的步骤 {dep} 不存在",
                        probability=1.0,
                        impact="critical",
                        mitigation="检查并修正步骤依赖关系",
                    ))

        return risks

    def _calculate_dependency_chain_length(
        self,
        step: ExecutionStep,
        all_steps: list[ExecutionStep],
        visited: set | None = None
    ) -> int:
        """计算依赖链长度"""
        if visited is None:
            visited = set()

        if step.id in visited:
            return 0  # 检测到循环

        visited.add(step.id)

        max_length = 0
        for dep_id in step.dependencies:
            dep_step = next((s for s in all_steps if s.id == dep_id), None)
            if dep_step:
                length = 1 + self._calculate_dependency_chain_length(dep_step, all_steps, visited)
                max_length = max(max_length, length)

        return max_length

    def _assess_complexity_risks(self, plan: ExecutionPlan) -> list[Risk]:
        """评估复杂度风险"""
        risks = []

        # 步骤过多
        if len(plan.steps) > 8:
            risks.append(Risk(
                type="complexity",
                description=f"方案包含{len(plan.steps)}个步骤，复杂度较高",
                probability=0.4 + (len(plan.steps) - 8) * 0.05,
                impact="medium",
                mitigation="考虑合并相似步骤或使用子流程",
            ))

        # 混合执行模式风险
        if plan.mode.value == "hybrid":
            risks.append(Risk(
                type="complexity",
                description="混合执行模式复杂度较高，可能增加调试难度",
                probability=0.3,
                impact="low",
                mitigation="完善日志和监控机制",
            ))

        # 意图置信度低的风险
        if plan.intent.confidence < 0.6:
            risks.append(Risk(
                type="complexity",
                description="用户意图理解不够明确，可能导致方案偏差",
                probability=plan.intent.confidence,
                impact="medium",
                mitigation="增加用户确认环节或提供多方案选择",
            ))

        return risks

    def _calculate_overall_risk(self, risks: list[Risk], plan: ExecutionPlan) -> float:
        """计算综合风险评分"""
        if not risks:
            return 0.0

        # 加权计算
        weighted_score = (
            sum(r.probability for r in risks if r.type == "time") * self.TIME_RISK_WEIGHT +
            sum(r.probability for r in risks if r.type == "resource") * self.RESOURCE_RISK_WEIGHT +
            sum(r.probability for r in risks if r.type == "dependency") * self.DEPENDENCY_RISK_WEIGHT +
            sum(r.probability for r in risks if r.type == "complexity") * self.COMPLEXITY_RISK_WEIGHT
        )

        # 归一化到0-1
        return min(1.0, weighted_score)

    def _determine_risk_level(self, score: float) -> RiskLevel:
        """确定风险等级"""
        if score >= 0.8:
            return RiskLevel.CRITICAL
        elif score >= 0.6:
            return RiskLevel.HIGH
        elif score >= 0.3:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _generate_mitigation_suggestions(
        self,
        risks: list[Risk],
        risk_level: RiskLevel
    ) -> list[str]:
        """生成缓解建议"""
        suggestions = []

        # 通用建议
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            suggestions.append("建议分阶段实施，降低单次执行风险")
            suggestions.append("增加监控和日志记录，便于问题追踪")

        # 基于具体风险的建议
        for risk in risks:
            if risk.mitigation and risk.probability > 0.4:
                suggestions.append(risk.mitigation)

        # 去重
        seen = set()
        unique_suggestions = []
        for suggestion in suggestions:
            if suggestion not in seen:
                seen.add(suggestion)
                unique_suggestions.append(suggestion)

        return unique_suggestions

    def get_prediction_stats(self) -> dict[str, Any]:
        """获取预测统计"""
        if not self.assessment_history:
            return {"total_assessments": 0}

        risk_levels = [a.overall_risk.value for a in self.assessment_history]
        risk_distribution = {}
        for level in risk_levels:
            risk_distribution[level] = risk_distribution.get(level, 0) + 1

        return {
            "total_assessments": len(self.assessment_history),
            "risk_distribution": risk_distribution,
            "average_risk_score": sum(a.overall_score for a in self.assessment_history) / len(self.assessment_history),
        }
