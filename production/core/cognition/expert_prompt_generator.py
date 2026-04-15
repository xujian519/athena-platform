# pyright: ignore
# !/usr/bin/env python3
"""
专家提示词动态生成器
Expert Prompt Dynamic Generator

基于专家类型和分析需求,动态生成专业的分析提示词

作者: 小娜·天秤女神
创建时间: 2025-12-16
版本: v1.0 Expert Prompt Generator
"""

from __future__ import annotations
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


@dataclass
class ExpertPromptConfig:
    """专家提示词配置"""

    expert_name: str
    expert_type: str  # patent_agent, patent_lawyer, patent_examiner, technical_expert
    specialization: str
    expertise_areas: list[str]
    analysis_focus: list[str]
    prompt_style: str  # formal, detailed, strategic, technical
    knowledge_bases: list[str]


@dataclass
class GeneratedPrompt:
    """生成的提示词"""

    prompt_id: str
    expert_context: str
    main_prompt: str
    expert_guidance: str
    evaluation_criteria: list[str]
    expected_output: str
    generation_time: datetime
    knowledge_sources: list[str]


class ExpertPromptGenerator:
    """专家提示词生成器"""

    def __init__(self):
        self.expert_configs = self._load_expert_configs()
        self.prompt_templates = self._load_prompt_templates()
        self.generation_history = []

    def _load_expert_configs(self) -> dict[str, ExpertPromptConfig]:
        """加载专家配置"""
        configs = {}

        # 专利代理人配置
        configs["天狼"] = ExpertPromptConfig(
            expert_name="天狼",
            expert_type="patent_agent",
            specialization="电子通信、计算机软件、人工智能",
            expertise_areas=[
                "发明专利撰写策略",
                "权利要求布局优化",
                "审查意见答复技巧",
                "专利诉讼支持",
            ],
            analysis_focus=["技术特征分析", "权利要求撰写", "专利保护范围", "申请策略"],
            prompt_style="detailed",
            knowledge_bases=[
                "patent_writing_guidelines",
                "claim_analysis_examples",
                "examination_response_tactics",
            ],
        )

        configs["织女"] = ExpertPromptConfig(
            expert_name="织女",
            expert_type="patent_agent",
            specialization="生物医药、化学工程、新材料",
            expertise_areas=["生物医药专利申请", "化学化合物保护", "药品专利战略"],
            analysis_focus=["实验数据评估", "化合物专利性", "制药用途权利要求", "生物技术保护"],
            prompt_style="formal",
            knowledge_bases=[
                "pharma_patent_guidelines",
                "chemical_compound_analysis",
                "biotech_patent_cases",
            ],
        )

        configs["北极"] = ExpertPromptConfig(
            expert_name="北极",
            expert_type="patent_agent",
            specialization="机械制造、汽车工程、工业设计",
            expertise_areas=["机械结构发明创造", "外观设计专利", "实用新型专利"],
            analysis_focus=["机械结构分析", "附图理解", "技术方案完整性", "工艺流程"],
            prompt_style="technical",
            knowledge_bases=[
                "mechanical_patent_examples",
                "design_patent_guidelines",
                "utility_model_practices",
            ],
        )

        # 专利律师配置
        configs["参宿"] = ExpertPromptConfig(
            expert_name="参宿",
            expert_type="patent_lawyer",
            specialization="专利侵权诉讼、专利无效、专利许可",
            expertise_areas=["专利侵权分析", "专利无效宣告", "专利合同纠纷"],
            analysis_focus=["权利要求解释", "侵权判定", "法律风险评估", "证据链分析"],
            prompt_style="strategic",
            knowledge_bases=[
                "patent_law_precedents",
                "infringement_analysis_cases",
                "litigation_strategies",
            ],
        )

        configs["角宿"] = ExpertPromptConfig(
            expert_name="角宿",
            expert_type="patent_lawyer",
            specialization="知识产权战略、专利许可、技术转让",
            expertise_areas=["专利价值实现", "专利池管理", "技术标准必要专利"],
            analysis_focus=["专利价值评估", "许可谈判策略", "技术转移风险", "合规性分析"],
            prompt_style="strategic",
            knowledge_bases=[
                "ip_strategy_frameworks",
                "licensing_best_practices",
                "tech_transfer_guidelines",
            ],
        )

        # 专利审查员配置
        configs["大角"] = ExpertPromptConfig(
            expert_name="大角",
            expert_type="patent_examiner",
            specialization="通信技术、计算机网络、人工智能",
            expertise_areas=["发明专利实质审查", "新颖性判断", "创造性评估"],
            analysis_focus=["现有技术检索", "技术方案对比", "三步法应用", "审查标准"],
            prompt_style="formal",
            knowledge_bases=[
                "examination_guidelines",
                "prior_art_search_methods",
                "inventive_step_criteria",
            ],
        )

        configs["毕宿"] = ExpertPromptConfig(
            expert_name="毕宿",
            expert_type="patent_examiner",
            specialization="生物医药、化学、医药",
            expertise_areas=["医药专利审查", "化学化合物审查", "生物技术审查"],
            analysis_focus=["实验数据真实性", "技术效果显著性", "充分公开要求", "支持性判断"],
            prompt_style="detailed",
            knowledge_bases=[
                "pharma_examination_standards",
                "experimental_data_evaluation",
                "disclosure_requirements",
            ],
        )

        configs["房宿"] = ExpertPromptConfig(
            expert_name="房宿",
            expert_type="patent_examiner",
            specialization="机械制造、工程设备、工业设计",
            expertise_areas=["机械专利审查", "实用新型审查", "外观设计审查"],
            analysis_focus=["技术方案可行性", "结构完整性", "功能实现性", "实用性判断"],
            prompt_style="technical",
            knowledge_bases=[
                "mechanical_examination_standards",
                "utility_model_criteria",
                "design_patent_requirements",
            ],
        )

        return configs

    def _load_prompt_templates(self) -> dict[str, str]:
        """加载提示词模板"""
        return {
            "patent_application": """
作为{expert_name}星,一位在{specialization}领域拥有{expert_type}资格的专家,
请基于以下技术描述进行专业的专利申请分析:

[技术背景]
{background_technology}

[发明内容]
{invention_content}

[分析要求]
{analysis_requirements}

请从{analysis_focus}的角度提供详细的专业分析。
            """,
            "patent_examination": """
作为{expert_name}星,一位经验丰富的{expert_type},专长于{specialization}领域,
请对以下专利申请进行审查分析:

[申请信息]
- 申请号: {application_number}
- 技术领域: {technical_field}
- 发明名称: {invention_title}

[技术方案]
{technical_solution}

[对比文件]
{prior_art_references}

请按照审查标准,从{analysis_focus}等方面进行全面评估。
            """,
            "patent_litigation": """
作为{expert_name}星,一位专业的{expert_type},专注于{specialization},
请分析以下专利争议案件:

[争议焦点]
{dispute_focus}

[涉案专利]
{patent_details}

[被控侵权技术]
{accused_technology}

请从{analysis_focus}等角度进行法律分析和风险评估。
            """,
            "technical_evaluation": """
作为{expert_name}星,一位{specialization}领域的{expert_type},
请对以下技术方案进行专业评估:

[技术方案]
{technology_description}

[应用场景]
{application_scenarios}

[比较对象]
{comparison_targets}

请从{analysis_focus}等方面提供专业的技术分析。
            """,
        }

    async def generate_expert_prompt(
        self,
        expert_name: str,
        analysis_type: str,
        context_data: dict[str, Any],        user_requirements: list[str] | None = None,
    ) -> GeneratedPrompt:
        """生成专家提示词"""

        if expert_name not in self.expert_configs:
            raise ValueError(f"未找到专家: {expert_name}")

        config = self.expert_configs.get(expert_name)

        # 生成提示词ID
        prompt_id = f"{expert_name}_{analysis_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 构建专家上下文
        expert_context = self._build_expert_context(config, analysis_type, context_data)

        # 选择提示词模板
        template = self._select_prompt_template(analysis_type)

        # 生成主要提示词
        main_prompt = template.format(
            expert_name=expert_name,
            expert_type=config.expert_type,  # type: ignore
            specialization=config.specialization,  # type: ignore
            analysis_focus="、".join(config.analysis_focus),  # type: ignore
            **context_data,
        )

        # 生成专家指导
        expert_guidance = self._generate_expert_guidance(config, analysis_type, user_requirements)

        # 生成评估标准
        evaluation_criteria = self._generate_evaluation_criteria(config, analysis_type)

        # 定义期望输出
        expected_output = self._define_expected_output(config, analysis_type)

        # 记录生成历史
        generation_record = {
            "prompt_id": prompt_id,
            "expert_name": expert_name,
            "analysis_type": analysis_type,
            "generation_time": datetime.now().isoformat(),
            "context_keys": list(context_data.keys()),
            "user_requirements": user_requirements or [],
        }
        self.generation_history.append(generation_record)

        generated_prompt = GeneratedPrompt(
            prompt_id=prompt_id,
            expert_context=expert_context,
            main_prompt=main_prompt,
            expert_guidance=expert_guidance,
            evaluation_criteria=evaluation_criteria,
            expected_output=expected_output,
            generation_time=datetime.now(),
            knowledge_sources=config.knowledge_bases,  # type: ignore
        )

        logger.info(f"生成专家提示词: {prompt_id}, 专家: {expert_name}, 类型: {analysis_type}")
        return generated_prompt

    def _build_expert_context(
        self, config: ExpertPromptConfig, analysis_type: str, context_data: dict[str, Any]
    ) -> str:
        """构建专家上下文"""
        context_parts = []

        context_parts.append(f"专家身份: {config.expert_name}星")
        context_parts.append(f"专业角色: {config.expert_type}")
        context_parts.append(f"专业领域: {config.specialization}")
        context_parts.append(f"核心专长: {', '.join(config.expertise_areas)}")
        context_parts.append(f"分析重点: {', '.join(config.analysis_focus)}")
        context_parts.append(f"知识库: {', '.join(config.knowledge_bases)}")

        return "\n".join(context_parts)

    def _select_prompt_template(self, analysis_type: str) -> str:
        """选择提示词模板"""
        template_mapping = {
            "patent_application": "patent_application",
            "patent_examination": "patent_examination",
            "patent_litigation": "patent_litigation",
            "technical_evaluation": "technical_evaluation",
            "patent_analysis": "patent_application",  # 默认使用专利申请模板
            "legal_analysis": "patent_litigation",  # 默认使用专利诉讼模板
            "technology_analysis": "technical_evaluation",  # 默认使用技术评估模板
        }

        template_key = template_mapping.get(analysis_type, "patent_application")
        return self.prompt_templates.get(template_key, self.prompt_templates["patent_application"])

    def _generate_expert_guidance(
        self, config: ExpertPromptConfig, analysis_type: str, user_requirements: list[str]
    ) -> str:
        """生成专家指导"""
        guidance_parts = []

        guidance_parts.append("[专家指导原则]")
        guidance_parts.append(f"1. 基于{config.specialization}领域的专业知识进行分析")
        guidance_parts.append(f"2. 重点关注{', '.join(config.analysis_focus)}")
        guidance_parts.append(f"3. 采用{config.prompt_style}的分析风格")

        if user_requirements:
            guidance_parts.append(f"4. 特别关注用户要求: {', '.join(user_requirements)}")

        # 添加特定分析类型的指导
        if analysis_type in ["patent_application", "patent_analysis"]:
            guidance_parts.append("5. 注重技术方案的专利性分析")
            guidance_parts.append("6. 提供具体的申请策略建议")

        elif analysis_type in ["patent_examination"]:
            guidance_parts.append("5. 严格按照审查标准进行评估")
            guidance_parts.append("6. 给出明确的审查结论")

        elif analysis_type in ["patent_litigation", "legal_analysis"]:
            guidance_parts.append("5. 进行全面的法律风险评估")
            guidance_parts.append("6. 提供具体的法律建议")

        return "\n".join(guidance_parts)

    def _generate_evaluation_criteria(
        self, config: ExpertPromptConfig, analysis_type: str
    ) -> list[str]:
        """生成评估标准"""
        criteria = []

        # 通用评估标准
        criteria.extend(["分析的专业性和准确性", "逻辑结构的清晰性", "建议的实用性和可操作性"])

        # 根据专家类型添加特定标准
        if config.expert_type == "patent_agent":
            criteria.extend(["技术方案的专利性评估", "权利要求撰写的合理性", "申请策略的有效性"])

        elif config.expert_type == "patent_lawyer":
            criteria.extend(["法律分析的准确性", "风险评估的全面性", "法律建议的可行性"])

        elif config.expert_type == "patent_examiner":
            criteria.extend(["审查标准的适用性", "现有技术检索的全面性", "审查结论的合理性"])

        elif config.expert_type == "technical_expert":
            criteria.extend(["技术理解的深度", "技术分析的准确性", "技术创新性的评估"])

        return criteria

    def _define_expected_output(self, config: ExpertPromptConfig, analysis_type: str) -> str:
        """定义期望输出"""
        output_structure = []

        output_structure.append("[输出结构]")
        output_structure.append("1. 分析概述")
        output_structure.append("2. 详细分析内容")
        output_structure.append("3. 专业结论")
        output_structure.append("4. 具体建议")
        output_structure.append("5. 风险提示(如适用)")

        # 根据分析类型添加特定输出要求
        if analysis_type in ["patent_application", "patent_analysis"]:
            output_structure.extend(["6. 权利要求撰写建议", "7. 申请策略建议"])

        return "\n".join(output_structure)

    async def generate_team_prompt(
        self,
        expert_names: list[str],
        analysis_type: str,
        context_data: dict[str, Any],        team_objectives: list[str] | None = None,
    ) -> dict[str, GeneratedPrompt]:
        """生成团队提示词"""
        team_prompts = {}

        # 为每个专家生成提示词
        for expert_name in expert_names:
            try:
                prompt = await self.generate_expert_prompt(
                    expert_name=expert_name,
                    analysis_type=analysis_type,
                    context_data=context_data,
                    user_requirements=team_objectives,
                )
                team_prompts[expert_name] = prompt
            except Exception as e:
                # 提示生成失败，记录错误
                logger.error(f'提示生成失败: {e}', exc_info=True)

        # 增强提示词的团队协作元素
        for expert_name, prompt in team_prompts.items():
            # 添加团队协作指导
            team_guidance = "\n[团队协作指导]\n"
            team_guidance += (
                f"本次分析是团队协作的一部分,团队成员包括: {', '.join(expert_names)}\n"
            )

            if team_objectives:
                team_guidance += f"团队目标: {', '.join(team_objectives)}\n"

            team_guidance += "请结合您的专业领域,为团队分析提供独特的视角和价值。"

            prompt.main_prompt += team_guidance

        return team_prompts

    def get_generation_statistics(self) -> dict[str, Any]:
        """获取生成统计信息"""
        if not self.generation_history:
            return {"total_generations": 0}

        expert_counts = {}
        type_counts = {}

        for record in self.generation_history:
            expert_name = record["expert_name"]
            analysis_type = record["analysis_type"]

            expert_counts[expert_name] = expert_counts.get(expert_name, 0) + 1
            type_counts[analysis_type] = type_counts.get(analysis_type, 0) + 1

        return {
            "total_generations": len(self.generation_history),
            "expert_usage": expert_counts,
            "analysis_type_usage": type_counts,
            "most_used_expert": (
                max(expert_counts.items(), key=lambda x: x[1]) if expert_counts else None  # type: ignore
            ),
            "most_common_type": (
                max(type_counts.items(), key=lambda x: x[1]) if type_counts else None  # type: ignore
            ),
            "latest_generation": (
                self.generation_history[-1]["generation_time"] if self.generation_history else None
            ),
        }


# 便捷函数
async def generate_patent_analysis_prompt(
    expert_name: str, invention_description: str, user_requirements: list[str] | None = None
) -> GeneratedPrompt:
    """便捷的专利分析提示词生成函数"""
    generator = ExpertPromptGenerator()

    context_data = {
        "background_technology": "基于当前技术背景",
        "invention_content": invention_description,
        "analysis_requirements": "请分析技术方案的专利性并提供申请建议",
    }

    return await generator.generate_expert_prompt(
        expert_name=expert_name,
        analysis_type="patent_analysis",
        context_data=context_data,
        user_requirements=user_requirements,
    )
