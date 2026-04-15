#!/usr/bin/env python3
from __future__ import annotations
"""
顶级专利专家系统 - 分析方法模块
Top Patent Expert System - Analysis Module

作者: Athena AI系统
创建时间: 2025-12-16
重构时间: 2026-01-27
版本: 2.0.0
"""

import logging
from typing import Any

from .types import ExpertConsultation

logger = logging.getLogger(__name__)


class AnalysisMethods:
    """分析方法类"""

    @staticmethod
    async def form_consensus(opinions: list[ExpertConsultation]) -> str:
        """形成团队共识

        Args:
            opinions: 专家咨询意见列表

        Returns:
            共识意见文本
        """
        # 收集各专家的主要观点
        agent_opinions = [op for op in opinions if op.expert_type == "agent"]
        lawyer_opinions = [op for op in opinions if op.expert_type == "lawyer"]
        examiner_opinions = [op for op in opinions if op.expert_type == "examiner"]
        technical_opinions = [op for op in opinions if op.expert_type == "technical"]

        consensus = "[专家团队共识意见]\n\n"

        # 专利代理人团队观点
        if agent_opinions:
            consensus += "📋 专利代理人团队观点:\n"
            for i, op in enumerate(agent_opinions, 1):
                response_text = (
                    op.response[:200] if len(op.response) > 200 else op.response
                )
                consensus += f"{i}. {response_text}...\n"
            consensus += "\n"

        # 专利律师团队观点
        if lawyer_opinions:
            consensus += "⚖️ 专利律师团队观点:\n"
            for i, op in enumerate(lawyer_opinions, 1):
                response_text = (
                    op.response[:200] if len(op.response) > 200 else op.response
                )
                consensus += f"{i}. {response_text}...\n"
            consensus += "\n"

        # 专利审查员团队观点
        if examiner_opinions:
            consensus += "🔍 专利审查员团队观点:\n"
            for i, op in enumerate(examiner_opinions, 1):
                response_text = (
                    op.response[:200] if len(op.response) > 200 else op.response
                )
                consensus += f"{i}. {response_text}...\n"
            consensus += "\n"

        # 技术专家团队观点
        if technical_opinions:
            consensus += "🔬 技术专家团队观点:\n"
            for i, op in enumerate(technical_opinions, 1):
                response_text = (
                    op.response[:200] if len(op.response) > 200 else op.response
                )
                consensus += f"{i}. {response_text}...\n"
            consensus += "\n"

        consensus += "[综合建议]\n"
        consensus += "基于各领域专家的综合分析,建议您:\n"
        consensus += "1. 立即启动专利申请程序,保护核心技术\n"
        consensus += "2. 进行全面的专利检索和分析\n"
        consensus += "3. 制定专业的专利布局策略\n"
        consensus += "4. 建立完善的知识产权管理体系\n"

        return consensus

    @staticmethod
    async def conduct_team_risk_assessment(
        opinions: list[ExpertConsultation],
    ) -> dict[str, Any]:
        """进行团队风险评估

        Args:
            opinions: 专家咨询意见列表

        Returns:
            风险评估字典
        """
        risks = {
            "technical_risks": [],
            "legal_risks": [],
            "commercial_risks": [],
            "timing_risks": [],
            "overall_risk_level": "medium",
        }

        # 收集各专家提到的风险
        for opinion in opinions:
            if "风险" in opinion.response:
                if opinion.expert_type == "agent":
                    risks["commercial_risks"].append("专利布局风险")
                elif opinion.expert_type == "lawyer":
                    risks["legal_risks"].append("侵权风险")
                elif opinion.expert_type == "examiner":
                    risks["technical_risks"].append("授权风险")
                elif opinion.expert_type == "technical":
                    risks["technical_risks"].append("技术可行性风险")

        # 评估整体风险等级
        total_risks = sum(
            len(risks[key])
            for key in ["technical_risks", "legal_risks", "commercial_risks", "timing_risks"]
        )
        if total_risks >= 4:
            risks["overall_risk_level"] = "high"
        elif total_risks >= 2:
            risks["overall_risk_level"] = "medium"
        else:
            risks["overall_risk_level"] = "low"

        return risks

    @staticmethod
    async def generate_team_recommendations(
        consensus: str, opinions: list[ExpertConsultation]
    ) -> list[str]:
        """生成团队建议

        Args:
            consensus: 共识意见
            opinions: 专家咨询意见列表

        Returns:
            建议列表
        """
        recommendations = []

        # 基于共识和建议生成具体行动
        recommendations.append("立即准备专利申请材料,确保技术方案得到充分保护")
        recommendations.append("进行全面的现有技术检索,评估技术方案的新颖性和创造性")
        recommendations.append("制定专业的权利要求布局,最大化专利保护范围")
        recommendations.append("建立专利监测机制,及时掌握相关技术发展动态")

        # 基于专家类型补充建议
        has_agent = any(op.expert_type == "agent" for op in opinions)
        has_lawyer = any(op.expert_type == "lawyer" for op in opinions)
        has_examiner = any(op.expert_type == "examiner" for op in opinions)
        has_technical = any(op.expert_type == "technical" for op in opinions)

        if has_agent:
            recommendations.append("咨询资深专利代理人,优化申请策略")
        if has_lawyer:
            recommendations.append("进行法律风险评估,避免未来纠纷")
        if has_examiner:
            recommendations.append("模拟审查过程,提前准备答复材料")
        if has_technical:
            recommendations.append("进行技术方案验证,确保可行性")

        return recommendations

    @staticmethod
    async def determine_next_steps(
        recommendations: list[str], analysis_type: str
    ) -> list[str]:
        """确定下一步行动

        Args:
            recommendations: 建议列表
            analysis_type: 分析类型

        Returns:
            下一步行动列表
        """
        next_steps = []

        if analysis_type == "申请撰写":
            next_steps = [
                "完善技术交底材料",
                "准备专利申请文件",
                "提交专利申请",
                "跟进审查进程",
            ]
        elif analysis_type == "侵权分析":
            next_steps = [
                "进行详细的权利要求对比",
                "收集侵权证据",
                "制定应对策略",
                "考虑法律行动",
            ]
        elif analysis_type == "审查答复":
            next_steps = [
                "分析审查意见",
                "准备答复材料",
                "修改申请文件",
                "提交答复意见",
            ]
        else:
            next_steps = [
                "执行专家团队建议",
                "制定详细行动计划",
                "分配执行责任",
                "设定时间节点",
            ]

        return next_steps

    @staticmethod
    async def calculate_team_confidence(opinions: list[ExpertConsultation]) -> float:
        """计算团队置信度

        Args:
            opinions: 专家咨询意见列表

        Returns:
            团队置信度 (0.0-1.0)
        """
        if not opinions:
            return 0.0

        # 加权平均置信度
        weights = {"agent": 0.3, "lawyer": 0.25, "examiner": 0.25, "technical": 0.2}

        total_weighted_confidence = 0.0
        total_weight = 0.0

        for opinion in opinions:
            weight = weights.get(opinion.expert_type, 0.1)
            total_weighted_confidence += opinion.confidence * weight
            total_weight += weight

        if total_weight > 0:
            return total_weighted_confidence / total_weight
        return 0.0


__all__ = ["AnalysisMethods"]
