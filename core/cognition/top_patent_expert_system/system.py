#!/usr/bin/env python3
from __future__ import annotations
"""
顶级专利专家系统 - 主系统
Top Patent Expert System - Main System

作者: Athena AI系统
创建时间: 2025-12-16
重构时间: 2026-01-27
版本: 2.0.0
"""

import json
import logging
from datetime import datetime
from typing import Any

from core.logging_config import setup_logging

from .analysis import AnalysisMethods
from .expert_selectors import ExpertSelectors
from .response_generators import ResponseGenerators
from .types import ExpertConsultation, ExpertTeamAnalysis

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class TopPatentExpertSystem:
    """顶级专利专家系统

    集成中国顶级专利代理人、专利律师、专利审查员和技术专家的专家系统
    """

    def __init__(self, expert_database_path: str | None = None):
        """初始化顶级专利专家系统

        Args:
            expert_database_path: 专家数据库路径
        """
        self.name = "顶级专利专家系统"
        self.version = "v2.0 Top Expert"

        # 专家数据库路径
        if expert_database_path is None:
            import os
            # 从当前文件 core/cognition/top_patent_expert_system/system.py 向上找到项目根目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            cognition_dir = os.path.dirname(current_dir)
            core_dir = os.path.dirname(cognition_dir)
            project_root = os.path.dirname(core_dir)
            expert_database_path = os.path.join(project_root, "core/patents/knowledge/top_patent_experts.json")
        self.expert_database_path = expert_database_path
        self.expert_database: dict[str, Any] = {}

        # 历史咨询记录
        self.consultation_history: list[ExpertTeamAnalysis] = []

        # 团队组合规则和共识机制
        self.composition_rules: dict[str, Any] = {}
        self.consensus_mechanism: dict[str, Any] = {}

        # 初始化子模块
        self.expert_selectors = ExpertSelectors(self.expert_database)
        self.response_generators = ResponseGenerators()
        self.analysis_methods = AnalysisMethods()

        self.is_initialized = False

    async def initialize(self):
        """初始化专家系统"""
        logger.info("🌟 初始化顶级专利专家系统...")

        try:
            # 1. 加载专家数据库
            await self._load_expert_database()

            # 2. 初始化专家选择器
            self.expert_selectors.expert_database = self.expert_database
            await self.expert_selectors.initialize_expert_instances()

            # 3. 构建团队组合规则
            await self._build_team_composition_rules()

            # 4. 建立共识机制
            await self._establish_consensus_mechanism()

            self.is_initialized = True
            logger.info("✅ 顶级专利专家系统初始化完成")

        except Exception as e:
            logger.error(f"❌ 专家系统初始化失败: {e!s}")
            logger.error(f"操作失败: {e}", exc_info=True)
            raise

    async def analyze_with_expert_team(
        self,
        technology_field: str,
        ipc_section: str,
        patent_type: str,
        analysis_type: str,
        technical_description: str,
        user_requirements: list[str] | None = None,
    ) -> ExpertTeamAnalysis:
        """使用专家团队进行分析

        Args:
            technology_field: 技术领域
            ipc_section: IPC分类号
            patent_type: 专利类型
            analysis_type: 分析类型
            technical_description: 技术描述
            user_requirements: 用户要求

        Returns:
            专家团队分析结果
        """
        if not self.is_initialized:
            raise RuntimeError("专家系统未初始化")

        logger.info(f"👥 专家团队分析: {technology_field} - {analysis_type}")
        start_time = datetime.now()

        # 1. 确定需要的专家组合
        team_composition = await self._determine_team_composition(
            technology_field, ipc_section, patent_type, analysis_type
        )

        # 2. 收集各专家意见
        individual_opinions = []
        for expert in team_composition:
            opinion = await self._consult_expert(
                expert, technical_description, analysis_type, user_requirements
            )
            individual_opinions.append(opinion)

        # 3. 形成团队共识
        consensus_opinion = await self.analysis_methods.form_consensus(
            individual_opinions
        )

        # 4. 风险评估
        risk_assessment = await self.analysis_methods.conduct_team_risk_assessment(
            individual_opinions
        )

        # 5. 制定建议
        recommendations = await self.analysis_methods.generate_team_recommendations(
            consensus_opinion, individual_opinions
        )

        # 6. 确定下一步行动
        next_steps = await self.analysis_methods.determine_next_steps(
            recommendations, analysis_type
        )

        # 7. 计算团队置信度
        confidence_score = await self.analysis_methods.calculate_team_confidence(
            individual_opinions
        )

        analysis_time = (datetime.now() - start_time).total_seconds()

        analysis_result = ExpertTeamAnalysis(
            analysis_id=f"expert_team_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            team_composition=team_composition,
            individual_opinions=individual_opinions,
            consensus_opinion=consensus_opinion,
            risk_assessment=risk_assessment,
            recommendations=recommendations,
            next_steps=next_steps,
            confidence_score=confidence_score,
            analysis_time=analysis_time,
        )

        # 8. 记录分析历史
        await self._record_analysis(analysis_result)

        logger.info(f"✅ 专家团队分析完成,耗时: {analysis_time:.2f}秒")
        return analysis_result

    async def _determine_team_composition(
        self,
        technology_field: str,
        ipc_section: str,
        patent_type: str,
        analysis_type: str,
    ) -> list[dict[str, Any]]:
        """确定专家团队组合

        Args:
            technology_field: 技术领域
            ipc_section: IPC分类号
            patent_type: 专利类型
            analysis_type: 分析类型

        Returns:
            专家团队列表
        """
        team = []

        # 基于IPC分类选择技术专家
        if ipc_section in self.expert_database.get("technical_experts_by_ipc", {}):
            ipc_experts = self.expert_database.get("technical_experts_by_ipc")[
                ipc_section
            ]
            if isinstance(ipc_experts, list):
                for ipc_expert in ipc_experts:
                    team.append(
                        {
                            "id": ipc_expert["technical_expert"]["id"],
                            "type": "technical",
                            "name": ipc_expert["technical_expert"]["name"],
                            "title": ipc_expert["technical_expert"]["title"],
                            "specialization": ipc_expert["technical_expert"][
                                "expertise"
                            ],
                            "role": "技术评估",
                        }
                    )
            else:
                team.append(
                    {
                        "id": ipc_experts["technical_expert"]["id"],
                        "type": "technical",
                        "name": ipc_experts["technical_expert"]["name"],
                        "title": ipc_experts["technical_expert"]["title"],
                        "specialization": ipc_experts["technical_expert"]["expertise"],
                        "role": "技术评估",
                    }
                )

        # 根据分析类型选择相应专家
        if analysis_type in ["申请撰写", "审查答复", "专利布局"]:
            best_agent = await self.expert_selectors.select_best_agent(
                technology_field
            )
            if best_agent:
                team.append(
                    {
                        "id": best_agent["id"],
                        "type": "agent",
                        "name": best_agent["name"],
                        "title": best_agent["title"],
                        "specialization": best_agent["specialization"],
                        "role": "申请策略",
                    }
                )

        if analysis_type in ["侵权分析", "法律风险评估", "专利诉讼"]:
            best_lawyer = await self.expert_selectors.select_best_lawyer(
                technology_field
            )
            if best_lawyer:
                team.append(
                    {
                        "id": best_lawyer["id"],
                        "type": "lawyer",
                        "name": best_lawyer["name"],
                        "title": best_lawyer["title"],
                        "specialization": best_lawyer["specialization"],
                        "role": "法律分析",
                    }
                )

        if analysis_type in ["审查预判", "授权前景评估"]:
            best_examiner = await self.expert_selectors.select_best_examiner(
                technology_field
            )
            if best_examiner:
                team.append(
                    {
                        "id": best_examiner["id"],
                        "type": "examiner",
                        "name": best_examiner["name"],
                        "title": best_examiner["title"],
                        "specialization": best_examiner["expertise_areas"],
                        "role": "审查分析",
                    }
                )

        return team

    async def _consult_expert(
        self,
        expert: dict[str, Any],        technical_description: str,
        analysis_type: str,
        user_requirements: list[str] | None = None,
    ) -> ExpertConsultation:
        """咨询单个专家

        Args:
            expert: 专家信息
            technical_description: 技术描述
            analysis_type: 分析类型
            user_requirements: 用户要求

        Returns:
            专家咨询记录
        """
        logger.info(f"👨‍⚖️ 咨询专家: {expert['name']} ({expert['type']})")

        # 生成专家特定的提示词
        expert_prompt = await self._generate_expert_prompt(
            expert, technical_description, analysis_type, user_requirements
        )

        # 模拟专家响应
        expert_response = await self.response_generators.simulate_expert_response(
            expert, expert_prompt, technical_description
        )

        # 计算响应置信度
        confidence = await self._calculate_expert_confidence(
            expert, expert_response, technical_description
        )

        # 生成推理过程
        reasoning_process = await self._generate_reasoning_process(
            expert, technical_description, expert_response
        )

        consultation = ExpertConsultation(
            expert_id=expert["id"],
            expert_type=expert["type"],
            consultation_type=analysis_type,
            query=technical_description,
            response=expert_response,
            confidence=confidence,
            reasoning_process=reasoning_process,
            references=await self._get_expert_references(expert),
        )

        return consultation

    async def _generate_expert_prompt(
        self,
        expert: dict[str, Any],        technical_description: str,
        analysis_type: str,
        user_requirements: list[str] | None = None,
    ) -> str:
        """生成专家特定的提示词

        Args:
            expert: 专家信息
            technical_description: 技术描述
            analysis_type: 分析类型
            user_requirements: 用户要求

        Returns:
            提示词
        """
        expert["type"]
        expert_name = expert["name"]
        expert_title = expert["title"]
        specialization = expert["specialization"]

        base_prompt = f"""
作为中国{expert_title}{expert_name},您在{', '.join(specialization)}领域拥有丰富的专业经验。

请基于您的专业知识和实践经验,对以下技术方案进行分析:

[技术描述]
{technical_description}

[分析类型]
{analysis_type}

[用户要求]
{', '.join(user_requirements) if user_requirements else '无特殊要求'}

请从您的专业角度提供:
1. 技术方案的专业评估
2. 专利前景分析
3. 存在的问题和改进建议
4. 下一步行动计划

请以您的专业身份,给出权威、准确、实用的分析意见。
        """
        return base_prompt

    async def _calculate_expert_confidence(
        self, expert: dict[str, Any], response: str, description: str
    ) -> float:
        """计算专家响应置信度

        Args:
            expert: 专家信息
            response: 响应内容
            description: 技术描述

        Returns:
            置信度 (0.0-1.0)
        """
        base_confidence = 0.8

        # 根据专家经验调整
        experience_bonus = min(expert.get("experience", 0) / 30, 0.1)

        # 根据专业匹配度调整
        specialization = expert.get("specialization", [])
        if isinstance(specialization, str):
            specialization = [specialization]

        match_bonus = 0.0
        for spec in specialization:
            if spec.lower() in description.lower():
                match_bonus += 0.05

        # 根据响应质量调整
        response_quality = len(response) / 1000
        quality_bonus = min(response_quality, 0.1)

        total_confidence = base_confidence + experience_bonus + match_bonus + quality_bonus
        return min(total_confidence, 1.0)

    async def _generate_reasoning_process(
        self, expert: dict[str, Any], description: str, response: str
    ) -> str:
        """生成推理过程

        Args:
            expert: 专家信息
            description: 技术描述
            response: 响应内容

        Returns:
            推理过程文本
        """
        reasoning = f"专家{expert['name']}的推理过程:\n"
        reasoning += "1. 分析技术方案的核心创新点\n"
        reasoning += "2. 评估技术方案的专利性\n"
        reasoning += "3. 识别潜在的风险和问题\n"
        reasoning += "4. 提出专业的改进建议\n"
        return reasoning

    async def _get_expert_references(self, expert: dict[str, Any]) -> list[str]:
        """获取专家参考信息

        Args:
            expert: 专家信息

        Returns:
            参考信息列表
        """
        references = []
        if expert["type"] == "agent":
            references = ["专利法", "专利审查指南", "专利代理规范"]
        elif expert["type"] == "lawyer":
            references = ["专利法", "专利侵权判定指南", "相关案例分析"]
        elif expert["type"] == "examiner":
            references = ["专利审查指南", "专利法", "审查操作规程"]
        elif expert["type"] == "technical":
            references = ["技术标准", "行业规范", "技术发展趋势报告"]
        return references

    async def _load_expert_database(self):
        """加载专家数据库"""
        try:
            with open(self.expert_database_path, encoding="utf-8") as f:
                self.expert_database = json.load(f)
            logger.info("✅ 专家数据库加载完成")
        except Exception:
            self.expert_database = {}
            logger.warning("⚠️  专家数据库加载失败,使用空数据库")

    async def _build_team_composition_rules(self):
        """构建团队组合规则"""
        self.composition_rules = {
            "application_writing": ["agent", "technical"],
            "infringement_analysis": ["lawyer", "technical", "examiner"],
            "examination_reply": ["agent", "examiner", "technical"],
            "patent_strategy": ["agent", "lawyer", "technical"],
            "risk_assessment": ["lawyer", "examiner", "agent"],
            "technical_evaluation": ["technical", "examiner"],
        }

    async def _establish_consensus_mechanism(self):
        """建立共识机制"""
        self.consensus_mechanism = {
            "voting_weight": {"agent": 0.3, "lawyer": 0.25, "examiner": 0.25, "technical": 0.2},
            "consensus_threshold": 0.7,
            "dispute_resolution": "expert_lead_vote",
        }

    async def _record_analysis(self, analysis: ExpertTeamAnalysis):
        """记录分析结果

        Args:
            analysis: 分析结果
        """
        self.consultation_history.append(analysis)
        logger.debug(f"📝 记录分析: {analysis.analysis_id}")

    async def get_expert_statistics(self) -> dict[str, Any]:
        """获取专家统计信息

        Returns:
            统计信息字典
        """
        return {
            "total_analyses": len(self.consultation_history),
            "expert_database_loaded": bool(self.expert_database),
            "composition_rules": list(self.composition_rules.keys()),
            "consensus_mechanism": self.consensus_mechanism,
        }

    async def cleanup(self):
        """清理资源"""
        self.consultation_history.clear()
        logger.info("✅ 资源清理完成")


__all__ = ["TopPatentExpertSystem"]
