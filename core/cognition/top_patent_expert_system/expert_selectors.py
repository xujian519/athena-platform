#!/usr/bin/env python3
from __future__ import annotations
"""
顶级专利专家系统 - 专家选择模块
Top Patent Expert System - Expert Selection Module

作者: Athena AI系统
创建时间: 2025-12-16
重构时间: 2026-01-27
版本: 2.0.0
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class ExpertSelectors:
    """专家选择器类"""

    def __init__(self, expert_database: dict[str, Any]):
        """初始化专家选择器

        Args:
            expert_database: 专家数据库
        """
        self.expert_database = expert_database
        self.agent_experts = {}
        self.lawyer_experts = {}
        self.examiner_experts = {}
        self.technical_experts = {}

    async def initialize_expert_instances(self):
        """初始化专家实例"""
        # 初始化专利代理人
        agents = self.expert_database.get("patent_agents", [])
        for agent in agents:
            agent_id = agent["id"]
            self.agent_experts[agent_id] = agent

        # 初始化专利律师
        lawyers = self.expert_database.get("patent_lawyers", [])
        for lawyer in lawyers:
            lawyer_id = lawyer["id"]
            self.lawyer_experts[lawyer_id] = lawyer

        # 初始化专利审查员
        examiners = self.expert_database.get("patent_examiners", [])
        for examiner in examiners:
            examiner_id = examiner["id"]
            self.examiner_experts[examiner_id] = examiner

        # 初始化技术专家
        technical_experts = self.expert_database.get("technical_experts", [])
        for expert in technical_experts:
            expert_id = expert["id"]
            self.technical_experts[expert_id] = expert

        logger.info(
            f"✅ 专家实例初始化完成: "
            f"{len(self.agent_experts)}代理人, "
            f"{len(self.lawyer_experts)}律师, "
            f"{len(self.examiner_experts)}审查员, "
            f"{len(self.technical_experts)}技术专家"
        )

    async def select_best_agent(self, technology_field: str) -> Optional[dict[str, Any]]:
        """选择最佳专利代理人

        Args:
            technology_field: 技术领域

        Returns:
            最佳专利代理人信息,如果没有找到返回None
        """
        best_agent = None
        best_score = 0.0

        for _agent_id, agent in self.agent_experts.items():
            score = 0.0
            # 基于专业匹配度评分
            if any(
                tech in str(agent.get("specialization", ""))
                for tech in technology_field.split()
            ):
                score += 2.0
            # 基于经验评分
            score += min(agent.get("experience", 0) / 10, 2.0)
            # 基于成功率评分
            score += agent.get("success_rate", 0) * 2.0

            if score > best_score:
                best_score = score
                best_agent = agent

        return best_agent

    async def select_best_lawyer(self, technology_field: str) -> Optional[dict[str, Any]]:
        """选择最佳专利律师

        Args:
            technology_field: 技术领域

        Returns:
            最佳专利律师信息,如果没有找到返回None
        """
        best_lawyer = None
        best_score = 0.0

        for _lawyer_id, lawyer in self.lawyer_experts.items():
            score = 0.0
            # 基于专业匹配度评分
            if any(
                tech in str(lawyer.get("specialization", ""))
                for tech in technology_field.split()
            ):
                score += 2.0
            # 基于经验评分
            score += min(lawyer.get("experience", 0) / 10, 2.0)
            # 基于胜诉率评分
            score += lawyer.get("win_rate", 0) * 2.0

            if score > best_score:
                best_score = score
                best_lawyer = lawyer

        return best_lawyer

    async def select_best_examiner(
        self, technology_field: str
    ) -> Optional[dict[str, Any]]:
        """选择最佳专利审查员

        Args:
            technology_field: 技术领域

        Returns:
            最佳专利审查员信息,如果没有找到返回None
        """
        best_examiner = None
        best_score = 0.0

        for _examiner_id, examiner in self.examiner_experts.items():
            score = 0.0
            # 基于专业匹配度评分
            if any(
                tech in str(examiner.get("expertise_areas", ""))
                for tech in technology_field.split()
            ):
                score += 2.0
            # 基于经验评分
            score += min(examiner.get("experience", 0) / 10, 2.0)
            # 基于审查数量评分
            score += min(examiner.get("reviewed_applications", 0) / 1000, 2.0)

            if score > best_score:
                best_score = score
                best_examiner = examiner

        return best_examiner


__all__ = ["ExpertSelectors"]
